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

TOP = 90.0
# v4 (Blake, Oct 30: "massively overhaul ... to the level of Dino valley in terms of
# immersion ... every section brings you to the world created in that level", and "if we
# would see the whole kingdom from the entrance that would be incredible"): Dino Valley's
# size, Layout A. Up the Burnt Gorge to the Arrival Pass, the highest road in the kingdom,
# every world's landmark in view; down the switchbacks into Hearthglow's winding lanes;
# through the Gatehouse into Frostveil's citadel, bailey and courtyard; up the Climb to the
# Summit (geysers, the frozen lake, pines, mammoths); through the Ice Cave onto the
# glacier and into the ice (the long gallery, the crystal cavern); out through a crevasse
# and back up the glacier's tongue to the pass.
HUB = (18.0, -160.0, 16.0, 58.0)  # x, y, radius, height: the Arrival Pass's crest
VILLAGE = (-96.0, -140.0, 14.0, 44.0)  # Hearthglow's little square (x, y, radius, height)
LAKE = (-30.0, 148.0, 20.0, 70.6)  # the frozen lake in the summit: x, y, radius, ice height

POCKETS = [
    ("pass", "pass", [(18.0, -160.0, 22.0, 58.0), (48.0, -148.0, 18.0, 58.0), (-8.0, -168.0, 16.0, 57.0)]),
    ("descent", "hearth", [(-30.0, -176.0, 16.0, 54.0), (-56.0, -170.0, 16.0, 49.0)]),
    ("hearth", "hearth",
     [(-86.0, -132.0, 40.0, 44.0), (-120.0, -102.0, 28.0, 45.0), (-62.0, -98.0, 24.0, 44.0), (-118.0, -158.0, 26.0, 44.0),
      (-80.0, -172.0, 20.0, 44.0), (-92.0, -84.0, 16.0, 45.0)]),
    ("frostveil", "frostveil",
     [(-164.0, -46.0, 40.0, 48.0), (-178.0, 4.0, 32.0, 51.0), (-150.0, 32.0, 24.0, 53.0), (-140.0, -82.0, 22.0, 48.0)]),
    ("climb", "summit", [(-170.0, 62.0, 16.0, 57.0), (-160.0, 88.0, 17.0, 62.0), (-136.0, 112.0, 17.0, 67.0),
                         (-124.0, 126.0, 14.0, 69.0)]),
    ("summit", "summit",
     [(-84.0, 152.0, 48.0, 72.0), (-24.0, 166.0, 36.0, 72.0), (-122.0, 170.0, 28.0, 73.0), (-50.0, 116.0, 28.0, 71.0),
      (14.0, 140.0, 24.0, 71.0), (-90.0, 196.0, 20.0, 73.0), (24.0, 166.0, 16.0, 72.0),
      (-14.0, 124.0, 16.0, 71.0)]),
    ("glacier", "aurora", [(76.0, 156.0, 26.0, 72.0), (116.0, 140.0, 32.0, 70.0), (92.0, 118.0, 20.0, 70.0),
                           (140.0, 122.0, 16.0, 70.0)]),
    ("cavern", "aurora", [(176.0, 58.0, 32.0, 62.0), (196.0, 82.0, 16.0, 62.0)]),
    ("crevasse", "aurora", [(178.0, 8.0, 18.0, 58.0), (170.0, -28.0, 18.0, 58.0), (168.0, -50.0, 16.0, 58.0)]),
    ("tongue", "pass", [(150.0, -66.0, 22.0, 58.0), (112.0, -104.0, 22.0, 58.0), (80.0, -130.0, 20.0, 58.0)]),
]

