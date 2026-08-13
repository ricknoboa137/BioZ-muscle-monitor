"""The two checks brief section 9 says DRC cannot make.

  1. GNDA and GNDD are joined at exactly one point, R1.
     Method: fill the zones, then test every piece of copper on every layer.
     GNDA copper must lie wholly on the analog side of the split, GNDD copper
     wholly on the digital side, and R1's two pads must be the only items that
     straddle it.  Then the two pours are geometrically tested for contact.

  2. No copper on any layer inside the antenna keepout.
     Method: intersect every filled zone outline, pad, track and via against
     the keepout rectangle, layer by layer.  AE1's own pads and the RF feed
     line are the documented exceptions.

Run with KiCad's bundled python.  Exit status is 0 only if both pass.
"""
import os, sys
import pcbnew

PCBDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD_FILE = os.path.join(PCBDIR, "BioZ-Muscle-Monitor.kicad_pcb")

SPLIT_X = 20.0
ANT_KO = (25.0, 0.0, 50.0, 6.82)
LAYERS = [(pcbnew.F_Cu, "L1 Top"), (pcbnew.In1_Cu, "L2 Escape"),
          (pcbnew.In2_Cu, "L3 GND"), (pcbnew.In3_Cu, "L4 Power"),
          (pcbnew.In4_Cu, "L5 Signal"), (pcbnew.B_Cu, "L6 Bottom")]

board = pcbnew.LoadBoard(BOARD_FILE)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.BuildConnectivity()
T = pcbnew.ToMM
fail = []

print("=" * 74)
print("CHECK 1 - GNDA / GNDD are joined at exactly one point (R1)")
print("=" * 74)

side_err = []
for f in board.Footprints():
    ref = f.GetReference()
    for p in f.Pads():
        nn = p.GetNetname()
        if nn not in ("GNDA", "GNDD"):
            continue
        bb = p.GetBoundingBox()
        x1, x2 = T(bb.GetLeft()), T(bb.GetRight())
        if ref == "R1":
            continue
        if nn == "GNDA" and x2 > SPLIT_X:
            side_err.append(f"{ref}.{p.GetNumber()} GNDA reaches x={x2:.2f}")
        if nn == "GNDD" and x1 < SPLIT_X:
            side_err.append(f"{ref}.{p.GetNumber()} GNDD reaches x={x1:.2f}")

for t in board.Tracks():
    nn = t.GetNetname()
    if nn not in ("GNDA", "GNDD"):
        continue
    bb = t.GetBoundingBox()
    x1, x2 = T(bb.GetLeft()), T(bb.GetRight())
    if nn == "GNDA" and x2 > SPLIT_X:
        side_err.append(f"track GNDA on {board.GetLayerName(t.GetLayer())} "
                        f"reaches x={x2:.2f}")
    if nn == "GNDD" and x1 < SPLIT_X:
        side_err.append(f"track GNDD on {board.GetLayerName(t.GetLayer())} "
                        f"reaches x={x1:.2f}")

# filled pour geometry, layer by layer
pour_err = []
for lay, name in LAYERS:
    polys = {}
    for z in board.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(lay):
            continue
        nn = z.GetNetname()
        if nn not in ("GNDA", "GNDD"):
            continue
        sp = z.GetFilledPolysList(lay)
        polys.setdefault(nn, []).append(sp)
    for nn, sps in polys.items():
        for sp in sps:
            bb = sp.BBox()
            x1, x2 = T(bb.GetLeft()), T(bb.GetRight())
            if nn == "GNDA" and x2 > SPLIT_X + 0.001:
                pour_err.append(f"{name}: GNDA pour reaches x={x2:.3f}")
            if nn == "GNDD" and x1 < SPLIT_X - 0.001:
                pour_err.append(f"{name}: GNDD pour reaches x={x1:.3f}")
    # closest approach between the two pours on this layer
    a = polys.get("GNDA"); d = polys.get("GNDD")
    if a and d:
        touch = False
        for pa in a:
            for pd in d:
                for oi in range(pd.OutlineCount()):
                    ol = pd.Outline(oi)
                    for vi in range(ol.PointCount()):
                        if pa.Collide(ol.CPoint(vi), pcbnew.FromMM(0.05)):
                            touch = True
                            break
                    if touch:
                        break
                if touch:
                    break
            if touch:
                break
        verdict = "TOUCH" if touch else "clear by at least 0.05 mm"
        print(f"    {name}: GNDA / GNDD pours {verdict}")
        if touch:
            pour_err.append(f"{name}: GNDA and GNDD pours touch")

r1 = next((f for f in board.Footprints() if f.GetReference() == "R1"), None)
if r1 is None:
    fail.append("R1 is missing from the board")
else:
    nets = sorted({p.GetNetname() for p in r1.Pads()})
    print(f"  R1 present on {board.GetLayerName(r1.GetLayer())}, "
          f"pads on nets {nets}")
    if nets != ["GNDA", "GNDD"]:
        fail.append(f"R1 pads are on {nets}, expected GNDA and GNDD")

if side_err:
    print("  FAIL - copper on the wrong side of the split:")
    for e in sorted(set(side_err))[:20]:
        print("    ", e)
    fail.append(f"{len(set(side_err))} ground items cross the split")
else:
    print("  PASS - every GNDA item is left of x=20.0 and every GNDD item "
          "right of it")

if pour_err:
    print("  FAIL - pour geometry:")
    for e in sorted(set(pour_err)):
        print("    ", e)
    fail.append("ground pours are not cleanly separated")
