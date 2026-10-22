# Dragon Canyon's frontier (see dragon_canyon.py): the Canyon Outpost and its Dragon
# Gate, the hairpins' turn boards and braziers, the Canyon Bridge, the dragon's bones,
# the Imperial Quarry, the caverns' torches and sealed chambers, the Lone Spire, the
# Hidden Oasis, the watchtower, the Dragon's Coil; the far spires; the people, the
# cranes, the birds, the dust and the great dragon's flight (for the game).
# SPDX-License-Identifier: MIT

import math

import dcanyon_land as L
import dcanyon_props as dp
import isles_props as ip
import props
from course_kit import rnd
from dcanyon_scenery import clear, game_entity
from isles_town import crowd_along, fwd, put, roadside, villager


def q_w(c, s):
    return c.at(s % c.length).w


def corner_centre(name):
    """The centre of a corner's arc (and its radius)."""
    i = L.NAMES.index(name)
    p0, p1, p2 = L.CORNERS[i - 1], L.CORNERS[i], L.CORNERS[(i + 1) % len(L.CORNERS)]
    ux, uy = p1[0] - p0[0], p1[1] - p0[1]
    vx, vy = p2[0] - p1[0], p2[1] - p1[1]
    lu, lv = math.hypot(ux, uy), math.hypot(vx, vy)
    ux, uy, vx, vy = ux / lu, uy / lu, vx / lv, vy / lv
    bx, by = vx - ux, vy - uy
    lb = math.hypot(bx, by) or 1.0
    th = math.acos(max(-1.0, min(1.0, ux * vx + uy * vy)))
    r = p1[2]
    d = r / math.cos(th / 2) if th < math.pi - 1e-3 else r
    return p1[0] + bx / lb * d, p1[1] + by / lb * d, r


def outside(c, s, off_extra=6.0):
    """The point beyond the outside edge of the turn at lap distance s, and the turn
    that faces a prop there toward the road (+1: right of the road is outside)."""
    q = c.at(s % c.length)
    a = c.at((s - 6) % c.length).t
    b = c.at((s + 6) % c.length).t
    turn = a.x * b.y - a.y * b.x  # > 0 turning left: the outside is the right
    side = 1 if turn > 0 else -1
    p = q.side(side * (q.w / 2 + off_extra))
    return p, ip.facing(p.x, p.y, q.p.x, q.p.y), q


def braziers(c, sc, s0, s1, every, off=2.2, sides=(-1, 1)):
    s = s0
    while s < s1:
        for side in sides:
            q = c.at(s % c.length)
            p = q.side(side * (q.w / 2 + off))
            if clear(c, p.x, p.y, 1.2) and sc.free(p.x, p.y, 1.0):
                sc.put(dp.brazier(c), p.x, p.y, sc.ground(p.x, p.y) - 0.2, 0.0, 1.0, role="both")
                sc.light("fire", p.x, p.y, p.z + 2.4)
                sc.footprints.append((p.x, p.y, 1.0))
        s += every


def chevrons(c, sc, s):
    """A turn board on the outside of the corner at s, its arrows pointing round it."""
    p, rot, q = outside(c, s, 3.6)
    t = c.at(s % c.length).t
    sc.put(dp.chevron_board(c, 9.0), p.x, p.y, sc.ground(p.x, p.y), math.atan2(t.y, t.x), 1.0, role="visual")


def banners(c, sc, s0, s1, every, off=3.0, mat="banner_royal"):
    s = s0
    k = 0
    while s < s1:
        side = 1 if k % 2 else -1
        x, y, rot, q = roadside(c, s, side * (q_w(c, s) / 2 + off))
        if clear(c, x, y, 1.5) and sc.free(x, y, 1.5):
            put(sc, ip.banner_pole(c, mat), x, y, rot, role="both")
            sc.footprints.append((x, y, 1.0))
        s += every
        k += 1


# ------------------------------------------------------------------ 1  the Canyon Outpost, 12 the Dragon Gate


