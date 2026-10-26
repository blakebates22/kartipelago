# Emberdeep Hold in ruins: Adventure's treasure map course for the Dragon Kingdom's
# mountain fortress (?track=snow_dragon_pass_ruin; in dev builds the course's menu entry
# asks Standard or Ruined).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/snow_dragon_pass_ruins.py      (the bpy module)
#
# The Chosen One's sacrifice split the mountain in two (Blake: the Dragon Kingdom's ruins
# are new courses, every change explained by the blast; at least half the lap). Down out
# of the Outer Gate and the lower town as ever, then into the split and straight through
# the mountain's heart between its two halves, out onto the ridge the blast heaved up on
# its west side (across the gorge), south along it, and round to the gate where the
# bastion stood: the blast threw it down. About 960 m (the full lap is 1902 m).
#
# snow_dragon_pass.py lays the lap out (ruin_mode.ON) and cuts the split and the ridge
# into the land; the hold, the town, the ramparts, the hall and the courtyard are the
# course's own scenery code along the standard lap (ruin_kit.ghost); here are the
# bastion's wreck, embers in the split, and the fires.

import importlib
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ruin_mode  # noqa: E402

ruin_mode.ON = False
import snow_dragon_pass as std  # noqa: E402

sys.modules.pop("snow_dragon_pass")
ruin_mode.ON = True
sdp = importlib.import_module("snow_dragon_pass")

import ember_scenery as es  # noqa: E402
import props  # noqa: E402
import ruin_kit as rk  # noqa: E402
from aurora_scenery import game_entity  # noqa: E402
from course_kit import rnd  # noqa: E402

BURNS = [(60.0, 20.0, 22.0), (150.0, 0.0, 20.0), (-40.0, 150.0, 24.0), (-30.0, 260.0, 22.0)]


class _Map:
    """The hold's air, for the ruin: no falls on its lap."""

    def __init__(self, m):
        self.TO_ROAD = m.TO_ROAD
        far = m.LENGTH + 100.0
        self.SEG = {20: far, 27: far + 10.0}
        self.SUPPLY, self.AQUEDUCT = std.SUPPLY, std.AQUEDUCT


def bastion_wreck(c, m, sc, fires):
    """The bastion, thrown down: its blocks strewn round where it stood, clear of the
    road; embers in the split's floor."""
    bx, by = std.BASTION
    for k in range(18):
        a = k * 2.39996
        r = 8.0 + 30.0 * rnd(k * 1.3 + 2)
        x, y = bx + r * math.cos(a), by + r * math.sin(a)
        if not props.clear_of_road(c, x, y, 4.0):
            continue
        z = sc.ground(x, y)
        blk = c.rock_mass("Bastion Block %d" % k, x, y, 2.5 + 3.0 * rnd(k), 2.0 + 2.0 * rnd(k + 5), z + 2.0 + 4.0 * rnd(k * 3), z0=z - 2.0, n=6,
                          seed=500 + k, angle=k)
        c.paint_rock(blk, ("ember_rock", "wall"), ("ember_moss", "rubble"))
        if k % 4 == 0:
            fires.append((x, y, z + 1.0))
    # Embers glowing along the split's walls.
    for k, (x, y, z) in enumerate(m.NEW[::8]):
        if k % 2:
            fires.append((x + 12.0 * (1 if k % 4 == 1 else -1), y, z + 2.0))


def dress(c, m, ter):
    g = rk.ghost_route(c, std.ROUTE, width=16.0, bank=7.0)
    z1 = (std.road_z(std.SEG[6], 6), std.road_z(std.SEG[16], 16))
    z2 = (std.road_z(std.SEG[27], 27), std.road_z(std.SEG[32], 32))
    with rk.ghost(c, g):
        sc = es.build(c, std, ter, z1, z2, ruin=True)
    fires = []
    bastion_wreck(c, m, sc, fires)
    fires += rk.scorch(c, BURNS, sc.ground, lambda x, y: props.clear_of_road(c, x, y, 4.0), per=4)
    print("cleared off the new road:", rk.clear_new_road(c, ("Castle", "Gate", "Town", "Approach", "Hall", "Ramparts", "Causeway", "Courtyard", "Tunnel",
                                                            "Fortress", "Nature")))
    sc.flames = [p for p in sc.flames if props.clear_of_road(c, p[0], p[1], 1.0)]
    for x, y, z in sc.flames:
        game_entity(c, "torch", x, y, z)
    rk.emit(c, fires)
    sc.flames += fires
    c.entity("storm", period=8.0, spread=4.0, distance=900.0, color="#cfd8ff")
    es.atmosphere(c, _Map(m), z1, z2)
    es.light(sc)
    c.merge_props(("Wreck",))
    c.entity("ashfall", rate=18, radius=40)
    print("hold ruin: fires", len(fires), "lap", round(c.length, 1))


ruin_mode.DRESS = dress

if __name__ == "__main__":
    sdp.main()
