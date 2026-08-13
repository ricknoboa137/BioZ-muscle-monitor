# refill_zones.py <board>
# Refills every copper zone and rebuilds connectivity, then saves.
# WHY THIS MATTERS (session 11): the stored pour fills on this board were
# computed while BioZ-Muscle-Monitor.kicad_dru was silently void, so the pours
# backed off from the patient nets by the NET-CLASS clearance, not by the
# custom patient_clearance rule.  That produced 18 patient_clearance violations
# all reading exactly "actual 0.5005 mm" against Zone 'GNDA_F.Cu'.  The copper
# is not misrouted; the pour is simply stale.
# Prints the unconnected count before and after -- entry 20's pour-severance
# trap means a refill CAN change connectivity, and that must never pass silently.
# Entry 21: RecalculateRatsnest() alone LIES; only connectivity.Build() is honest.
import sys, pcbnew

def unconnected(b):
    # API note, verified against the live pcbnew 10.0: GetUnconnectedCount lives
    # on CONNECTIVITY_DATA, NOT on BOARD.  b.GetUnconnectedCount() does not exist.
    c = b.GetConnectivity()
    c.Build(b)
    return c.GetUnconnectedCount(True)

def main():
    path = sys.argv[1]
    b = pcbnew.LoadBoard(path)
    before = unconnected(b)
    zones = b.Zones()
    filler = pcbnew.ZONE_FILLER(b)
    ok = filler.Fill(zones)
    after = unconnected(b)
    print(f"zones refilled: {len(zones)}  filler_ok={ok}")
    print(f"unconnected before={before}  after={after}")
    if after > before:
        print("!! REFILL SEVERED SOMETHING -- unconnected went UP. Not saving.")
        sys.exit(1)
    b.Save(path)
    print("saved:", path)

main()
