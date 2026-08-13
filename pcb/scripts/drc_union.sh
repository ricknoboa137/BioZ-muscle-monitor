#!/bin/bash
# drc_union.sh [runs] [board]
# KiCad's clearance DRC is NON-DETERMINISTIC run to run on this board: the same
# .kicad_dru against the same .kicad_pcb returned 157/158/159/163 error-severity
# violations on four consecutive runs (session 11).  The width, hole_size,
# annular_width and disallow counts are perfectly stable; only the clearance
# rules (rf_clearance, analog_sense_clearance) move.  So a single run's COUNT is
# not a usable progress metric.  This unions N runs and reports unique
# violations keyed on (rule, item identities), which is stable.
set -e
P="C:/Users/User/Documents/BioZ-muscle-monitor/pcb"
N="${1:-5}"
BOARD="${2:-$P/BioZ-Muscle-Monitor.kicad_pcb}"
S="$TEMP/drc_union"
rm -rf "$S"; mkdir -p "$S"
cp "$BOARD"                            "$S/BioZ-Muscle-Monitor.kicad_pcb"
cp "$P/BioZ-Muscle-Monitor.kicad_pro"  "$S/BioZ-Muscle-Monitor.kicad_pro"
cp "$P/BioZ-Muscle-Monitor.kicad_dru"  "$S/BioZ-Muscle-Monitor.kicad_dru"
for i in $(seq 1 "$N"); do
  "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" pcb drc --severity-error \
     --format json -o "$S/drc$i.json" "$S/BioZ-Muscle-Monitor.kicad_pcb" >/dev/null 2>&1 || true
done
"C:/Users/User/anaconda3/python.exe" - "$S" "$N" <<'PY'
import json,sys,re,collections,os
S,N=sys.argv[1],int(sys.argv[2])
R=re.compile(r"rule '([^']+)'")
uni={}
percount=[]
for i in range(1,N+1):
    d=json.load(open(os.path.join(S,f"drc{i}.json")))
    vs=[v for v in d.get("violations",[]) if v.get("severity")=="error"]
    percount.append(len(vs))
    for v in vs:
        m=R.search(v["description"]); r=m.group(1) if m else "(builtin) "+v["type"]
        key=(r,tuple(sorted((i2.get("description",""),round(i2["pos"]["x"],3),round(i2["pos"]["y"],3))
                            for i2 in v["items"] if "pos" in i2)))
        uni[key]=v["description"]
    unc=len(d.get("unconnected_items",[]))
print("per-run error counts:",percount)
c=collections.Counter(k[0] for k in uni)
print(f"UNION over {N} runs: {len(uni)} unique violations")
for k,n in c.most_common(): print(f"  {n:4d}  {k}")
print("unconnected_items:",unc)
json.dump([{"rule":k[0],"items":k[1],"desc":v} for k,v in uni.items()],
          open(os.path.join(S,"union.json"),"w"),indent=1)
print("written:",os.path.join(S,"union.json"))
PY
