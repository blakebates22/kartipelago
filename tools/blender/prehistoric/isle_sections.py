# Tropic Isles v5's sub-worlds (Blake, Nov 1: "all of the areas containing the levels need
# to be their own sub world like we have been doing ... make each section containing the
# race portal immersive"; "think tropical jungle rainforest vibe"): what's new in v5,
# each part of the island dressed as its own place (the coves' courses' kits are
# isle_dress's):
#
#   the High Bridge      a rope bridge high over the gorge: timber towers at its ends,
#                        cables sagging between them, vines hung off it
#   the Temple Gate      the old temple's gate bored through the ridge: carved heads either
#                        side of each mouth, torches
#   the Jungle Heart     the falls off the pinnacle arcing over the road into their pool;
#                        the temple's stepped front in the basin's south wall, the gateway on
#                        its steps; giant trees, vines, ferns, fireflies
#   the Black Shore      black sand, obsidian and basalt, steam out of the vents, braziers,
#                        burnt palms, obsidian spires on the beach toward Volcano Isle
#   the Cloud Forest     giant trees, lianas slung between them, mossy boulders
#   the Gorge            boulders in the river, side falls off its walls, ferns
#   the Lagoon           mangroves round its shore, the fishers' canoes
#
# Every prop on the lowest ground under it; nothing on a road.
# SPDX-License-Identifier: MIT

import math
import random

import beach_props as bp
import hop_props as hp_
import isle_dress as idr
import isle_layout as M
import pocket_build as pb
import props
import region_paint as paint
import tropic_props as tp
import volcano_props as vp
from course_kit import Vector, bmesh
from keep_scenery import clear_of
from pocket_build import box

WATER_Z = M.WATER_Z


def _route_s(c, i, f=0.0):
    (ax, ay, _), (bx, by, _) = M.ROUTE[i], M.ROUTE[(i + 1) % len(M.ROUTE)]
    return c.nearest(ax + (bx - ax) * f, ay + (by - ay) * f)[0].s


def _rope(c, name, a, b, sag, r=0.09, mat=("rope_rail", "wall"), n=10):
    bm = bmesh.new()
    pts = []
    for k in range(n + 1):
        t = k / n
        p = Vector(a).lerp(Vector(b), t)
        p.z -= sag * 4 * t * (1 - t)
        pts.append(tuple(p))
    props.tube(bm, pts, r, n=5)
    ob = c.mesh_object(name, bm, "Props", "visual")
    c.assign(ob, c.lib(*mat))
    return ob


def pocket_scatter(c, proto, n, pockets, ok, ground, taken, seed, room=3.0, scale=(0.8, 1.3), role="both", sink=0.2,
                   road_margin=3.0, trunk=None, seat=None, reach=14.0, tries=80):
    """region_paint.scatter's placing, its spots tried round the named pockets' own circles
    (out `reach` m past their edges) rather than anywhere on the island: so a narrow basin
    gets its share."""
    rnd = random.Random(seed)
    circles = [cc for p in M.POCKETS if p[0] in pockets for cc in p[2]]
    placed = []
    for _ in range(n * tries):
        if len(placed) >= n:
            break
        cx, cy, r, _f = rnd.choice(circles)
        a = rnd.uniform(0, math.tau)
        d = (r + reach) * math.sqrt(rnd.random())
        x, y = cx + d * math.cos(a), cy + d * math.sin(a)
        if not ok(x, y) or not taken.clear(x, y, room) or not paint.road_clear(c, x, y, road_margin):
            continue
        sc = rnd.uniform(*scale)
        rot = rnd.uniform(0, math.tau)
        gz = ground(x, y)
        if seat:
            gz = min([gz] + [ground(x + seat * sc * math.cos(t), y + seat * sc * math.sin(t)) for t in (0.0, 1.05, 2.09, 3.14, 4.19, 5.24)])
        if trunk:
            c.place(proto, x, y, gz - sink, rot=rot, scale=sc, role="visual")
            c.place(paint.trunk_proto(c, *trunk), x, y, gz - sink, scale=sc, coll="Collision", role="collision")
            c.place_foot(proto, x, y, gz - sink, rot=rot, scale=sc)
        else:
            c.place(proto, x, y, gz - sink, rot=rot, scale=sc, role=role)
        taken.add(x, y, room * 0.5)
        placed.append((x, y))
    return placed


