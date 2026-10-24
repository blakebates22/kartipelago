# Dry Gulch Ghost Town v3: the GREYBOX of the new lap (Blake's notes, 2026-10-23).
# Driving first: the new lap, playable with plain shapes, so it can be driven and changed
# quickly; the haunted town's look comes back once the lap is fun. Builds its own
# package, dry_gulch_v3 (?track=dry_gulch_v3); the current Dry Gulch stays as it is.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/dry_gulch_v3.py      (the bpy module)
#
# About 1.77 km (the current lap is 2.14 km), nearly all of it bends:
#
#   A  Main Street and the saloon district: north up Main Street, a drift left at the
#      square, then a tight S-chicane drifting between the buildings.
#   B  Through the graveyard (not round it): over its knoll, flicking between the graves.
#   C  The mine approach, east along the top of town. The shortcut leaves into the mine.
#   D  The main way round: the Rickety Trestle over the glowing chasm (a broken span to
#      jump), south along the rim and down the ravine's wall in S-bends, a weave round
#      the rock pillars on the ravine floor, the hairpin round Dead Man's Rock, and up
#      out of the ravine in an S, drifting back onto Main Street.
#   The Haunted Mine (the shortcut): into the portal and down through winding tunnels,
#   a drop into the old workings, through the glowing cavern and out of the broken
#   gateway onto the ravine floor. About 90 m shorter than the way round (3-4 s).

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import Vector, bmesh, lerp, smooth  # noqa: E402

TRACK_ID = "dry_gulch_v3"

START = (0.0, 0.0)
LAYOUT = [
    ("S", 100),  # 0  A: Main Street, north
    ("L", 35, 90),  # 1  a drift left at the square
    ("S", 20),  # 2
    ("R", 30, 70),  # 3  the chicane between the buildings...
    ("L", 30, 140),  # 4
    ("R", 30, 70),  # 5
    ("S", 35),  # 6
    ("R", 35, 90),  # 7  B: into the graveyard
    ("S", 40),  # 8  over the knoll
    ("R", 30, 45),  # 9  between the graves
    ("L", 30, 45),  # 10
    ("R", 35, 90),  # 11 out of it, east
    ("S", 50),  # 12 C: the mine approach (the shortcut leaves here)
    ("L", 40, 30),  # 13
    ("R", 40, 30),  # 14
    ("S", 130),  # 15 (stretched to close the loop)
    ("S", 130),  # 16 D: the Rickety Trestle, with its broken span
    ("R", 40, 90),  # 17 south along the rim
    ("S", 40),  # 18 down the ravine's wall
    ("L", 40, 40),  # 19
    ("R", 40, 40),  # 20
    ("S", 60),  # 21
    ("S", 40),  # 22 the ravine floor (the mine comes back in here)
    ("R", 30, 50),  # 23 weaving round the rock pillars
    ("L", 30, 100),  # 24
    ("R", 30, 50),  # 25
    ("S", 30),  # 26
    ("S", 80),  # 27 (stretched to close the loop)
    ("R", 35, 180),  # 28 the hairpin round Dead Man's Rock
    ("L", 35, 90),  # 29 west, up out of the ravine
    ("S", 60),  # 30
    ("R", 30, 60),  # 31
    ("L", 30, 60),  # 32
    ("R", 40, 90),  # 33 drifting onto Main Street
    ("S", 40),  # 34
]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 15, 27, START, 90.0)
SEG = kit.segment_starts(PATH)
LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))
_D = [0.0]
for _a, _b in zip(PATH, PATH[1:]):
    _D.append(_D[-1] + math.hypot(_b[0] - _a[0], _b[1] - _a[1]))


def seg_of(s):
    k = 0
    for i, d in SEG.items():
        if d <= s:
            k = max(k, i)
    return k


def _seg_point(i):
    return next(p for p in PATH if p[3] == i)


def _arc_centre(i):
    x, y, h, _ = _seg_point(i)
    sg = LAYOUT[i]
    a = math.radians(h + (90 if sg[0] == "L" else -90))
    return (x + sg[1] * math.cos(a), y + sg[1] * math.sin(a))


