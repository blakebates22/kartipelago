# Splash Lagoon in ruins: Adventure's treasure map course for the water park
# (?track=splash_lagoon_ruin; in dev builds the course's menu entry asks Standard or Ruined).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/splash_lagoon_ruins.py      (the bpy module)
#
# Tidewyrm's raid (Blake: Tropic Isles ruins change little: one decent change each, plus
# rubble to avoid; the first take: the slide tower has toppled and its wreck makes a
# ramp). The tower came down along its climbing ramp, so the lap climbs the wreck's side
# to the flume; its canopy lies torn on the sand, and pool tiles and park junk lie in the
# road in three places. The lap is the course's own. About 830 m.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ruin_mode  # noqa: E402

ruin_mode.ON = True
import splash_lagoon as sl  # noqa: E402

import beach_props as bp  # noqa: E402
import lagoon_scenery as ls  # noqa: E402
import ruin_kit as rk  # noqa: E402
from course_kit import Vector  # noqa: E402
from oasis_desert import Mesh  # noqa: E402
from props import cuboid  # noqa: E402

BURNS = [(-40.0, 80.0, 14.0), (160.0, 40.0, 14.0)]


def toppled_tower(c, m, sc, fires):
    """The tower lying along the climbing ramp, beside and under it (its panels the
    road's way up), its deck's posts broken off where it stood, the canopy torn on the
    sand beyond."""
    s1 = m.TO_ROAD(m.SEG[7])
    s0 = max(m.TO_ROAD(m.CLIMB[0]) + 6.0, s1 - m.TOP - 12.0)  # (its length, base to canopy)
    me = Mesh()
    k = 0
    s = s0
    while s < s1:
        q = c.at(s)
        side = q.side(q.w / 2 + 4.5)
        top = q.p.z - 0.6
        me.add(("splash_slide_yellow", "wall"), lambda bm, q=q, side=side, top=top: cuboid(bm, (side.x, side.y, top / 2), (6.0, 8.5, max(1.0, top)),
                                                                                           math.atan2(q.t.y, q.t.x)))
        if k % 2:
            me.add(("splash_slide_red", "wall"), lambda bm, q=q, side=side, top=top: cuboid(bm, (side.x, side.y, top + 0.3), (6.2, 8.7, 0.6),
                                                                                            math.atan2(q.t.y, q.t.x)))
        k += 1
        s += 6.0
    tx, ty = m.TOWER
    for j in range(4):
        a = j * math.pi / 2 + 0.785
        p0 = Vector((tx + 8.0 * math.cos(a), ty + 8.0 * math.sin(a), 0.0))
        me.add(("party_white", "wall"), lambda bm, p0=p0, j=j: rk.tube_between(bm, p0, p0 + Vector((0.0, 0.0, 3.0 + 2.0 * (j % 2))), 0.5, 0.4, n=6))
    cx, cy = tx + 26.0, ty - 6.0
    me.add(("splash_cabana", "wall"), lambda bm: cuboid(bm, (cx, cy, sc.ground(cx, cy) + 0.6), (16.0, 14.0, 0.5), 0.5, (0.12, 0.08)))
    me.build(c, "Toppled Tower", "Wreck", "visual")
    fires.append((cx, cy, sc.ground(cx, cy) + 1.0))


def road_junk(c, m, sc):
    """Pool tiles and park junk lying in the road, a third of the way across."""
    S = m.TO_ROAD
    for k, (s, side) in enumerate(((S(m.SEG[4]) + 20, 1), (S(m.SEG[14]) + 10, -1), (S(m.SEG[20]) + 10, 1))):
        q = c.at(s)
        p = q.side(side * (q.w / 2 - 3.0))
        rk.rubble_heap(c, p.x, p.y, sc.ground, n=6, spread=2.2, size=1.3, role="both", seed=80 + k)
        sc.put(bp.beach_ball(c, k % 3), p.x + 2.0, p.y, sc.ground(p.x, p.y) + 0.5, scale=1.5, coll="Wreck", role="visual")


def dress(c, m, sc):
    fires = []
    toppled_tower(c, m, sc, fires)
    road_junk(c, m, sc)
    fires += rk.scorch(c, BURNS, sc.ground, lambda x, y: ls.clear_of(c, x, y, 4.0), per=4)
    print("cleared off the new road:", rk.clear_new_road(c, ("Beach", "Park", "Palms")))
    rk.emit(c, fires)
    sc.flames += fires
    ls.light(sc)
    c.merge_props(("Wreck",))
    c.entity("ashfall", rate=12, radius=40)
    print("lagoon ruin: fires", len(fires), "lap", round(c.length, 1))


ruin_mode.DRESS = dress

if __name__ == "__main__":
    sl.main()
