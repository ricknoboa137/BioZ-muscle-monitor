"""Escape feasibility for the trapped U5 pins, with the corrected per-class
clearance model and a proper fine-pitch lead-out.

"Trapped" on this board has always meant the pin cannot get OFF its pad into
free space -- not that its whole net is unrouted.  The long hauls (nPGOOD is
24 mm across a congested board) are ordinary obstacle-avoiding routing and
belong to Freerouting.  This script answers only the escape question, per pin:

  lead out along the pad's long axis, then find the nearest point along that
  escape where a 0.30/0.20 mm via clears everything at the REAL pair clearance.

Usage: python escape_trapped.py [--place]     (default: report only)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from netclr import ClassRouter
from handroute import T

PLACE = "--place" in sys.argv
VIA_D, VIA_DR = 0.30, 0.20

# the 11 trapped pins, as (net, U5 pad number).  Pad numbers are read off the
# board below, not asserted -- the tuple is only the work list.
TRAPPED = ["nPGOOD", "nCHG", "VDD_nRF", "AFE_CS", "LED_K", "nRESET",
           "DECA_RF", "XL1", "XC1", "XC2", "DCC"]
NOVIA = {"XL1", "XC1", "XC2", "DCC"}

R = ClassRouter()
F = pcbnew.F_Cu
ALLCU = list(R.board.GetEnabledLayers().CuStack())
u5 = R.fp("U5")
cx, cy = T(u5.GetPosition().x), T(u5.GetPosition().y)

rows = []
for pad in u5.Pads():
    n = R.board.FindNet(pad.GetNetCode())
    net = n.GetNetname() if n else ""
    if net not in TRAPPED:
        continue
    q = pad.GetPosition()
    px, py = T(q.x), T(q.y)
    bb = pad.GetBoundingBox()
    hx = (T(bb.GetRight()) - T(bb.GetLeft())) / 2.0
    hy = (T(bb.GetBottom()) - T(bb.GetTop())) / 2.0
    # outward direction: along the pad's long axis, away from package centre
    if hx >= hy:
        ux, uy, half = (1.0 if px >= cx else -1.0), 0.0, hx
    else:
        ux, uy, half = 0.0, (1.0 if py >= cy else -1.0), hy

    best = None
    # walk outward; at each distance also try a small lateral shuffle
    d = half + 0.10
    while d <= half + 2.60 and best is None:
        for lat in (0.0, 0.1, -0.1, 0.2, -0.2, 0.3, -0.3, 0.4, -0.4):
            vx = px + ux * d - uy * lat
            vy = py + uy * d + ux * lat
            stub = [(px, py), (round(vx, 4), round(vy, 4))]
            for w in (R.trk.get(R.cls_of(net), 0.254), 0.15, 0.10, R.min_track):
                if w < R.min_track - 1e-9:
                    continue
                if not R.seg_clear_c(stub[0], stub[1], w, net, F):
                    continue
                if net in NOVIA:
                    best = (round(vx, 4), round(vy, 4), w, d, "stub only (no via allowed)")
                    break
                if R.in_rule_area(vx, vy, VIA_D / 2.0) or \
                   R.hole_conflict(vx, vy, VIA_DR) or \
                   not R.via_clear_c(vx, vy, VIA_D, net, ALLCU):
                    continue
                best = (round(vx, 4), round(vy, 4), w, d, "via 0.30/0.20")
                break
            if best:
                break
        d += 0.05
    rows.append((net, pad.GetNumber(), (px, py), best))

ok = 0
for net, num, p, best in sorted(rows):
    if best:
        ok += 1
        print("ESCAPE  %-9s U5.%-3s pad(%.2f,%.2f) -> (%.3f,%.3f) w=%.3f d=%.2f  %s"
              % (net, num, p[0], p[1], best[0], best[1], best[2], best[3], best[4]))
    else:
        print("TRAPPED %-9s U5.%-3s pad(%.2f,%.2f)  no escape within 2.6 mm"
              % (net, num, p[0], p[1]))
print("escapable %d of %d pads" % (ok, len(rows)))
