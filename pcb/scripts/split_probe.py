# split_probe.py <board>
# For each of entry 52's under-width segments, find how far along it the FULL
# class floor width becomes clearance-legal.  If that distance is short, the
# segment is not "package-determined" as a whole -- only its pad-exit tip is, and
# the honest fix is to SPLIT it: a short tip at the pad width (covered by the
# scoped exception) plus the remainder at the full brief floor.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from netclr import ClassRouter

FLOORS = {"SIGNAL": 0.254, "POWER_HIGH": 0.508, "POWER_LOW": 0.508}
R = ClassRouter(sys.argv[1] if len(sys.argv) > 1 else None)
b = R.board
T = pcbnew.ToMM

rows = []
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        continue
    n = t.GetNet()
    if not n:
        continue
    fl = FLOORS.get(n.GetNetClassName())
    if not fl or t.GetWidth() >= pcbnew.FromMM(fl):
        continue
    rows.append((n.GetNetname(), t, fl))

def lerp(a, c, f):
    return (a[0] + (c[0]-a[0])*f, a[1] + (c[1]-a[1])*f)

print("%-11s %-32s %6s %7s  %s" % ("net", "segment", "w", "len", "floor-legal from each end"))
for name, t, fl in sorted(rows, key=lambda r: r[0]):
    lay = t.GetLayer()
    s, e = t.GetStart(), t.GetEnd()
    a, c = (T(s.x), T(s.y)), (T(e.x), T(e.y))
    w = T(t.GetWidth())
    L = ((a[0]-c[0])**2 + (a[1]-c[1])**2) ** 0.5
    if R.seg_clear_c(a, c, fl, name, lay):
        note = "WHOLE SEGMENT ALREADY LEGAL AT FLOOR"
    else:
        # trim from the 'a' end: smallest f such that [lerp(a,c,f), c] is legal
        def trim(p, q):
            lo, hi = 0.0, 1.0
            if not R.seg_clear_c(lerp(p, q, 0.999), q, fl, name, lay):
                return None
            for _ in range(16):
                mid = (lo+hi)/2.0
                if R.seg_clear_c(lerp(p, q, mid), q, fl, name, lay):
                    hi = mid
                else:
                    lo = mid
            return hi*L
        ta = trim(a, c)
        tc = trim(c, a)
        note = "trim %s from A, %s from C" % (
            ("%.3fmm" % ta) if ta is not None else "IMPOSSIBLE",
            ("%.3fmm" % tc) if tc is not None else "IMPOSSIBLE")
    print("%-11s (%.3f,%.3f)-(%.3f,%.3f) %6.4f %7.3f  %s" % (
        name, a[0], a[1], c[0], c[1], w, L, note))
