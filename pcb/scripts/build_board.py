"""Build the BioZ Muscle Monitor board: outline, footprints, nets, placement,
pours, keepouts.  Run with KiCad's bundled python:

  & "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" build_board.py

Coordinates: board occupies (0,0)..(50,44) mm, KiCad Y increases downward.
The GNDA/GNDD split is the vertical line X = SPLIT_X; analog is X < SPLIT_X.

Placement happens in three passes:
  1. anchors      - critical parts placed at explicit coordinates and PINNED
  2. attachments  - decoupling placed automatically against a named host pad,
                    so brief section 5 adjacency is satisfied by construction
  3. relaxation   - remaining passives pushed apart until courtyards clear
"""
import os, math, itertools
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCBDIR = os.path.dirname(HERE)
BOARD_FILE = os.path.join(PCBDIR, "BioZ-Muscle-Monitor.kicad_pcb")
KIFP = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
LOCALFP = os.path.join(PCBDIR, "BioZ-Muscle-Monitor.pretty")

W, H = 62.0, 44.0        # grown from 50 mm in X to fit the WE-SHC frame
SPLIT_X = 20.0
SPLIT_GAP = 0.8
ANT_KO = (25.0, 0.0, 62.0, 6.82)   # 6.82 mm from the Wurth 74889302450 eval board
CELL = (0.5, 14.0, 48.5, 44.0)     # LP103048JU, stacked under the board.
                                   # X 48.5..62 is the cell-free strip, which
                                   # is where U8 lives.
# WE-SHC 26.5 mm land, stacked exactly under the antenna keepout and above the
# connector row.  Y is the binding dimension: 6.82 + 26.5 + 10.28 = 43.60 of
# 44.00 mm, so this is the only Y position the frame can occupy.
FRAME = (35.2, 7.2, 61.7, 33.7)

mm = pcbnew.FromMM
def V(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))

GA, GD = "GNDA", "GNDD"
C = []
ATTACH = []      # (ref, host, host_pad, gap_mm, direction_deg or None)

def add(ref, val, lib, fp, x, y, rot=0, side="T", nets=None, pin=True):
    C.append(dict(ref=ref, val=val, lib=lib, fp=fp, x=x, y=y, rot=rot,
                  side=side, nets=nets or {}, pin=pin,
                  analog=(x < SPLIT_X)))

def attach(ref, host, pad, gap=0.45, rot=None, dirn=None):
    """Place ref against a named host pad.  Attached parts are PINNED: their
    whole reason for existing is that they sit on that pad."""
    ATTACH.append((ref, host, pad, gap, rot, dirn))
    for c in C:
        if c["ref"] == ref:
            c["pin"] = True

R0402 = ("Resistor_SMD", "R_0402_1005Metric")
R0603 = ("Resistor_SMD", "R_0603_1608Metric")
C0201 = ("Capacitor_SMD", "C_0201_0603Metric")
C0402 = ("Capacitor_SMD", "C_0402_1005Metric")
C0603 = ("Capacitor_SMD", "C_0603_1608Metric")
C0805 = ("Capacitor_SMD", "C_0805_2012Metric")
C1206 = ("Capacitor_SMD", "C_1206_3216Metric")
L0201 = ("Inductor_SMD", "L_0201_0603Metric")
L0402 = ("Inductor_SMD", "L_0402_1005Metric")
L0603 = ("Inductor_SMD", "L_0603_1608Metric")
LOCAL = "BioZ-Muscle-Monitor"

# ===================== ANALOG ZONE (X < 21), GNDA =========================
# U1 straddles the split.  Bump rows A..E run along +X, so rows A,B,C (every
# analog bump) sit at X <= 20.8 and rows D,E (DVDD, DGND, SPI) at X >= 21.2.
# The split at X = 21.0 passes straight through the package -- no fingers -- and
# R1 bridges it on the bottom layer directly underneath.
add("U1", "MAX30009ENA+", LOCAL, "MAX30009ENA_WLP25_2.03x2.03_P0.4mm",
    19.8, 26.0, 0, "T", {
    "A1": "EL_DRVP", "A2": "", "A3": "EL_SENP", "A4": "CAL_F", "A5": "CAL_F",
    "B1": "EL_DRVN", "B2": "", "B3": "EL_SENN", "B4": "CAL_S", "B5": "CAL_S",
    "C1": "V1P8A",   "C2": "VREF", "C3": GA,    "C4": "DRVSJ", "C5": "",
    "D1": "V1P8A",   "D2": "AFE_CS", "D3": "",  "D4": GD,      "D5": "DRVXC",
    "E1": GD, "E2": "SPI_SDI", "E3": "SPI_SDO", "E4": "SPI_SCK", "E5": "AFE_INT"})
