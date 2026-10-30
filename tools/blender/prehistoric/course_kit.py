# The shared toolkit behind the Prehistoric World build scripts.
# SPDX-License-Identifier: MIT
#
# Each course script describes its layout as data (route control points, which stretches
# are dirt road, wooden bridge or causeway, where the river runs...) and calls the
# helpers here, which build an ordinary Kartipelago scene with the Blender add-on and
# export it as a track package:
#
#   Route       a hidden Bezier curve: the race line. Checkpoints, the start grid and
#               the AI's racing line all come from it (route.json).
#   Roads       separate road curves with the add-on's KP Road modifier, cut from the
#               route between two distances along it. Each piece has its own material,
#               shoulders, barriers and deck, and pieces can leave gaps (jumps).
#   Terrain     a height-field grid that meets the roads, textured by slope and height.
#   Rocks       rock masses (tunnels are cut through them with a boolean).
#   Water       visual water, lava and waterfalls with their flow animation.
#   Props       reusable low-poly props (palms, huts, bones...) as linked duplicates of
#               one mesh each, so editing the prop mesh edits every copy.
#
# The result is a normal .blend: open tracks-src/<id>.blend to keep editing by hand.
# Re-running a course script rebuilds the .blend and the package from the script.

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER_DIR = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(BLENDER_DIR))
sys.path.insert(0, os.path.join(BLENDER_DIR, "addons"))

import bpy  # noqa: E402  (first: bmesh and mathutils come with it)
import bmesh  # noqa: E402
from mathutils import Matrix, Vector, kdtree  # noqa: E402

import kartipelago_tools  # noqa: E402
from kartipelago_tools import checkpoints as cpts, export, materials, paint, road  # noqa: E402

TRACKS_DIR = os.environ.get("KP_TRACKS_DIR", os.path.join(REPO, "public", "tracks"))


def rnd(k):
    """A repeatable pseudo-random number in [0, 1) for any key."""
    return (math.sin(k * 12.9898 + 78.233) * 43758.5453) % 1


def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


class Sample:
    """A point on the route, every metre or so (Blender coordinates)."""

    __slots__ = ("p", "t", "r", "w", "bank", "s", "ground")

    def __init__(self, p, w, bank, s):
        self.p = p
        self.w = w
        self.bank = bank
        self.s = s
        self.t = Vector((0, 1, 0))
        self.r = Vector((1, 0, 0))
        self.ground = True

    def side(self, o, up=0.0):
        """The point `o` metres to the right of the centre, on the banked road, plus `up`."""
        return self.p + self.r * o + Vector((0, 0, -o * math.tan(math.radians(self.bank)) + up))


# A repaint: library material id -> the id to paint instead (Course.lib keeps the old
# material's surface). Dragon Canyon's Emerald Kingdom paint sets it.
MAT_REMAP = {}


