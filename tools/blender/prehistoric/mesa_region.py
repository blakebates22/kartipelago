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
from course_kit import lerp, smooth  # noqa: E402
import region_ruin as ruin  # noqa: E402
import puzzle_kit  # noqa: E402
import pocket_build as pb  # noqa: E402
from pocket_build import box, cone  # noqa: E402
import canyon_props as cp  # noqa: E402
import oasis_props as op  # noqa: E402
import gulch_props as gp  # noqa: E402
import impact_props as ip  # noqa: E402
import keep_props as kp  # noqa: E402
import summit_props as smp_  # noqa: E402
import props  # noqa: E402
import region_paint as paint  # noqa: E402
import desert_dress as dd  # noqa: E402
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
# The cliffs in beds of colour by height (Monument Valley's): (top of the bed, rock).
BEDS = [(4.0, "strata_red"), (16.0, "strata_rust"), (22.0, "strata_orange"), (34.0, "strata_red"), (40.0, "strata_cream"),
        (58.0, "strata_orange"), (64.0, "strata_rust"), (80.0, "strata_red"), (88.0, "strata_cream"), (999.0, "strata_orange")]


def natural(x, y):
    return M.natural(x, y)


def classify(c, n, info):
    look = M.look_at(c.x, c.y)
    if n.z < 0.62:
        if M.canyon_d(c.x, c.y) < M.CANYON_HW + 2 or math.hypot(c.x - M.FALLS[0], c.y - M.FALLS[1]) < M.FALLS[2] + 30:
            z = c.z - M.CANYON_DEPTH
            return (("strata_red", "strata_cream", "strata_rust", "strata_orange")[int(z / 7.0) % 4], "wall")
        if math.hypot(c.x - M.CRATER[0], c.y - M.CRATER[1]) < M.CRATER[2] * 1.3:
            return ("strata_purple", "wall")
        for top, rock in BEDS:
            if c.z < top + 1.5 * math.sin(c.x / 17.0):
                return (rock, "wall")
    if n.z < 0.85:
        return ("talus", "dirt")
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
    # Sun Arch's deck: the road over the arch, its stone the arch's own.
    kinds["bridge"] = {"mat": "dash_road", "surface": "road", "shoulder": 0.8, "shoulder_mat": ("slickrock", "road"),
                       "barrier": 0.9, "barrier_mat": ("strata_cream", "wall"), "deck": 3.0, "deck_mat": ("strata_orange", "wall"),
                       "ground": False}
    c.kinds = kinds

    def label(q):
        if M._land(q.p.x, q.p.y) < q.p.z - 4.0 and math.hypot(q.p.x - M.ARCH[0], q.p.y - M.ARCH[1]) < 24.0:
            return "bridge"
        return M.look_at(q.p.x, q.p.y)

    c.roads(kit.plan(c, pb.blend_runs(c, list(kit.runs(c, label)), {k: (v[0], None, v[1], v[2]) for k, v in LOOK.items()}),
                     "post", max_len=160.0))

    trail = dict(width=10.0, shoulder=1.2, shoulder_mat=("dash_shoulder", "dirt"))
    # The post's square, off the road; the Frozen Pass road west out of it.
    px, py, pr = M.POST
    smp, _ = c.nearest(px + pr + 12.0, py)
    c.side_road("Square Road", list(reversed(pb.line(natural, (smp.p.x, smp.p.y), (px + pr - 2.0, py), z0=smp.p.z, c=c))),
                "dash_road", "road", **trail)
    fx, fy = M.FROZEN_PASS
    way = [(x, py, natural(x, py) + 0.2) for x in range(int(px - pr + 2), int(fx - 6), -8)]
    c.side_road("Frozen Pass Road", way, "dash_road", "road", **trail)
    gates = dict(M.GATES)
    if not RUIN:
        gates.pop("lair")
    spots = pb.spurs(c, natural, gates, lambda x, y: LOOK[M.look_at(x, y)][1], trail)
    if RUIN:
        (ax, ay), (bx, by), _z, _hw = M.PASS_WAYS[1]
        smp, _ = c.nearest(ax, ay)
        first = pb.line(natural, (smp.p.x, smp.p.y), (ax, ay), z0=smp.p.z, c=c)
        rest = pb.line(natural, (ax, ay), (bx, by + 8.0), z0=first[-1][2], c=c)
        c.side_road("Dust Road", first + rest[1:], "dash_road", "road", **trail)

    X0, X1, Y0, Y1 = -470, 470, -470, 470
    ter = c.terrain("Desert World", X0, X1, Y0, Y1, 3.0, natural, classify, near=8.0, fade=16.0, verge_fill=1.5)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 6.0, lambda x, y: natural(x, y) - 0.5, c.lib("red_sand", "loose_sand"))

    def ground(x, y):
        z = c.ground_z(x, y, [ter])
        return natural(x, y) if z is None else z

    taken = paint.Taken([(px, py, pr + 10.0), (*M.ALCOVE[:2], 44.0), (*M.ARENA[:2], M.ARENA[2] + 16.0), (*M.CAVE, 16.0),
                         (*M.SECRET, 14.0), (M.FALLS[0], M.FALLS[1], M.FALLS[2] + 14.0),
                         *((e[0], e[1], 14.0) for e, _ in spots.values()), *((x, y, 16.0) for x, y in M.GATES.values())])
    water(c)
    sun_arch(c, ground)
    trading_post(c, ground, taken)
    pueblo(c, ground, taken)
    canyon_rim(c, ground, taken)
    havasu(c, ground, taken)
    boomtown(c, ground, taken)
    crater(c, ground, taken)
    showground(c, ground, taken)
    ledge(c, ground, taken)
    puzzle_kit.pen(c, "return", "Old Well", *M.CAVE, pb.to_road(c, *M.CAVE), 11.0, 4.5, ("adobe", "wall"), ground(*M.CAVE),
                   height=6.0)
    puzzle_kit.pen(c, "secret", "Sunken Garden", *M.SECRET, pb.to_road(c, *M.SECRET), 9.0, 4.5, ("oasis_stone", "wall"),
                   ground(*M.SECRET), height=6.0)
    pb.emit_spots(c, spots)
    desert(c, ground, taken)
    if RUIN:
        c.entity("ashfall", rate=8, radius=40)  # (dust on the wind)

    c.start_line()
    gts = c.checkpoints(height=10.0)
    kit.paint.shade_roads(c.pieces, 0.3)
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
    # The falls: off the side canyon's lip (north) into the pool.
    top = M.FLOOR + 1.0
    props.falls(c, "Havasu Falls", fx + 2.0, fy + fr - 4.0, top, fz + 0.6, 10.0, 16.0, facing=-1, throw=5.0, bulge=1.2, veils=3,
                mats=("falls_oasis", "falls_curtain_oasis", "falls_foam"))
    g = c.game(fx + 2.0, fy + fr - 8.0, fz + 0.6)
    c.entity("waterfall", x=g[0], y=g[1], z=g[2], top=round(top - fz, 1), width=14.0, heading=0.0)


