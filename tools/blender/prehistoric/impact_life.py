# Impact Depths' landmarks and life (see impact_depths_v2.py): the shortcut's causeway, each
# region's dressing (the desert outpost, the asteroid and its crater, the crystal halls,
# the Lost World's plants and ruins, the volcanic depths, the dragon's crag, the core's
# chamber, the ascent), the creatures' paths, and the gameplay entities.
# SPDX-License-Identifier: MIT

import math

import aurora_props as ap
import canyon_props as cp
import impact_land as L
import impact_props as ip
import props as pr
import volcano_props as vp
from canyon_scenery import Mesh, portal
from course_kit import Vector, bmesh, lerp, rnd
from impact_scenery import clear, game_entity
from props import cuboid

S = L.S


def road_rot(q):
    return math.atan2(q.t.y, q.t.x)


# ------------------------------------------------------------------ where things can go


def floor_z(c, sc, x, y):
    """The land's height straight below (x, y) (the cave floor under a roof)."""
    z = c.ground_z(x, y, sc.ground_obs)
    return z if z is not None else sc.info(x, y)[0]


def top_z(c, sc, x, y):
    """The top surface at (x, y): the desert over a cave, or the land where open."""
    z = c.ground_z(x, y, [sc.land, sc.over])
    return z if z is not None else L.natural(x, y)


def where(sc, x, y):
    """(biome, covered, roof, top, natural floor) of a spot."""
    z, (b, cov, roof, top) = sc.info(x, y)
    return b, cov, roof, top, z


def slope_ok(sc, x, y, rise=2.5, d=3.0):
    z0 = sc.info(x, y)[0]
    return all(abs(sc.info(x + dx, y + dy)[0] - z0) < rise for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d)))


def in_any_water(x, y, margin=2.0):
    return any(w.get("lair") is None and L.in_water(w, x, y, margin) > 0 for w in L.WATERS)


def scatter(c, sc, protos, n, area, ok, seed, scale=(0.8, 1.3), coll="Plants", role="visual", sink=0.25, gap=3.0, tries=30, hang=False,
            top=False):
    """Up to n copies of the protos (picked in turn) at random spots in `area` where
    ok(x, y, z) holds: on the land (the cave floor), on the top surface (`top`), or
    hanging from the caves' roof (`hang`: z is the roof)."""
    x0, x1, y0, y1 = area
    placed = []
    k = 0
    while len(placed) < n and k < n * tries:
        k += 1
        x = x0 + (x1 - x0) * rnd(k * 1.31 + seed * 7.7)
        y = y0 + (y1 - y0) * rnd(k * 2.17 + seed * 3.3)
        if any((x - px) ** 2 + (y - py) ** 2 < gap * gap for px, py in placed):
            continue
        if hang:
            b, cov, roof, tp, fz = where(sc, x, y)
            if not cov:
                continue
            z = roof
        else:
            z = top_z(c, sc, x, y) if top else floor_z(c, sc, x, y)
        if z is None or not ok(x, y, z):
            continue
        s = scale[0] + (scale[1] - scale[0]) * rnd(k * 5.9 + seed)
        proto = protos[len(placed) % len(protos)]
        c.place(proto, x, y, z + (0.0 if hang else -sink), rot=rnd(k * 3.7 + seed) * math.tau, scale=s, role=role, coll=coll)
        placed.append((x, y))
    return placed


def cave_ok(c, sc, biome, margin=6.0, dry=True, flat=True, room=0.0):
    """A test for scatter: on this biome's cave floor, clear of the roads (and the water,
    and steep ground), with `room` metres of headroom."""
    def ok(x, y, z):
        b, cov, roof, top, fz = where(sc, x, y)
        if b != biome or z > top - 4.0:
            return False
        if roof - z < room:
            return False
        if dry and in_any_water(x, y, 1.0):
            return False
        if flat and not slope_ok(sc, x, y):
            return False
        return clear(c, x, y, margin)
    return ok


def hang_ok(c, sc, biome, length, margin=4.0):
    """For things hanging from a roof: this biome, high enough over the road and floor."""
    def ok(x, y, z):
        b, cov, roof, top, fz = where(sc, x, y)
        if b != biome:
            return False
        smp, d = c.nearest(x, y)
        clearance = z - (smp.p.z if d < smp.w / 2 + margin + 6 else fz)
        if clearance < length + 7.0:
            return False
        return all((q.p.x - x) ** 2 + (q.p.y - y) ** 2 > (q.w / 2 + margin) ** 2 or z - q.p.z > length + 8 for q in c.extra_ground[::6])
    return ok


def area_of(biome):
    xs, ys = [], []
    for t in L.TUBES:
        if t.biome != biome:
            continue
        for n in t.nodes:
            xs += [n[0] - n[2], n[0] + n[2]]
            ys += [n[1] - n[2], n[1] + n[2]]
    return (min(xs), max(xs), min(ys), max(ys))


# ------------------------------------------------------------------ the Ancient Way


def shortcut(c, sc):
    """The shortcut's road: through the gateway, along the causeway over the black pool,
    round onto the volcanic causeway."""
    import dry_gulch_v2 as dry_gulch  # lane() lives with the first Dry Gulch lap

    n = len(L.SHORTCUT_LINE)
    pts = [(x, y, L.shortcut_z(i / (n - 1))) for i, (x, y) in enumerate(L.SHORTCUT_LINE)]
    sc.short_pts = pts
    dry_gulch.lane(c, "Ancient Way", pts, "causeway_stone", "road", width=11.0, shoulder=1.0,
                   shoulder_mat=("ruin_moss", "dirt"), step=4.0)
    return pts


# ------------------------------------------------------------------ 1  the desert approach


