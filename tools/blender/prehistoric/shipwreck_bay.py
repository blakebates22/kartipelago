# Shipwreck Bay: the beach world's second course, painted (the Tropic Isles): a pirate
# cove at golden hour. The greybox's lap exactly (kept as shipwreck_bay_v2): the same
# roads, heights, surfaces, pier humps, mast jump, zippers and checkpoints; only the look
# is new (wreck_scenery.py, tropic_textures.py). The greybox replaced the Sunset Reef one
# (Blake, Oct 25: it played like a longer Coral Cove; this one has its own pieces).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/shipwreck_bay.py      (the bpy module)
#
# About 740 m, a lap near 28 s, a pirate cove:
#
#   1  The start along the cove's beach, east, and a right out onto the old pier.
#   2  The rolling-plank pier: south over the water on three humps (light off each one).
#   3  Round the pier head onto the sandbar, and THROUGH the wrecked galleon: in at the
#      bow's breach, the length of its hold, out of the stern.
#   4  Left onto the fallen mast: a long ramp up out of the water, and the jump off its
#      end over the river mouth onto the beach (miss it and you're put back past it).
#   5  Up the beach, west into the cove, the dip round Skull Rock, and back down to the
#      line.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp, smooth  # noqa: E402

import wreck_scenery  # noqa: E402

TRACK_ID = "shipwreck_bay"

START = (0.0, 0.0)
LAYOUT = [
    ("S", 36),  # 0  1: the start along the beach, east
    ("R", 26, 90),  # 1  out onto the pier, south
    ("S", 52),  # 2  2: the rolling-plank pier
    ("L", 26, 90),  # 3  round the pier head, east
    ("S", 10),  # 4  onto the sandbar
    ("S", 44),  # 5  3: through the galleon's hold
    ("S", 8),  # 6  out of the stern
    ("L", 28, 90),  # 7  north
    ("S", 48),  # 8  4: up the fallen mast
    ("S", 85),  # 9  the jump over the river mouth, and up the beach
    ("L", 30, 90),  # 10 5: west into the cove
    ("S", 14),  # 11
    ("L", 30, 55),  # 12 the dip round Skull Rock...
    ("R", 26, 110),  # 13
    ("L", 30, 55),  # 14 ...and out
    ("S", 38),  # 15 the cove street (closes the lap)
    ("L", 34, 90),  # 16 south
    ("S", 23),  # 17 (closes the lap)
    ("L", 30, 90),  # 18 the last bend onto the line
]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 15, 17, START, 0.0)
SEG = kit.segment_starts(PATH)
LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))


def seg_of(s):
    k = 0
    for i, d in SEG.items():
        if d <= s:
            k = max(k, i)
    return k


def _seg_point(i):
    return next(p for p in PATH if p[3] == i)


def _arc_centre(i):
    x, y, h, _ = _seg_point(i)
    sg = LAYOUT[i]
    a = math.radians(h + (90 if sg[0] == "L" else -90))
    return (x + sg[1] * math.cos(a), y + sg[1] * math.sin(a))


SKULL_ROCK = _arc_centre(13)

# ---------------------------------------------------------------- heights

WATER_Z = 0.0
HEIGHT = {0: 2.0, 1: 2.0, 2: 3.4, 3: 3.4, 4: 2.8, 5: 2.6, 6: 2.6, 7: 2.6, 8: 2.8, 9: 3.8, 10: 4.6, 11: 5.0, 12: 5.4,
          13: 5.4, 14: 5.2, 15: 4.8, 16: 4.0, 17: 3.0, 18: 2.2}
# The hold: from the bow's breach to the stern's.
HULL = (SEG[4] + 4.0, SEG[6] + 4.0)
# The mast: up from the sandbar to its broken end, the lip; the river mouth's gap.
MAST_TOP = 8.0
LIP = SEG[9] + 6.0
LAND = LIP + 13.0
# The pier's rolling planks: three humps.
HUMPS = (3, 1.1)


