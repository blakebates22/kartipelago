# The overworld regions' own props (Blake's review of Dinosaur Valley, Oct 28): jungle
# giants whose roots grip the ground ("right now they look like fins to rockets"), carved
# totem poles ("more intricate"), the camp's well, kart shed and hearths, obsidian huts
# for Ember's villagers, burning trees, a temple gate with its lintel ON its pillars, lava
# geyser vents and a volcano's cone.
# SPDX-License-Identifier: MIT
#
# Like props.py: each builder makes one mesh (once per build, through Course.proto) that
# every copy shares. All original designs, low-poly in the spirit of late-90s scenery.

import math

from course_kit import Vector, bmesh, rnd
from props import _faces, blob, cuboid, loft, ring, tube


def _p(c, name, build):
    return c.proto(name, build) and name


def _cyl(bm, centre, r, h, n=8, r2=None):
    """An upright cylinder (or frustum) standing on centre (x, y, z)."""
    lo = ring(bm, centre[:2], r, centre[2], n)
    hi = ring(bm, centre[:2], r2 if r2 is not None else r, centre[2] + h, n)
    loft(bm, [lo, hi], cap_top=True, cap_bottom=True)


def _rot(v, a):
    ca, sa = math.cos(a), math.sin(a)
    return Vector((v[0] * ca - v[1] * sa, v[0] * sa + v[1] * ca, v[2]))


# ------------------------------------------------------------------ trees


def great_tree(c, variant=0):
    """A jungle giant (34-42 m) on real roots: buttresses that leave the trunk high up and
    arch down into the ground, then run on along it, splitting, gripping the earth (Blake,
    note 20); plain furrowed bark (no leaves on it); great limbs, a layered crown and vines
    hanging from the limbs."""
    name = "Great Tree %d" % variant

    def build(bm):
        h = 34.0 + 4.0 * variant
        lean = (0.7 * math.sin(variant * 2.1 + 0.4), 0.7 * math.cos(variant * 1.7))
        L = lambda t: (lean[0] * t, lean[1] * t)  # noqa: E731
        tube(bm, [(0, 0, -1.2), (*L(0.08), 3.0), (*L(0.3), h * 0.3), (*L(0.62), h * 0.62), (*L(1.0), h)],
             [2.9, 2.2, 1.65, 1.3, 0.9], n=12)
        # The roots: each leaves the trunk 4-8 m up, arches down to the ground and runs on
        # along it, sinking, with a smaller root splitting off.
        for i in range(9):
            a = i * math.tau / 9 + variant * 0.5 + 0.2 * rnd(i * 3 + variant)
            ca, sa = math.cos(a), math.sin(a)
            up = 4.0 + 4.0 * rnd(i * 2 + variant)
            reach = 6.5 + 4.0 * rnd(i + variant * 3)
            bend = 0.35 * (rnd(i * 5 + variant) - 0.5)

            def at(r, z, b=bend):
                return (r * math.cos(a + b * r / reach), r * math.sin(a + b * r / reach), z)

            path = [at(1.2, up), at(2.6, up * 0.72), at(reach * 0.55, up * 0.3), at(reach * 0.85, 0.35),
                    at(reach * 1.15, -0.1), at(reach * 1.5, -0.7)]
            tube(bm, path, [1.05, 0.95, 0.7, 0.5, 0.36, 0.2], n=6)
            if i % 2 == 0:
                s = path[3]
                d = 1 if rnd(i * 7 + variant) > 0.5 else -1
                tube(bm, [s, (s[0] + 2.2 * math.cos(a + d * 0.8), s[1] + 2.2 * math.sin(a + d * 0.8), 0.0),
                          (s[0] + 4.0 * math.cos(a + d * 0.9), s[1] + 4.0 * math.sin(a + d * 0.9), -0.6)], [0.38, 0.26, 0.14], n=5)
            _ = ca, sa
        limbs = []
        for i in range(5):
            a = i * math.tau / 5 + 0.4 + variant
            reach = 9.0 + 3.0 * rnd(i * 5 + variant)
            z0 = h * (0.66 + 0.06 * (i % 3))
            end = (lean[0] + reach * math.cos(a), lean[1] + reach * math.sin(a), z0 + 4.0 + 2 * rnd(i + 9))
            mid = ((lean[0] + end[0]) * 0.5, (lean[1] + end[1]) * 0.5, z0 + 3.2)
            tube(bm, [(lean[0] * 0.8, lean[1] * 0.8, z0), mid, end], [0.95, 0.62, 0.35], n=6)
            limbs.append(end)
        bark = _faces(bm, 0)
        k0 = len(bm.faces)
        crown = [(lean[0], lean[1], h + 3.0, 8.5)] + [(x, y, z + 1.5, 6.0 + 1.5 * rnd(k + variant)) for k, (x, y, z) in enumerate(limbs)]
        for x, y, z, r in crown:
            blob(bm, (x, y, z), r, sz=0.5, subdiv=2)
        top = _faces(bm, k0)
        k1 = len(bm.faces)
        for x, y, z, r in crown[1:]:
            blob(bm, (x * 0.85, y * 0.85, z - 2.0), r * 0.85, sz=0.35, subdiv=1)
        under = _faces(bm, k1)
        k2 = len(bm.faces)
        for k, (x, y, z) in enumerate(limbs):
            for j in range(3):
                vx = x * (0.55 + 0.15 * j) + (rnd(k * 7 + j) - 0.5) * 2
                vy = y * (0.55 + 0.15 * j) + (rnd(k * 11 + j) - 0.5) * 2
                top_z = z - 1.0 - j * 0.6
                length = 9.0 + 9.0 * rnd(k * 3 + j * 5 + variant)
                tube(bm, [(vx, vy, top_z), (vx + 0.3, vy, top_z - length * 0.5), (vx, vy + 0.2, top_z - length)], [0.16, 0.13, 0.08], n=4)
                for q in range(3):
                    blob(bm, (vx + 0.2, vy, top_z - length * (0.3 + 0.3 * q)), 0.5, sz=1.3, subdiv=0)
        vines = _faces(bm, k2)
        return [(c.lib("giant_bark"), bark), (c.lib("canopy_dark"), top), (c.lib("jungle_leafcover"), under),
                (c.lib("vine_leaf"), vines)]

    return _p(c, name, build)


