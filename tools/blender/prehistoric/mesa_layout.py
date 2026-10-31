# Desert World v4, the open Southwest (Blake, Oct 31: "a complete overhaul of the desert
# overworld ... unique from the other worlds ... really lean into the south west vibes";
# he chose an open valley with roads on the mesa tops, a day-night cycle, a cliff pueblo
# for its village and Scorchwind's rodeo arena). Pure geometry, no Blender.
# SPDX-License-Identifier: MIT
#
# Not a bowl of walled pockets like the valley's and the snow's: a wide desert floor with
# the mesas and buttes standing on it (Monument Valley), long sight lines to the far rim.
# Each world round its own rock:
#
#   the Trading Post (W)   the roadside post where the Frozen Pass comes down: diner, neon,
#                          gas pump (the way in from the snow, west)
#   the Pueblo (NW)        the cliff pueblo in a great alcove in Pueblo Mesa's south face,
#                          its farms in the wash below
#   the Canyon (N)         the Grand Canyon's rim: a deep red canyon cut into the floor, a
#                          river at its foot round Horseshoe Bend, the road along its rim
#   the Falls (NE)         the side canyon's end: Havasu's turquoise pools (Oasis Haven)
#   the Boomtown (E)       the mining town under Copper Mesa, the railroad into it
#   the Crater (SE)        Meteor Crater's rim, the observatory over its bowl
#   the Showground (S)     Scorchwind's rodeo arena on the open floor (his lair)
#   the High Road          up the cliff ramp onto Sky Mesa's top, along it over the whole
#                          valley, across Sun Arch to Dawn Mesa, down its ramp to the post
#
# Blender coordinates (x east, y north, z up).

import math

FLOOR = 10.0
EXTENT = 470.0


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def _seg(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / ((dx * dx + dy * dy) or 1e-9)))
    return math.hypot(px - a[0] - t * dx, py - a[1] - t * dy), t


# ------------------------------------------------------------------ the rocks

# Mesas: (name, x, y, rx, ry, top, rot (rad)). Their cliffs are banded, a talus skirt at
# their foot.
MESAS = [
    ("pueblo", -250.0, 230.0, 125.0, 70.0, 82.0, 0.15),
    ("sky", 30.0, 30.0, 105.0, 46.0, 36.0, 0.25),
    ("dawn", -190.0, -10.0, 52.0, 40.0, 36.0, -0.3),
    ("copper", 380.0, -20.0, 70.0, 95.0, 74.0, 0.1),
    ("rim_w", -470.0, -60.0, 60.0, 260.0, 110.0, 0.0),
    ("rim_s", 20.0, -470.0, 380.0, 60.0, 95.0, 0.0),
    ("rim_n", 160.0, 480.0, 360.0, 60.0, 120.0, 0.0),
]
# Buttes: (x, y, r, height): the valley's landmarks, the "mittens".
BUTTES = [
    (-120.0, -120.0, 20.0, 96.0),
    (-150.0, -160.0, 14.0, 84.0),
    (210.0, -190.0, 18.0, 110.0),
    (130.0, 150.0, 16.0, 88.0),
    (-370.0, 130.0, 13.0, 70.0),
    (270.0, 130.0, 12.0, 76.0),
]
# The Canyon: its line, the river's height at its foot, its rim's half width.
CANYON = [(-160.0, 330.0), (-60.0, 320.0), (40.0, 300.0), (110.0, 330.0), (150.0, 372.0), (190.0, 330.0), (240.0, 318.0),
          (300.0, 324.0), (352.0, 302.0), (384.0, 250.0), (396.0, 204.0)]
CANYON_DEPTH = -34.0  # the river's height
CANYON_HW = 34.0
# The Falls' basin at the side canyon's end: x, y, radius, pool height.
FALLS = (398.0, 196.0, 28.0, -22.0)
# The Crater: x, y, rim radius, rim height above the floor, floor height.
CRATER = (190.0, -300.0, 78.0, 12.0, -18.0)
# The Pueblo's alcove in Pueblo Mesa's south face: x, y, width, depth (into the cliff).
ALCOVE = (-250.0, 166.0, 70.0, 26.0)
# The Showground: the arena's middle and radius.
ARENA = (-20.0, -170.0, 34.0)
# The Trading Post: its square.
POST = (-360.0, -40.0, 22.0)
# The Boomtown's street (x, y, length, heading).
TOWN = (278.0, -40.0, 80.0, math.pi / 2)


