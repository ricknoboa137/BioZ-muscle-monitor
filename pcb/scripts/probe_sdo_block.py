"""Control experiment: run the same clearance check on SPI_SDO's vertical at its
CURRENT, DRC-clean x, and name the items that collide."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from netclr import ClassRouter
from handroute import T, V, mm

R = ClassRouter()
SIGNAL = R.layer("Signal")
NET = "SPI_SDO"
nc = R.netcode(NET)
W = 0.2540
Y_TOP, Y_BOT = 14.130, 23.210

for X in (26.470, 26.520, 25.970, 27.470):
    ok = R.seg_clear_c((X, Y_TOP), (X, Y_BOT), W, NET, SIGNAL)
    print("x=%.3f  seg_clear_c -> %s%s" %
          (X, ok, "   <-- CURRENT POSITION" if abs(X - 26.470) < 1e-6 else ""))

import sys as _s
X = float(_s.argv[1]) if len(_s.argv) > 1 else 26.470
print("\n--- what collides with the vertical at x=%.3f ---" % X)
sh = pcbnew.SHAPE_SEGMENT(V(X, Y_TOP), V(X, Y_BOT), mm(W))
x1, y1, x2, y2 = R.edge
print("edge box: %.3f,%.3f .. %.3f,%.3f ; halfwidth+clear needs margin" %
      (x1, y1, x2, y2))
print("edge_ok:", R._edge_ok([(X, Y_TOP), (X, Y_BOT)], W / 2.0))

hits = []
for f in R.board.Footprints():
    for p in f.Pads():
        if p.GetNetCode() == nc or not p.IsOnLayer(SIGNAL):
            continue
        need = R.pair_clearance(NET, p.GetNetCode())
        if sh.Collide(p.GetEffectiveShape(SIGNAL), mm(need)):
            q = p.GetPosition()
            hits.append("pad %s.%s [%s] at (%.3f,%.3f) need %.3f" %
                        (f.GetReference(), p.GetNumber(), p.GetNetname(),
                         T(q.x), T(q.y), need))
for t in R.board.GetTracks():
    if t.GetNetCode() == nc or not t.IsOnLayer(SIGNAL):
        continue
    need = R.pair_clearance(NET, t.GetNetCode())
    if sh.Collide(t.GetEffectiveShape(SIGNAL), mm(need)):
        q = t.GetPosition()
        hits.append("%s [%s] at (%.3f,%.3f) need %.3f" %
                    (t.GetClass(), t.GetNetname(), T(q.x), T(q.y), need))
for h in hits[:25]:
    print("  ", h)
print("total blockers at current position:", len(hits))