# --- BOTTOM SIDE, directly under the WLP escape --------------------------
# A 0402 cannot get within 1.5 mm of a bump on the far side of a 2.03 mm
# package from the top layer.  The via-in-pad escape that the WLP already
# forces makes the bottom side the shorter path: these four parts sit under
# U1, reached by microvia, and the resulting loop is well under what the brief
# asked for.  R1 straddles the split; it is the ONLY GNDA-GNDD connection.
add("R1", "0R STITCH", *R0603, 20.0, 26.0, 0, "B", {"1": GA, "2": GD})
add("C4", "100n AVDD", *C0402, 18.6, 24.6, 0, "B", {"1": "V1P8A", "2": GA})
add("C3", "100n DVDD", *C0402, 21.0, 24.6, 0, "B", {"1": "V1P8A", "2": GD})
# C1 sits on the TOP layer beside U1 now: VREF escapes on the L2 layer and
# comes back up to F.Cu, so there is no reason to put its capacitor underneath.
add("C1", "1u X5R VREF", *C0603, 18.4, 27.6, 0, "B", {"1": "VREF", "2": GA})
# C7 bridges bumps D5 (DRVXC) and C4 (DRVSJ), which sit on opposite sides of
# the row C / row D line.  Both nets are analog, so this is the SECOND
# documented crossing of the ground split -- see routing-order.md.
add("C7", "47n", *C0805, 21.0, 29.9, 0, "B", {"1": "DRVXC", "2": "DRVSJ"})

add("R7", "680R 0.1%", *R0603, 16.0, 26.0, 90, "T", {"1": "CAL_F", "2": "CAL_S"})
add("R5", "40k2", *R0603, 15.0, 22.0, 0, "T", {"2": "EL_SENP", "1": "PT_E3"})
add("R6", "40k2", *R0603, 15.0, 30.0, 0, "T", {"2": "EL_SENN", "1": "PT_E2"})
add("C5", "47n", *C0805, 15.0, 19.0, 0, "T", {"2": "EL_DRVP", "1": "PT_E1"})
add("C6", "47n", *C0805, 15.0, 33.0, 0, "T", {"2": "EL_DRVN", "1": "PT_E4"})

add("C2", "10u", *C0402, 16.4, 23.0, 0, "T", {"1": "V1P8A", "2": GA}, pin=False)
add("C37", "1u", *C0603, 15.0, 35.0, 0, "T", {"1": "V1P8A", "2": GA}, pin=False)
add("C42", "10u", *C0402, 22.6, 22.6, 0, "T", {"1": "V1P8A", "2": GD}, pin=False)
add("U10", "ADPL40502-1.8 A", "Package_DFN_QFN",
    "DFN-6-1EP_2x2mm_P0.65mm_EP1x1.6mm", 16.5, 39.0, 0, "T",
    {"1": "V1P8A", "2": "", "3": GA, "4": "AFE_PWR_EN", "5": "", "6": "V2P5F",
     "7": GA})
add("C28", "1u", *C0603, 12.5, 39.0, 0, "T", {"1": "V2P5F", "2": GA}, pin=False)
# Electrode harness, left (44 mm) edge -- opposite short edge from P1.
add("J1", "S4B-PH-K-S", "Connector_JST",
    "JST_PH_S4B-PH-K_1x04_P2.00mm_Horizontal", 4.6, 23.0, 90, "T",
    {"1": "PT_E4", "2": "PT_E2", "3": "PT_E3", "4": "PT_E1"})

# ================ DIGITAL / POWER ZONE (X > 21), GNDD =====================
add("AE1", "WE-MCA 74889302450", LOCAL, "Wurth_WE-MCA_74889302450",
    32.1, 2.4, 0, "T", {"1": "RF_ANT", "2": ""})
FX = 30.4                                  # AE1 feed-pad X = U5 pin 31 X                                  # AE1 feed-pad X: the RF centreline
add("L6", "3n5", *L0201, FX, 7.4, 90, "T", {"1": "RF_B", "2": "RF_ANT"})
add("L5", "3n5", *L0201, FX, 9.0, 90, "T", {"1": "RF_A", "2": "RF_B"})
add("L4", "2n7", *L0201, FX, 10.6, 90, "T", {"1": "ANT", "2": "RF_A"})
add("C23", "3p9", *C0201, FX - 1.7, 7.08, 180, "T", {"1": "RF_ANT", "2": GD})
add("C21", "0p3", *C0201, FX + 1.7, 7.72, 0, "T", {"1": "RF_B", "2": GD})
add("C20", "2p0", *C0201, FX + 1.7, 9.32, 0, "T", {"1": "RF_A", "2": "GND_C20"})
add("C19", "1p5", *C0201, FX - 1.7, 10.92, 180, "T", {"1": "ANT", "2": "VSS_PA"})
# VSS_PA reaches ground ONLY through U5 pin 32 -> die pad (brief 4.4).  Net tie
# sits on the die pad so the deliberate single-point return is legal to DRC.
add("NT1", "VSS_PA-GNDD", LOCAL, "NetTie-2_0.25mm_P0.65mm",
    30.0, 12.375, 0, "T", {"1": "VSS_PA", "2": GD})

