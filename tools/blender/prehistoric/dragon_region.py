# The Dragon Kingdom, the overworld's last region (greybox): far over the horizon at the
# end of Tidewyrm's Causeway, with the gateways into its four courses and King Pyrrhax's
# Citadel (the Claude Doc "Kartipelago Overworld: Concept & Layout"; src/overworld/
# regions.ts places them).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/dragon_region.py [--ruin]      (the bpy module)
#
# Broad strokes, all placeholder, built like the other regions:
#
#   - A green basin about 800 m across ringed by dark crags, a ring road round it and
#     Dragonfire Square in the middle, a great dragon statue at its heart.
#   - From the south, the Causeway comes in over the sea to the harbour (where you arrive).
#   - The landmarks the gateways stand at: Dragonspire Keep's tower on a crag (north-west),
#     Dragon Canyon's overgrown jungle gate (east), Emberdeep Hold's fortress gate cut into
#     the mountain under a storm (north-east), the Moonstone Kingdom's moon gate among
#     violet lanterns (west), and King Pyrrhax's Citadel on the north cliff.
#   - --ruin: the kingdom after the sacrifice: scorched, smoking, rubble at every gate, the
#     statue broken.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp, smooth  # noqa: E402
from valley_region import box, cone, polar  # noqa: E402
import region_ruin as ruin  # noqa: E402
import keep_props as kp  # noqa: E402
import props  # noqa: E402
import region_paint as paint  # noqa: E402
import ruin_kit  # noqa: E402
import summit_props as sp  # noqa: E402

RUIN = ruin.ON
TRACK_ID = ruin.track_id("dragon_region")
FLOOR_Z = 2.0
WATER_Z = -0.8
RING_R = 220.0
SQUARE_R = 30.0
CLIFF_R = 335.0
RIM_Z = 90.0

HARBOUR = (0.0, -285.0, 26.0)  # where the Causeway comes in: x, y, radius
CAUSE_HW = 12.0
CAUSE_Y0 = -470.0  # the Causeway's far (Tropic Isles) end: the passage back
KEEP = (140.0, 300.0)  # angle, radius
CANYON = (10.0, CLIFF_R + 6.0)
HOLD = (55.0, CLIFF_R + 6.0)
MOON = (200.0, 290.0)
CITADEL = (100.0, CLIFF_R + 6.0)


def ring_r(a):
    return RING_R + 10.0 * math.sin(3 * a + 1.4)


def natural(x, y):
    """Rolling green ground, Dragonfire Square level in the middle, dark crags all round,
    the Causeway's cut through them in the south down to the sea."""
    r = math.hypot(x, y)
    a = math.atan2(y, x)
    h = FLOOR_Z + 0.8 * math.sin(x / 35.0) * math.cos(y / 47.0) + 0.5 * math.sin((x - y) / 57.0)
    h = lerp(FLOOR_Z, h, smooth((r - SQUARE_R) / 14.0))
    hx, hy, hr = HARBOUR
    h = lerp(FLOOR_Z, h, smooth((math.hypot(x - hx, y - hy) - hr) / 14.0))
    h += RIM_Z * (1.0 + 0.3 * math.sin(6 * a) + 0.15 * math.sin(15 * a + 2.0)) * smooth((r - CLIFF_R) / 50.0)
    g = smooth((CAUSE_HW + 14 - abs(x)) / 12) * smooth((-y - 250.0) / 40.0)
    if g > 0:
        h = lerp(h, FLOOR_Z, g)
    return h


def classify(c, n, info):
    if n.z < 0.62:
        return ("keep_rock", "wall")
    if RUIN and math.hypot(c.x, c.y) < SQUARE_R + 4:
        return ("lava_crust", "dirt")
    if RUIN and burn(c.x, c.y) > 0.55:
        return ("scorched_ground", "dirt")
    return ("keep_grass", "grass")


def burn(x, y):
    """Where the sacrifice's fire fell (0 none .. 1)."""
    return 0.55 + 0.45 * math.sin(x / 61.0 - 0.7) * math.cos(y / 43.0 + 1.1)


def road_z(x, y):
    return natural(x, y) + 0.2


def line(a, b, every=8.0, z=road_z):
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / every))
    return [(lerp(a[0], b[0], k / n), lerp(a[1], b[1], k / n), z(lerp(a[0], b[0], k / n), lerp(a[1], b[1], k / n)))
            for k in range(n + 1)]


