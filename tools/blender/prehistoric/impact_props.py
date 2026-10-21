# The Impact Depths kit: prehistoric plants (cycads, tree ferns, giant horsetails), cave
# formations (stalactites, stalagmites, glowing fungi), meteorites and lava rocks, sun
# beams for the skylights, the ancient gateway, the expedition's camp, bones.
# SPDX-License-Identifier: MIT
#
# Same rules as props.py: each prop is one mesh built once (Course.proto) and placed as
# copies, chunky and low-poly, all original designs.

import math

from aurora_props import shard
from course_kit import Vector, bmesh, rnd
from props import _faces, blob, cuboid, frond, loft, ring, tube
from volcano_props import prism


def _p(c, name, build):
    return c.proto(name, build) and name


# ------------------------------------------------------------------ the Lost World's plants


def cycad(c, variant=0):
    """A cycad: a stout, scaly trunk (sometimes forked) under a crown of stiff, arching
    fronds, a fat cone in the middle (origin at the ground; 3-6 m)."""
    name = "Cycad %d" % variant
    h = (2.2, 3.4, 4.6, 1.4)[variant % 4]

    def build(bm):
        tops = [(0.0, 0.0, h)]
        if variant % 4 == 2:
            tops = [(0.8, 0.2, h * 0.9), (-0.7, -0.3, h * 1.1)]
            tube(bm, [(0, 0, -0.4), (0, 0, h * 0.4)], [0.75, 0.7], n=8)
            for x, y, z in tops:
                tube(bm, [(0, 0, h * 0.35), (x * 0.6, y * 0.6, z * 0.7), (x, y, z)], [0.6, 0.55, 0.5], n=8)
        else:
            tube(bm, [(0, 0, -0.4), (0.1, 0, h * 0.5), (0, 0.05, h)], [0.8, 0.72, 0.62], n=8)
        trunk = _faces(bm, 0)
        k0 = len(bm.faces)
        for t, (x, y, z) in enumerate(tops):
            n = 11
            for i in range(n):
                a = i * math.tau / n + variant + t
                frond(bm, (x, y, z), a, 3.6 + 0.8 * rnd(i + variant), -1.2 - 0.6 * rnd(i * 3), 0.7, segs=4)
                frond(bm, (x, y, z + 0.3), a + 0.3, 2.6, 1.2, 0.5, segs=3)
        leaves = _faces(bm, k0)
        k1 = len(bm.faces)
        for x, y, z in tops:
            blob(bm, (x, y, z + 0.5), 0.55, sz=1.5, subdiv=1)
        cone = _faces(bm, k1)
        return [(c.lib("cycad_bark"), trunk + cone), (c.lib("cycad_leaf"), leaves)]

    return _p(c, name, build)


def tree_fern(c, variant=0):
    """A tree fern: a slender shaggy trunk and a wide umbrella of drooping fronds
    (origin at the ground; 7-11 m)."""
    name = "Tree Fern %d" % variant
    h = 7.0 + 1.5 * (variant % 3)

    def build(bm):
        lean = 0.6 * math.sin(variant * 1.9)
        tube(bm, [(0, 0, -0.4), (lean * 0.4, 0, h * 0.5), (lean, 0.2, h)], [0.45, 0.38, 0.34], n=6)
        trunk = _faces(bm, 0)
        k0 = len(bm.faces)
        n = 9
        for i in range(n):
            a = i * math.tau / n + variant * 0.7
            frond(bm, (lean, 0.2, h + 0.2), a, 4.8 + rnd(i + variant), -2.6, 1.0, segs=5)
        leaves = _faces(bm, k0)
        return [(c.lib("jungle_bark"), trunk), (c.lib("jungle_fern"), leaves)]

    return _p(c, name, build)


