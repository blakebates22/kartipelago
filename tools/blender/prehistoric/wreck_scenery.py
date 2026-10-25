# Shipwreck Bay's paint (the beach world's second course; see shipwreck_bay.py): a pirate
# cove at golden hour. The skull-flag arch over the line, lanterns along the rolling pier,
# the galleon dressed (dark hull, masts and patched sails, the stern castle and its lit
# windows, cannons out of her ports, the bowsprit), barrels and crates on the sandbar, the
# fallen mast's rigging, rowboats in the river mouth, the stockade camp with its lookout,
# cannons and campfire, Skull Rock's carved face and the treasure at its feet, the shanty
# huts under the cove's cliffs, an old wreck far out, sea stacks and far islands.
# Nothing here changes the driving: the lap, its surfaces, the pier's humps and the mast
# jump are shipwreck_bay.py's, unchanged; everything solid stands clear of the road.
# SPDX-License-Identifier: MIT

import math

import beach_props as bp
import course_kit as kit
import props
import tropic_props as tp
from aurora_scenery import Mesh, game_entity
from canyon_props import _beam
from course_kit import rnd
from keep_scenery import Scene, across, clear_of, facing
from props import cuboid

ROCK = ("wreck_rock", "wall")
GRASS = ("wreck_grass", "grass")
HULL = ("wreck_hull", "wall")


def lantern(sc, x, y, z, scale=1.0, rot=0.0, coll="Lanterns"):
    sc.put(tp.lantern_post(sc.c), x, y, z, rot=rot, scale=scale, coll=coll, role="visual")
    fx, fy = -math.sin(rot) * 0.8 * scale, math.cos(rot) * 0.8 * scale
    sc.flames.append((x + fx, y + fy, z + 2.7 * scale))


def gate(sc):
    c = sc.c
    q = c.at(10.0)
    sc.put(tp.start_arch(c, 27.0, flag="wreck_flag", wood="wreck_post", rope="wreck_rail"), q.p.x, q.p.y, q.p.z - 0.2, rot=across(q), coll="Gate")
    # Barrels, crates and a cannon either side of the start, on the beach.
    for k, (x, y) in enumerate(((4.0, -14.0), (20.0, -15.0), (-10.0, 14.0), (14.0, 15.0), (28.0, 16.0))):
        if not clear_of(c, x, y, 3.0):
            continue
        z = sc.ground(x, y)
        sc.put(tp.barrel(c), x, y, z - 0.05, rot=k, coll="Camp", r=0.6)
        sc.put(tp.crate(c), x + 1.4, y + 0.6, z - 0.05, rot=k * 0.7, coll="Camp", r=0.8)
        if k % 2:
            sc.put(tp.barrel(c), x - 0.8, y + 1.3, z - 0.05, rot=k * 2, coll="Camp", r=0.6)


def pier(sc):
    """Lanterns on tall posts either side of the pier, a rowboat tied up."""
    c, m = sc.c, sc.dk
    S = m.TO_ROAD
    s = S(m.SEG[2]) + 4
    while s < S(m.SEG[3]):
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 1.4))
            lantern(sc, p.x, p.y, -0.6, scale=1.0 + (q.p.z + 0.6) / 3.6, rot=math.atan2(q.r.y * -side, q.r.x * -side) - math.pi / 2)
        s += 13.0
    q = c.at(S(m.SEG[2]) + 24)
    p = q.side(q.w / 2 + 5.0)
    sc.put(tp.rowboat(c), p.x, p.y, 0.1, rot=math.atan2(q.t.y, q.t.x) - math.pi / 2, coll="Boats", role="visual")
    q = c.at(S(m.SEG[2]) + 40)
    p = q.side(-(q.w / 2 + 6.0))
    sc.put(tp.rowboat(c), p.x, p.y, 0.1, rot=math.atan2(q.t.y, q.t.x) - math.pi / 2 + 0.4, coll="Boats", role="visual")


