# Dinosaur Valley's dressing, v4 (Blake's 46 review notes, Oct 28): the walls' ledges and
# rims brought to life, the living water and its banks, the grand falls, the camp's
# village, the Cascade's ruins and giants, the swamp's canopy, Ember's burning trees, lava
# geysers, obsidian huts and seeping walls, the volcano, and the tunnels' lights and webs.
# valley_region.py calls these (both builds: the ruin chars what burns).
# SPDX-License-Identifier: MIT

import math
import random

import course_kit as kit
from course_kit import Vector, bmesh, lerp, smooth
import props
import swamp_props as sp
import region_props as rp
import region_paint as paint
import region_ruin as ruin
import valley_layout as L
from pocket_build import box

RUIN = ruin.ON
RIVER_HW = L.RIVER_HW
POCKET_LOOK = {p[0]: p[1] for p in L.POCKETS}


def _toward_pocket(x, y, e=1.5):
    """The way down off a wall into its pocket (unit x, y)."""
    gx = (L.wall_sd(x + e, y) - L.wall_sd(x - e, y)) / (2 * e)
    gy = (L.wall_sd(x, y + e) - L.wall_sd(x, y - e)) / (2 * e)
    d = math.hypot(gx, gy) or 1.0
    return -gx / d, -gy / d


def _slope(x, y, e=1.2):
    gx = (L.natural(x + e, y) - L.natural(x - e, y)) / (2 * e)
    gy = (L.natural(x, y + e) - L.natural(x, y - e)) / (2 * e)
    return math.hypot(gx, gy)


def place_big(c, proto, n, box, ok, ground, taken, seed, room, margin, trunk=None, scale=(0.9, 1.1), sink=0.3, coll="Props",
              foot=4.0):
    """Up to n of something big (a jungle giant) at spots in box (x0, x1, y0, y1) where
    ok(x, y), `margin` m clear of the roads' edges, `room` from everything taken. Returns
    the spots. It's set down on the lowest ground round its foot (`foot` m out, times its
    scale), so no root hangs in the air (Blake, Oct 28: "these trees are floating"), and
    not on ground too steep for that to look right."""
    rnd = random.Random(seed)
    out = []
    for _ in range(6000):
        if len(out) >= n:
            break
        x, y = rnd.uniform(box[0], box[1]), rnd.uniform(box[2], box[3])
        if not ok(x, y) or not taken.clear(x, y, room) or not paint.road_clear(c, x, y, margin):
            continue
        s = rnd.uniform(*scale)
        rot = rnd.uniform(0, math.tau)
        ring = [ground(x + foot * s * math.cos(a), y + foot * s * math.sin(a)) for a in
                (k * math.tau / 10 for k in range(10))] + [ground(x, y)]
        if max(ring) - min(ring) > 2.2 * foot * s * 0.5:
            continue
        z = min(ring) - sink
        if trunk:
            c.place(proto, x, y, z, rot=rot, scale=s, coll=coll, role="visual")
            c.place(paint.trunk_proto(c, *trunk), x, y, z, scale=s, coll="Collision", role="collision")
        else:
            c.place(proto, x, y, z, rot=rot, scale=s, coll=coll)
        taken.add(x, y, room * 0.6)
        out.append((x, y))
    return out


def wall_spots(c, seed=11, tries=30000):
    """Where things can grow on the walls: the shelves between the tiers (x, y, look),
    the shelves' lips over a riser (x, y, look, (dx, dy) out over it, drop) and the rims'
    tops (x, y, look)."""
    rnd = random.Random(seed)
    shelves, lips, rims = [], [], []
    for _ in range(tries):
        x, y = rnd.uniform(-250, 250), rnd.uniform(-250, 250)
        wi = L.wall_info(x, y)
        look = POCKET_LOOK[wi["pocket"]]
        if wi["past"] > 1.0:
            lw = L.lobe_weights(x, y)
            look = max(lw, key=lw.get)
            if wi["past"] < 20.0 and _slope(x, y) < 0.6 and paint.road_clear(c, x, y, 14.0):
                rims.append((x, y, look))
            continue
        if not 0.05 < wi["t"] < 1.0 or _slope(x, y) > 0.6 or not paint.road_clear(c, x, y, 12.0):
            continue
        if L.river_d(x, y)[0] < RIVER_HW + 8:
            continue
        dx, dy = _toward_pocket(x, y)
        h = L.natural(x, y)
        drop = h - L.natural(x + dx * 3.5, y + dy * 3.5)
        if drop > 3.5:
            lips.append((x, y, look, (dx, dy), h - L.natural(x + dx * 6.5, y + dy * 6.5)))
        else:
            shelves.append((x, y, look))
    return shelves, lips, rims


def wall_life(c, ground, taken):
    """The walls brought to life (Blake, notes 2, 11-13, 17, 37, 42: "we need some ledges,
    maybe with a couple of palm trees and shrubs on the ledges", "add ledges and trees to
    make them come alive"): plants on the shelves, vines spilling over their lips, trees
    along the rims against the sky; in the swamp moss beards, on Ember's slopes charred
    and burning trees, basalt and lava seeping down the risers."""
    shelves, lips, rims = wall_spots(c)
    palms = [props.palm(c, 10.0 + 1.5 * v, 1.3 + 0.5 * v, v) for v in range(3)]
    jungle = [props.jungle_tree(c, v) for v in range(2)]
    bushes = [props.bush(c, v) for v in range(2)]
    fern = props.fern(c)
    leafy = [props.big_leaf_plant(c, v) for v in range(2)]
    vines = [props.vine_curtain(c, v, 8.0 + 3.0 * v) for v in range(3)]
    swampy = [sp.tier_tree(c, v) for v in range(2)]
    beards = [sp.moss_beard(c, v, 4.0) for v in range(2)]
    dead = props.dead_tree(c)
    burning = [rp.burning_tree(c, v) for v in range(2)]
    basalt = props.basalt_columns(c)
    swamp_tree = [rp.swamp_tree(c, v) for v in range(2)]
    grand = [props.grand_tree(c, v) for v in range(2)]
    room = paint.Taken(list(taken.spots))
    k = 0

    def put(proto, x, y, rot, scale, sink=0.3, coll="Ledges"):
        c.place(proto, x, y, ground(x, y) - sink, rot=rot, scale=scale, coll=coll, role="visual")

    # A rock ledge under each tree on the walls (Blake, Riverbend note 8, Bonebog note 11:
    # "give this a small ledge ... all trees in this section on the wall"): a broad slab
    # standing out of the wall at the tree's foot, in the world's own rock.
    trees = set(palms + jungle + swampy + burning + [dead])
    ledge = {lk: rp.tree_ledge(c, mat) for lk, mat in (("riverbend", "ancient_cliff"), ("camp", "ancient_cliff"),
                                                        ("cascade", "canyon_rock_moss"), ("bonebog", "moss_rock"),
                                                        ("ember", "volcano_slag"))}

    def put_tree(proto, x, y, rot, scale, look, sink=0.3, coll="Ledges"):
        if proto in trees:
            # (Set back into the wall a little, its top at the tree's foot.)
            dx, dy = _toward_pocket(x, y)
            lx, ly = x - dx * 0.7, y - dy * 0.7
            c.place(ledge.get(look, ledge["riverbend"]), lx, ly, ground(x, y) - 0.2, rot=rot, scale=1.0,
                    coll=coll, role="visual")
        put(proto, x, y, rot, scale, sink, coll)

    for x, y, look in shelves:
        if not room.clear(x, y, 3.5):
            continue
        k += 1
        rot = (k * 2.39996) % math.tau
        if look in ("riverbend", "camp"):
            pick = k % 5
            if pick == 0:
                put_tree(palms[k % 3], x, y, rot, 0.55 + 0.25 * ((k * 7) % 5) / 5, look)
            elif pick in (1, 2):
                put_tree(bushes[k % 2], x, y, rot, 0.9 + 0.5 * ((k * 3) % 5) / 5, look)
            elif pick == 3:
                put_tree(fern, x, y, rot, 1.4, look)
            else:
                put_tree(jungle[k % 2], x, y, rot, 0.6, look)
        elif look == "cascade":
            pick = k % 4
            put_tree(jungle[k % 2] if pick == 0 else leafy[k % 2] if pick in (1, 2) else fern, x, y, rot,
                     0.7 if pick == 0 else 1.3, look)
        elif look == "bonebog":
            pick = k % 3
            put_tree(swampy[k % 2] if pick == 0 else fern, x, y, rot, 0.75 if pick == 0 else 1.3, look)
        else:
            pick = k % 12
            if pick in (0, 6):
                put(basalt, x, y, rot, 0.55, sink=0.6)
            elif pick in (1, 4, 8):
                put_tree(dead, x, y, rot, 0.9, look)
            elif pick == 3:
                put_tree(burning[k % 2], x, y, rot, 0.8, look)
                gx, gy, gz = c.game(x, y, ground(x, y) + 6.0)
                c.entity("campfire", x=gx, y=gy, z=gz)
            else:
                continue
        room.add(x, y, 3.5)
    n_lips = 0
    seeps = 0
    for x, y, look, (dx, dy), drop in lips:
        if not room.clear(x, y, 4.0):
            continue
        rot = math.atan2(-dx, dy)
        z = ground(x, y)
        if look == "ember":
            # Lava seeping over the lip and down the riser, into a glowing pool below.
            if seeps < 9 and drop > 7.0 and ((int(x) + int(y)) % 3 == 0):
                lava_seep(c, x, y, dx, dy, z, drop, seeps)
                seeps += 1
                room.add(x, y, 9.0)
            continue
        if look == "bonebog":
            c.place(beards[n_lips % 2], x + dx * 0.6, y + dy * 0.6, z + 0.2, rot=rot, coll="Vines", role="visual")
        c.place(vines[n_lips % 3], x + dx * 0.5, y + dy * 0.5, z + 0.3, rot=rot, coll="Vines", role="visual")
        n_lips += 1
        room.add(x, y, 4.0)
    for x, y, look in rims:
        if not room.clear(x, y, 6.0):
            continue
        k += 1
        rot = (k * 1.7) % math.tau
        if look in ("riverbend", "camp"):
            put(palms[k % 3] if k % 3 == 0 else jungle[k % 2], x, y, rot, 0.9 + 0.3 * (k % 3) / 2, coll="Rim")
        elif look == "cascade":
            put(grand[k % 2] if k % 4 == 0 else jungle[k % 2], x, y, rot, 1.0 if k % 4 else 0.8, coll="Rim")
        elif look == "bonebog":
            put(swamp_tree[k % 2], x, y, rot, 1.2, coll="Rim")
        else:
            if k % 4:
                continue
            put(dead, x, y, rot, 1.1, coll="Rim")
        room.add(x, y, 6.0)
    print("walls: shelves %d, lips %d, rims %d, lava seeps %d" % (len(shelves), n_lips, len(rims), seeps))