# ------------------------------------------------------------------ the High Bridge


def high_bridge(c, ground, span):
    """Timber pylons on the gorge's rims at both ends of the bridge (A-frames each side of
    the deck, their legs down to the lowest ground under them), the main cables slung from
    pylon to pylon, hangers down to the deck's rails, vines hung off it."""
    s0, s1 = span
    tops = []

    def rim(s, step):
        # (out from the bridge's end along the road till the land's up near the deck)
        for _ in range(16):
            q = c.at(s)
            if all(ground(*q.side(sd * (q.w / 2 + 1.6)).xy) > q.p.z - 2.5 for sd in (-1, 1)):
                return s
            s += step
        return s

    for s, k in ((rim(s0, -2.0), 0), (rim(s1, 2.0), 1)):
        q = c.at(s)
        for sd in (-1, 1):
            p = q.side(sd * (q.w / 2 + 1.6))
            for lean in (-1, 1):
                fx, fy = p.x + q.t.x * lean * 1.6, p.y + q.t.y * lean * 1.6
                z0 = min(ground(fx, fy), q.p.z) - 1.0
                bm = bmesh.new()
                props.tube(bm, [(fx, fy, z0), (p.x, p.y, q.p.z + 8.0)], [0.42, 0.34], n=6)
                ob = c.mesh_object("Bridge Pylon %d %d %d" % (k, sd, lean), bm, "Props", "both")
                c.assign(ob, c.lib("weathered_timber", "wall"))
            box(c, "Bridge Pylon %d %d Cap" % (k, sd), p.x, p.y, 0.5, 0.5, q.p.z + 7.6, q.p.z + 8.4, ("weathered_timber", "wall"),
                rot=math.atan2(q.t.y, q.t.x), role="visual")
            g = c.game(p.x, p.y, q.p.z + 8.9)
            c.entity("torch", x=g[0], y=g[1], z=g[2])
            tops.append((k, sd, (p.x, p.y, q.p.z + 8.0)))
    for sd in (-1, 1):
        a = next(t for k, s, t in tops if k == 0 and s == sd)
        b = next(t for k, s, t in tops if k == 1 and s == sd)
        _rope(c, "Bridge Cable %d" % sd, a, b, 6.5, r=0.16)
        # (hangers from the cable down to the rail, every 4 m)
        L = s1 - s0
        n = max(2, int(L / 4.0))
        for j in range(1, n):
            t = j / n
            q = c.at(s0 + L * t)
            p = q.side(sd * (q.w / 2 + 1.0))
            cz = a[2] + (b[2] - a[2]) * t - 6.5 * 4 * t * (1 - t)
            if cz > q.p.z + 1.6:
                _rope(c, "Bridge Hanger %d %d" % (sd, j), (p.x, p.y, cz), (p.x, p.y, q.p.z + 1.1), 0.0, r=0.05, n=1)
        # vines hung off its side
        for j in range(3):
            q = c.at(s0 + L * (0.25 + 0.25 * j))
            p = q.side(sd * (q.w / 2 + 1.3))
            _rope(c, "Bridge Vine %d %d" % (sd, j), (p.x, p.y, q.p.z), (p.x + 0.4, p.y, q.p.z - 4.0 - 2.0 * j), 0.0, r=0.12,
                  mat=("vine_leaf", "wall"), n=1)
    print("high bridge: %.0f m" % (s1 - s0))


# ------------------------------------------------------------------ the Temple Gate


