# Coral Cove's paint (the beach world's first course; see coral_cove.py): the start arch
# and the beach (umbrellas, towels, surfboards, the lifeguard tower), a row of beach huts
# along the lagoon, the tiki bar on the point, overwater bungalows off the east shore,
# flags and buoys along the boardwalk and the channel, the red-and-white lighthouse on its
# rock with the keeper's hut, the palm avenue, coral in the lagoon's shallows, sea stacks
# and a reef offshore, gulls, and far islands.
# Nothing here changes the driving: the lap, its surfaces and the jump are coral_cove.py's,
# unchanged; everything solid stands clear of the road.
# SPDX-License-Identifier: MIT

import math

import beach_props as bp
import course_kit as kit
import props
import tropic_props as tp
from aurora_scenery import game_entity
from course_kit import rnd
from keep_scenery import Scene, across, clear_of, facing

ROCK = ("cove_rock", "wall")
GRASS = ("cove_grass", "grass")


def _shallows(c):
    """The lagoon and the channel read as clear shallows (their water is visual)."""
    for ob in c.coll("Water").objects:
        if ob.name.startswith(("Lagoon", "Channel")):
            ob.data.materials.clear()
            ob.data.materials.append(c.lib("cove_shallows"))


def beach(sc):
    """The start: the arch over the line, the beach between the road and the sea."""
    c, m = sc.c, sc.dk
    q = c.at(10.0)
    sc.put(tp.start_arch(c, 27.0), q.p.x, q.p.y, q.p.z - 0.2, rot=across(q), coll="Gate", r=0.0)
    # Umbrellas, towels, chairs, surfboards and sandcastles on the sand south of the road.
    k = 0
    for x in range(-6, 70, 9):
        y = -16.0 - 4.0 * rnd(x * 0.37)
        if m.sea_d(x, y) > -5 or not clear_of(c, x, y, 4.0):
            continue
        z = sc.ground(x, y)
        sc.put(bp.umbrella(c, k % 5), x, y, z - 0.2, rot=rnd(x) * 6, coll="Beach", r=0.0)
        sc.put(bp.towel(c, k % 4), x + 1.6, y - 0.6, z + 0.02, rot=0.3 * (k % 3), coll="Beach", role="visual")
        if k % 2 == 0:
            sc.put(bp.deck_chair(c, k % 3), x - 1.8, y + 0.4, z, rot=math.pi + 0.2, coll="Beach", r=0.8)
        if k % 3 == 1:
            sc.put(bp.surfboard(c, k % 4), x + 3.2, y + 1.6, z - 0.4, rot=0.2, coll="Beach", r=0.5)
        if k % 4 == 2:
            sc.put(bp.sandcastle(c, k % 2), x - 2.5, y - 3.0, z - 0.1, coll="Beach", role="visual")
        if k % 3 == 0:
            sc.put(bp.beach_ball(c, k % 3), x + 2.0, y + 2.5, z + 0.3, coll="Beach", role="visual")
        k += 1
    x, y = 34.0, -20.0
    sc.put(tp.lifeguard_tower(c), x, y, sc.ground(x, y) - 0.2, rot=math.pi, coll="Beach", r=2.2)
    for x, y in ((14.0, -24.0), (52.0, -25.0)):
        sc.put(tp.flag_pole(c, "cove_flag", 7.0), x, y, sc.ground(x, y) - 0.3, rot=0.4, coll="Beach", r=0.3)
    # The beach huts along the lagoon's south shore, facing the road.
    for k, x in enumerate((8.0, 16.0, 24.0, 47.0, 55.0)):
        y = 16.5
        if not clear_of(c, x, y, 4.5):
            continue
        sc.put(tp.beach_hut(c, k), x, y, sc.ground(x, y) - 0.1, rot=math.pi, coll="Beach", r=2.4)


