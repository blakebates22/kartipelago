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
import gulch_scenery as gs
import props
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
    cx, cy, cr, cz = SL.VILLAGE
    route = [(p[0], p[1]) for p in SL.route_points()]
    gx, gy = SL.GATES["hearthglow"]
    tx, ty = SL.TREE
    bx, by = SL.BELL
    pads = []
    for deg in range(0, 360, 6):
        a = math.radians(deg)
        if math.cos(a) < -0.3:
            continue  # (not the west, where the road runs by)
        for r in range(20, 56, 2):
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            wi = L.wall_info(x, y)
            if wi["pocket"] != "lake" or wi["past"] > -3.0:
                continue
            h = L.natural(x, y)
            if not 3.5 < h - cz < 24.0:
                continue
            if min(math.hypot(x - px, y - py) for px, py in route) < 18.0:
                continue
            if math.hypot(x - gx, y - gy) < 24.0 or math.hypot(x - bx, y - by) < 14.0:
                continue
            if math.hypot(x - tx, y - ty) < 20.0 or (x > cx and abs(y - cy) < 18.0):
                continue  # (the great tree; the lane east to Hearthglow's portal)
            if any(math.hypot(x - px, y - py) < 13.0 for px, py, _ in pads):
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

    import bpy

    land = bpy.data.objects.get("Snow Kingdom")

    def put_tree(proto, x, y, rot, scale, look):
        # (A ledge of the rock of the wall it stands out of, set back into it a little:
        # Blake, review-snow_region note 4.)
        dx, dy = _toward_pocket(x, y)
        tex = paint.wall_texture(land, x, y, dx, dy) if land else None
        ledge = rp.tree_ledge(c, tex) if tex else ledges.get(look, ledges["hearth"])
        c.place(ledge, x - dx * 0.7, y - dy * 0.7, ground(x, y) - 0.2, rot=rot, coll="Ledges", role="visual")
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
        # (Icicles only over icy rock: not on the brown and black walls, where they looked
        # wrong: Blake, review-snow_region note 8.)
        tex = paint.wall_texture(land, x + dx * 3.0, y + dy * 3.0, -dx, -dy, steps=(0.5, 1.5)) if land else None
        if tex and not any(k_ in tex for k_ in ("frost", "ice", "glacier", "snow", "berg")):
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


def footing(x, y, rot, w, d, ground, margin=0.6):
    """The ground under a building's footprint (w by d, turned `rot`; corners, edge middles
    and middle, `margin` out) and a step before its door (local -Y): (lowest, highest)."""
    ca, sa = math.cos(rot), math.sin(rot)
    hs = []
    for fx, fy in [(i, j) for i in (-0.5, 0.0, 0.5) for j in (-0.5, 0.0, 0.5)] + [(0.0, -0.5 - 1.4 / d)]:
        lx, ly = fx * (w + margin), fy * (d + margin)
        hs.append(ground(x + lx * ca - ly * sa, y + lx * sa + ly * ca))
    return min(hs), max(hs)


LEVEL = 0.6  # the most a cottage's ground may fall across it (its base course goes 0.7 m down)


def level_site(c, x, y, rot, w, d, ground, ter, most=3.0):
    """The ground a building of w by d goes on at (x, y), made level (the overworld rules,
    Blake, Oct 29: on level ground, never set into a slope): if it falls more than LEVEL
    across, the land's cut and filled level under it (up to `most`). The height to seat it
    at, or None if it's too steep to build there."""
    lo, hi = footing(x, y, rot, w, d, ground)
    if hi - lo <= LEVEL:
        return hi
    if ter is None or hi - lo > most:
        return None
    paint.grade(c, ter, x, y, rot, w, d, (lo + hi) / 2)
    lo, hi = footing(x, y, rot, w, d, ground)
    return hi if hi - lo <= LEVEL else None


