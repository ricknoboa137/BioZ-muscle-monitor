# maze_route.py <board> <net> "ax,ay" "bx,by" [--width W] [--grid 0.1]
#                [--layers F.Cu,Signal,B.Cu] [--viacost 2.0] [--dry]
#
# WHY THIS EXISTS.  try_connect.py tries a catalogue of ~15 fixed shapes
# (direct, L, dogleg, offset corners).  On this board that closed 0 of 37 pairs
# -- and NOT because the board is full.  Measured: a 14.35 mm SWDIO run straight
# down B.Cu has exactly THREE blockers on it, all clustered at the far end.  The
# inner layers carry 34 segments (B.Cu) and 77 (Signal) against 317 on F.Cu.
# The space is there; a fixed-shape catalogue just cannot find the shape.
# So: a real grid maze router with the project's per-net-pair clearance model.
#
# IT IS NOT AN AUTOROUTER IN THE SENSE BRIEF SECTION 11 FORBIDS.  It routes ONE
# named net at a time, on layers named by the caller, at a width the caller
# fixes, and every emitted segment is then re-verified with the exact geometric
# check before anything is saved.  The hand-route-only nets of section 11 are
# not fed to it.
#
# CLEARANCE MODEL.  Obstacles are rasterised as their true shapes -- capsules
# for tracks, discs for vias, inflated rectangles for pads -- each at ITS OWN
# required clearance, which is max(clearance(our class), clearance(its class)),
# the real KiCad rule (see netclr.py).  The raster is deliberately CONSERVATIVE
# (inflated by half a grid step), and the exact check afterwards is what the
# result is actually judged on.
import sys, os, heapq, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pcbnew
from netclr import ClassRouter

args = sys.argv[1:]
def opt(n, d=None):
    return args[args.index(n) + 1] if n in args else d

path, net = args[0], args[1]
A = tuple(float(v) for v in args[2].split(","))
B = tuple(float(v) for v in args[3].split(","))
G = float(opt("--grid", "0.1"))
VIACOST = float(opt("--viacost", "2.0"))
DRY = "--dry" in args

R = ClassRouter(path)
b = R.board
W = float(opt("--width", R.trk.get(R.cls_of(net), R.trk["Default"])))
LAYNAMES = opt("--layers", "F.Cu,Signal,B.Cu").split(",")
LAYS = [b.GetLayerID(n) for n in LAYNAMES]
VIA_DIA, VIA_DRILL = 0.6, 0.3
NC = R.netcode(net)

bb = b.GetBoardEdgesBoundingBox()
T = pcbnew.ToMM
X0, Y0 = T(bb.GetLeft()), T(bb.GetTop())
X1, Y1 = T(bb.GetRight()), T(bb.GetBottom())
NX = int((X1 - X0) / G) + 1
NY = int((Y1 - Y0) / G) + 1
print("grid %dx%d at %.3f mm over (%.2f,%.2f)-(%.2f,%.2f), %d layers, w=%.4f"
      % (NX, NY, G, X0, Y0, X1, Y1, len(LAYS), W))

def to_ix(x, y):
    return int(round((x - X0) / G)), int(round((y - Y0) / G))
def to_mm(ix, iy):
    return X0 + ix * G, Y0 + iy * G

# ---- rasterise obstacles ------------------------------------------------
YY, XX = np.meshgrid(np.arange(NY), np.arange(NX), indexing="ij")
CX = X0 + XX * G
CY = Y0 + YY * G

def blank():
    return np.zeros((NY, NX), dtype=bool)

def mark_disc(m, cx, cy, r):
    i0 = max(0, int((cx - r - X0) / G) - 1); i1 = min(NX, int((cx + r - X0) / G) + 2)
    j0 = max(0, int((cy - r - Y0) / G) - 1); j1 = min(NY, int((cy + r - Y0) / G) + 2)
    if i1 <= i0 or j1 <= j0:
        return
    sub = ((CX[j0:j1, i0:i1] - cx) ** 2 + (CY[j0:j1, i0:i1] - cy) ** 2) <= r * r
    m[j0:j1, i0:i1] |= sub

