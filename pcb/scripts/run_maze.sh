#!/bin/bash
# run_maze.sh <pairfile> [board]
# Same discipline as run_s13.sh -- one pair at a time, full DRC after each,
# board restored unless unconnected FELL and the violation count did not rise --
# but driving maze_route.py instead of the fixed-shape catalogue.
PY="C:/Program Files/KiCad/10.0/bin/python.exe"
KICLI="C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
P="C:/Users/User/Documents/BioZ-muscle-monitor/pcb"
PAIRS="$1"
BOARD="${2:-$P/BioZ-Muscle-Monitor.kicad_pcb}"
SNAP="$TEMP/s13_msnap.kicad_pcb"

count() {
  "$KICLI" pcb drc --severity-error --format json -o "$TEMP/s13_mdrc.json" "$BOARD" >/dev/null 2>&1
  "C:/Users/User/anaconda3/python.exe" -c "
import json
d=json.load(open(r'$TEMP/s13_mdrc.json'))
print(len([x for x in d.get('violations',[]) if x.get('severity')=='error']),
      len(d.get('unconnected_items',[])))"
}

read BV BU <<<"$(count)"
echo "BASELINE: $BV violations, $BU unconnected"
KEPT=0; FAILW=0; FAILR=0
while IFS='|' read -r NET A B EXTRA; do
  [ -z "$NET" ] && continue
  case "$NET" in \#*) continue;; esac
  cp "$BOARD" "$SNAP"
  OUT=$("$PY" "$P/scripts/maze_route.py" "$BOARD" "$NET" "$A" "$B" $EXTRA 2>&1 \
        | grep -v "memory leak\|image handler")
  if echo "$OUT" | grep -q "EXACT CHECK FAILED"; then
     WHY="pad-exit/width"; FAILW=$((FAILW+1))
  elif echo "$OUT" | grep -q "NO ROUTE"; then
     WHY="no route"; FAILR=$((FAILR+1))
  else WHY=""; fi
  read NV NU <<<"$(count)"
  if [ "$NU" -lt "$BU" ] && [ "$NV" -le "$BV" ]; then
    echo "KEPT   $NET  $A -> $B   violations $BV->$NV  unconnected $BU->$NU"
    BV=$NV; BU=$NU; KEPT=$((KEPT+1))
  else
    cp "$SNAP" "$BOARD"
    echo "open   $NET  $A -> $B   ($WHY)"
  fi
done < "$PAIRS"
echo "RESULT: kept $KEPT; blocked-by-width $FAILW; no-route $FAILR; now $BV violations, $BU unconnected"
