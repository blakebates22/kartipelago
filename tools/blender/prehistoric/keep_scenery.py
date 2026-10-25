# Dragonspire Keep's scenery (see dragon_isles.py): the castle gate, the castle town and
# its walls, the cliff road's parapets and torches, the Waterfall Viaduct's arches and the
# gorge's falls, the courtyard with its fountain under the great keep and the red dragon
# on its tower, the high viaducts' arches and the rock spires' watchtowers, the Beacon
# Tower on the last crag, the docks and boats, the tunnel's portals, the royal approach,
# pines and boulders, the sea of cloud, the light and the air.
# Built from keep_props.py. Nothing here changes the driving: everything solid stands
# clear of the roads (and of the Courtyard Passage); things over a road are visual only.
# SPDX-License-Identifier: MIT

import math

import course_kit as kit
import keep_props as kp
from aurora_scenery import Mesh, falls_sheet, game_entity, road_rot
from course_kit import Vector, bmesh, lerp, rnd
from props import boulder, cuboid

STONE = ("keep_ashlar", "wall")
ACCENT = ("keep_parapet", "wall")
ROCK = ("keep_rock", "wall")


class Scene:
    def __init__(self, c, dk, ter):
        self.c = c
        self.dk = dk
        self.ter = ter
        self.flames = []  # torch and brazier fire (x, y, z): game torches and warm light
        self.falls = []  # (x, y, z, top, width, heading): waterfall entities
        self.solid = []  # (x, y, r): footprints, so scatter keeps clear

    def put(self, proto, x, y, z, rot=0.0, scale=1.0, coll="Castle", role="both", r=0.0):
        if r > 0:
            self.solid.append((x, y, r))
        return self.c.place(proto, x, y, z, rot=rot, scale=scale, coll=coll, role=role)

    def ground(self, x, y):
        z = self.c.ground_z(x, y, [self.ter])
        return z if z is not None else self.dk.natural(x, y)

    def free(self, x, y, r):
        return all(math.hypot(x - a, y - b) > r + rr for a, b, rr in self.solid)


def facing(x, y, tx, ty):
    """The turn that points a prop's front (+Y) from (x, y) toward (tx, ty)."""
    return math.atan2(ty - y, tx - x) - math.pi / 2


def across(q):
    """The turn that lays a prop's X axis across the road at q (gates, arches)."""
    return road_rot(q) - math.pi / 2


def clear_of(c, x, y, margin, extra=()):
    """Far enough from every road (the lap, the Courtyard Passage) and extra polylines?"""
    smp, d = c.nearest(x, y)
    if d < smp.w / 2 + margin:
        return False
    for q in c.extra_ground:
        if (q.p.x - x) ** 2 + (q.p.y - y) ** 2 < (q.w / 2 + margin) ** 2:
            return False
    for pts in extra:
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            dx, dy = bx - ax, by - ay
            t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy + 1e-9)))
            if math.hypot(x - ax - t * dx, y - ay - t * dy) < margin:
                return False
    return True


def near_piece(c, q, x, y):
    """True when the road nearest (x, y) is this stretch (not another part of the lap)."""
    smp, _ = c.nearest(x, y)
    return abs(smp.s - q.s) < 40 or abs(abs(smp.s - q.s) - c.length) < 40


def torch_at(sc, x, y, z, rot=0.0, coll="Castle", role="both"):
    sc.put(kp.torch_post(sc.c), x, y, z, rot=rot, coll=coll, role=role, r=0.6)
    sc.flames.append((x, y, z + 2.9))


def brazier_at(sc, x, y, z, rot=0.0, coll="Castle"):
    sc.put(kp.brazier(sc.c), x, y, z, rot=rot, coll=coll, r=1.3)
    sc.flames.append((x, y, z + 3.2))


def wall_torch_at(sc, x, y, z, rot, coll="Castle"):
    """A torch on a wall at (x, y, z), its front (+Y) out from the wall along `rot`."""
    sc.put(kp.wall_torch(sc.c), x, y, z, rot=rot, coll=coll, role="visual")
    fx, fy = -math.sin(rot) * 0.6, math.cos(rot) * 0.6
    sc.flames.append((x + fx, y + fy, z + 0.8))


# ------------------------------------------------------------------ structures


