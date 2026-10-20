# The winter-ruin kit for Frostveil Peaks: snow-capped masonry, braziers, banners,
# carved pillars, towers, arches, giant carved heads, the stepped temple, the sun disk,
# statues, snowy palms and conifers, icicles, frozen falls and snow drifts.
# SPDX-License-Identifier: MIT
#
# Same rules as props.py: each prop is one mesh built once (Course.proto) and placed as
# copies, chunky and low-poly, all original designs. Big one-off pieces (walls along a
# path, the serpent gate) are built in place with Blocks.

import math

from course_kit import Vector, bmesh, rnd
from props import _faces, blob, cuboid, frond, loft, ring, tube

SNOW = "snow_ground"
STONE = "citadel_stone"
CARVED = "citadel_carved"
DARK = "citadel_dark"
GLOW = "window_glow"
FLAME = "torch_glow"


class Blocks:
    """A mesh made of boxes (and other shapes) grouped by material, with snow lying on
    top of every box that wants it."""

    def __init__(self, bm=None):
        self.bm = bm or bmesh.new()
        self.groups = {}

    def add(self, mat, make):
        k0 = len(self.bm.faces)
        make(self.bm)
        self.groups.setdefault(mat, []).extend(_faces(self.bm, k0))

    def box(self, mat, centre, size, rot=0.0, snow=True, tilt=(0.0, 0.0)):
        self.add(mat, lambda bm: cuboid(bm, centre, size, rot, tilt))
        if snow and abs(tilt[0]) + abs(tilt[1]) < 0.2:
            cx, cy, cz = centre
            w, d, h = size
            # A snow cap, a little wider than the top, sagging over the edges.
            self.add(SNOW, lambda bm: cuboid(bm, (cx, cy, cz + h / 2 + 0.12), (w + 0.18, d + 0.18, 0.28), rot))

    def slots(self, c):
        return [(c.lib(m), f) for m, f in self.groups.items() if f]

    def build(self, c, name, coll="Citadel", role="both"):
        ob = c.mesh_object(name, self.bm, coll, role)
        for mat, faces in self.groups.items():
            if faces:
                c.assign(ob, c.lib(mat), faces)
        ob.data.shade_flat()
        return ob


def _proto(c, name, make):
    """A prop built from Blocks."""

    def build(bm):
        k = Blocks(bm)
        make(k)
        return k.slots(c)

    return c.proto(name, build) and name


def _flame(k, x, y, z, size=1.0):
    def make(bm):
        for i, (r, h, dx) in enumerate(((0.42, 1.5, 0.0), (0.28, 1.1, 0.18), (0.26, 0.95, -0.2))):
            res = bmesh.ops.create_cone(bm, cap_ends=False, segments=5, radius1=r * size, radius2=0.0, depth=h * size)
            for v in res["verts"]:
                v.co += Vector((x + dx * size, y + (i - 1) * 0.1 * size, z + h * size / 2))

    k.add(FLAME, make)


# ------------------------------------------------------------------ fire and cloth


def brazier(c, variant=0):
    """A carved stone brazier: a pedestal, a wide bowl and a big flame. Variant 1 stands
    on a tall pillar (for gateways and parapets). Flame tip at about 3.4 m (6.4 m)."""
    name = "Brazier %d" % variant

    def make(k):
        base = 3.0 * variant
        if variant:
            k.box(CARVED, (0, 0, 1.5), (1.4, 1.4, 3.0), snow=False)
        k.box(STONE, (0, 0, base + 0.15), (1.7, 1.7, 0.3), snow=False)
        k.box(CARVED, (0, 0, base + 0.95), (1.2, 1.2, 1.3), snow=False)

        def bowl(bm):
            res = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.55, radius2=1.05, depth=0.6)
            for v in res["verts"]:
                v.co.z += base + 1.9

        k.add(DARK, bowl)
        _flame(k, 0, 0, base + 2.1, 1.0)

    return _proto(c, name, make)


