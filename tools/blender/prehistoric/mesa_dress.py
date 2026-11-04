# Desert World v4's dressing, the deep pass (Blake, Nov 1: "rigorously go through beach and
# desert world and do the stuff that you have been seeing me do with dino and snow ... like
# nothing floating, make it immersive for that level"): every section dressed from its
# own course's kit, the way Frostveil wears the citadel's and Hearthglow the Hollow's:
#
#   the boomtown     Dry Gulch's frontier buildings (gulch_town), its lantern posts down
#                    both sides of Main Street, hitching rails and troughs between them,
#                    its water tower, Boot Hill, the railroad on the ground;
#   the canyon rim   Canyon Dash's outpost: the timber arch and its banners, braziers, the
#                    windmill, the lookout tower, the water tank; a guard rail along the rim;
#   Havasu           Oasis Haven's village: adobe homes with vigas and ristras, the log
#                    ranch gate, lantern posts, ramadas, the campground, a corral;
#   the crater       Impact Depths' approach: the rustic timber arch, the survey camp,
#                    warning signs along the rim;
#   the roads        chevron boards round every big bend, telegraph poles down the long
#                    open stretches, their wires strung pole to pole.
#
# Every building on land graded level under it (region_paint.grade), its foot down to the
# lowest ground; every prop on the lowest ground under it.
# SPDX-License-Identifier: MIT

import functools
import math
import random

import canyon_props as cp
import gulch_props as gp
import gulch_scenery as gs
import gulch_town as gt
import impact_props as ip
import mesa_layout as M
import oasis_desert as od
import oasis_props as op
import region_paint as paint
import summit_props as smp_
from canyon_props import _beam
from course_kit import Vector, bmesh, rnd
from props import _faces, blob, cuboid, tube
from pocket_build import box

TIMBER = ("weathered_timber", "wall")


def road_rot(q):
    return math.atan2(q.t.y, q.t.x)


def _runs(c, test, step=2.0):
    """The stretches (s0, s1) of the lap where test(q) holds."""
    runs, cur = [], None
    s = 0.0
    while s < c.length:
        if test(c.at(s)):
            cur = [s, s] if cur is None else [cur[0], s]
        elif cur:
            runs.append(tuple(cur))
            cur = None
        s += step
    if cur:
        runs.append(tuple(cur))
    return runs


def _lowest(ground, x, y, r):
    """The lowest ground round (x, y) at r (and under it): where a thing's foot goes."""
    return min([ground(x + r * math.cos(t), y + r * math.sin(t)) for t in [k * math.tau / 8 for k in range(8)]] + [ground(x, y)])


def _spread(ground, x, y, r):
    hs = [ground(x + r * math.cos(t), y + r * math.sin(t)) for t in [k * math.tau / 8 for k in range(8)]] + [ground(x, y)]
    return max(hs) - min(hs)


def _off_roads(c, x, y, margin):
    """Clear of the lap and every side road by `margin` past their edges."""
    return gs.clear(c, x, y, margin)


class _DG:
    """What gulch_scenery's Scene asks of a course: its land."""

    natural = staticmethod(M.natural)


def _scene(c, ter):
    sc = gs.Scene(c, _DG)
    sc.ground_obs = [ter]
    return sc


# ------------------------------------------------------------------ the boomtown

WEST = [
    (20.0, 16.0, {"special": functools.partial(gt.hotel, haunted=False, sign_top=True)}),
    (10.0, 12.0, {"siding": "siding_green", "sign": "bank", "lit": 0.6}),
    (9.0, 11.0, {"siding": "siding_grey", "sign": "barber", "lit": 0.5}),
    (22.0, 18.0, {"special": gt.saloon}),
    (12.0, 13.0, {"siding": "siding_brown", "sign": "undertaker", "lit": 0.4}),
    (11.0, 12.0, {"siding": "siding_ochre", "storeys": 2, "balcony": True, "lit": 0.6}),
    (8.0, 10.0, {"siding": "siding_red", "lit": 0.6}),
]
EAST = [
    (18.0, 15.0, {"siding": "siding_ochre", "storeys": 2, "sign": "general", "lit": 0.8}),
    (11.0, 12.0, {"special": gt.sheriff, "extra": 9.0}),
    (12.0, 13.0, {"siding": "siding_brown", "sign": "assay", "lit": 0.6}),
    (16.0, 20.0, {"special": gt.livery}),
    (10.0, 12.0, {"siding": "siding_green", "storeys": 2, "balcony": True, "lit": 0.6}),
    (9.0, 11.0, {"siding": "siding_grey", "lit": 0.5}),
]
SETBACK = 13.5  # Main Street's fronts from the road's middle (porches 3.2 m in front of them)


def _row(c, sc, m, s0, s1, side, kinds, ground, ter, taken, seed=0, line=None, gap=2.0):
    """gulch_town.along's row of frontier buildings, each on land graded level under it
    (its footprint and its porch), its door sill at the ground; along the lap, or along
    `line` (a _Line: a side road's street)."""
    s, k, out = s0, 0, []
    while s < s1:
        w, d, opts = kinds[k % len(kinds)]
        ex = opts.get("extra", 0.0)
        mid = s + (w + ex) / 2
        if mid + (w + ex) / 2 > s1:
            break
        q = (line or c).at(s + w / 2)
        h = road_rot(q)
        rot = h + math.pi if side > 0 else h
        nx, ny = (math.sin(h), -math.cos(h)) if side > 0 else (-math.sin(h), math.cos(h))
        x, y = q.p.x + nx * SETBACK, q.p.y + ny * SETBACK
        f = gt.Frame(x, y, 0.0, rot)
        # (A building's extra: the jail beside the sheriff's, on its +u side: forward along the
        # lap on the left (side -1), so the sheriff's only goes on that side.)
        lo_u, hi_u = -w / 2, w / 2 + ex
        corners = [f.P(lo_u - 0.6, -3.4), f.P(hi_u + 0.6, -3.4), f.P(lo_u, d), f.P(hi_u, d)]
        cx, cy, _ = f.P((lo_u + hi_u) / 2, d / 2)
        R = math.hypot(hi_u - lo_u, d + 3.4) / 2
        why = None
        if not all(_off_roads(c, px, py, 1.4) for px, py, _ in corners):
            why = "road"
        elif not all(sc.free(px, py, 0.5) for px, py, _ in corners):
            why = "built"
        elif not taken.clear(cx, cy, R - 2.0):
            why = "taken"
        else:
            hs = [ground(px, py) for px, py, _ in corners] + [ground(cx, cy)]
            if max(hs) - min(hs) >= 4.0:
                why = "slope %.1f" % (max(hs) - min(hs))
        ok = why is None
        if not ok:
            print("  row %+d at s %.0f (%.0f, %.0f): %s" % (side, s, cx, cy, why))
        if ok:
            zf = (ground(*corners[0][:2]) + ground(*corners[1][:2])) / 2
            paint.grade(c, ter, cx, cy, rot, hi_u - lo_u + 1.0, d + 1.0, zf, front=3.8)
            kw = {kk: v for kk, v in opts.items() if kk not in ("special", "extra")}
            kw.setdefault("ghost", 0.0)
            if "special" in opts:
                opts["special"](m, sc, x, y, zf + 0.05, rot)
            else:
                gt.building(m, sc, x, y, zf + 0.05, rot, w, d, seed=seed * 50 + k, **kw)
            out.append((x, y, rot, w, cx, cy, R))
            print("  built %s %.0fx%.0f at (%.0f, %.0f)" % (opts.get("sign") or getattr(opts.get("special"), "__name__", "plain"), w, d, cx, cy))
        s += w + ex + gap + 2.0 * rnd(seed * 13 + k)
        k += 1
    return out


def boomtown(c, ground, taken, ter):
    """The boomtown on the road under Copper Mesa, as Dry Gulch's own Main Street: the
    frontier buildings down both sides (saloon, hotel, bank, barber, undertaker, general
    store, sheriff and jail, assay office, livery), lantern posts down both kerbs, the
    boardwalks dressed between them (hitching rails, troughs, barrels, crates, benches),
    the water tower behind, Boot Hill out west on its knoll, the railroad along the
    ground into town. Returns where the folk live (x, y)."""
    sc = _scene(c, ter)
    gs.protos(c)
    runs = _runs(c, lambda q: M.look_at(q.p.x, q.p.y) == "town" and q.p.x > 240 and -240 < q.p.y < 10)
    s0, s1 = max(runs, key=lambda r: r[1] - r[0])
    m = gs.Mesh()
    built = _row(c, sc, m, s0 + 4.0, s1 - 4.0, 1, WEST, ground, ter, taken, seed=1)
    built += _row(c, sc, m, s0 + 12.0, s1 - 4.0, -1, EAST, ground, ter, taken, seed=2)
    # (Their ground kept after both rows: each row keeps clear of its own by footprints.)
    for b in built:
        taken.add(b[4], b[5], b[6])
    m.build(c, "Boomtown Buildings", "Village", role="both")
    # Lantern posts down both kerbs, every 16 m, their lanterns out over the street (a light
    # on every other one); between them, the boardwalks' things.
    post = gp.lantern_post(c)
    lx, _ly, lz = gp.LANTERN_POST_LIGHT
    things = ["Hitching Rail", "Water Trough", "Barrel 0", "Bench", "Crate Stack 0", "Barrel 1", "Hitching Rail", "Crate Stack 1"]
    s, k = s0 + 6.0, 0
    while s < s1 - 4.0:
        q = c.at(s)
        h = road_rot(q)
        for side in (-1, 1):
            nx, ny = (math.sin(h), -math.cos(h)) if side > 0 else (-math.sin(h), math.cos(h))
            x, y = q.p.x + nx * (q.w / 2 + 2.3), q.p.y + ny * (q.w / 2 + 2.3)
            rot = math.atan2(-ny, -nx)
            if _off_roads(c, x, y, 0.4) and taken.clear(x, y, 0.3):
                z = _lowest(ground, x, y, 0.3) - 0.1
                c.place(post, x, y, z, rot=rot, coll="Village", role="both")
                if k % 2 == 0:
                    g = c.game(x + lx * math.cos(rot), y + lx * math.sin(rot), z + lz)
                    c.entity("lantern", x=g[0], y=g[1], z=g[2])
            q2 = c.at(s + 8.0)
            h2 = road_rot(q2)
            nx, ny = (math.sin(h2), -math.cos(h2)) if side > 0 else (-math.sin(h2), math.cos(h2))
            x, y = q2.p.x + nx * (q2.w / 2 + 2.6), q2.p.y + ny * (q2.w / 2 + 2.6)
            name = things[(k * 2 + (side > 0)) % len(things)]
            if _off_roads(c, x, y, 1.0) and taken.clear(x, y, 0.5):
                along = name in ("Hitching Rail", "Water Trough", "Bench")
                c.place(name, x, y, _lowest(ground, x, y, 0.9 if along else 0.5), rot=h2 if along else rnd(k) * 6.0, coll="Village",
                        role="both")
        s += 16.0
        k += 1
    # The water tower, behind the west row.
    q = c.at((s0 + s1) / 2 + 30.0)
    h = road_rot(q)
    for off in (30.0, 36.0, 42.0):
        x, y = q.p.x + math.sin(h) * off, q.p.y - math.cos(h) * off
        if taken.clear(x, y, 7.0) and _spread(ground, x, y, 6.0) < 2.0:
            gt.water_tower(c, sc, x, y, _lowest(ground, x, y, 6.0))
            taken.add(x, y, 8.0)
            break
    boot_hill(c, sc, ground, ter, taken)
    railroad(c, ground, taken)
    for x, y, z in sc.lanterns[::2]:
        g = c.game(x, y, z)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
    print("boomtown: %d buildings, the street %.0f m" % (len(built), s1 - s0))
    q = c.at((s0 + s1) / 2)
    return q.p.x, q.p.y


