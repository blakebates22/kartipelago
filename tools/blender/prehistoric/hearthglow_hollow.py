# Hearthglow Hollow: Frostveil Peaks, course 3. A Christmas village on a snowy evening.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/hearthglow_hollow.py      (the bpy module)
#
# A short lap (about 1.55 km), most of it in a magical alpine village at twilight, all
# decorated for Christmas, with a quick, winding run up the mountain above it (the
# first version is kept as hearthglow_hollow_v2):
#
#   A  The Village Entrance and the Square: from the start, under a great wooden
#      Christmas arch, up the entrance street of glowing cottages and round the giant
#      Christmas tree in a sweep of curves, past the frozen fountain, stalls, snowmen and
#      presents (drive into a present: it bursts into confetti, and boosts you like a
#      blue balloon).
#   B  The Frozen River Crossing: north over an arched stone bridge above the frozen
#      river, and west along the north lane, out of the village.
#   C  The Mountain Road: up through the lit pines in S-bends, giant snowballs rolling
#      across on a fixed beat, round the bell tower at the summit.
#   D  The Sleigh Run: a plunge down the far side, a jump, a sleigh crossing on a fixed
#      beat, and down onto the covered bridge.
#   E  The Old Town: through the lantern-lit covered bridge, an S through the old town,
#      the market chicane, down the west lane, along the bottom lane and a last drift
#      onto the finish street. Or, for the brave: a narrow back alley through the old
#      town (hidden in a gap between the cottages on the left, just before the market
#      chicane), walled, with an icy dogleg in the middle, that comes out on the finish
#      street right before the line.
#
# Every corner is a 30-50 m arc. Saves tracks-src/hearthglow_hollow.blend and exports
# public/tracks/hearthglow_hollow/. The scenery is hearthglow_scenery.py, built from
# the kit in hearthglow_props.py.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import ruin_mode  # noqa: E402
from course_kit import lerp, smooth  # noqa: E402

# The ruin (hearthglow_ruins.py): the dragons burned the village. The stone bridge has
# fallen into the river, so the mountain, the sleigh run and the covered bridge are cut
# off; the lap turns west out of the square along the burnt riverside, into the old town
# and down the back alley, which the fire and the falling houses have opened into a
# street of rubble, home. Everything else (the land, the landmarks) is the course's own.
RUIN = ruin_mode.ON
TRACK_ID = "hearthglow_hollow_ruin" if RUIN else "hearthglow_hollow"

# ---------------------------------------------------------------- the layout

START = (0.0, -120.0)
LAYOUT = [
    ("S", 60),  # 0  A: the entrance street, north
    ("R", 40, 40),  # 1  into the square...
    ("L", 50, 120),  # 2  ...round the giant tree...
    ("R", 45, 80),  # 3  ...and out, north
    ("S", 30),  # 4  B: the street to the bridge
    ("S", 60),  # 5  the stone bridge over the frozen river
    ("S", 20),  # 6
    ("L", 40, 90),  # 7  west...
    ("S", 20),  # 8  ...along the north lane (the first snowball crossing)
    ("R", 35, 90),  # 9  C: up into the pines, in S-bends
    ("L", 35, 45),  # 10
    ("R", 35, 45),  # 11
    ("S", 20),  # 12 the second snowball crossing
    ("L", 36, 180),  # 13 the summit, round the bell tower
    ("S", 60),  # 14 D: the sleigh run and its jump
    ("R", 40, 35),  # 15
    ("L", 40, 35),  # 16
    ("S", 50),  # 17 the sleigh crossing
    ("S", 70),  # 18 E: through the covered bridge
    ("L", 30, 60),  # 19 an S through the old town
    ("S", 20),  # 20
    ("R", 30, 60),  # 21
    ("S", 40),  # 22 (the back alley leaves on the left)
    ("R", 30, 45),  # 23 the market chicane
    ("L", 30, 90),  # 24
    ("R", 30, 45),  # 25
    ("S", 100),  # 26 the west lane (stretched to close the loop)
    ("L", 45, 90),  # 27
    ("S", 120),  # 28 the bottom lane (stretched to close the loop)
    ("L", 45, 90),  # 29 the last drift, onto the finish street
    ("S", 50),  # 30 the finish street, north to the line
]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 26, 28, START, 90.0)
STANDARD_LAYOUT, STANDARD_PATH = LAYOUT, PATH
SEG = STANDARD_SEG = kit.segment_starts(PATH)
LENGTH = STANDARD_LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))
# The jump on the sleigh run: (lip, landing).
JUMPS = STANDARD_JUMPS = [(SEG[14] + 26, SEG[14] + 38)]
# The zippers (metres along the lap): out of the square to the bridge, onto the climb,
# down onto the covered bridge, out of the market chicane and along the bottom lane.
ZIPPERS = [SEG[4] + 6, SEG[8] + 3, SEG[17] + 6, SEG[26] + 8, SEG[28] + 20]


