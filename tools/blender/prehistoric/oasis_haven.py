# Oasis Haven: Desert World, course 2. Havasu: turquoise pools and falls on the floor of
# a red-rock canyon, on a hot blue afternoon.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/oasis_haven.py      (the bpy module)
#
# v3, the Southwest (Blake, Oct 31: "the oasis rework to have it match the theme better",
# the desert's v4 overhaul: the open Southwest, mesas, the cliff pueblo, the rodeo): the
# lap Blake drove is kept bend for bend (about 1.56 km); round it, a side canyon of
# banded red sandstone, its walls stepping up in ledges, Havasu's turquoise water at its
# heart (the travertine-rimmed pool in the sweep, a creek in terraces under a timber
# bridge, and the falls off the canyon's south wall into their own plunge pool),
# cottonwoods along the water, and:
#
#   A  The village: the start among adobe homes (vigas, ladders, ristras, turquoise
#      doors) under a log ranch gate, an S-bend, and a long sweep south round the pool
#      over the creek's bridge, under the falls (or straight on through the cottonwood
#      grove on its north bank: the shortcut).
#   B  The camp: weaving north between the canvas tents and ramadas of the campground.
#   C  The butte: a hairpin round it, then west under the sandstone arch.
#   D  The slickrock: rolling swells over fast sweepers.
#   E  The watchtower: one and a quarter turns up round the old stone watchtower (the road
#      passes over itself), then the chute down to the start, with a jump over a dry wash.
#
# (v2, the Arabian oasis of mud brick and dunes, was oasis_desert.py's first dressing; the
# first version of all is kept as oasis_haven_v2.) Saves tracks-src/oasis_haven.blend and
# exports public/tracks/oasis_haven/. The scenery is oasis_desert.py.

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import ruin_mode  # noqa: E402
from course_kit import bmesh, lerp, smooth  # noqa: E402

# The ruin (oasis_ruins.py): the watchtower has toppled across its mesa and taken the
# spiral with it, so the lap climbs the fallen tower's rubble and jumps off its broken
# top down to the chute; the camp burned and its tents came down across the weave, so a
# scorched track swings out east over the dunes and back through the burnt camp; the
# arch's span has fallen across the road west of the butte. Everything else (the land,
# the landmarks) is the course's own.
RUIN = ruin_mode.ON
TRACK_ID = "oasis_haven_ruin" if RUIN else "oasis_haven"

START = (0.0, 0.0)
LAYOUT = [
    ("S", 60),  # 0  A: the start, south out of the village
    ("L", 35, 50),  # 1  an S-bend past the houses
    ("R", 35, 50),  # 2
    ("L", 40, 90),  # 3  east
    ("S", 40),  # 4  (the palm-grove shortcut leaves straight on from the end of this)
    ("R", 45, 75),  # 5  the long sweep south round the pool...
    ("L", 45, 150),  # 6
    ("R", 45, 75),  # 7  ...and back
    ("S", 30),  # 8  (the shortcut comes back in here)
    ("L", 35, 90),  # 9  north
    ("R", 30, 60),  # 10 B: weaving north through the camp
    ("L", 30, 120),  # 11
    ("R", 30, 60),  # 12
    ("S", 20),  # 13
    ("L", 30, 60),  # 14
    ("R", 30, 60),  # 15
    ("R", 35, 90),  # 16 C: out of the camp, east
    ("S", 20),  # 17
    ("L", 28, 180),  # 18 the hairpin round the butte
    ("S", 30),  # 19 west, under the arch
    ("S", 30),  # 20 D: the dune sea: crests...
    ("R", 45, 40),  # 21 ...over the sweepers
    ("L", 45, 80),  # 22
    ("R", 45, 40),  # 23
    ("S", 80),  # 24 two big crests (stretched to close the loop)
    ("L", 30, 450),  # 25 E: the spiral up round the watchtower
    ("R", 26, 50),  # 26 off the mesa, away from the tower
    ("S", 80),  # 27 the chute: the dune-lip jump (stretched to close the loop)
    ("L", 40, 50),  # 28 onto the start
]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 24, 27, START, 270.0)
SEG = kit.segment_starts(PATH)
LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))
# (The standard lap: the oasis's landmarks are laid out from it, in the ruin too.)
STD_LAYOUT, STD_PATH, STD_SEG, STD_LENGTH = LAYOUT, PATH, SEG, LENGTH

