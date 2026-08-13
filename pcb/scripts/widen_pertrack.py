# widen_pertrack.py <scratchdir>
# The cheap win entry 46 flagged: widen the still-under-width SIGNAL/POWER tracks
# ONE AT A TIME, keeping each only if DRC total does not rise and unconnected does
# not change.  Entry 46's batch guard was deliberately conservative -- it reverted
# any widened track that touched a bad point, including tracks that merely sat
# near a PRE-EXISTING violation -- so some of those 45 should widen safely alone.
#
# Not a shortcut and not a substitute for routing: whatever fails here genuinely
# cannot carry its brief width in the space available and is hand-routing work.
import sys, os, json, subprocess, pcbnew

KICLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
FLOORS = {"SIGNAL": 0.254, "POWER_HIGH": 0.508, "POWER_LOW": 0.508}

def drc(board, out):
    subprocess.run([KICLI, "pcb", "drc", "--severity-error", "--format", "json",
                    "-o", out, board], capture_output=True)
    j = json.load(open(out))
    v = [x for x in j.get("violations", []) if x.get("severity") == "error"]
    return len(v), len(j.get("unconnected_items", []))

def main():
    d = sys.argv[1]
    board = os.path.join(d, "BioZ-Muscle-Monitor.kicad_pcb")
    out = os.path.join(d, "p.json")
    base_v, base_u = drc(board, out)
    print(f"baseline: {base_v} violations, {base_u} unconnected")

    b = pcbnew.LoadBoard(board)
    todo = []
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        n = t.GetNet()
        if not n:
            continue
        f = FLOORS.get(n.GetNetClassName())
        if f and t.GetWidth() < pcbnew.FromMM(f):
            todo.append((t.m_Uuid.AsString(), f, n.GetNetname()))
    print(f"candidates: {len(todo)}")

    kept = 0
    for idx, (uid, floor, net) in enumerate(todo, 1):
        b = pcbnew.LoadBoard(board)
        tgt = None
        for t in b.GetTracks():
            if not isinstance(t, pcbnew.PCB_VIA) and t.m_Uuid.AsString() == uid:
                tgt = t
                break
        if tgt is None:
            continue
        old = tgt.GetWidth()
        tgt.SetWidth(pcbnew.FromMM(floor))
        b.Save(board)
        v, u = drc(board, out)
        # accept only if the total strictly falls (this width error cleared) and
        # nothing else broke, and connectivity is untouched
        if v < base_v and u == base_u:
            base_v = v
            kept += 1
            print(f"  [{idx}/{len(todo)}] KEPT  {net:12s} -> {floor}  (now {v})")
        else:
            b2 = pcbnew.LoadBoard(board)
            for t in b2.GetTracks():
                if not isinstance(t, pcbnew.PCB_VIA) and t.m_Uuid.AsString() == uid:
                    t.SetWidth(old)
                    break
            b2.Save(board)
    v, u = drc(board, out)
    print(f"RESULT: kept {kept} of {len(todo)}; now {v} violations, {u} unconnected")

main()
