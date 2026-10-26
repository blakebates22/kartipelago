# Dry Gulch Ghost Town (v3): the new lap (Blake's notes, 2026-10-23), dressed exactly like
# the first Dry Gulch (dry_gulch_v2.py): the same haunted town, graveyard, Hazard Ridge and its mine,
# ravine, trestles, props, light and haunt (gulch_scenery.py, gulch_town.py,
# gulch_props.py), laid along the new road. Builds public/tracks/dry_gulch/ (it replaced
# the first one in the Desert World on Oct 24; that one is dry_gulch_v2).
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
import ruin_mode  # noqa: E402
from course_kit import lerp, smooth  # noqa: E402

# The ruin (dry_gulch_ruins.py): the mine is gone. Its chasm cavern fell in, and Hazard
# Ridge, hollowed by the mine, slumped into it: a landslide runs from the mine approach
# (where the portal was) down through the ridge's broken middle to the ravine's bend,
# over the crack where the cavern's roof fell in. No shortcut, no trestle, no rim road;
# the town burns. Everything else (the land, the landmarks) is the course's own.
RUIN = ruin_mode.ON
TRACK_ID = "dry_gulch_ruin" if RUIN else "dry_gulch"

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
# (The standard lap: the town's landmarks are laid out from it, in the ruin too.)
STD_LAYOUT, STD_PATH, STD_SEG, STD_LENGTH = LAYOUT, PATH, SEG, LENGTH


def seg_of(s):
    k = 0
    for i, d in SEG.items():
        if d <= s:
            k = max(k, i)
    return k


def _seg_point(i):
    return next(p for p in STD_PATH if p[3] == i)


def path_at(s):
    """(x, y, heading degrees) of the (standard) layout s metres along the lap."""
    k = min(range(len(STD_PATH)), key=lambda i: abs(_D[i] - s))
    return STD_PATH[k][:3]


def _arc_centre(i):
    x, y, h, _ = _seg_point(i)
    sg = STD_LAYOUT[i]
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
    if RUIN and LAYOUT is not STD_LAYOUT:
        return _ruin_z(d, seg)
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
    if RUIN and seg >= 15:
        if seg == 23:
            return 18.0  # Main Street
        return 18.0 if 16 <= seg <= 18 else 16.0  # the landslide: wide and rough
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
    if CRACK:
        # (The ruin) the crack where the chasm cavern's roof fell in: sheer, deep.
        dc = crack_d(x, y)
        if dc < 9.0:
            h = lerp(h, -30.0, sm((9.0 - dc) / 4.0))
    return h


def crack_d(x, y):
    """(The ruin) how far (x, y) is from the crack's line."""
    return min(_seg_d(x, y, a[0], a[1], b[0], b[1])[0] for a, b in zip(CRACK, CRACK[1:])) if CRACK else 1e9


def slide_d(x, y):
    """(The ruin) how far (x, y) is from the landslide's road."""
    return min(math.hypot(x - p[0], y - p[1]) for p in SLIDE) if SLIDE else 1e9


def in_pit(x, y):
    """(The ruin) over the pit where the chasm cavern's roof fell in."""
    return bool(CRACK) and ((x - CAVERN[0]) / 36.0) ** 2 + ((y - CAVERN[1]) / 28.0) ** 2 < 1.0


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


def _near_mine(x, y):
    """Close to the mine's line (a tunnel, the workings or the cavern)?"""
    if math.hypot(x - CAVERN[0], y - CAVERN[1]) < 60 or math.hypot(x - WORKINGS[0], y - WORKINGS[1]) < 34:
        return True
    pts = [(p[0], p[1]) for p in MINE if p[2] is not None]
    return any(_seg_d(x, y, a[0], a[1], b[0], b[1])[0] < 14.0 for a, b in zip(pts, pts[1:]))


