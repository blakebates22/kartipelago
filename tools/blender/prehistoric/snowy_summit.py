# Snowy Summit Pass: Frostveil Peaks, course 2. A bright, wild ride round a frozen lake.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/snowy_summit.py      (the bpy module)
#
# A sunny, anticlockwise lap (about 2.2 km) round a frozen mountain lake, its geothermal
# shore, a glacier, a wind-carved plateau and a forest of colossal trees:
#
#   1  The Frozen Bay: the start, on a groomed snow road straight across the frozen
#      lake, past icebergs, a pirate ship wrecked in the ice and a woolly mammoth (and
#      her calf) wandering on it.
#   2  The Ice Archways: S-bends under great natural arches of blue ice.
#   3  The Geothermal Springs: the lake's east end, melted by hot springs. A road over
#      steaming travertine terraces past geysers (one in the road: hit it as it blows
#      and it throws you into the air), a wooden ramp, and a jump over the geyser basin.
#   4  The Crystal Caves: north into the glacier, climbing through a glowing blue and
#      violet ice tunnel, 3 -> 21 m, in a double S over icy rollers.
#   5  The Wind Canyons: west along a canyon carved into the snowy plateau, then a jump
#      over a deep gorge.
#   6  The Giant Trees: down into a half-frozen, half-thawed forest of colossal trees.
#      The road drives into the biggest (84 m across) and spirals up inside it like a
#      staircase, two whole turns, 10 -> 40 m, weaving in and out as it climbs.
#   7  The Treetop Bridges and the Summit Lookout: out of the tree high up onto a swinging
#      rope bridge, then plank bridges between the giants (round the outside of two
#      more), and onto the lookout rock, with the whole lake below.
#   8  The Glacier Fields: a fast plunge down the west ridge, a jump off an icy bluff
#      over a crevasse, and a sweep across the open ice (cut across it if you dare:
#      bare ice is slippery) past the mammoth-skull ruins, back to the start.
#
# Every corner is a 28-70 m arc. Saves tracks-src/snowy_summit.blend and exports
# public/tracks/snowy_summit/. The scenery is summit_scenery.py, built from the kit in
# summit_props.py.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import ruin_mode  # noqa: E402
from course_kit import lerp, smooth  # noqa: E402

# The ruin (snowy_ruins.py): the dragons brought the great hollow tree down. It fell
# towards the start, across the forest and over the crevasse, and with it went the spiral,
# the treetop bridges and the lookout road. The lap runs in at the tree's old door, across
# its broken stump, straight through its fallen trunk like a tunnel, off the trunk's
# shattered top over the crevasse, and down onto the glacier fields. Everything else (the
# land, the landmarks) is the course's own.
RUIN = ruin_mode.ON
TRACK_ID = "snowy_summit_ruin" if RUIN else "snowy_summit"

# ---------------------------------------------------------------- the layout

START = (-38.0, -170.0)
HELIX_R = 28.0  # the spiral inside the great tree
HELIX_TURNS = 2
HELIX_RISE = 15.0  # metres per turn
# (The spiral can weave in towards the column, HELIX_WAVE metres, and climb in steps,
# HELIX_STEP: both off since it became a ride: Blake wants it a clean, fast spiral.)
HELIX_WAVE = 0.0
HELIX_STEP = 0.0
LAYOUT = [
    ("S", 99),  # 0  1: the Frozen Bay, east across the lake
    ("L", 70, 40),  # 1  2: the Ice Archways
    ("S", 40),  # 2
    ("R", 60, 40),  # 3
    ("S", 50),  # 4  3: the travertine terraces (a geyser in the road)
    ("S", 30),  # 5  the wooden ramp
    ("S", 12),  # 6  the gap, over the geyser basin
    ("S", 50),  # 7  the landing
    ("L", 45, 90),  # 8  north along the hot shore
    ("S", 52.91),  # 9  into the glacier: 4: the Crystal Caves
    ("L", 34, 80),  # 10 a double S, climbing over icy rollers...
    ("R", 37.81, 140),  # 11
    ("L", 34, 61.29),  # 12 ...and out (it ends where the old straight climb did)
    ("L", 45, 90),  # 13 out, west: 5: the Wind Canyons
    ("S", 50),  # 14
    ("R", 40, 45),  # 15
    ("L", 40, 45),  # 16
    ("S", 40),  # 17 the run-up
    ("S", 16),  # 18 the gap, over the gorge
    ("S", 45),  # 19 the landing
    ("L", 50, 30),  # 20 6: down into the giant forest
    ("S", 45),  # 21 straight at the great tree
    ("L", HELIX_R, 360 * HELIX_TURNS),  # 22 the spiral, inside it
    ("S", 52),  # 23 7: out onto the rope bridge, short, narrow and sagging
    ("R", 34, 150),  # 24 round the second tree, on a ledge
    ("S", 45),  # 25 the second bridge
    ("L", 34, 120),  # 26 round the third tree
    ("S", 30),  # 27 the third bridge, to the lookout rock
    ("L", 50, 90),  # 28 the Summit Lookout
    ("S", 100),  # 29 8: the plunge down the west ridge (stretched to close the loop)
    ("L", 35, 55),  # 30 a tight S down the ridge (drift it both ways)...
    ("R", 35, 55),  # 31 ...that swings the run home east, shortening the lake straight
    ("S", 80),  # 32 the run-up
    ("S", 16),  # 33 the gap, off the bluff over the crevasse
    ("S", 60),  # 34 the landing, down onto the lake
    ("L", 70, 90),  # 35 the Glacier Fields
    ("S", 20),  # 36 onto the start (stretched to close the loop)
]
STANDARD_LAYOUT, STANDARD_PATH = kit.close_turtle(LAYOUT, 29, 36, START, 0.0)
LAYOUT, PATH = STANDARD_LAYOUT, STANDARD_PATH
if RUIN:
    # Blake: about half as long; the great tree destroyed and fallen towards the start,
    # and we drive through it like a tunnel. The course's own lap as far as the tree's
    # door (0-21), then across the stump (22), through the trunk (23), off its broken top
    # over the crevasse (24) and round onto the old landing and the glacier fields, which
    # are the course's own (26-29: the same arc and straight home as 35-36).
    LAYOUT = STANDARD_LAYOUT[:22] + [
        ("L", 40, 25),  # 22 across the stump, lining up with the fallen trunk
        ("S", 194.27),  # 23 through the trunk, and out along its shattered top
        ("S", 16),  # 24 the gap, over the crevasse
        ("S", 8.7),  # 25 the landing, on the crown's limbs (closes the loop)
        ("L", 50, 35),  # 26 onto the old landing
        ("S", 27.0),  # 27 (closes the loop)
        ("L", 70, 90),  # 28 the Glacier Fields
        ("S", STANDARD_LAYOUT[36][1]),  # 29 onto the start
    ]
    LAYOUT, PATH = kit.close_turtle(LAYOUT, 25, 27, START, 0.0)


