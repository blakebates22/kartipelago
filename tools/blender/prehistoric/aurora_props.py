# The Aurora Rift kit: crystal formations of several kinds (the Central Monolith, spire
# clusters like crystal cathedrals, fans, needles, hanging crystals, crystal gardens),
# amber lantern posts, natural ice arches and columns, icicle fringes, frozen falls.
# SPDX-License-Identifier: MIT
#
# Same rules as props.py: each prop is one mesh built once (Course.proto) and placed as
# copies, chunky and low-poly, all original designs. Big one-offs (the Monolith, the
# bridges' arches) are built in place by aurora_scenery.py with these helpers.

import math

from course_kit import Vector, bmesh, rnd
from props import _faces, blob, cuboid, tube

CYAN = "crystal_cyan"
VIOLET = "crystal_violet2"
MAGENTA = "crystal_magenta"
TEAL = "crystal_teal"
GOLD = "crystal_gold"
ICE = "glacier_wall"
SNOW = "rift_snow"
STONE = "rift_stone"
ROCK = "rift_rock"

CRYSTALS = (CYAN, VIOLET, TEAL, MAGENTA)


def _p(c, name, build):
    return c.proto(name, build) and name


def shard(bm, base, axis, length, r, n=6, tip=0.22, twist=0.0, flare=1.0):
    """A crystal: an n-sided prism from `base` along `axis` (any direction) ending in a
    point, `tip` of its length; `flare` widens it toward the top (1 = straight)."""
    a = Vector(axis).normalized()
    side = a.cross(Vector((0, 0, 1)))
    if side.length < 1e-3:
        side = Vector((1, 0, 0))
    side.normalize()
    up = side.cross(a).normalized()
    b = Vector(base)
    body = length * (1 - tip)
    rings = []
    for z, rr in ((0.0, r), (body, r * flare)):
        rings.append([bm.verts.new(b + a * z + (side * math.cos(twist + k * math.tau / n) + up * math.sin(twist + k * math.tau / n)) * rr) for k in range(n)])
    lo, hi = rings
    for k in range(n):
        bm.faces.new((lo[k], lo[(k + 1) % n], hi[(k + 1) % n], hi[k]))
    t = bm.verts.new(b + a * length)
    for k in range(n):
        bm.faces.new((hi[k], hi[(k + 1) % n], t))
    bm.faces.new(list(reversed(lo)))


def _lean(a, b, tilt):
    """A direction tilted `tilt` radians from straight up, toward compass angle a."""
    return Vector((math.sin(tilt) * math.cos(a), math.sin(tilt) * math.sin(a), math.cos(tilt) + b * 0))


# ------------------------------------------------------------------ crystal formations


def spire_cluster(c, variant=0, height=60.0, mat=CYAN, accent=VIOLET):
    """A crystal cathedral: a tall central spire ringed by tiers of smaller spires, all
    six-sided and pointed (origin at the foot). The big set pieces of the caverns."""
    name = "Spire Cluster %d %d %s" % (variant, int(height), mat)

    def build(bm):
        shard(bm, (0, 0, -4), (0.03 * math.sin(variant), 0.03, 1), height, height * 0.085, tip=0.2, twist=variant)
        main = _faces(bm, 0)
        k0 = len(bm.faces)
        n = 7 + variant % 3
        for i in range(n):
            a = i * math.tau / n + variant * 0.7
            tier = i % 2
            r = height * (0.1 + 0.05 * tier)
            h = height * (0.62 - 0.2 * tier) * (0.85 + 0.3 * rnd(i + variant * 11))
            shard(bm, (r * math.cos(a), r * math.sin(a), -3), _lean(a, 0, 0.12 + 0.1 * tier), h, height * 0.05, tip=0.24, twist=a)
        ring = _faces(bm, k0)
        k1 = len(bm.faces)
        for i in range(n + 3):
            a = i * math.tau / (n + 3) + 0.4 + variant
            r = height * (0.2 + 0.05 * rnd(i * 5 + variant))
            h = height * (0.18 + 0.12 * rnd(i * 3 + variant))
            shard(bm, (r * math.cos(a), r * math.sin(a), -2), _lean(a, 0, 0.35), h, height * 0.03, tip=0.3, twist=a)
        foot = _faces(bm, k1)
        return [(c.lib(mat), main + foot), (c.lib(accent), ring)]

    return _p(c, name, build)


