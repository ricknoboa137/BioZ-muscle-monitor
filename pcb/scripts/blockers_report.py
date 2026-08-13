# blockers_report.py [netfilter ...]
# For every SIGNAL/POWER track below its class floor, report:
#   - its geometry
#   - the widest width that IS clearance-legal in place (binary search)
#   - every different-net item that blocks it at the floor width, named
# Read-only.  Does not modify the board.
#
# The floor is a hard rule threshold, so a partial widen buys nothing; the point
# of the max-legal figure is to say how far short we are and whether the
# obstruction is one item or a wall.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from netclr import ClassRouter
from handroute import mm, T, V

FLOORS = {"SIGNAL": 0.254, "POWER_HIGH": 0.508, "POWER_LOW": 0.508}
filt = set(sys.argv[1:])

R = ClassRouter()
b = R.board

# label map for pads
padlabel = {}
for f in b.Footprints():
    for p in f.Pads():
        padlabel[id(p)] = "%s.%s" % (f.GetReference(), p.GetNumber())

def blockers(net, lay, a, c, w):
    sh = pcbnew.SHAPE_SEGMENT(V(*a), V(*c), mm(w))
    nc = R.netcode(net)
    out = []
    for f in b.Footprints():
        for p in f.Pads():
            if p.GetNetCode() == nc or not p.IsOnLayer(lay):
                continue
            req = R.pair_clearance(net, p.GetNetCode())
            if sh.Collide(p.GetEffectiveShape(lay), mm(req)):
                n = b.FindNet(p.GetNetCode())
                out.append("PAD %s.%s net=%s req=%.3f" % (
                    f.GetReference(), p.GetNumber(),
                    n.GetNetname() if n else "", req))
    for t in b.GetTracks():
        if t.GetNetCode() == nc or not t.IsOnLayer(lay):
            continue
        req = R.pair_clearance(net, t.GetNetCode())
        if sh.Collide(t.GetEffectiveShape(lay), mm(req)):
            n = b.FindNet(t.GetNetCode())
            s, e = t.GetStart(), t.GetEnd()
            isvia = isinstance(t, pcbnew.PCB_VIA)
            out.append("%s net=%s req=%.3f (%.3f,%.3f)-(%.3f,%.3f)" % (
                "VIA" if isvia else "TRK", n.GetNetname() if n else "", req,
                T(s.x), T(s.y), T(e.x), T(e.y)))
    return out

rows = []
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        continue
    n = t.GetNet()
    if not n:
        continue
    name = n.GetNetname()
    fl = FLOORS.get(n.GetNetClassName())
    if not fl or t.GetWidth() >= pcbnew.FromMM(fl):
        continue
    if filt and name not in filt:
        continue
    rows.append((name, t, fl))

print("under-width tracks: %d" % len(rows))
for name, t, fl in sorted(rows, key=lambda r: r[0]):
    lay = t.GetLayer()
    s, e = t.GetStart(), t.GetEnd()
    a = (T(s.x), T(s.y)); c = (T(e.x), T(e.y))
    w = T(t.GetWidth())
    # widest legal width in place
    lo, hi = w, fl
    if R.seg_clear_c(a, c, fl, name, lay):
        best = fl
    else:
        best = 0.0
        for _ in range(14):
            mid = (lo + hi) / 2.0
            if R.seg_clear_c(a, c, mid, name, lay):
                lo = mid
            else:
                hi = mid
        best = lo
    print("\n%-12s %-6s (%.3f,%.3f)-(%.3f,%.3f) w=%.4f floor=%.3f maxlegal=%.4f" % (
        name, b.GetLayerName(lay), a[0], a[1], c[0], c[1], w, fl, best))
    if best < fl:
        for bl in blockers(name, lay, a, c, fl):
            print("      " + bl)
