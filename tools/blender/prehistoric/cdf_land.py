# Celestial Dragon Festival's land (see celestial_dragon_festival.py): the lap, its
# heights and widths, the Palace Mount, the Observatory Pinnacle, the Cloud Chasm, the
# lagoon and the zones. Plain data, no Blender, so it can be checked and plotted alone.
# SPDX-License-Identifier: MIT
#
# The lap runs anticlockwise round the Palace Mount (inside the loop), out of the
# Festival Gate on the low terrace south of it, through the lantern market's chicane to
# the waterfront, north over the lagoon on the curving Waterfall Bridge, round the hairpin
# at the Great Dragon Shrine, up the Celestial Climb, west along the Star Bridge and over
# the Star Leap (the broken bridge: a zipper, a ramp, and a long flight over the Cloud
# Chasm), right round the Observatory Pinnacle (the spiral comes out over the Star
# Bridge's far end), down the Palace Terraces and the Procession Causeway to the
# Fireworks Overlook, and round the Final Ascension back down to the gate.
#
# Drawn as corners like Dragon Canyon: (x, y, radius, name), straights joined by arcs.
# Blender coordinates: x east, y north, z up.

import math

from dcanyon_land import fillet_path
from impact_land import clamp, lerp, noise, seg_dist, sm  # noqa: F401  (shared helpers)


def rnd(k):
    x = math.sin(k * 12.9898 + 78.233) * 43758.5453
    return x - math.floor(x)


# ---------------------------------------------------------------- the layout

CORNERS = [
    (40.0, 0.0, 0.0, "st"),  # 1  the Festival Gate: east along the start straight
    (120.0, 0.0, 40.0, "m1"),  # 2  the Lantern Market chicane: right, left...
    (165.0, -50.0, 34.0, "m2"),
    (245.0, -50.0, 34.0, "mx"),  #    ...right again, down to the waterfront
    (345.0, -75.0, 48.0, "m3"),  # 3  the Waterfall Bridge: north over the lagoon,
    (395.0, 40.0, 110.0, "w1"),  #    curving right then left
    (350.0, 160.0, 110.0, "w2"),
    (410.0, 285.0, 46.0, "p1"),  # 4  the Great Dragon Shrine: a hairpin right round it
    (262.0, 285.0, 46.0, "p2"),
    (262.0, 190.0, 38.0, "r1"),  #    and away west
    (172.0, 190.0, 38.0, "c1"),  # 5  the Celestial Climb: up the mountain in S-bends
    (172.0, 305.0, 38.0, "c2"),
    (75.0, 305.0, 40.0, "c3"),
    (75.0, 415.0, 42.0, "c4"),
    (-230.0, 415.0, 58.0, "o1"),  # 6  the Star Bridge and the Star Leap west over the Cloud
    (-230.0, 535.0, 58.0, "o2"),  #    Chasm; 7 the Observatory Spiral: right, round the
    (-110.0, 535.0, 58.0, "o3"),  #    pinnacle, out over the bridge's far end
    (-115.0, 300.0, 50.0, "t1"),  # 8  the Palace Terraces
    (-90.0, 225.0, 44.0, "t2"),
    (-160.0, 140.0, 46.0, "v1"),  # 9  the Procession Causeway, down to...
    (-255.0, 95.0, 44.0, "v2"),  # 10 ...the Fireworks Overlook
    (-230.0, -20.0, 44.0, "v3"),  # 11 the Final Ascension
    (-120.0, 0.0, 44.0, "f1"),  # 12 the Grand Finale: down onto the straight
]

PATH = fillet_path(CORNERS)
_D = [0.0]
for _a, _b in zip(PATH, PATH[1:]):
    _D.append(_D[-1] + math.hypot(_b[0] - _a[0], _b[1] - _a[1]))
LENGTH = _D[-1] + math.hypot(PATH[0][0] - PATH[-1][0], PATH[0][1] - PATH[-1][1])
NAMES = [c[3] for c in CORNERS]
S = {}  # corner name -> lap distance where its arc starts
for _i, _p in enumerate(PATH):
    S.setdefault(NAMES[int(_p[3])], _D[_i])


def arc_end(name):
    i = NAMES.index(name)
    for k, p in enumerate(PATH):
        if p[3] == i + 0.5:
            return _D[k]
    return S[name]


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
    """(x, y, heading degrees) s metres round the lap."""
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


def side(s, o):
    """The point `o` metres right of the centre line, s metres round."""
    x, y, h = path_at(s)
    r = math.radians(h - 90.0)
    return (x + o * math.cos(r), y + o * math.sin(r))


