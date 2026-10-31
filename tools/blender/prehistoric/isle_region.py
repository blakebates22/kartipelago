# Tropic Isles' overworld region, v4: one big island (isle_layout.py), replacing the
# walled coves of beach_region.py (kept, unused). Builds beach_region and, with --ruin,
# beach_region_ruin.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/isle_region.py [--ruin]
#
# Blake, Oct 31: "It's currently quite bad. Needs to be an island I think, with maybe
# tropical dense forest in the center." The island hop (the Dust Road's replacement) comes
# in over the east bay to Raptor's stilt village; the coast road round past Coral Cove's
# reef, the lagoon (its inlet on a boardwalk) and Splash Lagoon's slide tower, Shipwreck
# Bay's galleon, the Volcano Isle pier; then in through the jungle over the crest, the
# pinnacle and its falls across the valley, and down to the village.

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

RUIN = ruin.ON
TRACK_ID = ruin.track_id("beach_region") + os.environ.get("KP_REGION_SUFFIX", "")
WATER_Z = M.WATER_Z

LOOK = {
    # look: (ground, road, shoulder)
    "village": (("beach_sand", "sand"), "beach_road", ("beach_sand", "sand")),
    "coral": (("cove_sand", "sand"), "cove_road", ("cove_sand", "sand")),
    "lagoon": (("beach_sand", "sand"), "beach_road", ("beach_sand", "sand")),
    "wreck": (("wreck_sand", "sand"), "wreck_road", ("wreck_sand", "sand")),
    "beach": (("cove_sand", "sand"), "cove_road", ("cove_sand", "sand")),
    "jungle": (("isle_jungle", "grass"), "jungle_path", ("isle_jungle", "grass")),
}


def natural(x, y):
    return M.natural(x, y)


def classify(c, n, info):
    look = M.look_at(c.x, c.y)
    s = M.inland(c.x, c.y)
    if n.z < 0.62:
        if s < 90.0:
            return ("cove_rock", "wall")  # (the Head's sea cliffs)
        return ("jungle_mossstone" if c.z < 80.0 or n.z > 0.3 else "isle_rock", "wall")
    if c.z < WATER_Z - 2.0 and s < 0.0:
        return ("cove_wet_sand", "deep_water")  # (out of your depth: back to the road)
    if c.z < WATER_Z + 0.25:
        if math.hypot(c.x - M.LAGOON[0], c.y - M.LAGOON[1]) < M.LAGOON[2] + 20 or M.river_d(c.x, c.y)[0] < M.RIVER_HW + 3:
            return ("lagoon_shallow", "water")
        return ("cove_wet_sand", "water")  # (the shallows: wadeable)
    if n.z < 0.85:
        return ("jungle_mossstone", "dirt") if s > 90.0 else ("cove_rock", "dirt")
    if s < 10.0:
        return ("cove_wet_sand", "sand")
    if s < 36.0 and c.z < 4.0:
        return LOOK[look][0] if look != "jungle" else ("beach_sand", "sand")
    if s < 70.0 and c.z < 7.0 and look != "jungle":
        return LOOK[look][0] if math.sin(c.x / 13.0) * math.cos(c.y / 17.0) < 0.3 else ("isle_jungle", "grass")
    if c.z > 90.0:
        return ("jungle_mossstone", "dirt")  # (the pinnacle's mossy shoulders)
    return ("isle_jungle", "grass")