def banner_pole(c, variant=0):
    """Two poles and a crossbar with a long banner hanging from it (red, teal or blue)."""
    name = "Banner Pole %d" % variant
    cloth = ("banner_red", "banner_teal", "banner_blue")[variant % 3]

    def make(k):
        for x in (-1.0, 1.0):
            k.add("palm_bark", lambda bm, x=x: tube(bm, [(x, 0, -0.4), (x, 0, 7.2)], 0.09, n=5))
        k.add("palm_bark", lambda bm: tube(bm, [(-1.3, 0, 6.9), (1.3, 0, 6.9)], 0.08, n=5))

        def flag(bm):
            for side, dy in ((1, 0.03), (-1, -0.03)):
                pts = [(-0.85, dy, 6.8), (0.85, dy, 6.8), (0.85, dy, 2.6), (0.0, dy, 3.2), (-0.85, dy, 2.6)]
                vs = [bm.verts.new(p) for p in pts]
                bm.faces.new(vs if side > 0 else list(reversed(vs)))

        k.add(cloth, flag)

    return _proto(c, name, make)


def hanging_banner(c, variant=0, length=6.0):
    """A banner hung flat against a wall or a parapet (origin at its top centre, facing -Y)."""
    name = "Hanging Banner %d %d" % (variant, int(length))
    cloth = ("banner_red", "banner_teal", "banner_blue")[variant % 3]

    def make(k):
        k.add("palm_bark", lambda bm: tube(bm, [(-1.2, -0.15, 0.0), (1.2, -0.15, 0.0)], 0.07, n=4))

        def flag(bm):
            pts = [(-1.0, -0.2, -0.1), (1.0, -0.2, -0.1), (1.0, -0.2, -length), (0.0, -0.2, -length + 0.8), (-1.0, -0.2, -length)]
            vs = [bm.verts.new(p) for p in pts]
            bm.faces.new(list(reversed(vs)))

        k.add(cloth, flag)

    return _proto(c, name, make)


# ------------------------------------------------------------------ masonry


def carved_pillar(c, variant=0, height=6.0):
    """A carved stone pillar, snow on its capital; variant 2 is broken off and tilted."""
    name = "Carved Pillar %d %d" % (variant, int(height))

    def make(k):
        k.box(STONE, (0, 0, 0.3), (2.2, 2.2, 0.6))
        h = height * (0.55 if variant == 2 else 1.0)
        n = max(2, int(h / 1.4))
        for i in range(n):
            z = 0.6 + h * (i + 0.5) / n
            k.box(CARVED if (i + variant) % 2 else STONE, (0, 0, z), (1.6, 1.6, h / n - 0.06), snow=False)
        if variant == 2:
            k.box(STONE, (0.3, 0.2, 0.6 + h + 0.5), (1.5, 1.5, 0.9), tilt=(0.25, -0.2))
            k.box(STONE, (1.8, -0.4, 0.4), (1.3, 1.1, 0.8), rot=0.6)
        else:
            k.box(STONE, (0, 0, 0.6 + h + 0.35), (2.2, 2.2, 0.7))

    return _proto(c, name, make)


def guard_block(c, variant=0):
    """A chunky guardrail block with a snow cap (lining the roads)."""
    name = "Guard Block %d" % variant

    def make(k):
        k.box(CARVED if variant % 2 else STONE, (0, 0, 0.55), (1.9, 1.3, 1.1))

    return _proto(c, name, make)


def rubble(c, variant=0):
    """Tumbled carved blocks with snow on them."""
    name = "Rubble %d" % variant

    def make(k):
        for i in range(4 + variant % 2):
            a = i * 2.1 + variant
            r = 1.2 * (i > 0)
            s = 1.6 - 0.2 * i
            k.box(CARVED if i % 2 else STONE, (r * math.cos(a), r * math.sin(a), s / 2 - 0.1), (s, s * 0.9, s * 0.8), rot=a, tilt=((rnd(i + variant) - 0.5) * 0.4, 0))

    return _proto(c, name, make)


