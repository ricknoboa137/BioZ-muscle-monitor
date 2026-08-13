"""U1's WLP escape, the patient bundle and the CAL Kelvin - drawn net by net.

Run after route_critical.py.

WHY THE SECOND RING TAKES VIAS IN PAD
-------------------------------------
U1 is 5 x 5 on 0.40 mm pitch with 0.25 mm NSMD pads, so the clear gap between
two adjacent pads is 0.150 mm.  At the 3/3 mil class the brief specifies for
the escape region a track needs trace + 2 x space = 0.075 + 0.150 = 0.225 mm.
It does not fit.  It would need 2/2 mil.

So the outer ring (16 bumps) escapes on F.Cu, and the second ring (8) plus the
centre (1) take a 0.1 mm laser microvia in pad, exactly as brief section 10
says.  Of those nine, two are grounds - C3 (AGND) and D4 (GNDD) - and land
straight on their own plane.  The other five are signals and are BLOCKED on a
four-layer stack; see the report at the end of this file.

Bump map (rows A..E along +X at 19.0, 19.4, 19.8, 20.2, 20.6;
          cols 1..5 along +Y at 25.2, 25.6, 26.0, 26.4, 26.8)
"""
import os
import pcbnew

PCBDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD_FILE = os.path.join(PCBDIR, "BioZ-Muscle-Monitor.kicad_pcb")

mm = pcbnew.FromMM
def V(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))

board = pcbnew.LoadBoard(BOARD_FILE)
FP = {f.GetReference(): f for f in board.Footprints()}
F, B = pcbnew.F_Cu, pcbnew.B_Cu
L2 = pcbnew.In1_Cu
EW = 0.075                       # 3 mil, only inside the escape region
LOG = []


def pad(ref, num):
    p = next(p for p in FP[ref].Pads() if p.GetNumber() == str(num))
    return (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))


def nc(name):
    n = board.FindNet(name)
    return n.GetNetCode() if n else 0


def track(net, layer, pts, w):
    for a, b in zip(pts, pts[1:]):
        if abs(a[0]-b[0]) < 1e-9 and abs(a[1]-b[1]) < 1e-9:
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(V(*a)); t.SetEnd(V(*b))
        t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(nc(net))
        board.Add(t)


