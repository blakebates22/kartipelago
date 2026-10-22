# Celestial Dragon Festival's kingdom (see celestial_dragon_festival.py): the Festival
# Gate and the finish, the night market, the waterfront and its lantern boats, the
# Dragon Promenade's plaza of worship, the Celestial Climb, the Star Bridge, the
# Observatory, the Palace Terraces, the Procession Causeway, the Fireworks Overlook, the
# Final Ascension's golden arches, the Celestial Palace on its mountain; the crowds, the
# imperial dragon's flight, the festival's fireworks (for the game) and the air.
# SPDX-License-Identifier: MIT

import math

import cdf_land as L
import cdf_props as cp
import isles_props as ip
from cdf_scenery import clear, game_entity
from course_kit import rnd
from isles_town import crowd_along, fwd, put, roadside, strings_across, villager

A = L.at
S = L.S


def q_w(c, s):
    return c.at(s % c.length).w


def ok(c, sc, x, y, r, margin=3.0):
    return clear(c, x, y, r + margin) and sc.free(x, y, r)


def place(c, sc, proto, x, y, rot, r, coll="Town", role="both", sink=0.0, scale=1.0, z=None, margin=3.0):
    """A building or statue where there's room for it (r: its footprint)."""
    if not ok(c, sc, x, y, r, margin):
        return False
    put(sc, proto, x, y, rot, scale, coll=coll, role=role, sink=sink, z=z)
    sc.footprints.append((x, y, r))
    return True


def along(c, s0, s1, every):
    s = s0
    while s < s1:
        yield s
        s += every


def braziers(c, sc, s0, s1, every, off=3.0, sides=(-1, 1)):
    for s in along(c, s0, s1, every):
        for side in sides:
            x, y, rot, q = roadside(c, s, side * (q_w(c, s) / 2 + off))
            if sc.free(x, y, 1.2):
                put(sc, cp.brazier(c), x, y, rot, coll="Props", role="both")
                sc.footprints.append((x, y, 1.2))
                sc.light("fire", x, y, sc.ground(x, y) + cp.BRAZIER_LIGHT)


def banners(c, sc, s0, s1, every, off=3.0, mats=("cdf_banner_dragon", "cdf_banner_star")):
    k = 0
    for s in along(c, s0, s1, every):
        for side in (-1, 1):
            x, y, rot, q = roadside(c, s, side * (q_w(c, s) / 2 + off))
            if sc.free(x, y, 1.0):
                put(sc, ip.banner_pole(c, mats[k % len(mats)]), x, y, rot, coll="Props", role="both")
                sc.footprints.append((x, y, 1.0))
        k += 1


def pillars_along(c, sc, s0, s1, every, off=1.2, deck=False):
    """Star pillars along a high road (on a bridge: on its parapets)."""
    for s in along(c, s0, s1, every):
        q = c.at(s % c.length)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + off))
            z = p.z if deck else sc.ground(p.x, p.y)
            sc.put(cp.star_pillar(c, 6.0), p.x, p.y, z, 0.0, 1.0, coll="Props", role="visual" if deck else "both")
            sc.light("star", p.x, p.y, z + cp.STAR_LIGHT - 1.0)


def chevrons(c, sc, s, side):
    """Turn boards on the outside of a bend (their arrows point the way to go)."""
    q = c.at(s % c.length)
    p = q.side(side * (q.w / 2 + 2.4))
    rot = math.atan2(q.t.y, q.t.x) + (math.pi if side < 0 else 0.0)
    sc.put(chevron(c), p.x, p.y, sc.ground(p.x, p.y), rot, 1.0, coll="Props", role="both")


def chevron(c):
    name = "Festival Chevron"

    def build(bm):
        k = len(bm.faces)
        ip._box(bm, -3.0, -0.2, 0.0, 3.0, 0.2, 1.6)
        face = list(range(k, len(bm.faces)))
        k = len(bm.faces)
        for x in (-3.2, 3.2):
            ip._box(bm, x - 0.2, -0.25, -0.4, x + 0.2, 0.25, 1.9)
        gold = list(range(k, len(bm.faces)))
        return [(c.lib("cdf_chevron"), face), (c.lib("cdf_gold"), gold)]

    return ip._p(c, name, build)


def stand(c, sc, s, off, side, length=24.0, rows=4, role="cheer"):
    """A grandstand beside the road (its front row `off` m from the road's edge), its
    crowd on its steps facing the road."""
    x, y, rot, q = roadside(c, s, side * (q_w(c, s) / 2 + off))
    ca, sa = math.cos(rot), math.sin(rot)
    for lx in (-length / 2, 0.0, length / 2):
        for ly in (0.0, -1.6 * rows):
            wx, wy = x + lx * ca - ly * sa, y + lx * sa + ly * ca
            if not clear(c, wx, wy, off - 1.5):
                return
    cx, cy = x + 0.8 * rows * sa, y - 0.8 * rows * ca
    if not sc.free(cx, cy, length / 2):
        return
    gz = sc.ground(x, y)
    put(sc, cp.grandstand(c, length, rows), x, y, rot, coll="Town", role="both", z=gz)
    sc.footprints.append((cx, cy, length / 2))
    for k, (lx, ly, lz) in enumerate(cp.grandstand_rows(length, rows)):
        if rnd(k * 1.7 + s) > 0.55:
            continue
        wx, wy = x + lx * ca - ly * sa, y + lx * sa + ly * ca
        r_ = role if rnd(k * 3.1 + s) > 0.3 else "wave"
        villager(c, sc, wx, wy, r_, q.p.x, q.p.y, z=gz + lz)


def trees(c, sc, cx, cy, r, n, seed, zmin=-99, blossom=0.75):
    k = 0
    for i in range(n * 3):
        a = rnd(seed + i * 1.3) * math.tau
        d = r * math.sqrt(rnd(seed + i * 2.7))
        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
        if sc.info(x, y) < zmin or not ok(c, sc, x, y, 2.5, margin=4.0):
            continue
        proto = ip.blossom_tree(c, k % 4) if rnd(seed + i) < blossom else ip.pine(c, k % 5)
        put(sc, proto, x, y, rnd(i) * 6.28, 0.9 + 0.5 * rnd(i * 3), coll="Plants", role="both", sink=0.2)
        sc.footprints.append((x, y, 2.5))
        k += 1
        if k >= n:
            break


# ------------------------------------------------------------------ footprints


def footprints(c, sc):
    """Keep the islands and the scatter off the palace and the observatory."""
    sc.footprints.append((L.PALACE[0], L.PALACE[1], 120.0))
    sc.footprints.append((L.PINNACLE[0], L.PINNACLE[1], 30.0))


# ------------------------------------------------------------------ 1  the Festival Gate, 12  the Grand Finale


