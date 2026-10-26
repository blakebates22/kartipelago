# Coral Cove in ruins: Adventure's treasure map course for the first beach
# (?track=coral_cove_ruin; in dev builds the course's menu entry asks Standard or Ruined).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/coral_cove_ruins.py      (the bpy module)
#
# Tidewyrm's raid (Blake: Tropic Isles ruins change little: one decent change each,
# plus rubble to avoid; Coral Cove's jump must not change how it feels at all). The
# lighthouse has fallen off its rock across the road out of the hairpin, and the road
# rides up over its broken tower; rubble from the headland lies in the road in three
# places. The lap and the jump are the course's own. About 458 m.

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ruin_mode  # noqa: E402

ruin_mode.ON = True
import coral_cove as cc  # noqa: E402

import cove_scenery as cs  # noqa: E402
import ruin_kit as rk  # noqa: E402
from course_kit import Vector  # noqa: E402
from oasis_desert import Mesh  # noqa: E402
from props import cuboid  # noqa: E402

BURNS = [(-30.0, 40.0, 14.0), (90.0, 120.0, 14.0), (140.0, 60.0, 12.0)]


def fallen_lighthouse(c, m, sc, fires):
    """The lighthouse's stump on its rock, and the tower lying from the rock down across
    the road (its crown just under the road's hump), the lantern room and cap beyond."""
    lx, ly = m.LIGHTHOUSE
    s = m.TO_ROAD(m.TOPPLE[0])
    q = c.at(s)
    cross = Vector((q.p.x, q.p.y, 0.0))
    base = Vector((lx, ly, 0.0))
    ax = (cross - base).normalized()
    far = cross + ax * 9.0
    me = Mesh()
    # The stump: the tower's foot broken off on the rock.
    me.add(("cove_lighthouse", "wall"), lambda bm: rk.tube_between(bm, Vector((lx, ly, 11.0)), Vector((lx, ly, 14.6)), 2.6, 2.5))
    # The tower, in three lengths with breaks between, its crown under the hump.
    z_cross = q.p.z - 0.6 - 2.1
    a = Vector((base.x + ax.x * 3.0, base.y + ax.y * 3.0, 11.5))
    b = Vector((far.x, far.y, sc.ground(far.x, far.y) + 1.6))
    mid = Vector((cross.x, cross.y, z_cross))
    pts = [a, a.lerp(mid, 0.55), mid, b]
    radii = [2.4, 2.2, 2.1, 1.9]
    for k in range(3):
        p0, p1 = pts[k], pts[k + 1]
        gap = (p1 - p0).normalized() * 0.4
        me.add(("cove_lighthouse", "wall"), lambda bm, p0=p0, p1=p1, k=k, gap=gap: rk.tube_between(bm, p0 + gap, p1 - gap, radii[k], radii[k + 1]))
    # The gallery and the lantern room beyond the road, the cap knocked off beside them.
    e = b + (b - mid).normalized() * 1.6
    me.add(("cove_white", "wall"), lambda bm: rk.tube_between(bm, b, b + (b - mid).normalized() * 0.5, 2.6, 2.6))
    me.add(("cove_lamp", "wall"), lambda bm: rk.tube_between(bm, b + (b - mid).normalized() * 0.5, e, 1.3, 1.3, n=10))
    side = Vector((-ax.y, ax.x, 0.0))
    cap = e + side * 3.5
    me.add(("cove_lighthouse", "wall"), lambda bm: cuboid(bm, (cap.x, cap.y, sc.ground(cap.x, cap.y) + 0.6), (2.2, 2.2, 1.4), 0.7, (0.4, 0.2)))
    me.build(c, "Fallen Lighthouse", "Wreck", "both")
    fires.append((e.x, e.y, e.z + 1.0))
    fires.append((lx, ly, 15.0))


def road_rubble(c, m, sc):
    """Rubble from the headland lying in the road: a heap a third of the way across."""
    for k, (d, side) in enumerate(m.RUBBLE):
        q = c.at(m.TO_ROAD(d))
        p = q.side(side * (q.w / 2 - 3.0))
        rk.rubble_heap(c, p.x, p.y, sc.ground, n=6, spread=2.2, size=1.3, role="both", seed=40 + k)


def dress(c, m, sc):
    fires = []
    fallen_lighthouse(c, m, sc, fires)
    road_rubble(c, m, sc)
    fires += rk.scorch(c, BURNS, sc.ground, lambda x, y: cs.clear_of(c, x, y, 4.0), per=4)
    print("cleared off the new road:", rk.clear_new_road(c, ("Headland", "Beach", "Palms")))
    rk.emit(c, fires)
    sc.flames += fires
    cs.light(sc)
    c.merge_props(("Wreck",))
    c.entity("ashfall", rate=14, radius=40)
    print("cove ruin: fires", len(fires), "lap", round(c.length, 1))


ruin_mode.DRESS = dress

if __name__ == "__main__":
    cc.main()
