# Desert World's layout (v3, on pocket_kit): pure geometry, no Blender (desert_region.py
# builds it).
# SPDX-License-Identifier: MIT
#
# Built like the valley's and the Snow Kingdom's (Blake, Oct 26): a pocket for each of the
# kingdom's worlds walled off by red rock, the main road one loop through them (Stego's
# 1-on-1), a threshold between each:
#
#   the Trading Post (hub, W)  Stego's post round its square; the Frozen Pass comes down
#                              into it out of the snow, west
#     the Slot           a narrow winding slot canyon north, light falling into it
#   Canyon (N)        banded red cliffs, hoodoos, arches (Scorchwind's lair in its west
#                     wall, after his attack)
#     the Arch           a tunnel through a sandstone fin, east
#   the Oasis (NE)    palms round a spring-fed pool, adobe walls, green
#     the Mine           a timber-shored mine tunnel south under the ridge
#   the Gulch (SE)    the ghost town: false fronts, a water tower, tumbleweeds
#     the Rim            up over the meteor crater's rim and down inside it (the one view
#                        of another world: down into the crater)
#   the Crater (S)    the impact's bowl, glowing shards in its floor (the Dust Road out
#                     south to Tropic Isles, after Scorchwind falls)
#     the Wash           a dry riverbed's S-bends back west to the post
#
# Blender coordinates (x east, y north, z up).

import math

from pocket_kit import Layout, catmull, lerp, smooth  # noqa: F401

TOP = 64.0
HUB = (-162.4, 0.0, 19.2, 10.0)  # x, y, radius, height: the post's square
POST = HUB
POOL = (155.0, 141.4, 11.2, 5.0)  # the oasis pool: x, y, radius, water height
CRATER = (-6.2, -133.3)  # the crater's middle

POCKETS = [
    ("post", "post", [(-161.2, 0.0, 40.7, 10.0), (-137.6, 26.0, 23.7, 10.0), (-139.5, -26.0, 23.7, 10.0)]),
    # (the Frozen Pass, west, up to the snow)
    ("pass", "post", [(-204.6, 2.5, 16.3, 12.0), (-232.5, -2.5, 15.5, 14.0), (-260.4, 2.5, 15.5, 16.0),
                      (-286.4, 0.0, 17.8, 18.0)]),
    ("slot", "canyon", [(-132.7, 43.4, 13.3, 11.0), (-127.7, 57.0, 14.1, 12.0), (-112.8, 77.5, 13.3, 13.0),
                        (-121.5, 89.9, 12.6, 14.0), (-124.0, 99.2, 14.1, 15.0), (-114.7, 110.4, 12.6, 15.5),
                        (-105.4, 119.0, 14.8, 16.0), (-94.2, 131.4, 14.8, 16.5)]),
    ("canyon", "canyon", [(-55.8, 148.8, 51.8, 18.0), (-6.2, 173.6, 38.5, 19.0), (-93.0, 158.1, 28.1, 17.0)]),
    ("oasis", "oasis", [(105.4, 161.2, 29.6, 6.0), (142.6, 124.0, 51.8, 6.0), (179.8, 80.6, 33.3, 7.0)]),
    ("gulch", "gulch", [(176.7, -37.2, 29.6, 13.0), (142.6, -93.0, 51.8, 14.0), (93.0, -142.6, 31.1, 14.0),
                        (122.8, -132.7, 20.7, 14.0)]),
    ("rim", "crater", [(62.0, -162.4, 14.8, 16.0), (38.4, -162.4, 14.8, 13.5), (18.6, -164.9, 16.3, 10.5)]),
    ("crater", "crater", [(-6.2, -133.3, 47.4, 6.0), (-43.4, -105.4, 26.6, 7.0), (24.8, -111.6, 26.6, 7.0)]),
    ("wash", "post", [(-65.1, -93.0, 16.3, 7.5), (-80.6, -69.4, 14.8, 8.0), (-106.6, -73.2, 14.8, 8.5),
                      (-120.9, -50.8, 16.3, 9.5), (-133.3, -38.4, 17.8, 10.0)]),
]

