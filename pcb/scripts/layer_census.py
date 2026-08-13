"""Segments per copper layer + via count + ratsnest.  Run after every SES import:
if anything landed on Escape / GND / Power the plane patch failed and the board is
silently wrong."""
import os, collections, pcbnew
PCBDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
b = pcbnew.LoadBoard(os.path.join(PCBDIR, "BioZ-Muscle-Monitor.kicad_pcb"))
b.BuildConnectivity()
seg = collections.Counter(); vias = 0
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        vias += 1
    else:
        seg[b.GetLayerName(t.GetLayer())] += 1
print("segments per layer:")
for k in ("F.Cu", "Escape", "GND", "Power", "Signal", "B.Cu"):
    print("   %-8s %d" % (k, seg.get(k, 0)))
print("vias:", vias)
print("unconnected:", b.GetConnectivity().GetUnconnectedCount(True))
BAD = {k: v for k, v in seg.items() if k in ("GND", "Power")}
if BAD:
    print("*** PLANE VIOLATION: signal segments on plane layers:", BAD)
