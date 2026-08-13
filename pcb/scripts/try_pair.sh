#!/bin/sh
# Close ONE unconnected pair and prove it did no harm, or put the board back.
#
# The whole discipline of this session is in this script: nothing is trusted
# because it placed cleanly, only because kicad-cli DRC afterwards shows zero
# errors AND a strictly lower unconnected count.  The second half of that test
# is the pour-severance guard (entry 20) -- a track can sever a copper pour with
# DRC saying nothing at all, and the unconnected count is the only symptom.
#
# Usage:  try_pair.sh <pair_index> <expected_unconnected_before>
set -e
PCB=/c/Users/User/Documents/BioZ-muscle-monitor/pcb
BRD=$PCB/BioZ-Muscle-Monitor.kicad_pcb
KCLI="/c/Program Files/KiCad/10.0/bin/kicad-cli.exe"
PY="/c/Program Files/KiCad/10.0/bin/python.exe"
SAFE=$TEMP/s10-safe.kicad_pcb
IDX=$1
BEFORE=$2

cp "$BRD" "$SAFE"
if ! "$PY" "$PCB/scripts/route_s10.py" "$IDX" --place; then
  echo "PAIR $IDX: no candidate, board untouched"
  cp "$SAFE" "$BRD"
  exit 2
fi

OUT=$("$KCLI" pcb drc --format json --severity-error \
      --output "$TEMP/drc-try.json" "$BRD" 2>&1)
ERR=$(echo "$OUT" | grep -o '[0-9]* violations' | grep -o '[0-9]*')
UNC=$(echo "$OUT" | grep -o '[0-9]* unconnected' | grep -o '[0-9]*')
echo "PAIR $IDX: errors=$ERR unconnected=$UNC (was $BEFORE)"

if [ "$ERR" != "0" ] || [ "$UNC" -ge "$BEFORE" ]; then
  echo "PAIR $IDX: REJECTED -- reverting"
  cp "$SAFE" "$BRD"
  exit 3
fi
echo "PAIR $IDX: ACCEPTED"
exit 0