def fan(c, variant=0, size=12.0, mat=CYAN):
    """A fan of crystals spraying out of one point, flattened in one plane (origin at the
    root, the fan opening toward +Y)."""
    name = "Crystal Fan %d %d %s" % (variant, int(size), mat)

    def build(bm):
        n = 5 + variant % 4
        for i in range(n):
            t = i / (n - 1) - 0.5
            a = t * 2.0  # spread across ~115 degrees
            ln = size * (0.55 + 0.45 * math.cos(t * 2.4)) * (0.8 + 0.3 * rnd(i + variant * 7))
            d = Vector((math.sin(a) * 0.35, 0.35 + 0.15 * rnd(i), math.cos(a)))
            shard(bm, (0, 0, -0.5), d, ln, size * 0.06 * (1.2 - abs(t)), tip=0.25, twist=i)
        return [(c.lib(mat), _faces(bm, 0))]

    return _p(c, name, build)


def needles(c, variant=0, height=30.0, mat=TEAL):
    """A sheaf of long, thin crystal needles, leaning a little apart (origin at the foot)."""
    name = "Crystal Needles %d %d %s" % (variant, int(height), mat)

    def build(bm):
        n = 3 + variant % 3
        for i in range(n):
            a = i * math.tau / n + variant
            h = height * (0.6 + 0.4 * rnd(i * 3 + variant))
            shard(bm, (1.2 * math.cos(a), 1.2 * math.sin(a), -2), _lean(a, 0, 0.08 + 0.08 * rnd(i + 9)), h, 0.7 + 0.5 * rnd(i), n=5, tip=0.18, twist=a)
        return [(c.lib(mat), _faces(bm, 0))]

    return _p(c, name, build)


def hanging(c, variant=0, length=20.0, mat=CYAN):
    """Crystal stalactites hanging from a ceiling (origin at the ceiling, they point down)."""
    name = "Hanging Crystals %d %d %s" % (variant, int(length), mat)

    def build(bm):
        n = 4 + variant % 4
        for i in range(n):
            a = i * 2.4 + variant
            r = 2.0 + 3.0 * rnd(i * 5 + variant)
            ln = length * (0.4 + 0.6 * rnd(i * 7 + variant))
            shard(bm, (r * math.cos(a), r * math.sin(a), 2.0), (0.08 * math.cos(a), 0.08 * math.sin(a), -1), ln, length * 0.07, tip=0.3, twist=a)
        return [(c.lib(mat), _faces(bm, 0))]

    return _p(c, name, build)


def garden(c, variant=0, radius=14.0):
    """A crystal garden: many small crystals of mixed colours in a low, spreading patch
    (origin at its middle)."""
    name = "Crystal Garden %d %d" % (variant, int(radius))

    def build(bm):
        slots = {m: [] for m in CRYSTALS}
        n = 14 + variant % 5
        for i in range(n):
            a = i * 2.399 + variant
            r = radius * math.sqrt((i + 0.5) / n)
            h = 3.0 + 7.0 * rnd(i * 3 + variant) * (1.2 - r / radius)
            m = CRYSTALS[(i + variant) % 4]
            k0 = len(bm.faces)
            shard(bm, (r * math.cos(a), r * math.sin(a), -1), _lean(a, 0, 0.25 + 0.3 * rnd(i)), h, 0.5 + 0.6 * rnd(i * 11), n=5, tip=0.3, twist=a)
            slots[m] += _faces(bm, k0)
        return [(c.lib(m), f) for m, f in slots.items() if f]

    return _p(c, name, build)