class Course:
    def __init__(self, track_id, name, environment, fog=True):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        kartipelago_tools.register()
        self.id = track_id
        self.name = name
        sc = bpy.context.scene
        sc.kp_track_id = track_id
        sc.kp_track_name = name
        sc.kp_environment = environment
        sc.kp_fog = fog
        self.scene = sc
        self.colls = {}
        self.S = []
        self.length = 0.0
        self.width = 13.0
        self.pieces = []
        self.painted = []  # (object, preset list) for vertex paint
        self.protos = {}
        self.entities = []
        self.prop_count = 0
        self.extra_ground = []
        self.gaps = []

    # -------------------------------------------------------------- scene helpers

    def coll(self, name):
        c = self.colls.get(name)
        if c is None:
            c = bpy.data.collections.new(name)
            self.scene.collection.children.link(c)
            self.colls[name] = c
        return c

    def link(self, ob, coll):
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        self.coll(coll).objects.link(ob)
        return ob

    def mesh_object(self, name, bm, coll, role="both"):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(name, me)
        self.coll(coll).objects.link(ob)
        ob["kp_role"] = role
        return ob

    def lib(self, mat_id, surface=None):
        new = MAT_REMAP.get(mat_id)
        if new:
            # A repaint (MAT_REMAP): the new texture, but always the old one's surface, so
            # the driving can't change.
            if surface is None:
                surface = materials.entry(mat_id)["surface"]
            mat_id = new
        return materials.get_material(materials.entry(mat_id), surface)

    def assign(self, ob, mat, faces=None, size=None):
        """Put a library material on faces (all by default), with projected UVs."""
        e = materials.entry(mat["kp_texture"])
        if faces is None:
            faces = range(len(ob.data.polygons))
        materials.assign_faces(ob, mat, list(faces), size or e["tileMetres"], 0.0, materials.aspect(e))

    # -------------------------------------------------------------- the route

    def route(self, points, width=13.0, bank=8.0, bank_gain=40.0, spacing=1.0, sharp=(), flat=(), banks=()):
        """
        The race line through (x, y, z[, width]) control points, a closed loop. Banking is
        worked out from the curvature: up to `bank` degrees, into every turn. `sharp`:
        indices of points where the line may turn sharply (vector handles: the curve
        comes in and goes out straight, e.g. at a loop's ends); `flat`: (x, y, radius)
        circles where the road is never banked; `banks`: (x, y, radius, degrees) circles
        where a turn is banked harder, up to that many degrees (easing in and out over
        the outer third of the circle).
        """
        self.width = width
        cd = bpy.data.curves.new("Route", "CURVE")
        cd.dimensions = "3D"
        cd.twist_mode = "Z_UP"
        sp = cd.splines.new("BEZIER")
        sp.bezier_points.add(len(points) - 1)
        for k, (bp, p) in enumerate(zip(sp.bezier_points, points)):
            bp.co = p[:3]
            bp.handle_left_type = bp.handle_right_type = "VECTOR" if k in sharp else "AUTO"
            bp.radius = (p[3] if len(p) > 3 else width) / width
        sp.use_cyclic_u = True
        sp.resolution_u = 24
        ob = bpy.data.objects.new("Route", cd)
        self.coll("Route").objects.link(ob)
        ob["kp_route"] = "main"
        ob["kp_width"] = width
        self.route_ob = ob
        bpy.context.view_layer.update()
        self._sample(spacing)
        # Bank from curvature (+ = turning left), smoothed over ~25 m.
        n = len(self.S)
        head = []
        for i in range(n):
            a = self.S[(i + 2) % n].p - self.S[(i - 2) % n].p
            head.append(math.atan2(a.y, a.x))
        k = []
        for i in range(n):
            d = head[(i + 1) % n] - head[(i - 1) % n]
            d = (d + math.pi) % math.tau - math.pi
            ds = (self.S[(i + 1) % n].p - self.S[(i - 1) % n].p).length or 1
            k.append(d / ds)
        win = 12
        ks = [sum(k[(i + j) % n] for j in range(-win, win + 1)) / (2 * win + 1) for i in range(n)]
        tree = kdtree.KDTree(n)
        for i, s in enumerate(self.S):
            tree.insert(s.p, i)
        tree.balance()
        for bp in sp.bezier_points:
            _, i, _ = tree.find(bp.co)
            turn = clamp(ks[i] * bank_gain, -1, 1)
            deg = bank
            for bx, by, br, bd in banks:
                w = smooth((br - math.hypot(bp.co.x - bx, bp.co.y - by)) / (br / 3))
                deg = max(deg, lerp(bank, bd, w))
            bp.tilt = math.radians(-turn * deg)
            if any(math.hypot(bp.co.x - fx, bp.co.y - fy) < fr for fx, fy, fr in flat):
                bp.tilt = 0.0
        bpy.context.view_layer.update()
        self._sample(spacing)
        ob.hide_set(True)
        ob.hide_render = True
        return ob

    def _sample(self, spacing):
        pts = export.sample_route(self.route_ob, spacing)["points"]
        S = []
        s = 0.0
        prev = None
        for p in pts:
            v = Vector((p["x"], -p["z"], p["y"]))
            if prev is not None:
                s += (v - prev).length
            S.append(Sample(v, p["width"], p["bank"], s))
            prev = v
        self.length = s + (S[0].p - S[-1].p).length
        n = len(S)
        for i, smp in enumerate(S):
            t = S[(i + 1) % n].p - S[(i - 1) % n].p
            smp.t = t.normalized()
            h = Vector((t.x, t.y, 0)).normalized()
            smp.r = Vector((h.y, -h.x, 0))
        self.S = S

    def index_at(self, s):
        s %= self.length
        lo, hi = 0, len(self.S) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self.S[mid].s <= s:
                lo = mid
            else:
                hi = mid - 1
        return lo

    def at(self, s):
        """The route at distance s (metres from the start line), interpolated."""
        s %= self.length
        i = self.index_at(s)
        a = self.S[i]
        b = self.S[(i + 1) % len(self.S)]
        span = (b.s if b.s > a.s else self.length) - a.s
        f = clamp((s - a.s) / span) if span > 0 else 0
        out = Sample(a.p.lerp(b.p, f), lerp(a.w, b.w, f), lerp(a.bank, b.bank, f), s)
        out.t = a.t.lerp(b.t, f).normalized()
        out.r = a.r.lerp(b.r, f).normalized()
        return out

    def span(self, s0, s1):
        """Samples from s0 to s1 (s1 may pass the start line)."""
        if s1 < s0:
            s1 += self.length
        out = []
        i = self.index_at(s0)
        n = len(self.S)
        k = 0
        while k <= n:
            smp = self.S[(i + k) % n]
            lap = self.length if (i + k) >= n else 0
            if smp.s + lap > s1:
                break
            if smp.s + lap >= s0:
                out.append(smp)
            k += 1
        return out

    def nearest(self, x, y):
        """The route sample nearest (x, y), ignoring height, and how far away it is."""
        tree = getattr(self, "_near_tree", None)
        if tree is None or self._near_n != len(self.S):
            tree = kdtree.KDTree(len(self.S))
            for i, smp in enumerate(self.S):
                tree.insert(Vector((smp.p.x, smp.p.y, 0)), i)
            tree.balance()
            self._near_tree, self._near_n = tree, len(self.S)
        _, i, d = tree.find(Vector((x, y, 0)))
        return self.S[i], d

    # -------------------------------------------------------------- road pieces

    def piece(
        self,
        name,
        s0,
        s1,
        mat,
        surface=None,
        *,
        shoulder=1.5,
        shoulder_mat=None,
        barrier=0.0,
        barrier_mat=None,
        deck=0.0,
        deck_mat=None,
        ground=True,
        step=4.0,
        lift=None,
        exact=False,
    ):
        """
        A road from s0 to s1 along the route, built with the add-on's road generator.
        `ground=False` means the terrain doesn't rise to meet it (bridges, ledges, jumps).
        """
        if s1 < s0:
            s1 += self.length
        n = max(2, math.ceil((s1 - s0) / step))
        h = (s1 - s0) / n / 3
        cd = bpy.data.curves.new(name, "CURVE")
        cd.dimensions = "3D"
        cd.twist_mode = "Z_UP"
        sp = cd.splines.new("BEZIER")
        sp.bezier_points.add(n)
        def pos(s):
            q = self.at(s)
            return q.p + Vector((0, 0, lift(s - s0, s1 - s0) if lift else 0.0))

        for k, bp in enumerate(sp.bezier_points):
            sk = s0 + (s1 - s0) * k / n
            smp = self.at(sk)
            p = pos(sk)
            # The tangent includes any lift (a kicker at the end of a jump ramp).
            # (`exact`: tangents from this piece's own stretch, so it ends dead straight
            # where the route turns sharply just beyond it, e.g. into a loop.)
            t = (pos(min(s1, sk + 0.5)) - pos(max(s0, sk - 0.5))).normalized() if (lift or exact) else smp.t
            bp.handle_left_type = bp.handle_right_type = "FREE"
            bp.co = p
            bp.handle_right = p + t * h
            bp.handle_left = p - t * h
            bp.tilt = math.radians(smp.bank)
            bp.radius = smp.w / self.width
        sp.use_cyclic_u = False
        sp.resolution_u = 6
        ob = bpy.data.objects.new(name, cd)
        self.coll("Roads").objects.link(ob)
        road.attach_road(ob, width=self.width, barrier=barrier, deck=deck)
        mod = ob.modifiers["KP Road"]
        road.set_input(mod, "Shoulder Width", shoulder)
        road.set_input(mod, "Segment Length", 1.0)
        e = materials.entry(mat)
        materials.apply_to_road(ob, self.lib(mat, surface), "road", e["tileMetres"], 0, materials.aspect(e))
        sm = shoulder_mat or (mat, "dirt")
        se = materials.entry(sm[0])
        materials.apply_to_road(ob, self.lib(*sm), "shoulder", se["tileMetres"], 0, materials.aspect(se))
        if barrier > 0:
            bm_ = barrier_mat or ("valley_cliff", "wall")
            be = materials.entry(bm_[0])
            materials.apply_to_road(ob, self.lib(*bm_), "barrier", be["tileMetres"], 0, materials.aspect(be))
        if deck > 0:
            dm = deck_mat or ("valley_cliff", "wall")
            de = materials.entry(dm[0])
            materials.apply_to_road(ob, self.lib(*dm), "deck", de["tileMetres"], 0, materials.aspect(de))
        for smp in self.span(s0, s1):
            smp.ground = ground
        ob["kp_from"] = round(s0 % self.length, 2)
        ob["kp_to"] = round(s1 % self.length, 2)
        self.pieces.append(ob)
        return ob

    def roads(self, plan):
        """
        Build every road piece from a plan: a list of (from, to, kind) sorted by distance,
        where kind names an entry of `self.kinds` (or None for a gap: a jump).
        """
        for k, item in enumerate(plan):
            s0, s1, kind = item[:3]
            extra = item[3] if len(item) > 3 else {}
            if kind is None:
                for smp in self.span(s0, s1):
                    smp.ground = False
                self.gaps.append((s0, s1))
                continue
            opts = dict(self.kinds[kind])
            opts.update(extra)
            mat = opts.pop("mat")
            surface = opts.pop("surface", None)
            if opts.get("ground") is False and len(plan) > 1:
                # (A bridge or boardwalk laps 0.8 m over the road either side of it: where
                # they only met, a sliver of a gap at the joint let a kart's middle drop
                # through to the bank under it.)
                s0, s1 = s0 - 0.8, s1 + 0.8
            self.piece("Road %02d %s" % (k + 1, kind), s0, s1, mat, surface, **opts)

    # -------------------------------------------------------------- terrain

    def road_height(self, x, y, near, fade, under, nat=None):
        """
        How the terrain should meet the roads at (x, y): (weight 0..1, height). Every road
        that touches the terrain pulls it to its banked surface, fading out with distance.
        """
        # Under a bridge or over a jump's gap the land keeps its own shape, except that
        # it never comes up through the bridge.
        _, j, dj = self._all_tree.find(Vector((x, y, 0)))
        hits = self._ground_tree.find_range(Vector((x, y, 0)), near + fade)
        if not self.S[j].ground and dj < self.S[j].w / 2 + 4:
            # (Unless another road runs right under the bridge: then the land meets that
            # one, as it would anywhere else.)
            beneath = [h for h in hits if h[2] < near and self._ground[h[1]].p.z < self.S[j].p.z - 6.0]
            if not beneath:
                below = self.S[j].p.z - 3.0
                return (1.0, below) if nat is not None and nat > below else (0.0, 0.0)
            hits = beneath
        if not hits:
            return 0.0, 0.0
        wsum = 0.0
        hsum = 0.0
        wmax = 0.0
        best = None
        for _, i, d in hits:
            smp = self._ground[i]
            f = 1.0 - smooth((d - near) / fade) if d > near else 1.0
            o = (Vector((x, y, 0)) - Vector((smp.p.x, smp.p.y, 0))).dot(smp.r)
            edge = smp.w / 2 + 1.5
            o = clamp(o, -edge, edge)
            z = smp.p.z - o * math.tan(math.radians(smp.bank)) - under
            w = f * f / (d * d + 1.0) ** 2
            wsum += w
            hsum += w * z
            wmax = max(wmax, f)
            if best is None or d < best[0]:
                best = (d, z)
        z = hsum / wsum if wsum > 0 else best[1]
        if best[0] < near:
            z = min(z, best[1])  # never poke up through the nearest road
        return wmax, z

    def side_road(self, name, pts, mat, surface=None, width=9.0, shoulder=1.0, shoulder_mat=None, barrier=0.0, barrier_mat=None,
                  deck=0.0, deck_mat=None, ground=True):
        """
        Like shortcut (a road off the race line through (x, y, z) points), with a barrier
        and a deck if asked; `ground=False`: the terrain doesn't rise to meet it (a road
        up on the rooftops, say). Its samples are in self.side_samples either way.
        """
        cd = bpy.data.curves.new(name, "CURVE")
        cd.dimensions = "3D"
        cd.twist_mode = "Z_UP"
        sp = cd.splines.new("BEZIER")
        sp.bezier_points.add(len(pts) - 1)
        for bp, p in zip(sp.bezier_points, pts):
            bp.co = p[:3]
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        sp.resolution_u = 12
        ob = bpy.data.objects.new(name, cd)
        self.coll("Roads").objects.link(ob)
        road.attach_road(ob, width=width, barrier=barrier, deck=deck)
        mod = ob.modifiers["KP Road"]
        road.set_input(mod, "Shoulder Width", shoulder)
        road.set_input(mod, "Segment Length", 1.0)
        e = materials.entry(mat)
        materials.apply_to_road(ob, self.lib(mat, surface), "road", e["tileMetres"], 0, materials.aspect(e))
        sm = shoulder_mat or (mat, "dirt")
        se = materials.entry(sm[0])
        materials.apply_to_road(ob, self.lib(*sm), "shoulder", se["tileMetres"], 0, materials.aspect(se))
        if barrier > 0:
            bm_ = barrier_mat or ("valley_cliff", "wall")
            be = materials.entry(bm_[0])
            materials.apply_to_road(ob, self.lib(*bm_), "barrier", be["tileMetres"], 0, materials.aspect(be))
        if deck > 0:
            dm = deck_mat or ("valley_cliff", "wall")
            de = materials.entry(dm[0])
            materials.apply_to_road(ob, self.lib(*dm), "deck", de["tileMetres"], 0, materials.aspect(de))
        bpy.context.view_layer.update()
        if not hasattr(self, "side_samples"):
            self.side_samples = []
        for p in export.sample_route(ob, 1.0)["points"]:
            smp = Sample(Vector((p["x"], -p["z"], p["y"])), width, 0.0, 0.0)
            self.side_samples.append(smp)
            if ground:
                self.extra_ground.append(smp)
        return ob

    def shortcut(self, name, pts, mat, surface=None, width=9.0, shoulder=1.0, shoulder_mat=None):
        """
        A side road off the race line (a shortcut): a road curve through (x, y, z) points,
        open at both ends, that the terrain meets just like the main road. It isn't part
        of the route, so the AI keeps to the main road.
        """
        cd = bpy.data.curves.new(name, "CURVE")
        cd.dimensions = "3D"
        cd.twist_mode = "Z_UP"
        sp = cd.splines.new("BEZIER")
        sp.bezier_points.add(len(pts) - 1)
        for bp, p in zip(sp.bezier_points, pts):
            bp.co = p[:3]
            bp.handle_left_type = bp.handle_right_type = "AUTO"
            # (A fourth value: the width there, e.g. to taper a path's ends.)
            bp.radius = (p[3] / width) if len(p) > 3 else 1.0
        sp.resolution_u = 12
        ob = bpy.data.objects.new(name, cd)
        self.coll("Roads").objects.link(ob)
        road.attach_road(ob, width=width, barrier=0.0)
        mod = ob.modifiers["KP Road"]
        road.set_input(mod, "Shoulder Width", shoulder)
        road.set_input(mod, "Segment Length", 1.0)
        e = materials.entry(mat)
        materials.apply_to_road(ob, self.lib(mat, surface), "road", e["tileMetres"], 0, materials.aspect(e))
        sm = shoulder_mat or (mat, "dirt")
        se = materials.entry(sm[0])
        materials.apply_to_road(ob, self.lib(*sm), "shoulder", se["tileMetres"], 0, materials.aspect(se))
        bpy.context.view_layer.update()
        for p in export.sample_route(ob, 1.0)["points"]:
            smp = Sample(Vector((p["x"], -p["z"], p["y"])), p.get("width", width), 0.0, 0.0)
            self.extra_ground.append(smp)
        return ob

    def build_ground_tree(self):
        # (The side roads' samples their own way along, from their neighbours.)
        ex = self.extra_ground
        for i, smp in enumerate(ex):
            a = ex[i - 1].p if i > 0 and (ex[i - 1].p - smp.p).length < 3.0 else smp.p
            b = ex[i + 1].p if i + 1 < len(ex) and (ex[i + 1].p - smp.p).length < 3.0 else smp.p
            t = Vector((b.x - a.x, b.y - a.y, b.z - a.z))
            if Vector((t.x, t.y, 0.0)).length > 1e-6:
                t.normalize()
                smp.t = t
                h = Vector((t.x, t.y, 0.0)).normalized()
                smp.r = Vector((h.y, -h.x, 0.0))
        g = [s for s in self.S if s.ground] + self.extra_ground
        self._ground = g
        t = kdtree.KDTree(max(1, len(g)))
        for i, s in enumerate(g):
            t.insert(Vector((s.p.x, s.p.y, 0)), i)
        t.balance()
        self._ground_tree = t
        a = kdtree.KDTree(len(self.S))
        for i, s in enumerate(self.S):
            a.insert(Vector((s.p.x, s.p.y, 0)), i)
        a.balance()
        self._all_tree = a

    def spur_points(self, natural, a, b, z0=None, half=5.0, ease=20.0):
        """A side road's points from a to b (a on or by the main road): while any of its
        width is still over a ground road, just under that road's own banked surface there
        (a spur leaving at a slant runs along the road's edge a while); then eased into the
        land (`natural` + 0.2) over `ease` m. So it's flush with the road wherever they
        meet, never a step below it (Blake, valley polish 14, note 1)."""
        total = math.hypot(b[0] - a[0], b[1] - a[1])
        pts = []
        last = None  # (distance along, height) where it left the road
        k, n = 0, max(2, int(total / 2.0))
        while k <= n:
            f = k / n
            x, y = lerp(a[0], b[0], f), lerp(a[1], b[1], f)
            land = natural(x, y) + 0.2
            q, _ = self.nearest(x, y)
            o = (x - q.p.x) * q.r.x + (y - q.p.y) * q.r.y
            if q.ground and abs(o) <= q.w / 2 + 1.5 + half:
                oc = max(-q.w / 2, min(q.w / 2, o))
                h = q.p.z - oc * math.tan(math.radians(q.bank)) - 0.06
                last = None
            else:
                if last is None:
                    last = (total * f, pts[-1][2] if pts else (z0 if z0 is not None else land))
                h = lerp(last[1], land, smooth((total * f - last[0]) / ease))
            pts.append((x, y, h))
            # (Close together near the road, where the height follows it; on, every 8 m.)
            k += 1 if total * f < 30.0 else 4
        if (pts[-1][0], pts[-1][1]) != (b[0], b[1]):
            pts.append((b[0], b[1], natural(b[0], b[1]) + 0.2 if last is None else lerp(last[1], natural(*b) + 0.2, 1.0)))
        return pts

    def verge_height(self, x, y, z, under=0.2, edge_pad=4.0, slope=3.0, reach=7.5):
        """The land at (x, y), height z, brought up to meet the roads beside it (Blake,
        valley polish 14, note 1: "sometimes the road is higher than the ground and if I
        fall off the road and try to go back on the road, I cant"). A road is a slab with
        a skirt; where the land beside it dipped (a bog pool, a river's cut, the land
        pulled toward a lower road nearby), its edge stood up as a wall a kart can't
        climb (more than 0.25 m). So under a road and its shoulders the land lies just
        under its banked surface, and beside it no lower than that out to `edge_pad` past
        its surface, then a verge falling 1 in `slope` for `reach` m. Bridges and roads
        the terrain doesn't meet are left alone: their sides are meant to be drops."""
        hits = self._ground_tree.find_range(Vector((x, y, 0)), 9.0 + edge_pad + reach)
        # (The road the point is on, or nearest beside: the one whose surface's edge is
        # closest, the highest where two overlap. Only that one counts, so the land between
        # two roads at different heights, a hairpin's legs, follows the nearer.)
        best = None
        for _, i, _d in hits:
            smp = self._ground[i]
            dp = Vector((x - smp.p.x, y - smp.p.y, 0.0))
            txy = Vector((smp.t.x, smp.t.y, 0.0))
            if txy.length < 1e-6:
                continue
            along = dp.dot(txy) / txy.length
            if abs(along) > 2.5:
                continue  # (only the samples square across from the point)
            o = dp.dot(smp.r)
            half = smp.w / 2
            oc = clamp(o, -half - 1.5, half + 1.5)
            # (The road's surface there: banked across, and climbing along with its grade.)
            zs = smp.p.z + along * smp.t.z / txy.length - oc * math.tan(math.radians(smp.bank))
            out = max(0.0, abs(o) - half)
            key = (round(out, 1), -zs)
            if best is None or key < best[0]:
                best = (key, out, zs, half)
        if best is None:
            return z
        _, out, zs, half = best
        if out <= 1.5:
            # (Under the road and its shoulders: just under its surface.)
            return zs - under
        # (Beside it: no lower than just under its edge out to edge_pad, past its skirt,
        # then a verge falling 1 in `slope`, for `reach` m.)
        if out - edge_pad > reach:
            return z
        return max(z, zs - 0.17 - max(0.0, out - edge_pad) / slope)  # (just under the skirt's top)

    def terrain(self, name, x0, x1, y0, y1, cell, natural, classify, *, near=9.0, fade=20.0, under=0.2, verge=True):
        """
        A height-field grid over [x0, x1] x [y0, y1]. `natural(x, y)` is the land's own
        height; near the roads it's pulled to meet them. `classify(face_centre, normal,
        info)` returns a material per face (info: distance to the route). `verge`: the
        land also brought up to every road's edge, so a kart can always drive back up
        onto it (`verge_height`).
        """
        self.build_ground_tree()
        nx = int(round((x1 - x0) / cell))
        ny = int(round((y1 - y0) / cell))
        bm = bmesh.new()
        rows = []
        for j in range(ny + 1):
            row = []
            for i in range(nx + 1):
                x = x0 + (x1 - x0) * i / nx
                y = y0 + (y1 - y0) * j / ny
                nat = natural(x, y)
                w, z = self.road_height(x, y, near, fade, under, nat)
                h = lerp(nat, z, w)
                if verge:
                    h = self.verge_height(x, y, h, under)
                row.append(bm.verts.new((x, y, h)))
            rows.append(row)
        for j in range(ny):
            for i in range(nx):
                a, b, c, d = rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]
                # Split each quad along the flatter diagonal.
                if abs(a.co.z - c.co.z) < abs(b.co.z - d.co.z):
                    bm.faces.new((a, b, c))
                    bm.faces.new((a, c, d))
                else:
                    bm.faces.new((a, b, d))
                    bm.faces.new((b, c, d))
        ob = self.mesh_object(name, bm, "Terrain")
        groups = {}
        tree = kdtree.KDTree(len(self.S))
        for i, s in enumerate(self.S):
            tree.insert(Vector((s.p.x, s.p.y, 0)), i)
        tree.balance()
        for p in ob.data.polygons:
            _, i, d = tree.find(Vector((p.center.x, p.center.y, 0)))
            m = classify(p.center, p.normal, {"d": d, "sample": self.S[i]})
            if m is None:
                continue
            groups.setdefault(m, []).append(p.index)
        for (mid, surf), faces in groups.items():
            self.assign(ob, self.lib(mid, surf), faces)
        # Faces nobody wanted (classify returned None) are removed: holes for rock masses.
        kept = set()
        for faces in groups.values():
            kept.update(faces)
        drop = [p.index for p in ob.data.polygons if p.index not in kept]
        if drop:
            bm = bmesh.new()
            bm.from_mesh(ob.data)
            bm.faces.ensure_lookup_table()
            bmesh.ops.delete(bm, geom=[bm.faces[i] for i in drop], context="FACES")
            bm.to_mesh(ob.data)
            bm.free()
        ob.data.shade_smooth()
        return ob

    # -------------------------------------------------------------- shapes

    def ribbon(self, name, path, width, z, mat, coll="Water", role="both", steps=1):
        """
        A flat strip along a path of (x, y[, width[, z]]) points: rivers, lava flows.
        UVs run along the strip (V) so the flow animation scrolls downstream.
        """
        bm = bmesh.new()
        uv = bm.loops.layers.uv.new("UVMap")
        pts = [Vector((p[0], p[1], p[3] if len(p) > 3 else z)) for p in path]
        widths = [p[2] if len(p) > 2 else width for p in path]
        rows = []
        along = 0.0
        for i, p in enumerate(pts):
            a = pts[max(0, i - 1)]
            b = pts[min(len(pts) - 1, i + 1)]
            t = Vector((b.x - a.x, b.y - a.y, 0)).normalized()
            r = Vector((t.y, -t.x, 0))
            if i:
                along += (p - pts[i - 1]).length
            w = widths[i]
            row = []
            for k in range(steps + 1):
                o = -w / 2 + w * k / steps
                row.append((bm.verts.new(p + r * o), o, along))
            rows.append(row)
        e = materials.entry(mat["kp_texture"])
        tile = e["tileMetres"]
        for r0, r1 in zip(rows, rows[1:]):
            for k in range(steps):
                quad = (r0[k], r0[k + 1], r1[k + 1], r1[k])
                f = bm.faces.new([q[0] for q in quad])
                for loop, q in zip(f.loops, quad):
                    loop[uv].uv = (q[1] / tile, -q[2] / tile)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for f in bm.faces:
            if f.normal.z < 0:
                f.normal_flip()
        ob = self.mesh_object(name, bm, coll, role)
        ob.data.materials.append(mat)
        materials.ensure_paint(ob.data)
        return ob

    def disc(self, name, cx, cy, r, z, mat, coll="Water", role="both", n=40, wobble=0.0, seed=0):
        bm = bmesh.new()
        vs = []
        for i in range(n):
            a = i * math.tau / n
            rr = r * (1 + wobble * (math.sin(3 * a + seed) * 0.6 + (rnd(i + seed) - 0.5) * 0.4))
            vs.append(bm.verts.new((cx + rr * math.cos(a), cy + rr * math.sin(a), z)))
        bm.faces.new(vs)
        ob = self.mesh_object(name, bm, coll, role)
        self.assign(ob, mat)
        return ob

    def rock_mass(self, name, cx, cy, rx, ry, h, z0=-8.0, n=20, seed=0, bands=None, angle=0.0, base=0.0):
        """A layered rock: stacked, inset, lumpy rings from z0 up to h (band heights are
        fractions of the way from `base` to h)."""
        bands = bands or [(1.0, 0.0), (1.0, 0.45), (0.9, 0.5), (0.88, 0.78), (0.76, 0.82), (0.7, 1.0)]
        bm = bmesh.new()
        ca, sa = math.cos(angle), math.sin(angle)
        rings = []
        for scale, f in [(1.0, None)] + bands:
            z = z0 if f is None else base + f * (h - base)
            ring = []
            for i in range(n):
                a = i * math.tau / n
                k = scale * (1 + 0.1 * math.sin(3 * a + seed) + 0.07 * (rnd(i * 7 + seed + scale * 13) - 0.5))
                x, y = rx * k * math.cos(a), ry * k * math.sin(a)
                ring.append(bm.verts.new((cx + x * ca - y * sa, cy + x * sa + y * ca, z)))
            rings.append(ring)
        for lo, hi in zip(rings, rings[1:]):
            for i in range(n):
                bm.faces.new((lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i]))
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
        return self.mesh_object(name, bm, "Rocks")

    def tunnel(self, rock, s0, s1, half=None, height=8.5, pad=12.0, floor=-0.25):
        """Cut a tunnel through `rock` along the route from s0 to s1 (padded at both ends);
        its floor `floor` under the road (deeper to clear a rock right away), banked with
        the road. (It was flat 0.4 m under the road's middle: beside a banked road that
        left a gutter up to a metre deep along its high side, and a kart that slid off
        the road in a tunnel couldn't climb back on: Blake, valley polish 14, note 1.)"""
        half = half or self.width / 2 + 3.5
        prof = [(-half, floor), (half, floor), (half, height * 0.62), (half * 0.62, height), (-half * 0.62, height), (-half, height * 0.62)]
        bm = bmesh.new()
        rings = []
        n = max(4, math.ceil((s1 - s0 + 2 * pad) / 2.0))
        for k in range(n + 1):
            smp = self.at(s0 - pad + (s1 - s0 + 2 * pad) * k / n)
            tb = math.tan(math.radians(smp.bank))
            rings.append([bm.verts.new(smp.p + smp.r * a + Vector((0, 0, b - a * tb))) for a, b in prof])
        m = len(prof)
        for lo, hi in zip(rings, rings[1:]):
            for k in range(m):
                bm.faces.new((lo[k], lo[(k + 1) % m], hi[(k + 1) % m], hi[k]))
        bm.faces.new(rings[0])
        bm.faces.new(list(reversed(rings[-1])))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        cutter = self.mesh_object("Tunnel Cutter", bm, "Rocks", "visual")
        mod = rock.modifiers.new("Tunnel", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.solver = "EXACT"
        mod.object = cutter
        bpy.context.view_layer.objects.active = rock
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cutter)
        return rock

    def paint_rock(self, rock, wall, top, floor=None, top_z=None, floor_z=None):
        groups = {"wall": [], "top": [], "floor": []}
        for p in rock.data.polygons:
            if p.normal.z > 0.7 and floor_z is not None and p.center.z < floor_z:
                groups["floor"].append(p.index)
            elif p.normal.z > 0.6 and (top_z is None or p.center.z > top_z):
                groups["top"].append(p.index)
            else:
                groups["wall"].append(p.index)
        self.assign(rock, self.lib(*wall), groups["wall"])
        self.assign(rock, self.lib(*top), groups["top"])
        if groups["floor"]:
            self.assign(rock, self.lib(*(floor or wall)), groups["floor"])
        rock.data.shade_flat()

    # -------------------------------------------------------------- props

    def proto(self, name, build):
        """A prop's mesh, built once. `build(bm)` fills a bmesh and returns material slots
        as [(material, [face indices])]."""
        if name in self.protos:
            return self.protos[name]
        bm = bmesh.new()
        slots = build(bm)
        me = bpy.data.meshes.new("Prop " + name)
        bm.to_mesh(me)
        bm.free()
        tmp = bpy.data.objects.new("tmp", me)
        self.coll("Prop Library").objects.link(tmp)
        for mat, faces in slots:
            self.assign(tmp, mat, faces)
        # Shared by every copy, so the UVs are made once here (in the prop's own space)
        # and kept, rather than re-projected per copy on export.
        materials.keep_uvs(tmp, range(len(me.polygons)))
        bpy.data.objects.remove(tmp)
        self.protos[name] = me
        return me

    def foot_proto(self, proto, zmax=5.0, mats=r"root|bark|trunk|wood"):
        """A collider for a tree's foot (its roots and the bottom of its trunk), cut from
        its own mesh: the faces of the materials matching `mats` below `zmax` (in the prop's
        own space) that stand up steep, so a kart runs into a root's side and never rides
        up onto its back (Blake, valley polish 14, note 2: "all of the roots in this entire
        overworld have hitboxes. i can just drive right through them"). None if it has no
        such faces."""
        import re
        name = proto + " Foot"
        if name in self.protos:
            return name
        src = self.protos[proto]
        rx = re.compile(mats, re.I)
        keep = {i for i, m in enumerate(src.materials) if m is not None and rx.search(m.name)}
        bm = bmesh.new()
        bm.from_mesh(src)
        bm.normal_update()
        drop = [f for f in bm.faces if f.material_index not in keep or abs(f.normal.z) > 0.6
                or any(v.co.z > zmax for v in f.verts)]
        bmesh.ops.delete(bm, geom=drop, context="FACES")
        if not bm.faces:
            bm.free()
            self.protos[name] = None
            return None
        me = bpy.data.meshes.new("Prop " + name)
        bm.to_mesh(me)
        bm.free()
        # (A wall, as a tree's trunk collider is.)
        me.materials.append(self.lib("valley_cliff", "wall"))
        for poly in me.polygons:
            poly.material_index = 0
        self.protos[name] = me
        return name

    def place_foot(self, proto, x, y, z, rot=0.0, scale=1.0, zmax=5.0, clear=2.0):
        """The collider for a tree's roots (`foot_proto`) where the tree stands; none of it
        on a road or its shoulder (`clear` m past the road's edge), where a root mustn't
        stop a kart."""
        f = self.foot_proto(proto, zmax)
        if not f or self.protos.get(f) is None:
            return
        bm = bmesh.new()
        bm.from_mesh(self.protos[f])
        ca, sa = math.cos(rot), math.sin(rot)
        for v in bm.verts:
            lx, ly, lz = v.co.x * scale, v.co.y * scale, v.co.z * scale
            v.co = Vector((x + lx * ca - ly * sa, y + lx * sa + ly * ca, z + lz))

        spurs = [q for q in self.extra_ground if (q.p.x - x) ** 2 + (q.p.y - y) ** 2 < (40.0 * max(1.0, scale)) ** 2]

        def on_road(p):
            smp, d = self.nearest(p.x, p.y)
            if d <= smp.w / 2 + clear:
                return True
            return any((q.p.x - p.x) ** 2 + (q.p.y - p.y) ** 2 <= (q.w / 2 + clear) ** 2 for q in spurs)

        drop = [fc for fc in bm.faces if any(on_road(v.co) for v in fc.verts)]
        if drop:
            bmesh.ops.delete(bm, geom=drop, context="FACES")
        if not bm.faces:
            bm.free()
            return
        me = bpy.data.meshes.new(f)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(self.protos[f].materials[0])
        ob = bpy.data.objects.new(f, me)
        self.coll("Collision").objects.link(ob)
        ob["kp_role"] = "collision"

    def place(self, proto, x, y, z, rot=0.0, scale=1.0, coll="Props", role="both", name=None):
        me = self.protos[proto]
        self.prop_count += 1
        ob = bpy.data.objects.new(name or proto, me)
        ob.location = (x, y, z)
        ob.rotation_euler = (0, 0, rot)
        ob.scale = (scale, scale, scale) if isinstance(scale, (int, float)) else scale
        self.coll(coll).objects.link(ob)
        ob["kp_role"] = role
        return ob

    def ground_z(self, x, y, objs):
        """Height of the given meshes straight below (x, y), or None."""
        best = None
        for ob in objs:
            mw = ob.matrix_world
            inv = mw.inverted()
            o = inv @ Vector((x, y, 500))
            d = (inv.to_3x3() @ Vector((0, 0, -1))).normalized()
            hit, loc, _, _ = ob.ray_cast(o, d)
            if hit:
                z = (mw @ loc).z
                best = z if best is None else max(best, z)
        return best

    def path_curve(self, name, pts, z=0.0, closed=True):
        """A hidden curve exported as an extra route (route.json), named `name`: paths
        for creatures and the like. Edit it in Blender like any curve."""
        cd = bpy.data.curves.new(name, "CURVE")
        cd.dimensions = "3D"
        sp = cd.splines.new("BEZIER")
        sp.bezier_points.add(len(pts) - 1)
        for bp, p in zip(sp.bezier_points, pts):
            bp.co = (p[0], p[1], p[2] if len(p) > 2 else z)
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        sp.use_cyclic_u = closed
        ob = bpy.data.objects.new(name, cd)
        self.coll("Paths").objects.link(ob)
        ob["kp_route"] = name
        ob["kp_width"] = 4.0
        ob.hide_set(True)
        ob.hide_render = True
        return ob

    @staticmethod
    def game(x, y, z):
        """Blender (x, y, z) to game (x, y, z)."""
        return (round(x, 2), round(z, 2), round(-y, 2))

    # -------------------------------------------------------------- markings

    def start_line(self, mat_id="start_checker"):
        """A checkered start/finish line painted across the road at s = 0."""
        bm = bmesh.new()
        uv = bm.loops.layers.uv.new("UVMap")
        smp = self.at(0.0)
        half = smp.w / 2
        rows = []
        for along in (-1.0, 1.0):
            q = self.at(along)
            row = [q.side(-half + half * 2 * k / 8, 0.04) for k in range(9)]
            # (Sat on the road as built, not on the route's own cross-section: Blake, Oct
            # 28, the finish line was hovering where the road's draped over the land.)
            for i, v in enumerate(row):
                z = self.ground_z(v[0], v[1], self.pieces)
                if z is not None and abs(z - v[2]) < 1.5:
                    row[i] = (v[0], v[1], z + 0.03)
            rows.append(row)
        verts = [[bm.verts.new(v) for v in r] for r in rows]
        for k in range(8):
            f = bm.faces.new((verts[0][k], verts[0][k + 1], verts[1][k + 1], verts[1][k]))
            for loop, (u, v) in zip(f.loops, ((k, 0), (k + 1, 0), (k + 1, 1), (k, 1))):
                loop[uv].uv = (u / 4, v / 2)
        # (No grid bars in front of the slots: Blake, Oct 25, they read as dark lines. The
        # game strips them from courses built before: trackPackage.ts, stripStartGrid.)
        ob = self.mesh_object("Start Line", bm, "Markings", "visual")
        ob.data.materials.append(self.lib(mat_id))
        materials.ensure_paint(ob.data)
        return ob

    # -------------------------------------------------------------- gameplay data

    def zipper(self, at, across=0.0):
        self.entities.append({"id": "zip_%02d" % (sum(e["type"] == "zipper" for e in self.entities) + 1), "type": "zipper", "at": round(at, 1), "across": across})

    def bananas(self, at, across=0.0, count=5, gap=2.5):
        n = sum(e["type"] == "bananas" for e in self.entities) + 1
        self.entities.append({"id": "ban_%02d" % n, "type": "bananas", "at": round(at, 1), "across": across, "count": count, "gap": gap})

    def balloon(self, at, across=0.0, color="red"):
        n = sum(e["type"] == "balloon" for e in self.entities) + 1
        self.entities.append({"id": "bal_%02d" % n, "type": "balloon", "at": round(at, 1), "across": across, "color": color})

    def entity(self, kind, **data):
        n = sum(e["type"] == kind for e in self.entities) + 1
        self.entities.append({"id": "%s_%02d" % (kind, n), "type": kind, **data})

    # -------------------------------------------------------------- checkpoints

    def checkpoints(self, extra=(), avoid=(), margin=18.0, height=6.0):
        """
        The lap's checkpoint gates, with the add-on's own generator (the same as its
        Generate from Route button): the start line, after every real turn, the `extra`
        distances asked for (landmarks, landings), and none inside a jump's gap or a
        respawn zone. Returns {distance: gate object}.
        """
        avoid = list(avoid) + list(self.gaps) + [(e["from"], e["at"] + 6) for e in self.entities if e["type"] == "respawn"]
        made = cpts.generate(self.scene, avoid=avoid, extra=[d % self.length for d in extra], margin=margin, height=height)
        samples, length = cpts.route_samples(self.scene)
        return {cpts.distance_along(samples, g.location): g for g in made}

    def alt_gate(self, main_gate, route, points, width=None, height=6.0):
        """A gate on an alternate route (a shortcut) that counts the same as main_gate:
        placed across the middle of a polyline of (x, y, z) points."""
        a, b = Vector(points[len(points) // 2 - 1]), Vector(points[len(points) // 2])
        mid = (a + b) / 2
        f = (b - a)
        f.z = 0
        f.normalize()
        g = cpts.make(self.scene, main_gate["kp_checkpoint"], mid, (f.x, f.y), width or 22.0, height, route=route,
                      name="CP %02d %s" % (main_gate["kp_checkpoint"], route))
        cpts.add_respawn(g, mid + f * 4, (f.x, f.y))
        return g

    # -------------------------------------------------------------- finish

    def preset(self, name, obs, strength, color=(1.0, 0.9, 0.7), distance=8.0, faces=None):
        sun = paint.sun_direction(self.scene)
        ts = [paint.Target(o, faces) for o in obs]
        paint.run(name, ts, strength, color, distance, sun)

    def finish(self, extra=None):
        """Save the .blend, export the package and write track.json's gameplay data."""
        os.makedirs(os.path.join(REPO, "tracks-src"), exist_ok=True)
        blend = os.path.join(REPO, "tracks-src", self.id + ".blend")
        bpy.ops.wm.save_as_mainfile(filepath=blend)
        rep = export.export_track(TRACKS_DIR, self.id, self.name)
        meta_path = os.path.join(TRACKS_DIR, self.id, "track.json")
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        meta["name"] = self.name
        meta["generator"] = "tools/blender/prehistoric/%s.py (re-running it rewrites entities)" % self.id
        # The eggs: a few small clusters off the racing line (eggs.py).
        import eggs  # noqa: E402

        eggs.cluster(self.entities, eggs._routes(os.path.join(TRACKS_DIR, self.id)))
        meta["entities"] = self.entities
        if extra:
            meta.update(extra)
        import ruin_mode  # noqa: E402

        if ruin_mode.ON:
            # The sync rule: a ruin records the course scripts it was built from, so a
            # test can tell when the standard course has changed and the ruin needs
            # rebuilding (tests/ruin.test.ts).
            meta["builtFrom"] = ruin_mode.fingerprints(self.id)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
            f.write("\n")
        rep["length"] = round(self.length, 1)
        rep["props"] = self.prop_count
        print("EXPORTED", json.dumps(rep))
        return rep


def s_near(course, x, y, z=None):
    """Distance along the route of the route point nearest (x, y) (and, given z, the
    nearest in 3D: for a spot under or over another part of the lap)."""
    if z is not None:
        return min(course.S, key=lambda q: (q.p.x - x) ** 2 + (q.p.y - y) ** 2 + (q.p.z - z) ** 2).s
    smp, _ = course.nearest(x, y)
    return smp.s


def crossings(course, inside, margin=4.0):
    """Stretches of the route [(s0, s1)] where inside(sample) is true, padded by margin."""
    out = []
    run = None
    for smp in course.S:
        if inside(smp):
            run = [smp.s, smp.s] if run is None else [run[0], smp.s]
        elif run is not None:
            out.append((run[0] - margin, run[1] + margin))
            run = None
    if run is not None:
        out.append((run[0] - margin, run[1] + margin))
    return out


def plan(course, specials, default, max_len=260.0):
    """
    The whole lap as road pieces: `specials` [(s0, s1, kind)] where something other than
    the default road goes (kind None = a gap to jump), and the default everywhere else,
    in pieces no longer than max_len.
    """
    L = course.length
    out = []
    pos = 0.0
    for item in sorted(specials, key=lambda it: it[0]):
        s0, s1 = max(pos, item[0]), min(L, item[1])
        if s1 <= s0:
            continue
        if s0 > pos + 0.5:
            out += _split(pos, s0, default, max_len)
        out.append((s0, s1) + tuple(item[2:]))
        pos = s1
    if pos < L - 0.5:
        out += _split(pos, L, default, max_len)
    return out


def _split(a, b, kind, max_len):
    n = max(1, math.ceil((b - a) / max_len))
    return [(a + (b - a) * k / n, a + (b - a) * (k + 1) / n, kind) for k in range(n)]


def runs(course, label):
    """Group the route into stretches by label(sample): [(s0, s1, label)], merging
    stretches shorter than 6 m into their neighbours."""
    out = []
    for smp in course.S:
        k = label(smp)
        if out and out[-1][2] == k:
            out[-1][1] = smp.s
        else:
            if out:
                out[-1][1] = smp.s
            out.append([smp.s, smp.s, k])
    out[-1][1] = course.length
    merged = []
    for r in out:
        if merged and (r[1] - r[0] < 6 or merged[-1][2] == r[2]):
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    return [tuple(r) for r in merged]


# ---------------------------------------------------------------- arc-and-straight layouts


def turtle(segs, start, head, step=1.0):
    """
    Walk a layout made of straights and arcs: ("S", length), ("L", radius, degrees) or
    ("R", radius, degrees), from start (x, y) facing head (degrees, 90 = north). Returns
    dense points [(x, y, heading_degrees, segment_index)]. Arcs of a known radius make
    corners you can hold one drift through.
    """
    x, y = start
    h = head
    pts = [(x, y, h, 0)]
    for i, sg in enumerate(segs):
        if sg[0] == "LOOP":
            # ("LOOP", radius, ramp, offset): the route jumps straight from the loop's
            # entry to its exit (a gap in the roads; the loop itself is Course.loop).
            ahead, right = loop_layout(sg[1], sg[2], sg[3])
            hr = math.radians(h)
            dx = math.cos(hr) * ahead + math.sin(hr) * right
            dy = math.sin(hr) * ahead - math.cos(hr) * right
            n = max(2, int(math.hypot(dx, dy) / step))
            for _ in range(n):
                x += dx / n
                y += dy / n
                pts.append((x, y, h, i))
            continue
        if sg[0] == "S":
            n = max(1, int(sg[1] / step))
            for _ in range(n):
                x += math.cos(math.radians(h)) * sg[1] / n
                y += math.sin(math.radians(h)) * sg[1] / n
                pts.append((x, y, h, i))
        else:
            r, deg = sg[1], sg[2]
            sgn = 1 if sg[0] == "L" else -1
            n = max(2, int(r * math.radians(deg) / step))
            for _ in range(n):
                dh = sgn * deg / n
                chord = 2 * r * math.sin(math.radians(abs(dh)) / 2)
                x += math.cos(math.radians(h + dh / 2)) * chord
                y += math.sin(math.radians(h + dh / 2)) * chord
                h += dh
                pts.append((x, y, h, i))
    return pts


def close_turtle(segs, a, b, start, head):
    """Lengthen or shorten straights a and b (not parallel) so the layout closes."""
    segs = list(segs)
    for _ in range(40):
        p = turtle(segs, start, head)
        ex, ey = p[-1][0] - p[0][0], p[-1][1] - p[0][1]
        if math.hypot(ex, ey) < 1e-4:
            break
        ha = next(q[2] for q in p if q[3] == a)
        hb = next(q[2] for q in p if q[3] == b)
        ua = (math.cos(math.radians(ha)), math.sin(math.radians(ha)))
        ub = (math.cos(math.radians(hb)), math.sin(math.radians(hb)))
        det = ua[0] * ub[1] - ua[1] * ub[0]
        segs[a] = ("S", segs[a][1] + (-ex * ub[1] + ey * ub[0]) / det)
        segs[b] = ("S", segs[b][1] + (-ua[0] * ey + ua[1] * ex) / det)
    return segs, turtle(segs, start, head)


def route_points(pts, z, every=14.0):
    """Control points (x, y, z) every so many metres along a dense turtle path."""
    out = []
    d = 0.0
    next_at = 0.0
    for i, (x, y, _, _) in enumerate(pts[:-1]):
        if i:
            d += math.hypot(x - pts[i - 1][0], y - pts[i - 1][1])
        if d >= next_at:
            out.append((round(x, 2), round(y, 2), round(z(x, y), 2)))
            next_at += every
    return out


def route_points_by(pts, z, every=14.0, width=None):
    """
    Like route_points, but the height (and optionally the width) come from where along
    the layout a point is: z(distance, segment_index) and width(distance, segment_index).
    For layouts that cross over themselves (a bridge over the start straight).
    """
    out = []
    d = 0.0
    next_at = 0.0
    for i, (x, y, _, seg) in enumerate(pts[:-1]):
        if i:
            d += math.hypot(x - pts[i - 1][0], y - pts[i - 1][1])
        if d >= next_at:
            p = (round(x, 2), round(y, 2), round(z(d, seg), 2))
            if width is not None:
                p = p + (round(width(d, seg), 2),)
            out.append(p)
            next_at += every
    return out


def along(pts, z):
    """
    For layouts whose heights come from z(distance, segment): the turtle's distances are
    measured in plan, but the course measures along the road itself, which is longer
    wherever it climbs (a steep spiral's 3D length is several metres more). Returns
    (to_road, to_plan): plan distance -> distance along the road, and back.
    """
    d2 = [0.0]
    d3 = [0.0]
    zp = z(0.0, pts[0][3])
    for i in range(1, len(pts)):
        a, b = pts[i - 1], pts[i]
        h = math.hypot(b[0] - a[0], b[1] - a[1])
        d2.append(d2[-1] + h)
        zb = z(d2[-1], b[3])
        d3.append(d3[-1] + math.sqrt(h * h + (zb - zp) ** 2))
        zp = zb

    def interp(xs, ys, v):
        import bisect

        if v <= xs[0]:
            return ys[0] + (v - xs[0])
        if v >= xs[-1]:
            return ys[-1] + (v - xs[-1])
        k = bisect.bisect_right(xs, v)
        x0, x1 = xs[k - 1], xs[k]
        return ys[k - 1] + (ys[k] - ys[k - 1]) * (v - x0) / max(1e-9, x1 - x0)

    return (lambda d: interp(d2, d3, d)), (lambda s: interp(d3, d2, s))


def clear_piers(c, piece, terrain, **kw):
    """props.piers under a bridge piece, but none that would come down through another
    road below it (a spiral's lower turn, a loop's way in, a road passing under): a post
    stands only where its own road is the only one over that spot."""
    import props

    def avoid(x, y, bottom):
        zs = [q.p.z for q in c.S[::2] if (q.p.x - x) ** 2 + (q.p.y - y) ** 2 < (q.w / 2 + 2.0) ** 2]
        if not zs:
            return False
        top = max(zs)
        return any(bottom + 0.3 < z < top - 3.0 for z in zs)

    return props.piers(c, piece, terrain=terrain, avoid=avoid, **kw)


def with_jumps(base, seg_of, jumps, run=12.0, out=30.0):
    """
    A road height z(d, seg) from base(d, seg) with jumps cut in: for each (lip, landing,
    drop, kick), a kicker over the last `run` metres up to the lip (`kick` metres up), the
    flight line across the gap, a landing `drop` metres below the road there (so a kart at
    ordinary speed clears it), and the road easing back up out of the dip over `out`
    metres. Distances are the layout's (plan) distances.
    """

    def b(dd):
        return base(dd, seg_of(dd))

    def z(d, seg):
        for lip, land, drop, kick in jumps:
            if lip - run <= d <= land + out:
                if d <= lip:
                    return b(d) + kick * ((d - (lip - run)) / run) ** 2
                if d <= land:
                    return lerp(b(lip) + kick, b(land) - drop, (d - lip) / (land - lip))
                return b(d) - drop * (1 - smooth((d - land) / out))
        return base(d, seg)

    return z


def segment_starts(pts):
    """Distance along a turtle path where each segment starts."""
    out = {}
    d = 0.0
    for i, (x, y, _, seg) in enumerate(pts):
        if i:
            d += math.hypot(x - pts[i - 1][0], y - pts[i - 1][1])
        out.setdefault(seg, d)
    return out


def _underfloor(self, name, x0, x1, y0, y1, cell, height, mat):
    """
    A hidden collision floor under the land, so nowhere can a kart fall through the world:
    under steep slopes and wall feet (which only count as walls) there's always ground
    just below. `height(x, y)` returns the floor's height, or None to leave a hole (inside
    a rock mass, over a deliberate drop).
    """
    nx = int(round((x1 - x0) / cell))
    ny = int(round((y1 - y0) / cell))
    bm = bmesh.new()
    grid = {}
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx
            y = y0 + (y1 - y0) * j / ny
            h = height(x, y)
            if h is not None:
                grid[i, j] = bm.verts.new((x, y, h))
    for j in range(ny):
        for i in range(nx):
            q = [grid.get(k) for k in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))]
            if all(q):
                bm.faces.new(q)
    ob = self.mesh_object(name, bm, "Collision", "collision")
    self.assign(ob, mat)
    return ob


