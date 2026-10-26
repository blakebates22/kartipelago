# The Moonstone Kingdom's scenery (Celestial Dragon Festival's paint: see
# celestial_dragon_festival.py): the Moonstone Gate, the lantern town, the Lake Bridge's
# arches and the ruins and islands in the glowing lake, the shore's ruined arches, the
# Palace Courtyard's winged-dragon fountain, the Crystal Climb's crystals, the Star
# Bridge's tall arches over the Cloud Chasm and the floating islands round it, the
# observatory and its great armillary sphere on the pinnacle, the palace on the mount
# with the purple dragon on its tower, the terraces, the causeway's crescent banners, the
# overlook; the light and the air. Keep_props.py's castle kit in moonstone (a palette
# swap). Nothing here changes the driving: solids stand clear of the roads.
# SPDX-License-Identifier: MIT

import math

import course_kit as kit
import ember_props as ep
import keep_props as kp
import props
from aurora_scenery import Mesh, falls_sheet, game_entity, road_rot
from course_kit import rnd
from keep_props import _cyl, _dragon, _p
from keep_scenery import Scene, across, arches, brazier_at, clear_of, facing, near_piece, parapet_torches, side_banners, wall_line
from props import blob, cuboid, tube

STONE = ("moon_stone", "wall")
DARK = ("moon_stone_dark", "wall")
ROCK = ("moon_rock", "wall")

PALETTE = {
    "keep_ashlar": "moon_stone",
    "keep_ashlar_dark": "moon_stone_dark",
    "keep_parapet": "moon_stone",
    "keep_slate": "moon_slate",
    "keep_roof": "moon_slate",
    "keep_timber": "moon_stone",
    "keep_window": "moon_window",
    "keep_gold": "moon_silver",
    "keep_banner": "moon_banner",
    "keep_banner_dark": "moon_banner",
    "keep_flag_blue": "moon_banner",
    "dragon_red": "dragon_purple",
    "dragon_wing": "dragon_purple_wing",
    "dragon_belly": "moon_silver",
    "ember_ashlar": "moon_stone",
}


# ------------------------------------------------------------------ the kingdom's own props


def armillary(c, r=10.0):
    """A great armillary sphere: silver rings round a glowing blue orb, on a stand."""
    name = "Armillary Sphere %.0f" % r

    def build(P, bm):
        P.add("moon_stone", lambda: cuboid(bm, (0, 0, 1.0), (r * 0.8, r * 0.8, 2.0)))
        P.add("moon_silver", lambda: _cyl(bm, 0, 0, 2.0, r * 0.9, 0.5, 0.35, n=6))
        cz = r * 1.25
        for k, (tx, ty) in enumerate(((0.0, 0.0), (math.pi / 2, 0.0), (math.pi / 2, math.pi / 2), (0.42, 0.9))):
            pts = []
            for j in range(25):
                a = j * math.tau / 24
                x, y, z = r * math.cos(a), r * math.sin(a), 0.0
                y, z = y * math.cos(tx) - z * math.sin(tx), y * math.sin(tx) + z * math.cos(tx)
                x, y = x * math.cos(ty) - y * math.sin(ty), x * math.sin(ty) + y * math.cos(ty)
                pts.append((x, y, cz + z))
            P.add("moon_silver", lambda pts=pts: tube(bm, pts, 0.32, n=5))
        P.add("moon_crystal", lambda: blob(bm, (0, 0, cz), r * 0.32))

    return _p(c, name, build)


def winged_statue(c):
    """The courtyard fountain's centrepiece: a winged dragon in moonstone on a tall
    pedestal (origin at the pedestal's foot)."""
    name = "Winged Dragon Statue"

    def build(P, bm):
        P.add("moon_stone", lambda: _cyl(bm, 0, 0, 0.0, 6.0, 2.4, 1.8, n=8))
        P.add("moon_silver", lambda: _cyl(bm, 0, 0, 6.0, 6.6, 2.4, 2.4, n=8))
        _dragon(P, bm, (0, 0, 6.6), 0.75, "moon_stone", "moon_stone_dark", "moon_silver", wings=1.2)

    return _p(c, name, build)


