# Snow Dragon Pass's kingdom (see snow_dragon_pass.py): the Dragon Citadel blazing gold
# above the start and its ceremonial gate, the Frozen Gate, the Windy Village and its
# ration line, the High Cliff Road's turn boards and the Dragon Overlook, the Supply
# Road's depots and labour camp, Starvation Road between the empty stores and the full
# ones, the Broken Bridges, the Avalanche Run, the monastery on its mount, the frozen
# aqueduct and its falls, the guardian dragons of the Final Ascent; the people, the
# prayer flags, the bells, the blizzard, the avalanches and the ice dragon's flight
# (for the game).
# SPDX-License-Identifier: MIT
#
# The story is told by the places and the people: hungry villagers queue at bare stalls
# and huddle round small fires while guards stand before storehouses stacked to the
# rafters, and high above it all the citadel's windows blaze. Nothing here is violent.

import math

import dcanyon_props as dp
import isles_props as ip
import props
import snow_land as L
import snow_props as sp
from course_kit import rnd
from snow_scenery import MainWay, clear, game_entity

M = L.MAIN

# ------------------------------------------------------------------ helpers


def side_at(way, s, off):
    """The point `off` metres right of a road (main or a branch) at distance s, the turn
    that faces a prop there back toward the road, and the road sample."""
    q = way.at(s)
    p = q.side(off)
    return p.x, p.y, ip.facing(p.x, p.y, q.p.x, q.p.y), q


def put(sc, proto, x, y, rot=0.0, scale=1.0, coll="Props", role="visual", sink=0.0, z=None):
    gz = sc.ground(x, y) if z is None else z
    return sc.put(proto, x, y, gz - sink, rot, scale, coll=coll, role=role)


def villager(c, sc, x, y, role, face_x, face_y, variant=None, z=None):
    """A villager for the game to animate (game/isles.ts' roles)."""
    gz = sc.ground(x, y) if z is None else z
    dx, dy = face_x - x, face_y - y
    n = math.hypot(dx, dy) or 1.0
    k = len(sc.crowd)
    v = variant if variant is not None else int(rnd(k * 13 + 7) * 8)
    gx, gy, gzz = c.game(x, y, gz)
    sc.crowd.append([round(gx, 2), round(gy, 2), round(gzz, 2), round(dx / n, 3), round(-dy / n, 3), role, v])


def spot_ok(c, sc, x, y, r, margin=3.0):
    return clear(c, x, y, r + margin) and sc.free(x, y, r)


def place(c, sc, proto, x, y, rot, r, coll="Town", role="both", sink=0.0, scale=1.0, margin=3.0):
    """Put a prop down if there's room (clear of every road and everything else)."""
    if not spot_ok(c, sc, x, y, r, margin):
        return False
    put(sc, proto, x, y, rot, scale, coll=coll, role=role, sink=sink)
    sc.footprints.append((x, y, r))
    return True


def along(way, s0, s1, every):
    s = s0
    while s < s1:
        yield s
        s += every


def braziers(c, sc, way, s0, s1, every, off=3.4, sides=(-1, 1)):
    for s in along(way, s0, s1, every):
        for side in sides:
            x, y, rot, q = side_at(way, s, side * (q.w / 2 + off) if False else side * (way.at(s).w / 2 + off))
            if clear(c, x, y, 1.0) and sc.free(x, y, 1.0):
                z = sc.ground(x, y)
                sc.put(dp.brazier(c), x, y, z - 0.2, 0.0, 1.0, role="both")
                sc.light("fire", x, y, z + 2.4)
                sc.footprints.append((x, y, 1.0))


def banners(c, sc, way, s0, s1, every, off=4.0, mat="banner_royal"):
    for s in along(way, s0, s1, every):
        for side in (-1, 1):
            x, y, rot, q = side_at(way, s, side * (way.at(s).w / 2 + off))
            if clear(c, x, y, 1.0) and sc.free(x, y, 1.2):
                put(sc, ip.banner_pole(c, mat), x, y, rot + math.pi / 2, role="both")
                sc.footprints.append((x, y, 1.2))


def outside_of(way, s):
    """+1 if the outside of the road's turn at s is to its right, -1 if to its left."""
    a, b = way.at(s - 6).t, way.at(s + 6).t
    return 1 if a.x * b.y - a.y * b.x > 0 else -1


def chevrons(c, sc, way, s0, s1, every=10.0):
    """Turn boards round the outside of a bend, arrows pointing the way it turns."""
    for s in along(way, s0, s1, every):
        side = outside_of(way, s)
        x, y, rot, q = side_at(way, s, side * (q.w / 2 + 3.2) if False else side * (way.at(s).w / 2 + 3.2))
        if clear(c, x, y, 0.8) and sc.free(x, y, 2.0):
            # The board's arrows point along its +X: turned to face the road, +X points
            # along the road one way or the other; flip it to point the way it turns.
            r = rot + (math.pi if side > 0 else 0.0)
            put(sc, dp.chevron_board(c, 6.0), x, y, r, role="both")
            sc.footprints.append((x, y, 2.0))


def campfire(c, sc, x, y, n=4, role="huddle"):
    """A small fire with a few people huddled round it."""
    if not spot_ok(c, sc, x, y, 3.2, 2.0):
        return
    z = sc.ground(x, y)
    put(sc, props.campfire(c), x, y, 0.0, role="visual")
    sc.footprints.append((x, y, 3.2))
    sc.light("fire", x, y, z + 1.0)
    sc.fires.append((x, y, z))
    for i in range(n):
        a = i * math.tau / n + rnd(x + i) * 0.6
        villager(c, sc, x + 2.2 * math.cos(a), y + 2.2 * math.sin(a), role, x, y)