def _underfloor_flat(self, name, x0, x1, y0, y1, cell, height, mat, clear=0.3, clamp_where=None):
    """
    Like underfloor, but every cell is its own flat square at the lowest of its corners:
    under the steepest cliffs there's still a flat floor (never a steep face, which would
    count as a wall), so nothing can fall through the world anywhere.

    It's also kept `clear` metres under every road surface already built there (roads,
    side roads, shortcuts), so it can never sit above the road: `height` is
    usually the natural ground, and where a road is cut lower than that, a floor at the
    natural height would be an invisible plane over the road (it slowed karts down and
    blocked Dry Gulch's mine). `clamp_where(x, y)` can limit where that applies (round a
    tunnel's rock, the old floor height is what keeps the walls sealed).
    """
    nx = int(round((x1 - x0) / cell))
    ny = int(round((y1 - y0) / cell))
    hs = {}
    for j in range(ny + 1):
        for i in range(nx + 1):
            hs[i, j] = height(x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny)
    lowest = self._lowest_surface()
    # The land too: where the land's pulled down to meet a road (in a cutting, beside a
    # sunken road), the natural height is above the visible ground there, and a floor at
    # it was an invisible sheet over the land (karts drove in under it, or landed on it
    # and floated). Holes in the land (under rock masses) have nothing to keep under.
    land = self._lowest_surface(("Terrain",))
    bm = bmesh.new()
    zs = {}
    for j in range(ny):
        for i in range(nx):
            q = [hs[k] for k in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))]
            if any(h is None for h in q):
                continue
            z = min(q)
            xa, xb = x0 + (x1 - x0) * i / nx, x0 + (x1 - x0) * (i + 1) / nx
            ya, yb = y0 + (y1 - y0) * j / ny, y0 + (y1 - y0) * (j + 1) / ny
            for u, v in ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.5, 0.5), (0.5, 0.0), (1.0, 0.5), (0.5, 1.0), (0.0, 0.5)):
                if clamp_where is not None and not clamp_where(lerp(xa, xb, u), lerp(ya, yb, v)):
                    continue
                s = lowest(lerp(xa, xb, u), lerp(ya, yb, v))
                if s is not None:
                    z = min(z, s - clear)
                s = land(lerp(xa, xb, u), lerp(ya, yb, v))
                if s is not None:
                    z = min(z, s - clear)
            # A hair of overlap, so neighbouring squares never leave a crack.
            e = 0.02
            bm.faces.new([bm.verts.new(v) for v in ((xa - e, ya - e, z), (xb + e, ya - e, z), (xb + e, yb + e, z), (xa - e, yb + e, z))])
            zs[i, j] = z
    # Where neighbouring squares step by more than a little (a cliff, a pit's edge), a
    # face between them: else a kart on the lower one could drive under the higher one,
    # with nothing beneath it.
    for (i, j), z in zs.items():
        for di, dj in ((1, 0), (0, 1)):
            z2 = zs.get((i + di, j + dj))
            if z2 is None or abs(z2 - z) < 0.5:
                continue
            lo, hi = min(z, z2), max(z, z2)
            if di:
                xe = x0 + (x1 - x0) * (i + 1) / nx
                ya, yb = y0 + (y1 - y0) * j / ny, y0 + (y1 - y0) * (j + 1) / ny
                quad = ((xe, ya, lo), (xe, yb, lo), (xe, yb, hi), (xe, ya, hi))
            else:
                ye = y0 + (y1 - y0) * (j + 1) / ny
                xa, xb = x0 + (x1 - x0) * i / nx, x0 + (x1 - x0) * (i + 1) / nx
                quad = ((xa, ye, lo), (xb, ye, lo), (xb, ye, hi), (xa, ye, hi))
            bm.faces.new([bm.verts.new(v) for v in quad])
    ob = self.mesh_object(name, bm, "Collision", "collision")
    self.assign(ob, mat)
    return ob


