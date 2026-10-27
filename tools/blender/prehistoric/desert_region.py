# Desert World, the overworld's third region (v3): built from desert_layout.py's pockets
# (Blake, Oct 26: each world walled off by landscape, the main road one loop through them
# by a threshold each time; see desert_layout.py for the plan).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/desert_region.py [--ruin]      (the bpy module)
#
# (--ruin: after Scorchwind's attack. Only the ruin has his lair, and the Dust Road out of
# the crater south (his drift across it is the game's, regions.ts's blocker, until he
# falls); the trading post is wrecked and sand drifts across the floors.)

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
import canyon_props as cp  # noqa: E402
import oasis_props as op  # noqa: E402
import gulch_props as gp  # noqa: E402
import impact_props as ip  # noqa: E402
import region_paint as paint  # noqa: E402
from pocket_kit import seg_d  # noqa: E402
import desert_layout as DL  # noqa: E402

RUIN = ruin.ON
TRACK_ID = ruin.track_id("desert_region") + os.environ.get("KP_REGION_SUFFIX", "")
L = DL.L
HUB = DL.HUB
FLOOR_Z = HUB[3]
RIM_Z = DL.TOP
CRATER_R = 64.0

# The Crater Stones (src/overworld/puzzles.ts): a sandstone vault on the crater's floor,
# its gate shut, and four stones round the crater to press within 30 seconds.
VAULT = (-52.0, -228.0)
STONES = [(50.0, -168.0), (-78.0, -150.0), (30.0, -234.0), (-40.0, -192.0)]
# Stego's old well (Act V's return task): a walled yard behind the trading post, a drift
# burying its way in.
RETURN = (-296.0, -28.0)
# A secret: a sunken garden in the oasis, cut off by deep water (the Beach Tool's).
SECRET = (282.0, 214.0)

LOOK = {
    # look: (ground, cliff, road, shoulder)
    "post": (("pale_sand", "loose_sand"), ("strata_orange", "wall"), "dash_road", ("dash_shoulder", "dirt")),
    "canyon": (("red_sand", "loose_sand"), ("strata_red", "wall"), "dash_road", ("dash_shoulder", "dirt")),
    "oasis": (("gold_sand", "loose_sand"), ("gold_cliff", "wall"), "oasis_paving", ("gold_sand", "loose_sand")),
    "gulch": (("gulch_sand", "loose_sand"), ("strata_rust", "wall"), "gulch_road", ("gulch_verge", "dirt")),
    "crater": (("slickrock", "dirt"), ("strata_purple", "wall"), "dash_road", ("talus", "wall")),
}


def natural(x, y):
    h = DL.natural(x, y)
    tz = L.tunnel_floor(x, y)
    if tz is not None:
        h = min(h, tz - 0.25)
    if RUIN:
        # The Dust Road: a cut south out of the crater.
        d, t = seg_d(x, y, (DL.DUST_ROAD[0], DL.DUST_ROAD[1] + 30.0), DL.DUST_END)
        if d < 30:
            h = lerp(h, 7.0 + 4.0 * t, smooth((30.0 - d) / 12.0))
        # Scorchwind's lair: a notch in the canyon's west wall.
        d, t = seg_d(x, y, (DL.LAIR[0] + 36.0, DL.LAIR[1] - 10.0), (DL.LAIR[0] - 20.0, DL.LAIR[1] + 6.0))
        if d < 22:
            h = lerp(h, 17.0, smooth((22.0 - d) / 9.0))
    return h


def classify(c, n, info):
    look = L.look_at(c.x, c.y)
    ground, cliff, _, _ = LOOK[look]
    if n.z < 0.62:
        if c.x < -300 and abs(c.y) < 50:
            return ("frost_cliff", "wall")  # (the pass down from the snow)
        return cliff
    if look == "oasis":
        px, py, pr, pz = DL.POOL
        if math.hypot(c.x - px, c.y - py) < pr + 26:
            return ("oasis_lawn", "grass")
    if L.pocket_at(c.x, c.y) == "wash":
        return ("gulch_wash", "dirt")
    if RUIN and math.sin(c.x / 31.0 + 1.0) * math.cos(c.y / 27.0) > 0.5:
        return ("dune_crest", "loose_sand")  # (Scorchwind's drifts)
    return ground