def basin(c, r=11.0):
    """A wide round fountain basin with a rim, water inside."""
    name = "Moon Basin %.0f" % r

    def build(P, bm):
        P.add("moon_stone", lambda: _cyl(bm, 0, 0, -0.6, 1.1, r, r, n=16))
        P.add("moon_lake_shallow", lambda: _cyl(bm, 0, 0, 1.0, 1.15, r - 1.0, r - 1.0, n=16))

    return _p(c, name, build)


def island(c, x, y, z, r, seed, sc):
    """A floating island: a rock cone hanging under a grassy top, a little castle on it,
    a fall off its edge."""
    m = Mesh()
    m.add(ROCK, lambda bm: _cyl(bm, x, y, z - r * 1.6, z - 0.3, r * 0.15, r, n=10, phase=seed))
    m.add(("moon_grass", "grass"), lambda bm: _cyl(bm, x, y, z - 0.4, z + 0.3, r * 0.98, r * 0.92, n=10, phase=seed))
    m.build(c, "Floating Island", "Islands", "visual")
    if seed % 2 == 0:
        sc.put(kp.round_tower(c, r * 0.22, r * 0.9, True, seed % 3), x + r * 0.2, y, z + 0.2, coll="Islands", role="visual")
    else:
        sc.put(kp.square_tower(c, r * 0.35, r * 0.6, True, seed % 2), x - r * 0.15, y + r * 0.1, z + 0.2, coll="Islands", role="visual")
    a = seed * 1.7
    fx, fy = math.cos(a), math.sin(a)
    falls_sheet(c, x + fx * r * 0.9, y + fy * r * 0.9, z, z - r * 2.5, r * 0.35, (fx, fy), mat=("keep_falls", "water"), name="Island Falls", bulge=1.5)


# ------------------------------------------------------------------ the sections


def gate(sc):
    c, dk = sc.c, sc.dk
    q = c.at(12.0)
    for side in (-1, 1):
        p = q.side(side * (q.w / 2 + 5.0))
        sc.put(kp.round_tower(c, 4.5, 20.0, True, 2), p.x, p.y, q.p.z - 0.5, coll="Gate", r=4.8)
        for f in (-1, 1):
            b = q.side(side * (q.w / 2 + 2.5)) + q.t * f * 12.0
            brazier_at(sc, b.x, b.y, sc.ground(b.x, b.y), coll="Gate")
    sc.put(kp.gate_arch(c, q.w + 10.0, 11.5), q.p.x, q.p.y, q.p.z, rot=across(q), coll="Gate", role="visual")
    s = 28.0
    while s < dk.TO_ROAD(dk.SEG[1]) - 4:
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 3.0))
            sc.put(kp.banner_pole(c), p.x, p.y, sc.ground(p.x, p.y), rot=road_rot(q) + (0 if side > 0 else math.pi), coll="Gate", r=0.3)
        s += 18.0


def town(sc):
    c, dk = sc.c, sc.dk
    S = dk.TO_ROAD
    s, s1 = 30.0, S(dk.SEG[4]) + 4
    k = 0
    while s < s1:
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 8.5 + 1.5 * (k % 2)))
            if not near_piece(c, q, p.x, p.y) or not clear_of(c, p.x, p.y, 4.5) or not sc.free(p.x, p.y, 4.0):
                continue
            sc.put(kp.house(c, (k * 2 + (side > 0)) % 4), p.x, p.y, sc.ground(p.x, p.y) - 0.3, rot=facing(p.x, p.y, q.p.x, q.p.y), coll="Town", r=4.5)
            d = q.side(side * (q.w / 2 + 3.2))
            if k % 2 == 0 and clear_of(c, d.x, d.y, 1.0):
                sc.put(ep.lantern_post(c), d.x, d.y, sc.ground(d.x, d.y), rot=facing(d.x, d.y, q.p.x, q.p.y), coll="Town", r=0.5)
                f = d + (q.p - d).normalized() * 0.9
                sc.flames.append((f.x, f.y, sc.ground(d.x, d.y) + 4.3))
        s += 13.0
        k += 1


