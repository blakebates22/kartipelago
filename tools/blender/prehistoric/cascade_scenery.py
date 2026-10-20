# Cascade Caverns' scenery (see cascade_caverns.py): the temple bridge and viaduct, the
# temple tunnel, the waterfall leap, waterfalls, ledges, giant trees and jungle, ruins,
# the river's creatures and the pterosaur's flight path.
# SPDX-License-Identifier: MIT

import math

import course_kit as kit
import props
from course_kit import Vector, bmesh, lerp, rnd


def clear_of_other(c, x, y, s_lo, s_hi, margin):
    """No road other than the stretch s_lo..s_hi passes within `margin` of (x, y)."""
    for smp in c.S:
        if s_lo <= smp.s <= s_hi:
            continue
        if (smp.p.x - x) ** 2 + (smp.p.y - y) ** 2 < (smp.w / 2 + margin) ** 2:
            return False
    for q in c.extra_ground:
        if (q.p.x - x) ** 2 + (q.p.y - y) ** 2 < (q.w / 2 + margin) ** 2:
            return False
    return True


def block_object(c, name, boxes, coll="Ruins", role="both"):
    """One mesh of boxes: [(material, centre, size, rot)]."""
    bm = bmesh.new()
    slots = {}
    for mat, centre, size, rot in boxes:
        k0 = len(bm.faces)
        props.cuboid(bm, centre, size, rot)
        bm.faces.ensure_lookup_table()
        slots.setdefault(mat, []).extend(range(k0, len(bm.faces)))
    ob = c.mesh_object(name, bm, coll, role)
    for mat, faces in slots.items():
        c.assign(ob, c.lib(*mat), faces)
    ob.data.shade_flat()
    return ob


STONE = ("ruin_stone", "wall")
GLYPH = ("ruin_glyph", "wall")
DARK = ("ruin_dark", "wall")


# ------------------------------------------------------------------ bridge and viaduct


def pylons(c, cc, s0, s1, every, name, ter):
    """Stepped stone pylons under an elevated stretch, like the piers of a temple bridge.
    None stand on another road (or the river's deep middle)."""
    boxes = []
    n = max(1, int((s1 - s0) / every))
    for k in range(1, n):
        s = s0 + (s1 - s0) * k / n
        q = c.at(s)
        ground = c.ground_z(q.p.x, q.p.y, ter)
        if ground is None:
            continue
        deck_bottom = q.p.z - 3.2
        if deck_bottom - ground < 3.0:
            continue
        if not clear_of_other(c, q.p.x, q.p.y, s - 40, s + 40, 9.0):
            continue
        rot = math.atan2(q.t.y, q.t.x)
        w = q.w + 2.0
        tiers = 4
        span = deck_bottom - (ground - 1.5)
        for t in range(tiers):
            z0 = ground - 1.5 + span * t / tiers
            h = span / tiers
            grow = (tiers - t - 1) * 1.6
            boxes.append((STONE, (q.p.x, q.p.y, z0 + h / 2), (6.0 + grow, w + grow, h), rot))
        # A carved band at the top, under the deck.
        boxes.append((GLYPH, (q.p.x, q.p.y, deck_bottom - 0.8), (6.6, w + 0.6, 1.6), rot))
    if boxes:
        block_object(c, name, boxes, coll="Bridge")


def gateway(c, s, name, height=10.0):
    """Two stepped towers either side of the road and a carved lintel over it."""
    q = c.at(s)
    rot = math.atan2(q.t.y, q.t.x)
    z = q.p.z
    half = q.w / 2 + 3.6
    boxes = []
    for side in (-1, 1):
        p = q.p + q.r * side * half
        for t, (sz, h) in enumerate(((4.4, 4.0), (3.8, 3.5), (3.2, 3.0))):
            base = z - 1.0 + sum(hh for _, hh in ((4.4, 4.0), (3.8, 3.5), (3.2, 3.0))[:t])
            boxes.append((STONE, (p.x, p.y, base + h / 2), (sz, sz, h), rot))
        boxes.append((GLYPH, (p.x, p.y, z + 10.2), (2.6, 2.6, 1.6), rot))
    lin = q.p
    boxes.append((GLYPH, (lin.x, lin.y, z + height), (3.0, 2 * half + 3.2, 2.0), rot))
    boxes.append((STONE, (lin.x, lin.y, z + height + 1.4), (2.4, 2 * half + 1.0, 0.8), rot))
    # A roof comb on top, stepped.
    for k, wdt in enumerate((9.0, 6.0, 3.4)):
        boxes.append((STONE, (lin.x, lin.y, z + height + 2.2 + k * 1.1), (1.6, wdt, 1.1), rot))
    block_object(c, name, boxes)


