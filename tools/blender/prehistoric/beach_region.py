# Tropic Isles, the overworld's fourth region (v3): built from beach_layout.py's pockets
# (Blake, Oct 26: each world walled off by landscape, the main road one loop through them
# by a threshold each time; see beach_layout.py for the plan).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/beach_region.py [--ruin]      (the bpy module)
#
# (--ruin: after Tidewyrm's attack. Only the ruin has his sea cave and his Causeway out
# over the sea from the pier, south; his wave has flattened the village, snapped the palms
# and strewn wreckage up the beaches.)

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import pocket_kit  # noqa: E402
from course_kit import Vector, lerp  # noqa: E402
import region_ruin as ruin  # noqa: E402
import puzzle_kit  # noqa: E402
import pocket_build as pb  # noqa: E402
from pocket_build import box, cone  # noqa: E402
import props  # noqa: E402
import beach_props as bp  # noqa: E402
import tropic_props as tp  # noqa: E402
import villager_homes as vh  # noqa: E402
import swamp_props as swp  # noqa: E402
import region_paint as paint  # noqa: E402
import beach_layout as BL  # noqa: E402

RUIN = ruin.ON
TRACK_ID = ruin.track_id("beach_region") + os.environ.get("KP_REGION_SUFFIX", "")
L = BL.L
HUB = BL.HUB
FLOOR_Z = HUB[3]
WATER_Z = BL.WATER_Z
RIM_Z = BL.TOP

# The Tiki Gongs (src/overworld/puzzles.ts): a tiki hut behind the village, its door shut,
# and three gongs to strike in order (their torches: one, two, three): one in the water
# park, one by the lagoon, one on Coral's beach.
HUT = (-6.2, 187.2)
GONGS = [(-116.6, 80.6), (63.2, 14.9), (145.1, -140.1)]
# Raptor's cove (Act V's return task): a walled yard at Shipwreck's beach, its way in cut
# off by a deep channel the Beach Tool gets you over.
RETURN = (-163.7, -64.5)
# A secret: a smugglers' cave by the pier's cove, behind a rockfall (the Valley Tool's).
SECRET = (-33.5, -158.7)

LOOK = {
    # look: (ground, cliff, road, shoulder)
    "village": (("isle_jungle", "grass"), ("isle_rock", "wall"), "beach_road", ("isle_jungle", "grass")),
    "splash": (("isle_jungle", "grass"), ("cove_rock", "wall"), "cove_road", ("cove_sand", "sand")),
    "shipwreck": (("wreck_sand", "sand"), ("wreck_rock", "wall"), "wreck_road", ("wreck_sand", "sand")),
    "pier": (("cove_sand", "sand"), ("cove_rock", "wall"), "cove_road", ("cove_sand", "sand")),
    "coral": (("cove_sand", "sand"), ("cove_rock", "wall"), "cove_road", ("cove_sand", "sand")),
    "lagoon": (("beach_sand", "sand"), ("isle_rock", "wall"), "beach_road", ("beach_sand", "sand")),
}
# v4 (Blake, Oct 28): the headlands and hills rise in tiers (pocket_kit.terrace), a bed of
# each world's rock to a tier, foot to rim.
STRATA = {
    "village": ["isle_rock", "cove_rock", "isle_rock", "splash_rock", "isle_rock"],
    "splash": ["splash_rock", "cove_rock", "isle_rock", "splash_rock", "isle_rock"],
    "shipwreck": ["wreck_rock", "cove_rock", "wreck_rock", "isle_rock", "wreck_rock"],
    "pier": ["cove_rock", "isle_rock", "cove_rock", "wreck_rock", "cove_rock"],
    "coral": ["cove_rock", "isle_rock", "cove_rock", "splash_rock", "cove_rock"],
    "lagoon": ["isle_rock", "cove_rock", "isle_rock", "cove_rock", "isle_rock"],
}
WET = {"shipwreck": ("wreck_wet_sand", "water"), "pier": ("cove_wet_sand", "water"), "coral": ("cove_wet_sand", "water")}


def _natural(x, y):
    h = BL.natural(x, y)
    tz = L.tunnel_floor(x, y)
    if tz is not None:
        h = min(h, tz - 0.25)
    bz = L.bridge_floor(x, y)
    if bz is not None:
        h = min(h, bz)
    return h