def _lowest_surface(self, colls=("Roads",)):
    """A lookup (x, y) -> the height of the lowest road surface built so far there (the
    top faces of every road, side road and shortcut), or None if there's none. Only
    roads: a rock's buried base or a deck's underside mustn't drag the floor down."""
    from mathutils.bvhtree import BVHTree

    dg = bpy.context.evaluated_depsgraph_get()
    verts, faces = [], []
    obs = []
    for name in colls:
        got = self.colls.get(name)
        obs += list(got.all_objects) if got else []
    for ob in obs:
        if ob.type not in ("MESH", "CURVE") or ob.get("kp_role", "both") not in ("both", "collision"):
            continue
        ev = ob.evaluated_get(dg)
        try:
            me = ev.to_mesh()
        except RuntimeError:
            continue
        if me is None:
            continue
        mw = ob.matrix_world
        nm = mw.to_3x3().inverted().transposed()
        k = len(verts)
        verts += [mw @ v.co for v in me.vertices]
        for p in me.polygons:
            if (nm @ p.normal).normalized().z > 0.5:
                faces.append([k + i for i in p.vertices])
        ev.to_mesh_clear()
    if not faces:
        return lambda x, y: None
    tree = BVHTree.FromPolygons(verts, faces)
    up = Vector((0.0, 0.0, 1.0))

    def lowest(x, y):
        hit = tree.ray_cast(Vector((x, y, -2000.0)), up, 4000.0)
        return None if hit[0] is None else hit[0].z

    return lowest