def mark_capsule(m, x1, y1, x2, y2, r):
    L = math.hypot(x2 - x1, y2 - y1)
    n = max(1, int(L / (G * 0.5)) + 1)
    for k in range(n + 1):
        t = k / n
        mark_disc(m, x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, r)

def mark_rect(m, cx, cy, hw, hh, r):
    i0 = max(0, int((cx - hw - r - X0) / G) - 1); i1 = min(NX, int((cx + hw + r - X0) / G) + 2)
    j0 = max(0, int((cy - hh - r - Y0) / G) - 1); j1 = min(NY, int((cy + hh + r - Y0) / G) + 2)
    if i1 <= i0 or j1 <= j0:
        return
    m[j0:j1, i0:i1] = True

def build(lay, halfw):
    """blocked mask for an item of half-width halfw routed on layer lay"""
    m = blank()
    for f in b.Footprints():
        for p in f.Pads():
            if p.GetNetCode() == NC or not p.IsOnLayer(lay):
                continue
            req = R.pair_clearance(net, p.GetNetCode()) + halfw + G * 0.5
            c = p.GetCenter()
            pb = p.GetBoundingBox()
            mark_rect(m, T(c.x), T(c.y),
                      (T(pb.GetRight()) - T(pb.GetLeft())) / 2.0,
                      (T(pb.GetBottom()) - T(pb.GetTop())) / 2.0, req)
    for t in b.GetTracks():
        if t.GetNetCode() == NC or not t.IsOnLayer(lay):
            continue
        req = R.pair_clearance(net, t.GetNetCode()) + halfw + G * 0.5
        s, e = t.GetStart(), t.GetEnd()
        if isinstance(t, pcbnew.PCB_VIA):
            # GetWidth() bare asserts on a via and opens a blocking modal
            mark_disc(m, T(s.x), T(s.y), T(t.GetWidth(t.TopLayer())) / 2.0 + req)
        else:
            mark_capsule(m, T(s.x), T(s.y), T(e.x), T(e.y),
                         T(t.GetWidth()) / 2.0 + req)
    return m

print("rasterising...", flush=True)
track_mask = {L: build(L, W / 2.0) for L in LAYS}
# a via must clear on EVERY routing layer it passes through
via_each = {L: build(L, VIA_DIA / 2.0) for L in LAYS}
via_mask = np.zeros((NY, NX), dtype=bool)
for L in LAYS:
    via_mask |= via_each[L]

# keep everything inside the board outline, with a margin
edge = blank()
edge[:, :] = True
mi = int((0.5) / G)
edge[mi:NY - mi, mi:NX - mi] = False
for L in LAYS:
    track_mask[L] |= edge
via_mask |= edge

for L in LAYS:
    free = int((~track_mask[L]).sum())
    print("  %-8s free cells %d / %d (%.1f%%)"
          % (b.GetLayerName(L), free, NX * NY, 100.0 * free / (NX * NY)))

# ---- A* -----------------------------------------------------------------
sx, sy = to_ix(*A); gx, gy = to_ix(*B)
LI = {L: i for i, L in enumerate(LAYS)}
NL = len(LAYS)

def passable(ix, iy, li):
    return 0 <= ix < NX and 0 <= iy < NY and not track_mask[LAYS[li]][iy, ix]

# WHICH LAYER MAY AN ENDPOINT START ON.  This is load-bearing and the first
# version got it wrong: it happily started a run on In4 at the coordinates of an
# SMD pad that only exists on F.Cu, producing copper that touches nothing.  The
# save guard caught it (unconnected did not fall), but the fix is to constrain
# the search: an endpoint may only begin on a layer the item at that point is
# actually on.
def layers_at(pt):
    tol = 0.001
    best = None
    for f in b.Footprints():
        for p in f.Pads():
            if p.GetNetCode() != NC:
                continue
            c = p.GetCenter()
            if abs(T(c.x) - pt[0]) < 0.05 and abs(T(c.y) - pt[1]) < 0.05:
                best = [L for L in LAYS if p.IsOnLayer(L)]
    if best:
        return best
    # not a pad: a track or via end
    for t in b.GetTracks():
        if t.GetNetCode() != NC:
            continue
        for e in (t.GetStart(), t.GetEnd()):
            if abs(T(e.x) - pt[0]) < 0.05 and abs(T(e.y) - pt[1]) < 0.05:
                return [L for L in LAYS if t.IsOnLayer(L)]
    return list(LAYS)

