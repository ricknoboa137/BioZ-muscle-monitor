"""KiCad exports every copper layer as (type signal), planes included.  Left alone,
Freerouting drives signal tracks straight through the GND and Power planes and the
result passes DRC looking clean.  Patch the three non-routing layers to
(type power): GND, Power, and Escape -- Escape is U1's private WLP escape channel
and the router must not touch it.
Routing layers left as signal: F.Cu, Signal (In4), B.Cu.
"""
import re, sys

PLANES = {"Escape", "GND", "Power"}
path = sys.argv[1]
src = open(path, encoding="utf-8").read()

patched = []
def repl(m):
    name = m.group(1)
    if name in PLANES:
        patched.append(name)
        return "(layer %s\n      (type power)" % name
    return m.group(0)

out = re.sub(r"\(layer (\S+)\s*\n\s*\(type signal\)", repl, src)
if set(patched) != PLANES:
    sys.exit("REFUSING TO ROUTE: patched %s, expected %s" % (patched, sorted(PLANES)))
# Every wire already on the board is hand-routed critical work (the WLP escape,
# the patient bundle, the CAL Kelvin, the sense pair).  KiCad exports them as
# (type route), which tells Freerouting it may rip them up and re-optimise them.
# It must not: brief section 11 forbids autorouting any of it.  Marking them
# (type protect) fixes them in place -- and incidentally keeps them out of
# Freerouting 2.2.4's PolylineTrace.combine(), which recurses without bound on
# them and takes the JVM down with a StackOverflowError even at -Xss1g.
#
# Category 1 of routing-order.md -- "nets that cannot move".  These are protected
# so Freerouting cannot rip them up.  Category 2 (power/ground) and 3/4 are left
# as (type route) so the router may rework them; see the note in CHECKPOINT.md
# about category 2 being machine-routed rather than hand-routed.
CAT1 = {
    # RF chain: F.Cu only, no vias anywhere (brief 4.4)
    "ANT", "RF_A", "RF_B", "RF_ANT", "VSS_PA",
    # patient bundle and the electrode/sense/drive nets
    "PT_E1", "PT_E2", "PT_E3", "PT_E4",
    "EL_DRVP", "EL_DRVN", "EL_SENP", "EL_SENN",
    # CAL Kelvin, the AFE reference and the drive-side analog nodes
    "CAL_F", "CAL_S", "VREF", "DRVSJ", "DRVXC",
}
nwire = 0
def protect(m):
    global nwire
    if m.group(1) in CAT1:
        nwire += 1
        return "(net %s)(type protect)" % m.group(1)
    return m.group(0)

out = re.sub(r"\(net (\S+)\)\(type route\)", protect, out)
if nwire == 0:
    sys.exit("REFUSING TO ROUTE: no category-1 wires matched - check net names")

open(path, "w", encoding="utf-8").write(out)
print("patched to type power:", ", ".join(patched))
print("protected %d pre-existing hand-routed wires" % nwire)