def point(sc):
    """The point south-east of the sweeper: the tiki bar, palms, torches; and the
    overwater bungalows off the east shore with their footbridges."""
    c, m = sc.c, sc.dk
    x, y = 98.0, -12.0
    if clear_of(c, x, y, 6.0):
        sc.put(bp.tiki_bar(c), x, y, sc.ground(x, y) - 0.2, rot=facing(x, y, 65.0, 20.0), coll="Beach", r=4.5)
    for k, (x, y) in enumerate(((86.0, -18.0), (110.0, -6.0), (118.0, 10.0), (112.0, -18.0))):
        if clear_of(c, x, y, 3.0) and m.sea_d(x, y) < -2:
            sc.put(bp.tiki_torch(c, k % 2), x, y, sc.ground(x, y) - 0.2, coll="Beach", r=0.4)
            sc.flames.append((x, y, sc.ground(x, y) + 2.6))
    for k, (x, y, rot) in enumerate(((152.0, 14.0, 0.1), (160.0, 34.0, -0.1), (150.0, 54.0, 0.15))):
        sc.put(tp.bungalow(c, k), x, y, 0.0, rot=rot - math.pi / 2, coll="Bungalows", role="visual")
        sc.put(tp.boardwalk(c, 24.0), x - 26.0, y, 0.0, rot=-math.pi / 2, coll="Bungalows", role="visual")
    sc.put(tp.sailboat(c, 1), 138.0, 92.0, 0.0, rot=0.6, coll="Boats", role="visual")
    sc.put(tp.sailboat(c, 2), 182.0, -10.0, 0.0, rot=-0.4, coll="Boats", role="visual")
    sc.put(tp.sailboat(c, 0), 40.0, -78.0, 0.0, rot=1.2, coll="Boats", role="visual")


def boardwalk(sc):
    """The boardwalk's flags, the channel's buoys, the signs before the jump."""
    c, m = sc.c, sc.dk
    S = m.TO_ROAD
    s0, s1 = S(m.SEG[2]) + 6, S(m.SEG[3]) - 4
    lip, land = S(m.LIP), S(m.LAND)
    s = s0
    k = 0
    while s < s1:
        if not (lip - 16 < s < land + 10):
            q = c.at(s)
            for side in (-1, 1):
                p = q.side(side * (q.w / 2 + 2.6))
                g = sc.ground(p.x, p.y)
                sc.put(tp.flag_pole(c, "cove_flag", 4.0 + (q.p.z - g)), p.x, p.y, g - 0.3, rot=math.pi / 2 if side > 0 else -math.pi / 2,
                       coll="Boardwalk", role="visual")
        s += 14.0
        k += 1
    # Buoys down the channel, either side of the jump.
    for x, y in ((62.0, 50.0), (76.0, 62.0), (88.0, 70.0), (120.0, 79.0), (132.0, 80.0)):
        sc.put(tp.buoy(c, "cove_lighthouse" if int(x) % 2 else "cove_awning_sun"), x, y, -0.2, coll="Water Props", role="visual")
    # Arrow signs either side of the boardwalk before the lip.
    q = c.at(lip - 30)
    for side in (-1, 1):
        p = q.side(side * (q.w / 2 + 3.5))
        g = sc.ground(p.x, p.y)
        sc.put(tp.signpost(c), p.x, p.y, g + max(0.0, q.p.z - g - 1.2), rot=math.atan2(q.t.y, q.t.x) - math.pi / 2 + math.pi,
               coll="Boardwalk", role="visual")


def headland(sc):
    """The lighthouse on its rock in the hairpin; the keeper's hut, a flag and boulders on
    the headland beyond."""
    c, m = sc.c, sc.dk
    lx, ly = m.LIGHTHOUSE
    sc.put(tp.lighthouse(c), lx, ly, 12.2, coll="Headland", role="visual")
    sc.lamps.append((lx, ly, 12.2 + 17.8))
    # Well back from the hairpin, so its run-off stays open sand (as in the greybox).
    x, y = lx - 2.0, ly + 58.0
    if clear_of(c, x, y, 5.0):
        sc.put(tp.beach_hut(c, 3), x, y, sc.ground(x, y) - 0.1, rot=math.pi, coll="Headland", r=2.4)
        sc.put(tp.flag_pole(c, "cove_flag", 9.0), x + 5.0, y + 1.0, sc.ground(x + 5.0, y + 1.0) - 0.3, coll="Headland", r=0.3)
    for k in range(10):
        a = 0.2 + k * 0.33
        r = 50.0 + 8.0 * rnd(k * 3.1)
        x, y = lx + r * math.cos(a), ly + r * math.sin(a)
        if clear_of(c, x, y, 3.0):
            sc.put(props.boulder(c, "cove_rock", k % 3), x, y, sc.ground(x, y) - 0.4, rot=k, scale=0.8 + 0.5 * rnd(k), coll="Headland", r=1.6)


