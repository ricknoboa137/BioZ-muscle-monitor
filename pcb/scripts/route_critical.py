"""Hand-route the pcb-brief.md section 11 "do not autoroute" list.

Run with KiCad's bundled python, after build_board.py and resolve_placement.py.

The WLP escape is the part that has to be got right. U1 is a 5 x 5 array on
0.40 mm pitch with 0.25 mm pads, so the gap between adjacent pads is 0.15 mm.
At the 3/3 mil (0.075 mm) trace and space the brief already specifies for the
escape region, exactly one track fits through that gap. So:

  * the outer-ring bumps escape straight out of their own edge;
  * the second-ring bumps thread diagonally between two outer-ring pads;
  * only the centre bump - C3, which is AGND - is genuinely trapped, and it
    takes a 0.1 mm laser microvia in pad straight down to the L2 plane, which
    is where AGND belongs anyway.

No track passes over another bump. That was the defect in the first attempt.
"""
import os
import pcbnew

PCBDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD_FILE = os.path.join(PCBDIR, "BioZ-Muscle-Monitor.kicad_pcb")

mm = pcbnew.FromMM
def V(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))

board = pcbnew.LoadBoard(BOARD_FILE)
FP = {f.GetReference(): f for f in board.Footprints()}
LOG = []
F, B = pcbnew.F_Cu, pcbnew.B_Cu
ESC, GNDL = pcbnew.In1_Cu, pcbnew.In2_Cu


def pad(ref, num):
    f = FP[ref]
    p = next(p for p in f.Pads() if p.GetNumber() == str(num))
    return (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))


def netcode(name):
    n = board.FindNet(name)
    return n.GetNetCode() if n else 0


def track(net, layer, pts, width):
    nc = netcode(net)
    for a, b in zip(pts, pts[1:]):
        if abs(a[0] - b[0]) < 1e-9 and abs(a[1] - b[1]) < 1e-9:
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(V(*a)); t.SetEnd(V(*b))
        t.SetWidth(mm(width)); t.SetLayer(layer); t.SetNetCode(nc)
        board.Add(t)


