# Dragon Canyon's land and water (see dragon_canyon.py and dcanyon_land.py): the canyon
# ground, the far desert of spires, the river and the oasis pool, the mesa the caverns
# bore through, the light, and the gameplay (with the Quarry Service Road). The
# buildings, bones, quarry, life and the dragon's flight are dcanyon_town.py.
# SPDX-License-Identifier: MIT

import math

import course_kit as kit
import dcanyon_land as L
from course_kit import bmesh, lerp

# ------------------------------------------------------------------ shared


class Scene:
    """What the scenery builders share."""

    MERGED = {"Landmarks": "Town", "Quarry": "Town", "Oasis": "Town", "Plants": "Props"}

    def __init__(self, c):
        self.c = c
        self.ground_obs = []
        self.lights = {}
        self.footprints = []
        self.cache = {}
        self.crowd = []

    def light(self, kind, x, y, z):
        self.lights.setdefault(kind, []).append((x, y, z))

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
    c.entity(kind, x=round(gx, 2), y=round(gy, 2), z=round(gz, 2), **extra)


def clear(c, x, y, margin):
    """Far enough from the race line and the shortcut."""
    smp, d = c.nearest(x, y)
    if d <= smp.w / 2 + margin:
        return False
    return all((q.p.x - x) ** 2 + (q.p.y - y) ** 2 > (q.w / 2 + margin) ** 2 for q in c.extra_ground)


# ------------------------------------------------------------------ the land


def land_mat(x, y, z, nz, d_road, w_road):
    near = d_road < w_road / 2 + 2.0
    rd = L.river_d(x, y)
    if rd < L.RIVER_HW + 5 and z < 3.0:
        return ("river_sand", "sand")
    od = math.hypot(x - L.OASIS[0], y - L.OASIS[1])
    if od < L.OASIS_R + 26 and nz > 0.75 and z < 16:
        return ("oasis_grass", "grass") if not near else ("dust_shoulder", "dirt")
    if nz < 0.5:
        return ("canyon_cliff_shade", "wall") if z < 18 + 6 * math.sin(x / 37.0 + y / 23.0) else ("canyon_cliff", "wall")
    if nz < 0.78:
        return ("canyon_scree", "loose_sand")
    if near:
        return ("dust_shoulder", "dirt")
    if math.hypot(x - 300.0, y - 40.0) < 70 and z < 40:
        return ("quarry_dust", "dirt")
    return ("canyon_ledge", "dirt")


def land(c, sc):
    x0, x1, y0, y1 = L.GRID

    def classify(cen, n, info):
        return land_mat(cen.x, cen.y, cen.z, n.z, info["d"], info["sample"].w)

    ter = c.terrain("Land", x0, x1, y0, y1, L.CELL, sc.info, classify, near=8.0, fade=10.0, fine=3)
    sc.ground_obs = [ter]
    sc.land = ter

    # A hidden flat floor just under the land near every road (over steep faces, which
    # count only as walls, there's always ground below), and the river's bed, which
    # puts you back on the road.
    def under(x, y):
        if c.nearest(x, y)[1] > 60 and all((q.p.x - x) ** 2 + (q.p.y - y) ** 2 > 60 ** 2 for q in c.extra_ground[::8]):
            return None
        nt = sc.info(x, y)
        w, z = c.road_height(x, y, 8.0, 10.0, 0.2, nt)
        return lerp(nt, z, w) - 0.6

    c.underfloor_flat("Underfloor", x0, x1, y0, y1, L.CELL, under, c.lib("canyon_ledge", "dirt"))
    far_land(c)
    return ter


FAR = (-3400.0, 3400.0, -3400.0, 3400.0)


