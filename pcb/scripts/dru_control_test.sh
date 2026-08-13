#!/bin/bash
# dru_control_test.sh
# THE control experiment for "is BioZ-Muscle-Monitor.kicad_dru actually loaded?"
# KiCad silently discards every rule in the file if any one of them fails to
# parse, and then reports "Found 0 violations" with no warning at all.  The only
# way to know the file is live is to plant geometry that MUST trip named rules
# and confirm those exact rule names come back.
# RUN THIS AFTER EVERY EDIT TO THE .kicad_dru.  Exit 0 = file is live.
set -e
P="C:/Users/User/Documents/BioZ-muscle-monitor/pcb"
S="$TEMP/dru_control"
rm -rf "$S"; mkdir -p "$S"
cp "$P/BioZ-Muscle-Monitor.kicad_pcb"  "$S/BioZ-Muscle-Monitor.kicad_pcb"
cp "$P/BioZ-Muscle-Monitor.kicad_pro"  "$S/BioZ-Muscle-Monitor.kicad_pro"
cp "$P/BioZ-Muscle-Monitor.kicad_dru"  "$S/BioZ-Muscle-Monitor.kicad_dru"
"C:/Program Files/KiCad/10.0/bin/python.exe" "$P/scripts/plant_bad.py" "$S/BioZ-Muscle-Monitor.kicad_pcb"
"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" pcb drc --severity-error --format json \
    -o "$S/drc.json" "$S/BioZ-Muscle-Monitor.kicad_pcb" >/dev/null 2>&1 || true
"C:/Users/User/anaconda3/python.exe" - "$S/drc.json" <<'PY'
import json,sys,re
want={"patient_width","split_no_copper","split_no_ground_track","antenna_keepout"}
R=re.compile(r"rule '([^']+)'")
d=json.load(open(sys.argv[1]))
got=set()
for v in d.get("violations",[]):
    m=R.search(v.get("description",""))
    if m: got.add(m.group(1))
missing=want-got
for r in sorted(want):
    print(("  FIRED   " if r in got else "  MISSING ")+r)
if missing:
    print("\nFAIL: the .kicad_dru is NOT in force (or these rules are wrong).")
    print("Missing:", ", ".join(sorted(missing)))
    sys.exit(1)
print("\nPASS: .kicad_dru is loaded and these rules are binding.")
PY