# ------------------------------------------------------------------ the frontier town


class _Q:
    def __init__(self, p, t, w):
        self.p, self.t, self.w = p, t, w
        self.r = Vector((t.y, -t.x, 0.0))

    def side(self, o, up=0.0):
        return self.p + self.r * o + Vector((0, 0, up))


class _Line:
    """A side road's street as the lap's samples are: at(s) along it, its point, its way
    (t), its width."""

    def __init__(self, pts, width):
        self.pts = [Vector(p) for p in pts]
        self.w = width
        self.cum = [0.0]
        for a, b in zip(self.pts, self.pts[1:]):
            self.cum.append(self.cum[-1] + (Vector((b.x, b.y, 0)) - Vector((a.x, a.y, 0))).length)
        self.length = self.cum[-1]

    def at(self, s):
        s = max(0.0, min(self.length, s))
        for i in range(len(self.pts) - 1):
            if self.cum[i + 1] >= s:
                break
        a, b = self.pts[i], self.pts[i + 1]
        f = (s - self.cum[i]) / max(1e-6, self.cum[i + 1] - self.cum[i])
        t = Vector((b.x - a.x, b.y - a.y, 0.0)).normalized()
        return _Q(a.lerp(b, f), t, self.w)


# The frontier town's blocks (Blake, review-desert_region note 2: "lets go for old west town,
# with a salloon, a bank, barber, all the classic old west buildings. this needs to be a
# hopping old western town when we enter this world"): Main Street runs north through the
# bay under the rim, the road from the Frozen Pass crossing it in the middle of town. Each
# block: (from, to along Main Street, its east row, its west row).
TOWN_BLOCKS = [
    (4.0, 62.0, [(9.0, 11.0, {"siding": "siding_grey", "sign": "barber", "lit": 0.6}),
                 (8.0, 10.0, {"siding": "siding_red", "storeys": 2, "balcony": True, "lit": 0.6}),
                 (9.0, 11.0, {"siding": "siding_brown", "sign": "undertaker", "lit": 0.4}),
                 (11.0, 12.0, {"siding": "siding_green", "storeys": 2, "balcony": True, "sign": "livery", "lit": 0.6})],
     [(12.0, 12.0, {"special": lambda m, sc, x, y, z, rot: grand_jail(m, sc, x, y, z, rot), "extra": 15.0}),
      (18.0, 15.0, {"siding": "siding_ochre", "storeys": 2, "sign": "general", "lit": 0.8})]),
    (68.0, 128.0, [(10.0, 12.0, {"siding": "siding_green", "sign": "bank", "lit": 0.6}),
                   (12.0, 13.0, {"siding": "siding_brown", "sign": "assay", "lit": 0.5}),
                   (8.0, 10.0, {"siding": "siding_ochre", "lit": 0.6})],
     [(22.0, 18.0, {"special": gt.saloon}),
      (20.0, 16.0, {"special": functools.partial(gt.hotel, haunted=False, sign_top=True)})]),
]


def frontier_town(c, ground, taken, ter, street):
    """The frontier town where you come into the desert, down both sides of its Main Street
    (`street`: its points, south to north): the general store, the hotel, the sheriff's and
    the jail, the barber's, the saloon, the undertaker's, the bank, the assay office; the
    timber arch over the street at each end, lantern posts down both kerbs, hitching rails,
    troughs, barrels and crates on the boardwalks, wagons drawn up, the windmill and its tank
    and the water tower behind, and the town's folk up and down the street. Returns the
    buildings put up."""
    sc = _scene(c, ter)
    gs.protos(c)
    line = _Line(street, 12.0)
    s0, s1 = 0.0, line.length
    m = gs.Mesh()
    built = []
    for k, (b0, b1, east, west) in enumerate(TOWN_BLOCKS):
        built += _row(c, sc, m, b0, b1, 1, east, ground, ter, taken, seed=7 + k, line=line, gap=3.5)
        built += _row(c, sc, m, b0, b1, -1, west, ground, ter, taken, seed=9 + k, line=line, gap=3.5)
    for b in built:
        taken.add(b[4], b[5], b[6])
    square = town_square(c, sc, m, ground, ter, taken)
    m.build(c, "Frontier Town Buildings", "Village", role="both")
    rocking_chairs(c, ground, built[:6:2] + square[1:6:2])
    town_props(c, ground, taken, line, built + square)
    # (No arches over the street's ends: review-desert_region 2, notes 10 and 12.)
    # Lantern posts down both kerbs, the boardwalks' things between them.
    post = gp.lantern_post(c)
    lx, _ly, lz = gp.LANTERN_POST_LIGHT
    things = ["Hitching Rail", "Water Trough", "Barrel 0", "Bench", "Crate Stack 0", "Barrel 1", "Hitching Rail", "Crate Stack 1"]
    s, k = s0 + 2.0, 0
    while s < s1:
        q = line.at(s)
        h = road_rot(q)
        for side in (-1, 1):
            nx, ny = (math.sin(h), -math.cos(h)) if side > 0 else (-math.sin(h), math.cos(h))
            x, y = q.p.x + nx * (q.w / 2 + 2.3), q.p.y + ny * (q.w / 2 + 2.3)
            rot = math.atan2(-ny, -nx)
            if _off_roads(c, x, y, 0.4) and taken.clear(x, y, 0.3):
                z = _lowest(ground, x, y, 0.3) - 0.1
                c.place(post, x, y, z, rot=rot, coll="Village", role="both")
                if k % 2 == 0:
                    g = c.game(x + lx * math.cos(rot), y + lx * math.sin(rot), z + lz)
                    c.entity("lantern", x=g[0], y=g[1], z=g[2])
            q2 = line.at(s + 7.0)
            x, y = q2.p.x + nx * (q2.w / 2 + 2.6), q2.p.y + ny * (q2.w / 2 + 2.6)
            name = things[(k * 2 + (side > 0)) % len(things)]
            if _off_roads(c, x, y, 1.0) and taken.clear(x, y, 0.5):
                along = name in ("Hitching Rail", "Water Trough", "Bench")
                c.place(name, x, y, _lowest(ground, x, y, 0.9 if along else 0.5), rot=h if along else rnd(k) * 6.0,
                        coll="Village", role="both")
                taken.add(x, y, 0.8)
        s += 14.0
        k += 1
    # Wagons drawn up by the boardwalks, a tumbleweed or two in the street's edges.
    wag = [gp.wagon(c, True), gp.wagon(c, False)]
    for k, (f, side) in enumerate(((0.3, 1), (0.62, -1), (0.85, 1))):
        q = line.at(s0 + (s1 - s0) * f)
        h = road_rot(q)
        nx, ny = (math.sin(h), -math.cos(h)) if side > 0 else (-math.sin(h), math.cos(h))
        x, y = q.p.x + nx * (q.w / 2 + 5.5), q.p.y + ny * (q.w / 2 + 5.5)
        if _off_roads(c, x, y, 1.6) and taken.clear(x, y, 2.6):
            c.place(wag[k % 2], x, y, _lowest(ground, x, y, 2.0), rot=h, coll="Village", role="both")
            taken.add(x, y, 3.0)
    # Behind the rows: the water tower north, the windmill and its tank and the livery's
    # corral south.
    mid = line.at((s0 + s1) / 2)
    h = road_rot(mid)
    for off in (30.0, 36.0, 42.0):
        x, y = mid.p.x + math.sin(h) * -off, mid.p.y - math.cos(h) * -off
        if taken.clear(x, y, 7.0) and _off_roads(c, x, y, 6.0) and _spread(ground, x, y, 6.0) < 2.5:
            gt.water_tower(c, sc, x, y, _lowest(ground, x, y, 6.0))
            taken.add(x, y, 8.0)
            break
    q = line.at(s0 + (s1 - s0) * 0.2)
    h = road_rot(q)
    for off in (30.0, 34.0, 38.0):
        x, y = q.p.x - math.sin(h) * off, q.p.y + math.cos(h) * off
        if taken.clear(x, y, 8.0) and _off_roads(c, x, y, 8.0) and _spread(ground, x, y, 6.0) < 2.5:
            c.place(cp.windmill_tower(c), x, y, _lowest(ground, x, y, 2.5) - 0.2)
            c.place(cp.water_tank(c), x + 7.0, y, ground(x + 7.0, y) - 0.2)
            taken.add(x, y, 9.0)
            break
    for x, y, z in sc.lanterns[::2]:
        g = c.game(x, y, z)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
    # The folk, up and down the street: busy.
    for f in (0.2, 0.45, 0.7, 0.92):
        q = line.at(s0 + (s1 - s0) * f)
        g = c.game(q.p.x, q.p.y, q.p.z)
        c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=11.0, n=4, folk="desert", heading=0.0)
    print("frontier town: %d buildings, Main Street %.0f m" % (len(built), s1 - s0))
    return len(built)


