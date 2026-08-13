"""Read-only: what net class KiCad ITSELF assigns each remaining net, versus
what netclr infers from the .kicad_pro patterns.  Triggered by finding existing,
DRC-clean 0.250 mm V_SYS tracks on U8 -- V_SYS is supposedly POWER_HIGH with a
0.508 mm floor from rule power_width.  One of the two views is wrong and the
board's own view is the one that binds."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from netclr import ClassRouter, T

NETS = """AFE_CS BIAS BTN_N BTN_PU DCC DECA_RF DECD FPWM_CTL GNDD ILIM LED_K
MEM_CS SPI_SCK SPI_SDO SWDCLK SWDIO SWO TS_NTC V1P8A V1P8D V2P5 VDD_nRF VIN_EXT
V_BAT V_SYS XC1 XC2 XL1 nCHG nPGOOD nRESET""".split()

R = ClassRouter()
b = R.board
print("%-10s %-14s %-14s %-9s %-9s" % ("net", "netclr says", "KiCad says",
                                       "kc_width", "kc_clear"))
for n in NETS:
    net = b.FindNet(n)
    if net is None:
        print("%-10s MISSING" % n)
        continue
    # NetClass() comes back as a bare SwigPyObject with no GetName(), the same
    # trap as GetRatsnestForNet() in entry 29.  GetNetClassName() works.
    print("%-10s %-14s %-14s" % (n, R.cls_of(n), net.GetNetClassName()))

print("\n== width census of existing tracks, by net class KiCad reports ==")
import collections
cnt = collections.Counter()
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        continue
    net = t.GetNet()
    cnt[(net.GetNetClassName(), round(T(t.GetWidth()), 4))] += 1
for k in sorted(cnt):
    print("   %-14s w=%.4f  x%d" % (k[0], k[1], cnt[k]))
