# Volcano Isle: the beach world's third course, painted (the Tropic Isles). The greybox's
# lap exactly (it's kept as volcano_isle_v2): the same roads, heights, surfaces, geysers,
# jump, zippers and checkpoints; only the look is new (isle_scenery.py,
# tropic_textures.py): a tropical island on a clear morning, black sand, jungle, hot
# springs, a fishing village, the dormant volcano behind.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/volcano_isle.py      (the bpy module)
#
# Blake (Oct 25): a tropical island, a bit longer than Shipwreck Bay and just as exciting;
# the volcano dormant, behind it all ("we dont want the volcano to be driving the theme,
# but adding"). About 880 m, a lap near 37 s:
#
#   1  The start along the black-sand beach, east, and a sweeper north onto the hot-spring
#      flats: geysers in the road on staggered beats (hit one as it blows: a free launch).
#   2  The jungle switchbacks: two hairpins up the island's flank.
#   3  The lava tube: into the hill and west through an S-bend, dark and gently downhill.
#   4  The cliff ledge, south along the island's west side, and the jump off its lip down
#      across the lagoon onto the beach (miss it and you're put back past it).
#   5  The fishing village's S along the shore, and the line.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import ruin_mode  # noqa: E402
from course_kit import lerp, smooth  # noqa: E402

import isle_scenery  # noqa: E402

# The ruin (volcano_isle_ruins.py): Tidewyrm's raid woke the volcano, and a flow came down
# over the hot-spring flats and buried the road there. The new road runs 7 m east on the
# flow's cooled crust: a wider sweeper onto the flats, a tighter turn up into the jungle,
# live lava beside it where the old road was. Everything else is the course's own (the
# same segments, numbers and heights; the lap the same length).
RUIN = ruin_mode.ON
TRACK_ID = "volcano_isle_ruin" if RUIN else "volcano_isle"

START = (0.0, 0.0)
LAYOUT = [
    ("S", 24),  # 0  1: the start along the beach, east
    ("L", 40, 90),  # 1  the sweeper north onto the hot-spring flats
    ("S", 25),  # 2  the flats: geysers
    ("R", 26, 90),  # 3  east, up into the jungle
    ("S", 6),  # 4
    ("L", 18, 180),  # 5  2: hairpin one
    ("S", 28),  # 6  climbing west
    ("R", 18, 180),  # 7  hairpin two
    ("S", 20),  # 8  climbing east
    ("L", 26, 90),  # 9  north
    ("L", 32, 90),  # 10 west, to the lava tube's mouth
    ("S", 25),  # 11 3: the lava tube...
    ("R", 36, 40),  # 12 ...its S-bend...
    ("L", 36, 80),  # 13
    ("R", 36, 40),  # 14
    ("S", 12),  # 15 ...and out
    ("L", 44, 30),  # 16 4: onto the cliff ledge
    ("S", 20),  # 17
    ("L", 32, 60),  # 18 south along the island's west side
    ("S", 120),  # 19 the ledge, the jump over the lagoon, the beach (closes the lap)
    ("L", 32, 90),  # 20 5: east along the shore
    ("S", 14),  # 21 the fishing village...
    ("R", 26, 50),  # 22 ...its S...
    ("L", 26, 50),  # 23
    ("S", 20),  # 24 ...and the line (closes the lap)
]
STD_LAYOUT = list(LAYOUT)
if RUIN:
    LAYOUT[1:5] = [("L", 47, 90), ("S", 25), ("R", 19, 90), ("S", 6)]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 19, 24, START, 0.0)
STD_PATH = kit.close_turtle(STD_LAYOUT, 19, 24, START, 0.0)[1]
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


def _plan_point(d):
    t = 0.0
    for a, b in zip(PATH, PATH[1:]):
        t += math.hypot(b[0] - a[0], b[1] - a[1])
        if t >= d:
            return b
    return PATH[-1]


# ---------------------------------------------------------------- heights

