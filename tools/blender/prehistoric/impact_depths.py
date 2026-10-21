# Impact Depths: Desert World, course 4. Down through an asteroid's crater into the world
# under the desert, and back up into the sun.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/impact_depths.py      (the bpy module)
#
# A lap of about 2.6 km (around two minutes). Long ago an asteroid fell on the desert;
# its crater broke open a hidden world beneath. The race starts on the sunlit desert
# and goes down, each level stranger than the last, then climbs back out:
#
#   1  The Desert Approach: the start, on packed dirt between red mesas, under a rustic
#      timber arch; the asteroid smoking in its crater straight ahead.
#   2  The Colossal Crater: round the rim, then down its fractured inner wall on broad
#      banked curves, the glowing asteroid below, into a cave mouth at the bottom.
#   3  The Crystal Descent: a warm ochre hall of cyan, violet and rose crystal; a stone
#      bridge over the underground river, a waterfall, the blue lake.
#   4  The Lost World: a vast jungle cavern lit by shafts of sunlight through holes in
#      its roof: ferns and cycads, a turquoise lake, ruins, triceratops grazing, raptors
#      darting across the road, pterosaurs overhead, and a sauropod by the river bridge.
#   5  The Volcanic Depths: a tunnel down into black rock and lava: causeways between
#      lava rivers, lava falls, steam, lava geysers on a beat, rocks falling from the roof.
#   6  The Dragon's Lair: round the dragon's crag above a lake of lava, the great beast
#      watching, roaring, breathing fire across the broad bridge over the lava gorge.
#   7  The Heart of the Earth: through a portal into the shaft at the world's centre,
#      round the great pulsing core crystal (its ring road a boost), and...
#   8  The Final Ascent: up a terrace spiralling round the shaft's wall, from crystal to
#      sandstone to sunlight, out onto the desert, one fast curve to the line.
#
#   The Ancient Way (the shortcut): straight on where the main road turns into the Lost
#   World, through a narrow ruined gateway, along a stone causeway across a hidden
#   cavern's still black pool, and out onto the volcanic causeway.
#
# The land is impact_land.py (plain data, no Blender); the scenery impact_scenery.py and
# impact_life.py, the kit impact_props.py.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import impact_land as L  # noqa: E402

TRACK_ID = "impact_depths"

ROUTE = kit.route_points_by(L.PATH, L.road_z, every=8.0, width=L.road_w)
S = L.S


def main():
    c = kit.Course(TRACK_ID, "Impact Depths", "impact_depths")
    c.route(ROUTE, width=16.0, bank=7.0)
    stone = ("bridge_stone", "wall")
    c.kinds = {
        "desert": {"mat": "depths_road", "surface": "packed_dirt", "shoulder": 2.2, "shoulder_mat": ("desert_sand", "loose_sand")},
        "crater": {"mat": "crater_road", "shoulder": 1.6, "shoulder_mat": ("crater_ground", "dirt"), "barrier": 0.8,
                   "barrier_mat": ("crater_rock", "wall")},
        "crystal": {"mat": "cave_road", "shoulder": 1.6, "shoulder_mat": ("flowstone", "dirt")},
        "crystal_bridge": {"mat": "bridge_stone", "shoulder": 0.8, "shoulder_mat": ("bridge_stone", "road"), "barrier": 1.2,
                           "barrier_mat": stone, "deck": 3.0, "deck_mat": stone, "ground": False},
        "jungle": {"mat": "jungle_track", "surface": "packed_dirt", "shoulder": 1.8, "shoulder_mat": ("fern_floor", "grass")},
        "jungle_bridge": {"mat": "causeway_stone", "shoulder": 0.8, "shoulder_mat": ("causeway_stone", "road"), "barrier": 1.2,
                          "barrier_mat": ("ruin_moss", "wall"), "deck": 3.0, "deck_mat": ("ruin_moss", "wall"), "ground": False},
        "volcanic": {"mat": "basalt_slab", "shoulder": 1.5, "shoulder_mat": ("lava_crust", "dirt")},
        "volcanic_bridge": {"mat": "basalt_slab", "shoulder": 0.8, "shoulder_mat": ("basalt_slab", "road"), "barrier": 1.1,
                            "barrier_mat": ("black_rock", "wall"), "deck": 3.0, "deck_mat": ("black_rock", "wall"), "ground": False},
        "lair": {"mat": "lair_road", "shoulder": 1.4, "shoulder_mat": ("ember_ash", "dirt")},
        "lair_bridge": {"mat": "lair_road", "shoulder": 0.8, "shoulder_mat": ("lair_road", "road"), "barrier": 1.2,
                        "barrier_mat": ("lair_rock", "wall"), "deck": 4.0, "deck_mat": ("lair_rock", "wall"), "ground": False},
        "core": {"mat": "core_road", "shoulder": 1.0, "shoulder_mat": ("core_glass", "dirt"), "barrier": 1.0,
                 "barrier_mat": ("core_glass", "wall")},
        "ascent": {"mat": "spiral_road", "shoulder": 1.0, "shoulder_mat": ("spiral_road", "dirt"), "barrier": 1.0,
                   "barrier_mat": ("strata_cream", "wall")},
        "ascent_bridge": {"mat": "spiral_road", "shoulder": 1.0, "shoulder_mat": ("spiral_road", "road"), "barrier": 1.0,
                          "barrier_mat": ("strata_cream", "wall"), "deck": 3.0, "deck_mat": ("strata_orange", "wall"), "ground": False},
    }
    bridge_kind = {5: "crystal_bridge", 6: "crystal_bridge", 11: "jungle_bridge", 12: "jungle_bridge", 13: "volcanic_bridge", 14: "lair_bridge",
                   15: "lair_bridge", 16: "lair_bridge", 18: "ascent_bridge"}
    road_kind = {"desert": "desert", "crater": "crater", "crystal": "crystal", "jungle": "jungle", "volcanic": "volcanic",
                 "lair": "lair", "core": "core", "ascent": "ascent"}

    def label(smp):
        s = smp.s
        seg = L.seg_of(s)
        x, y = smp.p.x, smp.p.y
        if seg in bridge_kind:
            below = min(L.ground(x + ox, y + oy)[0] for ox, oy in ((0, 0), (4, 0), (-4, 0), (0, 4), (0, -4)))
            if below < smp.p.z - 3.5:
                return bridge_kind[seg]
        z = L.zone_of(s)
        if z == "core" and seg >= 18:
            return "ascent"
        return road_kind[z]

    specials = [r for r in kit.runs(c, label) if r[2] != "desert"]
    c.roads(kit.plan(c, specials, "desert", max_len=200.0))

    import impact_scenery  # noqa: E402

    impact_scenery.build(c, sys.modules[__name__])
    c.finish()


if __name__ == "__main__":
    main()
