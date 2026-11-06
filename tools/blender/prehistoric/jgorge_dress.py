# The Burnt Gorge's second pass (Blake, Nov 6, review journey_gorge 1): the Ash Tube's
# lava as cracks in its walls; the Long Meadow's falls out of the mountain; its bridge of
# planks; the Cleft's natural rock arch; the pilgrims' waystations, each in the manner of
# the world its travellers come from; ducks on the river.
# SPDX-License-Identifier: MIT
#
#   lava_crack        notes 4, 5: glowing cracks up the tube's walls, set into the rock
#   falls             note 14: the river springing from a cave in the mountain, down a
#                     gorge of its own, over an upper fall into a pool, then the great fall
#                     into the meadow, mist at their feet
#   plank_bridge      note 15: planks with gaps between them, rope rails, log posts (the
#                     Snowy Summit's rope bridges', built steady)
#   rock_arch         note 12: a weathered limestone arch over the Cleft's mouth, moss and
#                     vines on it, water trickling off it
#   waystations       notes 8 to 10 (Blake picked waystations by world): the desert
#                     caravanserai by the ford, the islanders' stilt stop at the falls' foot,
#                     the Kingdom's inn on the meadow's south side, the snow folk's lodge on
#                     the steppe; signposts to the kingdoms, travellers resting, trading,
#                     mending carts, feeding their beasts
#   ducks             note 17: a few families of ducks paddling along the river
#
# journey_region.py (gorge) calls these.

import math

from course_kit import lerp
from gulch_scenery import Mesh  # noqa: F401  (journey_region's cracks use it)
import props
from props import cuboid
import region_paint as paint


def rnd(k):
    return (math.sin(k * 12.9898 + 4.1414) * 43758.5453) % 1.0


def two_sided(m, mat, pts, uvs=None):
    uvs = uvs or [(0, 0), (1, 0), (1, 1), (0, 1)][:len(pts)]
    m.quad((mat, "wall"), pts, uvs)
    m.quad((mat, "wall"), list(reversed(pts)), list(reversed(uvs)))


def cone(bm, x, y, z, r, h, n=8):
    ring = [bm.verts.new((x + r * math.cos(a), y + r * math.sin(a), z)) for a in [i * math.tau / n for i in range(n)]]
    tip = bm.verts.new((x, y, z + h))
    for i in range(n):
        bm.faces.new((ring[i], ring[(i + 1) % n], tip))
    bm.faces.new(ring[::-1])


# ------------------------------------------------------------------ the Ash Tube


def lava_crack(m, q, sd, half, k):
    """A glowing crack running up the tube's wall beside road sample q, on side sd: a
    jagged line of lava from the floor to head height and more, flush with the rock, with
    a branch or two off it."""
    up = 1.5 + 4.5 * rnd(k * 3.1 + sd)
    n = 6
    off = sd * (half - 0.08)
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1.1 * math.sin(k * 1.7 + i * 2.3 + sd) * (0.3 + t)
        pts.append((q.p.x + q.r.x * off + q.t.x * u, q.p.y + q.r.y * off + q.t.y * u, q.p.z + 0.1 + up * t))
    for a, b in zip(pts, pts[1:]):
        w = 0.22 * (1.0 - 0.6 * (b[2] - q.p.z) / (up + 0.1))
        two_sided(m, "volcano_lava", [(a[0] - q.t.x * w, a[1] - q.t.y * w, a[2]), (a[0] + q.t.x * w, a[1] + q.t.y * w, a[2]),
                                     (b[0] + q.t.x * w * 0.8, b[1] + q.t.y * w * 0.8, b[2]), (b[0] - q.t.x * w * 0.8, b[1] - q.t.y * w * 0.8, b[2])])
    if k % 2 == 0:
        a = pts[2]
        b = (a[0] + q.t.x * 1.4, a[1] + q.t.y * 1.4, a[2] + 0.9)
        two_sided(m, "volcano_lava", [(a[0], a[1], a[2] - 0.1), (a[0], a[1], a[2] + 0.1), (b[0], b[1], b[2] + 0.04), (b[0], b[1], b[2] - 0.04)])
    # (a glow pooled at its foot)
    two_sided(m, "volcano_lava", [(pts[0][0] - q.t.x * 0.6 - q.r.x * sd * 0.5, pts[0][1] - q.t.y * 0.6 - q.r.y * sd * 0.5, q.p.z + 0.04),
                                 (pts[0][0] + q.t.x * 0.6 - q.r.x * sd * 0.5, pts[0][1] + q.t.y * 0.6 - q.r.y * sd * 0.5, q.p.z + 0.04),
                                 (pts[0][0] + q.t.x * 0.6, pts[0][1] + q.t.y * 0.6, q.p.z + 0.04),
                                 (pts[0][0] - q.t.x * 0.6, pts[0][1] - q.t.y * 0.6, q.p.z + 0.04)])


# ------------------------------------------------------------------ the falls