def seat_cottage(c, v, x, y, rot, ground, name=None, coll="Village", ter=None):
    """A cottage set level on its footing (the overworld rules, Blake, Oct 29: on level
    ground; its door sill at the highest ground, its stone base course down past the
    lowest; nothing in the hill, nothing floating), and solid. Returns where its chimney
    smokes from, or None if it can't be built there."""
    w, d = hp.COTTAGE_SIZE[v % 5]
    hi = level_site(c, x, y, rot, w, d, ground, ter)
    if hi is None:
        return None
    z = hi - 0.5
    # (Its stone footing on down to the lowest ground under it, so no corner of it ever
    # hangs in the air: tests/buildings.test.ts.)
    lo, _hi = footing(x, y, rot, w, d, ground, margin=1.2)
    box(c, "%s Footing" % (name or "Cottage"), x, y, w / 2 + 0.2, d / 2 + 0.2, min(lo, z) - 1.6, z + 0.1,
        ("hearth_stone", "wall"), rot=rot, role="visual")
    c.place(hp.cottage(c, v), x, y, z, rot=rot, coll=coll, role="visual", name=name)
    c.place(hp.cottage_block(c, v), x, y, z, rot=rot, coll=coll, role="collision")
    hx, hy, hz = hp.CHIMNEY[v % 5]
    ca, sa = math.cos(rot), math.sin(rot)
    return (x + hx * ca - hy * sa, y + hx * sa + hy * ca, z + hz)


def railing(c, px, py, toward, R, z, ground, span=1.25):
    """Timber railing on an arc `R` round (px, py), facing `toward` (+-span), at height z:
    along a terrace's edge over the drop below it. Only where the ground's level with it
    (none buried in a bank or standing out over the drop)."""
    rail = hp.pad_rail(c)
    n = 0
    a = toward - span
    da = 1.8 / R
    while a < toward + span:
        x, y = px + R * math.cos(a), py + R * math.sin(a)
        x2, y2 = px + R * math.cos(a + da), py + R * math.sin(a + da)
        if abs(ground(x, y) - z) < 0.4 and abs(ground(x2, y2) - z) < 0.4:
            c.place(rail, x, y, z - 0.05, rot=a + math.pi / 2, coll="Village", role="both")
            n += 1
        a += da
    return n


def hearthglow(c, ground, ter, taken):
    """Hearthglow, a real village (as the valley's camp was made: Blake, Oct 28, "lets
    add more to this village"): the cobbled square and round it the cottages, facing it,
    each with its lane trodden through the snow to the square; the frozen fountain and a
    bonfire either side of the way through (the cutscenes' stage, north to south, is kept
    clear); lantern posts round the square with strings of lights slung between them;
    smoke from every chimney; and the warm light of windows and lanterns on the snow."""
    cx, cy, cr, cz = SL.VILLAGE
    import villager_homes as vh

    # (Clear of what was built before the village: the Gatehouse's towers stood through a
    # cottage once. Taken before the square's own floor is laid.)
    standing = vh._built()
    sc = hs.Scene()
    paths = []
    vv.plaza(c, cx, cy, SQUARE_R, ground, dirt=("hearth_cobble", "road"),
             edge=(TX.blend_id("packed_snow_road", "hearth_cobble", 50), "road"), verge=1.6, name="Village Square")
    # (Its floor drives as a road; the snow round it as snow.)
    c.disc("Village Square Floor", cx, cy, SQUARE_R + 0.6, cz + 0.02, c.lib("hearth_cobble", "road"), coll="Props",
           role="collision", n=40)
    # (Out of the square west to the road and east to the portal is kept clear: the way
    # through, and the cutscenes' stage.)
    def in_lane(x, y, w):
        return abs(y - cy) < w * 0.75

    # The fountain north, the bonfire south, either side of the way through.
    fx, fy = cx - 2.0, cy + 10.5
    warm_fountain(c, fx, fy, ground(fx, fy))
    taken.add(fx, fy, 6.5)
    SPOTS.append((fx, fy, 8.0))
    bx, by = cx + 3.0, cy - 10.5
    # (Set down as the valley's are: solid, logs in the fire and log benches round it.)
    vv.place_hearth(c, bx, by, ground, rot=0.7)
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
        c.place(paint.trunk_proto(c, 0.3, 5.0), x, y, z, coll="Collision", role="collision")
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
    # (The whole basin and the lake's shore by it, both sides of the road, nearest the
    # square first: a village street, not a ring.)
    for gx_ in range(-60, 61, 5):
        for gy_ in range(-60, 61, 5):
            if 21.0 < math.hypot(gx_, gy_) < 62.0:
                cands.append((cx + gx_, cy + gy_, True))
    cands.sort(key=lambda p: math.hypot(p[0] - cx, p[1] - cy))
    cands += [(x, y, False) for x, y, _ in PADS]
    k = 0
    why = {}
    for x, y, floor in cands:
        if len(built) >= 18:
            break
        if any(math.hypot(x - ox, y - oy) < orr + 6.0 for ox, oy, orr in standing):
            why["built"] = why.get("built", 0) + 1
            continue
        if floor and (L.pocket_at(x, y) != "lake" or L.wall_sd(x, y) > -5.0
                      or math.hypot(x - SL.LAKE[0], y - SL.LAKE[1]) < SL.LAKE[2] + 7.0):
            why["pocket"] = why.get("pocket", 0) + 1
            continue
        r_ = "lane" if in_lane(x, y, 8.0) else "road" if not paint.road_clear(c, x, y, 8.0) else (
            "taken" if not taken.clear(x, y, 5.0) else None)
        if r_:
            why[r_] = why.get(r_, 0) + 1
            continue
        if any(math.hypot(x - hx, y - hy) < 12.0 for hx, hy, _, _ in built):
            continue
        a = math.atan2(y - cy, x - cx)
        rot = a - math.pi / 2  # (its front, local -Y, to the square)
        v = (k * 3 + 1) % 5
        if not floor and v in (0, 3):
            v = (1, 2)[k % 2]  # (on a pad: one that fits on it)
        w, d = hp.COTTAGE_SIZE[v]
        hi = level_site(c, x, y, rot, w, d, ground, ter, most=4.5)
        if hi is None:
            why["level"] = why.get("level", 0) + 1
            continue  # (only on level ground: Blake, Oct 29)
        if RUIN:
            z = hi - 0.5
            box(c, "House %d" % k, x, y, w / 2 - 0.5, d / 2 - 0.5, z - 0.8, z + 4.5, ("hearth_stone", "wall"), rot=rot)
            box(c, "House Ice %d" % k, x, y, w / 2 + 0.4, d / 2 + 0.4, z - 0.8, z + 7.0, ("berg_ice", "wall"), rot=rot + 0.08)
        else:
            smoke = seat_cottage(c, v, x, y, rot, ground, ter=ter)
            sc.chimneys.append(smoke)
            sc.warm.append((x, y, hi + 2.5))
        # (A terrace over a drop: a railing along its edge, before the door.)
        fx, fy = x - math.cos(a) * (d / 2 + 6.0), y - math.sin(a) * (d / 2 + 6.0)
        if not floor:
            railing(c, x, y, a + math.pi, PAD_R - 1.5, hi, ground)
        elif ground(fx, fy) < hi - 1.5:
            railing(c, x, y, a + math.pi, d / 2 + 2.6, hi, ground, span=0.6)
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
        # (Never over the road, nor up to it: the overworld rules. A cottage across the road
        # from the square has its doorstep, not a lane.)
        steps = int((door - end) / 1.5) + 1
        if any(not paint.road_clear(c, cx + (end + (door - end) * t / steps) * math.cos(a),
                                    cy + (end + (door - end) * t / steps) * math.sin(a), 3.5) for t in range(steps + 1)):
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


