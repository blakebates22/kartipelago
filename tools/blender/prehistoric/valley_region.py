# Dinosaur Valley, the overworld's first region (greybox): the drivable valley the game
# opens in, with the gateways into its four courses (the Claude Doc "Kartipelago
# Overworld: Concept & Layout"; src/overworld/regions.ts places the gateways).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/valley_region.py      (the bpy module)
#
# Blake (Oct 26): one region per kingdom, gateways at matching landmarks, about 800-900 m
# across. Broad strokes, all placeholder:
#
#   - A bowl about 800 m across ringed by cliffs: the dinosaurs think the valley is the
#     whole world. (The Burnt Gorge through the north cliff comes with the story.)
#   - A ring road round the valley floor, about a minute round at full speed, and four
#     spokes in to Elder Mossback's camp in the middle.
#   - The river, from the falls in the north-east cliff down to the bog in the south-west:
#     a bridge where the north spoke crosses it, a ford where the west one does, bridges
#     where the ring does.
#   - The four landmarks the gateways stand at: Riverbend Palms by the ford (west),
#     Cascade Caverns in a cave mouth beside the falls (north-east), Bonebog Pyramid where
#     the pyramid's tip shows above the bog (south-west), Ember Peak in a lava-lit tunnel
#     at the foot of the cliff with the volcano smoking beyond it (south-east). Short
#     roads run out to the three in the cliffs.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import bmesh, lerp, smooth  # noqa: E402

TRACK_ID = "valley_region"
WATER_Z = -0.8
RING_R = 225.0
CAMP_R = 30.0
CLIFF_R = 335.0  # where the cliffs begin to rise
RIM_Z = 70.0
FLOOR_Z = 1.4  # the valley floor (the river runs a couple of metres below it)

# The river, from the falls to the bog (x, y), and its half width.
RIVER = [(262.0, 318.0), (230.0, 270.0), (165.0, 205.0), (75.0, 150.0), (-55.0, 92.0), (-148.0, 2.0), (-196.0, -110.0),
         (-222.0, -200.0)]
RIVER_HW = 10.0
BOG = (-232.0, -232.0, 46.0)

# The landmarks (the gateways stand just in front of them).
CAVE = (40.0, CLIFF_R + 8.0)  # angle (degrees), radius
TUNNEL = (-40.0, CLIFF_R + 8.0)
PYRAMID = (-240.0, -242.0)
FORD = (-148.0, 2.0)


def polar(a_deg, r):
    a = math.radians(a_deg)
    return r * math.cos(a), r * math.sin(a)


def _seg_d(px, py, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def river_d(x, y):
    return min(_seg_d(x, y, a, b) for a, b in zip(RIVER, RIVER[1:]))


def ring_r(a):
    """The ring road's radius at angle a (radians): a slow wobble, three bulges round."""
    return RING_R + 12.0 * math.sin(3 * a + 0.4)


def natural(x, y):
    """The valley floor rolling gently, the river's channel and the bog sunk into it, the
    cliffs rising all round to the rim."""
    r = math.hypot(x, y)
    h = FLOOR_Z + 0.7 * math.sin(x / 37.0) * math.cos(y / 41.0) + 0.5 * math.sin((x + y) / 53.0)
    # (The camp sits on a level plaza.)
    h = lerp(FLOOR_Z, h, smooth((r - CAMP_R) / 14.0))
    h += RIM_Z * smooth((r - CLIFF_R) / 48.0) + 8.0 * smooth((r - CLIFF_R - 50) / 60.0)
    d = river_d(x, y)
    if d < RIVER_HW + 12:
        h = lerp(h, WATER_Z - 1.4, smooth((RIVER_HW + 12 - d) / 12))
    bx, by, br = BOG
    db = math.hypot(x - bx, y - by)
    if db < br + 10:
        h = lerp(h, WATER_Z - 0.9, smooth((br + 10 - db) / 10))
    return h


def classify(c, n, info):
    if n.z < 0.62:
        return ("valley_cliff", "wall")
    bx, by, br = BOG
    if math.hypot(c.x - bx, c.y - by) < br + 2 and c.z < WATER_Z + 0.4:
        return ("bog_mud", "mud")
    if c.z < WATER_Z + 0.3:
        return ("valley_sand", "water")  # (the river's wadeable)
    return ("valley_grass", "grass")


def box(c, name, cx, cy, hx, hy, z0, z1, mat, rot=0.0, role="both", coll="Props"):
    bm = bmesh.new()
    ca, sa = math.cos(rot), math.sin(rot)
    vs = []
    for z in (z0, z1):
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            lx, ly = sx * hx, sy * hy
            vs.append(bm.verts.new((cx + lx * ca - ly * sa, cy + lx * sa + ly * ca, z)))
    for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([vs[i] for i in f])
    ob = c.mesh_object(name, bm, coll, role)
    c.assign(ob, c.lib(*mat))
    return ob


def cone(c, name, cx, cy, r, z0, h, mat, segs=4, role="both", coll="Props"):
    bm = bmesh.new()
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=0.0, depth=h)
    for v in res["verts"]:
        v.co = kit.Vector((cx + v.co.x, cy + v.co.y, z0 + h / 2 + v.co.z))
    ob = c.mesh_object(name, bm, coll, role)
    c.assign(ob, c.lib(*mat))
    return ob


