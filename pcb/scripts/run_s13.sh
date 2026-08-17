#!/bin/bash
# run_s13.sh <pairfile> [board]
# Walk a ratsnest pair list ONE PAIR AT A TIME through try_connect.py, running a
# full DRC after each.  A pair is kept only if unconnected FELL and the DRC
# error count did NOT rise; otherwise the board is restored from the per-pair
# snapshot.  Never batches -- a bad connection can never hide behind a good one.
# Pair file lines: net|ax,ay|bx,by[|extra try_connect args]
PY="C:/Program Files/KiCad/10.0/bin/python.exe"
KICLI="C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
P="C:/Users/User/Documents/BioZ-muscle-monitor/pcb"
PAIRS="$1"
BOARD="${2:-$P/BioZ-Muscle-Monitor.kicad_pcb}"
SNAP="$TEMP/s13_snap.kicad_pcb"

count() {
  "$KICLI" pcb drc --severity-error --format json -o "$TEMP/s13_drc.json" "$BOARD" >/dev/null 2>&1
  "C:/Users/User/anaconda3/python.exe" -c "
import json,sys
d=json.load(open(r'$TEMP/s13_drc.json'))
print(len([x for x in d.get('violations',[]) if x.get('severity')=='error']),
      len(d.get('unconnected_items',[])))"
}

read BV BU <<<"$(count)"
echo "BASELINE: $BV violations, $BU unconnected"
KEPT=0
while IFS='|' read -r NET A B EXTRA; do
  [ -z "$NET" ] && continue
  case "$NET" in \#*) continue;; esac
  cp "$BOARD" "$SNAP"
  echo "--- $NET  $A -> $B"
  if ! "$PY" "$P/scripts/try_connect.py" "$BOARD" "$NET" "$A" "$B" $EXTRA 2>&1 \
        | grep -v "memory leak\|image handler" | sed 's/^/    /'; then :; fi
  read NV NU <<<"$(count)"
  if [ "$NU" -lt "$BU" ] && [ "$NV" -le "$BV" ]; then
    echo "    KEPT   violations $BV->$NV  unconnected $BU->$NU"
    BV=$NV; BU=$NU; KEPT=$((KEPT+1))
  else
    cp "$SNAP" "$BOARD"
    echo "    reject (would be $NV/$NU) -- board restored"
  fi
done < "$PAIRS"
echo "RESULT: kept $KEPT; now $BV violations, $BU unconnected"
