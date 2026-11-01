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
import yule_props as yp
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
        # (None up Frostveil's walls: its towers and spires against the rock, not trees,
        # Blake, review-snow_region 8 note 14.)
        if look == "frostveil":
            return
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
        # (None anywhere now: Blake, review-snow_region 7 and 8, "remove these weird icicles
        # and any others in the area", time after time.)
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


XMAS_TREE = (-110.4, -146.2)  # (review-snow_region 9 note 14: where the old lane left the street)
EXTRA_HOME = (-117.0, -114.0)  # (note 16: "SOMETHING NEEds to go here ... another house")
# review-snow_region 11 (Nov 1), Blake's pins (blender x, y):
NO_STALL = (-54.2, -164.1)  # note 1: "lets just remove this stall. and put a small christmas tree here."
SMALL_TREES = [(-54.2, -164.1), (-134.3, -128.8)]  # notes 1, 2
GRAND_SNOWMAN = (-66.2, -135.2)  # note 5: "a high fidelity snowman here facing the road"
LITTLE_SNOWMEN = (-88.2, -101.6)  # note 8: "like 3 little snow men here"
BEND_MARKET = (-82.2, -80.9)  # note 6: "this bend feels empty ... a couple of marktets and candy canes"


def hearthglow(c, ground, ter, taken):
    """Hearthglow, a street village (Blake, review-snow_region 7: the square, its fountain
    and bonfire gone; "houses lining the other side of this road. it needs to be done
    methodically"): small cottages in a row along both sides of the road through the
    basin, all set back the same, each facing the road, spaced evenly; a lantern post
    every so often on both sides, opposite each other, Christmas lights strung along each
    side and across the road between them; candy canes between the posts; the Christmas
    market's stalls along the road's south-east stretch (note 5), the folk about them;
    the warm light of the windows and lanterns on the snow. Returns its lanes (none now)."""
    cx, cy, cr, cz = SL.VILLAGE
    import villager_homes as vh

    standing = vh._built()
    sc = hs.Scene()
    post = hp.lantern_post(c, 0)
    cane = hp.candy_cane(c, 5.0)
    # The road through the basin, as it goes (only where it's Hearthglow's, inside the
    # basin's walls).
    S0, S1 = 40.0, 250.0
    # The market: the road's south-east stretch, its north side (note 5's spot).
    MARKET = (80.0, 124.0, 1)
    SMALL = (2, 1, 4, 2, 4, 1)  # (the cottages in turn: the small ones, hp.COTTAGE_SIZE)
    SET = 4.0  # (each front yard: the road's edge to the cottage's front)
    GAP = 3.5  # (between neighbours)

    def side_of(q, sd, off):
        return q.p.x + q.r.x * sd * off, q.p.y + q.r.y * sd * off

    def inside(x, y):
        return L.wall_sd(x, y) < -4.0 and L.look_at(x, y) == "hearth"

    def clear(x, y, r):
        return (taken.clear(x, y, r) and paint.road_clear(c, x, y, r)
                and all(math.hypot(x - ox, y - oy) > orr + r for ox, oy, orr in standing))

    built = []
    why = {}

    def no(r):
        why[r] = why.get(r, 0) + 1

    for sd in (-1, 1):
        s = S0
        k = 0
        while s < S1:
            q = c.at(s)
            if MARKET[0] <= s <= MARKET[1] and sd == MARKET[2]:
                s += 2.0
                continue
            v = SMALL[k % len(SMALL)]
            w, d = hp.COTTAGE_SIZE[v]
            room = max(w, d) / 2 + 0.8
            x, y = side_of(q, sd, q.w / 2 + SET + d / 2)
            rot = math.atan2(-q.r.y * sd, -q.r.x * sd) + math.pi / 2  # (its front, local -Y, to the road)
            if not inside(x, y):
                no("outside" if L.look_at(x, y) == "hearth" else "look:" + L.look_at(x, y))
                s += 2.0
                continue
            if not taken.clear(x, y, room):
                no("taken")
                s += 2.0
                continue
            if not paint.road_clear(c, x, y, room):
                no("road")
                s += 2.0
                continue
            if not clear(x, y, room):
                no("standing")
                s += 2.0
                continue
            if RUIN:
                hi = level_site(c, x, y, rot, w, d, ground, ter)
                if hi is None:
                    s += 2.0
                    continue
                z = hi - 0.5
                box(c, "Street House %d" % len(built), x, y, w / 2 - 0.5, d / 2 - 0.5, z - 0.8, z + 4.5, ("hearth_stone", "wall"),
                    rot=rot)
                box(c, "Street House Ice %d" % len(built), x, y, w / 2 + 0.4, d / 2 + 0.4, z - 0.8, z + 7.0, ("berg_ice", "wall"),
                    rot=rot + 0.08)
            else:
                smoke = seat_cottage(c, v, x, y, rot, ground, name="Street Cottage %d" % len(built), ter=ter)
                if smoke is None:
                    no("level")
                    s += 2.0
                    continue
                sc.chimneys.append(smoke)
                sc.warm.append((x, y, ground(x, y) + 2.5))
            taken.add(x, y, room)
            SPOTS.append((x, y, room + 0.2))
            built.append((x, y))
            k += 1
            s += w + GAP
    # Then the rest of the street's frontage (where the road bends, the walk along it skips
    # over room on its inside): every spot a cottage fits facing the road, its front the
    # same few metres back from the road's edge, nearest the road first.
    k = 0
    cands = []
    for gx_ in range(-75, 76, 3):
        for gy_ in range(-75, 76, 3):
            x, y = cx + gx_, cy + gy_
            q, _ = c.nearest(x, y)
            if not (S0 <= q.s <= S1) or not inside(x, y):
                continue
            dd = math.hypot(x - q.p.x, y - q.p.y)
            cands.append((dd - q.w / 2, x, y, q))
    cands.sort(key=lambda t: t[0])
    for edge, x, y, q in cands:
        v = SMALL[k % len(SMALL)]
        w, d = hp.COTTAGE_SIZE[v]
        # (Corner to corner, and the row's corners too: no two overlap, review-snow_region 11
        # note 3, "move this house over so it isnt interdecting with the other house".)
        room = math.hypot(w, d) / 2 + 1.8
        if not (SET - 1.0 + d / 2 <= edge <= SET + 2.0 + d / 2):
            continue
        sd = 1 if (x - q.p.x) * q.r.x + (y - q.p.y) * q.r.y > 0 else -1
        if MARKET[0] <= q.s <= MARKET[1] and sd == MARKET[2]:
            continue
        if not clear(x, y, room):
            continue
        rot = math.atan2(-q.r.y * sd, -q.r.x * sd) + math.pi / 2
        if RUIN:
            hi = level_site(c, x, y, rot, w, d, ground, ter)
            if hi is None:
                continue
            z = hi - 0.5
            box(c, "Street House %d" % len(built), x, y, w / 2 - 0.5, d / 2 - 0.5, z - 0.8, z + 4.5, ("hearth_stone", "wall"),
                rot=rot)
            box(c, "Street House Ice %d" % len(built), x, y, w / 2 + 0.4, d / 2 + 0.4, z - 0.8, z + 7.0, ("berg_ice", "wall"),
                rot=rot + 0.08)
        else:
            smoke = seat_cottage(c, v, x, y, rot, ground, name="Street Cottage %d" % len(built), ter=ter)
            if smoke is None:
                continue
            sc.chimneys.append(smoke)
            sc.warm.append((x, y, ground(x, y) + 2.5))
        taken.add(x, y, room)
        SPOTS.append((x, y, room + 0.2))
        built.append((x, y))
        k += 1
    # The market's stalls, along its stretch, facing the road, the folk about them.
    stalls = []
    s = MARKET[0] + 3.0
    while s < MARKET[1] - 3.0:
        q = c.at(s)
        x, y = side_of(q, MARKET[2], q.w / 2 + 3.2)
        rot = math.atan2(-q.r.y * MARKET[2], -q.r.x * MARKET[2]) + math.pi / 2
        if math.hypot(x - NO_STALL[0], y - NO_STALL[1]) < 5.0:
            s += 2.0
            continue
        if inside(x, y) and clear(x, y, 2.8):
            # (Level, on a stone footing down to the lowest ground under it, so the snow on
            # the steep street never fills it: Blake, review-snow_region 9 note 3.)
            hi = level_site(c, x, y, rot, 6.0, 4.0, ground, ter, most=3.0)
            lo, hi2 = footing(x, y, rot, 6.0, 4.0, ground)
            z = hi if hi is not None else hi2
            # (Stall and footing one building, "Market Stall n ...": tests/buildings.)
            box(c, "Market Stall %d Footing" % len(stalls), x, y, 3.1, 2.1, min(lo, z) - 0.8, z + 0.05, ("hearth_stone", "wall"),
                rot=rot)
            c.place(hp.stall(c, len(stalls) % 2), x, y, z + 0.05, rot=rot, coll="Village", name="Market Stall %d" % len(stalls))
            taken.add(x, y, 3.0)
            SPOTS.append((x, y, 3.5))
            stalls.append((x, y))
            s += 7.5
        else:
            s += 2.0
    if stalls:
        mx, my = stalls[len(stalls) // 2]
        q, _ = c.nearest(mx, my)
        hx, hy = mx + (mx - q.p.x) * 0.6, my + (my - q.p.y) * 0.6
        g = c.game(hx, hy, ground(hx, hy))
        c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=10.0, n=4, folk="snow", heading=0.0)
    if not RUIN:
        # A Christmas tree with its presents where the old lane left the street (note 14),
        # and a cottage on the empty stretch below the market (note 16).
        def near(x0, y0, r, rmax=16.0):
            for k in range(200):
                a, d = k * 2.399, 0.5 * math.sqrt(k) * 2.0
                if d > rmax:
                    break
                x, y = x0 + d * math.cos(a), y0 + d * math.sin(a)
                if clear(x, y, r) and inside(x, y):
                    return x, y
            return None

        spot = near(*XMAS_TREE, 4.0)
        print("hearthglow: christmas tree at", spot)
        if spot:
            tx, ty = spot
            tz = min(ground(tx + 2.5 * math.cos(a), ty + 2.5 * math.sin(a)) for a in [k * 0.785 for k in range(8)])
            c.place(hp.xmas_pine(c, 1, 11.0, lights=True), tx, ty, tz - 0.3, coll="Village")
            for k in range(5):
                a = k * 1.26 + 0.3
                px, py = tx + 3.2 * math.cos(a), ty + 3.2 * math.sin(a)
                c.place(hp.present_pile(c, k % 3), px, py, low(ground, px, py, 1.6) - 0.08, rot=a, coll="Village", role="visual")
            taken.add(tx, ty, 5.0)
            SPOTS.append((tx, ty, 5.0))
        w, d = hp.COTTAGE_SIZE[1]
        spot = near(*EXTRA_HOME, max(w, d) / 2 + 0.5, 20.0)
        print("hearthglow: the extra cottage at", spot)
        hx, hy = spot or EXTRA_HOME
        q, _ = c.nearest(hx, hy)
        rot = math.atan2(q.p.y - hy, q.p.x - hx) + math.pi / 2
        v = 1
        w, d = hp.COTTAGE_SIZE[v]
        if clear(hx, hy, max(w, d) / 2 + 0.5):
            smoke = seat_cottage(c, v, hx, hy, rot, ground, name="Street Cottage %d" % len(built), ter=ter)
            if smoke is not None:
                sc.chimneys.append(smoke)
                sc.warm.append((hx, hy, ground(hx, hy) + 2.5))
                taken.add(hx, hy, max(w, d) / 2 + 0.8)
                SPOTS.append((hx, hy, max(w, d) / 2 + 1.0))
                built.append((hx, hy))
    if not RUIN:
        yule(c, ground, ter, taken, clear, inside, stalls)
    # The lantern posts: every 18 m along, on both sides, opposite each other; lights
    # along each side post to post, and across the road from every other pair; a candy
    # cane between each two posts on each side.
    pairs = []
    s = S0 + 4.0
    while s < S1:
        q = c.at(s)
        pair = []
        for sd in (-1, 1):
            x, y = side_of(q, sd, q.w / 2 + 1.6)
            if not inside(x, y) or not taken.clear(x, y, 0.9) or not paint.road_clear(c, x, y, 0.8):
                pair.append(None)
                continue
            z = ground(x, y)
            c.place(post, x, y, z - 0.1, coll="Village", role="visual")
            c.place(paint.trunk_proto(c, 0.3, 5.0), x, y, z, coll="Collision", role="collision")
            taken.add(x, y, 1.0)
            if not RUIN:
                sc.lanterns.append((x, y, z + 4.6))
                sc.warm.append((x, y, z + 4.0))
            pair.append((x, y, z, s))
        pairs.append(pair)
        s += 18.0
    if not RUIN:
        for n, (a, b) in enumerate(zip(pairs, pairs[1:])):
            for p0, p1 in zip(a, b):
                if p0 and p1 and math.hypot(p0[0] - p1[0], p0[1] - p1[1]) < 26.0:
                    sc.lights.line((p0[0], p0[1], p0[2] + 4.3), (p1[0], p1[1], p1[2] + 4.3), sag=1.2, width=0.35)
        for n, pr in enumerate(pairs):
            if n % 2 == 0 and pr[0] and pr[1]:
                sc.lights.line((pr[0][0], pr[0][1], pr[0][2] + 4.4), (pr[1][0], pr[1][1], pr[1][2] + 4.4), sag=1.6, width=0.35)
    for a, b in zip(pairs, pairs[1:]):
        for sd, (p0, p1) in zip((-1, 1), zip(a, b)):
            if not (p0 and p1):
                continue
            q = c.at((p0[3] + p1[3]) / 2)
            x, y = side_of(q, sd, q.w / 2 + 1.4)
            if inside(x, y) and taken.clear(x, y, 0.8) and paint.road_clear(c, x, y, 0.6):
                c.place(cane, x, y, ground(x, y) - 0.1, rot=math.atan2(q.t.y, q.t.x) + (0.0 if sd > 0 else math.pi),
                        coll="Village")
                taken.add(x, y, 0.8)
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
               region=lambda w: math.hypot(w.x - cx, w.y - cy) < 110.0)
    print("hearthglow: %d cottages, %d stalls, %d posts" % (len(built), len(stalls), sum(1 for p in pairs for q in p if q)))
    return []