def main():
    c = kit.Course(TRACK_ID, "Desert World (ruined)" if RUIN else "Desert World", "canyon_dash")
    c.route(L.route_points(), width=14.0, bank=5.0)
    kinds = {}
    for look, (ground, cliff, road, shoulder) in LOOK.items():
        kinds[look] = {"mat": road, "shoulder": 1.5, "shoulder_mat": shoulder}
    kinds["bridge"] = {"mat": "plank_deck", "surface": "road", "shoulder": 0.6, "shoulder_mat": ("plank_deck", "road"),
                       "barrier": 1.0, "barrier_mat": ("fence_rail", "wall"), "deck": 1.8,
                       "deck_mat": ("weathered_timber", "wall"), "ground": False}
    kinds["mine"] = {"mat": "mine_floor", "shoulder": 1.5, "shoulder_mat": ("mine_floor", "dirt")}
    c.kinds = kinds

    def label(smp):
        d, wz = L.water_d(smp.p.x, smp.p.y)
        if d < L.river_hw + 4 and smp.p.z > wz + 0.9:
            return "bridge"
        if L.tunnel_floor(smp.p.x, smp.p.y) is not None and L.wall_sd(smp.p.x, smp.p.y) > -6:
            return "mine" if L.pocket_at(smp.p.x, smp.p.y) in ("oasis", "gulch") else "canyon"
        return L.look_at(smp.p.x, smp.p.y)

    c.roads(kit.plan(c, list(kit.runs(c, label)), "post", max_len=160.0))

    trail = dict(width=10.0, shoulder=1.2, shoulder_mat=("dash_shoulder", "dirt"))
    cx, cy, cr, cz = HUB
    smp, _ = c.nearest(cx + cr + 20.0, cy)
    c.side_road("Square Road", list(reversed(pb.line(natural, (smp.p.x, smp.p.y), (cx + cr - 2.0, cy), z0=smp.p.z))),
                "dash_road", "road", **trail)
    px, py = DL.PASS_END
    way = [(x, 0.0, natural(x, 0.0) + 0.2) for x in range(int(cx - cr + 2), int(px + 6), -8)]
    c.side_road("Frozen Pass Road", way, "dash_road", "road", **trail)
    gates = dict(DL.GATES)
    if RUIN:
        gates["lair"] = DL.LAIR
    spots = pb.spurs(c, natural, gates, lambda x, y: LOOK[L.look_at(x, y)][2], trail)
    if RUIN:
        smp, _ = c.nearest(*DL.DUST_ROAD)
        bx, by = DL.DUST_END
        c.side_road("Dust Road", pb.line(natural, (smp.p.x, smp.p.y), (bx, by + 10.0), z0=smp.p.z), "dash_road", "road",
                    **trail)

    X0, X1, Y0, Y1 = -490, 480, -480, 480
    ter = c.terrain("Desert World", X0, X1, Y0, Y1, 5.0, natural, classify, near=8.0, fade=16.0)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 5.0, lambda x, y: natural(x, y) - 0.5, c.lib("red_sand", "loose_sand"))

    def ground(x, y):
        z = c.ground_z(x, y, [ter])
        return natural(x, y) if z is None else z

    ppx, ppy, ppr, ppz = DL.POOL
    c.disc("Oasis Pool", ppx, ppy, ppr + 6.0, ppz - 0.1, c.lib("canal_water", "water"), role="visual", n=30, wobble=0.15,
           seed=4)

    thresholds(c, ground)
    trading_post(c, ground)
    landmarks(c, ground, spots)
    if RUIN:
        ruined(c, ground)
    puzzle_kit.pen(c, "crater_stones", "Vault", *VAULT, pb.to_road(c, *VAULT), 10.0, 4.5, ("masonry", "wall"),
                   ground(*VAULT), height=5.0)
    puzzle_kit.switches(c, "crater_stones", STONES, ground, ring_mat=("strata_cream", "wall"))
    puzzle_kit.pen(c, "return", "Old Well", *RETURN, pb.to_road(c, *RETURN), 11.0, 4.5, ("adobe", "wall"), ground(*RETURN),
                   height=6.0)
    puzzle_kit.pen(c, "secret", "Sunken Garden", *SECRET, pb.to_road(c, *SECRET), 9.0, 4.5, ("oasis_stone", "wall"),
                   ground(*SECRET), height=6.0)
    pb.emit_spots(c, spots)
    dress(c, ground, spots)
    box(c, "Pass Bend", px - 8.0, 0.0, 6.0, 40.0, natural(px, 0.0) - 2.0, RIM_Z + 30.0, ("frost_cliff", "wall"))
    if RUIN:
        c.entity("ashfall", rate=8, radius=40)  # (dust on the wind)

    c.start_line()
    gts = c.checkpoints(height=10.0)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish(extra={"race": {"laps": 1}})
    print("loop", round(c.length, 1), "gates", len(gts))


