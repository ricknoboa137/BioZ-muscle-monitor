# PCB brief — BioZ Muscle Monitor rev B

Source schematic: `C:\Users\User\Documents\BioZ-muscle-monitor\BioZ-Muscle-Monitor-Design-Dossier-RevB.docx` · `C:\Users\User\Documents\BioZ-muscle-monitor\schematic.html`
Net list: dossier section 9, or the same table in `schematic.html`.

**Status of inputs.**

*Verified pin-by-pin against the manufacturer datasheet, safe to route:* MAX30009ENA+ (all 25 bumps), nRF54L15-QFAA QFN48 (all 49 pins), CY15V108QI 8-GQFN (all 8 pins), BQ24073RGT VQFN-16 (all 16 pins + thermal pad), SN74LVC1G14 SC70-5 (KiCad 10 official symbol).

*Verified since first draft:* **MAX77827 pins 7 and 12 — CLOSED.** User supplied the datasheet (Maxim/ADI, 23 pp). Pin Description table, p.13: pin 7 is a second **IN** pad (shared with pin 6, both bypassed to PGND with 10 µF), pin 12 is a second **OUT** pad (shared with pin 11, both bypassed to PGND with 22 µF). The 14-FC2QFN simply duplicates IN and OUT across two pads each for current handling — no change to the schematic net assignment, tie 6+7 together and 11+12 together in the footprint/layout.

*Verified since first draft:* **ADPL40502 6-lead LFCSP numbering — CLOSED.** User supplied the datasheet (ADI, Rev. 0, 17 pp). Table 5, p.7: pin 1 = VOUT, pin 2 = NC, pin 3 = GND, pin 4 = EN, pin 5 = NC, pin 6 = VIN, plus an exposed pad that **must be tied to GND** (thermal/electrical). Matches the schematic's VIN/VOUT/GND/EN assignment exactly — no NC pin was left floating incorrectly. Both instances (U10, U14) share this footprint; ensure the exposed pad has a via array to GNDD/GNDA respectively.

*NOT verified — do not commit a footprint until closed:* J2 SWD header numbering. Antenna ladder node order. Full list with resolutions in §12.

**This brief is a placement and constraint specification, not a routing solution.** Where it states a physical reason for a constraint, that reason is the thing to preserve — if your placement achieves the same reason differently, that is fine. Where it states a number taken from a datasheet, that number is not negotiable.

---

## 1. Board outline and mechanical

| Item | Value |
|---|---|
| Outline | **50.0 × 44.0 mm**, rectangular, 2 mm corner radius |
| Board thickness | 1.0 mm (see §2 — thin board is deliberate, for enclosure stack height) |
| Construction | Rigid, 4 layer |
| Mounting | **No screws or standoffs.** Two auxiliary PCBs solder to the main board via edge pads, forming an inverted-U that slides into the enclosure rails. Provide 2 × edge pad rows, 1.6 mm pitch, on the two 44 mm edges |
| Enclosure | CamdenBoss BIM2000/10-BLK/BLK, ABS, IP54, **75 × 50 × 27 mm outside, 2 mm wall** → 71 × 46 × 23 mm internal |
| Battery | Jauch LP103048JU, approx **48 × 30 × 10 mm**, sits alongside the PCB inside the same cavity |

**Internal volume budget.** Cavity is 71 × 46 × 23 mm. The cell takes 48 × 30 × 10 mm. The board is 50 × 44 mm, so it fits the 71 × 46 footprint with 21 mm of length to spare and 2 mm across the width — **the 46 mm internal width against a 44 mm board leaves only 1 mm per side.** Confirm the enclosure's internal ribs and boss features do not intrude before committing the outline. This is the tightest mechanical dimension in the design.

Height stack: 10 mm cell + 1.0 mm board + tallest component. That leaves about 12 mm for components if the cell and board are stacked, or the full 23 mm if they sit side by side. Prefer **side by side** — it keeps the cell away from the charger's thermal pad (§8).

### Component and user-interface positions