# ------------------------------------------------------------------ Hearthglow, moved


def warm_fountain(c, x, y, z):
    """The square's fountain (Blake, review-snow_region note 6: "this water fountain looks
    horrible. please lets get a high fidelity water fountain"): a hot spring's, steaming
    in the cold: a carved octagonal basin of the village's stone, a column rising out of
    it with two bowls, water spilling over each bowl's lip in a sheet into the one below
    and into the basin, living water in all three, a lantern's gold finial on top, steam
    curling off it. Solid (the basin)."""
    from props import loft, ring, tube

    m = gs.Mesh()
    stone = ("hearth_stone", "wall")
    trim = ("gold_trim", "wall")
    n = 8

    def oct_ring(bm, r, h):
        return ring(bm, (x, y), r, h, n, phase=math.pi / 8)

    # The basin: its wall, its rim, a step round its foot.
    m.add(stone, lambda bm: loft(bm, [oct_ring(bm, 5.0, z - 0.4), oct_ring(bm, 5.0, z + 0.2), oct_ring(bm, 4.5, z + 0.2),
                                      oct_ring(bm, 4.5, z + 0.25)], cap_top=True))
    m.add(stone, lambda bm: loft(bm, [oct_ring(bm, 4.3, z + 0.2), oct_ring(bm, 4.3, z + 1.0), oct_ring(bm, 4.55, z + 1.05),
                                      oct_ring(bm, 4.55, z + 1.25), oct_ring(bm, 3.9, z + 1.25), oct_ring(bm, 3.9, z + 0.4)],
                                  cap_top=False))
    # The column and its two bowls.
    m.add(stone, lambda bm: tube(bm, [(x, y, z + 0.4), (x, y, z + 2.2)], [0.75, 0.55], n=8))
    m.add(stone, lambda bm: loft(bm, [ring(bm, (x, y), 0.55, z + 2.0, 16), ring(bm, (x, y), 2.1, z + 2.45, 16),
                                      ring(bm, (x, y), 2.3, z + 2.65, 16), ring(bm, (x, y), 2.05, z + 2.65, 16),
                                      ring(bm, (x, y), 1.9, z + 2.5, 16)], cap_top=True))
    m.add(stone, lambda bm: tube(bm, [(x, y, z + 2.6), (x, y, z + 3.7)], [0.42, 0.32], n=8))
    m.add(stone, lambda bm: loft(bm, [ring(bm, (x, y), 0.3, z + 3.55, 14), ring(bm, (x, y), 1.1, z + 3.85, 14),
                                      ring(bm, (x, y), 1.22, z + 4.0, 14), ring(bm, (x, y), 1.05, z + 4.0, 14),
                                      ring(bm, (x, y), 0.95, z + 3.9, 14)], cap_top=True))
    m.add(trim, lambda bm: tube(bm, [(x, y, z + 3.9), (x, y, z + 4.6), (x, y, z + 4.75)], [0.18, 0.12, 0.02], n=6))
    # The water falling over each bowl's lip, a sheet all round.
    veil = ("falls_veil", "water")
    m.add(veil, lambda bm: loft(bm, [ring(bm, (x, y), 1.24, z + 3.98, 16), ring(bm, (x, y), 1.4, z + 3.4, 16),
                                     ring(bm, (x, y), 1.6, z + 2.7, 16)], cap_top=False))
    m.add(veil, lambda bm: loft(bm, [ring(bm, (x, y), 2.32, z + 2.62, 20), ring(bm, (x, y), 2.6, z + 1.9, 20),
                                     ring(bm, (x, y), 2.95, z + 1.0, 20)], cap_top=False))
    m.build(c, "Warm Fountain", coll="Village", role="visual")
    water = c.lib("valley_river", "water")
    c.disc("Warm Fountain Pool", x, y, 4.0, z + 0.95, water, coll="Village", role="visual", n=16)
    c.disc("Warm Fountain Bowl", x, y, 1.95, z + 2.55, water, coll="Village", role="visual", n=16)
    c.disc("Warm Fountain Cup", x, y, 1.0, z + 3.92, water, coll="Village", role="visual", n=12)
    c.place(paint.trunk_proto(c, 5.2, 1.4), x, y, z, coll="Collision", role="collision")
    for dz, rate in ((1.0, 4), (4.0, 3)):
        g = c.game(x, y, z + dz)
        c.entity("steam", x=g[0], y=g[1], z=g[2])