def outpost(c, sc):
    q = c.at(24.0)
    put(sc, ip.gate(c, 24.0, 14.0, "roof_jade", grand=True), q.p.x, q.p.y, math.atan2(q.t.y, q.t.x) - math.pi / 2, coll="Landmarks",
        role="both", z=q.p.z)
    for s in (-14.0, 40.0):
        for side in (-1, 1):
            x, y, rot, q2 = roadside(c, s, side * (q_w(c, s) / 2 + 6.5))
            sc.put(ip.dragon_statue(c, "stone_base" if s > 0 else "jade_stone"), x, y, sc.ground(x, y), rot, 1.6, coll="Landmarks", role="both")
            sc.footprints.append((x, y, 5.0))
    # The fortress over the start: walls along the west side, towers, guards on top.
    for k, y in enumerate(range(-80, 60, 18)):
        x = -26.0 - 3.0 * math.sin(y / 30.0)
        if clear(c, x, y, 4.0):
            put(sc, dp.fort_wall(c, 18.0, 9.0), x, y, math.pi / 2, coll="Landmarks", role="both", sink=1.0)
            sc.footprints.append((x, y, 9.0))
            if k % 2 == 0:
                villager(c, sc, x + 1.2, y, "guard", x + 30, y, z=sc.ground(x, y) + 8.0)
    for x, y in ((-30.0, -88.0), (-30.0, 66.0), (-55.0, -10.0)):
        if clear(c, x, y, 6.0):
            put(sc, dp.fort_tower(c, 18.0, 8.0, "roof_blue"), x, y, 0.0, coll="Landmarks", role="both", sink=1.0)
            sc.footprints.append((x, y, 7.0))
    braziers(c, sc, -80.0, 60.0, 16.0, off=2.6)
    banners(c, sc, -70.0, 60.0, 11.0, off=5.0)
    # Workers and a caravan on the east side, guards at the gate.
    for i, s in enumerate((-40.0, -25.0, 50.0)):
        x, y, rot, q2 = roadside(c, s, q_w(c, s) / 2 + 12.0)
        if clear(c, x, y, 4.0):
            put(sc, dp.cart(c, i), x, y, rot + math.pi / 2, coll="Quarry", role="both")
            sc.footprints.append((x, y, 3.5))
            villager(c, sc, x + 2.5, y + 1.0, "hauler", x + 10, y + 1.0)
    for side in (-1, 1):
        x, y, rot, q2 = roadside(c, 24.0, side * (q_w(c, 24.0) / 2 + 3.0))
        villager(c, sc, x, y, "guard", q2.p.x, q2.p.y)
    crowd_along(c, sc, -60.0, 70.0, 11.0, 15.0, 7.0, role="cheer", sides=(1,), chance=0.55)


# ------------------------------------------------------------------ 2  the Cliffside Hairpins, 3 the descent


def hairpins(c, sc):
    for name in ("h1a", "h1b", "h2a", "h2b", "c1"):
        chevrons(c, sc, L.at(name, 0.5 if name == "c1" else 0.7))
    # Braziers round the outside of each hairpin; temples and lookouts on the terraces.
    for name in ("h1a", "h2a"):
        cx, cy, r = corner_centre(name)
        nxt = L.NAMES[L.NAMES.index(name) + 1]
        c2x, c2y, _ = corner_centre(nxt)
        mx, my = (cx + c2x) / 2, (cy + c2y) / 2
        for k in range(7):
            a = -math.pi / 2 + k * math.pi / 6
            d = 1 if name == "h1a" else -1
            x, y = mx + d * math.cos(a) * (r + 12.0), my + math.sin(a) * (r + 12.0)
            if clear(c, x, y, 1.5) and sc.free(x, y, 1.0):
                sc.put(dp.brazier(c), x, y, sc.ground(x, y) - 0.2, 0.0, 1.0, role="both")
                sc.light("fire", x, y, sc.ground(x, y) + 2.4)
    for x, y, proto in ((44.0, 66.0, ip.pavilion(c, 7.0, "roof_jade")), (52.0, 118.0, ip.pagoda(c, 3, 6.0, "roof_blue")),
                        (-28.0, 116.0, dp.fort_tower(c, 14.0, 6.0, "roof_jade"))):
        if clear(c, x, y, 4.0) and sc.free(x, y, 5.0):
            put(sc, proto, x, y, ip.facing(x, y, 40, 90), coll="Landmarks", role="both", sink=0.5)
            sc.footprints.append((x, y, 5.0))
    banners(c, sc, L.at("c1", 0.5), L.S["n1"], 24.0, off=3.0)
    # The descent: the Canyon Bridge's banners, a lookout over the falls.
    banners(c, sc, L.S["n2"], L.S["n3"], 20.0, off=0.6)
    for name in ("n1", "n2", "n3", "k1"):
        chevrons(c, sc, L.at(name, 0.6))
    x, y = 70.0, 214.0
    if clear(c, x, y, 5.0):
        put(sc, ip.pavilion(c, 6.0, "roof_blue"), x, y, ip.facing(x, y, 150, 260), coll="Landmarks", role="both")


