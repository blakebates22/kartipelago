# Snow Dragon Pass's land (see snow_dragon_pass.py): the road network, its heights and
# widths, the mountains, the gorge and the zones. Plain data, no Blender, so it can be
# checked and plotted on its own.
# SPDX-License-Identifier: MIT
#
# The course is a network, not one loop: a shared opening, the first split (the High
# Cliff Road or the Frozen Supply Road), a shared middle, the second split (the Monastery
# Ridge or the Frozen Aqueduct) and a shared finale. Each of the four branch combinations
# is a whole lap of its own (a "lap route"); the main route is Cliff + Ridge.
#
# Each section is drawn as corners: (x, y, radius, name) points joined by straights, each
# corner an arc of that radius tangent to both straights (Dragon Canyon's fillets). For
# the shared road to be the same whichever branch follows, a split's two branches start
# on the same ray out of the last shared corner (the one that peels off first turns away
# while the other runs on), and end on the same ray into the first shared corner after.
# Blender coordinates: x east, y north, z up.

import math

from dcanyon_land import fillet_path
from impact_land import clamp, lerp, noise, seg_dist, sm  # noqa: F401  (shared helpers)


def rnd(k):
    x = math.sin(k * 12.9898 + 78.233) * 43758.5453
    return x - math.floor(x)


# ---------------------------------------------------------------- the network

SECTIONS = {
    # 1-2  The Frozen Gate and the Windy Village: out of the citadel's gate, down
    #      through the village, to the first fork.
    "opening": [
        (-60.0, 0.0, 0.0, "st"),
        (90.0, 0.0, 60.0, "g1"),
        (190.0, -100.0, 60.0, "g2"),
        (300.0, -100.0, 50.0, "fork1"),
    ],
    # 3-4  The High Cliff Road: up the mountain's west face in switchbacks to the Dragon
    #      Overlook, over narrow stone bridges, and down to the crossing. Short, tight.
    "cliff": [
        (300.0, -250.0, 26.0, "a1"),
        (232.0, -250.0, 26.0, "a2"),
        (232.0, -302.0, 26.0, "a3"),
        (320.0, -302.0, 28.0, "a4"),
        (320.0, -400.0, 34.0, "a5"),
        (270.0, -460.0, 40.0, "a6"),
        (270.0, -560.0, 36.0, "a7"),
    ],
    # 5-6  The Frozen Supply Road: down round the mountain's east side past the depots
    #      and labour camps, through the blue ice cavern, back up to the crossing. Wide.
    "supply": [
        (300.0, -190.0, 60.0, "b1"),
        (396.0, -250.0, 90.0, "b2"),
        (396.0, -440.0, 80.0, "b3"),
        (360.0, -560.0, 60.0, "b4"),
    ],
    # 7-8  Starvation Road, the Broken Bridges over the frozen gorge, the Avalanche Run.
    "middle": [
        (170.0, -560.0, 70.0, "m1"),
        (40.0, -610.0, 90.0, "m2"),
        (-140.0, -610.0, 50.0, "fork2"),
    ],
    # 9-10  The Monastery Ridge: a switchback up the mountain's south face, east over the
    #       monastery's bridge (the aqueduct runs beneath), up to the monastery, down a
    #       steep exit.
    "ridge": [
        (-140.0, -530.0, 26.0, "r1"),
        (-230.0, -530.0, 26.0, "r2"),
        (-230.0, -478.0, 26.0, "r3"),
        (-105.0, -478.0, 36.0, "r4"),
        (-105.0, -390.0, 34.0, "r5"),
        (-280.0, -300.0, 40.0, "r6"),
    ],
    # 11-12 The Frozen Aqueduct: down along the old water channels, broad and fast, under
    #       the monastery's bridge, out along the frozen falls, a couple of tighter
    #       tunnel bends back to the ridge road.
    "aqueduct": [
        (-140.0, -440.0, 60.0, "q1"),
        (-349.0, -440.0, 50.0, "q2"),
        (-349.0, -335.0, 34.0, "q3"),
        (-280.0, -335.0, 34.0, "q4"),
    ],
    # 13-14 The Final Ascent: up past the guardian dragons to the Dragon Citadel's gate.
    "finale": [
        (-280.0, -220.0, 50.0, "f1"),
        (-200.0, -120.0, 45.0, "f2"),
        (-220.0, 0.0, 50.0, "f3"),
    ],
}

