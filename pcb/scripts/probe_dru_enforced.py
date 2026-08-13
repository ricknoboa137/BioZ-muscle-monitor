"""Decisive test: does kicad-cli DRC actually enforce BioZ-Muscle-Monitor.kicad_dru?

The board carries DRC-clean POWER_HIGH tracks at 0.250 mm and POWER_LOW/SIGNAL/
PATIENT tracks well under their .kicad_dru width floors.  Either those floors do
not bind (and routing has far more headroom than entry 23 assumed) or the custom
rules are not being loaded by kicad-cli (and every "0 errors" this project has
recorded was measured against defaults only).  Both answers matter; guessing
between them does not.

Writes a SCRATCH copy to %TEMP% and plants two deliberate violations in it --
never touches the live board.  BOARD.Remove() corrupts swig proxies fetched
afterwards (entry 33), so this script only ADDS.
"""
import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew

SRC = r"C:\Users\User\Documents\BioZ-muscle-monitor\pcb\BioZ-Muscle-Monitor.kicad_pcb"
DRU = r"C:\Users\User\Documents\BioZ-muscle-monitor\pcb\BioZ-Muscle-Monitor.kicad_dru"
TMP = os.environ["TEMP"]
DST = os.path.join(TMP, "dru-test.kicad_pcb")

shutil.copy(SRC, DST)
shutil.copy(DRU, os.path.join(TMP, "dru-test.kicad_dru"))

b = pcbnew.LoadBoard(DST)
mm = pcbnew.FromMM


def V(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


nc = b.FindNet("V_SYS").GetNetCode()

# (1) a 0.075 mm POWER_HIGH track -- floor is 0.508 under rule power_width.
#     Placed in the empty south-east of the board so nothing else can flag it.
t = pcbnew.PCB_TRACK(b)
t.SetStart(V(44.0, 40.0)); t.SetEnd(V(48.0, 40.0))
t.SetWidth(mm(0.075)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(nc)
b.Add(t)

# (2) a track straight through the ANTENNA_KEEPOUT rule area, which rule
#     antenna_keepout forbids outright.  This is the control: if THIS is not
#     flagged, the custom rules are certainly not loaded.
t2 = pcbnew.PCB_TRACK(b)
t2.SetStart(V(30.0, 3.0)); t2.SetEnd(V(40.0, 3.0))
t2.SetWidth(mm(0.25)); t2.SetLayer(pcbnew.F_Cu); t2.SetNetCode(nc)
b.Add(t2)

b.Save(DST)
print("scratch board written:", DST)
print("planted: 0.075mm POWER_HIGH track at y=40, and a track through "
      "ANTENNA_KEEPOUT at y=3")
