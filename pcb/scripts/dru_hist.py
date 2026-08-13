# dru_hist.py <drc.json> [--list RULE]
# Histogram of error-severity DRC violations BY CUSTOM RULE NAME (parsed out of
# the description -- KiCad's JSON "type" field carries the constraint type, not
# the rule that fired, so a raw type histogram cannot tell power_width from
# signal_width).  Run with anaconda python; no pcbnew needed.
import json, sys, re, collections

RULE = re.compile(r"rule '([^']+)'")

def rule_of(v):
    m = RULE.search(v.get("description", ""))
    return m.group(1) if m else "(builtin) " + v.get("type", "?")

def main():
    path = sys.argv[1]
    want = None
    if "--list" in sys.argv:
        want = sys.argv[sys.argv.index("--list") + 1]
    d = json.load(open(path))
    v = [x for x in d.get("violations", []) if x.get("severity") == "error"]
    c = collections.Counter(rule_of(x) for x in v)
    print(f"TOTAL error-severity violations: {len(v)}")
    for k, n in c.most_common():
        print(f"  {n:4d}  {k}")
    print("unconnected_items:", len(d.get("unconnected_items", [])))
    if want:
        print(f"\n--- {want} ---")
        for x in v:
            if rule_of(x) == want:
                items = "; ".join(
                    f"{i.get('description','?')} @ ({i['pos']['x']:.3f},{i['pos']['y']:.3f})"
                    for i in x.get("items", []) if "pos" in i)
                print(" *", x["description"])
                print("   ", items)

if __name__ == "__main__":
    main()
