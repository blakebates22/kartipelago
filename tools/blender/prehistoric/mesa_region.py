# Desert World v4, the open Southwest (Blake, Oct 31): built from mesa_layout.py (see it for
# the plan). Replaces desert_region.py's walled pockets with one open desert floor, its
# mesas and buttes standing on it, the road out along the Grand Canyon's rim, past Havasu's
# pools, through the boomtown, round Meteor Crater's rim, by Scorchwind's rodeo arena, up
# the Ledge Road and over Sun Arch home.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/mesa_region.py [--ruin]      (the bpy module)

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import bmesh, lerp, smooth  # noqa: E402
import region_ruin as ruin  # noqa: E402
import puzzle_kit  # noqa: E402
import pocket_build as pb  # noqa: E402
from pocket_build import box, cone  # noqa: E402
import canyon_props as cp  # noqa: E402
import hoodoo_family as hf  # noqa: E402
import oasis_props as op  # noqa: E402
import gulch_props as gp  # noqa: E402
import impact_props as ip  # noqa: E402
import keep_props as kp  # noqa: E402
import summit_props as smp_  # noqa: E402
import props  # noqa: E402
import region_paint as paint  # noqa: E402
import road_clip  # noqa: E402
import mesa_dress as md  # noqa: E402
import mesa_layout as M  # noqa: E402

RUIN = ruin.ON
TRACK_ID = ruin.track_id("desert_region") + os.environ.get("KP_REGION_SUFFIX", "")

LOOK = {
    # look: (ground, road, shoulder)
    "post": (("pale_sand", "loose_sand"), "dash_road", ("dash_shoulder", "dirt")),
    "pueblo": (("red_sand", "loose_sand"), "dash_road", ("dash_shoulder", "dirt")),
    "canyon": (("red_sand", "loose_sand"), "dash_road", ("dash_shoulder", "dirt")),
    "falls": (("gold_sand", "loose_sand"), "dash_road", ("dash_shoulder", "dirt")),
    "town": (("gulch_sand", "loose_sand"), "gulch_road", ("gulch_verge", "dirt")),
    "crater": (("slickrock", "dirt"), "dash_road", ("talus", "dirt")),
    "show": (("red_sand", "loose_sand"), "dash_road", ("dash_shoulder", "dirt")),
    "mesa": (("slickrock", "dirt"), "dash_road", ("dash_shoulder", "dirt")),
}


def natural(x, y):
    return M.natural(x, y)


def classify(c, n, info):
    look = M.look_at(c.x, c.y)
    # (Every cliff in the one texture of level beds, the canyon's too, its beds lying by
    # height the same on every wall: Blake, review-desert_region note 1, "redo all of the
    # walls so there layers make sense ... the zigzagedness is weird". They were a rock a
    # face, by its height give or take a wobble, so each bed's edge stepped and waved
    # across the land's triangles.)
    up = c.z > M.FLOOR + 3.0 or (M.canyon_d(c.x, c.y) < M.CANYON_HW + 2 and c.z < M.TERRACE - 1.0)
    if n.z < 0.62:
        if math.hypot(c.x - M.CRATER[0], c.y - M.CRATER[1]) < M.CRATER[2] * 1.3:
            return ("strata_purple", "wall")
        return ("desert_strata", "wall")
    cx, cy, R, _rim, _cz = M.CRATER
    in_crater = math.hypot(c.x - cx, c.y - cy) < M.CRATER[2] * 1.3
    if math.hypot(c.x - cx, c.y - cy) < R - 2.0:
        # (Down in the crater, Impact Depths' worlds: the crystal wall, the jungle ledge,
        # black volcanic rock round the core: v4b.)
        a = math.degrees(math.atan2(c.y - cy, c.x - cx))
        if math.hypot(c.x - cx, c.y - cy) < 20.0:
            return ("black_rock", "dirt")
        if -100.0 <= a <= 10.0:
            return ("crystal_rock", "dirt")
        if a < -100.0 or a > 150.0:
            return ("moss_rock", "dirt")
        return ("black_rock", "dirt")
    if n.z < 0.85:
        # (Up a cliff, the half-steep faces between its steep ones are its beds too: as
        # scree they stood out as grey teeth up the walls.)
        return ("desert_strata", "dirt") if up and not in_crater else ("talus", "dirt")  # (still driven on as before)
    fx, fy, fr, fz = M.FALLS
    if math.hypot(c.x - fx, c.y - fy) < fr + 2 and c.z < fz + 3:
        return ("sinter", "dirt")  # (the travertine round Havasu's pools)
    if M.canyon_d(c.x, c.y) < M.CANYON_HW and c.z < M.CANYON_DEPTH + 4:
        return ("canyon_rock_ochre", "dirt")
    if c.z > 30.0:
        return ("slickrock", "dirt")  # (the mesas' caprock)
    if RUIN and math.sin(c.x / 31.0 + 1.0) * math.cos(c.y / 27.0) > 0.5:
        return ("dune_crest", "loose_sand")  # (Scorchwind's drifts)
    if math.sin(c.x / 19.0 + c.y / 41.0 + math.sin(c.y / 33.0)) > 0.75 and c.x + c.y < -250:
        return ("dune_crest", "loose_sand")
    if math.sin(c.x / 47.0) * math.cos(c.y / 53.0 + 0.4) > 0.6:
        return ("dry_grass", "grass")  # (bunchgrass flats)
    return LOOK[look][0]


