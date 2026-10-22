# Celestial Dragon Festival's land and water (see celestial_dragon_festival.py and
# cdf_land.py): the ground, the lagoon and its inlet, the Cloud Chasm and its sea of
# cloud, the karst islands, the waterfalls, the far kingdom, the light and the gameplay.
# The city, the palace, the observatory, the people, the dragon and the festival are
# cdf_town.py; the kit cdf_props.py.
# SPDX-License-Identifier: MIT

import math

import cdf_land as L
import course_kit as kit
from course_kit import bmesh, lerp, rnd

# ------------------------------------------------------------------ shared


class Scene:
    """What the scenery builders share."""

    def __init__(self, c):
        self.c = c
        self.ground_obs = []
        self.lights = {}  # kind -> [(x, y, z)]
        self.footprints = []  # (x, y, r): keep scatter and buildings clear
        self.cache = {}
        self.crowd = []  # villagers: [x, y, z, heading x, heading z, role, variant]
        self.launchers = []  # firework launch sites: (x, y, z)

    def light(self, kind, x, y, z):
        self.lights.setdefault(kind, []).append((x, y, z))

    MERGED = {"Palace": "Town", "Temple": "Town", "Market": "Town", "Landmarks": "Town", "Gardens": "Town", "Plants": "Props"}

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
    """Far enough from the race line."""
    smp, d = c.nearest(x, y)
    return d > smp.w / 2 + margin


# ------------------------------------------------------------------ the land


def land_mat(x, y, z, nz, d_road, w_road):
    if z < -3.0:
        if L.chasm_d(x, y) < L.CHASM_HW + 30:
            return ("cdf_abyss", "abyss")
        return ("pale_beach", "sand")
    if nz < 0.6:
        return ("cdf_karst", "wall")
    if nz < 0.8:
        return ("limestone_moss", "dirt")
    if z < 1.2:
        return ("pale_beach", "sand")
    if L.city(x, y) > 0.5 and d_road < 70:
        return ("temple_flag", "road")
    if math.hypot(x - L.PALACE[0], y - L.PALACE[1]) < 120 and z > 90:
        return ("temple_flag", "road")
    return ("cdf_grass", "grass")


def land(c, sc):
    x0, x1, y0, y1 = L.GRID

    def classify(cen, n, info):
        return land_mat(cen.x, cen.y, cen.z, n.z, info["d"], info["sample"].w)

    ter = c.terrain("Land", x0, x1, y0, y1, L.CELL, sc.info, classify, near=9.0, fade=12.0)
    sc.ground_obs = [ter]
    sc.land = ter

    def under(x, y):
        if c.nearest(x, y)[1] > 60:
            return None
        nt = sc.info(x, y)
        w, z = c.road_height(x, y, 9.0, 12.0, 0.2, nt)
        return lerp(nt, z, w) - 0.6

    c.underfloor_flat("Underfloor", x0, x1, y0, y1, L.CELL, under, c.lib("cdf_grass", "grass"))
    far_land(c)
    return ter


FAR = (-3600.0, 3600.0, -3600.0, 3800.0)
# The far kingdom: karst mountains round the lagoon, festival towns on their shoulders.
FAR_PEAKS = [  # (x, y, r, top)
    (-1100.0, 1300.0, 260.0, 260.0),
    (900.0, 1500.0, 300.0, 300.0),
    (1500.0, 500.0, 220.0, 220.0),
    (1300.0, -900.0, 260.0, 210.0),
    (-1300.0, -800.0, 280.0, 240.0),
    (-1600.0, 400.0, 240.0, 280.0),
    (200.0, 2300.0, 440.0, 400.0),
    (-300.0, -1600.0, 360.0, 260.0),
    (2000.0, 1900.0, 420.0, 360.0),
    (-2100.0, 1800.0, 420.0, 380.0),
]


