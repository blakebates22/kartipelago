# Ember Peak: Prehistoric World, course 4. The complete redo (Blake, 2026-10-23): driven
# as a greybox first, then dressed as an open, smouldering volcanic field. (The previous
# Ember Peak, the long climb up the volcano, is ember_peak_v2.py: ?track=ember_peak_v2.)
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/ember_peak.py      (the bpy module)
#
# A short, fast lap (about 880 m, 30-odd seconds) across a volcanic field:
#
#   0  The start: east off a low basalt bridge over the lava river.
#   1  The big banked hairpin, climbing 15 m.
#   2  The cliff ledge, west, high above the start (a zipper).
#   3  THE BIG JUMP: up a straight stone ramp and over the same lava river, about
#      18 m across and 11 m down (the dragon swoops over you in the air).
#   4  The S-bends: a tight, deep drift chain down the obsidian slope.
#   5  The magma cave: through the volcano's flank.
#   6  The home run: flat out (a zipper), a fast kink, over the lava bridge to the line.
#
# Round it, open country: ash and cooled lava to the horizon, cinder cones, far
# volcanoes, the lava river winding across with three more feeding it, bubbling lava
# pits, burning and charred trees, obsidian spires and steam vents.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import Vector, lerp, smooth  # noqa: E402
from mathutils import kdtree  # noqa: E402

TRACK_ID = "ember_peak"
LAVA_Z = -1.5

LAYOUT = [
    ("S", 50),  # 0  the start straight, east
    ("L", 42, 180),  # 1  the big banked hairpin, climbing
    ("S", 30),  # 2  the cliff ledge, west (zipper)
    ("S", 24),  # 3  the ramp, with a kicker at the lip
    ("S", 18),  # 4  the gap: over the lava river
    ("S", 50),  # 5  the landing: a long downhill, so even a boosted jump lands on it
    ("R", 26, 70),  # 6  the S-bends: tight and deep, so you have to drift them
    ("L", 26, 140),  # 7
    ("R", 26, 140),  # 8
    ("L", 26, 70),  # 9
    ("L", 34, 90),  # 10 into the volcano: the magma cave, turning south
    ("S", 30),  # 11 the cave
    ("L", 34, 90),  # 12 turning east, out of the mountain
    ("S", 40),  # 13 the home run (closes)
    ("L", 160, 12),  # 14 a flat-out kink
    ("R", 160, 12),  # 15 and over the lava bridge to the line
]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 11, 13, (0.0, 0.0), 0.0)
SEG = kit.segment_starts(PATH)
LIP = SEG[4]
LAND = SEG[5]

# Heights at segment starts (the road eases between them; the ramp and the landing are
# straight slopes).
HEIGHT = [
    (0, 2.0),
    (1, 2.0),
    (2, 17.0),
    (3, 17.0),
    (4, 21.0),
    (5, 9.5),
    (6, 6.5),
    (7, 6.0),
    (8, 5.5),
    (9, 5.0),
    (10, 4.5),
    (11, 4.0),
    (12, 3.5),
    (13, 3.0),
    (14, 2.2),
    (15, 2.0),
]


def road_z(d, seg):
    if seg == 4:
        return lerp(21.0, 9.5, (d - LIP) / (LAND - LIP))
    for (s0, z0), (s1, z1) in zip(HEIGHT, HEIGHT[1:]):
        if s0 <= seg < s1:
            a, b = SEG[s0], SEG[s1]
            t = (d - a) / max(1e-6, b - a)
            if s0 == 3:
                # The ramp: eases in from the flat ledge, then a steady 11 degree slope
                # to a clean lip (v3.2: no kicker and no sudden change of slope, which
                # stopped some karts dead and fired others straight up).
                t0 = 0.35
                k = 1.0 / (1.0 - t0 / 2.0)
                f = k * t * t / (2 * t0) if t < t0 else k * (t - t0 / 2.0)
                return lerp(z0, z1, f)
            return lerp(z0, z1, t if s0 == 5 else smooth(t))
    end = HEIGHT[-1]
    t = (d - SEG[end[0]]) / max(1e-6, PATH_LEN - SEG[end[0]])
    return lerp(end[1], HEIGHT[0][1], smooth(t))