def arches(c, s0, s1, depth, every=26.0, pier=(4.5, 5.5), name="Viaduct", drop=3.4):
    """Stone arches under a raised road from s0 to s1: a pier every `every` metres down
    `depth` metres, a round arch between each pair (the deck itself is the road's)."""
    m = Mesh()
    L = s1 - s0
    n = max(1, int(round(L / every)))
    for k in range(n + 1):
        q = c.at(s0 + L * k / n)
        top = q.p.z - drop
        m.add(STONE, lambda bm, q=q, top=top: cuboid(bm, (q.p.x, q.p.y, top - depth / 2), (pier[0], pier[1], depth), road_rot(q)))
        m.add(ACCENT, lambda bm, q=q, top=top: cuboid(bm, (q.p.x, q.p.y, top - 1.2), (pier[0] + 1.0, pier[1] + 1.0, 1.0), road_rot(q)))
    for k in range(n):
        a, b = s0 + L * k / n, s0 + L * (k + 1) / n
        half = min(c.at(a).w, c.at(b).w) / 2 + 0.8

        def arc(bm, a=a, b=b, half=half):
            rings = []
            steps = 10
            for j in range(steps + 1):
                t = j / steps
                q = c.at(a + (b - a) * t)
                rise = math.sin(math.pi * t) ** 0.6
                z = q.p.z - drop - (1 - rise) * ((b - a) * 0.5)
                rings.append([bm.verts.new(q.p + q.r * o + Vector((0, 0, z - q.p.z + dz))) for o, dz in ((-half, 0), (half, 0), (half, 1.8), (-half, 1.8))])
            for lo, hi in zip(rings, rings[1:]):
                for i in range(4):
                    bm.faces.new((lo[i], hi[i], hi[(i + 1) % 4], lo[(i + 1) % 4]))

        m.add(STONE, arc)
    return m.build(c, name + " Arches", "Bridges", "visual")


def side_banners(sc, s0, s1, every=24.0, drop=0.6, coll="Bridges"):
    """Dragon banners hung down the outside of a bridge's deck, both sides."""
    c = sc.c
    s = s0 + every / 2
    k = 0
    while s < s1:
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 1.6))
            out = q.r * side
            rot = math.atan2(out.y, out.x) - math.pi / 2
            mat = kp.BANNER if k % 3 else "keep_banner_dark"
            sc.put(kp.wall_banner(c, mat, 2.6, 6.0), p.x, p.y, q.p.z - drop, rot=rot, coll=coll, role="visual")
        s += every
        k += 1


def parapet_torches(sc, s0, s1, every=22.0, out=0.9, coll="Bridges", sides=(-1, 1)):
    """Torch posts just outside a road's parapets."""
    c = sc.c
    s = s0 + 6
    k = 0
    while s < s1:
        q = c.at(s)
        for side in sides:
            if (k + (side > 0)) % 2:
                continue
            p = q.side(side * (q.w / 2 + out + 0.6))
            torch_at(sc, p.x, p.y, q.p.z - 0.1, rot=road_rot(q), coll=coll, role="visual")
        s += every
        k += 1


def wall_line(sc, pts, h=9.0, tower_every=48.0, margin=6.0, coll="Walls", tower_h=14.0, roof=True):
    """A curtain wall along a polyline, towers at the corners and every `tower_every`
    metres; sections too near a road are left out (a breach)."""
    c = sc.c
    done = 0.0
    k = 0
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay)
        n = max(1, int(L / 16.0))
        rot = math.atan2(by - ay, bx - ax)
        for i in range(n):
            t = (i + 0.5) / n
            x, y = lerp(ax, bx, t), lerp(ay, by, t)
            if not clear_of(c, x, y, margin + 2.0):
                continue
            z = sc.ground(x, y)
            sc.put(kp.curtain_wall(c, L / n + 0.3, h), x, y, z, rot=rot, coll=coll, r=0.0)
        for i in range(n + 1):
            if (done + L * i / n) // tower_every != (done + L * max(0, i - 1) / n) // tower_every or i == 0:
                x, y = lerp(ax, bx, i / n), lerp(ay, by, i / n)
                if clear_of(c, x, y, margin + 5.0) and sc.free(x, y, 4.0):
                    z = sc.ground(x, y)
                    sc.put(kp.round_tower(c, 3.6, tower_h + 2 * (k % 2), roof, k % 3), x, y, z, coll=coll, r=4.0)
                    k += 1
        done += L
    x, y = pts[-1]
    if clear_of(c, x, y, margin + 5.0) and sc.free(x, y, 4.0):
        sc.put(kp.round_tower(c, 3.6, tower_h, roof, k % 3), x, y, sc.ground(x, y), coll=coll, r=4.0)


# ------------------------------------------------------------------ the sections


