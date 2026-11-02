# The Island Hop's own pieces (Blake, Nov 1): mangroves on their roots, driftwood, the
# fishers' stilt houses, drying racks and nets, the mended bridge's scaffold, the great
# turtle rock, the smugglers' dock gear.
# SPDX-License-Identifier: MIT
#
# Same rules as props.py: each prop is one mesh built once (Course.proto) and placed as
# copies, all original designs. Built with keep_props' parts kit (keep_props._p).

import math

from canyon_props import _beam, _cyl
from course_kit import rnd
from keep_props import _p
from props import blob, cuboid, loft, ring, tube


def mangrove(c, variant=0, height=7.0):
    """A mangrove: a short trunk standing up on a skirt of arched prop roots that reach
    down into the water and mud all round, a broad low crown of leaf clumps. Origin at
    the water's level under it."""
    v = variant

    def build(P, bm):
        base = 1.8 + 0.3 * (v % 2)

        def roots():
            n = 8 + v % 3
            for i in range(n):
                a = i * math.tau / n + 0.3 * v
                r = 2.4 + 0.8 * rnd(i * 3 + v)
                top = (0.25 * math.cos(a), 0.25 * math.sin(a), base + 0.4)
                mid = (r * 0.55 * math.cos(a), r * 0.55 * math.sin(a), base + 0.6 + 0.4 * rnd(i))
                foot = (r * math.cos(a + 0.15), r * math.sin(a + 0.15), -0.8)
                tube(bm, [top, mid, foot], [0.16, 0.13, 0.11], n=5)
            tube(bm, [(0, 0, base), (0.3, 0.1, height * 0.6), (0.5, -0.2, height * 0.85)], [0.38, 0.3, 0.2], n=7)
            for a in (0.7, 2.6, 4.4):  # (its boughs)
                tube(bm, [(0.3, 0.0, height * 0.55), (2.6 * math.cos(a + v), 2.6 * math.sin(a + v), height * 0.8)],
                     [0.18, 0.1], n=5)
        P.add("jungle_bark", roots)

        def crown():
            for i, (dx, dy, dz, r) in enumerate(((0, 0, 1.0, 2.6), (2.2, 0.6, 0.75, 2.0), (-1.8, 1.4, 0.8, 1.9),
                                                (0.4, -2.2, 0.7, 2.0), (-1.2, -1.4, 0.9, 1.7))):
                a = v * 1.3
                x, y = dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)
                blob(bm, (x, y, height * 0.82 + dz), r, sx=1.2, sy=1.2, sz=0.6, subdiv=1)
        P.add("canopy_bright", crown)

    return _p(c, "Mangrove %d %d" % (v, int(height)), build)


def driftwood(c, variant=0):
    """A bleached driftwood log, a broken branch off it, lying on the sand."""

    def build(P, bm):
        ln = 4.0 + 1.5 * (variant % 2)
        P.add("dead_wood", lambda: tube(bm, [(-ln / 2, 0, 0.18), (0, 0.2, 0.25), (ln / 2, -0.1, 0.16)], [0.32, 0.28, 0.2], n=7))
        P.add("dead_wood", lambda: tube(bm, [(0.4, 0.15, 0.3), (1.2, 1.1, 0.5), (1.6, 1.9, 0.35)], [0.12, 0.08, 0.05], n=5))
        P.add("dead_wood", lambda: tube(bm, [(-ln / 2, 0, 0.18), (-ln / 2 - 0.6, 0.5, 0.1)], [0.2, 0.08], n=5))

    return _p(c, "Driftwood %d" % variant, build)


