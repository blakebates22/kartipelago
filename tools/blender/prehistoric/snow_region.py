# The Snow Kingdom, the overworld's second region (v3): built from snow_layout.py's
# pockets (Blake, Oct 26: each world walled off by landscape, the main road one loop through
# them by a threshold each time; see snow_layout.py for the plan).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/snow_region.py [--ruin]      (the bpy module)
#
# (--ruin: after Rimefang's attack. Only the ruin has his lair, the road out through the
# Frozen Pass (his ice across it is the game's, regions.ts's blocker, until he falls), the
# village frozen over, ice shards driven into the fields, the pines frozen solid.)

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp, smooth  # noqa: E402
import region_ruin as ruin  # noqa: E402
import puzzle_kit  # noqa: E402
import pocket_build as pb  # noqa: E402
from pocket_build import box, cone  # noqa: E402
import hearthglow_props as hp  # noqa: E402
import summit_props as sp  # noqa: E402
import aurora_props as ap  # noqa: E402
import keep_props as kp  # noqa: E402
import winter_props as wp  # noqa: E402
import region_paint as paint  # noqa: E402
import snow_layout as SL  # noqa: E402

RUIN = ruin.ON
TRACK_ID = ruin.track_id("snow_region") + os.environ.get("KP_REGION_SUFFIX", "")
L = SL.L
HUB = SL.HUB
FLOOR_Z = HUB[3]  # (the village's height: the old name)
RIM_Z = SL.TOP
GORGE_HW = 16.0

# The Ice Bells (src/overworld/puzzles.ts): a frost-stone hut on an island in the frozen
# lake, its ice door shut, and three bells out on the ice round it to ring in order (their
# lanterns: one, two, three).
HUT = (118.0, -92.0)
HUT_HALF = 10.0
HUT_GAP = 4.5
BELLS = [(90.0, -60.0), (150.0, -112.0), (104.0, -132.0)]
LANTERNS = [1, 2, 3]
# Brachio's hot spring (Act V's return task): a walled yard in the summit meadow, frozen shut.
RETURN = (-102.0, 268.0)
# A secret (regions.ts secret): an old store in Frostveil's bailey, buried under a drift
# (the Desert Tool's).
SECRET = (-195.0, -102.0)

LOOK = {
    # look: (ground, cliff, road, shoulder)
    "hearth": (("snow_ground", "deep_snow"), ("frost_cliff", "wall"), "hearth_cobble", ("snow_ground", "deep_snow")),
    "frostveil": (("snow_ground", "deep_snow"), ("frost_rock", "wall"), "snow_stone_road", ("snow_ground", "deep_snow")),
    "summit": (("summit_snow", "deep_snow"), ("summit_cliff", "wall"), "summit_road", ("summit_snow", "deep_snow")),
    "aurora": (("rift_snow", "deep_snow"), ("glacier_wall", "wall"), "rift_road", ("rift_snow", "deep_snow")),
    "lake": (("snow_ground", "deep_snow"), ("frost_cliff", "wall"), "packed_snow_road", ("snow_ground", "deep_snow")),
}


def gorge_x(y):
    return 6.0 * math.sin(max(0.0, -y - 300.0) / 40.0)


def natural(x, y):
    h = SL.natural(x, y)
    tz = L.tunnel_floor(x, y)
    if tz is not None:
        h = min(h, tz - 0.25)  # (under a tunnel's rock: flush under its road, out to the walls)
    # The Ice Bells' island in the lake.
    d = math.hypot(x - HUT[0], y - HUT[1])
    if d < 26:
        h = max(h, lerp(SL.LAKE[3] + 0.5, h, smooth((d - 14.0) / 12.0)))
    if RUIN:
        # The Frozen Pass: a slot through the mountains east, out of the lake.
        (ax, ay), (bx, by) = SL.FROZEN_PASS, SL.PASS_END
        dd, t = pb_seg(x, y, (ax - 30.0, ay + 10.0), (bx, by))
        if dd < 30:
            h = lerp(h, SL.LAKE[3] + 0.3 + 6.0 * t, smooth((30.0 - dd) / 12.0))
        # Rimefang's lair: a cleft in the summit's north wall.
        lx, ly = SL.LAIR
        dd, t = pb_seg(x, y, (lx, ly - 40.0), (lx, ly + 26.0))
        if dd < 26:
            h = lerp(h, 57.0 + 2.0 * t, smooth((26.0 - dd) / 10.0))
    return h