def _weave(path):
    """The spiral's weave: each of its points pulled in towards the tree's centre, by
    nothing at its start and end (so the doorways stay put) and the same on both turns
    (so each turn still lies right over the one below)."""
    pts = [p for p in path if p[3] == 22]
    x, y, h, _ = pts[0]
    a = math.radians(h + 90)
    cx, cy = x + HELIX_R * math.cos(a), y + HELIX_R * math.sin(a)
    out = []
    for x, y, h, i in path:
        if i == 22:
            th = math.radians(h - pts[0][2])
            r = math.hypot(x - cx, y - cy)
            k = (r - HELIX_WAVE * (1 - math.cos(3 * th)) / 2) / r
            x, y = cx + (x - cx) * k, cy + (y - cy) * k
        out.append([x, y, h, i])
    for j in range(1, len(out) - 1):
        if out[j][3] == 22:
            out[j][2] = math.degrees(math.atan2(out[j + 1][1] - out[j - 1][1], out[j + 1][0] - out[j - 1][0]))
    return [tuple(p) for p in out]


STANDARD_PATH = _weave(STANDARD_PATH)
if not RUIN:
    PATH = STANDARD_PATH
SEG = kit.segment_starts(PATH)
LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))
# The three jumps: (lip, landing) along the lap. (The ruin's last is off the fallen
# trunk's top, over the crevasse further east.)
JUMPS = [(SEG[6], SEG[7]), (SEG[18], SEG[19]), (SEG[24], SEG[25]) if RUIN else (SEG[33], SEG[34])]
HELIX = (-99.0, -98.0) if RUIN else (SEG[22], SEG[23])


def _seg_point(i, path=None):
    return next(p for p in (path or STANDARD_PATH) if p[3] == i)


def _arc_centre(i):
    """The centre of the standard lap's arc segment i (the landmarks stay put in the ruin)."""
    x, y, h, _ = _seg_point(i)
    sg = STANDARD_LAYOUT[i]
    side = 90 if sg[0] == "L" else -90
    a = math.radians(h + side)
    return (x + sg[1] * math.cos(a), y + sg[1] * math.sin(a))


TREE1 = _arc_centre(22)  # the great hollow tree
TREE2 = _arc_centre(24)
TREE3 = _arc_centre(26)
LOOKOUT = _arc_centre(28)
TREE1_R = (37.0, 42.0)  # its trunk wall: inside and outside radius at the road
TREE_R = 21.0  # the other two giants' trunks

# Heights along the lap (metres along it, height); the road eases between them.
ANCHORS = [] if RUIN else [
    (0.0, 0.6),
    (SEG[4], 0.6),
    (SEG[5], 1.4),
    (SEG[6], 3.4),  # the geyser jump's lip
    (SEG[7], 0.8),  # ...its landing
    (SEG[8], 0.9),
    (SEG[9], 3.5),
    (SEG[13], 21.0),  # out of the caves
    (SEG[14], 22.0),
    (SEG[17], 22.6),
    (SEG[18], 23.2),  # the canyon jump's lip
    (SEG[19], 15.5),  # ...its landing
    (SEG[20], 12.0),
    (SEG[22], 10.0),  # the spiral: a steady climb, 15 m a turn
    (SEG[23], 10.0 + HELIX_TURNS * HELIX_RISE),
    (SEG[24], 42.0),
    (SEG[25], 43.0),
    (SEG[26], 45.0),
    (SEG[27], 46.0),
    (SEG[28], 47.0),
    (SEG[29], 44.0),
    (SEG[33], 15.5),  # the bluff's lip
    (SEG[34], 5.0),  # ...the landing
    (SEG[35], 0.6),
    (LENGTH, 0.6),
]
if RUIN:
    # The course's own heights to the tree's door; level across the stump and through the
    # trunk (it lies on the forest floor), up its shattered top to the lip, down off the
    # crevasse onto the crown's limbs and the old landing, and the lake.
    ANCHORS = [
        (0.0, 0.6),
        (SEG[4], 0.6),
        (SEG[5], 1.4),
        (SEG[6], 3.4),
        (SEG[7], 0.8),
        (SEG[8], 0.9),
        (SEG[9], 3.5),
        (SEG[13], 21.0),
        (SEG[14], 22.0),
        (SEG[17], 22.6),
        (SEG[18], 23.2),
        (SEG[19], 15.5),
        (SEG[20], 12.0),
        (SEG[22], 10.0),
        (SEG[23], 10.4),
        (SEG[24] - 44, 11.0),
        (SEG[24], 14.5),  # the trunk's broken top: the lip
        (SEG[25], 5.5),  # ...the landing, on the crown's limbs (9 m under the lip)
        (SEG[26], 4.5),
        (SEG[27], 3.0),
        (SEG[28], 0.6),
        (LENGTH, 0.6),
    ]

