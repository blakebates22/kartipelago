# Hearthglow Hollow: Frostveil Peaks, course 3. A Christmas village on a snowy evening.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/hearthglow_hollow.py      (the bpy module)
#
# A short, twisting lap (about 1.7 km) through a magical alpine village at twilight, all
# decorated for Christmas, and up the mountain above it (the version before is kept as
# hearthglow_hollow_v2):
#
#   A  The Village Square: from the start, under a great wooden Christmas arch, round the
#      giant Christmas tree in a sweep of curves, past the frozen fountain, stalls,
#      snowmen and presents (drive into a present: it bursts into confetti, and boosts
#      you like a blue balloon).
#   B  The Frozen River Crossing: north over an arched stone bridge above the frozen
#      river, and out of the village.
#   C  The Mountain Road: winding up through the lit pines in tight S-bends, giant
#      snowballs rolling across on a fixed beat, to the bell tower at the summit.
#   D  The Sleigh Run: a plunge down the far side, a jump, a sleigh crossing on a fixed
#      beat, and a chain of S-bends down to the river.
#   E  The Covered Bridge and the Village Return: through the lantern-lit covered bridge,
#      down the west lane, along the bottom lane and a last drift onto the finish
#      street. Or, for the brave: up a hidden ramp in an alley off the west lane, along
#      the rooftops (two gaps to clear, and a long drop if you slip) and off the last
#      roof onto the finish street just before the line.
#
# Every corner is a 32-60 m arc. Saves tracks-src/hearthglow_hollow.blend and exports
# public/tracks/hearthglow_hollow/. The scenery is hearthglow_scenery.py, built from
# the kit in hearthglow_props.py.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp, smooth  # noqa: E402

TRACK_ID = "hearthglow_hollow"

# ---------------------------------------------------------------- the layout

START = (0.0, -75.0)
LAYOUT = [
    ("S", 16),  # 0  the start line, right before the square
    ("R", 40, 40),  # 1  A: into the square...
    ("L", 50, 120),  # 2  ...round the giant tree...
    ("R", 45, 80),  # 3  ...and out, north
    ("S", 30),  # 4  B: the street to the bridge
    ("S", 60),  # 5  the stone bridge over the frozen river
    ("S", 20),  # 6
    ("L", 40, 60),  # 7  C: out of the village and up into the pines...
    ("S", 30),  # 8  the first snowball crossing
    ("R", 35, 90),  # 9  ...winding up the mountain road in S-bends
    ("L", 35, 130),  # 10
    ("R", 35, 70),  # 11
    ("S", 20),  # 12 the second snowball crossing
    ("L", 40, 150),  # 13 the summit and the bell tower
    ("S", 100),  # 14 D: the sleigh run: the jump and the sleigh (stretched to close the loop)
    ("L", 40, 60),  # 15 a chain of S-bends down to the river
    ("R", 40, 120),  # 16
    ("L", 40, 60),  # 17
    ("S", 120),  # 18 E: through the covered bridge
    ("S", 200),  # 19 the west lane (the rooftop shortcut leaves on the left)
    ("L", 45, 90),  # 20
    ("S", 200),  # 21 the bottom lane (stretched to close the loop)
    ("L", 30, 90),  # 22 the last drift, onto the finish street
    ("S", 135),  # 23 the finish street, north to the line
]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 14, 21, START, 90.0)
SEG = kit.segment_starts(PATH)
LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))
# The jump on the sleigh run: (lip, landing).
JUMPS = [(SEG[14] + 48, SEG[14] + 62)]


def _seg_point(i):
    return next(p for p in PATH if p[3] == i)


def _arc_centre(i):
    x, y, h, _ = _seg_point(i)
    sg = LAYOUT[i]
    a = math.radians(h + (90 if sg[0] == "L" else -90))
    return (x + sg[1] * math.cos(a), y + sg[1] * math.sin(a))


TREE = _arc_centre(2)  # the giant Christmas tree, in the middle of the square
SUMMIT = _arc_centre(13)  # the bell tower stands inside the summit turn

