#!/bin/sh
# Walk the pair list, one pair at a time, through try_pair.sh.  Never batches:
# every accepted placement is DRC-proven before the next is attempted, so a bad
# one can never be hidden behind a good one.  Writes a running log.
PCB=/c/Users/User/Documents/BioZ-muscle-monitor/pcb
LOG=$PCB/s10-progress.log
UNC=${2:-51}
for IDX in $1; do
  if sh "$PCB/scripts/try_pair.sh" "$IDX" "$UNC" >>"$LOG" 2>&1; then
    NEW=$(grep "^PAIR $IDX: errors" "$LOG" | tail -1 | sed 's/.*unconnected=\([0-9]*\).*/\1/')
    echo "pair $IDX ACCEPTED  unconnected $UNC -> $NEW"
    UNC=$NEW
  else
    echo "pair $IDX open ($UNC)"
  fi
done
echo "FINAL unconnected=$UNC"