def burning_tree(c, variant=0):
    """A tree on fire on the volcano's slopes (Blake, note 25): a charred trunk and
    crooked limbs, flames licking up from its forks and the stubs of its branches."""
    name = "Burning Tree %d" % variant

    def build(bm):
        h = 7.0 + 1.5 * variant
        tube(bm, [(0, 0, -0.4), (0.25, 0.1, h * 0.45), (-0.2, 0.15, h * 0.8), (0.1, 0.0, h)], [0.55, 0.42, 0.26, 0.1], n=6)
        tips = []
        for i in range(4):
            a = i * 1.7 + variant
            z0 = h * (0.4 + 0.15 * i)
            r = 1.8 + 0.8 * rnd(i + variant * 2)
            p1 = (r * 0.6 * math.cos(a), r * 0.6 * math.sin(a), z0 + 0.9)
            p2 = (r * math.cos(a + 0.2), r * math.sin(a + 0.2), z0 + 2.0)
            tube(bm, [(0, 0, z0), p1, p2], [0.2, 0.13, 0.05], n=4)
            tips.append(p1)
        tips.append((0.1, 0.0, h - 0.6))
        charred = _faces(bm, 0)
        k0 = len(bm.faces)
        for j, (x, y, z) in enumerate(tips):
            for q in range(2):
                w = (0.55 if q == 0 else 0.35) * (1.2 if j == len(tips) - 1 else 1.0)
                hh = (1.9 if q == 0 else 1.3) * (1.3 if j == len(tips) - 1 else 1.0)
                res = bmesh.ops.create_cone(bm, cap_ends=False, segments=5, radius1=w, radius2=0.0, depth=hh)
                for v in res["verts"]:
                    v.co += Vector((x + 0.08 * q, y, z - 0.2 + hh / 2))
        flames = _faces(bm, k0)
        return [(c.lib("charred_bark"), charred), (c.lib("campfire_flame"), flames)]

    return _p(c, name, build)


