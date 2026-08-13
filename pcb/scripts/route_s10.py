"""Session-10 hand-routing driver: closes ONE unconnected pair per invocation.

This is not an autorouter.  There is no rip-up and no global search: it tries a
small, explicit catalogue of geometries that a person would try by hand, checks
every one against the board's REAL per-net-class clearance (netclr.ClassRouter),
and places the first that is clear.  The arbiter of whether the result is good
is kicad-cli DRC, run by the caller after every single placement -- see
route_s10_driver.sh.  Anything that raises an error or fails to reduce the
unconnected count is reverted, which is also the pour-severance guard entry 20
demands (a DRC-clean thin track can sever a pour and orphan pads; only the
unconnected count moves).

Width floors are the binding .kicad_dru minimums, NOT the class nominals and
NOT netclr.min_width_for(), which entry 25 proved untrustworthy:
    POWER_HIGH / POWER_LOW  0.508   (rule power_width, 20mil)
    SIGNAL                  0.254   (rule signal_width, 10mil)
    PATIENT                 0.3048  (rule patient_width, 12mil)
    anything else           0.127   (rule general_track_width)
    inside U1_ESCAPE        0.075   (rule wlp_track_width)

Vias are 0.50/0.30 -- drill 0.30 is the floor from rule through_via_min_drill
outside U1_ESCAPE, and 0.10 annulus clears min_via_annular_width 0.05.

Usage:  python route_s10.py <pair_index> [--place]
"""
import os
import sys
import json
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from netclr import ClassRouter, T, PCBDIR

PAIRS_JSON = os.path.join(PCBDIR, "pairs-s10.json")

VIA_D, VIA_DR = 0.50, 0.30

WIDTH_FLOOR = {
    "POWER_HIGH": 0.508,
    "POWER_LOW": 0.508,
    "SIGNAL": 0.254,
    "PATIENT": 0.3048,
}
GENERAL_FLOOR = 0.127

# planes: net name -> (layer name, island bbox) is discovered live, not assumed
PLANE_LAYERS = ("GND", "Power")


def load_pairs():
    return json.load(open(PAIRS_JSON))