def lava_seep(c, x, y, dx, dy, z, drop, k):
    """Lava welling over a shelf's lip and running down the riser into a pool below."""
    ang = math.atan2(dy, dx) + math.pi / 2
    fx, fy = props.falls(c, "Lava Seep %d" % k, x - dx * 0.4, y - dy * 0.4, z + 0.15, z - drop + 0.3, 2.2, 3.6, facing=-1,
                         throw=1.2, bulge=0.4, veils=1, foam=False, angle=ang,
                         mats=("volcano_lava", "volcano_lava", "lava_crust"))
    foot = z - drop + 0.25
    c.disc("Lava Seep Pool %d" % k, fx + dx * 1.5, fy + dy * 1.5, 2.8, foot, c.lib("volcano_lava"), coll="Props", role="visual",
           n=12, wobble=0.25, seed=k)
    g = c.game(fx + dx * 1.5, fy + dy * 1.5, foot + 1.0)
    c.entity("torch", x=g[0], y=g[1], z=g[2])
    c.entity("steam", x=g[0], y=g[1] - 0.6, z=g[2])


# ------------------------------------------------------------------ water


def depth_paint(ob, depth):
    """Vertex colour by depth (the living water's colour comes from it): depth(x, y) 0 at
    the bank .. 1 in the deep."""
    me = ob.data
    ca = kit.materials.ensure_paint(me)
    mw = ob.matrix_world
    cols = [1.0] * (4 * len(me.loops))
    for li, loop in enumerate(me.loops):
        p = mw @ me.vertices[loop.vertex_index].co
        d = max(0.0, min(1.0, depth(p.x, p.y)))
        f = d ** 1.3
        cols[4 * li:4 * li + 3] = (lerp(1.0, 0.5, f), lerp(1.0, 0.68, f), lerp(1.0, 0.8, f))
    ca.data.foreach_set("color", cols)


def water(c, ground=None):
    """The rivers and lakes in living water (Blake, notes 18 and 44: "in our original Oasis
    level before the rework, we had high quality water; let's bring it in"): the lagoon
    effect (waves, ripples of light, glitter, the sky in it), deep in the middle, clear
    and pale over the shallows."""
    mat = c.lib("valley_river", "water")
    for j, riv in enumerate(L.RIVERS):
        river = []
        for (ax, ay, az), (bx, by, bz) in zip(riv, riv[1:]):
            n = max(1, int(math.hypot(bx - ax, by - ay) / 3.0))
            for k in range(n):
                t = k / n
                river.append((lerp(ax, bx, t), lerp(ay, by, t), 2 * RIVER_HW + 8, lerp(az, bz, t) - 0.1))
        river.append((riv[-1][0], riv[-1][1], 2 * RIVER_HW + 8, riv[-1][2] - 0.1))
        ob = c.ribbon("River %d" % j, river, 2 * RIVER_HW + 8, 0, mat, role="visual", steps=8)
        depth_paint(ob, lambda x, y: 1.0 - L.river_d(x, y)[0] / (RIVER_HW + 3.0))
        if ground:
            tuck(ob, ground, lambda x, y: L.river_d(x, y)[0] > RIVER_HW - 1.0)
    for k, (lx, ly, lr, lz) in enumerate(L.LAKES):
        ob = c.disc("Lake %d" % k, lx, ly, lr + 6.0, lz - 0.1, mat, role="visual", n=36, wobble=0.12, seed=20 + k)
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.poke(bm, faces=bm.faces[:])
        bm.to_mesh(ob.data)
        bm.free()
        depth_paint(ob, lambda x, y, lx=lx, ly=ly, lr=lr: 1.0 - math.hypot(x - lx, y - ly) / (lr + 4.0))
        if ground:
            tuck(ob, ground, lambda x, y, lx=lx, ly=ly, lr=lr: math.hypot(x - lx, y - ly) > lr - 1.0)


def tuck(ob, ground, edge):
    """The water's edge into the bank (Blake, Oct 28: "the water appears to be a floating
    sheet above the sand"): wherever the land under the sheet's outer part is lower than
    the water, that part of the sheet runs down into it, so its edge is never in the air."""
    me = ob.data
    mw = ob.matrix_world
    inv = mw.inverted()
    n = 0
    for v in me.vertices:
        w = mw @ v.co
        g = ground(w.x, w.y)
        if g is None:
            continue
        # (Only near the edge: out in the channel the bed is meant to be under water.)
        if edge(w.x, w.y) and g < w.z - 0.05 and w.z - g < 4.0:
            w.z = g - 0.12
            v.co = inv @ w
            n += 1
    me.update()
    return n