# The ways in to the gateways cut level with the road (pocket_kit.Notches: a gateway's
# spur mustn't climb a wall).
NOTCHES = pocket_kit.Notches(BL.route_points(), dict({k: v for k, v in BL.GATES.items() if k != "volcano"}, **({"lair": BL.LAIR} if RUIN else {})))


# The Dust Road's way north from the village square to the passage, cut through the
# pockets' walls it crosses (pocket_kit.Cut).
DUST_CUT = pocket_kit.Cut([(0.0, float(y)) for y in range(int(BL.HUB[1] + BL.HUB[2] - 2), int(BL.DUST_END[1]) + 8, 8)],
                          _natural(0.0, BL.HUB[1] + BL.HUB[2] - 2), _natural(*BL.DUST_END))


def natural(x, y):
    return NOTCHES.apply(DUST_CUT.apply(_natural(x, y), x, y), x, y)


def classify(c, n, info):
    look = L.look_at(c.x, c.y)
    ground, cliff, _, _ = LOOK[look]
    # (on the tiered walls only the shelves' flat tops are ground)
    if n.z < (0.8 if L.wall_info(c.x, c.y)["t"] > 0.05 else 0.62):
        return (pb.strata(L, c, n, STRATA), "wall")
    if c.z < WATER_Z + 0.3:
        return WET.get(look, ("lagoon_shallow", "water"))  # (the shallows are wadeable)
    if look in WET and c.z < WATER_Z + 1.6:
        return WET[look]
    return pb.transition(L.look_weights(c.x, c.y), lambda lk: LOOK[lk][0])


# Where Tidewyrm's Causeway leaves the beach (the ruin), west of the pier.
CAUSEWAY_START = (-37.2, -162.4)


