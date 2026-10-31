# The first Dry Gulch, kept playable as dry_gulch_v2 (the new lap, dry_gulch.py, took
# its place on Oct 24).
# Dry Gulch Ghost Town: Desert World, course 3. A haunted frontier mining town by night.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/dry_gulch.py      (the bpy module)
#
# A lap of about 2.2 km (around 90 s) under an enormous full moon. Dry Gulch stands on a
# red-rock plateau. East of town rises Hazard Ridge, with the old mine bored into it; past
# the ridge a ravine drops into a deep chasm that glows green from below. Every lantern in
# town is still burning, though nobody has lived here for years.
#
#   1  Haunted Main Street: the start, on the wide main street (the saloon, the general
#      store and the hotel either side, the water tower beyond, the ridge and the mine
#      glowing behind the roofs), north to the town square...
#   2  The Saloon District: left at the square past the saloon, then drifting S-bends
#      west through the commercial streets (boardwalks, the sheriff's office, an
#      abandoned wagon) and out of town.
#   3  Graveyard Bend: one broad sweeping bend round the cemetery on its knoll, the moon
#      straight ahead.
#   4  The Mine Approach: east along the north edge of town towards Hazard Ridge, the
#      green-lit Hazard Mine portal on the right. The shortcut turns off into it.
#   5  The Moonlit Canyon: the long Rickety Trestle over the glowing chasm, then south
#      down the ravine's east wall, part of it on timber trestles over the drop.
#   6  The Lower Ravine: along the ravine floor (green fissures, old adits, rails), where
#      the shortcut rejoins, and round Dead Man's Rock...
#   7  The Final Return: up out of the ravine under the mine railway's trestle, into
#      town from the south, one last broad corner onto Main Street.
#
#   The Haunted Mine (the shortcut): into the portal, down through the timbered tunnels,
#   across the ore-cart crossing in the old workings (a runaway cart rattles across it on
#   a beat), over the spectral trestle above the glowing chasm, and up and out through
#   the broken gateway onto the ravine floor.
#
# Saves tracks-src/dry_gulch.blend and exports public/tracks/dry_gulch/. The scenery is
# gulch_scenery.py (the land, the ridge and the mine, the trestles, the light, the
# gameplay) and gulch_town.py (the town, the graveyard, the mineworks), built from the
# kit in gulch_props.py.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp, smooth  # noqa: E402

TRACK_ID = "dry_gulch_v2"

# ---------------------------------------------------------------- the layout

START = (0.0, 0.0)
LAYOUT = [
    ("S", 120),  # 0  1: Main Street, north
    ("L", 60, 90),  # 1  2: left at the town square, past the saloon
    ("S", 40),  # 2
    ("R", 55, 50),  # 3  the dusty drift: S-bends through the commercial streets
    ("L", 55, 50),  # 4
    ("S", 45),  # 5  the side street west, out of town
    ("R", 105, 180),  # 6  3: Graveyard Bend
    ("S", 260),  # 7  4: the mine approach, east (stretched to close the lap)
    ("S", 150),  # 8  5: the Rickety Trestle over the chasm
    ("R", 60, 90),  # 9  south along the east rim
    ("S", 150),  # 10 down the ravine's east wall
    ("R", 120, 30),  # 11 sweeping down onto the ravine floor
    ("L", 120, 30),  # 12
    ("S", 250),  # 13 6: the lower ravine, south (stretched to close the lap)
    ("R", 70, 90),  # 14 round Dead Man's Rock, west
    ("S", 140),  # 15 7: up out of the ravine, under the railway trestle
    ("R", 70, 90),  # 16 the last broad corner onto Main Street
    ("S", 50),  # 17 the finish straight
]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 7, 13, START, 90.0)
SEG = kit.segment_starts(PATH)
LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))
_D = [0.0]
for _a, _b in zip(PATH, PATH[1:]):
    _D.append(_D[-1] + math.hypot(_b[0] - _a[0], _b[1] - _a[1]))


def _seg_point(i):
    return next(p for p in PATH if p[3] == i)


def _seg_points(i):
    return [p for p in PATH if p[3] == i]


def _arc_centre(i):
    x, y, h, _ = _seg_point(i)
    sg = LAYOUT[i]
    a = math.radians(h + (90 if sg[0] == "L" else -90))
    return (x + sg[1] * math.cos(a), y + sg[1] * math.sin(a))


def path_at(s):
    """(x, y, heading degrees) of the layout s metres along the lap."""
    k = min(range(len(PATH)), key=lambda i: abs(_D[i] - s))
    return PATH[k][:3]