PATH_LEN = sum((Vector(b[:2]) - Vector(a[:2])).length for a, b in zip(PATH, PATH[1:]))


def road_w(d, seg):
    if seg == 5:
        return 24.0  # a wide landing: wherever you come down, you're on the road
    if seg == 3 and d > LIP - 14:
        return 18.0
    if seg in (13, 14, 15, 0):
        return 16.0  # the home run and the start: wide and fast
    return 14.0


ROUTE = kit.route_points_by(PATH, road_z, every=10.0, width=road_w)


# ---------------------------------------------------------------- the land


def _at(seg, f):
    pts = [p for p in PATH if p[3] == seg]
    return pts[min(len(pts) - 1, int(f * (len(pts) - 1)))]


_lip, _land = _at(4, 0.0), _at(4, 1.0)
GAP_X = (_lip[0] + _land[0]) / 2  # the river runs under the middle of the jump
LEDGE_Y = _lip[1]


def river_x(y):
    """The lava river's centre: north to south through the middle of the loop."""
    return GAP_X + 4.0 * math.sin((y - LEDGE_Y) / 19.0) + 1.5 * math.sin(y / 7.0)


RIVER_HALF = 7.0
RIVER_Y = (-70.0, 175.0)

# The volcano: a great cone west of the loop, its east flank holding the magma cave.
_cave = _at(11, 0.5)
VOLC = (_cave[0] - 58.0, _cave[1], 85.0, 70.0)  # centre x, y, radius x, y
VOLC_H = 115.0


def in_volcano(x, y, shrink=1.0):
    cx, cy, rx, ry = VOLC
    return ((x - cx) / (rx * shrink)) ** 2 + ((y - cy) / (ry * shrink)) ** 2 < 1


# Route samples every 4 m with their heights, for the land round the roads.
_samples = []
_d = 0.0
for _i, (_x, _y, _h, _s) in enumerate(PATH):
    if _i:
        _d += math.hypot(_x - PATH[_i - 1][0], _y - PATH[_i - 1][1])
    if not _samples or _d - _samples[-1][3] >= 4.0:
        _samples.append((_x, _y, road_z(_d, _s), _d))
_tree = kdtree.KDTree(len(_samples))
for _i, (_x, _y, _z, _dd) in enumerate(_samples):
    _tree.insert((_x, _y, 0.0), _i)
_tree.balance()

# v3.2, the look (Blake: "not just driving in a valley: more open, still a volcanic
# field"): the canyon walls are gone. The roads run over an open field of ash and
# black lava rock; the high stretches (the hairpin, the ledge, the ramp) ride on
# embankments that fall away to it; lava rivers wind across it, lava pits bubble in it,
# burning trees smoulder on it, and cinder cones and far volcanoes ring the horizon.
# The track itself is unchanged.


def field(x, y):
    """The open volcanic field: low rolling ash and lava-rock humps."""
    return 0.9 + 1.3 * math.sin(x / 31.0) * math.cos(y / 27.0) + 0.8 * math.sin((x + y) / 19.0) + 0.5 * math.sin(x / 9.0 - y / 13.0)


def embankment(x, y):
    """Under every road, a bank as high as the road, its sides falling away at about
    25 degrees, so the high stretches stand on ridges over the field."""
    best = None
    for (_, i, d) in _tree.find_range((x, y, 0.0), 70.0):
        z = _samples[i][2] - 0.47 * max(0.0, d - 11.0)
        best = z if best is None else max(best, z)
    return best


# Cinder cones round the field, well away from the road (x, y, foot radius, height).
CONES = [(330, 260, 110, 70), (-120, 380, 120, 60), (260, -260, 100, 55), (-420, -240, 110, 70), (-470, 170, 115, 85), (370, 20, 80, 45)]