SL = [LI[L] for L in layers_at(A) if L in LI]
GL = [LI[L] for L in layers_at(B) if L in LI]
if not SL or not GL:
    print("endpoint is not on any routing layer: start=%s goal=%s" % (SL, GL)); sys.exit(2)
print("start layers %s  goal layers %s"
      % ([b.GetLayerName(LAYS[i]) for i in SL], [b.GetLayerName(LAYS[i]) for i in GL]))

def snap(ix, iy, allowed):
    for rad in range(0, 8):
        for dx in range(-rad, rad + 1):
            for dy in range(-rad, rad + 1):
                if max(abs(dx), abs(dy)) != rad:
                    continue
                for li in allowed:
                    if passable(ix + dx, iy + dy, li):
                        return ix + dx, iy + dy, li
    return None

s = snap(sx, sy, SL); g = snap(gx, gy, GL)
if not s or not g:
    print("start or goal has no free cell on any routing layer"); sys.exit(2)
print("start %s  goal %s" % (s, g))

NB = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
      (-1, -1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (1, 1, 1.4142)]

def h(ix, iy):
    return math.hypot(ix - g[0], iy - g[1]) * G

start = (s[0], s[1], s[2])
dist = {start: 0.0}
prev = {}
pq = [(h(s[0], s[1]), 0.0, start)]
seen = set()
found = None
while pq:
    f, d, cur = heapq.heappop(pq)
    if cur in seen:
        continue
    seen.add(cur)
    if cur[0] == g[0] and cur[1] == g[1] and cur[2] in GL:
        found = cur; break
    ix, iy, li = cur
    for dx, dy, c in NB:
        nx_, ny_ = ix + dx, iy + dy
        if not passable(nx_, ny_, li):
            continue
        nd = d + c * G
        k = (nx_, ny_, li)
        if nd < dist.get(k, 1e18):
            dist[k] = nd; prev[k] = cur
            heapq.heappush(pq, (nd + h(nx_, ny_), nd, k))
    if not via_mask[iy, ix]:
        for nli in range(NL):
            if nli == li:
                continue
            if not passable(ix, iy, nli):
                continue
            nd = d + VIACOST
            k = (ix, iy, nli)
            if nd < dist.get(k, 1e18):
                dist[k] = nd; prev[k] = cur
                heapq.heappush(pq, (nd + h(ix, iy), nd, k))

if not found:
    print("NO ROUTE (explored %d nodes)" % len(seen)); sys.exit(2)

pathn = [found]
while pathn[-1] in prev:
    pathn.append(prev[pathn[-1]])
pathn.reverse()
print("route found: %d nodes, explored %d, length %.2f mm"
      % (len(pathn), len(seen), dist[found]))

# ---- collapse to segments + vias ---------------------------------------
segs = []   # (layer, (x1,y1), (x2,y2))
vias = []   # (x,y)
run = [pathn[0]]
for n in pathn[1:]:
    if n[2] != run[-1][2]:
        # layer change = via at this cell
        if len(run) > 1:
            segs.append((run[0][2], run[0], run[-1]))
        vias.append((run[-1][0], run[-1][1]))
        run = [n]
    else:
        # keep only direction changes
        if len(run) >= 2:
            ax_, ay_ = run[-1][0] - run[-2][0], run[-1][1] - run[-2][1]
            bx_, by_ = n[0] - run[-1][0], n[1] - run[-1][1]
            if (ax_, ay_) == (bx_, by_):
                run[-1] = n
                continue
        run.append(n)
