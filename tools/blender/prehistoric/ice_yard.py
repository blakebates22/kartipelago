# The ice harvesters' yard, in the middle of the Ice Hollow (Blake, Oct 30: "now we are
# crafter ice workers, not christmasy fun ice carvers. think of the people who cut the
# ice in frozen. almost lumberjack vibes, blue collar"). It replaces the Frost Spire and
# the garden of sculptures.
#
# The cutting pond, its ice scored in a grid of saw cuts, half of it cut out already to
# dark open water where blocks float, saws and pike poles left standing in the ice; the
# derrick, a tall timber A-frame with its boom swung out over the pond, guy ropes, a
# block-and-tackle and a winch, lifting a great block (the yard's landmark from the
# Crest); the ice house, blocks stacked in straw under a timber lean-to, a ramp up to its
# loading deck and sledges waiting with their harness poles; the brazier the cutters warm
# their hands at, on log benches; the grindstone and the tool bench; lantern poles; and
# one commission, a great block being roughed out into a dragon's head under scaffolding
# (Rimefang's, demanded of them). All our own designs; prototypes' fronts face +Y, their
# origins on the ground.
# SPDX-License-Identifier: MIT

import math

import snow_layout as SL
from canyon_props import _beam
from carvers_village import _crystal, _wedge
from keep_props import _p
from props import blob, cuboid, loft, ring

ICE = "glacier_ice"
BLUE = "icefall_blue"
CUT = "cavern_ice"  # (the saw cuts, dark)
WATER = "frost_pool"
TIMBER = "timber_beam"
PLANK = "weathered_timber"
DECK = "plank_deck"
ROPE = "rope_rail"
IRON = "keep_iron"
STRAW = "thatch"
STONE = "frost_stone"
LOGS = "log_end"
LAMP = "lantern_amber"
SNOW = "snow_ground"
FIRE = "keep_flame"


def _cyl(P, bm, mat, x, y, z0, z1, r0, r1=None, n=8):
    r1 = r0 if r1 is None else r1
    P.add(mat, lambda: loft(bm, [ring(bm, (x, y), r0, z0, n), ring(bm, (x, y), r1, z1, n)], cap_top=True, cap_bottom=True))


def _pulley(P, bm, x, y, z, r=0.35):
    """A pulley block: an iron-bound wooden sheave in its cheeks, hung by a hook."""
    P.add(TIMBER, lambda: cuboid(bm, (x, y, z), (0.24, 2 * r + 0.2, 2 * r + 0.3)))
    P.add(IRON, lambda: cuboid(bm, (x, y, z), (0.3, 2 * r, 0.12)))
    P.add(IRON, lambda: cuboid(bm, (x, y, z + r + 0.3), (0.08, 0.08, 0.5)))


def _rope(P, bm, a, b, w=0.07):
    P.add(ROPE, lambda: _beam(bm, a, b, w))


# ------------------------------------------------------------------ the derrick


