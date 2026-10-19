# Riverbend Palms: Prehistoric World, course 1. "Sunny tribal adventure."
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/riverbend_palms.py      (the bpy module)
#   blender --background --python tools/blender/prehistoric/riverbend_palms.py
#
# A green river valley ringed by warm sandstone walls. The road runs north up the east
# bank, crosses the river on an arched wooden bridge, snakes through S-bends and climbs
# a ridge on the west side with a view over the valley, sweeps back down to a stone ford
# and winds through a palm grove and a riverside village to the final straight.
#
# Saves tracks-src/riverbend_palms.blend and exports public/tracks/riverbend_palms/.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import props  # noqa: E402
from course_kit import bmesh, lerp, smooth  # noqa: E402

TRACK_ID = "riverbend_palms"
WATER_Z = -1.0
FORD_Y = -130.0

# The race line: (x, y, z) in Blender coordinates (y north, z up), counter-clockwise.
ROUTE = [
    (120, -40, 0.5),  # start / finish, heading north up the east bank
    (118, 22, 0.6),
    (104, 80, 0.8),
    (74, 116, 1.2),
    (34, 129, 2.4),
    (0, 133, 3.4),  # the wooden bridge
    (-34, 132, 2.4),
    (-74, 140, 1.6),  # S-bends along the bank
    (-112, 128, 2.6),
    (-134, 98, 4.6),
    (-148, 60, 7.0),  # up onto the ridge
    (-150, 18, 8.6),
    (-158, -24, 7.6),
    (-142, -70, 4.4),  # the long sweeping descent
    (-104, -102, 1.8),
    (-54, -122, 0.3),
    (0, FORD_Y, -0.45),  # the stone ford
    (50, -130, 0.3),
    (92, -140, 0.7),  # through the village, sweeping round to the final straight
    (122, -120, 0.6),
    (128, -84, 0.5),
]


def river_x(y):
    return 10 * math.sin(y / 48) + 5 * math.sin(y / 19 + 1.3)


def natural(x, y):
    """The valley: gentle meadows, a ridge in the west, sandstone walls all round, and
    the river's channel (shallow by the ford)."""
    h = 0.6 + 0.8 * math.sin(x / 31) * math.cos(y / 27) + 0.5 * math.sin((x + y) / 43)
    h += 9.5 * smooth((-x - 95) / 60)  # the west ridge
    h += 2.5 * smooth((x - 150) / 40)  # low hills in the east
    d = abs(x - river_x(y))
    # The valley walls, with a notch in the north for the waterfall and a gorge in the
    # south where the river leaves.
    r = math.hypot(x * 0.95, y)
    wall = 34 * smooth((r - 210) / 28) * (0.85 + 0.15 * math.sin(math.atan2(y, x) * 7))
    if y > 0:
        wall = min(wall, 17 + 40 * smooth((d - 16) / 18))
    else:
        wall *= smooth((d - 22) / 26)
    h += wall
    bed = -1.45 if abs(y - FORD_Y) < 36 else -2.7
    if d < 30:
        h = lerp(h, bed, smooth((30 - d) / 14))
    return h


def classify(c, n, info):
    if n.z < 0.62:
        return ("valley_cliff", "wall")
    if c.z < WATER_Z + 0.4 and abs(c.x - river_x(c.y)) < 34:
        return ("valley_sand", "sand")
    if c.z > 14:
        return ("valley_cliff", "sand")  # the tops of the walls
    return ("valley_grass", "grass")


VILLAGE = [(78, -104), (96, -170), (140, -150), (58, -168), (150, -108)]
TOTEMS = [(76, -112), (136, -96), (74, -158)]