WAYPOINTS = [
    (18.0, -150.0, None),  # 0: the start, on the pass's crest, westbound
    (-8.0, -160.0, None),
    (-32.0, -176.0, None),  # 2: over the edge, down the switchbacks
    (-58.0, -172.0, None),
    (-80.0, -156.0, None),  # 4: Hearthglow's lanes
    (-104.0, -168.0, None),
    (-128.0, -146.0, None),
    (-108.0, -122.0, None),
    (-80.0, -128.0, None),
    (-62.0, -104.0, None),
    (-82.0, -84.0, None),
    (-110.0, -101.0, None),
    (-126.0, -92.0, 45.5),  # 12: the Gatehouse
    (-144.0, -82.0, 47.5),
    (-160.0, -66.0, None),  # 15: Frostveil's bailey
    (-182.0, -42.0, None),
    (-164.0, -16.0, None),
    (-184.0, 10.0, None),  # 18: up into the courtyard
    (-170.0, 34.0, None),
    (-150.0, 48.0, None),
    (-162.0, 70.0, None),  # 21: the Climb
    (-160.0, 88.0, None),
    (-142.0, 106.0, None),
    (-128.0, 122.0, None),
    (-104.0, 150.0, None),  # 25: the summit
    (-120.0, 176.0, None),
    (-96.0, 200.0, None),
    (-70.0, 182.0, None),
    (-52.0, 166.0, None),  # 29: round the frozen lake
    (-66.0, 138.0, None),
    (-48.0, 110.0, None),
    (-18.0, 124.0, None),
    (8.0, 138.0, None),
    (22.0, 170.0, None),
    (44.0, 164.0, 72.0),  # 34: the Ice Cave
    (60.0, 158.0, 72.0),
    (80.0, 150.0, None),  # 37: the glacier, under the sky
    (104.0, 140.0, None),
    (128.0, 146.0, None),
    (142.0, 126.0, None),
    (142.0, 104.0, 69.0),  # 40: into the ice (the Ice Gallery)
    (150.0, 84.0, 64.0),
    (164.0, 68.0, None),  # 42: the crystal cavern
    (188.0, 62.0, None),
    (194.0, 44.0, None),
    (182.0, 28.0, 61.0),  # 45: out through the ice
    (178.0, 14.0, 59.0),
    (176.0, -6.0, None),  # 48: the crevasse
    (160.0, -30.0, None),
    (164.0, -58.0, None),  # 50: up the glacier's tongue
    (140.0, -76.0, None),
    (114.0, -90.0, None),
    (96.0, -114.0, None),
    (70.0, -128.0, None),
    (44.0, -146.0, None),
]
WAY_TUNNELS = [("Gatehouse", "gatehouse", 12, 13), ("Ice Cave", "ice", 34, 35), ("Ice Gallery", "ice", 40, 41),
               ("Ice Gallery Out", "ice", 45, 46)]


def _fillet(points, tunnels, rmax=22.0, every=7.0):
    """v4: the waypoints' corners rounded into arcs (as big as `rmax`, as the segments either
    side allow), sampled every `every` m: Dino Valley's bends are 12 m at least, and a lane's
    corner any tighter folds the road over itself on its inside. The tunnels' ends (their
    heights set) stay sharp points, the bores straight between them. Returns the points
    (x, y, z or None) and the tunnels re-indexed into them."""
    n = len(points)
    sharp = set()
    for _name, _kind, a, b in tunnels:
        sharp.update((a, b))
    out = []
    index = {}
    for i in range(n):
        a, b, c = points[i - 1], points[i], points[(i + 1) % n]
        if i in sharp:
            index[i] = len(out)
            out.append(b)
            continue
        ux, uy = b[0] - a[0], b[1] - a[1]
        vx, vy = c[0] - b[0], c[1] - b[1]
        lu, lv = math.hypot(ux, uy), math.hypot(vx, vy)
        ux, uy, vx, vy = ux / lu, uy / lu, vx / lv, vy / lv
        th = math.acos(max(-1.0, min(1.0, ux * vx + uy * vy)))  # (the turn)
        if th < 0.05:
            index[i] = len(out)
            out.append(b)
            continue
        t = min(rmax * math.tan(th / 2), 0.48 * min(lu, lv))
        r = t / math.tan(th / 2)
        p0 = (b[0] - ux * t, b[1] - uy * t)
        side = 1.0 if ux * vy - uy * vx > 0 else -1.0
        cx, cy = p0[0] - uy * r * side, p0[1] + ux * r * side
        a0 = math.atan2(p0[1] - cy, p0[0] - cx)
        k = max(2, int(r * th / every))
        index[i] = len(out) + k // 2
        for j in range(k + 1):
            ang = a0 + side * th * j / k
            out.append((cx + r * math.cos(ang), cy + r * math.sin(ang), None))
        # (and along the straight to the next corner)
        q1 = (b[0] + vx * t, b[1] + vy * t)
        nxt = points[(i + 1) % n]
        tn = 0.0 if (i + 1) % n in sharp else None
        end = (nxt[0] - vx * (tn if tn is not None else min(0.48 * lv, 0.48 * lv)), nxt[1] - vy * (tn if tn is not None else 0.48 * lv))
        seg = math.hypot(end[0] - q1[0], end[1] - q1[1])
        for j in range(1, int(seg / every)):
            f = j / int(seg / every)
            out.append((q1[0] + (end[0] - q1[0]) * f, q1[1] + (end[1] - q1[1]) * f, None))
    return out, [(nm, kd, index[a], index[b]) for nm, kd, a, b in tunnels]


