# Riverbend Palms v2.2: Blake's first review round (reviews/riverbend_palms/, his notes
# from the in-game review tool), built on v2.1 (kept playable as riverbend_palms_v21).
# SPDX-License-Identifier: MIT
#
#   rocks       many shapes of boulder (round, standing stones, slabs, split, mossy),
#               tilted and turned, and a few more of them
#   villages    dirt paths from every hut door to its fire, from each fire out to the
#               road, and between neighbouring hamlets; realistic campfires (a charred
#               bed, a teepee of logs, layered flames) with flickering light
#   volcano     the dark mountain beyond the walls is a proper volcano: a glowing
#               crater, lava streaks and a plume of smoke
#   walls       green ledges with shrubs and ferns all round the valley walls
#   landmarks   a light sandstone rock feature on the open east meadow, a grand rock
#               pillar east of the river, and a natural stone arch over the river you
#               can drive across (off the race line, for exploring)
#   driving     a little kicker on the ridge corner for a hop over the grass, and a
#               narrow footpath you can drive on without slowing (its own look)
#   creatures   a family of gentle long-necks grazing round the meadows (only the big
#               one crosses the road)
#
# Positions come from the notes: the game's (x, y, z) is Blender's (x, -z, y).
# All original designs, in the spirit of late-90s console scenery.

import math

import course_kit as kit
import props
from course_kit import Vector, bmesh, rnd
from props import _faces, blob, ring, loft, tube


def B(gx, gy, gz):
    """A point from the game (x, y up, z) in Blender (x, y, z up)."""
    return (gx, -gz, gy)


# ---------------------------------------------------------------- rocks


def boulder_shape(c, variant):
    """One of eight boulder shapes: round lumps, a standing stone, flat slabs, a split
    rock and craggy ones, some with moss on top (origin at the foot)."""
    name = "River Boulder %d" % variant
    kind = variant % 4
    mossy = variant >= 4

    def build(bm):
        if kind == 3:
            # Split: two lumps leaning apart.
            for side in (-1, 1):
                res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.9)
                for i, v in enumerate(res["verts"]):
                    k = 0.8 + 0.4 * rnd(i * 2.3 + variant * 11 + side)
                    v.co = Vector((v.co.x * k * 0.75 + side * 0.62, v.co.y * k, v.co.z * k * 1.05 + 0.6 + 0.12 * side * v.co.x))
        else:
            res = bmesh.ops.create_icosphere(bm, subdivisions=2 if kind == 0 else 1, radius=1.0)
            sx, sy, sz, lift = ((1.15, 1.0, 0.78, 0.3), (0.62, 0.55, 1.9, 1.6), (1.7, 1.25, 0.42, 0.2))[kind]
            for i, v in enumerate(res["verts"]):
                k = 0.78 + 0.44 * rnd(i * 3.7 + variant * 19)
                # Craggier at the top of standing stones, flatter on slabs.
                v.co = Vector((v.co.x * k * sx, v.co.y * k * sy, v.co.z * k * sz + lift))
        faces = _faces(bm, 0)
        bm.normal_update()
        if not mossy:
            return [(c.lib("valley_cliff" if variant % 2 == 0 else "canyon_rock_ochre"), faces)]
        top = [i for i, f in enumerate(bm.faces) if f.normal.z > 0.55]
        rest = [i for i in faces if i not in set(top)]
        return [(c.lib("canyon_rock_ochre" if variant % 2 else "valley_cliff"), rest), (c.lib("canyon_rock_moss"), top)]

    return c.proto(name, build) and name


