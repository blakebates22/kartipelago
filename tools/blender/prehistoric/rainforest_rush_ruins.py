# Rainforest Rush in ruins: Adventure's treasure map course for the rainforest
# (?track=rainforest_rush_ruin; in dev builds the course's menu entry asks Standard or Ruined).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/rainforest_rush_ruins.py      (the bpy module)
#
# After Tidewyrm's storm (Blake: Tropic Isles ruins change little: one decent change each,
# plus rubble to avoid): the great storm brought giant trees down across the way, the lap
# weaves past their trunks and the rubble they tore up (in three places), and the temple's
# braziers and the fallen trees smoulder. The lap is the course's own.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ruin_mode  # noqa: E402

ruin_mode.ON = True
import rainforest_rush as rr  # noqa: E402

import props  # noqa: E402
import ruin_kit as rk  # noqa: E402

BURNS = [(-150.0, 90.0, 16.0), (120.0, -150.0, 14.0), (-60.0, 0.0, 14.0)]
# (where the storm brought trees down: route point, along, which side the trunk lies from)
DOWN = [(4, 0.5, 1), (19, 0.5, -1), (24, 0.5, 1)]


def fallen_trees(c, m, ground, fires):
    """Giant trees down across half the road, their crowns in the jungle beside it, the
    rubble they tore up round their roots: weave past them."""
    for k, (i, f, sd) in enumerate(DOWN):
        q = c.at(m._s(c, i, f))
        # (the trunk from well off the road's edge to a third of the way across it)
        a = q.side(sd * (q.w / 2 + 16.0))
        b = q.side(sd * (q.w / 2 - 6.0))
        za, zb = ground(a.x, a.y) + 1.4, q.p.z + 1.2
        m._tube_ob(c, "Fallen Tree %d" % k, [(a.x, a.y, za), ((a.x + b.x) / 2, (a.y + b.y) / 2, (za + zb) / 2 + 0.3), (b.x, b.y, zb)],
                   [1.6, 1.4, 1.1], ("giant_bark", "wall"), role="both")
        rk.rubble_heap(c, b.x - q.t.x * 3.0, b.y - q.t.y * 3.0, ground, n=5, spread=2.4, size=1.2, role="both", seed=40 + k)
        fires.append((a.x, a.y, za + 0.8))


def dress(c, m, ground):
    fires = []
    fallen_trees(c, m, ground, fires)
    fires += rk.scorch(c, BURNS, ground, lambda x, y: m.paint.road_clear(c, x, y, 4.0), per=4)
    tx, ty = m.R.TEMPLE
    for sd in (-1, 1):
        fires.append((tx + sd * 8.0, ty + 11.0, ground(tx + sd * 8.0, ty + 11.0) + 1.6))
    rk.emit(c, fires)
    c.entity("ashfall", rate=12, radius=40)
    print("rainforest ruin: fires", len(fires))


ruin_mode.DRESS = dress

if __name__ == "__main__":
    rr.main()
