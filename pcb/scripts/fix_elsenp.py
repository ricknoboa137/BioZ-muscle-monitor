"""EL_SENP's north-south run sat at x = 17.40, leaving 0.09 mm to C2 pad 2 (GNDA)
against a 0.10 mm footprint-local rule.  The channel it runs in is bounded by
C2 pad 2 (east edge 17.16) and C4 pad 1 (west edge 17.87); with a 0.30 mm trace
the centre-line window is 17.31..17.72, so 17.52 is the middle of it and gives
0.205 mm both sides.
"""
import os, pcbnew
PCBDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BF = os.path.join(PCBDIR, "BioZ-Muscle-Monitor.kicad_pcb")
b = pcbnew.LoadBoard(BF)
NC = b.FindNet("EL_SENP").GetNetCode()
OLD, NEW = pcbnew.FromMM(17.4), pcbnew.FromMM(17.52)
n = 0
for t in b.GetTracks():
    if t.GetNetCode() != NC or t.GetClass() != "PCB_TRACK":
        continue
    for get, set_ in ((t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)):
        p = get()
        if p.x == OLD:
            set_(pcbnew.VECTOR2I(NEW, p.y)); n += 1
print("moved", n, "endpoints")
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(BF)
print("saved")