def friezes(c, s0, s1, name, drop=1.6):
    """A carved glyph band along both sides of an elevated stretch, under the barrier."""
    bm = bmesh.new()
    s = s0
    while s < s1:
        q = c.at(s)
        q2 = c.at(min(s1, s + 4.0))
        for side in (-1, 1):
            a = q.side(side * (q.w / 2 + 1.0), -drop)
            b = q2.side(side * (q2.w / 2 + 1.0), -drop)
            mid = (a + b) / 2
            ln = (b - a).length
            rot = math.atan2((b - a).y, (b - a).x)
            props.cuboid(bm, (mid.x, mid.y, mid.z), (ln + 0.05, 0.5, 1.4), rot)
        s += 4.0
    ob = c.mesh_object(name, bm, "Bridge", "visual")
    c.assign(ob, c.lib(*GLYPH))
    ob.data.shade_flat()


# ------------------------------------------------------------------ the temple tunnel


def facade(c, s, name, tunnel_half, tunnel_h, facing):
    """The temple's face round a tunnel mouth: massive pillars, a carved lintel, sloped
    side walls running into the rock, a roof comb, and torches. `facing` is +1 if the
    tunnel runs forward from s (an entrance), -1 if it runs back (an exit)."""
    q = c.at(s)
    rot = math.atan2(q.t.y, q.t.x)
    z = q.p.z
    boxes = []
    half = tunnel_half + 2.4
    for side in (-1, 1):
        p = q.p + q.r * side * half
        boxes.append((STONE, (p.x, p.y, z + tunnel_h / 2 + 1.0), (4.0, 4.8, tunnel_h + 4.0), rot))
        boxes.append((GLYPH, (p.x, p.y, z + tunnel_h * 0.55), (4.3, 5.1, 2.2), rot))
        # Sloped side walls (talud), stepping out into the rock.
        for k in range(3):
            o = q.p + q.r * side * (half + 4.5 + k * 4.0) - q.t * facing * (1.0 + k * 1.5)
            boxes.append((STONE, (o.x, o.y, z + (tunnel_h + 4 - k * 3) / 2 - 1), (4.0 + k, 4.0, tunnel_h + 4 - k * 3), rot))
    lin = q.p
    boxes.append((GLYPH, (lin.x, lin.y, z + tunnel_h + 1.6), (4.6, 2 * half + 4.0, 3.2), rot))
    boxes.append((STONE, (lin.x, lin.y, z + tunnel_h + 4.0), (5.2, 2 * half + 8.0, 1.6), rot))
    for k, wdt in enumerate((16.0, 11.0, 6.0)):
        boxes.append((STONE, (lin.x - q.t.x * facing * 1.0, lin.y - q.t.y * facing * 1.0, z + tunnel_h + 5.6 + k * 1.6), (2.0, wdt, 1.6), rot))
    boxes.append((GLYPH, (lin.x, lin.y, z + tunnel_h + 10.6), (2.2, 4.0, 2.4), rot))
    block_object(c, name, boxes)
    return q


def torches(c, s0, s1, every, half, up=3.6):
    """Wall torches all along the tunnel, alternating sides; returns where the flames are."""
    proto = props.torch(c)
    lights = []
    k = 0
    s = s0
    while s < s1:
        q = c.at(s)
        side = 1 if k % 2 else -1
        p = q.side(side * (half - 1.1), up)
        to = q.p - p
        rot = math.atan2(to.x, -to.y)
        c.place(proto, p.x, p.y, p.z, rot=rot, scale=1.6, coll="Tunnel", role="visual")
        lights.append(tuple(q.side(side * (half - 2.3), up + 1.9)))
        s += every
        k += 1
    return lights


