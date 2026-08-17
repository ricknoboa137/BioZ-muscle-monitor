# padstub_fix.py <board>
# Decision 1, copper half.  Before ANY rule exception is written, take every
# micron of width that is actually available:
#   - split V2P5's 2.412 mm run so only the pinched 0.70 mm tip stays narrow and
#     the remaining 1.71 mm carries the full 0.508 brief floor
#   - widen every other pad-exit stub to its measured widest clearance-legal width
# Refills zones and rebuilds connectivity before judging (entry 51's rule), and
# refuses to save on any connectivity regression (entry 20's pour-severance guard).
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from netclr import ClassRouter

R = ClassRouter(sys.argv[1] if len(sys.argv) > 1 else None)
b = R.board
T = pcbnew.ToMM

def unconnected():
    c = b.GetConnectivity(); c.Build(b)
    return c.GetUnconnectedCount(True)

before = unconnected()
print("unconnected before = %d" % before)

def near(p, q):
    return abs(p[0]-q[0]) < 0.002 and abs(p[1]-q[1]) < 0.002

def find(net, x1, y1, x2, y2):
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        n = t.GetNet()
        if not n or n.GetNetname() != net:
            continue
        s, e = t.GetStart(), t.GetEnd()
        a, c = (T(s.x), T(s.y)), (T(e.x), T(e.y))
        if near(a, (x1, y1)) and near(c, (x2, y2)):
            return t, a, c, False
        if near(a, (x2, y2)) and near(c, (x1, y1)):
            return t, c, a, True
    return None, None, None, None

def maxlegal(net, lay, a, c, cap):
    """widest clearance-legal width for this segment, capped"""
    if R.seg_clear_c(a, c, cap, net, lay):
        return cap
    lo, hi = 0.0, cap
    for _ in range(16):
        mid = (lo+hi)/2.0
        if R.seg_clear_c(a, c, mid, net, lay):
            lo = mid
        else:
            hi = mid
    return lo

# ---- 1. split V2P5 -------------------------------------------------------
# A end (41.750,18.762) is the U7.13 pad end and is the pinched one (0.607 mm).
t, a, c, flipped = find("V2P5", 41.750, 18.762, 41.750, 16.350)
assert t is not None, "V2P5 segment not found"
lay = t.GetLayer()
L = ((a[0]-c[0])**2 + (a[1]-c[1])**2) ** 0.5
f = 0.70 / L
split = (a[0] + (c[0]-a[0])*f, a[1] + (c[1]-a[1])*f)
tipw = maxlegal("V2P5", lay, a, split, 0.508)
restok = R.seg_clear_c(split, c, 0.508, "V2P5", lay)
print("V2P5 split at (%.3f,%.3f): tip maxlegal %.4f, remainder legal at 0.508 = %s"
      % (split[0], split[1], tipw, restok))
assert restok, "remainder not legal at floor -- abort"
tipw = min(tipw, 0.300)                      # never exceed the U7 pad width
t.SetWidth(pcbnew.FromMM(tipw))
if flipped:
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(split[0]), pcbnew.FromMM(split[1])))
else:
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(split[0]), pcbnew.FromMM(split[1])))
R.add_track(R.netcode("V2P5"), lay, split, c, 0.508)
print("  tip  (%.3f,%.3f)-(%.3f,%.3f) w=%.4f  [needs exception]" % (a[0], a[1], split[0], split[1], tipw))
print("  rest (%.3f,%.3f)-(%.3f,%.3f) w=0.5080  [full brief floor, no exception]"
      % (split[0], split[1], c[0], c[1]))

# ---- 2. widen the remaining stubs in place -------------------------------
STUBS = [
    ("VDD_nRF",    32.000, 18.250, 32.000, 18.550, 0.200),
    ("VDD_nRF",    33.850, 13.600, 34.200, 13.600, 0.200),
    ("VDD_nRF",    27.350, 16.800, 27.000, 16.800, 0.200),
    ("VDD_nRF",    28.400, 11.750, 27.600, 11.400, 0.200),
    ("AFE_PWR_EN", 31.200, 11.750, 31.310, 11.400, 0.254),
    ("AFE_PWR_EN", 31.200, 11.750, 31.200, 12.050, 0.254),
]
for net, x1, y1, x2, y2, cap in STUBS:
    t, a, c, _ = find(net, x1, y1, x2, y2)
    if t is None:
        print("MISSING %s (%.3f,%.3f)-(%.3f,%.3f)" % (net, x1, y1, x2, y2))
        continue
    w0 = T(t.GetWidth())
    best = maxlegal(net, t.GetLayer(), a, c, cap)
    if best > w0 + 0.0005:
        t.SetWidth(pcbnew.FromMM(best))
        print("%-11s (%.3f,%.3f)-(%.3f,%.3f)  %.4f -> %.4f" % (net, a[0], a[1], c[0], c[1], w0, best))
    else:
        print("%-11s (%.3f,%.3f)-(%.3f,%.3f)  %.4f  already at max (%.4f)"
              % (net, a[0], a[1], c[0], c[1], w0, best))

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
after = unconnected()
print("unconnected after = %d" % after)
if after > before:
    print("ABORT: connectivity regression, not saving")
    sys.exit(1)
b.Save(b.GetFileName())
print("saved", b.GetFileName())
