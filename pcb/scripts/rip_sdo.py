"""Rip SPI_SDO's In4 "Signal" run (plus its through via and the F.Cu stub that
feeds it) back to ratsnest, freeing the x=26.42 cap ground-pad column so C17.2
and C24.2 can be stitched.

Why ripping and not moving: see CHECKPOINT entry 25.  move_sdo.py proved there is
no legal alternative x within +/-3.0 mm (through vias block every layer), and
SPI_SDO is class SIGNAL whose width floor equals its nominal, so it cannot be
thinned either.  It is a non-critical net -- NOT brief 11 category 1 -- so
Freerouting re-routes it in the next pass, with the new stitches as obstacles.

This DELIBERATELY allows unconnected to rise; that is the point.  The F.Cu
segments near U1 (the 0.075/0.150 escape end) are NOT touched.

Usage: python rip_sdo.py [--place]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from netclr import ClassRouter
from handroute import T

PLACE = "--place" in sys.argv
NET = "SPI_SDO"
OLD_X = 26.470
Y_TOP = 14.130

R = ClassRouter()
nc = R.netcode(NET)
SIGNAL = R.layer("Signal")


def unconnected():
    pcbnew.ZONE_FILLER(R.board).Fill(R.board.Zones())
    cn = R.board.GetConnectivity()
    cn.Build(R.board)
    cn.RecalculateRatsnest()
    return cn.GetUnconnectedCount(False)


BASE = unconnected()
print("baseline unconnected: %d" % BASE)

victims = []
for t in R.board.GetTracks():
    if t.GetNetCode() != nc:
        continue
    if t.GetClass() == "PCB_VIA":
        p = t.GetPosition()
        if abs(T(p.x) - OLD_X) < 1e-3 and abs(T(p.y) - Y_TOP) < 1e-3:
            victims.append(("via at (%.3f,%.3f)" % (T(p.x), T(p.y)), t))
        continue
    if t.IsOnLayer(SIGNAL):
        s, e = t.GetStart(), t.GetEnd()
        victims.append(("Signal (%.3f,%.3f)->(%.3f,%.3f)" %
                        (T(s.x), T(s.y), T(e.x), T(e.y)), t))
        continue
    # the F.Cu stub that only existed to reach that via
    s, e = t.GetStart(), t.GetEnd()
    if abs(T(e.x) - OLD_X) < 1e-3 and abs(T(e.y) - Y_TOP) < 1e-3:
        victims.append(("F.Cu stub (%.3f,%.3f)->(%.3f,%.3f)" %
                        (T(s.x), T(s.y), T(e.x), T(e.y)), t))

print("items to remove:")
for d, _ in victims:
    print("   ", d)
if not PLACE:
    print("dry run - pass --place to apply")
    sys.exit(0)

for _, t in victims:
    R.board.Remove(t)

after = unconnected()
print("unconnected after rip: %d (was %d, delta %+d - a rise is EXPECTED)"
      % (after, BASE, after - BASE))
R.save()
print("saved.")