class PairRouter(ClassRouter):
    def __init__(self):
        super().__init__()
        self.F = pcbnew.F_Cu
        self.B = pcbnew.B_Cu
        self.SIG = self.layer("Signal")
        self.ALLCU = list(self.board.GetEnabledLayers().CuStack())
        self._planes = None

    # -- widths -----------------------------------------------------------
    def floor_for(self, net):
        return WIDTH_FLOOR.get(self.cls_of(net), GENERAL_FLOOR)

    def widths_for(self, net):
        """legal widths to try, widest (preferred) first"""
        fl = self.floor_for(net)
        nom = self.trk.get(self.cls_of(net), fl)
        out = []
        for w in (nom, 0.508, 0.4, 0.3, 0.254, 0.2, 0.15, fl):
            w = round(w, 4)
            if w >= fl - 1e-9 and w not in out:
                out.append(w)
        return sorted(set(out), reverse=True)

    # -- planes -----------------------------------------------------------
    def planes(self):
        """live map netname -> list of (layer_id, ZONE) for filled plane zones"""
        if self._planes is None:
            m = {}
            for lname in PLANE_LAYERS:
                lid = self.layer(lname)
                for z in self.board.Zones():
                    if z.GetIsRuleArea() or not z.IsOnLayer(lid):
                        continue
                    m.setdefault(z.GetNetname(), []).append((lid, z))
            self._planes = m
        return self._planes

    def in_plane(self, net, x, y):
        """is (x,y) inside this net's own filled plane island?"""
        for lid, z in self.planes().get(net, []):
            if z.Outline().Collide(pcbnew.VECTOR2I(pcbnew.FromMM(x),
                                                   pcbnew.FromMM(y)),
                                   pcbnew.FromMM(0.0)):
                return lid
        return None

    # -- via legality -----------------------------------------------------
    def via_ok(self, net, x, y, extra=()):
        if self.in_rule_area(x, y, VIA_D / 2.0):
            return False
        if self.hole_conflict(x, y, VIA_DR, extra=extra):
            return False
        return self.via_clear_c(x, y, VIA_D, net, self.ALLCU)

    # -- pad lead-out -----------------------------------------------------
    def pad_at(self, x, y, tol=0.02):
        """the pad whose centre is at (x,y), if any"""
        for f in self.board.Footprints():
            for p in f.Pads():
                q = p.GetPosition()
                if abs(T(q.x) - x) < tol and abs(T(q.y) - y) < tol:
                    return f, p
        return None, None

    def leadouts(self, x, y, net):
        """Entry 20's bug (a): a path starting at a pad CENTRE has its first leg
        cross that pad's own fine-pitch neighbours, so every candidate fails for
        a reason that has nothing to do with the route.  A real escape leaves
        the pad RADIALLY -- straight out of the package, along the pin axis,
        which is the one direction where the neighbouring pins are lateral.
        Returns [(leadout_point, stub_or_None), ...], nearest first, always
        including the bare centre so nothing is lost."""
        f, p = self.pad_at(x, y)
        if p is None:
            return [((x, y), None)]
        fc = f.GetPosition()
        vx, vy = x - T(fc.x), y - T(fc.y)
        # snap the outward direction to the pin axis: whichever of x/y dominates
        if abs(vx) >= abs(vy):
            dx, dy = (1.0 if vx >= 0 else -1.0), 0.0
        else:
            dx, dy = 0.0, (1.0 if vy >= 0 else -1.0)
        sz = p.GetSize(p.GetPrincipalLayer())
        half = max(T(sz.x), T(sz.y)) / 2.0
        w = self.floor_for(net)
        out = []
        d = half + 0.05
        while d <= half + 2.0:
            q = (round(x + dx * d, 4), round(y + dy * d, 4))
            if self.seg_clear_c((x, y), q, w, net, self.F):
                out.append((q, ((x, y), q, w)))
            d += 0.1
        out.append(((x, y), None))
        return out

    # -- shape catalogue --------------------------------------------------
    def shapes(self, a, c, span=6.0, step=0.1):
        """straight, both L's, and perpendicular detours at every offset.
        Entry 20: a 0.1 mm grid can step over a 0.025 mm channel, so a failure
        here is not proof no path exists -- it is proof none exists on this
        grid.  Reported as such."""
        out = [[a, c]]
        if a[0] != c[0] and a[1] != c[1]:
            out.append([a, (c[0], a[1]), c])
            out.append([a, (a[0], c[1]), c])
        n = int(span / step)
        for i in range(1, n + 1):
            for sgn in (1, -1):
                d = sgn * i * step
                out.append([a, (a[0], a[1] + d), (c[0], c[1] + d), c])
                out.append([a, (a[0] + d, a[1]), (c[0] + d, c[1]), c])
        return out

    # -- strategies -------------------------------------------------------
    def try_plane(self, net, a, c, ends_on_plane):
        """S0: drop a via at each endpoint into this net's own plane island.
        Closes power and ground pairs with no track at all, which is how a
        plane is supposed to be used and costs no routing channel."""
        need = []
        for p, already in ((a, ends_on_plane[0]), (c, ends_on_plane[1])):
            if already:
                continue
            if self.in_plane(net, p[0], p[1]) is None:
                return None
            need.append(p)
        if not need:
            return None
        extra = []
        for p in need:
            if not self.via_ok(net, p[0], p[1], extra=extra):
                return None
            extra.append((p[0], p[1], VIA_DR))
        for p in need:
            self.add_via(net, p[0], p[1], VIA_D, VIA_DR)
        return "plane-via x%d" % len(need)

    def try_plane_offset(self, net, a, c, ends_on_plane, reach=3.0, step=0.05):
        """S0b: same as S0 but the via sits up to `reach` mm off the endpoint,
        joined by a short stub -- a pad centre is often unusable for a 0.30 mm
        drill while a point 0.5 mm away is fine."""
        w = self.floor_for(net)
        placed_desc = []
        pending = []
        extra = []
        for p, already in ((a, ends_on_plane[0]), (c, ends_on_plane[1])):
            if already:
                continue
            spot = None
            n = int(reach / step)
            dirs = [(0, -1), (0, 1), (-1, 0), (1, 0),
                    (1, 1), (1, -1), (-1, 1), (-1, -1)]
            # 16 directions, not 8: on a board this congested the free spot is
            # as often off-axis as on it, and a via costs nothing extra there.
            dirs += [(2, 1), (2, -1), (-2, 1), (-2, -1),
                     (1, 2), (1, -2), (-1, 2), (-1, -2)]
            for i in range(0, n + 1):
                for dx, dy in dirs:
                    q = (round(p[0] + dx * i * step, 4),
                         round(p[1] + dy * i * step, 4))
                    if self.in_plane(net, q[0], q[1]) is None:
                        continue
                    if not self.via_ok(net, q[0], q[1], extra=extra):
                        continue
                    if q != p and not self.seg_clear_c(p, q, w, net, self.F):
                        continue
                    spot = q
                    break
                if spot:
                    break
            if spot is None:
                return None
            pending.append((p, spot))
            extra.append((spot[0], spot[1], VIA_DR))
        if not pending:
            return None
        for p, q in pending:
            if q != p:
                self.add_track(net, self.F, p, q, w)
            self.add_via(net, q[0], q[1], VIA_D, VIA_DR)
            placed_desc.append("via@%.3f,%.3f" % q)
        return "plane-via-offset " + " ".join(placed_desc)

    def try_direct(self, net, a, c, layers):
        """S1: a track on one layer, both endpoints already there.  Tried from
        every legal radial lead-out of each pad, not just from the centres --
        entry 20's bug (a), which alone accounts for most of the false 'no path'
        results on the fine-pitch packages."""
        loa = self.leadouts(a[0], a[1], net)
        lob = self.leadouts(c[0], c[1], net)
        for lay, nm in layers:
            for w in self.widths_for(net):
                for pa, sa in loa:
                    for pb, sb in lob:
                        for path in self.shapes(pa, pb):
                            if self.polyline_c(net, lay, path, w):
                                for s in (sa, sb):
                                    if s:
                                        self.add_track(net, self.F, s[0], s[1], s[2])
                                self._invalidate()
                                return ("direct %s w=%.3f pts=%d lead=%s/%s"
                                        % (nm, w, len(path),
                                           sa is not None, sb is not None))
        return None

    def try_layerhop(self, net, a, c, ends_layer):
        """S2: via down at both ends, run across on Signal or B.Cu.  The via sits
        at the lead-out point rather than in the pad, which is the only way it
        fits at all beside a 0.4-0.5 mm pitch package (entry 12/17 arithmetic)."""
        loa = self.leadouts(a[0], a[1], net)
        lob = self.leadouts(c[0], c[1], net)
        for lay, nm in ((self.SIG, "Signal"), (self.B, "B.Cu")):
            for w in self.widths_for(net):
                for pa, sa in loa:
                    for pb, sb in lob:
                        need, extra, ok = [], [], True
                        for p, l, s in ((pa, ends_layer[0], sa),
                                        (pb, ends_layer[1], sb)):
                            if s is None and l in (lay, "all"):
                                continue
                            if not self.via_ok(net, p[0], p[1], extra=extra):
                                ok = False
                                break
                            extra.append((p[0], p[1], VIA_DR))
                            need.append(p)
                        if not ok:
                            continue
                        for path in self.shapes(pa, pb):
                            if self.polyline_c(net, lay, path, w):
                                for s in (sa, sb):
                                    if s:
                                        self.add_track(net, self.F, s[0], s[1], s[2])
                                for p in need:
                                    self.add_via(net, p[0], p[1], VIA_D, VIA_DR)
                                self._invalidate()
                                return ("layerhop %s w=%.3f vias=%d"
                                        % (nm, w, len(need)))
        return None


