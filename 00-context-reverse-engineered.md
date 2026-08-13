# BioZ Muscle Monitor — Reverse-Engineering Context

Source: an unpublished 2026 Hungarian-language undergraduate thesis (90 pages) on
monitoring muscle activity with bioimpedance spectroscopy, from a Hungarian technical
university's electrical engineering programme. Cited here without identifying the
student, supervisors, or institution, out of respect for the author's privacy.
Original design captured in KiCad 9.0, 5 schematic sheets, 4-layer PCB.

This document is the extracted, datasheet-verified specification used to drive the
schematic → PCB → enclosure agent pipeline. Everything below is traced either to the
thesis text, to a schematic figure read at native resolution, or to a manufacturer
datasheet (marked **[DS]** where verified).

---

## 1. What the device is

A portable, battery-powered **bioimpedance spectroscopy (BIS)** instrument that measures
the electrical impedance of skeletal muscle (biceps) to track fatigue and fluid shift
during and after exercise. Intended for gym use as well as clinical/research use.

Physiological basis from the literature review: muscle resistance R rises ~9–10 % at
60–100 % MVC (Li et al.), and both R and reactance X fall measurably after eccentric
loading (Freeborn et al.) — so a localized BIS measurement is sensitive enough to track
muscle work.

### Functional requirements (thesis §3.1)

| # | Requirement |
|---|---|
| 1 | Compact, wearable, user-friendly |
| 2 | Longest possible run time per charge |
| 3 | Measured data must survive loss of supply (non-volatile) |
| 4 | Wireless link for configuration and data readout |

### Technical requirements

| Parameter | Value |
|---|---|
| Data acquisition duration | 2 h |
| Frequency sweep | 20 predetermined frequencies |
| Sweep period | T_sweep = 1 s |
| Measurement topology | bipolar and tetrapolar (4-electrode) supported |

Architecture decision: an **integrated AFE** was chosen over a discrete excitation /
filter / gain chain, for development time, lower circuit complexity, better SNR and
lower project risk. A docking-station concept was rejected in favour of a single
self-contained unit with BLE.

---

## 2. System block diagram (thesis fig. 8)

```
 3.7 V / 1.43 Ah Li-po ──► POWER ──┬──► 2.5 V  (MCU)
                                   └──► 1.8 V  (AFE + memory)

 BUTTON ──1 line──► uC ──SPI (4+2)──┬──► MEM  (1.8 V)
                                    └──► AFE  (1.8 V)
```

SPI is shown as "4+2": four shared bus lines (SCK, SDI, SDO, + ) with two separate
chip selects — one for the AFE, one for the F-RAM. Plus an interrupt line from the AFE.

---

## 3. Verified part selection

| Function | Part | Package | Status |
|---|---|---|---|
| BioZ AFE | **MAX30009ENA+** (Analog Devices) | 25-WLP, 2.03 × 2.03 mm, 0.4 mm pitch | **[DS] verified** |
| MCU + BLE | **nRF54L15-QFAA-R** (Nordic) | QFN48 6×6 | verified via BOM/schematic |
| Non-volatile store | **CY15V108QI-20LPXI** (Infineon) | 8-GQFN | 8 Mb (1 MB) F-RAM, SPI 20 MHz |
| Battery charger / power path | **BQ24073RGT** (TI) | VQFN-16 | linear charger, power-path |
| Buck-boost DC/DC | **MAX77827BEFD+T** (ADI/Maxim) | 14-FC2QFN 2.5×2.5 | 2.5 MHz, >90 % eff. |
| 1.8 V analog LDO | **ADPL40502ACPZ-1.8-R7** (ADI) | 6-lead 2×2 LFCSP (CP-6-3) | **[DS] verified** — real part |
| Schmitt inverter (debounce) | **SN74LVC1G14DCKR** (TI) | SC70-5 | |
| Antenna | **WE-MCA 74889302450** (Würth) | 2400–2500 MHz chip antenna | |
| NTC (battery temp) | **103AT-2** (Semitec) | 10 kΩ 1 % | |
| Crystals | ABS06-32.768kHz-9-1-T; ABM10-32.000MHz-D30-T3 | | |

