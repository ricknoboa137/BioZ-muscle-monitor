# probe_ic1_corner.py <board>
# Read-only.  Dump every SPI_SCK / V2P5F item and every pad in the IC1 corner so
# the re-plan is made against the real topology, not entry 52's summary.
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
T = pcbnew.ToMM
X0, X1, Y0, Y1 = 18.0, 26.0, 6.0, 16.0
NETS = ("SPI_SCK", "V2P5F")

print("=== pads in x %.1f..%.1f y %.1f..%.1f ===" % (X0, X1, Y0, Y1))
for f in b.Footprints():
    for p in f.Pads():
        c = p.GetCenter()
        x, y = T(c.x), T(c.y)
        if X0 <= x <= X1 and Y0 <= y <= Y1:
            n = p.GetNet()
            sz = p.GetSize(p.GetLayer() if hasattr(p, "GetLayer") else 0)
            print("  %-8s (%7.3f,%7.3f) net=%-10s size=%.3fx%.3f" % (
                f.GetReference()+"."+p.GetNumber(), x, y,
                n.GetNetname() if n else "", T(sz.x), T(sz.y)))

for net in NETS:
    print("\n=== %s ===" % net)
    for t in b.GetTracks():
        n = t.GetNet()
        if not n or n.GetNetname() != net:
            continue
        s, e = t.GetStart(), t.GetEnd()
        if isinstance(t, pcbnew.PCB_VIA):
            # GetWidth() with no layer arg opens a blocking modal on a via
            print("  VIA (%7.3f,%7.3f) dia=%.3f drill=%.3f layers %s..%s" % (
                T(s.x), T(s.y), T(t.GetWidth(t.TopLayer())), T(t.GetDrillValue()),
                b.GetLayerName(t.TopLayer()), b.GetLayerName(t.BottomLayer())))
        else:
            L = ((T(s.x)-T(e.x))**2 + (T(s.y)-T(e.y))**2) ** 0.5
            print("  TRK %-8s (%7.3f,%7.3f)-(%7.3f,%7.3f) w=%.4f len=%.3f" % (
                b.GetLayerName(t.GetLayer()), T(s.x), T(s.y), T(e.x), T(e.y),
                T(t.GetWidth()), L))