def derrick(c):
    """The derrick: an A-frame mast 22 m tall of lashed timbers, braced, guyed back with
    ropes to stakes; its boom swung out (along +Y) over the pond; a block-and-tackle at
    the boom's head, a great block of ice slung in tongs from it; a winch at its foot, the
    lifting rope wound on its drum."""
    H = 22.0

    def build(P, bm):
        # The A-frame's legs, its foot sills, cross-braces up it.
        for sx in (-1, 1):
            P.add(TIMBER, lambda sx=sx: _beam(bm, (sx * 3.6, -1.0, 0.0), (sx * 0.25, 0.0, H), 0.55))
            P.add(TIMBER, lambda sx=sx: _beam(bm, (sx * 3.6, -1.0, 0.0), (sx * 0.5, -4.5, 0.0), 0.45))
        P.add(TIMBER, lambda: _beam(bm, (-3.8, -1.0, 0.3), (3.8, -1.0, 0.3), 0.5))
        for k, z in enumerate((5.0, 10.0, 15.0)):
            f = z / H
            x0 = 3.6 * (1 - f) + 0.25 * f
            P.add(TIMBER, lambda z=z, x0=x0: _beam(bm, (-x0, -1.0 * (1 - z / H), z), (x0, -1.0 * (1 - z / H), z), 0.35))
            if k < 2:
                z2 = z + 5.0
                x1 = 3.6 * (1 - z2 / H) + 0.25 * z2 / H
                sd = 1 if k % 2 == 0 else -1
                P.add(TIMBER, lambda z=z, z2=z2, x0=x0, x1=x1, sd=sd: _beam(bm, (-sd * x0, -1.0 * (1 - z / H), z),
                                                                              (sd * x1, -1.0 * (1 - z2 / H), z2), 0.28))
        # Iron bands at the lashings, and the cap.
        P.add(IRON, lambda: cuboid(bm, (0, 0, H - 0.3), (1.2, 0.8, 0.6)))
        # The back leg, raking down behind.
        P.add(TIMBER, lambda: _beam(bm, (0.0, -9.0, 0.0), (0.0, -0.2, H - 0.6), 0.5))
        # The boom, out over the pond from a pivot 4 m up, held by its topping lift.
        foot = (0.0, 0.6, 4.0)
        head = (0.0, 12.0, 16.5)
        P.add(TIMBER, lambda: _beam(bm, foot, head, 0.5))
        P.add(IRON, lambda: cuboid(bm, foot, (1.0, 1.0, 0.6)))
        _rope(P, bm, (0.0, 0.0, H - 0.4), head, 0.09)
        _rope(P, bm, (0.0, 0.2, H - 0.8), (0.0, 11.6, 16.8), 0.09)
        _pulley(P, bm, 0.0, 12.1, 15.6, 0.45)
        # The block slung under it: the fall rope, the tongs, the block.
        bz = 7.5
        _rope(P, bm, (0.0, 12.1, 15.0), (0.0, 12.1, bz + 2.6), 0.1)
        _pulley(P, bm, 0.0, 12.1, bz + 2.3, 0.35)
        for sx in (-1, 1):
            P.add(IRON, lambda sx=sx: _beam(bm, (0.0, 12.1, bz + 1.9), (sx * 1.0, 12.1, bz + 0.6), 0.12))
            P.add(IRON, lambda sx=sx: _beam(bm, (sx * 1.0, 12.1, bz + 0.6), (sx * 0.85, 12.1, bz - 0.2), 0.12))
        P.add(ICE, lambda: cuboid(bm, (0.0, 12.1, bz - 0.4), (1.7, 1.5, 1.4), rot=0.2))
        P.add(SNOW, lambda: cuboid(bm, (0.0, 12.1, bz + 0.33), (1.6, 1.3, 0.08), rot=0.2))
        # The fall rope back to the winch.
        _rope(P, bm, (0.0, 0.3, H - 0.6), (0.0, 12.0, 16.2), 0.06)
        _rope(P, bm, (0.0, -0.4, H - 1.0), (0.0, -3.0, 1.5), 0.06)
        # The winch: its frame, the drum wound with rope, two cranks.
        for sx in (-1, 1):
            P.add(TIMBER, lambda sx=sx: cuboid(bm, (sx * 1.1, -3.0, 0.8), (0.25, 1.4, 1.6)))
            P.add(IRON, lambda sx=sx: _beam(bm, (sx * 1.3, -3.0, 1.3), (sx * 1.3, -2.4, 1.9), 0.08))
            P.add(IRON, lambda sx=sx: _beam(bm, (sx * 1.3, -2.4, 1.9), (sx * 1.6, -2.4, 1.9), 0.08))
        P.add(ROPE, lambda: _beam(bm, (-0.95, -3.0, 1.3), (0.95, -3.0, 1.3), 0.8))
        # Guy ropes back to stakes.
        for sx in (-1, 1):
            _rope(P, bm, (sx * 0.2, -0.3, H - 0.8), (sx * 9.0, -11.0, 0.4), 0.06)
            P.add(TIMBER, lambda sx=sx: cuboid(bm, (sx * 9.0, -11.0, 0.3), (0.3, 0.3, 1.0), tilt=(0.3, 0.0)))
        # A lantern up the mast.
        P.add(IRON, lambda: cuboid(bm, (0, 0.6, 12.0), (0.08, 1.0, 0.08)))
        P.add(LAMP, lambda: cuboid(bm, (0, 1.05, 11.6), (0.36, 0.36, 0.5)))

    return _p(c, "Ice Yard Derrick", build)


# ------------------------------------------------------------------ the ice house


