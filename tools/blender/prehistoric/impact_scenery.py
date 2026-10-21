# Impact Depths' land and its shell (see impact_depths.py and impact_land.py): the
# ground you drive on, the caves' roofs and the desert over them, the openings' rims,
# water and lava, the light, and the gameplay. The landmarks, plants and creatures'
# homes are impact_life.py; the props impact_props.py.
# SPDX-License-Identifier: MIT

import math

import course_kit as kit
import impact_land as L
from course_kit import Vector, bmesh, lerp, rnd

# ------------------------------------------------------------------ shared


class Scene:
    """What the scenery builders share."""

    def __init__(self, c):
        self.c = c
        self.ground_obs = []  # the land (for dropping props onto it)
        self.lights = {}  # name -> [(x, y, z)]: points painted with coloured light
        self.entities = []
        self.footprints = []  # (x, y, r): keep scatter clear of these
        self.cache = {}

    def light(self, kind, x, y, z):
        self.lights.setdefault(kind, []).append((x, y, z))

    def put(self, proto, x, y, z, rot=0.0, scale=1.0, coll="Props", role="visual"):
        return self.c.place(proto, x, y, z, rot, scale, coll=coll, role=role)

    def ground(self, x, y):
        z = self.c.ground_z(x, y, self.ground_obs)
        return z if z is not None else L.ground(x, y)[0]

    def free(self, x, y, r):
        return all(math.hypot(x - fx, y - fy) > r + fr for fx, fy, fr in self.footprints)

    def info(self, x, y):
        k = (round(x, 2), round(y, 2))
        v = self.cache.get(k)
        if v is None:
            v = L.ground(x, y)
            self.cache[k] = v
        return v


def game_entity(c, kind, x, y, z, **extra):
    gx, gy, gz = c.game(x, y, z)
    c.entity(kind, x=gx, y=gy, z=gz, **extra)


def clear(c, x, y, margin):
    """Far enough from the race line and the shortcut."""
    smp, d = c.nearest(x, y)
    if d <= smp.w / 2 + margin:
        return False
    return all((q.p.x - x) ** 2 + (q.p.y - y) ** 2 > (q.w / 2 + margin) ** 2 for q in c.extra_ground)


# ------------------------------------------------------------------ materials of the land


def strata(z):
    """The desert's sandstone layers, by height."""
    if z > 70:
        return "strata_cream"
    if z > 48:
        return "strata_orange" if int(z / 7) % 3 else "strata_red"
    if z > 30:
        return "strata_red" if int(z / 5) % 2 else "strata_orange"
    if z > 14:
        return "strata_rust"
    return "strata_purple"


def desert_floor(x, y):
    v = math.sin(x / 47.0 + 0.4) * math.cos(y / 39.0) + 0.5 * math.sin((x - y) / 21.0) + 0.25 * math.sin(x / 8.0 + y / 13.0)
    if v > 1.0:
        return "slickrock"
    if v < -0.7:
        return "red_sand"
    return "desert_sand"


ROCK = {
    "crater": "crater_rock",
    "crystal": "cave_ochre",
    "jungle": "moss_rock",
    "volcanic": "black_rock",
    "lair": "lair_rock",
    "core": "core_glass",
    "hidden": "cave_ochre_dark",
}


