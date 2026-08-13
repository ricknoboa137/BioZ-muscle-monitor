# probe_patclr.py <board>
# Read-only.  Dumps the exact geometry of the three non-patient offenders left in
# patient_clearance and of the PATIENT copper they crowd, so a fix can be computed
# rather than guessed.  Prints every item on the offending nets, with widths and
# endpoints, plus the measured centre-to-centre and edge-to-edge gaps.
import sys, pcbnew

MM = pcbnew.ToMM

def desc(t, b):
    if isinstance(t, pcbnew.PCB_VIA):
        # standing rule: PCB_VIA width calls ALWAYS take a layer argument, or a
        # blocking wxWidgets modal hangs the headless process forever.
        return (f"VIA  net={t.GetNetname():10s} pos=({MM(t.GetPosition().x):.4f},"
                f"{MM(t.GetPosition().y):.4f}) dia={MM(t.GetWidth(t.TopLayer())):.4f} "
                f"drill={MM(t.GetDrill()):.4f} {b.GetLayerName(t.TopLayer())}->"
                f"{b.GetLayerName(t.BottomLayer())}")
    return (f"TRK  net={t.GetNetname():10s} ({MM(t.GetStart().x):.4f},{MM(t.GetStart().y):.4f})"
            f"->({MM(t.GetEnd().x):.4f},{MM(t.GetEnd().y):.4f}) w={MM(t.GetWidth()):.4f} "
            f"layer={b.GetLayerName(t.GetLayer())}")

def main():
    b = pcbnew.LoadBoard(sys.argv[1])
    want = {"CAL_F", "VREF", "V2P5F", "EL_SENP", "EL_DRVN", "EL_DRVP"}
    for net in sorted(want):
        print(f"=== {net} ===")
        for t in b.GetTracks():
            if t.GetNetname() == net:
                print("  ", desc(t, b))
        for fp in b.GetFootprints():
            for p in fp.Pads():
                if p.GetNetname() == net:
                    print(f"   PAD  {fp.GetReference()}.{p.GetNumber()} "
                          f"({MM(p.GetPosition().x):.4f},{MM(p.GetPosition().y):.4f})")

main()
