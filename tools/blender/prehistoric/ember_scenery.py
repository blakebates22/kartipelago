# Emberdeep Hold's scenery (see snow_dragon_pass.py): the Outer Gate, the lower town, the
# Mountain Approach's parapets and torches, the Hall of Pillars on the first other road,
# the Ramparts and barracks, the Cliff Bridge's arches over the chasm and its falls, the
# Waterfall Causeway's crags and falls, the Courtyard's great hall, the Gatehouse Tunnel on
# the second other road, the Dragon's Perch (the red dragon on its hoard, on top of the
# bastion), the fortress built into the central peak, far peaks, pines, the storm, the
# light and the air. Keep_props.py's castle kit is built in Emberdeep's stone (a palette
# swap); ember_props.py has the rest. Nothing here changes the driving: everything solid
# stands clear of the roads; things over a road are visual only.
# SPDX-License-Identifier: MIT

import math

import course_kit as kit
import ember_props as ep
import keep_props as kp
from aurora_scenery import Mesh, falls_sheet, game_entity, road_rot
from course_kit import lerp, rnd, smooth
from keep_scenery import Scene, across, arches, brazier_at, clear_of, facing, near_piece, parapet_torches, sheet_rect, side_banners, torch_at, wall_line, wall_torch_at
from props import boulder, cuboid

SAND = ("ember_ashlar", "wall")
DARK = ("ember_ashlar_dark", "wall")
PARAPET = ("ember_parapet", "wall")
ROCK = ("ember_rock", "wall")

PALETTE = {
    "keep_ashlar": "ember_ashlar",
    "keep_ashlar_dark": "ember_ashlar_dark",
    "keep_parapet": "ember_parapet",
    "keep_slate": "ember_ashlar_dark",
    "keep_banner": "ember_banner",
    "keep_banner_dark": "ember_banner",
    "keep_flag_blue": "ember_flag_red",
}


def shortcut_z(pts, za, zb, i, u):
    """Height of the other road between its points i and i+1 (as the course lays it)."""
    n = len(pts) - 1
    return lerp(za, zb, smooth((i + u) / n)) - 0.05


# ------------------------------------------------------------------ the sections


def gate(sc):
    """The Outer Gate: two great square towers, the arch between them with its raised
    portcullis and banners, braziers, banner poles down the start, walls running off."""
    c, dk = sc.c, sc.dk
    q = c.at(12.0)
    for side in (-1, 1):
        p = q.side(side * (q.w / 2 + 6.0))
        sc.put(kp.square_tower(c, 9.0, 22.0, False, 1), p.x, p.y, q.p.z - 0.5, rot=road_rot(q), coll="Gate", r=6.5)
        sc.put(kp.flag_pole(c, "keep_flag_blue", 6.0), p.x, p.y, q.p.z + 22.8, coll="Gate", role="visual")
        for f in (-1, 1):
            b = q.side(side * (q.w / 2 + 2.6)) + q.t * f * 13.0
            brazier_at(sc, b.x, b.y, sc.ground(b.x, b.y), coll="Gate")
    sc.put(kp.gate_arch(c, q.w + 12.0, 11.5), q.p.x, q.p.y, q.p.z, rot=across(q), coll="Gate", role="visual")
    sc.put(ep.portcullis(c, q.w - 2.0, 5.0), q.p.x, q.p.y, q.p.z + 10.4, rot=across(q), coll="Gate", role="visual")
    s = 28.0
    while s < dk.TO_ROAD(dk.SEG[1]) - 4:
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 3.0))
            sc.put(kp.banner_pole(c), p.x, p.y, sc.ground(p.x, p.y), rot=road_rot(q) + (0 if side > 0 else math.pi), coll="Gate", r=0.3)
        s += 18.0
    q = c.at(12.0)
    w0, e0 = q.side(-(q.w / 2 + 11.0)), q.side(q.w / 2 + 11.0)
    wall_line(sc, [(w0.x, w0.y), (w0.x, w0.y + 60), (w0.x - 30, w0.y + 90)], h=11.0, tower_every=40.0, coll="Gate", tower_h=16.0, roof=False)
    wall_line(sc, [(e0.x, e0.y), (e0.x, e0.y - 40), (e0.x + 40, e0.y - 70)], h=11.0, tower_every=40.0, coll="Gate", tower_h=16.0, roof=False)


