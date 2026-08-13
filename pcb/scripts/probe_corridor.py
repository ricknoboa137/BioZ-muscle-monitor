"""Read-only: measure the corridor to the right of U5, between U5's cluster and H1.

Prints every footprint's bbox (courtyard-ish via GetBoundingBox) sorted by x, plus
rule areas, plus the extent of copper items in the band of U5's y-range.
No writes.
"""
import sys, pcbnew

B = pcbnew.LoadBoard(r"C:\Users\User\Documents\BioZ-muscle-monitor\pcb\BioZ-Muscle-Monitor.kicad_pcb")
MM = pcbnew.ToMM

def bb(item):
    r = item.GetBoundingBox()
    return (MM(r.GetLeft()), MM(r.GetTop()), MM(r.GetRight()), MM(r.GetBottom()))

fps = {}
for f in B.GetFootprints():
    ref = f.GetReference()
    p = f.GetPosition()
    fps[ref] = (MM(p.x), MM(p.y), bb(f))

print("=== U5 / H1 ===")
for r in ("U5", "H1", "U7", "U8"):
    if r in fps:
        x, y, box = fps[r]
        print(f"{r}: pos=({x:.3f},{y:.3f}) bbox=({box[0]:.3f},{box[1]:.3f})-({box[2]:.3f},{box[3]:.3f})")

if "U5" not in fps:
    sys.exit("no U5")
u5x, u5y, u5b = fps["U5"]

# U5 pad extent (real footprint extent, not silk-inflated bbox)
f5 = B.FindFootprintByReference("U5")
px = [MM(p.GetPosition().x) for p in f5.Pads()]
py = [MM(p.GetPosition().y) for p in f5.Pads()]
pw = max(MM(p.GetSize().x) for p in f5.Pads())
ph = max(MM(p.GetSize().y) for p in f5.Pads())
print(f"U5 pad centres x {min(px):.3f}..{max(px):.3f}  y {min(py):.3f}..{max(py):.3f}  maxpad {pw:.3f}x{ph:.3f}")
print(f"U5 pad copper extent x {min(px)-pw/2:.3f}..{max(px)+pw/2:.3f}  y {min(py)-ph/2:.3f}..{max(py)+ph/2:.3f}")
print(f"U5 courtyard/bbox right edge = {u5b[2]:.3f}")

# everything whose bbox overlaps U5's y band, sorted by left edge
ylo, yhi = u5b[1], u5b[3]
print(f"\n=== footprints overlapping U5 y-band {ylo:.2f}..{yhi:.2f}, sorted by left edge ===")
rows = []
for ref, (x, y, box) in fps.items():
    if box[3] < ylo or box[1] > yhi:
        continue
    rows.append((box[0], ref, x, y, box))
for left, ref, x, y, box in sorted(rows):
    tag = ""
    if box[0] > u5b[2]:
        tag = f"  <-- RIGHT of U5 by {box[0]-u5b[2]:.3f}mm"
    print(f"{ref:>6}  pos=({x:8.3f},{y:8.3f})  bbox x {box[0]:8.3f}..{box[2]:8.3f}  y {box[1]:7.3f}..{box[3]:7.3f}{tag}")

print("\n=== rule areas / zones (keepouts) ===")
for z in B.Zones():
    if z.GetIsRuleArea():
        r = z.GetBoundingBox()
        print(f"RULEAREA '{z.GetZoneName()}' x {MM(r.GetLeft()):.3f}..{MM(r.GetRight()):.3f} "
              f"y {MM(r.GetTop()):.3f}..{MM(r.GetBottom()):.3f} "
              f"tracks_not_allowed={z.GetDoNotAllowTracks()} vias={z.GetDoNotAllowVias()} pours={z.GetDoNotAllowZoneFills()}")

r = B.GetBoardEdgesBoundingBox()
print(f"\nEdge.Cuts bbox: x {MM(r.GetLeft()):.3f}..{MM(r.GetRight()):.3f} y {MM(r.GetTop()):.3f}..{MM(r.GetBottom()):.3f}")