# The fallen trunk (the ruin): it lies along the straight through it (segment 23), from
# just outside the stump's wall to its shattered top over the crevasse. TRUNK: (x, y) of
# the straight's start, its heading (unit vector), and where along it the trunk begins
# and ends. Its hollow is BORE wide; the road runs on the rotten floor, AXIS under its
# middle; its top is split open the last OPEN metres (only its lower half lies there).
TRUNK = None
TRUNK_BORE, TRUNK_AXIS, TRUNK_OPEN = 13.0, 8.0, 40.0
if RUIN:
    _a = _seg_point(23, PATH)
    _d = (math.cos(math.radians(_a[2])), math.sin(math.radians(_a[2])))
    _tx, _ty = TREE1[0] - _a[0], TREE1[1] - _a[1]
    _along, _lat = _tx * _d[0] + _ty * _d[1], _tx * _d[1] - _ty * _d[0]
    _out = _along + math.sqrt(max(0.0, (TREE1_R[1] + 2.0) ** 2 - _lat**2))
    TRUNK = ((_a[0], _a[1]), _d, _out + 1.0, SEG[24] - SEG[23] + 3.0)


def trunk_at(x, y):
    """(along the trunk from the straight's start, across it), or None off it."""
    if TRUNK is None:
        return None
    (ax, ay), (dx, dy), t0, t1 = TRUNK
    t = (x - ax) * dx + (y - ay) * dy
    return t, (x - ax) * dy - (y - ay) * dx


def trunk_radius(t):
    """The fallen trunk's outer radius, t metres along the straight (it tapers)."""
    (_, _, t0, t1) = TRUNK
    u = max(0.0, min(1.0, (t - t0) / (t1 - t0)))
    return lerp(33.0, 25.0, u)


def in_trunk(x, y, margin=0.0):
    p = trunk_at(x, y)
    if p is None:
        return False
    t0, t1 = TRUNK[2], TRUNK[3]
    return t0 - margin <= p[0] <= t1 + margin and abs(p[1]) < trunk_radius(p[0]) + margin


def _lin(d):
    d = min(max(d, 0.0), LENGTH)
    for (d0, z0), (d1, z1) in zip(ANCHORS, ANCHORS[1:]):
        if d0 <= d <= d1:
            return lerp(z0, z1, (d - d0) / max(1e-6, d1 - d0))
    return 0.6


def _straight(d):
    """Stretches kept as straight slopes: the jumps' run-ups, gaps and landings, and the
    spiral (so it climbs evenly and every turn clears the one below by the same)."""
    if HELIX[0] - 2 <= d <= HELIX[1] + 2:
        return True
    return any(lip - 34 <= d <= land + 14 for lip, land in JUMPS)


def _ease(t):
    return smooth(max(0.0, min(1.0, t)))


def _rollers(d, s0, s1, height, every):
    """Crests in the road between s0 and s1: one every `every` metres, `height` high,
    easing in and out at the ends (fast over them and you catch air)."""
    if not s0 < d < s1:
        return 0.0
    ease = _ease((d - s0) / 10) * _ease((s1 - d) / 10)
    return height * (0.5 - 0.5 * math.cos(math.tau * (d - s0) / every)) * ease


def bridge_sag(d):
    """The rope bridge sags in the middle (and the road with it)."""
    s0, s1 = SEG[23] + 33, SEG[24] + 2
    if not s0 < d < s1:
        return 0.0
    return -1.4 * math.sin(math.pi * (d - s0) / (s1 - s0))


def road_z(d, seg=None):
    if RUIN and d >= SEG[22]:
        # Level through the trunk (a straight slope), the lip's kick, the drop beyond.
        if d <= SEG[25] + 14:
            return _lin(d)
        return sum(_lin(d + k) for k in range(-15, 16, 3)) / 11
    if HELIX[0] <= d <= HELIX[1]:
        # The spiral's steps: four a turn (the same on each, so they stack evenly).
        turn = (HELIX[1] - HELIX[0]) / HELIX_TURNS
        ease = _ease((d - HELIX[0]) / 12) * _ease((HELIX[1] - d) / 12)
        return _lin(d) + HELIX_STEP * math.sin(math.tau * 4 * (d - HELIX[0]) / turn) * ease
    if _straight(d):
        return _lin(d)
    z = sum(_lin(d + k) for k in range(-15, 16, 3)) / 11
    # Icy rollers through the caves' S-bends, and down the plunge from the lookout.
    z += _rollers(d, SEG[10] - 4, SEG[13] - 6, 1.7, 34.0)
    if RUIN:
        return z
    z += _rollers(d, SEG[29] + 16, SEG[30] - 2, 1.6, 30.0)
    z += _rollers(d, SEG[32] + 2, SEG[33] - 40, 1.4, 28.0)
    return z + bridge_sag(d)