def _base_z(d, seg):
    a, b = SEG[seg], SEG.get(seg + 1, LENGTH)
    t = (d - a) / max(1e-6, b - a)
    z0, z1 = HEIGHT[seg], HEIGHT.get(seg + 1, HEIGHT[0])
    if seg == 8 or (seg == 9 and d <= LIP):
        # Up the mast, steadily, to its end.
        u = (d - SEG[8]) / (LIP - SEG[8])
        return lerp(HEIGHT[8], MAST_TOP, u)
    if seg == 9:
        # Past the lip: the beach, gently up towards the cove.
        u = (d - LIP) / max(1e-6, SEG[10] - LIP)
        return lerp(3.6, HEIGHT[10], smooth(u))
    z = lerp(z0, z1, smooth(t))
    if seg == 2:
        n, h = HUMPS
        z += h * math.sin(t * math.pi * n) ** 2
    return z


road_z = kit.with_jumps(_base_z, seg_of, [(LIP, LAND, 1.0, 0.7)])


def road_w(d, seg):
    if seg == 0 or d < 30:
        return 18.0
    if seg in (2,):
        return 14.0  # the pier
    if seg in (4, 5, 6):
        return 13.0  # the hold
    if seg == 8 or (seg == 9 and d < LIP):
        return 13.0  # the mast
    return 16.0


ROUTE, SHARP, LOOPS = kit.route_with_loops(PATH, LAYOUT, road_z, every=6.0, width=road_w)
TO_ROAD, TO_PLAN = kit.along(PATH, road_z)

# ---------------------------------------------------------------- the land


def _plan_point(d):
    t = 0.0
    for a, b in zip(PATH, PATH[1:]):
        t += math.hypot(b[0] - a[0], b[1] - a[1])
        if t >= d:
            return b
    return PATH[-1]


_gap = _plan_point((LIP + LAND) / 2)
RIVER_Y = _gap[1]
_p4 = _seg_point(4)
_p7 = _seg_point(7)
# The sandbar the galleon lies on (a rounded box), and the river mouth: from inland, east
# under the jump, out to sea.
BAR = (_p4[0] - 12.0, _p7[0] + 14.0, _p4[1] - 22.0, _p4[1] + 34.0)
RIVER = [(_gap[0] - 120.0, RIVER_Y + 8.0), (_gap[0] - 40.0, RIVER_Y + 2.0), (_gap[0] + 60.0, RIVER_Y)]
RIVER_HALF = 7.0


def sea_d(x, y):
    """How far out to sea (negative: on land): south of the cove's beach, east of it."""
    south = (-14.0 + 2.5 * math.sin(x / 23.0)) - y
    east = x - (_gap[0] + 24.0 + 3.0 * math.sin(y / 19.0))
    return max(south, east)


def bar_d(x, y):
    """Distance inside the sandbar (positive inside)."""
    x0, x1, y0, y1 = BAR
    return min(x - x0, x1 - x, y - y0, y1 - y)


def _seg_d(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - a[0] - t * dx, py - a[1] - t * dy)


def river_d(x, y):
    return min(_seg_d(x, y, a, b) for a, b in zip(RIVER, RIVER[1:])) - RIVER_HALF


# The terrain's square; the land sinks into the sea over its outer 50 m (an island).
BOUNDS = (-160, 360, -260, 240)


def island_d(x, y):
    x0, x1, y0, y1 = BOUNDS
    return min(x - x0, x1 - x, y - y0, y1 - y)


_PTS = None


def near_road_z(x, y):
    global _PTS
    if _PTS is None:
        _PTS = []
        d = 0.0
        for i, p in enumerate(PATH):
            if i:
                d += math.hypot(p[0] - PATH[i - 1][0], p[1] - PATH[i - 1][1])
            if i % 2 == 0:
                _PTS.append((p[0], p[1], min(road_z(d, p[3]), 5.5)))
    best = None
    bd = 1e18
    for px, py, pz in _PTS:
        dd = (px - x) ** 2 + (py - y) ** 2
        if dd < bd:
            bd, best = dd, pz
    return best, math.sqrt(bd)


