# Party Beach: the title screen's course. A dinosaur beach party.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/beach_party.py      (the bpy module)
#   blender --background --python tools/blender/prehistoric/beach_party.py
#
# A loop round a sunny bay. The start straight runs along the beach (white-gold sand,
# umbrellas, towels, surfboards and sandcastles between the road and a turquoise sea),
# swings up the east side past the tiki bar, wiggles along the dunes at the back
# (beach shacks and palms) and comes back down the west side past the bonfire. Inside
# the loop: a lagoon, a DJ stage with a dance floor of partying dinosaurs, a conga line
# round the bonfire, bunting and lanterns strung between the palms. Long-necks wade in
# the shallows and pterosaurs circle overhead.
#
# It isn't in any world (no track select): the title screen races on it (src/game/
# tracks.ts TITLE_TRACK). Saves tracks-src/beach_party.blend and exports
# public/tracks/beach_party/.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import beach_props as bp  # noqa: E402
import props  # noqa: E402
from course_kit import lerp, smooth  # noqa: E402

TRACK_ID = "beach_party"
WATER_Z = -0.5


def shore(x):
    """The waterline's y (the sea is south of it)."""
    return -105 + 10 * math.sin(x / 60) + 6 * math.sin(x / 23 + 1)


# The lagoon in the middle of the loop, the creek feeding it from the hills (under the
# back road) and the outlet to the sea (under the beach road).
LAGOON = (-80.0, 30.0, 30.0, 19.0)  # centre, radii
CREEK = [(-70, 44), (-58, 80), (-50, 114), (-46, 150), (-42, 200), (-38, 260)]
OUTLET = [(-86, 14), (-88, -20), (-90, -60), (-92, -98), (-94, -120)]


def seg_dist(px, py, pts):
    best = 1e9
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(px - ax - t * dx, py - ay - t * dy))
    return best


def lagoon_d(x, y):
    """Distance outside the lagoon's edge (negative inside), roughly in metres."""
    cx, cy, rx, ry = LAGOON
    e = math.hypot((x - cx) / rx, (y - cy) / ry)
    return (e - 1) * min(rx, ry)


def water_d(x, y):
    """Distance to the nearest fresh water's edge (lagoon, creek or outlet)."""
    return min(lagoon_d(x, y), seg_dist(x, y, CREEK) - 4.0, seg_dist(x, y, OUTLET) - 5.0)


# The loop, counter-clockwise from the start line on the beach.
START = (-120.0, -60.0)
LAYOUT = [
    ("S", 110),  # 0 the beach straight (stretched to close)
    ("L", 40, 90),  # 1 up the east side
    ("S", 40),  # 2 past the tiki bar
    ("R", 30, 35),  # 3 a flick right...
    ("L", 30, 35),  # 4 ...and back
    ("S", 20),  # 5
    ("L", 40, 90),  # 6 onto the back road
    ("S", 80),  # 7 the dunes (over the creek)
    ("R", 32, 40),  # 8 a wiggle...
    ("L", 32, 80),  # 9 ...through the palms
    ("S", 30),  # 10
    ("L", 40, 50),  # 11 down the west side
    ("S", 92),  # 12 past the bonfire (stretched to close)
    ("L", 40, 90),  # 13 back onto the beach
    ("S", 20),  # 14
]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 0, 12, START, 0.0)


def road_z(x, y):
    """Low on the beach, rising gently toward the dunes, humped over the two bridges."""
    z = 0.9 + 2.2 * smooth((y - 20) / 90)
    w = min(seg_dist(x, y, CREEK), seg_dist(x, y, OUTLET))
    return z + 1.3 * smooth((16 - w) / 12)


ROUTE = kit.route_points(PATH, road_z, every=12.0)


def natural(x, y):
    """The bay: a gentle shelf under the sea, the beach, rolling dunes, green hills at
    the back and rocky headlands at both ends; the lagoon and creeks cut in."""
    d = y - shore(x)
    if d < 0:
        h = max(-8.0, WATER_Z + d * 0.07)
    else:
        h = WATER_Z + 1.5 * smooth(d / 28) + 0.012 * max(0.0, d - 28)
        h += 0.7 * math.sin(x / 17) * math.sin(y / 13) * smooth((d - 50) / 30)
    # The hills behind the dunes, and the headlands.
    h += 26 * smooth((y - 165) / 80) * (0.8 + 0.2 * math.sin(x / 31))
    h += 20 * smooth((x - 120) / 60) * (0.85 + 0.15 * math.sin(y / 19))
    h += 22 * smooth((-x - 250) / 50) * (0.85 + 0.15 * math.sin(y / 23))
    # Fresh water: the lagoon and its creeks.
    w = water_d(x, y)
    if w < 10:
        h = lerp(h, -1.6, smooth((10 - w) / 9))
    return h


