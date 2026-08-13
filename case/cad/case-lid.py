r"""BioZ muscle monitor - enclosure LID (upper shell).

THIS SCRIPT IS THE SOURCE. The .sldprt is a build artifact.

Run:  "C:\Users\User\anaconda3\python.exe" <this file>

The lid is a deep tray, not a flat plate: the parting line sits at assembled
z = 14.0 mm, below every wall opening, so the lid carries the upper 8 mm of the
enclosure wall and the upper half of all three openings.

MODELLED IN PRINT ORIENTATION: the outer top face is at z = 0 and lies on the
bed; the skirt rises to z = 10 and the register lip to z = 11. So the exported
STL is already slicer-ready and needs no rotation.

    assembled_z = 24.0 - lid_z

Because the lid is inverted for printing, its share of each wall opening is open
towards the bed - no ceilings, no bridges, no support. The only support in the
whole job is the four screw counterbores, which is a deliberate trade: see
print-checks.md.
"""

import os
import sys

sys.path.insert(0, r"C:\Users\User\Documents\Agents\tools")
import swx

# =============================================================================
# CONSTANTS - millimetres. These MUST track case-base.py; the shared ones are
# repeated here rather than imported so each part file stands alone, and any
# divergence is caught by the mating checks at the bottom of main().
# =============================================================================
OUT_X = 77.0          # = base outer X
OUT_Y = 81.5          # = base outer Y
WALL_X = 6.5
WALL_Y = 2.0
PART_LINE = 14.0      # base rim height, assembled
TOTAL_H = 24.0        # assembled overall height

PLATE_T = 2.0         # lid outer plate
SKIRT_H = 8.0         # wall carried by the lid: TOTAL_H - PART_LINE - PLATE_T
LIP_H = 1.0           # register lip protrusion past the skirt free edge
LIP_W = 1.2           # register lip thickness
LIP_CLR = 0.2         # per face, lip to base cavity wall

LID_H = PLATE_T + SKIRT_H + LIP_H       # 11.0

# base cavity, for the lip to register into
CAV_X0, CAV_X1 = WALL_X, OUT_X - WALL_X          # 6.5 .. 70.5
CAV_Y0, CAV_Y1 = WALL_Y, OUT_Y - WALL_Y          # 2.0 .. 79.5

# --- board frame (identical derivation to case-base.py) ----------------------
BOARD_X, BOARD_Y = 62.0, 44.0
BOARD_GAP_X, BOARD_GAP_Y = 1.0, 0.3
OX = WALL_X + BOARD_GAP_X       # 7.5
OY = WALL_Y + BOARD_GAP_Y       # 2.3
RAIL_TOP, BOARD_T = 8.3, 1.0
BOARD_TOP_Z = RAIL_TOP + BOARD_T                 # 9.3 assembled

# --- panel features ----------------------------------------------------------
LED1_X, LED1_Y = 21.5, 8.4      # board coords, from BioZ-Muscle-Monitor.kicad_pcb
LIGHTPIPE_H = 12.7              # BIVAR VLP-500-R/F, 0.500 in. Distributor-listed
LIGHTPIPE_D = 3.0               # 3 mm round face, same source. FLAGGED - full
                                # datasheet PDF not obtained.
LIGHTPIPE_CLR = 0.4             # holes print undersize

BTN_CUTOUT_D = 18.0             # SCHURTER 52-03-80 "18 mm". ASSUMED to be the
                                # panel cutout diameter - the part number could
                                # not be found at SCHURTER or any distributor.
                                # FLAGGED, see case-design.md.
BTN_CLR = 0.6                   # generous: a panel nut must actually pass

SCREW_CLR_R = 1.2               # M2 shank + 0.4 on diameter
CBORE_R = 2.0                   # M2 pan head
CBORE_DEPTH = 1.0

# --- opening positions, must match case-base.py ------------------------------
J1_Y = 23.0
J8_X = 51.5
ELEC_Y0, ELEC_Y1 = OY + J1_Y - 3.0, OY + J1_Y + 3.0     # 22.3 .. 28.3
ELEC_TOP = 16.0                 # assembled top of the electrode opening
CHG_Y0, CHG_Y1 = 59.0, 69.0
CHG_TOP = 19.0
SW_X0, SW_X1 = OX + J8_X - 4.0, OX + J8_X + 4.0         # 55.0 .. 63.0
SW_TOP = 19.0