def _seg_point(i):
    return next(p for p in STANDARD_PATH if p[3] == i)


def _arc_centre(i):
    """The centre of the standard lap's arc segment i (the landmarks stay put in the ruin)."""
    x, y, h, _ = _seg_point(i)
    sg = STANDARD_LAYOUT[i]
    a = math.radians(h + (90 if sg[0] == "L" else -90))
    return (x + sg[1] * math.cos(a), y + sg[1] * math.sin(a))


TREE = _arc_centre(2)  # the giant Christmas tree, in the middle of the square
SUMMIT = _arc_centre(13)  # the bell tower stands inside the summit turn

# Heights along the lap (metres along it, height); the road eases between them.
J = JUMPS
ANCHORS = STANDARD_ANCHORS = [
    (0.0, 3.0),
    (SEG[1], 3.0),
    (SEG[2], 2.0),  # down into the square
    (SEG[3], 2.0),
    (SEG[4], 2.6),
    (SEG[5], 4.2),  # the stone bridge, arched over the river
    (SEG[5] + 30, 5.0),
    (SEG[6], 4.2),
    (SEG[8], 4.0),
    (SEG[9], 5.0),  # the mountain road
    (SEG[10], 10.0),
    (SEG[11], 13.5),
    (SEG[12], 17.0),
    (SEG[13], 20.0),
    (SEG[14], 22.5),  # the summit
    (J[0][0], 20.5),  # the jump's lip
    (J[0][1], 16.5),  # ...its landing
    (SEG[15], 14.0),
    (SEG[17], 9.0),
    (SEG[18], 6.0),  # the covered bridge
    (SEG[18] + 35, 5.8),
    (SEG[19], 4.6),
    (SEG[20], 4.0),
    (SEG[22], 3.4),
    (SEG[24], 3.0),
    (LENGTH, 3.0),
]
HUMPS = []

if RUIN:
    # Blake: the ruined city as the course, a fast speedrun-feel lap (not as wild as the
    # first beach course: there are four map fragments to collect). The course's own lap
    # through the square (0-3); the stone bridge is down, so west along the burnt
    # riverside (4-5), south into the old town (6-7), and down the back alley, opened into
    # a street by the fallen houses (8-12: the alley's own line), round onto the finish
    # street (13-14). The head's straights are solved so the lap meets the alley exactly.
    _R1, _R2 = 30.0, 40.0
    _ax, _ay = _seg_point(4)[:2]
    LAYOUT = STANDARD_LAYOUT[:4] + [
        ("L", _R1, 90),  # 4  west, short of the fallen bridge
        ("S", (_ax - _R1) + 212.0 - _R2),  # 5  along the burnt riverside (to x = -212, the alley's)
        ("L", _R2, 90),  # 6  south into the old town
        ("S", _ay + _R1 - _R2 - 44.0),  # 7  down its street to the alley
        ("L", 45, 35),  # 8  into the alley: its own line from here...
        ("S", 140),  # 9  (closes the loop)
        ("R", 25, 30),  # 10 the icy dogleg
        ("L", 25, 30),  # 11
        ("S", 40),  # 12
        ("L", 50, 145),  # 13 ...and round onto the finish street
        ("S", 10),  # 14 (closes the loop)
    ]
    LAYOUT, PATH = kit.close_turtle(LAYOUT, 9, 14, START, 90.0)
    SEG = kit.segment_starts(PATH)
    LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))
    JUMPS = []
    # Zippers: along the riverside, down the alley, round the last sweep.
    ZIPPERS = [SEG[5] + 8, SEG[9] + 30, SEG[13] + 24]
    ANCHORS = [
        (0.0, 3.0),
        (SEG[1], 3.0),
        (SEG[2], 2.0),
        (SEG[3], 2.0),
        (SEG[4], 2.6),
        (SEG[5], 3.2),
        (SEG[6], 3.6),
        (SEG[8], 3.4),
        (SEG[13], 3.0),
        (LENGTH, 3.0),
    ]
    # Rubble the road rides over (distance along the lap, height, length): the burnt
    # cottages' fallen walls on the riverside, the houses fallen into the alley.
    HUMPS = [(SEG[5] + 28, 1.5, 20), (SEG[5] + 62, 1.7, 22), (SEG[9] + 60, 1.4, 20), (SEG[9] + 104, 1.6, 22)]