def scatter_boulders(c, ter, ok, count=6):
    """Eight shapes, `count` of each, at random turns and tilts (so no two look alike)."""
    placed = []
    for v in range(8):
        proto = boulder_shape(c, v)
        for x, y in props.scatter(c, proto, count, (-220, 220, -220, 220), ok, ter, seed=150 + v * 7, scale=(0.9, 3.0)):
            placed.append((x, y))
    me = {c.protos["River Boulder %d" % v] for v in range(8)}
    k = 0
    for ob in kit.bpy.data.objects:
        if ob.data in me:
            k += 1
            ob.rotation_euler = (0.25 * (rnd(k * 1.7) - 0.5), 0.25 * (rnd(k * 2.9) - 0.5), ob.rotation_euler[2])
    return placed


# ---------------------------------------------------------------- villages


def campfire_v2(c):
    """A campfire you'd believe: a bed of ash and glowing coals inside a ring of stones,
    a teepee of logs, and flames in layers (orange outside, yellow inside) leaning up
    into a point."""
    name = "Campfire v2"

    def build(bm):
        # Ash and coals: a low disc.
        rim = ring(bm, (0, 0), 1.05, 0.06, 12)
        mid = bm.verts.new((0, 0, 0.1))
        for i in range(12):
            bm.faces.new((rim[i], rim[(i + 1) % 12], mid))
        coals = _faces(bm, 0)
        k0 = len(bm.faces)
        for i in range(11):
            a = i * math.tau / 11 + 0.2 * rnd(i)
            r = 1.3 + 0.1 * rnd(i * 3)
            blob(bm, (r * math.cos(a), r * math.sin(a), 0.14), 0.28 + 0.1 * rnd(i * 5), sx=1.3, sz=0.7, subdiv=1)
        stones = _faces(bm, k0)
        k1 = len(bm.faces)
        for i in range(6):
            a = i * math.tau / 6 + 0.3
            ca, sa = math.cos(a), math.sin(a)
            tube(bm, [(1.0 * ca, 1.0 * sa, 0.1), (0.12 * ca, 0.12 * sa, 1.25)], 0.11, n=6)
        logs = _faces(bm, k1)
        k2 = len(bm.faces)

        def tongue(cx, cy, w, h, a, lean):
            base = [bm.verts.new((cx + w * math.cos(k * math.tau / 6 + a), cy + w * math.sin(k * math.tau / 6 + a), 0.2)) for k in range(6)]
            waist = [bm.verts.new((cx * 0.7 + w * 0.6 * math.cos(k * math.tau / 6 + a + 0.3), cy * 0.7 + w * 0.6 * math.sin(k * math.tau / 6 + a + 0.3), 0.2 + h * 0.5)) for k in range(6)]
            tip = bm.verts.new((cx * 0.3 + lean * math.cos(a), cy * 0.3 + lean * math.sin(a), 0.2 + h))
            for k in range(6):
                bm.faces.new((base[k], base[(k + 1) % 6], waist[(k + 1) % 6], waist[k]))
                bm.faces.new((waist[k], waist[(k + 1) % 6], tip))

        for i, (r, w, h) in enumerate(((0.0, 0.55, 2.2), (0.35, 0.38, 1.6), (0.38, 0.36, 1.4), (0.32, 0.34, 1.7), (0.4, 0.3, 1.2))):
            a = i * 2.4
            tongue(r * math.cos(a), r * math.sin(a), w, h, a, 0.18)
        outer = _faces(bm, k2)
        k3 = len(bm.faces)
        for i, (r, w, h) in enumerate(((0.0, 0.32, 1.5), (0.2, 0.22, 1.05), (0.22, 0.2, 0.95))):
            a = i * 2.1 + 1
            tongue(r * math.cos(a), r * math.sin(a), w, h, a, 0.1)
        inner = _faces(bm, k3)
        return [(c.lib("ember_ash"), coals), (c.lib("valley_cliff"), stones), (c.lib("palm_bark"), logs),
                (c.lib("campfire_flame"), outer), (c.lib("brazier_fire"), inner)]

    return c.proto(name, build) and name


