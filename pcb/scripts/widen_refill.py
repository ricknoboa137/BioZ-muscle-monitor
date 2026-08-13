# widen_refill.py <dir> [net ...]
# Entry 48's widen_pertrack.py retried each under-width SIGNAL/POWER track one at
# a time and kept only 3 of 45.  IT DID NOT REFILL THE ZONES after widening.
# Entry 38 established that a stored pour computed against the OLD copper is
# silently wrong: KiCad's filler backs a pour off from each track by the binding
# clearance, so a track that grows by 0.1-0.3 mm now sits inside its own stale
# pour and DRC reports a clearance violation that a refill would remove.
# That would have caused widen_pertrack to reject widens that are in fact free.
# This version refills after every widen before judging it.
#
# Accept a widen only if: total error-severity violations strictly falls AND
# unconnected is unchanged.  Same bar as entry 48, plus the refill.
import sys, os, json, subprocess, pcbnew

KICLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
FLOORS = {"SIGNAL": 0.254, "POWER_HIGH": 0.508, "POWER_LOW": 0.508}

def drc(board, out):
    subprocess.run([KICLI, "pcb", "drc", "--severity-error", "--format", "json",
                    "-o", out, board], capture_output=True)
    j = json.load(open(out))
    v = [x for x in j.get("violations", []) if x.get("severity") == "error"]
    return len(v), len(j.get("unconnected_items", []))

def refill(b):
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    c = b.GetConnectivity(); c.Build(b)
    return c.GetUnconnectedCount(True)

def main():
    d = sys.argv[1]
    nets = set(sys.argv[2:])
    board = os.path.join(d, "BioZ-Muscle-Monitor.kicad_pcb")
    out = os.path.join(d, "p.json")
    base_v, base_u = drc(board, out)
    print(f"baseline: {base_v} violations, {base_u} unconnected", flush=True)

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
            if nets and n.GetNetname() not in nets:
                continue
            todo.append((t.m_Uuid.AsString(), f, n.GetNetname()))
    print(f"candidates: {len(todo)}", flush=True)

    kept = 0
    for idx, (uid, floor, net) in enumerate(todo, 1):
        b = pcbnew.LoadBoard(board)
        tgt = None
        for t in b.GetTracks():
            if not isinstance(t, pcbnew.PCB_VIA) and t.m_Uuid.AsString() == uid:
                tgt = t; break
        if tgt is None:
            continue
        old = tgt.GetWidth()
        tgt.SetWidth(pcbnew.FromMM(floor))
        u = refill(b)
        b.Save(board)
        v, u2 = drc(board, out)
        if v < base_v and u2 == base_u:
            base_v = v; kept += 1
            print(f"  [{idx}/{len(todo)}] KEPT  {net:12s} -> {floor}  (now {v})", flush=True)
        else:
            print(f"  [{idx}/{len(todo)}] rej   {net:12s} ({v}/{u2})", flush=True)
            b2 = pcbnew.LoadBoard(board)
            for t in b2.GetTracks():
                if not isinstance(t, pcbnew.PCB_VIA) and t.m_Uuid.AsString() == uid:
                    t.SetWidth(old); break
            refill(b2)
            b2.Save(board)
    v, u = drc(board, out)
    print(f"RESULT: kept {kept} of {len(todo)}; now {v} violations, {u} unconnected")

main()