**[DS] MAX30009 confirmed characteristics** (analog.com datasheet, 96 pp):
complete BioZ AFE for wearables; 25-bump WLP 2.03 × 2.03 mm; **250 µW at 1.8 V AVDD**;
PLL-based timing subsystem for fine-tuned stimulus/sample frequencies, synchronizable
with other ADI biosensors; two high-resolution ADCs give simultaneous I (real) and
Q (imaginary) measurement; flexible input/output MUX supports bipolar and tetrapolar;
**four-wire calibration port for an external precision resistor** for highest absolute
accuracy. This directly justifies the thesis's R7 = 680 Ω 0.1 % calibration resistor.

**[DS] ADPL40502 confirmed**: 2.2–5.5 V in, 200 mA, 150 mV dropout at 200 mA,
290 µA operating current, stable with 1 µF ceramic in/out, low noise **without** a
bypass capacitor, 5-lead TSOT or 6-lead 2×2 LFCSP. Thesis quotes 70 dB PSRR and
20 µV_RMS output noise, 300 mA current limit, 150 °C thermal shutdown.

---

## 4. Recovered schematic connectivity

Read directly from the KiCad sheets embedded in the thesis (figs. 22–26).

### 4.1 AFE sheet — U1 MAX30009ENA+ (`BioZ_AFE.kicad_sch`, sheet 5/5)

Bump map **verified against the ADI datasheet pin description — the thesis matches
the datasheet exactly**:

| Bump | Name | Net in design |
|---|---|---|
| A1 | EL1 | via C5 47 nF to J1.4 (electrode 1) |
| A2 | EL2A | **not connected** |
| A3 | EL2B | via R5 40.2 kΩ |
| B1 | EL4 | via C6 47 nF to J1.1 (electrode 4) |
| B2 | EL3A | **not connected** |
| B3 | EL3B | via R6 40.2 kΩ |
| A4 | CAL1 | ┐ tied together, top of R7 |
| A5 | CAL2 | ┘ |
| B5 | CAL3 | ┐ tied together, bottom of R7 |
| B4 | CAL4 | ┘ |
| C1 | AVDD | U1.8V; C4 0.1 µF → GNDA |
| C2 | VREF | C1 1 µF |
| C3 | AGND | GNDA |
| C4 | DRVSJ | DRVSJ net |
| C5 | DRVXR | tied to DRVSJ |
| D1 | DVDD | U1.8V; C3 0.1 µF |
| D2 | CSB/I2C_SEL | CS (SPI mode) |
| D3 | FCLK | not connected |
| D4 | TRIG | GNDD |
| D5 | DRVXC | C7 47 nF → DRVSJ |
| E1 | DGND | GNDD |
| E2 | SDO/ADDR | SDO |
| E3 | SDI/SDA | SDI |
| E4 | SCLK/SCL | SCLK |
| E5 | INT | INT |

Electrode connector **J1** = S4B-PH-K-S, 4-pin → tetrapolar electrode harness.
Calibration network: **R7 = 680 Ω, 0.1 % (ERA-3AEB681V)** in a true 4-wire Kelvin
connection across CAL1/CAL2 (force) and CAL3/CAL4 (sense).
AFE local bulk: C2 10 µF on U_1.8V → GNDA.

### 4.2 Memory sheet — IC1 CY15V108QI-20LPXI (`BioZ_Memory.kicad_sch`, sheet 4/5)

| Pin | Name | Net |
|---|---|---|
| 1 | /CS | CS (own chip select) |
| 2 | SO | SO |
| 3 | /WP | NWP |
| 4 | VSS | GNDD |
| 5 | SI | SI |
| 6 | SCK | SCK |
| 7 | DNU | GNDD |
| 8 | VDD | U_1.8V |

### 4.3 MCU sheet — U5 nRF54L15-QFAA-R (sheet 3/5)

