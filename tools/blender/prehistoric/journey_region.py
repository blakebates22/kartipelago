# The journeys between the kingdoms: each its own overworld section (Blake, Oct 26: "we hit
# a loading zone, then we go to the connecting segment, and then drive the segment to the
# next loading zone. this will allow us to build more depth and adventure"). Built from
# their layouts (pocket_kit, like the kingdoms' regions): j<id>_layout.py.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/journey_region.py <gorge|pass|dust|cause>
#
#   gorge  the Burnt Gorge: Dinosaur Valley up to the Snow Kingdom
#   pass   the Frozen Pass: the Snow Kingdom down to Desert World
#   dust   the Dust Road: Desert World down to Tropic Isles
#   cause  Tidewyrm's Causeway: Tropic Isles over the sea to the Dragon Kingdom
#
# The route is a loop (the kit's courses are) but the road runs only from the layout's
# START point to its END point: the rest goes round out of sight over the mountains, with no
# road. At each end, the loading zone (regions.ts's passage) and a gate beyond it.

import importlib
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp, smooth  # noqa: E402
import pocket_build as pb  # noqa: E402
from pocket_build import box, cone  # noqa: E402
import region_paint as paint  # noqa: E402
import props  # noqa: E402
import ruin_kit  # noqa: E402
import snow_props as snp  # noqa: E402
import summit_props as smp_  # noqa: E402
import aurora_props as ap  # noqa: E402
import canyon_props as cp  # noqa: E402
import gulch_props as gp  # noqa: E402
import oasis_props as op  # noqa: E402
import beach_props as bp  # noqa: E402
import tropic_props as tp  # noqa: E402
import swamp_props as swp  # noqa: E402
import volcano_props as vp  # noqa: E402
import keep_props as kp  # noqa: E402
import dcanyon_props as dcp  # noqa: E402
import impact_props as ip  # noqa: E402
import villager_homes as vh  # noqa: E402

JID = sys.argv[-1]
J = importlib.import_module("j%s_layout" % JID)
L = J.L
TRACK_ID = "journey_%s" % JID + os.environ.get("KP_REGION_SUFFIX", "")

SPECS = {
    "gorge": {
        "name": "The Burnt Gorge",
        # (v2: clear skies and far horizons, the world opening up: Blake, Oct 31)
        "env": "summit_pass",
        # look: (ground, cliff, road, shoulder)
        "looks": {
            "ember": (("ash_soil", "dirt"), ("ember_rock", "wall"), "basalt_road", ("scorched_ground", "dirt")),
            # (v2, the pilgrimage: the green valley, the cleft, the steppe, the snow)
            "meadow": (("valley_grass", "grass"), ("canyon_rock_moss", "wall"), "valley_road", ("valley_trail", "dirt")),
            "basalt": (("scorched_ground", "dirt"), ("obsidian_cliff", "wall"), "basalt_road", ("ash_soil", "dirt")),
            "steppe": (("thaw_grass", "grass"), ("summit_rock", "wall"), "forest_road", ("valley_trail", "dirt")),
            "snow": (("snow_ground", "deep_snow"), ("frost_cliff", "wall"), "packed_snow_road", ("snow_ground", "deep_snow")),
        },
        "bridge": ("plank_deck", ("weathered_timber", "wall"), ("fence_rail", "wall")),
        "water": ("valley_water", "water"),
        "ends": {"start": ("valley_cliff", "Dinosaur Valley"), "end": ("frost_cliff", "the Snow Kingdom")},
    },
    "pass": {
        "name": "The Frozen Pass",
        "env": "summit_pass",
        "looks": {
            "snow": (("summit_snow", "deep_snow"), ("summit_cliff", "wall"), "summit_road", ("summit_snow", "packed_snow")),
            "glacier": (("rift_snow", "packed_snow"), ("glacier_wall", "wall"), "rift_road", ("rift_snow", "packed_snow")),
            "melt": (("frost_rock", "dirt"), ("frost_cliff", "wall"), "snow_stone_road", ("frost_rock", "dirt")),
            "canyon": (("red_sand", "loose_sand"), ("strata_red", "wall"), "dash_road", ("dash_shoulder", "dirt")),
            "sand": (("pale_sand", "loose_sand"), ("strata_orange", "wall"), "dash_road", ("dash_shoulder", "dirt")),
        },
        "ends": {"start": ("summit_cliff", "the Snow Kingdom"), "end": ("strata_orange", "Desert World")},
    },
    "dust": {
        "name": "The Dust Road",
        "env": "canyon_dash",
        "looks": {
            "dunes": (("gold_sand", "loose_sand"), ("strata_orange", "wall"), "dash_road", ("gold_sand", "loose_sand")),
            "scrub": (("gulch_wash", "dirt"), ("strata_red", "wall"), "dash_road", ("dash_shoulder", "dirt")),
            "ford": (("valley_grass", "grass"), ("jungle_mossstone", "wall"), "jungle_path", ("valley_grass", "dirt")),
            "jungle": (("isle_jungle", "grass"), ("jungle_mossstone", "wall"), "beach_road", ("isle_jungle", "grass")),
        },
        "bridge": ("plank_deck", ("weathered_timber", "wall"), ("fence_rail", "wall")),
        "water": ("valley_water", "water"),
        "ends": {"start": ("strata_orange", "Desert World"), "end": ("isle_rock", "Tropic Isles")},
    },
    "cause": {
        "name": "Tidewyrm's Causeway",
        "env": "dragon_isles",
        "looks": {
            "reef": (("cove_sand", "sand"), ("cove_rock", "wall"), "beach_road", ("cove_sand", "sand")),
            "stacks": (("wet_sand", "sand"), ("isle_rock", "wall"), "beach_road", ("wet_sand", "sand")),
            "isle": (("keep_grass", "grass"), ("isle_rock", "wall"), "keep_path", ("keep_grass", "grass")),
            "strait": (("wet_sand", "sand"), ("keep_rock", "wall"), "keep_cobble", ("wet_sand", "sand")),
            "crags": (("keep_grass", "grass"), ("keep_rock", "wall"), "keep_cobble", ("keep_path", "dirt")),
        },
        "ends": {"start": ("cove_rock", "Tropic Isles"), "end": ("keep_rock", "the Dragon Kingdom")},
    },
}
SP = SPECS[JID]
LOOK = SP["looks"]
WATER_Z = getattr(J, "WATER_Z", -99.0)
SEA = WATER_Z > -50


def natural(x, y):
    h = J.natural(x, y)
    tz = L.tunnel_floor(x, y)
    if tz is not None:
        h = min(h, tz - 0.25)
    bz = L.bridge_floor(x, y)
    if bz is not None:
        h = min(h, bz)
    return h