def ice_house(c):
    """The ice house: a timber lean-to, its roof boarded and snowed over, open on its
    front; inside, cut blocks stacked in courses with straw packed between and over them;
    a loading deck along its front with a ramp up from the pond side, a pair of tongs
    hung on a post."""
    w, d, h = 10.0, 6.0, 5.2

    def build(P, bm):
        # Posts, the roof beams, the boarded roof falling to the back, snow on it.
        for x in (-w / 2, -w / 6, w / 6, w / 2):
            P.add(TIMBER, lambda x=x: cuboid(bm, (x, 0.0, h / 2), (0.35, 0.35, h)))
            P.add(TIMBER, lambda x=x: cuboid(bm, (x, -d, (h - 1.6) / 2), (0.35, 0.35, h - 1.6)))
            P.add(TIMBER, lambda x=x: _beam(bm, (x, 0.4, h), (x, -d - 0.4, h - 1.6), 0.3))
        P.add(PLANK, lambda: _beam(bm, (0.0, 0.6, h + 0.25), (0.0, -d - 0.6, h - 1.35), 0.2, w + 0.8))
        P.add(SNOW, lambda: _beam(bm, (0.0, 0.5, h + 0.5), (0.0, -d - 0.5, h - 1.1), 0.35, w + 0.6))
        # Back and side walls, boards.
        P.add(PLANK, lambda: cuboid(bm, (0.0, -d, (h - 1.6) / 2), (w, 0.2, h - 1.6)))
        for sx in (-1, 1):
            P.add(PLANK, lambda sx=sx: cuboid(bm, (sx * w / 2, -d / 2, (h - 1.6) / 2), (0.2, d, h - 1.6)))
        # The stacks: blocks in courses, straw between and over.
        for row in range(3):
            for k in range(6):
                for j in range(2):
                    x = -w / 2 + 1.0 + k * 1.6 + (0.4 if row % 2 else 0.0)
                    if x > w / 2 - 0.8:
                        continue
                    P.add(ICE, lambda x=x, j=j, row=row: cuboid(bm, (x, -1.6 - j * 1.9, 0.75 + row * 1.35), (1.4, 1.6, 1.15)))
            P.add(STRAW, lambda row=row: cuboid(bm, (0.0, -2.5, 1.38 + row * 1.35), (w - 0.6, 4.2, 0.18)))
        P.add(STRAW, lambda: blob(bm, (-1.0, -2.5, 4.4), 2.6, sx=1.5, sy=0.8, sz=0.25))
        # The loading deck along the front, a ramp up to it from the right.
        P.add(DECK, lambda: cuboid(bm, (0.0, 1.4, 0.55), (w + 0.8, 2.4, 0.3)))
        for x in (-w / 2, 0.0, w / 2):
            P.add(TIMBER, lambda x=x: cuboid(bm, (x, 2.5, 0.2), (0.3, 0.3, 0.7)))
        P.add(DECK, lambda: _beam(bm, (w / 2 + 0.4, 1.4, 0.55), (w / 2 + 4.6, 1.4, -0.1), 0.25, 2.2))
        # Tongs on a post, a pike pole leant on the wall.
        P.add(TIMBER, lambda: cuboid(bm, (-w / 2 - 0.8, 1.6, 1.2), (0.25, 0.25, 2.4)))
        for sx in (-1, 1):
            P.add(IRON, lambda sx=sx: _beam(bm, (-w / 2 - 0.8, 1.85, 2.2), (-w / 2 - 0.8 + sx * 0.35, 1.9, 1.2), 0.07))
        P.add(TIMBER, lambda: _beam(bm, (w / 2 + 0.2, 0.3, 0.0), (w / 2 + 0.3, 0.6, 4.2), 0.08))
        P.add(IRON, lambda: _crystal(bm, (w / 2 + 0.3, 0.6, 4.2), (0.02, 0.07, 1.0), 0.5, 0.06, n=4))
        # A lamp on the corner post.
        P.add(IRON, lambda: cuboid(bm, (-w / 2, 0.5, h - 0.8), (0.08, 0.9, 0.08)))
        P.add(LAMP, lambda: cuboid(bm, (-w / 2, 0.95, h - 1.2), (0.36, 0.36, 0.5)))

    return _p(c, "Ice House", build)


# ------------------------------------------------------------------ smaller kit