def _glow(self, obs, lights, radius, color, base=1.0, region=None):
    """
    Hand-painted light: every vertex inside `region(point)` (or everywhere) is tinted
    `base` (a number, or an (r, g, b) tint: a cold moonlit blue, say), then lit back up
    near each light point, tinted `color`, fading out over `radius` metres. For torchlit
    tunnels, and firelight on snow.
    """
    from kartipelago_tools import paint as _paint
    from mathutils import kdtree

    b = tuple(base) if isinstance(base, (tuple, list)) else (base, base, base)
    tree = kdtree.KDTree(max(1, len(lights)))
    for i, lp in enumerate(lights):
        tree.insert(Vector(lp), i)
    tree.balance()
    for ob in obs:
        t = _paint.Target(ob, None)
        for li, v, _ in t.corners:
            w = t.world[v]
            if region is not None and not region(w):
                continue
            k = 0.0
            if lights:
                _, _, d = tree.find(w)
                if d is not None:
                    k = max(0.0, 1.0 - d / radius) ** 1.4
            t.mul(li, [b[c] + (color[c] - b[c]) * k for c in range(3)])
        t.write()


def _merge_props(self, colls, cell=160.0):
    """
    Join the copies in these collections into one mesh per (collection, role, map
    square): a few hundred braziers, trees and blocks become a few dozen meshes, so the
    game draws far fewer things, and each square is still culled when it's off screen.
    Prop UVs are kept (their faces are marked to keep them); vertex paint carries over.
    """
    merged = 0
    for coll_name in colls:
        groups = {}
        for ob in list(self.coll(coll_name).objects):
            if ob.type != "MESH":
                continue
            key = (ob.get("kp_role", "both"), int(math.floor(ob.location.x / cell)), int(math.floor(ob.location.y / cell)))
            groups.setdefault(key, []).append(ob)
        for (role, gx, gy), obs in groups.items():
            if len(obs) < 2:
                continue
            for o in obs:
                if o.data.users > 1:
                    o.data = o.data.copy()
            with bpy.context.temp_override(active_object=obs[0], object=obs[0], selected_objects=obs, selected_editable_objects=obs):
                bpy.ops.object.join()
            obs[0].name = "%s %s %d %d" % (coll_name, role, gx, gy)
            obs[0]["kp_role"] = role
            merged += len(obs) - 1
    return merged


