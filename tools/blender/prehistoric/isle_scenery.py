# Volcano Isle's paint (the beach world's third course; see volcano_isle.py): the start
# arch on the black-sand beach, outrigger canoes and drying nets, the hot springs
# steaming beside the flats (rocks and bamboo round them), jungle all up the island's
# flanks (palms, tree ferns, cycads, big leaves, flowers), tiki torches at the lava tube's
# mouths and old lava glowing in its walls, signs and flags along the cliff ledge before
# the jump, coral in the lagoon, the fishing village of stilt huts along the shore with
# its dock and boats, sea stacks and far islands, and a wisp of steam off the dormant
# volcano's summit. Nothing here changes the driving: the lap, its surfaces, the geysers
# and the jump are volcano_isle.py's, unchanged; everything solid stands clear of the
# road.
# SPDX-License-Identifier: MIT

import math

import beach_props as bp
import course_kit as kit
import impact_props as ip
import props
import tropic_props as tp
from aurora_scenery import game_entity
from course_kit import rnd
from keep_scenery import Scene, across, clear_of, facing

ROCK = ("isle_rock", "wall")
GRASS = ("isle_jungle", "grass")


def _waters(c):
    """The lagoon and the hot springs read as their own water (it's all visual)."""
    for ob in c.coll("Water").objects:
        if ob.name.startswith("Lagoon"):
            ob.data.materials.clear()
            ob.data.materials.append(c.lib("isle_lagoon"))
        elif ob.name.startswith("Spring"):
            ob.data.materials.clear()
            ob.data.materials.append(c.lib("isle_spring"))


def beach(sc):
    """The start arch, and the black-sand beach south of the road: canoes drawn up,
    nets drying on poles, driftwood, torches."""
    c, m = sc.c, sc.dk
    q = c.at(10.0)
    sc.put(tp.start_arch(c, 27.0, flag="cove_flag", rope="isle_rail"), q.p.x, q.p.y, q.p.z - 0.2, rot=across(q), coll="Gate", r=0.0)
    k = 0
    for x in range(-40, 60, 11):
        y = -13.0 - 3.0 * rnd(x * 0.31)
        if m.sea_d(x, y) > -4 or not clear_of(c, x, y, 4.0):
            continue
        z = sc.ground(x, y)
        if k % 3 == 0:
            sc.put(bp.canoe(c, k % 2), x, y, z + 0.05, rot=1.4 + 0.3 * rnd(k), coll="Beach", role="visual")
        elif k % 3 == 1:
            for j in (-1, 1):
                sc.put(bp.bamboo_pole(c), x + 2.2 * j, y, z - 0.3, coll="Beach", role="visual")
            sc.put(tp.flag_pole(c, "isle_net", 0.1, "isle_huts"), x, y, z + 1.6, rot=0.0, coll="Beach", role="visual")
        else:
            sc.put(bp.tiki_torch(c, k % 2), x, y, z - 0.2, coll="Beach", r=0.4)
            sc.flames.append((x, y, z + 2.6))
        k += 1


def springs(sc):
    """Rocks and bamboo round the hot springs, steam rising off them."""
    c, m = sc.c, sc.dk
    for k, (x, y, r) in enumerate(m.SPRINGS):
        z, _ = m.near_road_z(x, y)
        for j in range(7):
            a = j * math.tau / 7 + k
            px, py = x + (r + 1.0) * math.cos(a), y + (r + 1.0) * math.sin(a)
            if clear_of(c, px, py, 2.0):
                sc.put(props.boulder(c, "isle_rock", j % 3), px, py, sc.ground(px, py) - 0.3, rot=j, scale=0.7 + 0.4 * rnd(j + k), coll="Springs",
                       role="visual")
        game_entity(c, "steam", x, y, z - 0.8)
        game_entity(c, "steam", x + r * 0.4, y - r * 0.3, z - 0.8)


