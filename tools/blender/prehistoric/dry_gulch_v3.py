# Dry Gulch Ghost Town v3: the new lap (Blake's notes, 2026-10-23), dressed exactly like
# the current Dry Gulch: the same haunted town, graveyard, Hazard Ridge and its mine,
# ravine, trestles, props, light and haunt (gulch_scenery.py, gulch_town.py,
# gulch_props.py), laid along the new road. Builds its own package, dry_gulch_v3
# (?track=dry_gulch_v3); the current Dry Gulch stays as it is.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/dry_gulch_v3.py      (the bpy module)
#
# About 1.8 km (the current lap is 2.14 km), nearly all of it bends:
#
#   A  Main Street and the saloon district: north up Main Street, a drift left at the
#      square, then a tight S-chicane drifting between the buildings.
#   B  Through Boot Hill (not round it): over its knoll, flicking between the graves.
#   C  The mine approach, east along the top of town. The shortcut leaves into the mine.
#   D  The main way round: the Rickety Trestle over the glowing chasm (a broken span to
#      jump), south along the rim and down the ravine's wall in S-bends, a weave round
#      the rock pillars on the ravine floor, the hairpin round Dead Man's Rock, and up
#      out of the ravine under the mine railway's trestle, drifting back onto Main Street.
#   The Haunted Mine (the shortcut): into the portal, down the timbered tunnels, through
#   the old workings (mind the runaway ore cart), across the spectral trestle over the
#   chasm cavern (one stretch of rail broken away), out of the broken gateway onto the
#   ravine floor.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp, smooth  # noqa: E402

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


def path_at(s):
    """(x, y, heading degrees) of the layout s metres along the lap."""
    k = min(range(len(PATH)), key=lambda i: abs(_D[i] - s))
    return PATH[k][:3]


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
S = SEG

# ---------------------------------------------------------------- landmarks

SQUARE = _arc_centre(1)  # the town square, inside the first corner
_C33 = _arc_centre(33)
CHAPEL = (_C33[0] + 8.0, _C33[1] + 8.0)  # inside the last corner
WATER_TOWER = (-50.0, 46.0)  # behind Main Street's west side
GRAVEYARD = ((_seg_point(8)[0] + _seg_point(10)[0]) / 2 + 4.0, (_seg_point(8)[1] + _seg_point(11)[1]) / 2)
DEAD_MANS_ROCK = _arc_centre(28)
Z_RIDGE = 72.0  # Hazard Ridge's top

# ---------------------------------------------------------------- the land


def sm(t):
    return smooth(max(0.0, min(1.0, t)))


def _seg_d(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy + 1e-9)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy), t


# The ravine: its centre line (x, y), half-width and floor. Deep in the north (the chasm
# the Rickety Trestle crosses, glowing green), it runs south past Hazard Ridge, its floor
# rising, bends west round Dead Man's Rock and climbs to the town's level south of town.
RAVINE = [
    (130.0, 1100.0, 80.0, -30.0), (130.0, 710.0, 70.0, -30.0), (130.0, 340.0, 60.0, -28.0), (145.0, 298.0, 52.0, -26.0),
    (185.0, 225.0, 44.0, -18.0), (225.0, 160.0, 40.0, 4.0), (248.0, 106.0, 42.0, 10.5), (254.0, 10.0, 42.0, 11.0),
    (246.0, -100.0, 48.0, 11.5), (220.0, -155.0, 50.0, 12.0), (160.0, -140.0, 40.0, 16.0), (100.0, -115.0, 32.0, 23.0),
    (40.0, -95.0, 24.0, 30.0),
]
WALLW = 22.0  # how far a ravine wall runs from its rim to the floor


def ravine_q(x, y):
    """(distance from the ravine's centre line, its half-width there, its floor there,
    and which side: +1 on its outer (east, then south) side, -1 on the town's)."""
    best = None
    for a, b in zip(RAVINE, RAVINE[1:]):
        d, t = _seg_d(x, y, a[0], a[1], b[0], b[1])
        if best is None or d < best[0]:
            cross = (b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0])
            best = (d, lerp(a[2], b[2], t), lerp(a[3], b[3], t), 1.0 if cross > 0 else -1.0)
    return best


def bands(u):
    """A ravine wall, rim (0) to foot (1): sheer drops with ledges between."""
    out = 0.0
    for w, f in ((3.0, 0.32), (5.0, 0.06), (4.0, 0.3), (6.0, 0.08), (3.0, 0.2), (3.0, 0.04)):
        out += f * sm(u / w)
        u -= w
        if u <= 0:
            break
    return min(1.0, out)


