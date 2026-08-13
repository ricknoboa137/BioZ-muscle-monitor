"""Second U5 fanout pass, per the user ruling in CHECKPOINT entry 16.

  * 0.30 / 0.20 mm vias for the 10 pins that just need to get off the package.
    0.20 mm is exactly the project's min_through_hole_diameter and the annular
    ring is (0.30-0.20)/2 = 0.05 mm, exactly min_via_annular_width.  Both are at
    the stated limit, not past it.  No trace width or clearance rule is relaxed.
  * XL1, XC1, XC2 and DCC get a via-less F.Cu escape stub instead: they sit
    beside their crystals and the ruling is that they stay on the top layer.
    The stub only has to get them clear of the 0.4 mm pad pitch; Freerouting
    then completes them on F.Cu from open copper.

The first pass (fanout_u5.py, 0.40/0.25) already escaped 15 pins; those are left
alone.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from handroute import Router, T

R = Router()
F = pcbnew.F_Cu
ALLCU = list(R.board.GetEnabledLayers().CuStack())

VIA_PINS = [6, 8, 10, 14, 16, 23, 26, 28, 30, 33]     # 0.30/0.20 vias
STUB_PINS = [1, 34, 35, 46]                            # F.Cu only, no via
DIA, DRILL = 0.30, 0.20
# The escape channel between two 0.30 mm vias 0.80 mm apart is 0.50 mm.  A
# 0.15 mm trace needs 0.15 + 2 x 0.20 = 0.55 mm and does NOT fit -- that was why
# pass 2 first escaped only one pin.  At the 0.075 mm minimum track width it
# needs 0.475 mm and does.  min_track_width is 0.075, so this is at the stated
# limit, not past it.
W = 0.075

SIDES = {"S": (0.0, 1.0), "E": (1.0, 0.0), "N": (0.0, -1.0), "W": (-1.0, 0.0)}


def side_of(x, y):
    if abs(y - 17.95) < 0.01: return "S"
    if abs(x - 33.55) < 0.01: return "E"
    if abs(y - 12.05) < 0.01: return "N"
    if abs(x - 27.65) < 0.01: return "W"
    return None


existing = [(T(t.GetPosition().x), T(t.GetPosition().y), T(t.GetDrill()))
            for t in R.board.GetTracks() if t.GetClass() == "PCB_VIA"]
new_vias = []

DISTS = [0.60, 0.80, 1.00, 1.25, 1.50, 1.80, 2.10, 2.50, 2.90, 3.30]
LATS = [0.0, 0.20, -0.20, 0.40, -0.40, 0.60, -0.60, 0.80, -0.80,
        1.00, -1.00, 1.20, -1.20, 1.50, -1.50, 1.90, -1.90]

placed, failed = [], []
for num in VIA_PINS:
    p = R.pad("U5", num)
    px, py = R.padxy("U5", num)
    nc = p.GetNetCode()
    s = side_of(px, py)
    tx, ty = SIDES[s]
    lx, ly = (1.0, 0.0) if s in ("S", "N") else (0.0, 1.0)
    sx, sy = px + tx * 0.30, py + ty * 0.30
    hit = None
    for d in DISTS:
        for lat in LATS:
            vx, vy = px + tx * d + lx * lat, py + ty * d + ly * lat
            if R.in_rule_area(vx, vy, DIA / 2.0):
                continue
            if R.hole_conflict(vx, vy, DRILL, new_vias):
                continue
            if not R.via_clear(vx, vy, DIA, nc, ALLCU):
                continue
            if not R.seg_clear((sx, sy), (vx, vy), W, nc, F):
                continue
            hit = (vx, vy)
            break
        if hit:
            break
    if not hit:
        failed.append((num, p.GetNetname(), "no clear 0.30 mm via site"))
        continue
    vx, vy = hit
    new_vias.append((vx, vy, DRILL))
    R.add_track(nc, F, (sx, sy), (vx, vy), W)
    R.add_via(nc, vx, vy, DIA, DRILL)
    placed.append((num, p.GetNetname(), round(vx, 3), round(vy, 3), "via"))

# via-less stubs: push out until the stub end is clear of the pad field, so the
# router has open copper to start from
for num in STUB_PINS:
    p = R.pad("U5", num)
    px, py = R.padxy("U5", num)
    nc = p.GetNetCode()
    s = side_of(px, py)
    tx, ty = SIDES[s]
    lx, ly = (1.0, 0.0) if s in ("S", "N") else (0.0, 1.0)
    best = None
    for d in (1.30, 1.10, 0.90, 1.60, 1.90):
        for lat in (0.0, 0.20, -0.20, 0.40, -0.40, 0.60, -0.60, 0.90, -0.90):
            ex, ey = px + tx * d + lx * lat, py + ty * d + ly * lat
            if R.polyline(nc, F, [(px, py), (px + tx * 0.30, py + ty * 0.30),
                                  (ex, ey)], W, 0.20):
                best = (ex, ey)
                break
        if best:
            break
    if best:
        placed.append((num, p.GetNetname(), round(best[0], 3), round(best[1], 3),
                       "stub, no via"))
    else:
        failed.append((num, p.GetNetname(), "no clear via-less stub"))

print("pass 2: escaped %d more U5 pins" % len(placed))
for num, net, x, y, kind in placed:
    print("   pad %-3s %-11s %-12s at %8.3f %8.3f" % (num, net, kind, x, y))
if failed:
    print("still trapped:")
    for num, net, why in failed:
        print("   pad %-3s %-11s %s" % (num, net, why))
R.save()
print("saved")
