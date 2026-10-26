# Shipwreck Bay in ruins: Adventure's treasure map course for the pirate cove
# (?track=shipwreck_bay_ruin; in dev builds the course's menu entry asks Standard or Ruined).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/shipwreck_bay_ruins.py      (the bpy module)
#
# Tidewyrm's raid (Blake: Tropic Isles ruins change little: one decent change each, plus
# rubble to avoid). The galleon's back is broken: her hull has split open amidships, the
# halves pulled apart, the mainmast down across the sandbar; the hold's floor went with
# it, so you jump the break over the sea. Her cargo is strewn over the road in three
# places. The lap, the pier and the mast jump are the course's own. About 740 m.

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ruin_mode  # noqa: E402

ruin_mode.ON = True
import shipwreck_bay as sb  # noqa: E402

import ruin_kit as rk  # noqa: E402
import tropic_props as tp  # noqa: E402
import wreck_scenery as ws  # noqa: E402
from course_kit import Vector  # noqa: E402
from oasis_desert import Mesh  # noqa: E402

BURNS = [(40.0, 60.0, 14.0), (-40.0, 70.0, 14.0)]


def broken_back(c, m, sc, fires):
    """The mainmast fallen off the break across the sandbar, splintered planks at the two
    halves' broken ends, a fire in the bow half."""
    s0, s1 = m.TO_ROAD(m.SPLIT[0]), m.TO_ROAD(m.SPLIT[1])
    q = c.at((s0 + s1) / 2)
    out = q.r * (1 if q.r.y > 0 else -1)
    foot = q.p + out * 9.0
    top = foot + out * 6.0 + q.t * 16.0
    me = Mesh()
    a = Vector((foot.x, foot.y, sc.ground(foot.x, foot.y) + 1.0))
    b = Vector((top.x, top.y, sc.ground(top.x, top.y) + 0.6))
    me.add(("wreck_planks", "wall"), lambda bm: rk.tube_between(bm, a, b, 0.7, 0.5, n=8))
    for s, d in ((s0 - 1.0, 1), (s1 + 1.0, -1)):
        qq = c.at(s)
        for k in range(5):
            o = (k - 2) * 4.6
            p = qq.side(o)
            tip = p + qq.t * d * (1.5 + 1.5 * ((k * 7) % 3)) + Vector((0, 0, -1.0 - (k % 2)))
            me.add(("wreck_planks", "wall"), lambda bm, p=p, tip=tip, z=qq.p.z, k=k: rk.tube_between(bm, Vector((p.x, p.y, z + 3.0 + k % 2)), Vector((tip.x, tip.y, z + 1.0)),
                                                                                      0.25, 0.15, n=5))
    me.build(c, "Broken Back", "Wreck", "visual")
    fires.append((q.p.x - q.t.x * 14, q.p.y - q.t.y * 14, q.p.z + 4.0))
    fires.append((b.x, b.y, b.z + 0.8))


def cargo(c, m, sc):
    """Her cargo strewn over the road: barrels and crates a third of the way across."""
    for k, (d, side) in enumerate(m.CARGO):
        q = c.at(m.TO_ROAD(d))
        for j in range(4):
            p = q.side(side * (q.w / 2 - 1.5 - 1.6 * j)) + q.t * ((j % 2) * 2.0 - 1.0)
            proto = (tp.barrel(c), tp.crate(c))[(j + k) % 2]
            sc.put(proto, p.x, p.y, sc.ground(p.x, p.y) - 0.1, rot=j * 1.3 + k, coll="Wreck", role="both", r=0.8)


def dress(c, m, sc):
    fires = []
    broken_back(c, m, sc, fires)
    cargo(c, m, sc)
    fires += rk.scorch(c, BURNS, sc.ground, lambda x, y: ws.clear_of(c, x, y, 4.0), per=4)
    rk.emit(c, fires)
    sc.flames += fires
    ws.light(sc)
    c.merge_props(("Wreck",))
    c.entity("ashfall", rate=14, radius=40)
    print("wreck ruin: fires", len(fires), "lap", round(c.length, 1))


ruin_mode.DRESS = dress

if __name__ == "__main__":
    sb.main()
