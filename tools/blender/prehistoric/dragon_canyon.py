# Dragon Canyon: Dragon Kingdom, course 2, painted as the Emerald Kingdom (Blake's boards,
# Oct 25: an overgrown jungle castle and its ruins; emerald.py). The same lap, land and
# collision as the first paint (kept as dragon_canyon_v2), and the most technical,
# drift-hungry lap in the game.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/dragon_canyon.py      (the bpy module)
#
# A lap of about 2.1 km of red sandstone canyon: stacked hairpins up the cliffs, a
# bridge across the gorge, S-bends through a dragon's bones, the imperial quarry, a
# tunnel through the mesa, the High Bridges over the chasm, a hidden oasis, a sprint
# along the river, the watchtower's hairpins, and the Final Twist down to the gate.
#
#   1  The Canyon Outpost: the start, under the fortress's dragon gate.
#   2  The Cliffside Hairpins: right onto the bottom ledge, then two stacked hairpins
#      climbing the cliff, each ledge above the last.
#   3  The Great Canyon Descent: off the top ledge, across the Canyon Bridge over the
#      gorge (the Great Falls beside it) and down the far wall.
#   4  Dragon Skeleton Pass: left-right-left through the ribs of a colossal dragon, its
#      skull jutting from the east wall.
#   5  The Imperial Quarry: round the loading yard past the cranes, the block stacks and
#      the workers. (The Service Road cuts the corner: narrow and dusty.)
#   6  The Winding Caverns: a tunnel through the mesa, bending west, gates shut on the
#      side passages, light leaking from sealed chambers.
#   7  The High Bridges: out over the River Sprint and the chasm, sweeping round the Lone
#      Spire.
#   8  The Hidden Oasis: down round the palm-fringed pool and its village.
#   9  River Canyon Sprint: north along the river, fast, under the High Bridges.
#  10  The Watchtower Ascent: over the river and up two hairpins to the watchtower.
#  11  The Final Twist: snapping left and right off the tower's ledge, over the crest,
#      round the Dragon's Coil hairpin...
#  12  ...and back to the Dragon Gate.
#
# The land is dcanyon_land.py (plain data, no Blender); the scenery dcanyon_scenery.py
# and dcanyon_town.py, the kit dcanyon_props.py (with Dragon Isles' isles_props.py).

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import dcanyon_land as L  # noqa: E402
import ruin_mode  # noqa: E402

# The ruin (dragon_canyon_ruins.py; dcanyon_land.py lays its lap out): the blast tore the
# canyon apart; the lap keeps the hairpins, the broken Canyon Bridge (a jump) and the
# Skeleton Pass, then runs down the slip the blast cut, over the river on fused rock,
# home.
RUIN = ruin_mode.ON
TRACK_ID = "dragon_canyon_ruin" if RUIN else "dragon_canyon"

ROUTE = kit.route_points_by([(p[0], p[1], p[2], 0) for p in L.PATH], L.road_z, every=6.0, width=L.road_w)
S = L.S


