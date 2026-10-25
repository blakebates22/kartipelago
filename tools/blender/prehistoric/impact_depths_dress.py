# Impact Depths' look (see impact_depths.py): the cave over the pit, the crack the crater
# broke in its roof (and the sunlight through it), and each terrace dressed as one of the
# old Impact Depths' worlds on the way down: the crater's rim, the crystal halls, the
# Lost World's jungle, the volcanic depths, the core. Built from the same props and
# materials as the old course (impact_props.py, aurora_props.py, props.py...).
# SPDX-License-Identifier: MIT

import math

import aurora_props as ap
import impact_props as ip
import props as pr
import volcano_props as vp
import course_kit as kit
from course_kit import Vector, bmesh, rnd
from impact_scenery import clear, game_entity

AQUA, AMETHYST, ROSE = "crystal_aqua", "crystal_amethyst", "crystal_rose"
SUN = Vector((0.34, -0.38, -0.86)).normalized()  # the way the sunlight falls
ROOF = {"crater": "crater_rock", "crystal": "cave_ochre_dark", "jungle": "moss_rock", "volcanic": "black_rock", "core": "black_rock"}
TINT = {
    "crater": (0.66, 0.56, 0.52),
    "crystal": (0.5, 0.48, 0.66),
    "jungle": (0.52, 0.66, 0.48),
    "volcanic": (0.52, 0.36, 0.32),
    "core": (0.6, 0.46, 0.7),
}


class Dress:
    def __init__(self, c, v, ter):
        self.c, self.v, self.ter = c, v, ter
        self.lights = {}

    def light(self, kind, x, y, z):
        self.lights.setdefault(kind, []).append((x, y, z))

    def floor(self, x, y):
        z = self.c.ground_z(x, y, [self.ter])
        return z if z is not None else self.v.natural(x, y)

    def sunlit(self, x, y, z):
        """Does the sunlight through the crack reach (x, y, z)?"""
        t = (self.v.roof_z(x, y) - z) / -SUN.z
        if t < 0:
            return self.v.opening(x, y) > 0
        return self.v.opening(x - SUN.x * t, y - SUN.y * t) > 0


def spots(d, n, ok, seed, ring=None, gap=4.0, tries=40):
    """Up to n random (x, y, z) on the land where ok(x, y, z): in the annulus `ring`
    (r0, r1) round the pit's centre."""
    r0, r1 = ring
    out = []
    k = 0
    while len(out) < n and k < n * tries:
        k += 1
        a = rnd(k * 1.37 + seed * 7.1) * math.tau
        r = math.sqrt(r0 * r0 + (r1 * r1 - r0 * r0) * rnd(k * 2.71 + seed * 3.9))
        x, y = r * math.cos(a), r * math.sin(a)
        if any((x - p[0]) ** 2 + (y - p[1]) ** 2 < gap * gap for p in out):
            continue
        z = d.floor(x, y)
        if not ok(x, y, z):
            continue
        out.append((x, y, z))
    return out


def flat(d, x, y, rise=2.0, s=3.0):
    z = [d.v.natural(x + ox, y + oy) for ox, oy in ((s, 0), (-s, 0), (0, s), (0, -s))]
    return max(z) - min(z) < rise


def steep(d, x, y, s=3.0):
    z = [d.v.natural(x + ox, y + oy) for ox, oy in ((s, 0), (-s, 0), (0, s), (0, -s))]
    return max(z) - min(z) > 6.0


def dry(d, x, y, z):
    zb = d.v.crack_floor(x, y)
    return z > d.v.Z_BOTTOM - 3 and (zb is None or z > zb - 2.0)


def put(d, protos, pts, seed, scale=(0.8, 1.2), coll="Props", role="visual", sink=0.25):
    for k, (x, y, z) in enumerate(pts):
        s = scale[0] + (scale[1] - scale[0]) * rnd(k * 5.9 + seed)
        d.c.place(protos[k % len(protos)], x, y, z - sink, rot=rnd(k * 3.7 + seed) * math.tau, scale=s, role=role, coll=coll)