| Feature | Part | Position requirement |
|---|---|---|
| Pushbutton | SCHURTER 52-03-80, 18 mm, IP65 | Panel-mounted in the lid, wired to SW1 pads. Not board-mounted — the 18 mm body will not fit the component height budget |
| Slide switch | G-107-SI-0511 SPDT | Side wall, aligned to J8 |
| Light pipe | BIVAR VLP-500-R/F | Vertical, directly over LED1. LED1 must be on the **top** layer with its optical axis normal to the board |
| Magnetic charge connector | MULTICOMP MP009329 | Short edge, wired to P1 |
| Electrode lead exit | JST S4B-PH-K-S (J1) | **Opposite short edge from the charge connector.** Physical separation of the patient-connected harness from the mains-referenced charge path is a safety requirement, not a preference |
| SWD header | Würth 62201021121, 10-pin 1.27 mm | Any accessible position; it is a build-time interface only. Must be reachable with the lid off |

### Maximum component height per zone

| Zone | Max height |
|---|---|
| Under the shield frame (power section) | 2.2 mm — the Würth SMD frame sets this |
| Antenna keepout zone | 0 mm (nothing at all, see §6) |
| General top side | 3.0 mm |
| Bottom side | 1.0 mm — the board sits against an enclosure rail |

---

## 2. Layer stack

**4 layers.** Layer count is set by two independent requirements, either of which alone would force it: the 0.4 mm pitch WLP escape (§10), and the need for an unbroken ground reference under the electrode nets while keeping analog and digital pours separate.

| Layer | Name | Function | Copper |
|---|---|---|---|
| L1 | Top | Components and signals. Split GNDA / GNDD pour in unused areas | 1 oz finished |
| L2 | GND | **Solid ground reference**, split into GNDA and GNDD regions. This is the RF and analog return plane | 0.5 oz |
| L3 | Power | Voltage islands: V_SYS, V2P5, V2P5F, V1P8A, V1P8D, VDD_nRF | 0.5 oz |
| L4 | Bottom | Signals, and the isolated ground island for C20 (§4) | 1 oz finished |

Dielectric: standard FR-4, Tg 150 or better. Total 1.0 mm.

**Controlled impedance:** one requirement only — the **ANT net and the matching-network ladder to AE1 must be 50 Ω single-ended, referenced to the L2 ground plane**. Ask the fabricator for their 50 Ω stackup on a 1.0 mm 4-layer build and set the trace width from their answer; do not assume a width. Everything else on this board is low speed and needs no impedance control.

---

## 3. Net classes

Every net in the net list belongs to exactly one class.

| Class | Nets | Trace width | Clearance | Via |
|---|---|---|---|---|
| **POWER_HIGH** | VIN_EXT, V_BAT, V_SYS | **20 mil** (0.51 mm) | 10 mil | 0.4 / 0.8 mm |
| **POWER_LOW** | V2P5, V2P5F, V1P8A, V1P8D, VDD_nRF, DCC, LX | **20 mil** (0.51 mm) | 10 mil | 0.4 / 0.8 mm |
| **SIGNAL** | SPI_SCK, SPI_SDO, SPI_SDI, AFE_CS, MEM_CS, MEM_WP, AFE_INT, AFE_PWR_EN, FPWM_CTL, nPGOOD, nCHG, LED_K, BTN_N, BTN_RC, SW_EN, SWDIO, SWDCLK, SWO, nRESET, POK | **10 mil** (0.25 mm) | 8 mil | 0.3 / 0.6 mm |
| **ANALOG_SENSE** | VREF, DRVSJ, DRVXC, CAL_F, CAL_S, VBAT_SENSE, TS_NTC, ISET, ILIM, SEL, BIAS | 10 mil | **12 mil** | 0.3 / 0.6 mm |
| **PATIENT** | EL_DRVP, EL_DRVN, EL_SENP, EL_SENN | **12 mil** | **20 mil minimum, see §4** | 0.3 / 0.6 mm |
| **RF** | ANT, RF_A, RF_B, RF_ANT | per fabricator's 50 Ω stackup | 3× trace width to any copper | no vias permitted |
| **GND_A** | GNDA | pour | — | 0.3 / 0.6 mm |
| **GND_D** | GNDD, VSS_PA | pour | — | 0.3 / 0.6 mm |

Note LX carries 1.6 A peak at 2.5 MHz. It is in POWER_LOW for width, but it is a switch node — see §4 and §5.

---

## 4. Critical routing constraints