def market(c, ground, cx, cy, cr, cz):
    """Hearthglow's Christmas market, redone (Blake, review-snow_region notes 1 and 5): a
    crescent of stalls round the square's north edge, off the way through and out of
    the lanes, each facing in, a lantern between each two and a string of lights over
    the lot."""
    sc = hs.Scene()
    posts = []
    R = cr + 3.5
    for k, deg in enumerate((58.0, 76.0, 94.0, 112.0, 130.0)):
        a = math.radians(deg)
        x, y = cx + R * math.cos(a), cy + R * math.sin(a)
        if not paint.road_clear(c, x, y, 4.0):
            continue
        rot = a - math.pi / 2  # (its front, local -Y, to the square)
        z = min(ground(x + dx, y + dy) for dx in (-2.5, 0.0, 2.5) for dy in (-1.5, 0.0, 1.5))
        c.place(hp.stall(c, k % 2), x, y, z - 0.05, rot=rot, coll="Village")
        SPOTS.append((x, y, 4.0))
        a2 = math.radians(deg + 9.0)
        px, py = cx + (R + 1.0) * math.cos(a2), cy + (R + 1.0) * math.sin(a2)
        if k < 4:
            pz = ground(px, py)
            c.place(hp.lantern_post(c, 0), px, py, pz - 0.1, coll="Village", role="visual")
            c.place(paint.trunk_proto(c, 0.3, 5.0), px, py, pz, coll="Collision", role="collision")
            g = c.game(px, py, pz + 4.6)
            c.entity("lantern", x=g[0], y=g[1], z=g[2])
            posts.append((px, py, pz))
    for a, b in zip(posts, posts[1:]):
        sc.lights.line((a[0], a[1], a[2] + 4.3), (b[0], b[1], b[2] + 4.3), sag=1.2, width=0.35)
    sc.lights.build(c, "Market Lights")
    print("market: %d stalls" % len(posts))


