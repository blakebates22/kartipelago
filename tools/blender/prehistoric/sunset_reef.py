# Sunset Reef: a greybox of the beach world's second course, to drive before it's dressed
# (?track=sunset_reef; working name). Coral Cove's feel, about half as long again.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/sunset_reef.py      (the bpy module)
#
# Blake (Oct 24): something like Coral Cove (he loved it) but about 50% longer: about
# 690 m, a lap around 28 s. Round a reef, anticlockwise:
#
#   1  The start straight along the beach, the sea off to the right.
#   2  A fast left sweeper, north up the beach (a zipper), and a quick right-left jog.
#   3  The pier: out along the reef's edge and a jump over the gap in it, the sea below.
#   4  Up onto the point and a hairpin round the sea stack.
#   5  A right-hander down off the point, and the long diagonal through the sea arch.
#   6  A left onto the west beach (a zipper), and the last drift onto the line.
#
# Plain shapes: sand, the sea, the lagoon, the tide pool and its channel, the sea stack
# and the arch. The look comes once the lap is fun.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp, smooth  # noqa: E402

TRACK_ID = "sunset_reef"

START = (0.0, 0.0)
LAYOUT = [
    ("S", 52),  # 0  1: the start straight along the beach, east (closes the lap)
    ("L", 45, 90),  # 1  2: the sweeper, north
    ("S", 45),  # 2  up the beach: a zipper
    ("R", 35, 60),  # 3  the jog...
    ("L", 35, 60),  # 4  ...back north
    ("S", 60),  # 5  3: the pier and the jump over the gap in the reef
    ("L", 28, 180),  # 6  4: the hairpin round the sea stack
    ("S", 25),  # 7
    ("R", 30, 70),  # 8  5: down off the point
    ("S", 80),  # 9  the diagonal through the sea arch
    ("L", 40, 70),  # 10 6: onto the west beach, south
    ("S", 47),  # 11 the west beach: a zipper (closes the lap)
    ("L", 45, 90),  # 12 the last drift onto the line
]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 0, 11, START, 0.0)
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


SEA_STACK = _arc_centre(6)

# ---------------------------------------------------------------- heights

WATER_Z = 0.0
HEIGHT = {0: 2.0, 1: 2.0, 2: 2.2, 3: 2.6, 4: 3.0, 5: 3.2, 6: 7.0, 7: 7.0, 8: 6.5, 9: 5.0, 10: 2.6, 11: 2.2, 12: 2.0}
# The jump over the gap in the reef, on the pier: (lip, landing) along the lap.
LIP = SEG[5] + 28.0
LAND = LIP + 10.0


def _base_z(d, seg):
    a, b = SEG[seg], SEG.get(seg + 1, LENGTH)
    t = (d - a) / max(1e-6, b - a)
    z0, z1 = HEIGHT[seg], HEIGHT.get(seg + 1, HEIGHT[0])
    if seg in (6, 7):
        return z0  # the point's hairpin is level
    return lerp(z0, z1, smooth(t))


road_z = kit.with_jumps(_base_z, seg_of, [(LIP, LAND, 2.5, 0.9)])


def road_w(d, seg):
    if seg == 0 or d < 30:
        return 18.0
    if seg == 5:
        return 15.0  # the pier
    return 16.0


ROUTE, SHARP, LOOPS = kit.route_with_loops(PATH, LAYOUT, road_z, every=6.0, width=road_w)
TO_ROAD, TO_PLAN = kit.along(PATH, road_z)

# ---------------------------------------------------------------- the land

# Where the jump crosses the channel (the boardwalk's line), and the lagoon inside the loop.
def _plan_point(d):
    """The layout's point d metres along it."""
    t = 0.0
    for a, b in zip(PATH, PATH[1:]):
        t += math.hypot(b[0] - a[0], b[1] - a[1])
        if t >= d:
            return b
    return PATH[-1]


_lip = _plan_point((LIP + LAND) / 2)
CHANNEL_Y = _lip[1]
CHANNEL_HALF = 4.5
LAGOON = (30.0, 62.0, 20.0)  # centre, radius
TIDE_POOL = (108.0, 150.0, 8.0)


