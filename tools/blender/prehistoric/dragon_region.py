# The Dragon Kingdom, the overworld's last region (v3): built from dragon_layout.py's
# pockets (Blake, Oct 26: each world walled off by landscape, the main road one loop
# through them by a threshold each time; see dragon_layout.py for the plan).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/dragon_region.py [--ruin]      (the bpy module)
#
# (--ruin: the kingdom after the sacrifice: scorched where the fire fell, smoke, the great
# statue broken, rubble at every gate, the same trees charred.)

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import pocket_kit  # noqa: E402
import region_ruin as ruin  # noqa: E402
import pocket_build as pb  # noqa: E402
from pocket_build import box, cone  # noqa: E402
import keep_props as kp  # noqa: E402
import villager_homes as vh  # noqa: E402
import isles_props as ip  # noqa: E402
import cdf_props as cdp  # noqa: E402
import props  # noqa: E402
import region_paint as paint  # noqa: E402
import ruin_kit  # noqa: E402
import dragon_layout as DL  # noqa: E402

RUIN = ruin.ON
TRACK_ID = ruin.track_id("dragon_region") + os.environ.get("KP_REGION_SUFFIX", "")
L = DL.L
HUB = DL.HUB
FLOOR_Z = HUB[3]
WATER_Z = DL.WATER_Z
RIM_Z = DL.TOP

LOOK = {
    # look: (ground, cliff, road, shoulder)
    "harbour": (("keep_grass", "grass"), ("keep_rock", "wall"), "keep_cobble", ("keep_path", "dirt")),
    "moon": (("moon_grass", "grass"), ("moon_rock", "wall"), "moon_paving", ("moon_grass", "grass")),
    "keep": (("keep_grass", "grass"), ("keep_rock_moss", "wall"), "keep_flag", ("keep_path", "dirt")),
    "citadel": (("ember_moss", "grass"), ("ember_rock", "wall"), "keep_flag", ("keep_path", "dirt")),
    "hold": (("ember_rubble", "dirt"), ("ember_rock", "wall"), "ember_setts", ("ember_path", "dirt")),
    "canyon": (("em_jungle_grass", "grass"), ("em_cliff", "wall"), "em_road", ("em_verge", "grass")),
}


def burn(x, y):
    """Where the sacrifice's fire fell (0 none .. 1)."""
    return 0.55 + 0.45 * math.sin(x / 61.0 - 0.7) * math.cos(y / 43.0 + 1.1)


def _natural(x, y):
    h = DL.natural(x, y)
    tz = L.tunnel_floor(x, y)
    if tz is not None:
        h = min(h, tz - 0.25)
    return h


# The ways in to the gateways cut level with the road (pocket_kit.Notches: a gateway's
# spur mustn't climb a wall).
NOTCHES = pocket_kit.Notches(DL.route_points(), dict(DL.GATES, citadel=DL.CITADEL))


def natural(x, y):
    return NOTCHES.apply(_natural(x, y), x, y)


def classify(c, n, info):
    look = L.look_at(c.x, c.y)
    ground, cliff, _, _ = LOOK[look]
    if n.z < 0.62:
        return cliff
    if c.z < WATER_Z + 0.3:
        return ("keep_lake_shallow", "water")
    if look == "harbour" and c.z < WATER_Z + 1.4:
        return ("keep_shore", "sand")
    if RUIN and burn(c.x, c.y) > 0.55:
        return ("scorched_ground", "dirt")
    return ground


