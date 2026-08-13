"""Rework VREF (U1.C2 -> C1.1).

The original escape exited the In1.Cu Escape layer at (17.60, 22.60), which put a
0.6 mm through via 0.2 mm from the EL_SENP patient trace at x = 17.4 (short +
clearance error), and then ran on B.Cu across EL_DRVN's B.Cu run at y = 23.6
(tracks crossing).  Three DRC errors, all from that one exit.

New topology: stay on the Escape layer until we are already SOUTH of EL_DRVN's
B.Cu wall (y = 23.6) and WEST of the whole patient bundle, drop one through via
at (15.0, 24.4) where F.Cu and B.Cu are both clear, then run on B.Cu straight to
C1 pad 1.  Nothing crosses; the EL_SENP wall is crossed on a different layer.
"""
import os, pcbnew

PCBDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BF = os.path.join(PCBDIR, "BioZ-Muscle-Monitor.kicad_pcb")
mm = pcbnew.FromMM
def V(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))

b = pcbnew.LoadBoard(BF)
NC = b.FindNet("VREF").GetNetCode()
ESC = pcbnew.In1_Cu

# --- remove everything on VREF except the microvia in pad at the C2 bump -----
KEEP = (mm(19.8), mm(25.6))
doomed = []
for t in b.GetTracks():
    if t.GetNetCode() != NC:
        continue
    if t.GetClass() == "PCB_VIA" and (t.GetPosition().x, t.GetPosition().y) == KEEP:
        continue
    doomed.append(t)
for t in doomed:
    b.Remove(t)
print("removed", len(doomed), "VREF items")


def track(layer, pts, w):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(V(*a)); t.SetEnd(V(*c))
        t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(NC)
        b.Add(t)

# Escape layer: one straight run out to the clear west field.
track(ESC, [(19.8, 25.6), (15.0, 24.4)], 0.075)

v = pcbnew.PCB_VIA(b)
v.SetPosition(V(15.0, 24.4)); v.SetDrill(mm(0.3)); v.SetWidth(mm(0.6))
v.SetViaType(pcbnew.VIATYPE_THROUGH)
v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(NC)
b.Add(v)

# B.Cu, entirely inside the region x > 12.8 / y > 23.6 that EL_DRVN encloses.
track(pcbnew.B_Cu, [(15.0, 24.4), (15.0, 27.6), (17.625, 27.6)], 0.25)

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(BF)
print("saved")