def sea_d(x, y):
    """How far out to sea a point is (negative: on land). The sea is south of the beach
    and east of the pier's shore."""
    south = (-26.0 + 3.0 * math.sin(x / 23.0)) - y
    east = x - (152.0 + 3.0 * math.sin(y / 19.0))
    return max(south, east)


# The channel: from the lagoon north-east under the jump and out to the sea.
# The gap in the reef: from the tide pool east under the pier's jump and out to sea.
CHANNEL = [(TIDE_POOL[0] + 4.0, TIDE_POOL[1]), (_lip[0] - 6.0, CHANNEL_Y), (166.0, CHANNEL_Y + 3.0)]


def _seg_d(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - a[0] - t * dx, py - a[1] - t * dy)


def water_d(x, y):
    """Distance to the lagoon's or the channel's edge (negative: in the water)."""
    cx, cy, r = LAGOON
    lag = math.hypot(x - cx, y - cy) - r
    px, py, pr = TIDE_POOL
    lag = min(lag, math.hypot(x - px, y - py) - pr)
    chan = min(_seg_d(x, y, a, b) for a, b in zip(CHANNEL, CHANNEL[1:])) - CHANNEL_HALF
    return min(lag, chan)


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
                _PTS.append((p[0], p[1], road_z(d, p[3])))
    best = None
    bd = 1e18
    for px, py, pz in _PTS:
        dd = (px - x) ** 2 + (py - y) ** 2
        if dd < bd:
            bd, best = dd, pz
    return best, math.sqrt(bd)


def natural(x, y):
    """Sand at about the road's level (the headland rising with it), sloping down into
    the sea, the lagoon and the channel."""
    z, d = near_road_z(x, y)
    h = z - 0.5 + 0.4 * math.sin(x / 17.0) * math.cos(y / 13.0) * smooth((d - 12) / 20)
    # Dunes behind the beach, away from the road.
    h += 3.0 * smooth((d - 25) / 40)
    s = sea_d(x, y)
    if s > -14:
        h = lerp(h, WATER_Z - 2.0 - 0.04 * max(0.0, s), smooth((s + 14) / 14))
    w = water_d(x, y)
    if w < 6:
        h = lerp(h, WATER_Z - 2.2, smooth((6 - w) / 6))
    return h


def classify(c, n, info):
    if n.z < 0.6:
        return ("valley_cliff", "wall")
    if c.z < WATER_Z - 0.4:
        return ("wet_sand", "deep_water")
    if c.z < WATER_Z + 0.6:
        return ("wet_sand", "sand")
    # Soft sand off the road (Blake: cutting across it mustn't pay); the road's own
    # shoulders stay ordinary sand.
    return ("beach_sand", "soft_sand")


