# Rainforest Rush: the Tropic Isles' fourth course (it replaces Splash Lagoon: Blake, Nov 1,
# "I dont like splash lagoon. it reminds me of a cheap water park ... maybe this becomes a
# super fast island tropical jungle course ... think tropical jungle rainforest vibe").
# The island's rainforest heart: the old temple, the giant trees, the falls, the gorge.
# The lap: rainforest_layout.py.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/rainforest_rush.py       (the bpy module)
#   python tools/blender/prehistoric/rainforest_rush_ruins.py (its ruin)

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import ruin_mode  # noqa: E402
from course_kit import Vector, bmesh, lerp  # noqa: E402
import pocket_build as pb  # noqa: E402
from pocket_build import box  # noqa: E402
import props  # noqa: E402
import beach_props as bp  # noqa: E402
import tropic_props as tp  # noqa: E402
import volcano_props as vp  # noqa: E402
import region_paint as paint  # noqa: E402
import rainforest_layout as R  # noqa: E402

RUIN = ruin_mode.ON
TRACK_ID = "rainforest_rush_ruin" if RUIN else "rainforest_rush"
L = R.L

ROAD = "isle_jungle_road"
LOOK = {
    # look: (ground, cliff, road, shoulder)
    "temple": (("jungle_leafcover", "grass"), ("jungle_temple", "wall"), "rain_paving", ("jungle_leafcover", "grass")),
    "canopy": (("jungle_leafcover", "grass"), ("jungle_mossstone", "wall"), ROAD, ("jungle_leafcover", "grass")),
    "river": (("isle_jungle", "grass"), ("canyon_rock_moss", "wall"), ROAD, ("isle_jungle", "grass")),
    "gorge": (("isle_jungle", "grass"), ("canyon_rock_moss", "wall"), ROAD, ("isle_jungle", "grass")),
    "hollow": (("jungle_leafcover", "grass"), ("jungle_mossstone", "wall"), ROAD, ("jungle_leafcover", "grass")),
    "kapok": (("isle_jungle", "grass"), ("jungle_mossstone", "wall"), ROAD, ("isle_jungle", "grass")),
    "avenue": (("jungle_leafcover", "grass"), ("jungle_mossstone", "wall"), ROAD, ("jungle_leafcover", "grass")),
    "ruins": (("isle_jungle", "grass"), ("jungle_temple", "wall"), "rain_paving", ("isle_jungle", "grass")),
}
FALLS_MATS = ("falls_oasis", "falls_curtain_oasis", "falls_foam")
FIRES = []


def natural(x, y):
    h = R.natural(x, y)
    tz = R.tunnel_floor(x, y)
    if tz is not None:
        h = min(h, tz - 0.25)
    return h


def classify(c, n, info):
    look = R.look_at(c.x, c.y)
    if n.z < 0.62:
        return LOOK[look][1] if L.wall_sd(c.x, c.y) < 24.0 else ("jungle_mossstone", "wall")
    if c.z < 1.0 and min(abs(c.x - p[0]) for p in R.GORGE_RIVER) < 30.0:
        return ("lagoon_shallow", "water")
    d, wz = L.water_d(c.x, c.y)
    if d < R.RIVER_HW + 2 and c.z < wz + 0.3:
        return ("lagoon_shallow", "water")
    if n.z < 0.85:
        return ("jungle_mossstone", "dirt")
    if L.wall_sd(c.x, c.y) < 2.0:
        return pb.transition(L.look_weights(c.x, c.y), lambda lk: LOOK[lk][0])
    return ("isle_jungle", "grass") if math.sin(c.x / 17.0) * math.cos(c.y / 21.0) < 0.4 else ("jungle_leafcover", "grass")


def _s(c, i, f=0.0):
    (ax, ay, _), (bx, by, _) = R.ROUTE[i], R.ROUTE[(i + 1) % len(R.ROUTE)]
    return c.nearest(ax + (bx - ax) * f, ay + (by - ay) * f)[0].s


