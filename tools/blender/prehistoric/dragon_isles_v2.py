# Dragon Isles: Dragon Kingdom, course 1. A festival lap of a kingdom ruled by dragons.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/dragon_isles_v2.py      (the bpy module)
#
# A lap of about 2.7 km (around two minutes) on a sunny festival day, round a kingdom
# of karst mountains rising out of a turquoise lagoon. A great jade-and-gold dragon flies
# over it all; the royal palace stands on its mountain far to the north.
#
#   1  The Grand Ceremonial Gate: the start, under a great gate between dragon statues,
#      the palace ahead in the distance.
#   2  The Riverside Festival Village: market streets, a canal bridge, the festival
#      square on the waterfront, crowds cheering behind the barriers, boats.
#   3  The Cliffside Ascent: up the cliff on two stone ledges and a hairpin, waterfalls
#      falling past, a short tunnel through an outcrop.
#   4  The Great Waterfall Bridge: a stone bridge across the gorge, the great falls
#      thundering beside it.
#   5  The Temple Gardens: round the temple's gardens past lotus pools, pagodas and
#      cherry blossom (the Courtyard Passage, the shortcut, goes straight through).
#   6  The Sky Paths: south along a spine of karst pillars over the lagoon, from pillar
#      to pillar on high bridges; the dragon passes overhead on the long bridge.
#   7  The Lantern Harbour: down to the harbour, along the boardwalk past the docks and
#      the junks, over the harbour bridge.
#   8  The Ancient Dragon Passage: a short tunnel through the headland, carved with
#      dragons; a sealed door, old carvings faintly glowing.
#   9  The Grand Reveal: out onto the overlook, the whole kingdom spread out below.
#  10  The Royal Approach: down the royal avenue between guards and statues...
#  11  The Palace Finish: ...and under the Royal Gate onto the line.
#
# The land is isles_land.py (plain data, no Blender); the scenery isles_scenery.py and
# isles_town.py, the kit isles_props.py.

import math  # noqa: F401
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import isles_land as L  # noqa: E402

TRACK_ID = "dragon_isles_v2"

ROUTE = kit.route_points_by(L.PATH, L.road_z, every=8.0, width=L.road_w)
S = L.S


def main():
    c = kit.Course(TRACK_ID, "Dragonspire Keep (v2)", "dragon_isles")
    c.route(ROUTE, width=16.0, bank=7.0)
    curb = ("stone_curb", "road")
    bal = ("isle_balustrade", "wall")
    rail = ("red_rail", "wall")
    stone = ("stone_base", "wall")
    c.kinds = {
        "gate": {"mat": "isle_paving", "shoulder": 1.6, "shoulder_mat": curb},
        "village": {"mat": "village_cobble", "shoulder": 1.4, "shoulder_mat": curb, "barrier": 1.0, "barrier_mat": rail},
        "canal_bridge": {"mat": "isle_paving", "shoulder": 0.8, "shoulder_mat": curb, "barrier": 1.2, "barrier_mat": bal, "deck": 2.4,
                         "deck_mat": stone, "ground": False},
        "cliff": {"mat": "cliff_road", "shoulder": 1.2, "shoulder_mat": ("cliff_road", "dirt"), "barrier": 1.1, "barrier_mat": bal},
        "bridge": {"mat": "isle_paving", "shoulder": 1.0, "shoulder_mat": curb, "barrier": 1.3, "barrier_mat": bal, "deck": 4.5,
                   "deck_mat": stone, "ground": False},
        "temple": {"mat": "temple_flag", "shoulder": 1.6, "shoulder_mat": ("flowerbed", "grass")},
        "sky": {"mat": "isle_paving", "shoulder": 1.0, "shoulder_mat": curb, "barrier": 1.1, "barrier_mat": rail},
        "sky_bridge": {"mat": "isle_paving", "shoulder": 0.8, "shoulder_mat": curb, "barrier": 1.2, "barrier_mat": rail, "deck": 3.5,
                       "deck_mat": stone, "ground": False},
        "harbour": {"mat": "wood_dock", "shoulder": 1.0, "shoulder_mat": ("wood_dock", "road"), "barrier": 1.0,
                    "barrier_mat": ("weathered_timber", "wall")},
        "harbour_bridge": {"mat": "isle_paving", "shoulder": 0.8, "shoulder_mat": curb, "barrier": 1.2, "barrier_mat": bal, "deck": 3.0,
                           "deck_mat": stone, "ground": False},
        "passage": {"mat": "passage_stone", "shoulder": 1.0, "shoulder_mat": ("passage_stone", "dirt")},
        "royal": {"mat": "royal_carpet", "shoulder": 2.0, "shoulder_mat": curb},
    }
    zone_kind = {"gate": "gate", "village": "village", "cliff": "cliff", "bridge": "cliff", "temple": "temple", "sky": "sky",
                 "harbour": "harbour", "passage": "passage", "reveal": "cliff", "royal": "royal"}
    bridge_kind = {3: "canal_bridge", 4: "canal_bridge", 13: "bridge", 14: "bridge", 15: "bridge", 25: "sky_bridge", 26: "sky_bridge",
                   27: "sky_bridge", 28: "sky_bridge", 29: "sky_bridge", 30: "sky_bridge", 33: "harbour_bridge", 34: "harbour_bridge",
                   35: "harbour_bridge"}

    def label(smp):
        s = smp.s
        seg = L.seg_of(s)
        x, y = smp.p.x, smp.p.y
        if seg in bridge_kind:
            below = min(L.ground(x + ox, y + oy) for ox, oy in ((0, 0), (5, 0), (-5, 0), (0, 5), (0, -5)))
            if below < smp.p.z - 3.5:
                return bridge_kind[seg]
        return zone_kind[L.zone_of(s)]

    specials = [r for r in kit.runs(c, label) if r[2] != "gate"]
    c.roads(kit.plan(c, specials, "gate", max_len=200.0))

    import isles_scenery  # noqa: E402

    isles_scenery.build(c, sys.modules[__name__])
    c.finish()


if __name__ == "__main__":
    main()
