# Canyon Dash in ruins: Adventure's treasure map course for the great red-rock canyon
# (?track=canyon_dash_ruin; in dev builds the course's menu entry asks Standard or Ruined).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/canyon_ruins.py      (the bpy module)
#
# The dragons broke the Great Canyon Bridge in the middle and wrecked the canyon's far
# side (Blake: jump the broken bridge; past it a steep tunnel dives down to the river,
# rubble crosses it, and another wrecked tunnel climbs back to the top). The lap is the
# course's own off the rim, down the wall and under the Sandstone Arch to the bridge;
# you jump the gap; the north mesa's lobe has come down over the pass, so a cutting
# through its rockslide dives down the gorge's north wall to the river, the fallen rock
# carries you across, and the wrecked tunnel (its roof caved in) climbs the south wall's
# rockslide to the rim and the outpost. About 1345 m (the full lap is 1801 m).
#
# canyon_dash.py lays the lap out (ruin_mode.ON) and opens the gorge's walls where they
# fell; the canyon (the walls, the river and the falls, the arches, the buttes, the
# outpost) is the course's own scenery code; here are the broken bridge, the rockslides,
# the ruined portals, the fallen great butte (the climb comes out where it stood) and the
# fires.

import importlib
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ruin_mode  # noqa: E402

# The standard course first (its route and landmarks), then the ruin's lap.
ruin_mode.ON = False
import canyon_dash as std  # noqa: E402

sys.modules.pop("canyon_dash")
ruin_mode.ON = True
cdr = importlib.import_module("canyon_dash")

import canyon_props as cp  # noqa: E402
import canyon_scenery as cs  # noqa: E402
import canyon_walls as cw  # noqa: E402
import course_kit as kit  # noqa: E402
import props  # noqa: E402
import ruin_kit as rk  # noqa: E402
from course_kit import rnd  # noqa: E402
from props import cuboid  # noqa: E402

TIMBER = ("weathered_timber", "wall")
STONE = ("masonry", "wall")
# Where the fire fell: round the broken bridge's ends, the outpost, the rockslides.
BURNS = [(-195.0, -90.0, 20.0), (-200.0, 110.0, 22.0), (150.0, -170.0, 18.0), (-60.0, 120.0, 20.0), (300.0, -110.0, 22.0)]


def broken_bridge(c, m, fires):
    """The bridge's broken ends: splintered beams jutting over the gap and hanging down,
    and its middle spans down in the gorge."""
    me = cs.Mesh()
    for s, out in ((m.LIP, 1), (m.LAND, -1)):
        q = c.at(s)
        for k in range(5):
            a = q.side((k - 2) * 2.6, -0.8)
            b = a + q.t * out * (2.0 + 3.0 * rnd(k + out)) + kit.Vector((0, 0, -(1.0 + 6.0 * rnd(k * 3 + out))))
            me.add(TIMBER, lambda bm, a=a, b=b: cp._beam(bm, tuple(a), tuple(b), 0.3))
        fires.append((q.p.x, q.p.y, q.p.z + 0.5))
    # The fallen spans on the gorge's floor and ledges.
    for k in range(10):
        q = c.at(m.LIP + 2 + k * 1.4)
        p = q.side((rnd(k * 1.7) - 0.5) * 16)
        z = m.natural(p.x, p.y) + 0.8
        me.add(TIMBER, lambda bm, p=p, z=z, k=k: cuboid(bm, (p.x, p.y, z), (1.2, 9.0 + 6 * rnd(k), 1.0), rnd(k * 2.3) * 3,
                                                          ((rnd(k) - 0.5) * 0.6, (rnd(k + 4) - 0.5) * 0.4)))
    me.build(c, "Broken Bridge", "Wreck", "both")


def rockslides(c, m, fires):
    """The rockslides the cuttings run down: boulders strewn over them (clear of the
    road), the rockfall under the river crossing, and the pass buried at its mouth."""
    S = m.SEG
    big = [cp.boulder(c, 3 + k % 2) for k in range(2)]
    small = [cp.boulder(c, k % 3) for k in range(3)]
    k = 0
    s = S[10]
    while s < S[21]:
        q = c.at(s)
        for side in (-1, 1):
            k += 1
            p = q.side(side * (q.w / 2 + 6 + 18 * rnd(k)))
            if not props.clear_of_road(c, p.x, p.y, 3.0):
                continue
            z = m.natural(p.x, p.y)
            if k % 3 == 0:
                c.place(big[k % 2], p.x, p.y, z - 0.6, rot=k, scale=2.5 + 2.5 * rnd(k), coll="Wreck")
            else:
                c.place(small[k % 3], p.x, p.y, z - 0.3, rot=k, scale=1.0 + 1.5 * rnd(k + 2), coll="Wreck", role="visual")
        s += 9.0
    # The rockfall across the river: great boulders in the water under the road.
    s = S[15]
    while s < S[17]:
        q = c.at(s)
        for side in (-1, 0, 1):
            p = q.side(side * 6.0)
            c.place(big[(k := k + 1) % 2], p.x, p.y, cdr.Z_RIVER - 2.0, rot=k, scale=3.5 + 1.5 * rnd(k), coll="Wreck", role="visual")
        s += 6.0
    # Where the pass ran into the mesa: buried under the lobe that came down.
    with rk.ghost(c, GHOST[0]):
        for f in (0.0, 0.5, 1.0):
            q = c.at(std.SEG[11] + f * 60)
            for j in range(4):
                p = q.side((j - 1.5) * 7.0)
                c.place(big[j % 2], p.x, p.y, std.natural(p.x, p.y) - 1.0, rot=j + f, scale=4.0 + 2 * rnd(j + f), coll="Wreck")
        q = c.at(std.SEG[11] + 20)
        fires.append((q.p.x, q.p.y, q.p.z + 3))


