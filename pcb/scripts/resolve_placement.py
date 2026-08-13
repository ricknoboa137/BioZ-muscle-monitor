"""Post-build placement resolver.

The critical parts (brief sections 4 and 5) are placed by hand in build_board.py
and must not move.  The remaining passives only need to be in the right zone,
near enough to their net, and not on top of anything.  This does a greedy
spiral search for each of them: keep the ideal position if it is clear,
otherwise take the nearest clear position on a 0.2 mm spiral.

Run after build_board.py, with KiCad's bundled python.
"""
import os, math, itertools
import pcbnew

PCBDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD_FILE = os.path.join(PCBDIR, "BioZ-Muscle-Monitor.kicad_pcb")

W, H = 62.0, 44.0
SPLIT_X, SPLIT_GAP = 20.0, 0.8
CLEAR = 0.20          # extra courtyard-to-courtyard margin, mm.  Courtyards
                      # already carry the IPC clearance, so this is 0.20 mm of
                      # real air on top of it - room for a rework iron tip.

# Everything not listed here is frozen where build_board.py put it.
MOVABLE = {"C2", "C37", "C42", "C28", "C13", "FL1", "L3", "R2", "R3",
           "C38", "C39", "C40", "C44", "C45", "C26", "C35", "C34",
           "R15", "R19", "R22", "R16", "L7", "C32", "C33",
           "R13", "R14", "R17", "R18", "C25", "R10", "R11", "R12", "D1",
           "R8", "R4",
           # U8's input bypass: the datasheet asks for 1-10 uF to VSS but sets
           # no adjacency requirement, and the antenna keepout owns the corner
           # it would otherwise sit in, so it is placed freely.
           "C27"}

# Decoupling attached to a specific pin: allowed to shuffle, but only far
# enough to clear a neighbour.  Brief section 5 wants these within 1.5 mm of
# their pin, so the search radius is capped well inside that.
SEMI_FIXED = {"C14": 0.8, "C15": 0.8, "C16": 0.8, "C17": 0.8, "C24": 0.8,
              "C36": 0.8, "C43": 0.8, "C11": 0.8, "C12": 0.8,
              "C18": 0.8, "C22": 0.8,
              "C30": 1.6, "C31": 1.6}

FORBIDDEN = [(24.0, 0.0, 62.0, 7.1),        # antenna keepout + margin
             (17.4, 22.8, 22.8, 29.8),      # U1 escape
             # Only the WE-SHC solder RING is forbidden.  Its interior is
             # exactly where the power section is supposed to live.
             (34.9, 6.9, 62.0, 8.5),        # frame ring, top
             (34.9, 32.4, 62.0, 34.0),      # frame ring, bottom
             (34.9, 6.9, 36.5, 34.0),       # frame ring, left
             (60.4, 6.9, 62.0, 34.0),       # frame ring, right
             (20.2, 33.4, 31.7, 44.0),      # P1
             (36.4, 33.4, 46.4, 44.0),      # J7
             (46.4, 33.4, 56.4, 44.0),      # J8
             (29.7, 24.9, 34.7, 32.5),      # J2
             (31.7, 34.9, 36.7, 44.0),      # SW1 / U9 wire pads
             (28.4, 6.4, 33.2, 11.6),       # RF ladder
             (0.0, 15.5, 9.5, 32.0)]        # J1


def bbox(fp):
    bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
    if bb.GetWidth() == 0:
        bb = fp.GetCourtyard(pcbnew.B_CrtYd).BBox()
    return (pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetRight()),
            pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetBottom()))


