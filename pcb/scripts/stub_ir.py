# stub_ir.py <board>
# Measure the 7 pad-stub segments named in CHECKPOINT entry 52 and compute a real
# IR-drop / current-capacity figure for each, instead of asserting "negligible".
#
# Physics:
#   R = rho * L / (w * t)          rho(Cu) = 1.72e-8 ohm.m @20C, 2.09e-8 @85C
#   1 oz finished outer copper = 34.8 um  (brief section 2, L1/L4 "1 oz finished")
#   IPC-2221 external conductor, 10 C rise:
#   I = 0.048 * dT^0.44 * A_mil2^0.725
import sys, pcbnew

RHO20, RHO85 = 1.72e-8, 2.09e-8
T_OZ1 = 34.8e-6          # metres, 1 oz finished
MIL = 0.0254             # mm per mil

# net -> worst-case current in amps, from the schematic dossier section 7 power
# budget plus the peak (not average) transient for each rail.  Sources noted.
CURRENT = {
    # V2P5 is the buck output feeding everything downstream of U7.  Budget sum on
    # V2P5F is 2163 uA logging.  Peak transient dominated by the nRF54L15 radio
    # burst (~5 mA at 1.8 V through U14) plus CPU 2.6 mA -> ~8 mA reflected.
    # Take 20 mA as a deliberately pessimistic peak.
    "V2P5":       (0.020,  "buck output, 2.163 mA avg logging; 20 mA pessimistic peak"),
    # VDD_nRF is the nRF54L15 supply through FL1.  CPU 2.6 mA active, radio burst
    # ~5 mA.  Take 20 mA as pessimistic peak.
    "VDD_nRF":    (0.020,  "nRF54L15 VDD via FL1, 2.6 mA CPU / ~5 mA radio; 20 mA peak"),
    # AFE_PWR_EN is a logic enable into U10.EN -- a CMOS input, leakage only.
    "AFE_PWR_EN": (1e-6,   "logic enable into U10.EN, CMOS input leakage ~1 uA"),
}

SEGS = [  # (net, x1,y1,x2,y2) from entry 52's table
    ("VDD_nRF",    32.000, 18.250, 32.000, 18.550),
    ("VDD_nRF",    33.850, 13.600, 34.200, 13.600),
    ("VDD_nRF",    27.350, 16.800, 27.000, 16.800),
    ("VDD_nRF",    28.400, 11.750, 27.600, 11.400),
    ("AFE_PWR_EN", 31.200, 11.750, 31.310, 11.400),
    ("V2P5",       41.750, 18.762, 41.750, 16.350),
]

b = pcbnew.LoadBoard(sys.argv[1])
T = pcbnew.ToMM

def near(p, q):
    return abs(p[0]-q[0]) < 0.002 and abs(p[1]-q[1]) < 0.002

found = []
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        continue
    n = t.GetNet()
    if not n:
        continue
    nm = n.GetNetname()
    s, e = t.GetStart(), t.GetEnd()
    a, c = (T(s.x), T(s.y)), (T(e.x), T(e.y))
    for net, x1, y1, x2, y2 in SEGS:
        if nm != net:
            continue
        if (near(a, (x1, y1)) and near(c, (x2, y2))) or (near(a, (x2, y2)) and near(c, (x1, y1))):
            found.append((nm, a, c, T(t.GetWidth()), b.GetLayerName(t.GetLayer())))

print("matched %d of %d listed segments\n" % (len(found), len(SEGS)))
hdr = "%-11s %-6s %-30s %6s %7s %9s %9s %9s %8s"
print(hdr % ("net", "layer", "segment (mm)", "w(mm)", "len(mm)", "R@20C", "R@85C",
             "IRdrop@85", "Imax10C"))
worst = 0.0
for nm, a, c, w, lay in found:
    L = ((a[0]-c[0])**2 + (a[1]-c[1])**2) ** 0.5
    area = (w*1e-3) * T_OZ1                      # m^2
    r20 = RHO20 * (L*1e-3) / area
    r85 = RHO85 * (L*1e-3) / area
    I, _ = CURRENT[nm]
    v = r85 * I
    worst = max(worst, v)
    # IPC-2221 external, 10 C rise
    a_mil2 = (w/MIL) * (T_OZ1*1e3/MIL)
    imax = 0.048 * (10 ** 0.44) * (a_mil2 ** 0.725)
    print(hdr % (nm, lay, "(%.3f,%.3f)-(%.3f,%.3f)" % (a[0], a[1], c[0], c[1]),
                 "%.4f" % w, "%.3f" % L, "%.3f mohm" % (r20*1e3),
                 "%.3f mohm" % (r85*1e3), "%.1f uV" % (v*1e6), "%.2f A" % imax))

print("\nworst-case IR drop across any one stub: %.1f uV" % (worst*1e6))
print("current assumptions used:")
for k, (i, why) in CURRENT.items():
    print("  %-11s %8.6f A   %s" % (k, i, why))