def banks(c, ground, taken):
    """Life along the water (Blake, notes 19 and 46: "lots of water features like cattails
    and logs", "cattails, water lilies; look to Riverbend Palms"): cattails in the
    shallows, lily pads and lotus flowers floating off the banks, logs fallen in, reeds."""
    rnd = random.Random(31)
    clumps = [props.cattails(c, v) for v in range(3)]
    pads = [props.lily_pad(c, v) for v in range(3)]
    lotus = props.lotus(c)
    logs = [props.log(c, v) for v in range(2)]
    reeds = props.reeds(c)
    n = [0, 0, 0]
    segs = []
    for riv in L.RIVERS:
        segs += list(zip(riv, riv[1:]))
    for k in range(900):
        (ax, ay, az), (bx, by, bz) = segs[rnd.randrange(len(segs))]
        t = rnd.random()
        x, y, wz = lerp(ax, bx, t), lerp(ay, by, t), lerp(az, bz, t)
        dx, dy = bx - ax, by - ay
        d = math.hypot(dx, dy)
        nx, ny = -dy / d, dx / d
        side = 1 if rnd.random() < 0.5 else -1
        off = RIVER_HW * rnd.uniform(0.55, 1.25)
        px, py = x + nx * side * off, y + ny * side * off
        if not paint.road_clear(c, px, py, 3.5) or not taken.clear(px, py, 1.0):
            continue
        g = ground(px, py)
        if off > RIVER_HW * 0.95 and g > wz - 1.0:
            c.place(clumps[k % 3] if k % 4 else reeds, px, py, max(g, wz - 0.4), rot=rnd.uniform(0, math.tau),
                    scale=rnd.uniform(0.8, 1.4), coll="Water Life", role="visual")
            n[0] += 1
        elif off < RIVER_HW * 0.9 and g < wz - 0.5 and k % 2 == 0:
            for m in range(3 + k % 3):
                a, r = rnd.uniform(0, math.tau), rnd.uniform(0, 3.0)
                qx, qy = px + r * math.cos(a), py + r * math.sin(a)
                bloom = m == 0 and k % 4 == 0
                c.place(lotus if bloom else pads[(k + m) % 3], qx, qy, wz - 0.08, rot=rnd.uniform(0, math.tau),
                        scale=(1.3 if bloom else 0.8) + 0.6 * rnd.random(), coll="Water Life", role="visual")
                n[1] += 1
    # Logs: fallen in from the banks, half in the water.
    for j, riv in enumerate(L.RIVERS):
        for k in range(len(riv) - 1):
            (ax, ay, az), (bx, by, bz) = riv[k], riv[k + 1]
            x, y = lerp(ax, bx, 0.5), lerp(ay, by, 0.5)
            dx, dy = bx - ax, by - ay
            d = math.hypot(dx, dy)
            side = 1 if (k + j) % 2 else -1
            px, py = x - dy / d * side * (RIVER_HW + 1.0), y + dx / d * side * (RIVER_HW + 1.0)
            if paint.road_clear(c, px, py, 5.0) and taken.clear(px, py, 3.0):
                c.place(logs[k % 2], px, py, lerp(az, bz, 0.5) - 0.55, rot=math.atan2(dy, dx) + side * 0.9,
                        scale=1.1, coll="Water Life", role="visual")
                n[2] += 1
    # Round the lakes too.
    for k, (lx, ly, lr, lz) in enumerate(L.LAKES):
        for m in range(26):
            a = m * 2.39996 + k
            r = lr + rnd.uniform(-1.5, 3.0)
            x, y = lx + r * math.cos(a), ly + r * math.sin(a)
            if paint.road_clear(c, x, y, 3.0):
                c.place(clumps[m % 3], x, y, max(ground(x, y), lz - 0.4), rot=a * 3.0, scale=rnd.uniform(0.9, 1.4),
                        coll="Water Life", role="visual")
                n[0] += 1
        for m in range(14):
            a = m * 2.39996 + 1.0
            r = lr * math.sqrt(rnd.random()) * 0.8
            x, y = lx + r * math.cos(a), ly + r * math.sin(a)
            c.place(lotus if m % 5 == 0 else pads[m % 3], x, y, lz - 0.08, rot=a, scale=1.0 + 0.5 * rnd.random(),
                    coll="Water Life", role="visual")
            n[1] += 1
        x, y = lx + (lr - 2.0) * math.cos(0.7 + k), ly + (lr - 2.0) * math.sin(0.7 + k)
        c.place(logs[k % 2], x, y, lz - 0.5, rot=1.2 + k, scale=1.3, coll="Water Life", role="visual")
    print("banks: cattails %d, lilies %d, logs %d" % tuple(n))


def grand_falls(c, j, name):
    """The falls (Blake, note 43: "lets make this waterfall wayy more grand! this needs to
    be magnificent"): the river over the rim of a sheer cliff the wall's full height
    (valley_layout.falls_cliff), a broad curving sheet, white veils over it, a twin fall
    either side, the river running to the lip above, a churning foam pool, a rainbow in
    the spray, and its roar and mist."""
    fx, fy, ux, uy = L.falls_axis(j)
    foot = L.RIVERS[j][0][2]
    top = L.TOP + 0.6
    ang = math.atan2(uy, ux) + math.pi / 2
    lip_back = 5.6
    lx, ly = fx - ux * lip_back, fy - uy * lip_back
    wide = 24.0 if j == 0 else 18.0
    props.falls(c, name, lx, ly, top, foot, wide, wide * 1.3, facing=-1, throw=4.5, bulge=2.0, veils=4,
                foam_r=wide * 0.75, angle=ang)
    for side in (-1, 1):
        sx, sy = lx + uy * side * (wide * 0.5 + 5.0), ly - ux * side * (wide * 0.5 + 5.0)
        sx -= ux * 1.0
        sy -= uy * 1.0
        props.falls(c, "%s Twin %d" % (name, side), sx, sy, top - 1.0, foot, 4.0, 6.5, facing=-1, throw=3.0, bulge=0.6,
                    veils=1, foam_r=4.5, angle=ang)
    # The river above, running to the lip.
    up = [(lx - ux * k * 4.0, ly - uy * k * 4.0, wide + 2.0, top - 0.5) for k in range(12, -1, -1)]
    c.ribbon(name + " Above", up, wide + 2.0, 0, c.lib("valley_river", "water"), role="visual", steps=4)
    # Spray, roar, mist, and the rainbow in the spray.
    gx, gy, gz = c.game(fx, fy, foot)
    c.entity("waterfall", x=gx, y=gy, z=gz, top=top, width=wide, heading=math.atan2(ux, -uy))
    # (Low white mist where the water lands, under the falls, not hiding them: Blake,
    # Riverbend note 12.)
    c.entity("mist", x=gx, y=gy + 0.2, z=gz, radius=wide * 0.9, rate=12, color="#eef6ff")
    # (A true arc in one upright plane across the spray: Blake, Oct 28, "the rainbow is
    # bent. This needs to be straightened out".)
    rows = []
    for i in range(9):
        t = i / 8
        row = []
        for k in range(25):
            a = math.pi * k / 24
            r = wide * 0.8 + 2.2 * t
            ox, oy = math.cos(a) * r, math.sin(a) * r * 0.62
            p = Vector((fx + ux * 9.0 - uy * ox, fy + uy * 9.0 + ux * ox, foot + 1.0 + oy))
            row.append((p, k / 24, t))
        rows.append(row)
    props.strip(c, name + " Rainbow", rows, c.lib("rainbow"))
    # The plunge pool's water (Blake, Oct 28: "add more detail to this water, maybe some
    # water features"): rocks standing in the foam with white water round each, ripple
    # rings spreading out, stepping stones across the outflow, reeds and lilies at the
    # pool's calm edge, a fallen log, spray.
    rnd = random.Random(70 + j)
    for k in range(6):
        a = ang + math.pi + (k - 2.5) * 0.42
        r = wide * (0.35 + 0.25 * (k % 2))
        x, y = fx + math.cos(a) * r + ux * 4.0, fy + math.sin(a) * r + uy * 4.0
        c.place(props.boulder(c, "canyon_rock_moss", k % 2), x, y, foot - 0.8, rot=k * 2.1, scale=0.9 + 0.5 * rnd.random(),
                coll="Props", role="visual")
        c.disc("%s Rock Foam %d" % (name, k), x, y, 2.4, foot + 0.07, c.lib("falls_foam"), role="visual", n=14, wobble=0.3,
               seed=k + 3 * j)
    for k in range(2):  # (not a third, out past the pool: Blake, Riverbend note 14)
        c.disc("%s Ripple %d" % (name, k), fx + ux * (wide * 0.9 + 4.0 * k), fy + uy * (wide * 0.9 + 4.0 * k), 3.0 + 2.0 * k,
               foot + 0.04, c.lib("falls_foam"), role="visual", n=24, wobble=0.35, seed=40 + k)
    for k in range(5):
        t = (k - 2) * 2.6
        x, y = fx + ux * (wide * 1.15) - uy * t, fy + uy * (wide * 1.15) + ux * t
        c.place(props.boulder(c, "canyon_rock_moss", 1), x, y, foot - 0.5, rot=k, scale=0.7, coll="Props", role="visual")
    for k in range(10):
        a = ang + math.pi + rnd.uniform(-1.4, 1.4)
        r = wide * rnd.uniform(1.05, 1.3)
        x, y = fx + math.cos(a) * r + ux * 3.0, fy + math.sin(a) * r + uy * 3.0
        if k % 2:
            c.place(props.cattails(c, k % 3), x, y, foot - 0.3, rot=rnd.uniform(0, math.tau), coll="Water Life", role="visual")
        else:
            c.place(props.lily_pad(c, k % 3), x, y, foot - 0.02, rot=rnd.uniform(0, math.tau), coll="Water Life",
                    role="visual")
    a = ang + math.pi + 1.2
    c.place(props.log(c, 0), fx + math.cos(a) * wide + ux * 2.0, fy + math.sin(a) * wide + uy * 2.0, foot - 0.5, rot=a + 0.8,
            scale=1.3, coll="Water Life", role="visual")
    gs = c.game(fx + ux * 3.0, fy + uy * 3.0, foot + 0.5)
    c.entity("steam", x=gs[0], y=gs[1], z=gs[2])
    # Boulders round the pool.
    for k in range(7):
        a = ang + math.pi + (k - 3) * 0.45
        r = wide * 0.85 + 2.0
        x, y = fx + math.cos(a) * r * 0.9 + ux * 3.0, fy + math.sin(a) * r * 0.9 + uy * 3.0
        c.place(props.boulder(c, "canyon_rock_moss", k % 2), x, y, foot - 0.6, rot=k * 1.3, scale=1.6 + 0.6 * (k % 3),
                coll="Props", role="visual")