def desert(c, sc):
    """The start: a rustic timber arch over the line, banners and braziers, the
    expedition's camp on the crater's rim, a natural arch over the last curve, and the
    desert's plants and rocks round the mesas."""
    m = Mesh()
    q = c.at(12.0)
    portal(c, sc, m, q, h=10.0, banners=False, post=1.2)
    rot = road_rot(q)
    for o in (-6.5, 6.5):
        p = q.side(o)
        m.add(("meteor_banner", "wall"), lambda bm, p=p, z=q.p.z: cuboid(bm, (p.x, p.y, z + 7.6), (0.1, 3.4, 4.2), rot + math.pi / 2))
    p = q.side(0)
    m.add(("start_checker", "wall"), lambda bm, p=p, z=q.p.z: cuboid(bm, (p.x, p.y, z + 11.8), (0.16, 9.0, 1.8), rot + math.pi / 2))
    m.build(c, "Start Arch", "Outpost", "visual")
    for k, s in enumerate((-70.0, -45.0, 40.0, 70.0, 100.0)):
        q = c.at(s % c.length)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 3.5))
            c.place(cp.banner_pole(c, (k + (side > 0)) % 2), p.x, p.y, q.p.z - 0.2, rot=road_rot(q) + (math.pi if side < 0 else 0.0),
                    coll="Outpost", role="both")
    for s in (-14.0, 22.0):
        q = c.at(s % c.length)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 2.4))
            c.place(cp.brazier(c), p.x, p.y, q.p.z - 0.1, coll="Outpost", role="both")
    # The expedition's camp on the rim, its telescope trained on the asteroid.
    camp = c.at(S[1] - 40).side(-(c.at(S[1] - 40).w / 2 + 26.0))
    cx, cy = camp.x, camp.y
    sc.footprints.append((cx, cy, 24.0))
    aim = math.atan2(L.ASTEROID[1] - cy, L.ASTEROID[0] - cx)
    for k, (dx, dy, r) in enumerate(((-8, 6, 0.3), (2, 10, -0.2), (10, 4, 0.5))):
        c.place(ip.tent(c, k), cx + dx, cy + dy, top_z(c, sc, cx + dx, cy + dy) - 0.1, rot=r, coll="Outpost", role="both")
    c.place(ip.survey_scope(c), cx + 6, cy - 6, top_z(c, sc, cx + 6, cy - 6), rot=aim, coll="Outpost", role="both")
    for k, (dx, dy) in enumerate(((-3, -4), (14, -2), (-12, -2))):
        c.place(cp.crates(c, k % 2), cx + dx, cy + dy, top_z(c, sc, cx + dx, cy + dy) - 0.1, rot=k, coll="Outpost", role="both")
    c.place(cp.lookout_tower(c), cx - 18, cy + 14, top_z(c, sc, cx - 18, cy + 14) - 0.3, rot=0.4, coll="Outpost", role="both")
    c.place(cp.water_tank(c), cx + 20, cy + 16, top_z(c, sc, cx + 20, cy + 16) - 0.3, coll="Outpost", role="both")
    # Warning boards along the rim and the descent's outer edge.
    for k, s in enumerate((S[1] + 20, S[1] + 70, S[1] + 130, S[1] + 190, S[2] + 40)):
        q = c.at(s)
        p = q.side(-(q.w / 2 + 3.5))
        c.place(ip.warning_sign(c, k), p.x, p.y, top_z(c, sc, p.x, p.y) - 0.2, rot=road_rot(q), coll="Outpost", role="both")
    # A natural arch over the final curve, out of the shaft into the sun.
    from canyon_scenery import arch

    q = c.at(S[20] + 6)
    ax = (q.r.x, q.r.y)
    z0 = q.p.z - 3.0
    arch(c, _Strata(), "Sun Arch", (q.p.x, q.p.y), ax, q.w + 14.0, 15.0, z0, 9.0, 7.0, seed=3, coll="Rocks", role="both")
    sc.footprints.append((q.p.x + q.r.x * (q.w / 2 + 11), q.p.y + q.r.y * (q.w / 2 + 11), 8.0))
    sc.footprints.append((q.p.x - q.r.x * (q.w / 2 + 11), q.p.y - q.r.y * (q.w / 2 + 11), 8.0))
    # A second, broken arch on the plain north of the straight (a landmark from the line).
    arch(c, _Strata(), "Old Arch", (120.0, 92.0), (1.0, 0.25), 46.0, 24.0, L.desert(120.0, 92.0) - 2.0, 10.0, 8.0, seed=7, coll="Rocks",
         role="both")
    sc.footprints.append((120.0, 92.0, 30.0))
    # Plants and rocks on the desert (over the caves too), clear of the roads and pits.
    def ok(x, y, z):
        if math.hypot(x - L.CRATER[0], y - L.CRATER[1]) < L.CRATER_LIP + 10:
            return False
        if math.hypot(x - L.SHAFT[0], y - L.SHAFT[1]) < L.SHAFT_R + 12:
            return False
        if L.mesa_h(x, y) > 1.0 or abs(z - L.desert(x, y)) > 3.0:
            return False
        if any(math.hypot(x - sx, y - sy) < r + 6 for sx, sy, r in L.SKYLIGHTS):
            return False
        return clear(c, x, y, 7.0) and c.nearest(x, y)[1] < 170.0 and sc.free(x, y, 4.0)

    area = (-520.0, 520.0, -700.0, 170.0)
    scatter(c, sc, [cp.saguaro(c, k) for k in range(4)], 70, area, ok, 11, top=True, gap=9.0)
    scatter(c, sc, [cp.agave(c, k) for k in range(2)] + [cp.sagebrush(c, k) for k in range(2)], 100, area, ok, 13, top=True)
    scatter(c, sc, [cp.dry_grass(c, k) for k in range(2)], 60, area, ok, 17, top=True, gap=2.0)
    scatter(c, sc, [cp.barrel_cactus(c, k) for k in range(2)], 30, area, ok, 19, top=True)
    scatter(c, sc, [cp.boulder(c, k) for k in range(3)], 80, area, ok, 23, top=True, coll="Rocks", role="both", scale=(1.0, 2.4))
    scatter(c, sc, [cp.hoodoo(c, k, 12.0 + 4 * k) for k in range(3)], 18, area, lambda x, y, z: ok(x, y, z) and clear(c, x, y, 26.0), 29,
            top=True, coll="Rocks", role="both", gap=40.0, scale=(0.8, 1.2))
    scatter(c, sc, [cp.joshua_tree(c, k) for k in range(2)], 20, area, ok, 31, top=True, gap=14.0)


class _Strata:
    """What canyon_scenery's rock painters need from a course: the rock's layers."""

    @staticmethod
    def _layer(z):
        from impact_scenery import strata

        return strata(z)


# ------------------------------------------------------------------ 2  the crater and the asteroid