def pb_seg(x, y, a, b):
    from pocket_kit import seg_d
    return seg_d(x, y, a, b)


def classify(c, n, info):
    look = L.look_at(c.x, c.y)
    ground, cliff, _, _ = LOOK[look]
    if n.z < 0.62:
        if c.y < -290 and abs(c.x - gorge_x(c.y)) < GORGE_HW + 40:
            return ("obsidian_cliff", "wall")  # (the Burnt Gorge's scorched walls)
        return cliff
    lx, ly, lr, lz = SL.LAKE
    if math.hypot(c.x - lx, c.y - ly) < lr + 2 and c.z < lz + 0.1:
        return ("lake_ice", "ice")
    if RUIN and look in ("hearth", "summit", "frostveil") and math.sin(c.x / 23.0) * math.cos(c.y / 19.0) > 0.55:
        return ("berg_ice", "ice")  # (Rimefang's frost)
    return ground


def main():
    c = kit.Course(TRACK_ID, "Snow Kingdom (ruined)" if RUIN else "Snow Kingdom", "summit_pass")
    c.route(L.route_points(), width=14.0, bank=5.0)
    kinds = {}
    for look, (ground, cliff, road, shoulder) in LOOK.items():
        kinds[look] = {"mat": road, "shoulder": 1.5, "shoulder_mat": shoulder}
    c.kinds = kinds
    c.roads(kit.plan(c, list(kit.runs(c, lambda smp: L.look_at(smp.p.x, smp.p.y))), "hearth", max_len=160.0))

    snow = ("snow_ground", "deep_snow")
    trail = dict(width=10.0, shoulder=1.2, shoulder_mat=snow)
    cx, cy, cr, cz = HUB
    # Out of the square onto the road (north), and down the Burnt Gorge to the valley (south).
    smp, _ = c.nearest(cx, cy + cr + 20.0)
    c.side_road("Square Road", list(reversed(pb.line(natural, (smp.p.x, smp.p.y), (cx, cy + cr - 2.0), z0=smp.p.z))),
                "hearth_cobble", "road", **trail)
    gx, gy = SL.GORGE_END
    gorge = [(gorge_x(y), y, natural(gorge_x(y), y) + 0.2) for y in range(int(cy - cr + 2), int(gy + 6), -8)]
    c.side_road("Burnt Gorge Road", gorge, "packed_snow_road", "road", **trail)
    gates = dict(SL.GATES)
    if RUIN:
        gates["lair"] = SL.LAIR
    spots = pb.spurs(c, natural, gates, lambda x, y: LOOK[L.look_at(x, y)][2], trail)
    if RUIN:
        # Out of the lake through the Frozen Pass, east.
        smp, _ = c.nearest(*SL.FROZEN_PASS)
        (ax, ay), (bx, by) = SL.FROZEN_PASS, SL.PASS_END
        way = pb.line(natural, (smp.p.x, smp.p.y), (bx - 10.0, by), z0=smp.p.z)
        c.side_road("Frozen Pass Road", way, "packed_snow_road", "road", **trail)

    X0, X1, Y0, Y1 = -480, 480, -490, 480
    ter = c.terrain("Snow Kingdom", X0, X1, Y0, Y1, 5.0, natural, classify, near=8.0, fade=16.0)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 5.0, lambda x, y: natural(x, y) - 0.5, c.lib(*snow))

    def ground(x, y):
        z = c.ground_z(x, y, [ter])
        return natural(x, y) if z is None else z

    lx, ly, lr, lz = SL.LAKE
    c.disc("Frozen Lake", lx, ly, lr + 4.0, lz - 0.05, c.lib("lake_ice", "ice"), role="visual", n=48, wobble=0.06)

    thresholds(c, ground)
    village(c, ground)
    landmarks(c, ground, spots)
    if RUIN:
        ruined(c, ground)
    ice_bells(c, ground)
    puzzle_kit.pen(c, "return", "Hot Spring", *RETURN, pb.to_road(c, *RETURN), 11.0, 4.5, ("frost_stone", "wall"),
                   ground(*RETURN), height=6.0)
    puzzle_kit.pen(c, "secret", "Old Store", *SECRET, pb.to_road(c, *SECRET), 9.0, 4.5, ("citadel_stone", "wall"),
                   ground(*SECRET), height=6.0)
    pb.emit_spots(c, spots)
    dress(c, ground, spots)
    # The gorge's far end, back towards the valley: it bends out of sight.
    box(c, "Gorge Bend", gorge_x(gy - 8), gy - 8, GORGE_HW + 24.0, 6.0, natural(0, gy) - 2.0, RIM_Z + 20.0,
        ("obsidian_cliff", "wall"))
    c.entity("snowfall", rate=60, radius=60)

    # (Raced too: the champion's challenge, once round the loop, from this line.)
    c.start_line()
    gts = c.checkpoints(height=10.0)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish(extra={"race": {"laps": 1}})
    print("loop", round(c.length, 1), "gates", len(gts))