def queue(c, sc, x0, y0, x1, y1, n, face=None):
    """A line of people from (x0, y0) toward (x1, y1), each facing along it."""
    fx, fy = face or (x1, y1)
    for i in range(n):
        t = i / max(1, n - 1)
        x = x0 + (x1 - x0) * t + 0.4 * (rnd(i * 3.3 + x0) - 0.5)
        y = y0 + (y1 - y0) * t + 0.4 * (rnd(i * 5.1 + y0) - 0.5)
        if clear(c, x, y, 1.0):
            villager(c, sc, x, y, "queue", x0 - (x1 - x0), y0 - (y1 - y0))


def flag_line(sc, a, b, sag=1.6):
    """A line of prayer flags from a to b ((x, y, z), Blender) for the game to flap."""
    sc.flags.append((a, b, sag))


# ------------------------------------------------------------------ 1  the Dragon Citadel and its gate; the Frozen Gate


def gate(c, sc):
    main = MainWay(c)
    # The citadel's ceremonial gate over the finish (just before the line), guardian
    # dragons either side, guards under it.
    for s, span, h, mat in ((M.length - 26.0, 30.0, 15.0, "roof_gold"), (86.0, 24.0, 12.0, "sdp_roof")):
        q = main.at(s)
        rot = math.atan2(q.t.y, q.t.x) - math.pi / 2
        put(sc, ip.gate(c, span, h, mat, grand=s > 100), q.p.x, q.p.y, rot, coll="Landmarks", role="both", z=q.p.z)
        for side in (-1, 1):
            x, y, r, _ = side_at(main, s, side * (q.w / 2 + 2.4))
            villager(c, sc, x, y, "guard", q.p.x, q.p.y, z=q.p.z)
    for s in (-60.0, -14.0, 40.0):
        for side in (-1, 1):
            x, y, rot, q = side_at(main, s, side * (main.at(s).w / 2 + 6.5))
            if clear(c, x, y, 3.0):
                sc.put(ip.dragon_statue(c, "citadel_stone"), x, y, sc.ground(x, y), rot, 1.6, coll="Landmarks", role="both")
                sc.footprints.append((x, y, 5.0))
    braziers(c, sc, main, -160.0, 70.0, 16.0)
    banners(c, sc, main, -150.0, 70.0, 12.0, off=5.5)
    # Fortress walls along both sides of the start straight, guards on top.
    for s in along(main, -110.0, 80.0, 19.0):
        for side in (-1, 1):
            x, y, rot, q = side_at(main, s, side * (main.at(s).w / 2 + 13.0))
            if spot_ok(c, sc, x, y, 6.0, 1.0):
                put(sc, dp.fort_wall(c, 18.0, 8.0), x, y, rot, coll="Landmarks", role="both", sink=1.0)
                sc.footprints.append((x, y, 8.0))
                if int(s) % 2 == 0:
                    villager(c, sc, x, y, "guard", q.p.x, q.p.y, z=sc.ground(x, y) + 7.0)


def citadel(c, sc):
    """The Dragon Citadel on its crag over the start: the great hall, towers round it,
    pagodas, walls, every window blazing. Built big: it's seen from all over the pass."""
    cx, cy = L.CITADEL
    S = 1.6
    z0 = sc.ground(cx, cy)
    face = ip.facing(cx, cy, cx, cy - 100)  # facing south, down over the course
    put(sc, sp.citadel_hall(c, 34.0, 20.0, 13.0), cx, cy, face, S, coll="Landmarks", role="visual", z=z0)
    sc.light("lamp", cx, cy - 20, z0 + 12)
    for i, (dx, dy, h) in enumerate(((-30, -16, 30), (30, -16, 34), (-34, 20, 24), (34, 22, 26), (0, 34, 40), (-52, -30, 22), (52, -28, 24))):
        x, y = cx + dx * S, cy + dy * S
        put(sc, sp.citadel_tower(c, h, 11.0), x, y, face, S, coll="Landmarks", role="visual", z=sc.ground(x, y))
        sc.light("lamp", x, y - 10, sc.ground(x, y) + h * S * 0.6)
    for dx, dy in ((-58, 0), (58, 4), (0, -40), (-20, 52), (24, 54)):
        x, y = cx + dx * S, cy + dy * S
        put(sc, ip.pagoda(c, 7, 9.0, "roof_gold"), x, y, face, S, coll="Landmarks", role="visual", z=sc.ground(x, y))
    for k in range(16):
        a = k * math.tau / 16
        x, y = cx + 70 * S * math.cos(a), cy + 52 * S * math.sin(a)
        put(sc, dp.fort_wall(c, 30.0, 12.0), x, y, a + math.pi / 2, S, coll="Landmarks", role="visual", sink=2.0)
        if k % 3 == 0:
            villager(c, sc, x, y, "guard", cx, cy - 300, z=sc.ground(x, y) + 12.0 * S)
    # Braziers along the walls' top: gold light against the snow.
    for k in range(12):
        a = k * math.tau / 12 + 0.3
        x, y = cx + 72 * S * math.cos(a), cy + 54 * S * math.sin(a)
        sc.light("fire", x, y, sc.ground(x, y) + 14 * S)


# ------------------------------------------------------------------ 2  the Windy Village