def gate(c, sc):
    L_ = c.length
    # The great ceremonial gate just past the line, the celestial arch before it.
    for s, kind in ((34.0, "gate"), (L_ - 40.0, "arch"), (L_ - 150.0, "arch")):
        q = c.at(s % L_)
        rot = math.atan2(q.t.y, q.t.x) - math.pi / 2
        span = q.w + 6.0
        proto = ip.gate(c, span, 16.0, "roof_gold", grand=True) if kind == "gate" else cp.celestial_arch(c, span, 16.0)
        sc.put(proto, q.p.x, q.p.y, q.p.z, rot, 1.0, coll="Landmarks", role="both")
        sc.light("gold", q.p.x, q.p.y, q.p.z + 14.0)
    # Colossal golden dragons either side of the line, facing the road.
    for s in (-10.0, 60.0):
        for side in (-1, 1):
            x, y, rot, q = roadside(c, s, side * (q_w(c, s) / 2 + 9.0))
            place(c, sc, cp.colossus(c), x, y, rot, 7.0, coll="Landmarks", scale=2.6, margin=0.0)
            sc.light("gold", x, y, q.p.z + 12.0)
    # Grandstands packed with the crowd, banners, lanterns across the road.
    for s in (-120.0, -70.0, 100.0):
        for side in (-1, 1):
            stand(c, sc, s, 4.0, side, 26.0, 5)
    crowd_along(c, sc, -150, 110, q_w(c, 0) / 2 + 1.5, q_w(c, 0) / 2 + 3.5, 4.0, role="cheer", chance=0.6)
    banners(c, sc, -150.0, 120.0, 16.0, off=1.5)
    strings_across(c, sc, -140.0, 120.0, 22.0, height=10.0, kind="lantern", posts=False)
    braziers(c, sc, -150.0, 120.0, 32.0, off=2.6)
    # Drum stages and dancers on the terrace south of the straight.
    for s in (-40.0, 70.0):
        x, y, rot, q = roadside(c, s, 40.0)
        if place(c, sc, ip.drum_stage(c), x, y, rot, 7.0, coll="Landmarks"):
            for i in range(8):
                a = i * math.tau / 8
                villager(c, sc, x + 9 * math.cos(a), y + 9 * math.sin(a), "dancer", x, y)


# ------------------------------------------------------------------ 2  the Lantern Market Curve


def market(c, sc):
    a, b = A("m1", 0.0) - 20.0, A("m3", 0.0)
    houses = [ip.house(c, v) for v in range(5)]
    shops = [ip.shop(c, v) for v in range(4)]
    mix = [shops[0], houses[0], shops[1], houses[1], shops[2], houses[2], shops[3], houses[3]]
    k = 0
    for s in along(c, a, b, 13.0):
        for side, off in ((1, 19.0), (-1, 19.0)):
            x, y, rot, q = roadside(c, s, side * off)
            if place(c, sc, mix[k % len(mix)], x, y, rot, 6.0, margin=1.0):
                fx, fy = fwd(rot)
                villager(c, sc, x + fx * 5.0, y + fy * 5.0, "merchant", x + fx * 20, y + fy * 20)
            k += 1
    for s in along(c, a + 6, b, 17.0):
        for side in (1, -1):
            x, y, rot, q = roadside(c, s, side * (q_w(c, s) / 2 + 4.6))
            if sc.free(x, y, 2.2) and clear(c, x, y, 3.0):
                put(sc, ip.stall(c, k % 4), x, y, rot, coll="Props", role="both")
                sc.footprints.append((x, y, 2.2))
                sc.light("lantern", x, y, sc.ground(x, y) + 3.0)
            k += 1
    crowd_along(c, sc, a, b, q_w(c, a) / 2 + 2.0, q_w(c, a) / 2 + 5.0, 5.0, role="cheer", chance=0.55)
    strings_across(c, sc, a + 10, b, 20.0, height=9.0, kind="lantern", posts=True)
    strings_across(c, sc, a + 20, b, 40.0, height=11.5, kind="bunting", posts=False)
    # Floats waiting for the procession; performers.
    for s, side in ((A("m1", 0.6), 1), (A("m2", 0.5), 1)):
        x, y, rot, q = roadside(c, s, side * 32.0)
        place(c, sc, cp.dragon_float(c), x, y, rot + math.pi / 2, 6.0, margin=1.0)
    for i in range(30):
        s = a + rnd(i * 2.3) * (b - a)
        x, y, rot, q = roadside(c, s, (1 if i % 2 else -1) * (30.0 + rnd(i) * 30.0))
        if sc.info(x, y) > 3 and ok(c, sc, x, y, 1.0):
            villager(c, sc, x, y, "dancer" if i % 3 else "musician", q.p.x, q.p.y)
    trees(c, sc, 180.0, -120.0, 110.0, 16, 11, zmin=3.0)
    chevrons(c, sc, A("m2", 0.4), -1)


# ------------------------------------------------------------------ 3  the Waterfall Bridge


def waterfront(c, sc):
    a, b = A("m3", 0.0), S["p1"] + 20.0
    # Stone lanterns and banners along the bridge's parapets.
    for s in along(c, a + 40, b - 30, 26.0):
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 0.6))
            sc.put(ip.stone_lantern(c), p.x, p.y, p.z, 0.0, 0.9, coll="Props", role="visual")
            sc.light("lantern", p.x, p.y, p.z + 1.8)
    for s in along(c, a + 53, b - 30, 52.0):
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 0.6))
            sc.put(ip.banner_pole(c, "cdf_banner_dragon"), p.x, p.y, p.z - 0.2, math.atan2(q.t.y, q.t.x) + (0 if side > 0 else math.pi), 0.9,
                   coll="Props", role="visual")
    # Pagodas and pavilions on the islands across the inlet.
    k = 0
    for x, y, s_ in sc.islands:
        if x < L.INLET[1] + 120 and -100 < y < 360 and x > L.INLET[0] + 60 and k < 6:
            top = L.SEA + 26.0 * s_
            sc.put(ip.pagoda(c, 5, 6.0, "roof_gold" if k % 2 else "roof_blue"), x, y, top, rnd(k) * 6.28, 1.0, coll="Temple", role="visual")
            sc.light("lantern", x, y, top + 4.0)
            sc.launchers.append((x, y, top))
            k += 1
    # Lantern boats sailing the inlet and the lagoon.
    loops = ((L.INLET[0] + 90.0, 40.0, 40.0, 100.0, 2.4), (L.INLET[0] + 120.0, 180.0, 30.0, 70.0, 2.0), (200.0, -260.0, 120.0, 40.0, 2.8),
             (-60.0, -230.0, 90.0, 35.0, 2.6), (560.0, 120.0, 50.0, 140.0, 2.2))
    for k, (cx, cy, rx, ry, sp) in enumerate(loops):
        pts = [(cx + rx * math.cos(i * math.tau / 16), cy + ry * math.sin(i * math.tau / 16)) for i in range(16)]
        if any(not clear(c, x, y, 16.0) or sc.info(x, y) > -1.0 for x, y in pts):
            continue
        c.path_curve("Boat Path %d" % (k + 1), pts, z=0.0, closed=True)
        c.entity("boat", route="Boat Path %d" % (k + 1), speed=sp, start=round(k * 37.0, 1), colors=["#c8322a", "#f2d27a"], scale=1.3)
    for i, (x, y) in enumerate(((470.0, -40.0), (520.0, 240.0), (100.0, -250.0), (-120.0, -260.0))):
        if sc.info(x, y) < -2 and clear(c, x, y, 14.0):
            put(sc, ip.dragon_boat(c) if i % 2 == 0 else ip.junk(c, i % 2), x, y, rnd(i) * 6.28, coll="Props", role="visual", z=-0.1)
    game_entity(c, "motes", L.INLET[0] + 80, 120.0, 30.0, radius=120.0, rate=10.0, color="#ffffff", rise=0.6, size=0.5)