def entry_pass(c, ground, way):
    """The hollow the village left: the grand way in to the Snow Kingdom (Blake, Oct 29,
    review-snow_region notes 7 and 11, "we need to massively overhaul the area when we
    first enter the snow world"; he chose the grand entry pass): up out of the Burnt Gorge
    you come through a great stone gateway, banners hung either side of it and lanterns
    burning on it, the hollow's walls hung with frozen falls, a lookout hut on a ledge
    over the way, and lantern posts lighting the road on to the kingdom. `way`: the road's
    points, from the kingdom's road down to the gorge."""
    import keep_props as kp

    if len(way) < 4:
        return
    # The gateway, across the road where it comes up out of the gorge into the hollow.
    cx, cy, cr, cz = SL.HUB
    best = min(way, key=lambda p: abs(p[1] - (cy - cr + 4.0)))
    k = way.index(best)
    ax, ay = way[max(0, k - 1)]
    bx, by = way[min(len(way) - 1, k + 1)]
    rot = math.atan2(by - ay, bx - ax)
    gz = ground(*best)
    kp.use_palette({"keep_ashlar": "citadel_stone", "keep_ashlar_dark": "citadel_dark", "keep_parapet": "citadel_stone",
                    "keep_gold": "temple_gold", "keep_banner": "banner_teal", "keep_pine": "pine_snow"})
    arch = kp.gate_arch(c, span=22.0, clear=12.0, depth=6.0)
    c.place(arch, best[0], best[1], gz - 0.3, rot=rot - math.pi / 2, coll="Props", role="visual")
    nx, ny = -math.sin(rot), math.cos(rot)
    for sd in (-1, 1):
        px, py = best[0] + nx * sd * 13.5, best[1] + ny * sd * 13.5
        tower = kp.round_tower(c, r=3.6, h=18.0)
        zt = min(ground(px + 3.6 * math.cos(t), py + 3.6 * math.sin(t)) for t in (0.0, 1.57, 3.14, 4.71))
        c.place(tower, px, py, zt - 0.5, rot=rot)
        g = c.game(best[0] + nx * sd * 9.5, best[1] + ny * sd * 9.5, gz + 9.0)
        c.entity("torch", x=g[0], y=g[1], z=g[2])
        bpx, bpy = best[0] + nx * sd * 17.5 + math.cos(rot) * 3.0, best[1] + ny * sd * 17.5 + math.sin(rot) * 3.0
        c.place(kp.banner_pole(c), bpx, bpy, ground(bpx, bpy) - 0.2, rot=rot, coll="Props")
    # Lantern posts up the road from the gateway to the kingdom's road.
    post = hp.lantern_post(c, 0)
    for j in range(0, k, 2):
        (x0, y0), (x1, y1) = way[j], way[min(j + 1, len(way) - 1)]
        tx, ty = x1 - x0, y1 - y0
        tl = math.hypot(tx, ty) or 1.0
        for sd in (-1, 1):
            px, py = x0 - ty / tl * sd * 8.5, y0 + tx / tl * sd * 8.5
            if not paint.road_clear(c, px, py, 3.0):
                continue
            pz = ground(px, py)
            c.place(post, px, py, pz - 0.1, coll="Props", role="visual")
            c.place(paint.trunk_proto(c, 0.3, 5.0), px, py, pz, coll="Collision", role="collision")
            g = c.game(px, py, pz + 4.6)
            c.entity("lantern", x=g[0], y=g[1], z=g[2])
    # Frozen falls down the hollow's walls, either side, facing the way in.
    n = 0
    for deg in (40.0, 140.0, 200.0, 340.0):
        a = math.radians(deg)
        for r in range(int(cr) + 14, int(cr) + 60, 2):
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            if L.wall_info(x, y)["past"] > -2.0:
                top = L.natural(x, y)
                foot = ground(cx + (r - 14) * math.cos(a), cy + (r - 14) * math.sin(a))
                if top - foot < 10.0:
                    break
                props.falls(c, "Frozen Falls %d" % n, x, y, top, foot, 5.0, 8.0, facing=-1, throw=2.0, bulge=0.8, veils=2,
                            foam=False, angle=a + math.pi / 2, mats=("icefall_blue", "glacier_ice", "glacier_ice"))
                n += 1
                break
    print("entry pass: the gateway, %d frozen falls" % n)