def _mesa(h, x, y, m):
    _n, cx, cy, rx, ry, top, rot = m
    c, s = math.cos(rot), math.sin(rot)
    dx, dy = (x - cx) * c + (y - cy) * s, -(x - cx) * s + (y - cy) * c
    a = math.atan2(dy / ry, dx / rx)
    wob = 1.0 + 0.06 * math.sin(3 * a + cx * 0.01) + 0.035 * math.sin(7 * a + cy * 0.02) + 0.02 * math.sin(13 * a)
    e = (abs(dx / rx) ** 2.6 + abs(dy / ry) ** 2.6) ** (1 / 2.6) / wob
    # (Metres from its rim: + outside.)
    d = (e - 1.0) * min(rx, ry)
    if d > 60.0:
        return h
    hgt = top - FLOOR
    if d <= 0.0:
        z = top - 0.6 * smooth(-d / 30.0) * math.sin(x / 13.0) * math.cos(y / 17.0)
    elif d < 7.0:
        # The cliff, in bands: steep with ledges.
        t = d / 7.0
        z = top - hgt * 0.72 * (t + 0.06 * math.sin(t * 9.0))
    else:
        # The talus skirt down to the floor.
        z = lerp(top - hgt * 0.72, FLOOR, smooth((d - 7.0) / (10.0 + hgt * 0.25)) ** 0.7)
    return max(h, z)


def _butte(h, x, y, b):
    bx, by, r, height = b
    d = math.hypot(x - bx, y - by) - r * (1.0 + 0.08 * math.sin(3 * math.atan2(y - by, x - bx) + bx))
    if d > 40.0:
        return h
    top = FLOOR + height
    if d <= 0:
        z = top
    elif d < 3.0:
        z = lerp(top, FLOOR + height * 0.35, d / 3.0)
    else:
        z = lerp(FLOOR + height * 0.35, FLOOR, smooth((d - 3.0) / 30.0))
    return max(h, z)


def canyon_d(x, y):
    best, bt = 1e9, 0.0
    tot = 0.0
    for a, b in zip(CANYON, CANYON[1:]):
        d, t = _seg(x, y, a, b)
        if d < best:
            best = d
    return best


def _canyon(h, x, y):
    d = canyon_d(x, y)
    if d > CANYON_HW + 4.0:
        return h
    # Stepped walls: a sheer upper band, a bench, the inner gorge, the river.
    u = d / CANYON_HW
    if u > 0.78:
        z = lerp(CANYON_DEPTH * 0.18, FLOOR, smooth((u - 0.78) / 0.24))
    elif u > 0.5:
        z = lerp(CANYON_DEPTH * 0.42, CANYON_DEPTH * 0.18, smooth((u - 0.5) / 0.28) ** 0.5)
    elif u > 0.24:
        z = lerp(CANYON_DEPTH * 0.92, CANYON_DEPTH * 0.42, smooth((u - 0.24) / 0.26))
    else:
        z = CANYON_DEPTH - 0.6
    return min(h, z)


def _falls(h, x, y):
    fx, fy, fr, fz = FALLS
    d = math.hypot(x - fx, y - fy)
    if d > fr + 30.0:
        return h
    z = fz - 0.6 if d < fr else lerp(fz, h, smooth((d - fr) / 30.0))
    return min(h, z)


def _crater(h, x, y):
    cx, cy, R, rim, fz = CRATER
    d = math.hypot(x - cx, y - cy)
    if d > R * 2.2:
        return h
    if d < R:
        u = d / R
        z = lerp(fz, FLOOR + rim, smooth(u) ** 1.6)
        return z
    return h + rim * math.exp(-((d - R) / (R * 0.38)) ** 2)


def _floor(x, y):
    """The desert floor: long low swells, a dune field in the south-west, dry washes."""
    h = FLOOR + 1.6 * math.sin(x / 71.0 + 0.4) * math.cos(y / 59.0) + 0.9 * math.sin((x - y) / 37.0)
    dune = smooth((-x - y - 250.0) / 160.0) * smooth((x + 470.0) / 80.0)
    h += dune * 4.5 * max(0.0, math.sin(x / 19.0 + y / 41.0 + math.sin(y / 33.0)))
    return h


# ------------------------------------------------------------------ the road

