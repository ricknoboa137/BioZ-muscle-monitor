# Routing order — BioZ Muscle Monitor rev B

**State: 62.0 x 44.0 mm, shielded, placed, poured and hand-routed through all
of section 11 that four layers permit, at 0 DRC errors.** 113 unconnected
items remain: five trapped WLP bumps (see below) and all of categories 3-4 — that is the full ratsnest. The critical-net
geometry is specified below and scripted in `scripts/route_critical.py`, but
that script does not yet produce DRC-clean copper (see "status" at the end).
Route in the order given. Nothing in categories 1 and 2 goes to a router.

---

## Category 1 — nets that cannot move. Hand route first, then lock.

Route each of these, then set it read-only in KiCad before touching anything
else. Locking is not optional: a later autoroute pass will rip up anything
that is not locked.

### 1.1 ANT, RF_A, RF_B, RF_ANT

| Rule | Value | Source |
|---|---|---|
| Layer | **F.Cu only**, no exceptions | brief 4.4 |
| Vias | **none anywhere in the chain** | brief 4.4 |
| Impedance | 50 Ω single-ended, referenced to L2 | brief 2 |
| Width | **OPEN — not set.** The net class carries a 0.20 mm placeholder | brief 2: take it from the fabricator's 50 Ω stackup |
| Clearance | 3 × trace width to any other copper (0.60 mm at the placeholder) | brief 3 |
| Geometry | Straight line on **X = 31.30 mm**, which is AE1's feed-pad X | — |

Order along the line, top to bottom: AE1 pad 1 (31.30, 2.40) → L6 → L5 → L4 →
U5 pad 31. Shunt caps join the line at their own node: C23 at the RF_ANT node,
C21 at RF_B, C20 at RF_A, C19 at ANT.

The RF feed line is **the only copper permitted inside the antenna keepout**,
and it is the only exception in the `antenna_keepout` DRC rule.

### 1.2 C19 and C20 grounds

These two returns are deliberately abnormal. Any router will connect them to
the nearest ground and silently delete the harmonic filtering.

- **C19 pad 2 (net VSS_PA) → U5 pin 32 only, on F.Cu.** Pin 32 then reaches
  pin 49 (the die pad) and nothing else. The connection is modelled with the
  net tie NT1 at (34.6, 12.4) so DRC will accept it; route pin 32 → NT1 pad 1
  and NT1 pad 2 → the die pad, both short, both on F.Cu.
  VSS_PA must touch the GNDD pour nowhere else on any layer.
- **C20 pad 2 (net GND_C20) → the isolated L4 island only.** One via down at
  (29.05, 9.80), then a stub to the island at X 28.6–30.9, Y 8.8–10.8.
  The island connects to nothing else — that is its entire purpose.

### 1.3 EL_SENP, EL_SENN

| Rule | Value |
|---|---|
| Net class | PATIENT — 0.30 mm (12 mil) wide, 0.51 mm (20 mil) clearance |
| Layer | F.Cu only, over unbroken GNDA on L2 |
| Vias | **zero on each**, and the counts must be equal |
| Length match | within 1 mm of each other |
| Geometry | mirrored about Y = 26.0, the U1 centre line |
| Adjacency | not parallel to any other track anywhere |
| Zone | entirely X < 20.0; must not cross the split or pass over GNDD on any layer |

Path: U1 bump A3 → R5 pad 1, R5 pad 2 → J1 pin 3 (EL_SENP);
U1 bump B3 → R6 pad 1, R6 pad 2 → J1 pin 2 (EL_SENN).
R5 is at (15.0, 22.0) and R6 at (15.0, 30.0) — symmetric about Y = 26.0, so
mirroring the path gives the match by construction.

Keep both away from L8, the whole power zone, the antenna and IC1.

### 1.4 EL_DRVP, EL_DRVN

