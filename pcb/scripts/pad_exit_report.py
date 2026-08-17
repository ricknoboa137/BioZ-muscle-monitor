# pad_exit_report.py <board> <pairfile>
# THE decisive measurement for the remaining ratsnest.  For each endpoint of
# each unconnected pair, find the pad there and report:
#   - the pad's own dimensions
#   - the net class floor the brief demands for that net
#   - the widest track that can ACTUALLY leave that pad, measured by trying a
#     short 0.3 mm stub in 16 directions and binary-searching the width
# If the third number is below the second, that connection cannot be made at
# the brief width no matter how it is routed -- it is a land-pattern limit, not
# a congestion problem, and no amount of re-routing will change it.
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from netclr import ClassRouter

FLOORS = {"SIGNAL": 0.254, "POWER_HIGH": 0.508, "POWER_LOW": 0.508,
          "ANALOG_SENSE": 0.254, "PATIENT": 0.3048}
STUB = 0.30

R = ClassRouter(sys.argv[1])
b = R.board
T = pcbnew.ToMM

padat = {}
for f in b.Footprints():
    for p in f.Pads():
        c = p.GetCenter()
        padat[(round(T(c.x), 2), round(T(c.y), 2))] = (f, p)

def exitwidth(pt, net, floor):
    """widest stub that can leave this point in the best of 16 directions"""
    best, bestdir = 0.0, None
    for k in range(16):
        th = k * math.pi / 8.0
        q = (pt[0] + STUB * math.cos(th), pt[1] + STUB * math.sin(th))
        for L in (b.GetLayerID("F.Cu"),):
            if R.seg_clear_c(pt, q, floor, net, L):
                return floor, k
            lo, hi = 0.0, floor
            for _ in range(12):
                mid = (lo + hi) / 2.0
                if R.seg_clear_c(pt, q, mid, net, L):
                    lo = mid
                else:
                    hi = mid
            if lo > best:
                best, bestdir = lo, k
    return best, bestdir

rows = []
for line in open(sys.argv[2]):
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    parts = line.split("|")
    net = parts[0]
    for spec in parts[1:3]:
        pt = tuple(float(v) for v in spec.split(","))
        cls = R.cls_of(net)
        floor = FLOORS.get(cls, 0.254)
        key = (round(pt[0], 2), round(pt[1], 2))
        fp = padat.get(key)
        if fp:
            f, p = fp
            sz = p.GetSize(p.GetLayer())
            what = "%s.%s %s %.3fx%.3f" % (f.GetReference(), p.GetNumber(),
                                           f.GetFPIDAsString().split(":")[-1][:24],
                                           T(sz.x), T(sz.y))
        else:
            what = "(track/via end)"
        w, d = exitwidth(pt, net, floor)
        rows.append((net, cls, floor, w, what, pt))

print("%-10s %-11s %6s %6s  %-34s %s" % ("net", "class", "floor", "maxexit", "endpoint", "at"))
short = 0
for net, cls, floor, w, what, pt in rows:
    flag = ""
    if w < floor - 0.0005:
        flag = "  <-- CANNOT EMIT BRIEF WIDTH"
        short += 1
    print("%-10s %-11s %6.3f %6.3f  %-34s (%.3f,%.3f)%s" % (
        net, cls, floor, w, what, pt[0], pt[1], flag))
print("\n%d of %d endpoints cannot emit their brief-mandated width" % (short, len(rows)))
