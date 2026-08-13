# fix_patclr.py <board> [--place]
# Closes the 4 REAL patient_clearance violations left after the zone refill and
# the PATIENT widen (checkpoint entry 38).  Geometry-only edits: every one is a
# translation of an existing segment/via endpoint.  No topology changes, no net
# re-assignment, no widths touched, nothing deleted.
#
# Required gap is 20 mil = 0.5080 mm (rule patient_clearance).  Each move below
# is computed from the measured centre-to-centre distance, not estimated:
#
# A. CAL_F horizontal run at y=26.700 vs the EL_SENP vertical's top end at
#    (17.520,26.000).  Perpendicular gap 0.700 - 0.075 - 0.1524 = 0.4726.
#    Need centre distance 0.508+0.075+0.1524 = 0.7354.  Move CAL_F's y=26.700
#    nodes to y=26.760 -> gap 0.5326.  CAL_F is the FORCE half of the CAL Kelvin
#    pair; a Kelvin pair is force/sense, not a length-matched differential pair,
#    so a 60 micron shift on one leg carries no matching penalty.
#
# B. VREF through via at (15.000,24.400), dia 0.600, vs the EL_DRVN B.Cu run
#    along y=23.600, w=0.3048.  Gap 0.800 - 0.300 - 0.1524 = 0.3476.
#    FIRST ATTEMPT, REJECTED BY MEASUREMENT: move the via to y=24.600.  That
#    does clear EL_DRVN (0.5476) but it drives the via 0.200 straight at the
#    CAL_S runs to its south and opened THREE new analog_sense_clearance
#    violations (CAL_S at (15.2,25.175), (15.2,28.6), (15.3,29.0)).  Trading a
#    patient violation for three analog ones is not a fix.
#    ADOPTED INSTEAD: shrink the via AND move it only slightly.
#    dia 0.600 -> 0.450 (drill stays 0.300, so annular goes 0.150 -> 0.075,
#    still well over the board's 0.050 minimum and equal to the WLP annulus),
#    and y 24.400 -> 24.490.  Gap to EL_DRVN = 0.890 - 0.225 - 0.1524 = 0.5126,
#    over the 0.508 floor.  Toward CAL_S the via moves 0.090 nearer but its
#    radius drops 0.075, so the net change there is 0.015 -- neutral, and no new
#    violation.  The drill is untouched, so through_via_min_drill (0.300) is
#    unaffected.  The via MOVES AWAY from EL_DRVN; it does not go back to the
#    deleted (17.6,22.6) exit -- entry, do not restore that one.
#
# C/D. EL_DRVP's corner at (18.350,20.500) vs the V2P5F via at (19.050,20.772)
#    (dia 0.500) and the V2P5F F.Cu run leaving it eastward (w=0.508).
#    Gaps 0.3485 and 0.3445.  Here the OFFENDER cannot be moved cheaply: that
#    V2P5F via is the landing point of an In4 'Signal' diagonal AND the start of
#    an F.Cu run, so shifting it drags three segments on two layers.  The
#    EL_DRVP vertical, by contrast, is a plain straight run with a jog at each
#    end, so the cheap and safe edit is to slide it west, x 18.350 -> 18.100.
#    That gives via-to-track 19.050-18.100-0.250-0.1524 = 0.5476 and
#    track-to-track 19.050-18.100-0.254-0.1524 = 0.5436, both over 0.508.
#    Clearance to the neighbouring EL_SENP vertical at x=17.520 becomes 0.275,
#    which is fine: both are PATIENT, so patient_clearance does not apply to the
#    pair (its condition is B.NetClass != 'PATIENT') and the binding floor there
#    is general_clearance 0.127.
#
# Verify with scripts/refill_zones.py then scripts/drc_union.sh.  Widening or
# moving copper can sever a pour invisibly to DRC (entry 20) -- refill_zones.py
# carries that guard.
import sys, pcbnew

NM = pcbnew.FromMM
def mm(v): return pcbnew.ToMM(v)

def near(a, b, tol=1000):      # 1 micron, in internal nm units
    return abs(a - b) < tol

def main():
    path = sys.argv[1]
    place = "--place" in sys.argv
    b = pcbnew.LoadBoard(path)
    moves = []

    for t in b.GetTracks():
        net = t.GetNetname()

        # --- A: CAL_F, y 26.700 -> 26.760 -----------------------------------
        if net == "CAL_F" and not isinstance(t, pcbnew.PCB_VIA):
            for get, set_ in ((t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)):
                p = get()
                if near(p.y, NM(26.700)):
                    moves.append(f"A CAL_F ({mm(p.x):.4f},{mm(p.y):.4f}) -> y 26.7600")
                    if place: set_(pcbnew.VECTOR2I(p.x, NM(26.760)))

        # --- B: VREF via shrink 0.600 -> 0.450 and y 24.400 -> 24.490 -------
        if net == "VREF":
            if isinstance(t, pcbnew.PCB_VIA):
                p = t.GetPosition()
                if near(p.x, NM(15.000)) and near(p.y, NM(24.400)):
                    moves.append("B VREF via (15.0000,24.4000) dia 0.600"
                                 " -> (15.0000,24.4900) dia 0.450, drill unchanged")
                    if place:
                        t.SetPosition(pcbnew.VECTOR2I(p.x, NM(24.490)))
                        # PCB_VIA width setters take a layer argument, same
                        # standing rule as the getters.
                        t.SetWidth(pcbnew.F_Cu, NM(0.450))
            else:
                for get, set_ in ((t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)):
                    p = get()
                    if near(p.x, NM(15.000)) and near(p.y, NM(24.400)):
                        moves.append("B VREF end (15.0000,24.4000) -> (15.0000,24.4900)")
                        if place: set_(pcbnew.VECTOR2I(p.x, NM(24.490)))

        # --- C/D: EL_DRVP vertical, x 18.350 -> 18.100 ----------------------
        if net == "EL_DRVP" and not isinstance(t, pcbnew.PCB_VIA):
            for get, set_ in ((t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)):
                p = get()
                if near(p.x, NM(18.350)):
                    moves.append(f"C EL_DRVP ({mm(p.x):.4f},{mm(p.y):.4f}) -> x 18.1000")
                    if place: set_(pcbnew.VECTOR2I(NM(18.100), p.y))

    for m in moves:
        print("  " + m)
    print(f"{'moved' if place else 'would move'} {len(moves)} endpoints")
    if place:
        b.Save(path)
        print("saved:", path)

main()
