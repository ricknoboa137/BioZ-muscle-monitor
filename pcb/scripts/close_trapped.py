"""Close the 11 trapped U5 pins, one pair at a time, with correct per-class
clearance and a strict preference order.

Preference order, from the ruling plus the user's added guidance:
  1. F.Cu at the class nominal width, no via.
  2. F.Cu at progressively thinner widths down to the board minimum, no via.
     A legally-thinner trace that fits beats an extra via or an extra layer.
  3. Only if no F.Cu path exists at any legal width: In4 "Signal" or B.Cu,
     with 0.30/0.20 mm vias (entry 16 ruling).
XL1/XC1/XC2/DCC are restricted to steps 1-2: entry 16 says F.Cu, no via.

Usage:  python close_trapped.py <NET> [NET ...]        (one net at a time)
        python close_trapped.py --dry <NET>            (report, do not save)
"""
import os
import sys
import json
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from netclr import ClassRouter
from handroute import T

DRY = "--dry" in sys.argv
WANT = [a for a in sys.argv[1:] if not a.startswith("--")]

NOVIA = {"XL1", "XC1", "XC2", "DCC"}
VIA_D, VIA_DR = 0.30, 0.20

R = ClassRouter()
F, B = pcbnew.F_Cu, pcbnew.B_Cu
SIG = R.layer("Signal")
ALLCU = list(R.board.GetEnabledLayers().CuStack())
DRCJSON = os.path.join(os.path.dirname(R.path), "drc.json")


def pt(i):
    p = i.get("pos")
    return None if p is None else (round(p["x"], 4), round(p["y"], 4))


def on_layer(i, lay):
    d = i["description"]
    if d.startswith("Via"):
        return True
    if " on Signal" in d:
        return lay == SIG
    if " on B.Cu" in d:
        return lay == B
    return lay == F


def leadout(item, p):
    """Point just outside a pad, along the pad's long axis, pointing away from
    the component.  Routing from the pad CENTRE is what defeated every earlier
    attempt: the first leg of any detour crosses the pad's own neighbours.

    Two cases, and getting them the wrong way round is the entry-19 bug:
      - fine-pitch IC pad (>2 pads): exit outward from the footprint centre.
      - 2-pad passive: exit directly away from the sibling pad, otherwise the
        lead-out lands on the far side of the part and the route has to loop
        all the way around it.
    Returns (leadout_point, pad_object) or (p, None) if the endpoint is not a pad.
    """
    d = item["description"]
    m = re.match(r"Pad (\S+) \[[\w]+\] of (\w+)", d)
    if not m:
        return p, None
    num, ref = m.group(1), m.group(2)
    try:
        fp = R.fp(ref)
        pad = R.pad(ref, num)
    except StopIteration:
        return p, None
    pads = list(fp.Pads())
    bb = pad.GetBoundingBox()
    hx = (T(bb.GetRight()) - T(bb.GetLeft())) / 2.0
    hy = (T(bb.GetBottom()) - T(bb.GetTop())) / 2.0
    if len(pads) > 2:
        cx, cy = T(fp.GetPosition().x), T(fp.GetPosition().y)
        vx, vy = p[0] - cx, p[1] - cy
    else:
        sib = [q for q in pads if q.GetNumber() != num]
        if not sib:
            return p, None
        s = sib[0].GetPosition()
        vx, vy = p[0] - T(s.x), p[1] - T(s.y)
    # step out along the dominant axis, past the pad edge plus clearance
    if abs(vx) >= abs(vy):
        step = (hx + 0.24) * (1 if vx >= 0 else -1)
        return (round(p[0] + step, 4), p[1]), pad
    step = (hy + 0.24) * (1 if vy >= 0 else -1)
    return (p[0], round(p[1] + step, 4)), pad


def shapes(a, c):
    """straight, both L's, and a perpendicular detour at every 0.1 mm offset.
    Guard against the entry-19 bug: when the pads share an X or a Y the three
    base shapes collapse onto one line, so dedupe."""
    base = [[a, c], [a, (c[0], a[1]), c], [a, (a[0], c[1]), c]]
    out, seen = [], set()
    for s in base:
        k = tuple(s)
        if k not in seen:
            seen.add(k)
            out.append(s)
    # 0.025 mm step, not 0.1.  The usable channel between C18 and C11 is
    # y in [15.9375, 15.9625] -- 0.025 mm wide.  A 0.1 mm grid steps straight
    # over gaps like that and reports "no path" on a board that has one.
    for i in range(-160, 161):
        d = i * 0.025
        if abs(d) < 0.05:
            continue
        d = round(d, 4)
        out.append([a, (a[0], a[1] + d), (c[0], c[1] + d), c])
        out.append([a, (a[0] + d, a[1]), (c[0] + d, c[1]), c])
    # Detour that can also approach the target from BEYOND it.  Needed
    # whenever the blocker is the target component's own other pad -- e.g. DCC,
    # where C11.2 (GNDD) sits directly between U5.46 and C11.1, so every path
    # that stops short of C11.1 crosses C11.2.  The overshoot `e` carries the
    # run past the target and comes back at it from the far side.
    for i in range(-30, 31):
        d = i * 0.1
        if abs(d) < 0.2:
            continue
        for e in (-1.6, -1.2, -0.9, -0.6, 0.6, 0.9, 1.2, 1.6):
            out.append([a, (a[0], a[1] + d), (c[0] + e, c[1] + d),
                        (c[0] + e, c[1]), c])
            out.append([a, (a[0] + d, a[1]), (c[0] + d, c[1] + e),
                        (c[0], c[1] + e), c])
    return out