def low(ground, x, y, r):
    """The lowest ground round (x, y) out to r: what a thing that wide is set down on, so
    no part of it floats."""
    return min([ground(x, y)] + [ground(x + f * r * math.cos(a), y + f * r * math.sin(a))
                                 for f in (0.5, 1.0) for a in [k * 0.785 for k in range(8)]])


def _near(x0, y0, ok, rmax=14.0):
    """The nearest spot to (x0, y0) where ok(x, y) holds (a spiral out), or None."""
    for k in range(400):
        a, d = k * 2.399, 0.6 * math.sqrt(k)
        if d > rmax:
            break
        x, y = x0 + d * math.cos(a), y0 + d * math.sin(a)
        if ok(x, y):
            return x, y
    return None


def yule(c, ground, ter, taken, clear, inside, stalls):
    """review-snow_region 11 (Nov 1): small Christmas trees where a stall stood and up the
    street (notes 1, 2), a grand snowman facing the road (note 5), three little snowmen
    (note 8), and a couple of market stalls with candy canes round the empty bend (note 6)."""
    def facing(x, y):
        """A prop's front (-Y) turned to the road."""
        q, _ = c.nearest(x, y)
        return math.atan2(q.p.y - y, q.p.x - x) + math.pi / 2

    for k, (x0, y0) in enumerate(SMALL_TREES):
        spot = _near(x0, y0, lambda x, y: inside(x, y) and clear(x, y, 2.6))
        print("hearthglow: small christmas tree", k, spot)
        if not spot:
            continue
        x, y = spot
        c.place(hp.xmas_pine(c, k % 2, 6.0, lights=True), x, y, low(ground, x, y, 1.6) - 0.2, rot=k * 1.3, coll="Village")
        for j in range(2):
            a = j * 2.6 + 0.8 + k
            px, py = x + 1.9 * math.cos(a), y + 1.9 * math.sin(a)
            c.place(hp.present_pile(c, (j + k) % 3), px, py, low(ground, px, py, 1.1) - 0.08, rot=a, scale=0.7, coll="Village",
                    role="visual")
        taken.add(x, y, 2.8)
        SPOTS.append((x, y, 2.8))
    spot = _near(*GRAND_SNOWMAN, lambda x, y: inside(x, y) and clear(x, y, 1.8))
    print("hearthglow: the grand snowman at", spot)
    if spot:
        x, y = spot
        c.place(yp.grand_snowman(c, 0), x, y, low(ground, x, y, 1.2) - 0.25, rot=facing(x, y), coll="Village")
        taken.add(x, y, 2.2)
        SPOTS.append((x, y, 2.2))
    for j, (dx, dy) in enumerate(((0.0, 0.0), (2.4, 0.9), (1.0, 2.5))):
        spot = _near(LITTLE_SNOWMEN[0] + dx, LITTLE_SNOWMEN[1] + dy, lambda x, y: inside(x, y) and clear(x, y, 0.9), 8.0)
        if not spot:
            continue
        x, y = spot
        c.place(hp.snowman(c, j), x, y, low(ground, x, y, 0.6) - 0.15, rot=facing(x, y) + (j - 1) * 0.35, scale=0.45 + 0.08 * j,
                coll="Village")
        taken.add(x, y, 1.1)
        SPOTS.append((x, y, 1.1))
    # The bend: a stall either side of where Blake pinned, on the outside of the road, on
    # footings like the market's; candy canes flanking each.
    q0, _ = c.nearest(*BEND_MARKET)
    cane = hp.candy_cane(c, 5.0)
    made = 0
    here = []
    for sd in (-1, 1):
        for ds in (-4.0, 4.0, -10.0, 10.0, -14.0, 14.0):
            if made >= 2:
                break
            q = c.at(q0.s + ds)
            x, y = q.p.x + q.r.x * sd * (q.w / 2 + 3.4), q.p.y + q.r.y * sd * (q.w / 2 + 3.4)
            if math.hypot(x - BEND_MARKET[0], y - BEND_MARKET[1]) > 15.0:
                continue  # (at the bend, not up the street)
            if not (inside(x, y) and clear(x, y, 3.2)) or any(math.hypot(x - a, y - b) < 7.5 for a, b in here):
                continue
            here.append((x, y))
            rot = math.atan2(-q.r.y * sd, -q.r.x * sd) + math.pi / 2
            hi = level_site(c, x, y, rot, 6.0, 4.0, ground, ter, most=3.0)
            lo, hi2 = footing(x, y, rot, 6.0, 4.0, ground)
            z = hi if hi is not None else hi2
            n = len(stalls)
            box(c, "Market Stall %d Footing" % n, x, y, 3.1, 2.1, min(lo, z) - 0.8, z + 0.05, ("hearth_stone", "wall"), rot=rot)
            c.place(hp.stall(c, n % 2), x, y, z + 0.05, rot=rot, coll="Village", name="Market Stall %d" % n)
            taken.add(x, y, 3.3)
            SPOTS.append((x, y, 3.6))
            stalls.append((x, y))
            made += 1
            for side in (-1, 1):
                cx_, cy_ = x + q.t.x * side * 4.3, y + q.t.y * side * 4.3
                if inside(cx_, cy_) and clear(cx_, cy_, 0.7):
                    c.place(cane, cx_, cy_, ground(cx_, cy_) - 0.1, rot=math.atan2(q.t.y, q.t.x) + (0.0 if side > 0 else math.pi),
                            coll="Village")
                    taken.add(cx_, cy_, 0.8)
    print("hearthglow: %d stalls on the bend" % made, here)


