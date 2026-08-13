# Placement plan — BioZ Muscle Monitor rev B

Board: 62.0 × 44.0 mm (grown from 50 mm to fit the WE-SHC shield frame), 2 mm corner radius, 1.0 mm thick, 4 layer HDI.
Origin at the top-left corner; Y increases downward (KiCad convention).

Implemented in `scripts/build_board.py` (anchors + pin-adjacent attachment) and
`scripts/resolve_placement.py` (collision resolution for the free passives).
Result: 92 footprints (91 + the WE-SHC frame H1), **zero courtyard overlaps**, both manual ground and
antenna checks passing (`scripts/verify_board.py`).

---

## 1. Zone map

The analog/digital boundary is the **vertical line X = 20.0 mm**. Analog is
left of it, digital and power right of it.

```
        0                     20.0                              50  mm
      0 +----------------------+-----------------+----------------+
        |                      | LED1 R4  |  RF  |  ANTENNA       |
        |                      | U2 debnc | ladd |  KEEPOUT       | 6.82
        |                      |          | er   |----------------+
        |   (GNDA, top-left    | IC1 C43  | AE1  | U8 charger     |
     14 |    is analog pour    |----------+------+ C30 C31 C27    |
        |    with no parts)    |    U5 nRF54L15  | R13 R14 R17    |
        |                      |    Y1  Y2       |----------------+
     20 |  J1 electrode        |    FL1 L3 C13   |                |
        |  harness (left       |-----------------+  P1 charge     |
        |  44 mm edge)         | U14 LDO   U7 +  |  connector     |
     26 |     U1  R7  R5  R6   | C38-C45   L8 +  |  (right        |
        |     C5  C6           |           C29 + |   44 mm edge)  |
     30 |  R1 C1 C3 C4 C7      | C32 C33   C9    |----------------+
        |  (BOTTOM side,       | L7 R16    R15   |  J2 SWD        |
     34 |   under U1)          |           R19   |  R8            |
        |                      |                 |----------------+
     38 |  U10  C28  C37       | J7 battery      | J8 switch      |
     44 +----------------------+-----------------+----------------+
```

| Region | X, Y (mm) | Contents |
|---|---|---|
| Antenna keepout | 25.0–50.0, 0–6.82 | AE1 only. No copper on any layer. |
| RF ladder | 29.0–33.7, 6.4–12.0 | L4 L5 L6 C19 C20 C21 C23, all 0201 |
| Charger | 40.0–49.4, 7.2–16 | U8 + C30 C31 C27 R13 R14 R17 R18 |
| MCU | 27.0–37.0, 11.5–22 | U5, Y1, Y2, its five 100 nF, C18 C22 C11 C12 C36 |
| Memory | 21.5–27.0, 12–18 | IC1 + C43 |
| Button / LED | 21.5–28.0, 4–13 | U2 C25 R10 R11 R12 D1, LED1 R4 |
| Power | 30.0–41.0, 22–32 | U7 L8 C29 C9 C26 C35 C34 R15 R19 R22, LC filter |
| Digital LDO | 21.5–28.5, 24–31 | U14 + C38 C39 C40 C44 C45 |
| Charge connector | 39.5–49.7, 15.9–27.1 | P1 |
| Debug | 42.8–47.7, 29.6–37.4 | J2 |
| Analog | 0.6–19.6, 15–40 | U1 R7 R5 R6 C5 C6 C2 C37 C42 U10 C28 J1 |
| Bottom side | under U1 | R1 C1 C3 C4 C7 — the only bottom-side parts |

**Battery cell.** The LP103048JU sits **stacked under the board**, occupying
X 1–49, Y 14–44. See deviation D1 in the report: side-by-side does not fit.
U8 is deliberately in the Y < 14 strip, off the cell, and so is the antenna.

---

## 2. Adjacency, in the brief's priority order

