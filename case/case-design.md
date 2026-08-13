# BioZ Muscle Monitor — enclosure design

Two-part 3D-printed enclosure, parametric, generated from
`cad/case-base.py` and `cad/case-lid.py`.

**The `.py` files are the source. The `.SLDPRT` files are build artifacts.**
Change a number in the constants block and re-run; hand edits made in
SOLIDWORKS are lost on the next run. If you want to take a part over by hand
from some point, that is fine — but the script stops being authoritative from
then on, and you should say so here.

**Nothing here has been printed.** Both parts are modelled, measured and
exported. Fit against a real board and a real cell is unproven until one exists.

---

## 1. Headline result

| | |
|---|---|
| External | **77.0 × 81.5 × 24.0 mm** |
| Base shell | 77.0 × 81.5 × 14.0 mm |
| Lid | 77.0 × 81.5 × 11.0 mm (1.0 mm of that is the register lip, internal) |
| Internal cavity | 64.0 × 77.5 × 20.0 mm |
| Wall | 6.5 mm on the X ends (they carry the screws), 2.0 mm on the Y sides |
| Floor / lid plate | 2.0 mm each |
| Parting line | assembled z = 14.0 mm |
| Retention | 4 × M2 self-tapping, counterbored flush in the lid |
| Support material | base **0.000 mm²**, lid **32.007 mm²** (counterbores only) |

Reference for comparison: the source thesis specified a CamdenBoss
BIM2000/10-BLK/BLK, 75 × 50 × 27 mm external. This design is 6.5 mm longer in
one axis, 31.5 mm longer in the other, and 3.0 mm thinner. **Section 3 explains
why that growth is unavoidable and is not a design choice.**

---

## 2. Intake set

Every number the geometry depends on, with where it came from. The **assumed,
unverified** rows are the ones to close.

| # | Item | Value | Source |
|---|---|---|---|
| 1 | Board outline | 62.0 × 44.0 mm | `pcb/CHECKPOINT.md`, board facts — settled |
| 1 | Board thickness | 1.0 mm | `pcb-brief.md` §1 |
| 2 | Max component height, **top** | 3.0 mm general, 2.2 mm under the shield frame | `pcb-brief.md` §1 |
| 2 | Max component height, **bottom** | 1.0 mm | `pcb-brief.md` §1 |
| 2 | Light pipe height above board | 12.7 mm (0.500 in), Ø3.0 face | BIVAR VLP-500-R/F, distributor listings (Newark/RS/Arrow). **Datasheet PDF not obtained** |
| 3 | Mounting | No screws, no standoffs. Two aux PCBs on MP1/MP2 edge pads form an inverted-U | `pcb-brief.md` §1, thesis §3.8 |
| 3 | MP1 / MP2 pad column x | board x = 1.1 / 60.8 | read from `pcb/BioZ-Muscle-Monitor.kicad_pcb` |
| 3 | Aux panel thickness | 1.0 mm FR4 | **ASSUMED, UNVERIFIED.** `pcb-brief.md` open question 3 states the source material never specifies the pad geometry or load path |
| 4 | Electrode connector J1 | board (4.6, 23.0), exits −X | `.kicad_pcb` |
| 4 | Charge connector P1 | board (26.0, 38.84) — **panel part is wired, not board-edge** | `.kicad_pcb` + `pcb-brief.md` §1 |
| 4 | Slide switch feed J8 | board (51.5, 38.84) | `.kicad_pcb` |
| 4 | LED1 (light pipe axis) | board (21.5, 8.4) | `.kicad_pcb` |
| 4 | Charge connector cutout | MULTICOMP MP009329 — **dimensions UNVERIFIED**, opening is a provisional 10 mm slot | — |
| 4 | Slide switch cutout | G-107-SI-0511 — **dimensions UNVERIFIED**, provisional 8 mm slot | — |
| 5 | Cell | Jauch LP103048JU, 48 × 30 × 10 mm | `pcb-brief.md` §1 |
| 5 | Pushbutton | SCHURTER 52-03-80, "18 mm", IP65, panel-mounted in the lid | thesis §3.3.1.5. **Cutout diameter ASSUMED to be the 18 mm figure; behind-panel depth UNVERIFIED and not findable at SCHURTER or any distributor** |
| 6 | How it is worn / mounted | **NOT SPECIFIED** — no strap lugs modelled. See §9 |
| 7 | Environment | Worn on the biceps; source design was IP54. This print is **not sealed** | thesis §1, §3.3.1.5 |
| 8 | Printer / process | **ASSUMED** FDM, 0.4 mm nozzle. Material not specified | — |