def main():
    c = kit.Course(TRACK_ID, "Desert World (ruined)" if RUIN else "Desert World", "canyon_dash")
    c.route(M.route_points(), width=14.0, bank=5.0)
    kinds = {}
    for look, (ground, road, shoulder) in LOOK.items():
        kinds[look] = {"mat": road, "shoulder": 1.5, "shoulder_mat": shoulder}
    # The Gap Bridge (was Sun Arch's back; review-desert_region 3, note 12: "lets make this a
    # wood bridge with wooden support"): a timber trestle bridge, plank deck, timber rails.
    kinds["bridge"] = {"mat": "plank_road", "surface": "road", "shoulder": 0.8, "shoulder_mat": ("weathered_timber", "road"),
                       "barrier": 1.1, "barrier_mat": ("timber_rail", "wall"), "deck": 1.2, "deck_mat": ("weathered_timber", "wall"),
                       "ground": False}
    c.kinds = kinds

    def label(q):
        if M._land(q.p.x, q.p.y) < q.p.z - 4.0 and math.hypot(q.p.x - M.ARCH[0], q.p.y - M.ARCH[1]) < 24.0:
            return "bridge"
        return M.look_at(q.p.x, q.p.y)

    c.roads(kit.plan(c, pb.blend_runs(c, list(kit.runs(c, label)), {k: (v[0], None, v[1], v[2]) for k, v in LOOK.items()}),
                     "post", max_len=160.0))

    trail = dict(width=10.0, shoulder=1.2, shoulder_mat=("dash_shoulder", "dirt"))
    # The frontier town (review-desert_region note 2): its Main Street north through the bay
    # under the rim, and the road from the lap west across it, through town and on to the
    # Frozen Pass (the trading post's square and its roads were in the buildings' way).
    px, py, pr = M.POST
    smp, _ = c.nearest(px + pr + 12.0, py)
    fx, fy = M.FROZEN_PASS
    mouth = pb.line(natural, (smp.p.x, smp.p.y), (px + 10.0, py), z0=smp.p.z, c=c)
    way = mouth + [(x, py, natural(x, py) + 0.2) for x in range(int(px + 2), int(fx - 6), -8)]
    c.side_road("Pass Road", list(reversed(way)), "dash_road", "road", **trail)
    STREET[:] = [(M.MAIN_STREET[0], y, natural(M.MAIN_STREET[0], y) + 0.2) for y in range(int(M.MAIN_STREET[1]), int(M.MAIN_STREET[2]) + 1, 6)]
    c.side_road("Main Street", STREET, "dash_road", "road", **dict(trail, width=12.0))
    # The ring road round the town square's plaza, at Main Street's north end.
    c.side_road("Square Ring", md.square_ring_points(), "dash_road", "road", **dict(trail, width=10.0))
    # The way up into the pueblo's alcove (review-desert_region 3, note 2; the ramp up to its
    # upper terrace is gone: review-desert_region 4, note 1).
    ax, ay, aw, adp = M.ALCOVE
    smp, _ = c.nearest(ax, ay - 40.0)
    c.side_road("Pueblo Way", pb.line(natural, (smp.p.x, smp.p.y), (ax, ay - 6.0), z0=smp.p.z, c=c), "dash_road", "road",
                **dict(trail, width=9.0))
    gates = dict(M.GATES)
    if not RUIN:
        gates.pop("lair")
    spots = pb.spurs(c, natural, gates, lambda x, y: LOOK[M.look_at(x, y)][1], trail, short={"canyon": 6.0})
    for name, ((ex, ey), hd) in spots.items():
        print("gateway %s: x %.2f z %.2f heading %.4f" % (name, ex, -ey, hd))
    # (No Dust Road out through the south rim after Scorchwind's fall any more: the only way
    # out is the smugglers' tunnel from the Drift Cave, Blake, Nov 1.)
    if RUIN and False:
        (ax, ay), (bx, by), _z, _hw = M.PASS_WAYS[1]
        smp, _ = c.nearest(*M.DUST_FROM)
        first = pb.line(natural, (smp.p.x, smp.p.y), (ax, ay), z0=smp.p.z, c=c)
        rest = pb.line(natural, (ax, ay), (bx, by + 8.0), z0=first[-1][2], c=c)
        c.side_road("Dust Road", first + rest[1:], "dash_road", "road", **trail)

    X0, X1, Y0, Y1 = -470, 470, -470, 470
    ter = c.terrain("Desert World", X0, X1, Y0, Y1, 3.0, natural, classify, near=8.0, fade=16.0, verge_fill=1.5)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 6.0, lambda x, y: natural(x, y) - 0.5, c.lib("red_sand", "loose_sand"))

    def ground(x, y):
        z = c.ground_z(x, y, [ter])
        return natural(x, y) if z is None else z

    taken = paint.Taken([(*M.ALCOVE[:2], 44.0), (*M.ARENA[:2], M.ARENA[2] + 16.0), (*M.CAVE, 16.0),
                         (*M.SECRET, 14.0), (M.FALLS[0], M.FALLS[1], M.FALLS[2] + 14.0),
                         *((e[0], e[1], 14.0) for e, _ in spots.values()), *((x, y, 16.0) for x, y in M.GATES.values())])
    water(c)
    sun_arch(c, ground)
    trading_post(c, ground, taken, ter)
    pueblo(c, ground, taken)
    canyon_rim(c, ground, taken)
    havasu(c, ground, taken)
    # (The deep pass, Nov 1: each section in its own course's kit: mesa_dress.)
    md.canyon_outpost(c, ground, taken, ter)
    md.havasu_village(c, ground, taken, ter)
    town_at = md.boomtown(c, ground, taken, ter)
    boomtown(c, ground, taken, town_at)
    crater(c, ground, taken)
    md.crater_depths(c, ground, taken)
    md.crater_camp(c, ground, taken, ter)
    # (No rodeo showground, review-desert_region 3 note 1: "lets remove this rodeo ... I will
    # think of something else later"; its ground stays clear. No telegraph lines, note 4.)
    ledge(c, ground, taken)
    md.chevrons(c, ground, taken)
    # (Folk along the roads, far from the towns'.)
    paint.wayfolk(c, ground, "desert", [(-360.0, -44.0), (-250.0, 160.0), (282.0, -120.0), (110.0, -335.0), (100.0, -168.0)], 4)
    # The smugglers' Drift Cave, in Meteor Crater's inner wall (review-desert_region note 3): only
    # its gate (the guards keep it), its yard the ledge, the mouth in its crag (drift_cave).
    out = math.atan2(M.CRATER[1] - M.CAVE[1], M.CRATER[0] - M.CAVE[0])
    puzzle_kit.pen(c, "return", "Drift Cave", *M.CAVE, out, 4.5, 4.5, ("adobe", "wall"), ground(*M.CAVE), height=6.0, walls=False)
    drift_cave(c, ground)
    puzzle_kit.pen(c, "secret", "Sunken Garden", *M.SECRET, pb.to_road(c, *M.SECRET), 9.0, 4.5, ("oasis_stone", "wall"),
                   ground(*M.SECRET), height=6.0)
    pb.emit_spots(c, spots)
    desert(c, ground, taken)
    if RUIN:
        c.entity("ashfall", rate=8, radius=40)  # (dust on the wind)

    # Zippers on the long drives between the worlds (Blake, Nov 1).
    md.zippers(c, [M.POST[:2], M.ALCOVE[:2], M.ROUTE[7][:2], M.ROUTE[19][:2], M.ROUTE[21][:2], M.ROUTE[25][:2], M.ROUTE[27][:2],
                   M.ROUTE[29][:2], M.ROUTE[41][:2], M.ROUTE[43][:2], M.ROUTE[46][:2], M.ARCH])
    c.start_line()
    gts = c.checkpoints(height=10.0)
    kit.paint.shade_roads(c.pieces, 0.3)
    # (No shoulder strip across another road's paving: review-desert_region 2, notes 6, 7, 13.)
    road_clip.clip_shoulders(c, [("Pass Road", 10.0), ("Main Street", 12.0), ("Pueblo Way", 9.0), ("Square Ring", 10.0)]
                             + [(name.title() + " Road", 10.0) for name in spots])
    c.finish(extra={"race": {"laps": 1}})
    print("loop", round(c.length, 1), "gates", len(gts))
    s0 = c.at(0.0)
    g = c.game(s0.p.x, s0.p.y, 0.0)
    print("start x %.1f z %.1f heading %.4f" % (g[0], g[2], math.atan2(s0.t.x, -s0.t.y)))
    for name, (zone, end, _z, _hw) in zip(("frozen_pass", "dust_road"), M.PASS_WAYS):
        g = c.game(end[0], end[1], 0.0)
        hx, hy = zone[0] - end[0], zone[1] - end[1]
        print("passage %s: x %.1f z %.1f heading %.4f" % (name, g[0], g[2], math.atan2(hx, -hy)))


