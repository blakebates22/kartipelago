# The mini-games' arenas (Blake, Oct 26: two battle royales like the old kart racers', two
# of our own; Oct 27: rework Balloon Brawl's and Star Fall's arenas ("I can hardly drive
# around", "I can't climb the centre mound"), new games Smugglers' Run and Crumble Rink):
# each an open bowl walled by its landscape, with the things its game needs. Built on
# pocket_kit like the overworld (one pocket, its floor, walls as steep as they're high).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/arena_region.py <bowl|docks|rink|stars>
#
#   bowl   Crater Bowl (Balloon Brawl): a wide, open crater floor to drift round, banked
#          rims, a low island in the middle (gentle slopes all round), a few broken
#          walls and boulders for cover, two jumps on the outer loop
#   docks  Smugglers' Cove (Smugglers' Run): a sandy cove, a crew's dock at each corner,
#          crate stacks to dodge round, where the crates fall in the middle
#   rink   Crumble Rink: a round sheet of ice over a crevasse (the tiles are the game's:
#          src/screens/minigames.ts draws them; the build is the crevasse round it and an
#          invisible floor under the ice)
#   stars  Star Fall (catch the falling stars): a plaza of three terraces with gentle
#          slopes between (no step a kart can't climb), a shallow ring road round it
#
# The route is a ring round the floor with no road (the kit's courses have a route: the
# balloons go round it, and a kart that falls off is put back on it).

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp, smooth  # noqa: E402
from pocket_kit import Layout  # noqa: E402
from pocket_build import box  # noqa: E402
import region_paint as paint  # noqa: E402
import props  # noqa: E402
import beach_props as bp  # noqa: E402
import canyon_props as cp  # noqa: E402
import keep_props as kp  # noqa: E402

AID = sys.argv[-1]
TRACK_ID = "arena_%s" % AID

SPECS = {
    "bowl": {
        "name": "Crater Bowl",
        "env": "ember_volcano",
        "floor": 2.0,
        "r": 86.0,
        "top": 40.0,
        "mats": (("ash_soil", "dirt"), ("ember_rock", "wall"), ("basalt_road", "road")),
    },
    "docks": {
        "name": "Smugglers' Cove",
        "env": "coral_cove",
        "floor": 1.5,
        "r": 80.0,
        "top": 30.0,
        "mats": (("beach_sand", "sand"), ("cove_rock", "wall"), ("cove_planks", "road")),
    },
    "rink": {
        "name": "Crumble Rink",
        "env": "aurora_rift",
        # (The crevasse's floor, far under the ice.)
        "floor": -34.0,
        "r": 66.0,
        "top": 40.0,
        "mats": (("cavern_ice", "wall"), ("icefall_rift", "wall"), ("lake_ice", "ice")),
    },
    "stars": {
        "name": "Star Fall",
        "env": "moonstone_kingdom",
        "floor": 2.0,
        "r": 80.0,
        "top": 40.0,
        "mats": (("moon_grass", "grass"), ("moon_rock", "wall"), ("moon_paving", "road")),
    },
}
SP = SPECS[AID]
F, R, TOP = SP["floor"], SP["r"], SP["top"]
RING = R - 22.0  # (the route's ring)
# Crumble Rink's ice: its height and radius (the tiles are the game's).
ICE_Z, ICE_R, TILE = 2.0, 40.0, 2.6
if AID == "rink":
    RING = 24.0

ROUTE = [(RING * math.cos(k * math.tau / 16), RING * math.sin(k * math.tau / 16), ICE_Z if AID == "rink" else None)
         for k in range(16)]
L = Layout([("floor", "floor", [(0.0, 0.0, R, F)])], TOP, ROUTE, [], roll=1.2, flat=(), mountains=30.0)


def feature(x, y):
    """The arena's own shapes over its floor: the bowl's mound, the crown's hill, the
    stars' terraces (a height to add, 0 elsewhere)."""
    d = math.hypot(x, y)
    if AID == "bowl":
        # A low island (2.4 m over 12 m: about 11 degrees at its steepest), and the rim
        # banked up gently so you can drift round it.
        return 2.4 * smooth((26.0 - d) / 12.0) + 5.0 * smooth((d - (R - 28.0)) / 24.0)
    if AID == "stars":
        # Three terraces with long slopes between (3 m over 12 m and over 10 m), and a
        # shallow ring road round the outside.
        return (3.0 * smooth((50.0 - d) / 12.0) + 3.0 * smooth((26.0 - d) / 10.0)
                - 1.0 * smooth(1.0 - abs(d - 64.0) / 6.0) + 3.0 * smooth((d - (R - 10.0)) / 10.0))
    return 0.0


def natural(x, y):
    return L.natural(x, y) + feature(x, y)


def classify(c, n, info):
    ground, cliff, _ = SP["mats"]
    if n.z < 0.62:
        return cliff
    if AID == "docks" and math.hypot(c.x, c.y) > R - 6:
        return ("cove_wet_sand", "water")
    return ground


