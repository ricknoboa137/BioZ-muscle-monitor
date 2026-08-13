"""Ground-truth probe of the live board: origin, unconnected (Build()-verified),
segments per layer, via/microvia census.  Read-only, writes nothing."""
import os, sys, collections, pcbnew

PCBDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BF = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    PCBDIR, "BioZ-Muscle-Monitor.kicad_pcb")
T = pcbnew.ToMM
b = pcbnew.LoadBoard(BF)
print("board file:", BF)

# --- origin: Edge.Cuts top-left should be (-0.05, -0.05) ---
xs, ys = [], []
for d in b.GetDrawings():
    if d.GetLayer() == pcbnew.Edge_Cuts:
        bb = d.GetBoundingBox()
        xs += [T(bb.GetLeft()), T(bb.GetRight())]
        ys += [T(bb.GetTop()), T(bb.GetBottom())]
print("Edge.Cuts extents: x %.4f..%.4f  y %.4f..%.4f" %
      (min(xs), max(xs), min(ys), max(ys)))
print("  origin top-left = (%.4f, %.4f)  [expect -0.0500,-0.0500]" %
      (min(xs), min(ys)))

# --- anchor pads named in fix_origin.py's assertions ---
for ref, pad, exp in (("U1", "C1", (19.8000, 25.2000)),
                      ("R1", "1", (19.1750, 26.0000))):
    f = next((f for f in b.Footprints() if f.GetReference() == ref), None)
    if f:
        p = next((p for p in f.Pads() if p.GetNumber() == pad), None)
        if p:
            pos = p.GetPosition()
            print("  %s.%s at (%.4f, %.4f)  [expect %.4f,%.4f]" %
                  (ref, pad, T(pos.x), T(pos.y), exp[0], exp[1]))

# --- segments per layer, vias ---
seg = collections.Counter()
vias = collections.Counter()
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        vt = t.GetViaType()
        name = {pcbnew.VIATYPE_THROUGH: "through",
                pcbnew.VIATYPE_BLIND: "blind",
                pcbnew.VIATYPE_BURIED: "buried",
                pcbnew.VIATYPE_MICROVIA: "microvia"}.get(vt, str(vt))
        vias[name] += 1
    else:
        seg[b.GetLayerName(t.GetLayer())] += 1
print("segments per layer:")
for k in ("F.Cu", "Escape", "GND", "Power", "Signal", "B.Cu"):
    print("   %-8s %d" % (k, seg.get(k, 0)))
print("vias:", dict(vias), "total", sum(vias.values()))
bad = {k: v for k, v in seg.items() if k in ("GND", "Power")}
print("*** PLANE VIOLATION:" if bad else "planes clean:", bad if bad else "0 on GND, 0 on Power")

# --- unconnected, Build()-verified (entry 21 trap) ---
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
conn = b.GetConnectivity()
conn.Build(b)
print("UNCONNECTED (Build()-verified):", conn.GetUnconnectedCount(True))