# ------------------------------------------------------------------ water and rock


def water(c):
    """The Colorado at the canyon's foot (turquoise, round Horseshoe Bend), Havasu's pools
    and its falls off the side canyon's lip."""
    strip = []
    for (ax, ay), (bx, by) in zip(M.CANYON, M.CANYON[1:]):
        n = max(1, int(math.hypot(bx - ax, by - ay) / 6))
        for k in range(n):
            t = k / n
            strip.append((lerp(ax, bx, t), lerp(ay, by, t), 20.0, M.CANYON_DEPTH + 0.5))
    strip.append((M.CANYON[-1][0], M.CANYON[-1][1], 20.0, M.CANYON_DEPTH + 0.5))
    c.ribbon("Colorado", strip, 20.0, 0, c.lib("canyon_river", "water"), role="visual", steps=4)
    fx, fy, fr, fz = M.FALLS
    c.disc("Havasu Pool", fx, fy, fr - 2.0, fz + 0.6, c.lib("lagoon_shallow", "water"), role="visual", n=32, wobble=0.12, seed=2)
    for k, (dx, dy, r) in enumerate(((-18.0, -10.0, 8.0), (-10.0, -22.0, 6.5), (6.0, -24.0, 5.5))):
        z = fz + 1.6 + 1.1 * k
        c.disc("Havasu Terrace Pool %d" % k, fx + dx, fy + dy, r, z, c.lib("lagoon_shallow", "water"), role="visual", n=20,
               wobble=0.15, seed=k)
        c.disc("Havasu Terrace Rim %d" % k, fx + dx, fy + dy, r + 0.9, z - 0.15, c.lib("sinter_rim", "wall"), role="visual",
               n=20, wobble=0.15, seed=k)
    # Havasu's creek, from its spring out on the bench down its channel to the lip (review-
    # desert_region 3, note 7: the falls had no water feeding them).
    strip = []
    for (ax_, ay_), (bx_, by_) in zip(M.CREEK, M.CREEK[1:]):
        n = max(1, int(math.hypot(bx_ - ax_, by_ - ay_) / 3.0))
        for k in range(n):
            x, y = lerp(ax_, bx_, k / n), lerp(ay_, by_, k / n)
            strip.append((x, y, 2 * M.CREEK_HW + 1.0, M.natural(x, y) + 0.9))
    sx_, sy_ = M.CREEK[-1]
    strip.append((sx_, sy_, 2 * M.CREEK_HW + 1.0, M.natural(sx_, sy_) + 0.9))
    lip_z = strip[0][3]
    # (level as it runs: never higher downstream than up)
    for k in range(len(strip) - 2, -1, -1):
        x, y, wd, z = strip[k]
        strip[k] = (x, y, wd, min(z, strip[k + 1][3]))
    lip_z = strip[0][3]
    c.ribbon("Havasu Creek", list(reversed(strip)), 2 * M.CREEK_HW + 1.0, 0, c.lib("lagoon_shallow", "water"), role="visual", steps=2)
    c.disc("Havasu Spring", sx_, sy_, 7.4, strip[-1][3], c.lib("lagoon_shallow", "water"), role="visual", n=20, wobble=0.15, seed=7)
    # The falls: off the bench's lip (north) into the pool.
    top = lip_z
    props.falls(c, "Havasu Falls", fx + 2.0, fy + fr - 4.0, top, fz + 0.6, 10.0, 16.0, facing=-1, throw=5.0, bulge=1.2, veils=3,
                mats=("falls_oasis", "falls_curtain_oasis", "falls_foam"))
    g = c.game(fx + 2.0, fy + fr - 8.0, fz + 0.6)
    c.entity("waterfall", x=g[0], y=g[1], z=g[2], top=round(top - fz, 1), width=14.0, heading=0.0)


