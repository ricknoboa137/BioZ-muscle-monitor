"""Fan U5 out.

U5 is a QFN48 on 0.40 mm pitch: 0.20 x 0.80 mm pads with a 0.20 mm gap between
neighbours.  A 0.40 mm via cannot pass between two pads, so every escape has to
leave the package footprint before it can drop a via.  Freerouting's fanout
stage escaped 0 of U5's pins, which is why nearly every remaining ratsnest in
the board terminates on a U5 pad.

Method, per pad: step outward from the pad's outer tip along the side normal,
trying a grid of candidate via positions (increasing distance, then lateral
offset both ways).  Take the first candidate where BOTH the via and the trace
that reaches it are clear of every other net on every layer they touch.  A pad
that finds nothing is reported, not fudged.

Vias are 0.40 / 0.25 mm through: annular ring 0.075 mm against a 0.05 mm
minimum, hole 0.25 mm against a 0.20 mm minimum.  Both from the project's own
design_settings, not from memory.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from handroute import Router

R = Router()
F = pcbnew.F_Cu

u5 = R.fp("U5")
# side normals: which way is "out" for each perimeter row
SIDES = {
    "S": (0.0,  1.0),   # y = 17.95 row, escapes south
    "E": (1.0,  0.0),   # x = 33.55 col, escapes east
    "N": (0.0, -1.0),   # y = 12.05 row, escapes north
    "W": (-1.0, 0.0),   # x = 27.65 col, escapes west
}


def side_of(x, y):
    if abs(y - 17.95) < 0.01:
        return "S"
    if abs(x - 33.55) < 0.01:
        return "E"
    if abs(y - 12.05) < 0.01:
        return "N"
    if abs(x - 27.65) < 0.01:
        return "W"
    return None


# pads that still need to reach something, from the DRC ratsnest
WANT = [1, 2, 6, 7, 8, 10, 12, 13, 14, 15, 16, 18, 22, 23, 24,
        25, 26, 27, 28, 29, 30, 33, 34, 35, 36, 45, 46, 47, 48]

PAD_HALF = 0.40          # pads are 0.80 long, so the tip is 0.40 from centre
W = 0.15                 # escape trace width, well over the 0.075 minimum
DIA, DRILL = 0.40, 0.25

DISTS = [0.65, 0.90, 1.15, 1.40, 1.70, 2.00, 2.35, 2.70, 3.10, 3.50, 4.00]
LATS = [0.0, 0.40, -0.40, 0.80, -0.80, 1.20, -1.20, 1.60, -1.60,
        2.00, -2.00, 2.40, -2.40]

# A via already placed on the SAME net is not an obstacle, so a greedy search
# will happily stack two vias on one spot (pads 47 and 48 are both VDD_nRF and
# did exactly that on the first run).  Keep every new via 0.6 mm from every
# other new via regardless of net.
new_vias = []


def spaced(vx, vy):
    return all((vx - ax) ** 2 + (vy - ay) ** 2 >= 0.6 ** 2 for ax, ay in new_vias)


placed, failed = [], []
for num in WANT:
    p = R.pad("U5", num)
    net = p.GetNetname()
    px, py = R.padxy("U5", num)
    s = side_of(px, py)
    if s is None:
        failed.append((num, net, "pad is not on a perimeter row"))
        continue
    nx, ny = SIDES[s]
    tx, ty = nx or 0.0, ny or 0.0
    # tangent direction along the row
    lx, ly = (1.0, 0.0) if s in ("S", "N") else (0.0, 1.0)
    # start just inside the pad tip so the stub is genuinely attached
    sx, sy = px + tx * (PAD_HALF - 0.10), py + ty * (PAD_HALF - 0.10)
    nc = p.GetNetCode()

    hit = None
    for d in DISTS:
        for lat in LATS:
            vx = px + tx * d + lx * lat
            vy = py + ty * d + ly * lat
            if not spaced(vx, vy):
                continue
            if not R.via_clear(vx, vy, DIA, nc, list(R.board.GetEnabledLayers().CuStack())):
                continue
            if not R.seg_clear((sx, sy), (vx, vy), W, nc, F):
                continue
            hit = (vx, vy)
            break
        if hit:
            break

    if not hit:
        failed.append((num, net, "no clear via site within 2.7 mm"))
        continue
    vx, vy = hit
    new_vias.append((vx, vy))
    R.add_track(nc, F, (sx, sy), (vx, vy), W)
    R.add_via(nc, vx, vy, DIA, DRILL)
    placed.append((num, net, round(vx, 3), round(vy, 3)))

print("fanned out %d of %d U5 pads" % (len(placed), len(WANT)))
for num, net, vx, vy in placed:
    print("   pad %-3s %-12s via at %8.3f %8.3f" % (num, net, vx, vy))
if failed:
    print("FAILED:")
    for num, net, why in failed:
        print("   pad %-3s %-12s %s" % (num, net, why))
R.save()
print("saved")