Each constraint states its physical reason. A constraint without a reason gets optimised away by whoever routes it.

### 4.1 The four patient nets — EL_DRVP, EL_DRVN, EL_SENP, EL_SENN

- **EL_SENP and EL_SENN must be length- and geometry-matched to within 1 mm**, and routed as a loosely coupled pair with identical via count and identical layer usage. *Reason:* the sense pair feeds a differential input. Any asymmetry in track capacitance adds to the R5/R6 mismatch that already sets the 250 kHz sweep ceiling (design risk 2 in the dossier). Calibration through CAL1–CAL4 bypasses this path and cannot correct it.
- **Keep total track capacitance on EL_SENP/EL_SENN as low as achievable.** Route on Top, over a solid GNDA reference, but do not run them adjacent to any other track. *Reason:* the 40.2 kΩ series resistors work into whatever capacitance you add; every extra picofarad moves the 400 kHz pole down.
- **20 mil minimum clearance from any other net** and 40 mil from any switching node. Patient nets must not share a via barrel field with anything.
- **These nets must be routed entirely within the GNDA region** and must not cross the R1 stitch point or pass over the GNDD pour on any layer. *Reason:* a return current forced across the split is exactly the coupling path the split exists to prevent.
- Route them away from: L8 and the entire power section, the antenna, and the F-RAM.

### 4.2 The AFE calibration network — CAL_F, CAL_S, R7

- R7 is a **four-wire Kelvin** connection. CAL1/CAL2 land on one end of R7 and CAL3/CAL4 on the other. **The force and sense connections must meet at the resistor's own terminations, not at a shared track.** *Reason:* the whole point of the Kelvin connection is that track resistance is excluded from the measurement. Merging them early puts copper resistance directly into the absolute accuracy reference.
- R7 as close to U1 as the WLP escape allows.

### 4.3 The switching loop — L8, C29, C9, U7

- **Minimise the physical loop area of C29 → U7.IN → LX1 → L8 → LX2 → U7.OUT → C9 → PGND.** This is the highest-priority loop on the board. *Reason:* 1.6 A peak switching at 2.5 MHz radiates from loop area, and the victim is a 6.4 mV RMS measurement a few millimetres away. The LC filter and the LDO PSRR handle the conducted path; nothing but geometry handles the magnetic path.
- Keep the LX node copper **small in area** — just enough for current. *Reason:* LX is the high-dv/dt node and area on it is a capacitive antenna.
- OUTS is a Kelvin sense line. Route it as a thin track to the **far side of C9**, not to the OUT pin. *Reason:* it exists to regulate out the IR drop in the output track.
- The entire loop must sit under the shield frame (§6).

### 4.4 RF — ANT, RF_A, RF_B, RF_ANT

- 50 Ω controlled impedance, referenced to L2. **No vias anywhere in the RF chain.** Route entirely on Top.
- Keep the ladder as short and as straight as the reference layout allows.
- **C19's ground connects ONLY to nRF54L15 pin 32 (VSS_PA), on the top layer.** Pin 32 in turn connects **ONLY to pin 49** (the die pad), underneath the package. It must not connect to the general ground pour anywhere else. *Reason:* Nordic states this explicitly — it creates additional harmonic filtering. This is the single most commonly broken rule on nRF54L layouts.
- **C20's ground must be isolated from every ground layer except the bottom (L4) ground island.** *Reason:* also explicit in Nordic's reference layout, for the same harmonic-filtering purpose.
- **The ladder node order in the schematic is INFERRED, not verified (V8).** Take the node order and the physical geometry from Nordic's reference design files for circuit configuration 1, QFAA QFN-48, and match their layout as closely as the outline permits. Component *values* are confirmed correct.

### 4.5 Crystals

- Y1 (32.768 kHz) and Y2 (32 MHz) as close to their pins as possible, with a local ground guard.
- **No external load capacitors are fitted** — the nRF54L15 uses internal, firmware-configured load capacitance. Do not add footprints for them.
- Keep SPI and the switching node away from both crystals.

### 4.6 Battery sense

- VBAT_SENSE is a 91 kΩ source impedance node with a 100 nF capacitor (C36) on it. **C36 must be adjacent to the MCU pin, not to the divider.** *Reason:* it supplies the SAADC's sampling charge; its usefulness is proportional to how little track sits between it and the pin.