def main():
    c = kit.Course(TRACK_ID, SP["name"], SP["env"])
    c.route(L.route_points(), width=14.0, bank=0.0)
    ground_m, cliff_m, road_m = SP["mats"]
    c.kinds = {"floor": {"mat": road_m[0], "shoulder": 1.0, "shoulder_mat": ground_m}}
    if AID != "rink":
        c.roads(kit.plan(c, [(0.0, c.length, None)], "floor", max_len=160.0))
    X0, X1, Y0, Y1 = -200, 200, -200, 200
    ter = c.terrain(SP["name"], X0, X1, Y0, Y1, 2.5, natural, classify, near=4.0, fade=8.0)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 2.5, lambda x, y: natural(x, y) - 0.5, c.lib(*ground_m))

    def ground(x, y):
        if AID == "rink" and math.hypot(x, y) < ICE_R:
            return ICE_Z
        z = c.ground_z(x, y, [ter])
        return natural(x, y) if z is None else z

    taken = paint.Taken([(0.0, 0.0, 30.0)])
    # Where the karts start: round the ring, facing in.
    for k in range(8):
        a = k * math.tau / 8 + 0.2
        sr = 18.0 if AID == "rink" else RING - 6.0
        x, y = sr * math.cos(a), sr * math.sin(a)
        g = c.game(x, y, ground(x, y))
        c.entity("arena_spawn", x=round(g[0], 2), z=round(g[2], 2), heading=round(math.atan2(-x, y), 3), index=k)
    # Item balloons round the ring and nearer the middle.
    n = 0
    for k in range(10):
        c.balloon(c.length * (k + 0.5) / 10, (k % 3 - 1) * 4.0, ("red", "blue", "green", "yellow", "rainbow")[k % 5])
        n += 1
    BUILD[AID](c, ground, taken)
    c.entity("arena", game={"bowl": "balloons", "docks": "smugglers", "rink": "crumble", "stars": "stars"}[AID],
             radius=round(R - 8.0, 1))
    kit.paint.shade_roads(c.pieces, 0.3)
    c.checkpoints(height=12.0)
    c.finish(extra={"race": {"laps": 1}, "arena": True})


def ramp(c, name, x, y, rot, length, width, rise, mat, z0):
    """A wedge ramp: up `rise` over `length` along local +x."""
    bm = kit.bmesh.new()
    ca, sa = math.cos(rot), math.sin(rot)

    def at(lx, ly, z):
        return bm.verts.new((x + lx * ca - ly * sa, y + lx * sa + ly * ca, z))

    a = [at(-length / 2, -width / 2, z0 - 0.5), at(length / 2, -width / 2, z0 - 0.5), at(length / 2, width / 2, z0 - 0.5),
         at(-length / 2, width / 2, z0 - 0.5)]
    b = [at(-length / 2, -width / 2, z0 - 0.02), at(length / 2, -width / 2, z0 + rise), at(length / 2, width / 2, z0 + rise),
         at(-length / 2, width / 2, z0 - 0.02)]
    for f in ((0, 3, 2, 1),):
        bm.faces.new([a[i] for i in f])
    bm.faces.new([b[0], b[1], b[2], b[3]])
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh = kit.bmesh
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = c.mesh_object(name, bm, "Props", "both")
    c.assign(ob, c.lib(*mat))
    return ob


def build_bowl(c, ground, taken):
    """Cover round the island (a few low boulders and broken walls, spaced so there's a
    line of sight between any two and room to drive round each), two jump ramps on the
    outer loop."""
    for k in range(5):
        a = k * math.tau / 5 + 0.35
        x, y = 42.0 * math.cos(a), 42.0 * math.sin(a)
        if k % 2 == 0:
            # A broken wall, side-on to the middle.
            for j in range(3):
                t = (j - 1) * 3.4
                h = (3.6, 2.6, 1.8)[j]
                box(c, "Broken Wall %d %d" % (k, j), x - math.sin(a) * t, y + math.cos(a) * t, 1.6, 3.2, F - 0.5,
                    ground(x, y) + h, ("obsidian_cliff", "wall"), rot=a)
        else:
            c.assign(c.rock_mass("Boulder %d" % k, x, y, 3.2, 2.6, ground(x, y) + 3.4, z0=F - 2.0, n=10, seed=k + 2),
                     c.lib("obsidian_cliff", "wall"))
        taken.add(x, y, 9.0)
    for k, a in enumerate((0.9, 0.9 + math.pi)):
        x, y = (RING - 2.0) * math.cos(a), (RING - 2.0) * math.sin(a)
        ramp(c, "Jump %d" % k, x, y, a + math.pi / 2, 11.0, 9.0, 1.8, ("basalt_road", "road"), ground(x, y))
    for k in range(5):
        a = k * math.tau / 5 + 0.3
        x, y = 14.0 * math.cos(a), 14.0 * math.sin(a)
        g = c.game(x, y, ground(x, y) + 0.3)
        c.entity("steam", x=g[0], y=g[1], z=g[2])
    g = c.game(0.0, 0.0, ground(0.0, 0.0) + 1.0)
    c.entity("bubbles", x=g[0], y=g[1], z=g[2], r=3.0, molten=True)
    paint.scatter(c, props.basalt_columns(c), 10, R - 10, lambda x, y: math.hypot(x, y) > RING + 6, ground, taken, 4,
                  room=6.0, road_margin=-30.0)