def far_natural(x, y):
    X0, X1, Y0, Y1 = L.GRID
    if X0 <= x <= X1 and Y0 <= y <= Y1:
        return L.SEA - 4.0
    z = L.SEA + 1.5 * L.noise(x, y, 0.01, 2.0)
    for px, py, r, top in FAR_PEAKS:
        d = math.hypot(x - px, y - py) / r + 0.1 * L.noise(x, y, 0.008, px)
        if d < 1.4:
            k = (1.0 - L.sm((d - 0.55) / 0.5)) if d > 0.55 else 1.0
            z = max(z, L.SEA + (top - L.SEA) * k ** 0.6)
    return z


def far_land(c):
    X0, X1, Y0, Y1 = L.GRID

    def cls(cen, n, info):
        if X0 + 30 < cen.x < X1 - 30 and Y0 + 30 < cen.y < Y1 - 30:
            return None
        if cen.z < -0.5:
            return ("pale_beach", "sand")
        if n.z < 0.6:
            return ("cdf_karst", "wall")
        return ("cdf_grass", "grass")

    fx0, fx1, fy0, fy1 = FAR
    far = c.terrain("Far Land", fx0, fx1, fy0, fy1, 80.0, far_natural, cls, near=0.0, fade=1.0)
    far["kp_role"] = "visual"
    return far


# ------------------------------------------------------------------ water and cloud


def sheet(c, sc, name, z, region, mat, cell=None, role="both"):
    """A flat sheet at height z over every land cell inside `region` whose ground dips
    below z."""
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
    c.assign(ob, c.lib(*mat) if isinstance(mat, tuple) else c.lib(mat))
    return ob


def waters(c, sc):
    """The lagoon (deep: in it you're put back on the road), the far sea, the sea of cloud
    filling the Cloud Chasm and drifting round the mountains' feet."""
    sheet(c, sc, "Lagoon", L.WATER_Z, lambda x, y: L.chasm_d(x, y) > L.CHASM_HW + 20, ("cdf_lagoon", "deep_water"))
    X0, X1, Y0, Y1 = L.GRID
    bm = bmesh.new()
    R = 3600.0
    outer = [(-R, -R), (R, -R), (R, R + 200), (-R, R + 200)]
    inner = [(X0 + 2, Y0 + 2), (X1 - 2, Y0 + 2), (X1 - 2, Y1 - 2), (X0 + 2, Y1 - 2)]
    ov = [bm.verts.new((x, y, L.WATER_Z - 0.02)) for x, y in outer]
    iv = [bm.verts.new((x, y, L.WATER_Z - 0.02)) for x, y in inner]
    for k in range(4):
        bm.faces.new((ov[k], ov[(k + 1) % 4], iv[(k + 1) % 4], iv[k]))
    ob = c.mesh_object("Far Sea", bm, "Water", "visual")
    c.assign(ob, c.lib("cdf_lagoon"))
    # The sea of cloud in the chasm, well below the Star Bridge (visual only: a fall goes
    # straight through it to the abyss).
    sheet(c, sc, "Cloud Sea", 36.0, lambda x, y: L.chasm_d(x, y) < L.CHASM_HW + 60, "cdf_cloud", cell=L.CELL * 2, role="visual")


# ------------------------------------------------------------------ islands and falls