SQUARE = _arc_centre(1)  # the town square, inside the first corner
_C16 = _arc_centre(16)
CHAPEL = (_C16[0] + 6.0, _C16[1] + 16.0)  # inside the last corner, by the ravine's rim
WATER_TOWER = (52.0, 42.0)  # behind Main Street's east side
_C6 = _arc_centre(6)
GRAVEYARD = (_C6[0] - 42.0, _C6[1])  # the cemetery, on its knoll inside Graveyard Bend, close by the road
DEAD_MANS_ROCK = _arc_centre(14)

# ---------------------------------------------------------------- heights

Z_TOWN = 30.0  # the town's plateau
Z_RIDGE = 72.0  # Hazard Ridge's top
Z_BRIDGE = 32.0
S = SEG
ANCHORS = [
    (0.0, Z_TOWN),
    (S[1] + 40, Z_TOWN),
    (S[6], Z_TOWN + 0.5),
    (S[6] + 165, 32.5),  # up onto the graveyard's knoll
    (S[7] + 60, 32.0),
    (S[8] - 40, Z_BRIDGE),
    (S[9] + 50, Z_BRIDGE),  # the trestle, dead level
    (S[10], 31.0),
    (S[11], 19.0),  # down the east wall
    (S[12], 13.0),
    (S[13], 11.5),  # the ravine floor
    (S[14], 12.5),
    (S[15], 14.5),
    (S[16] - 10, 28.5),  # up out of the ravine
    (S[16] + 60, Z_TOWN),
    (LENGTH, Z_TOWN),
]
LEVEL = [(S[8] - 40, S[9] + 50)]


def _lin(d):
    d = min(max(d, 0.0), LENGTH)
    for (d0, z0), (d1, z1) in zip(ANCHORS, ANCHORS[1:]):
        if d0 <= d <= d1:
            return lerp(z0, z1, (d - d0) / max(1e-6, d1 - d0))
    return Z_TOWN


def road_z(d, seg=None):
    """The road's height d metres along the lap: the anchors, eased over 30 m (dead
    level across the trestle)."""
    for a, b in LEVEL:
        if a <= d <= b:
            return _lin(d)
    return sum(_lin(d + k) for k in range(-15, 16, 3)) / 11


def road_w(d, seg):
    if seg in (0, 17):
        return 20.0  # Main Street: room for the pack
    if seg in (2, 3, 4, 5):
        return 16.0  # the commercial streets
    if seg in (8,):
        return 15.0  # the trestle
    if seg in (10, 11):
        return 16.0  # the ledge
    return 18.0


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


def _seg_d(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy + 1e-9)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy), t


# The ravine: its centre line (x, y), half-width and floor. Deep in the north (the chasm
# the Rickety Trestle crosses, glowing green), it runs south past Hazard Ridge, its floor
# rising, bends west round Dead Man's Rock and climbs to the town's level south of town.
RAVINE = [
    (175.0, 1400.0, 90.0, -30.0),
    (178.0, 700.0, 80.0, -28.0),
    (180.0, 470.0, 64.0, -26.0),
    (205.0, 405.0, 58.0, -24.0),
    (262.0, 352.0, 52.0, -16.0),
    (282.0, 300.0, 48.0, -6.0),
    (272.0, 232.0, 50.0, 4.0),
    (258.0, 150.0, 68.0, 9.5),
    (262.0, 60.0, 64.0, 10.5),
    (262.0, -30.0, 60.0, 11.5),
    (228.0, -100.0, 54.0, 13.0),
    (150.0, -128.0, 42.0, 18.0),
    (80.0, -124.0, 34.0, 26.5),
    (25.0, -112.0, 24.0, 31.0),
]
WALLW = 24.0  # how far a ravine wall runs from its rim to the floor


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
    return lerp(31.5, 44.0, sm((360.0 - y) / 150.0))


def plateau(x, y):
    """The land before the ravine is cut into it: the town's plateau, rolling gently,
    rising into low hills far out, and the higher mesa across the ravine."""
    h = Z_TOWN + 0.8 * math.sin(x / 53.0 + 0.4) * math.cos(y / 61.0) + 0.5 * math.sin((x + y) / 29.0)
    r = math.hypot((x + 60.0) / 1.15, y - 180.0)
    h += (16.0 + 5.0 * math.sin(x / 90.0) * math.cos(y / 70.0)) * sm((r - 470.0) / 260.0)
    # Across the ravine (east of it, and south of its west arm): the mesa.
    d, hw, _, side = ravine_q(x, y)
    if side > 0 and d > hw - 4.0:
        k = sm((d - hw + 4.0) / 14.0) * sm((x - 60.0) / 120.0)
        h = lerp(h, east_land(y) + 1.2 * math.sin(y / 23.0 + x / 31.0), k)
    return h


