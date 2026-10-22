# Snow Dragon Pass: Dragon Kingdom, course 3. The kingdom's highest mountains in a
# blizzard, and a lap that splits twice: half of it shared, half of it a choice of roads.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/snow_dragon_pass.py      (the bpy module)
#
# A network of mountain roads (about 2.35-2.4 km a lap, whichever way you go):
#
#    1  The Frozen Gate: the start, just below the Dragon Citadel's gate.
#    2  The Windy Village: down through the village, past the ration lines.
#    3  First split.
#       The High Cliff Road (main): a switchback up the mountain's face, along the
#       exposed ledge past the Dragon Overlook, down to the crossing. Short and tight.
#       The Frozen Supply Road: round the mountain's foot past the depots and the labour
#       camps, through the blue ice cavern. Wide and flowing, a little longer.
#    4  Starvation Road: the shared supply corridor, the storehouses under guard.
#    5  The Broken Bridges over the frozen gorge.
#    6  The Avalanche Run: down the windswept pass.
#    7  Second split.
#       The Monastery Ridge (main): a switchback up round the Monastery Mount, east over
#       its bridge, a steep descending exit.
#       The Frozen Aqueduct: straight on and down along the old water channels, under the
#       monastery's bridge, out past the frozen falls, a tunnel bend back. Faster.
#    8  The Final Ascent: up past the guardian dragons to the Dragon Citadel's gate.
#
# The main route is Cliff + Ridge; the other three combinations are lap routes of their
# own (route.json, track.json's lapRoutes) for the rivals, and every branch has its own
# checkpoints. The land is snow_land.py (plain data, no Blender); the land, branch roads
# and gameplay snow_scenery.py; the buildings, people, weather and dragon snow_town.py.

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import snow_land as L  # noqa: E402

TRACK_ID = "snow_dragon_pass"
M = L.MAIN

ROUTE = kit.route_points_by([(p[0], p[1], 0.0, 0) for p in M.path], lambda d, seg=None: L.road_z(M, d), every=6.0,
                            width=lambda d, seg=None: L.road_w(M, d))


def main():
    c = kit.Course(TRACK_ID, "Snow Dragon Pass", "snow_dragon_pass")
    c.route(ROUTE, width=16.0, bank=5.0)
    snowbank = ("sdp_snowbank", "packed_snow")
    timber = ("weathered_timber", "wall")
    parapet = ("sdp_aqueduct", "wall")
    c.kinds = {
        # The citadel's paved approach and the Frozen Gate: red walls either side.
        "gate": {"mat": "sdp_setts", "shoulder": 1.3, "shoulder_mat": ("kerb_redwhite", "road"), "barrier": 1.2,
                 "barrier_mat": ("sdp_redwall", "wall")},
        # Through the village: paved, low timber fences.
        "village": {"mat": "sdp_setts", "shoulder": 1.3, "shoulder_mat": snowbank, "barrier": 0.9, "barrier_mat": timber},
        # The mountain road: packed snow over the setts, timber rails.
        "road": {"mat": "sdp_road", "shoulder": 1.3, "shoulder_mat": snowbank, "barrier": 1.0, "barrier_mat": timber},
        # Cut into the cliff: stone parapets, a rock edge under the drop side.
        "cliff": {"mat": "sdp_road", "shoulder": 1.3, "shoulder_mat": snowbank, "barrier": 1.2, "barrier_mat": parapet, "deck": 4.0,
                  "deck_mat": ("sdp_slate", "wall")},
        # Over a drop: stone bridges with parapets.
        "bridge": {"mat": "sdp_setts", "shoulder": 1.3, "shoulder_mat": ("sdp_aqueduct", "road"), "barrier": 1.3, "barrier_mat": parapet,
                   "deck": 4.0, "deck_mat": parapet, "ground": False},
        # Where a branch leaves or joins: open, no rails.
        "open": {"mat": "sdp_road", "shoulder": 1.3, "shoulder_mat": snowbank},
    }
    zone_kind = {"gate": "gate", "village": "village", "cliff": "cliff", "starvation": "road", "avalanche": "road", "ridge": "cliff",
                 "ascent": "road"}

    def label(smp):
        x, y = smp.p.x, smp.p.y
        below = min(L.ground(x + ox, y + oy) for ox, oy in ((0, 0), (5, 0), (-5, 0), (0, 5), (0, -5)))
        if below < smp.p.z - 3.5:
            return "bridge"
        # Over a branch road passing underneath (and well clear of it either side, so the
        # land meets the lower road, not this one).
        for d, z, w in L.roads_near(x, y, 40.0):
            if z < smp.p.z - 6.0 and d < smp.w / 2 + w / 2 + 12.0:
                return "bridge"
        if L.junction_open(smp.s):
            return "open"
        return zone_kind[L.zone_of(smp.s)]

    specials = [r for r in kit.runs(c, label) if r[2] != "road"]
    c.roads(kit.plan(c, specials, "road", max_len=180.0))

    import snow_scenery  # noqa: E402

    sc = snow_scenery.build(c, sys.modules[__name__])
    c.finish(extra={"lapRoutes": sc.lap_ids})


if __name__ == "__main__":
    main()
