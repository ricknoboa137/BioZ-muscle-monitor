import os, pcbnew, collections
PCBDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BF = os.path.join(PCBDIR, "BioZ-Muscle-Monitor.kicad_pcb")
b = pcbnew.LoadBoard(BF)
print("layers:", b.GetCopperLayerCount())
FP = {f.GetReference(): f for f in b.Footprints()}
u1 = FP["U1"]
# tracks per layer
c = collections.Counter()
for t in b.GetTracks():
    c[b.GetLayerName(t.GetLayer())] += 1
print("track/via items per start layer:", dict(c))
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
print("vias:", len(vias), "tracks:", len(b.GetTracks()) - len(vias))

conn = b.GetConnectivity()
print("unconnected ratsnest:", conn.GetUnconnectedCount(True))

print("\nU1 pads:")
for p in sorted(u1.Pads(), key=lambda p: p.GetNumber()):
    n = p.GetNetname()
    # count items on this net
    print("  %-4s %-12s" % (p.GetNumber(), n or "<none>"), end="")
    print()

# per-net item counts for the 5 trapped
for net in ("EL_SENN", "CAL_S", "VREF", "DRVSJ", "AFE_CS", "EL_SENP"):
    n = b.FindNet(net)
    if not n:
        print(net, "NO SUCH NET"); continue
    items = [t for t in b.GetTracks() if t.GetNetCode() == n.GetNetCode()]
    lay = collections.Counter(b.GetLayerName(t.GetLayer()) for t in items)
    print(net, "items", len(items), dict(lay))

# ratsnest detail
print("\nnets with unconnected:")
for i in range(b.GetNetCount()):
    ni = b.GetNetInfo().GetNetItem(i)
    if not ni: continue
print("netcount", b.GetNetCount())