WATER_Z = 0.0
HEIGHT = {0: 2.0, 1: 2.0, 2: 3.0, 3: 5.0, 4: 7.0, 5: 8.0, 6: 12.0, 7: 18.0, 8: 22.0, 9: 24.0, 10: 26.0, 11: 26.0,
          12: 25.0, 13: 23.5, 14: 22.0, 15: 21.0, 16: 20.5, 17: 20.0, 18: 20.0, 19: 20.0, 20: 3.4, 21: 3.0, 22: 2.6,
          23: 2.4, 24: 2.2}
# The cliff jump: the ledge's lip, the lagoon below, the landing on the beach.
LEDGE = 46.0
LIP = SEG[19] + LEDGE
LAND = LIP + 18.0
LAND_Z = 7.0
TUBE = (SEG[11] - 6.0, SEG[16] + 4.0)


def _base_z(d, seg):
    a, b = SEG[seg], SEG.get(seg + 1, LENGTH)
    t = (d - a) / max(1e-6, b - a)
    z0, z1 = HEIGHT[seg], HEIGHT.get(seg + 1, HEIGHT[0])
    if seg == 19:
        if d <= LIP:
            return HEIGHT[19] - 0.03 * (d - SEG[19])  # the ledge, a touch downhill
        if d >= LAND:
            return lerp(LAND_Z, HEIGHT[20], smooth((d - LAND) / max(1e-6, SEG[20] - LAND)))
        return lerp(HEIGHT[19] - 0.03 * LEDGE, LAND_Z, (d - LIP) / (LAND - LIP))
    return lerp(z0, z1, smooth(t))


road_z = kit.with_jumps(_base_z, seg_of, [(LIP, LAND, 1.2, 0.8)])


def road_w(d, seg):
    if seg == 0 or d < 30:
        return 18.0
    if seg in (5, 6, 7):
        return 15.0  # the switchbacks
    if 11 <= seg <= 15:
        return 15.0  # the tube
    return 16.0


ROUTE, SHARP, LOOPS = kit.route_with_loops(PATH, LAYOUT, road_z, every=6.0, width=road_w)
TO_ROAD, TO_PLAN = kit.along(PATH, road_z)

# ---------------------------------------------------------------- the land

_gap = _plan_point((LIP + LAND) / 2)
LAGOON = (_gap[0] + 10.0, _gap[1], 34.0, 20.0)  # centre, radii
_t0, _t1 = _plan_point(TUBE[0]), _plan_point(TUBE[1])
HILL = ((_t0[0] + _t1[0]) / 2, (_t0[1] + _t1[1]) / 2 + 6.0)
VOLCANO = (HILL[0] + 60.0, HILL[1] + 420.0)
# The hot springs beside the flats.
_f = _plan_point(SEG[2] + 18)
SPRINGS = [(_f[0] - 22.0, _f[1] - 10.0, 7.0), (_f[0] - 26.0, _f[1] + 16.0, 5.0), (_f[0] + 24.0, _f[1] + 4.0, 6.0)]


def sea_d(x, y):
    """How far out to sea (negative: on land): south of the beach and west of the cliff."""
    south = (-16.0 + 2.5 * math.sin(x / 23.0)) - y
    west = (_gap[0] - 48.0 + 3.0 * math.sin(y / 19.0)) - x
    # (The paint: the island's east shore too, so the land never ends in a straight cut.)
    east = x - (240.0 + 8.0 * math.sin(y / 23.0) + 5.0 * math.cos(y / 11.0))
    return max(south, west, east)


def lagoon_d(x, y):
    cx, cy, rx, ry = LAGOON
    return (math.hypot((x - cx) / rx, (y - cy) / ry) - 1.0) * min(rx, ry)


# (The ruin) the old road over the flats, under the lava now: its centreline.
OLD_FLATS = [(p[0], p[1]) for p in STD_PATH if 1 <= p[3] <= 3]


def lava_d(x, y):
    """How far from the old flats road's edge (negative: on it); far away off the ruin."""
    if not RUIN:
        return 1e9
    return min(math.hypot(x - a, y - b) for a, b in OLD_FLATS) - 9.0


