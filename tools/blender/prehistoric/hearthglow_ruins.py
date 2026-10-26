# Hearthglow Hollow in ruins: Adventure's treasure map course for the Christmas village
# (?track=hearthglow_hollow_ruin; in dev builds the course's menu entry asks Standard or Ruined).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/hearthglow_ruins.py      (the bpy module)
#
# The dragons burned the village (Blake: the ruined city as the course, a fast
# speedrun-feel lap, but not so wild there's no time for the four map fragments). The
# stone bridge has fallen into the river, so the mountain road, the sleigh run and the
# covered bridge (burnt to its posts) are cut off. The lap runs through the square past
# the scorched giant tree, west along the burnt riverside over the cottages' fallen walls,
# south into the old town (the market street beyond it is buried under the fallen market
# hall) and down the back alley, which the fire and the falling houses opened into a
# street of rubble, icy dogleg and all, and round onto the finish street. About 860 m
# (the full lap is 1554 m).
#
# hearthglow_hollow.py lays the lap out (ruin_mode.ON); the village itself is placed by
# the course's own scenery code along the standard lap (ruin_kit.ghost); here are the
# fallen bridge, the burnt houses, the rubble and the fires.

import importlib
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ruin_mode  # noqa: E402

# The standard course first (its route and landmarks), then the ruin's lap.
ruin_mode.ON = False
import hearthglow_hollow as std  # noqa: E402

sys.modules.pop("hearthglow_hollow")
ruin_mode.ON = True
hh = importlib.import_module("hearthglow_hollow")

import hearthglow_props as hp  # noqa: E402
import hearthglow_scenery as hs  # noqa: E402
import props  # noqa: E402
import ruin_kit as rk  # noqa: E402
from course_kit import Vector, rnd  # noqa: E402
from hearthglow_props import Parts  # noqa: E402

# Where the fire fell: the riverside, the old town, the alley, the square's north side.
BURNS = [(-110.0, 125.0, 26.0), (-180.0, 110.0, 22.0), (-235.0, 60.0, 20.0), (-170.0, -30.0, 24.0),
         (-110.0, -110.0, 22.0), (-40.0, 70.0, 18.0), (-250.0, 170.0, 16.0)]


def burnt_cottage(c, variant=0):
    """A cottage the fire gutted: its stone footing, the plaster or log walls standing
    to ragged heights, the roof gone but for charred rafters, embers in the rubble."""
    name = "Burnt Cottage %d" % variant
    w, d, h, wall = ((11.0, 8.0, 6.5, "cabin_plaster"), (9.0, 8.0, 4.6, "cabin_wall"), (10.0, 9.0, 7.0, "cabin_plaster"))[variant % 3]

    def build(bm):
        k = Parts(bm)
        k.box("hearth_stone", (0, 0, 0.6), (w + 0.4, d + 0.4, 1.6))
        # The walls, broken off at different heights; one side wall gone.
        k.box(wall, (0, -d / 2 + 0.3, 1.2 + h * 0.35), (w, 0.6, h * 0.7))
        k.box(wall, (-w * 0.2, d / 2 - 0.3, 1.2 + h * 0.2), (w * 0.6, 0.6, h * 0.4))
        k.box(wall, (w / 2 - 0.3, 0, 1.2 + h * 0.45), (0.6, d, h * 0.9))
        # Soot over the tops of the walls, charred rafters fallen in, the chimney standing.
        k.box("ruin_char", (0, -d / 2 + 0.3, 1.2 + h * 0.7), (w + 0.1, 0.7, 0.4))
        for i in range(4):
            x = -w / 2 + 1.5 + i * (w - 3) / 3
            k.box("ruin_char", (x, 0.5 * (i % 2), 1.6 + h * 0.4), (0.4, d * 0.9, 0.4), rot=0.2 * (i - 1.5),
                  tilt=(0.5 * (1 if i % 2 else -1), 0.1 * i))
        k.box("brick", (w * 0.25, d * 0.18, (h + 2) / 2), (1.4, 1.4, h + 2))
        k.add("ruin_rubble", lambda bm: [blobs(bm, (-1.5 + 2 * i, -0.5 + i % 2, 1.3), 1.4 - 0.2 * i) for i in range(3)])
        k.add("ruin_ember", lambda bm: blobs(bm, (0.5, 0.8, 1.2), 0.9))
        return k.slots(c)

    return hp._p(c, name, build)


def blobs(bm, at, r):
    props.blob(bm, at, r, sx=1.2, sy=1.0, sz=0.5, subdiv=1)


def fallen_bridge(c, z_at, fires):
    """The stone bridge (along the standard lap): its two end piers stand, a stub of the
    deck on each, the middle spans down on the river ice in blocks. (Called on the
    standard lap: c.at is the old road.)"""
    S = std.SEG
    m = hs.Mesh()
    s0, s1 = S[5], S[6]
    for j, s in enumerate((s0 + 8, s1 - 8)):
        q = c.at(s)
        top = q.p.z - 0.6
        m.box("hearth_stone", (q.p.x, q.p.y, (top + std.RIVER_Z - 2) / 2), (q.w + 2.0, 5.0, top - std.RIVER_Z + 2), rot=hs.road_rot(q) + math.pi / 2)
        # A stub of the deck reaching out over the river, broken off.
        for k in range(3):
            r = c.at(s + (k * 4.0 if j == 0 else -k * 4.0))
            m.box("hearth_stone", (r.p.x, r.p.y, r.p.z - 0.9 - 0.25 * k), (r.w + 1.6, 4.2, 1.2), rot=hs.road_rot(r) + math.pi / 2,
                  tilt=(0.06 * k * (1 if j == 0 else -1), 0.0))
    # The middle on the ice, in tumbled blocks.
    for k in range(9):
        q = c.at(s0 + 18 + k * 3.0)
        p = q.side((rnd(k * 1.7) - 0.5) * 10)
        m.box("hearth_stone", (p.x, p.y, std.RIVER_Z + 0.4), (4.0 + 2 * rnd(k), 3.0 + 2 * rnd(k + 3), 1.6), rot=rnd(k * 2.9) * 3,
              tilt=((rnd(k) - 0.5) * 0.6, (rnd(k + 9) - 0.5) * 0.5))
    m.build(c, "Fallen Stone Bridge", "Wreck", "both")
    q = c.at((s0 + s1) / 2)
    fires.append((q.p.x + 6, q.p.y, std.RIVER_Z + 1.5))


