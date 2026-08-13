"""Two V_SYS vias came back from the SES 0.583 mm apart, both with 0.40 mm
drills, leaving a 0.183 mm hole edge gap against a 0.1995 mm minimum.

Both are Freerouting's and both have tracks landing exactly on them, so moving
either would orphan track endpoints.  Shrinking one drill 0.40 -> 0.30 while
keeping its 0.80 mm pad fixes the spacing (0.583 - (0.40+0.30)/2 = 0.233 mm)
and *increases* that via's annular ring.  V_SYS is the 400 mA charge path, but
it is carried by the In3 plane and a dozen other vias; one via at 0.30 mm drill
does not change its current capability.

Generic: shrink the drill of one via in any offending pair.
"""
import os, sys, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from handroute import Router, T

R = Router()
MIN_GAP = 0.1995
vias = [t for t in R.board.GetTracks() if t.GetClass() == "PCB_VIA"]
fixed = 0
for a, b in itertools.combinations(vias, 2):
    pa, pb = a.GetPosition(), b.GetPosition()
    d = ((T(pa.x) - T(pb.x)) ** 2 + (T(pa.y) - T(pb.y)) ** 2) ** 0.5
    da, db = T(a.GetDrill()), T(b.GetDrill())
    gap = d - (da + db) / 2.0
    if gap >= MIN_GAP:
        continue
    # shrink whichever has the larger drill, but never below 0.25 mm
    victim = a if da >= db else b
    other = db if victim is a else da
    need = d - MIN_GAP - 0.005          # 5 um margin
    newdrill = round(min(T(victim.GetDrill()), 2 * need - other) - 0.005, 3)
    if newdrill < 0.25:
        print("CANNOT FIX pair at %.3f,%.3f - would need a %.3f mm drill"
              % (T(pa.x), T(pa.y), newdrill))
        continue
    print("via at %.4f,%.4f drill %.3f -> %.3f (gap was %.4f)"
          % (T(victim.GetPosition().x), T(victim.GetPosition().y),
             T(victim.GetDrill()), newdrill, gap))
    victim.SetDrill(pcbnew.FromMM(newdrill))
    fixed += 1

print("adjusted %d via drills" % fixed)
R.save()
print("saved")