def tunnel_dressing(c, s0, s1, half, every):
    """The inside of the temple: carved pilasters down both walls (each torch hangs on
    one), a glyph frieze along the walls, roots hanging through the roof and fallen
    blocks along the foot of the walls. All scenery: the karts meet the tunnel's own
    smooth walls, never a corner of carving."""
    boxes = []
    k = 0
    s = s0
    while s < s1:
        q = c.at(s)
        rot = math.atan2(q.t.y, q.t.x)
        side = 1 if k % 2 else -1
        for sd in (side, -side):
            p = q.side(sd * (half - 0.5), 0.0)
            tall = 6.4
            boxes.append((DARK, (p.x, p.y, p.z + tall / 2 - 0.4), (1.9, 1.0, tall), rot))
            boxes.append((GLYPH, (p.x, p.y, p.z + tall - 0.1), (2.3, 1.3, 0.9), rot))
            boxes.append((DARK, (p.x, p.y, p.z + 0.1), (2.3, 1.3, 0.8), rot))
        s += every
        k += 1
    # The frieze: a carved band along both walls, just under the roof's spring.
    s = s0 - 4
    while s < s1 + 4:
        q = c.at(s)
        q2 = c.at(s + 4.0)
        for sd in (-1, 1):
            a = q.side(sd * (half - 0.25), 6.9)
            b = q2.side(sd * (half - 0.25), 6.9)
            mid = (a + b) / 2
            boxes.append((GLYPH, (mid.x, mid.y, mid.z), ((b - a).length + 0.05, 0.5, 1.0), math.atan2((b - a).y, (b - a).x)))
        s += 4.0
    block_object(c, "Temple Halls", boxes, coll="Tunnel", role="visual")
    roots = [props.hanging_roots(c, v, 2.6 + v) for v in range(3)]
    rubble = [props.ruin_blocks(c, v) for v in range(2)]
    k = 0
    s = s0 + 5
    while s < s1:
        q = c.at(s)
        off = (rnd(k * 3.1) - 0.5) * 2 * (half * 0.55)
        p = q.side(off, 10.6 - abs(off) * 0.25)
        c.place(roots[k % 3], p.x, p.y, p.z, rot=k * 1.7, scale=0.9 + 0.4 * rnd(k), coll="Tunnel", role="visual")
        if k % 3 == 1:
            sd = 1 if rnd(k * 7.7) < 0.5 else -1
            r = q.side(sd * (half - 1.4), -0.2)
            c.place(rubble[k % 2], r.x, r.y, r.z, rot=k, scale=0.45, coll="Tunnel", role="visual")
        s += 7.0 + 4.0 * rnd(k * 5.3)
        k += 1


# ------------------------------------------------------------------ the land's features


def ledges(c, cc, ter, count, seed):
    """Rock shelves jutting out of the canyon walls, with plants on top and vines below."""
    vines = [props.vine_curtain(c, v, 9.0 + 3 * v) for v in range(3)]
    fern = props.fern(c)
    leafy = props.big_leaf_plant(c, 0)
    made = 0
    k = 0
    while made < count and k < count * 6:
        k += 1
        x = -260 + 450 * rnd(k * 3.7 + seed)
        north = rnd(k * 5.1 + seed) < 0.5
        tier = 1 + int(rnd(k * 7.3 + seed) * 3)
        step = sum(t[0] for t in cc.TIERS[: tier + 1]) * 0 + cc.TIERS[tier][0]
        edge = cc.wall_n(x) if north else cc.wall_s(x)
        y = edge + (step + 1.5) * (1 if north else -1)
        if cc.in_tunnel_rock(x, y, 1.15) or not props.clear_of_road(c, x, y, 14):
            continue
        z = c.ground_z(x, y, ter)
        if z is None or z < 8:
            continue
        out = -1 if north else 1  # toward the canyon
        w = 7 + 5 * rnd(k)
        slab = c.rock_mass("Ledge %02d" % (made + 1), x, y + out * 1.5, w, 3.6, z + 0.6, z0=z - 1.8, n=10, seed=k,
                           bands=[(1.0, 0.0), (1.05, 0.5), (0.95, 1.0)], base=z - 1.8)
        c.paint_rock(slab, (cc.rock_mat(Vector((x, y, z))), "wall"), ("jungle_leafcover", "grass"))
        rot = 0.0 if out < 0 else math.pi
        for j in range(2):
            vx = x + (j - 0.5) * w * 0.8
            c.place(vines[(k + j) % 3], vx, y + out * 4.6, z + 0.4, rot=rot, coll="Vines", role="visual")
        c.place(fern if k % 2 else leafy, x, y + out * 1.5, z + 0.6, rot=k, scale=1.3, role="visual")
        made += 1