def sledge(c, k):
    """A work sledge: heavy runners, a slatted bed, its harness poles out front, blocks
    roped on (or empty)."""

    def build(P, bm):
        for sy in (-1, 1):
            P.add(TIMBER, lambda sy=sy: cuboid(bm, (0, sy * 0.85, 0.2), (4.2, 0.22, 0.4)))
            P.add(IRON, lambda sy=sy: cuboid(bm, (0, sy * 0.85, 0.02), (4.2, 0.26, 0.06)))
            P.add(TIMBER, lambda sy=sy: _beam(bm, (2.1, sy * 0.85, 0.2), (2.6, sy * 0.85, 0.7), 0.2))
            P.add(TIMBER, lambda sy=sy: _beam(bm, (2.4, sy * 0.6, 0.5), (5.2, sy * 0.35, 0.7), 0.12))
        for k2 in range(6):
            P.add(PLANK, lambda k2=k2: cuboid(bm, (-1.8 + k2 * 0.72, 0, 0.48), (0.55, 2.0, 0.12)))
        P.add(TIMBER, lambda: cuboid(bm, (5.2, 0, 0.7), (0.15, 0.9, 0.12)))
        if k % 2 == 0:
            for j, (x, z) in enumerate(((-1.0, 1.15), (0.6, 1.15), (-0.2, 2.35))):
                P.add(ICE, lambda x=x, z=z, j=j: cuboid(bm, (x, 0, z), (1.4, 1.5, 1.15), rot=0.05 * j))
            _rope(P, bm, (-1.9, 0.9, 0.5), (-0.2, 0.8, 2.95), 0.05)
            _rope(P, bm, (1.5, 0.9, 0.5), (-0.2, 0.8, 2.95), 0.05)
        else:
            P.add(STRAW, lambda: cuboid(bm, (0, 0, 0.62), (3.6, 1.7, 0.2)))

    return _p(c, "Ice Sledge %d" % (k % 2), build)


def brazier(c):
    """An iron fire basket on legs, logs burning in it, two log benches either side and a
    pile of split wood."""

    def build(P, bm):
        for k in range(3):
            a = k * math.tau / 3
            P.add(IRON, lambda a=a: _beam(bm, (math.cos(a) * 0.9, math.sin(a) * 0.9, 0.0), (math.cos(a) * 0.55, math.sin(a) * 0.55, 1.0), 0.09))
        _cyl(P, bm, IRON, 0, 0, 0.9, 1.5, 0.45, 0.75)
        for k in range(4):
            a = k * math.pi / 4
            P.add(LOGS, lambda a=a: _beam(bm, (math.cos(a) * -0.55, math.sin(a) * -0.55, 1.35), (math.cos(a) * 0.55, math.sin(a) * 0.55, 1.45), 0.2))
        P.add(FIRE, lambda: _crystal(bm, (0, 0, 1.4), (0, 0, 1), 1.1, 0.45, n=5))
        for sy in (-1, 1):
            P.add(LOGS, lambda sy=sy: _beam(bm, (-1.4, sy * 2.0, 0.3), (1.4, sy * 2.2, 0.3), 0.55))
        for j in range(5):
            P.add(LOGS, lambda j=j: _beam(bm, (2.4, -0.6 + j * 0.3, 0.2 + (j % 2) * 0.25), (3.3, -0.6 + j * 0.3, 0.2 + (j % 2) * 0.25), 0.25))

    return _p(c, "Ice Yard Brazier", build)


