# Cascade Caverns: Prehistoric World, course 2. "Rushing jungle canyon."
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/cascade_caverns.py      (the bpy module)
#
# A deep jungle canyon with a river along its floor. The road starts on the canyon
# floor, climbs a viaduct at the east end, runs west along a ledge cut into the north
# wall, crosses the whole canyon on a high bridge (right over the start straight),
# dives into a tunnel through the south wall, then leaps the river gorge through a
# waterfall pouring off an overhang, and winds back down to the canyon floor.
#
# Saves tracks-src/cascade_caverns.blend and exports public/tracks/cascade_caverns/.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import props  # noqa: E402
from course_kit import bmesh, lerp, smooth  # noqa: E402

TRACK_ID = "cascade_caverns"
WATER_Z = -1.6
JUMP_X = -190.0
LIP_Y = -6.0  # the ramp's lip
LAND_Y = 5.0  # where the landing road starts
FALL_Y = -1.0  # the waterfall curtain, across the jump
TUNNEL = ((-117.0, -101.0), 70.0, 36.0)  # rock centre, radii

ROUTE = [
    (-20, -40, 0.0),  # start / finish: the canyon floor, heading east
    (40, -40, 0.0),
    (92, -34, 0.8),
    (134, -12, 2.6),
    (152, 26, 5.2),  # up the viaduct at the east end
    (140, 66, 8.6),
    (104, 86, 11.6),
    (56, 94, 13.6),  # the ledge along the north wall
    (12, 92, 14.8),
    (-22, 70, 15.4),
    (-36, 32, 15.8),  # the high bridge, over the river and the start straight
    (-40, -14, 15.8),
    (-44, -56, 15.4),
    (-64, -88, 15.0),  # into the tunnel through the south wall
    (-104, -110, 14.6),
    (-148, -110, 14.2),
    (-178, -94, 13.9),
    (-192, -62, 13.8),
    (JUMP_X, -30, 14.0),  # the ramp...
    (JUMP_X, LIP_Y, 14.6),
    (JUMP_X + 1, LAND_Y + 9, 10.6),  # ...over the gorge, through the falls
    (-178, 46, 8.6),
    (-154, 72, 6.4, 16.0),
    (-126, 60, 4.2),
    (-112, 34, 2.4),  # over the river on a low stone bridge
    (-100, -6, 1.0),
    (-78, -32, 0.3),
]


def river_y(x):
    return 2.0 + 3.0 * math.sin(x / 50.0) + 2.0 * math.sin(x / 23.0 + 0.7)


def wall_n(x):
    return 70 + 7 * math.sin(x / 37) + 3 * math.sin(x / 11)


def wall_s(x):
    return -70 + 7 * math.sin(x / 29 + 1) + 3 * math.sin(x / 13)


def natural(x, y):
    """The canyon: a floor with the river, steep stepped walls, closed at both ends."""
    h = 0.3 * math.sin(x / 17) * math.cos(y / 13)
    rise = 0.0
    for edge, sign in ((wall_n(x), 1), (wall_s(x), -1)):
        d = (y - edge) * sign
        for step, up in ((0, 11), (7, 10), (15, 9), (24, 8)):
            rise += up * smooth((d - step) / 3.5)
    for edge, sign in ((176, 1), (-212, -1)):
        d = (x - edge) * sign
        for step, up in ((0, 12), (8, 12), (18, 14)):
            rise += up * smooth((d - step) / 4)
    h += rise
    d = abs(y - river_y(x))
    if d < 15:
        bed = -4.0 if x > -170 else -6.0
        h = lerp(h, bed, smooth((15 - d) / 6))
    return h


def in_tunnel_rock(x, y, shrink=1.0):
    (cx, cy), rx, ry = TUNNEL
    return ((x - cx) / (rx * shrink)) ** 2 + ((y - cy) / (ry * shrink)) ** 2 < 1


def classify(c, n, info):
    if in_tunnel_rock(c.x, c.y, 0.94):
        return None  # the tunnel rock covers it
    if n.z < 0.62:
        return ("fossil_strata", "wall")
    if c.z < WATER_Z + 0.4 and abs(c.y - river_y(c.x)) < 18:
        return ("fossil_scree", "sand")
    if c.z > 20:
        return ("jungle_leafcover", "grass")
    if info["d"] < 12:
        return ("jungle_path", "dirt")
    return ("jungle_leafcover", "grass")


def wall_fall(c, name, x, y_wall, top, side):
    """A waterfall down a canyon wall: a sheet leaning out from the wall to the river."""
    out = -side  # towards the canyon floor
    pts = [(x + o, y_wall) for o in range(-6, 7, 3)]
    fall = c.ribbon(name, [(px, py, 2.0, 0) for px, py in pts], 2.0, 0, c.lib("waterfall"), role="visual")
    for v in fall.data.vertices:
        s = v.co.y - y_wall
        v.co.y = y_wall + (0 if s > 0 else out * 10)
        v.co.z = top if s > 0 else WATER_Z
    fall.data.update()
    c.disc(name + " Foam", x, y_wall + out * 11, 8, WATER_Z + 0.05, c.lib("foam"), role="visual", n=16, wobble=0.2)


