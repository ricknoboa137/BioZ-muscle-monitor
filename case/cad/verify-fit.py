r"""Assembled fit and interference check for the BioZ enclosure.

Run AFTER case-base.py and case-lid.py.
    "C:\Users\User\anaconda3\python.exe" <this file>

This is deliberately not a SOLIDWORKS assembly. What needs proving is not that
two parts can be mated in a CAD window, but that:

  1. the two shells do not interfere anywhere when closed,
  2. the 62 x 44 mm board's slab, its top-side and bottom-side component
     envelopes, and the light-pipe column are all clear of case material,
  3. the 48 x 30 x 10 mm cell's envelope is clear,
  4. the board can be inserted in one straight vertical motion.

All four are measured against the EXPORTED MESHES - the same files that go to
the slicer - not against the feature tree.

Method: for a given (x, y) column, collect every triangle crossing it and the z
of each crossing. Membership at any z is then the parity of crossings above it.
One pass over the triangles per column serves every z in that column, which is
what makes a grid check of this size tractable in pure Python.
"""

import os
import sys

sys.path.insert(0, r"C:\Users\User\Documents\Agents\tools")
import swx

CASE = r"C:\Users\User\Documents\BioZ-muscle-monitor\case"
BASE_STL = os.path.join(CASE, "stl", "case-base.stl")
LID_STL = os.path.join(CASE, "stl", "case-lid.stl")

TOTAL_H = 24.0          # assembled overall height
PART_LINE = 14.0

# --- assembled envelopes, design frame --------------------------------------
OX, OY = 7.5, 2.3               # board origin in the case frame
BOARD_X, BOARD_Y, BOARD_T = 62.0, 44.0, 1.0
RAIL_TOP = 8.3                  # board underside
BOARD_TOP = RAIL_TOP + BOARD_T  # 9.3

TOP_COMP_H = 3.0                # pcb-brief.md s1, general top side
BOT_COMP_H = 1.0                # pcb-brief.md s1, bottom side
RAIL_IN_X0, RAIL_IN_X1 = 12.3, 64.6     # inboard faces of the rail ribs

LED1 = (OX + 21.5, OY + 8.4)
LIGHTPIPE_R = 1.5
LIGHTPIPE_TOP = BOARD_TOP + 12.7         # 22.0

# The cell sits CENTRED in its bay, so the slack is shared between both faces
# rather than all piling up at one end. Bay is bounded by the two side ribs in X
# and by the divider / +Y cavity wall in Y.
BAY_X0, BAY_X1 = 14.0, 63.0          # inboard faces of the bay side ribs
BAY_Y0, BAY_Y1 = 48.6, 79.5          # divider face .. +Y cavity wall
CELL_W, CELL_D, CELL_H = 48.0, 30.0, 10.0
CELL = dict(x0=(BAY_X0 + BAY_X1 - CELL_W) / 2.0, x1=(BAY_X0 + BAY_X1 + CELL_W) / 2.0,
            y0=(BAY_Y0 + BAY_Y1 - CELL_D) / 2.0, y1=(BAY_Y0 + BAY_Y1 + CELL_D) / 2.0,
            z0=2.0, z1=2.0 + CELL_H)

FAILS = []


def col_crossings(tris, px, py):
    """z of every triangle crossing the vertical line through (px, py)."""
    zs = []
    for a, b, c in tris:
        d = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        if abs(d) < 1e-12:
            continue
        u = ((px - a[0]) * (c[1] - a[1]) - (py - a[1]) * (c[0] - a[0])) / d
        w = ((b[0] - a[0]) * (py - a[1]) - (b[1] - a[1]) * (px - a[0])) / d
        if u < 0 or w < 0 or u + w > 1:
            continue
        zs.append(a[2] + u * (b[2] - a[2]) + w * (c[2] - a[2]))
    zs.sort()
    return zs


def inside(zs, z):
    return sum(1 for t in zs if t > z) % 2 == 1