def tool_bench(c):
    """The tool bench: a heavy trestle table, ice saws hung over it on a rack (long blades,
    T handles), an axe in a block, and the grindstone in its frame beside it."""

    def build(P, bm):
        P.add(TIMBER, lambda: cuboid(bm, (0, 0, 0.95), (3.4, 1.0, 0.18)))
        for sx in (-1, 1):
            P.add(TIMBER, lambda sx=sx: cuboid(bm, (sx * 1.4, 0, 0.45), (0.2, 0.9, 0.9)))
        P.add(TIMBER, lambda: cuboid(bm, (0, -0.55, 2.0), (3.6, 0.15, 0.15)))
        for sx in (-1, 1):
            P.add(TIMBER, lambda sx=sx: cuboid(bm, (sx * 1.7, -0.55, 1.2), (0.15, 0.15, 2.4)))
        for k in range(3):
            x = -1.0 + k * 1.0
            P.add(IRON, lambda x=x: cuboid(bm, (x, -0.5, 1.15), (0.05, 0.3, 1.6)))  # (the blade)
            P.add(TIMBER, lambda x=x: cuboid(bm, (x, -0.5, 1.98), (0.6, 0.12, 0.12)))  # (the T)
        P.add(LOGS, lambda: cuboid(bm, (2.6, 0.4, 0.4), (0.8, 0.8, 0.8)))
        P.add(TIMBER, lambda: _beam(bm, (2.6, 0.4, 0.8), (2.9, 0.5, 1.5), 0.08))
        P.add(IRON, lambda: cuboid(bm, (2.6, 0.43, 0.88), (0.06, 0.4, 0.22)))
        # The grindstone.
        for sy in (-1, 1):
            P.add(TIMBER, lambda sy=sy: cuboid(bm, (-2.7, sy * 0.35, 0.55), (0.18, 0.12, 1.1)))
        for a in (0.0, math.pi / 4):  # (the wheel: an octagon of two squares)
            P.add(STONE, lambda a=a: cuboid(bm, (-2.7, 0.0, 1.05), (0.9, 0.3, 0.9), tilt=(0.0, a)))
        P.add(IRON, lambda: _beam(bm, (-2.7, 0.15, 1.05), (-2.7, 0.7, 1.05), 0.06))
        P.add(IRON, lambda: _beam(bm, (-2.7, 0.7, 1.05), (-2.7, 0.7, 0.75), 0.06))

    return _p(c, "Ice Yard Bench", build)


def lantern_pole(c):
    def build(P, bm):
        P.add(TIMBER, lambda: cuboid(bm, (0, 0, 2.2), (0.25, 0.25, 4.4)))
        P.add(TIMBER, lambda: _beam(bm, (0, 0, 4.2), (0, 0.9, 4.2), 0.15))
        P.add(IRON, lambda: cuboid(bm, (0, 0.85, 3.9), (0.04, 0.04, 0.5)))
        P.add(LAMP, lambda: cuboid(bm, (0, 0.85, 3.45), (0.38, 0.38, 0.55)))
        P.add(IRON, lambda: cuboid(bm, (0, 0.85, 3.75), (0.5, 0.5, 0.08)))

    return _p(c, "Ice Yard Lantern Pole", build)


def stuck_tools(c, k):
    """An ice saw standing in its cut, or a pike pole and tongs, left mid-job."""

    def build(P, bm):
        if k % 2 == 0:
            P.add(IRON, lambda: cuboid(bm, (0, 0, 0.6), (0.05, 0.35, 1.8), tilt=(0.12, 0.0)))
            P.add(TIMBER, lambda: cuboid(bm, (0, -0.12, 1.55), (0.7, 0.12, 0.12)))
        else:
            P.add(TIMBER, lambda: _beam(bm, (0, 0, -0.3), (0.5, 0.2, 3.2), 0.08))
            P.add(IRON, lambda: _crystal(bm, (0.5, 0.2, 3.2), (0.14, 0.06, 1.0), 0.4, 0.06, n=4))
            for sx in (-1, 1):
                P.add(IRON, lambda sx=sx: _beam(bm, (1.2, 0.0, 0.02), (1.2 + sx * 0.4, 0.5, 0.02), 0.06))

    return _p(c, "Ice Yard Tools %d" % (k % 2), build)