def east_land(y):
    """The mesa east of the ravine: low by the trestle, higher to the south."""
    return lerp(31.5, 44.0, sm((229.0 - y) / 150.0))


def plateau(x, y):
    """The town's plateau, rolling gently, rising into low hills far out, and the higher
    mesa across the ravine."""
    h = Z_TOWN + 0.8 * math.sin(x / 53.0 + 0.4) * math.cos(y / 61.0) + 0.5 * math.sin((x + y) / 29.0)
    r = math.hypot((x + 20.0) / 1.15, y - 120.0)
    h += (16.0 + 5.0 * math.sin(x / 90.0) * math.cos(y / 70.0)) * sm((r - 420.0) / 240.0)
    d, hw, _, side = ravine_q(x, y)
    if side > 0 and d > hw - 4.0:
        k = sm((d - hw + 4.0) / 14.0) * sm((x - 60.0) / 120.0)
        h = lerp(h, east_land(y) + 1.2 * math.sin(y / 23.0 + x / 31.0), k)
    return h


def ravine_cut(x, y, top):
    d, hw, floor, _ = ravine_q(x, y)
    u = hw - d
    if u <= 0.0 or floor >= top:
        return None
    z = top - (top - floor) * bands(u * 24.0 / WALLW)
    if u > WALLW:
        z = floor + 0.4 * math.sin(x / 7.0) * math.cos(y / 9.0)
    return min(top, z)


def natural(x, y):
    """The land before it's shaped round the roads."""
    h = plateau(x, y)
    z = ravine_cut(x, y, h)
    if z is not None:
        h = z
    # Boot Hill's knoll (the lap runs over it).
    g = math.hypot(x - GRAVEYARD[0], y - GRAVEYARD[1])
    h += 4.0 * (1.0 - sm((g - 18.0) / 34.0))
    return h


# ---------------------------------------------------------------- Hazard Ridge


def _smooth_loop(pts, n=3):
    for _ in range(n):
        out = []
        for a, b in zip(pts, pts[1:] + pts[:1]):
            out.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            out.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        pts = out
    return pts


# Hazard Ridge's footprint (anticlockwise): between the mine approach, the town and the
# ravine, the old mine bored through it. Its north face drops sheer into the chasm's
# side, its east face into the ravine.
RIDGE = _smooth_loop([
    (70.0, 20.0), (130.0, 6.0), (192.0, 16.0), (220.0, 50.0), (215.0, 105.0), (185.0, 160.0), (160.0, 215.0),
    (132.0, 248.0), (80.0, 262.0), (34.0, 250.0), (50.0, 160.0), (46.0, 60.0),
], 3)
RIDGE_C = (sum(p[0] for p in RIDGE) / len(RIDGE), sum(p[1] for p in RIDGE) / len(RIDGE))


def _inside(poly, x, y):
    c = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            c = not c
        j = i
    return c


def ridge_d(x, y):
    """Signed distance to the ridge's foot: positive inside it."""
    best = 1e9
    for a, b in zip(RIDGE, RIDGE[1:] + RIDGE[:1]):
        d, _ = _seg_d(x, y, a[0], a[1], b[0], b[1])
        best = min(best, d)
    return best if _inside(RIDGE, x, y) else -best


# ---------------------------------------------------------------- the haunted mine

# The shortcut through the mine: (x, y, z) waypoints, and what each stretch is (the
# same plan as the current Dry Gulch's mine, waypoint for waypoint, so its dressing fits).
MINE = [
    (-10.0, 298.0, None, "approach"),  # (on the mine approach)
    (14.0, 284.0, 30.4, "approach"),
    (38.0, 262.0, 29.6, "tunnel"),  # the portal
    (52.0, 240.0, 28.4, "tunnel"),
    (60.0, 214.0, 27.4, "workings"),
    (74.0, 192.0, 26.8, "workings"),  # the ore-cart crossing
    (94.0, 176.0, 25.8, "tunnel"),
    (110.0, 164.0, 24.4, "tunnel"),
    (124.0, 150.0, 22.8, "trestle"),
    (144.0, 136.0, 21.0, "trestle"),
    (164.0, 126.0, 19.4, "trestle"),
    (180.0, 118.0, 17.8, "tunnel"),
    (194.0, 110.0, 15.8, "tunnel"),
    (206.0, 104.0, 14.2, "tunnel"),
    (222.0, 97.0, 13.4, "ravine"),  # the gateway
    (240.0, 87.0, 12.9, "ravine"),
    (257.0, 74.0, None, "ravine"),  # (on the ravine floor)
]
CART_AT = 5
PORTAL_AT = 2
GATEWAY_AT = 14
CAVERN = (153.0, 134.0)  # the chasm cavern's centre
WORKINGS = (74.0, 192.0)