def main():
    import dcanyon_props  # noqa: E402
    import dcanyon_town  # noqa: E402
    import emerald  # noqa: E402
    import isles_props  # noqa: E402

    c = kit.Course(TRACK_ID, "Dragon Canyon (Ruined)" if RUIN else "Dragon Canyon", "emerald_ruins" if RUIN else "emerald_kingdom")
    emerald.install(dcanyon_town, isles_props, dcanyon_props)
    c.route(ROUTE, width=14.0, bank=6.0)
    kerb = ("kerb_redwhite", "road")
    timber = ("weathered_timber", "wall")
    ashlar = ("fortress_wall", "wall")
    stone = ("stone_base", "wall")
    c.kinds = {
        "outpost": {"mat": "imperial_setts", "shoulder": 1.4, "shoulder_mat": kerb, "barrier": 1.2, "barrier_mat": ashlar},
        "ledge": {"mat": "frontier_road", "shoulder": 1.2, "shoulder_mat": kerb, "barrier": 1.1, "barrier_mat": timber},
        "bridge": {"mat": "imperial_setts", "shoulder": 0.8, "shoulder_mat": kerb, "barrier": 1.3, "barrier_mat": ashlar, "deck": 4.0,
                   "deck_mat": stone, "ground": False},
        "skeleton": {"mat": "frontier_road", "shoulder": 1.2, "shoulder_mat": kerb, "barrier": 1.1, "barrier_mat": timber},
        "quarry": {"mat": "frontier_road", "shoulder": 1.4, "shoulder_mat": ("quarry_dust", "dirt"), "barrier": 1.1,
                   "barrier_mat": ("scaffold_timber", "wall")},
        "quarry_open": {"mat": "frontier_road", "shoulder": 1.4, "shoulder_mat": ("quarry_dust", "dirt")},
        "cavern": {"mat": "imperial_setts", "shoulder": 1.0, "shoulder_mat": kerb, "barrier": 1.0, "barrier_mat": ashlar},
        "oasis": {"mat": "imperial_setts", "shoulder": 1.2, "shoulder_mat": kerb, "barrier": 1.0, "barrier_mat": ("fence_rail", "wall")},
        "river": {"mat": "frontier_road", "shoulder": 1.2, "shoulder_mat": kerb, "barrier": 1.1, "barrier_mat": timber},
    }
    zone_kind = {"outpost": "outpost", "hairpins": "ledge", "descent": "ledge", "skeleton": "skeleton", "quarry": "quarry",
                 "caverns": "cavern", "bridges": "ledge", "oasis": "oasis", "river": "river", "watchtower": "ledge", "twist": "ledge",
                 "slip": "slip"}
    if RUIN:
        c.kinds["slip"] = {"mat": "frontier_road", "shoulder": 1.6, "shoulder_mat": ("canyon_scree", "loose_sand")}
        c.kinds["kicker"] = {"mat": "imperial_setts", "shoulder": 0.8, "shoulder_mat": kerb, "deck": 4.0, "deck_mat": stone, "ground": False}

    def label(smp):
        if RUIN:
            a, b = L.BREAK
            if a <= smp.s <= b:
                return "gap"
            if a - 12 <= smp.s < a:
                return "kicker"
        x, y = smp.p.x, smp.p.y
        below = min(L.ground(x + ox, y + oy) for ox, oy in ((0, 0), (5, 0), (-5, 0), (0, 5), (0, -5)))
        if below < smp.p.z - 3.5:
            return "bridge"
        if L.open_sides(smp.s):
            return "quarry_open"
        return zone_kind[L.zone_of(smp.s)]

    specials = [r if r[2] != "kicker" else (r[0], r[1], "kicker", {"lift": lambda u, n: 0.9 * max(0.0, (u - (n - 8)) / 8) ** 2})
                for r in kit.runs(c, label) if r[2] != "ledge"]
    specials = [(r[0], r[1], None) if r[2] == "gap" else r for r in specials]
    c.roads(kit.plan(c, specials, "ledge", max_len=180.0))

    if RUIN:
        ruin_mode.DRESS(c, sys.modules[__name__])
        ruin_gameplay(c)
        c.finish()
        return
    import dcanyon_scenery  # noqa: E402

    dcanyon_scenery.build(c, sys.modules[__name__])
    c.finish()


def ruin_gameplay(c):
    """The ruin's boosts, pickups, respawn and checkpoints."""
    for at in (S["c1"] + 10, L.BREAK[0] - 34, S["k1"] + 10, S["f1"] - 30, S["f2"] + 10):
        c.zipper(at, 0)
    for at, across in ((S["h1b"] + 10, 0), (S["n3"] + 10, 0), (S["k2"] + 20, 3), (S["f1"] + 40, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in ((20.0, -4, "red"), (20.0, 4, "blue"), (S["h2a"] + 10, 0, "green"), (S["n3"] + 30, 0, "yellow"),
                            (S["k3"] + 10, -4, "rainbow"), (S["k3"] + 10, 4, "red"), (S["f1"] + 90, 0, "blue")):
        c.balloon(at, across, col)
    a, b = L.BREAK
    c.entity("respawn", **{"from": round(a - 20, 1), "to": round(b + 4, 1), "at": round(b + 18, 1)})
    c.checkpoints(extra=[S["h1a"], S["h2a"], S["n1"], S["n3"], S["k2"], S["f1"], S["f2"], S["x5"]], avoid=[(a - 14, b + 8)], height=10.0)


if __name__ == "__main__":
    main()
