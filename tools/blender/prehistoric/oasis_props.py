# The Oasis Haven kit: swaying palms, cypresses, bougainvillea, hedges and planters, gold
# lanterns, banner poles, chevron boards, market stalls and fruit, café tables, beach
# umbrellas and loungers, moored boats, tiered fountains with their jets, little domed
# kiosks, pots and crates; and the building blocks of the resort's architecture (domes,
# towers, arcaded blocks) used by oasis_scenery.py.
# SPDX-License-Identifier: MIT
#
# Same rules as props.py: each prop is one mesh built once (Course.proto) and placed as
# copies, chunky and low-poly, all original designs.

import math

from course_kit import Vector, bmesh, rnd
from props import _faces, blob, cuboid, frond, loft, ring, tube


def _p(c, name, build):
    return c.proto(name, build) and name


def _cyl(bm, x, y, z0, z1, r0, r1=None, n=8, cap=True):
    r1 = r0 if r1 is None else r1
    loft(bm, [ring(bm, (x, y), r0, z0, n), ring(bm, (x, y), r1, z1, n)], cap_top=cap, cap_bottom=cap)


def dome(bm, x, y, z, r, h=None, n=16, rings=6, onion=0.0):
    """A dome over a circle of radius r at height z, `h` tall (a hemisphere by default);
    `onion` swells it out above its base and draws it to a point."""
    h = h or r
    rs = []
    for k in range(rings + 1):
        t = k / rings
        a = t * math.pi / 2
        rr = r * math.cos(a) * (1 + onion * math.sin(math.pi * t) * 0.6)
        zz = z + h * math.sin(a) * (1 + onion * 0.4 * t)
        if k == rings:
            rr = r * 0.02
        rs.append(ring(bm, (x, y), rr, zz, n))
    loft(bm, rs, cap_top=True)


def finial(bm, x, y, z, s=1.0):
    """A gold finial: a stack of balls on a spike."""
    _cyl(bm, x, y, z, z + 0.6 * s, 0.25 * s, 0.15 * s, n=6)
    blob(bm, (x, y, z + 0.9 * s), 0.38 * s, subdiv=0)
    blob(bm, (x, y, z + 1.55 * s), 0.24 * s, subdiv=0)
    _cyl(bm, x, y, z + 1.7 * s, z + 2.6 * s, 0.1 * s, 0.01 * s, n=4)


# ------------------------------------------------------------------ plants


def palm(c, variant=0, height=10.0):
    """A tall swaying palm: a curving ringed trunk and a crown of drooping fronds (the
    fronds sway in the breeze in game)."""
    name = "Oasis Palm %d %d" % (variant, int(height))
    lean = (1.2, 2.2, 0.6, 1.7)[variant % 4]

    def build(bm):
        rings = []
        top = None
        for k in range(6):
            t = k / 5
            cx = lean * t * t + 0.3 * math.sin(variant + t * 3)
            z = -0.3 + (height + 0.3) * t
            rings.append(ring(bm, (cx, 0), 0.45 - 0.17 * t, z, 5))
            top = (cx, 0, z)
        loft(bm, rings)
        trunk = _faces(bm, 0)
        k0 = len(bm.faces)
        for i in range(7):
            a = i * math.tau / 7 + variant * 0.4
            frond(bm, top, a, 5.0 + 0.8 * rnd(i + variant), 2.6, 1.1, segs=3)
        leaves = _faces(bm, k0)
        return [(c.lib("oasis_bark"), trunk), (c.lib("oasis_frond"), leaves)]

    return _p(c, name, build)


def cypress(c, variant=0):
    """A tall slim garden cypress."""
    name = "Cypress %d" % variant

    def build(bm):
        h = 7.0 + 1.5 * variant
        _cyl(bm, 0, 0, -0.3, 1.0, 0.25, 0.22, n=5)
        rs = [ring(bm, (0, 0), r, z, 8) for r, z in ((0.9, 0.8), (1.35, h * 0.3), (1.2, h * 0.6), (0.7, h * 0.86), (0.06, h))]
        loft(bm, rs)
        return [(c.lib("oasis_bark"), list(range(0, 12))), (c.lib("hedge"), list(range(12, len(bm.faces))))]

    return _p(c, name, build)


def bougainvillea(c, variant=0, size=1.0):
    """A billowing mound of magenta blossom."""
    name = "Bougainvillea %d" % variant

    def build(bm):
        for k in range(4 + variant % 2):
            a = k * 2.1 + variant
            r = (1.1 + 0.35 * (k % 2)) * size
            blob(bm, (math.cos(a) * 0.9 * size, math.sin(a) * 0.9 * size, r * 0.55), r, sz=0.75, subdiv=0)
        return [(c.lib("bougainvillea"), list(range(len(bm.faces))))]

    return _p(c, name, build)