def springs_d(x, y):
    return min(math.hypot(x - a, y - b) - r for a, b, r in SPRINGS)


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


def volcano_top(c, volcano):
    """The paint (the volcano read as a green hill): jungle only on its lower slopes,
    bare grey ash and black rock above, a lake of lava in the crater, lava running down
    its south face towards the course, and an eruption now and then."""
    vx, vy = VOLCANO
    rx, ry, h = 300.0, 260.0, 230.0
    ash, rock = c.lib("lava_crust", "wall"), c.lib("isle_rock", "wall")
    up = [p.index for p in volcano.data.polygons if p.center.z > 120.0]
    c.assign(volcano, ash, [i for i in up if volcano.data.polygons[i].normal.z > 0.5])
    c.assign(volcano, rock, [i for i in up if volcano.data.polygons[i].normal.z <= 0.5])
    c.disc("Crater Lava", vx, vy, 0.24 * min(rx, ry), h + 0.4, c.lib("volcano_lava"), coll="Rocks", role="visual", n=24,
           wobble=0.1, seed=4)
    bands = [(1.0, 0.0), (0.82, 0.25), (0.62, 0.5), (0.44, 0.75), (0.3, 0.95), (0.26, 1.0)]

    def r_at(f):
        for (r0, f0), (r1, f1) in zip(bands, bands[1:]):
            if f0 <= f <= f1:
                return lerp(r0, r1, (f - f0) / (f1 - f0))
        return bands[-1][0]

    for k, a_deg in enumerate((-100.0, -78.0, -122.0)):
        a = math.radians(a_deg)
        pts = []
        f = 0.99
        while f > 0.42 + 0.08 * k:
            r = r_at(f) * 1.015
            pts.append((vx + r * rx * math.cos(a + 0.05 * math.sin(f * 9)), vy + r * ry * math.sin(a + 0.05 * math.sin(f * 9)),
                        10.0 - 6.0 * (0.99 - f), f * h + 0.6))
            f -= 0.03
        c.ribbon("Lava Run %d" % k, pts, 8.0, 0.0, c.lib("volcano_lava"), coll="Rocks", role="visual", steps=2)
    gx, gy, gz = c.game(vx, vy, h + 2.0)
    c.entity("eruption", x=gx, y=gy, z=gz, period=11.0, offset=4.0)


def natural(x, y):
    """The ground at about the road's height near it, the island rising inland (north),
    sloping into the sea south and west, the lagoon under the jump, the hot springs."""
    z, d = near_road_z(x, y)
    inland = 26.0 * smooth((y - 60.0) / 140.0) * smooth((x - (_gap[0] - 10.0)) / 40.0)
    h = lerp(z - 0.5, max(z - 0.5, inland + 2.0), smooth((d - 14) / 30))
    h += 0.5 * math.sin(x / 17.0) * math.cos(y / 13.0) * smooth((d - 12) / 20)
    s = sea_d(x, y)
    if s > -14:
        h = lerp(h, WATER_Z - 2.0 - 0.05 * max(0.0, s), smooth((s + 14) / 14))
    w = lagoon_d(x, y)
    if w < 8:
        h = lerp(h, WATER_Z - 2.5, smooth((8 - w) / 8))
    sp = springs_d(x, y)
    if sp < 3 and d > 10:
        h = lerp(h, z - 1.6, smooth((3 - sp) / 3))
    if RUIN and d > 9.6:
        lv = lava_d(x, y)
        if lv < 4:  # the flow, a little below the crust road, its edges heaped
            h = lerp(h, z - 0.5, smooth((4 - lv) / 4))
    return h


