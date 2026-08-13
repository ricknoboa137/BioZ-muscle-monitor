import os, sys, pcbnew
PCBDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
b = pcbnew.LoadBoard(os.path.join(PCBDIR, "BioZ-Muscle-Monitor.kicad_pcb"))
T = pcbnew.ToMM
for ref in sys.argv[1:]:
    f = next(x for x in b.Footprints() if x.GetReference() == ref)
    print("== %s  layer=%s  pos=%.3f,%.3f  rot=%.1f  pads=%d" % (
        ref, b.GetLayerName(f.GetLayer()), T(f.GetPosition().x), T(f.GetPosition().y),
        f.GetOrientationDegrees(), len(list(f.Pads()))))
    for p in sorted(f.Pads(), key=lambda p: (p.GetNumber().zfill(4))):
        sz = p.GetSize()
        print("   %-4s %-11s %8.3f %8.3f  size %.3fx%.3f  %s" % (
            p.GetNumber(), p.GetNetname() or "-", T(p.GetPosition().x), T(p.GetPosition().y),
            T(sz.x), T(sz.y), b.GetLayerName(p.GetLayer())))
