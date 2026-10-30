# Dinosaur Valley, the overworld's first region: the valley the game opens in, with the
# gateways into its four courses (the Claude Doc "Kartipelago Overworld: Concept &
# Layout"; src/overworld/regions.ts places the gateways).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/valley_region.py [--ruin]      (the bpy module)
#
# v2 (Blake, Oct 26: "a unique shape ... segments of the overworld that capture the
# flavor of the level ... secretly an awesome race course ... think of kokiri forest"):
# the layout is valley_layout.py. Four lobes round Elder Mossback's camp on its low
# plateau, each one of the valley's courses' worlds, joined by necks over low ridges:
#
#   Riverbend (west)   a palm-lined river bend; its gateway among the palms on the far bank
#   Cascade (NE)       a jungle canyon climbing to the falls, temple ruins in the trees; its
#                      gateway the cave mouth beside the falls
#   Ember (SE)         volcanic ground rising to the cliffs, lava pools and smoking vents;
#                      its gateway the lava-lit tunnel
#   Bonebog (SW)       sunken swamp: pools, mud, dead trees, reeds, bones, mist; its gateway
#                      on the shore by the pyramid's tip
#
# The main road is one winding loop through all four (the champion's challenge is raced
# on it, from the line by the camp). --ruin: the valley after Cinderjaw's attack: the
# Burnt Gorge split through the north cliff, his Scar in the south up a burnt trench, the
# trees charred, the ground scorched.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import pocket_kit  # noqa: E402
from course_kit import Vector, bmesh, lerp, smooth  # noqa: E402
import region_ruin as ruin  # noqa: E402
import puzzle_kit  # noqa: E402
import props  # noqa: E402
import villager_homes as vh  # noqa: E402
import region_paint as paint  # noqa: E402
import ruin_kit  # noqa: E402
import swamp_props as sp  # noqa: E402
import bonebog_scenery as bs  # noqa: E402
import valley_layout as L  # noqa: E402
import valley_dress as vd  # noqa: E402
import valley_village as vv  # noqa: E402
import region_props as rp  # noqa: E402
import region_textures as TX  # noqa: E402

RUIN = ruin.ON
TRACK_ID = ruin.track_id("valley_region") + os.environ.get("KP_REGION_SUFFIX", "")
WATER_Z = L.WATER_Z
FLOOR_Z = 1.4  # (the other regions' builds still read these)
RIM_Z = L.RIM_Z
CAMP_R = L.CAMP[2]
GORGE_HW = 16.0
GORGE_END = L.GORGE_END
RIVER_HW = L.RIVER_HW

# The Elder's lookout (Act V's return task): a walled hollow on Ember's lower slope, its
# way in blocked by a rockfall the Valley Tool clears.
RETURN = (78.0, -108.0)
# A secret: a grotto in the Cascade's woods, walled with ice the Snow Tool melts.
SECRET = (129.0, 98.0)


def polar(a_deg, r):
    a = math.radians(a_deg)
    return r * math.cos(a), r * math.sin(a)


def gorge_x(y):
    """The Burnt Gorge winds a little as it climbs north from the road."""
    return L.GORGE[0] + 6.0 * math.sin(max(0.0, y - 155.0) / 30.0)


def burn(x, y):
    """Where Cinderjaw's fire fell (0 none .. 1): most of the valley, a few green patches
    left (the swamp's too wet to burn much)."""
    w = L.lobe_weights(x, y)
    return (0.6 + 0.45 * math.sin(x / 53.0 + 1.3) * math.cos(y / 47.0 - 0.4)) * (1.0 - 0.6 * w["bonebog"])


def _natural(x, y):
    h = L.natural(x, y)
    tz = L.tunnel_floor(x, y)
    if tz is not None:
        h = min(h, tz - 0.25)  # (under a tunnel's rock: flush under its road, out to the walls)
    bz = L.bridge_floor(x, y)
    if bz is not None:
        h = min(h, bz)  # (under a bridge's deck)
    if RUIN:
        # The Burnt Gorge: the split in the north cliff, its floor rising gently to the far
        # end, where the way on to the Snow Kingdom begins.
        # (Cut down from inside Riverbend, at its floor's height, rising gently: it used to
        # start where the wall did, leaving a 40 m hump at its mouth that the road climbed
        # and a kart couldn't get back over: Blake, Oct 26.)
        g = smooth((GORGE_HW + 12 - abs(x - gorge_x(y))) / 12) * smooth((y - L.GORGE[1] + 30.0) / 24.0)
        if g > 0:
            h = lerp(h, 4.0 + 0.04 * max(0.0, y - L.GORGE[1]), g)
        # The burnt trench up to the Scar.
        sx, sy = L.SCAR
        if y < -170 and abs(x - sx) < 26:
            t = smooth((26 - abs(x - sx)) / 10.0) * smooth((-170 - y) / 14.0)
            h = lerp(h, 10.0, t)
    return h


# The ways in to the gateways cut level with the road (pocket_kit.Notches: a gateway's
# spur mustn't climb a wall).
NOTCHES = pocket_kit.Notches(L.route_points(), dict(L.GATES, **({"lair": L.SCAR} if RUIN else {})))


def _pyramid_bay(h, x, y):
    """The wall cut back round Bonebog's pyramid, a square bay a little bigger than its
    base, down to the bog's floor (Blake, Bonebog note 5: "move the pyramid so it is not
    going into the wall")."""
    px, py = L.PYRAMID
    gx, gy = L.GATES["bonebog"]
    rot = math.atan2(py - gy, px - gx)
    ca, sa = math.cos(rot), math.sin(rot)
    u = (x - px) * ca + (y - py) * sa
    v = -(x - px) * sa + (y - py) * ca
    d = max(abs(u), abs(v))
    if d > 38.0:
        return h
    base = _natural(px - ca * 30.0, py - sa * 30.0)
    if d < 28.0:
        return min(h, base)
    return min(h, lerp(base, h, smooth((d - 28.0) / 10.0)))


def natural(x, y):
    return _pyramid_bay(NOTCHES.apply(_natural(x, y), x, y), x, y)


LOOK = {
    # lobe: (ground, cliff, road, shoulder)
    "riverbend": (("valley_grass", "grass"), ("valley_cliff", "wall"), "valley_road", ("valley_grass", "dirt")),
    "cascade": (("jungle_leafcover", "grass"), ("jungle_mossstone", "wall"), "jungle_path", ("jungle_leafcover", "dirt")),
    "ember": (("ash_soil", "dirt"), ("magma_rock", "wall"), "basalt_road", ("scorched_ground", "dirt")),
    "bonebog": (("bog_bank", "grass"), ("bog_dark_stone", "wall"), "bog_paving", ("bog_moss_ground", "dirt")),
    "camp": (("valley_grass", "grass"), ("valley_cliff", "wall"), "valley_road", ("valley_grass", "dirt")),
}
# v4 (Blake, Oct 28: "the walls are too boring ... take inspiration from the walls in
# Cascade Caverns"; Ember's lava-lined walls "complete AI slop ... have the walls fade
# into darker and darker rock"): each world's walls are beds of its own rock, one bed to a
# tier (pocket_kit.terrace), from the foot up, and the rim's crags above.
STRATA = {
    "camp": ["moss_rock", "ancient_cliff", "canyon_rock_ochre", "canyon_rock_grey", "canyon_rock_moss"],
    "riverbend": ["moss_rock", "ancient_cliff", "canyon_rock_ochre", "canyon_rock_grey", "canyon_rock_moss"],
    "cascade": ["canyon_rock_moss", "canyon_rock_grey", "canyon_rock_ochre", "canyon_rock_grey", "canyon_rock_moss"],
    "bonebog": ["ember_moss", "moss_rock", "canyon_rock_moss", "canyon_rock_grey", "moss_rock"],
    "ember": ["volcano_slag", "cave_rock", "ember_rock", "black_rock", "obsidian_cliff"],
}
# The shelves between the tiers, and the high ground over the rim.
SHELF = {"camp": ("ancient_grass", "grass"), "riverbend": ("ancient_grass", "grass"),
         "cascade": ("canopy_dark", "grass"), "bonebog": ("bog_moss_ground", "grass"), "ember": ("ember_ash", "dirt")}
POCKET_LOOK = {p[0]: p[1] for p in L.POCKETS}


def lobe_at(x, y):
    w = L.lobe_weights(x, y)
    return max(w, key=w.get)


def transition(x, y, mat_of):
    """Where two worlds meet (Blake: "gradient transition between the two textures"): the
    ground turning from one to the other in bands of transition textures
    (region_textures.py). mat_of(lobe) -> (material, surface); returns one."""
    w = L.lobe_weights(x, y)
    order = sorted(w, key=w.get, reverse=True)
    a, b = order[0], order[1]
    ma, mb = mat_of(a), mat_of(b)
    if ma[0] == mb[0]:
        return ma
    f = w[b] / (w[a] + w[b])
    if f < 0.1:
        return ma
    p = 25 if f < 0.24 else 50
    return blended(ma, mb, p)