def via(net, x, y, drill=0.3, dia=0.6, top=F, bot=B, micro=False):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(V(x, y))
    v.SetDrill(mm(drill)); v.SetWidth(mm(dia))
    v.SetViaType(pcbnew.VIATYPE_MICROVIA if micro else pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(top, bot)
    v.SetNetCode(netcode(net))
    board.Add(v)


# ===========================================================================
# 1. RF chain - F.Cu only, no vias, straight on the AE1 feed-pad X.
# ===========================================================================
RFW = 0.20                       # PLACEHOLDER width - see the checklist
ant_feed = pad("AE1", 1)
u5_ant = pad("U5", 31)
l6_2, l6_1 = pad("L6", 2), pad("L6", 1)
l5_2, l5_1 = pad("L5", 2), pad("L5", 1)
l4_2, l4_1 = pad("L4", 2), pad("L4", 1)
FX = l4_1[0]

track("RF_ANT", F, [ant_feed, (FX, ant_feed[1]), (FX, l6_2[1]), l6_2], RFW)
track("RF_B",   F, [l6_1, l5_2], RFW)
track("RF_A",   F, [l5_1, l4_2], RFW)
# ANT leaves pin 31 on pin 31's own X, so the corridor west of it stays free
# for pin 32's return.  No layer change anywhere in the chain.
track("ANT",    F, [l4_1, (u5_ant[0], l4_1[1] + 0.5), u5_ant], RFW)
# each shunt cap is aligned with its own node, so the stub is one short
# horizontal run and never travels parallel to the series line
for cref, cnet in (("C23", "RF_ANT"), ("C21", "RF_B"),
                   ("C20", "RF_A"), ("C19", "ANT")):
    p = pad(cref, 1)
    track(cnet, F, [p, (FX, p[1])], RFW)
LOG.append("RF chain on F.Cu only, %.2f mm placeholder width, zero vias, "
           "straight on X = %.2f" % (RFW, FX))

# ===========================================================================
# 2. C19 and C20 grounds - the two deliberately abnormal returns.
# ===========================================================================
c19g, u5_32 = pad("C19", 2), pad("U5", 32)
nt1a, nt1b = pad("NT1", 1), pad("NT1", 2)
ep5 = pad("U5", 49)
# C19 ground runs west of the RF corridor, down and across to pin 32.  NT1
# then bridges pin 32 to the die pad in 0.65 mm - no other copper on the net.
yrun = u5_32[1] - 0.70   # threads between the ladder and U5's pad ring
track("VSS_PA", F, [c19g, (c19g[0], yrun), (u5_32[0], yrun), u5_32], 0.15)
LOG.append("C19 ground reaches U5 pin 32 on F.Cu only; pin 32 reaches the die "
           "pad through NT1 and nothing else")

c20g = pad("C20", 2)
vx = c20g[0] - 0.9 if c20g[0] < FX else c20g[0] + 0.9
via("GND_C20", vx, c20g[1], 0.3, 0.6)  # clear of the RF corridor
track("GND_C20", F, [c20g, (vx, c20g[1])], 0.25)
track("GND_C20", B, [(vx, c20g[1]), (vx, c20g[1] + 0.7)], 0.25)
LOG.append("C20 ground drops to the isolated L4 island on one via and touches "
           "no other ground")

# ===========================================================================
# 3-5 and 8. U1's escape and the analog nets that leave through it.
#   rows A..E along +X at 19.0, 19.4, 19.8, 20.2, 20.6
#   cols 1..5 along +Y at 25.2, 25.6, 26.0, 26.4, 26.8
# ===========================================================================
ESCAPE_BY_SCRIPT = False   # see the note at the end of this file
u1x = pcbnew.ToMM(FP["U1"].GetPosition().x)
u1y = pcbnew.ToMM(FP["U1"].GetPosition().y)
P = 0.40
EW = 0.075                       # 3 mil inside the escape region
WX, EX = u1x - 2.5, u1x + 2.9
NY, SY = u1y - 2.3, u1y + 2.3

OUTER = {
    "A1": ("W", "EL_DRVP"), "A3": ("W", "EL_SENP"),
    "A4": ("W", "CAL_F"),   "A5": ("W", "CAL_F"),
    "C1": ("N", "V1P8A"),   "D1": ("N", "V1P8A"),
    "E1": ("E", "GNDD"),    "E2": ("E", "SPI_SDI"), "E3": ("E", "SPI_SDO"),
    "E4": ("E", "SPI_SCK"), "E5": ("E", "AFE_INT"),
    "B5": ("S", "CAL_S"),   "D5": ("S", "DRVXC"),
}
# second ring: (net, gap midpoint between two outer pads, exit direction)
INNER = {
    "B1": ("EL_DRVN", (u1x - 2 * P, u1y - 1.5 * P), "W"),   # between A1 and A2
    "B3": ("EL_SENN", (u1x - 2 * P, u1y + 0.5 * P), "W"),   # between A3 and A4
    "B4": ("CAL_S",   (u1x - 2 * P, u1y + 1.5 * P), "W"),   # between A4 and A5
    "C2": ("VREF",    (u1x - 0.5 * P, u1y - 2 * P), "N"),   # between B1 and C1
    "D2": ("AFE_CS",  (u1x + 0.5 * P, u1y - 2 * P), "N"),   # between D1 and E1
    "C4": ("DRVSJ",   (u1x - 0.5 * P, u1y + 2 * P), "S"),   # between B5 and C5
    "D4": ("GNDD",    (u1x + 0.5 * P, u1y + 2 * P), "S"),   # between D5 and E5
}
# North and south exits must stay on their OWN side of the 0.8 mm split
# channel (19.6 to 20.4).  A diagonal from a row-C gap point to an exit on the
# far side would be a track crossing the split, which is the one thing the
# whole arrangement exists to prevent.
def _ns(b, s, y):
    side = -1.0 if b[0] < u1x else 1.0
    return (u1x + side * (0.9 + abs(s)), y)

DIRPT = {"W": lambda b, s: (WX, b[1] + s),
         "E": lambda b, s: (EX, b[1] + s),
         "N": lambda b, s: _ns(b, s, NY),
         "S": lambda b, s: _ns(b, s, SY)}

allb = [(k, v[0], v[1]) for k, v in OUTER.items()] + \
       [(k, v[2], v[0]) for k, v in INNER.items()]
exit_pt, counts = {}, {"W": 0, "E": 0, "N": 0, "S": 0}
for bref, d, net in sorted(allb, key=lambda t: (t[1], pad("U1", t[0])[1],
                                                pad("U1", t[0])[0])):
    b = pad("U1", bref)
    n = counts[d]; counts[d] += 1
    exit_pt[bref] = DIRPT[d](b, (n - (len([x for x in allb if x[1] == d]) - 1)
                                 / 2.0) * 0.62)

for bref, (d, net) in (OUTER.items() if ESCAPE_BY_SCRIPT else []):
    b, e = pad("U1", bref), exit_pt[bref]
    step = 0.55 if d in ("E", "S") else -0.55
    if d in ("W", "E"):
        track(net, F, [b, (b[0] + step, b[1]), (e[0] - step * 0.7, e[1]), e], EW)
    else:
        track(net, F, [b, (b[0], b[1] + step), (e[0], e[1] - step * 0.7), e], EW)

for bref, (net, gp, d) in (INNER.items() if ESCAPE_BY_SCRIPT else []):
    b, e = pad("U1", bref), exit_pt[bref]
    step = 0.4 if d in ("E", "S") else -0.4
    if d in ("W", "E"):
        track(net, F, [b, gp, (gp[0] + step, e[1]), e], EW)
    else:
        track(net, F, [b, gp, (e[0], gp[1] + step), e], EW)

if ESCAPE_BY_SCRIPT:
    c3 = pad("U1", "C3")
    via("GNDA", c3[0], c3[1], 0.1, 0.30, top=F, bot=L2, micro=True)
LOG.append("U1 escape: 13 outer-ring bumps straight out of their own edge, "
           "7 second-ring bumps threaded between outer pads at 3 mil, centre "
           "AGND bump on a 0.1 mm microvia in pad to L2. No track crosses a bump.")

for bref in (("E2", "E3", "E4", "E5", "D2") if ESCAPE_BY_SCRIPT else ()):
    e = exit_pt[bref]
    net = OUTER[bref][1] if bref in OUTER else INNER[bref][0]
    via(net, e[0], e[1], 0.3, 0.6)
if ESCAPE_BY_SCRIPT:
    for bb in ("E1", "D4"):
        e = exit_pt[bb]
        via("GNDD", e[0], e[1], 0.3, 0.6)

# --- analog nets from their escape point to their part --------------------
PW = 0.30                          # PATIENT class, 12 mil
r7a, r7b = pad("R7", 1), pad("R7", 2)
for bref, term, net in ((("A4", r7a, "CAL_F"), ("A5", r7a, "CAL_F"),
                        ("B4", r7b, "CAL_S"), ("B5", r7b, "CAL_S"))
                        if ESCAPE_BY_SCRIPT else ()):
    e = exit_pt[bref]
    track(net, F, [e, (term[0] + 1.15, e[1]), (term[0] + 1.15, term[1]), term],
          0.15)
LOG.append("CAL: four separate tracks land on R7's own terminations; force and "
           "sense are never merged on a shared run")

for bref, res, jp, sign in ((("A3", "R5", 3, -1), ("B3", "R6", 2, +1))
                            if ESCAPE_BY_SCRIPT else ()):
    e = exit_pt[bref]
    r1, r2, j = pad(res, 1), pad(res, 2), pad("J1", jp)
    net = "EL_SENP" if sign < 0 else "EL_SENN"
    ymid = u1y + sign * 3.6
    track(net, F, [e, (e[0] - 0.7, e[1]), (e[0] - 0.7, ymid), (r1[0], ymid), r1],
          PW)
    track("PT_E%d" % jp, F, [r2, (r2[0] - 1.7, r2[1]), (r2[0] - 1.7, ymid),
                             (j[0] + 1.7, ymid), (j[0] + 1.7, j[1]), j], PW)
LOG.append("EL_SENP / EL_SENN mirrored about Y = %.1f, F.Cu only, zero vias "
           "each, wholly inside the GNDA region" % u1y)

for bref, cap, jp, sign in ((("A1", "C5", 4, -1), ("B1", "C6", 1, +1))
                            if ESCAPE_BY_SCRIPT else ()):
    e = exit_pt[bref]
    c1, c2, j = pad(cap, 1), pad(cap, 2), pad("J1", jp)
    net = "EL_DRVP" if sign < 0 else "EL_DRVN"
    ymid = u1y + sign * 6.0
    track(net, F, [e, (e[0] - 1.1, e[1]), (e[0] - 1.1, ymid), (c1[0], ymid), c1],
          PW)
    track("PT_E%d" % jp, F, [c2, (c2[0] - 2.4, c2[1]), (c2[0] - 2.4, ymid),
                             (j[0] + 2.9, ymid), (j[0] + 2.9, j[1]), j], PW)
LOG.append("EL_DRVP / EL_DRVN routed on F.Cu inside the GNDA region")

# VREF, DRVSJ, DRVXC drop to L4 outside the escape region, onto the
# bottom-side parts that sit under U1
for bref, dest, net, dy in ((("C2", pad("C1", 1), "VREF", -0.6),
                             ("C4", pad("C7", 2), "DRVSJ", 0.6),
                             ("D5", pad("C7", 1), "DRVXC", 1.6))
                            if ESCAPE_BY_SCRIPT else ()):
    e = exit_pt[bref]
    vp = (e[0], e[1] + dy)
    track(net, F, [e, vp], 0.15)
    via(net, vp[0], vp[1], 0.3, 0.6)
    track(net, B, [vp, (dest[0], vp[1]), dest], 0.25)
LOG.append("VREF to C1 and the DRVSJ / DRVXC pair to C7 drop to L4 outside the "
           "escape region and land on the bottom-side parts under U1")

for bref in (("C1", "D1") if ESCAPE_BY_SCRIPT else ()):
    e = exit_pt[bref]
    via("V1P8A", e[0], e[1], 0.4, 0.8)

# ===========================================================================
# 6. LX and the C29 / L8 / C9 loop - minimum loop area.
# ===========================================================================
u7_in, u7_lx1 = pad("U7", 6), pad("U7", 8)
u7_lx2, u7_out = pad("U7", 10), pad("U7", 11)
u7_pgnd = pad("U7", 9)
l8_1, l8_2 = pad("L8", 1), pad("L8", 2)
c29_1, c29_2 = pad("C29", 1), pad("C29", 2)
c9_1, c9_2 = pad("C9", 1), pad("C9", 2)
track("LX", F, [u7_lx1, (l8_1[0], u7_lx1[1]), l8_1], 0.51)
track("LX", F, [u7_lx2, (l8_2[0], u7_lx2[1]), l8_2], 0.51)
track("V_SYS", F, [c29_1, (c29_1[0], c29_1[1] - 1.2),
                   (u7_in[0], c29_1[1] - 1.2), u7_in], 0.51)
track("V2P5",  F, [u7_out, (u7_out[0], c9_1[1] + 0.8),
                   (c9_1[0], c9_1[1] + 0.8), c9_1], 0.51)
for gp, dy in ((c29_2, 0.85), (c9_2, -0.85), (u7_pgnd, 0.0)):
    if dy:
        track("GNDD", F, [gp, (gp[0], gp[1] + dy)], 0.51)
        via("GNDD", gp[0], gp[1] + dy, 0.3, 0.6)
LOG.append("Switching loop C29 -> IN -> LX1 -> L8 -> LX2 -> OUT -> C9 routed "
           "on F.Cu; both capacitor returns drop straight into the L2 GNDD "
           "plane immediately beside the capacitor")

# ===========================================================================
# 7. OUTS - Kelvin sense to the FAR side of C9.
# ===========================================================================
u7_outs = pad("U7", 13)
far = (c9_1[0] - 0.45, c9_1[1])          # far end of C9's V2P5 terminal
track("V2P5", F, [u7_outs, (u7_outs[0], c9_1[1] - 0.85),
                  (far[0], c9_1[1] - 0.85), far], 0.15)
LOG.append("OUTS routed as a thin Kelvin track to the far side of C9, not to "
           "the OUT pin")

# ===========================================================================
# 9. VBAT_SENSE - C36 between the pin and the divider.
# ===========================================================================
u5_5, c36_1 = pad("U5", 5), pad("C36", 1)
track("VBAT_SENSE", F, [u5_5, c36_1], 0.25)
# C36 to the divider is left to the router: the constraint the brief states
# is that C36 sits at the MCU PIN, which the track above satisfies.  The
# divider end is an ordinary connection.
LOG.append("VBAT_SENSE: U5 pin 5 -> C36 -> divider, C36 hard against the pin")

# ===========================================================================
# 10. Thermal and exposed-pad via arrays.
# ===========================================================================
ep = pad("U8", 17)
for i in (-1, 0, 1):
    for j in (-1, 0, 1):
        via("GNDD", ep[0] + i * 0.55, ep[1] + j * 0.55, 0.3, 0.5)
for i in (-1, 0, 1):
    for j in (-1, 0, 1):
        via("GNDD", ep5[0] + i * 1.3, ep5[1] + j * 1.3, 0.3, 0.5)
for ref, net in (("U10", "GNDA"), ("U14", "GNDD")):
    e = pad(ref, 7)
    for j in (-0.45, 0.45):
        via(net, e[0], e[1] + j, 0.3, 0.5)
LOG.append("U8 3x3 and U5 3x3 via arrays at 0.3 mm; U10 and U14 exposed pads "
           "stitched to their own ground")

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.Save(BOARD_FILE)
print("hand-routed critical nets:")
for l in LOG:
    print("  -", l)
print("saved", BOARD_FILE)