def tower(c, variant=0, height=18.0):
    """A square watchtower: a battered base, a shaft with glowing window slits, a
    crenellated top and a pointed cap."""
    name = "Tower %d %d" % (variant, int(height))

    def make(k):
        w = 7.0
        k.box(STONE, (0, 0, 1.5), (w + 2.0, w + 2.0, 3.0))
        k.box(STONE, (0, 0, 3.0 + (height - 5) / 2), (w, w, height - 5), snow=False)
        k.box(CARVED, (0, 0, height - 1.2), (w + 0.8, w + 0.8, 1.6), snow=False)
        for i in range(4):
            a = i * math.pi / 2
            for j in (-1, 1):
                ox = math.cos(a) * (w / 2 + 0.2) + math.sin(a) * j * 2.2
                oy = math.sin(a) * (w / 2 + 0.2) - math.cos(a) * j * 2.2
                k.box(STONE, (ox, oy, height + 0.4), (1.2, 1.2, 1.2))
            # Window slits, two storeys.
            for z in (height * 0.45, height * 0.72):
                wx, wy = math.cos(a) * (w / 2 + 0.03), math.sin(a) * (w / 2 + 0.03)
                k.box(GLOW, (wx, wy, z), (0.12 + 1.0 * abs(math.sin(a)), 0.12 + 1.0 * abs(math.cos(a)), 2.0), snow=False)
        if variant % 2 == 0:

            def cap(bm):
                res = bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=w * 0.62, radius2=0.0, depth=6.0)
                for v in res["verts"]:
                    v.co = Vector((v.co.x * 0.707 - v.co.y * 0.707, v.co.x * 0.707 + v.co.y * 0.707, v.co.z + height + 3.6))

            k.add(SNOW, cap)
        else:
            k.box(DARK, (0, 0, height + 0.1), (w - 0.6, w - 0.6, 0.2), snow=False)

    return _proto(c, name, make)


def ruin_house(c, variant=0):
    """A small stone house of the lower town: thick walls, a glowing doorway, a flat
    snowy roof (variant 1 has lost half its roof)."""
    name = "Ruin House %d" % variant

    def make(k):
        w, d, h = 9.0, 7.0, 5.0
        k.box(STONE, (0, d / 2 - 0.5, h / 2), (w, 1.0, h), snow=variant != 1)
        k.box(STONE, (-w / 2 + 0.5, 0, h / 2), (1.0, d, h))
        k.box(STONE, (w / 2 - 0.5, 0, h / 2 - (1.2 if variant == 1 else 0)), (1.0, d, h - (2.4 if variant == 1 else 0)))
        for x in (-2.6, 2.6):
            k.box(STONE, (x, -d / 2 + 0.5, h / 2), (3.8, 1.0, h))
        k.box(CARVED, (0, -d / 2 + 0.5, h - 0.6), (1.4, 1.0, 1.2), snow=False)
        k.box(GLOW, (0, -d / 2 + 0.55, 1.6), (1.4, 0.9, 3.2), snow=False)
        if variant != 1:
            k.box(STONE, (0, 0, h + 0.3), (w + 0.6, d + 0.6, 0.6))
        else:
            k.box(STONE, (-2.0, 0, h + 0.3), (w * 0.5, d + 0.6, 0.6))
        k.box(STONE, (w / 2 + 1.4, -d / 2 + 1.0, 0.5), (1.6, 1.4, 1.0), rot=0.4)

    return _proto(c, name, make)


