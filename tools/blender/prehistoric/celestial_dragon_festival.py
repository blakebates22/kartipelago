# Celestial Dragon Festival: Dragon Kingdom, course 4. The kingdom's sacred heart on the
# night of its greatest festival: the grand finale of the dragon kingdom.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/celestial_dragon_festival.py      (the bpy module)
#
# A lap of about 2.9 km (just under two minutes) round the Palace Mount, at night, with
# the sky filling with fireworks lap by lap (the game's festival: game/festival.ts).
#
#    1  The Festival Gate: the start, under the great ceremonial arch, east along the
#       broad straight on the gate's terrace, the crowds packed either side.
#    2  The Lantern Market Curve: sweeping down through the night market to the water.
#    3  The Waterfall Bridge: north over the lagoon on a long stone bridge, waterfalls
#       pouring off the islands either side, lantern boats beneath.
#    4  The Dragon Promenade: west across the great plaza of worship, the golden dragon
#       monuments, the dancers, the altar, the kneeling crowds.
#    5  The Celestial Climb: up the mountain's north face in sweeping S-bends.
#    6  The Star Bridge: west across the Cloud Chasm, high over a sea of cloud, the stars
#       all round; parapets only at its ends.
#    7  The Observatory Spiral: right, all the way round the Observatory Pinnacle and its
#       great golden rings, climbing, and out over the Star Bridge's far end.
#    8  The Palace Terraces: through the palace's upper gardens and courtyards.
#    9  The Procession Causeway: down the broad processional way, thousands watching.
#   10  The Fireworks Overlook: out on the cliff's edge, the whole kingdom below.
#   11  The Final Ascension: up round the palace's western bastion under golden arches...
#   12  The Grand Finale: ...and down onto the straight, under the gate, to the line.
#
# The land is cdf_land.py (plain data, no Blender); the land, water and gameplay
# cdf_scenery.py; the city, the palace, the observatory, the people, the dragon and the
# festival cdf_town.py; the kit cdf_props.py (with Dragon Isles' isles_props.py).

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import cdf_land as L  # noqa: E402

TRACK_ID = "celestial_dragon_festival"

ROUTE = kit.route_points_by([(p[0], p[1], p[2], 0) for p in L.PATH], L.road_z, every=6.0, width=L.road_w)
S = L.S


def main():
    c = kit.Course(TRACK_ID, "Celestial Dragon Festival", "celestial_dragon_festival")
    c.route(ROUTE, width=18.0, bank=6.0)
    kerb = ("cdf_kerb", "road")
    bal = ("cdf_balustrade", "wall")
    lanterns = ("cdf_lantern_rail", "wall")
    marble = ("cdf_marble", "wall")
    c.kinds = {
        # The gate's terrace and the finish: festival paving, lantern rails.
        "gate": {"mat": "cdf_paving", "shoulder": 1.6, "shoulder_mat": kerb, "barrier": 1.1, "barrier_mat": lanterns},
        # The market: paving, low red rails.
        "market": {"mat": "cdf_paving", "shoulder": 1.4, "shoulder_mat": kerb, "barrier": 1.0, "barrier_mat": lanterns},
        # Over water or a drop: white stone bridges with gilded balustrades.
        "bridge": {"mat": "cdf_paving", "shoulder": 1.2, "shoulder_mat": kerb, "barrier": 1.3, "barrier_mat": bal, "deck": 4.5,
                   "deck_mat": marble, "ground": False},
        # The plaza and the terraces: paving between balustrades.
        "plaza": {"mat": "cdf_paving", "shoulder": 1.6, "shoulder_mat": kerb, "barrier": 1.0, "barrier_mat": bal},
        # The high roads: celestial blue stone, gilded balustrades.
        "high": {"mat": "cdf_celestial", "shoulder": 1.2, "shoulder_mat": kerb, "barrier": 1.2, "barrier_mat": bal},
        "high_bridge": {"mat": "cdf_celestial", "shoulder": 1.0, "shoulder_mat": kerb, "barrier": 1.3, "barrier_mat": bal, "deck": 5.0,
                        "deck_mat": marble, "ground": False},
        # The Star Bridge's open middle: no parapets at all.
        "star_open": {"mat": "cdf_celestial", "shoulder": 1.0, "shoulder_mat": kerb, "deck": 5.0, "deck_mat": marble, "ground": False},
        # The processional way and the finale: the crimson runner, lantern rails.
        "royal": {"mat": "cdf_royal", "shoulder": 1.6, "shoulder_mat": kerb, "barrier": 1.1, "barrier_mat": lanterns},
        "royal_bridge": {"mat": "cdf_royal", "shoulder": 1.2, "shoulder_mat": kerb, "barrier": 1.3, "barrier_mat": bal, "deck": 4.5,
                         "deck_mat": marble, "ground": False},
    }
    zone_kind = {"gate": "gate", "market": "market", "falls": "plaza", "promenade": "plaza", "climb": "high", "star": "high",
                 "observatory": "high", "terraces": "plaza", "causeway": "royal", "overlook": "plaza", "ascension": "royal",
                 "finale": "royal"}
    bridge_kind = {"gate": "bridge", "market": "bridge", "plaza": "bridge", "high": "high_bridge", "royal": "royal_bridge"}

    def label(smp):
        x, y = smp.p.x, smp.p.y
        s = smp.s
        if L.STAR_OPEN[0] <= s <= L.STAR_OPEN[1]:
            return "star_open"
        kind = zone_kind[L.zone_of(s)]
        below = min(L.ground(x + ox, y + oy) for ox, oy in ((0, 0), (5, 0), (-5, 0), (0, 5), (0, -5)))
        if below < smp.p.z - 3.5:
            return bridge_kind[kind]
        # Over another stretch of the lap (the spiral's way out over the Star Bridge).
        for d, s2 in L.roads_near(x, y, 30.0):
            if L.road_z(s2) < smp.p.z - 6.0 and d < smp.w / 2 + 16.0:
                return bridge_kind[kind]
        return kind

    specials = [r for r in kit.runs(c, label) if r[2] != "gate"]
    c.roads(kit.plan(c, specials, "gate", max_len=200.0))

    import cdf_scenery  # noqa: E402

    cdf_scenery.build(c, sys.modules[__name__])
    c.finish()


if __name__ == "__main__":
    main()
