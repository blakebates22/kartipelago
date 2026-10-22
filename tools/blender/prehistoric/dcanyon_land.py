# Dragon Canyon's land (see dragon_canyon.py): the layout, the road's heights and
# widths, the river's course, the canyon itself (the ledges the roads are cut into, the
# gorge, the chasm, the buttes and spires, the walls round it all), and the zones. Plain
# data, no Blender, so it can be checked and plotted on its own.
# SPDX-License-Identifier: MIT
#
# The road is drawn as corners: (x, y, radius) points joined by straights, each corner an
# arc of that radius tangent to both straights ("fillets"). A hairpin is two corners 2r
# apart. Blender coordinates: x east, y north, z up.

import math

from impact_land import clamp, lerp, noise, seg_dist, sm  # noqa: F401  (shared helpers)


def rnd(k):
    x = math.sin(k * 12.9898 + 78.233) * 43758.5453
    return x - math.floor(x)


# ---------------------------------------------------------------- the layout

# (x, y, radius, name). Lap order; the start line is on the straight into corner "c1".
CORNERS = [
    (0.0, -20.0, 0.0, "start"),  # 1  the Canyon Outpost: north up the start straight
    (0.0, 40.0, 30.0, "c1"),  # 2  the Cliffside Hairpins: east onto the bottom ledge
    (88.0, 40.0, 30.0, "h1a"),  # hairpin one (left), up a tier...
    (88.0, 100.0, 30.0, "h1b"),
    (6.0, 100.0, 30.0, "h2a"),  # ...hairpin two (right), up another
    (6.0, 160.0, 30.0, "h2b"),
    (98.0, 160.0, 28.0, "n1"),  # 3  the Great Canyon Descent: north off the top ledge
    (104.0, 222.0, 34.0, "n2"),  # east onto the Canyon Bridge
    (246.0, 222.0, 36.0, "n3"),  # south, down the far wall
    (272.0, 172.0, 30.0, "k1"),  # 4  Dragon Skeleton Pass: left, right, left through the ribs
    (222.0, 128.0, 30.0, "k2"),
    (270.0, 84.0, 30.0, "k3"),
    (300.0, 4.0, 26.0, "q1"),  # 5  the Imperial Quarry: right round the loading yard
    (232.0, 4.0, 24.0, "q2"),  # left, south into the mesa
    (244.0, -72.0, 30.0, "t1"),  # 6  the Winding Caverns: the tunnel bends west
    (178.0, -100.0, 40.0, "b1"),  # 7  the High Bridges: over the river road and the chasm,
    (134.0, -170.0, 40.0, "b2"),  #    sweeping round the Lone Spire
    (50.0, -176.0, 30.0, "o1"),  # 8  the Hidden Oasis: round the pool
    (50.0, -254.0, 32.0, "o2"),
    (178.0, -254.0, 32.0, "o3"),
    (190.0, -140.0, 60.0, "r1"),  # 9  River Canyon Sprint: north along the river, under
    (172.0, -50.0, 60.0, "r2"),  #    the High Bridges
    (176.0, 4.0, 28.0, "w0"),  # 10 the Watchtower Ascent: west, then up two hairpins
    (60.0, 4.0, 30.0, "w1a"),
    (60.0, -56.0, 30.0, "w1b"),
    (122.0, -56.0, 30.0, "w2a"),
    (122.0, -116.0, 30.0, "w2b"),
    (80.0, -116.0, 26.0, "x1"),  # 11 the Final Twist: snapping left and right off the
    (52.0, -142.0, 26.0, "x2"),  #    tower's ledge...
    (-18.0, -142.0, 26.0, "x3"),
    (-92.0, -142.0, 30.0, "x4a"),  # ...the Dragon's Coil hairpin...
    (-92.0, -82.0, 30.0, "x4b"),
    (0.0, -82.0, 28.0, "x5"),  # 12 Return to the Dragon Gate: left onto the straight
]


