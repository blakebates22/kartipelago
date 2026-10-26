# Desert World, the overworld's third region (greybox): the drivable red-rock basin past
# the Snow Kingdom's Frozen Pass, with the gateways into its four courses (the Claude Doc
# "Kartipelago Overworld: Concept & Layout"; src/overworld/regions.ts places them).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/desert_region.py      (the bpy module)
#
# Broad strokes, all placeholder, built like Dinosaur Valley and the Snow Kingdom:
#
#   - A basin about 800 m across ringed by banded mesa cliffs, a ring road round it, and
#     a meteor crater in the middle (the Impact Depths gateway on its rim).
#   - From the west, the Frozen Pass comes down out of the snow to Stego's trading post
#     (the town square) and on east to the ring and the crater.
#   - The landmarks the gateways stand at: Canyon Dash at a slot canyon in the north cliff,
#     Oasis Haven at a palm-ringed pool in the north-east, Dry Gulch Ghost Town at the end
#     of its false-front street in the south-east, Impact Depths on the crater's rim.
#   - Scorchwind's lair (the boss gateway): a rock arch in the south-west cliff with a dust
#     devil turning in front of it.
#   - The Dust Road south, on to Tropic Isles, buried under a sand drift until Scorchwind
#     falls (the story's way on; its region comes later).

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp, smooth  # noqa: E402
from valley_region import box, cone, polar  # noqa: E402
import puzzle_kit  # noqa: E402
import region_ruin as ruin  # noqa: E402
import canyon_props as cp  # noqa: E402
import oasis_props as op  # noqa: E402
import region_paint as paint  # noqa: E402

# (--ruin: Desert World after Scorchwind's attack. Only the ruin has his lair, and his
# drift burying the Dust Road; the trading post is wrecked and sand drifts across the
# basin.)
RUIN = ruin.ON
TRACK_ID = ruin.track_id("desert_region")
FLOOR_Z = 2.0
RING_R = 222.0
CLIFF_R = 335.0
RIM_Z = 75.0
CRATER_R = 48.0  # the crater's rim

POST = (-290.0, 0.0, 26.0)  # Stego's trading post: x, y, radius
PASS_HW = 14.0
PASS_X0 = -470.0  # the Frozen Pass's far (snow) end: the passage back
CANYON = (100.0, CLIFF_R + 6.0)  # angle, radius
OASIS = (40.0, 290.0)
GULCH = (-40.0, CLIFF_R - 30.0)
LAIR = (-135.0, CLIFF_R + 6.0)  # Scorchwind's lair: the boss gateway (south-west)
DUST_ROAD = (-90.0, CLIFF_R + 6.0)  # the way on, south
# Stego's old well (Act V's return task): a walled yard in the north-west, its way in
# buried under a drift the Desert Tool blows away.
RETURN = (145.0, 300.0)


def ring_r(a):
    return RING_R + 11.0 * math.sin(3 * a + 0.7)


def natural(x, y):
    """The basin floor in low dunes; the crater sunk in the middle with its raised rim;
    banded mesas all round; the Frozen Pass's cut in the west; the slot canyon's in the
    north."""
    r = math.hypot(x, y)
    h = FLOOR_Z + 0.9 * math.sin(x / 33.0 + y / 71.0) + 0.6 * math.cos(y / 29.0 - x / 87.0)
    px, py, pr = POST
    h = lerp(FLOOR_Z, h, smooth((math.hypot(x - px, y - py) - pr) / 14.0))
    # The crater: a raised rim, the bowl inside it.
    h += 5.0 * math.exp(-((r - CRATER_R) / 9.0) ** 2)
    if r < CRATER_R:
        h = lerp(h, FLOOR_Z - 10.0, smooth((CRATER_R - r) / 26.0))
    # The mesas: terraced (three steps) rather than one slope.
    a = math.atan2(y, x)
    t = smooth((r - CLIFF_R) / 50.0)
    steps = sum(smooth((t - k / 3.0) * 6.0) for k in range(3)) / 3.0
    h += RIM_Z * (0.9 + 0.15 * math.sin(4 * a) + 0.1 * math.sin(9 * a + 2.0)) * lerp(t, steps, 0.6)
    # The Frozen Pass (west) and the slot canyon (north) cut through.
    g = smooth((PASS_HW + 12 - abs(y)) / 12) * smooth((-x - 250.0) / 40.0)
    if g > 0:
        h = lerp(h, FLOOR_Z + 0.03 * max(0.0, -x - 330.0), g)
    return h


