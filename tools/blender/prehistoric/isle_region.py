# Tropic Isles' overworld region, v5: the island lived in, a figure eight through it
# (isle_layout.py: Blake, Nov 1: "i want to also travel through the island. not just around
# it"; "all of the areas containing the levels need to be their own sub world"). Builds
# beach_region and, with --ruin, beach_region_ruin.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/isle_region.py [--ruin]
#
# Raptor's Bay, the Head Pass, Coral Cove, up the Ridge Road and over the High Bridge, down
# the Cloud Forest to Shipwreck Bay, Smugglers' Point, round the Lagoon, up the Gorge Road
# under the High Bridge to the Jungle Heart (the falls over the road, the temple, Rainforest
# Rush's gateway), through the Temple Gate, down the North Valley to the Black Shore
# (Volcano Isle's gateway), round the north-east coast home. Each its own basin, walled by
# jungle ridges; the coves' beaches the island's ring.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp  # noqa: E402
import region_ruin as ruin  # noqa: E402
import puzzle_kit  # noqa: E402
import pocket_build as pb  # noqa: E402
from pocket_build import box, cone  # noqa: E402
import props  # noqa: E402
import beach_props as bp  # noqa: E402
import tropic_props as tp  # noqa: E402
import region_paint as paint  # noqa: E402
import isle_layout as M  # noqa: E402
import isle_dress as idr  # noqa: E402
import isle_sections as isec  # noqa: E402

RUIN = ruin.ON
TRACK_ID = ruin.track_id("beach_region") + os.environ.get("KP_REGION_SUFFIX", "")
WATER_Z = M.WATER_Z
L = M.L

# (Blake, Nov 1: "the track texture looks too much like dirt. ... if we are close to beach it
# can be sand color, if in the center of the island it can be browner.")
SAND_ROAD = "isle_sand_road"
JUNGLE_ROAD = "isle_jungle_road"
LOOK = {
    # look: (ground, cliff, road, shoulder)
    "village": (("beach_sand", "sand"), ("cove_rock", "wall"), SAND_ROAD, ("beach_sand", "sand")),
    "head": (("cove_grass", "grass"), ("cove_rock", "wall"), SAND_ROAD, ("cove_sand", "sand")),
    "coral": (("cove_sand", "sand"), ("cove_rock", "wall"), SAND_ROAD, ("cove_sand", "sand")),
    "ridge": (("isle_jungle", "grass"), ("jungle_mossstone", "wall"), JUNGLE_ROAD, ("isle_jungle", "grass")),
    "cloud": (("jungle_leafcover", "grass"), ("jungle_mossstone", "wall"), JUNGLE_ROAD, ("jungle_leafcover", "grass")),
    "wreck": (("wreck_sand", "sand"), ("wreck_rock", "wall"), SAND_ROAD, ("wreck_sand", "sand")),
    "point": (("cove_sand", "sand"), ("cove_rock", "wall"), SAND_ROAD, ("cove_sand", "sand")),
    "lagoon": (("beach_sand", "sand"), ("jungle_mossstone", "wall"), SAND_ROAD, ("beach_sand", "sand")),
    "gorge": (("isle_jungle", "grass"), ("canyon_rock_moss", "wall"), JUNGLE_ROAD, ("isle_jungle", "grass")),
    "heart": (("jungle_leafcover", "grass"), ("jungle_mossstone", "wall"), JUNGLE_ROAD, ("jungle_leafcover", "grass")),
    "north": (("isle_jungle", "grass"), ("jungle_mossstone", "wall"), JUNGLE_ROAD, ("isle_jungle", "grass")),
    "volcano": (("black_sand", "sand"), ("isle_rock", "wall"), SAND_ROAD, ("black_sand", "sand")),
    "northeast": (("beach_sand", "sand"), ("cove_rock", "wall"), SAND_ROAD, ("beach_sand", "sand")),
}
JUNGLE_LOOKS = ("ridge", "cloud", "gorge", "heart", "north")
BEACH_SAND = {"volcano": ("black_sand", "sand"), "wreck": ("wreck_sand", "sand"), "coral": ("cove_sand", "sand"),
              "point": ("cove_sand", "sand")}
