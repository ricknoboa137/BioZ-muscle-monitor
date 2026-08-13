"""Read-only: is C24.2 (and the other decoupling ground pads) connected?

Uses the zone-fill + Build() protocol from entry 21 -- RecalculateRatsnest()
alone under-reports.  No PCB_VIA.GetWidth() calls anywhere in here.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew

PCBDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BF = os.path.join(PCBDIR, "BioZ-Muscle-Monitor.kicad_pcb")
T = pcbnew.ToMM

b = pcbnew.LoadBoard(BF)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
cn = b.GetConnectivity()
cn.Build(b)
cn.RecalculateRatsnest()
print("unconnected (in-process, post-fill):", cn.GetUnconnectedCount(False))

# Which pads of interest are isolated on their own island?
WATCH = [("C11", "2"), ("C12", "2"), ("C17", "2"), ("C18", "2"), ("C24", "2"),
         ("C24", "1"), ("C22", "2"), ("C16", "2")]
print("\n-- watched pads --")
for ref, num in WATCH:
    fp = b.FindFootprintByReference(ref)
    if fp is None:
        print("  %-6s footprint not found" % ref)
        continue
    pad = fp.FindPadByNumber(num)
    if pad is None:
        print("  %s.%s pad not found" % (ref, num))
        continue
    q = pad.GetPosition()
    net = pad.GetNetname()
    print("  %-6s pad %s  net=%-10s at (%.3f,%.3f)"
          % (ref, num, net, T(q.x), T(q.y)))

# Ratsnest endpoints, so we can see exactly what is still open and where.
print("\n-- unconnected pairs by net (from ratsnest) --")
tot = 0
for i in range(1, b.GetNetCount()):
    ni = b.GetNetInfo().GetNetItem(i)
    if ni is None:
        continue
    rn = cn.GetRatsnestForNet(i)
    if rn is None:
        continue
    edges = list(rn.GetEdges())
    if not edges:
        continue
    print("  %s: %d" % (ni.GetNetname(), len(edges)))
    tot += len(edges)
    for e in edges:
        a, z = e.GetSourceNode(), e.GetTargetNode()
        print("      (%.3f,%.3f) -> (%.3f,%.3f)"
              % (T(int(a.Pos().x)), T(int(a.Pos().y)),
                 T(int(z.Pos().x)), T(int(z.Pos().y))))
print("total ratsnest edges:", tot)
