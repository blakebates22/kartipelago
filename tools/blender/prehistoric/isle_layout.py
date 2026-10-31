# Tropic Isles v4: one big island (Blake, Oct 31: "Needs to be an island I think, with maybe
# tropical dense forest in the center"; he picked a jungle peak at the centre). Pure
# geometry, no Blender (isle_region.py builds it).
# SPDX-License-Identifier: MIT
#
# A high island in a turquoise sea: a ring of beach and shallows round the coast, the
# coastal flats behind it, then dense rainforest climbing in ridges and valleys to a sheer
# green pinnacle in the middle, its falls dropping into a river gorge that runs out to the
# lagoon. The road: round the coast (the island hop comes in to Raptor's stilt village on
# the east bay; Coral Cove's reef, south-east; Splash Lagoon by the lagoon, south-west;
# Shipwreck Bay, north-west; the Volcano Isle pier, north), then in from the north coast
# up through the jungle over a crest (the look across to the pinnacle and its falls) and
# down to the village. Tidewyrm's sea cave is in the cliffs of the headland south of the
# village.
#
# Blender coordinates (x east, y north, z up).

import math

EXTENT = 470.0
WATER_Z = 0.0
PEAK = (10.0, 30.0)  # the pinnacle
PEAK_Z = 150.0


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def _seg(px, py, a, b):
    ax, ay = a[0], a[1]
    bx, by = b[0], b[1]
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - ax - t * dx, py - ay - t * dy), t


def _adiff(a, b):
    return (a - b + math.pi) % math.tau - math.pi


# ---------------------------------------------------------------- the coast

# The bays: (angle from the island's middle, half width in radians, depth in metres).
BAYS = {
    "village": (math.radians(4.0), 0.22, 46.0),  # Raptor's bay, east: the stilt village over it
    "coral": (math.radians(-52.0), 0.2, 54.0),  # Coral Cove, south-east: the reef across its mouth
    "wreck": (math.radians(140.0), 0.24, 64.0),  # Shipwreck Bay, north-west
}
# Tidewyrm's Head: a rocky headland reaching out south of the village bay, sea cliffs
# round it (his cave in its south face, after his attack).
HEAD = (math.radians(-22.0), 0.14, 40.0)  # angle, half width, how far it reaches out
HEAD_Z = 24.0


def shore_r(a):
    """The coastline's distance from the island's middle at angle a."""
    r = 352.0 + 22.0 * math.sin(3.0 * a + 0.7) + 12.0 * math.sin(5.0 * a + 2.0) + 6.0 * math.sin(9.0 * a + 1.1)
    for ang, hw, depth in BAYS.values():
        d = abs(_adiff(a, ang))
        if d < hw:
            r -= depth * (0.5 + 0.5 * math.cos(math.pi * d / hw))
    ha, hhw, reach = HEAD
    d = abs(_adiff(a, ha))
    if d < hhw:
        r += reach * (0.5 + 0.5 * math.cos(math.pi * d / hhw))
    return r


def inland(x, y):
    """How far inland (x, y) is from the shore (negative: out to sea)."""
    return shore_r(math.atan2(y, x)) - math.hypot(x, y)


# The lagoon: shallow still water behind the south-west shore, open to the sea by an inlet
# (the road crosses it on a boardwalk).
LAGOON = (-168.0, -150.0, 58.0)
LAGOON_INLET = [(-196.0, -178.0), (-262.0, -238.0)]
LAGOON_Z = -0.6

# The river: off the pinnacle's falls, down its gorge to the lagoon.
RIVER = [(0.0, -28.0), (-30.0, -62.0), (-70.0, -92.0), (-110.0, -112.0), (-140.0, -128.0)]
RIVER_HW = 7.0
FALLS = (6.0, -18.0)  # the pinnacle's great falls' foot (off its south cliff)


def river_d(x, y):
    best = 1e9
    tt = 0.0
    k = 0
    for i, (a, b) in enumerate(zip(RIVER, RIVER[1:])):
        d, t = _seg(x, y, a, b)
        if d < best:
            best, tt, k = d, t, i
    return best, (k + tt) / (len(RIVER) - 1)