def thresholds(c, ground):
    """The Gatehouse (through Frostveil's curtain wall, a castle gate at each end), the Ice
    Cave (blue ice, crystals in its walls), the Frozen Falls (a tunnel up behind a frozen
    waterfall into the village), and the Snowshed (a timber avalanche gallery down the
    cliff to the lake)."""
    kp.use_palette({"keep_ashlar": "citadel_stone", "keep_ashlar_dark": "citadel_dark", "keep_parapet": "citadel_stone",
                    "keep_gold": "temple_gold", "keep_banner": "banner_teal", "keep_pine": "pine_snow"})
    for name, kind, a, b in L.tunnels:
        s0, s1 = pb.tunnel_span(c, L, a, b)
        if kind == "gatehouse":
            half = pb.bore(c, L, name, s0, s1, ("citadel_stone", "wall"), ("snow_ground", "deep_snow"), height=11.0)
            arch = kp.gate_arch(c, span=2 * half + 6.0, clear=11.0, depth=7.0)
            tower = kp.round_tower(c, r=4.5, h=24.0)
            for k, s in enumerate((s0 - 3.0, s1 + 3.0)):
                q = c.at(s)
                rot = math.atan2(q.t.y, q.t.x) - math.pi / 2
                c.place(arch, q.p.x, q.p.y, q.p.z - 0.2, rot=rot, role="visual")
                for sd in (-1, 1):
                    x, y = q.p.x + q.r.x * sd * (half + 6.5), q.p.y + q.r.y * sd * (half + 6.5)
                    c.place(tower, x, y, ground(x, y) - 0.5, rot=rot)
            for k in range(3):
                q = c.at(s0 + (s1 - s0) * (k + 0.5) / 3)
                for sd in (-1, 1):
                    x, y = q.p.x + q.r.x * sd * (half - 0.6), q.p.y + q.r.y * sd * (half - 0.6)
                    g = c.game(x, y, q.p.z + 4.5)
                    c.entity("torch", x=g[0], y=g[1], z=g[2])
        elif kind == "ice":
            half = pb.bore(c, L, name, s0, s1, ("cavern_ice", "wall"), ("summit_snow", "deep_snow"), height=11.0)
            crystals = [ap.fan(c, v, size=5.0, mat=m) for v, m in ((0, ap.CYAN), (1, ap.VIOLET), (2, ap.TEAL))]
            s = s0 + 5.0
            k = 0
            while s < s1 - 4.0:
                q = c.at(s)
                sd = 1 if k % 2 else -1
                x, y = q.p.x + q.r.x * sd * (half - 0.3), q.p.y + q.r.y * sd * (half - 0.3)
                c.place(crystals[k % 3], x, y, q.p.z + 1.0 + 3.0 * (k % 2), rot=math.atan2(q.r.y, q.r.x) * sd,
                        role="visual")
                g = c.game(x, y, q.p.z + 5.0)
                c.entity("lantern", x=g[0], y=g[1], z=g[2])
                s += 9.0
                k += 1
            for s in (s0 - 2.0, s1 + 2.0):
                q = c.at(s)
                c.place(ap.icicle_fringe(c, 0, width=2 * half, length=4.0), q.p.x, q.p.y, q.p.z + 10.5,
                        rot=math.atan2(q.t.y, q.t.x) - math.pi / 2, role="visual")
        else:  # the Frozen Falls
            half = pb.bore(c, L, name, s0, s1, ("frost_cliff", "wall"), ("snow_ground", "deep_snow"), height=10.0)
            q = c.at(s0 - 4.0)  # (the lake side: the falls pour down either side of the mouth)
            for sd in (-1, 1):
                x, y = q.p.x + q.r.x * sd * (half + 12.0), q.p.y + q.r.y * sd * (half + 12.0)
                foot = ground(x, y)
                wp.ice_fall(c, "%s %d" % (name, sd), x, y, foot + 22.0, foot - 0.5, 14.0, facing=(-q.t.x, -q.t.y))
            c.place(ap.icicle_fringe(c, 1, width=2 * half + 4.0, length=5.0), q.p.x, q.p.y, q.p.z + 9.5,
                    rot=math.atan2(q.t.y, q.t.x) - math.pi / 2, role="visual")
            for k in range(3):
                q = c.at(s0 + (s1 - s0) * (k + 0.5) / 3)
                g = c.game(q.p.x + q.r.x * (half - 0.6), q.p.y + q.r.y * (half - 0.6), q.p.z + 4.5)
                c.entity("lantern", x=g[0], y=g[1], z=g[2])
    snowshed(c, ground)


