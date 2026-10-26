# Moonstone Kingdom in ruins: Adventure's treasure map course for the Dragon Kingdom's
# moonlit palace (?track=celestial_dragon_festival_ruin; in dev builds the course's menu
# entry asks Standard or Ruined).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/celestial_dragon_festival_ruins.py      (the bpy module)
#
# The Chosen One's sacrifice split the Palace Mount (Blake: the Dragon Kingdom's ruins are
# new courses, every change explained by the blast; at least half the lap). From the gate
# the lap turns north into the split and climbs through the mount's broken heart, runs
# west along the Cloud Chasm's edge (the blast tore a crack across it: leap it), and
# comes down past the palace terraces, the overlook and the bastion to the line. About
# 1020 m (the full lap is 2040 m).
#
# celestial_dragon_festival.py lays the lap out (ruin_mode.ON) and cuts the split and the
# crack into the land; the town, the shrine, the palace, the observatory and the terraces
# are the course's own scenery code along the standard lap (ruin_kit.ghost); here are
# the fallen palace stones, crystal shards and the fires.

import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ruin_mode  # noqa: E402

ruin_mode.ON = False
import celestial_dragon_festival as std  # noqa: E402

sys.modules.pop("celestial_dragon_festival")
ruin_mode.ON = True
cdf = importlib.import_module("celestial_dragon_festival")

import moon_scenery as ms  # noqa: E402
import props  # noqa: E402
import ruin_kit as rk  # noqa: E402
from aurora_scenery import game_entity  # noqa: E402
from course_kit import rnd  # noqa: E402

BURNS = [(120.0, 120.0, 24.0), (110.0, 260.0, 24.0), (20.0, 350.0, 22.0), (-89.0, 220.0, 22.0)]


class _Map:
    """The kingdom's air, for the ruin: no lake or chasm stretch on its lap."""

    def __init__(self, m):
        self.TO_ROAD = m.TO_ROAD
        far = m.LENGTH + 100.0
        self.SEG = {4: far, 9: far + 5.0, 21: far + 10.0, 24: far + 15.0}


def split_stones(c, m, sc, fires):
    """Blocks of the mount's rock and the palace's moonstone tumbled down the split's
    sides, clear of the road; crystal shards glowing in them."""
    k = 0
    for x, y, z in m.NEW[4::3]:
        for side in (-1, 1):
            k += 1
            if k % 3:
                continue
            px, py = x + side * (16.0 + 10.0 * rnd(k)), y + (rnd(k * 1.7) - 0.5) * 10.0
            if not props.clear_of_road(c, px, py, 4.0):
                continue
            g = sc.ground(px, py)
            blk = c.rock_mass("Split Block %d" % k, px, py, 2.5 + 3.0 * rnd(k), 2.0 + 2.5 * rnd(k + 2), g + 2.0 + 5.0 * rnd(k * 3), z0=g - 2.0, n=6,
                              seed=600 + k, angle=k * 0.9)
            c.paint_rock(blk, ("moon_rock", "wall"), ("moon_grass", "grass"))
            if k % 4 == 0:
                sc.glows.append((px, py, g + 3.0))
            if k % 6 == 0:
                fires.append((px, py, g + 1.0))
    cx, cy = m.CRACK
    for j in (-1, 1):
        fires.append((cx, cy + j * 12.0, -20.0))


def dress(c, m, ter):
    g = rk.ghost_route(c, std.ROUTE, width=16.0, bank=6.0)
    with rk.ghost(c, g):
        sc = ms.build(c, std, ter, ruin=True)
    fires = []
    split_stones(c, m, sc, fires)
    fires += rk.scorch(c, BURNS, sc.ground, lambda x, y: props.clear_of_road(c, x, y, 4.0), per=4)
    print("cleared off the new road:", rk.clear_new_road(c, ("Castle", "Gate", "Town", "Lake", "Shore", "Courtyard", "Climb", "Islands", "Observatory",
                                                            "Palace", "Terraces", "Nature")))
    sc.flames = [p for p in sc.flames if props.clear_of_road(c, p[0], p[1], 1.0)]
    for x, y, z in sc.flames:
        game_entity(c, "torch", x, y, z)
    for x, y, z in sc.glows:
        game_entity(c, "glow", x, y, z, color="#8ab8ff")
    c.entity("sparkles", rate=20, radius=34)
    rk.emit(c, fires)
    sc.flames += fires
    ms.atmosphere(c, _Map(m))
    ms.light(sc)
    c.merge_props(("Wreck",))
    c.entity("ashfall", rate=14, radius=40)
    print("moon ruin: fires", len(fires), "lap", round(c.length, 1))


ruin_mode.DRESS = dress

if __name__ == "__main__":
    cdf.main()