Z_TOWN = 30.0
Z_TRESTLE = 32.0
# The broken span on the trestle: (lip, landing).
GAP = (SEG[16] + 62.0, SEG[16] + 72.0)
HEIGHT = {
    0: 30.0, 1: 30.0, 2: 30.0, 3: 30.0, 4: 30.0, 5: 30.0, 6: 30.0, 7: 30.0, 8: 30.5, 9: 31.0, 10: 31.0,
    11: 30.5, 12: 30.0, 13: 30.0, 14: 30.2, 15: 30.5, 16: Z_TRESTLE, 17: Z_TRESTLE, 18: 31.5, 19: 27.0,
    20: 23.0, 21: 19.0, 22: 13.0, 23: 12.5, 24: 12.2, 25: 12.0, 26: 11.8, 27: 11.6, 28: 12.0, 29: 12.5,
    30: 16.0, 31: 22.0, 32: 25.5, 33: 28.5, 34: 30.0,
}
# Rolling crests: segment: (how many, how high).
CRESTS = {8: (1, 2.4), 9: (1, 0.9), 10: (1, 0.9), 22: (1, 1.0), 26: (1, 1.2), 27: (2, 1.4), 30: (1, 1.0)}


def road_z(d, seg):
    if seg == 16:
        if GAP[0] <= d <= GAP[1]:
            return lerp(Z_TRESTLE + 0.6, Z_TRESTLE - 0.4, (d - GAP[0]) / (GAP[1] - GAP[0]))
        return Z_TRESTLE + (0.6 * smooth((d - (GAP[0] - 10)) / 10) if GAP[0] - 10 <= d < GAP[0] else 0.0) - (
            0.4 * (1 - smooth((d - GAP[1]) / 10)) if GAP[1] < d <= GAP[1] + 10 else 0.0)
    a, b = SEG[seg], SEG.get(seg + 1, LENGTH)
    t = (d - a) / max(1e-6, b - a)
    z0, z1 = HEIGHT[seg], HEIGHT.get(seg + 1, HEIGHT[0])
    z = lerp(z0, z1, smooth(t))
    if seg in CRESTS:
        n, h = CRESTS[seg]
        z += h * math.sin(t * math.pi * n) ** 2
    return z


def road_w(d, seg):
    if seg in (0, 34):
        return 18.0  # Main Street: room for the pack
    if 2 <= seg <= 6:
        return 14.0  # the narrow streets of the chicane
    if 7 <= seg <= 11:
        return 14.0  # the graveyard lane
    if seg == 16:
        return 13.0  # the trestle
    if 18 <= seg <= 21:
        return 14.0  # the ledge down the wall
    return 16.0


ROUTE = kit.route_points_by(PATH, road_z, every=8.0, width=road_w)

# ---------------------------------------------------------------- the land

# The ravine: (x, y, half-width, floor). Deep in the north (the chasm the trestle
# crosses), it runs south-east to the floor the road drives along, round Dead Man's
# Rock, and climbs west to the town's level south of town.
RAVINE = [
    (130.0, 710.0, 70.0, -30.0), (130.0, 340.0, 60.0, -28.0), (145.0, 298.0, 52.0, -26.0), (185.0, 225.0, 44.0, -18.0),
    (225.0, 160.0, 40.0, 4.0), (248.0, 106.0, 40.0, 10.5), (254.0, 10.0, 40.0, 11.0), (246.0, -100.0, 46.0, 11.5),
    (220.0, -155.0, 48.0, 12.0), (160.0, -140.0, 40.0, 16.0), (100.0, -115.0, 32.0, 23.0), (40.0, -95.0, 24.0, 30.0),
]
WALLW = 22.0


def _seg_d(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy + 1e-9)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy), t


def ravine_q(x, y):
    best = None
    for a, b in zip(RAVINE, RAVINE[1:]):
        d, t = _seg_d(x, y, a[0], a[1], b[0], b[1])
        if best is None or d < best[0]:
            best = (d, lerp(a[2], b[2], t), lerp(a[3], b[3], t))
    return best


def natural(x, y):
    h = Z_TOWN + 0.8 * math.sin(x / 53.0 + 0.4) * math.cos(y / 61.0) + 0.5 * math.sin((x + y) / 29.0)
    r = math.hypot(x - 20.0, (y - 80.0) * 0.8)
    h += 25.0 * smooth((r - 380.0) / 160.0)
    d, hw, floor = ravine_q(x, y)
    if d < hw and floor < h:
        u = (hw - d) / WALLW
        h = lerp(h, floor, smooth(min(1.0, u)))
    g = math.hypot(x - GRAVE[0], y - GRAVE[1])
    h += 3.0 * (1.0 - smooth((g - 10.0) / 30.0))
    return h


