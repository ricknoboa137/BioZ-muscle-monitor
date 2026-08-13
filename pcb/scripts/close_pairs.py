"""Close the trapped-pin pairs that feasibility_11.py proved have a clear path.

Only touches nets sanctioned for 0.30/0.20 mm vias in entry 16.  XL1, XC1, XC2
and DCC are NOT handled here: entry 16 requires them to stay on F.Cu with no
via, no F.Cu path exists, and the alternative would contradict the ruling.  That
is escalated in entry 19, not worked around.

Usage:  python close_pairs.py <NET> [NET ...]
"""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from handroute import Router, T

R = Router()
F, B = pcbnew.F_Cu, pcbnew.B_Cu
SIG = R.layer("Signal")
ALLCU = list(R.board.GetEnabledLayers().CuStack())
VIA_D, VIA_DR = 0.30, 0.20

# Use the LARGEST net-class clearance on the board (POWER_HIGH, 0.254 mm) for
# every check rather than the 0.20 mm default.  Checking at 0.20 put an nCHG via
# 0.225 mm from a V_SYS track and produced a real clearance error, because V_SYS
# is POWER_HIGH.  Conservative everywhere beats correct-on-average.
CLR = 0.254

ALLOWED = {"nPGOOD", "nCHG", "VDD_nRF", "AFE_CS", "LED_K", "nRESET", "DECA_RF"}
WANT = [n for n in sys.argv[1:]] or sorted(ALLOWED)

drc = json.load(open(os.path.join(os.path.dirname(R.path), "drc.json")))


def pt(i):
    p = i.get("pos")
    return None if p is None else (p["x"], p["y"])


def is_via_end(i):
    return i["description"].startswith("Via")


def on_layer(i, lay):
    """is this endpoint already present on `lay`?"""
    d = i["description"]
    if d.startswith("Via"):
        return True                     # through via reaches every copper layer
    if " on Signal" in d:
        return lay == SIG
    if " on B.Cu" in d:
        return lay == B
    return lay == F


def shapes(a, c):
    out = [[a, c], [a, (c[0], a[1]), c], [a, (a[0], c[1]), c]]
    for i in range(-40, 41):
        d = i * 0.1
        if abs(d) < 0.3:
            continue
        out.append([a, (a[0], a[1] + d), (c[0], c[1] + d), c])
        out.append([a, (a[0] + d, a[1]), (c[0] + d, c[1]), c])
    return out


closed, skipped = [], []
seen = set()
for u in drc["unconnected_items"]:
    m = re.search(r"\[(\w+)\]", u["items"][0]["description"])
    if not m or m.group(1) not in WANT or m.group(1) not in ALLOWED:
        continue
    net = m.group(1)
    i1, i2 = u["items"][0], u["items"][1]
    a, c = pt(i1), pt(i2)
    if a is None or c is None:
        continue
    if (net, a, c) in seen:
        continue
    seen.add((net, a, c))
    nc = R.netcode(net)

    done = False
    for lay, nm in ((F, "F.Cu"), (SIG, "In4"), (B, "B.Cu")):
        need = [e for e in (i1, i2) if not on_layer(e, lay)]
        pts_need = [a if e is i1 else c for e in need]
        # every endpoint that is not already on this layer needs a via
        ok_v = True
        for p in pts_need:
            if R.in_rule_area(p[0], p[1], VIA_D / 2.0) or \
               R.hole_conflict(p[0], p[1], VIA_DR) or \
               not R.via_clear(p[0], p[1], VIA_D, nc, ALLCU, CLR):
                ok_v = False
                break
        if not ok_v:
            continue
        for w in (0.2, 0.15, 0.1, 0.075):
            for path in shapes(a, c):
                if R.polyline(nc, lay, path, w, CLR):
                    for p in pts_need:
                        R.add_via(nc, p[0], p[1], VIA_D, VIA_DR)
                    closed.append((net, nm, w, len(pts_need),
                                   "%.1f,%.1f->%.1f,%.1f" % (a[0], a[1], c[0], c[1])))
                    done = True
                    break
            if done:
                break
        if done:
            break
    if not done:
        skipped.append((net, "%.1f,%.1f->%.1f,%.1f" % (a[0], a[1], c[0], c[1])))

for net, nm, w, nv, s in closed:
    print("CLOSED  %-9s on %-5s w=%.3f  %d new via(s)  %s" % (net, nm, w, nv, s))
for net, s in skipped:
    print("OPEN    %-9s %s" % (net, s))
print("closed %d, still open %d" % (len(closed), len(skipped)))
if closed:
    R.save()
    print("saved")