| Pin | Name | Net |
|---|---|---|
| 1, 2 | P1.00/XL1, P1.01/XL2 | Y1 32.768 kHz crystal |
| 5 | P1.04/AIN0 | **AIN0** — battery sense divider |
| 7 | P1.06/AIN2 | MEM_WP |
| 10, 22 | VDD | VDD1 |
| 12 | P2.01/SPI.SCK | nSPI_CLK |
| 13 | P2.02/SPI.SDI/SDO | nSPI_SDO |
| 14 | P2.03 | nSPI_CS2 |
| 15 | P2.04/SPI.SDI/SDO | nSPI_SDI |
| 16 | P2.05/SPI.CS | nSPI_CS1 |
| 18 | P2.07/TRACEDATA[0]/SWO | SWO |
| 23 | P0.00 | LED |
| 24 | P0.01 | Button |
| 25, 26 | SWDIO, SWDCLK | SWD header J2 |
| 27 | P0.02 | INT_AFE |
| 30 | NRESET | reset |
| 31 | ANT | antenna matching network |
| 32 | VSS_PA | |
| 33 | DECRF | 2.2 nF |
| 34, 35 | XC1, XC2 | Y2 32 MHz crystal |
| 36, 48 | VDD | VDD2 |
| 43 | DECA | 10 nF |
| 45 | DECD | 2.2 nF |
| 46 | DCC | L3 4.7 µH + 2.2 µF (DC/DC mode) |
| 44, 49 | VSS | GNDD |
| 3, 4, 6, 8, 9, 11, 17, 19, 20, 21, 28, 29, 37–42 | | not connected |

Supply decoupling: VDD1 = 10 nF ∥ 100 nF; VDD2 = 100 nF ∥ 10 nF ∥ 100 nF, fed from
UFilter_2.5V through FL1 120 Ω ferrite.
Antenna chain: ANT → L4 2.7 nH → L5 3.5 nH → L6 3.5 nH → AE1 chip antenna, with
shunt caps 1.5 pF / 2 pF / 0.3 pF / 3.9 pF (C19–C23).
Programming: **SWD** via J2 (Würth 62201021121, 10-pin 1.27 mm header).

### 4.4 Power sheet — (`BioZ_Power.kicad_sch`, sheet 2/5)

**U8 BQ24073RGT** battery charger / power path:
- P1 (S3B-PH-SM4-TB, 3-pin) = magnetic charge connector input → IN (pin 13), 1 µF to GND
- pin 15 TD, pin 3 CE, pin 14 TMR → GND rail
- pin 6 EN1, pin 5 EN2 → Ubat
- pin 12 ILIM → **R = 1.5 kΩ** → GND  ⇒ input current limit ≈ 1 A
- pin 16 ISET → **R14 = 1.13 kΩ** → GND ⇒ fast-charge current 800 mA
- pin 10 OUT → Ubat rail, 4.7 µF
- pin 2 BAT → 4.7 µF, → J7 battery connector, → Ubat_gd
- pin 1 TS → U9 103AT-2 10 k NTC → GND
- pins 7 /PGOOD, 9 /CHG → 1.5 kΩ pull-ups to Ubat

Design math from thesis: R_ISET = K_ISET/I_CHG = 890 AΩ / 0.8 A = 1.1125 kΩ → E96 **1.13 kΩ**;
R_ILIM = K_ILIM/I_INmax = 1550 AΩ / 1.033 A → **1.5 kΩ**.

**U7 MAX77827BEFD+T** buck-boost → 2.5 V:
- R15 = **634 kΩ 1 %** on SEL sets V_OUT = 2.5 V (datasheet lookup table)
- FPWM pulled to V_OUT through R19 10 kΩ → forced-PWM, stable switching frequency
- L8 1 µH inductor; C26 1 µF, C29 10 µF input; C9 22 µF, C35 100 nF output
- Ratings: V_IN 1.8–5.5 V, V_OUT 2.3–5.3 V, 1.6 A buck / 900 mA boost, 2.5 MHz

**Output LC filter** (thesis §3.5.2.3), designed for f_c = 250 kHz (one decade below
the 2.5 MHz switching frequency), damped to Q_S < 0.5:
- R16 = 0.1 Ω, L7 = **32 nH** (MHQ1005P3N2BT000), C32 3.3 µF ∥ C33 10 µF = 13.3 µF
- Result: UFilter_2.5V