def town(sc):
    """The lower town: houses down both sides of the S, lantern posts, barrels."""
    c, dk = sc.c, sc.dk
    S = dk.TO_ROAD
    s, s1 = S(dk.SEG[1]) - 4, S(dk.SEG[5]) + 10
    k = 0
    while s < s1:
        q = c.at(s)
        for side in (-1, 1):
            off = q.w / 2 + 8.5 + 1.5 * ((k + (side > 0)) % 2)
            p = q.side(side * off)
            if not near_piece(c, q, p.x, p.y) or not clear_of(c, p.x, p.y, 4.5) or not sc.free(p.x, p.y, 4.0):
                continue
            sc.put(kp.house(c, (k * 2 + (side > 0)) % 4), p.x, p.y, sc.ground(p.x, p.y) - 0.3, rot=facing(p.x, p.y, q.p.x, q.p.y), coll="Town", r=4.5)
            if k % 2 == 0:
                d = q.side(side * (q.w / 2 + 3.4))
                sc.put(ep.lantern_post(c), d.x, d.y, sc.ground(d.x, d.y), rot=facing(d.x, d.y, q.p.x, q.p.y), coll="Town", r=0.5)
                f = d + (q.p - d).normalized() * 0.9
                sc.flames.append((f.x, f.y, sc.ground(d.x, d.y) + 4.3))
            elif k % 3 == 1:
                d = q.side(side * (q.w / 2 + 3.6)) + q.t * 1.5
                sc.put(kp.barrel(c), d.x, d.y, sc.ground(d.x, d.y), coll="Town", role="visual")
                sc.put(kp.crate(c), d.x + 1.2, d.y + 0.4, sc.ground(d.x, d.y), rot=0.4, coll="Town", role="visual")
        s += 13.0
        k += 1


def approach(sc):
    """The Mountain Approach: torches along the hairpins' parapets, banners down the
    cliff decks' sides."""
    dk = sc.dk
    S = dk.TO_ROAD
    parapet_torches(sc, S(dk.SEG[7]), S(dk.SEG[14]), every=20.0, out=1.2, coll="Approach")
    for i in (8, 10, 12):
        side_banners(sc, S(dk.SEG[i]) + 4, S(dk.SEG[i + 1]) - 4, every=18.0, drop=0.6, coll="Approach")


def hall(sc, z1):
    """The Hall of Pillars, on the first other road (where the greybox's cavern stood):
    pillars either side, walls behind them, a vaulted roof, chandeliers, banners, torches
    on the pillars; an arch at each end."""
    c, dk = sc.c, sc.dk
    pts = dk.SUPPLY
    za, zb = z1
    i = int(0.55 * (len(pts) - 1))
    (x0, y0), (x1, y1) = pts[i], pts[i + 1]
    L = math.hypot(x1 - x0, y1 - y0)
    rot = math.atan2(y1 - y0, x1 - x0)
    tx, ty = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -ty, tx
    m = Mesh()
    n = int(L / 10.0)
    for k in range(n + 1):
        u = k / n
        x, y = lerp(x0, x1, u), lerp(y0, y1, u)
        z = shortcut_z(pts, za, zb, i, u)
        for side in (-1, 1):
            px, py = x + nx * side * 9.8, y + ny * side * 9.8
            sc.put(ep.pillar(c, 11.0, 1.05), px, py, z - 0.4, coll="Hall", r=1.4)
            if k % 2 == 0:
                wall_torch_at(sc, px - nx * side * 1.1, py - ny * side * 1.1, z + 4.0, math.atan2(-ny * side, -nx * side) - math.pi / 2, coll="Hall")
        if 0 < k < n:
            sc.put(ep.chandelier(c, 2.2, 4.0), x, y, z + 12.5, coll="Hall", role="visual")
            for a in range(6):
                aa = a * math.tau / 6
                sc.flames.append((x + 2.2 * math.cos(aa), y + 2.2 * math.sin(aa), z + 8.8))
    # The walls behind the pillars (solid), and the vault over it all (visual).
    zm = shortcut_z(pts, za, zb, i, 0.5)
    for side in (-1, 1):
        cx, cy = (x0 + x1) / 2 + nx * side * 13.5, (y0 + y1) / 2 + ny * side * 13.5
        m.add(SAND, lambda bm, cx=cx, cy=cy: cuboid(bm, (cx, cy, zm + 5.0), (L + 6.0, 2.0, 16.0), rot))
    ob = m.build(c, "Hall Walls", "Hall", "both")
    v = Mesh()
    steps = 8

    def vault(bm):
        rings = [math.pi * j / steps for j in range(steps + 1)]
        verts = []
        for k in range(n + 1):
            u = k / n
            x, y = lerp(x0 - tx * 3, x1 + tx * 3, u), lerp(y0 - ty * 3, y1 + ty * 3, u)
            z = shortcut_z(pts, za, zb, i, u)
            verts.append([bm.verts.new((x + nx * 13.0 * math.cos(a), y + ny * 13.0 * math.cos(a), z + 11.0 + 4.0 * math.sin(a))) for a in rings])
        for lo, hi in zip(verts, verts[1:]):
            for j in range(steps):
                bm.faces.new((lo[j], hi[j], hi[j + 1], lo[j + 1]))

    v.add(DARK, vault)
    v.build(c, "Hall Vault", "Hall", "visual")
    for u, flip in ((0.0, 0.0), (1.0, math.pi)):
        x, y = lerp(x0, x1, u), lerp(y0, y1, u)
        z = shortcut_z(pts, za, zb, i, u)
        out = 3.5 if u else -3.5
        sc.put(kp.stone_arch(c, 22.0, 13.0, 3.0), x + tx * out, y + ty * out, z, rot=rot - math.pi / 2 + flip, coll="Hall", role="visual")
        for side in (-1, 1):
            bx, by = x + nx * side * 7.0, y + ny * side * 7.0
            sc.put(kp.wall_banner(c, kp.BANNER, 2.6, 6.0), bx, by, z + 14.5, rot=rot + (math.pi / 2 if u == 0 else -math.pi / 2), coll="Hall", role="visual")
    return ob