def wall_vines(c, cc, ter, count, seed):
    """Vines spilling over the edges of the wall tiers."""
    vines = [props.vine_curtain(c, v, 8.0 + 4 * v) for v in range(3)]
    k = 0
    made = 0
    while made < count and k < count * 8:
        k += 1
        x = -265 + 455 * rnd(k * 2.3 + seed)
        north = rnd(k * 4.9 + seed) < 0.55
        tier = int(rnd(k * 6.1 + seed) * 4)
        edge = cc.wall_n(x) if north else cc.wall_s(x)
        y = edge + (cc.TIERS[tier][0] + 0.2) * (1 if north else -1)
        if cc.in_tunnel_rock(x, y, 1.1):
            continue
        z = c.ground_z(x, y + (2.5 if north else -2.5), ter)
        if z is None or z < 6:
            continue
        rot = 0.0 if north else math.pi
        c.place(vines[k % 3], x, y + (-0.6 if north else 0.6), z + 0.2, rot=rot, coll="Vines", role="visual")
        made += 1


def ruins(c, cc, ter):
    """The lost city: columns, tumbled blocks, steles and colossal heads along the floor,
    an archway over the road, and stairs up to the ledges."""
    cols = [props.ruin_column(c, v) for v in range(3)]
    blocks = [props.ruin_blocks(c, v) for v in range(2)]
    steles = [props.stele(c, v) for v in range(2)]
    head = props.idol_head(c)
    steps = props.stairs(c, 7)

    def floor_ok(m0, m1):
        def ok(x, y, z):
            smp, d = c.nearest(x, y)
            return z > cc.WATER_Z + 0.6 and smp.w / 2 + m0 < d < smp.w / 2 + m1 and not cc.in_tunnel_rock(x, y, 1.05) and z < 16
        return ok

    for v, p in enumerate(cols):
        props.scatter(c, p, 12, (-270, 190, -75, 110), floor_ok(5, 30), ter, seed=200 + v, scale=(0.9, 1.3), sink=0.4, coll="Ruins")
    for v, p in enumerate(blocks):
        props.scatter(c, p, 10, (-270, 190, -75, 110), floor_ok(4, 34), ter, seed=210 + v, scale=(0.8, 1.2), sink=0.5, coll="Ruins")
    for v, p in enumerate(steles):
        props.scatter(c, p, 6, (-270, 190, -75, 110), floor_ok(5, 22), ter, seed=220 + v, scale=(1.0, 1.2), sink=0.3, coll="Ruins")
    # Colossal heads: one watching the start straight, one on the north road.
    for i, (x, y, face) in enumerate(((10, -62, 0.0), (-160, 106, math.pi), (150, -60, 0.4))):
        z = c.ground_z(x, y, ter)
        if z is not None and props.clear_of_road(c, x, y, 8):
            c.place(head, x, y, z - 0.6, rot=face, scale=1.4, coll="Ruins")
    # Stairs climbing the first tier of the south wall near the start.
    for i, x in enumerate((-10, 70)):
        y = cc.wall_s(x) + 6
        z = c.ground_z(x, y, ter)
        if z is not None and props.clear_of_road(c, x, y, 6):
            c.place(steps, x, y, z - 0.3, rot=math.pi, scale=1.2, coll="Ruins")
    # A ruined archway over the north road.
    s = cc.SEG[23] + 20
    q = c.at(s)
    rot = math.atan2(q.t.y, q.t.x)
    half = q.w / 2 + 3.2
    boxes = []
    for side in (-1, 1):
        p = q.p + q.r * side * half
        boxes.append((STONE, (p.x, p.y, q.p.z + 4.5), (2.6, 2.6, 10.0), rot))
        boxes.append((GLYPH, (p.x, p.y, q.p.z + 9.8), (3.0, 3.0, 1.0), rot))
    boxes.append((GLYPH, (q.p.x, q.p.y, q.p.z + 11.0), (2.4, 2 * half + 3.0, 1.6), rot))
    block_object(c, "Ruined Arch", boxes)