### 4.7 Digital

- SPI_SCK, SPI_SDO, SPI_SDI are shared between U1 and IC1. Keep total stub length short; there is no speed problem at 8–20 MHz, but **route SPI_SCK away from the electrode nets** — it is the only fast-edged digital signal that goes near the analog section.
- No length matching required on any digital net.

---

## 5. Placement zones and adjacency

The board divides into three zones. **The boundary between analog and digital runs roughly through the middle of the 50 mm dimension**, with the single R1 stitch on it.

```
   50 mm
 +--------------------------------------------------+
 |  ANTENNA KEEPOUT   |                             |
 |  (no copper, any   |   DIGITAL / POWER ZONE      |  44
 |   layer)           |   U5, IC1, U2, U7, U8       |  mm
 |   AE1 + ladder     |   shield frame over U7/U8   |
 |--------------------+--- R1 stitch ---------------|
 |          ANALOG ZONE (GNDA)                      |
 |          U1, R7, R5, R6, C5, C6, U10, J1         |
 +--------------------------------------------------+
        electrode exit                 charge conn
```

### Adjacency requirements, in priority order

| Priority | Requirement | Reason |
|---|---|---|
| 1 | **U1 decoupling:** C4 (0.1 µF) and C3 (0.1 µF) within 1.5 mm of the AVDD (C1) and DVDD (D1) bumps respectively, each with its own via to the correct ground. C2 (10 µF) and C42 (10 µF) may sit further out | The 0.1 µF parts carry the high-frequency return; loop inductance is what they are there to minimise |
| 2 | **C4 returns to GNDA. C3 and C42 return to GNDD. C1 (VREF, 1 µF) returns to GNDA.** These are not interchangeable | Correction 1 in the dossier. The VREF cap on the wrong ground was the source design's headline accuracy defect |
| 3 | **R1 (0 Ω) placed directly under U1**, at the AGND (C3) / DGND (E1) bump corner | It is the only connection between the pours and it must be at the point where the two grounds are physically closest, so neither pour carries the other's return current any distance |
| 4 | **C7 (47 nF) immediately between the DRVXC (D5) and DRVSJ (C4) bumps** | It AC-couples the two drive amplifiers; track inductance here directly degrades the current source |
| 5 | **U5 decoupling:** one 100 nF within 1.5 mm of each of the five VDD pins (10, 22, 36, 47, 48). C13 (10 µF) bulk near FL1 | Nordic reference. Pin 47 was unaccounted for in the source design |
| 6 | **C11 and C12 (2.2 µF) adjacent to DCC (46), L3 between DCC and VDD_nRF** | DC/DC output filter |
| 7 | **C22 (10 nF) on the tied DECA (43) / DECRF (33) node, close to both** | These pins must be connected to each other — datasheet requirement |
| 8 | **C43 (100 nF) within 1.5 mm of IC1 pin 8** | Correction 4 — the source design had no decoupling here at all |
| 9 | **C31 (4.7 µF) at U8 OUT pins; C30 (4.7 µF) at U8 BAT pins** | Datasheet requires 4.7–47 µF on both |
| 10 | **C26/C29 at U7 IN, C9/C35 at U7 OUT** — part of the critical loop, §4.3 | |

### Separation

- **U1, R7, R5, R6, C5, C6, C1, C2, C4, J1 and U10 are the analog zone.** Nothing else may be placed inside it.
- **U7, U8, L8 and all their passives are the power zone**, under the shield frame.
- Keep U7's switching loop **at least 15 mm from U1** and from the electrode nets. On a 50 × 44 mm board that is most of the width — it is the reason the zones are arranged as they are.
- **U8's thermal pad at the opposite end of the board from J7 (battery).** See §8.

---

## 6. Keepouts