# ------------------------------------------------------------------ 4  Dragon Skeleton Pass


def skeleton(c, sc):
    sx, sy = L.SKULL
    put(sc, dp.skull(c), sx, sy, ip.facing(sx, sy, 240, 120), 1.0, coll="Landmarks", role="both", sink=3.0)
    sc.footprints.append((sx, sy, 22.0))
    # Ribs arching over the road through the S-bends.
    s = L.S["k1"] - 6.0
    k = 0
    while s < L.at("k3", 0.7):
        q = c.at(s)
        span = q.w + 10.0
        rot = math.atan2(q.t.y, q.t.x) - math.pi / 2
        put(sc, dp.rib(c, span, 15.0 - 2.0 * (k % 2), k % 3), q.p.x, q.p.y, rot, coll="Landmarks", role="both", z=q.p.z - 0.5)
        s += 16.0
        k += 1
    # The spine running off along the east wall, a few vertebrae by the road.
    for i in range(8):
        t = i / 7
        x, y = 300.0 - 6 * t, 96.0 - 60.0 * t
        if clear(c, x, y, 4.0):
            sc.put(dp.vertebra(c), x, y, sc.ground(x, y) - 0.5, 0.3 * i, 1.2 - 0.06 * i, coll="Landmarks", role="both")
    banners(c, sc, L.S["k1"], L.at("k3", 0.8), 26.0, off=4.5, mat="banner_royal")
    for name in ("k1", "k2", "k3"):
        chevrons(c, sc, L.at(name, 0.5))


# ------------------------------------------------------------------ 5  the Imperial Quarry


def quarry(c, sc):
    cranes = [(324.0, 40.0, math.pi * 0.75), (336.0, -10.0, math.pi * 1.05), (322.0, 92.0, math.pi * 0.6), (300.0, -40.0, math.pi * 1.3)]
    for x, y, rot in cranes:
        if not clear(c, x, y, 6.0):
            continue
        put(sc, dp.crane(c), x, y, rot, coll="Quarry", role="both")
        sc.footprints.append((x, y, 5.0))
        tx, ty, tz = dp.CRANE_TIP
        gz = sc.ground(x, y)
        cx, cy = x - math.sin(rot) * ty, y + math.cos(rot) * ty
        game_entity(c, "crane", x, y, gz + tz, heading=round(-rot, 3), reach=ty, drop=round(tz - 1.5, 1), swing=0.5,
                    period=round(9.0 + 3.0 * rnd(x), 1))
    for i in range(16):
        x = 248 + rnd(i * 3.1) * 110
        y = -40 + rnd(i * 5.7) * 110
        if clear(c, x, y, 5.0) and sc.free(x, y, 4.0):
            put(sc, dp.block_stack(c, i % 4), x, y, rnd(i) * 3.0, coll="Quarry", role="both")
            sc.footprints.append((x, y, 4.0))
    for i in range(6):
        x = 250 + rnd(i * 7.3) * 100
        y = -30 + rnd(i * 2.3) * 100
        if clear(c, x, y, 4.0) and sc.free(x, y, 3.0):
            put(sc, dp.tent(c, i % 3) if i % 2 else dp.cart(c, i), x, y, rnd(i * 3) * 6.28, coll="Quarry", role="both")
            sc.footprints.append((x, y, 3.0))
    # Scaffolds and a cargo lift on the cliffs round the yard; the guarded mine door.
    for x, y, rot in ((346.0, 60.0, -math.pi / 2), (350.0, 10.0, -math.pi / 2), (338.0, -40.0, -math.pi * 0.6)):
        if sc.free(x, y, 5):
            put(sc, dp.scaffold(c, 12.0, 15.0), x, y, rot + math.pi / 2, coll="Quarry", role="visual")
    put(sc, dp.lift(c, 26.0), 352.0, 32.0, math.pi / 2, coll="Quarry", role="visual")
    put(sc, dp.chamber_door(c), 344.0, -22.0, math.pi / 2 + 0.3, coll="Quarry", role="both")
    sc.light("glow", 342.0, -22.0, sc.ground(344, -22) + 2.5)
    villager(c, sc, 340.0, -16.0, "guard", 300.0, -16.0)
    villager(c, sc, 340.0, -28.0, "guard", 300.0, -28.0)
    put(sc, dp.fort_tower(c, 16.0, 6.0, "roof_blue"), 330.0, 74.0, 0.0, coll="Quarry", role="both")
    villager(c, sc, 330.0, 74.0, "guard", 290.0, 30.0, z=sc.ground(330, 74) + 16.6)
    # The workers: hewing, hauling, pushing carts; guards watching.
    k = 0
    for i in range(44):
        x = 250 + rnd(i * 4.9 + 1) * 110
        y = -40 + rnd(i * 6.3 + 2) * 115
        if not clear(c, x, y, 3.0) or not sc.free(x, y, 1.0):
            continue
        role = "worker" if k % 3 else "hauler"
        if k % 7 == 6:
            role = "guard"
        face = (x + math.cos(i) * 5, y + math.sin(i) * 5)
        villager(c, sc, x, y, role, *face)
        k += 1
    # The Service Road's arch.
    pts = L.SERVICE
    p0, p1 = pts[6], pts[9]
    put(sc, ip.gate(c, 12.0, 9.0, "roof_blue", grand=False), p0[0], p0[1], math.atan2(p1[1] - p0[1], p1[0] - p0[0]) - math.pi / 2,
        coll="Landmarks", role="both", z=p0[2])
    braziers(c, sc, L.S["q1"], L.at("q2", 0.5), 18.0, off=2.6, sides=(1,))
    for name in ("q1", "q2"):
        chevrons(c, sc, L.at(name, 0.5))