def blended(ma, mb, p):
    """The p% transition from material ma to mb (either way round), or ma if there's none."""
    if (ma[0], mb[0]) in TX.PAIRS:
        return (TX.blend_id(ma[0], mb[0], p), ma[1] if p <= 50 else mb[1])
    if (mb[0], ma[0]) in TX.PAIRS:
        return (TX.blend_id(mb[0], ma[0], 100 - p), ma[1] if p <= 50 else mb[1])
    return ma


def classify(c, n, info):
    lobe = lobe_at(c.x, c.y)
    ground, cliff, _, _ = LOOK[lobe]
    wi = L.wall_info(c.x, c.y)
    look = POCKET_LOOK[wi["pocket"]]
    # (on the walls, only the shelves' flat tops are ground: the faces between them rock)
    steep = 0.62 if wi["t"] <= 0.05 else 0.8
    if n.z < steep:
        if RUIN and c.y > L.GORGE[1] + 20 and abs(c.x - gorge_x(c.y)) < GORGE_HW + 30:
            return ("obsidian_cliff", "wall")  # (the gorge's walls are scorched black)
        beds = STRATA[look]
        if wi["past"] > 0:
            return (beds[-1], "wall")
        frac = (c.z - wi["floor"]) / max(1.0, L.TOP - wi["floor"])
        return (beds[min(len(beds) - 2, L.tier_of(frac, wi["n"]))], "wall")
    if RUIN and c.y < -175 and abs(c.x - L.SCAR[0]) < 16:
        return ("lava_crust", "dirt")
    # Up on the shelves and over the rim: the world's ledge ground.
    if wi["t"] > 0.08 and info["d"] > 16.0:
        if RUIN and look != "bonebog" and burn(c.x, c.y) > 0.5:
            return ("scorched_ground", "dirt")
        if wi["past"] > 0:
            # (over the rim: whichever world's high ground it is, blending between them)
            return transition(c.x, c.y, lambda lb: SHELF[lb])
        return SHELF[look]
    for px, py, pr in L.POOLS:
        if math.hypot(c.x - px, c.y - py) < pr + 6 and c.z < WATER_Z + 0.6:
            return ("bog_mud", "mud")
    d, wz = L.river_d(c.x, c.y)
    # (Sand under all the water, out to the sheet's edge, not grass: Blake, Riverbend
    # note 11.)
    # (A smooth band along the banks too, by distance, not only where the land dips under
    # the water: the sand came in ragged scraps, Blake, Cascade note 10.)
    if (d < RIVER_HW + 7 and c.z < wz + 0.35) or (d < RIVER_HW + 4.5 and c.z < wz + 2.5):
        return ("valley_sand", "water")  # (the river's wadeable)
    if RUIN and lobe != "bonebog" and burn(c.x, c.y) > 0.5:
        return ("scorched_ground", "dirt")
    return transition(c.x, c.y, lambda lb: LOOK[lb][0])


def box(c, name, cx, cy, hx, hy, z0, z1, mat, rot=0.0, role="both", coll="Props"):
    bm = bmesh.new()
    ca, sa = math.cos(rot), math.sin(rot)
    vs = []
    for z in (z0, z1):
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            lx, ly = sx * hx, sy * hy
            vs.append(bm.verts.new((cx + lx * ca - ly * sa, cy + lx * sa + ly * ca, z)))
    for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([vs[i] for i in f])
    ob = c.mesh_object(name, bm, coll, role)
    c.assign(ob, c.lib(*mat))
    return ob


def cone(c, name, cx, cy, r, z0, h, mat, segs=4, role="both", coll="Props"):
    bm = bmesh.new()
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=0.0, depth=h)
    for v in res["verts"]:
        v.co = kit.Vector((cx + v.co.x, cy + v.co.y, z0 + h / 2 + v.co.z))
    ob = c.mesh_object(name, bm, coll, role)
    c.assign(ob, c.lib(*mat))
    return ob


def line(a, b, every=8.0, z=None, z0=None):
    """Points from a to b on the land (or z(x, y)); z0: the height it leaves from (a road
    it joins), eased into the land over its first 24 m so the joint is flush."""
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / every))
    total = math.hypot(b[0] - a[0], b[1] - a[1])
    pts = []
    for k in range(n + 1):
        x, y = lerp(a[0], b[0], k / n), lerp(a[1], b[1], k / n)
        h = z(x, y) if z else natural(x, y) + 0.2
        if z0 is not None:
            h = lerp(z0 + 0.02, h, smooth(total * k / n / 24.0))
        pts.append((x, y, h))
    return pts