def main():
    c = kit.Course(TRACK_ID, "Dragon Kingdom (ruined)" if RUIN else "Dragon Kingdom", "dragon_isles")
    c.route(L.route_points(), width=14.0, bank=5.0)
    kinds = {}
    for look, (ground, cliff, road, shoulder) in LOOK.items():
        kinds[look] = {"mat": road, "shoulder": 1.5, "shoulder_mat": shoulder}
    c.kinds = kinds
    c.roads(kit.plan(c, list(kit.runs(c, lambda smp: L.look_at(smp.p.x, smp.p.y))), "harbour", max_len=160.0))

    trail = dict(width=10.0, shoulder=1.2, shoulder_mat=("keep_path", "dirt"))
    cx, cy, cr, cz = HUB
    # The Causeway in from the sea onto the square's south side.
    ex, ey = DL.CAUSEWAY_END
    way = [(0.0, y, max(natural(0.0, y), WATER_Z + 1.4) + 0.2) for y in range(int(ey + 6), int(cy - cr + 2), 8)]
    c.side_road("Causeway", way, "keep_cobble", "road", width=10.0, shoulder=0.6, shoulder_mat=("keep_ashlar", "road"),
                barrier=0.6, barrier_mat=("keep_ashlar", "wall"), deck=1.4, deck_mat=("keep_ashlar", "wall"), ground=False)
    box(c, "Causeway End", 0.0, ey - 4.0, 12.0, 3.0, WATER_Z - 4.0, WATER_Z + 14.0, ("keep_rock", "wall"))
    gates = dict(DL.GATES)
    gates["citadel"] = DL.CITADEL
    spots = pb.spurs(c, natural, gates, lambda x, y: LOOK[L.look_at(x, y)][2], trail)

    X0, X1, Y0, Y1 = -490, 490, -490, 480
    ter = c.terrain("Dragon Kingdom", X0, X1, Y0, Y1, 5.0, natural, classify, near=8.0, fade=16.0)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 5.0, lambda x, y: natural(x, y) - 0.5, c.lib("keep_grass", "grass"))
    c.disc("Sea", 0.0, -500.0, 900.0, WATER_Z, c.lib("keep_lake", "water"), role="visual", n=48)

    def ground(x, y):
        z = c.ground_z(x, y, [ter])
        return natural(x, y) if z is None else z

    thresholds(c, ground)
    square(c, ground)
    landmarks(c, ground, spots)
    pb.emit_spots(c, spots)
    # The villagers' homes, in every part of the region (src/overworld/villagers.ts).
    vh.homes(c, L, ground, "dragon", vh.proto_house(lambda c, k: kp.house(c, k % 4)), avoid=[(HUB[0], HUB[1], HUB[2] + 22.0)])
    dress(c, ground, spots)
    if RUIN:
        ruined(c, ground, spots)
    else:
        c.entity("storm", period=9, spread=5, distance=900)

    c.start_line()
    gts = c.checkpoints(height=10.0)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish(extra={"race": {"laps": 1}})
    print("loop", round(c.length, 1), "gates", len(gts))


def thresholds(c, ground):
    """The Dragon Gate and the Keep Gate (castle gates at both ends, banners), the Lava Tube
    (lava glowing in its walls), the Root Tunnel (roots and vines)."""
    for name, kind, a, b in L.tunnels:
        s0, s1 = pb.tunnel_span(c, L, a, b)
        if kind == "gate":
            half = pb.bore(c, L, name, s0, s1, ("keep_ashlar", "wall"), ("keep_grass", "grass"), height=11.0)
            arch = kp.gate_arch(c, span=2 * half + 6.0, clear=11.0, depth=7.0)
            tower = kp.round_tower(c, r=4.5, h=24.0)
            for s in (s0 - 3.0, s1 + 3.0):
                q = c.at(s)
                rot = math.atan2(q.t.y, q.t.x) - math.pi / 2
                c.place(arch, q.p.x, q.p.y, q.p.z - 0.2, rot=rot, role="visual")
                for sd in (-1, 1):
                    x, y = q.p.x + q.r.x * sd * (half + 6.5), q.p.y + q.r.y * sd * (half + 6.5)
                    c.place(tower, x, y, ground(x, y) - 0.5, rot=rot)
        elif kind == "lava":
            half = pb.bore(c, L, name, s0, s1, ("ember_rock", "wall"), ("ember_moss", "grass"), height=11.0)
            for sd in (-1, 1):
                strip = []
                s = s0 + 4.0
                while s < s1 - 4.0:
                    q = c.at(s)
                    off = c.width / 2 + 2.2
                    strip.append((q.p.x + q.r.x * sd * off, q.p.y + q.r.y * sd * off, 1.6, q.p.z - 0.15))
                    s += 4.0
                if len(strip) > 1:
                    c.ribbon(name + " Lava %d" % sd, strip, 1.6, 0, c.lib("volcano_lava", "lava"), role="visual", steps=2)
        else:  # the roots
            half = pb.bore(c, L, name, s0, s1, ("em_moss_stone", "wall"), ("em_jungle_grass", "grass"), height=11.0)
            for s in (s0 - 2.0, s1 + 2.0):
                q = c.at(s)
                for j in range(5):
                    t = (j - 2) / 2.0
                    x, y = q.p.x + q.r.x * t * (half + 3.0), q.p.y + q.r.y * t * (half + 3.0)
                    cone(c, "%s Root %d %d" % (name, int(s), j), x, y, 1.4, q.p.z + 7.0 + 2.0 * abs(t), 6.0,
                         ("em_root_bark", "wall"), segs=5, role="visual")
        for k in range(3):
            q = c.at(s0 + (s1 - s0) * (k + 0.5) / 3)
            for sd in (-1, 1):
                x, y = q.p.x + q.r.x * sd * (half - 0.6), q.p.y + q.r.y * sd * (half - 0.6)
                g = c.game(x, y, q.p.z + 4.5)
                c.entity("torch", x=g[0], y=g[1], z=g[2])