def gate(sc):
    """The Castle Gate over the start: twin towers, the arch with its banners, braziers,
    the town walls running off either side."""
    c, dk = sc.c, sc.dk
    q = c.at(14.0)
    for side in (-1, 1):
        p = q.side(side * (q.w / 2 + 5.0))
        sc.put(kp.round_tower(c, 4.5, 21.0, True, 1 if side > 0 else 2), p.x, p.y, q.p.z - 0.5, coll="Gate", r=4.8)
        for zz in (6.0,):
            for f in (-1, 1):
                w = p - q.r * side * 0.0 + q.t * f * 4.6
                rot = road_rot(q) + (math.pi / 2 if f > 0 else -math.pi / 2)
                wall_torch_at(sc, w.x, w.y, q.p.z + zz, rot, coll="Gate")
        for f in (-1, 1):
            b = q.side(side * (q.w / 2 + 2.5)) + q.t * f * 12.0
            brazier_at(sc, b.x, b.y, sc.ground(b.x, b.y), coll="Gate")
    sc.put(kp.gate_arch(c, q.w + 10.0, 11.5), q.p.x, q.p.y, q.p.z, rot=across(q), coll="Gate", role="visual")
    # Banner poles up the start straight.
    s = 30.0
    while s < dk.SEG[1] - 6:
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 3.0))
            rot = facing(p.x, p.y, q.p.x, q.p.y) + math.pi / 2 * side
            sc.put(kp.banner_pole(c), p.x, p.y, sc.ground(p.x, p.y), rot=road_rot(q) + (0 if side > 0 else math.pi), coll="Gate", r=0.3)
        s += 20.0
    # The town walls: from the gate towers out west and east, then north.
    q = c.at(14.0)
    w0, e0 = q.side(-(q.w / 2 + 9.0)), q.side(q.w / 2 + 9.0)
    wall_line(sc, [(w0.x, w0.y), (w0.x - 50, w0.y), (w0.x - 64, w0.y + 70), (w0.x - 64, w0.y + 200)])
    wall_line(sc, [(e0.x, e0.y), (e0.x + 60, e0.y + 10), (e0.x + 110, e0.y + 60), (e0.x + 150, e0.y + 150)])


def town(sc):
    """The castle town: houses both sides of the streets, facing them, torches and
    barrels at their doors, banners; the market square's dragon statue."""
    c, dk = sc.c, sc.dk
    S = dk.TO_ROAD
    s0, s1 = S(dk.SEG[1]) - 10, S(dk.SEG[7])
    bridge = (S(dk.SEG[4]) - 6, S(dk.SEG[5]) + 6)
    s = s0
    k = 0
    while s < s1:
        q = c.at(s)
        if not (bridge[0] <= s <= bridge[1]):
            for side in (-1, 1):
                off = q.w / 2 + 8.5 + 1.5 * ((k + (side > 0)) % 2)
                p = q.side(side * off)
                if not near_piece(c, q, p.x, p.y) or not clear_of(c, p.x, p.y, 4.5) or not sc.free(p.x, p.y, 4.0):
                    continue
                rot = facing(p.x, p.y, q.p.x, q.p.y)
                z = sc.ground(p.x, p.y)
                sc.put(kp.house(c, (k * 2 + (side > 0)) % 4), p.x, p.y, z - 0.3, rot=rot, coll="Town", r=4.5)
                d = q.side(side * (q.w / 2 + 3.6)) + q.t * 2.0
                if k % 3 == 0:
                    sc.put(kp.barrel(c), d.x, d.y, sc.ground(d.x, d.y), coll="Town", role="visual")
                    e = d + q.t * 1.3
                    sc.put(kp.crate(c), e.x, e.y, sc.ground(e.x, e.y), rot=0.3 * k, coll="Town", role="visual")
                elif k % 3 == 1:
                    w = q.side(side * (off - 3.6))
                    wall_torch_at(sc, w.x, w.y, z + 2.6, rot + math.pi * 0, coll="Town")
        s += 13.0
        k += 1
    # The market square, inside the bend.
    x, y = dk.SQUARE
    sc.put(kp.dragon_statue(c), x, y, sc.ground(x, y), rot=facing(x, y, *dk._seg_point(5)[:2]), coll="Town", r=3.0)
    for a in range(4):
        bx, by = x + 7 * math.cos(a * math.pi / 2 + 0.6), y + 7 * math.sin(a * math.pi / 2 + 0.6)
        if clear_of(c, bx, by, 3.0):
            brazier_at(sc, bx, by, sc.ground(bx, by), coll="Town")
    # Banners across the town bridge's parapets.
    side_banners(sc, bridge[0] + 4, bridge[1] - 4, every=12.0, drop=0.4, coll="Town")


