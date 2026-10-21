# Dragon Isles' land and water (see dragon_isles.py and isles_land.py): the ground, the
# lagoon, the headland and the outcrop the tunnels bore through, the gorge's river and
# the falls, the far kingdom, the light and the gameplay. The buildings, gardens, people
# and the dragon's path are isles_town.py; the kit isles_props.py.
# SPDX-License-Identifier: MIT

import math

import course_kit as kit
import isles_land as L
from course_kit import Vector, bmesh, lerp, rnd

# ------------------------------------------------------------------ shared


class Scene:
    """What the scenery builders share."""

    def __init__(self, c):
        self.c = c
        self.ground_obs = []
        self.lights = {}  # kind -> [(x, y, z)]
        self.footprints = []  # (x, y, r): keep scatter and buildings clear
        self.cache = {}
        self.crowd = []  # villagers: [x, y, z, heading, kind, variant]

    def light(self, kind, x, y, z):
        self.lights.setdefault(kind, []).append((x, y, z))

    # Buildings of every quarter share one collection, so the merge (light()) joins
    # them by map square: far fewer draw calls than one merged mesh per quarter.
    MERGED = {"Temple": "Town", "Harbour": "Town", "Gardens": "Town", "Landmarks": "Town", "Plants": "Props"}

    def put(self, proto, x, y, z, rot=0.0, scale=1.0, coll="Props", role="visual"):
        return self.c.place(proto, x, y, z, rot, scale, coll=self.MERGED.get(coll, coll), role=role)

    def ground(self, x, y):
        z = self.c.ground_z(x, y, self.ground_obs)
        return z if z is not None else self.info(x, y)

    def info(self, x, y):
        k = (round(x, 2), round(y, 2))
        v = self.cache.get(k)
        if v is None:
            v = L.ground(x, y)
            self.cache[k] = v
        return v

    def free(self, x, y, r):
        return all(math.hypot(x - fx, y - fy) > r + fr for fx, fy, fr in self.footprints)


def game_entity(c, kind, x, y, z, **extra):
    gx, gy, gz = c.game(x, y, z)
    c.entity(kind, x=gx, y=gy, z=gz, **extra)


def clear(c, x, y, margin):
    """Far enough from the race line and the shortcut."""
    smp, d = c.nearest(x, y)
    if d <= smp.w / 2 + margin:
        return False
    return all((q.p.x - x) ** 2 + (q.p.y - y) ** 2 > (q.w / 2 + margin) ** 2 for q in c.extra_ground)


def road_rot(q):
    return math.atan2(q.t.y, q.t.x)


# ------------------------------------------------------------------ the land


def land_mat(x, y, z, nz, d_road, w_road):
    near = d_road < w_road / 2 + 1.5
    if z < -0.6:
        return ("pale_beach", "sand")
    if nz < 0.55:
        return ("limestone", "wall")
    if nz < 0.8:
        return ("limestone_moss", "dirt")
    if z < 1.4:
        return ("pale_beach", "sand")
    if L.harbour_shore(x, y) > 0.5 and z < 6:
        return ("village_cobble", "dirt")
    if L.canal_d(x, y) < L.CANAL_HW + 3 and z < 4:
        return ("stone_base", "dirt")
    if math.hypot(x - L.TEMPLE[0], y - L.TEMPLE[1]) < 85 and not near:
        v = math.sin(x / 7.0) * math.cos(y / 9.0)
        return ("flowerbed", "grass") if v > 0.55 else ("lush_grass", "grass")
    return ("lush_grass", "grass")


def land(c, sc):
    x0, x1, y0, y1 = L.GRID

    def classify(cen, n, info):
        return land_mat(cen.x, cen.y, cen.z, n.z, info["d"], info["sample"].w)

    ter = c.terrain("Land", x0, x1, y0, y1, L.CELL, sc.info, classify, near=9.0, fade=12.0)
    sc.ground_obs = [ter]
    sc.land = ter

    def under(x, y):
        if c.nearest(x, y)[1] > 70 and all((q.p.x - x) ** 2 + (q.p.y - y) ** 2 > 70 ** 2 for q in c.extra_ground[::8]):
            return None
        nt = sc.info(x, y)
        w, z = c.road_height(x, y, 9.0, 12.0, 0.2, nt)
        return lerp(nt, z, w) - 0.6

    c.underfloor_flat("Underfloor", x0, x1, y0, y1, L.CELL, under, c.lib("lush_grass", "grass"))
    far_land(c)
    return ter