def scenery(c, rock):
    ter = list(c.coll("Terrain").objects)
    for piece in c.pieces:
        if "viaduct" in piece.name:
            props.piers(c, piece, every=14, mat=("jungle_temple", "wall"), size=1.3, terrain=ter, inset=2.0)
        if "ramp" in piece.name:
            props.piers(c, piece, every=8, mat=("palm_bark", "wall"), size=0.5, terrain=ter)
    trees = [props.jungle_tree(c, v) for v in range(3)]
    palms = [props.palm(c, 8 + v * 1.5, 1.0 + v * 0.6, v) for v in range(2)]
    fern = props.fern(c)
    rocks = [props.boulder(c, "jungle_mossstone", v) for v in range(3)]

    def floor_ok(m0, m1):
        def ok(x, y, z):
            smp, d = c.nearest(x, y)
            return z > WATER_Z + 0.5 and smp.w / 2 + m0 < d < smp.w / 2 + m1 and not in_tunnel_rock(x, y, 1.05)
        return ok

    for v, t in enumerate(trees):
        props.scatter(c, t, 14, (-210, 175, -64, 64), floor_ok(6, 40), ter, seed=60 + v)
        props.scatter(c, t, 16, (-235, 205, -150, 150), lambda x, y, z: z > 24 and props.clear_of_road(c, x, y, 10), ter, seed=70 + v, scale=(1.0, 1.6))
    for v, p in enumerate(palms):
        props.scatter(c, p, 14, (-210, 175, -64, 64), floor_ok(4, 30), ter, seed=80 + v)
    props.scatter(c, fern, 80, (-215, 180, -100, 110), floor_ok(2.5, 30), ter, seed=90, role="visual")
    for v, r in enumerate(rocks):
        props.scatter(c, r, 8, (-200, 170, -40, 40), lambda x, y, z: abs(y - river_y(x)) < 12 and props.clear_of_road(c, x, y, 6), ter, seed=95 + v, scale=(1.0, 2.6), sink=0.6)
    # Waterfalls pouring down both canyon walls into the river.
    for i, x in enumerate((-120, 30, 110)):
        wall_fall(c, "Wall Falls %d" % (i + 1), x, wall_n(x) + 10, 30, 1)
    for i, x in enumerate((-60, 80)):
        wall_fall(c, "South Falls %d" % (i + 1), x, wall_s(x) - 10, 30, -1)
    c.disc("Jump Falls Foam", JUMP_X, FALL_Y, 12, WATER_Z + 0.05, c.lib("foam"), role="visual", n=18, wobble=0.2)


