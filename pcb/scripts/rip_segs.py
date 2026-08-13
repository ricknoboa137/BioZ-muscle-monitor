# rip_segs.py <board> <net> <layer> "x1,y1,x2,y2" ["x1,y1,x2,y2" ...]
# Delete named track segments (matched on net + layer + endpoints, either order,
# 1 um tolerance).  Vias are never matched.
# BOARD.Remove() corrupts the SWIG proxies of everything fetched afterwards in
# the same process, so this script does NOTHING after the removals except Save()
# and exit.  The re-route runs in a separate process against the saved file.
import sys, pcbnew

path, net, layname = sys.argv[1], sys.argv[2], sys.argv[3]
wanted = []
for a in sys.argv[4:]:
    x1, y1, x2, y2 = [float(v) for v in a.split(",")]
    wanted.append(((x1, y1), (x2, y2)))

b = pcbnew.LoadBoard(path)
lay = b.GetLayerID(layname)
T = pcbnew.ToMM

def near(p, q):
    return abs(p[0] - q[0]) < 0.001 and abs(p[1] - q[1]) < 0.001

kill = []
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        continue
    n = t.GetNet()
    if not n or n.GetNetname() != net or t.GetLayer() != lay:
        continue
    s, e = t.GetStart(), t.GetEnd()
    a = (T(s.x), T(s.y)); c = (T(e.x), T(e.y))
    for w in wanted:
        if (near(a, w[0]) and near(c, w[1])) or (near(a, w[1]) and near(c, w[0])):
            kill.append(t)
            print("rip %s %s (%.3f,%.3f)-(%.3f,%.3f) w=%.4f" % (
                net, layname, a[0], a[1], c[0], c[1], T(t.GetWidth())))
            break

if len(kill) != len(wanted):
    print("ABORT: matched %d of %d requested segments" % (len(kill), len(wanted)))
    sys.exit(1)
for t in kill:
    b.Remove(t)
b.Save(path)
print("removed %d, saved %s" % (len(kill), path))