def falls(c, J, L, ground):
    """The river out of the mountain: its cave, its gorge, the upper fall, the pool, the
    great fall into the meadow; mist and spray."""
    sp = J.SPRING
    foot = L.rivers[0][0][2]
    (lx, ly, lz), (px, py, pz), (ux, uy, uz), (cx, cy, cz) = sp
    # (the water: the channel from the cave to the upper fall, the pool between the falls)
    for name, pts, w in (("Spring Channel", [(cx, cy, cz), (ux, uy, uz)], 12.0), ("Spring Pool", [(px, py, pz), (lx, ly, lz)], 20.0)):
        strip = []
        (ax, ay, az), (bx, by, bz) = pts
        n = max(2, int(math.hypot(bx - ax, by - ay) / 4))
        for k in range(n + 1):
            t = k / n
            strip.append((lerp(ax, bx, t), lerp(ay, by, t), w, lerp(az, bz, t) - 0.1))
        c.ribbon(name, strip, w, 0, c.lib("valley_water", "water"), role="visual", steps=3)
    # (the great fall off the gorge's lip into the meadow; the upper fall into the pool)
    props.falls(c, "Meadow Falls", lx, ly, lz, foot, 18.0, 30.0, facing=-1, throw=7.5, bulge=2.0, veils=4)
    props.falls(c, "Meadow Upper Falls", ux, uy, uz, pz, 10.0, 14.0, facing=-1, throw=4.0, bulge=1.2, veils=2)
    for (x, y, z, r) in ((lx, ly - 14.0, foot + 1.0, 8.0), (lx, ly - 10.0, foot + 6.0, 6.0), (ux, uy - 6.0, pz + 1.0, 5.0)):
        g = c.game(x, y, z)
        c.entity("mist", x=round(g[0], 1), y=round(g[1], 1), z=round(g[2], 1), radius=r, rate=3.0, color="#e8f4ff")
    g = c.game(lx, ly - 12.0, foot)
    c.entity("waterfall", x=g[0], y=g[1], z=g[2], top=round(lz - foot, 1), width=26.0, heading=0.0)
    # (the cave it springs from: a dark mouth under a brow of mossy rock, boulders round it)
    m = Mesh()
    mouth = (cx, cy + 3.0)
    for i in range(9):
        a = math.pi * i / 8
        rx, rz = 9.0 * math.cos(a), 7.0 * math.sin(a)
        bx, by = mouth[0] + rx, mouth[1] + 1.0
        m.add(("limestone_moss", "wall"), lambda bm, bx=bx, by=by, rz=rz, i=i: props.blob(bm, (bx, by, cz + rz), 2.4 + 0.8 * rnd(i), sy=0.8, subdiv=1))
    two_sided(m, "obsidian_cliff", [(mouth[0] - 8.0, mouth[1] + 2.0, cz - 0.5), (mouth[0] + 8.0, mouth[1] + 2.0, cz - 0.5),
                                    (mouth[0] + 6.0, mouth[1] + 2.0, cz + 6.0), (mouth[0] - 6.0, mouth[1] + 2.0, cz + 6.0)])
    for i in range(6):
        a = i * 1.1 + 0.4
        bx, by = mouth[0] + 10.0 * math.cos(a) * 0.9, mouth[1] - 6.0 + 4.0 * math.sin(a)
        m.add(("moss_rock", "wall"), lambda bm, bx=bx, by=by, i=i: props.blob(bm, (bx, by, ground(bx, by)), 1.4 + rnd(i * 3), sz=0.8, subdiv=1))
    # (rocks at both lips, the water parting round them)
    for (x, y, z) in ((lx - 7.0, ly, lz), (lx + 8.0, ly + 1.0, lz), (ux - 4.5, uy, uz), (ux + 5.0, uy, uz)):
        m.add(("moss_rock", "wall"), lambda bm, x=x, y=y, z=z: props.blob(bm, (x, y, z), 1.8, sz=0.9, subdiv=1))
    m.build(c, "Spring Cave", coll="Props", role="visual")


# ------------------------------------------------------------------ the bridge


def plank_bridge(c):
    """The river's bridge as planks with gaps between them on rope stringers, rope rails,
    log posts at its ends (summit_scenery's rope bridge, steady: none missing)."""
    import summit_scenery as ss

    spans = sorted((p["kp_from"], p["kp_to"]) for p in c.pieces if " bridge" in p.name)
    for k, (s0, s1) in enumerate(spans):
        ss._rope_span(c, ss, s0, s1, "Plank Bridge %d" % (k + 1), worn=False)
    return len(spans)


# ------------------------------------------------------------------ the arch