# ------------------------------------------------------------------ the camp


def totem_pole(c, variant=0):
    """A tall carved totem (Blake, note 6: "make the totem poles more intricate"): stacked
    carved faces, each with a heavy brow, round eyes, a beak or a snout and bared teeth,
    ears or little wings at the sides, painted bands between, and a great spread-winged
    bird on top."""
    name = "Totem Pole %d" % variant

    def build(bm):
        z = 0.0
        faces = []
        dark = []
        paint = []
        heads = 4 if variant % 2 == 0 else 3
        for k in range(heads):
            w = 0.95 - 0.06 * k
            hh = 1.6 - 0.08 * k
            k0 = len(bm.faces)
            cuboid(bm, (0, 0, z + hh / 2), (w * 2, w * 1.8, hh))
            cuboid(bm, (0, -w * 0.95, z + hh * 0.72), (w * 2.05, 0.45, 0.28))  # brow
            kind = (k + variant) % 3
            if kind == 0:  # a beak
                cuboid(bm, (0, -w * 1.15, z + hh * 0.42), (0.5, 0.9, 0.42), tilt=(0.35, 0))
            elif kind == 1:  # a snout
                cuboid(bm, (0, -w * 1.05, z + hh * 0.38), (1.0, 0.6, 0.55))
            else:  # a long nose
                cuboid(bm, (0, -w * 1.05, z + hh * 0.5), (0.35, 0.55, 0.8), tilt=(-0.25, 0))
            for s in (-1, 1):  # ears / little wings
                cuboid(bm, (s * w * 1.12, -0.1, z + hh * 0.62), (0.35, 0.6, 0.7 if kind else 1.0),
                       tilt=(0, s * 0.25))
            faces += _faces(bm, k0)
            k1 = len(bm.faces)
            for s in (-1, 1):  # eyes
                cuboid(bm, (s * w * 0.45, -w * 0.91, z + hh * 0.56), (0.42, 0.06, 0.34))
            cuboid(bm, (0, -w * 0.91, z + hh * 0.16), (w * 1.1, 0.06, 0.16))  # mouth
            dark += _faces(bm, k1)
            k2 = len(bm.faces)
            for s in (-1, 1):  # pupils' whites and teeth
                cuboid(bm, (s * w * 0.45, -w * 0.94, z + hh * 0.56), (0.18, 0.04, 0.16))
            for t in range(4):
                cuboid(bm, ((t - 1.5) * w * 0.26, -w * 0.94, z + hh * 0.2), (0.12, 0.04, 0.1))
            paint += _faces(bm, k2)
            z += hh
            k3 = len(bm.faces)
            cuboid(bm, (0, 0, z + 0.12), (w * 2.1, w * 1.9, 0.24))  # a painted band
            paint += _faces(bm, k3)
            z += 0.24
        # The bird on top: its body, head and beak, and its wings spread.
        k4 = len(bm.faces)
        cuboid(bm, (0, 0, z + 0.6), (1.3, 1.5, 1.2))
        cuboid(bm, (0, -0.55, z + 1.55), (0.9, 0.9, 0.8))
        cuboid(bm, (0, -1.15, z + 1.45), (0.3, 0.7, 0.3), tilt=(0.4, 0))
        faces += _faces(bm, k4)
        k5 = len(bm.faces)
        for s in (-1, 1):
            for f in range(3):
                cuboid(bm, (s * (1.2 + f * 0.95), 0.1, z + 1.0 + f * 0.35 - (0.25 if f == 2 else 0)), (1.0, 0.22, 0.75 - 0.15 * f),
                       tilt=(0, -s * (0.25 + 0.12 * f)))
        paint += _faces(bm, k5)
        return [(c.lib("palm_bark"), faces), (c.lib("volcano_basalt"), dark), (c.lib("tribal_paint"), paint)]

    return _p(c, name, build)