def main():
    c = kit.Course(TRACK_ID, "Tropic Isles (ruined)" if RUIN else "Tropic Isles", "coral_cove")
    c.route(L.route_points(), width=14.0, bank=5.0)
    kinds = {}
    for look, (ground, cliff, road, shoulder) in LOOK.items():
        kinds[look] = {"mat": road, "shoulder": 1.5, "shoulder_mat": shoulder}
    kinds["boardwalk"] = {"mat": "cove_planks", "surface": "road", "shoulder": 0.6, "shoulder_mat": ("cove_planks", "road"),
                          "barrier": 1.0, "barrier_mat": ("cove_rail", "wall"), "deck": 1.6, "deck_mat": ("cove_post", "wall"),
                          "ground": False}
    c.kinds = kinds

    def label(smp):
        d, wz = L.water_d(smp.p.x, smp.p.y)
        if d < L.river_hw + 4 and smp.p.z > wz + 0.9 and BL.natural(smp.p.x, smp.p.y) < smp.p.z - 1.2:
            return "boardwalk"
        return L.look_at(smp.p.x, smp.p.y)

    c.roads(kit.plan(c, pb.blend_runs(c, list(kit.runs(c, label)), LOOK), "village", max_len=160.0))

    trail = dict(width=10.0, shoulder=1.2, shoulder_mat=("isle_jungle", "grass"))
    cx, cy, cr, cz = HUB
    smp, _ = c.nearest(cx, cy - cr - 20.0)
    c.side_road("Square Road", list(reversed(pb.line(natural, (smp.p.x, smp.p.y), (cx, cy - cr + 2.0), z0=smp.p.z, c=c))),
                "cove_planks", "road", **trail)
    dx, dy = BL.DUST_END
    dust = [(0.0, y, natural(0.0, y) + 0.2) for y in range(int(cy + cr - 2), int(dy - 6), 8)]
    c.side_road("Dust Road", dust, "beach_road", "road", **trail)
    gates = {k: v for k, v in BL.GATES.items() if k != "volcano"}
    if RUIN:
        gates["lair"] = BL.LAIR
    spots = pb.spurs(c, natural, gates, lambda x, y: LOOK[L.look_at(x, y)][2], trail)
    # The pier: out over the shallows towards Volcano Isle (the gateway at its end).
    px, py = BL.GATES["volcano"]
    smp, _ = c.nearest(px, py)
    d = math.hypot(px - smp.p.x, py - smp.p.y)
    ux, uy = (px - smp.p.x) / d, (py - smp.p.y) / d
    # (From the road's edge at its height, a plain spur to the shore; the pier with its
    # rails only from there: rails laid from the road's middle stood in the road.)
    sx, sy = smp.p.x + ux * (smp.w / 2 - 1.0), smp.p.y + uy * (smp.w / 2 - 1.0)
    z0 = pb.road_z_at(c, sx, sy) or smp.p.z
    pier_z = max(WATER_Z + 2.2, z0)
    hx, hy = smp.p.x + ux * (smp.w / 2 + 12.0), smp.p.y + uy * (smp.w / 2 + 12.0)
    c.side_road("Pier Road", [(lerp(sx, hx, k / 4), lerp(sy, hy, k / 4), lerp(z0, pier_z, k / 4) + 0.02) for k in range(5)],
                "cove_planks", "road", width=10.0, shoulder=0.4, shoulder_mat=("cove_planks", "road"))
    pier = [(lerp(hx, px, k / 16), lerp(hy, py, k / 16), pier_z + 0.02) for k in range(17)]
    c.side_road("Pier", pier, "cove_planks", "road", width=10.0, shoulder=0.4, shoulder_mat=("cove_planks", "road"),
                barrier=1.0, barrier_mat=("cove_rail", "wall"), deck=1.6, deck_mat=("cove_post", "wall"), ground=False)
    sx, sy = smp.p.x, smp.p.y
    d = math.hypot(px - sx, py - sy)
    spots["volcano"] = ((px - (px - sx) / d * 4.0, py - (py - sy) / d * 4.0), math.atan2(-(px - sx) / d, (py - sy) / d))
    if RUIN:
        # Tidewyrm's Causeway: out over the sea from the beach west of the pier, south-east to
        # its far end (his reef raised). (It ran on from the pier's end, through Volcano
        # Isle's arch: Blake, Oct 27.) A spur down the beach to where it starts.
        ax, ay = CAUSEWAY_START
        bx, by = BL.CAUSEWAY_END
        smp, _ = c.nearest(ax, ay + 20.0)
        c.side_road("Causeway Beach", pb.line(natural, (smp.p.x, smp.p.y), (ax, ay), z0=smp.p.z, c=c), "beach_road",
                    "road", width=10.0, shoulder=0.6, shoulder_mat=("beach_sand", "sand"))
        az = natural(ax, ay) + 0.2
        way = [(lerp(ax, bx, k / 24), lerp(ay, by, k / 24), lerp(az, pier_z, min(1.0, k / 4)) + 0.02)
               for k in range(25)]
        box(c, "Causeway End", bx, by - 6.0, 12.0, 3.0, WATER_Z - 4.0, WATER_Z + 14.0, ("isle_rock", "wall"))
        c.side_road("Tidewyrm's Causeway", way, "beach_road", "road", width=10.0, shoulder=0.6,
                    shoulder_mat=("isle_rock", "road"), barrier=0.6, barrier_mat=("isle_rock", "wall"), deck=1.4,
                    deck_mat=("isle_rock", "wall"), ground=False)

    # (v4: drawn in, and finer, for the walls' tiers)
    X0, X1, Y0, Y1 = -310, 310, -310, 310
    ter = c.terrain("Tropic Isles", X0, X1, Y0, Y1, 2.5, natural, classify, near=8.0, fade=16.0, verge_fill=1.5)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 5.0, lambda x, y: natural(x, y) - 0.5, c.lib("beach_sand", "sand"))
    c.disc("Sea", 0.0, -200.0, 1600.0, WATER_Z, c.lib("sea_water", "water"), role="visual", n=64)

    def ground(x, y):
        z = c.ground_z(x, y, [ter])
        return natural(x, y) if z is None else z

    lx, ly, lr, lz = BL.LAGOON
    c.disc("Lagoon", lx, ly, lr + 6.0, lz - 0.05, c.lib("lagoon_shallow", "water"), role="visual", n=36, wobble=0.12, seed=3)

    thresholds(c, ground)
    village(c, ground)
    landmarks(c, ground, spots)
    if RUIN:
        ruined(c, ground)
    puzzle_kit.pen(c, "return", "Cove Yard", *RETURN, pb.to_road(c, *RETURN), 11.0, 4.5, ("tiki_wood", "wall"),
                   ground(*RETURN), height=5.0)
    puzzle_kit.pen(c, "secret", "Smugglers Cave", *SECRET, pb.to_road(c, *SECRET), 9.0, 4.5, ("isle_rock", "wall"),
                   ground(*SECRET), height=6.0)
    pb.emit_spots(c, spots)
    # The villagers' homes, in every part of the region (src/overworld/villagers.ts).
    vh.homes(c, L, ground, "beach", vh.proto_house(lambda c, k: tp.beach_hut(c, k % 4)), avoid=[(HUB[0], HUB[1], HUB[2] + 20.0)],
             wall=-15.0)
    dress(c, ground, spots)
    box(c, "Road Bend", 0.0, dy + 8.0, 40.0, 6.0, natural(0.0, dy) - 2.0, RIM_Z + 30.0, ("isle_rock", "wall"))

    c.start_line()
    gts = c.checkpoints(height=10.0)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish(extra={"race": {"laps": 1}})
    print("loop", round(c.length, 1), "gates", len(gts))


