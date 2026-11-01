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
from keep_props import _p as _kp_p
from ice_homes import _fin, _log
from props import blob, cuboid, loft, ring, tube

ICE = "glacier_ice"
BLUE = "icefall_blue"
CLEAR_ = "river_ice"
CUT = "cavern_ice"  # (the saw cuts, dark)
WATER = "frost_pool"
TIMBER = "timber_beam"
PLANK = "weathered_timber"
DECK = "plank_deck"
ROPE = "rope_rail"
IRON = "keep_iron"
STRAW = "thatch"
STONE = "frost_stone"
LOGS = "log_sawn"  # (each sawn end a whole end grain: keep_props.disc_fit)
LAMP = "lantern_amber"
SNOW = "snow_ground"
FIRE = "keep_flame"


def _p(c, name, build, fit=None):
    """keep_props._p, its logs' sawn ends each a whole end grain."""
    return _kp_p(c, name, build, fit=fit, discs=(LOGS,))


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
        # (its pivot on a crossbeam between the legs: Blake, review-snow_region 4, "not
        # connected to the base of the hoist")
        P.add(TIMBER, lambda: _beam(bm, (-3.05, -0.82, 4.0), (3.05, -0.82, 4.0), 0.45))
        for sx in (-1, 1):
            P.add(IRON, lambda sx=sx: cuboid(bm, (sx * 0.4, -0.5, 4.0), (0.12, 0.9, 0.8)))
        foot = (0.0, -0.45, 4.0)
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
            _rope(P, bm, (sx * 0.2, -0.3, H - 0.8), (sx * 6.0, -8.0, 0.4), 0.06)
            P.add(TIMBER, lambda sx=sx: cuboid(bm, (sx * 6.0, -8.0, 0.3), (0.3, 0.3, 1.0), tilt=(0.3, 0.0)))
        # (No lantern up the mast: Blake, review-snow_region 6, "it is just floating".)

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
        P.add(PLANK, lambda: _beam(bm, (0.0, 0.6, h + 0.25), (0.0, -d - 0.6, h - 1.35), w + 0.8, 0.2))
        P.add(SNOW, lambda: _beam(bm, (0.0, 0.5, h + 0.5), (0.0, -d - 0.5, h - 1.1), w + 0.6, 0.35))
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
        P.add(DECK, lambda: _beam(bm, (w / 2 + 0.4, 1.4, 0.55), (w / 2 + 4.6, 1.4, -0.1), 2.2, 0.25))
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
            for sy in (-1, 1):  # (roped over both sides: review-snow_region 4)
                _rope(P, bm, (-1.9, sy * 0.9, 0.5), (-0.2, sy * 0.8, 2.95), 0.05)
                _rope(P, bm, (1.5, sy * 0.9, 0.5), (-0.2, sy * 0.8, 2.95), 0.05)
            _rope(P, bm, (-0.2, -0.8, 2.95), (-0.2, 0.8, 2.95), 0.05)
        else:
            P.add(STRAW, lambda: cuboid(bm, (0, 0, 0.62), (3.6, 1.7, 0.2)))

    return _p(c, "Ice Sledge %d" % (k % 2), build)