def hedge_box(c, length=6.0):
    name = "Hedge %d" % int(length)

    def build(bm):
        cuboid(bm, (0, 0, 0.6), (length, 1.3, 1.3))
        k0 = len(bm.faces)
        for k in range(int(length / 2)):
            blob(bm, (-length / 2 + 1 + k * 2, 0, 1.35), 0.5, subdiv=0)
        return [(c.lib("hedge"), list(range(k0))), (c.lib("bougainvillea"), _faces(bm, k0))]

    return _p(c, name, build)


def planter(c, variant=0):
    """A painted terracotta urn spilling with flowers."""
    name = "Planter %d" % variant

    def build(bm):
        loft(bm, [ring(bm, (0, 0), r, z, 8) for r, z in ((0.45, 0.0), (0.7, 0.35), (0.8, 0.9), (0.95, 1.1))], cap_bottom=True)
        pot = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        if variant % 2:
            blob(bm, (0, 0, 1.5), 1.0, sz=0.7, subdiv=0)
            leaves = [(c.lib("bougainvillea"), _faces(bm, k0))]
        else:
            for i in range(6):
                frond(bm, (0, 0, 1.0), i * math.tau / 6, 1.6, 0.8, 0.45, segs=3)
            leaves = [(c.lib("oasis_frond"), _faces(bm, k0))]
        return [(c.lib("terracotta"), pot)] + leaves

    return _p(c, name, build)


# ------------------------------------------------------------------ street furniture


def lantern_post(c):
    """A slim lamp post: a cream stone base, a dark iron post and a golden lantern."""
    name = "Gold Lantern"

    def build(bm):
        cuboid(bm, (0, 0, 0.45), (0.8, 0.8, 0.9))
        base = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        _cyl(bm, 0, 0, 0.9, 3.8, 0.12, 0.09, n=4)
        iron = _faces(bm, k0)
        k1 = len(bm.faces)
        loft(bm, [ring(bm, (0, 0), r, z, 5) for r, z in ((0.25, 3.8), (0.45, 4.1), (0.45, 4.6), (0.03, 5.3))], cap_bottom=True)
        gold = _faces(bm, k1)
        return [(c.lib("oasis_stone"), base), (c.lib("weathered_timber"), iron), (c.lib("gold_leaf"), gold)]

    return _p(c, name, build)


def banner_pole(c, variant=0):
    """A tall pole with a gold finial and a hanging blue-and-gold banner (it sways)."""
    name = "Oasis Banner %d" % variant

    def build(bm):
        _cyl(bm, 0, 0, -0.3, 8.0, 0.16, 0.12, n=6)
        pole = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        finial(bm, 0, 0, 8.0, 0.8)
        cuboid(bm, (0.75, 0, 7.4), (1.6, 0.14, 0.14))
        gold = _faces(bm, k0)
        k1 = len(bm.faces)
        cuboid(bm, (0.8, 0, 5.4), (1.4, 0.06, 3.8))
        cloth = _faces(bm, k1)
        return [(c.lib("oasis_stone"), pole), (c.lib("gold_leaf"), gold), (c.lib("oasis_banner"), cloth)]

    return _p(c, name, build)


def chevron_board(c):
    """A red-and-white chevron board on a cream plinth (faces +Y)."""
    name = "Red Chevron"

    def build(bm):
        cuboid(bm, (0, 0, 0.4), (4.4, 0.8, 0.8))
        base = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        cuboid(bm, (0, 0, 1.45), (4.2, 0.2, 1.3))
        board = _faces(bm, k0)
        return [(c.lib("oasis_stone"), base), (c.lib("chevron_red"), board)]

    return _p(c, name, build)


AWNINGS = ("awning_sun", "awning_sea", "awning_teal", "awning_rose")


