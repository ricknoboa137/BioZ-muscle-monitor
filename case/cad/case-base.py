r"""BioZ muscle monitor - enclosure BASE (lower shell).

THIS SCRIPT IS THE SOURCE. The .sldprt is a build artifact. Change a number in
the constants block and re-run; hand edits made in SOLIDWORKS are lost.

Run:  "C:\Users\User\anaconda3\python.exe" <this file>

Design summary
--------------
Two-part case, parting line at assembled z = 14.0 mm, which is deliberately
BELOW every wall opening. Every connector/switch opening therefore straddles the
parting line and is a notch open to the bed in BOTH halves - no internal
ceilings, no bridges, no support anywhere on either part except the lid's screw
counterbores.

Base prints open-face-up (outer bottom face on the bed).

Construction trick: SOLIDWORKS extrusions that must START above z=0 need either a
reference plane or the StartCondition enum, neither of which I am willing to
assert from memory. Instead the solid is expressed as a UNION OF BANDS, every one
of them a plain Top-Plane rectangle extruded blind from z=0. A wall that is
notched above z=S is built as (full wall bar, height S) + (wall bar segments
either side of the notch, full height). The union is exactly the notched wall.
All geometry is therefore Top-Plane, blind-from-zero, and needs no enum I have
not verified by measuring the result.
"""

import os
import sys

sys.path.insert(0, r"C:\Users\User\Documents\Agents\tools")
import swx

# =============================================================================
# CONSTANTS - all millimetres. Source of every number is stated.
# =============================================================================

# --- the board it has to hold ------------------------------------------------
BOARD_X = 62.0        # pcb/CHECKPOINT.md "Board facts (settled)" - grown from 50
BOARD_Y = 44.0        # pcb/CHECKPOINT.md - final, do not shrink
BOARD_T = 1.0         # pcb-brief.md s1
BOARD_GAP_X = 1.0     # chosen: needs >= 0.3 print clearance AND room for the
                      # outboard rail rib (see RAIL_* below). 1.0 is the smallest
                      # value that leaves a printable 1.4 mm rib.
BOARD_GAP_Y = 0.3     # print/pocket clearance only; nothing intrudes in Y

# --- the cell ----------------------------------------------------------------
CELL_X, CELL_Y, CELL_Z = 48.0, 30.0, 10.0   # Jauch LP103048JU, brief s1
CELL_CLR = 0.5                              # per face

# --- shell ------------------------------------------------------------------
WALL_X = 6.5          # thick: the X walls carry the four screw pilot holes.
                      # 6.5 = 1.6 pilot + 2.45 mm of material each side.
WALL_Y = 2.0          # >= 1.2 mm (3 perimeters at 0.4 nozzle)
FLOOR = 2.0
PART_LINE = 14.0      # base outer height = base rim height

# --- the inverted-U PCB mount ------------------------------------------------
# Two auxiliary PCBs solder to the main board's MP1/MP2 edge-pad columns and hang
# down as legs. MP1 sits at board x = 1.1, MP2 at board x = 60.8 (read from
# BioZ-Muscle-Monitor.kicad_pcb). Panel assumed 1.0 mm FR4 centred on the pad row.
AUX_T = 1.0           # ASSUMED - aux panel thickness. Not specified anywhere in
                      # the source material (pcb-brief.md open question 3).
AUX_CLR = 0.2         # per face, slot clearance
MP1_X = 1.1           # board coords, from the .kicad_pcb
MP2_X = 60.8
RAIL_TOP = 8.3        # board underside height above the outer bottom face
RIB_IN_W = 3.0        # inboard rail rib width

# --- heights -----------------------------------------------------------------
LIGHTPIPE_H = 12.7    # BIVAR VLP-500-R/F, 0.500 in above the board.
                      # Distributor-listed (Newark/RS/Arrow); full datasheet PDF
                      # not obtained. FLAGGED.
