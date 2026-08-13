"""Freerouting 2.2.4 hangs (runaway PolylineTrace.combine recursion, ~5 GB and
climbing) loading a DSN that contains overlapping collinear segments on the same
net and layer.  route_escape.py produced several: e.g. CAL_S has both
(15.2,25.175)-(16.0,25.175) and (15.3,25.175)-(16.0,25.175).

This removes, per (net, layer): exact duplicates, zero-length segments, and any
segment whose span is wholly contained in another collinear segment.
"""
import os, pcbnew

PCBDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BF = os.path.join(PCBDIR, "BioZ-Muscle-Monitor.kicad_pcb")
b = pcbnew.LoadBoard(BF)

segs = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]


def key(t):
    a = (t.GetStart().x, t.GetStart().y)
    c = (t.GetEnd().x, t.GetEnd().y)
    return (t.GetNetCode(), t.GetLayer(), t.GetWidth()), tuple(sorted((a, c)))


def collinear_contained(inner, outer):
    """is segment `inner` wholly inside collinear segment `outer`?"""
    (ax, ay), (bx, by) = inner
    (px, py), (qx, qy) = outer
    dx, dy = qx - px, qy - py
    if dx == 0 and dy == 0:
        return False
    for (x, y) in ((ax, ay), (bx, by)):
        cross = (x - px) * dy - (y - py) * dx
        if abs(cross) > 2000:            # 2 um in nm, tolerance
            return False
        dot = (x - px) * dx + (y - py) * dy
        if dot < 0 or dot > dx * dx + dy * dy:
            return False
    return True


doomed, seen = [], {}
for t in segs:
    k, pts = key(t)
    if pts[0] == pts[1]:
        doomed.append(t); continue
    if (k, pts) in seen:
        doomed.append(t); continue
    seen[(k, pts)] = t

groups = {}
for (k, pts), t in seen.items():
    groups.setdefault(k[:2], []).append((pts, t))

for g in groups.values():
    for pts, t in g:
        for pts2, t2 in g:
            if t is t2:
                continue
            if t2 in doomed:
                continue
            if collinear_contained(pts, pts2) and pts != pts2:
                doomed.append(t)
                break

for t in doomed:
    b.Remove(t)
print("removed %d degenerate/overlapping segments of %d" % (len(doomed), len(segs)))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(BF)
print("saved")