# The jump down the chute: (lip, landing). The chute eases off to a near-level kicker at
# the lip, a 14 m gap over a dry wash, and a long landing that runs on downhill.
LIP = SEG[27] + 45.0
LAND = LIP + 14.0
STD_LIP, STD_LAND = LIP, LAND

# Heights at segment starts; between them the road eases (the spiral climbs steadily).
HEIGHT = {
    0: 3.0, 1: 3.0, 2: 2.8, 3: 2.6, 4: 2.4, 5: 2.4, 6: 2.0, 7: 2.0, 8: 2.4, 9: 2.6,
    10: 3.0, 11: 3.4, 12: 3.8, 13: 4.2, 14: 4.6, 15: 5.0, 16: 5.6, 17: 6.5, 18: 7.0, 19: 8.0,
    20: 8.0, 21: 8.2, 22: 8.6, 23: 8.8, 24: 9.0, 25: 9.0, 26: 21.0, 27: 20.0, 28: 4.0,
}
# Rolling crests: (segment, how many, how high).
CRESTS = {4: (1, 1.2), 8: (1, 1.0), 19: (1, 1.4), 20: (1, 1.8), 21: (1, 1.2), 22: (2, 1.4), 23: (1, 1.2), 24: (2, 2.0)}


def seg_of(s):
    k = 0
    for i, d in SEG.items():
        if d <= s:
            k = max(k, i)
    return k


def _chute(d):
    a, b = SEG[27], SEG[28]
    if d <= LIP - 12:
        return lerp(HEIGHT[27], 15.0, smooth((d - a) / (LIP - 12 - a)))
    if d <= LIP:
        return lerp(15.0, 14.6, (d - (LIP - 12)) / 12)
    if d <= LAND:
        return lerp(14.6, 10.0, (d - LIP) / (LAND - LIP))
    return lerp(10.0, HEIGHT[28], (d - LAND) / (b - LAND))


def road_z(d, seg):
    if RUIN:
        return _ruin_z(d, seg)
    if seg == 27:
        return _chute(d)
    a, b = SEG[seg], SEG.get(seg + 1, LENGTH)
    t = (d - a) / max(1e-6, b - a)
    z0, z1 = HEIGHT[seg], HEIGHT.get(seg + 1, HEIGHT[0])
    z = lerp(z0, z1, t if seg == 25 else smooth(t))
    if seg in CRESTS:
        n, h = CRESTS[seg]
        z += h * math.sin(t * math.pi * n) ** 2
    return z


def road_w(d, seg):
    if RUIN:
        if seg in (0, 1, 2, 3, 27):
            return 16.0  # the village street
        return 17.0 if seg == 26 else 15.0
    if seg in (0, 1, 2, 3, 28):
        return 16.0  # the village street
    if seg == 25:
        return 14.0  # the spiral
    if seg == 27:
        return 17.0  # the chute
    return 15.0


def _seg_point(i):
    return next(p for p in STD_PATH if p[3] == i)


def _arc_centre(i):
    x, y, h, _ = _seg_point(i)
    sg = STD_LAYOUT[i]
    a = math.radians(h + (90 if sg[0] == "L" else -90))
    return (x + sg[1] * math.cos(a), y + sg[1] * math.sin(a))


_D = [0.0]
for _a, _b in zip(STD_PATH, STD_PATH[1:]):
    _D.append(_D[-1] + math.hypot(_b[0] - _a[0], _b[1] - _a[1]))
WASH = [(p[0], p[1]) for p, d in zip(STD_PATH, _D) if STD_LIP - 2 <= d <= STD_LAND + 2][::2]
# The landing's embankment: the land beside the road past the wash built up to it (v3: the
# canyon floor lies lower than the dunes did).
LANDING = [(p[0], p[1], _chute(d)) for p, d in zip(STD_PATH, _D) if STD_LAND <= d <= STD_LAND + 34][::2]

BUTTE = _arc_centre(18)
TOWER = _arc_centre(25)
_c6 = _arc_centre(6)
POOL = (_c6[0], _c6[1] - 8.0, 19.0)  # centre and radius: inside the sweep south
# Havasu's falls: off the canyon's south wall (out past the sweep) into their plunge pool,
# and the creek from it north in terraces, under the road's bridge, into the pool.
FALLS = (POOL[0], POOL[1] - 89.0, 18.0)  # the plunge pool: centre, radius
ALCOVE = FALLS[2] + 8.0  # the amphitheatre the falls have cut back into the wall
CREEK = [(FALLS[0], FALLS[1] + FALLS[2] - 2.0), (FALLS[0] + 3.0, (FALLS[1] + POOL[1]) / 2), (POOL[0], POOL[1] - POOL[2] + 2.0)]
CREEK_HW = 6.0