def horsetails(c, variant=0):
    """A stand of giant horsetails: jointed green stems with whorls of needle leaves
    (origin at the ground; 3-6 m)."""
    name = "Horsetails %d" % variant

    def build(bm):
        n = 6 + variant % 4
        for i in range(n):
            a = i * 2.39 + variant
            r = 1.4 * math.sqrt(rnd(i * 3 + variant))
            x, y = r * math.cos(a), r * math.sin(a)
            h = 3.0 + 3.0 * rnd(i * 7 + variant)
            tube(bm, [(x, y, -0.3), (x + 0.15, y, h * 0.5), (x + 0.3 * math.cos(a), y + 0.3 * math.sin(a), h)], [0.16, 0.13, 0.08], n=5)
            for k in range(1, 4):
                z = h * k / 4
                for j in range(5):
                    b = j * math.tau / 5 + k
                    tip = Vector((x + 0.9 * math.cos(b), y + 0.9 * math.sin(b), z + 0.4))
                    v0 = bm.verts.new((x, y, z))
                    v1 = bm.verts.new((x + 0.12 * math.cos(b + 1.5), y + 0.12 * math.sin(b + 1.5), z + 0.1))
                    bm.faces.new((v0, v1, bm.verts.new(tip)))
        return [(c.lib("horsetail"), _faces(bm, 0))]

    return _p(c, name, build)


def giant_fungi(c, variant=0, mat="glow_fungus"):
    """A cluster of giant glowing cave fungi: pale stalks, broad luminous caps (origin
    at the ground; 2-5 m)."""
    name = "Giant Fungi %d %s" % (variant, mat)

    def build(bm):
        caps = []
        n = 3 + variant % 3
        for i in range(n):
            a = i * 2.2 + variant
            r = 1.6 * rnd(i + variant * 5)
            x, y = r * math.cos(a), r * math.sin(a)
            h = 1.6 + 3.2 * rnd(i * 3 + variant)
            tube(bm, [(x, y, -0.2), (x + 0.2, y, h * 0.6), (x + 0.1, y + 0.1, h)], [0.28, 0.22, 0.2], n=6)
            caps.append((x + 0.1, y + 0.1, h, 0.9 + 0.9 * rnd(i * 7 + variant)))
        stalks = _faces(bm, 0)
        k0 = len(bm.faces)
        for x, y, z, r in caps:
            loft(bm, [ring(bm, (x, y), r * 0.3, z - 0.1, 8), ring(bm, (x, y), r, z + 0.1, 8), ring(bm, (x, y), r * 0.75, z + 0.45, 8),
                      ring(bm, (x, y), r * 0.2, z + 0.6, 8)], cap_top=True, cap_bottom=True)
        cap = _faces(bm, k0)
        return [(c.lib("flowstone"), stalks), (c.lib(mat), cap)]

    return _p(c, name, build)


def nest(c):
    """A dinosaur nest: a ring of trampled fern and mud, a clutch of big speckled eggs."""
    name = "Dino Nest"

    def build(bm):
        loft(bm, [ring(bm, (0, 0), 2.6, -0.2, 10), ring(bm, (0, 0), 2.2, 0.5, 10), ring(bm, (0, 0), 1.6, 0.35, 10)], cap_top=True)
        mud = _faces(bm, 0)
        k0 = len(bm.faces)
        for i in range(5):
            a = i * math.tau / 5
            blob(bm, (0.8 * math.cos(a), 0.8 * math.sin(a), 0.75), 0.42, sz=1.35, subdiv=1)
        eggs = _faces(bm, k0)
        return [(c.lib("jungle_mud"), mud), (c.lib("bone"), eggs)]

    return _p(c, name, build)


# ------------------------------------------------------------------ cave formations


def stalactites(c, mat, variant=0, length=10.0):
    """A cluster of stalactites hanging from the roof (origin at the roof, pointing down;
    the root sunk 2 m up into it)."""
    name = "Stalactites %s %d %d" % (mat, variant, int(length))

    def build(bm):
        n = 3 + variant % 4
        for k in range(n):
            a = k * 1.7 + variant
            r = 3.0 * rnd(k * 3 + variant)
            x, y = r * math.cos(a), r * math.sin(a)
            ln = length * (0.35 + 0.65 * rnd(k * 7 + variant))
            w = ln * 0.16 + 0.4
            prism(bm, (x, y, 2.0), (x * 0.9, y * 0.9, -ln * 0.45), w, w * 0.5, n=6, phase=a, tip=(x * 0.85, y * 0.85, -ln))
        return [(c.lib(mat), _faces(bm, 0))]

    return _p(c, name, build)