def classify(c, n, info):
    look = L.look_at(c.x, c.y)
    ground, cliff, _, _ = LOOK[look]
    if n.z < 0.62:
        return cliff
    if SEA:
        if c.z < WATER_Z - 1.0:
            return ("wet_sand", "deep_water")  # (off the causeway into the sea)
        if c.z < WATER_Z + 0.4:
            return ("cove_wet_sand", "water")
    if JID == "gorge" and look == "ember" and math.sin(c.x / 13.0) * math.cos(c.y / 11.0) > 0.55:
        return ("lava_crust", "dirt")
    if JID == "gorge" and L.wall_sd(c.x, c.y) > 20.0:
        # (The ranges beyond the basins, v2b: snow on their heights, more of it northward;
        # their faces the rock of the land below them.)
        snowline = 150.0 - 50.0 * smooth((c.x + c.y + 200.0) / 700.0)
        if c.z > snowline + 6.0 * math.sin(c.x / 23.0) * math.cos(c.y / 19.0):
            return ("snow_ground", "deep_snow") if n.z > 0.55 else ("frost_cliff", "wall")
    if JID == "gorge" and look in ("meadow", "steppe"):
        d, wz = L.water_d(c.x, c.y)
        if d < L.river_hw + 3 and c.z < wz + 0.4:
            return ("valley_sand", "water")  # (the river's bed, wadeable)
        if look == "steppe" and n.z > 0.9 and math.sin(c.x / 19.0) * math.cos(c.y / 15.0 + 0.5) > 0.55:
            return ("snow_ground", "packed_snow")  # (the first frost lying in hollows)
    if JID == "pass" and look == "glacier" and math.sin(c.x / 17.0 + c.y / 23.0) > 0.4:
        return ("glacier_wall", "packed_snow") if n.z < 0.8 else ground
    if JID == "dust" and look == "dunes" and math.sin(c.x / 29.0 + 1.0) * math.cos(c.y / 23.0) > 0.35:
        return ("dune_crest", "loose_sand")
    return ground


def main():
    c = kit.Course(TRACK_ID, SP["name"], SP["env"])
    rp = L.route_points()
    c.route(rp, width=14.0, bank=5.0)
    kinds = {}
    for look, (ground, cliff, road, shoulder) in LOOK.items():
        kinds[look] = {"mat": road, "shoulder": 1.5, "shoulder_mat": shoulder}
    deck, post, rail = SP.get("bridge", ("cove_planks", ("cove_post", "wall"), ("cove_rail", "wall")))
    kinds["bridge"] = {"mat": deck, "surface": "road", "shoulder": 0.6, "shoulder_mat": (deck, "road"), "barrier": 1.0,
                       "barrier_mat": rail, "deck": 1.8, "deck_mat": post, "ground": False}
    if JID == "cause":
        kinds["bridge"] = {"mat": "beach_road", "surface": "road", "shoulder": 0.6, "shoulder_mat": ("isle_rock", "road"),
                           "barrier": 0.7, "barrier_mat": ("isle_rock", "wall"), "deck": 2.4,
                           "deck_mat": ("isle_rock", "wall"), "ground": False}
    c.kinds = kinds
    s_start = c.nearest(*J.ROUTE[J.START][:2])[0].s
    s_end = c.nearest(*J.ROUTE[J.END][:2])[0].s

    arch = [pb.tunnel_span(c, L, a, b) for name, kind, a, b in L.tunnels if JID == "gorge" and name == "Snow Arch"]

    def label(q):
        if not s_start <= q.s <= s_end:
            return None  # (no road: the way round out of sight)
        if arch and arch[0][0] - 12.0 <= q.s <= arch[0][1] + 4.0:
            return "snow"  # (snow from the Snow Arch's mouth: Blake, Oct 31)
        if L.tunnel_floor(q.p.x, q.p.y) is not None and L.wall_sd(q.p.x, q.p.y) > -6:
            lk = L.look_at(q.p.x, q.p.y)
            if JID == "gorge" and lk in ("steppe", "snow"):
                return "snow"  # (the Snow Arch's road is snow already: Blake, Oct 31)
            return lk
        d, wz = L.water_d(q.p.x, q.p.y)
        if d < L.river_hw + 4 and q.p.z > wz + 0.9:
            return "bridge"
        if SEA and J.natural(q.p.x, q.p.y) < q.p.z - 1.2:
            return "bridge"  # (the causeway over the sea)
        return L.look_at(q.p.x, q.p.y)

    specials = [(s0, s1, k) for s0, s1, k in kit.runs(c, label)]
    c.roads(kit.plan(c, specials, next(iter(LOOK)), max_len=160.0))

    X0, X1, Y0, Y1 = -490, 490, -490, 490
    ter = c.terrain(SP["name"], X0, X1, Y0, Y1, 5.0, natural, classify, near=8.0, fade=16.0)
    first = next(iter(LOOK.values()))
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 5.0, lambda x, y: natural(x, y) - 0.5, c.lib(*first[0]))

    def ground(x, y):
        z = c.ground_z(x, y, [ter])
        return natural(x, y) if z is None else z

    def on_road(s):
        return s_start + 2.0 <= s <= s_end - 2.0

    water(c)
    if SEA:
        c.disc("Sea", 0.0, 0.0, 1600.0, WATER_Z, c.lib("sea_water", "water"), role="visual", n=64)
    thresholds(c, ground)
    ends(c, ground)
    # Travellers on the road between the kingdoms: a camp in each part of it.
    vh.homes(c, L, ground, "road", camp, per=1, avoid=[(e[0][0], e[0][1], 30.0) for e in J.ENDS.values()], n=(1, 2))
    taken = paint.Taken([(e[0][0], e[0][1], 22.0) for e in J.ENDS.values()])
    DRESS[JID](c, ground, taken, on_road)

    gts = c.checkpoints(height=10.0)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish(extra={"race": {"laps": 1}, "journey": {"from": round(s_start, 1), "to": round(s_end, 1)}})
    print("road %.0f m (s %.0f..%.0f), loop %.0f, gates %d" % (s_end - s_start, s_start, s_end, c.length, len(gts)))
    for name, (zone, beyond) in J.ENDS.items():
        g = c.game(zone[0], zone[1], 0.0)
        q, _ = c.nearest(*zone)
        # (The way into the journey from this end: facing along the road, away from the gate.)
        tx, ty = (q.t.x, q.t.y) if name == "start" else (-q.t.x, -q.t.y)
        print("passage %s: x %.1f z %.1f heading %.4f" % (name, g[0], g[2], math.atan2(tx, -ty)))  # (game heading: z is -y)


def water(c):
    """The rivers (Frost Creek frozen over; the Ford's water) and the gorge's lava pools."""
    for j, riv in enumerate(L.rivers):
        strip = []
        for (ax, ay, az), (bx, by, bz) in zip(riv, riv[1:]):
            n = max(1, int(math.hypot(bx - ax, by - ay) / 6))
            for k in range(n):
                t = k / n
                strip.append((lerp(ax, bx, t), lerp(ay, by, t), 2 * L.river_hw + 8, lerp(az, bz, t) - 0.1))
        strip.append((riv[-1][0], riv[-1][1], 2 * L.river_hw + 8, riv[-1][2] - 0.1))
        mat, surface = SP.get("water", ("valley_water", "water"))
        c.ribbon("River %d" % j, strip, 2 * L.river_hw + 8, 0, c.lib(mat, surface), role="both" if surface == "ice" else "visual",
                 steps=4)
    for k, (lx, ly, lr) in enumerate(J.LAVA):
        z = J.natural(lx, ly) + 1.2
        c.disc("Lava Pool %d" % k, lx, ly, lr + 3.0, z, c.lib("volcano_lava", "lava"), n=24, wobble=0.15, seed=k)
        g = c.game(lx, ly, z)
        c.entity("bubbles", x=g[0], y=g[1], z=g[2], r=lr, molten=True)