Same net class and zone confinement. 40 mil minimum from LX (the DRC rule
`patient_to_switching` enforces it; the 15.8 mm zone separation makes it
trivially satisfied). Path: U1 A1 → C5 → J1 pin 4, U1 B1 → C6 → J1 pin 1.

**Watch this:** J1's pin order runs *opposite* to the component order down the
analog zone. Going down the board the parts are C5 (E1), R5 (E3), R6 (E2),
C6 (E4); going down J1 the pins are E4, E2, E3, E1. The bundle therefore has
to cross. Do it on **L4 for the drive pair only** — EL_DRVP/EL_DRVN may take
vias, the sense pair may not. Do not "fix" this by rotating J1: the pin
assignment is the electrode harness wiring and belongs to the schematic.

### 1.5 CAL_F, CAL_S

Four-wire Kelvin. R7 is at (16.0, 26.0), rotated 90°.

- U1 A4 → R7 pad 1 and U1 A5 → R7 pad 1 as **two separate tracks**.
- U1 B4 → R7 pad 2 and U1 B5 → R7 pad 2 as **two separate tracks**.
- Force and sense meet **at the resistor's own terminations**, never earlier.
  If you find yourself drawing one track from a merged pair, you have
  destroyed the absolute-accuracy reference.

### 1.6 LX and the C29 / L8 / C9 loop

The highest-priority loop on the board. 1.6 A peak at 2.5 MHz, 15.8 mm from a
6.4 mV measurement.

Loop, in order: C29 pad 1 → U7 pad 6 (IN) → U7 pad 8 (LX1) → L8 pad 1 →
L8 pad 2 → U7 pad 10 (LX2) → U7 pad 11 (OUT) → C9 pad 1 → C9 pad 2 → PGND.

- All on F.Cu, 0.51 mm (20 mil) minimum.
- **Keep the LX copper area as small as current allows** — it is the high
  dv/dt node and area on it is a capacitive antenna.
- Both capacitor returns go into the **L2 GNDD plane directly beneath**, by a
  0.3 mm via immediately beside each capacitor's ground pad. That is the
  shortest return there is.
- **The L2 GNDD plane under X 30–41, Y 22–32 must stay unbroken.** No via
  barrels for other nets, no split, no track crossing it on L2.

### 1.7 OUTS

U7 pad 13. Route as a **thin** track (0.15 mm) to the **far terminal of C9**,
not to the OUT pin and not to C9's near pad. It exists to regulate out the IR
drop in the output track; connecting it to OUT makes it useless.

### 1.8 U1's entire WLP escape

25 bumps, 5 × 5 on 0.40 mm pitch, 0.25 mm NSMD pads, 0.15 mm pad-to-pad gap.

- Rows A, B, C escape **west, north and south** into GNDA territory.
  Rows D and E escape **east** into GNDD territory. That is what puts the
  split between rows C and D.
- Trace/space in the escape region is **0.075 mm / 0.075 mm (3/3 mil)**.
  The `wlp_*` DRC rules apply inside the `U1_ESCAPE` rule area
  (18.4–21.2, 24.6–27.4).
- A bump in row B or C escaping west must **step half a pitch (0.2 mm)
  perpendicular first**, then run west through the 0.15 mm gap between the
  row-A bumps. Going straight west from B1 runs over A1.
- **Centre bump C3 (AGND) takes a 0.1 mm laser microvia in pad**, filled and
  capped, straight down to the L2 plane. It is the only genuinely trapped
  bump, and it is a ground bump, so the plane is the right destination.
- Fan the rest out to a ring at radius ≈ 2.6 mm from the U1 centre, outside
  both the `U1_ESCAPE` area and the bottom-side decoupling cluster, and drop
  0.3 mm through vias there.
- The split channel **necks from 0.8 mm to 0.2 mm between Y 24.4 and 27.6**
  because a 0.8 mm plane gap will not fit between bump rows C and D, which are
  0.4 mm apart. 0.2 mm is a routinely manufacturable plane gap.