def main():
    c = kit.Course(TRACK_ID, "Dinosaur Valley (ruined)" if RUIN else "Dinosaur Valley", "mirror_lake")
    c.route(L.route_points(), width=14.0, bank=6.0)
    kinds = {}
    for lobe, (ground, cliff, road, shoulder) in LOOK.items():
        # (A skirt under the road's edges, so where it stands over the land you see earth,
        # not through it: Blake, Riverbend note 1, "I can see the underside of this plane".)
        kinds[lobe] = {"mat": road, "shoulder": 1.5, "shoulder_mat": shoulder, "deck": 1.2, "deck_mat": cliff}
        if lobe in ("camp", "riverbend"):
            # (No tan strip of the skirt showing beside the road on the grass: its skirt the
            # grass; and the camp's road edged into the grass by a strip half road, half
            # grass, on the border: Blake, Oct 29, village notes 15, 19.)
            kinds[lobe]["deck_mat"] = ground
        if lobe == "camp":
            kinds[lobe].update(shoulder=2.0, shoulder_mat=(TX.blend_id("valley_grass", "valley_road", 50), "dirt"))
    stone = ("jungle_mossstone", "wall")
    kinds["bridge"] = {"mat": "wood_planks", "surface": "road", "shoulder": 0.6, "shoulder_mat": ("wood_planks", "road"),
                       "barrier": 1.0, "barrier_mat": ("palm_bark", "wall"), "deck": 1.8, "deck_mat": ("palm_bark", "wall"),
                       "ground": False}
    kinds["temple_bridge"] = {"mat": "jungle_temple", "surface": "road", "shoulder": 0.6, "shoulder_mat": ("ruin_stone", "road"),
                              "barrier": 1.2, "barrier_mat": stone, "deck": 2.4, "deck_mat": stone, "ground": False}
    # Where a gateway's spur leaves a bridge: its deck with no railing (Blake, Oct 28:
    # "you can't easily access Cascade Caverns because of the railing").
    kinds["bridge_open"] = {**kinds["bridge"], "barrier": 0.0}
    kinds["temple_bridge_open"] = {**kinds["temple_bridge"], "barrier": 0.0}
    c.kinds = kinds
    junctions = [c.nearest(gx, gy)[0].s for gx, gy in L.GATES.values()]

    def near_junction(s):
        return any(min(abs(s - j), c.length - abs(s - j)) < 16.0 for j in junctions)

    def label(smp):
        d, wz = L.river_d(smp.p.x, smp.p.y)
        # (a bridge only where the land's well under the road: no bank stands up through it)
        if d < RIVER_HW + 6 and smp.p.z > wz + 0.9 and natural(smp.p.x, smp.p.y) < smp.p.z - 1.2:
            kind = "temple_bridge" if lobe_at(smp.p.x, smp.p.y) == "cascade" else "bridge"
            return kind + "_open" if near_junction(smp.s) else kind
        return lobe_at(smp.p.x, smp.p.y)

    c.roads(kit.plan(c, blend_runs(c, list(kit.runs(c, label))), "camp", max_len=160.0))

    # The camp's square, and the way out of it onto the road (east).
    cx, cy, cr = L.CAMP
    trail = dict(width=10.0, shoulder=1.2, shoulder_mat=("valley_grass", "dirt"))
    # (No broad slab of a road into the camp any more, just its path: Blake, Oct 29,
    # "this looks horrible, maybe just remove this plane". See hut_paths below.)
    smp_out, _ = c.nearest(cx + cr + 30.0, cy)
    # Out from the road to each landmark's gateway (off an open stretch of deck where it
    # leaves a bridge: see bridge_open), with the shoulder of the world it's in (not grass
    # in Ember: Blake, Oct 28).
    spurs = {}
    for name, (gx, gy) in L.GATES.items():
        smp, _ = c.nearest(gx, gy)
        ax, ay = smp.p.x, smp.p.y
        d = math.hypot(gx - ax, gy - ay)
        ux, uy = (gx - ax) / d, (gy - ay) / d
        end = (gx - ux * 12.0, gy - uy * 12.0)
        spurs[name] = (end, math.atan2(-ux, uy))
        look = LOOK[lobe_at(gx, gy)]
        # (On a little way into the gateway's mouth, so its end is in the dark of the
        # tunnel: Blake, Riverbend note 6, a green strip across the road before the gate.)
        into = (end[0] + ux * 7.0, end[1] + uy * 7.0)
        # (Off a bridge, from the deck's edge, not its middle: laid over the deck, the
        # spur's surface showed through it in scraps and its edge stood out over the
        # bridge's side, Blake, Cascade note 15, "this is really jank".)
        surf = look[2]
        if not smp.ground:
            ax, ay = ax + ux * (c.width / 2 - 0.3), ay + uy * (c.width / 2 - 0.3)
            if lobe_at(ax, ay) == "cascade":
                surf = "jungle_temple"  # (paved on from the temple bridge's own stones)
        # (Its shoulders in the road's own surface, not the world's grass: a green line ran
        # along it into the gate, Blake, Riverbend note 4.)
        c.side_road(name.title() + " Road", line((ax, ay), into, z0=smp.p.z), surf, "road",
                    **{**trail, "shoulder_mat": (surf, "dirt")})
    if RUIN:
        # Up the burnt trench to Cinderjaw's Scar, and the Burnt Gorge north.
        smp, _ = c.nearest(*L.SCAR)
        c.side_road("Scar Road", line((smp.p.x, smp.p.y), (L.SCAR[0], L.SCAR[1] + 18.0), z0=smp.p.z), "basalt_road", "road",
                    width=10.0,
                    shoulder=1.2, shoulder_mat=("lava_crust", "dirt"))
        smp, _ = c.nearest(*L.GORGE)
        gorge = [(smp.p.x, smp.p.y, smp.p.z)] + [(gorge_x(y), y, natural(gorge_x(y), y) + 0.2)
                                                 for y in range(int(L.GORGE[1]) + 24, int(GORGE_END) + 1, 8)]
        c.side_road("Burnt Gorge Road", gorge, "valley_trail", "road", **trail)

    # (v4: finer, for the tiers' risers and shelves)
    X0, X1, Y0, Y1 = -310, 310, -310, 310
    ter = c.terrain("Valley", X0, X1, Y0, Y1, 2.5, natural, classify, near=8.0, fade=16.0)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 5.0, lambda x, y: natural(x, y) - 0.5, c.lib("valley_grass", "grass"))

    def ground(x, y):
        z = c.ground_z(x, y, [ter])
        return natural(x, y) if z is None else z

    # (Each hut's pots, woodpile and bench on the land where they stand.)
    vv.GROUND = ground

    # Water: the rivers and lakes in living water (valley_dress), the bog's pools.
    vd.water(c, ground)
    for k, (px, py, pr) in enumerate(L.POOLS):
        # (Not running on into a gateway's mouth: Blake, Bonebog note 2.)
        r = pr + 8.0
        for (ex, ey), _h in spurs.values():
            d = math.hypot(px - ex, py - ey)
            r = min(r, d - 14.0)
        if r < 3.0:
            continue
        c.disc("Bog Pool %d" % k, px, py, r, WATER_Z, c.lib("bog_water", "mud"), role="visual", n=30, wobble=0.15,
               seed=k)
        gx, gy, gz = c.game(px, py, WATER_Z + 0.1)
        c.entity("bubbles", x=gx, y=gy, z=gz, r=pr * 0.7)
        c.entity("mist", x=gx, y=gy + 1.0, z=gz, radius=pr + 10.0, rate=5)
    # The falls, grand, each over the sheer cliff behind it.
    for j, name in enumerate(("Riverbend Falls", "Cascade Falls")):
        vd.grand_falls(c, j, name)

    # The camp: a beaten-earth square, Riverbend's huts round a fire (burnt out after),
    # the village round it (valley_dress.camp).
    # (No beaten-earth plane any more: Blake, Oct 28, "remove this entire dirt plane and
    # just make paths connecting the huts".)
    hut_paths = []
    CAMP_HUTS.clear()
    for k in range(5):
        a = k * math.tau / 5 + 0.9
        if abs(math.sin(a)) < 0.35 and math.cos(a) > 0:
            continue  # (clear of the way out, east)
        # (On truly level ground: Blake, Oct 29, two huts were set into the side of the
        # slight rise toward the road, their doors in the ground. Each moves round or in a
        # little until the land under it is flat.)
        best = None
        for step in range(45):
            da_ = (step + 1) // 2 * 0.1 * (1 if step % 2 else -1)
            for dr in (0.0, -2.0, -4.0, 2.0, 4.0):
                aa = a + da_
                tx, ty = cx + (cr - 6 + dr) * math.cos(aa), cy + (cr - 6 + dr) * math.sin(aa)
                if any(math.hypot(tx - ox, ty - oy) < 9.5 for ox, oy in CAMP_HUTS):
                    continue
                (sx, sy), sr = vd.STAGE[1]
                if math.hypot(tx - sx, ty - sy) < sr:
                    continue  # (not by the Pact Stone: the cutscenes' ground)
                if not vd.scene_clear(tx, ty, 5.5):
                    continue  # (nor over anyone in a cutscene)
                if abs(math.sin(aa)) < 0.35 and math.cos(aa) > 0:
                    continue
                ring_ = [ground(tx + 4.2 * math.cos(t), ty + 4.2 * math.sin(t)) for t in (j * math.tau / 12 for j in range(12))]
                sp = max(ring_) - min(ring_)
                if best is None or sp < best[0] - 0.05:
                    best = (sp, aa, tx, ty)
        if best is None or best[0] > 0.3:
            print("camp hut %d: no level ground, left out" % k)
            continue
        _sp, a, hx, hy = best
        if RUIN:
            box(c, "Hut %d" % k, hx, hy, 3.2, 3.2, L.CAMP_Z - 1.0, L.CAMP_Z + 2.2 + 0.6 * (k % 2), ("obsidian_cliff", "wall"), rot=a)
            ruin.smoke(c, hx, hy, L.CAMP_Z + 2.5)
        else:
            foot = min(ground(hx + 3.6 * math.cos(t), hy + 3.6 * math.sin(t)) for t in (0.0, 1.57, 3.14, 4.71))
            vv.place_hut(c, k, hx, hy, foot - 0.05, a + math.pi)
            print("camp hut %d at (%.1f, %.1f), level to %.2f m" % (k, hx, hy, _sp))
            CAMP_HUTS.append((hx, hy))
        # (From its door to the fire, curving a little: Blake, notes 1 and 3.)
        dx, dy = hx + 4.2 * math.cos(a + math.pi), hy + 4.2 * math.sin(a + math.pi)
        hut_paths.append(vv.wander((dx, dy), (cx + 6.4 * math.cos(a), cy + 6.4 * math.sin(a)), bend=1.4 * (-1) ** k, seed=k))
    # The way out of the square east, a path on to the main road's edge.
    ox, oy = smp_out.p.x, smp_out.p.y
    od = math.hypot(ox - (cx + 6.4), oy - cy)
    ux, uy = (ox - (cx + 6.4)) / od, (oy - cy) / od
    hut_paths.append(vv.wander((cx + 6.4, cy), (ox - ux * (smp_out.w / 2 + vv.ROAD_CLEAR), oy - uy * (smp_out.w / 2 + vv.ROAD_CLEAR)), bend=0.8,
                               seed=9))
    # The Elder's fire in the middle of the camp, on a round of trodden earth where the
    # paths all meet.
    vv.plaza(c, cx, cy, 6.5, ground, name="Camp Plaza")
    vv.place_hearth(c, cx, cy, ground, rot=0.3)
    gx, gy, gz = c.game(cx, cy, L.CAMP_Z + 0.2)
    c.entity("campfire", x=gx, y=gy, z=gz)
    camp_taken = paint.Taken([(cx, cy, cr)])
    paths = vd.camp(c, ground, camp_taken) + hut_paths
    paint.EXTRA.extend(camp_taken.spots)

    thresholds(c, ground)
    landmarks(c, ground, spurs)
    if RUIN:
        ruined(c, ground, spurs)
    puzzle_kit.pen(c, "return", "Lookout", *RETURN, to_road(c, *RETURN), 11.0, 4.5, ("basalt_block", "wall"),
                   ground(*RETURN), height=6.0)
    vd.smugglers_den(c, ground, *RETURN, to_road(c, *RETURN), 11.0, 4.5, ground(*RETURN), 6.0)
    puzzle_kit.pen(c, "secret", "Grotto", *SECRET, to_road(c, *SECRET), 9.0, 4.5, ("jungle_mossstone", "wall"),
                   ground(*SECRET), height=6.0)
    vd.jungle_grotto(c, ground, *SECRET, to_road(c, *SECRET), 9.0, 4.5, ground(*SECRET), 6.0)
    roads = [ob for ob in c.coll("Roads").objects]

    def on_road(x, y):
        z = ground(x, y)
        r = c.ground_z(x, y, roads)
        return z if r is None else max(z, r)

    for name, (end, heading) in spurs.items():
        gx, gy, gz = c.game(end[0], end[1], 0.0)
        c.entity("gateway_spot", gateway=name, x=gx, z=gz, heading=heading)
        # The road carried on up into the gateway's mouth (Blake, Riverbend notes 6, 7).
        gxy = L.GATES[name]
        dx, dy = gxy[0] - end[0], gxy[1] - end[1]
        dl = math.hypot(dx, dy) or 1.0
        look = LOOK[lobe_at(*gxy)]
        # (Wide enough, and on right into the mouth, to meet the tunnel's floor: no grass
        # showing either side or between: Blake, Riverbend notes 3 and 4.)
        # (Starting clear of the main road: where it ran back over a bridge's deck it stood
        # up off the river as a block, Blake, Cascade note 15.)
        q0, _ = c.nearest(*end)
        back = max(4.0, min(14.0, math.hypot(end[0] - q0.p.x, end[1] - q0.p.y) - c.width / 2 - 2.0))
        vv.road_apron(c, (end[0] - dx / dl * back, end[1] - dy / dl * back), end, (look[2], "road"), on_road,
                      width=19.0, past=max(6.0, dl + 5.0), name=name.title() + " Gateway Apron")
    # The villagers' homes, in every part of the region (src/overworld/villagers.ts).
    # (Off the water and out of the walls: Blake's notes 34 and 45, a hut half in the river
    # and one in a wall.)
    homes = vh.homes(c, L, ground, "valley", vv.house, avoid=[(0.0, 3.0, 34.0)], wet=wet,
                     wall=-15.0, skip=("ember", "gulch"))
    # Ember's folk in obsidian huts (Blake, note 30).
    homes += vh.homes(c, L, ground, "valley", vd.obsidian_house, pockets=["ember"], wet=wet, wall=-15.0, seed=13, level=0.8,
                      foot=6.5)
    dress(c, ground, spurs)
    # Bonebog: the swamp-dweller's hut where the tier tree stood (Blake, Bonebog notes 9,
    # 10), the fossil skulls carved finely (8), and logs in the pool (7).
    hx, hy = -98.5, -173.4
    q, _ = c.nearest(hx, hy)
    vv.place_swamp_hut(c, hx, hy, ground(hx, hy) - 0.2, math.atan2(q.p.y - hy, q.p.x - hx))
    vv.fossil_skulls(c)
    px, py, pr = L.POOLS[2]
    for k, (ox, oy, a) in enumerate(((0.3, -0.2, 0.6), (-0.35, 0.3, 2.2))):
        c.place(props.log(c, k % 2), px + ox * pr, py + oy * pr, WATER_Z - 0.35, rot=a, scale=1.4, coll="Water Life",
                role="visual")
    vd.shade_walls(c, ter)
    # The paths, as ribbons laid on the land (Blake, Oct 28: the painted ones "look
    # horrible"): the camp's, and each home's from its door to the road.
    def path_look(x, y):
        under = {"cascade": "jungle_leafcover", "bonebog": "bog_bank", "ember": "ash_soil"}.get(lobe_at(x, y), "valley_grass")
        dirt = "scorched_ground" if under == "ash_soil" else "camp_earth"
        # (Into the grass in three steps, not one: Blake, Oct 29, note 12.)
        return (dirt, "dirt"), [(TX.blend_id(under, dirt, p), "dirt") for p in (75, 50, 25)]

    def meets_road(x, y):
        q, d = c.nearest(x, y)
        return d < q.w / 2 + vv.ROAD_CLEAR + 1.5

    def path_ground(x, y):
        # (Up onto the road's shoulder and surface where a path runs in under it: Blake,
        # Oct 28, a path stopping short of the road.)
        z = ground(x, y)
        r = c.ground_z(x, y, c.pieces)
        return z if r is None else max(z, r)

    all_paths = paths + [vv.home_path(c, x, y, r) for x, y, r in homes]
    vv.path_ribbons(c, all_paths, path_ground, look=path_look, verge=0.65, flare=meets_road)
    vd.place_totems(c, ground, CAMP_HUTS + [(x, y) for x, y, _r in homes], all_paths)
    vd.pact_stone_ground(c, ground)
    vv.clear_paths(c, all_paths)
    vd.area_air(c)

    # (Raced too: the champion's challenge, once round the loop, from this line by the camp.)
    c.start_line()
    gates = c.checkpoints(height=10.0)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish(extra={"race": {"laps": 1}})
    print("loop", round(c.length, 1), "gates", len(gates))