def stalagmites(c, mat, variant=0, height=6.0):
    """Stalagmites rising from the floor (origin at the ground)."""
    name = "Stalagmites %s %d %d" % (mat, variant, int(height))

    def build(bm):
        n = 2 + variant % 4
        for k in range(n):
            a = k * 2.3 + variant
            r = 2.2 * rnd(k * 5 + variant)
            x, y = r * math.cos(a), r * math.sin(a)
            hh = height * (0.4 + 0.6 * rnd(k * 9 + variant))
            w = hh * 0.2 + 0.5
            prism(bm, (x, y, -1.0), (x * 1.05, y * 1.05, hh * 0.5), w, w * 0.55, n=6, phase=a, tip=(x * 1.1, y * 1.1, hh))
        return [(c.lib(mat), _faces(bm, 0))]

    return _p(c, name, build)


def column(c, mat, height=30.0, variant=0):
    """A cave column from floor to roof, pinched where stalactite met stalagmite (origin
    at the foot)."""
    name = "Cave Column %s %d %d" % (mat, int(height), variant)

    def build(bm):
        rings = []
        for k in range(9):
            t = k / 8
            r = (4.5 + 1.0 * rnd(variant)) * (0.45 + 0.55 * (abs(t - 0.52) * 2) ** 1.4) * (1 + 0.1 * math.sin(k * 2.1 + variant))
            rings.append(ring(bm, (0.6 * math.sin(t * 3 + variant), 0.4 * math.cos(t * 2.3)), r, -2.0 + (height + 4.0) * t, 8, phase=k * 0.3))
        loft(bm, rings, cap_top=True, cap_bottom=True)
        return [(c.lib(mat), _faces(bm, 0))]

    return _p(c, name, build)


def rock(c, mat, variant=0, size=3.0, glow=None):
    """A lumpy boulder (origin at its foot); with `glow`, some faces glow (cracks)."""
    name = "Rock %s %d %d %s" % (mat, variant, int(size * 10), glow)

    def build(bm):
        blob(bm, (0, 0, size * 0.35), size, sx=1.2 + 0.2 * math.sin(variant), sy=0.95, sz=0.72, subdiv=1)
        for v in bm.verts:
            v.co.x += size * 0.12 * math.sin(v.co.y * 2.1 / size + variant)
            v.co.z += size * 0.1 * math.cos(v.co.x * 1.7 / size + variant * 2)
        faces = _faces(bm, 0)
        if glow is None:
            return [(c.lib(mat), faces)]
        hot = [f for f in faces if (f * 7 + variant) % 5 == 0]
        cold = [f for f in faces if f not in hot]
        return [(c.lib(mat), cold), (c.lib(glow), hot)]

    return _p(c, name, build)


def meteorite(c, variant=0, size=3.0):
    """A fallen fragment of the asteroid: dark pitted rock split by glowing cracks,
    half buried, a ring of thrown-up dirt round it (origin at the ground)."""
    name = "Meteorite %d %d" % (variant, int(size * 10))

    def build(bm):
        res = blob(bm, (0, 0, size * 0.2), size, sx=1.3, sy=1.0, sz=0.8, subdiv=2)
        for v in res["verts"]:
            k = 1.0 + 0.18 * math.sin(v.co.x * 2.3 / size + variant) * math.cos(v.co.y * 1.9 / size) + 0.1 * math.sin(v.co.z * 3.1 / size)
            v.co = Vector((v.co.x * k, v.co.y * k, v.co.z * k))
        faces = _faces(bm, 0)
        bm.faces.ensure_lookup_table()
        hot = [i for i in faces if abs(math.sin(bm.faces[i].calc_center_median().x * 1.7 / size + variant) +
                                       math.cos(bm.faces[i].calc_center_median().y * 1.3 / size)) < 0.22]
        cold = [i for i in faces if i not in set(hot)]
        k0 = len(bm.faces)
        loft(bm, [ring(bm, (0, 0), size * 2.2, -0.3, 12), ring(bm, (0, 0), size * 1.7, size * 0.25, 12, phase=0.2),
                  ring(bm, (0, 0), size * 1.25, 0.0, 12)], cap_top=False)
        dirt = _faces(bm, k0)
        return [(c.lib("asteroid_rock"), cold), (c.lib("asteroid_vein"), hot), (c.lib("crater_ground"), dirt)]

    return _p(c, name, build)


def glass_shards(c, variant=0):
    """Impact glass: a spray of dark glassy blades standing out of the ground."""
    name = "Impact Glass %d" % variant

    def build(bm):
        for i in range(5 + variant % 3):
            a = i * 1.9 + variant
            shard(bm, (1.2 * math.cos(a), 1.2 * math.sin(a), -0.5), (0.4 * math.cos(a), 0.4 * math.sin(a), 1), 2.0 + 2.5 * rnd(i + variant), 0.35,
                  n=4, tip=0.4, twist=a)
        return [(c.lib("impact_glass"), _faces(bm, 0))]

    return _p(c, name, build)