def lined(c, name, s0, s1, ri, ro, lift, mat):
    """A tube lining a tunnel, following the road (its middle `lift` over the road): a
    hollow log, a ship's hull. Collides (its inside is the tunnel's wall)."""
    bm = kit.bmesh.new()
    n = 18
    rings = []
    m = max(6, int((s1 - s0 + 16.0) / 3.0))
    for k in range(m + 1):
        q = c.at(s0 - 8.0 + (s1 - s0 + 16.0) * k / m)
        side = Vector((q.r.x, q.r.y, 0.0)).normalized()
        c0 = Vector((q.p.x, q.p.y, q.p.z + lift))
        outer = [bm.verts.new(c0 + (side * math.cos(t) + Vector((0, 0, math.sin(t)))) * ro) for t in
                 (j * math.tau / n for j in range(n))]
        inner = [bm.verts.new(c0 + (side * math.cos(t) + Vector((0, 0, math.sin(t)))) * ri) for t in
                 (j * math.tau / n for j in range(n))]
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
    kit.bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = c.mesh_object(name, bm, "Props", "both")
    c.assign(ob, c.lib(*mat))
    return ob


def thresholds(c, ground):
    """The Vine Tunnel (roots and vines hanging), the Falls (a waterfall over its mouth: you
    drive through the water), the Hull (a great wreck lying across the headland, the road
    through its hold), the Sea Arch, the Mangroves (a root tunnel)."""
    for name, kind, a, b in L.tunnels:
        s0, s1 = pb.tunnel_span(c, L, a, b)
        if kind in ("vine", "mangrove"):
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
            for s in (s0 - 2.0, s1 + 2.0):
                q = c.at(s)
                for j in range(5):
                    t = (j - 2) / 2.0
                    x, y = q.p.x + q.r.x * t * (half + 3.0), q.p.y + q.r.y * t * (half + 3.0)
                    cone(c, "%s Root %d %d" % (name, int(s), j), x, y, 1.4, q.p.z + 7.0 + 2.0 * abs(t), 6.0,
                         ("bog_root" if kind == "mangrove" else "jungle_bark", "wall"), segs=5, role="visual")
        elif kind == "falls":
            half = pb.bore(c, L, name, s0, s1, ("isle_rock", "wall"), ("isle_jungle", "grass"), height=11.0)
            q = c.at(s0 - 3.0)  # (the water park's side: the falls pour over the mouth)
            rot = math.atan2(q.t.y, q.t.x)
            # (Across the mouth: the sheet along the road's right, thrown back towards you.)
            props.falls(c, name + " Falls", q.p.x, q.p.y, q.p.z + 22.0, q.p.z - 0.5, 2 * half + 4.0, 2 * half + 8.0, facing=-1,
                        throw=2.0, foam=False, angle=math.atan2(q.r.y, q.r.x))
            g = c.game(q.p.x, q.p.y, q.p.z)
            c.entity("waterfall", x=g[0], y=g[1], z=g[2], top=round(g[1] + 22.0, 1), width=round(2 * half + 4.0, 1),
                     heading=round(rot, 3))
            for k in range(3):
                q = c.at(s0 + (s1 - s0) * (k + 0.5) / 3)
                g = c.game(q.p.x + q.r.x * (half - 0.6), q.p.y + q.r.y * (half - 0.6), q.p.z + 4.0)
                c.entity("torch", x=g[0], y=g[1], z=g[2])
        elif kind == "hull":
            half = pb.bore(c, L, name, s0, s1, ("wreck_rock", "wall"), ("wreck_grass", "grass"), half=c.width / 2 + 4.5,
                           height=16.0)
            lined(c, name, s0, s1, 11.0, 12.0, 4.6, ("wreck_hull", "wall"))
            s = s0
            k = 0
            while s < s1:
                q = c.at(s)
                rot = math.atan2(q.r.y, q.r.x)
                box(c, "%s Rib %d" % (name, k), q.p.x, q.p.y, 10.6, 0.5, q.p.z + 13.0, q.p.z + 14.0, ("wreck_planks", "wall"),
                    rot=rot, role="visual")
                if k % 2 == 0:
                    g = c.game(q.p.x + q.r.x * (c.width / 2 + 1.5), q.p.y + q.r.y * (c.width / 2 + 1.5), q.p.z + 6.0)
                    c.entity("torch", x=g[0], y=g[1], z=g[2])
                s += 7.0
                k += 1
            q = c.at(s1 + 6.0)
            c.place(tp.mast(c, h=20.0, broken=True), q.p.x + q.r.x * 14.0, q.p.y + q.r.y * 14.0,
                    ground(q.p.x + q.r.x * 14.0, q.p.y + q.r.y * 14.0) - 0.5, rot=1.2)
        else:  # the Sea Arch
            pb.bore(c, L, name, s0, s1, ("cove_rock", "wall"), ("cove_grass", "grass"), height=14.0)