def land_mat(x, y, z, nz, d_road, w_road, biome):
    """A face's material and driving surface: by where it is, its slope and height."""
    near = d_road < w_road / 2 + 1.5
    rc = math.hypot(x - L.CRATER[0], y - L.CRATER[1])
    rs = math.hypot(x - L.SHAFT[0], y - L.SHAFT[1])
    if biome is None and rs < L.SHAFT_R + 6:
        biome = "shaft"
    elif biome is None and rc < L.CRATER_LIP:
        biome = "crater"
    if biome is None:  # the open desert
        if nz < 0.55:
            return (strata(z), "wall")
        if nz < 0.8:
            return ("talus", "loose_sand")
        if near:
            return ("dash_shoulder", "dirt")
        return (desert_floor(x, y), "loose_sand")
    if biome == "shaft":
        if z < -30.0:
            return ("core_abyss", "abyss")
        if nz < 0.55:
            if z < -2.0:
                return ("crystal_rock", "wall")
            if z < 8.0:
                return ("cave_ochre", "wall")
            return (strata(z + 6.0), "wall")
        if z < -11.0:
            return ("core_glass", "dirt")
        return ("pale_sand", "loose_sand")
    if biome == "crater":
        if nz < 0.6:
            return ("crater_rock", "wall")
        if near:
            return ("crater_ground", "dirt")
        if rc < L.CRATER_R0 + 14:
            g = math.sin(x / 9.0) * math.cos(y / 11.0) + 0.6 * math.sin((x + y) / 7.0)
            return ("impact_glass" if g > 0.9 else "crater_ground", "loose_sand")
        return ("crater_ground", "loose_sand")
    rock = ROCK[biome]
    if nz < 0.55:
        if biome == "crystal" and z < -2.0:
            return ("cave_ochre_dark", "wall")
        return (rock, "wall")
    if biome == "crystal":
        if z < L.CRYSTAL_WATER_Z + 0.4:
            return ("cave_ochre_dark", "dirt")
        return ("flowstone", "dirt") if nz > 0.8 else (rock, "dirt")
    if biome == "jungle":
        if z < L.JUNGLE_WATER_Z + 0.5:
            return ("jungle_mud", "mud")
        if nz < 0.8:
            return ("moss_rock", "dirt")
        return ("fern_floor", "grass")
    if biome == "volcanic":
        if z < -17.0:
            return ("black_rock", "dirt")
        return ("lava_crust", "dirt") if nz > 0.85 else ("black_rock", "dirt")
    if biome == "lair":
        if z < L.LAVA_Z + 1.0:
            return ("black_rock", "dirt")
        return ("ember_ash", "dirt") if nz > 0.8 else ("lair_rock", "dirt")
    if biome == "core":
        return ("core_glass", "dirt")
    if biome == "hidden":
        if z < L.HIDDEN_WATER_Z + 0.4:
            return ("cave_ochre_dark", "mud")
        return ("ruin_moss", "dirt") if nz > 0.8 else ("cave_ochre_dark", "dirt")
    return (rock, "dirt")


# ------------------------------------------------------------------ the land


def land(c, sc):
    x0, x1, y0, y1 = L.GRID

    def natural(x, y):
        return sc.info(x, y)[0]

    def classify(cen, n, info):
        smp = info["sample"]
        biome = L.cave(cen.x, cen.y)
        b = biome[2] if biome is not None and biome[0] < L.natural(cen.x, cen.y) - 0.5 else None
        return land_mat(cen.x, cen.y, cen.z, n.z, info["d"], smp.w, b)

    ter = c.terrain("Land", x0, x1, y0, y1, L.CELL, natural, classify, near=9.0, fade=12.0)
    sc.ground_obs = [ter]
    sc.land = ter

    # A hidden flat floor under the land near the roads, so nowhere can a kart fall
    # through the world: over steep faces (which count only as walls) there's always
    # ground just below. (Not in the core's abyss: its own floor puts you back.)
    def under(x, y):
        if c.nearest(x, y)[1] > 80 and all((q.p.x - x) ** 2 + (q.p.y - y) ** 2 > 80 ** 2 for q in c.extra_ground[::8]):
            return None
        if math.hypot(x - L.CORE[0], y - L.CORE[1]) < L.CORE_PIT_R - 3:
            return None
        nt = natural(x, y)
        w, z = c.road_height(x, y, 9.0, 12.0, 0.2, nt)
        return lerp(nt, z, w) - 0.6

    x0, x1, y0, y1 = L.GRID
    c.underfloor_flat("Underfloor", x0, x1, y0, y1, L.CELL, under, c.lib("crater_ground", "dirt"))
    # The abyss under the core: anything falling off the ring lands here and is put back.
    c.underfloor_flat("Abyss Floor", x0, x1, y0, y1, L.CELL,
                      lambda x, y: -46.8 if math.hypot(x - L.CORE[0], y - L.CORE[1]) < L.CORE_PIT_R + 10 else None,
                      c.lib("core_abyss", "abyss"))
    # Far off: the desert running on to the horizon, mesas standing about (no collision).
    far = far_land(c)
    sc.far = far
    return ter