def road_w(d, seg):
    if RUIN and seg >= 22:
        if seg in (25, 26):
            return 22.0  # the landing
        if seg == 23 and d > SEG[24] - 34:
            return 17.0  # the ramp, up the trunk's shattered top
        return 18.0 if seg >= 27 else 15.0
    if seg in (0, 35, 36):
        return 18.0  # the open lake
    if seg in (7, 19, 34):
        return 22.0  # the landings
    if seg in (5, 17, 32):
        return 17.0  # the ramps
    if seg == 22:
        return 14.0  # the spiral
    if seg == 23 and d > SEG[23] + 32:
        return 10.0  # the rope bridge: narrow
    if seg in (23, 24, 25, 26, 27):
        return 13.0  # the bridges and ledges
    if seg in (10, 11, 12):
        return 15.0
    return 15.0


ROUTE = kit.route_points_by(PATH, road_z, every=8.0, width=road_w)


# The route's distances (along the road in 3D, round its spline) run a little ahead of
# the layout's (flat, along the turtle path): by about 12 m at the end of the lap, most of
# it climbing the spiral. MARKS pairs them up (set in main, once the route is made), so
# the layout's marks land where they belong on the road: R(d) is the route's distance at
# layout distance d, and L(s) the other way round.
MARKS = []


def _interp(v, pairs):
    if not pairs:
        return v
    if v <= pairs[0][0]:
        return pairs[0][1] + (v - pairs[0][0])
    for (a0, b0), (a1, b1) in zip(pairs, pairs[1:]):
        if a0 <= v <= a1:
            return lerp(b0, b1, (v - a0) / max(1e-6, a1 - a0))
    return pairs[-1][1] + (v - pairs[-1][0])


def R(d):
    return _interp(d, MARKS)


def L(s):
    return _interp(s, [(b, a) for a, b in MARKS])


def _match_route(c):
    """Fill MARKS: each route point's layout distance, and the route's distance where the
    road passes through it (found in 3D, so the spiral's stacked turns don't mix)."""
    from mathutils import kdtree

    tree = kdtree.KDTree(len(c.S))
    for i, smp in enumerate(c.S):
        tree.insert(smp.p, i)
    tree.balance()
    d, nxt, last = 0.0, 0.0, -1.0
    MARKS.clear()
    for i, (x, y, _, seg) in enumerate(PATH[:-1]):
        if i:
            d += math.hypot(x - PATH[i - 1][0], y - PATH[i - 1][1])
        if d >= nxt:
            _, k, _ = tree.find((x, y, road_z(d)))
            s = c.S[k].s
            if s > last:
                MARKS.append((d, s))
                last = s
            nxt += 8.0


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


# The lake: three overlapping ellipses (centre, radii). The east one is the geothermal
# end, melted (MELT): steaming turquoise water, ice floes and travertine terraces.
LAKES = [((0.0, -205.0), 272.0, 122.0), ((-200.0, -128.0), 112.0, 96.0), ((250.0, -140.0), 118.0, 84.0)]
MELT = ((252.0, -140.0), 104.0, 72.0)


def _ell(x, y, e, wob=0.0):
    (cx, cy), rx, ry = e
    a = math.atan2(y - cy, x - cx)
    k = 1 + wob * (0.06 * math.sin(3 * a + 1) + 0.04 * math.sin(7 * a + 2))
    return math.hypot((x - cx) / rx, (y - cy) / ry) / k


def lake_k(x, y):
    """Under 1 inside the lake (its shore at 1)."""
    return min(_ell(x, y, e, 1.0) for e in LAKES)


def melted(x, y):
    return _ell(x, y, MELT, 1.0) < 1.0


# The gorge: a deep slot running south from the north mountains (the canyon jump
# crosses it) and opening out into a frozen river that runs into the lake.
GORGE = [(150.0, 470.0), (141.0, 310.0), (137.0, 186.0), (128.0, 90.0), (116.0, 0.0), (108.0, -80.0)]
# The crevasse below the bluff (the last jump), running east-west.
CREVASSE = [(-330.0, -36.0), (-280.0, -31.0), (-238.0, -33.0), (-190.0, -30.0), (-150.0, -34.0), (-110.0, -33.0), (-70.0, -40.0)]


def gorge_at(x, y):
    """(distance from the gorge's centre, its half-width at the top, its bed height)."""
    d, i, (qx, qy) = _nearest(x, y, GORGE)
    if qy > 120:
        return d, 7.5 + 1.5 * math.sin(qy / 23), -14.0
    t = sm((120 - qy) / 160)
    return d, lerp(9.0, 16.0, t) + 2 * math.sin(qy / 19), lerp(-14.0, -0.2, t)


# The glacier the caves run through (the tunnel rock): an ellipse (centre, radii, turn).
GLACIER = ((348.0, 52.0), 64.0, 110.0, 0.08)
GLACIER_TOP = 84.0


def in_glacier(x, y, shrink=1.0):
    (cx, cy), rx, ry, a = GLACIER
    dx, dy = x - cx, y - cy
    u = dx * math.cos(a) + dy * math.sin(a)
    v = -dx * math.sin(a) + dy * math.cos(a)
    return (u / (rx * shrink)) ** 2 + (v / (ry * shrink)) ** 2 < 1


# The lookout rock: a flat-topped crag, the road round its top edge.
MESA = (LOOKOUT[0] - 10.0, LOOKOUT[1] + 4.0, 50.0, 47.0)  # x, y, radius, top