def classify(c, n, info):
    if n.z < 0.62:
        return ("valley_cliff", "wall")
    d = c.y - shore(c.x)
    if d < -1:
        return ("wet_sand", "deep_water")
    if water_d(c.x, c.y) < 1.5 or d < 4:
        return ("wet_sand", "sand")
    if c.z > 9:
        return ("canopy_bright" if math.sin(c.x / 11) * math.cos(c.y / 9) > 0.35 else "valley_grass", "grass")
    if d < 60 or water_d(c.x, c.y) < 9 or info["d"] < 9:
        return ("beach_sand", "sand")
    # Inside the loop and out to the dunes it's mostly sand, with tufts of dune grass;
    # further back the grass takes over.
    tuft = math.sin(c.x / 13 + c.y / 29) + 0.6 * math.sin(c.y / 7) + 0.5 * math.sin(c.x / 5)
    if d < 230:
        return ("valley_grass", "grass") if tuft > 1.35 else ("beach_sand", "sand")
    return ("beach_sand", "sand") if tuft > 1.2 else ("valley_grass", "grass")


def beach_ok(c, ter, m0=5.0, m1=60.0, wet=False):
    """Spots on the beach between the road and the sea."""

    def ok(x, y, z):
        d = y - shore(x)
        smp, dist = c.nearest(x, y)
        return (2 if wet else 6) < d < 40 and smp.w / 2 + m0 < dist < smp.w / 2 + m1 and water_d(x, y) > 3

    return ok


def land_ok(c, m0, m1, zmax=8.0, room=()):
    def ok(x, y, z):
        smp, dist = c.nearest(x, y)
        return (
            y - shore(x) > 20
            and z < zmax
            and water_d(x, y) > 4
            and smp.w / 2 + m0 < dist < smp.w / 2 + m1
            and all(math.hypot(x - tx, y - ty) > tr for tx, ty, tr in room)
        )

    return ok


