# The Snow Kingdom, the overworld's second region (greybox): the drivable mountain basin
# past the Burnt Gorge, with the gateways into its four courses (the Claude Doc
# "Kartipelago Overworld: Concept & Layout"; src/overworld/regions.ts places them).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/snow_region.py      (the bpy module)
#
# Broad strokes, all placeholder, built like Dinosaur Valley (valley_region.py):
#
#   - A basin about 800 m across ringed by snowy peaks, a frozen lake in the middle with a
#     ring road round it (the lake is ice: drive on it if you like).
#   - From the south, the Burnt Gorge comes in from the valley, past Hearthglow's village
#     (the town square: Brachio's) and on up to the ring.
#   - The landmarks the gateways stand at: Hearthglow Hollow by the village's great tree
#     (south), Frostveil Citadel at its gate in the west cliff, Snowy Summit Pass at the foot
#     of the giant tree (north), Aurora Rift at the crack in the glacier (east), each at the
#     end of a road from the ring.
#   - Beside the rift, the Frozen Pass east to the desert: walled with Rimefang's ice until
#     he falls (the story's way on).

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp, smooth  # noqa: E402
from valley_region import box, cone, polar  # noqa: E402

TRACK_ID = "snow_region"
FLOOR_Z = 2.0
RING_R = 215.0
LAKE_R = 125.0
CLIFF_R = 335.0
RIM_Z = 95.0

VILLAGE = (0.0, -285.0, 30.0)  # the town square: x, y, radius
GORGE_HW = 16.0
GORGE_Y0 = -470.0  # the gorge's far (valley) end: the passage back
CITADEL = (180.0, CLIFF_R + 6.0)  # angle, radius
TREE = (90.0, CLIFF_R - 40.0)
RIFT = (0.0, CLIFF_R + 6.0)
FROZEN_PASS = (28.0, CLIFF_R + 6.0)


def ring_r(a):
    return RING_R + 10.0 * math.sin(3 * a + 1.1)


def gorge_x(y):
    return 8.0 * math.sin(max(0.0, -y - 300.0) / 40.0)


def natural(x, y):
    """The basin floor, gently rolling; the frozen lake's hollow; the peaks all round; the
    Burnt Gorge's cut in the south."""
    r = math.hypot(x, y)
    h = FLOOR_Z + 0.8 * math.sin(x / 41.0) * math.cos(y / 37.0) + 0.6 * math.sin((x - y) / 59.0)
    vx, vy, vr = VILLAGE
    h = lerp(FLOOR_Z, h, smooth((math.hypot(x - vx, y - vy) - vr) / 14.0))
    h = lerp(FLOOR_Z - 0.6, h, smooth((r - LAKE_R) / 10.0))
    peaks = 1.0 + 0.25 * math.sin(5 * math.atan2(y, x)) + 0.15 * math.sin(11 * math.atan2(y, x) + 1.0)
    h += RIM_Z * peaks * smooth((r - CLIFF_R) / 55.0) + 10.0 * smooth((r - CLIFF_R - 60) / 50.0)
    g = smooth((GORGE_HW + 12 - abs(x - gorge_x(y))) / 12) * smooth((-y - 250.0) / 40.0)
    if g > 0:
        h = lerp(h, FLOOR_Z + 0.03 * max(0.0, -y - 330.0), g)
    return h


def classify(c, n, info):
    if n.z < 0.62:
        if c.y < -260 and abs(c.x - gorge_x(c.y)) < GORGE_HW + 30:
            return ("obsidian_cliff", "wall")  # (the gorge's scorched walls)
        return ("frost_cliff", "wall")
    if math.hypot(c.x, c.y) < LAKE_R + 1 and c.z < FLOOR_Z - 0.2:
        return ("lake_ice", "ice")
    return ("snow_ground", "deep_snow")


def road_z(x, y):
    return FLOOR_Z + 0.2