def arch(c, span=20.0, height=12.0, variant=0):
    """A monumental arch over a road: two stepped piers, a carved lintel, a stepped crest.
    The opening is `span` wide and `height` tall (origin at the middle of the road)."""
    name = "Arch %d %d %d" % (variant, int(span), int(height))

    def make(k):
        for side in (-1, 1):
            x = side * (span / 2 + 2.0)
            k.box(STONE, (x, 0, 1.0), (5.0, 5.0, 2.0))
            k.box(CARVED if variant % 2 else STONE, (x, 0, 2.0 + (height - 2) / 2), (4.0, 4.0, height - 2), snow=False)
            k.box(STONE, (x, 0, height + 0.5), (4.6, 4.6, 1.0), snow=False)
        k.box(CARVED, (0, 0, height + 1.6), (span + 9.0, 4.4, 2.4))
        for i, wdt in enumerate((span * 0.7, span * 0.42, span * 0.18)):
            k.box(STONE, (0, 0, height + 3.3 + i * 1.3), (wdt, 3.2, 1.3))
        # Icicles under the lintel.
        def ice(bm):
            for i in range(9):
                x = (i - 4) * span / 9 + 0.5 * math.sin(i * 2.3)
                ln = 0.8 + 1.4 * rnd(i + variant)
                res = bmesh.ops.create_cone(bm, cap_ends=False, segments=4, radius1=0.0, radius2=0.22, depth=ln)
                for v in res["verts"]:
                    v.co += Vector((x, -1.8 + 0.4 * (i % 2), height + 0.4 - ln / 2))

        k.add("ice", ice)

    return _proto(c, name, make)


# ------------------------------------------------------------------ giant carvings


def dino_head(c, variant=0):
    """A giant carved dinosaur head, blocky and weathered, snout along +X: a skull with
    heavy brows, glowing eyes in deep sockets, nostrils, a jaw lined with teeth. About
    14 m long and 9 m tall (origin at the back of the neck, on the ground)."""
    name = "Dino Head %d" % variant

    def make(k):
        k.box(STONE, (-1.0, 0, 3.0), (5.0, 6.0, 6.0))  # neck block
        k.box(STONE, (3.0, 0, 6.0), (7.0, 7.2, 5.6))  # skull
        k.box(CARVED, (8.0, 0, 5.3), (6.0, 5.4, 3.2), snow=False)  # upper snout
        k.box(STONE, (8.4, 0, 7.2), (5.0, 4.4, 1.0))  # snout ridge
        k.box(STONE, (6.2, 0, 2.2), (9.0, 5.0, 1.8))  # lower jaw
        for side in (-1, 1):
            k.box(STONE, (4.4, side * 2.7, 9.2), (3.2, 1.8, 1.2))  # brow
            k.box(DARK, (4.6, side * 3.62, 7.4), (2.0, 0.2, 1.6), snow=False)  # socket
            k.box(GLOW, (4.7, side * 3.7, 7.4), (1.0, 0.12, 0.8), snow=False)  # eye
            k.box(DARK, (10.6, side * 1.4, 6.6), (0.8, 0.8, 0.5), snow=False)  # nostril
            if variant == 1:
                # A horn over each brow.
                def horn(bm, side=side):
                    tube(bm, [(4.0, side * 2.8, 9.6), (4.6, side * 3.4, 11.4), (6.2, side * 3.6, 12.6)], [0.7, 0.5, 0.05], n=5)

                k.add(STONE, horn)
        # Teeth along both jaws (pale stone).
        def teeth(bm):
            for i in range(7):
                x = 5.2 + i * 1.05
                for side in (-1, 1):
                    for z0, up in ((3.1, 1), (4.0, -1)):
                        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.32, radius2=0.0, depth=1.0)
                        for v in res["verts"]:
                            v.co = Vector((v.co.x + x, v.co.y + side * 2.3, z0 + up * (v.co.z + 0.5)))

        k.add("bone", teeth)

    return _proto(c, name, make)