def village(c, sc):
    main = MainWay(c)
    s0, s1 = M.S["g1"] - 20.0, L.SPLIT1[0] - 20.0
    # Houses along both sides, some half buried in drifts.
    k = 0
    for s in along(main, s0, s1, 15.0):
        for side in (-1, 1):
            k += 1
            off = main.at(s).w / 2 + 10.0 + 4.0 * rnd(k * 1.7)
            x, y, rot, q = side_at(main, s, side * off)
            buried = rnd(k * 2.9) < 0.3
            if place(c, sc, sp.snow_house(c, k % 8), x, y, rot, 6.0, sink=1.6 if buried else 0.0):
                z = sc.ground(x, y)
                sc.light("lamp", x + math.cos(rot + math.pi / 2) * 3.5, y + math.sin(rot + math.pi / 2) * 3.5, z + 2.2)
                if buried:
                    put(sc, sp.snow_mound(c, k % 3), x + 3 * math.cos(rot), y + 3 * math.sin(rot), rot, role="visual")
    # The ration line: a stall with a guard, villagers queuing along the road.
    s = M.S["g2"] + 30.0
    x, y, rot, q = side_at(main, s, main.at(s).w / 2 + 7.0)
    if place(c, sc, sp.ration_stall(c, 0), x, y, rot, 3.5):
        villager(c, sc, x + 2.8 * math.cos(rot), y + 2.8 * math.sin(rot), "guard", q.p.x, q.p.y)
        villager(c, sc, x - 2.8 * math.cos(rot), y - 2.8 * math.sin(rot), "merchant", q.p.x, q.p.y)
        qa = side_at(main, s - 6.0, main.at(s).w / 2 + 5.0)
        qb = side_at(main, s - 50.0, main.at(s).w / 2 + 5.0)
        queue(c, sc, qa[0], qa[1], qb[0], qb[1], 16)
    # Families round small fires; empty stalls; a sled or two.
    for s, off in ((M.S["g1"] + 40, 18.0), (M.S["g2"] - 30, -19.0), (M.S["g2"] + 80, -17.0), (M.S["fork1"] - 40, 20.0)):
        x, y, rot, q = side_at(main, s, off)
        campfire(c, sc, x, y, 4)
    for i, s in enumerate((M.S["g1"] + 70, M.S["g2"] + 60)):
        x, y, rot, q = side_at(main, s, -(main.at(s).w / 2 + 7.0))
        place(c, sc, sp.ration_stall(c, i + 1), x, y, rot, 3.5)
    for i, s in enumerate((M.S["g1"] + 20, M.S["g2"] + 10, M.S["fork1"] - 70)):
        x, y, rot, q = side_at(main, s, (main.at(s).w / 2 + 6.0) * (1 if i % 2 else -1))
        if place(c, sc, sp.sled(c, i), x, y, rot + math.pi / 2, 2.0):
            villager(c, sc, x + 3.6 * math.cos(rot), y + 3.6 * math.sin(rot), "hauler", x, y)
    # Lanterns along the street, flags across it.
    for s in along(main, s0, s1, 22.0):
        for side in (-1, 1):
            x, y, rot, q = side_at(main, s, side * (main.at(s).w / 2 + 3.0))
            if spot_ok(c, sc, x, y, 0.8, 0.5):
                put(sc, ip.lantern_post(c), x, y, rot + math.pi, role="both")
                sc.footprints.append((x, y, 0.8))
                sc.light("lamp", x, y, sc.ground(x, y) + 4.0)
    for s in along(main, s0 + 20, s1, 45.0):
        q = main.at(s)
        a, b = q.side(-(q.w / 2 + 5)), q.side(q.w / 2 + 5)
        flag_line(sc, (a.x, a.y, sc.ground(a.x, a.y) + 7.5), (b.x, b.y, sc.ground(b.x, b.y) + 7.5))


# ------------------------------------------------------------------ the fork signs


def fork_signs(c, sc):
    """At each split, a signpost in the gore between the two roads, an arrow each way:
    either road is the race."""
    main = MainWay(c)
    for (a, b), branch in ((L.SPLIT1, "supply"), (L.SPLIT2, "aqueduct")):
        lane = sc.lanes[branch]
        ls0 = lane.s0
        for d in range(30, 120, 4):
            p = main.at(a + d).p
            q = lane.at(ls0 + d).p
            gap = math.hypot(p.x - q.x, p.y - q.y)
            if gap > main.at(a + d).w / 2 + lane.at(ls0 + d).w / 2 + 6.0:
                x, y = (p.x + q.x) / 2, (p.y + q.y) / 2
                back = main.at(a).p
                rot = ip.facing(x, y, back.x, back.y)
                put(sc, sp.fork_sign(c), x, y, rot, role="both")
                sc.footprints.append((x, y, 2.5))
                for k in range(2):
                    put(sc, dp.brazier(c), x + (k * 2 - 1) * 2.0, y, 0.0, role="both")
                    sc.light("fire", x + (k * 2 - 1) * 2.0, y, sc.ground(x, y) + 2.4)
                break


# ------------------------------------------------------------------ 3  the High Cliff Road


