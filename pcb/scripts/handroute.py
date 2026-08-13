"""Collision-checked primitives for hand routing this board.

This is NOT an autorouter.  There is no rip-up, no net ordering, no cost
function and no search over topology.  It places exactly the geometry the
caller asks for, and refuses to place it if it would violate clearance -- which
is the part a human does badly and slowly by hand, and the reason the earlier
hand-scripted routing produced shorts and crossings that DRC had to catch.

Clearance model is deliberately conservative: one global figure (default
0.20 mm, the largest net-class clearance on the board bar POWER_HIGH) applied
to every other-net copper item on every layer the new item touches.  Board
edge is kept at 0.25 mm per min_copper_edge_clearance.
"""
import os
import pcbnew

PCBDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD_FILE = os.path.join(PCBDIR, "BioZ-Muscle-Monitor.kicad_pcb")

mm = pcbnew.FromMM
T = pcbnew.ToMM
CLEAR = 0.20
EDGE_CLEAR = 0.25

LAYER_BY_NAME = {}


def V(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


class Router:
    def __init__(self, path=BOARD_FILE):
        self.path = path
        self.board = pcbnew.LoadBoard(path)
        self.added = []
        for lid in self.board.GetEnabledLayers().CuStack():
            LAYER_BY_NAME[self.board.GetLayerName(lid)] = lid
        self.edge = self._edge_outline()

    # -- lookups ----------------------------------------------------------
    def fp(self, ref):
        return next(f for f in self.board.Footprints() if f.GetReference() == ref)

    def pad(self, ref, num):
        return next(p for p in self.fp(ref).Pads() if p.GetNumber() == str(num))

    def padxy(self, ref, num):
        p = self.pad(ref, num).GetPosition()
        return (T(p.x), T(p.y))

    def netcode(self, name):
        n = self.board.FindNet(name)
        if n is None:
            raise KeyError("no such net: %s" % name)
        return n.GetNetCode()

    def layer(self, name):
        return LAYER_BY_NAME[name]

    def _edge_outline(self):
        """board extents from Edge.Cuts, as mm.  Only SHAPE_SEGMENT exposes the
        generic Collide(SHAPE, clearance) in the swig bindings, so edge distance
        is done as a bounding-box inset rather than a true outline collision.
        The outline is a 62 x 44 rounded rectangle, so an inset is exact except
        at the four corner radii, where it is conservative."""
        # BOX2I.Merge mutates and returns None under swig, so accumulate by hand
        xs, ys = [], []
        for d in self.board.GetDrawings():
            if d.GetLayer() != pcbnew.Edge_Cuts:
                continue
            bb = d.GetBoundingBox()
            xs += [T(bb.GetLeft()), T(bb.GetRight())]
            ys += [T(bb.GetTop()), T(bb.GetBottom())]
        if not xs:
            raise RuntimeError("no Edge.Cuts geometry found")
        return (min(xs), min(ys), max(xs), max(ys))

    # -- clearance --------------------------------------------------------
    def _obstacles(self, layers, netcode):
        """every copper item of a DIFFERENT net present on any of `layers`"""
        out = []
        for f in self.board.Footprints():
            for p in f.Pads():
                if p.GetNetCode() == netcode:
                    continue
                for lay in layers:
                    if p.IsOnLayer(lay):
                        out.append(p.GetEffectiveShape(lay))
                        break
        for t in self.board.GetTracks():
            if t.GetNetCode() == netcode:
                continue
            for lay in layers:
                if t.IsOnLayer(lay):
                    out.append(t.GetEffectiveShape(lay))
                    break
        return out

    def _edge_ok(self, pts, halfwidth):
        x1, y1, x2, y2 = self.edge
        m = halfwidth + EDGE_CLEAR
        for (x, y) in pts:
            if not (x1 + m <= x <= x2 - m and y1 + m <= y <= y2 - m):
                return False
        return True

    def in_rule_area(self, x, y, margin=0.0):
        """rule areas (GND_SPLIT, U1_ESCAPE, ANTENNA_KEEPOUT) forbid vias.
        Placing one inside is an 'items not allowed' DRC error, and in the case
        of GND_SPLIT it would also short the two ground systems together."""
        for z in self.board.Zones():
            if not z.GetIsRuleArea():
                continue
            if z.Outline().Collide(V(x, y), mm(margin)):
                return z.GetZoneName() or "unnamed rule area"
        return None

    def hole_conflict(self, x, y, drill, extra=(), min_gap=0.25):
        """hole-to-hole against every existing via AND every pad hole, plus any
        (x, y, drill) tuples in `extra` for vias queued in this run.  The board
        minimum is 0.2 mm; 0.25 is used to leave margin for rounding."""
        for t in self.board.GetTracks():
            if t.GetClass() != "PCB_VIA":
                continue
            q = t.GetPosition()
            need = (drill + T(t.GetDrill())) / 2.0 + min_gap
            if (T(q.x) - x) ** 2 + (T(q.y) - y) ** 2 < need ** 2:
                return True
        for f in self.board.Footprints():
            for p in f.Pads():
                dh = T(p.GetDrillSizeX())
                if dh <= 0:
                    continue
                q = p.GetPosition()
                need = (drill + dh) / 2.0 + min_gap
                if (T(q.x) - x) ** 2 + (T(q.y) - y) ** 2 < need ** 2:
                    return True
        for (ax, ay, ad) in extra:
            need = (drill + ad) / 2.0 + min_gap
            if (ax - x) ** 2 + (ay - y) ** 2 < need ** 2:
                return True
        return False

    def via_clear(self, x, y, dia, netcode, layers, clearance=CLEAR):
        # a via is modelled as a zero-length segment of the via's diameter:
        # SHAPE_SEGMENT is the only shape exposing Collide(SHAPE, clearance)
        sh = pcbnew.SHAPE_SEGMENT(V(x, y), V(x, y), mm(dia))
        if not self._edge_ok([(x, y)], dia / 2.0):
            return False
        for o in self._obstacles(layers, netcode):
            if sh.Collide(o, mm(clearance)):
                return False
        return True

    def seg_clear(self, a, c, w, netcode, layer, clearance=CLEAR):
        sh = pcbnew.SHAPE_SEGMENT(V(*a), V(*c), mm(w))
        if not self._edge_ok([a, c], w / 2.0):
            return False
        for o in self._obstacles([layer], netcode):
            if sh.Collide(o, mm(clearance)):
                return False
        return True

    # -- placement --------------------------------------------------------
    def add_track(self, net, layer, a, c, w):
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(V(*a)); t.SetEnd(V(*c))
        t.SetWidth(mm(w)); t.SetLayer(layer)
        t.SetNetCode(self.netcode(net) if isinstance(net, str) else net)
        self.board.Add(t)
        self.added.append(t)
        return t

    def add_via(self, net, x, y, dia=0.4, drill=0.25,
                top=pcbnew.F_Cu, bot=pcbnew.B_Cu, micro=False):
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(V(x, y)); v.SetDrill(mm(drill)); v.SetWidth(mm(dia))
        v.SetViaType(pcbnew.VIATYPE_MICROVIA if micro else pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(top, bot)
        v.SetNetCode(self.netcode(net) if isinstance(net, str) else net)
        self.board.Add(v)
        self.added.append(v)
        return v

    def polyline(self, net, layer, pts, w, clearance=CLEAR):
        """place a polyline, checking every segment first; all-or-nothing"""
        nc = self.netcode(net) if isinstance(net, str) else net
        for a, c in zip(pts, pts[1:]):
            if a == c:
                continue
            if not self.seg_clear(a, c, w, nc, layer, clearance):
                return False
        for a, c in zip(pts, pts[1:]):
            if a != c:
                self.add_track(nc, layer, a, c, w)
        return True

    # -- output -----------------------------------------------------------
    def save(self, refill=True):
        if refill:
            pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())
        self.board.Save(self.path)