# ------------------------------------------------------------------ 4  the Dragon Promenade


def promenade(c, sc):
    a, b = S["p1"] + 30.0, S["c1"]
    px, py = L.PLAZA
    gz = sc.info(px, py + 30)
    # The altar of the dragon, facing the road across the plaza.
    ax, ay = px, py + 48.0
    put(sc, cp.altar(c), ax, ay, math.pi, 1.4, coll="Landmarks", role="both", z=sc.info(ax, ay))
    sc.footprints.append((ax, ay, 18.0))
    sc.light("gold", ax, ay - 4, sc.info(ax, ay) + 8.0)
    sc.light("fire", ax - 6.4, ay - 1.7, sc.info(ax, ay) + 7.5)
    sc.light("fire", ax + 6.4, ay - 1.7, sc.info(ax, ay) + 7.5)
    # Two colossal golden dragons either side of the altar.
    for dx in (-34.0, 34.0):
        x, y = ax + dx, ay - 4.0
        put(sc, cp.colossus(c), x, y, math.pi, 4.0, coll="Landmarks", role="both", z=sc.info(x, y))
        sc.footprints.append((x, y, 10.0))
        sc.light("gold", x, y, sc.info(x, y) + 22.0)
    # Gongs, murals, braziers.
    for dx in (-18.0, 18.0):
        place(c, sc, cp.gong(c), ax + dx, ay - 10.0, math.pi, 3.0, coll="Landmarks", margin=0.0)
    for dx in (-60.0, 60.0):
        place(c, sc, cp.mural_wall(c), ax + dx, ay + 6.0, math.pi, 6.0, coll="Landmarks", margin=0.0)
    for i in range(10):
        x = ax - 45 + i * 10
        if sc.free(x, ay - 24, 1.2):
            put(sc, cp.brazier(c), x, ay - 24.0, 0.0, coll="Props", role="both")
            sc.light("fire", x, ay - 24.0, sc.info(x, ay - 24) + cp.BRAZIER_LIGHT)
    # The worshippers: rows kneeling toward the altar, priests before it, dancers in a
    # ring, the crowd along the road.
    for row in range(5):
        for i in range(16):
            x = ax - 30 + i * 4.0 + (2.0 if row % 2 else 0.0)
            y = ay - 16.0 - row * 3.2
            if ok(c, sc, x, y, 0.6, margin=2.0):
                villager(c, sc, x, y, "worship", ax, ay)
    for i in range(6):
        villager(c, sc, ax - 7.5 + i * 3.0, ay - 6.0, "monk", ax, ay, z=sc.info(ax, ay) + 1.8)
    for side in (-1, 1):
        cx, cy = ax + side * 62.0, ay - 22.0
        for i in range(10):
            ang = i * math.tau / 10
            villager(c, sc, cx + 7 * math.cos(ang), cy + 7 * math.sin(ang), "dancer", cx, cy)
    crowd_along(c, sc, a, b, q_w(c, a) / 2 + 2.0, q_w(c, a) / 2 + 6.0, 4.0, role="bow", chance=0.6, sides=(1,))
    banners(c, sc, a, b, 18.0, off=1.6)
    braziers(c, sc, a, b, 36.0, off=2.6, sides=(-1,))
    for s in (a + 30.0, b - 40.0):
        q = c.at(s)
        sc.put(cp.celestial_arch(c, q.w + 6.0, 15.0), q.p.x, q.p.y, q.p.z, math.atan2(q.t.y, q.t.x) - math.pi / 2, 1.0, coll="Landmarks",
               role="both")
        sc.light("gold", q.p.x, q.p.y, q.p.z + 14.0)
    game_entity(c, "motes", px, py + 20, gz + 8, radius=90.0, rate=14.0, color="#ffb8d8", rise=-0.3, size=0.32)
    trees(c, sc, px + 120.0, py + 40.0, 60.0, 12, 21)
    trees(c, sc, px - 120.0, py + 50.0, 50.0, 10, 23)


# ------------------------------------------------------------------ 5  the Celestial Climb, 6  the Star Bridge


def climb(c, sc):
    a, b = S["c1"], L.STAR[0]
    pillars_along(c, sc, a + 10, b, 30.0, off=2.6)
    for name in ("c1", "c2", "c3"):
        s = A(name, 0.5)
        chevrons(c, sc, s, 1 if name == "c2" else -1)
    for s, off in ((A("c2", 0.3), 24.0), (A("c3", 0.4), -26.0), (A("c1", 0.3), -26.0)):
        x, y, rot, q = roadside(c, s, off)
        place(c, sc, ip.pavilion(c, 7.0, "roof_gold"), x, y, rot, 5.0)
    trees(c, sc, 140.0, 340.0, 80.0, 24, 31, zmin=25.0)
    crowd_along(c, sc, a, b, q_w(c, a) / 2 + 3.0, q_w(c, a) / 2 + 6.0, 9.0, role="wave", chance=0.4)


def star_bridge(c, sc):
    a, b = L.STAR
    o0, o1 = L.STAR_OPEN
    # Star pillars on the parapets either side of the open stretch, navy star banners.
    pillars_along(c, sc, a + 15.0, o0 - 10.0, 34.0, off=0.6, deck=True)
    pillars_along(c, sc, o1 + 15.0, b, 34.0, off=0.6, deck=True)
    # Lamps right at the open stretch's ends so you see where the parapets stop.
    for s in (o0 - 2.0, o1 + 2.0):
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 0.6))
            sc.put(cp.star_pillar(c, 4.0), p.x, p.y, p.z, 0.0, 1.0, coll="Props", role="visual")
            sc.light("star", p.x, p.y, p.z + 4.6)