def thresholds(c, ground):
    """The Arch (a tunnel through a sandstone fin), the Mine (timber-shored, lanterns, ore
    carts at its mouths), the Slot (light falling into a narrow canyon), the Rim (the
    surveyors' camp on the crater's lip, warning signs)."""
    for name, kind, a, b in L.tunnels:
        s0, s1 = pb.tunnel_span(c, L, a, b)
        if kind == "arch":
            half = pb.bore(c, L, name, s0, s1, ("strata_cream", "wall"), ("red_sand", "loose_sand"), height=12.0)
            for s in (s0 - 4.0, s1 + 4.0):
                q = c.at(s)
                for sd in (-1, 1):
                    x, y = q.p.x + q.r.x * sd * (half + 8.0), q.p.y + q.r.y * sd * (half + 8.0)
                    c.place(cp.hoodoo(c, 0 if sd < 0 else 1, height=16.0), x, y, ground(x, y) - 0.5)
        else:  # the Mine
            half = pb.bore(c, L, name, s0, s1, ("mine_rock", "wall"), ("gulch_sand", "loose_sand"), height=10.0)
            sets = gp.timber_set(c, half=half - 0.4, height=9.4)
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
            portal = gp.mine_portal(c, half=half + 0.6, height=11.0)
            for k, s in enumerate((s0 - 2.0, s1 + 2.0)):
                q = c.at(s)
                c.place(portal, q.p.x, q.p.y, q.p.z - 0.3, rot=math.atan2(q.t.y, q.t.x) - math.pi / 2 + math.pi * k,
                        role="visual")
                x, y = q.p.x + q.r.x * (half + 6.0), q.p.y + q.r.y * (half + 6.0)
                c.place(gp.ore_cart(c, glow=True), x, y, ground(x, y), rot=math.atan2(q.t.y, q.t.x))
    # The Slot: sunbeams falling into it.
    for k, smp in enumerate(c.S[::25]):
        if L.pocket_at(smp.p.x, smp.p.y) == "slot":
            c.place(ip.sun_beam(c, length=50.0, r=5.0, variant=k % 2), smp.p.x + smp.r.x * 4.0, smp.p.y + smp.r.y * 4.0,
                    smp.p.z, rot=k * 0.7, role="visual")
    # The Rim: the surveyors' camp on the lip, warning signs.
    taken = []
    for k, smp in enumerate(c.S[::12]):
        if L.pocket_at(smp.p.x, smp.p.y) == "rim":
            sd = 1 if k % 2 else -1
            x, y = smp.p.x + smp.r.x * sd * (smp.w / 2 + 4.0), smp.p.y + smp.r.y * sd * (smp.w / 2 + 4.0)
            c.place(ip.warning_sign(c, k % 2), x, y, ground(x, y), rot=math.atan2(smp.t.y, smp.t.x) + math.pi / 2 * sd)
            taken.append((x, y))


def trading_post(c, ground):
    """Stego's trading post: the square, its stalls under awnings, the water tower, the
    windmill (after the attack: the stalls flattened, the tower down)."""
    cx, cy, cr, cz = HUB
    c.disc("Post Square", cx, cy, cr, cz + 0.05, c.lib("pale_sand", "dirt"), coll="Props", n=40)
    for k in range(7):
        a = k * math.tau / 7 + 0.4
        if math.cos(a) > 0.6:
            continue  # (clear of the way out, east)
        hx, hy = cx + (cr + 6) * math.cos(a), cy + (cr + 6) * math.sin(a)
        if not paint.road_clear(c, hx, hy, 6.0):
            continue
        if RUIN:
            box(c, "Stall %d" % k, hx, hy, 4.5, 3.5, cz - 1.0, cz + 1.6 + 0.8 * (k % 2), ("adobe", "wall"), rot=a)
            ruin.rubble(c, "Stall Rubble %d" % k, hx + 3.0 * math.cos(a), hy + 3.0 * math.sin(a), ground, ("adobe", "wall"),
                        n=5, spread=3.0, size=0.9, seed=k)
            continue
        box(c, "Stall %d" % k, hx, hy, 4.5, 3.5, cz - 1.0, cz + 4.5, ("adobe", "wall"), rot=a)
        box(c, "Stall Awning %d" % k, hx, hy, 5.2, 4.2, cz + 4.5, cz + 5.0, (("tent_cloth", "tent_cloth_red")[k % 2], "wall"),
            rot=a, role="visual")
    tx, ty = cx - 10.0, cy + 16.0
    if RUIN:
        box(c, "Water Tower Tank", tx - 6.0, ty + 3.0, 3.0, 2.5, cz - 0.5, cz + 4.5, ("weathered_timber", "wall"), rot=0.5)
    else:
        for sx in (-1, 1):
            for sy in (-1, 1):
                box(c, "Water Tower Leg %d%d" % (sx, sy), tx + sx * 2.2, ty + sy * 2.2, 0.3, 0.3, cz - 1.0, cz + 9.0,
                    ("weathered_timber", "wall"))
        box(c, "Water Tower Tank", tx, ty, 3.0, 3.0, cz + 9.0, cz + 14.0, ("tank_staves", "wall"), role="visual")
        c.place(cp.windmill_tower(c), cx + 6.0, cy - 30.0, ground(cx + 6.0, cy - 30.0) - 0.2)
    g = c.game(cx, cy, cz + 0.3)
    c.entity("campfire", x=g[0], y=g[1], z=g[2])