def natural(x, y):
    """Sand at about the road's level, dunes away from it, sloping into the sea; the
    sandbar out in the water; the river mouth cut through the beach."""
    z, d = near_road_z(x, y)
    h = z - 0.5 + 0.4 * math.sin(x / 17.0) * math.cos(y / 13.0) * smooth((d - 12) / 20)
    h += 3.0 * smooth((d - 25) / 40)
    s = sea_d(x, y)
    if s > -14:
        h = lerp(h, WATER_Z - 2.0 - 0.04 * max(0.0, s), smooth((s + 14) / 14))
    b = bar_d(x, y)
    if b > -10:
        h = lerp(h, 2.0 + 0.3 * math.sin(x / 9.0), smooth((b + 10) / 10))
    w = river_d(x, y)
    if w < 6:
        h = lerp(h, WATER_Z - 2.2, smooth((6 - w) / 6))
    e = island_d(x, y)
    if e < 50:
        h = lerp(h, WATER_Z - 3.0, smooth((50 - e) / 40))
    return h


def classify(c, n, info):
    if n.z < 0.6:
        return ("valley_cliff", "wall")
    if c.z < WATER_Z - 0.4:
        return ("wet_sand", "deep_water")
    if c.z < WATER_Z + 0.6:
        return ("wet_sand", "sand")
    # Soft sand off the road (cutting across mustn't pay); the shoulders stay sand.
    return ("beach_sand", "soft_sand")


def hull_shell(c, s0, s1, half=11.0, keel=-3.0, rail=6.5):
    """The galleon, plain: a shell round the hold (open at the breaches), its deck over
    the road (visual: the road runs under it)."""
    from course_kit import Vector, bmesh

    bm = bmesh.new()
    rings = []
    n = 12
    for k in range(n + 1):
        q = c.at(s0 + (s1 - s0) * k / n)
        t = k / n
        bulge = 0.75 + 0.25 * math.sin(math.pi * t)
        hw = half * bulge
        z0 = q.p.z
        prof = [(-hw * 0.55, keel), (-hw, z0 - q.p.z + 1.0), (-hw * 1.02, rail), (hw * 1.02, rail), (hw, 1.0), (hw * 0.55, keel)]
        rings.append([bm.verts.new(q.p + q.r * o + Vector((0, 0, dz))) for o, dz in prof])
    for a, b in zip(rings, rings[1:]):
        for i in range(len(a) - 1):
            bm.faces.new((a[i], b[i], b[i + 1], a[i + 1]))
    ob = c.mesh_object("Galleon", bm, "Props", "visual")
    c.assign(ob, c.lib("wood_planks", "wall"))
    # The hull's sides as walls, outside the hold's own barriers.
    bm = bmesh.new()
    for side in (-1, 1):
        rs = []
        for k in range(n + 1):
            q = c.at(s0 + (s1 - s0) * k / n)
            hw = half * (0.75 + 0.25 * math.sin(math.pi * k / n))
            rs.append([bm.verts.new(q.p + q.r * side * hw + Vector((0, 0, dz))) for dz in (keel, rail)])
        for a, b in zip(rs, rs[1:]):
            bm.faces.new((a[0], b[0], b[1], a[1]))
    side = c.mesh_object("Galleon Sides", bm, "Props", "both")
    c.assign(side, c.lib("wood_planks", "wall"))
    return ob


# The paint: each greybox material -> Shipwreck Bay's own (Course.lib keeps the old surface).
PAINT = {
    "beach_road": "wreck_road",
    "beach_sand": "wreck_sand",
    "wet_sand": "wreck_wet_sand",
    "sea_water": "wreck_sea",
    "wood_planks": "wreck_planks",
    "tiki_wood": "wreck_rail",
    "valley_cliff": "wreck_rock",
}