def main():
    c = kit.Course(TRACK_ID, "Rainforest Rush (Ruined)" if RUIN else "Rainforest Rush", "rainforest_ruins" if RUIN else "rainforest_rush")
    c.route(R.route_points(), width=R.WIDTH, bank=6.0)
    kinds = {}
    for look, (ground, cliff, road, shoulder) in LOOK.items():
        kinds[look] = {"mat": road, "shoulder": 1.6, "shoulder_mat": shoulder}
    kinds["bridge"] = {"mat": "plank_deck", "surface": "road", "shoulder": 0.6, "shoulder_mat": ("plank_deck", "road"),
                       "barrier": 1.1, "barrier_mat": ("rope_rail", "wall"), "deck": 2.2, "deck_mat": ("weathered_timber", "wall"),
                       "ground": False}
    kinds["log"] = {"mat": "giant_heartwood", "surface": "road", "shoulder": 1.0, "shoulder_mat": ("giant_bark", "road")}
    c.kinds = kinds
    b0 = _s(c, R.BRIDGE[0] - 1, 0.55)
    b1 = _s(c, R.BRIDGE[1], 0.45)
    l0 = _s(c, R.LOG[0], 0.15)
    l1 = _s(c, R.LOG[0], 0.85)

    def label(q):
        if b0 <= q.s <= b1:
            return "bridge"
        if l0 <= q.s <= l1:
            return "log"
        return R.look_at(q.p.x, q.p.y)

    runs = list(kit.runs(c, label))
    c.roads(kit.plan(c, pb.blend_runs(c, runs, LOOK), "temple", max_len=150.0))

    X0, X1, Y0, Y1 = -262, 262, -262, 262
    ter = c.terrain("Rainforest", X0, X1, Y0, Y1, 2.5, natural, classify, near=9.0, fade=14.0, verge_fill=1.5)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 5.0, lambda x, y: natural(x, y) - 0.5, c.lib("jungle_leafcover", "grass"))

    def ground(x, y):
        z = c.ground_z(x, y, [ter])
        return natural(x, y) if z is None else z

    taken = paint.Taken([(R.KAPOK[0], R.KAPOK[1], 16.0), (R.PYRAMID[0], R.PYRAMID[1], 14.0), (R.TEMPLE[0], R.TEMPLE[1], 26.0)])
    water(c)
    falls_cave(c, ground, taken)
    rope_bridge(c, ground, (b0, b1))
    hollow_log(c, ground, (l0, l1))
    kapok(c, ground, taken)
    pyramid(c, ground, taken)
    temple(c, ground, taken)
    jungle(c, ground, taken)

    c.start_line()
    for i, f, across in R.ZIPPERS:
        c.zipper(_s(c, i, f), across)
    for i, f, across in ((3, 0.5, 0.0), (9, 0.5, -3.0), (17, 0.5, 0.0), (25, 0.4, 3.0), (31, 0.5, 0.0)):
        c.bananas(_s(c, i, f), across, count=5, gap=2.6)
    for i, f, across, col in ((1, 0.5, -4, "red"), (1, 0.5, 4, "blue"), (7, 0.5, 0, "green"), (12, 0.5, 0, "yellow"),
                              (22, 0.5, 0, "rainbow"), (28, 0.6, 0, "red")):
        c.balloon(_s(c, i, f), across, col)
    c.checkpoints(avoid=[(b0 + 2.0, b1 - 2.0)], height=10.0)
    if RUIN:
        ruin_mode.DRESS(c, sys.modules[__name__], ground)
    c.finish()
    print("lap", round(c.length, 1))


# ------------------------------------------------------------------ the water


def water(c):
    """The river down the valley beside the River Run; the gorge's river far under the
    bridge; the great falls."""
    for name, riv, hw in (("River", R.RIVER, R.RIVER_HW), ("Gorge River", R.GORGE_RIVER, 12.0)):
        strip = []
        for (ax, ay, az), (bx, by, bz) in zip(riv, riv[1:]):
            n = max(1, int(math.hypot(bx - ax, by - ay) / 5))
            for k in range(n):
                t = k / n
                strip.append((lerp(ax, bx, t), lerp(ay, by, t), hw * 2 + 3.0, lerp(az, bz, t)))
        strip.append((riv[-1][0], riv[-1][1], hw * 2 + 3.0, riv[-1][2]))
        c.ribbon(name, strip, hw * 2 + 3.0, 0, c.lib("lagoon_shallow", "water"), role="visual", steps=3)