def _mountain(x, y):
    """The jungle mountain: a cone to the pinnacle, ribbed in radial ridges and valleys,
    the pinnacle itself sheer."""
    px, py = PEAK
    r = math.hypot(x - px, y - py)
    a = math.atan2(y - py, x - px)
    cone = 150.0 * max(0.0, 1.0 - r / 290.0) ** 1.35
    ribs = 0.62 + 0.38 * abs(math.sin(3.5 * a + 0.25 * math.sin(r / 37.0) + 0.6))
    knobs = 1.0 + 0.12 * math.sin(x / 23.0) * math.cos(y / 29.0)
    h = cone * ribs * knobs
    # The pinnacle: a green spire, sheer on every side.
    h += 70.0 * smooth((58.0 - r) / 22.0) * (0.9 + 0.1 * math.sin(a * 5.0))
    return h


def _land(x, y):
    s = inland(x, y)
    if s < 0.0:
        # The sea: shallows (turquoise, wadeable) a little way out, then deep.
        h = WATER_Z - 0.35 + s * 0.045
        h = max(h, WATER_Z - 2.2 + s * 0.12)
        return max(h, -40.0)  # (falling away to the deep blue)
    beach = WATER_Z - 0.3 + 2.6 * smooth(s / 34.0)
    flats = beach + 3.5 * smooth((s - 34.0) / 50.0) + 1.2 * math.sin(x / 31.0) * math.cos(y / 37.0) * smooth((s - 30.0) / 40.0)
    h = flats + _mountain(x, y) * smooth((s - 50.0) / 90.0)
    # Tidewyrm's Head: the headland's top a grassy shelf, cliffs to the sea.
    ha, hhw, reach = HEAD
    a = math.atan2(y, x)
    d = abs(_adiff(a, ha))
    if d < hhw * 1.6 and s < 70.0:
        w = smooth((hhw * 1.4 - d) / (hhw * 0.6)) * smooth(s / 6.0)
        h = lerp(h, max(h, HEAD_Z + 3.0 * math.sin(x / 11.0)), w)
    # Tidewyrm's ledge: a rock shelf at the cliffs' foot, his cave's mouth on it (level with
    # the road above the beach).
    dl = math.hypot(x - LAIR[0], y - LAIR[1])
    if dl < 34.0:
        h = lerp(h, max(h, 5.2), smooth((34.0 - dl) / 12.0))
    # The lagoon: still shallow water behind the shore, its inlet out to sea.
    lx, ly, lr = LAGOON
    dl = math.hypot(x - lx, y - ly)
    if dl < lr + 30.0:
        h = lerp(h, LAGOON_Z - 1.4, smooth((lr + 14.0 - dl) / 18.0))
    di, _ = _seg(x, y, *LAGOON_INLET)
    if di < 30.0:
        h = lerp(h, min(h, LAGOON_Z - 1.4), smooth((22.0 - di) / 10.0))
    # The river's gorge: cut down from the falls to the lagoon, its floor falling with it.
    dr, t = river_d(x, y)
    if dr < 40.0:
        floor = lerp(14.0, LAGOON_Z - 0.6, t)
        h = lerp(h, min(h, floor), smooth((34.0 - dr) / (34.0 - RIVER_HW)) if dr > RIVER_HW else 1.0)
    # The plunge pool under the pinnacle's falls.
    df = math.hypot(x - FALLS[0], y - FALLS[1])
    if df < 30.0:
        h = lerp(h, min(h, 12.0), smooth((30.0 - df) / 12.0))
    return h


# ---------------------------------------------------------------- the road

def _coast(a_deg, back=46.0):
    """A point on the coast road: `back` m inland at angle a."""
    a = math.radians(a_deg)
    r = shore_r(a) - back
    return (r * math.cos(a), r * math.sin(a))


# Clockwise round the coast from the village (east), then in from the north coast over the
# jungle crest and back down to the village. (x, y, height or None: the land's.)
ROUTE = []
for _a in (10, -6):
    ROUTE.append(_coast(_a, 76.0) + (None,))
# (round the back of Tidewyrm's Head: inland of its cliffs)
for _a, _b in ((-18, 96.0), (-28, 96.0)):
    ROUTE.append(_coast(_a, _b) + (None,))
for _a in (-40, -56, -70, -86, -102, -116, -128):
    ROUTE.append(_coast(_a, 48.0 if _a != -56 else 40.0) + (None,))
# (the lagoon's inlet, crossed on a boardwalk: on_boardwalk)
for _a in (-140, -152, -166, 178, 164, 150, 138, 126, 112, 100, 88, 76, 64):
    ROUTE.append(_coast(_a, 48.0 if _a not in (138, 150) else 40.0) + (None,))
