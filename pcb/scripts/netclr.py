"""Per-net-class clearance model.

Fixes the bug that cost entry 19/20: clearance is NOT one number.  The rule
KiCad actually applies between two copper items is

    required = max(clearance(class of item A), clearance(class of item B))

The first attempt hardcoded 0.20 and put an nCHG via 0.225 mm from a V_SYS
track -- V_SYS is POWER_HIGH at 0.254, so that was a real error.  The second
attempt over-corrected to a blanket 0.254 everywhere, which is safe but wrong
in the other direction: GND_A, GND_D and Default are all 0.15, and the ground
pours and their tracks are the single most common obstacle on this board.
Checking against them at 0.254 throws away 0.104 mm per side -- decisive in a
0.40 mm fanout channel.

Both numbers here are read from the project file at run time.  Nothing is
hardcoded and nothing is relaxed: every check uses that net pair's real
minimum, no more and no less.
"""
import os
import json
import pcbnew
from handroute import Router, PCBDIR, mm, T, V

PRO = os.path.join(PCBDIR, "BioZ-Muscle-Monitor.kicad_pro")


def load_classes():
    d = json.load(open(PRO))
    ns = d["net_settings"]
    clr = {c["name"]: float(c["clearance"]) for c in ns["classes"]}
    trk = {c["name"]: float(c["track_width"]) for c in ns["classes"]}
    net2cls = {p["pattern"]: p["netclass"] for p in ns.get("netclass_patterns", [])}
    rules = d["board"]["design_settings"]["rules"]
    return clr, trk, net2cls, rules


class ClassRouter(Router):
    """Router whose clearance checks resolve per obstacle net."""

    def __init__(self, path=None):
        super().__init__(path) if path else super().__init__()
        self.clr, self.trk, self.net2cls, self.rules = load_classes()
        self.min_track = float(self.rules["min_track_width"])
        self.min_clear = float(self.rules["min_clearance"])
        self._name_cache = {}

    # -- class resolution -------------------------------------------------
    def cls_of(self, netname):
        return self.net2cls.get(netname, "Default")

    def clr_of_net(self, netname):
        return self.clr.get(self.cls_of(netname), self.clr["Default"])

    def clr_of_code(self, netcode):
        if netcode not in self._name_cache:
            n = self.board.FindNet(netcode)
            self._name_cache[netcode] = n.GetNetname() if n else ""
        return self.clr_of_net(self._name_cache[netcode])

    def pair_clearance(self, my_net, other_code):
        """the real KiCad rule: the larger of the two classes' clearances"""
        return max(self.clr_of_net(my_net), self.clr_of_code(other_code))

    def min_width_for(self, netname):
        """thinnest legal track for this net: the board minimum.  The class
        track_width is a nominal/preferred width, not a floor -- the floor is
        design_settings.rules.min_track_width.  Used only to squeeze through a
        gap that the nominal width will not fit, same technique as the WLP
        escape."""
        return self.min_track

    # -- obstacle iteration with per-item clearance ------------------------
    def _layer_cache(self, lay):
        """all copper items on one layer, as (shape, netcode, bbox-in-mm).

        Built once per layer and reused.  The previous version rebuilt the
        whole ~600-item list on every single segment check, which made any
        catalogue larger than a few hundred candidates unusable.  Invalidated
        by _invalidate() whenever geometry is added.
        """
        if not hasattr(self, "_lc"):
            self._lc = {}
        if lay in self._lc:
            return self._lc[lay]
        items = []
        for f in self.board.Footprints():
            for p in f.Pads():
                if p.IsOnLayer(lay):
                    bb = p.GetBoundingBox()
                    items.append((p.GetEffectiveShape(lay), p.GetNetCode(),
                                  (T(bb.GetLeft()), T(bb.GetTop()),
                                   T(bb.GetRight()), T(bb.GetBottom()))))
        for t in self.board.GetTracks():
            if t.IsOnLayer(lay):
                bb = t.GetBoundingBox()
                items.append((t.GetEffectiveShape(lay), t.GetNetCode(),
                              (T(bb.GetLeft()), T(bb.GetTop()),
                               T(bb.GetRight()), T(bb.GetBottom()))))
        self._lc[lay] = items
        return items

    def _invalidate(self):
        if hasattr(self, "_lc"):
            self._lc = {}

    def _obstacles_tagged(self, layers, netcode):
        """(shape, obstacle_netcode) for every different-net copper item"""
        out = []
        seen = set()
        for lay in layers:
            for sh, code, bb in self._layer_cache(lay):
                if code == netcode or id(sh) in seen:
                    continue
                seen.add(id(sh))
                out.append((sh, code))
        return out

    def _near(self, lay, netcode, box, pad):
        """different-net items on `lay` whose bbox is within `pad` mm of box"""
        x1, y1, x2, y2 = box
        for sh, code, (bx1, by1, bx2, by2) in self._layer_cache(lay):
            if code == netcode:
                continue
            if bx2 + pad < x1 or bx1 - pad > x2 or by2 + pad < y1 or by1 - pad > y2:
                continue
            yield sh, code

    def via_clear_c(self, x, y, dia, my_net, layers):
        sh = pcbnew.SHAPE_SEGMENT(V(x, y), V(x, y), mm(dia))
        if not self._edge_ok([(x, y)], dia / 2.0):
            return False
        nc = self.netcode(my_net)
        for o, ocode in self._obstacles_tagged(layers, nc):
            if sh.Collide(o, mm(self.pair_clearance(my_net, ocode))):
                return False
        return True

    def seg_clear_c(self, a, c, w, my_net, layer):
        sh = pcbnew.SHAPE_SEGMENT(V(*a), V(*c), mm(w))
        if not self._edge_ok([a, c], w / 2.0):
            return False
        nc = self.netcode(my_net)
        myclr = self.clr_of_net(my_net)
        # widest clearance any net on this board can demand, as the bbox pad
        pad = max(self.clr.values()) + w / 2.0 + 0.01
        box = (min(a[0], c[0]), min(a[1], c[1]), max(a[0], c[0]), max(a[1], c[1]))
        for o, ocode in self._near(layer, nc, box, pad):
            if sh.Collide(o, mm(max(myclr, self.clr_of_code(ocode)))):
                return False
        return True

    def polyline_c(self, my_net, layer, pts, w):
        """all-or-nothing polyline with per-obstacle clearance"""
        for a, c in zip(pts, pts[1:]):
            if a == c:
                continue
            if not self.seg_clear_c(a, c, w, my_net, layer):
                return False
        nc = self.netcode(my_net)
        for a, c in zip(pts, pts[1:]):
            if a != c:
                self.add_track(nc, layer, a, c, w)
        self._invalidate()
        return True

    def add_via(self, *a, **k):
        v = super().add_via(*a, **k)
        self._invalidate()
        return v