def sun_arch(c, ground):
    """The Gap Bridge's trestles (the gap between Sky Mesa and Dawn Mesa; the deck is the
    bridge kind): a bent of timber posts every 5 m along it, the outer ones battered out,
    from the deck's underside down to the gap's floor, their cross beams and the X braces
    between the bents; one solid mesh."""
    span = [q for q in c.S if M._land(q.p.x, q.p.y) < q.p.z - 4.0 and math.hypot(q.p.x - M.ARCH[0], q.p.y - M.ARCH[1]) < 24.0]
    if not span:
        return
    span.sort(key=lambda q: q.s)
    bm = bmesh.new()
    bents = []
    s = span[0].s + 2.0
    while s < span[-1].s - 1.0:
        q = c.at(s)
        top = q.p.z - 1.3
        feet = []
        for off, batter in ((-q.w / 2 - 0.6, -1.0), (0.0, 0.0), (q.w / 2 + 0.6, 1.0)):
            tx, ty = q.p.x + q.r.x * off, q.p.y + q.r.y * off
            foot_z = ground(tx, ty)
            lean = 0.12 * (top - foot_z) * batter
            fx, fy = tx + q.r.x * lean, ty + q.r.y * lean
            cp._beam(bm, (fx, fy, ground(fx, fy) - 0.5), (tx, ty, top), 0.45)
            feet.append(((fx, fy, ground(fx, fy)), (tx, ty, top)))
        # (cross beams across the bent every 4 m down)
        z = top - 0.3
        while z > max(ground(*feet[0][0][:2]), ground(*feet[2][0][:2])) + 1.0:
            pts = []
            for (fx, fy, fz_), (tx, ty, tz) in (feet[0], feet[2]):
                t = (tz - z) / max(0.1, tz - fz_)
                pts.append((lerp(tx, fx, t), lerp(ty, fy, t), z))
            cp._beam(bm, pts[0], pts[1], 0.3)
            z -= 4.0
        bents.append((s, feet))
        s += 5.0
    # (X braces between the bents, under each side of the deck)
    for (s0, f0), (s1, f1) in zip(bents, bents[1:]):
        for side in (0, 2):
            (ax_, ay_, az_), (atx, aty, atz) = f0[side]
            (bx_, by_, bz_), (btx, bty, btz) = f1[side]
            mid_a = (lerp(ax_, atx, 0.5), lerp(ay_, aty, 0.5), lerp(az_, atz, 0.5))
            mid_b = (lerp(bx_, btx, 0.5), lerp(by_, bty, 0.5), lerp(bz_, btz, 0.5))
            cp._beam(bm, (atx, aty, atz - 0.3), mid_b, 0.22)
            cp._beam(bm, (btx, bty, btz - 0.3), mid_a, 0.22)
        cp._beam(bm, (f0[1][1][0], f0[1][1][1], f0[1][1][2] - 0.2), (f1[1][1][0], f1[1][1][1], f1[1][1][2] - 0.2), 0.35)
    ob = c.mesh_object("Gap Bridge Trestles", bm, "Props", "both")
    c.assign(ob, c.lib("weathered_timber", "wall"))