---

## 3. The fit arithmetic — the original calculation no longer holds

`pcb-brief.md` §1 concluded the board and cell fit side by side in the
CamdenBoss 71 × 46 × 23 mm cavity. **That was computed for the original
50 × 44 mm board and it is now false.** Re-derived against the current 62 × 44:

```
cavity floor area   71 × 46  =  3266 mm²
board footprint     62 × 44  =  2728 mm²
cell footprint      48 × 30  =  1440 mm²
                    board + cell = 4168 mm²   >   3266 mm²
```

Side by side does not fit **on area alone**, before a single millimetre of
clearance is allowed. The two axis-by-axis checks agree:

- along the 71 mm length: 71 − 62 = **9 mm** left; the cell needs 48 or 30.
- across the 46 mm width: 46 − 44 = **2 mm** left; the cell needs 30 or 48.

So one of two things had to give: the side-by-side arrangement, or the
enclosure size. **The arrangement was kept and the enclosure was grown**, because
the reason for side-by-side is thermal (keep the cell off the BQ24073's thermal
pad) and that reason is still valid. We are printing this case, not buying the
CamdenBoss, so its dimensions are a reference and not a constraint.

### Which side the cell goes on

Four candidate edges, three of them rejected on physical grounds:

| Edge | Verdict |
|---|---|
| −Y | **Rejected.** This is the chip-antenna edge (AE1 at board y = 2.4, keepout y 0–6.82 mm). A Li-po pouch's metal foil against a 2.4 GHz chip antenna detunes it. |
| −X | **Rejected.** Electrode harness exit (J1 exits −X). Patient-connected side; the cell must not share it. |
| +X | **Rejected.** This is the charger end — U8 sits at board (54, 15). Putting the cell here defeats the entire purpose of the side-by-side arrangement. |
| **+Y** | **Chosen.** J7, the battery connector, is at board (41.5, 38.84) facing +Y, so the leads are short. |

Measured consequences of that choice:

- cell nearest face to **U8 (charger)**: **31.8 mm**
- cell nearest face to **AE1 (antenna)**: **44.4 mm**

Both are large. The thermal and RF intents of the brief are satisfied by
geometry rather than by assertion.

### Resulting cavity

Minimum side-by-side cavity is 62 × 75 mm before clearances. Built cavity is
**64.0 × 77.5 mm**, which is that plus board clearance, the 2.0 mm bay divider
and the cell clearance.

---

## 4. The tight Y tolerance — what it actually is, and what the case did about it

The 0.40 mm figure flagged in the brief is **internal to the PCB**:

```
antenna keepout strip    6.82 mm
shield frame footprint  26.50 mm
connector row           10.28 mm
                        ------- 
                        43.60 mm  of the board's 44.00 mm width
                        = 0.40 mm of slack
```

**No enclosure can relieve this.** It is a budget between three features on the
board, all of which are already committed. The enclosure's only obligation is to
**steal none of it**, and this one steals none:

- The rails are **entirely beneath the board** — their top face *is* the board's
  underside plane (z = 8.3). They constrain the board in X. They do not touch it
  in Y at all.
- **No boss, rib, standoff or screw column enters the board's 62 × 44 plan area
  at board level.** Verified, not asserted: the board slab envelope is clear over
  2520 sample points and the 3.0 mm top-side component envelope is clear over
  3780, measured against the exported meshes.
- Board-to-wall clearance in Y is **0.30 mm at the antenna edge** and **0.30 mm
  to the battery divider**.
- The only case feature anywhere over the board is the lid's −Y register lip,
  which overhangs the board's −Y edge by 1.1 mm in plan but sits at z 13.0–14.0
  — **0.7 mm above the top-side component envelope.**

**Verdict: the 0.40 mm is unchanged and remains the tightest dimension in the
whole design, but it is a PCB-internal constraint and the enclosure contributes
zero to it.**

