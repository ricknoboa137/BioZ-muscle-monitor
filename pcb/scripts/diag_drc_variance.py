# diag_drc_variance.py <dir-with-drcN.json>
# Diagnoses WHY kicad-cli's DRC violation count varies between identical runs on
# an identical board.  Distinguishes the candidate causes rather than calling it
# noise:
#   - if the varying violations all involve a small set of ITEMS, and each such
#     item appears in at most one violation per run, the cause is per-item
#     attribution (the clearance test stops at the first violation it finds for
#     an item, and thread scheduling decides which one that is);
#   - if entire item PAIRS appear and vanish, the cause is a missed test;
#   - if the same pair is reported with different "actual" distances, the cause
#     is differing geometry, i.e. a stale or re-computed zone fill.
import sys, os, json, re, collections, glob

R = re.compile(r"rule '([^']+)'")
ACT = re.compile(r"actual ([0-9.]+) mm")

def key(v):
    r = R.search(v["description"])
    rule = r.group(1) if r else "(builtin) " + v["type"]
    items = tuple(sorted((i.get("description", ""), round(i["pos"]["x"], 3), round(i["pos"]["y"], 3))
                         for i in v["items"] if "pos" in i))
    return (rule, items)

def main():
    d = sys.argv[1]
    runs = []
    for f in sorted(glob.glob(os.path.join(d, "drc*.json")),
                    key=lambda p: int(re.search(r"drc(\d+)", p).group(1))):
        j = json.load(open(f))
        runs.append({key(v): v["description"] for v in j.get("violations", [])
                     if v.get("severity") == "error"})
    n = len(runs)
    print(f"runs analysed: {n}   per-run counts: {[len(r) for r in runs]}")

    freq = collections.Counter()
    for r in runs:
        freq.update(r.keys())
    always = [k for k, c in freq.items() if c == n]
    never  = []
    varying = [k for k, c in freq.items() if c < n]
    print(f"unique violations seen at least once: {len(freq)}")
    print(f"  reported in EVERY run (stable core): {len(always)}")
    print(f"  reported in SOME runs only         : {len(varying)}")

    print("\n-- stable core by rule --")
    for k, c in collections.Counter(x[0] for x in always).most_common():
        print(f"  {c:4d}  {k}")
    print("\n-- varying by rule (with how many of the runs each appeared in) --")
    byrule = collections.defaultdict(list)
    for k in varying:
        byrule[k[0]].append(freq[k])
    for rule, counts in sorted(byrule.items(), key=lambda x: -len(x[1])):
        print(f"  {len(counts):4d}  {rule}   seen in {sorted(counts)} of {n} runs")

    # Does each ITEM appear in at most one violation per run?  If a set of
    # varying violations all share one item and that item is reported exactly
    # once per run, that is per-item attribution, not a missed test.
    print("\n-- items involved in varying violations --")
    itemhits = collections.defaultdict(set)
    for k in varying:
        for it in k[1]:
            itemhits[it].add(k)
    shared = {it: ks for it, ks in itemhits.items() if len(ks) > 1}
    print(f"  items appearing in more than one varying violation: {len(shared)}")
    for it, ks in sorted(shared.items(), key=lambda x: -len(x[1]))[:12]:
        percount = [sum(1 for k in ks if k in r) for r in runs]
        print(f"    {it[0]} @({it[1]},{it[2]})")
        print(f"      in {len(ks)} varying violations; reported per run: {percount}")

    # Same pair, different measured distance => geometry differed between runs.
    print("\n-- same violation reported with different 'actual' distance? --")
    diff = 0
    for k in freq:
        acts = {ACT.search(r[k]).group(1) for r in runs if k in r and ACT.search(r[k])}
        if len(acts) > 1:
            diff += 1
            print(f"    {k[0]}: actuals {sorted(acts)}")
    if not diff:
        print("    none -- geometry was identical in every run "
              "(so it is NOT a zone-refill / stale-fill effect)")

main()