CAMP_HUTS = []


def blend_runs(c, runs, span=42.0):
    """Where the road passes from one world's paving to the next (Blake, Oct 28: "here we
    need a gradient transition between the two textures, this changes way too
    drastically"): a stretch of transition pieces between them (25, 50, 75%), its
    shoulders turning too."""
    out = []
    for i, (s0, s1, k) in enumerate(runs):
        out.append([s0, s1, k])
    res = []
    for i, r in enumerate(out):
        res.append(r)
        if i + 1 >= len(out):
            continue
        a, b = r[2], out[i + 1][2]
        if a not in LOOK or b not in LOOK or LOOK[a][2] == LOOK[b][2]:
            continue
        s = r[1]
        half = min(span / 2, (r[1] - r[0]) / 2, (out[i + 1][1] - out[i + 1][0]) / 2)
        if half < 6.0:
            continue
        r[1] = s - half
        out[i + 1][0] = s + half
        for j, p in enumerate((25, 50, 75)):
            kind = "%s>%s %d" % (a, b, p)
            if kind not in c.kinds:
                road = blended((LOOK[a][2], "road"), (LOOK[b][2], "road"), p)
                sh = blended(LOOK[a][3], LOOK[b][3], p)
                c.kinds[kind] = {"mat": road[0], "surface": "road", "shoulder": 1.5, "shoulder_mat": sh}
            res.append([s - half + 2 * half * j / 3, s - half + 2 * half * (j + 1) / 3, kind])
    return [tuple(r) for r in res]


def tunnel_span(c, a, b):
    """The stretch of the road (s0, s1) that runs through the high ground round route
    points a..b (a tunnel's length: from the wall's foot on one side to the other's)."""
    s0 = c.nearest(*L.ROUTE[a][:2])[0].s
    s1 = c.nearest(*L.ROUTE[b][:2])[0].s
    if s1 < s0:
        s1 += c.length

    def inwall(s):
        q = c.at(s)
        return L.wall_sd(q.p.x, q.p.y) > -10.0

    for _ in range(40):
        if not inwall(s0 - 3.0):
            break
        s0 -= 3.0
    for _ in range(40):
        if not inwall(s1 + 3.0):
            break
        s1 += 3.0
    return s0, s1


