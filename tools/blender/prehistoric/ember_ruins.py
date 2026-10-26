# Ember Peak in ruins: Adventure's treasure map course for the volcanic field
# (?track=ember_peak_ruin; in dev builds Ember Peak's menu entry asks Standard or Ruined).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/ember_ruins.py      (the bpy module)
#
# The eruption the dragons woke brought the flank of the lava tube's ridge down over the
# home straight.
# Out of the magma cave the road dives south-east round the landslide's toe, sweeps left
# and back right over the humps of its rubble, and runs onto the lava bridge to the line
# (Blake: not shorter, a little longer; the boring straight made fast and exciting, like
# the beach courses). Everything before the cave is Ember Peak's own lap. About 920 m
# (the full lap is 878 m). ember_peak.py lays the lap out (ruin_mode.ON); this adds the
# landslide (a wall of rock over the old straight, so nobody cuts across it), rubble
# beside the humps, fires, smoke and heavier ash.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ruin_mode  # noqa: E402

ruin_mode.ON = True

import ember_peak as ep  # noqa: E402  (lays out the ruined lap)
import props  # noqa: E402
import ruin_kit as rk  # noqa: E402
from course_kit import rnd  # noqa: E402

# Where the fire fell: along the landslide and round the new road's sweeps.
BURNS = [(-150.0, -8.0, 30.0), (-95.0, -10.0, 26.0), (-130.0, -50.0, 22.0), (-60.0, -35.0, 18.0), (-200.0, -30.0, 18.0)]


def dress(c, m):
    ter = list(c.coll("Terrain").objects)

    def z_at(x, y):
        z = c.ground_z(x, y, ter)
        return z if z is not None else m.natural(x, y)

    def clear(x, y, margin=4.0):
        return props.clear_of_road(c, x, y, margin)

    # The landslide: a ridge of fallen rock along the old straight, solid (it walls the old
    # line off), boulders tumbled off its sides.
    old = [p for p in m.STANDARD_PATH if p[3] in (13, 14)]
    d, nxt, k = 0.0, 0.0, 0
    for a, b in zip(old, old[1:]):
        d += math.hypot(b[0] - a[0], b[1] - a[1])
        if d < nxt:
            continue
        nxt = d + 11.0
        x, y = b[0], b[1]
        if not clear(x, y, 9.0):
            continue
        k += 1
        z = z_at(x, y)
        h = 5.0 + 4.0 * rnd(k * 1.9)
        rock = c.rock_mass("Landslide %02d" % k, x, y + 3.0 * math.sin(k * 1.3), 8.0, 6.5, z + h, z0=z - 3.0, n=8, seed=k,
                           bands=[(1.0, 0.0), (0.9, 0.4), (0.7, 0.75), (0.4, 1.0)], base=z)
        c.assign(rock, c.lib("basalt_block", "wall"))
        rk.rubble_heap(c, x + 6.0 * math.cos(k), y - 8.0, z_at, n=6, spread=6.0, size=2.0, role="visual", seed=k)
    print("landslide rocks", k)
    # Rubble beside the new road's humps (the slide's spill it rolls over).
    for hmp in m.HUMPS:
        q = c.at(m.SEG[m.HOME] + hmp)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 6.0))
            if clear(p.x, p.y, 4.5):
                rk.rubble_heap(c, p.x, p.y, z_at, n=5, spread=4.0, size=1.6, role="visual", seed=int(hmp) + side)
    fires = rk.scorch(c, BURNS, z_at, clear, per=4, wet=lambda x, y, z: z < m.LAVA_Z + 0.6)
    rk.emit(c, fires, glow_on=ter)
    c.entity("ashfall", rate=30, radius=40)
    print("ember ruin: fires", len(fires))


ruin_mode.DRESS = dress

if __name__ == "__main__":
    ep.main()