| Keepout | Extent |
|---|---|
| **Chip antenna AE1** | **No copper on ANY layer** under the antenna or in the manufacturer's specified clearance region around it — this includes L2 ground, L3 power, and both outer pours. Take the exact keepout dimensions from the Würth WE-MCA 74889302450 datasheet; do not estimate them. Also no components, no vias, no silkscreen, and no enclosure metalwork |
| Antenna, ground-plane edge | The antenna must sit at a board edge with the ground plane terminating cleanly at the manufacturer's specified distance |
| **Shield frame footprint** | Würth WE-SHC 26 × 26 mm SMD frame over the power section. Its solder ring needs a continuous, unbroken GNDD pad ring. No tracks may cross under the ring on the top layer, and no components within 0.5 mm inside or outside the ring |
| Under shield frame | Max component height 2.2 mm |
| Pushbutton, slide switch, light pipe, magnetic connector | Mechanical clearance per the enclosure openings; treat as no-component zones on the top layer |
| Battery cavity | The cell sits alongside the board. Nothing may protrude into its 48 × 30 × 10 mm volume, including bottom-side components |
| Electrode connector J1 | Strain-relief clearance for the harness at the board edge |

---

## 7. Ground and power strategy

### Pour assignment

| Layer | GNDA | GNDD | Notes |
|---|---|---|---|
| L1 Top | Fill analog zone | Fill digital/power zone | Split follows the zone boundary in §5 |
| L2 GND | **Solid** under the analog zone | **Solid** under the digital/power zone | The split is a single straight gap. Do not create fingers or islands |
| L3 Power | — | — | Voltage islands only; no ground |
| L4 Bottom | Fill analog zone | Fill digital/power zone + **isolated island for C20** | The C20 island connects to nothing else |

### The split and its single stitch

- **GNDA and GNDD are joined at exactly one point: R1, a 0 Ω 0603 link, placed under U1.** There must be no other connection on any layer. Verify this with a connectivity check before gerber export — an accidental second stitch is invisible in a plot and defeats the entire arrangement.
- The split gap on L2 should be 0.5–1.0 mm. Keep it straight.
- **No track on any layer may cross the split**, except at R1. This includes the patient nets (§4.1), which stay entirely on the GNDA side.

### Return paths

| Net | Return path |
|---|---|
| LX, U7 switching loop | GNDD on L2, directly beneath the loop. This return must be unbroken — no split, no via field, no track crossing under it |
| EL_SENP / EL_SENN | GNDA on L2, solid and unbroken beneath the full length of both |
| ANT and the RF ladder | L2 ground directly beneath, unbroken. C19 returns through pin 32 only; C20 returns to the isolated L4 island only |
| SPI | GNDD on L2. Keep the AFE's SPI on the digital side of the split until it crosses at U1's own pins |
| Charge current, VIN_EXT → U8 → V_BAT | GNDD, wide. This is the highest current path on the board at 400 mA |

### Power distribution

- V_SYS, V2P5, V2P5F, V1P8D as islands on L3. **V1P8A as an island on L3 confined to the analog zone.**
- V1P8A and V1P8D must not overlap on L3 — they are different regulators and overlapping islands couple their noise.
- VDD_nRF is a short island fed through FL1; keep FL1 physically between the V1P8D island and the VDD_nRF island so the ferrite is actually in series and not bypassed by pour.

---

## 8. Thermal

| Part | Dissipation | Requirement |
|---|---|---|
| **U8 BQ24073** | **0.806 W worst case** (charging a depleted cell from a 5 V adapter) | The dominant thermal source by an order of magnitude. Thermal pad to a large GNDD copper area with **at least 9 thermal vias, 0.3 mm, in a 3×3 grid**, connecting to L2 and L4. Target the largest continuous copper area available on the digital side. R_θJA is 44.5 °C/W as datasheet-specified on a 4-layer board — that figure assumes a proper thermal land, so achieving it is a layout obligation, not a given |
| U7 MAX77827 | 0.40 W | Exposed pad to GNDD with 4 thermal vias minimum |
| U10 / U14 ADPL40502 | ~1 mW and ~4 mW | Negligible in Rev B — the second LDO split the load and the drop is only 0.7 V |
| U5 nRF54L15 | 50 mW | Die pad to GNDD with a via array; this is also its electrical ground and is mandatory regardless |
| U1, IC1, U2 | < 5 mW each | No thermal provision needed |

**Worst-case ambient 40 °C.** Sealed IP54 ABS enclosure, thermal resistance approximately 0.83 °C/W, no ventilation. U8 junction reaches 75.9 °C at 0.806 W.