def classify(c, n, info):
    if n.z < 0.62:
        if c.x < -260 and abs(c.y) < PASS_HW + 30:
            return ("frost_cliff", "wall")  # (the pass down from the snow)
        return ("strata_orange", "wall")
    r = math.hypot(c.x, c.y)
    if r < CRATER_R + 4:
        return ("crater_ground", "dirt")
    return ("red_sand", "loose_sand")


def road_z(x, y):
    return natural(x, y) + 0.2


def line(a, b, every=8.0, z=road_z):
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / every))
    return [(lerp(a[0], b[0], k / n), lerp(a[1], b[1], k / n), z(lerp(a[0], b[0], k / n), lerp(a[1], b[1], k / n)))
            for k in range(n + 1)]


def main():
    c = kit.Course(TRACK_ID, "Desert World (greybox, ruined)" if RUIN else "Desert World (greybox)", "canyon_dash")
    ring = []
    for k in range(48):
        a = k * math.tau / 48
        r = ring_r(a)
        x, y = r * math.cos(a), r * math.sin(a)
        ring.append((x, y, road_z(x, y)))
    c.route(ring, width=14.0, bank=4.0)
    sand = ("red_sand", "loose_sand")
    c.kinds = {"road": {"mat": "dash_road", "shoulder": 1.5, "shoulder_mat": ("pale_sand", "dirt")}}
    c.roads(kit.plan(c, [], "road", max_len=200.0))

    def ring_end(a_deg):
        a = math.radians(a_deg)
        return ring_r(a) * math.cos(a) * 0.985, ring_r(a) * math.sin(a) * 0.985

    trail = dict(width=10.0, shoulder=1.2, shoulder_mat=("pale_sand", "dirt"))
    # The Frozen Pass, down past the trading post to the ring, and on to the crater's rim.
    px, py, pr = POST
    pas = [(x, 0.0, FLOOR_Z + 0.2 + 0.03 * max(0.0, -x - 330.0)) for x in range(int(PASS_X0) + 25, int(px - pr), 8)]
    c.side_road("Frozen Pass Road", pas, "dash_road", "road", **trail)
    c.side_road("Post Road", line((px + pr - 2, py), ring_end(180.0)), "dash_road", "road", **trail)
    c.side_road("Crater Road", line(ring_end(180.0), polar(180.0, CRATER_R + 12.0)), "dash_road", "road", **trail)
    # Out from the ring to the landmarks.
    outs = [("Canyon Road", CANYON), ("Oasis Road", OASIS), ("Gulch Street", GULCH)]
    if RUIN:
        outs += [("Lair Road", LAIR), ("Dust Road", DUST_ROAD)]
    for name, (a, r) in outs:
        c.side_road(name, line(ring_end(a), polar(a, r - (28.0 if name == "Oasis Road" else 12.0))), "dash_road", "road", **trail)

    X0, X1, Y0, Y1 = -480, 470, -470, 470
    c.terrain("Basin", X0, X1, Y0, Y1, 5.0, natural, classify, near=8.0, fade=14.0)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 5.0, lambda x, y: natural(x, y) - 0.5, c.lib(*sand))

    # Stego's trading post: the town square, its stalls and its water tower.
    c.disc("Post Square", px, py, pr, FLOOR_Z + 0.05, c.lib("pale_sand", "dirt"), coll="Props", n=40)
    for k in range(6):
        a = k * math.tau / 6 + math.pi / 6
        if abs(math.sin(a)) < 0.3:
            continue  # (clear of the road through the square)
        hx, hy = px + (pr + 6) * math.cos(a), py + (pr + 6) * math.sin(a)
        if RUIN:
            # Blown down: the walls broken off low, the awnings gone, sand piled against them.
            box(c, "Stall %d" % k, hx, hy, 4.5, 3.5, FLOOR_Z - 1.0, FLOOR_Z + 1.6 + 0.8 * (k % 2), ("adobe", "wall"), rot=a)
            ruin.rubble(c, "Stall Rubble %d" % k, hx + 3.0 * math.cos(a), hy + 3.0 * math.sin(a), natural, ("adobe", "wall"),
                        n=5, spread=3.0, size=0.9, seed=k)
            continue
        box(c, "Stall %d" % k, hx, hy, 4.5, 3.5, FLOOR_Z - 1.0, FLOOR_Z + 4.5, ("adobe", "wall"), rot=a)
        box(c, "Stall Awning %d" % k, hx, hy, 5.2, 4.2, FLOOR_Z + 4.5, FLOOR_Z + 5.0, ("tin_roof", "wall"), rot=a,
            role="visual")
    tx, ty = px - 10.0, py + 16.0
    if RUIN:
        # The water tower toppled: its tank on its side in the sand, legs snapped.
        box(c, "Water Tower Tank", tx - 6.0, ty + 3.0, 3.0, 2.5, FLOOR_Z - 0.5, FLOOR_Z + 4.5, ("weathered_timber", "wall"),
            rot=0.5)
        for sx in (-1, 1):
            ruin.stump(c, "Water Tower Leg %d" % sx, tx + sx * 2.2, ty - 2.2, FLOOR_Z, ("weathered_timber", "wall"), h=2.0, r=0.3)
    for sx in ((-1, 1) if not RUIN else ()):
        for sy in (-1, 1):
            box(c, "Water Tower Leg %d%d" % (sx, sy), tx + sx * 2.2, ty + sy * 2.2, 0.3, 0.3, FLOOR_Z - 1.0, FLOOR_Z + 9.0,
                ("weathered_timber", "wall"))
    if not RUIN:
        box(c, "Water Tower Tank", tx, ty, 3.0, 3.0, FLOOR_Z + 9.0, FLOOR_Z + 14.0, ("weathered_timber", "wall"), role="visual")
    gx, gy, gz = c.game(px, py, FLOOR_Z + 0.3)
    c.entity("campfire", x=gx, y=gy, z=gz)

    # Canyon Dash: a slot canyon's mouth in the north cliff, a cairn either side.
    x, y = polar(*CANYON)
    rot = math.radians(CANYON[0]) + math.pi / 2
    box(c, "Slot Canyon", x, y, 6.0, 2.0, FLOOR_Z - 1.0, FLOOR_Z + 30.0, ("dark_corridor", "wall"), rot=rot, role="visual")
    for side in (-1, 1):
        sx, sy = x + side * 9.0 * math.cos(rot), y + side * 9.0 * math.sin(rot)
        c.assign(c.rock_mass("Canyon Pillar %d" % side, sx, sy, 5.0, 4.0, FLOOR_Z + 34.0, z0=FLOOR_Z - 1.0, n=10, seed=3 + side),
                 c.lib("strata_orange", "wall"))
    # Oasis Haven: the pool and its palms.
    x, y = polar(*OASIS)
    c.disc("Oasis Pool", x, y, 16.0, FLOOR_Z - 0.3, c.lib("canal_water", "water"), role="visual", n=30, wobble=0.15, seed=4)
    c.disc("Oasis Lawn", x, y, 24.0, FLOOR_Z - 0.35, c.lib("oasis_lawn", "grass"), coll="Props", n=30, wobble=0.1, seed=5)
    for k in range(7):
        a = k * math.tau / 7 + 0.3
        bx, by = x + 20.0 * math.cos(a), y + 20.0 * math.sin(a)
        if math.hypot(bx - polar(OASIS[0], OASIS[1] - 12)[0], by - polar(OASIS[0], OASIS[1] - 12)[1]) < 10:
            continue  # (clear of the road in)
        box(c, "Oasis Palm %d" % k, bx, by, 0.5, 0.5, FLOOR_Z - 1.0, FLOOR_Z + 10.0, ("weathered_timber", "wall"))
        cone(c, "Oasis Palm Crown %d" % k, bx, by, 4.5, FLOOR_Z + 9.0, 2.0, ("oasis_lawn", "wall"), segs=5, role="visual")
    # Dry Gulch: its false-front street, a row of buildings either side of the road's end.
    x0, y0 = polar(GULCH[0], GULCH[1] - 40.0)
    ua = math.radians(GULCH[0])
    ux, uy = math.cos(ua), math.sin(ua)
    for k in range(4):
        for side in (-1, 1):
            bx = x0 + ux * (8 + k * 11.0) + side * 12.0 * -uy
            by = y0 + uy * (8 + k * 11.0) + side * 12.0 * ux
            hgt = 6.0 + 2.0 * ((k + side) % 3)
            box(c, "Gulch House %d %d" % (k, side), bx, by, 4.5, 3.5, FLOOR_Z - 1.0, FLOOR_Z + hgt,
                ("siding_grey" if (k + side) % 2 else "weathered_timber", "wall"), rot=ua)
            box(c, "Gulch Front %d %d" % (k, side), bx - side * 3.6 * -uy, by - side * 3.6 * ux, 4.5, 0.3, FLOOR_Z + hgt,
                FLOOR_Z + hgt + 2.5, ("weathered_timber", "wall"), rot=ua, role="visual")
    gx, gy, gz = c.game(x0, y0, FLOOR_Z + 1.0)
    c.entity("tumbleweed", ax=gx - 20 * uy, ay=gy, az=gz - 20 * ux, bx=gx + 20 * uy, by=gy, bz=gz + 20 * ux, period=13.0,
             offset=0.0, travel=6.0, r=0.8)
    # Impact Depths: the crater's rim, black rock heaped round it.
    for k in range(12):
        a = k * math.tau / 12 + 0.2
        if abs(math.cos(a) + 1.0) < 0.3:
            continue  # (the road onto the rim, from the west)
        bx, by = (CRATER_R + 10) * math.cos(a), (CRATER_R + 10) * math.sin(a)
        cone(c, "Crater Rock %d" % k, bx, by, 3.5 + math.sin(k * 1.7), natural(bx, by) - 1.0, 4.0 + 2.0 * math.cos(k * 2.3),
             ("crater_rock", "wall"), segs=5)
    gx, gy, gz = c.game(0.0, 0.0, FLOOR_Z - 9.0)
    c.entity("steam", x=gx, y=gy, z=gz)

    if RUIN:
        ruined(c)
    crater_stones(c)
    puzzle_kit.pen(c, "return", "Well Yard", *polar(*RETURN), math.radians(RETURN[0]) + math.pi, 11.0, 4.5,
                   ("adobe", "wall"), natural(*polar(*RETURN)), height=5.0)

    # The pass's far end, back up towards the snow: it bends out of sight.
    box(c, "Pass Bend", PASS_X0 - 4, 0.0, 6.0, PASS_HW + 24.0, FLOOR_Z - 2.0, RIM_Z, ("frost_cliff", "wall"))
    c.entity("dust", color="#d89a6a", rate=1.0)
    c.entity("dustwind", rate=22 if RUIN else 10, radius=60, color="#e0a878")
    gx, gy, gz = c.game(-150.0, 120.0, 40.0)
    c.entity("birds", x=gx, y=gy, z=gz, radius=70.0, count=3, speed=0.16, seed=1)

    dress(c)
    # (Raced too: the champion's challenge, once round the ring, from this line.)
    c.start_line()
    gates = c.checkpoints(height=10.0)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish(extra={"race": {"laps": 1}})
    print("ring", round(c.length, 1), "gates", len(gates))


