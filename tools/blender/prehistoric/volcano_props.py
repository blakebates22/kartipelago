# The volcanic kit for Ember Peak: obsidian spires, clusters, leaning slabs and
# arches with glowing veins; basalt bridge piers and arches; ruined pillars;
# stalactites and cave columns; red and purple crystal clusters; braziers; charred and
# burning trees; smoke plumes and distant volcanoes.
# SPDX-License-Identifier: MIT
#
# Each builder makes one mesh (once per course, through Course.proto) that every copy
# shares, so editing "Prop Obsidian Spire 0" in the .blend edits every copy. All
# original designs, kept low-poly in the spirit of late-90s console scenery.

import math

from course_kit import Vector, bmesh, rnd
from props import _faces, blob, cuboid, loft, ring, tube

OBS = "obsidian"
VEIN = "obsidian_vein"


def _p(c, name, build):
    return c.proto(name, build) and name


def prism(bm, base, top, r0, r1, n=5, phase=0.0, tip=None):
    """A tapering n-sided prism from base to top (x, y, z), optionally ending in a
    point at `tip`. Returns the side faces' indices, alternating (for veins)."""
    k0 = len(bm.faces)
    lo = [bm.verts.new((base[0] + r0 * math.cos(phase + i * math.tau / n), base[1] + r0 * math.sin(phase + i * math.tau / n), base[2])) for i in range(n)]
    hi = [bm.verts.new((top[0] + r1 * math.cos(phase + 0.3 + i * math.tau / n), top[1] + r1 * math.sin(phase + 0.3 + i * math.tau / n), top[2])) for i in range(n)]
    for i in range(n):
        bm.faces.new((lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i]))
    if tip is not None:
        t = bm.verts.new(tip)
        for i in range(n):
            bm.faces.new((hi[i], hi[(i + 1) % n], t))
    else:
        bm.faces.new(hi)
    bm.faces.new(list(reversed(lo)))
    return _faces(bm, k0)


def obsidian_spire(c, variant=0):
    """A tall, sharp obsidian spire (about 30 m) split by glowing veins, with a couple
    of smaller shards at its foot (origin at the ground)."""
    name = "Obsidian Spire %d" % variant

    def build(bm):
        h = 24.0 + 8.0 * variant
        lean = (2.5 * math.sin(variant * 1.7), 2.0 * math.cos(variant * 2.3))
        obs, vein = [], []
        f = prism(bm, (0, 0, -2), (lean[0] * 0.6, lean[1] * 0.6, h * 0.62), 4.2, 2.6, n=5, phase=variant, tip=None)
        for i, fi in enumerate(f):
            (vein if i in (1, 3) else obs).append(fi)
        f = prism(bm, (lean[0] * 0.6, lean[1] * 0.6, h * 0.62), (lean[0], lean[1], h * 0.85), 2.6, 1.2, n=5, phase=variant, tip=(lean[0] * 1.2, lean[1] * 1.2, h))
        for i, fi in enumerate(f):
            (vein if i == 2 else obs).append(fi)
        for k in range(3):
            a = k * 2.1 + variant
            x, y = 5.0 * math.cos(a), 5.0 * math.sin(a)
            hh = 4.0 + 4.0 * rnd(k + variant * 3)
            f = prism(bm, (x, y, -1), (x * 1.2, y * 1.2, hh * 0.7), 1.6, 0.8, n=4, phase=a, tip=(x * 1.35, y * 1.35, hh))
            obs += f
        return [(c.lib(OBS), obs), (c.lib(VEIN), vein)]

    return _p(c, name, build)


def obsidian_cluster(c, variant=0):
    """A cluster of black glass shards bursting from the ground (about 10 m)."""
    name = "Obsidian Cluster %d" % variant

    def build(bm):
        obs, vein = [], []
        for k in range(6):
            a = k * 1.05 + variant * 0.7
            r = 1.5 + 2.5 * rnd(k * 3 + variant)
            x, y = r * math.cos(a), r * math.sin(a)
            h = 4.0 + 7.0 * rnd(k * 5 + variant)
            out = 0.35 + 0.3 * rnd(k + variant)
            tip = (x + out * h * math.cos(a), y + out * h * math.sin(a), h)
            f = prism(bm, (x, y, -1), ((x + tip[0]) / 2, (y + tip[1]) / 2, h * 0.55), 1.4, 0.9, n=4, phase=a, tip=tip)
            (vein if k % 3 == 0 else obs).extend(f)
        return [(c.lib(OBS), obs), (c.lib(VEIN), vein)]

    return _p(c, name, build)


