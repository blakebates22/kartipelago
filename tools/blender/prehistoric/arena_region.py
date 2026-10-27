# The mini-games' arenas (Blake, Oct 26: two battle royales like the old kart racers', two
# of our own; they unlock nothing yet): each an open bowl walled by its landscape, with
# the things its game needs. Built on pocket_kit like the overworld (one pocket, its
# floor, walls as steep as they're high).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/arena_region.py <bowl|nest|crown|stars>
#
#   bowl   Crater Bowl (Balloon Brawl): a crater floor, a mound in the middle with ramps
#          up it, rock pillars to hide behind, item balloons round the ring
#   nest   Nest Island (Egg Scramble): a sandy island, a nest in each corner, the egg
#          stone in the middle
#   crown  Crown Hill (King of the Hill): a round valley, a flat-topped hill in the middle
#          with two ramps up, the crown's ring on top
#   stars  Star Fall (catch the falling stars): a plaza of three terraces, ramps between
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
        "r": 78.0,
        "top": 40.0,
        "mats": (("ash_soil", "dirt"), ("ember_rock", "wall"), ("basalt_road", "road")),
    },
    "nest": {
        "name": "Nest Island",
        "env": "coral_cove",
        "floor": 1.5,
        "r": 80.0,
        "top": 30.0,
        "mats": (("beach_sand", "sand"), ("cove_rock", "wall"), ("cove_planks", "road")),
    },
    "crown": {
        "name": "Crown Hill",
        "env": "dragon_isles",
        "floor": 3.0,
        "r": 82.0,
        "top": 44.0,
        "mats": (("keep_grass", "grass"), ("keep_rock", "wall"), ("keep_cobble", "road")),
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

ROUTE = [(RING * math.cos(k * math.tau / 16), RING * math.sin(k * math.tau / 16), None) for k in range(16)]
L = Layout([("floor", "floor", [(0.0, 0.0, R, F)])], TOP, ROUTE, [], roll=1.2, flat=(), mountains=30.0)


def feature(x, y):
    """The arena's own shapes over its floor: the bowl's mound, the crown's hill, the
    stars' terraces (a height to add, 0 elsewhere)."""
    d = math.hypot(x, y)
    if AID == "bowl":
        return 6.0 * smooth((22.0 - d) / 10.0)
    if AID == "crown":
        return 10.0 * smooth((30.0 - d) / 14.0)
    if AID == "stars":
        return 3.0 * smooth((46.0 - d) / 3.0) + 3.0 * smooth((24.0 - d) / 3.0)
    return 0.0


def natural(x, y):
    return L.natural(x, y) + feature(x, y)


def classify(c, n, info):
    ground, cliff, _ = SP["mats"]
    if n.z < 0.62:
        return cliff
    if AID == "nest" and math.hypot(c.x, c.y) > R - 6:
        return ("cove_wet_sand", "water")
    return ground


def main():
    c = kit.Course(TRACK_ID, SP["name"], SP["env"])
    c.route(L.route_points(), width=14.0, bank=0.0)
    ground_m, cliff_m, road_m = SP["mats"]
    c.kinds = {"floor": {"mat": road_m[0], "shoulder": 1.0, "shoulder_mat": ground_m}}
    c.roads(kit.plan(c, [(0.0, c.length, None)], "floor", max_len=160.0))
    X0, X1, Y0, Y1 = -200, 200, -200, 200
    ter = c.terrain(SP["name"], X0, X1, Y0, Y1, 2.5, natural, classify, near=4.0, fade=8.0)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 2.5, lambda x, y: natural(x, y) - 0.5, c.lib(*ground_m))

    def ground(x, y):
        z = c.ground_z(x, y, [ter])
        return natural(x, y) if z is None else z

    taken = paint.Taken([(0.0, 0.0, 30.0)])
    # Where the karts start: round the ring, facing in.
    for k in range(8):
        a = k * math.tau / 8 + 0.2
        x, y = (RING - 6.0) * math.cos(a), (RING - 6.0) * math.sin(a)
        g = c.game(x, y, ground(x, y))
        c.entity("arena_spawn", x=round(g[0], 2), z=round(g[2], 2), heading=round(math.atan2(-x, y), 3), index=k)
    # Item balloons round the ring and nearer the middle.
    n = 0
    for k in range(10):
        c.balloon(c.length * (k + 0.5) / 10, (k % 3 - 1) * 4.0, ("red", "blue", "green", "yellow", "rainbow")[k % 5])
        n += 1
    BUILD[AID](c, ground, taken)
    c.entity("arena", game={"bowl": "balloons", "nest": "eggs", "crown": "crown", "stars": "stars"}[AID],
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
    """Rock pillars round the mound, two jump ramps across the floor."""
    for k in range(6):
        a = k * math.tau / 6
        x, y = 40.0 * math.cos(a), 40.0 * math.sin(a)
        c.assign(c.rock_mass("Pillar %d" % k, x, y, 5.0, 4.0, F + 14.0, z0=F - 3.0, n=12, seed=k + 2),
                 c.lib("obsidian_cliff", "wall"))
        taken.add(x, y, 8.0)
    for k, a in enumerate((0.5, 0.5 + math.pi)):
        x, y = 56.0 * math.cos(a), 56.0 * math.sin(a)
        ramp(c, "Jump %d" % k, x, y, a + math.pi / 2, 10.0, 9.0, 2.0, ("basalt_road", "road"), ground(x, y))
    for k in range(5):
        a = k * math.tau / 5 + 0.3
        x, y = 14.0 * math.cos(a), 14.0 * math.sin(a)
        g = c.game(x, y, ground(x, y) + 0.3)
        c.entity("steam", x=g[0], y=g[1], z=g[2])
    g = c.game(0.0, 0.0, ground(0.0, 0.0) + 1.0)
    c.entity("bubbles", x=g[0], y=g[1], z=g[2], r=3.0, molten=True)
    paint.scatter(c, props.basalt_columns(c), 10, R - 10, lambda x, y: math.hypot(x, y) > RING + 6, ground, taken, 4,
                  room=6.0, road_margin=-30.0)


def build_nest(c, ground, taken):
    """A nest in each corner (four players: red, blue, green, yellow), the egg stone in the
    middle, palms round the shore."""
    colors = ("red", "blue", "green", "yellow")
    for k, col in enumerate(colors):
        a = k * math.tau / 4 + math.pi / 4
        x, y = 48.0 * math.cos(a), 48.0 * math.sin(a)
        z = ground(x, y)
        for j in range(12):
            b = j * math.tau / 12
            box(c, "Nest %s Twig %d" % (col, j), x + 6.0 * math.cos(b), y + 6.0 * math.sin(b), 1.6, 0.35, z - 0.2, z + 0.7,
                ("weathered_timber", "wall"), rot=b + math.pi / 2, role="visual")
        g = c.game(x, y, z)
        c.entity("nest", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), color=col, index=k)
        taken.add(x, y, 10.0)
    z = ground(0.0, 0.0)
    box(c, "Egg Stone", 0.0, 0.0, 3.0, 3.0, z - 0.5, z + 0.4, ("cove_rock", "wall"), rot=math.pi / 4, role="visual")
    g = c.game(0.0, 0.0, z + 0.5)
    c.entity("egg_spawn", x=g[0], z=g[2], y=g[1], r=10.0)
    for v in range(2):
        paint.scatter(c, bp.coconut_palm(c, v), 10, R - 6, lambda x, y: math.hypot(x, y) > RING + 4, ground, taken, 10 + v,
                      room=6.0, road_margin=-30.0, trunk=(0.6, 7.0))