SCREW_XS = [WALL_X / 2.0, OUT_X - WALL_X / 2.0]         # 3.25 , 73.75
SCREW_YS = [6.0, OUT_Y - 6.0]                           # 6.0 , 75.5

# battery bay, for the pushbutton position and its depth budget
CELL_X, CELL_Y, CELL_Z = 48.0, 30.0, 10.0
DIV_Y1 = OY + BOARD_Y + 0.3 + 2.0                        # 48.6
BAY_CX = (CAV_X0 + CAV_X1) / 2.0                         # 38.5
BTN_CX, BTN_CY = BAY_CX, 64.0
RIB_TOP = 2.0 + CELL_Z + 0.5                             # 12.5 assembled

OUTDIR = r"C:\Users\User\Documents\BioZ-muscle-monitor\case"
PRT = os.path.join(OUTDIR, "cad", "case-lid.SLDPRT")
STL = os.path.join(OUTDIR, "stl", "case-lid.stl")

# lid_z at which material stops, for each notched wall
ELEC_CUT_Z = TOTAL_H - ELEC_TOP     # 8.0
CHG_CUT_Z = TOTAL_H - CHG_TOP       # 5.0
SW_CUT_Z = TOTAL_H - SW_TOP         # 5.0

# lip bands, inset from the base cavity walls by LIP_CLR
LIPmX0, LIPmX1 = CAV_X0 + LIP_CLR, CAV_X0 + LIP_CLR + LIP_W     # 6.7 .. 7.9
LIPpX0, LIPpX1 = CAV_X1 - LIP_CLR - LIP_W, CAV_X1 - LIP_CLR     # 69.1 .. 70.3
LIPmY0, LIPmY1 = CAV_Y0 + LIP_CLR, CAV_Y0 + LIP_CLR + LIP_W     # 2.2 .. 3.4
LIPpY0, LIPpY1 = CAV_Y1 - LIP_CLR - LIP_W, CAV_Y1 - LIP_CLR     # 78.1 .. 79.3

SKIRT_TOP = PLATE_T + SKIRT_H       # 10.0
LIP_TOP = LID_H                     # 11.0

# The skirt's inner face is the LIP's OUTER face, not the base cavity wall.
# Getting this wrong leaves a LIP_CLR-wide, SKIRT_H-deep slot between skirt and
# lip - 0.2 x 8 mm, far below the 0.8 mm minimum feature, so the slicer fuses it
# solid anyway. The 0.2 mm register clearance is taken on the lip's outboard
# face instead, which means the skirt overhangs the base cavity edge by 0.2 mm.
# That ledge is harmless and it hides the joint line.
BOSSES = [
    ("plate",       0.0,     0.0,     OUT_X,   OUT_Y,   PLATE_T),

    # -X wall + its lip, notched for the electrode harness
    ("skmX_lo",     0.0,     0.0,     LIPmX0,  OUT_Y,   ELEC_CUT_Z),
    ("skmX_a",      0.0,     0.0,     LIPmX0,  ELEC_Y0, SKIRT_TOP),
    ("skmX_b",      0.0,     ELEC_Y1, LIPmX0,  OUT_Y,   SKIRT_TOP),
    # NOTE the lip ring stops at LIPmY0/LIPpY1, it does NOT run to OUT_Y. The
    # lip is the only feature of either shell that reaches across the parting
    # line; running it the full length drove it straight into the base's -Y and
    # +Y walls. Caught by verify-fit.py, not by any single-part check.
    ("lipmX_lo",    LIPmX0,  LIPmY0,  LIPmX1,  LIPpY1,  ELEC_CUT_Z),
    ("lipmX_a",     LIPmX0,  LIPmY0,  LIPmX1,  ELEC_Y0, LIP_TOP),
    ("lipmX_b",     LIPmX0,  ELEC_Y1, LIPmX1,  LIPpY1,  LIP_TOP),

    # +X wall + its lip, notched for the magnetic charge connector
    ("skpX_lo",     LIPpX1,  0.0,     OUT_X,   OUT_Y,   CHG_CUT_Z),
    ("skpX_a",      LIPpX1,  0.0,     OUT_X,   CHG_Y0,  SKIRT_TOP),
    ("skpX_b",      LIPpX1,  CHG_Y1,  OUT_X,   OUT_Y,   SKIRT_TOP),
    ("lippX_lo",    LIPpX0,  LIPmY0,  LIPpX1,  LIPpY1,  CHG_CUT_Z),
    ("lippX_a",     LIPpX0,  LIPmY0,  LIPpX1,  CHG_Y0,  LIP_TOP),
    ("lippX_b",     LIPpX0,  CHG_Y1,  LIPpX1,  LIPpY1,  LIP_TOP),

    # -Y wall: chip-antenna edge, unbroken
    ("skmY",        LIPmX0,  0.0,     LIPpX1,  LIPmY0,  SKIRT_TOP),
    # Y lips run out to the X lips so the register ring closes at the corners.
    ("lipmY",       LIPmX0,  LIPmY0,  LIPpX1,  LIPmY1,  LIP_TOP),

    # +Y wall + its lip, notched for the slide switch
    ("skpY_lo",     LIPmX0,  LIPpY1,  LIPpX1,  OUT_Y,   SW_CUT_Z),
    ("skpY_a",      LIPmX0,  LIPpY1,  SW_X0,   OUT_Y,   SKIRT_TOP),
    ("skpY_b",      SW_X1,   LIPpY1,  LIPpX1,  OUT_Y,   SKIRT_TOP),
    ("lippY_lo",    LIPmX0,  LIPpY0,  LIPpX1,  LIPpY1,  SW_CUT_Z),
    ("lippY_a",     LIPmX0,  LIPpY0,  SW_X0,   LIPpY1,  LIP_TOP),
    ("lippY_b",     SW_X1,   LIPpY0,  LIPpX1,  LIPpY1,  LIP_TOP),
]