def galleon(sc):
    """The wreck dressed: her hull's planks, masts and sails on the deck over the hold, the
    stern castle, the bowsprit, cannons out of her ports, flags; barrels on the sandbar."""
    c, m = sc.c, sc.dk
    for ob in c.coll("Props").objects:
        if ob.name.startswith("Galleon"):
            ob.data.materials.clear()
            ob.data.materials.append(c.lib(*HULL))
    S = m.TO_ROAD
    h0, h1 = S(m.HULL[0]) - 6.0, S(m.HULL[1]) + 4.0
    deck = lambda s: c.at(s).p.z + 6.5  # noqa: E731
    mid = (h0 + h1) / 2
    qm = c.at(mid)
    rot = math.atan2(qm.t.y, qm.t.x) - math.pi / 2  # the ship's length along the road
    # Masts: the foremast broken, the mainmast whole with its sails, the mizzen torn.
    for s, h, broken in ((h0 + 12.0, 14.0, True), (mid, 18.0, False), (h1 - 12.0, 13.0, False)):
        q = c.at(s)
        sc.put(tp.mast(c, h, broken), q.p.x, q.p.y, deck(s) - 0.4, rot=rot, coll="Galleon", role="visual")
        if not broken:
            sc.put(tp.sail(c, 8.0 if h > 15 else 6.0, 6.0 if h > 15 else 4.5, int(h < 15)), q.p.x, q.p.y, deck(s) + h * 0.62 - 0.2,
                   rot=rot, coll="Galleon", role="visual")
            if h > 15:
                sc.put(tp.sail(c, 6.0, 4.0, 1), q.p.x, q.p.y, deck(s) + h * 0.9 - 0.2, rot=rot, coll="Galleon", role="visual")
                sc.put(tp.flag_pole(c, "wreck_flag", 3.0, "wreck_iron"), q.p.x, q.p.y, deck(s) + h - 0.4, rot=rot, coll="Galleon", role="visual")
    # The stern castle: a raised cabin with lit windows; a lantern each side.
    q = c.at(h1 - 4.0)
    ms = Mesh()
    z0 = deck(h1 - 4.0)
    ms.add(HULL, lambda bm: cuboid(bm, (q.p.x, q.p.y, z0 + 2.2), (8.0, 15.0, 4.4), rot=rot + math.pi / 2))
    ms.add(("wreck_trim", "wall"), lambda bm: cuboid(bm, (q.p.x, q.p.y, z0 + 4.6), (8.6, 15.6, 0.4), rot=rot + math.pi / 2))
    back = q.p + q.t * 4.05
    ms.add(("wreck_lantern", "wall"), lambda bm: cuboid(bm, (back.x, back.y, z0 + 2.4), (0.2, 9.0, 1.4), rot=rot + math.pi / 2))
    # The bowsprit, out over the bow.
    qb = c.at(h0 + 1.0)
    tip = qb.p - qb.t * 14.0
    ms.add(HULL, lambda bm: _beam(bm, (qb.p.x, qb.p.y, deck(h0 + 1.0) - 1.0), (tip.x, tip.y, deck(h0 + 1.0) + 4.0), 0.5))
    ms.build(c, "Galleon Dress", "Galleon", "visual")
    for side in (-1, 1):
        p = q.side(side * 7.4)
        sc.flames.append((p.x, p.y, z0 + 3.0))
    # Lanterns hung from the deck beams down the hold (high over the road), lighting it.
    hold = Mesh()
    for k in range(4):
        s = S(m.HULL[0]) + 6.0 + k * (S(m.HULL[1]) - S(m.HULL[0]) - 12.0) / 3
        ql = c.at(s)
        z = ql.p.z + 5.4
        hold.add(("wreck_iron", "wall"), lambda bm, ql=ql, z=z: _beam(bm, (ql.p.x, ql.p.y, z + 0.5), (ql.p.x, ql.p.y, ql.p.z + 6.4), 0.05))
        hold.add(("wreck_lantern", "wall"), lambda bm, ql=ql, z=z: cuboid(bm, (ql.p.x, ql.p.y, z), (0.45, 0.45, 0.7)))
        sc.flames.append((ql.p.x, ql.p.y, z))
    hold.build(c, "Hold Lanterns", "Galleon", "visual")
    # Cannons out of her ports, both sides.
    for k in range(4):
        s = h0 + 10.0 + k * (h1 - h0 - 20.0) / 3
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * 11.6)
            sc.put(tp.cannon(c), p.x, p.y, q.p.z + 2.2, rot=math.atan2(q.r.y * side, q.r.x * side) - math.pi / 2, coll="Galleon", role="visual")
    # Barrels, crates and planks washed up on the sandbar, clear of the road.
    x0, x1, y0, y1 = m.BAR
    for k in range(18):
        x = x0 + (x1 - x0) * rnd(k * 1.7 + 3)
        y = y0 + (y1 - y0) * rnd(k * 2.9 + 5)
        if not clear_of(c, x, y, 3.0) or m.bar_d(x, y) < 2:
            continue
        z = sc.ground(x, y)
        proto = (tp.barrel(c), tp.crate(c), tp.plank_pile(c))[k % 3]
        sc.put(proto, x, y, z - 0.1, rot=k * 1.9, coll="Sandbar", role="visual" if k % 3 == 2 else "both", r=0.8)
    for k, (x, y) in enumerate(((x0 + 6, y0 + 4), (x1 - 4, y1 - 6), (x0 + 30, y0 + 2))):
        if clear_of(c, x, y, 3.0):
            sc.put(tp.anchor(c), x, y, sc.ground(x, y) - 0.6, rot=k * 2.1, coll="Sandbar", role="visual")