def leaning_slab(c, variant=0):
    """A huge broken slab of obsidian leaning out over the ground (about 20 m tall;
    it leans toward +X), veined along its edge."""
    name = "Obsidian Slab %d" % variant

    def build(bm):
        h = 18.0 + 6.0 * variant
        k0 = len(bm.faces)
        cuboid(bm, (h * 0.22, 0, h * 0.45), (5.5, 3.0, h), tilt=(0.0, 0.5 + 0.1 * variant))
        obs = _faces(bm, k0)
        k1 = len(bm.faces)
        cuboid(bm, (h * 0.22 + 0.2, 1.55, h * 0.45), (4.2, 0.2, h * 0.9), tilt=(0.0, 0.5 + 0.1 * variant))
        vein = _faces(bm, k1)
        k2 = len(bm.faces)
        for k in range(3):
            cuboid(bm, (-3 + k * 2.5, 3 + k, 0.6), (2.5, 2.0, 2.0), rot=k, tilt=(0.3, 0.2))
        obs += _faces(bm, k2)
        return [(c.lib(OBS), obs), (c.lib(VEIN), vein)]

    return _p(c, name, build)


def obsidian_arch(c, span=26.0, variant=0):
    """A natural arch of black glass: two leaning legs meeting overhead, veined (origin
    at the middle of its feet; the span runs along X)."""
    name = "Obsidian Arch %d" % variant

    def build(bm):
        obs, vein = [], []
        h = span * 0.85
        pts = []
        for j in range(9):
            u = j / 8
            x = -span / 2 * math.cos(u * math.pi)
            z = -1 + (h + 1) * math.sin(u * math.pi) ** 0.8
            pts.append((x, 0.0, z))
        k0 = len(bm.faces)
        tube(bm, pts, [3.4, 2.8, 2.2, 1.8, 1.7, 1.8, 2.2, 2.8, 3.4], n=5)
        f = _faces(bm, k0)
        for i, fi in enumerate(f):
            (vein if i % 5 == 2 else obs).append(fi)
        for s in (-1, 1):
            k1 = len(bm.faces)
            prism(bm, (s * span / 2, 0, -1), (s * (span / 2 + 1), 0.5, 6), 4.5, 3.0, n=5, phase=s, tip=(s * (span / 2 + 2), 0.0, 10))
            obs += _faces(bm, k1)
        return [(c.lib(OBS), obs), (c.lib(VEIN), vein)]

    return _p(c, name, build)


def ruin_pillar(c, variant=0):
    """An ancient basalt pillar with a glowing rune band, broken at the top (origin at
    its foot, about 12 m)."""
    name = "Ruin Pillar %d" % variant

    def build(bm):
        h = 9.0 + 3.0 * variant
        cuboid(bm, (0, 0, 0.6), (4.0, 4.0, 1.2))
        cuboid(bm, (0, 0, h / 2 + 0.6), (2.6, 2.6, h - 1.2))
        if variant % 2 == 0:
            cuboid(bm, (0, 0, h + 0.4), (3.6, 3.6, 0.9))
        else:
            cuboid(bm, (0.4, 0.2, h + 0.6), (2.6, 2.6, 1.6), rot=0.3, tilt=(0.25, 0.1))
        stone = _faces(bm, 0)
        k0 = len(bm.faces)
        cuboid(bm, (0, 0, h * 0.62), (2.75, 2.75, 1.8))
        runes = _faces(bm, k0)
        return [(c.lib("basalt_block"), stone), (c.lib("basalt_carved"), runes)]

    return _p(c, name, build)


def brazier(c):
    """A squat basalt brazier with a big fire (the flame top at about 3 m)."""
    name = "Basalt Brazier"

    def build(bm):
        cuboid(bm, (0, 0, 0.5), (2.2, 2.2, 1.0))
        lo = ring(bm, (0, 0), 0.9, 1.0, 6)
        hi = ring(bm, (0, 0), 1.5, 1.8, 6)
        loft(bm, [lo, hi], cap_top=False, cap_bottom=True)
        stone = _faces(bm, 0)
        k0 = len(bm.faces)
        for k, (r, hgt, ox, oy) in enumerate(((0.95, 2.2, 0, 0), (0.55, 1.5, 0.45, 0.2), (0.5, 1.3, -0.4, -0.3))):
            res = bmesh.ops.create_cone(bm, cap_ends=False, segments=5, radius1=r, radius2=0.0, depth=hgt)
            for v in res["verts"]:
                v.co += Vector((ox, oy, 1.6 + hgt / 2))
        flame = _faces(bm, k0)
        return [(c.lib("basalt_block"), stone), (c.lib("torch_glow"), flame)]

    return _p(c, name, build)


# ------------------------------------------------------------------ the caverns


