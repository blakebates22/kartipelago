# Dragon Isles' kingdom (see dragon_isles.py): the Grand Ceremonial Gate, the festival
# village and its canal, the cliffs' waterfalls, the Great Waterfall Bridge, the temple
# and its gardens, the karst towers of the Sky Paths, the Lantern Harbour, the Ancient
# Dragon Passage, the overlook, the royal avenue and the palace on its mountain; the
# villagers, the boats, the birds and the great dragon's flight (for the game).
# SPDX-License-Identifier: MIT

import math

import isles_land as L
import isles_props as ip
import props
from course_kit import rnd
from isles_scenery import clear, game_entity

S = L.S


# ------------------------------------------------------------------ helpers


def roadside(c, s, off):
    """The point `off` metres right of the road at lap distance s (negative: left), and
    the turn that faces a prop there back toward the road."""
    q = c.at(s % c.length)
    p = q.side(off)
    return p.x, p.y, ip.facing(p.x, p.y, q.p.x, q.p.y), q


def put(sc, proto, x, y, rot=0.0, scale=1.0, coll="Props", role="visual", sink=0.0, z=None):
    gz = sc.ground(x, y) if z is None else z
    return sc.put(proto, x, y, gz - sink, rot, scale, coll=coll, role=role)


def fwd(rot):
    """A prop's front (its +Y) after turning by rot (Blender x, y)."""
    return -math.sin(rot), math.cos(rot)


def villager(c, sc, x, y, role, face_x, face_y, variant=None, z=None):
    """A villager for the game to animate (game/islesLife.ts): where, facing what, doing
    what (cheer, wave, merchant, dancer, musician, fisher, gardener, guard, bow)."""
    gz = sc.ground(x, y) if z is None else z
    dx, dy = face_x - x, face_y - y
    n = math.hypot(dx, dy) or 1.0
    k = len(sc.crowd)
    v = variant if variant is not None else int(rnd(k * 13 + 7) * 8)
    gx, gy, gzz = c.game(x, y, gz)
    sc.crowd.append([round(gx, 2), round(gy, 2), round(gzz, 2), round(dx / n, 3), round(-dy / n, 3), role, v])


def crowd_along(c, sc, s0, s1, off0, off1, every, role="cheer", sides=(-1, 1), skip=None, chance=0.8):
    """Cheering villagers lining the road between off0 and off1 metres from its centre."""
    s = s0
    k = 0
    while s < s1:
        for side in sides:
            for row in range(2):
                k += 1
                if rnd(k * 3.7 + s) > chance:
                    continue
                off = side * (off0 + (off1 - off0) * (row + 0.3 * rnd(k)) / 2.0)
                x, y, _, q = roadside(c, s + rnd(k * 1.3) * every * 0.6, off)
                if skip is not None and skip(x, y):
                    continue
                if not clear(c, x, y, abs(off0) - q.w / 2 - 0.5):
                    continue
                r = role if rnd(k * 5.1) > 0.25 else ("wave" if role == "cheer" else role)
                villager(c, sc, x, y, r, q.p.x, q.p.y)
        s += every


def strings_across(c, sc, s0, s1, every, height=8.0, kind="lantern", posts=True):
    """Lantern strings (or bunting) across the road between red posts."""
    s = s0
    k = 0
    while s < s1:
        q = c.at(s % c.length)
        half = q.w / 2 + 3.0
        a = q.side(-half)
        b = q.side(half)
        span = math.hypot(b.x - a.x, b.y - a.y)
        rot = math.atan2(b.y - a.y, b.x - a.x)
        top = max(a.z, b.z) + height
        if posts:
            for p in (a, b):
                put(sc, ip.lantern_post(c), p.x, p.y, rot + (math.pi if p is a else 0.0), coll="Props", role="both")
                sc.light("lantern", p.x, p.y, p.z + 4.0)
        proto = ip.lantern_string(c, 20.0) if kind == "lantern" else ip.bunting_string(c, 20.0)
        sc.put(proto, a.x, a.y, top, rot, (span / 20.0, 1.0, 1.0), coll="Props", role="visual")
        if kind == "lantern":
            for t in (0.3, 0.7):
                sc.light("lantern", a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t, top - 1.5)
        s += every
        k += 1


def row_of(c, sc, s0, s1, every, off, protos, side=1, margin=4.0, footprint=5.0, coll="Town", role="both", jitter=0.0):
    """Buildings in a row along the road, fronts to it."""
    s = s0
    k = 0
    placed = []
    while s < s1:
        x, y, rot, q = roadside(c, s + jitter * (rnd(k * 2.1) - 0.5), side * off)
        if clear(c, x, y, footprint + margin - 2.0) and sc.free(x, y, footprint) and L.canal_d(x, y) > L.CANAL_HW + footprint + 2:
            proto = protos[k % len(protos)]
            put(sc, proto, x, y, rot, coll=coll, role=role)
            sc.footprints.append((x, y, footprint))
            placed.append((x, y, rot))
        s += every
        k += 1
    return placed


# ------------------------------------------------------------------ 1  the Grand Ceremonial Gate and 11 the finish


