"""Build a CORRECTED BioZ-Muscle-Monitor.kicad_dru into the scratch project.

Two independent defects were established by experiment in session 10, both of
which have made the project's custom rules inert since they were written:

 (1) rule `pads_inside_one_package` uses `A.Footprint == B.Footprint`, which is
     not a valid property in KiCad's DRC expression language.  KiCad discards
     the ENTIRE rules file on that error, silently -- proven by bisect_dru.py,
     and by the control experiment where a track planted straight through
     ANTENNA_KEEPOUT drew no antenna_keepout violation at all.

 (2) rule order.  In KiCad the LAST matching rule wins for a given constraint
     type, and the file put the permissive catch-alls `general_track_width`
     (0.127 mm) and `general_clearance` (0.127 mm) at the END.  They therefore
     overrode power_width / signal_width / patient_width / patient_clearance /
     rf_clearance / analog_sense_clearance for every item outside U1_ESCAPE.
     Measured directly: power_width alone -> 6 errors; power_width THEN
     general_track_width -> 2; general_track_width THEN power_width -> 8.

This file re-emits every rule unchanged in wording, ordered least-specific
first, so that the specific brief-derived constraints actually bind.  NOTHING is
relaxed and no constraint is dropped; the only rule not reproduced is the
unparseable generic one, whose intent cannot be expressed in the rule language
and is therefore carried as a manual check instead.
"""
import os
import re

PCB = r"C:\Users\User\Documents\BioZ-muscle-monitor\pcb"
SRC = os.path.join(PCB, "BioZ-Muscle-Monitor.kicad_dru")

# least specific first; the LAST matching rule wins, so the most specific
# exceptions (package-internal geometry) must come last.
ORDER = [
    "general_track_width", "general_clearance",
    "power_width", "signal_width", "patient_width",
    "analog_sense_clearance", "patient_clearance", "patient_to_switching",
    "rf_internal", "rf_clearance", "rf_no_vias", "rf_top_layer_only",
    "wlp_track_width", "wlp_clearance", "wlp_annular", "wlp_microvia_drill",
    "patient_not_over_gndd_split", "split_no_copper",
    "antenna_keepout", "antenna_keepout_no_vias_even_rf",
    "through_via_min_drill",
    "lfcsp_internal_U10", "lfcsp_internal_U14", "fc2qfn_internal_U7",
    "wlp_internal_U1", "qfn48_internal_U5", "qfn16_internal_U8",
    "nettie_NT1",
]
# deliberately NOT re-emitted -- unparseable, see module docstring
DROPPED = ["pads_inside_one_package"]


def split_rules(src):
    rules, depth, buf = {}, 0, ""
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
                nm = re.search(r'\(rule\s+"([^"]+)"', buf).group(1)
                rules[nm] = buf
    return rules


def build():
    rules = split_rules(open(SRC).read())
    missing = [n for n in ORDER if n not in rules]
    extra = [n for n in rules if n not in ORDER and n not in DROPPED]
    if missing:
        raise SystemExit("ORDER names rules that do not exist: %s" % missing)
    if extra:
        raise SystemExit("rules in the file that ORDER does not place: %s" % extra)
    out = ["(version 1)", "",
           "# Rebuilt by scripts/make_fixed_dru.py -- see that file for why.",
           "# ORDER MATTERS: the LAST matching rule wins, so general catch-alls",
           "# come first and package-specific exceptions come last.  Do not",
           "# move general_track_width / general_clearance back to the bottom.",
           ""]
    for n in ORDER:
        out.append(rules[n].strip())
        out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    import sys
    dst = sys.argv[1]
    open(dst, "w").write(build())
    print("wrote", dst)