# Heights along the lap (metres along it, height); the road eases between them.
J = JUMPS
ANCHORS = [
    (0.0, 3.0),
    (SEG[1], 3.0),
    (SEG[2], 2.0),  # down into the square
    (SEG[3], 2.0),
    (SEG[4], 2.6),
    (SEG[5], 4.2),  # the stone bridge, arched over the river
    (SEG[5] + 30, 5.0),
    (SEG[6], 4.2),
    (SEG[7], 4.0),
    (SEG[9], 9.0),  # the mountain road
    (SEG[10], 12.5),
    (SEG[11], 18.5),
    (SEG[13], 24.0),
    (SEG[14], 26.0),  # the summit
    (J[0][0], 21.5),  # the jump's lip
    (J[0][1], 17.0),  # ...its landing
    (SEG[15], 14.0),
    (SEG[17], 8.0),
    (SEG[18], 5.6),  # the covered bridge
    (SEG[18] + 50, 5.2),
    (SEG[19], 4.0),
    (SEG[20], 3.2),
    (SEG[22], 3.0),
    (LENGTH, 3.0),
]


def _lin(d):
    d = min(max(d, 0.0), LENGTH)
    for (d0, z0), (d1, z1) in zip(ANCHORS, ANCHORS[1:]):
        if d0 <= d <= d1:
            return lerp(z0, z1, (d - d0) / max(1e-6, d1 - d0))
    return 3.0


def road_z(d, seg=None):
    # The jumps' run-ups, gaps and landings are straight slopes; elsewhere heights ease
    # over 30 m.
    if any(lip - 34 <= d <= land + 14 for lip, land in JUMPS):
        return _lin(d)
    return sum(_lin(d + k) for k in range(-15, 16, 3)) / 11


def road_w(d, seg):
    if seg in (1, 2, 3):
        return 17.0  # the square
    if seg in (14, 15, 16, 17):
        return 18.0  # the sleigh run's broad chute
    if seg in (5, 18):
        return 14.0  # the bridges
    if seg in (8, 9, 10, 11, 12, 13):
        return 14.0  # the mountain road
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
# stone bridge (x = -57), past the north lane, south-west to meet the creek, and south
# under the covered bridge (y = -70) out of the valley.
RIVER = [(300.0, 600.0), (250.0, 470.0), (150.0, 300.0), (40.0, 180.0), (-57.0, 150.0), (-150.0, 155.0),
         (-250.0, 115.0), (-320.0, 25.0), (-345.0, -40.0), (-338.0, -70.0), (-330.0, -200.0), (-320.0, -560.0)]
# The creek: from the falls in the north mountains, south under the high trestle, down
# between the forest and the sleigh run, into the river.
CREEK = [(-350.0, 640.0), (-352.0, 560.0), (-355.0, 503.0), (-362.0, 400.0), (-365.0, 250.0), (-358.0, 100.0), (-345.0, -40.0)]
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