def cliff(sc):
    """The cliff road: torches along the parapets, banners on the bends, a hanging cage
    or two, and the crag's pines."""
    c, dk = sc.c, sc.dk
    S = dk.TO_ROAD
    parapet_torches(sc, S(dk.SEG[7]), S(dk.SEG[12]) - 4, every=18.0, out=1.1, coll="Cliff")
    for s, side in ((S(dk.SEG[8]) + 20, 1), (S(dk.SEG[10]) + 26, -1)):
        q = c.at(s)
        p = q.side(side * (q.w / 2 + 5.5))
        if clear_of(c, p.x, p.y, 3.0):
            sc.put(kp.cage(c), p.x, p.y, sc.ground(p.x, p.y), rot=facing(p.x, p.y, q.p.x, q.p.y), coll="Cliff", r=0.6)


def viaduct(sc):
    """The Waterfall Viaduct: arches down into the gorge either side of the broken
    span, banners down its sides, torches; the falls pouring into the gorge."""
    c, dk = sc.c, sc.dk
    S = dk.TO_ROAD
    lip, land = S(dk.FALLS_LIP), S(dk.FALLS_LAND)
    a0, a1 = S(dk.SEG[12]) + 6, S(dk.SEG[13]) - 4
    arches(c, a0, lip - 1, 44.0, every=20.0, name="Waterfall Viaduct West")
    arches(c, land + 1, a1, 44.0, every=20.0, name="Waterfall Viaduct East")
    side_banners(sc, a0, lip - 4, every=20.0)
    side_banners(sc, land + 4, a1, every=20.0)
    parapet_torches(sc, a0, lip - 6, every=20.0)
    parapet_torches(sc, land + 4, a1, every=20.0)
    # The falls: down both walls of the gorge north of the viaduct, and a great one at
    # its head.
    gx = dk.GORGE_X
    zb = -3.0
    for x, y, w, face in ((gx - 21.0, dk.HIGH_Y + 95, 10.0, (1, 0)), (gx + 21.0, dk.HIGH_Y + 135, 12.0, (-1, 0)), (gx - 20.0, dk.HIGH_Y + 175, 9.0, (1, 0))):
        top = dk.natural(x - face[0] * 8, y) + 0.5
        falls_sheet(c, x, y, top, zb, w, face, mat=("keep_falls", "water"), name="Gorge Falls")
        sc.falls.append((x + face[0] * 3, y, zb, top, w, math.atan2(face[0], face[1])))
    # The head of the gorge: a crag wall across it with the great falls.
    hy = dk.HIGH_Y + 225
    head = c.rock_mass("Gorge Head", gx, hy + 18, 34.0, 14.0, 48.0, z0=-6.0, n=16, seed=21)
    c.paint_rock(head, ROCK, ("keep_grass", "grass"))
    falls_sheet(c, gx, hy + 4, 46.0, zb, 22.0, (0, -1), mat=("keep_falls", "water"), name="Great Falls", bulge=4.0)
    sc.falls.append((gx, hy, zb, 46.0, 22.0, math.pi))
    # Mist over the gorge's river.
    sheet_rect(c, "Gorge Mist", gx - 22, gx + 22, dk.HIGH_Y - 30, hy, 2.5, ("keep_mist", "water"))


def sheet_rect(c, name, x0, x1, y0, y1, z, mat, coll="Water"):
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))]
    bm.faces.new(vs)
    ob = c.mesh_object(name, bm, coll, "visual")
    c.assign(ob, c.lib(*mat))
    return ob