def far_natural(x, y):
    X0, X1, Y0, Y1 = L.GRID
    if X0 <= x <= X1 and Y0 <= y <= Y1:
        return L.BED - 8.0
    # The desert floor far below the rim, cut by the river's canyon running on south,
    # with great walls of mesa round the horizon.
    d = max(X0 - x, x - X1, Y0 - y, y - Y1, 0.0)
    z = L.RIM - 10.0 + 6.0 * L.noise(x, y, 0.004, 3.0)
    river = abs(x - (250.0 + 120.0 * math.sin(y / 600.0)))
    if y < 0 and river < 120:
        z = lerp(L.BED, z, L.sm((river - 30.0) / 90.0))
    if y > 0 and abs(x - 150.0 - 60.0 * math.sin(y / 500.0)) < 100:
        z = lerp(L.BED + 20.0, z, L.sm((abs(x - 150.0 - 60.0 * math.sin(y / 500.0)) - 25.0) / 75.0))
    ring_ = L.sm((d - 900.0) / 900.0)
    return z + ring_ * (90.0 + 60.0 * L.noise(x, y, 0.003, 9.0))


def far_land(c):
    X0, X1, Y0, Y1 = L.GRID

    def cls(cen, n, info):
        if X0 + 30 < cen.x < X1 - 30 and Y0 + 30 < cen.y < Y1 - 30:
            return None
        if cen.z < L.BED + 2:
            return ("river_sand", "sand")
        if n.z < 0.6:
            return ("canyon_cliff", "wall")
        return ("canyon_ledge", "dirt")

    fx0, fx1, fy0, fy1 = FAR
    far = c.terrain("Far Land", fx0, fx1, fy0, fy1, 70.0, far_natural, cls, near=0.0, fade=1.0)
    far["kp_role"] = "visual"
    return far


# ------------------------------------------------------------------ the caverns' mesa


def caverns(c, sc):
    """The mesa the Winding Caverns bore through, from the quarry to the High Bridges."""
    s0, s1 = L.at("q2", 0.85), L.at("t1", 0.55)
    qa, qb = c.at(s0), c.at(s1)
    mx, my = (qa.p.x + qb.p.x) / 2 + 6.0, (qa.p.y + qb.p.y) / 2
    ang = math.atan2(qb.p.y - qa.p.y, qb.p.x - qa.p.x)
    bands = [(1.0, 0.0), (1.0, 0.25), (0.93, 0.32), (0.9, 0.6), (0.82, 0.66), (0.78, 0.9), (0.7, 1.0)]
    top = max(qa.p.z, qb.p.z) + 26.0
    half = math.hypot(qb.p.x - qa.p.x, qb.p.y - qa.p.y) / 2 + 2.0
    rock = c.rock_mass("Cavern Mesa", mx, my, half, 34.0, top, z0=min(qa.p.z, qb.p.z) - 14.0, n=26, seed=11, bands=bands, angle=ang,
                       base=min(qa.p.z, qb.p.z) - 2.0)
    c.tunnel(rock, s0 + 6.0, s1 - 6.0, half=c.width / 2 + 5.5, height=11.0, pad=18.0)
    c.paint_rock(rock, ("canyon_cliff", "wall"), ("canyon_ledge", "dirt"), top_z=top - 6.0)
    sc.mesa = rock
    sc.tunnel = (s0 + 6.0 - 18.0, s1 - 6.0 + 18.0)
    sc.ground_obs.append(rock)


# ------------------------------------------------------------------ water