def ramparts(sc):
    """The Ramparts along the top: a battlemented wall with towers and red flags on the
    mountain side, the barracks where the greybox's storehouses stood."""
    c, dk = sc.c, sc.dk
    S = dk.TO_ROAD
    pts = []
    s = S(dk.SEG[15]) + 10
    while s < S(dk.SEG[20]) - 4:
        q = c.at(s)
        # The mountain side: the side where the ground is higher.
        hi = 1 if dk.natural(*q.side(30.0).xy) > dk.natural(*q.side(-30.0).xy) else -1
        p = q.side(hi * (q.w / 2 + 16.0))
        pts.append((p.x, p.y))
        s += 16.0
    wall_line(sc, pts, h=10.0, tower_every=48.0, margin=8.0, coll="Ramparts", tower_h=16.0, roof=False)
    for k, (x, y) in enumerate(pts[::3]):
        if clear_of(c, x, y, 9.0):
            sc.put(kp.flag_pole(c, "keep_flag_blue", 7.0), x, y, sc.ground(x, y) + 10.5, coll="Ramparts", role="visual")
    s = dk.SEG[16] + 10
    k = 0
    while s < dk.SEG[20] - 6:
        q = c.at(S(s))
        side = 1 if k % 2 else -1
        p = q.side(side * (q.w / 2 + 9.0))
        if clear_of(c, p.x, p.y, 4.0) and sc.free(p.x, p.y, 4.0):
            sc.put(kp.house(c, 2 + k % 2), p.x, p.y, sc.ground(p.x, p.y) - 0.3, rot=facing(p.x, p.y, q.p.x, q.p.y), coll="Ramparts", r=4.5)
        d = q.side(side * (q.w / 2 + 3.2)) + q.t * 6.0
        if clear_of(c, d.x, d.y, 2.0):
            torch_at(sc, d.x, d.y, sc.ground(d.x, d.y), coll="Ramparts")
        s += 22.0
        k += 1