def ruined(c):
    """After Scorchwind's attack: his lair, his drift over the Dust Road, and drifts of sand
    blown across the basin."""
    # Scorchwind's lair: a rock arch in the south-west cliff, a dust devil turning before it.
    x, y = polar(*LAIR)
    rot = math.radians(LAIR[0]) + math.pi / 2
    box(c, "Lair Mouth", x, y, 8.0, 2.0, FLOOR_Z - 1.0, FLOOR_Z + 14.0, ("dark_corridor", "wall"), rot=rot, role="visual")
    for side in (-1, 1):
        sx, sy = x + side * 11.0 * math.cos(rot), y + side * 11.0 * math.sin(rot)
        box(c, "Lair Arch Leg %d" % side, sx, sy, 3.0, 3.0, FLOOR_Z - 1.0, FLOOR_Z + 18.0, ("black_rock", "wall"), rot=rot)
    box(c, "Lair Arch", x, y, 14.0, 3.0, FLOOR_Z + 16.0, FLOOR_Z + 21.0, ("black_rock", "wall"), rot=rot)
    for k in range(4):  # (the dust devil: stacked, widening, see-through cones; visual only)
        z = FLOOR_Z + k * 6.0
        cone(c, "Dust Devil %d" % k, x - 20 * math.cos(math.radians(LAIR[0])), y - 20 * math.sin(math.radians(LAIR[0])),
             2.0 + k * 1.8, z, 8.0, ("pale_sand", "wall"), segs=8, role="visual")
    # The Dust Road south (Scorchwind's drift across it is the game's: regions.ts blocker,
    # which breaks open when he falls); where it leaves the basin, a dark cut in the cliff.
    x, y = polar(*DUST_ROAD)
    rot = math.radians(DUST_ROAD[0]) + math.pi / 2
    box(c, "Dust Road Cut", x, y, 7.0, 1.5, FLOOR_Z - 1.0, FLOOR_Z + 16.0, ("dark_corridor", "wall"), rot=rot, role="visual")
    # Drifts blown across the fields (off the roads).
    avoid = (0.0, 180.0, CANYON[0], OASIS[0], GULCH[0], LAIR[0], DUST_ROAD[0], RETURN[0], 45.0, 135.0, -45.0, -135.0)
    for k, (x, y) in enumerate(ruin.ring_spots(12, 95.0, 190.0, 8, avoid) + ruin.ring_spots(8, 255.0, 300.0, 9, avoid)):
        c.assign(c.rock_mass("Drift %d" % k, x, y, 7.0 + k % 4, 4.0 + k % 3, natural(x, y) + 2.5 + k % 3, z0=natural(x, y) - 1.0,
                             n=10, seed=20 + k, angle=k * 0.7, bands=[(1.0, 0.0), (0.7, 0.6), (0.4, 1.0)],
                             base=natural(x, y) - 1.0), c.lib("pale_sand", "wall"))