Course.underfloor = _underfloor
Course.merge_props = _merge_props
Course.underfloor_flat = _underfloor_flat
Course._lowest_surface = _lowest_surface
Course.glow = _glow



# ---------------------------------------------------------------- loop-the-loops

LOOP_SAMPLES = 1024


class LoopPath:
    """
    A loop-the-loop's road: the same curve as src/game/loops.ts (buildLoop / loopFrame),
    in Blender coordinates. It starts at (x, y, z) heading `head` (turtle degrees, 90 =
    north), climbs, goes over the top upside down and comes down `offset` metres to the
    right of where it started, a little way ahead, facing the same way. The pitch turns
    through 360°: its rate eases in over `ramp` metres, holds at 1/radius, and eases out.
    The game rides karts round it from track.json's "loop" entity (Course.loop), so this
    and loops.ts must stay in step: tests/loops.test.ts compares them through the
    entity's probe points.
    """

    def __init__(self, x, y, z, head, radius, ramp, offset, width):
        self.origin = Vector((x, y, z))
        self.head = head
        self.radius = radius
        self.ramp = ramp
        self.offset = offset
        self.width = width
        self.k0 = 1.0 / radius
        self.L = 2 * math.pi * radius + ramp
        n = LOOP_SAMPLES
        self.ds = self.L / n
        a = [0.0] * (n + 1)
        b = [0.0] * (n + 1)
        for i in range(n):
            phi = self.pitch((i + 0.5) * self.ds)
            a[i + 1] = a[i] + math.cos(phi) * self.ds
            b[i + 1] = b[i] + math.sin(phi) * self.ds
        self.a, self.b = a, b
        h = math.radians(head)
        self.fwd = Vector((math.cos(h), math.sin(h), 0.0))
        self.right = Vector((math.sin(h), -math.cos(h), 0.0))
        self.exit = self.origin + self.fwd * a[n] + self.right * offset + Vector((0, 0, b[n]))
        self.advance = a[n]
        self.height = max(b)

    def pitch(self, s):
        k0, r, L = self.k0, self.ramp, self.L
        if s <= 0:
            return 0.0
        if s >= L:
            return 2 * math.pi
        if r > 0 and s < r:
            return k0 * s * s / (2 * r)
        if r > 0 and s > L - r:
            return 2 * math.pi - k0 * (L - s) * (L - s) / (2 * r)
        return k0 * (r / 2) + k0 * (s - r)

    @staticmethod
    def _shift(u):
        t = clamp(u)
        return t * t * t * (t * (t * 6 - 15) + 10)

    @staticmethod
    def _shift_rate(u):
        t = clamp(u)
        return 30 * t * t * (1 - t) * (1 - t)

    def frame(self, s):
        """(point, tangent, normal, across) at distance s; straight beyond either end."""
        if s <= 0 or s >= self.L:
            o = self.origin if s <= 0 else self.exit
            along = s if s <= 0 else s - self.L
            return o + self.fwd * along, self.fwd.copy(), Vector((0, 0, 1)), self.right.copy()
        at = s / self.ds
        i = min(LOOP_SAMPLES - 1, int(math.floor(at)))
        t = at - i
        la = self.a[i] + (self.a[i + 1] - self.a[i]) * t
        lb = self.b[i] + (self.b[i + 1] - self.b[i]) * t
        u = s / self.L
        lc = self.offset * self._shift(u)
        phi = self.pitch(s)
        cc = self.offset * self._shift_rate(u) / self.L
        p = self.origin + self.fwd * la + self.right * lc + Vector((0, 0, lb))
        tan = (self.fwd * math.cos(phi) + Vector((0, 0, math.sin(phi))) + self.right * cc).normalized()
        nrm = self.right.cross(tan).normalized()
        across = tan.cross(nrm)
        return p, tan, nrm, across

    def point(self, s, across=0.0, up=0.0):
        p, _, n, b = self.frame(s)
        return p + b * across + n * up