def thresholds(c, ground):
    """The ways between the worlds (Blake: tunnels you can't see through, walls that are
    landscape): a ridge of rock heaped over the road where it crosses the high ground,
    bored through, each its own: the Fallen Giant (a colossal hollow log the dinosaurs
    made their tunnel, lanterns inside), the Lava Tube (basalt, lava glowing in channels
    along its walls) and the Temple Steps (carved stone, a gateway at each end)."""
    for name, kind, a, b in L.TUNNELS:
        s0, s1 = tunnel_span(c, a, b)
        mid = c.at((s0 + s1) / 2)
        half_len = (s1 - s0) / 2
        ang = math.atan2(mid.t.y, mid.t.x)
        zr = min(c.at(s0).p.z, c.at(s1).p.z)
        wall, top = {"log": (("valley_cliff", "wall"), ("valley_grass", "grass")),
                     "lava": (("volcano_basalt", "wall"), ("ash_soil", "dirt")),
                     "temple": (("jungle_mossstone", "wall"), ("jungle_leafcover", "grass"))}[kind]
        # The heap over the road (it fills the cut the road makes through the high ground,
        # and stands a little over the ridge round it, so nothing shows through).
        # (v4: as high as the ridge it crosses, no higher: it stood up out of a lower ridge
        # like a tower, Blake's notes 37 and 39)
        ridge = max(L.natural(mid.p.x + mid.t.x * f * (half_len + 10.0) + mid.r.x * o, mid.p.y + mid.t.y * f * (half_len + 10.0)
                              + mid.r.y * o) for f in (-1.0, -0.5, 0.0, 0.5, 1.0) for o in (-30.0, -15.0, 15.0, 30.0))
        rock = c.rock_mass(name + " Rock", mid.p.x, mid.p.y, half_len + 16.0, 40.0, min(L.TOP - 1.0, ridge + 2.0), z0=zr - 6.0, n=30,
                           seed=len(name), angle=ang, base=zr,
                           bands=[(1.0, 0.0), (1.0, 0.22), (0.92, 0.24), (0.91, 0.46), (0.83, 0.48), (0.82, 0.7),
                                  (0.75, 0.72), (0.73, 0.94), (0.68, 1.0)])
        half = c.width / 2 + (4.5 if kind == "log" else 3.0)
        c.tunnel(rock, s0, s1, half=half, height=13.0 if kind == "log" else 10.0, pad=6.0)
        for p, q in ((s0 - 70.0, s0 - 2.0), (s1 + 2.0, s1 + 70.0)):  # (overlapping the bore: no skin left between)
            c.tunnel(rock, p, q, half=half + 1.0, height=70.0, pad=0.0, floor=-12.0)
        heap_strata(c, rock, kind, zr, top)
        if kind in ("log", "temple") and not RUIN:
            vd.ledge_greens(c, rock, ground, seed=len(name))
        if kind == "log":
            fallen_giant(c, s0, s1)
        elif kind == "lava":
            # (v4: lava in basalt-kerbed troughs, columns along the walls: valley_dress)
            vd.lava_tube(c, s0, s1, half)
            for k in range(3):
                q = c.at(s0 + (s1 - s0) * (k + 0.5) / 3)
                g = c.game(q.p.x + q.r.x * (c.width / 2 + 2.6), q.p.y + q.r.y * (c.width / 2 + 2.6), q.p.z + 0.2)
                c.entity("steam", x=g[0], y=g[1], z=g[2])
            # (No steam puffing up in the middle of the road at its two mouths: Blake, Ember
            # note 2, "a weird smoke effect I want to remove".)
        else:
            for k, s in enumerate((s0 - 1.0, s1 + 1.0)):
                q = c.at(s)
                rot = math.atan2(q.r.y, q.r.x)
                for sd in (-1, 1):
                    x, y = q.p.x + q.r.x * sd * (half + 1.6), q.p.y + q.r.y * sd * (half + 1.6)
                    box(c, "%s Jamb %d %d" % (name, k, sd), x, y, 1.6, 2.2, q.p.z - 1.0, q.p.z + 11.0,
                        ("jungle_temple", "wall"), rot=rot)
                box(c, "%s Lintel %d" % (name, k), q.p.x, q.p.y, half + 3.4, 2.4, q.p.z + 10.0, q.p.z + 12.6,
                    ("jungle_temple", "wall"), rot=rot)
                # (Its face, local -Y, out along the road, at whoever's coming: it looked
                # off sideways, Blake, Cascade note 13, "rotate this face so it is facing
                # outward".)
                sg = -1.0 if k == 0 else 1.0
                c.place(props.idol_head(c), q.p.x, q.p.y, q.p.z + 12.6, rot=math.atan2(sg * q.t.x, -sg * q.t.y),
                        role="visual")
            vd.temple_tunnel(c, s0, s1, half)


HEAP_LOOK = {"log": ("riverbend", "bonebog"), "lava": ("bonebog", "ember"), "temple": ("cascade", "camp")}


def heap_strata(c, rock, kind, zr, top):
    """A threshold's heap of rock in the beds of the worlds either side of it (Blake, note
    37: "this is boring, let's add some ledges with grass and maybe a small shrub"): its
    shelves grassed and planted, its faces in strata, the two worlds' rock meeting over
    the bore."""
    a, b = HEAP_LOOK[kind]
    groups = {}
    shelves = []
    mw = rock.matrix_world
    for p in rock.data.polygons:
        cen = mw @ p.center
        if p.normal.z > 0.6:
            groups.setdefault(top, []).append(p.index)
            if cen.z > zr + 4.0:
                shelves.append(cen)
            continue
        look = a if L.wall_sd(cen.x, cen.y) < 0 and lobe_at(cen.x, cen.y) == a else b
        beds = STRATA[look]
        frac = (cen.z - zr) / max(1.0, L.TOP - zr)
        groups.setdefault((beds[min(len(beds) - 2, int(frac * 4))], "wall"), []).append(p.index)
    for mat, faces in groups.items():
        c.assign(rock, c.lib(*mat), faces)
    rock.data.shade_flat()
    plants = {"riverbend": [props.bush(c, 0), props.fern(c)], "camp": [props.bush(c, 1), props.fern(c)],
              "cascade": [props.big_leaf_plant(c, 0), props.fern(c)], "bonebog": [props.fern(c), props.fern(c)],  # (no trees over the canopy: Blake, Oct 29)
              "ember": [props.dead_tree(c), props.crystals(c, "obsidian_cliff")]}
    taken = []
    for k, cen in enumerate(shelves):
        if k % 3 or any((cen - q).length < 4.0 for q in taken):
            continue
        # (Not on the road through the bore: Blake, Oct 28, charred trees and crystals in
        # the middle of the Lava Tube.)
        if not paint.road_clear(c, cen.x, cen.y, 2.5):
            continue
        look = a if lobe_at(cen.x, cen.y) == a else b
        pick = plants[look][k % 2]
        c.place(pick, cen.x, cen.y, cen.z - 0.2, rot=k * 1.3, scale=0.8 if pick.startswith("Tier") else 1.2, coll="Ledges",
                role="visual")
        taken.append(cen)


def fallen_giant(c, s0, s1):
    """The Fallen Giant: a colossal hollow trunk lying through the ridge, the road running
    inside it, its broken top and its root plate standing out at the two ends, the
    dinosaurs' lanterns hung in it, moss over it."""
    ro, ri = 13.0, 11.0
    lift = ri * 0.42
    a = c.at(s0 - 8.0)
    bm = bmesh.new()
    n = 20
    rings = []
    m = max(6, int((s1 - s0 + 16.0) / 3.0))
    frames = []
    for k in range(m + 1):
        f = k / m
        q = c.at(s0 - 8.0 + (s1 - s0 + 16.0) * f)  # (it follows the road, bending with it)
        side = Vector((q.r.x, q.r.y, 0.0)).normalized()
        c0 = Vector((q.p.x, q.p.y, q.p.z + lift))
        frames.append((c0, side, q))
        lump = 1.0 + 0.04 * math.sin(f * 17.0)
        outer = [bm.verts.new(c0 + (side * math.cos(t) + Vector((0, 0, math.sin(t)))) * ro * lump)
                 for t in (j * math.tau / n for j in range(n))]
        inner = [bm.verts.new(c0 + (side * math.cos(t) + Vector((0, 0, math.sin(t)))) * ri)
                 for t in (j * math.tau / n for j in range(n))]
        rings.append((outer, inner))
    for (o0, i0), (o1, i1) in zip(rings, rings[1:]):
        for j in range(n):
            jj = (j + 1) % n
            bm.faces.new((o0[j], o0[jj], o1[jj], o1[j]))
            bm.faces.new((i0[j], i1[j], i1[jj], i0[jj]))
    for (oo, ii), flip in ((rings[0], True), (rings[-1], False)):
        for j in range(n):
            jj = (j + 1) % n
            f = (oo[j], ii[j], ii[jj], oo[jj])
            bm.faces.new(f if flip else tuple(reversed(f)))
    o, side, qa = frames[0]
    end, side_e, qb = frames[-1]
    ax = Vector((qa.t.x, qa.t.y, 0.0)).normalized()
    zc = o.z
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    log = c.mesh_object("Fallen Giant", bm, "Props", "both")
    c.assign(log, c.lib("giant_bark", "wall"))
    # The root plate at one end: roots twisting out of the trunk's end and down into the
    # ground (v4: real roots, not cones).
    bm = bmesh.new()
    for k in range(11):
        t = k * math.tau / 11 + 0.3
        d = (side * math.cos(t) + Vector((0, 0, math.sin(t)))).normalized()
        if d.z < -0.6:
            continue
        p0 = o + d * ro * 0.85 + ax * 1.5
        p1 = p0 + d * (4.0 + 1.5 * math.sin(k * 2.1)) - ax * 2.5
        p2 = p1 + d * 2.5 - ax * 3.0 + Vector((0, 0, -3.0 - 2.0 * max(0.0, d.z)))
        p3 = Vector((p2.x - ax.x * 2.0 + d.x * 2.0, p2.y - ax.y * 2.0 + d.y * 2.0, qa.p.z - 2.0))
        # (None across the road: Blake, Oct 28, "they go right in the road".)
        if any(not paint.road_clear(c, v.x, v.y, 1.5) for v in (p1, p2, p3)):
            continue
        props.tube(bm, [tuple(p0), tuple(p1), tuple(p2), tuple(p3)], [1.3, 1.0, 0.7, 0.35], n=6)
    roots = c.mesh_object("Giant Roots", bm, "Props", "visual")
    c.assign(roots, c.lib("giant_bark", "wall"))
    # (Its broken top's splinters are gone: Blake, Oct 28, "delete this".)
    # Torches up its walls, webs and roots at the swamp's end (valley_dress), and a carved
    # frame of bones at the near mouth.
    vd.log_tunnel(c, s0, s1, ro, ri, lift)
    q = c.at(s0 - 6.0)
    # The horned skull over the mouth, carved finely in the game (Blake, Riverbend note 15:
    # "completely redone and high fidelity"): render/villageDecor.ts, a horned_skull
    # entity. (Smaller than it was, 1.8: its frill was wider than the cut through the rock
    # over the road and was lost in the rock either side, so it didn't read as a
    # triceratops: Blake, Riverbend note 7.)
    face = math.atan2(-q.t.y, -q.t.x)
    g = c.game(q.p.x, q.p.y, zc + ro + 0.2)
    c.entity("horned_skull", x=g[0], y=g[1], z=g[2], scale=1.1, heading=round(math.atan2(math.cos(face), -math.sin(face)), 3))