def party(c, ter):
    """The party: the stage and dance floor, the bonfire and its conga line, the tiki
    bar, the beach stuff, torches, bunting and lanterns. Returns spots kept clear."""
    taken = []

    def place_at(proto, x, y, rot=0.0, scale=1.0, coll="Party", role="both", sink=0.05, r=3.0):
        z = c.ground_z(x, y, ter)
        if z is None:
            return None
        c.place(proto, x, y, z - sink, rot=rot, scale=scale, coll=coll, role=role)
        taken.append((x, y, r))
        return z

    def dancer(x, y, heading, variant, **extra):
        z = c.ground_z(x, y, ter)
        if z is None:
            return
        gx, gy, gz = c.game(x, y, z)
        c.entity("partygoer", x=round(gx, 2), y=round(gy, 2), z=round(gz, 2), heading=round(heading, 3), variant=variant, **extra)

    # The DJ stage, facing the dance floor and the lagoon, with dancers in front.
    sx, sy = -32.0, 72.0
    srot = 0.25
    sz = place_at(bp.stage(c), sx, sy, rot=srot, r=8.0)
    if sz is not None:
        # The DJ, up on the deck behind the booth, facing the crowd.
        dx, dy = sx + math.sin(srot) * 0.2, sy - math.cos(srot) * 0.2
        gx, gy, gz = c.game(dx, dy, sz + 0.95)
        c.entity("partygoer", x=round(gx, 2), y=round(gy, 2), z=round(gz, 2), heading=srot, variant=0, dance="dj")
    for k in range(9):
        a = -0.9 + 1.8 * k / 8
        r = 9 + 5 * kit.rnd(k * 3.1)
        x = sx + r * math.sin(a + srot)
        y = sy - r * math.cos(a + srot)
        heading = math.atan2(sx - x, -(sy - y))  # face the stage (game heading: atan2(dx, dz))
        dancer(x, y, heading, k % 6, dance=["bounce", "sway", "wave"][k % 3])
    for k in range(6):
        a = k * math.tau / 6
        place_at(bp.tiki_torch(c, k % 2), sx + 15 * math.cos(a), sy - 6 + 10 * math.sin(a), role="visual", r=1.0)

    # The bonfire, a conga line round it, drums and torches.
    fx, fy = -132.0, 40.0
    fz = place_at(props.campfire(c), fx, fy, role="visual", r=9.0)
    if fz is not None:
        gx, gy, gz = c.game(fx, fy, fz)
        c.entity("campfire", x=gx, y=gy, z=gz)
        c.entity("conga", x=round(gx, 2), y=round(gy, 2), z=round(gz, 2), radius=6.5, count=7, speed=1.4)
    for k in range(3):
        a = k * 2.2 + 0.5
        place_at(bp.drum(c), fx + 10 * math.cos(a), fy + 10 * math.sin(a), role="visual", r=1.0)
    for k in range(8):
        a = k * math.tau / 8
        place_at(bp.tiki_torch(c, k % 2), fx + 12.5 * math.cos(a), fy + 12.5 * math.sin(a), role="visual", r=1.0)

    # The tiki bar on the east side, regulars at the counter.
    tx, ty = 2.0, -8.0
    place_at(bp.tiki_bar(c), tx, ty, rot=-0.6, r=7.0)
    for k, off in enumerate((-1.5, 0.0, 1.5)):
        rot = -0.6
        x = tx + math.cos(rot) * off - math.sin(rot) * -2.8
        y = ty + math.sin(rot) * off + math.cos(rot) * -2.8
        dancer(x, y, math.atan2(-math.sin(rot), -math.cos(rot)), 3 + k, dance="chill")

    # The beach: umbrellas with towels and chairs under them, surfboards, beach balls,
    # sandcastles and canoes, a volleyball game, starfish and shells.
    ok = beach_ok(c, ter)
    umbrellas = [bp.umbrella(c, v) for v in range(5)]
    towels = [bp.towel(c, v) for v in range(3)]
    chairs = [bp.deck_chair(c, v) for v in range(2)]
    k = 0
    n = 0
    while n < 16 and k < 400:
        k += 1
        x = -200 + 290 * kit.rnd(k * 1.7 + 3)
        y = shore(x) + 10 + 22 * kit.rnd(k * 2.3 + 1)
        z = c.ground_z(x, y, ter)
        if z is None or not ok(x, y, z) or any(math.hypot(x - a, y - b) < r + 6 for a, b, r in taken):
            continue
        place_at(umbrellas[n % 5], x, y, rot=kit.rnd(k) * math.tau, role="visual", r=2.5, sink=0.0)
        a = kit.rnd(k * 5.1) * math.tau
        place_at(towels[n % 3], x + 1.8 * math.cos(a), y + 1.8 * math.sin(a), rot=a, role="visual", r=0.5, sink=0.0)
        if n % 2 == 0:
            place_at(chairs[n % 4 // 2], x - 1.6 * math.cos(a), y - 1.6 * math.sin(a), rot=math.pi / 2 + 0.3, role="visual", r=0.5, sink=0.0)
        if n % 3 == 0:
            dancer(x + 2.6 * math.cos(a + 1), y + 2.6 * math.sin(a + 1), kit.rnd(k * 9) * math.tau, (n + 2) % 6, dance="sway")
        n += 1
    for v in range(5):
        props.scatter(c, bp.surfboard(c, v), 3, (-200, 90, -110, -64), beach_ok(c, ter, 6, 50), ter, seed=500 + v, role="visual", sink=0.3, coll="Party")
    for v in range(3):
        props.scatter(c, bp.beach_ball(c, v), 3, (-200, 90, -110, -64), beach_ok(c, ter, 4, 50), ter, seed=510 + v, role="visual", sink=0.0, coll="Party")
    for v in range(3):
        props.scatter(c, bp.sandcastle(c, v), 3, (-200, 90, -112, -70), beach_ok(c, ter, 8, 60, wet=True), ter, seed=520 + v, role="visual", sink=0.1, coll="Party", scale=(0.9, 1.4))
    for v in range(2):
        props.scatter(c, bp.canoe(c, v), 2, (-200, 90, -112, -80), beach_ok(c, ter, 10, 60, wet=True), ter, seed=530 + v, role="visual", sink=0.15, coll="Party")
    for v in range(3):
        props.scatter(c, bp.starfish(c, v), 10, (-220, 110, -115, -70), beach_ok(c, ter, 3, 70, wet=True), ter, seed=540 + v, role="visual", sink=0.0, coll="Party", scale=(1.2, 2.0))
    props.scatter(c, bp.shell(c), 24, (-220, 110, -115, -70), beach_ok(c, ter, 3, 70, wet=True), ter, seed=550, role="visual", sink=0.0, coll="Party", scale=(1.0, 2.0))
    # Volleyball, east along the beach, with two players.
    vx, vy = 58.0, shore(58.0) + 16
    if place_at(bp.volley_net(c), vx, vy, rot=math.pi / 2 - 0.2, role="visual", r=6.0) is not None:
        dancer(vx - 4, vy - 0.8, math.pi / 2, 1, dance="hop")
        dancer(vx + 4, vy + 0.8, -math.pi / 2, 4, dance="hop")
        place_at(bp.beach_ball(c, 1), vx - 1.2, vy + 0.5, role="visual", r=0.5, sink=-1.9)

    # Tiki torches along the road, both sides.
    torches = [bp.tiki_torch(c, v) for v in range(2)]
    s = 6.0
    k = 0
    while s < c.length - 6:
        q = c.at(s)
        side = 1 if k % 2 else -1
        p = q.side(side * (q.w / 2 + 3.2))
        if water_d(p.x, p.y) > 2 and p.y - shore(p.x) > 6:
            place_at(torches[k % 2], p.x, p.y, role="visual", r=1.0)
        s += 16.0
        k += 1
    return taken


def palms_and_strings(c, ter, taken):
    """Coconut palms lining the beach road in pairs, with bunting strung across the road
    between them; palms everywhere else; lantern strings round the dance floor."""
    palms = [bp.coconut_palm(c, v) for v in range(3)]
    small = [props.palm(c, 8.0 + v * 1.5, 1.2 + v * 0.5, v) for v in range(2)]

    def clear(x, y, m=2.0):
        return all(math.hypot(x - tx, y - ty) > tr + m for tx, ty, tr in taken)

    pairs = 0
    s = 8.0
    while s < c.length:
        q = c.at(s)
        sides = []
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 5.5))
            z = c.ground_z(p.x, p.y, ter)
            if z is None or water_d(p.x, p.y) < 3 or p.y - shore(p.x) < 6 or not clear(p.x, p.y):
                sides = []
                break
            sides.append((p, z))
        if len(sides) == 2:
            # Lean the palms out from the road, so their crowns frame it.
            for (p, z), side in zip(sides, (-1, 1)):
                rot = math.atan2(q.r.y * side, q.r.x * side)
                c.place(palms[pairs % 3], p.x, p.y, z - 0.3, rot=rot, scale=0.95, coll="Palms")
                taken.append((p.x, p.y, 1.5))
            (a, za), (b, zb) = sides
            bp.string_line(c, "Bunting %02d" % (pairs + 1), (a.x, a.y, za + 7.8), (b.x, b.y, zb + 7.8), 1.6, "bunting" if pairs % 2 == 0 else "lanterns")
            pairs += 1
        s += 34.0

    def anywhere(m0, m1, zmax=30.0):
        def ok(x, y, z):
            smp, dist = c.nearest(x, y)
            return (y - shore(x) > 8 and z < zmax and water_d(x, y) > 3 and smp.w / 2 + m0 < dist < smp.w / 2 + m1 and clear(x, y))

        return ok

    for v, p in enumerate(palms):
        for x, y in props.scatter(c, p, 26, (-300, 200, -110, 240), anywhere(6, 140), ter, seed=600 + v, scale=(0.8, 1.25), coll="Palms"):
            taken.append((x, y, 1.5))
    for v, p in enumerate(small):
        props.scatter(c, p, 26, (-300, 200, -100, 260), anywhere(5, 160), ter, seed=610 + v, coll="Palms")
    # Palms round the lagoon's shore.
    for k in range(14):
        a = k * math.tau / 14 + 0.2
        cx, cy, rx, ry = LAGOON
        x, y = cx + (rx + 5) * math.cos(a), cy + (ry + 5) * math.sin(a)
        z = c.ground_z(x, y, ter)
        if z is not None and clear(x, y, 1.0) and props.clear_of_road(c, x, y, 4):
            c.place(palms[k % 3], x, y, z - 0.3, rot=a, scale=0.7 + 0.2 * kit.rnd(k), coll="Palms")
    # Lantern strings round the dance floor, from the stage to the lagoon palms.
    sx, sy = -32.0, 72.0
    for k, (a, b) in enumerate((((-40, 66), (-58, 52)), ((-24, 66), (-14, 48)), ((-58, 52), (-36, 44)), ((-36, 44), (-14, 48)))):
        za = (c.ground_z(*a, ter) or 0) + 6.0
        zb = (c.ground_z(*b, ter) or 0) + 6.0
        bp.string_line(c, "Lanterns %02d" % (k + 1), (a[0], a[1], za), (b[0], b[1], zb), 1.2, "lanterns")
        for x, y in (a, b):
            z = c.ground_z(x, y, ter)
            if z is not None:
                c.place(bp.bamboo_pole(c), x, y, z - 0.3, coll="Party", role="visual")