def islands(c, sc):
    """Karst islands in the lagoon: east of the Waterfall Bridge, round the western and
    northern cliffs, and far out; tall pillars with temples on some (cdf_town.py)."""
    import isles_props as ip

    k = 0
    sc.islands = []
    for i in range(150):
        x = L.GRID[0] + rnd(i * 3.1) * (L.GRID[1] - L.GRID[0])
        y = L.GRID[2] + rnd(i * 6.7) * (L.GRID[3] - L.GRID[2])
        if L.inside(x, y) or L.city(x, y) > 0.05 or sc.info(x, y) > -2:
            continue
        if not clear(c, x, y, 34.0) or not sc.free(x, y, 18):
            continue
        s_ = 0.8 + rnd(i * 2.2) * 1.1
        c.place(ip.karst(c, k % 6), x, y, L.SEA, rnd(i) * 6.28, s_, coll="Rocks Small", role="both")
        sc.footprints.append((x, y, 10 * s_ + 6))
        sc.islands.append((x, y, s_))
        k += 1
    # Round the edges of the world, far out.
    for i in range(110):
        a = rnd(i * 1.7) * math.tau
        r = 800 + rnd(i * 4.3) * 1100
        x = 40 + math.cos(a) * r
        y = 250 + math.sin(a) * r
        if L.GRID[0] < x < L.GRID[1] and L.GRID[2] < y < L.GRID[3]:
            continue
        s_ = 1.2 + rnd(i * 2.9) * 2.0
        c.place(ip.karst(c, i % 6), x, y, L.SEA - 2, rnd(i) * 6.28, s_, coll="Far Rocks", role="visual")
        if i % 9 == 0:
            sc.launchers.append((x, y, L.SEA + 60.0 * s_))


def falls(c, sc):
    """Waterfalls: off the Palace Mount's east cliffs into the inlet beside the Waterfall
    Bridge, off the islands across it, down into the Cloud Chasm, off the Observatory
    Pinnacle and down the western cliffs."""
    import props

    out = []

    def fall(name, x, y, ang, w, foot=L.WATER_Z + 0.3, throw=6.0, veils=3):
        # The lip: back a little into the cliff (opposite the way it falls).
        bx, by = x - 6 * math.cos(ang - math.pi / 2), y - 6 * math.sin(ang - math.pi / 2)
        top = sc.info(bx, by) - 0.8
        if top < foot + 8:
            return
        props.falls(c, name, x, y, top, foot, w * 0.7, w, facing=-1, throw=throw, bulge=1.4, veils=veils, angle=ang)
        out.append((x, y, top, w, ang, foot))

    E, W, N, S_ = math.pi / 2, -math.pi / 2, math.pi, 0.0  # (falls toward +X, -X, +Y, -Y)
    # Beside the Waterfall Bridge: the mountain's cliffs to the west, falling east...
    for k, y in enumerate((20.0, 95.0, 165.0)):
        x = L.INLET[0] - 2.0
        fall("Bridge Falls West %d" % (k + 1), x, y, E, 12.0 + 4 * (k % 2), throw=8.0)
    # The Cloud Chasm: off the mountain's north edge into the cloud.
    for k, x in enumerate((-130.0, -40.0, 30.0)):
        y = 356.0 + 4 * k
        fall("Chasm Falls %d" % (k + 1), x, y, N, 10.0, foot=30.0, throw=6.0, veils=2)
    # Off the pinnacle's north side and the western cliffs into the lagoon.
    fall("Pinnacle Falls", L.PINNACLE[0] - 10.0, L.PINNACLE[1] + 74.0, N, 9.0, throw=6.0, veils=2)
    for k, (x, y) in enumerate(((-142.0, 345.0), (-205.0, 200.0))):
        fall("West Falls %d" % (k + 1), x, y, W, 12.0, throw=7.0)
    for x, y, top, w, ang, foot in out:
        game_entity(c, "waterfall", x, y, foot, top=round(top, 1), width=w, heading=round(ang, 3), sound=False)
    sc.falls = out
    del S_


# ------------------------------------------------------------------ the light