def main():
    c = kit.Course(TRACK_ID, "Tropic Isles (ruined)" if RUIN else "Tropic Isles", "coral_cove")
    c.route(M.route_points(), width=14.0, bank=5.0)
    kinds = {}
    for look, (ground, road, shoulder) in LOOK.items():
        kinds[look] = {"mat": road, "shoulder": 1.5, "shoulder_mat": shoulder}
    kinds["boardwalk"] = {"mat": "cove_planks", "surface": "road", "shoulder": 0.6, "shoulder_mat": ("cove_planks", "road"),
                          "barrier": 1.0, "barrier_mat": ("cove_rail", "wall"), "deck": 1.6, "deck_mat": ("cove_post", "wall"),
                          "ground": False}
    c.kinds = kinds

    def label(q):
        if M.on_boardwalk(q.p.x, q.p.y):
            return "boardwalk"
        return M.look_at(q.p.x, q.p.y)

    c.roads(kit.plan(c, pb.blend_runs(c, list(kit.runs(c, label)), {k: (v[0], None, v[1], v[2]) for k, v in LOOK.items()}),
                     "village", max_len=160.0))

    trail = dict(width=10.0, shoulder=1.2, shoulder_mat=("beach_sand", "sand"))
    # Raptor's square, off the road; the island hop's pier out east over the bay.
    hx, hy, hr = M.HUB
    smp, _ = c.nearest(hx, hy)
    c.side_road("Square Road", pb.line(natural, (smp.p.x, smp.p.y), (hx, hy), z0=smp.p.z, c=c), "cove_planks", "road", **trail)
    hz = natural(hx, hy)
    (ax, ay), (bx, by) = M.HOP_PIER
    pier_z = max(WATER_Z + 2.2, hz)
    hop = [(lerp(ax, bx, k / 20), lerp(ay, by, k / 20), lerp(hz + 0.05, pier_z, min(1.0, k / 3)) + 0.02) for k in range(21)]
    c.side_road("Hop Pier", hop, "cove_planks", "road", width=10.0, shoulder=0.4, shoulder_mat=("cove_planks", "road"),
                barrier=1.0, barrier_mat=("cove_rail", "wall"), deck=1.6, deck_mat=("cove_post", "wall"), ground=False)
    gates = {k: v for k, v in M.GATES.items() if k != "volcano"}
    if RUIN:
        gates["lair"] = M.LAIR
    spots = pb.spurs(c, natural, gates, lambda x, y: LOOK[M.look_at(x, y)][1], trail)
    # The Volcano Isle pier: out over the shallows north (the gateway at its end).
    px, py = M.GATES["volcano"]
    smp, _ = c.nearest(px, py)
    d = math.hypot(px - smp.p.x, py - smp.p.y)
    ux, uy = (px - smp.p.x) / d, (py - smp.p.y) / d
    sx, sy = smp.p.x + ux * (smp.w / 2 - 1.0), smp.p.y + uy * (smp.w / 2 - 1.0)
    z0 = pb.road_z_at(c, sx, sy) or smp.p.z
    vz = max(WATER_Z + 2.2, z0)
    qx, qy = smp.p.x + ux * (smp.w / 2 + 14.0), smp.p.y + uy * (smp.w / 2 + 14.0)
    c.side_road("Volcano Pier Road", [(lerp(sx, qx, k / 4), lerp(sy, qy, k / 4), lerp(z0, vz, k / 4) + 0.02) for k in range(5)],
                "cove_planks", "road", width=10.0, shoulder=0.4, shoulder_mat=("cove_planks", "road"))
    c.side_road("Volcano Pier", [(lerp(qx, px, k / 16), lerp(qy, py, k / 16), vz + 0.02) for k in range(17)], "cove_planks", "road",
                width=10.0, shoulder=0.4, shoulder_mat=("cove_planks", "road"), barrier=1.0, barrier_mat=("cove_rail", "wall"),
                deck=1.6, deck_mat=("cove_post", "wall"), ground=False)
    spots["volcano"] = ((px - ux * 4.0, py - uy * 4.0), math.atan2(-ux, uy))
    if RUIN:
        # Tidewyrm's Causeway: west over the sea from the west beach (his reef raised).
        (cx0, cy0), (cx1, cy1) = M.CAUSEWAY
        smp, _ = c.nearest(cx0, cy0)
        c.side_road("Causeway Beach", pb.line(natural, (smp.p.x, smp.p.y), (cx0, cy0), z0=smp.p.z, c=c), "beach_road", "road",
                    width=10.0, shoulder=0.6, shoulder_mat=("beach_sand", "sand"))
        cz = natural(cx0, cy0) + 0.2
        way = [(lerp(cx0, cx1, k / 24), lerp(cy0, cy1, k / 24), lerp(cz, WATER_Z + 2.2, min(1.0, k / 4)) + 0.02) for k in range(25)]
        c.side_road("Tidewyrm's Causeway", way, "beach_road", "road", width=10.0, shoulder=0.6, shoulder_mat=("isle_rock", "road"),
                    barrier=0.6, barrier_mat=("isle_rock", "wall"), deck=1.4, deck_mat=("isle_rock", "wall"), ground=False)

    X0, X1, Y0, Y1 = -470, 470, -470, 470
    ter = c.terrain("Tropic Isles", X0, X1, Y0, Y1, 3.0, natural, classify, near=8.0, fade=16.0, verge_fill=1.5)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 6.0, lambda x, y: natural(x, y) - 0.5, c.lib("beach_sand", "sand"))
    c.disc("Sea", 0.0, 0.0, 1800.0, WATER_Z, c.lib("sea_water", "water"), role="visual", n=72)

    def ground(x, y):
        z = c.ground_z(x, y, [ter])
        return natural(x, y) if z is None else z

    taken = paint.Taken([(hx, hy, hr + 12.0), (*M.CAVE, 16.0), (*M.SECRET, 14.0), (*M.CREST, 14.0),
                         (M.LAGOON[0], M.LAGOON[1], M.LAGOON[2] + 4.0), (*M.FALLS, 26.0),
                         *((e[0], e[1], 14.0) for e, _ in spots.values()), *((x, y, 22.0) for x, y in M.GATES.values()),
                         (*M.LAIR, 22.0)])
    water(c)
    village(c, ground, taken)
    landmarks(c, ground, spots, taken)
    if RUIN:
        ruined(c, ground)
    puzzle_kit.pen(c, "return", "Cove Yard", *M.CAVE, pb.to_road(c, *M.CAVE), 11.0, 4.5, ("tiki_wood", "wall"), ground(*M.CAVE),
                   height=5.0)
    puzzle_kit.pen(c, "secret", "Smugglers Cave", *M.SECRET, pb.to_road(c, *M.SECRET), 9.0, 4.5, ("isle_rock", "wall"),
                   ground(*M.SECRET), height=6.0)
    pb.emit_spots(c, spots)
    dress(c, ground, taken)

    c.start_line()
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
    if RUIN:
        g = c.game(cx1 + 10.0, cy1, 0.0)
        print("passage causeway: x %.1f z %.1f heading %.4f" % (g[0], g[2], math.atan2(cx0 - cx1, -(cy0 - cy1))))
    for name, (end, hd) in spots.items():
        g = c.game(end[0], end[1], 0.0)
        print("spot %s x %.2f z %.2f heading %.4f" % (name, g[0], g[2], hd))