def brazier(c):
    """The fire the cutters warm up at (Blake, review-snow_region 4: "redo the fire and the
    wood in it"): an iron basket on three legs, split logs crossed in it and burning,
    tongues of flame of every height, embers; two log benches on stub stumps either
    side, and a stack of split wood."""

    def build(P, bm):
        for k in range(3):
            a = k * math.tau / 3
            P.add(IRON, lambda a=a: _beam(bm, (math.cos(a) * 0.95, math.sin(a) * 0.95, 0.0), (math.cos(a) * 0.6, math.sin(a) * 0.6, 1.0), 0.09))
        _cyl(P, bm, IRON, 0, 0, 0.9, 1.0, 0.5, 0.55, n=12)
        for k in range(12):  # (the basket's bars)
            a = k * math.tau / 12
            P.add(IRON, lambda a=a: _beam(bm, (math.cos(a) * 0.55, math.sin(a) * 0.55, 1.0), (math.cos(a) * 0.82, math.sin(a) * 0.82, 1.6), 0.05))
        P.add(IRON, lambda: loft(bm, [ring(bm, (0, 0), 0.84, 1.56, 16), ring(bm, (0, 0), 0.84, 1.66, 16)], cap_top=False))
        # The logs, crossed, burning.
        for k in range(4):
            a = k * math.pi / 4 + 0.2
            ca, sa = math.cos(a), math.sin(a)
            z = 1.18 + 0.16 * (k % 2)
            _log(P, bm, (-ca * 0.62, -sa * 0.62, z), (ca * 0.62, sa * 0.62, z + 0.12), 0.11, k)
        P.add("fire_glow", lambda: blob(bm, (0, 0, 1.15), 0.45, sx=1.0, sy=1.0, sz=0.3, subdiv=2))
        for k, (dx, dy, hh, r) in enumerate(((0.0, 0.0, 1.5, 0.32), (0.25, 0.1, 1.0, 0.22), (-0.22, 0.18, 0.85, 0.2),
                                             (0.05, -0.28, 1.1, 0.22), (-0.15, -0.12, 0.7, 0.16))):
            P.add(FIRE, lambda dx=dx, dy=dy, hh=hh, r=r, k=k: _fin(bm, (dx, dy, 1.3), (dx * 0.4 + 0.05 * (k % 2), dy * 0.4, hh), r))
        # The benches: a half log on two stubs each side.
        for sy in (-1, 1):
            for sx in (-1, 1):
                P.add("giant_bark", lambda sx=sx, sy=sy: tube(bm, [(sx * 0.9, sy * 2.1, 0.0), (sx * 0.9, sy * 2.1, 0.32)], 0.22, n=8))
            _log(P, bm, (-1.5, sy * 2.1, 0.5), (1.5, sy * 2.15, 0.5), 0.22, 3 + sy)
        # Split wood, stacked.
        for row in range(2):
            for j in range(3 - row):
                y0 = -0.35 + (j + row * 0.5) * 0.34
                _log(P, bm, (2.3, y0, 0.15 + row * 0.3), (3.2, y0, 0.15 + row * 0.3), 0.15, j + row)

    return _p(c, "Ice Yard Brazier", build)


def _saw(P, bm, x, y, z, L=1.7):
    """An ice saw hung blade down (Blake, review-snow_region 4: "make this blade look a
    little nicer"): a long blade tapering to its tip, teeth down one edge, an iron ferrule,
    a wooden T handle."""

    def blade():
        t = 0.03
        pts = [(x - 0.17, z), (x + 0.17, z), (x + 0.07, z - L), (x - 0.06, z - L)]
        f = [bm.verts.new((px, y + t, pz)) for px, pz in pts]
        b_ = [bm.verts.new((px, y - t, pz)) for px, pz in pts]
        bm.faces.new(f)
        bm.faces.new(list(reversed(b_)))
        for k in range(4):
            j = (k + 1) % 4
            bm.faces.new((b_[k], b_[j], f[j], f[k]))

    P.add(IRON, blade)
    n = 16
    for k in range(n):  # (its teeth, down its right edge)
        u = (k + 0.5) / n
        ex = x + 0.17 + (0.07 - 0.17) * u
        ez = z - L * u
        P.add(IRON, lambda ex=ex, ez=ez: _fin(bm, (ex - 0.01, y, ez), (0.07, 0.0, -0.03), 0.025, n=4))
    P.add(IRON, lambda: cuboid(bm, (x, y, z + 0.08), (0.36, 0.1, 0.16)))
    P.add(TIMBER, lambda: tube(bm, [(x, y, z + 0.14), (x, y, z + 0.55)], 0.06, n=8))
    P.add(TIMBER, lambda: tube(bm, [(x - 0.3, y, z + 0.6), (x + 0.3, y, z + 0.6)], 0.07, n=8))


