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
        "env": "ember_volcano",
        # look: (ground, cliff, road, shoulder)
        "looks": {
            "ember": (("ash_soil", "dirt"), ("ember_rock", "wall"), "basalt_road", ("scorched_ground", "dirt")),
            "basalt": (("scorched_ground", "dirt"), ("obsidian_cliff", "wall"), "basalt_road", ("ash_soil", "dirt")),
            "frost": (("snow_ground", "packed_snow"), ("frost_rock", "wall"), "snow_stone_road", ("snow_ground", "packed_snow")),
            "snow": (("snow_ground", "deep_snow"), ("frost_cliff", "wall"), "packed_snow_road", ("snow_ground", "deep_snow")),
        },
        "bridge": ("plank_deck", ("weathered_timber", "wall"), ("fence_rail", "wall")),
        "water": ("river_ice", "ice"),
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

    def label(q):
        if not s_start <= q.s <= s_end:
            return None  # (no road: the way round out of sight)
        if L.tunnel_floor(q.p.x, q.p.y) is not None and L.wall_sd(q.p.x, q.p.y) > -6:
            return L.look_at(q.p.x, q.p.y)
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
            half = pb.bore(c, L, name, s0, s1, ("glacier_wall", "wall"), ("snow_ground", "deep_snow"), height=12.0)
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
    tree = dict(room=5.0, road_margin=6.0, trunk=(0.6, 6.0))
    _scatter_look(c, ground, taken, "ember", [
        (props.jungle_tree(c, 0), 10, tree), (props.jungle_tree(c, 1), 10, tree),
        (props.basalt_columns(c), 6, dict(room=6.0, road_margin=6.0)),
        (vp.obsidian_cluster(c, 0), 6, dict(room=5.0, road_margin=6.0)),
        (props.boulder(c, "volcano_basalt", 1), 10, dict(room=4.0, road_margin=6.0, scale=(1.0, 2.0))),
    ])
    _scatter_look(c, ground, taken, "basalt", [
        (props.basalt_columns(c), 8, dict(room=6.0, road_margin=6.0)),
        (props.boulder(c, "volcano_basalt", 2), 8, dict(room=4.0, road_margin=6.0, scale=(1.0, 2.2))),
        (props.dead_tree(c), 6, dict(room=5.0, road_margin=5.0, trunk=(0.5, 5.0))),
    ])
    _scatter_look(c, ground, taken, "frost", [
        (smp_.broadleaf(c, 0, frosted=True), 10, tree), (smp_.broadleaf(c, 1, frosted=True), 8, tree),
        (snp.snow_pine(c, 0), 10, tree), (snp.snow_pine(c, 2), 8, tree),
        (smp_.boulder(c, 0), 8, dict(room=4.0, road_margin=6.0)),
    ])
    _scatter_look(c, ground, taken, "snow", [
        (snp.snow_pine(c, 1), 14, tree), (snp.snow_pine(c, 3), 10, tree),
        (snp.ice_spike(c, 0), 8, dict(room=5.0, road_margin=7.0)),
        (snp.snow_mound(c, 0), 8, dict(room=4.0, road_margin=5.0, role="visual")),
    ])
    # The gorge burnt: its trees charred where Cinderjaw's fire came down it.
    ruin_kit.char_trees(c, lambda x, y: 1.0 if L.look_at(x, y) == "ember" else 0.0, ("Jungle Tree",), chance=0.9,
                        threshold=0.5)
    # Steam off the lava, and vents along the gorge.
    for k, q in enumerate(c.S[::90]):
        if on_road(q.s) and L.look_at(q.p.x, q.p.y) == "ember":
            sd = 1 if k % 2 else -1
            x, y = q.p.x + q.r.x * sd * 16.0, q.p.y + q.r.y * sd * 16.0
            g = c.game(x, y, ground(x, y) + 0.5)
            c.entity("steam", x=g[0], y=g[1], z=g[2])
    c.entity("ashfall", rate=10, radius=40)


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