BASE_ROUTE, BASE_TUNNELS = _fillet(WAYPOINTS, WAY_TUNNELS)
_KW = dict(hub=HUB, roll=4.0, flat=("hearth",), mountains=50.0, tiers=True)
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
LIPS = [(146.0, -70.0, 2.2, 8.0), (66.0, 154.0, 2.0, 7.5), (-112.0, 164.0, 1.8, 7.0)]
# The crevasse across the glacier: its line, depth and half-width at the top.
CREVASSE = [(100.0, 156.0), (106.0, 142.0), (110.0, 128.0), (112.0, 114.0), (110.0, 102.0)]
CREVASSE_DEPTH = 18.0
CREVASSE_HW = 9.0
CALM = [(-150.0, -162.0), (-216.0, 4.0), (-156.0, 180.0), (122.0, 178.0), (-90.0, 222.0)]  # gates, lair


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


def _radius(a, b, c):
    """The radius of the circle through three points (xy)."""
    ab, bc, ca = math.dist(a[:2], b[:2]), math.dist(b[:2], c[:2]), math.dist(c[:2], a[:2])
    cr = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
    return 1e9 if cr < 1e-9 else ab * bc * ca / (2.0 * cr)


def _ease(points, fixed, rmin=16.0, rounds=400):
    """v4: the bends eased to `rmin` at least (as Dino Valley's, 12 m): a lane's corner any
    tighter folds the road over itself on its inside. Each point on too tight a bend moves
    a little toward its neighbours' middle, round after round; the tunnels' and the fixed
    points stay as they are."""
    pts = [list(p) for p in points]
    n = len(pts)
    still = [_L0.tunnel_floor(p[0], p[1]) is not None or any(math.hypot(p[0] - a, p[1] - b) < 10.0 for a, b in fixed)
             for p in pts]
    for _ in range(rounds):
        moved = False
        for i in range(n):
            if still[i]:
                continue
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
            a2, c2 = pts[i - 2], pts[(i + 2) % n]
            if min(_radius(a, b, c), _radius(a2, b, c2)) >= rmin:
                continue
            mx, my = (a[0] + c[0]) / 2, (a[1] + c[1]) / 2
            b[0] += 0.3 * (mx - b[0])
            b[1] += 0.3 * (my - b[1])
            moved = True
        if not moved:
            break
    return [tuple(p) for p in pts]


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
    # (Blake, Oct 29: the portal stood in the middle of the road. v4: in the hollow's
    # west wall, at the end of a lane out of the square: the village's own course entered
    # from the village.)
    "hearthglow": (-150.0, -162.0),
    "frostveil": (-216.0, 4.0),  # the keep's gate in the courtyard's west wall
    "summit": (-156.0, 180.0),  # the giant tree, the summit's west end
    "aurora": (122.0, 178.0),  # the rift in the glacier's north wall
}
TREE = (-84.0, -158.0)  # the village's great tree, south of the square
BELL = (-110.0, -122.0)  # the bell tower, north-west of the square
LAIR = (-90.0, 222.0)  # Rimefang's lair (the ruin's boss gateway), the summit's north wall
FROZEN_PASS = (164.0, -62.0)  # where the Frozen Pass leaves the glacier's tongue (the ruin), on east
PASS_END = (262.0, -90.0)
GORGE_END = (0.0, -314.0)  # the Burnt Gorge's far end: the passage back to the valley

# The Lookout Road (Blake, Oct 30: "what if we had to drive a bit before we get to the
# actual lap, that way it isnt so steep ... so we can see everything with switchbacks"):
# up out of the Burnt Gorge onto the Lookout, the high shoulder of the mountain south of
# the pass, 100 m up, over every world's walls, the whole kingdom laid out below; then down
# its north face in three legs and two hairpins into the pass, onto the lap. (x, y, road
# height) at its turns; between them it runs straight, the corners rounded.
LOOKOUT_WAY = [
    (0.0, -314.0, 88.0),  # the passage (back down the gorge to the valley)
    (10.0, -286.0, 90.6),
    (36.0, -266.0, 93.6),
    (62.0, -254.0, 96.1),
    (80.0, -238.0, 98.2),
    (66.0, -224.0, 100.0),  # 5: the Lookout
    (30.0, -228.0, 95.0),
    (-10.0, -230.0, 89.4),
    (-34.0, -224.0, 86.0),  # the first hairpin
    (-40.0, -210.0, 83.9),
    (-26.0, -202.0, 81.6),
    (10.0, -206.0, 76.6),
    (46.0, -208.0, 71.6),
    (70.0, -200.0, 68.1),  # the second hairpin
    (74.0, -186.0, 66.1),
    (60.0, -176.0, 63.7),
    (40.0, -170.0, 60.8),
    (26.0, -160.0, 58.4),  # onto the lap, on the pass
]
LOOKOUT = (66.0, -224.0)
LOOKOUT_PEAK = (20.0, -222.0, 104.0, 58.0)  # x, y, top, flat radius: the shoulder it's cut into