LIGHTPIPE_D = 3.0     # 3 mm round face, same source

# --- panel-part opening positions (board coords, from the .kicad_pcb) --------
J1_Y = 23.0           # electrode connector, exits -X  (patient side)
J8_X = 51.5           # slide switch feed connector
LED1_X, LED1_Y = 21.5, 8.4    # light pipe must be over this

# =============================================================================
# DERIVED - model coordinate frame
# =============================================================================
OX = WALL_X + BOARD_GAP_X       # board x=0 -> model x
OY = WALL_Y + BOARD_GAP_Y       # board y=0 -> model y

CAV_X0, CAV_X1 = WALL_X, WALL_X + BOARD_X + 2 * BOARD_GAP_X     # 6.5 .. 70.5
DIV_Y0 = OY + BOARD_Y + 0.3                                      # 46.6
DIV_Y1 = DIV_Y0 + 2.0                                            # 48.6
CAV_Y0 = WALL_Y                                                  # 2.0
CAV_Y1 = DIV_Y1 + CELL_Y + 2 * CELL_CLR - 0.1                    # 79.5

OUT_X = CAV_X1 + WALL_X          # 77.0
OUT_Y = CAV_Y1 + WALL_Y          # 81.5

# rails, model x
S1_0, S1_1 = OX + MP1_X - AUX_T / 2 - AUX_CLR, OX + MP1_X + AUX_T / 2 + AUX_CLR
S2_0, S2_1 = OX + MP2_X - AUX_T / 2 - AUX_CLR, OX + MP2_X + AUX_T / 2 + AUX_CLR

# battery bay
BAY_CX = (CAV_X0 + CAV_X1) / 2.0
CELL_X0, CELL_X1 = BAY_CX - CELL_X / 2.0, BAY_CX + CELL_X / 2.0
RIB_TOP = FLOOR + CELL_Z + 0.5                                   # 12.5

# --- wall openings: sill height (base side) and width -----------------------
# All three straddle PART_LINE = 14.0, so each is open at the base rim.
ELEC_Y0, ELEC_Y1 = OY + J1_Y - 3.0, OY + J1_Y + 3.0     # 6 mm wide
ELEC_SILL = 10.0                                        # 0.7 above board top
CHG_Y0, CHG_Y1 = 59.0, 69.0                             # 10 mm wide, over the bay
CHG_SILL = 11.0
SW_X0, SW_X1 = OX + J8_X - 4.0, OX + J8_X + 4.0         # 8 mm wide
SW_SILL = 13.0                                          # clears the cell (top 12.0)

# --- screws ------------------------------------------------------------------
SCREW_R = 0.8         # M2 self-tapping pilot, dia 1.6
SCREW_XS = [WALL_X / 2.0, OUT_X - WALL_X / 2.0]         # 3.25 , 73.75
SCREW_YS = [6.0, OUT_Y - 6.0]                           # 6.0 , 75.5

OUTDIR = r"C:\Users\User\Documents\BioZ-muscle-monitor\case"
PRT = os.path.join(OUTDIR, "cad", "case-base.SLDPRT")
STL = os.path.join(OUTDIR, "stl", "case-base.stl")

