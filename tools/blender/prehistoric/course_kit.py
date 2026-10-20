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
        return materials.get_material(materials.entry(mat_id), surface)

    def assign(self, ob, mat, faces=None, size=None):
        """Put a library material on faces (all by default), with projected UVs."""
        e = materials.entry(mat["kp_texture"])
        if faces is None:
            faces = range(len(ob.data.polygons))
        materials.assign_faces(ob, mat, list(faces), size or e["tileMetres"], 0.0, materials.aspect(e))

    # -------------------------------------------------------------- the route

    def route(self, points, width=13.0, bank=8.0, bank_gain=40.0, spacing=1.0):
        """
        The race line through (x, y, z[, width]) control points, a closed loop. Banking is
        worked out from the curvature: up to `bank` degrees, into every turn.
        """
        self.width = width
        cd = bpy.data.curves.new("Route", "CURVE")
        cd.dimensions = "3D"
        cd.twist_mode = "Z_UP"
        sp = cd.splines.new("BEZIER")
        sp.bezier_points.add(len(points) - 1)
        for bp, p in zip(sp.bezier_points, points):
            bp.co = p[:3]
            bp.handle_left_type = bp.handle_right_type = "AUTO"
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
            bp.tilt = math.radians(-clamp(ks[i] * bank_gain, -1, 1) * bank)
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
            t = (pos(min(s1, sk + 0.5)) - pos(max(s0, sk - 0.5))).normalized() if lift else smp.t
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
        if not self.S[j].ground and dj < self.S[j].w / 2 + 4:
            below = self.S[j].p.z - 3.0
            return (1.0, below) if nat is not None and nat > below else (0.0, 0.0)
        hits = self._ground_tree.find_range(Vector((x, y, 0)), near + fade)
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
            smp = Sample(Vector((p["x"], -p["z"], p["y"])), width, 0.0, 0.0)
            self.extra_ground.append(smp)
        return ob

    def build_ground_tree(self):
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

    def terrain(self, name, x0, x1, y0, y1, cell, natural, classify, *, near=9.0, fade=20.0, under=0.2):
        """
        A height-field grid over [x0, x1] x [y0, y1]. `natural(x, y)` is the land's own
        height; near the roads it's pulled to meet them. `classify(face_centre, normal,
        info)` returns a material per face (info: distance to the route).
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
                row.append(bm.verts.new((x, y, lerp(nat, z, w))))
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

    def tunnel(self, rock, s0, s1, half=None, height=8.5, pad=12.0):
        """Cut a tunnel through `rock` along the route from s0 to s1 (padded at both ends)."""
        half = half or self.width / 2 + 3.5
        prof = [(-half, -0.4), (half, -0.4), (half, height * 0.62), (half * 0.62, height), (-half * 0.62, height), (-half, height * 0.62)]
        bm = bmesh.new()
        rings = []
        n = max(4, math.ceil((s1 - s0 + 2 * pad) / 2.0))
        for k in range(n + 1):
            smp = self.at(s0 - pad + (s1 - s0 + 2 * pad) * k / n)
            rings.append([bm.verts.new(smp.p + smp.r * a + Vector((0, 0, b))) for a, b in prof])
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
            rows.append([q.side(-half + half * 2 * k / 8, 0.04) for k in range(9)])
        verts = [[bm.verts.new(v) for v in r] for r in rows]
        for k in range(8):
            f = bm.faces.new((verts[0][k], verts[0][k + 1], verts[1][k + 1], verts[1][k]))
            for loop, (u, v) in zip(f.loops, ((k, 0), (k + 1, 0), (k + 1, 1), (k, 1))):
                loop[uv].uv = (u / 4, v / 2)
        # The grid: a white bar in front of each starting slot, matching the game's own
        # grid (src/race/grid.ts: rows 7 m apart from 5 m back, columns 4.5 m off the
        # centre, the right-hand column half a row further back).
        for slot in range(8):
            back = 5 + (slot // 2) * 7 + (slot % 2) * 3.5 - 1.3
            side = -1 if slot % 2 == 0 else 1
            q = self.at(-back)
            o = side * 4.5
            corners = [q.side(o - 1.7, 0.04) - q.t * 0.25, q.side(o + 1.7, 0.04) - q.t * 0.25,
                       q.side(o + 1.7, 0.04) + q.t * 0.25, q.side(o - 1.7, 0.04) + q.t * 0.25]
            f = bm.faces.new([bm.verts.new(v) for v in corners])
            for loop, uvp in zip(f.loops, ((0.01, 0.02), (0.11, 0.02), (0.11, 0.2), (0.01, 0.2))):
                loop[uv].uv = uvp
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
        meta["entities"] = self.entities
        if extra:
            meta.update(extra)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
            f.write("\n")
        rep["length"] = round(self.length, 1)
        rep["props"] = self.prop_count
        print("EXPORTED", json.dumps(rep))
        return rep


def s_near(course, x, y):
    """Distance along the route of the route point nearest (x, y)."""
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


def _glow(self, obs, lights, radius, color, base=1.0, region=None):
    """
    Hand-painted light: every vertex inside `region(point)` (or everywhere) is darkened
    to `base`, then lit back up near each light point, tinted `color`, fading out over
    `radius` metres. For torchlit tunnels.
    """
    from kartipelago_tools import paint as _paint

    for ob in obs:
        t = _paint.Target(ob, None)
        for li, v, _ in t.corners:
            w = t.world[v]
            if region is not None and not region(w):
                continue
            k = 0.0
            for lp in lights:
                d = (w - Vector(lp)).length
                k = max(k, 1.0 - d / radius)
            k = max(0.0, k) ** 1.4
            t.mul(li, [base + (color[c] - base) * k for c in range(3)])
        t.write()


Course.underfloor = _underfloor
Course.glow = _glow