def sun_beam(c, length=40.0, r=6.0, variant=0):
    """A shaft of sunlight falling through a hole in the roof: an open, see-through,
    glowing cylinder slanting down the sun's way (origin at the top)."""
    name = "Sun Beam %d %d %d" % (int(length), int(r), variant)
    # The sun's direction (the theme's [-0.34, 0.86, -0.38] in Blender's axes), reversed.
    d = Vector((0.34, -0.38, -0.86)).normalized()

    def build(bm):
        n = 10
        rings = []
        for k in range(4):
            t = k / 3
            c0 = d * length * t
            rr = r * (1.0 + 0.35 * t)
            rings.append([bm.verts.new(c0 + Vector((rr * math.cos(i * math.tau / n + variant), rr * math.sin(i * math.tau / n + variant), 0)))
                          for i in range(n)])
        loft(bm, rings, cap_top=False, cap_bottom=False)
        return [(c.lib("light_shaft"), _faces(bm, 0))]

    return _p(c, name, build)


# ------------------------------------------------------------------ ruins and works


def gateway(c, width=12.0, height=11.0):
    """The ancient gateway: two great carved pillars, a cracked lintel with glowing
    glyphs, rubble at their feet (origin at the middle of the threshold; the way through
    runs along Y)."""
    name = "Ancient Gateway %d" % int(width)

    def build(bm):
        hw = width / 2
        for s in (-1, 1):
            cuboid(bm, (s * (hw + 2.0), 0, height / 2 - 0.5), (4.0, 4.6, height + 1.0))
            cuboid(bm, (s * (hw + 2.0), 0, -0.2), (5.2, 5.8, 1.2))
        stone = _faces(bm, 0)
        k0 = len(bm.faces)
        cuboid(bm, (0, 0, height + 1.4), (width + 9.0, 5.0, 2.8), tilt=(0.0, 0.03))
        cuboid(bm, (-1.0, 0, height + 3.4), (width + 4.0, 3.6, 1.2))
        lintel = _faces(bm, k0)
        k1 = len(bm.faces)
        for s in (-1, 1):
            cuboid(bm, (s * (hw + 0.05), 0, height * 0.55), (0.2, 3.0, height * 0.7))
        glyph = _faces(bm, k1)
        k2 = len(bm.faces)
        for i in range(5):
            a = i * 1.3
            cuboid(bm, ((hw + 5.5) * (1 if i % 2 else -1) + rnd(i) * 2, -3.0 + 6 * rnd(i + 3), 0.4), (1.6, 1.4, 1.2), rot=a, tilt=(0.2, 0.1))
        rubble = _faces(bm, k2)
        return [(c.lib("ruin_moss"), stone + rubble), (c.lib("ruin_stone"), lintel), (c.lib("ancient_glyph"), glyph)]

    return _p(c, name, build)


def obelisk(c, variant=0, height=9.0):
    """A leaning carved obelisk, glyphs glowing faintly (origin at the foot)."""
    name = "Obelisk %d %d" % (variant, int(height))

    def build(bm):
        tilt = (0.08 * math.sin(variant * 1.3), 0.06 * math.cos(variant))
        cuboid(bm, (0, 0, 0.3), (3.0, 3.0, 0.8))
        base = _faces(bm, 0)
        k0 = len(bm.faces)
        prism(bm, (0, 0, 0.6), (math.sin(tilt[1]) * height, -math.sin(tilt[0]) * height, height), 1.2, 0.8, n=4, phase=math.pi / 4,
              tip=(math.sin(tilt[1]) * height * 1.1, -math.sin(tilt[0]) * height * 1.1, height + 1.6))
        body = _faces(bm, k0)
        return [(c.lib("ruin_moss"), base), (c.lib("ancient_glyph"), body)]

    return _p(c, name, build)