# ------------------------------------------------------------------ the camp


# The camp's village (Blake, note 1: "add more to this village: some fire places, a well,
# maybe a shed that they use to work on karts"): (x, y) of each.
WELL = (9.0, 25.0)
SHED = (-22.0, 31.0)
HEARTHS = [(-10.0, -8.0), (12.0, 10.0), (-4.0, 42.0)]
HAMLET = (-4.0, 42.0)  # a few more huts round the north hearth
HAMLET_HUTS = []
STAGE = [((-6.0, 4.0), 13.0), ((15.0, -6.0), 15.0)]  # the cutscenes' camp and the Pact Stone (Blender x, y; clear radius)


def camp(c, ground, taken):
    """The camp: huts round the Elder's fire, hearths with log benches, the well, the kart
    shed, carved totems, a hamlet to the north, and the dirt paths between them (returned
    as lists of points, for valley_village.path_ribbons). The village made over: Blake,
    Oct 28, review-valley_region 3 (see valley_village)."""
    import valley_village as vv

    cx, cy, cr = L.CAMP
    paths = []
    h = vv.hearth(c)
    for k, (x, y) in enumerate(HEARTHS):
        z = ground(x, y)
        c.place(h, x, y, z - 0.05, rot=k * 1.1, coll="Village", role="visual")
        g = c.game(x, y, z + 0.3)
        c.entity("campfire", x=g[0], y=g[1], z=g[2])
        taken.add(x, y, 5.0)
    z = ground(*WELL)
    c.place(vv.well(c), WELL[0], WELL[1], z - 0.05, rot=0.4, coll="Village")
    vv.well_hole(c, WELL[0], WELL[1], ground)
    taken.add(WELL[0], WELL[1], 4.0)
    a = math.atan2(cy - SHED[1], cx - SHED[0])
    z = min(ground(SHED[0] + dx, SHED[1] + dy) for dx in (-4, 0, 4) for dy in (-3, 0, 3))
    rot = a + math.pi / 2
    c.place(vv.kart_shed(c), SHED[0], SHED[1], z - 0.1, rot=rot, coll="Village", role="visual")
    c.place(vv.repair_sign(c), SHED[0], SHED[1], z - 0.1, rot=rot, coll="Village", role="visual")
    c.place(rp.kart_shed_collider(c), SHED[0], SHED[1], z - 0.1, rot=rot, coll="Collision", role="collision")
    # The kart taken apart on its blocks under the hoist (the game's own kart: Blake, note
    # 12, "an actual rendered cart thats dissasembled"), its nose to the open front.
    ca, sa = math.cos(rot), math.sin(rot)
    kx, ky = SHED[0] + (-1.9 * ca - 0.2 * sa), SHED[1] + (-1.9 * sa + 0.2 * ca)
    face = rot - math.pi / 2
    g = c.game(kx, ky, z - 0.1)
    c.entity("kart_wreck", x=g[0], y=g[1], z=g[2], heading=round(math.atan2(math.cos(face), -math.sin(face)), 3))
    taken.add(SHED[0], SHED[1], 8.0)
    # The hamlet: huts round the north hearth, their doors to the fire.
    hx, hy = HAMLET
    for k in range(4):
        a = k * math.tau / 4 + 0.6
        x, y = hx + 10.0 * math.cos(a), hy + 10.0 * math.sin(a)
        if L.wall_sd(x, y) > -10.0 or not paint.road_clear(c, x, y, 6.0):
            continue
        vv.place_hut(c, k + 2, x, y, ground(x, y) - 0.1, a + math.pi, scale=0.85)
        taken.add(x, y, 5.0)
        HAMLET_HUTS.append((x, y))
        # (From its door to the fire.)
        paths.append(vv.wander((x - 3.6 * math.cos(a), y - 3.6 * math.sin(a)),
                               (hx + 2.6 * math.cos(a), hy + 2.6 * math.sin(a)), bend=1.2 * (-1) ** k, seed=k))
    # The camp's folk: about the hamlet's hearth, the well and the kart shed (their homes
    # for src/overworld/villagers.ts).
    for k, (x, y, n) in enumerate(((hx, hy - 6.0, 3), (WELL[0] - 4.0, WELL[1] - 5.0, 2), (SHED[0] + 6.0, SHED[1] - 8.0, 2))):
        face = math.atan2(cy - y, cx - x)
        g = c.game(x, y, ground(x, y))
        c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=10.0, n=n, folk="valley",
                 heading=round(math.atan2(-math.cos(face), math.sin(face)), 3))
    # (The totems: place_totems, once every hut and path is down.)
    # The paths: from the square to the well and on to the hamlet, and to the shed.
    sq = (cx, cy + cr - 2.0)
    wd = math.hypot(WELL[0] - sq[0], WELL[1] - sq[1])
    to_well = (WELL[0] - (WELL[0] - sq[0]) / wd * 4.2, WELL[1] - (WELL[1] - sq[1]) / wd * 4.2)
    paths.append(vv.wander(sq, to_well, bend=1.5, seed=3))
    hd = math.hypot(HAMLET[0] - WELL[0], HAMLET[1] - WELL[1])
    from_well = (WELL[0] + (HAMLET[0] - WELL[0]) / hd * 4.2, WELL[1] + (HAMLET[1] - WELL[1]) / hd * 4.2)
    to_ham = (HAMLET[0] - (HAMLET[0] - WELL[0]) / hd * 3.0, HAMLET[1] - (HAMLET[1] - WELL[1]) / hd * 3.0)
    paths.append(vv.wander(from_well, to_ham, bend=-2.0, seed=5))
    paths.append(vv.wander((cx - cr + 4.0, cy + 6.0), (SHED[0] + 4.0, SHED[1] - 4.0), bend=2.0, seed=7))
    return paths


def place_totems(c, ground, huts, paths):
    """The carved totems, placed with thought (Blake, Oct 29, notes 14 and 17: "relocate
    the totem poles strategically ... in a place that doesn't ruin the cutscenes"; one
    stood in a hut): one keeping watch by each of the camp's working places, the well,
    the kart shed and the hamlet's hearth, and one at the head of the west path out of
    the square. Each at the spot round its place furthest from every hut and path, well
    clear of the cutscenes' ground (the camp's middle and the Pact Stone) and the road,
    facing the square."""
    import valley_village as vv

    cx, cy, cr = L.CAMP
    pts = [p for path in paths for p in vv._catmull(path, step=1.0)]
    huts = list(huts) + HAMLET_HUTS
    features = [WELL, SHED, HAMLET, (cx - cr + 2.0, cy - 6.0)]
    placed = []
    for k, (fx, fy) in enumerate(features):
        best = None
        for r in (4.5, 5.5, 6.5, 7.5, 8.5):
            for i in range(32):
                a = i * math.tau / 32
                x, y = fx + r * math.cos(a), fy + r * math.sin(a)
                gap = min([math.hypot(x - hx, y - hy) - 6.5 for hx, hy in huts] or [9.0])
                gap = min(gap, min([math.hypot(x - px, y - py) - 2.6 for px, py in pts] or [9.0]))
                gap = min(gap, *[math.hypot(x - sx, y - sy) - sr for (sx, sy), sr in STAGE])
                gap = min(gap, *[math.hypot(x - tx, y - ty) - 9.0 for tx, ty in placed] or [9.0])
                if gap <= 0.0 or not paint.road_clear(c, x, y, 4.0) or L.wall_sd(x, y) > -6.0:
                    continue
                if best is None or gap > best[0]:
                    best = (gap, x, y)
        if best is None:
            print("totem %d: no room" % k)
            continue
        _, x, y = best
        rot = math.atan2(cy - y, cx - x) + math.pi / 2
        vv.totem(c, x, y, ground(x, y) - 0.2, rot, k)
        placed.append((x, y))
    print("totems placed: %d" % len(placed))