def grand_jail(m, sc, x, y, z, rot):
    """The sheriff's office and, beside it, the jailhouse made grand (review-desert_region 2,
    note 9: "lets make this building bigger and more grand"): two storeys of dressed stone,
    a corniced parapet, pilasters, tall barred windows on both floors, a stone stair to its
    door under a pediment, the JAIL sign, a flag on its roof."""
    f, top = gt.building(m, sc, x, y, z, rot, 12.0, 12.0, storeys=2, siding="siding_grey", sign="sheriff", balcony=True, lit=0.7,
                         ghost=0.0, seed=3)
    W, D, H = 13.0, 13.0, 8.6
    j = gt.Frame(*f.P(12.0 / 2 + 1.0 + W / 2, 1.0), rot)
    m.add(("masonry", "wall"), lambda bm: cuboid(bm, j.P(0, D / 2, H / 2 - 0.8), (W, D, H + 1.6), rot))
    m.add(("sandstone_block", "wall"), lambda bm: cuboid(bm, j.P(0, -0.1, H + 0.5), (W + 0.8, 0.8, 0.6), rot))  # (the cornice)
    m.add(("masonry", "wall"), lambda bm: cuboid(bm, j.P(0, 0.2, H + 1.4), (W, 0.5, 1.4), rot))  # (the parapet)
    m.add(("tin_roof", "wall"), lambda bm: cuboid(bm, j.P(0, D / 2, H + 0.1), (W - 0.4, D - 0.4, 0.3), rot))
    for u in (-W / 2 + 0.3, -W / 6, W / 6, W / 2 - 0.3):
        m.add(("sandstone_block", "wall"), lambda bm, u=u: cuboid(bm, j.P(u, -0.25, H / 2), (0.7, 0.5, H), rot))  # (pilasters)
    fn = j.N(0, -1)
    for fl, zz in ((0, 1.4), (1, 5.3)):
        for u in (-4.4, -1.6, 1.6, 4.4):
            if fl == 0 and abs(u) < 2.0:
                continue
            cx, cy, _ = j.P(u, 0)
            gt.face_quad(m, ("window_dark", "wall"), cx, cy, fn[0], fn[1], 0.7, z + zz, z + zz + 2.2, out=0.05)
            for k in range(5):
                bx, by, _ = j.P(u - 0.56 + k * 0.28, -0.15)
                m.add(("iron", "wall"), lambda bm, bx=bx, by=by, zz=zz: cuboid(bm, (bx, by, z + zz + 1.1), (0.07, 0.07, 2.2)))
    cx, cy, _ = j.P(0, 0)
    gt.face_quad(m, ("door_wood", "wall"), cx, cy, fn[0], fn[1], 1.1, z + 0.6, z + 3.4, out=0.06)
    for k in range(3):
        m.add(("sandstone_block", "wall"), lambda bm, k=k: cuboid(bm, j.P(0, -0.9 - k * 0.6, 0.1 + 0.2 * (2 - k)), (3.6 + 0.8 * k, 0.6, 0.2 * (3 - k)), rot))
    m.add(("sandstone_block", "wall"), lambda bm: cuboid(bm, j.P(0, -0.5, 4.0), (3.4, 1.0, 0.35), rot, tilt=(0.0, 0.0)))
    for sx in (-1, 1):
        m.add(("sandstone_block", "wall"), lambda bm, sx=sx: cuboid(bm, j.P(sx * 1.5, -0.7, 2.0), (0.4, 0.4, 3.8), rot))
    gt.face_quad(m, ("sign_jail", "wall"), cx, cy, fn[0], fn[1], 2.0, z + H - 1.8, z + H - 0.2, out=0.06)
    px, py, _ = j.P(W / 2 - 1.0, D - 1.0)
    m.add(TIMBER, lambda bm: cuboid(bm, (px, py, z + H + 3.5), (0.15, 0.15, 7.0)))
    m.add(("banner_red", "wall"), lambda bm: cuboid(bm, (px + 0.9 * math.cos(rot), py + 0.9 * math.sin(rot), z + H + 6.2), (1.8, 0.05, 1.1), rot))
    sc.footprints.append((j.P(0, D / 2)[0], j.P(0, D / 2)[1], 9.5))
    return f


def town_square(c, sc, m, ground, ter, taken):
    """The town square at Main Street's north end (review-desert_region 2, note 14: "a cul
    de sac of buildings ... a lively town square"): the ring road round a plaza (the well,
    the bandstand, the flagpole, benches and its lamps; mesa_region lays the ring), and the
    buildings all round it facing in, each on land graded level under it, signs on every
    one. Returns them as _row's."""
    sx, sy, R, _pad = M.TOWN_SQUARE
    kinds = [(12.0, 12.0, {"siding": "siding_green", "sign": "bank", "lit": 0.7}),
             (10.0, 11.0, {"siding": "siding_brown", "sign": "barber", "lit": 0.6}),
             (13.0, 12.0, {"siding": "siding_red", "storeys": 2, "balcony": True, "sign": "saloon", "lit": 0.85}),
             (11.0, 11.0, {"siding": "siding_ochre", "sign": "assay", "lit": 0.6}),
             (14.0, 12.0, {"siding": "siding_grey", "storeys": 2, "sign": "hotel", "lit": 0.6}),
             (10.0, 11.0, {"siding": "siding_brown", "sign": "undertaker", "lit": 0.4}),
             (12.0, 12.0, {"siding": "siding_green", "storeys": 2, "balcony": True, "sign": "general", "lit": 0.75}),
             (11.0, 11.0, {"siding": "siding_red", "sign": "livery", "lit": 0.5})]
    Rf = R + 5.0 + 1.2 + 3.6
    out = []
    a = math.radians(-58.0)
    k = 0
    while a < math.radians(238.0) and k < len(kinds):
        w, d, opts = kinds[k]
        da = (w + 1.6) / Rf
        am = a + da / 2
        x, y = sx + Rf * math.cos(am), sy + Rf * math.sin(am)
        rot = am - math.pi / 2  # (its front, -v, toward the plaza)
        f = gt.Frame(x, y, 0.0, rot)
        cx, cy, _ = f.P(0, d / 2)
        corners = [f.P(-w / 2, -3.4), f.P(w / 2, -3.4), f.P(-w / 2, d), f.P(w / 2, d)]
        hs = [ground(px, py) for px, py, _ in corners] + [ground(cx, cy)]
        if max(hs) - min(hs) < 5.0 and all(_off_roads(c, px, py, 1.0) for px, py, _ in corners):
            zf = (ground(*corners[0][:2]) + ground(*corners[1][:2])) / 2
            paint.grade(c, ter, cx, cy, rot, w + 1.0, d + 1.0, zf, front=3.8)
            gt.building(m, sc, x, y, zf + 0.05, rot, w, d, seed=200 + k, ghost=0.0, **opts)
            R_ = math.hypot(w, d + 3.4) / 2
            out.append((x, y, rot, w, cx, cy, R_))
            taken.add(cx, cy, R_)
            print("  square: %s at (%.0f, %.0f)" % (opts.get("sign"), cx, cy))
        a += da
        k += 1
    # The plaza: the well in its middle, the bandstand, the flagpole, benches round it.
    z = ground(sx, sy)
    m.add(("masonry", "wall"), lambda bm: tube(bm, [(sx, sy, z - 0.4), (sx, sy, z + 0.9)], 1.4, n=12))
    m.add(TIMBER, lambda bm: cuboid(bm, (sx - 1.2, sy, z + 1.9), (0.15, 0.15, 2.0)))
    m.add(TIMBER, lambda bm: cuboid(bm, (sx + 1.2, sy, z + 1.9), (0.15, 0.15, 2.0)))
    m.add(("shingle_roof", "wall"), lambda bm: cuboid(bm, (sx, sy, z + 3.0), (3.2, 2.0, 0.15), 0.0, tilt=(0.0, 0.0)))
    bx, by = sx + 4.2, sy - 1.0
    m.add(("board_walk", "wall"), lambda bm: tube(bm, [(bx, by, z - 0.2), (bx, by, z + 0.6)], 2.4, n=8))
    for k2 in range(8):
        a2 = k2 * math.tau / 8
        m.add(TIMBER, lambda bm, a2=a2: cuboid(bm, (bx + 2.2 * math.cos(a2), by + 2.2 * math.sin(a2), z + 2.0), (0.15, 0.15, 2.8)))
    m.add(("awning_red", "wall"), lambda bm: blob(bm, (bx, by, z + 3.6), 2.7, sz=0.35, subdiv=1))
    fx, fy = sx - 4.0, sy + 2.0
    m.add(TIMBER, lambda bm: cuboid(bm, (fx, fy, z + 4.5), (0.16, 0.16, 9.0)))
    m.add(("banner_red", "wall"), lambda bm: cuboid(bm, (fx + 1.0, fy, z + 8.2), (2.0, 0.05, 1.2)))
    for k2 in range(4):
        a2 = k2 * math.tau / 4 + 0.4
        c.place("Bench", sx + 5.6 * math.cos(a2), sy + 5.6 * math.sin(a2), z, rot=a2 + math.pi / 2, coll="Village", role="both")
    for k2 in range(6):
        a2 = k2 * math.tau / 6
        lx, ly = sx + (R + 6.4) * math.cos(a2 + 0.3), sy + (R + 6.4) * math.sin(a2 + 0.3)
        if _off_roads(c, lx, ly, 0.4) and taken.clear(lx, ly, 0.3):
            c.place(gp.lantern_post(c), lx, ly, _lowest(ground, lx, ly, 0.3) - 0.1, rot=a2, coll="Village", role="both")
            g = c.game(lx, ly, ground(lx, ly) + 3.2)
            c.entity("lantern", x=g[0], y=g[1], z=g[2])
    taken.add(sx, sy, R - 5.0)
    # The square busy: its folk.
    for k2 in range(3):
        a2 = k2 * math.tau / 3 + 0.9
        g = c.game(sx + (R + 7.0) * math.cos(a2), sy + (R + 7.0) * math.sin(a2), z)
        c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=9.0, n=5, folk="desert", heading=0.0)
    return out


def square_ring_points():
    """The ring road round the square's plaza (closed: from Main Street's end, round)."""
    sx, sy, R, _pad = M.TOWN_SQUARE
    pts = []
    for k in range(25):
        a = -math.pi / 2 + k * math.tau / 24
        x, y = sx + R * math.cos(a), sy + R * math.sin(a)
        pts.append((x, y, M.natural(x, y) + 0.2))
    return pts


def rocking_chairs(c, ground, homes):
    """Dinos rocking on their porches (review-desert_region 2, note 5: "lets have a couple
    of dinos on rocking chairs rocking back and forth"): a partygoer rocking, chair and all
    (render/partyDino.ts), at one end of each porch, facing the street."""
    for k, (x, y, rot, w, cx, cy, R) in enumerate(homes):
        f = gt.Frame(x, y, 0.0, rot)
        u = (w / 2 - 1.4) * (1 if k % 2 else -1)
        px, py, _ = f.P(u, -1.5)
        nx, ny = f.N(0, -1)
        z = ground(px, py) + 0.5  # (the porch's boards)
        g = c.game(px, py, z)
        c.entity("partygoer", x=round(g[0], 2), y=round(g[1], 2), z=round(g[2], 2), heading=round(math.atan2(nx, -ny), 3),
                 dance="rock", variant=k)


def town_props(c, ground, taken, line, homes):
    """The frontier town dressed more (review-desert_region 2, note 8: "lets get more props
    ... Barrels crates, wagon carts, old west themed things"): in the gaps between the
    buildings and along their sides, stacked crates and barrels, wagon wheels leant on the
    walls, a broken wagon, troughs, an ore cart, cattle skulls on posts, benches; the
    street's edges a tumbleweed or two."""
    rng = random.Random(23)
    protos = ["Barrel 0", "Barrel 1", "Crate Stack 0", "Crate Stack 1", "Water Trough", "Bench"]
    extra = [gp.wagon_wheel(c), gp.ore_cart(c), gp.wagon(c, False, True), gp.cattle_skull(c), gp.crate_stack(c, 2), gp.barrel(c, 2)]
    n = 0
    for k, (x, y, rot, w, cx, cy, R) in enumerate(homes):
        f = gt.Frame(x, y, 0.0, rot)
        for side in (-1, 1):
            for v in (1.5, 4.5, 7.5):
                px, py, _ = f.P(side * (w / 2 + 1.3), v)
                if not taken.clear(px, py, 0.6) and False:
                    continue
                if not _off_roads(c, px, py, 0.8):
                    continue
                r = rng.random()
                if r < 0.55:
                    name = protos[rng.randrange(len(protos) - 2)]
                elif r < 0.8:
                    name = extra[rng.randrange(len(extra))]
                else:
                    continue
                c.place(name, px, py, _lowest(ground, px, py, 0.6), rot=rot + rng.uniform(-0.4, 0.4), coll="Village", role="both")
                n += 1
    for k in range(10):
        s = line.length * (k + 0.5) / 10
        q = line.at(s)
        for side in (-1, 1):
            h = road_rot(q)
            nx, ny = (math.sin(h), -math.cos(h)) if side > 0 else (-math.sin(h), math.cos(h))
            px, py = q.p.x + nx * (q.w / 2 + 1.6), q.p.y + ny * (q.w / 2 + 1.6)
            if k % 3 == side % 3 and _off_roads(c, px, py, 0.6) and taken.clear(px, py, 0.6):
                c.place(gp.tumbleweed(c, k % 2), px, py, ground(px, py), rot=k, coll="Village", role="visual")
    print("frontier town props: %d" % n)