def cliff(c, sc):
    main = MainWay(c)
    a, b = L.SPLIT1
    for n0, n1 in (("a1", "a2"), ("a2", "a4"), ("a4", "a5"), ("a5", "a7"), ("a7", "m1")):
        s0 = M.S[n0] - 6.0
        s1 = M.at(n0, 0.45)
        chevrons(c, sc, main, max(a + 10, s0), min(b - 10, s1), 9.0)
    braziers(c, sc, main, a + 60.0, b - 60.0, 26.0)
    # Stone dragons along the ledge, on the mountain side.
    for i, s in enumerate(along(main, a + 90.0, b - 60.0, 70.0)):
        side = -outside_of(main, s)
        x, y, rot, q = side_at(main, s, side * (q.w / 2 + 5.5) if False else side * (main.at(s).w / 2 + 5.5))
        if spot_ok(c, sc, x, y, 2.8, 1.0):
            sc.put(ip.dragon_statue(c, "frost_rock"), x, y, sc.ground(x, y), rot, 1.3, coll="Landmarks", role="both")
            sc.footprints.append((x, y, 3.5))
    # The Dragon Overlook: a colossal stone dragon on the ridge's prow, looking out over
    # the valley and the Supply Road far below; a pavilion and prayer flags round it.
    ox, oy = L.OVERLOOK
    z = sc.ground(ox, oy)
    sc.put(ip.dragon_statue(c, "frost_rock"), ox, oy, z - 0.5, ip.facing(ox, oy, ox + 100, oy), 3.4, coll="Landmarks", role="both")
    sc.footprints.append((ox, oy, 10.0))
    for k in range(6):
        ang = k * math.tau / 6
        x, y = ox + 14 * math.cos(ang), oy + 14 * math.sin(ang)
        if spot_ok(c, sc, x, y, 1.0, 1.0):
            put(sc, sp.flag_pole(c, k % 3), x, y, ang, role="visual")
            flag_line(sc, (ox, oy, z + 20.0), (x, y, sc.ground(x, y) + 6.0), sag=2.0)
    for s in along(main, a + 40, b - 40, 60.0):
        q = main.at(s)
        side = outside_of(main, s)
        x, y, rot, _ = side_at(main, s, side * (q.w / 2 + 4.0))
        if clear(c, x, y, 0.6):
            x2, y2, _, _ = side_at(main, s + 24, side * (main.at(s + 24).w / 2 + 4.0))
            flag_line(sc, (x, y, sc.ground(x, y) + 5.0), (x2, y2, sc.ground(x2, y2) + 5.0), sag=1.2)


# ------------------------------------------------------------------ 3b  the Frozen Supply Road


def supply(c, sc):
    lane = sc.lanes["supply"]
    s0, s1 = lane.s0 + 70.0, lane.s1 - 60.0
    tun = sc.tunnels.get("supply", (0, 0, 0))
    lap = L.LAPS[L.LANES["supply"][0]]
    # The depots: storehouses stacked full, guards before their doors.
    for i, s in enumerate((lap.at("b2", 0.2), lap.at("b2", 0.7))):
        side = outside_of(lane, s)
        x, y, rot, q = side_at(lane, s, side * (lane.at(s).w / 2 + 14.0))
        if place(c, sc, sp.storehouse(c, True), x, y, rot, 9.0):
            for k in (-1, 1):
                gx, gy = x + k * 2.6 * math.cos(rot) - 5.6 * math.sin(rot), y + k * 2.6 * math.sin(rot) + 5.6 * math.cos(rot)
                villager(c, sc, gx, gy, "guard", q.p.x, q.p.y)
            put(sc, ip.banner_pole(c, "banner_royal"), x + 8.0 * math.cos(rot), y + 8.0 * math.sin(rot), rot, role="visual")
    # The labour camp: sledges hauled to and fro, workers at the ice and the sacks,
    # tattered shelters, people huddled under them.
    k = 0
    for s in along(lane, s0, s1, 22.0):
        if tun[0] - 30 < s < tun[1] + 30:
            continue
        k += 1
        side = -outside_of(lane, s) if k % 2 else outside_of(lane, s)
        x, y, rot, q = side_at(lane, s, side * (lane.at(s).w / 2 + 8.0 + 3.0 * rnd(k)))
        kind = k % 4
        if kind == 0 and place(c, sc, sp.sled(c, k), x, y, rot + math.pi / 2, 2.0):
            villager(c, sc, x + 3.6 * math.cos(rot), y + 3.6 * math.sin(rot), "hauler", x, y)
        elif kind == 1 and place(c, sc, sp.ration_stall(c, k), x, y, rot, 3.5):
            for j in range(3):
                villager(c, sc, x - 1.5 + j * 1.5, y - 0.5, "huddle", q.p.x, q.p.y)
        elif kind == 2 and place(c, sc, sp.sack_pile(c, k), x, y, rot, 2.0):
            villager(c, sc, x + 2.2 * math.cos(rot), y + 2.2 * math.sin(rot), "worker", x, y)
            villager(c, sc, x - 2.2 * math.cos(rot), y - 2.2 * math.sin(rot), "worker", x, y)
        elif kind == 3:
            campfire(c, sc, x, y, 3)
    # The blue ice cavern: cold lights down its length, ice at its mouths.
    if tun[1] > tun[0]:
        for s in along(lane, tun[0] + 4, tun[1] - 4, 14.0):
            q = lane.at(s)
            sc.light("ice", q.p.x, q.p.y, q.p.z + 7.0)
        for s in (tun[0] - 14.0, tun[1] + 14.0):
            for side in (-1, 1):
                x, y, rot, q = side_at(lane, s, side * (lane.at(s).w / 2 + 4.5))
                place(c, sc, sp.ice_spike(c, int(s) % 3), x, y, rot, 2.0, role="both", margin=1.0)


# ------------------------------------------------------------------ 4  Starvation Road, 5 the Broken Bridges, 6 the Avalanche Run