def courtyard(sc):
    """The keep's courtyard: the fountain inside the S (clear of the Courtyard Passage),
    braziers and statues, the castle wall along the crag's rim, and north of it all the
    great keep, its towers and the Dragon Tower with the red dragon on top."""
    c, dk = sc.c, sc.dk
    tx, ty = dk.TEMPLE
    fy = ty - 15.5
    z = sc.ground(tx, fy)
    sc.put(kp.fountain(c), tx, fy, z, rot=math.pi, coll="Courtyard", r=5.2)
    game_entity(c, "fountain", tx, fy, z + 3.9, height=3.0, jets=6, radius=3.2)
    for dx, dy in ((-13, -2), (13, -2)):
        x, y = tx + dx, fy + dy
        if clear_of(c, x, y, 2.5, [dk.COURTYARD]):
            brazier_at(sc, x, y, sc.ground(x, y), coll="Courtyard")
    # Statues at the passage's ends, looking down it.
    for (x, y), (fx, fy2) in ((dk.COURTYARD[0], dk.COURTYARD[1]), (dk.COURTYARD[-1], dk.COURTYARD[1])):
        for side in (-1, 1):
            px, py = x, y + side * 10.0
            if clear_of(c, px, py, 3.0, [dk.COURTYARD]):
                sc.put(kp.dragon_statue(c), px, py, sc.ground(px, py), rot=facing(px, py, fx, fy2), coll="Courtyard", r=2.8)
    # The rim wall: along the crag south of the courtyard, seen from the valley.
    rim = dk.HIGH_Y + 2.0
    wall_line(sc, [(118.0, rim), (160.0, rim - 4), (230.0, rim - 4), (268.0, rim + 6)], h=10.0, tower_every=36.0, coll="Courtyard", tower_h=16.0)
    # The great keep and its towers, north of the road.
    kx, ky = tx, ty + 62.0
    kz = sc.ground(kx, ky)
    sc.put(kp.keep_block(c, 40.0, 24.0, 28.0), kx, ky, kz, coll="Keep", r=24.0)
    for dx, dy, h, rf in ((-30, -14, 30.0, True), (30, -14, 30.0, True), (-30, 16, 26.0, True)):
        x, y = kx + dx, ky + dy
        sc.put(kp.square_tower(c, 9.0, h, rf, 0), x, y, sc.ground(x, y), coll="Keep", r=7.0)
    # The Dragon Tower: tall, open-topped, the dragon perched on it looking out over the
    # courtyard towards the viaduct.
    dx_, dy_ = kx + 34.0, ky + 18.0
    dz = sc.ground(dx_, dy_)
    TH = 48.0
    sc.put(kp.round_tower(c, 7.5, TH, False, 0), dx_, dy_, dz, coll="Keep", r=8.0)
    look = facing(dx_, dy_, dk.GORGE_X + 40, dk.HIGH_Y + 30)
    sc.put(kp.great_dragon(c), dx_, dy_ + 1.0, dz + TH + 0.6, rot=look, scale=1.25, coll="Keep", role="visual")
    for k in range(4):
        a = k * math.pi / 2 + 0.3
        bx, by = dx_ + 6.2 * math.cos(a), dy_ + 6.2 * math.sin(a)
        sc.flames.append((bx, by, dz + TH + 2.2))
        sc.put(kp.torch_post(c, 1.6), bx, by, dz + TH + 0.6, coll="Keep", role="visual")
    # Curtain walls linking the keep's towers, and flags on the ramparts.
    wall_line(sc, [(kx - 30, ky - 14), (kx - 70, ky - 20), (kx - 96, ky + 10)], h=11.0, tower_every=40.0, coll="Keep", tower_h=18.0)
    wall_line(sc, [(kx + 30, ky - 14), (kx + 74, ky - 24), (kx + 92, ky + 6)], h=11.0, tower_every=40.0, coll="Keep", tower_h=18.0)
    for dx, dy in ((-30, -14), (30, -14)):
        x, y = kx + dx, ky + dy
        sc.put(kp.flag_pole(c), x + 2, y + 2, sc.ground(x, y) + 31.4, coll="Keep", role="visual")


def high_viaducts(sc):
    """The sky paths: arches down to the lake between the piers, banners and torches; the
    rock spires either side crowned with watchtowers."""
    c, dk = sc.c, sc.dk
    S = dk.TO_ROAD
    lip, land = S(dk.SKY_LIP), S(dk.SKY_LAND)
    s0, s1 = S(dk.SEG[17]) + 20, S(dk.SEG[23])
    arches(c, s0, lip - 1, 48.0, every=26.0, pier=(5.0, 6.0), name="High Viaduct North")
    arches(c, land + 1, s1, 48.0, every=26.0, pier=(5.0, 6.0), name="High Viaduct South")
    side_banners(sc, s0, lip - 4, every=26.0)
    side_banners(sc, land + 4, s1, every=26.0)
    parapet_torches(sc, s0, lip - 6, every=26.0)
    parapet_torches(sc, land + 4, s1, every=26.0)
    # Watchtowers on some of the rock spires (the course's own loop of spires).
    for k in range(9):
        d = dk.SEG[18] + (dk.SEG[23] - dk.SEG[18]) * (k + 0.5) / 9
        q = c.at(dk.TO_ROAD(d))
        for side in (-1, 1):
            if (k + (side > 0)) % 3:
                continue
            p = q.side(side * (q.w / 2 + 16.0 + 6 * (k % 2)))
            top = q.p.z + 10 + 8 * ((k + side) % 3)
            sc.put(kp.round_tower(c, 3.2, 9.0, True, k % 3), p.x, p.y, top - 0.8, coll="Spires", role="visual")
            sc.put(kp.flag_pole(c, "keep_banner" if k % 2 else "keep_flag_blue", 5.0), p.x + 1.5, p.y, top + 9.0, coll="Spires", role="visual")