def square(c, ground):
    """Dragonfire Square and its great dragon statue (broken after the sacrifice); the
    harbour's quays and lighthouse where the Causeway comes in."""
    cx, cy, cr, cz = HUB
    c.disc("Dragonfire Square", cx, cy, cr, cz + 0.05, c.lib("keep_cobble", "road"), coll="Props", n=40)
    if RUIN:
        box(c, "Statue Plinth", cx, cy, 5.0, 5.0, cz - 1.0, cz + 3.0, ("keep_ashlar", "wall"), rot=math.pi / 4)
        box(c, "Statue Stump", cx, cy, 2.0, 3.0, cz + 3.0, cz + 7.0, ("keep_rock", "wall"))
        ruin.rubble(c, "Statue Rubble", cx + 6.0, cy + 6.0, ground, ("keep_rock", "wall"), n=8, spread=4.0, size=1.4, seed=2)
        ruin.smoke(c, cx, cy, cz + 7.0)
    else:
        box(c, "Statue Plinth", cx, cy, 5.0, 5.0, cz - 1.0, cz + 3.0, ("keep_ashlar", "wall"), rot=math.pi / 4)
        c.place(kp.dragon_statue(c), cx, cy, cz + 3.0, rot=math.pi / 2)
    for k in range(6):
        a = k * math.tau / 6 + 0.5
        if math.sin(a) < -0.5 or math.sin(a) > 0.8:
            continue  # (clear of the ways in)
        hx, hy = cx + (cr + 8) * math.cos(a), cy + (cr + 8) * math.sin(a)
        if not paint.road_clear(c, hx, hy, 7.0):
            continue
        if RUIN:
            ruin.rubble(c, "House Rubble %d" % k, hx, hy, ground, ("keep_ashlar", "wall"), n=6, spread=4.0, size=1.2, seed=k)
            continue
        c.place(kp.house(c, k % 3), hx, hy, ground(hx, hy) - 0.3, rot=a + math.pi / 2)
    box(c, "Lighthouse", cx + 46.0, cy - 50.0, 3.0, 3.0, ground(cx + 46.0, cy - 50.0) - 1.0, cz + 22.0, ("keep_ashlar", "wall"))
    g = c.game(cx + 46.0, cy - 50.0, cz + 24.0)
    c.entity("lantern", x=g[0], y=g[1], z=g[2])