def ravine_cut(x, y, top):
    """The ravine cut into land of height `top` at (x, y), or None outside it."""
    d, hw, floor, _ = ravine_q(x, y)
    u = hw - d
    if u <= 0.0:
        return None
    if floor >= top:
        return None
    z = top - (top - floor) * bands(u * 24.0 / WALLW)
    # The floor itself: a little rough, rising to the walls.
    if u > WALLW:
        z = floor + 0.4 * math.sin(x / 7.0) * math.cos(y / 9.0)
    return min(top, z)


def natural(x, y):
    """The land before it's shaped round the roads."""
    h = plateau(x, y)
    z = ravine_cut(x, y, h)
    if z is not None:
        h = z
    # The cemetery's knoll.
    g = math.hypot(x - GRAVEYARD[0], y - GRAVEYARD[1])
    h += 5.0 * (1.0 - sm((g - 18.0) / 34.0))
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


# Hazard Ridge's footprint (anticlockwise): between the town and the ravine, the old mine
# bored into it. Its north face drops sheer into the chasm, its east face into the ravine.
RIDGE = _smooth_loop([
    (58.0, 392.0), (48.0, 340.0), (46.0, 260.0), (60.0, 170.0), (98.0, 112.0), (158.0, 90.0),
    (212.0, 108.0), (234.0, 168.0), (240.0, 250.0), (233.0, 328.0), (205.0, 368.0), (128.0, 382.0),
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

# The shortcut through the mine: (x, y, z) waypoints, and what each stretch is.
#   approach  off the mine approach, down to the portal
#   tunnel    the timbered tunnels
#   workings  the old workings: a wide chamber where a runaway ore cart crosses
#   trestle   the spectral trestle over the glowing chasm
#   ravine    out of the broken gateway, across the ravine floor to the road
MINE = [
    (6.0, 429.0, None, "approach"),  # (on the mine approach)
    (44.0, 418.0, 30.6, "approach"),
    (70.0, 396.0, 28.6, "tunnel"),  # the portal
    (90.0, 362.0, 25.2, "tunnel"),
    (103.0, 332.0, 21.8, "workings"),
    (118.0, 306.0, 21.4, "workings"),  # the ore-cart crossing
    (133.0, 282.0, 21.0, "tunnel"),
    (143.0, 256.0, 18.0, "tunnel"),
    (148.0, 230.0, 15.4, "trestle"),
    (160.0, 203.0, 13.6, "trestle"),
    (163.0, 173.0, 12.6, "trestle"),
    (153.0, 147.0, 12.4, "tunnel"),
    (161.0, 124.0, 12.4, "tunnel"),
    (190.0, 110.0, 12.2, "tunnel"),
    (226.0, 104.0, 12.0, "ravine"),  # the gateway
    (252.0, 90.0, 11.9, "ravine"),
    (280.0, 56.0, None, "ravine"),  # (on the lower ravine)
]
CART_AT = 5  # the waypoint where the ore cart crosses
PORTAL_AT = 2
GATEWAY_AT = 14
CAVERN = (166.0, 188.0)  # the chasm cavern's centre
WORKINGS = (118.0, 306.0)  # the old workings' centre


def _catmull(pts, every=1.0):
    """A smooth line through (x, y, z) points, sampled every ~`every` metres."""
    out = []
    n = len(pts)
    for i in range(n - 1):
        p0 = pts[max(0, i - 1)]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[min(n - 1, i + 2)]
        L = math.dist(p1[:2], p2[:2])
        k = max(2, int(L / every))
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
    # Lead in and out along the race line, so it leaves and joins it smoothly.
    a, _ = c.nearest(*pts[0][:2])
    b, _ = c.nearest(*pts[-1][:2])
    pa = c.at(a.s - 16.0).p
    pb = c.at(b.s + 16.0).p
    dense = _catmull([(pa.x, pa.y, pa.z)] + pts + [(pb.x, pb.y, pb.z)])
    # Only the stretch between the first and last waypoint.
    i0 = min(range(len(dense)), key=lambda i: math.dist(dense[i][:2], pts[0][:2]))
    i1 = min(range(len(dense)), key=lambda i: math.dist(dense[i][:2], pts[-1][:2]))
    dense = dense[i0:i1 + 1]
    # What each point is: the kind of the waypoint stretch it's in.
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


# ---------------------------------------------------------------- side roads


def lane(c, name, pts, mat, surface=None, *, width=10.0, shoulder=0.8, shoulder_mat=None, barrier=0.0, barrier_mat=None,
         deck=0.0, deck_mat=None, ground=True, step=3.0, flush=False, ease=20.0):
    """A road along a dense (x, y, z, ...) polyline (not the race line), open at both
    ends, built with the add-on's road generator. With `ground`, the land meets it.
    `flush`: flush with the race line where it leaves and joins it (Course.flush_profile:
    leaving at the road's middle height, its edge stood over the banked road's)."""
    from course_kit import Vector, bpy, materials, road

    tilts = [0.0] * len(pts)
    if flush:
        cos = [Vector(p[:3]) for p in pts]
        tans = [cos[min(len(cos) - 1, i + 1)] - cos[max(0, i - 1)] for i in range(len(cos))]
        zs, tilts = c.flush_profile(cos, tans, width / 2 + shoulder + 0.5, ease)
        pts = [(p[0], p[1], z) + tuple(p[3:]) for p, z in zip(pts, zs)]

    # Points every `step` metres, tangents from the polyline itself.
    keep = [0]
    acc = 0.0
    for i in range(1, len(pts)):
        acc += math.dist(pts[i][:2], pts[i - 1][:2])
        if acc >= step:
            keep.append(i)
            acc = 0.0
    if keep[-1] != len(pts) - 1:
        keep.append(len(pts) - 1)
    cd = bpy.data.curves.new(name, "CURVE")
    cd.dimensions = "3D"
    cd.twist_mode = "Z_UP"
    sp = cd.splines.new("BEZIER")
    sp.bezier_points.add(len(keep) - 1)
    for k, (bp, i) in enumerate(zip(sp.bezier_points, keep)):
        p = Vector(pts[i][:3])
        a = Vector(pts[max(0, i - 1)][:3])
        b = Vector(pts[min(len(pts) - 1, i + 1)][:3])
        t = (b - a).normalized()
        h = step / 3.0
        bp.handle_left_type = bp.handle_right_type = "FREE"
        bp.co = p
        bp.handle_right = p + t * h
        bp.handle_left = p - t * h
        bp.tilt = tilts[i]
    sp.resolution_u = 6
    ob = bpy.data.objects.new(name, cd)
    c.coll("Roads").objects.link(ob)
    road.attach_road(ob, width=width, barrier=barrier, deck=deck)
    mod = ob.modifiers["KP Road"]
    road.set_input(mod, "Shoulder Width", shoulder)
    road.set_input(mod, "Segment Length", 1.0)
    e = materials.entry(mat)
    materials.apply_to_road(ob, c.lib(mat, surface), "road", e["tileMetres"], 0, materials.aspect(e))
    sm_ = shoulder_mat or (mat, "dirt")
    se = materials.entry(sm_[0])
    materials.apply_to_road(ob, c.lib(*sm_), "shoulder", se["tileMetres"], 0, materials.aspect(se))
    if barrier > 0:
        be = materials.entry(barrier_mat[0])
        materials.apply_to_road(ob, c.lib(*barrier_mat), "barrier", be["tileMetres"], 0, materials.aspect(be))
    if deck > 0:
        de = materials.entry(deck_mat[0])
        materials.apply_to_road(ob, c.lib(*deck_mat), "deck", de["tileMetres"], 0, materials.aspect(de))
    if ground:
        for p, tl in zip(pts, tilts):
            c.extra_ground.append(kit.Sample(Vector(p[:3]), width, math.degrees(tl), 0.0))
    if not hasattr(c, "lanes"):
        c.lanes = []
    c.lanes.append(ob)
    return ob


# ---------------------------------------------------------------- the course


def main():
    c = kit.Course(TRACK_ID, "Dry Gulch Ghost Town (v2)", "dry_gulch")
    c.route(ROUTE, width=18.0, bank=6.0)
    verge = ("gulch_verge", "dirt")
    fence = ("fence_rail", "wall")
    timber = ("weathered_timber", "wall")
    c.kinds = {
        # In town: the dusty main street and its side streets, boardwalk edges.
        "street": {"mat": "gulch_road", "surface": "packed_dirt", "shoulder": 1.6, "shoulder_mat": verge},
        # Out of town: ranch fences.
        "trail": {"mat": "gulch_road", "surface": "packed_dirt", "shoulder": 1.8, "shoulder_mat": verge, "barrier": 1.0,
                  "barrier_mat": fence},
        # The Rickety Trestle, and the trestles along the ravine wall.
        "trestle": {"mat": "plank_deck", "shoulder": 0.6, "shoulder_mat": ("plank_deck", "road"), "barrier": 1.2,
                    "barrier_mat": timber, "deck": 1.8, "deck_mat": timber, "ground": False},
        # Cut into the ravine's east wall: a rock edge under the road on the drop side.
        "ledge": {"mat": "gulch_road", "surface": "packed_dirt", "shoulder": 1.2, "shoulder_mat": verge, "barrier": 1.1,
                  "barrier_mat": fence, "deck": 3.0, "deck_mat": ("strata_red", "wall")},
        # The ravine floor.
        "ravine": {"mat": "gulch_road", "surface": "packed_dirt", "shoulder": 2.2, "shoulder_mat": verge},
        # Where the shortcut leaves and rejoins: open, no fence.
        "open": {"mat": "gulch_road", "surface": "packed_dirt", "shoulder": 2.6, "shoulder_mat": verge},
    }
    line = mine_line(c)
    sa = kit.s_near(c, *line[0][:2])
    sb = kit.s_near(c, *line[-1][:2])

    def label(smp):
        s = smp.s
        seg = seg_of(s)
        x, y = smp.p.x, smp.p.y
        if sa - 12 <= s <= sa + 62 or sb - 62 <= s <= sb + 12:
            return "open"
        if seg in (7, 8, 9, 10, 11) and natural(x, y) < smp.p.z - 5.0:
            return "trestle"
        if seg in (9, 10, 11):
            return "ledge"
        if seg in (12, 13, 14) or (seg == 15 and s < S[15] + 60):
            return "ravine"
        if seg in (0, 1, 2, 3, 4, 5, 16, 17) or (seg == 15 and s > S[15] + 100):
            return "street"
        return "trail"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k != "street":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "street", max_len=200.0))
    c.mine = line
    mine_roads(c, line)

    import gulch_scenery  # noqa: E402

    gulch_scenery.build(c, sys.modules[__name__])
    c.finish()