Separately: the 0.30 mm/side board-to-wall clearance in Y **meets** the 0.3 mm
per side pocket target but has no margin beyond it. FR-4 routing tolerance is
typically ±0.15 mm and printed wall position is comparable, so a board at the
high limit in a case at the low limit is a zero-clearance fit. **Check this on
the first article before printing a batch.**

---

## 5. Clearances, and the reason for each

| Interface | Value | Reason |
|---|---|---|
| Board to X cavity walls | 1.00 mm/side | Not print clearance — this is what makes room for the 1.4 mm outboard rail rib. See §6. |
| Board to Y cavity walls | 0.30 mm/side | PCB pocket clearance: board outline tolerance + print tolerance. The minimum that is defensible. |
| Aux panel to rail slot | 0.20 mm/face (1.4 mm slot for 1.0 mm FR4) | Mating part clearance; the panel must slide, not press. |
| Cell to bay ribs, X | 0.50 mm/side | Pouch cells swell in service; this is deliberately looser than a rigid part would get. |
| Cell in bay, Y | 0.45 mm/side | Same, cell centred so the slack is shared rather than piling up at one end. |
| Lid register lip to base cavity | 0.20 mm/face | Mating part clearance. |
| Screw pilot | Ø1.6 for M2 self-tapping | Standard pilot; 2.45 mm of wall remains each side. |
| Screw clearance in lid | Ø2.4 | M2 shank + 0.4 mm on diameter — holes print undersize. |
| Light pipe hole | Ø3.4 for a Ø3.0 pipe | +0.4 mm on diameter, loose fit. |
| Pushbutton cutout | Ø18.6 for an "18 mm" part | +0.6 mm, deliberately generous — a panel nut has to pass and the cutout figure is itself unverified. |

---

## 6. The inverted-U mount

The board carries no screws and no standoffs. Two auxiliary PCBs solder to the
MP1/MP2 edge-pad columns and hang down as legs, and the resulting inverted-U
drops into rails in the base.

Each rail is **rib / slot / rib**, all three rising from the cavity floor:

| | −X end | +X end |
|---|---|---|
| Outboard rib | x 6.5–7.9 (1.4 mm) | x 69.0–70.5 (1.5 mm) |
| **Slot** | **x 7.90–9.30** | **x 67.60–69.00** |
| Inboard rib | x 9.3–12.3 (3.0 mm) | x 64.6–67.6 (3.0 mm) |

Rib tops at z = 8.3, which is the board's underside. Slot depth 6.3 mm, so the
aux panel legs are 6.3 mm tall. The board lands on the four rib tops; the legs
in the slots locate it laterally; the lid bears down from above.

**This is why the board gets 1.0 mm of X clearance and only 0.3 mm of Y.** MP1
sits 1.1 mm in from the board edge, so the slot has to be 1.1 mm inboard too,
and the outboard rib has to fit in what is left. At 0.3 mm of board clearance
that rib would be 0.7 mm wide — below the 0.8 mm minimum feature, and the slicer
would silently drop it. 1.0 mm of clearance makes it 1.4 mm and printable.

### Action back to the PCB stage

**No bottom-side components within board x < 5.0 mm or x > 57.0 mm.** That is
where the rail ribs contact the board underside. The brief's 1.0 mm bottom-side
height allowance does not apply in those two strips — the allowance there is
zero.

---

## 7. Openings, and why the parting line is where it is

The parting line sits at assembled **z = 14.0 mm**, which is deliberately
**below every wall opening**:

| Opening | Wall | Position | Assembled z | Split |
|---|---|---|---|---|
| Electrode harness (J1) | −X | y 22.3–28.3 (6 mm) | 10.0 – 16.0 | base 10–14, lid 14–16 |
| Magnetic charge connector | +X | y 59.0–69.0 (10 mm) | 11.0 – 19.0 | base 11–14, lid 14–19 |
| Slide switch | +Y | x 55.0–63.0 (8 mm) | 13.0 – 19.0 | base 13–14, lid 14–19 |
| Light pipe | lid plate | Ø3.4 at (29.0, 10.7) | through the plate | — |
| Pushbutton | lid plate | Ø18.6 at (38.5, 64.0) | through the plate | — |

