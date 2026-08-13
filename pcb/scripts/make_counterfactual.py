"""Write a scratch counterfactual copy of the board (NEVER over the real one).

usage: make_counterfactual.py <B|C|D> <outpath>
  B = the 7 cluster decoupling caps deleted
  C = all tracks/vias in the west/north annulus of U5 deleted
  D = both
Note: BOARD.Remove() corrupts the swig proxies of anything fetched afterwards,
so every object this needs is collected BEFORE the first Remove().
"""
import sys, pcbnew

SRC = r"C:\Users\User\Documents\BioZ-muscle-monitor\pcb\BioZ-Muscle-Monitor.kicad_pcb"
CAPS = set("C11 C12 C16 C17 C18 C22 C24".split())
ANN = (23.5, 9.0, 27.5, 19.5)
T = pcbnew.ToMM

which, out = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(SRC)

doomed = []
if which in ("B", "D"):
    doomed += [f for f in b.GetFootprints() if f.GetReference() in CAPS]
if which in ("C", "D"):
    L, Tp, R, B = ANN
    for t in b.GetTracks():
        s, e = t.GetStart(), t.GetEnd()
        for p in (s, e):
            if L <= T(p.x) <= R and Tp <= T(p.y) <= B:
                doomed.append(t)
                break
print("removing %d items" % len(doomed))
for it in doomed:
    b.Remove(it)
pcbnew.SaveBoard(out, b)
print("wrote", out)