def classify(c, n, info):
    d, hw, floor = ravine_q(c.x, c.y)
    if c.z < 0.0 and d < hw:
        return ("gulch_chasm", "abyss")  # the glowing chasm: back past the broken span
    if n.z < 0.62:
        return ("mine_rock", "wall")
    if math.hypot(c.x - GRAVE[0], c.y - GRAVE[1]) < 42:
        return ("graveyard_earth", "dirt")
    if info["d"] < 10:
        return ("gulch_verge", "dirt")
    return ("gulch_sand", "loose_sand")


GRAVE = ((_seg_point(8)[0] + _seg_point(10)[0]) / 2 + 4.0, (_seg_point(8)[1] + _seg_point(11)[1]) / 2)
DEAD_MANS_ROCK = _arc_centre(28)

# Hazard Ridge: the mine is bored through it, between the mine approach and the ravine.
RIDGE = [(40.0, 50.0), (48.0, 160.0), (28.0, 250.0), (80.0, 262.0), (132.0, 248.0), (160.0, 215.0), (185.0, 160.0),
         (215.0, 105.0), (220.0, 50.0), (192.0, 16.0), (130.0, 6.0), (70.0, 20.0)]

# The Haunted Mine: off the approach, through the ridge, onto the ravine floor.
#   (x, y, z) waypoints; None z: on the road there.
MINE = [
    (-10.0, 298.0, None),  # (on the approach)
    (14.0, 284.0, 30.0),
    (38.0, 262.0, 29.4),  # the portal
    (62.0, 238.0, 28.4),  # winding down the tunnels...
    (64.0, 210.0, 27.4),
    (86.0, 192.0, 26.6),
    (112.0, 180.0, 26.0),  # the drop into the workings
    (128.0, 164.0, 20.5),
    (146.0, 138.0, 18.5),  # the glowing cavern
    (170.0, 122.0, 16.0),
    (196.0, 110.0, 14.0),
    (217.0, 98.0, 13.0),  # the broken gateway
    (238.0, 88.0, 12.8),
    (257.0, 74.0, None),  # (on the ravine floor)
]
CAVERN = (146.0, 138.0)


def catmull(pts, every=1.0):
    out = []
    n = len(pts)
    for i in range(n - 1):
        p0 = pts[max(0, i - 1)]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[min(n - 1, i + 2)]
        k = max(2, int(math.dist(p1[:2], p2[:2]) / every))
        for j in range(k):
            t = j / k
            out.append(tuple(0.5 * (2 * p1[c] + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t * t
                                    + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t ** 3) for c in range(3)))
    out.append(tuple(pts[-1][:3]))
    return out


def mine_line(c):
    pts = []
    for x, y, z in MINE:
        if z is None:
            smp, _ = c.nearest(x, y)
            x, y, z = smp.p.x, smp.p.y, smp.p.z
        pts.append((x, y, z))
    return catmull(pts, 2.0)