| Pri | Brief requirement | How it is met | Measured |
|---|---|---|---|
| 1 | C4 within 1.5 mm of AVDD (C1 bump), C3 within 1.5 mm of DVDD (D1) | Both on the **bottom** layer directly under the WLP, reached through the via-in-pad escape | C4 1.0 mm, C3 1.2 mm from their bumps |
| 2 | C4 → GNDA, C3 → GNDD, C42 → GNDD, C1 (VREF) → GNDA | Net assignment in `build_board.py`; C4/C1 sit on the GNDA side of the split, C3/C42 on the GNDD side | verified by `verify_board.py` |
| 3 | R1 directly under U1 at the AGND/DGND corner | R1 is bottom side at (20.0, 26.0), straddling the split neck | pads on GNDA and GNDD only |
| 4 | C7 immediately between DRVXC (D5) and DRVSJ (C4) | Bottom side at (21.0, 29.9), under the escape | see deviation D6 |
| 5 | 100 nF within 1.5 mm of each of U5 pins 10, 22, 36, 47, 48 | Placed automatically against the named pad | 1.30, 1.29, 1.29, 1.30, 1.30 mm |
| 6 | C11/C12 adjacent to DCC (46), L3 between DCC and VDD_nRF | C11 1.30 mm, C12 2.5 mm from pin 46; L3 in series | pass |
| 7 | C22 (10 nF) close to the tied DECA (43) / DECRF (33) node | Attached to pin 43, 1.3 mm | pass |
| 8 | C43 within 1.5 mm of IC1 pin 8 | Attached, 1.65 mm | see deviation D7 |
| 9 | C31 at U8 OUT, C30 at U8 BAT | Attached to pins 10 and 2 | 2.4 mm and 1.9 mm — see D7 |
| 10 | C26/C29 at U7 IN, C9/C35 at U7 OUT | C29 2.8 mm below U7's IN pad, C9 2.6 mm above the OUT pad, both inside the loop block | pass |

---

## 3. Separation

- U7's switching loop centre is at (35.6, 26.0). U1 is at (19.8, 26.0).
  **Separation 15.8 mm** — the brief requires ≥ 15 mm.
- Nothing but U1, R7, R5, R6, C5, C6, C2, C37, C42, U10, C28 and J1 sits in
  the analog zone. C42 and C3 are the two deliberate exceptions on the GNDD
  side of the split, both belonging to U1's DVDD domain.
- U8's thermal pad (43.0, 12.5) to J7 battery connector (26.4, 38.6):
  **31.4 mm**, diagonally opposite as §8 requires.
- The NTC U9 is **not** near U8: it is a pair of wire pads at (45.0, 39.4) for
  a lead bonded to the cell.

---

## 4. Parts whose position is fixed by mechanics

| Part | Constraint | Position |
|---|---|---|
| AE1 | Board edge, inside the 6.82 mm ground clearance | (33.0, 2.4), long axis along the top edge |
| J1 | Left 44 mm edge, opposite P1, strain relief | (4.6, 23.0) |
| P1 | Right 44 mm edge, opposite J1 | (44.6, 21.5) |
| J7 | Bottom edge, far from U8 | (26.4, 38.6) |
| J8 | Bottom edge, aligned to the enclosure side wall | (36.4, 38.6) |
| J2 | Accessible with the lid off | (44.6, 31.0) |
| LED1 | Top layer, optical axis normal to the board, under the light pipe | (22.5, 4.8) |
| SW1 | **Not board mounted** — panel button, wire pads | (45.0, 42.3) |
| U9 | **Not board mounted** — bonded to the cell, wire pads | (45.0, 39.4) |
| MP1 / MP2 | Edge pad rows on both 44 mm edges | (1.1, 8.0) and (48.9, 34.0) |

---

## 5. Thermal

- **U8, 0.806 W.** Exposed pad with a 3×3 array of 0.3 mm vias on 0.55 mm
  pitch into GNDD on L2 and L4 (`route_critical.py`). The pad sits on the
  largest continuous GNDD area on the board and, because the cell is stacked
  underneath, in the one strip of board that has no cell below it.
- **U7, 0.40 W.** The MAX77827 14-FC2QFN **has no exposed pad** — see
  deviation D4. Heat leaves through the PGND pin (9) and the AGND pin (4);
  both are stitched to GNDD by the loop routing.
- **U5, 50 mW.** Die pad with a 3×3 array of 0.3 mm vias — mandatory as its
  electrical ground, not only thermal.
- **U10 / U14.** Exposed pads via-stitched to GNDA and GNDD respectively
  (2 vias each). This closes brief item V5's layout obligation.

---

## 6. Assembly side and order

- **Single-sided reflow on Top.** The only bottom-side parts are R1, C1, C3,
  C4 and C7 — five passives under the WLP, all 0402 or 0603.
- **Machine placement mandatory:** U1 (WLP), U5 (QFN48), IC1 (GQFN),
  U7 (FC2QFN), U8 (VQFN) and every 0201.
- **Fit last, by hand:** J1, J7, P1, J8, J2, and the SW1 / U9 flying leads.
- **Do not fit U1, U5 or IC1 on the first article** until the power section is
  verified at 2.5 V, 1.8 V(A) and 1.8 V(D).
- The Würth shield frame is **not on this layout** — see deviation D3.