FALLS_MATS = ("falls_oasis", "falls_curtain_oasis", "falls_foam")


def natural(x, y):
    h = M.natural(x, y)
    tz = M.tunnel_floor(x, y)
    if tz is not None:
        h = min(h, tz - 0.25)
    return h


def classify(c, n, info):
    look = M.look_at(c.x, c.y)
    s = M.inland(c.x, c.y)
    if n.z < 0.62:
        if s < 70.0:
            return ("isle_rock", "wall") if look == "volcano" else ("cove_rock", "wall")  # (the sea bluffs)
        return LOOK[look][1] if M.wall_sd(c.x, c.y) < 30.0 else ("jungle_mossstone", "wall")
    if c.z < WATER_Z - 2.0 and s < 0.0:
        return ("cove_wet_sand", "deep_water")  # (out of your depth: back to the road)
    if c.z < WATER_Z + 0.25:
        if math.hypot(c.x - M.LAGOON[0], c.y - M.LAGOON[1]) < M.LAGOON[2] + 20 or M.river_d(c.x, c.y)[0] < M.RIVER_HW + 3:
            return ("lagoon_shallow", "water")
        return ("black_sand", "water") if look == "volcano" else ("cove_wet_sand", "water")
    if n.z < 0.85:
        return ("jungle_mossstone", "dirt") if s > 70.0 else ("cove_rock", "dirt")
    if s < 8.0:
        return ("black_sand", "sand") if look == "volcano" else ("cove_wet_sand", "sand")
    if s < 40.0 and c.z < 4.2:
        return BEACH_SAND.get(look, ("beach_sand", "sand"))
    sd = M.wall_sd(c.x, c.y)
    if sd < 2.0:
        # (a basin's floor: its own ground, turning into the next's where two meet)
        return pb.transition(M.look_weights(c.x, c.y), lambda lk: LOOK[lk][0])
    if c.z > 120.0:
        return ("jungle_mossstone", "dirt")  # (the pinnacle's mossy shoulders)
    return ("isle_jungle", "grass") if math.sin(c.x / 19.0) * math.cos(c.y / 23.0) < 0.45 else ("jungle_leafcover", "grass")