def asteroid(c, sc):
    """The asteroid itself: a vast, pitted, iron-dark rock half buried in the crater's
    floor, split by glowing cracks; meteorites and impact glass round it, glowing
    fissures across the floor."""
    ax, ay = L.ASTEROID
    bm = bmesh.new()
    res = bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
    R = 46.0
    for v in res["verts"]:
        d = v.co.normalized()
        k = 1.0 + 0.16 * math.sin(d.x * 4.1 + 1.0) * math.cos(d.y * 3.3) + 0.1 * math.sin(d.z * 6.1 + d.x * 2.0) + 0.05 * math.sin(d.y * 11.0)
        # Big impact pits.
        for px, py, pz, pr_ in ((0.6, 0.5, 0.6, 0.35), (-0.7, 0.2, 0.7, 0.3), (0.1, -0.8, 0.6, 0.28)):
            dd = (d - Vector((px, py, pz)).normalized()).length
            if dd < pr_:
                k -= 0.12 * (1 - (dd / pr_) ** 2)
        v.co = Vector((ax + d.x * R * 1.15 * k, ay + d.y * R * k, L.CRATER_FLOOR + 2.0 + d.z * R * 0.9 * k))
    bm.faces.ensure_lookup_table()
    hot, cold = [], []
    for f in bm.faces:
        cn = f.calc_center_median()
        u = math.sin((cn.x - ax) * 0.23 + (cn.z) * 0.11) + math.cos((cn.y - ay) * 0.19 - cn.z * 0.07)
        (hot if abs(u) < 0.08 else cold).append(f.index)
    ob = c.mesh_object("Asteroid", bm, "Landmarks", "both")
    c.assign(ob, c.lib("asteroid_rock"), cold)
    c.assign(ob, c.lib("asteroid_vein"), hot)
    ob.data.shade_flat()
    top = L.CRATER_FLOOR + 2.0 + R * 0.9 * 1.1
    sc.asteroid_top = top
    sc.footprints.append((ax, ay, R * 1.3))
    for k in range(10):
        a = k * math.tau / 10
        sc.light("asteroid", ax + math.cos(a) * R * 1.1, ay + math.sin(a) * R, L.CRATER_FLOOR + 6.0)
    sc.light("asteroid", ax, ay, top)
    # Glowing fissures across the floor and up the walls, radiating from the asteroid.
    fiss = Mesh()
    for k in range(16):
        a = k * math.tau / 16 + 0.2 * math.sin(k * 3.1)
        r0 = R * 1.1
        r1 = r0 + 40.0 + 70.0 * rnd(k * 7)
        pts = []
        n = 14
        for j in range(n + 1):
            t = j / n
            r = lerp(r0, r1, t)
            aa = a + 0.18 * math.sin(t * 6 + k)
            pts.append((ax + r * math.cos(aa), ay + r * math.sin(aa)))
        w0 = 2.6 - 1.4 * rnd(k)
        for j, ((x0, y0), (x1, y1)) in enumerate(zip(pts, pts[1:])):
            t = j / n
            w = w0 * (1 - t) + 0.3
            nx, ny = -(y1 - y0), x1 - x0
            ln = math.hypot(nx, ny) or 1
            nx, ny = nx / ln * w / 2, ny / ln * w / 2
            if not clear(c, (x0 + x1) / 2, (y0 + y1) / 2, 3.0):
                continue
            q = [(x0 - nx, y0 - ny), (x1 - nx, y1 - ny), (x1 + nx, y1 + ny), (x0 + nx, y0 + ny)]
            zs = [floor_z(c, sc, *p) + 0.12 for p in q]
            fiss.add(("impact_glow", "wall"), lambda bm, q=q, zs=zs: bm.faces.new([bm.verts.new((p[0], p[1], z)) for p, z in zip(q, zs)]))
            if j % 4 == 0:
                sc.light("asteroid", (x0 + x1) / 2, (y0 + y1) / 2, zs[0] + 2)
    fiss.build(c, "Fissures", "Landmarks", "visual")
    # Meteorites, impact glass, slumped boulders over the floor and the terraces.
    def ok(x, y, z):
        r = math.hypot(x - L.CRATER[0], y - L.CRATER[1])
        return r < L.CRATER_R1 - 6 and clear(c, x, y, 6.0) and sc.free(x, y, 3.0)

    area = (L.CRATER[0] - 170, L.CRATER[0] + 170, L.CRATER[1] - 170, L.CRATER[1] + 170)
    for x, y in scatter(c, sc, [ip.meteorite(c, k, 2.0 + k) for k in range(3)], 26, area, ok, 41, coll="Rocks", role="both", gap=14.0,
                        scale=(0.8, 1.6)):
        sc.light("asteroid", x, y, floor_z(c, sc, x, y) + 3)
    scatter(c, sc, [ip.glass_shards(c, k) for k in range(3)], 40, area, ok, 43, coll="Rocks", gap=8.0, scale=(0.8, 1.5))
    scatter(c, sc, [ip.rock(c, "crater_rock", k, 2.5 + k) for k in range(3)], 60, area, ok, 47, coll="Rocks", role="both", gap=8.0,
            scale=(0.7, 1.8))
    # Debris thrown out over the rim.
    def ok_rim(x, y, z):
        r = math.hypot(x - L.CRATER[0], y - L.CRATER[1])
        return L.CRATER_R1 + 4 < r < L.CRATER_LIP + 70 and clear(c, x, y, 8.0) and sc.free(x, y, 3.0)

    area2 = (L.CRATER[0] - 280, L.CRATER[0] + 280, L.CRATER[1] - 280, L.CRATER[1] + 280)
    scatter(c, sc, [ip.meteorite(c, k + 3, 1.5 + 0.5 * k) for k in range(2)], 20, area2, ok_rim, 53, top=True, coll="Rocks", role="both",
            gap=20.0)
    scatter(c, sc, [ip.rock(c, "crater_rock", k + 3, 1.6) for k in range(2)], 50, area2, ok_rim, 59, top=True, coll="Rocks", role="both",
            gap=8.0)
    # Smoke rising off the asteroid, steam from the fissures.
    game_entity(c, "plume", ax - 4, ay + 2, top - 4, height=150.0, radius=16.0, rate=7.0, color="#4a3e44", glow="#ff7a4a")
    for k in range(6):
        a = k * math.tau / 6 + 0.4
        x, y = ax + math.cos(a) * (R + 22), ay + math.sin(a) * (R + 18)
        game_entity(c, "steam", x, y, floor_z(c, sc, x, y) + 0.3)


def cave_mouth(c, sc):
    """The cave mouth at the crater's foot: hanging rock teeth over the way in, glowing
    cracks round it."""
    s0 = S[3] + 30
    for k in range(9):
        s = s0 + 10 + 6 * k
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 2.0 + 1.5 * rnd(k)))
            b, cov, roof, top, fz = where(sc, p.x, p.y)
            if cov and roof - q.p.z > 9.0:
                c.place(ip.stalactites(c, "crater_rock", k % 4, 5.0), p.x, p.y, roof, rot=k, coll="Cave Props")


# ------------------------------------------------------------------ 3  the Crystal Descent


AQUA, AMETHYST, ROSE, GOLD = "crystal_aqua", "crystal_amethyst", "crystal_rose", "core_crystal"