def hump(d):
    z = 0.0
    for at, h, ln in HUMPS:
        t = (d - at) / (ln / 2)
        if -1 < t < 1:
            z += h * 0.5 * (1 + math.cos(math.pi * t))
    return z


def _heights(anchors, length, jumps, humps):
    """road_z for a lap: its anchors, eased over 30 m (straight through its jumps)."""

    def lin(d):
        d = min(max(d, 0.0), length)
        for (d0, z0), (d1, z1) in zip(anchors, anchors[1:]):
            if d0 <= d <= d1:
                return lerp(z0, z1, (d - d0) / max(1e-6, d1 - d0))
        return 3.0

    def road_z(d, seg=None):
        # The jumps' run-ups, gaps and landings are straight slopes; elsewhere heights
        # ease over 30 m.
        if any(lip - 34 <= d <= land + 14 for lip, land in jumps):
            return lin(d)
        return sum(lin(d + k) for k in range(-15, 16, 3)) / 11 + (hump(d) if humps else 0.0)

    return lin, road_z


_lin, road_z = _heights(ANCHORS, LENGTH, JUMPS, HUMPS)
# The standard lap's heights (the land round the mountain road is shaped by them).
_, standard_road_z = _heights(STANDARD_ANCHORS, STANDARD_LENGTH, STANDARD_JUMPS, [])


def road_w(d, seg):
    if RUIN:
        if seg in (1, 2, 3):
            return 17.0  # the square
        if 8 <= seg <= 12:
            return 14.0  # the alley, opened up
        return 16.0 if seg in (4, 5, 6, 7) else 15.0
    if seg in (1, 2, 3):
        return 17.0  # the square
    if seg in (14, 15, 16, 17):
        return 18.0  # the sleigh run's broad chute
    if seg in (5, 18):
        return 14.0  # the bridges
    if seg in (23, 24, 25):
        return 16.0  # the market chicane
    return 15.0


ROUTE = kit.route_points_by(PATH, road_z, every=10.0, width=road_w)


def seg_of(s):
    k = 0
    for i, d in SEG.items():
        if d <= s:
            k = max(k, i)
    return k


# ---------------------------------------------------------------- the land


def sm(t):
    return smooth(max(0.0, min(1.0, t)))


def _nearest(px, py, pts):
    """Distance to a polyline, the index of the nearest segment, and the nearest point."""
    best = (1e9, 0, (0.0, 0.0))
    for i, ((ax, ay), (bx, by)) in enumerate(zip(pts, pts[1:])):
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        qx, qy = ax + t * dx, ay + t * dy
        d = math.hypot(px - qx, py - qy)
        if d < best[0]:
            best = (d, i, (qx, qy))
    return best


# The frozen river: down from the falls in the north-east mountains, west under the
# stone bridge (x = -57) and the covered bridge (x = -259), and south down the west side
# of the valley, where the creek comes in, out of the valley.
RIVER = [(300.0, 600.0), (250.0, 470.0), (150.0, 300.0), (40.0, 180.0), (-57.0, 150.0), (-150.0, 150.0),
         (-250.0, 146.0), (-345.0, 138.0), (-378.0, 70.0), (-382.0, -40.0), (-365.0, -200.0), (-340.0, -560.0)]