def lake(sc):
    """Arches under the Lake Bridge, banners and lanterns along it; ruined arches standing
    in the water and little islands with boats."""
    c, dk = sc.c, sc.dk
    for piece in c.pieces:
        if not (piece.name.endswith("bridge") and not piece.name.endswith("high_bridge")):
            continue
        s0, s1 = piece["kp_from"], piece["kp_to"]
        if s1 - s0 > 10:
            arches(c, s0 + 2, s1 - 2, c.at(s0).p.z + 3.0, every=18.0, name="Lake Bridge", stone=STONE, accent=DARK)
            side_banners(sc, s0 + 4, s1 - 4, every=18.0)
            parapet_torches(sc, s0 + 2, s1 - 2, every=18.0)
    for k in range(7):
        x = dk.LAGOON_X + 60 + 230 * rnd(k * 3 + 1)
        y = dk.MOUNT[1] - 260 + 180 * rnd(k * 3 + 2)
        if not clear_of(c, x, y, 18.0):
            continue
        rk = c.rock_mass("Lake Islet %d" % k, x, y, 9.0, 7.0, 3.0, z0=-4.0, n=10, seed=80 + k)
        c.paint_rock(rk, ROCK, ("moon_grass", "grass"))
        if k % 2:
            sc.put(ep.ruined_arch(c, 9.0, 8.0), x, y, 2.6, rot=rnd(k) * 6.28, coll="Lake", role="visual")
        else:
            sc.put(kp.boat(c, k), x + 10.0, y, -1.8, rot=rnd(k) * 6.28, coll="Lake", role="visual")
            sc.put(kp.round_tower(c, 2.6, 8.0, True, k % 3), x, y, 2.6, coll="Lake", role="visual")


def shore(sc):
    c, dk = sc.c, sc.dk
    S = dk.TO_ROAD
    s, s1 = S(dk.SEG[9]) + 10, S(dk.SEG[14])
    k = 0
    while s < s1:
        q = c.at(s)
        side = 1 if k % 2 else -1
        p = q.side(side * (q.w / 2 + 9.0))
        if clear_of(c, p.x, p.y, 6.0) and sc.free(p.x, p.y, 5.0):
            sc.put(ep.ruined_arch(c, 8.0, 8.0), p.x, p.y, sc.ground(p.x, p.y), rot=road_rot(q), coll="Shore", r=5.0)
            sc.put(kp.wall_banner(c, kp.BANNER, 2.2, 4.5), p.x - math.cos(road_rot(q)) * 5.0, p.y - math.sin(road_rot(q)) * 5.0, sc.ground(p.x, p.y) + 8.6,
                   rot=road_rot(q) + math.pi / 2, coll="Shore", role="visual")
        s += 34.0
        k += 1


def courtyard(sc):
    """The Palace Courtyard inside the loop: the winged dragon's fountain, braziers."""
    c, dk = sc.c, sc.dk
    x, y = dk.SHRINE
    z = sc.ground(x, y)
    sc.put(basin(c, 11.0), x, y, z, coll="Courtyard", r=11.0)
    sc.put(winged_statue(c), x, y, z + 1.0, rot=facing(x, y, *dk._seg_point(13)[:2]), coll="Courtyard", r=2.6)
    game_entity(c, "fountain", x, y, z + 1.2, height=4.0, jets=8, radius=7.0)
    for k in range(6):
        a = k * math.tau / 6 + 0.3
        bx, by = x + 15.0 * math.cos(a), y + 15.0 * math.sin(a)
        if clear_of(c, bx, by, 2.5):
            brazier_at(sc, bx, by, sc.ground(bx, by), coll="Courtyard")