def stilt_house(c, variant=0):
    """A fisher family's house on stilts over the water: a plank deck on posts, a hut of
    painted boards under a thatched roof, a ladder down to the water, a net hung over the
    rail, a lamp. Origin at the water's level; its front (the ladder) toward -Y."""
    walls = ("cove_hut_teal", "cove_hut_coral", "cove_hut_sun", "cove_white")[variant % 4]

    def build(P, bm):
        deck = 2.4
        for sx in (-1, 1):
            for sy in (-1, 0, 1):
                P.add("cove_post", lambda sx=sx, sy=sy: _cyl(bm, sx * 2.7, sy * 2.5, -3.0, deck, 0.2, n=6))
        P.add("cove_planks", lambda: cuboid(bm, (0, 0, deck + 0.1), (6.2, 6.0, 0.25)))
        P.add(walls, lambda: cuboid(bm, (0, 0.6, deck + 1.5), (4.2, 3.6, 2.6)))
        P.add("cove_thatch", lambda: loft(bm, [ring(bm, (0, 0.6), 3.4, deck + 2.7, 4, rx=3.6, phase=math.pi / 4),
                                               ring(bm, (0, 0.6), 0.25, deck + 4.6, 4, phase=math.pi / 4)], cap_top=True))
        P.add("cove_white", lambda: cuboid(bm, (0, -1.22, deck + 1.2), (1.1, 0.08, 2.0)))
        P.add("cove_metal", lambda: cuboid(bm, (0, -1.25, deck + 1.1), (0.8, 0.06, 1.7)))
        # The rail round the deck's front, a ladder down to the water.
        for x in (-2.9, -1.5, 1.5, 2.9):
            P.add("cove_post", lambda x=x: _cyl(bm, x, -2.9, deck, deck + 1.0, 0.08, n=5))
        P.add("cove_rail", lambda: cuboid(bm, (-2.2, -2.9, deck + 0.95), (1.6, 0.1, 0.1)))
        P.add("cove_rail", lambda: cuboid(bm, (2.2, -2.9, deck + 0.95), (1.6, 0.1, 0.1)))
        for sx in (-0.45, 0.45):
            P.add("cove_post", lambda sx=sx: _beam(bm, (sx, -3.0, deck), (sx, -3.8, -1.0), 0.07))
        for k in range(5):
            z = deck - 0.6 - k * 0.65
            P.add("cove_post", lambda z=z, k=k: _beam(bm, (-0.45, -3.1 - k * 0.15, z), (0.45, -3.1 - k * 0.15, z), 0.05))
        # A net hung over the side rail, and its floats.
        P.add("isle_net", lambda: cuboid(bm, (2.95, 0.6, deck + 0.4), (0.06, 3.2, 1.4)))
        for k in range(4):
            P.add("cove_flag", lambda k=k: blob(bm, (3.0, -0.6 + 0.8 * k, deck + 1.05), 0.12, subdiv=1))
        P.add("cove_lamp", lambda: cuboid(bm, (1.9, -1.4, deck + 2.1), (0.3, 0.3, 0.4)))

    return _p(c, "Stilt House %d" % variant, build)


def drying_rack(c, variant=0):
    """Fish hung to dry on a rack of poles, a net spread over the end of it."""

    def build(P, bm):
        for x in (-2.0, 0.0, 2.0):
            for y in (-0.5, 0.5):
                P.add("cove_post", lambda x=x, y=y: _beam(bm, (x, y, -0.3), (x, 0.0, 2.2), 0.07))
        P.add("cove_post", lambda: _beam(bm, (-2.3, 0, 2.1), (2.3, 0, 2.1), 0.06))
        for k in range(9):
            x = -1.8 + 0.45 * k
            P.add("cove_metal" if k % 3 else "cove_coral_orange",
                  lambda x=x, k=k: blob(bm, (x, 0.0, 1.65 - 0.05 * (k % 2)), 0.16, sx=0.5, sy=0.3, sz=1.6, subdiv=1))
        P.add("isle_net", lambda: cuboid(bm, (2.6, 0.0, 1.0), (1.2, 0.06, 2.0), rot=0.4, tilt=(0.0, 0.25)))

    return _p(c, "Drying Rack %d" % variant, build)


def lobster_pots(c):
    """A stack of wicker pots, a coil of rope, a float."""

    def build(P, bm):
        for i, (x, y, z) in enumerate(((0, 0, 0.3), (0.75, 0.1, 0.3), (0.35, 0.05, 0.85))):
            P.add("bamboo", lambda x=x, y=y, z=z: loft(bm, [ring(bm, (x, y), 0.36, z - 0.3, 8), ring(bm, (x, y), 0.3, z + 0.25, 8),
                                                         ring(bm, (x, y), 0.12, z + 0.3, 8)], cap_top=True, cap_bottom=True))
        P.add("rope_rail", lambda: loft(bm, [ring(bm, (-0.8, 0.4), 0.4, 0.0, 12), ring(bm, (-0.8, 0.4), 0.4, 0.18, 12)], cap_top=True))
        P.add("cove_flag", lambda: blob(bm, (-0.6, -0.5, 0.2), 0.2, subdiv=1))

    return _p(c, "Lobster Pots", build)