def stalactite(c, variant=0):
    """A cluster of stalactites hanging from a cave roof (origin at the top)."""
    name = "Stalactites %d" % variant

    def build(bm):
        rock, glow = [], []
        for k in range(5):
            a = k * 1.3 + variant
            r = 2.2 * rnd(k * 3 + variant)
            x, y = r * math.cos(a), r * math.sin(a)
            ln = 4.0 + 7.0 * rnd(k * 7 + variant)
            f = prism(bm, (x, y, 1.0), (x * 0.9, y * 0.9, -ln * 0.5), 1.3, 0.7, n=5, phase=a, tip=(x * 0.8, y * 0.8, -ln))
            (glow if k == 2 else rock).extend(f)
        return [(c.lib("cave_rock"), rock), (c.lib("magma_rock"), glow)]

    return _p(c, name, build)


def cave_column(c, height=30.0):
    """A massive obsidian column from cave floor to roof, pinched in the middle, veined
    (origin at its foot)."""
    name = "Cave Column %d" % int(height)

    def build(bm):
        obs, vein = [], []
        f = prism(bm, (0, 0, -1), (0.5, 0.3, height * 0.5), 5.5, 2.6, n=6, phase=0.2)
        for i, fi in enumerate(f):
            (vein if i % 3 == 1 else obs).append(fi)
        f = prism(bm, (0.5, 0.3, height * 0.5), (0, 0, height + 3), 2.6, 6.0, n=6, phase=0.5)
        for i, fi in enumerate(f):
            (vein if i % 3 == 2 else obs).append(fi)
        return [(c.lib(OBS), obs), (c.lib(VEIN), vein)]

    return _p(c, name, build)


def crystals(c, mat="crystal_red", variant=0):
    """A cluster of big glowing crystals (about 6 m), growing from the ground or a wall
    (origin at its base, growing toward +Z)."""
    name = "Crystals %s %d" % (mat, variant)

    def build(bm):
        for k in range(7):
            a = k * 0.9 + variant
            tilt = 0.25 + 0.45 * rnd(k * 3 + variant)
            ln = 2.5 + 4.5 * rnd(k * 5 + variant)
            d = Vector((math.sin(tilt) * math.cos(a), math.sin(tilt) * math.sin(a), math.cos(tilt)))
            b = Vector((0.6 * math.cos(a), 0.6 * math.sin(a), -0.3))
            prism(bm, tuple(b), tuple(b + d * ln * 0.75), 0.55 + 0.25 * rnd(k), 0.55, n=6, phase=a, tip=tuple(b + d * ln))
        return [(c.lib(mat), _faces(bm, 0))]

    return _p(c, name, build)


# ------------------------------------------------------------------ the burning forest


def burnt_pine(c, variant=0, burning=False):
    """A tall prehistoric pine: charred, bare, or with its crown still on fire."""
    name = "Pine %s %d" % ("Burning" if burning else "Charred", variant)

    def build(bm):
        h = 14.0 + 4.0 * variant
        tube(bm, [(0, 0, -0.5), (0.3, 0.2, h * 0.5), (0.1, -0.2, h)], [0.65, 0.45, 0.2], n=5)
        for k in range(5):
            z = h * (0.35 + 0.12 * k)
            a = k * 2.2 + variant
            ln = (4.5 - 0.7 * k) * (0.6 if not burning else 1.0)
            tube(bm, [(0, 0, z), (ln * math.cos(a), ln * math.sin(a), z + 1.2 - 0.4 * ln)], [0.18, 0.06], n=3)
        bark = _faces(bm, 0)
        out = [(c.lib("charred_bark"), bark)]
        if burning:
            k0 = len(bm.faces)
            for k in range(3):
                z = h * (0.45 + 0.17 * k)
                r = 3.6 - 0.9 * k
                prism(bm, (0, 0, z), (0, 0, z + 3.2), r, r * 0.4, n=6, phase=k, tip=(0, 0, z + 5.0))
            out.append((c.lib("burning_leaves"), _faces(bm, k0)))
        return out

    return _p(c, name, build)


def burnt_palm(c, variant=0):
    """A scorched palm: a bent trunk and drooping dead fronds."""
    name = "Burnt Palm %d" % variant

    def build(bm):
        h = 9.0 + 2.0 * variant
        pts = [(1.4 * (k / 6) ** 2, 0, h * k / 6) for k in range(7)]
        tube(bm, pts, [0.4 - 0.03 * k for k in range(7)], n=5)
        top = pts[-1]
        for i in range(6):
            a = i * math.tau / 6 + variant
            tube(bm, [top, (top[0] + 2.5 * math.cos(a), 2.5 * math.sin(a), top[2] - 0.5), (top[0] + 3.6 * math.cos(a), 3.6 * math.sin(a), top[2] - 3.2)], [0.15, 0.1, 0.03], n=3)
        return [(c.lib("charred_bark"), _faces(bm, 0))]

    return _p(c, name, build)