def loop_layout(radius, ramp, offset):
    """How far ahead (and to the right) a loop's exit is from its entry: (ahead, right)."""
    lp = LoopPath(0, 0, 0, 90, radius, ramp, offset, 10)
    return lp.advance, offset


def _course_loop(
    self,
    lp,
    *,
    road_mat,
    side_mat,
    rail_mat,
    glow_mat=None,
    thickness=1.4,
    rail=0.9,
    step=0.6,
    min_speed=14.0,
    commit=18.0,
    boost=(1.45, 2.2),
    gravity=8.0,
    name="Loop",
    gaps=(),
):
    """
    Build a loop-the-loop's visible road (a solid deck with low rails along both edges,
    lit edge strips, a rock or ice underside) and add the "loop" entity that the game
    rides karts round with. The road is visual only: on the loop the kart follows the
    curve itself (src/game/loops.ts), so it never touches collision geometry there.
    `gaps`: stretches of it that are gone ((from, to) as fractions of its length: a ruin's
    loop with its top broken away). The game still rides karts across them.
    Returns the deck object.
    """
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    h = lp.width / 2
    rw = 0.55  # rail thickness
    road_tile = materials.entry(road_mat[0])["tileMetres"]
    side_tile = materials.entry(side_mat[0])["tileMetres"]
    # Cross-section (across, up) points, each strip with its material slot:
    # 0 road top, 1 rail faces, 2 underside and outer walls, 3 lit strip.
    strips = [
        (0, [(-h, 0.0), (-h / 2, 0.0), (0.0, 0.0), (h / 2, 0.0), (h, 0.0)]),
        (1, [(h, 0.0), (h, rail), (h + rw, rail)]),
        (2, [(h + rw, rail), (h + rw, -thickness), (-h - rw, -thickness), (-h - rw, rail)]),
        (1, [(-h - rw, rail), (-h, rail), (-h, 0.0)]),
    ]
    if glow_mat:
        strips.append((3, [(h - 0.05, rail * 0.45), (h - 0.05, rail * 0.75)]))
        strips.append((3, [(-h + 0.05, rail * 0.75), (-h + 0.05, rail * 0.45)]))
    n = max(8, int(math.ceil(lp.L / step)))
    frames = [lp.frame(lp.L * k / n) for k in range(n + 1)]
    for slot, pts in strips:
        rows = []
        for k, (p, tan, nrm, acr) in enumerate(frames):
            rows.append([bm.verts.new(p + acr * a + nrm * u) for a, u in pts])
        tile = road_tile if slot == 0 else side_tile
        # UV across: metres along the cross-section.
        lens = [0.0]
        for (a0, u0), (a1, u1) in zip(pts, pts[1:]):
            lens.append(lens[-1] + math.hypot(a1 - a0, u1 - u0))
        for k in range(n):
            if any(g0 <= (k + 0.5) / n <= g1 for g0, g1 in gaps):
                continue
            v0 = lp.L * k / n / tile
            v1 = lp.L * (k + 1) / n / tile
            for j in range(len(pts) - 1):
                quad = (rows[k][j], rows[k][j + 1], rows[k + 1][j + 1], rows[k + 1][j])
                f = bm.faces.new(quad)
                f.material_index = slot
                if slot == 3:
                    uvs = ((v0 * tile / 3.0, 0.25), (v0 * tile / 3.0, 0.75), (v1 * tile / 3.0, 0.75), (v1 * tile / 3.0, 0.25))
                else:
                    u0, u1 = lens[j] / tile, lens[j + 1] / tile
                    uvs = ((u0, v0), (u1, v0), (u1, v1), (u0, v1))
                for loop, (uu, vv) in zip(f.loops, uvs):
                    loop[uv].uv = (uu, vv)
    # End caps under the road where it meets the ordinary road (hidden mostly).
    bm.normal_update()
    ob = self.mesh_object(name, bm, "Loops", "visual")
    for m in (road_mat, side_mat, rail_mat, glow_mat or rail_mat):
        ob.data.materials.append(self.lib(*m) if isinstance(m, tuple) else self.lib(m))
    materials.ensure_paint(ob.data)
    materials.keep_uvs(ob, range(len(ob.data.polygons)))
    gx, gy, gz = self.game(*lp.origin)
    probe = []
    for f in (0.0, 0.12, 0.31, 0.5, 0.69, 0.88, 1.0):
        s = lp.L * f
        p = lp.point(s, 0.0)
        probe.append([round(s, 3)] + [round(v, 3) for v in (p.x, p.z, -p.y)])
    heading = (math.radians(lp.head) + math.pi / 2 + math.pi) % (2 * math.pi) - math.pi
    self.entities.append({
        "id": "loop_%02d" % (sum(e["type"] == "loop" for e in self.entities) + 1),
        "type": "loop",
        "x": round(lp.origin.x, 4), "y": round(lp.origin.z, 4), "z": round(-lp.origin.y, 4),
        "heading": round(heading, 6),
        "radius": lp.radius, "ramp": lp.ramp, "offset": lp.offset, "width": lp.width,
        "minSpeed": min_speed, "commit": commit,
        "boostMult": boost[0] if boost else 0, "boostSec": boost[1] if boost else 0,
        "gravity": gravity,
        "probe": probe,
    })
    return ob