def snowshed(c, ground):
    """The Snowshed: down the cliff from the glacier to the lake, a timber gallery over the
    road (posts on the open, lake side; its roof sloping back into the cliff)."""
    a = SL.ROUTE[33]
    b = SL.ROUTE[35]
    s0 = c.nearest(*a[:2])[0].s
    s1 = c.nearest(*b[:2])[0].s
    if s1 < s0:
        s1 += c.length
    timber = ("weathered_timber", "wall")
    s = s0
    k = 0
    while s < s1:
        q = c.at(s)
        half = q.w / 2 + 2.0
        # Which side is the cliff (the higher ground)?
        hl = ground(q.p.x - q.r.x * (half + 8), q.p.y - q.r.y * (half + 8))
        hr = ground(q.p.x + q.r.x * (half + 8), q.p.y + q.r.y * (half + 8))
        out = 1 if hr < hl else -1
        rot = math.atan2(q.r.y, q.r.x)
        x, y = q.p.x + q.r.x * out * half, q.p.y + q.r.y * out * half
        box(c, "Snowshed Post %d" % k, x, y, 0.5, 0.5, q.p.z - 1.0, q.p.z + 7.0, timber, rot=rot)
        # (the roof: from over the posts up into the cliff, visual)
        rx, ry = q.p.x + q.r.x * -out * 2.0, q.p.y + q.r.y * -out * 2.0
        box(c, "Snowshed Roof %d" % k, rx, ry, half + 5.0, 3.4, q.p.z + 7.0, q.p.z + 7.5, timber, rot=rot, role="visual")
        box(c, "Snowshed Snow %d" % k, rx, ry, half + 5.2, 3.5, q.p.z + 7.5, q.p.z + 8.2, ("snow_ground", "deep_snow"),
            rot=rot, role="visual")
        if k % 2 == 0:
            g = c.game(x, y, q.p.z + 6.0)
            c.entity("lantern", x=g[0], y=g[1], z=g[2])
        s += 6.0
        k += 1


def village(c, ground):
    """Hearthglow: the town square in its hollow, the cottages round it, the great tree, the
    stalls, the bell tower, lanterns (after the attack: frozen solid, the tree iced)."""
    cx, cy, cr, cz = HUB
    c.disc("Village Square", cx, cy, cr, cz + 0.05, c.lib("hearth_cobble", "road"), coll="Props", n=40)
    for k in range(8):
        a = k * math.tau / 8 + math.pi / 8
        if math.sin(a) > 0.75 or math.sin(a) < -0.8:
            continue  # (clear of the ways in: north to the road, south to the gorge)
        hx, hy = cx + (cr + 7) * math.cos(a), cy + (cr + 7) * math.sin(a)
        if not paint.road_clear(c, hx, hy, 6.0):
            continue
        if RUIN:
            box(c, "House %d" % k, hx, hy, 4.5, 3.5, cz - 1.0, cz + 4.0, ("hearth_stone", "wall"), rot=a)
            box(c, "House Ice %d" % k, hx, hy, 5.4, 4.4, cz - 1.0, cz + 6.5, ("berg_ice", "wall"), rot=a + 0.08)
            continue
        c.place(hp.cottage(c, k % 4), hx, hy, ground(hx, hy) - 0.2, rot=a - math.pi / 2)
    gx, gy = SL.GATES["hearthglow"]
    if RUIN:
        box(c, "Great Tree Trunk", gx, gy, 1.6, 1.6, ground(gx, gy) - 1.0, ground(gx, gy) + 8.0, ("weathered_timber", "wall"))
        for k, (r, z) in enumerate(((8.0, 6.0), (6.0, 12.0), (4.0, 17.0))):
            cone(c, "Great Tree Ice %d" % k, gx, gy, r, ground(gx, gy) + z, 6.0, ("glacier_ice", "wall"), segs=8,
                 role="visual")
    else:
        hp.giant_tree(c, "Great Tree", gx, gy, ground(gx, gy), height=34.0)
    g = c.game(cx, cy, cz + 0.3)
    c.entity("campfire", x=g[0], y=g[1], z=g[2])
    if not RUIN:
        tower = hp.bell_tower(c)
        c.place(tower, cx + 18.0, cy - 30.0, ground(cx + 18.0, cy - 30.0) - 0.2, rot=math.pi)
        for k in range(3):
            a = 0.9 + 0.5 * k
            x, y = cx + (cr - 4) * math.cos(-a), cy + (cr - 4) * math.sin(-a)
            c.place(hp.stall(c, k % 2), x, y, cz, rot=-a + math.pi / 2)