def waters(c, sc):
    """The river (deep: in it, you're put back on the road), the oasis pool, the far
    river on south."""
    path = []
    for a, b in zip(L.RIVER, L.RIVER[1:]):
        n = max(2, int(math.dist(a, b) / 8.0))
        for k in range(n):
            t = k / n
            path.append((lerp(a[0], b[0], t), lerp(a[1], b[1], t), 2 * L.RIVER_HW + 6.0, L.RIVER_Z))
    path.append((L.RIVER[-1][0], L.RIVER[-1][1], 2 * L.RIVER_HW + 6.0, L.RIVER_Z))
    c.ribbon("River", path, 2 * L.RIVER_HW, L.RIVER_Z, c.lib("canyon_river", "deep_water"), role="both")
    c.disc("Oasis Pool", L.OASIS[0], L.OASIS[1], L.OASIS_R + 1.0, 8.6, c.lib("lagoon", "water"), role="both", n=32, wobble=0.08)
    # The river beyond the canyon (visual), and a floor of water under it all far below.
    far = [(250.0 + 120.0 * math.sin(y / 600.0), y, 60.0, L.BED + 1.0) for y in range(-3300, -340, 120)]
    c.ribbon("Far River", far, 60.0, L.BED + 1.0, c.lib("canyon_river"), role="visual")
    # The Bed: under the river, anything that falls lands here and is put back.
    c.underfloor_flat("River Bed", *L.GRID, L.CELL * 2, lambda x, y: L.BED - 2.0 if L.river_d(x, y) < L.RIVER_HW + 30 else None,
                      c.lib("canyon_river", "deep_water"))


def falls(c, sc):
    """The Great Falls at the gorge's head, and the falls off the canyon walls."""
    import props

    out = []
    lx, ly = L.FALLS
    top = sc.info(lx, ly + 16) - 1.0
    fx, fy = props.falls(c, "Great Falls", lx, ly, top, L.RIVER_Z + 0.3, 16.0, 26.0, facing=-1, throw=9.0, bulge=1.8, veils=3,
                         mats=("falls_dash", "falls_veil", "falls_foam"))
    out.append((fx, fy, top, 22.0, 0.0))
    for name, x, y, ang, w in (("Chasm Falls", 238.0, -98.0, -math.pi / 2, 7.0), ("South Falls West", 213.0, -336.0, math.pi / 2, 10.0),
                               ("South Falls East", 267.0, -324.0, -math.pi / 2, 10.0)):
        top = sc.info(x - 10 * math.cos(ang - math.pi / 2), y) - 0.8
        if top < 14:
            continue
        props.falls(c, name, x, y, top, L.RIVER_Z + 0.3, w * 0.7, w, facing=-1, throw=5.0, bulge=1.0, veils=2, angle=ang,
                    mats=("falls_dash", "falls_veil", "falls_foam"))
        out.append((x, y, top, w, ang))
    for x, y, top, w, ang in out:
        game_entity(c, "waterfall", x, y, L.RIVER_Z, top=round(top, 1), width=w, heading=round(ang, 3))
    return out


# ------------------------------------------------------------------ the light


def light(c, sc):
    """The sun low in the west: lit faces glow orange, the canyon's depths sink into
    shade; the tunnel dim; warm round every brazier and torch."""
    c.merge_props(("Props", "Town", "Rocks Small"), cell=260.0)
    c.merge_props(("Far Rocks",), cell=2400.0)
    land = [sc.land, sc.mesa]
    built = [o for name in ("Bridges", "Arch", "Props", "Town", "Rocks Small") for o in c.coll(name).objects if o.type == "MESH" and o.data.users == 1]
    c.preset("sun", land + built, 0.38, color=(1.0, 0.78, 0.55))
    c.preset("bottoms", land, 0.35)

    t0, t1 = sc.tunnel

    def in_tunnel(w):
        smp, d = c.nearest(w.x, w.y)
        return d < 16 and t0 < smp.s < t1 and w.z < smp.p.z + 11

    c.glow([sc.land, sc.mesa] + built, [], 1.0, (1, 1, 1), base=(0.5, 0.42, 0.38), region=in_tunnel)

    def deep(w):
        return w.z < 10.0

    c.glow([sc.land], [], 1.0, (1, 1, 1), base=(0.78, 0.76, 0.86), region=deep)
    colours = {"fire": (14.0, (1.0, 0.72, 0.42)), "glow": (10.0, (1.0, 0.7, 0.36))}
    for kind, pts in sc.lights.items():
        if kind in colours and pts:
            r, col = colours[kind]
            c.glow(land + built, pts, r, col, base=1.0)
    kit.paint.shade_roads(c.pieces + getattr(c, "lanes", []), 0.4)