def dragon_commission(c):
    """Rimefang's commission: a great block of glacier ice, its front roughed out into a
    dragon's head (the snout and jaw cut, a brow ridge, one horn sweeping back, the other
    still in the block), under scaffolding: poles, two walkways, ladders, a hoist arm."""

    def build(P, bm):
        # The block, its back still square.
        P.add(STONE, lambda: cuboid(bm, (0, 0, 0.4), (7.0, 7.0, 0.8)))
        P.add(ICE, lambda: cuboid(bm, (0, -0.8, 4.6), (5.6, 4.4, 7.6)))
        # The head coming out of its front: skull, brow, snout, jaw, nostrils, an eye.
        P.add(ICE, lambda: _wedge(bm, -2.2, 2.2, 1.4, 2.6, 2.0, 6.6, 7.4))
        P.add(ICE, lambda: _wedge(bm, -1.5, 1.5, 2.6, 5.6, 3.4, 4.6, 6.0))
        P.add(ICE, lambda: _wedge(bm, -1.3, 1.3, 2.6, 5.0, 2.2, 3.0, 3.4))
        for sx in (-1, 1):
            P.add(BLUE, lambda sx=sx: cuboid(bm, (sx * 0.6, 5.5, 4.3), (0.35, 0.2, 0.25)))
            P.add(ICE, lambda sx=sx: cuboid(bm, (sx * 1.6, 2.3, 6.4), (1.2, 1.4, 0.7), tilt=(0.25, sx * 0.2)))
            P.add(BLUE, lambda sx=sx: cuboid(bm, (sx * 1.55, 2.6, 5.6), (0.6, 0.15, 0.35)))
            for j in range(3):
                P.add(ICE, lambda sx=sx, j=j: _crystal(bm, (sx * 0.9, 3.0 + j * 0.8, 3.0), (0, 0, -1), 0.6, 0.14, n=4))
        P.add(ICE, lambda: _crystal(bm, (-1.6, 1.0, 7.0), (-0.3, -0.9, 0.5), 4.0, 0.5, n=5))
        # Ice chips in heaps round its foot.
        for k, (x, y) in enumerate(((2.8, 3.0), (-3.0, 2.2), (1.2, -3.4))):
            P.add(BLUE, lambda x=x, y=y: blob(bm, (x, y, 0.8), 0.9, sx=1.4, sy=1.0, sz=0.35))
        # The scaffold: poles round it, walkways at 3 and 6 m, ladders, a hoist arm.
        pts = [(-3.4, -3.4), (3.4, -3.4), (3.4, 3.0), (-3.4, 3.0), (0.0, 3.6)]
        for x, y in pts[:4]:
            P.add(TIMBER, lambda x=x, y=y: cuboid(bm, (x, y, 4.6), (0.22, 0.22, 9.2)))
        for z in (3.0, 6.2):
            P.add(DECK, lambda z=z: cuboid(bm, (3.4, -0.2, z), (1.0, 6.8, 0.15)))
            P.add(DECK, lambda z=z: cuboid(bm, (-3.4, -0.2, z), (1.0, 6.8, 0.15)))
            P.add(DECK, lambda z=z: cuboid(bm, (0.0, -3.4, z), (6.8, 1.0, 0.15)))
            for y in (-3.4, 3.0):
                P.add(TIMBER, lambda z=z, y=y: cuboid(bm, (0, y, z + 1.0), (7.0, 0.1, 0.1)))
        for sx in (-1, 1):
            P.add(TIMBER, lambda sx=sx: _beam(bm, (sx * 3.9, 2.2, 0.0), (sx * 3.9, 1.6, 6.2), 0.1, 0.8))
        P.add(TIMBER, lambda: _beam(bm, (3.4, 3.0, 9.0), (1.0, 4.6, 9.4), 0.2))
        _rope(P, bm, (1.0, 4.6, 9.3), (1.0, 4.6, 6.0), 0.05)
        P.add(IRON, lambda: cuboid(bm, (1.0, 4.6, 5.9), (0.3, 0.3, 0.3)))

    return _p(c, "Ice Yard Commission", build)


# ------------------------------------------------------------------ the pond


def pond(c, x, y, r, z):
    """The cutting pond: its ice (drivable), a grid of saw cuts scored over it, and its
    cut half: dark open water with blocks floating, a floating line of them being poled
    to the derrick."""
    c.disc("Ice Yard Pond", x, y, r, z, c.lib("river_ice", "ice"), coll="Village", role="both", n=36, wobble=0.04, seed=3)

    def build(P, bm):
        # The open water, on the pond's east half (a channel along +X).
        P.add(WATER, lambda: cuboid(bm, (r * 0.45, 0.0, 0.03), (r * 0.9, r * 0.9, 0.04)))
        for k, (bx, by) in enumerate(((0.3, -0.4), (0.4, 0.3), (0.62, -0.1), (0.75, 0.32), (0.55, 0.62), (0.82, -0.45))):
            P.add(ICE, lambda bx=bx, by=by, k=k: cuboid(bm, (r * bx, r * by, 0.18), (1.5, 1.3, 0.5), rot=0.25 * k))
        # The saw cuts: a grid over the west half, dark, a hair above the ice.
        for k in range(-3, 4):
            P.add(CUT, lambda k=k: cuboid(bm, (-r * 0.45, k * 1.6, 0.04), (r * 0.9, 0.12, 0.03)))
        for k in range(0, 6):
            P.add(CUT, lambda k=k: cuboid(bm, (-k * 1.5 - 0.1, 0.0, 0.04), (0.12, r * 1.15, 0.03)))
        # Snow heaped round the edge where it's been shovelled off.
        for k in range(9):
            a = k * math.tau / 9 + 0.2
            P.add(SNOW, lambda a=a, k=k: blob(bm, (math.cos(a) * (r + 0.6), math.sin(a) * (r + 0.6), 0.1), 1.2 + 0.3 * (k % 3),
                                               sx=1.6, sy=0.9, sz=0.35))

    proto = _p(c, "Ice Yard Pond Works", build)
    c.place(proto, x, y, z, rot=0.0, coll="Village", role="visual")