def landmarks(c, ground, spots):
    """Each world's landmark, its gateway in front of it: Frostveil's keep, the summit's
    giant tree and shipwreck, the rift in the glacier."""
    def facing(name):
        (ex, ey), _ = spots[name]
        gx, gy = SL.GATES[name] if name in SL.GATES else SL.LAIR
        return math.atan2(gy - ey, gx - ex)

    # Frostveil Citadel: the keep behind its gate.
    gx, gy = SL.GATES["frostveil"]
    f = facing("frostveil")
    keep = kp.keep_block(c, w=30.0, d=20.0, h=30.0)
    c.place(keep, gx + 14.0 * math.cos(f), gy + 14.0 * math.sin(f), ground(gx, gy) - 0.5, rot=f + math.pi / 2)
    arch = kp.gate_arch(c, span=16.0, clear=9.0, depth=5.0)
    c.place(arch, gx, gy, ground(gx, gy) - 0.3, rot=f - math.pi / 2, role="visual")
    box(c, "Keep Gate Dark", gx + 2.0 * math.cos(f), gy + 2.0 * math.sin(f), 6.0, 1.0, ground(gx, gy) - 1.0,
        ground(gx, gy) + 9.0, ("dark_corridor", "wall"), rot=f + math.pi / 2, role="visual")
    # Snowy Summit: the giant tree.
    gx, gy = SL.GATES["summit"]
    z = ground(gx, gy)
    box(c, "Giant Tree Trunk", gx, gy, 6.0, 6.0, z - 2.0, z + 50.0, ("giant_bark", "wall"))
    for k, (r, h) in enumerate(((24.0, 34.0), (18.0, 48.0), (12.0, 60.0))):
        cone(c, "Giant Tree Crown %d" % k, gx, gy, r, z + h, 18.0, ("glacier_ice" if RUIN else "pine_snow", "wall"), segs=8,
             role="visual")
    # Aurora Rift: the crack in the glacier, ice spires either side, the sky alight.
    gx, gy = SL.GATES["aurora"]
    f = facing("aurora")
    z = ground(gx, gy)
    box(c, "Rift Crack", gx + 3.0 * math.cos(f), gy + 3.0 * math.sin(f), 5.0, 1.0, z - 1.0, z + 22.0, ("icefall_rift", "wall"),
        rot=f + math.pi / 2, role="visual")
    for sd in (-1, 1):
        x, y = gx + sd * 12.0 * math.cos(f + math.pi / 2), gy + sd * 12.0 * math.sin(f + math.pi / 2)
        c.place(ap.spire_cluster(c, 0 if sd < 0 else 1, height=34.0), x, y, ground(x, y) - 0.5, role="visual")
        c.place(paint.trunk_proto(c, 5.0, 16.0), x, y, ground(x, y) - 0.5, coll="Collision", role="collision")
    g = c.game(gx, gy, z + 30.0)
    c.entity("sparkles", rate=12, radius=40)