**U10 ADPL40502ACPZ-1.8-R7** LDO → 1.8 V for AFE + memory, fed from UFilter_2.5V.
C28 1 µF in. Dissipation (2.5−1.8) × 0.2 A = 0.14 W.

Also on this sheet: J8 on/off slide switch; R1 0 Ω single-point link joining **GNDA to
GNDD**; H1 Würth SMD shield frame 26 × 26 mm over the power section; U3/U4/U6 and
U11/U12/U13 support pads.

### 4.5 Battery monitoring (thesis §3.5.3)

Divider R2 = 10 kΩ / R3 = 1 kΩ from Ubat into AIN0, so 4.5 V battery → 0.45 V ADC
full scale (nRF54L15 internal 0.9 V reference, Gain = 1, U_ADCmax = 0.5 × V_REF/Gain).
10-bit ADC, U_LSB = 0.45/1023 = 0.439 mV. Low-battery cut-off at 3.1 V terminal
voltage → 0.281 V at ADC → **threshold code 640**. Below 640 the device stops saving
data and will not start.

### 4.6 Status LED (§3.5.4)

GPIO P0.00 source-drives LED1 (CSL1901UW1, V_F = 1.8 V) at 2 mA:
R = (2.5 − 1.8)/2 mA = 350 Ω → E96 **348 Ω**. Light guided out through a
BIVAR VLP-500-R/F vertical light pipe.

### 4.7 Button debounce (§3.5.5)

RC + Schmitt-trigger (SN74LVC1G14, inverting). Thresholds taken as the datasheet
mid-range: U_HL = 0.725 V, U_HH = 1.335 V; first pulse t_el = 20 µs, total bounce
t_p = 900 µs, C = 10 nF, U_T = 2.5 V.
- R2 (discharge) = −t_el / (C·ln(U_HL/U_T)) = 1615.67 Ω → **1.6 kΩ**
- R (pull-up) computed = 207.37 kΩ; split into **R1 2.2 kΩ + R3 220 kΩ** in series to
  avoid a single very high-impedance node, with **D1 BAT54-02V** separating the charge
  and discharge paths.

---

## 5. Power budget and run time (thesis §3.5.1)

| Component / state | Current |
|---|---|
| MAX30009 measuring | 1.5 mA |
| MAX30009 idle (250 µW / 1.8 V) | 138 µA |
| nRF54L15 sleep | 1.5 µA |
| nRF54L15 CPU active @128 MHz | 2.6 mA |
| nRF54L15 BLE RX @1 Mbps | 3.4 mA |
| nRF54L15 BLE TX @1 Mbps | 4.8 mA |
| CY15V108QI active @20 MHz | 1.3 mA |
| CY15V108QI sleep | 3.5 µA |

Worst-case simultaneous draw ⇒ supply must deliver ≥ **10.2 mA**.
Charge over a 2 h period Q_T0 = 19 997.268 mAs ⇒ **I_avg = 2.777 mA**.
With a 1430 mAh cell ⇒ estimated **514.9 h ≈ 21.5 days** of operation.

### Storage sizing (§3.3.1.2)

One I/Q result = 6 bytes (2 × 3-byte samples). 20 frequencies/s × 6 B = 120 B/s.
7200 s × 120 B = **864 000 B = 864 kB**, i.e. 144 000 samples. The MAX30009's internal
FIFO holds only 256 samples and is volatile — hence the external 1 MB F-RAM.

### Thermal (§3.5.6)

T_ambient assumed 40 °C, T_J = T_K + R_θJA · P_D:

