# plant_bad.py <scratch-board>
# Plants four DELIBERATELY ILLEGAL items on a SCRATCH copy of the board, each
# chosen to trip one specific custom rule in BioZ-Muscle-Monitor.kicad_dru.
# This is the control experiment for "is the rules file actually loaded?" -
# checkpoint entry 35 showed KiCad silently discards ALL rules if any one of
# them fails to parse, and then cheerfully reports "Found 0 violations".
#
# NEVER point this at the live board.  Run with KiCad's bundled python:
#   "C:\Program Files\KiCad\10.0\bin\python.exe" plant_bad.py <scratch.kicad_pcb>
import sys, pcbnew

MM = pcbnew.FromMM

def track(board, net, layer, x1, y1, x2, y2, w):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1)))
    t.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
    t.SetWidth(MM(w))
    t.SetLayer(layer)
    if net: t.SetNet(net)
    board.Add(t)
    return t

def via(board, net, x, y, dia, drill):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetWidth(pcbnew.F_Cu, MM(dia))      # entry: PCB_VIA width calls take a layer
    v.SetDrill(MM(drill))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    if net: v.SetNet(net)
    board.Add(v)
    return v

def main():
    path = sys.argv[1]
    b = pcbnew.LoadBoard(path)
    nets = b.GetNetsByName()
    patient = None
    for nm, n in nets.items():
        if n.GetNetClassName() == "PATIENT":
            patient = n; break
    gndd = nets["GNDD"]

    planted = []
    # 1. patient_width: PATIENT floor is 12 mil = 0.3048 mm.  0.05 mm is far under.
    #    Placed in clear space in the analog half, well away from the split.
    track(b, patient, pcbnew.B_Cu, 5.0, 5.0, 9.0, 5.0, 0.05)
    planted.append("patient_width")
    # 2. split_no_copper: a through via inside the GND_SPLIT channel (x 19.6-20.4).
    #    The zone's own keepout says vias not_allowed, so this must fire.
    #    NOTE the net must NOT be a ground net: split_no_ground_track sits later
    #    in the file and, last-match-wins, would take the report for itself and
    #    make this leg of the control test silently pass for the wrong reason.
    via(b, nets["SPI_SCK"], 20.0, 5.0, 0.5, 0.3)
    planted.append("split_no_copper")
    # 3. split_no_ground_track: a GNDD track lying in the split channel.
    #    This is the genuine ground-bridging defect the rescoped rule exists to catch.
    track(b, gndd, pcbnew.B_Cu, 19.7, 8.0, 20.3, 8.0, 0.3)
    planted.append("split_no_ground_track")
    # 4. antenna_keepout: keepout is x 25.0-50.0, y 0-6.82, all layers.
    track(b, gndd, pcbnew.B_Cu, 30.0, 3.0, 34.0, 3.0, 0.3)
    planted.append("antenna_keepout")

    b.Save(path)
    print("planted, expecting these rules to fire:", ", ".join(planted))

main()
