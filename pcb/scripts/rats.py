import os, pcbnew, collections
PCBDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BF = os.path.join(PCBDIR, "BioZ-Muscle-Monitor.kicad_pcb")
b = pcbnew.LoadBoard(BF)
b.BuildConnectivity()
conn = b.GetConnectivity()
print("total unconnected:", conn.GetUnconnectedCount(True))
cnt = collections.Counter()
for i in range(1, b.GetNetCount()):
    ni = b.GetNetInfo().GetNetItem(i)
    if ni is None: continue
    name = ni.GetNetname()
    rn = conn.GetRatsnestForNet(i)
    if rn is None: continue
    try:
        edges = rn.GetEdges()
        n = sum(1 for e in edges if e.IsVisible() or True)
    except Exception as ex:
        n = -1
    if n:
        cnt[name] = n
for k, v in sorted(cnt.items(), key=lambda kv: -kv[1]):
    print("  %-14s %d" % (k, v))