def gorge_bend(c, natural):
    """The far end of the Burnt Gorge, where it bends out of sight back to the valley: a
    fall of frosted rock behind the passage (it was a black slab across the gorge)."""
    gx, gy = SL.GORGE_END
    z0 = natural(gx, gy) - 3.0
    for k, (dx, dy, rx, ry, h) in enumerate(((0.0, -10.0, 26.0, 9.0, 34.0), (-14.0, -4.0, 12.0, 8.0, 22.0),
                                              (15.0, -3.0, 13.0, 9.0, 26.0), (2.0, -18.0, 30.0, 10.0, 46.0))):
        ob = c.rock_mass("Gorge Bend %d" % k, gx + dx, gy + dy, rx, ry, z0 + h, z0=z0 - 4.0, n=14, seed=31 + k)
        c.assign(ob, c.lib("frost_cliff", "wall"))  # (v4: snowy rock, not the scorched gorge's)


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


def entry_pass(c, ground, way, taken=None):
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
    # The gateway: the Crest Gate, across the road at the top of the climb, the kingdom
    # below it (v4b).
    cx, cy, cr, cz = SL.HUB
    # (Down the climb from the top, so nothing's in the way when you crest the lip: Blake,
    # Oct 30, "the castle is in the way".)
    top = min(way, key=lambda p: math.hypot(p[0] - SL.CREST[0], p[1] - SL.CREST[1]))
    k = max(0, way.index(top) - 9)
    best = way[k]
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
    # Lantern posts the whole way, up the climb and down the switchbacks (v4b).
    post = hp.lantern_post(c, 0)
    for j in range(0, len(way) - 1, 4):
        (x0, y0), (x1, y1) = way[j], way[min(j + 1, len(way) - 1)]
        tx, ty = x1 - x0, y1 - y0
        tl = math.hypot(tx, ty) or 1.0
        for sd in ((-1, 1)[(j // 4) % 2],):
            px, py = x0 - ty / tl * sd * 8.5, y0 + tx / tl * sd * 8.5
            if not paint.road_clear(c, px, py, 3.0) or (taken is not None and not taken.clear(px, py, 1.5)):
                continue
            pz = ground(px, py)
            c.place(post, px, py, pz - 0.1, coll="Props", role="visual")
            c.place(paint.trunk_proto(c, 0.3, 5.0), px, py, pz, coll="Collision", role="collision")
            g = c.game(px, py, pz + 4.6)
            c.entity("lantern", x=g[0], y=g[1], z=g[2])
    # (No frozen falls down the old hollow's walls: Blake, review-snow_region 3, "this is strange".)
    n = 0
    print("entry pass: the gateway, %d frozen falls" % n)



def giant_pine(c, name, x, y, z, height=60.0, seed=0, snowy=True):
    """A giant evergreen (Blake, Oct 30: "another large green everpine for snowy pass"):
    a buttressed trunk, twelve tiers of drooping green boughs, each a little turned and
    ragged at its edge, snow lying on their tops, the leader at its crown. Built in place,
    one of a kind; its trunk is solid, its boughs visual."""
    import bmesh as _bm
    from course_kit import Vector

    rng = random.Random(seed)
    bm = _bm.new()
    k = hp.Parts(bm)
    r0 = height * 0.05
    k.add("giant_bark", lambda bm: props.tube(bm, [(x, y, z - 2.0), (x, y, z + height * 0.15), (x, y, z + height * 0.9)],
                                              [r0 * 1.3, r0, r0 * 0.3], n=12))
    for j in range(6):  # (the buttress roots)
        a = j * math.tau / 6 + rng.uniform(-0.2, 0.2)
        k.add("giant_bark", lambda bm, a=a: props.tube(bm, [(x + math.cos(a) * r0 * 0.6, y + math.sin(a) * r0 * 0.6, z + r0 * 1.4),
                                                            (x + math.cos(a) * r0 * 2.2, y + math.sin(a) * r0 * 2.2, z - 0.6)],
                                                       [r0 * 0.5, r0 * 0.15], n=6))
    tiers = 12

    def tier(bm, i, snow):
        t = i / tiers
        r = height * 0.32 * (1 - t * 0.86) * rng.uniform(0.94, 1.06)
        zc = z + height * (0.16 + 0.065 * i)
        depth = height * 0.1
        n = 16
        top = []
        rim = []
        for j in range(n):
            a = j * math.tau / n + i * 0.37
            rr = r * (1.0 + 0.12 * math.sin(a * 3 + i)) * (1.0 if j % 2 else 0.86)
            droop = depth * (0.55 if j % 2 else 0.4)
            rim.append(bm.verts.new((x + rr * math.cos(a), y + rr * math.sin(a), zc - droop + (0.35 if snow else 0.0))))
            top.append(bm.verts.new((x + rr * 0.3 * math.cos(a), y + rr * 0.3 * math.sin(a), zc + depth * 0.45 + (0.3 if snow else 0.0))))
        tip = bm.verts.new((x, y, zc + depth * 0.7 + (0.3 if snow else 0.0)))
        for j in range(n):
            j2 = (j + 1) % n
            bm.faces.new((rim[j], rim[j2], top[j2], top[j]))
            bm.faces.new((top[j], top[j2], tip))
        if not snow:
            bm.faces.new(list(reversed(rim)))

    for i in range(tiers):
        k.add("pine_bright", lambda bm, i=i: tier(bm, i, False))
        if snowy and i % 2 == 0:
            k.add("snow_ground", lambda bm, i=i: _snow_cap(bm, x, y, z + height * (0.16 + 0.065 * i), height * 0.32 * (1 - i / tiers * 0.86), height * 0.1))
    k.add("pine_bright", lambda bm: props.tube(bm, [(x, y, z + height * 0.9), (x, y, z + height * 1.02)], [height * 0.02, 0.05], n=6))
    groups = k.groups  # (before the bmesh goes into the mesh)
    ob = c.mesh_object(name, bm, "Props", "visual")
    for mat, faces in groups.items():
        if faces:
            c.assign(ob, c.lib(mat), faces)
    ob.data.shade_flat()
    c.place(paint.trunk_proto(c, r0 * 1.2, height * 0.5), x, y, z - 1.0, coll="Collision", role="collision")
    return ob


def _snow_cap(bm, x, y, zc, r, depth):
    """Snow lying on a tier of boughs: a thin ring on its upper slope."""
    n = 12
    lo = [bm.verts.new((x + r * 0.78 * math.cos(j * math.tau / n), y + r * 0.78 * math.sin(j * math.tau / n), zc - depth * 0.25 + 0.45)) for j in range(n)]
    hi = [bm.verts.new((x + r * 0.42 * math.cos(j * math.tau / n), y + r * 0.42 * math.sin(j * math.tau / n), zc + depth * 0.3 + 0.45)) for j in range(n)]
    for j in range(n):
        j2 = (j + 1) % n
        bm.faces.new((lo[j], lo[j2], hi[j2], hi[j]))