def ruined_portals(c, m, fires):
    """Where the wrecked tunnels began: their stone portals, broken (a jamb each side and a
    fallen lintel), at the top of the dive and the top of the climb."""
    me = cs.Mesh()
    for s in (m.SEG[11] + 6, m.SEG[20] + 4):
        q = c.at(s)
        rot = cs.road_rot(q)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 2.2))
            h = 6.0 + 4.0 * rnd(s + side)
            me.add(STONE, lambda bm, p=p, h=h, z=q.p.z: cuboid(bm, (p.x, p.y, z + h / 2 - 0.3), (2.4, 3.0, h), rot))
        lin = q.side(q.w / 2 + 6.0)
        me.add(STONE, lambda bm, p=lin, z=q.p.z: cuboid(bm, (p.x, p.y, m.natural(p.x, p.y) + 0.6), (2.0, q.w + 6.0, 1.8), rot + 0.4, (0.15, 0.1)))
        fires.append((lin.x, lin.y, m.natural(lin.x, lin.y) + 2.0))
    me.build(c, "Ruined Portals", "Wreck", "both")


def fallen_butte(c, m, fires):
    """The great butte came down with the far side (the ruin's lap runs where it stood,
    onto the rim): its foot stands broken south of the road, in a field of its own
    blocks, with the slot's wedged boulder down among them."""
    import bpy

    for ob in list(c.coll("Buttes").objects):
        if ob.name.startswith(("Great Butte", "Chockstone", "Slot Cutter")):
            bpy.data.objects.remove(ob, do_unlink=True)
    bx, by = std.BUTTE
    stump = c.rock_mass("Great Butte Stump", bx, by - 34.0, 38.0, 12.0, cdr.Z_RIM + 16.0, z0=cdr.Z_RIM - 30.0, n=16, seed=17,
                        angle=std.BUTTE_ANGLE, bands=[(1.15, 0.0), (1.0, 0.15), (0.9, 0.6), (0.7, 1.0)])
    c.paint_rock(stump, ("strata_orange", "wall"), ("talus", "dirt"))
    big = [cp.boulder(c, 3 + k % 2) for k in range(2)]
    for k in range(18):
        a = k * 2.39996
        r = 20.0 + 60.0 * math.sqrt(rnd(k * 1.3 + 4))
        x, y = bx + r * math.cos(a), by + r * math.sin(a) * 0.7
        if not props.clear_of_road(c, x, y, 5.0):
            continue
        c.place(big[k % 2], x, y, m.natural(x, y) - 1.0, rot=k, scale=3.0 + 3.0 * rnd(k + 9), coll="Wreck")
        if k % 4 == 0:
            fires.append((x, y, m.natural(x, y) + 3.0))


GHOST = []


def dress(c, m):
    sc = cs.Scene(c, m)
    sc.lip = cs.find_lip(m)
    # The walls (open where they fell), the land, the start line: round the ruin's road.
    cw.gorge(c, m)
    m.WALL_SPANS.update(cw.rim_walls(c, m))
    cs.land(c, m, sc)
    c.start_line()
    # The canyon's landmarks, from the course's own scenery code, along the standard lap.
    GHOST.append(rk.ghost_route(c, std.ROUTE, width=18.0, bank=7.0))
    with rk.ghost(c, GHOST[0]):
        cs.river(c, sc, std)
        cs.head_falls(c, sc, std)
        cs.side_falls(c, sc, std)
        cs.great_arch(c, sc, std)
        cs.buttes(c, sc, std)
        cs.outpost(c, sc, std)
    fires = []
    fallen_butte(c, m, fires)
    # The bridge and the trestle stand where the ruin's road still runs on them.
    cs.great_bridge(c, sc, m)
    cs.descent_trestle(c, sc, m)
    cs.plants(c, sc, m)
    broken_bridge(c, m, fires)
    rockslides(c, m, fires)
    ruined_portals(c, m, fires)

    def clear(x, y, margin=4.0):
        return props.clear_of_road(c, x, y, margin) and m.gorge_u(x, y) < -6.0

    fires += rk.scorch(c, BURNS, lambda x, y: m.natural(x, y), clear, per=5)
    m.ruin_gameplay(c)
    print("cleared off the new road:", rk.clear_new_road(c, ("Props", "Plants", "Outpost", "Buttes")))
    rk.emit(c, fires)
    groups = ("Props", "Plants", "Outpost", "Wreck")
    c.merge_props(groups)
    joined = [o for name in groups for o in c.coll(name).objects if o.type == "MESH" and o.data.users == 1]
    ter = list(c.coll("Terrain").objects)
    rocks = list(c.coll("Buttes").objects) + list(c.coll("Arch").objects) + list(c.coll("Pass").objects)
    c.preset("sun", ter + rocks, 0.32)
    c.preset("bottoms", ter + rocks, 0.35)
    c.glow(ter + rocks, [], 1.0, (1, 1, 1), base=(0.8, 0.8, 1.0), region=lambda w: 12.0 > w.z > -10.0)
    c.glow(ter + rocks, [], 1.0, (1, 1, 1), base=(0.66, 0.66, 0.95), region=lambda w: w.z <= -10.0)
    c.glow(ter + joined, sc.fires + fires, 10.0, (1.5, 1.0, 0.6), base=1.0)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.entity("ashfall", rate=20, radius=40)
    print("canyon ruin: fires", len(fires), "lap", round(c.length, 1))


ruin_mode.DRESS = dress

if __name__ == "__main__":
    cdr.main()