def facing(spurs, name):
    """The way a landmark at the end of its spur faces (back down the spur), as a box's
    turn: its local x across the spur."""
    (ex, ey), _ = spurs[name]
    gx, gy = L.GATES[name]
    return math.atan2(gy - ey, gx - ex) + math.pi / 2


def landmarks(c, ground, spurs):
    """Each lobe's landmark, its gateway in front of it."""
    # Cascade Caverns' cave mouth beside the falls; Ember Peak's lava-lit tunnel.
    for name, key, rock in (("Cave Mouth", "cascade", ("jungle_mossstone", "wall")),
                            ("Tunnel Mouth", "ember", ("black_rock", "wall"))):
        gx, gy = L.GATES[key]
        rot = facing(spurs, key)
        z0 = ground(gx - 8 * math.cos(rot - math.pi / 2), gy - 8 * math.sin(rot - math.pi / 2))
        box(c, name, gx, gy, 9.0, 2.0, z0 - 1.0, z0 + 11.0, ("dark_corridor", "wall"), rot=rot, role="visual")
        for side in (-1, 1):
            px, py = gx + side * 8.0 * math.cos(rot), gy + side * 8.0 * math.sin(rot)
            box(c, name + " Jamb %d" % side, px, py, 1.6, 2.6, z0 - 1.0, z0 + 12.0, rock, rot=rot)
        box(c, name + " Lintel", gx, gy, 10.0, 2.8, z0 + 11.0, z0 + 14.0, rock, rot=rot)
    gx, gy = L.GATES["ember"]
    rot = facing(spurs, "ember")
    z0 = ground(gx, gy)
    box(c, "Tunnel Lava", gx + 1.5 * math.cos(rot - math.pi / 2), gy + 1.5 * math.sin(rot - math.pi / 2), 7.0, 0.6, z0 - 3.0,
        z0 + 2.0, ("volcano_lava", "wall"), rot=rot, role="visual")
    # The volcano over Ember's cliffs (valley_dress: a real cone, lava down its gullies).
    vd.volcano(c)
    # Ember's lava pools, ringed with black rock, bubbling and steaming.
    for k, (px, py, pr) in enumerate(L.LAVA):
        if k == 1:
            continue  # (not the one before Ember's gateway, nor its rocks: Blake, Ember note 5)
        g = ground(px, py)
        c.disc("Lava Pool %d" % k, px, py, pr, g - 0.2, c.lib("volcano_lava"), coll="Props", role="visual", n=18, wobble=0.25,
               seed=11 + k)
        for j in range(5):
            a = j * math.tau / 5 + k
            cone(c, "Lava Rim %d %d" % (k, j), px + (pr + 2.0) * math.cos(a), py + (pr + 2.0) * math.sin(a), 2.2, g - 0.8,
                 2.6 + j % 2, ("obsidian_cliff", "wall"), segs=5)
        gx, gy, gz = c.game(px, py, g + 0.2)
        c.entity("bubbles", x=gx, y=gy, z=gz, r=pr * 0.8, molten=True)
        c.entity("steam", x=gx, y=gy, z=gz)
    # Bonebog Pyramid (Blake, Oct 28: "move this pyramid and make it larger and match the
    # colour of the ruins in Bonebog that we drive through"): further back behind its
    # gateway, a great stepped pyramid in Bonebog's own dark mossy stone, a carved band
    # round each tier, its upper tiers rising out of the bog.
    px, py = L.PYRAMID
    gx, gy = L.GATES["bonebog"]
    rot = math.atan2(py - gy, px - gx)
    # (Out of the wall, Blake's Bonebog note 5: the wall is cut back round it into a bay,
    # natural() below.)
    k_size = 1.0
    z = WATER_Z - 2.0
    for k, (half, h) in enumerate(((24.0, 5.0), (19.5, 5.0), (15.0, 5.0), (10.5, 5.0), (6.5, 4.5), (3.2, 4.0))):
        half *= k_size
        box(c, "Pyramid Tier %d" % k, px, py, half, half, z, z + h, ("bog_stone", "wall"), rot=rot)
        box(c, "Pyramid Band %d" % k, px, py, half + 0.15, half + 0.15, z + h - 1.0, z + h - 0.4, ("bog_carved", "wall"),
            rot=rot, role="visual")
        z += h
    cone(c, "Pyramid Tip", px, py, 3.0, z, 3.5, ("bog_dark_stone", "wall"))
    # Its stair up the front, toward the gateway.
    for k in range(8):
        sx, sy = px - math.cos(rot) * (24.0 * k_size - k * 2.6), py - math.sin(rot) * (24.0 * k_size - k * 2.6)
        box(c, "Pyramid Stair %d" % k, sx, sy, 2.0, 4.0, WATER_Z - 2.0, WATER_Z + 1.0 + k * 3.4, ("bog_carved", "wall"),
            rot=rot, role="visual")
    # The bay's walls made rocky plateaus (Blake, Bonebog notes 19 and 20: "this wall is
    # bland, lets make it have more rocky plateau features", "lets make this wall look
    # better"): buttresses of the swamp's mossy rock standing out of them, stepped in
    # flat-topped tiers, ferns and shrubs along their ledges.
    ca, sa = math.cos(rot), math.sin(rot)
    base = ground(px - ca * 30.0, py - sa * 30.0)
    beds = [("moss_rock", "wall"), ("canyon_rock_moss", "wall"), ("canyon_rock_grey", "wall"), ("moss_rock", "wall")]
    n_out = 0
    for k, (u, v, side) in enumerate(((31.0, -22.0, 0), (31.0, 3.0, 0), (31.0, 26.0, 0), (14.0, -31.0, 1), (-12.0, -31.0, 1),
                                      (14.0, 31.0, 1), (-12.0, 31.0, 1))):
        x, y = px + u * ca - v * sa, py + u * sa + v * ca
        if not paint.road_clear(c, x, y, 14.0):
            continue
        # (Against the bay's wall, standing out of it, up toward the wall's top.)
        uu, vv = (u + 12.0, v) if side == 0 else (u, v + math.copysign(12.0, v))
        top = ground(px + uu * ca - vv * sa, py + uu * sa + vv * ca)
        h = base + (top - base) * (0.55 + 0.12 * (k % 3))
        if h < base + 6.0:
            continue
        ang = rot + (math.pi / 2 if side == 0 else 0.0)
        rock = c.rock_mass("Bay Plateau %d" % k, x, y, 11.0 + 2.0 * (k % 2), 7.0, h, z0=base - 4.0, n=18, seed=70 + k,
                           angle=ang, base=base,
                           bands=[(1.0, 0.0), (1.0, 0.3), (0.86, 0.33), (0.84, 0.6), (0.7, 0.63), (0.68, 0.85),
                                  (0.55, 0.88), (0.52, 1.0)])
        groups = {}
        mw = rock.matrix_world
        for poly in rock.data.polygons:
            cen = mw @ poly.center
            if poly.normal.z > 0.6:
                groups.setdefault(("bog_moss_ground", "grass"), []).append(poly.index)
            else:
                f = (cen.z - base) / max(1.0, h - base)
                groups.setdefault(beds[min(len(beds) - 1, int(f * len(beds)))], []).append(poly.index)
        for mat, faces in groups.items():
            c.assign(rock, c.lib(*mat), faces)
        rock.data.shade_flat()
        if not RUIN:
            vd.ledge_greens(c, rock, ground, seed=80 + k, every=0.7, floor=base)
        n_out += 1
    print("bonebog bay: %d rock plateaus" % n_out)


