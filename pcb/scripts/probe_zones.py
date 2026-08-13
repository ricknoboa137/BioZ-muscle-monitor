import os, pcbnew
PCBDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
b = pcbnew.LoadBoard(os.path.join(PCBDIR, "BioZ-Muscle-Monitor.kicad_pcb"))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
T = pcbnew.ToMM
print("%-22s %-10s %-8s %s" % ("zone", "net", "layer", "bbox mm"))
for z in b.Zones():
    if z.GetIsRuleArea():
        print("RULEAREA", z.GetZoneName(), [b.GetLayerName(l) for l in z.GetLayerSet().Seq()])
        continue
    for lay in z.GetLayerSet().Seq():
        sp = z.GetFilledPolysList(lay)
        bb = sp.BBox()
        print("%-22s %-10s %-8s %.1f,%.1f .. %.1f,%.1f  outlines=%d" % (
            z.GetZoneName() or "-", z.GetNetname(), b.GetLayerName(lay),
            T(bb.GetLeft()), T(bb.GetTop()), T(bb.GetRight()), T(bb.GetBottom()),
            sp.OutlineCount()))
