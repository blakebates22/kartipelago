# Dragonspire Keep in ruins: Adventure's treasure map course for the Dragon Kingdom's
# castle (?track=dragon_isles_ruin; in dev builds the course's menu entry asks Standard or
# Ruined).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/dragon_isles_ruins.py      (the bpy module)
#
# The Chosen One's sacrifice remade the kingdom (Blake: the Dragon Kingdom's ruins are new
# courses, every change explained by that blast: land lifted, split, flipped or fused; at
# least half the lap). Past the gate and the town's first bend the market streets are
# torn up, so the lap turns south across the lowland, jumps the split the blast tore in
# it, swings east across the lake bed it heaved up dry in tilted slabs, rounds the foot
# of the Beacon crag (its spiral road is gone), and comes home by the harbour, the
# passage and the royal approach as ever. About 1110 m (the full lap is 2161 m).
#
# dragon_isles.py lays the lap out (ruin_mode.ON) and shapes the split and the heaved lake
# bed; the castle, the town, the cliffs, the keep, the harbour and the pillars are the
# course's own scenery code along the standard lap (ruin_kit.ghost); here are the torn
# streets, the slabs and the blast's scorch.

import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ruin_mode  # noqa: E402

ruin_mode.ON = False
import dragon_isles as std  # noqa: E402

sys.modules.pop("dragon_isles")
ruin_mode.ON = True
di = importlib.import_module("dragon_isles")

import keep_scenery as ks  # noqa: E402
import props  # noqa: E402
import ruin_kit as rk  # noqa: E402
from aurora_scenery import game_entity  # noqa: E402
from course_kit import rnd  # noqa: E402

BURNS = [(40.0, 160.0, 26.0), (70.0, 230.0, 22.0), (90.0, 40.0, 24.0), (180.0, -60.0, 30.0), (250.0, -80.0, 24.0), (100.0, 300.0, 24.0)]


class _Map:
    """The standard lap's landmarks' distances as the ruin's (for the keep's light and
    air: its tunnel, its harbour)."""

    def __init__(self, m):
        self.TO_ROAD = m.TO_ROAD
        far = m.LENGTH + 100.0
        self.SEG = {29: m.SEG[12], 30: m.SEG[13], 24: m.SEG[7], 28: m.SEG[11], 11: far, 13: far + 10.0}


def torn_streets(c, sc, fires):
    """Where the market streets ran (the standard lap's S through them): torn up, the
    paving in heaped slabs, fires in the wreck of the stalls."""
    S = std.SEG
    k = 0
    with rk.ghost(c, GHOST[0]):
        pts = []
        s = S[2]
        while s < S[7]:
            q = c.at(std.TO_ROAD(s))
            pts.append((q.p.x, q.p.y))
            s += 12.0
    for x, y in pts:
        k += 1
        if not props.clear_of_road(c, x, y, 4.0):
            continue
        rk.rubble_heap(c, x, y, sc.ground, n=5, spread=4.0, size=2.4, role="both", seed=k)
        if k % 3 == 0:
            fires.append((x, y, sc.ground(x, y) + 1.5))


def slabs(c, m, sc, fires):
    """The heaved lake bed's broken edges: slabs tipped up on end round it, weed and
    shells drying on them, a few still steaming."""
    x0, x1, y0, y1 = m.HEAVE
    for k in range(26):
        x = x0 + (x1 - x0) * rnd(k * 1.7 + 2)
        y = y0 + (y1 - y0) * rnd(k * 2.9 + 4)
        if not props.clear_of_road(c, x, y, 5.0):
            continue
        z = sc.ground(x, y)
        r = c.rock_mass("Heaved Slab %d" % k, x, y, 4.0 + 5.0 * rnd(k), 1.6 + 1.2 * rnd(k + 3), z + 3.0 + 6.0 * rnd(k * 5), z0=z - 3.0, n=6,
                        seed=300 + k, angle=k * 1.1)
        c.paint_rock(r, ("keep_rock", "wall"), ("keep_shore", "dirt"))
        if k % 5 == 0:
            game_entity(c, "steam", x, y, z + 1.0)
    # Down the split: fires deep in it.
    for x, y in m.SPLIT_LINE:
        fires.append((x, y, -10.0))


GHOST = []


def dress(c, m, ter):
    GHOST.append(rk.ghost_route(c, std.ROUTE, width=16.0, bank=7.0))
    with rk.ghost(c, GHOST[0]):
        sc = ks.build(c, std, ter, ruin=True)
        std.pillars(c, std)
    fires = []
    torn_streets(c, sc, fires)
    slabs(c, m, sc, fires)
    fires += rk.scorch(c, BURNS, sc.ground, lambda x, y: ks.clear_of(c, x, y, 4.0), per=5)
    print("cleared off the new road:", rk.clear_new_road(c, ("Castle", "Gate", "Town", "Cliff", "Courtyard", "Keep", "Walls", "Spires", "Beacon", "Harbour",
                                                            "Passage", "Royal", "Nature")))
    sc.flames = [p for p in sc.flames if ks.clear_of(c, p[0], p[1], 1.0)]
    for x, y, z in sc.flames:
        game_entity(c, "torch", x, y, z)
    for x, y, z, top, w, h in sc.falls:
        gx, gy, gz = c.game(x, y, z)
        c.entity("waterfall", x=gx, y=gy, z=gz, top=round(top, 1), width=round(w, 1), heading=round(h, 3))
    rk.emit(c, fires)
    sc.flames += fires
    sc.dk = _Map(m)
    ks.atmosphere(c, sc.dk)
    ks.light(sc)
    c.merge_props(("Wreck",))
    c.entity("ashfall", rate=18, radius=40)
    print("keep ruin: fires", len(fires), "lap", round(c.length, 1))


ruin_mode.DRESS = dress

if __name__ == "__main__":
    di.main()