add("U5", "nRF54L15-QFAA", "Package_DFN_QFN",
    "QFN-48-1EP_6x6mm_P0.4mm_EP4.6x4.6mm", 30.6, 15.0, 90, "T", {
    "1": "XL1", "2": "XL2", "5": "VBAT_SENSE", "6": "nPGOOD", "7": "MEM_WP",
    "8": "nCHG", "10": "VDD_nRF", "12": "SPI_SCK", "13": "SPI_SDO",
    "14": "MEM_CS", "15": "SPI_SDI", "16": "AFE_CS", "18": "SWO",
    "22": "VDD_nRF", "23": "LED_K", "24": "BTN_N", "25": "SWDIO",
    "26": "SWDCLK", "27": "AFE_INT", "28": "FPWM_CTL", "29": "AFE_PWR_EN",
    "30": "nRESET", "31": "ANT", "32": "VSS_PA", "33": "DECA_RF",
    "34": "XC1", "35": "XC2", "36": "VDD_nRF", "43": "DECA_RF", "44": GD,
    "45": "DECD", "46": "DCC", "47": "VDD_nRF", "48": "VDD_nRF", "49": GD})

add("Y1", "32.768kHz ABS06", "Crystal", "Crystal_SMD_3215-2Pin_3.2x1.5mm",
    32.2, 22.2, 0, "T", {"1": "XL1", "2": "XL2"})
add("Y2", "32MHz ABM10", "Crystal", "Crystal_SMD_2520-4Pin_2.5x2.0mm",
    25.6, 8.4, 0, "T", {"1": "XC1", "2": GD, "3": "XC2", "4": GD})

# U5 decoupling: one 100 nF per VDD pin, placed automatically against the pin.
for ref, pad, dn in (("C14", "10", "S"), ("C15", "22", "E"), ("C16", "36", "W"),
                     ("C17", "47", "W"), ("C24", "48", "W")):
    add(ref, "100n", *C0201, 0, 0, 0, "T", {"1": "VDD_nRF", "2": GD}, pin=False)
    attach(ref, "U5", pad, 1.65 if ref == "C24" else 0.10, dirn=dn)
add("C22", "10n DECA/DECRF", *C0201, 0, 0, 0, "T", {"1": "DECA_RF", "2": GD},
    pin=False); attach("C22", "U5", "43", 0.10, dirn="W")
add("C18", "10n DECD", *C0201, 0, 0, 0, "T", {"1": "DECD", "2": GD},
    pin=False); attach("C18", "U5", "45", 0.10, dirn="W")
add("C11", "2u2", *C0201, 0, 0, 0, "T", {"1": "DCC", "2": GD}, pin=False)
attach("C11", "U5", "46", 0.10, dirn="W")
add("C12", "2u2", *C0201, 0, 0, 0, "T", {"1": "DCC", "2": GD}, pin=False)
attach("C12", "U5", "46", 1.20, dirn="W")
add("C36", "100n", *C0402, 0, 0, 0, "T", {"1": "VBAT_SENSE", "2": GD},
    pin=False); # rot 270 so C36 pad 1 (VBAT_SENSE) faces the pin and pad 2 (GNDD) points
# away: otherwise the ground pad sits between the pin and the signal pad.
attach("C36", "U5", "5", 0.10, rot=270, dirn="S")     # brief 4.6: at the MCU pin
add("L3", "4u7", *L0603, 30.0, 22.4, 0, "T", {"1": "DCC", "2": "VDD_nRF"})
add("FL1", "120R", *L0201, 27.6, 22.4, 0, "T", {"1": "V1P8D", "2": "VDD_nRF"})
add("C13", "10u", *C0402, 32.6, 22.4, 0, "T", {"1": "VDD_nRF", "2": GD})
# The divider sits beside C36, not across the board: VBAT_SENSE is a 91 kOhm
# source impedance node and every millimetre of track on it is loss.
add("R2", "1M", *R0402, 25.6, 20.4, 0, "T", {"2": "V_SYS", "1": "VBAT_SENSE"},
    pin=False)
add("R3", "100k", *R0402, 25.6, 21.6, 0, "T", {"1": "VBAT_SENSE", "2": GD},
    pin=False)

add("IC1", "CY15V108QI", LOCAL, "Infineon_GQFN-8_3.23x3.28mm",
    22.6, 12.0, 0, "T", {"1": "MEM_CS", "2": "SPI_SDI", "3": "MEM_WP", "4": GD,
                         "5": "SPI_SDO", "6": "SPI_SCK", "7": "", "8": "V1P8D"})
add("C43", "100n", *C0402, 0, 0, 0, "T", {"1": "V1P8D", "2": GD}, pin=False)
attach("C43", "IC1", "8", 0.10)                    # brief 5 priority 8

add("U14", "ADPL40502-1.8 D", "Package_DFN_QFN",
    "DFN-6-1EP_2x2mm_P0.65mm_EP1x1.6mm", 25.8, 26.8, 0, "T",
    {"1": "V1P8D", "2": "", "3": GD, "4": "V2P5F", "5": "", "6": "V2P5F",
     "7": GD})
for ref, val, pk, net, sx, sy in (("C38", "1u", C0603, "V2P5F", 22.4, 22.6),
                                  ("C39", "1u", C0603, "V1P8D", 25.6, 25.5),
                                  ("C40", "10u", C0402, "V1P8D", 25.6, 23.9),
                                  ("C44", "1u", C0603, "V1P8D", 22.2, 27.6),
                                  ("C45", "100n", C0402, "V1P8D", 25.4, 27.6)):
    add(ref, val, *pk, sx, sy, 0, "T", {"1": net, "2": GD})