def temple_gate(c, ground):
    """The Temple Gate: the old temple's way through the ridge, bored, its mouths framed in
    carved stone (a lintel over pillars), a stone head and a torch either side of each."""
    name, kind, a, b = M.TUNNELS[0]
    s0, s1 = pb.tunnel_span(c, M.L, a, b)
    half = pb.bore(c, M.L, name, s0, s1, ("jungle_temple", "wall"), ("isle_jungle", "grass"), height=11.0)
    for s, out in ((s0, -1), (s1, 1)):
        q = c.at(s)
        rot = math.atan2(q.t.y, q.t.x)
        for sd in (-1, 1):
            p = q.side(sd * (half + 0.6))
            box(c, "Temple Pillar %d %d" % (out, sd), p.x, p.y, 1.1, 1.1, q.p.z - 1.5, q.p.z + 11.5, ("jungle_temple", "wall"),
                rot=rot)
            h = q.side(sd * (half + 4.5))
            hx, hy = h.x + q.t.x * out * 4.0, h.y + q.t.y * out * 4.0
            if clear_of(c, hx, hy, 2.5):
                c.place(idr.tiki_head(c, 1), hx, hy, ground(hx, hy) - 0.2, rot=rot + (math.pi / 2 if out > 0 else -math.pi / 2),
                        coll="Village", role="both")
            tx, ty = h.x - q.t.x * out * 0.0, h.y
            g = c.game(p.x + q.t.x * out * 1.4, p.y + q.t.y * out * 1.4, q.p.z + 6.0)
            c.entity("torch", x=g[0], y=g[1], z=g[2])
        box(c, "Temple Lintel %d" % out, q.p.x, q.p.y, 1.4, half + 2.4, q.p.z + 11.0, q.p.z + 13.4, ("jungle_temple", "wall"),
            rot=rot + math.pi / 2, role="visual")
        box(c, "Temple Glyphs %d" % out, q.p.x + q.t.x * out * 1.45, q.p.y + q.t.y * out * 1.45, 0.08, half + 1.2,
            q.p.z + 11.4, q.p.z + 13.0, ("ruin_glyph", "wall"), rot=rot + math.pi / 2, role="visual")
    print("temple gate: %.0f m" % (s1 - s0))


# ------------------------------------------------------------------ the Jungle Heart