def statue(c, variant=0):
    """A snow-covered statue of a dinosaur guardian on a plinth (about 9 m tall)."""
    name = "Statue %d" % variant

    def make(k):
        k.box(CARVED, (0, 0, 1.2), (5.0, 5.0, 2.4))
        k.box(STONE, (0, 0, 2.7), (5.6, 5.6, 0.6))
        # Sitting upright: haunches, body, arms, head, tail curled round the front.
        k.box(STONE, (0, -0.6, 4.4), (3.2, 3.6, 2.8))
        k.box(STONE, (0, 0.2, 6.6), (2.6, 2.8, 3.4), tilt=(-0.15, 0))
        k.box(STONE, (0, 0.4, 9.0), (2.4, 3.6, 2.0))
        k.box(STONE, (0, 2.0, 8.6), (1.8, 2.0, 1.2))
        for side in (-1, 1):
            k.box(STONE, (side * 1.3, 1.2, 6.4), (0.6, 1.8, 0.6), snow=False)
            k.box(GLOW if variant else DARK, (side * 0.85, 1.6, 9.3), (0.3, 0.3, 0.3), snow=False)
        k.box(STONE, (1.6, -2.4, 3.4), (1.2, 3.0, 1.0), rot=0.5)
        if variant == 1:
            k.box(CARVED, (0, -0.2, 10.4), (1.0, 3.0, 1.2))  # a crest

    return _proto(c, name, make)


def sun_disk(c):
    """The ceremonial sun disk: a great golden emblem in a carved stone ring, standing on
    a stepped plinth (about 22 m tall, facing along -Y and +Y)."""
    name = "Sun Disk"

    def make(k):
        for i, (w, h) in enumerate(((16.0, 1.6), (12.0, 1.6), (8.0, 1.6))):
            k.box(STONE, (0, 0, h * i + h / 2), (w, w * 0.7, h))
        r = 8.0
        zc = 4.8 + r + 0.4

        def ring_(bm):
            n = 20
            outer = [(math.cos(i * math.tau / n) * r, math.sin(i * math.tau / n) * r) for i in range(n)]
            inner = [(x * 0.78, z * 0.78) for x, z in outer]
            for y in (-1.0, 1.0):
                for i in range(n):
                    a, b = outer[i], outer[(i + 1) % n]
                    ia, ib = inner[i], inner[(i + 1) % n]
                    vs = [bm.verts.new((p[0], y, zc + p[1])) for p in (a, b, ib, ia)]
                    bm.faces.new(vs if y < 0 else list(reversed(vs)))
            for i in range(n):
                a, b = outer[i], outer[(i + 1) % n]
                vs = [bm.verts.new((a[0], -1, zc + a[1])), bm.verts.new((b[0], -1, zc + b[1])), bm.verts.new((b[0], 1, zc + b[1])), bm.verts.new((a[0], 1, zc + a[1]))]
                bm.faces.new(list(reversed(vs)))

        k.add(CARVED, ring_)

        def face(bm):
            n = 20
            for y in (-0.6, 0.6):
                vs = [bm.verts.new((math.cos(i * math.tau / n) * r * 0.79, y, zc + math.sin(i * math.tau / n) * r * 0.79)) for i in range(n)]
                bm.faces.new(vs if y > 0 else list(reversed(vs)))

        k.add("temple_gold", face)

    return _proto(c, name, make)


# ------------------------------------------------------------------ the temple