def main():
    c = kit.Course(TRACK_ID, "Sunset Reef (greybox)", "beach_party")
    c.route(ROUTE, width=16.0, bank=6.0, sharp=SHARP)
    sand = ("beach_sand", "sand")
    planks = ("wood_planks", "road")
    tiki = ("tiki_wood", "wall")
    c.kinds = {
        "road": {"mat": "beach_road", "shoulder": 1.6, "shoulder_mat": sand},
        "boardwalk": {"mat": "wood_planks", "surface": "road", "shoulder": 0.4, "shoulder_mat": planks, "barrier": 1.0,
                      "barrier_mat": tiki, "deck": 2.0, "deck_mat": ("wood_planks", "road"), "ground": False},
        "kicker": {"mat": "wood_planks", "surface": "road", "shoulder": 0.4, "shoulder_mat": planks, "deck": 2.0,
                   "deck_mat": ("wood_planks", "road"), "ground": False},
        "headland": {"mat": "beach_road", "shoulder": 1.4, "shoulder_mat": ("valley_cliff", "road")},
    }
    lip, land = TO_ROAD(LIP), TO_ROAD(LAND)

    def label(smp):
        s = smp.s
        if lip <= s <= land:
            return "gap"
        if lip - 12 <= s < lip:
            return "kicker"
        seg = seg_of(TO_PLAN(s))
        if seg == 5 or (seg == 4 and TO_PLAN(s) > SEG[5] - 6):
            return "boardwalk"
        if seg in (6, 7):
            return "headland"
        return "road"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "kicker":
            specials.append((s0, s1, "kicker", {"lift": lambda u, n: 0.6 * max(0.0, (u - (n - 8)) / 8) ** 2}))
        elif k != "road":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "road", max_len=150.0))

    X0, X1, Y0, Y1 = -180, 320, -200, 360
    ter = c.terrain("Sand", X0, X1, Y0, Y1, 4.0, natural, classify, near=9.0, fade=10.0, under=0.2)
    c.underfloor_flat("Seabed", X0, X1, Y0, Y1, 4.0, lambda x, y: natural(x, y) - 0.6, c.lib("wet_sand", "deep_water"))
    # The sea out to the horizon, the lagoon and the channel (water to look at; the sand
    # under them is deep water).
    c.ribbon("Sea South", [(x, -1340.0) for x in range(-1600, 1801, 200)], 2700.0, WATER_Z, c.lib("sea_water"), role="visual", steps=2)
    c.ribbon("Sea East", [(1220.0, y) for y in range(-1400, 1401, 200)], 2200.0, WATER_Z, c.lib("sea_water"), role="visual", steps=2)
    for name, (cx, cy, r) in (("Lagoon", LAGOON), ("Tide Pool", TIDE_POOL)):
        c.ribbon(name, [(cx - r - 3 + k * (2 * r + 6) / 12, cy) for k in range(13)], 2 * r + 6, WATER_Z, c.lib("sea_water"), role="visual", steps=2)
    c.ribbon("Channel", CHANNEL, 2 * CHANNEL_HALF + 4, WATER_Z, c.lib("sea_water"), role="visual", steps=2)

    # Piers under the pier, the sea stack in the hairpin, and the sea arch over the diagonal.
    for piece in c.pieces:
        for kind, size, every in (("boardwalk", 0.9, 7.0), ("kicker", 0.9, 6.0)):
            if piece.name.endswith(kind):
                kit.clear_piers(c, piece, [ter], every=every, mat=("palm_bark", "wall"), size=size, inset=size + 0.6)
    rock = c.rock_mass("Sea Stack", SEA_STACK[0], SEA_STACK[1], 9.0, 9.0, 22.0, z0=0.0, n=10, seed=4)
    c.assign(rock, c.lib("valley_cliff", "wall"))
    a0, a1 = TO_ROAD(SEG[9] + 28), TO_ROAD(SEG[9] + 50)
    q = c.at((a0 + a1) / 2)
    arch = c.rock_mass("Sea Arch", q.p.x, q.p.y, 16.0, 13.0, 17.0, z0=0.0, n=14, seed=7)
    c.tunnel(arch, a0, a1, half=c.width / 2 + 2.5, height=8.0, pad=10.0)
    c.paint_rock(arch, ("valley_cliff", "wall"), ("beach_sand", "sand"), floor=("beach_road", "road"), floor_z=q.p.z + 1.5)

    c.start_line()
    S = lambda i: TO_ROAD(SEG[i])  # noqa: E731
    # Zippers: up the beach, onto the pier (it carries you over the gap), the west beach.
    for at in (S(2) + 10, S(5) + 2, S(11) + 6):
        c.zipper(at, 0)
    for at, across in ((S(1) + 30, 3), (S(4) + 10, 0), (S(7) + 10, 0), (S(10) + 20, -3)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in ((S(0) + 30, -4, "red"), (S(0) + 30, 4, "blue"), (S(3) + 10, 0, "green"), (S(8) + 20, 0, "yellow"), (S(9) + 10, 0, "rainbow")):
        c.balloon(at, across, col)
    # A missed jump: put down past the channel.
    c.entity("respawn", **{"from": round(lip - 20, 1), "to": round(land + 4, 1), "at": round(land + 16, 1)})
    c.checkpoints(
        extra=[S(1) + 20, S(3) + 10, S(6) + 30, S(8) + 20, S(9) + 60, S(11) + 20],
        avoid=[(lip - 14, land + 8)],
        height=8.0,
    )

    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish()
    print("lap", round(c.length, 1))


if __name__ == "__main__":
    main()