def amber_cluster(c, variant=0, size=6.0):
    """Warm amber crystals: the gold glow at the Monolith's foot."""
    name = "Amber Cluster %d %d" % (variant, int(size))

    def build(bm):
        n = 5 + variant % 3
        for i in range(n):
            a = i * math.tau / n + variant
            shard(bm, (1.2 * math.cos(a), 1.2 * math.sin(a), -0.5), _lean(a, 0, 0.3 + 0.2 * rnd(i)), size * (0.5 + 0.5 * rnd(i * 3 + variant)), size * 0.09, tip=0.3, twist=a)
        return [(c.lib(GOLD), _faces(bm, 0))]

    return _p(c, name, build)


# ------------------------------------------------------------------ lanterns and posts


def lantern_post(c, variant=0):
    """A squat stone post with a glowing amber lantern on top, snow on its roof (origin at
    the ground; the lantern's glass is 2.3 m up)."""
    name = "Lantern Post %d" % variant

    def build(bm):
        cuboid(bm, (0, 0, 0.7), (1.1, 1.1, 1.8))
        cuboid(bm, (0, 0, 1.7), (1.4, 1.4, 0.25))
        stone = _faces(bm, 0)
        k0 = len(bm.faces)
        cuboid(bm, (0, 0, 2.3), (0.8, 0.8, 0.95))
        glass = _faces(bm, k0)
        k1 = len(bm.faces)
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.85, radius2=0.08, depth=0.7)
        for v in res["verts"]:
            v.co = Vector((v.co.x, v.co.y, v.co.z + 3.1))
        bmesh.ops.rotate(bm, verts=res["verts"], cent=(0, 0, 3.1), matrix=__import__("mathutils").Matrix.Rotation(math.pi / 4, 3, "Z"))
        roof = _faces(bm, k1)
        k2 = len(bm.faces)
        blob(bm, (0, 0, 3.35), 0.5, sz=0.45)
        blob(bm, (0, 0, 1.9), 0.75, sz=0.18)
        snow = _faces(bm, k2)
        return [(c.lib(STONE), stone + roof), (c.lib("lantern_amber"), glass), (c.lib(SNOW), snow)]

    return _p(c, name, build)


def ice_column(c, variant=0, height=60.0, radius=6.0):
    """A massive natural column of ice from floor to ceiling, waisted and lumpy, with
    crystals growing from it (origin at the floor)."""
    name = "Ice Column %d %d" % (variant, int(height))

    def build(bm):
        pts, radii = [], []
        n = 10
        for k in range(n + 1):
            t = k / n
            pts.append((1.5 * math.sin(t * 3 + variant), 1.2 * math.cos(t * 2 + variant), -6 + (height + 12) * t))
            radii.append(radius * (1.25 - 0.55 * math.sin(math.pi * t)) * (1 + 0.15 * math.sin(k * 1.7 + variant)))
        tube(bm, pts, radii, n=8)
        for v in bm.verts:
            v.co += Vector((0.5 * math.sin(v.co.z * 0.3 + variant), 0.5 * math.cos(v.co.z * 0.23), 0))
        col = _faces(bm, 0)
        k0 = len(bm.faces)
        for i in range(5):
            a = i * 1.9 + variant
            z = height * (0.15 + 0.15 * i)
            r = radius * (1.1 - 0.4 * math.sin(math.pi * z / height))
            shard(bm, (r * math.cos(a), r * math.sin(a), z), (math.cos(a), math.sin(a), 0.6), 5 + 3 * rnd(i + variant), 0.8, tip=0.3, twist=a)
        return [(c.lib(ICE), col), (c.lib(CRYSTALS[variant % 4]), _faces(bm, k0))]

    return _p(c, name, build)


def icicle_fringe(c, variant=0, width=12.0, length=4.0):
    """A row of icicles hanging along an edge (origin at the edge's middle, along X)."""
    name = "Icicle Fringe %d %d %d" % (variant, int(width), int(length))

    def build(bm):
        n = max(4, int(width / 0.9))
        for i in range(n):
            x = -width / 2 + width * (i + 0.5) / n
            ln = length * (0.35 + 0.65 * rnd(i * 3 + variant))
            res = bmesh.ops.create_cone(bm, cap_ends=False, segments=4, radius1=0.0, radius2=0.18 + 0.12 * rnd(i + variant), depth=ln)
            for v in res["verts"]:
                v.co += Vector((x, 0.3 * math.sin(i * 1.3), -ln / 2))
        return [(c.lib("icefall_rift"), _faces(bm, 0))]

    return _p(c, name, build)