def scenery(c):
    ter = list(c.coll("Terrain").objects)
    for piece in c.pieces:
        if "bridge" in piece.name:
            props.piers(c, piece, every=7, mat=("palm_bark", "wall"), size=0.45, terrain=ter)
    taken = party(c, ter)
    palms_and_strings(c, ter, taken)
    # Beach shacks on the dunes behind the back road, and a lifeguard's hut on the sand.
    hut = props.hut(c)
    for i, (x, y) in enumerate(((-130, 150), (-95, 160), (-20, 150), (25, 140), (-200, 120), (70, 95))):
        z = c.ground_z(x, y, ter)
        if z is not None and props.clear_of_road(c, x, y, 8):
            c.place(hut, x, y, z - 0.1, rot=math.atan2(-60 - y, -60 - x) - math.pi / 2, scale=0.9, coll="Village")
    bushes = [props.bush(c, v) for v in range(2)]
    flowers = props.flowers(c)
    fern = props.fern(c, "palm_frond")
    grand = [props.grand_tree(c, v) for v in range(2)]

    def inland(m0, m1, zmin=-9, zmax=40):
        def ok(x, y, z):
            smp, dist = c.nearest(x, y)
            return y - shore(x) > 30 and zmin < z < zmax and water_d(x, y) > 3 and smp.w / 2 + m0 < dist < smp.w / 2 + m1

        return ok

    for v, t in enumerate(grand):
        props.scatter(c, t, 10, (-320, 240, 120, 320), inland(30, 300, 8), ter, seed=700 + v, scale=(1.1, 1.6))
    for v, b in enumerate(bushes):
        props.scatter(c, b, 60, (-300, 220, -60, 300), inland(4, 200), ter, seed=710 + v, role="visual", scale=(0.8, 1.6))
    props.scatter(c, flowers, 140, (-300, 220, -60, 300), inland(3, 160), ter, seed=720, role="visual", sink=0.1)
    props.scatter(c, fern, 90, (-300, 220, -60, 300), inland(3, 160), ter, seed=721, role="visual")
    # Sea stacks with palms on top, and a volcano island far out to sea.
    palm = bp.coconut_palm(c, 1)
    for i, (x, y, rx, h) in enumerate(((120, -165, 10, 18), (-240, -150, 12, 22), (40, -210, 7, 13), (-120, -230, 9, 15))):
        rock = c.rock_mass("Sea Stack %d" % (i + 1), x, y, rx, rx * 0.8, h, z0=-9, n=12, seed=31 + i * 4)
        c.paint_rock(rock, ("valley_cliff", "wall"), ("valley_grass", "grass"))
        c.place(palm, x, y, h - 0.6, rot=i * 1.4, scale=0.8, coll="Backdrop", role="visual")
    bm = kit.bmesh.new()
    rings = [props.ring(bm, (420, -900), r, z, 18) for r, z in ((260, -6), (180, 70), (80, 150), (55, 160))]
    props.loft(bm, rings)
    vol = c.mesh_object("Far Volcano", bm, "Backdrop", "visual")
    c.assign(vol, c.lib("valley_cliff"))
    vol.data.shade_flat()
    bm = kit.bmesh.new()
    rings = [props.ring(bm, (-650, -1100), r, z, 18) for r, z in ((300, -6), (220, 40), (120, 70), (40, 80))]
    props.loft(bm, rings)
    isle = c.mesh_object("Far Island", bm, "Backdrop", "visual")
    c.assign(isle, c.lib("canopy_bright"))
    isle.data.shade_flat()


