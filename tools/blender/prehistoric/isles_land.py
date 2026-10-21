# Dragon Isles: the land, as plain data and functions (no Blender), shared by the course
# script (dragon_isles.py), its scenery modules and the preview tools.
# SPDX-License-Identifier: MIT
#
# A kingdom of karst mountains rising out of a turquoise lagoon. The lap runs clockwise:
#
#   West: the Riverside Festival Village on the valley floor (z ~6), the lagoon's
#   waterfront to its east. North: a cliff band climbs to the northern highland (z ~46),
#   cut by the river's gorge. East: the temple plateau, then a spine of karst pillars
#   running south through the lagoon (the Sky Paths). South: the harbour town on the
#   shore. South-west: the headland the Ancient Dragon Passage bores through, and its
#   overlook north over the whole kingdom to the palace on its mountain far beyond.

import math

from impact_land import _close, _turtle, clamp, lerp, noise, rnd, seg_dist, sm  # noqa: F401

# ---------------------------------------------------------------- the layout

START = (0.0, 0.0)
LAYOUT = [
    ("S", 80),  # 0  1: the Grand Ceremonial Gate, north up the start straight
    ("R", 80, 20),  # 1  2: into the Riverside Festival Village
    ("S", 25),  # 2  market street
    ("L", 50, 35),  # 3  over the canal bridge
    ("R", 50, 35),  # 4
    ("S", 20),  # 5  the festival square
    ("L", 80, 20),  # 6
    ("S", 10),  # 7
    ("L", 50, 90),  # 8  3: the Cliffside Ascent: west up the cliff
    ("S", 60),  # 9  the lower ledge, waterfalls below
    ("R", 50, 180),  # 10 the hairpin
    ("S", 60),  # 11 the upper ledge (a short tunnel through an outcrop)
    ("L", 120, 20),  # 12
    ("R", 120, 20),  # 13
    ("S", 140),  # 14 4: the Great Waterfall Bridge over the gorge
    ("S", 30),  # 15 5: the Temple Gardens
    ("R", 42, 90),  # 16 round the temple garden's south side (the courtyard passage
    ("S", 10),  # 17      cuts straight across)
    ("L", 42, 90),  # 18
    ("S", 46),  # 19 past the lotus pools
    ("L", 42, 90),  # 20
    ("S", 10),  # 21
    ("R", 42, 90),  # 22
    ("S", 30),  # 23
    ("R", 70, 90),  # 24 6: the Sky Paths, south along the karst spine
    ("S", 100),  # 25 (closes the lap)
    ("R", 160, 25),  # 26
    ("L", 160, 50),  # 27
    ("R", 160, 25),  # 28
    ("S", 90),  # 29 the long bridge: the dragon flies over
    ("R", 90, 60),  # 30 7: down to the Lantern Harbour
    ("S", 60),  # 31
    ("R", 90, 30),  # 32
    ("S", 120),  # 33 the harbour boardwalk (closes the lap)
    ("S", 80),  # 34 the harbour bridge
    ("R", 70, 40),  # 35
    ("S", 85),  # 36 8: the Ancient Dragon Passage
    ("R", 100, 50),  # 37 9: the Grand Reveal
    ("S", 45),  # 38 the overlook
    ("R", 150, 15),  # 39 10: the Royal Approach
    ("L", 150, 15),  # 40
    ("S", 20),  # 41 11: the Palace Finish
]
LAYOUT, PATH = _close(LAYOUT, 25, 33, START, 90.0)
_D = [0.0]
for _a, _b in zip(PATH, PATH[1:]):
    _D.append(_D[-1] + math.hypot(_b[0] - _a[0], _b[1] - _a[1]))
LENGTH = _D[-1]
SEG = {}
for _i, _p in enumerate(PATH):
    SEG.setdefault(_p[3], _D[_i])
S = SEG


def seg_of(s):
    k = 0
    for i, d in SEG.items():
        if d <= s:
            k = max(k, i)
    return k