def crystal_descent(c, sc):
    """Great crystal formations (cyan, violet, rose) rising from the warm ochre floor,
    fans and needles on the walls, crystals and stalactites hanging from the roof, the
    waterfall into the stream, flaring crystals by the road, ferns near the far end."""
    area = area_of("crystal")
    ok_big = cave_ok(c, sc, "crystal", margin=24.0, room=30.0)
    ok = cave_ok(c, sc, "crystal", margin=7.0)
    spires = [ap.spire_cluster(c, k, 22.0 + 6 * k, mat=(AQUA, AMETHYST, ROSE)[k], accent=(AMETHYST, ROSE, AQUA)[k]) for k in range(3)]
    for k, (x, y) in enumerate(scatter(c, sc, spires, 7, area, ok_big, 61, coll="Crystals", gap=40.0, scale=(0.8, 1.15))):
        z = floor_z(c, sc, x, y)
        sc.light("crystal_cyan" if k % 3 == 0 else "crystal_violet", x, y, z + 12)
    smalls = [ap.needles(c, k, 10.0 + 4 * k, mat=(AQUA, AMETHYST, ROSE)[k % 3]) for k in range(3)] + \
        [vp.crystals(c, (AQUA, AMETHYST, ROSE)[k % 3], k) for k in range(3)]
    for k, (x, y) in enumerate(scatter(c, sc, smalls, 40, area, ok, 67, coll="Crystals", gap=8.0, scale=(0.7, 1.5))):
        if k % 3 == 0:
            sc.light("crystal_cyan" if k % 2 else "crystal_violet", x, y, floor_z(c, sc, x, y) + 4)
    hanging = [ap.hanging(c, k, 7.0 + 3 * k, mat=(AQUA, AMETHYST)[k % 2]) for k in range(3)]
    scatter(c, sc, hanging, 12, area, hang_ok(c, sc, "crystal", 12.0, margin=10.0), 71, coll="Crystals", hang=True, gap=26.0, scale=(0.7, 1.0))
    drips = [ip.stalactites(c, "cave_ochre", k, 9.0 + 3 * k) for k in range(4)]
    scatter(c, sc, drips, 45, area, hang_ok(c, sc, "crystal", 16.0), 73, coll="Cave Props", hang=True, gap=8.0)
    mites = [ip.stalagmites(c, "cave_ochre", k, 5.0 + 2 * k) for k in range(3)]
    scatter(c, sc, mites, 40, area, ok, 79, coll="Cave Props", role="both", gap=8.0)
    cols = [ip.column(c, "cave_ochre", 30.0, k) for k in range(2)]
    scatter(c, sc, cols, 4, area, lambda x, y, z: ok_big(x, y, z) and where(sc, x, y)[2] - z > 22, 83, coll="Cave Props", role="both",
            gap=50.0)
    # Crystals that flare as you pass, along the bridge's parapets and the hall's road.
    for k, s in enumerate(range(int(S[4] + 40), int(S[7]), 16)):
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 2.6))
            z = q.p.z + (1.2 if L.seg_of(s) in (5,) else 0.0)
            col = "#5ae8ff" if (k + side) % 2 else "#d27aff"
            c.place(vp.crystals(c, AQUA if (k + side) % 2 else AMETHYST, k % 3), p.x, p.y, max(z, floor_z(c, sc, p.x, p.y)) - 0.3, rot=k,
                    scale=0.45, coll="Crystals")
            game_entity(c, "shimmer", p.x, p.y, max(z, floor_z(c, sc, p.x, p.y)) + 1.6, size=1.6, color=col)
    # The waterfall from a crack in the north wall into the stream.
    fx, fy = L.WATERFALL_CRYSTAL
    top = where(sc, fx, fy)[2] - 2.0
    foot = L.CRYSTAL_WATER_Z
    pr.falls(c, "Crystal Falls", fx, fy + 10.0, top, foot + 0.1, 9.0, 13.0, facing=-1, throw=5.0, angle=-0.45,
             mats=("falls_rift", "falls_curtain", "falls_foam"))
    game_entity(c, "waterfall", fx, fy, foot, top=round(top, 1), width=12.0, heading=0.4)
    sc.light("crystal_cyan", fx, fy, foot + 6)
    # Ferns and moss starting toward the passage on to the Lost World.
    ferns = [pr.fern(c), pr.fern(c, "glow_moss")]
    a2 = (-20.0, 120.0, -420.0, -330.0)
    scatter(c, sc, ferns, 40, a2, cave_ok(c, sc, "crystal", margin=4.0), 89, gap=4.0, scale=(0.8, 1.4))
    game_entity(c, "motes", 150.0, -340.0, 6.0, radius=80.0, rate=14.0, color="#9ae8ff", rise=0.2, size=0.3)


# ------------------------------------------------------------------ 4  the Lost World


def lost_world(c, sc):
    """The jungle cavern: cycads, tree ferns, giant horsetails, ferns and big leaves;
    vines and roots from the roof; ruins round the turquoise lake; waterfalls; sunbeams
    pouring through the roof's holes; nests by the meadow."""
    area = area_of("jungle")
    ok = cave_ok(c, sc, "jungle", margin=6.0)
    ok_tall = cave_ok(c, sc, "jungle", margin=9.0, room=16.0)
    scatter(c, sc, [ip.tree_fern(c, k) for k in range(3)], 55, area, ok_tall, 101, gap=9.0, scale=(0.9, 1.3))
    scatter(c, sc, [ip.cycad(c, k) for k in range(4)], 85, area, ok, 103, gap=6.0, scale=(0.9, 1.5))
    scatter(c, sc, [ip.horsetails(c, k) for k in range(3)], 50, area, ok, 107, gap=6.0, scale=(0.9, 1.5))
    scatter(c, sc, [pr.fern(c), pr.big_leaf_plant(c, 0), pr.big_leaf_plant(c, 1)], 170, area, ok, 109, gap=3.0, scale=(0.9, 1.8))
    scatter(c, sc, [pr.giant_tree(c, k) for k in range(2)], 7, area, lambda x, y, z: ok_tall(x, y, z) and where(sc, x, y)[2] - z > 26.0,
            113, gap=50.0, scale=(0.55, 0.65))
    # Vines and roots hanging from the roof, mossy stalactites.
    scatter(c, sc, [pr.vine_curtain(c, k, 12.0) for k in range(3)], 16, area, hang_ok(c, sc, "jungle", 12.0), 117, coll="Cave Props",
            hang=True, gap=10.0)
    scatter(c, sc, [pr.hanging_roots(c, k, 5.0) for k in range(3)], 40, area, hang_ok(c, sc, "jungle", 6.0), 119, coll="Cave Props",
            hang=True, gap=8.0)
    scatter(c, sc, [ip.stalactites(c, "moss_rock", k, 10.0) for k in range(3)], 40, area, hang_ok(c, sc, "jungle", 12.0), 121,
            coll="Cave Props", hang=True, gap=12.0)
    # Sunbeams through the skylights, and their light on the ground.
    for k, (sx, sy, r) in enumerate(L.SKYLIGHTS):
        top = L.natural(sx, sy)
        fz = floor_z(c, sc, sx, sy)
        ln = (top - fz) / 0.86 + 6.0
        for j in range(3):
            a = j * 2.1 + k
            c.place(ip.sun_beam(c, ln, r * (0.5 + 0.2 * j), j), sx + 2.0 * math.cos(a), sy + 2.0 * math.sin(a), top + 1.0, coll="Beams")
        d = Vector((0.34, -0.38, -0.86)).normalized()
        t = (top - fz) / 0.86
        gx, gy = sx + d.x * t, sy + d.y * t
        for j in range(5):
            sc.light("sun", gx + (j - 2) * 3.0, gy, fz + 2.0)
        game_entity(c, "motes", gx, gy, fz + 8.0, radius=r * 1.6, rate=round(6.0 + r * 0.4, 1), color="#ffe6a0", rise=0.15, size=0.25)
    # Ruins by the lake: a colossal head, broken columns, steles, stairs to the water.
    lx, ly = L.LAKE_JUNGLE
    ruins = [(lx - 30, ly + 52, pr.idol_head(c), 2.6, -0.5), (lx + 46, ly + 46, pr.ruin_column(c, 0), 1.4, 0.0),
             (lx + 58, ly + 36, pr.ruin_column(c, 1), 1.5, 0.3), (lx + 64, ly + 50, pr.ruin_column(c, 2), 1.4, 0.0),
             (lx - 70, ly + 40, pr.stele(c, 0), 1.3, 0.4), (lx - 84, ly + 20, pr.stele(c, 1), 1.3, 1.0),
             (lx + 12, ly + 50, pr.ruin_blocks(c, 0), 1.6, 0.0), (lx - 50, ly + 46, pr.ruin_blocks(c, 1), 1.6, 0.0),
             (lx + 90, ly - 10, ip.obelisk(c, 0, 12.0), 1.0, 0.0), (lx - 100, ly - 20, ip.obelisk(c, 1, 10.0), 1.0, 0.0)]
    for x, y, proto, s, r in ruins:
        if not clear(c, x, y, 10.0):
            continue
        c.place(proto, x, y, floor_z(c, sc, x, y) - 0.4, rot=r + math.atan2(ly - y, lx - x) + math.pi / 2, scale=s, coll="Ruins", role="both")
        sc.footprints.append((x, y, 8.0))
    # Waterfalls into the lake from the south wall.
    for k, (fx, fy, w) in enumerate(((lx - 30, ly - 46, 10.0), (lx + 40, ly - 44, 7.0))):
        top = where(sc, fx, fy - 8)[2] - 3.0
        pr.falls(c, "Lake Falls %d" % (k + 1), fx, fy - 6.0, top, L.JUNGLE_WATER_Z + 0.1, w, w * 1.4, facing=1, throw=6.0,
                 mats=("falls_sheet", "falls_veil", "falls_foam"))
        game_entity(c, "waterfall", fx, fy, L.JUNGLE_WATER_Z, top=round(top, 1), width=w, heading=0.0)
    # Nests by the meadow, where the triceratops graze.
    mx, my = L.MEADOW
    for k in range(3):
        a = k * 2.0 + 0.5
        x, y = mx + 30 * math.cos(a), my + 24 * math.sin(a)
        if clear(c, x, y, 8.0):
            c.place(ip.nest(c), x, y, floor_z(c, sc, x, y) - 0.1, rot=a, coll="Props", role="both")
    game_entity(c, "motes", -150.0, -520.0, 0.0, radius=110.0, rate=12.0, color="#c8ff7a", rise=0.05, size=0.22, blink=True)