def pact_stone_ground(c, ground):
    """The valley's Pact Stone given a setting worthy of it, subtly (Blake, Oct 29, note
    18: "a very important artifact ... spruce up the surroundings subtly without ruining
    the cutscenes"): a round of old flagstones laid flush round its foot, a kerb of low
    worn stones round that, wildflowers growing between them, and offerings left at its
    foot, a few bowls of flowers and fruit. Nothing knee-high or more, nothing solid:
    the camera and the actors pass over it all. (After the attack: the flowers gone.)"""
    import valley_village as vv
    import gulch_scenery as gs

    sx, sy = STAGE[1][0]
    m = gs.Mesh()
    n = 24
    R = 3.0

    def P(r, a, lift):
        rr = r * (1.0 + 0.04 * math.sin(a * 5 + 1.0))
        x, y = sx + rr * math.cos(a), sy + rr * math.sin(a)
        return (x, y, ground(x, y) + lift)

    def disc(bm):
        cv = bm.verts.new((sx, sy, ground(sx, sy) + 0.07))
        ring_ = [bm.verts.new(P(R, i * math.tau / n, 0.06)) for i in range(n)]
        for i in range(n):
            bm.faces.new((cv, ring_[i], ring_[(i + 1) % n]))

    m.add(("ruin_stone", "road"), disc)
    # The kerb: low worn stones round the flagstones, a gap toward the camp.
    k = 0
    for i in range(18):
        a = i * math.tau / 18
        if abs(math.atan2(math.sin(a - 2.4), math.cos(a - 2.4))) < 0.45:
            continue
        x, y = sx + (R + 0.35) * math.cos(a), sy + (R + 0.35) * math.sin(a)
        z = ground(x, y)
        h = 0.18 + 0.1 * ((i * 7) % 3) / 2
        m.add(("ruin_stone", "wall"), lambda bm, x=x, y=y, z=z, a=a, h=h: vv.cuboid(bm, (x, y, z + h / 2 - 0.05),
                                                                                   (0.62, 0.42, h), a + math.pi / 2))
        k += 1
    ob = m.build(c, "Pact Stone Ground", "Village", role="visual")
    # Wildflowers between the kerb stones and round about, and offerings at its foot.
    import props

    fl = props.flowers(c)
    for i in range(9):
        a = i * 2.39996 + 0.4
        r = R + 0.9 + 1.4 * ((i * 5) % 3) / 2
        x, y = sx + r * math.cos(a), sy + r * math.sin(a)
        if not paint.road_clear(c, x, y, 1.5) or RUIN:
            continue
        c.place(fl, x, y, ground(x, y) - 0.05, rot=a, scale=0.8, coll="Village", role="visual")
    if not RUIN:
        bowl = rp.offering_bowl(c)
        for i, a in enumerate((2.0, 2.45, 2.85)):
            x, y = sx + 1.6 * math.cos(a), sy + 1.6 * math.sin(a)
            c.place(bowl, x, y, ground(x, y) + 0.04, rot=a, coll="Village", role="visual")
    return ob


def paint_paths(c, ter, paths, width=3.6, mat=("camp_earth", "dirt")):
    """Dirt paths painted into the land (Blake: "dirt paths connecting the villages",
    without grass in the dirt)."""
    import numpy as np

    me = ter.data
    n = len(me.polygons)
    cen = np.empty(n * 3, np.float32)
    me.polygons.foreach_get("center", cen)
    cen = cen.reshape(n, 3)
    hit = np.zeros(n, bool)
    for path in paths:
        for (ax, ay), (bx, by) in zip(path, path[1:]):
            dx, dy = bx - ax, by - ay
            ll = dx * dx + dy * dy or 1.0
            t = np.clip(((cen[:, 0] - ax) * dx + (cen[:, 1] - ay) * dy) / ll, 0.0, 1.0)
            # (a little wander, so they aren't ruled lines)
            wob = 0.6 * np.sin(cen[:, 0] / 5.0) * np.cos(cen[:, 1] / 7.0)
            d = np.hypot(cen[:, 0] - ax - t * dx, cen[:, 1] - ay - t * dy) + wob
            hit |= d < width / 2
    faces = [int(i) for i in np.nonzero(hit)[0]]
    if faces:
        c.assign(ter, c.lib(*mat), faces)
    print("paths: %d faces" % len(faces))


def home_path(x, y, c):
    """A path from a home's door to the road."""
    q, _ = c.nearest(x, y)
    return [(x, y), (q.p.x, q.p.y)]


# ------------------------------------------------------------------ the Cascade


def ruin_site(c, x, y, rot, ground, k):
    """A ruined temple in the trees (Blake, note 21: "we need some ruins in this section,
    we want it to look more like the actual level"): a stepped platform, stairs up its
    front, broken columns, a fallen lintel, an idol's head on top, tumbled blocks."""
    ca, sa = math.cos(rot), math.sin(rot)

    def at(lx, ly):
        return x + lx * ca - ly * sa, y + lx * sa + ly * ca

    z = min(ground(*at(dx, dy)) for dx in (-8, 0, 8) for dy in (-7, 0, 7)) - 0.3
    temple = ("jungle_temple", "wall")
    glyph = ("ruin_glyph", "wall")
    for t, (hx, hy, hh) in enumerate(((9.0, 7.5, 1.8), (7.0, 5.8, 1.7), (5.0, 4.2, 1.6))):
        zz = z + sum(q[2] for q in ((9.0, 7.5, 1.8), (7.0, 5.8, 1.7))[:t])
        box(c, "Temple Ruin %d Tier %d" % (k, t), x, y, hx, hy, zz - (1.5 if t == 0 else 0.0), zz + hh,
            glyph if t == 1 else temple, rot=rot)
    sx, sy = at(0.0, -8.8)
    c.place(props.stairs(c, 6, 4.0, 0.58, 0.9), sx, sy, z, rot=rot, coll="Ruins")
    top = z + 5.1
    for s in (-1, 1):
        px, py = at(s * 3.6, -2.8)
        c.place(props.ruin_column(c, k + (s > 0)), px, py, top - 0.1, rot=rot, scale=0.9, coll="Ruins")
    ix, iy = at(0.0, 1.0)
    c.place(props.idol_head(c), ix, iy, top - 0.1, rot=rot, scale=0.75, coll="Ruins")
    lx, ly = at(10.5, -3.0)
    box(c, "Temple Ruin %d Lintel" % k, lx, ly, 4.2, 0.9, ground(lx, ly) - 0.4, ground(lx, ly) + 1.0, glyph, rot=rot + 0.5)
    for s in (-1, 1):
        bx, by = at(s * 11.0, 3.0)
        c.place(props.ruin_blocks(c, k + s), bx, by, ground(bx, by) - 0.3, rot=rot + s, coll="Ruins")
    vx, vy = at(-9.0, 5.0)
    c.place(props.vine_curtain(c, 1, 11.0), vx, vy, top - 1.5, rot=rot + math.pi, coll="Vines", role="visual")