# The creek: from the falls in the north-west mountains, south behind the mountain, into
# the river.
CREEK = [(-430.0, 640.0), (-432.0, 560.0), (-436.0, 450.0), (-440.0, 300.0), (-425.0, 180.0), (-400.0, 110.0), (-378.0, 70.0)]
RIVER_Z = -1.6  # the ice


def water_at(x, y):
    """(distance from the nearest water's centre, its half-width, which: 0 river 1 creek)."""
    d0 = _nearest(x, y, RIVER)[0]
    d1 = _nearest(x, y, CREEK)[0]
    if d0 <= d1:
        return d0, 13.0 + 2.5 * math.sin(x / 31 + y / 47), 0
    return d1, 7.0 + 1.5 * math.sin(y / 23), 1


def mountains(x, y):
    """How high the mountains round the valley rise here (before terracing)."""
    north = 1.4 * max(0.0, y - (560 + 30 * math.sin(x / 61) + 10 * math.sin(x / 17)))
    west = 1.5 * max(0.0, -x - (470 + 18 * math.sin(y / 43)))
    east = 1.2 * max(0.0, x - (330 + 25 * math.sin(y / 51)))
    south = 1.1 * max(0.0, -y - (340 + 20 * math.sin(x / 37)))
    return north, west, east, south


# The mountainside behind the mountain road: terraced shelves rising north (round where
# the first version's climb ran, at y = 439 and 503), steeper in the west.
LEG1_Y, LEG2_Y = 439.0, 503.0


def mountainside(x, y, floor):
    z1 = 12.0 + (x + 311) * 0.06
    z2 = 27.0 + (-142 - x) * 0.087
    t = (y - LEG1_Y) / (LEG2_Y - LEG1_Y)
    if t < 0:
        h = lerp(floor, z1 - 1.0, sm((y - 360) / (LEG1_Y - 360)))
    elif t <= 1:
        h = lerp(z1, z2, t) - 1.0
    else:
        h = z2 - 1.0 + (y - LEG2_Y) * 0.55
    w = sm((x + 440) / 30) * sm((-40 - x) / 70)
    return lerp(floor, max(floor, h), w)


# The mountain the road winds up and the sleigh run comes down: a hill raised round those
# roads (each point of them a cone of ground, falling away 0.3 m a metre beyond 12 m),
# kept on a grid so it's quick to look up.
_HILL = {}


def _hill_grid():
    if _HILL:
        return _HILL
    pts = []
    d = 0.0
    P, S = STANDARD_PATH, STANDARD_SEG
    for i, (x, y, _, seg) in enumerate(P):
        if i:
            d += math.hypot(x - P[i - 1][0], y - P[i - 1][1])
        if S[8] <= d <= S[18] and (not pts or d - pts[-1][3] >= 6.0):
            pts.append((x, y, standard_road_z(d) - 0.5, d))
    x0, x1 = min(p[0] for p in pts) - 120, max(p[0] for p in pts) + 120
    y0, y1 = min(p[1] for p in pts) - 120, max(p[1] for p in pts) + 120
    cell = 4.0
    nx, ny = int((x1 - x0) / cell) + 2, int((y1 - y0) / cell) + 2
    poly = [(p[0], p[1]) for p in pts]

    def inside(px, py):
        hit = False
        for (ax, ay), (bx, by) in zip(poly, poly[1:] + poly[:1]):
            if (ay > py) != (by > py) and px < ax + (py - ay) * (bx - ax) / (by - ay):
                hit = not hit
        return hit

    grid = []
    for j in range(ny):
        row = []
        for i in range(nx):
            gx, gy = x0 + i * cell, y0 + j * cell
            h = max(z - 0.3 * max(0.0, math.hypot(gx - px, gy - py) - 12.0) for px, py, z, _ in pts)
            if inside(gx, gy):
                # Inside the loop of the mountain road: the mountain top, rising between
                # the roads to a little above them.
                ws = [(1.0 / max(1.0, (gx - px) ** 2 + (gy - py) ** 2), z) for px, py, z, _ in pts]
                w = sum(a for a, _ in ws)
                far = min(math.hypot(gx - px, gy - py) for px, py, _, _ in pts)
                h = max(h, sum(a * z for a, z in ws) / w + 0.12 * max(0.0, far - 12.0))
            row.append(h)
        grid.append(row)
    _HILL.update(x0=x0, y0=y0, cell=cell, nx=nx, ny=ny, grid=grid)
    return _HILL