def bridge(sc):
    """The Cliff Bridge over the chasm: arches down into it either side of the broken
    span, banners and torches; falls down the chasm's walls and at its head."""
    c, dk = sc.c, sc.dk
    S = dk.TO_ROAD
    lip, land = S(dk.LIP), S(dk.LAND)
    a0, a1 = S(dk.SEG[20]) + 4, S(dk.SEG[21]) - 2
    zf = 18.0
    for s0, s1, name in ((a0, lip - 1, "Cliff Bridge East"), (land + 1, a1, "Cliff Bridge West")):
        if s1 - s0 > 8:
            arches(c, s0, s1, c.at(s0).p.z - zf + 4, every=16.0, name=name, stone=SAND, accent=PARAPET)
            side_banners(sc, s0, s1, every=16.0)
            parapet_torches(sc, s0, s1 - 2, every=16.0)
    gx = dk.GORGE_X
    qb = c.at((lip + land) / 2)
    for y, w, face in ((qb.p.y + 60, 10.0, (1, 0)), (qb.p.y + 95, 12.0, (-1, 0)), (qb.p.y - 50, 9.0, (-1, 0))):
        x = gx - face[0] * 21.0
        top = dk.natural(x - face[0] * 8, y) + 0.5
        if top > zf + 6:
            falls_sheet(c, x, y, top, zf - 1.0, w, face, mat=("keep_falls", "water"), name="Chasm Falls")
            sc.falls.append((x + face[0] * 3, y, zf, top, w, math.atan2(face[0], face[1])))
    hy = 505.0
    head = c.rock_mass("Chasm Head", gx, hy + 14, 34.0, 12.0, 92.0, z0=0.0, n=16, seed=31)
    c.paint_rock(head, ROCK, ("ember_moss", "rubble"))
    falls_sheet(c, gx, hy, 88.0, zf - 1.0, 20.0, (0, -1), mat=("keep_falls", "water"), name="Great Chasm Falls", bulge=4.0)
    sc.falls.append((gx, hy - 4, zf, 88.0, 20.0, math.pi))
    sheet_rect(c, "Chasm Mist", gx - 20, gx + 20, 250.0, hy, zf + 2.5, ("keep_mist", "water"))


def causeway(sc):
    """The Waterfall Causeway: crags beside the run down, each with falls into a pool,
    braziers along the road."""
    c, dk = sc.c, sc.dk
    S = dk.TO_ROAD
    s0, s1 = S(dk.SEG[21]) + 20, S(dk.SEG[27])
    for k, f in enumerate((0.15, 0.5, 0.85)):
        q = c.at(lerp(s0, s1, f))
        hi = 1 if dk.natural(*q.side(30.0).xy) > dk.natural(*q.side(-30.0).xy) else -1
        p = q.side(hi * (q.w / 2 + 30.0))
        base = sc.ground(p.x, p.y)
        top = base + 26.0 + 6 * k
        rk = c.rock_mass("Causeway Crag %d" % k, p.x, p.y, 14.0, 10.0, top, z0=base - 6.0, n=14, seed=50 + k, angle=road_rot(q))
        c.paint_rock(rk, ROCK, ("ember_moss", "rubble"))
        face = (q.p.x - p.x, q.p.y - p.y)
        fl = math.hypot(*face)
        fx, fy = face[0] / fl, face[1] / fl
        wx, wy = p.x + fx * 9.0, p.y + fy * 9.0
        falls_sheet(c, wx, wy, top - 1.0, base - 0.5, 7.0, (fx, fy), mat=("keep_falls", "water"), name="Causeway Falls")
        sc.falls.append((wx + fx * 3, wy + fy * 3, base, top, 7.0, math.atan2(fx, fy)))
        c.disc("Causeway Pool %d" % k, wx + fx * 5, wy + fy * 5, 6.0, base - 0.2, c.lib("ember_water"), role="visual", n=14)
    s = s0
    k = 0
    while s < s1:
        q = c.at(s)
        side = 1 if k % 2 else -1
        b = q.side(side * (q.w / 2 + 3.4))
        if clear_of(c, b.x, b.y, 2.0):
            brazier_at(sc, b.x, b.y, sc.ground(b.x, b.y), coll="Causeway")
        s += 24.0
        k += 1


def courtyard(sc):
    """The Courtyard on the zigzag: the great hall inside the hairpin (where the
    greybox's monastery stood), statues and braziers round it, banners."""
    c, dk = sc.c, sc.dk
    mx, my = dk._arc_centre(29)
    z = sc.ground(mx, my)
    sc.put(kp.keep_block(c, 16.0, 13.0, 16.0), mx, my, z - 0.5, rot=facing(mx, my, *dk._seg_point(28)[:2]) + math.pi / 2, coll="Courtyard", r=11.0)
    S = dk.TO_ROAD
    for s, side in ((S(dk.SEG[28]) + 6, 1), (S(dk.SEG[28]) + 6, -1), (S(dk.SEG[30]) + 20, 1), (S(dk.SEG[30]) + 20, -1)):
        q = c.at(s)
        p = q.side(side * (q.w / 2 + 5.0))
        if clear_of(c, p.x, p.y, 3.0) and sc.free(p.x, p.y, 3.0):
            if side > 0:
                sc.put(kp.dragon_statue(c, "keep_ashlar"), p.x, p.y, sc.ground(p.x, p.y), rot=facing(p.x, p.y, q.p.x, q.p.y), coll="Courtyard", r=2.8)
            else:
                brazier_at(sc, p.x, p.y, sc.ground(p.x, p.y), coll="Courtyard")