THRU = LID_H + 6.0
CIRCLE_CUTS = [
    ("lightpipe", OX + LED1_X, OY + LED1_Y, (LIGHTPIPE_D + LIGHTPIPE_CLR) / 2.0, THRU),
    ("button",    BTN_CX,      BTN_CY,      (BTN_CUTOUT_D + BTN_CLR) / 2.0,      THRU),
]
for i, x in enumerate(SCREW_XS):
    for j, y in enumerate(SCREW_YS):
        CIRCLE_CUTS.append(("screw_%d%d" % (i, j), x, y, SCREW_CLR_R, THRU))
        CIRCLE_CUTS.append(("cbore_%d%d" % (i, j), x, y, CBORE_R, CBORE_DEPTH))

EXPECT_BBOX = (OUT_X, OUT_Y, LID_H)


# =============================================================================
# See case-base.py for the derivation: a Top-Plane sketch maps (u,v) to model
# (-v, u) on this install. sk() undoes it so the constants above are in the
# design frame.
def sk(x, y):
    return swx.mm(y), swx.mm(-x)


def assert_frame(path, expect, tol=0.05):
    """Order-sensitive bbox check. swx.assert_bbox sorts and cannot see a
    transposed frame; this can. Also pins the mesh origin to (0,0,0) so
    assert_material's model coordinates are design coordinates."""
    _, lo, hi = swx.stl_triangles(path)
    got = [hi[a] - lo[a] for a in range(3)]
    for a, axis in enumerate("XYZ"):
        if abs(got[a] - expect[a]) > tol:
            swx.fail("%s: %s extent %.3f mm, expected %.3f mm (frame is wrong)"
                     % (os.path.basename(path), axis, got[a], expect[a]))
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
    # FeatureExtrusion3, 23 args (type library confirms the published signature).
    # T1 = 0 = swEndCondBlind, T0 = 0 = swStartSketchPlane, Dir = False for a boss.
    f = model.FeatureManager.FeatureExtrusion3(
        True, False, False, 0, 0, swx.mm(h), 0.0,
        False, False, False, False, 0.0, 0.0,
        False, False, False, False,
        True, True, True, 0, 0.0, False)
    swx.check(f, "FeatureExtrusion3(%s)" % label)
    print("  boss %-12s %6.2f,%6.2f -> %6.2f,%6.2f  h=%5.2f"
          % (label, x0, y0, x1, y1, h))


def circle_cut(sw, model, label, cx, cy, r, depth):
    swx.select(model, "Top Plane", "PLANE")
    model.SketchManager.InsertSketch(True)
    ucx, vcy = sk(cx, cy)
    c = model.SketchManager.CreateCircleByRadius(ucx, vcy, 0.0, swx.mm(r))
    swx.check(c, "CreateCircleByRadius(%s)" % label)
    # FeatureCut4 takes 27 args on this release, NOT the 26 the VBA help lists -
    # a trailing OptimizeGeometry. Read from sldworks.tlb. Dir = True for a cut.
    f = model.FeatureManager.FeatureCut4(
        True, False, True, 0, 0, swx.mm(depth), 0.0,
        False, False, False, False, 0.0, 0.0,
        False, False, False, False,
        False, True, True,
        False, False, False,
        0, 0.0, False, False)
    swx.check(f, "FeatureCut4(%s)" % label)
    print("  cut  %-12s at %6.2f,%6.2f  r=%.2f depth=%.1f" % (label, cx, cy, r, depth))