def well(c):
    """The camp's well: a round stone kerb, dark water down in it, two posts and a beam
    with a winding drum, a rope and bucket, under a little thatched roof."""
    name = "Camp Well"

    def build(bm):
        lo = ring(bm, (0, 0), 1.7, -0.3, 12)
        hi = ring(bm, (0, 0), 1.7, 1.0, 12)
        ilo = ring(bm, (0, 0), 1.25, -0.3, 12)
        ihi = ring(bm, (0, 0), 1.25, 1.0, 12)
        loft(bm, [lo, hi], cap_top=False)
        loft(bm, [ihi, ilo], cap_top=False)
        for i in range(12):
            bm.faces.new((hi[i], hi[(i + 1) % 12], ihi[(i + 1) % 12], ihi[i]))
        for i in range(10):
            a = i * math.tau / 10 + 0.2
            blob(bm, (1.72 * math.cos(a), 1.72 * math.sin(a), 0.55 + 0.25 * (i % 2)), 0.32, sx=1.4, sz=0.8, subdiv=0)
        stone = _faces(bm, 0)
        k0 = len(bm.faces)
        wr = ring(bm, (0, 0), 1.25, 0.2, 12)
        bm.faces.new(wr)
        water = _faces(bm, k0)
        k1 = len(bm.faces)
        for s in (-1, 1):
            cuboid(bm, (s * 1.55, 0, 1.6), (0.26, 0.26, 3.2))
        cuboid(bm, (0, 0, 2.7), (3.4, 0.2, 0.2))
        _cyl(bm, (0, 0, 2.45), 0.32, 0.1, n=6)
        tube(bm, [(0, 0, 2.5), (0, 0, 1.4)], 0.03, n=4)
        _cyl(bm, (0, 0, 1.05), 0.28, 0.42, n=8, r2=0.33)
        wood = _faces(bm, k1)
        k2 = len(bm.faces)
        for s in (-1, 1):
            v = [bm.verts.new(q) for q in ((-2.0, s * 0.05, 3.0), (2.0, s * 0.05, 3.0), (2.0, s * 1.6, 2.35), (-2.0, s * 1.6, 2.35))]
            bm.faces.new(v if s > 0 else list(reversed(v)))
        roof = _faces(bm, k2)
        return [(c.lib("ruin_stone"), stone), (c.lib("valley_river"), water), (c.lib("palm_bark"), wood),
                (c.lib("thatch"), roof)]

    return _p(c, name, build)