def landmarks(c, ground, spots):
    def facing(name):
        (ex, ey), _ = spots[name]
        gx, gy = (DL.GATES[name] if name in DL.GATES else DL.LAIR)
        return math.atan2(gy - ey, gx - ex)

    # Canyon Dash: the slot canyon's mouth, a dark cleft between two pillars.
    gx, gy = DL.GATES["canyon"]
    f = facing("canyon")
    z = ground(gx, gy)
    box(c, "Slot Canyon", gx + 3.0 * math.cos(f), gy + 3.0 * math.sin(f), 6.0, 2.0, z - 1.0, z + 30.0, ("dark_corridor", "wall"),
        rot=f + math.pi / 2, role="visual")
    for sd in (-1, 1):
        sx, sy = gx + sd * 10.0 * math.cos(f + math.pi / 2), gy + sd * 10.0 * math.sin(f + math.pi / 2)
        c.assign(c.rock_mass("Canyon Pillar %d" % sd, sx, sy, 5.0, 4.0, z + 34.0, z0=z - 1.0, n=10, seed=3 + sd),
                 c.lib("strata_orange", "wall"))
    # Oasis Haven: palms round a spring, a domed kiosk.
    gx, gy = DL.GATES["oasis"]
    c.place(op.kiosk(c, 0), gx + 6.0, gy + 8.0, ground(gx + 6.0, gy + 8.0) - 0.2)
    # Dry Gulch: the street's end arch, the graveyard by it.
    gx, gy = DL.GATES["gulch"]
    f = facing("gulch")
    for sd in (-1, 1):
        x, y = gx + sd * 8.0 * math.cos(f + math.pi / 2), gy + sd * 8.0 * math.sin(f + math.pi / 2)
        box(c, "Gulch Gate Post %d" % sd, x, y, 0.5, 0.5, ground(x, y) - 1.0, ground(x, y) + 8.0, ("weathered_timber", "wall"))
    box(c, "Gulch Gate Beam", gx, gy, 9.0, 0.5, ground(gx, gy) + 7.0, ground(gx, gy) + 8.0, ("weathered_timber", "wall"),
        rot=f + math.pi / 2, role="visual")
    # Impact Depths: the meteorite in the crater's floor, glowing shards round it.
    gx, gy = DL.GATES["impact"]
    f = facing("impact")
    x, y = gx + 6.0 * math.cos(f), gy + 6.0 * math.sin(f)
    c.place(ip.meteorite(c, 0, size=7.0), x, y, ground(x, y) - 1.0)
    for k in range(5):
        a = f + (k - 2) * 0.6
        x, y = gx + 12.0 * math.cos(a), gy + 12.0 * math.sin(a)
        c.place(ip.glass_shards(c, k % 2), x, y, ground(x, y) - 0.3, rot=a, role="visual")