def cascade(c, ground, taken):
    """The Cascade's jungle: great trees on real roots (notes 20 and 22: two more), ruined
    temples near the road (note 21)."""
    rnd = random.Random(23)
    cas = lambda x, y: (L.pocket_at(x, y) == "cascade" and L.wall_sd(x, y) < -10.0  # noqa: E731
                        and L.river_d(x, y)[0] > RIVER_HW + 6)
    sites = 0
    for _ in range(4000):
        if sites >= 3:
            break
        x, y = rnd.uniform(50, 200), rnd.uniform(60, 220)
        if not cas(x, y) or not taken.clear(x, y, 14.0):
            continue
        if not paint.road_clear(c, x, y, 13.0) or paint.road_clear(c, x, y, 30.0):
            continue
        q, _ = c.nearest(x, y)
        rot = math.atan2(q.p.y - y, q.p.x - x) + math.pi / 2
        ok = all(L.wall_sd(x + dx, y + dy) < -3.0 for dx in (-9, 9) for dy in (-9, 9))
        if not ok:
            continue
        ruin_site(c, x, y, rot, ground, sites)
        taken.add(x, y, 14.0)
        sites += 1
    print("cascade ruins:", sites)
    trees = 0
    near = lambda x, y: (L.pocket_at(x, y) == "cascade" and L.wall_sd(x, y) < -3.0  # noqa: E731
                         and L.river_d(x, y)[0] > RIVER_HW + 5)
    for v in range(2):
        trees += len(place_big(c, rp.great_tree(c, v), 4, (40, 200, 50, 225), near, ground, taken, 160 + v, room=13.0,
                               margin=6.0, trunk=(3.4, 14.0)))
    print("great trees:", trees)


def cascade_gate(c, q, half, ground, k):
    """The Cascade's threshold (Blake, note 23: "this is just floating, we need to
    completely redo this"): two stepped temple pillars either side of the road and the
    lintel resting ON them, a carved head over the middle."""
    rot = math.atan2(q.r.y, q.r.x)
    temple = ("jungle_temple", "wall")
    glyph = ("ruin_glyph", "wall")
    zs = []
    for sd in (-1, 1):
        x, y = q.p.x + q.r.x * sd * (half + 2.2), q.p.y + q.r.y * sd * (half + 2.2)
        g = ground(x, y)
        zs.append(g)
        box(c, "Cascade Gate %d Plinth %d" % (k, sd), x, y, 2.4, 2.4, g - 1.0, g + 1.2, temple, rot=rot)
        box(c, "Cascade Gate %d Pillar %d" % (k, sd), x, y, 1.7, 1.7, g + 1.2, q.p.z + 9.2, glyph, rot=rot)
        box(c, "Cascade Gate %d Capital %d" % (k, sd), x, y, 2.2, 2.2, q.p.z + 9.2, q.p.z + 10.0, temple, rot=rot)
    box(c, "Cascade Gate %d Lintel" % k, q.p.x, q.p.y, half + 4.4, 1.6, q.p.z + 10.0, q.p.z + 11.8, glyph, rot=rot,
        role="visual")
    box(c, "Cascade Gate %d Cornice" % k, q.p.x, q.p.y, half + 3.2, 1.2, q.p.z + 11.8, q.p.z + 12.6, temple, rot=rot,
        role="visual")
    c.place(props.idol_head(c), q.p.x, q.p.y, q.p.z + 12.5, rot=math.atan2(q.t.y, q.t.x) + math.pi / 2, scale=0.45,
            role="visual")


# ------------------------------------------------------------------ the swamp


def swamp(c, ground, taken):
    """The swamp made immersive (Blake, note 35: "think large canopy trees like we have in
    Bonebog"): more colossal swamp giants, a canopy of leaves overhead with gaps of sky,
    vines and moss hanging down."""
    rnd = random.Random(41)
    bog = lambda x, y: (L.pocket_at(x, y) == "bonebog" and L.wall_sd(x, y) < -4.0  # noqa: E731
                       and all(math.hypot(x - px, y - py) > pr + 2 for px, py, pr in L.POOLS))
    giants = 0
    for v in range(2):
        giants += len(place_big(c, sp.swamp_giant(c, v), 5, (-215, -25, -230, -85), bog, ground, taken, 190 + v, room=14.0,
                                margin=7.0, trunk=(3.6, 14.0), scale=(0.7, 0.95), sink=1.0))
    patches = 0
    vines = [sp.hanging_vine(c, v, 14.0 + 4.0 * v) for v in range(2)]
    beards = [sp.moss_beard(c, v, 5.0) for v in range(2)]
    done = []
    for k in range(60):
        x, y = rnd.uniform(-220, -30), rnd.uniform(-230, -90)
        if L.pocket_at(x, y) != "bonebog" or L.wall_sd(x, y) > 6.0 or not taken.clear(x, y, 0.0):
            continue
        if any(math.hypot(x - px, y - py) < 30.0 for px, py in done):
            continue
        done.append((x, y))
        z = 26.0 + 6.0 * rnd.random()
        c.place(sp.canopy_patch(c, k % 2), x, y, z, rot=rnd.uniform(0, math.tau), scale=rnd.uniform(0.8, 1.1),
                coll="Canopy", role="visual")
        for m in range(4):
            a, r = rnd.uniform(0, math.tau), rnd.uniform(4.0, 14.0)
            vx, vy = x + r * math.cos(a), y + r * math.sin(a)
            if paint.road_clear(c, vx, vy, 2.0):
                c.place(vines[m % 2] if m % 2 else beards[m % 2], vx, vy, z + 1.0, rot=a, coll="Canopy", role="visual")
        patches += 1
    print("swamp: giants %d, canopy %d" % (giants, patches))


# ------------------------------------------------------------------ Ember


def ember(c, ground, taken):
    """Ember's slopes (Blake, notes 25, 27, 30): more trees on fire, lava geysers (Snowy
    Summit's, recoloured: lava ones) out on the barren ground, and an obsidian hut or two
    with their folk."""
    rnd = random.Random(53)
    em = lambda x, y: (L.pocket_at(x, y) in ("ember", "gulch") and L.wall_sd(x, y) < -8.0  # noqa: E731
                       and all(math.hypot(x - px, y - py) > pr + 6 for px, py, pr in L.LAVA))
    burning = 0
    for v in range(2):
        for x, y in paint.scatter(c, rp.burning_tree(c, v), 7, 260.0, em, ground, taken, 210 + v, room=7.0, scale=(0.9, 1.3),
                                  road_margin=6.0, trunk=(0.7, 6.0), tries=600):
            g = c.game(x, y, ground(x, y) + 7.5)
            c.entity("campfire", x=g[0], y=g[1], z=g[2])
            if burning % 2 == 0:
                c.entity("torch", x=g[0], y=g[1] - 3.0, z=g[2])
            burning += 1
    geysers = 0
    for k in range(3000):
        if geysers >= 5:
            break
        x, y = rnd.uniform(40, 200), rnd.uniform(-215, -60)
        if L.pocket_at(x, y) != "ember" or L.wall_sd(x, y) > -6.0 or not taken.clear(x, y, 8.0):
            continue
        if not paint.road_clear(c, x, y, 8.0) or any(math.hypot(x - px, y - py) < pr + 10 for px, py, pr in L.LAVA):
            continue
        z = ground(x, y)
        c.place(rp.lava_vent(c, k % 2), x, y, z - 0.3, rot=k, coll="Props")
        g = c.game(x, y, z + 1.2)
        c.entity("geyser", x=g[0], y=g[1], z=g[2], r=2.6, height=16.0 + 4.0 * (k % 2), period=8.0, offset=1.6 * geysers,
                 warn=1.6, blast=2.4, launch=0.0, lava=True)
        taken.add(x, y, 9.0)
        geysers += 1
    print("ember: burning trees %d, lava geysers %d" % (burning, geysers))


def obsidian_house(c, name, x, y, z, rot, k):
    c.place(rp.obsidian_hut(c, k % 2), x, y, z - 0.3, rot=rot, name=name)
    g = c.game(x, y, z + 3.0)
    c.entity("chimney", x=g[0], y=g[1] + 2.2, z=g[2])


# ------------------------------------------------------------------ the volcano


VOLCANO = (262.0, -262.0, 118.0, 190.0)  # x, y, base radius, the rim's height