def vegetation(c, cc, ter):
    """Dense jungle: giant trees, jungle trees, palms, big-leaf plants, ferns and bushes on
    the floor and the shelves, and a ring of giants along the canyon rims."""
    giants = [props.giant_tree(c, v) for v in range(3)]
    trees = [props.jungle_tree(c, v) for v in range(2)]
    grand = [props.grand_tree(c, v) for v in range(2)]
    palms = [props.palm(c, 9 + v * 2, 1.0 + v * 0.6, v) for v in range(2)]
    leaves = [props.big_leaf_plant(c, v) for v in range(2)]
    bushes = [props.bush(c, v) for v in range(2)]
    fern = props.fern(c)

    def floor_ok(m0, m1, zmax=16):
        def ok(x, y, z):
            smp, d = c.nearest(x, y)
            return (
                z > cc.WATER_Z + 0.6
                and smp.w / 2 + m0 < d < smp.w / 2 + m1
                and not cc.in_tunnel_rock(x, y, 1.08)
                and abs(y - cc.river_y(x)) > cc.river_half(x) + 2
                and z < zmax
            )
        return ok

    rim = lambda x, y, z: z > 36 and props.clear_of_road(c, x, y, 16)  # noqa: E731
    shelf = lambda x, y, z: 10 < z < 36 and props.clear_of_road(c, x, y, 14) and not cc.in_tunnel_rock(x, y, 1.05)  # noqa: E731
    area = (-275, 200, -150, 150)
    for v, t in enumerate(giants):
        props.scatter(c, t, 6, area, floor_ok(14, 70), ter, seed=300 + v, scale=(0.9, 1.15))
        props.scatter(c, t, 12, area, rim, ter, seed=310 + v, scale=(0.9, 1.25), role="visual")
    for v, t in enumerate(grand):
        props.scatter(c, t, 10, area, floor_ok(10, 60), ter, seed=320 + v, scale=(1.2, 1.7))
        props.scatter(c, t, 10, area, shelf, ter, seed=325 + v, scale=(1.0, 1.4), role="visual")
    for v, t in enumerate(trees):
        props.scatter(c, t, 26, area, floor_ok(7, 60), ter, seed=330 + v, scale=(1.1, 1.8))
        props.scatter(c, t, 22, area, rim, ter, seed=335 + v, scale=(1.4, 2.0), role="visual")
        props.scatter(c, t, 14, area, shelf, ter, seed=338 + v, scale=(1.0, 1.5), role="visual")
    for v, p in enumerate(palms):
        props.scatter(c, p, 14, area, floor_ok(4, 30), ter, seed=340 + v)
    for v, p in enumerate(leaves):
        props.scatter(c, p, 60, area, floor_ok(3, 50), ter, seed=350 + v, role="visual", scale=(0.9, 1.6))
        props.scatter(c, p, 16, area, shelf, ter, seed=355 + v, role="visual", scale=(1.0, 1.5))
    for v, b in enumerate(bushes):
        props.scatter(c, b, 50, area, floor_ok(3, 55), ter, seed=360 + v, role="visual", scale=(0.8, 1.6))
    props.scatter(c, fern, 140, area, floor_ok(2.5, 60, zmax=40), ter, seed=370, role="visual", scale=(0.9, 1.5))


