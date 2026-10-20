# Hearthglow Hollow: Frostveil Peaks, course 3. A Christmas village on a snowy evening.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/hearthglow_hollow.py      (the bpy module)
#
# A lap of about 2.55 km through a magical alpine village at twilight, all decorated
# for Christmas, and up the mountain above it:
#
#   A  The Village Entrance: the start, under a great wooden Christmas arch, up a street
#      of glowing cottages, market stalls and lantern posts, the giant tree ahead.
#   B  The Village Square: down into the plaza and round the giant Christmas tree in a
#      sweep of curves, past the frozen fountain, stalls, snowmen and presents.
#   C  The Frozen River Crossing: north over an arched stone bridge above the frozen
#      river (or, before it, a shortcut down onto the river ice: tighter, slippery and
#      shorter), then west along the north bank.
#   D  The Enchanted Forest: winding between towering pines strung with lights, past
#      cabins and lanterns; giant snowballs roll across the road on a fixed beat.
#   E  The Mountain Climb: a long climb up the mountainside on snowy roads and timber
#      trestles, a hairpin, the village glowing below, a high trestle over the creek's
#      gorge, to the bell tower at the summit.
#   F  The Sleigh Run: a fast plunge south down a broad snowy chute under decorated
#      arches, two jumps, and a sleigh that crosses the run on a fixed beat.
#   G  The Covered Bridge and the Village Return: through a long lantern-lit covered
#      bridge over the river, back through the village's lanes, and a last drift round
#      onto the finish straight.
#
# Every corner is a 32-60 m arc. Saves tracks-src/hearthglow_hollow.blend and exports
# public/tracks/hearthglow_hollow/. The scenery is hearthglow_scenery.py, built from
# the kit in hearthglow_props.py.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp, smooth  # noqa: E402

TRACK_ID = "hearthglow_hollow"

# ---------------------------------------------------------------- the layout

START = (0.0, -180.0)
LAYOUT = [
    ("S", 120),  # 0  A: the entrance street, north
    ("R", 40, 40),  # 1  B: down into the square...
    ("L", 50, 120),  # 2  ...round the giant tree...
    ("R", 45, 80),  # 3  ...and out, north
    ("S", 30),  # 4  C: the street to the bridge (the shortcut leaves here)
    ("S", 60),  # 5  the stone bridge over the frozen river
    ("S", 20),  # 6
    ("L", 40, 90),  # 7  west along the north bank
    ("S", 80),  # 8  the north lane (the shortcut comes back here)
    ("R", 45, 60),  # 9  D: into the forest
    ("S", 40),  # 10 the first snowball crossing
    ("L", 40, 60),  # 11
    ("R", 40, 90),  # 12
    ("S", 40),  # 13 the second snowball crossing
    ("R", 40, 90),  # 14 E: onto the mountainside, east
    ("S", 130),  # 15 the climb
    ("L", 32, 180),  # 16 the hairpin
    ("S", 230),  # 17 the high road west, the village below; the creek trestle
    ("L", 50, 90),  # 18 the summit and the bell tower
    ("S", 80),  # 19 F: the sleigh run
    ("R", 60, 40),  # 20
    ("L", 60, 80),  # 21
    ("R", 60, 40),  # 22
    ("S", 80),  # 23 the first jump
    ("S", 70),  # 24 the sleigh crossing
    ("S", 90),  # 25 the second jump (stretched to close the loop)
    ("L", 50, 90),  # 26 G: east...
    ("S", 80),  # 27 ...through the covered bridge
    ("S", 120),  # 28 the river lane (stretched to close the loop)
    ("R", 40, 90),  # 29 south down the west lane
    ("S", 110),  # 30
    ("L", 45, 90),  # 31 east along the bottom lane
    ("S", 40),  # 32
    ("L", 45, 90),  # 33 the last drift, onto the finish straight
    ("S", 40),  # 34
]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 25, 28, START, 90.0)
SEG = kit.segment_starts(PATH)
LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))
# The two jumps on the sleigh run: (lip, landing).
JUMPS = [(SEG[23] + 30, SEG[23] + 42), (SEG[25] + 38, SEG[25] + 50)]


def _seg_point(i):
    return next(p for p in PATH if p[3] == i)