def hang(d, protos, n, seed, ring, length, coll="Cave Props", gap=10.0, scale=(0.8, 1.2)):
    """Things hanging from the roof (not in the openings), high over whatever's below."""
    v = d.v
    out = []
    k = 0
    r0, r1 = ring
    while len(out) < n and k < n * 40:
        k += 1
        a = rnd(k * 1.91 + seed * 5.3) * math.tau
        r = math.sqrt(r0 * r0 + (r1 * r1 - r0 * r0) * rnd(k * 3.13 + seed * 2.1))
        x, y = r * math.cos(a), r * math.sin(a)
        if v.opening(x, y) > -6 or any((x - p[0]) ** 2 + (y - p[1]) ** 2 < gap * gap for p in out):
            continue
        z = v.roof_z(x, y)
        smp, dd = d.c.nearest(x, y)
        below = max(d.floor(x, y), smp.p.z if dd < smp.w / 2 + 10 else -1e9)
        if z - below < length + 14.0:
            continue
        out.append((x, y, z + 1.0))
    for k, (x, y, z) in enumerate(out):
        s = scale[0] + (scale[1] - scale[0]) * rnd(k * 4.3 + seed)
        d.c.place(protos[k % len(protos)], x, y, z, rot=rnd(k * 2.9 + seed) * math.tau, scale=s, role="visual", coll=coll)
    return out


# ------------------------------------------------------------------ the shell


def shell(d):
    """The cave's roof over the pit, the desert over it, and the walls of the crack and
    the skylights between them (all to look at: nothing up there to touch)."""
    v, c = d.v, d.c
    cell = 6.0
    R = v.R_CAVE + 30
    n = int(2 * R / cell)
    roof_bm, top_bm, rim_bm = bmesh.new(), bmesh.new(), bmesh.new()
    rv, tv = {}, {}
    roof_mat, top_mat, rim_mat = [], [], []

    def xy(i, j):
        return -R + i * cell, -R + j * cell

    covered = {}

    def cov(i, j):
        k = (i, j)
        if k not in covered:
            x, y = xy(i + 0.5, j + 0.5)
            r = math.hypot(x, y)
            covered[k] = r < R and v.opening(x, y) < 0 and v.natural(x, y) < v.roof_z(x, y) - 0.5
        return covered[k]

    def hole(i, j):
        x, y = xy(i + 0.5, j + 0.5)
        return math.hypot(x, y) < R and v.opening(x, y) >= 0

    def vert(bm, cache, i, j, z):
        k = (i, j)
        if k not in cache:
            x, y = xy(i, j)
            cache[k] = bm.verts.new((x, y, z(x, y)))
        return cache[k]

    def top(x, y):
        return v.Z_DESERT + 0.8 * math.sin(x / 31.0) * math.cos(y / 27.0)

    for j in range(n):
        for i in range(n):
            x, y = xy(i + 0.5, j + 0.5)
            if cov(i, j):
                ks = ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))
                roof_bm.faces.new([vert(roof_bm, rv, a, b, v.roof_z) for a, b in reversed(ks)])
                roof_mat.append(ROOF[v.zone(x, y)])
                for (a, b), (di, dj) in (((ks[0], ks[1]), (0, -1)), ((ks[1], ks[2]), (1, 0)), ((ks[2], ks[3]), (0, 1)), ((ks[3], ks[0]), (-1, 0))):
                    if not hole(i + di, j + dj):
                        continue
                    pa, pb = Vector((*xy(*a), 0)), Vector((*xy(*b), 0))
                    q = [rim_bm.verts.new((pa.x, pa.y, v.roof_z(pa.x, pa.y) - 0.3)), rim_bm.verts.new((pb.x, pb.y, v.roof_z(pb.x, pb.y) - 0.3)),
                         rim_bm.verts.new((pb.x, pb.y, top(pb.x, pb.y) + 0.05)), rim_bm.verts.new((pa.x, pa.y, top(pa.x, pa.y) + 0.05))]
                    f = rim_bm.faces.new(q)
                    f.normal_update()
                    if f.normal.dot(Vector((di, dj, 0))) < 0:
                        f.normal_flip()
                    zm = (v.roof_z(pa.x, pa.y) + v.Z_DESERT) / 2
                    rim_mat.append("strata_cream" if zm > 100 else "strata_orange" if zm > 90 else "strata_red")
            # The desert over the roof, round the openings (where you can see it).
            if not hole(i, j) and v.opening(x, y) > -60:
                ks = ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))
                top_bm.faces.new([vert(top_bm, tv, a, b, top) for a, b in ks])
                g = math.sin(x / 47.0 + 0.4) * math.cos(y / 39.0) + 0.5 * math.sin((x - y) / 21.0)
                top_mat.append("slickrock" if g > 1.0 else "red_sand" if g < -0.7 else "desert_sand")
    obs = []
    for bm, mats, name in ((roof_bm, roof_mat, "Cave Roof"), (top_bm, top_mat, "Desert Over"), (rim_bm, rim_mat, "Crack Walls")):
        ob = c.mesh_object(name, bm, "Shell", "visual")
        groups = {}
        for fi, m in enumerate(mats):
            groups.setdefault(m, []).append(fi)
        for m, faces in groups.items():
            c.assign(ob, c.lib(m), faces)
        ob.data.shade_flat() if name == "Crack Walls" else ob.data.shade_smooth()
        obs.append(ob)
    d.roof, d.over, d.rims = obs