# ------------------------------------------------------------------ 7  the Observatory


def observatory(c, sc):
    ox, oy = L.PINNACLE
    oz = sc.info(ox, oy)
    sc.observatory = (ox, oy, oz)
    put(sc, cp.observatory(c), ox, oy, 0.0, coll="Landmarks", role="both", z=oz)
    for k in range(8):
        a = k * math.tau / 8
        sc.light("star", ox + 16 * math.cos(a), oy + 16 * math.sin(a), oz + 10.0)
    sc.light("gold", ox, oy, oz + 30.0)
    s0, s1 = S["o1"] - 10.0, A("o3", 1.0)
    pillars_along(c, sc, s0, s1, 28.0, off=2.4)
    for s in along(c, s0 + 14, s1, 56.0):
        chevrons(c, sc, s, -1)
    sc.launchers.append((ox, oy, oz + 20.0))


# ------------------------------------------------------------------ 8  the Palace Terraces


def terraces(c, sc):
    a, b = A("o3", 0.6), A("t2", 1.0)
    # Halls with domes facing the road on the palace's side, gardens and pools between.
    for s in along(c, a + 20, b, 46.0):
        x, y, rot, q = roadside(c, s, -34.0)
        place(c, sc, cp.dome_hall(c, 22.0, 14.0, 8.0, 1), x, y, rot, 15.0)
        x2, y2, rot2, _ = roadside(c, s + 23, -20.0)
        if place(c, sc, ip.lotus_pool(c, 6.0), x2, y2, rot2, 7.0, coll="Gardens", sink=0.1):
            sc.light("lantern", x2, y2, sc.ground(x2, y2) + 1.5)
    for s in along(c, a, b, 16.0):
        for side in (-1, 1):
            q = c.at(s)
            p = q.side(side * (q.w / 2 + 2.8))
            if sc.free(p.x, p.y, 1.0) and clear(c, p.x, p.y, 1.8):
                sc.put(ip.stone_lantern(c), p.x, p.y, sc.ground(p.x, p.y), 0.0, 0.9, role="visual")
                sc.light("lantern", p.x, p.y, sc.ground(p.x, p.y) + 1.8)
    for s in along(c, a + 8, b, 24.0):
        x, y, rot, q = roadside(c, s, -(q_w(c, s) / 2 + 3.5))
        villager(c, sc, x, y, "guard", q.p.x, q.p.y)
    trees(c, sc, -150.0, 330.0, 70.0, 26, 41, blossom=0.9)
    for i in range(18):
        x, y, rot, q = roadside(c, a + rnd(i * 4.1) * (b - a), -(16.0 + rnd(i) * 30.0))
        if ok(c, sc, x, y, 2.0):
            put(sc, ip.hedge_box(c, 5.0), x, y, rnd(i) * 3.0, coll="Gardens", role="both", sink=0.2)
            sc.footprints.append((x, y, 2.0))
    crowd_along(c, sc, a, b, q_w(c, a) / 2 + 2.5, q_w(c, a) / 2 + 5.5, 6.0, role="bow", chance=0.45, sides=(1,))
    game_entity(c, "motes", -170.0, 300.0, 80.0, radius=80.0, rate=12.0, color="#ffb8d8", rise=-0.3, size=0.32)


# ------------------------------------------------------------------ 9  the Procession Causeway, 10  the Fireworks Overlook


def causeway(c, sc):
    a, b = A("t2", 1.0), S["v2"]
    for s in along(c, a + 10, b - 10, 32.0):
        for side in (-1, 1):
            stand(c, sc, s, 3.5, side, 22.0, 4, role="bow" if side < 0 else "cheer")
    banners(c, sc, a, b, 14.0, off=1.4)
    braziers(c, sc, a, b, 28.0, off=2.4)
    for s in (a + 20.0, b - 20.0):
        for side in (-1, 1):
            x, y, rot, q = roadside(c, s, side * (q_w(c, s) / 2 + 9.0))
            if place(c, sc, cp.colossus(c), x, y, rot, 6.0, coll="Landmarks", scale=2.2, margin=0.0):
                sc.light("gold", x, y, q.p.z + 10.0)
    # A procession of monks with banners walking beside the road (well, standing in line).
    for i, s in enumerate(along(c, a + 15, b - 15, 7.0)):
        x, y, rot, q = roadside(c, s, -(q_w(c, s) / 2 + 1.6))
        if sc.free(x, y, 0.6):
            villager(c, sc, x, y, "monk", x + q.t.x, y + q.t.y)
    strings_across(c, sc, a + 10, b, 30.0, height=10.0, kind="lantern", posts=False)


def overlook(c, sc):
    a, b = S["v2"] - 20.0, A("v2", 1.0)
    x, y = L.OVERLOOK
    place(c, sc, ip.pavilion(c, 8.0, "roof_gold"), x, y, ip.facing(x, y, 0, 0), 6.0, margin=0.0)
    for s in along(c, a, b, 18.0):
        q = c.at(s)
        p = q.side(-(q.w / 2 + 0.6))
        sc.put(ip.stone_lantern(c), p.x, p.y, q.p.z, 0.0, 0.9, coll="Props", role="visual")
        sc.light("lantern", p.x, p.y, q.p.z + 1.8)
    crowd_along(c, sc, a, b, q_w(c, a) / 2 + 2.0, q_w(c, a) / 2 + 5.0, 4.0, role="cheer", chance=0.6, sides=(1,))


# ------------------------------------------------------------------ 11  the Final Ascension


def ascension(c, sc):
    a, b = A("v2", 1.0), c.length - 160.0
    for s in along(c, a + 20, b, 44.0):
        q = c.at(s)
        sc.put(cp.celestial_arch(c, q.w + 6.0, 15.0), q.p.x, q.p.y, q.p.z, math.atan2(q.t.y, q.t.x) - math.pi / 2, 1.0, coll="Landmarks",
               role="both")
        sc.light("gold", q.p.x, q.p.y, q.p.z + 14.0)
    for s in along(c, a + 10, b, 30.0):
        for side in (1,):
            stand(c, sc, s, 4.0, side, 20.0, 4)
    crowd_along(c, sc, a, b, q_w(c, a) / 2 + 2.0, q_w(c, a) / 2 + 4.0, 5.0, role="cheer", chance=0.5, sides=(-1,))
    chevrons(c, sc, A("v3", 0.5), 1)
    braziers(c, sc, a, b, 30.0, off=2.4)


# ------------------------------------------------------------------ the Celestial Palace