# ------------------------------------------------------------------ placing it


def build(c, ground, taken):
    """The yard, round SL.HOLLOW_GARDEN."""
    gx, gy, gr = SL.HOLLOW_GARDEN
    z0 = ground(gx, gy)
    pr = 8.0
    pond(c, gx, gy, pr, z0 + 0.06)
    taken.add(gx, gy, pr + 1.0)

    def put(proto, dx, dy, rot, r, coll="Village"):
        x, y = gx + dx, gy + dy
        z = min(ground(x + ox, y + oy) for ox in (-1.5, 0.0, 1.5) for oy in (-1.5, 0.0, 1.5))
        c.place(proto, x, y, z - 0.1, rot=rot, coll=coll)
        taken.add(x, y, r)
        return x, y, z

    # The derrick on the pond's north-west, its boom over the water.
    x, y, z = put(derrick(c), -9.5, 6.5, math.atan2(-6.5, 9.5) - math.pi / 2, 5.0)
    g = c.game(x, y, z + 11.6)
    c.entity("lantern", x=g[0], y=g[1], z=g[2])
    # The ice house north-east, its deck to the pond.
    x, y, z = put(ice_house(c), 8.0, 13.0, math.atan2(-13.0, -8.0) - math.pi / 2, 6.5)
    # Sledges on the yard's east and south, harness poles out.
    put(sledge(c, 0), 13.5, 1.0, 0.4, 3.0)
    put(sledge(c, 1), 10.0, -9.5, -0.6, 3.0)
    put(sledge(c, 2), -2.0, 13.0, 2.6, 3.0)
    # The brazier and benches south-west, where the cutters warm up.
    x, y, z = put(brazier(c), -11.5, -6.0, 0.3, 3.5)
    g = c.game(x, y, z + 1.6)
    c.entity("campfire", x=g[0], y=g[1], z=g[2])
    # The tool bench and grindstone south.
    put(tool_bench(c), 1.0, -11.5, 0.05, 3.0)
    # Rimefang's commission, west, under its scaffold.
    put(dragon_commission(c), -15.5, 4.0, -math.pi / 2 - 0.2, 5.5)
    # Saws and pike poles left in the pond's cuts.
    for k, (dx, dy, rot) in enumerate(((-3.5, 1.6, 0.0), (-5.0, -1.6, 1.57), (-2.0, -3.2, 0.4), (-6.2, 3.0, -0.6))):
        c.place(stuck_tools(c, k), gx + dx, gy + dy, z0 + 0.1, rot=rot, coll="Props", role="visual")
    # Lantern poles round the yard.
    for k, a in enumerate((0.3, 1.5, 2.6, 3.7, 4.8, 5.8)):
        x, y = gx + 18.0 * math.cos(a), gy + 18.0 * math.sin(a)
        if not taken.clear(x, y, 1.0):
            continue
        z = ground(x, y)
        c.place(lantern_pole(c), x, y, z - 0.1, rot=a + math.pi / 2, coll="Village")
        taken.add(x, y, 1.0)
        cr, sr = math.cos(a + math.pi / 2), math.sin(a + math.pi / 2)
        g = c.game(x - 0.85 * sr, y + 0.85 * cr, z + 3.45)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
    # The cutters, at work about the pond.
    g = c.game(gx + 2.0, gy - 8.0, z0)
    c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=10.0, n=6, folk="snow",
             heading=0.0)
