import os, pcbnew, itertools
PCBDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
b = pcbnew.LoadBoard(os.path.join(PCBDIR, "BioZ-Muscle-Monitor.kicad_pcb"))
T = pcbnew.ToMM
segs = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
print("segments:", len(segs))
g = {}
for t in segs:
    g.setdefault((t.GetNetCode(), t.GetLayer()), []).append(t)

def seg(t):
    return ((t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y))

bad = 0
for k, lst in g.items():
    for a, c in itertools.combinations(lst, 2):
        (ax, ay), (bx, by) = seg(a)
        (px, py), (qx, qy) = seg(c)
        d1 = (bx-ax, by-ay); d2 = (qx-px, qy-py)
        cr = d1[0]*d2[1]-d1[1]*d2[0]
        if abs(cr) > 10**7:      # not parallel
            continue
        # collinear?
        if abs((px-ax)*d1[1] - (py-ay)*d1[0]) > 2000:
            continue
        # 1-D overlap along d1
        L = (d1[0]**2+d1[1]**2)**0.5
        if L == 0: continue
        def proj(x, y): return ((x-ax)*d1[0]+(y-ay)*d1[1])/L
        i0, i1 = 0, L
        j0, j1 = sorted((proj(px, py), proj(qx, qy)))
        ov = min(i1, j1) - max(i0, j0)
        if ov > 1000:            # >1 um of shared length
            bad += 1
            print("OVERLAP %s L%s  %.3f,%.3f-%.3f,%.3f  vs  %.3f,%.3f-%.3f,%.3f  ov=%.3fmm"
                  % (a.GetNetname(), b.GetLayerName(a.GetLayer()),
                     T(ax), T(ay), T(bx), T(by), T(px), T(py), T(qx), T(qy), ov/1e6))
print("overlapping collinear pairs:", bad)

# junction degree: how many segments meet at each point, per net+layer
from collections import Counter
for k, lst in g.items():
    c = Counter()
    for t in lst:
        for p in seg(t): c[p] += 1
    for p, n in c.items():
        if n > 2:
            print("degree-%d junction on %s %s at %.3f,%.3f" %
                  (n, lst[0].GetNetname(), b.GetLayerName(k[1]), T(p[0]), T(p[1])))
