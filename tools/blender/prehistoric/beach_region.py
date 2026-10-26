# Tropic Isles, the overworld's fourth region (greybox): the drivable island at the end of
# Desert World's Dust Road, with the gateways into its four courses (the Claude Doc
# "Kartipelago Overworld: Concept & Layout"; src/overworld/regions.ts places them).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/beach_region.py      (the bpy module)
#
# Broad strokes, all placeholder, built like the other three regions:
#
#   - An island about 800 m across: jungle hills round its north half, a long beach round
#     its south half running down into shallow sea, sea stacks out on the reef, and a
#     lagoon in the middle with the ring road round it.
#   - From the north, the Dust Road comes down through the hills from the desert to
#     Raptor's boardwalk village (the town square) and on to the ring.
#   - The landmarks the gateways stand at: Coral Cove on the beach in the south-east,
#     Volcano Isle at the end of a pier pointing out to the smoking island offshore
#     (south), Shipwreck Bay by a wrecked hull on the beach (south-west), Splash Lagoon at
#     the water park's slide tower against the hills (north-west).
#   - Tidewyrm's lair (the boss gateway): a sea cave in the east headland.
#   - The reef running out to sea in the south: Tidewyrm's Causeway one day (the way on to
#     the Dragon Kingdom, far over the horizon).

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp, smooth  # noqa: E402
from valley_region import box, cone, polar  # noqa: E402
import puzzle_kit  # noqa: E402

TRACK_ID = "beach_region"
FLOOR_Z = 2.0
WATER_Z = -0.8
RING_R = 220.0
LAGOON_R = 100.0
CLIFF_R = 335.0
RIM_Z = 70.0
SHORE_R = 262.0  # where the beach starts down into the sea
STACKS_R = 405.0  # the reef's sea stacks: the edge

VILLAGE = (0.0, 290.0, 26.0)  # Raptor's boardwalk village: x, y, radius
ROAD_HW = 14.0
ROAD_Y0 = 470.0  # the Dust Road's far (desert) end: the passage back
CORAL = (-35.0, 288.0)  # angle, radius
PIER = (-90.0, 280.0, 345.0)  # angle, from radius, to radius
WRECK = (-145.0, 290.0)
SPLASH = (150.0, CLIFF_R - 30.0)
LAIR = (8.0, CLIFF_R + 6.0)  # Tidewyrm's lair: the boss gateway (east headland)
VOLCANO = (-90.0, 620.0)
# The Tiki Gongs (src/overworld/puzzles.ts): a tiki hut in the north-east, its door shut,
# and three gongs to strike in order (their torches: one, two, three) round the island.
HUT = (45.0, 300.0)
GONGS = [(120.0, 255.0), (-10.0, 250.0), (-120.0, 245.0)]


def ring_r(a):
    return RING_R + 10.0 * math.sin(3 * a + 0.2)


def south(a):
    """How much of the island's edge at angle a is beach and sea (1) rather than hills (0)."""
    return smooth((-math.sin(a) - 0.1) / 0.35)


def natural(x, y):
    """The island: low and rolling, the lagoon sunk in the middle, jungle hills round the
    north, the beach running down into the shallows round the south; the Dust Road's cut
    through the hills."""
    r = math.hypot(x, y)
    a = math.atan2(y, x)
    h = FLOOR_Z + 0.8 * math.sin(x / 39.0) * math.cos(y / 43.0) + 0.5 * math.sin((x + y) / 61.0)
    vx, vy, vr = VILLAGE
    h = lerp(FLOOR_Z, h, smooth((math.hypot(x - vx, y - vy) - vr) / 14.0))
    if r < LAGOON_R + 14:
        h = lerp(h, WATER_Z - 0.9, smooth((LAGOON_R + 14 - r) / 14.0))
    s = south(a)
    hills = RIM_Z * (1.0 + 0.2 * math.sin(5 * a) + 0.1 * math.sin(13 * a + 1.0)) * smooth((r - CLIFF_R) / 55.0)
    beach = lerp(0.0, WATER_Z - 0.9 - FLOOR_Z, smooth((r - SHORE_R) / 40.0))
    h += lerp(hills, beach, s)
    g = smooth((ROAD_HW + 12 - abs(x)) / 12) * smooth((y - 250.0) / 40.0) * (1 - s)
    if g > 0:
        h = lerp(h, FLOOR_Z + 0.03 * max(0.0, y - 330.0), g)
    return h


