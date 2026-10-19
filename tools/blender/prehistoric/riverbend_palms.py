# Riverbend Palms: Prehistoric World, course 1. "Sunny tribal adventure."
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/riverbend_palms.py      (the bpy module)
#   blender --background --python tools/blender/prehistoric/riverbend_palms.py
#
# A green river valley ringed by warm sandstone walls. The road runs north up the east
# bank, swings left onto an arched wooden bridge over the river, then dances through a
# chain of S-bends, climbs the west ridge, drops through a hairpin, crosses the stone
# ford and swings through the riverside village onto the final straight.
#
# Version 2 is laid out for drifting: every corner is a true arc (30-40 m, the drift's
# own radii), long enough to hold a drift and earn its boost, and the S-bends chain one
# drift into the next. Version 1 is in git: tag riverbend-v1.
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
# The waterfall: its lip (y, z) in the notch of the north wall.
FALLS_Y, FALLS_TOP = 228.5, 17.5


def river_x(y):
    return 10 * math.sin(y / 48) + 5 * math.sin(y / 19 + 1.3)


# The layout, as straights and arcs ("L"/"R", radius m, degrees), counter-clockwise from
# the start line on the east bank. Two straights are stretched to close the loop.
START = (150.0, -45.0)
LAYOUT = [
    ("S", 110),  # 0 the start straight, north up the east bank
    ("L", 34, 110),  # 1 a long left drift onto the river road
    ("R", 40, 20),  # 2
    ("S", 110),  # 3 the wooden bridge
    ("L", 30, 60),  # 4 the S-bend chain: left...
    ("R", 30, 100),  # 5 ...right...
    ("L", 30, 130),  # 6 ...and a long left up onto the ridge
    ("S", 90),  # 7 the ridge (stretched to close)
    ("R", 30, 60),  # 8 a flick right...
    ("L", 30, 180),  # 9 ...into the hairpin
    ("R", 40, 30),  # 10
    ("S", 40),  # 11 down to the ford
    ("L", 70, 25),  # 12 the ford, in a gentle kink
    ("R", 70, 25),  # 13
    ("S", 70),  # 14 (stretched to close)
    ("R", 32, 60),  # 15 the village: a flick right...
    ("L", 30, 150),  # 16 ...and a long left drift onto the final straight
    ("S", 60),  # 17
]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 7, 14, START, 90.0)


def road_z(x, y):
    """Road height: up the west ridge, arched over the river at the bridge, down to the
    water at the ford."""
    z = 0.5 + 8.2 * smooth((-x - 95) / 60) + 0.25 * math.sin(x / 37) * math.cos(y / 41)
    d = abs(x - river_x(y))
    if y > 0:
        z += 3.0 * smooth((34 - d) / 28)
    else:
        z -= 0.95 * smooth((30 - d) / 22)
    return z


ROUTE = kit.route_points(PATH, road_z, every=14.0)
# Where the road fords the river (the bed is shallow there).
FORD_Y = min((p for p in PATH if p[1] < 0), key=lambda p: abs(p[0] - river_x(p[1])))[1]


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
    # Above the falls the river runs on a ledge at the top of the notch.
    bed = lerp(bed, FALLS_TOP - 0.7, smooth((y - FALLS_Y + 4.5) / 3.5))
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


# The long-neck's stroll (see main), and a test for keeping trees off it.
DINO = [(-75 + 42 * math.cos(a), -28 + 88 * math.sin(a)) for a in [k * math.tau / 16 for k in range(16)]]


def off_dino_path(x, y, margin=8.0):
    return all(math.hypot(x - (-75 + 42 * math.cos(a)), y - (-28 + 88 * math.sin(a))) > margin for a in [k * math.tau / 96 for k in range(96)])


VILLAGE = [(112, -72), (88, -82), (132, -108), (110, -160), (140, -162), (78, -150)]
TOTEMS = [(92, -90), (128, -80), (124, -150)]
# The dirt shortcut through the village: off the end of the ford road, rejoining the
# final straight.
SHORTCUT = [(72, -104), (96, -99), (120, -90), (147, -70)]


