# Cascade Caverns in ruins: Adventure's treasure map course for the jungle canyon
# (?track=cascade_caverns_ruin; in dev builds Cascade's menu entry asks Standard or Ruined).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/cascade_ruins.py      (the bpy module)
#
# The dragons brought down the viaduct and the ledge at the east end: the lap climbs their
# rubble straight north across the canyon (over the river) to the temple bridge, then runs
# Cascade's own course: the bridge over the start, the torchlit tunnel, the leap through
# the waterfall, the north road and the low bridge. About 1070 m (the full lap is 1209 m).
# cascade_caverns.py lays the lap out (ruin_mode.ON); this adds the wreckage: the fallen
# viaduct's broken piers and rubble where it stood, burnt patches in the jungle, charred
# trees, fires, smoke and ash, the jungle elsewhere untouched.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ruin_mode  # noqa: E402

ruin_mode.ON = True

import cascade_caverns as cc  # noqa: E402  (lays out the ruined lap)
import course_kit as kit  # noqa: E402
import props  # noqa: E402
import ruin_kit as rk  # noqa: E402
from course_kit import rnd  # noqa: E402

# Where the fire fell: round the fallen viaduct at the east end, along the climb, and a
# few patches further west.
BURNS = [(110.0, -10.0, 34.0), (85.0, -50.0, 26.0), (80.0, 40.0, 26.0), (30.0, 25.0, 18.0), (-10.0, 30.0, 16.0),
         (10.0, -20.0, 16.0), (70.0, -5.0, 18.0), (25.0, 70.0, 16.0), (-45.0, -15.0, 14.0), (-20.0, -60.0, 14.0),
         (-150.0, 55.0, 20.0), (-200.0, -40.0, 18.0), (-120.0, 20.0, 16.0), (-170.0, 85.0, 16.0)]
burn = rk.burns_fn(BURNS)

_classify = cc.classify


def classify(c, n, info):
    mat = _classify(c, n, info)
    if mat and mat[0] in ("jungle_leafcover", "jungle_path") and burn(c.x, c.y) > 0.45 + 0.2 * math.sin(c.x * 0.6 + c.y * 0.4):
        return ("ruin_ash", mat[1])
    return mat


cc.classify = classify


def dress(c, m):
    ter = list(c.coll("Terrain").objects)

    def z_at(x, y):
        z = c.ground_z(x, y, ter)
        return z if z is not None else m.natural(x, y)

    def clear(x, y, margin=4.0):
        return props.clear_of_road(c, x, y, margin)

    # The fallen viaduct: where its sweep round the east end stood (the standard lap's
    # segment 4), broken piers and heaps of its stones.
    d = 0.0
    old = []
    for a, b in zip(m.STANDARD_PATH, m.STANDARD_PATH[1:]):
        d += math.hypot(b[0] - a[0], b[1] - a[1])
        if b[3] in (3, 4, 5):
            old.append((b[0], b[1], d))
    nxt = 0.0
    k = 0
    for x, y, dd in old:
        if dd < nxt:
            continue
        nxt = dd + 22.0
        k += 1
        if not clear(x, y, 6.0):
            continue
        z = z_at(x, y)
        if k % 2:
            h = 5.0 + 6.0 * rnd(k * 3.1)
            pier = c.rock_mass("Fallen Viaduct Pier %d" % k, x, y, 2.8, 2.4, z + h, z0=z - 2.0, n=6, seed=k,
                               bands=[(1.0, 0.0), (1.0, 0.8), (0.8, 0.9), (0.5, 1.0)], base=z)
            c.assign(pier, c.lib("ruin_stone", "wall"))
        rk.rubble_heap(c, x + 3.0, y - 2.0, z_at, n=7, spread=6.0, size=1.8, seed=k)
    fires = rk.scorch(c, BURNS, z_at, clear, per=6, wet=lambda x, y, z: z < m.WATER_Z + 0.4)
    print("charred trees", rk.char_trees(c, burn, ("Palm", "Jungle Tree", "Grand Tree", "Giant Tree", "Canopy Tree")))
    rk.emit(c, fires, glow_on=ter)
    c.entity("ashfall", rate=40, radius=40)
    print("cascade ruin: fires", len(fires))


ruin_mode.DRESS = dress

if __name__ == "__main__":
    cc.main()