# (in from the north coast: up through the jungle, over the crest, down to the village)
ROUTE += [
    (150.0, 262.0, 6.0),
    (128.0, 214.0, 12.0),
    (118.0, 166.0, 20.0),
    (138.0, 126.0, 27.0),  # the crest: the look across to the pinnacle and its falls
    (182.0, 108.0, 24.0),
    (220.0, 112.0, 17.0),
    (248.0, 96.0, 10.0),
    (258.0, 62.0, None),
]
CREST = (138.0, 126.0)

# Raptor's village: its square on the flats above the east bay (the island hop's pier comes
# in past it), the stilt huts out over the bay.
HUB = (252.0, 30.0, 20.0)  # x, y, radius (the square)
HOP_PIER = [(276.0, 30.0), (452.0, 26.0)]  # the pier out east over the bay to the island hop
# The gateways' landmarks.
GATES = {
    "coral": _coast(-50.0, 6.0),
    "splash": (-112.0, -236.0),  # (on the flats between the lagoon and the south road)
    "wreck": _coast(142.0, 10.0),
    "volcano": _coast(88.0, -60.0),  # the pier's end, out over the shallows
}
LAIR = _coast(-35.0, 16.0)  # Tidewyrm's sea cave, at the foot of the Head's south cliffs
VOLCANO = (250.0, 640.0)  # Volcano Isle, smoking offshore north
CAVE = (-250.0, -40.0)  # the return yard: Raptor's old cove, in the jungle's edge behind the west beach
SECRET = (34.0, 300.0)  # the smugglers' cave, behind the north beach
CAUSEWAY = [(-330.0, 70.0), (-456.0, 92.0)]  # Tidewyrm's Causeway, west over the sea (the ruin)


def _dense(points, every=4.0):
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


_RP = None


def route_points():
    """The road's points: its set heights where given, the land's (a ring average, never
    below the beach's top) elsewhere, smoothed."""
    global _RP
    if _RP is not None:
        return _RP
    zs = []
    for x, y, z in ROUTE:
        if z is None:
            ring = [_land(x + 10 * math.cos(a), y + 10 * math.sin(a)) for a in (0, 1.57, 3.14, 4.71)]
            z = max(2.4, (sum(ring) + _land(x, y)) / 5.0 + 0.3)
        zs.append(z)
    n = len(ROUTE)
    for _ in range(3):
        zs = [z if ROUTE[i][2] is not None else 0.25 * zs[i - 1] + 0.5 * z + 0.25 * zs[(i + 1) % n] for i, z in enumerate(zs)]
    _RP = [(x, y, z) for (x, y, _), z in zip(ROUTE, zs)]
    return _RP


_DENSE = None


def road_line():
    global _DENSE
    if _DENSE is not None:
        return _DENSE
    rp = route_points()
    n = len(rp)
    _DENSE = [(x, y, lerp(rp[i][2], rp[(i + 1) % n][2], t)) for x, y, i, t in _dense(rp)]
    return _DENSE


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
    best = (1e9, 0.0)
    for a, b in _grid().get((int(math.floor(x / _CELL)), int(math.floor(y / _CELL))), ()):
        d, t = _seg(x, y, a, b)
        if d < best[0]:
            best = (d, lerp(a[2], b[2], t))
    return best


def on_boardwalk(x, y):
    """Over the lagoon's inlet (the road crosses it on a boardwalk)."""
    d, t = _seg(x, y, *LAGOON_INLET)
    return d < 26.0 and 0.05 < t < 0.95


def natural(x, y):
    """The land, with the road's shelf cut into the hills (built up over the low ground);
    open water under the boardwalk."""
    h = _land(x, y)
    if on_boardwalk(x, y):
        return h
    d, z = road_floor(x, y)
    if d < 8.0:
        return z - 0.25
    if d < 20.0:
        return lerp(z - 0.25, h, smooth((d - 8.0) / 12.0))
    return h


def look_at(x, y):
    """Which part of the island (x, y) is in."""
    s = inland(x, y)
    if s < 40.0:
        a = math.degrees(math.atan2(y, x))
        if -40 < a < 30:
            return "village"
        if -90 <= a <= -40:
            return "coral"
        if -160 <= a < -90 or a < -160 and math.hypot(x - LAGOON[0], y - LAGOON[1]) < 140:
            return "lagoon"
        if a > 115 or a < -160:
            return "wreck"
        return "beach"
    return "jungle"