def main():
    print("BioZ enclosure - LID")
    print("  outer %.1f x %.1f x %.1f mm (modelled in print orientation,"
          " outer top face on the bed)" % EXPECT_BBOX)
    print("  parting line assembled z=%.1f; lid carries wall z=%.1f..%.1f"
          % (PART_LINE, PART_LINE, TOTAL_H - PLATE_T))
    print("  light pipe hole dia %.1f at (%.1f, %.1f); pipe tops out at"
          " assembled z=%.1f, lid inner ceiling is z=%.1f"
          % (LIGHTPIPE_D + LIGHTPIPE_CLR, OX + LED1_X, OY + LED1_Y,
             BOARD_TOP_Z + LIGHTPIPE_H, TOTAL_H - PLATE_T))
    print("  pushbutton cutout dia %.1f at (%.1f, %.1f); depth available behind"
          " the panel = %.1f mm" % (BTN_CUTOUT_D + BTN_CLR, BTN_CX, BTN_CY,
                                    (TOTAL_H - PLATE_T) - RIB_TOP))

    # Consistency gates on the numbers themselves, before any geometry.
    if abs((PLATE_T + SKIRT_H) - (TOTAL_H - PART_LINE)) > 1e-9:
        swx.fail("lid height does not close: plate+skirt %.2f != TOTAL_H-PART_LINE %.2f"
                 % (PLATE_T + SKIRT_H, TOTAL_H - PART_LINE))
    if abs((BOARD_TOP_Z + LIGHTPIPE_H) - (TOTAL_H - PLATE_T)) > 0.001:
        swx.fail("light pipe does not meet the lid: pipe top z=%.2f, lid inner "
                 "ceiling z=%.2f" % (BOARD_TOP_Z + LIGHTPIPE_H, TOTAL_H - PLATE_T))

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
    sw.SetUserPreferenceIntegerValue(78, 2)     # swSTLQuality = Fine
    stats = swx.export_stl(sw, model, STL, expected_mm=EXPECT_BBOX)
    swx.require_watertight(stats, STL)
    assert_frame(STL, EXPECT_BBOX)

    swx.assert_material(STL, [
        ("plate solid",              38.5, 40.0,  1.0, True),
        ("lid cavity open",          38.5, 40.0,  6.0, False),
        ("button hole open",         BTN_CX, BTN_CY, 1.0, False),
        ("plate beside button",      BTN_CX, BTN_CY - 12.0, 1.0, True),
        ("light pipe hole open",     OX + LED1_X, OY + LED1_Y, 1.0, False),
        ("plate beside light pipe",  OX + LED1_X + 4.0, OY + LED1_Y, 1.0, True),
        ("-X skirt solid",            3.0, 40.0,  9.0, True),
        ("electrode notch open",      3.0, OY + J1_Y, 9.0, False),
        ("-X skirt below notch",      3.0, OY + J1_Y, 6.0, True),
        ("+X skirt solid",           73.0, 40.0,  8.0, True),
        ("charge notch open",        73.0, 64.0,  8.0, False),
        ("+Y skirt solid",           20.0, 80.5,  8.0, True),
        ("switch notch open",        OX + J8_X, 80.5, 8.0, False),
        ("-Y skirt solid",           38.5,  1.0,  8.0, True),
        ("register lip solid",        7.3, 40.0, 10.5, True),
        ("skirt/lip continuous",      6.6, 40.0,  9.0, True),
        ("open outboard of lip",      5.0, 40.0, 10.5, False),
        ("screw clearance open", SCREW_XS[0], SCREW_YS[0], 5.0, False),
        ("counterbore open",    SCREW_XS[0], SCREW_YS[0], 0.5, False),
        ("plate beside screw",  SCREW_XS[0], SCREW_YS[0] + 6.0, 0.5, True),
    ], origin="model")

    swx.report_supports(STL)
    swx.close(sw, model)
    swx.finish([PRT, STL])


if __name__ == "__main__":
    main()