def ruined(c, ground, spurs):
    """After Cinderjaw's attack: his Scar, the Burnt Gorge's far end, smoke and rubble."""
    sx, sy = L.SCAR
    for k in range(9):
        a = k * math.tau / 9
        if abs(math.sin(a) - 1.0) < 0.35:
            continue  # (its mouth, towards the valley)
        px, py = sx + 17.0 * math.cos(a), sy + 17.0 * math.sin(a)
        cone(c, "Scar Rock %d" % k, px, py, 6.0 + 2.0 * math.sin(k * 2.3), ground(px, py) - 1.0, 12.0 + 6.0 * math.cos(k * 1.7),
             ("obsidian_cliff", "wall"), segs=5)
    g = ground(sx, sy)
    c.disc("Scar Lava", sx, sy - 4.0, 9.0, g + 0.25, c.lib("volcano_lava"), coll="Props", role="visual", n=18, wobble=0.2, seed=7)
    gx, gy, gz = c.game(sx, sy - 4.0, g + 1.0)
    c.entity("eruption", x=gx, y=gy, z=gz, period=9.0, offset=1.0)
    for k in range(4):
        px, py = sx + (k - 1.5) * 9.0, sy + 12.0
        ruin.smoke(c, px, py, ground(px, py) + 0.2)
    # The gorge's far end: it bends out of sight (the passage on starts just before it).
    box(c, "Gorge Bend", gorge_x(GORGE_END + 25.0), GORGE_END + 25.0, GORGE_HW + 24.0, 6.0, 0.0, RIM_Z + 10.0,
        ("obsidian_cliff", "wall"))
    for k, y in enumerate((300.0, 350.0, 400.0)):
        x = gorge_x(y) + (GORGE_HW - 2.0) * (1 if k % 2 else -1)
        ruin.smoke(c, x, y, ground(x, y) + 0.2)
    # Rubble at the cave and tunnel mouths.
    for name in ("cascade", "ember"):
        gx, gy = L.GATES[name]
        rot = facing(spurs, name)
        for side in (-1, 1):
            x, y = gx + side * 16.0 * math.cos(rot), gy + side * 16.0 * math.sin(rot)
            ruin.rubble(c, "%s Rubble %d" % (name, side), x, y, ground, ("valley_cliff", "wall"), seed=len(name) + side)


def wet(x, y):
    """In or beside water: the rivers, the lakes, the bog's pools, Ember's lava."""
    if L.river_d(x, y)[0] < RIVER_HW + 9.0:
        return True
    return any(math.hypot(x - px, y - py) < pr + 9.0 for px, py, pr in L.POOLS + L.LAVA)


def to_road(c, x, y):
    """The way from (x, y) to the nearest of the main road (a pen's gate faces it)."""
    q, _ = c.nearest(x, y)
    return math.atan2(q.p.y - y, q.p.x - x)


def entrances(c):
    """Where the main road crosses into each lobe: [{s, frm, to}], s along the road."""
    out = []
    prev = lobe_at(c.S[0].p.x, c.S[0].p.y)
    for smp in c.S:
        cur = lobe_at(smp.p.x, smp.p.y)
        if cur != prev:
            out.append({"s": smp.s, "frm": prev, "to": cur})
            prev = cur
    return out


def gates(c, ground):
    """Each lobe's sign where the road comes into it, so you know the course's world from
    its threshold: the swamp through a giant's rib cage, Ember between smoking basalt
    stacks, the Cascade under a temple lintel, Riverbend between two great palms."""
    for k, e in enumerate(entrances(c)):
        to, s = e["to"], e["s"] + 10.0
        for _ in range(40):  # (out of a tunnel first, into the pocket)
            q = c.at(s)
            if L.wall_sd(q.p.x, q.p.y) < -14.0:
                break
            s += 4.0
        q = c.at(s)
        half = q.w / 2
        side = lambda sd, off=0.0: (q.p.x + q.r.x * sd * (half + off), q.p.y + q.r.y * sd * (half + off))
        head = math.atan2(q.t.y, q.t.x)
        if to == "bonebog":
            bs.rib_cage(c, None, s - 14.0, s + 22.0, "Bonebog Ribs %d" % k, spine_up=13.0, reach=half + 7.0, every=6.0)
        elif to == "ember":
            # (The brazier stood in among the basalt stacks, which reach 4.4 m round their
            # middle: Blake, valley polish 15, note 9, "this torch is in the wall". Now
            # the stacks stand back off the shoulder, and each brazier a little before its
            # stack, clear of it.)
            qb = c.at(s - 7.0)
            for sd in (-1, 1):
                x, y = side(sd, 6.5)
                c.place(props.basalt_columns(c), x, y, ground(x, y) - 0.3, rot=head, scale=1.6)
                x, y = qb.p.x + qb.r.x * sd * (qb.w / 2 + 2.6), qb.p.y + qb.r.y * sd * (qb.w / 2 + 2.6)
                c.place(sp.stone_brazier(c), x, y, ground(x, y) - 0.1)
                gx, gy, gz = c.game(x, y, ground(x, y) + 1.6)
                c.entity("torch", x=gx, y=gy, z=gz)
        elif to == "cascade":
            vd.cascade_gate(c, q, half, ground, k)
        elif to == "riverbend":
            for sd in (-1, 1):
                x, y = side(sd, 3.5)
                c.place(props.palm(c, 15.0, 2.0, 2), x, y, ground(x, y) - 0.2, rot=head + sd)