def path_at(s):
    """(x, y, heading degrees) s metres along the lap (wraps)."""
    s %= LENGTH
    lo, hi = 0, len(_D) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if _D[mid] <= s:
            lo = mid
        else:
            hi = mid
    a, b = PATH[lo], PATH[hi]
    t = (s - _D[lo]) / max(1e-9, _D[hi] - _D[lo])
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def side(s, o):
    """The point `o` metres to the right of the centre line, s metres along."""
    x, y, h = path_at(s)
    r = math.radians(h - 90.0)
    return (x + o * math.cos(r), y + o * math.sin(r))


def arc_centre(i):
    k = next(j for j, p in enumerate(PATH) if p[3] == i)
    x, y, h, _ = PATH[k]
    sg = LAYOUT[i]
    a = math.radians(h + (90 if sg[0] == "L" else -90))
    return (x + sg[1] * math.cos(a), y + sg[1] * math.sin(a))


_TREE = None


def nearest(x, y):
    """(distance, lap s) of the race line's nearest point (a coarse grid search)."""
    global _TREE
    if _TREE is None:
        cells = {}
        for j in range(0, len(PATH), 2):
            p = PATH[j]
            cells.setdefault((int(p[0] // 40), int(p[1] // 40)), []).append(j)
        _TREE = cells
    cx, cy = int(x // 40), int(y // 40)
    best = (1e9, 0.0)
    for r in range(0, 6):
        for i in range(cx - r, cx + r + 1):
            for k in range(cy - r, cy + r + 1):
                if max(abs(i - cx), abs(k - cy)) != r:
                    continue
                for j in _TREE.get((i, k), ()):
                    p = PATH[j]
                    d = (p[0] - x) ** 2 + (p[1] - y) ** 2
                    if d < best[0]:
                        best = (d, _D[j])
        if best[0] < (r * 40) ** 2:
            break
    return math.sqrt(best[0]), best[1]


# ---------------------------------------------------------------- the road

Z_VALLEY = 6.5
Z_HIGH = 46.0
ANCHORS = [
    (0.0, 8.0),
    (S[1], 7.5),
    (S[3], 6.6),  # the canal bridge
    (S[5], 6.5),
    (S[8], 7.0),
    (S[9], 12.0),  # up the cliff
    (S[10], 19.0),
    (S[11], 29.0),
    (S[12], 37.0),
    (S[14], 44.0),  # the Great Waterfall Bridge
    (S[15], 45.5),
    (S[24], 47.0),
    (S[26], 46.0),  # the Sky Paths
    (S[28], 41.0),
    (S[29], 38.0),
    (S[30], 31.0),  # down to the harbour
    (S[32], 10.0),
    (S[33], 3.6),
    (S[34], 3.8),
    (S[34] + 40, 8.5),  # the harbour bridge's crown
    (S[35], 4.5),
    (S[36], 6.0),
    (S[37], 16.0),  # up through the passage
    (S[38], 18.5),  # the overlook
    (S[39], 17.0),
    (S[41], 9.0),
    (LENGTH, 8.0),
]


def _lin(d):
    d = min(max(d, 0.0), LENGTH)
    for (d0, z0), (d1, z1) in zip(ANCHORS, ANCHORS[1:]):
        if d0 <= d <= d1:
            return lerp(z0, z1, (d - d0) / max(1e-6, d1 - d0))
    return ANCHORS[-1][1]


def road_z(d, seg=None):
    return sum(_lin(d + k) for k in range(-12, 13, 3)) / 9.0


def road_w(d, seg):
    if seg in (0, 41) or d > S[40] + 30 or d < 40:
        return 22.0  # the start: room for the pack
    if seg in (14, 29):
        return 18.0  # the great bridges
    if seg in (2, 3, 4, 5, 6):
        return 15.0  # the village streets
    if seg in (36,):
        return 15.0  # the passage
    return 16.0


# ---------------------------------------------------------------- landmarks

PALACE = (150.0, 1240.0)  # the royal palace on its mountain, far to the north
PALACE_Z = 150.0
RIVER_X = 150.0  # the gorge through the northern highland
GORGE_HW = 40.0
FALLS_Y = 530.0  # the great falls, where the highland river drops into the gorge
HEADLAND = (40.0, -285.0)
TEMPLE = arc_centre(16)  # (the temple stands inside the bend round it)
SQUARE = (60.0, 230.0)  # the festival square, by the village's waterfront


def _temple_centre():
    a = path_at(S[16])
    b = path_at(S[19])
    return ((a[0] + b[0]) / 2 + 10.0, (a[1] + b[1]) / 2 + 22.0)



# ---------------------------------------------------------------- the land


def _blob(x, y, cx, cy, rx, ry, a=0.0):
    ca, sa = math.cos(a), math.sin(a)
    u = ((x - cx) * ca + (y - cy) * sa) / rx
    v = (-(x - cx) * sa + (y - cy) * ca) / ry
    return math.sqrt(u * u + v * v)


def valley(x, y):
    """The western valley floor: the start, the village, the approach (0 outside, 1 in)."""
    d = 1e9
    for a, b in (((-20.0, -170.0), (-10.0, 60.0)), ((-10.0, 60.0), (40.0, 300.0))):
        dd, _ = seg_dist(x, y, a[0], a[1], b[0], b[1])
        d = min(d, dd)
    w = 95.0 + 18.0 * noise(x, y, 0.02, 1.0)
    return 1.0 - sm((d - w) / 30.0)


def highland(x, y):
    """The northern highland and the temple plateau: 1 on top, 0 below its cliffs."""
    edge = 330.0 + 80.0 * sm((x + 250.0) / 300.0) * 0.0 + 12.0 * noise(x, y, 0.03, 2.0)
    # The cliff band: from the valley at y 300 up to the top at y 440 (west of the gorge),
    # stepped; east of the gorge the plateau's edge comes further south.
    if x > RIVER_X + GORGE_HW - 6:
        e = 296.0 + 10.0 * noise(x, y, 0.04, 3.0)
        if x > 480.0:
            e += (x - 480.0) * 1.6
        t = sm((y - e) / 26.0)
        if x > 520.0 + 10.0 * noise(x, y, 0.05):
            t *= 1.0 - sm((x - 520.0) / 20.0)
        return t, "east"
    t = (y - (edge - 20.0)) / 110.0
    return clamp(t), "north"


def gorge(x, y):
    """How deep inside the river's gorge (metres from its wall, > 0 inside)."""
    if y < 300.0:
        return -99.0
    hw = GORGE_HW + 6.0 * noise(x, y, 0.05, 4.0) + (12.0 if y > FALLS_Y + 20 else 0.0)
    return hw - abs(x - (RIVER_X + 8.0 * math.sin(y / 70.0)))


def headland(x, y):
    d = _blob(x, y, HEADLAND[0], HEADLAND[1], 125.0, 95.0, 0.3)
    return 1.0 - sm((d - 0.35) / 0.65)


def west_wall(x, y):
    """The great karst wall west of the valley (0..1)."""
    e = -150.0 + 25.0 * noise(x, y, 0.025, 5.0)
    return sm((e - x) / 45.0)


def harbour_shore(x, y):
    """The harbour town's strip of shore, north of the boardwalk (0..1)."""
    if not (190.0 < x < 470.0):
        return 0.0
    return sm((y + 312.0) / 6.0) * (1.0 - sm((y + 200.0) / 30.0)) * (1.0 - sm((x - 440.0) / 30.0)) * sm((x - 200.0) / 14.0)


def spine(x, y):
    """The karst spine under the Sky Paths: (height, weight) near the road in segments
    20-26, but broken by gaps the road bridges."""
    d, s = nearest(x, y)
    if not (S[24] - 20 <= s <= S[30] + 30) or d > 40:
        return None
    for a, b in GAPS:
        if a < s < b:
            return None
    w = 1.0 - sm((d - 14.0) / 22.0)
    return road_z(s) - 0.4 - (d * 0.6 if d > 12 else 0.0), w


# Stretches of the Sky Paths (lap distance) bridged over the lagoon.
GAPS = [(S[25] + 20, S[26] + 30), (S[27] + 60, S[28] + 10), (S[29] - 5, S[29] + 125)]

SEA = -7.0  # the lagoon's bed
WATER_Z = 0.0


def natural(x, y):
    """The land before the roads shape it."""
    z = SEA + 1.5 * noise(x, y, 0.03, 6.0)
    # The valley floor.
    v = valley(x, y)
    z = lerp(z, Z_VALLEY + 0.8 * noise(x, y, 0.04, 7.0), v)
    # The highland and its stepped cliffs.
    h, part = highland(x, y)
    if h > 0:
        top = Z_HIGH + 2.0 * noise(x, y, 0.02, 8.0)
        if part == "north":
            # Terraced: three steps up the cliff.
            steps = (Z_VALLEY, 18.0, 30.0, top)
            k = min(2.999, h * 3.0)
            i = int(k)
            f = k - i
            hz = lerp(steps[i], steps[i + 1], sm((f - 0.55) / 0.3))
        else:
            hz = top
        z = max(z, lerp(z, hz, 1.0 if part == "north" else h))
        if part == "east":
            z = lerp(z, top, h)
    # The gorge, down to the river.
    g = gorge(x, y)
    if g > -20:
        floor = -4.0 if y < FALLS_Y else Z_HIGH - 3.0
        z = lerp(z, floor, sm((g + 4.0) / 10.0))
    # The headland, the west wall.
    # The headland itself is a rock (isles_scenery.py); under and round it, a low shelf.
    hd = headland(x, y)
    if hd > 0:
        z = max(z, lerp(z, 7.0, min(1.0, hd * 2.5)))
    ww = west_wall(x, y)
    if ww > 0:
        z = max(z, lerp(z, 85.0 + 25.0 * noise(x, y, 0.012, 10.0), ww))
    hs = harbour_shore(x, y)
    if hs > 0:
        z = max(z, lerp(z, 3.4, hs))
    sp = spine(x, y)
    if sp is not None:
        sz, w = sp
        z = max(z, lerp(z, sz, w))
    return z


# The village canal: from the lagoon west across the valley, under the canal bridge.
CANAL = [(130.0, 172.0), (70.0, 166.0), (20.0, 158.0), (-40.0, 150.0), (-80.0, 140.0)]
CANAL_HW = 7.0


def canal_d(x, y):
    best = 1e9
    for a, b in zip(CANAL, CANAL[1:]):
        d, _ = seg_dist(x, y, a[0], a[1], b[0], b[1])
        best = min(best, d)
    return best


def ground(x, y):
    """The land with the canal cut through it."""
    z = natural(x, y)
    d = canal_d(x, y)
    if d < CANAL_HW + 4 and z > -2.5:
        z = lerp(-2.5, z, sm((d - CANAL_HW + 1.0) / 4.0))
    return z


# The temple courtyard passage (the shortcut): a smooth curve from where the main road
# turns south round the temple to where it comes back.
def _shortcut_line():
    a = S[15] + 6.0
    b = S[23] + 10.0
    x0, y0, h0 = path_at(a)
    x3, y3, h3 = path_at(b)
    k = 0.38 * math.hypot(x3 - x0, y3 - y0)
    x1, y1 = x0 + k * math.cos(math.radians(h0)), y0 + k * math.sin(math.radians(h0))
    x2, y2 = x3 - k * math.cos(math.radians(h3)), y3 - k * math.sin(math.radians(h3))
    pts = []
    n = 80
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u ** 3 * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t ** 3 * x3
        y = u ** 3 * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t ** 3 * y3
        pts.append((x, y, lerp(road_z(a), road_z(b), t) + 0.4 * math.sin(math.pi * t)))
    return pts, a, b


SHORTCUT, SHORT_A, SHORT_B = _shortcut_line()
TEMPLE = (SHORTCUT[40][0], SHORTCUT[40][1])

GRID = (-400.0, 760.0, -520.0, 720.0)
CELL = 6.0


def zone_of(s):
    z = ZONES[0][1]
    for d, name in ZONES:
        if s >= d:
            z = name
    return z


ZONES = [
    (0.0, "gate"),
    (S[1] - 10, "village"),
    (S[8] + 20, "cliff"),
    (S[14] - 10, "bridge"),
    (S[15], "temple"),
    (S[23] + 16, "sky"),
    (S[30] + 40, "harbour"),
    (S[35] + 30, "passage"),
    (S[37] + 30, "reveal"),
    (S[39], "royal"),
]
