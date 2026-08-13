"""Find which rule in BioZ-Muscle-Monitor.kicad_dru makes KiCad discard the file.

Established by experiment in session 10: a minimal one-rule .kicad_dru IS loaded
and enforced by kicad-cli, but the project's real .kicad_dru produces no custom
violations at all -- not even from its antenna_keepout disallow rule with a track
planted straight through the keepout.  KiCad drops the WHOLE file on a parse or
validation error, silently, so every "0 DRC errors" this project has recorded was
measured against the default rules only.

Method: feed the scratch project one rule at a time (each preceded by the same
control rule that is KNOWN to fire) and see whether the control still fires.  If
adding rule N kills the control, rule N is what invalidates the file.
Runs entirely in %TEMP%\\drutest -- the live board is never touched.
"""
import os
import re
import json
import subprocess

PCB = r"C:\Users\User\Documents\BioZ-muscle-monitor\pcb"
SD = os.path.join(os.environ["TEMP"], "drutest")
DRU = os.path.join(SD, "BioZ-Muscle-Monitor.kicad_dru")
BRD = os.path.join(SD, "BioZ-Muscle-Monitor.kicad_pcb")
KCLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
OUT = os.path.join(SD, "bisect.json")

CONTROL = """(rule "zz_control_width"
  (constraint track_width (min 20mil))
  (condition "A.NetClass == 'POWER_HIGH'"))
"""

src = open(os.path.join(PCB, "BioZ-Muscle-Monitor.kicad_dru")).read()
# split into top-level (rule ...) blocks by paren depth
rules, depth, buf = [], 0, ""
for ch in src:
    if ch == "(":
        if depth == 0:
            buf = ""
        depth += 1
    if depth > 0:
        buf += ch
    if ch == ")":
        depth -= 1
        if depth == 0 and buf.lstrip().startswith("(rule"):
            rules.append(buf)
print("parsed %d rule blocks" % len(rules))


def control_fires(text):
    open(DRU, "w").write("(version 1)\n" + text + "\n" + CONTROL)
    subprocess.run([KCLI, "pcb", "drc", "--format", "json",
                    "--severity-error", "--output", OUT, BRD],
                   capture_output=True)
    d = json.load(open(OUT))
    return any(v["type"] == "track_width" and "zz_control" in v["description"]
               for v in d["violations"])


assert control_fires(""), "control does not fire even alone -- test invalid"
print("control fires on its own: OK\n")

bad = []
for i, r in enumerate(rules):
    name = re.search(r'\(rule\s+"([^"]+)"', r)
    name = name.group(1) if name else "?"
    ok = control_fires(r)
    print("  %-38s %s" % (name, "ok" if ok else "*** KILLS THE FILE ***"))
    if not ok:
        bad.append((name, r))

print("\n%d rule(s) invalidate the file:" % len(bad))
for name, r in bad:
    print("\n--- %s ---\n%s" % (name, r))