# ------------------------------------------------------------------ water


def water(c):
    """The lagoon, the river down its gorge, the pinnacle's falls into their plunge pool."""
    lx, ly, lr = M.LAGOON
    c.disc("Lagoon", lx, ly, lr + 10.0, M.LAGOON_Z, c.lib("lagoon_shallow", "water"), role="visual", n=40, wobble=0.12, seed=3)
    strip = []
    for (ax, ay), (bx, by) in zip(M.RIVER, M.RIVER[1:]):
        n = max(1, int(math.hypot(bx - ax, by - ay) / 6))
        for k in range(n):
            t = k / n
            x, y = lerp(ax, bx, t), lerp(ay, by, t)
            _, u = M.river_d(x, y)
            strip.append((x, y, M.RIVER_HW * 2 + 2.0, lerp(14.0, M.LAGOON_Z, u) + 0.5))
    c.ribbon("River", strip, M.RIVER_HW * 2 + 2.0, 0, c.lib("lagoon_shallow", "water"), role="visual", steps=3)
    fx, fy = M.FALLS
    c.disc("Plunge Pool", fx, fy, 20.0, 12.6, c.lib("lagoon_shallow", "water"), role="visual", n=28, wobble=0.1, seed=5)
    lip = fy + 22.0
    top = M._land(fx, lip + 6.0) - 1.0
    props.falls(c, "Pinnacle Falls", fx, lip, top, 12.6, 8.0, 14.0, facing=-1, throw=6.0, bulge=1.4, veils=4,
                mats=("falls_oasis", "falls_curtain_oasis", "falls_foam"))
    g = c.game(fx, fy, 12.6)
    c.entity("waterfall", x=g[0], y=g[1], z=g[2], top=round(top - 12.6, 1), width=14.0, heading=0.0)
    # (more falls off the pinnacle's other faces: the big one facing the crest's lookout,
    # two thinner ones seen from the coast)
    px, py = M.PEAK
    toward = math.atan2(M.CREST[1] - py, M.CREST[0] - px)
    for k, (a, wt, wb) in enumerate(((toward, 6.0, 11.0), (2.3, 3.0, 6.0), (4.1, 3.0, 6.0))):
        lx2, ly2 = px + 46.0 * math.cos(a), py + 46.0 * math.sin(a)
        t2 = M._land(lx2, ly2) - 1.0
        b2 = M.natural(px + 70.0 * math.cos(a), py + 70.0 * math.sin(a))
        props.falls(c, "Spire Falls %d" % k, lx2, ly2, t2, b2, wt, wb, facing=1, throw=4.0, bulge=0.8, veils=3 if k == 0 else 2,
                    angle=a - math.pi / 2, mats=("falls_oasis", "falls_curtain_oasis", "falls_foam"))


