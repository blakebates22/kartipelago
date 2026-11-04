# The Snow Kingdom's sections brought in from their courses (Blake, Oct 30: "I want to
# heavily lean into what is in the levels ... again its all about immersion"):
#
# - Hearthglow: its streets lined with warm cottages, lantern posts between them, presents
#   by the road that burst into a boost, candy canes and baubles.
# - Frostveil: the road walled in on both sides by the citadel's curtain walls, towers at
#   their corners, braziers and banners, arches over the road: inside the castle.
# - Snowy Summit: the deep thaw: green pines, geysers blowing in their sinter cones,
#   steaming terrace pools, ice ponds half melted, steam from the vents, a mammoth herd
#   walking its round in the meadow.
# - Aurora: the dark of the rift lit by lantern posts along the road, crystals flaring by
#   it, crystal gardens and amber clusters, sparkles in the air.
#
# Everything's kept off the road, its side roads and whatever's taken; walls and arches
# stand at the road's shoulders. All our own designs, from the courses' own kits.
# SPDX-License-Identifier: MIT

import math
import random

import aurora_props as ap
import frost_props as fp
import rift_props as rp
import hearthglow_props as hp
import keep_props as kp
import props as pr
import region_paint as paint
import snow_props as snp
import snow_layout as SL
import iceage_props as ia
import summit_props as sp

L = SL.L


def _stretches(c, look, every):
    """The road's samples in a look, every `every` m along it (s, sample)."""
    out = []
    s = 0.0
    while s < c.length:
        q = c.at(s)
        if L.look_at(q.p.x, q.p.y) == look:
            out.append((s, q))
        s += every
    return out


def _off_side_roads(c, x, y, margin):
    return all((q.p.x - x) ** 2 + (q.p.y - y) ** 2 > (q.w / 2 + margin) ** 2 for q in c.extra_ground)


def _game_heading(fx, fy):
    """A Blender direction as a game heading (atan2(dx, dz), game z = -blender y)."""
    return round(math.atan2(fx, -fy), 3)


# ------------------------------------------------------------------ Hearthglow


def hearthglow(c, ground, taken, seat):
    """Presents by the road through Hearthglow (a boost when burst). (Its cottages, lantern
    posts, lights and candy canes are the village's street now: snow_dress.hearthglow;
    its baubles are gone, floating over nothing: Blake, review-snow_region 7.)"""
    st = _stretches(c, "hearth", 6.0)
    n = 0
    for frac, side in ((0.22, 1), (0.5, -1), (0.78, 1)):
        if not st:
            break
        s, q = st[int(frac * (len(st) - 1))]
        x, y = q.p.x + q.r.x * side * (q.w / 2 - 1.6), q.p.y + q.r.y * side * (q.w / 2 - 1.6)
        g = c.game(x, y, ground(x, y))
        c.entity("present", x=g[0], y=g[1], z=g[2], size=2.4, variant=n % 4, heading=_game_heading(q.t.x, q.t.y))
        n += 1
    print("hearthglow presents: %d" % n)


# ------------------------------------------------------------------ Frostveil


# The courtyard opened up (Blake, review-snow_region 8, notes 2-5: "we have too much castle
# wall"): no wall either side of the road here; the Frost Chapel in the open court east,
# the cove carved into the mountain west (snow_layout.FROST_COVE) for the ice dragon under
# its frozen falls.
FROST_OPEN = (-176.0, -40.0, 19.0)  # x, y, radius: the walls stop round it
FROST_CHAPEL = (-151.0, -40.0)  # its middle (its door west, to the road)