def main():
    c = kit.Course(TRACK_ID, "Cascade Caverns", "jungle_falls")
    c.route(ROUTE, width=14.0, bank=7.0)
    stone = ("jungle_mossstone", "wall")
    c.kinds = {
        "path": {"mat": "jungle_path", "shoulder": 1.5, "shoulder_mat": ("jungle_leafcover", "dirt"), "barrier": 0.0},
        "ledge": {
            "mat": "jungle_path",
            "shoulder": 1.0,
            "shoulder_mat": ("jungle_mossstone", "dirt"),
            "barrier": 1.1,
            "barrier_mat": stone,
        },
        "viaduct": {
            "mat": "jungle_temple",
            "surface": "road",
            "shoulder": 0.6,
            "shoulder_mat": ("jungle_mossstone", "road"),
            "barrier": 1.1,
            "barrier_mat": stone,
            "deck": 2.2,
            "deck_mat": ("jungle_temple", "wall"),
            "ground": False,
        },
        "cave": {"mat": "jungle_path", "shoulder": 1.0, "shoulder_mat": ("fossil_scree", "dirt")},
        "ramp": {
            "mat": "wood_planks",
            "surface": "road",
            "shoulder": 0.5,
            "shoulder_mat": ("wood_planks", "road"),
            "barrier": 1.0,
            "barrier_mat": ("palm_bark", "wall"),
            "deck": 2.0,
            "deck_mat": ("palm_bark", "wall"),
            "ground": False,
        },
    }
    s_lip = kit.s_near(c, JUMP_X, LIP_Y)
    s_land = kit.s_near(c, JUMP_X, LAND_Y)

    def label(smp):
        x, y = smp.p.x, smp.p.y
        if s_lip <= smp.s <= s_land:
            return "gap"
        if s_lip - 34 <= smp.s < s_lip:
            return "ramp"
        if in_tunnel_rock(x, y, 0.98):
            return "cave"
        if smp.p.z - natural(x, y) > 4.0:
            return "viaduct"
        if y > wall_n(x) - 6 or y < wall_s(x) + 6:
            return "ledge"
        return "path"

    stretches = kit.runs(c, label)
    specials = []
    for s0, s1, k in stretches:
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "ramp":
            # A kicker: the last 10 m of the ramp curve up by 1.5 m, steepest at the lip.
            specials.append((s0, s1, "ramp", {"lift": lambda u, n: 1.5 * max(0.0, (u - (n - 10)) / 10) ** 2}))
        elif k != "path":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "path"))

    c.terrain("Canyon", -240, 210, -150, 150, 3.0, natural, classify, near=8.5, fade=16.0)
    path = [(x, river_y(x)) for x in range(-236, 211, 6)]
    c.ribbon("River", path, 30, WATER_Z, c.lib("valley_water", "deep_water"), steps=3)

    # The tunnel rock, cut through along the route.
    (cx, cy), rx, ry = TUNNEL
    rock = c.rock_mass("Tunnel Rock", cx, cy, rx, ry, 34.0, z0=-2.0, n=28, seed=3,
                       bands=[(1.0, 0.0), (1.0, 0.3), (0.95, 0.34), (0.93, 0.62), (0.86, 0.66), (0.82, 1.0)])
    inside = kit.crossings(c, lambda s: in_tunnel_rock(s.p.x, s.p.y, 1.0), margin=0)
    s0, s1 = max(inside, key=lambda r: r[1] - r[0])
    c.tunnel(rock, s0, s1, height=9.0, pad=14.0)
    c.paint_rock(rock, ("fossil_strata", "wall"), ("jungle_leafcover", "grass"), floor=("fossil_scree", "dirt"), top_z=30, floor_z=17)

    # The overhang the waterfall pours from, and the curtain itself (you drive through
    # it: it's only seen, never hit).
    lip = c.at(s_lip)
    top = 27.0
    bm = bmesh.new()
    pts = [(-224, FALL_Y - 9), (JUMP_X + 14, FALL_Y - 7), (JUMP_X + 14, FALL_Y + 5), (-224, FALL_Y + 8)]
    lo = [bm.verts.new((x, y, top)) for x, y in pts]
    hi = [bm.verts.new((x, y, top + 4)) for x, y in pts]
    bm.faces.new(list(reversed(lo)))
    bm.faces.new(hi)
    for i in range(4):
        bm.faces.new((lo[i], lo[(i + 1) % 4], hi[(i + 1) % 4], hi[i]))
    over = c.mesh_object("Overhang", bm, "Rocks", "visual")
    c.assign(over, c.lib("fossil_strata", "wall"))
    over.data.shade_flat()
    curtain = [(x, FALL_Y) for x in range(-210, int(JUMP_X) + 14, 3)]
    fall = c.ribbon("Waterfall", [(x, y, 2.0, 0) for x, y in curtain], 2.0, 0, c.lib("waterfall"), role="visual")
    # Stand the strip up: a vertical sheet from the overhang to the gorge.
    for v in fall.data.vertices:
        side = v.co.y - FALL_Y  # -1 or +1
        v.co.y = FALL_Y + side * 0.15
        v.co.z = top if side > 0 else WATER_Z
    fall.data.update()

    c.start_line()
    scenery(c, rock)
    L = c.length
    c.zipper(s_lip - 24, 0)  # onto the ramp: plenty of speed for the leap
    c.zipper(kit.s_near(c, 12, 92), -2)
    c.zipper(L - 70, 3)
    for at, across in ((50, 0), (kit.s_near(c, 104, 86), 2), (kit.s_near(c, -40, -14), 0), (s0 + 30, -2), (kit.s_near(c, -128, 54), 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (110, -3, "red"),
        (110, 3, "blue"),
        (kit.s_near(c, 56, 94), 0, "green"),
        (s1 + 6, 0, "yellow"),
        (kit.s_near(c, -160, 66), 0, "rainbow"),
    ):
        c.balloon(at, across, col)

    # Missing the leap drops you in the gorge: you're fished out past it, not before it.
    c.entity("respawn", **{"from": round(s_lip - 40, 1), "to": round(s_land + 6, 1), "at": round(s_land + 14, 1)})
    gx, gy, gz = c.game(JUMP_X, FALL_Y, WATER_Z)
    c.entity("waterfall", x=gx, y=gy, z=gz, top=27, width=34, heading=0)
    for x in (-120, 30, 110):
        gx, gy, gz = c.game(x, wall_n(x) - 1, WATER_Z)
        c.entity("waterfall", x=gx, y=gy, z=gz, top=30, width=12, heading=0)

    # Checkpoints: up the viaduct, along the ledge, off the high bridge, out of the
    # tunnel, and just past the landing of the leap (beyond where a missed jump puts you).
    c.checkpoints(extra=[kit.s_near(c, 104, 86), kit.s_near(c, -44, -56) + 10, s1 + 10, s_land + 24])

    ter = list(c.coll("Terrain").objects)
    c.preset("sun", ter + [rock], 0.35)
    c.preset("bottoms", ter, 0.45)
    c.preset("cover", [rock], 0.6)
    kit.paint.shade_roads(c.pieces, 0.55)
    c.finish()


main()