def starvation(c, sc):
    main = MainWay(c)
    s0 = L.SPLIT1[1] + 20.0
    # The bare store: an empty storehouse, a long line of people waiting at its door.
    s = s0 + 20.0
    x, y, rot, q = side_at(main, s, -(main.at(s).w / 2 + 16.0))
    if place(c, sc, sp.storehouse(c, False), x, y, rot, 9.0):
        villager(c, sc, x + 1.2 * math.cos(rot) - 6.0 * math.sin(rot), y + 1.2 * math.sin(rot) + 6.0 * math.cos(rot), "guard", q.p.x, q.p.y)
        qa = side_at(main, s + 6.0, -(main.at(s).w / 2 + 6.0))
        qb = side_at(main, s + 60.0, -(main.at(s).w / 2 + 6.0))
        queue(c, sc, qa[0], qa[1], qb[0], qb[1], 22)
    # Across the road: the royal storehouses, full, under guard, banners flying.
    for i, s in enumerate((s0 + 10.0, s0 + 40.0)):
        x, y, rot, q = side_at(main, s, main.at(s).w / 2 + 17.0)
        if place(c, sc, sp.storehouse(c, True), x, y, rot, 9.0):
            for k in (-1, 1):
                villager(c, sc, x + k * 2.6 * math.cos(rot) - 5.6 * math.sin(rot), y + k * 2.6 * math.sin(rot) + 5.6 * math.cos(rot), "guard",
                         q.p.x, q.p.y)
            put(sc, ip.banner_pole(c, "banner_royal"), x + 9.0 * math.cos(rot), y + 9.0 * math.sin(rot), rot, role="visual")
    # Families round small fires, empty market stalls in the drifts, half-buried houses.
    for i, s in enumerate(along(main, s0 + 70.0, s0 + 150.0, 26.0)):
        side = -1 if i % 2 else 1
        x, y, rot, q = side_at(main, s, side * (main.at(s).w / 2 + 12.0))
        campfire(c, sc, x, y, 3 + i % 2)
        x, y, rot, q = side_at(main, s + 12, -side * (main.at(s).w / 2 + 7.0))
        if place(c, sc, sp.ration_stall(c, i + 3), x, y, rot, 3.5):
            put(sc, sp.snow_mound(c, i), x + 2.5, y, rot, role="visual")
    for i, s in enumerate((s0 + 90.0, s0 + 130.0)):
        x, y, rot, q = side_at(main, s, (main.at(s).w / 2 + 22.0) * (1 if i % 2 else -1))
        place(c, sc, sp.snow_house(c, 3 + i), x, y, rot, 6.0, sink=2.2)


def broken_bridges(c, sc):
    """Ruined bridges either side of the road's own across the gorge: piers, the stubs of
    their decks, icicles hanging off the broken ends."""
    for (gx, gy), (hx, hy), v in ((L.GORGE[0], L.GORGE[1], 0), (L.GORGE[2], L.GORGE[3], 1)):
        t = 0.55 if v == 0 else 0.35
        x, y = gx + (hx - gx) * t, gy + (hy - gy) * t
        ang = math.atan2(hy - gy, hx - gx) + math.pi / 2  # across the gorge
        top = min(sc.info(x + 30 * math.cos(ang), y + 30 * math.sin(ang)), sc.info(x - 30 * math.cos(ang), y - 30 * math.sin(ang)))
        h = top - L.FLOOR
        if h > 12:
            sc.put(sp.broken_arch(c, 2 * L.GORGE_HW + 10.0, h + 2.0, v), x, y, top, ang, 1.0, coll="Landmarks", role="both")
    # Icicles under the road's bridge.
    for s in along(MainWay(c), 1080.0, 1170.0, 12.0):
        q = c.at(s)
        if sc.info(q.p.x, q.p.y) < q.p.z - 8:
            for side in (-1, 1):
                p = q.side(side * (q.w / 2 + 0.6))
                sc.put(sp.icicles(c, 6.0, int(s) % 3), p.x, p.y, q.p.z - 4.0, math.atan2(q.t.y, q.t.x), 1.0, role="visual")


def avalanche_run(c, sc):
    """Avalanches down the far slopes south of the pass (seen, never on the road): each a
    path down a slope the game sends powder down now and then."""
    main = MainWay(c)
    s0, s1 = M.S["m2"] - 20.0, L.SPLIT2[0]
    for i, s in enumerate(along(main, s0, s1, 70.0)):
        q = main.at(s)
        side = -1 if outside_of(main, s) < 0 else 1
        # Up the slope on the valley's far side.
        p0 = q.side(-side * 160.0)
        p1 = q.side(-side * 90.0)
        z0 = sc.info(p0.x, p0.y)
        z1 = sc.info(p1.x, p1.y)
        if z0 - z1 > 25:
            sc.avalanches.append(((p0.x, p0.y, z0 + 2.0), (p1.x, p1.y, z1 + 1.0), 23.0 + 7.0 * i, 9.0 * i))
    # Turn boards round the run's bends; braziers few and far between.
    for n0 in ("m2", "fork2"):
        chevrons(c, sc, main, M.S[n0] - 4.0, M.at(n0, 0.5), 10.0)
    braziers(c, sc, main, s0, s1, 40.0)


# ------------------------------------------------------------------ 7  the Monastery Ridge


