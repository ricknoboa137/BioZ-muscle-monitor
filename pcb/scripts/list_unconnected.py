# list_unconnected.py <board> [--json <out>]
# Enumerate the live ratsnest as concrete (net, A, B) pairs with the layers each
# end is reachable on, sorted shortest first.  Regenerate this whenever copper
# moves -- pairs-s10.json predates several sessions of edits.
#
# METHODOLOGY NOTE, and it matters (see the CHECKPOINT header): the count is
# taken from CONNECTIVITY_DATA.Build() + GetUnconnectedCount(True), the same way
# every other number in this project is taken.  RecalculateRatsnest() has
# under-reported against Build() on this board by more than 2x.  Do not mix them.
import sys, json, pcbnew

path = sys.argv[1]
b = pcbnew.LoadBoard(path)
c = b.GetConnectivity(); c.Build(b)
T = pcbnew.ToMM
print("unconnected (Build + GetUnconnectedCount(True)) = %d" % c.GetUnconnectedCount(True))

# what layers each pad / track end lives on, for planning
def item_desc(it):
    if it is None:
        return ("?", None, None)
    try:
        p = it.GetPosition()
        pos = (round(T(p.x), 3), round(T(p.y), 3))
    except Exception:
        pos = None
    kind = it.GetClass()
    name = ""
    if kind == "PAD":
        try:
            name = "%s.%s" % (it.GetParentFootprint().GetReference(), it.GetNumber())
        except Exception:
            name = "PAD"
    elif kind == "PCB_VIA":
        name = "via"
    else:
        name = kind
    return (name, pos, kind)

rows = []
def on_edge(edge):
    try:
        s = edge.GetSourceNode(); d = edge.GetTargetNode()
        si = s.Parent(); di = d.Parent()
    except Exception:
        return
    net = b.FindNet(edge.GetSourceNode().GetNet()) if hasattr(edge.GetSourceNode(), "GetNet") else None
    sn, sp, sk = item_desc(si)
    dn, dp, dk = item_desc(di)
    nm = ""
    try:
        nm = si.GetNet().GetNetname()
    except Exception:
        pass
    if sp and dp:
        L = ((sp[0]-dp[0])**2 + (sp[1]-dp[1])**2) ** 0.5
    else:
        L = -1
    rows.append({"net": nm, "a": sn, "apos": sp, "b": dn, "bpos": dp,
                 "len": round(L, 3)})

c.RunOnUnconnectedEdges(on_edge)
rows.sort(key=lambda r: r["len"])
print("\n%-12s %-10s %-18s %-10s %-18s %8s" % ("net", "from", "at", "to", "at", "len(mm)"))
for r in rows:
    print("%-12s %-10s %-18s %-10s %-18s %8.3f" % (
        r["net"], r["a"], str(r["apos"]), r["b"], str(r["bpos"]), r["len"]))
print("\ntotal ratsnest edges listed: %d" % len(rows))

if "--json" in sys.argv:
    out = sys.argv[sys.argv.index("--json") + 1]
    json.dump(rows, open(out, "w"), indent=1)
    print("written:", out)