def thresholds(c, ground):
    for name, kind, a, b in L.tunnels:
        s0, s1 = pb.tunnel_span(c, L, a, b)
        if kind == "lava":  # the Ash Tube: a lava tube, glowing seams down its walls
            half = pb.bore(c, L, name, s0, s1, ("obsidian_cliff", "wall"), ("ash_soil", "dirt"), height=11.0)
            s = s0 + 3.0
            k = 0
            while s < s1 - 2.0:
                q = c.at(s)
                for sd in (-1, 1):
                    strip = [(q.p.x + q.r.x * sd * (half - 0.4) + q.t.x * u, q.p.y + q.r.y * sd * (half - 0.4) + q.t.y * u)
                             for u in (-2.0, 2.0)]
                    c.ribbon("%s Seam %d %d" % (name, k, sd), strip, 0.8, q.p.z + 0.2 + 0.4 * (k % 3),
                             c.lib("volcano_lava", "lava"), role="visual")
                if k % 2 == 0:
                    g = c.game(q.p.x + q.r.x * (half - 0.6), q.p.y + q.r.y * (half - 0.6), q.p.z + 4.0)
                    c.entity("torch", x=g[0], y=g[1], z=g[2])
                s += 7.0
                k += 1
            for s in (s0 - 4.0, s1 + 4.0):
                q = c.at(s)
                g = c.game(q.p.x, q.p.y, q.p.z + 12.0)
                c.entity("steam", x=g[0], y=g[1], z=g[2])
        elif kind == "ice":  # the Snow Arch / the Ice Cave: bored through blue ice
            # (The Burnt Gorge's Snow Arch in Aurora's clear mirror ice, v2c: Blake, "can we
            # make it out of the mirror material transparent lake we see in aurora".)
            wall = ("mirror_ice", "wall") if JID == "gorge" else ("glacier_wall", "wall")
            half = pb.bore(c, L, name, s0, s1, wall, ("snow_ground", "deep_snow"), height=12.0)
            s = s0 + 4.0
            k = 0
            while s < s1 - 3.0:
                q = c.at(s)
                c.place(snp.icicles(c, length=4.0 + 2.0 * (k % 2), variant=k % 2), q.p.x + q.r.x * (half - 3.0),
                        q.p.y + q.r.y * (half - 3.0), q.p.z + 11.0, rot=k * 0.9, role="visual")
                if k % 2 == 0:
                    g = c.game(q.p.x - q.r.x * (half - 0.6), q.p.y - q.r.y * (half - 0.6), q.p.z + 4.0)
                    c.entity("lantern", x=g[0], y=g[1], z=g[2])
                s += 8.0
                k += 1
        elif kind == "mesa":  # the Mesa Tunnel: timber-shored through a red mesa
            half = pb.bore(c, L, name, s0, s1, ("strata_red", "wall"), ("red_sand", "loose_sand"), height=11.0)
            sets = gp.timber_set(c, half=half - 0.4, height=10.4)
            s = s0 + 2.0
            k = 0
            while s < s1 - 1.0:
                q = c.at(s)
                c.place(sets, q.p.x, q.p.y, q.p.z - 0.3, rot=math.atan2(q.t.y, q.t.x) - math.pi / 2, role="visual")
                if k % 2 == 0:
                    g = c.game(q.p.x + q.r.x * (half - 1.0), q.p.y + q.r.y * (half - 1.0), q.p.z + 6.0)
                    c.entity("torch", x=g[0], y=g[1], z=g[2])
                s += 8.0
                k += 1
        elif kind == "vine":  # the Vine Gorge: roots and vines hanging
            half = pb.bore(c, L, name, s0, s1, ("jungle_mossstone", "wall"), ("isle_jungle", "grass"), height=11.0)
            vines = [swp.hanging_vine(c, v, length=6.0 + 2.0 * v) for v in range(2)] + [swp.moss_beard(c, 0)]
            s = s0 + 3.0
            k = 0
            while s < s1 - 2.0:
                q = c.at(s)
                for sd in (-1, 1):
                    x, y = q.p.x + q.r.x * sd * (half - 2.0), q.p.y + q.r.y * sd * (half - 2.0)
                    c.place(vines[(k + (sd > 0)) % 3], x, y, q.p.z + 9.5, rot=k * 1.3, role="visual")
                if k % 2 == 0:
                    g = c.game(q.p.x + q.r.x * (half - 0.6), q.p.y + q.r.y * (half - 0.6), q.p.z + 4.0)
                    c.entity("torch", x=g[0], y=g[1], z=g[2])
                s += 6.0
                k += 1
        else:  # the Sea Cave
            half = pb.bore(c, L, name, s0, s1, ("cove_rock", "wall"), ("cove_grass", "grass"), height=12.0)
            for k in range(3):
                q = c.at(s0 + (s1 - s0) * (k + 0.5) / 3)
                g = c.game(q.p.x + q.r.x * (half - 0.6), q.p.y + q.r.y * (half - 0.6), q.p.z + 4.0)
                c.entity("torch", x=g[0], y=g[1], z=g[2])


def ends(c, ground):
    """Each end's gate: a great arch over the road's end, a wall of the next kingdom's rock
    beyond it (the loading zone is just before the arch)."""
    for name, (zone, beyond) in J.ENDS.items():
        mat, _ = SP["ends"][name]
        q, _ = c.nearest(*zone)
        ux, uy = beyond[0] - zone[0], beyond[1] - zone[1]
        d = math.hypot(ux, uy) or 1.0
        ux, uy = ux / d, uy / d
        rot = math.atan2(uy, ux)
        z = q.p.z
        gx, gy = zone[0] + ux * 10.0, zone[1] + uy * 10.0
        for sd in (-1, 1):
            px, py = gx - uy * sd * 11.0, gy + ux * sd * 11.0
            box(c, "%s Gate Pier %d" % (name.title(), sd), px, py, 2.2, 2.2, z - 3.0, z + 16.0, (mat, "wall"), rot=rot)
            g = c.game(px - ux * 2.6, py - uy * 2.6, z + 6.0)
            c.entity("torch", x=g[0], y=g[1], z=g[2])
        box(c, "%s Gate Lintel" % name.title(), gx, gy, 2.4, 13.4, z + 14.0, z + 18.0, (mat, "wall"), rot=rot, role="visual")
        # Beyond: the next kingdom's rock (the road goes no further; the zone takes you on).
        bx, by = zone[0] + ux * 22.0, zone[1] + uy * 22.0
        box(c, "%s End Wall" % name.title(), bx, by, 4.0, 22.0, z - 6.0, z + 40.0, (mat, "wall"), rot=rot)
        box(c, "%s End Floor" % name.title(), zone[0] + ux * 12.0, zone[1] + uy * 12.0, 12.0, 12.0, z - 6.0, z - 0.15,
            (LOOK[L.look_at(*zone)][2], "road"), rot=rot)


# ---------------------------------------------------------------- the dressing


def camp(c, name, x, y, z, rot, k):
    """A travellers' camp: a tent, its fire."""
    c.place(ip.tent(c, k % 2), x, y, z - 0.1, rot=rot, name=name)
    fx, fy = x - math.sin(rot) * 0.0 + math.cos(rot - math.pi / 2) * 4.0, y + math.sin(rot - math.pi / 2) * 4.0
    g = c.game(fx, fy, z + 0.2)
    c.entity("campfire", x=g[0], y=g[1], z=g[2])