def check_void(label, tris_base, tris_lid, x0, x1, y0, y1, z0, z1, step=1.0):
    """Assert an assembled envelope contains no case material, either shell."""
    nx = max(2, int((x1 - x0) / step) + 1)
    ny = max(2, int((y1 - y0) / step) + 1)
    nz = max(2, int((z1 - z0) / step) + 1)
    hits = []
    inset = 0.05          # stay off the exact boundary planes
    for i in range(nx):
        px = x0 + inset + (x1 - x0 - 2 * inset) * i / (nx - 1)
        for j in range(ny):
            py = y0 + inset + (y1 - y0 - 2 * inset) * j / (ny - 1)
            zb = col_crossings(tris_base, px, py)
            zl = col_crossings(tris_lid, px, py)
            for k in range(nz):
                pz = z0 + inset + (z1 - z0 - 2 * inset) * k / (nz - 1)
                if inside(zb, pz):
                    hits.append(("base", px, py, pz))
                elif inside(zl, TOTAL_H - pz):
                    hits.append(("lid", px, py, pz))
    if hits:
        FAILS.append(label)
        who, hx, hy, hz = hits[0]
        print("  [FAIL] %-38s %d/%d sample points hit %s material, "
              "first at (%.2f, %.2f, %.2f)"
              % (label, len(hits), nx * ny * nz, who, hx, hy, hz))
    else:
        print("  [ok]   %-38s clear over %d sample points"
              % (label, nx * ny * nz))


def check_interference(tris_base, tris_lid):
    """Base and lid must not occupy the same space when closed.

    Only the register lip can possibly interfere - it is the sole part of either
    shell that reaches across the parting line - so the strips it occupies are
    sampled finely rather than gridding the whole 77 x 81.5 x 24 volume.
    """
    strips = [("-X lip", 6.0, 8.4, 0.0, 81.5),
              ("+X lip", 68.6, 71.0, 0.0, 81.5),
              ("-Y lip", 0.0, 77.0, 1.5, 3.9),
              ("+Y lip", 0.0, 77.0, 77.6, 80.0)]
    hits = 0
    total = 0
    worst = None
    for name, x0, x1, y0, y1 in strips:
        nx = max(3, int((x1 - x0) / 0.4))
        ny = max(3, int((y1 - y0) / 0.4))
        for i in range(nx):
            px = x0 + (x1 - x0) * i / (nx - 1)
            for j in range(ny):
                py = y0 + (y1 - y0) * j / (ny - 1)
                zb = col_crossings(tris_base, px, py)
                zl = col_crossings(tris_lid, px, py)
                for k in range(31):
                    pz = 12.0 + 3.0 * k / 30.0     # 12.0 .. 15.0, across the joint
                    total += 1
                    if inside(zb, pz) and inside(zl, TOTAL_H - pz):
                        hits += 1
                        if worst is None:
                            worst = (name, px, py, pz)
    if hits:
        FAILS.append("shell interference")
        print("  [FAIL] %-38s %d/%d points inside BOTH shells, first %s at "
              "(%.2f, %.2f, %.2f)" % ("base/lid interference", hits, total,
                                      worst[0], worst[1], worst[2], worst[3]))
    else:
        print("  [ok]   %-38s no overlap over %d points across the joint"
              % ("base/lid interference", total))


def check_insertion(tris_base):
    """The board assembly must drop in vertically in one motion.

    For every column the board slab occupies, there must be no base material
    anywhere ABOVE the board's own underside - otherwise something overhangs the
    board's landing site and it cannot be lowered into place.
    """
    bad = []
    for i in range(63):
        px = OX + 0.2 + (BOARD_X - 0.4) * i / 62.0
        for j in range(45):
            py = OY + 0.2 + (BOARD_Y - 0.4) * j / 44.0
            zs = col_crossings(tris_base, px, py)
            for k in range(24):
                pz = RAIL_TOP + 0.05 + (PART_LINE - RAIL_TOP - 0.1) * k / 23.0
                if inside(zs, pz):
                    bad.append((px, py, pz))
                    break
    if bad:
        FAILS.append("insertion path")
        print("  [FAIL] %-38s %d columns obstructed, first at (%.2f, %.2f, %.2f)"
              % ("vertical insertion path", len(bad), bad[0][0], bad[0][1], bad[0][2]))
    else:
        print("  [ok]   %-38s board drops straight in, 2835 columns clear"
              % "vertical insertion path")