# =============================================================================
# Band decomposition: (label, x0, y0, x1, y1, height)
# =============================================================================
BOSSES = [
    ("floor",        0.0,     0.0,     OUT_X,   OUT_Y,   FLOOR),

    # -X wall, notched above ELEC_SILL for the electrode harness
    ("wallmX_lo",    0.0,     0.0,     WALL_X,  OUT_Y,   ELEC_SILL),
    ("wallmX_a",     0.0,     0.0,     WALL_X,  ELEC_Y0, PART_LINE),
    ("wallmX_b",     0.0,     ELEC_Y1, WALL_X,  OUT_Y,   PART_LINE),

    # +X wall, notched above CHG_SILL for the magnetic charge connector
    ("wallpX_lo",    CAV_X1,  0.0,     OUT_X,   OUT_Y,   CHG_SILL),
    ("wallpX_a",     CAV_X1,  0.0,     OUT_X,   CHG_Y0,  PART_LINE),
    ("wallpX_b",     CAV_X1,  CHG_Y1,  OUT_X,   OUT_Y,   PART_LINE),

    # -Y wall: the chip-antenna edge. No opening, no metal, no extra thickness.
    ("wallmY",       CAV_X0,  0.0,     CAV_X1,  WALL_Y,  PART_LINE),

    # +Y wall, notched above SW_SILL for the slide switch
    ("wallpY_lo",    CAV_X0,  CAV_Y1,  CAV_X1,  OUT_Y,   SW_SILL),
    ("wallpY_a",     CAV_X0,  CAV_Y1,  SW_X0,   OUT_Y,   PART_LINE),
    ("wallpY_b",     SW_X1,   CAV_Y1,  CAV_X1,  OUT_Y,   PART_LINE),

    # inverted-U rails: rib / slot / rib on each X end. The board rests on the
    # rib tops; the aux PCB legs drop into the slots between them.
    ("rail_mX_out",  CAV_X0,  CAV_Y0,  S1_0,    CAV_Y1,  RAIL_TOP),
    ("rail_mX_in",   S1_1,    CAV_Y0,  S1_1 + RIB_IN_W, CAV_Y1, RAIL_TOP),
    ("rail_pX_in",   S2_0 - RIB_IN_W, CAV_Y0, S2_0,     CAV_Y1, RAIL_TOP),
    ("rail_pX_out",  S2_1,    CAV_Y0,  CAV_X1,  CAV_Y1,  RAIL_TOP),

    # battery bay: divider (split for the J7 wire run) and two side ribs. All
    # kept inboard of the lid's register lip footprint.
    ("div_a",        8.5,     DIV_Y0,  46.0,    DIV_Y1,  RIB_TOP),
    ("div_b",        52.0,    DIV_Y0,  68.5,    DIV_Y1,  RIB_TOP),
    ("bat_rib_mX",   CELL_X0 - 2.0, DIV_Y1, CELL_X0, 77.5, RIB_TOP),
    ("bat_rib_pX",   CELL_X1, DIV_Y1,  CELL_X1 + 2.0,  77.5, RIB_TOP),
]

CIRCLE_CUTS = [("pilot_%d_%d" % (i, j), x, y, SCREW_R, PART_LINE + 6.0)
               for i, x in enumerate(SCREW_XS) for j, y in enumerate(SCREW_YS)]

EXPECT_BBOX = (OUT_X, OUT_Y, PART_LINE)


# =============================================================================
# MEASURED, NOT ASSUMED: a sketch on the Top Plane does NOT map sketch (u,v) to
# model (X,Y). On this install it comes out rotated 90 deg about Z:
#     model_x = -v      model_y = +u      model_z = extrusion depth
# Established by rastering point_in_solid over the first exported STL and
# matching the notches and rail slots to their design positions - the solid was
# geometrically correct, only the frame was turned. The build axis is still +Z
# with the flat bottom at z=0, which is what matters for slicing.
#
# sk() undoes it, so every coordinate in the constants block above is in the
# design frame and the .SLDPRT/.stl come out in the same frame.
def sk(x, y):
    return swx.mm(y), swx.mm(-x)