def rock_arch(c, ground, x, y, rot, span, h):
    """A natural arch of weathered limestone over the road: two rough legs of stacked
    rock, the arch between them knobbly and mossed, vines hanging off it, water trickling
    from it (note 12: Blake picked a natural rock arch)."""
    import swamp_props as swp

    m, solid = Mesh(), Mesh()
    ca, sa = math.cos(rot), math.sin(rot)

    def P(u, z):
        return x + u * ca, y + u * sa, z

    gz = ground(x, y)
    legs = []
    for sd in (-1, 1):
        u0 = sd * span / 2
        bx, by, _ = P(u0, 0)
        g = min(ground(bx + ox, by + oy) for ox, oy in ((2, 0), (-2, 0), (0, 2), (0, -2)))
        legs.append((u0, g))
        for i in range(7):
            z = g + i * (h * 0.55) / 6
            r = 4.2 - 0.25 * i + 0.6 * rnd(i + sd)
            ox = (rnd(i * 3 + sd) - 0.5) * 1.4
            px, py, _ = P(u0 + ox + sd * 0.6 * (6 - i) * 0.2, 0)
            mat = ("limestone", "wall") if i % 3 else ("limestone_moss", "wall")
            solid.add(mat, lambda bm, px=px, py=py, z=z, r=r, i=i: props.blob(bm, (px, py, z), r, sx=1.0, sy=1.25, sz=0.75, subdiv=2))
    # (the span: a thick knobbly band over the top, sagging a little, mossed on top)
    n = 14
    for i in range(n + 1):
        t = i / n
        u = lerp(legs[0][0], legs[1][0], t)
        z = gz + h * 0.5 + h * 0.48 * math.sin(math.pi * t) ** 0.7
        r = 3.2 - 0.9 * math.sin(math.pi * t) + 0.5 * rnd(i * 5)
        px, py, _ = P(u, 0)
        m.add((("limestone", "limestone_moss")[i % 3 == 0], "wall"),
              lambda bm, px=px, py=py, z=z, r=r: props.blob(bm, (px, py, z), r, sx=0.9, sy=1.5, sz=0.8, subdiv=2))
        if 2 < i < n - 2 and i % 3 == 1:
            m.add(("lush_grass", "wall"), lambda bm, px=px, py=py, z=z, r=r: props.blob(bm, (px, py, z + r * 0.62), r * 0.75, sx=1.0, sy=1.3, sz=0.25, subdiv=1))
    for i in range(5):
        t = 0.2 + 0.15 * i
        u = lerp(legs[0][0], legs[1][0], t)
        z = gz + h * 0.5 + h * 0.48 * math.sin(math.pi * t) ** 0.7 - 2.0
        px, py, _ = P(u, 0)
        c.place(swp.hanging_vine(c, i % 2, length=5.0 + 3.0 * rnd(i)), px + sa * (1.5 if i % 2 else -1.5), py - ca * (1.5 if i % 2 else -1.5), z,
                rot=i * 1.3, coll="Props", role="visual")
    # (a trickle of water off its brow, splashing on the rock beside the road)
    u = legs[1][0] * 0.72
    tx, ty, _ = P(u, 0)
    top = gz + h * 0.5 + h * 0.48 * math.sin(math.pi * 0.86) ** 0.7 - 1.0
    props.falls(c, "Arch Trickle", tx, ty + 0.8, top, ground(tx, ty), 1.2, 2.0, facing=1, throw=1.0, bulge=0.3, veils=1, angle=rot)
    m.build(c, "Rock Arch", coll="Props", role="visual")
    solid.build(c, "Rock Arch Legs", coll="Props", role="both")


# ------------------------------------------------------------------ the waystations


GORGE_SIGNS = {"sign_to_snow": 3, "sign_to_valley": 3, "sign_to_desert": 3, "sign_to_isles": 3, "sign_to_dragon": 3}


def signpost(m, x, y, z, k, toward):
    """A pilgrims' signpost: a stout post, arrow boards to the kingdoms at different
    heights pointing their ways (toward: [(sign id, angle)])."""
    m.add(("weathered_timber", "wall"), lambda bm: props.tube(bm, [(x, y, z - 0.3), (x, y, z + 4.2)], 0.14, n=6))
    m.add(("weathered_timber", "wall"), lambda bm: cone(bm, x, y, z + 4.2, 0.2, 0.35, n=6))
    for i, (sid, a) in enumerate(toward):
        zb = z + 3.6 - i * 0.62
        ca, sa = math.cos(a), math.sin(a)
        n = GORGE_SIGNS[sid]
        L_ = 2.2
        for j in range(n):
            u0, u1 = 0.25 + L_ * j / n, 0.25 + L_ * (j + 1) / n
            pts = [(x + ca * u0, y + sa * u0, zb - 0.22), (x + ca * u1, y + sa * u1, zb - 0.22),
                   (x + ca * u1, y + sa * u1, zb + 0.22), (x + ca * u0, y + sa * u0, zb + 0.22)]
            m.quad(("%s_%d" % (sid, j + 1), "wall"), pts, [(0, 0), (1, 0), (1, 1), (0, 1)])
            m.quad(("%s_%d" % (sid, n - j), "wall"), list(reversed(pts)), [(1, 0), (0, 0), (0, 1), (1, 1)])
        # (its arrowhead)
        tipx, tipy = x + ca * (L_ + 0.25), y + sa * (L_ + 0.25)
        two_sided(m, "weathered_timber", [(tipx, tipy, zb - 0.26), (tipx + ca * 0.45, tipy + sa * 0.45, zb), (tipx, tipy, zb + 0.26)], [(0, 0), (1, 0.5), (0, 1)])


class Folk:
    """A waystation's travellers (one folk_poses entity: detailed folk, busy)."""

    def __init__(self, c, folk):
        self.c, self.folk, self.rows = c, folk, []

    def add(self, x, y, z, pose, fx, fy, seed, at=None):
        g = self.c.game(x, y, z)
        row = [round(g[0], 2), round(g[1], 2), round(g[2], 2), round(math.atan2(fx - x, -(fy - y)), 3), pose, seed]
        if at is not None:
            row += [round(v, 2) for v in self.c.game(*at)]
        self.rows.append(row)

    def done(self):
        if self.rows:
            self.c.entity("folk_poses", folk=self.folk, list=self.rows)
        return len(self.rows)


def _ring(cx, cy, r, n, a0=0.0):
    return [(cx + r * math.cos(a0 + k * math.tau / n), cy + r * math.sin(a0 + k * math.tau / n), a0 + k * math.tau / n) for k in range(n)]