FAR = (-3600.0, 3600.0, -3400.0, 4000.0)
FAR_PEAKS = [  # (x, y, r, top): the far kingdom's mountains (the palace's is first)
    (L.PALACE[0], L.PALACE[1], 170.0, L.PALACE_Z),
    (-700.0, 1100.0, 220.0, 240.0),
    (900.0, 1200.0, 260.0, 280.0),
    (1500.0, 300.0, 200.0, 220.0),
    (1300.0, -900.0, 240.0, 200.0),
    (-1300.0, -700.0, 260.0, 230.0),
    (-1500.0, 500.0, 220.0, 260.0),
    (200.0, 2200.0, 420.0, 380.0),
    (-1100.0, 2000.0, 380.0, 340.0),
    (1700.0, 1900.0, 400.0, 360.0),
]


def far_natural(x, y):
    X0, X1, Y0, Y1 = L.GRID
    inside = X0 <= x <= X1 and Y0 <= y <= Y1
    if inside:
        return L.SEA - 4.0
    z = L.SEA + 1.5 * L.noise(x, y, 0.01, 2.0)
    for px, py, r, top in FAR_PEAKS:
        d = math.hypot(x - px, y - py) / r + 0.1 * L.noise(x, y, 0.008, px)
        if d < 1.4:
            k = (1.0 - L.sm((d - 0.55) / 0.5)) if d > 0.55 else 1.0
            z = max(z, L.SEA + (top - L.SEA) * k ** 0.6)
    # The great karst wall to the west carries on north and south.
    if x < -380:
        z = max(z, 70.0 + 30.0 * L.noise(x, y, 0.01, 4.0))
    return z


def far_land(c):
    X0, X1, Y0, Y1 = L.GRID

    def cls(cen, n, info):
        if X0 + 30 < cen.x < X1 - 30 and Y0 + 30 < cen.y < Y1 - 30:
            return None
        if cen.z < -0.5:
            return ("pale_beach", "sand")
        if n.z < 0.6:
            return ("limestone", "wall")
        return ("limestone_moss", "grass")

    fx0, fx1, fy0, fy1 = FAR
    far = c.terrain("Far Land", fx0, fx1, fy0, fy1, 80.0, far_natural, cls, near=0.0, fade=1.0)
    far["kp_role"] = "visual"
    return far


# ------------------------------------------------------------------ rocks the tunnels go through


def tunnels(c, sc):
    """The headland (the Ancient Dragon Passage bores through it) and the outcrop on the
    cliff's upper ledge (a short tunnel)."""
    bands = [(1.0, 0.0), (1.0, 0.2), (0.92, 0.3), (0.9, 0.62), (0.8, 0.7), (0.74, 0.92), (0.6, 1.0)]
    # Centred on the passage, long side along it, so the tunnel runs right through.
    qa, qb = c.at(L.S[36] - 4), c.at(L.S[37] + 30)
    hx, hy = (qa.p.x + qb.p.x) / 2 - 8.0, (qa.p.y + qb.p.y) / 2 - 6.0
    ang = math.atan2(qb.p.y - qa.p.y, qb.p.x - qa.p.x)
    rock = c.rock_mass("Headland", hx, hy, 60.0, 50.0, 46.0, z0=-6.0, n=32, seed=7, bands=bands, angle=ang, base=2.0)
    c.tunnel(rock, L.S[36] - 4, L.S[37] + 30, half=c.width / 2 + 2.5, height=11.0, pad=20.0)
    c.paint_rock(rock, ("limestone", "wall"), ("limestone_moss", "grass"), top_z=20.0)
    sc.headland = rock
    # The outcrop over the upper ledge.
    q = c.at(L.S[11] + 30)
    out = q.side(-9.0)
    knob = [(1.0, 0.0), (0.97, 0.3), (0.86, 0.55), (0.72, 0.78), (0.5, 0.94), (0.28, 1.0)]
    rock2 = c.rock_mass("Outcrop", out.x, out.y, 25.0, 22.0, q.p.z + 26.0, z0=q.p.z - 14.0, n=18, seed=3, bands=knob,
                        angle=road_rot(q), base=q.p.z - 4.0)
    c.tunnel(rock2, L.S[11] + 12, L.S[11] + 48, half=c.width / 2 + 2.5, height=10.0, pad=18.0)
    c.paint_rock(rock2, ("limestone", "wall"), ("limestone_moss", "grass"), top_z=q.p.z + 12.0)
    sc.outcrop = rock2
    sc.ground_obs += [rock, rock2]