Because every wall opening straddles the parting line, **each half's share of it
is open towards that half's build plate**. There is no ceiling over any opening
in either part, so there is nothing to bridge and nothing to support. This is
the single decision that gets the base to 0.000 mm² of support, and it is why
the parting line is at 14.0 rather than at the rim of a conventional shell.

**Patient-safety separation is satisfied.** The electrode harness exits the −X
short wall; the magnetic charge connector is on the +X short wall — opposite
short edges, 77 mm apart in X and a further 37 mm apart in Y. Note the panel
parts are *wired* to P1/J8, not mounted at those connectors, so the opening
positions were free to be chosen for safety rather than dictated by the board.

The −Y wall carries **no opening at all**: that is the chip-antenna edge.

---

## 8. Print settings and orientation

Assumed FDM, 0.4 mm nozzle, 0.2 mm layers. **Confirm the printer and material.**

| Part | Orientation | Bed face |
|---|---|---|
| `case-base.stl` | As exported, open-face-up | Outer bottom, 77.0 × 81.5 mm |
| `case-lid.stl` | As exported, outer top face down | Outer top, 77.0 × 81.5 mm |

**Both STLs are exported already in their print orientation.** Do not rotate
them in the slicer. Both are open-side-up, which is what removes the supports.

**What the orientation makes strong, and what it makes weak.** Layer adhesion is
the weak axis on both parts, and on both parts it runs vertically (along Z).
Consequences worth knowing:

- The **rail ribs** are loaded sideways by the board legs — across the layers,
  which is the weak direction. They are 1.4–3.0 mm thick and 6.3 mm tall, and
  the load is trivial (a 62 × 44 × 1 mm board), so this is fine. Do not thin
  them further.
- The **screw bosses are not bosses** — the pilot holes go straight down into
  6.5 mm of solid wall, so the screw threads along the layers rather than
  splitting them apart. This is the strongest possible arrangement for a
  self-tapper in an FDM part and it is the main reason the X walls are 6.5 mm.
- The **lid skirt** takes lid-lifting load along the layers. Good.

Bed adhesion: both parts present a full flat 77 × 81.5 mm face, so no brim is
needed. **No bottom chamfer is modelled** — deal with elephant foot using the
slicer's first-layer horizontal compensation rather than by adding geometry.
**No external corner fillets are modelled either**; see §9.

---

## 9. Open questions

Resolve these; do not assume.

1. **SCHURTER 52-03-80 behind-panel depth — UNVERIFIED, and blocking.** The part
   number could not be found at SCHURTER or at any distributor. The design
   allows **9.5 mm** behind the lid over the battery bay. If the real part needs
   more, `TOTAL_H` and `CAV_H` must grow. The 18 mm figure is also *assumed* to
   be the panel cutout diameter rather than the bezel diameter.
2. **MULTICOMP MP009329 and G-107-SI-0511 cutout dimensions — UNVERIFIED.**
   Both openings are provisional rectangles (10 mm and 8 mm). They are
   parametric; supply the real cutouts and re-run.
3. **Aux mounting panel thickness and pad geometry — UNVERIFIED.** Assumed
   1.0 mm FR4 centred on the MP1/MP2 pad columns. `pcb-brief.md` open question 3
   confirms the source material never specifies this. The 1.4 mm slot width is
   derived from it and changes with it.
4. **How is the device worn?** Not specified anywhere. **No strap lugs, no belt
   clip and no mounting features are modelled.** A 77 × 81.5 × 24 mm brick worn
   on a biceps needs a defined strap interface, and its load path should be
   designed rather than added later.
5. **Wearable finish.** External vertical corners are square and external edges
   are unfilleted. For a device worn against skin the skill's own rule is to
   fillet every external edge. Doing that through the API needs edge selection,
   which was judged too brittle to do blind. **Either accept a hand-finishing
   step, or take the part over by hand in SOLIDWORKS from this point.**
6. **Sealing.** The source design was IP54. **This one is not sealed** — the
   parting-line-split openings are deliberately open. If IP54 matters, this needs
   a gasket groove and the opening strategy has to be reconsidered, which will
   cost the zero-support result.
7. **Printer, material and nozzle are unconfirmed.** Every clearance in §5
   assumes FDM at 0.4 mm. On SLA or MJF they are all too loose.