def beacon(sc):
    """The Beacon Tower on the last great crag, its fire burning on top; arches under the
    spiral; banners on its parapet."""
    import bpy

    c, dk = sc.c, sc.dk
    S = dk.TO_ROAD
    x, y = dk.SPIRE
    rock = bpy.data.objects.get("Great Pillar")
    z = c.ground_z(x, y, [rock]) if rock else 60.0
    z = z if z is not None else 60.0
    sc.put(kp.round_tower(c, 6.0, 14.0, False, 1), x, y, z - 1.0, coll="Beacon", role="visual")
    sc.put(kp.brazier(c), x, y, z + 13.6, scale=1.8, coll="Beacon", role="visual")
    sc.flames.append((x, y, z + 13.6 + 5.0))
    for k in range(4):
        a = k * math.pi / 2
        sc.put(kp.wall_banner(c, kp.BANNER, 3.0, 7.0), x + 6.1 * math.cos(a), y + 6.1 * math.sin(a), z + 11.5, rot=a - math.pi / 2, coll="Beacon", role="visual")
    a0, a1 = S(dk.SEG[23]) + 10, S(dk.SEG[24]) - 30
    s = a0
    while s < a1:
        q = c.at(s)
        if q.p.z > 10:
            arches(c, s, min(a1, s + 60), max(4.0, q.p.z + 2.0), every=20.0, pier=(3.5, 4.5), name="Spiral", drop=3.0)
        s += 60
    parapet_torches(sc, a0, S(dk.SEG[24]) - 4, every=24.0, sides=(1,), coll="Beacon")


def harbour(sc):
    """The lakeside docks: houses on the shore side, jetties out into the lake with boats
    tied up, barrels and crates, torches."""
    c, dk = sc.c, sc.dk
    S = dk.TO_ROAD
    s0, s1 = S(dk.SEG[24]) + 6, S(dk.SEG[28]) + 10
    s = s0
    k = 0
    while s < s1:
        q = c.at(s)
        p = q.side(-(q.w / 2 + 9.5))
        if clear_of(c, p.x, p.y, 4.5) and sc.free(p.x, p.y, 4.5):
            sc.put(kp.house(c, k % 4), p.x, p.y, sc.ground(p.x, p.y) - 0.3, rot=facing(p.x, p.y, q.p.x, q.p.y), coll="Harbour", r=4.5)
        # A jetty out into the lake on the other side, every other house.
        if k % 2 == 0 and s < S(dk.SEG[27]):
            a = q.side(q.w / 2 + 2.5)
            out = q.r
            m = Mesh()
            for j in range(4):
                b = a + out * (3.5 + j * 3.5)
                m.add(("keep_dock", "road"), lambda bm, b=b: cuboid(bm, (b.x, b.y, 1.0), (3.6, 3.4, 0.4), road_rot(q)))
                m.add(("weathered_timber", "wall"), lambda bm, b=b: cuboid(bm, (b.x, b.y, -1.5), (0.5, 0.5, 5.0), road_rot(q)))
            m.build(c, "Jetty", "Harbour", "visual")
            bt = a + out * 9.0 + q.t * 4.2
            sc.put(kp.boat(c, k // 2), bt.x, bt.y, -0.3, rot=math.atan2(out.y, out.x) - math.pi / 2, coll="Harbour", role="visual")
            e = a + out * 13.0
            sc.put(kp.barrel(c), e.x, e.y, 1.2, coll="Harbour", role="visual")
            sc.put(kp.crate(c), e.x + 1.2, e.y + 0.4, 1.2, rot=0.4, coll="Harbour", role="visual")
            torch_at(sc, (a + out * 1.0).x, (a + out * 1.0).y, q.p.z - 0.2, coll="Harbour", role="visual")
        s += 16.0
        k += 1


def passage(sc):
    """The tunnel through the headland: a stone portal at each end with banners and
    torches, torches along its walls inside."""
    c, dk = sc.c, sc.dk
    S = dk.TO_ROAD
    t0, t1 = S(dk.SEG[29] - 8), S(dk.SEG[30] + 14)
    for s, flip in ((t0, 0.0), (t1, math.pi)):
        q = c.at(s)
        sc.put(kp.stone_arch(c, 26.0, 13.0, 4.0), q.p.x, q.p.y, q.p.z, rot=across(q) + flip, coll="Passage", role="visual")
        for side in (-1, 1):
            p = q.side(side * 11.6) - q.t * (2.6 if flip == 0 else -2.6)
            rot = road_rot(q) + (math.pi / 2 if flip == 0 else -math.pi / 2)
            wall_torch_at(sc, p.x, p.y, q.p.z + 3.0, rot - math.pi, coll="Passage")
            b = q.side(side * 7.0) - q.t * (2.3 if flip == 0 else -2.3)
            sc.put(kp.wall_banner(c, kp.BANNER, 2.4, 5.0), b.x, b.y, q.p.z + 14.0, rot=rot - math.pi, coll="Passage", role="visual")
    s = t0 + 12
    k = 0
    while s < t1 - 8:
        q = c.at(s)
        side = 1 if k % 2 else -1
        p = q.side(side * (c.width / 2 + 2.0))
        out = q.r * -side
        wall_torch_at(sc, p.x, p.y, q.p.z + 3.2, math.atan2(out.y, out.x) - math.pi / 2, coll="Passage")
        s += 12.0
        k += 1


def royal(sc):
    """The royal approach: banner poles and torches down both sides of the carpet, a
    triumphal arch over it, dragon statues at the overlook."""
    c, dk = sc.c, sc.dk
    S = dk.TO_ROAD
    s0, s1 = S(dk.SEG[31]) + 20, c.length - 8
    s = s0
    k = 0
    while s < s1:
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 3.2))
            if not clear_of(c, p.x, p.y, 2.0):
                continue
            if k % 2 == 0:
                sc.put(kp.banner_pole(c, kp.BANNER, 8.0), p.x, p.y, sc.ground(p.x, p.y), rot=road_rot(q) + (0 if side > 0 else math.pi), coll="Royal", r=0.3)
            else:
                torch_at(sc, p.x, p.y, sc.ground(p.x, p.y), rot=road_rot(q), coll="Royal")
        s += 9.0
        k += 1
    q = c.at(S(dk.SEG[32]) + 4)
    sc.put(kp.stone_arch(c, q.w + 8.0, 13.0, 4.0), q.p.x, q.p.y, q.p.z, rot=across(q), coll="Royal", role="visual")
    q = c.at(S(dk.SEG[31]) + 8)
    for side in (-1, 1):
        p = q.side(side * (q.w / 2 + 6.0))
        if clear_of(c, p.x, p.y, 3.0):
            sc.put(kp.dragon_statue(c), p.x, p.y, sc.ground(p.x, p.y), rot=facing(p.x, p.y, q.p.x, q.p.y), coll="Royal", r=2.8)