| Part | P_D | R_θJA | T_J |
|---|---|---|---|
| BQ24073 (VQFN) | 1.04 W | 44.5 °C/W | 86.3 °C |
| MAX77827 (FC2QFN) | 0.40 W | 63.4 °C/W | 65.4 °C |
| ADPL40502 (LFCSP) | 0.14 W | 63.6 °C/W | 48.9 °C |
| nRF54L15 (QFN48) | 50 mW | 24.86 °C/W | 41.2 °C |
| SN74LVC1G14 (SOT-23) | 25 µW | 357.1 °C/W | 40.0 °C |
| MAX30009 (WLP) | 4.86 mW | 54.43 °C/W | 40.3 °C |
| CY15V108QI (GQFN) | 2.7 mW | 113.5 °C/W | 40.3 °C |

Total ΣP_D = 1.6375 W. Enclosure R_TH = l/(λ·A) = 0.002/(0.17 × 14.25e−3) = 0.826 °C/W
⇒ case temperature 41.4 °C.

---

## 6. PCB (thesis §3.8) — original design, to be reproduced

- Tool: **KiCad 9.0**
- **4 layers**: Top (components + signals) / GND (solid pour, reference + shield) /
  Power (voltage islands) / Bottom (signals)
- Track widths: **20 mil** for power/high current, **10 mil** for signals
- Board outline: **50 mm × 44 mm**
- Analog and digital ground pours are separate, **joined at a single point** (R1, 0 Ω)
- **No copper pour under or around the chip antenna**, on any layer
- Mechanical concept: instead of standoffs and screws, two additional PCBs solder to
  the main board via pads, forming an **inverted-U** that slides into the case
- Metal shield frame (H1, Würth 26 × 26 mm) over the power section

## 7. Enclosure (thesis §3.3.1.5)

- **CamdenBoss BIM2000/10-BLK/BLK**, ABS, **IP54**, **75 × 50 × 27 mm** outside,
  2 mm wall, λ = 0.17 W/m·K
- Openings/features: slide switch (G-107-SI-0511 SPDT), pushbutton
  (SCHURTER 52-03-80, 18 mm, IP65), light pipe (BIVAR VLP-500-R/F), magnetic charge
  connector (MULTICOMP MP009329), electrode lead exit
- Battery: Jauch **LP103048JU** Li-po, 3.7 V, 1.43 Ah, with PCM and 2 wires

---

## 8. Complete BOM as published (thesis §3.7, table 9)

