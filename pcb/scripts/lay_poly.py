# lay_poly.py <board> <net> <layer> <width> "x,y;x,y;..."
# Lay a clearance-checked polyline using netclr.ClassRouter (per-net-pair
# clearance, the real KiCad rule), all-or-nothing.  Refills zones and refuses to
# save if unconnected rises (entry 20's pour-severance guard).
# Caveat, same as blockers_report.py: the clearance check walks pads/tracks/vias,
# NOT zone pours -- so the DRC run after this is the authority, not this script.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from netclr import ClassRouter

path, net, layname, w = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
pts = [tuple(float(v) for v in p.split(",")) for p in sys.argv[5].split(";")]

R = ClassRouter(path)
lay = R.board.GetLayerID(layname)

def unconnected(b):
    c = b.GetConnectivity(); c.Build(b)
    return c.GetUnconnectedCount(True)

before = unconnected(R.board)

# report per-segment first so a failure names the offending leg
ok = True
for a, c in zip(pts, pts[1:]):
    if a == c:
        continue
    good = R.seg_clear_c(a, c, w, net, lay)
    print("  seg (%.3f,%.3f)-(%.3f,%.3f) w=%.4f : %s" % (a[0], a[1], c[0], c[1], w,
                                                         "ok" if good else "BLOCKED"))
    ok = ok and good
if not ok:
    print("ABORT: not laid, nothing changed")
    sys.exit(1)

nc = R.netcode(net)
for a, c in zip(pts, pts[1:]):
    if a != c:
        R.add_track(nc, lay, a, c, w)

pcbnew.ZONE_FILLER(R.board).Fill(R.board.Zones())
after = unconnected(R.board)
print("unconnected before=%d after=%d" % (before, after))
if after > before:
    print("ABORT: pour severance / connectivity regression. Not saving.")
    sys.exit(1)
R.board.Save(path)
print("laid %d segments, saved %s" % (len(pts) - 1, path))