def main():
    c = kit.Course(TRACK_ID, "Tropic Isles (ruined)" if RUIN else "Tropic Isles", "coral_cove")
    c.route(M.route_points(), width=14.0, bank=5.0)
    kinds = {}
    for look, (ground, cliff, road, shoulder) in LOOK.items():
        kinds[look] = {"mat": road, "shoulder": 1.5, "shoulder_mat": shoulder}
    # The High Bridge: planks on rope rails, high over the gorge.
    kinds["highbridge"] = {"mat": "plank_deck", "surface": "road", "shoulder": 0.6, "shoulder_mat": ("plank_deck", "road"),
                           "barrier": 1.1, "barrier_mat": ("rope_rail", "wall"), "deck": 2.2,
                           "deck_mat": ("weathered_timber", "wall"), "ground": False}
    c.kinds = kinds

    def label(q):
        # (the whole span over the gorge: no land raised under it, the Gorge Road's under it)
        if M.is_bridge(q.p.x, q.p.y, q.p.z):
            return "highbridge"
        return M.look_at(q.p.x, q.p.y)

    runs = list(kit.runs(c, label))
    c.roads(kit.plan(c, pb.blend_runs(c, runs, LOOK), "village", max_len=160.0))
    bridge = [(s0, s1) for s0, s1, k in runs if k == "highbridge"]

    trail = dict(width=9.0, shoulder=1.2, shoulder_mat=("beach_sand", "sand"))
    # Raptor's square, off the road; the island hop's pier out east over the bay (the road's
    # west of the square: the pier never crosses it).
    hx, hy, hr = M.HUB
    smp, _ = c.nearest(hx, hy)
    a = math.atan2(smp.p.y - hy, smp.p.x - hx)
    c.side_road("Square Road", pb.line(natural, (smp.p.x, smp.p.y), (hx + (hr - 3.0) * math.cos(a), hy + (hr - 3.0) * math.sin(a)),
                                       z0=smp.p.z, c=c), "wood_dock", "road", **trail)
    hz = natural(hx, hy)
    (ax, ay), (bx, by) = M.HOP_PIER
    pier_z = max(WATER_Z + 2.2, hz)
    hop = [(lerp(ax, bx, k / 20), lerp(ay, by, k / 20), lerp(hz + 0.14, pier_z + 0.02, min(1.0, k / 3))) for k in range(21)]
    c.side_road("Hop Pier", hop, "wood_dock", "road", width=10.0, shoulder=0.4, shoulder_mat=("wood_dock", "road"),
                barrier=1.0, barrier_mat=("cove_rail", "wall"), deck=1.6, deck_mat=("cove_post", "wall"), ground=False)
    # The gateways: each at the end of a short path off the road (Blake, Nov 1).
    gates = dict(M.GATES)
    if RUIN:
        gates["lair"] = M.LAIR
    path_mat = lambda x, y: LOOK[M.look_at(x, y)][2]  # noqa: E731
    spots = pb.spurs(c, natural, gates, path_mat, trail)

    X0, X1, Y0, Y1 = -476, 476, -476, 476
    ter = c.terrain("Tropic Isles", X0, X1, Y0, Y1, 3.0, natural, classify, near=8.0, fade=16.0, verge_fill=1.5)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 6.0, lambda x, y: natural(x, y) - 0.5, c.lib("beach_sand", "sand"))
    c.disc("Sea", 0.0, 0.0, 1800.0, WATER_Z, c.lib("sea_water", "water"), role="visual", n=72)

    def ground(x, y):
        z = c.ground_z(x, y, [ter])
        return natural(x, y) if z is None else z

    taken = paint.Taken([(hx, hy, hr + 12.0), (*M.CAVE, 18.0), (*M.SECRET, 14.0),
                         *((lerp(ax, bx, k / 24), lerp(ay, by, k / 24), 7.0) for k in range(25)),
                         (M.LAGOON[0], M.LAGOON[1], M.LAGOON[2] - 6.0), (*M.FALLS, M.POOL_R + 4.0),
                         *((e[0], e[1], 12.0) for e, _ in spots.values()), *((x, y, 14.0) for x, y in M.GATES.values()),
                         (*M.LAIR, 18.0)])
    water(c)
    isec.temple_gate(c, ground)
    if bridge:
        isec.high_bridge(c, ground, bridge[0])
    village(c, ground, taken, ter)
    landmarks(c, ground, spots, taken)
    isec.heart(c, ground, taken, ter, FALLS_MATS)
    isec.gorge(c, ground, taken, FALLS_MATS)
    isec.lagoon(c, ground, taken)
    if RUIN:
        ruined(c, ground)
    else:
        idr.coral_cove(c, ground, taken, ter)
        idr.shipwreck(c, ground, taken, ter)
        idr.pier_lamps(c, "Hop Pier", (ax, ay), (bx, by), pier_z, start=math.hypot(bx - ax, by - ay) * 3 / 20 + 2.0)
        isec.black_shore(c, ground, taken)
    isec.cloud_forest(c, ground, taken)
    isec.head_pass(c, ground, taken)
    if not RUIN:
        isec.fishing_camp(c, ground, taken, ter)
        isec.valley_hamlet(c, ground, taken, ter)
    idr.jungle(c, ground, taken, looks=JUNGLE_LOOKS)
    sea_cave(c, ground)
    puzzle_kit.pen(c, "secret", "Hidden Cove", *M.SECRET, pb.to_road(c, *M.SECRET), 9.0, 4.5, ("isle_rock", "wall"),
                   ground(*M.SECRET), height=6.0)
    pb.emit_spots(c, spots)
    dress(c, ground, taken)
    paint.wayfolk(c, ground, "beach", [M.HUB[:2]], 10, apart=110.0, every=25)

    c.start_line()
    keep = list(M.GATES.values()) + [M.LAIR, M.CAVE, M.SECRET, M.HUB[:2], M.HOP_PIER[0]]
    spans = [pb.tunnel_span(c, M.L, *M.TUNNELS[0][2:])]
    # (both roads past the crossing: the bridge over it, the gorge road under it)
    for q in c.S:
        if math.hypot(q.p.x - M.CROSS[0], q.p.y - M.CROSS[1]) < M.BRIDGE_HALF + 6.0:
            if spans[-1][1] >= q.s - 3.0 and len(spans) > 1:
                spans[-1] = (spans[-1][0], q.s)
            else:
                spans.append((q.s, q.s))
    isec.zippers(c, (keep, spans))
    gts = c.checkpoints(height=10.0)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish(extra={"race": {"laps": 1}})
    print("loop", round(c.length, 1), "gates", len(gts))
    s0 = c.at(0.0)
    g = c.game(s0.p.x, s0.p.y, 0.0)
    print("start x %.1f z %.1f heading %.4f" % (g[0], g[2], math.atan2(s0.t.x, -s0.t.y)))
    g = c.game(hx, hy, 0.0)
    print("hub x %.1f z %.1f" % (g[0], g[2]))
    g = c.game(bx - 10.0, by, 0.0)
    print("passage hop: x %.1f z %.1f heading %.4f" % (g[0], g[2], math.atan2(ax - bx, -(ay - by))))
    for name, (end, hd) in spots.items():
        g = c.game(end[0], end[1], 0.0)
        print("spot %s x %.2f z %.2f heading %.4f" % (name, g[0], g[2], hd))