if len(run) > 1:
    segs.append((run[0][2], run[0], run[-1]))

# rebuild as real polylines per layer run
poly = []
cur_li = pathn[0][2]
pts = [pathn[0]]
out = []
for n in pathn[1:]:
    if n[2] != cur_li:
        out.append((cur_li, pts + []))
        pts = [(n[0], n[1], n[2])]
        cur_li = n[2]
    else:
        pts.append(n)
out.append((cur_li, pts))

def simplify(pts):
    if len(pts) < 3:
        return [(p[0], p[1]) for p in pts]
    o = [(pts[0][0], pts[0][1])]
    for i in range(1, len(pts) - 1):
        a1 = (pts[i][0] - pts[i-1][0], pts[i][1] - pts[i-1][1])
        a2 = (pts[i+1][0] - pts[i][0], pts[i+1][1] - pts[i][1])
        if a1 != a2:
            o.append((pts[i][0], pts[i][1]))
    o.append((pts[-1][0], pts[-1][1]))
    return o

# STRING-PULL SMOOTHING.  A grid A* result is a staircase of 0.1 mm jogs, which
# is legal but is poor copper: needlessly long, dozens of segments, and every
# jog is a discontinuity.  Greedily replace runs of points with a single
# straight segment wherever the EXACT clearance check allows it -- so smoothing
# can never introduce a violation, it can only remove geometry.
def smooth(mmpts, lay):
    if len(mmpts) < 3:
        return mmpts
    o = [mmpts[0]]
    i = 0
    while i < len(mmpts) - 1:
        j = len(mmpts) - 1
        while j > i + 1:
            if R.seg_clear_c(mmpts[i], mmpts[j], W, net, lay):
                break
            j -= 1
        o.append(mmpts[j])
        i = j
    return o

plan = []
for li, pts in out:
    sp = simplify(pts)
    mmpts = [to_mm(ix, iy) for ix, iy in sp]
    lay = LAYS[li]
    n0 = len(mmpts)
    mmpts = smooth(mmpts, lay)
    print("  smoothed %s: %d -> %d points" % (b.GetLayerName(lay), n0, len(mmpts)))
    plan.append((lay, mmpts))

# stitch the real pad centres onto the ends
plan[0] = (plan[0][0], [A] + plan[0][1])
plan[-1] = (plan[-1][0], plan[-1][1] + [B])

vialist = []
for i in range(len(plan) - 1):
    vialist.append(plan[i][1][-1])

print("plan: %d layer runs, %d vias" % (len(plan), len(vialist)))
bad = 0
for lay, pts in plan:
    print("  %s: %s" % (b.GetLayerName(lay),
                        " -> ".join("(%.3f,%.3f)" % p for p in pts)))
    for p, q in zip(pts, pts[1:]):
        if p == q:
            continue
        if not R.seg_clear_c(p, q, W, net, lay):
            print("     EXACT CHECK FAILED on (%.3f,%.3f)-(%.3f,%.3f)" % (p + q))
            bad += 1
if bad:
    print("ABORT: %d segments fail the exact clearance check -- nothing changed" % bad)
    sys.exit(1)
if DRY:
    print("(dry run)"); sys.exit(0)

def unconnected():
    cd = b.GetConnectivity(); cd.Build(b)
    return cd.GetUnconnectedCount(True)
before = unconnected()

for lay, pts in plan:
    for p, q in zip(pts, pts[1:]):
        if p != q:
            R.add_track(NC, lay, p, q, W)
for vx, vy in vialist:
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(vx), pcbnew.FromMM(vy)))
    v.SetWidth(pcbnew.FromMM(VIA_DIA))
    v.SetDrill(pcbnew.FromMM(VIA_DRILL))
    v.SetNetCode(NC)
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    b.Add(v)

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
after = unconnected()
print("unconnected %d -> %d" % (before, after))
if after >= before:
    print("ABORT: did not reduce the unconnected count. Not saving.")
    sys.exit(1)
b.Save(path)
print("saved", path)