def _arc_centre(i):
    x, y, h, _ = _seg_point(i)
    sg = LAYOUT[i]
    a = math.radians(h + (90 if sg[0] == "L" else -90))
    return (x + sg[1] * math.cos(a), y + sg[1] * math.sin(a))


TREE = _arc_centre(2)  # the giant Christmas tree, in the middle of the square
SUMMIT = _arc_centre(18)  # the bell tower stands inside the summit turn

# Heights along the lap (metres along it, height); the road eases between them.
J = JUMPS
ANCHORS = [
    (0.0, 3.0),
    (SEG[1], 3.0),
    (SEG[2], 2.0),  # down into the square
    (SEG[3], 2.0),
    (SEG[4], 2.6),
    (SEG[5], 4.2),  # the stone bridge, arched over the river
    (SEG[5] + 30, 5.0),
    (SEG[6], 4.2),
    (SEG[7], 3.6),
    (SEG[9], 4.0),
    (SEG[12], 7.0),
    (SEG[14], 11.0),
    (SEG[15], 12.5),
    (SEG[16], 23.0),
    (SEG[17], 28.0),
    (SEG[18], 49.0),
    (SEG[19], 51.0),  # the summit
    (J[0][0], 25.5),  # the first jump's lip
    (J[0][1], 20.6),  # ...its landing
    (J[1][0], 11.5),  # the second jump's lip
    (J[1][1], 6.8),  # ...its landing
    (SEG[26], 4.6),
    (SEG[27], 4.4),  # the covered bridge
    (SEG[28], 4.4),
    (SEG[29], 3.4),
    (SEG[31], 3.0),
    (LENGTH, 3.0),
]


def _lin(d):
    d = min(max(d, 0.0), LENGTH)
    for (d0, z0), (d1, z1) in zip(ANCHORS, ANCHORS[1:]):
        if d0 <= d <= d1:
            return lerp(z0, z1, (d - d0) / max(1e-6, d1 - d0))
    return 3.0


def road_z(d, seg=None):
    # The jumps' run-ups, gaps and landings are straight slopes; elsewhere heights ease
    # over 30 m.
    if any(lip - 34 <= d <= land + 14 for lip, land in JUMPS):
        return _lin(d)
    return sum(_lin(d + k) for k in range(-15, 16, 3)) / 11


def road_w(d, seg):
    if seg in (1, 2, 3):
        return 17.0  # the square
    if seg in (19, 20, 21, 22, 23, 24, 25):
        return 18.0  # the sleigh run's broad chute
    if seg in (5, 27):
        return 14.0  # the bridges
    if seg in (15, 16, 17):
        return 14.0  # the mountain road
    return 15.0


ROUTE = kit.route_points_by(PATH, road_z, every=10.0, width=road_w)


def seg_of(s):
    k = 0
    for i, d in SEG.items():
        if d <= s:
            k = max(k, i)
    return k


# ---------------------------------------------------------------- the land


def sm(t):
    return smooth(max(0.0, min(1.0, t)))


def _nearest(px, py, pts):
    """Distance to a polyline, the index of the nearest segment, and the nearest point."""
    best = (1e9, 0, (0.0, 0.0))
    for i, ((ax, ay), (bx, by)) in enumerate(zip(pts, pts[1:])):
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        qx, qy = ax + t * dx, ay + t * dy
        d = math.hypot(px - qx, py - qy)
        if d < best[0]:
            best = (d, i, (qx, qy))
    return best


# The frozen river: down from the falls in the north-east mountains, west under the
# stone bridge (x = -57), past the north lane, south-west to meet the creek, and south
# under the covered bridge (y = -70) out of the valley.
RIVER = [(300.0, 600.0), (250.0, 470.0), (150.0, 300.0), (40.0, 180.0), (-57.0, 150.0), (-150.0, 155.0),
         (-250.0, 115.0), (-320.0, 25.0), (-345.0, -40.0), (-338.0, -70.0), (-330.0, -200.0), (-320.0, -560.0)]
# The creek: from the falls in the north mountains, south under the high trestle, down
# between the forest and the sleigh run, into the river.
CREEK = [(-350.0, 640.0), (-352.0, 560.0), (-355.0, 503.0), (-362.0, 400.0), (-365.0, 250.0), (-358.0, 100.0), (-345.0, -40.0)]
RIVER_Z = -1.6  # the ice