def ruined(c, ground):
    """After Scorchwind's attack: his lair (a rock arch in the canyon's west wall, a dust
    devil turning before it), the Dust Road's cut south, drifts."""
    lx, ly = DL.LAIR
    z = ground(lx, ly)
    box(c, "Lair Dark", lx - 3.0, ly + 1.0, 2.0, 7.0, z - 1.0, z + 12.0, ("dark_corridor", "wall"), role="visual")
    for sd in (-1, 1):
        c.assign(c.rock_mass("Lair Arch Leg %d" % sd, lx - 2.0, ly + sd * 11.0, 4.0, 4.0, z + 18.0, z0=z - 1.0, n=10,
                             seed=9 + sd), c.lib("strata_red", "wall"))
    box(c, "Lair Arch Span", lx - 2.0, ly, 5.0, 14.0, z + 15.0, z + 20.0, ("strata_red", "wall"), role="visual")
    bx, by = DL.DUST_END
    box(c, "Dust Road Bend", bx, by - 8.0, 40.0, 6.0, natural(bx, by) - 2.0, RIM_Z + 30.0, ("strata_orange", "wall"))


def false_front(c, name, x, y, z, rot, w, d, siding, lit=True):
    """A frontier false-front building facing the street (local -y): a clapboard body, a
    tall square front over its gable, a porch roof, lit windows."""
    ca, sa = math.cos(rot), math.sin(rot)

    def at(lx, ly):
        return x + lx * ca - ly * sa, y + lx * sa + ly * ca

    bx, by = at(0.0, d / 2)
    box(c, name, bx, by, w / 2, d / 2, z - 1.0, z + 5.0, (siding, "wall"), rot=rot)
    fx, fy = at(0.0, 0.3)
    box(c, name + " Front", fx, fy, w / 2 + 0.3, 0.3, z + 4.0, z + 8.5, (siding, "wall"), rot=rot, role="visual")
    rx, ry = at(0.0, d / 2)
    box(c, name + " Roof", rx, ry, w / 2 + 0.4, d / 2 + 0.3, z + 5.0, z + 5.6, ("shingle_roof", "wall"), rot=rot, role="visual")
    px, py = at(0.0, -1.6)
    box(c, name + " Porch", px, py, w / 2, 1.6, z + 3.4, z + 3.7, ("tin_roof", "wall"), rot=rot, role="visual")
    for k in (-1, 1):
        wx, wy = at(k * w / 4, -0.05)
        box(c, name + " Window %d" % k, wx, wy, 1.0, 0.06, z + 1.2, z + 2.8, ("window_lit" if lit else "window_dark", "wall"),
            rot=rot, role="visual")