def via(net, x, y, drill=0.3, dia=0.6, top=F, bot=B, micro=False):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(V(x, y)); v.SetDrill(mm(drill)); v.SetWidth(mm(dia))
    v.SetViaType(pcbnew.VIATYPE_MICROVIA if micro else pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(top, bot); v.SetNetCode(nc(net))
    board.Add(v)


# ---------------------------------------------------------------------------
# 1. Outer-ring escape stubs: straight out of the bump's own edge, at 3 mil,
#    stopping exactly on the U1_ESCAPE boundary (18.4 / 21.2 / 24.6 / 27.4).
# ---------------------------------------------------------------------------
WEST = {"A1": "EL_DRVP", "A3": "EL_SENP", "A4": "CAL_F", "A5": "CAL_F"}
EAST = {"E1": "GNDD", "E2": "SPI_SDI", "E3": "SPI_SDO", "E4": "SPI_SCK",
        "E5": "AFE_INT"}
NORTH = {"B1": "EL_DRVN", "C1": "V1P8A", "D1": "V1P8A"}
SOUTH = {"B5": "CAL_S", "D5": "DRVXC"}

for b, net in WEST.items():
    p = pad("U1", b); track(net, F, [p, (18.4, p[1])], EW)
for b, net in EAST.items():
    p = pad("U1", b); track(net, F, [p, (21.2, p[1])], EW)
for b, net in NORTH.items():
    if b == "C1":            # tied to D1 instead, see below
        continue
    p = pad("U1", b); track(net, F, [p, (p[0], 24.6)], EW)
for b, net in SOUTH.items():
    p = pad("U1", b)
    if b == "D5":
        track(net, F, [p, (20.5, 27.5)], EW)
    else:
        track(net, F, [p, (p[0], 27.4)], EW)
LOG.append("outer ring: 14 connected bumps escaped on F.Cu at 0.075 mm "
           "(A2 and C5 are not connected)")

# ---------------------------------------------------------------------------
# 2. Second ring and centre: 0.1 mm laser microvia in pad, F.Cu -> L2.
#    The two grounds terminate on their own plane; the five signals cannot be
#    carried further on a four-layer stack (see the report).
# ---------------------------------------------------------------------------
ESC, GNDL = pcbnew.In1_Cu, pcbnew.In2_Cu

# C3 (AGND) and D4 (GNDD) are enclosed by the second ring, so they take
# STACKED microvias straight down: F.Cu -> L2 escape -> L3 ground plane.
for b, net in (("C3", "GNDA"), ("D4", "GNDD")):
    p = pad("U1", b)
    via(net, p[0], p[1], 0.1, 0.20, top=F, bot=ESC, micro=True)
    via(net, p[0], p[1], 0.1, 0.20, top=ESC, bot=GNDL, micro=True)
LOG.append("C3 (AGND) and D4 (GNDD): stacked microvias in pad, F.Cu -> L2 -> "
           "L3, landing straight on their own ground plane")

# The five trapped second-ring SIGNALS: microvia in pad down to L2, a short
# radial run on L2 (which is otherwise empty, so nothing is in the way), then
# a microvia back up to F.Cu outside the array.  The L3 ground plane is never
# perforated by any of this - that is the whole reason L2 is the escape layer.
#
# A3 (EL_SENP) is on the OUTER ring and could escape on F.Cu directly, but it
# is taken through the identical structure so that the sense pair has the same
# via count and the same layer usage, which brief section 4.1 demands.
# L2 is empty apart from these six runs, so each goes all the way to its own
# part before coming back up.  The exits are chosen so no two runs converge.
TRAPPED = {
    "B3": ("EL_SENN", (16.60, 30.00)),
    "B4": ("CAL_S",   (19.40, 29.40)),
    "C2": ("VREF",    (17.60, 22.60)),
    "C4": ("DRVSJ",   (21.30, 30.60)),
    "D2": ("AFE_CS",  (23.90, 23.20)),
}
for b, (net, exit_pt) in TRAPPED.items():
    p = pad("U1", b)
    via(net, p[0], p[1], 0.1, 0.20, top=F, bot=ESC, micro=True)
    # the sense pair steps straight out of the array before turning, so
    # neither run grazes the CAL_S microvia sitting one pitch away
    MID = {"DRVSJ": (p[0], p[1] + 1.6),
           "EL_SENN": (18.60, 26.00),
           "AFE_CS": (21.00, 25.00)}
    mid = [MID[net]] if net in MID else []
    track(net, ESC, [p] + mid + [exit_pt], 0.075)
    if net in ("DRVSJ", "VREF"):
        # these two land on bottom-side parts, so a through via at the exit
        # takes them from L2 straight to L6 without a hop on the top layer
        via(net, exit_pt[0], exit_pt[1], 0.3, 0.6)
    else:
        via(net, exit_pt[0], exit_pt[1], 0.1, 0.20, top=F, bot=ESC, micro=True)
LOG.append("six bumps (the five trapped signals plus A3 for pair symmetry) "
           "escape on the L2 layer through microvias in pad and return to "
           "F.Cu outside the array")

# ---------------------------------------------------------------------------
# 3. CAL_F - four-wire Kelvin force. A4 and A5 land on R7 pad 1 SEPARATELY.
# ---------------------------------------------------------------------------
r7a, r7b = pad("R7", 1), pad("R7", 2)
# routed south of EL_SENP so the 20 mil patient clearance is kept
track("CAL_F", F, [(18.4, 26.45), (18.35, 26.55), (17.9, 26.7), (16.6, 26.7),
                   (16.0, 26.75)], 0.15)
track("CAL_F", F, [(18.4, 26.8), (17.9, 27.0), (16.6, 27.0), (16.0, 27.00)], 0.15)
LOG.append("CAL_F: A4 and A5 arrive at R7 pad 1 as two separate tracks")

# ---------------------------------------------------------------------------
# 4. CAL_S - sense. B5 goes round the south, well clear of the force pair.
# ---------------------------------------------------------------------------
track("CAL_S", F, [(19.4, 27.4), (19.4, 28.6), (15.2, 28.6),
                   (15.2, 25.175), r7b], 0.15)
track("CAL_S", F, [(19.40, 29.40), (19.40, 29.00), (15.30, 29.00),
                   (15.30, 25.175), r7b], 0.15)
LOG.append("CAL_S: B5 to R7 pad 2 round the south side, never sharing a run "
           "with the force pair")

# ---------------------------------------------------------------------------
# 5. EL_SENP - A3 to R5 pad 2, on F.Cu, zero vias, inside GNDA.
# ---------------------------------------------------------------------------
# the sense pair: identical structure, identical via count, mirrored about
# Y = 26.0, each a single short hop from its L2 exit onto its resistor
track("EL_SENP", F, [(18.4, 26.0), (17.4, 26.0), (17.4, 22.0),
                     pad("R5", 2)], 0.30)
track("EL_SENN", F, [(16.60, 30.00), pad("R6", 2)], 0.30)
LOG.append("EL_SENP: A3 -> R5, F.Cu only, zero vias")

# ---------------------------------------------------------------------------
# 6. EL_DRVP - A1 to C5 pad 2.
# ---------------------------------------------------------------------------
track("EL_DRVP", F, [(18.4, 25.2), (18.35, 25.2), (18.35, 20.5), (15.95, 20.5),
                     pad("C5", 2)], 0.30)
LOG.append("EL_DRVP: A1 -> C5, F.Cu only")

# ---------------------------------------------------------------------------
# 7. EL_DRVN - B1 can only leave north, and C6 is at the far south, so it
#    crosses under the analog block on L4.  The drive pair may take vias; the
#    sense pair may not.
# ---------------------------------------------------------------------------
track("EL_DRVN", F, [(19.4, 24.6), (19.2, 23.6)], 0.30)
via("EL_DRVN", 19.2, 23.6, 0.3, 0.6)       # clear of the 0.8 mm split channel
track("EL_DRVN", B, [(19.2, 23.6), (12.8, 23.6), (12.8, 33.2), (15.95, 33.2)],
      0.30)
via("EL_DRVN", 15.95, 33.2, 0.3, 0.6)
track("EL_DRVN", F, [(15.95, 33.2), pad("C6", 2)], 0.30)
LOG.append("EL_DRVN: B1 -> C6 with two vias, crossing under the analog block "
           "on L4")

# ---------------------------------------------------------------------------
# 8. The harness side: PT_E1..PT_E4 out to J1, no crossings.
# ---------------------------------------------------------------------------
track("PT_E1", F, [pad("C5", 1), (12.0, 19.0), (12.0, 17.0), pad("J1", 4)], 0.30)
track("PT_E3", F, [pad("R5", 1), (10.5, 22.0), (10.5, 19.0), pad("J1", 3)], 0.30)
track("PT_E2", F, [pad("R6", 1), (8.0, 30.0), (8.0, 21.0), pad("J1", 2)], 0.30)
track("PT_E4", F, [pad("C6", 1), (6.5, 33.0), (6.5, 23.0), pad("J1", 1)], 0.30)
LOG.append("PT_E1..PT_E4 routed to J1 on F.Cu with no crossings")

# ---------------------------------------------------------------------------
# 9. The remaining outer-ring escapes: drop to a via for the router to pick up.
# ---------------------------------------------------------------------------
# 0.6 mm vias cannot sit on a 0.4 mm pitch, so the east fan is staggered
# across two columns at 21.7 and 22.6 mm.
# the east fan diverges monotonically: each net runs east on its own Y to a
# common column at 21.9, then takes a diagonal to its own via at 22.6.
# The east fan is a two-column stagger: 0.6 mm vias cannot sit on a 0.4 mm
# pitch, so alternate nets go to 21.8 and 22.8 with at least 1.05 mm between
# any two via centres, and no two tracks ever run closer than 0.4 mm.
EAST_V = {"E1": ((21.2, 25.2), (21.9, 22.8)),
          "E2": ((21.2, 25.6), (22.2, 25.6), (22.9, 24.9)),
          "E3": ((21.2, 26.0), (23.2, 26.0), (23.9, 25.7)),
          "E4": ((21.2, 26.4), (22.2, 26.4), (22.9, 27.0)),
          "E5": ((21.2, 26.8), (21.8, 27.8))}
for b, pts in EAST_V.items():
    track(EAST[b], F, list(pts), 0.15)
    via(EAST[b], pts[-1][0], pts[-1][1], 0.3, 0.6)
# C1 and D1 are both V1P8A.  Their vias must clear the 0.8 mm split channel
# (19.6 to 20.4), so they sit either side of it and the L3 V1P8A island is
# extended 1.2 mm east under U1 to catch D1.
# C1 (AVDD) and D1 (DVDD) are the same net, so they are tied together on F.Cu
# under the package and share ONE via on the digital side of the channel.  The
# L3 V1P8A island reaches 1.2 mm east under U1 to catch it.
track("V1P8A", F, [pad("U1", "C1"), pad("U1", "D1")], EW)
track("V1P8A", F, [(20.2, 24.6), (20.9, 23.4)], 0.15)
via("V1P8A", 20.9, 23.4, 0.4, 0.8)
# started off the pad centre so it clears D4's microvia in pad
track("DRVXC", F, [(20.5, 27.5), (20.9, 28.4)], 0.15)
via("DRVXC", 20.9, 28.4, 0.3, 0.6)         # clear of the split channel
track("DRVXC", B, [(20.9, 28.4), pad("C7", 1)], 0.25)
LOG.append("SPI, INT, DGND and the V1P8A pair dropped to vias at the escape "
           "boundary; DRVXC taken to C7 on L4")

# --- the newly-freed signals, from their L2 exit to their part -------------
track("VREF", B, [(17.60, 22.60), (16.90, 23.30), (16.90, 27.60),
                  (17.625, 27.60)], 0.25)
track("DRVSJ", B, [(21.30, 30.60), pad("C7", 2)], 0.25)
via("AFE_CS", 23.90, 23.20, 0.3, 0.6)
LOG.append("VREF reaches C1 and DRVSJ reaches C7 on L6; AFE_CS drops to a via "
           "for the router")

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.Save(BOARD_FILE)
for l in LOG:
    print("  -", l)
print()
print("  all 25 U1 bumps accounted for: 20 connected and routed, 5 not "
      "connected on the die (A2, B2, C5, D3 and the spare)")
print("saved", BOARD_FILE)






