# ------------------------------------------------------------------ Smugglers' Point


def _into_point(x, y, d):
    """(x, y) moved d metres in toward Smugglers' Point's cliffs."""
    a = M.POINT[0]
    r = M.shore_r(a) - 20.0
    px, py = r * math.cos(a), r * math.sin(a)
    L = math.hypot(px - x, py - y)
    return x + (px - x) / L * d, y + (py - y) / L * d, math.atan2(py - y, px - x)


def sea_cave(c, ground):
    """The smugglers' Sea Cave: its yard on the beach under the Point's south cliff (rock
    walls, the cave's dark mouth at its back, lanterns, their chests and crates): the way in
    and out to the Dragon Kingdom (no sea door any more)."""
    cx, cy = M.CAVE
    puzzle_kit.pen(c, "return", "Sea Cave", cx, cy, pb.to_road(c, cx, cy), 11.0, 4.5, ("cove_rock", "wall"), ground(cx, cy),
                   height=6.0)
    for name, (x, y), w, h in (("Sea Cave Mouth", M.CAVE, 6.0, 7.0),):
        mx, my, rot = _into_point(x, y, 13.0 if name == "Tunnel Door" else 15.0)
        z = ground(x, y)
        box(c, name, mx, my, 1.2, w / 2, z - 1.0, z + h, ("dark_corridor", "wall"), rot=rot, role="visual")
        # (Its rock round it: the mouth in the face of a rock, not a dark slab standing on
        # the beach: the deep pass.)
        rx, ry = mx + 8.4 * math.cos(rot), my + 8.4 * math.sin(rot)
        if all(paint.road_clear(c, rx + 9.0 * math.cos(t), ry + 9.0 * math.sin(t), 1.0) for t in [k * 0.785 for k in range(8)]):
            rk = c.rock_mass(name + " Rock", rx, ry, 7.8, w / 2 + 6.0, z + h + 5.0, z0=z - 3.0, n=16, seed=len(name), angle=rot, base=z)
            c.assign(rk, c.lib("cove_rock", "wall"))
        box(c, name + " Lintel", mx - 1.3 * math.cos(rot), my - 1.3 * math.sin(rot), 0.4, w / 2 + 0.8, z + h, z + h + 0.7,
            ("weathered_timber", "wall"), rot=rot, role="visual")
        for sd in (-1, 1):
            px, py = mx - 1.3 * math.cos(rot) - sd * (w / 2 + 0.5) * math.sin(rot), my - 1.3 * math.sin(rot) + sd * (w / 2 + 0.5) * math.cos(rot)
            box(c, name + " Post %d" % sd, px, py, 0.35, 0.35, z - 0.5, z + h, ("weathered_timber", "wall"), rot=rot)  # (solid)
            lx, ly = px - 1.2 * math.cos(rot), py - 1.2 * math.sin(rot)
            c.place(bp.tiki_torch(c, 0), lx, ly, ground(lx, ly))
            g = c.game(lx, ly, ground(lx, ly) + 2.6)
            c.entity("torch", x=g[0], y=g[1], z=g[2])
        for k in range(4):
            bx_ = mx - 6.0 * math.cos(rot) + (k - 1.5) * 2.2 * math.sin(rot) * (1 if name == "Tunnel Door" else -1)
            by_ = my - 6.0 * math.sin(rot) - (k - 1.5) * 2.2 * math.cos(rot) * (1 if name == "Tunnel Door" else -1)
            if paint.road_clear(c, bx_, by_, 2.0) and math.hypot(bx_ - x, by_ - y) > 6.0:
                c.place(tp.barrel(c), bx_, by_, ground(bx_, by_) - 0.1, rot=k)