def mine_roads(c, line):
    """The shortcut's roads: dirt down into the portal, the mine's floor (rails and
    sleepers) through the tunnels and workings, the spectral trestle's planks (rails
    either side, broken in one place), and dirt across the ravine floor."""
    verge = ("gulch_verge", "dirt")
    timber = ("weathered_timber", "wall")
    runs_ = []
    for i, p in enumerate(line):
        k = p[3]
        if k == "workings":
            k = "tunnel"
        if runs_ and runs_[-1][2] == k:
            runs_[-1][1] = i
        else:
            if runs_:
                runs_[-1][1] = i
            runs_.append([i, i, k])
    c.mine_runs = runs_
    for n, (i0, i1, k) in enumerate(runs_):
        seg = line[max(0, i0 - 1 if n else 0):i1 + 1]
        name = "Mine %02d %s" % (n + 1, k)
        if k in ("approach", "ravine"):
            lane(c, name, seg, "gulch_road", "packed_dirt", width=11.0, shoulder=1.0, shoulder_mat=verge, flush=True)
        elif k == "tunnel":
            lane(c, name, seg, "mine_floor", "packed_dirt", width=10.0, shoulder=0.8, shoulder_mat=("mine_floor", "dirt"), ground=False)
        else:
            # The spectral trestle: rails either side, but one stretch broken away on the
            # outside of the bend (the risk of the shortcut).
            # (No rails over the first and last few metres, where it meets the tunnels'
            # floors: nothing to catch a kart's nose on.)
            L = len(seg)
            g0, g1 = int(L * 0.42), int(L * 0.56)
            parts = [(0, 8, 0.0), (7, g0 + 1, 1.0), (g0, g1 + 1, 0.0), (g1, L - 7, 1.0), (L - 8, L, 0.0)]
            for j, (a, b, rail) in enumerate(parts):
                lane(c, "%s %d" % (name, j + 1), seg[a:b], "plank_deck", "road", width=10.0, shoulder=0.4,
                     shoulder_mat=("plank_deck", "road"), barrier=rail, barrier_mat=timber, deck=1.6, deck_mat=timber, ground=False,
                     step=2.0)
            c.mine_gap = (seg[g0][:3], seg[g1][:3])


if __name__ == "__main__":
    main()