def cones(x, y):
    h = None
    for cx, cy, r, ht in CONES:
        d = math.hypot(x - cx, y - cy)
        if d < r:
            z = ht * (1 - d / r) ** 1.5 - 8 * max(0.0, 1 - d / (r * 0.16))  # a crater on top
            h = z if h is None else max(h, z)
    return h


# The lava rivers: polylines (x, y) and half-widths. The first is the one you cross
# twice (under the start's bridge and under the jump), winding off across the field
# both ways; the others run away from the road.
RIVER_HALF = 7.0
RIVERS = [
    ([(river_x(y), y) for y in range(-320, 381, 10)], RIVER_HALF),
    ([(VOLC[0] + 25, VOLC[1] - 70), (VOLC[0] + 30, VOLC[1] - 120), (VOLC[0] + 5, VOLC[1] - 190), (VOLC[0] - 40, VOLC[1] - 260), (VOLC[0] - 110, VOLC[1] - 340), (VOLC[0] - 200, VOLC[1] - 400)], 6.0),
    ([(150, 70), (210, 45), (280, 60), (350, 110), (430, 130), (520, 190)], 6.5),
    ([(-170, 230), (-210, 290), (-200, 360), (-250, 430), (-320, 480)], 5.5),
]
RIVER_Y = (-320.0, 380.0)


def _seg_dist(px, py, pts):
    best = 1e9
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(px - ax - t * dx, py - ay - t * dy))
    return best


def river_dist(x, y):
    """(distance from the nearest lava river's centre, its half-width)."""
    best = (1e9, 1.0)
    for pts, hw in RIVERS:
        d = _seg_dist(x, y, pts)
        if d - hw < best[0] - best[1]:
            best = (d, hw)
    return best


def _far_from_road(x, y, m):
    _, _, d = _tree.find((x, y, 0.0))
    return d > m


# Lava pits: glowing, bubbling pools out in the field (x, y, radius).
PITS = [
    p
    for p in [(-120, 45, 8), (-55, 40, 6), (25, 45, 7), (125, -45, 9), (-160, -60, 8), (60, -60, 7), (-40, -70, 6), (150, 150, 9),
              (-100, 175, 8), (-330, -60, 9), (210, -120, 10), (-30, 160, 6), (-200, 60, 6), (110, 210, 8)]
    if _far_from_road(p[0], p[1], p[2] + 20) and river_dist(p[0], p[1])[0] > p[2] + 18 and not in_volcano(p[0], p[1], 1.15)
]


def natural(x, y):
    h = field(x, y)
    e = embankment(x, y)
    if e is not None:
        h = max(h, e)
    k = cones(x, y)
    if k is not None:
        h = max(h, k)
    # A raised rim round each lava pit, then down into it.
    for px, py, pr in PITS:
        d = math.hypot(x - px, y - py)
        if d < pr + 10:
            rim = h + 1.6 * math.sin(math.pi * max(0.0, min(1.0, (d - pr + 2) / 10)))
            h = lerp(rim, LAVA_Z - 2.0, smooth((pr + 1 - d) / 3.0)) if d < pr + 1 else rim
    d, hw = river_dist(x, y)
    if d < hw + 9.0:
        h = lerp(h, LAVA_Z - 2.5, smooth((hw + 9.0 - d) / 9.0))
    return h


def base_floor(x, y):
    return natural(x, y)


CAVE_S = [0.0, 0.0]


def classify(c, n, info):
    if in_volcano(c.x, c.y, 0.86):
        return None  # the volcano is its own rock
    smp = info["sample"]
    if CAVE_S[0] <= smp.s <= CAVE_S[1] and info["d"] < 16 and c.z > smp.p.z - 1.0 and in_volcano(c.x, c.y, 1.04):
        return None
    if n.z < 0.62:
        return ("ember_ash", "wall")
    if c.z < LAVA_Z + 0.6:
        return ("magma_rock", "wall")
    if river_dist(c.x, c.y)[0] < river_dist(c.x, c.y)[1] + 14 and info["d"] > 10:
        return ("obsidian", "wall") if c.z < 1.0 else ("lava_crust", "dirt")  # cooled lava along the rivers
    if info["d"] < 12:
        return ("scorched_ground", "dirt")
    return ("ash_soil", "sand")