# The palm-grove shortcut: from the end of the street east (seg 4) straight on along the
# pool's north bank, between the palms, back onto the road at seg 8.
_p4, _p8 = _seg_point(5), _seg_point(8)
SHORTCUT = [(_p4[0] - 6.0, _p4[1]), (_p4[0] + 30.0, _p4[1] + 3.0), ((_p4[0] + _p8[0]) / 2, _p4[1] + 5.0),
            (_p8[0] - 30.0, _p8[1] + 3.0), (_p8[0] + 6.0, _p8[1])]

# ---------------------------------------------------------------- the ruin's lap

TGAP = []  # the ruin: [(x, y)] over the gap off the fallen tower's top
HUMPS = []  # the ruin: [(at, height, length)]: the road over the fallen arch's span
# The ruin's lap (laid out in both: the land is shaped round both laps).
# The course's own lap round the pool (0-9); then, where the camp's tents came down
# across the weave, the dragon's scorched track out east over the dunes (10-11), a
# wide hairpin back (12) and west through the burnt camp (13-15) onto the course's
# own road out to the butte, under the fallen arch and over the dune sea (16-23);
# then up the fallen tower's rubble (24-26), off its broken top, down the chute and
# over the wash, and onto the start (27).
R_LAYOUT = STD_LAYOUT[:10] + [
    ("R", 45, 90),  # 10 out of the old camp, east along the scorch
    ("S", 48),  # 11
    ("L", 41, 180),  # 12 the wide hairpin back...
    ("S", 83),  # 13 ...west, through the burnt camp
    ("R", 40, 90),  # 14 north
    ("S", 8.9),  # 15 onto the course's own road
] + list(STD_LAYOUT[16:24]) + [
    ("S", 16),  # 24 off the dune sea (closes the loop)
    ("L", 60, 40),  # 25 onto the rubble, climbing
    ("S", 160),  # 26 up the fallen tower, the jump, the chute, the wash (closes the loop)
    ("L", 40, 50),  # 27 onto the start
]
R_LAYOUT, R_PATH = kit.close_turtle(R_LAYOUT, 24, 26, START, 270.0)
if RUIN:
    LAYOUT, PATH = R_LAYOUT, R_PATH
    SEG = kit.segment_starts(PATH)
    LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))
    # The jump off the fallen tower's broken top (12 m, down onto the chute), and the
    # chute's own jump over the wash, where it always was.
    TLIP = SEG[26] + 38.0
    TLAND = TLIP + 12.0
    LIP = SEG[27] - (STD_SEG[28] - STD_LIP)
    LAND = LIP + 14.0
    HEIGHT = {k: v for k, v in HEIGHT.items() if k < len(LAYOUT)}
    HEIGHT.update({10: 3.0, 11: 3.4, 12: 3.8, 13: 4.4, 14: 5.0, 15: 5.4, 24: 9.0, 25: 11.0, 26: 15.0, 27: 4.0})
    CRESTS = {k: v for k, v in CRESTS.items() if k < 24}
    CRESTS.update({11: (1, 1.2), 13: (2, 1.4)})
    HUMPS = [(SEG[19] + 20.0, 2.4, 16.0)]
    _d = 0.0
    for _i, (_x, _y, _h, _sg) in enumerate(PATH):
        if _i:
            _d += math.hypot(_x - PATH[_i - 1][0], _y - PATH[_i - 1][1])
        if TLIP - 2 <= _d <= TLAND + 2:
            TGAP.append((_x, _y))


def _ruin_z(d, seg):
    """The ruin's road: the climb up the rubble onto the fallen tower (from the dune sea's
    end), the jump off its top, then the chute as it always was."""
    if seg >= 24 and d <= TLIP:
        a = SEG[24]
        if d <= TLIP - 12:
            return lerp(HEIGHT[24], 20.5, smooth((d - a) / (TLIP - 12 - a)))
        return lerp(20.5, 20.8, (d - (TLIP - 12)) / 12)
    if seg >= 26:
        if d <= TLAND:
            return lerp(20.8, 16.5, (d - TLIP) / (TLAND - TLIP))
        if d <= LIP - 12:
            return lerp(16.5, 15.0, smooth((d - TLAND) / (LIP - 12 - TLAND)))
        if d <= LIP:
            return lerp(15.0, 14.6, (d - (LIP - 12)) / 12)
        if d <= LAND:
            return lerp(14.6, 10.0, (d - LIP) / (LAND - LIP))
        return lerp(10.0, HEIGHT[27], smooth((d - LAND) / (SEG[27] - LAND)))
    a, b = SEG[seg], SEG.get(seg + 1, LENGTH)
    t = (d - a) / max(1e-6, b - a)
    z = lerp(HEIGHT[seg], HEIGHT.get(seg + 1, HEIGHT[0]), smooth(t))
    if seg in CRESTS:
        n, h = CRESTS[seg]
        z += h * math.sin(t * math.pi * n) ** 2
    for at, h, ln in HUMPS:
        if abs(d - at) < ln / 2:
            z += h * math.cos(math.pi * (d - at) / ln) ** 2
    return z


