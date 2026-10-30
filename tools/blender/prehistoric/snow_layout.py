# The Snow Kingdom's layout (v3, on pocket_kit): pure geometry, no Blender (snow_region.py
# builds it).
# SPDX-License-Identifier: MIT
#
# Built like Dinosaur Valley's (Blake, Oct 26): a pocket for each of the kingdom's worlds,
# walled off by the mountains so you only see the one you're in, and the main road one
# winding loop through them (Brachio's 1-on-1), a threshold between each:
#
#   Hearthglow (hub)  the village in its hollow, warm lights, the great tree; the Burnt
#                     Gorge comes up into it from the valley, south
#     the Gatehouse     through Frostveil's curtain wall, a portcullis at each end
#   Frostveil (W)     the citadel's bailey: battlements, towers, the keep's gate
#     the Climb         a switchback ravine up out of the bailey, north
#   Summit (NW)       the high meadow under the giant tree, mammoths, snowy pines (Rimefang's
#                     lair in its north wall, after his attack)
#     the Ice Cave      bored through the glacier's tongue, blue light in its walls
#   Aurora (NE)       the glacier: blue ice, crevasses, the rift, the sky alight
#     the Snowshed      down a timber avalanche gallery cut into the cliff, the frozen lake
#                       below (the one view of another world: down the hill)
#   the Lake (E)      the frozen lake, the Ice Bells' hut on its shore, the Frozen Pass out
#                     east to Desert World (after Rimefang falls)
#     the Frozen Falls  up a tunnel behind a frozen waterfall, back into the village
#
# Blender coordinates (x east, y north, z up).

import math

from pocket_kit import Layout, catmull, lerp, smooth  # noqa: F401

TOP = 78.0
HUB = (0.0, -151.3, 20.8, 20.0)  # x, y, radius, height: the hollow you arrive in (the Burnt Gorge's top)
# Hearthglow, moved (Blake, Oct 29, review-snow_region notes 1, 2: "I want to officially
# move hearthglow hollow to where I drop pin number 2 ... this is now the new section for
# hearth glow hollow"): in the lake's east basin, its square here (x, y, radius, height).
# The hollow it left is the grand way in to the kingdom (snow_dress.entry_pass).
VILLAGE = (130.0, -29.0, 15.0, 12.0)
LAKE = (71.3, -54.6, 32.2, 12.0)  # the frozen lake's ice: x, y, radius, height

POCKETS = [
    ("hearth", "hearth", [(0.0, -148.8, 42.9, 20.0), (24.8, -124.0, 22.2, 20.0), (-27.9, -127.1, 23.7, 20.0)]),
    # (the Burnt Gorge, south, down to the valley's passage)
    ("gorge", "hearth", [(2.5, -204.6, 14.8, 18.0), (-3.7, -232.5, 14.1, 16.0), (3.7, -260.4, 14.1, 14.0),
                         (0.0, -286.4, 16.3, 12.0)]),
    ("frostveil", "frostveil",
     [(-145.7, -74.4, 45.9, 26.0), (-179.8, -31.0, 38.5, 28.0), (-117.8, -117.8, 26.6, 25.0),
      (-186.0, 18.6, 29.6, 32.0)]),
    ("climb", "summit",
     [(-184.8, 42.2, 16.3, 35.0), (-189.1, 58.9, 18.5, 38.0), (-173.6, 81.8, 17.0, 44.0), (-186.0, 106.6, 17.8, 50.0),
      (-162.4, 129.0, 18.5, 54.0)]),
    ("summit", "summit",
     [(-93.0, 142.6, 53.3, 58.0), (-37.2, 167.4, 38.5, 58.0), (-139.5, 158.1, 33.3, 56.0),
      (-55.8, 117.8, 29.6, 57.0)]),
    ("aurora", "aurora",
     [(117.8, 105.4, 51.8, 44.0), (161.2, 62.0, 37.0, 42.0), (83.7, 151.9, 31.1, 48.0),
      (172.4, 18.6, 25.2, 40.0)]),
    ("snowshed", "aurora",
     [(187.2, -13.6, 18.5, 34.0), (189.7, -42.2, 17.8, 27.0), (176.1, -68.2, 17.8, 20.0),
      (155.0, -86.8, 19.2, 15.0)]),
    ("lake", "lake",
     [(71.3, -54.6, 57.7, 12.0), (126.0, -28.5, 38.0, 12.0), (124.0, -79.4, 29.6, 12.0),
      (43.4, -86.8, 26.6, 12.0)]),
]

