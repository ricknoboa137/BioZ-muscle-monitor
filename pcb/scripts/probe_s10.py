"""Read-only probe for session 10 hand routing: net classes of the 31 remaining
nets, the via geometries actually in use on the board, and the layer stack."""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from netclr import ClassRouter, T

NETS = """AFE_CS BIAS BTN_N BTN_PU DCC DECA_RF DECD FPWM_CTL GNDD ILIM LED_K
MEM_CS SPI_SCK SPI_SDO SWDCLK SWDIO SWO TS_NTC V1P8A V1P8D V2P5 VDD_nRF VIN_EXT
V_BAT V_SYS XC1 XC2 XL1 nCHG nPGOOD nRESET""".split()

r = ClassRouter()
b = r.board
print("== layers ==")
for lid in b.GetEnabledLayers().CuStack():
    print("  %3d  %s" % (lid, b.GetLayerName(lid)))

print("\n== net class / clearance / nominal width ==")
for n in NETS:
    c = r.cls_of(n)
    print("  %-9s %-12s clr=%.4f  nom_w=%.4f" % (n, c, r.clr[c], r.trk[c]))

print("\n== via geometries in use (dia/drill, count) ==")
cnt = collections.Counter()
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        cnt[(round(T(t.GetWidth(t.TopLayer())), 3), round(T(t.GetDrill()), 3),
             t.GetViaType())] += 1
for k, v in sorted(cnt.items()):
    print("   dia=%.3f drill=%.3f type=%s  x%d" % (k[0], k[1], k[2], v))

print("\n== design_settings rules ==")
for k, v in sorted(r.rules.items()):
    print("   %-32s %s" % (k, v))

print("\n== rule areas ==")
for z in b.Zones():
    if z.GetIsRuleArea():
        bb = z.GetBoundingBox()
        print("   %-20s (%.3f,%.3f)-(%.3f,%.3f)" % (
            z.GetZoneName(), T(bb.GetLeft()), T(bb.GetTop()),
            T(bb.GetRight()), T(bb.GetBottom())))
