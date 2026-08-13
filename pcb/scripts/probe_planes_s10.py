"""Read-only: what islands exist on the internal GND/Power planes, and where.
Needed because for a POWER/GND net the cheapest legal closure is a via at each
open endpoint down into that net's own plane island -- no track at all."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from netclr import ClassRouter, T

r = ClassRouter()
b = r.board
for lname in ("GND", "Power", "Signal", "Escape"):
    lid = r.layer(lname)
    print("== %s (id %d) ==" % (lname, lid))
    for z in b.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(lid):
            continue
        bb = z.GetBoundingBox()
        print("   zone %-16s net=%-10s (%.2f,%.2f)-(%.2f,%.2f)" % (
            z.GetZoneName() or "-", z.GetNetname(),
            T(bb.GetLeft()), T(bb.GetTop()), T(bb.GetRight()), T(bb.GetBottom())))