def scenery(c):
    ter = list(c.coll("Terrain").objects)
    for piece in c.pieces:
        if "bridge" in piece.name:
            props.piers(c, piece, every=10, mat=("palm_bark", "wall"), size=0.55, terrain=ter)
    palms = [props.palm(c, 8.5 + v, 1.2 + 0.5 * v, v) for v in range(3)]
    trees = [props.jungle_tree(c, v) for v in range(2)]
    fern = props.fern(c)
    flowers = props.flowers(c)
    rocks = [props.boulder(c, "valley_cliff", v) for v in range(3)]
    hut, totem = props.hut(c), props.totem(c)

    def dry(x, y, z):
        return z > WATER_Z + 0.3

    def beside(m0, m1):
        def ok(x, y, z):
            smp, d = c.nearest(x, y)
            return dry(x, y, z) and smp.w / 2 + m0 < d < smp.w / 2 + m1 and z < 12
        return ok

    # Palms lining the road and the river banks; trees and rocks further out.
    for v, p in enumerate(palms):
        props.scatter(c, p, 34, (-200, 200, -200, 200), beside(4, 22), ter, seed=10 + v)
        props.scatter(c, p, 10, (-60, 60, -200, 200),
                      lambda x, y, z: dry(x, y, z) and 26 < abs(x - river_x(y)) < 40 and kit.Vector((x, y)).length < 200 and props.clear_of_road(c, x, y, 5), ter, seed=20 + v)
    for v, t in enumerate(trees):
        props.scatter(c, t, 16, (-210, 210, -210, 210), beside(16, 70), ter, seed=30 + v)
    props.scatter(c, fern, 70, (-200, 200, -200, 200), beside(3, 40), ter, seed=40, role="visual")
    props.scatter(c, flowers, 60, (-200, 200, -200, 200), beside(2.5, 30), ter, seed=41, role="visual", sink=0.1)
    for v, r in enumerate(rocks):
        props.scatter(c, r, 9, (-220, 220, -220, 220), beside(8, 60), ter, seed=50 + v, scale=(1.2, 3.2))
    # The village: huts and totems inside the last bend.
    for i, (x, y) in enumerate(VILLAGE):
        z = c.ground_z(x, y, ter)
        if z is not None and props.clear_of_road(c, x, y, 6):
            c.place(hut, x, y, z - 0.1, rot=i * 1.3, scale=1.0 + 0.15 * (i % 2), coll="Village")
    for i, (x, y) in enumerate(TOTEMS):
        z = c.ground_z(x, y, ter)
        if z is not None and props.clear_of_road(c, x, y, 3):
            c.place(totem, x, y, z - 0.2, rot=i * 2.1 + 0.5, coll="Village")
    # Sandstone stacks: landmarks you can see across the valley.
    for i, (x, y, h) in enumerate(((-60, 40, 22), (60, 10, 16), (-100, -10, 26), (40, -60, 14), (-190, 120, 30))):
        if props.clear_of_road(c, x, y, 12):
            rock = c.rock_mass("Sandstone Stack %d" % (i + 1), x, y, 7 + i % 3, 6, h, z0=-3, n=10, seed=i * 3)
            c.paint_rock(rock, ("valley_cliff", "wall"), ("valley_grass", "grass"))
    # The waterfall the river comes from, pouring through the notch in the north wall.
    fx = river_x(226)
    fall = c.ribbon("Waterfall", [(fx + o, 226, 2.0, 0) for o in range(-14, 15, 4)], 2.0, 0, c.lib("waterfall"), role="visual")
    for v in fall.data.vertices:
        side = v.co.y - 226
        v.co.y = 226 + side * 0.1 + (1.5 if side < 0 else 0)
        v.co.z = 17.5 if side > 0 else WATER_Z
    fall.data.update()
    c.disc("Falls Foam", fx, 222, 13, WATER_Z + 0.05, c.lib("foam"), role="visual", n=20, wobble=0.15)
    # A smoking volcano far beyond the walls: a hint of Ember Peak.
    bm = bmesh.new()
    rings = [props.ring(bm, (-360, 380), r, z, 16) for r, z in ((170, -5), (120, 50), (55, 105), (40, 112))]
    props.loft(bm, rings)
    vol = c.mesh_object("Far Volcano", bm, "Backdrop", "visual")
    c.assign(vol, c.lib("volcano_basalt"))
    vol.data.shade_flat()