def temple(c):
    """The Moonlit Temple: a great stepped pyramid (six tiers, 64 m square, 52 m tall)
    with a grand staircase up its south face, a shrine on top with a firelit doorway and
    the golden sun emblem over it, and carved bands round every tier."""
    name = "Temple"

    def make(k):
        size = 64.0
        z = 0.0
        tiers = 6
        for i in range(tiers):
            s = size - i * 8.5
            h = 6.2
            k.box(STONE, (0, 0, z + h / 2), (s, s, h))
            k.box(CARVED, (0, 0, z + h - 0.9), (s + 0.3, s + 0.3, 1.4), snow=False)
            z += h
        # The grand staircase, up the south (-Y) face, with carved balustrades.
        steps = 30
        for j in range(steps):
            t = j / steps
            y = -size / 2 - 1.0 + t * (size / 2 - (size - 5 * 8.5) / 2)
            k.box(STONE, (0, y, (z * t) / 2 + 0.25), (10.0, 2.6, z * t + 0.5), snow=j % 3 == 0)
        for side in (-1, 1):
            for j in range(6):
                t0, t1 = j / 6, (j + 1) / 6
                y0 = -size / 2 - 1.0 + t0 * (size / 2 - (size - 5 * 8.5) / 2)
                y1 = -size / 2 - 1.0 + t1 * (size / 2 - (size - 5 * 8.5) / 2)
                k.box(CARVED, (side * 5.8, (y0 + y1) / 2, z * (t0 + t1) / 2 + 0.6), (1.6, abs(y1 - y0) + 0.2, 1.6))
        # The shrine on top.
        k.box(STONE, (0, 0, z + 5.5), (16.0, 14.0, 11.0))
        k.box(CARVED, (0, 0, z + 11.6), (18.0, 16.0, 1.4))
        k.box(STONE, (0, 0, z + 13.4), (11.0, 9.0, 2.4))
        k.box(GLOW, (0, -7.05, z + 3.8), (5.0, 0.2, 7.6), snow=False)
        k.box(DARK, (0, -7.0, z + 8.4), (6.6, 0.2, 1.4), snow=False)
        k.box("temple_gold", (0, -7.2, z + 9.0 + 2.1), (5.6, 0.4, 3.4), snow=False)
        # A crowning spire with the sun on every face, lit from inside.
        k.box(STONE, (0, 0, z + 17.6), (7.0, 7.0, 6.0), snow=False)
        for a in range(4):
            ang = a * math.pi / 2
            k.box("temple_gold", (math.cos(ang) * 3.55, math.sin(ang) * 3.55, z + 17.8), (0.2 + 3.6 * abs(math.sin(ang)), 0.2 + 3.6 * abs(math.cos(ang)), 3.6), snow=False)

        def spire(bm):
            res = bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=5.4, radius2=0.0, depth=12.0)
            for v in res["verts"]:
                v.co = Vector((v.co.x * 0.707 - v.co.y * 0.707, v.co.x * 0.707 + v.co.y * 0.707, v.co.z + z + 26.6))

        k.add(STONE, spire)

    return _proto(c, name, make)


# ------------------------------------------------------------------ nature


def snowy_palm(c, variant=0):
    """A prehistoric palm under snow: a ringed trunk, drooping fronds with snow on them,
    icicles hanging off the frond tips."""
    name = "Snowy Palm %d" % variant

    def build(bm):
        h = 8.0 + 2.0 * variant
        lean = 1.2 + 0.6 * variant
        rings = []
        top = None
        for i in range(9):
            t = i / 8
            x = lean * t * t
            rings.append(ring(bm, (x, 0), 0.4 - 0.13 * t, h * t, 6))
            top = Vector((x, 0, h * t))
        loft(bm, rings)
        bark = _faces(bm, 0)
        k0 = len(bm.faces)
        for i in range(8):
            a = i * math.tau / 8 + variant
            frond(bm, tuple(top), a, 3.8 + 0.6 * rnd(i + variant), 2.6, 0.7, segs=4)
        leaves = _faces(bm, k0)
        k1 = len(bm.faces)
        for i in range(8):
            a = i * math.tau / 8 + variant
            d = Vector((math.cos(a), math.sin(a), 0))
            tip = top + d * 3.6 + Vector((0, 0, -2.2))
            res = bmesh.ops.create_cone(bm, cap_ends=False, segments=4, radius1=0.0, radius2=0.13, depth=0.9)
            for v in res["verts"]:
                v.co += tip + Vector((0, 0, -0.45))
        ice = _faces(bm, k1)
        return [(c.lib("palm_bark"), bark), (c.lib("frond_snow"), leaves), (c.lib("ice"), ice)]

    return c.proto(name, build) and name