def avenue(sc):
    """The palm avenue along the palm straight, torches between the palms."""
    c, m = sc.c, sc.dk
    S = m.TO_ROAD
    s0, s1 = S(m.SEG[5]) + 20, S(m.SEG[7]) + 10
    s = s0
    k = 0
    while s < s1:
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 6.0 + 0.8 * (k % 2)))
            if clear_of(c, p.x, p.y, 5.2):
                sc.put(bp.coconut_palm(c, (k + (side > 0)) % 3), p.x, p.y, sc.ground(p.x, p.y) - 0.3,
                       rot=math.atan2(q.r.y * side, q.r.x * side) + math.pi, coll="Palms", r=0.6)
            if k % 2 == 1:
                p = q.side(side * (q.w / 2 + 2.8))
                if clear_of(c, p.x, p.y, 2.2):
                    sc.put(bp.tiki_torch(c, k % 2), p.x, p.y, sc.ground(p.x, p.y) - 0.2, coll="Palms", role="visual")
                    sc.flames.append((p.x, p.y, sc.ground(p.x, p.y) + 2.6))
        s += 9.0
        k += 1


def lagoon(sc):
    """Coral heads in the lagoon's shallows; starfish, shells and a canoe on its shore."""
    c, m = sc.c, sc.dk
    cx, cy, r = m.LAGOON
    for k in range(14):
        a = k * 2.4
        rr = r * (0.2 + 0.7 * rnd(k * 1.7))
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        sc.put(tp.coral(c, k % 3), x, y, -1.9 + 0.3 * rnd(k), rot=k * 1.3, scale=0.9 + 0.6 * rnd(k * 2.3), coll="Coral", role="visual")
    for k in range(8):
        a = k * 0.8 + 3.6
        x, y = cx + (r + 3.5) * math.cos(a), cy + (r + 3.5) * math.sin(a)
        if clear_of(c, x, y, 2.0):
            z = sc.ground(x, y)
            sc.put(bp.starfish(c, k % 3) if k % 2 else bp.shell(c), x, y, z + 0.05, rot=k, coll="Coral", role="visual")
    x, y = cx - r - 2.0, cy + 6.0
    if clear_of(c, x, y, 3.0):
        sc.put(bp.canoe(c, 0), x, y, sc.ground(x, y) + 0.1, rot=0.9, coll="Coral", role="visual")
    # Coral along the channel's banks too.
    for k, (x, y) in enumerate(((58.0, 46.0), (70.0, 56.0), (84.0, 66.0), (118.0, 83.0), (128.0, 77.0))):
        sc.put(tp.coral(c, k + 1), x, y, -1.8, rot=k, scale=0.8, coll="Coral", role="visual")