BASE_ROUTE = [
    (15.5, -127.1, None),  # 0: the start, the village's north side, westbound
    (-18.6, -124.0, None),
    (-44.6, -131.4, 20.3),
    (-59.5, -130.2, 20.6),  # 3: the Gatehouse
    (-85.6, -124.0, 23.4),
    (-109.1, -115.3, None),  # Frostveil's bailey
    (-137.6, -94.2, None),
    (-157.8, -72.2, None),
    (-157.1, -45.7, None),
    (-179.8, -24.8, None),
    (-191.2, 2.3, None),
    (-179.2, 27.8, None),
    (-187.0, 58.3, None),  # 12: the Climb
    (-176.5, 82.0, None),
    (-179.4, 106.2, None),
    (-162.4, 129.0, None),
    (-132.7, 152.5, None),  # 16: the summit meadow
    (-108.5, 152.4, None),
    (-91.8, 132.7, None),
    (-62.5, 118.6, None),
    (-38.4, 141.4, None),
    (-24.8, 171.1, None),
    (-2.5, 174.8, 57.0),  # 22: the Ice Cave
    (26.0, 167.4, 53.0),
    (53.3, 158.1, 49.0),
    (80.6, 148.8, None),  # 25: the glacier
    (109.1, 132.7, None),
    (129.6, 109.8, None),
    (128.8, 82.5, None),
    (149.3, 62.5, None),
    (169.3, 54.3, None),
    (181.0, 31.0, None),
    (176.7, 8.7, None),
    (187.2, -13.6, None),  # 33: the Snowshed, down the cliff
    (189.7, -42.2, None),
    (174.8, -69.4, None),
    (153.8, -88.0, None),
    (126.5, -90.5, None),  # 37: the lake
    (110.4, -62.0, None),
    (99.2, -24.8, None),
    (68.2, -16.1, None),
    (38.4, -40.9, None),
    (38.4, -75.6, None),
    (59.5, -98.0, None),
    (55.8, -116.6, 15.6),  # 44: the Frozen Falls
    (37.2, -131.4, 19.0),
]
BASE_TUNNELS = [("Gatehouse", "gatehouse", 3, 4), ("Ice Cave", "ice", 22, 24), ("Frozen Falls", "icefall", 44, 45)]
_KW = dict(hub=HUB, roll=4.0, flat=("hearth", "lake"), mountains=50.0, tiers=True)
_L0 = Layout(POCKETS, TOP, BASE_ROUTE, BASE_TUNNELS, **_KW)

# ------------------------------------------------------------------ v5: the driving
# (Blake, Oct 29: "improve the driving experience of the snow world ... it is currently
# boring.") The snow lies in drifts and the road rides them: long rolling swells over the
# summit's high meadow, wind-carved ridges (sastrugi) on the glacier; kickers that throw
# you off the end of the Snowshed's run down the cliff and out of the Ice Cave onto the
# glacier; and a crevasse split across the glacier, crossed on a bridge of ice.
DRIFT = {  # look: (height m, crest spacing m)
    "summit": (2.6, 54.0),
    "aurora": (1.9, 30.0),
}
# Kickers: x, y, height, half-width along the road.
LIPS = [(160.0, -82.5, 2.4, 8.0), (64.0, 154.5, 2.0, 7.5), (-150.0, 138.0, 1.8, 7.0)]
# The crevasse across the glacier: its line, depth and half-width at the top.
CREVASSE = [(104.0, 104.0), (118.0, 99.0), (130.0, 96.0), (142.0, 93.0), (156.0, 86.0)]
CREVASSE_DEPTH = 18.0
CREVASSE_HW = 9.0
CALM = [(160.0, -29.0), (-212.0, -38.4), (-155.0, 178.6), (197.2, 64.5), (-105.0, 196.0)]  # gates, lair


def crevasse_d(x, y):
    best = 1e9
    for a, b in zip(CREVASSE, CREVASSE[1:]):
        ax, ay = a
        bx, by = b
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(x - ax - dx * t, y - ay - dy * t))
    return best


def crevasse_cut(x, y):
    d = crevasse_d(x, y)
    if d > CREVASSE_HW + 1.0:
        return 0.0
    (sx, sy), (ex, ey) = CREVASSE[0], CREVASSE[-1]
    ends = min(math.hypot(x - sx, y - sy), math.hypot(x - ex, y - ey))
    hw = CREVASSE_HW * (1.0 + 0.15 * math.sin(x * 0.27 + y * 0.11))
    return CREVASSE_DEPTH * (1.0 - smooth((d - 2.0) / (hw - 2.0))) * smooth(ends / 18.0)


def _floor(x, y):
    return 1.0 - smooth((_L0.wall_sd(x, y) + 12.0) / 10.0)