def main():
    c = kit.Course(TRACK_ID, "Party Beach", "beach_party")
    c.route(ROUTE, width=14.0, bank=6.0)
    c.kinds = {
        "road": {"mat": "beach_road", "shoulder": 1.6, "shoulder_mat": ("beach_sand", "sand")},
        "bridge": {
            "mat": "wood_planks",
            "surface": "road",
            "shoulder": 0.4,
            "shoulder_mat": ("wood_planks", "road"),
            "barrier": 1.0,
            "barrier_mat": ("tiki_wood", "wall"),
            "deck": 1.2,
            "deck_mat": ("wood_planks", "wall"),
            "ground": False,
        },
    }
    wet = kit.crossings(c, lambda s: min(seg_dist(s.p.x, s.p.y, CREEK), seg_dist(s.p.x, s.p.y, OUTLET)) < 13, margin=3)
    c.roads(kit.plan(c, [(s0, s1, "bridge") for s0, s1 in wet], "road"))

    c.terrain("Bay", -360, 280, -250, 330, 3.3, natural, classify)
    # The sea, out to the horizon (scenery: nobody drives out there), with the surf
    # lapping along the shore.
    xs = list(range(-1600, -360, 200)) + list(range(-360, 281, 8)) + list(range(480, 1801, 200))
    W = 2600.0
    c.ribbon("Sea", [(x, shore(max(-360, min(280, x))) + 3 - W / 2) for x in xs], W, WATER_Z, c.lib("sea_water"), role="visual", steps=2)
    c.ribbon("Surf", [(x, shore(x) + 1.5) for x in range(-360, 281, 4)], 4.5, WATER_Z + 0.06, c.lib("surf_foam"), role="visual")
    c.ribbon("Surf Out", [(x, shore(x) - 7) for x in range(-360, 281, 4)], 2.5, WATER_Z + 0.05, c.lib("surf_foam"), role="visual")
    cx, cy, rx, ry = LAGOON
    c.ribbon("Lagoon", [(cx + rx * 1.08 * math.cos(a), cy, 2 * ry * 1.08 * abs(math.sin(a)) + 0.5) for a in [math.pi - k * math.pi / 24 for k in range(25)]], 1, WATER_Z + 0.1, c.lib("sea_water"), role="visual", steps=4)
    c.ribbon("Creek", [p + (10.0,) for p in CREEK], 10, WATER_Z + 0.1, c.lib("valley_water"), role="visual", steps=2)
    c.ribbon("Outlet", [p + (11.0,) for p in OUTLET], 11, WATER_Z + 0.08, c.lib("sea_water"), role="visual", steps=2)
    c.start_line()
    scenery(c)

    L = c.length
    # A few pickups so the demo racers have something to chase.
    c.zipper(L - 30, 0)
    c.zipper(kit.s_near(c, -20, 114), 2)
    for at, across in ((50, 0), (kit.s_near(c, 30, 20), -2), (kit.s_near(c, -120, 118), 0), (kit.s_near(c, -180, 0), 2)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in ((90, -4, "red"), (90, 4, "blue"), (kit.s_near(c, 39, 60), 0, "yellow"), (kit.s_near(c, -180, 50), -3, "green"), (kit.s_near(c, -150, -60), 0, "rainbow")):
        c.balloon(at, across, col)

    # Long-necks wading in the shallows (a big one and a youngster), and pterosaurs.
    wade = [(-60 + 95 * math.cos(a), -152 + 14 * math.sin(a)) for a in [k * math.tau / 20 for k in range(20)]]
    c.path_curve("Wade Path", wade)
    c.entity("dinosaur", route="Wade Path", speed=2.4, scale=1.0, start=0)
    c.entity("dinosaur", route="Wade Path", speed=2.4, scale=0.55, start=22)
    sky = [(-60 + 170 * math.cos(a), 20 + 120 * math.sin(a), 42 + 5 * math.sin(3 * a)) for a in [k * math.tau / 16 for k in range(16)]]
    c.path_curve("Flyer Path", sky)
    c.entity("pterosaur", route="Flyer Path", speed=13.0, scale=1.5)
    sky2 = [(-40 + 90 * math.cos(-a), -40 + 70 * math.sin(-a), 30 + 4 * math.sin(2 * a)) for a in [k * math.tau / 14 for k in range(14)]]
    c.path_curve("Flyer Path 2", sky2)
    c.entity("pterosaur", route="Flyer Path 2", speed=11.0, scale=1.0, start=60)

    c.checkpoints()
    c.preset("sun", [o for o in c.coll("Terrain").objects], 0.3)
    c.finish()


main()