Course.loop = _course_loop


def route_with_loops(pts, layout, z, every=10.0, width=None):
    """
    route_points_by for a layout with ("LOOP", ...) segments: control points every so
    many metres, but across each loop only its entry and exit (both exact, both sharp,
    so the route runs dead straight into and out of them). Returns (points, sharp
    indices, [(entry, exit)] as (x, y, z) points).
    """
    loops = [i for i, sg in enumerate(layout) if sg[0] == "LOOP"]
    # Distance along the path of each point.
    ds = [0.0]
    for a, b in zip(pts, pts[1:]):
        ds.append(ds[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    ends = []
    for li in loops:
        ks = [k for k, p in enumerate(pts) if p[3] == li]
        ends.append((ks[0] - 1, ks[-1]))  # entry = last point before the loop
    out = []
    sharp = []
    pairs = []
    next_at = 0.0
    k = 0
    while k < len(pts) - 1:
        x, y, _, seg = pts[k]
        hit = next((e for e in ends if e[0] == k), None)
        near = any(abs(ds[k] - ds[e[0]]) < 4 or abs(ds[k] - ds[e[1]]) < 4 for e in ends)
        if hit:
            for kk in hit:
                px, py, _, sg = pts[kk]
                p = (round(px, 3), round(py, 3), round(z(ds[kk], sg), 3))
                if width is not None:
                    p = p + (round(width(ds[kk], sg), 2),)
                sharp.append(len(out))
                out.append(p)
            pairs.append((out[-2][:3], out[-1][:3]))
            k = hit[1] + 1
            next_at = ds[hit[1]] + every
            continue
        if ds[k] >= next_at and not near:
            p = (round(x, 2), round(y, 2), round(z(ds[k], seg), 2))
            if width is not None:
                p = p + (round(width(ds[k], seg), 2),)
            out.append(p)
            next_at += every
        k += 1
    return out, sharp, pairs