### 1.9 VBAT_SENSE

U5 pin 5 → C36 → the R2/R3 divider. C36 is 1.4 mm from the pin and must stay
between the pin and the divider, not on the divider side.

### 1.10 U8's thermal via array

3 × 3 of 0.3 mm vias on 0.55 mm pitch in the exposed pad, tied to GNDD on L2
and L4. Thermal, not electrical — no router will place these.
Same treatment for U5's die pad (3 × 3, 1.3 mm pitch) and for U10 / U14's
exposed pads (2 vias each, into GNDA and GNDD respectively).

---

## Category 2 — power and ground distribution. Hand route.

1. **V_SYS**: P1 → U8 pin 13, U8 pins 10/11 → J8 → U7 pin 6. 0.51 mm minimum,
   400 mA charge path. Widen beyond 20 mil wherever there is room.
2. **V_BAT**: U8 pins 2/3 → J7. 0.51 mm.
3. **V2P5 → LC filter (R16, L7, C32, C33) → V2P5F**. Keep FL1 physically in
   series between the V1P8D island and the VDD_nRF island so the ferrite is
   not bypassed by pour.
4. **V1P8A**: U10 → U1 bumps C1 and D1, on the L3 island confined to the
   analog zone. V1P8A and V1P8D must not overlap on L3.
5. **V1P8D**: U14 → IC1, U2, J2 pin 1, and the pull-ups.
6. **The documented split crossings.** Two, and only two, tracks cross the
   GNDA/GNDD boundary besides R1:
   - **V2P5F into U10's VIN.** U10 is in the analog zone and its input comes
     from the digital zone; there is no way around it. Cross **within 2 mm of
     R1**, on L1, so the displacement return has a defined short path.
   - **C7's DRVXC leg.** Bump D5 (DRVXC) is an analog node that sits in the
     digital bump row. C7 is on the bottom layer bridging D5 and C4.
   Both are listed in the pre-gerber checklist as accepted exceptions.
   Nothing else crosses, on any layer.

---

## Category 3 and 4 — everything else. Autoroute permitted, after locking.

SPI_SCK, SPI_SDO, SPI_SDI, AFE_CS, MEM_CS, MEM_WP, AFE_INT, AFE_PWR_EN,
FPWM_CTL, nPGOOD, nCHG, LED_K, LED_K_R, BTN_N, BTN_RC, BTN_PU, BTN_SW, SW_EN,
SWDIO, SWDCLK, SWO, nRESET, POK, TS_NTC, ILIM, ISET, SEL, BIAS, XL1, XL2,
XC1, XC2, DECA_RF, DECD, DCC.

One extra constraint the router will not know: **route SPI_SCK away from the
electrode nets.** It is the only fast-edged digital signal that goes near the
analog section. Give it a path along the top of the digital zone, and check it
by eye afterwards.

Route via Specctra DSN → Freerouting → SES:

```
export DSN  ->  patch In1.Cu and In2.Cu to "type power"  ->  freerouting
            ->  import SES  ->  DRC + render
```

Traps that have already cost runs on this pipeline:

- `kicad-cli` cannot export DSN or import SES. Use KiCad's **bundled** Python
  (`C:\Program Files\KiCad\10.0\bin\python.exe`) with
  `pcbnew.ExportSpecctraDSN` / `pcbnew.ImportSpecctraSES`.
- **Patch the plane layers to `type power` in the DSN before routing.** KiCad
  exports every copper layer as `type signal`, planes included, and
  Freerouting will run signal tracks straight through the ground and power
  planes. Refuse to route if the patch does not apply, and **count segments
  per layer afterwards** — this failure passes DRC looking clean.
- Freerouting 2.2.4 needs **Java 25**; the jar is class file v69 and a 21 JRE
  throws `UnsupportedClassVersionError`.
- Invoke headless: `--gui.enabled=false -de <dsn> -do <ses> -mp <passes>`.
- Specctra carries **no length or skew constraint**, so nothing matched can be
  autorouted. EL_SENP/EL_SENN are in category 1 for exactly this reason.