def water_at(x, y):
    """(distance from the nearest water's centre, its half-width, which: 0 river 1 creek)."""
    d0 = _nearest(x, y, RIVER)[0]
    d1 = _nearest(x, y, CREEK)[0]
    if d0 <= d1:
        return d0, 13.0 + 2.5 * math.sin(x / 31 + y / 47), 0
    return d1, 7.0 + 1.5 * math.sin(y / 23), 1


def mountains(x, y):
    """How high the mountains round the valley rise here (before terracing)."""
    north = 1.4 * max(0.0, y - (560 + 30 * math.sin(x / 61) + 10 * math.sin(x / 17)))
    west = 1.5 * max(0.0, -x - (470 + 18 * math.sin(y / 43)))
    east = 1.2 * max(0.0, x - (330 + 25 * math.sin(y / 51)))
    south = 1.1 * max(0.0, -y - (340 + 20 * math.sin(x / 37)))
    return north, west, east, south


# The mountainside the climb crosses: shaped round its two roads (the first rising east
# at y = 439, the high road rising west at y = 503), steeper in the west.
LEG1_Y, LEG2_Y = 439.0, 503.0


def mountainside(x, y, floor):
    z1 = 12.0 + (x + 311) * 0.06
    z2 = 27.0 + (-142 - x) * 0.087
    t = (y - LEG1_Y) / (LEG2_Y - LEG1_Y)
    if t < 0:
        h = lerp(floor, z1 - 1.0, sm((y - 360) / (LEG1_Y - 360)))
    elif t <= 1:
        h = lerp(z1, z2, t) - 1.0
    else:
        h = z2 - 1.0 + (y - LEG2_Y) * 0.55
    w = sm((x + 440) / 30) * sm((-40 - x) / 70)
    return lerp(floor, max(floor, h), w)


def terrace(v, step=16.0):
    if v <= 0:
        return v
    k = math.floor(v / step)
    f = v / step - k
    return (k + sm((f - 0.55) / 0.45)) * step


def land(x, y):
    """The valley without its waterways: the village floor, the forest slopes, the
    mountainside the climb crosses, the ridge the sleigh run comes down, and the
    mountains all round."""
    h = 3.0 + 0.6 * math.sin(x / 29) * math.cos(y / 23) + 0.4 * math.sin((x - y) / 41)
    # The forest floor rises gently to the north-west.
    h += 8.0 * sm((y - 200) / 200) * sm((-x - 60) / 120)
    north, west, east, south = mountains(x, y)
    h = mountainside(x, y, h)
    # The ridge the sleigh run comes down, west of the creek.
    ridge = sm((-x - 380) / 30) * max(0.0, (y + 40) * 0.1)
    h = max(h, 3.0 + ridge) if y > -60 else h
    hi = max(north, west, east, south)
    h += terrace(min(240.0, hi), 18.0)
    h += 40 * (0.5 + 0.5 * math.sin(x / 47 + 0.4) * math.cos(y / 37)) * sm((hi - 50) / 90)
    return h


def natural(x, y):
    h = land(x, y)
    d, hw, which = water_at(x, y)
    if d < hw + 12:
        bed = RIVER_Z if which == 0 else RIVER_Z + 0.4
        h = lerp(h, min(h, bed), sm((hw + 12 - d) / 12))
    return h


def classify(c, n, info):
    d, hw, which = water_at(c.x, c.y)
    if d < hw and c.z < RIVER_Z + 0.8:
        return ("river_ice", "ice")
    if n.z < 0.62:
        if c.z > 60 and n.z > 0.3:
            return ("summit_snow", "wall")
        return ("summit_cliff" if (int(c.z / 8) + int(c.x / 40)) % 3 else "summit_rock", "wall")
    # The village square is paved (swept cobbles round the giant tree).
    if math.hypot(c.x - TREE[0], c.y - TREE[1]) < 86 and c.z < 6:
        return ("hearth_cobble", "snow_stone")
    if info["d"] < 11:
        return ("summit_road", "packed_snow")
    return ("summit_snow", "deep_snow")


def underfloor_z(x, y):
    return min(land(x, y), natural(x, y)) - 0.35


# The shortcut onto the frozen river: off the street before the stone bridge, down the
# bank onto the ice, west along the river, and up the north bank onto the north lane.
SHORTCUT = [(-57.0, 100.0), (-61.0, 116.0), (-78.0, 136.0), (-100.0, 150.0), (-122.0, 156.0), (-138.0, 162.0),
            (-145.0, 180.0), (-148.0, 205.0), (-155.0, 228.0), (-166.0, 238.5), (-180.0, 241.0)]