def jungle(sc):
    """The jungle up the island's flanks, thick away from the road."""
    c, m = sc.c, sc.dk

    def ok(margin, lo=5.0):
        def f(x, y, z):
            return z > lo and m.sea_d(x, y) < -10 and m.lagoon_d(x, y) > 6 and clear_of(c, x, y, margin) and sc.free(x, y, 2.0)

        return f

    area = (-250, 290, 10, 370)
    for k in range(3):
        props.scatter(c, bp.coconut_palm(c, k), 26, area, ok(6.0), [sc.ter], seed=3 + k, coll="Jungle")
    for k in range(3):
        props.scatter(c, ip.tree_fern(c, k), 22, area, ok(6.0, 8.0), [sc.ter], seed=13 + k, coll="Jungle")
    for k in range(4):
        props.scatter(c, ip.cycad(c, k), 16, area, ok(4.0), [sc.ter], seed=23 + k, coll="Jungle", role="visual")
    props.scatter(c, props.big_leaf_plant(c, 0), 50, area, ok(3.0), [sc.ter], seed=31, coll="Jungle", role="visual", scale=(0.8, 1.6))
    props.scatter(c, props.big_leaf_plant(c, 1), 50, area, ok(3.0), [sc.ter], seed=33, coll="Jungle", role="visual", scale=(0.8, 1.6))
    props.scatter(c, props.fern(c), 90, area, ok(2.5), [sc.ter], seed=35, coll="Jungle", role="visual", scale=(0.8, 1.8))
    props.scatter(c, props.flowers(c), 40, area, ok(2.5), [sc.ter], seed=37, coll="Jungle", role="visual")
    props.scatter(c, props.bush(c, 1), 40, area, ok(3.0), [sc.ter], seed=39, coll="Jungle", role="visual")
    # Along the shore too, palms leaning out over the sand.
    props.scatter(c, bp.coconut_palm(c, 1), 20, (-250, 290, -30, 60), lambda x, y, z: z > 0.8 and m.sea_d(x, y) < -3 and clear_of(c, x, y, 6.0),
                  [sc.ter], seed=41, coll="Jungle")


def tube(sc):
    """Torches either side of the lava tube's mouths; old lava still glowing in its walls."""
    c, m = sc.c, sc.dk
    for d in (m.TUBE[0] - 4.0, m.TUBE[1] + 2.0):
        q = c.at(m.TO_ROAD(d))
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 2.4))
            if clear_of(c, p.x, p.y, 1.5):
                sc.put(bp.tiki_torch(c, 1), p.x, p.y, sc.ground(p.x, p.y) - 0.2, coll="Tube", r=0.4)
                sc.flames.append((p.x, p.y, sc.ground(p.x, p.y) + 2.6))
    s0, s1 = m.TO_ROAD(m.TUBE[0]) + 10, m.TO_ROAD(m.TUBE[1]) - 8
    k = 0
    s = s0
    while s < s1:
        q = c.at(s)
        for side in (-1, 1):
            k += 1
            p = q.side(side * (q.w / 2 + 2.2))
            sc.put(tp.coral(c, k % 3), p.x, p.y, q.p.z + 1.0 + 3.0 * rnd(k), rot=k, scale=0.5, coll="Tube", role="visual")
            sc.embers.append((p.x, p.y, q.p.z + 2.0))
        s += 18.0


def ledge(sc):
    """Flags along the cliff ledge, signs before its lip."""
    c, m = sc.c, sc.dk
    lip = m.TO_ROAD(m.LIP)
    s = m.TO_ROAD(m.SEG[17])
    while s < lip - 20:
        q = c.at(s)
        p = q.side(-(q.w / 2 + 2.4))
        if clear_of(c, p.x, p.y, 1.5):
            sc.put(tp.flag_pole(c, "cove_flag", 5.0, "isle_huts"), p.x, p.y, sc.ground(p.x, p.y) - 0.3, coll="Ledge", role="visual")
        s += 16.0
    q = c.at(lip - 30)
    for side in (-1, 1):
        p = q.side(side * (q.w / 2 + 3.2))
        if clear_of(c, p.x, p.y, 1.5):
            sc.put(tp.signpost(c, "cove_sign", "isle_huts"), p.x, p.y, sc.ground(p.x, p.y), rot=math.atan2(q.t.y, q.t.x) + math.pi / 2, coll="Ledge",
                   role="visual")


def lagoon(sc):
    """Coral in the lagoon under the jump; a canoe on its shore."""
    c, m = sc.c, sc.dk
    cx, cy, rx, ry = m.LAGOON
    for k in range(16):
        a = k * 2.4
        rr = 0.2 + 0.65 * rnd(k * 1.7)
        x, y = cx + rx * rr * math.cos(a), cy + ry * rr * math.sin(a)
        sc.put(tp.coral(c, k % 3), x, y, -1.9 + 0.3 * rnd(k), rot=k * 1.3, scale=0.9 + 0.6 * rnd(k * 2.3), coll="Lagoon", role="visual")