# ------------------------------------------------------------------ the village


def village(c, ground, taken):
    """Raptor's village: a boardwalk square above the east bay, huts round it, stilt huts
    out over the bay either side of the hop's pier, tiki torches, a fire, its folk."""
    hx, hy, hr = M.HUB
    hz = natural(hx, hy)
    c.disc("Village Boardwalk", hx, hy, hr, hz + 0.05, c.lib("cove_planks", "road"), coll="Props", n=40)
    for k in range(8):
        a = k * math.tau / 8 + 0.3
        if math.cos(a) > 0.7 or math.cos(a) < -0.7 and math.sin(a) > -0.2:
            continue  # (clear of the pier, east, and the road, west)
        x, y = hx + (hr + 7) * math.cos(a), hy + (hr + 7) * math.sin(a)
        if not paint.road_clear(c, x, y, 6.0):
            continue
        if RUIN:
            box(c, "Hut %d" % k, x, y, 3.5, 3.5, ground(x, y) - 1.0, ground(x, y) + 1.4, ("tiki_wood", "wall"), rot=a)
            ruin.rubble(c, "Hut Wreck %d" % k, x + 4 * math.cos(a), y + 4 * math.sin(a), ground, ("thatch", "wall"), n=4, spread=3.0,
                        size=1.0, seed=k)
            continue
        foot = min(ground(x + dx, y + dy) for dx in (-3.5, 0.0, 3.5) for dy in (-3.5, 0.0, 3.5))
        c.place(tp.beach_hut(c, k % 3), x, y, foot - 0.2, rot=a + math.pi / 2)
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
        box(c, "Stilt Deck %d" % k, x, y, 4.0, 4.0, WATER_Z + 2.2, WATER_Z + 2.45, ("cove_planks", "wall"))
        box(c, "Stilt Walk %d" % k, x, lerp(y, lerp(ay, by, t), 0.5), 1.0, 5.0, WATER_Z + 2.2, WATER_Z + 2.4, ("cove_planks", "wall"),
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


# ------------------------------------------------------------------ the landmarks


def landmarks(c, ground, spots, taken):
    """Splash Lagoon's slide tower, Shipwreck Bay's galleon, Volcano Isle smoking offshore,
    Coral Cove's coral heads and lifeguard tower, the crest's lookout."""
    def facing(name):
        (ex, ey), _ = spots[name]
        gx, gy = M.GATES[name] if name in M.GATES else M.LAIR
        return math.atan2(gy - ey, gx - ex)

    # Splash Lagoon: the slide tower by the lagoon.
    x, y = M.GATES["splash"]
    rot = facing("splash") + math.pi / 2
    z = ground(x, y)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(c, "Slide Tower Leg %d%d" % (sx, sy), x + sx * 9.0 * math.cos(rot) + sy * 3.0 * math.cos(rot - math.pi / 2),
                y + sx * 9.0 * math.sin(rot) + sy * 3.0 * math.sin(rot - math.pi / 2), 0.6, 0.6, z - 1.0, z + 18.0,
                ("party_white", "wall"))
    box(c, "Slide Tower Deck", x, y, 10.0, 4.0, z + 18.0, z + 19.0, ("splash_deck", "wall"), rot=rot, role="visual")
    for k, m in enumerate(("splash_slide_red", "splash_slide_yellow", "splash_slide_blue")):
        box(c, "Slide %d" % k, x + (k - 1) * 6.0 * math.cos(rot) + 5 * math.cos(rot + math.pi / 2),
            y + (k - 1) * 6.0 * math.sin(rot) + 5 * math.sin(rot + math.pi / 2), 1.2, 8.0, z + 4.0 + 4 * k, z + 5.0 + 4 * k,
            (m, "wall"), rot=rot, role="visual")
    # Shipwreck Bay: a galleon on its side down the beach.
    x, y = M.GATES["wreck"]
    f = facing("wreck")
    gx, gy = x + 16.0 * math.cos(f), y + 16.0 * math.sin(f)
    box(c, "Wreck Hull", gx, gy, 16.0, 4.5, WATER_Z - 1.0, ground(gx, gy) + 5.0, ("wreck_hull", "wall"), rot=f + math.pi / 2)
    c.place(tp.mast(c, h=16.0, broken=True), gx + 4.0 * math.cos(f), gy + 4.0 * math.sin(f), ground(gx, gy) + 4.0, rot=f)
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
    # The crest's lookout: a tiki platform at the road's edge looking across to the pinnacle.
    q, _ = c.nearest(*M.CREST)
    px, py = M.PEAK
    ux, uy = px - q.p.x, py - q.p.y
    d = math.hypot(ux, uy)
    ox, oy = q.p.x + ux / d * (q.w / 2 + 6.0), q.p.y + uy / d * (q.w / 2 + 6.0)
    oz = q.p.z
    box(c, "Lookout Deck", ox, oy, 5.0, 4.0, oz - 3.0, oz + 0.3, ("cove_planks", "wall"), rot=math.atan2(uy, ux))
    torch = bp.tiki_torch(c, 0)
    for sd in (-1, 1):
        tx, ty = ox - uy / d * 4.5 * sd, oy + ux / d * 4.5 * sd
        c.place(torch, tx, ty, oz + 0.3)
        g = c.game(tx, ty, oz + 2.9)
        c.entity("torch", x=g[0], y=g[1], z=g[2])


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
        return 6.0 < s < 60.0 and natural(x, y) < 8.0

    def jungle(x, y):
        s = M.inland(x, y)
        return s > 40.0 and natural(x, y) > 3.5 and M.river_d(x, y)[0] > M.RIVER_HW + 3

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
    la = look("lagoon")
    for k, (p, n) in enumerate(((bp.umbrella(c, 0), 6), (bp.deck_chair(c, 1), 8), (bp.beach_ball(c, 0), 6))):
        paint.scatter(c, p, n, rmax, la, g, taken, 70 + k, room=3.0, role="visual", sink=0.05)


if __name__ == "__main__":
    main()