def river_life(c, cc, ter):
    """Cattails along the banks, lily pads and logs in the shallows, stumps, and frogs."""
    clumps = [props.cattails(c, v) for v in range(3)]
    pads = [props.lily_pad(c, v) for v in range(3)]
    logs = [props.log(c, v) for v in range(2)]
    stumps = [props.stump(c, v) for v in range(2)]
    frog = props.frog(c)
    n = 0
    for k in range(320):
        x = -268 + 466 * rnd(k * 2.9 + 17)
        side = -1 if rnd(k * 1.3 + 2) < 0.5 else 1
        hw = cc.river_half(x)
        y = cc.river_y(x) + side * (hw - 1.5 + 4.0 * rnd(k * 4.3 + 1))
        if not props.clear_of_road(c, x, y, 5):
            continue
        g = c.ground_z(x, y, ter)
        if g is None or not (cc.WATER_Z - 2.2 < g < cc.WATER_Z + 0.9):
            continue
        z = max(g, cc.WATER_Z - 0.5)
        r = rnd(k * 6.1)
        if r < 0.55:
            c.place(clumps[k % 3], x, y, z, rot=r * 20, scale=0.9 + 0.7 * rnd(k * 9.7), coll="Water", role="visual")
        elif r < 0.8:
            yy = cc.river_y(x) + side * (hw - 4.0 - 3 * rnd(k))
            c.place(pads[k % 3], x, yy, cc.WATER_Z, rot=r * 30, scale=1.0 + 0.8 * rnd(k + 3), coll="Water", role="visual")
            if k % 3 == 0:
                c.place(frog, x, yy, cc.WATER_Z + 0.08, rot=r * 40, scale=1.4, coll="Water", role="visual")
        else:
            yy = cc.river_y(x) + side * (hw - 2.5)
            c.place(logs[k % 2], x, yy, cc.WATER_Z - 0.6, rot=0.3 * (rnd(k) - 0.5), coll="Water", role="visual")
            if k % 2 == 0:
                c.place(frog, x + 0.5, yy, cc.WATER_Z + 0.75, rot=r * 13, scale=1.4, coll="Water", role="visual")
        n += 1

    def floor_ok(x, y, z):
        smp, d = c.nearest(x, y)
        return z > cc.WATER_Z + 0.6 and smp.w / 2 + 4 < d < smp.w / 2 + 40 and not cc.in_tunnel_rock(x, y, 1.05) and z < 16

    for v, s in enumerate(stumps):
        props.scatter(c, s, 14, (-270, 190, -75, 110), floor_ok, ter, seed=400 + v, scale=(0.8, 1.4), sink=0.3)
    for v, lg in enumerate(logs):
        props.scatter(c, lg, 10, (-270, 190, -75, 110), floor_ok, ter, seed=410 + v, scale=(0.8, 1.2), sink=0.4)
    props.scatter(c, frog, 14, (-270, 190, -75, 110), floor_ok, ter, seed=420, scale=(1.3, 1.6), role="visual", sink=0.0)
    return n


# ------------------------------------------------------------------ build


