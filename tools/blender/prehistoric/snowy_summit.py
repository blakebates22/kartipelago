# Snowy Summit Pass: Frostveil Peaks, course 2. A bright, wild ride round a frozen lake.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/snowy_summit.py      (the bpy module)
#
# A sunny, anticlockwise lap (about 2.4 km) round a frozen mountain lake, its geothermal
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
#      violet ice tunnel, 3 -> 21 m.
#   5  The Wind Canyons: west along a canyon carved into the snowy plateau, then a jump
#      over a deep gorge.
#   6  The Giant Trees: down into a half-frozen, half-thawed forest of colossal trees.
#      The road drives into the biggest (84 m across) and spirals up inside it like a
#      staircase, two whole turns, 10 -> 40 m.
#   7  The Treetop Bridges and the Summit Lookout: out of the tree high up onto plank
#      bridges between the giants (round the outside of two more), and onto the
#      lookout rock, with the whole lake below.
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
from course_kit import lerp, smooth  # noqa: E402

TRACK_ID = "snowy_summit"

# ---------------------------------------------------------------- the layout

START = (-150.0, -170.0)
HELIX_R = 28.0  # the spiral inside the great tree
HELIX_TURNS = 2
HELIX_RISE = 15.0  # metres per turn
LAYOUT = [
    ("S", 210),  # 0  1: the Frozen Bay, east across the lake
    ("L", 70, 40),  # 1  2: the Ice Archways
    ("S", 40),  # 2
    ("R", 60, 40),  # 3
    ("S", 50),  # 4  3: the travertine terraces (a geyser in the road)
    ("S", 30),  # 5  the wooden ramp
    ("S", 12),  # 6  the gap, over the geyser basin
    ("S", 50),  # 7  the landing
    ("L", 45, 90),  # 8  north along the hot shore
    ("S", 40),  # 9
    ("L", 40, 45),  # 10 4: into the glacier: the Crystal Caves
    ("R", 40, 45),  # 11
    ("S", 90),  # 12 the climb
    ("L", 45, 90),  # 13 out, west: 5: the Wind Canyons
    ("S", 50),  # 14
    ("R", 40, 45),  # 15
    ("L", 40, 45),  # 16
    ("S", 40),  # 17 the run-up
    ("S", 16),  # 18 the gap, over the gorge
    ("S", 60),  # 19 the landing
    ("L", 50, 30),  # 20 6: down into the giant forest
    ("S", 60),  # 21 straight at the great tree
    ("L", HELIX_R, 360 * HELIX_TURNS),  # 22 the spiral, inside it
    ("S", 80),  # 23 7: out onto the first bridge
    ("R", 34, 150),  # 24 round the second tree, on a ledge
    ("S", 80),  # 25 the second bridge
    ("L", 34, 120),  # 26 round the third tree
    ("S", 50),  # 27 the third bridge, to the lookout rock
    ("L", 50, 90),  # 28 the Summit Lookout
    ("S", 100),  # 29 8: the plunge down the west ridge (stretched to close the loop)
    ("R", 55, 40),  # 30
    ("L", 55, 40),  # 31
    ("S", 80),  # 32 the run-up
    ("S", 16),  # 33 the gap, off the bluff over the crevasse
    ("S", 60),  # 34 the landing, down onto the lake
    ("L", 70, 90),  # 35 the Glacier Fields
    ("S", 20),  # 36 onto the start (stretched to close the loop)
]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 29, 36, START, 0.0)
SEG = kit.segment_starts(PATH)
LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))
# The three jumps: (lip, landing) along the lap.
JUMPS = [(SEG[6], SEG[7]), (SEG[18], SEG[19]), (SEG[33], SEG[34])]
HELIX = (SEG[22], SEG[23])


def _seg_point(i):
    return next(p for p in PATH if p[3] == i)


def _arc_centre(i):
    """The centre of arc segment i."""
    x, y, h, _ = _seg_point(i)
    sg = LAYOUT[i]
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
ANCHORS = [
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
    (SEG[34], 6.0),  # ...the landing
    (SEG[35], 0.6),
    (LENGTH, 0.6),
]


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


