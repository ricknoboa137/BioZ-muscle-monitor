# fix_wlp_annular.py <board> [--place]
# The 8 laser microvias in the U1 WLP escape sit at 0.200 mm diameter over a
# 0.100 mm drill, i.e. a 0.050 mm annular ring.  brief section 9/10 and the rule
# wlp_annular both call for 0.075 mm, which needs a 0.250 mm pad over the same
# 0.100 mm drill.  The DRILL IS NOT TOUCHED - wlp_microvia_drill wants it in
# 0.100..0.150 and it stays at 0.100 - so this is a pad-diameter change only and
# does not alter the laser-drilling process the fab was quoted for.
#
# Widening a via pad inside a 0.400 mm-pitch WLP fanout is not obviously safe, so
# this is deliberately a separate, testable step: run it on a scratch copy, then
# refill_zones.py, then drc_union.sh, and only keep it if wlp_annular falls
# without wlp_clearance rising.
#
# PCB_VIA width getters AND setters take a layer argument on this pcbnew.  The
# bare no-argument form pops a blocking wxWidgets modal that hangs a headless
# process forever (standing project rule).
import sys, pcbnew

TARGET = 0.250

def main():
    path = sys.argv[1]
    place = "--place" in sys.argv
    b = pcbnew.LoadBoard(path)
    n = 0
    for t in b.GetTracks():
        if not isinstance(t, pcbnew.PCB_VIA):
            continue
        if t.GetViaType() != pcbnew.VIATYPE_MICROVIA:
            continue
        top = t.TopLayer()
        w, d = t.GetWidth(top), t.GetDrill()
        if (w - d) / 2 < pcbnew.FromMM(0.075):
            p = t.GetPosition()
            print(f"  {t.GetNetname():8s} @({pcbnew.ToMM(p.x):.3f},{pcbnew.ToMM(p.y):.3f}) "
                  f"dia {pcbnew.ToMM(w):.3f} -> {TARGET:.3f}  drill {pcbnew.ToMM(d):.3f} unchanged")
            if place:
                t.SetWidth(top, pcbnew.FromMM(TARGET))
            n += 1
    print(f"{'widened' if place else 'would widen'} {n} microvias")
    if place:
        b.Save(path)
        print("saved:", path)

main()
