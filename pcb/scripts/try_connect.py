# try_connect.py <board> <net> "ax,ay" "bx,by" [--layer F.Cu] [--width W]
#                                              [--via-at "x,y"] [--layer2 B.Cu]
# Close ONE ratsnest pair.  Tries a catalogue of candidate paths in order of
# preference (direct, then L both ways, then 45-degree dogleg both ways, at a
# range of corner positions) and lays the FIRST that is clearance-legal along
# every leg.  Refills zones and rebuilds connectivity before judging, and
# refuses to save unless the unconnected count actually FALLS (entry 20's
# pour-severance guard, tightened: for this job "unchanged" is also a failure).
#
# Width defaults to the net class's nominal track width from the .kicad_pro, so
# a connection is never quietly laid under its brief-mandated width.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from netclr import ClassRouter

args = sys.argv[1:]
def opt(name, default=None):
    if name in args:
        return args[args.index(name) + 1]
    return default

path, net = args[0], args[1]
a = tuple(float(v) for v in args[2].split(","))
c = tuple(float(v) for v in args[3].split(","))
layname = opt("--layer", "F.Cu")

R = ClassRouter(path)
b = R.board
lay = b.GetLayerID(layname)
w = float(opt("--width", R.trk.get(R.cls_of(net), R.trk["Default"])))

def unconnected():
    cd = b.GetConnectivity(); cd.Build(b)
    return cd.GetUnconnectedCount(True)

before = unconnected()

def cands(a, c):
    out = [("direct", [a, c])]
    out.append(("L-x-first", [a, (c[0], a[1]), c]))
    out.append(("L-y-first", [a, (a[0], c[1]), c]))
    dx, dy = c[0]-a[0], c[1]-a[1]
    s = min(abs(dx), abs(dy))
    sx = 1 if dx > 0 else -1
    sy = 1 if dy > 0 else -1
    # 45-degree dogleg, diagonal first then straight, and the reverse
    out.append(("diag-first", [a, (a[0]+sx*s, a[1]+sy*s), c]))
    out.append(("diag-last",  [a, (c[0]-sx*s, c[1]-sy*s), c]))
    # offset L corners, to step around a single obstacle at the corner
    for d in (0.4, 0.8, 1.2, -0.4, -0.8, -1.2):
        out.append(("L-x-off%+.1f" % d, [a, (c[0], a[1]+d), (c[0], c[1])]))
        out.append(("L-y-off%+.1f" % d, [a, (a[0]+d, a[1]), (a[0]+d, c[1]), c]))
    return out

def legal(pts):
    bad = []
    for p, q in zip(pts, pts[1:]):
        if p == q:
            continue
        if not R.seg_clear_c(p, q, w, net, lay):
            bad.append((p, q))
    return bad

chosen = None
for name, pts in cands(a, c):
    bad = legal(pts)
    if not bad:
        chosen = (name, pts)
        break
    print("  %-14s blocked on %d/%d legs" % (name, len(bad), len(pts)-1))

if not chosen:
    print("NO CANDIDATE PATH -- nothing changed.  Needs a hand plan (probe_seg.py).")
    sys.exit(2)

name, pts = chosen
nc = R.netcode(net)
for p, q in zip(pts, pts[1:]):
    if p != q:
        R.add_track(nc, lay, p, q, w)
print("chose %s: %s  w=%.4f on %s" % (
    name, " -> ".join("(%.3f,%.3f)" % p for p in pts), w, layname))

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
after = unconnected()
print("unconnected %d -> %d" % (before, after))
if after >= before:
    print("ABORT: did not reduce the unconnected count. Not saving.")
    sys.exit(1)
b.Save(path)
print("saved", path)