def tunnel(sc, z2):
    """The Gatehouse Tunnel on the second other road (where the greybox's arches stood):
    stone walls, a vault, portals with raised portcullises and banners, torches inside."""
    c, dk = sc.c, sc.dk
    pts = dk.AQUEDUCT
    za, zb = z2
    i = int(0.5 * (len(pts) - 1))
    (x0, y0), (x1, y1) = pts[i], pts[i + 1]
    L = math.hypot(x1 - x0, y1 - y0)
    rot = math.atan2(y1 - y0, x1 - x0)
    tx, ty = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -ty, tx
    zm = shortcut_z(pts, za, zb, i, 0.5)
    m = Mesh()
    for side in (-1, 1):
        cx, cy = (x0 + x1) / 2 + nx * side * 10.5, (y0 + y1) / 2 + ny * side * 10.5
        m.add(SAND, lambda bm, cx=cx, cy=cy: cuboid(bm, (cx, cy, zm + 4.0), (L + 4.0, 3.0, 14.0), rot))
    m.build(c, "Tunnel Walls", "Tunnel", "both")
    v = Mesh()
    v.add(DARK, lambda bm: cuboid(bm, ((x0 + x1) / 2, (y0 + y1) / 2, zm + 11.0), (L + 4.0, 24.0, 4.0), rot))
    v.build(c, "Tunnel Roof", "Tunnel", "visual")
    for u in (0.0, 1.0):
        x, y = lerp(x0, x1, u), lerp(y0, y1, u)
        z = shortcut_z(pts, za, zb, i, u)
        sc.put(kp.stone_arch(c, 20.0, 12.0, 3.0), x, y, z, rot=rot - math.pi / 2, coll="Tunnel", role="visual")
        sc.put(ep.portcullis(c, 16.0, 5.0), x, y, z + 9.5, rot=rot - math.pi / 2, coll="Tunnel", role="visual")
    for k in range(3):
        u = (k + 0.5) / 3
        x, y = lerp(x0, x1, u), lerp(y0, y1, u)
        z = shortcut_z(pts, za, zb, i, u)
        for side in (-1, 1):
            wx, wy = x + nx * side * 8.9, y + ny * side * 8.9
            wall_torch_at(sc, wx, wy, z + 3.6, math.atan2(-ny * side, -nx * side) - math.pi / 2, coll="Tunnel")


def perch(sc):
    """The Dragon's Perch: on top of the bastion the spiral climbs round, the red dragon
    on its hoard, braziers about it; banners and torches up the spiral."""
    import bpy

    c, dk = sc.c, sc.dk
    S = dk.TO_ROAD
    bx, by = dk.BASTION
    rock = bpy.data.objects.get("Bastion")
    z = c.ground_z(bx, by, [rock]) if rock else 62.0
    z = z if z is not None else 62.0
    sc.put(ep.hoard(c, 7.5), bx, by, z - 0.4, coll="Perch", role="visual")
    gx, gy = 0.0, 0.0  # it watches the gate
    sc.put(kp.great_dragon(c), bx, by - 1.0, z + 1.6, rot=facing(bx, by, gx, gy), scale=1.35, coll="Perch", role="visual")
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        x, y = bx + 9.0 * math.cos(a), by + 9.0 * math.sin(a)
        sc.put(kp.brazier(c), x, y, z - 0.4, coll="Perch", role="visual")
        sc.flames.append((x, y, z + 2.8))
    side_banners(sc, S(dk.SEG[33]) + 30, S(dk.SEG[34]) - 10, every=30.0, coll="Perch")
    parapet_torches(sc, S(dk.SEG[33]) + 10, S(dk.SEG[34]) - 6, every=24.0, coll="Perch")


