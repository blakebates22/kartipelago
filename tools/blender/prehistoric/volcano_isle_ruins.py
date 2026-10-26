# Volcano Isle in ruins: Adventure's treasure map course for the volcanic island
# (?track=volcano_isle_ruin; in dev builds the course's menu entry asks Standard or Ruined).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/volcano_isle_ruins.py      (the bpy module)
#
# Tidewyrm's raid woke the volcano (Blake: Tropic Isles ruins change little: one decent
# change each, plus rubble to avoid). A flow came down over the hot-spring flats and
# buried the road there; the new road runs on its cooled crust 7 m east, a wider sweeper
# onto the flats and a tighter turn up into the jungle, live lava beside it (cut the
# corner and you're in it). Volcanic bombs lie in the road in three places; the
# village's huts burnt. The rest of the lap is the course's own. About 880 m.
#
# volcano_isle.py lays the lap out (ruin_mode.ON) and lays the flow into the land; the
# beach, the springs, the jungle, the tube, the ledge, the lagoon and the village are the
# course's own scenery code (isle_scenery.py); here are the bombs, the flow's glow and
# steam, and the fires.

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ruin_mode  # noqa: E402

ruin_mode.ON = True
import volcano_isle as vi  # noqa: E402

import isle_scenery as iss  # noqa: E402
import ruin_kit as rk  # noqa: E402
from aurora_scenery import game_entity  # noqa: E402

BURNS = [(-30.0, 10.0, 12.0), (60.0, 30.0, 14.0)]


def off_the_flow(c, m):
    """Scenery the flow buried: anything standing on it is gone."""
    import bpy

    gone = 0
    for name in ("Beach", "Springs", "Jungle"):
        for ob in list(c.coll(name).objects):
            x, y = ob.matrix_world.translation.x, ob.matrix_world.translation.y
            if m.lava_d(x, y) < 1.0:
                bpy.data.objects.remove(ob, do_unlink=True)
                gone += 1
    return gone


def flow(c, m, sc, fires):
    """The flow's glow and steam, and its source: a breach in the hill's flank above the
    flats, still smoking."""
    pts = m.OLD_FLATS
    for k, (x, y) in enumerate(pts[::4]):
        z = sc.ground(x, y)
        fires.append((x, y, z + 0.6))
        if k % 3 == 1:
            game_entity(c, "steam", x, y, z + 0.5)
    x, y = pts[-1]
    rk.rubble_heap(c, x - 12.0, y + 10.0, sc.ground, n=8, spread=5.0, size=2.4, role="both", seed=91)


def bombs(c, m, sc):
    """Volcanic bombs in the road, a third of the way across: drive round."""
    S = m.TO_ROAD
    for k, (s, side) in enumerate(((S(m.SEG[2]) + 12, 1), (S(m.SEG[8]) + 10, -1), (S(m.SEG[20]) + 40, 1))):
        q = c.at(s)
        p = q.side(side * (q.w / 2 - 3.2))
        rk.rubble_heap(c, p.x, p.y, sc.ground, n=5, spread=2.0, size=1.5, role="both", seed=40 + k)


def burnt_village(c, m, sc, fires):
    """Half the torches flared into fires (the huts and the tube mouths burning)."""
    for x, y, z in list(sc.flames)[::2]:
        fires.append((x, y, z - 1.0))


def dress(c, m, sc):
    fires = []
    print("off the flow:", off_the_flow(c, m))
    flow(c, m, sc, fires)
    bombs(c, m, sc)
    burnt_village(c, m, sc, fires)
    fires += rk.scorch(c, BURNS, sc.ground, lambda x, y: iss.clear_of(c, x, y, 4.0) and m.lava_d(x, y) > 2, per=4)
    print("cleared off the new road:", rk.clear_new_road(c, ("Beach", "Springs", "Jungle", "Village")))
    rk.emit(c, fires)
    sc.embers += [f for f in fires if m.lava_d(f[0], f[1]) < 2]
    sc.flames += fires
    iss.light(sc)
    c.merge_props(("Wreck",))
    c.entity("ashfall", rate=20, radius=40)
    print("isle ruin: fires", len(fires), "lap", round(c.length, 1))


ruin_mode.DRESS = dress

if __name__ == "__main__":
    vi.main()
