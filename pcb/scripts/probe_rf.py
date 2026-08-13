# probe_rf.py <board>
# Read-only.  Dumps every footprint and pad in the RF matching-network region so
# the rf_clearance violations can be attributed to a CAUSE -- land-pattern
# geometry versus an actual routing choice -- instead of being assumed to be one
# or the other.  Same discipline as the split_no_copper investigation.
import sys, pcbnew

MM = pcbnew.ToMM

def main():
    b = pcbnew.LoadBoard(sys.argv[1])
    X0, X1, Y0, Y1 = 26.0, 35.0, 5.0, 13.5
    print("footprints in the RF region (x 26-35, y 5-13.5):")
    for fp in b.GetFootprints():
        p = fp.GetPosition()
        if not (X0 <= MM(p.x) <= X1 and Y0 <= MM(p.y) <= Y1):
            continue
        print(f"  {fp.GetReference():6s} {fp.GetValue():12s} "
              f"@({MM(p.x):.3f},{MM(p.y):.3f}) rot={fp.GetOrientationDegrees():.0f} "
              f"fpid={fp.GetFPIDAsString()}")
        pads = list(fp.Pads())
        for pad in pads:
            pp = pad.GetPosition()
            sz = pad.GetSize()
            print(f"      pad {pad.GetNumber():3s} net={pad.GetNetname():10s} "
                  f"@({MM(pp.x):.4f},{MM(pp.y):.4f}) size={MM(sz.x):.4f}x{MM(sz.y):.4f}")
        # centre-to-centre pitch between the two pads of a 2-pad part, and the
        # actual copper gap between them: this is the land-pattern figure that
        # the brief's rf_internal rule already acknowledges.
        if len(pads) == 2:
            a, c = pads[0].GetPosition(), pads[1].GetPosition()
            pitch = ((MM(a.x) - MM(c.x)) ** 2 + (MM(a.y) - MM(c.y)) ** 2) ** 0.5
            gap = pitch - MM(pads[0].GetSize().x) / 2 - MM(pads[1].GetSize().x) / 2
            print(f"      -> pad pitch {pitch:.4f} mm, copper gap {gap:.4f} mm")

main()