def climb(sc):
    """Crystal outcrops and lantern posts up the Crystal Climb."""
    c, dk = sc.c, sc.dk
    S = dk.TO_ROAD
    s, s1 = S(dk.SEG[16]), S(dk.SEG[22])
    k = 0
    while s < s1:
        q = c.at(s)
        side = 1 if k % 2 else -1
        p = q.side(side * (q.w / 2 + 6.5 + 2 * (k % 3)))
        if clear_of(c, p.x, p.y, 4.0) and sc.free(p.x, p.y, 3.0):
            mat = "moon_crystal" if k % 3 else "moon_crystal_violet"
            sc.put(props.crystals(c, mat), p.x, p.y, sc.ground(p.x, p.y) - 0.3, rot=rnd(k) * 6.28, scale=1.6 + 0.6 * (k % 2), coll="Climb", role="both", r=2.5)
            sc.glows.append((p.x, p.y, sc.ground(p.x, p.y) + 2.0))
        d = q.side(-side * (q.w / 2 + 3.2))
        if k % 2 == 0 and clear_of(c, d.x, d.y, 1.0):
            sc.put(ep.lantern_post(c), d.x, d.y, sc.ground(d.x, d.y), rot=facing(d.x, d.y, q.p.x, q.p.y), coll="Climb", r=0.5)
            f = d + (q.p - d).normalized() * 0.9
            sc.flames.append((f.x, f.y, sc.ground(d.x, d.y) + 4.3))
        s += 22.0
        k += 1


def star_bridge(sc):
    """Tall arches down into the Cloud Chasm under the Star Bridge, banners and lanterns;
    floating islands round it; cloud along the chasm's floor."""
    c, dk = sc.c, sc.dk
    for piece in c.pieces:
        if not (piece.name.endswith("high_bridge") or piece.name.endswith("ramp")):
            continue
        s0, s1 = piece["kp_from"], piece["kp_to"]
        if s1 < s0:
            s1 += c.length
        q = c.at((s0 + s1) / 2 % c.length)
        ground = sc.ground(q.p.x, q.p.y)
        if s1 - s0 > 10 and q.p.z - ground > 14:
            arches(c, s0 + 2, s1 - 2, min(90.0, q.p.z - ground + 4.0), every=22.0, pier=(5.0, 6.0), name="Star Bridge", stone=STONE, accent=DARK)
            side_banners(sc, s0 + 4, s1 - 4, every=22.0)
            parapet_torches(sc, s0 + 2, s1 - 2, every=22.0)
    for k, (x, y, z, r) in enumerate(((-40, 430, 70, 16), (60, 460, 95, 20), (150, 420, 60, 13), (-160, 470, 110, 18), (230, 480, 85, 15),
                                      (-250, 420, 75, 12), (100, 540, 130, 24))):
        if clear_of(c, x, y, 25.0):
            island(c, x, y, z, r, k, sc)
    bm = kit.bmesh.new()
    vs = [bm.verts.new(p) for p in ((-260, dk.CHASM_Y + 30, -25.0), (560, dk.CHASM_Y + 30, -25.0), (560, 560, -25.0), (-260, 560, -25.0))]
    bm.faces.new(vs)
    ob = c.mesh_object("Chasm Clouds", bm, "Water", "visual")
    c.assign(ob, c.lib("cdf_cloud", "water"))


def observatory(sc):
    """On the pinnacle: the observatory's towers and the great armillary sphere."""
    import bpy

    c, dk = sc.c, sc.dk
    x, y = dk.PINNACLE
    rock = bpy.data.objects.get("Observatory Pinnacle")
    z = c.ground_z(x, y, [rock]) if rock else 88.0
    z = z if z is not None else 88.0
    sc.put(armillary(c, 7.5), x, y, z - 0.5, rot=0.4, coll="Observatory", role="visual")
    for k, a in enumerate((0.8, 2.9, 4.6)):
        tx, ty = x + 10.5 * math.cos(a), y + 10.5 * math.sin(a)
        sc.put(kp.round_tower(c, 3.0, 12.0 + 4 * k, True, k), tx, ty, z - 1.0, coll="Observatory", role="visual")
    sc.glows.append((x, y, z + 9.0))


