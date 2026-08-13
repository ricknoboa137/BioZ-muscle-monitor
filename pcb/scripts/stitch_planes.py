"""Connect power and ground pads to their own plane island with a via.

This is not routing.  Every net handled here already has a plane or a pour
carrying it -- V_SYS, V1P8D, V2P5F, V2P5, VDD_nRF and V1P8A each own an island
on In3.Cu "Power", GNDA and GNDD own In2.Cu "GND" and the F.Cu/B.Cu pours.  A
pad sitting on top of its own plane needs one via, not a trace.  This is the
same technique already used for the U8/U5 thermal via arrays.

For each pad: if the pad centre lies inside its net's filled polygon on a
target layer, try a via at the pad centre first (legal for the big thermal and
QFN pads), then on a ring of offsets for small pads where via-in-pad is not
wanted.  Every candidate is clearance-checked against every other net on every
layer the via passes through.

Isolated pour islands (the GNDD F.Cu fragments) are handled the same way: a via
anywhere inside the island ties it down to the In2.Cu plane.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import math
import pcbnew
from handroute import Router, V, mm, T

R = Router()
ALLCU = list(R.board.GetEnabledLayers().CuStack())
pcbnew.ZONE_FILLER(R.board).Fill(R.board.Zones())

# net -> layers that carry a plane/pour for it, best target first
TARGET = {
    "VDD_nRF": ["Power"], "V_SYS": ["Power"], "V1P8D": ["Power"],
    "V2P5F": ["Power"], "V2P5": ["Power"], "V1P8A": ["Power"],
    "GNDD": ["GND", "B.Cu", "F.Cu"], "GNDA": ["GND", "B.Cu", "F.Cu"],
}

# filled polygons, per (net, layername)
polys = {}
for z in R.board.Zones():
    if z.GetIsRuleArea():
        continue
    for lay in z.GetLayerSet().Seq():
        polys.setdefault((z.GetNetname(), R.board.GetLayerName(lay)), []).append(
            z.GetFilledPolysList(lay))


def inside(net, layname, x, y, margin=0.35):
    for sp in polys.get((net, layname), []):
        if sp.Collide(V(x, y), mm(margin)):
            return True
    return False


DIA, DRILL = 0.60, 0.30
RING = [(0.0, 0.0)] + [(0.55 * math.cos(a * math.pi / 4),
                        0.55 * math.sin(a * math.pi / 4)) for a in range(8)] \
                    + [(0.85 * math.cos(a * math.pi / 4),
                        0.85 * math.sin(a * math.pi / 4)) for a in range(8)]

new_vias = []
placed, skipped = [], []

for f in R.board.Footprints():
    for p in f.Pads():
        net = p.GetNetname()
        if net not in TARGET:
            continue
        px, py = T(p.GetPosition().x), T(p.GetPosition().y)
        nc = p.GetNetCode()
        # already has a via of its own net within 0.35 mm?  leave it alone
        done = False
        for t in R.board.GetTracks():
            if t.GetClass() == "PCB_VIA" and t.GetNetCode() == nc:
                q = t.GetPosition()
                if (T(q.x) - px) ** 2 + (T(q.y) - py) ** 2 < 0.35 ** 2:
                    done = True
                    break
        if done:
            continue

        hit = None
        for layname in TARGET[net]:
            for dx, dy in RING:
                vx, vy = px + dx, py + dy
                if not inside(net, layname, vx, vy):
                    continue
                if R.in_rule_area(vx, vy, DIA / 2.0):
                    continue
                if R.hole_conflict(vx, vy, DRILL, new_vias):
                    continue
                if not R.via_clear(vx, vy, DIA, nc, ALLCU):
                    continue
                # a via off the pad centre needs a stub back to the pad
                if abs(dx) > 1e-9 or abs(dy) > 1e-9:
                    if not R.seg_clear((px, py), (vx, vy), 0.25, nc, p.GetLayer()):
                        continue
                hit = (vx, vy, layname, dx, dy)
                break
            if hit:
                break

        if not hit:
            skipped.append((f.GetReference(), p.GetNumber(), net))
            continue
        vx, vy, layname, dx, dy = hit
        if abs(dx) > 1e-9 or abs(dy) > 1e-9:
            R.add_track(nc, p.GetLayer(), (px, py), (vx, vy), 0.25)
        R.add_via(nc, vx, vy, DIA, DRILL)
        new_vias.append((vx, vy, DRILL))
        placed.append((f.GetReference(), p.GetNumber(), net, layname,
                       round(vx, 3), round(vy, 3)))

print("stitched %d pads to their plane" % len(placed))
for ref, num, net, lay, vx, vy in placed:
    print("   %-5s.%-3s %-9s -> %-6s via %8.3f %8.3f" % (ref, num, net, lay, vx, vy))
if skipped:
    print("no plane under, or no clear via site (%d):" % len(skipped))
    for ref, num, net in skipped:
        print("   %-5s.%-3s %s" % (ref, num, net))
R.save()
print("saved")