---

## Manual checks that DRC cannot express

Each of these is a rule with a physical reason that KiCad's rule language
cannot state. They are repeated in `pre-gerber-checklist.md`.

1. **GNDA and GNDD connect at exactly one point, R1.**
   Automated in `scripts/verify_board.py` — currently PASS.
2. **C19's ground reaches U5 pin 32 and nothing else**, on F.Cu only; pin 32
   reaches pin 49 and nothing else.
3. **C20's ground touches only the isolated L4 island.**
4. **No copper on any layer inside the antenna keepout.**
   Automated in `scripts/verify_board.py`, layer by layer — currently PASS on
   all four layers.
5. **No track crosses the L2 split** except at R1 and the two documented
   crossings above.
6. **The U7 switching loop's L2 return is unbroken** beneath the loop.
7. **CAL force and sense meet at R7's terminations**, not on a shared track.
8. **R5 and R6 have matched routing geometry** to EL_SENP/EL_SENN.
9. **RF trace width has been set from the fabricator's 50 Ω stackup** and is no
   longer the 0.20 mm placeholder.

---

## Status of `scripts/route_critical.py`

DONE and DRC-clean: the RF chain, C19 and C20's special grounds, the
LX/C29/L8/C9 loop, OUTS to the far side of C9, VBAT_SENSE at the MCU pin, the
U8 3x3 and U5 3x3 via arrays, and the U10/U14 exposed-pad stitching.

NOT DONE, and set behind `ESCAPE_BY_SCRIPT = False`: U1's WLP escape, the
patient bundle, and the CAL Kelvin. The geometry below is correct and was
worked out in full - it is the drawing of it by script that does not converge.

### Superseded note

The script lays down every category-1 net as explicit track geometry and is
correct in intent, ordering and layer assignment. It is **not yet DRC clean**:
the last run produced 215 errors, principally tracks crossing where two
polylines share a corridor, and escape traces passing over neighbouring WLP
bumps. Scripted polylines are the wrong tool for this — the escape and the
patient bundle need an interactive router with a push-and-shove engine.

Use the script as the specification of what to draw, and draw it in pcbnew.
The board as shipped has **no tracks**, so nothing has to be ripped up first.


---

## MANUAL CHECKS — constraints that cannot be expressed as DRC rules

These are not optional. Each one exists because the constraint is real but
KiCad's DRC expression language cannot state it. Work through them before
generating fabrication output, and record the result in
`pre-gerber-checklist.md`.

### MC-1. Pad-to-pad clearance *inside* a single footprint

**Why this is a manual check.** The rule that used to cover it,
`pads_inside_one_package`, had the condition `A.Footprint == B.Footprint`.
There is no `A.Footprint` property in KiCad's DRC expression language and no
cross-reference form of any kind — the only footprint predicate is
`A.memberOfFootprint('REF')`, which requires a **literal** reference designator,
so a single generic rule covering "any two pads of the same part" cannot be
written. Worse, the malformed rule did not merely fail: **it silently voided
the entire `.kicad_dru`, all 29 rules, for the whole PCB stage** (checkpoint
entries 35–37). It has been deleted, not commented out.

**What covers it now, and what it does not cover.** Three overlapping
mechanisms, verified in session 11 to leave zero package-internal pad-pair
violations between them:

1. Per-footprint rules in the `.kicad_dru` for every fine-pitch package on the
   board — `wlp_internal_U1` (0.14), `qfn48_internal_U5` (0.14),
   `fc2qfn_internal_U7` (0.15), `qfn16_internal_U8` (0.15),
   `lfcsp_internal_U10` / `lfcsp_internal_U14` (0.15), `nettie_NT1` (0.0).
2. The footprint-level local clearance override of **0.10 mm** that
   `scripts/build_board.py` applies to every placed footprint — confirmed
   present on **92 of 92** footprints in the live `.kicad_pcb`.
