"""Read-only: U8's pad geometry and the widths of tracks that ALREADY land on
its pads.  If existing, DRC-clean routing on this package uses widths below the
POWER class floor, then either those tracks are a latent violation or the floor
does not bind the way route_s10 assumes -- either answer changes what I place."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from netclr import ClassRouter, T

R = ClassRouter()
b = R.board
for ref in ("U8", "U7", "U5"):
    f = R.fp(ref)
    fc = f.GetPosition()
    print("== %s centre (%.3f,%.3f) ==" % (ref, T(fc.x), T(fc.y)))
    for p in f.Pads():
        sz = p.GetSize(p.GetPrincipalLayer())
        q = p.GetPosition()
        print("   pad %-4s net=%-10s pos=(%8.3f,%8.3f) size=%.3fx%.3f" % (
            p.GetNumber(), p.GetNetname(), T(q.x), T(q.y), T(sz.x), T(sz.y)))
    if ref != "U8":
        continue
    print("   -- tracks whose end lands on a %s pad --" % ref)
    pads = [(T(p.GetPosition().x), T(p.GetPosition().y), p.GetNumber(),
             p.GetNetname()) for p in f.Pads()]
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            continue
        for end in (t.GetStart(), t.GetEnd()):
            ex, ey = T(end.x), T(end.y)
            for px, py, num, netn in pads:
                if abs(ex - px) < 0.06 and abs(ey - py) < 0.06:
                    print("      pad %-4s net=%-10s track w=%.4f layer=%s" % (
                        num, netn, T(t.GetWidth()),
                        b.GetLayerName(t.GetLayer())))
