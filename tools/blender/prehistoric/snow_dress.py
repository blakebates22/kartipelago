# The Snow Kingdom's dressing, made over the way Dinosaur Valley's was (Blake, Oct 29:
# "Snow Kingdom overworld" next): the walls' ledges and rims brought to life (snowy pines
# on rock ledges, frosted shrubs, icicles hanging over the risers, ice spikes and crystals
# on the glacier's), and Hearthglow made a real village: cottages round a cobbled square,
# their doors on lanes trodden in the snow, smoke from every chimney, a bonfire, the
# frozen fountain, lantern posts with strings of lights between them, and the warm light
# of all of it on the snow. snow_region.py calls these (both builds: after Rimefang's
# attack the village is frozen over, the lights out, the pines turned to ice).
# SPDX-License-Identifier: MIT

import math
import random

import aurora_props as ap
import hearthglow_props as hp
import hearthglow_scenery as hs
import region_paint as paint
import region_props as rp
import region_ruin as ruin
import region_textures as TX
import snow_layout as SL
import summit_props as sp
import valley_village as vv
from pocket_build import box

RUIN = ruin.ON
L = SL.L
POCKET_LOOK = {p[0]: p[1] for p in SL.POCKETS}
# Each world's rock for the ledges under its trees.
LEDGE_ROCK = {"hearth": "frost_rock", "frostveil": "frost_rock", "summit": "summit_rock", "aurora": "rift_rock",
              "lake": "frost_rock"}
SQUARE_R = 17.0
SPOTS = []  # (x, y, r): what the village took, kept clear by the rest of the dressing  # the cobbled square's radius
LANE = ("packed_snow_road", "road")


def _pads():
    """Where cottages stand up the hollow's walls (Hearthglow climbing them, its windows
    over the square): level pads cut into the walls round the square, clear of the road,
    the ways through (north and south), the great tree and the bell tower. (x, y, z)."""
    cx, cy, cr, cz = SL.HUB
    route = [(p[0], p[1]) for p in SL.route_points()]
    gx, gy = SL.GATES["hearthglow"]
    tx, ty = SL.TREE
    pads = []
    for deg in range(0, 360, 9):
        a = math.radians(deg)
        if abs(math.cos(a)) < 0.42:
            continue
        for r in range(36, 64, 2):
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            wi = L.wall_info(x, y)
            if wi["pocket"] != "hearth" or wi["past"] > -3.0:
                continue
            h = L.natural(x, y)
            if not 5.0 < h - cz < 20.0:
                continue
            if min(math.hypot(x - px, y - py) for px, py in route) < 18.0:
                continue
            if math.hypot(x - gx, y - gy) < 24.0 or math.hypot(x - 18.0, y + 181.3) < 14.0:
                continue
            if math.hypot(x - tx, y - ty) < 20.0 or (x < cx and abs(y - cy) < 18.0):
                continue  # (the great tree; the lane west to Hearthglow's portal)
            if any(math.hypot(x - px, y - py) < 15.0 for px, py, _ in pads):
                continue
            pads.append((x, y, h))
            break
    return pads


PADS = _pads()
PAD_R = 7.5


def pad_height(x, y, h):
    """The land with the cottages' pads cut level into it."""
    for px, py, pz in PADS:
        d = math.hypot(x - px, y - py)
        if d < PAD_R + 3.0:
            t = max(0.0, min(1.0, (d - PAD_R) / 3.0))
            t = t * t * (3 - 2 * t)
            h = pz + (h - pz) * t
    return h


def level_pads(ter):
    """Lay the pads level in the built land (near a road the land is pulled toward the
    road's height, which tilted them)."""
    me = ter.data
    n = 0
    for v in me.vertices:
        for px, py, pz in PADS:
            d = math.hypot(v.co.x - px, v.co.y - py)
            if d < PAD_R + 3.0:
                v.co.z = pad_height(v.co.x, v.co.y, v.co.z)
                n += 1
                break
    me.update()
    return n


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