def mountain(sc):
    """The fortress built into the central peak: walls and square towers round its
    slopes, the keep and a tall flag tower on top."""
    c, dk = sc.c, sc.dk
    px, py = dk.PEAK
    ring = []
    for k in range(13):
        a = k * math.tau / 12
        ring.append((px + 62 * math.cos(a), py + 55 * math.sin(a)))
    wall_line(sc, ring, h=12.0, tower_every=55.0, margin=14.0, coll="Fortress", tower_h=18.0, roof=False)
    for k, (r, a) in enumerate(((34, 0.6), (30, 2.4), (36, 4.2), (24, 5.4))):
        x, y = px + r * math.cos(a), py + r * math.sin(a)
        if clear_of(c, x, y, 14.0):
            sc.put(kp.square_tower(c, 8.0, 18.0 + 4 * (k % 2), False, k), x, y, sc.ground(x, y) - 2.0, rot=a, coll="Fortress", r=6.0)
            sc.put(kp.flag_pole(c, "keep_flag_blue", 6.0), x, y, sc.ground(x, y) + 17.0 + 4 * (k % 2), coll="Fortress", role="visual")
    z = sc.ground(px, py)
    sc.put(kp.keep_block(c, 26.0, 18.0, 22.0), px, py, z - 2.0, rot=0.3, coll="Fortress", r=16.0)
    tx, ty = px + 20.0, py - 14.0
    sc.put(kp.square_tower(c, 9.0, 40.0, False, 2), tx, ty, sc.ground(tx, ty) - 2.0, rot=0.3, coll="Fortress", r=7.0)
    sc.put(kp.flag_pole(c, "keep_flag_blue", 8.0), tx, ty, sc.ground(tx, ty) + 39.4, coll="Fortress", role="visual")
    for k in range(4):
        a = k * math.pi / 2 + 0.3
        x, y = tx + 4.6 * math.cos(a), ty + 4.6 * math.sin(a)
        sc.flames.append((x, y, sc.ground(tx, ty) + 41.0))


def far(sc):
    """Far peaks all round, dark, a few with towers."""
    c = sc.c
    for k in range(16):
        a = k * math.tau / 16 + 0.2
        r = 700 + 400 * rnd(k * 3 + 1)
        x, y = 110 + r * math.cos(a), 180 + r * math.sin(a)
        h = 120 + 160 * rnd(k * 3 + 2)
        rk = c.rock_mass("Far Peak %d" % k, x, y, 90 + 60 * rnd(k), 80 + 50 * rnd(k + 9), h, z0=-40.0, n=12, seed=70 + k,
                         bands=[(1.0, 0.0), (0.8, 0.3), (0.6, 0.55), (0.4, 0.8), (0.22, 1.0)])
        rk["kp_role"] = "visual"
        c.paint_rock(rk, ROCK, ROCK)
        if k % 4 == 0:
            sc.put(kp.square_tower(c, 14.0, 30.0, False, k % 3), x, y, h - 8.0, coll="Far", role="visual")


def nature(sc):
    """Pines on the mossy slopes and boulders, clear of the roads and the buildings."""
    c, dk = sc.c, sc.dk
    k = 0
    extra = [dk.SUPPLY, dk.AQUEDUCT]
    for i in range(3000):
        x = -250 + rnd(i * 3 + 1) * 720
        y = -150 + rnd(i * 3 + 2) * 660
        if k > 360:
            break
        if not clear_of(c, x, y, 13.0, extra) or not sc.free(x, y, 6.0):
            continue
        if abs(x - dk.GORGE_X) < 30 and y > 240:
            continue
        if rnd(i * 5 + 7) < 0.3:
            continue
        zz = sc.ground(x, y)
        if rnd(i * 7 + 3) < 0.8:
            h = 8.0 + 8.0 * rnd(i * 11 + 5)
            sc.put(kp.pine(c, k % 3, 10.0), x, y, zz - 0.3, rot=rnd(i) * 6.3, scale=h / 10.0, coll="Nature", r=1.2)
        else:
            sc.put(boulder(c, "ember_rock", k % 3), x, y, zz - 0.4, rot=rnd(i) * 6.3, scale=1.0 + 1.6 * rnd(i * 13 + 1), coll="Nature", r=2.0)
        k += 1


# ------------------------------------------------------------------ light and air