def offshore(sc):
    """Sea stacks with palms, a reef line breaking white, far islands."""
    c, m = sc.c, sc.dk
    for k, (x, y, rx, h) in enumerate(((70.0, -95.0, 9.0, 16.0), (-50.0, -120.0, 12.0, 22.0), (210.0, -70.0, 10.0, 18.0),
                                       (235.0, 60.0, 14.0, 26.0), (-110.0, -60.0, 7.0, 12.0))):
        tp.rock_island(c, "Sea Stack %d" % k, x, y, rx, rx * 0.9, h, ROCK, GRASS, seed=60 + k)
        for j in range(2):
            sc.put(bp.coconut_palm(c, j), x + 2.0 * (j - 0.5), y + 1.5 * j, h - 2.5, rot=k + j * 2, scale=0.8, coll="Offshore", role="visual")
    # The reef: a ragged white line of surf a way out.
    pts = [(-200.0 + 25 * k, -62.0 - 10 * math.sin(k * 0.7) - 5 * rnd(k)) for k in range(18)]
    c.ribbon("Reef Surf", pts, 6.0, 0.08, c.lib("cove_reef"), role="visual", steps=2)
    for k in range(9):
        a = -0.4 + k * 0.42
        r = 900 + 380 * rnd(k * 5.1)
        x, y = 60 + r * math.cos(a - math.pi / 2), 40 + r * math.sin(a - math.pi / 2)
        tp.rock_island(c, "Far Island %d" % k, x, y, 60 + 40 * rnd(k), 50 + 40 * rnd(k + 3), 30 + 50 * rnd(k + 7), ROCK, GRASS, seed=80 + k, z0=-20.0, hill=True)
    for k in range(5):
        a = math.pi * 0.45 + k * 0.35
        r = 760 + 300 * rnd(k * 9.1)
        x, y = 60 + r * math.cos(a), 40 + r * math.sin(a)
        tp.rock_island(c, "North Island %d" % k, x, y, 80 + 60 * rnd(k), 70 + 50 * rnd(k + 3), 50 + 60 * rnd(k + 7), ROCK, GRASS, seed=95 + k, z0=-20.0, hill=True)


def nature(sc):
    """Coconut palms, bushes, flowers and dune grass on the dunes, clear of the road."""
    c, m = sc.c, sc.dk

    def ok(x, y, z, margin):
        return z > 0.8 and clear_of(c, x, y, margin) and sc.free(x, y, 2.5)

    props.scatter(c, bp.coconut_palm(c, 0), 30, (-150, 290, -40, 250), lambda x, y, z: ok(x, y, z, 6.0), [sc.ter], seed=3, coll="Palms")
    props.scatter(c, bp.coconut_palm(c, 2), 22, (-150, 290, -40, 250), lambda x, y, z: ok(x, y, z, 6.0), [sc.ter], seed=5, coll="Palms")
    props.scatter(c, props.bush(c, 0), 30, (-150, 290, -40, 250), lambda x, y, z: ok(x, y, z, 4.0), [sc.ter], seed=7, coll="Nature", role="visual")
    props.scatter(c, props.flowers(c), 26, (-150, 290, -40, 250), lambda x, y, z: ok(x, y, z, 3.0), [sc.ter], seed=9, coll="Nature", role="visual")
    props.scatter(c, tp.dune_grass(c), 120, (-150, 290, -60, 250), lambda x, y, z: z > 0.4 and clear_of(c, x, y, 2.0), [sc.ter], seed=11,
                  coll="Nature", role="visual", scale=(0.8, 1.6))
    game_entity(c, "birds", 82.0, 110.0, 40.0, radius=40, count=5, speed=0.2, seed=3, color="#ffffff")
    game_entity(c, "birds", 30.0, -40.0, 22.0, radius=60, count=4, speed=0.16, seed=7, color="#f4f4f0")
    c.entity("sparkles", rate=10, radius=30)


def light(sc):
    c = sc.c
    groups = ("Gate", "Beach", "Bungalows", "Boats", "Boardwalk", "Water Props", "Headland", "Palms", "Coral", "Offshore", "Nature")
    c.merge_props(groups, cell=220.0)
    built = [o for name in groups for o in c.coll(name).objects if o.type == "MESH" and o.data.users == 1]
    c.preset("sun", [sc.ter] + built, 0.25)
    c.glow([sc.ter] + built, sc.flames + sc.lamps, 9.0, (1.4, 1.1, 0.7), base=1.0)
    kit.paint.shade_roads(c.pieces, 0.3)


def build(c, m, ter):
    sc = Scene(c, m, ter)
    sc.lamps = []
    _shallows(c)
    beach(sc)
    point(sc)
    boardwalk(sc)
    headland(sc)
    avenue(sc)
    lagoon(sc)
    offshore(sc)
    nature(sc)
    for x, y, z in sc.flames:
        game_entity(c, "torch", x, y, z)
    light(sc)
    print("cove scenery: props", c.prop_count, "flames", len(sc.flames))