def light(c, sc):
    """Night: cool moonlight from the south-east, the mountain's flanks dim, warm pools
    round every lantern and brazier, gold round the palace, blue-white round the
    observatory."""
    c.merge_props(("Props", "Town", "Rocks Small"), cell=520.0)
    c.merge_props(("Far Rocks",), cell=2400.0)
    land = [sc.land]
    built = [o for name in ("Bridges", "Arch", "Props", "Town", "Rocks Small") for o in c.coll(name).objects
             if o.type == "MESH" and o.data.users == 1]
    c.preset("sun", land + built, 0.3, color=(0.78, 0.8, 1.0))
    c.preset("bottoms", land, 0.3)

    def low(w):
        return w.z < 6.0

    c.glow([sc.land], [], 1.0, (1, 1, 1), base=(0.7, 0.72, 0.95), region=low)
    colours = {"lantern": (16.0, (1.0, 0.78, 0.5)), "gold": (26.0, (1.0, 0.86, 0.55)), "star": (24.0, (0.75, 0.82, 1.0)),
               "fire": (12.0, (1.0, 0.66, 0.36))}
    for kind, pts in sc.lights.items():
        if kind in colours and pts:
            r, col = colours[kind]
            c.glow(land + built, pts, r, col, base=1.0)
    kit.paint.shade_roads(c.pieces, 0.35)


# ------------------------------------------------------------------ gameplay


def gameplay(c, sc):
    A = L.at
    # Missing the Star Leap puts you back on its landing (first: the checkpoints keep clear
    # of it).
    c.entity("respawn", **{"from": round(L.LIP - 40, 1), "to": round(L.LAND + 8, 1), "at": round(L.LAND + 44, 1)})
    c.checkpoints(
        extra=[A("m1", 0.5), A("mx", 0.5), A("m3", 0.6), A("w2", 0.5), A("p2", 0.2), A("r1", 0.6), A("c1", 0.6), A("c3", 0.5),
               A("c4", 0.6), L.LIP - 50, L.LAND + 60, A("o2", 0.0), A("o3", 0.2), A("o3", 0.7), A("t1", 0.6), A("t2", 0.6), A("v1", 0.5),
               A("v2", 0.6), A("v3", 0.6), A("f1", 0.4)],
        height=9.0,
    )
    # Zippers: out of the market chicane, onto the bridge, out of the shrine's hairpin, up
    # the climb, the run-up to the Star Leap (three abreast: it makes the leap huge), down the terraces,
    # down the causeway, out of the overlook, and the start and finish straights.
    for at, across in ((A("st", 0.55), 0), (A("mx", 0.7), 0), (A("m3", 0.75), 0), (A("r1", 0.55), 0), (A("c3", 0.7), 0),
                       (L.LIP - 46.0, -6), (L.LIP - 46.0, 0), (L.LIP - 46.0, 6), (A("t1", 0.3), 0), (A("v1", 0.25), 0), (A("v3", 0.75), 0), (A("f1", 0.3), 0)):
        c.zipper(at, across)
    for at, across in ((A("m1", 0.7), 3), (A("m2", 0.5), -3), (A("w1", 0.5), 0), (A("p2", 0.5), 0), (A("c2", 0.6), 0),
                       (L.LAND + 70.0, -4), (A("o2", 0.5), 0), (A("t2", 0.4), -3), (A("v2", 0.4), 3)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in ((A("st", 0.8), -4, "red"), (A("st", 0.8), 4, "blue"), (A("mx", 0.4), 0, "green"),
                            (A("w1", 0.8), -4, "yellow"), (A("w1", 0.8), 4, "rainbow"), (A("p1", 0.6), 0, "red"),
                            (A("c3", 0.3), 0, "blue"), (L.LAND + 110.0, -4, "green"), (L.LAND + 110.0, 4, "yellow"),
                            (A("o3", 0.5), 0, "rainbow"), (A("t2", 0.8), 0, "red"), (A("v1", 0.6), -4, "blue"),
                            (A("v1", 0.6), 4, "green"), (A("v3", 0.3), 0, "yellow")):
        c.balloon(at, across, col)


# ------------------------------------------------------------------ build


def build(c, dc):
    import cdf_town as town

    sc = Scene(c)
    sc.dc = dc
    land(c, sc)
    waters(c, sc)
    town.footprints(c, sc)  # the palace's, the observatory's (before the islands)
    islands(c, sc)
    falls(c, sc)
    c.start_line()
    town.build(c, sc)
    gameplay(c, sc)
    town.entities(c, sc)
    light(c, sc)
