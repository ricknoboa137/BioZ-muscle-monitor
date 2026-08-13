"""Specctra has no concept of a laser microvia.  The DSN/SES round-trip brings the
U1 WLP escape's 0.1 mm vias back as plain blind/buried vias, which then fail the
board's 0.2 mm minimum *through* hole rule (microvias have their own, smaller,
minimum in board setup).  Re-stamp every 0.1 mm via as VIATYPE_MICROVIA.

Run after EVERY SES import.
"""
import os, pcbnew
PCBDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BF = os.path.join(PCBDIR, "BioZ-Muscle-Monitor.kicad_pcb")
b = pcbnew.LoadBoard(BF)
UV = pcbnew.FromMM(0.1)
n = 0
for t in b.GetTracks():
    if t.GetClass() != "PCB_VIA" or t.GetDrill() != UV:
        continue
    top, bot = t.TopLayer(), t.BottomLayer()
    if abs(b.GetCopperLayerCount() and 1) and t.GetViaType() != pcbnew.VIATYPE_MICROVIA:
        t.SetViaType(pcbnew.VIATYPE_MICROVIA)
        t.SetLayerPair(top, bot)
        n += 1
print("restored %d vias to VIATYPE_MICROVIA" % n)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(BF)
print("saved")