def gate(c, name, a, r, mat, width=8.0, height=12.0, towers=0.0, roof=None):
    """A gate in the cliff (or standing free): a dark doorway between two jambs, a lintel,
    and towers either side when `towers` is given (their height)."""
    x, y = polar(a, r)
    rot = math.radians(a) + math.pi / 2
    z0 = natural(*polar(a, r - 12))
    box(c, name, x, y, width, 2.0, z0 - 1.0, z0 + height, ("dark_corridor", "wall"), rot=rot, role="visual")
    for side in (-1, 1):
        px, py = x + side * (width + 1.5) * math.cos(rot), y + side * (width + 1.5) * math.sin(rot)
        box(c, "%s Jamb %d" % (name, side), px, py, 1.8, 2.8, z0 - 1.0, z0 + height + 2.0, mat, rot=rot)
        if towers:
            tx, ty = x + side * (width + 7.0) * math.cos(rot), y + side * (width + 7.0) * math.sin(rot)
            box(c, "%s Tower %d" % (name, side), tx, ty, 4.0, 4.0, z0 - 1.0, z0 + towers, mat, rot=rot)
            if roof:
                cone(c, "%s Tower Roof %d" % (name, side), tx, ty, 5.5, z0 + towers, 9.0, roof, segs=4, role="visual")
    box(c, name + " Lintel", x, y, width + 2.5, 3.0, z0 + height, z0 + height + 3.5, mat, rot=rot)
    return x, y, z0


def dress(c):
    """The paint pass: Dragonspire's dark mountain pines and green broadleaves over the
    basin, bushes and flowers, banner poles along the spokes and up to the Citadel. After
    the sacrifice: the same trees charred where the fire fell, the undergrowth burnt."""
    hx, hy, hr = HARBOUR
    taken = paint.Taken([(0.0, 0.0, SQUARE_R + 10.0), (hx, hy, hr + 22.0), (*polar(KEEP[0], KEEP[1] + 20.0), 34.0),
                         (*polar(*CANYON), 30.0), (*polar(*HOLD), 30.0), (*polar(*MOON), 30.0), (*polar(*CITADEL), 34.0)])

    def open_ground(x, y):
        r = math.hypot(x, y)
        return SQUARE_R + 10 < r < CLIFF_R - 10 and not (abs(x) < CAUSE_HW + 12 and y < -250)

    def foot(x, y):
        return open_ground(x, y) and math.hypot(x, y) > CLIFF_R - 50

    g = natural
    for v in range(2):
        paint.scatter(c, sp.boulder(c, v), 14, CLIFF_R, foot, g, taken, 90 + v, room=4.0, scale=(1.0, 2.2))
    for v in range(3):
        paint.scatter(c, kp.pine(c, v, 9.0 + 3.0 * v), 60, CLIFF_R, open_ground, g, taken, 10 + v, room=5.0, scale=(1.0, 1.6))
    for v in range(2):
        paint.scatter(c, sp.broadleaf(c, v, frosted=False), 30, CLIFF_R, open_ground, g, taken, 20 + v, room=6.0,
                      scale=(1.0, 1.5))
        paint.scatter(c, props.bush(c, v), 90, CLIFF_R, open_ground, g, taken, 30 + v, room=2.5, role="visual")
    paint.scatter(c, props.flowers(c), 160, CLIFF_R, open_ground, g, taken, 40, room=1.5, role="visual", sink=0.1)
    # Banner poles either side of the spokes and of the road up to the Citadel.
    pole = kp.banner_pole(c)
    for a in (0.0, 90.0, 180.0, -90.0):
        for k in range(3):
            for side in (-1, 1):
                x, y = polar(a, SQUARE_R + 20.0 + k * 50.0)
                rot = math.radians(a) + math.pi / 2
                x, y = x + side * 8.0 * math.cos(rot), y + side * 8.0 * math.sin(rot)
                c.place(pole, x, y, g(x, y), rot=rot)
    if RUIN:
        ruin_kit.char_trees(c, burn, ("Keep Pine", "Broadleaf"), chance=0.85, threshold=0.3)
        ruin.burn_away(c, burn, ("Bush", "Flowers"), threshold=0.3)