def line(a, b, every=8.0, z=road_z):
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / every))
    return [(lerp(a[0], b[0], k / n), lerp(a[1], b[1], k / n), z(lerp(a[0], b[0], k / n), lerp(a[1], b[1], k / n)))
            for k in range(n + 1)]


def main():
    c = kit.Course(TRACK_ID, "Snow Kingdom (greybox)", "summit_pass")
    ring = []
    for k in range(48):
        a = k * math.tau / 48
        r = ring_r(a)
        x, y = r * math.cos(a), r * math.sin(a)
        ring.append((x, y, road_z(x, y)))
    c.route(ring, width=14.0, bank=4.0)
    snow = ("snow_ground", "deep_snow")
    c.kinds = {"road": {"mat": "packed_snow_road", "shoulder": 1.5, "shoulder_mat": snow}}
    c.roads(kit.plan(c, [], "road", max_len=200.0))

    def ring_end(a_deg):
        a = math.radians(a_deg)
        return ring_r(a) * math.cos(a) * 0.985, ring_r(a) * math.sin(a) * 0.985

    trail = dict(width=10.0, shoulder=1.2, shoulder_mat=snow)
    # The Burnt Gorge, up past the village to the ring.
    vx, vy, vr = VILLAGE
    gorge = [(gorge_x(y), y, FLOOR_Z + 0.2 + 0.03 * max(0.0, -y - 330.0)) for y in range(int(GORGE_Y0) + 25, int(vy - vr), 8)]
    c.side_road("Burnt Gorge Road", gorge, "packed_snow_road", "road", **trail)
    c.side_road("Village Road", line((vx, vy + vr - 2), ring_end(-90.0)), "packed_snow_road", "road", **trail)
    # Out from the ring to the landmarks.
    for name, (a, r) in (("Citadel Road", CITADEL), ("Tree Road", TREE), ("Rift Road", RIFT), ("Pass Road", FROZEN_PASS)):
        c.side_road(name, line(ring_end(a), polar(a, r - 12.0)), "packed_snow_road", "road", **trail)

    X0, X1, Y0, Y1 = -470, 470, -480, 470
    ter = c.terrain("Basin", X0, X1, Y0, Y1, 5.0, natural, classify, near=8.0, fade=14.0)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 5.0, lambda x, y: natural(x, y) - 0.5, c.lib("snow_ground", "deep_snow"))
    c.disc("Frozen Lake", 0.0, 0.0, LAKE_R + 2.0, FLOOR_Z - 0.55, c.lib("lake_ice", "ice"), role="visual", n=48, wobble=0.05)

    # The village: the town square, its houses and its great tree.
    c.disc("Village Square", vx, vy, vr, FLOOR_Z + 0.05, c.lib("hearth_cobble", "road"), coll="Props", n=40)
    for k in range(6):
        a = k * math.tau / 6 + math.pi / 6
        if abs(math.cos(a)) < 0.3:
            continue  # (clear of the road through the square)
        hx, hy = vx + (vr + 6) * math.cos(a), vy + (vr + 6) * math.sin(a)
        box(c, "House %d" % k, hx, hy, 4.5, 3.5, FLOOR_Z - 1.0, FLOOR_Z + 5.0, ("hearth_stone", "wall"), rot=a)
        cone(c, "House Roof %d" % k, hx, hy, 6.0, FLOOR_Z + 5.0, 4.0, ("pine_snow", "wall"), segs=4, role="visual")
    tx, ty = vx + 18.0, vy - 6.0
    box(c, "Great Tree Trunk", tx, ty, 1.6, 1.6, FLOOR_Z - 1.0, FLOOR_Z + 8.0, ("weathered_timber", "wall"))
    for k, (r, z) in enumerate(((7.0, 6.0), (5.5, 10.0), (3.8, 13.5))):
        cone(c, "Great Tree %d" % k, tx, ty, r, FLOOR_Z + z, 5.0, ("pine_snow", "wall"), segs=8, role="visual")
    gx, gy, gz = c.game(vx, vy, FLOOR_Z + 0.3)
    c.entity("campfire", x=gx, y=gy, z=gz)

    # Frostveil Citadel: its gate and walls in the west cliff.
    x, y = polar(*CITADEL)
    rot = math.radians(CITADEL[0]) + math.pi / 2
    for side in (-1, 1):
        px, py = x + side * 10.0 * math.cos(rot), y + side * 10.0 * math.sin(rot)
        box(c, "Citadel Tower %d" % side, px, py, 4.0, 4.0, FLOOR_Z - 1.0, FLOOR_Z + 22.0, ("frost_stone", "wall"), rot=rot)
        cone(c, "Citadel Spire %d" % side, px, py, 5.0, FLOOR_Z + 22.0, 8.0, ("frost_cliff", "wall"), role="visual")
    box(c, "Citadel Gate", x, y, 6.0, 2.0, FLOOR_Z - 1.0, FLOOR_Z + 12.0, ("dark_corridor", "wall"), rot=rot, role="visual")
    box(c, "Citadel Gate Arch", x, y, 7.5, 3.0, FLOOR_Z + 12.0, FLOOR_Z + 16.0, ("frost_stone", "wall"), rot=rot)
    # Snowy Summit Pass: the giant tree.
    x, y = polar(*TREE)
    x, y = x, y + 18.0
    box(c, "Giant Tree Trunk", x, y, 7.0, 7.0, FLOOR_Z - 2.0, FLOOR_Z + 60.0, ("weathered_timber", "wall"))
    for k, (r, z) in enumerate(((26.0, 40.0), (20.0, 56.0), (13.0, 70.0))):
        cone(c, "Giant Tree Crown %d" % k, x, y, r, FLOOR_Z + z, 20.0, ("pine_snow", "wall"), segs=8, role="visual")
    # Aurora Rift: the crack in the glacier, ice blocks either side.
    x, y = polar(*RIFT)
    rot = math.radians(RIFT[0]) + math.pi / 2
    for side in (-1, 1):
        for j in range(3):
            px = x + side * (9.0 + j * 7.0) * math.cos(rot) + j * 6.0 * math.cos(rot - math.pi / 2)
            py = y + side * (9.0 + j * 7.0) * math.sin(rot) + j * 6.0 * math.sin(rot - math.pi / 2)
            box(c, "Rift Ice %d %d" % (side, j), px, py, 4.0, 5.0, FLOOR_Z - 1.0, FLOOR_Z + 24.0 - j * 4.0, ("glacier_ice", "wall"),
                rot=rot + 0.3 * side)
    box(c, "Rift Crack", x + 6 * math.cos(rot - math.pi / 2), y + 6 * math.sin(rot - math.pi / 2), 5.0, 1.0, FLOOR_Z - 1.0,
        FLOOR_Z + 20.0, ("icefall_blue", "wall"), rot=rot, role="visual")
    gx, gy, gz = c.game(x, y, FLOOR_Z + 30.0)
    c.entity("sparkles", rate=12, radius=30)
    # The Frozen Pass: walled with Rimefang's ice (the way on, once he falls).
    x, y = polar(*FROZEN_PASS)
    rot = math.radians(FROZEN_PASS[0]) + math.pi / 2
    box(c, "Frozen Pass Ice", x, y, 9.0, 3.0, FLOOR_Z - 1.0, FLOOR_Z + 18.0, ("berg_ice", "wall"), rot=rot)

    # The gorge's far end, back towards the valley: it bends out of sight.
    box(c, "Gorge Bend", gorge_x(GORGE_Y0 - 4), GORGE_Y0 - 4, GORGE_HW + 24.0, 6.0, FLOOR_Z - 2.0, RIM_Z, ("obsidian_cliff", "wall"))
    c.entity("snowfall", rate=60, radius=60)

    gates = c.checkpoints(height=10.0)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish()
    print("ring", round(c.length, 1), "gates", len(gates))


if __name__ == "__main__":
    main()