def falls_cave(c, ground, taken):
    """The Falls Cave: bored through the valley's north wall, the great falls coming down
    the cliff beside its mouth into the river's head, moss and roots round the bore."""
    name, kind, a, b = R.TUNNELS[0]
    s0, s1 = pb.tunnel_span(c, L, a, b)
    half = pb.bore(c, L, name, s0, s1, ("canyon_rock_moss", "wall"), ("isle_jungle", "grass"), height=11.0)
    for s in (s0 + 4.0, (s0 + s1) / 2, s1 - 4.0):
        q = c.at(s)
        for sd in (-1, 1):
            p = q.side(sd * (half - 0.6))
            g = c.game(p.x, p.y, q.p.z + 4.5)
            c.entity("torch", x=g[0], y=g[1], z=g[2])
    fx, fy = R.FALLS
    top = natural(fx, fy + 16.0) - 1.0
    wz = R.RIVER[0][2]
    if top - wz > 12.0:
        props.falls(c, "Great Falls", fx, fy + 12.0, top, wz, 10.0, 16.0, facing=-1, throw=7.0, bulge=1.6, veils=4, mats=FALLS_MATS)
        g = c.game(fx, fy, wz)
        c.entity("waterfall", x=g[0], y=g[1], z=g[2], top=round(top - wz, 1), width=16.0, heading=0.0)
    taken.add(fx, fy, 14.0)
    print("falls cave: %.0f m, falls top %.0f" % (s1 - s0, top))


# ------------------------------------------------------------------ the pieces


def _tube_ob(c, name, pts, radii, mat, role="visual", n=8):
    bm = bmesh.new()
    props.tube(bm, pts, radii, n=n)
    ob = c.mesh_object(name, bm, "Props", role)
    c.assign(ob, c.lib(*mat))
    return ob


def rope_bridge(c, ground, span):
    """Timber towers at both ends, the cables slung between them, hangers, vines."""
    s0, s1 = span
    tops = {}
    for s, k in ((s0, 0), (s1, 1)):
        q = c.at(s)
        for sd in (-1, 1):
            p = q.side(sd * (q.w / 2 + 1.6))
            z0 = min(ground(p.x, p.y), q.p.z) - 2.0
            for lean in (-1, 1):
                _tube_ob(c, "Bridge Pylon %d %d %d" % (k, sd, lean), [(p.x + q.t.x * lean * 1.8, p.y + q.t.y * lean * 1.8, z0),
                                                                       (p.x, p.y, q.p.z + 9.0)], [0.5, 0.4], ("weathered_timber", "wall"),
                         role="both")
            g = c.game(p.x, p.y, q.p.z + 9.6)
            c.entity("torch", x=g[0], y=g[1], z=g[2])
            tops[k, sd] = (p.x, p.y, q.p.z + 9.0)
    L_ = s1 - s0
    for sd in (-1, 1):
        a, b = Vector(tops[0, sd]), Vector(tops[1, sd])
        pts = []
        for k in range(13):
            t = k / 12
            p = a.lerp(b, t)
            p.z -= 7.0 * 4 * t * (1 - t)
            pts.append(tuple(p))
        _tube_ob(c, "Bridge Cable %d" % sd, pts, 0.16, ("rope_rail", "wall"), n=5)
        n = max(2, int(L_ / 4.5))
        for j in range(1, n):
            t = j / n
            q = c.at(s0 + L_ * t)
            p = q.side(sd * (q.w / 2 + 1.0))
            cz = a.z + (b.z - a.z) * t - 7.0 * 4 * t * (1 - t)
            if cz > q.p.z + 1.6:
                _tube_ob(c, "Bridge Hanger %d %d" % (sd, j), [(p.x, p.y, cz), (p.x, p.y, q.p.z + 1.1)], 0.05, ("rope_rail", "wall"),
                         n=4)
        for j in range(4):
            q = c.at(s0 + L_ * (0.2 + 0.2 * j))
            p = q.side(sd * (q.w / 2 + 1.3))
            _tube_ob(c, "Bridge Vine %d %d" % (sd, j), [(p.x, p.y, q.p.z), (p.x + 0.3, p.y, q.p.z - 5.0 - 2.0 * (j % 2))], [0.14, 0.08],
                     ("vine_leaf", "wall"), n=5)
    print("rope bridge: %.0f m" % L_)