def dress(c):
    """The paint pass: Canyon Dash's desert flora (saguaros, Joshua trees, barrel cacti,
    agave, sagebrush, dry grass) and boulders and hoodoos over the basin, the oasis's
    palms and cypresses round its pool, barrels and crates at the trading post. After
    Scorchwind: the cacti and trees blown flat (most gone, the rest stumps), the
    undergrowth stripped."""
    px, py, pr = POST
    ox, oy = polar(*OASIS)
    taken = paint.Taken([(px, py, pr + 16.0), (0.0, 0.0, CRATER_R + 16.0), (*polar(*CANYON), 26.0), (ox, oy, 30.0),
                         (*polar(GULCH[0], GULCH[1] - 20.0), 34.0), (*polar(*LAIR), 34.0), (*polar(*DUST_ROAD), 22.0),
                         (*polar(*RETURN), 18.0), (*polar(RETURN[0], RETURN[1] - 16.0), 9.0),
                         *((*polar(a, 74.0), 10.0) for a in (135.0, 45.0, -45.0, -135.0))])

    def open_ground(x, y):
        r = math.hypot(x, y)
        return CRATER_R + 10 < r < CLIFF_R - 10 and not (x < -250 and abs(y) < PASS_HW + 12)

    def foot(x, y):
        return open_ground(x, y) and math.hypot(x, y) > CLIFF_R - 50

    g = natural
    for v in range(3):
        paint.scatter(c, cp.boulder(c, v), 14, CLIFF_R, foot, g, taken, 90 + v, room=4.0, scale=(1.0, 2.4))
    for v in range(2):
        paint.scatter(c, cp.hoodoo(c, v, 12.0 + 6.0 * v), 5, CLIFF_R, open_ground, g, taken, 95 + v, room=12.0)
    # Round the oasis's pool: palms and cypresses (it's water: they stay, even after).
    for v in range(2):
        paint.scatter(c, op.palm(c, v, 10.0 + 2.0 * v), 6, CLIFF_R,
                      lambda x, y: 18.0 < math.hypot(x - ox, y - oy) < 32.0 and open_ground(x, y), g, paint.Taken(), 70 + v,
                      room=4.0)
    tall = [cp.saguaro(c, v) for v in range(3)] + [cp.joshua_tree(c, v) for v in range(2)]
    low = [cp.barrel_cactus(c, v) for v in range(2)] + [cp.agave(c, v) for v in range(2)]
    if RUIN:
        # Scorchwind's storm tore through: a few broken stems stand, the rest is bare.
        for v, t in enumerate(tall):
            paint.scatter(c, t, 8, CLIFF_R, open_ground, g, taken, 10 + v, room=6.0)
        for k in range(40):
            a, r = k * 2.39996, 70.0 + (k * 41) % 250
            x, y = r * math.cos(a), r * math.sin(a)
            if open_ground(x, y) and taken.clear(x, y, 3.0) and paint.road_clear(c, x, y, 4.0):
                ruin.stump(c, "Snapped Cactus %d" % k, x, y, g(x, y), ("weathered_timber", "wall"), h=0.6 + (k % 3) * 0.5,
                           r=0.4)
                taken.add(x, y, 2.0)
        return
    for v, t in enumerate(tall):
        paint.scatter(c, t, 26, CLIFF_R, open_ground, g, taken, 10 + v, room=6.0, scale=(0.9, 1.5))
    for v, t in enumerate(low):
        paint.scatter(c, t, 40, CLIFF_R, open_ground, g, taken, 30 + v, room=2.5, role="visual")
    for v in range(2):
        paint.scatter(c, cp.sagebrush(c, v), 120, CLIFF_R, open_ground, g, taken, 40 + v, room=2.0, role="visual")
        paint.scatter(c, cp.dry_grass(c, v), 140, CLIFF_R, open_ground, g, taken, 50 + v, room=1.5, role="visual")
    # The trading post's barrels and crates, stacked by the stalls.
    crate = cp.crates(c, 0)
    for k in range(5):
        a = k * math.tau / 5 + 0.3
        x, y = px + (pr - 4.0) * math.cos(a), py + (pr - 4.0) * math.sin(a)
        if abs(math.sin(a)) > 0.35:
            c.place(crate, x, y, FLOOR_Z, rot=a)


def crater_stones(c):
    # The Crater Stones (src/overworld/puzzles.ts): a sandstone vault on the crater's floor,
    # its gate looking west up the road in, and four switch stones round the rim.
    puzzle_kit.pen(c, "crater_stones", "Vault", 0.0, 0.0, math.pi, 8.0, 4.5, ("sandstone_block", "wall"), natural(0.0, 0.0),
                   height=5.0)
    puzzle_kit.switches(c, "crater_stones", [polar(a, 74.0) for a in (135.0, 45.0, -45.0, -135.0)], natural,
                        ring_mat=("crater_rock", "wall"))


if __name__ == "__main__":
    main()