ROUTE = kit.route_points_by(PATH, road_z, every=10.0, width=road_w)


def _seg_d(x, y, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(x - ax - t * dx, y - ay - t * dy)


def creek_d(x, y):
    return min(_seg_d(x, y, a, b) for a, b in zip(CREEK, CREEK[1:]))


# How far each spot is from either lap (the canyon's walls stand back from both): a field
# on a 4 m grid, read bilinearly.
X0, X1, Y0, Y1 = -260, 620, -440, 420


def _road_field(cell=4.0):
    import numpy as np

    pts = np.array([(p[0], p[1]) for p in (STD_PATH[::3] + R_PATH[::3])])
    xs = np.arange(X0, X1 + cell, cell)
    ys = np.arange(Y0, Y1 + cell, cell)
    gx, gy = np.meshgrid(xs, ys, indexing="ij")
    flat = np.stack([gx.ravel(), gy.ravel()], 1)
    out = np.empty(len(flat))
    for k in range(0, len(flat), 4000):
        d = flat[k:k + 4000, None, :] - pts[None, :, :]
        out[k:k + 4000] = np.sqrt((d ** 2).sum(-1)).min(1)
    return out.reshape(gx.shape), cell


_FIELD, _CELL = _road_field()


def road_d(x, y):
    i = (x - X0) / _CELL
    j = (y - Y0) / _CELL
    nx, ny = _FIELD.shape
    i = max(0.0, min(nx - 1.001, i))
    j = max(0.0, min(ny - 1.001, j))
    i0, j0 = int(i), int(j)
    u, v = i - i0, j - j0
    f = _FIELD
    return float(lerp(lerp(f[i0, j0], f[i0 + 1, j0], u), lerp(f[i0, j0 + 1], f[i0 + 1, j0 + 1], u), v))


def wall_h(x, y):
    """The canyon's walls: three cliffs stepping back in ledges from the floor, their
    edges wandering (alcoves and buttresses), cut back round the falls' amphitheatre."""
    dd = road_d(x, y) + 7.0 * math.sin(x / 31.0 + 0.7 * math.sin(y / 17.0)) + 4.0 * math.cos(y / 23.0 - x / 41.0)
    # (the ledges' widths and the cliffs' heights wander too, slowly, round the canyon)
    a = math.atan2(y - 0.0, x - 190.0)
    w1 = 38.0 + 14.0 * math.sin(a * 3.0 + 0.8) + 6.0 * math.sin(a * 7.0)
    w2 = 46.0 + 18.0 * math.sin(a * 2.0 + 2.1)
    h1 = 30.0 + 7.0 * math.sin(a * 4.0 + 1.3)
    h2 = 22.0 + 8.0 * math.sin(a * 5.0 + 0.2)
    h = h1 * smooth((dd - 58.0) / 5.0) + h2 * smooth((dd - 58.0 - w1) / 6.0) + 34.0 * smooth((dd - 58.0 - w1 - w2) / 8.0)
    df = math.hypot(x - FALLS[0], y - FALLS[1])
    return h * smooth((df - ALCOVE) / 4.0)


def natural(x, y):
    """The canyon floor: low slickrock swells and red sand, rising a little to the north;
    the pool's basin, the plunge pool's and the creek's; the canyon's walls all round."""
    u = 0.5 + 0.5 * math.sin(x / 23.0 + 1.3 * math.sin(y / 41.0))
    h = 2.0 + 2.2 * u ** 3 + 0.9 * math.sin(y / 23.0 + x / 53.0) + 0.4 * math.sin(x / 7.3) * math.cos(y / 9.1)
    h += 6.0 * smooth((y - 60.0) / 90.0)
    dp = math.hypot(x - POOL[0], y - POOL[1])
    h = lerp(h, -1.6, smooth((POOL[2] + 10.0 - dp) / 12.0))
    df = math.hypot(x - FALLS[0], y - FALLS[1])
    h = lerp(h, -2.0, smooth((FALLS[2] + 6.0 - df) / 8.0))
    h = lerp(h, -1.0, smooth((CREEK_HW + 4.0 - creek_d(x, y)) / 5.0))
    if WASH:
        dw = min(math.hypot(x - p[0], y - p[1]) for p in WASH)
        h = lerp(h, 1.0, smooth((22.0 - dw) / 10.0))
        dl, zl = min((math.hypot(x - p[0], y - p[1]), p[2]) for p in LANDING)
        if dl < 20.0 and dl < dw + 1.0:
            # (only beside the road past the gap: the wash under the jump stays open)
            h = lerp(h, max(h, zl - 0.4), smooth((20.0 - dl) / 9.0) * smooth((dw + 1.0 - dl) / 4.0))
    if TGAP:
        # The pit the tower's top came down in: rubble far below the jump.
        dg = min(math.hypot(x - p[0], y - p[1]) for p in TGAP)
        h = lerp(h, 4.0, smooth((16.0 - dg) / 8.0))
    return h + wall_h(x, y)


def in_wash(x, y, z):
    """In the dry wash under the chute's jump (fall in and you're put back past it), or
    (the ruin) the pit under the fallen tower's top."""
    if TGAP and z < 12.0 and any(math.hypot(x - p[0], y - p[1]) < 14.0 for p in TGAP):
        return True
    return any(math.hypot(x - p[0], y - p[1]) < 16.0 for p in WASH) and z < 8.0


BANDS = (9.0, 30.0, 38.0, 64.0)  # where the rock changes, foot to rim


def layer(z):
    """The canyon's rock in bands, foot to rim: red shale, red and orange sandstone in
    alternating beds, the cream caprock."""
    if z < 9.0:
        return "strata_rust"
    if z < 30.0:
        return "strata_red"
    if z < 38.0:
        return "strata_orange"
    if z < 64.0:
        return "strata_red"
    return "strata_cream"


def in_water(x, y):
    return (math.hypot(x - POOL[0], y - POOL[1]) < POOL[2] + 5 or math.hypot(x - FALLS[0], y - FALLS[1]) < FALLS[2] + 4
            or creek_d(x, y) < CREEK_HW + 1.5)


def classify(c, n, info):
    if in_wash(c.x, c.y, c.z):
        return ("red_sand", "abyss")
    if n.z < 0.62:
        return (layer(c.z), "wall")
    if c.z < 0.6 and in_water(c.x, c.y):
        return ("sinter", "water")  # the travertine under the water
    if c.z > 14.0:
        return ("slickrock" if n.z > 0.9 else "talus", "dirt")  # the ledges up the walls
    if n.z < 0.85:
        return ("talus", "dirt")
    near_water = min(math.hypot(c.x - POOL[0], c.y - POOL[1]) - POOL[2], math.hypot(c.x - FALLS[0], c.y - FALLS[1]) - FALLS[2],
                     creek_d(c.x, c.y) - CREEK_HW)
    if near_water < 5.0:
        return ("sinter", "dirt")  # the travertine banks
    if near_water < 18.0:
        return ("oasis_lawn", "grass")
    if RUIN and info["d"] < 13 and 10 <= seg_of(info["sample"].s) <= 15:
        return ("ruin_ash", "dirt")  # the dragon's scorch across the slickrock
    if RUIN and info["d"] < 16 and SEG[24] <= info["sample"].s <= SEG[26] + 10:
        return ("ruin_rubble", "dirt")  # the spiral's fallen decks, heaped
    if info["d"] < 11:
        return ("pale_sand", "dirt")
    if c.z > 4.6 and n.z < 0.985:
        return ("slickrock", "dirt")  # the swells
    v = math.sin(c.x / 29.0) * math.cos(c.y / 31.0) + 0.3 * math.sin(c.x / 11.0 + c.y / 13.0)
    return ("red_sand" if v < -0.25 else "desert_sand", "loose_sand")


def on_bridge(smp):
    """Where the road crosses Havasu Creek."""
    return creek_d(smp.p.x, smp.p.y) < CREEK_HW + 5.0


def box(bm, centre, size, rot=0.0):
    import props  # noqa: E402

    props.cuboid(bm, centre, size, rot=rot)


WATER_Z = (0.0, 0.7, 1.4)  # the pool's, the creek's and the plunge pool's surfaces


def water(c):
    """Havasu's water, turquoise over travertine: the pool in the sweep, the creek down to
    it in two terraces (each held by a travertine rim), the plunge pool under the falls."""
    zp, zc, zf = WATER_Z
    c.disc("Pool", POOL[0], POOL[1], POOL[2] + 4.0, zp, c.lib("lagoon", "deep_water"), n=40, wobble=0.08, seed=3)
    c.disc("Plunge Pool", FALLS[0], FALLS[1], FALLS[2] + 3.0, zf, c.lib("lagoon", "deep_water"), n=40, wobble=0.1, seed=4)
    strip = []
    for (ax, ay), (bx, by) in zip(CREEK, CREEK[1:]):
        n = max(1, int(math.hypot(bx - ax, by - ay) / 4))
        for k in range(n):
            t = k / n
            strip.append((lerp(ax, bx, t), lerp(ay, by, t), CREEK_HW * 2 + 1.0, lerp(zf, zp, smooth((CREEK[0][1] - lerp(ay, by, t)) / (CREEK[0][1] - CREEK[-1][1])))))
    strip.append((CREEK[-1][0], CREEK[-1][1], CREEK_HW * 2 + 1.0, zp))
    c.ribbon("Havasu Creek", strip, CREEK_HW * 2 + 1.0, 0, c.lib("lagoon_shallow", "water"), steps=2)


def main():
    import props  # noqa: E402

    c = kit.Course(TRACK_ID, "Oasis Haven (Ruined)" if RUIN else "Oasis Haven", "oasis_ruins" if RUIN else "oasis_haven")
    c.route(ROUTE, width=15.0, bank=7.0)
    wall = ("adobe", "wall")
    c.kinds = {
        "street": {"mat": "oasis_paving", "shoulder": 1.4, "shoulder_mat": ("adobe_dark", "road"), "barrier": 0.8, "barrier_mat": wall},
        "trail": {"mat": "dash_road", "surface": "road", "shoulder": 1.6, "shoulder_mat": ("dash_shoulder", "dirt")},
        "spiral": {
            "mat": "oasis_paving",
            "surface": "road",
            "shoulder": 0.6,
            "shoulder_mat": ("masonry", "road"),
            "barrier": 1.3,
            "barrier_mat": ("masonry", "wall"),
            "deck": 2.2,
            "deck_mat": ("masonry", "wall"),
            "ground": False,
        },
        "ramp": {"mat": "dash_road", "surface": "road", "shoulder": 1.6, "shoulder_mat": ("pale_sand", "dirt")},
        # Over Havasu Creek: a timber bridge, plank deck, ranch rails.
        "bridge": {"mat": "plank_deck", "surface": "road", "shoulder": 0.5, "shoulder_mat": ("weathered_timber", "road"),
                   "barrier": 1.1, "barrier_mat": ("fence_rail", "wall"), "deck": 1.0, "deck_mat": ("weathered_timber", "wall"),
                   "ground": False},
    }
    if RUIN:
        ruin_course(c)
        return

    def label(smp):
        s = smp.s
        seg = seg_of(s)
        if LIP <= s <= LAND:
            return "gap"
        if LIP - 12 <= s < LIP:
            return "ramp"
        if seg in (0, 1, 2, 28):
            return "street"
        if on_bridge(smp):
            return "bridge"
        if seg == 25 or (seg == 26 and s < SEG[26] + 12):
            return "spiral"
        return "trail"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "ramp":
            specials.append((s0, s1, "ramp", {"lift": lambda u, n: 0.8 * max(0.0, (u - (n - 8)) / 8) ** 2}))
        elif k != "trail":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "trail", max_len=200.0))

    # The shortcut along the pool's bank, at the road's height where it leaves and rejoins.
    za, zb = road_z(SEG[5], 4), road_z(SEG[8], 8)
    sc = [(x, y, lerp(za, zb, i / (len(SHORTCUT) - 1)) - 0.05) for i, (x, y) in enumerate(SHORTCUT)]
    c.shortcut("Cottonwood Grove", sc, "dash_road", "road", width=8.0, shoulder=0.8, shoulder_mat=("oasis_lawn", "grass"), flush=True)

    c.terrain("Canyon", X0, X1, Y0, Y1, 6.0, natural, classify, near=10.0, fade=18.0, under=0.2, fine=3, cut_z=BANDS)
    water(c)

    def under(x, y):
        return natural(x, y) - 0.4

    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 6.0, under, c.lib("red_sand", "loose_sand"))

    import oasis_desert  # noqa: E402

    oasis_desert.build(c, sys.modules[__name__])

    c.start_line()
    S = lambda i: SEG[i]  # noqa: E731
    # Zippers: onto the sweep round the pool, out of it, out of the camp, and west under
    # the arch. (Onto the spiral there's a blue balloon instead: a zipper there was too
    # much speed.)
    for at in (S(4) + 6, S(8) + 6, S(13) + 4, S(19) + 4):
        c.zipper(at, 0)
    for at, across in ((S(6) + 40, 0), (S(11) + 30, 0), (S(18) + 40, 0), (S(22) + 30, 0), (S(28) + 10, -3)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (S(1) + 20, -4, "red"),
        (S(1) + 20, 4, "blue"),
        (S(7) + 20, 0, "green"),
        (S(12) + 10, 0, "yellow"),
        (S(17) + 10, 0, "rainbow"),
        (S(21) + 10, -4, "red"),
        (S(21) + 10, 4, "blue"),
        (S(24) + 40, 0, "blue"),
        (S(25) + 120, 0, "green"),
    ):
        c.balloon(at, across, col)
    # A missed jump: put down past it.
    c.entity("respawn", **{"from": round(LIP - 20, 1), "to": round(LAND + 4, 1), "at": round(LAND + 20, 1)})

    # Checkpoints: one in the middle of the stretch the shortcut skips, with a twin gate
    # across the shortcut (either counts), and none elsewhere in that stretch.
    s_in, s_out = kit.s_near(c, *SHORTCUT[0]), kit.s_near(c, *SHORTCUT[-1])
    apex = (s_in + s_out) / 2
    gates = c.checkpoints(
        extra=[S(2), apex, S(10) + 30, S(13), S(16) + 20, S(18) + 50, S(21), S(24) + 20, S(25) + 100, S(25) + 200, LAND + 25],
        avoid=[(s_in - 4, apex - 8), (apex + 8, s_out + 4)],
        height=10.0,
    )
    main_gate = min(gates.items(), key=lambda kv: abs(kv[0] - apex))[1]
    mid = SHORTCUT[2]
    c.alt_gate(main_gate, "palm_grove", [(SHORTCUT[1][0], SHORTCUT[1][1], za), (mid[0], mid[1], za), (SHORTCUT[3][0], SHORTCUT[3][1], zb)], width=14.0)

    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish()
    # A hot blue Southwest afternoon over the red rock.
    path = os.path.join(kit.TRACKS_DIR, TRACK_ID, "look.json")
    with open(path, encoding="utf-8") as f:
        look = json.load(f)
    look["sky"] = "#3d8fd6"
    look.setdefault("fog", {}).update({"enabled": True, "color": "#d9d4c8", "near": 500, "far": 2600})
    dome = look.setdefault("skyDome", {})
    dome.update({"top": "#1d64c4", "horizon": "#b9d9f0", "bottom": "#d9875a"})
    dome.setdefault("sun", {}).update({"color": "#fff6e0", "glow": "#ffd9a0", "elevation": 48})
    dome.setdefault("hills", {}).update({"color": "#b4532e", "far": "#d98a5c", "style": "mesas"})
    look.setdefault("ambient", {}).update({"sky": "#cfe2f2"})
    with open(path, "w", encoding="utf-8") as f:
        json.dump(look, f, indent=2)
        f.write("\n")
    print("lap", round(c.length, 1))