def path_strip(c, name, pts, ter, width=2.2, mat=("jungle_path", "grass"), lift=0.12):
    """A dirt path laid on the ground along (x, y) points, a little wavy and uneven at
    its edges (visual only: you drive on the grass under it)."""
    # Resample every ~1.6 m so it follows the ground.
    dense = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 1.6))
        for k in range(n):
            t = k / n
            dense.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    dense.append(pts[-1])
    if len(dense) < 2:
        return None
    rows = []
    along = 0.0
    for i, (x, y) in enumerate(dense):
        a = dense[max(0, i - 1)]
        b = dense[min(len(dense) - 1, i + 1)]
        d = Vector((b[0] - a[0], b[1] - a[1], 0)).normalized()
        r = Vector((d.y, -d.x, 0))
        if i:
            along += math.hypot(x - dense[i - 1][0], y - dense[i - 1][1])
        w = width * (0.85 + 0.3 * rnd(i * 1.7 + len(name)))
        row = []
        for u in (-0.5, 0.0, 0.5):
            px, py = x + r.x * u * w, y + r.y * u * w
            z = c.ground_z(px, py, ter)
            if z is None:
                return None
            row.append((Vector((px, py, z + lift)), (u + 0.5) * w / 3.0, along / 3.0))
        rows.append(row)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    grid = [[(bm.verts.new(p), u, v) for p, u, v in row] for row in rows]
    for r0, r1 in zip(grid, grid[1:]):
        for k in range(len(r0) - 1):
            quad = (r0[k], r0[k + 1], r1[k + 1], r1[k])
            f = bm.faces.new([q[0] for q in quad])
            for loop, q in zip(f.loops, quad):
                loop[uv].uv = (q[1], q[2])
    ob = c.mesh_object(name, bm, "Village", "visual")
    ob.data.materials.append(c.lib(*mat))
    kit.materials.ensure_paint(ob.data)
    return ob


def wobble(a, b, seed, amp=1.2):
    """Points from a to b with a gentle meander (paths are never ruler-straight)."""
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 5))
    d = Vector((b[0] - a[0], b[1] - a[1], 0))
    side = Vector((d.y, -d.x, 0)).normalized()
    out = []
    for k in range(n + 1):
        t = k / n
        s = math.sin(t * math.pi) * amp * math.sin(t * 5 + seed)
        out.append((a[0] + d.x * t + side.x * s, a[1] + d.y * t + side.y * s))
    return out


def village_paths(c, ter, villages, water_z, river_x):
    """Paths from every hut door to its fire, from each fire to the nearest road edge,
    and between hamlets close enough to walk. Returns spots for trees to keep off."""
    keep = []
    n = 0

    def lay(pts, width):
        nonlocal n
        # Never into the river.
        for x, y in pts:
            z = c.ground_z(x, y, ter)
            if z is None or z < water_z + 0.3 or abs(x - river_x(y)) < 26:
                return
        n += 1
        if path_strip(c, "Village Path %d" % n, pts, ter, width=width):
            keep.extend((x, y, width / 2 + 0.8) for x, y in pts[::2])

    for h, ((cx, cy), huts) in enumerate(villages):
        for k, (x, y, a) in enumerate(huts):
            # The doorway faces the fire (a + pi); start just outside it.
            dx, dy = cx - x, cy - y
            L = math.hypot(dx, dy) or 1
            door = (x + dx / L * 3.6, y + dy / L * 3.6)
            stop = (cx - dx / L * 2.0, cy - dy / L * 2.0)
            lay(wobble(door, stop, h * 3 + k, 0.5), 1.6)
        # Out to the road.
        smp, d = c.nearest(cx, cy)
        edge = smp.p + (Vector((cx, cy, 0)) - Vector((smp.p.x, smp.p.y, 0))).normalized() * (smp.w / 2 + 1.0)
        if d < 70:
            lay(wobble((cx, cy), (edge.x, edge.y), h * 7, 1.5), 2.2)
    # Between neighbouring hamlets.
    fires = [v[0] for v in villages]
    for i in range(len(fires)):
        for j in range(i + 1, len(fires)):
            a, b = fires[i], fires[j]
            if math.hypot(a[0] - b[0], a[1] - b[1]) < 75:
                pts = wobble(a, b, i * 5 + j, 3.0)
                if all(props.clear_of_road(c, x, y, 1.0) for x, y in pts):
                    lay(pts, 2.2)
    return keep


