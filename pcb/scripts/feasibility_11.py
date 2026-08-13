"""Feasibility scan for the 11 trapped U5 pins.

For each unconnected pair on those nets, ask two separate questions and report
them separately, because they have different answers and different fixes:

  A. Is there ANY clear simple path on F.Cu?  Scanned as a perpendicular detour
     at every offset from -4.0 to +4.0 mm in 0.1 mm steps, at four trace widths
     down to the 0.075 mm minimum, plus the straight line and both L-shapes.
  B. Is there a clear escape-via site next to the U5 pad, at 0.30/0.20?

A "no" to A is a congestion/placement finding, not a clearance one.  A "no" to
both means the pin cannot be resolved without moving something.
"""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from handroute import Router, T

R = Router()
F = pcbnew.F_Cu
ALLCU = list(R.board.GetEnabledLayers().CuStack())
SIG = R.layer("Signal")
B = pcbnew.B_Cu

TRAPPED = {"nPGOOD", "nCHG", "VDD_nRF", "AFE_CS", "LED_K", "nRESET",
           "DECA_RF", "XL1", "XC1", "XC2", "DCC"}

drc = json.load(open(os.path.join(os.path.dirname(R.path), "drc.json")))


def pt(item):
    p = item.get("pos")
    return None if p is None else (p["x"], p["y"])


def any_path(a, c, nc, layer):
    for w in (0.2, 0.15, 0.1, 0.075):
        if R.seg_clear(a, c, w, nc, layer):
            return "straight w=%.3f" % w
        for corner in ((c[0], a[1]), (a[0], c[1])):
            if (R.seg_clear(a, corner, w, nc, layer)
                    and R.seg_clear(corner, c, w, nc, layer)):
                return "L w=%.3f" % w
        for i in range(-40, 41):
            d = i * 0.1
            if abs(d) < 0.3:
                continue
            for pts in ([a, (a[0], a[1] + d), (c[0], c[1] + d), c],
                        [a, (a[0] + d, a[1]), (c[0] + d, c[1]), c]):
                if all(R.seg_clear(x, y, w, nc, layer)
                       for x, y in zip(pts, pts[1:])):
                    return "detour %+.1f w=%.3f" % (d, w)
    return None


seen = set()
print("%-9s %-34s %-22s %s" % ("net", "pair", "F.Cu path?", "other layers?"))
print("-" * 96)
for u in drc["unconnected_items"]:
    net = re.search(r"\[(\w+)\]", u["items"][0]["description"])
    if not net or net.group(1) not in TRAPPED:
        continue
    net = net.group(1)
    a, c = pt(u["items"][0]), pt(u["items"][1])
    if a is None or c is None:
        continue
    key = (net, a, c)
    if key in seen:
        continue
    seen.add(key)
    nc = R.netcode(net)
    f = any_path(a, c, nc, F)
    others = []
    for lay, nm in ((SIG, "In4"), (B, "B.Cu")):
        r = any_path(a, c, nc, lay)
        if r:
            others.append("%s:%s" % (nm, r))
    print("%-9s %-34s %-22s %s"
          % (net, "%.1f,%.1f -> %.1f,%.1f" % (a[0], a[1], c[0], c[1]),
             f or "NONE", ", ".join(others) or "none"))