def tool_bench(c):
    """The tool bench: a heavy trestle table, ice saws hung over it on a rack, the
    grindstone in its frame beside it."""

    def build(P, bm):
        P.add(TIMBER, lambda: cuboid(bm, (0, 0, 0.95), (3.4, 1.0, 0.18)))
        for sx in (-1, 1):
            P.add(TIMBER, lambda sx=sx: _beam(bm, (sx * 1.4, -0.4, 0.0), (sx * 1.3, 0.0, 0.88), 0.14))
            P.add(TIMBER, lambda sx=sx: _beam(bm, (sx * 1.4, 0.4, 0.0), (sx * 1.3, 0.0, 0.88), 0.14))
        P.add(TIMBER, lambda: cuboid(bm, (0, -0.55, 2.75), (3.6, 0.15, 0.15)))
        for sx in (-1, 1):
            P.add(TIMBER, lambda sx=sx: cuboid(bm, (sx * 1.7, -0.55, 1.4), (0.15, 0.15, 2.8)))
        for k in range(3):
            x = -1.0 + k * 1.0
            P.add(IRON, lambda x=x: cuboid(bm, (x, -0.55, 2.62), (0.05, 0.05, 0.15)))
            _saw(P, bm, x, -0.45, 2.45, L=1.3 + 0.15 * (k % 2))
        # The grindstone: a round stone in its frame, a crank.
        for sy in (-1, 1):
            P.add(TIMBER, lambda sy=sy: cuboid(bm, (-2.7, sy * 0.35, 0.55), (0.18, 0.12, 1.1)))
        P.add(STONE, lambda: tube(bm, [(-2.7, -0.15, 1.05), (-2.7, 0.15, 1.05)], 0.48, n=16))
        P.add(IRON, lambda: _beam(bm, (-2.7, 0.15, 1.05), (-2.7, 0.7, 1.05), 0.06))
        P.add(IRON, lambda: _beam(bm, (-2.7, 0.7, 1.05), (-2.7, 0.7, 0.75), 0.06))

    return _p(c, "Ice Yard Bench", build)


def stump(c):
    """A chopping stump (Blake, review-snow_region 4: "a nice looking stump with an axe
    stuck into it"): bark sides flaring into roots, a pale cut top with its rings, an axe
    bitten into it."""

    def build(P, bm):
        P.add("giant_bark", lambda: tube(bm, [(0, 0, -0.1), (0, 0, 0.12), (0, 0, 0.35), (0.02, 0, 0.7)], [0.72, 0.6, 0.5, 0.48], n=12))
        P.add(LOGS, lambda: loft(bm, [ring(bm, (0.02, 0), 0.47, 0.71, 12), ring(bm, (0.02, 0), 0.47, 0.72, 12)], cap_top=True))
        for k in range(5):
            a = k * math.tau / 5 + 0.4
            P.add("giant_bark", lambda a=a: _fin(bm, (math.cos(a) * 0.35, math.sin(a) * 0.35, 0.18),
                                                 (math.cos(a) * 0.75, math.sin(a) * 0.75, -0.2), 0.16, n=6))
        # The axe: its haft rising off the top at a slant, the head bitten in.
        P.add(TIMBER, lambda: tube(bm, [(0.05, 0.0, 0.78), (0.35, 0.1, 1.15), (0.62, 0.2, 1.5)], [0.05, 0.045, 0.05], n=8))

        def head():
            vs = [(-0.14, -0.04, 0.62), (0.2, -0.04, 0.62), (0.16, -0.04, 0.9), (-0.06, -0.04, 0.95),
                  (-0.14, 0.04, 0.62), (0.2, 0.04, 0.62), (0.16, 0.04, 0.9), (-0.06, 0.04, 0.95)]
            v = [bm.verts.new((x + 0.02, y, z)) for x, y, z in vs]
            for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
                bm.faces.new([v[i] for i in f])

        P.add(IRON, head)
        P.add(IRON, lambda: cuboid(bm, (0.08, 0.0, 0.92), (0.16, 0.12, 0.2), tilt=(0.0, -0.6)))
        # Chips about its foot.
        for k in range(6):
            a = k * 1.1
            P.add(PLANK, lambda a=a: cuboid(bm, (math.cos(a) * 0.9, math.sin(a) * 0.8, 0.03), (0.16, 0.08, 0.05), rot=a))

    return _p(c, "Ice Yard Stump", build)


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
            # An ice saw, the real thing (Blake, review-snow_region 6: "make this look more
            # like a saw"): its toothed blade down in the cut, the T handle up.
            _saw(P, bm, 0.0, 0.0, 1.15, L=1.7)
        else:
            P.add(TIMBER, lambda: _beam(bm, (0, 0, -0.3), (0.5, 0.2, 3.2), 0.08))
            P.add(IRON, lambda: _crystal(bm, (0.5, 0.2, 3.2), (0.14, 0.06, 1.0), 0.4, 0.06, n=4))
            for sx in (-1, 1):
                P.add(IRON, lambda sx=sx: _beam(bm, (1.2, 0.0, 0.02), (1.2 + sx * 0.4, 0.5, 0.02), 0.06))

    return _p(c, "Ice Yard Tools %d" % (k % 2), build)