FAR = (-3200.0, 3200.0, -3200.0, 3000.0)
FAR_MESAS = [  # (x, y, rx, ry, top)
    (-1100.0, 900.0, 260.0, 170.0, 150.0),
    (-300.0, 1250.0, 300.0, 150.0, 170.0),
    (700.0, 1150.0, 260.0, 180.0, 160.0),
    (1400.0, 450.0, 200.0, 280.0, 185.0),
    (1300.0, -600.0, 200.0, 300.0, 170.0),
    (650.0, -1400.0, 300.0, 160.0, 180.0),
    (-300.0, -1500.0, 280.0, 150.0, 160.0),
    (-1200.0, -1000.0, 240.0, 180.0, 175.0),
    (-1700.0, -300.0, 300.0, 180.0, 165.0),
    (-1500.0, 600.0, 260.0, 220.0, 180.0),
    (950.0, 350.0, 90.0, 120.0, 115.0),
    (-800.0, 380.0, 70.0, 60.0, 95.0),
]


def far_land(c):
    X0, X1, Y0, Y1 = L.GRID

    def nat(x, y):
        dx = max(X0 - x, x - X1, 0.0)
        dy = max(Y0 - y, y - Y1, 0.0)
        inside = dx == 0 and dy == 0
        h = L.desert(x, y) if not inside else L.Z_DESERT - 3.0
        for mx, my, rx, ry, top in FAR_MESAS:
            d = math.hypot((x - mx) / rx, (y - my) / ry) + 0.08 * L.noise(x, y, 0.01, mx)
            if d < 1.3:
                k = 1.0 - L.sm((d - 0.85) / 0.15) if d > 0.85 else 1.0
                hh = top * max(k, 0.2 * (1.0 - L.sm((d - 1.0) / 0.3)))
                if 0.15 < k < 1.0:
                    hh = round(hh / 12.0) * 6.0 + hh * 0.5
                h = max(h, L.Z_DESERT + hh)
        return h - (2.5 if inside else 0.0)

    def cls(cen, n, info):
        if X0 + 30 < cen.x < X1 - 30 and Y0 + 30 < cen.y < Y1 - 30:
            return None
        if n.z < 0.55:
            return (strata(cen.z - 20.0), "wall")
        if n.z < 0.8:
            return ("talus", "loose_sand")
        return (desert_floor(cen.x, cen.y), "loose_sand")

    fx0, fx1, fy0, fy1 = FAR
    far = c.terrain("Far Land", fx0, fx1, fy0, fy1, 80.0, nat, cls, near=0.0, fade=1.0)
    far["kp_role"] = "visual"
    return far


# ------------------------------------------------------------------ the shell over the caves


class _Grid:
    def __init__(self, sc):
        x0, x1, y0, y1 = L.GRID
        self.nx = int(round((x1 - x0) / L.CELL))
        self.ny = int(round((y1 - y0) / L.CELL))
        self.x0, self.x1, self.y0, self.y1 = x0, x1, y0, y1
        self.state = {}
        self.roof = {}
        self.top = {}
        self.biome = {}
        for j in range(self.ny + 1):
            for i in range(self.nx + 1):
                x, y = self.xy(i, j)
                z, (b, cov, roof, top) = sc.info(x, y)
                if cov:
                    st = "cov"
                elif b is None:
                    st = "rock"
                else:
                    st = "open"
                self.state[i, j] = st
                self.top[i, j] = top
                self.roof[i, j] = roof if roof is not None else top - L.ROOF_MIN
                self.biome[i, j] = b

    def xy(self, i, j):
        return (self.x0 + (self.x1 - self.x0) * i / self.nx, self.y0 + (self.y1 - self.y0) * j / self.ny)

    def roofed(self, i, j):
        """Is cell (i, j) under the roof (and the desert over it)?"""
        if not (0 <= i < self.nx and 0 <= j < self.ny):
            return False
        sts = [self.state[k] for k in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))]
        return "open" not in sts and "cov" in sts