def palace(sc):
    """The palace on the mount, its towers, and the purple dragon on the tallest."""
    c, dk = sc.c, sc.dk
    mx, my = dk.MOUNT
    z = sc.ground(mx, my)
    sc.put(kp.keep_block(c, 44.0, 28.0, 30.0), mx, my, z - 2.0, rot=0.2, coll="Palace", r=26.0)
    for dx, dy, h in ((-30, -20, 34.0), (30, -18, 30.0), (-28, 22, 28.0)):
        x, y = mx + dx, my + dy
        sc.put(kp.round_tower(c, 5.0, h, True, int(h) % 3), x, y, sc.ground(x, y) - 2.0, coll="Palace", r=5.5)
    tx, ty = mx + 32.0, my + 22.0
    TH = 46.0
    tz = sc.ground(tx, ty) - 2.0
    sc.put(kp.round_tower(c, 6.5, TH, False, 0), tx, ty, tz, coll="Palace", r=7.0)
    sc.put(kp.great_dragon(c), tx, ty + 1.0, tz + TH + 0.6, rot=facing(tx, ty, *dk.PINNACLE), scale=1.2, coll="Palace", role="visual")
    for k in range(4):
        a = k * math.pi / 2 + 0.4
        bx, by = tx + 5.4 * math.cos(a), ty + 5.4 * math.sin(a)
        sc.put(kp.torch_post(c, 1.6), bx, by, tz + TH + 0.6, coll="Palace", role="visual")
        sc.flames.append((bx, by, tz + TH + 2.2))
    ring = []
    for k in range(13):
        a = k * math.tau / 12
        ring.append((mx + 58 * math.cos(a), my + 46 * math.sin(a)))
    wall_line(sc, ring, h=9.0, tower_every=60.0, margin=10.0, coll="Palace", tower_h=14.0, roof=True)


def terraces(sc):
    """The terraces under the palace: houses where the greybox's blocks stood, lantern
    posts, banner poles down the causeway, statues at the overlook."""
    c, dk = sc.c, sc.dk
    S = dk.TO_ROAD
    s = dk.SEG[25]
    k = 0
    while s < dk.SEG[28]:
        q = c.at(S(s))
        p = q.side((1 if k % 2 else -1) * (q.w / 2 + 9.0))
        if clear_of(c, p.x, p.y, 4.5) and sc.free(p.x, p.y, 4.5):
            sc.put(kp.house(c, k % 4), p.x, p.y, sc.ground(p.x, p.y) - 0.3, rot=facing(p.x, p.y, q.p.x, q.p.y), coll="Terraces", r=4.5)
        s += 18.0
        k += 1
    s, s1 = S(dk.SEG[28]) + 6, S(dk.SEG[29])
    while s < s1:
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 3.2))
            if clear_of(c, p.x, p.y, 2.0):
                sc.put(kp.banner_pole(c, kp.BANNER, 8.0), p.x, p.y, sc.ground(p.x, p.y), rot=road_rot(q) + (0 if side > 0 else math.pi), coll="Terraces", r=0.3)
        s += 15.0
    q = c.at(S(dk.SEG[30]))
    for side in (-1, 1):
        p = q.side(side * (q.w / 2 + 6.0))
        if clear_of(c, p.x, p.y, 3.0) and sc.free(p.x, p.y, 3.0):
            sc.put(kp.dragon_statue(c, "keep_ashlar"), p.x, p.y, sc.ground(p.x, p.y), rot=facing(p.x, p.y, q.p.x, q.p.y), coll="Terraces", r=2.8)
    s, s1 = S(dk.SEG[29]), c.length - 20
    k = 0
    while s < s1:
        q = c.at(s)
        b = q.side((1 if k % 2 else -1) * (q.w / 2 + 3.2))
        if clear_of(c, b.x, b.y, 2.0):
            brazier_at(sc, b.x, b.y, sc.ground(b.x, b.y), coll="Terraces")
        s += 26.0
        k += 1


def nature(sc):
    """Trees with violet leaves? Pines in moonlight, and boulders, clear of everything."""
    c, dk = sc.c, sc.dk
    k = 0
    for i in range(2600):
        x = -250 + rnd(i * 3 + 1) * 800
        y = -150 + rnd(i * 3 + 2) * 700
        if k > 300:
            break
        z = dk.natural(x, y)
        if z < 1.5 or not clear_of(c, x, y, 13.0) or not sc.free(x, y, 6.0):
            continue
        if rnd(i * 5 + 7) < 0.3:
            continue
        zz = sc.ground(x, y)
        if rnd(i * 7 + 3) < 0.85:
            sc.put(kp.pine(c, k % 3, 10.0), x, y, zz - 0.3, rot=rnd(i) * 6.3, scale=(8.0 + 7.0 * rnd(i * 11 + 5)) / 10.0, coll="Nature", r=1.2)
        else:
            sc.put(props.boulder(c, "moon_rock", k % 3), x, y, zz - 0.4, rot=rnd(i) * 6.3, scale=1.0 + 1.4 * rnd(i * 13 + 1), coll="Nature", r=2.0)
        k += 1