def village_lights(c, ter, villages):
    """A flickering torch light at every campfire (the game's torch light: warm, on the
    road, the walls and the karts, for the fires nearest the camera)."""
    for (cx, cy), _ in villages:
        z = c.ground_z(cx, cy, ter)
        if z is not None:
            gx, gy, gz = c.game(cx, cy, z + 1.2)
            c.entity("torch", x=gx, y=gy, z=gz)


# ---------------------------------------------------------------- the volcano


def volcano(c, vp):
    """A real volcano where the dark cone stood beyond the north-west wall: a glowing
    crater, lava running down its flanks and a plume of smoke leaning on the wind."""
    x, y, sc = -360.0, 380.0, 0.58
    c.place(vp.far_volcano(c, 0), x, y, -8, rot=0.4, scale=sc, coll="Backdrop", role="visual")
    plume = vp.smoke_plume(c, 0, 80.0)
    c.place(plume, x, y, 200 * sc - 10, rot=0.9, scale=1.4, coll="Backdrop", role="visual")
    c.place(plume, x + 8, y - 6, 200 * sc - 6, rot=2.1, scale=1.0, coll="Backdrop", role="visual")


# ---------------------------------------------------------------- the walls


def wall_ledges(c, ter, natural, wall_r=210.0, avoid=()):
    """Green ledges stepping round the valley walls: rock shelves with grassy tops that
    jut from the cliffs at different heights, with shrubs and ferns on them (none within
    the (x, y, radius) circles in `avoid`: the waterfall's notch, say)."""
    bush = props.bush(c, 0)
    fern = props.fern(c)
    shelves = []
    n = 0
    for k in range(84):
        ang = (k // 2) * math.tau / 42 + 0.06 * math.sin(k * 1.7) + (k % 2) * 0.05
        # Two tiers on each bearing: a low ledge and a high one.
        target = (5 + 7 * rnd(k * 3.3)) if k % 2 == 0 else (15 + 9 * rnd(k * 3.3))
        best = None
        for step in range(70):
            r = 185 + step * 1.2
            px, py = r * math.cos(ang) / 0.95, r * math.sin(ang)
            if natural(px, py) >= target:
                best = (px, py, r)
                break
        if best is None:
            continue
        px, py, r = best
        z = natural(px, py)
        # Skip the river's notch and gorge.
        if not props.clear_of_road(c, px, py, 8) or z < 4:
            continue
        if any(math.hypot(px - ax, py - ay) < ar for ax, ay, ar in avoid):
            continue
        n += 1
        length = 16 + 18 * rnd(k * 5.1)
        depth = 5.5 + 4.0 * rnd(k * 7.3)
        # Jut out toward the valley (the rock's long side along the wall).
        ox, oy = math.cos(ang) / 0.95, math.sin(ang)
        cx, cy = px - ox * depth * 0.55, py - oy * depth * 0.55
        rock = c.rock_mass("Wall Ledge %d" % n, cx, cy, length / 2, depth, z, z0=z - 6 - 4 * rnd(k), n=12, seed=k * 2,
                           bands=[(1.0, 0.0), (1.0, 0.55), (0.96, 0.8), (0.94, 1.0)], angle=ang + math.pi / 2, base=z - 6)
        c.paint_rock(rock, ("valley_cliff", "wall"), ("valley_grass", "grass"))
        shelves.append((cx, cy, z, ang, length))
        # Shrubs and ferns along the shelf.
        for m in range(int(length / 3.5)):
            t = (m + 0.5) / max(1, int(length / 3.5)) - 0.5
            sx = cx + math.cos(ang + math.pi / 2) * t * length * 0.8 + ox * (rnd(k + m) - 0.5) * depth * 0.4
            sy = cy + math.sin(ang + math.pi / 2) * t * length * 0.8 + oy * (rnd(k * 2 + m) - 0.5) * depth * 0.4
            proto = bush if (k + m) % 3 else fern
            c.place(proto, sx, sy, z - 0.1, rot=rnd(k * 9 + m) * math.tau, scale=0.7 + 0.6 * rnd(k * 4 + m), coll="Walls", role="visual")
    return shelves


# ---------------------------------------------------------------- landmarks


def rock_feature(c, ter):
    """A cluster of light sandstone rocks on the open east meadow: a tall weathered
    stack, two leaning boulders beside it and a low shelf."""
    cx, cy, _ = B(201.71, 2.78, -1.57)
    cx -= 8  # off the wall's foot, onto the meadow
    z = c.ground_z(cx, cy, ter) or 2.0
    parts = [(0, 0, 5.5, 4.5, 15), (7, 3, 3.2, 2.6, 7), (-5, -5, 3.0, 3.6, 5), (3, -8, 5.0, 2.2, 2.6)]
    for i, (dx, dy, rx, ry, h) in enumerate(parts):
        rock = c.rock_mass("Sandstone Feature %d" % (i + 1), cx + dx, cy + dy, rx, ry, z + h, z0=z - 3, n=11, seed=40 + i * 3,
                           angle=0.6 * i, base=z)
        # (The valley's own layered rock, so it matches the walls round it.)
        c.paint_rock(rock, ("valley_cliff", "wall"), ("valley_grass", "grass"))
    return [(cx, cy, 12.0)]


def grand_pillar(c, ter):
    """A grand rock pillar east of the river: a 46 m column of banded sandstone,
    swelling at its foot and flaring under a grassy crown with a palm on top."""
    cx, cy, _ = B(100.89, 3.3, 23.71)
    z = c.ground_z(cx, cy, ter) or 1.0
    bands = [(1.25, 0.0), (1.1, 0.08), (0.92, 0.2), (0.86, 0.45), (0.82, 0.7), (0.9, 0.86), (1.05, 0.94), (1.0, 1.0)]
    rock = c.rock_mass("Grand Pillar", cx, cy, 8.5, 7.5, z + 46, z0=z - 4, n=14, seed=91, bands=bands, base=z)
    c.paint_rock(rock, ("valley_cliff", "wall"), ("valley_grass", "grass"))
    palm = props.palm(c, 9.0, 1.2, 1)
    c.place(palm, cx + 1.5, cy - 1.0, z + 46 - 0.3, rot=1.1, scale=1.0, coll="Rocks", role="visual")
    return [(cx, cy, 14.0)]


def stone_arch(c, ter, river_x, water_z):
    """A natural stone arch over the river, east of the S-bends: a broad rock deck you
    can drive up from either bank, over the water and down the other side (off the race
    line, just for exploring). The deck drives like road; its sides are rock."""
    gx, gy, gz = 1.76, 12.3, 6.38
    _, want, _ = B(gx, gy, gz)
    # From bank to bank across the river, long enough for gentle ramps; nudged up or
    # down the river (nearest Blake's box first) until it's clear of the road.
    half = 40.0
    ycen = None
    for dy in (0, 6, -6, 12, -12, 18, -18, 26, -26):
        yy = want + dy
        xr = river_x(yy)
        if all(props.clear_of_road(c, xr - half + 2 * half * k / 24, yy, 4) for k in range(25)):
            ycen = yy
            break
    if ycen is None:
        print("riverbend_review: no room for the arch")
        return []
    xr = river_x(ycen)
    a = (xr - half, ycen)
    b = (xr + half, ycen)
    za = c.ground_z(*a, ter) or 0.5
    zb = c.ground_z(*b, ter) or 0.5
    H = 9.5
    W = 8.0
    n = 32
    bm = bmesh.new()
    rows = []
    for k in range(n + 1):
        t = k / n
        x = a[0] + (b[0] - a[0]) * t
        y = a[1] + 2.5 * math.sin(t * math.pi * 2)
        base = za + (zb - za) * t
        top = base + H * math.sin(t * math.pi) - 0.4 * (1 - math.sin(t * math.pi))
        # The arch's underside: thick at the ends, thin over the water.
        under = top - (3.2 + 6.0 * (1 - math.sin(t * math.pi)) ** 2)
        w = W * (1.0 + 0.25 * (1 - math.sin(t * math.pi)))
        bulge = 1.2 + 0.5 * math.sin(k * 1.9)
        rows.append([bm.verts.new((x, y + s, zz)) for s, zz in ((-w / 2 - bulge, (top + under) / 2), (-w / 2, top), (w / 2, top), (w / 2 + bulge, (top + under) / 2), (w / 2 * 0.6, under), (-w / 2 * 0.6, under))])
    deck, sides = [], []
    for r0, r1 in zip(rows, rows[1:]):
        for i in range(6):
            f = bm.faces.new((r0[i], r1[i], r1[(i + 1) % 6], r0[(i + 1) % 6]))
            (deck if i == 1 else sides).append(f.index)
    bm.faces.new(list(reversed(rows[0])))
    bm.faces.new(rows[-1])
    bm.faces.ensure_lookup_table()
    sides += [len(bm.faces) - 2, len(bm.faces) - 1]
    ob = c.mesh_object("River Arch", bm, "Rocks", "both")
    c.assign(ob, c.lib("valley_cliff", "road"), deck)
    c.assign(ob, c.lib("valley_cliff", "wall"), sides)
    ob.data.shade_flat()
    # Rocky edges: a ragged lip of boulders along both sides of the deck, so from the road
    # it reads as a natural arch, not a bridge (the way over is still there between them).
    stones = [boulder_shape(c, v) for v in (0, 2, 4, 6)]
    for k in range(1, n):
        t = k / n
        x = a[0] + (b[0] - a[0]) * t
        y = a[1] + 2.5 * math.sin(t * math.pi * 2)
        base = za + (zb - za) * t
        top = base + H * math.sin(t * math.pi) - 0.4 * (1 - math.sin(t * math.pi))
        w = W * (1.0 + 0.25 * (1 - math.sin(t * math.pi)))
        for side in (-1, 1):
            j = k * 2 + (side > 0)
            sc = 0.75 + 0.55 * rnd(j * 3.1)
            c.place(stones[j % 4], x + (rnd(j * 1.7) - 0.5) * 1.2, y + side * (w / 2 - 0.35 * sc), top - 0.35 * sc,
                    rot=rnd(j * 5.3) * math.tau, scale=sc, coll="Rocks", role="both")
    return [(a[0], a[1], 9.0), (b[0], b[1], 9.0), ((a[0] + b[0]) / 2, ycen, 14.0)]


# ---------------------------------------------------------------- driving


def corner_kicker(c):
    """A low rock kicker on the ridge corner (Blake: "the slightest bump"): 0.45 m up
    over 4 m, then it drops away, for a little hop across the corner instead of
    bogging down in the grass. Drives like road."""
    x, y, z = B(-141.65, 8.91, 68.94)
    s = kit.s_near(c, x, y)
    q = c.at(s)
    t = q.t.normalized()
    r = q.r.normalized()
    L, Hk, W = 4.0, 0.45, 5.0
    bm = bmesh.new()
    # Keep it on the road (the pin was near the inside edge) and sit it on the road's
    # real surface (banked), so it isn't buried.
    off = (Vector((x, y, 0)) - Vector((q.p.x, q.p.y, 0))).dot(r)
    off = max(-q.w / 2 + W / 2 + 0.3, min(q.w / 2 - W / 2 - 0.3, off))
    p0 = q.p + r * off
    roads = [o for o in c.pieces if o.type in ("MESH", "CURVE")]
    pts = []
    for along, up in ((-L, 0.0), (0.0, Hk), (0.5, Hk), (0.9, 0.0)):
        for side in (-W / 2, W / 2):
            p = p0 + t * along + r * side
            zs = c.ground_z(p.x, p.y, roads)
            pts.append(bm.verts.new((p.x, p.y, (zs if zs is not None else p.z) + up - 0.03)))
    # 0-1 back, 2-3 lip, 4-5 lip end, 6-7 front foot
    v = pts
    ramp = bm.faces.new((v[0], v[1], v[3], v[2])).index
    top = bm.faces.new((v[2], v[3], v[5], v[4])).index
    drop = bm.faces.new((v[4], v[5], v[7], v[6])).index
    s1 = bm.faces.new((v[0], v[2], v[4], v[6])).index
    s2 = bm.faces.new((v[1], v[7], v[5], v[3])).index
    ob = c.mesh_object("Corner Kicker", bm, "Road", "both")
    c.assign(ob, c.lib("valley_road", "road"), [ramp, top, drop])
    c.assign(ob, c.lib("valley_road", "wall"), [s1, s2])
    return ob


# The footpath Blake drove (a recorded line), from the ford road west into the hills.
FOOTPATH_GAME = [
    (-89.77, 1.05, -64.64), (-96.86, 0.51, -61.43), (-103.08, 0.35, -59.15), (-109.13, 1.16, -56.5),
    (-115.03, 2.84, -53.67), (-121.61, 5.11, -50.62), (-125.42, 6.03, -48.9),
]


def footpath(c, line=None):
    """A narrow footpath you can drive on at full speed: a winding trail of packed earth
    with grass sprinkled through it (its own look, not the road's), along the line Blake
    drove."""
    pts = [B(*p) for p in (line or FOOTPATH_GAME)]
    # A trail of packed earth with grass growing through it, petering out into the grass
    # at both ends (it narrows to nothing rather than stopping square).
    # (Its start is on the road's edge: it opens out from there, and narrows away into the
    # meadow at its far end.)
    w = [3.6] * len(pts)
    w[0], w[-2], w[-1] = 2.6, 2.2, 0.5
    c.shortcut("Footpath", [(x, y, z - 0.05, ww) for (x, y, z), ww in zip(pts, w)], "valley_trail", "road", width=3.6,
               shoulder=0.3, shoulder_mat=("valley_trail", "road"))


# ---------------------------------------------------------------- creatures


def meadow_dinos(c, road_clear):
    """A family of gentle long-necks grazing round the meadows: a mother and two young,
    each on its own loop well away from the road (the big one still strolls across it).
    Loops are found by trying spots round the valley until three fit."""
    family = [((18, 30), 0.7, 1.6), ((14, 20), 0.5, 2.0), ((12, 18), 0.45, 1.8)]
    spots = []
    for k in range(400):
        if len(spots) == len(family):
            break
        rx, ry = family[len(spots)][0]
        cx = -170 + 340 * rnd(k * 1.37 + 3)
        cy = -170 + 340 * rnd(k * 2.71 + 5)
        if any(math.hypot(cx - x, cy - y) < 70 for x, y in spots) or math.hypot(cx + 75, cy + 28) < 100:
            continue
        loop = [(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in [j * math.tau / 16 for j in range(16)]]
        if all(road_clear(x, y) for x, y in loop):
            spots.append((cx, cy))
    for i, (cx, cy) in enumerate(spots):
        (rx, ry), sc, sp = family[i]
        loop = [(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in [j * math.tau / 16 for j in range(16)]]
        name = "Dino Path %d" % (i + 2)
        c.path_curve(name, loop)
        c.entity("dinosaur", route=name, speed=sp, scale=sc, start=7 * (i + 1))
    print("riverbend_review: %d meadow long-necks" % len(spots))
    return len(spots)