def dress(c, ground, spurs):
    """The paint pass, lobe by lobe, each with its course's own things. After the attack:
    the same trees charred where the fire fell, the undergrowth burnt away."""
    taken = paint.Taken([(L.CAMP[0], L.CAMP[1], L.CAMP[2] + 6.0), (*L.PYRAMID, 34.0), (*RETURN, 18.0),
                         (*SECRET, 16.0), *((x, y, 30.0) for x, y in L.FALLS), *((x, y, r + 8.0) for x, y, r, _ in L.LAKES),
                         *((e[0], e[1], 16.0) for e, _ in spurs.values()), *((x, y, 22.0) for x, y in L.GATES.values()),
                         *((x, y, r + 6.0) for x, y, r in L.POOLS), *((x, y, r + 8.0) for x, y, r in L.LAVA),
                         (*L.SCAR, 30.0)])

    # v4: the jungle giants and ruins, the swamp's canopy, Ember's fires, geysers, the
    # walls' life, the water's banks (valley_dress), first: the big things.
    vd.cascade(c, ground, taken)
    vd.swamp(c, ground, taken)
    vd.ember(c, ground, taken)
    vd.banks(c, ground, taken)
    if not RUIN:
        # (On the side wall's top: the wall's 0.6 m thick past a 0.6 m shoulder, and stands
        # 0.9 m over the deck. None where a gateway's spur leaves the bridge: no wall there.)
        junctions = [c.nearest(gx, gy)[0].s for gx, gy in L.GATES.values()]
        vd.bridge_dress(c, lambda q: lobe_at(q.p.x, q.p.y) != "cascade", ground, rail=(0.9, 0.9),
                        railed=lambda q: all(min(abs(q.s - j), c.length - abs(q.s - j)) >= 16.0 for j in junctions))
    vd.wall_life(c, ground, taken)

    tunnels = [tunnel_span(c, a, b) for _, _, a, b in L.TUNNELS]

    def in_tunnel(x, y):
        q, d = c.nearest(x, y)
        if d > 30.0:
            return False
        return any(s0 - 6.0 <= q.s <= s1 + 6.0 or s0 - 6.0 <= q.s + c.length <= s1 + 6.0 for s0, s1 in tunnels)

    def inside(x, y):
        if L.wall_sd(x, y) > -8:
            return False
        # (Nothing scattered in the tunnels: Blake, Oct 28, charred trees and crystals in
        # the middle of the lava tube's road.)
        if in_tunnel(x, y):
            return False
        if L.river_d(x, y)[0] < RIVER_HW + 5:
            return False
        if RUIN and abs(x - gorge_x(y)) < GORGE_HW + 14 and y > L.GORGE[1]:
            return False
        return True

    def lobe(name):
        return lambda x, y: inside(x, y) and lobe_at(x, y) == name

    def bank(x, y):
        return inside(x, y) and L.river_d(x, y)[0] < RIVER_HW + 22

    rmax = 420.0
    # Rocks at the cliffs' feet, lobe by lobe.
    for name, mat in (("riverbend", "valley_cliff"), ("cascade", "jungle_mossstone"), ("ember", "volcano_basalt"),
                      ("bonebog", "bog_dark_stone")):
        def foot(x, y, n=name):
            return lobe(n)(x, y) and L.wall_sd(x, y) > -30

        for v in range(2):
            paint.scatter(c, props.boulder(c, mat, v), 8, rmax, foot, ground, taken, 90 + v + len(name), room=4.0,
                          scale=(1.0, 2.4))
    # Riverbend: palms along the river and the road, jungle trees.
    palms = [props.palm(c, 10.0 + 1.5 * v, 1.3 + 0.5 * v, v) for v in range(3)]
    rb = lobe("riverbend")
    for v, p in enumerate(palms):
        paint.scatter(c, p, 20, rmax, lambda x, y: bank(x, y) and lobe_at(x, y) in ("riverbend", "camp"), ground, taken, 20 + v,
                      room=4.0, scale=(0.9, 1.4), road_margin=5.0, trunk=(0.6, 8.0))
        paint.scatter(c, p, 14, rmax, rb, ground, taken, 10 + v, room=4.0, near_road=(5.0, 14.0), scale=(0.9, 1.4),
                      trunk=(0.6, 8.0))
    for v in range(2):
        paint.scatter(c, props.jungle_tree(c, v), 22, rmax, rb, ground, taken, 30 + v, room=5.0, scale=(1.0, 1.6),
                      road_margin=6.0, trunk=(0.8, 6.0))
    # Cascade: a jungle canyon: giant and grand trees, big-leaf plants, temple ruins.
    cas = lobe("cascade")
    for v in range(2):
        paint.scatter(c, props.grand_tree(c, v), 10, rmax, cas, ground, taken, 62 + v, room=10.0, scale=(1.2, 1.6),
                      road_margin=9.0, trunk=(1.6, 10.0))
        paint.scatter(c, props.jungle_tree(c, v), 30, rmax, cas, ground, taken, 64 + v, room=5.0, scale=(1.1, 1.9),
                      road_margin=6.0, trunk=(0.8, 6.0))
        paint.scatter(c, props.big_leaf_plant(c, v), 40, rmax, cas, ground, taken, 66 + v, room=2.5, role="visual")
    for v, p in enumerate((props.ruin_column(c, 0), props.ruin_column(c, 1), props.ruin_blocks(c, 0), props.stele(c, 0),
                           props.idol_head(c))):
        paint.scatter(c, p, 5, rmax, cas, ground, taken, 70 + v, room=5.0, near_road=(5.0, 24.0))
    # Ember: charred trees, basalt columns, glowing crystals, smoking vents.
    em = lobe("ember")
    paint.scatter(c, props.dead_tree(c), 30, rmax, em, ground, taken, 80, room=5.0, scale=(1.0, 1.7), road_margin=5.0,
                  trunk=(0.6, 6.0))
    paint.scatter(c, props.basalt_columns(c), 10, rmax, em, ground, taken, 81, room=7.0, road_margin=7.0)
    # (Black glass, not glowing orange spikes that looked like cheap cone fire: Blake, Ember
    # note 1, "only ... the high fidelity fire, not the low quality cone looking fire".)
    paint.scatter(c, props.crystals(c, "obsidian_cliff"), 12, rmax, em, ground, taken, 82, room=4.0, role="visual")
    for x, y in paint.scatter(c, props.boulder(c, "volcano_basalt", 2), 8, rmax, em, ground, taken, 83, room=6.0):
        gx, gy, gz = c.game(x, y, ground(x, y) + 1.0)
        c.entity("steam", x=gx, y=gy, z=gz)
    # Bonebog: swamp trees, reeds and cattails round the pools, lily pads on them, glowing
    # caps, skulls and bones.
    bog = lobe("bonebog")

    def shore(x, y):
        # (At the pools' edges, the water's, not out on the land: Blake, Riverbend note 10.)
        return bog(x, y) and ground(x, y) < WATER_Z + 0.4 and any(abs(math.hypot(x - px, y - py) - pr - 7.0) < 2.0
                                                                   for px, py, pr in L.POOLS)

    for v in range(2):
        vd.place_big(c, rp.swamp_tree(c, v), 24, (-rmax, rmax, -rmax, rmax), bog, ground, taken, 40 + v, room=6.0,
                     margin=6.0, trunk=(0.9, 6.0), scale=(1.0, 1.5), sink=0.3, foot=3.2)
        paint.scatter(c, props.cattails(c, v), 30, rmax, shore, ground, taken, 42 + v, room=2.0, role="visual")
    paint.scatter(c, props.reeds(c), 50, rmax, shore, ground, taken, 44, room=2.0, role="visual")
    paint.scatter(c, props.glow_caps(c), 30, rmax, bog, ground, taken, 45, room=2.0, role="visual")
    paint.scatter(c, props.skull(c), 10, rmax, bog, ground, taken, 46, room=4.0, road_margin=4.0)
    for k, (px, py, pr) in enumerate(L.POOLS):
        for j in range(int(pr / 4)):
            a = j * 2.39996 + k
            r = pr * 0.8 * math.sqrt((j + 0.5) / (pr / 4))
            x, y = px + r * math.cos(a), py + r * math.sin(a)
            if math.hypot(x - L.PYRAMID[0], y - L.PYRAMID[1]) > 34 and paint.road_clear(c, x, y, 3.0):
                c.place(props.lily_pad(c, j % 3), x, y, WATER_Z + 0.03, rot=a * 3.0, role="visual")
    # The swamp's big things: giant trees, stilt huts on the shores, sunken timber and
    # crocodiles in the pools, bone piles, torch posts along its road.
    vd.place_big(c, sp.swamp_giant(c, 0), 6, (-rmax, rmax, -rmax, rmax), bog, ground, taken, 47, room=14.0, margin=12.0,
                 trunk=(2.5, 12.0), scale=(0.8, 1.1), sink=0.6, foot=6.0)
    for v in range(2):
        paint.scatter(c, sp.bone_pile(c, v), 5, rmax, bog, ground, taken, 48 + v, room=5.0, road_margin=5.0)
    big = sorted(L.POOLS, key=lambda q: -q[2])
    for k, (px, py, pr) in enumerate(big[:3]):
        a = 0.9 + 2.1 * k
        x, y = px + (pr + 9.0) * math.cos(a), py + (pr + 9.0) * math.sin(a)
        if paint.road_clear(c, x, y, 9.0) and taken.clear(x, y, 6.0):
            c.place(sp.stilt_hut(c, k % 2), x, y, ground(x, y) - 0.4, rot=a + math.pi)
            taken.add(x, y, 7.0)
    for k, (px, py, pr) in enumerate(big[:5]):
        a = 2.4 * k + 0.4
        x, y = px + pr * 0.45 * math.cos(a), py + pr * 0.45 * math.sin(a)
        if math.hypot(x - L.PYRAMID[0], y - L.PYRAMID[1]) > 34 and paint.road_clear(c, x, y, 6.0):
            c.place(sp.sunken_timber(c, k % 2), x, y, WATER_Z - 0.3, rot=a * 1.7, role="visual")
    for k, (px, py, pr) in enumerate(big[:2]):
        x, y = px - pr * 0.3, py + pr * 0.35
        c.place(sp.croc(c), x, y, WATER_Z - 0.25, rot=1.1 + 2.0 * k, role="visual")
    torch = sp.torch_post(c)
    for e in entrances(c):
        if e["to"] != "bonebog":
            continue
        for k in range(6):
            q = c.at(e["s"] + 20.0 + 34.0 * k)
            if lobe_at(q.p.x, q.p.y) != "bonebog":
                break
            sd = 1 if k % 2 else -1
            x, y = q.p.x + q.r.x * sd * (q.w / 2 + 6.5), q.p.y + q.r.y * sd * (q.w / 2 + 6.5)
            c.place(torch, x, y, ground(x, y) - 0.2)
            gx, gy, gz = c.game(x, y, ground(x, y) + 3.2)
            c.entity("torch", x=gx, y=gy, z=gz)
    gates(c, ground)
    # Everywhere that isn't the swamp or the volcano's slope: bushes, ferns, flowers.
    def green(x, y):
        return inside(x, y) and lobe_at(x, y) in ("riverbend", "cascade", "camp")

    for v in range(2):
        paint.scatter(c, props.bush(c, v), 90, rmax, green, ground, taken, 50 + v, room=2.5, role="visual", scale=(0.7, 1.5),
                      seat=1.0)
    paint.scatter(c, props.fern(c), 200, rmax, green, ground, taken, 54, room=1.5, role="visual", seat=0.8)
    # (Each set down on the lowest ground under it, its blossoms in the grass: none floating,
    # Blake, Riverbend note 1.)
    paint.scatter(c, props.flowers(c), 180, rmax, lambda x, y: green(x, y) and lobe_at(x, y) != "cascade", ground, taken, 55,
                  room=1.5, role="visual", sink=0.22, seat=1.6)
    if RUIN:
        ruin_kit.char_trees(c, burn, ("Palm", "Jungle Tree", "Grand Tree", "Giant Tree", "Great Tree"), chance=0.85,
                            threshold=0.3)
        ruin.burn_away(c, burn, ("Fern", "Flowers", "Bush", "Big Leaf"), threshold=0.3)
        paint.scatter(c, props.log(c, 0), 40, rmax, inside, ground, taken, 13, room=5.0, role="visual", sink=0.3)


if __name__ == "__main__":
    main()