SPLITS = (("cliff", "supply"), ("ridge", "aqueduct"))
ORDER = ("opening", None, "middle", None, "finale")

# The four whole-lap routes: main first (its id is "main" in the exported package).
COMBOS = {
    "main": ("cliff", "ridge"),
    "Lap Cliff Aqueduct": ("cliff", "aqueduct"),
    "Lap Supply Ridge": ("supply", "ridge"),
    "Lap Supply Aqueduct": ("supply", "aqueduct"),
}


def combo_corners(b1, b2):
    S_ = SECTIONS
    return S_["opening"] + S_[b1] + S_["middle"] + S_[b2] + S_["finale"]


class Lap:
    """One whole-lap route through the network: its path, distances and corner starts."""

    def __init__(self, cid, b1, b2):
        self.id = cid
        self.branches = (b1, b2)
        self.corners = combo_corners(b1, b2)
        self.path = fillet_path(self.corners)
        D = [0.0]
        for a, b in zip(self.path, self.path[1:]):
            D.append(D[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        self.D = D
        self.length = D[-1] + math.hypot(self.path[0][0] - self.path[-1][0], self.path[0][1] - self.path[-1][1])
        self.names = [c[3] for c in self.corners]
        self.S = {}
        for i, p in enumerate(self.path):
            self.S.setdefault(self.names[int(p[3])], D[i])
        # Which section each corner index belongs to.
        sec = []
        for name in ("opening", b1, "middle", b2, "finale"):
            sec += [name] * len(SECTIONS[name])
        self.section_of_corner = sec

    def at(self, name, frac=0.0):
        i = self.names.index(name)
        s0 = self.S[name]
        s1 = self.S[self.names[i + 1]] if i + 1 < len(self.names) else self.length
        return s0 + (s1 - s0) * frac

    def section(self, k):
        """Section of path point k (a straight belongs to the corner before it)."""
        return self.section_of_corner[int(self.path[k][3])]

    def point_at(self, s):
        s %= self.length
        lo, hi = 0, len(self.D) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self.D[mid] <= s:
                lo = mid
            else:
                hi = mid - 1
        a = self.path[lo]
        b = self.path[(lo + 1) % len(self.path)]
        d1 = self.D[lo + 1] if lo + 1 < len(self.D) else self.length
        t = (s - self.D[lo]) / max(1e-6, d1 - self.D[lo])
        return (lerp(a[0], b[0], t), lerp(a[1], b[1], t), a[2])


LAPS = {cid: Lap(cid, *br) for cid, br in COMBOS.items()}
MAIN = LAPS["main"]


def divergence(lap, ref=MAIN, tol=0.3):
    """Stretches [(s0, s1)] of `lap` (its own distances) that leave the reference lap's
    road: the branches it takes that the reference doesn't."""
    import bisect

    grid = {}
    for p in ref.path:
        grid.setdefault((int(p[0] // 10), int(p[1] // 10)), []).append(p)

    def off(x, y):
        best = 1e9
        gx, gy = int(x // 10), int(y // 10)
        for i in range(gx - 1, gx + 2):
            for j in range(gy - 1, gy + 2):
                for q in grid.get((i, j), ()):
                    best = min(best, (q[0] - x) ** 2 + (q[1] - y) ** 2)
        return math.sqrt(best)

    out = []
    run = None
    for k, p in enumerate(lap.path):
        o = off(p[0], p[1]) > tol
        if o and run is None:
            run = [lap.D[k], lap.D[k]]
        if o:
            run[1] = lap.D[k]
        if not o and run is not None:
            out.append(tuple(run))
            run = None
    if run:
        out.append(tuple(run))
    del bisect
    # Join stretches a few metres apart (numerical wobble where two paths run together)
    # and drop slivers.
    joined = []
    for r in out:
        if joined and r[0] - joined[-1][1] < 15.0:
            joined[-1] = (joined[-1][0], r[1])
        else:
            joined.append(r)
    return [r for r in joined if r[1] - r[0] > 10.0]


# ---------------------------------------------------------------- heights

# (corner, where, z[, level]): `where` is metres from the start of the corner's arc, or
# "end" for the end of its arc. Heights follow a smooth curve through the anchors
# (cubic Hermite); `level` anchors are flat (the forks and merges, so the shared road is
# the same whichever branch comes next).
LEVEL = True
ANCHORS = {
    "opening": [("st", 0.0, 108.0), ("g1", 30.0, 107.0), ("g2", 40.0, 106.0), ("fork1", "end", 104.0, LEVEL)],
    "cliff": [("a1", 0.0, 105.0), ("a3", "end", 109.0), ("a4", "end", 114.0, LEVEL), ("a5", 0.0, 114.0, LEVEL),
              ("a6", 0.0, 108.0), ("a7", "end", 100.0, LEVEL)],
    "supply": [("b1", 0.0, 104.0, LEVEL), ("b1", 50.0, 104.0, LEVEL), ("b2", 30.0, 99.0), ("b3", 0.0, 90.0, LEVEL), ("b3", "end", 91.0),
               ("b4", "end", 100.0, LEVEL)],
    "middle": [("m1", 0.0, 100.0, LEVEL), ("m1", "end", 98.0), ("m2", 0.0, 93.0), ("fork2", "end", 78.0, LEVEL)],
    "ridge": [("r2", 0.0, 80.0), ("r3", "end", 86.0), ("r4", 0.0, 91.0), ("r5", "end", 98.0, LEVEL),
              ("r6", 0.0, 82.0, LEVEL), ("r6", "end", 82.0, LEVEL)],
    "aqueduct": [("q1", 0.0, 78.0, LEVEL), ("q1", "end", 72.0), ("q2", "end", 71.0), ("q4", "end", 82.0, LEVEL)],
    "finale": [("f1", 0.0, 82.0, LEVEL), ("f3", 0.0, 100.0)],
}


def _arc_end(lap, name):
    i = lap.names.index(name)
    for k, p in enumerate(lap.path):
        if p[3] == i + 0.5:
            return lap.D[k]
    return lap.S[name]


def _anchors(lap):
    out = []
    for sec in ("opening", lap.branches[0], "middle", lap.branches[1], "finale"):
        for a in ANCHORS[sec]:
            name, where, z = a[:3]
            if name not in lap.names:
                continue
            d = _arc_end(lap, name) if where == "end" else lap.S[name] + where
            out.append((d, z, len(a) > 3))
    out.sort()
    # Slopes: level anchors flat; the rest from their neighbours (wrapping round the lap).
    n = len(out)
    L_ = lap.length
    res = []
    for i, (d, z, lvl) in enumerate(out):
        if lvl:
            m = 0.0
        else:
            dp, zp, _ = out[i - 1]
            dn, zn, _ = out[(i + 1) % n]
            if i == 0:
                dp -= L_
            if i == n - 1:
                dn += L_
            m = (zn - zp) / (dn - dp)
        res.append((d, z, m))
    return res + [(res[0][0] + L_, res[0][1], res[0][2])]


for _lap in LAPS.values():
    _lap.anchors = _anchors(_lap)


def road_z(lap, d):
    A = lap.anchors
    d %= lap.length
    if d < A[0][0]:
        d += lap.length
    for (d0, z0, m0), (d1, z1, m1) in zip(A, A[1:]):
        if d0 <= d <= d1:
            h = d1 - d0
            t = (d - d0) / max(1e-6, h)
            t2, t3 = t * t, t * t * t
            return ((2 * t3 - 3 * t2 + 1) * z0 + (t3 - 2 * t2 + t) * h * m0 + (-2 * t3 + 3 * t2) * z1
                    + (t3 - t2) * h * m1)
    return A[0][1]


WIDTH = {"opening": 16.0, "cliff": 14.0, "supply": 18.0, "middle": 17.0, "ridge": 15.0, "aqueduct": 17.0, "finale": 16.0}


def road_w(lap, d):
    d %= lap.length
    if d < 40 or d > lap.length - 60:
        return 18.0  # the start: room for the pack
    k = min(range(len(lap.D)), key=lambda i: abs(lap.D[i] - d)) if False else _idx(lap, d)
    return WIDTH[lap.section(k)]


def _idx(lap, d):
    lo, hi = 0, len(lap.D) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if lap.D[mid] <= d:
            lo = mid
        else:
            hi = mid - 1
    return lo


def lap_points(lap, every=6.0):
    """(x, y, z, width) every `every` metres round a lap."""
    n = int(lap.length // every)
    out = []
    for k in range(n):
        d = k * lap.length / n
        x, y, _ = lap.point_at(d)
        out.append((x, y, road_z(lap, d), road_w(lap, d)))
    return out


# ---------------------------------------------------------------- the network's road points

# Every stretch of road once: the main lap, then the branches only the other laps take.
# (x, y, z, width, key) every 3 m; `key` tells stretches apart (section, distance).
NET = []
for _x, _y, _z, _w in lap_points(MAIN, 3.0):
    NET.append((_x, _y, _z, _w))
_NET_KEY = [("main", i * 3.0) for i in range(len(NET))]
for _cid in ("Lap Supply Aqueduct",):
    _lap = LAPS[_cid]
    for _s0, _s1 in divergence(_lap):
        _s = _s0
        while _s <= _s1:
            _x, _y, _ = _lap.point_at(_s)
            NET.append((_x, _y, road_z(_lap, _s), road_w(_lap, _s)))
            _NET_KEY.append((_cid, _s))
            _s += 3.0

_NGRID = {}
for _i, _p in enumerate(NET):
    _NGRID.setdefault((int(_p[0] // 20), int(_p[1] // 20)), []).append(_i)


def _stretch(i):
    """A number per stretch of road, so nearby points of one road count once."""
    lap, s = _NET_KEY[i]
    return (lap, int(s // 40))


def roads_near(x, y, reach=80.0):
    """The nearest point of each separate stretch of road within `reach`:
    [(distance, z, width)], nearest first. Stretches more than 50 m apart along the road
    (or on different laps' branches) count separately."""
    gx, gy = int(x // 20), int(y // 20)
    r = int(reach // 20) + 1
    found = []
    for i in range(gx - r, gx + r + 1):
        for j in range(gy - r, gy + r + 1):
            for k in _NGRID.get((i, j), ()):
                p = NET[k]
                d = math.hypot(p[0] - x, p[1] - y)
                if d < reach:
                    found.append((d, k))
    found.sort()
    out = []
    seen = []
    for d, k in found:
        lap, s = _NET_KEY[k]
        if any(lap == l2 and abs(s - s2) < 50.0 for l2, s2 in seen):
            continue
        seen.append((lap, s))
        out.append((d, NET[k][2], NET[k][3]))
    return out


def net_d(x, y):
    n = roads_near(x, y, 400.0)
    return n[0][0] if n else 1e9


# ---------------------------------------------------------------- the mountains

GRID = (-520.0, 640.0, -860.0, 300.0)
CELL = 6.0
FLOOR = 40.0  # the gorge's frozen river, the lowest anything goes
RIM = 260.0  # the ring of peaks round it all

# Landforms: (cx, cy, rx, ry, peak, name). Each rises smoothly from its edge to its peak.
MASSIFS = [
    (40.0, -300.0, 230.0, 230.0, 235.0, "Central Massif"),  # inside the loop: the great peaks
    (370.0, -380.0, 42.0, 130.0, 136.0, "Overlook Ridge"),  # between the Cliff and Supply roads
    (-150.0, -305.0, 44.0, 34.0, 128.0, "Monastery Mount"),  # above the Monastery Ridge's high corner
    (-120.0, 150.0, 120.0, 90.0, 190.0, "Citadel Crag"),  # the Dragon Citadel's rock, north of the start
]

# The frozen gorge the Broken Bridges cross: down from the massif's falls, south.
GORGE = [(118.0, -420.0), (106.0, -520.0), (96.0, -620.0), (84.0, -720.0), (60.0, -860.0)]
GORGE_HW = 14.0

# Landmarks.
CITADEL = (-110.0, 140.0)  # the Dragon Citadel, high above the start
FROZEN_GATE = (40.0, 0.0)  # the guarded gate on the start straight
OVERLOOK = (346.0, -300.0)  # the Dragon Overlook's monument, out on the ridge's prow
MONASTERY = (-150.0, -305.0)  # on the Monastery Mount's top, above the ridge road


def _massif(x, y):
    best = None
    for cx, cy, rx, ry, peak, _ in MASSIFS:
        dx, dy = (x - cx) / rx, (y - cy) / ry
        r = math.hypot(dx, dy)
        if r < 1.0:
            v = peak * (1.0 - sm(r) * 0.85) + 10.0 * noise(x, y, 0.03, 7.0)
            best = v if best is None else max(best, v)
    return best


def gorge_d(x, y):
    best = 1e9
    for a, b in zip(GORGE, GORGE[1:]):
        d, _ = seg_dist(x, y, a[0], a[1], b[0], b[1])
        best = min(best, d)
    return best


_OUTER = [(p[0], p[1]) for p in LAPS["Lap Supply Aqueduct"].path[::4]]


def inside(x, y):
    """Inside the course's outer edge (the Supply + Aqueduct lap): the mountains' side of
    the roads. Outside, the land falls away to the valleys."""
    c = False
    n = len(_OUTER)
    for i in range(n):
        (x0, y0), (x1, y1) = _OUTER[i], _OUTER[i - 1]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            c = not c
    return c


def basin(x, y, near=None):
    """The land away from the roads: inside the course it climbs steeply to the massifs
    (the uphill side of every mountain road); outside it drops away to the valleys and
    then climbs to the ring of peaks round the edge."""
    near = near if near is not None else roads_near(x, y, 300.0)
    if near:
        w = [1.0 / (d * d + 4.0) for d, _, _ in near[:4]]
        zr = sum(wi * z for wi, (_, z, _) in zip(w, near[:4])) / sum(w)
        d = near[0][0]
    else:
        zr, d = 90.0, 300.0
    n = noise(x, y, 0.02, 2.0)
    if inside(x, y):
        z = zr + 3.0 + max(0.0, d - 12.0) * (0.55 + 0.15 * n)
        m = _massif(x, y)
        if m is not None:
            z = max(z, lerp(z, m, sm((d - 20.0) / 60.0)))
        z = min(z, 280.0)
    else:
        z = zr - 24.0 * sm((d - 14.0) / 46.0) + max(0.0, d - 120.0) * 0.5 + 8.0 * n
        m = _massif(x, y)
        if m is not None:
            z = max(z, lerp(z, m, sm((d - 20.0) / 60.0)))
    X0, X1, Y0, Y1 = GRID
    edge = min(x - X0, X1 - x, y - Y0, Y1 - y)
    z = lerp(z, max(z, RIM + 30.0 * noise(x, y, 0.01, 5.0)), 1.0 - sm((edge - 30.0) / 160.0))
    return z


def natural(x, y):
    """The mountains before the roads shape them: each road's ledge cut into the slope,
    terraces between nearby roads, then the land proper, and the gorge cut down to the
    frozen river."""
    near = roads_near(x, y, 300.0)
    n = noise(x, y, 0.035, 1.0)
    b = basin(x, y, near)
    close = [q for q in near if q[0] < 90.0]
    if close:
        w = [1.0 / (d * d + 4.0) for d, _, _ in close]
        zr = sum(wi * z for wi, (_, z, _) in zip(w, close)) / sum(w)
        dmin, _, wmin = close[0]
        k = sm((dmin - wmin / 2 - 5.0 - 3.0 * n) / 22.0)
        z = lerp(zr - 0.6 + 0.8 * n, b, k)
    else:
        z = b
    gd = gorge_d(x, y)
    if gd < 70:
        z = lerp(z, FLOOR, 1.0 - sm((gd - GORGE_HW) / 30.0))
    return z


def ground(x, y):
    return natural(x, y)


# ---------------------------------------------------------------- branches, junctions, zones


def _main_s(x, y):
    """Main-lap distance of the main road point nearest (x, y)."""
    best = (1e18, 0.0)
    for k, p in enumerate(MAIN.path):
        d = (p[0] - x) ** 2 + (p[1] - y) ** 2
        if d < best[0]:
            best = (d, MAIN.D[k])
    return best[1]


# The branches only the other laps take, as stretches of those laps: {branch: (lap, s0, s1)}.
# (Supply: the Supply + Ridge lap's own stretch; Aqueduct: the Cliff + Aqueduct lap's.)
LANES = {}
_sr = divergence(LAPS["Lap Supply Ridge"])
LANES["supply"] = ("Lap Supply Ridge",) + tuple(_sr[0])
_ca = divergence(LAPS["Lap Cliff Aqueduct"])
LANES["aqueduct"] = ("Lap Cliff Aqueduct",) + tuple(_ca[0])

# Where each split leaves and rejoins the main road (main-lap distances).
SPLIT1 = (_main_s(*LAPS["Lap Supply Ridge"].point_at(LANES["supply"][1])[:2]),
          _main_s(*LAPS["Lap Supply Ridge"].point_at(LANES["supply"][2])[:2]))
SPLIT2 = (_main_s(*LAPS["Lap Cliff Aqueduct"].point_at(LANES["aqueduct"][1])[:2]),
          _main_s(*LAPS["Lap Cliff Aqueduct"].point_at(LANES["aqueduct"][2])[:2]))


def lane_points(branch, step=3.0, pad=0.0):
    """(x, y, z, width, s) along a branch's lane, `pad` metres beyond each end."""
    lap_id, s0, s1 = LANES[branch]
    lap = LAPS[lap_id]
    out = []
    s = s0 - pad
    while s <= s1 + pad + 1e-6:
        x, y, _ = lap.point_at(s)
        out.append((x, y, road_z(lap, s), road_w(lap, s), s))
        s += step
    return out


def junction_open(s):
    """No barriers on the main road here: where a branch leaves or joins it."""
    s %= MAIN.length
    for a, b in (SPLIT1, SPLIT2):
        if a - 12.0 < s < a + 70.0 or b - 70.0 < s < b + 12.0:
            return True
    return False


ZONES = [  # (main-lap distance, zone)
    (0.0, "gate"),
    (MAIN.S["g1"] - 30.0, "village"),
    (SPLIT1[0], "cliff"),
    (SPLIT1[1], "starvation"),
    (MAIN.S["m2"] - 20.0, "avalanche"),
    (SPLIT2[0], "ridge"),
    (SPLIT2[1], "ascent"),
    (MAIN.length - 120.0, "gate"),
]


def zone_of(s):
    s %= MAIN.length
    z = ZONES[0][1]
    for d, name in ZONES:
        if s >= d:
            z = name
    return z
