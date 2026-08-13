"""Put the board back on its specified origin.

A Specctra SES import re-places everything relative to the DSN's own origin, and
the last round-trip translated the ENTIRE board by (+28.800, +30.364) mm.  Every
relative dimension survived, so DRC still read 0 and nothing looked wrong -- but
every ABSOLUTE constraint silently stopped meaning anything:

  * the antenna keepout is specified at 25.0-50.0 x 0-6.82 mm
  * the GNDA/GNDD split is specified at x = 20.0
  * mounting holes and connector positions are mechanical, fixed by the enclosure

verify_board.py tests those as absolute rectangles, so on a shifted board it
would have cheerfully reported PASS for a keepout rectangle sitting in empty
space off the edge of the copper.  That is a false pass, which is worse than a
failure.

The delta is derived from Edge.Cuts, not hardcoded: the outline's top-left
corner belongs at (-0.05, -0.05) mm, being a 62 x 44 mm outline drawn with a
0.10 mm line starting at the origin.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from handroute import Router, T

TARGET = (-0.05, -0.05)          # where the Edge.Cuts bounding box must start

R = Router()
x1, y1, x2, y2 = R.edge
dx, dy = TARGET[0] - x1, TARGET[1] - y1
print("edge box is %.5f,%.5f .. %.5f,%.5f  (%.3f x %.3f mm)"
      % (x1, y1, x2, y2, x2 - x1, y2 - y1))
print("translating everything by %+.5f, %+.5f mm" % (dx, dy))

if abs(dx) < 1e-6 and abs(dy) < 1e-6:
    print("already on origin, nothing to do")
    sys.exit(0)

off = pcbnew.VECTOR2I(pcbnew.FromMM(dx), pcbnew.FromMM(dy))
n = 0
for group in (R.board.Footprints(), R.board.GetTracks(),
              R.board.Zones(), R.board.GetDrawings()):
    for item in group:
        item.Move(off)
        n += 1
print("moved %d items" % n)

pcbnew.ZONE_FILLER(R.board).Fill(R.board.Zones())
R.board.Save(R.path)

chk = Router()
print("after: edge box %.5f,%.5f .. %.5f,%.5f" % chk.edge)
print("after: U1.C1 at %.4f,%.4f  (expected 19.8000,25.2000)" % chk.padxy("U1", "C1"))
print("after: R1.1  at %.4f,%.4f  (expected 19.1750,26.0000)" % chk.padxy("R1", "1"))