def village(c, ground):
    """Raptor's village: a boardwalk square on the plateau, huts round it on stilts, tiki
    torches, a fire (after the wave: flattened)."""
    cx, cy, cr, cz = HUB
    c.disc("Village Boardwalk", cx, cy, cr, cz + 0.05, c.lib("cove_planks", "road"), coll="Props", n=40)
    for k in range(7):
        a = k * math.tau / 7 + 0.45
        if math.sin(a) < -0.6 or math.sin(a) > 0.8:
            continue  # (clear of the ways in: south to the road, north to the Dust Road)
        hx, hy = cx + (cr + 6) * math.cos(a), cy + (cr + 6) * math.sin(a)
        if not paint.road_clear(c, hx, hy, 6.0):
            continue
        if RUIN:
            box(c, "Hut %d" % k, hx, hy, 3.5, 3.5, cz - 1.0, cz + 1.4, ("tiki_wood", "wall"), rot=a)
            ruin.rubble(c, "Hut Wreck %d" % k, hx + 4 * math.cos(a), hy + 4 * math.sin(a), ground, ("thatch", "wall"), n=4,
                        spread=3.0, size=1.0, seed=k)
            continue
        c.place(tp.beach_hut(c, k % 3), hx, hy, ground(hx, hy) - 0.2, rot=a + math.pi / 2)
    g = c.game(cx, cy, cz + 0.3)
    c.entity("campfire", x=g[0], y=g[1], z=g[2])
    torch = bp.tiki_torch(c, 0)
    for k in range(12):
        a = k * math.tau / 12 + 0.26
        if abs(math.sin(a)) > 0.85:
            continue
        x, y = cx + (cr + 1.5) * math.cos(a), cy + (cr + 1.5) * math.sin(a)
        c.place(torch, x, y, ground(x, y))
        g = c.game(x, y, ground(x, y) + 2.6)
        c.entity("torch", x=g[0], y=g[1], z=g[2])