def _scatter_look(c, ground, taken, look, items):
    def ok(x, y):
        return L.wall_sd(x, y) < -8 and L.look_at(x, y) == look

    for k, (proto, n, kw) in enumerate(items):
        paint.scatter(c, proto, n, 480.0, ok, ground, taken, 100 + 7 * k + len(look), **kw)


def dress_gorge(c, ground, taken, on_road):
    """The pilgrimage (jgorge_layout v2): the burnt narrows; the Long Meadow green and
    alive, herds grazing, the falls, the traders' camp by the ford; the steppe's basalt,
    hot springs, prayer flags and the herders' village, mammoths on its grass; the
    Snowgate's pines and the pilgrims' hostel; the Snow Kingdom's peaks ahead."""
    import valley_village as vv

    vv.GROUND = ground
    tree = dict(room=5.0, road_margin=6.0, trunk=(0.6, 6.0))
    _scatter_look(c, ground, taken, "ember", [
        (props.jungle_tree(c, 0), 8, tree), (props.jungle_tree(c, 1), 6, tree),
        (props.basalt_columns(c), 5, dict(room=6.0, road_margin=6.0)),
        (vp.obsidian_cluster(c, 0), 5, dict(room=5.0, road_margin=6.0)),
        (props.boulder(c, "volcano_basalt", 1), 8, dict(room=4.0, road_margin=6.0, scale=(1.0, 2.0))),
    ])
    ruin_kit.char_trees(c, lambda x, y: 1.0 if L.look_at(x, y) == "ember" else 0.0, ("Jungle Tree",), chance=0.9,
                        threshold=0.5)
    for k, q in enumerate(c.S[::60]):
        if on_road(q.s) and L.look_at(q.p.x, q.p.y) == "ember":
            sd = 1 if k % 2 else -1
            x, y = q.p.x + q.r.x * sd * 12.0, q.p.y + q.r.y * sd * 12.0
            g = c.game(x, y, ground(x, y) + 0.5)
            c.entity("steam", x=g[0], y=g[1], z=g[2])
    # ---- The Long Meadow.
    _scatter_look(c, ground, taken, "meadow", [
        (smp_.broadleaf(c, 0, frosted=False), 34, tree), (smp_.broadleaf(c, 1, frosted=False), 28, tree),
        (ip.cycad(c, 0), 18, dict(room=4.0, road_margin=5.0)), (ip.tree_fern(c, 1), 18, dict(room=4.0, road_margin=5.0)),
        (smp_.pine(c, 1, 14.0, snowy=False), 20, tree),
        (smp_.shrub(c, 0, frosted=False), 70, dict(room=2.0, road_margin=3.0, role="visual", scale=(0.7, 1.5))),
        (ip.horsetails(c, 0), 30, dict(room=2.0, road_margin=4.0, role="visual")),
        (props.boulder(c, "valley_cliff", 0), 10, dict(room=4.0, road_margin=6.0, scale=(1.0, 2.2))),
    ])
    # Forested hills round it (v2b): pines and broadleaves up the ranges' lower slopes.
    def hills(x, y):
        b = L.wall_sd(x, y)
        return 6.0 < b < 70.0 and L.look_at(x, y) == "meadow" and J.natural(x, y) < 120.0

    for v, (proto, n) in enumerate(((smp_.pine(c, 0, 16.0, snowy=False), 70), (smp_.pine(c, 2, 20.0, snowy=False), 50),
                                    (smp_.broadleaf(c, 0, frosted=False), 40))):
        paint.scatter(c, proto, n, 480.0, hills, ground, taken, 300 + v, room=5.0, road_margin=10.0, role="visual",
                      scale=(0.9, 1.5))
    # The falls off the steppe's edge into the meadow's north.
    fx, fy = J.FALLS
    top = J.natural(fx, fy + 16.0)
    foot = L.rivers[0][0][2]
    props.falls(c, "Meadow Falls", fx, fy + 10.0, top, foot, 14.0, 20.0, facing=-1, throw=7.0, bulge=1.6, veils=3)
    g = c.game(fx, fy + 2.0, foot)
    c.entity("waterfall", x=g[0], y=g[1], z=g[2], top=round(top - foot, 1), width=18.0, heading=0.0)
    # Herds of long-necks grazing, on two rounds.
    for k, (cx, cy, rx, ry, n) in enumerate(((-120.0, -100.0, 50.0, 30.0, 3), (-80.0, 60.0, 40.0, 26.0, 2))):
        pts = []
        for j in range(16):
            a = j * math.tau / 16
            x, y = cx + rx * math.cos(a) + 4.0 * math.sin(3 * a), cy + ry * math.sin(a)
            pts.append((x, y, ground(x, y)))
        c.path_curve("Meadow Herd %d" % k, pts, closed=True)
        for j in range(n):
            c.entity("dinosaur", route="Meadow Herd %d" % k, speed=1.4, scale=(1.0, 0.6, 0.85)[j], start=j * 9.0)
    # The traders' camp by the ford (v2b, Blake: "lets add more to the hostels and traders
    # camps"): tents in a ring round the fire, market stalls along the road, covered
    # wagons and their goods, a jetty on the river with canoes, fish drying on racks,
    # lanterns on posts, their folk at the stalls.
    tx, ty, tr = J.VILLAGES["traders"]

    def put(proto, x, y, rot, r, coll="Village", role="both", sink=0.1):
        if not paint.road_clear(c, x, y, r) or not taken.clear(x, y, r):
            return False
        d, _wz = L.water_d(x, y)
        if d < L.river_hw + 1.0:
            return False
        c.place(proto, x, y, ground(x, y) - sink, rot=rot, coll=coll, role=role)
        taken.add(x, y, r)
        return True

    for k in range(6):
        a = k * math.tau / 6 + 0.2
        put(ip.tent(c, k % 2), tx + tr * 0.75 * math.cos(a), ty + tr * 0.75 * math.sin(a), a + math.pi / 2, 4.0)
    g = c.game(tx, ty, ground(tx, ty) + 0.2)
    c.entity("campfire", x=g[0], y=g[1], z=g[2])
    q, _ = c.nearest(tx, ty)
    side = 1.0 if (tx - q.p.x) * q.r.x + (ty - q.p.y) * q.r.y > 0 else -1.0
    rot = math.atan2(q.t.y, q.t.x)
    for k in range(4):  # (stalls along the road's camp side, facing it)
        along = (k - 1.5) * 9.0
        x = q.p.x + q.t.x * along + q.r.x * side * (q.w / 2 + 5.0)
        y = q.p.y + q.t.y * along + q.r.y * side * (q.w / 2 + 5.0)
        if put(op.market_stall(c, k % 3), x, y, rot + (math.pi if side > 0 else 0.0) - math.pi / 2, 3.2):
            gx_, gy_, gz_ = c.game(x, y, ground(x, y) + 3.0)
            c.entity("lantern", x=gx_, y=gy_, z=gz_)
    for k, (dx, dy) in enumerate(((-14.0, 12.0), (12.0, 16.0), (-18.0, -8.0))):
        put(gp.wagon(c, covered=True), tx + dx, ty + dy, 0.6 * k + 0.4, 4.5)
        for j in range(2):
            put(gp.barrel(c, j) if j else gp.crate_stack(c, k % 2), tx + dx + 3.5 + 1.4 * j, ty + dy - 2.5, 0.3 * j, 1.2)
    put(op.crates(c, 0), tx - 4.0, ty - 13.0, 0.4, 2.0)
    for k in range(3):
        put(gp.lantern_post(c), tx + 16.0 * math.cos(k * 2.1 + 1.0), ty + 16.0 * math.sin(k * 2.1 + 1.0), 0.0, 1.0)
    # The jetty: planks out over the river's edge on posts, canoes moored at it.
    riv = L.rivers[0]
    best = min(((math.hypot(px - tx, py - ty), (px, py, pz)) for px, py, pz in riv), key=lambda t: t[0])[1]
    jx, jy, jz = best
    ang = math.atan2(jy - ty, jx - tx)
    for k in range(6):
        px, py = tx + math.cos(ang) * (tr + k * 2.4), ty + math.sin(ang) * (tr + k * 2.4)
        box(c, "Jetty Deck %d" % k, px, py, 1.2, 2.2, jz + 0.4, jz + 0.65, ("plank_deck", "road"), rot=ang, role="visual")
        if k % 2 == 1:
            for sd in (-1, 1):
                ox, oy = px - math.sin(ang) * sd * 2.0, py + math.cos(ang) * sd * 2.0
                box(c, "Jetty Post %d %d" % (k, sd), ox, oy, 0.18, 0.18, jz - 1.5, jz + 1.4, ("weathered_timber", "wall"), role="visual")
    for k in range(3):
        px = tx + math.cos(ang) * (tr + 4.0 + 4.0 * k) - math.sin(ang) * 3.4
        py = ty + math.sin(ang) * (tr + 4.0 + 4.0 * k) + math.cos(ang) * 3.4
        c.place(op.moored_boat(c, k % 2), px, py, jz - 0.1, rot=ang + 0.1 * k, coll="Props", role="visual")
    # Fish drying on racks: two rails on posts, the catch hung along them.
    for k in range(2):
        rx_, ry_ = tx - 10.0 + 4.0 * k, ty + 14.0 - 2.0 * k
        if paint.road_clear(c, rx_, ry_, 2.5) and taken.clear(rx_, ry_, 2.5):
            z = ground(rx_, ry_)
            for sd in (-1, 1):
                box(c, "Fish Rack Post %d %d" % (k, sd), rx_ + sd * 1.8, ry_, 0.12, 0.12, z - 0.3, z + 2.2, ("weathered_timber", "wall"),
                    role="visual")
            box(c, "Fish Rack Rail %d" % k, rx_, ry_, 2.0, 0.08, z + 2.05, z + 2.15, ("weathered_timber", "wall"), role="visual")
            for j in range(6):
                box(c, "Fish %d %d" % (k, j), rx_ - 1.5 + 0.6 * j, ry_, 0.12, 0.05, z + 1.4, z + 2.0, ("crystal_teal", "wall"), role="visual")
            taken.add(rx_, ry_, 2.5)
    g = c.game(tx + 4.0, ty - 4.0, ground(tx, ty))
    c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=16.0, n=7, folk="road", heading=0.0)
    # Two more little villages in the meadow (v2c, Blake): Fallsfoot, the fishers at the
    # falls' foot (huts round a hearth, boats drawn up, fish drying); and the hamlet on the
    # south side, farmers (huts, a fenced paddock, hay, a trough and a well).
    def village(key, huts, folk_n):
        vx_, vy_, vr_ = J.VILLAGES[key]
        placed = 0
        for k in range(huts):
            a = k * math.tau / huts + 0.5
            x, y = vx_ + vr_ * 0.7 * math.cos(a), vy_ + vr_ * 0.7 * math.sin(a)
            if L.water_d(x, y)[0] < L.river_hw + 3.0 or not paint.road_clear(c, x, y, 6.0) or not taken.clear(x, y, 4.5):
                continue
            ring = [ground(x + 4.0 * math.cos(t), y + 4.0 * math.sin(t)) for t in (0.0, 1.57, 3.14, 4.71)]
            vv.place_hut(c, k + 1, x, y, min(ring) - 0.05, a + math.pi, scale=0.9)
            taken.add(x, y, 5.5)
            placed += 1
        g = c.game(vx_, vy_, ground(vx_, vy_) + 0.2)
        c.entity("campfire", x=g[0], y=g[1], z=g[2])
        c.place(vv.hearth(c), vx_, vy_, ground(vx_, vy_) - 0.05, coll="Props")
        taken.add(vx_, vy_, 3.0)
        g = c.game(vx_ + 3.0, vy_ - 3.0, ground(vx_, vy_))
        c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=vr_, n=folk_n, folk="valley", heading=0.0)
        return vx_, vy_, vr_

    fx_, fy_, fr_ = village("fallsfoot", 5, 4)
    for k in range(3):  # (their boats, drawn up toward the river)
        a = math.atan2(J.FALLS[1] - fy_, J.FALLS[0] - fx_) + (k - 1) * 0.35
        x, y = fx_ + (fr_ + 4.0) * math.cos(a), fy_ + (fr_ + 4.0) * math.sin(a)
        if L.water_d(x, y)[0] > L.river_hw and taken.clear(x, y, 2.0):
            c.place(kp.boat(c, k % 2), x, y, ground(x, y) - 0.15, rot=a, coll="Props", role="visual")
            taken.add(x, y, 2.0)
    for k in range(2):
        rx_, ry_ = fx_ - fr_ + 2.0, fy_ - 4.0 + 6.0 * k
        if taken.clear(rx_, ry_, 2.5):
            z = ground(rx_, ry_)
            for sd in (-1, 1):
                box(c, "Falls Rack Post %d %d" % (k, sd), rx_, ry_ + sd * 1.8, 0.12, 0.12, z - 0.3, z + 2.2, ("weathered_timber", "wall"),
                    role="visual")
            box(c, "Falls Rack Rail %d" % k, rx_, ry_, 0.08, 2.0, z + 2.05, z + 2.15, ("weathered_timber", "wall"), role="visual")
            for j in range(6):
                box(c, "Falls Fish %d %d" % (k, j), rx_, ry_ - 1.5 + 0.6 * j, 0.05, 0.12, z + 1.4, z + 2.0, ("crystal_teal", "wall"),
                    role="visual")
            taken.add(rx_, ry_, 2.5)
    hx_, hy_, hr_ = village("hamlet", 5, 4)
    # Their paddock: a timber fence round a square of trampled ground, a trough, hay.
    px_, py_ = hx_ + hr_ + 10.0, hy_ - 4.0
    pz = ground(px_, py_)
    for k in range(12):
        side, t = divmod(k, 3)
        u = (t - 1) * 5.0
        ox, oy = ((u, -8.0), (8.0, u), (-u, 8.0), (-8.0, -u))[side]
        rot = (0.0, math.pi / 2, 0.0, math.pi / 2)[side]
        if side == 3 and t == 1:
            continue  # (its gate's gap, toward the huts)
        x, y = px_ + ox, py_ + oy
        box(c, "Paddock Rail %d" % k, x, y, 2.5 if rot == 0.0 else 0.08, 0.08 if rot == 0.0 else 2.5, ground(x, y) + 0.9,
            ground(x, y) + 1.05, ("fence_rail", "wall"), role="visual")
        box(c, "Paddock Post %d" % k, x, y, 0.12, 0.12, ground(x, y) - 0.3, ground(x, y) + 1.3, ("weathered_timber", "wall"))
    c.place(gp.trough(c), px_, py_ + 3.0, pz - 0.05, coll="Props")
    for k, (dx, dy) in enumerate(((-3.0, -3.0), (2.5, -4.0), (4.0, 2.0))):
        x, y = px_ + dx, py_ + dy
        hz = ground(x, y)
        cone(c, "Haystack %d" % k, x, y, 1.6, hz - 0.2, 2.4, ("dry_grass", "wall"), segs=8)
    taken.add(px_, py_, 9.0)
    wx_, wy_ = hx_ - hr_ * 0.2, hy_ + hr_ * 0.45
    c.place(vv.well(c), wx_, wy_, ground(wx_, wy_) - 0.1, coll="Props")
    taken.add(wx_, wy_, 2.5)
    pts = []
    for j in range(12):
        a = j * math.tau / 12
        x, y = px_ + 5.0 * math.cos(a), py_ + 5.0 * math.sin(a)
        pts.append((x, y, ground(x, y)))
    c.path_curve("Paddock Round", pts, closed=True)
    c.entity("dinosaur", route="Paddock Round", speed=0.9, scale=0.35, start=0.0)
    # The stone arch over the cleft's mouth.
    ax, ay = J.ARCH
    q, _ = c.nearest(ax, ay)
    c.place(kp.stone_arch(c, span=q.w + 16.0, h=24.0, depth=7.0), q.p.x, q.p.y, q.p.z - 1.0,
            rot=math.atan2(q.t.y, q.t.x) - math.pi / 2, coll="Props")
    # ---- The High Steppe.
    _scatter_look(c, ground, taken, "steppe", [
        (props.basalt_columns(c), 14, dict(room=6.0, road_margin=6.0)),
        (smp_.pine(c, 0, 13.0, snowy=False), 24, tree), (smp_.pine(c, 2, 16.0, snowy=True), 14, tree),
        (smp_.broadleaf(c, 1, frosted=True), 10, tree),
        (smp_.shrub(c, 1, frosted=False), 40, dict(room=2.0, road_margin=3.0, role="visual", scale=(0.7, 1.4))),
        (smp_.boulder(c, 1), 12, dict(room=4.0, road_margin=6.0)),
    ])
    for k, (x, y) in enumerate(((150.0, 236.0), (214.0, 176.0), (100.0, 186.0), (230.0, 230.0))):
        if not paint.road_clear(c, x, y, 9.0) or not taken.clear(x, y, 7.0):
            continue
        z = ground(x, y)
        c.place(smp_.geyser_cone(c, 1 + k % 2), x, y, z - 0.3, rot=k, coll="Props")
        g = c.game(x, y, z + 2.6)
        c.entity("geyser", x=g[0], y=g[1], z=g[2], r=3.5, height=16.0 + 4 * (k % 2), period=8.0 + k, offset=1.7 * k,
                 warn=1.4, blast=2.2, launch=0.0)
        taken.add(x, y, 7.0)
    flags = smp_.Bunting()
    hx, hy, hr = J.VILLAGES["herders"]
    poles = []
    for k in range(5):
        a = k * math.tau / 5 + 0.3
        x, y = hx + hr * math.cos(a), hy + hr * math.sin(a)
        z = ground(x, y)
        c.place(smp_.flag_pole(c, 8.0), x, y, z - 0.2, coll="Props")
        poles.append((x, y, z + 7.6))
    for a, b in zip(poles, poles[1:] + poles[:1]):
        flags.line(a, b, sag=1.6)
    # The herders' huts round their fire, their mammoths on the grass beyond.
    for k in range(4):
        a = k * math.tau / 4 + 0.9
        x, y = hx + hr * 0.55 * math.cos(a), hy + hr * 0.55 * math.sin(a)
        if paint.road_clear(c, x, y, 6.0):
            vv.place_hut(c, k + 1, x, y, ground(x, y) - 0.05, a + math.pi, scale=0.9)
            taken.add(x, y, 6.0)
    g = c.game(hx, hy, ground(hx, hy) + 0.2)
    c.entity("campfire", x=g[0], y=g[1], z=g[2])
    g = c.game(hx + 5.0, hy - 5.0, ground(hx, hy))
    c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=14.0, n=4, folk="valley", heading=0.0)
    pts = []
    for j in range(16):
        a = j * math.tau / 16
        x, y = 150.0 + 36.0 * math.cos(a), 200.0 + 20.0 * math.sin(a)
        pts.append((x, y, ground(x, y)))
    c.path_curve("Steppe Herd", pts, closed=True)
    for j, sc in enumerate((1.0, 0.6, 0.9)):
        c.entity("dinosaur", route="Steppe Herd", speed=1.3, scale=sc, model="mammoth", start=j * 10.0)
    # ---- The Snowgate.
    _scatter_look(c, ground, taken, "snow", [
        (snp.snow_pine(c, 1), 16, tree), (snp.snow_pine(c, 3), 12, tree),
        (snp.ice_spike(c, 0), 6, dict(room=5.0, road_margin=7.0)),
        (snp.snow_mound(c, 0), 8, dict(room=4.0, road_margin=5.0, role="visual")),
    ])
    # The pilgrims' hostel (v2b): a walled courtyard in the bay off the road, its gate to
    # the road, the great lodge across the yard, a stable lean-to with sledges, braziers at
    # the gate, prayer flags over the yard, a well, benches, the pilgrims about the fire.
    import ice_yard

    hx, hy, hr = J.VILLAGES["hostel"]
    q, _ = c.nearest(hx, hy)
    face = math.atan2(q.p.y - hy, q.p.x - hx)  # (from the yard to the road)
    cf, sf = math.cos(face), math.sin(face)
    zy = min(ground(hx + hr * 0.7 * math.cos(t), hy + hr * 0.7 * math.sin(t)) for t in [j * math.tau / 8 for j in range(8)])
    kp.use_palette({})
    wall = kp.curtain_wall(c, length=6.0, h=3.2, thick=1.2)
    for j in range(14):
        a = face + math.pi / 8 + j * (math.tau - math.pi / 4) / 13
        x, y = hx + hr * math.cos(a), hy + hr * math.sin(a)
        c.place(wall, x, y, ground(x, y) - 0.4, rot=a + math.pi / 2, coll="Village")
    for sd in (-1, 1):  # (the gate's piers and braziers)
        a = face + sd * math.pi / 8
        x, y = hx + hr * math.cos(a), hy + hr * math.sin(a)
        box(c, "Hostel Gate Pier %d" % sd, x, y, 0.9, 0.9, ground(x, y) - 0.5, ground(x, y) + 5.0, ("frost_stone", "wall"))
        bx, by = x + cf * 2.0, y + sf * 2.0
        c.place(kp.brazier(c), bx, by, ground(bx, by) - 0.1, coll="Props")
        g = c.game(bx, by, ground(bx, by) + 2.8)
        c.entity("torch", x=g[0], y=g[1], z=g[2])
    # The lodge across the yard, its door to the gate; a second house beside it.
    lx, ly = hx - cf * hr * 0.55, hy - sf * hr * 0.55
    c.place(kp.house(c, 1), lx, ly, zy - 0.1, rot=face - math.pi / 2, scale=1.7, coll="Village")
    l2x, l2y = lx - sf * 10.5, ly + cf * 10.5
    c.place(kp.house(c, 2), l2x, l2y, ground(l2x, l2y) - 0.1, rot=face - math.pi / 2, scale=1.2, coll="Village")
    g = c.game(lx, ly, zy + 13.0)
    c.entity("chimney", x=g[0], y=g[1], z=g[2])
    # The stable lean-to on the yard's other side, sledges in it.
    sx_, sy_ = hx + sf * hr * 0.55 - cf * 2.0, hy - cf * hr * 0.55 - sf * 2.0
    box(c, "Hostel Stable Roof", sx_, sy_, 5.0, 2.6, zy + 3.6, zy + 3.9, ("weathered_timber", "wall"), rot=face, role="visual")
    for j in (-1, 1):
        for k in (-1, 1):
            px, py = sx_ + cf * j * 4.6 - sf * k * 2.2, sy_ + sf * j * 4.6 + cf * k * 2.2
            box(c, "Hostel Stable Post %d %d" % (j, k), px, py, 0.15, 0.15, zy - 0.3, zy + 3.7, ("timber_beam", "wall"))
    c.place(ice_yard.sledge(c, 0), sx_ - cf * 1.5, sy_ - sf * 1.5, zy, rot=face, coll="Props")
    c.place(ice_yard.sledge(c, 1), sx_ + cf * 2.0, sy_ + sf * 2.0, zy, rot=face + 0.1, coll="Props")
    # The yard: its fire, benches, a well, flags strung over it.
    g = c.game(hx, hy, zy + 0.2)
    c.entity("campfire", x=g[0], y=g[1], z=g[2])
    for k in range(3):
        a = face + 1.3 + k * 1.6
        c.place(gp.bench(c), hx + 3.2 * math.cos(a), hy + 3.2 * math.sin(a), zy - 0.05, rot=a + math.pi / 2, coll="Props")
    wx, wy = hx + sf * 6.0 + cf * 4.0, hy - cf * 6.0 + sf * 4.0
    import valley_village as vv

    vv.GROUND = ground
    c.place(vv.well(c), wx, wy, ground(wx, wy) - 0.1, coll="Props")
    hflags = smp_.Bunting()
    tops = []
    for k in range(4):
        a = face + math.pi / 4 + k * math.pi / 2
        x, y = hx + hr * 0.85 * math.cos(a), hy + hr * 0.85 * math.sin(a)
        c.place(smp_.flag_pole(c, 7.0), x, y, ground(x, y) - 0.2, coll="Props")
        tops.append((x, y, ground(x, y) + 6.6))
    for k in range(4):
        hflags.line(tops[k], tops[(k + 2) % 4] if k < 2 else tops[(k + 1) % 4], sag=1.2)
    hflags.build(c, "Hostel Flags")
    g = c.game(hx + 2.0, hy + 2.0, zy)
    c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=hr - 2.0, n=5, folk="snow", heading=0.0)
    # The pilgrims' camp in its bay in the spur (v2c): tents round a fire, a cairn shrine
    # under prayer flags with lanterns about it, a standing stone, pilgrims resting.
    cx_, cy_, cr_ = J.VILLAGES["camp"]
    cz_ = ground(cx_, cy_)
    q, _ = c.nearest(cx_, cy_)
    toward = math.atan2(q.p.y - cy_, q.p.x - cx_)
    for k in range(4):
        a = toward + math.pi / 2 + k * (math.pi / 3.2)
        x, y = cx_ + cr_ * 0.75 * math.cos(a), cy_ + cr_ * 0.75 * math.sin(a)
        c.place(ip.tent(c, k % 2), x, y, ground(x, y) - 0.1, rot=a + math.pi / 2, coll="Village")
    g = c.game(cx_, cy_, cz_ + 0.2)
    c.entity("campfire", x=g[0], y=g[1], z=g[2])
    sx2, sy2 = cx_ - math.cos(toward) * cr_ * 0.7, cy_ - math.sin(toward) * cr_ * 0.7
    for k, (r, z0, h) in enumerate(((1.8, 0.0, 1.2), (1.3, 1.1, 1.0), (0.9, 2.0, 0.9), (0.5, 2.8, 0.8))):
        box(c, "Shrine Cairn %d" % k, sx2, sy2, r, r, ground(sx2, sy2) + z0 - 0.3, ground(sx2, sy2) + z0 + h, ("frost_stone", "wall"),
            rot=0.4 * k)
    c.place(ip.obelisk(c, 1, 6.0), sx2 + math.sin(toward) * 3.5, sy2 - math.cos(toward) * 3.5, ground(sx2, sy2) - 0.2, rot=toward,
            coll="Props")
    cflags = smp_.Bunting()
    for sd in (-1, 1):
        x, y = sx2 + math.sin(toward) * sd * 6.0, sy2 - math.cos(toward) * sd * 6.0
        c.place(smp_.flag_pole(c, 6.0), x, y, ground(x, y) - 0.2, coll="Props")
        cflags.line((sx2, sy2, ground(sx2, sy2) + 4.6), (x, y, ground(x, y) + 5.6), sag=0.8)
        g = c.game(x - math.cos(toward) * 1.0, y - math.sin(toward) * 1.0, ground(x, y) + 1.2)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
    cflags.build(c, "Camp Flags")
    g = c.game(cx_ + 2.0, cy_, cz_)
    c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=cr_ - 1.0, n=4, folk="snow", heading=0.0)
    taken.add(cx_, cy_, cr_ + 2.0)
    for k, qq in enumerate(c.S[::14]):
        if on_road(qq.s) and L.look_at(qq.p.x, qq.p.y) == "snow":
            sd = 1 if k % 2 else -1
            px, py = qq.p.x + qq.r.x * sd * (qq.w / 2 + 1.6), qq.p.y + qq.r.y * sd * (qq.w / 2 + 1.6)
            if paint.road_clear(c, px, py, 0.8):
                pz = ground(px, py)
                c.place(kp.torch_post(c), px, py, pz - 0.1, coll="Props", role="visual")
                g = c.game(px, py, pz + 2.6)
                c.entity("torch", x=g[0], y=g[1], z=g[2])
    flags.build(c)
    # ---- The Snow Kingdom's peaks, ahead the whole way (beyond the land's edge).
    for k, (x, y, r, h) in enumerate(((520.0, 560.0, 150.0, 330.0), (380.0, 620.0, 130.0, 280.0), (640.0, 420.0, 140.0, 300.0),
                                      (250.0, 640.0, 110.0, 230.0), (680.0, 620.0, 160.0, 360.0))):
        cone(c, "Far Peak %d" % k, x, y, r, 60.0, h, ("frost_cliff", "wall"), segs=7, role="visual")
        cone(c, "Far Peak Snow %d" % k, x, y, r * 0.42, 60.0 + h * 0.58, h * 0.42 + 2.0, ("snow_ground", "wall"), segs=7,
             role="visual")


