#!/usr/bin/env python
"""Read-only: measure the U5 crowding cluster and the candidate open area south of it."""
import pcbnew, sys

PCB = r"C:\Users\User\Documents\BioZ-muscle-monitor\pcb\BioZ-Muscle-Monitor.kicad_pcb"
b = pcbnew.LoadBoard(PCB)
MM = pcbnew.ToMM

CLUSTER = "C11 C12 C16 C17 C18 C22 C24 IC1 U2 C25 R10".split()

def crtyd(fp):
    bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
    return (MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom()))

fps = {f.GetReference(): f for f in b.GetFootprints()}

u5 = fps["U5"]
u5c = crtyd(u5)
print("U5 F.CrtYd  L=%.3f T=%.3f R=%.3f B=%.3f" % u5c)
print("U5 pos %.3f,%.3f" % (MM(u5.GetPosition().x), MM(u5.GetPosition().y)))
print()
print("ref   crtydL   crtydT   crtydR   crtydB   gapWestOfU5  nets")
for r in CLUSTER:
    f = fps.get(r)
    if f is None:
        print(r, "NOT FOUND"); continue
    c = crtyd(f)
    gap = u5c[0] - c[2]   # U5 left edge minus part right edge
    nets = ",".join(sorted({p.GetNetname() for p in f.Pads()}))
    print("%-4s %8.3f %8.3f %8.3f %8.3f   %8.3f  %s" % (r, c[0], c[1], c[2], c[3], gap, nets))

print()
print("--- pad-level: which U5 pad each cap sits nearest, and net match ---")
u5pads = [(p.GetPadName(), p.GetNetname(), MM(p.GetPosition().x), MM(p.GetPosition().y)) for p in u5.Pads()]
for r in CLUSTER:
    f = fps.get(r)
    if not f: continue
    for p in f.Pads():
        n = p.GetNetname()
        same = [q for q in u5pads if q[1] == n]
        px, py = MM(p.GetPosition().x), MM(p.GetPosition().y)
        if same:
            d = min(((q[2]-px)**2+(q[3]-py)**2)**0.5 for q in same)
            names = ",".join(q[0] for q in same)
            print("%-4s pad%-3s net=%-10s U5 pads[%s] mindist=%.3f" % (r, p.GetPadName(), n, names, d))

print()
print("--- ALL footprints, courtyard boxes, sorted by y then x (for open-area hunt) ---")
rows = []
for f in b.GetFootprints():
    try:
        c = crtyd(f)
    except Exception:
        continue
    rows.append((c[1], c[0], f.GetReference(), c))
rows.sort()
for _, _, r, c in rows:
    print("%-5s L=%7.3f T=%7.3f R=%7.3f B=%7.3f" % (r, *c))