def village(sc):
    """The fishing village along the shore: stilt huts either side of its S, a dock out
    into the sea with boats, torches, nets."""
    c, m = sc.c, sc.dk
    S = m.TO_ROAD
    k = 0
    s = S(m.SEG[20]) + 10
    while s < S(m.SEG[24]):
        q = c.at(s)
        for side in (-1, 1):
            k += 1
            p = q.side(side * (q.w / 2 + 8.0 + 2.0 * (k % 2)))
            if not clear_of(c, p.x, p.y, 5.0) or not sc.free(p.x, p.y, 3.0):
                continue
            z = sc.ground(p.x, p.y)
            if z < 0.6:
                sc.put(tp.bungalow(c, k % 3), p.x, p.y, 0.0, rot=facing(p.x, p.y, q.p.x, q.p.y), coll="Village", role="visual")
            else:
                sc.put(tp.beach_hut(c, k % 4), p.x, p.y, z - 0.1, rot=facing(p.x, p.y, q.p.x, q.p.y), coll="Village", r=2.6)
            if k % 3 == 0:
                t = q.side(side * (q.w / 2 + 3.0))
                if clear_of(c, t.x, t.y, 1.5):
                    sc.put(bp.tiki_torch(c, k % 2), t.x, t.y, sc.ground(t.x, t.y) - 0.2, coll="Village", r=0.4)
                    sc.flames.append((t.x, t.y, sc.ground(t.x, t.y) + 2.6))
        s += 15.0
    # The dock and the boats, off the village to the south.
    q = c.at(S(m.SEG[22]))
    x, y = q.p.x, -36.0
    sc.put(tp.boardwalk(c, 26.0), x, y, 0.0, rot=0.0, coll="Village", role="visual")
    for j, (dx, dy) in enumerate(((6.0, -12.0), (-8.0, -22.0), (14.0, -30.0))):
        sc.put(tp.sailboat(c, j), x + dx, y + dy, 0.0, rot=0.5 * j, coll="Boats", role="visual")
    sc.put(tp.rowboat(c), x - 4.0, y - 6.0, 0.0, rot=1.2, coll="Boats", role="visual")


def offshore(sc):
    """Sea stacks topped with palms, far islands, the reef's surf."""
    c, m = sc.c, sc.dk
    for k, (x, y, rx, h) in enumerate(((60.0, -95.0, 9.0, 18.0), (-120.0, -80.0, 12.0, 24.0), (-260.0, 60.0, 10.0, 16.0),
                                       (220.0, -60.0, 12.0, 22.0), (-200.0, -150.0, 8.0, 14.0))):
        tp.rock_island(c, "Sea Stack %d" % k, x, y, rx, rx * 0.9, h, ROCK, GRASS, seed=60 + k)
        sc.put(bp.coconut_palm(c, k % 3), x, y, h - 2.5, rot=k, scale=0.8, coll="Offshore", role="visual")
    pts = [(-260.0 + 28 * k, -58.0 - 9 * math.sin(k * 0.7) - 5 * rnd(k)) for k in range(20)]
    c.ribbon("Reef Surf", pts, 6.0, 0.08, c.lib("cove_reef"), role="visual", steps=2)
    for k in range(9):
        a = -0.3 + k * 0.45
        r = 900 + 380 * rnd(k * 5.1)
        x, y = 20 + r * math.cos(a - math.pi / 2), r * math.sin(a - math.pi / 2)
        tp.rock_island(c, "Far Island %d" % k, x, y, 60 + 40 * rnd(k), 50 + 40 * rnd(k + 3), 30 + 50 * rnd(k + 7), ROCK, GRASS, seed=80 + k, z0=-20.0,
                       hill=True)
    vx, vy = m.VOLCANO
    game_entity(c, "steam", vx, vy, 200.0)
    game_entity(c, "birds", 0.0, 120.0, 46.0, radius=60, count=6, speed=0.2, seed=3, color="#ffffff")
    game_entity(c, "birds", 40.0, -50.0, 24.0, radius=60, count=4, speed=0.16, seed=7, color="#f4f4f0")
    c.entity("sparkles", rate=8, radius=30)


def light(sc):
    c = sc.c
    groups = ("Gate", "Beach", "Springs", "Jungle", "Tube", "Ledge", "Lagoon", "Village", "Boats", "Offshore")
    c.merge_props(groups, cell=220.0)
    built = [o for name in groups for o in c.coll(name).objects if o.type == "MESH" and o.data.users == 1]
    rocks = [o for o in c.coll("Rocks").objects if o.type == "MESH"]
    c.preset("sun", [sc.ter] + built + rocks, 0.25)
    c.glow([sc.ter] + built + rocks, sc.flames, 9.0, (1.4, 1.1, 0.7), base=1.0)
    c.glow([sc.ter] + rocks, sc.embers, 7.0, (1.6, 0.8, 0.45), base=1.0)
    kit.paint.shade_roads(c.pieces, 0.3)


def build(c, m, ter):
    sc = Scene(c, m, ter)
    sc.embers = []
    _waters(c)
    beach(sc)
    springs(sc)
    tube(sc)
    ledge(sc)
    lagoon(sc)
    village(sc)
    jungle(sc)
    offshore(sc)
    for x, y, z in sc.flames:
        game_entity(c, "torch", x, y, z)
    if getattr(m, "RUIN", False):
        return sc  # (the ruin lights it, with its own wreckage)
    light(sc)
    print("isle scenery: props", c.prop_count, "flames", len(sc.flames))
    return sc
