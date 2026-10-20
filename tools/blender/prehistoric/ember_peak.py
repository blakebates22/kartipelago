# Ember Peak: Prehistoric World, course 4. The Volcanic Apocalypse.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/ember_peak.py      (the bpy module)
#
# A lap of about 2.3 km round, up, into and down a colossal erupting volcano (230 m
# tall, 760 m across at its foot), in a landscape of lava rivers, black obsidian and
# burning forest, with more volcanoes smoking on the horizon:
#
#   A  The Burning Forest: the start, a wide road east across the south, the volcano
#      looming on the left.
#   B  The Obsidian Fields: sweeping S-bends between leaning black spires and lava pools.
#   C  The Dragon's Crossing: a wide stone bridge north over a deep lava ravine, below
#      the dragon's cliffs.
#   D  The Volcanic Ascent: a road carved round the east flank, a hairpin, and a
#      second, higher cliff road, 17 -> 55 m, over lava ravines.
#   E  The Mouth of the Volcano: a monumental glowing opening in the east face.
#   F  The Infernal Caverns: about 450 m (20 s) inside the mountain: an entry hall, a
#      lava-lake cavern crossed on a bridge, tunnels, the crystal gallery and the
#      magma falls hall, down to 49 m and up to 74 m.
#   G  The Eruption Escape: out high on the north-west flank and a fast sweeping
#      descent round the west side.
#   H  The Final Descent: past lava rivers and burning forest, back onto the start.
#
# Saves tracks-src/ember_peak.blend and exports public/tracks/ember_peak/. The scenery
# is ember_scenery.py, built from the volcanic kit in volcano_props.py.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp, smooth  # noqa: E402

TRACK_ID = "ember_peak"

# ---------------------------------------------------------------- the volcano

R0, HT = 380.0, 230.0  # the cone's foot radius and height (centred on the origin)
CRATER_R = 46.0
CORE_R = 192.0  # inside this the mountain is a separate rock (the caverns are cut in it)


PEAK = 130.0  # the steep summit cone, above the core


def _base(r):
    return HT * max(0.0, 1 - r / R0) ** 1.6 + PEAK * max(0.0, 1 - r / 215) ** 2


RIM_Z = _base(CRATER_R + 12) + 6.0
CRATER_LAVA_Z = RIM_Z - 40.0


def cone(r):
    """The volcano's height at distance r from its centre: a steepening cone, its summit
    rising sharply from the mountain's shoulders, with a crater pit at the top."""
    h = _base(r)
    if r < CRATER_R + 12:
        h = min(h, RIM_Z) - 42 * smooth((CRATER_R + 4 - r) / 16)
    return h


def P(theta, r, z, w=15.0):
    t = math.radians(theta)
    return (round(r * math.cos(t), 1), round(r * math.sin(t), 1), z, w)


# ---------------------------------------------------------------- the route

# (x, y, height, width) through the eight sections, anticlockwise round the volcano.
WAYPOINTS = [
    # A: the Burning Forest
    (-150, -405, 2.0, 16), (-50, -412, 2.0, 16), (40, -405, 2.5, 16),
    # B: the Obsidian Fields
    (100, -385, 3.5, 15), (153, -350, 5.0, 15), (207, -360, 6.0, 15), (255, -322, 7.0, 15), (286, -258, 8.5, 15),
    # C: the Dragon's Crossing (north over the lava ravine)
    (300, -190, 10.0, 17), (305, -120, 13.5, 17), (305, -50, 17.0, 16),
    # D: the ascent: round the east flank, the hairpin, and the higher cliff road
    P(5, 300, 21.0), P(17, 294, 25.5), P(28, 284, 29.5),
    (256, 188, 31.5, 15), (241.5, 216, 33.5, 15), (210.4, 221, 35.0, 15), (189.2, 197, 36.5, 15),
    P(32, 238, 40.0), P(20, 238, 44.0), P(8, 236, 48.5), P(-3, 233, 52.5),
    # E: into the mouth
    (213, -45, 55.0, 15), (186, -58, 56.5, 15),
    # F: the Infernal Caverns
    (150, -50, 56.0, 14), (124, -8, 53.0, 14), (122, 45, 49.5, 15), (98, 95, 49.0, 15), (50, 128, 52.0, 14),
    (-5, 140, 57.0, 14), (-55, 130, 63.0, 14), (-95, 110, 68.0, 14), (-130, 96, 72.0, 14), (-163, 92, 74.0, 15),
    # G: the Eruption Escape
    P(156, 205, 71.0), P(168, 222, 65.0), P(182, 240, 57.0), P(196, 262, 47.0), P(209, 285, 36.0), P(221, 310, 25.0),
    # H: the Final Descent
    (-218, -322, 13.0, 15), (-205, -380, 6.0, 16),
]