def wall_spots(c, seed=13, tries=34000):
    """Where things can grow on the walls: the shelves between the tiers, the shelves'
    lips over a riser (with the way out over it and the drop), and the rims' tops."""
    rnd = random.Random(seed)
    shelves, lips, rims = [], [], []
    for _ in range(tries):
        x, y = rnd.uniform(-300, 300), rnd.uniform(-300, 300)
        wi = L.wall_info(x, y)
        look = POCKET_LOOK.get(wi["pocket"], "hearth")
        if wi["past"] > 1.0:
            lw = L.look_weights(x, y)
            look = max(lw, key=lw.get)
            if wi["past"] < 20.0 and _slope(x, y) < 0.6 and paint.road_clear(c, x, y, 14.0):
                rims.append((x, y, look))
            continue
        if not 0.05 < wi["t"] < 1.0 or _slope(x, y) > 0.6 or not paint.road_clear(c, x, y, 12.0):
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
    """The walls brought to life (as the valley's, Blake's notes 2, 11-13, 42: "add
    ledges and trees to make them come alive"): snowy pines on rock ledges, frosted
    shrubs and boulders on the shelves; icicles hanging off the lips over the risers;
    pines along the rims against the sky. On the glacier, ice spikes and crystal fans.
    After the attack the pines are gone to ice: spikes of it where they stood."""
    shelves, lips, rims = wall_spots(c)
    pines = [sp.pine(c, v, 10.0 + 3.0 * v, snowy=True) for v in range(3)]
    broad = [sp.broadleaf(c, v, frosted=True) for v in range(2)]
    shrubs = [sp.shrub(c, v) for v in range(2)]
    boulders = [sp.boulder(c, v) for v in range(2)]
    spikes = [ap.ice_spike(c, v, height=7.0 + 3.0 * v) for v in range(2)]
    fans = [ap.fan(c, v, size=4.0, mat=m) for v, m in ((0, ap.CYAN), (1, ap.VIOLET))]
    icicles = [ap.icicle_fringe(c, v, width=6.0, length=2.5 + 1.5 * v) for v in range(2)]
    ledges = {lk: rp.tree_ledge(c, mat) for lk, mat in LEDGE_ROCK.items()}
    room = paint.Taken(list(taken.spots))
    k = 0

    def put(proto, x, y, rot, scale, sink=0.3, coll="Ledges"):
        c.place(proto, x, y, ground(x, y) - sink, rot=rot, scale=scale, coll=coll, role="visual")

    def put_tree(proto, x, y, rot, scale, look):
        # (A ledge of the world's rock under it, set back into the wall a little.)
        dx, dy = _toward_pocket(x, y)
        c.place(ledges.get(look, ledges["hearth"]), x - dx * 0.7, y - dy * 0.7, ground(x, y) - 0.2, rot=rot,
                coll="Ledges", role="visual")
        put(proto, x, y, rot, scale)

    for x, y, look in shelves:
        if not room.clear(x, y, 3.5):
            continue
        k += 1
        rot = (k * 2.39996) % math.tau
        if look == "aurora":
            pick = k % 4
            if pick == 0:
                put(spikes[k % 2], x, y, rot, 0.8, sink=0.5)
            elif pick == 1:
                put(fans[k % 2], x, y, rot, 1.0, sink=0.4)
            elif pick == 2:
                put(boulders[k % 2], x, y, rot, 0.9, sink=0.5)
            else:
                continue
        elif RUIN:
            pick = k % 4
            if pick in (0, 1):
                put(spikes[k % 2], x, y, rot, 0.7, sink=0.5)
            elif pick == 2:
                put(boulders[k % 2], x, y, rot, 1.0, sink=0.5)
            else:
                continue
        else:
            pick = k % 6
            if pick in (0, 1, 4):
                put_tree(pines[k % 3], x, y, rot, 0.55 + 0.3 * ((k * 7) % 5) / 5, look)
            elif pick == 2:
                put_tree(broad[k % 2] if look == "summit" else pines[(k + 1) % 3], x, y, rot, 0.6, look)
            elif pick == 3:
                put(shrubs[k % 2], x, y, rot, 1.0 + 0.4 * ((k * 3) % 5) / 5, sink=0.2)
            else:
                put(boulders[k % 2], x, y, rot, 0.8, sink=0.5)
        room.add(x, y, 3.5)
    n_lips = 0
    for x, y, look, (dx, dy), drop in lips:
        if not room.clear(x, y, 5.0) or drop < 4.5:
            continue
        # (The fringe runs along the lip, hanging just out over the riser.)
        rot = math.atan2(dy, dx) + math.pi / 2
        c.place(icicles[n_lips % 2], x + dx * 0.9, y + dy * 0.9, ground(x, y) - 0.15, rot=rot, coll="Vines",
                role="visual")
        n_lips += 1
        room.add(x, y, 5.0)
    n_rims = 0
    for x, y, look in rims:
        if not room.clear(x, y, 6.0):
            continue
        k += 1
        rot = (k * 1.7) % math.tau
        if look == "aurora" or RUIN:
            if k % 3:
                continue
            put(spikes[k % 2], x, y, rot, 1.2, sink=0.6, coll="Rim")
        else:
            put(pines[k % 3], x, y, rot, 0.9 + 0.35 * (k % 3) / 2, coll="Rim")
        n_rims += 1
        room.add(x, y, 6.0)
    print("snow walls: shelves %d, lips %d, rims %d" % (len(shelves), n_lips, n_rims))