def landmarks(c, ground, spots):
    """The water park's slide tower, the wrecked galleon on Shipwreck's beach, Volcano Isle
    smoking offshore at the end of the pier, the coral heads in Coral's shallows."""
    def facing(name):
        (ex, ey), _ = spots[name]
        gx, gy = BL.GATES[name] if name in BL.GATES else BL.LAIR
        return math.atan2(gy - ey, gx - ex)

    # Splash Lagoon: the slide tower.
    x, y = BL.GATES["splash"]
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
    # Shipwreck Bay: a galleon on its side up the beach.
    x, y = BL.GATES["wreck"]
    f = facing("wreck")
    hx, hy = x + 14.0 * math.cos(f), y + 14.0 * math.sin(f)
    box(c, "Wreck Hull", hx, hy, 16.0, 4.5, WATER_Z - 1.0, ground(hx, hy) + 5.0, ("wreck_hull", "wall"), rot=f + math.pi / 2)
    c.place(tp.mast(c, h=16.0, broken=True), hx + 4.0 * math.cos(f), hy + 4.0 * math.sin(f), ground(hx, hy) + 4.0, rot=f)
    # Volcano Isle offshore, smoking.
    vx, vy = BL.VOLCANO
    volc = c.rock_mass("Volcano Isle", vx, vy, 72.0, 60.0, 96.0, z0=WATER_Z - 4.0, n=18, seed=7,
                       bands=[(1.0, 0.0), (0.7, 0.4), (0.4, 0.8), (0.25, 1.0)], base=WATER_Z)
    c.assign(volc, c.lib("isle_rock", "wall"))
    g = c.game(vx, vy, 98.0)
    c.entity("eruption", x=g[0], y=g[1], z=g[2], period=15.0, offset=2.0)
    # Coral Cove: coral heads in the shallows by its gateway.
    x, y = BL.GATES["coral"]
    f = facing("coral")
    for k in range(7):
        a = f + (k - 3) * 0.35
        px, py = x + 16.0 * math.cos(a), y + 16.0 * math.sin(a)
        c.place(tp.coral(c, k % 3), px, py, ground(px, py) - 0.3, rot=a, role="visual")
    c.place(tp.lifeguard_tower(c), x - 20.0 * math.sin(f), y + 20.0 * math.cos(f), ground(x - 20.0 * math.sin(f),
                                                                                         y + 20.0 * math.cos(f)))


def ruined(c, ground):
    """After Tidewyrm's attack: his sea cave in Coral's east headland, wreckage up the
    beaches."""
    x, y = BL.LAIR
    z = ground(x, y)
    box(c, "Lair Mouth", x + 3.0, y, 2.0, 8.0, z - 1.0, z + 12.0, ("dark_corridor", "wall"), role="visual")
    for k in range(7):
        t = (k - 3) / 3.0
        if abs(t) < 0.4:
            continue
        px, py = x + 1.0, y + t * 12.0
        cone(c, "Lair Rock %d" % k, px, py, 3.5 + abs(t) * 1.5, ground(px, py) - 1.0, 9.0 + 7.0 * (1 - abs(t)),
             ("isle_rock", "wall"), segs=6)
    spots = []
    for k in range(30):
        a = k * 2.399
        r = 50.0 + 236.0 * ((k * 0.618) % 1.0)
        px, py = r * math.cos(a), r * math.sin(a)
        if L.wall_sd(px, py) < -14 and L.look_at(px, py) in ("shipwreck", "pier", "coral") and paint.road_clear(c, px, py, 7.0):
            spots.append((px, py))
    for k, (px, py) in enumerate(spots):
        ruin.rubble(c, "Wreckage %d" % k, px, py, ground, ("wreck_planks", "wall"), n=5, spread=4.0, size=1.1, seed=30 + k)