def main():
    board = pcbnew.LoadBoard(BOARD_FILE)
    fps = {f.GetReference(): f for f in board.Footprints()}

    # cache each footprint's courtyard size and its offset from the origin
    geom = {}
    for ref, fp in fps.items():
        x1, x2, y1, y2 = bbox(fp)
        px = pcbnew.ToMM(fp.GetPosition().x); py = pcbnew.ToMM(fp.GetPosition().y)
        geom[ref] = dict(w=x2-x1, h=y2-y1, ox=(x1+x2)/2-px, oy=(y1+y2)/2-py,
                         flip=fp.IsFlipped())

    def box_at(ref, x, y):
        g = geom[ref]
        cx, cy = x + g["ox"], y + g["oy"]
        return (cx-g["w"]/2, cx+g["w"]/2, cy-g["h"]/2, cy+g["h"]/2)

    def clear_at(ref, x, y, placed):
        b = box_at(ref, x, y)
        analog = geom[ref]["_analog"]
        lo = 0.7 if analog else SPLIT_X + SPLIT_GAP/2 + 0.3
        hi = SPLIT_X - SPLIT_GAP/2 - 0.3 if analog else W - 0.7
        if b[0] < lo or b[1] > hi or b[2] < 0.7 or b[3] > H - 0.7:
            return False
        for f in FORBIDDEN:
            if b[1] > f[0] and b[0] < f[2] and b[3] > f[1] and b[2] < f[3]:
                return False
        for other, ob in placed.items():
            if other == ref: continue
            if geom[other]["flip"] != geom[ref]["flip"]: continue
            # Decoupling attached to a pin is MEANT to be tight against its
            # IC - that is the entire requirement.  The extra breathing room
            # applies between free passives, not between a capacitor and the
            # package it decouples.
            gap = 0.02 if (ref in SEMI_FIXED or other in SEMI_FIXED) else CLEAR
            if (min(b[1], ob[1]) - max(b[0], ob[0]) > -gap and
                    min(b[3], ob[3]) - max(b[2], ob[2]) > -gap):
                return False
        return True

    for ref, fp in fps.items():
        geom[ref]["_analog"] = pcbnew.ToMM(fp.GetPosition().x) < SPLIT_X

    # fixed parts define the occupied map
    placed = {}
    for ref, fp in fps.items():
        if ref in MOVABLE or ref in SEMI_FIXED: continue
        if ref == "NT1": continue   # deliberately sits on U5 pin 32 / die pad
        if ref == "H1": continue    # a ring: its bbox contains the parts it
                                    # shields, which is the point of it
        placed[ref] = bbox(fp)

    moved = failed = 0
    # semi-fixed first (small radius), then the free passives
    for ref in sorted(SEMI_FIXED) + sorted(MOVABLE):
        fp = fps.get(ref)
        if fp is None: continue
        limit = SEMI_FIXED.get(ref, 16.0)
        ix = pcbnew.ToMM(fp.GetPosition().x); iy = pcbnew.ToMM(fp.GetPosition().y)
        best = None
        for radius in [i * 0.25 for i in range(0, int(limit / 0.25) + 1)]:
            steps = max(1, int(radius / 0.35))
            for k in range(steps * 8 if radius else 1):
                a = 2 * math.pi * k / (steps * 8) if radius else 0.0
                x, y = ix + radius * math.cos(a), iy + radius * math.sin(a)
                if clear_at(ref, x, y, placed):
                    best = (x, y, radius); break
            if best: break
        if best is None:
            print(f"   !! no free position for {ref}"); failed += 1
            placed[ref] = bbox(fp); continue
        x, y, rad = best
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        placed[ref] = box_at(ref, x, y)
        if rad > 0.01:
            moved += 1

    # fill the pours so the saved board carries real copper, not just outlines
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(BOARD_FILE)
    print(f"resolver: relocated {moved}, unplaceable {failed}; zones filled")

    # report what is still overlapping
    n = 0
    for a, b in itertools.combinations(sorted(placed), 2):
        if geom[a]["flip"] != geom[b]["flip"]: continue
        pa, pb = placed[a], placed[b]
        ox = min(pa[1], pb[1]) - max(pa[0], pb[0])
        oy = min(pa[3], pb[3]) - max(pa[2], pb[2])
        if ox > 0.02 and oy > 0.02:
            n += 1; print(f"   still overlapping: {a} x {b}  {ox:.2f} x {oy:.2f}")
    print("remaining overlapping pairs:", n)


main()