def fillet_path(V, step=1.0):
    """The closed path through corners V: straights joined by tangent arcs. Returns
    [(x, y, heading_deg, corner_index)] (a straight's index is its corner's + 0.5)."""
    n = len(V)
    arcs = []
    for i in range(n):
        p0, p1, p2 = V[i - 1], V[i], V[(i + 1) % n]
        ux, uy = p1[0] - p0[0], p1[1] - p0[1]
        vx, vy = p2[0] - p1[0], p2[1] - p1[1]
        lu, lv = math.hypot(ux, uy), math.hypot(vx, vy)
        ux, uy, vx, vy = ux / lu, uy / lu, vx / lv, vy / lv
        th = math.acos(max(-1.0, min(1.0, ux * vx + uy * vy)))
        r = p1[2]
        t = r * math.tan(th / 2) if th > 1e-6 else 0.0
        arcs.append(dict(a=(p1[0] - ux * t, p1[1] - uy * t), b=(p1[0] + vx * t, p1[1] + vy * t), th=th, r=r,
                         sgn=1 if ux * vy - uy * vx > 0 else -1, h0=math.degrees(math.atan2(uy, ux)), t=t))
    for i in range(n):
        ln = math.hypot(V[(i + 1) % n][0] - V[i][0], V[(i + 1) % n][1] - V[i][1])
        assert arcs[i]["t"] + arcs[(i + 1) % n]["t"] <= ln + 0.5, ("corners overlap", V[i][3], V[(i + 1) % n][3])
    pts = []
    for i in range(n):
        A = arcs[i]
        x, y = A["a"]
        h = A["h0"]
        if A["th"] > 1e-6:
            m = max(2, int(A["r"] * A["th"] / step))
            deg = math.degrees(A["th"])
            for _ in range(m):
                pts.append((x, y, h, i))
                dh = A["sgn"] * deg / m
                chord = 2 * A["r"] * math.sin(math.radians(abs(dh)) / 2)
                x += math.cos(math.radians(h + dh / 2)) * chord
                y += math.sin(math.radians(h + dh / 2)) * chord
                h += dh
        B = arcs[(i + 1) % n]
        (sx, sy), (ex, ey) = A["b"], B["a"]
        L = math.hypot(ex - sx, ey - sy)
        m = max(1, int(L / step))
        hh = math.degrees(math.atan2(ey - sy, ex - sx)) if L > 1e-6 else h
        for k in range(m):
            pts.append((sx + (ex - sx) * k / m, sy + (ey - sy) * k / m, hh, i + 0.5))
    return pts


PATH = fillet_path(CORNERS)
_D = [0.0]
for _a, _b in zip(PATH, PATH[1:]):
    _D.append(_D[-1] + math.hypot(_b[0] - _a[0], _b[1] - _a[1]))
LENGTH = _D[-1] + math.hypot(PATH[0][0] - PATH[-1][0], PATH[0][1] - PATH[-1][1])
NAMES = [c[3] for c in CORNERS]
S = {}  # corner name -> lap distance where its arc starts
for _i, _p in enumerate(PATH):
    S.setdefault(NAMES[int(_p[3])], _D[_i])


def at(name, frac=0.0):
    """Lap distance a fraction of the way through corner `name`'s arc and straight."""
    i = NAMES.index(name)
    s0 = S[name]
    s1 = S[NAMES[(i + 1) % len(NAMES)]] if i + 1 < len(NAMES) else LENGTH
    return s0 + (s1 - s0) * frac


def seg_of(s):
    s %= LENGTH
    best = NAMES[0]
    for n in NAMES:
        if S[n] <= s:
            best = n
    return best


def path_at(s):
    s %= LENGTH
    lo, hi = 0, len(_D) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if _D[mid] <= s:
            lo = mid
        else:
            hi = mid - 1
    a = PATH[lo]
    b = PATH[(lo + 1) % len(PATH)]
    d1 = _D[lo + 1] if lo + 1 < len(_D) else LENGTH
    t = (s - _D[lo]) / max(1e-6, d1 - _D[lo])
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t), a[2])