def palace(c, sc):
    """The Celestial Palace on the Palace Mount's crown: marble terraces, the great hall
    under its three domes, four onion-domed towers, gold-roofed pagodas, banners, the
    colossal dragons at its gate. Big enough to read from anywhere on the lap."""
    px, py = L.PALACE
    z0 = sc.info(px, py)
    sc.palace_z = z0
    put(sc, cp.terrace(c, 170.0, 136.0, 30.0), px, py, 0.0, coll="Palace", role="visual", z=z0 + 2.0)
    put(sc, cp.terrace(c, 120.0, 92.0, 12.0), px, py + 10, 0.0, coll="Palace", role="visual", z=z0 + 14.0)
    zt = z0 + 14.0
    put(sc, cp.dome_hall(c, 44.0, 28.0, 14.0, 3), px, py + 14, 0.0, 2.4, coll="Palace", role="visual", z=zt)
    for dx, dy in ((-74.0, -56.0), (74.0, -56.0), (-74.0, 58.0), (74.0, 58.0)):
        put(sc, cp.dome_tower(c, 34.0, 4.6), px + dx, py + dy, 0.0, 2.1, coll="Palace", role="visual", z=z0 + 2.0)
        sc.light("gold", px + dx, py + dy, z0 + 60.0)
    for dx in (-46.0, 46.0):
        put(sc, ip.pagoda(c, 7, 8.0, "roof_gold"), px + dx, py - 40.0, 0.0, 2.4, coll="Palace", role="visual", z=z0 + 2.0)
    put(sc, ip.gate(c, 20.0, 14.0, "roof_gold", grand=True), px, py - 70.0, 0.0, 2.4, coll="Palace", role="visual", z=z0 + 2.0)
    for dx in (-30.0, 30.0):
        put(sc, cp.colossus(c), px + dx, py - 78.0, 0.0, 5.0, coll="Palace", role="visual", z=z0 + 2.0)
    for k, dx in enumerate(range(-80, 81, 20)):
        put(sc, ip.banner_pole(c, "cdf_banner_dragon" if k % 2 else "cdf_banner_star"), px + dx, py - 68.0, 0.0, 2.4, coll="Palace",
            role="visual", z=z0 + 2.0)
    for k in range(10):
        sc.light("gold", px - 70 + k * 15.0, py - 66.0, z0 + 8.0)
    sc.light("gold", px, py + 14, zt + 70.0)
    sc.light("gold", px, py - 20, zt + 30.0)
    for dx, dy in ((-60.0, 0.0), (60.0, 0.0), (0.0, -50.0), (0.0, 60.0)):
        sc.launchers.append((px + dx, py + dy, z0 + 4.0))


def islands_temples(c, sc):
    """Lantern-lit temples on the karst islands round the lagoon (and rockets from them)."""
    k = 0
    for x, y, s_ in sc.islands:
        if rnd(x * 0.13 + y) > 0.3 or k > 14:
            continue
        top = L.SEA + 26.0 * s_
        proto = ip.pagoda(c, 3 + k % 3, 5.0, ("roof_gold", "roof_blue", "roof_jade")[k % 3]) if k % 2 else ip.pavilion(c, 6.0, "roof_gold")
        sc.put(proto, x, y, top, rnd(k) * 6.28, 1.0, coll="Temple", role="visual")
        sc.light("lantern", x, y, top + 3.0)
        sc.launchers.append((x, y, top))
        k += 1


def mountain(c, sc):
    """The Palace Mount's terraced gardens: blossom and pine, little halls and pagodas,
    stone lanterns; the observatory pinnacle's pines."""
    X0, X1, Y0, Y1 = L.GRID
    k = 0
    built = 0
    for i in range(2400):
        x = -260 + rnd(i * 1.37) * 700
        y = -40 + rnd(i * 2.11 + 5) * 560
        if not L.inside(x, y) or math.hypot(x - L.PINNACLE[0], y - L.PINNACLE[1]) < 60:
            continue
        z = sc.info(x, y)
        smp, d = c.nearest(x, y)
        if z < smp.p.z + 4 or not ok(c, sc, x, y, 3.0, margin=6.0):
            continue
        if built < 26 and rnd(i * 5.3) < 0.12 and ok(c, sc, x, y, 7.0, margin=8.0):
            proto = (ip.pagoda(c, 5, 6.0, "roof_gold"), ip.hall(c, 12.0, 8.0, 4.0, "roof_blue", tiers=2), ip.pavilion(c, 6.0, "roof_jade"),
                     cp.dome_tower(c, 18.0, 3.0))[built % 4]
            put(sc, proto, x, y, ip.facing(x, y, smp.p.x, smp.p.y), coll="Temple", role="visual")
            sc.footprints.append((x, y, 7.0))
            sc.light("lantern", x, y, z + 4.0)
            built += 1
            continue
        proto = ip.blossom_tree(c, k % 4) if rnd(i * 3.1) < 0.6 else ip.pine(c, k % 5)
        put(sc, proto, x, y, rnd(i) * 6.28, 0.9 + 0.6 * rnd(i * 7.7), coll="Plants", role="visual", sink=0.3)
        sc.footprints.append((x, y, 2.5))
        k += 1
        if k > 260:
            break
    print("mountain: trees %d, buildings %d" % (k, built))


def city_south(c, sc):
    """The lower city below the gate's terrace: rooftops, lanterns, a pagoda or two."""
    houses = [ip.house(c, v) for v in range(5)]
    k = 0
    for i in range(160):
        x = -200 + rnd(i * 3.3) * 560
        y = -230 + rnd(i * 7.7) * 190
        if L.city(x, y) < 0.6 or not ok(c, sc, x, y, 6.0, margin=6.0):
            continue
        z = sc.info(x, y)
        if z < 2:
            continue
        put(sc, houses[k % 5] if k % 9 else ip.pagoda(c, 5, 6.0, "roof_gold"), x, y, rnd(i) * 6.28, coll="Market", role="visual")
        sc.footprints.append((x, y, 6.0))
        if k % 2 == 0:
            sc.light("lantern", x, y, z + 6.0)
        if k % 7 == 0:
            sc.launchers.append((x, y, z))
        k += 1


# ------------------------------------------------------------------ the imperial dragon