def endpoint_layer(desc, R):
    """which copper layer an endpoint description already lives on"""
    if desc.startswith("Via") or desc.startswith("PTH pad") or "Zone" in desc:
        return "all"
    if " on Signal" in desc:
        return R.SIG
    if " on B.Cu" in desc:
        return R.B
    return R.F


def main():
    idx = int(sys.argv[1])
    place = "--place" in sys.argv
    pairs = load_pairs()
    p = pairs[idx]
    net = p["net"]
    a = (p["a"]["x"], p["a"]["y"])
    c = (p["b"]["x"], p["b"]["y"])

    R = PairRouter()
    la = endpoint_layer(p["a"]["desc"], R)
    lb = endpoint_layer(p["b"]["desc"], R)
    print("pair %d  net=%s  class=%s  floor=%.4f" % (
        idx, net, R.cls_of(net), R.floor_for(net)))
    print("   A %s @ (%.3f,%.3f)" % (p["a"]["desc"], a[0], a[1]))
    print("   B %s @ (%.3f,%.3f)" % (p["b"]["desc"], c[0], c[1]))

    on_plane = []
    for pt, lay in ((a, la), (c, lb)):
        pl = R.in_plane(net, pt[0], pt[1])
        on_plane.append(lay == "all" and pl is not None)
    print("   plane island at A: %s   at B: %s" % (
        R.in_plane(net, *a), R.in_plane(net, *c)))

    layers = []
    if la in (R.F, "all") and lb in (R.F, "all"):
        layers.append((R.F, "F.Cu"))
    if la in (R.SIG, "all") and lb in (R.SIG, "all"):
        layers.append((R.SIG, "Signal"))
    if la in (R.B, "all") and lb in (R.B, "all"):
        layers.append((R.B, "B.Cu"))

    res = None
    for name, fn in (("S0 plane", lambda: R.try_plane(net, a, c, on_plane)),
                     ("S0b plane-offset",
                      lambda: R.try_plane_offset(net, a, c, on_plane)),
                     ("S1 direct", lambda: R.try_direct(net, a, c, layers)),
                     ("S2 layerhop",
                      lambda: R.try_layerhop(net, a, c, (la, lb)))):
        res = fn()
        if res:
            print("   %s -> %s" % (name, res))
            break
        print("   %s -> no" % name)

    if not res:
        print("RESULT: OPEN (no clear geometry on this catalogue/grid)")
        return 2
    print("RESULT: candidate placed: %s" % res)
    if place:
        R.save()
        print("SAVED %s" % R.path)
        return 0
    print("(dry run, not saved)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