def monastery(c, sc):
    main = MainWay(c)
    mx, my = L.MONASTERY
    z = sc.ground(mx, my)
    face = ip.facing(mx, my, L.CITADEL[0], L.CITADEL[1])
    put(sc, sp.monastery_hall(c, 18.0, 12.0, 9.0, 0), mx, my, face, coll="Landmarks", role="both", z=z - 1.0)
    for i, (dx, dy) in enumerate(((-22, -8), (20, -10), (0, 22))):
        x, y = mx + dx, my + dy
        put(sc, sp.monastery_hall(c, 11.0, 8.0, 6.0, 1), x, y, face, coll="Landmarks", role="both", z=sc.ground(x, y) - 1.0)
        sc.light("lamp", x, y + 4, sc.ground(x, y) + 3)
    for i, (dx, dy) in enumerate(((-12, 16), (14, 14), (-30, 10), (30, 6))):
        x, y = mx + dx, my + dy
        put(sc, sp.chorten(c, 1.0 if i < 2 else 0.8), x, y, 0.0, coll="Landmarks", role="both")
    for i, (dx, dy) in enumerate(((-6, -18), (8, -18))):
        x, y = mx + dx, my + dy
        put(sc, sp.bell_frame(c), x, y, face, coll="Landmarks", role="both")
        sc.bells.append((x, y, sc.ground(x, y) + 2.8))
    # Monks on the terraces, all looking the same way: across to the citadel.
    for i in range(10):
        a = i * 0.6 - 1.5
        x, y = mx + 26 * math.cos(a), my + 20 * math.sin(a)
        if clear(c, x, y, 2.0):
            villager(c, sc, x, y, "monk", L.CITADEL[0], L.CITADEL[1])
    # Prayer flags from the hall's roof down to poles round the mount.
    for k in range(9):
        a = k * math.tau / 9
        x, y = mx + 34 * math.cos(a), my + 26 * math.sin(a)
        if clear(c, x, y, 1.0):
            put(sc, sp.flag_pole(c, k % 3), x, y, a, role="visual")
            flag_line(sc, (mx, my, z + 13.0), (x, y, sc.ground(x, y) + 6.5), sag=2.4)
    # Ceremonial gates over the ridge road, braziers and turn boards on its bends.
    for s in (M.at("r3", 0.5), M.at("r5", 0.3)):
        q = main.at(s)
        rot = math.atan2(q.t.y, q.t.x) - math.pi / 2
        put(sc, ip.gate(c, q.w + 6.0, 9.0, "sdp_roof", grand=False), q.p.x, q.p.y, rot, coll="Landmarks", role="both", z=q.p.z)
    for n0 in ("r1", "r2", "r3", "r4", "r5", "r6"):
        chevrons(c, sc, main, M.S[n0] - 4.0, M.at(n0, 0.4), 9.0)
    braziers(c, sc, main, L.SPLIT2[0] + 60, L.SPLIT2[1] - 60, 30.0)


# ------------------------------------------------------------------ 7b  the Frozen Aqueduct


def aqueduct(c, sc):
    lane = sc.lanes["aqueduct"]
    lap = L.LAPS[L.LANES["aqueduct"][0]]
    tun = sc.tunnels.get("aqueduct", (0, 0, 0))
    # The old channel beside the road, frozen solid (a ribbon of turquoise ice in a stone
    # trough) wherever there's room on the outside.
    run = []
    for s in along(lane, lane.s0 + 80.0, lane.s1 - 70.0, 4.0):
        if tun[0] - 10 < s < tun[1] + 10:
            if len(run) > 4:
                sc.channels.append(run)
            run = []
            continue
        side = outside_of(lane, lap.at("q2", 0.5))
        q = lane.at(s)
        p = q.side(side * (q.w / 2 + 3.4))
        run.append((p.x, p.y, 3.0, q.p.z + 0.15))
    if len(run) > 4:
        sc.channels.append(run)
    # The aqueduct's own arches across the valley to the west, frozen falls down the
    # cliffs on the mountain side.
    for i, (s, off, span, h) in enumerate(((lap.at("q1", 0.9), -60.0, 70.0, 28.0), (lap.at("q2", 0.6), 55.0, 60.0, 24.0))):
        x, y, rot, q = side_at(lane, s, off)
        if spot_ok(c, sc, x, y, span / 2, 2.0):
            put(sc, dp.aqueduct(c, span, h), x, y, rot + math.pi / 2, coll="Landmarks", role="visual", z=q.p.z + h * 0.6)
    for i, s in enumerate((lap.at("q1", 0.6), lap.at("q2", 0.3), lap.at("q3", 0.0))):
        side = -outside_of(lane, s)
        q = lane.at(s)
        p = q.side(side * (q.w / 2 + 10.0))
        top = sc.info(p.x, p.y) + 18.0
        ang = math.atan2(q.p.y - p.y, q.p.x - p.x) + math.pi / 2
        props.falls(c, "Frozen Falls %d" % i, p.x, p.y, top, q.p.z - 0.5, 6.0, 9.0, facing=-1, throw=2.0, bulge=0.6, veils=1, angle=ang,
                    mats=("frost_falls", "icefall_blue", "glacier_ice"))
    if tun[1] > tun[0]:
        for s in along(lane, tun[0] + 4, tun[1] - 4, 16.0):
            q = lane.at(s)
            sc.light("lamp", q.p.x, q.p.y, q.p.z + 6.5)
    # Icicles hanging from the monastery's bridge as it crosses over.
    for s in along(MainWay(c), L.SPLIT2[0], L.SPLIT2[1], 4.0):
        q = c.at(s)
        sm_, d = None, 1e9
        for p in lane.pts[::2]:
            dd = math.hypot(p[0] - q.p.x, p[1] - q.p.y)
            if dd < d:
                d, sm_ = dd, p
        if d < 6.0 and sm_[2] < q.p.z - 8:
            for side in (-1, 1):
                p = q.side(side * (q.w / 2 + 0.6))
                sc.put(sp.icicles(c, 8.0, int(s) % 3), p.x, p.y, q.p.z - 4.0, math.atan2(q.t.y, q.t.x), 1.0, role="visual")


# ------------------------------------------------------------------ 8  the Final Ascent


def ascent(c, sc):
    main = MainWay(c)
    s0, s1 = L.SPLIT2[1] + 20.0, M.length - 40.0
    for s in along(main, s0, s1, 46.0):
        for side in (-1, 1):
            x, y, rot, q = side_at(main, s, side * (main.at(s).w / 2 + 7.0))
            if spot_ok(c, sc, x, y, 3.0, 1.0):
                sc.put(ip.dragon_statue(c, "citadel_stone"), x, y, sc.ground(x, y), rot, 1.5, coll="Landmarks", role="both")
                sc.footprints.append((x, y, 4.0))
    braziers(c, sc, main, s0, s1, 18.0)
    banners(c, sc, main, s0 + 8, s1, 14.0, off=5.0)
    # Walls up the climb with guards along them.
    for s in along(main, s0 + 30, s1, 22.0):
        side = outside_of(main, s)
        x, y, rot, q = side_at(main, s, side * (main.at(s).w / 2 + 12.0))
        if spot_ok(c, sc, x, y, 6.0, 1.0):
            put(sc, dp.fort_wall(c, 20.0, 7.0), x, y, rot, coll="Landmarks", role="both", sink=1.0)
            sc.footprints.append((x, y, 8.0))
            villager(c, sc, x, y, "guard", q.p.x, q.p.y, z=sc.ground(x, y) + 6.0)
    for n0 in ("f1", "f2", "f3"):
        chevrons(c, sc, main, M.S[n0] - 4.0, M.at(n0, 0.4), 10.0)