def assert_frame(path, expect, tol=0.05):
    """Component-wise, order-sensitive bbox check, and origin at (0,0,0).

    swx.assert_bbox sorts the three extents before comparing, so a part built
    with X and Y transposed passes it. That is not hypothetical - it is what the
    first build of this part did. This is the check that catches it, and it also
    pins the mesh origin so assert_material's model coordinates are the design
    coordinates.
    """
    _, lo, hi = swx.stl_triangles(path)
    got = [hi[a] - lo[a] for a in range(3)]
    for a, axis in enumerate("XYZ"):
        if abs(got[a] - expect[a]) > tol:
            swx.fail("%s: %s extent %.3f mm, expected %.3f mm (frame is wrong - "
                     "check sk(), the Top Plane maps sketch (u,v) to model "
                     "(-v, u))" % (os.path.basename(path), axis, got[a], expect[a]))
        if abs(lo[a]) > tol:
            swx.fail("%s: %s minimum is %.3f mm, expected 0.000"
                     % (os.path.basename(path), axis, lo[a]))
    print("  frame OK: origin at (0,0,0), extents %.2f x %.2f x %.2f mm" % tuple(got))


def rect_boss(sw, model, label, x0, y0, x1, y1, h):
    swx.select(model, "Top Plane", "PLANE")
    model.SketchManager.InsertSketch(True)
    u0, v0 = sk(x0, y0)
    u1, v1 = sk(x1, y1)
    r = model.SketchManager.CreateCornerRectangle(u0, v0, 0.0, u1, v1, 0.0)
    swx.check(r, "CreateCornerRectangle(%s)" % label)
    if len(r) != 4:
        swx.fail("%s: rectangle came back with %d segments" % (label, len(r)))
    # FeatureExtrusion3: T1 = 0 is swEndCondBlind (swEndConditions). Dir=False is
    # the boss convention (see swx docstring); both are verified downstream by
    # assert_bbox and assert_material, not taken on trust.
    f = model.FeatureManager.FeatureExtrusion3(
        True,           # Sd - single ended
        False,          # Flip
        False,          # Dir  (bosses want False)
        0, 0,           # T1, T2 = blind
        swx.mm(h), 0.0,  # D1, D2
        False, False,   # Dchk1, Dchk2
        False, False,   # Ddir1, Ddir2
        0.0, 0.0,       # Dang1, Dang2
        False, False,   # OffsetReverse1/2
        False, False,   # TranslateSurface1/2
        True,           # Merge  - must stay one body
        True, True,     # UseFeatScope, UseAutoSelect
        0,              # T0 - start from sketch plane
        0.0, False)     # StartOffset, FlipStartOffset
    swx.check(f, "FeatureExtrusion3(%s)" % label)
    print("  boss %-14s %6.2f,%6.2f -> %6.2f,%6.2f  h=%5.2f"
          % (label, x0, y0, x1, y1, h))


def circle_cut(sw, model, label, cx, cy, r, depth):
    swx.select(model, "Top Plane", "PLANE")
    model.SketchManager.InsertSketch(True)
    ucx, vcy = sk(cx, cy)
    c = model.SketchManager.CreateCircleByRadius(ucx, vcy, 0.0, swx.mm(r))
    swx.check(c, "CreateCircleByRadius(%s)" % label)
    # FeatureCut4: Dir=True is the cut convention (swx docstring - bosses and
    # cuts do NOT share a sign convention). T1 = 0 = swEndCondBlind,
    # T0 = 0 = swStartSketchPlane, both read out of
    # D:\ProgramFiles\SOLIDWORKS\swconst.tlb on this install.
    #
    # ARGUMENT COUNT: 27, NOT the 26 the published VBA help lists. This release's
    # sldworks.tlb adds a trailing OptimizeGeometry. Passing 26 fails with
    # "Parameter not optional". Read from the type library, not from memory.
    f = model.FeatureManager.FeatureCut4(
        True,           # Sd
        False,          # Flip
        True,           # Dir  (cuts want True)
        0, 0,           # T1, T2 = blind
        swx.mm(depth), 0.0,
        False, False,
        False, False,
        0.0, 0.0,
        False, False,
        False, False,
        False,          # NormalCut
        True, True,     # UseFeatScope, UseAutoSelect
        False, False, False,   # AssemblyFeatureScope, AutoSelectComponents,
                               # PropagateFeatureToParts
        0,                     # T0 = swStartSketchPlane
        0.0, False,            # StartOffset, FlipStartOffset
        False)                 # OptimizeGeometry
    swx.check(f, "FeatureCut4(%s)" % label)
    print("  cut  %-14s at %6.2f,%6.2f  r=%.2f depth=%.1f" % (label, cx, cy, r, depth))