def ruin_course(c):
    """The ruin's roads, land and gameplay (oasis_ruins.py builds the wreckage)."""
    S = SEG
    rubble = ("ruin_rubble", "dirt")
    c.kinds.update({
        # The dragon's scorch over the dunes: the sand burnt hard and dark.
        "scorch": {"mat": "ruin_road", "surface": "road", "shoulder": 1.8, "shoulder_mat": ("ruin_ash", "dirt")},
        # Up the rubble of the spiral's fallen decks, then along the fallen tower's broken
        # body (on it: the land keeps its own shape under the tower) to its top.
        "rubble": {"mat": "ruin_road", "surface": "road", "shoulder": 1.4, "shoulder_mat": rubble},
        "tower": {"mat": "ruin_road", "surface": "road", "shoulder": 1.2, "shoulder_mat": rubble, "deck": 2.4, "deck_mat": ("adobe", "wall"),
                  "ground": False},
        "kicker": {"mat": "ruin_road", "surface": "road", "shoulder": 1.2, "shoulder_mat": rubble, "deck": 2.4, "deck_mat": ("adobe", "wall"),
                   "ground": False},
        # Over the fallen arch's span.
        "span": {"mat": "dash_road", "surface": "road", "shoulder": 1.4, "shoulder_mat": rubble},
    })

    def label(smp):
        s = smp.s
        seg = seg_of(s)
        if LIP <= s <= LAND or TLIP <= s <= TLAND:
            return "gap"
        if LIP - 12 <= s < LIP:
            return "ramp"
        if TLIP - 12 <= s < TLIP:
            return "kicker"
        if seg in (0, 1, 2, 27):
            return "street"
        if on_bridge(smp):
            return "bridge"
        if 10 <= seg <= 15:
            return "scorch"
        if seg >= 24 and s < SEG[26] + 4:
            return "rubble"
        if seg >= 24 and s < TLIP:
            return "tower"
        if any(abs(s - at) < ln / 2 + 3 for at, _, ln in HUMPS):
            return "span"
        return "trail"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "ramp":
            specials.append((s0, s1, k, {"lift": lambda u, n: 0.8 * max(0.0, (u - (n - 8)) / 8) ** 2}))
        elif k == "kicker":
            specials.append((s0, s1, k, {"lift": lambda u, n: 1.2 * max(0.0, (u - (n - 8)) / 8) ** 2}))
        elif k != "trail":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "trail", max_len=200.0))

    # The palm-grove shortcut, as it always was.
    za, zb = road_z(SEG[5], 4), road_z(SEG[8], 8)
    sc = [(x, y, lerp(za, zb, i / (len(SHORTCUT) - 1)) - 0.05) for i, (x, y) in enumerate(SHORTCUT)]
    c.shortcut("Cottonwood Grove", sc, "dash_road", "road", width=8.0, shoulder=0.8, shoulder_mat=("oasis_lawn", "grass"), flush=True)

    c.terrain("Canyon", X0, X1, Y0, Y1, 6.0, natural, classify, near=10.0, fade=18.0, under=0.2, fine=3, cut_z=BANDS)
    water(c)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 6.0, lambda x, y: natural(x, y) - 0.4, c.lib("red_sand", "loose_sand"))
    ruin_mode.DRESS(c, sys.modules[__name__])
    c.start_line()

    # Zippers: onto the sweep round the pool and out of it, out along the scorch, west
    # through the burnt camp, at the fallen arch, and up the tower's rubble (to clear its
    # gap).
    for at in (S[4] + 6, S[8] + 6, S[11] + 6, S[13] + 10, S[19] + 4, TLIP - 22):
        c.zipper(at, 0)
    for at, across in ((S[6] + 40, 0), (S[12] + 60, 0), (S[18] + 40, 0), (S[22] + 30, 0), (S[27] + 10, -3)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in ((S[1] + 20, -4, "red"), (S[1] + 20, 4, "blue"), (S[7] + 20, 0, "green"), (S[11] + 20, 0, "yellow"),
                            (S[13] + 40, 0, "blue"), (S[17] + 10, 0, "rainbow"), (S[21] + 10, -4, "red"), (S[21] + 10, 4, "blue"),
                            (TLAND + 18, 0, "green")):
        c.balloon(at, across, col)
    # Missed jumps: put down past them.
    c.entity("respawn", **{"from": round(TLIP - 20, 1), "to": round(TLAND + 4, 1), "at": round(TLAND + 16, 1)})
    c.entity("respawn", **{"from": round(LIP - 20, 1), "to": round(LAND + 4, 1), "at": round(LAND + 20, 1)})
    s_in, s_out = kit.s_near(c, *SHORTCUT[0]), kit.s_near(c, *SHORTCUT[-1])
    apex = (s_in + s_out) / 2
    gates = c.checkpoints(
        extra=[S[2], apex, S[10] + 30, S[11] + 30, S[12] + 60, S[13] + 40, S[14] + 30, S[16] + 20, S[18] + 50, S[21], S[24] + 5,
               S[25] + 20, TLAND + 12, LAND + 25],
        avoid=[(s_in - 4, apex - 8), (apex + 8, s_out + 4)],
        height=10.0,
    )
    main_gate = min(gates.items(), key=lambda kv: abs(kv[0] - apex))[1]
    mid = SHORTCUT[2]
    c.alt_gate(main_gate, "palm_grove", [(SHORTCUT[1][0], SHORTCUT[1][1], za), (mid[0], mid[1], za), (SHORTCUT[3][0], SHORTCUT[3][1], zb)], width=14.0)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish()
    print("lap", round(c.length, 1))


if __name__ == "__main__":
    main()