def nature(sc):
    """Pines on the grass and boulders on the slopes, clear of the roads and the
    buildings."""
    c, dk = sc.c, sc.dk
    k = 0
    for i in range(2600):
        x = -200 + rnd(i * 3 + 1) * 740
        y = -300 + rnd(i * 3 + 2) * 800
        if k > 420:
            break
        z = dk.natural(x, y)
        if z < 1.8 or dk.in_drop(x, y, z):
            continue
        if not clear_of(c, x, y, 14.0, [dk.COURTYARD]) or not sc.free(x, y, 6.0):
            continue
        # Fewer on the highland behind the keep, more on the crag and in the valley.
        if rnd(i * 5 + 7) < 0.35:
            continue
        zz = sc.ground(x, y)
        if rnd(i * 7 + 3) < 0.82:
            h = 8.0 + 7.0 * rnd(i * 11 + 5)
            sc.put(kp.pine(c, k % 3, 10.0), x, y, zz - 0.3, rot=rnd(i) * 6.3, scale=h / 10.0, coll="Nature", r=1.2)
        else:
            sc.put(boulder(c, "keep_rock", k % 3), x, y, zz - 0.4, rot=rnd(i) * 6.3, scale=1.0 + 1.6 * rnd(i * 13 + 1), coll="Nature", r=2.0)
        k += 1


def clouds(sc):
    """The sea of cloud round the kingdom, just under the valley's rim, out to the
    horizon, and far crags standing out of it, some with towers."""
    c = sc.c
    X0, X1, Y0, Y1 = -220, 560, -320, 520
    R = 2600.0
    z = 1.2
    bm = bmesh.new()
    inner = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]
    outer = [(-R, -R), (R, -R), (R, R), (-R, R)]
    vi = [bm.verts.new((x, y, z)) for x, y in inner]
    vo = [bm.verts.new((x, y, z)) for x, y in outer]
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((vo[i], vo[j], vi[j], vi[i]))
    ob = c.mesh_object("Cloud Sea", bm, "Water", "visual")
    c.assign(ob, c.lib("keep_cloud", "water"))
    for k in range(14):
        a = k * math.tau / 14 + 0.3
        r = 900 + 500 * rnd(k * 3 + 1)
        x, y = 170 + r * math.cos(a), 100 + r * math.sin(a)
        h = 60 + 110 * rnd(k * 3 + 2)
        rk = c.rock_mass("Far Crag %d" % k, x, y, 40 + 30 * rnd(k), 36 + 30 * rnd(k + 9), h, z0=-20.0, n=12, seed=40 + k)
        rk["kp_role"] = "visual"
        c.paint_rock(rk, ROCK, ("keep_grass", "grass"))
        if k % 3 == 0:
            sc.put(kp.round_tower(c, 6.0, 26.0, True, k % 3), x, y, h - 6.0, scale=1.4, coll="Far", role="visual")