def shell(c, sc):
    """The caves' roofs, the desert over them and the rims of every opening (the crater's
    cave mouth, the skylights, the shaft's portal): separate meshes over the land."""
    g = _Grid(sc)
    sc.grid = g
    roof_bm, top_bm, rim_bm = bmesh.new(), bmesh.new(), bmesh.new()
    rv, tv = {}, {}
    roof_mat, top_mat, rim_mat = [], [], []

    def vert(bm, cache, k, z):
        v = cache.get(k)
        if v is None:
            x, y = g.xy(*k)
            v = bm.verts.new((x, y, z))
            cache[k] = v
        return v

    for j in range(g.ny):
        for i in range(g.nx):
            if not g.roofed(i, j):
                continue
            ks = ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))
            bs = [g.biome[k] for k in ks if g.biome[k]]
            biome = max(set(bs), key=bs.count) if bs else "crystal"
            r = [vert(roof_bm, rv, k, g.roof[k]) for k in ks]
            roof_bm.faces.new(list(reversed(r)))
            roof_mat.append(ROOF.get(biome, "cave_ochre_dark"))
            t = [vert(top_bm, tv, k, g.top[k]) for k in ks]
            top_bm.faces.new(t)
            x, y = g.xy(i, j)
            top_mat.append(_top_mat(x + 2.5, y + 2.5, g.top[ks[0]]))
            # The rims: each edge onto an opening gets a wall from the roof up to the top.
            for (a, b), (di, dj) in (((ks[0], ks[1]), (0, -1)), ((ks[1], ks[2]), (1, 0)), ((ks[2], ks[3]), (0, 1)), ((ks[3], ks[0]), (-1, 0))):
                if g.roofed(i + di, j + dj):
                    continue
                if g.state[a] != "cov" and g.state[b] != "cov":
                    continue
                if not (0 <= i + di < g.nx and 0 <= j + dj < g.ny):
                    continue
                pa = Vector((*g.xy(*a), 0))
                pb = Vector((*g.xy(*b), 0))
                q = [rim_bm.verts.new((pa.x, pa.y, g.roof[a] - 0.3)), rim_bm.verts.new((pb.x, pb.y, g.roof[b] - 0.3)),
                     rim_bm.verts.new((pb.x, pb.y, g.top[b] + 0.05)), rim_bm.verts.new((pa.x, pa.y, g.top[a] + 0.05))]
                f = rim_bm.faces.new(q)
                f.normal_update()
                out = Vector((di, dj, 0))
                if f.normal.dot(out) < 0:
                    f.normal_flip()
                zmid = (g.top[a] + g.roof[a]) / 2
                rim_mat.append(ROOF.get(biome, "cave_ochre") if zmid < L.Z_DESERT - 10 else strata(zmid))
    obs = []
    for bm, mats, name in ((roof_bm, roof_mat, "Cave Roof"), (top_bm, top_mat, "Desert Over"), (rim_bm, rim_mat, "Cave Rims")):
        ob = c.mesh_object(name, bm, "Shell", "visual")
        groups = {}
        for fi, m in enumerate(mats):
            groups.setdefault(m, []).append(fi)
        for m, faces in groups.items():
            c.assign(ob, c.lib(m), faces)
        ob.data.shade_flat() if name == "Cave Rims" else ob.data.shade_smooth()
        obs.append(ob)
    sc.roof, sc.over, sc.rims = obs
    return obs


ROOF = {
    "crater": "crater_rock",
    "crystal": "cave_ochre_dark",
    "jungle": "moss_rock",
    "volcanic": "black_rock",
    "lair": "lair_rock",
    "core": "core_glass",
    "hidden": "cave_ochre_dark",
}


def _top_mat(x, y, z):
    rc = math.hypot(x - L.CRATER[0], y - L.CRATER[1])
    if rc < L.CRATER_LIP:
        return "crater_ground"
    return desert_floor(x, y)


# ------------------------------------------------------------------ water and lava


def sheet(c, sc, name, z, region, mat, surface=None, role="both", coll="Water", cell=None):
    """A flat sheet of water (or lava) at height z over every land cell inside `region`
    whose ground dips below z."""
    g = sc.grid
    bm = bmesh.new()
    vs = {}

    def v(k):
        p = vs.get(k)
        if p is None:
            x, y = g.xy(*k)
            p = bm.verts.new((x, y, z))
            vs[k] = p
        return p

    for j in range(g.ny):
        for i in range(g.nx):
            x, y = g.xy(i, j)
            cx, cy = x + L.CELL / 2, y + L.CELL / 2
            if not region(cx, cy):
                continue
            ks = ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))
            lo = min(sc.info(*g.xy(*k))[0] for k in ks)
            if lo > z - 0.05:
                continue
            bm.faces.new([v(k) for k in ks])
    if not bm.faces:
        bm.free()
        return None
    ob = c.mesh_object(name, bm, coll, role)
    c.assign(ob, c.lib(mat, surface))
    return ob


WATER_MATS = {
    "Blue Lake": "depths_water",
    "Crystal Stream": "depths_stream",
    "Turquoise Lake": "jungle_lake",
    "Jungle River": "jungle_river",
    "Black Pool": "dark_pool",
    "Lava Lake": "lava_flow",
    "West Lava River": "lava_flow",
    "East Lava River": "lava_flow",
}