def hollow_log(c, ground, span):
    """A colossal fallen tree the road runs through: its hollow trunk a tunnel of bark (its
    walls solid), the heartwood its floor; broken branches off it, moss and ferns on it."""
    s0, s1 = span
    n = 14
    hw, hh = 11.5, 13.0  # (the hollow's half width, its height over the road)
    bm = bmesh.new()
    rings = []
    for k in range(n + 1):
        q = c.at(s0 + (s1 - s0) * k / n)
        wob = 1.0 + 0.04 * math.sin(k * 1.7)
        ring = []
        for j in range(17):
            a = math.pi * j / 16  # (round the top, from the right side over to the left)
            x_ = math.cos(a) * hw * wob
            z_ = math.sin(a) * hh * wob
            ring.append(bm.verts.new(q.p + q.r * x_ + Vector((0, 0, z_ - 0.2))))
        # (down into the ground both sides)
        ring.insert(0, bm.verts.new(q.p + q.r * hw * wob + Vector((0, 0, -3.0))))
        ring.append(bm.verts.new(q.p - q.r * hw * wob + Vector((0, 0, -3.0))))
        rings.append(ring)
    for ra, rb in zip(rings, rings[1:]):
        for i in range(len(ra) - 1):
            bm.faces.new((ra[i], rb[i], rb[i + 1], ra[i + 1]))
    # (its outside, a little bigger: the bark's thickness)
    ob = c.mesh_object("Hollow Log", bm, "Props", "visual")
    c.assign(ob, c.lib("giant_bark", "wall"))
    # Its walls a kart hits: the sides, up from the road to the springing.
    bm = bmesh.new()
    for sd in (-1, 1):
        rs = []
        for k in range(n + 1):
            q = c.at(s0 + (s1 - s0) * k / n)
            rs.append([bm.verts.new(q.p + q.r * sd * (hw - 0.4) + Vector((0, 0, dz))) for dz in (-1.0, 6.0)])
        for a, b in zip(rs, rs[1:]):
            bm.faces.new((a[0], b[0], b[1], a[1]))
    c.assign(c.mesh_object("Hollow Log Walls", bm, "Props", "collision"), c.lib("giant_bark", "wall"))
    # The rim of each open end: a ring of jagged bark.
    for s in (s0, s1):
        q = c.at(s)
        pts = []
        for j in range(17):
            a = math.pi * j / 16
            pts.append(tuple(q.p + q.r * math.cos(a) * (hw + 0.6) + Vector((0, 0, math.sin(a) * (hh + 0.6) - 0.2))))
        _tube_ob(c, "Log Rim %d" % int(s), pts, [1.2 + 0.3 * math.sin(j * 2.1) for j in range(17)], ("giant_bark", "wall"), n=6)
    # Branches broken off it, roots at its end.
    q = c.at(s0 + (s1 - s0) * 0.35)
    for sd, ln, up in ((1, 12.0, 9.0), (-1, 9.0, 12.0)):
        base = q.p + q.r * sd * (hw - 1.0) + Vector((0, 0, hh * 0.6))
        tip = base + q.r * sd * ln + Vector((0, 0, up))
        _tube_ob(c, "Log Branch %d" % sd, [tuple(base), tuple(base.lerp(tip, 0.5)), tuple(tip)], [1.6, 1.1, 0.5], ("giant_bark", "wall"))
    q = c.at(s1)
    for j in range(7):
        a = j * math.pi / 6
        base = q.p + q.r * math.cos(a) * hw * 0.8 + Vector((0, 0, math.sin(a) * hh * 0.8))
        tip = base + q.t * (8.0 + 3.0 * (j % 2)) + q.r * math.cos(a) * 4.0 + Vector((0, 0, math.sin(a) * 3.0 - 2.0))
        _tube_ob(c, "Log Root %d" % j, [tuple(base), tuple(tip)], [1.0, 0.25], ("giant_bark", "wall"), n=6)
    # Moss and ferns along its top.
    for k in range(1, n, 2):
        q = c.at(s0 + (s1 - s0) * k / n)
        p = q.p + Vector((0, 0, hh - 0.2))
        c.place(props.fern(c), p.x + q.r.x * 2.0, p.y + q.r.y * 2.0, p.z, rot=k, scale=1.6, role="visual")
    print("hollow log: %.0f m" % (s1 - s0))