_GRID = {}
for _i, _p in enumerate(PATH):
    _GRID.setdefault((int(_p[0] // 20), int(_p[1] // 20)), []).append(_i)


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


def nearest(x, y):
    n = roads_near(x, y, 400.0)
    return n[0] if n else (1e9, 0.0)


# ---------------------------------------------------------------- heights

LEVEL = True
# (corner, where, z[, level]): `where` metres from the start of the corner's arc, or "end"
# for the end of its arc. A smooth curve (cubic Hermite) through them.
ANCHORS = [
    ("st", 0.0, 32.0, LEVEL),  # the Festival Gate's terrace
    ("m1", 0.0, 32.0, LEVEL),
    ("m2", 0.0, 27.0),  # down through the market's chicane...
    ("mx", 0.0, 21.0),
    ("m3", 0.0, 15.0, LEVEL),  # ...to the waterfront
    ("m3", "end", 15.5),
    ("w2", 0.0, 21.0),  # the Waterfall Bridge's crown
    ("p1", 0.0, 24.0, LEVEL),  # round the Great Dragon Shrine
    ("r1", "end", 24.0, LEVEL),
    ("c1", 0.0, 26.0),
    ("c2", 0.0, 35.0),  # the Celestial Climb
    ("c3", 0.0, 44.0),
    ("c4", 0.0, 53.0),
    ("c4", "end", 58.0, LEVEL),
    # (the Star Leap's run-up, gap and landing: jump_z below)
    ("o1", 0.0, 33.0, LEVEL),  # round the pinnacle, climbing
    ("o2", 0.0, 41.0),
    ("o3", 0.0, 49.0),
    ("o3", "end", 55.0),
    ("t1", 0.0, 58.0, LEVEL),  # down the Palace Terraces
    ("t2", 0.0, 53.0),
    ("v1", 0.0, 46.0),  # the Procession Causeway
    ("v2", 0.0, 40.0, LEVEL),  # the Fireworks Overlook
    ("v2", "end", 40.0, LEVEL),
    ("v3", "end", 42.0, LEVEL),  # the Final Ascension's crest
    ("f1", 40.0, 37.0),  # the Grand Finale: down to the gate
    ("st", -40.0, 32.0, LEVEL),
]


def _anchors():
    out = []
    for a in ANCHORS:
        name, where, z = a[:3]
        d = arc_end(name) if where == "end" else (S[name] + where) % LENGTH
        out.append((d, z, len(a) > 3))
    out.sort()
    n = len(out)
    res = []
    for i, (d, z, lvl) in enumerate(out):
        if lvl:
            m = 0.0
        else:
            dp, zp, _ = out[i - 1]
            dn, zn, _ = out[(i + 1) % n]
            if i == 0:
                dp -= LENGTH
            if i == n - 1:
                dn += LENGTH
            m = (zn - zp) / (dn - dp)
        res.append((d, z, m))
    return res + [(res[0][0] + LENGTH, res[0][1], res[0][2])]


_A = _anchors()

# The Star Leap (lap distances along the Star Bridge): a gentle run-up to the lip (the
# last 12 m a 30% kicker), the gap (the route runs straight through the air), and the
# landing 12 m below: a wide ramp falling away at 30% (fast karts fly far down it),
# easing out to 12%. At top speed you drop onto the landing's lip; with the zipper on
# the run-up you fly about forty metres, with a rainbow boost seventy.
RUNUP = arc_end("c4") + 4.0  # (level here)
LIP = RUNUP + 56.0
GAP = 16.0
LAND = LIP + GAP
JUMP_Z = [  # (lap distance, z): straight lines between these
    (LIP - 12.0, 60.6),
    (LIP, 64.2),
    (LAND, 52.2),
    (LAND + 40.0, 40.2),
    (LAND + 100.0, 33.0),
]


def _smooth_join(d, d0, z0, m0, d1, z1, m1):
    h = d1 - d0
    t = (d - d0) / max(1e-6, h)
    t2, t3 = t * t, t * t * t
    return (2 * t3 - 3 * t2 + 1) * z0 + (t3 - 2 * t2 + t) * h * m0 + (-2 * t3 + 3 * t2) * z1 + (t3 - t2) * h * m1


def road_z(d, seg=None):
    d %= LENGTH
    if RUNUP <= d <= S["o1"]:
        (a0, za), (a1, zb) = JUMP_Z[0], JUMP_Z[-1]
        if d < a0:  # ease up from the level corner into the kicker
            return _smooth_join(d, RUNUP, 58.0, 0.0, a0, za, 0.12)
        if d > a1:  # ease out of the landing into the spiral
            return _smooth_join(d, a1, zb, -0.12, S["o1"], _base_z(S["o1"]), 0.0)
        for (d0, z0), (d1, z1) in zip(JUMP_Z, JUMP_Z[1:]):
            if d0 <= d <= d1:
                return lerp(z0, z1, (d - d0) / max(1e-6, d1 - d0))
    return _base_z(d)


def _base_z(d):
    d %= LENGTH
    if d < _A[0][0]:
        d += LENGTH
    for (d0, z0, m0), (d1, z1, m1) in zip(_A, _A[1:]):
        if d0 <= d <= d1:
            h = d1 - d0
            t = (d - d0) / max(1e-6, h)
            t2, t3 = t * t, t * t * t
            return ((2 * t3 - 3 * t2 + 1) * z0 + (t3 - 2 * t2 + t) * h * m0 + (-2 * t3 + 3 * t2) * z1 + (t3 - t2) * h * m1)
    return _A[0][1]


WIDTH = {"st": 22.0, "m1": 18.0, "m2": 18.0, "mx": 18.0, "m3": 18.0, "w1": 18.0, "w2": 18.0, "p1": 20.0, "p2": 20.0, "r1": 18.0,
         "c1": 17.0, "c2": 17.0, "c3": 17.0, "c4": 17.0, "o1": 16.0, "o2": 16.0, "o3": 17.0, "t1": 18.0, "t2": 20.0, "v1": 20.0,
         "v2": 18.0, "v3": 18.0, "f1": 20.0}


def road_w(d, seg=None):
    s = d % LENGTH
    if s < 40 or s > LENGTH - 80:
        return 22.0  # the start: room for the pack
    if LIP - 40 <= s <= LAND + 70:
        return 22.0  # the Star Leap: a broad ramp, a broad landing
    if STAR[0] < s < STAR[1]:
        return 16.0
    return WIDTH[seg_of(s)]


# The Star Bridge (lap distances): from the climb's top west to the pinnacle.
STAR = (arc_end("c4") + 2.0, S["o1"] - 6.0)

# ---------------------------------------------------------------- the land

GRID = (-560.0, 640.0, -330.0, 820.0)
CELL = 6.0
WATER_Z = 0.0  # the lagoon
SEA = -9.0  # its bed

PALACE = (40.0, 205.0)  # the Celestial Palace on the Palace Mount's top
PALACE_Z = 104.0
PINNACLE = (-172.0, 477.0)  # the Observatory Pinnacle inside the spiral
PINNACLE_Z = 96.0
OBSERVATORY = PINNACLE
GATE = (-20.0, 0.0)  # the Festival Gate over the start straight
PLAZA = (336.0, 240.0)  # the Great Dragon Shrine, inside the hairpin
SHRINE = PLAZA
SHRINE_R = 34.0
OVERLOOK = (-300.0, 96.0)


def _winding(x, y, poly):
    w = 0
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i - 1]
        x1, y1 = poly[i]
        if y0 <= y < y1 or y1 <= y < y0:
            xi = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if xi > x:
                w += 1 if y1 > y0 else -1
    return w


_POLY = [(p[0], p[1]) for p in PATH[::3]]


def inside(x, y):
    """Inside the lap's loops (the Palace Mount; the pinnacle inside the spiral)."""
    return _winding(x, y, _POLY) != 0


# The Cloud Chasm: the deep cleft between the Palace Mount and the northern heights that
# the Star Bridge crosses (floor far below, filled with cloud).
CHASM = [(50.0, 392.0), (-20.0, 402.0), (-100.0, 405.0), (-160.0, 398.0)]
CHASM_HW = 36.0


def chasm_d(x, y):
    best = 1e9
    for a, b in zip(CHASM, CHASM[1:]):
        d, _ = seg_dist(x, y, a[0], a[1], b[0], b[1])
        best = min(best, d)
    return best


# The city's terraces outside the loop (south and east): flat ground at about the road's
# level, out to the lagoon's edge.
def city(x, y):
    """0..1: how much (x, y) is the festival city's ground (south of the start straight,
    round the market, along the waterfront, round the plaza)."""
    k = 0.0
    if -220 < x < 430 and -230 < y < 60:
        k = 1.0 - sm((-y - 150.0 - 20.0 * noise(x, y, 0.02, 3.0)) / 40.0)
        k *= 1.0 - sm((x - 400.0) / 30.0)
    sd = math.hypot(x - SHRINE[0], y - SHRINE[1])
    k = max(k, 1.0 - sm((sd - 120.0) / 30.0))
    return k


def massif(x, y):
    """The Palace Mount's own height (inside the loop): up from the roads to the palace's
    terraced crown."""
    d = math.hypot(x - PALACE[0], y - PALACE[1])
    crown = PALACE_Z - 2.0
    return lerp(crown, 40.0, sm((d - 90.0) / 260.0)) + 4.0 * noise(x, y, 0.03, 5.0)


def pinnacle(x, y):
    d = math.hypot(x - PINNACLE[0], y - PINNACLE[1])
    return PINNACLE_Z - sm((d - 20.0) / 30.0) * 30.0


def natural(x, y):
    """The land before the roads shape it."""
    near = roads_near(x, y, 120.0)
    n = noise(x, y, 0.035, 1.0)
    ins = inside(x, y)
    pd = math.hypot(x - PINNACLE[0], y - PINNACLE[1])
    if pd < 52:
        base = pinnacle(x, y)
    elif ins:
        base = massif(x, y)
    else:
        base = SEA + 1.5 * noise(x, y, 0.02, 2.0)
        c = city(x, y)
        if c > 0:
            base = lerp(base, 8.0 + 1.0 * n, c)
    if near:
        w = [1.0 / (d * d + 4.0) for d, _ in near[:3]]
        zr = sum(wi * road_z(s) for wi, (_, s) in zip(w, near[:3])) / sum(w)
        dmin = near[0][0]
        # Next to the road: its ledge. Inside: the hill rises behind; outside a cliff
        # drops away (the city's terraces step down more gently).
        k = sm((dmin - 14.0 - 3.0 * n) / (55.0 if ins else 30.0))
        z = lerp(zr - 0.6 + 0.6 * n, max(base, zr + 2.0) if ins else min(base, zr - 1.0), k)
        if ins and pd >= 52:
            # The mountain's gardens: terraces stepping up from the road.
            z = lerp(z, max(zr - 0.6, round(z / 7.0) * 7.0), 0.7 * sm((dmin - 18.0) / 12.0))
        if not ins and city(x, y) > 0.3:
            z = lerp(zr - 0.6, min(zr - 0.6, 8.0 + n), sm((dmin - 30.0) / 60.0))
    else:
        z = base
    # The Cloud Chasm.
    cd = chasm_d(x, y)
    if cd < CHASM_HW + 40:
        z = lerp(z, SEA - 6.0, 1.0 - sm((cd - CHASM_HW) / 40.0))
    return z


# The lagoon's inlet the Waterfall Bridge crosses: between the Palace Mount's eastern
# cliffs and the islands.
INLET = (300.0, 500.0, -10.0, 196.0)


def inlet(x, y):
    """0..1: how deep inside the inlet (x, y) is."""
    x0, x1, y0, y1 = INLET
    e = min(x - x0, x1 - x, y - y0, y1 - y) + 6.0 * noise(x, y, 0.04, 9.0)
    return sm(e / 24.0)


def ground(x, y):
    z = natural(x, y)
    # The Great Dragon Shrine's plaza, inside the hairpin: flat, at the road's level.
    sd = math.hypot(x - SHRINE[0], y - SHRINE[1])
    if sd < 110:
        z = lerp(23.4, z, sm((sd - 70.0) / 40.0))
    k = inlet(x, y)
    if k > 0:
        z = lerp(z, SEA, k)
    return z


# ---------------------------------------------------------------- zones

ZONES = [  # (lap distance, zone)
    (0.0, "gate"),
    (S["m1"] - 20.0, "market"),
    (arc_end("m3") - 10.0, "falls"),
    (S["p1"] + 30.0, "promenade"),
    (S["c1"] + 10.0, "climb"),
    (STAR[0], "star"),
    (S["o1"] - 10.0, "observatory"),
    (arc_end("o3") + 40.0, "terraces"),
    (arc_end("t2") + 10.0, "causeway"),
    (S["v2"] - 20.0, "overlook"),
    (arc_end("v2") + 20.0, "ascension"),
    (S["f1"] - 10.0, "finale"),
    (LENGTH - 60.0, "gate"),
]


def zone_of(s):
    s %= LENGTH
    z = ZONES[0][1]
    for d, name in ZONES:
        if s >= d:
            z = name
    return z


if __name__ == "__main__":
    print("length %.0f" % LENGTH)
    for n in NAMES:
        print(n, round(S[n]), round(road_z(S[n]), 1))
    worst = max(range(0, int(LENGTH), 5), key=lambda s: abs(road_z(s + 5) - road_z(s)))
    print("steepest %.1f%% at %d" % (abs(road_z(worst + 5) - road_z(worst)) * 20, worst))
    print("star", [round(v) for v in STAR], "open", [round(v) for v in STAR_OPEN])
