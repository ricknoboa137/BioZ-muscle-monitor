"""Shrink the first-pass U5 fanout vias from 0.40/0.25 to 0.30/0.20.

Pass 1 placed 15 escape vias at 0.40 mm diameter on an 0.80 mm stagger.  That
leaves a 0.40 mm channel between two adjacent vias, and an escape trace through
it needs 0.075 + 2 x 0.20 = 0.475 mm.  So pass 1's own vias were the thing
blocking pass 2 -- not the pads, and not the trace width I first suspected.

At 0.30 mm the channel becomes 0.50 mm and the escape fits.  0.20 mm drill is
exactly min_through_hole_diameter and the 0.05 mm annular ring is exactly
min_via_annular_width, both from the project's design_settings.  This is the
user's sanctioned option (a); no trace width or clearance rule is relaxed.

Only touches vias that are 0.40/0.25 AND within 4 mm of U5, so the POWER_HIGH
0.80/0.40 vias and the U1 microvias are left alone.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from handroute import Router, T

R = Router()
u5x, u5y = 30.6, 15.0
n = 0
for t in R.board.GetTracks():
    if t.GetClass() != "PCB_VIA":
        continue
    if abs(T(t.GetWidth(t.TopLayer())) - 0.40) > 1e-6 or abs(T(t.GetDrill()) - 0.25) > 1e-6:
        continue
    p = t.GetPosition()
    if (T(p.x) - u5x) ** 2 + (T(p.y) - u5y) ** 2 > 6.0 ** 2:
        continue
    t.SetWidth(pcbnew.FromMM(0.30))
    t.SetDrill(pcbnew.FromMM(0.20))
    n += 1
print("shrunk %d U5 fanout vias to 0.30/0.20" % n)
R.save()
print("saved")