def sunlight(d):
    """Shafts of sunlight through the crack and the skylights, and their light below."""
    v, c = d.v, d.c
    holes = [(x, y, w / 2) for x, y, w in v.CRACK] + list(v.SKYLIGHTS)
    # Along the crack, a shaft every 25 m or so.
    pts = []
    for a, b in zip(v.CRACK, v.CRACK[1:]):
        L = math.dist(a[:2], b[:2])
        for k in range(max(1, int(L / 25))):
            t = k / max(1, int(L / 25))
            pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, 0.3 * (a[2] + (b[2] - a[2]) * t)))
    pts += [(x, y, r * 0.6) for x, y, r in v.SKYLIGHTS]
    for k, (sx, sy, r) in enumerate(pts):
        top = v.roof_z(sx, sy) + 4.0
        # Down the sun's way to whatever it lands on.
        t = 1.0
        while t < 400:
            px, py = sx + SUN.x * t, sy + SUN.y * t
            pz = top + SUN.z * t
            if pz < d.floor(px, py):
                break
            t += 3.0
        for j in range(2):
            a = j * 2.1 + k
            c.place(ip.sun_beam(c, t + 4.0, max(3.0, r) * (0.6 + 0.25 * j), j), sx + 2 * math.cos(a), sy + 2 * math.sin(a), top, coll="Beams",
                    role="visual")
        gx, gy = sx + SUN.x * t, sy + SUN.y * t
        gz = d.floor(gx, gy)
        for j in range(3):
            d.light("sun", gx + (j - 1) * 4.0, gy, gz + 2.0)
        game_entity(c, "motes", gx, gy, gz + 8.0, radius=round(max(8.0, r * 2.0), 1), rate=8.0, color="#ffe6a0", rise=0.15, size=0.25)
    return holes


# ------------------------------------------------------------------ the worlds