def landmarks(c, ground, spots):
    """Each world's gateway landmark: Dragonspire's tall keep on its crag, the jungle
    castle's overgrown gate, Emberdeep's fortress gate under its storm, the moon gate among
    violet lanterns, King Pyrrhax's Citadel."""
    def facing(name):
        (ex, ey), _ = spots[name]
        gx, gy = gates_at(name)
        return math.atan2(gy - ey, gx - ex)

    def gates_at(name):
        return DL.CITADEL if name == "citadel" else DL.GATES[name]

    def gateway(name, mat, width=8.0, height=12.0, towers=0.0, roof=None):
        x, y = gates_at(name)
        f = facing(name)
        rot = f + math.pi / 2
        z0 = ground(x - 6.0 * math.cos(f), y - 6.0 * math.sin(f))
        box(c, name.title() + " Gate", x, y, width, 2.0, z0 - 1.0, z0 + height, ("dark_corridor", "wall"), rot=rot,
            role="visual")
        for sd in (-1, 1):
            px, py = x + sd * (width + 1.5) * math.cos(rot), y + sd * (width + 1.5) * math.sin(rot)
            box(c, "%s Gate Jamb %d" % (name.title(), sd), px, py, 1.8, 2.8, z0 - 1.0, z0 + height + 2.0, mat, rot=rot)
            if towers:
                tx, ty = x + sd * (width + 7.0) * math.cos(rot), y + sd * (width + 7.0) * math.sin(rot)
                box(c, "%s Gate Tower %d" % (name.title(), sd), tx, ty, 4.0, 4.0, z0 - 1.0, z0 + towers, mat, rot=rot)
                if roof:
                    cone(c, "%s Gate Roof %d" % (name.title(), sd), tx, ty, 5.5, z0 + towers, 9.0, roof, segs=4,
                         role="visual")
        box(c, name.title() + " Gate Lintel", x, y, width + 2.5, 3.0, z0 + height, z0 + height + 3.5, mat, rot=rot)
        return x, y, z0, f

    roof = ("keep_slate", "wall")
    x, y, z0, f = gateway("keep", ("keep_ashlar", "wall"))
    kx, ky = x + 26.0 * math.cos(f), y + 26.0 * math.sin(f)
    box(c, "Dragonspire", kx, ky, 5.0, 5.0, z0 - 1.0, z0 + (24.0 if RUIN else 48.0), ("keep_ashlar", "wall"))
    if not RUIN:
        cone(c, "Dragonspire Roof", kx, ky, 7.0, z0 + 48.0, 14.0, roof, segs=4, role="visual")
    gateway("canyon", ("limestone_moss", "wall"), towers=20.0, roof=("lush_grass", "wall"))
    gateway("hold", ("fortress_wall", "wall"), height=16.0, towers=30.0)
    # The moon gate: a ring of stone among violet lanterns.
    mx, my = DL.GATES["moon"]
    f = facing("moon")
    rot = f + math.pi / 2
    z0 = ground(mx - 6.0 * math.cos(f), my - 6.0 * math.sin(f))
    for k in range(12):
        t = k * math.tau / 12
        bx, by = mx + 9.0 * math.cos(t) * math.cos(rot), my + 9.0 * math.cos(t) * math.sin(rot)
        z = z0 + 9.0 + 9.0 * math.sin(t)
        if z < z0 + 2.5 and abs(math.cos(t)) < 0.6:
            continue
        box(c, "Moon Gate %d" % k, bx, by, 1.6, 1.2, z - 1.2, z + 1.2, ("moon_stone", "wall"), rot=rot,
            role="both" if z < z0 + 6 else "visual")
    x, y, z0, f = gateway("citadel", ("keep_ashlar_dark", "wall"), width=10.0, height=18.0, towers=26.0 if RUIN else 44.0,
                          roof=None if RUIN else roof)
    kx, ky = x + 40.0 * math.cos(f), y + 40.0 * math.sin(f)
    box(c, "Citadel Keep", kx, ky, 22.0, 14.0, z0 + 10.0, z0 + (40.0 if RUIN else 70.0), ("keep_ashlar_dark", "wall"),
        rot=f + math.pi / 2, role="visual")


def ruined(c, ground, spots):
    """After the sacrifice: smoke and rubble at every gate, the trees charred."""
    for name, ((ex, ey), _) in spots.items():
        for sd in (-1, 1):
            ruin.rubble(c, "%s Rubble %d" % (name.title(), sd), ex + sd * 9.0, ey + 4.0, ground, ("keep_rock", "wall"),
                        seed=len(name) + sd)
        ruin.smoke(c, ex, ey + 8.0, ground(ex, ey) + 0.5)
    ruin_kit.char_trees(c, burn, ("Pine", "Broadleaf", "Blossom", "Jungle Tree"), chance=0.85, threshold=0.4)