# ------------------------------------------------------------------ the mountains


def scenery(c, sc):
    """Snowy pines down the lower slopes, rocks and ice here and there."""
    X0, X1, Y0, Y1 = L.GRID
    k = 0
    for i in range(1400):
        x = X0 + 40 + (X1 - X0 - 80) * rnd(i * 1.37)
        y = Y0 + 40 + (Y1 - Y0 - 80) * rnd(i * 2.11 + 5)
        z = sc.info(x, y)
        if z > 170 or L.gorge_d(x, y) < L.GORGE_HW + 25:
            continue
        if not clear(c, x, y, 8.0) or not sc.free(x, y, 3.0):
            continue
        k += 1
        if rnd(i * 4.4) < 0.85:
            put(sc, sp.snow_pine(c, k % 8), x, y, rnd(i) * 6.3, 0.8 + 0.6 * rnd(i * 7.7), coll="Plants", role="visual", sink=0.3)
        else:
            put(sc, sp.ice_spike(c, k % 3), x, y, rnd(i) * 6.3, 1.0, coll="Plants", role="visual")
        sc.footprints.append((x, y, 2.5))
        if k > 520:
            break


# ------------------------------------------------------------------ the ice dragon


def dragon(c, sc):
    """The ice dragon's flight, keyed to where the leader is round the main lap: high over
    the peaks most of the way, then the Dragon's Shadow: out of the clouds and low over
    the Final Ascent, its shadow sweeping the snow, and away up to the citadel."""
    main = MainWay(c)

    def over(s, up, side=0.0):
        q = main.at(s % M.length)
        p = q.side(side)
        return (p.x, p.y, q.p.z + up)

    a2, b2 = L.SPLIT2
    cx, cy = L.CITADEL
    sh = b2 + 140.0  # the Dragon's Shadow
    keys = [
        (0.0, cx + 40, cy + 40, 300.0),
        (M.S["g2"], 260.0, 120.0, 280.0),
        (L.SPLIT1[0] + 120, 520.0, -260.0, 270.0),  # over the peaks east of the cliff road
        (L.SPLIT1[1], 380.0, -760.0, 260.0),
        (M.S["m2"], -40.0, -820.0, 270.0),  # down the valley beyond the Avalanche Run
        (a2 + 120.0, -460.0, -560.0, 270.0),
        (b2, -460.0, -200.0, 250.0),
        (sh - 70.0, *over(sh - 70.0, 120.0, -260.0)),  # sinking out of the cloud
        (sh - 30.0, *over(sh - 30.0, 46.0, -90.0)),
        (sh, *over(sh, 28.0, 0.0)),  # straight over the road: the shadow passes over you
        (sh + 30.0, *over(sh + 30.0, 40.0, 90.0)),
        (sh + 80.0, *over(sh + 80.0, 110.0, 200.0)),
        (M.length - 30.0, cx - 60, cy - 20, 260.0),  # up round the citadel
    ]
    out = []
    for s, x, y, z in keys:
        gx, gy, gz = c.game(x, y, z)
        out.append([round(s, 1), round(gx, 1), round(gy, 1), round(gz, 1)])
    c.entity("isles_dragon", keys=out, length=round(M.length, 1), size=1.15, colors={"body": "#9cc8e8", "belly": "#eef6ff"})


# ------------------------------------------------------------------ the air, the snow, the sound

ZONES = {  # the air and sound of each part (game/depths.ts' atmosphere)
    "gate": {"fog": "#c8d4e4", "near": 160, "far": 950, "sun": 1.9, "sky": "#d0dcf0", "ground": "#6a6a7a", "hemi": 1.3, "sound": "blizzard"},
    "village": {"fog": "#ccd8e6", "near": 190, "far": 1050, "sun": 1.8, "sky": "#d0dcf0", "ground": "#6e6a6a", "hemi": 1.3, "sound": "wind"},
    "cliff": {"fog": "#c4d0e2", "near": 140, "far": 880, "sun": 1.9, "sky": "#ccd8f0", "ground": "#5e6678", "hemi": 1.25, "sound": "blizzard"},
    "supply": {"fog": "#c8d4e4", "near": 170, "far": 1000, "sun": 1.7, "sky": "#ccd8ec", "ground": "#66666e", "hemi": 1.25, "sound": "wind"},
    "cavern": {"fog": "#2a5a8a", "near": 30, "far": 300, "sun": 0.4, "sky": "#8ad0ff", "ground": "#1a3a5a", "hemi": 1.1, "sound": "drip"},
    "starvation": {"fog": "#c6d2e2", "near": 170, "far": 1000, "sun": 1.7, "sky": "#ccd8ec", "ground": "#6a6668", "hemi": 1.25, "sound": "wind"},
    "gorge": {"fog": "#c2cee0", "near": 140, "far": 900, "sun": 1.8, "sky": "#c8d6ee", "ground": "#5a6478", "hemi": 1.25, "sound": "blizzard"},
    "avalanche": {"fog": "#bccadc", "near": 120, "far": 820, "sun": 1.8, "sky": "#c8d6ee", "ground": "#5a6478", "hemi": 1.25, "sound": "blizzard"},
    "monastery": {"fog": "#c8d4e4", "near": 160, "far": 950, "sun": 1.9, "sky": "#d0dcf0", "ground": "#6a6470", "hemi": 1.3, "sound": "bells"},
    "aqueduct": {"fog": "#c6d4e2", "near": 170, "far": 1000, "sun": 1.7, "sky": "#cad8ec", "ground": "#5e6a74", "hemi": 1.25, "sound": "wind"},
    "tunnel": {"fog": "#30343e", "near": 30, "far": 280, "sun": 0.4, "sky": "#a0a8c0", "ground": "#2a2a30", "hemi": 0.9, "sound": "drip"},
    "ascent": {"fog": "#bac8dc", "near": 120, "far": 800, "sun": 1.9, "sky": "#ccd8f0", "ground": "#6a6070", "hemi": 1.3, "sound": "blizzard"},
}
MAIN_ZONE = {"gate": "gate", "village": "village", "cliff": "cliff", "starvation": "starvation", "avalanche": "avalanche", "ridge": "monastery",
             "ascent": "ascent"}
