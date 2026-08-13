# add_rf_match_area.py <board> [--place]
# Adds a NAMED RULE AREA "RF_MATCH" around the RF matching network, so the
# rf_shunt_ground exception can be scoped geometrically.  It is a pure DRC
# label: every do-not-allow flag is FALSE, so it forbids nothing, blocks
# nothing, and does not affect zone filling, routing or the ratsnest.  Same
# mechanism the project already uses for U1_ESCAPE.
#
# WHY AN AREA AND NOT memberOfFootprint (session 11, entry 44).  The rf_clearance
# violations are RF *track* vs ground *track*.  `B.memberOfFootprint('C21')`
# matches pads and footprint graphics, NOT free tracks, so the footprint-scoped
# form closes NOTHING -- measured: rf_clearance stayed at 14.  Verified, not
# assumed, before changing approach.
#
# WHY THE RULE ALSO NAMES THE GROUND NETS AND IS NOT AREA-ONLY.  An area-only
# exemption would also exempt the AFE_PWR_EN via at (31.200,11.400), which is a
# GENUINE rf_clearance defect sitting inside the same box.  Pairing the area with
# the three shunt-ground nets keeps that one enforced.
#
# Extent: x 27.5..33.5, y 6.85..12.90.  Chosen to cover C23/L6/C21/L5/C20/L4/C19
# and net-tie NT1, and to START BELOW the antenna keepout, which is
# x 25.0..50.0, y 0..6.82 -- the two must not overlap.
import sys, pcbnew

X0, X1, Y0, Y1 = 27.5, 33.5, 6.85, 12.90
NAME = "RF_MATCH"

def main():
    path = sys.argv[1]
    place = "--place" in sys.argv
    b = pcbnew.LoadBoard(path)

    for z in b.Zones():
        if z.GetIsRuleArea() and z.GetZoneName() == NAME:
            print(f"{NAME} already present -- nothing to do")
            return

    z = pcbnew.ZONE(b)
    z.SetIsRuleArea(True)
    z.SetZoneName(NAME)
    # forbid nothing: this area exists only so a DRC rule can say "here"
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
    # API note, verified against the live pcbnew 10.0: ZONE has no
    # SetLocalCoord() -- it does not exist and is not needed here.

    print(f"{NAME}: x {X0}..{X1}, y {Y0}..{Y1}, all 6 copper layers, "
          f"all do-not-allow flags FALSE")
    if place:
        b.Add(z)
        b.Save(path)
        print("saved:", path)
    else:
        print("(dry run -- pass --place to write)")

main()