def terrace(v, step=16.0):
    """Mountainsides in ledges: flat shelves (where snow lies) between steep bands."""
    if v <= 0:
        return v
    k = math.floor(v / step)
    f = v / step - k
    return (k + sm((f - 0.55) / 0.45)) * step


def land(x, y):
    """The valley without the lake, the gorge or the crevasse: forest floor, the snowy
    plateau, the glacier, the west ridge and the mountains all round."""
    # The forest floor and the gentle hills round the lake.
    h = 10.0 + 1.6 * math.sin(x / 31) * math.cos(y / 27) + 0.8 * math.sin((x + y) / 17)
    # The snowy plateau the wind canyons are cut into (between the gorge and the
    # glacier), sloping down to the hot shore in the south.
    pl = sm((x - 150) / 18) * sm((y + 40) / 120)
    h = lerp(h, 44.0 + 3 * math.sin(x / 19) * math.cos(y / 23), pl)
    # The glacier and the mountains behind it in the east. (South of the glacier they
    # stand back, beyond the hot shore.)
    # They stand back behind the glacier too (it sits on the plateau, the range rising
    # beyond it), and close in north of it.
    foot = lerp(445.0, 432.0, sm((y + 40) / 60))
    foot = lerp(foot, 320.0, sm((y - 175) / 70)) + 18 * math.sin(y / 41) + 8 * math.sin(y / 13)
    east = 2.2 * max(0.0, x - foot)
    # The west ridge (the descent runs down its east side) and the peaks behind it.
    # (South of the ridge they stand back beyond the lake's west shore.)
    west_foot = lerp(335.0, 215.0, sm((y + 40) / 40)) + 14 * math.sin(y / 37)
    west = 1.6 * max(0.0, -x - west_foot)
    ridge = 34.0 * sm((-x - 80) / 70) * sm((y + 10) / 160)
    if y > -60:
        h = max(h, 10 + ridge)
    # The north mountains, behind the forest and the plateau, and the southern hills
    # beyond the lake: all one range, rising in snowy ledges to jagged summits.
    north = 330 + 30 * math.sin(x / 47) + 12 * math.sin(x / 13 + 1)
    n_rise = 1.6 * max(0.0, y - north)
    s_rise = 1.0 * max(0.0, -y - (345 + 20 * math.sin(x / 33)))
    hi = max(east, west, n_rise, s_rise)
    h += terrace(min(230.0, hi), 18.0)
    h += 45 * (0.5 + 0.5 * math.sin(x / 41 + 0.7) * math.cos(y / 33)) * sm((hi - 60) / 90)
    # The lookout rock.
    mx, my, mr, mtop = MESA
    dm = math.hypot(x - mx, y - my)
    h = max(h, lerp(h, mtop, sm((mr - dm) / 10)))
    return h


def natural(x, y):
    h = land(x, y)
    # The lake: its ice is the level at 0, the shore easing up from it. Under the melted
    # end there is water, so the bed is lower.
    k = lake_k(x, y)
    if k < 1.25:
        bed = -5.0 if melted(x, y) else 0.0
        h = lerp(h, bed, sm((1.25 - k) / 0.25)) if k > 1.0 else bed
    # The gorge.
    d, hw, bed = gorge_at(x, y)
    if d < hw + 10:
        h = lerp(h, min(h, bed), sm((hw + 10 - d) / 10))
    # The crevasse under the bluff.
    d, i, (qx, qy) = _nearest(x, y, CREVASSE)
    if d < 9 + 6:
        h = lerp(h, min(h, -16.0), sm((15 - d) / 6))
    return h


HIDE_S = [0.0, 0.0]  # the stretch of road inside the glacier (set in main)


def in_tree1(x, y, extra=0.0):
    return math.hypot(x - TREE1[0], y - TREE1[1]) < TREE1_R[0] + extra


def in_abyss(x, y, margin=0.0):
    """Over the deep gorge (north of the lake) or the crevasse."""
    d, hw, bed = gorge_at(x, y)
    if bed < -6 and d < hw + 6 + margin:
        return True
    return _nearest(x, y, CREVASSE)[0] < 12 + margin


def classify(c, n, info):
    if in_glacier(c.x, c.y, 0.8) or in_tree1(c.x, c.y, 1.5):
        return None
    smp = info["sample"]
    if RUIN and in_trunk(c.x, c.y) and info["d"] < 16:
        return ("forest_road", "dirt")  # the rotten floor inside the fallen trunk
    if HIDE_S[0] <= smp.s <= HIDE_S[1] and info["d"] < 18 and c.z > smp.p.z - 1.0:
        return None
    if c.z < -6:
        return ("summit_rock", "abyss")  # the gorge's and crevasse's floors put you back
    if lake_k(c.x, c.y) < 1.0 and c.z < 0.3:
        if melted(c.x, c.y):
            return ("sinter", "dirt")  # the bed under the hot water
        return ("lake_ice", "ice")
    if n.z < 0.62 and lake_k(c.x, c.y) < 1.0:
        return ("glacier_ice", "wall")  # the edge of the ice, round the melted end
    if n.z < 0.62:
        if c.z > 70 and n.z > 0.3:
            return ("summit_snow", "wall")  # snow plastered on the high mountains
        return ("summit_cliff" if (int(c.z / 8) + int(c.x / 40)) % 3 else "summit_rock", "wall")
    if info["d"] < 11:
        return ("summit_road", "packed_snow")
    # Round the hot springs and in the low forest the snow has melted.
    warm = _ell(c.x, c.y, MELT) < 1.35 or (c.y > 40 and c.x < 140 and c.z < 16 and (math.sin(c.x / 23) + math.cos(c.y / 19)) > -0.2)
    if warm:
        return ("sinter", "dirt") if _ell(c.x, c.y, MELT) < 1.35 else ("thaw_grass", "grass")
    return ("summit_snow", "deep_snow")