_GRID = {}
for _i, _p in enumerate(PATH):
    _GRID.setdefault((int(_p[0] // 20), int(_p[1] // 20)), []).append(_i)


def nearest(x, y, near=None):
    """(distance, lap distance) of the nearest road point (optionally only those within
    `near` m of lap distance)."""
    gx, gy = int(x // 20), int(y // 20)
    best = (1e18, 0.0)
    for r in range(0, 30):
        for i in range(gx - r, gx + r + 1):
            for j in range(gy - r, gy + r + 1):
                if r and max(abs(i - gx), abs(j - gy)) != r:
                    continue
                for k in _GRID.get((i, j), ()):
                    p = PATH[k]
                    d = (p[0] - x) ** 2 + (p[1] - y) ** 2
                    if d < best[0]:
                        best = (d, _D[k])
        if best[0] < (r * 20) ** 2:
            break
    return math.sqrt(best[0]), best[1]


# ---------------------------------------------------------------- heights

ANCHORS = [  # (corner, fraction through it, z)
    ("start", 0.0, 30.0),
    ("c1", 0.0, 30.5),
    ("n2", 0.0, 52.0),  # up the ledges to the top: the Canyon Bridge
    ("n3", 0.0, 49.5),
    ("q1", 0.0, 29.0),  # down the far wall, through the Skeleton Pass, to the quarry floor
    ("q2", 0.4, 27.5),
    ("b1", 0.0, 35.0),  # climbing through the caverns to the High Bridges
    ("b2", 0.3, 34.0),
    ("o3", 0.0, 12.0),  # down to the oasis
    ("r1", 0.0, 9.0),  # along the river
    ("w0", 0.0, 9.0),
    ("x1", 0.0, 31.0),  # up to the watchtower
    ("x3", 0.5, 37.0),  # the Final Twist: over the crest...
    ("x4b", 0.3, 36.0),  # ...round the Dragon's Coil...
    ("x5", 0.4, 30.5),  # ...and down to the gate
]
_A = sorted((at(n, f), z) for n, f, z in ANCHORS) + [(LENGTH, ANCHORS[0][2])]


def _lin(d):
    d %= LENGTH
    for (d0, z0), (d1, z1) in zip(_A, _A[1:]):
        if d0 <= d <= d1:
            return lerp(z0, z1, (d - d0) / max(1e-6, d1 - d0))
    return _A[-1][1]


def road_z(d, seg=None):
    return sum(_lin(d + k) for k in range(-12, 13, 3)) / 9.0


WIDE = {"b1", "b2", "n2", "r1", "r2"}  # the sweeping bridges and the sprint


def road_w(d, seg=None):
    s = d % LENGTH
    if s < 30 or s > at("x5", 0.5):
        return 18.0  # the start: room for the pack
    name = seg_of(s)
    if name in WIDE:
        return 17.0
    return 16.0  # room for a drift's entry swing


# ---------------------------------------------------------------- the canyon

GRID = (-260.0, 420.0, -360.0, 340.0)
CELL = 6.0
RIM = 96.0  # the canyon's rim, above everything
RIVER_Z = 0.0  # the river's water
BED = -3.0

# The river: down from the Great Falls at the north end, south through the gorge,
# under the Watchtower bridge, south beside the River Sprint and under the High Bridges.
RIVER = [(150.0, 266.0), (152.0, 200.0), (146.0, 130.0), (152.0, 66.0), (176.0, 20.0), (196.0, -20.0),
         (208.0, -70.0), (212.0, -130.0), (214.0, -200.0), (230.0, -280.0), (250.0, -380.0)]
RIVER_HW = 9.0
FALLS = (150.0, 280.0)  # the Great Falls' lip (it drops south into the gorge)
OASIS = (114.0, -212.0)  # the oasis pool's centre (inside the loop)
OASIS_R = 30.0
SKULL = (300.0, 115.0)  # the dragon's skull, out of the east wall
TOWER = (92.0, -86.0)  # the watchtower, between its hairpins
SPIRE = (156.0, -186.0)  # the Lone Spire the High Bridges sweep round
OUTPOST = (-40.0, 0.0)  # the fortress over the start


def river_d(x, y):
    best = 1e9
    for a, b in zip(RIVER, RIVER[1:]):
        d, _ = seg_dist(x, y, a[0], a[1], b[0], b[1])
        best = min(best, d)
    return best


def roads_near(x, y, reach=70.0):
    """The nearest point of each separate stretch of road within `reach`: [(distance,
    lap distance)], nearest first. Stretches are told apart by lap distance."""
    gx, gy = int(x // 20), int(y // 20)
    r = int(reach // 20) + 1
    found = []
    for i in range(gx - r, gx + r + 1):
        for j in range(gy - r, gy + r + 1):
            for k in _GRID.get((i, j), ()):
                p = PATH[k]
                d = math.hypot(p[0] - x, p[1] - y)
                if d < reach:
                    found.append((d, _D[k]))
    found.sort()
    out = []
    for d, s in found:
        if all(min(abs(s - t), LENGTH - abs(s - t)) > 50.0 for _, t in out):
            out.append((d, s))
    return out


WASH = [(-260.0, -170.0), (-120.0, -175.0), (-20.0, -205.0), (60.0, -262.0), (150.0, -290.0), (226.0, -275.0)]


def wash_d(x, y):
    best = 1e9
    for a, b in zip(WASH, WASH[1:]):
        d, _ = seg_dist(x, y, a[0], a[1], b[0], b[1])
        best = min(best, d)
    return best


def basin(x, y):
    """The canyon away from the roads: down to the river (and the dry wash in the
    south-west) in ledges, up to the rim round the edge."""
    rd = min(river_d(x, y), wash_d(x, y) + 14.0)
    z = lerp(BED + 6.0, RIM, sm((rd - 26.0) / 230.0))
    X0, X1, Y0, Y1 = GRID
    edge = min(x - X0, X1 - x, y - Y0, Y1 - y)
    z = max(z, lerp(z, RIM, 1.0 - sm((edge - 20.0) / 70.0)))
    z += 7.0 * noise(x, y, 0.02, 4.0)
    return lerp(z, round(z / 9.0) * 9.0, 0.55)  # ledges of harder rock


def natural(x, y):
    """The canyon before the roads shape it: each road's ledge with terraces stepping
    between nearby roads, then the canyon proper (down toward the river, up to the
    rim), the gorge cut down to the river, the oasis hollow."""
    near = roads_near(x, y)
    n = noise(x, y, 0.035, 1.0)
    b = basin(x, y)
    if near:
        w = [1.0 / (d * d + 4.0) for d, _ in near]
        zr = sum(wi * road_z(s) for wi, (_, s) in zip(w, near)) / sum(w)
        dmin = near[0][0]
        k = sm((dmin - 16.0 - 4.0 * n) / 26.0)
        z = lerp(zr - 0.6 + 1.0 * n, b, k)
    else:
        z = b
    # The gorge, down to the river bed.
    rd = river_d(x, y)
    if rd < 60:
        z = lerp(z, BED, 1.0 - sm((rd - RIVER_HW - 1.0) / 18.0))
    # The oasis hollow.
    od = math.hypot(x - OASIS[0], y - OASIS[1])
    if od < OASIS_R + 34:
        z = lerp(z, 11.5, 1.0 - sm((od - OASIS_R - 4) / 26.0))
        if od < OASIS_R + 4:
            z = min(z, lerp(6.5, 11.5, sm((od - OASIS_R + 4) / 8.0)))
    return z


def ground(x, y):
    return natural(x, y)


# ---------------------------------------------------------------- the Quarry Service Road


def _service_line():
    """The Service Road: off the Skeleton Pass's last bend, straight through the loading
    yard (under a stone arch), back onto the road where it turns south into the mesa.
    Narrow and dusty; it cuts the quarry's big right-left."""
    a = at("k3", 0.55)
    b = at("q2", 0.3)
    x0, y0, h0 = path_at(a)
    x3, y3, h3 = path_at(b)
    k = 0.35 * math.hypot(x3 - x0, y3 - y0)
    x1, y1 = x0 + k * math.cos(math.radians(h0)), y0 + k * math.sin(math.radians(h0))
    x2, y2 = x3 - k * math.cos(math.radians(h3)), y3 - k * math.sin(math.radians(h3))
    pts = []
    n = 60
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u ** 3 * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t ** 3 * x3
        y = u ** 3 * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t ** 3 * y3
        pts.append((x, y, lerp(road_z(a), road_z(b), t)))
    return pts, a, b


SERVICE, SERVICE_A, SERVICE_B = _service_line()
SERVICE_LEN = sum(math.dist(p[:2], q[:2]) for p, q in zip(SERVICE, SERVICE[1:]))


def open_sides(s):
    """No barriers here: where the Service Road leaves and rejoins the road."""
    s %= LENGTH
    return SERVICE_A - 14 < s < SERVICE_A + 24 or SERVICE_B - 24 < s < SERVICE_B + 12


# ---------------------------------------------------------------- zones

ZONES = [  # (lap distance, zone)
    (0.0, "outpost"),
    (S["c1"], "hairpins"),
    (S["n1"], "descent"),
    (S["k1"] - 10.0, "skeleton"),
    (S["q1"] - 10.0, "quarry"),
    (at("q2", 0.85), "caverns"),
    (at("t1", 0.75), "bridges"),
    (S["o1"] + 10.0, "oasis"),
    (S["r1"], "river"),
    (S["w0"] + 20.0, "watchtower"),
    (S["x1"] + 10.0, "twist"),
    (at("x5", 0.3), "outpost"),
]


def zone_of(s):
    s %= LENGTH
    z = ZONES[0][1]
    for d, name in ZONES:
        if s >= d:
            z = name
    return z
