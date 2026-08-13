"""Clean up the artifacts entry 17's unfinished U5 fanout left behind.

The board already reads 0 DRC ERRORS.  The "157 violations" are all warnings,
and 141 of them are the silkscreen and courtyard overlaps under the shield frame
that the prior agent recorded as expected.  This script deals with the 10 that
are genuinely entry 17's leftovers, plus one older defect it uncovered.

1. NINE DANGLING FANOUT VIAS.  BTN_N, DECD, MEM_CS, SPI_SDO, SPI_SCK, SWO,
   SWDIO, SWDCLK and FPWM_CTL each got an escape via that was never routed
   onward, so it is a hole drilled for nothing.  Per the instruction to leave
   pins as open ratsnest rather than half-fixed, they and their orphaned stubs
   are removed.  Nothing is lost: fanout_u5.py and fanout_u5_pass2.py are
   deterministic and re-place them in one command when the routing is resumed.

2. ONE CO-LOCATED DRILL PAIR, and this one is older than entry 17 and a real
   manufacturing defect: route_escape.py put a 0.30 mm THROUGH via and a 0.10 mm
   laser MICROVIA at the same point (23.90, 23.20) on AFE_CS.  That is two drills
   in one hole.  The through via already spans F.Cu to B.Cu and therefore already
   reaches the Escape layer, so the microvia is redundant and is the one removed.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from handroute import Router, T

R = Router()

DANGLING = {
    "BTN_N": (34.20, 12.80), "DECD": (27.00, 16.00), "MEM_CS": (34.55, 16.80),
    "SPI_SDO": (34.20, 17.20), "SPI_SCK": (32.80, 18.60), "SWO": (34.20, 15.20),
    "SWDIO": (32.80, 11.40), "SWDCLK": (32.40, 11.05), "FPWM_CTL": (31.60, 11.05),
}
TOL = 0.02


def near(p, xy):
    return abs(T(p.x) - xy[0]) < TOL and abs(T(p.y) - xy[1]) < TOL


doomed = []
for t in R.board.GetTracks():
    net = t.GetNetname()
    if net not in DANGLING:
        continue
    xy = DANGLING[net]
    if t.GetClass() == "PCB_VIA":
        if near(t.GetPosition(), xy):
            doomed.append(("via", net, t))
    else:
        # the orphaned F.Cu stub that fed the via
        if near(t.GetStart(), xy) or near(t.GetEnd(), xy):
            doomed.append(("stub", net, t))

# the redundant AFE_CS microvia
for t in R.board.GetTracks():
    if (t.GetClass() == "PCB_VIA" and t.GetNetname() == "AFE_CS"
            and t.GetViaType() == pcbnew.VIATYPE_MICROVIA
            and near(t.GetPosition(), (23.90, 23.20))):
        doomed.append(("microvia", "AFE_CS", t))

for kind, net, t in doomed:
    p = t.GetPosition()
    print("removing %-8s %-10s at %8.3f %8.3f" % (kind, net, T(p.x), T(p.y)))
    R.board.Remove(t)
print("removed %d items" % len(doomed))

pcbnew.ZONE_FILLER(R.board).Fill(R.board.Zones())
R.board.Save(R.path)
print("saved")