def road_z(d, seg=None):
    if _straight(d):
        return _lin(d)
    return sum(_lin(d + k) for k in range(-15, 16, 3)) / 11


def road_w(d, seg):
    if seg in (0, 35, 36):
        return 18.0  # the open lake
    if seg in (7, 19, 34):
        return 22.0  # the landings
    if seg in (5, 17, 32):
        return 17.0  # the ramps
    if seg == 22:
        return 14.0  # the spiral
    if seg in (23, 24, 25, 26, 27):
        return 13.0  # the bridges and ledges
    if seg in (10, 11, 12):
        return 15.0
    return 15.0


ROUTE = kit.route_points_by(PATH, road_z, every=8.0, width=road_w)


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
CREVASSE = [(-330.0, -36.0), (-280.0, -31.0), (-238.0, -33.0), (-190.0, -30.0), (-150.0, -40.0)]


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
    ridge = 34.0 * sm((-x - 150) / 70) * sm((y + 10) / 160)
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
    c = kit.Course(TRACK_ID, "Snowy Summit Pass", "summit_pass")
    c.route(ROUTE, width=15.0, bank=6.0)
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

    lift = {"lift": lambda u, n: 1.5 * max(0.0, (u - (n - 10)) / 10) ** 2}

    def label(smp):
        x, y, s = smp.p.x, smp.p.y, smp.s
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

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k in ("ramp", "stoneramp", "snowramp"):
            specials.append((s0, s1, k, lift))
        elif k != "lake":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "lake", max_len=220.0))

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
    S = lambda i: SEG[i]  # noqa: E731
    # Zippers: off the start, before the terraces, on the cave's long climb, at the
    # canyon jump's run-up (for a huge leap), and down the plunge to the bluff.
    c.zipper(50, 0)
    c.zipper(S(4) - 6, 0)
    c.zipper(S(12) + 20, 0)
    c.zipper(S(17) + 4, 0)
    c.zipper(S(29) + 40, 0)
    for at, across in ((110, -4), (S(2) + 10, 0), (S(9) + 10, 0), (S(14) + 20, 2), (S(21) + 10, 0), (S(22) + 120, 0), (S(25) + 30, 0), (S(30), 0), (S(35) + 40, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (160, -4, "red"),
        (160, 4, "blue"),
        (S(3) + 10, 0, "green"),
        (S(8) + 30, 0, "yellow"),
        (S(12) + 50, 0, "rainbow"),
        (S(19) + 30, -4, "red"),
        (S(19) + 30, 4, "blue"),
        (S(22) + 240, 0, "green"),
        (S(26) + 30, 0, "yellow"),
        (S(31) + 20, 0, "rainbow"),
        (S(35) + 80, 0, "red"),
    ):
        c.balloon(at, across, col)

    # A missed jump drops you into the hot water, the gorge or the crevasse: you're put
    # down on its landing.
    for lip, land_ in JUMPS:
        c.entity("respawn", **{"from": round(lip - 40, 1), "to": round(land_ + 8, 1), "at": round(land_ + 36, 1)})

    # Gates: none inside a jump's respawn stretch (a respawn there would skip it), so one
    # just before each run-up and one just after each landing, and no more than 130 m
    # apart anywhere (the generator's own fill-ins would land in those stretches).
    J = JUMPS
    c.checkpoints(
        extra=[S(2), J[0][0] - 60, J[0][1] + 46, S(10) + 10, S(12) + 60, S(14) + 20, J[1][0] - 66, J[1][1] + 48, S(21),
               S(22) + 90, S(22) + 180, S(22) + 270, S(23) + 40, S(25) + 40, S(27), S(29) + 40, S(31), J[2][0] - 70, J[2][1] + 43, S(35) + 60],
        height=9.0,
    )

    summit_scenery.build(c, rock, t0, t1, sys.modules[__name__])
    ter = list(c.coll("Terrain").objects)
    c.preset("sun", ter + [rock], 0.25)
    c.preset("bottoms", ter, 0.4)
    kit.paint.shade_roads(c.pieces, 0.35)
    c.finish()


if __name__ == "__main__":
    main()