# ------------------------------------------------------------------ 6  the Winding Caverns


def caverns(c, sc):
    t0, t1 = sc.tunnel
    s = t0 + 16.0
    k = 0
    while s < t1 - 14.0:
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 2.4))
            rot = ip.facing(p.x, p.y, q.p.x, q.p.y) + math.pi  # the torch points out along -Y
            sc.put(props.torch(c), p.x, p.y, q.p.z + 3.4, rot, 1.2, coll="Props", role="visual")
            sc.light("fire", p.x, p.y, q.p.z + 4.4)
        if k % 2 == 1:
            side = 1 if k % 4 == 1 else -1
            p = q.side(side * (q.w / 2 + 2.0))
            sc.put(dp.chamber_door(c), p.x, p.y, q.p.z - 0.3, ip.facing(p.x, p.y, q.p.x, q.p.y), 0.9, coll="Landmarks", role="visual")
            sc.light("glow", p.x, p.y, q.p.z + 2.5)
        s += 18.0
        k += 1
    q = c.at(t0 + 10.0)
    sc.put(ip.emblem_plaque(c), q.p.x, q.p.y, q.p.z + 12.0, math.atan2(q.t.y, q.t.x) - math.pi / 2 + math.pi, 1.6, coll="Landmarks",
           role="visual")
    game_entity(c, "motes", q.p.x, q.p.y, q.p.z + 4.0, radius=40.0, rate=5.0, color="#ffb060", rise=0.1, size=0.18, blink=True)


# ------------------------------------------------------------------ 7  the High Bridges, 9 the river