**Placement consequence:** U8 must be at the opposite end of the board from J7 and the battery cavity. The cell is the temperature-sensitive component in the assembly and the NTC (U9) must be mounted against the cell, not near U8 — otherwise it reads the charger's heat and throttles charging for the wrong reason.

---

## 9. DRC rules to encode

Expressible as KiCad custom rules:

```
(version 1)

(rule "patient_clearance"
  (constraint clearance (min 20mil))
  (condition "A.NetClass == 'PATIENT' && B.NetClass != 'PATIENT'"))

(rule "patient_to_switching"
  (constraint clearance (min 40mil))
  (condition "A.NetClass == 'PATIENT' && B.NetName == 'LX'"))

(rule "power_width"
  (constraint track_width (min 20mil))
  (condition "A.NetClass == 'POWER_HIGH' || A.NetClass == 'POWER_LOW'"))

(rule "signal_width"
  (constraint track_width (min 10mil))
  (condition "A.NetClass == 'SIGNAL'"))

(rule "analog_sense_clearance"
  (constraint clearance (min 12mil))
  (condition "A.NetClass == 'ANALOG_SENSE'"))

(rule "rf_no_vias"
  (constraint disallow via)
  (condition "A.NetClass == 'RF'"))

(rule "antenna_keepout"
  (constraint disallow track via pad zone footprint)
  (condition "A.insideArea('ANTENNA_KEEPOUT')"))

(rule "wlp_microvia"
  (constraint hole_size (min 0.1mm) (max 0.15mm))
  (condition "A.insideArea('U1_ESCAPE')"))

(rule "wlp_annular"
  (constraint annular_width (min 0.075mm))
  (condition "A.insideArea('U1_ESCAPE')"))
```

Plain text, because DRC cannot express them — **these must be checked by inspection before gerber export:**

1. **GNDA and GNDD connect at exactly one point, R1.** Run a net-connectivity check with R1 removed and confirm the two pours are fully isolated. This is the single most important manual check on the board.
2. **C19's ground reaches nRF54L15 pin 32 and nothing else**, on the top layer only; pin 32 reaches pin 49 and nothing else.
3. **C20's ground touches only the isolated L4 island.**
4. **No copper on any layer inside the antenna keepout** — check all four layers individually in a plot, not just the DRC report.
5. **No track crosses the L2 ground split** on any layer, except at R1.
6. **The U7 switching loop's L2 return is unbroken** — no via barrels, splits or crossing tracks beneath it.
7. **CAL force and sense connections meet at R7's terminations**, not on a shared track.
8. **R5 and R6 have matched routing geometry** to EL_SENP/EL_SENN.

---

## 10. Fabrication and assembly

### The 0.4 mm pitch WLP — read this before fixing the stackup

**U1 (MAX30009ENA+) is a 25-bump wafer-level package on 0.4 mm pitch in a 2.03 × 2.03 mm body. This single component sets the fabrication class for the entire board.**

Consequences, none of them optional:

- **Via-in-pad is unavoidable.** There is no room to escape a 5×5 bump array on 0.4 mm pitch with dogbone vias. The inner bumps must be escaped through vias placed in the pads themselves.
- **Vias in pad must be filled and capped** (plated over, planarised). An unfilled via in a WLP pad wicks solder away from the joint and produces an open that passes optical inspection and fails electrically.
- **Laser-drilled microvias**, typically 0.1 mm drill in 0.2–0.25 mm pad, L1→L2 and L4→L3. Mechanical drilling will not achieve this pitch.
- This means an **HDI build with at least 1+N+1 construction**, not a standard through-hole 4-layer.
- Minimum trace/space in the escape region drops to approximately **3/3 mil (0.075/0.075 mm)**.

**Action for the PCB stage: obtain the chosen fabricator's HDI capability sheet and confirm minimum microvia drill, minimum annular ring, via-fill process and the resulting minimum trace/space, BEFORE finalising the stackup.** The dielectric thickness between L1 and L2 must suit their laser drilling aspect ratio. Getting this wrong is discovered at fabrication, not at DRC.

Also confirm the land pattern against **Analog Devices Application Note 1891**, which the MAX30009 datasheet references for the WLP footprint. Do not use a generic BGA land pattern generator.

### Process summary