def main():
    c = kit.Course(TRACK_ID, "Dragon Kingdom (greybox, ruined)" if RUIN else "Dragon Kingdom (greybox)", "dragonspire_keep")
    ring = []
    for k in range(48):
        a = k * math.tau / 48
        r = ring_r(a)
        x, y = r * math.cos(a), r * math.sin(a)
        ring.append((x, y, road_z(x, y)))
    c.route(ring, width=14.0, bank=4.0)
    grass = ("keep_grass", "grass")
    c.kinds = {"road": {"mat": "keep_flag", "shoulder": 1.6, "shoulder_mat": ("keep_path", "dirt")}}
    c.roads(kit.plan(c, [], "road", max_len=200.0))

    def ring_end(a_deg):
        a = math.radians(a_deg)
        return ring_r(a) * math.cos(a) * 0.985, ring_r(a) * math.sin(a) * 0.985

    trail = dict(width=10.0, shoulder=1.2, shoulder_mat=("keep_path", "dirt"))
    # The Causeway in from the sea, the harbour, on up to the ring; spokes to the square.
    hx, hy, hr = HARBOUR
    cause = [(0.0, y, FLOOR_Z + 0.2) for y in range(int(CAUSE_Y0) + 25, int(hy - hr), 8)]
    c.side_road("Causeway", cause, "keep_cobble", "road", **trail)
    c.side_road("Harbour Road", line((hx, hy + hr - 2), ring_end(-90.0)), "keep_flag", "road", **trail)
    for a in (0.0, 90.0, 180.0, -90.0):
        c.side_road("Spoke %d" % a, line(polar(a, SQUARE_R - 2), ring_end(a)), "keep_flag", "road", **trail)
    for name, (a, r) in (("Keep Road", KEEP), ("Canyon Road", CANYON), ("Hold Road", HOLD), ("Moon Road", MOON),
                         ("Citadel Road", CITADEL)):
        c.side_road(name, line(ring_end(a), polar(a, r - 12.0)), "keep_flag", "road", **trail)

    X0, X1, Y0, Y1 = -470, 470, -480, 470
    c.terrain("Basin", X0, X1, Y0, Y1, 5.0, natural, classify, near=8.0, fade=14.0)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 5.0, lambda x, y: natural(x, y) - 0.5, c.lib(*grass))
    c.disc("Sea", 0.0, -700.0, 600.0, WATER_Z, c.lib("keep_lake", "water"), role="visual", n=48)

    # Dragonfire Square and its great dragon statue (broken after the sacrifice).
    c.disc("Dragonfire Square", 0.0, 0.0, SQUARE_R, FLOOR_Z + 0.05, c.lib("keep_cobble", "road"), coll="Props", n=40)
    box(c, "Statue Plinth", 0.0, 0.0, 5.0, 5.0, FLOOR_Z - 1.0, FLOOR_Z + 3.0, ("keep_ashlar", "wall"), rot=math.pi / 4)
    if RUIN:
        box(c, "Statue Stump", 0.0, 0.0, 2.0, 3.0, FLOOR_Z + 3.0, FLOOR_Z + 7.0, ("keep_rock", "wall"))
        ruin.rubble(c, "Statue Rubble", 6.0, 6.0, natural, ("keep_rock", "wall"), n=8, spread=4.0, size=1.4, seed=2)
        ruin.smoke(c, 0.0, 0.0, FLOOR_Z + 7.0)
    else:
        box(c, "Statue Body", 0.0, 0.0, 2.0, 4.5, FLOOR_Z + 3.0, FLOOR_Z + 10.0, ("keep_rock", "wall"))
        box(c, "Statue Neck", 0.0, 3.5, 1.0, 1.0, FLOOR_Z + 10.0, FLOOR_Z + 17.0, ("keep_rock", "wall"), role="visual")
        box(c, "Statue Head", 0.0, 5.0, 1.5, 2.5, FLOOR_Z + 16.0, FLOOR_Z + 18.5, ("keep_rock", "wall"), role="visual")
        for side in (-1, 1):
            box(c, "Statue Wing %d" % side, side * 5.0, -0.5, 4.0, 0.4, FLOOR_Z + 9.0, FLOOR_Z + 14.0, ("keep_rock", "wall"),
                rot=side * 0.4, role="visual")
    # The harbour: quays either side of the Causeway's end, a lighthouse.
    for side in (-1, 1):
        box(c, "Quay %d" % side, side * (hr + 4.0), hy - 6.0, 4.0, 14.0, FLOOR_Z - 1.0, FLOOR_Z + 1.5, ("keep_ashlar", "wall"))
    box(c, "Lighthouse", hr + 10.0, hy - 20.0, 3.0, 3.0, FLOOR_Z - 1.0, FLOOR_Z + 22.0, ("keep_ashlar", "wall"))
    gx, gy, gz = c.game(hr + 10.0, hy - 20.0, FLOOR_Z + 24.0)
    c.entity("lantern", x=gx, y=gy, z=gz)

    # The landmarks.
    roof = ("keep_parapet", "wall")
    # Dragonspire Keep: a tall keep on a crag, its gate at the foot.
    x, y = polar(*KEEP)
    kx, ky = polar(KEEP[0], KEEP[1] + 30.0)
    c.assign(c.rock_mass("Keep Crag", kx, ky, 18.0, 14.0, FLOOR_Z + 14.0, z0=FLOOR_Z - 1.0, n=12, seed=4),
             c.lib("keep_rock", "wall"))
    gate(c, "Keep Gate", KEEP[0], KEEP[1] + 6.0, ("keep_ashlar", "wall"), towers=0.0)
    box(c, "Dragonspire", kx, ky, 5.0, 5.0, FLOOR_Z + 10.0, FLOOR_Z + (34.0 if RUIN else 58.0), ("keep_ashlar", "wall"))
    if not RUIN:
        cone(c, "Dragonspire Roof", kx, ky, 7.0, FLOOR_Z + 58.0, 14.0, roof, segs=4, role="visual")
    # Dragon Canyon: the jungle castle's gate in the east cliff, overgrown.
    gate(c, "Jungle Gate", CANYON[0], CANYON[1], ("limestone_moss", "wall"), towers=20.0, roof=("lush_grass", "wall"))
    # Emberdeep Hold: the fortress gate cut into the mountain.
    gate(c, "Hold Gate", HOLD[0], HOLD[1], ("fortress_wall", "wall"), height=16.0, towers=30.0)
    # The Moonstone Kingdom: a moon gate (a ring) among violet lanterns.
    mx, my = polar(*MOON)
    rot = math.radians(MOON[0]) + math.pi / 2
    for k in range(12):
        t = k * math.tau / 12
        bx, by = mx + 9.0 * math.cos(t) * math.cos(rot), my + 9.0 * math.cos(t) * math.sin(rot)
        z = FLOOR_Z + 9.0 + 9.0 * math.sin(t)
        if z < FLOOR_Z + 2.5 and abs(math.cos(t)) < 0.6:
            continue  # (the way through)
        box(c, "Moon Gate %d" % k, bx, by, 1.6, 1.2, z - 1.2, z + 1.2, ("limestone", "wall"), rot=rot,
            role="both" if z < FLOOR_Z + 6 else "visual")
    for k in range(6):
        lx, ly = polar(MOON[0] + (k - 2.5) * 6.0, MOON[1] - 22.0)
        box(c, "Moon Lantern Post %d" % k, lx, ly, 0.3, 0.3, FLOOR_Z - 1.0, FLOOR_Z + 4.0, ("weathered_timber", "wall"))
        gx, gy, gz = c.game(lx, ly, FLOOR_Z + 4.5)
        c.entity("lantern", x=gx, y=gy, z=gz)
    # King Pyrrhax's Citadel: a great gate with towers on the north cliff.
    gate(c, "Citadel Gate", CITADEL[0], CITADEL[1], ("keep_ashlar", "wall"), width=10.0, height=18.0,
         towers=26.0 if RUIN else 44.0, roof=None if RUIN else roof)
    cx, cy = polar(CITADEL[0], CITADEL[1] + 40.0)
    box(c, "Citadel Keep", cx, cy, 22.0, 14.0, RIM_Z - 10.0, RIM_Z + (25.0 if RUIN else 55.0), ("keep_ashlar", "wall"),
        rot=math.radians(CITADEL[0]) + math.pi / 2, role="visual")

    if RUIN:
        # After the sacrifice: a storm over the kingdom, scorched ground, smoke and rubble
        # at every gate.
        c.entity("storm", period=9, spread=5, distance=900)
        avoid = (0.0, 90.0, 180.0, -90.0, KEEP[0], CANYON[0], HOLD[0], MOON[0], CITADEL[0])
        burns = ruin.ring_spots(14, 60.0, 195.0, 21, avoid) + ruin.ring_spots(12, 255.0, 310.0, 22, avoid)
        ruin.scorch(c, "Scorch", burns, natural)
        for x, y in burns[::3]:
            ruin.smoke(c, x, y, natural(x, y) + 0.2)
        for name, (a, r) in (("Keep", KEEP), ("Canyon", CANYON), ("Hold", HOLD), ("Moon", MOON), ("Citadel", CITADEL)):
            for side in (-1, 1):
                x, y = polar(a + side * 6.0, r - 16.0)
                ruin.rubble(c, "%s Rubble %d" % (name, side), x, y, natural, ("keep_rock", "wall"), seed=int(a) + side)

    dress(c)

    # The Causeway's far end, back over the sea towards Tropic Isles: it fades into the
    # sea mist (a wall of rock closes the view).
    box(c, "Causeway Bend", 0.0, CAUSE_Y0 - 4, CAUSE_HW + 24.0, 6.0, FLOOR_Z - 2.0, RIM_Z, ("keep_rock", "wall"))

    c.start_line()
    gates = c.checkpoints(height=10.0)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish(extra={"race": {"laps": 1}})
    print("ring", round(c.length, 1), "gates", len(gates))


if __name__ == "__main__":
    main()