def dress_pass(c, ground, taken, on_road):
    tree = dict(room=5.0, road_margin=6.0, trunk=(0.6, 6.0))
    _scatter_look(c, ground, taken, "snow", [
        (snp.ice_spike(c, 0), 10, dict(room=5.0, road_margin=7.0)), (snp.ice_spike(c, 1), 8, dict(room=5.0, road_margin=7.0)),
        (snp.snow_mound(c, 1), 10, dict(room=4.0, road_margin=5.0, role="visual")),
    ])
    _scatter_look(c, ground, taken, "glacier", [
        (ap.ice_column(c, 0, height=22.0, radius=4.0), 8, dict(room=8.0, road_margin=8.0)),
        (ap.ice_spike(c, 1, height=10.0), 12, dict(room=5.0, road_margin=7.0)),
    ])
    _scatter_look(c, ground, taken, "melt", [
        (snp.snow_pine(c, 0), 10, tree), (snp.snow_pine(c, 2), 8, tree),
        (smp_.boulder(c, 1), 12, dict(room=4.0, road_margin=6.0, scale=(1.0, 2.0))),
        (smp_.broadleaf(c, 1), 6, tree),
    ])
    _scatter_look(c, ground, taken, "canyon", [
        (cp.boulder(c, 0), 6, dict(room=4.0, road_margin=6.0)),
        (cp.sagebrush(c, 0), 16, dict(room=2.5, role="visual")),
    ])
    _scatter_look(c, ground, taken, "sand", [
        (cp.saguaro(c, 0), 10, dict(room=5.0, road_margin=6.0, trunk=(0.6, 6.0))),
        (cp.saguaro(c, 1), 8, dict(room=5.0, road_margin=6.0, trunk=(0.6, 6.0))),
        (cp.hoodoo(c, 1, height=16.0), 4, dict(room=10.0, road_margin=9.0)),
        (cp.sagebrush(c, 1), 24, dict(room=2.5, role="visual")),
        (gp.cattle_skull(c), 4, dict(room=3.0, role="visual")),
    ])
    # The Melt: meltwater falls down its walls.
    for k, q in enumerate(c.S[::70]):
        if on_road(q.s) and L.look_at(q.p.x, q.p.y) == "melt" and k % 2 == 0:
            for sd in (-1, 1):
                x, y = q.p.x + q.r.x * sd * 24.0, q.p.y + q.r.y * sd * 24.0
                if L.wall_sd(x, y) > -2:
                    z = ground(x, y)
                    props.falls(c, "Melt Falls %d %d" % (k, sd), x, y, z + 18.0, z - 0.5, 4.0, 7.0, throw=1.5, foam=True,
                                angle=math.atan2(q.r.y * sd, q.r.x * sd) - math.pi / 2)
                    break
    # Sunbeams in the Red Cut.
    for k, q in enumerate(c.S[::30]):
        if on_road(q.s) and L.look_at(q.p.x, q.p.y) == "canyon":
            import impact_props as ip

            c.place(ip.sun_beam(c, length=50.0, r=5.0, variant=k % 2), q.p.x + q.r.x * 3.0, q.p.y + q.r.y * 3.0, q.p.z,
                    rot=k * 0.7, role="visual")


