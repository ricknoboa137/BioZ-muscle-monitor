"""The crystal and DCC pins: F.Cu, no vias.

User ruling 2026-08-07 (CHECKPOINT entry 16): these pins sit right beside their
parts, so they escape on the top layer with no via at all.  That is better for
the crystals anyway -- a via in an oscillator loop adds inductance and a stub,
and XC1/XC2 are the 32 MHz loop the radio depends on.

Pairs, each a single hop:
    U5.1  XL1  -> Y1.1        32.768 kHz
    U5.34 XC1  -> Y2.1        32 MHz
    U5.35 XC2  -> Y2.3        32 MHz
    U5.46 DCC  -> C11.1 / L3.1  DC-DC coil node

Geometry catalogue is deliberately small and every candidate is clearance
checked; anything that will not fit is reported, not forced.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from handroute import Router, T

R = Router()
F = pcbnew.F_Cu
W = 0.20                       # SIGNAL class minimum-ish; these are short hops
CLR = 0.20

PAIRS = [
    ("XL1",  ("U5", "1"),  ("Y1", "1")),
    ("XC1",  ("U5", "34"), ("Y2", "1")),
    ("XC2",  ("U5", "35"), ("Y2", "3")),
    ("DCC",  ("U5", "46"), ("C11", "1")),
    ("DCC",  ("C11", "1"), ("C12", "1")),
    ("DCC",  ("L3", "1"),  ("U5", "46")),
]


def escape_point(ref, num, out=0.15):
    """A trace drawn from a pad CENTRE leaves sideways and instantly collides
    with the neighbouring pads on a 0.4 mm-pitch part.  Every real escape runs
    along the pad's long axis first.  Return the point just beyond the pad tip,
    in the direction pointing away from the footprint body."""
    p = R.pad(ref, num)
    px, py = R.padxy(ref, num)
    f = R.fp(ref)
    fx, fy = T(f.GetPosition().x), T(f.GetPosition().y)
    sz = p.GetSize()
    w, h = T(sz.x), T(sz.y)
    if abs(p.GetOrientationDegrees() + f.GetOrientationDegrees()) % 180 > 45:
        w, h = h, w
    # push out along whichever axis the pad is longer on
    if w >= h:
        d = w / 2.0 + out
        sx = 1.0 if px >= fx else -1.0
        return (px + sx * d, py)
    d = h / 2.0 + out
    sy = 1.0 if py >= fy else -1.0
    return (px, py + sy * d)


def shapes(a, c):
    ax, ay = a
    cx, cy = c
    out = [[a, c], [a, (cx, ay), c], [a, (ax, cy), c]]
    for f in (0.25, 0.4, 0.5, 0.6, 0.75):
        mx, my = ax + (cx - ax) * f, ay + (cy - ay) * f
        out.append([a, (mx, ay), (mx, cy), c])
        out.append([a, (ax, my), (cx, my), c])
    # 45-degree dog-legs, which is how a crystal pair is normally drawn
    for f in (0.3, 0.5, 0.7):
        d = min(abs(cx - ax), abs(cy - ay)) * f
        sx = 1 if cx > ax else -1
        sy = 1 if cy > ay else -1
        out.append([a, (ax + sx * d, ay + sy * d), (cx, ay + sy * d), c])
        out.append([a, (ax + sx * d, ay + sy * d), (ax + sx * d, cy), c])

    # PERPENDICULAR DETOURS.  Without these, two pads that share a Y (or an X)
    # collapse every shape above onto the same straight line, so nothing is ever
    # tried that steps around an obstacle sitting between them -- which is
    # exactly the case for DCC, where C12 pad 2 (GNDD) sits between C11 pad 1
    # and C12 pad 1 on y = 16.4.  Step out, run across, step back.
    for d in (0.6, 0.8, 1.0, 1.25, 1.5, 1.9, 2.4):
        for s in (1, -1):
            out.append([a, (ax, ay + s * d), (cx, cy + s * d), c])
            out.append([a, (ax + s * d, ay), (cx + s * d, cy), c])
    return out


ONLY = sys.argv[1:] if len(sys.argv) > 1 else None

ok_n = 0
for net, (r1, p1), (r2, p2) in PAIRS:
    if ONLY and net not in ONLY:
        continue
    pa, pc = R.padxy(r1, p1), R.padxy(r2, p2)
    nc = R.netcode(net)
    done = False
    # The lead-out only exists to get clear of U5's 0.40 mm pad pitch.  Applying
    # it to a two-pad passive pushes the endpoint along the pad axis AWAY from
    # the part we are trying to reach -- for C11.1 -> C12.1 it put the target
    # point on the far side of C12, forcing a loop round the whole component.
    # Fine-pitch parts get the lead-out; everything else is approached at the
    # pad centre and the detour shapes do the work.
    FINE = ("U5",)
    for lead in (0.15, 0.35, 0.60):
        for w in (W, 0.15, 0.1, 0.075):
            a = escape_point(r1, p1, lead) if r1 in FINE else pa
            c = escape_point(r2, p2, lead) if r2 in FINE else pc
            for body in shapes(a, c):
                pts = [pa] + body + [pc]
                if R.polyline(nc, F, pts, w, CLR):
                    print("OK   %-5s %s.%s -> %s.%s  at %.3f mm, lead %.2f, %d segs"
                          % (net, r1, p1, r2, p2, w, lead, len(pts) - 1))
                    done = True
                    ok_n += 1
                    break
            if done:
                break
        if done:
            break
    if not done:
        print("FAIL %-5s %s.%s -> %s.%s  no clear F.Cu shape" % (net, r1, p1, r2, p2))

print("routed %d of %d" % (ok_n, len(PAIRS)))
R.save()
print("saved")
