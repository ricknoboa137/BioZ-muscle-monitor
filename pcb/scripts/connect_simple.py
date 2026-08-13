"""Close the remaining short hops with simple, clearance-checked geometry.

Scope and honesty about what this is: for each unconnected pair KiCad reports,
it tries a fixed, small catalogue of shapes between the two endpoints -- a
straight run, the two L-shapes, a few Z-shapes, and if F.Cu is blocked a detour
down to In4.Cu "Signal" through a via at each end.  The first shape that is
clear of every other net wins.

There is no rip-up, no net ordering, no cost function and no search over
topology.  It cannot go around an obstacle it was not handed a shape for.  Any
pair it fails on stays unrouted and is listed, not fudged.  That is the whole
difference between this and an autorouter, and it is why the failures below are
reported rather than hidden.

Usage:  python connect_simple.py drc.json
"""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from handroute import Router, T

R = Router()
F, B = pcbnew.F_Cu, pcbnew.B_Cu
SIG = R.layer("Signal")
ALLCU = list(R.board.GetEnabledLayers().CuStack())

WIDE = {"V_SYS": 0.508, "V_BAT": 0.508, "VIN_EXT": 0.508, "V2P5": 0.508,
        "V1P8D": 0.508, "V1P8A": 0.508, "V2P5F": 0.508, "VDD_nRF": 0.508,
        "GNDD": 0.508, "GNDA": 0.508}
DEF_W = 0.254

# Per-class clearance. The global 0.20 mm default is BELOW POWER_HIGH's 0.254,
# which produced a real clearance error on V_BAT the first time round.
CLR = {"VIN_EXT": 0.254, "V_BAT": 0.254, "V_SYS": 0.254}
DEF_CLR = 0.20

drc = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "drc.json"))


def endpoint(item, net):
    """a concrete (x, y, layer) for one end of a ratsnest line"""
    d = item["description"]
    pos = item.get("pos")
    if pos is None:
        return None
    x, y = pos["x"], pos["y"]
    m = re.match(r".*?(?:PTH pad|Pad) (\S+) \[(\w+)\] of (\w+)", d)
    if m:
        p = R.pad(m.group(3), m.group(1))
        q = p.GetPosition()
        lay = F if p.IsOnLayer(F) else B
        return (T(q.x), T(q.y), lay)
    if d.startswith("Via"):
        return (x, y, F)
    if d.startswith("Track"):
        lay = SIG if " on Signal" in d else (B if " on B.Cu" in d else F)
        return (x, y, lay)
    return None            # zones: nothing to aim at


def shapes(a, c):
    ax, ay = a
    cx, cy = c
    out = [[a, c],
           [a, (cx, ay), c],
           [a, (ax, cy), c]]
    for f in (0.35, 0.5, 0.65):
        mx = ax + (cx - ax) * f
        my = ay + (cy - ay) * f
        out.append([a, (mx, ay), (mx, cy), c])
        out.append([a, (ax, my), (cx, my), c])
    return out


done, failed = [], []
seen = set()
for u in drc["unconnected_items"]:
    if len(u["items"]) < 2:
        continue
    net = re.search(r"\[(\w+)\]", u["items"][0]["description"])
    if not net:
        continue
    net = net.group(1)
    e1, e2 = endpoint(u["items"][0], net), endpoint(u["items"][1], net)
    if e1 is None or e2 is None:
        failed.append((net, "endpoint is a zone - needs a stitching via, not a trace"))
        continue
    key = (net, round(e1[0], 2), round(e1[1], 2), round(e2[0], 2), round(e2[1], 2))
    if key in seen:
        continue
    seen.add(key)

    nc = R.netcode(net)
    w = WIDE.get(net, DEF_W)
    clr = CLR.get(net, DEF_CLR)
    a, c = (e1[0], e1[1]), (e2[0], e2[1])
    la, lc = e1[2], e2[2]

    # A trace is drawn between pad CENTRES, so its end cap sticks out half a
    # width beyond the pad centre and can foul the next pad along on a
    # fine-pitch part -- a 0.508 mm power strap between two adjacent QFN pads
    # 0.5 mm apart fails on the neighbours every time.  Try the net-class width
    # first and fall back to narrower ones.  On the power nets the plane
    # carries the current; these straps only have to make the connection.
    ladder = [x for x in (w, 0.3, 0.2, 0.15) if x <= w] or [w]

    ok = False
    # 1. same layer, simple shapes
    if la == lc:
        for ww in ladder:
            for pts in shapes(a, c):
                if R.polyline(nc, la, pts, ww, clr):
                    ok = True
                    break
            if ok:
                break
    # 2. different layers, or blocked: detour through In4 "Signal"
    if not ok:
        for lay in (SIG, B):
            if lay in (la, lc):
                continue
            va = a if la == lay else None
            vc = c if lc == lay else None
            good = True
            queued = []
            for (pt, lay0) in ((a, la), (c, lc)):
                if lay0 == lay:
                    continue
                if R.in_rule_area(pt[0], pt[1], 0.3) or \
                   R.hole_conflict(pt[0], pt[1], 0.3, [q[:3] for q in queued]):
                    good = False
                    break
                if not R.via_clear(pt[0], pt[1], 0.6, nc, ALLCU, clr):
                    good = False
                    break
                queued.append((pt[0], pt[1], 0.3))
            if not good:
                continue
            for ww in ladder:
                for pts in shapes(a, c):
                    if R.polyline(nc, lay, pts, ww, clr):
                        for (vx, vy, dr) in queued:
                            R.add_via(nc, vx, vy, 0.6, 0.3)
                        ok = True
                        break
                if ok:
                    break
            if ok:
                break

    (done if ok else failed).append(
        (net, "%.2f,%.2f -> %.2f,%.2f" % (a[0], a[1], c[0], c[1])))

print("connected %d, failed %d" % (len(done), len(failed)))
for net, s in done:
    print("   OK   %-11s %s" % (net, s))
for net, s in failed:
    print("   FAIL %-11s %s" % (net, s))
R.save()
print("saved")
