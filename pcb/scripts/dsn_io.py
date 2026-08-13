import os, sys, pcbnew
PCBDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BF = os.path.join(PCBDIR, "BioZ-Muscle-Monitor.kicad_pcb")
mode = sys.argv[1]
path = sys.argv[2]
b = pcbnew.LoadBoard(BF)
if mode == "export":
    # Filled copper pours export as solid obstacles on every layer.  With them in
    # the DSN, Freerouting has almost no usable F.Cu and plateaus (77 of 119 nets
    # unrouted, score frozen from pass 1).  Drop the pours from the *in-memory*
    # board only -- the file on disk keeps them, and they are refilled after the
    # SES comes back.  Rule areas (the antenna keepout) are kept: those are real.
    # MEASURED 2026-08-07: dropping the pours made the result WORSE, not better
    # (93-94 unrouted and oscillating, vs 77 with the pours in).  Left in place,
    # off by default, so the next agent does not spend another hour rediscovering
    # it.  Set DROP_POURS = True to re-test.
    DROP_POURS = False
    doomed = [z for z in b.Zones() if not z.GetIsRuleArea()] if DROP_POURS else []
    for z in doomed:
        b.Remove(z)
    print("dropped %d copper pours from the export copy" % len(doomed))
    ok = pcbnew.ExportSpecctraDSN(b, path)
    print("export", ok, path)
else:
    ok = pcbnew.ImportSpecctraSES(b, path)
    print("import", ok, path)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(BF)
    print("saved", BF)