def build_crown(c, ground, taken):
    """The hill's two ramps up (cut into its flanks), banners round its top, the crown's
    ring."""
    zt = ground(0.0, 0.0)
    for k, a in enumerate((0.0, math.pi)):
        x, y = 22.0 * math.cos(a), 22.0 * math.sin(a)
        ramp(c, "Hill Ramp %d" % k, x, y, a + math.pi, 18.0, 9.0, zt - ground(x + 9 * math.cos(a), y + 9 * math.sin(a)) - 0.2,
             ("keep_cobble", "road"), ground(x + 9 * math.cos(a), y + 9 * math.sin(a)))
    for k in range(8):
        a = k * math.tau / 8 + 0.4
        x, y = 13.0 * math.cos(a), 13.0 * math.sin(a)
        c.place(kp.banner_pole(c), x, y, ground(x, y) - 0.2)
    g = c.game(0.0, 0.0, zt)
    c.entity("crown_zone", x=g[0], z=g[2], y=g[1], r=10.0)
    for v in range(2):
        paint.scatter(c, kp.pine(c, v, 10.0 + v * 2), 12, R - 6, lambda x, y: math.hypot(x, y) > RING + 5, ground, taken,
                      20 + v, room=6.0, road_margin=-30.0, trunk=(0.6, 6.0))


def build_stars(c, ground, taken):
    """Ramps up the terraces, lanterns round them."""
    for k in range(4):
        a = k * math.tau / 4
        for rr, lo in ((46.0, 0.0), (24.0, 3.0)):
            x, y = (rr + 2.0) * math.cos(a), (rr + 2.0) * math.sin(a)
            ramp(c, "Terrace Ramp %d %d" % (k, int(rr)), x, y, a + math.pi, 10.0, 8.0, 3.0, ("moon_paving", "road"),
                 ground(x + 5.0 * math.cos(a), y + 5.0 * math.sin(a)))
    for k in range(12):
        a = k * math.tau / 12 + 0.26
        x, y = 47.5 * math.cos(a), 47.5 * math.sin(a)
        g = c.game(x, y, ground(x, y) + 3.0)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
    c.entity("star_field", radius=R - 12.0)
    c.entity("fireflies", rate=30, radius=36)


BUILD = {"bowl": build_bowl, "nest": build_nest, "crown": build_crown, "stars": build_stars}

if __name__ == "__main__":
    main()
