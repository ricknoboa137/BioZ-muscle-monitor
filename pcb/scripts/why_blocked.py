"""Name the obstacle that blocks a given segment, instead of guessing.

Usage: python why_blocked.py NET LAYER x1 y1 x2 y2 [width]
Prints every different-net item whose clearance envelope the segment enters,
with the required clearance for that net pair and the actual gap.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from netclr import ClassRouter
from handroute import mm, T, V

net, layname = sys.argv[1], sys.argv[2]
x1, y1, x2, y2 = [float(v) for v in sys.argv[3:7]]
w = float(sys.argv[7]) if len(sys.argv) > 7 else 0.075

R = ClassRouter()
lay = pcbnew.F_Cu if layname == "F.Cu" else (
    pcbnew.B_Cu if layname == "B.Cu" else R.layer(layname))
nc = R.netcode(net)
sh = pcbnew.SHAPE_SEGMENT(V(x1, y1), V(x2, y2), mm(w))

print("net %s (class %s, clearance %.3f)  %s  w=%.3f" % (
    net, R.cls_of(net), R.clr_of_net(net), layname, w))
print("edge ok:", R._edge_ok([(x1, y1), (x2, y2)], w / 2.0))

# label obstacles by owner
labels = {}
for f in R.board.Footprints():
    for p in f.Pads():
        if p.IsOnLayer(lay):
            labels[id(p)] = "%s.%s" % (f.GetReference(), p.GetNumber())

hits = 0
for f in R.board.Footprints():
    for p in f.Pads():
        if p.GetNetCode() == nc or not p.IsOnLayer(lay):
            continue
        req = R.pair_clearance(net, p.GetNetCode())
        if sh.Collide(p.GetEffectiveShape(lay), mm(req)):
            n = R.board.FindNet(p.GetNetCode())
            q = p.GetPosition()
            print("  PAD  %-8s net=%-10s req=%.3f  at (%.3f,%.3f) size %.3fx%.3f" % (
                "%s.%s" % (f.GetReference(), p.GetNumber()),
                n.GetNetname() if n else "", req, T(q.x), T(q.y),
                T(p.GetSizeX()), T(p.GetSizeY())))
            hits += 1
for t in R.board.GetTracks():
    if t.GetNetCode() == nc or not t.IsOnLayer(lay):
        continue
    req = R.pair_clearance(net, t.GetNetCode())
    if sh.Collide(t.GetEffectiveShape(lay), mm(req)):
        n = R.board.FindNet(t.GetNetCode())
        s, e = t.GetStart(), t.GetEnd()
        isvia = t.GetClass() == "PCB_VIA"
        # KiCad 10: PCB_VIA::GetWidth() asserts without a layer argument
        wd = T(t.GetWidth(lay)) if isvia else T(t.GetWidth())
        print("  %-4s net=%-10s req=%.3f  (%.2f,%.2f)-(%.2f,%.2f) w=%.3f" % (
            "VIA" if isvia else "TRK",
            n.GetNetname() if n else "", req,
            T(s.x), T(s.y), T(e.x), T(e.y), wd))
        hits += 1
print("blockers:", hits)