# ------------------------------------------------------------------ water


def water(c):
    """The lagoon, the river down its gorge from the falls' pool (the falls: isle_sections.heart)."""
    lx, ly, lr = M.LAGOON
    c.disc("Lagoon", lx, ly, lr + 10.0, M.LAGOON_Z, c.lib("lagoon_shallow", "water"), role="visual", n=40, wobble=0.12, seed=3)
    strip = []
    for (ax, ay, az), (bx, by, bz) in zip(M.RIVER, M.RIVER[1:]):
        n = max(1, int(math.hypot(bx - ax, by - ay) / 5))
        for k in range(n):
            t = k / n
            strip.append((lerp(ax, bx, t), lerp(ay, by, t), M.RIVER_HW * 2 + 3.0, lerp(az, bz, t)))
    strip.append((M.RIVER[-1][0], M.RIVER[-1][1], M.RIVER_HW * 2 + 3.0, M.RIVER[-1][2]))
    c.ribbon("River", strip, M.RIVER_HW * 2 + 3.0, 0, c.lib("lagoon_shallow", "water"), role="visual", steps=3)


# ------------------------------------------------------------------ the village


def village(c, ground, taken, ter):
    """Raptor's village: a boardwalk square above the east bay, huts round it, stilt huts
    out over the bay either side of the hop's pier, tiki torches, a fire, its folk."""
    hx, hy, hr = M.HUB
    # (The square a deck of planks on land graded level, not a plane over the sand: the deep
    # pass, isle_dress.village_deck; its huts graded round it: isle_dress.village.)
    hz = idr.village_deck(c, ground, ter) - 0.12
    if RUIN:
        for k in range(8):
            a = k * math.tau / 8 + 0.3
            if math.cos(a) > 0.7 or math.cos(a) < -0.7 and math.sin(a) > -0.2:
                continue  # (clear of the pier, east, and the road, west)
            x, y = hx + (hr + 7) * math.cos(a), hy + (hr + 7) * math.sin(a)
            if not paint.road_clear(c, x, y, 6.0):
                continue
            box(c, "Hut %d" % k, x, y, 3.5, 3.5, ground(x, y) - 1.0, ground(x, y) + 1.4, ("tiki_wood", "wall"), rot=a)
            ruin.rubble(c, "Hut Wreck %d" % k, x + 4 * math.cos(a), y + 4 * math.sin(a), ground, ("thatch", "wall"), n=4, spread=3.0,
                        size=1.0, seed=k)
    # Stilt huts over the bay, along the pier.
    (ax, ay), (bx, by) = M.HOP_PIER
    for k in range(8):
        t = 0.18 + 0.1 * (k // 2)
        sd = 1 if k % 2 else -1
        x, y = lerp(ax, bx, t), lerp(ay, by, t) + sd * 15.0
        if M.inland(x, y) > -4.0:
            continue
        for sx in (-1, 1):
            for sy in (-1, 1):
                box(c, "Stilt %d %d%d" % (k, sx, sy), x + sx * 3.0, y + sy * 3.0, 0.2, 0.2, WATER_Z - 3.0, WATER_Z + 2.4,
                    ("cove_post", "wall"), role="visual")
        box(c, "Stilt Deck %d" % k, x, y, 4.0, 4.0, WATER_Z + 2.2, WATER_Z + 2.45, ("wood_dock", "wall"))
        box(c, "Stilt Walk %d" % k, x, lerp(y, lerp(ay, by, t), 0.5), 1.0, 5.0, WATER_Z + 2.2, WATER_Z + 2.4, ("wood_dock", "wall"),
            role="visual")
        if RUIN:
            ruin.rubble(c, "Stilt Wreck %d" % k, x, y, lambda x_, y_: WATER_Z + 2.4, ("thatch", "wall"), n=3, spread=2.5, size=1.0,
                        seed=40 + k)
        else:
            c.place(tp.beach_hut(c, k % 3), x, y, WATER_Z + 2.45, rot=math.pi / 2 if sd > 0 else -math.pi / 2, role="visual",
                    name="Stilt Hut %d" % k)
    g = c.game(hx, hy, hz + 0.3)
    c.entity("campfire", x=g[0], y=g[1], z=g[2])
    c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=hr - 2.0, n=7, folk="beach", heading=0.0)
    torch = bp.tiki_torch(c, 0)
    for k in range(12):
        a = k * math.tau / 12 + 0.26
        x, y = hx + (hr + 1.5) * math.cos(a), hy + (hr + 1.5) * math.sin(a)
        if not paint.road_clear(c, x, y, 1.0):
            continue
        c.place(torch, x, y, ground(x, y))
        g = c.game(x, y, ground(x, y) + 2.6)
        c.entity("torch", x=g[0], y=g[1], z=g[2])
    if not RUIN:
        idr.village(c, ground, taken, ter, hz + 0.12)