def widths(net):
    """class nominal first, then thinner, down to the board minimum."""
    nom = R.trk.get(R.cls_of(net), 0.254)
    ws = [nom, 0.20, 0.15, 0.12, 0.10, R.min_track]
    out = []
    for w in ws:
        if w >= R.min_track - 1e-9 and w not in out:
            out.append(round(w, 4))
    return out


drc = json.load(open(os.path.abspath(DRCJSON)))
pairs = []
seen = set()
for u in drc["unconnected_items"]:
    m = re.search(r"\[([\w]+)\]", u["items"][0]["description"])
    if not m or m.group(1) not in WANT:
        continue
    net = m.group(1)
    i1, i2 = u["items"][0], u["items"][1]
    a, c = pt(i1), pt(i2)
    if a is None or c is None or (net, a, c) in seen:
        continue
    seen.add((net, a, c))
    pairs.append((net, i1, i2, a, c))

def unconnected_now():
    """refill pours, then ask KiCad's own connectivity engine.  Refilling is
    the point: a thin track squeezed through a tight channel can SEVER a
    copper pour and orphan the pads it was feeding, which no clearance check
    will ever notice."""
    pcbnew.ZONE_FILLER(R.board).Fill(R.board.Zones())
    cn = R.board.GetConnectivity()
    # TRAP: after a zone fill, RecalculateRatsnest() alone UNDER-REPORTS badly
    # (21 vs the true 52 on this board, and it is stable across repeat calls, so
    # it looks like an answer).  Only Build(board) rebuilds connectivity from
    # scratch and agrees with kicad-cli.  Do not drop the Build call.
    cn.Build(R.board)
    cn.RecalculateRatsnest()
    return cn.GetUnconnectedCount(False)


def undo(mark):
    """remove everything added since `mark`"""
    for it in R.added[mark:]:
        R.board.Remove(it)
    del R.added[mark:]
    R._invalidate()


BASE = unconnected_now()
print("baseline unconnected: %d" % BASE)
closed, openp = [], []
for net, i1, i2, a, c in pairs:
    cls = R.cls_of(net)
    # lead the route out of each fine-pitch pad before searching for a path
    la, pada = leadout(i1, a)
    lc, padc = leadout(i2, c)
    layers = [(F, "F.Cu")] if net in NOVIA else [(F, "F.Cu"), (SIG, "In4"), (B, "B.Cu")]
    done = False
    for lay, nm in layers:
        need = [(e, p) for e, p in ((i1, a), (i2, c)) if not on_layer(e, lay)]
        if need and net in NOVIA:
            continue
        ok = True
        for _, p in need:
            if R.in_rule_area(p[0], p[1], VIA_D / 2.0) or \
               R.hole_conflict(p[0], p[1], VIA_DR) or \
               not R.via_clear_c(p[0], p[1], VIA_D, net, ALLCU):
                ok = False
                break
        if not ok:
            continue
        for w in widths(net):
            for core in shapes(la, lc):
                # stub from each pad centre out to its lead-out point
                path = ([a] if la != a else []) + core + ([c] if lc != c else [])
                mark = len(R.added)
                if R.polyline_c(net, lay, path, w):
                    for _, p in need:
                        R.add_via(net, p[0], p[1], VIA_D, VIA_DR)
                    # accept only if the board is genuinely better off
                    got = unconnected_now()
                    if got > BASE - 1:
                        if "--why" in sys.argv:
                            print("   reject %-8s %s w=%.3f  %d -> %d" %
                                  (net, path, w, BASE, got))
                        undo(mark)
                        continue
                    BASE = got
                    closed.append((net, cls, nm, w, len(need),
                                   "%.2f,%.2f->%.2f,%.2f" % (a + c)))
                    done = True
                    break
            if done:
                break
        if done:
            break
    if not done:
        openp.append((net, cls, "%.2f,%.2f->%.2f,%.2f" % (a + c)))

for net, cls, nm, w, nv, s in closed:
    print("CLOSED  %-9s %-12s %-5s w=%.3f  %d via(s)  %s" % (net, cls, nm, w, nv, s))
for net, cls, s in openp:
    print("OPEN    %-9s %-12s %s" % (net, cls, s))
print("closed %d, still open %d" % (len(closed), len(openp)))
if closed and not DRY:
    R.save()
    print("saved")