def _catmull(pts, every=1.0):
    out = []
    n = len(pts)
    for i in range(n - 1):
        p0 = pts[max(0, i - 1)]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[min(n - 1, i + 2)]
        k = max(2, int(math.dist(p1[:2], p2[:2]) / every))
        for j in range(k):
            t = j / k
            t2, t3 = t * t, t * t * t
            out.append(tuple(
                0.5 * (2 * p1[c] + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2 + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3)
                for c in range(3)))
    out.append(tuple(pts[-1][:3]))
    return out


def mine_line(c):
    """The shortcut's centre line, dense: (x, y, z, kind) every metre, its ends on the
    race line (and leaving and joining it along it)."""
    pts = []
    for x, y, z, kind in MINE:
        if z is None:
            smp, _ = c.nearest(x, y)
            x, y, z = smp.p.x, smp.p.y, smp.p.z
        pts.append((x, y, z))
    a, _ = c.nearest(*pts[0][:2])
    b, _ = c.nearest(*pts[-1][:2])
    pa = c.at(a.s - 16.0).p
    pb = c.at(b.s + 16.0).p
    dense = _catmull([(pa.x, pa.y, pa.z)] + pts + [(pb.x, pb.y, pb.z)])
    i0 = min(range(len(dense)), key=lambda i: math.dist(dense[i][:2], pts[0][:2]))
    i1 = min(range(len(dense)), key=lambda i: math.dist(dense[i][:2], pts[-1][:2]))
    dense = dense[i0:i1 + 1]
    marks = []
    for k, (x, y, z, kind) in enumerate(MINE):
        p = pts[k]
        marks.append((min(range(len(dense)), key=lambda i: math.dist(dense[i][:2], p[:2])), kind))
    out = []
    for i, p in enumerate(dense):
        kind = marks[0][1]
        for j, kd in marks:
            if j <= i:
                kind = kd
        out.append((p[0], p[1], p[2], kind))
    return out


def mine_index(line, k):
    """Index into the dense line of MINE waypoint k."""
    x, y = MINE[k][0], MINE[k][1]
    return min(range(len(line)), key=lambda i: math.dist(line[i][:2], (x, y)))


# ---------------------------------------------------------------- materials


def classify(c, n, info):
    if ridge_d(c.x, c.y) > 5.0:
        return None  # under the ridge (its own rock stands here)
    d, hw, floor, _ = ravine_q(c.x, c.y)
    in_ravine = hw - d > 0.5
    if in_ravine and c.z < 0.0:
        return ("gulch_chasm", "abyss")  # the glowing chasm's floor: back on the road
    if n.z < 0.55:
        return (layer(c.z), "wall")
    if n.z < 0.8:
        return ("gulch_talus", "loose_sand")
    if info["d"] < info["sample"].w / 2 + 1.5:
        return ("gulch_verge", "dirt")
    if in_ravine and c.z < floor + 3.0:
        return ("gulch_wash", "dirt")
    g = math.hypot(c.x - GRAVEYARD[0], c.y - GRAVEYARD[1])
    if g < 50:
        return ("graveyard_earth", "dirt")
    return (ground_mat(c.x, c.y), "loose_sand")


def ground_mat(x, y):
    v = math.sin(x / 41.0 + 0.7) * math.cos(y / 37.0) + 0.5 * math.sin((x - y) / 23.0) + 0.25 * math.sin(x / 9.0 + y / 11.0)
    if v > 0.95:
        return "slickrock"
    if v < -0.6:
        return "red_sand"
    return "gulch_sand"


def layer(z):
    """The rock's layers, top to bottom (the canyon's sandstones, darker at night)."""
    if z > 50:
        return "strata_cream"
    if z > 26:
        return "strata_orange" if int(z / 6) % 3 else "strata_red"
    if z > 8:
        return "strata_red"
    if z > -10:
        return "strata_rust"
    return "strata_purple"