def sun_arch(c, ground):
    """Sun Arch: a great natural arch over the gap between Sky Mesa and Dawn Mesa, the road
    on its back (the road's deck is the bridge kind; this is the arch's body and its legs
    down to the floor)."""
    x0, y0, x1, y1 = M.ARCH_SPAN
    rot = math.atan2(y1 - y0, x1 - x0)
    q, _ = c.nearest(*M.ARCH)
    # (Its legs down in the gap, on the floor; its crown just under the road's deck.)
    span = math.hypot(x1 - x0, y1 - y0) * 0.72
    ca, sa = math.cos(rot), math.sin(rot)
    base = max(ground(M.ARCH[0] - ca * span / 2, M.ARCH[1] - sa * span / 2),
               ground(M.ARCH[0] + ca * span / 2, M.ARCH[1] + sa * span / 2))
    dd.natural_arch(c, "Sun Arch", M.ARCH[0], M.ARCH[1], rot, span, q.p.z - base - 3.2,
                    ("strata_orange", "strata_cream", "strata_red"), ground, seed=5)


# ------------------------------------------------------------------ the worlds


def _foot(ground, x, y, rot, w, d):
    """The lowest of the land under a building's footprint (w across, d deep, turned rot):
    where it stands, so none of its foot hangs over a slope."""
    ca, sa = math.cos(rot), math.sin(rot)
    return min(ground(x + lx * ca - ly * sa, y + lx * sa + ly * ca) for lx in (-w / 2, 0.0, w / 2) for ly in (-d / 2, 0.0, d / 2))


