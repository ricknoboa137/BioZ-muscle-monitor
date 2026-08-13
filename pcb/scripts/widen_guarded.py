# widen_guarded.py <scratchdir> [--apply-to <realboard>]
# Widens every SIGNAL / POWER_HIGH / POWER_LOW track to its .kicad_dru floor, then
# ITERATIVELY REVERTS only those tracks whose new width actually breaks something,
# until DRC reports no clearance or shorting violations at all.
#
# WHY NOT JUST WIDEN EVERYTHING (measured on this board, session 11): widening all
# 69 under-width tracks does close signal_width 37 and power_width 32 outright,
# but it CREATES 17 new violations -- 8 builtin clearance, 5 general_clearance,
# 2 rf_clearance, 1 wlp_clearance and 1 SHORTING_ITEMS.  Trading 69 width errors
# for a short is not a fix.  So the widening is kept only where it is free.
#
# Whatever is left un-widened at the end is NOT solved and must not be recorded as
# solved: it is genuine hand-routing / re-placement work, because those tracks
# cannot carry their brief-mandated width in the space currently available.
#
# The board is only ever written in the scratch directory.  Nothing here touches
# the real board unless you copy the result yourself.
import sys, os, json, re, subprocess, pcbnew

KICLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
FLOORS = {"SIGNAL": 0.254, "POWER_HIGH": 0.508, "POWER_LOW": 0.508}
BAD = ("clearance", "shorting_items", "track_dangling")

def drc(board, out):
    subprocess.run([KICLI, "pcb", "drc", "--severity-error", "--format", "json",
                    "-o", out, board], capture_output=True)
    return json.load(open(out))

def bad_points(j):
    """positions of items involved in any clearance/short violation"""
    pts = set()
    for v in j.get("violations", []):
        if v.get("severity") != "error":
            continue
        t = v.get("type", "")
        if not any(k in t for k in BAD):
            continue
        for i in v.get("items", []):
            if "pos" in i:
                pts.add((round(i["pos"]["x"], 3), round(i["pos"]["y"], 3)))
    return pts

def main():
    d = sys.argv[1]
    board = os.path.join(d, "BioZ-Muscle-Monitor.kicad_pcb")

    b = pcbnew.LoadBoard(board)
    orig = {}
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        n = t.GetNet()
        if not n:
            continue
        f = FLOORS.get(n.GetNetClassName())
        if f and t.GetWidth() < pcbnew.FromMM(f):
            k = t.m_Uuid.AsString()
            orig[k] = t.GetWidth()
            t.SetWidth(pcbnew.FromMM(f))
    print(f"candidates widened: {len(orig)}")
    b.Save(board)

    frozen = set()
    for it in range(1, 12):
        j = drc(board, os.path.join(d, "g.json"))
        pts = bad_points(j)
        if not pts:
            print(f"iteration {it}: no clearance/short violations left")
            break
        b = pcbnew.LoadBoard(board)
        reverted = 0
        for t in b.GetTracks():
            if isinstance(t, pcbnew.PCB_VIA):
                continue
            k = t.m_Uuid.AsString()
            if k not in orig or k in frozen:
                continue
            s, e = t.GetStart(), t.GetEnd()
            for p in ((round(pcbnew.ToMM(s.x), 3), round(pcbnew.ToMM(s.y), 3)),
                      (round(pcbnew.ToMM(e.x), 3), round(pcbnew.ToMM(e.y), 3))):
                if p in pts:
                    t.SetWidth(orig[k])
                    frozen.add(k)
                    reverted += 1
                    break
        print(f"iteration {it}: {len(pts)} bad points -> reverted {reverted} tracks")
        if reverted == 0:
            print("  !! bad points remain but none map to a widened track -- "
                  "these are pre-existing, stopping")
            break
        b.Save(board)

    kept = len(orig) - len(frozen)
    print(f"RESULT: widened and KEPT {kept} of {len(orig)}; "
          f"reverted {len(frozen)} as not-free (= hand-routing work)")

main()