def dress(c, ground, spots):
    """The paint pass: coconut palms on every beach and round the village, the jungle's
    trees, bushes and ferns; Coral's umbrellas, deck chairs, towels, canoes and beach huts;
    Shipwreck's pirate huts, barrels, cannon, stockade; the pier's cove's boats; the water
    park's pools, umbrellas and loungers; the Tiki Steps' torches. After the wave: palms
    snapped, the beach things gone."""
    taken = paint.Taken([(HUB[0], HUB[1], HUB[2] + 12.0), (*HUT, 18.0), (*RETURN, 18.0), (*SECRET, 16.0),
                         *((x, y, 9.0) for x, y in GONGS), *((e[0], e[1], 16.0) for e, _ in spots.values()),
                         *((x, y, 26.0) for x, y in BL.GATES.values()), (*BL.LAIR, 24.0),
                         (BL.LAGOON[0], BL.LAGOON[1], BL.LAGOON[2] + 4.0)])

    def inside(x, y):
        return L.wall_sd(x, y) < -8 and natural(x, y) > WATER_Z + 0.6

    def look(*names):
        return lambda x, y: inside(x, y) and L.look_at(x, y) in names

    rmax = 480.0
    g = ground
    snapped = lambda x, y, z, s: ruin.stump(c, "Snapped Palm %d %d" % (int(x), int(y)), x, y, z, ("palm_bark", "wall"),
                                            h=1.5 + 2.0 * s, r=0.45)
    sandy = look("shipwreck", "pier", "coral", "lagoon")
    green = look("village", "splash")
    for v in range(3):
        paint.scatter(c, bp.coconut_palm(c, v), 22, rmax, sandy, g, taken, 10 + v, room=5.0, road_margin=5.0,
                      instead=snapped if RUIN else None, trunk=(0.5, 8.0))
        paint.scatter(c, bp.coconut_palm(c, v), 10, rmax, green, g, taken, 15 + v, room=5.0, road_margin=5.0,
                      instead=snapped if RUIN else None, trunk=(0.5, 8.0))
    for v in range(2):
        paint.scatter(c, props.jungle_tree(c, v), 24, rmax, green, g, taken, 20 + v, room=5.0, scale=(1.0, 1.7), road_margin=6.0,
                      trunk=(0.8, 6.0))
        paint.scatter(c, props.bush(c, v), 40, rmax, green, g, taken, 30 + v, room=2.5, role="visual")
    paint.scatter(c, props.fern(c), 80, rmax, green, g, taken, 35, room=1.5, role="visual")
    for k, p in enumerate((bp.starfish(c, 0), bp.starfish(c, 1), bp.shell(c))):
        paint.scatter(c, p, 20, rmax, sandy, g, taken, 40 + k, room=1.0, role="visual", sink=0.05)
    # The Tiki Steps: torches up the ravine.
    torch = bp.tiki_torch(c, 0)
    for k, smp in enumerate(c.S[::12]):
        if L.pocket_at(smp.p.x, smp.p.y) != "steps":
            continue
        sd = 1 if k % 2 else -1
        x, y = smp.p.x + smp.r.x * sd * (smp.w / 2 + 3.0), smp.p.y + smp.r.y * sd * (smp.w / 2 + 3.0)
        c.place(torch, x, y, g(x, y))
        gg = c.game(x, y, g(x, y) + 2.6)
        c.entity("torch", x=gg[0], y=gg[1], z=gg[2])
    if RUIN:
        return
    co = look("coral")
    for k, (p, n) in enumerate(((bp.umbrella(c, 0), 8), (bp.umbrella(c, 1), 8), (bp.deck_chair(c, 0), 10),
                                (bp.towel(c, 0), 8), (bp.canoe(c, 0), 3))):
        paint.scatter(c, p, n, rmax, co, g, taken, 50 + k, room=3.0, role="visual", sink=0.05)
    for v in range(2):
        paint.scatter(c, tp.beach_hut(c, v), 2, rmax, co, g, taken, 56 + v, room=10.0, road_margin=7.0)
    sw = look("shipwreck")
    for v in range(2):
        paint.scatter(c, tp.pirate_hut(c, v), 2, rmax, sw, g, taken, 60 + v, room=10.0, road_margin=7.0)
    paint.scatter(c, tp.barrel(c), 8, rmax, sw, g, taken, 62, room=3.0, road_margin=4.0)
    paint.scatter(c, tp.cannon(c), 3, rmax, sw, g, taken, 63, room=5.0, road_margin=5.0)
    paint.scatter(c, tp.rowboat(c), 3, rmax, look("shipwreck", "pier"), g, taken, 64, room=6.0, road_margin=5.0)
    sp = look("splash")
    for k, (p, n) in enumerate(((bp.umbrella(c, 0), 6), (bp.deck_chair(c, 1), 8), (bp.beach_ball(c, 0), 6))):
        paint.scatter(c, p, n, rmax, sp, g, taken, 70 + k, room=3.0, role="visual", sink=0.05)


if __name__ == "__main__":
    main()