def build(c, rock, t0, t1, cc):
    ter = list(c.coll("Terrain").objects)
    half = c.width / 2 + 3.6

    # The temple bridge and the viaduct: stepped pylons (none on another road), carved
    # friezes, and a gateway at the start of the bridge.
    for piece in c.pieces:
        if "viaduct" in piece.name or "ramp" in piece.name or "lowbridge" in piece.name:
            s0, s1 = piece["kp_from"], piece["kp_to"]
            if s1 < s0:
                s1 += c.length
            pylons(c, cc, s0, s1, 30.0 if "viaduct" in piece.name else 14.0, piece.name + " Pylons", ter)
            friezes(c, s0, s1, piece.name + " Frieze")
    gateway(c, cc.SEG[9] - 6, "Bridge Gateway")
    gateway(c, cc.SEG[4] + 4, "Viaduct Gateway", height=9.0)

    # The temple tunnel: a carved face at each mouth, torches all the way through, and
    # its rock painted dark with warm pools of torchlight.
    facade(c, t0 - 3, "Temple Face", half, 11.0, 1)
    facade(c, t1 + 3, "Temple Back", half, 11.0, -1)
    lights = torches(c, t0 + 6, t1 - 4, 8.0, half)
    tunnel_dressing(c, t0 + 6, t1 - 4, half, 8.0)
    for s, side in ((t0 - 3, -1), (t0 - 3, 1), (t1 + 3, -1), (t1 + 3, 1)):
        q = c.at(s)
        p = q.side(side * (half + 0.4), 5.0)
        c.place(props.torch(c), p.x, p.y, p.z, rot=math.atan2(q.t.x, -q.t.y) + (math.pi if s > t0 else 0), scale=1.5, coll="Tunnel", role="visual")
    (rcx, rcy), rrx, rry = cc.TUNNEL

    def inside(w):
        return cc.in_tunnel_rock(w.x, w.y, 1.0) and w.z < 32

    c.glow([rock], lights, 10.0, (1.25, 0.9, 0.55), base=0.38, region=inside)
    # The flames, for the flickering torchlight on the road and the karts.
    for x, y, z in lights:
        gx, gy, gz = c.game(x, y, z)
        c.entity("torch", x=gx, y=gy, z=gz)

    # The leap: rock pillars either side of the gorge holding up an arch of rock, a
    # curtain of water pouring off it across the gap (you fly through it), and spray.
    jx = c.at(cc.LIP).p.x
    gy = (c.at(cc.LIP).p.y + c.at(cc.LAND).p.y) / 2
    for i, side in enumerate((-1, 1)):
        pil = c.rock_mass("Falls Pillar %d" % (i + 1), jx + side * 24, gy, 7, 9, 34.0, z0=-8, n=12, seed=11 + i)
        c.paint_rock(pil, ("canyon_rock_moss", "wall"), ("canopy_dark", "grass"))
    arch = c.rock_mass("Falls Arch", jx, gy + 2.0, 31, 8, 34.0, z0=26.0, n=16, seed=21,
                       bands=[(1.0, 0.0), (1.05, 0.4), (0.95, 0.75), (0.85, 1.0)], base=26.0)
    c.paint_rock(arch, ("canyon_rock_grey", "wall"), ("canopy_dark", "grass"))
    props.falls(c, "Leap Falls", jx, gy - 0.5, 26.2, cc.WATER_Z - 3.0, 30.0, 34.0, facing=-1, throw=0.8, bulge=0.5, veils=4, foam_r=10.0)
    for v in range(3):
        c.place(props.vine_curtain(c, v, 12.0), jx + (v - 1) * 14, gy - 6.5, 26.6, rot=0.0, coll="Vines", role="visual")

    # Waterfalls down the canyon walls, and the river's source at the east end.
    feet = []
    for i, (x, north) in enumerate(((40, False), (130, False), (-70, True), (100, True))):
        edge = cc.wall_n(x) if north else cc.wall_s(x)
        lip_y = edge + (cc.TIERS[3][0] if north else -cc.TIERS[3][0])
        top = c.ground_z(x, lip_y + (1 if north else -1), ter) or 30.0
        foot = (c.ground_z(x, edge, ter) or 0.0) - 0.2
        fx, fy = props.falls(c, "Wall Falls %d" % (i + 1), x, lip_y, top, foot, 9.0, 13.0, facing=-1 if north else 1, throw=5.0)
        c.disc("Wall Falls %d Pool" % (i + 1), fx, fy + (-3 if north else 3), 9.0, foot + 0.1, c.lib("valley_water"), coll="Water", role="visual", n=18, wobble=0.25)
        feet.append((fx, fy, foot, top, 13.0))
    sx = 197.0
    sy = cc.river_y(sx)
    fx, fy = props.falls(c, "Source Falls", sx, sy, 36.0, cc.WATER_Z, 20.0, 28.0, facing=-1, throw=8.0, angle=-math.pi / 2, veils=4, foam_r=14.0)
    feet.append((fx, fy, cc.WATER_Z, 36.0, 28.0))
    wx = -282.0
    fx, fy = props.falls(c, "Gorge Falls", wx, cc.river_y(wx), 30.0, cc.WATER_Z - 3.0, 12.0, 16.0, facing=-1, throw=6.0, angle=math.pi / 2, veils=3)
    feet.append((fx, fy, cc.WATER_Z - 3.0, 30.0, 16.0))

    ledges(c, cc, ter, 18, 7)
    wall_vines(c, cc, ter, 60, 3)
    ruins(c, cc, ter)
    vegetation(c, cc, ter)
    river_life(c, cc, ter)

    # Lianas slung across the canyon floor between the trees, high over the road.
    for i, (a, b) in enumerate((((-20, -75, 22), (-30, 25, 24)), ((90, -72, 20), (70, -10, 22)), ((-150, 100, 26), (-135, 60, 24)), ((150, -66, 24), (160, -20, 22)))):
        props.liana(c, "Liana %d" % (i + 1), a, b, sag=5.0, r=0.16)

    # Gameplay entities for the scenery: the waterfalls' spray and roar, and the
    # pterosaur gliding round the canyon.
    gx, gy2, gz = c.game(jx, gy, cc.WATER_Z)
    c.entity("waterfall", x=gx, y=gy2, z=gz, top=26, width=34, heading=0)
    for fx, fy, foot, top, w in feet:
        gx, gy2, gz = c.game(fx, fy, foot)
        c.entity("waterfall", x=gx, y=gy2, z=gz, top=round(top, 1), width=w, heading=0)
    sky = [(-40 + 175 * math.cos(a), 8 + 62 * math.sin(a), 46 + 6 * math.sin(3 * a)) for a in [k * math.tau / 14 for k in range(14)]]
    c.path_curve("Flyer Path", sky)
    c.entity("pterosaur", route="Flyer Path", speed=13.0, scale=1.6)