# ------------------------------------------------------------------ the landmarks


def landmarks(c, ground, spots, taken):
    """Volcano Isle smoking offshore, Coral Cove's coral heads and lifeguard tower."""
    def facing(name):
        (ex, ey), _ = spots[name]
        gx, gy = M.GATES[name] if name in M.GATES else M.LAIR
        return math.atan2(gy - ey, gx - ex)

    # (Splash Lagoon's slide tower and Shipwreck Bay's galleon: isle_dress, the deep pass.)
    # Volcano Isle offshore, smoking.
    vx, vy = M.VOLCANO
    volc = c.rock_mass("Volcano Isle", vx, vy, 90.0, 74.0, 120.0, z0=WATER_Z - 6.0, n=20, seed=7,
                       bands=[(1.0, 0.0), (0.7, 0.4), (0.4, 0.8), (0.25, 1.0)], base=WATER_Z)
    c.assign(volc, c.lib("isle_rock", "wall"))
    g = c.game(vx, vy, 122.0)
    c.entity("eruption", x=g[0], y=g[1], z=g[2], period=15.0, offset=2.0)
    # Coral Cove: coral heads in the shallows off its beach, the lifeguard tower.
    x, y = M.GATES["coral"]
    f = facing("coral")
    for k in range(9):
        a = f + (k - 4) * 0.3
        px, py = x + 18.0 * math.cos(a), y + 18.0 * math.sin(a)
        c.place(tp.coral(c, k % 3), px, py, ground(px, py) - 0.3, rot=a, role="visual")
    lx, ly = x - 22.0 * math.sin(f), y + 22.0 * math.cos(f)
    c.place(tp.lifeguard_tower(c), lx, ly, ground(lx, ly))
    taken.add(lx, ly, 6.0)


def ruined(c, ground):
    """After Tidewyrm's attack: his sea cave in the Head's cliffs, wreckage up the beaches."""
    x, y = M.LAIR
    z = ground(x, y)
    box(c, "Lair Mouth", x, y, 3.0, 8.0, z - 1.0, z + 12.0, ("dark_corridor", "wall"), role="visual")
    for k in range(7):
        t = (k - 3) / 3.0
        if abs(t) < 0.4:
            continue
        px, py = x + 1.0, y + t * 12.0
        cone(c, "Lair Rock %d" % k, px, py, 3.5 + abs(t) * 1.5, ground(px, py) - 1.0, 9.0 + 7.0 * (1 - abs(t)), ("isle_rock", "wall"),
             segs=6)
    k = 0
    for j in range(60):
        a = j * 2.399
        r = 200.0 + 140.0 * ((j * 0.618) % 1.0)
        px, py = r * math.cos(a), r * math.sin(a)
        s = M.inland(px, py)
        if 4.0 < s < 50.0 and paint.road_clear(c, px, py, 7.0):
            ruin.rubble(c, "Wreckage %d" % k, px, py, ground, ("wreck_planks", "wall"), n=5, spread=4.0, size=1.1, seed=30 + k)
            k += 1