def gate_and_finish(c, sc):
    # The great gate just past the line, the royal gate before it.
    for s, span, mat in ((36.0, 28.0, "roof_gold"), (c.length - 46.0, 26.0, "roof_blue")):
        q = c.at(s % c.length)
        rot = math.atan2(q.t.y, q.t.x) - math.pi / 2
        put(sc, ip.gate(c, span, 13.0, mat, grand=True), q.p.x, q.p.y, rot, coll="Landmarks", role="both", z=q.p.z)
    # Dragon statues either side of the start, facing the road.
    for s in (-18.0, 14.0, 62.0):
        for side, mat in ((-1, "jade_stone"), (1, "isle_gold" if s == 14.0 else "jade_stone")):
            x, y, rot, q = roadside(c, s, side * (q_w(c, s) / 2 + 6.0))
            put(sc, ip.dragon_statue(c, mat), x, y, rot, coll="Landmarks", role="both")
            sc.footprints.append((x, y, 3.5))
    # Banners and crowds along the start straight; grandstand terraces behind them.
    for s in range(-70, 90, 12):
        for side in (-1, 1):
            x, y, rot, q = roadside(c, s, side * 14.5)
            if sc.free(x, y, 1.5):
                put(sc, ip.banner_pole(c, "banner_royal" if (s // 12) % 2 else "banner_jade"), x, y, rot, role="both")
    crowd_along(c, sc, -80, 90, 15.5, 22.0, 4.5, role="cheer", chance=0.9)
    for side in (-1, 1):
        for s in (-55.0, 75.0):
            x, y, rot, q = roadside(c, s, side * 27.0)
            put(sc, ip.pavilion(c, 8.0, "roof_jade", rail=True), x, y, rot, coll="Town", role="both")
            sc.footprints.append((x, y, 6.0))
    strings_across(c, sc, -40.0, 80.0, 40.0, height=9.0, kind="bunting", posts=False)


def q_w(c, s):
    return c.at(s % c.length).w


# ------------------------------------------------------------------ 2  the Riverside Festival Village


def village(c, sc):
    a, b = S[1] - 10.0, S[8] + 10.0
    houses = [ip.house(c, v) for v in range(5)]
    shops = [ip.shop(c, v) for v in range(4)]
    mix = [shops[0], houses[0], shops[1], houses[1], houses[2], shops[2], houses[3], shops[3], houses[4]]
    for side in (-1, 1):
        placed = row_of(c, sc, a, b, 12.5, 18.5, mix if side > 0 else mix[::-1], side=side, footprint=6.0, jitter=2.0)
        # Second row behind, here and there.
        row_of(c, sc, a + 6, b, 17.0, 33.0, houses, side=side, footprint=6.5, jitter=4.0)
        for x, y, rot in placed:
            fx, fy = fwd(rot)
            villager(c, sc, x + fx * 5.0, y + fy * 5.0, "merchant", x + fx * 20, y + fy * 20)
    crowd_along(c, sc, a, b, 10.0, 13.5, 5.0, role="cheer", chance=0.75)
    # Stalls along the street.
    k = 0
    s = a + 8.0
    while s < b:
        side = 1 if k % 2 else -1
        x, y, rot, q = roadside(c, s, side * 14.0)
        if clear(c, x, y, 4.5) and sc.free(x, y, 2.5) and L.canal_d(x, y) > L.CANAL_HW + 4:
            put(sc, ip.stall(c, k % 4), x, y, rot, role="both")
            sc.footprints.append((x, y, 2.5))
        s += 19.0
        k += 1
    strings_across(c, sc, a + 12, b, 24.0, height=7.5, kind="lantern")
    strings_across(c, sc, a + 24, b, 48.0, height=10.0, kind="bunting", posts=False)
    # The canal: stone banks, footbridges, moored sampans, a mill with its wheel.
    for (x, y) in ((-48.0, 148.0), (75.0, 166.0)):
        put(sc, ip.bridge_arch(c, 22.0), x, y, math.pi / 2 - 0.1, coll="Town", role="both", z=sc.info(x, y + 14) - 1.0)
    for x, y, r in ((-62.0, 141.0, 0.15), (95.0, 169.0, 0.05), (110.0, 172.0, -0.1)):
        put(sc, ip.sampan(c, 0), x, y, r + math.pi / 2, coll="Harbour", role="visual", z=-0.1)
    mx, my = -22.0, 170.0
    put(sc, ip.waterwheel_house(c), mx, my, 0.0, coll="Town", role="both")
    sc.footprints.append((mx, my, 5.0))
    wy = 162.0  # the wheel turns in the canal below the mill, its axle across the flow
    gx, gy, gz = c.game(mx, wy, 3.2)
    c.entity("waterwheel", x=round(gx, 2), y=round(gy, 2), z=round(gz, 2), heading=0.0, radius=3.4, speed=0.8)
    # The festival square on the waterfront: the drum stage, dancers, musicians.
    sx, sy = L.SQUARE
    put(sc, ip.drum_stage(c), sx + 10, sy, ip.facing(sx + 10, sy, sx - 20, sy), coll="Landmarks", role="both")
    sc.footprints.append((sx + 10, sy, 7.0))
    for i in range(10):
        a_ = i * math.tau / 10
        villager(c, sc, sx - 8 + 7 * math.cos(a_), sy + 7 * math.sin(a_), "dancer", sx - 8, sy)
    for i in range(3):
        villager(c, sc, sx + 8 + (i - 1) * 3.0, sy + 1.0, "musician", sx - 10, sy, z=sc.ground(sx + 10, sy) + 1.2)
    for i in range(14):
        a_ = i * math.tau / 14 + 0.2
        villager(c, sc, sx - 8 + 14 * math.cos(a_), sy + 14 * math.sin(a_), "cheer", sx - 8, sy)
    for i in range(4):
        x, y = sx - 18 + i * 9, sy + 18
        put(sc, ip.banner_pole(c, "banner_royal"), x, y, 0.0, role="both")
    game_entity(c, "motes", sx, sy, sc.ground(sx, sy) + 6, radius=70.0, rate=10.0, color="#ffc0d8", rise=-0.35, size=0.3)
    # Blossom along the waterfront and among the houses.
    for i in range(26):
        x = -60 + rnd(i * 3.3) * 160
        y = 90 + rnd(i * 7.1) * 180
        if clear(c, x, y, 9.0) and sc.free(x, y, 3.0) and L.canal_d(x, y) > L.CANAL_HW + 3 and sc.info(x, y) > 3:
            put(sc, ip.blossom_tree(c, i % 4), x, y, rnd(i) * 6.28, coll="Plants", role="both", sink=0.2)
            sc.footprints.append((x, y, 2.5))
    for i in range(18):
        x = -90 + rnd(i * 5.3) * 100
        y = 60 + rnd(i * 2.9) * 220
        if clear(c, x, y, 8.0) and sc.free(x, y, 2.5) and L.canal_d(x, y) > L.CANAL_HW + 3 and sc.info(x, y) > 3:
            put(sc, ip.bamboo(c, i % 3), x, y, rnd(i) * 6.28, coll="Plants", role="both", sink=0.2)
            sc.footprints.append((x, y, 2.0))
    # Unease: down a side street, a royal gate, shut.
    x, y, rot, q = roadside(c, S[6] + 4.0, -42.0)
    put(sc, ip.gatehouse(c, 8.0), x, y, rot, coll="Landmarks", role="both")
    sc.footprints.append((x, y, 8.0))
    for k in (-1, 1):
        fx, fy = fwd(rot)
        gx_, gy_ = x + fx * 3.0 + math.cos(rot) * k * 3.2, y + fy * 3.0 + math.sin(rot) * k * 3.2
        villager(c, sc, gx_, gy_, "guard", gx_ + fx, gy_ + fy)


# ------------------------------------------------------------------ 3  the Cliffside Ascent, 4  the Great Waterfall Bridge


def cliffs(c, sc):
    # The great falls up the gorge, and a falls either side of the bridge.
    foot = L.WATER_Z + 0.3
    fx, fy = props.falls(c, "Great Falls", L.RIVER_X, L.FALLS_Y, L.Z_HIGH - 2.6, foot, 30.0, 40.0, facing=-1, throw=9.0, bulge=2.0, veils=4)
    game_entity(c, "waterfall", fx, fy, foot, top=L.Z_HIGH - 2.6, width=34.0, heading=0.0)
    game_entity(c, "motes", fx, fy + 10, 12.0, radius=40.0, rate=10.0, color="#ffffff", rise=0.8, size=0.6)
    for name, x, y, ang in (("East Gorge Falls", 194.0, 446.0, -math.pi / 2), ("West Gorge Falls", 104.0, 380.0, math.pi / 2)):
        top = sc.info(x + (8 if ang < 0 else -8), y) - 0.6
        props.falls(c, name, x, y, top, foot, 7.0, 10.0, facing=-1, throw=5.0, bulge=1.0, veils=2, angle=ang)
        game_entity(c, "waterfall", x, y, foot, top=round(top, 1), width=8.0, heading=round(ang, 3))
    # Off the great karst wall into the valley.
    for name, y in (("Wall Falls North", 245.0), ("Wall Falls South", 40.0)):
        x = -168.0
        top = sc.info(x - 6, y) - 0.8
        props.falls(c, name, x, y, top, sc.info(x + 22, y) + 0.2, 6.0, 12.0, facing=-1, throw=7.0, bulge=1.0, veils=2,
                    angle=math.pi / 2, mats=("falls_sheet", "falls_veil", "falls_foam"))
        game_entity(c, "waterfall", x + 12, y, sc.info(x + 22, y), top=round(top, 1), width=8.0, heading=round(math.pi / 2, 3))
    # Bridge piers under the stone bridges.
    for piece in c.pieces:
        kind = piece.name.split()[-1]
        if kind in ("bridge", "sky_bridge", "harbour_bridge", "canal_bridge"):
            props.piers(c, piece, every=26.0 if kind != "canal_bridge" else 10.0, mat=("stone_base", "wall"), size=2.6 if kind == "bridge" else 1.8,
                        terrain=sc.ground_obs, inset=2.4)
    # The bridge's ends: dragon statues, pavilions, lanterns along it.
    for s, side in ((S[14] + 4, -1), (S[14] + 4, 1), (S[15] - 6, -1), (S[15] - 6, 1)):
        x, y, rot, q = roadside(c, s, side * 13.0)
        put(sc, ip.dragon_statue(c, "jade_stone"), x, y, rot, coll="Landmarks", role="both")
        sc.footprints.append((x, y, 3.5))
    for s in range(int(S[14]) + 20, int(S[15]) - 10, 24):
        for side in (-1, 1):
            q = c.at(s)
            p = q.side(side * (q.w / 2 + 0.5))
            sc.put(ip.stone_lantern(c), p.x, p.y, p.z, 0.0, 0.8, coll="Props", role="visual")
            sc.light("lantern", p.x, p.y, p.z + 1.6)
    # Lookout pavilions and pines on the cliff ledges; stone lanterns up the climb.
    for s, off in ((S[9] + 30, -20.0), (S[12] + 10, -18.0), (S[8] + 20, 22.0)):
        x, y, rot, q = roadside(c, s, off)
        if clear(c, x, y, 5.0):
            put(sc, ip.pavilion(c, 6.0, "roof_jade"), x, y, rot, coll="Town", role="both")
            sc.footprints.append((x, y, 5.0))
    for s in range(int(S[8]), int(S[14]), 22):
        for side in (-1, 1):
            q = c.at(s)
            p = q.side(side * (q.w / 2 + 2.6))
            if clear(c, p.x, p.y, 1.5):
                sc.put(ip.stone_lantern(c), p.x, p.y, sc.ground(p.x, p.y), 0.0, 0.8, role="visual")
                sc.light("lantern", p.x, p.y, p.z + 1.6)
    k = 0
    for i in range(160):
        x = -150 + rnd(i * 2.7) * 360
        y = 300 + rnd(i * 5.9) * 260
        z = sc.info(x, y)
        if z < 12 or not clear(c, x, y, 8.0) or L.gorge(x, y) > -6 or not sc.free(x, y, 3.0):
            continue
        put(sc, ip.pine(c, k % 5), x, y, rnd(i) * 6.28, coll="Plants", role="both", sink=0.3, scale=0.9 + rnd(i * 3) * 0.5)
        k += 1
    game_entity(c, "birds", 40.0, 420.0, 90.0, radius=90, count=5, speed=0.18, seed=3, color="#f4f4f0")


# ------------------------------------------------------------------ 5  the Temple Gardens


def temple(c, sc):
    tx, ty = L.TEMPLE  # the courtyard (the shortcut runs through it, along y)
    hz = sc.info(tx, ty + 45)
    # The main hall north of the courtyard, facing it; side halls; the pagoda in the
    # garden inside the bend.
    put(sc, ip.hall(c, 26.0, 14.0, 6.0, "roof_gold", tiers=2), tx, ty + 46, math.pi, coll="Temple", role="both")
    sc.footprints.append((tx, ty + 46, 18.0))
    for dx in (-36.0, 36.0):
        put(sc, ip.hall(c, 14.0, 9.0, 4.5, "roof_jade", tiers=1), tx + dx, ty + 38, math.pi, coll="Temple", role="both")
        sc.footprints.append((tx + dx, ty + 38, 10.0))
    gx, gy = tx + 6.0, ty - 50.0
    put(sc, ip.pagoda(c, 7, 9.0, "roof_jade"), gx, gy, 0.0, coll="Temple", role="both")
    sc.footprints.append((gx, gy, 10.0))
    for dx, dy in ((-30.0, -22.0), (34.0, -22.0)):
        put(sc, ip.pavilion(c, 6.0, "roof_gold"), gx + dx, gy + dy, 0.0, coll="Temple", role="both")
        sc.footprints.append((gx + dx, gy + dy, 5.0))
    for i in range(14):
        a_ = i * math.tau / 14
        x, y = gx + math.cos(a_) * 16.0, gy + math.sin(a_) * 16.0
        if clear(c, x, y, 2.0) and sc.free(x, y, 0.8):
            sc.put(ip.stone_lantern(c), x, y, sc.ground(x, y), 0.0, 0.8, coll="Gardens", role="visual")
            sc.light("lantern", x, y, sc.ground(x, y) + 1.7)
    for dx in (-30.0, 34.0):
        put(sc, ip.lotus_pool(c, 7.0), gx + dx, gy + 6, 0.0, coll="Gardens", role="both", sink=0.1)
        sc.footprints.append((gx + dx, gy + 6, 8.0))
    # Gates framing the courtyard passage, and over the main road at the bend's ends.
    for x in (tx - 42.0, tx + 42.0):
        put(sc, ip.gate(c, 14.0, 9.0, "roof_blue", grand=False), x, ty, -math.pi / 2, coll="Landmarks", role="both", z=sc.info(x, ty))
    for s in (S[16] + 4.0, S[23] - 4.0):
        q = c.at(s)
        put(sc, ip.gate(c, 20.0, 10.0, "roof_jade", grand=False), q.p.x, q.p.y, math.atan2(q.t.y, q.t.x) - math.pi / 2, coll="Landmarks",
            role="both", z=q.p.z)
    # Statues facing the road; stone lanterns; blossom; hedges; guards that never move.
    for s in range(int(S[17]), int(S[22]), 26):
        for side in (-1, 1):
            x, y, rot, q = roadside(c, s, side * (q_w(c, s) / 2 + 4.5))
            if clear(c, x, y, 2.5) and sc.free(x, y, 2.0) and math.hypot(x - tx, y - ty) > 8:
                put(sc, ip.guardian_statue(c), x, y, rot, coll="Temple", role="both")
                sc.footprints.append((x, y, 2.0))
    for s in range(int(S[15]), int(S[24]), 14):
        for side in (-1, 1):
            q = c.at(s)
            p = q.side(side * (q.w / 2 + 2.4))
            if clear(c, p.x, p.y, 1.5) and sc.free(p.x, p.y, 1.0):
                sc.put(ip.stone_lantern(c), p.x, p.y, sc.ground(p.x, p.y), 0.0, 0.85, role="visual")
                sc.light("lantern", p.x, p.y, p.z + 1.8)
    for i in range(70):
        x = tx - 120 + rnd(i * 4.4) * 240
        y = ty - 100 + rnd(i * 8.3) * 180
        if not clear(c, x, y, 6.0) or not sc.free(x, y, 3.0) or sc.info(x, y) < 40:
            continue
        proto = ip.blossom_tree(c, i % 4) if i % 3 else ip.pine(c, i % 5)
        put(sc, proto, x, y, rnd(i) * 6.28, coll="Plants", role="both", sink=0.2)
        sc.footprints.append((x, y, 2.5))
    for i in range(40):
        x = tx - 110 + rnd(i * 3.7) * 220
        y = ty - 110 + rnd(i * 9.1) * 200
        if clear(c, x, y, 5.0) and sc.free(x, y, 2.5) and sc.info(x, y) > 40:
            put(sc, ip.bamboo(c, i % 3), x, y, rnd(i) * 6.28, coll="Plants", role="both", sink=0.2)
            sc.footprints.append((x, y, 2.0))
    for i in range(30):
        x = tx - 70 + rnd(i * 6.1) * 140
        y = ty - 90 + rnd(i * 2.9) * 70
        if clear(c, x, y, 4.0) and sc.free(x, y, 2.5) and sc.info(x, y) > 40:
            put(sc, ip.hedge_box(c, 5.0), x, y, rnd(i) * 3.0, coll="Gardens", role="both", sink=0.2)
    for i in range(6):
        x = tx - 12 + i * 5
        villager(c, sc, x, ty + 27, "guard", x, ty)  # in perfect formation before the hall
    for x, y in ((tx - 40, ty - 30), (tx + 45, ty - 25), (tx - 15, ty - 75), (tx + 30, ty - 70)):
        if clear(c, x, y, 3.0):
            villager(c, sc, x, y, "gardener", x + 3, y + 1)
    crowd_along(c, sc, S[15], S[16] + 10, 11.0, 14.0, 6.0, role="bow", chance=0.6)
    crowd_along(c, sc, S[23], S[24], 11.0, 14.0, 6.0, role="bow", chance=0.6)
    game_entity(c, "motes", tx, ty - 30, hz + 6, radius=90.0, rate=14.0, color="#ffb8d0", rise=-0.3, size=0.32)
    game_entity(c, "little_dragons", gx, gy, hz + 34.0, radius=26.0, count=3, speed=0.35, seed=1)


# ------------------------------------------------------------------ 6  the Sky Paths


def sky(c, sc):
    """Karst towers: under the Sky Paths' spans, round the lagoon and far off."""
    k = 0
    # Towers standing in the lagoon beside the Sky Paths (clear of the road).
    for i in range(70):
        x = 380 + rnd(i * 3.1) * 380
        y = -480 + rnd(i * 6.7) * 900
        if not clear(c, x, y, 26.0) or sc.info(x, y) > -1 or not sc.free(x, y, 16):
            continue
        sc_ = 0.7 + rnd(i * 2.2) * 0.8
        put(sc, ip.karst(c, k % 6), x, y, rnd(i) * 6.28, sc_, coll="Rocks Small", role="both", z=L.SEA)
        sc.footprints.append((x, y, 10 * sc_ + 4))
        k += 1
    # Round the lagoon's far side and the edges of the world.
    for i in range(90):
        a = rnd(i * 1.7) * math.tau
        r = 700 + rnd(i * 4.3) * 900
        x = 180 + math.cos(a) * r
        y = 100 + math.sin(a) * r
        if L.GRID[0] < x < L.GRID[1] and L.GRID[2] < y < L.GRID[3]:
            continue
        if x < -360:
            continue  # the great wall's there
        sc_ = 1.0 + rnd(i * 2.9) * 1.8
        sc.put(ip.karst(c, i % 6), x, y, L.SEA - 2, rnd(i) * 6.28, sc_, coll="Far Rocks", role="visual")
    # Pagoda-capped spine pillars, banners on the long bridge.
    for s in (S[26] + 50, S[28] + 40):
        x, y, rot, q = roadside(c, s, 24.0)
        if clear(c, x, y, 6):
            put(sc, ip.pavilion(c, 6.0, "roof_blue"), x, y, rot, coll="Town", role="both")
    for s in range(int(S[29]) + 10, int(S[30]) - 10, 18):
        for side in (-1, 1):
            q = c.at(s)
            p = q.side(side * (q.w / 2 + 0.4))
            sc.put(ip.banner_pole(c, "banner_royal" if (s // 18) % 2 else "banner_jade"), p.x, p.y, p.z - 0.2,
                   math.atan2(q.t.y, q.t.x) + (0 if side > 0 else math.pi), 0.8, coll="Props", role="visual")
    game_entity(c, "birds", 600.0, 0.0, 70.0, radius=120, count=6, speed=0.16, seed=7, color="#f4f4f0")
    game_entity(c, "little_dragons", 470.0, 150.0, 70.0, radius=60.0, count=2, speed=0.25, seed=4)


# ------------------------------------------------------------------ 7  the Lantern Harbour


def harbour(c, sc):
    a, b = S[31] + 20, S[34] - 10
    houses = [ip.house(c, v) for v in range(5)]
    shops = [ip.shop(c, v) for v in range(4)]
    mix = [shops[1], houses[1], houses[0], shops[2], houses[3], shops[0], houses[4]]
    placed = row_of(c, sc, a, b, 13.0, 17.0, mix, side=1, footprint=6.0, coll="Harbour")
    row_of(c, sc, a + 6, b, 15.0, 31.0, houses, side=1, footprint=6.5, coll="Harbour", jitter=3)
    for x, y, rot in placed:
        fx, fy = fwd(rot)
        villager(c, sc, x + fx * 5.0, y + fy * 5.0, "merchant", x + fx * 20, y + fy * 20)
    crowd_along(c, sc, a, b, 10.0, 12.5, 6.0, role="cheer", sides=(1,), chance=0.75)
    strings_across(c, sc, a + 8, b, 22.0, height=7.0, kind="lantern")
    # Docks out into the lagoon on the seaward side, junks and sampans moored.
    k = 0
    for s in range(int(a) + 10, int(b), 34):
        x, y, rot, q = roadside(c, s, -(q_w(c, s) / 2 + 1.5))
        put(sc, ip.dock(c, 18.0, 4.0), x, y, rot + math.pi, coll="Harbour", role="both", z=1.2)
        fx, fy = fwd(rot + math.pi)
        bx, by = x + fx * 12.0 + math.cos(rot) * 6.0, y + fy * 12.0 + math.sin(rot) * 6.0
        boat = ip.junk(c, k % 2) if k % 3 != 2 else ip.sampan(c, k)
        put(sc, boat, bx, by, rot + math.pi, coll="Harbour", role="visual", z=-0.2)
        villager(c, sc, x + fx * 16.0, y + fy * 16.0, "fisher", x + fx * 30.0, y + fy * 30.0, z=3.4)
        k += 1
    # The festival dragon boat, out on the water.
    put(sc, ip.dragon_boat(c), 300.0, -350.0, 0.3, coll="Harbour", role="visual", z=-0.1)
    # Unease: between the houses, a doorway onto a dark corridor.
    x, y, rot, q = roadside(c, S[33] + 95.0, 34.0)
    put(sc, ip.dark_arch(c), x, y, rot, coll="Harbour", role="both")
    sc.footprints.append((x, y, 6.0))
    villager(c, sc, x + fwd(rot)[0] * 2.5 + 3.0, y + fwd(rot)[1] * 2.5, "guard", q.p.x, q.p.y)
    # Junks sailing the lagoon (the oasis boat, on loops of their own).
    for k, (cx, cy, rx, ry, sp) in enumerate(((330.0, -420.0, 120.0, 40.0, 3.0), (650.0, 120.0, 60.0, 180.0, 2.6), (120.0, -40.0, 50.0, 90.0, 2.4))):
        pts = [(cx + rx * math.cos(a_ * math.tau / 16), cy + ry * math.sin(a_ * math.tau / 16)) for a_ in range(16)]
        if any(not clear(c, x, y, 18.0) for x, y in pts):
            continue
        c.path_curve("Junk Path %d" % (k + 1), pts, z=0.0, closed=True)
        c.entity("boat", route="Junk Path %d" % (k + 1), speed=sp, start=round(k * 41.0, 1), colors=["#c8322a", "#f2d27a"], scale=1.3)
    game_entity(c, "birds", 320.0, -260.0, 40.0, radius=70, count=6, speed=0.22, seed=11, color="#ffffff")


# ------------------------------------------------------------------ 8  the Ancient Dragon Passage, 9  the Grand Reveal, 10  the Royal Approach


def passage(c, sc):
    s0, s1 = L.S[36] + 4.0, L.S[37] + 22.0
    q0 = c.at(s0 - 10.0)
    # The royal emblem over the tunnel's mouth.
    rot = math.atan2(q0.t.y, q0.t.x) + math.pi / 2
    sc.put(ip.emblem_plaque(c), q0.p.x - q0.t.x * 2, q0.p.y - q0.t.y * 2, q0.p.z + 13.0, rot + math.pi, 1.6, coll="Landmarks", role="visual")
    # Inside: lanterns along the walls, old carvings faintly glowing, the sealed door.
    k = 0
    s = s0 + 6
    while s < s1 - 4:
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 1.4))
            sc.put(ip.stone_lantern(c), p.x, p.y, p.z, 0.0, 0.7, coll="Props", role="visual")
            sc.light("lantern", p.x, p.y, p.z + 1.6)
            if k % 2 == 0:
                g = q.side(side * (q.w / 2 + 2.3))
                sc.light("teal", g.x, g.y, g.z + 4.0)
        s += 14.0
        k += 1
    q = c.at(s0 + 34.0)
    p = q.side(q.w / 2 + 2.4)
    rot = ip.facing(p.x, p.y, q.p.x, q.p.y)
    sc.put(ip.sealed_door(c), p.x, p.y, p.z - 0.3, rot, 0.95, coll="Landmarks", role="visual")
    sc.light("teal", p.x, p.y, p.z + 4.0)
    fx, fy = fwd(rot)
    villager(c, sc, p.x + fx * 1.5 - math.cos(rot) * 5.5, p.y + fy * 1.5 - math.sin(rot) * 5.5, "guard", q.p.x, q.p.y, z=p.z)
    game_entity(c, "motes", q.p.x, q.p.y, q.p.z + 4, radius=30.0, rate=6.0, color="#7affe0", rise=0.08, size=0.2, blink=True)
    # The overlook: a pavilion, a balustrade, the kingdom spread out below.
    x, y, rot, q = roadside(c, S[37] + 40.0, 18.0)
    if clear(c, x, y, 5.0):
        put(sc, ip.pavilion(c, 7.0, "roof_gold"), x, y, rot, coll="Town", role="both")
    for s in range(int(S[37]) + 30, int(S[38]) + 40, 22):
        for side in (-1, 1):
            q = c.at(s)
            p = q.side(side * (q.w / 2 + 2.4))
            if clear(c, p.x, p.y, 1.5):
                sc.put(ip.stone_lantern(c), p.x, p.y, sc.ground(p.x, p.y), 0.0, 0.85, role="visual")
                sc.light("lantern", p.x, p.y, p.z + 1.6)


def royal(c, sc):
    a, b = S[39] - 10.0, c.length - 52.0
    # Guards in perfect formation both sides; statues facing the road; banners.
    s = a
    k = 0
    while s < b:
        for side in (-1, 1):
            x, y, rot, q = roadside(c, s, side * (q_w(c, s) / 2 + 3.0))
            villager(c, sc, x, y, "guard", q.p.x, q.p.y)
            if k % 3 == 0:
                x2, y2, rot2, q2 = roadside(c, s + 3, side * (q_w(c, s) / 2 + 8.0))
                if sc.free(x2, y2, 2):
                    put(sc, ip.dragon_statue(c, "jade_stone") if k % 2 else ip.guardian_statue(c), x2, y2, rot2, coll="Landmarks",
                        role="both")
                    sc.footprints.append((x2, y2, 3.0))
            if k % 2 == 1:
                x3, y3, rot3, _ = roadside(c, s, side * (q_w(c, s) / 2 + 11.5))
                if sc.free(x3, y3, 1.5):
                    put(sc, ip.banner_pole(c, "banner_royal"), x3, y3, rot3, role="both")
        s += 7.0
        k += 1
    crowd_along(c, sc, a, b, 14.0, 18.0, 6.0, role="bow", chance=0.7)
    # Walls with roofs behind, halls beyond.
    for s in range(int(a), int(b), 14):
        for side in (-1, 1):
            x, y, rot, q = roadside(c, s, side * 24.0)
            if clear(c, x, y, 3.0) and sc.free(x, y, 2.0):
                put(sc, ip.wall(c, 14.0, 4.2), x, y, rot, coll="Town", role="both")
    for s, side in ((S[39] + 20, -1), (S[40] + 20, 1), (S[40] - 10, -1)):
        x, y, rot, q = roadside(c, s, side * 40.0)
        if clear(c, x, y, 10.0) and sc.free(x, y, 10.0):
            put(sc, ip.hall(c, 16.0, 10.0, 5.0, "roof_blue", tiers=2), x, y, rot, coll="Town", role="both")
            sc.footprints.append((x, y, 12.0))


# ------------------------------------------------------------------ the palace on its mountain


def palace(c, sc):
    """The royal palace on its mountain, far to the north: terraces of halls, pagodas
    and walls, big enough to read from the start line 1.2 km away."""
    px, py = L.PALACE
    z = L.PALACE_Z
    K = 2.6  # its scale
    # The terraces it stands on, stepping down the mountain.
    bm_names = []
    for i, (w, d, h) in enumerate(((200.0, 150.0, 70.0), (150.0, 110.0, 16.0), (90.0, 70.0, 12.0))):
        name = "Palace Terrace %d" % i

        def build(bm, w=w, d=d, h=h):
            ip._box(bm, -w / 2, -d / 2, -h, w / 2, d / 2, 0.0)
            ip._box(bm, -w / 2 - 1, -d / 2 - 1, -1.0, w / 2 + 1, d / 2 + 1, 1.2)
            return [(c.lib("stone_base"), list(range(len(bm.faces))))]

        c.proto(name, build)
        bm_names.append(name)
    zs = (z, z + 16.0, z + 28.0)
    for name, zz in zip(bm_names, zs):
        sc.put(name, px, py, zz, 0.0, 1.0, coll="Palace", role="visual")
    hall = ip.hall(c, 30.0, 16.0, 7.0, "roof_gold", tiers=2)
    sc.put(hall, px, py, zs[2] + 1.0, math.pi, K, coll="Palace", role="visual")
    for dx in (-52.0, 52.0):
        sc.put(ip.hall(c, 16.0, 10.0, 5.0, "roof_blue", tiers=2), px + dx, py - 20, zs[1] + 1.0, math.pi, K * 0.9, coll="Palace", role="visual")
        sc.put(ip.pagoda(c, 7, 8.0, "roof_gold"), px + dx * 1.55, py + 10, zs[0] + 1.0, 0.0, K * 0.9, coll="Palace", role="visual")
    for dx in range(-90, 91, 30):
        sc.put(ip.wall(c, 30.0, 6.0, "roof_blue"), px + dx, py - 75, zs[0] + 1.0, 0.0, 1.0 * K * 0.5, coll="Palace", role="visual")
    sc.put(ip.gate(c, 18.0, 12.0, "roof_gold", grand=True), px, py - 76, zs[0] + 1.0, 0.0, K * 0.7, coll="Palace", role="visual")
    for k, dx in enumerate((-80, -40, 40, 80)):
        sc.put(ip.banner_pole(c, "banner_royal"), px + dx, py - 80, zs[0] + 1.0, 0.0, K, coll="Palace", role="visual")


# ------------------------------------------------------------------ the dragon's flight


def dragon(c, sc):
    """The great dragon's flight, keyed to where the leader is on the lap: (lap distance,
    x, y, z). The game (islesLife.ts) flies it smoothly between these, swaying."""
    def over(s, up, ox=0.0, oy=0.0):
        q = c.at(s % c.length)
        return (q.p.x + ox, q.p.y + oy, q.p.z + up)

    px, py = L.PALACE
    sb = S[29] + 60.0  # the signature pass over the long bridge
    bx, by, bz = over(sb, 0.0)
    keys = [
        (0.0, 40.0, 1120.0, 230.0),  # by the palace, ahead as the race starts
        (S[2], -110.0, 940.0, 200.0),
        (S[6], -80.0, 760.0, 160.0),  # coming south between the mountains
        (S[9], 150.0, 640.0, 120.0),  # across the valley from the cliff road
        (S[12], 150.0, 545.0, 78.0),  # over the great falls as you reach the bridge
        (S[14] + 70, 260.0, 520.0, 90.0),
        (S[18], 420.0, 520.0, 110.0),  # behind the temple
        (S[22], 620.0, 420.0, 100.0),
        (S[25] + 40, 660.0, 260.0, 80.0),
        (S[28], 620.0, by + 90.0, 60.0),
        (sb - 25, bx + 70.0, by + 15.0, bz + 30.0),
        (sb, bx, by, bz + 24.0),  # straight overhead
        (sb + 25, bx - 75.0, by - 15.0, bz + 30.0),
        (S[31] + 20, 380.0, -200.0, 46.0),  # low over the harbour: its shadow on the road
        (S[34], 150.0, 200.0, 120.0),  # away north over the lagoon
        (S[37] + 30, 60.0, 700.0, 180.0),  # seen from the overlook, heading for the palace
        (S[40], 100.0, 1000.0, 220.0),
        (c.length - 1.0, 45.0, 1115.0, 230.0),
    ]
    out = []
    for s, x, y, z in keys:
        gx, gy, gz = c.game(x, y, z)
        out.append([round(s, 1), round(gx, 1), round(gy, 1), round(gz, 1)])
    c.entity("isles_dragon", keys=out, length=round(c.length, 1), size=1.0)
    # Report the speeds it implies (for a kart at ~24 m/s), to keep the flight graceful.
    for (s0, *a), (s1, *b) in zip(keys, keys[1:]):
        d = math.dist(a, b)
        t = max(0.5, (s1 - s0) / 24.0)
        if d / t > 70:
            print("dragon fast: %.0f m/s from s=%.0f" % (d / t, s0))


# ------------------------------------------------------------------ the air


ZONES = {  # the air and the sound of each part (game/depths.ts' atmosphere)
    "gate": {"fog": "#cfe4f4", "near": 520, "far": 2900, "sun": 2.7, "sky": "#c4dcff", "ground": "#86a070", "hemi": 1.25, "sound": "festival"},
    "village": {"fog": "#cfe4f4", "near": 480, "far": 2700, "sun": 2.7, "sky": "#c8dcff", "ground": "#8aa070", "hemi": 1.25, "sound": "festival"},
    "cliff": {"fog": "#d4e8f4", "near": 420, "far": 2600, "sun": 2.6, "sky": "#c4dcff", "ground": "#7a9a70", "hemi": 1.2, "sound": "falls"},
    "temple": {"fog": "#d8e6f0", "near": 460, "far": 2700, "sun": 2.6, "sky": "#d4dcff", "ground": "#8aa078", "hemi": 1.25, "sound": "garden"},
    "sky": {"fog": "#cfe4f6", "near": 560, "far": 3000, "sun": 2.8, "sky": "#c0dcff", "ground": "#70a0a0", "hemi": 1.25, "sound": "wind"},
    "harbour": {"fog": "#cfe4f4", "near": 480, "far": 2800, "sun": 2.7, "sky": "#c4dcff", "ground": "#80a0a0", "hemi": 1.25, "sound": "harbour"},
    "passage": {"fog": "#2a3a38", "near": 40, "far": 420, "sun": 0.5, "sky": "#a0d8c8", "ground": "#3a3028", "hemi": 0.9, "sound": "drip"},
    "reveal": {"fog": "#d4e8f8", "near": 600, "far": 3200, "sun": 2.8, "sky": "#c8e0ff", "ground": "#8aa070", "hemi": 1.3, "sound": "wind"},
}
ZONE_OF = {"gate": "gate", "village": "village", "cliff": "cliff", "bridge": "cliff", "temple": "temple", "sky": "sky", "harbour": "harbour",
           "passage": "passage", "reveal": "reveal", "royal": "gate"}


def atmosphere(c, sc):
    """Keys every 12 m along the lap: the zone either side and how far between them,
    blending over `blend` metres each side of every change."""
    keys = []
    blend = 24.0
    tunnel = (L.S[36] - 4, L.S[37] + 30)

    def zone(s):
        s %= c.length
        if tunnel[0] <= s <= tunnel[1]:
            return "passage"
        z = ZONE_OF[L.zone_of(s)]
        if z == "passage":  # either side of the tunnel: the harbour's air, then the overlook's
            return "harbour" if s < tunnel[0] else "reveal"
        return z

    def change(s, direction):
        here = zone(s)
        d = 0.0
        while d < blend:
            d += 2.0
            if zone(s + direction * d) != here:
                return d, zone(s + direction * d)
        return None, here

    s = 0.0
    while s < c.length:
        q = c.at(s)
        cur = zone(s)
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
        s += 12.0
    for i in range(0, len(L.SHORTCUT), 8):
        x, y, z = c.game(*L.SHORTCUT[i])
        keys.append([round(x, 1), round(y, 1), round(z, 1), "temple", "temple", 0.0])
    c.entity("atmosphere", zones=ZONES, keys=keys)


# ------------------------------------------------------------------ build


def build(c, sc):
    gate_and_finish(c, sc)
    village(c, sc)
    cliffs(c, sc)
    temple(c, sc)
    sky(c, sc)
    harbour(c, sc)
    passage(c, sc)
    royal(c, sc)
    palace(c, sc)


def entities(c, sc):
    dragon(c, sc)
    c.entity("villagers", list=sc.crowd)
    print("villagers:", len(sc.crowd))
    atmosphere(c, sc)
    for kind, col in (("teal", "#5affd8"), ("lantern", "#ffb060")):
        pts = sc.lights.get(kind, [])
        step = 1 if kind == "teal" else 6
        for x, y, z in pts[::step]:
            game_entity(c, "glow", x, y, z, color=col)
