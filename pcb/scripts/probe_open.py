#!/usr/bin/env python
"""Read-only: values of cluster parts + occupancy map of the candidate open area."""
import pcbnew
PCB = r"C:\Users\User\Documents\BioZ-muscle-monitor\pcb\BioZ-Muscle-Monitor.kicad_pcb"
b = pcbnew.LoadBoard(PCB)
MM = pcbnew.ToMM
NM = pcbnew.FromMM

print("=== cluster part values / footprints ===")
for f in b.GetFootprints():
    r = f.GetReference()
    if r in "C11 C12 C16 C17 C18 C22 C24 C25 R10 IC1 U2 C15".split():
        print("%-4s val=%-12s fpid=%-28s layer=%s pos=%.3f,%.3f rot=%.0f" % (
            r, f.GetValue(), f.GetFPID().GetUniStringLibId(),
            b.GetLayerName(f.GetLayer()), MM(f.GetPosition().x), MM(f.GetPosition().y),
            f.GetOrientationDegrees()))

print()
print("=== rule areas (keepouts) ===")
for z in b.Zones():
    if z.GetIsRuleArea():
        bb = z.GetBoundingBox()
        print("%-20s L=%.3f T=%.3f R=%.3f B=%.3f  copper=%s tracks=%s vias=%s fp=%s" % (
            z.GetZoneName(), MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom()),
            z.GetDoNotAllowZoneFills(), z.GetDoNotAllowTracks(), z.GetDoNotAllowVias(),
            z.GetDoNotAllowFootprints()))

print()
print("=== occupancy grid, x 17..36, y 19..42, 0.5mm cells (courtyards F+B, any side) ===")
boxes = []
for f in b.GetFootprints():
    for lyr in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
        poly = f.GetCourtyard(lyr)
        if poly.OutlineCount() == 0:
            continue
        bb = poly.BBox()
        boxes.append((f.GetReference(), MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())))
# fall back: any footprint with empty courtyard -> use pad bbox
for f in b.GetFootprints():
    if f.GetCourtyard(pcbnew.F_CrtYd).OutlineCount() == 0 and f.GetCourtyard(pcbnew.B_CrtYd).OutlineCount() == 0:
        bb = f.GetBoundingBox(False, False)
        boxes.append((f.GetReference()+"*", MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())))

import math
x0, x1, y0, y1, s = 17.0, 36.0, 19.0, 42.0, 0.5
ny = int((y1-y0)/s); nx = int((x1-x0)/s)
print("     " + "".join("%d" % (int(x0+i*s) % 10) for i in range(nx)))
for j in range(ny):
    yy = y0 + j*s
    row = ""
    for i in range(nx):
        xx = x0 + i*s
        cx, cy = xx+s/2, yy+s/2
        ch = "."
        for (r, L, T, R, B) in boxes:
            if L <= cx <= R and T <= cy <= B:
                ch = r[0] if not r.endswith("*") else "?"
                break
        row += ch
    print("%5.1f%s" % (yy, row))

print()
print("=== board edge bbox ===")
bb = b.GetBoardEdgesBoundingBox()
print("L=%.3f T=%.3f R=%.3f B=%.3f" % (MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())))
print()
print("=== footprints with y>28 (bottom band), all sides ===")
for (r, L, T, R, B) in sorted(boxes, key=lambda t: t[2]):
    if B > 28:
        print("%-6s L=%7.3f T=%7.3f R=%7.3f B=%7.3f" % (r, L, T, R, B))