def shortcut_z(i, n):
    """Heights down onto the ice and back up: the street, the ice, the lane."""
    zs = [2.6, 2.0, 0.2, -1.2, -1.4, -1.3, -0.6, 1.4, 3.0, 3.6, 3.7]
    return zs[i]


# ---------------------------------------------------------------- the course


def main():
    c = kit.Course(TRACK_ID, "Hearthglow Hollow", "hearthglow")
    c.route(ROUTE, width=15.0, bank=6.0)
    snowbank = ("summit_snow", "packed_snow")
    fence = ("timber_rail", "wall")
    stone = ("hearth_stone", "wall")
    c.kinds = {
        "street": {"mat": "hearth_cobble", "shoulder": 1.4, "shoulder_mat": snowbank, "barrier": 0.7, "barrier_mat": ("summit_snow", "wall")},
        "icy": {"mat": "icy_cobble", "shoulder": 1.4, "shoulder_mat": snowbank, "barrier": 0.7, "barrier_mat": ("summit_snow", "wall")},
        "square": {"mat": "hearth_cobble", "shoulder": 2.6, "shoulder_mat": ("hearth_cobble", "snow_stone")},
        "stonebridge": {
            "mat": "hearth_cobble",
            "shoulder": 0.8,
            "shoulder_mat": ("hearth_stone", "snow_stone"),
            "barrier": 1.2,
            "barrier_mat": stone,
            "deck": 4.0,
            "deck_mat": stone,
            "ground": False,
        },
        "forest": {"mat": "summit_road", "shoulder": 1.8, "shoulder_mat": snowbank},
        "climb": {"mat": "summit_road", "shoulder": 1.2, "shoulder_mat": snowbank, "barrier": 1.0, "barrier_mat": fence},
        "trestle": {
            "mat": "plank_road",
            "shoulder": 0.6,
            "shoulder_mat": ("plank_road", "road"),
            "barrier": 1.2,
            "barrier_mat": fence,
            "deck": 2.4,
            "deck_mat": ("timber_beam", "wall"),
            "ground": False,
        },
        "summit": {"mat": "hearth_cobble", "shoulder": 1.4, "shoulder_mat": ("hearth_stone", "snow_stone"), "barrier": 1.1, "barrier_mat": stone},
        "sleighrun": {"mat": "summit_road", "shoulder": 1.6, "shoulder_mat": snowbank, "barrier": 1.2, "barrier_mat": ("summit_snow", "wall")},
        "ramp": {
            "mat": "summit_road",
            "shoulder": 0.8,
            "shoulder_mat": snowbank,
            "barrier": 1.2,
            "barrier_mat": fence,
            "deck": 5.0,
            "deck_mat": ("timber_beam", "wall"),
            "ground": False,
        },
        "landing": {"mat": "summit_road", "shoulder": 1.6, "shoulder_mat": snowbank, "barrier": 1.2, "barrier_mat": ("summit_snow", "wall")},
        "covered": {
            "mat": "plank_road",
            "shoulder": 0.8,
            "shoulder_mat": ("plank_road", "road"),
            "barrier": 1.4,
            "barrier_mat": fence,
            "deck": 3.0,
            "deck_mat": ("timber_beam", "wall"),
            "ground": False,
        },
    }
    lift = {"lift": lambda u, n: 1.5 * max(0.0, (u - (n - 10)) / 10) ** 2}

    def label(smp):
        x, y, s = smp.p.x, smp.p.y, smp.s
        seg = seg_of(s)
        for lip, land_ in JUMPS:
            if lip <= s <= land_:
                return "gap"
            if lip - 30 <= s < lip:
                return "ramp"
            if land_ < s <= land_ + 30:
                return "landing"
        above = smp.p.z - natural(x, y)
        if seg in (4, 5, 6) and above > 2.5:
            return "stonebridge"
        if seg in (27, 28) and above > 2.5:
            return "covered"
        if seg in (1, 2, 3):
            return "square"
        if seg in (15, 16, 17, 18) and above > 4.0:
            return "trestle"
        if seg == 18 or seg == 19:
            return "summit"
        if seg in (15, 16, 17):
            return "climb"
        if 19 <= seg <= 26:
            return "sleighrun"
        if 9 <= seg <= 14:
            return "forest"
        # Icy patches in the village lanes.
        if (seg == 8 and s > SEG[8] + 30) or (seg == 30 and s < SEG[30] + 50):
            return "icy"
        return "street"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "ramp":
            specials.append((s0, s1, k, lift))
        elif k != "street":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "street", max_len=200.0))
    short = [(x, y, shortcut_z(i, len(SHORTCUT))) for i, (x, y) in enumerate(SHORTCUT)]
    c.shortcut("River Shortcut", short, "river_ice_road", "icy_stone", width=10.0, shoulder=0.8, shoulder_mat=("river_ice", "ice"))

    X0, X1, Y0, Y1 = -620, 520, -460, 720
    c.terrain("Land", X0, X1, Y0, Y1, 6.5, natural, classify, near=9.0, fade=18.0)

    def near(fn, m=64.0):
        return lambda x, y: fn(x, y) if c.nearest(x, y)[1] < m else None

    def under(x, y):
        # Just under the land as it really is (pulled down to the road where the road is
        # cut into a slope).
        nat = natural(x, y)
        w, z = c.road_height(x, y, 9.0, 18.0, 0.2, nat)
        return min(underfloor_z(x, y), lerp(nat, z, w) - 0.6)

    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 5.0, near(under), c.lib("summit_snow", "deep_snow"))

    c.start_line()
    S = lambda i: SEG[i]  # noqa: E731
    # Zippers: off the start, out of the square, along the north lane, up the climb, on
    # the high road, down the sleigh run and out of the covered bridge.
    c.zipper(40, 0)
    c.zipper(S(4) + 6, 0)
    c.zipper(S(15) + 50, 0)
    c.zipper(S(17) + 120, 0)
    c.zipper(S(19) + 30, 0)
    c.zipper(S(28) + 20, 0)
    for at, across in ((80, -4), (S(3) + 20, 0), (S(8) + 20, 3), (S(13) + 30, 0), (S(15) + 100, 0), (S(17) + 60, -3), (S(24) + 50, 0), (S(28) + 70, 0), (S(32) + 10, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (100, -4, "red"),
        (100, 4, "green"),
        (S(2) + 50, 0, "blue"),
        (S(8) + 50, 0, "yellow"),
        (S(14) + 30, 0, "rainbow"),
        (S(17) + 180, 0, "red"),
        (S(20) + 30, -4, "green"),
        (S(20) + 30, 4, "blue"),
        (S(26) + 40, 0, "yellow"),
        (S(30) + 60, 0, "rainbow"),
    ):
        c.balloon(at, across, col)

    # A missed jump: put down on its landing.
    for lip, land_ in JUMPS:
        c.entity("respawn", **{"from": round(lip - 30, 1), "to": round(land_ + 6, 1), "at": round(land_ + 30, 1)})

    # Checkpoints: one in the middle of the stretch the shortcut skips, with a twin gate
    # across the shortcut on the ice (either counts), and none elsewhere in that stretch.
    s_in, s_out = kit.s_near(c, *SHORTCUT[0]), kit.s_near(c, *SHORTCUT[-1])
    apex = (s_in + s_out) / 2
    # (With a gate just before and just after the stretch, no gap is long enough for the
    # generator to fill one in inside it.)
    gates = c.checkpoints(
        extra=[S(2), s_in - 5, apex, s_out + 5, S(9) + 30, S(12), S(14) + 40, S(16), S(17) + 100, S(18) + 20, J[0][0] - 50, J[0][1] + 40,
               J[1][0] - 45, J[1][1] + 40, S(27) + 40, S(29) + 40, S(31) + 40],
        avoid=[(s_in - 2, apex - 6), (apex + 6, s_out + 2)],
        height=8.0,
    )
    main_gate = min(gates.items(), key=lambda kv: abs(kv[0] - apex))[1]
    c.alt_gate(main_gate, "river_shortcut", [(x, y, z) for x, y, z in short[2:7]], width=22.0)

    import hearthglow_scenery  # noqa: E402

    hearthglow_scenery.build(c, sys.modules[__name__])
    ter = list(c.coll("Terrain").objects)
    c.preset("sun", ter, 0.2)
    c.preset("bottoms", ter, 0.3)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish()


if __name__ == "__main__":
    main()