def dress_dust(c, ground, taken, on_road):
    tree = dict(room=5.0, road_margin=6.0, trunk=(0.6, 7.0))
    _scatter_look(c, ground, taken, "dunes", [
        (cp.sagebrush(c, 0), 10, dict(room=3.0, role="visual")),
        (gp.cattle_skull(c), 4, dict(room=3.0, role="visual")),
        (gp.tumbleweed(c, 0), 10, dict(room=3.0, role="visual")),
    ])
    _scatter_look(c, ground, taken, "scrub", [
        (gp.dead_tree(c, 0), 8, dict(room=5.0, road_margin=5.0, trunk=(0.5, 5.0))),
        (cp.joshua_tree(c, 0), 8, dict(room=5.0, road_margin=6.0, trunk=(0.6, 5.0))),
        (props.bush(c, 0), 14, dict(room=3.0, road_margin=4.0)),
        (cp.agave(c, 0), 12, dict(room=2.5, role="visual")),
    ])
    _scatter_look(c, ground, taken, "ford", [
        (op.palm(c, 0, height=10.0), 10, tree), (op.palm(c, 1, height=12.0), 8, tree),
        (props.reeds(c), 14, dict(room=2.5, role="visual")),
        (props.fern(c), 16, dict(room=2.5, role="visual")),
    ])
    _scatter_look(c, ground, taken, "jungle", [
        (props.jungle_tree(c, 0), 16, tree), (props.jungle_tree(c, 2), 14, tree),
        (bp.coconut_palm(c, 0), 10, tree),
        (props.big_leaf_plant(c, 0), 16, dict(room=2.5, role="visual")),
        (props.fern(c), 20, dict(room=2.5, role="visual")),
    ])
    c.entity("dustwind", rate=6)


