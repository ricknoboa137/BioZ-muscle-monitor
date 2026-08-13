"""Move the SPI_SDO In4 "Signal" vertical off x = 26.470 so the cap ground-pad
column at x = 26.420 is no longer blocked for through vias (entry 21's unlock).

SPI_SDO is net class SIGNAL, whose .kicad_dru width floor (0.254 mm) EQUALS its
nominal -- entry 23 -- so there is ZERO thinning headroom here.  The track cannot
be made thinner; it has to be relocated.  Nothing is relaxed: every candidate is
checked with the real per-net-class pair clearance (netclr.ClassRouter), and the
whole move is rejected unless Build()-verified unconnected does not get worse.

Usage: python move_sdo.py [--place]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from netclr import ClassRouter
from handroute import T

PLACE = "--place" in sys.argv
NET = "SPI_SDO"
OLD_X = 26.470
Y_TOP, Y_BOT = 14.130, 23.210
DIAG_END = (23.980, 25.700)
STUB_START = (25.609, 14.130)
VIA_D, VIA_DR = 0.600, 0.300
W_SIG = 0.2540

R = ClassRouter()
SIGNAL = R.layer("Signal")
FCU = pcbnew.F_Cu
nc = R.netcode(NET)

print("SPI_SDO class=%s  dru width floor=%.4f mm  (nominal in use %.4f)" %
      (R.cls_of(NET), R.min_width_for(NET), W_SIG))


def unconnected():
    pcbnew.ZONE_FILLER(R.board).Fill(R.board.Zones())
    cn = R.board.GetConnectivity()
    cn.Build(R.board)          # entry 21: RecalculateRatsnest alone lies
    cn.RecalculateRatsnest()
    return cn.GetUnconnectedCount(False)


BASE = unconnected()
print("baseline unconnected: %d" % BASE)

# --- locate the exact items to move -------------------------------------
victims = {"via": None, "vert": None, "diag": None, "stub": None}
for t in R.board.GetTracks():
    if t.GetNetCode() != nc:
        continue
    if t.GetClass() == "PCB_VIA":
        p = t.GetPosition()
        if abs(T(p.x) - OLD_X) < 1e-3 and abs(T(p.y) - Y_TOP) < 1e-3:
            victims["via"] = t
        continue
    s, e = t.GetStart(), t.GetEnd()
    sx, sy, ex, ey = T(s.x), T(s.y), T(e.x), T(e.y)
    lay = R.board.GetLayerName(t.GetLayer())
    if lay == "Signal" and abs(sx - OLD_X) < 1e-3 and abs(ex - OLD_X) < 1e-3:
        victims["vert"] = t
    elif lay == "Signal" and abs(sx - OLD_X) < 1e-3:
        victims["diag"] = t
    elif lay == "F.Cu" and abs(ex - OLD_X) < 1e-3:
        victims["stub"] = t

for k, v in victims.items():
    print("  %-5s %s" % (k, "found" if v is not None else "*** MISSING ***"))
if any(v is None for v in victims.values()):
    sys.exit("board geometry does not match entry 21's description - stop")

# --- search a new x, nearest-first --------------------------------------
cands = []
step = 0.05
for i in range(1, 61):
    for sgn in (-1, +1):
        cands.append(round(OLD_X + sgn * i * step, 3))

# the old geometry is same-net so it is invisible to the clearance check; that
# is correct here because it is about to be deleted.
best = None
import collections
why = collections.Counter()
detail = []
for X in cands:
    if not (23.0 < X < 30.0):
        continue
    fails = []
    if not R.seg_clear_c((X, Y_TOP), (X, Y_BOT), W_SIG, NET, SIGNAL):
        fails.append("vertical")
    if not R.seg_clear_c((X, Y_BOT), DIAG_END, W_SIG, NET, SIGNAL):
        fails.append("diagonal")
    if not R.seg_clear_c(STUB_START, (X, Y_TOP), W_SIG, NET, FCU):
        fails.append("fcu_stub")
    if not R.via_clear_c(X, Y_TOP, VIA_D, NET, [FCU, SIGNAL]):
        fails.append("via_clear")
    if R.hole_conflict(X, Y_TOP, VIA_DR):
        fails.append("hole2hole")
    if R.in_rule_area(X, Y_TOP):
        fails.append("rule_area")
    if not fails:
        best = X
        break
    why[",".join(fails)] += 1
    detail.append((X, fails))

if best is None:
    print("-- why every candidate failed (combination -> count) --")
    for k, v in why.most_common():
        print("   %-45s %d" % (k, v))
    print("-- nearest 12 candidates --")
    for X, f in sorted(detail, key=lambda d: abs(d[0] - OLD_X))[:12]:
        print("   x=%.3f  %s" % (X, ",".join(f)))

if best is None:
    sys.exit("no clear x found within +/-3.0 mm - report, do not relax anything")

print("chosen new x = %.3f  (was %.3f, moved %+.3f mm)"
      % (best, OLD_X, best - OLD_X))
if not PLACE:
    print("dry run - pass --place to apply")
    sys.exit(0)

# --- apply ---------------------------------------------------------------
for v in victims.values():
    R.board.Remove(v)
R.add_track(nc, SIGNAL, (best, Y_TOP), (best, Y_BOT), W_SIG)
R.add_track(nc, SIGNAL, (best, Y_BOT), DIAG_END, W_SIG)
R.add_track(nc, FCU, STUB_START, (best, Y_TOP), W_SIG)
via = R.add_via(NET, best, Y_TOP, dia=VIA_D, drill=VIA_DR,
                top=FCU, bot=pcbnew.B_Cu)

after = unconnected()
print("unconnected after move: %d (was %d)" % (after, BASE))
if after > BASE:
    sys.exit("REGRESSION - move made connectivity worse, not saving")
R.save()
print("saved.")