# ------------------------------------------------------------------ the worlds


def _foot(ground, x, y, rot, w, d):
    """The lowest of the land under a building's footprint (w across, d deep, turned rot):
    where it stands, so none of its foot hangs over a slope."""
    ca, sa = math.cos(rot), math.sin(rot)
    return min(ground(x + lx * ca - ly * sa, y + lx * sa + ly * ca) for lx in (-w / 2, 0.0, w / 2) for ly in (-d / 2, 0.0, d / 2))


STREET = []  # (Main Street's points, from the lap west: filled in main())


def drift_cave(c, ground):
    """The Drift Cave's mouth: a crag of the crater's purple rock stood against its inner
    wall, the mouth dark in its face, propped with old mine timbers, lanterns on posts
    either side, the smugglers' barrels and crates on the ledge. (The game draws the
    mouth's rocks round the cave's spot, 2 m in from it.)"""
    cx, cy = M.CRATER[:2]
    ux, uy = math.cos(M.CAVE_A), math.sin(M.CAVE_A)  # (out from the crater's middle)
    tx, ty = -uy, ux
    rot = math.atan2(uy, ux)
    fx, fy = cx + ux * M.CAVE_FACE, cy + uy * M.CAVE_FACE
    z = ground(fx - ux * 1.5, fy - uy * 1.5)
    rk = c.rock_mass("Drift Cave Rock", fx + ux * 6.0, fy + uy * 6.0, 6.0, 10.0, z + 15.0, z0=z - 3.0, n=18, seed=21, angle=rot, base=z)
    c.assign(rk, c.lib("strata_purple", "wall"))
    box(c, "Drift Cave Mouth", fx + ux * 0.2, fy + uy * 0.2, 0.9, 2.6, z - 1.0, z + 5.6, ("dark_corridor", "wall"), rot=rot, role="visual")
    for sd in (-1, 1):
        px, py = fx - ux * 0.4 + tx * sd * 3.4, fy - uy * 0.4 + ty * sd * 3.4
        box(c, "Drift Cave Post %d" % sd, px, py, 0.3, 0.3, ground(px, py) - 0.5, z + 5.8, ("weathered_timber", "wall"), rot=rot)
        lx, ly = fx - ux * 2.6 + tx * sd * 6.0, fy - uy * 2.6 + ty * sd * 6.0
        c.place(gp.lantern_post(c), lx, ly, ground(lx, ly) - 0.1, rot=math.atan2(-sd * ty, -sd * tx), coll="Props")
        llx, _lly, llz = gp.LANTERN_POST_LIGHT
        g = c.game(lx - tx * sd * llx, ly - ty * sd * llx, ground(lx, ly) + llz)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
    bx, by = fx - ux * 0.4, fy - uy * 0.4
    box(c, "Drift Cave Lintel", bx, by, 0.35, 4.0, z + 5.8, z + 6.4, ("weathered_timber", "wall"), rot=rot, role="visual")
    for k, (o, a) in enumerate(((-7.8, 5.0), (7.6, 4.2), (-6.4, 7.0))):
        x, y = fx - ux * a + tx * o, fy - uy * a + ty * o
        c.place(("Barrel 0", "Crate Stack 1", "Barrel 1")[k], x, y, ground(x, y) - 0.05, rot=k * 1.3, coll="Props")


