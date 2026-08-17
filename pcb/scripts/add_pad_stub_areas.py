# add_pad_stub_areas.py <board> [--place]
# Adds SIX small named rule areas, all called "PAD_STUB", one hugging each
# pad-exit stub that the fine-pitch land pattern forces below its class floor.
# Pure DRC labels: every do-not-allow flag FALSE, so they forbid nothing, block
# nothing, and do not affect zone fill, routing or the ratsnest.  Same mechanism
# as U1_ESCAPE, RF_MATCH and U5_FANOUT.
#
# WHY SIX SMALL BOXES AND NOT THE EXISTING U5_FANOUT BOX (entry 52's proposal).
# U5_FANOUT is x 24.4..34.6, y 10.9..20.1 -- 10.2 x 9.2 mm, a large fraction of
# the digital side.  A width FLOOR of 0.150 over that whole box would let any
# 0.150 mm track anywhere in it pass, including long distribution runs that have
# nothing to do with a land pattern.  That is a real weakening of a brief-stated
# constraint.  These boxes total under 3 mm^2 and contain only the stubs
# themselves, so the exception applies exactly where the package forces it.
#
# WHY THE FLOOR IS 0.150 AND NOT THE PAD WIDTH.  Entry 52 assumed the widest
# legal width always equals the pad width (0.200 at U5, 0.300 at U7).  Measured
# on the live board, three of the seven are tighter than their own pad --
# VDD_nRF's (28.400,11.750) stub at 0.167 and AFE_PWR_EN's at 0.138 -- because
# neighbouring copper, not just the pad, sets the limit.  0.150 is the value that
# covers the narrowest of them after every stub has already been widened as far
# as it will legally go (scripts/padstub_fix.py).
import sys, pcbnew

NAME = "PAD_STUB"
BOXES = [
    # x0, x1, y0, y1, what it covers
    (31.70, 32.30, 18.10, 18.70, "VDD_nRF stub off U5.10"),
    (33.60, 34.45, 13.35, 13.85, "VDD_nRF stub off U5.22"),
    (26.75, 27.60, 16.55, 17.05, "VDD_nRF stub off U5.47"),
    (27.35, 28.65, 11.15, 12.00, "VDD_nRF stub off U5.36"),
    (30.95, 31.56, 11.15, 12.30, "AFE_PWR_EN stubs off U5.29"),
    (41.50, 42.00, 17.81, 19.01, "V2P5 tip off U7.13"),
]

def main():
    path = sys.argv[1]
    place = "--place" in sys.argv
    b = pcbnew.LoadBoard(path)

    have = sum(1 for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName() == NAME)
    if have:
        print("%s already present (%d areas) -- nothing to do" % (NAME, have))
        return

    for X0, X1, Y0, Y1, what in BOXES:
        z = pcbnew.ZONE(b)
        z.SetIsRuleArea(True)
        z.SetZoneName(NAME)
        z.SetDoNotAllowTracks(False)
        z.SetDoNotAllowVias(False)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowZoneFills(False)
        z.SetDoNotAllowFootprints(False)
        ls = pcbnew.LSET()
        for lay in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu,
                    pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu):
            ls.addLayer(lay)
        z.SetLayerSet(ls)
        poly = z.Outline()
        poly.NewOutline()
        for x, y in ((X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)):
            poly.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        print("%s: x %6.2f..%6.2f  y %6.2f..%6.2f  (%5.3f mm^2)  %s"
              % (NAME, X0, X1, Y0, Y1, (X1-X0)*(Y1-Y0), what))
        if place:
            b.Add(z)
    print("total area: %.3f mm^2 over %d boxes, all 6 copper layers, "
          "all do-not-allow flags FALSE"
          % (sum((x1-x0)*(y1-y0) for x0, x1, y0, y1, _ in BOXES), len(BOXES)))
    if place:
        b.Save(path)
        print("saved:", path)
    else:
        print("(dry run -- pass --place to write)")

main()