def road_z(x, y):
    """The roads sit on the valley floor, rising onto their bridges over the river."""
    return FLOOR_Z + 0.2 + 2.0 * smooth((RIVER_HW + 22 - river_d(x, y)) / 22)


def line(a, b, every=8.0, z=None):
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / every))
    pts = []
    for k in range(n + 1):
        x, y = lerp(a[0], b[0], k / n), lerp(a[1], b[1], k / n)
        pts.append((x, y, z(x, y) if z else road_z(x, y)))
    return pts


def main():
    c = kit.Course(TRACK_ID, "Dinosaur Valley (greybox)", "mirror_lake")
    # The ring road, counter-clockwise from due east.
    ring = []
    for k in range(48):
        a = k * math.tau / 48
        r = ring_r(a)
        x, y = r * math.cos(a), r * math.sin(a)
        ring.append((x, y, road_z(x, y)))
    c.route(ring, width=14.0, bank=4.0)
    grass = ("valley_grass", "grass")
    wall = ("valley_cliff", "wall")
    c.kinds = {
        "road": {"mat": "valley_road", "shoulder": 1.5, "shoulder_mat": grass},
        "bridge": {"mat": "valley_road", "surface": "road", "shoulder": 0.6, "shoulder_mat": ("valley_road", "road"),
                   "barrier": 1.0, "barrier_mat": wall, "deck": 2.0, "deck_mat": wall, "ground": False},
    }

    def label(smp):
        return "bridge" if river_d(smp.p.x, smp.p.y) < RIVER_HW + 5 else "road"

    specials = [(s0, s1, k) for s0, s1, k in kit.runs(c, label) if k != "road"]
    c.roads(kit.plan(c, specials, "road", max_len=200.0))

    # The spokes in to the camp: east and south straight in; the north one over its
    # bridge; the west one through the ford (down to the water and up the far bank).
    def spoke_end(a_deg):
        a = math.radians(a_deg)
        return ring_r(a) * math.cos(a) * 0.985, ring_r(a) * math.sin(a) * 0.985

    for name, a in (("East", 0.0), ("South", -90.0)):
        c.side_road("Spoke " + name, line(polar(a, CAMP_R - 2), spoke_end(a)), "valley_trail", "road", width=10.0,
                    shoulder=1.2, shoulder_mat=grass)
    # North: up to the bridge, over it, on to the ring.
    yb0, yb1 = 98.0, 136.0  # (the river crosses x = 0 near y = 117)
    c.side_road("Spoke North", line((0.0, CAMP_R - 2), (0.0, yb0 + 2)), "valley_trail", "road", width=10.0, shoulder=1.2,
                shoulder_mat=grass)
    c.side_road("North Bridge", line((0.0, yb0), (0.0, yb1), every=4.0, z=lambda x, y: FLOOR_Z + 2.2), "valley_road", "road",
                width=10.0, shoulder=0.4, shoulder_mat=("valley_road", "road"), barrier=1.0, barrier_mat=wall, deck=1.6,
                deck_mat=wall, ground=False)
    c.side_road("Spoke North 2", line((0.0, yb1 - 2), spoke_end(90.0)), "valley_trail", "road", width=10.0, shoulder=1.2,
                shoulder_mat=grass)

    def ford_z(x, y):
        return lerp(FLOOR_Z + 0.2, WATER_Z - 0.25, smooth((RIVER_HW + 16 - river_d(x, y)) / 16))

    c.side_road("Spoke West (the ford)", line((-(CAMP_R - 2), 0.0), spoke_end(180.0), z=ford_z), "valley_trail", "road",
                width=10.0, shoulder=1.2, shoulder_mat=grass)
    # Out from the ring to the three landmarks in the cliffs.
    for name, (a, r) in (("Cave Road", CAVE), ("Tunnel Road", TUNNEL)):
        a0 = math.radians(a)
        c.side_road(name, line(spoke_end(a), polar(a, r - 10.0)), "valley_trail", "road", width=10.0, shoulder=1.2,
                    shoulder_mat=grass)
    bx, by, br = BOG
    shore = (bx + (br + 4) * math.cos(math.radians(45)), by + (br + 4) * math.sin(math.radians(45)))
    c.side_road("Bog Road", line(spoke_end(225.0), shore), "valley_trail", "road", width=10.0, shoulder=1.2,
                shoulder_mat=grass)

    X0, X1, Y0, Y1 = -470, 470, -470, 470
    ter = c.terrain("Valley", X0, X1, Y0, Y1, 5.0, natural, classify, near=8.0, fade=14.0)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 5.0, lambda x, y: natural(x, y) - 0.5, c.lib("valley_grass", "grass"))
    river = [(x, y, 2 * RIVER_HW + 6) for x, y in RIVER]
    c.ribbon("River", river, 2 * RIVER_HW + 6, WATER_Z, c.lib("valley_water", "water"), role="visual", steps=6)
    c.disc("Bog", bx, by, br + 3.0, WATER_Z, c.lib("bog_water", "mud"), role="visual", n=36, wobble=0.12, seed=3)

    # The falls: a sheet of water down the north-east cliff where the river begins.
    fx, fy = RIVER[0]
    ux, uy = fx / math.hypot(fx, fy), fy / math.hypot(fx, fy)
    box(c, "Falls", fx + ux * 6, fy + uy * 6, 9.0, 1.2, WATER_Z, RIM_Z - 4.0, ("waterfall", "wall"),
        rot=math.atan2(uy, ux) + math.pi / 2, role="visual")

    # Elder Mossback's camp: four huts round a fire on a beaten-earth plaza.
    c.disc("Camp Plaza", 0.0, 0.0, CAMP_R, FLOOR_Z + 0.05, c.lib("valley_trail", "dirt"), coll="Props",
           role="both", n=40)
    for k in range(4):
        a = k * math.tau / 4 + math.pi / 4  # (on the diagonals, clear of the four spokes)
        hx, hy = (CAMP_R - 8) * math.cos(a), (CAMP_R - 8) * math.sin(a)
        box(c, "Hut %d" % k, hx, hy, 3.2, 3.2, FLOOR_Z - 1.0, FLOOR_Z + 4.0, ("weathered_timber", "wall"), rot=a)
        cone(c, "Hut Roof %d" % k, hx, hy, 5.2, FLOOR_Z + 4.0, 3.4, ("thatch", "wall"), segs=6, role="visual")
    c.entity("campfire", **dict(zip(("x", "y", "z"), c.game(0.0, 0.0, natural(0, 0) + 0.2))))

    # The landmarks the gateways stand at.
    # Cascade Caverns: a dark cave mouth in the cliff beside the falls.
    for name, (a, r), mat in (("Cave Mouth", CAVE, ("dark_corridor", "wall")), ("Tunnel Mouth", TUNNEL, ("dark_corridor", "wall"))):
        x, y = polar(a, r)
        rot = math.radians(a) + math.pi / 2
        z0 = natural(*polar(a, r - 10))
        box(c, name, x, y, 9.0, 2.0, z0 - 1.0, z0 + 11.0, mat, rot=rot, role="visual")
        for side in (-1, 1):
            px, py = x + side * 8.0 * math.cos(rot), y + side * 8.0 * math.sin(rot)
            box(c, name + " Jamb %d" % side, px, py, 1.6, 2.6, z0 - 1.0, z0 + 12.0, ("valley_cliff", "wall"), rot=rot)
        box(c, name + " Lintel", x, y, 10.0, 2.8, z0 + 11.0, z0 + 14.0, ("valley_cliff", "wall"), rot=rot)
    # Ember Peak: the tunnel glows with lava inside, the volcano smoking beyond the rim.
    x, y = polar(TUNNEL[0], TUNNEL[1] + 1.5)
    box(c, "Tunnel Lava", x, y, 7.0, 0.6, natural(*polar(TUNNEL[0], TUNNEL[1] - 10)) - 0.5,
        natural(*polar(TUNNEL[0], TUNNEL[1] - 10)) + 3.0, ("volcano_lava", "wall"), rot=math.radians(TUNNEL[0]) + math.pi / 2,
        role="visual")
    vx, vy = polar(TUNNEL[0], 520.0)
    volc = c.rock_mass("Volcano", vx, vy, 120.0, 110.0, 190.0, z0=60.0, n=18, seed=5,
                       bands=[(1.0, 0.0), (0.7, 0.5), (0.4, 0.85), (0.25, 1.0)], base=60.0)
    c.assign(volc, c.lib("valley_cliff", "wall"))
    gx, gy, gz = c.game(vx, vy, 192.0)
    c.entity("eruption", x=gx, y=gy, z=gz, period=14.0, offset=3.0)
    # Bonebog Pyramid: its tip above the bog.
    px, py = PYRAMID
    cone(c, "Pyramid Tip", px, py, 14.0, WATER_Z - 2.0, 18.0, ("sandstone_block", "wall"))
    # Riverbend Palms: a few palms at the ford.
    for k, (dx, dy) in enumerate(((14, 18), (-16, 22), (18, -20), (-12, -24))):
        fx, fy = FORD
        g = natural(fx + dx, fy + dy)
        box(c, "Ford Palm %d" % k, fx + dx, fy + dy, 0.5, 0.5, g - 1.0, g + 9.0, ("weathered_timber", "wall"))
        cone(c, "Ford Palm Crown %d" % k, fx + dx, fy + dy, 4.0, g + 8.0, 2.0, ("valley_grass", "wall"), segs=5, role="visual")

    gates = c.checkpoints(height=10.0)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish()
    print("ring", round(c.length, 1), "gates", len(gates))


if __name__ == "__main__":
    main()