# ---------------------------------------------------------------- the course


def main():
    c = kit.Course(TRACK_ID, "Ember Peak", "volcanic_apocalypse")
    c.route(ROUTE, width=14.0, bank=7.0)
    wall = ("basalt_block", "wall")
    c.kinds = {
        "path": {"mat": "basalt_road", "shoulder": 1.5, "shoulder_mat": ("scorched_ground", "dirt")},
        "ledge": {"mat": "basalt_road", "shoulder": 1.0, "shoulder_mat": ("scorched_ground", "dirt"), "barrier": 1.2, "barrier_mat": wall},
        "ramp": {
            "mat": "basalt_road",
            "surface": "road",
            "shoulder": 0.6,
            "shoulder_mat": ("basalt_block", "road"),
            "barrier": 1.2,
            "barrier_mat": wall,
            "deck": 6.0,
            "deck_mat": wall,
            "ground": False,
        },
        "landing": {"mat": "basalt_road", "surface": "road", "shoulder": 1.0, "shoulder_mat": ("basalt_block", "road"), "barrier": 1.4, "barrier_mat": wall},
        "cave": {"mat": "basalt_road", "surface": "road", "shoulder": 3.0, "shoulder_mat": ("cave_rock", "road")},
        "lowbridge": {
            "mat": "basalt_road",
            "surface": "road",
            "shoulder": 0.6,
            "shoulder_mat": ("basalt_block", "road"),
            "barrier": 1.1,
            "barrier_mat": wall,
            "deck": 2.4,
            "deck_mat": wall,
            "ground": False,
        },
    }

    def seg_of(s):
        k = 0
        for i, d in SEG.items():
            if d <= s:
                k = max(k, i)
        return k

    def label(smp):
        x, y, s = smp.p.x, smp.p.y, smp.s
        seg = seg_of(s)
        if LIP <= s <= LAND:
            return "gap"
        if seg == 3:
            return "ramp"
        if seg == 5:
            return "landing"
        if in_volcano(x, y, 0.98):
            return "cave"
        if seg in (13, 14, 15, 0) and abs(x - river_x(y)) < RIVER_HALF + 12:
            return "lowbridge"
        if seg in (1, 2):
            return "ledge"
        return "path"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "ramp":
            specials.append((s0, s1, "ramp"))
        elif k != "path":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "path"))

    inside = kit.crossings(c, lambda smp: in_volcano(smp.p.x, smp.p.y, 1.0), margin=0)
    t0, t1 = max(inside, key=lambda r: r[1] - r[0])
    CAVE_S[:] = [t0 - 16, t1 + 16]
    # The land near the road in fine detail, the open field beyond it coarser (it overlaps
    # under the fine land by a cell, a little lower, so there's never a crack between).
    X0, X1, Y0, Y1 = -560, 420, -340, 490
    I0, I1, J0, J1 = -360, 240, -150, 240
    c.terrain("Field", I0, I1, J0, J1, 3.0, natural, classify, near=8.5, fade=14.0)

    def far_natural(x, y):
        return natural(x, y) - 0.4

    def far_classify(c_, n, info):
        if I0 + 12 < c_.x < I1 - 12 and J0 + 12 < c_.y < J1 - 12:
            return None
        return classify(c_, n, info)

    c.terrain("Far Field", X0, X1, Y0, Y1, 12.0, far_natural, far_classify, near=8.5, fade=14.0)
    import cascade_review  # noqa: E402  (its bounds helpers)

    me = sys.modules[__name__]
    # (Flat squares, each at the lowest of its corners: always a floor, never a slope
    # steep enough to count as a wall, and always under the land as it's shaped.)
    c.underfloor_flat("Underfloor", I0, I1, J0, J1, 3.0, cascade_review.underfloor_height(c, me), c.lib("ash_soil", "sand"))
    # The lava: the rivers across the field (as wide as their beds are below the lava,
    # so there's no dry pit at their edges), and the pits.
    for k, (pts, hw) in enumerate(RIVERS):
        path = []
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(bx - ax, by - ay) / 4))
            for j in range(n):
                path.append((ax + (bx - ax) * j / n, ay + (by - ay) * j / n, 2 * hw + 12))
        path.append((pts[-1][0], pts[-1][1], 2 * hw + 12))
        c.ribbon("Lava River %d" % (k + 1), path, 2 * hw + 12, LAVA_Z, c.lib("volcano_lava", "lava"), steps=3)
    for k, (px, py, pr) in enumerate(PITS):
        c.disc("Lava Pit %d" % (k + 1), px, py, pr + 1.5, LAVA_Z, c.lib("volcano_lava", "lava"), n=18, wobble=0.18)
        g = c.game(px, py, LAVA_Z + 0.2)
        c.entity("bubbles", x=g[0], y=g[1], z=g[2], r=pr, molten=True)
    # Bubbles along the rivers too, here and there.
    for k, (pts, hw) in enumerate(RIVERS):
        for j in range(2, len(pts) - 1, 5):
            g = c.game(pts[j][0], pts[j][1], LAVA_Z + 0.2)
            c.entity("bubbles", x=g[0], y=g[1], z=g[2], r=hw * 0.8, molten=True)

    # The volcano, with the magma cave cut through its flank.
    cx, cy, rx, ry = VOLC
    rock = c.rock_mass("Volcano", cx, cy, rx, ry, VOLC_H, z0=-4.0, n=36, seed=5,
                       bands=[(1.0, 0.0), (1.0, 0.12), (0.86, 0.2), (0.7, 0.4), (0.5, 0.65), (0.3, 0.88), (0.2, 1.0)])
    c.tunnel(rock, t0, t1, half=c.width / 2 + 3.0, height=10.0, pad=14.0)
    c.paint_rock(rock, ("ember_ash", "wall"), ("magma_rock", "wall"), floor=("cave_rock", "road"), top_z=VOLC_H - 8, floor_z=14)
    c.disc("Crater Lava", cx, cy, rx * 0.17, VOLC_H + 0.3, c.lib("volcano_lava", "lava"), role="visual", n=20, wobble=0.15)
    floor = []
    s = t0 - 22
    while s <= t1 + 22:
        q = c.at(s)
        wide = in_volcano(q.p.x, q.p.y, 0.85)
        floor.append((q.p.x, q.p.y, 2 * (c.width / 2 + 3.0) + (14.0 if wide else 0.0), q.p.z - 0.25))
        s += 2.0
    c.ribbon("Cave Floor", floor, 26, 0, c.lib("cave_rock", "road"), coll="Collision", role="collision", steps=4)
    # Warm light pools down the cave, so it reads in the dark.
    lights = []
    s = t0 + 6
    k = 0
    while s < t1 - 4:
        q = c.at(s)
        side = 1 if k % 2 else -1
        lights.append(tuple(q.side(side * (c.width / 2 + 1.5), 5.5)))
        s += 10.0
        k += 1
    c.glow([rock], lights, 11.0, (1.4, 0.75, 0.35), base=0.45, region=lambda w: in_volcano(w.x, w.y, 1.0) and w.z < 30)
    for x, y, z in lights:
        gx, gy, gz = c.game(x, y, z)
        c.entity("torch", x=gx, y=gy, z=gz)

    dress(c, list(c.coll("Terrain").objects), rock)

    c.start_line()
    # Speed: one on the ledge so everyone reaches the ramp fast, one out of the cave and
    # one at the home run's kink, well apart so one boost is over before the next.
    # (None by the start: there's the start boost.)
    c.zipper(SEG[2] + 6, 0)
    c.zipper(SEG[13] - 2, 0)
    c.zipper(SEG[14] + 25, 0)
    for at, across in ((SEG[1] + 60, 0), (SEG[7] + 10, 0), (SEG[11] + 10, 0), (SEG[13] + 80, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in ((SEG[1] + 20, -3, "red"), (SEG[1] + 20, 3, "blue"), (SEG[6] + 8, 0, "green"), (SEG[10] + 20, 0, "yellow"), (SEG[13] + 30, 0, "rainbow")):
        c.balloon(at, across, col)
    # Missing the jump drops you in the lava: back out at the end of the landing.
    c.entity("respawn", **{"from": round(LIP - 30, 1), "to": round(LAND + 6, 1), "at": round(LAND + 30, 1)})
    c.checkpoints(extra=[SEG[1] + 40, SEG[2], LAND + 34, SEG[8], SEG[11], SEG[13] + 20], height=10.0)

    # The dragon: from beyond the valley. It circles high, then swoops in low across the
    # jump just as you're in the air, and climbs away over the volcano (scenery only).
    gx = GAP_X
    keys_b = [
        (0.0, cx, cy + 40, VOLC_H + 40),
        (SEG[1], 150.0, -60.0, 80.0),
        (SEG[2], 120.0, 150.0, 55.0),
        (LIP - 15, gx + 40, LEDGE_Y + 70, 38.0),
        ((LIP + LAND) / 2, gx, LEDGE_Y + 2, 29.0),
        (LAND + 30, gx - 30, LEDGE_Y - 70, 40.0),
        (SEG[9], -120.0, -60.0, 70.0),
        (SEG[12], cx - 40, cy - 60, VOLC_H + 20),
        (c.length - 1, cx, cy + 40, VOLC_H + 40),
    ]
    keys = []
    for s_, x, y, z in keys_b:
        g = c.game(x, y, z)
        keys.append([round(s_, 1), g[0], g[1], g[2]])
    c.entity("isles_dragon", keys=keys, length=round(c.length, 1), size=1.0, colors={"body": "#c8482a", "belly": "#ffcf6a"})

    print("edge rails:", cascade_review.edge_rails(c, me, list(c.coll("Terrain").objects) + [rock]))
    c.preset("sun", list(c.coll("Terrain").objects) + [rock], 0.35)
    kit.paint.shade_roads(c.pieces, 0.5)
    rep = c.finish()
    # The greybox's look: a sunset over ash (Blake's pick), written over the theme's.
    import json  # noqa: E402

    look_path = os.path.join(kit.TRACKS_DIR, TRACK_ID, "look.json")
    with open(look_path, encoding="utf-8") as f:
        look = json.load(f)
    look.update(LOOK)
    with open(look_path, "w", encoding="utf-8") as f:
        json.dump(look, f, indent=2)
        f.write("\n")
    print("lap", round(c.length, 1), "m;", rep.get("route_points"), "route points")


def dress(c, ter, rock):
    """The field's life: smouldering trees (some still burning, with smoke and embers
    curling off them), black obsidian spires, the volcano erupting, far volcanoes and
    cinder cones smoking on the horizon, and ash drifting down."""
    import props  # noqa: E402
    import volcano_props as vp  # noqa: E402

    cx, cy, rx, ry = VOLC

    def ok(m0, m1, zmax=12.0):
        def f(x, y, z):
            _, i, d = _tree.find((x, y, 0.0))
            if not (m0 < d < m1) or z > zmax or z < LAVA_Z + 1.0:
                return False
            rd, hw = river_dist(x, y)
            if rd < hw + 7:
                return False
            if any(math.hypot(x - px, y - py) < pr + 6 for px, py, pr in PITS):
                return False
            return not in_volcano(x, y, 1.12)

        return f

    area = (-620, 470, -430, 530)
    burning = [vp.burnt_pine(c, v, burning=True) for v in range(2)]
    charred = [vp.burnt_pine(c, v, burning=False) for v in range(2)]
    palms = [vp.burnt_palm(c, v) for v in range(2)]
    fires = []
    for v, t in enumerate(burning):
        fires += props.scatter(c, t, 14, area, ok(14, 160), ter, seed=500 + v, scale=(0.9, 1.3), sink=0.3)
    for v, t in enumerate(charred):
        props.scatter(c, t, 24, area, ok(12, 260), ter, seed=510 + v, scale=(0.8, 1.3), sink=0.3)
    for v, t in enumerate(palms):
        props.scatter(c, t, 14, area, ok(12, 200), ter, seed=520 + v, scale=(0.9, 1.4), sink=0.2)
    # Smoke and embers off the burning trees (the nearest few to the road).
    for k, (x, y) in enumerate(fires):
        if k % 2 == 0:
            z = c.ground_z(x, y, ter) or 1.0
            g = c.game(x, y, z + 0.5)
            c.entity("campfire", x=g[0], y=g[1], z=g[2])
    spires = [vp.obsidian_spire(c, v) for v in range(2)]
    for v, t in enumerate(spires):
        props.scatter(c, t, 6, area, ok(30, 260, zmax=20), ter, seed=530 + v, scale=(0.6, 1.1), sink=1.0, role="visual")
    # Steam vents out in the field.
    for k in range(10):
        a = k * 2.4
        x, y = -60 + 220 * math.cos(a) * (0.5 + 0.05 * k), 60 + 200 * math.sin(a) * (0.5 + 0.05 * k)
        z = c.ground_z(x, y, ter)
        if z is not None and ok(20, 300)(x, y, z):
            g = c.game(x, y, z)
            c.entity("steam", x=g[0], y=g[1], z=g[2])
    # The volcano erupts now and then, its smoke towering over the field.
    g = c.game(cx, cy, VOLC_H)
    c.entity("eruption", x=g[0], y=g[1], z=g[2], period=12.0, offset=2.0)
    c.place(vp.smoke_plume(c, 0, 140.0), cx, cy, VOLC_H - 2, rot=0.3, coll="Sky", role="visual")
    # The horizon: far volcanoes all round, smoking, and the cinder cones' smoke.
    for k in range(7):
        a = 0.4 + k * math.tau / 7
        r = 700 + 100 * math.sin(k * 1.7)
        sc = 1.4 + 0.5 * (k % 3) / 2
        x, y = -60 + r * math.cos(a), 50 + r * math.sin(a)
        c.place(vp.far_volcano(c, k % 2), x, y, -20, rot=a, scale=sc, coll="Sky", role="visual")
        if k % 2 == 0:
            c.place(vp.smoke_plume(c, 1, 120.0), x, y, 200 * sc - 30, rot=a, scale=sc * 0.8, coll="Sky", role="visual")
    for x, y, r, ht in CONES[:3]:
        c.place(vp.smoke_plume(c, 2, 60.0), x, y, ht - 6, rot=x, coll="Sky", role="visual")
    c.entity("ashfall", rate=40, radius=40)


LOOK = {
    "sky": "#d0806a",
    "fog": {"enabled": True, "color": "#b47866", "near": 220, "far": 1200},
    "sun": {"color": "#ffc896", "intensity": 2.6, "direction": [-0.72, 0.28, -0.62]},
    "ambient": {"sky": "#ffc0a8", "ground": "#4e3e3a", "intensity": 1.4},
    "skyDome": {
        "top": "#5c4466",
        "horizon": "#ffa070",
        "bottom": "#c27a68",
        "sun": {"color": "#fff2c8", "size": 15, "glow": "#ff9e60", "elevation": 5},
        "clouds": {"count": 40, "color": "#b47a70", "shade": "#5e3e48", "seed": 41, "low": 5, "high": 26, "drift": 0.004},
        "hills": {"color": "#4c3638", "far": "#9e6e66", "height": 10, "seed": 59, "layers": 2},
    },
}


if __name__ == "__main__":
    main()