def mast_jump(sc):
    """The fallen mast's rigging (ropes trailing down to the water), a crow's nest
    sunk beside it, rowboats in the river mouth, reeds on its banks."""
    c, m = sc.c, sc.dk
    S = m.TO_ROAD
    s0, lip = S(m.SEG[8]) + 8, S(m.LIP)
    ms = Mesh()
    for k in range(5):
        s = s0 + (lip - 8 - s0) * k / 4
        q = c.at(s)
        for side in (-1, 1):
            a = q.side(side * (q.w / 2 + 0.2))
            b = q.side(side * (q.w / 2 + 5.0 + 2.0 * (k % 2)))
            ms.add(("wreck_rail", "wall"), lambda bm, a=a, b=b, q=q: _beam(bm, (a.x, a.y, q.p.z - 0.4), (b.x, b.y, -0.2), 0.12))
    ms.build(c, "Mast Rigging", "Galleon", "visual")
    q = c.at(s0 + 10)
    p = q.side(-(q.w / 2 + 8.0))
    sc.put(tp.sail(c, 7.0, 5.0, 1), p.x, p.y, 3.0, rot=math.atan2(q.t.y, q.t.x) + 0.3, coll="Galleon", role="visual")
    for k, (x, y) in enumerate(((150.0, -4.0), (210.0, -22.0), (120.0, -16.0))):
        if clear_of(c, x, y, 4.0):
            sc.put(tp.rowboat(c), x, y, 0.1, rot=k * 1.3 + 0.4, coll="Boats", role="visual")
    for k in range(10):
        x = 70.0 + 14.0 * k
        for side in (-1, 1):
            y = m.RIVER_Y + side * (m.RIVER_HALF + 2.5) + 2.0 * rnd(k + side)
            if clear_of(c, x, y, 3.0):
                sc.put(props.reeds(c), x, y, sc.ground(x, y) - 0.2, rot=k, coll="Nature", role="visual")


def camp(sc):
    """The pirates' camp between the beach and the cove: a stockade with a lookout tower,
    cannons on its south wall, huts, a campfire, barrels and the flag."""
    c = sc.c
    cx, cy = 122.0, 30.0
    walls = [((cx - 26, cy - 14), 0.0, 20.0), ((cx + 14, cy - 14), 0.0, 20.0), ((cx - 34, cy + 2), math.pi / 2, 24.0),
             ((cx + 26, cy + 2), math.pi / 2, 24.0), ((cx - 14, cy + 16), 0.0, 22.0), ((cx + 14, cy + 16), 0.0, 14.0)]
    for (x, y), rot, L in walls:
        ok = all(clear_of(c, x + math.cos(rot) * t, y + math.sin(rot) * t, 4.0) for t in (-L / 2, 0, L / 2))
        if ok:
            sc.put(tp.stockade(c, L), x, y, sc.ground(x, y) - 0.2, rot=rot, coll="Camp", r=0.0)
    for x, y in ((cx + 24, cy - 12), (cx - 32, cy + 14)):
        if clear_of(c, x, y, 4.0):
            sc.put(tp.watchtower(c), x, y, sc.ground(x, y) - 0.2, rot=0.3, coll="Camp", r=2.6)
            sc.flames.append((x, y, sc.ground(x, y) + 10.6))
    for k, x in enumerate((cx - 20, cx - 6, cx + 8)):
        y = cy - 17.0
        if clear_of(c, x, y, 3.0):
            sc.put(tp.cannon(c), x, y, sc.ground(x, y), rot=math.pi, coll="Camp", r=1.2)
    for k, (x, y) in enumerate(((cx - 18, cy + 6), (cx + 12, cy + 7), (cx - 4, cy + 9))):
        sc.put(tp.pirate_hut(c, k % 2), x, y, sc.ground(x, y) - 0.1, rot=math.pi + 0.2 * (k - 1), coll="Camp", r=2.6)
        lantern(sc, x + 3.0, y - 2.6, sc.ground(x + 3.0, y - 2.6) - 0.2, rot=math.pi, coll="Camp")
    x, y = cx - 2.0, cy - 4.0
    sc.put(props.campfire(c), x, y, sc.ground(x, y) - 0.1, coll="Camp", r=1.5)
    sc.flames.append((x, y, sc.ground(x, y) + 1.2))
    for k in range(6):
        a = k * 1.05
        x2, y2 = x + 4.0 * math.cos(a), y + 4.0 * math.sin(a)
        if k % 2:
            sc.put(tp.barrel(c), x2, y2, sc.ground(x2, y2) - 0.05, rot=a, coll="Camp", r=0.6)
    sc.put(tp.flag_pole(c, "wreck_flag", 10.0, "wreck_iron"), cx + 4.0, cy - 2.0, sc.ground(cx + 4.0, cy - 2.0) - 0.3, coll="Camp", r=0.3)