# ------------------------------------------------------------------ water


def sheet(c, sc, name, z, region, mat, cell=None, role="both"):
    """A flat water sheet at height z over every land cell inside `region` whose ground
    dips below z (cells of the land's grid)."""
    x0, x1, y0, y1 = L.GRID
    cell = cell or L.CELL * 2
    nx = int(round((x1 - x0) / cell))
    ny = int(round((y1 - y0) / cell))
    bm = bmesh.new()
    vs = {}

    def v(i, j):
        p = vs.get((i, j))
        if p is None:
            p = bm.verts.new((x0 + i * cell, y0 + j * cell, z))
            vs[i, j] = p
        return p

    for j in range(ny):
        for i in range(nx):
            xa, ya = x0 + i * cell, y0 + j * cell
            if not region(xa + cell / 2, ya + cell / 2):
                continue
            lo = min(sc.info(xa + dx, ya + dy) for dx in (0, cell / 2, cell) for dy in (0, cell / 2, cell))
            if lo > z - 0.05:
                continue
            bm.faces.new((v(i, j), v(i + 1, j), v(i + 1, j + 1), v(i, j + 1)))
    if not bm.faces:
        bm.free()
        return None
    ob = c.mesh_object(name, bm, "Water", role)
    c.assign(ob, c.lib(mat))
    return ob


def waters(c, sc):
    """The lagoon (living turquoise water), the far sea, the canal, the gorge's river."""
    sheet(c, sc, "Lagoon", L.WATER_Z, lambda x, y: True, "lagoon")
    # The far sea, beyond the land's grid (no collision).
    X0, X1, Y0, Y1 = L.GRID
    bm = bmesh.new()
    R = 3600.0
    outer = [(-R, -R), (R, -R), (R, R + 400), (-R, R + 400)]
    inner = [(X0 + 2, Y0 + 2), (X1 - 2, Y0 + 2), (X1 - 2, Y1 - 2), (X0 + 2, Y1 - 2)]
    ov = [bm.verts.new((x, y, L.WATER_Z - 0.02)) for x, y in outer]
    iv = [bm.verts.new((x, y, L.WATER_Z - 0.02)) for x, y in inner]
    for k in range(4):
        bm.faces.new((ov[k], ov[(k + 1) % 4], iv[(k + 1) % 4], iv[k]))
    ob = c.mesh_object("Far Sea", bm, "Water", "visual")
    c.assign(ob, c.lib("lagoon"))
    # The gorge's river: from the foot of the great falls down to the lagoon.
    path = []
    for k in range(40):
        y = L.FALLS_Y - 10 - k * 8.0
        x = L.RIVER_X + 8.0 * math.sin(y / 70.0)
        path.append((x, y, 34.0, L.WATER_Z + 0.25))
    c.ribbon("Gorge River", path, 30.0, 0.0, c.lib("canal_water"), role="visual")
    # Foam where the river meets the lagoon, and round the falls' foot.
    c.disc("River Mouth Foam", L.RIVER_X + 6, path[-1][1] + 6, 22.0, L.WATER_Z + 0.3, c.lib("shore_foam"), role="visual", n=24,
           wobble=0.2)


# ------------------------------------------------------------------ the light