def underfloor_z(x, y):
    if in_glacier(x, y, 0.8) or in_tree1(x, y, 1.0) or in_abyss(x, y, -4.0):
        return None
    if melted(x, y) and lake_k(x, y) < 1.0:
        return None  # the hot water's surface is the floor there
    return min(land(x, y), natural(x, y)) - 0.35


def abyss_z(x, y):
    if not in_abyss(x, y, 4.0):
        return None
    return natural(x, y) - 1.5


# ---------------------------------------------------------------- the course


def main():
    c = kit.Course(TRACK_ID, "Snowy Summit Pass (Ruined)" if RUIN else "Snowy Summit Pass", "summit_ruins" if RUIN else "summit_pass")
    c.route(ROUTE, width=15.0, bank=6.0)
    _match_route(c)
    rope = ("rope_rail", "wall")
    wood = ("heartwood", "wall")
    snowbank = ("summit_snow", "packed_snow")
    c.kinds = {
        "lake": {"mat": "summit_road", "shoulder": 2.2, "shoulder_mat": snowbank},
        "terrace": {"mat": "sinter_road", "shoulder": 1.6, "shoulder_mat": ("sinter", "dirt"), "barrier": 0.6, "barrier_mat": ("sinter_rim", "wall")},
        "ramp": {
            "mat": "plank_road",
            "shoulder": 0.6,
            "shoulder_mat": ("plank_road", "road"),
            "barrier": 1.2,
            "barrier_mat": rope,
            "deck": 3.0,
            "deck_mat": wood,
            "ground": False,
        },
        "landing": {"mat": "summit_stone_road", "shoulder": 1.4, "shoulder_mat": ("sinter", "dirt")},
        "shore": {"mat": "summit_stone_road", "shoulder": 1.8, "shoulder_mat": snowbank},
        "cave": {"mat": "crystal_road", "shoulder": 3.0, "shoulder_mat": ("glacier_ice", "snow_stone")},
        "canyon": {"mat": "summit_stone_road", "shoulder": 1.4, "shoulder_mat": snowbank},
        "stoneramp": {
            "mat": "summit_stone_road",
            "shoulder": 0.6,
            "shoulder_mat": ("frost_stone", "snow_stone"),
            "barrier": 1.2,
            "barrier_mat": ("frost_stone", "wall"),
            "deck": 6.0,
            "deck_mat": ("frost_stone", "wall"),
            "ground": False,
        },
        "stonelanding": {"mat": "summit_stone_road", "shoulder": 1.2, "shoulder_mat": snowbank, "barrier": 1.0, "barrier_mat": ("frost_stone", "wall")},
        "forest": {"mat": "forest_road", "shoulder": 1.6, "shoulder_mat": ("thaw_grass", "dirt")},
        "spiral": {
            "mat": "plank_road",
            "shoulder": 0.8,
            "shoulder_mat": ("heartwood", "road"),
            "barrier": 1.4,
            "barrier_mat": wood,
            "deck": 1.6,
            "deck_mat": wood,
            "ground": False,
        },
        "bridge": {
            "mat": "plank_road",
            "shoulder": 0.5,
            "shoulder_mat": ("plank_road", "road"),
            "barrier": 1.3,
            "barrier_mat": rope,
            "deck": 0.8,
            "deck_mat": wood,
            "ground": False,
        },
        # The rope bridge out of the great tree: only its collision is a road piece (the
        # same deck and rope rails as a bridge); what you see is built plank by plank in
        # summit_scenery.rope_bridge, gaps and all.
        "ropebridge": {
            "mat": "plank_road",
            "shoulder": 0.5,
            "shoulder_mat": ("plank_road", "road"),
            "barrier": 1.3,
            "barrier_mat": rope,
            "deck": 0.8,
            "deck_mat": wood,
            "ground": False,
        },
        "ledge": {
            "mat": "plank_road",
            "shoulder": 0.6,
            "shoulder_mat": ("plank_road", "road"),
            "barrier": 1.3,
            "barrier_mat": rope,
            "deck": 2.2,
            "deck_mat": wood,
            "ground": False,
        },
        "lookout": {"mat": "summit_stone_road", "shoulder": 1.2, "shoulder_mat": ("frost_stone", "snow_stone"), "barrier": 1.1, "barrier_mat": ("frost_stone", "wall")},
        "descent": {"mat": "summit_road", "shoulder": 1.6, "shoulder_mat": snowbank, "barrier": 0.9, "barrier_mat": ("frost_stone", "wall")},
        "snowramp": {
            "mat": "summit_road",
            "shoulder": 0.8,
            "shoulder_mat": snowbank,
            "barrier": 1.2,
            "barrier_mat": ("glacier_ice", "wall"),
            "deck": 6.0,
            "deck_mat": ("glacier_ice", "wall"),
            "ground": False,
        },
        "snowlanding": {"mat": "summit_road", "shoulder": 1.6, "shoulder_mat": snowbank},
    }
    if RUIN:
        rotten = ("heartwood", "dirt")
        c.kinds.update({
            # Across the stump's floor, where the spiral began.
            "stump": {"mat": "forest_road", "shoulder": 2.0, "shoulder_mat": rotten},
            # Through the fallen trunk, on its rotten floor (its walls are the tunnel's).
            "hollow": {"mat": "forest_road", "shoulder": 1.6, "shoulder_mat": rotten},
            # Up its shattered top and out over the crevasse.
            "logramp": {
                "mat": "forest_road",
                "shoulder": 0.8,
                "shoulder_mat": rotten,
                "deck": 4.0,
                "deck_mat": ("giant_bark", "wall"),
                "ground": False,
            },
            # The landing: the crown's great limbs lying across the crevasse's far side.
            "limbs": {
                "mat": "plank_road",
                "shoulder": 0.8,
                "shoulder_mat": ("heartwood", "road"),
                "barrier": 1.2,
                "barrier_mat": ("giant_bark", "wall"),
                "deck": 4.0,
                "deck_mat": ("giant_bark", "wall"),
                "ground": False,
            },
        })

    lift = {"lift": lambda u, n: 1.5 * max(0.0, (u - (n - 10)) / 10) ** 2}

    def label(smp):
        x, y, s = smp.p.x, smp.p.y, L(smp.s)
        seg = seg_of(s)
        for k, (lip, land_) in enumerate(JUMPS):
            if lip <= s <= land_:
                return "gap"
        if seg == 5:
            return "ramp"
        if seg == 17 and s >= SEG[18] - 34:
            return "stoneramp"
        if seg == 32 and s >= SEG[33] - 34:
            return "snowramp"
        if seg == 19:
            return "stonelanding"
        if seg == 34:
            return "snowlanding"
        if seg == 7:
            return "landing"
        if seg == 4:
            return "terrace"
        if in_glacier(x, y, 1.0):
            return "cave"
        if seg == 22 or (seg == 21 and in_tree1(x, y, 6.0)) or (seg == 23 and in_tree1(x, y, 6.0)):
            return "spiral"
        if seg == 23 and s >= SEG[23] + 33:
            return "ropebridge"
        if seg in (23, 25, 27):
            return "bridge"
        if seg in (24, 26):
            return "ledge"
        if seg == 28:
            return "lookout"
        if seg in (29, 30, 31, 32):
            return "descent"
        if seg in (20, 21):
            return "forest"
        if seg in (13, 14, 15, 16, 17):
            return "canyon"
        if seg in (8, 9, 10, 11, 12):
            return "shore"
        return "lake"

    def ruin_label(smp):
        x, y, s = smp.p.x, smp.p.y, L(smp.s)
        seg = seg_of(s)
        if seg < 21 or (seg == 21 and not in_tree1(x, y, 6.0)):
            return label(smp)
        if JUMPS[2][0] <= s <= JUMPS[2][1]:
            return "gap"
        if seg in (21, 22) or (seg == 23 and in_tree1(x, y, 6.0)):
            return "stump"
        if seg == 23:
            return "logramp" if s >= SEG[24] - 34 else "hollow"
        if in_abyss(x, y, 3.0):
            return "limbs"
        if seg in (25, 26, 27):
            return "snowlanding"
        return "lake"

    specials = []
    for s0, s1, k in kit.runs(c, ruin_label if RUIN else label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k in ("ramp", "stoneramp", "snowramp", "logramp"):
            specials.append((s0, s1, k, lift))
        elif k != "lake":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "lake", max_len=220.0))
    for p in c.pieces:
        if "ropebridge" in p.name:
            p["kp_role"] = "collision"

    inside = kit.crossings(c, lambda smp: in_glacier(smp.p.x, smp.p.y, 1.0), margin=0)
    t0, t1 = max(inside, key=lambda r: r[1] - r[0])
    HIDE_S[:] = [t0 - 16, t1 + 16]

    X0, X1, Y0, Y1 = -520, 520, -480, 480
    c.terrain("Land", X0, X1, Y0, Y1, 5.5, natural, classify, near=9.0, fade=18.0)

    def near(fn, m=64.0):
        return lambda x, y: fn(x, y) if c.nearest(x, y)[1] < m else None

    def under(x, y):
        # Just under the land as it really is: where the road is cut into a slope the
        # land is pulled down to meet it, so the floor follows (never above the road, or
        # a kart coming down would land on it; never far below the land either).
        h = underfloor_z(x, y)
        if h is None:
            return None
        nat = natural(x, y)
        w, z = c.road_height(x, y, 9.0, 18.0, 0.2, nat)
        return min(h, lerp(nat, z, w) - 0.6)

    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 5.0, near(under), c.lib("summit_snow", "deep_snow"))
    c.underfloor_flat("Abyss Floor", X0, X1, Y0, Y1, 4.0, near(abyss_z), c.lib("summit_rock", "abyss"))

    import summit_scenery  # noqa: E402

    rock = summit_scenery.glacier(c, sys.modules[__name__], t0, t1)

    c.start_line()
    if RUIN:
        ruin_gameplay(c)
        wreck = ruin_mode.DRESS(c, sys.modules[__name__], rock, t0, t1)
        ter = list(c.coll("Terrain").objects)
        c.preset("sun", ter + [rock] + wreck, 0.25)
        c.preset("bottoms", ter, 0.4)
        kit.paint.shade_roads(c.pieces, 0.35)
        c.finish()
        return
    S = lambda i: R(SEG[i])  # noqa: E731
    # Zippers: off the start, before the terraces, on the cave's long climb, at the
    # canyon jump's run-up (for a huge leap), and down the plunge to the bluff.
    c.zipper(50, 0)
    c.zipper(S(4) - 6, 0)
    c.zipper(S(10) - 8, 0)  # (into the caves' rollers)
    c.zipper(S(17) + 4, 0)
    c.zipper(S(29) + 40, 0)
    # ...and two more: onto the second treetop bridge, and on the sweep home across the ice.
    c.zipper(S(25) + 4, 0)
    c.zipper(S(35) + 24, 0)
    for at, across in ((70, -4), (S(2) + 10, 0), (S(9) + 10, 0), (S(14) + 20, 2), (S(21) + 10, 0), (S(22) + 120, 0), (S(25) + 30, 0), (S(30), 0), (S(35) + 40, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (92, -4, "red"),
        (92, 4, "blue"),
        (S(3) + 10, 0, "green"),
        (S(8) + 30, 0, "yellow"),
        (S(11) + 50, 0, "rainbow"),
        (S(19) + 30, -4, "red"),
        (S(19) + 30, 4, "blue"),
        (S(22) + 240, 0, "green"),
        (S(26) + 30, 0, "yellow"),
        (S(31) + 20, 0, "rainbow"),
        (S(35) + 80, 0, "red"),
    ):
        c.balloon(at, across, col)

    # The spiral is a ride (src/game/loops.ts): in at its foot, the kart is carried up both
    # turns at full zipper speed, steering only across the road, and out at the top.
    ride = []
    s, s1 = R(HELIX[0]) + 1.0, R(HELIX[1]) - 1.0
    while s < s1:
        q = c.at(s)
        ride.append([round(v, 2) for v in c.game(q.p.x, q.p.y, q.p.z)] + [round(q.bank, 2)])
        s += 2.0
    q = c.at(s1)
    ride.append([round(v, 2) for v in c.game(q.p.x, q.p.y, q.p.z)] + [round(q.bank, 2)])
    # (Much faster than a zipper, 38 m/s; the boost runs out 60 m from the top and the
    # ride eases down to 26 m/s, so you come out onto the rope bridge fast but in control.)
    c.entity("ride", id="tree_spiral", points=ride, width=13.0, minSpeed=38.0, outSpeed=26.0, commit=0.0, boostMult=1.75,
             boostSec=round((R(HELIX[1]) - R(HELIX[0]) - 60.0) / 38.0, 1), gravity=0.0)

    # A missed jump drops you into the hot water, the gorge or the crevasse: you're put
    # down on its landing.
    for lip, land_ in JUMPS:
        lip, land_ = R(lip), R(land_)
        c.entity("respawn", **{"from": round(lip - 40, 1), "to": round(land_ + 8, 1), "at": round(land_ + 36, 1)})

    # Gates: none inside a jump's respawn stretch (a respawn there would skip it), so one
    # just before each run-up and one just after each landing, and no more than 130 m
    # apart anywhere (the generator's own fill-ins would land in those stretches).
    J = [(R(a), R(b)) for a, b in JUMPS]
    c.checkpoints(
        extra=[S(2), J[0][0] - 60, J[0][1] + 46, S(10) + 10, S(11) + 70, S(14) + 20, J[1][0] - 66, J[1][1] + 48, S(21),
               S(22) + 90, S(22) + 180, S(22) + 270, S(23) + 40, S(25) + 40, S(27), S(29) + 40, S(31), J[2][0] - 70, J[2][1] + 43, S(35) + 60],
        height=9.0,
    )

    summit_scenery.build(c, rock, t0, t1, sys.modules[__name__])
    ter = list(c.coll("Terrain").objects)
    c.preset("sun", ter + [rock], 0.25)
    c.preset("bottoms", ter, 0.4)
    kit.paint.shade_roads(c.pieces, 0.35)
    c.finish()


def ruin_gameplay(c):
    """The ruin's zippers, items, respawns and checkpoints: the course's own to the tree,
    then through the trunk and on the glacier fields (where the course's own were)."""
    S = lambda i: R(SEG[i])  # noqa: E731
    # (And one up the trunk's shattered top, for the leap over the crevasse.)
    for at in (50, S(4) - 6, S(10) - 8, S(17) + 4, S(23) + 70, S(24) - 38, S(28) + 24):
        c.zipper(at, 0)
    for at, across in ((70, -4), (S(2) + 10, 0), (S(9) + 10, 0), (S(14) + 20, 2), (S(21) + 10, 0), (S(23) + 120, 0), (S(28) + 40, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (92, -4, "red"),
        (92, 4, "blue"),
        (S(3) + 10, 0, "green"),
        (S(8) + 30, 0, "yellow"),
        (S(11) + 50, 0, "rainbow"),
        (S(19) + 30, -4, "red"),
        (S(19) + 30, 4, "blue"),
        (S(23) + 40, 0, "green"),
        (S(26) + 10, 0, "yellow"),
        (S(28) + 80, 0, "red"),
    ):
        c.balloon(at, across, col)
    for lip, land_ in JUMPS:
        lip, land_ = R(lip), R(land_)
        c.entity("respawn", **{"from": round(lip - 40, 1), "to": round(land_ + 8, 1), "at": round(land_ + 36, 1)})
    J = [(R(a), R(b)) for a, b in JUMPS]
    c.checkpoints(
        extra=[S(2), J[0][0] - 60, J[0][1] + 46, S(10) + 10, S(11) + 70, S(14) + 20, J[1][0] - 66, J[1][1] + 48, S(21),
               S(23) + 50, J[2][0] - 66, J[2][1] + 40, S(28) + 60],
        height=9.0,
    )


if __name__ == "__main__":
    main()