| Item | Specification |
|---|---|
| Fab class | HDI, 1+2+1 or 1+N+1, laser microvias |
| Minimum trace / space | 3/3 mil in the U1 escape region; 5/5 mil elsewhere |
| Minimum microvia | 0.1 mm drill, filled and capped, plated over |
| Minimum through via | 0.3 mm drill / 0.6 mm pad |
| Surface finish | **ENIG.** Required — HASL cannot produce the coplanarity a 0.4 mm WLP needs, and the 0201 passives also need a flat finish |
| Solder mask | Mask-defined pads not permitted on U1; use non-solder-mask-defined |
| Copper | 1 oz outer, 0.5 oz inner |
| Panelisation | Discuss with assembler; 50 × 44 mm suits a multi-up panel with tab routing and mouse bites clear of the antenna edge and the electrode connector |

### Assembly

- **Single-sided assembly on Top wherever possible.** Bottom side carries signals and, if unavoidable, only the smallest passives.
- **Machine placement mandatory** for U1 (WLP), U5 (QFN48), IC1 (GQFN), U7 (FC2QFN) and every 0201 part. The antenna matching network is entirely 0201 and is not hand-placeable.
- **Fit last, by hand:** J1 electrode connector, J7 battery connector, P1 charge connector, J8 slide switch, and the shield frame H1. The shield frame goes on after the power section has been electrically verified — see the dossier build sequence, which brings the power section up before U1, U5 and IC1 are fitted.
- **Do not fit U1, U5, IC1 on the first article** until the power section is verified at 2.5 V, 1.8 V(A) and 1.8 V(D). The 1.8 V logic domain correction (dossier correction 10) means an incorrect rail will overstress IC1.

---

## 11. Do not autoroute

The following must be routed **by hand**, in this order:

| Net(s) | Reason |
|---|---|
| **ANT, RF_A, RF_B, RF_ANT** | 50 Ω controlled impedance, no vias, and the geometry must follow Nordic's reference layout. An autorouter will via it to another layer and destroy the match |
| **C19 and C20 ground connections** | Their whole purpose is a deliberately abnormal return path. Any router will connect them to the nearest ground and silently remove the harmonic filtering |
| **EL_SENP, EL_SENN** | Matched geometry, minimum capacitance, and confinement to the GNDA region. No router understands "keep the parasitic capacitance low" |
| **EL_DRVP, EL_DRVN** | Patient-net clearance and zone confinement |
| **CAL_F, CAL_S** | Four-wire Kelvin. A router will merge force and sense at the first opportunity, which silently destroys the accuracy reference |
| **LX, and the C29/C9/L8 loop** | Loop area is the constraint, and loop area is not something a router optimises |
| **OUTS** | Must reach the far side of C9, not the OUT pin. A router will treat it as the same net and connect it anywhere |
| **U1's entire escape** | Via-in-pad, two ground domains 0.4 mm apart, and the R1 stitch. Hand-route the whole WLP fanout |
| **VBAT_SENSE** | C36 must be at the MCU pin |
| **U8 thermal pad and its via array** | Thermal, not electrical, and no router places thermal vias |

Everything else — SPI, status lines, button, LED, SWD — may be autorouted, **after** the above are locked.

---

## 12. Verify before gerber export

Inherited from the schematic's unverified list. **Items V1–V5 are blockers on committing footprints.**