def ice_spike(c, variant=0, height=18.0):
    """A jagged spike of glacier ice (origin at the foot): the shattered ice round the
    Rift's rims and the snowfield."""
    name = "Ice Spike %d %d" % (variant, int(height))

    def build(bm):
        shard(bm, (0, 0, -3), (0.12 * math.sin(variant), 0.1 * math.cos(variant), 1), height, height * 0.16, n=5, tip=0.45, twist=variant, flare=0.7)
        k0 = len(bm.faces)
        shard(bm, (height * 0.12, 0, -3), (0.4, 0.1, 1), height * 0.5, height * 0.09, n=5, tip=0.5, twist=variant + 1, flare=0.7)
        shard(bm, (-height * 0.1, height * 0.08, -3), (-0.3, 0.3, 1), height * 0.38, height * 0.08, n=5, tip=0.5, twist=variant + 2, flare=0.7)
        return [(c.lib(ICE), list(range(k0))), (c.lib(ICE), _faces(bm, k0))]

    return _p(c, name, build)


def snow_rock(c, variant=0, size=4.0):
    """An indigo boulder with snow on its back."""
    name = "Snow Rock %d %d" % (variant, int(size))

    def build(bm):
        blob(bm, (0, 0, size * 0.25), size, sx=1.2, sy=0.9, sz=0.6)
        for v in bm.verts:
            v.co += Vector((0.4 * math.sin(v.co.y * 1.3 + variant), 0.3 * math.cos(v.co.x * 1.1), 0.25 * math.sin(v.co.x + v.co.y)))
        rock = _faces(bm, 0)
        k0 = len(bm.faces)
        blob(bm, (0, 0, size * 0.62), size * 0.8, sx=1.15, sy=0.85, sz=0.22)
        return [(c.lib(ROCK), rock), (c.lib(SNOW), _faces(bm, k0))]

    return _p(c, name, build)


def ice_arch_big(c, span=34.0, height=26.0):
    """A natural arch of glacier ice spanning a canyon (origin at the road's middle; the
    arch spans along X), lumpy, icicles under it, crystals on its back."""
    name = "Canyon Arch %d %d" % (int(span), int(height))

    def build(bm):
        pts, radii = [], []
        n = 14
        for k in range(n + 1):
            t = k / n
            a = math.pi * t
            pts.append((-math.cos(a) * (span / 2 + 4.0), 1.8 * math.sin(a * 2), math.sin(a) ** 0.75 * height - 3))
            radii.append((4.5 - 1.5 * math.sin(a)) * (1 + 0.18 * math.sin(k * 2.1)))
        tube(bm, pts, radii, n=7)
        for v in bm.verts:
            v.co += Vector((0.5 * math.sin(v.co.z * 0.6), 0.5 * math.cos(v.co.x * 0.5), 0.4 * math.sin(v.co.x * 0.8)))
        ice = _faces(bm, 0)
        k0 = len(bm.faces)
        for k in range(3, n - 2):
            x, y, z = pts[k]
            res = bmesh.ops.create_cone(bm, cap_ends=False, segments=4, radius1=0.0, radius2=0.35, depth=2.5 + 3 * rnd(k))
            for v in res["verts"]:
                v.co += Vector((x, y, z - radii[k] * 0.8 - 1.5))
        k1 = len(bm.faces)
        for k in range(2, n - 1, 3):
            x, y, z = pts[k]
            shard(bm, (x, y, z + radii[k] * 0.6), (0.2 * math.sin(k), 0.3, 1), 4 + 3 * rnd(k), 0.9, n=6, tip=0.3)
        return [(c.lib(ICE), ice), (c.lib("icefall_rift"), list(range(k0, k1))), (c.lib(VIOLET), _faces(bm, k1))]

    return _p(c, name, build)