def rim(d):
    """The crater's rim: scorched rock, impact glass, meteorites, an expedition's camp by
    the start, and the asteroid itself, lodged in the cave's wall where it came through."""
    v, c = d.v, d.c
    ring = (v.R_T1 + 20, v.R_RIM + 40)
    ok = lambda x, y, z: v.zone(x, y) == "crater" and dry(d, x, y, z) and clear(c, x, y, 5.0) and flat(d, x, y)
    put(d, [ip.meteorite(c, k, 1.6 + k) for k in range(3)], spots(d, 18, ok, 11, ring, gap=14.0), 11, role="both", coll="Rocks")
    put(d, [ip.glass_shards(c, k) for k in range(3)], spots(d, 40, ok, 13, ring, gap=6.0), 13, coll="Props")
    put(d, [ip.rock(c, "crater_rock", k, 2.5 + k) for k in range(3)], spots(d, 30, ok, 17, ring, gap=9.0), 17, role="both", coll="Rocks")
    # The cliffs above the road: rocks jutting out, glass glinting.
    wall = lambda x, y, z: v.zone(x, y) == "crater" and steep(d, x, y) and clear(c, x, y, 4.0) and dry(d, x, y, z)
    put(d, [ip.glass_shards(c, k) for k in range(3)], spots(d, 40, wall, 19, (v.R_RIM + 14, v.R_RIM + 48), gap=10.0), 19, scale=(1.2, 2.0))
    # The camp, on the rim just past the start: tents, a survey scope, warning signs.
    q = c.at(60.0)
    for k, (fwd, side, proto) in enumerate(((0, 1, ip.tent(c, 0)), (14, 1, ip.tent(c, 1)), (26, 1, ip.survey_scope(c)), (8, -1, ip.warning_sign(c, 0)),
                                             (40, -1, ip.warning_sign(c, 1)), (34, 1, ip.tent(c, 2)))):
        p = c.at(60.0 + fwd)
        o = p.side(side * (p.w / 2 + 4.5))
        if not clear(c, o.x, o.y, 2.0):
            continue
        c.place(proto, o.x, o.y, d.floor(o.x, o.y) - 0.1, rot=math.atan2(p.t.y, p.t.x) + (math.pi if side < 0 else 0.0), coll="Props", role="both")
        d.light("torch", o.x, o.y, d.floor(o.x, o.y) + 3.0)
    del q
    # The asteroid: in the outer wall above the start, under the crack's end, glowing.
    a = math.atan2(v.CRACK[0][1], v.CRACK[0][0])
    r = v.R_RIM + 38
    x, y = r * math.cos(a), r * math.sin(a)
    z = v.natural(x, y) + 2.0
    c.place(ip.meteorite(c, 3, 18.0), x, y, z, rot=0.7, coll="Landmarks", role="visual")
    d.light("asteroid", x, y, z)
    d.light("asteroid", x * 0.95, y * 0.95, z - 14)
    game_entity(c, "motes", x * 0.94, y * 0.94, z - 10, radius=40.0, rate=10.0, color="#ff9aa8", rise=0.4, size=0.3)
    hang(d, [ip.stalactites(c, "crater_rock", k, 8.0 + 3 * k) for k in range(3)], 30, 23, (v.R_T1, v.R_RIM + 30), 14.0)


def crystal(d):
    """The crystal wall: great clusters of cyan, violet and rose crystal growing out of
    the cliffs, needles along the ledges, crystals hanging from the roof, crystals by the
    road that flare as you pass."""
    v, c = d.v, d.c
    ring = (v.R_T2 + 20, v.R_T1 + 30)
    wall = lambda x, y, z: v.zone(x, y) == "crystal" and steep(d, x, y) and clear(c, x, y, 5.0) and dry(d, x, y, z)
    big = [ap.spire_cluster(c, k, 16.0 + 5 * k, mat=(AQUA, AMETHYST, ROSE)[k], accent=(AMETHYST, ROSE, AQUA)[k]) for k in range(3)]
    for k, (x, y, z) in enumerate(spots(d, 14, wall, 31, ring, gap=26.0)):
        c.place(big[k % 3], x, y, z - 2.0, rot=rnd(k * 3.1) * math.tau, scale=0.6 + 0.3 * rnd(k * 1.7), coll="Crystals", role="visual")
        d.light("crystal_cyan" if k % 2 else "crystal_violet", x, y, z + 8)
    small = [ap.needles(c, k, 8.0 + 3 * k, mat=(AQUA, AMETHYST, ROSE)[k]) for k in range(3)] + [vp.crystals(c, m, k) for k, m in enumerate((AQUA, AMETHYST, ROSE))]
    ok = lambda x, y, z: v.zone(x, y) == "crystal" and dry(d, x, y, z) and clear(c, x, y, 3.0)
    pts = spots(d, 70, ok, 37, ring, gap=7.0)
    put(d, small, pts, 37, scale=(0.5, 1.1), coll="Crystals")
    for k, (x, y, z) in enumerate(pts[::4]):
        d.light("crystal_cyan" if k % 2 else "crystal_violet", x, y, z + 3)
    hang(d, [ap.hanging(c, k, 8.0 + 3 * k, mat=(AQUA, AMETHYST)[k % 2]) for k in range(3)], 26, 41, (v.R_T2, v.R_T1 + 20), 12.0, coll="Crystals")
    hang(d, [ip.stalactites(c, "cave_ochre", k, 9.0 + 3 * k) for k in range(3)], 34, 43, (v.R_T2, v.R_T1 + 20), 14.0)
    # The flaring crystals along terrace one's road.
    s0, s1 = v.TO_ROAD(v.SEG[v.K["t1"]]), v.TO_ROAD(v.SEG[v.K["t1"] + 1])
    for k, s in enumerate(range(int(s0 + 20), int(s1 - 20), 22)):
        q = c.at(s)
        side = 1 if k % 2 else -1
        p = q.side(side * (q.w / 2 + 2.6))
        z = d.floor(p.x, p.y)
        if z < q.p.z - 3:
            continue
        col = "#5ae8ff" if k % 4 < 2 else "#d27aff"
        c.place(vp.crystals(c, AQUA if k % 4 < 2 else AMETHYST, k % 3), p.x, p.y, z - 0.3, rot=k, scale=0.45, coll="Crystals", role="visual")
        game_entity(c, "shimmer", p.x, p.y, z + 1.6, size=1.6, color=col)
    game_entity(c, "motes", 0.0, -v.R_T1, v.HEIGHT[v.K["t1"]] + 4, radius=120.0, rate=10.0, color="#9ae8ff", rise=0.2, size=0.3)