def dragon(c, sc):
    """The imperial dragon's flight, keyed to where you are on the lap; on the last lap
    (game/festival.ts' grand finale) it takes the finale's path: up round the palace as you
    climb the Final Ascension, then low over the finish."""
    def over(s, up, side=0.0):
        q = c.at(s % c.length)
        p = q.side(side)
        return (p.x, p.y, q.p.z + up)

    px, py = L.PALACE
    pz = getattr(sc, "palace_z", 100.0)
    ox, oy = L.PINNACLE
    star = L.STAR[0] + 120.0
    keys = [
        (0.0, 60.0, 60.0, 150.0),  # over the gate as the race starts
        (S["m1"], 260.0, 120.0, 140.0),
        (A("m3", 0.4), *over(A("m3", 0.4), 70.0, 120.0)),  # over the inlet beside the bridge
        (S["p1"], *over(S["p1"], 60.0, 40.0)),
        (A("p1", 0.6), *over(A("p1", 0.6), 34.0, -20.0)),  # low over the Dragon Promenade: the worshippers bow
        (S["c2"], 120.0, 420.0, 130.0),
        (star - 60.0, *over(star - 60.0, 70.0, 60.0)),
        (star, *over(star, 36.0, 0.0)),  # over the Star Bridge
        (star + 60.0, *over(star + 60.0, 70.0, -60.0)),
        (A("o2", 0.5), ox, oy, 210.0),  # round the observatory's rings
        (A("o3", 0.8), ox + 90.0, oy - 60.0, 180.0),
        (A("t2", 0.5), px - 60.0, py + 40.0, pz + 90.0),
        (A("v1", 0.6), *over(A("v1", 0.6), 40.0, 30.0)),  # down the causeway with the procession
        (A("v2", 0.6), -430.0, 130.0, 120.0),  # out over the lagoon, seen from the overlook
        (A("v3", 0.6), -300.0, 260.0, 180.0),
        (c.length - 90.0, px + 40.0, py - 110.0, pz + 90.0),
        (c.length - 1.0, 60.0, 60.0, 150.0),
    ]
    finale = keys[:-4] + [
        (A("v2", 0.5), px - 110.0, py - 60.0, pz + 60.0),  # round the palace's west side...
        (A("v3", 0.5), px - 10.0, py - 80.0, pz + 100.0),
        (S["f1"] + 30.0, px + 30.0, py + 10.0, pz + 150.0),  # the Dragon's Ascension above the palace...
        (c.length - 60.0, *over(c.length - 60.0, 60.0, 30.0)),  # ...and down over the finish
        (c.length - 1.0, 60.0, 60.0, 150.0),
    ]

    def conv(ks):
        out = []
        for s, x, y, z in ks:
            gx, gy, gz = c.game(x, y, z)
            out.append([round(s, 1), round(gx, 1), round(gy, 1), round(gz, 1)])
        return out

    c.entity("isles_dragon", keys=conv(keys), finale=conv(finale), length=round(c.length, 1), size=1.35,
             colors={"body": "#f0b830", "belly": "#fff0c0"})
    for ks in (keys, finale):
        for (s0, *a), (s1, *b) in zip(ks, ks[1:]):
            d = math.dist(a, b)
            t = max(0.5, (s1 - s0) / 24.0)
            if d / t > 70:
                print("dragon fast: %.0f m/s from s=%.0f" % (d / t, s0))


# ------------------------------------------------------------------ the festival


RED_GOLD = ["#ff3a3a", "#ffd050", "#ffe8a0"]
GOLD = ["#ffd060", "#ffb030", "#fff0b0"]
BLUE_GOLD = ["#5aa0ff", "#ffd050", "#e0f0ff"]
BLUE = ["#6ab4ff", "#bfe0ff", "#ffffff"]
PINK = ["#ff5ac8", "#ffb0e8", "#ffffff"]
VIOLET = ["#b07aff", "#5ac8ff", "#ffffff"]
RAINBOW = ["#ff3a3a", "#ffa030", "#ffe050", "#4aff9a", "#5aa0ff", "#b07aff"]