def heart(c, ground, taken, ter, falls_mats):
    """The falls off the pinnacle's south face, thrown out in an arc over the road into the
    plunge pool (you drive under them); two thinner falls off the spire; the temple's
    stepped front in the basin's south wall behind the rainforest's gateway; giant trees,
    lianas, stone heads; fireflies."""
    fx, fy = M.FALLS
    lx, ly = M.FALLS_LIP
    top = M.natural(lx, ly + 2.0) - 1.0
    pz = M.RIVER[0][2]
    c.disc("Plunge Pool", fx, fy, M.POOL_R + 1.0, pz, c.lib("lagoon_shallow", "water"), role="visual", n=28, wobble=0.1, seed=5)
    # (thrown out so it lands in the pool beyond the road: the road's under its arc)
    throw = (ly - fy) - 2.0
    props.falls(c, "Heart Falls", lx, ly, top, pz, 9.0, 16.0, facing=-1, throw=throw, bulge=1.6, veils=4, mats=falls_mats,
                foam_r=9.0)
    g = c.game(fx, fy, pz)
    c.entity("waterfall", x=g[0], y=g[1], z=g[2], top=round(top - pz, 1), width=16.0, heading=0.0)
    px, py = M.PEAK
    for k, a in enumerate((2.2, 0.9, 3.9)):
        r = M.PEAK_R + 4.0
        x2, y2 = px + r * math.cos(a), py + r * math.sin(a)
        t2 = M.natural(x2, y2) - 1.0
        b2 = M.natural(px + (r + 30.0) * math.cos(a), py + (r + 30.0) * math.sin(a))
        if t2 - b2 > 20.0:
            props.falls(c, "Spire Falls %d" % k, x2, y2, t2, b2, 3.0, 6.0, facing=1, throw=5.0, bulge=0.8, veils=2,
                        angle=a - math.pi / 2, mats=falls_mats)
    # The temple's front: three stepped tiers of mossy stone back into the south wall,
    # stairs up their middle, carved heads either side, braziers; the gateway at its foot.
    gx, gy = M.GATES["rainforest"]
    q, _ = c.nearest(gx, gy)
    ux, uy = gx - q.p.x, gy - q.p.y
    d = math.hypot(ux, uy)
    ux, uy = ux / d, uy / d
    rot = math.atan2(uy, ux)
    base = ground(gx, gy)
    for k in range(3):
        cx, cy = gx + ux * (10.0 + 6.0 * k), gy + uy * (10.0 + 6.0 * k)
        w = 16.0 - 3.5 * k
        box(c, "Temple Tier %d" % k, cx, cy, 5.0, w, base - 2.0, base + 4.0 * (k + 1), ("jungle_temple", "wall"), rot=rot)
        box(c, "Temple Frieze %d" % k, cx - ux * 5.05, cy - uy * 5.05, 0.06, w - 1.0, base + 4.0 * (k + 1) - 1.4,
            base + 4.0 * (k + 1) - 0.3, ("ruin_glyph", "wall"), rot=rot, role="visual")
    box(c, "Temple Shrine", gx + ux * 26.0, gy + uy * 26.0, 4.0, 4.5, base + 12.0, base + 18.0, ("ruin_stone", "wall"), rot=rot)
    box(c, "Temple Shrine Door", gx + ux * 21.95, gy + uy * 21.95, 0.06, 1.6, base + 12.0, base + 15.6, ("dark_corridor", "wall"),
        rot=rot, role="visual")
    for k in range(6):
        sx, sy = gx + ux * (5.6 + 1.0 * k), gy + uy * (5.6 + 1.0 * k)
        box(c, "Temple Step %d" % k, sx, sy, 0.5, 3.2, base - 1.0, base + 0.7 * (k + 1), ("ruin_stone", "wall"), rot=rot)
    for sd in (-1, 1):
        hx, hy = gx + ux * 3.0 - uy * sd * 9.0, gy + uy * 3.0 + ux * sd * 9.0
        c.place(idr.tiki_head(c, 0), hx, hy, ground(hx, hy) - 0.2, rot=rot + math.pi / 2, coll="Village", role="both")
        bx, by = gx + ux * 1.0 - uy * sd * 5.5, gy + uy * 1.0 + ux * sd * 5.5
        c.place(vp.brazier(c), bx, by, ground(bx, by) - 0.1, coll="Village", role="both")
        g = c.game(bx, by, ground(bx, by) + 1.9)
        c.entity("torch", x=g[0], y=g[1], z=g[2])
    taken.add(gx + ux * 14.0, gy + uy * 14.0, 20.0)
    taken.add(gx, gy, 8.0)
    # The jungle at its densest: giant trees, lianas between them, big leaves, ferns.
    trees = []

    def ok(x, y):
        return (M.pocket_at(x, y) == "heart" and M.wall_sd(x, y) < 10.0 and idr._dry(x, y, 3.0)
                and math.hypot(x - fx, y - fy) > M.POOL_R + 6.0 and idr._spread(ground, x, y, 1.5) < 2.5)

    for v in range(2):
        trees += pocket_scatter(c, props.jungle_tree(c, v), 9, ("heart",), ok, ground, taken, 300 + v, room=6.0, scale=(1.8, 2.6),
                                road_margin=7.0, trunk=(1.1, 8.0))
    for v in range(2):
        pocket_scatter(c, props.big_leaf_plant(c, v), 30, ("heart",), ok, ground, taken, 310 + v, room=2.5, role="visual")
    pocket_scatter(c, props.fern(c), 60, ("heart",), ok, ground, taken, 312, room=2.0, role="visual")
    # The old temple's ruins along the road through the basin: broken pillars, a fallen one;
    # shafts of sun down through the canopy.
    import impact_props as ip

    rnd = random.Random(31)
    np_ = 0
    for i in (31, 32, 33):
        for f in (0.25, 0.75):
            q = c.at(_route_s(c, i, f))
            for sd in (-1, 1):
                p = None
                for off in (4.5, 6.5, 8.5):
                    pp = q.side(sd * (q.w / 2 + off))
                    if clear_of(c, pp.x, pp.y, 2.0) and taken.clear(pp.x, pp.y, 1.4) and idr._dry(pp.x, pp.y, 1.5):
                        p = pp
                        break
                if p is None:
                    continue
                if math.hypot(p.x - fx, p.y - fy) < M.POOL_R + 3.0:
                    continue
                h = 3.0 + 6.0 * rnd.random()
                z = idr._lowest(ground, p.x, p.y, 1.2)
                box(c, "Ruin Pillar %d" % np_, p.x, p.y, 0.9, 0.9, z - 1.0, z + h, ("jungle_temple", "wall"), rot=rnd.random())
                box(c, "Ruin Pillar Cap %d" % np_, p.x, p.y, 1.15, 1.15, z + h, z + h + 0.5, ("ruin_stone", "wall"), rot=rnd.random(),
                    role="visual")
                taken.add(p.x, p.y, 2.0)
                np_ += 1
    for k, f in enumerate((0.2, 0.6)):
        for i in (31, 33):
            q = c.at(_route_s(c, i, f))
            ln = 50.0
            c.place(ip.sun_beam(c, length=ln, r=4.5, variant=k % 2), q.p.x - 0.34 * ln, q.p.y + 0.38 * ln, q.p.z + 0.86 * ln - 1.0,
                    role="visual")
    c.entity("area_ambient", area="rainforest", effect="fireflies", rate=26, radius=40)
    print("heart: falls top %.0f, %d giant trees, %d ruin pillars" % (top, len(trees), np_))