# --------------- switching converter U7 (brief 4.3, minimum loop) ----------
# Loop: C29 -> IN(6) -> LX1(8) -> L8 -> LX2(10) -> OUT(11) -> C9 -> PGND(9).
# KiCad's FC2QFN-14 land merges datasheet pads 6+7 into one "6" and 11+12 into
# one "11" -- which is what the package physically is (V1, closed).
# U7 is 15.8 mm from U1 (brief 5 requires >= 15 mm) and the whole loop sits
# inside a 6 x 5 mm block with its L2 return directly beneath.
add("U7", "MAX77827BEFD+T", "Package_DFN_QFN",
    "Maxim_FC2QFN-14_2.5x2.5mm_P0.5mm", 42.0, 20.0, 0, "T",
    {"1": "SEL", "2": "POK", "3": "SW_EN", "4": GD, "5": "BIAS", "6": "V_SYS",
     "8": "LX", "9": GD, "10": "LX", "11": "V2P5", "13": "V2P5",
     "14": "FPWM_CTL"})
add("L8", "1u0", "Inductor_SMD", "L_0805_2012Metric", 44.9, 20.0, 90, "T",
    {"1": "LX", "2": "LX"})
add("C29", "10u", *C0805, 42.0, 23.2, 0, "T", {"1": "V_SYS", "2": GD})
add("C9", "22u", *C0603, 42.2, 17.2, 0, "T", {"1": "V2P5", "2": GD})
add("C26", "1u", *C0603, 39.0, 23.2, 0, "T", {"1": "V_SYS", "2": GD}, pin=False)
add("C35", "100n", *C0402, 39.4, 17.2, 0, "T", {"1": "V2P5", "2": GD})
add("C34", "1u BIAS", *C0603, 38.4, 20.0, 0, "T", {"1": "BIAS", "2": GD},
    pin=False)
add("R15", "634k 1%", *R0402, 38.4, 26.4, 0, "T", {"1": "SEL", "2": GD},
    pin=False)
add("R19", "10k", *R0402, 40.0, 26.4, 0, "T", {"1": "FPWM_CTL", "2": GD},
    pin=False)
add("R22", "100k", *R0402, 41.6, 26.4, 0, "T", {"1": "POK", "2": "V2P5"},
    pin=False)
add("R16", "0R1", *R0603, 31.0, 32.6, 0, "T", {"1": "V2P5", "2": "V2P5FA"},
    pin=False)
add("L7", "32n", *L0402, 28.4, 32.6, 0, "T", {"1": "V2P5FA", "2": "V2P5F"},
    pin=False)
add("C32", "3u3", *C1206, 23.4, 30.2, 0, "T", {"1": "V2P5F", "2": GD})
add("C33", "10u", *C0805, 27.4, 30.2, 0, "T", {"1": "V2P5F", "2": GD})

# --------- charger U8: top-right strip, deliberately clear of the cell -----
add("U8", "BQ24073RGT", "Package_DFN_QFN",
    "QFN-16-1EP_3x3mm_P0.5mm_EP1.7x1.7mm", 54.0, 15.0, 0, "T", {
    "1": "TS_NTC", "2": "V_BAT", "3": "V_BAT", "4": GD, "5": "V_SYS",
    "6": "V_SYS", "7": "nPGOOD", "8": GD, "9": "nCHG", "10": "V_SYS",
    "11": "V_SYS", "12": "ILIM", "13": "VIN_EXT", "14": GD, "15": GD,
    "16": "ISET", "17": GD})
add("C30", "4u7", *C0805, 0, 0, 0, "T", {"1": "V_BAT", "2": GD}, pin=False)
attach("C30", "U8", "2", 0.10, dirn="W")                      # brief 5 priority 9
add("C31", "4u7", *C0805, 0, 0, 0, "T", {"1": "V_SYS", "2": GD}, pin=False)
attach("C31", "U8", "10", 0.10, dirn="E")
add("C27", "1u", *C0603, 0, 0, 0, "T", {"1": "VIN_EXT", "2": GD}, pin=False)
attach("C27", "U8", "13", 1.7, dirn="N")
add("R13", "2k55 ILIM", *R0402, 50.4, 19.0, 0, "T", {"1": "ILIM", "2": GD},
    pin=False)
add("R14", "2k21 ISET", *R0402, 50.4, 11.0, 0, "T", {"1": "ISET", "2": GD},
    pin=False)
add("R17", "1k5", *R0402, 58.0, 11.0, 0, "T", {"1": "nPGOOD", "2": "V1P8D"},
    pin=False)
add("R18", "1k5", *R0402, 58.0, 12.4, 0, "T", {"1": "nCHG", "2": "V1P8D"},
    pin=False)
