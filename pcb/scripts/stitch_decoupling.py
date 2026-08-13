"""Stitch the nRF52 decoupling caps' ground pads to the In2 GND plane.

Coordinator ruling (session 3): give C11.2, C12.2, C17.2 and C18.2 their own
individual vias down to In2 GND *first*, then route DCC across the gap on F.Cu.
That fixes the real problem at its source -- these decoupling returns should
have had their own vias all along; depending on a thin F.Cu pour neck for a
decoupling return is the actual defect -- and it keeps DCC itself via-free per
the entry 16 ruling.

Verified with the same pour-severance guard used by close_trapped.py: the
stitch is only kept if total unconnected does not get worse.

Usage: python stitch_decoupling.py [--place]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from netclr import ClassRouter
from handroute import T

PLACE = "--place" in sys.argv
TARGETS = [("C11", "2"), ("C12", "2"), ("C17", "2"), ("C18", "2")]
_refs = [a for a in sys.argv[1:] if not a.startswith("--")]
if _refs:
    TARGETS = [(r, "2") for r in _refs]
VIA_D, VIA_DR = 0.30, 0.20

R = ClassRouter()
ALLCU = list(R.board.GetEnabledLayers().CuStack())


def unconnected():
    pcbnew.ZONE_FILLER(R.board).Fill(R.board.Zones())
    cn = R.board.GetConnectivity()
    cn.Build(R.board)          # see close_trapped.py -- recalc alone lies
    cn.RecalculateRatsnest()
    return cn.GetUnconnectedCount(False)


BASE = unconnected()
print("baseline unconnected: %d" % BASE)

placed = 0
for ref, num in TARGETS:
    pad = R.pad(ref, num)
    q = pad.GetPosition()
    px, py = T(q.x), T(q.y)
    n = R.board.FindNet(pad.GetNetCode())
    net = n.GetNetname()
    bb = pad.GetBoundingBox()
    hx = (T(bb.GetRight()) - T(bb.GetLeft())) / 2.0
    hy = (T(bb.GetBottom()) - T(bb.GetTop())) / 2.0

    # try the pad centre first (via-in-pad on a plain SMD ground pad is normal
    # for a decoupling return), then just outside along each axis
    # Grid search around the pad, nearest first.  A tight ring is not enough
    # here: SPI_SDO runs on In4 as a straight vertical at x = 26.470, only
    # 0.05 mm off the cap ground pads at x = 26.420, so every via in the pad
    # column is blocked and the stitch has to step clear of that track.
    cands = [(px, py)]
    ring = []
    step = 0.05
    for i in range(-24, 25):
        for j in range(-24, 25):
            if i == 0 and j == 0:
                continue
            dx, dy = i * step, j * step
            # must start outside the pad itself unless it is the centre
            if abs(dx) < hx + 0.02 and abs(dy) < hy + 0.02:
                continue
            ring.append((dx * dx + dy * dy, px + dx, py + dy))
    ring.sort()
    cands += [(x, y) for _, x, y in ring]

    got = None
    for (vx, vy) in cands:
        vx, vy = round(vx, 4), round(vy, 4)
        if R.in_rule_area(vx, vy, VIA_D / 2.0):
            continue
        if R.hole_conflict(vx, vy, VIA_DR):
            continue
        if not R.via_clear_c(vx, vy, VIA_D, net, ALLCU):
            continue
        inpad = (vx, vy) == (px, py)
        sw = None
        if not inpad:
            # Stub back to the pad.  Widest legal first, then thinner: the
            # GND_D class nominal is 0.508 mm, which does not fit anywhere in
            # this cluster.  Thinner-but-compliant beats giving up -- the floor
            # is design_settings.rules.min_track_width, checked below.
            for w in (R.trk.get(R.cls_of(net), 0.254), 0.3, 0.254,
                      0.2, 0.15, 0.1, R.min_track):
                if w < R.min_track - 1e-9:
                    continue
                if R.seg_clear_c((px, py), (vx, vy), w, net, pcbnew.F_Cu):
                    sw = w
                    break
            if sw is None:
                continue
        got = (vx, vy, inpad, sw)
        break

    if not got:
        print("FAIL    %s.%s [%s] at (%.3f,%.3f) - no via position" %
              (ref, num, net, px, py))
        continue
    vx, vy, inpad, sw = got
    mark = len(R.added)
    if not inpad:
        R.polyline_c(net, pcbnew.F_Cu, [(px, py), (vx, vy)], sw)
    R.add_via(net, vx, vy, VIA_D, VIA_DR)
    now = unconnected()
    if now > BASE:
        for it in R.added[mark:]:
            R.board.Remove(it)
        del R.added[mark:]
        R._invalidate()
        print("REJECT  %s.%s - stitch made things worse (%d -> %d)" %
              (ref, num, BASE, now))
        continue
    print("STITCH  %s.%s [%s] via at (%.3f,%.3f)%s  unconnected %d -> %d" %
          (ref, num, net, vx, vy, "  (in pad)" if inpad else "  stub w=%.3f" % sw, BASE, now))
    BASE = now
    placed += 1

print("stitched %d of %d" % (placed, len(TARGETS)))
if placed and PLACE:
    R.save()
    print("saved")