3. `general_clearance` at 0.127 mm, which happens to sit below the pad gap of
   every ordinary passive on this board (an 0201 gap is 0.18 mm).

**Mechanism 3 is a coincidence of this board's part mix, not a guarantee.**

**The check.** Whenever a part is added, changed or re-footprinted, confirm its
minimum pad-to-pad gap from the manufacturer's land-pattern drawing, and:

- if that gap is **below 0.127 mm**, add a `<pkg>_internal_<REF>` rule for it,
  placed at the END of the `.kicad_dru` (last matching rule wins);
- if it is at or above 0.127 mm, no rule is needed — record the figure and the
  datasheet page in the checklist and move on.

**After ANY edit to the `.kicad_dru`, run `scripts/dru_control_test.sh`.** It
plants four deliberately illegal items and requires four named rules to fire.
It is the only way to detect the silent-void failure mode, which produces a
clean-looking "Found 0 violations" from a file that is not loaded at all.

### MC-2. Refill the zones after any rules change

KiCad's zone filler honours custom DRC rules, so stored pour fills computed
under a different (or void) rules file are silently wrong. This is not
cosmetic: it accounted for **18 of the 22** `patient_clearance` violations,
every one reading exactly `actual 0.5005 mm` against the GNDA pour, and a
single refill closed all 18. Run `scripts/refill_zones.py` — it carries the
pour-severance guard and refuses to save if the unconnected count rises.

### MC-3. Clearance violation counts are a LOWER BOUND, not a work list

**kicad-cli silently under-reports overlapping clearance violations, and which
ones it drops varies between identical runs.** This is not noise and not a
board problem — root-caused in checkpoint entry 41. The geometry is identical
every run (same measured `actual` distances), the board bytes are identical,
and width / hole-size / annular-width / `disallow` results are 100 % stable.
Only clearance rules move.

Proof: on the ANT-vs-VSS_PA cluster, direct geometry finds **five** genuine
`rf_clearance` violations (edge gaps 0.2250, 0.2250, 0.2550, 0.2550, 0.4650
against a 0.600 floor); kicad-cli reports two to four of them, a different
subset each run. Across the whole RF class the true figure is **16** while DRC
reports 13-15.

**Rules that follow, and they are not optional:**

1. Never quote a single DRC run's total as progress, and never quote a union of
   runs as exact. Report per-category state instead.
2. **Zero is trustworthy; a non-zero count is not.** There is nothing to race
   over in an empty category, so "reports zero on every one of N runs" is a
   sound closure test. That is how every category closed in session 11 was
   signed off.
3. **Take the work list for any clearance category from
   `scripts/true_clearance.py`, not from the DRC JSON.** It enumerates every
   same-layer copper pair below the floor directly from the geometry, is
   verified deterministic, and cross-validates against DRC (it returns 0 for
   PATIENT, matching DRC's 0).
   - **`--exclude-area U1_ESCAPE` is mandatory for PATIENT and RF.** The
     `.kicad_dru` resolves last-matching-rule-wins and `wlp_clearance` (0.075)
     sits after `patient_clearance`, so inside the WLP escape the binding floor
     is 0.075. Omitting the flag reports 25 phantom PATIENT violations on a
     genuinely clean board.
   - **It walks tracks and vias only** — it does not compare against zone pours
     or pads. Use it alongside the DRC JSON, not instead of it.
4. `scripts/drc_union.sh <runs>` remains useful for a whole-board sweep; read
   its number as "at least this many". `scripts/diag_drc_variance.py` splits a
   set of runs into the stable core and the variable tail.

Tested and rejected as a fix: `DRC.report_all_track_errors` in
`%APPDATA%/kicad/10.0/pcbnew.json` (note it is nested under `"DRC"`, so setting
it at top level does nothing). Flipping it to `true` did not restore
determinism. It has been left at its original `false`.
