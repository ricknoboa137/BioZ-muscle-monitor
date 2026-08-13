# true_clearance.py <board> <NETCLASS> <min_mm> [--vs-class OTHER] [--same]
# DETERMINISTIC ground truth for a clearance rule.  Enumerates every copper pair
# on the same layer whose edge-to-edge gap is below <min_mm>, and prints them in
# sorted order.  Same board in, same list out, every time.
#
# WHY THIS EXISTS (session 11).  kicad-cli's DRC UNDER-REPORTS overlapping
# clearance violations and the subset it reports VARIES BETWEEN IDENTICAL RUNS.
# Proven: on the rf_clearance rule, direct geometry finds FIVE real ANT-vs-VSS_PA
# violations (gaps 0.2250, 0.2250, 0.2550, 0.2550, 0.4650 against a 0.600 floor)
# while kicad-cli reports only two to four of them, a different subset each run.
# The violations are real; the reporting is lossy.  So a DRC clearance COUNT is
# not a work list and not a progress metric.  This script is the work list.
#
# Consequence for the rest of the project: a non-zero clearance count is a lower
# bound only.  ZERO, however, is trustworthy -- there is nothing for the reporter
# to race over -- so "closed" still means "reports zero on every run", and that
# is how the closed categories in this project were signed off.
#
# Run with KiCad's bundled python.  Read-only; never writes the board.
import sys, math, pcbnew

MM = pcbnew.ToMM

def endpoints(t):
    return ((MM(t.GetStart().x), MM(t.GetStart().y)),
            (MM(t.GetEnd().x),   MM(t.GetEnd().y)))

def pt_seg(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

def seg_seg(a1, a2, b1, b2):
    # sufficient for the near-miss distances we care about; exact when the
    # segments do not cross, and a crossing shows up as a much larger violation
    # elsewhere anyway.
    return min(pt_seg(a1, b1, b2), pt_seg(a2, b1, b2),
               pt_seg(b1, a1, a2), pt_seg(b2, a1, a2))

def radius(t):
    if isinstance(t, pcbnew.PCB_VIA):
        # standing rule: PCB_VIA width calls ALWAYS take a layer argument
        return MM(t.GetWidth(t.TopLayer())) / 2
    return MM(t.GetWidth()) / 2

def layers(t):
    if isinstance(t, pcbnew.PCB_VIA):
        return set(range(t.TopLayer(), t.BottomLayer() + 1))
    return {t.GetLayer()}

def pos(t):
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        return ((MM(p.x), MM(p.y)), (MM(p.x), MM(p.y)))
    return endpoints(t)

def label(t, b):
    a, c = pos(t)
    if isinstance(t, pcbnew.PCB_VIA):
        return f"Via  [{t.GetNetname()}] @({a[0]:.3f},{a[1]:.3f})"
    return (f"Trk  [{t.GetNetname()}] ({a[0]:.3f},{a[1]:.3f})->({c[0]:.3f},{c[1]:.3f}) "
            f"{b.GetLayerName(t.GetLayer())}")

def area_tester(b, name):
    """Returns f(x_mm, y_mm) -> bool for the named rule area, or None.
    NEEDED FOR CORRECTNESS, not a refinement: this script compares raw geometry,
    but the .kicad_dru resolves LAST MATCHING RULE WINS, and `wlp_clearance`
    (0.075 mm, condition insideArea('U1_ESCAPE')) sits AFTER patient_clearance in
    the file.  So inside U1_ESCAPE the binding patient floor is 0.075, not 0.508.
    Without this exclusion the script reported 25 phantom PATIENT violations on a
    board where DRC correctly reports zero -- every one of them inside the WLP
    escape.  If you add a rule area to the .kicad_dru, add it here too."""
    for z in b.Zones():
        if z.GetIsRuleArea() and z.GetZoneName() == name:
            poly = z.Outline()
            def inside(x, y, poly=poly):
                return poly.Collide(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
            return inside
    return None

def main():
    path, cls, mn = sys.argv[1], sys.argv[2], float(sys.argv[3])
    other = None
    if "--vs-class" in sys.argv:
        other = sys.argv[sys.argv.index("--vs-class") + 1]
    same = "--same" in sys.argv
    excl = []
    for i, a in enumerate(sys.argv):
        if a == "--exclude-area":
            excl.append(sys.argv[i + 1])

    b = pcbnew.LoadBoard(path)
    testers = []
    for nm in excl:
        f = area_tester(b, nm)
        if f is None:
            sys.exit(f"ERROR: no rule area named {nm!r} on this board -- refusing to "
                     f"run, because silently ignoring an exclusion would over-report.")
        testers.append((nm, f))
    items = [t for t in b.GetTracks()]
    inA = [t for t in items if t.GetNet() and t.GetNet().GetNetClassName() == cls]

    def wanted(t):
        n = t.GetNet()
        if not n:
            return False
        c = n.GetNetClassName()
        if other:
            return c == other
        return (c == cls) if same else (c != cls)

    inB = [t for t in items if wanted(t)]
    hits = []
    for t1 in inA:
        for t2 in inB:
            if t1 is t2 or t1.GetNetname() == t2.GetNetname():
                continue
            if not (layers(t1) & layers(t2)):
                continue
            a1, a2 = pos(t1); b1, b2 = pos(t2)
            skip = False
            for nm, f in testers:
                if any(f(*p) for p in (a1, a2, b1, b2)):
                    skip = True
                    break
            if skip:
                continue
            g = seg_seg(a1, a2, b1, b2) - radius(t1) - radius(t2)
            if g < mn:
                pair = tuple(sorted([label(t1, b), label(t2, b)]))
                hits.append((round(g, 4), pair))
    uniq = sorted(set(hits))
    print(f"class {cls} vs {other or ('same class' if same else 'everything else')}, "
          f"floor {mn} mm")
    for g, (x, y) in uniq:
        print(f"  gap {g:7.4f}   {x}\n                 {y}")
    print(f"TRUE violation pairs: {len(uniq)}")

main()