def bridges(c, sc):
    def on_a_road(x, y, bottom):
        """A pier standing on a road below (the River Sprint under the High Bridges)."""
        for q in c.S[::2]:
            if q.p.z < bottom + 14.0 and (q.p.x - x) ** 2 + (q.p.y - y) ** 2 < (q.w / 2 + 4.0) ** 2:
                return True
        return False

    for piece in c.pieces:
        if piece.name.split()[-1] == "bridge":
            props.piers(c, piece, every=22.0, mat=("fortress_wall", "wall"), size=2.4, terrain=sc.ground_obs, inset=2.4, avoid=on_a_road)
    sx, sy = L.SPIRE
    sc.put(dp.spire(c, 1, 80.0), sx, sy, L.BED, 0.4, 1.0, coll="Landmarks", role="both")
    sc.footprints.append((sx, sy, 15.0))
    banners(c, sc, L.S["b1"], L.at("b2", 0.9), 18.0, off=0.6)
    for name in ("t1", "b1", "b2", "o1"):
        chevrons(c, sc, L.at(name, 0.5))
    # An old aqueduct high over the River Sprint.
    q = c.at(L.at("r2", 0.6))
    gz = q.p.z
    put(sc, dp.aqueduct(c, 60.0, 34.0), q.p.x, q.p.y, math.atan2(q.t.y, q.t.x) - math.pi / 2, coll="Landmarks", role="visual", z=gz + 32.0)
    braziers(c, sc, L.S["r1"], L.S["w0"], 30.0, off=2.6, sides=(-1,))


# ------------------------------------------------------------------ 8  the Hidden Oasis


def oasis(c, sc):
    ox, oy = L.OASIS
    for i in range(22):
        a = i * math.tau / 22 + rnd(i) * 0.2
        r = L.OASIS_R + 4.0 + rnd(i * 3) * 6.0
        x, y = ox + math.cos(a) * r, oy + math.sin(a) * r
        if clear(c, x, y, 3.0) and sc.free(x, y, 1.5):
            put(sc, props.palm(c, 8.0 + rnd(i) * 3.0, 1.0 + rnd(i * 5) * 1.6, i % 4), x, y, a + math.pi, coll="Plants", role="both", sink=0.3)
            sc.footprints.append((x, y, 1.2))
    for i, (dx, dy) in enumerate(((-6.0, 40.0), (14.0, 44.0), (34.0, 36.0), (-30.0, 12.0))):
        x, y = ox + dx, oy + dy
        if clear(c, x, y, 5.0) and sc.free(x, y, 5.0):
            put(sc, ip.house(c, 1 + i % 3 * 2), x, y, ip.facing(x, y, ox, oy), coll="Oasis", role="both")
            sc.footprints.append((x, y, 6.0))
    for i, (dx, dy) in enumerate(((0.0, -38.0), (22.0, -30.0))):
        x, y = ox + dx, oy + dy
        if clear(c, x, y, 3.0) and sc.free(x, y, 3.0):
            put(sc, ip.stall(c, i), x, y, ip.facing(x, y, ox, oy), coll="Oasis", role="both")
            villager(c, sc, x, y + 1.5, "merchant", ox, oy)
    for i in range(10):
        a = i * math.tau / 10 + 0.3
        x, y = ox + math.cos(a) * (L.OASIS_R + 2.0), oy + math.sin(a) * (L.OASIS_R + 2.0)
        if clear(c, x, y, 2.0):
            villager(c, sc, x, y, ("fisher", "gardener", "wave", "merchant")[i % 4], ox, oy)
    wx, wy = ox - L.OASIS_R + 2.0, oy - 4.0
    gx, gy, gz = c.game(wx, wy, 9.6)
    c.entity("waterwheel", x=round(gx, 2), y=round(gy, 2), z=round(gz, 2), heading=0.0, radius=3.0, speed=0.6)
    put(sc, ip.waterwheel_house(c), wx - 6.0, wy, 0.0, coll="Oasis", role="both")
    game_entity(c, "birds", ox, oy, 40.0, radius=50, count=5, speed=0.22, seed=21, color="#ffffff")
    for name in ("o2", "o3"):
        chevrons(c, sc, L.at(name, 0.5))


# ------------------------------------------------------------------ 10 the watchtower, 11 the Final Twist


def watchtower(c, sc):
    tx, ty = L.TOWER
    put(sc, dp.watchtower(c), tx, ty, 0.0, coll="Landmarks", role="both", sink=1.0)
    sc.footprints.append((tx, ty, 9.0))
    gz = sc.ground(tx, ty)
    for k in range(6):
        a = k * math.tau / 6
        villager(c, sc, tx + math.cos(a) * 5.0, ty + math.sin(a) * 5.0, "guard", tx + math.cos(a) * 30, ty + math.sin(a) * 30, z=gz + 21.8)
    for name in ("w0", "w1a", "w1b", "w2a", "w2b"):
        chevrons(c, sc, L.at(name, 0.6))
    banners(c, sc, L.S["w0"], L.S["x1"], 22.0, off=3.0)
    braziers(c, sc, L.S["w1a"], L.S["x1"], 24.0, off=2.4)