def main():
    c = kit.Course(TRACK_ID, "Riverbend Palms", "river_valley")
    c.route(ROUTE, width=14.0, bank=7.0)
    c.kinds = {
        "road": {"mat": "valley_road", "shoulder": 1.5, "shoulder_mat": ("valley_grass", "dirt")},
        "bridge": {
            "mat": "wood_planks",
            "surface": "road",
            "shoulder": 0.4,
            "shoulder_mat": ("wood_planks", "road"),
            "barrier": 1.0,
            "barrier_mat": ("palm_bark", "wall"),
            "deck": 1.4,
            "deck_mat": ("wood_planks", "wall"),
            "ground": False,
        },
        "ford": {
            "mat": "swamp_stone",
            "surface": "road",
            "shoulder": 1.0,
            "shoulder_mat": ("valley_sand", "sand"),
            "deck": 1.6,
            "deck_mat": ("swamp_stone", "wall"),
            "ground": False,
        },
    }
    river = kit.crossings(c, lambda s: abs(s.p.x - river_x(s.p.y)) < 30, margin=3)
    specials = []
    for s0, s1 in river:
        mid = c.at((s0 + s1) / 2)
        specials.append((s0, s1, "ford" if mid.p.y < 0 else "bridge"))
    c.roads(kit.plan(c, specials, "road"))
    # A dirt shortcut through the village, cutting the last bend.
    c.shortcut("Village Shortcut", [(58, -131, 0.3), (84, -125, 0.5), (106, -115, 0.6), (125, -101, 0.5)],
               "valley_road", "dirt", width=8.0, shoulder_mat=("valley_grass", "dirt"))

    c.terrain("Valley", -250, 250, -250, 250, 3.3, natural, classify)
    # The river: shallow (slow, but you can splash across) by the ford, deep (you're
    # fished out) everywhere else.
    ford = [(river_x(y), y) for y in range(int(FORD_Y) - 36, int(FORD_Y) + 37, 6)]
    north = [(river_x(y), y) for y in range(int(FORD_Y) + 36, 263, 6)]
    south = [(river_x(y), y) for y in range(-262, int(FORD_Y) - 35, 6)]
    c.ribbon("River Ford", ford, 56, WATER_Z, c.lib("valley_water"), steps=4)
    c.ribbon("River", north, 56, WATER_Z, c.lib("valley_water", "deep_water"), steps=4)
    c.ribbon("River South", south, 56, WATER_Z, c.lib("valley_water", "deep_water"), steps=4)
    c.start_line()
    scenery(c)

    L = c.length
    # Gameplay: zippers on the final straight and off the bridge, bananas on the
    # straights, balloons where there's room to pick a line.
    c.zipper(L - 85, 0)
    c.zipper(river[0][1] + 25, -3)
    c.zipper(kit.s_near(c, -146, 16), 3)
    for at, across in ((40, -3), (150, 3), (kit.s_near(c, -122, 86), 0), (kit.s_near(c, -98, -104), -2), (L - 160, 2)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (95, -4, "red"),
        (95, 4, "blue"),
        (kit.s_near(c, -152, 56), 0, "green"),
        (kit.s_near(c, -52, -124), -3, "yellow"),
        (kit.s_near(c, 72, -150), 3, "rainbow"),
    ):
        c.balloon(at, across, col)

    # The long-neck's stroll: round the west meadow, across the road near the ford
    # (it waits for karts to pass), and back up beside the river.
    dino = [(-75 + 42 * math.cos(a), -28 + 88 * math.sin(a)) for a in [k * math.tau / 16 for k in range(16)]]
    c.path_curve("Dino Path", dino)
    c.entity("dinosaur", route="Dino Path", speed=3.0, scale=1.0, start=40)
    fx = river_x(226)
    gx, gy, gz = c.game(fx, 224, WATER_Z)
    c.entity("waterfall", x=gx, y=gy, z=gz, top=17.5, width=28, heading=0)

    # Checkpoints: after the bridge, over the ridge, after the ford, and one at the
    # village bend with a twin gate across the shortcut (either counts).
    short = [(58, -131, 0.3), (84, -125, 0.5), (106, -115, 0.6), (125, -101, 0.5)]
    s_in, s_out = kit.s_near(c, 58, -131), kit.s_near(c, 125, -101)
    apex = (s_in + s_out) / 2
    gates = c.checkpoints(
        extra=[river[0][1] + 12, kit.s_near(c, -150, 18), river[1][1] + 12, apex],
        avoid=[(s_in, apex - 12), (apex + 12, s_out)],
    )
    main = min(gates.items(), key=lambda kv: abs(kv[0] - apex))[1]
    c.alt_gate(main, "village_shortcut", short, width=26)

    c.preset("sun", [o for o in c.coll("Terrain").objects], 0.35)
    c.preset("road_edge", [o for o in c.coll("Terrain").objects], 0.4, color=(1.0, 0.86, 0.55), distance=7.0)
    c.finish()


main()