| # | Ref | Qty | Value | Part number | Mfr | Package |
|---|---|---|---|---|---|---|
| 1 | AE1 | 1 | – | WE-MCA_74889302450 | Würth | chip antenna 2400–2500 MHz |
| 2 | C1, C26, C27, C28 | 4 | 1 µF | CC0603JRX7R7BB105 | YAGEO | 0603 |
| 3 | C11, C12 | 2 | 2.2 µF | GRM033D80E225ME47D | Murata | 0201 |
| 4 | C14–C17, C24, C35 | 6 | 100 nF | GCM31C5C1H104FA16L | Murata | 1206 |
| 5 | C18 | 1 | 2.2 nF | GRM033R71A222KA01D | Murata | 0201 |
| 6 | C19 | 1 | 1.5 pF | GJM0335C1E1R5WB01D | Murata | 0201 |
| 7 | C2, C13 | 2 | 10 µF | CL05X106MQ5NUNL | Samsung | 0402 |
| 8 | C20 | 1 | 2 pF | GJM0335C1E2R0WB01D | Murata | 0201 |
| 9 | C21 | 1 | 0.3 pF | GRM0335C1HR30BA01D | Murata | 0201 |
| 10 | C22 | 1 | 10 nF | GJM0335C1E1R5WB01D | Murata | 0201 |
| 11 | C23 | 1 | 3.9 pF | GRM0335C1H3R9CA01D | Murata | 0201 |
| 12 | C25 | 1 | 10 nF | C0603C103F4GACTU | KEMET | 0603 |
| 13 | C29, C33 | 2 | 10 µF | C0805X106J8RACTU | KEMET | 0805 |
| 14 | C3, C4 | 2 | 0.1 µF | GCM31C5C1H104FA16L | Murata | 1206 |
| 15 | C30, C31 | 2 | 4.7 µF | C0805C475M9RACAUTO | KEMET | 0805 |
| 16 | C32 | 1 | 3.3 µF | GCG31CR71E335JA01L | Murata | 1206 |
| 17 | C5, C6, C7 | 3 | 47 nF | C0805C475J8RACAUTO | KEMET | 0805 |
| 18 | C9 | 1 | 22 µF | CL10A226KQ8NRNE | Samsung | 0603 |
| 19 | D1 | 1 | 30 V 0.2 A | BAT54-02V | Vishay | SOD-523 |
| 20 | FL1 | 1 | 120 Ω | BLM03AG121SN1D | Murata | 0201 |
| 21 | H1 | 1 | – | WE-SHC SMD-FRAME | Würth | 26 × 26 mm |
| 22 | IC1 | 1 | – | CY15V108QI-20LPXI | Infineon | 8-GQFN |
| 23 | J1 | 1 | – | S4B-PH-K-S | JST | 4-pin |
| 24 | J2 | 1 | – | 62201021121 | Würth | 10-pin 1.27 mm |
| 25 | J5, J7, J8 | 3 | – | S2B-PH-SM4-TB | JST | 2-pin SMD R/A |
| 26 | L3 | 1 | 4.7 µH | KLZ1608MHR4R7WTD25 | TDK | 0603 |
| 27 | L4 | 1 | 2.7 nH | LQP03HQ2N7B02D | Murata | 0201 |
| 28 | L5, L6 | 2 | 3.5 nH | LQP03HQ3N5B02D | Murata | 0201 |
| 29 | L7 | 1 | 32 nH | MHQ1005P3N2BT000 | TDK | 0402 |
| 30 | L8 | 1 | 1 µH | MEKK2016H1ROM | Taiyo Yuden | 0806 |
| 31 | LED1 | 1 | 1.8 V 2 mA | CSL1901UW1 | ROHM | 0603 |
| 32 | P1 | 1 | – | S3B-PH-SM4-TB | JST | 3-pin R/A |
| 33 | R1 | 1 | 0 Ω | RC0603FR-070RL | YAGEO | 0603 |
| 34 | R10 | 1 | 2.2 kΩ | RC0603FR-072K2L | YAGEO | 0603 |
| 35 | R11 | 1 | 210 kΩ | RC0603FR-07210KL | YAGEO | 0603 |
| 36 | R12 | 1 | 1.6 kΩ | RC0603FR-071K6L | YAGEO | 0603 |
| 37 | R13, R18, R18 | 3 | 1.5 kΩ | RC0603FR-071K5L | YAGEO | 0603 |
| 38 | R14 | 1 | 1.13 kΩ | RC0603FR-071K13L | YAGEO | 0603 |
| 39 | R15 | 1 | 634 kΩ | RC0603FR-07634KL | YAGEO | 0603 |
| 40 | R16 | 1 | 0.1 Ω | ERJ-3RSFR10V | Panasonic | 0603 |
| 41 | R2, R19 | 2 | 10 kΩ | RC0603FR-0710KL | YAGEO | 0603 |
| 42 | R3 | 1 | 1 kΩ | RC0603FR-071KL | YAGEO | 0603 |
| 43 | R4 | 1 | 348 Ω | RC0603FR-07232RL | YAGEO | 0603 |
| 44 | R5, R6 | 2 | 40.2 kΩ | RC0603FR-0740K2L | YAGEO | 0603 |
| 45 | R7 | 1 | 680 Ω | ERA-3AEB681V | Panasonic | 0603, 0.1 % |
| 46 | R8 | 1 | 1 kΩ | RC0603FR-071KL | YAGEO | 0603 |
| 47 | R9 | 1 | 100 Ω | RC0603FR-07100RL | YAGEO | 0603 |
| 48 | U1 | 1 | – | MAX30009ENA+ | ADI | 25-WLP |
| 49 | U10 | 1 | – | ADPL40502ACPZ-1.8-R7 | ADI | CP-6-3 |
| 50 | U2 | 1 | – | SN74LVC1G14DCKR | TI | SC70-5 |
| 51 | U3, U4, U6 | 3 | – | support pads | – | – |
| 52 | U5 | 1 | – | NRF54L15-QFAA-R | Nordic | QFN48 6×6 |
| 53 | U7 | 1 | – | MAX77827BEFD+T | ADI | 14-FC2QFN |
| 54 | U8 | 1 | – | BQ24073RGT | TI | VQFN-16 |
| 55 | U9 | 1 | 10 kΩ | 103AT-2 | Semitec | NTC |
| 56 | Y1 | 1 | 32.768 kHz | ABS06-32.768KHZ-9-1-T | Abracon | 2-SMD |
| 57 | Y2 | 1 | 32 MHz | ABM10-32.000MHZ-D30-T3 | Abracon | 4-SMD 2.5×2 |
| 58 | Case | 1 | – | BIM2000/10-BLK/BLK | CamdenBoss | ABS |
| 59 | Button | 1 | – | 52-03-80 | SCHURTER | 18 mm IP65 |
| 60 | Switch | 1 | – | G-107-SI-0511 | CW Industries | SPDT 500 mA |
| 61 | Magnetic conn. | 1 | – | MP009329 | MULTICOMP PRO | |
| 62 | Light pipe | 1 | – | VLP-500-R/F | BIVAR | |
| 63 | Battery | 1 | – | LP103048JU + PCM | Jauch | 3.7 V 1.43 Ah |