# ------------------------------------------------------------------ Hearthglow


def _lane_look(x, y):
    return LANE, (TX.blend_id("snow_ground", "packed_snow_road", 50), "deep_snow")


def hearthglow(c, ground, ter, taken):
    """Hearthglow, a real village (as the valley's camp was made: Blake, Oct 28, "lets
    add more to this village"): the cobbled square and round it the cottages, facing it,
    each with its lane trodden through the snow to the square; the frozen fountain and a
    bonfire either side of the way through (the cutscenes' stage, north to south, is kept
    clear); lantern posts round the square with strings of lights slung between them;
    smoke from every chimney; and the warm light of windows and lanterns on the snow."""
    cx, cy, cr, cz = SL.HUB
    sc = hs.Scene()
    paths = []
    vv.plaza(c, cx, cy, SQUARE_R, ground, dirt=("hearth_cobble", "road"),
             edge=(TX.blend_id("packed_snow_road", "hearth_cobble", 50), "road"), verge=1.6, name="Village Square")
    # (Its floor drives as a road; the snow round it as snow.)
    c.disc("Village Square Floor", cx, cy, SQUARE_R + 0.6, cz + 0.02, c.lib("hearth_cobble", "road"), coll="Props",
           role="collision", n=40)
    # (Out of the square north to the road and south to the gorge is kept clear: the stage.)
    def in_lane(x, y, w):
        # (North to the road, south to the gorge: the stage; and west, the lane to the
        # portal.)
        return abs(x - cx) < w or (x < cx - 4.0 and abs(y - cy) < w * 0.75)

    # The fountain east, the bonfire west, either side of the way through.
    fx, fy = cx + 12.5, cy - 2.0
    hs.fountain(c, fx, fy, ground(fx, fy))
    taken.add(fx, fy, 6.5)
    SPOTS.append((fx, fy, 8.0))
    bx, by = cx - 11.0, cy + 10.5
    c.place(vv.hearth(c), bx, by, ground(bx, by) - 0.05, rot=0.7, coll="Village", role="visual")
    if not RUIN:
        g = c.game(bx, by, ground(bx, by) + 0.3)
        c.entity("campfire", x=g[0], y=g[1], z=g[2])
        sc.warm.append((bx, by, ground(bx, by) + 1.5))
    taken.add(bx, by, 5.0)
    SPOTS.append((bx, by, 6.0))
    # The folk who live here, about the bonfire.
    face = math.atan2(cy - by, cx - bx)
    g = c.game(bx - 2.0, by - 5.0, ground(bx, by))
    c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=9.0, n=3, folk="snow",
             heading=round(math.atan2(-math.cos(face), math.sin(face)), 3))
    # Lantern posts round the square, and lights slung between them (and over to the
    # fountain's crown).
    post = hp.lantern_post(c, 0)
    posts = []
    for k in range(10):
        a = k * math.tau / 10 + math.pi / 10
        x, y = cx + (SQUARE_R + 1.8) * math.cos(a), cy + (SQUARE_R + 1.8) * math.sin(a)
        if in_lane(x, y, 7.0) or not paint.road_clear(c, x, y, 3.0):
            posts.append(None)
            continue
        z = ground(x, y)
        c.place(post, x, y, z - 0.1, coll="Village", role="visual")
        posts.append((x, y, z))
        taken.add(x, y, 1.5)
        if not RUIN:
            sc.lanterns.append((x, y, z + 4.6))
            sc.warm.append((x, y, z + 4.0))
    if not RUIN:
        for a, b in zip(posts, posts[1:] + posts[:1]):
            if a and b:
                sc.lights.line((a[0], a[1], a[2] + 4.3), (b[0], b[1], b[2] + 4.3), sag=1.4, width=0.35)
        for p in posts:
            if p and math.hypot(p[0] - fx, p[1] - fy) < 12.0:
                sc.lights.line((p[0], p[1], p[2] + 4.3), (fx, fy, ground(fx, fy) + 5.0), sag=0.8, width=0.3)
    # The cottages, facing the square: round it on the hollow's floor, and up on the
    # shelves of its walls (the village climbing the hollow, their windows over it).
    built = []
    cands = []
    for r in (25.0, 30.0, 35.0):
        n = int(math.tau * r / 6.0)
        for i in range(n):
            a = i * math.tau / n
            cands.append((cx + r * math.cos(a), cy + r * math.sin(a), True))
    cands += [(x, y, False) for x, y, _ in PADS]
    k = 0
    for x, y, floor in cands:
        if len(built) >= 18:
            break
        if floor and (L.pocket_at(x, y) != "hearth" or L.wall_sd(x, y) > -5.0):
            continue
        if in_lane(x, y, 11.0) or not paint.road_clear(c, x, y, 8.0) or not taken.clear(x, y, 5.0):
            continue
        if any(math.hypot(x - hx, y - hy) < 13.0 for hx, hy, _, _ in built):
            continue
        ring = [ground(x + 5.5 * math.cos(t), y + 5.5 * math.sin(t)) for t in (0.0, 0.79, 1.57, 2.36, 3.14, 3.93, 4.71, 5.5)]
        if max(ring) - min(ring) > (2.2 if floor else 1.4):
            continue
        a = math.atan2(y - cy, x - cx)
        rot = a - math.pi / 2  # (its front, local -Y, to the square)
        z = min(ring) + 0.05
        v = (k * 3 + 1) % 5
        if RUIN:
            box(c, "House %d" % k, x, y, 4.5, 3.5, z - 1.0, z + 4.0, ("hearth_stone", "wall"), rot=rot)
            box(c, "House Ice %d" % k, x, y, 5.4, 4.4, z - 1.0, z + 6.5, ("berg_ice", "wall"), rot=rot + 0.08)
        else:
            c.place(hp.cottage(c, v), x, y, z - 0.6, rot=rot, coll="Village", role="visual")
            c.place(hp.cottage_block(c, v), x, y, z - 0.6, rot=rot, coll="Village", role="collision")
            hx, hy, hz = hp.CHIMNEY[v]
            ca, sa = math.cos(rot), math.sin(rot)
            sc.chimneys.append((x + hx * ca - hy * sa, y + hx * sa + hy * ca, z - 0.6 + hz))
            sc.warm.append((x, y, z + 3.0))
        built.append((x, y, v, floor))
        taken.add(x, y, 7.0)
        SPOTS.append((x, y, 9.0))
        k += 1
    # Each cottage's lane: from before its door to the square's edge.
    depth = (8.0, 8.0, 8.0, 9.0, 9.0)
    for x, y, v, floor in built:
        if not floor:
            continue
        a = math.atan2(y - cy, x - cx)
        d = math.hypot(x - cx, y - cy)
        door = d - depth[v] / 2 - (1.6 if not RUIN else 3.0)
        end = SQUARE_R - 0.5
        if door - end < 2.0:
            continue
        paths.append(vv.wander((cx + door * math.cos(a), cy + door * math.sin(a)),
                               (cx + end * math.cos(a), cy + end * math.sin(a)),
                               bend=1.2 * math.sin(a * 3.0), seed=int(d) % 7))
    vv.path_ribbons(c, paths, ground, look=_lane_look, width=2.6, verge=1.1, name="Village Lanes")
    # The finishing: lanterns, chimney smoke, the lights, the warm light on the snow.
    for x, y, z in sc.lanterns:
        g = c.game(x, y, z)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
    for x, y, z in sc.chimneys:
        g = c.game(x, y, z)
        c.entity("chimney", x=g[0], y=g[1], z=g[2])
    sc.lights.build(c, "Village Lights")
    if sc.warm:
        # (Only meshes of their own: a prop's mesh is shared by all its copies.)
        near = [o for o in c.coll("Village").objects if o.type == "MESH" and o.data.users == 1]
        c.glow([ter] + near, sc.warm, 16.0, (1.35, 1.12, 0.82), base=1.0,
               region=lambda w: math.hypot(w.x - cx, w.y - cy) < 80.0)
    print("hearthglow: %d cottages, %d lanes, %d lights" % (len(built), len(paths), len(sc.lanterns)))
    return paths