def dress(c, ground, spots):
    """The paint pass: the canyon's hoodoos, saguaros, joshua trees and sage; the oasis's
    palms, cypresses and bougainvillea; the ghost town's false fronts down the street,
    barrels, wagons, tumbleweeds; the crater's shards and the surveyors' tents; the wash's
    dead trees and skulls."""
    taken = paint.Taken([(HUB[0], HUB[1], HUB[2] + 12.0), (*VAULT, 18.0), (*RETURN, 18.0), (*SECRET, 16.0),
                         *((x, y, 9.0) for x, y in STONES), *((e[0], e[1], 16.0) for e, _ in spots.values()),
                         *((x, y, 24.0) for x, y in DL.GATES.values()), (*DL.LAIR, 24.0),
                         (DL.POOL[0], DL.POOL[1], DL.POOL[2] + 8.0)])

    def inside(x, y):
        return L.wall_sd(x, y) < -8

    def look(name):
        return lambda x, y: inside(x, y) and L.look_at(x, y) == name

    def pocket(name):
        return lambda x, y: inside(x, y) and L.pocket_at(x, y) == name

    rmax = 480.0
    g = ground
    for name in ("post", "canyon", "gulch", "crater"):
        for v in range(2):
            paint.scatter(c, cp.boulder(c, v), 6, rmax, lambda x, y, n=name: look(n)(x, y) and L.wall_sd(x, y) > -30, g,
                          taken, 90 + v + len(name), room=4.0, scale=(1.0, 2.2), road_margin=9.0)
    # The canyon: hoodoos, saguaros, joshua trees, sage and dry grass.
    ca = look("canyon")
    for v in range(2):
        paint.scatter(c, cp.hoodoo(c, v, height=12.0 + 6.0 * v), 6, rmax, ca, g, taken, 10 + v, room=10.0, road_margin=9.0)
        paint.scatter(c, cp.saguaro(c, v), 14, rmax, ca, g, taken, 12 + v, room=5.0, road_margin=6.0, trunk=(0.6, 6.0))
        paint.scatter(c, cp.joshua_tree(c, v), 8, rmax, ca, g, taken, 14 + v, room=6.0, road_margin=6.0, trunk=(0.6, 5.0))
        paint.scatter(c, cp.sagebrush(c, v), 40, rmax, ca, g, taken, 16 + v, room=2.5, role="visual")
    paint.scatter(c, cp.agave(c, 0), 20, rmax, ca, g, taken, 18, room=2.5, role="visual")
    # The oasis: palms round the pool, cypresses, bougainvillea, market stalls.
    oa = look("oasis")
    for v in range(3):
        paint.scatter(c, op.palm(c, v, height=10.0 + 2.0 * v), 14, rmax, oa, g, taken, 20 + v, room=5.0, road_margin=6.0,
                      trunk=(0.6, 8.0))
    for v in range(2):
        paint.scatter(c, op.cypress(c, v), 8, rmax, oa, g, taken, 24 + v, room=5.0, road_margin=6.0, trunk=(0.7, 6.0))
        paint.scatter(c, op.bougainvillea(c, v), 12, rmax, oa, g, taken, 26 + v, room=3.0, role="visual")
        paint.scatter(c, op.market_stall(c, v), 3, rmax, oa, g, taken, 28 + v, room=8.0, near_road=(3.0, 8.0))
    # The ghost town: false fronts down both sides of its street, barrels, wagons.
    sidings = ("siding_brown", "siding_grey", "siding_red", "siding_ochre", "siding_green")
    k = 0
    for smp in c.S[::14]:
        if L.pocket_at(smp.p.x, smp.p.y) != "gulch":
            continue
        for sd in (-1, 1):
            off = smp.w / 2 + 6.0
            x, y = smp.p.x + smp.r.x * sd * off, smp.p.y + smp.r.y * sd * off
            if not inside(x, y) or not taken.clear(x, y, 7.0) or not paint.road_clear(c, x, y, 4.0):
                continue
            rot = math.atan2(smp.r.y * sd, smp.r.x * sd) - math.pi / 2  # (its front, local -y, to the street)
            false_front(c, "Gulch House %d" % k, x, y, g(x, y), rot, 9.0 + 2.0 * (k % 3), 10.0, sidings[k % len(sidings)],
                        lit=not RUIN and k % 3 != 1)
            taken.add(x, y, 8.0)
            k += 1
    gu = look("gulch")
    paint.scatter(c, gp.barrel(c, 0), 10, rmax, gu, g, taken, 30, room=3.0, near_road=(2.0, 5.0))
    paint.scatter(c, gp.wagon(c, broken=True), 3, rmax, gu, g, taken, 31, room=8.0, road_margin=5.0)
    paint.scatter(c, gp.tumbleweed(c, 0), 14, rmax, gu, g, taken, 32, room=3.0, role="visual")
    for v in range(2):
        paint.scatter(c, gp.headstone(c, v), 6, rmax, lambda x, y: gu(x, y) and math.hypot(
            x - DL.GATES["gulch"][0], y - DL.GATES["gulch"][1]) < 50, g, taken, 33 + v, room=2.5)
        paint.scatter(c, gp.dead_tree(c, v), 6, rmax, gu, g, taken, 35 + v, room=5.0, road_margin=5.0, trunk=(0.5, 5.0))
    # The crater: shards, meteorites, the surveyors' tents and scope.
    cr = look("crater")
    for v in range(2):
        paint.scatter(c, ip.glass_shards(c, v), 10, rmax, cr, g, taken, 40 + v, room=4.0, role="visual")
        paint.scatter(c, ip.meteorite(c, v, size=2.5), 6, rmax, cr, g, taken, 42 + v, room=5.0, road_margin=5.0)
    paint.scatter(c, ip.tent(c, 0), 3, rmax, pocket("rim"), g, taken, 44, room=8.0, road_margin=5.0)
    paint.scatter(c, ip.survey_scope(c), 2, rmax, pocket("rim"), g, taken, 45, room=6.0, road_margin=4.0)
    # The wash: dead trees, cattle skulls.
    wa = pocket("wash")
    paint.scatter(c, gp.dead_tree(c, 1), 6, rmax, wa, g, taken, 50, room=6.0, road_margin=5.0, trunk=(0.5, 5.0))
    paint.scatter(c, gp.cattle_skull(c), 5, rmax, wa, g, taken, 51, room=3.0, role="visual")
    # The post: crates, banner poles.
    po = look("post")
    paint.scatter(c, cp.crates(c, 0), 6, rmax, po, g, taken, 60, room=4.0, near_road=(2.0, 6.0))
    paint.scatter(c, cp.banner_pole(c, 0), 6, rmax, po, g, taken, 61, room=6.0, near_road=(2.0, 5.0))


if __name__ == "__main__":
    main()