# ------------------------------------------------------------------ the Black Shore


def black_shore(c, ground, taken):
    """The north coast facing Volcano Isle: obsidian spires on the black sand either side behind
    the gateway, toward the volcano; obsidian and basalt along the shore, steam out of vents,
    braziers, burnt palms."""
    gx, gy = M.GATES["volcano"]
    q, _ = c.nearest(gx, gy)
    ux, uy = gx - q.p.x, gy - q.p.y
    d = math.hypot(ux, uy)
    ux, uy = ux / d, uy / d
    # (obsidian spires either side behind it, the gateway's own rock between them)
    for sd in (-1, 1):
        ax, ay = gx + ux * 7.0 - uy * sd * 11.0, gy + uy * 7.0 + ux * sd * 11.0
        if clear_of(c, ax, ay, 4.0):
            c.place(vp.obsidian_spire(c, (sd + 1) // 2), ax, ay, ground(ax, ay) - 0.5, rot=sd * 0.6, scale=0.45, coll="Village",
                    role="both")
            taken.add(ax, ay, 4.0)
    taken.add(gx, gy, 8.0)
    for sd in (-1, 1):
        bx, by = gx - uy * sd * 6.0, gy + ux * sd * 6.0
        c.place(vp.brazier(c), bx, by, ground(bx, by) - 0.1, coll="Village", role="both")
        g = c.game(bx, by, ground(bx, by) + 1.9)
        c.entity("torch", x=g[0], y=g[1], z=g[2])
        taken.add(bx, by, 1.5)

    def shore(x, y):
        return M.look_at(x, y) == "volcano" and idr._dry(x, y, 1.0) and M.wall_sd(x, y) < 6.0

    for v in range(2):
        pocket_scatter(c, vp.obsidian_cluster(c, v), 7, ("volcano",), shore, ground, taken, 330 + v, room=5.0, road_margin=4.0,
                       seat=2.0, reach=40.0)
        pocket_scatter(c, vp.burnt_palm(c, v), 6, ("volcano",), shore, ground, taken, 334 + v, room=5.0, road_margin=5.0,
                       trunk=(0.5, 6.0), reach=40.0)
    pocket_scatter(c, props.basalt_columns(c), 5, ("volcano",), shore, ground, taken, 336, room=7.0, road_margin=6.0, seat=3.0,
                   reach=40.0)
    rnd = random.Random(77)
    n = 0
    for _ in range(300):
        if n >= 9:
            break
        x, y = rnd.uniform(-60, 140), rnd.uniform(230, 330)
        if shore(x, y) and clear_of(c, x, y, 6.0) and taken.clear(x, y, 4.0):
            g = c.game(x, y, ground(x, y) + 0.5)
            c.entity("steam", x=g[0], y=g[1], z=g[2])
            taken.add(x, y, 4.0)
            n += 1
    # A jetty out over the black sand into the sea, two boats tied up at it.
    best = None
    for k in range(-6, 7):
        x, y = gx - uy * k * 8.0 + ux * 14.0, gy + ux * k * 8.0 + uy * 14.0
        if abs(k) > 2 and -2.0 < M.inland(x, y) < 6.0 and clear_of(c, x, y, 10.0) and taken.clear(x, y, 6.0):
            best = (x, y)
            break
    if best:
        x, y = best
        for j in range(8):
            px_, py_ = x + ux * j * 3.0, y + uy * j * 3.0
            box(c, "Shore Jetty %d" % j, px_, py_, 1.6, 1.8, WATER_Z + 1.0, WATER_Z + 1.25, ("wood_dock", "wall"),
                rot=math.atan2(uy, ux), role="visual")
            for sd in (-1, 1):
                box(c, "Shore Jetty Post %d %d" % (j, sd), px_ - uy * sd * 1.5, py_ + ux * sd * 1.5, 0.15, 0.15, WATER_Z - 2.0,
                    WATER_Z + 1.6, ("cove_post", "wall"), role="visual")
        for j, sd in enumerate((-1, 1)):
            bx, by = x + ux * 18.0 - uy * sd * 5.0, y + uy * 18.0 + ux * sd * 5.0
            if M.inland(bx, by) < -2.0:
                c.place(tp.rowboat(c), bx, by, WATER_Z + 0.1, rot=math.atan2(uy, ux) + 0.2 * sd, coll="Village", role="visual")
        taken.add(x + ux * 12.0, y + uy * 12.0, 14.0)
    c.entity("area_ambient", area="volcano", effect="ashfall", rate=14, radius=50)
    print("black shore: %d vents, jetty %s" % (n, bool(best)))


# ------------------------------------------------------------------ the Cloud Forest, the Gorge


def cloud_forest(c, ground, taken):
    """The giant trees of the cloud forest along the Ridge Road and down it, lianas slung
    between them, mossy boulders."""
    looks = ("cloud", "ridge", "north")

    def ok(x, y):
        return (M.look_at(x, y) in looks and M.wall_sd(x, y) < 12.0 and idr._dry(x, y, 2.0)
                and idr._spread(ground, x, y, 1.5) < 2.5)

    placed = []
    for v in range(2):
        placed += pocket_scatter(c, props.jungle_tree(c, v), 16, looks, ok, ground, taken, 340 + v, room=7.0, scale=(2.0, 2.8),
                                 road_margin=6.0, trunk=(1.2, 8.0))
    for v in range(2):
        pocket_scatter(c, props.boulder(c, "jungle_mossstone", v), 12, looks, ok, ground, taken, 344 + v, room=4.0, road_margin=3.0,
                       seat=2.0)
    # The mist the forest's named for (Blake, Nov 2): banks of it lying in the ravine,
    # thin at the road, thicker up the walls, a layer over the treetops.
    nm = 0
    for p in M.POCKETS:
        if p[0] != "cloud":
            continue
        for k, (cx, cy, r, _f) in enumerate(p[2]):
            z0 = ground(cx, cy)
            for j, (dz, rr) in enumerate(((1.4, r + 4.0), (7.0, r + 12.0), (15.0, r + 22.0))):
                c.disc("Cloud Mist %d %d" % (k, j), cx + 3.0 * math.sin(k + j), cy + 3.0 * math.cos(k * 2 + j), rr, z0 + dz,
                       c.lib("cloud_mist"), coll="Mist", role="visual", n=18, wobble=0.3, seed=k * 7 + j)
                nm += 1
    import impact_props as ip

    for k, (i, f) in enumerate(((14, 0.5), (15, 0.5), (16, 0.4), (9, 0.5), (39, 0.4))):
        q = c.at(_route_s(c, i, f))
        ln = 50.0
        c.place(ip.sun_beam(c, length=ln, r=4.0, variant=k % 2), q.p.x - 0.34 * ln, q.p.y + 0.38 * ln, q.p.z + 0.86 * ln - 1.0,
                role="visual")
    print("cloud forest: %d giant trees, %d mist banks" % (len(placed), nm))


def gorge(c, ground, taken, falls_mats):
    """The river's gorge: boulders in the river, two thin falls off its walls, ferns."""
    n = 0
    for (ax, ay, az), (bx, by, bz) in zip(M.RIVER, M.RIVER[1:]):
        for t in (0.3, 0.7):
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            if clear_of(c, x, y, 5.0):
                c.place(props.boulder(c, "jungle_mossstone", n % 2), x + 2.0 * (n % 2 - 0.5), y, az - 1.2, rot=n, scale=1.3,
                        coll="Props", role="visual")
                n += 1
    k = 0
    for i in (1, 3):
        (ax, ay, az), (bx, by, bz) = M.RIVER[i], M.RIVER[i + 1]
        tx, ty = bx - ax, by - ay
        L = math.hypot(tx, ty)
        nx, ny = ty / L, -tx / L  # (the river's right bank: away from the road)
        for off in (18.0, 22.0, 26.0, 30.0, 35.0, 40.0):
            x, y = (ax + bx) / 2 + nx * off, (ay + by) / 2 + ny * off
            top = M.natural(x, y)
            if top - az > 10.0 and clear_of(c, x, y, 4.0):
                props.falls(c, "Gorge Falls %d" % k, x, y, top - 0.8, (az + bz) / 2, 2.2, 4.0, facing=1, throw=2.5, bulge=0.6, veils=2,
                            angle=math.atan2(-ny, -nx) - math.pi / 2, mats=falls_mats)
                k += 1
                break
    print("gorge: %d boulders, %d side falls" % (n, k))


def lagoon(c, ground, taken):
    """Mangroves round the lagoon's shore and out in its shallows, the fishers' canoes."""
    mangroves = [hp_.mangrove(c, v, height=6.5 + 1.5 * v) for v in range(3)]
    lx, ly, lr = M.LAGOON
    rnd = random.Random(53)
    n = 0
    for _ in range(500):
        if n >= 30:
            break
        a = rnd.uniform(0, math.tau)
        d = lr + rnd.uniform(-14.0, 10.0)
        x, y = lx + d * math.cos(a), ly + d * math.sin(a)
        if not clear_of(c, x, y, 6.0) or not taken.clear(x, y, 4.5) or M.inland(x, y) < 4.0:
            continue
        z = min(ground(x, y), 0.4)
        c.place(mangroves[n % 3], x, y, max(M.LAGOON_Z, z), rot=a * 2.0, scale=0.9 + 0.3 * rnd.random(), role="visual")
        c.place(paint.trunk_proto(c, 0.5, 5.0), x, y, max(M.LAGOON_Z, z) - 0.5, coll="Collision", role="collision")
        taken.add(x, y, 4.5)
        n += 1
    for j in range(3):
        a = 1.2 + 0.5 * j
        x, y = lx + (lr - 6.0) * math.cos(a), ly + (lr - 6.0) * math.sin(a)
        if clear_of(c, x, y, 4.0):
            c.place(bp.canoe(c, j % 2), x, y, M.LAGOON_Z + 0.1, rot=a, coll="Village", role="visual")
    # The lagoon fishers' houses on their stilts out over the water, off its south shore.
    ns = 0
    for j, a in enumerate((-1.2, -1.75, -2.3)):
        x, y = lx + (lr - 14.0) * math.cos(a), ly + (lr - 14.0) * math.sin(a)
        if clear_of(c, x, y, 8.0) and M.natural(x, y) < M.LAGOON_Z - 0.4:
            c.place(hp_.stilt_house(c, j), x, y, M.LAGOON_Z, rot=math.atan2(ly - y, lx - x) + math.pi / 2, coll="Village")
            taken.add(x, y, 6.0)
            ns += 1
    print("lagoon: %d mangroves, %d stilt houses" % (n, ns))


# ------------------------------------------------------------------ the Head Pass, the camps


def head_pass(c, ground, taken):
    """The Head Pass: old Tidewyrm's bones, a sea serpent's ribs arching over the road
    where it squeezes between the Head and the mountain (the islanders say it's his
    grandfather's)."""
    import dcanyon_props as dcp

    s0 = _route_s(c, 2, 0.1)
    s1 = _route_s(c, 3, 0.2)
    n = 0
    s = s0
    while s < s1 and n < 6:
        q = c.at(s)
        feet = [q.side(sd * 13.0) for sd in (-1, 1)]
        c.place(dcp.rib(c, span=26.0, height=17.0 - 1.2 * abs(n - 2.5), variant=n % 3), q.p.x, q.p.y, q.p.z - 1.0,
                rot=math.atan2(q.t.y, q.t.x) - math.pi / 2, role="visual")
        for f in feet:
            c.place(paint.trunk_proto(c, 0.9, 5.0), f.x, f.y, ground(f.x, f.y) - 0.5, coll="Collision", role="collision")
            taken.add(f.x, f.y, 2.0)
        n += 1
        s += 9.0
    print("head pass: %d ribs" % n)


def fishing_camp(c, ground, taken, ter):
    """On the north-east coast: the fishers' camp on the beach, drying racks, nets of
    lobster pots, canoes drawn up, a beach hut graded level, its fire."""
    q = c.at(_route_s(c, 44, 0.5))
    sea = 1 if M.inland(*q.side(30.0).xy) < M.inland(*q.side(-30.0).xy) else -1
    cx, cy = q.side(sea * (q.w / 2 + 18.0)).xy
    if not idr._dry(cx, cy, 6.0) or not taken.clear(cx, cy, 10.0):
        print("fishing camp: no room")
        return
    rot = math.atan2(q.p.y - cy, q.p.x - cx)
    z = idr._seat(c, ground, ter, cx, cy, rot, 6.0, 6.0)
    c.place(tp.beach_hut(c, 1), cx, cy, z - 0.1, rot=rot + math.pi / 2, coll="Village", role="both")
    taken.add(cx, cy, 6.0)
    n = 0
    for k, (u, v) in enumerate(((7.0, 4.0), (7.0, -4.0), (-6.0, 7.0), (-6.0, -7.0), (10.0, 0.0))):
        x = cx + u * math.cos(rot) - v * math.sin(rot)
        y = cy + u * math.sin(rot) + v * math.cos(rot)
        if not idr._dry(x, y, 1.5) or not clear_of(c, x, y, 3.0) or not taken.clear(x, y, 2.0):
            continue
        proto = (hp_.drying_rack(c, 0), hp_.drying_rack(c, 0), hp_.lobster_pots(c), bp.canoe(c, 1), hp_.lobster_pots(c))[k]
        c.place(proto, x, y, idr._lowest(ground, x, y, 1.0) - 0.05, rot=rot + k, coll="Village", role="both" if k < 2 else "visual")
        taken.add(x, y, 2.0)
        n += 1
    fx, fy = cx + 4.0 * math.cos(rot + 1.2), cy + 4.0 * math.sin(rot + 1.2)
    g = c.game(fx, fy, ground(fx, fy) + 0.2)
    c.entity("campfire", x=g[0], y=g[1], z=g[2])
    g = c.game(cx, cy, z)
    c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=9.0, n=3, folk="beach", heading=0.0)
    print("fishing camp: %d things" % n)