def drifts(x, y):
    """The drifts' height at (x, y): long swells across the wind (from the north-west),
    steeper on their lee, wandering, by world."""
    if _L0.pocket_at(x, y) not in ("summit", "aurora"):
        return 0.0
    key = _L0.look_at(x, y)
    if key not in DRIFT:
        return 0.0
    amp, gap = DRIFT[key]
    th = -0.7
    u = x * math.cos(th) + y * math.sin(th)
    v = -x * math.sin(th) + y * math.cos(th)
    ph = u / gap * math.tau + 1.3 * math.sin(v / 47.0) + 0.5 * math.sin(v / 15.0 + 2.0)
    w = 0.5 + 0.5 * math.sin(ph + 0.4 * math.sin(ph))
    calm = smooth((crevasse_d(x, y) - 16.0) / 14.0)
    for gx, gy in CALM:
        calm *= smooth((math.hypot(x - gx, y - gy) - 30.0) / 24.0)
    return amp * (w - 0.5) * 2.0 * _floor(x, y) * calm


def lips(x, y):
    h = 0.0
    for lx, ly, lh, lw in LIPS:
        d = math.hypot(x - lx, y - ly)
        h += lh * max(0.0, 1.0 - (d / lw) ** 2) ** 1.5
    return h


def _densify(points, step=12.0, keep=()):
    """Control points every `step` m or so along the closed curve through `points`, but
    the segments in `keep` (by their first point's index) left as they were: the road into
    and through the tunnels keeps its hand-set shape (the bores are cut to fit it)."""
    out = []
    n = len(points)
    for i in range(n):
        p1, p2 = points[i], points[(i + 1) % n]
        if i in keep:
            out.append(p1)
            continue
        per = max(1, int(round(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / step)))
        out.extend(catmull([points[(i + k) % n] for k in (-1, 0, 1, 2)], per)[per:2 * per])
    return out


def _dense_route():
    fixed = [(p[0], p[1]) for p in BASE_ROUTE if p[2] is not None]
    keep = set()
    for _name, _kind, a, b in BASE_TUNNELS:
        keep.update(range(a - 2, b + 2))
    out = []
    for x, y, z in _densify(_L0.route_points(), keep=keep):
        if _L0.tunnel_floor(x, y) is not None or any(math.hypot(x - a, y - b) < 18.0 for a, b in fixed):
            out.append((round(x, 2), round(y, 2), round(z, 2)))
        else:
            out.append((round(x, 2), round(y, 2), round(z + drifts(x, y) + lips(x, y), 2)))
    return out


ROUTE = _dense_route()


def _nearest(p):
    return min(range(len(ROUTE)), key=lambda i: (ROUTE[i][0] - p[0]) ** 2 + (ROUTE[i][1] - p[1]) ** 2)


TUNNELS = [(name, kind, _nearest(BASE_ROUTE[a]), _nearest(BASE_ROUTE[b])) for name, kind, a, b in BASE_TUNNELS]

L = Layout(POCKETS, TOP, ROUTE, TUNNELS, **_KW)
# (The tunnels' corridors as the hand-set route made them: the dense route's shorter
# segments would trim their ends, leaving the land standing over the road at the mouths.)
_L0.tunnel_floor(0.0, 0.0)
L._corridors = _L0._corridors

# The gateways' landmarks (x, y), each at the end of a short spur off the road.
GATES = {
    # (Blake, Oct 29: the portal stood in the middle of the road. Now it's in the hollow's
    # west wall, at the end of a lane straight out of the square: the village's own course
    # entered from the village.)
    # (Oct 29, moved with the village: in its basin's east wall, a lane out of the square.)
    "hearthglow": (160.0, -29.0),
    "frostveil": (-212.0, -38.4),  # the keep's gate in the bailey's west wall
    "summit": (-155.0, 178.6),  # the giant tree
    "aurora": (197.2, 64.5),  # the rift in the glacier
}
TREE = (136.0, -55.0)  # the village's great tree, south of the square
BELL = (146.0, -10.0)  # the bell tower, north-east of the square
LAIR = (-105.0, 196.0)  # Rimefang's lair (the ruin's boss gateway), the summit's north wall
FROZEN_PASS = (152.5, -105.4)  # where the Frozen Pass leaves the lake (the ruin), on east
PASS_END = (260.4, -117.8)
GORGE_END = (0.0, -291.4)  # the Burnt Gorge's far end: the passage back to the valley


def natural(x, y):
    """The land, with the frozen lake's ice laid level in its hollow (and v5's drifts,
    kickers and the crevasse)."""
    h = L.natural(x, y) + drifts(x, y) + lips(x, y) - crevasse_cut(x, y)
    lx, ly, lr, lz = LAKE
    d = math.hypot(x - lx, y - ly)
    if d < lr + 14:
        h = lerp(lz - 0.4, h, smooth((d - lr) / 14.0))
    return h


# (The names the checker and the build read.)
route_points = L.route_points
wall_sd = L.wall_sd
pocket_at = L.pocket_at
lobe_weights = L.look_weights
look_at = L.look_at
tunnel_floor = L.tunnel_floor
RIVERS = []
LAKES = []
POOLS = []
LAVA = []
RIVER_HW = 9.0


def river_d(x, y):
    return 1e9, 0.0