BOOT_HILL = (194.0, -66.0, 19.0)  # Boot Hill: its middle and radius, out west of town over the railroad


def boot_hill(c, sc, ground, ter, taken):
    """Boot Hill, as Dry Gulch's own (review-desert_region 3, note 9: "the same fidelity as
    is the graveyard in dry gulch"): an iron fence all round it on stone posts, its gate
    toward town under a cattle skull, rows and rows of headstones and wooden crosses
    (tilted, half sunk, each on its mound), three crypts, twisted dead trees, an open grave
    with its shovel and the coffin waiting, lanterns at the gate; on ground graded level.
    (Its lights warm: only Dry Gulch's are green.)"""
    gx, gy, R = BOOT_HILL
    z = sum(ground(gx + R * math.cos(t), gy + R * math.sin(t)) for t in [k * math.tau / 8 for k in range(8)]) / 8
    paint.grade(c, ter, gx, gy, 0.0, 2 * R + 3.0, 2 * R + 3.0, z, front=0.0)
    gate_a = math.atan2(-100.0 - gy, 282.0 - gx)  # (toward Main Street)
    n = 30
    for k in range(n):
        am = (k + 0.5) * math.tau / n
        if abs(((am - gate_a + math.pi) % math.tau) - math.pi) < 0.1:
            continue
        x, y = gx + math.cos(am) * R, gy + math.sin(am) * R
        L = 2 * R * math.sin(math.pi / n)
        c.place("Iron Fence 10", x, y, _lowest(ground, x, y, L / 2), rot=am + math.pi / 2, scale=(L / 10.0 * 1.03, 1.0, 1.0),
                coll="Village", role="both")
        if k % 3 == 0:
            a1 = k * math.tau / n
            px, py = gx + math.cos(a1) * R, gy + math.sin(a1) * R
            box(c, "Boot Hill Post %d" % k, px, py, 0.35, 0.35, z - 0.4, z + 1.9, ("masonry", "wall"))
            box(c, "Boot Hill Post Cap %d" % k, px, py, 0.45, 0.45, z + 1.9, z + 2.1, ("masonry", "wall"), role="visual")
    x, y = gx + math.cos(gate_a) * R, gy + math.sin(gate_a) * R
    c.place("Cemetery Gate", x, y, _lowest(ground, x, y, 2.0), rot=gate_a + math.pi / 2, coll="Village", role="both")
    c.place(gp.cattle_skull(c), x, y, z + 4.6, rot=gate_a, scale=1.4, coll="Village", role="visual")
    for sd in (-1, 1):
        a = gate_a + sd * 0.16
        lx, ly = gx + math.cos(a) * (R + 1.2), gy + math.sin(a) * (R + 1.2)
        c.place(gp.lantern_post(c), lx, ly, _lowest(ground, lx, ly, 0.3), rot=gate_a, coll="Village", role="both")
        g = c.game(lx, ly, z + 3.2)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
    rng = random.Random(4)
    ca, sa = math.cos(gate_a + math.pi / 2), math.sin(gate_a + math.pi / 2)
    crypts = [(gx - math.cos(gate_a) * R * 0.62 + ca * dx, gy - math.sin(gate_a) * R * 0.62 + sa * dx) for dx in (-7.0, 0.0, 7.0)]
    k = 0
    for row in range(-4, 5):
        for j in range(-5, 6):
            k += 1
            u, v = j * 3.0 + rng.uniform(-0.5, 0.5), row * 3.8 + rng.uniform(-0.4, 0.4)
            px, py = gx + u * ca - v * sa, gy + u * sa + v * ca
            if math.hypot(px - gx, py - gy) > R - 2.5 or abs(u) < 2.2 or rng.random() < 0.15:
                continue
            if any(math.hypot(px - qx, py - qy) < 5.0 for qx, qy in crypts):
                continue
            zz = _lowest(ground, px, py, 0.5)
            rot = gate_a + math.pi / 2 + rng.uniform(-0.2, 0.2)
            name = ("Grave Cross %d" % rng.randrange(3)) if rng.random() < 0.35 else ("Headstone %d" % rng.randrange(6))
            c.place(name, px, py, zz - 0.15 * rng.random(), rot=rot, scale=1.35 + 0.3 * rng.random(), coll="Village", role="both")
            # (its mound, in front of it, toward the gate)
            mx, my = px + math.cos(gate_a) * 1.2, py + math.sin(gate_a) * 1.2
            bm = bmesh.new()
            blob(bm, (mx, my, zz - 0.25), 0.75, sx=1.2, sy=1.2, sz=0.4, subdiv=1)
            c.assign(c.mesh_object("Grave Mound %d" % k, bm, "Village", "visual"), c.lib("graveyard_earth", "dirt"))
    for i, (cx, cy) in enumerate(crypts):
        c.place("Crypt %d" % (i % 2), cx, cy, _lowest(ground, cx, cy, 2.5), rot=gate_a + math.pi / 2, scale=1.2, coll="Village",
                role="both")
    for k, a in enumerate((gate_a + 2.0, gate_a - 2.2, gate_a + 3.1, gate_a - 1.0)):
        tx, ty = gx + math.cos(a) * (R - 3.5), gy + math.sin(a) * (R - 3.5)
        c.place("Dead Tree %d" % (k % 4), tx, ty, _lowest(ground, tx, ty, 0.6) - 0.2, rot=a, scale=1.25, coll="Village", role="both")
    # The open grave by the gate, its shovel stuck in the heap, the coffin beside it.
    ox, oy = gx + math.cos(gate_a + 0.5) * R * 0.55, gy + math.sin(gate_a + 0.5) * R * 0.55
    box(c, "Open Grave", ox, oy, 1.0, 1.9, z - 1.2, z + 0.02, ("dark_corridor", "wall"), rot=gate_a + math.pi / 2, role="visual")
    bm = bmesh.new()
    blob(bm, (ox + ca * 2.0, oy + sa * 2.0, z - 0.2), 1.1, sx=1.0, sy=1.6, sz=0.6, subdiv=1)
    c.assign(c.mesh_object("Grave Heap", bm, "Village", "visual"), c.lib("graveyard_earth", "dirt"))
    c.place(gp.pick_and_shovel(c), ox + ca * 2.0, oy + sa * 2.0, z + 0.2, rot=gate_a, coll="Village", role="visual")
    c.place(gp.coffin(c), ox - ca * 2.2, oy - sa * 2.2, z, rot=gate_a + math.pi / 2, coll="Village", role="both")
    taken.add(gx, gy, R + 2.0)


RAIL = [(228.0, -205.0), (222.0, -130.0), (220.0, -60.0), (224.0, 0.0), (232.0, 46.0)]


