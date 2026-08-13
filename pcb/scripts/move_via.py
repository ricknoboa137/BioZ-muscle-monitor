# move_via.py <board> <x_mm> <y_mm> <newx_mm> <newy_mm> [--place]
# Moves a via and drags every track endpoint that sits exactly on it, so the
# connection is preserved.  Geometry only -- no width, net or topology change.
#
# Session 11 use: the AFE_PWR_EN through via at (31.200,11.400) sits 0.550 mm
# from the ANT feed run at x=30.400, against an rf_clearance floor of 0.600.  It
# is an ordinary signal via with no part in the RF circuit -- the ONE genuine
# rf_clearance defect once the land-pattern cases are correctly scoped out -- so
# the via moves, not the RF chain (brief 11 category 1: hand-route only).
# Moving it to x=31.310 gives centre distance 0.910 and a gap of 0.660.
import sys, pcbnew

NM = pcbnew.FromMM
def mm(v): return pcbnew.ToMM(v)

def near(p, x, y, tol=1000):     # 1 micron
    return abs(p.x - x) < tol and abs(p.y - y) < tol

def main():
    path = sys.argv[1]
    x, y, nx, ny = (NM(float(v)) for v in sys.argv[2:6])
    place = "--place" in sys.argv
    b = pcbnew.LoadBoard(path)
    new = pcbnew.VECTOR2I(nx, ny)
    moved_via = 0
    moved_ends = 0
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            if near(t.GetPosition(), x, y):
                print(f"  via [{t.GetNetname()}] ({mm(x):.3f},{mm(y):.3f}) -> "
                      f"({mm(nx):.3f},{mm(ny):.3f})")
                if place: t.SetPosition(new)
                moved_via += 1
        else:
            for get, set_ in ((t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)):
                if near(get(), x, y):
                    print(f"  track [{t.GetNetname()}] endpoint dragged with it")
                    if place: set_(new)
                    moved_ends += 1
    if moved_via == 0:
        sys.exit(f"ERROR: no via at ({mm(x):.3f},{mm(y):.3f}) -- refusing to run")
    print(f"{'moved' if place else 'would move'} {moved_via} via(s), "
          f"{moved_ends} attached track endpoint(s)")
    if place:
        b.Save(path)
        print("saved:", path)

main()
