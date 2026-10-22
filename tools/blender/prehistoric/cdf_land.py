# Celestial Dragon Festival's land (see celestial_dragon_festival.py): the lap, its
# heights and widths, the Palace Mount, the Observatory Pinnacle, the Cloud Chasm, the
# lagoon and the zones. Plain data, no Blender, so it can be checked and plotted alone.
# SPDX-License-Identifier: MIT
#
# The lap runs anticlockwise round the Palace Mount (inside the loop), out of the
# Festival Gate on the low terrace south of it, east through the lantern market to the
# waterfront, north over the lagoon on the Waterfall Bridge, west along the Dragon
# Promenade, up the Celestial Climb, west across the Cloud Chasm on the Star Bridge,
# right round the Observatory Pinnacle (the spiral comes out over the Star Bridge's far
# end), south along the Palace Terraces, down the Procession Causeway to the Fireworks
# Overlook, and round the Final Ascension back down to the gate.
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
    (150.0, 0.0, 70.0, "m1"),  # 2  the Lantern Market Curve: down through the market...
    (260.0, -90.0, 70.0, "m2"),  #    ...and out along the waterfront
    (390.0, -90.0, 60.0, "m3"),  # 3  the Waterfall Bridge: north over the lagoon
    (390.0, 280.0, 60.0, "p1"),  # 4  the Dragon Promenade: west across the great plaza
    (180.0, 280.0, 38.0, "c1"),  # 5  the Celestial Climb: up the mountain in S-bends
    (180.0, 380.0, 38.0, "c2"),
    (75.0, 380.0, 40.0, "c3"),
    (75.0, 470.0, 42.0, "c4"),
    (-320.0, 470.0, 58.0, "o1"),  # 6  the Star Bridge west over the Cloud Chasm, then
    (-320.0, 590.0, 58.0, "o2"),  # 7  the Observatory Spiral: right, round the pinnacle,
    (-200.0, 590.0, 58.0, "o3"),  #    out over the bridge's far end
    (-200.0, 320.0, 60.0, "t1"),  # 8  the Palace Terraces
    (-140.0, 240.0, 56.0, "t2"),
    (-200.0, 130.0, 56.0, "v1"),  # 9  the Procession Causeway, down to...
    (-305.0, 90.0, 48.0, "v2"),  # 10 ...the Fireworks Overlook
    (-280.0, -20.0, 50.0, "v3"),  # 11 the Final Ascension
    (-175.0, 0.0, 50.0, "f1"),  # 12 the Grand Finale: down onto the straight
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
    ("m2", 0.0, 24.0),  # down through the market to the waterfront
    ("m3", 0.0, 15.0, LEVEL),
    ("m3", "end", 15.5),
    ("p1", -110.0, 21.0),  # the Waterfall Bridge's crown
    ("p1", "end", 22.0, LEVEL),  # the Dragon Promenade
    ("c1", 0.0, 29.0),
    ("c2", 0.0, 37.0),  # the Celestial Climb
    ("c3", 0.0, 46.0),
    ("c4", 0.0, 53.0),
    ("c4", "end", 57.5),
    ("o1", -150.0, 62.0, LEVEL),  # the Star Bridge's crown
    ("o1", 0.0, 61.5),
    ("o2", 0.0, 65.5),  # round the pinnacle, climbing
    ("o3", 0.0, 70.0),
    ("o3", "end", 75.0),
    ("t1", 0.0, 78.0, LEVEL),  # the Palace Terraces
    ("t2", 0.0, 71.0),
    ("v1", 0.0, 55.5),  # down the Procession Causeway
    ("v2", 0.0, 47.0, LEVEL),  # the Fireworks Overlook
    ("v2", "end", 47.0, LEVEL),
    ("v3", "end", 50.0, LEVEL),  # the Final Ascension's crest
    ("f1", 40.0, 44.0),  # the Grand Finale: down to the gate
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


def road_z(d, seg=None):
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


WIDTH = {"st": 22.0, "m1": 18.0, "m2": 18.0, "m3": 18.0, "p1": 22.0, "c1": 17.0, "c2": 17.0, "c3": 17.0, "c4": 16.0, "o1": 16.0,
         "o2": 16.0, "o3": 17.0, "t1": 18.0, "t2": 20.0, "v1": 20.0, "v2": 18.0, "v3": 18.0, "f1": 20.0}


def road_w(d, seg=None):
    s = d % LENGTH
    if s < 40 or s > LENGTH - 80:
        return 22.0  # the start: room for the pack
    if STAR[0] < s < STAR[1]:
        return 15.0  # the Star Bridge: narrow-looking, high and exposed
    return WIDTH[seg_of(s)]


# The Star Bridge (lap distances): from the climb's top west to the pinnacle; the open
# stretch in its middle, no parapets.
STAR = (arc_end("c4") + 20.0, S["o1"] - 10.0)
STAR_OPEN = (lerp(STAR[0], STAR[1], 0.42), lerp(STAR[0], STAR[1], 0.42) + 70.0)

# ---------------------------------------------------------------- the land

GRID = (-560.0, 640.0, -330.0, 820.0)
CELL = 6.0
WATER_Z = 0.0  # the lagoon
SEA = -9.0  # its bed

PALACE = (40.0, 205.0)  # the Celestial Palace on the Palace Mount's top
PALACE_Z = 104.0
PINNACLE = (-262.0, 532.0)  # the Observatory Pinnacle inside the spiral
PINNACLE_Z = 96.0
OBSERVATORY = PINNACLE
GATE = (-20.0, 0.0)  # the Festival Gate over the start straight
PLAZA = (280.0, 330.0)  # the Dragon Promenade's great plaza
OVERLOOK = (-350.0, 96.0)


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
CHASM = [(60.0, 437.0), (-20.0, 453.0), (-120.0, 457.0), (-195.0, 448.0)]
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
    if -240 < x < 430 and -230 < y < 60:
        k = 1.0 - sm((-y - 150.0 - 20.0 * noise(x, y, 0.02, 3.0)) / 40.0)
        k *= 1.0 - sm((x - 400.0) / 30.0)
    if 170 < x < 480 and 250 < y < 380:
        k = max(k, (1.0 - sm((x - 430.0) / 30.0)) * (1.0 - sm((y - 360.0) / 20.0)))
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
INLET = (298.0, 500.0, -10.0, 236.0)


def inlet(x, y):
    """0..1: how deep inside the inlet (x, y) is."""
    x0, x1, y0, y1 = INLET
    e = min(x - x0, x1 - x, y - y0, y1 - y) + 6.0 * noise(x, y, 0.04, 9.0)
    return sm(e / 24.0)


def ground(x, y):
    z = natural(x, y)
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
