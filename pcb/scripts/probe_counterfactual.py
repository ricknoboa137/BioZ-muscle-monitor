"""READ-ONLY counterfactual: is U5's escape blocked by the decoupling CAPS,
or by the existing tracks/vias in the annulus?

Runs the escape_trapped feasibility four ways on an IN-MEMORY board that is
never saved:
  A baseline
  B cluster capacitors deleted outright
  C all tracks+vias in the west/north annulus deleted (caps kept)
  D both
Nothing is written to disk.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from netclr import ClassRouter
from handroute import T

VIA_D, VIA_DR = 0.30, 0.20
TRAPPED = ["nPGOOD", "nCHG", "VDD_nRF", "AFE_CS", "LED_K", "nRESET",
           "DECA_RF", "XL1", "XC1", "XC2", "DCC"]
NOVIA = {"XL1", "XC1", "XC2", "DCC"}
CAPS = "C11 C12 C16 C17 C18 C22 C24".split()
# annulus box: west + north of U5 (U5 crtyd L=26.955 T=11.355 R=34.245 B=18.645)
ANN = (23.5, 9.0, 27.5, 19.5)


def feasible(R, label, ALLCU, u5):
    F = pcbnew.F_Cu
    cx, cy = T(u5.GetPosition().x), T(u5.GetPosition().y)
    rows = []
    for pad in u5.Pads():
        n = R.board.FindNet(pad.GetNetCode())
        net = n.GetNetname() if n else ""
        if net not in TRAPPED:
            continue
        q = pad.GetPosition(); px, py = T(q.x), T(q.y)
        bb = pad.GetBoundingBox()
        hx = (T(bb.GetRight()) - T(bb.GetLeft())) / 2.0
        hy = (T(bb.GetBottom()) - T(bb.GetTop())) / 2.0
        if hx >= hy:
            ux, uy, half = (1.0 if px >= cx else -1.0), 0.0, hx
        else:
            ux, uy, half = 0.0, (1.0 if py >= cy else -1.0), hy
        best = None
        d = half + 0.10
        while d <= half + 2.60 and best is None:
            for lat in (0.0, 0.1, -0.1, 0.2, -0.2, 0.3, -0.3, 0.4, -0.4):
                vx = px + ux * d - uy * lat
                vy = py + uy * d + ux * lat
                for w in (R.trk.get(R.cls_of(net), 0.254), 0.15, 0.127):
                    if w < R.min_track - 1e-9:
                        continue
                    if not R.seg_clear_c((px, py), (round(vx, 4), round(vy, 4)), w, net, F):
                        continue
                    if net in NOVIA:
                        best = (vx, vy, w, d, "stub only"); break
                    if R.in_rule_area(vx, vy, VIA_D / 2.0) or \
                       R.hole_conflict(vx, vy, VIA_DR) or \
                       not R.via_clear_c(vx, vy, VIA_D, net, ALLCU):
                        continue
                    best = (vx, vy, w, d, "via"); break
                if best:
                    break
            d += 0.05
        rows.append((net, pad.GetNumber(), (px, py), best))
    ok = sum(1 for r in rows if r[3])
    print("--- %s : escapable %d of %d ---" % (label, ok, len(rows)))
    for net, num, p, best in sorted(rows):
        if best:
            print("   ESCAPE  %-9s U5.%-3s -> (%.3f,%.3f) d=%.2f %s" % (net, num, best[0], best[1], best[3], best[4]))
        else:
            print("   TRAPPED %-9s U5.%-3s pad(%.2f,%.2f)" % (net, num, p[0], p[1]))
    return ok, len(rows)


def del_caps(R):
    n = 0
    for f in list(R.board.GetFootprints()):
        if f.GetReference() in CAPS:
            R.board.Remove(f); n += 1
    R._invalidate()
    print("   [removed %d cap footprints]" % n)


def del_annulus(R):
    L, Tp, Rt, B = ANN
    doomed = []
    for t in R.board.GetTracks():
        p = t.GetStart()
        x, y = T(p.x), T(p.y)
        q = t.GetEnd()
        x2, y2 = T(q.x), T(q.y)
        if (L <= x <= Rt and Tp <= y <= B) or (L <= x2 <= Rt and Tp <= y2 <= B):
            doomed.append(t)
    for t in doomed:
        R.board.Remove(t)
    R._invalidate()
    print("   [removed %d tracks/vias from annulus %s]" % (len(doomed), ANN))


if __name__ == "__main__":
    # one scenario per process: board.Remove() corrupts the swig proxy for the
    # BOARD object afterwards (GetEnabledLayers() comes back as a bare
    # SwigPyObject), so scenarios cannot share an interpreter.
    # arg1 = label, arg2 = optional board path (a scratch counterfactual copy
    # written by make_counterfactual.py -- in-process Remove() is unusable, it
    # corrupts every swig proxy fetched afterwards).
    which = sys.argv[1] if len(sys.argv) > 1 else "A"
    R = ClassRouter(sys.argv[2]) if len(sys.argv) > 2 else ClassRouter()
    ALLCU = list(R.board.GetEnabledLayers().CuStack())
    u5 = R.fp("U5")
    feasible(R, which, ALLCU, u5)