---

## 9. Defects found in the source design

Found by checking the thesis schematic against the manufacturer datasheets. These are
to be **corrected** in our reproduction, not copied.

1. **MAX30009 VREF cap returns to the wrong ground.** The datasheet states: connect a
   1 µF X5R capacitor between VREF and **AGND**. The thesis returns C1 to GNDD.
   On a part whose whole value is absolute impedance accuracy, referencing the ADC
   reference buffer to the digital ground is a real accuracy and noise risk.
2. **DVDD is under-decoupled.** The datasheet asks for **0.1 µF *and* 10 µF** on both
   AVDD and DVDD. The design has 0.1 µF on DVDD and no local bulk.
3. **DRVXR is tied to DRVSJ.** The datasheet gives two legal options — a precision
   resistor between DRVXR and DRVXC to set drive current externally, or **leave DRVXR
   unconnected** to use the internal current setting. Shorting DRVXR to DRVSJ is
   neither.
4. **No decoupling capacitor on the F-RAM VDD** anywhere on the memory sheet.
5. **BOM reference designator collision**: item 37 lists "R13; R18; R18" for a quantity
   of 3 — one designator is duplicated, so one 1.5 kΩ resistor is unaccounted for.
6. **BOM part/value mismatches** (transcription errors in the source):
   - item 43: R4 value 348 Ω but part number `RC0603FR-07232RL` is a 232 Ω part
   - item 10: C22 value 10 nF but part number is the 1.5 pF `GJM0335C1E1R5WB01D`
   - item 17: C5–C7 value 47 nF but part number `C0805C475J8RACAUTO` is 4.7 µF
   - item 35: R11 value 210 kΩ, while the debounce calculation calls for 220 kΩ
7. **BQ24073 thermal margin is thin.** At 1.04 W the computed junction temperature is
   86.3 °C in a sealed IP54 ABS box at 40 °C ambient — inside spec but with little
   headroom. Worth reducing fast-charge current or improving the copper thermal path.
8. **F-RAM DNU pin tied to GND** — "Do Not Use" pins should generally be left floating
   unless the datasheet explicitly permits grounding; to be confirmed against the
   Infineon datasheet.

---

## 10. Notes for the downstream agents

- Design intent is a **faithful reproduction** of the thesis device, with the §9 defects
  corrected and each correction called out.
- The AFE is a WLP with 0.4 mm pitch — this forces the fabrication class. Expect
  laser-drilled microvias or via-in-pad; confirm against the chosen fab's capability
  before committing the stackup.
- Keep the single-point analog/digital ground join (R1) and the antenna keep-out.
- Board outline 50 × 44 mm, 4 layers, must fit a 75 × 50 × 27 mm ABS box alongside a
  LP103048 cell (approx. 48 × 30 × 10 mm).