# (x, y, z or None): None rides the land; set heights on the ramps and the mesa tops.
ROUTE = [
    (-320.0, -40.0, None),  # 0: the start, the post's east side, northbound
    (-310.0, 30.0, None),
    (-290.0, 110.0, None),  # 2: along the pueblo mesa's foot, the alcove up on the right
    (-230.0, 128.0, None),
    (-150.0, 138.0, None),
    (-66.0, 190.0, None),  # 5: up to the canyon's rim
    (-40.0, 262.0, None),
    (30.0, 248.0, None),  # 7: along the rim
    (96.0, 270.0, None),
    (150.0, 314.0, None),  # 9: Horseshoe overlook
    (204.0, 268.0, None),
    (256.0, 262.0, None),
    (316.0, 250.0, None),
    (340.0, 196.0, None),  # 13: the Falls, down at its pools on the right
    (316.0, 140.0, None),
    (282.0, 60.0, None),
    (278.0, -20.0, None),  # 16: the Boomtown's street, Copper Mesa over it
    (274.0, -100.0, None),
    (264.0, -170.0, None),
    (258.0, -236.0, None),  # 19: up onto the crater's rim
    (190.0, -214.0, None),  # 20: along the rim, the observatory over the bowl
    (116.0, -246.0, None),
    (50.0, -214.0, None),  # 22: past the Showground
    (96.0, -110.0, None),
    (150.0, -30.0, None),  # 24: round Sky Mesa's east end, onto its ledge
    (121.0, -3.0, 12.0),  # 25: the Ledge Road up its south cliff, west
    (82.0, -12.0, 17.6),
    (43.0, -22.0, 23.2),
    (4.0, -32.0, 28.6),
    (-34.0, -42.0, 33.0),
    (-66.0, -16.0, 35.6),  # 30: over its west tip
    (-90.0, 8.0, 36.0),
    (-122.0, 14.0, 36.0),  # 32: over Sun Arch
    (-160.0, 0.0, 36.0),  # 33: on Dawn Mesa
    (-200.0, -34.0, 31.4),  # 34: its causeway down, west
    (-236.0, -60.0, 26.2),
    (-276.0, -74.0, 20.4),
    (-312.0, -70.0, 15.0),  # 37: and back into the post
]
ARCH = (-122.0, 14.0)  # Sun Arch: the road over it; the floor under it open
ARCH_SPAN = (-108.0, 20.0, -140.0, 8.0)  # its ends (x0, y0, x1, y1) where the mesas' rims are

# The worlds' gates (x, y): beside the road, each at its rock.
GATES = {
    "canyon": (150.0, 296.0),
    "oasis": (347.0, 157.0),
    "gulch": (248.0, -60.0),
    "impact": (190.0, -236.0),
    "lair": (26.0, -188.0),  # (out of the arena's east gate)
}
FROZEN_PASS = (-440.0, -40.0)  # the way in from the snow, west
CAVE = (-363.0, -94.0)  # the smugglers' Drift Cave's yard, behind the post
SECRET = (330.0, 259.0)  # the sunken garden by the falls' side canyon (the Beach Tool's)
DUST_ROAD = (-80.0, -440.0)  # the way out south to Tropic Isles


def _dense(points, every=4.0):
    """The route's points rounded through their corners (Catmull-Rom), every `every` m."""
    n = len(points)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = points[(i - 1) % n], points[i], points[(i + 1) % n], points[(i + 2) % n]
        L = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        k = max(2, int(L / every))
        for j in range(k):
            t = j / k
            t2, t3 = t * t, t * t * t
            x = 0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y, i, t))
    return out


def _land(x, y):
    h = _floor(x, y)
    for m in MESAS:
        h = _mesa(h, x, y, m)
    for b in BUTTES:
        h = _butte(h, x, y, b)
    h = _canyon(h, x, y)
    h = _falls(h, x, y)
    h = _crater(h, x, y)
    h = _alcove(h, x, y)
    h = _arch_gap(h, x, y)
    h = _passes(h, x, y)
    return h


def _alcove(h, x, y):
    """The pueblo's alcove: a deep half-round bay cut back into Pueblo Mesa's south cliff,
    its floor a step above the desert (the overhang over it is a mesh: mesa_region)."""
    ax, ay, w, dp = ALCOVE
    dx, dy = (x - ax) / (w / 2), (y - ay) / dp
    e = math.hypot(dx, max(0.0, dy))
    if e > 1.25 or dy < -0.6:
        return h
    fz = FLOOR + 6.0
    if e < 1.0:
        return min(h, fz) if h > fz else max(h, lerp(h, fz, smooth((dy + 0.6) / 0.6)))
    return lerp(fz, h, smooth((e - 1.0) / 0.25)) if h > fz else h