def lookout_line(every=3.0, r=11.0):
    """The Lookout Road's centre line, dense: (x, y, z), its corners rounded (radius `r`)."""
    pts = LOOKOUT_WAY
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        ux, uy = b[0] - a[0], b[1] - a[1]
        vx, vy = c[0] - b[0], c[1] - b[1]
        lu, lv = math.hypot(ux, uy), math.hypot(vx, vy)
        ux, uy, vx, vy = ux / lu, uy / lu, vx / lv, vy / lv
        th = math.acos(max(-1.0, min(1.0, ux * vx + uy * vy)))
        if th < 0.05:
            out.append(b)
            continue
        t = min(r * math.tan(th / 2), 0.48 * min(lu, lv))
        rr = t / math.tan(th / 2)
        p0 = (b[0] - ux * t, b[1] - uy * t)
        side = 1.0 if ux * vy - uy * vx > 0 else -1.0
        cx, cy = p0[0] - uy * rr * side, p0[1] + ux * rr * side
        a0 = math.atan2(p0[1] - cy, p0[0] - cx)
        k = max(2, int(rr * th / 2.0))
        za = lerp(a[2], b[2], 1.0 - t / lu)
        zc = lerp(b[2], c[2], t / lv)
        for j in range(k + 1):
            ang = a0 + side * th * j / k
            out.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang), lerp(za, zc, j / k)))
    out.append(pts[-1])
    dense = [out[0]]
    for a, b in zip(out, out[1:]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / every))
        for j in range(1, n + 1):
            dense.append((lerp(a[0], b[0], j / n), lerp(a[1], b[1], j / n), lerp(a[2], b[2], j / n)))
    return dense


LOOKOUT_LINE = lookout_line()
_LK_BOX = (min(p[0] for p in LOOKOUT_LINE) - 30, max(p[0] for p in LOOKOUT_LINE) + 30,
           min(p[1] for p in LOOKOUT_LINE) - 30, max(p[1] for p in LOOKOUT_LINE) + 30)


def lookout_floor(x, y):
    """(distance from the Lookout Road's line, its road height there) or None far off."""
    x0, x1, y0, y1 = _LK_BOX
    if not (x0 <= x <= x1 and y0 <= y <= y1):
        return None
    best = None
    for a, b in zip(LOOKOUT_LINE, LOOKOUT_LINE[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy or 1e-9
        t = max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / L2))
        d = math.hypot(x - a[0] - dx * t, y - a[1] - dy * t)
        if best is None or d < best[0]:
            best = (d, lerp(a[2], b[2], t))
    return best


def lookout_land(h, x, y, wsd):
    """The mountain the Lookout Road is cut into: its shoulder built up (never in a pocket),
    then the road's shelf cut level across, 7 m each side, banked back into the slope; a leg
    below another sits on its own shelf, the slope between them a cut face."""
    px, py, top, flat = LOOKOUT_PEAK
    d = math.hypot(x - px, y - py)
    peak = top - max(0.0, d - flat) * 0.55
    if peak > h:
        h = lerp(h, peak, smooth((wsd - 2.0) / 16.0))
    f = lookout_floor(x, y)
    if f is None:
        return h
    dd, z = f
    if dd < 7.0:
        return z - 0.25
    if dd < 16.0 and h > z - 0.25:
        return lerp(z - 0.25, h, smooth((dd - 7.0) / 9.0))
    return h


def natural(x, y):
    """The land, with the frozen lake's ice laid level in its hollow (and v5's drifts,
    kickers and the crevasse)."""
    h = L.natural(x, y) + drifts(x, y) + lips(x, y) - crevasse_cut(x, y)
    h = lookout_land(h, x, y, L.wall_sd(x, y))
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
