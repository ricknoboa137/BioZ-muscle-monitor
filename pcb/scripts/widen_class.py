# widen_class.py <board> <NETCLASS> <target_mm> [--place]
# Widens every track on <NETCLASS> that is currently below <target_mm>, up to
# <target_mm>.  Without --place it only reports.  It does NOT move anything and
# does NOT change topology -- width only.
#
# Context (session 11): with the .kicad_dru finally in force, patient_width
# flagged 20 tracks all sitting at exactly 0.3000 mm against a 12 mil =
# 0.3048 mm floor.  That is a 4.8 micron shortfall from the board having been
# built in round millimetres against a rule stated in mils -- not a routing
# error, but the brief says 12 mil and the copper must meet it.  Relaxing the
# rule to 0.3 mm would be silently relaxing a brief constraint; widening the
# copper is the honest fix.
#
# Widening reduces the gap to neighbouring copper, so ALWAYS re-run
# scripts/refill_zones.py and scripts/drc_union.sh afterwards.
import sys, pcbnew

def main():
    path, cls, target = sys.argv[1], sys.argv[2], float(sys.argv[3])
    place = "--place" in sys.argv
    b = pcbnew.LoadBoard(path)
    tgt = pcbnew.FromMM(target)
    n = 0
    for t in b.GetTracks():
        # PCB_VIA is a subclass of PCB_TRACK.  Skip vias: track_width does not
        # apply to them, and PCB_VIA.GetWidth() with no layer argument pops a
        # blocking wxWidgets modal that hangs a headless process forever
        # (standing project rule).
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        net = t.GetNet()
        if not net or net.GetNetClassName() != cls:
            continue
        w = t.GetWidth()
        if w < tgt:
            print(f"  {net.GetNetname():10s} {pcbnew.ToMM(w):.4f} -> {target:.4f} "
                  f"@ ({pcbnew.ToMM(t.GetStart().x):.3f},{pcbnew.ToMM(t.GetStart().y):.3f})")
            if place:
                t.SetWidth(tgt)
            n += 1
    print(f"{'widened' if place else 'would widen'} {n} tracks on class {cls}")
    if place:
        b.Save(path)
        print("saved:", path)

main()