# The mountainside the climb crosses: shaped round its two roads (the first rising east
# at y = 439, the high road rising west at y = 503), steeper in the west.
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
    for i, (x, y, _, seg) in enumerate(PATH):
        if i:
            d += math.hypot(x - PATH[i - 1][0], y - PATH[i - 1][1])
        if SEG[7] + 20 <= d <= SEG[18] and (not pts or d - pts[-1][3] >= 6.0):
            pts.append((x, y, road_z(d) - 0.5, d))
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
    mountainside the climb crosses, the ridge the sleigh run comes down, and the
    mountains all round."""
    h = 3.0 + 0.6 * math.sin(x / 29) * math.cos(y / 23) + 0.4 * math.sin((x - y) / 41)
    # The forest floor rises gently to the north-west.
    h += 8.0 * sm((y - 200) / 200) * sm((-x - 60) / 120)
    north, west, east, south = mountains(x, y)
    h = mountainside(x, y, h)
    h = max(h, hill(x, y))
    # The ridge the sleigh run comes down, west of the creek.
    ridge = sm((-x - 380) / 30) * max(0.0, (y + 40) * 0.1)
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
    # Slip off the rooftops into the back gardens and you're put back (it's the price of
    # the shortcut).
    if info["d"] > 13 and roof_dist(c.x, c.y) < 9.0:
        return ("summit_snow", "abyss")
    if info["d"] < 11:
        return ("summit_road", "packed_snow")
    return ("summit_snow", "deep_snow")


def underfloor_z(x, y):
    return min(land(x, y), natural(x, y)) - 0.35


# The rooftop shortcut: off the west lane up a hidden ramp in an alley, along the roofs of
# a row of cottages (eaves to eaves, two gaps to clear) in a long left-hand sweep, and
# off the last roof, flying onto the finish street just before the line.
ROOF_START = (-274.0, 0.0)  # on the west lane, heading south
ROOF_LAYOUT = [("L", 30, 55), ("S", 220), ("L", 50, 90)]
ROOF_PATH = kit.turtle(ROOF_LAYOUT, ROOF_START, 270.0, step=2.0)
ROOF_Z = 10.4  # the boardwalk along the ridges (the first roofs; then a step down at each gap)
ROOF_STEP = 1.5
ROOF_RAMP = (6.0, 40.0)  # metres along the shortcut: the alley ramp up to the roofs
ROOF_GAPS = [(0.45, 5.0), (0.74, 5.0)]  # (fraction of the roofs, gap length)


def roof_points():
    """The shortcut's centre line: [(x, y, z, metres along)], every 2 m."""
    out = []
    d = 0.0
    # (The west lane's height where the shortcut leaves it.)
    z0 = road_z(SEG[19] + abs(_seg_point(19)[1] - ROOF_START[1]))
    for i, (x, y, _, _) in enumerate(ROOF_PATH):
        if i:
            d += math.hypot(x - ROOF_PATH[i - 1][0], y - ROOF_PATH[i - 1][1])
        a, b = ROOF_RAMP
        if d <= a:
            z = z0
        elif d <= b:
            z = lerp(z0, ROOF_Z, smooth((d - a) / (b - a)))
        else:
            # Each roof past a gap 1.5 m lower than the last (the cottages step down the
            # lane), with a little kick at each gap's lip, so a kart at speed clears it.
            z = ROOF_Z
            for g0, g1 in roof_gaps():
                if d >= g1:
                    z -= ROOF_STEP
                elif g0 - 5 <= d <= g0:
                    z += 0.45 * ((d - (g0 - 5)) / 5) ** 2
        out.append((x, y, z, d))
    return out


ROOF_LEN = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(ROOF_PATH, ROOF_PATH[1:]))


def roof_gaps():
    """The gaps in the boardwalk: [(from, to)] metres along the shortcut."""
    a = ROOF_RAMP[1] + 10
    span = ROOF_LEN - 10 - a
    return [(a + span * f - g / 2, a + span * f + g / 2) for f, g in ROOF_GAPS]


def roof_dist(x, y):
    return _nearest(x, y, [(p[0], p[1]) for p in ROOF_PATH[::3]])[0]


# ---------------------------------------------------------------- the course