def hill(x, y):
    g = _hill_grid()
    u, v = (x - g["x0"]) / g["cell"], (y - g["y0"]) / g["cell"]
    if not (0 <= u < g["nx"] - 1 and 0 <= v < g["ny"] - 1):
        return -99.0
    i, j = int(u), int(v)
    fu, fv = u - i, v - j
    G = g["grid"]
    a = lerp(G[j][i], G[j][i + 1], fu)
    b = lerp(G[j + 1][i], G[j + 1][i + 1], fu)
    return lerp(a, b, fv)


def terrace(v, step=16.0):
    if v <= 0:
        return v
    k = math.floor(v / step)
    f = v / step - k
    return (k + sm((f - 0.55) / 0.45)) * step


def land(x, y):
    """The valley without its waterways: the village floor, the forest slopes, the
    mountainside behind the mountain road, the ridge west of the creek, and the
    mountains all round."""
    h = 3.0 + 0.6 * math.sin(x / 29) * math.cos(y / 23) + 0.4 * math.sin((x - y) / 41)
    # The forest floor rises gently to the north-west.
    h += 8.0 * sm((y - 200) / 200) * sm((-x - 60) / 120)
    north, west, east, south = mountains(x, y)
    h = mountainside(x, y, h)
    h = max(h, hill(x, y))
    # A ridge west of the creek.
    ridge = sm((-x - 455) / 30) * max(0.0, (y + 40) * 0.1)
    h = max(h, 3.0 + ridge) if y > -60 else h
    hi = max(north, west, east, south)
    h += terrace(min(240.0, hi), 18.0)
    h += 40 * (0.5 + 0.5 * math.sin(x / 47 + 0.4) * math.cos(y / 37)) * sm((hi - 50) / 90)
    return h


def natural(x, y):
    h = land(x, y)
    d, hw, which = water_at(x, y)
    if d < hw + 12:
        bed = RIVER_Z if which == 0 else RIVER_Z + 0.4
        h = lerp(h, min(h, bed), sm((hw + 12 - d) / 12))
    return h


def classify(c, n, info):
    d, hw, which = water_at(c.x, c.y)
    if d < hw and c.z < RIVER_Z + 0.8:
        return ("river_ice", "ice")
    if n.z < 0.62:
        if c.z > 60 and n.z > 0.3:
            return ("summit_snow", "wall")
        return ("summit_cliff" if (int(c.z / 8) + int(c.x / 40)) % 3 else "summit_rock", "wall")
    # The village square is paved (swept cobbles round the giant tree).
    if math.hypot(c.x - TREE[0], c.y - TREE[1]) < 86 and c.z < 6:
        return ("hearth_cobble", "snow_stone")
    if info["d"] < 11:
        return ("summit_road", "packed_snow")
    return ("summit_snow", "deep_snow")


def underfloor_z(x, y):
    return min(land(x, y), natural(x, y)) - 0.35


# The back alley: it leaves the old town's street on the left (a gap between the
# cottages, just before the market chicane), sweeps through the old town between stone
# walls, flicks right and left round an icy dogleg, and bends hard left onto the finish
# street right before the line.
ALLEY_START = (-212.0, 44.0)  # on the old town's street (seg 22), heading south
ALLEY_LAYOUT = [("L", 45, 35), ("S", 140), ("R", 25, 30), ("L", 25, 30), ("S", 40), ("L", 50, 115), ("S", 10)]
ALLEY_PATH = kit.turtle(ALLEY_LAYOUT, ALLEY_START, 270.0, step=2.0)
ALLEY_W = 7.5
ALLEY_LEN = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(ALLEY_PATH, ALLEY_PATH[1:]))
# The icy dogleg (metres along the alley).
ALLEY_ICE = (150.0, 215.0)


def alley_points():
    """The alley's centre line: [(x, y, metres along)], every 2 m."""
    out = []
    d = 0.0
    for i, (x, y, _, _) in enumerate(ALLEY_PATH):
        if i:
            d += math.hypot(x - ALLEY_PATH[i - 1][0], y - ALLEY_PATH[i - 1][1])
        out.append((x, y, d))
    return out