def market_stall(c, variant=0):
    """A market stall: a wooden counter heaped with produce, posts, and a striped sloping
    awning (it ripples in the breeze). Faces +Y (the counter's front)."""
    name = "Stall %d" % variant

    def build(bm):
        cuboid(bm, (0, 0.4, 0.5), (4.0, 1.4, 1.0))
        wood = list(range(len(bm.faces)))
        for x in (-1.9, 1.9):
            for y in (-0.9, 1.1):
                cuboid(bm, (x, y, 1.6), (0.16, 0.16, 3.2))
        wood = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        cuboid(bm, (0, 0.4, 1.12), (3.8, 1.2, 0.24))
        goods = _faces(bm, k0)
        k1 = len(bm.faces)
        v = [bm.verts.new(p) for p in ((-2.3, -1.3, 3.4), (2.3, -1.3, 3.4), (2.3, 2.0, 2.6), (-2.3, 2.0, 2.6))]
        bm.faces.new(v)
        w = [bm.verts.new(p) for p in ((-2.3, -1.3, 3.38), (2.3, -1.3, 3.38), (2.3, 2.0, 2.58), (-2.3, 2.0, 2.58))]
        bm.faces.new(list(reversed(w)))
        for x in range(5):
            xx = -2.3 + x * 1.15
            f = [bm.verts.new(p) for p in ((xx, 2.0, 2.6), (xx + 1.15, 2.0, 2.6), (xx + 0.575, 2.0, 2.1))]
            bm.faces.new(f)
            bm.faces.new([bm.verts.new(p.co) for p in reversed(f)])
        cloth = _faces(bm, k1)
        return [(c.lib("weathered_timber"), wood), (c.lib("fruit"), goods), (c.lib(AWNINGS[variant % 4]), cloth)]

    return _p(c, name, build)


def cafe_table(c, variant=0):
    """A round café table with stools and a striped parasol."""
    name = "Cafe %d" % variant

    def build(bm):
        _cyl(bm, 0, 0, 0.0, 0.75, 0.08, n=5)
        _cyl(bm, 0, 0, 0.75, 0.85, 0.7, n=10)
        for k in range(3):
            a = k * math.tau / 3 + 0.4
            _cyl(bm, math.cos(a) * 1.15, math.sin(a) * 1.15, 0.0, 0.5, 0.25, 0.3, n=6)
        _cyl(bm, 0, 0, 0.85, 2.6, 0.05, n=4)
        wood = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        loft(bm, [ring(bm, (0, 0), 1.7, 2.3, 8), ring(bm, (0, 0), 0.05, 2.9, 8)], cap_top=False)
        loft(bm, [ring(bm, (0, 0), 0.05, 2.88, 8), ring(bm, (0, 0), 1.7, 2.28, 8)], cap_top=False)
        cloth = _faces(bm, k0)
        return [(c.lib("weathered_timber"), wood), (c.lib(AWNINGS[(variant + 1) % 4]), cloth)]

    return _p(c, name, build)


def beach_set(c, variant=0):
    """A beach umbrella over two loungers and a towel."""
    name = "Beach Set %d" % variant

    def build(bm):
        _cyl(bm, 0, 0, -0.2, 2.6, 0.05, n=4)
        pole = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        for x in (-0.9, 0.9):
            cuboid(bm, (x, 0.6, 0.3), (0.7, 1.9, 0.12), tilt=(0.0, 0.0))
            cuboid(bm, (x, -0.35, 0.55), (0.7, 0.5, 0.12), tilt=(0.6, 0.0))
        lounger = _faces(bm, k0)
        k1 = len(bm.faces)
        loft(bm, [ring(bm, (0, 0), 1.6, 2.2, 8), ring(bm, (0, 0), 0.05, 2.75, 8)], cap_top=False)
        loft(bm, [ring(bm, (0, 0), 0.05, 2.73, 8), ring(bm, (0, 0), 1.6, 2.18, 8)], cap_top=False)
        cloth = _faces(bm, k1)
        return [(c.lib("weathered_timber"), pole), (c.lib("canvas_blue" if variant % 2 else "canvas_sun"), lounger),
                (c.lib(AWNINGS[variant % 4]), cloth)]

    return _p(c, name, build)


def moored_boat(c, variant=0):
    """A little sailing boat tied up at a dock, sail furled (faces +X)."""
    name = "Moored Boat %d" % variant

    def build(bm):
        rings = []
        for k in range(7):
            t = k / 6
            x = -2.6 + 5.6 * t
            w = 1.2 * math.sin(math.pi * min(1.0, 0.15 + t * 0.95)) + 0.05
            rings.append([bm.verts.new(p) for p in ((x, -w, 0.55), (x, w, 0.55), (x, w * 0.6, -0.3), (x, -w * 0.6, -0.3))])
        loft(bm, rings, cap_top=True, cap_bottom=True)
        hull = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        _cyl(bm, 0.4, 0, 0.5, 5.0, 0.08, n=4)
        _cyl(bm, -1.6, 0, 1.4, 1.7, 0.25, n=6)
        mast = _faces(bm, k0)
        k1 = len(bm.faces)
        cuboid(bm, (-0.6, 0, 1.55), (2.4, 0.35, 0.35))
        sail = _faces(bm, k1)
        return [(c.lib("wood_dock"), hull), (c.lib("weathered_timber"), mast), (c.lib(AWNINGS[variant % 4]), sail)]

    return _p(c, name, build)