def main():
    import props  # noqa: E402

    c = kit.Course(TRACK_ID, "Dry Gulch Ghost Town (v3 greybox)", "dry_gulch")
    c.route(ROUTE, width=16.0, bank=7.0)
    verge = ("gulch_verge", "dirt")
    timber = ("mine_timber", "wall")
    c.kinds = {
        "street": {"mat": "gulch_road", "surface": "packed_dirt", "shoulder": 1.2, "shoulder_mat": ("board_walk", "road")},
        "trail": {"mat": "gulch_road", "surface": "packed_dirt", "shoulder": 1.6, "shoulder_mat": verge},
        "trestle": {"mat": "board_walk", "surface": "road", "shoulder": 0.5, "shoulder_mat": ("board_walk", "road"), "barrier": 1.1,
                    "barrier_mat": timber, "deck": 1.8, "deck_mat": timber, "ground": False},
        "ramp": {"mat": "board_walk", "surface": "road", "shoulder": 0.5, "shoulder_mat": ("board_walk", "road"), "barrier": 1.1,
                 "barrier_mat": timber, "deck": 1.8, "deck_mat": timber, "ground": False},
        "ledge": {"mat": "gulch_road", "surface": "packed_dirt", "shoulder": 1.0, "shoulder_mat": verge, "barrier": 1.0,
                  "barrier_mat": timber, "deck": 3.0, "deck_mat": ("mine_rock", "wall")},
    }

    def label(smp):
        s = smp.s
        seg = seg_of(s)
        if GAP[0] <= s <= GAP[1]:
            return "gap"
        if seg == 16 and GAP[0] - 10 <= s < GAP[0]:
            return "ramp"
        x, y = smp.p.x, smp.p.y
        d, hw, floor = ravine_q(x, y)
        if seg in (15, 16, 17) and d < hw - 4 and floor < smp.p.z - 6:
            return "trestle"
        if 18 <= seg <= 21:
            return "ledge"
        if seg <= 6 or seg >= 33:
            return "street"
        return "trail"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "ramp":
            specials.append((s0, s1, "ramp", {"lift": lambda u, n: 0.9 * max(0.0, (u - (n - 8)) / 8) ** 2}))
        elif k != "trail":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "trail", max_len=200.0))

    # The mine's floor: a road off the race line, through the ridge.
    line = mine_line(c)
    c.shortcut("Mine", [(x, y, z - 0.05) for x, y, z in line], "mine_floor", "packed_dirt", width=9.0, shoulder=0.6,
               shoulder_mat=("mine_floor", "packed_dirt"))

    X0, X1, Y0, Y1 = -420, 480, -360, 760
    c.terrain("Land", X0, X1, Y0, Y1, 6.0, natural, classify, near=10.0, fade=16.0, under=0.2)

    def under(x, y):
        return natural(x, y) - 0.4

    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 6.0, under, c.lib("gulch_sand", "loose_sand"))

    # Hazard Ridge, the mine bored through it, and a shaft of green light over the cavern.
    cx = sum(p[0] for p in RIDGE) / len(RIDGE)
    cy = sum(p[1] for p in RIDGE) / len(RIDGE)
    bm = bmesh.new()
    rings = []
    for z, k in ((0.0, 1.0), (Z_TOWN, 1.0), (52.0, 0.92), (66.0, 0.8), (70.0, 0.7)):
        rings.append([bm.verts.new((cx + (x - cx) * k, cy + (y - cy) * k, z)) for x, y in RIDGE])
    props.loft(bm, rings, cap_top=True, cap_bottom=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ridge = c.mesh_object("Hazard Ridge", bm, "Rocks")
    cut = bmesh.new()
    rr = []
    n = len(line)
    for i, (x, y, z) in enumerate(line):
        a = line[max(0, i - 1)]
        b = line[min(n - 1, i + 1)]
        t = Vector((b[0] - a[0], b[1] - a[1], 0)).normalized()
        r = Vector((t.y, -t.x, 0))
        p = Vector((x, y, z))
        rr.append([cut.verts.new(p + r * o + Vector((0, 0, dz))) for o, dz in ((-6.0, -0.6), (6.0, -0.6), (6.0, 6.5), (3.6, 10.0), (-3.6, 10.0), (-6.0, 6.5))])
    for lo, hi in zip(rr, rr[1:]):
        for k in range(6):
            cut.faces.new((lo[k], lo[(k + 1) % 6], hi[(k + 1) % 6], hi[k]))
    cut.faces.new(rr[0])
    cut.faces.new(list(reversed(rr[-1])))
    bmesh.ops.recalc_face_normals(cut, faces=cut.faces)
    props.loft(cut, [props.ring(cut, CAVERN, 16.0, 18.0, 12), props.ring(cut, CAVERN, 24.0, 90.0, 12)], cap_top=True, cap_bottom=True)
    cutter = c.mesh_object("Mine Cutter", cut, "Rocks", "visual")
    mod = ridge.modifiers.new("Mine", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
    mod.object = cutter
    kit.bpy.context.view_layer.objects.active = ridge
    kit.bpy.ops.object.modifier_apply(modifier=mod.name)
    kit.bpy.data.objects.remove(cutter)
    c.paint_rock(ridge, ("mine_rock", "wall"), ("gulch_talus", "loose_sand"))
    for i in range(8, len(line) - 8, 14):
        x, y, z = line[i]
        g = c.game(x, y, z + 5.5)
        c.entity("torch", x=g[0], y=g[1], z=g[2])

    # Dead Man's Rock, inside the hairpin, and the rock pillars the floor weaves round.
    rk = c.rock_mass("Dead Mans Rock", DEAD_MANS_ROCK[0], DEAD_MANS_ROCK[1], 18.0, 16.0, 46.0, z0=0.0, n=14, seed=3)
    c.paint_rock(rk, ("mine_rock", "wall"), ("gulch_talus", "loose_sand"))
    for i in (24,):
        px, py = _arc_centre(i)
        pl = c.rock_mass("Pillar %d" % i, px, py, 9.0, 8.0, 34.0, z0=0.0, n=10, seed=i)
        c.paint_rock(pl, ("mine_rock", "wall"), ("gulch_talus", "loose_sand"))
    for i in (23, 25):
        px, py = _arc_centre(i)
        pl = c.rock_mass("Pillar %d" % i, px, py, 7.0, 6.0, 28.0, z0=0.0, n=10, seed=i)
        c.paint_rock(pl, ("mine_rock", "wall"), ("gulch_talus", "loose_sand"))

    # The town: buildings crowding the streets (the chicane drifts right between them).
    bm = bmesh.new()
    s = 6.0
    k = 0
    while s < SEG[7]:
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 8.5))
            if all(math.hypot(p.x - o.p.x, p.y - o.p.y) > o.w / 2 + 7.5 for o in c.S[:: 6]):
                h = 7.0 + 3.0 * ((k + (side > 0)) % 3)
                props.cuboid(bm, (p.x, p.y, q.p.z + h / 2 - 0.5), (9.0, 8.0, h), rot=math.atan2(q.t.y, q.t.x))
        s += 12.0
        k += 1
    s = SEG[33]
    while s < LENGTH - 6:
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 8.5))
            if all(math.hypot(p.x - o.p.x, p.y - o.p.y) > o.w / 2 + 7.5 for o in c.S[:: 6]):
                props.cuboid(bm, (p.x, p.y, q.p.z + 4.0), (9.0, 8.0, 9.0), rot=math.atan2(q.t.y, q.t.x))
        s += 12.0
    town = c.mesh_object("Town", bm, "Props")
    c.assign(town, c.lib("siding_brown", "wall"))
    # The graveyard: headstones either side of the lane, close by.
    bm = bmesh.new()
    s = SEG[7] + 4
    k = 0
    while s < SEG[12]:
        q = c.at(s)
        for side in (-1, 1):
            for off in (q.w / 2 + 3.0, q.w / 2 + 7.0, q.w / 2 + 11.0):
                p = q.side(side * (off + (k % 2)))
                props.cuboid(bm, (p.x, p.y, c.ground_z(p.x, p.y, list(c.coll("Terrain").objects)) or q.p.z), (0.5, 1.4, 2.2), rot=math.atan2(q.t.y, q.t.x))
        s += 5.0
        k += 1
    stones = c.mesh_object("Graves", bm, "Props")
    c.assign(stones, c.lib("tombstone", "wall"))

    c.start_line()
    S = lambda i: SEG[i]  # noqa: E731
    # Zippers: up Main Street, out of the chicane, along the approach, onto the trestle
    # (for the broken span), down the wall, along the floor, and up out of the ravine.
    for at in (S(0) + 30, S(6) + 10, S(15) + 30, S(16) + 20, S(21) + 10, S(27) + 20, S(30) + 10):
        c.zipper(at, 0)
    for at, across in ((S(2) + 10, 0), (S(8) + 30, 0), (S(13) + 10, 0), (S(18) + 20, 0), (S(24) + 30, 0), (S(29) + 30, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (S(0) + 70, -4, "red"),
        (S(0) + 70, 4, "blue"),
        (S(4) + 40, 0, "green"),
        (S(12) + 20, 0, "yellow"),
        (S(17) + 30, 0, "rainbow"),
        (S(22) + 20, -4, "red"),
        (S(22) + 20, 4, "blue"),
        (S(31) + 10, 0, "green"),
    ):
        c.balloon(at, across, col)
    # The broken span: fall in and you're put back past it.
    c.entity("respawn", **{"from": round(GAP[0] - 20, 1), "to": round(GAP[1] + 4, 1), "at": round(GAP[1] + 20, 1)})

    # Checkpoints: one in the middle of the stretch the mine skips, with a twin gate in the
    # mine (either counts), and none elsewhere in that stretch.
    s_in = kit.s_near(c, *MINE[0][:2])
    s_out = kit.s_near(c, *MINE[-1][:2])
    apex = (s_in + s_out) / 2
    gates = c.checkpoints(
        extra=[S(1) + 20, S(4) + 30, S(8) + 20, S(11) + 30, s_in - 8, apex, s_out + 8, S(24) + 30, S(28) + 50, S(30) + 30],
        avoid=[(s_in - 4, apex - 8), (apex + 8, s_out + 4)],
        height=10.0,
    )
    main_gate = min(gates.items(), key=lambda kv: abs(kv[0] - apex))[1]
    mid = len(line) // 2
    c.alt_gate(main_gate, "haunted_mine", line[mid - 2 : mid + 2], width=12.0)

    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish()
    mine_len = sum(math.dist(a[:2], b[:2]) for a, b in zip(line, line[1:]))
    print("lap", round(c.length, 1), "mine", round(mine_len, 1), "skips", round(s_out - s_in, 1))


if __name__ == "__main__":
    main()