def alley_dist(x, y):
    return _nearest(x, y, [(p[0], p[1]) for p in ALLEY_PATH[::3]])[0]


# ---------------------------------------------------------------- the course


def main():
    c = kit.Course(TRACK_ID, "Hearthglow Hollow (Ruined)" if RUIN else "Hearthglow Hollow", "hearth_ruins" if RUIN else "hearthglow")
    c.route(ROUTE, width=15.0, bank=6.0)
    snowbank = ("summit_snow", "packed_snow")
    fence = ("timber_rail", "wall")
    stone = ("hearth_stone", "wall")
    c.kinds = {
        "street": {"mat": "hearth_cobble", "shoulder": 1.4, "shoulder_mat": snowbank, "barrier": 0.7, "barrier_mat": ("summit_snow", "wall")},
        "icy": {"mat": "icy_cobble", "shoulder": 1.4, "shoulder_mat": snowbank, "barrier": 0.7, "barrier_mat": ("summit_snow", "wall")},
        "square": {"mat": "hearth_cobble", "shoulder": 2.6, "shoulder_mat": ("hearth_cobble", "snow_stone")},
        "stonebridge": {
            "mat": "hearth_cobble",
            "shoulder": 0.8,
            "shoulder_mat": ("hearth_stone", "snow_stone"),
            "barrier": 1.2,
            "barrier_mat": stone,
            "deck": 4.0,
            "deck_mat": stone,
            "ground": False,
        },
        "forest": {"mat": "summit_road", "shoulder": 1.8, "shoulder_mat": snowbank},
        "climb": {"mat": "summit_road", "shoulder": 1.2, "shoulder_mat": snowbank, "barrier": 1.0, "barrier_mat": fence},
        "trestle": {
            "mat": "plank_road",
            "shoulder": 0.6,
            "shoulder_mat": ("plank_road", "road"),
            "barrier": 1.2,
            "barrier_mat": fence,
            "deck": 2.4,
            "deck_mat": ("timber_beam", "wall"),
            "ground": False,
        },
        "summit": {"mat": "hearth_cobble", "shoulder": 1.4, "shoulder_mat": ("hearth_stone", "snow_stone"), "barrier": 1.1, "barrier_mat": stone},
        "sleighrun": {"mat": "summit_road", "shoulder": 1.6, "shoulder_mat": snowbank, "barrier": 1.2, "barrier_mat": ("summit_snow", "wall")},
        "ramp": {
            "mat": "summit_road",
            "shoulder": 0.8,
            "shoulder_mat": snowbank,
            "barrier": 1.2,
            "barrier_mat": fence,
            "deck": 5.0,
            "deck_mat": ("timber_beam", "wall"),
            "ground": False,
        },
        "landing": {"mat": "summit_road", "shoulder": 1.6, "shoulder_mat": snowbank, "barrier": 1.2, "barrier_mat": ("summit_snow", "wall")},
        "covered": {
            "mat": "plank_road",
            "shoulder": 0.8,
            "shoulder_mat": ("plank_road", "road"),
            "barrier": 1.4,
            "barrier_mat": fence,
            "deck": 3.0,
            "deck_mat": ("timber_beam", "wall"),
            "ground": False,
        },
        # Where the back alley leaves the old town's street and comes out on the finish
        # street: no snow wall on its left.
        "lane": {"mat": "hearth_cobble", "shoulder": 1.4, "shoulder_mat": snowbank},
    }
    lift = {"lift": lambda u, n: 1.5 * max(0.0, (u - (n - 10)) / 10) ** 2}
    if RUIN:
        ruin_course(c, stone)
        return

    alley = alley_points()
    alley_in = kit.s_near(c, *ALLEY_START)
    alley_out = kit.s_near(c, alley[-1][0], alley[-1][1])

    def label(smp):
        x, y, s = smp.p.x, smp.p.y, smp.s
        seg = seg_of(s)
        for lip, land_ in JUMPS:
            if lip <= s <= land_:
                return "gap"
            if lip - 30 <= s < lip:
                return "ramp"
            if land_ < s <= land_ + 30:
                return "landing"
        above = smp.p.z - natural(x, y)
        if seg in (4, 5, 6) and above > 2.5:
            return "stonebridge"
        if seg == 18 and above > 2.5:
            return "covered"
        if seg in (1, 2, 3):
            return "square"
        if 9 <= seg <= 13 and above > 4.0:
            return "trestle"
        if seg == 13:
            return "summit"
        if 9 <= seg <= 12:
            return "climb"
        if 14 <= seg <= 17:
            return "sleighrun"
        if alley_in - 10 <= s <= alley_in + 40 or alley_out - 45 <= s <= alley_out + 10:
            return "lane"
        # Icy patches in the old town's lanes.
        if seg == 24 or (seg == 28 and s < SEG[28] + 40):
            return "icy"
        return "street"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "ramp":
            specials.append((s0, s1, k, lift))
        elif k != "street":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "street", max_len=200.0))

    # The back alley: cobbles (icy round the dogleg) between low stone walls, open where
    # it leaves and joins the street (the land meets it like any road).
    def gap_to_street(p):
        return c.nearest(p[0], p[1])[1]

    walled = [k for k, p in enumerate(alley) if gap_to_street(p) > 15.0]
    w0, w1 = walled[0], walled[-1]
    z0, z1 = road_z(alley_in), road_z(alley_out)

    def run(a, b):
        return [(x, y, lerp(z0, z1, d / ALLEY_LEN) - 0.05) for x, y, d in alley[a : b + 1]]

    i0 = next(k for k, p in enumerate(alley) if p[2] >= ALLEY_ICE[0])
    i1 = next(k for k, p in enumerate(alley) if p[2] >= ALLEY_ICE[1])
    open_kw = dict(width=ALLEY_W, shoulder=0.6, shoulder_mat=("hearth_cobble", "snow_stone"))
    wall_kw = dict(open_kw, barrier=1.3, barrier_mat=stone)
    c.side_road("Alley Mouth", run(0, w0 + 2), "hearth_cobble", **open_kw, flush=True, ease=5.0)
    c.side_road("Alley 1", run(w0, i0 + 1), "hearth_cobble", **wall_kw)
    c.side_road("Alley Ice", run(i0, i1 + 1), "icy_cobble", **wall_kw)
    c.side_road("Alley 2", run(i1, w1), "hearth_cobble", **wall_kw)
    c.side_road("Alley End", run(w1 - 2, len(alley) - 1), "hearth_cobble", **open_kw, flush=True, ease=5.0)

    X0, X1, Y0, Y1 = -620, 520, -460, 720
    c.terrain("Land", X0, X1, Y0, Y1, 6.5, natural, classify, near=9.0, fade=18.0, fine=3)

    def near(fn, m=64.0):
        return lambda x, y: fn(x, y) if c.nearest(x, y)[1] < m else None

    def under(x, y):
        # Just under the land as it really is (pulled down to the road where the road is
        # cut into a slope).
        nat = natural(x, y)
        w, z = c.road_height(x, y, 9.0, 18.0, 0.2, nat)
        return min(underfloor_z(x, y), lerp(nat, z, w) - 0.6)

    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 5.0, near(under), c.lib("summit_snow", "deep_snow"))

    c.start_line()
    S = lambda i: SEG[i]  # noqa: E731
    for at in ZIPPERS:
        c.zipper(at, 0)
    for at, across in ((S(3) + 20, 0), (S(10) + 10, 3), (S(15) + 15, 0), (S(19) + 10, 0), (S(25) + 10, 0), (S(28) + 70, 0), (S(30) + 25, -3)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (S(2) + 50, -4, "blue"),
        (S(2) + 50, 4, "red"),
        (S(10) + 25, 0, "yellow"),
        (S(13) + 40, 0, "rainbow"),
        (S(17) + 30, -4, "green"),
        (S(17) + 30, 4, "blue"),
        (S(22) + 6, 0, "red"),
        (S(26) + 55, 0, "yellow"),
        (S(29) + 30, 0, "rainbow"),
    ):
        c.balloon(at, across, col)

    # A missed jump: put down on its landing.
    for lip, land_ in JUMPS:
        c.entity("respawn", **{"from": round(lip - 30, 1), "to": round(land_ + 6, 1), "at": round(land_ + 30, 1)})

    # Checkpoints: one in the middle of the stretch the alley skips, with a twin gate
    # across the alley (either counts), and none elsewhere in that stretch.
    s_in, s_out = alley_in, alley_out
    apex = (s_in + s_out) / 2
    gates = c.checkpoints(
        extra=[S(2), S(5) + 30, S(8) + 10, S(10) + 20, S(12), S(14) + 15, J[0][1] + 25, S(17) + 20, S(18) + 50, s_in - 6, apex, s_out + 4],
        avoid=[(s_in - 2, apex - 6), (apex + 6, s_out + 2)],
        height=8.0,
    )
    main_gate = min(gates.items(), key=lambda kv: abs(kv[0] - apex))[1]
    mid = len(alley) // 2
    c.alt_gate(main_gate, "alley_shortcut", [(x, y, lerp(z0, z1, d / ALLEY_LEN)) for x, y, d in alley[mid - 4 : mid + 4]], width=12.0)

    import hearthglow_scenery  # noqa: E402

    hearthglow_scenery.build(c, sys.modules[__name__])
    ter = list(c.coll("Terrain").objects)
    c.preset("sun", ter, 0.2)
    c.preset("bottoms", ter, 0.3)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish()


