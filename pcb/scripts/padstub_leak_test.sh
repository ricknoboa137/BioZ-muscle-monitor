#!/bin/bash
# padstub_leak_test.sh [board]
# Control experiment for the pad_stub_width exception (entry 53).  A scoped
# exception is only safe if it is (a) still a FLOOR inside its own areas and
# (b) confined to those areas.  A clean DRC run proves neither, so both are
# tested by planting geometry that MUST be caught.
#
#   TEST 1  a 0.100 mm POWER_LOW track INSIDE a PAD_STUB box
#           -> must fire pad_stub_width (the 0.150 floor is still enforced)
#   TEST 2  a 0.200 mm POWER_LOW track 1 mm OUTSIDE the same box
#           -> must fire power_width (the exception has not leaked outwards)
#   TEST 3  the real stubs, untouched
#           -> must NOT fire anything (the exception actually works)
set -e
P="C:/Users/User/Documents/BioZ-muscle-monitor/pcb"
BOARD="${1:-$P/BioZ-Muscle-Monitor.kicad_pcb}"
S="$TEMP/padstub_leak"
rm -rf "$S"; mkdir -p "$S"
cp "$BOARD"                            "$S/BioZ-Muscle-Monitor.kicad_pcb"
cp "$P/BioZ-Muscle-Monitor.kicad_pro"  "$S/BioZ-Muscle-Monitor.kicad_pro"
cp "$P/BioZ-Muscle-Monitor.kicad_dru"  "$S/BioZ-Muscle-Monitor.kicad_dru"

"C:/Program Files/KiCad/10.0/bin/python.exe" - "$S/BioZ-Muscle-Monitor.kicad_pcb" <<'PY'
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
net = b.FindNet("VDD_nRF")
assert net, "VDD_nRF not found"
def track(x1, y1, x2, y2, w):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
    t.SetWidth(pcbnew.FromMM(w)); t.SetLayer(pcbnew.B_Cu); t.SetNet(net)
    b.Add(t)
# TEST 1: inside the U5.10 PAD_STUB box (x 31.70..32.30, y 18.10..18.70)
track(31.85, 18.20, 32.15, 18.20, 0.100)
# TEST 2: 1 mm below that box, same net, same layer, 0.200 mm
track(31.85, 19.90, 32.15, 19.90, 0.200)
b.Save(sys.argv[1])
print("planted 2 test tracks on B.Cu")
PY

"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" pcb drc --severity-error --format json \
    -o "$S/drc.json" "$S/BioZ-Muscle-Monitor.kicad_pcb" >/dev/null 2>&1 || true

"C:/Users/User/anaconda3/python.exe" - "$S/drc.json" <<'PY'
import json, sys, re
d = json.load(open(sys.argv[1]))
R = re.compile(r"rule '([^']+)'")
hits = []
for v in d.get("violations", []):
    if v.get("severity") != "error":
        continue
    m = R.search(v.get("description", ""))
    r = m.group(1) if m else "(builtin)"
    for it in v.get("items", []):
        p = it.get("pos")
        if p:
            hits.append((r, round(p["x"], 2), round(p["y"], 2)))
def at(rule, y):
    return any(h[0] == rule and abs(h[2] - y) < 0.35 and 31.5 < h[1] < 32.5 for h in hits)
t1 = at("pad_stub_width", 18.20)
t2 = at("power_width",   19.90)
print("  TEST 1  0.100 mm INSIDE  PAD_STUB -> pad_stub_width : %s" % ("FIRED  (floor still enforced)" if t1 else "MISSING"))
print("  TEST 2  0.200 mm OUTSIDE PAD_STUB -> power_width    : %s" % ("FIRED  (no leak outwards)" if t2 else "MISSING"))
# TEST 3 checks ONLY the six PAD_STUB boxes.  The group-2 congestion violations
# elsewhere on the board (SPI_SCK / V2P5F in the IC1 corner, the VDD_nRF 2.77 mm
# run) are expected to remain and are NOT what this exception was for.
BOXES = [(31.70, 32.30, 18.10, 18.70), (33.60, 34.45, 13.35, 13.85),
         (26.75, 27.60, 16.55, 17.05), (27.35, 28.65, 11.15, 12.00),
         (30.95, 31.56, 11.15, 12.30), (41.50, 42.00, 17.81, 19.01)]
real = [h for h in hits
        if h[0] in ("pad_stub_width", "power_width", "signal_width")
        and not (abs(h[2] - 18.20) < 0.35 or abs(h[2] - 19.90) < 0.35)
        and any(x0 <= h[1] <= x1 and y0 <= h[2] <= y1 for x0, x1, y0, y1 in BOXES)]
print("  TEST 3  real stubs inside the boxes now clean      : %s"
      % ("PASS (0 width violations in any PAD_STUB box)" if not real else "FAIL %r" % real))
if not (t1 and t2 and not real):
    print("\nFAIL: the pad_stub_width exception is not behaving as scoped.")
    sys.exit(1)
print("\nPASS: pad_stub_width is a floor, is confined to its areas, and closes the real stubs.")
PY