def light(c, sc):
    """Paint the light: the kingdom in warm afternoon sun, the tunnels dim, warm round the
    lanterns, the passage's old carvings faintly teal."""
    groups = ("Props", "Town", "Palace", "Rocks Small", "Far Rocks")
    c.merge_props(("Props", "Town", "Palace", "Rocks Small"), cell=260.0)
    c.merge_props(("Far Rocks",), cell=2400.0)
    land = [sc.land, sc.headland, sc.outcrop]
    built = [o for name in ("Bridges", "Arch") + groups for o in c.coll(name).objects if o.type == "MESH" and o.data.users == 1]
    c.preset("sun", land + built, 0.32)
    c.preset("bottoms", land, 0.25)

    def in_tunnel(w):
        smp, d = c.nearest(w.x, w.y)
        if d > 16:
            return False
        s = smp.s
        return ((L.S[36] - 2 < s < L.S[37] + 26) or (L.S[11] + 12 < s < L.S[11] + 48)) and w.z < smp.p.z + 12

    c.glow([sc.land, sc.headland, sc.outcrop] + built, [], 1.0, (1, 1, 1), base=(0.55, 0.5, 0.48), region=in_tunnel)
    colours = {"lantern": (16.0, (1.0, 0.86, 0.62)), "teal": (12.0, (0.7, 1.0, 0.95))}
    for kind, pts in sc.lights.items():
        if kind in colours and pts:
            r, col = colours[kind]
            c.glow(land + built, pts, r, col, base=1.0)
    kit.paint.shade_roads(c.pieces + getattr(c, "lanes", []), 0.4)


# ------------------------------------------------------------------ gameplay


def shortcut(c, sc):
    """The Courtyard Passage: straight through the temple's courtyard."""
    import dry_gulch

    dry_gulch.lane(c, "Courtyard Passage", L.SHORTCUT, "temple_flag", "road", width=11.0, shoulder=1.0,
                   shoulder_mat=("flowerbed", "grass"), step=4.0)


def gameplay(c, sc):
    a, b = L.SHORT_A, L.SHORT_B
    apex = L.S[19] + 23.0
    gates = c.checkpoints(
        extra=[L.S[2] + 10, L.S[5], L.S[9] + 30, L.S[11] + 30, L.S[14] + 70, a - 10, apex, b + 12, L.S[26] + 60, L.S[29] + 45,
               L.S[31] + 20, L.S[34] + 40, L.S[37] + 30, L.S[39] + 10],
        avoid=[(a - 2, apex - 8), (apex + 8, b + 2)],
        height=9.0,
    )
    main_gate = min(gates.items(), key=lambda kv: abs(kv[0] - apex))[1]
    pts = L.SHORTCUT
    k = len(pts) // 2
    c.alt_gate(main_gate, "courtyard_passage", [pts[k - 4], pts[k], pts[k + 4]], width=15.0, height=8.0)
    c.path_curve("Courtyard Passage Path", [p for p in pts[::4]] + [pts[-1]], closed=False)
    for at, across in ((L.S[0] + 50, 0), (L.S[8] + 30, 0), (L.S[14] + 30, 0), (L.S[25] + 60, 0), (L.S[29] + 30, 0), (L.S[33] + 60, 0),
                       (L.S[38] + 15, 0)):
        c.zipper(at, across)
    for at, across in ((L.S[2] + 5, 0), (L.S[6] + 10, 3), (L.S[11] + 5, 0), (L.S[19] + 20, -3), (L.S[27] + 60, 3), (L.S[33] + 110, -3),
                       (L.S[36] + 40, 0), (L.S[40] + 10, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in ((L.S[0] + 70, -5, "red"), (L.S[0] + 70, 5, "blue"), (L.S[5] + 10, 0, "green"), (L.S[9] + 50, 0, "yellow"),
                            (L.S[13] + 20, -4, "rainbow"), (L.S[13] + 20, 4, "red"), (L.S[17], 0, "blue"), (L.S[25] + 100, 0, "green"),
                            (L.S[28] + 40, -4, "yellow"), (L.S[28] + 40, 4, "rainbow"), (L.S[33] + 20, 0, "red"),
                            (L.S[38] + 30, -4, "blue"), (L.S[38] + 30, 4, "green")):
        c.balloon(at, across, col)


# ------------------------------------------------------------------ build


def build(c, dc):
    import isles_town as town

    sc = Scene(c)
    sc.dc = dc
    shortcut(c, sc)  # first: the land meets its road
    land(c, sc)
    tunnels(c, sc)
    waters(c, sc)
    c.start_line()
    town.build(c, sc)
    gameplay(c, sc)
    town.entities(c, sc)
    light(c, sc)