# ------------------------------------------------------------------ the Quarry Service Road


def shortcut(c, sc):
    import dry_gulch_v2 as dry_gulch  # lane() lives with the first Dry Gulch lap

    pts, a, b = L.SERVICE, L.SERVICE_A, L.SERVICE_B
    sc.short = (pts, a, b)
    dry_gulch.lane(c, "Quarry Service Road", pts, "quarry_dust", "dirt", width=8.0, shoulder=0.8, shoulder_mat=("quarry_dust", "dirt"),
                   step=3.0, flush=True)


# ------------------------------------------------------------------ gameplay


def gameplay(c, sc):
    pts, a, b = sc.short
    apex = L.at("q1", 0.4)
    gates = c.checkpoints(
        extra=[L.at("c1", 0.6), L.at("h1a", 0.5), L.at("h2a", 0.5), L.at("n2", 0.5), L.at("k2", 0.5), apex, L.at("t1", 0.2),
               L.at("b2", 0.5), L.at("o2", 0.5), L.at("r1", 0.5), L.at("w1a", 0.5), L.at("w2a", 0.5), L.at("x2", 0.5), L.at("x4a", 0.5)],
        avoid=[(a - 2, apex - 8), (apex + 8, b + 2)],
        height=8.0,
    )
    main_gate = min(gates.items(), key=lambda kv: abs(kv[0] - apex))[1]
    k = len(pts) // 2
    c.alt_gate(main_gate, "service_road", [pts[k - 3], pts[k], pts[k + 3]], width=12.0, height=8.0)
    c.path_curve("Quarry Service Road Path", [p for p in pts[::3]] + [pts[-1]], closed=False)
    # Zippers where a clean exit is worth chaining: off the hairpins, onto the bridges,
    # out of the oasis, up the watchtower and out of the Dragon's Coil.
    for at in (L.at("h1b", 0.7), L.at("n2", 0.7), L.at("b1", 0.1), L.at("o3", 0.6), L.at("r2", 0.3), L.at("w2b", 0.6), L.at("x5", 0.0)):
        c.zipper(at, 0.0)
    for at, across in ((L.at("c1", 0.8), 0), (L.at("h2b", 0.6), 3), (L.at("k1", 0.6), 0), (L.at("q2", 0.2), 0), (L.at("b2", 0.9), -3),
                       (L.at("o2", 0.7), 0), (L.at("r1", 0.2), 3), (L.at("w1b", 0.6), 0), (L.at("x3", 0.3), 0)):
        c.bananas(at, across, count=5, gap=2.4)
    for at, across, col in ((L.at("start", 0.6), -4, "red"), (L.at("start", 0.6), 4, "blue"), (L.at("h1a", 0.8), 0, "green"),
                            (L.at("n2", 0.3), -3, "yellow"), (L.at("n2", 0.3), 3, "rainbow"), (L.at("k3", 0.3), 0, "red"),
                            (L.at("t1", 0.3), 0, "blue"), (L.at("o1", 0.5), 0, "green"), (L.at("r1", 0.7), -4, "yellow"),
                            (L.at("r1", 0.7), 4, "rainbow"), (L.at("w2a", 0.4), 0, "red"), (L.at("x2", 0.3), 0, "blue"),
                            (L.at("x4b", 0.5), 0, "green")):
        c.balloon(at, across, col)


# ------------------------------------------------------------------ build


def build(c, dc):
    import dcanyon_town as town

    sc = Scene(c)
    sc.dc = dc
    shortcut(c, sc)  # first: the land meets its road
    land(c, sc)
    caverns(c, sc)
    waters(c, sc)
    sc.falls = falls(c, sc)
    c.start_line()
    town.build(c, sc)
    gameplay(c, sc)
    town.entities(c, sc)
    light(c, sc)