def twist(c, sc):
    for name in ("x1", "x2", "x3", "x4a", "x4b", "x5"):
        chevrons(c, sc, L.at(name, 0.55))
    cx, cy, r = corner_centre("x4a")
    put(sc, ip.dragon_statue(c, "jade_stone"), cx, cy, ip.facing(cx, cy, cx + 30, cy), 2.6, coll="Landmarks", role="both")
    sc.footprints.append((cx, cy, 9.0))
    braziers(c, sc, L.S["x1"], L.at("x5", 0.8), 20.0, off=2.4)
    banners(c, sc, L.S["x3"], L.at("x5", 0.8), 26.0, off=3.5)


# ------------------------------------------------------------------ the canyon round it all


def scenery(c, sc):
    """Spires and buttes in the gaps, and out to the horizon."""
    k = 0
    for i in range(140):
        x = L.GRID[0] + rnd(i * 3.3) * (L.GRID[1] - L.GRID[0])
        y = L.GRID[2] + rnd(i * 7.7) * (L.GRID[3] - L.GRID[2])
        if not clear(c, x, y, 30.0) or not sc.free(x, y, 14.0) or L.river_d(x, y) < 20:
            continue
        h = 40.0 + rnd(i * 2.2) * 50.0
        sc.put(dp.spire(c, k % 5, 60.0), x, y, sc.ground(x, y) - 2.0, rnd(i) * 6.28, h / 60.0, coll="Rocks Small", role="both")
        sc.footprints.append((x, y, h / 6.0))
        k += 1
    for i in range(70):
        a = rnd(i * 1.9) * math.tau
        r = 600.0 + rnd(i * 4.1) * 1600.0
        x, y = 100.0 + math.cos(a) * r, 0.0 + math.sin(a) * r
        if L.GRID[0] - 80 < x < L.GRID[1] + 80 and L.GRID[2] - 80 < y < L.GRID[3] + 80:
            continue
        proto = dp.butte(c, i % 3) if i % 3 == 0 else dp.spire(c, i % 5, 60.0)
        sc_ = (1.2 + rnd(i) * 1.6) if i % 3 == 0 else (1.6 + rnd(i * 3) * 2.2)
        sc.put(proto, x, y, L.RIM - 30.0, rnd(i) * 6.28, sc_, coll="Far Rocks", role="visual")


# ------------------------------------------------------------------ the dragon's flight


def dragon(c, sc):
    """The great dragon's keys: (lap distance, x, y, z). Majestic, but here it watches:
    it glides low over the watchtower, its shadow across the road."""
    def over(s, up):
        q = c.at(s % c.length)
        return (q.p.x, q.p.y, q.p.z + up)

    wx, wy, wz = over(L.at("w2a", 0.5), 0.0)
    keys = [
        (0.0, -120.0, 120.0, 130.0),  # over the fortress as the race starts
        (L.S["h1a"], 60.0, 260.0, 140.0),
        (L.at("n2", 0.3), 150.0, 300.0, 110.0),  # over the Great Falls as you cross the bridge
        (L.S["k1"], 330.0, 230.0, 120.0),
        (L.S["q1"], 380.0, 60.0, 110.0),  # watching the quarry
        (L.S["t1"], 360.0, -100.0, 120.0),
        (L.S["o1"], 200.0, -280.0, 110.0),
        (L.S["r1"], 160.0, -300.0, 90.0),
        (L.S["w0"], 240.0, -60.0, 80.0),
        (L.at("w1b", 0.5), wx + 50.0, wy + 20.0, wz + 40.0),
        (L.at("w2a", 0.5), wx, wy, wz + 22.0),  # low over the watchtower: its shadow on you
        (L.at("x1", 0.5), wx - 60.0, wy - 20.0, wz + 34.0),
        (L.S["x4a"], -160.0, -80.0, 100.0),
        (c.length - 1.0, -130.0, 100.0, 128.0),
    ]
    out = []
    for s, x, y, z in keys:
        gx, gy, gz = c.game(x, y, z)
        out.append([round(s, 1), round(gx, 1), round(gy, 1), round(gz, 1)])
    c.entity("isles_dragon", keys=out, length=round(c.length, 1), size=1.0)
    for (s0, *a), (s1, *b) in zip(keys, keys[1:]):
        d = math.dist(a, b)
        t = max(0.5, (s1 - s0) / 22.0)
        if d / t > 70:
            print("dragon fast: %.0f m/s from s=%.0f" % (d / t, s0))