def skull_rock(sc):
    """Skull Rock's carved face, looking out over the dip; treasure at its feet."""
    c, m = sc.c, sc.dk
    x, y = m.SKULL_ROCK
    sc.put(tp.skull_face(c, 9.5, 17.0), x, y, -0.6, rot=math.pi, coll="Skull", role="visual")
    for k, (dx, dy) in enumerate(((-6.0, -9.5), (5.0, -10.0), (0.0, -11.5), (-9.0, -5.0), (9.0, -6.0))):
        px, py = x + dx, y + dy
        z = sc.ground(px, py)
        proto = (tp.chest(c, True), tp.gold_pile(c), tp.chest(c, False), tp.gold_pile(c), tp.barrel(c))[k]
        sc.put(proto, px, py, z - 0.15, rot=math.pi + 0.3 * (k - 2), coll="Skull", role="visual")
    for dx in (-11.0, 11.0):
        lantern(sc, x + dx, y - 4.0, sc.ground(x + dx, y - 4.0) - 0.2, rot=math.pi, coll="Skull")


def cove(sc):
    """The cove's back: cliffs north of the cove street, shanty huts and lanterns under
    them, palms; the west side's barrels, a beached rowboat, a signpost."""
    c, m = sc.c, sc.dk
    for k in range(7):
        x = -40.0 + 34.0 * k
        y = 132.0 + 10.0 * rnd(k * 3.3)
        if clear_of(c, x, y, 18.0):
            rk = c.rock_mass("Cove Cliff %d" % k, x, y, 22.0 + 6 * rnd(k), 14.0, 22.0 + 12.0 * rnd(k + 5), z0=-2.0, n=14, seed=20 + k,
                             bands=tp.STACK)
            c.paint_rock(rk, ROCK, ("wreck_grass", "wall"))  # out of reach: its top is just wall
            for j in range(2):
                sc.put(bp.coconut_palm(c, j), x - 6 + 12 * j, y, 20.0 + 10 * rnd(k + 5) - 0.5, rot=j + k, scale=0.8, coll="Cove", role="visual")
    for k in range(6):
        x = -10.0 + 26.0 * k
        y = 108.0 + 3.0 * (k % 2)
        if clear_of(c, x, y, 6.0):
            sc.put(tp.pirate_hut(c, k % 2), x, y, sc.ground(x, y) - 0.1, rot=math.pi + 0.15 * (k % 3 - 1), coll="Cove", r=2.6)
            lantern(sc, x + 3.2, y - 2.8, sc.ground(x + 3.2, y - 2.8) - 0.2, rot=math.pi, coll="Cove")
    for k, (x, y) in enumerate(((-48.0, 70.0), (-50.0, 46.0), (-46.0, 20.0), (-12.0, 108.0))):
        if clear_of(c, x, y, 4.0):
            z = sc.ground(x, y)
            sc.put(tp.barrel(c), x, y, z - 0.05, coll="Cove", r=0.6)
            sc.put(tp.crate(c), x + 1.3, y + 0.5, z - 0.05, rot=0.4, coll="Cove", r=0.8)
    x, y = -50.0, 0.0
    if clear_of(c, x, y, 4.0):
        sc.put(tp.rowboat(c), x, y, sc.ground(x, y) + 0.05, rot=0.8, coll="Cove", role="visual")
    q = c.at(m.TO_ROAD(m.SEG[16]) + 30)
    p = q.side(q.w / 2 + 3.5)
    sc.put(tp.signpost(c, "cove_sign", "wreck_post"), p.x, p.y, sc.ground(p.x, p.y), rot=math.atan2(q.t.y, q.t.x) + math.pi / 2, coll="Cove", role="visual")


