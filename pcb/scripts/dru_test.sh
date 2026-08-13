#!/bin/bash
# dru_test.sh <dru-file> [board-file] [scratch-name]
# Copies board + .kicad_pro + the given .kicad_dru into a fresh scratch project
# (entry 34 trap: a board copied WITHOUT its .kicad_pro silently falls back to
# KiCad defaults and manufactures phantom results), runs kicad-cli DRC, and
# prints an error-severity violation histogram by rule name.
set -e
P="C:/Users/User/Documents/BioZ-muscle-monitor/pcb"
DRU="$1"
BOARD="${2:-$P/BioZ-Muscle-Monitor.kicad_pcb}"
NAME="${3:-drutest}"
S="$TEMP/$NAME"
rm -rf "$S"; mkdir -p "$S"
cp "$BOARD"                          "$S/BioZ-Muscle-Monitor.kicad_pcb"
cp "$P/BioZ-Muscle-Monitor.kicad_pro" "$S/BioZ-Muscle-Monitor.kicad_pro"
cp "$DRU"                            "$S/BioZ-Muscle-Monitor.kicad_dru"
"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" pcb drc \
    --severity-error --format json --exit-code-violations \
    -o "$S/drc.json" "$S/BioZ-Muscle-Monitor.kicad_pcb" >/dev/null 2>&1 || true
"C:/Users/User/anaconda3/python.exe" - "$S/drc.json" <<'PY'
import json,sys,collections
d=json.load(open(sys.argv[1]))
v=d.get("violations",[])
c=collections.Counter(x["type"] for x in v)
print("TOTAL error-severity violations:", len(v))
for k,n in c.most_common(): print(f"  {n:4d}  {k}")
print("unconnected_items:", len(d.get("unconnected_items",[])))
print("json:", sys.argv[1])
PY