def build_docks(c, ground, taken):
    """A crew's dock in each corner (four players: red, blue, green, yellow): a plank
    landing flush with the sand, mooring posts, a flag in the crew's colour and crates
    stacked behind; crate stacks round the middle to dodge round; where the crates fall."""
    colors = ("red", "blue", "green", "yellow")
    flags = {"red": "party_red", "blue": "party_blue", "green": "party_teal", "yellow": "party_yellow"}
    for k, col in enumerate(colors):
        a = k * math.tau / 4 + math.pi / 4
        x, y = 50.0 * math.cos(a), 50.0 * math.sin(a)
        z = ground(x, y)
        box(c, "Dock %s Deck" % col, x, y, 12.0, 10.0, z - 0.3, z + 0.06, ("cove_planks", "road"), rot=a, role="visual")
        for j in range(6):
            b = a + (j - 2.5) * 0.36
            px, py = x + 8.0 * math.cos(b), y + 8.0 * math.sin(b)
            box(c, "Dock %s Post %d" % (col, j), px, py, 0.5, 0.5, z - 0.5, z + 1.6, ("cove_post", "wall"))
        fx, fy = x + 9.5 * math.cos(a), y + 9.5 * math.sin(a)
        box(c, "Dock %s Flagpole" % col, fx, fy, 0.3, 0.3, z, z + 7.0, ("cove_post", "wall"))
        box(c, "Dock %s Flag" % col, fx - 1.3 * math.sin(a), fy + 1.3 * math.cos(a), 0.12, 2.4, z + 5.0, z + 6.6,
            (flags[col], "wall"), rot=a, role="visual")
        for j in (-1, 1):
            sx, sy = x + 11.0 * math.cos(a) + j * 6.0 * math.sin(a), y + 11.0 * math.sin(a) - j * 6.0 * math.cos(a)
            box(c, "Dock %s Crates %d" % (col, j), sx, sy, 2.2, 2.2, z - 0.2, z + 2.0, ("weathered_timber", "wall"), rot=a + 0.3 * j)
        g = c.game(x, y, z)
        c.entity("dock", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), color=col, index=k)
        taken.add(x, y, 14.0)
    # Stacks round the middle (cover, and something to cut round).
    for k in range(4):
        a = k * math.tau / 4
        x, y = 26.0 * math.cos(a), 26.0 * math.sin(a)
        z = ground(x, y)
        box(c, "Stack %d" % k, x, y, 3.0, 3.0, z - 0.3, z + 2.4, ("weathered_timber", "wall"), rot=a + 0.4)
        box(c, "Stack %d Top" % k, x + 0.4, y - 0.3, 2.0, 2.0, z + 2.4, z + 4.2, ("weathered_timber", "wall"), rot=a - 0.2)
        taken.add(x, y, 6.0)
    g = c.game(0.0, 0.0, ground(0.0, 0.0))
    c.entity("crate_spawn", x=g[0], z=g[2], y=g[1], r=34.0)
    for v in range(2):
        paint.scatter(c, bp.coconut_palm(c, v), 10, R - 6, lambda x, y: math.hypot(x, y) > RING + 4, ground, taken, 10 + v,
                      room=6.0, road_margin=-30.0, trunk=(0.6, 7.0))


def build_rink(c, ground, taken):
    """The ice's invisible floor (the karts drive on it; what they see is the game's
    tiles), a rim of ice boulders round the crevasse's lip, icicles down its walls."""
    c.disc("Ice Floor", 0.0, 0.0, ICE_R + 0.5, ICE_Z, c.lib("lake_ice", "ice"), coll="Props", role="collision", n=64)
    for k in range(14):
        a = k * math.tau / 14 + 0.1
        rr = R - 4.0
        x, y = rr * math.cos(a), rr * math.sin(a)
        c.assign(c.rock_mass("Lip Boulder %d" % k, x, y, 4.0, 3.0, ground(x, y) + 5.0 + (k % 3) * 2.0, z0=ground(x, y) - 3.0,
                             n=10, seed=k + 5), c.lib("glacier_ice", "wall"))
    g = c.game(0.0, 0.0, ICE_Z)
    c.entity("rink", x=g[0], z=g[2], y=g[1], r=ICE_R, tile=TILE)
    c.entity("fireflies", rate=20, radius=40)


def build_stars(c, ground, taken):
    """Lanterns round the terraces (their slopes are gentle all round: no ramps needed)."""
    for k in range(12):
        a = k * math.tau / 12 + 0.26
        x, y = 56.0 * math.cos(a), 56.0 * math.sin(a)
        g = c.game(x, y, ground(x, y) + 3.0)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
    c.entity("star_field", radius=R - 12.0)
    c.entity("fireflies", rate=30, radius=36)


BUILD = {"bowl": build_bowl, "docks": build_docks, "rink": build_rink, "stars": build_stars}

if __name__ == "__main__":
    main()