def kart_shed(c):
    """Where the camp works on its karts (Blake, note 1): an open-fronted timber shed under
    a thatched gable, a kart up on blocks inside with a wheel off, a workbench with tools,
    stacked tyres, barrels. Its open side faces -Y."""
    name = "Kart Shed"

    def build(bm):
        W, D, H = 9.0, 6.0, 3.4
        for sx in (-1, 1):
            for sy in (-1, 1):
                cuboid(bm, (sx * W / 2, sy * D / 2, H / 2 - 0.3), (0.35, 0.35, H + 0.6))
        cuboid(bm, (0, D / 2, H / 2 - 0.3), (W, 0.18, H))  # back wall
        for sx in (-1, 1):
            cuboid(bm, (sx * W / 2, D / 4, H / 2 - 0.3), (0.18, D / 2, H))  # half side walls
        cuboid(bm, (0, -D / 2, H - 0.1), (W + 0.4, 0.3, 0.3))  # the front beam
        cuboid(bm, (W * 0.25, D / 2 - 0.7, 0.95), (3.2, 1.0, 0.12))  # workbench top
        for sx in (-1, 1):
            cuboid(bm, (W * 0.25 + sx * 1.4, D / 2 - 0.7, 0.45), (0.15, 0.8, 0.9))
        for k in range(3):  # tools hung on the back wall
            cuboid(bm, (W * 0.12 + k * 0.6, D / 2 - 0.15, 2.0), (0.08, 0.06, 0.9 - 0.15 * k))
        wood = _faces(bm, 0)
        k0 = len(bm.faces)
        for s in (-1, 1):
            v = [bm.verts.new(q) for q in ((-W / 2 - 0.8, 0.0, H + 2.2), (W / 2 + 0.8, 0.0, H + 2.2),
                                           (W / 2 + 0.8, s * (D / 2 + 1.2), H - 0.4), (-W / 2 - 0.8, s * (D / 2 + 1.2), H - 0.4))]
            bm.faces.new(v if s < 0 else list(reversed(v)))
        for s in (-1, 1):  # gable ends
            v = [bm.verts.new(q) for q in ((s * W / 2, -D / 2, H - 0.2), (s * W / 2, D / 2, H - 0.2), (s * W / 2, 0.0, H + 2.1))]
            bm.faces.new(v)
        roof = _faces(bm, k0)
        k1 = len(bm.faces)
        # The kart: a chassis on blocks, a seat, a steering column, three wheels and one off.
        cuboid(bm, (-1.6, 0.2, 0.75), (1.6, 2.6, 0.3))
        cuboid(bm, (-1.6, 0.6, 1.15), (0.9, 0.8, 0.6))
        cuboid(bm, (-1.6, -0.75, 1.0), (1.4, 0.7, 0.35))
        kart = _faces(bm, k1)
        k2 = len(bm.faces)
        tube(bm, [(-1.6, -0.6, 1.0), (-1.6, -0.3, 1.7)], 0.05, n=4)
        for x, y in ((-2.55, 1.2), (-0.65, 1.2), (-2.55, -0.9)):
            res = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.42, radius2=0.42, depth=0.32)
            for v in res["verts"]:
                v.co = Vector((x + v.co.z, y + v.co.x, 0.55 + v.co.y))
        for k in range(4):  # a stack of tyres, and the one off the kart
            _cyl(bm, (W / 2 - 1.1, -D / 2 + 1.3, -0.1 + 0.34 * k), 0.5, 0.32, n=10)
        _cyl(bm, (-0.3, -1.8, -0.1), 0.42, 0.3, n=10)
        for k in range(4):  # blocks under the kart
            cuboid(bm, (-1.6 + (k % 2 - 0.5) * 1.2, 0.2 + (k // 2 - 0.5) * 1.8, 0.3), (0.5, 0.5, 0.6))
        rubber = _faces(bm, k2)
        k3 = len(bm.faces)
        for k in range(2):  # barrels
            _cyl(bm, (-W / 2 + 0.9 + k * 1.0, D / 2 - 0.9, -0.1), 0.45, 1.1, n=8, r2=0.42)
        barrels = _faces(bm, k3)
        return [(c.lib("wood_planks"), wood), (c.lib("thatch"), roof), (c.lib("tribal_paint"), kart),
                (c.lib("black_rock"), rubber), (c.lib("palm_bark"), barrels)]

    return _p(c, name, build)


def hearth(c):
    """A fireplace for the camp (Blake, note 1): a hearth of stones round a bed of coals,
    logs crossed in it, and log benches round it."""
    name = "Hearth"

    def build(bm):
        for i in range(12):
            a = i * math.tau / 12
            blob(bm, (1.45 * math.cos(a), 1.45 * math.sin(a), 0.18), 0.36, sx=1.3, sz=0.85, subdiv=1)
        stone = _faces(bm, 0)
        k0 = len(bm.faces)
        for i in range(5):
            a = i * math.tau / 5 + 0.3
            ca, sa = math.cos(a), math.sin(a)
            tube(bm, [(1.1 * ca, 1.1 * sa, 0.12), (0.1 * ca, 0.1 * sa, 1.2)], 0.12, n=6)
        for i in range(3):
            a = i * math.tau / 3 + 0.5
            ca, sa = math.cos(a), math.sin(a)
            res = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.32, radius2=0.3, depth=2.6)
            for v in res["verts"]:
                p = Vector((v.co.z, v.co.x, v.co.y + 0.3))
                v.co = Vector((3.2 * ca, 3.2 * sa, 0.0)) + _rot(p, a + math.pi / 2)
        logs = _faces(bm, k0)
        k1 = len(bm.faces)
        for i, (r, w, hh) in enumerate(((0.0, 0.5, 1.9), (0.32, 0.34, 1.35), (0.34, 0.32, 1.2), (0.3, 0.3, 1.45))):
            a = i * 2.4
            res = bmesh.ops.create_cone(bm, cap_ends=False, segments=6, radius1=w, radius2=0.0, depth=hh)
            for v in res["verts"]:
                v.co += Vector((r * math.cos(a), r * math.sin(a), 0.2 + hh / 2))
        flames = _faces(bm, k1)
        return [(c.lib("ruin_stone"), stone), (c.lib("palm_bark"), logs), (c.lib("campfire_flame"), flames)]

    return _p(c, name, build)


# ------------------------------------------------------------------ Ember


def obsidian_hut(c, variant=0):
    """An Ember villager's home (Blake, note 30: "a lava rock hut or 2, black rock obsidian
    looking"): a beehive of stacked black rock courses, a glowing doorway, a lit window
    and a smoke hole (its door faces -Y)."""
    name = "Obsidian Hut %d" % variant

    def build(bm):
        r0 = 3.4 + 0.4 * variant
        rows = 6
        z = -0.4
        rings = []
        for k in range(rows + 1):
            t = k / rows
            r = r0 * math.cos(t * 1.35) + 0.15 * (k % 2)
            rings.append(ring(bm, (0, 0), max(0.5, r), z, 12, phase=0.13 * k))
            z += 0.95 - 0.08 * k
        loft(bm, rings, cap_top=False)
        # Courses of rough blocks round its belly, and the smoke hole's lip.
        for k in range(2):
            for i in range(12):
                a = i * math.tau / 12 + 0.26 * k
                blob(bm, ((r0 + 0.1) * math.cos(a), (r0 + 0.1) * math.sin(a), 0.4 + 1.1 * k), 0.55, sx=1.4, sz=0.7, subdiv=0)
        rock = _faces(bm, 0)
        k0 = len(bm.faces)
        d = [bm.verts.new(q) for q in ((-0.7, -r0 * 0.99 - 0.05, -0.2), (0.7, -r0 * 0.99 - 0.05, -0.2), (0.6, -r0 * 0.94 - 0.05, 1.9),
                                       (-0.6, -r0 * 0.94 - 0.05, 1.9))]
        bm.faces.new(d)
        for s in (-1, 1):
            a = -math.pi / 2 + s * 1.1
            p = Vector((r0 * 0.93 * math.cos(a), r0 * 0.93 * math.sin(a), 2.2))
            n = Vector((math.cos(a), math.sin(a), 0)) * 0.08
            side = Vector((-math.sin(a), math.cos(a), 0)) * 0.4
            v = [bm.verts.new(p + n - side + Vector((0, 0, -0.35))), bm.verts.new(p + n + side + Vector((0, 0, -0.35))),
                 bm.verts.new(p + n + side + Vector((0, 0, 0.35))), bm.verts.new(p + n - side + Vector((0, 0, 0.35)))]
            bm.faces.new(v)
        glow = _faces(bm, k0)
        k1 = len(bm.faces)
        cuboid(bm, (0, -r0 - 0.6, 2.25), (2.0, 1.4, 0.25))  # a lintel slab over the door
        for s in (-1, 1):
            cuboid(bm, (s * 0.95, -r0 - 0.5, 1.0), (0.45, 0.7, 2.4))
        slabs = _faces(bm, k1)
        return [(c.lib("obsidian_cliff"), rock), (c.lib("ember_glow"), glow), (c.lib("basalt_block"), slabs)]

    return _p(c, name, build)


def lava_vent(c, variant=0):
    """A lava geyser's vent (Blake, note 27: Snowy Summit's geysers, recoloured): a squat
    cone of black rock round a glowing throat, crusted lava down its sides."""
    name = "Lava Vent %d" % variant

    def build(bm):
        r = 4.6 + 0.6 * variant
        rings = [ring(bm, (0, 0), r, -0.8, 14), ring(bm, (0, 0), r * 0.82, 0.5, 14, phase=0.1),
                 ring(bm, (0, 0), r * 0.55, 1.5, 14, phase=0.2), ring(bm, (0, 0), r * 0.42, 1.8, 14)]
        loft(bm, rings, cap_top=False)
        for i in range(7):
            a = i * math.tau / 7 + variant
            blob(bm, (r * 0.78 * math.cos(a), r * 0.78 * math.sin(a), 0.7), 0.9, sx=1.3, sz=0.6, subdiv=0)
        rock = _faces(bm, 0)
        k0 = len(bm.faces)
        inner = ring(bm, (0, 0), r * 0.42, 1.8, 14)
        low = ring(bm, (0, 0), r * 0.3, 0.9, 14)
        loft(bm, [inner, low], cap_top=True)
        throat = _faces(bm, k0)
        k1 = len(bm.faces)
        for i in range(4):  # crusted runs of lava down its sides
            a = i * math.tau / 4 + 0.6 + variant
            p0 = Vector((r * 0.45 * math.cos(a), r * 0.45 * math.sin(a), 1.85))
            p1 = Vector((r * 0.95 * math.cos(a + 0.1), r * 0.95 * math.sin(a + 0.1), -0.2))
            side = Vector((-math.sin(a), math.cos(a), 0)) * 0.45
            v = [bm.verts.new(p0 - side), bm.verts.new(p0 + side), bm.verts.new(p1 + side * 1.6), bm.verts.new(p1 - side * 1.6)]
            bm.faces.new(v)
        runs = _faces(bm, k1)
        return [(c.lib("obsidian_cliff"), rock), (c.lib("volcano_lava"), throat), (c.lib("lava_crust"), runs)]

    return _p(c, name, build)


# ------------------------------------------------------------------ the swamp, the tunnels


def wall_sconce(c):
    """A torch in an iron cage on a bracket, for a tunnel's wall (origin at the wall,
    pointing out along -Y)."""
    name = "Wall Sconce"

    def build(bm):
        cuboid(bm, (0, -0.1, 0), (0.4, 0.2, 0.8))
        tube(bm, [(0, -0.15, -0.25), (0, -0.55, 0.0), (0, -0.7, 0.45)], 0.07, n=5)
        for k in range(4):
            a = k * math.tau / 4
            tube(bm, [(0.25 * math.cos(a), -0.7 + 0.25 * math.sin(a), 0.45), (0.3 * math.cos(a), -0.7 + 0.3 * math.sin(a), 1.0)], 0.03, n=3)
        iron = _faces(bm, 0)
        k0 = len(bm.faces)
        for q, (r, hh) in enumerate(((0.26, 0.95), (0.16, 0.7))):
            res = bmesh.ops.create_cone(bm, cap_ends=False, segments=5, radius1=r, radius2=0.0, depth=hh)
            for v in res["verts"]:
                v.co += Vector((0.03 * q, -0.7, 0.6 + hh / 2))
        flame = _faces(bm, k0)
        return [(c.lib("black_rock"), iron), (c.lib("torch_glow"), flame)]

    return _p(c, name, build)


def root_curtain(c, variant=0, length=6.0):
    """Roots and moss hanging from a tunnel's roof (origin at the top)."""
    name = "Root Curtain %d" % variant

    def build(bm):
        for k in range(6):
            x = (k - 2.5) * 0.7 + 0.3 * (rnd(k + variant) - 0.5)
            ln = length * (0.4 + 0.6 * rnd(k * 3 + variant))
            tube(bm, [(x, 0, 0), (x + 0.2, 0.1, -ln * 0.5), (x - 0.1, 0.0, -ln)], [0.12, 0.08, 0.03], n=4)
        return [(c.lib("bog_root"), _faces(bm, 0))]

    return _p(c, name, build)


def lava_channel_lip(c, length=4.0):
    """A kerb of basalt blocks along a lava channel (along X)."""
    name = "Lava Lip %.1f" % length

    def build(bm):
        n = max(2, int(length / 1.1))
        for k in range(n):
            x = -length / 2 + (k + 0.5) * length / n
            cuboid(bm, (x, 0, 0.2), (length / n * 0.92, 0.7, 0.55 + 0.15 * (k % 2)), rot=0.08 * (rnd(k) - 0.5))
        return [(c.lib("basalt_block"), _faces(bm, 0))]

    return _p(c, name, build)