def classify(c, n, info):
    if n.z < 0.62:
        return ("valley_cliff", "wall")
    if c.z < WATER_Z + 0.3:
        return ("wet_sand", "water")  # (the lagoon and the shallows are wadeable)
    r = math.hypot(c.x, c.y)
    if r > SHORE_R - 30 and south(math.atan2(c.y, c.x)) > 0.5:
        return ("beach_sand", "sand")
    if r < LAGOON_R + 18:
        return ("beach_sand", "sand")
    return ("fern_floor", "grass")


def road_z(x, y):
    return max(natural(x, y), WATER_Z + 0.4) + 0.2


def line(a, b, every=8.0, z=road_z):
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / every))
    return [(lerp(a[0], b[0], k / n), lerp(a[1], b[1], k / n), z(lerp(a[0], b[0], k / n), lerp(a[1], b[1], k / n)))
            for k in range(n + 1)]


def main():
    c = kit.Course(TRACK_ID, "Tropic Isles (greybox)", "coral_cove")
    ring = []
    for k in range(48):
        a = k * math.tau / 48
        r = ring_r(a)
        x, y = r * math.cos(a), r * math.sin(a)
        ring.append((x, y, road_z(x, y)))
    c.route(ring, width=14.0, bank=4.0)
    sand = ("beach_sand", "sand")
    planks = ("wood_planks", "road")
    c.kinds = {"road": {"mat": "beach_road", "shoulder": 1.6, "shoulder_mat": sand}}
    c.roads(kit.plan(c, [], "road", max_len=200.0))

    def ring_end(a_deg):
        a = math.radians(a_deg)
        return ring_r(a) * math.cos(a) * 0.985, ring_r(a) * math.sin(a) * 0.985

    trail = dict(width=10.0, shoulder=1.2, shoulder_mat=sand)
    # The Dust Road, down through the hills past the village to the ring.
    vx, vy, vr = VILLAGE
    road = [(0.0, y, FLOOR_Z + 0.2 + 0.03 * max(0.0, y - 330.0)) for y in range(int(ROAD_Y0) - 25, int(vy + vr), -8)]
    c.side_road("Dust Road", road, "beach_road", "road", **trail)
    c.side_road("Village Road", line((vx, vy - vr + 2), ring_end(90.0)), "beach_road", "road", **trail)
    # Out from the ring to the landmarks.
    for name, (a, r) in (("Coral Road", CORAL), ("Wreck Road", WRECK), ("Splash Road", SPLASH), ("Lair Road", LAIR)):
        c.side_road(name, line(ring_end(a), polar(a, r - 12.0)), "beach_road", "road", **trail)
    a, r0, r1 = PIER
    c.side_road("Pier Road", line(ring_end(a), polar(a, r0 + 2.0)), "beach_road", "road", **trail)
    c.side_road("Pier", line(polar(a, r0), polar(a, r1), every=4.0, z=lambda x, y: FLOOR_Z + 0.4), "wood_planks", "road",
                width=10.0, shoulder=0.4, shoulder_mat=planks, barrier=1.0, barrier_mat=("tiki_wood", "wall"), deck=1.6,
                deck_mat=("tiki_wood", "wall"), ground=False)

    X0, X1, Y0, Y1 = -470, 470, -470, 480
    c.terrain("Island", X0, X1, Y0, Y1, 5.0, natural, classify, near=8.0, fade=14.0)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 5.0, lambda x, y: natural(x, y) - 0.5, c.lib(*sand))
    c.disc("Sea", 0.0, -200.0, 1500.0, WATER_Z, c.lib("sea_water", "water"), role="visual", n=64)

    # Raptor's village: a boardwalk square, tiki huts round it, a campfire.
    c.disc("Village Boardwalk", vx, vy, vr, FLOOR_Z + 0.05, c.lib(*planks), coll="Props", n=40)
    for k in range(6):
        a = k * math.tau / 6 + math.pi / 6
        if abs(math.cos(a)) < 0.3:
            continue  # (clear of the road through the square)
        hx, hy = vx + (vr + 6) * math.cos(a), vy + (vr + 6) * math.sin(a)
        box(c, "Hut %d" % k, hx, hy, 3.5, 3.5, FLOOR_Z - 1.0, FLOOR_Z + 4.0, ("tiki_wood", "wall"), rot=a)
        cone(c, "Hut Roof %d" % k, hx, hy, 5.5, FLOOR_Z + 4.0, 4.0, ("thatch", "wall"), segs=6, role="visual")
    gx, gy, gz = c.game(vx, vy, FLOOR_Z + 0.3)
    c.entity("campfire", x=gx, y=gy, z=gz)
    # Palms all round the island.
    for k in range(40):
        a = k * math.tau / 40 + 0.37 * math.sin(k * 1.9)
        r = (SHORE_R - 18 if south(a) > 0.5 else CLIFF_R - 25) + 9 * math.sin(k * 2.7)
        px, py = polar(math.degrees(a), r)
        if min(abs(math.degrees(a) - g) % 360 for g in (CORAL[0], PIER[0], WRECK[0], SPLASH[0], LAIR[0], 90.0,
                                                    HUT[0], *(a for a, _ in GONGS))) < 7:
            continue  # (clear of the roads out)
        g = natural(px, py)
        box(c, "Palm %d" % k, px, py, 0.5, 0.5, g - 1.0, g + 10.0, ("palm_bark", "wall"))
        cone(c, "Palm Crown %d" % k, px, py, 4.5, g + 9.0, 2.0, ("fern_floor", "wall"), segs=5, role="visual")

    # Coral Cove: coral heads in the shallows off the beach.
    for k in range(6):
        x, y = polar(CORAL[0] + (k - 2.5) * 4.0, CORAL[1] + 30 + 8 * (k % 2))
        cone(c, "Coral %d" % k, x, y, 2.5, WATER_Z - 1.5, 3.0 + k % 3, ("party_red" if k % 2 else "party_yellow", "wall"),
             segs=6)
    # Volcano Isle: the smoking island offshore, beyond the reef.
    vx2, vy2 = polar(*VOLCANO)
    volc = c.rock_mass("Volcano Isle", vx2, vy2, 110.0, 90.0, 130.0, z0=WATER_Z - 4.0, n=18, seed=7,
                       bands=[(1.0, 0.0), (0.7, 0.4), (0.4, 0.8), (0.25, 1.0)], base=WATER_Z)
    c.assign(volc, c.lib("isle_rock", "wall"))
    gx, gy, gz = c.game(vx2, vy2, 132.0)
    c.entity("eruption", x=gx, y=gy, z=gz, period=15.0, offset=2.0)
    # Shipwreck Bay: a wrecked hull lying on its side on the beach.
    x, y = polar(WRECK[0], WRECK[1] + 22.0)
    ua = math.radians(WRECK[0]) + 0.6
    box(c, "Wreck Hull", x, y, 16.0, 4.5, WATER_Z - 1.0, FLOOR_Z + 4.0, ("wreck_planks", "wall"), rot=ua)
    box(c, "Wreck Mast", x + 6 * math.cos(ua + 1.2), y + 6 * math.sin(ua + 1.2), 0.5, 0.5, FLOOR_Z, FLOOR_Z + 16.0,
        ("wreck_planks", "wall"), rot=ua)
    # Splash Lagoon: the water park's slide tower against the hills.
    x, y = polar(*SPLASH)
    rot = math.radians(SPLASH[0]) + math.pi / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(c, "Slide Tower Leg %d%d" % (sx, sy), x + sx * 9.0 * math.cos(rot) + sy * 3.0 * math.cos(rot - math.pi / 2),
                y + sx * 9.0 * math.sin(rot) + sy * 3.0 * math.sin(rot - math.pi / 2), 0.6, 0.6, FLOOR_Z - 1.0, FLOOR_Z + 18.0,
                ("party_white", "wall"))
    box(c, "Slide Tower Deck", x + 6 * math.cos(rot - math.pi / 2), y + 6 * math.sin(rot - math.pi / 2), 10.0, 4.0,
        FLOOR_Z + 18.0, FLOOR_Z + 19.0, ("splash_deck", "wall"), rot=rot, role="visual")
    for k, m in enumerate(("splash_slide_red", "splash_slide_yellow", "splash_slide_blue")):
        box(c, "Slide %d" % k, x + (k - 1) * 6.0 * math.cos(rot) + 3 * math.cos(rot - math.pi / 2),
            y + (k - 1) * 6.0 * math.sin(rot) + 3 * math.sin(rot - math.pi / 2), 1.2, 8.0, FLOOR_Z + 4.0 + 4 * k,
            FLOOR_Z + 5.0 + 4 * k, (m, "wall"), rot=rot, role="visual")

    # Tidewyrm's lair: a sea cave in the east headland, rocks heaped round its mouth.
    x, y = polar(*LAIR)
    rot = math.radians(LAIR[0]) + math.pi / 2
    box(c, "Lair Mouth", x, y, 8.0, 2.0, FLOOR_Z - 1.0, FLOOR_Z + 12.0, ("dark_corridor", "wall"), rot=rot, role="visual")
    for k in range(7):
        t = (k - 3) / 3.0
        if abs(t) < 0.4:
            continue
        px, py = x + t * 12.0 * math.cos(rot), y + t * 12.0 * math.sin(rot)
        cone(c, "Lair Rock %d" % k, px, py, 3.5 + abs(t) * 1.5, FLOOR_Z - 1.0, 9.0 + 7.0 * (1 - abs(t)), ("isle_rock", "wall"),
             segs=5)

    # The reef: sea stacks all round the south, the edge of the drivable shallows, and a
    # line of reef rocks running out to sea through them (the causeway, one day).
    a0, a1 = math.radians(-172.0), math.radians(-8.0)
    n = int((a1 - a0) * STACKS_R / 13.0)
    for k in range(n + 1):
        a = lerp(a0, a1, k / n)
        r = STACKS_R + 8.0 * math.sin(k * 1.3)
        x, y = r * math.cos(a), r * math.sin(a)
        cone(c, "Sea Stack %d" % k, x, y, 8.5, WATER_Z - 3.0, 14.0 + 8.0 * abs(math.sin(k * 0.77)), ("isle_rock", "wall"),
             segs=6)
    for k in range(8):
        x, y = polar(-90.0 + 3.0 * math.sin(k * 1.7), STACKS_R + 30.0 + k * 22.0)
        cone(c, "Reef Rock %d" % k, x, y, 4.0, WATER_Z - 2.0, 2.6, ("isle_rock", "wall"), segs=5, role="visual")

    # The Tiki Gongs' hut (its door is the game's) and where the gongs hang.
    puzzle_kit.pen(c, "tiki_gongs", "Tiki Hut", *polar(*HUT), math.radians(HUT[0]) + math.pi, 10.0, 4.5, ("tiki_wood", "wall"),
                   FLOOR_Z, roof=("thatch", "wall"))
    puzzle_kit.switches(c, "tiki_gongs", [polar(*g) for g in GONGS], natural, lanterns=[1, 2, 3])

    # The Dust Road's far end, back up towards the desert: it bends out of sight.
    box(c, "Road Bend", 0.0, ROAD_Y0 + 4, ROAD_HW + 24.0, 6.0, FLOOR_Z - 2.0, RIM_Z, ("valley_cliff", "wall"))

    # (Raced too: the champion's challenge, once round the ring, from this line.)
    c.start_line()
    gates = c.checkpoints(height=10.0)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish(extra={"race": {"laps": 1}})
    print("ring", round(c.length, 1), "gates", len(gates))


if __name__ == "__main__":
    main()