def _fire(c, x, y, z):
    g = c.game(x, y, z + 0.2)
    c.entity("campfire", x=g[0], y=g[1], z=g[2])


def _talkers(c, x, y, z, r, n, folk):
    g = c.game(x, y, z)
    c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=r, n=n, folk=folk, heading=0.0)


def _ok(c, taken, L, x, y, r):
    return paint.road_clear(c, x, y, r + 1.0) and taken.clear(x, y, r) and L.water_d(x, y)[0] > L.river_hw + 2.0


def caravanserai(c, ground, taken, L, cx, cy, cr, road_toward):
    """The desert folk's caravanserai by the ford: a walled yard of adobe with an arched
    gate to the road, domed rooms round it, rugs and cushions in its shade, a fountain in
    the middle, their pack-beasts at a trough, striped awnings over the traders' stalls,
    lanterns, a signpost; the travellers resting, haggling, feeding the beasts."""
    import oasis_props as op
    import gulch_props as gp

    m, solid = Mesh(), Mesh()
    folk = Folk(c, "desert")
    z0 = min(ground(cx + cr * 0.6 * math.cos(a), cy + cr * 0.6 * math.sin(a)) for a in [k * math.tau / 8 for k in range(8)])
    # (the walls round the yard, a gap for the gate on the road side; domed rooms on them)
    for k in range(16):
        a = k * math.tau / 16
        da = (a - road_toward + math.pi) % math.tau - math.pi
        if abs(da) < 0.35:
            continue
        x, y = cx + cr * math.cos(a), cy + cr * math.sin(a)
        if not paint.road_clear(c, x, y, 2.0):
            continue
        g = ground(x, y)
        solid.add(("adobe", "wall"), lambda bm, x=x, y=y, g=g, a=a: cuboid(bm, (x, y, g + 1.4), (1.0, cr * 0.42, 3.6), a))
        if k % 4 == 1:
            rx, ry = cx + (cr - 3.0) * math.cos(a), cy + (cr - 3.0) * math.sin(a)
            rg = ground(rx, ry)
            solid.add(("adobe", "wall"), lambda bm, rx=rx, ry=ry, rg=rg, a=a: cuboid(bm, (rx, ry, rg + 1.6), (4.6, 4.6, 3.6), a))
            m.add(("white_plaster", "wall"), lambda bm, rx=rx, ry=ry, rg=rg: op.dome(bm, rx, ry, rg + 3.4, 2.4, h=2.2, n=14, rings=5))
            dx, dy = cx + (cr - 5.35) * math.cos(a), cy + (cr - 5.35) * math.sin(a)
            m.add(("door_wood", "wall"), lambda bm, dx=dx, dy=dy, rg=rg, a=a: cuboid(bm, (dx, dy, rg + 1.0), (0.12, 1.2, 2.0), a))
    # (the gate: two piers and a pointed arch over the road side's gap)
    for sd in (-1, 1):
        a = road_toward + sd * 0.38
        x, y = cx + cr * math.cos(a), cy + cr * math.sin(a)
        g = ground(x, y)
        solid.add(("adobe_dark", "wall"), lambda bm, x=x, y=y, g=g: cuboid(bm, (x, y, g + 2.6), (1.6, 1.6, 5.4)))
        c.place(op.lantern_post(c), x + math.cos(road_toward) * 1.6, y + math.sin(road_toward) * 1.6, g, coll="Props", role="visual")
    gx, gy = cx + cr * math.cos(road_toward), cy + cr * math.sin(road_toward)
    gg = ground(gx, gy)
    m.add(("adobe_dark", "wall"), lambda bm: cuboid(bm, (gx, gy, gg + 5.6), (1.4, 2 * cr * math.sin(0.38) + 1.6, 1.0), road_toward))
    m.add(("adobe_dark", "wall"), lambda bm: cone(bm, gx, gy, gg + 6.1, 1.2, 1.6, n=4))
    # (the fountain, rugs and cushions round it, travellers lounging)
    c.place(op.fountain(c, 0, r=2.4), cx, cy, z0, coll="Props")
    g = c.game(cx, cy, z0)
    c.entity("fountain", x=g[0], y=g[1], z=g[2], r=2.4)
    for k, (x, y, a) in enumerate(_ring(cx, cy, 5.5, 5, 0.3)):
        rx_, ry_ = math.cos(a), math.sin(a)
        two_sided(m, ("rug", "royal_carpet", "keep_carpet")[k % 3], [(x - ry_ * 1.4 - rx_ * 0.9, y + rx_ * 1.4 - ry_ * 0.9, z0 + 0.05),
                                                                     (x + ry_ * 1.4 - rx_ * 0.9, y - rx_ * 1.4 - ry_ * 0.9, z0 + 0.05),
                                                                     (x + ry_ * 1.4 + rx_ * 0.9, y - rx_ * 1.4 + ry_ * 0.9, z0 + 0.05),
                                                                     (x - ry_ * 1.4 + rx_ * 0.9, y + rx_ * 1.4 + ry_ * 0.9, z0 + 0.05)])
        for j in range(2):
            px, py = x + ry_ * (j - 0.5) * 1.4, y - rx_ * (j - 0.5) * 1.4
            m.add(("awning_sun", "wall"), lambda bm, px=px, py=py: props.blob(bm, (px, py, z0 + 0.2), 0.35, sz=0.45, subdiv=1))
        pose = ("kneel", "chat", "eat", "kneel", "chat")[k]
        folk.add(x + rx_ * 0.3, y + ry_ * 0.3, z0, pose, cx, cy, 600 + k, at=(cx, cy, z0 + 1.0))
    # (the stalls under awnings along the inside of the wall, their traders)
    for k, (x, y, a) in enumerate(_ring(cx, cy, cr * 0.68, 4, road_toward + 0.8)):
        if not _ok(c, taken, L, x, y, 0.5):
            continue
        c.place(op.market_stall(c, k % 3), x, y, ground(x, y) - 0.05, rot=a + math.pi / 2 + math.pi, coll="Props")
        folk.add(x + math.cos(a) * 1.6, y + math.sin(a) * 1.6, ground(x, y), ("chat", "point")[k % 2], cx, cy, 610 + k, at=(x, y, ground(x, y) + 1.0))
        folk.add(x - math.cos(a) * 2.4, y - math.sin(a) * 2.4, ground(x, y), ("think", "chat")[k % 2], x, y, 615 + k, at=(x, y, ground(x, y) + 1.0))
    # (the pack-beasts outside the wall at their trough, a traveller feeding them, their
    # packs and bales stacked; the signpost by the gate)
    bx, by = cx + (cr + 9.0) * math.cos(road_toward + 1.4), cy + (cr + 9.0) * math.sin(road_toward + 1.4)
    if _ok(c, taken, L, bx, by, 4.0):
        bz = ground(bx, by)
        c.place(gp.trough(c), bx, by, bz - 0.05, rot=road_toward, coll="Props")
        pts = []
        for j in range(10):
            a = j * math.tau / 10
            px, py = bx + 6.0 * math.cos(a), by + 4.0 * math.sin(a)
            pts.append((px, py, ground(px, py)))
        c.path_curve("Caravan Beasts", pts, closed=True)
        for j in range(2):
            c.entity("dinosaur", route="Caravan Beasts", speed=0.5, scale=0.45 + 0.1 * j, start=j * 8.0)
        folk.add(bx + 1.4, by + 0.6, bz, "work", bx, by, 620, at=(bx, by, bz + 0.6))
        c.place(op.crates(c, 1), bx - 3.2, by + 2.0, ground(bx - 3.2, by + 2.0) - 0.05, coll="Props")
        taken.add(bx, by, 7.0)
    sx, sy = cx + (cr + 4.0) * math.cos(road_toward + 0.6), cy + (cr + 4.0) * math.sin(road_toward + 0.6)
    signpost(m, sx, sy, ground(sx, sy), 0, [("sign_to_snow", 0.9), ("sign_to_desert", 2.6), ("sign_to_valley", 4.0)])
    _fire(c, cx + 3.0, cy - 3.0, z0)
    _talkers(c, cx, cy, z0, cr - 2.0, 5, "desert")
    m.build(c, "Caravanserai", coll="Village", role="visual")
    solid.build(c, "Caravanserai Walls", coll="Village", role="both")
    taken.add(cx, cy, cr + 3.0)
    return folk.done()


