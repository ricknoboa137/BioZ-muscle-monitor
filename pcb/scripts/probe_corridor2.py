"""Read-only: H1 shield-frame pad geometry near its left wall, C15/C14/C36 nets,
and U5 pad-level extents. No writes."""
import pcbnew
B = pcbnew.LoadBoard(r"C:\Users\User\Documents\BioZ-muscle-monitor\pcb\BioZ-Muscle-Monitor.kicad_pcb")
MM = pcbnew.ToMM

h1 = B.FindFootprintByReference("H1")
print("=== H1 pads with left edge < 40 mm ===")
for p in h1.Pads():
    r = p.GetBoundingBox()
    if MM(r.GetLeft()) < 40:
        print(f"  pad {p.GetNumber():>4} net={p.GetNetname():<10} "
              f"x {MM(r.GetLeft()):8.3f}..{MM(r.GetRight()):8.3f} "
              f"y {MM(r.GetTop()):7.3f}..{MM(r.GetBottom()):7.3f}")
print("H1 pad count:", h1.GetPadCount())
r = h1.GetCourtyard(pcbnew.F_CrtYd).BBox()
print(f"H1 F.CrtYd bbox x {MM(r.GetLeft()):.3f}..{MM(r.GetRight()):.3f} y {MM(r.GetTop()):.3f}..{MM(r.GetBottom()):.3f}")

print("\n=== U5 courtyard + per-pad extents ===")
f5 = B.FindFootprintByReference("U5")
c = f5.GetCourtyard(pcbnew.F_CrtYd).BBox()
print(f"U5 F.CrtYd bbox x {MM(c.GetLeft()):.3f}..{MM(c.GetRight()):.3f} y {MM(c.GetTop()):.3f}..{MM(c.GetBottom()):.3f}")
mx = -1e9
for p in f5.Pads():
    r = p.GetBoundingBox()
    mx = max(mx, MM(r.GetRight()))
print(f"U5 rightmost pad copper edge = {mx:.3f}")

print("\n=== nets of parts in the corridor ===")
for ref in ("C15", "C14", "C36", "NT1", "R11", "C19"):
    f = B.FindFootprintByReference(ref)
    if not f: continue
    nets = sorted({p.GetNetname() for p in f.Pads()})
    r = f.GetBoundingBox()
    print(f"{ref:>5} val={f.GetValue():<12} nets={nets} x {MM(r.GetLeft()):.3f}..{MM(r.GetRight()):.3f}")

print("\n=== which crystal is U5's? ===")
for ref in ("Y1", "Y2", "Y3"):
    f = B.FindFootprintByReference(ref)
    if not f: continue
    p = f.GetPosition()
    nets = sorted({pd.GetNetname() for pd in f.Pads()})
    print(f"{ref} val={f.GetValue()} pos=({MM(p.x):.3f},{MM(p.y):.3f}) nets={nets}")
u5nets = sorted({p.GetNetname() for p in f5.Pads() if p.GetNetname()})
print("U5 nets:", u5nets)