def trading_post(c, ground, taken):
    """The roadside trading post where the Frozen Pass comes down: adobe houses round its
    square, the diner, its neon sign on a tall post, a gas pump under a canopy, the
    windmill and its tank, stalls of blankets and pots."""
    px, py, pr = M.POST
    z = ground(px, py)
    c.disc("Post Square", px, py, pr, z + 0.03, c.lib("palace_paving", "road"), coll="Props", role="collision", n=36)
    for k, (a, w, d, h) in enumerate(((0.9, 12.0, 9.0, 5.0), (1.9, 9.0, 8.0, 6.0), (2.9, 10.0, 8.0, 5.5), (4.2, 11.0, 9.0, 6.5),
                                      (5.2, 8.0, 7.0, 5.0))):
        x, y = px + (pr + 7.0) * math.cos(a), py + (pr + 7.0) * math.sin(a)
        dd.adobe_house(c, "Post House %d" % k, x, y, _foot(ground, x, y, a - math.pi / 2, w, d) - 0.1, a - math.pi / 2, w, d, h, k)
        taken.add(x, y, 7.0)
    # The diner: a long low block with a big lit window band, its neon sign up on a post.
    dx_, dy_ = px + 4.0, py - pr - 12.0
    dz = ground(dx_, dy_)
    box(c, "Diner", dx_, dy_, 9.0, 4.5, dz - 1.0, dz + 4.2, ("siding_ochre", "wall"))
    box(c, "Diner Roof", dx_, dy_, 9.6, 5.0, dz + 4.2, dz + 4.8, ("tin_roof", "wall"), role="visual")
    box(c, "Diner Windows", dx_, dy_ + 4.52, 7.5, 0.05, dz + 1.2, dz + 3.2, ("window_lit", "wall"), role="visual")
    box(c, "Neon Post", dx_ + 12.0, dy_ + 6.0, 0.25, 0.25, dz - 0.5, dz + 11.0, ("rail_iron", "wall"))
    box(c, "Neon Sign", dx_ + 12.0, dy_ + 6.0, 3.2, 0.3, dz + 8.0, dz + 11.5, ("lantern_amber", "wall"), role="visual")
    box(c, "Neon Arrow", dx_ + 12.0, dy_ + 6.0, 1.6, 0.32, dz + 6.8, dz + 7.6, ("fire_glow", "wall"), role="visual")
    taken.add(dx_, dy_, 12.0)
    # The gas pump under its canopy.
    gx_, gy_ = px + pr + 2.0, py - pr + 2.0
    gz = ground(gx_, gy_)
    for sx in (-1, 1):
        box(c, "Canopy Post %d" % sx, gx_ + sx * 3.0, gy_, 0.2, 0.2, gz - 0.3, gz + 4.6, ("rail_iron", "wall"))
    box(c, "Canopy", gx_, gy_, 4.2, 2.6, gz + 4.6, gz + 5.0, ("siding_red", "wall"), role="visual")
    box(c, "Gas Pump", gx_, gy_, 0.45, 0.35, gz - 0.2, gz + 1.9, ("siding_red", "wall"))
    box(c, "Gas Pump Globe", gx_, gy_, 0.3, 0.3, gz + 1.9, gz + 2.4, ("lantern_amber", "wall"), role="visual")
    taken.add(gx_, gy_, 5.0)
    wx, wy = px - 10.0, py + pr + 10.0
    c.place(cp.windmill_tower(c), wx, wy, _foot(ground, wx, wy, 0.0, 5.0, 5.0) - 0.2)
    c.place(cp.water_tank(c), wx + 7.0, wy + 2.0, ground(wx + 7.0, wy + 2.0) - 0.2)
    taken.add(wx, wy, 8.0)
    for k in range(3):
        a = 3.4 + k * 0.5
        x, y = px + (pr - 4.0) * math.cos(a), py + (pr - 4.0) * math.sin(a)
        c.place(op.market_stall(c, k % 3), x, y, ground(x, y) - 0.05, rot=a + math.pi / 2)
    for k in range(6):
        a = k * math.tau / 6 + 0.3
        g = c.game(px + (pr - 1.0) * math.cos(a), py + (pr - 1.0) * math.sin(a), z + 3.4)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
    g = c.game(px, py - 4.0, z)
    c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=pr - 2.0, n=5, folk="desert", heading=0.0)