def stilt_stop(c, ground, taken, L, cx, cy, cr, toward_river):
    """The islanders' stop at the falls' foot: stilt huts of bamboo and thatch along the
    water, a boardwalk between them, canoes drawn up, hammocks slung between posts, a
    fruit stall, tiki torches, a signpost; the islanders cooking, mending a canoe, resting
    in the hammocks."""
    import tropic_props as tp
    import beach_props as bp
    import oasis_props as op

    m, solid = Mesh(), Mesh()
    folk = Folk(c, "beach")
    z0 = ground(cx, cy)
    huts = []
    for k in range(4):
        a = toward_river + (k - 1.5) * 0.55
        x, y = cx + cr * 0.72 * math.cos(a), cy + cr * 0.72 * math.sin(a)
        if not _ok(c, taken, L, x, y, 3.5):
            continue
        c.place(tp.beach_hut(c, k % 3), x, y, ground(x, y) - 0.05, rot=a + math.pi / 2 + math.pi, coll="Village")
        taken.add(x, y, 4.0)
        huts.append((x, y, a))
    for (ax, ay, _), (bx, by, _) in zip(huts, huts[1:]):
        az, bz = ground(ax, ay) + 0.9, ground(bx, by) + 0.9
        dx, dy = bx - ax, by - ay
        d = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / d * 0.8, dx / d * 0.8
        two_sided(m, "plank_deck", [(ax - nx, ay - ny, az), (bx - nx, by - ny, bz), (bx + nx, by + ny, bz), (ax + nx, ay + ny, az)])
        for t in (0.25, 0.5, 0.75):
            px, py = ax + dx * t, ay + dy * t
            m.add(("bamboo", "wall"), lambda bm, px=px, py=py, t=t: props.tube(bm, [(px, py, ground(px, py) - 0.3), (px, py, lerp(az, bz, t))], 0.08, n=5))
    # (hammocks between posts, someone in each)
    for k in range(2):
        a = toward_river + math.pi + (k - 0.5) * 0.9
        x, y = cx + cr * 0.35 * math.cos(a), cy + cr * 0.35 * math.sin(a)
        if not _ok(c, taken, L, x, y, 2.5):
            continue
        ca, sa = math.cos(a + math.pi / 2), math.sin(a + math.pi / 2)
        g = ground(x, y)
        ends = [(x - ca * 2.0, y - sa * 2.0), (x + ca * 2.0, y + sa * 2.0)]
        for ex, ey in ends:
            solid.add(("bamboo", "wall"), lambda bm, ex=ex, ey=ey, g=g: props.tube(bm, [(ex, ey, g - 0.3), (ex, ey, g + 2.2)], 0.1, n=6))
        pts = [(lerp(ends[0][0], ends[1][0], t), lerp(ends[0][1], ends[1][1], t), g + 1.6 - 0.8 * math.sin(math.pi * t)) for t in [i / 6 for i in range(7)]]
        m.add(("cove_awning_coral", "wall"), lambda bm, pts=pts: props.tube(bm, pts, [0.05, 0.35, 0.45, 0.45, 0.45, 0.35, 0.05], n=6))
        folk.add(x, y, g + 0.85, "kneel", x + math.cos(a) * 3.0, y + math.sin(a) * 3.0, 630 + k)
        taken.add(x, y, 2.5)
    # (the fire, the cooks; the fruit stall; a canoe being mended)
    fx, fy = cx - math.cos(toward_river) * 2.0, cy - math.sin(toward_river) * 2.0
    _fire(c, fx, fy, ground(fx, fy))
    for k, (x, y, a) in enumerate(_ring(fx, fy, 1.9, 3, 0.4)):
        folk.add(x, y, ground(x, y), ("cook", "chat", "eat")[k], fx, fy, 640 + k, at=(fx, fy, ground(fx, fy) + 0.5))
    sx, sy = cx + cr * 0.5 * math.cos(toward_river + 2.2), cy + cr * 0.5 * math.sin(toward_river + 2.2)
    if _ok(c, taken, L, sx, sy, 2.5):
        c.place(op.market_stall(c, 2), sx, sy, ground(sx, sy) - 0.05, rot=toward_river, coll="Props")
        folk.add(sx + 1.4, sy, ground(sx, sy), "point", fx, fy, 645)
        taken.add(sx, sy, 3.0)
    kx, ky = cx + (cr + 2.0) * math.cos(toward_river + 0.9), cy + (cr + 2.0) * math.sin(toward_river + 0.9)
    if taken.clear(kx, ky, 2.5) and paint.road_clear(c, kx, ky, 2.5):
        c.place(bp.canoe(c, 0), kx, ky, ground(kx, ky) + 0.05, rot=toward_river + 1.4, coll="Props", role="visual")
        folk.add(kx + 1.2, ky - 0.6, ground(kx, ky), "beat", kx, ky, 648, at=(kx, ky, ground(kx, ky) + 0.4))
        taken.add(kx, ky, 3.0)
    for k, (x, y, a) in enumerate(_ring(cx, cy, cr * 0.9, 5, toward_river + 0.3)):
        if paint.road_clear(c, x, y, 1.0) and taken.clear(x, y, 0.8) and L.water_d(x, y)[0] > L.river_hw:
            c.place(bp.tiki_torch(c, k % 2), x, y, ground(x, y) - 0.05, coll="Props", role="visual")
            g = c.game(x, y, ground(x, y) + 2.2)
            c.entity("torch", x=g[0], y=g[1], z=g[2])
    px, py = cx + (cr + 5.0) * math.cos(toward_river + math.pi - 0.5), cy + (cr + 5.0) * math.sin(toward_river + math.pi - 0.5)
    signpost(m, px, py, ground(px, py), 1, [("sign_to_isles", 4.4), ("sign_to_snow", 1.2), ("sign_to_valley", 3.6)])
    _talkers(c, cx, cy, z0, cr, 4, "beach")
    m.build(c, "Stilt Stop", coll="Village", role="visual")
    solid.build(c, "Stilt Stop Posts", coll="Village", role="both")
    taken.add(cx, cy, cr * 0.5)
    return folk.done()