def jungle(d):
    """The Lost World ledge: ferns, cycads, tree ferns and horsetails on the ledges, vines
    and roots down the cliffs and from the roof, glowing fungi, sun through the holes."""
    v, c = d.v, d.c
    ring = (v.R_BOT + 20, v.R_T2 + 30)
    ok = lambda x, y, z: v.zone(x, y) == "jungle" and dry(d, x, y, z) and clear(c, x, y, 3.0) and flat(d, x, y, 2.5)
    put(d, [ip.cycad(c, k) for k in range(4)], spots(d, 50, ok, 51, ring, gap=6.0), 51, scale=(0.8, 1.3), coll="Plants")
    put(d, [ip.tree_fern(c, k) for k in range(3)], spots(d, 30, lambda x, y, z: ok(x, y, z) and clear(c, x, y, 6.0), 53, ring, gap=9.0), 53,
        scale=(0.8, 1.2), coll="Plants")
    put(d, [ip.horsetails(c, k) for k in range(3)], spots(d, 30, ok, 57, ring, gap=6.0), 57, coll="Plants")
    put(d, [pr.fern(c), pr.big_leaf_plant(c, 0), pr.big_leaf_plant(c, 1)], spots(d, 110, ok, 59, ring, gap=3.0), 59, scale=(0.8, 1.6),
        coll="Plants")
    wall = lambda x, y, z: v.zone(x, y) == "jungle" and steep(d, x, y) and clear(c, x, y, 4.0) and dry(d, x, y, z)
    put(d, [pr.fern(c, "glow_moss"), pr.fern(c)], spots(d, 70, wall, 61, ring, gap=6.0), 61, scale=(1.0, 1.8), coll="Plants")
    fungi = spots(d, 16, ok, 63, ring, gap=14.0)
    put(d, [ip.giant_fungi(c, k) for k in range(3)], fungi, 63, scale=(0.7, 1.1), coll="Plants")
    for x, y, z in fungi:
        d.light("fungus", x, y, z + 3)
    hang(d, [pr.vine_curtain(c, k, 12.0) for k in range(3)], 18, 67, (v.R_BOT, v.R_T2 + 20), 12.0)
    hang(d, [pr.hanging_roots(c, k, 5.0) for k in range(3)], 30, 69, (v.R_BOT, v.R_T2 + 20), 6.0)
    hang(d, [ip.stalactites(c, "moss_rock", k, 10.0) for k in range(3)], 24, 71, (v.R_BOT, v.R_T2 + 20), 12.0)
    game_entity(c, "motes", 0.0, v.R_T2, v.HEIGHT[v.K["t2"]] + 4, radius=130.0, rate=12.0, color="#c8ff7a", rise=0.05, size=0.22, blink=True)