_layer = layer  # (the name canyon_scenery's rock painters look for)


def underfloor_z(x, y):
    if ridge_d(x, y) > -2.0:
        return None
    d, hw, _, _ = ravine_q(x, y)
    if hw - d > 2.0 and natural(x, y) < 0.0:
        return None  # the chasm: its own floor
    return natural(x, y) - 0.4


def abyss_z(x, y):
    """The invisible floor under the chasm: fall in anywhere and you're put back."""
    if ridge_d(x, y) > -2.0:
        return None
    d, hw, floor, _ = ravine_q(x, y)
    if hw - d < -6.0 or floor > 2.0:
        return None
    return floor - 1.0


# ---------------------------------------------------------------- where things go
# (gulch_town.py and gulch_scenery.py place the town, mineworks and haunt by these; see
# the current Dry Gulch for what each is.)

STREETS = {
    "main": (SEG[34] + 4.0 - LENGTH, SEG[1] - 6.0),
    "side": (SEG[2], SEG[7]),
    "main_back": 16.5,
    "side_back": 14.5,
    "square_back": 9.0 + 5.4,
    "dress": 11.0,
    "wagon": SEG[5] + 16.0,
}
BACK_LANES = (-170, 10, 170, 275)
WINDMILL = (-118.0, 270.0, 200.0)
GRAVE_GATE = 0.0  # facing town, off the lap
GRAVE_THROUGH = True
GRAVE_STRETCH = (SEG[7], SEG[12], 0)  # both sides of the lane through it
HEADFRAME = (96.0, 236.0, 66.0)
RAILWAY = {"adit": (128.0, 1.0), "via": (128.0, -40.0), "cross": SEG[30] + 30.0}
APPROACH = (SEG[12], SEG[16] - 10)
APPROACH_PROPS = ((-40.0, 316.0, "Winch"), (-62.0, 318.0, "Ore Heap 0"), (-22.0, 316.0, "Crate Stack 1"), (6.0, 314.0, "Ore Cart Tipped"))
NEAR = (-420.0, 480.0, -360.0, 640.0)
MINE_BOX = (0.0, 260.0, 0.0, 300.0)
CRAGS = ((100.0, 200.0, 20.0, 15.0, 94.0), (175.0, 75.0, 16.0, 14.0, 88.0), (90.0, 100.0, 16.0, 12.0, 84.0), (130.0, 45.0, 12.0, 10.0, 82.0))
LANTERNS = (SEG[7], SEG[16])
CHEVRONS = ((7, 3), (17, 3), (28, 5), (33, 3))
RAVINE_JUNK = ((SEG[22] + 20, -18, "Crate Stack 0"), (SEG[23] + 10, 19, "Winch"), (SEG[26] + 10, 18, "Ore Cart Tipped"), (SEG[27] + 30, -17, "Ore Heap 1"),
               (SEG[28] + 60, 18, "Ore Cart"), (SEG[29] + 30, -17, "Barrel 1"))
RAVINE_WHISPER = (250.0, 20.0, 14.0, 60.0)
TUMBLEWEEDS = (SEG[0] + 60, SEG[3] + 10, SEG[8] + 20, SEG[22] + 20, SEG[27] + 40, SEG[34] - 20)
BIRDS = ((140.0, 150.0), (230.0, -120.0))