def trading_post(c, ground, taken, ter):
    """The frontier town where the Frozen Pass comes down (Blake, review-desert_region note
    2: "redo this whole front village ... lets go for old west town ... this needs to be a
    hopping old western town when we enter this world. we need to be brought back to the
    old west"): Main Street lined with the saloon, the bank, the barber's, the general
    store, the sheriff's and the hotel (mesa_dress.frontier_town, Dry Gulch's frontier
    kit). (It was a trading post: adobe homes round a paved square, a diner's neon sign
    and a gas pump.)"""
    md.frontier_town(c, ground, taken, ter, STREET)


def pueblo(c, ground, taken):
    """The cliff pueblo: in the great alcove in Pueblo Mesa's south face, under its
    overhang of rock, adobe homes stacked in three tiers back into the alcove, their
    roofs the terraces of the tier above, ladders between, round kivas in the plaza, ovens,
    ristras by the doors; its folk; the farms in the wash below."""
    ax, ay, w, dp = M.ALCOVE
    fz = M.ALCOVE_Z
    # The overhang (one shell of the mesa's caprock over the alcove) and the homes in three
    # tiers under it, Oasis Haven's adobe (mesa_dress, the deep pass).
    md.alcove_overhang(c)
    md.pueblo_homes(c, ground, taken)
    print("pueblo plaza: %d fires and things" % md.pueblo_plaza(c, ground))
    # The plaza in front: two kivas (round, sunken rooms, their ladders poking out), beehive
    # ovens, pots.
    for j, sx in enumerate((-1, 1)):
        kx, ky = ax + sx * 16.0, ay - 10.0
        kz = ground(kx, ky)
        c.disc("Kiva %d" % j, kx, ky, 4.2, kz + 0.25, c.lib("adobe", "wall"), coll="Props", role="visual", n=20)
        box(c, "Kiva Ladder %d" % j, kx, ky, 0.5, 0.06, kz, kz + 3.6, ("weathered_timber", "wall"), role="visual")
        cone(c, "Oven %d" % j, kx + sx * 8.0, ky + 2.0, 1.4, kz - 0.1, 2.0, ("adobe", "wall"), segs=10)
    g = c.game(ax, ay - 12.0, ground(ax, ay - 12.0) + 0.3)
    c.entity("campfire", x=g[0], y=g[1], z=g[2])
    g = c.game(ax, ay - 6.0, fz)
    c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=16.0, n=7, folk="desert", heading=0.0)
    for j in range(5):
        g = c.game(ax - w * 0.35 + j * w * 0.17, ay + 2.0, fz + 3.0)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
    # The farms in the wash below: rows of corn, a scarecrow pole, a fence.
    for r in range(8):
        rx, ry = ax - 24.0 + r * 6.0, ay - 34.0
        if paint.road_clear(c, rx, ry, 4.0):
            box(c, "Corn Row %d" % r, rx, ry, 0.6, 7.0, ground(rx, ry) - 0.2, ground(rx, ry) + 1.6, ("jungle_fern", "wall"),
                role="visual")
    taken.add(ax, ay - 34.0, 26.0)


def canyon_rim(c, ground, taken):
    """The Grand Canyon's rim: a timber railing along the overlook at Horseshoe Bend, its
    viewing scope, hoodoos in a crowd along the rim west (Bryce), junipers."""
    gx, gy = M.GATES["canyon"]
    # (The overlook's rail: mesa_dress.rim_rail, all along the rim.)
    c.place(ip.survey_scope(c), gx + 4.0, gy + 6.0, ground(gx + 4.0, gy + 6.0))
    rng = random.Random(7)
    n = 0
    for _ in range(600):
        x, y = rng.uniform(-150, 260), rng.uniform(220, 300)
        d = M.canyon_d(x, y)
        if not M.CANYON_HW + 5 < d < M.CANYON_HW + 40 or not taken.clear(x, y, 5.0) or not paint.road_clear(c, x, y, 7.0):
            continue
        z = ground(x, y)
        if z > M.FLOOR + 5.0:
            continue  # (none up on the buttes' tops: review-desert_region 3, note 6)
        # (a family of formations, not one column in sizes: note 5)
        k = n % (len(hf.FAMILY) + 1)
        h = rng.random()
        if k == len(hf.FAMILY):
            proto = cp.hoodoo(c, n % 2, height=8.0 + 7.0 * h)
        else:
            shape = hf.FAMILY[k]
            size = {"mushroom": 5.0 + 4.0 * h, "balanced": 7.0 + 5.0 * h, "spires": 10.0 + 6.0 * h, "fin": 7.0 + 5.0 * h,
                    "arch": 7.0 + 4.0 * h, "goblin": 3.5 + 3.0 * h, "totem": 9.0 + 6.0 * h}[shape.__name__]
            proto = shape(c, n % 2, height=round(size))
        c.place(proto, x, y, z - 0.4, rot=rng.uniform(0, 6.28))
        taken.add(x, y, 6.0)
        n += 1
        if n >= 34:
            break