def dress(c, ground, spots):
    """The paint pass, world by world: the harbour's boats and lanterns; Moonstone's
    pagodas, blossom trees, stone lanterns and lantern strings; Dragonspire's houses,
    banners and mountain pines; the Citadel's banners and braziers; Emberdeep's black walls,
    braziers and basalt; the Emerald Canyon's jungle, ruined temple blocks, roots."""
    taken = paint.Taken([(HUB[0], HUB[1], HUB[2] + 14.0), *((e[0], e[1], 16.0) for e, _ in spots.values()),
                         *((x, y, 26.0) for x, y in DL.GATES.values()), (*DL.CITADEL, 40.0)])

    def inside(x, y):
        return L.wall_sd(x, y) < -8 and natural(x, y) > WATER_Z + 0.6

    def look(*names):
        return lambda x, y: inside(x, y) and L.look_at(x, y) in names

    rmax = 480.0
    g = ground
    # Moonstone.
    mo = look("moon")
    paint.scatter(c, ip.pagoda(c, tiers=3, w=6.0, roof_mat="roof_jade"), 3, rmax, mo, g, taken, 10, room=14.0,
                  road_margin=10.0)
    for v in range(2):
        paint.scatter(c, ip.blossom_tree(c, v), 12, rmax, mo, g, taken, 11 + v, room=6.0, road_margin=6.0, trunk=(0.7, 5.0))
    for x, y in paint.scatter(c, ip.stone_lantern(c), 10, rmax, mo, g, taken, 13, room=6.0, near_road=(2.0, 5.0)):
        gg = c.game(x, y, g(x, y) + 2.0)
        c.entity("lantern", x=gg[0], y=gg[1], z=gg[2])
    # Dragonspire's crag and the climb.
    ke = look("keep")
    for v in range(2):
        paint.scatter(c, kp.pine(c, v, 9.0 + 3.0 * v), 26, rmax, ke, g, taken, 20 + v, room=5.0, scale=(1.0, 1.6),
                      road_margin=6.0, trunk=(0.7, 6.0))
        paint.scatter(c, kp.house(c, v), 4, rmax, ke, g, taken, 22 + v, room=14.0, road_margin=9.0)
    paint.scatter(c, kp.banner_pole(c), 10, rmax, look("keep", "citadel"), g, taken, 24, room=8.0, near_road=(2.0, 5.0))
    for x, y in paint.scatter(c, kp.brazier(c), 8, rmax, look("citadel", "hold"), g, taken, 25, room=8.0,
                              near_road=(2.0, 6.0)):
        gg = c.game(x, y, g(x, y) + 2.4)
        c.entity("torch", x=gg[0], y=gg[1], z=gg[2])
    # Emberdeep: black walls, basalt, steam.
    ho = look("hold")
    paint.scatter(c, kp.curtain_wall(c, length=18.0, h=10.0), 6, rmax, lambda x, y: ho(x, y) and L.wall_sd(x, y) > -16, g,
                  taken, 30, room=16.0, road_margin=10.0)
    paint.scatter(c, props.basalt_columns(c), 10, rmax, ho, g, taken, 31, room=7.0, road_margin=7.0)
    for x, y in paint.scatter(c, props.boulder(c, "volcano_basalt", 1), 6, rmax, ho, g, taken, 32, room=6.0):
        gg = c.game(x, y, g(x, y) + 1.0)
        c.entity("steam", x=gg[0], y=gg[1], z=gg[2])
    # The Emerald Canyon: jungle and temple ruins.
    ca = look("canyon")
    for v in range(2):
        paint.scatter(c, props.jungle_tree(c, v), 24, rmax, ca, g, taken, 40 + v, room=5.0, scale=(1.1, 1.8), road_margin=6.0,
                      trunk=(0.8, 6.0))
        paint.scatter(c, props.big_leaf_plant(c, v), 30, rmax, ca, g, taken, 42 + v, room=2.5, role="visual")
    for v, p in enumerate((props.ruin_column(c, 0), props.ruin_blocks(c, 0), props.idol_head(c))):
        paint.scatter(c, p, 4, rmax, ca, g, taken, 44 + v, room=6.0, near_road=(5.0, 20.0))
    # The harbour: pines and boats.
    ha = look("harbour")
    paint.scatter(c, kp.pine(c, 0, 10.0), 10, rmax, ha, g, taken, 50, room=6.0, road_margin=7.0, trunk=(0.7, 6.0))
    for k in range(4):
        x, y = -40.0 + 26.0 * k, -300.0 - 10.0 * (k % 2)
        c.place(kp.boat(c, k % 2), x, y, WATER_Z - 0.2, rot=0.3 * k, role="visual")


if __name__ == "__main__":
    main()
