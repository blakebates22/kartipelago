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
import hearthglow_props as hp
import keep_props as kp
import region_paint as paint
import snow_layout as SL
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
    """Cottages along both sides of the road through Hearthglow, set back from it facing
    it, lantern posts between, presents by the road (a boost when burst), candy canes
    and baubles. `seat(v, x, y, rot, name)`: sets a cottage level and solid, returns its
    chimney or None."""
    rng = random.Random(41)
    post = hp.lantern_post(c, 0)
    cane = hp.candy_cane(c, 5.0)
    houses = 0
    for k, (s, q) in enumerate(_stretches(c, "hearth", 11.0)):
        for side in (-1, 1):
          for v in rng.sample(range(5), 3):
            w, d = hp.COTTAGE_SIZE[v]
            off = q.w / 2 + 3.0 + d / 2 + rng.uniform(0.0, 2.0)
            x, y = q.p.x + q.r.x * side * off, q.p.y + q.r.y * side * off
            if not taken.clear(x, y, max(w, d) / 2 + 1.0) or not paint.road_clear(c, x, y, d / 2 + 1.5):
                continue
            if not _off_side_roads(c, x, y, max(w, d) / 2 + 2.0):
                continue
            if L.wall_sd(x, y) > -3.0:
                continue
            # (Its front, local -Y, to the road.)
            rot = math.atan2(-q.r.y * side, -q.r.x * side) + math.pi / 2
            smoke = seat(v, x, y, rot, "Street Cottage %d" % houses)
            if smoke is None:
                continue
            taken.add(x, y, max(w, d) / 2 + 1.0)
            g = c.game(*smoke)
            c.entity("chimney", x=g[0], y=g[1], z=g[2])
            houses += 1
            break
        # A lantern post at the road's edge between houses, sides alternating.
        side = 1 if k % 2 else -1
        x, y = q.p.x + q.r.x * side * (q.w / 2 + 1.6), q.p.y + q.r.y * side * (q.w / 2 + 1.6)
        if taken.clear(x, y, 1.0) and paint.road_clear(c, x, y, 0.8) and _off_side_roads(c, x, y, 1.0):
            z = ground(x, y)
            c.place(post, x, y, z - 0.1, coll="Props", role="visual")
            c.place(paint.trunk_proto(c, 0.3, 5.0), x, y, z, coll="Collision", role="collision")
            g = c.game(x, y, z + 4.6)
            c.entity("lantern", x=g[0], y=g[1], z=g[2])
            taken.add(x, y, 1.2)
        elif k % 3 == 1:
            x, y = q.p.x + q.r.x * -side * (q.w / 2 + 1.8), q.p.y + q.r.y * -side * (q.w / 2 + 1.8)
            if taken.clear(x, y, 1.0) and paint.road_clear(c, x, y, 0.8):
                c.place(cane, x, y, ground(x, y) - 0.1, rot=rng.uniform(0, 6.28), coll="Props")
                taken.add(x, y, 1.0)
    # Presents by the road, three, on its shoulder: burst one for a small boost.
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
    # Baubles turning over the square's edge.
    vx, vy, vr, vz = SL.VILLAGE
    for k, col in enumerate(("#d82a3a", "#2a8a4a", "#e8b64a", "#3a6ad8")):
        a = k * math.tau / 4 + 0.4
        x, y = vx + (vr + 6.0) * math.cos(a), vy + (vr + 6.0) * math.sin(a)
        g = c.game(x, y, ground(x, y) + 7.0)
        c.entity("ornament", x=g[0], y=g[1], z=g[2], r=1.4, color=col)
    print("hearthglow streets: %d cottages, %d presents" % (houses, n))


# ------------------------------------------------------------------ Frostveil