def kingdom_inn(c, ground, taken, L, cx, cy, cr, road_toward):
    """The Dragon Kingdom's inn on the meadow's south side: the inn (a timber-framed house,
    its sign out on a bracket), its stable with a cart being mended, a well, benches and
    tables out front, banners, torch posts, a signpost; the travellers eating at the
    tables, the smith at the cart's wheel, the stable hand with the beasts."""
    import keep_props as kp
    import gulch_props as gp
    import valley_village as vv

    m, solid = Mesh(), Mesh()
    folk = Folk(c, "dragon")
    kp.use_palette({})
    z0 = ground(cx, cy)
    back = road_toward + math.pi
    ix, iy = cx + math.cos(back) * cr * 0.45, cy + math.sin(back) * cr * 0.45
    c.place(kp.house(c, 1), ix, iy, ground(ix, iy) - 0.1, rot=road_toward - math.pi / 2, scale=1.6, coll="Village")
    for sd in (-1, 1):
        hx, hy = ix + math.cos(back + sd * math.pi / 2) * 11.0, iy + math.sin(back + sd * math.pi / 2) * 11.0
        if _ok(c, taken, L, hx, hy, 4.0):
            c.place(kp.house(c, 2 if sd > 0 else 0), hx, hy, ground(hx, hy) - 0.1, rot=road_toward - math.pi / 2 + sd * 0.3, scale=1.1, coll="Village")
            taken.add(hx, hy, 5.0)
    g = c.game(ix, iy, ground(ix, iy) + 14.0)
    c.entity("chimney", x=g[0], y=g[1], z=g[2])
    # (its sign on a bracket)
    sx, sy = ix + math.cos(road_toward) * 6.5, iy + math.sin(road_toward) * 6.5
    sg = ground(sx, sy)
    m.add(("timber_beam", "wall"), lambda bm: props.tube(bm, [(sx, sy, sg - 0.2), (sx, sy, sg + 4.4)], 0.12, n=6))
    bx, by = sx + math.cos(road_toward + math.pi / 2) * 1.2, sy + math.sin(road_toward + math.pi / 2) * 1.2
    m.add(("timber_beam", "wall"), lambda bm: props.tube(bm, [(sx, sy, sg + 4.2), (bx, by, sg + 4.2)], 0.07, n=4))
    m.add(("keep_banner", "wall"), lambda bm: cuboid(bm, (bx, by, sg + 3.5), (1.1, 0.08, 1.1), road_toward))
    # (tables and benches out front, the travellers at them)
    for k in range(3):
        a = road_toward + (k - 1) * 0.55
        tx, ty = cx + math.cos(a) * cr * 0.1 + math.cos(road_toward) * 3.0 * (k % 2), cy + math.sin(a) * cr * 0.1 + math.sin(road_toward) * 3.0 * (k % 2)
        tx += math.cos(road_toward + math.pi / 2) * (k - 1) * 4.5
        ty += math.sin(road_toward + math.pi / 2) * (k - 1) * 4.5
        if not _ok(c, taken, L, tx, ty, 1.8):
            continue
        tz = ground(tx, ty)
        solid.add(("weathered_timber", "wall"), lambda bm, tx=tx, ty=ty, tz=tz: cuboid(bm, (tx, ty, tz + 0.4), (2.2, 0.9, 0.8), road_toward))
        for sd in (-1, 1):
            ex, ey = tx + math.cos(road_toward) * sd * 1.0, ty + math.sin(road_toward) * sd * 1.0
            m.add(("weathered_timber", "wall"), lambda bm, ex=ex, ey=ey, tz=tz: cuboid(bm, (ex, ey, tz + 0.22), (2.0, 0.35, 0.44), road_toward))
            fx_, fy_ = tx + math.cos(road_toward) * sd * 1.15, ty + math.sin(road_toward) * sd * 1.15
            folk.add(fx_, fy_, tz, ("eat", "chat")[(k + (sd > 0)) % 2], tx, ty, 650 + k * 2 + (sd > 0), at=(tx, ty, tz + 0.9))
        taken.add(tx, ty, 2.2)
    # (the stable: posts and a roof, a cart in it with its wheel off, the smith at it)
    st = back + 1.2
    stx, sty = cx + math.cos(st) * cr * 0.7, cy + math.sin(st) * cr * 0.7
    if _ok(c, taken, L, stx, sty, 4.0):
        stz = ground(stx, sty)
        for j in (-1, 1):
            for q in (-1, 1):
                px, py = stx + math.cos(st) * j * 2.4 - math.sin(st) * q * 3.6, sty + math.sin(st) * j * 2.4 + math.cos(st) * q * 3.6
                solid.add(("timber_beam", "wall"), lambda bm, px=px, py=py, stz=stz: props.tube(bm, [(px, py, stz - 0.3), (px, py, stz + 3.4)], 0.12, n=5))
        m.add(("shingle_roof", "wall"), lambda bm: cuboid(bm, (stx, sty, stz + 3.6), (5.6, 8.2, 0.2), st, tilt=(0.0, 0.12)))
        c.place(gp.wagon(c, covered=False), stx, sty, stz - 0.05, rot=st, coll="Props")
        folk.add(stx + math.cos(st) * 2.0, sty + math.sin(st) * 2.0, stz, "beat", stx, sty, 660, at=(stx, sty, stz + 0.6))
        taken.add(stx, sty, 5.0)
    wx, wy = cx + math.cos(back - 1.1) * cr * 0.55, cy + math.sin(back - 1.1) * cr * 0.55
    if _ok(c, taken, L, wx, wy, 2.0):
        vv.GROUND = ground
        c.place(vv.well(c), wx, wy, ground(wx, wy) - 0.1, coll="Props")
        folk.add(wx + 1.3, wy, ground(wx, wy), "work", wx, wy, 662, at=(wx, wy, ground(wx, wy) + 0.8))
        taken.add(wx, wy, 2.5)
    for k, (x, y, a) in enumerate(_ring(cx, cy, cr * 0.95, 6, road_toward + 0.5)):
        if paint.road_clear(c, x, y, 1.0) and taken.clear(x, y, 0.8):
            c.place(kp.torch_post(c) if k % 2 else kp.banner_pole(c, h=7.0), x, y, ground(x, y) - 0.1, coll="Props")
            if k % 2:
                g = c.game(x, y, ground(x, y) + 2.7)
                c.entity("torch", x=g[0], y=g[1], z=g[2])
    px, py = cx + math.cos(road_toward + 0.7) * (cr + 2.0), cy + math.sin(road_toward + 0.7) * (cr + 2.0)
    signpost(m, px, py, ground(px, py), 2, [("sign_to_dragon", 5.2), ("sign_to_snow", 1.0), ("sign_to_valley", 3.2)])
    _talkers(c, cx, cy, z0, cr - 2.0, 5, "dragon")
    m.build(c, "Kingdom Inn", coll="Village", role="visual")
    solid.build(c, "Kingdom Inn Solids", coll="Village", role="both")
    taken.add(ix, iy, 8.0)
    return folk.done()