def pickups(c):
    """The new lap's boosts, pickups and checkpoints (gulch_scenery adds the mine's twin
    gate)."""
    S = lambda i: SEG[i]  # noqa: E731
    # Zippers: up Main Street, out of the chicane, along the approach, onto the trestle
    # (for the broken span), down the wall, along the floor, and up out of the ravine.
    for at in (S(0) + 30, S(6) + 10, S(15) + 30, S(16) + 20, S(21) + 10, S(27) + 20, S(30) + 10):
        c.zipper(at, 0)
    for at, across in ((S(2) + 10, 0), (S(8) + 30, 0), (S(13) + 10, 0), (S(18) + 20, 0), (S(24) + 30, 0), (S(29) + 30, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in ((S(0) + 70, -4, "red"), (S(0) + 70, 4, "blue"), (S(4) + 40, 0, "green"), (S(12) + 20, 0, "yellow"),
                            (S(17) + 30, 0, "rainbow"), (S(22) + 20, -4, "red"), (S(22) + 20, 4, "blue"), (S(31) + 10, 0, "green")):
        c.balloon(at, across, col)
    # The broken span: fall in and you're put back past it.
    c.entity("respawn", **{"from": round(GAP[0] - 20, 1), "to": round(GAP[1] + 4, 1), "at": round(GAP[1] + 20, 1)})
    line = c.mine
    s_in = kit.s_near(c, *line[0][:2])
    s_out = kit.s_near(c, *line[-1][:2])
    apex = (s_in + s_out) / 2
    gates = c.checkpoints(
        extra=[S(1) + 20, S(4) + 30, S(8) + 20, S(11) + 30, s_in - 8, apex, s_out + 8, S(24) + 30, S(28) + 50, S(30) + 30],
        avoid=[(s_in - 4, apex - 8), (apex + 8, s_out + 4)],
        height=10.0,
    )
    return gates, apex


# ---------------------------------------------------------------- the course


def main():
    from dry_gulch import mine_roads

    c = kit.Course(TRACK_ID, "Dry Gulch Ghost Town", "dry_gulch")
    c.route(ROUTE, width=16.0, bank=7.0)
    verge = ("gulch_verge", "dirt")
    fence = ("fence_rail", "wall")
    timber = ("weathered_timber", "wall")
    c.kinds = {
        "street": {"mat": "gulch_road", "surface": "packed_dirt", "shoulder": 1.6, "shoulder_mat": verge},
        "trail": {"mat": "gulch_road", "surface": "packed_dirt", "shoulder": 1.8, "shoulder_mat": verge, "barrier": 1.0,
                  "barrier_mat": fence},
        # Boot Hill's lane: no fence (the cemetery's iron fence is round it).
        "lane": {"mat": "gulch_road", "surface": "packed_dirt", "shoulder": 1.6, "shoulder_mat": ("graveyard_earth", "dirt")},
        "trestle": {"mat": "plank_deck", "shoulder": 0.6, "shoulder_mat": ("plank_deck", "road"), "barrier": 1.2,
                    "barrier_mat": timber, "deck": 1.8, "deck_mat": timber, "ground": False},
        "ramp": {"mat": "plank_deck", "shoulder": 0.6, "shoulder_mat": ("plank_deck", "road"), "barrier": 1.2,
                 "barrier_mat": timber, "deck": 1.8, "deck_mat": timber, "ground": False},
        "ledge": {"mat": "gulch_road", "surface": "packed_dirt", "shoulder": 1.2, "shoulder_mat": verge, "barrier": 1.1,
                  "barrier_mat": fence, "deck": 3.0, "deck_mat": ("strata_red", "wall")},
        "ravine": {"mat": "gulch_road", "surface": "packed_dirt", "shoulder": 2.2, "shoulder_mat": verge},
        "open": {"mat": "gulch_road", "surface": "packed_dirt", "shoulder": 2.6, "shoulder_mat": verge},
    }
    line = mine_line(c)
    sa = kit.s_near(c, *line[0][:2])
    sb = kit.s_near(c, *line[-1][:2])

    def label(smp):
        s = smp.s
        seg = seg_of(s)
        if GAP[0] <= s <= GAP[1]:
            return "gap"
        if seg == 16 and GAP[0] - 10 <= s < GAP[0]:
            return "ramp"
        x, y = smp.p.x, smp.p.y
        if sa - 12 <= s <= sa + 62 or sb - 62 <= s <= sb + 12:
            return "open"
        if seg in (15, 16, 17) and natural(x, y) < smp.p.z - 5.0:
            return "trestle"
        if 18 <= seg <= 21:
            return "ledge"
        if 22 <= seg <= 29:
            return "ravine"
        if 7 <= seg <= 11:
            return "lane"
        if seg <= 6 or seg >= 33:
            return "street"
        return "trail"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "ramp":
            specials.append((s0, s1, "ramp", {"lift": lambda u, n: 0.9 * max(0.0, (u - (n - 8)) / 8) ** 2}))
        elif k != "street":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "street", max_len=200.0))
    c.mine = line
    mine_roads(c, line)

    import gulch_scenery  # noqa: E402

    gulch_scenery.build(c, sys.modules[__name__])
    c.finish()
    mine_len = sum(math.dist(a[:2], b[:2]) for a, b in zip(line, line[1:]))
    print("lap", round(c.length, 1), "mine", round(mine_len, 1), "skips", round(sb - sa, 1))


if __name__ == "__main__":
    main()