def frostveil(c, ground, taken, keep_clear):
    """The road through Frostveil walled in: curtain walls along both shoulders, a tower
    at every fourth length, braziers on the walls' feet, banners hung on them, arches
    over the road every so often. `keep_clear`: (x, y, r) circles the walls stay out of
    (the gateways' spurs, the secret yard)."""
    wall = kp.curtain_wall(c, length=10.4, h=10.0, thick=3.0)
    tower = kp.round_tower(c, r=3.8, h=17.0, variant=0)
    brazier = kp.brazier(c)
    banner = kp.wall_banner(c)
    arch = kp.gate_arch(c, span=c.width + 10.0, clear=10.0, depth=5.0)
    st = _stretches(c, "frostveil", 10.0)
    walls = towers = arches = 0
    last_arch = -999.0
    for k, (s, q) in enumerate(st):
        rot = math.atan2(q.t.y, q.t.x)
        for side in (-1, 1):
            off = q.w / 2 + 3.2
            x, y = q.p.x + q.r.x * side * off, q.p.y + q.r.y * side * off
            if any(math.hypot(x - cx, y - cy) < cr for cx, cy, cr in keep_clear):
                continue
            if not _off_side_roads(c, x, y, 4.0) or not paint.road_clear(c, x, y, 1.2):
                continue
            z = min(ground(x, y), q.p.z)
            c.place(wall, x, y, z - 0.6, rot=rot + (0.0 if side < 0 else math.pi), coll="Village")
            taken.add(x, y, 5.5)
            walls += 1
            if k % 4 == 0:
                tx, ty = q.p.x + q.r.x * side * (off + 2.5), q.p.y + q.r.y * side * (off + 2.5)
                c.place(tower, tx, ty, min(ground(tx, ty), q.p.z) - 2.0, rot=rot, coll="Village")
                taken.add(tx, ty, 5.0)
                towers += 1
            elif k % 4 == 2:
                bx, by = q.p.x + q.r.x * side * (q.w / 2 + 1.2), q.p.y + q.r.y * side * (q.w / 2 + 1.2)
                if paint.road_clear(c, bx, by, 0.4):
                    c.place(brazier, bx, by, ground(bx, by) - 0.1, rot=rot, coll="Fire")
                    g = c.game(bx, by, ground(bx, by) + 2.8)
                    c.entity("torch", x=g[0], y=g[1], z=g[2])
                wx, wy = q.p.x + q.r.x * side * (off - 1.55), q.p.y + q.r.y * side * (off - 1.55)
                c.place(banner, wx, wy, z + 3.0, rot=rot + (math.pi if side < 0 else 0.0), coll="Props", role="visual")
        if s - last_arch > 70.0 and 0 < k < len(st) - 1 and _off_side_roads(c, q.p.x, q.p.y, 14.0):
            c.place(arch, q.p.x, q.p.y, q.p.z - 0.3, rot=rot - math.pi / 2, coll="Props", role="visual")
            last_arch = s
            arches += 1
    print("frostveil streets: %d walls, %d towers, %d arches" % (walls, towers, arches))


# ------------------------------------------------------------------ Snowy Summit


def summit(c, ground, taken):
    """The deep thaw: geysers in their cones (blowing, away from the road), steaming
    terrace pools, ice ponds half melted, steam from vents, green pines (the region's
    scatter), and the mammoth herd on its round in the meadow."""
    rng = random.Random(53)
    cones = [sp.geyser_cone(c, v) for v in range(3)]
    pools = [sp.terrace_pools(c, v) for v in range(2)]
    pockets = [p for p in SL.POCKETS if p[0] in ("summit", "climb")]
    circles = [ci for p in pockets for ci in p[2]]
    lx, ly, lr, lz = SL.LAKE
    geysers = ponds = 0

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

    for k in range(7):
        p = spot(7.0, 9.0)
        if not p:
            continue
        x, y, z = p
        v = k % 3
        c.place(cones[v], x, y, z - 0.3, rot=rng.uniform(0, 6.28), coll="Props")
        taken.add(x, y, 7.0)
        g = c.game(x, y, z + 2.4 + 0.6 * v)
        c.entity("geyser", x=g[0], y=g[1], z=g[2], r=3.5, height=16.0 + 5.0 * (k % 3), period=8.0 + (k % 3), offset=1.3 * k,
                 warn=1.4, blast=2.2, launch=0.0)
        geysers += 1
        for j in range(2):
            a = rng.uniform(0, math.tau)
            vx, vy = x + 9.0 * math.cos(a), y + 9.0 * math.sin(a)
            if paint.road_clear(c, vx, vy, 3.0):
                g = c.game(vx, vy, ground(vx, vy) + 0.2)
                c.entity("steam", x=g[0], y=g[1], z=g[2])
    for k in range(4):
        p = spot(6.0, 7.0)
        if not p:
            continue
        x, y, z = p
        c.place(pools[k % 2], x, y, z - 0.5, rot=rng.uniform(0, 6.28), coll="Props", role="visual")
        taken.add(x, y, 6.0)
        g = c.game(x, y, z + 0.6)
        c.entity("steam", x=g[0], y=g[1], z=g[2])
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
    # The mammoths' round: a loop through the meadow, on the ground, off the road.
    pts = []
    mx, my = -60.0, 186.0
    for k in range(18):
        a = k * math.tau / 18
        x, y = mx + 30.0 * math.cos(a) + 5.0 * math.sin(3 * a), my + 14.0 * math.sin(a)
        pts.append((x, y, ground(x, y)))
    c.path_curve("Mammoth Path", pts, closed=True)
    for k, (scale, start) in enumerate(((1.0, 0.0), (0.6, 12.0), (0.95, 70.0), (0.55, 82.0))):
        c.entity("dinosaur", route="Mammoth Path", speed=1.5, scale=scale, model="mammoth", start=start)
    print("snowy summit: %d geysers, %d ponds, 4 mammoths" % (geysers, ponds))


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
            ox = q.w / 2 + 6.0
            x, y = q.p.x + q.r.x * -side * ox, q.p.y + q.r.y * -side * ox
            if taken.clear(x, y, 3.0) and paint.road_clear(c, x, y, 3.0):
                proto = amber if k % 6 == 0 else fans[k % 3]
                c.place(proto, x, y, ground(x, y) - 0.3, rot=math.atan2(q.t.y, q.t.x) + k, coll="Props", role="visual")
                taken.add(x, y, 3.0)
    c.entity("area_ambient", area="aurora", effect="sparkles", rate=14, radius=34, colors=["#9ef3ff", "#c9a2ff", "#ffffff"])
    print("aurora: %d lantern posts" % n)