def strip(c, name, rows, mat, coll="Water", role="visual"):
    """A mesh from rows of (position, u, v) with its own UVs (kept on export), for the
    waterfall's curved sheets and the rainbow."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    grid = [[(bm.verts.new(p), u, v) for p, u, v in row] for row in rows]
    for r0, r1 in zip(grid, grid[1:]):
        for k in range(len(r0) - 1):
            quad = (r0[k], r0[k + 1], r1[k + 1], r1[k])
            f = bm.faces.new([q[0] for q in quad])
            for loop, q in zip(f.loops, quad):
                loop[uv].uv = (q[1], q[2])
    ob = c.mesh_object(name, bm, coll, role)
    ob.data.materials.append(mat)
    kit.materials.ensure_paint(ob.data)
    return ob


def waterfall(c, ter):
    """The falls the river pours from: a curved sheet leaving the lip and dropping in an
    arc, fast white veils over it, rocks either side, a churning foam pool and a rainbow
    in the spray (the spray itself is the waterfall entity's particles)."""
    fx = river_x(FALLS_Y)
    V = kit.Vector
    width_top, width_bottom, drop = 26.0, 31.0, FALLS_TOP - WATER_Z

    def sheet_rows(front, cols, wscale, tile, t_rows=12, wob=0.0, seed=0.0):
        rows = []
        along = [0.0] * (cols + 1)
        prev = None
        for j in range(t_rows + 1):
            t = j / t_rows
            w = (width_top + (width_bottom - width_top) * t) * wscale
            y = FALLS_Y - 0.3 - 6.5 * math.sqrt(t) - front
            z = FALLS_TOP + 0.05 - drop * t - 0.15
            row = []
            for k in range(cols + 1):
                u = k / cols - 0.5
                # Bulges out in the middle, with a gentle ripple down the face.
                yy = y - 1.4 * (1 - (2 * u) ** 2) - wob * math.sin(t * 9 + k * 1.7 + seed)
                p = V((fx + u * w, yy, z))
                if prev is not None:
                    along[k] += (p - prev[k]).length
                row.append(p)
            rows.append([(p, (k / cols - 0.5) * w / tile, -along[k] / tile) for k, p in enumerate(row)])
            prev = row
        return rows

    strip(c, "Waterfall", sheet_rows(0.0, 10, 1.0, 6.0), c.lib("falls_sheet"))
    for i, (wscale, off) in enumerate(((0.36, -0.28), (0.22, 0.2), (0.3, 0.05))):
        rows = sheet_rows(0.35 + 0.12 * i, 4, wscale, 4.0, wob=0.25, seed=i * 2.0)
        rows = [[(p + V((off * width_top, 0, 0)), u, v) for p, u, v in row] for row in rows]
        strip(c, "Waterfall Veil %d" % (i + 1), rows, c.lib("falls_veil"))
    # The river above, running to the lip.
    # Listed downstream (north to the lip), so the water flows towards the edge.
    upper = [(river_x(y) * 0.3 + fx * 0.7, y, 24.0, FALLS_TOP) for y in range(int(FALLS_Y) + 28, int(FALLS_Y) + 1, -4)]
    upper.append((fx, FALLS_Y - 0.3, 26.0, FALLS_TOP))
    c.ribbon("River Above The Falls", upper, 24.0, FALLS_TOP, c.lib("valley_water"), role="visual", steps=2)
    # Rocks framing the falls, a lip of boulders and more in the pool.
    for i, (dx, rx, h) in enumerate(((-1, 6.5, 24), (1, 7.0, 22))):
        rock = c.rock_mass("Falls Rock %d" % (i + 1), fx + dx * (width_top / 2 + 5.5), FALLS_Y - 2.5, rx, 6, h, z0=-3, n=12, seed=7 + i * 5)
        c.paint_rock(rock, ("valley_cliff", "wall"), ("valley_grass", "grass"))
    stones = [props.boulder(c, "valley_cliff", v) for v in range(3)]
    for i, (dx, dy, z, sc) in enumerate((
        (-0.47, -1.2, FALLS_TOP - 0.4, 1.6), (0.46, -1.0, FALLS_TOP - 0.5, 1.8), (-0.18, 0.6, FALLS_TOP - 0.6, 1.0),
        (0.25, 0.8, FALLS_TOP - 0.6, 1.1), (-0.55, -12.0, WATER_Z - 0.6, 2.6), (0.6, -11.0, WATER_Z - 0.6, 3.0),
        (-0.3, -16.5, WATER_Z - 0.5, 1.4), (0.34, -18.0, WATER_Z - 0.5, 1.2),
    )):
        c.place(stones[i % 3], fx + dx * width_top, FALLS_Y + dy, z, rot=i * 1.9, scale=sc, coll="Water", role="visual")
    # Foam where it lands, and rings of it spreading out.
    foot = FALLS_Y - 8.5
    c.disc("Falls Foam", fx, foot, 17, WATER_Z + 0.05, c.lib("falls_foam"), role="visual", n=24, wobble=0.18)
    c.disc("Falls Foam Spread", fx, foot - 9, 23, WATER_Z + 0.03, c.lib("foam"), role="visual", n=24, wobble=0.25, seed=3)
    # A rainbow in the spray, facing down the valley.
    ry, rz, r_out, r_in = foot - 4.0, WATER_Z - 2.0, 15.0, 12.6
    rows = []
    for j, (r, v) in enumerate(((r_in, 0.02), (r_out, 0.98))):
        rows.append([(V((fx + r * math.cos(a), ry, rz + r * math.sin(a))), k / 16, v) for k, a in ((k, math.pi * (0.12 + 0.76 * k / 16)) for k in range(17))])
    strip(c, "Falls Rainbow", rows, c.lib("rainbow"))


def water_flowers(c, ter):
    """Lily pads and pink lotus flowers floating in clusters along the river's edges."""
    pads = [props.lily_pad(c, v) for v in range(3)]
    flower = props.lotus(c)
    n = 0
    for k in range(70):
        y = -240 + 440 * kit.rnd(k * 3.3 + 1)
        if y > FALLS_Y - 30 or abs(y - FORD_Y) < 30:
            continue
        side = -1 if kit.rnd(k * 1.9 + 4) < 0.5 else 1
        cx = river_x(y) + side * (15 + 9 * kit.rnd(k * 2.7 + 2))
        for m in range(3 + int(kit.rnd(k * 5.1) * 4)):
            a, r = kit.rnd(k * 7 + m * 1.3) * math.tau, 3.2 * kit.rnd(k * 11 + m * 2.9)
            x, yy = cx + r * math.cos(a), y + r * math.sin(a)
            ground = c.ground_z(x, yy, ter)
            if ground is None or ground > WATER_Z - 0.25 or not props.clear_of_road(c, x, yy, 4):
                continue
            bloom = m == 0 and k % 2 == 0 or m == 3
            proto = flower if bloom else pads[(k + m) % 3]
            scale = (1.3 if bloom else 0.8) + 0.7 * kit.rnd(k + m * 17)
            c.place(proto, x, yy, WATER_Z, rot=kit.rnd(k * 13 + m) * math.tau, scale=scale, coll="Water", role="visual")
            n += 1
    return n


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
            return dry(x, y, z) and smp.w / 2 + m0 < d < smp.w / 2 + m1 and z < 12 and off_dino_path(x, y)
        return ok

    # Palms lining the road and the river banks; trees and rocks further out.
    for v, p in enumerate(palms):
        props.scatter(c, p, 34, (-200, 200, -200, 200), beside(4, 22), ter, seed=10 + v)
        props.scatter(c, p, 10, (-60, 60, -200, 200),
                      lambda x, y, z: dry(x, y, z) and off_dino_path(x, y) and 26 < abs(x - river_x(y)) < 40 and kit.Vector((x, y)).length < 200 and props.clear_of_road(c, x, y, 5), ter, seed=20 + v)
    for v, t in enumerate(trees):
        props.scatter(c, t, 16, (-210, 210, -210, 210), beside(16, 70), ter, seed=30 + v)
    props.scatter(c, fern, 70, (-200, 200, -200, 200), beside(3, 40), ter, seed=40, role="visual")
    props.scatter(c, flowers, 95, (-200, 200, -200, 200), beside(2.5, 30), ter, seed=41, role="visual", sink=0.1)
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
    waterfall(c, ter)
    water_flowers(c, ter)
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
    c.shortcut("Village Shortcut", [(x, y, road_z(x, y) - 0.05) for x, y in SHORTCUT],
               "valley_road", "dirt", width=8.0, shoulder_mat=("valley_grass", "dirt"))

    c.terrain("Valley", -250, 250, -250, 250, 3.3, natural, classify)
    # The river: shallow (slow, but you can splash across) by the ford, deep (you're
    # fished out) everywhere else.
    ford = [(river_x(y), y) for y in range(int(FORD_Y) - 36, int(FORD_Y) + 37, 6)]
    north = [(river_x(y), y) for y in range(int(FORD_Y) + 36, int(FALLS_Y) - 6, 6)]
    north.append((river_x(FALLS_Y - 4.0), FALLS_Y - 4.0))
    south = [(river_x(y), y) for y in range(-262, int(FORD_Y) - 35, 6)]
    c.ribbon("River Ford", ford, 56, WATER_Z, c.lib("valley_water"), steps=4)
    c.ribbon("River", north, 56, WATER_Z, c.lib("valley_water", "deep_water"), steps=4)
    c.ribbon("River South", south, 56, WATER_Z, c.lib("valley_water", "deep_water"), steps=4)
    c.start_line()
    scenery(c)

    L = c.length
    # Gameplay: zippers on the final straight and off the bridge, bananas on the
    # straights, balloons where there's room to pick a line.
    c.zipper(L - 40, 0)  # out of the last drift, onto the final straight
    c.zipper(kit.s_near(c, -150, 10), 2)  # along the ridge
    c.zipper(river[1][1] + 30, -3)  # off the ford
    for at, across in (
        (40, -3),
        (river[0][0] - 25, 3),
        (kit.s_near(c, -150, 40), 0),
        (river[1][1] + 60, 2),
        (L - 22, 3),
    ):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (95, -4, "red"),
        (95, 4, "blue"),
        ((river[0][1] + kit.s_near(c, -150, 40)) / 2, 0, "green"),
        (kit.s_near(c, -150, -20), 0, "yellow"),
        (river[1][0] - 15, 3, "rainbow"),
    ):
        c.balloon(at, across, col)

    # The long-neck's stroll: round the west meadow, across the road near the ford
    # (it waits for karts to pass), and back up beside the river.
    c.path_curve("Dino Path", DINO)
    c.entity("dinosaur", route="Dino Path", speed=3.0, scale=1.0, start=40)
    gx, gy, gz = c.game(river_x(FALLS_Y), FALLS_Y - 7.5, WATER_Z)
    c.entity("waterfall", x=gx, y=gy, z=gz, top=FALLS_TOP, width=30, heading=0)

    # Checkpoints: after the bridge, over the ridge, after the ford, and one at the
    # village bend with a twin gate across the shortcut (either counts).
    short = [(x, y, road_z(x, y)) for x, y in SHORTCUT]
    s_in, s_out = kit.s_near(c, *SHORTCUT[0]), kit.s_near(c, *SHORTCUT[-1])
    apex = (s_in + s_out) / 2
    gates = c.checkpoints(
        extra=[river[0][1] + 12, kit.s_near(c, -150, 0), river[1][1] + 12, apex],
        avoid=[(s_in, apex - 12), (apex + 12, s_out)],
    )
    main = min(gates.items(), key=lambda kv: abs(kv[0] - apex))[1]
    c.alt_gate(main, "village_shortcut", short, width=26)

    c.preset("sun", [o for o in c.coll("Terrain").objects], 0.35)
    c.preset("road_edge", [o for o in c.coll("Terrain").objects], 0.4, color=(1.0, 0.86, 0.55), distance=7.0)
    c.finish()


main()