def classify(c, n, info):
    # Under the ridge its own rock stands, so no land there; only so far in as its
    # fluted foot can reach (10 m), except along the mine, where nothing may block it.
    rd = ridge_d(c.x, c.y)
    if RUIN and slide_d(c.x, c.y) < 34.0:
        # The landslide through the ridge's broken middle: land, the crack's abyss.
        if crack_d(c.x, c.y) < 6.0 and c.z < -6.0:
            return ("gulch_chasm", "abyss")
        if n.z < 0.55:
            return (layer(c.z), "wall")
        if info["d"] < info["sample"].w / 2 + 1.5:
            return ("gulch_talus", "loose_sand")
        return ("gulch_talus" if n.z < 0.9 else "red_sand", "loose_sand")
    if RUIN and (in_pit(c.x, c.y) or crack_d(c.x, c.y) < 9.0) and rd > -10.0:
        return None  # the pit and the crack: open down to the chasm
    if rd > 10.0 or (rd > 5.0 and _near_mine(c.x, c.y)):
        return None
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
    if RUIN and (crack_d(x, y) < 9.0 or in_pit(x, y)):
        return None
    if ridge_d(x, y) > -2.0 and not (RUIN and slide_d(x, y) < 30.0):
        return None
    d, hw, _, _ = ravine_q(x, y)
    if hw - d > 2.0 and natural(x, y) < 0.0:
        return None  # the chasm: its own floor
    return natural(x, y) - 0.4


def abyss_z(x, y):
    """The invisible floor under the chasm: fall in anywhere and you're put back (right
    up under the ridge's foot too, where the chasm's wall meets it; in the ruin, under
    the crack and the pit where the cavern's roof fell in)."""
    if RUIN and (crack_d(x, y) < 10.0 or in_pit(x, y)):
        return -31.0
    if ridge_d(x, y) > 8.0:
        return None
    d, hw, floor, _ = ravine_q(x, y)
    if hw - d < -14.0 or floor > 2.0:
        return None  # (well out past the chasm's rim, so no gap where its wall comes down)
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


# ---------------------------------------------------------------- the ruin's lap

CRACK = []  # the ruin: [(x, y)] down the crack where the chasm cavern's roof fell in
SLIDE = []  # the ruin: [(x, y, z)] along the landslide's road
if RUIN:
    # The course's own lap through town, Boot Hill and along the mine approach (0-14);
    # then where the portal was, down the landslide through the ridge's broken middle
    # (15-17) to the ravine's bend (18), and the course's own climb out of it into town
    # (19-23).
    LAYOUT = STD_LAYOUT[:15] + [
        ("S", 52),  # 15 along the approach to where the portal was (closes the loop)
        ("R", 80, 60),  # 16 over the lip, down into the slide...
        ("S", 338),  # 17 ...down through the ridge, over the crack (closes the loop)
        ("R", 50, 120),  # 18 round at the foot, into the ravine's bend
    ] + list(STD_LAYOUT[30:])
    LAYOUT, PATH = kit.close_turtle(LAYOUT, 15, 17, START, 90.0)
    SEG = kit.segment_starts(PATH)
    LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))
    _RD = [0.0]
    for _a, _b in zip(PATH, PATH[1:]):
        _RD.append(_RD[-1] + math.hypot(_b[0] - _a[0], _b[1] - _a[1]))
    # The crack: where the slide passes nearest the cavern, from the cavern's middle out
    # past the road. 12 m to jump, downhill.
    _k = min((i for i, p in enumerate(PATH) if p[3] == 17), key=lambda i: math.hypot(PATH[i][0] - CAVERN[0], PATH[i][1] - CAVERN[1]))
    _px, _py = PATH[_k][0], PATH[_k][1]
    _ux, _uy = _px - CAVERN[0], _py - CAVERN[1]
    _ul = math.hypot(_ux, _uy)
    CRACK = [(CAVERN[0] + _ux * f, CAVERN[1] + _uy * f) for f in [i / 10 for i in range(0, 11)] + [(_ul + 10 * j) / _ul for j in (1, 2, 3)]]
    GAP = (_RD[_k] - 6.0, _RD[_k] + 6.0)
    HEIGHT = dict(HEIGHT)
    HEIGHT.update({15: 30.5, 16: 30.0, 17: 29.0, 18: 16.0, 19: 16.0, 20: 22.0, 21: 25.5, 22: 28.5, 23: 30.0})
    CRESTS = {k: v for k, v in CRESTS.items() if k < 15}
    CRESTS.update({19: (1, 1.0)})
    STREETS = dict(STREETS, main=(SEG[23] + 4.0 - LENGTH, SEG[1] - 6.0))