def snow_lodge(c, ground, taken, L, cx, cy, cr, road_toward):
    """The snow folk's lodge on the steppe, for those coming down from the Snow Kingdom:
    mountain houses round a yard, a white stupa, sledges and their loads, a ration stall,
    sacks stacked, a signpost; the snow pilgrims at the stall, loading a sledge, warming at
    the fire."""
    import snow_props as snp

    m, solid = Mesh(), Mesh()
    folk = Folk(c, "pilgrim")
    z0 = ground(cx, cy)
    for k in range(3):
        a = road_toward + math.pi + (k - 1) * 0.95
        x, y = cx + cr * 0.62 * math.cos(a), cy + cr * 0.62 * math.sin(a)
        if _ok(c, taken, L, x, y, 4.5):
            c.place(snp.snow_house(c, k % 3), x, y, ground(x, y) - 0.15, rot=a + math.pi / 2, coll="Village")
            taken.add(x, y, 5.5)
    sx, sy = cx + math.cos(road_toward + 1.6) * cr * 0.45, cy + math.sin(road_toward + 1.6) * cr * 0.45
    if _ok(c, taken, L, sx, sy, 2.5):
        c.place(snp.chorten(c, 0.9), sx, sy, ground(sx, sy) - 0.1, coll="Props")
        taken.add(sx, sy, 3.0)
    rx, ry = cx + math.cos(road_toward - 1.3) * cr * 0.45, cy + math.sin(road_toward - 1.3) * cr * 0.45
    if _ok(c, taken, L, rx, ry, 2.5):
        c.place(snp.ration_stall(c, 0), rx, ry, ground(rx, ry) - 0.05, rot=road_toward, coll="Props")
        folk.add(rx + math.cos(road_toward) * 1.6, ry + math.sin(road_toward) * 1.6, ground(rx, ry), "chat", rx, ry, 670, at=(rx, ry, ground(rx, ry) + 1.0))
        folk.add(rx - math.cos(road_toward) * 1.2, ry - math.sin(road_toward) * 1.2, ground(rx, ry), "cook", rx, ry, 671, at=(rx, ry, ground(rx, ry) + 1.0))
        taken.add(rx, ry, 3.0)
    for k in range(2):
        a = road_toward + 0.4 + k * 0.5
        lx, ly = cx + math.cos(a) * cr * 0.75, cy + math.sin(a) * cr * 0.75
        if _ok(c, taken, L, lx, ly, 2.0):
            c.place(snp.sled(c, k), lx, ly, ground(lx, ly), rot=a, coll="Props")
            c.place(snp.sack_pile(c, k), lx + math.cos(a + 1.6) * 2.0, ly + math.sin(a + 1.6) * 2.0, ground(lx, ly), coll="Props")
            folk.add(lx + math.cos(a + 1.6) * 1.0, ly + math.sin(a + 1.6) * 1.0, ground(lx, ly), "work", lx, ly, 672 + k, at=(lx, ly, ground(lx, ly) + 0.6))
            taken.add(lx, ly, 3.0)
    _fire(c, cx, cy, z0)
    for k, (x, y, a) in enumerate(_ring(cx, cy, 2.0, 4, 0.2)):
        folk.add(x, y, ground(x, y), ("kneel", "chat", "eat", "chat")[k], cx, cy, 676 + k, at=(cx, cy, z0 + 0.6))
    px, py = cx + math.cos(road_toward - 0.6) * (cr + 2.0), cy + math.sin(road_toward - 0.6) * (cr + 2.0)
    signpost(m, px, py, ground(px, py), 3, [("sign_to_snow", 0.8), ("sign_to_valley", 3.9)])
    _talkers(c, cx, cy, z0, cr - 2.0, 4, "pilgrim")
    m.build(c, "Snow Lodge", coll="Village", role="visual")
    solid.build(c, "Snow Lodge Solids", coll="Village", role="both")
    taken.add(cx, cy, 4.0)
    return folk.done()


# ------------------------------------------------------------------ the ducks


def ducks(c, L):
    """Families of ducks on the meadow's river (note 17), each paddling up and down its
    own stretch of it (the ducks entity: game/ducks.ts)."""
    riv = L.rivers[0]
    n = 0
    for k, (t0, t1, count) in enumerate(((0.12, 0.3, 4), (0.42, 0.6, 5), (0.68, 0.86, 3))):
        pts = []
        for i in range(8):
            t = lerp(t0, t1, i / 7)
            f = t * (len(riv) - 1)
            j = min(len(riv) - 2, int(f))
            u = f - j
            (ax, ay, az), (bx, by, bz) = riv[j], riv[j + 1]
            x, y, z = lerp(ax, bx, u), lerp(ay, by, u), lerp(az, bz, u)
            side = (2.5 if k % 2 else -2.5) * math.sin(i * 0.9)
            dx, dy = bx - ax, by - ay
            d = math.hypot(dx, dy) or 1.0
            g = c.game(x - dy / d * side, y + dx / d * side, z - 0.1)
            pts.append([round(g[0], 2), round(g[1], 2), round(g[2], 2)])
        c.entity("ducks", points=pts, count=count, seed=11 + k)
        n += count
    return n