def gorge_bend(c, natural):
    """The far end of the Burnt Gorge, where it bends out of sight back to the valley: a
    fall of scorched rock (it was a black slab across the gorge, seen from the square)."""
    gx, gy = SL.GORGE_END
    z0 = natural(gx, gy) - 3.0
    for k, (dx, dy, rx, ry, h) in enumerate(((0.0, -10.0, 26.0, 9.0, 34.0), (-14.0, -4.0, 12.0, 8.0, 22.0),
                                              (15.0, -3.0, 13.0, 9.0, 26.0), (2.0, -18.0, 30.0, 10.0, 46.0))):
        ob = c.rock_mass("Gorge Bend %d" % k, gx + dx, gy + dy, rx, ry, z0 + h, z0=z0 - 4.0, n=14, seed=31 + k)
        c.assign(ob, c.lib("obsidian_cliff", "wall"))


# ------------------------------------------------------------------ the ice bridge


def ice_bridge(c, ground):
    """The bridge of ice over the glacier's crevasse: icicles hanging all along under its
    deck's edges, and great tusks of ice holding it up from the crevasse's walls."""
    fringe = ap.icicle_fringe(c, 1, width=6.0, length=4.0)
    spike = ap.ice_spike(c, 1, height=14.0)
    last = -1e9
    n = 0
    for q in c.S:
        if q.ground or SL.crevasse_d(q.p.x, q.p.y) > SL.CREVASSE_HW + 8.0 or q.s - last < 5.0:
            continue
        last = q.s
        rot = math.atan2(q.t.y, q.t.x)
        for sd in (-1, 1):
            x, y = q.p.x + q.r.x * sd * (q.w / 2 + 0.6), q.p.y + q.r.y * sd * (q.w / 2 + 0.6)
            c.place(fringe, x, y, q.p.z - 3.0, rot=rot, coll="Bridges", role="visual")
        n += 1
    # (Tusks of ice up out of the crevasse under each end of the deck.)
    for q in c.S[::4]:
        d = SL.crevasse_d(q.p.x, q.p.y)
        if q.ground or not SL.CREVASSE_HW - 2.0 < d < SL.CREVASSE_HW + 1.0:
            continue
        for sd in (-1, 1):
            x, y = q.p.x + q.r.x * sd * 3.0, q.p.y + q.r.y * sd * 3.0
            c.place(spike, x, y, ground(x, y) - 1.0, rot=q.s, scale=(q.p.z - 3.0 - ground(x, y)) / 14.0 + 0.1,
                    coll="Bridges", role="visual")
    print("ice bridge: %d fringes" % n)