def ruined(c, ground):
    """After Rimefang's attack: his lair (ice teeth round a dark mouth in the summit's north
    wall), the cleft of the Frozen Pass, ice shards in the fields."""
    lx, ly = SL.LAIR
    z = ground(lx, ly)
    box(c, "Lair Mouth", lx, ly + 4.0, 8.0, 2.0, z - 1.0, z + 12.0, ("dark_corridor", "wall"), role="visual")
    for k in range(7):
        t = (k - 3) / 3.0
        if abs(t) < 0.4:
            continue
        px, py = lx + t * 13.0, ly + 2.0
        cone(c, "Lair Ice %d" % k, px, py, 3.0 + abs(t) * 1.5, ground(px, py) - 1.0, 10.0 + 8.0 * (1 - abs(t)),
             ("glacier_ice", "wall"), segs=5)
    bx, by = SL.PASS_END
    box(c, "Frozen Pass Bend", bx + 6.0, by, 6.0, 40.0, natural(bx, by) - 2.0, RIM_Z + 20.0, ("frost_cliff", "wall"))
    spots = []
    for k in range(40):
        a = k * 2.399
        r = 60.0 + 380.0 * ((k * 0.618) % 1.0)
        x, y = r * math.cos(a), r * math.sin(a)
        if L.wall_sd(x, y) < -16 and paint.road_clear(c, x, y, 8.0):
            spots.append((x, y))
    ruin.shards(c, "Ice Shard", spots, ground, ("glacier_ice", "wall"), seed=7)


def ice_bells(c, ground):
    puzzle_kit.pen(c, "ice_bells", "Bell Hut", *HUT, pb.to_road(c, *HUT), HUT_HALF, HUT_GAP, ("frost_stone", "wall"),
                   ground(*HUT), roof=("pine_snow", "wall"), height=6.0)
    puzzle_kit.switches(c, "ice_bells", BELLS, ground, lanterns=LANTERNS)