def pueblo(c, ground, taken):
    """The cliff pueblo: in the great alcove in Pueblo Mesa's south face, under its
    overhang of rock, adobe homes stacked in three tiers back into the alcove, their
    roofs the terraces of the tier above, ladders between, round kivas in the plaza, ovens,
    ristras by the doors; its folk; the farms in the wash below."""
    ax, ay, w, dp = M.ALCOVE
    fz = M.FLOOR + 6.0
    # The overhang: a slab of the mesa's caprock out over the alcove, its lip ragged.
    top = 82.0
    for k in range(7):
        t = (k - 3) / 3.0
        x = ax + t * w * 0.42
        reach = dp * (1.0 - 0.5 * abs(t) ** 2)
        box(c, "Alcove Overhang %d" % k, x, ay + dp - reach / 2, w * 0.08, reach / 2 + 1.0, fz + 22.0 + 2.0 * abs(t),
            top - 8.0, ("strata_cream" if k % 2 else "strata_orange", "wall"), role="visual")
    box(c, "Alcove Back", ax, ay + dp + 1.0, w / 2, 3.0, fz - 1.0, top - 6.0, ("strata_rust", "wall"))
    # The homes: three tiers stepping back into the alcove.
    k = 0
    for tier in range(3):
        n = (6, 5, 3)[tier]
        y = ay + 3.0 + tier * 6.5
        z = fz + tier * 4.2
        span = w * (0.78 - 0.14 * tier)
        for j in range(n):
            x = ax - span / 2 + (j + 0.5) * span / n
            ww, dd_ = 7.5 - 0.6 * (j % 2), 6.0
            dd.adobe_house(c, "Pueblo Home %d" % k, x, y, z - 0.1, math.pi, ww, dd_, 4.2, k, lit=True)
            # A ladder up its front to the roof (the tier above's terrace).
            lx, ly = x + ww * 0.3, y - dd_ / 2 - 0.6
            for sd in (-1, 1):
                box(c, "Pueblo Ladder %d %d" % (k, sd), lx + sd * 0.35, ly, 0.06, 0.06, z - 0.2, z + 5.0, ("weathered_timber", "wall"),
                    role="visual")
            for r in range(6):
                box(c, "Pueblo Rung %d %d" % (k, r), lx, ly, 0.38, 0.04, z + 0.6 + 0.75 * r, z + 0.66 + 0.75 * r,
                    ("weathered_timber", "wall"), role="visual")
            # Ristras (strings of red chiles) by its door.
            box(c, "Ristra %d" % k, x - ww * 0.3, y - dd_ / 2 - 0.15, 0.12, 0.12, z + 1.6, z + 3.0, ("party_red", "wall"),
                role="visual")
            k += 1
        # The terrace in front of the tier: the roofs below it, a level floor.
        box(c, "Pueblo Terrace %d" % tier, ax, y - 3.6, span / 2 + 2.0, 1.4, fz - 1.0 + tier * 4.2, z - 0.05, ("adobe", "wall"))
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
    for k in range(12):
        t = (k - 5.5) / 5.5
        x, y = gx + t * 22.0, gy + 12.0 - 3.0 * t * t
        if M.canyon_d(x, y) > M.CANYON_HW - 2.0:
            z = ground(x, y)
            box(c, "Overlook Post %d" % k, x, y, 0.12, 0.12, z - 0.3, z + 1.2, ("weathered_timber", "wall"))
            box(c, "Overlook Rail %d" % k, x, y, 2.0, 0.08, z + 1.0, z + 1.15, ("fence_rail", "wall"), role="visual")
    c.place(ip.survey_scope(c), gx + 4.0, gy + 6.0, ground(gx + 4.0, gy + 6.0))
    rng = random.Random(7)
    n = 0
    for _ in range(400):
        x, y = rng.uniform(-150, 260), rng.uniform(220, 300)
        d = M.canyon_d(x, y)
        if not M.CANYON_HW + 5 < d < M.CANYON_HW + 40 or not taken.clear(x, y, 5.0) or not paint.road_clear(c, x, y, 7.0):
            continue
        c.place(cp.hoodoo(c, n % 2, height=8.0 + 7.0 * rng.random()), x, y, ground(x, y) - 0.4, rot=rng.uniform(0, 6.28))
        taken.add(x, y, 5.0)
        n += 1
        if n >= 26:
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
    gx, gy = M.GATES["oasis"]
    for k in range(3):
        c.place(op.palm(c, k, height=9.0 + 2.0 * k), gx + 8.0 * math.cos(k * 2.1), gy + 8.0 * math.sin(k * 2.1),
                ground(gx, gy) - 0.2)