def classify(c, n, info):
    if n.z < 0.6:
        return ("valley_cliff", "wall")
    if c.z < WATER_Z - 0.4:
        return ("wet_sand", "deep_water")
    if c.z < WATER_Z + 0.6:
        return ("wet_sand", "sand")
    if RUIN and lava_d(c.x, c.y) < 0:
        # (info["d"]: how far from the road) live lava clear of the new road's shoulders; crust
        # between, and along the flow's edges.
        return ("lava_flow", "lava") if info["d"] > 11.0 and lava_d(c.x, c.y) < -1.0 else ("lava_crust", "soft_sand")
    # Soft ground off the road (cutting across mustn't pay); the shoulders stay sand.
    # (The paint: black sand by the sea, jungle up the island's flanks; the same surface.)
    if c.z > 4.5 and sea_d(c.x, c.y) < -16 and lagoon_d(c.x, c.y) > 4:
        return ("isle_moss" if n.z < 0.85 else "isle_jungle", "soft_sand")
    return ("beach_sand", "soft_sand")


# The paint: each greybox material -> Volcano Isle's own (Course.lib keeps the old surface).
PAINT = {
    "beach_road": "isle_road",
    "beach_sand": "isle_sand",
    "wet_sand": "isle_wet_sand",
    "sea_water": "isle_sea",
    "tiki_wood": "isle_rail",
    "valley_cliff": "isle_rock",
}