def _arch_gap(h, x, y):
    """The gap between Sky Mesa and Dawn Mesa that Sun Arch spans: cut to the floor."""
    x0, y0, x1, y1 = ARCH_SPAN
    d, t = _seg(x, y, (x0, y0), (x1, y1))
    if 0.08 < t < 0.92 and d < 26.0:
        w = smooth((26.0 - d) / 12.0) * smooth(min(t - 0.08, 0.92 - t) / 0.1)
        return lerp(h, min(h, FLOOR + 1.0), w)
    return h


_RP = None


def route_points():
    """The road's points: its set heights where given (eased between), the land's (a ring
    average, smoothed) elsewhere."""
    global _RP
    if _RP is not None:
        return _RP
    zs = []
    for x, y, z in ROUTE:
        if z is None:
            ring = [_land(x + 10 * math.cos(a), y + 10 * math.sin(a)) for a in (0, 1.57, 3.14, 4.71)]
            z = (sum(ring) + _land(x, y)) / 5.0 + 0.3
        zs.append(z)
    n = len(ROUTE)
    for _ in range(2):
        zs = [z if ROUTE[i][2] is not None else 0.25 * zs[i - 1] + 0.5 * z + 0.25 * zs[(i + 1) % n] for i, z in enumerate(zs)]
    _RP = [(x, y, z) for (x, y, _), z in zip(ROUTE, zs)]
    return _RP


_DENSE = None


def road_line():
    """The road densely: [(x, y, z)], heights eased along it between its points."""
    global _DENSE
    if _DENSE is not None:
        return _DENSE
    rp = route_points()
    n = len(rp)
    out = []
    for x, y, i, t in _dense(rp):
        z0, z1 = rp[i][2], rp[(i + 1) % n][2]
        out.append((x, y, lerp(z0, z1, t)))
    _DENSE = out
    return out


_GRID = None
_CELL = 24.0


def _grid():
    global _GRID
    if _GRID is None:
        line = road_line()
        _GRID = {}
        for a, b in zip(line, line[1:] + line[:1]):
            for gx in range(int(math.floor(min(a[0], b[0]) / _CELL)) - 1, int(math.floor(max(a[0], b[0]) / _CELL)) + 2):
                for gy in range(int(math.floor(min(a[1], b[1]) / _CELL)) - 1, int(math.floor(max(a[1], b[1]) / _CELL)) + 2):
                    _GRID.setdefault((gx, gy), []).append((a, b))
    return _GRID


def road_floor(x, y):
    """(distance to the road's middle, its height there) for the land's shelf under it
    (1e9 beyond a cell or so of it)."""
    best = (1e9, 0.0)
    for a, b in _grid().get((int(math.floor(x / _CELL)), int(math.floor(y / _CELL))), ()):
        d, t = _seg(x, y, a, b)
        if d < best[0]:
            best = (d, lerp(a[2], b[2], t))
    return best


# The ways out through the rim walls: (from (x, y), to (x, y), floor at the far end,
# half width). The Frozen Pass west (up to the snow); the Dust Road south (after
# Scorchwind's fall).
PASS_WAYS = [((-380.0, -40.0), (-452.0, -40.0), 22.0, 9.0), ((-60.0, -330.0), (-80.0, -452.0), 14.0, 9.0)]


def _passes(h, x, y):
    for a, b, zend, hw in PASS_WAYS:
        d, t = _seg(x, y, a, b)
        if d < hw + 16.0:
            z = lerp(_floor(*a), zend, t)
            h = lerp(min(h, z), h, smooth((d - hw) / 16.0)) if h > z else h
    return h


def natural(x, y):
    """The land, with the road's shelf: cut level across it where it's on a ramp or a
    mesa (into the rock, built up where it crosses lower ground), eased on the floor;
    open under Sun Arch."""
    h = _land(x, y)
    d, z = road_floor(x, y)
    ax, ay = ARCH
    if math.hypot(x - ax, y - ay) < 16.0:
        return h  # (the arch's deck is a bridge; the floor stays under it)
    if d < 8.0:
        return z - 0.25
    if d < 20.0:
        return lerp(z - 0.25, h, smooth((d - 8.0) / 12.0))
    return h


def look_at(x, y):
    """Which world (x, y) is in, by its nearest landmark."""
    places = {"post": POST[:2], "pueblo": ALCOVE[:2], "canyon": (60.0, 300.0), "falls": FALLS[:2],
              "town": TOWN[:2], "crater": CRATER[:2], "show": ARENA[:2], "mesa": (0.0, 30.0)}
    return min(places, key=lambda k: math.hypot(x - places[k][0], y - places[k][1]))