def main():
    c = kit.Course(TRACK_ID, "Hearthglow Hollow", "hearthglow")
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
        # The west lane where the rooftop shortcut leaves it: no snow wall on its left.
        "lane": {"mat": "hearth_cobble", "shoulder": 1.4, "shoulder_mat": snowbank},
    }
    lift = {"lift": lambda u, n: 1.5 * max(0.0, (u - (n - 10)) / 10) ** 2}

    roof_in = kit.s_near(c, *ROOF_START)
    # Where the leap off the last roof comes down on the finish street (no snow wall on
    # its left there, so you land on the road and not behind the wall).
    rx, ry, _, rh = ROOF_PATH[-1]
    roof_land = kit.s_near(c, rx + 14 * math.cos(math.radians(rh)), ry + 14 * math.sin(math.radians(rh)))

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
        if 8 <= seg <= 13 and above > 4.0:
            return "trestle"
        if seg == 13:
            return "summit"
        if 7 <= seg <= 12:
            return "climb"
        if 14 <= seg <= 17:
            return "sleighrun"
        if roof_in - 24 <= s <= roof_in + 20 or roof_land - 45 <= s <= roof_land + 15:
            return "lane"
        # Icy patches in the village lanes.
        if (seg == 19 and s > roof_in + 40) or (seg == 21 and s < SEG[21] + 50):
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

    # The rooftop shortcut: the alley ramp, then the boardwalk along the ridges in three
    # stretches (with the two gaps between), none of them meeting the land.
    pts = roof_points()
    (g1a, g1b), (g2a, g2b) = roof_gaps()
    stretches = [(0.0, ROOF_RAMP[1] + 4), (ROOF_RAMP[1], g1a), (g1b, g2a), (g2b, ROOF_LEN)]
    for k, (a, b) in enumerate(stretches):
        run = [(x, y, z) for x, y, z, d in pts if a - 0.01 <= d <= b + 0.01]
        if k == 0:
            # (Onward 4 m onto the first roof, so the ramp and the boardwalk overlap.)
            c.side_road("Rooftop Ramp", run, "plank_road", "road", width=8.0, shoulder=0.4, shoulder_mat=("plank_road", "road"),
                        deck=2.0, deck_mat=("timber_beam", "wall"), ground=False)
        else:
            c.side_road("Rooftops %d" % k, run, "plank_road", "road", width=8.0, shoulder=0.4, shoulder_mat=("plank_road", "road"),
                        deck=0.6, deck_mat=("timber_beam", "wall"), ground=False)

    X0, X1, Y0, Y1 = -620, 520, -460, 720
    c.terrain("Land", X0, X1, Y0, Y1, 6.5, natural, classify, near=9.0, fade=18.0)

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
    # Zippers: out of the square, up the mountain road, off the summit, down the S-bends,
    # out of the covered bridge and along the bottom lane.
    c.zipper(S(4) + 6, 0)
    c.zipper(S(9) + 10, 0)
    c.zipper(S(14) + 10, 0)
    c.zipper(S(16) + 40, 0)
    c.zipper(S(19) + 70, 0)
    c.zipper(S(21) + 80, 0)
    for at, across in ((S(3) + 20, 0), (S(8) + 10, 3), (S(11) + 20, 0), (S(15) + 10, 0), (S(19) + 120, 0), (S(21) + 140, 0), (S(23) + 60, -3)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (S(2) + 50, -4, "blue"),
        (S(2) + 50, 4, "red"),
        (S(8) + 20, 0, "yellow"),
        (S(12) + 10, 0, "rainbow"),
        (S(15) + 30, -4, "green"),
        (S(15) + 30, 4, "blue"),
        (S(19) + 40, 0, "red"),
        (S(21) + 60, 0, "yellow"),
        (S(23) + 40, 0, "rainbow"),
    ):
        c.balloon(at, across, col)

    # A missed jump: put down on its landing.
    for lip, land_ in JUMPS:
        c.entity("respawn", **{"from": round(lip - 30, 1), "to": round(land_ + 6, 1), "at": round(land_ + 30, 1)})

    # Checkpoints: one in the middle of the stretch the rooftops skip, with a twin gate
    # across the rooftops (either counts), and none elsewhere in that stretch.
    s_in = roof_in
    land_pt = pts[-1]
    s_out = kit.s_near(c, land_pt[0] + 30 * math.cos(math.radians(ROOF_PATH[-1][2])), land_pt[1] + 30 * math.sin(math.radians(ROOF_PATH[-1][2])))
    apex = (s_in + s_out) / 2
    gates = c.checkpoints(
        extra=[S(2), S(5) + 30, S(8) + 10, S(10) + 20, S(12), S(14) + 20, J[0][1] + 40, S(16) + 30, S(18) + 50, s_in - 6, apex, s_out + 4],
        avoid=[(s_in - 2, apex - 6), (apex + 6, s_out + 2)],
        height=8.0,
    )
    main_gate = min(gates.items(), key=lambda kv: abs(kv[0] - apex))[1]
    mid = int(len(pts) * 0.3)
    c.alt_gate(main_gate, "rooftop_shortcut", [(x, y, z) for x, y, z, _ in pts[mid - 4 : mid + 4]], width=14.0)

    import hearthglow_scenery  # noqa: E402

    hearthglow_scenery.build(c, sys.modules[__name__])
    ter = list(c.coll("Terrain").objects)
    c.preset("sun", ter, 0.2)
    c.preset("bottoms", ter, 0.3)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish()


if __name__ == "__main__":
    main()
