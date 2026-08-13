import os, pcbnew
PCBDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
b = pcbnew.LoadBoard(os.path.join(PCBDIR, "BioZ-Muscle-Monitor.kicad_pcb"))
tm = pcbnew.ToMM
for f in b.Footprints():
    for p in f.Pads():
        if p.GetNetname() == "VREF":
            print("PAD", f.GetReference(), p.GetNumber(), tm(p.GetPosition().x), tm(p.GetPosition().y), b.GetLayerName(p.GetLayer()))
n = b.FindNet("VREF").GetNetCode()
for t in b.GetTracks():
    if t.GetNetCode() == n:
        print(t.GetClass(), b.GetLayerName(t.GetLayer()), tm(t.GetStart().x), tm(t.GetStart().y), "->", tm(t.GetEnd().x), tm(t.GetEnd().y))
print("--- items on Escape layer ---")
for t in b.GetTracks():
    if t.GetLayer() == pcbnew.In1_Cu:
        print(t.GetNetname(), tm(t.GetStart().x), tm(t.GetStart().y), "->", tm(t.GetEnd().x), tm(t.GetEnd().y))
print("--- copper items within x 15-22, y 20-31 (F/B/In1) ---")
for t in b.GetTracks():
    s = t.GetStart()
    if 15 < tm(s.x) < 22 and 20 < tm(s.y) < 31 and t.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu):
        print(" ", t.GetClass(), b.GetLayerName(t.GetLayer()), t.GetNetname(), tm(s.x), tm(s.y), "->", tm(t.GetEnd().x), tm(t.GetEnd().y))
print("--- pads in x 14-23, y 20-32 ---")
for f in b.Footprints():
    for p in f.Pads():
        x, y = tm(p.GetPosition().x), tm(p.GetPosition().y)
        if 14 < x < 23 and 20 < y < 32 and f.GetReference() != "U1":
            print(" ", f.GetReference(), p.GetNumber(), p.GetNetname(), round(x,3), round(y,3), b.GetLayerName(p.GetLayer()))