def valley_hamlet(c, ground, taken, ter):
    """The North Valley's growers: two huts graded level by the road, their banana and taro
    plants round them, the folk."""
    n = 0
    for i in (37, 38, 39):
        for f in (0.3, 0.7):
            if n >= 2:
                break
            q0 = c.at(_route_s(c, i, f))
            for sd in (-1, 1):
                for off in (8.0, 10.0, 12.0, 14.0, 16.0):
                    p = q0.side(sd * (q0.w / 2 + off))
                    if (taken.clear(p.x, p.y, 6.0) and clear_of(c, p.x, p.y, 5.5) and idr._spread(ground, p.x, p.y, 3.5) < 3.5
                            and M.wall_sd(p.x, p.y) < 10.0):
                        break
                else:
                    continue
                rot = math.atan2(q0.p.y - p.y, q0.p.x - p.x)
                z = idr._seat(c, ground, ter, p.x, p.y, rot, 6.0, 6.0)
                c.place(tp.beach_hut(c, 2 + (sd > 0)), p.x, p.y, z - 0.1, rot=rot + math.pi / 2, coll="Village", role="both")
                taken.add(p.x, p.y, 7.0)
                for k in range(6):
                    a = rot + math.pi + (k - 2.5) * 0.45
                    x, y = p.x + 8.0 * math.cos(a), p.y + 8.0 * math.sin(a)
                    if clear_of(c, x, y, 2.0) and taken.clear(x, y, 2.0) and idr._dry(x, y, 1.0):
                        c.place(props.big_leaf_plant(c, k % 2), x, y, ground(x, y) - 0.1, rot=k, scale=1.3, role="visual")
                        taken.add(x, y, 2.0)
                g = c.game(p.x, p.y, z)
                c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=8.0, n=2, folk="beach", heading=0.0)
                n += 1
                break
    print("valley hamlet: %d huts" % n)