def _ruin_z(d, seg):
    """The ruin's road: down the landslide in humps of fallen rock, over the crack, round
    at its foot; elsewhere the course's own."""
    if 16 <= seg <= 18:
        a, b = SEG[16], SEG[19]
        t = (d - a) / (b - a)
        z = lerp(HEIGHT[16], HEIGHT[19], smooth(t))
        # Humps of the slide's debris (not near the crack).
        if GAP[0] - 20 > d or d > GAP[1] + 20:
            z += 1.5 * math.sin(t * math.pi * 7) ** 2 * (1 - t) ** 0.5
        # The crack: a kicker up to the lip, the far side a little lower.
        if GAP[0] - 10 <= d < GAP[0]:
            z += 0.6 * smooth((d - (GAP[0] - 10)) / 10)
        elif GAP[0] <= d <= GAP[1]:
            z += lerp(0.6, -1.0, (d - GAP[0]) / (GAP[1] - GAP[0]))
        elif GAP[1] < d <= GAP[1] + 12:
            z -= 1.0 * (1 - smooth((d - GAP[1]) / 12))
        return z
    a, b = SEG[seg], SEG.get(seg + 1, LENGTH)
    t = (d - a) / max(1e-6, b - a)
    z = lerp(HEIGHT[seg], HEIGHT.get(seg + 1, HEIGHT[0]), smooth(t))
    if seg in CRESTS:
        n, h = CRESTS[seg]
        z += h * math.sin(t * math.pi * n) ** 2
    return z


if RUIN:
    ROUTE = kit.route_points_by(PATH, road_z, every=8.0, width=road_w)
    S = SEG
    for _i, (_x, _y, _h, _sg) in enumerate(PATH):
        if 16 <= _sg <= 18 and (not SLIDE or math.hypot(_x - SLIDE[-1][0], _y - SLIDE[-1][1]) >= 6.0):
            SLIDE.append((_x, _y, road_z(_RD[_i], _sg)))
    TUMBLEWEEDS = (S[0] + 60, S[3] + 10, S[8] + 20, S[17] + 100, S[17] + 260, S[23] - 20)


def ruin_pickups(c):
    """The ruin's boosts, pickups, respawn and checkpoints (no mine, no twin gate)."""
    S = SEG
    for at in (S[0] + 30, S[6] + 10, S[15] + 20, S[17] + 40, GAP[0] - 30, S[19] + 10):
        c.zipper(at, 0)
    for at, across in ((S[2] + 10, 0), (S[8] + 30, 0), (S[13] + 10, 0), (S[17] + 150, 0), (S[17] + 260, -3), (S[20] + 10, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in ((S[0] + 70, -4, "red"), (S[0] + 70, 4, "blue"), (S[4] + 40, 0, "green"), (S[12] + 20, 0, "yellow"),
                            (S[16] + 30, 0, "rainbow"), (S[17] + 230, -4, "red"), (S[17] + 230, 4, "blue"), (S[20] + 20, 0, "green")):
        c.balloon(at, across, col)
    c.entity("respawn", **{"from": round(GAP[0] - 20, 1), "to": round(GAP[1] + 4, 1), "at": round(GAP[1] + 20, 1)})
    gates = c.checkpoints(
        extra=[S[1] + 20, S[4] + 30, S[8] + 20, S[11] + 30, S[15] + 20, S[17] + 60, GAP[1] + 20, S[17] + 250, S[18] + 60, S[20] + 20],
        height=10.0,
    )
    return gates, None


def pickups(c):
    """The new lap's boosts, pickups and checkpoints (gulch_scenery adds the mine's twin
    gate)."""
    if RUIN:
        return ruin_pickups(c)
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
    from dry_gulch_v2 import mine_roads

    c = kit.Course(TRACK_ID, "Dry Gulch Ghost Town (Ruined)" if RUIN else "Dry Gulch Ghost Town", "gulch_ruins" if RUIN else "dry_gulch")
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
    if RUIN:
        ruin_course(c)
        return
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


def ruin_course(c):
    """The ruin's roads (dry_gulch_ruins.py builds the land, the town and the wreckage)."""
    c.kinds["slide"] = {"mat": "gulch_road", "surface": "packed_dirt", "shoulder": 2.6, "shoulder_mat": ("gulch_talus", "loose_sand")}

    def label(smp):
        s = smp.s
        seg = seg_of(s)
        if GAP[0] <= s <= GAP[1]:
            return "gap"
        if 16 <= seg <= 18:
            return "slide"
        if 19 <= seg <= 20:
            return "ravine"
        if 7 <= seg <= 11:
            return "lane"
        if seg <= 6 or seg >= 22:
            return "street"
        return "trail"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k != "street":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "street", max_len=200.0))
    ruin_mode.DRESS(c, sys.modules[__name__])
    c.finish()
    print("lap", round(c.length, 1))


if __name__ == "__main__":
    main()