def burnt_covered_bridge(c, fires):
    """The covered bridge, burnt to its posts: charred stumps down both sides, a few
    fallen beams. (On the standard lap.)"""
    S = std.SEG
    st = rk.stub(c)
    for k, s in enumerate(range(int(S[18]) + 10, int(S[19]) - 6, 5)):
        q = c.at(s)
        if q.p.z - std.natural(q.p.x, q.p.y) < 2.5:
            continue
        for side in (-1, 1):
            if rnd(k * 3.1 + side) < 0.25:
                continue
            p = q.side(side * (q.w / 2 + 1.4))
            c.place(st, p.x, p.y, std.RIVER_Z - 0.5, scale=(1.0 + 1.4 * rnd(k + side)), coll="Wreck", role="visual")
        if k % 4 == 1:
            fires.append((q.p.x, q.p.y, std.RIVER_Z + 1.2))


def dress(c, m):
    ter = list(c.coll("Terrain").objects)

    def z_at(x, y):
        z = c.ground_z(x, y, ter)
        return z if z is not None else m.natural(x, y)

    def clear(x, y, margin=4.0):
        return props.clear_of_road(c, x, y, margin) and hs.dry(std, x, y, 3.0)

    fires = []
    # The village, from the course's own scenery code, along the standard lap.
    g = rk.ghost_route(c, std.ROUTE, width=15.0, bank=6.0)
    with rk.ghost(c, g):
        sc = hs.build(c, std, ruin=True)
        fallen_bridge(c, z_at, fires)
        burnt_covered_bridge(c, fires)
        # The market hall fallen across the old town's street, past where the alley
        # leaves it (why the lap goes down the alley now).
        q = c.at(std.SEG[23] + 4)
        c.place(burnt_cottage(c, 2), q.p.x, q.p.y, z_at(q.p.x, q.p.y) - 0.6, rot=hs.road_rot(q) + 0.3, scale=1.3, coll="Wreck")
        rk.rubble_heap(c, q.p.x, q.p.y + 8, z_at, n=12, spread=9.0, size=2.6, seed=31)
    # The giant tree scorched: its boughs burnt black, its lights out.
    tree = next((o for o in c.coll("Village").objects if o.name.startswith("Giant Christmas Tree")), None)
    if tree is not None:
        for slot in tree.material_slots:
            if slot.material and slot.material.name.startswith(("pine_night", "xmas_lights")):
                slot.material = c.lib("ruin_char")
    c.entities[:] = [e for e in c.entities if e["type"] != "ornament"]
    # Along the new road: the houses that stood there, burnt out, and their rubble.
    k = 0
    S = m.SEG
    for s0, s1 in ((S[4], S[8]), (S[8], S[13] + 30)):
        s = s0 + 6
        while s < s1:
            q = c.at(s)
            for side in (-1, 1):
                k += 1
                p = q.side(side * (q.w / 2 + 9.5 + 3 * rnd(k)))
                if not clear(p.x, p.y, 5.0):
                    continue
                if k % 3 == 0:
                    rk.rubble_heap(c, p.x, p.y, z_at, n=7, spread=5.0, size=2.0, role="visual", seed=k)
                else:
                    c.place(burnt_cottage(c, k % 3), p.x, p.y, z_at(p.x, p.y) - 0.6, rot=hs.road_rot(q) + (math.pi if side > 0 else 0.0),
                            coll="Wreck")
                    if k % 2:
                        fires.append((p.x, p.y, z_at(p.x, p.y) + 2.0))
            s += 17.0 + 4 * rnd(s)
    # The fallen walls the road rides over: rubble either side of each hump.
    for at, h, ln in m.HUMPS:
        q = c.at(at)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 3.5))
            if clear(p.x, p.y, 2.0):
                rk.rubble_heap(c, p.x, p.y, z_at, n=5, spread=3.5, size=1.6, role="visual", seed=int(at) + side)
    print("cleared off the new road:", rk.clear_new_road(c, ("Village", "Blocks", "Distant", "Pines", "Forest", "Mountain", "Bridges")))
    fires += rk.scorch(c, BURNS, z_at, clear, per=5, wet=lambda x, y, z: not hs.dry(std, x, y, 2.0))
    hs.finish(c, ter, sc)
    rk.emit(c, fires, glow_on=ter)
    c.merge_props(("Wreck",))
    # A few presents left in the road (smash them for a boost), out of the slow corners.
    for k, (s, side) in enumerate(((30.0, 1), (S[2] + 60, -1), (S[7] + 10, 1), (S[9] + 20, -1), (S[12] + 15, 1))):
        q = c.at(s)
        p = q.side(side * (q.w / 2 + 0.9))
        hs.game_entity(c, "present", p.x, p.y, q.p.z, size=2.2 + 0.4 * (k % 3), variant=k, heading=round(hs.road_rot(q), 3))
    c.entity("ashfall", rate=22, radius=40)
    print("hearthglow ruin: fires", len(fires), "lap", round(c.length, 1))


ruin_mode.DRESS = dress

if __name__ == "__main__":
    hh.main()
