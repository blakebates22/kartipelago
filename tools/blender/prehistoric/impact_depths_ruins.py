# Impact Depths in ruins: Adventure's treasure map course for the asteroid's pit
# (?track=impact_depths_ruin; in dev builds the course's menu entry asks Standard or Ruined).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/impact_depths_ruins.py      (the bpy module)
#
# Much of the cave's roof has come down (Blake: the descent becomes a run of jumps over
# the broken road; rock keeps falling, with a shadow on the road first so it's fair;
# hard to make it drive very differently, and that's fine). The lap is the course's own;
# the fallen roof broke the terraces' roads in six places (jumps, the old crevasse among
# them), great holes show the sky (and the sunlight pours down them), slabs of the roof
# lie on the ledges, and rock keeps falling from the holes' edges.
#
# impact_depths.py lays the lap out (ruin_mode.ON: the breaks, their holes through the
# ledges, the roof's holes); its own dressing (impact_depths_dress.py) builds the cave
# round them; here are the fallen roof, the broken edges, the falling rock and the fires.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ruin_mode  # noqa: E402

ruin_mode.ON = True
import impact_depths as idp  # noqa: E402

import impact_depths_dress as idd  # noqa: E402
import ruin_kit as rk  # noqa: E402
from course_kit import rnd  # noqa: E402
from impact_scenery import clear, game_entity  # noqa: E402

FLOOR = {"crater": "crater_ground", "crystal": "flowstone", "jungle": "fern_floor", "volcanic": "lava_crust", "core": "lava_crust"}


def fallen_roof(c, m, d, fires):
    """Slabs of the roof on the ledges under each new hole (clear of the road), and the
    biggest down in the lava round the core."""
    k = 0
    for hx, hy, hr in m.SKYLIGHTS[-4:]:
        for j in range(14):
            k += 1
            a = j * 2.39996 + hx * 0.01
            rr = hr * 0.95 * math.sqrt(rnd(k * 1.37 + 3))
            x, y = hx + rr * math.cos(a), hy + rr * math.sin(a)
            if not clear(c, x, y, 5.0) or m.in_break(x, y) is not None:
                continue
            z = d.floor(x, y)
            zn = m.zone(x, y)
            slab = c.rock_mass("Fallen Roof %d" % k, x, y, 3.0 + 5.0 * rnd(k), 2.5 + 4.0 * rnd(k + 7), z + 2.0 + 5.0 * rnd(k * 3), z0=z - 3.0, n=8,
                               seed=200 + k, angle=k * 0.8)
            c.paint_rock(slab, (idd.ROOF[zn], "wall"), (FLOOR[zn], "dirt"))
            if k % 4 == 0:
                fires.append((x, y, z + 1.5))


def broken_edges(c, m, d, fires):
    """Rubble heaped either side of each break, where the ledge went down."""
    for i, (hx, hy, ux, uy, z) in enumerate(m.HOLES):
        for side in (-1, 1):
            x, y = hx - uy * side * 14.0, hy + ux * side * 14.0
            if clear(c, x, y, 2.0):
                rk.rubble_heap(c, x, y, d.floor, n=7, spread=5.0, size=2.2, role="visual", seed=i * 2 + (side > 0))
        fires.append((hx - uy * 12.0, hy + ux * 12.0, z - 6.0))


def rockfall(c, m):
    """Rock falling from the holes' edges onto the road on the race clock's beat, a
    shadow on the road first (game/rift.ts: an icicle that looks like rock)."""
    k = 0
    last = -1e9
    s = 40.0
    while s < c.length - 40:
        q = c.at(s)
        o = m.opening(q.p.x, q.p.y)
        near_break = any(abs(m.TO_PLAN(s) - (g0 + g1) / 2) < 40 for g0, g1 in m.BREAKS)
        if -24.0 < o < -4.0 and not near_break and s - last > 60 and q.p.z < m.Z_TOP - 4:
            k += 1
            last = s
            p = q.side((rnd(k * 2.7) - 0.5) * q.w * 0.6)
            roof = m.roof_z(p.x, p.y)
            game_entity(c, "icicle", p.x, p.y, q.p.z, top=round(min(roof - 1.0, q.p.z + 30.0), 1), period=round(8.0 + 3.0 * rnd(k), 1),
                        offset=round(1.0 + k * 2.3, 2), warn=1.6, r=3.4, look="rock")
        s += 6.0
    return k


def dress(c, m, d):
    fires = []
    fallen_roof(c, m, d, fires)
    broken_edges(c, m, d, fires)
    n = rockfall(c, m)
    rk.emit(c, fires, glow_on=[d.ter])
    c.merge_props(("Wreck",))
    # (Ash: the crater has its own, impact_depths_dress.py.)
    print("impact ruin: fires", len(fires), "falling rock", n, "lap", round(c.length, 1))


ruin_mode.DRESS = dress

if __name__ == "__main__":
    idp.main()