def smoke_plume(c, variant=0, height=60.0):
    """A column of dark smoke billowing up and spreading on the wind (see-through,
    soft-shaded; origin at its foot)."""
    name = "Smoke Plume %d %d" % (variant, int(height))

    def build(bm):
        n = 11
        for k in range(n):
            t = k / (n - 1)
            z = height * t
            r = 3.0 + height * 0.16 * t ** 1.2 * (0.8 + 0.4 * rnd(k + variant))
            drift = height * 0.3 * t * t
            res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
            for v in res["verts"]:
                v.co = Vector((drift + 2.5 * math.sin(k * 1.7 + variant) + v.co.x, 2.5 * math.cos(k * 1.3 + variant) + v.co.y, z + v.co.z * 0.75))
        for f in bm.faces:
            f.smooth = True
        return [(c.lib("ash_smoke"), _faces(bm, 0))]

    return _p(c, name, build)


def crag(c, variant=0):
    """A towering crag of black rock and obsidian blades, about 65 m tall (the dragon's
    perch; origin at its foot)."""
    name = "Crag %d" % variant

    def build(bm):
        obs, vein, rock = [], [], []
        for k, (x, y, h, r) in enumerate(((0, 0, 66, 15), (12, 8, 48, 11), (-10, 9, 40, 10), (6, -12, 34, 10), (-14, -8, 28, 9), (18, -6, 22, 8))):
            f = prism(bm, (x, y, -8), (x * 1.05, y * 1.05, h * 0.7), r, r * 0.55, n=6, phase=k * 0.7,
                      tip=(x * 0.9 + 2, y * 0.9 - 1, h))
            for i, fi in enumerate(f):
                (vein if (i + k) % 5 == 0 else rock if k % 2 else obs).append(fi)
        # The ledge it perches on, near the top.
        k0 = len(bm.faces)
        cuboid(bm, (-6, 0, 52), (16, 14, 3), rot=0.3, tilt=(0.05, -0.06))
        rock += _faces(bm, k0)
        return [(c.lib(OBS), obs), (c.lib(VEIN), vein), (c.lib("obsidian_cliff"), rock)]

    return _p(c, name, build)


def far_volcano(c, variant=0):
    """A distant volcano for the horizon: a simple cone (about 200 m tall at scale 1)
    with a glowing crater and lava streaks down its sides (origin at its foot)."""
    name = "Far Volcano %d" % variant

    def build(bm):
        n = 14
        H = 200.0
        R = 340.0
        rings = []
        for k, (f, z) in enumerate(((1.0, -20), (0.72, H * 0.22), (0.44, H * 0.58), (0.2, H * 0.92), (0.14, H))):
            rr = R * f
            rings.append([bm.verts.new((rr * (1 + 0.08 * math.sin(i * 2.3 + variant + k)) * math.cos(i * math.tau / n), rr * (1 + 0.08 * math.cos(i * 1.7 + variant)) * math.sin(i * math.tau / n), z)) for i in range(n)])
        for lo, hi in zip(rings, rings[1:]):
            for i in range(n):
                bm.faces.new((lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i]))
        rock = _faces(bm, 0)
        k0 = len(bm.faces)
        bm.faces.new(rings[-1])
        glow = _faces(bm, k0)
        k1 = len(bm.faces)
        # Lava streaks down the flanks.
        for s in range(4):
            a = s * math.tau / 4 + 0.5 + variant
            pts = []
            for k in range(6):
                t = k / 5
                rr = R * (0.14 + 0.62 * t)
                z = H - H * 0.9 * t ** 1.1 + 2.0
                pts.append((rr * math.cos(a + 0.1 * math.sin(t * 5)), rr * math.sin(a + 0.1 * math.sin(t * 5)), z))
            for p0, p1 in zip(pts, pts[1:]):
                d = Vector(p1) - Vector(p0)
                side = d.cross(Vector((0, 0, 1))).normalized() * (5.0 + 3 * rnd(s))
                bm.faces.new([bm.verts.new(v) for v in (Vector(p0) - side, Vector(p0) + side, Vector(p1) + side * 1.4, Vector(p1) - side * 1.4)])
        streaks = _faces(bm, k1)
        return [(c.lib("obsidian_cliff"), rock), (c.lib("fire_glow"), glow), (c.lib("lava_falls"), streaks)]

    return _p(c, name, build)