def boomtown(c, ground, taken):
    """The mining town on the road under Copper Mesa: false fronts down both sides of its
    street, the water tower, the railroad in along the mesa's foot to the depot, ore carts,
    the mine's headframe up on the talus, barrels and wagons."""
    sidings = ("siding_brown", "siding_grey", "siding_red", "siding_ochre", "siding_green")
    k = 0
    for q in c.S[::12]:
        if M.look_at(q.p.x, q.p.y) != "town" or not -110.0 < q.p.y < 50.0:
            continue
        for sd in (-1, 1):
            off = q.w / 2 + 5.5
            x, y = q.p.x + q.r.x * sd * off, q.p.y + q.r.y * sd * off
            if not taken.clear(x, y, 7.0) or not paint.road_clear(c, x, y, 4.0):
                continue
            rot = math.atan2(q.r.y * sd, q.r.x * sd) - math.pi / 2
            w = 9.0 + 2.0 * (k % 3)
            ca, sa = math.cos(rot), math.sin(rot)
            foot = [ground(x + lx * ca - ly * sa, y + lx * sa + ly * ca) for lx in (-w / 2, 0.0, w / 2) for ly in (0.0, 5.0, 10.0)]
            if max(foot) - min(foot) > 3.0:
                continue
            _false_front(c, "Boomtown House %d" % k, x, y, ground(x, y), rot, w, 10.0, sidings[k % len(sidings)],
                         lit=not RUIN and k % 3 != 1, foot=min(foot) - 0.4)
            taken.add(x, y, 8.0)
            k += 1
    tx, ty, tl, th = M.TOWN
    wx, wy = tx - 30.0, ty + 40.0
    c.place(cp.water_tank(c), wx, wy, ground(wx, wy) - 0.2, scale=1.4)
    taken.add(wx, wy, 6.0)
    # The railroad: ties and rails along the mesa's foot into the depot, a cart on it.
    pts = [(250.0, -260.0), (262.0, -190.0), (258.0, -140.0), (240.0, -80.0), (236.0, -10.0), (244.0, 60.0)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay)
        rot = math.atan2(by - ay, bx - ax)
        n = int(L / 2.4)
        for j in range(n):
            t = (j + 0.5) / n
            x, y = lerp(ax, bx, t), lerp(ay, by, t)
            if not paint.road_clear(c, x, y, 1.5):
                continue
            z = ground(x, y)
            box(c, "Tie %d %d" % (int(ax), j), x, y, 0.3, 1.5, z - 0.1, z + 0.12, ("weathered_timber", "wall"), rot=rot, role="visual")
        for sd in (-1, 1):
            ox, oy = -math.sin(rot) * sd * 0.75, math.cos(rot) * sd * 0.75
            strip = [(lerp(ax, bx, t) + ox, lerp(ay, by, t) + oy) for t in (0.0, 1.0)]
            zr = (ground(ax, ay) + ground(bx, by)) / 2 + 0.2
            c.ribbon("Rail %d %d" % (int(ax), sd), strip, 0.14, zr, c.lib("rail_iron", "wall"), role="visual")
    for k, (x, y) in enumerate(((238.0, -40.0), (240.0, -30.0))):
        c.place(gp.ore_cart(c, glow=False), x, y, ground(x, y) + 0.1, rot=math.pi / 2)
    for k in range(6):
        a = k * 1.3
        x, y = tx - 12.0 + 6.0 * math.cos(a), ty - 50.0 + 6.0 * math.sin(a)
        if taken.clear(x, y, 1.5):
            c.place(gp.barrel(c, k % 2), x, y, ground(x, y))
    g = c.game(tx - 10.0, ty, ground(tx - 10.0, ty))
    c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=16.0, n=5, folk="desert", heading=0.0)