def waters(c, sc):
    """The lakes, rivers and pools, and the lava (lakes are sheets over wherever the land
    dips below them; rivers ribbons, so they flow)."""
    for w in L.WATERS:
        mat = WATER_MATS[w["name"]]
        if "channel" in w:
            c.ribbon(w["name"], L.ribbon_path(w), 10.0, 0.0, c.lib(mat))
            continue

        def region(x, y, w=w):
            q = L.cave(x, y)
            if q is None or q[2] != w["biome"] or q[3] < -6:
                return False
            return w.get("lair") or L.in_water(w, x, y, margin=0.0 if w.get("pool") else 6.0) > 0

        sheet(c, sc, w["name"], w["z"], region, mat)
    sheet(c, sc, "Core Glow", -38.0, lambda x, y: math.hypot(x - L.CORE[0], y - L.CORE[1]) < L.CORE_PIT_R + 3, "core_abyss", role="visual")


# ------------------------------------------------------------------ the light


def light(c, sc):
    """Paint the light: the desert in full sun; every cave dim and tinted by its own
    world, lit back up round its crystals, lava, sunbeams and the core."""
    land = [sc.land, sc.roof, sc.rims] + [o for o in c.coll("Water").objects if o.type == "MESH"]
    groups = ("Plants", "Props", "Crystals", "Cave Props", "Rocks", "Ruins", "Outpost")
    c.merge_props(groups, cell=200.0)
    built = [o for name in ("Landmarks", "Bridges", "Arch") + groups for o in c.coll(name).objects if o.type == "MESH" and o.data.users == 1]
    joined = []
    every = land + built + joined
    c.preset("sun", [sc.land, sc.over] + built, 0.35)
    c.preset("bottoms", [sc.land], 0.3)

    memo = {}

    def where(w):
        k = (round(w.x * 0.5), round(w.y * 0.5))
        v = memo.get(k)
        if v is None:
            q = L.cave(w.x, w.y)
            v = (q[2] if q is not None and q[3] > -10 else None, L.natural(w.x, w.y))
            memo[k] = v
        return v

    def under(w):
        b, n = where(w)
        return b is not None and w.z < n - 2.0

    tint = {
        "crater": (0.62, 0.52, 0.5),
        "crystal": (0.52, 0.5, 0.66),
        "jungle": (0.58, 0.7, 0.52),
        "volcanic": (0.5, 0.36, 0.34),
        "lair": (0.5, 0.3, 0.28),
        "core": (0.6, 0.46, 0.7),
        "hidden": (0.36, 0.44, 0.42),
    }
    shaft = (0.72, 0.62, 0.8)
    from kartipelago_tools import paint as _paint

    for ob in every:
        t = _paint.Target(ob, None)
        for li, v, _ in t.corners:
            w = t.world[v]
            b, n = where(w)
            if b is not None and w.z < n - 2.0:
                t.mul(li, tint[b])
            elif math.hypot(w.x - L.SHAFT[0], w.y - L.SHAFT[1]) < L.SHAFT_R + 4 and w.z < 22:
                k = L.sm((22 - w.z) / 30.0)
                t.mul(li, [1 + (c_ - 1) * k for c_ in shaft])
        t.write()
    colours = {
        "crystal_cyan": (24.0, (0.7, 1.0, 1.0)),
        "crystal_violet": (24.0, (0.95, 0.75, 1.0)),
        "sun": (30.0, (1.0, 0.95, 0.75)),
        "lava": (40.0, (1.0, 0.62, 0.36)),
        "core": (70.0, (1.0, 0.82, 0.9)),
        "fungus": (16.0, (0.6, 1.0, 0.9)),
        "torch": (16.0, (1.0, 0.8, 0.5)),
        "asteroid": (60.0, (1.0, 0.6, 0.7)),
    }
    for kind, pts in sc.lights.items():
        if kind not in colours or not pts:
            continue
        r, col = colours[kind]
        c.glow(every, pts, r, col, base=1.0, region=under if kind not in ("asteroid", "core") else None)
    kit.paint.shade_roads(c.pieces + getattr(c, "lanes", []), 0.45)


# ------------------------------------------------------------------ build


def build(c, dc):
    import impact_life as life

    sc = Scene(c)
    sc.dc = dc
    life.shortcut(c, sc)  # first: the land meets its road
    land(c, sc)
    shell(c, sc)
    waters(c, sc)
    c.start_line()
    life.build(c, sc)
    light(c, sc)
