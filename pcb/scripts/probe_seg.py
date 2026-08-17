# probe_seg.py <board> <net> <layer> <width> "x1,y1" "x2,y2"
# Name every item that blocks a CANDIDATE segment that does not exist yet, with
# the clearance required for that net pair and the actual gap.  blockers_report.py
# only works on tracks already on the board; this is for planning a new run.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from netclr import ClassRouter
from handroute import mm, T, V

path, net, layname, w = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
a = tuple(float(v) for v in sys.argv[5].split(","))
c = tuple(float(v) for v in sys.argv[6].split(","))

R = ClassRouter(path)
b = R.board
lay = b.GetLayerID(layname)
nc = R.netcode(net)
sh = pcbnew.SHAPE_SEGMENT(V(*a), V(*c), mm(w))

print("candidate %s %s (%.3f,%.3f)-(%.3f,%.3f) w=%.4f" % (net, layname, a[0], a[1], c[0], c[1], w))
n = 0
for f in b.Footprints():
    for p in f.Pads():
        if p.GetNetCode() == nc or not p.IsOnLayer(lay):
            continue
        req = R.pair_clearance(net, p.GetNetCode())
        if sh.Collide(p.GetEffectiveShape(lay), mm(req)):
            nn = b.FindNet(p.GetNetCode())
            ctr = p.GetCenter()
            print("  PAD %s.%s net=%s req=%.3f at (%.3f,%.3f)" % (
                f.GetReference(), p.GetNumber(), nn.GetNetname() if nn else "",
                req, T(ctr.x), T(ctr.y)))
            n += 1
for t in b.GetTracks():
    if t.GetNetCode() == nc or not t.IsOnLayer(lay):
        continue
    req = R.pair_clearance(net, t.GetNetCode())
    if sh.Collide(t.GetEffectiveShape(lay), mm(req)):
        nn = b.FindNet(t.GetNetCode())
        s, e = t.GetStart(), t.GetEnd()
        isvia = isinstance(t, pcbnew.PCB_VIA)
        print("  %s net=%s req=%.3f (%.3f,%.3f)-(%.3f,%.3f)%s" % (
            "VIA" if isvia else "TRK", nn.GetNetname() if nn else "", req,
            T(s.x), T(s.y), T(e.x), T(e.y),
            (" dia=%.3f" % T(t.GetWidth(t.TopLayer()))) if isvia else ""))
        n += 1
print("blockers: %d" % n)