def tent(c, variant=0):
    """An expedition tent: a ridge tent of canvas on poles, guy lines, a crate by the door."""
    name = "Tent %d" % variant

    def build(bm):
        w, d, h = 3.6, 4.6, 2.6
        vs = [bm.verts.new(p) for p in ((-w / 2, -d / 2, 0), (w / 2, -d / 2, 0), (0, -d / 2, h), (-w / 2, d / 2, 0), (w / 2, d / 2, 0), (0, d / 2, h))]
        bm.faces.new((vs[0], vs[3], vs[5], vs[2]))
        bm.faces.new((vs[4], vs[1], vs[2], vs[5]))
        bm.faces.new((vs[1], vs[0], vs[2]))
        bm.faces.new((vs[3], vs[4], vs[5]))
        canvas = _faces(bm, 0)
        k0 = len(bm.faces)
        cuboid(bm, (1.2, -d / 2 - 0.9, 0.4), (0.8, 0.8, 0.8), rot=0.3)
        tube(bm, [(0, -d / 2 - 0.2, 0), (0, -d / 2 - 0.2, h + 0.4)], 0.06, n=4)
        tube(bm, [(0, d / 2 + 0.2, 0), (0, d / 2 + 0.2, h + 0.4)], 0.06, n=4)
        wood = _faces(bm, k0)
        return [(c.lib("canvas_sun" if variant % 2 == 0 else "canvas_blue"), canvas), (c.lib("weathered_timber"), wood)]

    return _p(c, name, build)


def survey_scope(c):
    """The expedition's big telescope on a tripod, aimed at the asteroid."""
    name = "Survey Scope"

    def build(bm):
        for a in (0.0, 2.1, 4.2):
            tube(bm, [(1.2 * math.cos(a), 1.2 * math.sin(a), -0.2), (0, 0, 2.2)], 0.07, n=4)
        legs = _faces(bm, 0)
        k0 = len(bm.faces)
        tube(bm, [(-0.9, 0, 1.9), (1.4, 0, 2.7)], [0.22, 0.3], n=8)
        body = _faces(bm, k0)
        return [(c.lib("weathered_timber"), legs), (c.lib("iron"), body)]

    return _p(c, name, build)


def warning_sign(c, variant=0):
    """A striped warning board on two posts at the crater's edge."""
    name = "Warning Sign %d" % variant

    def build(bm):
        for s in (-1, 1):
            tube(bm, [(s * 1.1, 0, -0.3), (s * 1.1, 0, 2.4)], 0.09, n=4)
        posts = _faces(bm, 0)
        k0 = len(bm.faces)
        cuboid(bm, (0, 0, 1.8), (2.8, 0.12, 0.9), tilt=(0.0, 0.05 * (variant % 3 - 1)))
        board = _faces(bm, k0)
        return [(c.lib("weathered_timber"), posts), (c.lib("warning_stripe"), board)]

    return _p(c, name, build)


def bones(c, variant=0):
    """Huge old bones by the lair: a curve of ribs and a long thigh bone."""
    name = "Bones %d" % variant

    def build(bm):
        n = 5 + variant % 3
        for i in range(n):
            x = (i - n / 2) * 1.4
            tube(bm, [(x, -2.6, 0), (x, -2.2, 2.6), (x, 0, 3.6), (x, 2.2, 2.6), (x, 2.6, 0)], 0.22, n=5)
        tube(bm, [(-n * 0.8, 0, 2.4), (n * 0.8, 0, 2.6)], 0.32, n=6)
        tube(bm, [(n * 0.9, 3.5, 0.3), (n * 0.9 + 4.0, 5.0, 0.4)], [0.35, 0.3], n=6)
        blob(bm, (n * 0.9 + 4.3, 5.1, 0.45), 0.6, subdiv=0)
        return [(c.lib("bone_pile"), _faces(bm, 0))]

    return _p(c, name, build)


def lava_spire(c, variant=0, height=14.0):
    """A jagged spire of black volcanic rock, cracks glowing (origin at the foot)."""
    name = "Lava Spire %d %d" % (variant, int(height))

    def build(bm):
        rock_, hot = [], []
        for k, (x, y, h, r) in enumerate(((0, 0, height, 3.4), (2.6, 1.2, height * 0.6, 2.2), (-2.2, 1.6, height * 0.45, 1.9))):
            f = prism(bm, (x, y, -2), (x * 1.1, y * 1.1, h * 0.65), r, r * 0.5, n=5, phase=k + variant, tip=(x * 0.9 + 0.6, y * 0.9, h))
            for i, fi in enumerate(f):
                (hot if (i + k + variant) % 5 == 0 else rock_).append(fi)
        return [(c.lib("black_rock"), rock_), (c.lib("lava_crust"), hot)]

    return _p(c, name, build)
