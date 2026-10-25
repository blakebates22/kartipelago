# The beach world's kit (the Tropic Isles): Coral Cove's lighthouse, beach huts, overwater
# bungalows, a lifeguard tower, coral, sailboats, buoys, boardwalk lamps, the start arch,
# signposts and flags; Shipwreck Bay's masts and sails, cannons, barrels, chests and gold,
# a log stockade with its watchtower, lanterns, rowboats and the skull rock's face.
# Each builds one mesh (a prototype) every copy shares; origins at the ground, fronts
# facing +Y. All our own designs, chunky and low-poly.
# SPDX-License-Identifier: MIT

import math

from canyon_props import _beam, _cyl
from course_kit import Vector
from keep_props import _p, _quad
from props import blob, cuboid, frond, loft, ring, tube


def _hip_roof(bm, x, y, z, hx, hy, h, over=0.5):
    """A four-sided roof over a hx x hy box at height z, overhanging by `over`."""
    a, b = hx + over, hy + over
    base = [bm.verts.new((x + sx * a, y + sy * b, z)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    r = min(a, b) * 0.3
    if a >= b:
        top = [bm.verts.new((x - a + b - r, y, z + h)), bm.verts.new((x + a - b + r, y, z + h))]
        bm.faces.new((base[0], base[1], top[1], top[0]))
        bm.faces.new((base[2], base[3], top[0], top[1]))
        bm.faces.new((base[1], base[2], top[1]))
        bm.faces.new((base[3], base[0], top[0]))
    else:
        top = [bm.verts.new((x, y - b + a - r, z + h)), bm.verts.new((x, y + b - a + r, z + h))]
        bm.faces.new((base[1], base[2], top[1], top[0]))
        bm.faces.new((base[3], base[0], top[0], top[1]))
        bm.faces.new((base[0], base[1], top[0]))
        bm.faces.new((base[2], base[3], top[1]))


def _awning(bm, x, y0, y1, z0, z1, w):
    """A sloping awning from (y0, z0) at the wall out to (y1, z1), w wide."""
    pts = [(x - w / 2, y0, z0), (x + w / 2, y0, z0), (x + w / 2, y1, z1), (x - w / 2, y1, z1)]
    _quad(bm, pts, normal=(0, 0, 1), gap=0.06)


# ------------------------------------------------------------------ Coral Cove


def lighthouse(c, h=16.0, r=2.6):
    """A tapering red-and-white banded lighthouse: a gallery with a rail, the lantern room
    glowing, a red cap and a weather vane."""

    def build(P, bm):
        P.add("cove_lighthouse", lambda: _cyl(bm, 0, 0, -1.0, h, r, r * 0.68, n=12))
        P.add("cove_white", lambda: _cyl(bm, 0, 0, h, h + 0.5, r * 0.68 + 0.9, r * 0.68 + 0.9, n=12))
        P.add("cove_metal", lambda: _cyl(bm, 0, 0, h + 0.5, h + 1.4, r * 0.68 + 0.85, r * 0.68 + 0.85, n=12))
        P.add("cove_lamp", lambda: _cyl(bm, 0, 0, h + 0.5, h + 3.2, r * 0.5, r * 0.5, n=10))
        P.add("cove_metal", lambda: _cyl(bm, 0, 0, h + 3.2, h + 3.5, r * 0.6, r * 0.6, n=10))
        P.add("cove_lighthouse", lambda: _cyl(bm, 0, 0, h + 3.5, h + 5.3, r * 0.62, 0.08, n=10))
        P.add("cove_metal", lambda: _beam(bm, (0, 0, h + 5.2), (0, 0, h + 6.4), 0.12))
        P.add("cove_metal", lambda: cuboid(bm, (0.3, 0, h + 6.1), (0.8, 0.06, 0.4)))
        P.add("cove_white", lambda: cuboid(bm, (0, r * 0.97, 1.2), (1.4, 0.3, 2.4)))  # the door's frame
        P.add("cove_metal", lambda: cuboid(bm, (0, r * 1.03, 1.1), (1.0, 0.2, 2.1)))
        for k in range(3):
            z = 4.5 + k * 4.0
            rr = r - (r - r * 0.68) * (z / h)
            P.add("cove_lamp", lambda z=z, rr=rr: cuboid(bm, (0, rr + 0.02, z), (0.6, 0.1, 0.9)))

    return _p(c, "Lighthouse %.0f" % h, build)


def beach_hut(c, variant=0):
    """A little beach hut on short stilts: painted boards, a thatched hip roof, a door,
    a striped awning over the front and two steps."""
    walls = ("cove_hut_teal", "cove_hut_coral", "cove_hut_sun", "cove_white")[variant % 4]
    awn = ("cove_awning_coral", "cove_awning_sun", "cove_awning_teal", "cove_awning_teal")[variant % 4]

    def build(P, bm):
        for sx in (-1, 1):
            for sy in (-1, 1):
                P.add("cove_post", lambda sx=sx, sy=sy: _cyl(bm, sx * 1.6, sy * 1.4, -0.5, 0.8, 0.16, n=5))
        P.add("cove_planks", lambda: cuboid(bm, (0, 0.3, 0.9), (4.0, 3.8, 0.25)))
        P.add(walls, lambda: cuboid(bm, (0, 0, 2.3), (3.4, 3.0, 2.6)))
        P.add("cove_thatch", lambda: _hip_roof(bm, 0, 0, 3.6, 1.7, 1.5, 1.8, over=0.6))
        P.add("cove_white", lambda: cuboid(bm, (0, 1.52, 2.1), (1.1, 0.08, 2.0)))
        P.add("cove_metal", lambda: cuboid(bm, (0, 1.56, 2.0), (0.8, 0.06, 1.7)))
        P.add(awn, lambda: _awning(bm, 0, 1.5, 2.9, 3.4, 2.7, 3.6))
        P.add("cove_planks", lambda: cuboid(bm, (0, 2.5, 0.45), (1.4, 0.6, 0.18)))

    return _p(c, "Beach Hut %d" % variant, build)


def bungalow(c, variant=0):
    """An overwater bungalow: a deck on piles, a hut with a tall thatched roof, a ladder
    down to the water."""
    walls = ("cove_white", "cove_hut_teal", "cove_hut_sun")[variant % 3]

    def build(P, bm):
        for sx in (-1, 0, 1):
            for sy in (-1, 1):
                P.add("cove_post", lambda sx=sx, sy=sy: _cyl(bm, sx * 3.2, sy * 3.0, -3.0, 2.4, 0.22, n=5))
        P.add("cove_planks", lambda: cuboid(bm, (0, 0, 2.5), (7.4, 7.0, 0.3)))
        P.add(walls, lambda: cuboid(bm, (0, -0.8, 4.2), (5.0, 4.0, 3.2)))
        P.add("cove_thatch", lambda: _hip_roof(bm, 0, -0.8, 5.8, 2.5, 2.0, 3.4, over=0.8))
        P.add("cove_metal", lambda: cuboid(bm, (1.2, 1.22, 3.9), (1.0, 0.08, 1.9)))
        P.add("cove_lamp", lambda: cuboid(bm, (-1.2, 1.22, 4.4), (1.2, 0.08, 0.9)))
        for x in (-3.6, 3.6):
            P.add("cove_post", lambda x=x: cuboid(bm, (x, 0, 3.2), (0.12, 7.0, 0.12)))
        P.add("cove_post", lambda: cuboid(bm, (0, 3.45, 3.2), (7.2, 0.12, 0.12)))
        for k in range(4):
            P.add("cove_post", lambda k=k: cuboid(bm, (2.4, 3.6, 2.2 - k * 0.6), (0.9, 0.1, 0.08)))

    return _p(c, "Bungalow %d" % variant, build)


def boardwalk(c, length=10.0, w=2.4, h=1.6):
    """A plain footbridge out to a bungalow: planks on posts, a rope each side."""

    def build(P, bm):
        P.add("cove_planks", lambda: cuboid(bm, (0, length / 2, h), (w, length, 0.2)))
        n = max(2, int(length / 3.0))
        for k in range(n + 1):
            y = length * k / n
            for sx in (-1, 1):
                P.add("cove_post", lambda y=y, sx=sx: _cyl(bm, sx * w / 2, y, -2.5, h + 1.0, 0.12, n=4))
        for sx in (-1, 1):
            P.add("cove_rail", lambda sx=sx: cuboid(bm, (sx * w / 2, length / 2, h + 0.85), (0.08, length, 0.1)))

    return _p(c, "Footbridge %.0f" % length, build)


def lifeguard_tower(c):
    """A lifeguard's tower: four splayed legs, a ladder, a little cabin with a sloping
    roof, a flag."""

    def build(P, bm):
        for sx in (-1, 1):
            for sy in (-1, 1):
                P.add("cove_white", lambda sx=sx, sy=sy: _beam(bm, (sx * 1.6, sy * 1.6, -0.4), (sx * 1.0, sy * 1.0, 3.6), 0.2))
        for k in range(5):
            P.add("cove_white", lambda k=k: cuboid(bm, (0, 2.2 - k * 0.22, 0.4 + k * 0.7), (0.9, 0.12, 0.08)))
        P.add("cove_planks", lambda: cuboid(bm, (0, 0, 3.7), (2.8, 2.8, 0.2)))
        P.add("cove_hut_coral", lambda: cuboid(bm, (0, -0.3, 4.6), (2.4, 1.9, 1.6)))
        P.add("cove_metal", lambda: cuboid(bm, (0, 0.66, 4.8), (1.8, 0.06, 0.8)))
        P.add("cove_white", lambda: _awning(bm, 0, -1.6, 1.4, 5.9, 5.4, 3.0))
        P.add("cove_post", lambda: _beam(bm, (1.2, -1.2, 5.4), (1.2, -1.2, 7.8), 0.08))
        P.add("cove_flag", lambda: _quad(bm, [(1.2, -1.2, 7.7), (2.6, -1.2, 7.4), (2.6, -1.2, 6.6), (1.2, -1.2, 6.9)]), )

    return _p(c, "Lifeguard Tower", build, fit=["cove_flag"])


def coral(c, variant=0):
    """A clump of coral: branching fingers (pink or orange) round a brain-coral dome
    (violet), or a fan."""
    mats = ("cove_coral_pink", "cove_coral_orange", "cove_coral_violet")
    a_mat, b_mat = mats[variant % 3], mats[(variant + 1) % 3]

    def build(P, bm):
        P.add(mats[(variant + 2) % 3], lambda: blob(bm, (0.3, 0.2, 0.2), 1.0, sz=0.6, subdiv=1))
        for k in range(5 + variant % 3):
            a = k * 2.3 + variant
            r = 0.7 + 0.3 * (k % 2)
            x, y = r * math.cos(a), r * math.sin(a)
            h = 1.4 + 0.5 * ((k + variant) % 3)
            P.add(a_mat, lambda x=x, y=y, h=h, a=a: tube(bm, [(x, y, -0.2), (x * 1.3, y * 1.3, h * 0.55), (x * 1.6 + 0.2 * math.cos(a + 1), y * 1.6, h)], [0.22, 0.16, 0.1], n=5))
            if k % 2 == 0:
                P.add(a_mat, lambda x=x, y=y, h=h: tube(bm, [(x * 1.3, y * 1.3, h * 0.5), (x * 2.0, y * 2.0, h * 0.8)], [0.12, 0.08], n=4))
        P.add(b_mat, lambda: _quad(bm, [(-1.6, -0.6, 0), (-0.6, -0.9, 0), (-0.4, -1.2, 1.8), (-1.9, -0.8, 1.6)], normal=(0.3, -1, 0)))

    return _p(c, "Coral %d" % variant, build)


def sailboat(c, variant=0):
    """A small sailboat at anchor: a white hull, a mast and boom, a striped mainsail and
    a jib."""
    sail = ("cove_awning_teal", "cove_awning_coral", "cove_awning_sun")[variant % 3]

    def build(P, bm):
        def hull():
            rings = []
            for k, (y, w, d) in enumerate(((-3.2, 0.6, 0.6), (-2.2, 1.3, 0.9), (0.0, 1.5, 1.0), (2.2, 1.2, 0.9), (3.6, 0.1, 0.5))):
                rings.append([bm.verts.new((sx * w, y, z)) for sx, z in ((-1, 0.8), (-0.7, -d + 0.6), (0.7, -d + 0.6), (1, 0.8))])
            for lo, hi in zip(rings, rings[1:]):
                for i in range(3):
                    bm.faces.new((lo[i], lo[i + 1], hi[i + 1], hi[i]))
            bm.faces.new([rings[0][i] for i in range(4)])
            deck = []
            for r in rings:
                deck.append((r[0], r[3]))
            for (a0, a1), (b0, b1) in zip(deck, deck[1:]):
                if b0 is b1:
                    bm.faces.new((a0, a1, b1))
                else:
                    bm.faces.new((a1, a0, b0, b1))

        P.add("cove_white", hull)
        P.add("cove_post", lambda: _beam(bm, (0, 0.6, 0.8), (0, 0.6, 9.5), 0.14))
        P.add("cove_post", lambda: _beam(bm, (0, 0.6, 2.0), (0, -2.9, 2.0), 0.1))
        P.add(sail, lambda: _quad(bm, [(0, 0.5, 2.1), (0, -2.8, 2.1), (0, 0.5, 9.2)], normal=(1, 0, 0)))
        P.add("cove_white", lambda: _quad(bm, [(0, 0.8, 1.2), (0, 3.5, 1.0), (0, 0.8, 8.4)], normal=(1, 0, 0)))

    return _p(c, "Sailboat %d" % variant, build)


def buoy(c, mat="cove_lighthouse"):
    def build(P, bm):
        P.add(mat, lambda: blob(bm, (0, 0, 0.3), 0.7, sz=0.9, subdiv=1))
        P.add("cove_metal", lambda: _beam(bm, (0, 0, 0.8), (0, 0, 2.2), 0.08))
        P.add("cove_lamp", lambda: blob(bm, (0, 0, 2.3), 0.18, subdiv=0))

    return _p(c, "Buoy " + mat, build)


def lamp_post(c, mat="cove_metal", glow="cove_lamp", wood="cove_post"):
    """A boardwalk lamp: a post, a hook and a hanging lantern."""

    def build(P, bm):
        P.add(wood, lambda: _cyl(bm, 0, 0, -0.5, 3.6, 0.13, 0.1, n=5))
        P.add(mat, lambda: _beam(bm, (0, 0, 3.4), (0, 0.8, 3.4), 0.07))
        P.add(mat, lambda: cuboid(bm, (0, 0.8, 2.95), (0.36, 0.36, 0.08)))
        P.add(glow, lambda: cuboid(bm, (0, 0.8, 2.7), (0.3, 0.3, 0.45)))
        P.add(mat, lambda: cuboid(bm, (0, 0.8, 2.42), (0.36, 0.36, 0.1)))

    return _p(c, "Lamp Post %s" % glow, build)


def start_arch(c, span=24.0, h=7.5, flag="cove_flag", wood="palm_bark", rope="cove_rail"):
    """Two leaning palm-trunk posts, a lashed crossbar with flags hung under it and frond
    tufts on top (spans the road; the crossbar is high above it)."""

    def build(P, bm):
        for sx in (-1, 1):
            x = sx * span / 2
            P.add(wood, lambda x=x, sx=sx: tube(bm, [(x, 0, -0.5), (x - sx * 0.3, 0, h * 0.6), (x - sx * 0.2, 0, h + 0.8)], [0.5, 0.42, 0.38], n=6))
            P.add("palm_frond", lambda x=x, sx=sx: [frond(bm, (x - sx * 0.2, 0, h + 0.9), a * math.tau / 6, 2.8, 1.6, 0.7, segs=4) for a in range(6)])
        P.add(wood, lambda: _beam(bm, (-span / 2 - 0.5, 0, h), (span / 2 + 0.5, 0, h), 0.45))
        P.add(rope, lambda: _beam(bm, (-span / 2, 0, h - 0.3), (span / 2, 0, h - 0.3), 0.12))
        n = 5
        for k in range(n):
            x = -span / 2 + span * (k + 0.5) / n
            P.add(flag, lambda x=x: _quad(bm, [(x - 1.3, 0, h - 0.3), (x + 1.3, 0, h - 0.3), (x + 1.3, 0, h - 3.0), (x - 1.3, 0, h - 3.0)], normal=(0, 1, 0)))

    return _p(c, "Start Arch %.0f %s" % (span, flag), build, fit=[flag])


def signpost(c, sign="cove_sign", wood="cove_post"):
    def build(P, bm):
        P.add(wood, lambda: _cyl(bm, 0, 0, -0.5, 3.0, 0.12, n=5))
        P.add(sign, lambda: _quad(bm, [(-1.0, 0.13, 2.9), (1.0, 0.13, 2.9), (1.0, 0.13, 1.6), (-1.0, 0.13, 1.6)], gap=0.1))

    return _p(c, "Signpost " + sign, build, fit=[sign])


def flag_pole(c, flag="cove_flag", h=8.0, pole="cove_white"):
    def build(P, bm):
        P.add(pole, lambda: _cyl(bm, 0, 0, -0.5, h, 0.12, 0.08, n=5))
        P.add(pole, lambda: blob(bm, (0, 0, h + 0.1), 0.18, subdiv=0))
        P.add(flag, lambda: _quad(bm, [(0.1, 0, h - 0.2), (2.6, 0, h - 0.4), (2.6, 0, h - 2.0), (0.1, 0, h - 1.8)]))

    return _p(c, "Flag Pole %s %.0f" % (flag, h), build, fit=[flag])


def dune_grass(c, mat="cove_grass"):
    """A tuft of dune grass: thin blades fanned out."""

    def build(P, bm):
        for k in range(9):
            a = k * math.tau / 9 + 0.3 * (k % 2)
            L = 0.9 + 0.35 * (k % 3)
            dx, dy = math.cos(a), math.sin(a)
            P.add(mat, lambda dx=dx, dy=dy, L=L: _quad(bm, [(-0.08 * dy, 0.08 * dx, 0), (0.08 * dy, -0.08 * dx, 0), (dx * L * 0.6, dy * L * 0.6, L)], normal=(dx, dy, 0)))

    return _p(c, "Dune Grass " + mat, build)


STACK = [(1.0, 0.0), (0.92, 0.2), (0.96, 0.42), (0.8, 0.62), (0.84, 0.8), (0.6, 0.94), (0.3, 1.0)]
HILL = [(1.0, 0.0), (0.86, 0.12), (0.66, 0.34), (0.5, 0.56), (0.34, 0.78), (0.18, 0.94), (0.06, 1.0)]


def rock_island(c, name, x, y, rx, ry, h, mat, top, seed=0, z0=-6.0, hill=False):
    """A sea stack (sheer, lumpy sides, a small grassy cap) or, `hill`, a far island (a
    green hump rising out of the sea) (visual)."""
    rk = c.rock_mass(name, x, y, rx, ry, h, z0=z0, n=14, seed=seed, bands=HILL if hill else STACK, base=0.0)
    rk["kp_role"] = "visual"
    c.paint_rock(rk, mat, top)
    return rk


# ------------------------------------------------------------------ Shipwreck Bay


def mast(c, h=16.0, broken=False):
    """A ship's mast: a tapering pole, a yard (or two), a crow's nest, ratlines; a broken
    one ends in a splintered stump."""

    def build(P, bm):
        top = h * (0.6 if broken else 1.0)
        P.add("wreck_hull", lambda: _cyl(bm, 0, 0, -0.5, top, 0.45, 0.28, n=6))
        if broken:
            for k in range(4):
                a = k * math.pi / 2
                P.add("wreck_hull", lambda a=a: tube(bm, [(0.2 * math.cos(a), 0.2 * math.sin(a), top), (0.25 * math.cos(a), 0.25 * math.sin(a), top + 1.0 + 0.4 * (k % 2))], [0.14, 0.02], n=4))
        else:
            P.add("wreck_hull", lambda: _beam(bm, (-4.5, 0, h * 0.62), (4.5, 0, h * 0.62), 0.22))
            P.add("wreck_hull", lambda: _beam(bm, (-3.2, 0, h * 0.9), (3.2, 0, h * 0.9), 0.18))
            P.add("wreck_planks", lambda: _cyl(bm, 0, 0, h * 0.74, h * 0.8, 1.0, 1.1, n=8))
        for sx in (-1, 1):
            P.add("wreck_rail", lambda sx=sx: _quad(bm, [(0, 0, top * 0.95), (sx * 3.0, 0.2, 0.3), (sx * 3.0, -0.2, 0.3)], normal=(0, 1, 0)))

    return _p(c, "Mast %.0f %d" % (h, broken), build)


def sail(c, w=8.0, h=6.0, torn=0):
    """A square sail hanging from its yard, bellied a little; torn ones have a ragged
    hem."""

    def build(P, bm):
        for side, off in ((1, 0.0), (-1, -0.06)):
            rows = []
            for j in range(4):
                t = j / 3
                row = []
                for i in range(5):
                    u = i / 4
                    belly = 0.9 * math.sin(math.pi * u) * math.sin(math.pi * (0.2 + 0.8 * t))
                    rag = 0.8 if (torn and j == 3 and i % 2 == 1) else 0.0
                    row.append(bm.verts.new(((u - 0.5) * w, belly + off, -t * h + rag)))
                rows.append(row)
            for a, b in zip(rows, rows[1:]):
                for i in range(4):
                    q = (a[i], a[i + 1], b[i + 1], b[i])
                    bm.faces.new(q if side > 0 else tuple(reversed(q)))

    def build_all(P, bm):
        P.add("wreck_sail", lambda: build(P, bm))

    return _p(c, "Sail %.0f %.0f %d" % (w, h, torn), build_all)


def cannon(c):
    """A cannon on its wooden carriage."""

    def build(P, bm):
        P.add("wreck_planks", lambda: cuboid(bm, (0, 0, 0.45), (1.1, 1.8, 0.5)))
        for sx in (-1, 1):
            for sy in (-1, 1):
                P.add("wreck_iron", lambda sx=sx, sy=sy: _beam(bm, (sx * 0.62, sy * 0.6, 0.3), (sx * 0.78, sy * 0.6, 0.3), 0.5))
        P.add("wreck_iron", lambda: tube(bm, [(0, -0.9, 0.95), (0, 0.4, 1.0), (0, 1.7, 1.05)], [0.42, 0.34, 0.3], n=8))
        P.add("wreck_iron", lambda: blob(bm, (0, -1.0, 0.95), 0.28, subdiv=0))

    return _p(c, "Cannon", build)


def barrel(c, mat="wreck_planks"):
    def build(P, bm):
        rs = [ring(bm, (0, 0), r, z, 8) for r, z in ((0.45, 0.0), (0.55, 0.45), (0.55, 0.85), (0.45, 1.3))]
        P.add(mat, lambda: loft(bm, rs, cap_top=True, cap_bottom=False))
        for z in (0.2, 1.1):
            P.add("wreck_iron", lambda z=z: _cyl(bm, 0, 0, z, z + 0.08, 0.53, n=8))

    return _p(c, "Barrel " + mat, build)


def crate(c, mat="wreck_planks"):
    def build(P, bm):
        P.add(mat, lambda: cuboid(bm, (0, 0, 0.55), (1.1, 1.1, 1.1)))
        P.add("wreck_hull", lambda: _beam(bm, (-0.55, -0.56, 0.0), (0.55, -0.56, 1.1), 0.12))
        P.add("wreck_hull", lambda: _beam(bm, (0.56, -0.55, 0.0), (0.56, 0.55, 1.1), 0.12))

    return _p(c, "Crate " + mat, build)


def chest(c, open_=True):
    """A treasure chest, lid up, heaped with gold."""

    def build(P, bm):
        P.add("wreck_hull", lambda: cuboid(bm, (0, 0, 0.4), (1.4, 0.9, 0.8)))
        P.add("wreck_trim", lambda: cuboid(bm, (0, 0, 0.4), (1.46, 0.2, 0.84)))
        if open_:
            P.add("wreck_hull", lambda: cuboid(bm, (0, -0.55, 1.15), (1.4, 0.12, 0.8), tilt=(0.35, 0)))
            P.add("wreck_gold", lambda: blob(bm, (0, 0, 0.82), 0.62, sx=1.0, sy=0.62, sz=0.45, subdiv=1))
        else:
            P.add("wreck_hull", lambda: cuboid(bm, (0, 0, 0.95), (1.4, 0.9, 0.3)))

    return _p(c, "Chest %d" % open_, build)


def gold_pile(c):
    def build(P, bm):
        P.add("wreck_gold", lambda: blob(bm, (0, 0, 0.0), 1.4, sz=0.5, subdiv=1))
        P.add("wreck_gold", lambda: blob(bm, (0.9, 0.5, 0.1), 0.7, sz=0.5, subdiv=1))

    return _p(c, "Gold Pile", build)


def lantern_post(c):
    return lamp_post(c, mat="wreck_iron", glow="wreck_lantern", wood="wreck_post")


def stockade(c, length=12.0, h=4.0):
    """A run of stockade: upright pointed logs on a sill."""

    def build(P, bm):
        n = int(length / 0.6)
        for k in range(n):
            x = -length / 2 + (k + 0.5) * length / n
            hh = h + 0.3 * ((k * 7) % 3)
            P.add("wreck_logs", lambda x=x, hh=hh: _cyl(bm, x, 0, -0.6, hh, 0.32, 0.3, n=5))
            P.add("wreck_logs", lambda x=x, hh=hh: _cyl(bm, x, 0, hh, hh + 0.6, 0.3, 0.04, n=5))
        P.add("wreck_logs", lambda: _beam(bm, (-length / 2, 0.35, h * 0.7), (length / 2, 0.35, h * 0.7), 0.22))

    return _p(c, "Stockade %.0f" % length, build)


def watchtower(c, h=9.0):
    """A pirate lookout: four log legs, a platform, a thatched roof and a flag."""

    def build(P, bm):
        for sx in (-1, 1):
            for sy in (-1, 1):
                P.add("wreck_logs", lambda sx=sx, sy=sy: _beam(bm, (sx * 2.0, sy * 2.0, -0.5), (sx * 1.5, sy * 1.5, h), 0.35))
        P.add("wreck_planks", lambda: cuboid(bm, (0, 0, h), (4.2, 4.2, 0.3)))
        for sx in (-1, 1):
            P.add("wreck_logs", lambda sx=sx: cuboid(bm, (sx * 2.0, 0, h + 0.6), (0.2, 4.2, 0.9)))
            P.add("wreck_logs", lambda sx=sx: cuboid(bm, (0, sx * 2.0, h + 0.6), (4.2, 0.2, 0.9)))
        for sx in (-1, 1):
            for sy in (-1, 1):
                P.add("wreck_logs", lambda sx=sx, sy=sy: _beam(bm, (sx * 1.9, sy * 1.9, h), (sx * 1.9, sy * 1.9, h + 2.8), 0.2))
        P.add("wreck_thatch", lambda: _hip_roof(bm, 0, 0, h + 2.8, 2.0, 2.0, 2.0, over=0.7))
        P.add("wreck_iron", lambda: _beam(bm, (0, 0, h + 4.6), (0, 0, h + 7.0), 0.1))
        P.add("wreck_flag", lambda: _quad(bm, [(0.1, 0, h + 6.9), (2.8, 0, h + 6.7), (2.8, 0, h + 5.1), (0.1, 0, h + 5.3)]))

    return _p(c, "Watchtower %.0f" % h, build, fit=["wreck_flag"])


def pirate_hut(c, variant=0):
    """A ramshackle hut: plank walls, a thatched roof, a lantern by the door."""

    def build(P, bm):
        P.add("wreck_hull", lambda: cuboid(bm, (0, 0, 1.5), (4.0, 3.4, 3.0)))
        P.add("wreck_thatch", lambda: _hip_roof(bm, 0, 0, 3.0, 2.0, 1.7, 2.2 + 0.4 * variant, over=0.7))
        P.add("wreck_iron", lambda: cuboid(bm, (0.6, 1.72, 1.1), (1.0, 0.08, 2.0)))
        P.add("wreck_lantern", lambda: cuboid(bm, (-0.9, 1.85, 2.2), (0.32, 0.32, 0.45)))

    return _p(c, "Pirate Hut %d" % variant, build)


def rowboat(c):
    def build(P, bm):
        rings = []
        for y, w, d in ((-2.0, 0.2, 0.3), (-1.2, 0.8, 0.5), (0.4, 0.9, 0.55), (1.7, 0.5, 0.45), (2.3, 0.05, 0.4)):
            rings.append([bm.verts.new((sx * w, y, z)) for sx, z in ((-1, 0.5), (-0.6, -d + 0.4), (0.6, -d + 0.4), (1, 0.5))])

        def hull():
            for lo, hi in zip(rings, rings[1:]):
                for i in range(3):
                    bm.faces.new((lo[i], lo[i + 1], hi[i + 1], hi[i]))

        P.add("wreck_planks", hull)
        P.add("wreck_hull", lambda: cuboid(bm, (0, -0.3, 0.3), (1.5, 0.3, 0.08)))
        P.add("wreck_hull", lambda: _beam(bm, (-1.4, -0.3, 0.5), (1.6, 1.0, -0.1), 0.08))

    return _p(c, "Rowboat", build)


def anchor(c):
    def build(P, bm):
        P.add("wreck_iron", lambda: _beam(bm, (0, 0, 0), (0, 0, 3.0), 0.2))
        P.add("wreck_iron", lambda: _beam(bm, (-1.0, 0, 2.6), (1.0, 0, 2.6), 0.15))
        P.add("wreck_iron", lambda: tube(bm, [(-1.4, 0, 1.0), (-1.0, 0, 0.2), (0, 0, 0), (1.0, 0, 0.2), (1.4, 0, 1.0)], 0.14, n=4))
        P.add("wreck_iron", lambda: _cyl(bm, 0, 0, 3.0, 3.1, 0.4, n=8))

    return _p(c, "Anchor", build)


def skull_face(c, r=9.0, h=16.0):
    """A skull carved in the rock, facing +Y: a rounded crown, two deep eye sockets, a
    nose hole and a row of teeth (visual, set into Skull Rock's face)."""

    def build(P, bm):
        P.add("wreck_skull", lambda: blob(bm, (0, 0, h * 0.62), r, sx=1.0, sy=0.82, sz=0.62, subdiv=2))
        P.add("wreck_skull", lambda: cuboid(bm, (0, -0.4, h * 0.26), (r * 1.25, r * 1.2, h * 0.45)))
        for sx in (-1, 1):
            P.add("wreck_iron", lambda sx=sx: blob(bm, (sx * r * 0.36, r * 0.74, h * 0.6), r * 0.22, sx=1.0, sy=0.5, sz=1.1, subdiv=1))
        P.add("wreck_iron", lambda: blob(bm, (0, r * 0.78, h * 0.42), r * 0.1, sx=0.8, sy=0.4, sz=1.2, subdiv=0))
        for k in range(6):
            x = (k - 2.5) * r * 0.16
            P.add("wreck_skull", lambda x=x: cuboid(bm, (x, r * 0.62, h * 0.24), (r * 0.12, 0.6, r * 0.18)))
            P.add("wreck_iron", lambda x=x: cuboid(bm, (x + r * 0.08, r * 0.6, h * 0.24), (r * 0.03, 0.62, r * 0.16)))

    return _p(c, "Skull Face %.0f" % r, build)


def plank_pile(c):
    """Broken planks and a spar washed up."""

    def build(P, bm):
        for k in range(5):
            a = k * 1.1
            P.add("wreck_planks", lambda k=k, a=a: cuboid(bm, (0.4 * k - 0.8, 0.3 * (k % 2), 0.1 + 0.12 * k), (3.0, 0.4, 0.12), rot=a))
        P.add("wreck_hull", lambda: _beam(bm, (-2.0, -0.8, 0.2), (2.5, 1.2, 0.5), 0.3))

    return _p(c, "Plank Pile", build)