def dress_cause(c, ground, taken, on_road):
    # The sea stacks, out of the water either side of the causeway.
    for k, (x, y, r, h) in enumerate(J.STACKS):
        if not paint.road_clear(c, x, y, r + 4.0):
            continue
        c.assign(c.rock_mass("Sea Stack %d" % k, x, y, r, r * 0.8, h, z0=-12.0, n=14, seed=k + 3), c.lib("isle_rock", "wall"))
        taken.add(x, y, r + 4.0)
    _scatter_look(c, ground, taken, "reef", [
        (tp.coral(c, 0), 18, dict(room=3.0, road_margin=4.0, role="visual")),
        (tp.coral(c, 1), 14, dict(room=3.0, road_margin=4.0, role="visual")),
    ])
    _scatter_look(c, ground, taken, "isle", [
        (kp.pine(c, 0, 9.0), 8, dict(room=5.0, road_margin=6.0, trunk=(0.6, 6.0))),
        (smp_.boulder(c, 1), 8, dict(room=4.0, road_margin=6.0)),
    ])
    _scatter_look(c, ground, taken, "crags", [
        (kp.pine(c, 1, 11.0), 12, dict(room=5.0, road_margin=6.0, trunk=(0.6, 6.0))),
        (kp.brazier(c), 4, dict(room=5.0, near_road=(2.0, 5.0))),
    ])
    # The Isle's ruined lighthouse on its crest.
    lx, ly = 30.0, -40.0
    if paint.road_clear(c, lx, ly, 12.0):
        c.place(tp.lighthouse(c, h=18.0), lx, ly, ground(lx, ly) - 0.5)
    else:
        for x, y in ((52.0, -70.0), (0.0, -78.0), (88.0, -40.0)):
            if paint.road_clear(c, x, y, 10.0):
                c.place(tp.lighthouse(c, h=18.0), x, y, ground(x, y) - 0.5)
                break
    # The Ribs: a sea serpent's skeleton arching over the strait.
    for k, q in enumerate(c.S[::14]):
        if on_road(q.s) and L.pocket_at(q.p.x, q.p.y) == "strait":
            c.place(dcp.rib(c, span=24.0, height=16.0, variant=k % 2), q.p.x, q.p.y, q.p.z - 4.0,
                    rot=math.atan2(q.t.y, q.t.x) - math.pi / 2, role="visual")
    c.entity("storm", period=11, spread=5, distance=900)


DRESS = {"gorge": dress_gorge, "pass": dress_pass, "dust": dress_dust, "cause": dress_cause}


if __name__ == "__main__":
    main()