| Ref | Item | Status | Action |
|---|---|---|---|
| ~~V1~~ | ~~MAX77827 pins 7 and 12~~ | **CLOSED** | Datasheet Pin Description table confirms pin 7 = IN (2nd pad, w/ pin 6), pin 12 = OUT (2nd pad, w/ pin 11). Tie in pairs in the footprint |
| V2 | MAX77827 BIAS pin treatment | UNVERIFIED | C34 1 µF to PGND is provisional |
| V3 | MAX77827 FPWM polarity | UNVERIFIED | R19 fitted as pull-down assuming high = forced PWM. If inverted, the footprint changes to a pull-up to V2P5 |
| V4 | MAX77827 A vs B suffix | CHECK | KiCad models the A part; the BOM specifies B. Confirm identical pinout |
| ~~V5~~ | ~~ADPL40502 6-lead LFCSP pin numbering~~ | **CLOSED** | Datasheet Table 5: 1=VOUT, 2=NC, 3=GND, 4=EN, 5=NC, 6=VIN, EPAD=GND (must be grounded). Two instances (U10, U14) |
| V6 | SN74LVC1G14 thresholds at 1.8 V | UNVERIFIED | Affects R10/R11/R12/C25 *values*, not footprints. Can be closed after layout |
| **V7** | **J2 SWD header pin numbering** | **UNVERIFIED** | Confirm Würth 62201021121 against the Arm Cortex Debug 10-pin convention, including both grounds and the key |
| **V8** | **Antenna ladder node order** | **INFERRED** | Take node order AND physical geometry from Nordic's reference design files. RF performance depends on it |
| V9 | nRF54L15 absolute maximum ratings | NOT PUBLISHED | Datasheet v0.7 lists them as TBD. Obtain the production specification |
| V10 | CY15V108QI 8-GQFN is marked **NRND** | SOURCING | Pinout verified from the family datasheet. For anything beyond prototypes, move to the SOIC or UFLGA variant — which changes the footprint |
| V11 | MAX30009 input capacitance at EL2B/EL3B | ASSUMED 10 pF | Sets the 250 kHz sweep ceiling. Minimising track capacitance on the sense pair is the layout's contribution |
| V12 | EL2A/EL2B and EL3A/EL3B selection for BIS | CHECK | Confirm the register setting matches the B pins being populated |
| V13 | BQ24073 battery drain current | ASSUMED 15 µA | Affects the runtime figure, not the layout |
| V14 | LED1 part selection | OPEN | Red, V_F ≤ 2.0 V at 2 mA, 0603. Pick a specific part; confirm the footprint |
| V15 | IEC 60601-1 patient auxiliary current limits | NOT READ | Must be read before any human use |
| V16 | Crystal load capacitance vs internal caps | CHECK | Note ABM10 is a 2520 package where Nordic's reference shows 2016 — **confirm the footprint** |

### Layout-specific checks

- [ ] Fabricator HDI capability confirmed and the stackup built to their laser-drill aspect ratio (§10)
- [ ] U1 land pattern taken from ADI Application Note 1891, not a generic generator
- [ ] Würth WE-MCA antenna keepout dimensions taken from the datasheet, not estimated
- [ ] Würth WE-SHC 26 × 26 mm frame footprint and its solder ring confirmed
- [ ] CamdenBoss BIM2000/10 internal rib and boss positions checked against the 44 mm board width — only 1 mm clearance per side (§1)
- [ ] Board outline vs LP103048JU cell volume confirmed in 3D
- [ ] All eight manual checks in §9 performed on plots, layer by layer

---

## 13. Open questions

Resolve or escalate; do not assume.

1. ~~MAX77827 pins 7 and 12 (V1).~~ **Closed** — datasheet obtained and confirmed, see status block above.
2. **Board and cell arrangement.** This brief assumes the board and cell sit **side by side** in the 71 × 46 × 23 mm cavity, to keep the cell away from U8's thermal pad. If the mechanical design instead stacks them, the thermal analysis in §8 must be redone and U8's placement reconsidered.
3. **Inverted-U mounting.** The source design mounts the board via two auxiliary PCBs soldered to edge pads. The pad geometry, spacing and mechanical load path are not specified anywhere in the source material. Confirm with mechanical before committing edge pad positions — they consume board edge that the antenna and connectors also want.
4. **Antenna edge selection.** The antenna needs a board edge and a clear enclosure region. The electrode harness needs the opposite edge from the charge connector. With four features and four edges on a 50 × 44 mm board, confirm the assignment against the enclosure's actual opening positions before placement.
5. **8-GQFN is NRND (V10).** Confirm whether this build is prototype-only. If it is heading for any volume, switch to the SOIC or UFLGA F-RAM variant now, while the footprint is still cheap to change.
6. **Panelisation and the antenna edge.** Tab or mouse-bite positions must not intrude into the antenna keepout or leave copper burrs at that edge. Agree the panel with the assembler before finalising the outline.
7. **Shield frame vs. rework.** The Würth frame covers U7 and U8. Once fitted, those parts cannot be probed. Confirm the build sequence allows full power-section verification before the frame goes on — the dossier build sequence assumes this.