def wall_run(c, name, pts, thick=3.0, mat=kp.ASHLAR, merlon=kp.PARAPET):
    """A curtain wall along a run of points [(x, y, z0, z1)]: one continuous body (no gaps
    between lengths, nothing of one through another: Blake, review-snow_region 8, notes 7,
    9, 10), battlements along its outer edge, a walk behind them. Solid."""
    import bmesh
    from props import cuboid

    if len(pts) < 2:
        return 0
    bm = bmesh.new()
    rings = []
    for i, (x, y, z0, z1) in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        tl = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / tl, tx / tl
        h = thick / 2
        rings.append([bm.verts.new((x - nx * h, y - ny * h, z0)), bm.verts.new((x + nx * h, y + ny * h, z0)),
                      bm.verts.new((x + nx * h, y + ny * h, z1)), bm.verts.new((x - nx * h, y - ny * h, z1))])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(4):
            bm.faces.new((r0[k], r1[k], r1[(k + 1) % 4], r0[(k + 1) % 4]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    body = len(bm.faces)
    # (The battlements: every other 2 m along, on the edge away from the road: +normal.)
    run = 0.0
    k = 0
    for i in range(len(pts) - 1):
        (x0, y0, _a, t0), (x1, y1, _b, t1) = pts[i], pts[i + 1]
        seg = math.hypot(x1 - x0, y1 - y0)
        tx, ty = (x1 - x0) / (seg or 1.0), (y1 - y0) / (seg or 1.0)
        nx, ny = -ty, tx
        d = 0.0
        while d < seg:
            if (run + d) // 2.0 > k:
                k = int((run + d) // 2.0)
                if k % 2 == 0:
                    u = d / (seg or 1.0)
                    px, py, pz = x0 + tx * d, y0 + ty * d, t0 + (t1 - t0) * u
                    cuboid(bm, (px + nx * (thick / 2 - 0.3), py + ny * (thick / 2 - 0.3), pz + 0.6), (1.0, 0.6, 1.2),
                           rot=math.atan2(ty, tx))
            d += 0.5
        run += seg
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = c.mesh_object(name, bm, "Village", "both")
    # (The palette the kingdom's keep props are painted in: kp.use_palette.)
    c.assign(ob, c.lib(kp.REMAP.get(mat, mat)), range(body))
    c.assign(ob, c.lib(kp.REMAP.get(merlon, merlon)), range(body, len(ob.data.polygons)))
    return 1


def frostveil(c, ground, taken, keep_clear):
    """The road through Frostveil walled in, inside the castle: on each side one
    continuous curtain wall along the road's shoulder (broken only where something's
    kept clear: the gateways' spurs, the side roads, the opened courtyard), a round tower
    at each end of every run (its end tucked into the tower: nothing left sticking out)
    and every 40 m along it; braziers at its foot, banners on it; arches over the road
    now and then (their gold plaques gone, review-snow_region 8 notes 6, 16, 17)."""
    tower = kp.round_tower(c, r=3.8, h=17.0, variant=0)
    brazier = kp.brazier(c)
    banner = kp.wall_banner(c)
    arch = kp.gate_arch(c, span=c.width + 10.0, clear=10.0, depth=5.0, gold=False)
    st = _stretches(c, "frostveil", 2.0)
    ox, oy, orr = FROST_OPEN
    walls = towers = arches = 0

    def open_at(x, y):
        return (math.hypot(x - ox, y - oy) < orr
                or any(math.hypot(x - cx, y - cy) < cr for cx, cy, cr in keep_clear)
                or not _off_side_roads(c, x, y, 4.0) or not paint.road_clear(c, x, y, 1.2))

    for side in (-1, 1):
        runs, cur, last = [], [], None
        for s, q in st:
            off = q.w / 2 + 3.2
            x, y = q.p.x + q.r.x * side * off, q.p.y + q.r.y * side * off
            if open_at(x, y) or (last is not None and s - last > 3.0):
                if len(cur) > 8:  # (no stubs: a run of 16 m at least, Blake's notes 3 and 4)
                    runs.append(cur)
                cur = []
            if not open_at(x, y):
                cur.append((s, q, x, y))
            last = s
        if len(cur) > 8:
            runs.append(cur)
        for n, run in enumerate(runs):
            pts = [(x, y, min(ground(x, y), q.p.z) - 1.2, q.p.z + 9.5) for s, q, x, y in run]
            walls += wall_run(c, "Frostveil Wall %d %d" % (side, n), pts)
            for _s, _q, x, y in run:
                taken.add(x, y, 2.5)
            # Towers: each end, and every 40 m between.
            ends = [0, len(run) - 1] + list(range(20, len(run) - 10, 20))
            for i in ends:
                s, q, x, y = run[i]
                c.place(tower, x, y, min(ground(x, y), q.p.z) - 2.0, rot=math.atan2(q.t.y, q.t.x), coll="Village")
                taken.add(x, y, 5.0)
                towers += 1
            # Braziers at the wall's foot, banners hung on its face, between the towers.
            for i in range(10, len(run) - 5, 20):
                s, q, x, y = run[i]
                rot = math.atan2(q.t.y, q.t.x)
                bx, by = q.p.x + q.r.x * side * (q.w / 2 + 1.2), q.p.y + q.r.y * side * (q.w / 2 + 1.2)
                if paint.road_clear(c, bx, by, 0.4):
                    c.place(brazier, bx, by, ground(bx, by) - 0.1, rot=rot, coll="Fire")
                    g = c.game(bx, by, ground(bx, by) + 2.8)
                    c.entity("torch", x=g[0], y=g[1], z=g[2])
                wx, wy = q.p.x + q.r.x * side * (q.w / 2 + 1.65), q.p.y + q.r.y * side * (q.w / 2 + 1.65)
                c.place(banner, wx, wy, q.p.z + 3.0, rot=rot + (math.pi if side < 0 else 0.0), coll="Props", role="visual")
    # Arches over the road, where both sides are walled.
    last_arch = -999.0
    for k, (s, q) in enumerate(st):
        if s - last_arch < 70.0 or k == 0 or k == len(st) - 1 or not _off_side_roads(c, q.p.x, q.p.y, 14.0):
            continue
        if any(open_at(q.p.x + q.r.x * sd * (q.w / 2 + 3.2), q.p.y + q.r.y * sd * (q.w / 2 + 3.2)) for sd in (-1, 1)):
            continue
        c.place(arch, q.p.x, q.p.y, q.p.z - 0.3, rot=math.atan2(q.t.y, q.t.x) - math.pi / 2, coll="Props", role="visual")
        last_arch = s
        arches += 1
    frost_chapel(c, ground, taken)
    frost_cove(c, ground, taken)
    print("frostveil streets: %d wall runs, %d towers, %d arches" % (walls, towers, arches))


def frost_chapel(c, ground, taken):
    """The Frost Chapel, in the courtyard opened east of the road (Blake, review-snow_region
    8 note 2: "some spectacular structure"): a tall nave of the citadel's stone, its roof
    steep slate, flying buttresses down its sides, twin spired towers either side of its
    great door, a rose window lit over it and tall lancets down the nave; steps up to the
    door; braziers either side. Its door faces the road (west)."""
    from pocket_build import box

    x, y = FROST_CHAPEL
    rot = 0.0  # (local +X east, along the nave; its front, local -X, west to the road)
    ca, sa = math.cos(rot), math.sin(rot)

    def at(lx, ly):
        return x + lx * ca - ly * sa, y + lx * sa + ly * ca

    z = max(ground(*at(dx, dy)) for dx in (-12.0, 0.0, 12.0) for dy in (-7.0, 0.0, 7.0))
    lo = min(ground(*at(dx, dy)) for dx in (-14.0, 0.0, 14.0) for dy in (-9.0, 0.0, 9.0))
    pal = lambda m: kp.REMAP.get(m, m)  # noqa: E731  (the kingdom's palette: kp.use_palette)
    stone, dark = (pal(kp.ASHLAR), "wall"), (pal(kp.DARK), "wall")
    # (Every part named "Frost Chapel 1 ...": one building, standing on its footing; tests/buildings.)
    box(c, "Frost Chapel 1 Footing", x, y, 13.0, 8.0, lo - 2.0, z + 0.4, dark, rot=rot)
    box(c, "Frost Chapel 1 Nave", x, y, 11.0, 6.0, z, z + 14.0, stone, rot=rot)
    # The roof: a steep gable along the nave.
    import bmesh

    bm = bmesh.new()
    pts = []
    for lx in (-11.6, 11.6):
        for ly, lz in ((-6.8, 13.6), (0.0, 22.0), (6.8, 13.6)):
            px, py = at(lx, ly)
            pts.append(bm.verts.new((px, py, z + lz)))
    a, b = pts[:3], pts[3:]
    bm.faces.new((a[0], b[0], b[1], a[1]))
    bm.faces.new((a[1], b[1], b[2], a[2]))
    bm.faces.new((a[0], a[1], a[2]))
    bm.faces.new((b[2], b[1], b[0]))
    bm.faces.new((a[0], a[2], b[2], b[0]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    c.assign(c.mesh_object("Frost Chapel 1 Roof", bm, "Village", "visual"), c.lib(pal(kp.SLATE)))
    # The front gable over the door, its rose window lit.
    fx, fy = at(-11.1, 0.0)
    bm = bmesh.new()
    ring = []
    for k in range(16):
        aa = k * math.tau / 16
        ring.append(bm.verts.new((fx - 0.12, fy + 3.0 * math.cos(aa), z + 15.5 + 3.0 * math.sin(aa))))
    bm.faces.new(ring)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    c.assign(c.mesh_object("Frost Chapel 1 Rose Window", bm, "Village", "visual"), c.lib("window_warm"))
    # The great door: oak leaves under a pointed arch, iron straps, a stone surround
    # (review-snow_region 12 note 10: "a nice wooden castle door").
    c.place(fp.chapel_door(c, 4.0, 6.1), fx + 0.1, fy, z + 0.4, rot=rot - math.pi / 2, coll="Village", role="visual",
            name="Frost Chapel 1 Door")
    # Lancets down both sides of the nave.
    for k in range(5):
        lx = -7.0 + k * 3.6
        for sd in (-1, 1):
            wx, wy = at(lx, sd * 6.05)
            box(c, "Frost Chapel 1 Lancet %d %d" % (k, sd), wx, wy, 0.6, 0.12, z + 4.0, z + 11.0, ("window_warm", "wall"), rot=rot,
                role="visual")
            # A flying buttress: a pier out from the wall, an arm up to the wall's top.
            px, py = at(lx + 1.8, sd * 9.5)
            box(c, "Frost Chapel 1 Pier %d %d" % (k, sd), px, py, 0.8, 0.8, lo - 0.5, z + 9.0, stone, rot=rot)
            from canyon_props import _beam

            bm = bmesh.new()
            qx, qy = at(lx + 1.8, sd * 6.2)
            _beam(bm, (px, py, z + 9.0), (qx, qy, z + 13.0), 0.45)
            c.assign(c.mesh_object("Frost Chapel 1 Buttress %d %d" % (k, sd), bm, "Village", "visual"), c.lib(pal(kp.ASHLAR)))
    # The twin towers either side of the door, their spires.
    tower = kp.round_tower(c, r=3.2, h=24.0, variant=1)
    for sd in (-1, 1):
        tx, ty = at(-9.8, sd * 7.6)
        c.place(tower, tx, ty, lo - 1.0, rot=rot, coll="Village")
    # Steps up to the door, braziers either side.
    for k in range(3):
        sx_, sy_ = at(-12.4 - k * 0.9, 0.0)
        box(c, "Frost Chapel 1 Step %d" % k, sx_, sy_, 0.5, 3.4, lo - 0.5, z + 0.4 - 0.45 * (k + 1), stone, rot=rot)
    for sd in (-1, 1):
        bx, by = at(-14.5, sd * 4.2)
        c.place(kp.brazier(c), bx, by, ground(bx, by) - 0.1, coll="Fire")
        g = c.game(bx, by, ground(bx, by) + 2.8)
        c.entity("torch", x=g[0], y=g[1], z=g[2])
    taken.add(x, y, 16.0)


def frost_cove(c, ground, taken):
    """The cove carved back into the mountain west of the road (Blake, review-snow_region 8
    note 5: "have something brilliant back here"): a great frozen waterfall down its back
    wall, the ice in tall fluted columns from the lip to the floor, a frozen pool at its
    foot, and the carvers' ice dragon on a stone plinth before it, rearing over the road."""
    import bmesh
    from props import tube

    cx, cy, cr, cz = SL.FROST_COVE
    # The frozen falls: fluted columns down the cove's back wall (west), the lip up top.
    bx = cx - cr + 1.0
    top = ground(bx - 6.0, cy) - 0.5
    bm = bmesh.new()
    for k in range(13):
        u = (k - 6) / 6.0
        y = cy + u * 9.0
        w = 1.2 + 0.5 * math.cos(k * 1.7)
        x0 = bx - 1.0 + 1.6 * (1 - u * u)
        tube(bm, [(x0 - 2.0, y, top + 1.0), (x0 - 0.5, y, top - 1.5), (x0 + 0.6 + 0.3 * math.sin(k), y, (top + cz) / 2),
                  (x0 + 1.4, y, cz + 2.0), (x0 + 2.2, y, cz - 0.2)], [w * 0.8, w, w * 1.1, w * 1.25, w * 1.4], n=7)
    c.assign(c.mesh_object("Frost Cove Falls", bm, "Village", "both"), c.lib("glacier_ice"))
    c.disc("Frost Cove Pool", bx + 6.0, cy, 7.0, cz + 0.05, c.lib("lake_ice", "ice"), coll="Village", role="both", n=24)
    # The ice dragon on its plinth, before the falls, facing the road (east).
    dx, dy = cx + 2.0, cy
    # (Finer, on a finer pedestal: review-snow_region 12 note 9.)
    dz = min(ground(dx + 4.9 * math.cos(a), dy + 4.9 * math.sin(a)) for a in [k * 0.785 for k in range(8)])
    c.place(fp.ice_dragon(c), dx, dy, dz - 0.1, rot=-math.pi / 2, scale=1.5, coll="Village")
    taken.add(cx, cy, cr)


# ------------------------------------------------------------------ Snowy Summit

HOT_SPRING = (-84.9, 152.2)  # where to look for the hot spring's level ground (note 24; where it stood, note 11)
CAMP = (-176.0, 62.0)  # the hunters' camp: its fire, in the bay west of the climb (note 19)
CAIRNS = (70.0, 130.0)  # the climb: the camp is looked for between these (blender y)


def summit(c, ground, taken, ter=None):
    """The deep thaw: ice ponds half melted, a hot spring steaming in the snow, a
    mammoth's skull frozen in the lake, green pines (the region's scatter), the mammoth
    herd on its round in the meadow; the hunters' camp up the climb; geysers.
    (No terrace pools; the geyser in the wall gone, review-snow_region 9 note 20, and
    geysers where Blake pinned them instead, review-snow_region 10.)"""
    rng = random.Random(53)
    pockets = [p for p in SL.POCKETS if p[0] in ("summit", "climb")]
    circles = [ci for p in pockets for ci in p[2]]
    lx, ly, lr, lz = SL.LAKE
    ponds = 0

    def spot(room, margin, tries=200):
        for _ in range(tries):
            cx, cy, cr, _f = circles[rng.randrange(len(circles))]
            a = rng.uniform(0, math.tau)
            r = cr * math.sqrt(rng.random())
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            if L.pocket_at(x, y) not in ("summit", "climb") or L.wall_sd(x, y) > -8.0:
                continue
            if math.hypot(x - lx, y - ly) < lr + 6.0:
                continue
            if not taken.clear(x, y, room) or not paint.road_clear(c, x, y, margin):
                continue
            ring = [ground(x + room * 0.6 * math.cos(t), y + room * 0.6 * math.sin(t)) for t in (0, 1.57, 3.14, 4.71)]
            if max(ring) - min(ring) > 2.5:
                continue
            return x, y, min(ring)
        return None

    # The mammoths' round: a loop through the meadow, on the ground, off the road.
    pts = []
    mx, my = -60.0, 186.0
    # (Drawn in wherever it would climb a wall or a bank: the meadow's floor only, review-
    # snow_region 9 notes 18, 23, "mammoths shouldnt be able to go up here".)
    z0 = ground(mx, my)
    for k in range(36):
        a = k * math.tau / 36
        for f in (1.0, 0.92, 0.84, 0.76, 0.68, 0.6, 0.52, 0.44, 0.36):
            x, y = mx + f * (30.0 * math.cos(a) + 5.0 * math.sin(3 * a)), my + f * 14.0 * math.sin(a)
            if L.wall_sd(x, y) < -10.0 and abs(ground(x, y) - z0) < 3.0 and paint.road_clear(c, x, y, 5.0):
                break
        pts.append((x, y, ground(x, y)))
    c.path_curve("Mammoth Path", pts, closed=True)
    for k, (scale, start) in enumerate(((1.0, 0.0), (0.6, 12.0), (0.95, 70.0), (0.55, 82.0))):
        c.entity("dinosaur", route="Mammoth Path", speed=1.5, scale=scale, model="mammoth", start=start)
    # (The hot spring and the geysers first, where Blake pinned them: the rest fit round.)
    springs = hot_spring(c, ground, taken, ter)
    blown = geysers(c, ground, taken, ter, avoid=pts)
    # Ice ponds, half melted: a ring of thin ice round dark open water, floes in it.
    for k in range(5):
        p = spot(8.0, 8.0)
        if not p:
            continue
        x, y, z = p
        r = rng.uniform(5.0, 7.0)
        c.disc("Thaw Pond Ice %d" % k, x, y, r, z + 0.06, c.lib("lake_ice", "ice"), coll="Props", role="visual", n=24, wobble=0.12,
               seed=k)
        c.disc("Thaw Pond Water %d" % k, x + 0.6, y - 0.4, r * 0.58, z + 0.09, c.lib("hot_pool", "water"), coll="Props", role="visual",
               n=20, wobble=0.18, seed=k + 9)
        for j in range(3):
            a = rng.uniform(0, math.tau)
            fx, fy = x + 0.6 + r * 0.3 * math.cos(a), y - 0.4 + r * 0.3 * math.sin(a)
            c.place(sp.floe(c, j % 2), fx, fy, z + 0.05, rot=a, scale=0.45, coll="Props", role="visual")
        g = c.game(x, y, z + 0.3)
        c.entity("steam", x=g[0], y=g[1], z=g[2])
        taken.add(x, y, r + 1.0)
        ponds += 1
    frozen_skull(c, ground, taken)
    camp = climb_camp(c, ground, taken, ter)
    print("snowy summit: %d ponds, %d hot springs, the skull, camp %d, %d geysers, 4 mammoths" % (ponds, springs, camp, blown))


# Where the geysers blow (review-snow_region 10, Nov 1: notes 1, 7, "I still want a couple
# of geysers here. I just meant to remove the geyser that was literally in the wall";
# note 10, "a couple of big geysers up here", on the high meadow over the wall): the pins,
# blender (x, y), how many, how big, and whether they're up out of the play area.
GEYSERS = [((-96.5, 164.8), 2, 0.85, False), ((-45.0, 133.7), 1, 0.8, False), ((-97.3, 228.1), 2, 1.6, True)]


def geysers(c, ground, taken, ter=None, avoid=()):
    """Geysers in their sinter cones, each well out of the walls and off the road, on
    ground cut level for it, blowing in turns; steam from vents round them."""
    n = 0
    homes = [(e["x"], -e["z"]) for e in c.entities if e["type"] == "villager_home"]
    for (px, py), count, big, up in GEYSERS:
        got = 0
        for k in range(900):
            if got >= count:
                break
            a = k * 2.399
            r = 1.2 * math.sqrt(k)
            x, y = px + r * math.cos(a), py + r * math.sin(a)
            room = 6.0 * big
            # (Down in the meadow: well inside the walls. Up on the high meadow: well back
            # from its edge, out of the walls' slopes.)
            sd = L.wall_sd(x, y)
            if (sd < 9.0 + room) if up else (sd > -(6.0 + room)):
                continue
            if not paint.road_clear(c, x, y, room + 0.8) or not taken.clear(x, y, room):
                continue
            if any(math.hypot(x - ax, y - ay) < room + 2.5 for ax, ay, _ in avoid):
                continue  # (off the mammoths' round)
            if any(math.hypot(x - hx, y - hy) < room + 7.0 for hx, hy in homes):
                continue  # (clear of the huts)
            ring = [ground(x + room * math.cos(t), y + room * math.sin(t)) for t in [j * 0.785 for j in range(8)]]
            if max(ring) - min(ring) > 2.0:
                continue
            z = min(ring)
            if ter is not None and not up:
                paint.grade(c, ter, x, y, 0.0, room * 2.0, room * 2.0, z)
            v = (n + got) % 3
            c.place(sp.geyser_cone(c, v, white=True), x, y, z - 0.3, rot=1.7 * (n + got), scale=big, coll="Props")
            taken.add(x, y, room)
            g = c.game(x, y, z - 0.3 + (2.4 + 0.6 * v) * big)
            c.entity("geyser", x=g[0], y=g[1], z=g[2], r=3.5 * big, height=(16.0 + 4.0 * v) * big, period=8.0 + v + got,
                     offset=1.7 * (n + got), warn=1.4, blast=2.2 * big, launch=0.0)
            for j in range(2):
                b = 1.3 + j * 2.6 + got
                vx, vy = x + (room + 1.5) * math.cos(b), y + (room + 1.5) * math.sin(b)
                if paint.road_clear(c, vx, vy, 3.0) and L.wall_sd(vx, vy) < (99 if up else -4.0):
                    g = c.game(vx, vy, ground(vx, vy) + 0.2)
                    c.entity("steam", x=g[0], y=g[1], z=g[2])
            print("geyser at (%.0f, %.0f) x%.1f" % (x, y, big))
            got += 1
        if got < count:
            print("geysers: only %d of %d by (%.0f, %.0f)" % (got, count, px, py))
        n += got
    return n


def hot_spring(c, ground, taken, ter=None):
    """A hot spring by the road below the lookout (review-snow_region 9 note 24, "this
    section needs more flare ... maybe a hot spring pool"): on level snow, off the road,
    steam rising, a tent and a hide rack by it."""
    best = None
    why = [0, 0, 0, 0]
    for k in range(700):
        a = k * 2.399
        r = 1.5 * math.sqrt(k)
        x, y = HOT_SPRING[0] + r * math.cos(a), HOT_SPRING[1] + r * math.sin(a)
        if L.wall_sd(x, y) > -12.0:
            why[0] += 1
            continue
        if not paint.road_clear(c, x, y, 7.5):
            why[1] += 1
            continue
        if not taken.clear(x, y, 5.2):
            why[2] += 1
            continue
        ring = [ground(x + 7.0 * math.cos(t), y + 7.0 * math.sin(t)) for t in [j * 0.785 for j in range(8)]]
        if max(ring) - min(ring) > 3.5:
            why[3] += 1
            continue
        best = (x, y, min(ring))
        break
    if not best:
        print("hot spring: no room (walls, road, taken, slope)", why)
        return 0
    x, y, z = best
    # (Its ground cut level at the lowest of its rim first: the water in the basin, not
    # under the snow.)
    if ter is not None:
        paint.grade(c, ter, x, y, 0.0, 19.0, 19.0, z)
        z = min([ground(x + 4.0 * math.cos(t), y + 4.0 * math.sin(t)) for t in [j * 0.785 for j in range(8)]] + [ground(x, y)])
    print("hot spring at (%.0f, %.0f)" % (x, y), why)
    # (Sunk to the lowest of its rim: the basin's outside runs 1.2 m down into the snow.)
    # (Its water is its own: a lopsided pool, review-snow_region 10 note 11.)
    c.place(ia.hot_spring(c, 4.2), x, y, z + 0.1, rot=0.4, coll="Props")
    # (No cone of steam over it: review-snow_region 16 note 2, "this weird cone steam effect
    # that looks weird. lets remove it"; the steam puffs rise off it.)
    taken.add(x, y, 8.0)
    for j in range(5):
        a = j * 1.26 + 0.3
        g = c.game(x + 2.8 * math.cos(a), y + 2.8 * math.sin(a), z + 0.4)
        c.entity("steam", x=g[0], y=g[1], z=g[2])
    return 1


def frozen_skull(c, ground, taken):
    """A mammoth's skull frozen in the lake, off its middle (note 21)."""
    lx, ly, lr, lz = SL.LAKE
    x, y = lx - lr * 0.25, ly + lr * 0.2
    c.place(ia.frozen_skull(c), x, y, lz, rot=-0.9, scale=1.25, coll="Props")
    taken.add(x, y, 9.0)


def climb_camp(c, ground, taken, ter=None):
    """The climb between the snowy pass and Frostveil (review-snow_region 9 note 19:
    "this strip ... is boring. lets add something here. nothing crazy, but something"):
    a hunters' camp in the bay west of the road (two hide tents, a fire, a hide rack, a
    sled)."""
    n = 0

    def flat(x, y, r):
        hs = [ground(x + r * math.cos(t), y + r * math.sin(t)) for t in [j * 0.785 for j in range(8)]] + [ground(x, y)]
        return max(hs) - min(hs)

    # (The levellest ground off the road in the bay, nearest CAMP.)
    best = None
    why = [0, 0, 0, 99.0, 0]
    for s, q in _stretches(c, "summit", 2.0):
        why[4] += 1
        if not (CAIRNS[0] - 20 <= q.p.y <= CAIRNS[1]) or q.p.x > -100:
            continue
        for sd in (-1, 1):
            for off in (6.0, 8.0, 10.0, 12.0, 14.0):
                x, y = q.p.x + q.r.x * sd * (q.w / 2 + off), q.p.y + q.r.y * sd * (q.w / 2 + off)
                if L.wall_sd(x, y) > -5.0:
                    why[0] += 1
                    continue
                if not paint.road_clear(c, x, y, 4.5):
                    why[1] += 1
                    continue
                if not taken.clear(x, y, 5.0):
                    why[2] += 1
                    continue
                f = flat(x, y, 4.0)
                why[3] = min(why[3], f)
                if f < 3.0:
                    score = f + 0.02 * math.hypot(x - CAMP[0], y - CAMP[1])
                    if best is None or score < best[0]:
                        best = (score, x, y)
    if best is None:
        print("camp: no room (walls, road, taken, flattest, samples)", why)
        return 0
    cx, cy = best[1], best[2]
    # (Its ground cut and filled level first: the overworld rules, nothing set into a slope.)
    hs = [ground(cx + 6.5 * math.cos(t), cy + 6.5 * math.sin(t)) for t in [j * 0.785 for j in range(8)]]
    if ter is not None:
        paint.grade(c, ter, cx, cy, 0.0, 14.0, 14.0, (min(hs) + max(hs)) / 2)
    print("camp at (%.0f, %.0f), %.1f m levelled" % (cx, cy, max(hs) - min(hs)))
    tents = [ia.hide_tent(c, v) for v in range(2)]
    pieces = [(tents[0], -3.5, 2.5, 0.9), (tents[1], 3.0, 3.5, -0.6), (ia.hide_rack(c), 0.5, -3.8, 0.2)]
    def level(x, y, r):
        """The lowest of the ground round (x, y) at r, or None where it's not level."""
        hs = [ground(x + r * math.cos(t), y + r * math.sin(t)) for t in [j * 0.785 for j in range(8)]] + [ground(x, y)]
        return min(hs) if max(hs) - min(hs) < 1.2 else None

    for proto, dx, dy, rot in pieces:
        x, y = cx + dx, cy + dy
        if L.wall_sd(x, y) > -4.5 or not paint.road_clear(c, x, y, 3.2) or not taken.clear(x, y, 2.5):
            continue
        z = level(x, y, 2.2)
        if z is None:
            continue
        c.place(proto, x, y, z, rot=rot, coll="Village")
        taken.add(x, y, 3.0)
        n += 1
    if paint.road_clear(c, cx, cy, 1.8) and level(cx, cy, 1.5) is not None:
        c.place(pr.campfire(c), cx, cy, ground(cx, cy), coll="Fire", role="visual")
        g = c.game(cx, cy, ground(cx, cy) + 1.2)
        c.entity("torch", x=g[0], y=g[1], z=g[2])
        taken.add(cx, cy, 2.0)
        n += 1
    x, y = cx - 2.0, cy - 6.5
    if paint.road_clear(c, x, y, 2.0) and taken.clear(x, y, 2.0) and level(x, y, 1.6) is not None:
        c.place(snp.sled(c, 0), x, y, level(x, y, 1.6), rot=0.5, coll="Props")
        taken.add(x, y, 2.0)
    # (No cairns up the climb: review-snow_region 10 note 5, "lets remove these rock props".)
    return n


# ------------------------------------------------------------------ Aurora


def aurora(c, ground, taken):
    """Lantern posts along the road through the rift (the course's own), crystal fans and
    amber clusters by it, crystal gardens back from it, sparkles in the air."""
    post = ap.lantern_post(c, 0)
    fans = [ap.fan(c, v, size=6.0) for v in range(3)]
    amber = ap.amber_cluster(c, 0, size=4.0)
    n = 0
    for k, (s, q) in enumerate(_stretches(c, "aurora", 14.0)):
        side = 1 if k % 2 else -1
        x, y = q.p.x + q.r.x * side * (q.w / 2 + 1.8), q.p.y + q.r.y * side * (q.w / 2 + 1.8)
        if taken.clear(x, y, 1.0) and paint.road_clear(c, x, y, 1.0) and _off_side_roads(c, x, y, 1.0):
            z = ground(x, y)
            c.place(post, x, y, z - 0.1, rot=math.atan2(q.t.y, q.t.x), coll="Props", role="visual")
            c.place(paint.trunk_proto(c, 0.3, 4.0), x, y, z, coll="Collision", role="collision")
            g = c.game(x, y, z + 3.4)
            c.entity("lantern", x=g[0], y=g[1], z=g[2])
            taken.add(x, y, 1.2)
            n += 1
        if k % 2 == 0:
            # (Grown out of the foot of the rift's wall, their roots in it, fanned out toward
            # the road: review-snow_region 13 note 4, "move this so the base is more into
            # the wall". Out from the road till the wall rises.)
            ux, uy = q.r.x * -side, q.r.y * -side
            z0 = ground(q.p.x + ux * (q.w / 2 + 2.0), q.p.y + uy * (q.w / 2 + 2.0))
            spot = None
            for ox in [q.w / 2 + 3.0 + 0.5 * j for j in range(30)]:
                x, y = q.p.x + ux * ox, q.p.y + uy * ox
                if ground(x, y) > z0 + 1.6 or L.wall_sd(x, y) > -2.0:
                    spot = (x + ux * 0.6, y + uy * 0.6)
                    break
            proto = amber if k % 6 == 0 else fans[k % 3]
            if spot and taken.clear(spot[0], spot[1], 2.5) and paint.road_clear(c, spot[0], spot[1], 2.5):
                x, y = spot
                z = min(ground(x + 1.5 * math.cos(a), y + 1.5 * math.sin(a)) for a in [j * 0.785 for j in range(8)])
                c.place(proto, x, y, z - 0.9, rot=math.atan2(ux, -uy), coll="Props", role="visual")
                taken.add(x, y, 3.0)
    c.entity("area_ambient", area="aurora", effect="sparkles", rate=14, radius=34, colors=["#9ef3ff", "#c9a2ff", "#ffffff"])
    print("aurora: %d lantern posts" % n)


# review-snow_region 13 (Nov 1), Blake's pins (blender x, y):
CRYSTAL_HUT = (165.4, 46.7)  # note 2: "a nice crystal hut with npcs ... like they built a home from the crystals"
RIFT_FIRE = (95.5, 122.5)  # note 7: "a little fire here with some stump chairs around it"
OUTPOST = (84.7, -401.9)  # note 1: "a little outpost here with some npcs they are about to pilgramige to dino valley"
# (review-snow_region 14 note 10: "mover the little pilgram camp right here. flatten it if
# needed and make sure nothing is floating or buried in the snow": it had wandered 30 m off,
# to (97, -416).)
OUTPOST = (84.7, -389.9)
# (review-snow_region 15 notes 9, 10: "shift this whole cmap over. the tent is half way off the
# stone and the rocks are floating", "this needs to be higher up by the tents": it stood by the
# road, whose verge the levelling can't cut; 14 m out east of it, the ground's near level.)
OUTPOST = (94.4, -382.5)


def _level_spot(c, ground, taken, x0, y0, room, slope, rmax=20.0, wall=None, margin=None):
    """The nearest spot to (x0, y0) with `room` clear and level to within `slope` (a spiral
    out), with the lowest ground under it, or None."""
    why = [0, 0, 0, 99.0]
    for k in range(2000):
        a, d = k * 2.399, 0.55 * math.sqrt(k)
        if d > rmax:
            break
        x, y = x0 + d * math.cos(a), y0 + d * math.sin(a)
        if wall is not None and L.wall_sd(x, y) > wall:
            why[0] += 1
            continue
        if not taken.clear(x, y, room):
            why[1] += 1
            continue
        if not paint.road_clear(c, x, y, room if margin is None else margin):
            why[2] += 1
            continue
        hs = [ground(x, y)] + [ground(x + room * math.cos(t), y + room * math.sin(t)) for t in [j * 0.785 for j in range(8)]]
        why[3] = min(why[3], max(hs) - min(hs))
        if max(hs) - min(hs) <= slope:
            return x, y, min(hs)
    print("  no level spot by (%.0f, %.0f): walls, taken, road, flattest" % (x0, y0), why)
    return None


def _face(c, x, y):
    """A prop's front (-Y) turned to the nearest road."""
    q, _ = c.nearest(x, y)
    return math.atan2(q.p.y - y, q.p.x - x) + math.pi / 2


def rift_folk(c, ground, taken, ter=None):
    """The crystal hut and its folk (note 2), a fire with stump seats round it (note 7)."""
    import props as pr

    spot = _level_spot(c, ground, taken, *CRYSTAL_HUT, 6.0, 2.5, wall=-6.0, margin=4.0)
    print("rift: the crystal hut at", spot and (round(spot[0]), round(spot[1])))
    if spot:
        x, y, z = spot
        if ter is not None:
            paint.grade(c, ter, x, y, 0.0, 13.0, 13.0, z)
        rot = _face(c, x, y)
        c.place(rp.crystal_hut(c, 0), x, y, z, rot=rot, coll="Village", name="Crystal Hut 1")
        taken.add(x, y, 7.0)
        fx, fy = x + 6.5 * math.sin(rot), y - 6.5 * math.cos(rot)  # (before its door)
        g = c.game(fx, fy, ground(fx, fy))
        c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=9.0, n=3, folk="snow",
                 heading=round(-rot, 3))
        g = c.game(x, y, z + 6.0)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
    spot = _level_spot(c, ground, taken, *RIFT_FIRE, 3.6, 1.0, wall=-3.0, margin=3.0)
    print("rift: the fire at", spot and (round(spot[0]), round(spot[1])))
    if spot:
        # (Levelled first, filled up to its highest ground, and the fire's stones and the
        # stumps set on it: they stood sunk in the mirror ice, Blake, review-snow_region 14
        # note 6, "the rocks around the fire and the stumps are below the ice".)
        x, y, _ = spot
        z = max([ground(x, y)] + [ground(x + r * math.cos(t), y + r * math.sin(t)) for r in (1.5, 3.0) for t in [i * 0.785 for i in range(8)]])
        if ter is not None:
            paint.grade(c, ter, x, y, 0.0, 7.0, 7.0, z)
        z = ground(x, y)
        c.place(pr.campfire(c), x, y, z + 0.02, coll="Fire", role="visual")
        g = c.game(x, y, z + 1.2)
        c.entity("torch", x=g[0], y=g[1], z=g[2])
        for j in range(4):
            a = j * math.tau / 4 + 0.4
            sx, sy = x + 2.5 * math.cos(a), y + 2.5 * math.sin(a)
            sz = max(ground(sx + 0.5 * math.cos(t), sy + 0.5 * math.sin(t)) for t in [i * 1.047 for i in range(6)])
            c.place(rp.stump_seat(c, j % 3), sx, sy, sz - 0.05, rot=a, coll="Props")
        taken.add(x, y, 3.8)
        g = c.game(x, y, z)
        c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=5.0, n=2, folk="snow", heading=0.0)


def outpost(c, ground, taken, ter=None):
    """The pilgrims' outpost on the crest over the way down to the Burnt Gorge (note 1):
    two hide tents, a fire, a loaded sled, a woodpile, and the snow folk packed for the
    long walk to Dino Valley (the "pilgrim" folk)."""
    import props as pr
    import snow_props as snp

    # (The nearest spot with room off the road, levelled by filling up to its highest
    # ground, never cutting: the grade's never cut near a road, so a cut left the road's
    # side of the camp standing proud of it.)
    spot = _level_spot(c, ground, taken, *OUTPOST, 7.5, 3.0, rmax=6.0, margin=9.0)
    print("outpost at", spot and (round(spot[0]), round(spot[1])), "(pin %.0f, %.0f)" % OUTPOST)
    if not spot:
        return 0
    x, y, _ = spot
    z = max([ground(x, y)] + [ground(x + r * math.cos(t), y + r * math.sin(t)) for r in (4.0, 8.0) for t in [j * 0.785 for j in range(8)]])
    if ter is not None:
        paint.grade(c, ter, x, y, 0.0, 17.0, 17.0, z)
    print("  levelled to %.2f: %.2f..%.2f under it" % (z, min(ground(x + 7.0 * math.cos(t), y + 7.0 * math.sin(t)) for t in [j * 0.785 for j in range(8)]),
                                                     max(ground(x + 7.0 * math.cos(t), y + 7.0 * math.sin(t)) for t in [j * 0.785 for j in range(8)])))
    rot = _face(c, x, y)
    cs, sn = math.cos(rot), math.sin(rot)

    def at(lx, ly):
        return x + lx * cs - ly * sn, y + lx * sn + ly * cs

    for proto, lx, ly, turn, coll in ((ia.hide_tent(c, 0), -3.8, 2.4, 0.5, "Village"), (ia.hide_tent(c, 1), 3.6, 3.0, -0.6, "Village"),
                                      (snp.sled(c, 1), 5.6, 0.2, 1.9, "Props"), (ia.camp_woodpile(c), -4.4, -1.8, 0.3, "Props"),
                                      (ia.camp_pots(c, 1), -1.6, 4.4, 0.0, "Props"), (ia.hide_rack(c), 0.4, 5.6, 0.0, "Props")):
        px, py = at(lx, ly)
        c.place(proto, px, py, ground(px, py) - 0.05, rot=rot + turn, coll=coll)
    c.place(pr.campfire(c), x, y, ground(x, y), coll="Fire", role="visual")
    g = c.game(x, y, ground(x, y) + 1.2)
    c.entity("torch", x=g[0], y=g[1], z=g[2])
    for j in range(3):
        a = j * math.tau / 3 - 0.6
        sx, sy = x + 2.4 * math.cos(a), y + 2.4 * math.sin(a)
        c.place(rp.stump_seat(c, j), sx, sy, ground(sx, sy), rot=a, coll="Props")
    taken.add(x, y, 9.0)
    g = c.game(x, y, ground(x, y))
    c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=9.0, n=4, folk="pilgrim",
             heading=round(-rot, 3))
    return 1