def dragon_commission(c):
    """Rimefang's commission, near done (Blake, review-snow_region 4: "lets get a high
    fidelity sculpture here"): a dragon's head and neck rising out of what's left of its
    block, carved smooth: the neck's curve, the long skull, the snout and the jaw a little
    open with its teeth, brow ridges, swept-back horns, the crest of spikes down the
    neck; on a stepped stone plinth, a short scaffold still up one side."""

    def build(P, bm):
        P.add(STONE, lambda: cuboid(bm, (0, 0, 0.3), (5.6, 5.6, 0.6)))
        P.add(STONE, lambda: cuboid(bm, (0, 0, 0.8), (4.6, 4.6, 0.5)))
        P.add("rift_stone", lambda: cuboid(bm, (0, 2.32, 0.8), (3.0, 0.06, 0.3)))
        # What's left of the block, behind: rough, a step cut in it.
        P.add(ICE, lambda: cuboid(bm, (0, -1.3, 2.2), (3.4, 1.8, 2.4)))
        P.add(ICE, lambda: cuboid(bm, (0.3, -1.6, 3.8), (2.4, 1.2, 1.0), rot=0.1))
        # The neck, rising and curving forward.
        neck = [(0, -0.6, 1.0), (0, -0.4, 2.2), (0, 0.0, 3.4), (0, 0.5, 4.5), (0, 1.0, 5.3)]
        P.add(ICE, lambda: tube(bm, neck, [1.25, 1.15, 1.0, 0.88, 0.8], n=14))
        for k in range(5):  # (the throat's plates)
            p = neck[k]
            P.add(CLEAR_, lambda p=p, k=k: blob(bm, (p[0], p[1] + 0.75 - 0.05 * k, p[2] - 0.1), 0.42 - 0.03 * k, sx=1.4, sy=0.45, sz=0.8, subdiv=2))
        # The skull, the snout, the jaw.
        P.add(ICE, lambda: blob(bm, (0, 1.3, 5.75), 1.0, sx=0.85, sy=1.15, sz=0.8, subdiv=3))
        P.add(ICE, lambda: tube(bm, [(0, 1.9, 5.85), (0, 2.8, 5.75), (0, 3.6, 5.55)], [0.68, 0.55, 0.4], n=14))
        P.add(ICE, lambda: blob(bm, (0, 3.65, 5.55), 0.42, sx=0.9, sy=0.8, sz=0.75, subdiv=2))
        P.add(ICE, lambda: tube(bm, [(0, 1.6, 5.2), (0, 2.6, 5.0), (0, 3.4, 4.85)], [0.5, 0.4, 0.28], n=12))
        for sx in (-1, 1):
            for k in range(5):  # (teeth along the upper jaw, down)
                yy = 2.2 + k * 0.32
                P.add(CLEAR_, lambda sx=sx, yy=yy: _fin(bm, (sx * (0.36 - 0.03 * (yy - 2.2)), yy, 5.32 - 0.07 * (yy - 2.2)), (0.0, 0.03, -0.3), 0.06, n=6))
            # Nostrils, eyes under brow ridges, the cheek's spur.
            P.add(BLUE, lambda sx=sx: blob(bm, (sx * 0.2, 3.95, 5.72), 0.08, subdiv=2))
            P.add(BLUE, lambda sx=sx: blob(bm, (sx * 0.55, 1.95, 6.05), 0.16, sx=0.6, sy=1.0, sz=0.6, subdiv=2))
            P.add(ICE, lambda sx=sx: _fin(bm, (sx * 0.5, 1.8, 6.35), (sx * 0.15, 0.9, 0.12), 0.18, n=8))
            P.add(ICE, lambda sx=sx: _fin(bm, (sx * 0.75, 1.0, 5.4), (sx * 0.55, -0.4, -0.2), 0.2, n=8))
            # The horns, swept back and curling down.
            P.add(BLUE, lambda sx=sx: tube(bm, [(sx * 0.45, 0.9, 6.3), (sx * 0.75, 0.0, 6.9), (sx * 1.0, -1.0, 7.0),
                                                 (sx * 1.15, -1.8, 6.6), (sx * 1.2, -2.2, 6.0)], [0.34, 0.27, 0.19, 0.11, 0.02], n=10))
        # The crest of spikes down the back of the neck.
        for k in range(6):
            t = k / 5.0
            p = (0.0, 0.4 - 1.1 * t, 6.2 - 4.4 * t)
            P.add(BLUE, lambda p=p, k=k: _fin(bm, p, (0.0, -0.6 + 0.04 * k, 0.45 - 0.05 * k), 0.16 - 0.015 * k, n=8))
        # A short scaffold up one side: two poles, a deck at 3 m, a ladder.
        for y in (-1.6, 1.6):
            P.add(TIMBER, lambda y=y: cuboid(bm, (2.9, y, 2.4), (0.2, 0.2, 4.8)))
        P.add(DECK, lambda: cuboid(bm, (2.75, 0.0, 3.0), (1.0, 3.6, 0.15)))
        P.add(TIMBER, lambda: cuboid(bm, (3.25, 0.0, 4.0), (0.1, 3.4, 0.1)))
        for sy in (-1, 1):
            P.add(TIMBER, lambda sy=sy: _beam(bm, (3.7, 2.2 + sy * 0.3, 0.0), (3.35, 1.7 + sy * 0.3, 3.1), 0.08))
        for k in range(6):
            z = 0.45 + k * 0.48
            P.add(TIMBER, lambda z=z, k=k: _beam(bm, (3.68 - 0.054 * k * 0.9, 1.9 - 0.075 * k * 0.9, z), (3.68 - 0.054 * k * 0.9, 2.5 - 0.075 * k * 0.9, z), 0.06))
        P.add(IRON, lambda: cuboid(bm, (2.7, -1.0, 3.15), (0.5, 0.1, 0.05)))  # (a chisel left on the deck)

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
    # The ice house north-east, its deck to the pond.
    x, y, z = put(ice_house(c), 8.0, 13.0, math.atan2(-13.0, -8.0) - math.pi / 2, 6.5)
    # Sledges on the yard's east and south, harness poles out.
    put(sledge(c, 0), 13.5, 1.0, 0.4, 3.0)
    put(sledge(c, 1), 10.0, -9.5, -0.6, 3.0)
    put(sledge(c, 2), -2.0, 13.0, 2.6, 3.0)
    # The brazier and benches south-west, where the cutters warm up.
    x, y, z = put(brazier(c), -7.0, -14.0, 0.3, 3.5)
    g = c.game(x, y, z + 1.6)
    c.entity("campfire", x=g[0], y=g[1], z=g[2])
    # The tool bench and grindstone south.
    put(tool_bench(c), 5.0, -14.5, 0.05, 3.0)
    put(stump(c), 8.6, -12.2, 0.7, 1.2)
    # Rimefang's commission, west, under its scaffold.
    put(dragon_commission(c), -16.0, -6.0, math.atan2(6.0, 16.0) - math.pi / 2, 5.0)
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