# Lava rivers: (bearing from the centre in degrees, from radius, to radius, half-width,
# depth of the ravine below the land). The first runs under the Dragon's Crossing.
RIVERS = [
    (-25.0, 240.0, 560.0, 26.0, 22.0),
    (15.0, 200.0, 330.0, 9.0, 13.0),
    (200.0, 200.0, 560.0, 11.0, 8.0),
    (236.0, 250.0, 560.0, 10.0, 6.0),
]


def river_at(x, y):
    """(distance across the nearest river, its half-width, depth, index), or None."""
    r = math.hypot(x, y)
    a = math.degrees(math.atan2(y, x))
    best = None
    for k, (th, r0, r1, hw, depth) in enumerate(RIVERS):
        if not (r0 - 10 < r < r1):
            continue
        wob = 6 * math.sin(r / 23 + k) + 3 * math.sin(r / 9 + k * 2)
        d = abs(math.radians((a - th + 180) % 360 - 180) * r - wob)
        if best is None or d - hw < best[0] - best[1]:
            best = (d, hw, depth, k)
    return best


def river_centre(k, r):
    th, r0, r1, hw, depth = RIVERS[k]
    wob = 6 * math.sin(r / 23 + k) + 3 * math.sin(r / 9 + k * 2)
    t = math.radians(th) + wob / r
    return r * math.cos(t), r * math.sin(t)


def land(x, y):
    """The volcano, its ridged flanks and the plain round it, rising to jagged hills at
    the map's edge (no rivers)."""
    r = math.hypot(x, y)
    a = math.atan2(y, x)
    h = cone(r)
    # Ridges and gullies down the flanks.
    h += 5.0 * math.sin(a * 9 + r / 40) * smooth((R0 - r) / 120) * smooth((r - 70) / 40)
    # The plain: lumpy, with low lava-rock mounds.
    h += 0.9 * math.sin(x / 17) * math.cos(y / 21) + 0.6 * math.sin((x - y) / 29)
    # Jagged hills all round the edge.
    e = math.hypot(x * 0.95, y)
    h += 70 * smooth((e - 470) / 70) * (0.6 + 0.4 * math.sin(a * 7 + 1.3)) + 20 * smooth((e - 480) / 40) * math.sin(a * 23)
    return h


# Lava pools in the obsidian fields (x, y, radius).
POOLS = [(130, -300, 16), (190, -305, 13), (230, -385, 15), (70, -350, 12), (250, -260, 12)]


def natural(x, y):
    h = land(x, y)
    rv = river_at(x, y)
    if rv:
        d, hw, depth, k = rv
        if d < hw + 14:
            bed = (h if k else min(h, 3.0)) - depth
            h = lerp(h, bed, smooth((hw + 14 - d) / 14))
    for px, py, pr in POOLS:
        dp = math.hypot(x - px, y - py)
        if dp < pr + 8:
            h = lerp(h, -2.5, smooth((pr + 8 - dp) / 8))
    return h


def lava_under(x, y):
    """Is (x, y) in a lava river or pool?"""
    rv = river_at(x, y)
    if rv and rv[0] < rv[1]:
        return True
    return any(math.hypot(x - px, y - py) < pr for px, py, pr in POOLS)


CAVE_S = [0.0, 0.0]  # the stretch of the lap inside the mountain (set in main)
LAKE_S = [0.0, 0.0]  # the lava-lake cavern's bridge (set in main)


def classify(c, n, info):
    r = math.hypot(c.x, c.y)
    if r < CORE_R - 6:
        return None  # the core rock is a separate mesh
    if lava_under(c.x, c.y) and c.z < land(c.x, c.y) - 1.5:
        return ("magma_rock", "lava")  # the bed of a lava river or pool: it burns
    if n.z < 0.62:
        return ("obsidian_cliff" if (int(c.z / 9) + int(r / 50)) % 3 else "magma_rock", "wall")
    if info["d"] < 12:
        return ("scorched_ground", "dirt")
    if r < 300:
        return ("ash_soil", "sand")
    return ("scorched_ground", "sand")


# ---------------------------------------------------------------- the course