def havasu(c, ground, taken):
    """Havasu's pools (Oasis Haven, until its course is reworked): the cottonwoods and
    willows round them, ferns at the water, a trail down."""
    fx, fy, fr, fz = M.FALLS
    for k in range(10):
        a = k * math.tau / 10 + 0.3
        x, y = fx + (fr - 4.0) * math.cos(a), fy + (fr - 4.0) * math.sin(a)
        if math.hypot(x - fx, y - fy - fr) < 10.0:
            continue
        c.place(smp_.broadleaf(c, k % 2, frosted=False), x, y, ground(x, y) - 0.2, rot=a, scale=0.9)
    for k in range(10):
        a = k * math.tau / 10 + 0.0
        x, y = fx + (fr - 7.0) * math.cos(a), fy + (fr - 7.0) * math.sin(a)
        c.place(ip.tree_fern(c, k % 2), x, y, ground(x, y) - 0.2, rot=a, role="visual")
    # Along the creek: cottonwoods and willows on its banks, reeds at the water, the spring's
    # ring of ferns.
    for (ax_, ay_), (bx_, by_) in zip(M.CREEK, M.CREEK[1:]):
        L = math.hypot(bx_ - ax_, by_ - ay_)
        nx, ny = -(by_ - ay_) / L, (bx_ - ax_) / L
        for k in range(int(L / 7.0)):
            t = (k + 0.5) / int(L / 7.0)
            for sd in (-1, 1):
                if (k + (sd > 0)) % 2:
                    continue
                x, y = lerp(ax_, bx_, t) + nx * sd * (M.CREEK_HW + 4.5), lerp(ay_, by_, t) + ny * sd * (M.CREEK_HW + 4.5)
                if taken.clear(x, y, 3.0) and paint.road_clear(c, x, y, 4.0):
                    c.place(smp_.broadleaf(c, k % 2, frosted=False), x, y, ground(x, y) - 0.2, rot=k + sd, scale=0.8 + 0.2 * (k % 3))
            x, y = lerp(ax_, bx_, t) + nx * (M.CREEK_HW + 0.8), lerp(ay_, by_, t) + ny * (M.CREEK_HW + 0.8)
            c.place(props.cattails(c, k % 2), x, y, ground(x, y) - 0.1, rot=k, role="visual")
    sx_, sy_ = M.CREEK[-1]
    for k in range(8):
        a = k * math.tau / 8
        x, y = sx_ + 9.0 * math.cos(a), sy_ + 9.0 * math.sin(a)
        c.place(ip.tree_fern(c, k % 2), x, y, ground(x, y) - 0.2, rot=a, role="visual")
    taken.add(sx_, sy_, 12.0)
    # (No palms: Oasis Haven's cottonwoods, mesa_dress.havasu_village.)


def boomtown(c, ground, taken, at):
    """The boomtown's folk (its buildings, Main Street's dressing, the water tower, Boot
    Hill and the railroad: mesa_dress.boomtown, Dry Gulch's own kit)."""
    x, y = at
    g = c.game(x - 30.0, y, ground(x - 30.0, y))
    c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=16.0, n=5, folk="desert", heading=0.0)


def crater(c, ground, taken):
    """Meteor Crater: the observatory on its rim (a round white tower and its dome), the
    surveyors' tents, warning signs along the rim, glowing shards down the bowl, the
    meteorite in its floor."""
    cx, cy, R, rim, fz = M.CRATER
    gx, gy = M.GATES["impact"]
    ox, oy, _r = M.OBSERVATORY  # (on its pad, cut level into the rim)
    oz = ground(ox, oy)
    # (No observatory any more: review-desert_region 3, note 11, "delete this building for
    # now". Its pad stays clear.)
    taken.add(ox, oy, 9.0)
    # (The survey camp and the rim's warning signs: mesa_dress.crater_camp.)
    rng = random.Random(11)
    for k in range(22):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(4.0, R * 0.8)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        if not paint.road_clear(c, x, y, 2.0):
            continue
        c.place(ip.glass_shards(c, k % 2), x, y, ground(x, y) - 0.3, rot=a, role="visual")
    c.place(ip.meteorite(c, 0, size=8.0), cx, cy, ground(cx, cy) - 1.5)
    g = c.game(ox + 8.0, oy, oz)
    c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=10.0, n=3, folk="desert", heading=0.0)