BASE_ROUTE = [
    (-145.7, -6.2, None),  # 0: the start, the post's east side, northbound
    (-141.4, 21.7, None),
    (-127.7, 55.8, None),  # 2: the Slot
    (-116.3, 77.5, None),
    (-118.6, 98.8, None),
    (-104.2, 119.0, None),
    (-80.6, 147.6, None),  # 6: the canyon
    (-53.6, 153.0, None),
    (-33.5, 142.3, None),
    (-6.2, 148.8, None),
    (12.2, 172.1, None),
    (29.8, 174.8, 18.6),  # 11: the Arch
    (62.0, 166.2, 12.0),
    (93.0, 158.1, None),  # 13: the oasis
    (119.0, 148.8, None),
    (132.3, 123.0, None),
    (156.2, 114.1, None),
    (168.6, 91.8, None),
    (186.0, 68.2, None),
    (183.5, 43.4, 8.6),  # 19: the Mine
    (179.8, 13.6, 10.4),
    (176.7, -14.9, 12.2),
    (170.5, -43.4, None),  # 21: the ghost town's street
    (148.8, -74.4, None),
    (131.7, -94.8, None),
    (134.2, -121.2, None),
    (111.4, -146.6, None),
    (86.8, -147.7, None),
    (62.0, -162.4, None),  # 27: over the rim
    (38.4, -162.4, None),
    (17.4, -162.4, None),
    (6.1, -149.7, None),  # 30: the crater
    (4.5, -129.5, None),
    (-12.4, -111.6, None),
    (-43.4, -105.4, None),
    (-65.1, -93.0, None),  # 34: the Wash
    (-82.0, -73.1, None),
    (-105.1, -70.0, None),
    (-120.9, -50.8, None),
    (-133.3, -38.4, None),
    (-145.7, -24.8, None),
]
BASE_TUNNELS = [("The Arch", "arch", 11, 12), ("The Mine", "mine", 19, 21)]
_KW = dict(hub=HUB, lakes=[POOL], roll=4.0, flat=("post",), mountains=40.0, water_floor=1.2, tiers=True)
_L0 = Layout(POCKETS, TOP, BASE_ROUTE, BASE_TUNNELS, **_KW)

# ------------------------------------------------------------------ v5: the driving
# (Blake, Oct 29: "much more exciting ... driving and visuals needs to be better. feel free
# to reshape.") The land rolls in dunes, and the road rides them: in the open canyon long
# rolling swells you crest at speed; round the post's outskirts and in the crater's floor
# gentler ones; down the Wash the dry riverbed's ripples, short whoops; and over the
# crater's rim a lip that throws you off it and down into the bowl.
DUNE = {  # look/pocket: (height m, crest spacing m)
    "canyon": (2.9, 54.0),
    "post": (2.2, 38.0),
    "crater": (1.6, 34.0),
    "wash": (1.1, 19.0),
}
RIM_LIP = (44.0, -162.4, 2.6, 9.0)  # x, y, height, half-width (along the road)
# The Gorge Bridge: a dry ravine cracked across the canyon's floor, the road over it on a
# timber trestle (its line, its depth, its half-width at the top).
RAVINE = [(-10.0, 108.0), (-14.0, 124.0), (-19.0, 140.0), (-21.0, 152.0), (-23.0, 166.0)]
RAVINE_DEPTH = 14.0
RAVINE_HW = 11.0


def ravine_d(x, y):
    """How far (x, y) is from the ravine's line (and 1e9 past its ends)."""
    best = 1e9
    for a, b in zip(RAVINE, RAVINE[1:]):
        ax, ay = a
        bx, by = b
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(x - ax - dx * t, y - ay - dy * t))
    return best


def ravine_cut(x, y):
    """How deep the ravine cuts at (x, y): a flat dry bed, steep walls, wandering a
    little, shallowing out at its two ends."""
    d = ravine_d(x, y)
    if d > RAVINE_HW + 1.0:
        return 0.0
    (sx, sy), (ex, ey) = RAVINE[0], RAVINE[-1]
    ends = min(math.hypot(x - sx, y - sy), math.hypot(x - ex, y - ey))
    hw = RAVINE_HW * (1.0 + 0.12 * math.sin(x * 0.21 + y * 0.13))
    return RAVINE_DEPTH * (1.0 - smooth((d - 4.0) / (hw - 4.0))) * smooth(ends / 22.0)


def _floor(x, y):  # noqa: E302
    """1 out on a pocket's floor, 0 up its walls (the dunes stay on the floors)."""
    return 1.0 - smooth((_L0.wall_sd(x, y) + 12.0) / 10.0)


