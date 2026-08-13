# Enclosure stage checkpoint — read first

Resume from this file alone. Status as of the current session.

## The source is the Python, not the SLDPRT

`case/cad/case-base.py` and `case/cad/case-lid.py` are authoritative. Change a
number in the constants block and re-run:

```
"C:\Users\User\anaconda3\python.exe" "C:\Users\User\Documents\BioZ-muscle-monitor\case\cad\case-base.py"
```

Hand edits in SOLIDWORKS are lost on the next run.

## Hard-won API facts (verified on this install, do not re-derive)

- **`FeatureCut4` takes 27 arguments, not the 26 the published VBA help lists.**
  This release's `sldworks.tlb` adds a trailing `OptimizeGeometry`. Passing 26
  fails with "Parameter not optional". `FeatureExtrusion3` takes 23 and the
  documented signature is correct.
- Read signatures straight out of the type library, it is on disk:
  `pythoncom.LoadTypeLib(r'D:\ProgramFiles\SOLIDWORKS\sldworks.tlb')`, then walk
  `IFeatureManager`. Enums are in `swconst.tlb` alongside it.
- Verified enum values: `swEndCondBlind = 0`, `swStartSketchPlane = 0`,
  `swSTLQuality = 78` (Fine = 2), `swExportStlUnits = 211`, `swSolidBody = 0`.
  Note `swx.py`'s STL preference ids 4 and 56 are guesses and are wrong; 78/211
  are the real ones.
- **A Top-Plane sketch does NOT map (u,v) to model (X,Y).** On this install it
  comes out rotated 90 deg about Z: `model_x = -v`, `model_y = +u`. Established
  by rastering `point_in_solid` over the first exported STL. The build axis is
  still +Z with the flat bottom at z=0, so printing is unaffected, but every
  probe coordinate is wrong until it is undone. Both scripts carry an `sk()`
  helper that undoes it.
- **`swx.assert_bbox` SORTS the three extents before comparing, so it passes on
  a part built with X and Y transposed.** That is not hypothetical — it is what
  the first build did here. Both scripts carry a local `assert_frame()` that
  checks extents component-wise and in order, and pins the mesh origin to
  (0,0,0) so `assert_material` model coordinates are design coordinates.

## Construction approach — union of bands

Extrusions that must start above z=0 need a reference plane or the
`StartCondition` enum. Avoided entirely: the solid is a **union of plain
Top-Plane rectangles all extruded blind from z=0**. A wall notched above height
S is built as (full bar, height S) + (bar segments either side of the notch,
full height). The union is exactly the notched wall. No reference planes, no
face selection, no unverified enum.

## Geometry decisions already settled

- Parting line at assembled **z = 14.0 mm**, deliberately BELOW every wall
  opening, so all three openings straddle it and are notches open to the bed in
  both halves. No internal ceilings, no bridges, no support on either part
  except the lid screw counterbores.
- Base prints open-face-up; lid prints outer-top-face-down. Both open-side-up.
- Base outer **77.0 x 81.5 x 14.0**; lid outer **77.0 x 81.5 x 11.0**;
  assembled **77.0 x 81.5 x 24.0** (lid lip is internal).
- Board sits on rail ribs at z=8.3, board top face z=9.3, light pipe (12.7 mm)
  tops out at z=22.0 which is exactly the lid inner ceiling.
- **Side-by-side board/cell arrangement retained** per the user's stated thermal
  decision. It does NOT fit the CamdenBoss 71x46 internal — see the arithmetic
  in `case-design.md`. The case was grown instead of overturning the decision.

## Status

- [x] Intake set assembled from `00-context-reverse-engineered.md`,
      `pcb-brief.md`, `pcb/CHECKPOINT.md`, and connector positions read directly
      out of `pcb/BioZ-Muscle-Monitor.kicad_pcb`.
- [x] `case/cad/case-base.py` written; all 19 bosses and 4 pilot cuts build;
      watertight STL exported; geometry confirmed correct by raster probe.
- [ ] Base re-run in the corrected frame with `assert_frame` + material probes.
- [ ] `case/cad/case-lid.py`.
- [ ] `case-design.md`, `print-checks.md`, figures, docx dossier.

## Open items to carry forward

1. **SCHURTER 52-03-80 behind-panel depth is UNVERIFIED** and not findable
   online. Design allows 10.0 mm behind the lid over the battery bay. If the
   real part is deeper, `PART_LINE`/`CAV` heights must grow.
2. Slide switch G-107-SI-0511 and MULTICOMP MP009329 panel cutout dimensions
   unverified; openings are provisional rectangles, parametric.
3. Aux mounting-panel thickness assumed 1.0 mm FR4 (`AUX_T`). `pcb-brief.md`
   open question 3 confirms the source material never specifies it.
4. PCB action: **no bottom-side components within board x < 5.0 or x > 57.0** —
   that is where the rail ribs contact the board underside.
5. How the device is worn/strapped is unspecified; no strap lugs modelled.