def railroad(c, ground, taken):
    """The railroad in along the ground (ties on the ground every 2.4 m, the rails on
    them, following its every rise and dip): one mesh, ore carts standing on it."""
    m = gs.Mesh()
    pts = []
    for (ax, ay), (bx, by) in zip(RAIL, RAIL[1:]):
        n = int(math.hypot(bx - ax, by - ay) / 2.4)
        for j in range(n):
            t = j / n
            pts.append((ax + (bx - ax) * t, ay + (by - ay) * t))
    pts.append(RAIL[-1])
    ties = []
    for i, (x, y) in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        rot = math.atan2(b[1] - a[1], b[0] - a[0])
        ok = _off_roads(c, x, y, 2.0)
        z = _lowest(ground, x, y, 1.2) if ok else None
        ties.append((x, y, z, rot))
        if ok:
            m.add(TIMBER, lambda bm, x=x, y=y, z=z, rot=rot: cuboid(bm, (x, y, z + 0.06), (0.3, 2.6, 0.22), rot))
            taken.add(x, y, 1.6)
    for sd in (-1, 1):
        for (x0, y0, z0, r0), (x1, y1, z1, r1) in zip(ties, ties[1:]):
            if z0 is None or z1 is None:
                continue
            o0 = (-math.sin(r0) * sd * 0.75, math.cos(r0) * sd * 0.75)
            o1 = (-math.sin(r1) * sd * 0.75, math.cos(r1) * sd * 0.75)
            m.add(("rail_iron", "wall"), lambda bm, a=(x0 + o0[0], y0 + o0[1], z0 + 0.26), b=(x1 + o1[0], y1 + o1[1], z1 + 0.26):
                  _beam(bm, a, b, 0.12))
    m.build(c, "Railroad", "Village", role="visual")
    for k, i in enumerate((len(ties) * 3 // 5, len(ties) * 3 // 5 + 2)):
        x, y, z, rot = ties[i]
        if z is not None:
            c.place(gp.ore_cart(c, glow=False), x, y, z + 0.3, rot=rot, coll="Village", role="both")


# ------------------------------------------------------------------ the canyon rim


def timber_arch(c, ground, q, name, h=10.0, banners=True, post=1.0):
    """Canyon Dash's timber gateway over the road (canyon_scenery.portal), its posts down to
    the lowest ground under each (none of them hanging over the road's fill): two posts
    each side, a double crossbeam, braced corners, its banners and amber board."""
    rot = road_rot(q)
    half = q.w / 2 + 1.6
    m = gs.Mesh()
    for side in (-1, 1):
        for along in (-0.8, 0.8):
            p = q.side(side * half) + q.t * along
            z0 = _lowest(ground, p.x, p.y, post * 0.7) - 0.4
            top = q.p.z + h + 0.5
            m.add(TIMBER, lambda bm, p=p, z0=z0, top=top: cuboid(bm, (p.x, p.y, (z0 + top) / 2), (post, post, top - z0), rot))
        a = q.side(side * half)
        b = q.side(side * (half - 2.6))
        m.add(TIMBER, lambda bm, a=a, b=b: _beam(bm, (a.x, a.y, q.p.z + h - 3.0), (b.x, b.y, q.p.z + h - 0.4), 0.35))
    for dz in (h - 0.4, h + 0.6):
        a, b = q.side(-half - 1.2), q.side(half + 1.2)
        m.add(TIMBER, lambda bm, a=a, b=b, dz=dz: _beam(bm, (a.x, a.y, q.p.z + dz), (b.x, b.y, q.p.z + dz), 0.55))
    if banners:
        for o in (-half * 0.55, half * 0.55):
            p = q.side(o)
            m.add(("canvas_sun", "wall"), lambda bm, p=p: cuboid(bm, (p.x, p.y, q.p.z + h - 2.0), (0.08, 2.6, 3.0), rot + math.pi / 2))
        p = q.side(0)
        m.add(("chevron_amber", "wall"), lambda bm, p=p: cuboid(bm, (p.x, p.y, q.p.z + h + 1.6), (0.12, 7.0, 1.4), rot + math.pi / 2))
    m.build(c, name, "Village", role="both")


def canyon_outpost(c, ground, taken, ter):
    """Canyon Dash's racing outpost where its gateway stands on the rim: the timber arch
    over the road with its banners and amber board, banner poles down both sides, braziers
    by the arch, the windmill, the lookout tower and the water tank back from the rim,
    crates; and a timber guard rail along the rim wherever the road runs by the drop."""
    # (At the top of the shelf road down into the canyon: v4b.)
    smp, _ = c.nearest(*M.ROUTE[7][:2])
    sg = smp.s
    q = c.at(sg - 6.0)
    timber_arch(c, ground, q, "Outpost Arch", h=10.0)
    for sd in (-1, 1):
        p = q.side(sd * (q.w / 2 + 3.4)) - q.t * 2.5
        c.place(cp.brazier(c), p.x, p.y, _lowest(ground, p.x, p.y, 0.6) - 0.1, coll="Village", role="both")
        g = c.game(p.x, p.y, ground(p.x, p.y) + 2.4)
        c.entity("torch", x=g[0], y=g[1], z=g[2])
    # Banner poles down both sides, every 20 m round the gateway.
    for k, ds in enumerate(range(-120, 1, 20)):
        q = c.at(sg + ds)
        for sd in (-1, 1):
            p = q.side(sd * (q.w / 2 + 3.0))
            if _off_roads(c, p.x, p.y, 1.0) and taken.clear(p.x, p.y, 0.5) and M.canyon_d(p.x, p.y) > M.CANYON_HW + 1.0:
                c.place(cp.banner_pole(c, (k + (sd > 0)) % 2), p.x, p.y, _lowest(ground, p.x, p.y, 0.4) - 0.2,
                        rot=road_rot(q) + (math.pi if sd < 0 else 0.0), coll="Village", role="both")
    # The windmill, the water tank, the lookout tower and crates, away from the rim.
    away = 1 if M.canyon_d(*(c.at(sg).side(20.0).xy)) > M.canyon_d(*(c.at(sg).side(-20.0).xy)) else -1
    for proto, ds, off, room in ((cp.windmill_tower(c), -80.0, 24.0, 5.0), (cp.water_tank(c), -56.0, 18.0, 4.0),
                                 (cp.lookout_tower(c), -104.0, 22.0, 5.0), (cp.crates(c, 0), -28.0, 11.0, 2.0),
                                 (cp.crates(c, 1), -14.0, 12.0, 2.0)):
        q = c.at(sg + ds)
        for extra in (0.0, 6.0, 12.0, -4.0):
            p = q.side(away * (q.w / 2 + off + extra))
            if (_off_roads(c, p.x, p.y, room) and taken.clear(p.x, p.y, room) and M.canyon_d(p.x, p.y) > M.CANYON_HW + room + 2
                    and _spread(ground, p.x, p.y, room) < 1.5):
                c.place(proto, p.x, p.y, _lowest(ground, p.x, p.y, room) - 0.2, rot=road_rot(q) + 0.3, coll="Village", role="both")
                taken.add(p.x, p.y, room + 1.0)
                break
    rim_rail(c, ground, taken)


def rim_rail(c, ground, taken):
    """A timber guard rail on the canyon's side of the road wherever the road runs within
    30 m of its rim: posts every 3 m at the road's edge, two rails between, one solid
    run (broken only where a side road or a spur leaves)."""
    m = gs.Mesh()
    n = 0
    for s0, s1 in _runs(c, lambda q: M.look_at(q.p.x, q.p.y) == "canyon"):
        last = None
        s = s0
        while s <= s1:
            q = c.at(s)
            sd = 1 if M.canyon_d(*q.side(8.0).xy) < M.canyon_d(*q.side(-8.0).xy) else -1
            p = q.side(sd * (q.w / 2 + 1.4))
            near = M.canyon_d(p.x, p.y) < M.CANYON_HW + 30.0
            ok = near and _off_roads(c, p.x, p.y, 0.6) and taken.clear(p.x, p.y, 0.2)
            if ok:
                z = ground(p.x, p.y)
                m.add(TIMBER, lambda bm, p=p, z=z: cuboid(bm, (p.x, p.y, z + 0.45), (0.22, 0.22, 1.5), 0.0))
                if last is not None and last[3] == sd and math.hypot(p.x - last[0], p.y - last[1]) < 4.5:
                    for hz in (0.55, 1.05):
                        m.add(("fence_rail", "wall"), lambda bm, a=(last[0], last[1], last[2] + hz), b=(p.x, p.y, z + hz):
                              _beam(bm, a, b, 0.14))
                last = (p.x, p.y, z, sd)
                n += 1
            else:
                last = None
            s += 3.0
    m.build(c, "Rim Rail", "Village", role="both")
    print("canyon rim rail: %d posts" % n)


# ------------------------------------------------------------------ Havasu


def havasu_village(c, ground, taken, ter):
    """Oasis Haven's village by Havasu's rim, where its gateway stands: the log ranch gate
    over the road, adobe homes either side (vigas, ristras, turquoise doors) on land graded
    level, lantern posts down the road, a ramada, the campground's sites back from the
    road, a corral with its horses, cottonwoods. Returns where the folk live."""
    gx, gy = M.GATES["oasis"]
    smp, _ = c.nearest(gx, gy)
    sg = smp.s
    # The ranch gate, 50 m before the gateway.
    q = c.at(sg - 50.0)
    m = gs.Mesh()
    rot = road_rot(q)
    span = q.w + 6.0
    ends = []
    for sd in (-1, 1):
        p = q.side(sd * span / 2)
        ends.append(p)
        z0 = _lowest(ground, p.x, p.y, 0.6)
        m.add(TIMBER, lambda bm, p=p, z0=z0: tube(bm, [(p.x, p.y, z0 - 0.6), (p.x, p.y, q.p.z + 11.5)], 0.55, n=8))
    a, b = ends
    for z, r, over in ((10.6, 0.5, 1.6), (8.4, 0.32, 0.6)):
        dx, dy = (b.x - a.x) / span, (b.y - a.y) / span
        m.add(TIMBER, lambda bm, z=z, r=r, over=over: tube(
            bm, [(a.x - dx * over, a.y - dy * over, q.p.z + z), (b.x + dx * over, b.y + dy * over, q.p.z + z)], r, n=7))
    m.build(c, "Ranch Gate", "Village", role="both")
    c.place(gp.cattle_skull(c), q.p.x, q.p.y, q.p.z + 11.4, rot=rot - math.pi / 2, scale=2.2, coll="Village", role="visual")
    # Adobe homes either side, every 18 m, from the gate on.
    homes = []
    k = 0
    for ds in range(-40, 70, 18):
        q = c.at(sg + ds)
        for sd in (-1, 1):
            w, d, h = 9.0 + (k % 2), 8.0, 6.0 + 1.4 * (k % 3)
            p = q.side(sd * (q.w / 2 + 10.0 + 2.0 * (k % 2)))
            rot = math.atan2(q.p.y - p.y, q.p.x - p.x) + math.pi / 2  # (it faces -Y: its door to the road)
            if not (_off_roads(c, p.x, p.y, 7.0) and taken.clear(p.x, p.y, 6.5)):
                k += 1
                continue
            hs = [ground(p.x + dx, p.y + dy) for dx in (-5, 0, 5) for dy in (-5, 0, 5)]
            if max(hs) - min(hs) > 3.5 or _near_water(p.x, p.y, 8.0):
                k += 1
                continue
            z = sum(hs) / len(hs)
            paint.grade(c, ter, p.x, p.y, rot, w + 1.0, d + 1.0, z, front=2.5)
            c.place(od.house(c, k % 4, w, d, h), p.x, p.y, z - 0.05, rot=rot, coll="Village", role="visual")
            c.place(od.collider(c, w, d, h * 0.62), p.x, p.y, z - 0.6, rot=rot, coll="Village", role="collision")
            taken.add(p.x, p.y, 7.0)
            homes.append((p.x, p.y))
            k += 1
    # Lantern posts down the road through the village, by turns either side, every 24 m.
    post = gp.lantern_post(c)
    lx, _ly, lz = gp.LANTERN_POST_LIGHT
    for j, ds in enumerate(range(-56, 80, 24)):
        q = c.at(sg + ds)
        sd = 1 if j % 2 else -1
        p = q.side(sd * (q.w / 2 + 2.6))
        if _off_roads(c, p.x, p.y, 0.4) and taken.clear(p.x, p.y, 0.4):
            r = road_rot(q) + (math.pi / 2 if sd > 0 else -math.pi / 2)
            z = _lowest(ground, p.x, p.y, 0.3) - 0.1
            c.place(post, p.x, p.y, z, rot=r, coll="Village", role="both")
            g = c.game(p.x + lx * math.cos(r), p.y + lx * math.sin(r), z + lz)
            c.entity("lantern", x=g[0], y=g[1], z=g[2])
    # A ramada at the roadside; the campground's sites and a corral back from the road.
    q = c.at(sg + 26.0)
    for sd in (1, -1):
        p = q.side(sd * (q.w / 2 + 5.5))
        if _off_roads(c, p.x, p.y, 3.0) and taken.clear(p.x, p.y, 3.5) and _spread(ground, p.x, p.y, 3.0) < 0.8:
            c.place(od.ramada(c, 0), p.x, p.y, _lowest(ground, p.x, p.y, 3.0) - 0.05, rot=road_rot(q) + (math.pi if sd > 0 else 0.0),
                    coll="Village", role="both")
            taken.add(p.x, p.y, 4.0)
            break
    n_sites = 0
    for j, ds in enumerate((-30.0, -6.0, 18.0, 42.0)):
        q = c.at(sg + ds)
        for sd in (-1, 1):
            p = q.side(sd * (q.w / 2 + 32.0))
            if (n_sites >= 3 or not _off_roads(c, p.x, p.y, 9.0) or not taken.clear(p.x, p.y, 9.0) or _near_water(p.x, p.y, 10.0)
                    or _spread(ground, p.x, p.y, 7.0) > 3.0):
                continue
            z = ground(p.x, p.y)
            rot = math.atan2(q.p.y - p.y, q.p.x - p.x) + math.pi / 2
            paint.grade(c, ter, p.x, p.y, rot, 15.0, 13.0, z, front=1.0)
            c.place(od.wall_tent(c, n_sites % 2), p.x, p.y, z - 0.05, rot=rot, coll="Village", role="visual")
            c.place(od.collider(c, 14.0, 12.3, 3.2, 0.85, "sail_cloth"), p.x, p.y, z - 0.1, rot=rot, coll="Village", role="collision")
            taken.add(p.x, p.y, 10.0)
            n_sites += 1
            break
    for ds, sd in ((70.0, 1), (70.0, -1), (-60.0, 1), (-60.0, -1)):
        q = c.at(sg + ds)
        p = q.side(sd * (q.w / 2 + 26.0))
        if (_off_roads(c, p.x, p.y, 12.0) and taken.clear(p.x, p.y, 13.0) and not _near_water(p.x, p.y, 14.0)
                and _spread(ground, p.x, p.y, 10.0) < 3.0):
            z = ground(p.x, p.y)
            rot = road_rot(q) + (0.0 if sd > 0 else math.pi)
            paint.grade(c, ter, p.x, p.y, rot, 22.0, 16.0, z, front=0.0)
            od.corral(c, p.x, p.y, z, rot)
            taken.add(p.x, p.y, 13.0)
            break
    # Cottonwoods along the road through the village, back from it.
    trees = [smp_.broadleaf(c, v, frosted=False) for v in range(2)]
    for j, ds in enumerate(range(-50, 80, 15)):
        q = c.at(sg + ds)
        sd = 1 if j % 2 else -1
        p = q.side(sd * (q.w / 2 + 20.0 + 3.0 * (j % 3)))
        if _off_roads(c, p.x, p.y, 8.0) and taken.clear(p.x, p.y, 4.0):
            c.place(trees[j % 2], p.x, p.y, _lowest(ground, p.x, p.y, 1.0) - 0.2, rot=j * 1.7, scale=0.9 + 0.1 * (j % 3),
                    coll="Village", role="both")
            taken.add(p.x, p.y, 4.0)
    print("havasu village: %d homes, %d camp sites" % (len(homes), n_sites))
    q = c.at(sg)
    return q.p.x, q.p.y


def _hazard_d(x, y):
    """How far (x, y) is from the canyon's rim, Havasu's water and the crater's rim."""
    fx, fy, fr, _fz = M.FALLS
    cx, cy, R, _r, _f = M.CRATER
    return min(M.canyon_d(x, y) - M.CANYON_HW, math.hypot(x - fx, y - fy) - fr, math.hypot(x - cx, y - cy) - R)


def _near_water(x, y, r):
    fx, fy, fr, _fz = M.FALLS
    return math.hypot(x - fx, y - fy) < fr + r or M.canyon_d(x, y) < M.CANYON_HW + r


# ------------------------------------------------------------------ the crater


def crater_camp(c, ground, taken, ter):
    """Impact Depths' approach where its gateway stands on the crater's rim: the rustic
    timber arch over the road, warning signs down the rim side of the road every 16 m, the
    surveyors' camp (tents, a scope, crates) back from the rim."""
    cx, cy, R, _rim, _fz = M.CRATER
    gx, gy = M.GATES["impact"]
    smp, _ = c.nearest(*M.ROUTE[29][:2])  # (over the crater's east rim: where the road goes down into it)
    q = c.at(smp.s - 14.0)
    timber_arch(c, ground, q, "Impact Arch", h=9.0, banners=False)  # (not "Crater ...": tests/hitboxes reads that as a crate)
    n = 0
    for s0, s1 in _runs(c, lambda q: M.look_at(q.p.x, q.p.y) == "crater"):
        s = s0 + 6.0
        while s < s1 - 6.0:
            q = c.at(s)
            sd = 1 if math.hypot(*(q.side(8.0).xy - Vector((cx, cy)))) < math.hypot(*(q.side(-8.0).xy - Vector((cx, cy)))) else -1
            p = q.side(sd * (q.w / 2 + 2.2))
            if math.hypot(p.x - cx, p.y - cy) < R + 30.0 and _off_roads(c, p.x, p.y, 0.8) and taken.clear(p.x, p.y, 0.5):
                c.place(ip.warning_sign(c, n % 2), p.x, p.y, _lowest(ground, p.x, p.y, 0.4) - 0.1, rot=road_rot(q) + math.pi / 2 * sd,
                        coll="Village", role="both")
                n += 1
            s += 16.0
    # The survey camp: three tents on graded ground out of the bowl, near the gateway.
    tents = 0
    rng = random.Random(9)
    for _ in range(600):
        if tents >= 3:
            break
        a = rng.uniform(0, math.tau)
        r = rng.uniform(14.0, 50.0)
        ox, oy, _r = M.OBSERVATORY
        x, y = ox + r * math.cos(a), oy + r * math.sin(a)
        if math.hypot(x - cx, y - cy) < R + 10.0 or not _off_roads(c, x, y, 6.0) or not taken.clear(x, y, 5.0):
            continue
        if _spread(ground, x, y, 3.5) > 2.5:
            continue
        z = ground(x, y)
        q, _d = c.nearest(x, y)
        rot = math.atan2(q.p.y - y, q.p.x - x) + math.pi / 2
        paint.grade(c, ter, x, y, rot, 7.0, 7.0, z, front=1.5)
        c.place(ip.tent(c, tents % 2), x, y, z - 0.1, rot=rot, coll="Village", role="both")
        taken.add(x, y, 6.0)
        tents += 1
    print("crater: %d warning signs, %d tents" % (n, tents))


# ------------------------------------------------------------------ the roads


def chevrons(c, ground, taken, skip=("town", "post", "pueblo", "crater")):
    """Amber chevron boards round the outside of every big bend (the heading turning more
    than 30 degrees over 40 m), every 12 m through it, facing the drivers coming in."""
    n = 0
    s = 0.0
    while s < c.length:
        a, b = c.at(s - 20.0), c.at(s + 20.0)
        turn = (math.atan2(b.t.y, b.t.x) - math.atan2(a.t.y, a.t.x) + math.pi) % math.tau - math.pi
        q = c.at(s)
        if abs(turn) > 0.52 and M.look_at(q.p.x, q.p.y) not in skip and q.p.z < 16.0:
            sd = 1 if turn > 0 else -1  # (a left turn's outside is on the right: +)
            p = q.side(sd * (q.w / 2 + 3.2))
            if _off_roads(c, p.x, p.y, 1.2) and taken.clear(p.x, p.y, 0.6):
                back = c.at(s - 30.0).p
                nv = Vector((back.x - p.x, back.y - p.y, 0)).normalized()
                c.place(cp.chevron_sign(c, 1), p.x, p.y, _lowest(ground, p.x, p.y, 0.5) - 0.2, rot=math.atan2(-nv.x, nv.y),
                        coll="Village", role="both")
                taken.add(p.x, p.y, 0.8)
                n += 1
            s += 12.0
        else:
            s += 3.0
    print("chevrons: %d" % n)


def telegraph_pole(c):
    """A telegraph pole: a tall peeled pole, a crossarm with four glass insulators, a
    brace under it. About 8 m. Wires go from the insulators (x +-1.0, z 7.5)."""
    name = "Telegraph Pole"

    def build(bm):
        k0 = len(bm.faces)
        tube(bm, [(0, 0, -0.6), (0, 0, 8.2)], [0.17, 0.12], n=7)
        cuboid(bm, (0, 0, 7.35), (2.6, 0.14, 0.16))
        _beam(bm, (-0.7, 0, 7.25), (0, 0, 6.5), 0.06)
        _beam(bm, (0.7, 0, 7.25), (0, 0, 6.5), 0.06)
        wood = _faces(bm, k0)
        k1 = len(bm.faces)
        for x in (-1.15, -0.45, 0.45, 1.15):
            blob(bm, (x, 0, 7.55), 0.09, sz=1.3, subdiv=1)
        glass = _faces(bm, k1)
        return [(c.lib("weathered_timber", "wall"), wood), (c.lib("lantern_glass", "wall"), glass)]

    return c.proto(name, build) and name


def telegraph(c, ground, taken, looks=("canyon", "falls", "show", "pueblo")):
    """Telegraph poles down the long open stretches, on the left of the road 6 m off it,
    every 34 m, the wires strung pole to pole with a sag (broken where a pole can't stand)."""
    pole = telegraph_pole(c)
    m = gs.Mesh()
    n = 0
    for s0, s1 in _runs(c, lambda q: M.look_at(q.p.x, q.p.y) in looks and 8.0 < q.p.z < 16.0):
        if s1 - s0 < 80.0:
            continue
        last = None
        s = s0 + 10.0
        while s < s1 - 10.0:
            q = c.at(s)
            # (On the side away from the canyon and the crater: the wires keep to one side
            # over a run, and break where it swaps.)
            sd = 1 if _hazard_d(*q.side(10.0).xy) > _hazard_d(*q.side(-10.0).xy) else -1
            p = q.side(sd * (q.w / 2 + 6.0))
            if last is not None and last[4] != sd:
                last = None
            if _off_roads(c, p.x, p.y, 4.0) and taken.clear(p.x, p.y, 0.8) and _hazard_d(p.x, p.y) > 6.0:
                z = _lowest(ground, p.x, p.y, 0.3)
                rot = road_rot(q) + math.pi / 2  # (its crossarm across the line, the wires along it)
                c.place(pole, p.x, p.y, z, rot=rot, coll="Village", role="both")
                taken.add(p.x, p.y, 1.0)
                n += 1
                if last is not None:
                    for u in (-1.15, -0.45, 0.45, 1.15):
                        a = (last[0] + u * math.cos(last[3]), last[1] + u * math.sin(last[3]), last[2] + 7.62)
                        b = (p.x + u * math.cos(rot), p.y + u * math.sin(rot), z + 7.62)
                        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2 - 0.9)
                        m.add(("rail_iron", "wall"), lambda bm, a=a, mid=mid: _beam(bm, a, mid, 0.025))
                        m.add(("rail_iron", "wall"), lambda bm, mid=mid, b=b: _beam(bm, mid, b, 0.025))
                last = (p.x, p.y, z, rot, sd)
            else:
                last = None
            s += 34.0
    m.build(c, "Telegraph Wires", "Village", role="visual")
    print("telegraph: %d poles" % n)


# ------------------------------------------------------------------ the pueblo and the post

# (mesa_region.BEDS: the cliffs' beds of colour by height.)
BEDS = [(4.0, "strata_red"), (16.0, "strata_rust"), (22.0, "strata_orange"), (34.0, "strata_red"), (40.0, "strata_cream"),
        (58.0, "strata_orange"), (64.0, "strata_rust"), (80.0, "strata_red"), (88.0, "strata_cream"), (999.0, "strata_orange")]


def _bed(z, x=0.0):
    """The cliff's rock: the level beds (make_textures.desert_strata, review-desert_region
    note 1), one texture whose beds lie by height."""
    return "desert_strata"


def alcove_overhang(c, top=81.6):
    """The pueblo's alcove's roof: the mesa's caprock carried on out over the alcove in one
    shell of rock (its top the mesa's, under it a vault rising from a ragged lip at the
    front to the back), its faces in the cliff's own beds of colour; its sides and back
    run into the cliff. Solid."""
    ax, ay, w, dp = M.ALCOVE
    fz = M.ALCOVE_Z
    NU, NV = 28, 12
    us = [-1.32 + 2.64 * i / NU for i in range(NU + 1)]
    vs = [-0.22 + 1.52 * j / NV for j in range(NV + 1)]
    rng = random.Random(3)
    lip = [rng.uniform(-1.6, 1.2) for _ in us]

    def under(i, j):
        u, v = us[i], vs[j]
        e = math.hypot(u, max(0.0, v))
        if e > 1.08:
            return fz - 2.0  # (in the cliff)
        z = fz + 15.0 + 8.0 * max(0.0, 1.0 - e * e) - 2.0 * max(0.0, -v) / 0.22
        if j == 0:
            z += lip[i]
        return z

    bm = bmesh.new()
    T = [[bm.verts.new((ax + u * w / 2, ay + v * dp, top)) for v in vs] for u in us]
    B = [[bm.verts.new((ax + us[i] * w / 2, ay + vs[j] * dp, under(i, j))) for j in range(NV + 1)] for i in range(NU + 1)]
    faces = []
    for i in range(NU):
        for j in range(NV):
            faces.append(bm.faces.new((T[i][j], T[i + 1][j], T[i + 1][j + 1], T[i][j + 1])))
            faces.append(bm.faces.new((B[i][j], B[i][j + 1], B[i + 1][j + 1], B[i + 1][j])))
        faces.append(bm.faces.new((T[i][0], B[i][0], B[i + 1][0], T[i + 1][0])))  # (the lip)
        faces.append(bm.faces.new((T[i][NV], T[i + 1][NV], B[i + 1][NV], B[i][NV])))
    for i in (0, NU):
        for j in range(NV):
            faces.append(bm.faces.new((T[i][j], T[i][j + 1], B[i][j + 1], B[i][j])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.faces.ensure_lookup_table()
    mats = {}
    for f in bm.faces:
        cz = f.calc_center_median()
        key = "slickrock" if f.normal.z > 0.7 else _bed(cz.z, cz.x)
        mats.setdefault(key, []).append(f.index)
    ob = c.mesh_object("Alcove Overhang", bm, "Village", "both")
    for key, idx in mats.items():
        c.assign(ob, c.lib(key, "dirt" if key == "slickrock" else "wall"), idx)


PUEBLO_T1 = (4.5, 179.0)  # the upper terrace: its height over the floor, its front (y)
# The front row along the terrace's wall (review-desert_region 4, note 3: "we need to line
# this wall with more houses, keep the same style but lets have this front row have the
# houses that slightly vary"): (x off the alcove's middle, width, depth, height, setback)
PUEBLO_ROW = [(-23.2, 6.2, 5.0, 4.4, 0.0), (-16.4, 5.6, 4.6, 5.2, 0.4), (-9.9, 6.6, 5.4, 4.0, 0.1), (-3.0, 5.8, 4.8, 5.6, 0.5),
              (3.8, 6.4, 5.2, 4.6, 0.0), (10.6, 5.4, 4.4, 4.2, 0.3), (17.1, 6.8, 5.6, 5.0, 0.1), (23.6, 5.6, 4.8, 4.4, 0.4)]


def pueblo_homes(c, ground, taken):
    """The pueblo, to drive about in (review-desert_region 3, notes 2 and 3; 4, notes 1-3):
    its floor in from the way up through the alcove's lip, a row of homes lining the whole
    front of the upper terrace (Oasis Haven's adobe, each a little different: wider or
    narrower, a storey taller or lower, set a little back or forward, the variants by
    turns), and the terrace of solid adobe behind, with
    its own row of homes at the back. (No ramp up to the terrace any more: note 1.) Returns
    how many."""
    ax, ay, w, dp = M.ALCOVE
    fz = M.ALCOVE_Z
    h, fy = PUEBLO_T1
    k = 0
    # The upper terrace: one solid block of adobe, its front a wall running back into the cliff.
    box(c, "Pueblo Terrace", ax, fy + 9.0, 26.0, 9.0, fz - 2.0, fz + h, ("adobe", "dirt"))
    box(c, "Pueblo Terrace Coping", ax, fy + 0.15, 26.2, 0.35, fz + h - 0.05, fz + h + 0.35, ("adobe_dark", "wall"), role="visual")
    # The front row, backs to the terrace's wall, doors out over the plaza.
    for j, (dx, ww, dd_, hh, back) in enumerate(PUEBLO_ROW):
        x, y = ax + dx, fy - 0.1 - back - dd_ / 2
        c.place(od.house(c, (j + 1) % 4, ww, dd_, hh), x, y, fz - 0.05, rot=0.0, coll="Village", role="visual")
        c.place(od.collider(c, ww, dd_, hh * 0.62), x, y, fz - 0.6, rot=0.0, coll="Village", role="collision")
        k += 1
    # The homes on the terrace, along its back with a lane in front of them.
    for j in range(5):
        x = ax - 18.0 + j * 9.0
        ww, dd_, hh = 6.8 - 0.6 * (j % 2), 5.0, 4.4 + 0.8 * (j % 2)
        yy = fy + 5.6 + dd_ / 2
        c.place(od.house(c, (k + 1) % 4, ww, dd_, hh), x, yy, fz + h - 0.05, rot=0.0, coll="Village", role="visual")
        c.place(od.collider(c, ww, dd_, hh * 0.62), x, yy, fz + h - 0.6, rot=0.0, coll="Village", role="collision")
        k += 1
    taken.add(ax, ay + 10.0, 34.0)
    return k


# The plaza's everyday things (review-desert_region 4, note 4: "we need more props here. a
# few more fires, other things that would be present"): (prop, x, y off the alcove's middle,
# turn). Clear of the way in (its end at y -6), the kivas (x +-16, y -10) and their ovens.
PUEBLO_FIRES = [(-30.0, -6.0), (30.0, -6.0), (-8.0, 3.4), (8.5, 3.6)]
PUEBLO_THINGS = [("ristra_rack", -20.5, 4.6, 0.0), ("ristra_rack", 18.0, 4.8, 0.0), ("ristra_rack", -22.0, -3.0, 0.3),
                 ("ollas", -27.0, 5.0, 0.3), ("ollas", 2.0, 5.3, 1.2), ("ollas", 26.0, 5.0, 2.0), ("ollas", -13.0, 4.9, 0.7),
                 ("ollas", 13.5, 4.4, 2.6), ("woodpile", -33.0, 6.5, 0.0), ("woodpile", 32.5, 5.5, 0.1), ("woodpile", -5.0, 5.6, 0.0),
                 ("blanket_line", -28.0, -12.0, 0.4), ("blanket_line", 28.0, -12.0, -0.4), ("grinding", 4.6, 4.2, 0.2),
                 ("grinding", -2.4, 4.0, -0.1), ("corn_heap", 22.0, 2.0, 0.5), ("corn_heap", -24.5, 1.0, 2.0),
                 ("ramada", -30.0, -0.5, 0.0), ("ramada", 30.5, -0.8, 0.0)]


def pueblo_plaza(c, ground):
    """The fires (stone rings, their flames and smoke) and the plaza's things. Returns how
    many."""
    import pueblo_props as pp

    ax, ay, w, dp = M.ALCOVE
    n = 0
    for k, (dx, dy) in enumerate(PUEBLO_FIRES):
        x, y = ax + dx, ay + dy
        z = ground(x, y)
        c.place(pp.fire_ring(c, k), x, y, z - 0.05, rot=k * 1.3, role="visual")
        g = c.game(x, y, z + 0.3)
        c.entity("campfire", x=round(g[0], 2), y=round(g[1], 2), z=round(g[2], 2))
        n += 1
    for k, (kind, dx, dy, rot) in enumerate(PUEBLO_THINGS):
        x, y = ax + dx, ay + dy
        proto = od.ramada(c, k % 2) if kind == "ramada" else getattr(pp, kind)(c, k % 3)
        c.place(proto, x, y, ground(x, y) - 0.05, rot=rot, role="both" if kind == "ramada" else "visual")
        n += 1
    return n


def post_homes(c, ground, taken, ter):
    """The trading post's adobe homes round its square, each Oasis Haven's, on land graded
    level, their doors to the square."""
    px, py, pr = M.POST
    n = 0
    for k, (a, w, d, h) in enumerate(((0.9, 11.0, 9.0, 6.0), (1.9, 9.0, 8.0, 7.0), (2.9, 10.0, 8.0, 6.5), (4.2, 11.0, 9.0, 7.5),
                                      (5.2, 9.0, 8.0, 6.0))):
        x, y = px + (pr + 7.0) * math.cos(a), py + (pr + 7.0) * math.sin(a)
        rot = a + math.pi / 2  # (its -Y, its door, to the square's middle)
        hs = [ground(x + dx, y + dy) for dx in (-5, 0, 5) for dy in (-5, 0, 5)]
        if max(hs) - min(hs) > 3.5:
            continue
        z = sum(hs) / len(hs)
        paint.grade(c, ter, x, y, rot, w + 1.0, d + 1.0, z, front=2.5)
        c.place(od.house(c, k % 4, w, d, h), x, y, z - 0.05, rot=rot, coll="Village", role="visual")
        c.place(od.collider(c, w, d, h * 0.62), x, y, z - 0.6, rot=rot, coll="Village", role="collision")
        taken.add(x, y, 7.0)
        n += 1
    return n


# ------------------------------------------------------------------ the ledge


def parapet(c, ground, taken):
    """The Ledge Road's and the High Road's parapet: one continuous wall of the cliff's
    cream stone along the drop side of the road (no gaps, no blocks), its coping a little
    proud of it. Solid."""
    n = 0
    for side in (-1, 1):
        run = []

        def flush(run):
            if len(run) < 4:
                return 0
            bm = bmesh.new()
            rings = []
            for i, (x, y, z0, z1, nx, ny) in enumerate(run):
                hw = 0.45
                rings.append([bm.verts.new((x - nx * hw, y - ny * hw, z0)), bm.verts.new((x + nx * hw, y + ny * hw, z0)),
                              bm.verts.new((x + nx * hw, y + ny * hw, z1)), bm.verts.new((x - nx * hw, y - ny * hw, z1))])
            for r0, r1 in zip(rings, rings[1:]):
                for k in range(4):
                    bm.faces.new((r0[k], r1[k], r1[(k + 1) % 4], r0[(k + 1) % 4]))
            bm.faces.new(list(reversed(rings[0])))
            bm.faces.new(rings[-1])
            body = len(bm.faces)
            crings = []
            for x, y, z0, z1, nx, ny in run:
                hw = 0.6
                crings.append([bm.verts.new((x - nx * hw, y - ny * hw, z1)), bm.verts.new((x + nx * hw, y + ny * hw, z1)),
                               bm.verts.new((x + nx * hw, y + ny * hw, z1 + 0.22)), bm.verts.new((x - nx * hw, y - ny * hw, z1 + 0.22))])
            for r0, r1 in zip(crings, crings[1:]):
                for k in range(4):
                    bm.faces.new((r0[k], r1[k], r1[(k + 1) % 4], r0[(k + 1) % 4]))
            bm.faces.new(list(reversed(crings[0])))
            bm.faces.new(crings[-1])
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            ob = c.mesh_object("Ledge Parapet %d %d" % (side, len(run)), bm, "Village", "both")
            c.assign(ob, c.lib("strata_cream", "wall"), range(body))
            c.assign(ob, c.lib("slickrock", "wall"), range(body, len(ob.data.polygons)))
            return 1

        s = 0.0
        while s < c.length:
            q = c.at(s)
            ok = q.p.z > 16.0 and M.look_at(q.p.x, q.p.y) in ("mesa", "show", "post")
            if ok:
                x, y = q.p.x + q.r.x * side * (q.w / 2 + 1.0), q.p.y + q.r.y * side * (q.w / 2 + 1.0)
                drop = M.natural(x + q.r.x * side * 5.0, y + q.r.y * side * 5.0) < q.p.z - 3.0
                # (not along the Gap Bridge: it has its own timber rails)
                ok = drop and math.hypot(q.p.x - M.ARCH[0], q.p.y - M.ARCH[1]) > 32.0 and _off_roads(c, x, y, 0.3) and not any(
                    (e.p.x - x) ** 2 + (e.p.y - y) ** 2 < (e.w / 2 + 1.5) ** 2 for e in c.extra_ground)
            if ok:
                run.append((x, y, max(min(ground(x, y), q.p.z) - 1.2, q.p.z - 12.0), q.p.z + 0.75, q.r.x, q.r.y))
                taken.add(x, y, 1.0)
            else:
                n += flush(run)
                run = []
            s += 2.0
        n += flush(run)
    print("ledge parapet: %d runs" % n)


# ------------------------------------------------------------------ the arena


def arena_fence(c, ground, gate_a):
    """The rodeo ring's fence: stout timber posts every 2.6 m round it, three rails between
    them, its gate open toward the lair; one solid mesh, every post on the ground."""
    ax, ay, ar = M.ARENA
    m = gs.Mesh()
    n = int(math.tau * ar / 2.6)
    pts = []
    for k in range(n + 1):
        a = k * math.tau / n
        gap = abs((a - gate_a + math.pi) % math.tau - math.pi) < 0.12
        x, y = ax + ar * math.cos(a), ay + ar * math.sin(a)
        pts.append(None if gap else (x, y, _lowest(ground, x, y, 0.3)))
    for p in pts[:-1]:
        if p:
            m.add(TIMBER, lambda bm, p=p: tube(bm, [(p[0], p[1], p[2] - 0.5), (p[0], p[1], p[2] + 2.2)], 0.16, n=6))
    for a, b in zip(pts, pts[1:]):
        if a and b:
            for hz in (0.7, 1.35, 2.0):
                m.add(("fence_rail", "wall"), lambda bm, a=a, b=b, hz=hz: _beam(bm, (a[0], a[1], a[2] + hz), (b[0], b[1], b[2] + hz), 0.12))
    m.build(c, "Arena Fence", "Village", role="both")


def post_store(c, ground, taken, ter):
    """The trading post's store on the square's south side, Dry Gulch's frontier kit: a
    long false-fronted store, its GENERAL sign, a boardwalk porch with lanterns, lit
    windows, its door to the square; on land graded level."""
    px, py, pr = M.POST
    sc = _scene(c, ter)
    gs.protos(c)
    x, y = px + 4.0, py - pr - 4.0
    rot = math.pi  # (its front north, to the square; its body south of it)
    w, d = 18.0, 11.0
    cx, cy = x, y - d / 2
    hs = [ground(cx + dx, cy + dy) for dx in (-w / 2, 0.0, w / 2) for dy in (-d / 2 - 3.4, 0.0, d / 2)]
    z = ground(x, y + 1.0)
    if max(hs) - min(hs) > 4.0:
        return False
    paint.grade(c, ter, cx, cy, rot, w + 1.0, d + 1.0, z, front=3.8)
    m = gs.Mesh()
    gt.building(m, sc, x, y, z + 0.05, rot, w, d, siding="siding_ochre", sign="general", lit=0.8, ghost=0.0, seed=7)
    m.build(c, "Trading Post Store", "Village", role="both")
    for lx, ly, lz in sc.lanterns:
        g = c.game(lx, ly, lz)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
    taken.add(cx, cy, 11.0)
    return True


# ------------------------------------------------------------------ the crater's depths


def crater_depths(c, ground, taken):
    """Down in the crater (Blake, Nov 1: "drive down into the actual crater ... encorporate
    themes from this level"): Impact Depths' worlds on the way down its spiral, as the
    course's terraces: the crystal wall on the upper south wall (great clusters of aqua,
    amethyst and rose crystal, flaring crystals at the road's edge), the Lost World's
    jungle ledge lower down (cycads, tree ferns, horsetails, glowing fungi), and the core
    on its floor (the meteorite in a ring of lava, black lava spires, glowing rocks); the
    climb out up its north wall through black volcanic rock."""
    import aurora_props as ap
    import volcano_props as vp

    cx, cy, R, _rim, _fz = M.CRATER
    AQUA, AMETHYST, ROSE = "crystal_aqua", "crystal_amethyst", "crystal_rose"

    def zone(x, y):
        a = math.degrees(math.atan2(y - cy, x - cx))
        r = math.hypot(x - cx, y - cy)
        if r < 20.0:
            return "core"
        if -100.0 <= a <= 10.0:
            return "crystal"
        if a < -100.0 or a > 150.0:
            return "jungle"
        return "volcanic"

    def ring_pts(n, rmin, rmax, seed, room, want):
        rng = random.Random(seed)
        out = []
        for _ in range(n * 30):
            if len(out) >= n:
                break
            a = rng.uniform(0, math.tau)
            r = rng.uniform(rmin, rmax)
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            if zone(x, y) != want or not _off_roads(c, x, y, room) or not taken.clear(x, y, room * 0.8):
                continue
            out.append((x, y))
            taken.add(x, y, room * 0.8)
        return out

    big = [ap.spire_cluster(c, k, 16.0 + 5 * k, mat=(AQUA, AMETHYST, ROSE)[k], accent=(AMETHYST, ROSE, AQUA)[k]) for k in range(3)]
    small = [vp.crystals(c, m, k) for k, m in enumerate((AQUA, AMETHYST, ROSE))]
    nb = 0
    for k, (x, y) in enumerate(ring_pts(9, 30.0, R + 6.0, 31, 6.0, "crystal")):
        c.place(big[k % 3], x, y, _lowest(ground, x, y, 2.0) - 1.5, rot=rnd(k * 3.1) * math.tau, scale=0.45 + 0.2 * rnd(k * 1.7),
                coll="Crater", role="visual")
        nb += 1
    for k, (x, y) in enumerate(ring_pts(26, 24.0, R + 4.0, 37, 2.5, "crystal")):
        c.place(small[k % 3], x, y, _lowest(ground, x, y, 1.0) - 0.3, rot=k, scale=0.4 + 0.3 * rnd(k), coll="Crater", role="visual")
    # The flaring crystals at the road's edge down the crystal wall, by turns either side.
    for s0, s1 in _runs(c, lambda q: math.hypot(q.p.x - cx, q.p.y - cy) < R and zone(q.p.x, q.p.y) == "crystal"):
        s, k = s0 + 8.0, 0
        while s < s1:
            q = c.at(s)
            p = q.side((1 if k % 2 else -1) * (q.w / 2 + 2.2))
            if _off_roads(c, p.x, p.y, 0.6):
                z = _lowest(ground, p.x, p.y, 0.6)
                c.place(small[k % 2], p.x, p.y, z - 0.3, rot=k, scale=0.35, coll="Crater", role="visual")
                g = c.game(p.x, p.y, z + 1.4)
                c.entity("shimmer", x=g[0], y=g[1], z=g[2], size=1.4, color="#5ae8ff" if k % 2 else "#d27aff")
            s += 18.0
            k += 1
    # The jungle ledge.
    nj = 0
    plants = [ip.cycad(c, k) for k in range(3)] + [ip.tree_fern(c, k) for k in range(2)] + [ip.horsetails(c, k) for k in range(2)]
    for k, (x, y) in enumerate(ring_pts(34, 20.0, R + 6.0, 51, 3.0, "jungle")):
        c.place(plants[k % len(plants)], x, y, _lowest(ground, x, y, 0.8) - 0.2, rot=rnd(k) * 6.28, scale=0.8 + 0.4 * rnd(k * 2.3),
                coll="Crater", role="visual")
        nj += 1
    for k, (x, y) in enumerate(ring_pts(6, 20.0, R, 63, 4.0, "jungle")):
        c.place(ip.giant_fungi(c, k % 3), x, y, _lowest(ground, x, y, 1.0) - 0.2, rot=k, scale=0.6, coll="Crater", role="both")
    # The core: the meteorite in its ring of lava, black spires round it.
    bm = bmesh.new()
    n = 40
    zc = ground(cx, cy)
    inner = [bm.verts.new((cx + 9.0 * math.cos(k * math.tau / n), cy + 9.0 * math.sin(k * math.tau / n), zc + 0.08)) for k in range(n)]
    outer = [bm.verts.new((cx + (13.5 + 0.8 * math.sin(k * 1.7)) * math.cos(k * math.tau / n),
                           cy + (13.5 + 0.8 * math.sin(k * 1.7)) * math.sin(k * math.tau / n), zc + 0.08)) for k in range(n)]
    for k in range(n):
        bm.faces.new((inner[k], outer[k], outer[(k + 1) % n], inner[(k + 1) % n]))
    ob = c.mesh_object("Core Lava Ring", bm, "Crater", "visual")
    c.assign(ob, c.lib("lava_flow", "wall"))
    for k in range(5):
        a = k * math.tau / 5 + 0.4
        x, y = cx + 16.5 * math.cos(a), cy + 16.5 * math.sin(a)
        if _off_roads(c, x, y, 2.5):
            c.place(ip.lava_spire(c, k % 3, 7.0 + 2.0 * (k % 3)), x, y, _lowest(ground, x, y, 1.2) - 0.6, rot=a, coll="Crater", role="both")
    taken.add(cx, cy, 18.0)
    # The volcanic north wall: black rocks with glowing fissures.
    for k, (x, y) in enumerate(ring_pts(14, 24.0, R + 4.0, 83, 3.0, "volcanic")):
        c.place(ip.rock(c, "black_rock", k % 3, 2.0 + (k % 3), glow="fissure_glow"), x, y, _lowest(ground, x, y, 1.0) - 0.4, rot=k,
                coll="Crater", role="both")
    print("crater depths: %d crystal clusters, %d jungle plants" % (nb, nj))


# ------------------------------------------------------------------ the zippers


def zippers(c, anchors):
    """Zippers on the long drives between the worlds (Blake, Nov 1: "it also feels long to
    go through ... putting zippers throughout the overworld in strategic places,
    specifically between level areas"): between each pair of places along the lap (x, y),
    one every 110 m or so of the stretch, each on its straightest bit."""
    ss = sorted(c.nearest(x, y)[0].s for x, y in anchors)
    ss.append(ss[0] + c.length)
    n = 0
    for a, b in zip(ss, ss[1:]):
        gap = b - a
        k = int(gap // 110.0)
        for j in range(k):
            want = a + gap * (j + 1) / (k + 1)
            best, bs = None, want
            for ds in range(-24, 25, 4):
                s = want + ds
                q0, q1 = c.at(s - 12.0), c.at(s + 12.0)
                turn = abs((math.atan2(q1.t.y, q1.t.x) - math.atan2(q0.t.y, q0.t.x) + math.pi) % math.tau - math.pi)
                if best is None or turn < best:
                    best, bs = turn, s
            q = c.at(bs)
            # (Blake's nudges: review-desert_region 3, note 8, "move this zipper forward like
            # 10 meters")
            bs += sum(ds for (nx, ny), ds in ZIPPER_NUDGES if math.hypot(q.p.x - nx, q.p.y - ny) < 24.0)
            c.zipper(bs % c.length, 0.0)
            n += 1
    print("zippers: %d" % n)


ZIPPER_NUDGES = [((299.3, 16.8), 10.0)]