def _false_front(c, name, x, y, z, rot, w, d, siding, lit=True, foot=None):
    ca, sa = math.cos(rot), math.sin(rot)

    def at(lx, ly):
        return x + lx * ca - ly * sa, y + lx * sa + ly * ca

    bx, by = at(0.0, d / 2)
    box(c, name, bx, by, w / 2, d / 2, min(z - 1.0, foot if foot is not None else z - 1.0), z + 5.0, (siding, "wall"), rot=rot)
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
        p2x, p2y = at(k * (w / 2 - 0.3), -3.0)
        box(c, name + " Porch Post %d" % k, p2x, p2y, 0.12, 0.12, z - 0.2, z + 3.5, ("weathered_timber", "wall"), rot=rot)


def crater(c, ground, taken):
    """Meteor Crater: the observatory on its rim (a round white tower and its dome), the
    surveyors' tents, warning signs along the rim, glowing shards down the bowl, the
    meteorite in its floor."""
    cx, cy, R, rim, fz = M.CRATER
    gx, gy = M.GATES["impact"]
    ox, oy, _r = M.OBSERVATORY  # (on its pad, cut level into the rim)
    oz = ground(ox, oy)
    c.place(paint.trunk_proto(c, 5.0, 9.0), ox, oy, oz - 1.0, coll="Collision", role="collision")
    cone(c, "Observatory Tower", ox, oy, 5.4, oz - 1.0, 9.0 + 4.0, ("arcade_white", "wall"), segs=16, role="visual")
    box(c, "Observatory Base", ox, oy, 5.0, 5.0, oz - 1.0, oz + 7.0, ("arcade_white", "wall"), role="visual")
    import oasis_props as _op

    def dome(bm):
        _op.dome(bm, ox, oy, oz + 7.0, 5.2)

    import bmesh

    bm = bmesh.new()
    dome(bm)
    ob = c.mesh_object("Observatory Dome", bm, "Props", "visual")
    c.assign(ob, c.lib("tin_roof", "wall"))
    box(c, "Observatory Slit", ox, oy - 0.2, 0.7, 5.3, oz + 8.0, oz + 12.0, ("dark_corridor", "wall"), rot=1.9, role="visual")
    taken.add(ox, oy, 9.0)
    for k in range(3):
        a = 1.4 + k * 0.35
        x, y = cx + (R + 24.0) * math.cos(a), cy + (R + 24.0) * math.sin(a)
        if taken.clear(x, y, 4.0) and paint.road_clear(c, x, y, 4.0):
            c.place(ip.tent(c, k % 2), x, y, ground(x, y) - 0.1, rot=a)
            taken.add(x, y, 4.0)
    for k in range(10):
        a = k * math.tau / 10 + 0.2
        x, y = cx + (R + 3.0) * math.cos(a), cy + (R + 3.0) * math.sin(a)
        if paint.road_clear(c, x, y, 3.0):
            c.place(ip.warning_sign(c, k % 2), x, y, ground(x, y), rot=a)
    rng = random.Random(11)
    for k in range(22):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(4.0, R * 0.8)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
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
    n = 36
    for k in range(n):
        a = k * math.tau / n
        if abs((a - GATE_A + math.pi) % math.tau - math.pi) < 0.12:
            continue  # (its gate, east, to the lair)
        x, y = ax + ar * math.cos(a), ay + ar * math.sin(a)
        box(c, "Arena Post %d" % k, x, y, 0.16, 0.16, ground(x, y) - 0.3, ground(x, y) + 1.9, ("weathered_timber", "wall"))
        for j in (0.8, 1.6):
            box(c, "Arena Rail %d %d" % (k, j * 10), x, y, 0.08, ar * math.pi / n, ground(x, y) + j, ground(x, y) + j + 0.14,
                ("fence_rail", "wall"), rot=a, role="visual")
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
        box(c, "Stand Roof Post %d" % k, x, y, 0.15, 0.15, z - 0.3, z + 8.0, ("weathered_timber", "wall"), role="visual")
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
    """The Ledge Road and the High Road: a low stone parapet along the drop side, cairns at
    its bends."""
    k = 0
    for q in c.S[::6]:
        if not (q.p.z > 16.0 and M.look_at(q.p.x, q.p.y) in ("mesa", "show", "post")):
            continue
        for sd in (-1, 1):
            x, y = q.p.x + q.r.x * sd * (q.w / 2 + 1.0), q.p.y + q.r.y * sd * (q.w / 2 + 1.0)
            if natural(x + q.r.x * sd * 5.0, y + q.r.y * sd * 5.0) < q.p.z - 3.0 and paint.road_clear(c, x, y, 0.4):
                box(c, "Ledge Wall %d" % k, x, y, 0.4, 1.6, q.p.z - 1.0, q.p.z + 0.7, ("strata_cream", "wall"),
                    rot=math.atan2(q.t.y, q.t.x) + math.pi / 2)
                k += 1