def ruin_course(c, stone):
    """The ruin's roads, land, gameplay and wreckage (hearthglow_ruins.py dresses it)."""
    rubble = ("ruin_rubble", "snow_stone")
    snowbank = ("summit_snow", "packed_snow")
    c.kinds.update({
        # Through the burnt riverside: packed snow over the cottages' rubble.
        "rubble": {"mat": "summit_road", "shoulder": 1.8, "shoulder_mat": rubble},
        # The alley, opened up: its cobbles, the fallen houses' rubble along its sides.
        "alley": {"mat": "hearth_cobble", "shoulder": 1.6, "shoulder_mat": rubble},
        "alley_ice": {"mat": "icy_cobble", "shoulder": 1.6, "shoulder_mat": rubble},
    })
    ice0, ice1 = SEG[8] + ALLEY_ICE[0], SEG[8] + ALLEY_ICE[1]

    def label(smp):
        s = smp.s
        seg = seg_of(s)
        if seg in (1, 2, 3):
            return "square"
        if seg in (4, 5, 6):
            return "rubble"
        if 8 <= seg <= 12:
            return "alley_ice" if ice0 <= s <= ice1 else "alley"
        if seg == 13 and s < SEG[13] + 40:
            return "alley"
        return "street"

    specials = [(s0, s1, k) for s0, s1, k in kit.runs(c, label) if k != "street"]
    c.roads(kit.plan(c, specials, "street", max_len=200.0))

    X0, X1, Y0, Y1 = -620, 520, -460, 720
    c.terrain("Land", X0, X1, Y0, Y1, 6.5, natural, classify, near=9.0, fade=18.0, fine=3)

    def under(x, y):
        nat = natural(x, y)
        w, z = c.road_height(x, y, 9.0, 18.0, 0.2, nat)
        return min(underfloor_z(x, y), lerp(nat, z, w) - 0.6) if c.nearest(x, y)[1] < 64.0 else None

    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 5.0, under, c.lib("summit_snow", "deep_snow"))
    c.start_line()
    S = lambda i: SEG[i]  # noqa: E731
    for at in ZIPPERS:
        c.zipper(at, 0)
    for at, across in ((S(3) + 20, 0), (S(5) + 45, 3), (S(9) + 80, 0), (S(12) + 10, 0), (S(14) - 2, -3)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (S(2) + 50, -4, "blue"),
        (S(2) + 50, 4, "red"),
        (S(5) + 80, 0, "yellow"),
        (S(8) + 20, 0, "rainbow"),
        (S(9) + 130, -3, "green"),
        (S(9) + 130, 3, "blue"),
        (S(13) + 60, 0, "red"),
    ):
        c.balloon(at, across, col)
    c.checkpoints(extra=[S(2), S(4), S(5) + 50, S(7), S(9) + 50, S(10), S(13), S(13) + 70], height=8.0)
    ruin_mode.DRESS(c, sys.modules[__name__])
    ter = list(c.coll("Terrain").objects)
    c.preset("sun", ter, 0.2)
    c.preset("bottoms", ter, 0.3)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish()


if __name__ == "__main__":
    main()
