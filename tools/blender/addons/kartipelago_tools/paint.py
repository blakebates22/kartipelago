# Kartipelago Track Tools: vertex colour presets.
# SPDX-License-Identifier: MIT
"""
One-click colour variation painted into the "Col" colour attribute (glTF COLOR_0),
which library materials multiply into their texture, in Blender and in the game.

Every preset works on the selected objects, or in Edit Mode on just the selected faces,
and builds on what's already painted (press Reset to start again). For freehand work,
Blender's own Vertex Paint mode paints the same attribute.

Colours multiply, so presets can darken and tint; "lighten" presets bring colours back
towards white (undoing earlier darkening), they can't go brighter than the texture.
"""

import bpy
from mathutils import Vector, kdtree

from . import materials, road

PRESETS = [
    ("bottoms", "Darken Bottoms", "Darker towards the bottom (cliff bases, under ledges)"),
    ("tops", "Lighten Tops", "Brighter on faces that point up (exposed rock, ledges)"),
    ("sun", "Warm Sunlight", "Warm on sunlit sides, cool and darker in shade"),
    ("road_edge", "Tint Near Roads", "Tint ground near the road (worn, dry grass)"),
    ("cover", "Darken Under Cover", "Darken anything with something above it (tunnels, bridges)"),
    ("edges", "Blend Material Edges", "Tint where two materials meet (soft terrain transitions)"),
    ("reset", "Reset to White", "Remove all painted colour"),
]


def _lerp(a, b, t):
    return a + (b - a) * t


class Target:
    """One mesh object's colours as a flat list, plus what the presets need per corner."""

    def __init__(self, ob, faces):
        self.ob = ob
        me = ob.data
        self.ca = materials.ensure_paint(me)
        n = len(me.loops)
        self.cols = [1.0] * (4 * n)
        self.ca.data.foreach_get("color", self.cols)
        mw = ob.matrix_world
        nm = mw.inverted_safe().transposed().to_3x3()
        self.world = [mw @ v.co for v in me.vertices]
        self.corners = []  # (corner index, vertex index, world normal of its face)
        for p in me.polygons if faces is None else (me.polygons[i] for i in faces):
            fn = (nm @ p.normal).normalized()
            for li in p.loop_indices:
                self.corners.append((li, me.loops[li].vertex_index, fn))

    def mul(self, li, rgb):
        c = self.cols
        for k in range(3):
            c[4 * li + k] = max(0.0, min(1.0, c[4 * li + k] * rgb[k]))

    def toward_white(self, li, t):
        c = self.cols
        for k in range(3):
            c[4 * li + k] = _lerp(c[4 * li + k], 1.0, t)

    def write(self):
        self.ca.data.foreach_set("color", self.cols)
        self.ob.data.update()


def _road_points():
    """Points along every road's centre line (Blender coords) with the road's half-width."""
    from .export import sample_route

    pts = []
    for ob in materials.roads():
        settings = road.road_settings(ob) or {"width": 12.0, "shoulder": 0.0}
        for p in sample_route(ob, 2.0)["points"]:
            # Game (x, y, z) is Blender (x, -z, y).
            pts.append((Vector((p["x"], -p["z"], p["y"])), p["width"] / 2 + settings["shoulder"]))
    return pts


def run(preset, targets, strength, color, distance, sun_dir):
    """Apply a preset to the Target list."""
    s = strength
    if preset == "reset":
        for t in targets:
            t.cols = [1.0] * len(t.cols)
    elif preset == "bottoms":
        zs = [t.world[v].z for t in targets for _, v, _ in t.corners]
        if not zs:
            return
        lo, hi = min(zs), max(zs)
        span = max(hi - lo, 1e-6)
        for t in targets:
            for li, v, _ in t.corners:
                h = (t.world[v].z - lo) / span
                k = 1.0 - s * (1.0 - h) ** 1.5
                t.mul(li, (k, k, k * 1.02))
    elif preset == "tops":
        for t in targets:
            for li, _, n in t.corners:
                t.toward_white(li, s * max(0.0, n.z) ** 2)
    elif preset == "sun":
        sun = Vector(sun_dir).normalized()
        warm = Vector(color)
        cool = Vector((0.78, 0.83, 0.97))
        for t in targets:
            for li, _, n in t.corners:
                d = n.dot(sun)
                if d >= 0:
                    t.mul(li, [_lerp(1.0, warm[k], s * d) for k in range(3)])
                else:
                    t.mul(li, [_lerp(1.0, cool[k] * 0.85, s * -d) for k in range(3)])
    elif preset == "road_edge":
        pts = _road_points()
        if not pts:
            return
        tree = kdtree.KDTree(len(pts))
        for i, (p, _) in enumerate(pts):
            tree.insert(Vector((p.x, p.y, 0.0)), i)
        tree.balance()
        for t in targets:
            for li, v, _ in t.corners:
                w = t.world[v]
                q, i, dist = tree.find(Vector((w.x, w.y, 0.0)))
                past = max(0.0, dist - pts[i][1])
                k = max(0.0, 1.0 - past / max(distance, 1e-3))
                if k > 0:
                    t.mul(li, [_lerp(1.0, color[c], s * k) for c in range(3)])
    elif preset == "cover":
        dg = bpy.context.evaluated_depsgraph_get()
        scene = bpy.context.scene
        up = Vector((0.0, 0.0, 1.0))
        k = 1.0 - s
        for t in targets:
            hit_cache = {}
            for li, v, n in t.corners:
                if v not in hit_cache:
                    o = t.world[v] + n * 0.05 + up * 0.25
                    hit_cache[v] = scene.ray_cast(dg, o, up, distance=40.0)[0]
                if hit_cache[v]:
                    t.mul(li, (k, k, k * 1.05))
    elif preset == "edges":
        for t in targets:
            me = t.ob.data
            vmats = {}
            for p in me.polygons:
                for vi in p.vertices:
                    vmats.setdefault(vi, set()).add(p.material_index)
            border = {vi for vi, ms in vmats.items() if len(ms) > 1}
            ring = set()
            for e in me.edges:
                a, b = e.vertices
                if (a in border) != (b in border):
                    ring.add(b if a in border else a)
            for li, v, _ in t.corners:
                w = 1.0 if v in border else 0.45 if v in ring else 0.0
                if w:
                    t.mul(li, [_lerp(1.0, color[c], s * w) for c in range(3)])
    for t in targets:
        t.write()


def shade_roads(road_objs, strength):
    """Road surfaces are generated, so they're shaded by the road itself: a ray up
    from the road finds tunnel roofs and bridges (the KP Shade Casters collection)."""
    coll = materials.refresh_shade_casters()
    for ob in road_objs:
        mod = materials.road_modifier(ob)
        road.set_input(mod, "Shade Casters", coll)
        road.set_input(mod, "Shade Strength", strength)


def sun_direction(scene):
    """The environment's sun direction in Blender coordinates (game y-up to z-up)."""
    t = materials.theme(scene.kp_environment) if scene.kp_environment != "none" else None
    d = t["environment"]["sun"]["direction"] if t else (0.55, 0.75, 0.35)
    # Game (x, y, z) -> Blender (x, -z, y)
    return (d[0], -d[2], d[1])