# Charge connector, right (44 mm) edge -- opposite short edge from J1.
add("P1", "S3B-PH-SM4-TB", "Connector_JST",
    "JST_PH_S3B-PH-SM4-TB_1x03-1MP_P2.00mm_Horizontal", 26.0, 38.84, 0, "T",
    {"1": "VIN_EXT", "2": GD, "3": GD})

# ------------------------- button, LED, debug -----------------------------
add("U2", "SN74LVC1G14", "Package_TO_SOT_SMD", "SOT-353_SC-70-5",
    22.4, 18.5, 0, "T", {"1": "", "2": "BTN_RC", "3": GD, "4": "BTN_N",
                          "5": "V1P8D"})
add("C25", "10n", *C0603, 22.6, 15.0, 0, "T", {"1": "BTN_RC", "2": GD},
    pin=False)
add("R11", "220k", *R0402, 24.4, 15.4, 0, "T", {"1": "BTN_RC", "2": "BTN_PU"},
    pin=False)
add("R10", "2k2", *R0402, 24.4, 16.6, 0, "T", {"1": "BTN_PU", "2": "V1P8D"},
    pin=False)
add("D1", "BAT54-02V", "Diode_SMD", "D_SOD-523", 24.4, 18.4, 0, "T",
    {"1": "BTN_RC", "2": "BTN_PU"}, pin=False)
add("R12", "1k6", *R0402, 22.6, 18.8, 0, "T", {"1": "BTN_RC", "2": "BTN_SW"},
    pin=False)
add("R8", "1k", *R0402, 30.4, 36.0, 0, "T", {"1": "nRESET", "2": "V1P8D"},
    pin=False)
add("LED1", "APT1608SURCK", "LED_SMD", "LED_0603_1608Metric", 21.5, 8.4, 0, "T",
    {"1": "V2P5F", "2": "LED_K_R"})
add("R4", "200R", *R0402, 21.5, 10.4, 0, "T", {"1": "LED_K_R", "2": "LED_K"},
    pin=False)
add("J2", "62201021121 SWD", "Connector_PinHeader_1.27mm",
    "PinHeader_2x05_P1.27mm_Vertical", 31.6, 26.4, 0, "T",
    {"1": "V1P8D", "2": "SWDIO", "3": GD, "4": "SWDCLK", "5": GD,
     "6": "SWO", "7": "", "8": "", "9": GD, "10": "nRESET"})

# ---------------------------- edge connectors -----------------------------
add("J7", "S2B-PH-SM4-TB BATT", "Connector_JST",
    "JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal", 41.5, 38.84, 0, "T",
    {"1": "V_BAT", "2": GD})
add("J8", "S2B-PH-SM4-TB SW", "Connector_JST",
    "JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal", 51.5, 38.84, 0, "T",
    {"1": "V_SYS", "2": "SW_EN"})
# Not board mounted: SW1 is panel mounted in the lid, U9 is bonded to the cell.
add("SW1", "52-03-80 (panel)", LOCAL, "WirePads_1x2_P2.54mm",
    34.2, 36.5, 0, "T", {"1": "BTN_SW", "2": GD})
add("U9", "103AT-2 (on cell)", LOCAL, "WirePads_1x2_P2.54mm",
    34.2, 40.5, 0, "T", {"1": "TS_NTC", "2": GD})

# --------------------------- shield frame ---------------------------------
# Wurth WE-SHC 36103255, over the whole power section (U7 and U8).  Its solder
# ring is a continuous GNDD land; no track may cross under it on the top layer.
add("H1", "WE-SHC 36103255", LOCAL, "Wurth_WE-SHC_36103255_26x26mm",
    (FRAME[0] + FRAME[2]) / 2.0, (FRAME[1] + FRAME[3]) / 2.0, 0, "T",
    {"1": GD})

# ----------- inverted-U mounting edge pads (the two 44 mm edges) ----------
add("MP1", "edge pads L", LOCAL, "EdgePads_1x6_P1.6mm", 1.1, 8.0, 0, "T",
    {str(i): GA for i in range(1, 7)})
add("MP2", "edge pads R", LOCAL, "EdgePads_1x6_P1.6mm", 60.8, 36.0, 0, "T",
    {str(i): GD for i in range(1, 7)})

# Regions no relaxed part may drift into (connector bodies, antenna, U1 escape)
FORBIDDEN = [(24.0, 0.0, 50.0, 7.2),        # antenna keepout + margin
             (17.6, 23.0, 22.6, 29.5),      # U1 escape
             (39.2, 15.6, 50.0, 27.4),      # P1 courtyard
             (21.5, 33.2, 31.3, 44.0),      # J7 courtyard
             (31.5, 33.2, 41.3, 44.0),      # J8 courtyard
             (42.8, 29.6, 47.7, 37.4),      # J2 courtyard
             (42.4, 37.8, 47.6, 44.0),      # SW1 / U9 wire pads
             (28.9, 6.4, 33.7, 12.0),       # RF ladder - nothing else here
             (0.0, 15.5, 9.5, 32.0)]        # J1 courtyard