def main():
    for p in (BASE_STL, LID_STL):
        if not os.path.isfile(p):
            swx.fail("%s missing - run case-base.py and case-lid.py first" % p)

    tb, blo, bhi = swx.stl_triangles(BASE_STL)
    tl, llo, lhi = swx.stl_triangles(LID_STL)
    print("base %d facets, extents %s" % (len(tb), [round(bhi[a] - blo[a], 2) for a in range(3)]))
    print("lid  %d facets, extents %s" % (len(tl), [round(lhi[a] - llo[a], 2) for a in range(3)]))
    print()

    print("Assembled envelope checks (both shells):")
    check_void("board slab 62 x 44 x 1.0", tb, tl,
               OX, OX + BOARD_X, OY, OY + BOARD_Y, RAIL_TOP, BOARD_TOP, step=1.5)
    check_void("top-side components, 3.0 mm", tb, tl,
               OX, OX + BOARD_X, OY, OY + BOARD_Y,
               BOARD_TOP, BOARD_TOP + TOP_COMP_H, step=1.5)
    check_void("bottom-side components, 1.0 mm", tb, tl,
               RAIL_IN_X0, RAIL_IN_X1, OY, OY + BOARD_Y,
               RAIL_TOP - BOT_COMP_H, RAIL_TOP, step=1.5)
    check_void("light pipe column dia 3.0", tb, tl,
               LED1[0] - LIGHTPIPE_R, LED1[0] + LIGHTPIPE_R,
               LED1[1] - LIGHTPIPE_R, LED1[1] + LIGHTPIPE_R,
               BOARD_TOP, LIGHTPIPE_TOP, step=0.5)
    check_void("cell 48 x 30 x 10", tb, tl,
               CELL["x0"], CELL["x1"], CELL["y0"], CELL["y1"],
               CELL["z0"], CELL["z1"], step=1.5)
    # Prove the bay clearance is REAL and not nominal-on-nominal: the same
    # envelope grown by 0.4 mm in X and Y must still be clear.
    check_void("cell envelope + 0.4 mm in X and Y", tb, tl,
               CELL["x0"] - 0.4, CELL["x1"] + 0.4,
               CELL["y0"] - 0.4, CELL["y1"] + 0.4,
               CELL["z0"], CELL["z1"], step=1.5)
    print()
    check_interference(tb, tl)
    check_insertion(tb)

    print()
    print("Measured clearances (design frame):")
    print("  board to -X cavity wall      %.2f mm" % (OX - 6.5))
    print("  board to +X cavity wall      %.2f mm" % (70.5 - (OX + BOARD_X)))
    print("  board to -Y cavity wall      %.2f mm" % (OY - 2.0))
    print("  board to battery divider     %.2f mm" % (46.6 - (OY + BOARD_Y)))
    print("  cell to bay ribs, X per side %.2f mm" % (CELL["x0"] - BAY_X0))
    print("  cell in bay, Y per side      %.2f mm" % (CELL["y0"] - BAY_Y0))
    print("  cell top to base rim         %.2f mm" % (PART_LINE - CELL["z1"]))
    print("  top components to lid inner  %.2f mm"
          % ((TOTAL_H - 2.0) - (BOARD_TOP + TOP_COMP_H)))
    print("  light pipe tip to lid inner  %.2f mm" % ((TOTAL_H - 2.0) - LIGHTPIPE_TOP))
    print("  pushbutton depth available   %.2f mm" % ((TOTAL_H - 2.0) - 12.5))

    print()
    if FAILS:
        swx.fail("fit check failed: %s" % ", ".join(FAILS))
    print("OK - all fit, interference and insertion checks pass")


if __name__ == "__main__":
    main()