def offshore(sc):
    """An old wreck far out, sea stacks and an arch of rock, far islands."""
    c = sc.c
    ms = Mesh()
    ox, oy = 140.0, -240.0

    def hull(bm):
        for k in range(8):
            a = k * math.tau / 8
            cuboid(bm, (ox + 12 * math.cos(a) * 0.9, oy + 4.5 * math.sin(a), 0.8), (5.0, 2.0, 4.0), rot=a + math.pi / 2, tilt=(0.25, 0.0))

    ms.add(HULL, hull)
    ms.build(c, "Old Wreck", "Offshore", "visual")
    sc.put(tp.mast(c, 16.0, True), ox - 3.0, oy, -1.0, rot=0.2, coll="Offshore", role="visual")
    sc.put(tp.mast(c, 12.0, False), ox + 5.0, oy + 1.0, -1.0, rot=0.3, coll="Offshore", role="visual")
    sc.put(tp.sail(c, 6.0, 4.0, 1), ox + 5.0, oy + 1.0, -1.0 + 12 * 0.62, rot=0.3, coll="Offshore", role="visual")
    for k, (x, y, rx, h) in enumerate(((40.0, -170.0, 9.0, 18.0), (260.0, -110.0, 12.0, 24.0), (290.0, 40.0, 10.0, 20.0),
                                       (-90.0, -110.0, 8.0, 14.0), (230.0, -200.0, 14.0, 28.0))):
        tp.rock_island(c, "Sea Stack %d" % k, x, y, rx, rx * 0.85, h, ROCK, GRASS, seed=50 + k)
    for k in range(10):
        a = -0.2 + k * 0.38
        r = 850 + 400 * rnd(k * 5.1)
        x, y = 80 + r * math.cos(a - math.pi / 2), r * math.sin(a - math.pi / 2)
        tp.rock_island(c, "Far Island %d" % k, x, y, 60 + 50 * rnd(k), 50 + 40 * rnd(k + 3), 40 + 60 * rnd(k + 7), ROCK, GRASS, seed=70 + k,
                       z0=-20.0, hill=True)


def nature(sc):
    c = sc.c

    def ok(x, y, z, margin):
        return z > 0.8 and clear_of(c, x, y, margin) and sc.free(x, y, 2.5)

    area = (-150, 340, -40, 230)
    props.scatter(c, bp.coconut_palm(c, 1), 34, area, lambda x, y, z: ok(x, y, z, 7.0), [sc.ter], seed=13, coll="Palms")
    props.scatter(c, bp.coconut_palm(c, 2), 20, area, lambda x, y, z: ok(x, y, z, 7.0), [sc.ter], seed=17, coll="Palms")
    props.scatter(c, tp.dune_grass(c, "wreck_grass"), 120, (-150, 340, -60, 230), lambda x, y, z: z > 0.4 and clear_of(c, x, y, 2.0),
                  [sc.ter], seed=19, coll="Nature", role="visual", scale=(0.8, 1.6))
    props.scatter(c, props.boulder(c, "wreck_rock", 1), 26, area, lambda x, y, z: ok(x, y, z, 8.0), [sc.ter], seed=23, coll="Nature",
                  scale=(0.6, 1.4))
    game_entity(c, "birds", 120.0, -100.0, 30.0, radius=50, count=5, speed=0.18, seed=4, color="#2a2420")
    game_entity(c, "birds", 88.0, 90.0, 34.0, radius=30, count=4, speed=0.22, seed=8, color="#f0e8d8")
    c.entity("sparkles", rate=10, radius=30)


def light(sc):
    c = sc.c
    groups = ("Gate", "Lanterns", "Boats", "Galleon", "Sandbar", "Camp", "Skull", "Cove", "Offshore", "Palms", "Nature")
    c.merge_props(groups, cell=220.0)
    built = [o for name in groups + ("Rocks",) for o in c.coll(name).objects if o.type == "MESH" and o.data.users == 1]
    c.preset("sun", [sc.ter] + built, 0.3)
    c.glow([sc.ter] + built, sc.flames, 10.0, (1.6, 1.1, 0.6), base=1.0)
    kit.paint.shade_roads(c.pieces, 0.3)


def build(c, m, ter):
    sc = Scene(c, m, ter)
    gate(sc)
    pier(sc)
    galleon(sc)
    mast_jump(sc)
    camp(sc)
    skull_rock(sc)
    cove(sc)
    offshore(sc)
    nature(sc)
    for x, y, z in sc.flames:
        game_entity(c, "torch", x, y, z)
    light(sc)
    print("wreck scenery: props", c.prop_count, "flames", len(sc.flames))