def desert(c, ground, taken):
    """The floor alive: saguaros, joshua trees, barrel cacti, agave, sage, dry grass,
    boulders; the buttes' talus their own boulders."""
    rmax = 480.0

    def floor(x, y):
        return (natural(x, y) < 18.0 and M.canyon_d(x, y) > M.CANYON_HW + 4
                and math.hypot(x - M.CRATER[0], y - M.CRATER[1]) > M.CRATER[2] + 8)

    g = ground
    for v in range(2):
        paint.scatter(c, cp.saguaro(c, v), 90, rmax, floor, g, taken, 10 + v, room=6.0, road_margin=6.0, trunk=(0.6, 6.0),
                      scale=(0.9, 1.5))
        paint.scatter(c, cp.joshua_tree(c, v), 30, rmax, floor, g, taken, 12 + v, room=6.0, road_margin=6.0, trunk=(0.6, 5.0))
        paint.scatter(c, cp.barrel_cactus(c, v), 60, rmax, floor, g, taken, 14 + v, room=2.5, road_margin=3.0, role="visual")
        paint.scatter(c, cp.sagebrush(c, v), 220, rmax, floor, g, taken, 16 + v, room=2.5, role="visual")
        paint.scatter(c, cp.boulder(c, v), 40, rmax, lambda x, y: natural(x, y) < 40.0, g, taken, 18 + v, room=4.0,
                      road_margin=7.0, scale=(1.0, 2.6))
    paint.scatter(c, cp.agave(c, 0), 80, rmax, floor, g, taken, 20, room=2.5, road_margin=3.0, role="visual")
    paint.scatter(c, cp.dry_grass(c, 0), 160, rmax, floor, g, taken, 21, room=2.0, role="visual")
    paint.scatter(c, gp.tumbleweed(c, 0), 30, rmax, floor, g, taken, 22, room=3.0, role="visual")
    paint.scatter(c, gp.cattle_skull(c), 10, rmax, floor, g, taken, 23, room=3.0, role="visual")


if __name__ == "__main__":
    main()