# ------------------------------------------------------------------ the hidden cavern


def hidden_cavern(c, sc):
    """The Ancient Way: the ruined gateway, obelisks and fallen columns along the
    causeway, glowing fungi and carved glyphs round the still black pool."""
    pts = sc.short_pts
    k = 8
    a, b = pts[k - 2], pts[k + 2]
    rot = math.atan2(b[1] - a[1], b[0] - a[0]) - math.pi / 2
    c.place(ip.gateway(c, 13.0, 10.0), pts[k][0], pts[k][1], pts[k][2] - 0.6, rot=rot, coll="Ruins", role="both")
    for j in range(6, len(pts) - 12, 10):
        x, y, z = pts[j]
        a, b = pts[j - 1], pts[j + 1]
        h = math.atan2(b[1] - a[1], b[0] - a[0])
        for side in (-1, 1):
            if (j // 10 + side) % 2:
                continue
            ox, oy = x + side * 9.0 * math.sin(h), y - side * 9.0 * math.cos(h)
            proto = ip.obelisk(c, j % 3, 7.0) if (j // 10) % 3 else pr.ruin_column(c, j % 3)
            c.place(proto, ox, oy, floor_z(c, sc, ox, oy) - 0.5, rot=h, scale=1.0, coll="Ruins", role="both")
            sc.light("fungus", ox, oy, z + 3.0)
    area = area_of("hidden")
    scatter(c, sc, [ip.giant_fungi(c, k) for k in range(3)], 45, area, cave_ok(c, sc, "hidden", margin=5.0), 131, coll="Cave Props",
            gap=6.0, scale=(0.8, 1.6))
    for x, y in scatter(c, sc, [ip.giant_fungi(c, k + 3) for k in range(2)], 20, area, cave_ok(c, sc, "hidden", margin=8.0), 137,
                        coll="Cave Props", gap=12.0, scale=(1.2, 2.0)):
        sc.light("fungus", x, y, floor_z(c, sc, x, y) + 3)
    scatter(c, sc, [ip.stalactites(c, "cave_ochre_dark", k, 7.0) for k in range(3)], 36, area, hang_ok(c, sc, "hidden", 8.0), 139,
            coll="Cave Props", hang=True, gap=8.0)
    mid = pts[len(pts) // 2]
    game_entity(c, "motes", mid[0], mid[1], mid[2] + 3, radius=70.0, rate=8.0, color="#6affd8", rise=0.1, size=0.25, blink=True)


# ------------------------------------------------------------------ 5  the volcanic depths


def volcanic(c, sc):
    """Black rock and fire: lava falls feeding the rivers, spires and obsidian blades,
    basalt ruins, glowing stalactites; lights on the lava."""
    area = area_of("volcanic")
    ok = cave_ok(c, sc, "volcanic", margin=7.0)
    scatter(c, sc, [ip.lava_spire(c, k, 10.0 + 5 * k) for k in range(3)], 30, area, cave_ok(c, sc, "volcanic", margin=12.0), 151,
            coll="Rocks", role="both", gap=14.0)
    scatter(c, sc, [vp.obsidian_cluster(c, k) for k in range(2)] + [vp.obsidian_spire(c, k) for k in range(2)], 30, area, ok, 157,
            coll="Rocks", role="both", gap=10.0, scale=(0.6, 1.0))
    scatter(c, sc, [vp.ruin_pillar(c, k) for k in range(2)] + [vp.leaning_slab(c, k) for k in range(2)], 16, area, ok, 163, coll="Ruins",
            role="both", gap=16.0)
    scatter(c, sc, [ip.stalactites(c, "black_rock", k, 10.0) for k in range(3)], 50, area, hang_ok(c, sc, "volcanic", 12.0), 167,
            coll="Cave Props", hang=True, gap=9.0)
    # Lava falls from the walls into the heads of the rivers.
    for w in L.WATERS:
        if w["kind"] != "lava" or "channel" not in w:
            continue
        x0, y0 = w["channel"][0]
        x1, y1 = w["channel"][1]
        h = math.atan2(y1 - y0, x1 - x0)
        lx, ly = x0 - 10 * math.cos(h), y0 - 10 * math.sin(h)
        top = where(sc, lx, ly)[2] - 4.0
        pr.falls(c, w["name"] + " Fall", lx, ly, top, w["z"] + 0.2, 8.0, 10.0, facing=1, throw=4.0, angle=h - math.pi / 2,
                 mats=("lava_fall", "ember_mist", "lava_flow"), foam=False)
        for j in range(4):
            sc.light("lava", lx, ly, top - j * 8)
    # Light all along the rivers and round the lair's lake.
    for w in L.WATERS:
        if w["kind"] != "lava":
            continue
        if "channel" in w:
            for x, y, _, z in L.ribbon_path(w)[::3]:
                sc.light("lava", x, y, z + 2.0)
    g = sc.grid
    for j in range(0, g.ny, 3):
        for i in range(0, g.nx, 3):
            x, y = g.xy(i, j)
            b, cov, roof, top, fz = where(sc, x, y)
            if b == "lair" and fz < L.LAVA_Z + 0.2:
                sc.light("lava", x, y, L.LAVA_Z + 2.0)
    game_entity(c, "motes", -400.0, -280.0, -8.0, radius=90.0, rate=16.0, color="#ff8a3a", rise=1.2, size=0.22)


# ------------------------------------------------------------------ 6  the dragon's lair


def lair(c, sc):
    """The dragon's crag rising out of the lava lake beside the gorge, bones on the
    ledges, more lava falling from the walls."""
    px, py = L.PERCH
    scale = 0.72
    foot = L.LAVA_Z - 1.0
    c.place(vp.crag(c, 1), px, py, foot, rot=0.6, scale=scale, coll="Landmarks", role="both")
    sc.perch = (px - 6 * scale, py, foot + 52 * scale + 1.5 * scale)
    sc.footprints.append((px, py, 24.0))
    area = area_of("lair")
    ok = cave_ok(c, sc, "lair", margin=6.0)
    scatter(c, sc, [ip.bones(c, k) for k in range(2)], 8, area, ok, 171, coll="Props", gap=20.0, scale=(0.8, 1.2))
    scatter(c, sc, [ip.lava_spire(c, k, 12.0 + 4 * k) for k in range(3)], 18, area, cave_ok(c, sc, "lair", margin=10.0, dry=False), 173,
            coll="Rocks", role="both", gap=16.0)
    scatter(c, sc, [ip.stalactites(c, "lair_rock", k, 12.0) for k in range(3)], 30, area, hang_ok(c, sc, "lair", 14.0), 177,
            coll="Cave Props", hang=True, gap=12.0)
    for k, (x, y, h) in enumerate(((-372.0, -128.0, 0.4), (-388.0, -230.0, 0.9), (-290.0, -12.0, -1.6))):
        top = where(sc, x, y)[2] - 3.0
        pr.falls(c, "Lair Lava Fall %d" % (k + 1), x, y, top, L.LAVA_Z + 0.2, 7.0, 9.0, facing=1, throw=4.0, angle=h,
                 mats=("lava_fall", "ember_mist", "lava_flow"), foam=False)
        sc.light("lava", x, y, top - 10)
    game_entity(c, "motes", px, py, -6.0, radius=70.0, rate=18.0, color="#ff6a2a", rise=1.6, size=0.25)


# ------------------------------------------------------------------ 7  the Heart of the Earth


def heart(c, sc):
    """The core's chamber: a rock pillar out of the glowing abyss carrying the core
    crystal (drawn by the game, pulsing), crystal growths round the ring and up the walls,
    the portal's carved frame."""
    cx, cy = L.CORE
    bm = bmesh.new()
    from volcano_props import prism

    prism(bm, (cx, cy, -48.0), (cx + 0.5, cy, -18.0), 13.0, 7.0, n=7, phase=0.3)
    prism(bm, (cx + 0.5, cy, -18.0), (cx, cy, -12.0), 7.0, 9.5, n=7, phase=0.6)
    ob = c.mesh_object("Core Pillar", bm, "Landmarks", "both")
    c.assign(ob, c.lib("core_glass"))
    ob.data.shade_flat()
    sc.core = (cx, cy, -1.0)
    for k in range(8):
        a = k * math.tau / 8
        sc.light("core", cx + 30 * math.cos(a), cy + 30 * math.sin(a), -10.0)
        sc.light("core", cx + 70 * math.cos(a), cy + 70 * math.sin(a), -12.0)
    sc.light("core", cx, cy, -1.0)
    # Crystal growths between the ring and the walls, and up the walls.
    def ok(x, y, z):
        r = math.hypot(x - L.SHAFT[0], y - L.SHAFT[1])
        return r < L.SHAFT_R - 4 and z < -8.0 and clear(c, x, y, 6.0) and math.hypot(x - cx, y - cy) > L.CORE_PIT_R + 4
    area = (L.SHAFT[0] - 100, L.SHAFT[0] + 100, L.SHAFT[1] - 100, L.SHAFT[1] + 100)
    growths = [ap.spire_cluster(c, k + 3, 16.0 + 4 * k, mat=(GOLD, ROSE, AMETHYST)[k], accent=(ROSE, GOLD, GOLD)[k]) for k in range(3)]
    scatter(c, sc, growths, 14, area, ok, 181, coll="Crystals", gap=20.0, scale=(0.7, 1.1))
    scatter(c, sc, [vp.crystals(c, (GOLD, ROSE, AMETHYST)[k], k) for k in range(3)], 50, area, ok, 183, coll="Crystals", gap=6.0,
            scale=(0.6, 1.3))
    # The portal's carved frame where the lair's bridge enters the shaft.
    s = S[15] + 62
    q = c.at(s)
    c.place(ip.gateway(c, q.w + 4.0, 12.0), q.p.x, q.p.y, q.p.z - 0.6, rot=road_rot(q) - math.pi / 2, coll="Ruins", role="both")
    game_entity(c, "motes", cx, cy, -8.0, radius=60.0, rate=20.0, color="#ffd27a", rise=0.6, size=0.3)


def ascent(c, sc):
    """Braziers up the ascent's terrace, and banners toward the top."""
    for k, s in enumerate(range(int(S[18] + 30), int(S[19] - 10), 34)):
        q = c.at(s)
        p = q.side(-(q.w / 2 + 2.0))
        c.place(cp.brazier(c), p.x, p.y, q.p.z - 0.1, coll="Props", role="both")
        sc.light("torch", p.x, p.y, q.p.z + 2.4)
        game_entity(c, "torch", p.x, p.y, q.p.z + 2.5)


# ------------------------------------------------------------------ the bridges


def bridges(c, sc):
    """Piers under every bridge, down to whatever's below."""
    mats = {"crystal_bridge": ("bridge_stone", "wall"), "jungle_bridge": ("ruin_moss", "wall"), "volcanic_bridge": ("black_rock", "wall"),
            "lair_bridge": ("lair_rock", "wall")}  # (the ascent's bridge over the portal stands on its own)
    for piece in c.pieces:
        kind = piece.name.split(" ", 2)[-1]
        if kind in mats:
            pr.piers(c, piece, every=14.0, mat=mats[kind], size=1.6, terrain=sc.ground_obs, inset=2.0)


# ------------------------------------------------------------------ the creatures


def creatures(c, sc):
    """The Lost World's animals: triceratops grazing on the meadow, raptors darting across
    the road, a sauropod by the river bridge and another wading in the lake, pterosaurs
    circling under the roof. And the dragon on its crag."""
    # Triceratops: a small herd, each grazing round its own little patch.
    mx, my = L.MEADOW
    for k, (dx, dy, s) in enumerate(((0, 0, 1.25), (16, -10, 1.0), (-14, -16, 1.1), (6, 20, 0.8), (-24, 8, 0.65))):
        x, y = mx + dx, my + dy
        if not clear(c, x, y, 12.0):
            continue
        game_entity(c, "triceratops", x, y, floor_z(c, sc, x, y), heading=round(k * 1.3, 2), scale=s, roam=6.0, seed=k + 1)
    # Raptors: packs darting across the road on a beat.
    for k, (s, period, offset, n) in enumerate(((S[9] + 25, 9.0, 0.0, 3), (S[9] + 80, 11.0, 4.0, 2), (S[11] - 10, 13.0, 7.0, 3))):
        q = c.at(s)
        a, b = q.side(-(q.w / 2 + 16.0)), q.side(q.w / 2 + 16.0)
        if k % 2:
            a, b = b, a
        A = c.game(a.x, a.y, floor_z(c, sc, a.x, a.y))
        B = c.game(b.x, b.y, floor_z(c, sc, b.x, b.y))
        c.entity("raptors", ax=A[0], ay=A[1], az=A[2], bx=B[0], by=B[1], bz=B[2], period=period, offset=offset, travel=2.2, warn=1.4, count=n)
    # The sauropods: one by the corner at the river bridge, one wading in the lake.
    q = c.at(S[12] + 20)
    cx, cy = q.side(q.w / 2 + 30.0).x, q.side(q.w / 2 + 30.0).y
    path = []
    for k in range(10):
        a = k * math.tau / 10
        x, y = cx + 16 * math.cos(a), cy + 10 * math.sin(a)
        path.append((x, y, floor_z(c, sc, x, y)))
    c.path_curve("Sauropod Path", path)
    c.entity("dinosaur", route="Sauropod Path", speed=1.4, scale=2.1, start=0)
    lx, ly = L.LAKE_JUNGLE
    path = []
    for k in range(12):
        a = k * math.tau / 12
        x, y = lx + 40 * math.cos(a), ly - 6 + 18 * math.sin(a)
        path.append((x, y, L.JUNGLE_WATER_Z - 1.2))
    c.path_curve("Lake Wade Path", path)
    c.entity("dinosaur", route="Lake Wade Path", speed=1.6, scale=1.7, start=30)
    c.entity("dinosaur", route="Lake Wade Path", speed=1.6, scale=0.9, start=42)
    # Pterosaurs circling under the jungle's roof, and one over the desert.
    for k, (x, y, rx, ry, z) in enumerate(((-120.0, -520.0, 90.0, 50.0, 14.0), (-40.0, -470.0, 50.0, 40.0, 10.0),
                                            (140.0, 60.0, 140.0, 90.0, 85.0))):
        path = [(x + rx * math.cos(a), y + ry * math.sin(a), z + 3 * math.sin(a * 3)) for a in (j * math.tau / 14 for j in range(14))]
        c.path_curve("Flyer Path %d" % (k + 1), path)
        c.entity("pterosaur", route="Flyer Path %d" % (k + 1), speed=11.0 + k, scale=1.2 if k < 2 else 1.6, start=k * 20)


# ------------------------------------------------------------------ gameplay


def gameplay(c, sc):
    a, b = L.merge_s()
    apex = S[10] + 40.0
    gates = c.checkpoints(
        extra=[S[1] + 40, S[2] + 60, S[4] + 30, S[5] + 50, S[6] + 60, a - 10, apex, b + 12, S[13] + 120, S[14] + 80,
               S[15] + 60, S[17] + 60, S[17] + 160, S[18] + 80, S[18] + 180, S[19] + 30],
        avoid=[(a - 2, apex - 8), (apex + 8, b + 2)],
        height=9.0,
    )
    main_gate = min(gates.items(), key=lambda kv: abs(kv[0] - apex))[1]
    pts = sc.short_pts
    k = len(pts) // 2
    c.alt_gate(main_gate, "ancient_way", [pts[k - 4], pts[k], pts[k + 4]], width=15.0, height=8.0)
    c.path_curve("Ancient Way Path", [p for p in pts[::4]] + [pts[-1]], closed=False)
    sc.apex = apex
    # Boosts (the core's ring is the Core Boost), bananas, balloons.
    for at, across in ((S[0] + 70, 0), (S[2] + 120, 0), (S[5] + 20, 0), (S[9] + 30, 0), (S[13] + 60, 0), (S[15] + 20, -4),
                       (S[17] + 50, 0), (S[17] + 130, 0), (S[19] + 20, 0)):
        c.zipper(at, across)
    for at, across in ((S[0] + 150, 0), (S[3] + 20, 3), (S[6] + 30, -3), (S[8] + 60, 0), (S[11] + 20, 3), (S[13] + 140, -3),
                       (S[16] + 10, 0), (S[18] + 120, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in ((S[0] + 110, -5, "red"), (S[0] + 110, 5, "blue"), (S[1] + 80, 0, "green"), (S[4] + 50, 0, "yellow"),
                            (S[6] + 10, -4, "rainbow"), (S[6] + 10, 4, "red"), (S[9] + 70, 0, "blue"), (S[12] + 40, 0, "green"),
                            (S[13] + 30, -4, "yellow"), (S[13] + 30, 4, "rainbow"), (S[14] + 120, 0, "red"), (S[17] + 90, 0, "blue"),
                            (S[18] + 40, -4, "green"), (S[18] + 40, 4, "yellow")):
        c.balloon(at, across, col)
    hazards(c, sc)
    atmosphere(c, sc)


def hazards(c, sc):
    """The dragon, the lava geysers, the falling rocks, the meteor debris, the core."""
    # ---- the dragon: on its crag, breathing fire across the bridge's right-hand lanes
    dx, dy, dz = sc.perch
    s_fire = S[15] + 18.0
    q = c.at(s_fire)
    f = q.side(5.0)
    head = math.atan2(q.p.x - dx, q.p.y - dy)
    D = c.game(dx, dy, dz)
    F = c.game(f.x, f.y, q.p.z)
    fh = math.atan2(q.t.x, -q.t.y)  # along the road, game heading (0 = +z)
    c.entity("dragon", x=D[0], y=D[1], z=D[2], heading=round(math.atan2(F[0] - D[0], F[2] - D[2]), 3), scale=1.7, look="obsidian",
             fire={"x": F[0], "y": F[1], "z": F[2], "heading": round(fh, 3), "length": 30.0, "width": 11.0, "height": 6.0},
             period=10.0, offset=2.0, aim=1.4, warn=1.8, breathe=2.2, cool=1.2)
    sc.dragon = (dx, dy, dz, head)
    # ---- lava geysers on the volcanic causeway's shoulders: they warn, then blow
    for k, (s, side, off) in enumerate(((S[13] + 40, 1, 0.0), (S[13] + 95, -1, 2.3), (S[13] + 150, 1, 4.6), (S[13] + 205, -1, 1.2))):
        q = c.at(s)
        p = q.side(side * (q.w / 2 - 2.0))
        game_entity(c, "geyser", p.x, p.y, q.p.z, r=3.6, height=16.0, period=6.5, offset=round(off, 2), warn=1.5, blast=1.6, launch=0,
                    lava=True)
    # ---- rocks falling from the volcanic roof onto the road (a ring glows first)
    for k, (s, across, off) in enumerate(((S[13] + 120, -3.0, 0.0), (S[14] + 30, 3.0, 3.5), (S[12] + 110, 2.0, 5.0))):
        q = c.at(s)
        p = q.side(across)
        b, cov, roof, top, fz = where(sc, p.x, p.y)
        game_entity(c, "icicle", p.x, p.y, q.p.z, top=round(min(roof - 1.0, q.p.z + 24.0), 1), period=8.0, offset=off, warn=1.6, r=3.4,
                    look="rock")
    # ---- debris from the sky onto the crater's descent (the ring glows, it streaks in)
    for k, (s, across, off) in enumerate(((S[1] + 160, 3.0, 1.0), (S[2] + 70, -3.0, 4.0), (S[2] + 150, 2.0, 7.0))):
        q = c.at(s)
        p = q.side(across)
        game_entity(c, "icicle", p.x, p.y, q.p.z, top=round(q.p.z + 120.0, 1), period=11.0, offset=off, warn=2.0, r=3.8, look="meteor")
    # ---- the meteor shower over the desert, and the big one at the start of the race
    ax, ay = L.ASTEROID
    game_entity(c, "meteors", ax, ay, sc.asteroid_top, rate=0.35, intro=True)
    # ---- the core: the Heart of the Earth's crystal, pulsing over the abyss
    cx, cy, cz = sc.core
    game_entity(c, "core", cx, cy, cz + 2.0, size=16.0)
    # ---- warm and coloured lights near the camera
    for kind, col in (("lava", "#ff6a2a"), ("crystal_cyan", "#5ae8ff"), ("crystal_violet", "#c070ff"), ("fungus", "#4affc8"),
                      ("core", "#ffc070")):
        for x, y, z in sc.lights.get(kind, [])[::4 if kind == "lava" else 2]:
            game_entity(c, "glow", x, y, z, color=col)


ZONES = {  # the air and the sound of each world (see game/depths.ts)
    "desert": {"fog": "#e0c49c", "near": 420, "far": 2400, "sun": 2.8, "sky": "#b0ccf0", "ground": "#9a6a42", "hemi": 1.2, "sound": "wind"},
    "crater": {"fog": "#a87a62", "near": 260, "far": 1500, "sun": 2.4, "sky": "#c8a49a", "ground": "#5a3a32", "hemi": 1.1, "sound": "resonance"},
    "crystal": {"fog": "#241a3a", "near": 60, "far": 520, "sun": 0.35, "sky": "#8ab0ff", "ground": "#6a3a2a", "hemi": 1.25, "sound": "chime"},
    "jungle": {"fog": "#2a4a34", "near": 70, "far": 620, "sun": 0.7, "sky": "#cfe8a8", "ground": "#3a5a2a", "hemi": 1.3, "sound": "jungle"},
    "hidden": {"fog": "#0e2224", "near": 40, "far": 380, "sun": 0.25, "sky": "#7ad8c0", "ground": "#1e3a32", "hemi": 1.0, "sound": "drip"},
    "volcanic": {"fog": "#3a1008", "near": 50, "far": 460, "sun": 0.3, "sky": "#ff9a6a", "ground": "#4a1408", "hemi": 1.2, "sound": "rumble"},
    "lair": {"fog": "#4a0c06", "near": 50, "far": 480, "sun": 0.3, "sky": "#ff7a4a", "ground": "#5a1006", "hemi": 1.25, "sound": "rumble"},
    "core": {"fog": "#2a0e3a", "near": 60, "far": 520, "sun": 0.6, "sky": "#ffc0e8", "ground": "#5a2a6a", "hemi": 1.35, "sound": "hum"},
    "ascent": {"fog": "#c8a07a", "near": 200, "far": 1400, "sun": 2.2, "sky": "#d8c8e8", "ground": "#8a5a3a", "hemi": 1.15, "sound": "wind"},
}


def atmosphere(c, sc):
    """The air as you go down: fog, light and sound blend from one world to the next.
    Keys every ~12 m along the lap (and the shortcut) name the worlds either side and how
    far between them."""
    keys = []
    zs = L.ZONES
    blend = 30.0
    s = 0.0
    while s < c.length:
        q = c.at(s)
        cur = L.zone_of(s)
        nxt, t = cur, 0.0
        for d, name in zs:
            if name != cur and abs(s - d) < blend:
                prev = L.zone_of(d - 1.0)
                cur, nxt = prev, name
                t = (s - d + blend) / (2 * blend)
                break
        x, y, z = c.game(q.p.x, q.p.y, q.p.z)
        keys.append([x, y, z, cur, nxt, round(L.sm(t), 3)])
        s += 12.0
    pts = sc.short_pts
    n = len(pts)
    for i in range(0, n, 6):
        u = i / (n - 1)
        if c.nearest(pts[i][0], pts[i][1])[1] < 40.0:
            continue  # near the main road its own keys say
        x, y, z = c.game(*pts[i])
        if u < 0.12:
            keys.append([x, y, z, "crystal", "hidden", round(L.sm(u / 0.12), 3)])
        elif u > 0.85:
            keys.append([x, y, z, "hidden", "volcanic", round(L.sm((u - 0.85) / 0.15), 3)])
        else:
            keys.append([x, y, z, "hidden", "hidden", 0.0])
    c.entity("atmosphere", zones=ZONES, keys=keys)


# ------------------------------------------------------------------ build


def build(c, sc):
    desert(c, sc)
    asteroid(c, sc)
    cave_mouth(c, sc)
    crystal_descent(c, sc)
    lost_world(c, sc)
    hidden_cavern(c, sc)
    volcanic(c, sc)
    lair(c, sc)
    heart(c, sc)
    ascent(c, sc)
    bridges(c, sc)
    creatures(c, sc)
    gameplay(c, sc)