# ------------------------------------------------------------------ light and air


ZONES = {
    "open": {"fog": "#3a3a78", "near": 380, "far": 2300, "sun": 1.8, "sky": "#9a9ae0", "ground": "#3a3060", "hemi": 1.3, "sound": "wind"},
    "lake": {"fog": "#34407a", "near": 400, "far": 2400, "sun": 1.8, "sky": "#90a8e8", "ground": "#2a3a70", "hemi": 1.3, "sound": "harbour"},
    "chasm": {"fog": "#40407e", "near": 360, "far": 2200, "sun": 1.9, "sky": "#a4a0ea", "ground": "#3a3268", "hemi": 1.3, "sound": "wind"},
}


def atmosphere(c, dk):
    S = dk.TO_ROAD
    lake_ = (S(dk.SEG[4]), S(dk.SEG[9]))
    chasm = (S(dk.SEG[21]), S(dk.SEG[24]))

    def zone(s):
        s %= c.length
        if lake_[0] <= s <= lake_[1]:
            return "lake"
        if chasm[0] <= s <= chasm[1]:
            return "chasm"
        return "open"

    keys = []
    s = 0.0
    while s < c.length:
        q = c.at(s)
        here = zone(s)
        a_, b_, t = here, here, 0.0
        for d in range(2, 25, 2):
            if zone(s + d) != here:
                a_, b_, t = here, zone(s + d), 0.5 * (1.0 - d / 24.0)
                break
            if zone(s - d) != here:
                a_, b_, t = zone(s - d), here, 0.5 + 0.5 * d / 24.0
                break
        x, y, z = c.game(q.p.x, q.p.y, q.p.z)
        keys.append([round(x, 1), round(y, 1), round(z, 1), a_, b_, round(t * t * (3 - 2 * t), 3)])
        s += 12.0
    c.entity("atmosphere", zones=ZONES, keys=keys)


def light(sc):
    c = sc.c
    groups = ("Castle", "Gate", "Town", "Lake", "Shore", "Courtyard", "Climb", "Islands", "Observatory", "Palace", "Terraces", "Nature")
    c.merge_props(groups, cell=260.0)
    built = [o for name in groups + ("Bridges", "Rocks") for o in c.coll(name).objects if o.type == "MESH" and o.data.users == 1]
    ter = [sc.ter]
    c.preset("sun", ter + built, 0.24)
    c.glow(ter + built, [], 1.0, (1, 1, 1), base=(0.78, 0.78, 0.95))
    c.glow(ter + built, sc.flames, 14.0, (1.8, 1.3, 0.8), base=1.0)
    c.glow(ter + built, sc.glows, 16.0, (0.9, 1.1, 1.7), base=1.0)
    kit.paint.shade_roads(c.pieces + getattr(c, "lanes", []), 0.3)


def build(c, dk, ter, ruin=False):
    """(`ruin`: returns the scene before its lights, for the ruin's dressing.)"""
    kp.use_palette(PALETTE)
    sc = Scene(c, dk, ter)
    sc.glows = []
    gate(sc)
    town(sc)
    lake(sc)
    shore(sc)
    courtyard(sc)
    climb(sc)
    star_bridge(sc)
    observatory(sc)
    palace(sc)
    terraces(sc)
    nature(sc)
    if ruin:
        return sc
    for x, y, z in sc.flames:
        game_entity(c, "torch", x, y, z)
    for x, y, z in sc.glows:
        game_entity(c, "glow", x, y, z, color="#8ab8ff")
    c.entity("sparkles", rate=20, radius=34)
    atmosphere(c, dk)
    light(sc)
    print("moon scenery: props", c.prop_count, "flames", len(sc.flames))
    return sc