# ------------------------------------------------------------------ the paint pass


def dress(c, ground, taken):
    """Coconut palms round every beach, leaning out over the sand; the rainforest dense up
    the mountain (big trees, palms, bushes, ferns, big-leaf plants); Coral's umbrellas,
    chairs, towels, canoes; Shipwreck's pirate huts, barrels, cannon, rowboats; starfish
    and shells. (After the wave: the palms snapped, the beach things gone.)"""
    rmax = 470.0
    g = ground

    def beach(x, y):
        s = M.inland(x, y)
        return 6.0 < s < 60.0 and natural(x, y) < 8.0 and M.look_at(x, y) != "volcano"

    def jungle(x, y):
        s = M.inland(x, y)
        return (s > 40.0 and natural(x, y) > 3.5 and M.river_d(x, y)[0] > M.RIVER_HW + 3 and M.look_at(x, y) != "volcano"
                and natural(x, y) < 140.0)

    def look(name):
        return lambda x, y: beach(x, y) and M.look_at(x, y) == name

    snapped = lambda x, y, z, s: ruin.stump(c, "Snapped Palm %d %d" % (int(x), int(y)), x, y, z, ("palm_bark", "wall"),  # noqa: E731
                                            h=1.5 + 2.0 * s, r=0.45)
    for v in range(3):
        paint.scatter(c, bp.coconut_palm(c, v), 60, rmax, beach, g, taken, 10 + v, room=6.0, road_margin=5.0,
                      instead=snapped if RUIN else None, trunk=(0.5, 8.0))
    for v in range(2):
        paint.scatter(c, props.jungle_tree(c, v), 170, rmax, jungle, g, taken, 20 + v, room=7.0, scale=(1.0, 1.9), road_margin=6.0,
                      trunk=(0.8, 6.0))
        paint.scatter(c, bp.coconut_palm(c, v), 40, rmax, jungle, g, taken, 24 + v, room=6.0, road_margin=5.0,
                      instead=snapped if RUIN else None, trunk=(0.5, 8.0))
        paint.scatter(c, props.bush(c, v), 160, rmax, jungle, g, taken, 30 + v, room=3.0, role="visual")
        paint.scatter(c, props.big_leaf_plant(c, v), 120, rmax, jungle, g, taken, 33 + v, room=2.5, role="visual")
    paint.scatter(c, props.fern(c), 300, rmax, jungle, g, taken, 35, room=2.0, role="visual")
    for k, p in enumerate((bp.starfish(c, 0), bp.starfish(c, 1), bp.shell(c))):
        paint.scatter(c, p, 30, rmax, beach, g, taken, 40 + k, room=1.0, role="visual", sink=0.05)
    if RUIN:
        return
    co = look("coral")
    for k, (p, n) in enumerate(((bp.umbrella(c, 0), 8), (bp.umbrella(c, 1), 8), (bp.deck_chair(c, 0), 10), (bp.towel(c, 0), 8),
                                (bp.canoe(c, 0), 4))):
        paint.scatter(c, p, n, rmax, co, g, taken, 50 + k, room=3.0, role="visual", sink=0.05)
    for v in range(2):
        paint.scatter(c, tp.beach_hut(c, v), 2, rmax, co, g, taken, 56 + v, room=10.0, road_margin=7.0)
    sw = look("wreck")
    for v in range(2):
        paint.scatter(c, tp.pirate_hut(c, v), 2, rmax, sw, g, taken, 60 + v, room=10.0, road_margin=7.0)
    paint.scatter(c, tp.barrel(c), 10, rmax, sw, g, taken, 62, room=3.0, road_margin=4.0)
    paint.scatter(c, tp.cannon(c), 3, rmax, sw, g, taken, 63, room=5.0, road_margin=5.0)
    paint.scatter(c, tp.rowboat(c), 5, rmax, lambda x, y: beach(x, y) and M.inland(x, y) < 16.0, g, taken, 64, room=6.0,
                  road_margin=5.0)


if __name__ == "__main__":
    main()