def volcanic(d):
    """The bottom: black rock and lava. Spires standing in the lava lake round the core,
    glowing cracks, lava light everywhere, ash in the air."""
    v, c = d.v, d.c
    lake = lambda x, y, z: z < v.Z_BOTTOM - 4 and math.hypot(x, y) > v.R_HELIX + 22 and clear(c, x, y, 8.0)
    pts = spots(d, 16, lake, 81, (v.R_HELIX + 24, v.R_BOT - 20), gap=14.0)
    put(d, [ip.lava_spire(c, k, 10.0 + 4 * k) for k in range(3)], pts, 81, scale=(0.8, 1.3), coll="Rocks", sink=1.0)
    for x, y, z in pts:
        d.light("lava", x, y, z + 4)
    ok = lambda x, y, z: v.zone(x, y) == "volcanic" and dry(d, x, y, z) and clear(c, x, y, 4.0) and flat(d, x, y)
    put(d, [ip.rock(c, "black_rock", k, 2.0 + k, glow="fissure_glow") for k in range(3)], spots(d, 30, ok, 83, (v.R_BOT - 16, v.R_T2 - 20), gap=8.0),
        83, role="both", coll="Rocks")
    hang(d, [ip.stalactites(c, "black_rock", k, 8.0 + 3 * k) for k in range(3)], 26, 87, (v.R_HELIX + 30, v.R_BOT + 20), 14.0)
    # Light off the lava: the lake, round the core, and the cracks at every cliff's foot.
    for k in range(36):
        a = k * math.tau / 36
        for r in (v.R_HELIX + 30, v.R_BOT - 24):
            d.light("lava", r * math.cos(a), r * math.sin(a), v.Z_BOTTOM - 4)
    game_entity(c, "ashfall", 0.0, 0.0, 0.0, rate=40, radius=40)


def cracks(d):
    """A glow along every crack at the cliffs' feet (so you see where not to go)."""
    v = d.v
    for k in range(240):
        a = k * math.tau / 240
        for r in range(int(v.R_BOT), int(v.R_RIM), 3):
            x, y = r * math.cos(a), r * math.sin(a)
            zb = v.crack_floor(x, y)
            if zb is not None:
                d.light("lava", x, y, zb - 16)
                break


# ------------------------------------------------------------------ light


def light(d):
    v, c = d.v, d.c
    groups = ("Plants", "Props", "Crystals", "Cave Props", "Rocks")
    c.merge_props(groups, cell=200.0)
    built = [o for name in ("Landmarks", "Bridges") + groups for o in c.coll(name).objects if o.type == "MESH" and o.data.users == 1]
    land = [d.ter, d.roof, d.rims]
    every = land + built
    c.preset("sun", [d.ter, d.over] + built, 0.3)
    from kartipelago_tools import paint as _paint

    memo = {}

    def lit(w):
        k = (round(w.x), round(w.y), round(w.z))
        if k not in memo:
            memo[k] = d.sunlit(w.x, w.y, w.z)
        return memo[k]

    for ob in every:
        t = _paint.Target(ob, None)
        for li, vi, _ in t.corners:
            w = t.world[vi]
            if lit(w):
                continue
            t.mul(li, TINT[v.zone(w.x, w.y)])
        t.write()
    colours = {
        "crystal_cyan": (22.0, (0.7, 1.0, 1.0)),
        "crystal_violet": (22.0, (0.95, 0.75, 1.0)),
        "sun": (34.0, (1.0, 0.95, 0.75)),
        "lava": (36.0, (1.0, 0.6, 0.34)),
        "core": (70.0, (1.0, 0.82, 0.9)),
        "fungus": (16.0, (0.6, 1.0, 0.9)),
        "torch": (14.0, (1.0, 0.8, 0.5)),
        "asteroid": (60.0, (1.0, 0.6, 0.7)),
    }
    for kind, pts in d.lights.items():
        if kind in colours and pts:
            r, col = colours[kind]
            c.glow(every, pts, r, col, base=1.0)
    kit.paint.shade_roads(c.pieces, 0.45)


def build(c, v, ter):
    d = Dress(c, v, ter)
    shell(d)
    sunlight(d)
    rim(d)
    crystal(d)
    jungle(d)
    volcanic(d)
    cracks(d)
    d.light("core", 0.0, 0.0, v.Z_BOTTOM + 10)
    d.light("core", 0.0, 0.0, v.Z_TOP - 10)
    light(d)
    return d