def main():
    print("BioZ enclosure - BASE")
    print("  outer %.1f x %.1f x %.1f mm" % EXPECT_BBOX)
    print("  cavity x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f"
          % (CAV_X0, CAV_X1, CAV_Y0, CAV_Y1, FLOOR, PART_LINE))
    print("  board sits x %.1f..%.1f  y %.1f..%.1f  top face z=%.1f"
          % (OX, OX + BOARD_X, OY, OY + BOARD_Y, RAIL_TOP + BOARD_T))
    print("  rail slots x %.2f..%.2f and %.2f..%.2f (%.1f mm wide, %.1f deep)"
          % (S1_0, S1_1, S2_0, S2_1, S1_1 - S1_0, RAIL_TOP - FLOOR))

    sw = swx.connect()
    model = swx.new_part(sw)

    for b in BOSSES:
        rect_boss(sw, model, *b)
    for c in CIRCLE_CUTS:
        circle_cut(sw, model, *c)

    model.EditRebuild3        # property, not a method
    swx.assert_bbox(model, EXPECT_BBOX)
    swx.assert_single_body(model)

    swx.save_as(model, PRT, sw=sw)
    # swSTLQuality = 78, swSTLQuality_Fine = 2 (swconst.tlb, this install).
    # The part is all planar except the lid holes, but Coarse would inscribe a
    # visibly faceted, undersize circle.
    sw.SetUserPreferenceIntegerValue(78, 2)
    stats = swx.export_stl(sw, model, STL, expected_mm=EXPECT_BBOX)
    swx.require_watertight(stats, STL)

    # swx.assert_bbox SORTS the axes, so it passes on a part whose X and Y are
    # transposed - which is exactly what happened on the first build here.
    # Check the frame component-wise and in order.
    assert_frame(STL, EXPECT_BBOX)

    # Every cavity and every opening probed. assert_bbox cannot see a cut that
    # went the wrong way - the envelope is identical either way.
    swx.assert_material(STL, [
        ("floor solid",              38.5, 25.0,  1.0, True),
        ("cavity void over board",   38.5, 25.0, 12.0, False),
        ("-X wall solid",             3.0, 40.0, 12.0, True),
        ("electrode notch open",      3.0, OY + J1_Y, 12.0, False),
        ("electrode sill solid",      3.0, OY + J1_Y,  5.0, True),
        ("+X wall solid",            73.0, 40.0, 12.5, True),
        ("charge notch open",        73.0, 64.0, 12.5, False),
        ("+Y wall solid",            20.0, 80.5, 13.5, True),
        ("switch notch open",        OX + J8_X, 80.5, 13.5, False),
        ("rail outboard rib solid",   7.2, 40.0,  6.0, True),
        ("rail slot open",            8.6, 40.0,  6.0, False),
        ("rail inboard rib solid",   10.0, 40.0,  6.0, True),
        ("void above rail",          10.0, 40.0, 10.0, False),
        ("bay divider solid",        20.0, 47.6,  8.0, True),
        ("battery bay open",         38.5, 64.0,  8.0, False),
        ("battery side rib solid",   13.5, 60.0,  8.0, True),
        ("screw pilot open",   SCREW_XS[0], SCREW_YS[0], 7.0, False),
        ("wall beside pilot solid",   5.5, SCREW_YS[0], 7.0, True),
    ], origin="model")

    area, span, n = swx.report_supports(STL)
    swx.close(sw, model)
    swx.finish([PRT, STL])


if __name__ == "__main__":
    main()
