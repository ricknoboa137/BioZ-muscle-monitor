# Print-readiness checks — BioZ enclosure

Every result below is **measured**, from the exported STLs that go to the
slicer, not asserted from the feature tree. Reproduce with:

```
"C:\Users\User\anaconda3\python.exe" "...\case\cad\case-base.py"
"C:\Users\User\anaconda3\python.exe" "...\case\cad\case-lid.py"
"C:\Users\User\anaconda3\python.exe" "...\case\cad\verify-fit.py"
```

Targets assume FDM, 0.4 mm nozzle. **The printer and material are unconfirmed** —
see `case-design.md` §9.7.

---

## 1. Results

| Check | Target | `case-base` | `case-lid` | |
|---|---|---|---|---|
| Support material | as low as good engineering allows | **0.000 mm²**, 0 facets | **32.007 mm²**, 288 facets | pass |
| Widest unsupported span | ≤ 5 mm bridge | 0.00 mm | **0.33 mm** | pass |
| Internal ceilings | none | none | none | pass |
| Watertight | every edge shared by exactly 2 triangles | yes | yes | pass |
| Binary STL, mm | required | yes, 812 facets | yes, 1656 facets | pass |
| Bounding box vs design | ±0.5 mm | 77.0 × 81.5 × 14.0 | 77.0 × 81.5 × 11.0 | exact |
| Frame, order-sensitive | X,Y,Z in design order, origin at 0,0,0 | pass | pass | pass |
| Single solid body | 1 | 1 | 1 | pass |
| Material/void probes | all | **18/18** | **20/20** | pass |
| Wall thickness | ≥ 1.2 mm | 2.0 / 6.5 mm | 2.0 / 6.5 mm | pass |
| Minimum feature | ≥ 0.8 mm | **1.2 mm** (register lip) / 1.4 mm (rail rib) | 1.2 mm | pass |
| Unsupported overhang | ≤ 45° from vertical | none | counterbores only | see §2 |
| First-layer footprint | largest flat face down | 77.0 × 81.5 mm | 77.0 × 81.5 mm | pass |
| Assembly path | one straight motion | clear over 2835 columns | — | pass |
| Shell interference | none | no overlap over 140988 points across the joint | | pass |

---

## 2. The 32 mm² of support on the lid, and why it stays

The lid's only downward-facing geometry is the **four M2 counterbore shoulders**:
Ø4.0 stepping down to Ø2.4, so an annular ledge 0.8 mm wide, four of them.
Predicted 4 × π(2.0² − 1.2²) = 32.2 mm²; **measured 32.007 mm²**, which is a
good check that the measurement is measuring what I think it is. Widest
unsupported width **0.33 mm**.

**This is a deliberate trade and it should not be designed out.** The
alternative is screw heads standing proud of the outer top face of a device worn
against a biceps under a strap. A 0.33 mm ledge bridges cleanly at any sane
setting and needs no slicer support at all — it is well inside the 5 mm bridge
limit and inside a single perimeter.

Everything else on both parts is vertical or upward-facing. **The base is at
exactly zero.**

---

## 3. How zero support was achieved

By geometry, not by slicer settings, in the order the design decisions were made:

1. **Parting line at z = 14.0, below every wall opening.** All three connector
   openings straddle it, so each half's share is open towards its own build
   plate. No opening in either part has a ceiling. This one decision does most
   of the work.
2. **Both halves print open-side-up.** The base sits on its outer bottom; the
   lid is a deep tray printed on its outer top face. Every cavity wall rises
   vertically off the bed and neither part has an internal ceiling anywhere.
3. **Every internal feature grows from the floor.** Rails, bay divider and bay
   ribs are all extruded from the cavity floor rather than cantilevered off a
   wall, so none of them has an underside.
4. **The screws go into solid wall, not into bosses.** A boss would have needed
   a gusset; 6.5 mm walls need nothing.
5. **No horizontal holes with unsupported crowns.** There are none — every
   opening is a notch open to the parting line.

No 45° chamfers or teardrops were needed anywhere, because no feature ended up
with a horizontal ceiling to chamfer.

---

## 4. Fit verification (`verify-fit.py`)

Measured against the exported meshes of **both** shells simultaneously, in the
assembled position.

| Envelope | Result |
|---|---|
| Board slab, 62 × 44 × 1.0 mm | clear over 2520 points |
| Top-side components, 3.0 mm | clear over 3780 points |
| Bottom-side components, 1.0 mm | clear over 2100 points |
| Light pipe column, Ø3.0 × 12.7 mm | clear over 1274 points |
| Cell, 48 × 30 × 10 mm | clear over 4851 points |
| Cell envelope **+0.4 mm** in X and Y | clear over 4851 points |
| Base/lid interference across the joint | **no overlap over 140988 points** |
| Vertical insertion path | clear over 2835 columns |

The "+0.4 mm" row exists because the first version of the bay had the ribs on
the cell's nominal faces — a nominal-on-nominal fit that no printed part
achieves. Checking the nominal envelope alone passed it. Growing the envelope is
what caught it.

### Measured clearances

| | |
|---|---|
| Board to −X / +X cavity wall | 1.00 mm |
| Board to −Y cavity wall (antenna edge) | 0.30 mm |
| Board to battery divider | 0.30 mm |
| Cell to bay ribs, X per side | 0.50 mm |
| Cell in bay, Y per side | 0.45 mm |
| Cell top to base rim | 2.00 mm |
| Top-side components to lid inner face | 9.70 mm |
| Light pipe tip to lid inner face | 0.00 mm — see below |
| Pushbutton depth available behind the lid | 9.50 mm |

**Light pipe at 0.00 mm is intentional.** A VLP-series pipe is meant to butt
against the panel it lights through, and the Ø3.4 hole in the 2.0 mm lid plate
gives the Ø3.0 head 2.0 mm of travel to enter. So a pipe on the long side of
tolerance cannot hold the lid open. It is worth stating explicitly because a
0.00 in a clearance table normally means someone forgot.

---

## 5. Not checked, and honest about it

- **Nothing has been printed.** Every result above is geometric. Warping,
  first-layer squash, hole shrinkage and how an M2 self-tapper actually bites in
  this material are all unmeasured.
- **Slicing has not been run.** The support figures are measured from facet
  normals, which is a direct measure of the geometry but is not the same as a
  slicer's support decision at its own threshold angle.
- **Faceting.** STL quality is set to Fine (`swSTLQuality = 78`, value 2).
  The Ø18.6 button hole is the only feature where faceting could matter; it is
  cut oversize by 0.6 mm partly for that reason. Check it against the real part.
- **The three unverified panel-part cutouts** (`case-design.md` §9.1, §9.2) mean
  three of the five openings are provisional. They are parametric — supply the
  real numbers and re-run.