def volcano(c):
    """The volcano over Ember (Blake, note 29: "change the shape to be more volcano like and
    redo the colour and lava coming out"): a broad cone, its flanks swooping up concave
    to a crater rim breached on the valley's side, gullied with ridges between, dark ash
    below, black rock above, lava glowing in its crater and running down the gullies from
    the breach."""
    vx, vy, R, H = VOLCANO
    base = 20.0
    rc = 24.0  # the crater's rim
    breach = math.atan2(-vy, -vx)  # (toward the valley)
    n = 64
    radii = [rc * 0.45, rc * 0.7, rc] + [rc + (R - rc) * (k / 12.0) ** 1.3 for k in range(1, 13)]
    bm = bmesh.new()
    rows = []

    def notch(a):
        d = math.atan2(math.sin(a - breach), math.cos(a - breach))
        return smooth((0.32 - abs(d)) / 0.22)

    def gully(a):
        return 0.5 + 0.5 * math.sin(a * 9.0 + 0.7) * math.cos(a * 4.0)

    for r in radii:
        row = []
        for i in range(n):
            a = i * math.tau / n
            nb = notch(a)
            if r < rc:
                z = H - 26.0 + 6.0 * (r / rc) - 8.0 * nb * 0.0
            else:
                t = (r - rc) / (R - rc)
                z = base + (H - base) * (1.0 - t) ** 2.2
                # (Its foot runs down under the land: Blake, Oct 28, its skirt's edge stood
                # in the air over Ember's road.)
                z -= 16.0 * smooth((t - 0.8) / 0.2)
                z -= nb * 14.0 * (1.0 - t) ** 3
                z -= 5.0 * gully(a) * math.sin(math.pi * min(1.0, t * 1.4))
            rr = r * (1.0 + 0.05 * math.sin(a * 5.0 + 1.0) + 0.03 * math.sin(a * 13.0))
            row.append(bm.verts.new((vx + rr * math.cos(a), vy + rr * math.sin(a), z)))
        rows.append(row)
    hub = bm.verts.new((vx, vy, H - 26.0))
    for i in range(n):
        bm.faces.new((hub, rows[0][i], rows[0][(i + 1) % n]))
    for lo, hi in zip(rows, rows[1:]):
        for i in range(n):
            bm.faces.new((lo[i], hi[i], hi[(i + 1) % n], lo[(i + 1) % n]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = c.mesh_object("Volcano", bm, "Rocks", "visual")
    groups = {"crater": [], "lava": [], "black": [], "rock": [], "ash": []}
    for p in ob.data.polygons:
        r = math.hypot(p.center.x - vx, p.center.y - vy)
        if r < rc * 0.5:
            groups["lava"].append(p.index)
        elif r < rc + 1.0:
            groups["crater"].append(p.index)
        elif p.center.z > H - 50:
            groups["black"].append(p.index)
        elif p.center.z > base + 40:
            groups["rock"].append(p.index)
        else:
            groups["ash"].append(p.index)
    for key, mat in (("lava", ("volcano_lava", "lava")), ("crater", ("cave_rock", "wall")), ("black", ("obsidian_cliff", "wall")),
                     ("rock", ("black_rock", "wall")), ("ash", ("ember_ash", "wall"))):
        if groups[key]:
            c.assign(ob, c.lib(*mat), groups[key])
    ob.data.shade_flat()
    # Lava from the breach, down the gullies.
    for j, da in enumerate((-0.12, 0.0, 0.14)):
        pts = []
        for k in range(40):
            t = k / 39.0
            r = rc - 2.0 + (R * 0.85 - rc) * t
            a = breach + da * (1.0 + 2.0 * t) + 0.05 * math.sin(t * 9.0 + j)
            nb = notch(a)
            tt = (r - rc) / (R - rc)
            z = base + (H - base) * (1.0 - max(0.0, tt)) ** 2.2 - nb * 14.0 * (1.0 - max(0.0, tt)) ** 3
            z -= 5.0 * gully(a) * math.sin(math.pi * min(1.0, max(0.0, tt) * 1.4))
            pts.append((vx + r * math.cos(a), vy + r * math.sin(a), 3.0 + 6.0 * t + 2.0 * (j == 1), z + 0.6))
        c.ribbon("Volcano Lava %d" % j, pts, 6.0, 0, c.lib("volcano_lava"), coll="Rocks", role="visual", steps=2)
        crust = [(x, y, w + 4.0, z - 0.25) for x, y, w, z in pts]
        c.ribbon("Volcano Crust %d" % j, crust, 8.0, 0, c.lib("lava_crust"), coll="Rocks", role="visual", steps=2)
    gx, gy, gz = c.game(vx, vy, H - 18.0)
    c.entity("eruption", x=gx, y=gy, z=gz, period=14.0, offset=3.0)
    for k in range(3):
        a = breach + (k - 1) * 0.5
        g = c.game(vx + rc * 0.6 * math.cos(a), vy + rc * 0.6 * math.sin(a), H - 22.0)
        c.entity("campfire", x=g[0], y=g[1], z=g[2])


# ------------------------------------------------------------------ the tunnels


def wall_point(c, q, side, height, inset):
    """A point on a bore's wall: `side` -1/1, `height` over the road, `inset` m in from
    the wall (the bore's half width from c.tunnel)."""
    return q.p.x + q.r.x * side * inset, q.p.y + q.r.y * side * inset, q.p.z + height


def sconces(c, s0, s1, half, every=11.0, height=4.6, lit_from=0.0):
    """Torches in iron cages along both walls of a bore (Blake, notes 15 and 41), lit."""
    sc = rp.wall_sconce_cage(c)
    s = s0 + 5.0 + lit_from
    k = 0
    while s < s1 - 4.0:
        q = c.at(s)
        sd = 1 if k % 2 else -1
        x, y, z = wall_point(c, q, sd, height, half - 0.15)
        rx, ry = q.r.x * sd, q.r.y * sd
        rot = math.atan2(-rx, ry) + math.pi
        c.place(sc, x, y, z, rot=rot, coll="Tunnels", role="visual")
        g = c.game(x - rx * 0.7, y - ry * 0.7, z + 1.0)
        c.entity("torch", x=g[0], y=g[1], z=g[2])
        # Its fire, the game's own, over the basket (render/fire.ts).
        fx, fy = x + 0.7 * math.sin(rot), y - 0.7 * math.cos(rot)
        f = c.game(fx, fy, z + 0.82)
        c.entity("fire", x=f[0], y=f[1], z=f[2], size=0.5)
        s += every
        k += 1
    return k


def log_tunnel(c, s0, s1, ro, ri, lift):
    """Inside the Fallen Giant (note 41): torches up its walls all the way through, and once
    into the swamp's end, cobwebs in its corners and roots hanging from its roof."""
    sc = rp.wall_sconce_cage(c)
    webs = [sp.cobweb(c, 0), sp.cobweb(c, 1)]
    roots = [rp.root_curtain(c, v, 5.0 + 2.0 * v) for v in range(2)]
    s = s0 - 4.0
    k = 0
    while s < s1 + 4.0:
        q = c.at(s)
        sd = 1 if k % 2 else -1
        th = 0.35
        side = Vector((q.r.x, q.r.y, 0.0)).normalized() * sd
        p = Vector((q.p.x, q.p.y, q.p.z + lift)) + (side * math.cos(th) + Vector((0, 0, math.sin(th)))) * (ri - 0.2)
        rot = math.atan2(side.x, -side.y) + math.pi
        c.place(sc, p.x, p.y, p.z - 1.0, rot=rot, coll="Tunnels", role="visual")
        g = c.game(p.x - side.x * 0.8, p.y - side.y * 0.8, p.z)
        c.entity("torch", x=g[0], y=g[1], z=g[2])
        # Its fire, the game's own (render/fire.ts), over the basket.
        f = c.game(p.x + 0.7 * math.sin(rot), p.y - 0.7 * math.cos(rot), p.z - 1.0 + 0.82)
        c.entity("fire", x=f[0], y=f[1], z=f[2], size=0.5)
        s += 10.0
        k += 1
    # The swamp's end: webs and roots (the last third, and out past the mouth). Each web is
    # strung across the log's own wall (Blake, Oct 28: "these spider webs need to make
    # sense, they're not connected correctly"): a fan in the trunk's cross-section, every
    # spoke ending on the bark, its hub hanging just off the wall above the road.
    s = s0 + (s1 - s0) * 0.55
    k = 0
    void(webs)
    while s < s1 + 6.0:
        q = c.at(s)
        t = Vector((q.t.x, q.t.y, 0.0)).normalized()
        face = math.atan2(-t.x, t.y)
        for sd in (-1, 1):
            if (k + (sd > 0)) % 2:
                continue
            side = Vector((q.r.x, q.r.y, 0.0)).normalized() * sd
            th = 0.75 + 0.25 * (k % 3)
            log_web(c, "Log Web %d %d" % (k, sd), Vector((q.p.x, q.p.y, q.p.z + lift)), side, ri, th, seed=k * 2 + (sd > 0))
        top = Vector((q.p.x, q.p.y, q.p.z + lift + ri - 0.4))
        c.place(roots[k % 2], top.x + q.r.x * 3.0 * (1 if k % 2 else -1), top.y + q.r.y * 3.0 * (1 if k % 2 else -1), top.z,
                rot=face, coll="Tunnels", role="visual")
        s += 7.0
        k += 1


def void(*_):
    pass


def log_web(c, name, centre, side, ri, th, seed=0, span=0.8, spokes=6, rings=5):
    """A cobweb across the inside of a round tunnel (radius `ri` round `centre`, `side`
    the horizontal unit across it): spokes from a hub out to the wall between the angles
    th - span and th + span (0 at the side, up toward the roof), threads round between."""
    rnd = random.Random(seed)
    up = Vector((0, 0, 1))
    wall = lambda a: centre + (side * math.cos(a) + up * math.sin(a)) * (ri - 0.05)  # noqa: E731
    hub = centre + (side * math.cos(th) + up * math.sin(th)) * (ri * 0.45)
    ends = [wall(th - span + 2 * span * i / (spokes - 1) + rnd.uniform(-0.05, 0.05)) for i in range(spokes)]
    # (and one strand up to the roof and one down to the wall below, holding it)
    bm = bmesh.new()
    w = 0.035
    normal = side.cross(up).normalized()

    def thread(p, q):
        d = q - p
        if d.length < 1e-4:
            return
        x = d.cross(normal).normalized() * w
        vs = [bm.verts.new(p - x), bm.verts.new(q - x), bm.verts.new(q + x), bm.verts.new(p + x)]
        bm.faces.new(vs)

    for e in ends:
        thread(hub, e)
    for r in range(1, rings + 1):
        f = r / (rings + 0.7)
        pts = [hub.lerp(e, f) for e in ends]
        for p, q in zip(pts, pts[1:]):
            mid = (p + q) / 2
            mid = hub.lerp(mid, 0.96)
            thread(p, mid)
            thread(mid, q)
    ob = c.mesh_object(name, bm, "Tunnels", "visual")
    c.assign(ob, c.lib("cobweb"))
    return ob


def lava_tube(c, s0, s1, half):
    """The Lava Tube made grand (Blake, notes 31 and 33: "too bland"; "the lava on the side
    here is strange"): lava channels set down in basalt-kerbed troughs along both walls,
    their glow lighting the bore, basalt columns standing against the walls, steam."""
    cols = props.basalt_columns(c)
    s = s0 + 3.0
    k = 0
    while s < s1 - 3.0:
        q = c.at(s)
        for sd in (-1, 1):
            x, y, z = wall_point(c, q, sd, 0.0, half - 1.2)
            c.place(cols, x, y, z - 1.0, rot=k * 0.9 + sd, scale=(0.55, 0.55, 1.05), coll="Tunnels", role="visual")
        s += 9.0
        k += 1
    lip = rp.lava_channel_lip(c, 4.4)
    for sd in (-1, 1):
        strip = []
        s = s0 + 2.0
        while s < s1 - 2.0:
            q = c.at(s)
            off = c.width / 2 + 2.6
            strip.append((q.p.x + q.r.x * sd * off, q.p.y + q.r.y * sd * off, 2.0, q.p.z - 0.05))
            s += 2.0
        c.ribbon("Lava Tube Lava %d" % sd, strip, 2.0, 0, c.lib("volcano_lava", "lava"), role="visual", steps=2)
        s = s0 + 4.0
        k = 0
        while s < s1 - 4.0:
            q = c.at(s)
            for o in (c.width / 2 + 1.2, c.width / 2 + 4.0):
                x, y = q.p.x + q.r.x * sd * o, q.p.y + q.r.y * sd * o
                c.place(lip, x, y, q.p.z - 0.45, rot=math.atan2(q.t.y, q.t.x), coll="Tunnels", role="visual")
            if k % 2 == 0:
                x, y = q.p.x + q.r.x * sd * (c.width / 2 + 2.6), q.p.y + q.r.y * sd * (c.width / 2 + 2.6)
                g = c.game(x, y, q.p.z + 1.2)
                c.entity("torch", x=g[0], y=g[1], z=g[2])
                c.entity("bubbles", x=g[0], y=g[1] - 1.0, z=g[2], r=0.9, molten=True)
            s += 4.4
            k += 1


def temple_tunnel(c, s0, s1, half):
    """The Temple Steps' bore carved out (Blake, notes 14 and 15: "a bit more detailed",
    "some lights in this tunnel"): pilasters along both walls, a frieze of glyphs above
    them, and a torch between every pair."""
    s = s0 + 2.0
    k = 0
    while s < s1 - 2.0:
        q = c.at(s)
        rot = math.atan2(q.r.y, q.r.x)
        for sd in (-1, 1):
            x, y, z = wall_point(c, q, sd, 0.0, half - 0.5)
            box(c, "Temple Pilaster %d %d" % (k, sd), x, y, 0.9, 1.1, z - 0.6, z + 6.0, ("jungle_temple", "wall"), rot=rot,
                role="visual", coll="Tunnels")
        s += 7.0
        k += 1
    s = s0
    while s < s1:
        q = c.at(s)
        rot = math.atan2(q.r.y, q.r.x)
        for sd in (-1, 1):
            x, y, z = wall_point(c, q, sd, 0.0, half - 0.25)
            box(c, "Temple Frieze %d %d" % (int(s), sd), x, y, 0.35, 2.1, z + 5.2, z + 6.4, ("ruin_glyph", "wall"), rot=rot,
                role="visual", coll="Tunnels")
        s += 4.0
    return sconces(c, s0, s1, half - 0.4, every=7.0, height=3.6, lit_from=1.5)


# ------------------------------------------------------------------ the air


def area_air(c):
    """Each area's own extras in its air (on top of its course's: Bonebog's fireflies and
    Ember's ash come from the courses themselves, src/overworld/air.ts): Riverbend's
    pollen in the sun, the Cascade's spray drifting through its canyon."""
    c.entity("area_ambient", area="riverbend", effect="sparkles", rate=9, radius=34,
             colors=["#fff6c0", "#ffe9a0", "#ffffff", "#f8ffd0"])
    c.entity("area_ambient", area="cascade", effect="sparkles", rate=12, radius=28,
             colors=["#e8fbff", "#c8f0ff", "#ffffff"])
    c.entity("area_ambient", area="hub", effect="sparkles", rate=4, radius=30, colors=["#fff6c0", "#ffffff"])


def shade_walls(c, ter):
    """Light and shade on the walls (vertex colour, multiplied into the textures): each
    riser darker at its foot, under the shelf above; Ember's walls fading darker and
    darker the higher they climb (Blake, note 24: "have the walls fade into darker and
    darker rock"); the swamp's a little gloomier."""
    import numpy as np
    from pocket_kit import tier_cum

    me = ter.data
    nv = len(me.vertices)
    co = np.empty(nv * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(nv, 3)
    vcol = np.ones((nv, 3), np.float32)
    for i in range(nv):
        x, y, z = float(co[i, 0]), float(co[i, 1]), float(co[i, 2])
        wi = L.wall_info(x, y)
        look = POCKET_LOOK[wi["pocket"]]
        if wi["t"] <= 0.02:
            if look == "bonebog":
                vcol[i] = (0.86, 0.9, 0.84)
            continue
        frac = (z - wi["floor"]) / max(1.0, L.TOP - wi["floor"])
        if wi["past"] > 0:
            frac = 1.0
        cum = tier_cum(wi["n"])
        k = 0
        while k < wi["n"] - 1 and frac > cum[k + 1]:
            k += 1
        u = (frac - cum[k]) / max(1e-3, cum[k + 1] - cum[k])
        f = 0.72 + 0.28 * smooth(u / 0.45)  # (the foot of each riser in shade)
        if look == "ember":
            f *= lerp(1.0, 0.5, smooth(min(1.0, frac)))
            vcol[i] = (f * 1.0, f * 0.92, f * 0.88)
        elif look == "bonebog":
            vcol[i] = (f * 0.86, f * 0.9, f * 0.84)
        else:
            vcol[i] = (f, f * 0.98, f * 0.94)
    ca = kit.materials.ensure_paint(me)
    nl = len(me.loops)
    vi = np.empty(nl, np.int64)
    me.loops.foreach_get("vertex_index", vi)
    cols = np.ones((nl, 4), np.float32)
    cols[:, :3] = vcol[vi]
    ca.data.foreach_set("color", cols.ravel())