def main():
    board = pcbnew.BOARD()
    # 6 layers, HDI 1+4+1.  L2 is a sparse ESCAPE layer so a microvia in the
    # WLP pad lands on a routing layer; L3 is the solid ground reference and is
    # therefore never perforated by the escape.  See the dossier, section 2.
    board.SetCopperLayerCount(6)
    board.SetLayerName(pcbnew.In1_Cu, "Escape")
    board.SetLayerName(pcbnew.In2_Cu, "GND")
    board.SetLayerName(pcbnew.In3_Cu, "Power")
    board.SetLayerName(pcbnew.In4_Cu, "Signal")

    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(1.0))
    ds.m_MinThroughDrill = mm(0.1)
    ds.m_ViasMinSize = mm(0.18)
    ds.m_MicroViasAllowed = True
    ds.m_MinClearance = mm(0.075)
    ds.m_TrackMinWidth = mm(0.075)
    ds.m_CopperEdgeClearance = mm(0.25)

    netnames = {n for c in C for n in c["nets"].values() if n}
    netnames.add("GND_C20")
    for n in sorted(netnames):
        board.Add(pcbnew.NETINFO_ITEM(board, n))

    r = 2.0
    def seg(x1, y1, x2, y2):
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(x1, y1)); s.SetEnd(V(x2, y2))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); board.Add(s)
    def arc(cx, cy, sa, ea):
        a = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
        a.SetCenter(V(cx, cy))
        a.SetStart(V(cx + r*math.cos(math.radians(sa)), cy + r*math.sin(math.radians(sa))))
        a.SetEnd(V(cx + r*math.cos(math.radians(ea)), cy + r*math.sin(math.radians(ea))))
        a.SetLayer(pcbnew.Edge_Cuts); a.SetWidth(mm(0.1)); board.Add(a)
    seg(r, 0, W-r, 0);   arc(W-r, r, -90, 0)
    seg(W, r, W, H-r);   arc(W-r, H-r, 0, 90)
    seg(W-r, H, r, H);   arc(r, H-r, 90, 180)
    seg(0, H-r, 0, r);   arc(r, r, 180, 270)

    fps = {}
    for c in C:
        libdir = LOCALFP if c["lib"] == LOCAL else os.path.join(KIFP, c["lib"] + ".pretty")
        fp = pcbnew.FootprintLoad(libdir, c["fp"])
        if fp is None:
            print("!! MISSING FOOTPRINT", c["ref"], c["fp"]); continue
        fp.SetReference(c["ref"]); fp.SetValue(c["val"])
        board.Add(fp)
        fp.SetPosition(V(c["x"], c["y"]))
        if c["side"] == "B":
            fp.Flip(V(c["x"], c["y"]), False)
        fp.SetOrientationDegrees(c["rot"])
        ref = fp.Reference()
        ref.SetTextSize(pcbnew.VECTOR2I(mm(0.6), mm(0.6)))
        ref.SetTextThickness(mm(0.1))
        fp.Value().SetVisible(False)
        # Footprint-level clearance override.  The net-class clearances in
        # brief section 3 are ROUTING clearances: 8-20 mil, which is wider than
        # the pad gaps of the fine-pitch parts the brief itself specifies
        # (0.15 mm between WLP bumps, 0.18 mm inside an 0201, 0.1796 mm on the
        # FC2QFN, 0.20 mm on the QFN48).  Applying a routing clearance to
        # package geometry is a category error.  0.10 mm sits above the
        # 0.075 mm fabricator floor and below every one of those gaps.
        # The safety-critical clearances - PATIENT 20 mil, PATIENT-to-LX
        # 40 mil, RF 3x width - are custom RULES in the .kicad_dru, and a rule
        # outranks a local override, so they are unaffected.
        fp.SetLocalClearance(mm(0.10))
        want = dict(c["nets"])
        seen = set()
        for pad in fp.Pads():
            nm = pad.GetNumber()
            if nm in want:
                if want[nm]:
                    net = board.FindNet(want[nm])
                    if net: pad.SetNet(net)
                seen.add(nm)     # do NOT pop: the shield ring is four pads
        for nm in seen:          # sharing one pad number
            want.pop(nm, None)
        if want:
            print(f"   {c['ref']}: pads not on footprint: {sorted(want)}")
        fps[c["ref"]] = fp

    # ---- pass 2: attach decoupling to its own host pad, radially outward
    for ref, host, padnum, gap, rot, dirn in ATTACH:
        fp, hf = fps.get(ref), fps.get(host)
        if not fp or not hf: continue
        pad = next((p for p in hf.Pads() if p.GetNumber() == padnum), None)
        if pad is None:
            print("!! attach: no pad", host, padnum); continue
        px = pcbnew.ToMM(pad.GetPosition().x); py = pcbnew.ToMM(pad.GetPosition().y)
        hx = pcbnew.ToMM(hf.GetPosition().x); hy = pcbnew.ToMM(hf.GetPosition().y)
        # outward direction = the dominant axis from host centre to the pad, so
        # the part lands square to the package edge rather than on a diagonal
        dx, dy = px - hx, py - hy
        if dirn:
            nx, ny = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}[dirn]
        elif abs(dx) >= abs(dy):
            nx, ny = (1.0 if dx > 0 else -1.0), 0.0
        else:
            nx, ny = 0.0, (1.0 if dy > 0 else -1.0)
        # long axis perpendicular to the package edge keeps the pitch tight
        orient = 0 if ny == 0 else 90
        fp.SetOrientationDegrees(rot if rot is not None else orient)
        hb = hf.GetCourtyard(pcbnew.F_CrtYd).BBox()
        hx1, hx2 = pcbnew.ToMM(hb.GetLeft()), pcbnew.ToMM(hb.GetRight())
        hy1, hy2 = pcbnew.ToMM(hb.GetTop()), pcbnew.ToMM(hb.GetBottom())
        for step in [i * 0.05 for i in range(1, 200)]:
            fp.SetPosition(V(px + nx * step, py + ny * step))
            b = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
            x1, x2 = pcbnew.ToMM(b.GetLeft()), pcbnew.ToMM(b.GetRight())
            y1, y2 = pcbnew.ToMM(b.GetTop()), pcbnew.ToMM(b.GetBottom())
            if not (x2 > hx1 - gap and x1 < hx2 + gap and
                    y2 > hy1 - gap and y1 < hy2 + gap):
                break

    # ---- pass 3: relaxation of the non-pinned parts
    pinned = {c["ref"] for c in C if c["pin"]}
    zone_of = {c["ref"]: c["analog"] for c in C}
    def bbox(fp):
        bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
        if bb.GetWidth() == 0: bb = fp.GetCourtyard(pcbnew.B_CrtYd).BBox()
        return (pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetRight()),
                pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetBottom()))
    def move(fp, dx, dy):
        p = fp.GetPosition()
        fp.SetPosition(pcbnew.VECTOR2I(p.x + mm(dx), p.y + mm(dy)))

    order = [c["ref"] for c in C]
    for it in range(1500):
        moved = 0
        for a, b in itertools.combinations(order, 2):
            fa, fb = fps.get(a), fps.get(b)
            if not fa or not fb: continue
            if a in pinned and b in pinned: continue
            # a top/bottom pair never collides
            if (fa.IsFlipped() != fb.IsFlipped()): continue
            ax1, ax2, ay1, ay2 = bbox(fa); bx1, bx2, by1, by2 = bbox(fb)
            ox = min(ax2, bx2) - max(ax1, bx1); oy = min(ay2, by2) - max(ay1, by1)
            if ox <= 0.02 or oy <= 0.02: continue
            acx, acy = (ax1+ax2)/2, (ay1+ay2)/2
            bcx, bcy = (bx1+bx2)/2, (by1+by2)/2
            if ox < oy:
                s = 0.5*(ox+0.06) * (1 if acx < bcx else -1)
                da, db = (-s, 0), (s, 0)
            else:
                s = 0.5*(oy+0.06) * (1 if acy < bcy else -1)
                da, db = (0, -s), (0, s)
            if a in pinned:
                move(fb, db[0]*2, db[1]*2)
            elif b in pinned:
                move(fa, da[0]*2, da[1]*2)
            else:
                move(fa, *da); move(fb, *db)
            moved += 1
        # keep relaxed parts on the board, out of forbidden regions and off
        # the wrong side of the ground split
        for ref in order:
            if ref in pinned: continue
            fp = fps.get(ref)
            if not fp: continue
            x1, x2, y1, y2 = bbox(fp)
            dx = dy = 0.0
            analog = zone_of[ref]
            lo = 0.6 if analog else SPLIT_X + SPLIT_GAP/2 + 0.2
            hi = SPLIT_X - SPLIT_GAP/2 - 0.2 if analog else W - 0.6
            if x1 < lo: dx = lo - x1
            if x2 > hi: dx = hi - x2
            if y1 < 0.6: dy = 0.6 - y1
            if y2 > H - 0.6: dy = H - 0.6 - y2
            for fx1, fy1, fx2, fy2 in FORBIDDEN:
                if x2 > fx1 and x1 < fx2 and y2 > fy1 and y1 < fy2:
                    push = [(fx1 - x2, 0), (fx2 - x1, 0), (0, fy1 - y2), (0, fy2 - y1)]
                    px, py = min(push, key=lambda p: abs(p[0]) + abs(p[1]))
                    dx += px; dy += py
            if dx or dy:
                move(fp, dx, dy); moved += 1
        if not moved:
            print(f"   relaxation converged after {it} iterations"); break
    else:
        print("   relaxation did NOT fully converge")

    # ---- rule areas
    def rule_area(name, x1, y1, x2, y2, layers, no_pour=True, no_track=True,
                  no_via=True, no_pad=False, no_fp=False):
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True); z.SetZoneName(name)
        z.SetDoNotAllowZoneFills(no_pour); z.SetDoNotAllowTracks(no_track)
        z.SetDoNotAllowVias(no_via); z.SetDoNotAllowPads(no_pad)
        z.SetDoNotAllowFootprints(no_fp)
        ls = pcbnew.LSET()
        for l in layers: ls.AddLayer(l)
        z.SetLayerSet(ls)
        o = z.Outline(); o.NewOutline()
        for (px, py) in [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]:
            o.Append(mm(px), mm(py))
        z.SetAssignedPriority(100); board.Add(z)

    ALL_CU = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu,
              pcbnew.In4_Cu, pcbnew.B_Cu]
    rule_area("ANTENNA_KEEPOUT", *ANT_KO, ALL_CU, no_track=False)
    rule_area("U1_ESCAPE", 18.4, 24.6, 21.2, 27.4, ALL_CU,
              no_pour=False, no_track=False, no_via=False)
    # The split channel necks from 0.8 mm to 0.2 mm where it passes under U1:
    # bump rows C and D are 0.4 mm apart, so a 0.8 mm plane gap cannot fit
    # between them.  0.2 mm is a routinely manufacturable plane gap.
    def split_area():
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True); z.SetZoneName("GND_SPLIT")
        z.SetDoNotAllowZoneFills(True); z.SetDoNotAllowTracks(False)
        z.SetDoNotAllowVias(True); z.SetDoNotAllowPads(False)
        ls = pcbnew.LSET()
        for l in ALL_CU: ls.AddLayer(l)
        z.SetLayerSet(ls)
        g, n = SPLIT_GAP/2, 0.1
        y1, y2 = 24.4, 27.6
        pts = [(SPLIT_X-g, 0.0), (SPLIT_X-g, y1), (SPLIT_X-n, y1),
               (SPLIT_X-n, y2), (SPLIT_X-g, y2), (SPLIT_X-g, H),
               (SPLIT_X+g, H), (SPLIT_X+g, y2), (SPLIT_X+n, y2),
               (SPLIT_X+n, y1), (SPLIT_X+g, y1), (SPLIT_X+g, 0.0)]
        o = z.Outline(); o.NewOutline()
        for (px, py) in pts: o.Append(mm(px), mm(py))
        z.SetAssignedPriority(100); board.Add(z)
    split_area()

    # ---- copper pours
    def pour(net, layer, pts, priority=0, name=""):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer); z.SetNet(board.FindNet(net))
        z.SetZoneName(name or f"{net}_{board.GetLayerName(layer)}")
        z.SetAssignedPriority(priority)
        # no local clearance override: the pour must respect each net class,
        # notably RF (0.60 mm) and PATIENT (0.508 mm)
        z.SetMinThickness(mm(0.2))
        # Solid, not thermal relief.  Spokes add inductance to exactly the
        # decoupling return paths that exist to remove it, and the boards
        # thermal pads want maximum copper, not four spokes.
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        o = z.Outline(); o.NewOutline()
        for (px, py) in pts: o.Append(mm(px), mm(py))
        board.Add(z)

    m = 0.3
    gapL = SPLIT_X - SPLIT_GAP/2
    gapR = SPLIT_X + SPLIT_GAP/2
    nk, y1, y2 = 0.1, 24.4, 27.6
    A = [(m, m), (gapL, m), (gapL, y1), (SPLIT_X-nk, y1), (SPLIT_X-nk, y2),
         (gapL, y2), (gapL, H-m), (m, H-m)]
    kx, ky = ANT_KO[0] - 0.3, ANT_KO[3] + 0.3      # keepout plus 0.3 mm margin
    D = [(gapR, m), (kx, m), (kx, ky), (W-m, ky), (W-m, H-m), (gapR, H-m),
         (gapR, y2), (SPLIT_X+nk, y2), (SPLIT_X+nk, y1), (gapR, y1)]
    for lay in (pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        pour(GA, lay, A); pour(GD, lay, D)
    pour("GND_C20", pcbnew.B_Cu,
         [(28.6, 8.8), (30.9, 8.8), (30.9, 10.8), (28.6, 10.8)], 5, "C20_ISLAND")

    P = pcbnew.In3_Cu
    # V1P8A reaches 1.2 mm east of the split, but ONLY under U1, so the DVDD
    # bump D1 has an L3 island to land on.  L3 carries no ground, so this does
    # not touch the L2 ground split.
    pour("V1P8A",   P, [(m, 18.0), (gapL, 18.0), (gapL, 23.4), (21.4, 23.4),
                        (21.4, 28.6), (gapL, 28.6), (gapL, H-m), (m, H-m)], 10)
    # V_SYS spans the charger and the converter, both inside the frame
    pour("V_SYS",   P, [(35.0, ky), (W-m, ky), (W-m, 34.5), (35.0, 34.5)], 8)
    pour("V2P5",    P, [(35.0, 34.5), (W-m, 34.5), (W-m, H-m), (35.0, H-m)], 12)
    pour("V2P5F",   P, [(gapR, 28.5), (35.0, 28.5), (35.0, H-m), (gapR, H-m)], 12)
    pour("V1P8D",   P, [(gapR, 21.0), (35.0, 21.0), (35.0, 28.5), (gapR, 28.5)], 12)
    pour("VDD_nRF", P, [(24.5, ky), (35.0, ky), (35.0, 20.5), (24.5, 20.5)], 16)

    board.BuildListOfNets()
    board.Save(BOARD_FILE)
    print("saved", BOARD_FILE)
    print("nets:", board.GetNetCount(), " footprints:", len(board.Footprints()))


main()
















