def main():
    kit.MAT_REMAP.clear()
    kit.MAT_REMAP.update(PAINT)
    c = kit.Course(TRACK_ID, "Shipwreck Bay", "shipwreck_bay")
    c.route(ROUTE, width=16.0, bank=6.0, sharp=SHARP)
    sand = ("beach_sand", "sand")
    planks = ("wood_planks", "road")
    tiki = ("tiki_wood", "wall")
    c.kinds = {
        "road": {"mat": "beach_road", "shoulder": 1.6, "shoulder_mat": sand},
        "pier": {"mat": "wood_planks", "surface": "road", "shoulder": 0.4, "shoulder_mat": planks, "barrier": 1.0,
                 "barrier_mat": tiki, "deck": 2.0, "deck_mat": ("wood_planks", "road"), "ground": False},
        "hold": {"mat": "wood_planks", "surface": "road", "shoulder": 0.4, "shoulder_mat": planks, "barrier": 1.4,
                 "barrier_mat": tiki},
        "mast": {"mat": "palm_bark", "surface": "road", "shoulder": 0.3, "shoulder_mat": planks, "deck": 2.0,
                 "deck_mat": ("palm_bark", "road"), "ground": False},
    }
    lip, land = TO_ROAD(LIP), TO_ROAD(LAND)
    h0, h1 = TO_ROAD(HULL[0]), TO_ROAD(HULL[1])
    m0 = TO_ROAD(SEG[8]) + 6

    def label(smp):
        s = smp.s
        if lip <= s <= land:
            return "gap"
        if m0 <= s < lip:
            return "mast"
        seg = seg_of(TO_PLAN(s))
        if h0 <= s <= h1:
            return "hold"
        if seg == 2 or (seg in (1, 3) and abs(TO_PLAN(s) - SEG[2] - (SEG[3] - SEG[2]) / 2) < (SEG[3] - SEG[2]) / 2 + 14):
            return "pier"
        return "road"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "mast":
            specials.append((s0, s1, "mast", {"lift": lambda u, n: 0.5 * max(0.0, (u - (n - 8)) / 8) ** 2}))
        elif k != "road":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "road", max_len=150.0))

    X0, X1, Y0, Y1 = BOUNDS
    ter = c.terrain("Sand", X0, X1, Y0, Y1, 4.0, natural, classify, near=9.0, fade=10.0, under=0.2)
    c.underfloor_flat("Seabed", X0, X1, Y0, Y1, 4.0, lambda x, y: natural(x, y) - 0.6, c.lib("wet_sand", "deep_water"))
    c.ribbon("Sea South", [(x, -1340.0) for x in range(-1600, 1801, 200)], 2700.0, WATER_Z, c.lib("sea_water"), role="visual", steps=2)
    c.ribbon("Sea East", [(1260.0, y) for y in range(-1400, 1401, 200)], 2200.0, WATER_Z, c.lib("sea_water"), role="visual", steps=2)
    c.ribbon("River", RIVER, 2 * RIVER_HALF + 4, WATER_Z, c.lib("sea_water"), role="visual", steps=2)

    # Piles under the pier and the mast, the galleon round the hold, Skull Rock.
    for piece in c.pieces:
        for kind, size, every in (("pier", 0.9, 7.0), ("mast", 1.2, 9.0)):
            if piece.name.endswith(kind):
                kit.clear_piers(c, piece, [ter], every=every, mat=("palm_bark", "wall"), size=size, inset=size + 0.6)
    hull_shell(c, h0 - 6.0, h1 + 4.0)
    rock = c.rock_mass("Skull Rock", SKULL_ROCK[0], SKULL_ROCK[1], 9.0, 8.0, 16.0, z0=0.0, n=10, seed=4)
    c.assign(rock, c.lib("valley_cliff", "wall"))

    c.start_line()
    S = lambda i: TO_ROAD(SEG[i])  # noqa: E731
    # Zippers: onto the pier, into the hold, up the mast (it takes you over the river).
    for at in (S(1) + 6, h0 - 8, m0 + 4):
        c.zipper(at, 0)
    for at, across in ((S(2) + 26, 0), (S(10) + 10, 3), (S(13) + 10, 0), (S(16) + 10, -3)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in ((S(0) + 24, -4, "red"), (S(0) + 24, 4, "blue"), (S(3) + 12, 0, "green"), (S(9) + 50, 0, "yellow"), (S(12) + 8, 0, "rainbow")):
        c.balloon(at, across, col)
    c.entity("respawn", **{"from": round(lip - 20, 1), "to": round(land + 4, 1), "at": round(land + 16, 1)})
    c.checkpoints(
        extra=[S(1) + 20, S(3) + 10, (h0 + h1) / 2, S(8) + 10, S(10) + 10, S(13) + 10, S(16) + 10],
        avoid=[(lip - 14, land + 8)],
        height=8.0,
    )

    wreck_scenery.build(c, sys.modules[__name__], ter)
    c.finish()
    print("lap", round(c.length, 1))


if __name__ == "__main__":
    main()