def kapok(c, ground, taken):
    """The colossal kapok the hairpin turns round: a trunk 10 m across, buttress roots out
    from it like walls, its crown up over everything."""
    x, y = R.KAPOK
    z = ground(x, y) - 1.0
    _tube_ob(c, "Kapok Trunk", [(x, y, z - 2.0), (x, y, z + 20.0), (x + 0.6, y, z + 46.0), (x + 1.0, y, z + 62.0)],
             [5.4, 4.2, 3.4, 2.6], ("giant_bark", "wall"), role="both", n=14)
    for j in range(7):
        a = j * math.tau / 7 + 0.3
        bm = bmesh.new()
        ca, sa = math.cos(a), math.sin(a)
        pts = [(x + ca * 4.0, y + sa * 4.0, z + 12.0), (x + ca * 9.0, y + sa * 9.0, z + 3.0), (x + ca * 12.5, y + sa * 12.5, z - 1.0)]
        props.tube(bm, pts, [1.4, 0.9, 0.5], n=6)
        # (each buttress a blade: squashed across)
        for v in bm.verts:
            dx, dy = v.co.x - x, v.co.y - y
            along = dx * ca + dy * sa
            across = -dx * sa + dy * ca
            across *= 0.35
            v.co.x, v.co.y = x + along * ca - across * sa, y + along * sa + across * ca
        ob = c.mesh_object("Kapok Buttress %d" % j, bm, "Props", "both")
        c.assign(ob, c.lib("giant_bark", "wall"))
    for k, (dx, dy, dz, s) in enumerate(((0, 0, 58, 3.4), (12, 6, 50, 2.6), (-10, 8, 52, 2.6), (4, -12, 48, 2.4), (-6, -8, 56, 2.2))):
        c.place(props.jungle_tree(c, k % 2), x + dx, y + dy, z + dz - 20.0 * s / 3.4, rot=k * 1.3, scale=s, role="visual")
    taken.add(x, y, 16.0)
    print("kapok at (%.0f, %.0f)" % (x, y))


def pyramid(c, ground, taken):
    """The fallen pyramid inside the Ruins Hairpin: four stepped tiers of mossy temple
    stone, its top tier slid off and lying broken at its foot, a stone head half sunk."""
    x, y = R.PYRAMID
    z = ground(x, y)
    for k in range(4):
        r = 11.0 - 2.6 * k
        box(c, "Pyramid Tier %d" % k, x, y, r, r, z - 2.0, z + 3.5 * (k + 1), ("jungle_temple", "wall"), rot=0.3)
        box(c, "Pyramid Frieze %d" % k, x, y, r + 0.05, r + 0.05, z + 3.5 * (k + 1) - 1.2, z + 3.5 * (k + 1) - 0.4,
            ("ruin_glyph", "wall"), rot=0.3, role="visual")
    box(c, "Pyramid Top", x + 8.0, y - 6.0, 2.8, 2.8, z - 1.0, z + 3.0, ("jungle_temple", "wall"), rot=0.9)
    taken.add(x, y, 14.0)


def temple(c, ground, taken):
    """The old temple behind the start: its stepped front south of the paving, stairs up
    its middle, carved heads and braziers either side; the temple's gate over the road
    into the paving (its pillars, the lintel, glyphs)."""
    tx, ty = R.TEMPLE
    z = ground(tx, ty)
    for k in range(4):
        box(c, "Temple Tier %d" % k, tx, ty - 4.0 * k, 26.0 - 4.5 * k, 8.0, z - 2.0, z + 5.0 * (k + 1), ("jungle_temple", "wall"))
        box(c, "Temple Frieze %d" % k, tx, ty - 4.0 * k + 8.05, 26.0 - 4.5 * k - 1.0, 0.06, z + 5.0 * (k + 1) - 1.6,
            z + 5.0 * (k + 1) - 0.4, ("ruin_glyph", "wall"), role="visual")
    box(c, "Temple Shrine", tx, ty - 16.0, 6.0, 5.0, z + 20.0, z + 28.0, ("ruin_stone", "wall"))
    for k in range(8):
        box(c, "Temple Stair %d" % k, tx, ty + 9.0 - 1.1 * k, 3.6, 0.6, z - 1.0, z + 0.8 * (k + 1), ("ruin_stone", "wall"))
    for sd in (-1, 1):
        hx, hy = tx + sd * 8.0, ty + 11.0
        c.place(vp.brazier(c), hx, hy, ground(hx, hy) - 0.1, coll="Village", role="both")
        g = c.game(hx, hy, ground(hx, hy) + 1.9)
        c.entity("torch", x=g[0], y=g[1], z=g[2])
    # The gate over the road into the paving.
    q = c.at(_s(c, 33, 0.4))
    rot = math.atan2(q.t.y, q.t.x)
    for sd in (-1, 1):
        p = q.side(sd * (q.w / 2 + 2.6))
        box(c, "Temple Gate Pillar %d" % sd, p.x, p.y, 1.4, 1.4, q.p.z - 2.0, q.p.z + 12.0, ("jungle_temple", "wall"), rot=rot)
        g = c.game(p.x - q.t.x * 1.6, p.y - q.t.y * 1.6, q.p.z + 6.0)
        c.entity("torch", x=g[0], y=g[1], z=g[2])
        taken.add(p.x, p.y, 3.0)
    box(c, "Temple Gate Lintel", q.p.x, q.p.y, 2.0, q.w / 2 + 4.6, q.p.z + 12.0, q.p.z + 14.6, ("jungle_temple", "wall"),
        rot=rot + math.pi / 2, role="visual")
    box(c, "Temple Gate Glyphs", q.p.x - q.t.x * 2.05, q.p.y - q.t.y * 2.05, 0.06, q.w / 2 + 3.0, q.p.z + 12.4, q.p.z + 14.2,
        ("ruin_glyph", "wall"), rot=rot + math.pi / 2, role="visual")
    taken.add(tx, ty, 26.0)