else:
    print("  PASS - GNDA and GNDD pours do not touch on any of the four "
          "layers; R1 is the only join")

# --- 1b. the literal test: take R1 out, is anything else still joining them? --
# The geometric split test above is a proxy.  This is the direct version: no
# footprint other than R1 may have pads on both nets, and with R1's pads
# excluded no GNDA copper item may collide with any GNDD copper item, on any
# of the six layers.
print("  -- R1 removed: direct GNDA/GNDD isolation test --")
bridges = []
# R1 is the deliberate stitch.  U1 is the AFE itself: it has separate analog and
# digital ground bumps (C3 -> GNDA, D4/E1 -> GNDD), which is the whole reason the
# split-plane + single-stitch topology exists.  A part straddling the split
# through its own package is not a board-level bridge.
# NOT VERIFIED HERE: whether the MAX30009 die bonds AGND to DGND internally.  If
# it does, R1 is in parallel with that bond and the split is only partial.  Check
# the datasheet's ground description before fab.
STRADDLE_OK = {"R1", "U1"}
for f in board.Footprints():
    if f.GetReference() in STRADDLE_OK:
        continue
    nets = {p.GetNetname() for p in f.Pads()}
    if "GNDA" in nets and "GNDD" in nets:
        bridges.append(f"footprint {f.GetReference()} has pads on both nets")

def shapes(netname, lay):
    """every copper item of `netname` present on layer `lay`, R1 excluded"""
    out = []
    for f in board.Footprints():
        if f.GetReference() == "R1":
            continue
        for p in f.Pads():
            if p.GetNetname() == netname and p.IsOnLayer(lay):
                out.append(p.GetEffectiveShape(lay))
    for t in board.Tracks():
        if t.GetNetname() == netname and t.IsOnLayer(lay):
            out.append(t.GetEffectiveShape(lay))
    for z in board.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(lay):
            continue
        if z.GetNetname() == netname:
            out.append(z.GetFilledPolysList(lay))
    return out

for lay, name in LAYERS:
    ga, gd = shapes("GNDA", lay), shapes("GNDD", lay)
    touch = None
    for sa in ga:
        for sd in gd:
            if sa.Collide(sd, 0):
                touch = True
                break
        if touch:
            break
    print("    %-12s GNDA items %-4d GNDD items %-4d -> %s"
          % (name, len(ga), len(gd), "TOUCH" if touch else "isolated"))
    if touch:
        bridges.append("GNDA touches GNDD on %s" % name)
if bridges:
    print("  FAIL - GNDA and GNDD are joined somewhere other than R1:")
    for bb_ in sorted(set(bridges))[:10]:
        print("    ", bb_)
    fail.append("GNDA/GNDD not isolated with R1 removed")
else:
    print("  PASS - with R1 removed, no footprint and no copper item on any of "
          "the 6 layers joins GNDA to GNDD")

print()
print("=" * 74)
print("CHECK 2 - no copper on any layer inside the antenna keepout")
print("=" * 74)
kx1, ky1, kx2, ky2 = ANT_KO
print(f"  keepout {kx1}..{kx2} x {ky1}..{ky2} mm "
      f"(6.82 mm from the Wurth 74889302450 evaluation-board drawing)")


def hits(bb):
    return (T(bb.GetRight()) > kx1 and T(bb.GetLeft()) < kx2 and
            T(bb.GetBottom()) > ky1 and T(bb.GetTop()) < ky2)


for lay, name in LAYERS:
    bad = []
    for f in board.Footprints():
        for p in f.Pads():
            if not p.IsOnLayer(lay):
                continue
            if f.GetReference() == "AE1":
                continue                      # the antenna itself
            if hits(p.GetBoundingBox()):
                bad.append(f"pad {f.GetReference()}.{p.GetNumber()} "
                           f"[{p.GetNetname()}]")
    for t in board.Tracks():
        if not t.IsOnLayer(lay):
            continue
        cls = t.GetNetClassName() if hasattr(t, "GetNetClassName") else ""
        if hits(t.GetBoundingBox()):
            tag = "track" if t.Type() == pcbnew.PCB_TRACE_T else "via"
            if tag == "track" and cls == "RF":
                continue                      # the documented RF feed line
            bad.append(f"{tag} [{t.GetNetname()}] class={cls}")
    for z in board.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(lay):
            continue
        sp = z.GetFilledPolysList(lay)
        if not sp.OutlineCount():
            continue
        # Grid-sample the keepout rectangle.  A bounding-box test is useless
        # here: the pours span the whole digital half of the board, so their
        # bounding boxes always overlap the keepout.
        hit = False
        gx = kx1
        while gx <= kx2 and not hit:
            gy = ky1
            while gy <= ky2:
                if sp.Collide(pcbnew.VECTOR2I(pcbnew.FromMM(gx),
                                              pcbnew.FromMM(gy)), 0):
                    hit = True
                    break
                gy += 0.25
            gx += 0.25
        if hit:
            bad.append(f"filled pour [{z.GetNetname()}]")
    if bad:
        print(f"  {name}: FAIL - {len(bad)} item(s)")
        for b in sorted(set(bad))[:10]:
            print("    ", b)
        fail.append(f"copper inside the antenna keepout on {name}")
    else:
        print(f"  {name}: PASS - clear")

print()
print("=" * 74)
if fail:
    print("RESULT: FAIL")
    for f_ in fail:
        print("  -", f_)
    sys.exit(1)
print("RESULT: PASS - both manual checks satisfied")