def festival(c, sc):
    """The fireworks (game/festival.ts): the city's launch sites, the lantern grounds, the
    observatory's rings, and the set pieces keyed to places round the lap."""
    g = c.game
    px, py = L.PALACE
    pz = getattr(sc, "palace_z", 100.0)
    ox, oy, oz = getattr(sc, "observatory", (L.PINNACLE[0], L.PINNACLE[1], L.PINNACLE_Z))
    ring_c = (ox, oy, oz + cp.OBSERVATORY_RINGS_Z)

    def G(x, y, z):
        return [round(v, 1) for v in g(x, y, z)]

    def viewer(s, up=2.0):
        q = c.at(s % c.length)
        return (q.p.x, q.p.y, q.p.z + up)

    def yaw_to(burst, eye):
        bx, by, bz = g(*burst)
        ex, ey, ez = g(*eye)
        return round(math.atan2(ex - bx, ez - bz), 3)

    def B(t, at, pattern, size, colors, frm=None, yaw=0.0, tilt=0.0):
        b = {"t": round(t, 2), "x": None, "y": None, "z": None, "pattern": pattern, "size": round(size, 1), "colors": colors}
        b["x"], b["y"], b["z"] = G(*at)
        if frm is not None:
            b["from"] = G(*frm)
        if yaw:
            b["yaw"] = yaw
        if tilt:
            b["tilt"] = round(tilt, 3)
        return b

    pieces = []

    def piece(pid, stages, at, bursts, cue=None):
        p = {"id": pid, "stages": stages, "at": round(at % c.length, 1), "bursts": bursts}
        if cue:
            p["cue"] = cue
        pieces.append(p)

    # Launch sites: the city, the islands, the palace, the far shores.
    sites = []
    for x, y, z in sc.launchers:
        sites.append(G(x, y, z))
    # A ring of barges and shore batteries round the mountain, out on the lagoon and in
    # the city, so the show is all round you wherever you are.
    for k in range(28):
        a = k * math.tau / 28 + 0.1
        for r in (430.0, 560.0):
            x, y = 70.0 + math.cos(a) * r, 230.0 + math.sin(a) * r * 0.95
            if not (L.GRID[0] < x < L.GRID[1] and L.GRID[2] < y < L.GRID[3]):
                continue
            z = sc.info(x, y)
            if z < 1.0 or L.city(x, y) > 0.5:
                sites.append(G(x, y, max(0.0, z)))
    # Districts, for the salutes: points round the skyline seen from the overlook.
    city = [(80.0, -150.0), (230.0, -170.0), (360.0, -140.0), (520.0, 40.0), (540.0, 220.0), (380.0, 420.0)]
    palace_up = (px, py, pz + 120.0)

    # ---- lap 1: the Opening Celebration (a beautiful beginning)
    piece("opening", [1], 8.0, [
        B(0.0, (px - 60, py, pz + 110), "peony", 34, RED_GOLD, frm=(px - 60, py, pz + 4)),
        B(0.6, (px + 60, py, pz + 120), "peony", 34, BLUE_GOLD, frm=(px + 60, py, pz + 4)),
        B(1.4, (px, py + 10, pz + 150), "chrysanthemum", 44, GOLD, frm=(px, py, pz + 4)),
    ], cue="gong")
    piece("promenade_1", [1], S["p1"] - 40.0, [
        B(0.0, (L.PLAZA[0] - 40, L.PLAZA[1] + 90, 120), "peony", 30, RED_GOLD, frm=(L.PLAZA[0] - 40, L.PLAZA[1] + 90, 10)),
        B(0.8, (L.PLAZA[0] + 40, L.PLAZA[1] + 90, 130), "glitter", 30, GOLD, frm=(L.PLAZA[0] + 40, L.PLAZA[1] + 90, 10)),
    ])
    piece("observatory_1", [1], S["o1"] - 60.0, [
        B(0.0, (ring_c[0], ring_c[1], ring_c[2] + 30), "ring", 40, BLUE, frm=(ox, oy, oz + 25), tilt=0.5),
    ])

    # ---- lap 2: the Ceremony Intensifies (higher energy)
    piece("ceremony", [2], 8.0, [
        B(0.0 + i * 0.35, (px - 90 + i * 30, py + (i % 2) * 20, pz + 110 + (i % 3) * 20), ("peony", "chrysanthemum", "glitter")[i % 3], 36,
          (RED_GOLD, BLUE_GOLD, GOLD, PINK)[i % 4], frm=(px - 90 + i * 30, py, pz + 4)) for i in range(7)
    ], cue="gong")
    piece("inlet_comets", [2], A("m3", 0.2), [
        B(0.0, (L.INLET[0] + 200, 300.0, 170.0), "comet", 10, GOLD, frm=(L.INLET[0] + 260, -60.0, 60.0)),
        B(0.4, (L.INLET[0] + 140, 320.0, 180.0), "comet", 10, GOLD, frm=(L.INLET[0] + 220, -80.0, 60.0)),
        B(1.6, (L.INLET[0] + 150, 120.0, 140.0), "willow", 40, GOLD, frm=(L.INLET[0] + 150, 120.0, 10.0)),
    ])
    eye = viewer(L.STAR[0] + 80)
    dpos = (ox + 10, oy - 10, oz + 120)
    piece("dragon_sketch", [2], L.STAR[0] + 10, [
        B(0.0, dpos, "dragon", 60, PINK, frm=(ox, oy, oz + 20), yaw=yaw_to(dpos, eye)),
    ], cue="roar")
    piece("rings_2", [2], S["o1"] - 40.0, [
        B(0.0 + i * 0.6, (ring_c[0], ring_c[1], ring_c[2] + 10 + i * 6), "ring", 44 + i * 8, (BLUE, BLUE_GOLD, GOLD)[i], frm=(ox, oy, oz + 25),
          tilt=0.3 + i * 0.5, yaw=round(i * 1.1, 2)) for i in range(3)
    ])
    piece("districts_2", [2], S["v2"] - 40.0, [
        B(0.2 * i, (x, y, 130 + 20 * (i % 2)), ("peony", "palm", "willow")[i % 3], 38, (RED_GOLD, GOLD, PINK, BLUE_GOLD)[i % 4],
          frm=(x, y, 10)) for i, (x, y) in enumerate(city)
    ])

    # ---- lap 3: the Grand Finale (the entire sky explodes), building all the way
    piece("salute", [3], 8.0, [
        B(0.18 * i, (x, y, 140 + 15 * (i % 2)), "peony", 40, (RED_GOLD, GOLD)[i % 2], frm=(x, y, 10)) for i, (x, y) in enumerate(city)
    ] + [B(1.8, palace_up, "chrysanthemum", 60, GOLD, frm=(px, py, pz + 4))], cue="gong")
    piece("golden_rain", [3], A("m3", 0.3), [
        B(0.3 * i, (px - 60 + i * 30, py + 20 * (i % 2), pz + 150), "willow", 56, GOLD, frm=(px - 60 + i * 30, py, pz + 4)) for i in range(5)
    ])
    piece("starfall", [3], S["p1"] + 20.0, [
        B(0.35 * i, (300 - i * 120, 700.0 - i * 20, 260 - i * 10), "comet", 12, (GOLD, BLUE_GOLD)[i % 2], frm=(700.0 - i * 40, 200.0 + i * 60, 300.0))
        for i in range(6)
    ])
    cpos = (60.0, 820.0, 330.0)
    piece("constellation", [3], S["c2"], [
        B(0.0, cpos, "constellation", 170, BLUE, yaw=yaw_to(cpos, viewer(S["c4"]))),
    ], cue="bells")
    # The signature moment: crossing the Star Bridge on the last lap, the dragon drawn in
    # gold over the observatory, ringed by its rings.
    eye = viewer(L.STAR_OPEN[0])
    dpos = (ox + 20, oy - 10, oz + 140)
    piece("star_bridge_dragon", [3], L.STAR[0] + 10, [
        B(0.0, dpos, "dragon", 92, GOLD, frm=(ox, oy, oz + 20), yaw=yaw_to(dpos, eye)),
        B(0.9, (dpos[0], dpos[1], dpos[2] + 10), "ring", 120, BLUE_GOLD, frm=(ox, oy, oz + 20), yaw=yaw_to(dpos, eye)),
        B(1.6, (ox - 80, oy + 40, oz + 100), "willow", 40, GOLD, frm=(ox - 80, oy + 40, 10)),
        B(1.8, (ox + 100, oy + 30, oz + 110), "willow", 40, GOLD, frm=(ox + 100, oy + 30, 10)),
    ], cue="roar")
    piece("celestial_rings", [3], A("o2", 0.0), [
        B(0.5 * i, (ring_c[0], ring_c[1], ring_c[2] + 5 * i), "ring", 50 + i * 14, (BLUE_GOLD, GOLD, BLUE, GOLD)[i], frm=(ox, oy, oz + 25),
          tilt=0.25 + i * 0.45, yaw=round(i * 0.8, 2)) for i in range(4)
    ])
    piece("palace_salute", [3], A("t1", 0.2), [
        B(0.25 * i, (px - 70 + i * 28, py - 30 + 20 * (i % 2), pz + 130 + 10 * (i % 3)), ("chrysanthemum", "glitter", "star")[i % 3], 46,
          (GOLD, RED_GOLD, PINK, BLUE_GOLD)[i % 4], frm=(px - 70 + i * 28, py, pz + 4)) for i in range(6)
    ])
    piece("panorama", [3], S["v2"] - 30.0, [
        B(0.15 * i, (x, y, 150 + 20 * (i % 3)), ("willow", "peony", "palm", "ring", "chrysanthemum")[i % 5], 50,
          (GOLD, RED_GOLD, PINK, BLUE_GOLD, RAINBOW)[i % 5], frm=(x, y, 10)) for i, (x, y) in enumerate(city * 2)
    ], cue="cheer")
    eye = viewer(A("v3", 0.5))
    apos = (px, py - 20, pz + 170)
    piece("ascension", [3], A("v3", 0.0), [
        B(0.0, apos, "dragon", 80, RED_GOLD, frm=(px, py, pz + 4), yaw=yaw_to(apos, eye)),
        B(0.8, (px - 60, py, pz + 140), "willow", 60, GOLD, frm=(px - 60, py, pz + 4)),
        B(1.0, (px + 60, py, pz + 140), "willow", 60, GOLD, frm=(px + 60, py, pz + 4)),
    ], cue="roar")
    # The grand finale over the finish: wave after wave, the dragon, golden rain, rings.
    s_fin = c.length - 190.0
    eye = viewer(c.length - 40.0)
    fpos = (170.0, 70.0, 150.0)
    fin = [B(0.0, fpos, "dragon", 100, GOLD, frm=(170.0, 70.0, 20.0), yaw=yaw_to(fpos, eye)),
           B(0.4, (px, py, pz + 160), "ring", 110, BLUE_GOLD, frm=(px, py, pz + 4), yaw=yaw_to((px, py, pz + 160), eye)),
           B(1.6, (300.0, -140.0, 170.0), "constellation", 120, BLUE, yaw=yaw_to((300.0, -140.0, 170.0), eye))]
    for i in range(18):
        x = 0 + (i % 9) * 45.0
        y = -40.0 + (i // 9) * 110.0 + 30 * rnd(i)
        fin.append(B(0.3 + 0.22 * i, (x, y, 130 + 40 * rnd(i * 3)), ("peony", "chrysanthemum", "willow", "glitter", "palm", "star")[i % 6],
                     60 + 22 * rnd(i * 5), (GOLD, RED_GOLD, PINK, BLUE_GOLD, RAINBOW, VIOLET)[i % 6], frm=(x, y - 60.0, 10.0)))
    for i in range(8):
        fin.append(B(4.6 + 0.12 * i, (px - 90 + i * 26, py + 10, pz + 150), "willow", 80, GOLD, frm=(px - 90 + i * 26, py, pz + 4)))
    piece("grand_finale", [3], s_fin, fin, cue="finale")

    lanterns = [G(150.0, -140.0, 10.0) + [140.0], G(L.PLAZA[0], L.PLAZA[1] + 40, 12.0) + [90.0], G(px, py, pz + 4.0) + [80.0],
                G(L.INLET[0] + 110, 120.0, 0.0) + [110.0], G(-420.0, 200.0, 0.0) + [140.0], G(-60.0, -120.0, 8.0) + [120.0]]
    c.entity("festival", length=round(c.length, 1), sites=sites, pieces=pieces, lanterns=lanterns,
             observatory=G(*ring_c) + [34.0])
    print("festival: sites %d, pieces %d" % (len(sites), len(pieces)))


# ------------------------------------------------------------------ the air

ZONES = {  # the air and sound of each part (game/depths.ts' atmosphere)
    "gate": {"fog": "#2c2a6a", "near": 420, "far": 2600, "sun": 1.75, "sky": "#9a9af0", "ground": "#4a3a78", "hemi": 1.6, "sound": "festival"},
    "market": {"fog": "#2e2a66", "near": 380, "far": 2500, "sun": 1.7, "sky": "#a29af0", "ground": "#5a3a70", "hemi": 1.6, "sound": "festival"},
    "falls": {"fog": "#262c6a", "near": 420, "far": 2600, "sun": 1.75, "sky": "#9aa4f4", "ground": "#3a4a78", "hemi": 1.6, "sound": "falls"},
    "promenade": {"fog": "#2e2a6a", "near": 420, "far": 2600, "sun": 1.7, "sky": "#a49af0", "ground": "#5a3a6a", "hemi": 1.6, "sound": "festival"},
    "climb": {"fog": "#24286a", "near": 460, "far": 2800, "sun": 1.8, "sky": "#9aa0f4", "ground": "#3a3a78", "hemi": 1.55, "sound": "garden"},
    "star": {"fog": "#1e2466", "near": 520, "far": 3000, "sun": 1.85, "sky": "#9aa6ff", "ground": "#3a3a80", "hemi": 1.5, "sound": "wind"},
    "observatory": {"fog": "#1e2466", "near": 520, "far": 3000, "sun": 1.85, "sky": "#9aa6ff", "ground": "#3a3a80", "hemi": 1.55,
                    "sound": "wind"},
    "terraces": {"fog": "#2a2a6a", "near": 440, "far": 2700, "sun": 1.75, "sky": "#a29af0", "ground": "#4a3a70", "hemi": 1.6, "sound": "garden"},
    "causeway": {"fog": "#2e2a66", "near": 420, "far": 2600, "sun": 1.7, "sky": "#a49af0", "ground": "#5a3a6a", "hemi": 1.6, "sound": "festival"},
    "overlook": {"fog": "#24286a", "near": 520, "far": 3000, "sun": 1.8, "sky": "#9aa4f4", "ground": "#3a3a78", "hemi": 1.55, "sound": "wind"},
}
ZONE_OF = {"gate": "gate", "market": "market", "falls": "falls", "promenade": "promenade", "climb": "climb", "star": "star",
           "observatory": "observatory", "terraces": "terraces", "causeway": "causeway", "overlook": "overlook", "ascension": "causeway",
           "finale": "gate"}


def atmosphere(c, sc):
    keys = []
    blend = 24.0

    def zone(s):
        return ZONE_OF[L.zone_of(s % c.length)]

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
    c.entity("atmosphere", zones=ZONES, keys=keys)


# ------------------------------------------------------------------ build


def build(c, sc):
    palace(c, sc)
    gate(c, sc)
    market(c, sc)
    waterfront(c, sc)
    promenade(c, sc)
    climb(c, sc)
    star_bridge(c, sc)
    observatory(c, sc)
    terraces(c, sc)
    causeway(c, sc)
    overlook(c, sc)
    ascension(c, sc)
    islands_temples(c, sc)
    city_south(c, sc)
    mountain(c, sc)


def entities(c, sc):
    dragon(c, sc)
    c.entity("villagers", list=sc.crowd)
    print("villagers:", len(sc.crowd))
    festival(c, sc)
    atmosphere(c, sc)
    for kind, col, step in (("lantern", "#ffb060", 3), ("gold", "#ffd880", 1), ("star", "#a8c8ff", 2), ("fire", "#ff9040", 1)):
        for x, y, z in sc.lights.get(kind, [])[::step]:
            game_entity(c, "glow", x, y, z, color=col)
    print("glows:", {k: len(v) for k, v in sc.lights.items()})