def main():
    c = kit.Course(TRACK_ID, "Ember Peak", "volcanic_apocalypse")
    c.route(WAYPOINTS, width=15.0, bank=6.0)
    wall = ("basalt_block", "wall")
    c.kinds = {
        "ash": {"mat": "basalt_road", "shoulder": 1.8, "shoulder_mat": ("scorched_ground", "dirt")},
        "cliff": {"mat": "basalt_road", "shoulder": 1.2, "shoulder_mat": ("scorched_ground", "dirt"), "barrier": 1.1, "barrier_mat": wall},
        "bridge": {
            "mat": "basalt_road",
            "shoulder": 0.8,
            "shoulder_mat": ("basalt_block", "road"),
            "barrier": 1.3,
            "barrier_mat": wall,
            "deck": 4.0,
            "deck_mat": wall,
            "ground": False,
        },
        "cave": {"mat": "basalt_road", "shoulder": 2.5, "shoulder_mat": ("cave_rock", "dirt")},
        "cavebridge": {
            "mat": "basalt_road",
            "shoulder": 0.8,
            "shoulder_mat": ("basalt_block", "road"),
            "barrier": 1.3,
            "barrier_mat": wall,
            "deck": 3.0,
            "deck_mat": wall,
            "ground": False,
        },
    }

    def inside(smp):
        return math.hypot(smp.p.x, smp.p.y) < CORE_R + 2

    caves = kit.crossings(c, inside, margin=0)
    c0, c1 = max(caves, key=lambda r: r[1] - r[0])
    CAVE_S[:] = [c0, c1]
    S = lambda k: kit.s_near(c, WAYPOINTS[k][0], WAYPOINTS[k][1])  # noqa: E731
    LAKE = (S(25) + 12, S(27) + 8)  # the lava-lake cavern's bridge
    LAKE_S[:] = list(LAKE)

    def label(smp):
        x, y, s = smp.p.x, smp.p.y, smp.s
        if c0 - 2 <= s <= c1 + 2:
            return "cavebridge" if LAKE[0] <= s <= LAKE[1] else "cave"
        above = smp.p.z - natural(x, y)
        if above > 4.5:
            return "bridge"
        r = math.hypot(x, y)
        if r < 330:
            return "cliff"
        return "ash"

    specials = [(s0, s1, k) for s0, s1, k in kit.runs(c, label) if k != "ash"]
    c.roads(kit.plan(c, specials, "ash", max_len=220.0))

    X0, X1, Y0, Y1 = -560, 560, -560, 560
    c.terrain("Land", X0, X1, Y0, Y1, 5.5, natural, classify, near=9.0, fade=18.0)
    # Hidden floors, so nowhere can a kart fall through the world: under the land (flat
    # squares, so even under a cliff there's floor) and under the caverns (at each
    # cavern's floor). Only within 70 m of the road.

    def near(fn, m=70.0):
        return lambda x, y: fn(x, y) if c.nearest(x, y)[1] < m else None

    def under_land(x, y):
        if math.hypot(x, y) < CORE_R - 22:
            return None
        return natural(x, y) - 0.4

    def under_caves(x, y):
        if math.hypot(x, y) > CORE_R + 2:
            return None
        smp, d = c.nearest(x, y)
        if not (c0 - 25 <= smp.s <= c1 + 25) or d > 60:
            return None
        if LAKE[0] - 22 <= smp.s <= LAKE[1] + 18:
            return smp.p.z - 16.8
        if CAVE_S[0] + 0.78 * (c1 - c0) <= smp.s <= c0 + 0.92 * (c1 - c0):
            return smp.p.z - 4.4
        return smp.p.z - 0.9

    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 5.5, near(under_land), c.lib("scorched_ground", "dirt"))
    c.underfloor_flat("Cave Underfloor", -CORE_R, CORE_R, -CORE_R, CORE_R, 3.0, under_caves, c.lib("cave_rock", "dirt"))

    import ember_scenery  # noqa: E402

    core = ember_scenery.volcano_core(c, sys.modules[__name__], LAKE)
    lava = ember_scenery.lava(c, sys.modules[__name__])

    c.start_line()
    # Zippers: off the start, on the dragon bridge's approach, up the second cliff road,
    # on the caverns' long tunnel, and two down the escape.
    c.zipper(60, 0)
    c.zipper(S(8) - 10, 0)
    c.zipper(S(19), 0)
    c.zipper(S(29), 0)
    c.zipper(S(35), 0)
    c.zipper(S(38), 2)
    for at, across in ((110, -3), (S(4), 0), (S(9) + 20, 2), (S(12), 0), (S(20), 0), (S(25), 0), (S(30), 0), (S(36), 0), (S(40), 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (160, -4, "red"),
        (160, 4, "blue"),
        (S(6), 0, "green"),
        (S(12), 0, "yellow"),
        (S(18), 0, "rainbow"),
        (S(28), -3, "red"),
        (S(28), 3, "blue"),
        (S(37), 0, "green"),
        (S(41), 0, "yellow"),
    ):
        c.balloon(at, across, col)

    # Falling off the dragon's bridge into the ravine: put back at its far end.
    b0, b1 = S(7), S(10)
    c.entity("respawn", **{"from": round(b0, 1), "to": round(b1, 1), "at": round(b1 + 12, 1)})
    # And off the lava-lake bridge, likewise.
    c.entity("respawn", **{"from": round(LAKE[0] - 5, 1), "to": round(LAKE[1] + 5, 1), "at": round(LAKE[1] + 15, 1)})

    c.checkpoints(
        extra=[S(3), S(6), S(9), S(12), S(16), S(20), S(24), S(27), S(30), S(33), S(36), S(39)],
        height=10.0,
    )

    ember_scenery.build(c, core, lava, sys.modules[__name__])
    kit.paint.shade_roads(c.pieces, 0.45)
    c.finish()


if __name__ == "__main__":
    main()