def crates(c, variant=0):
    """Crates, sacks and a tall painted jar."""
    name = "Oasis Goods %d" % variant

    def build(bm):
        cuboid(bm, (0, 0, 0.5), (1.0, 1.0, 1.0), rot=0.2 * variant)
        cuboid(bm, (1.1, 0.3, 0.4), (0.8, 0.8, 0.8), rot=0.5)
        wood = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        loft(bm, [ring(bm, (-1.0, 0.4), r, z, 8) for r, z in ((0.3, 0.0), (0.5, 0.5), (0.45, 1.1), (0.25, 1.4), (0.3, 1.55))], cap_bottom=True)
        jar = _faces(bm, k0)
        k1 = len(bm.faces)
        blob(bm, (0.2, -0.9, 0.35), 0.45, sz=0.8, subdiv=0)
        sack = _faces(bm, k1)
        return [(c.lib("wood_dock"), wood), (c.lib("terracotta"), jar), (c.lib("rug"), sack)]

    return _p(c, name, build)


def kiosk(c, variant=0):
    """A little open kiosk: four columns, a blue (or turquoise) dome, a gold finial."""
    name = "Kiosk %d" % variant

    def build(bm):
        _cyl(bm, 0, 0, 0.0, 0.5, 3.4, n=8)
        for k in range(4):
            a = k * math.pi / 2 + math.pi / 4
            _cyl(bm, math.cos(a) * 2.5, math.sin(a) * 2.5, 0.5, 4.0, 0.28, n=6)
        _cyl(bm, 0, 0, 4.0, 4.7, 3.2, n=8)
        stone = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        dome(bm, 0, 0, 4.7, 3.0, h=3.0, n=12, rings=4, onion=0.5 if variant % 2 else 0.0)
        cap = _faces(bm, k0)
        k1 = len(bm.faces)
        finial(bm, 0, 0, 7.9, 0.7)
        gold = _faces(bm, k1)
        return [(c.lib("oasis_stone"), stone), (c.lib("dome_teal" if variant % 2 else "dome_blue"), cap), (c.lib("gold_leaf"), gold)]

    return _p(c, name, build)


def fountain(c, variant=0, r=4.0):
    """A tiered fountain: an octagonal basin with blue tiles, water in it, a column, an
    upper bowl, and the jet itself (a scrolling column of water; the spray is the game's
    "fountain" entity). Origin at the ground; the jet's top at about 2.4 r."""
    name = "Fountain %d %d" % (variant, int(r * 10))

    def build(bm):
        loft(bm, [ring(bm, (0, 0), rr, z, 8, phase=math.pi / 8) for rr, z in ((r, -0.2), (r, 0.7), (r - 0.4, 0.7))], cap_bottom=True, cap_top=False)
        stone = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        bm.faces.new(ring(bm, (0, 0), r - 0.4, 0.5, 8, phase=math.pi / 8))
        water = _faces(bm, k0)
        k1 = len(bm.faces)
        _cyl(bm, 0, 0, 0.5, 1.9, 0.35 * r / 4, n=8)
        loft(bm, [ring(bm, (0, 0), rr, z, 10) for rr, z in ((0.3 * r / 4, 1.9), (1.5 * r / 4, 2.4), (1.6 * r / 4, 2.6))], cap_top=False)
        stone2 = _faces(bm, k1)
        k2 = len(bm.faces)
        bm.faces.new(ring(bm, (0, 0), 1.45 * r / 4, 2.5, 10))
        water2 = _faces(bm, k2)
        k3 = len(bm.faces)
        # The jet and the veil spilling from the bowl.
        _cyl(bm, 0, 0, 2.5, 2.4 * r, 0.18, 0.05, n=6, cap=False)
        jet = _faces(bm, k3)
        k4 = len(bm.faces)
        loft(bm, [ring(bm, (0, 0), rr, z, 10) for rr, z in ((1.62 * r / 4, 2.55), (1.75 * r / 4, 1.6), (2.0 * r / 4, 0.55))], cap_top=False)
        veil = _faces(bm, k4)
        return [(c.lib("oasis_stone"), stone + stone2), (c.lib("canal_water"), water + water2), (c.lib("fountain_jet"), jet),
                (c.lib("falls_oasis"), veil)]

    return _p(c, name, build)


def column(bm, x, y, z0, z1, r=0.6, n=8):
    """A slender column with a base and a capital."""
    _cyl(bm, x, y, z0, z0 + 0.5, r * 1.5, r * 1.3, n=n)
    _cyl(bm, x, y, z0 + 0.5, z1 - 0.6, r, r * 0.85, n=n)
    _cyl(bm, x, y, z1 - 0.6, z1, r * 1.0, r * 1.6, n=n)
