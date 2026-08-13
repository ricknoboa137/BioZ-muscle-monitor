"""Read-only: locate SPI_SDO's In4/Signal geometry and report its net class + the
binding width floor, plus the cap ground-pad column it is blocking."""
import os, pcbnew
PCBDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
b = pcbnew.LoadBoard(os.path.join(PCBDIR, "BioZ-Muscle-Monitor.kicad_pcb"))
T = pcbnew.ToMM

print("--- all SPI_SDO track segments, every layer ---")
for t in b.GetTracks():
    if t.GetNetname() != "SPI_SDO":
        continue
    lay = b.GetLayerName(t.GetLayer())
    if t.GetClass() == "PCB_VIA":
        p = t.GetPosition()
        print("  VIA   (%.3f, %.3f) drill %.3f dia %.3f" %
              (T(p.x), T(p.y), T(t.GetDrillValue()), T(t.GetWidth(t.TopLayer()))))
    else:
        s, e = t.GetStart(), t.GetEnd()
        print("  %-8s (%.3f, %.3f) -> (%.3f, %.3f)  w=%.4f" %
              (lay, T(s.x), T(s.y), T(e.x), T(e.y), T(t.GetWidth())))

nc = b.FindNet("SPI_SDO").GetNetClassName()
print("\nSPI_SDO net class:", nc)

print("\n--- pads of the decoupling caps in the x~26.4 column ---")
for ref in ("C11", "C12", "C17", "C18", "C24"):
    f = next((f for f in b.Footprints() if f.GetReference() == ref), None)
    if not f:
        continue
    for p in f.Pads():
        pos = p.GetPosition()
        print("  %-4s.%s  (%.3f, %.3f)  net=%s" %
              (ref, p.GetNumber(), T(pos.x), T(pos.y), p.GetNetname()))