# ------------------------------------------------------------------ light and air


ZONES = {  # the air and sound of each part (game/depths.ts' atmosphere)
    "open": {"fog": "#c4849a", "near": 420, "far": 2600, "sun": 2.5, "sky": "#b49ad8", "ground": "#5a4048", "hemi": 1.2, "sound": "wind"},
    "falls": {"fog": "#c890a8", "near": 380, "far": 2400, "sun": 2.4, "sky": "#b8a0dc", "ground": "#5a4850", "hemi": 1.2, "sound": "falls"},
    "harbour": {"fog": "#c4849a", "near": 420, "far": 2600, "sun": 2.5, "sky": "#b49ad8", "ground": "#5a4850", "hemi": 1.2, "sound": "harbour"},
    "tunnel": {"fog": "#2a1a1c", "near": 30, "far": 380, "sun": 0.45, "sky": "#d89a6a", "ground": "#3a2420", "hemi": 0.85, "sound": "drip"},
}


def atmosphere(c, dk):
    S = dk.TO_ROAD
    tunnel = (S(dk.SEG[29] - 10), S(dk.SEG[30] + 16))
    falls = (S(dk.SEG[11]) + 20, S(dk.SEG[13]))
    harbour = (S(dk.SEG[24]), S(dk.SEG[28]) + 30)

    def zone(s):
        s %= c.length
        if tunnel[0] <= s <= tunnel[1]:
            return "tunnel"
        if falls[0] <= s <= falls[1]:
            return "falls"
        if harbour[0] <= s <= harbour[1]:
            return "harbour"
        return "open"

    keys = []
    blend = 24.0
    s = 0.0
    while s < c.length:
        q = c.at(s)
        here = zone(s)
        after = before = here
        da = db = None
        d = 0.0
        while d < blend:
            d += 2.0
            if da is None and zone(s + d) != here:
                da, after = d, zone(s + d)
            if db is None and zone(s - d) != here:
                db, before = d, zone(s - d)
        if da is not None and (db is None or da <= db):
            a_, b_, t = here, after, 0.5 * (1.0 - da / blend)
        elif db is not None:
            a_, b_, t = before, here, 0.5 + 0.5 * db / blend
        else:
            a_, b_, t = here, here, 0.0
        x, y, z = c.game(q.p.x, q.p.y, q.p.z)
        keys.append([round(x, 1), round(y, 1), round(z, 1), a_, b_, round(t * t * (3 - 2 * t), 3)])
        s += 12.0
    c.entity("atmosphere", zones=ZONES, keys=keys)


def light(sc):
    c, dk = sc.c, sc.dk
    groups = ("Castle", "Gate", "Town", "Cliff", "Courtyard", "Keep", "Walls", "Spires", "Beacon", "Harbour", "Passage", "Royal", "Nature", "Far")
    c.merge_props(groups, cell=260.0)
    built = [o for name in groups + ("Bridges", "Rocks") for o in c.coll(name).objects if o.type == "MESH" and o.data.users == 1]
    ter = [sc.ter]
    c.preset("sun", ter + built, 0.3)
    S = dk.TO_ROAD
    t0, t1 = S(dk.SEG[29] - 10), S(dk.SEG[30] + 16)

    def in_tunnel(w):
        smp, d = c.nearest(w.x, w.y)
        return d < 18 and t0 < smp.s < t1 and w.z < smp.p.z + 12

    c.glow(ter + built, [], 1.0, (1, 1, 1), base=(0.5, 0.42, 0.42), region=in_tunnel)
    c.glow(ter + built, sc.flames, 13.0, (1.6, 1.15, 0.7), base=1.0)
    kit.paint.shade_roads(c.pieces + getattr(c, "lanes", []), 0.3)


def build(c, dk, ter):
    sc = Scene(c, dk, ter)
    gate(sc)
    town(sc)
    cliff(sc)
    viaduct(sc)
    courtyard(sc)
    high_viaducts(sc)
    beacon(sc)
    harbour(sc)
    passage(sc)
    royal(sc)
    clouds(sc)
    nature(sc)
    for x, y, z in sc.flames:
        game_entity(c, "torch", x, y, z)
    for x, y, z, top, w, h in sc.falls:
        gx, gy, gz = c.game(x, y, z)
        c.entity("waterfall", x=gx, y=gy, z=gz, top=round(top, 1), width=round(w, 1), heading=round(h, 3))
    atmosphere(c, dk)
    light(sc)
    print("keep scenery: props", c.prop_count, "flames", len(sc.flames))