ZONES = {  # the air and sound of each part (game/depths.ts' atmosphere)
    "open": {"fog": "#2c2a3e", "near": 300, "far": 1900, "sun": 1.5, "sky": "#7a7aa8", "ground": "#4a3426", "hemi": 1.15, "sound": "wind"},
    "falls": {"fog": "#30304a", "near": 260, "far": 1700, "sun": 1.4, "sky": "#7a80b0", "ground": "#3a3030", "hemi": 1.1, "sound": "falls"},
    "hall": {"fog": "#2a1a14", "near": 40, "far": 420, "sun": 0.5, "sky": "#e0a070", "ground": "#4a2a1a", "hemi": 1.0, "sound": "drip"},
}


def atmosphere(c, dk, z1, z2):
    S = dk.TO_ROAD
    falls = (S(dk.SEG[20]) - 10, S(dk.SEG[27]))

    def zone(s):
        s %= c.length
        return "falls" if falls[0] <= s <= falls[1] else "open"

    keys = []
    blend = 24.0
    s = 0.0
    while s < c.length:
        q = c.at(s)
        here = zone(s)
        a_, b_, t = here, here, 0.0
        for d in range(2, int(blend) + 1, 2):
            if zone(s + d) != here:
                a_, b_, t = here, zone(s + d), 0.5 * (1.0 - d / blend)
                break
            if zone(s - d) != here:
                a_, b_, t = zone(s - d), here, 0.5 + 0.5 * d / blend
                break
        x, y, z = c.game(q.p.x, q.p.y, q.p.z)
        keys.append([round(x, 1), round(y, 1), round(z, 1), a_, b_, round(t * t * (3 - 2 * t), 3)])
        s += 12.0
    # Inside the hall and the tunnel, on the other roads.
    for pts, (za, zb), frac in ((dk.SUPPLY, z1, 0.55), (dk.AQUEDUCT, z2, 0.5)):
        i = int(frac * (len(pts) - 1))
        for k in range(5):
            u = k / 4
            x, y = lerp(pts[i][0], pts[i + 1][0], u), lerp(pts[i][1], pts[i + 1][1], u)
            gx, gy, gz = c.game(x, y, shortcut_z(pts, za, zb, i, u))
            keys.append([round(gx, 1), round(gy, 1), round(gz, 1), "hall", "hall", 0.0])
    c.entity("atmosphere", zones=ZONES, keys=keys)


def light(sc):
    c = sc.c
    groups = ("Castle", "Gate", "Town", "Approach", "Hall", "Ramparts", "Causeway", "Courtyard", "Tunnel", "Perch", "Fortress", "Nature", "Far")
    c.merge_props(groups, cell=260.0)
    built = [o for name in groups + ("Bridges", "Rocks") for o in c.coll(name).objects if o.type == "MESH" and o.data.users == 1]
    ter = [sc.ter]
    c.preset("sun", ter + built, 0.22)
    # Night: everything a little dim and blue, warm round every flame.
    c.glow(ter + built, [], 1.0, (1, 1, 1), base=(0.66, 0.66, 0.82))
    c.glow(ter + built, sc.flames, 15.0, (1.9, 1.3, 0.75), base=1.0)
    kit.paint.shade_roads(c.pieces + getattr(c, "lanes", []), 0.3)


def build(c, dk, ter, z1, z2, ruin=False):
    """(`ruin`: no bastion's perch (the ruin's bastion is down); returns the scene before
    its lights, for the ruin's dressing.)"""
    kp.use_palette(PALETTE)
    sc = Scene(c, dk, ter)
    gate(sc)
    town(sc)
    approach(sc)
    hall(sc, z1)
    ramparts(sc)
    bridge(sc)
    causeway(sc)
    courtyard(sc)
    tunnel(sc, z2)
    if not ruin:
        perch(sc)
    mountain(sc)
    far(sc)
    nature(sc)
    if ruin:
        return sc
    for x, y, z in sc.flames:
        game_entity(c, "torch", x, y, z)
    for x, y, z, top, w, h in sc.falls:
        gx, gy, gz = c.game(x, y, z)
        c.entity("waterfall", x=gx, y=gy, z=gz, top=round(top, 1), width=round(w, 1), heading=round(h, 3))
    c.entity("storm", period=8.0, spread=4.0, distance=900.0, color="#cfd8ff")
    atmosphere(c, dk, z1, z2)
    light(sc)
    print("ember scenery: props", c.prop_count, "flames", len(sc.flames))
    return sc