# ------------------------------------------------------------------ the air


ZONES = {
    "outpost": {"fog": "#f0a47c", "near": 420, "far": 2300, "sun": 2.6, "sky": "#f4b494", "ground": "#8a4630", "hemi": 1.2, "sound": "wind"},
    "canyon": {"fog": "#ec9c78", "near": 380, "far": 2100, "sun": 2.5, "sky": "#f0aa90", "ground": "#82402c", "hemi": 1.15, "sound": "wind"},
    "falls": {"fog": "#e8a488", "near": 360, "far": 2000, "sun": 2.4, "sky": "#e8b0a0", "ground": "#7a4430", "hemi": 1.15, "sound": "falls"},
    "quarry": {"fog": "#e8a880", "near": 340, "far": 1900, "sun": 2.5, "sky": "#f0b090", "ground": "#8a5034", "hemi": 1.2, "sound": "quarry"},
    "caverns": {"fog": "#3a2418", "near": 40, "far": 380, "sun": 0.55, "sky": "#e0a070", "ground": "#3a2016", "hemi": 0.95, "sound": "drip"},
    "oasis": {"fog": "#f0b090", "near": 400, "far": 2200, "sun": 2.5, "sky": "#f0c0a0", "ground": "#6a6a3a", "hemi": 1.25, "sound": "garden"},
    "river": {"fog": "#e4a08c", "near": 360, "far": 2000, "sun": 2.3, "sky": "#e8b4a8", "ground": "#6a4a3a", "hemi": 1.15, "sound": "falls"},
}
ZONE_OF = {"outpost": "outpost", "hairpins": "canyon", "descent": "falls", "skeleton": "canyon", "quarry": "quarry",
           "caverns": "caverns", "bridges": "canyon", "oasis": "oasis", "river": "river", "watchtower": "canyon", "twist": "canyon"}


def atmosphere(c, sc):
    keys = []
    blend = 22.0
    t0, t1 = sc.tunnel

    def zone(s):
        s %= c.length
        if t0 <= s <= t1:
            return "caverns"
        z = ZONE_OF[L.zone_of(s)]
        return "quarry" if z == "caverns" else z

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
        s += 10.0
    for p in L.SERVICE[::6]:
        x, y, z = c.game(*p)
        keys.append([round(x, 1), round(y, 1), round(z, 1), "quarry", "quarry", 0.0])
    c.entity("atmosphere", zones=ZONES, keys=keys)


# ------------------------------------------------------------------ build


def build(c, sc):
    outpost(c, sc)
    hairpins(c, sc)
    skeleton(c, sc)
    quarry(c, sc)
    caverns(c, sc)
    bridges(c, sc)
    oasis(c, sc)
    watchtower(c, sc)
    twist(c, sc)
    scenery(c, sc)


def entities(c, sc):
    dragon(c, sc)
    c.entity("villagers", list=sc.crowd)
    print("villagers:", len(sc.crowd))
    atmosphere(c, sc)
    c.entity("dust", color="#d8945e", rate=1.0)
    c.entity("dustwind", rate=10, radius=60, color="#e8a878")
    game_entity(c, "birds", 150.0, 60.0, 110.0, radius=140, count=5, speed=0.14, seed=5, color="#2a1c18")
    game_entity(c, "birds", -60.0, -40.0, 95.0, radius=90, count=4, speed=0.18, seed=9, color="#2a1c18")
    game_entity(c, "little_dragons", 300.0, 115.0, 70.0, radius=60.0, count=2, speed=0.22, seed=3)
    for kind, col, step in (("fire", "#ff9a40", 5), ("glow", "#ffaa50", 1)):
        for x, y, z in sc.lights.get(kind, [])[::step]:
            game_entity(c, "glow", x, y, z, color=col)