def jungle(c, ground, taken):
    """The rainforest: giant trees close by the road, palms, bushes, big leaves, ferns;
    lianas slung from tree to tree over the road; torches along the way."""
    g = ground

    def floor(x, y):
        d, wz = L.water_d(x, y)
        return L.wall_sd(x, y) < 14.0 and d > R.RIVER_HW + 2 and min(abs(x - p[0]) for p in R.GORGE_RIVER) > 26.0

    trees = []
    for v in range(2):
        trees += paint.scatter(c, props.jungle_tree(c, v), 70, 262.0, floor, g, taken, 20 + v, room=6.0, scale=(1.6, 2.6),
                               road_margin=5.0, trunk=(1.0, 8.0))
        paint.scatter(c, bp.coconut_palm(c, v), 30, 262.0, floor, g, taken, 24 + v, room=5.0, road_margin=4.0, trunk=(0.5, 8.0))
        paint.scatter(c, props.bush(c, v), 120, 262.0, floor, g, taken, 30 + v, room=2.5, road_margin=2.0, role="visual")
        paint.scatter(c, props.big_leaf_plant(c, v), 110, 262.0, floor, g, taken, 33 + v, room=2.5, road_margin=2.0, role="visual")
    paint.scatter(c, props.fern(c), 240, 262.0, floor, g, taken, 35, room=2.0, road_margin=1.5, role="visual")
    # (up on the walls' shelves and the high ground: the forest goes on out of sight)
    for v in range(2):
        paint.scatter(c, props.jungle_tree(c, v), 140, 262.0, lambda x, y: L.wall_sd(x, y) >= 14.0, g, taken, 40 + v, room=8.0,
                      scale=(1.4, 2.4), road_margin=8.0, role="visual")
    # Lianas from tree to tree over the road.
    rnd = random.Random(7)
    nl = 0
    for k in range(0, int(c.length), 45):
        q = c.at(float(k))
        a, b = q.side(q.w / 2 + 5.0), q.side(-(q.w / 2 + 5.0))
        za, zb = g(a.x, a.y) + 14.0 + 3.0 * rnd.random(), g(b.x, b.y) + 14.0 + 3.0 * rnd.random()
        if min(za, zb) < q.p.z + 9.0:
            continue
        props.liana(c, "Liana %d" % k, (a.x, a.y, za), (b.x, b.y, zb), sag=3.0 + 2.0 * rnd.random())
        nl += 1
    torch = bp.tiki_torch(c, 0)
    nt = 0
    for k in range(10, int(c.length), 36):
        q = c.at(float(k))
        sd = 1 if (k // 36) % 2 else -1
        p = q.side(sd * (q.w / 2 + 2.4))
        if paint.road_clear(c, p.x, p.y, 1.0) and taken.clear(p.x, p.y, 0.5):
            zt = g(p.x, p.y)
            c.place(torch, p.x, p.y, zt, coll="Props", role="both")
            gg = c.game(p.x, p.y, zt + 2.6)
            c.entity("torch", x=gg[0], y=gg[1], z=gg[2])
            taken.add(p.x, p.y, 0.6)
            nt += 1
    c.entity("fireflies", rate=24, radius=40)
    print("jungle: %d trees, %d lianas, %d torches" % (len(trees), nl, nt))


if __name__ == "__main__":
    main()