def dress(c, ground, spots):
    """The paint pass, world by world: the village's lantern posts, Christmas pines and
    snowmen; the bailey's curtain walls, towers, braziers and banners; the summit's pines,
    broadleaves, boulders, the frozen shipwreck and the mammoth's tusk gate; the glacier's
    ice columns, spires and crystal gardens; the lake's icebergs. After the attack: the
    pines frozen into ice, the undergrowth gone."""
    taken = paint.Taken([(HUB[0], HUB[1], HUB[2] + 10.0), (*HUT, 26.0), (*RETURN, 18.0), (*SECRET, 16.0),
                         *((x, y, 9.0) for x, y in BELLS), *((e[0], e[1], 16.0) for e, _ in spots.values()),
                         *((x, y, 26.0) for x, y in SL.GATES.values()), (*SL.LAIR, 24.0)])

    def inside(x, y):
        if L.wall_sd(x, y) > -8:
            return False
        lx, ly, lr, _ = SL.LAKE
        return math.hypot(x - lx, y - ly) > lr + 6

    def look(name):
        return lambda x, y: inside(x, y) and L.look_at(x, y) == name

    rmax = 470.0
    g = ground
    pines = [sp.pine(c, v, 12.0 + 4.0 * v, snowy=True) for v in range(3)]
    for name in ("hearth", "frostveil", "summit", "lake"):
        for v in range(2):
            paint.scatter(c, sp.boulder(c, v), 6, rmax, lambda x, y, n=name: look(n)(x, y) and L.wall_sd(x, y) > -30, g,
                          taken, 90 + v + len(name), room=4.0, scale=(1.0, 2.2), road_margin=9.0)
    if RUIN:
        for v, p in enumerate(pines):
            for x, y in paint.scatter(c, p, 50, rmax, lambda x, y: inside(x, y) and L.look_at(x, y) != "aurora", g, taken,
                                      10 + v, room=5.0, scale=(0.9, 1.4), road_margin=7.0):
                cone(c, "Frozen Pine %d %d" % (v, int(x)), x, y, 3.2, g(x, y) - 0.5, 9.0 + 3.0 * v, ("glacier_ice", "wall"),
                     segs=6, role="visual")
        return
    # Hearthglow: Christmas pines with lights, lantern posts along the road, snowmen.
    hub = look("hearth")
    for v in range(2):
        paint.scatter(c, hp.xmas_pine(c, v, height=12.0 + 3.0 * v), 10, rmax, hub, g, taken, 60 + v, room=6.0,
                      road_margin=6.0, trunk=(0.8, 6.0))
    post = hp.lantern_post(c, 0)
    for x, y in paint.scatter(c, post, 10, rmax, hub, g, taken, 62, room=10.0, near_road=(3.0, 5.0)):
        gx, gy, gz = c.game(x, y, g(x, y) + 4.6)
        c.entity("lantern", x=gx, y=gy, z=gz)
    paint.scatter(c, hp.snowman(c, 0), 5, rmax, hub, g, taken, 63, room=3.0)
    # Frostveil: towers and curtain walls round the bailey's edge, braziers, banners.
    fv = look("frostveil")
    for x, y in paint.scatter(c, kp.round_tower(c, r=4.0, h=20.0), 8, rmax,
                              lambda x, y: fv(x, y) and L.wall_sd(x, y) > -16, g, taken, 70, room=26.0, road_margin=10.0):
        pass
    wall = kp.curtain_wall(c, length=18.0, h=10.0)
    for x, y in paint.scatter(c, wall, 10, rmax, lambda x, y: fv(x, y) and L.wall_sd(x, y) > -14, g, taken, 71, room=14.0,
                              road_margin=10.0):
        pass
    for x, y in paint.scatter(c, kp.brazier(c), 8, rmax, fv, g, taken, 72, room=8.0, near_road=(3.0, 6.0)):
        gx, gy, gz = c.game(x, y, g(x, y) + 2.4)
        c.entity("torch", x=gx, y=gy, z=gz)
    paint.scatter(c, kp.banner_pole(c), 8, rmax, fv, g, taken, 73, room=8.0, near_road=(3.0, 6.0))
    for v, p in enumerate(pines[:2]):
        paint.scatter(c, p, 14, rmax, fv, g, taken, 74 + v, room=6.0, scale=(0.9, 1.3), road_margin=7.0, trunk=(0.8, 6.0))
    # The summit: pines, broadleaves, shrubs, the frozen shipwreck, the tusk gate over the road.
    su = look("summit")
    for v, p in enumerate(pines):
        paint.scatter(c, p, 40, rmax, su, g, taken, 10 + v, room=5.0, scale=(0.9, 1.5), road_margin=7.0, trunk=(0.8, 6.0))
    for v in range(2):
        paint.scatter(c, sp.broadleaf(c, v, frosted=True), 12, rmax, su, g, taken, 30 + v, room=5.0, road_margin=7.0,
                      trunk=(0.9, 6.0))
        paint.scatter(c, sp.shrub(c, v), 50, rmax, su, g, taken, 40 + v, room=2.5, role="visual", scale=(0.7, 1.4))
    paint.scatter(c, sp.shipwreck(c), 1, rmax, lambda x, y: su(x, y) and L.wall_sd(x, y) < -24, g, taken, 44, room=40.0,
                  road_margin=18.0)
    paint.scatter(c, sp.lookout_hut(c), 2, rmax, su, g, taken, 45, room=10.0, road_margin=8.0)
    # The glacier: ice columns, spires, crystal gardens, ice spikes.
    au = look("aurora")
    for v in range(2):
        paint.scatter(c, ap.ice_column(c, v, height=30.0, radius=4.0), 6, rmax,
                      lambda x, y: au(x, y) and L.wall_sd(x, y) > -24, g, taken, 80 + v, room=14.0, road_margin=10.0)
        paint.scatter(c, ap.spire_cluster(c, v, height=22.0), 5, rmax, au, g, taken, 82 + v, room=14.0, road_margin=10.0,
                      trunk=(4.0, 12.0))
        paint.scatter(c, ap.ice_spike(c, v, height=10.0), 14, rmax, au, g, taken, 84 + v, room=5.0, road_margin=6.0)
    paint.scatter(c, ap.garden(c, 0, radius=8.0), 4, rmax, au, g, taken, 86, room=14.0, road_margin=9.0, role="visual")
    # The lake: pines on its shores, icebergs frozen in the ice.
    la = look("lake")
    for v, p in enumerate(pines[:2]):
        paint.scatter(c, p, 16, rmax, la, g, taken, 50 + v, room=6.0, scale=(0.9, 1.3), road_margin=7.0, trunk=(0.8, 6.0))
    lx, ly, lr, lz = SL.LAKE
    for k in range(5):
        a = k * 1.3 + 0.5
        x, y = lx + lr * 0.75 * math.cos(a), ly + lr * 0.75 * math.sin(a)
        if taken.clear(x, y, 10.0) and paint.road_clear(c, x, y, 8.0):
            c.place(sp.iceberg(c, k % 2), x, y, lz - 0.4, rot=a)
            taken.add(x, y, 10.0)


if __name__ == "__main__":
    main()