def conifer(c, variant=0, height=10.0):
    """A frosted conifer: a trunk and stacked boughs, snow lying on each."""
    name = "Conifer %d %d" % (variant, int(height))

    def build(bm):
        tube(bm, [(0, 0, -0.4), (0, 0, height * 0.3)], [0.4, 0.3], n=6)
        trunk = _faces(bm, 0)
        k0 = len(bm.faces)
        tiers = 4
        for i in range(tiers):
            t = i / tiers
            r = (height * 0.32) * (1 - t * 0.7)
            z = height * (0.18 + 0.2 * i)
            res = bmesh.ops.create_cone(bm, cap_ends=True, segments=7, radius1=r, radius2=r * 0.15, depth=height * 0.34)
            for v in res["verts"]:
                v.co += Vector((0, 0, z + height * 0.17))
                v.co.x += 0.15 * math.sin(v.co.z + variant)
        return [(c.lib("palm_bark"), trunk), (c.lib("pine_snow"), _faces(bm, k0))]

    return c.proto(name, build) and name


def snow_shrub(c, variant=0):
    name = "Snow Shrub %d" % variant

    def build(bm):
        for i in range(3 + variant % 2):
            a = i * 2.2 + variant
            blob(bm, (0.9 * math.cos(a) * (i > 0), 0.9 * math.sin(a) * (i > 0), 0.8), 1.1 - 0.15 * i, sz=0.8, subdiv=0)
        green = _faces(bm, 0)
        k0 = len(bm.faces)
        for i in range(2):
            blob(bm, (0.4 * i, -0.2 * i, 1.45), 0.75, sz=0.4, subdiv=0)
        return [(c.lib("pine_snow"), green), (c.lib(SNOW), _faces(bm, k0))]

    return c.proto(name, build) and name


def snow_drift(c, variant=0):
    name = "Snow Drift %d" % variant

    def build(bm):
        blob(bm, (0, 0, 0.0), 3.0 + variant, sx=1.6, sy=1.0, sz=0.35, subdiv=1)
        return [(c.lib(SNOW), _faces(bm, 0))]

    return c.proto(name, build) and name


def icicles(c, variant=0, length=2.0):
    """A row of icicles hanging from an edge (origin at the top middle, along X)."""
    name = "Icicles %d %d" % (variant, int(length * 10))

    def build(bm):
        for i in range(7):
            x = (i - 3) * 0.55 + 0.2 * math.sin(i * 1.7 + variant)
            ln = length * (0.4 + 0.6 * rnd(i * 3 + variant))
            res = bmesh.ops.create_cone(bm, cap_ends=False, segments=4, radius1=0.0, radius2=0.12 + 0.06 * rnd(i), depth=ln)
            for v in res["verts"]:
                v.co += Vector((x, 0, -ln / 2))
        return [(c.lib("ice"), _faces(bm, 0))]

    return c.proto(name, build) and name


def ice_fall(c, name, x, y, top, foot, width, facing=(0.0, -1.0), coll="Waterfalls"):
    """A frozen waterfall down a cliff: a curtain of chunky ice columns of different
    widths, bulging out as they fall, with icicles along the top. `facing` is the way it
    faces (out from the cliff)."""
    k = Blocks()
    fx, fy = facing
    rot = math.atan2(fy, fx) - math.pi / 2  # local -Y faces out: columns run along local X
    ca, sa = math.cos(rot), math.sin(rot)
    n = max(4, int(width / 2.2))
    for i in range(n):
        u = (i + 0.5) / n - 0.5
        w = width / n * (0.9 + 0.5 * rnd(i * 3.1))
        h = (top - foot) * (0.82 + 0.18 * rnd(i * 5.7))
        bulge = 1.2 + 2.0 * (1 - (2 * u) ** 2) + 0.8 * rnd(i)
        lx, ly = u * width, -bulge
        cx, cy = x + lx * ca - ly * sa, y + lx * sa + ly * ca
        k.box("ice", (cx, cy, top - h / 2), (w, 1.6 + rnd(i * 2) * 1.4, h), rot=rot, snow=False)
        # A frozen splash at the foot.
        k.box("ice", (cx, cy - fy * 0.0, foot + 0.6), (w * 1.3, 3.0, 1.2), rot=rot, snow=True)
    return k.build(c, name, coll, "visual")