def showground(c, ground, taken):
    """Scorchwind's showground: the rodeo arena (a ring of timber rails round a sand floor),
    its grandstand under a roof, the chutes, flags on poles, braziers, caged performers;
    banners with his colours across the valley."""
    ax, ay, ar = M.ARENA
    GATE_A = math.atan2(M.GATES["lair"][1] - ay, M.GATES["lair"][0] - ax)
    z = ground(ax, ay)
    c.disc("Arena Floor", ax, ay, ar, z + 0.04, c.lib("red_sand", "loose_sand"), coll="Props", role="visual", n=40)
    # (Its fence one solid mesh, its gate east to the lair: mesa_dress.arena_fence.)
    md.arena_fence(c, ground, GATE_A)
    # The grandstand, north, in tiers, under a striped roof.
    for t in range(5):
        r = ar + 4.0 + t * 1.6
        for k in range(9):
            a = math.pi / 2 + (k - 4) * 0.14
            x, y = ax + r * math.cos(a), ay + r * math.sin(a)
            box(c, "Stand %d %d" % (t, k), x, y, 1.0, r * 0.075, z - 0.5, z + 0.6 + t * 0.9, ("weathered_timber", "wall"), rot=a)
    for k in range(9):
        a = math.pi / 2 + (k - 4) * 0.14
        x, y = ax + (ar + 13.0) * math.cos(a), ay + (ar + 13.0) * math.sin(a)
        box(c, "Stand Roof Post %d" % k, x, y, 0.15, 0.15, z - 0.3, z + 8.0, ("weathered_timber", "wall"))  # (solid)
        x2, y2 = ax + (ar + 8.5) * math.cos(a), ay + (ar + 8.5) * math.sin(a)
        box(c, "Stand Roof %d" % k, x2, y2, 5.2, (ar + 8.5) * 0.075, z + 7.6, z + 8.0, ("candy_stripe" if k % 2 else "awning_red", "wall"),
            rot=a, role="visual")
    taken.add(ax, ay + ar + 8.0, 16.0)
    # Banner poles round the ring, braziers at its gate, a row of cages (his performers).
    for k in range(8):
        a = k * math.tau / 8 + 0.2
        x, y = ax + (ar + 2.5) * math.cos(a), ay + (ar + 2.5) * math.sin(a)
        c.place(kp.banner_pole(c), x, y, ground(x, y) - 0.2, rot=a)
    for sd in (-1, 1):
        ga = GATE_A + sd * 0.2
        x, y = ax + (ar + 1.5) * math.cos(ga), ay + (ar + 1.5) * math.sin(ga)
        c.place(cp.brazier(c), x, y, ground(x, y) - 0.1)
        g = c.game(x, y, ground(x, y) + 2.6)
        c.entity("torch", x=g[0], y=g[1], z=g[2])
    for k in range(4):
        x, y = ax - ar - 8.0, ay - 12.0 + k * 6.0
        c.place(kp.cage(c), x, y, ground(x, y) + 0.1, rot=math.pi / 2)
    g = c.game(ax, ay + ar + 8.0, z + 3.0)
    c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=10.0, n=6, folk="desert", heading=0.0)


def ledge(c, ground, taken):
    """The Ledge Road's and the High Road's parapet: mesa_dress.parapet (one continuous wall,
    no blocks with gaps between)."""
    md.parapet(c, ground, taken)


def desert(c, ground, taken):
    """The floor alive: saguaros, joshua trees, barrel cacti, agave, sage, dry grass,
    boulders; the buttes' talus their own boulders."""
    rmax = 480.0

    def floor(x, y):
        return (natural(x, y) < 18.0 and M.canyon_d(x, y) > M.CANYON_HW + 4
                and math.hypot(x - M.CRATER[0], y - M.CRATER[1]) > M.CRATER[2] + 8)

    g = ground
    for v in range(2):
        # (Each set down on the lowest ground under it, nothing floating on a slope; the barrel
        # cacti knee-high, so solid: the overworld rules, the deep pass.)
        paint.scatter(c, cp.saguaro(c, v), 90, rmax, floor, g, taken, 10 + v, room=6.0, road_margin=6.0, trunk=(0.6, 6.0),
                      scale=(0.9, 1.5), seat=0.8)
        paint.scatter(c, cp.joshua_tree(c, v), 30, rmax, floor, g, taken, 12 + v, room=6.0, road_margin=6.0, trunk=(0.6, 5.0),
                      seat=1.0)
        paint.scatter(c, cp.barrel_cactus(c, v), 60, rmax, floor, g, taken, 14 + v, room=2.5, road_margin=3.0, trunk=(0.5, 1.2),
                      seat=0.6)
        paint.scatter(c, cp.sagebrush(c, v), 220, rmax, floor, g, taken, 16 + v, room=2.5, role="visual", seat=0.8)
        paint.scatter(c, cp.boulder(c, v), 40, rmax, lambda x, y: natural(x, y) < 40.0, g, taken, 18 + v, room=4.0,
                      road_margin=7.0, scale=(1.0, 2.6), seat=1.6)
    paint.scatter(c, cp.agave(c, 0), 80, rmax, floor, g, taken, 20, room=2.5, road_margin=3.0, role="visual", seat=0.8)
    paint.scatter(c, cp.dry_grass(c, 0), 160, rmax, floor, g, taken, 21, room=2.0, role="visual", seat=0.6)
    paint.scatter(c, gp.tumbleweed(c, 0), 30, rmax, floor, g, taken, 22, room=3.0, role="visual", seat=0.6)
    paint.scatter(c, gp.cattle_skull(c), 10, rmax, floor, g, taken, 23, room=3.0, role="visual", seat=0.5)


if __name__ == "__main__":
    main()