def dunes(x, y):
    """The dunes' height at (x, y): crests running across the wind (from the west-south-
    west), each a long swell steeper on its lee side, wandering, by world."""
    pk = _L0.pocket_at(x, y)
    if pk in ("slot", "rim", "pass"):
        return 0.0
    key = pk if pk == "wash" else _L0.look_at(x, y)
    if key not in DUNE:
        return 0.0
    amp, gap = DUNE[key]
    hx, hy = HUB[0], HUB[1]
    near = math.hypot(x - hx, y - hy)
    keep = smooth((near - HUB[2] - 14.0) / 16.0)  # (none in the post's square)
    if keep <= 0.0:
        return 0.0
    th = 0.35
    u = x * math.cos(th) + y * math.sin(th)
    v = -x * math.sin(th) + y * math.cos(th)
    ph = u / gap * math.tau + 1.4 * math.sin(v / 53.0) + 0.6 * math.sin(v / 17.0 + 1.0)
    w = 0.5 + 0.5 * math.sin(ph + 0.35 * math.sin(ph))  # (asymmetric: a long back, a steeper face)
    near_ravine = smooth((ravine_d(x, y) - 18.0) / 16.0)
    # (Calm by the gateways and the lair: their ways in are cut level with the road.)
    for gx, gy in _CALM:
        near_ravine *= smooth((math.hypot(x - gx, y - gy) - 34.0) / 26.0)
    return amp * (w - 0.5) * 2.0 * keep * _floor(x, y) * near_ravine


def _lip(x, y):
    lx, ly, lh, lw = RIM_LIP
    d = math.hypot(x - lx, y - ly)
    return lh * max(0.0, 1.0 - (d / lw) ** 2) ** 1.5


def _densify(points, step=12.0):
    """The control points every `step` m or so along the closed curve through them."""
    out = []
    n = len(points)
    for i in range(n):
        p1, p2 = points[i], points[(i + 1) % n]
        seg = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        per = max(1, int(round(seg / step)))
        out.extend(catmull([points[(i + k) % n] for k in (-1, 0, 1, 2)], per)[per:2 * per])
    return out


def _dense_route():
    base = _L0.route_points()
    pts = _densify(base)
    bx = [(p[0], p[1]) for p in BASE_ROUTE]
    fixed = {i for i, p in enumerate(BASE_ROUTE) if p[2] is not None}
    # (Where a tunnel or a hand-set height is, the road keeps the base heights.)
    near_fixed = []
    for i in fixed:
        near_fixed.append(bx[i])
    out = []
    for x, y, z in pts:
        if _L0.tunnel_floor(x, y) is not None or any(math.hypot(x - a, y - b) < 20.0 for a, b in near_fixed):
            out.append((round(x, 2), round(y, 2), round(z, 2)))
        else:
            out.append((round(x, 2), round(y, 2), round(z + dunes(x, y) + _lip(x, y), 2)))
    return out


_CALM = [(-37.2, 199.6), (193.4, 106.6), (147.6, -141.4), (-24.8, -151.3), (-117.8, 167.4)]  # (GATES and LAIR)
ROUTE = _dense_route()


def _nearest(p):
    return min(range(len(ROUTE)), key=lambda i: (ROUTE[i][0] - p[0]) ** 2 + (ROUTE[i][1] - p[1]) ** 2)


TUNNELS = [(name, kind, _nearest(BASE_ROUTE[a]), _nearest(BASE_ROUTE[b])) for name, kind, a, b in BASE_TUNNELS]

L = Layout(POCKETS, TOP, ROUTE, TUNNELS, **_KW)

GATES = {
    "canyon": (-37.2, 199.6),  # the slot canyon's mouth in the north wall
    "oasis": (193.4, 106.6),  # the palm grove by the spring
    "gulch": (147.6, -141.4),  # the end of the false-front street
    "impact": (-24.8, -151.3),  # the shards in the crater's floor
}
LAIR = (-117.8, 167.4)  # Scorchwind's lair (the ruin's boss gateway): a rock arch in the canyon's west wall
DUST_ROAD = (0.0, -173.6)  # where the Dust Road leaves the crater (the ruin), on south
DUST_END = (0.0, -285.2)
PASS_END = (-291.4, 0.0)  # the Frozen Pass's far end: the passage back to the snow


def natural(x, y):
    h = L.natural(x, y) + dunes(x, y) + _lip(x, y) - ravine_cut(x, y)
    # The crater's bowl: its floor dips to the middle.
    cx, cy = CRATER
    d = math.hypot(x - cx, y - cy)
    if d < 37:
        h -= 3.0 * (1.0 - smooth(d / 37.0))
    return h


route_points = L.route_points
wall_sd = L.wall_sd
pocket_at = L.pocket_at
lobe_weights = L.look_weights
look_at = L.look_at
tunnel_floor = L.tunnel_floor
RIVERS = []
LAKES = [POOL]
POOLS = []
LAVA = []
RIVER_HW = 9.0


def river_d(x, y):
    return L.water_d(x, y)