def main():
    kit.MAT_REMAP.clear()
    kit.MAT_REMAP.update(PAINT)
    c = kit.Course(TRACK_ID, "Volcano Isle (Ruined)" if RUIN else "Volcano Isle", "isle_ruins" if RUIN else "volcano_isle")
    c.route(ROUTE, width=16.0, bank=6.0, sharp=SHARP)
    sand = ("beach_sand", "sand")
    rock = ("valley_cliff", "road")
    c.kinds = {
        "road": {"mat": "beach_road", "shoulder": 1.6, "shoulder_mat": sand},
        "jungle": {"mat": "beach_road", "shoulder": 1.2, "shoulder_mat": sand, "barrier": 1.0, "barrier_mat": ("tiki_wood", "wall")},
        "tube": {"mat": "beach_road", "shoulder": 1.0, "shoulder_mat": rock},
        "ledge": {"mat": "beach_road", "shoulder": 1.0, "shoulder_mat": rock, "barrier": 1.0, "barrier_mat": ("valley_cliff", "wall")},
        "kicker": {"mat": "beach_road", "shoulder": 1.0, "shoulder_mat": rock},
        # (The ruin) the new road over the flats, on the flow's cooled crust.
        "crust": {"mat": "basalt_road", "shoulder": 1.6, "shoulder_mat": ("lava_crust", "sand")},
    }
    lip, land = TO_ROAD(LIP), TO_ROAD(LAND)
    t0, t1 = TO_ROAD(TUBE[0]), TO_ROAD(TUBE[1])

    def label(smp):
        s = smp.s
        if lip <= s <= land:
            return "gap"
        if lip - 12 <= s < lip:
            return "kicker"
        if t0 <= s <= t1:
            return "tube"
        seg = seg_of(TO_PLAN(s))
        if RUIN and seg in (1, 2, 3):
            return "crust"
        if seg in (5, 6, 7):
            return "jungle"
        if seg in (16, 17, 18, 19) and s < lip:
            return "ledge"
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

    X0, X1, Y0, Y1 = -260, 300, -200, 380
    ter = c.terrain("Sand", X0, X1, Y0, Y1, 4.0, natural, classify, near=9.0, fade=10.0, under=0.2)
    c.underfloor_flat("Seabed", X0, X1, Y0, Y1, 4.0, lambda x, y: natural(x, y) - 0.6, c.lib("wet_sand", "deep_water"))
    c.ribbon("Sea South", [(x, -1340.0) for x in range(-1600, 1801, 200)], 2700.0, WATER_Z, c.lib("sea_water"), role="visual", steps=2)
    c.ribbon("Sea West", [(-1260.0, y) for y in range(-1400, 1401, 200)], 2200.0, WATER_Z, c.lib("sea_water"), role="visual", steps=2)
    # (The paint: the sea round the east shore and behind the island, under the volcano.)
    c.ribbon("Sea East", [(1330.0, y) for y in range(-1400, 1401, 200)], 2200.0, WATER_Z, c.lib("sea_water"), role="visual", steps=2)
    c.ribbon("Sea North", [(x, 1500.0) for x in range(-1600, 1801, 200)], 2300.0, WATER_Z, c.lib("sea_water"), role="visual", steps=2)
    cx, cy, rx, ry = LAGOON
    c.disc("Lagoon", cx, cy, rx + 4, WATER_Z, c.lib("sea_water"), role="visual")
    for k, (x, y, r) in enumerate(SPRINGS):
        z, _ = near_road_z(x, y)
        c.disc("Spring %d" % k, x, y, r, z - 0.9, c.lib("sea_water"), role="visual", n=16)

    # The hill the lava tube runs through, and the volcano far behind (scenery).
    hx, hy = HILL
    # Its ends stop short of the tube's mouths (the road mustn't meet rock before them).
    span = math.hypot(_t1[0] - _t0[0], _t1[1] - _t0[1]) / 2 - 4.0
    hill = c.rock_mass("Tube Hill", hx, hy, span, 48.0, 50.0, z0=-4.0, n=24, seed=11)
    c.tunnel(hill, t0 + 6, t1 - 4, half=c.width / 2 + 2.5, height=9.5, pad=14.0)
    c.paint_rock(hill, ("valley_cliff", "wall"), ("isle_jungle", "sand"), floor=("isle_tube", "road"), floor_z=road_z(SEG[11], 11) - 3.0)
    vx, vy = VOLCANO
    volcano = c.rock_mass("Volcano", vx, vy, 300.0, 260.0, 230.0, z0=-10.0, n=28, seed=3,
                          bands=[(1.0, 0.0), (0.82, 0.25), (0.62, 0.5), (0.44, 0.75), (0.3, 0.95), (0.26, 1.0)])
    volcano["kp_role"] = "visual"
    c.paint_rock(volcano, ("isle_rock", "wall"), ("isle_jungle", "grass"))
    volcano_top(c, volcano)

    c.start_line()
    S = lambda i: TO_ROAD(SEG[i])  # noqa: E731
    # Zippers: off the flats into the climb, out of the tube, onto the ledge's lip.
    for at in (S(3) + 4, S(16) + 4, TO_ROAD(LIP - 34)):
        c.zipper(at, 0)
    for at, across in ((S(6) + 20, 0), (S(13) + 20, 3), (S(20) + 30, -3), (S(23) + 6, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in ((S(0) + 22, -4, "red"), (S(0) + 22, 4, "blue"), (S(4) + 6, 0, "green"), (S(9) + 10, 0, "yellow"),
                            (S(17) + 12, 0, "rainbow"), (S(21) + 10, 0, "red")):
        c.balloon(at, across, col)
    # The geysers in the flats' road: a free launch if you hit one as it blows.
    for k, (s, across) in enumerate(((S(1) + 50, -3.5), (S(2) + 10, 3.5), (S(2) + 28, -2.0))):
        q = c.at(s)
        p = q.side(across)
        gx, gy, gz = c.game(p.x, p.y, q.p.z)
        c.entity("geyser", x=gx, y=gy, z=gz, r=3.4, height=16.0, period=6.0, offset=round(k * 2.0, 2), warn=1.2, blast=1.8, launch=14.0)
    c.entity("respawn", **{"from": round(lip - 20, 1), "to": round(land + 4, 1), "at": round(land + 18, 1)})
    c.checkpoints(
        extra=[S(1) + 20, S(4), S(6) + 20, S(8) + 10, S(11) + 10, S(13) + 30, S(17), S(20) + 10, S(22) + 10],
        avoid=[(lip - 14, land + 8)],
        height=8.0,
    )

    sc = isle_scenery.build(c, sys.modules[__name__], ter)
    if RUIN:
        ruin_mode.DRESS(c, sys.modules[__name__], sc)
    c.finish()
    print("lap", round(c.length, 1))


if __name__ == "__main__":
    main()