# How hard it snows (0..1): the exposed heights fiercest, the village sheltered, none in
# the tunnels.
SNOW = {"gate": 0.8, "village": 0.45, "cliff": 1.0, "supply": 0.55, "cavern": 0.0, "starvation": 0.55, "gorge": 0.9, "avalanche": 1.0,
        "monastery": 0.8, "aqueduct": 0.6, "tunnel": 0.0, "ascent": 1.0}


def main_zone(c, s):
    s %= M.length
    q = c.at(s)
    if L.gorge_d(q.p.x, q.p.y) < 60:
        return "gorge"
    return MAIN_ZONE[L.zone_of(s)]


def lane_zone(sc, branch, s):
    a, b, _ = sc.tunnels.get(branch, (0, 0, 0))
    if a - 6 < s < b + 6:
        return "cavern" if branch == "supply" else "tunnel"
    return "supply" if branch == "supply" else "aqueduct"


def air(c, sc):
    """Keys every 12 m along every road: the air's zone either side and how far between
    them; and the blizzard's strength."""
    blend = 24.0
    keys = []
    snow = []

    def add(zone_fn, at_fn, s0, s1, closed):
        def change(s, direction):
            here = zone_fn(s)
            d = 0.0
            while d < blend:
                d += 2.0
                ss = s + direction * d
                if not closed and not (s0 <= ss <= s1):
                    break
                if zone_fn(ss) != here:
                    return d, zone_fn(ss)
            return None, here

        s = s0
        while s < s1:
            q = at_fn(s)
            cur = zone_fn(s)
            da, after = change(s, 1)
            db, before = change(s, -1)
            if da is not None and (db is None or da <= db):
                a_, b_, t = cur, after, 0.5 * (1.0 - da / blend)
            elif db is not None:
                a_, b_, t = before, cur, 0.5 + 0.5 * db / blend
            else:
                a_, b_, t = cur, cur, 0.0
            x, y, z = c.game(q.p.x, q.p.y, q.p.z)
            keys.append([round(x, 1), round(y, 1), round(z, 1), a_, b_, round(L.sm(t), 3)])
            k = SNOW[a_] * (1 - L.sm(t)) + SNOW[b_] * L.sm(t)
            snow.append([round(x, 1), round(y, 1), round(z, 1), round(k, 2)])
            s += 12.0

    add(lambda s: main_zone(c, s), lambda s: c.at(s % M.length), 0.0, M.length, True)
    for branch, lane in sc.lanes.items():
        add(lambda s, b=branch: lane_zone(sc, b, s), lane.at, lane.s0, lane.s1, False)
    c.entity("atmosphere", zones=ZONES, keys=keys)
    # The blizzard: wind from the north-west (game x, z), how hard it snows where.
    c.entity("blizzard", wind=[0.78, -0.62], keys=snow)


# ------------------------------------------------------------------ build


def build(c, sc):
    sc.fires = []
    sc.flags = []
    sc.bells = []
    sc.avalanches = []
    sc.channels = []
    gate(c, sc)
    citadel(c, sc)
    village(c, sc)
    fork_signs(c, sc)
    cliff(c, sc)
    supply(c, sc)
    starvation(c, sc)
    broken_bridges(c, sc)
    avalanche_run(c, sc)
    monastery(c, sc)
    aqueduct(c, sc)
    ascent(c, sc)
    scenery(c, sc)
    for i, run in enumerate(sc.channels):
        c.ribbon("Frozen Channel %d" % i, run, 3.0, run[0][3], c.lib("sdp_ice_channel"), coll="Props", role="visual")


def entities(c, sc):
    dragon(c, sc)
    c.entity("villagers", list=sc.crowd)
    print("villagers:", len(sc.crowd))
    air(c, sc)
    for x, y, z in sc.fires:
        game_entity(c, "campfire", x, y, z)
    lines = []
    for (ax, ay, az), (bx, by, bz), sag in sc.flags:
        a = c.game(ax, ay, az)
        b = c.game(bx, by, bz)
        lines.append([*(round(v, 2) for v in a), *(round(v, 2) for v in b), round(sag, 2)])
    c.entity("prayer_flags", lines=lines)
    c.entity("bells", list=[[round(v, 2) for v in c.game(x, y, z)] for x, y, z in sc.bells])
    av = []
    for (ax, ay, az), (bx, by, bz), period, offset in sc.avalanches:
        a = c.game(ax, ay, az)
        b = c.game(bx, by, bz)
        av.append([*(round(v, 1) for v in a), *(round(v, 1) for v in b), round(period, 1), round(offset, 1)])
    c.entity("avalanches", list=av)
    print("flags:", len(lines), "bells:", len(sc.bells), "avalanches:", len(av), "fires:", len(sc.fires))