def scaffold(c, length=10.0):
    """The mended bridge's last scaffold, left beside it: poles lashed in a frame, a pile
    of fresh planks on its foot, a mallet."""

    def build(P, bm):
        for x in (-length / 2, 0.0, length / 2):
            for y in (-0.6, 0.6):
                P.add("bamboo", lambda x=x, y=y: _beam(bm, (x, y, -3.0), (x, y, 4.0), 0.09))
        for z in (0.5, 2.5):
            for y in (-0.6, 0.6):
                P.add("bamboo", lambda z=z, y=y: _beam(bm, (-length / 2, y, z), (length / 2, y, z), 0.07))
        P.add("bamboo", lambda: _beam(bm, (-length / 2, 0, 0.5), (0, 0, 2.5), 0.06))
        P.add("bamboo", lambda: _beam(bm, (0, 0, 2.5), (length / 2, 0, 0.5), 0.06))
        for k in range(6):
            P.add("wood_planks", lambda k=k: cuboid(bm, (0.2 * (k % 2), 0, 2.62 + 0.12 * k), (3.2, 1.2, 0.1), rot=0.04 * k))

    return _p(c, "Scaffold %d" % int(length), build)


def turtle_rock(c):
    """The great turtle rock of Turtle Rocks: a dome of a shell plated in great scutes,
    a head up out of the sea looking east, flippers of rock, moss and grass on its back.
    Origin at the water."""

    def build(P, bm):
        P.add("isle_rock", lambda: blob(bm, (0, 0, -2.0), 9.0, sx=1.25, sy=1.0, sz=0.7, subdiv=3))
        def scutes():
            for i in range(6):
                a = i * math.tau / 6
                blob(bm, (5.8 * math.cos(a), 4.6 * math.sin(a), 2.0), 2.4, sx=1.1, sy=1.0, sz=0.38, subdiv=2)
            blob(bm, (0, 0, 4.2), 3.0, sx=1.2, sy=1.0, sz=0.35, subdiv=2)
        P.add("cove_rock", scutes)
        P.add("isle_rock", lambda: [blob(bm, (12.6, 0.0, 1.2), 2.4, sx=1.3, sy=0.9, sz=0.9, subdiv=2),
                                    tube(bm, [(9.5, 0, -0.5), (11.4, 0, 0.6)], [1.6, 1.4], n=10)])
        P.add("cove_rock", lambda: [blob(bm, (8.0 * sx_, 7.5 * sy_, -0.6), 2.6, sx=1.4, sy=0.6, sz=0.35, subdiv=1)
                                    for sx_ in (-1, 1) for sy_ in (-1, 1)])
        P.add("ship_hull", lambda: [blob(bm, (13.7, sd * 0.9, 1.7), 0.32, subdiv=1) for sd in (-1, 1)])
        P.add("cove_grass", lambda: blob(bm, (-1.0, 0.5, 4.9), 3.6, sx=1.3, sy=1.0, sz=0.25, subdiv=2))

    return _p(c, "Turtle Rock", build)


def dock_crates(c, variant=0):
    """The smugglers' goods on the dock: crates roped in a stack, barrels, a sack."""

    def build(P, bm):
        for i, (x, y, z, s) in enumerate(((0, 0, 0.5, 1.0), (1.1, 0.1, 0.45, 0.9), (0.5, 0.0, 1.45, 0.85))[:2 + variant % 2]):
            P.add("wreck_planks", lambda x=x, y=y, z=z, s=s, i=i: cuboid(bm, (x, y, z), (s, s, s), rot=0.2 * i))
        for k in range(2):
            P.add("barrel_wood", lambda k=k: loft(bm, [ring(bm, (-1.0 - 0.8 * k, 0.4), 0.38, 0.0, 10),
                                                       ring(bm, (-1.0 - 0.8 * k, 0.4), 0.44, 0.55, 10),
                                                       ring(bm, (-1.0 - 0.8 * k, 0.4), 0.38, 1.1, 10)], cap_top=True))
        P.add("rope_rail", lambda: cuboid(bm, (0, 0, 0.5), (1.04, 0.08, 1.04)))
        P.add("thatch_pale", lambda: blob(bm, (0.9, -0.9, 0.35), 0.45, sx=1.1, sy=0.8, sz=0.8, subdiv=1))

    return _p(c, "Dock Crates %d" % variant, build)
