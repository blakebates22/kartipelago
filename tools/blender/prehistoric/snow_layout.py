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
LAKE = (-24.0, 155.0, 23.0, 69.2)  # the frozen lake in the summit: x, y, radius, ice height (v4: larger, note 21;
# sunk below all its shore, so its ice never shows past it)

POCKETS = [
    ("pass", "pass", [(18.0, -160.0, 22.0, 58.0), (48.0, -148.0, 18.0, 58.0), (-8.0, -168.0, 16.0, 57.0)]),
    ("descent", "hearth", [(-30.0, -176.0, 16.0, 54.0), (-56.0, -170.0, 16.0, 49.0)]),
    # (Oct 30: bigger, south and west: "hearthglow feels the smallest")
    ("hearth", "hearth",
     [(-88.0, -136.0, 46.0, 44.0), (-124.0, -104.0, 30.0, 45.0), (-62.0, -98.0, 26.0, 44.0), (-126.0, -166.0, 30.0, 44.0),
      (-86.0, -184.0, 24.0, 44.0), (-92.0, -84.0, 16.0, 45.0), (-150.0, -136.0, 18.0, 45.0)]),
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
    pts = _densify(_L0.route_points(), keep=keep)
    held = [_L0.tunnel_floor(x, y) is not None or any(math.hypot(x - a, y - b) < 18.0 for a, b in fixed) for x, y, _ in pts]
    # (The drifts and kickers ease in and out over 24 m from where the road's held to its
    # set height (tunnels, gates): they stepped on and off it before, too steep to drive:
    # Blake, review-snow_region 2 notes 5, 6 and 8.)
    n = len(pts)
    cum = [0.0]
    for p, q in zip(pts, pts[1:] + pts[:1]):
        cum.append(cum[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
    total = cum[-1]
    hi = [i for i in range(n) if held[i]]
    out = []
    for i, (x, y, z) in enumerate(pts):
        if held[i] or not hi:
            w = 0.0 if hi else 1.0
        else:
            d = min(min(abs(cum[i] - cum[j]), total - abs(cum[i] - cum[j])) for j in hi)
            w = smooth(d / 24.0)
        out.append((x, y, z + w * (drifts(x, y) + lips(x, y))))
    # (And the road's height smoothed along it, 20 m either way: the set heights stepped
    # up and down at the bends between them, a metre or two in as many metres.)
    zs = []
    for i in range(n):
        acc = wt = 0.0
        for j in range(i - 16, i + 17):
            jj = j % n
            d = cum[i] - cum[jj] if abs(cum[i] - cum[jj]) < total / 2 else (total - abs(cum[i] - cum[jj]))
            g = math.exp(-0.5 * (d / 20.0) ** 2)
            acc += g * out[jj][2]
            wt += g
        zs.append(acc / wt)
    # (Out of Frostveil's courtyard up the Climb, eased out longer, 45 m either way: it rose
    # a quarter in places, and a kart out of the keep's gate crawled up it. The 4 snow test
    # failures, Blake, Oct 31.)
    cx, cy, cr = CLIMB_EASE
    eased = list(zs)
    for i in range(n):
        w = smooth((cr - math.hypot(out[i][0] - cx, out[i][1] - cy)) / 25.0)
        if w <= 0.0:
            continue
        acc = wt = 0.0
        for j in range(i - 40, i + 41):
            jj = j % n
            d = cum[i] - cum[jj] if abs(cum[i] - cum[jj]) < total / 2 else (total - abs(cum[i] - cum[jj]))
            g = math.exp(-0.5 * (d / 45.0) ** 2)
            acc += g * zs[jj]
            wt += g
        eased[i] = lerp(zs[i], acc / wt, w)
    return [(round(x, 2), round(y, 2), round(z, 2)) for (x, y, _), z in zip(out, eased)]


CLIMB_EASE = (-160.0, 40.0, 110.0)  # (x, y, radius): the Climb out of Frostveil's courtyard


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
TREE = (-90.0, -192.0)
FROST_COVE = (-204.0, -42.0, 13.0, 47.2)  # Frostveil's cove carved west of the courtyard: x, y, radius, floor
# (Blake, Oct 30: "we can remove some of the cliff behind the big christmas tree to make
# more room for a larger tree": its court cut back into the basin's south wall.)
TREE_COURT = (-90.0, -196.0, 19.0, 44.8)  # the village's great tree, south of the square
BELL = (-110.0, -122.0)  # the bell tower, north-west of the square
LAIR = (-90.0, 222.0)  # Rimefang's lair (the ruin's boss gateway), the summit's north wall
FROZEN_PASS = (164.0, -62.0)  # where the Frozen Pass leaves the glacier's tongue (the ruin), on east
PASS_END = (262.0, -90.0)
# v4b (Blake, Oct 30: "go higher still ... build the mountain up and relocate the portal",
# "a little village that is carved straight into the plateau ... a small village that
# captures the culture of the area and is independent of the level designs, like ... the
# little village in dino valley"; he chose the stone-carvers, and the mountain in the
# south: the Burnt Gorge is a road from the valley, it comes over the kingdom's rim): the
# Carvers' Crest. Up the outside of the southern mountains from the passage in two
# hairpins to the Crest Gate, 140 m, over every world's walls, the whole kingdom below;
# then down the inner cliff in five legs into the pass, onto the lap. The carvers'
# village is cut into the faces between the legs, its square on a terrace halfway down.
GORGE_END = (0.0, -410.0)  # the passage back to the valley, at the climb's foot
CREST = (-24.0, -348.0)  # the Crest Gate
CREST_WAY = [  # (x, y) from the passage to the lap (v4b: pushed back 50 m, Blake, Oct 30)
    (0.0, -410.0),
    (60.0, -405.0),
    (82.0, -389.0),  # hairpin (opened out: its legs were too close, the one over the other)
    (40.0, -372.0),
    (-20.0, -372.0),
    (-34.0, -362.0),  # and up north
    (-24.0, -348.0),  # 6: the Crest Gate, the top, facing the kingdom
    (-4.0, -340.0),
    (40.0, -340.1),
    (66.0, -334.2),
    (78.0, -316.6),
    (50.0, -301.8),
    (-30.0, -298.9),
    (-44.0, -281.2),
    (-30.0, -266.5),
    (56.0, -263.6),
    (70.0, -245.9),
    (50.0, -231.2),
    (-30.0, -228.3),
    (-44.0, -210.6),
    (-26.0, -195.9),
    (24.0, -190.0),
    (30.0, -176.0),
    (24.0, -158.0),
]
_CREST_TOP = 6
_CREST_Z = (124.0, 155.0, 58.4)  # the passage, the Crest Gate, the lap
CARVERS = (14.0, -271.0, 15.0)  # the carvers' square: x, y, radius (on the third leg's terrace)
MOUNT = (-74.0, 104.0, -342.0, -350.0, 157.0)  # the Crest's x from, to; its inner and outer edges' y; its top


def _round_way(pts, every=3.0, r=11.0):
    """(x, y) waypoints, their corners rounded, sampled every `every` m."""
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
        for j in range(k + 1):
            ang = a0 + side * th * j / k
            out.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    out.append(pts[-1])
    dense = [out[0]]
    for a, b in zip(out, out[1:]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / every))
        for j in range(1, n + 1):
            dense.append((lerp(a[0], b[0], j / n), lerp(a[1], b[1], j / n)))
    return dense


def _crest_line():
    pts = _round_way(CREST_WAY)
    cum = [0.0]
    for p, q in zip(pts, pts[1:]):
        # (Round the climb's hairpin the road runs level, the climbing done on the legs
        # either side: its inside edge, a fraction of the way round, was too steep to drive.)
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        hx, hy = CREST_WAY[2]
        f = 0.15 + 0.85 * smooth((math.hypot(mx - hx, my - hy) - 12.0) / 10.0)
        cum.append(cum[-1] + f * math.hypot(q[0] - p[0], q[1] - p[1]))
    tx, ty = CREST_WAY[_CREST_TOP]
    top = min(range(len(pts)), key=lambda i: math.hypot(pts[i][0] - tx, pts[i][1] - ty))
    z0, zt, z1 = _CREST_Z
    out = []
    for i, (x, y) in enumerate(pts):
        z = lerp(z0, zt, cum[i] / cum[top]) if i <= top else lerp(zt, z1, (cum[i] - cum[top]) / (cum[-1] - cum[top]))
        out.append((x, y, z))
    return out


LOOKOUT_LINE = _crest_line()  # (the whole way in, from the passage to the lap)
LOOKOUT = CREST
_LK_BOX = (min(p[0] for p in LOOKOUT_LINE) - 30, max(p[0] for p in LOOKOUT_LINE) + 30,
           min(p[1] for p in LOOKOUT_LINE) - 30, max(p[1] for p in LOOKOUT_LINE) + 30)


# The plateau in the middle (Blake, Oct 30: "we may need to lower the mountain ... we can
# also use the ice plateau for decoration for the different areas"): the high ground
# inside the ring drawn down to PLATEAU_Z, still over every world's floor (each stays
# walled in) but low enough that from the Lookout you see across it into them all.
PLATEAU = (6.0, -4.0, 128.0)  # x, y, radius
PLATEAU_Z = 80.0


def plateau(h, x, y, wsd):
    px, py, pr = PLATEAU
    rc = math.hypot(x - px, y - py)
    if rc > pr or h <= PLATEAU_Z:
        return h
    w = smooth((wsd - 3.0) / 12.0) * smooth((pr - rc) / 34.0)
    # (Not a table: long low swells of wind-packed snow and ice over it.)
    z = PLATEAU_Z + 2.6 * math.sin(x / 37.0 + 0.6) * math.sin(y / 29.0 + 1.1) + 1.8 * math.sin((x + y) / 23.0)
    return lerp(h, min(h, z), w)


def lookout_floor(x, y):
    """(distance from the way in's line, its road height there) or None far off."""
    x0, x1, y0, y1 = _LK_BOX
    if not (x0 <= x <= x1 and y0 <= y <= y1):
        return None
    best = None
    for a, b in zip(LOOKOUT_LINE, LOOKOUT_LINE[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        if abs(x - a[0]) > 40 and abs(x - b[0]) > 40:
            continue
        L2 = dx * dx + dy * dy or 1e-9
        t = max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / L2))
        d = math.hypot(x - a[0] - dx * t, y - a[1] - dy * t)
        if best is None or d < best[0]:
            best = (d, lerp(a[2], b[2], t))
    return best


def _terrace_cols():
    """The descent's samples by metre of x: [(y, z)] sorted by y, for terrace()."""
    tx, ty = CREST_WAY[_CREST_TOP]
    top = min(range(len(LOOKOUT_LINE)), key=lambda i: math.hypot(LOOKOUT_LINE[i][0] - tx, LOOKOUT_LINE[i][1] - ty))
    # (Every metre along the descent, so no column misses a leg.)
    pts = []
    for a, b in zip(LOOKOUT_LINE[top:], LOOKOUT_LINE[top + 1:]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1])))
        pts.extend((lerp(a[0], b[0], j / n), lerp(a[1], b[1], j / n), lerp(a[2], b[2], j / n)) for j in range(n))
    cols = {}
    for x, y, z in pts:
        for k in range(int(math.floor(x)) - 1, int(math.floor(x)) + 2):
            cols.setdefault(k, []).append((y, z))
    for v in cols.values():
        v.sort()
    return cols


_TERRACE = _terrace_cols()


def terrace(h, x, y):
    """Between two legs of the switchbacks the mountain is cut in terraces, as the carvers
    cut it (Blake, Oct 30, "a little village that is carved straight into the plateau"):
    each leg's shelf runs level out to the next leg's sheer face (lookout_land cuts it)."""
    col = _TERRACE.get(int(math.floor(x)))
    if not col or y < col[0][0] or y > col[-1][0]:
        return h
    south = [z for yy, z in col if yy < y - 1.0]
    north = [yy for yy, z in col if yy > y + 1.0]
    if not south or not north:
        return h
    # (The leg just south, uphill: the highest-y sample below this point.)
    zs = max(((yy, z) for yy, z in col if yy < y - 1.0))[1]
    return zs - 0.25


def crest_height(x, y):
    """The mountain the Crest is: a broad top at MOUNT's height; its inner face falling north
    as steeply as the legs step down it (so from the gate you look down over them), its
    outer face falling south to the passage; its ends falling away east and west."""
    x0, x1, yin, yout, top = MOUNT
    side = smooth((x - x0) / 30.0) * smooth((x1 - x) / 30.0)
    return top - 0.78 * max(0.0, y - yin) - 0.5 * max(0.0, yout - y) - (1.0 - side) * 70.0


def lookout_land(h, x, y, wsd):
    """The Crest raised over the walls (never in a pocket), the carvers' square levelled,
    and the way in's shelf cut level across (cut into the mountain, built up where it
    crosses lower ground), 7 m each side, banked back into the land; a leg below another
    sits on its own shelf, the face between them a cliff (the carvers' village cut into
    them)."""
    if y < -150.0:
        ch = crest_height(x, y)
        if ch > h:
            h = lerp(h, ch, smooth((wsd - 6.0) / 14.0))
        h = terrace(h, x, y)
    f = lookout_floor(x, y)
    cx, cy, cr = CARVERS
    d = math.hypot(x - cx, y - cy)
    if d < cr + 12.0 and f is not None:
        zsq = lookout_floor(cx, cy)[1]
        h = lerp(zsq - 0.25, h, smooth((d - cr) / 12.0)) if d > cr else zsq - 0.25
    if f is None:
        return h
    dd, z = f
    if dd < 7.0:
        return z - 0.25
    # (Cut into the mountain, the face stands sheer: the carvers' rock, their houses cut
    # into it; built out over lower ground, it falls away more gently.)
    span = 3.5 if h > z else 9.0
    if dd < 7.0 + span:
        return lerp(z - 0.25, h, smooth((dd - 7.0) / span))
    return h


# v4c (Blake, Oct 30: "I do want a little village that we can drive around in as soon as
# we get down into the switch backs ... we can just go into the plateau and carve out
# space"; the ice carvers): the Ice Hollow, cut into the plateau's south flank over the
# pass where the switchbacks come down: sheer snow and ice walls round a level floor, open
# to the pass by its mouth, a lane looping round the carvers' homes in its walls and the
# sculpture garden in its middle.
HOLLOW = (12.0, -108.0, 38.0, 38.0)  # (Blake's pin, review-snow_region 1: (20, -133))  # x, y, half-widths across and along
HOLLOW_MOUTH = (12.0, -141.0, 24.0, 14.0)
HOLLOW_Z = 62.0
HOLLOW_LANE_WAY = [(0.0, -157.0), (-5.0, -138.0), (-10.0, -118.0), (-5.0, -95.0), (12.0, -86.0), (29.0, -95.0),
                   (33.0, -114.0), (28.0, -134.0), (22.0, -150.0)]
HOLLOW_GARDEN = (12.0, -110.0, 18.0)  # (the ice harvesters' yard)  # the sculpture garden: x, y, radius (inside the lane's loop)


def _ell(x, y, e):
    cx, cy, rx, ry = e
    return math.hypot((x - cx) / rx, (y - cy) / ry)


def hollow(h, x, y):
    """The Ice Hollow cut out of the land: its floor level (a hair higher to the back), its
    walls sheer (4 m), the mouth's floor easing down to the pass's road."""
    e1 = _ell(x, y, HOLLOW)
    e2 = _ell(x, y, HOLLOW_MOUTH)
    _, cy, _, ry = HOLLOW
    # (Inside: how far in from the wall, in metres, near enough.)
    d1 = (1.0 - e1) * min(HOLLOW[2], HOLLOW[3])
    d2 = (1.0 - e2) * min(HOLLOW_MOUTH[2], HOLLOW_MOUTH[3])
    d = max(d1, d2)
    if d < -1.5:
        return h
    zf = HOLLOW_Z + 0.8 * smooth((cy - y) / -ry)
    if d2 > d1:
        # (The mouth: down towards the road at its south.)
        zf = lerp(zf, 60.6, smooth((HOLLOW_MOUTH[1] - y) / HOLLOW_MOUTH[3]))
    if zf > h and d < 0.0:
        return h
    # (The walls sheer, 1.5 m: the carvers' homes are cut straight into them.)
    return lerp(h, min(h, zf) if d < 0.0 else zf, smooth((d + 1.5) / 1.5))


def hollow_floor(x, y):
    """In the Ice Hollow, on its floor (not its walls)."""
    return _ell(x, y, HOLLOW) < 0.97 or _ell(x, y, HOLLOW_MOUTH) < 0.95


def _hollow_lane():
    pts = _round_way(HOLLOW_LANE_WAY, every=2.5, r=9.0)
    return [(x, y, natural(x, y) + 0.05) for x, y in pts]


def natural(x, y):
    """The land, with the frozen lake's ice laid level in its hollow (and v5's drifts,
    kickers and the crevasse)."""
    h = L.natural(x, y) + drifts(x, y) + lips(x, y) - crevasse_cut(x, y)
    wsd = L.wall_sd(x, y)
    h = plateau(h, x, y, wsd)
    h = lookout_land(h, x, y, wsd)
    h = hollow(h, x, y)
    tx, ty, tr, tz = TREE_COURT
    dt = math.hypot(x - tx, y - ty)
    if dt < tr + 5.0 and h > tz:
        h = lerp(tz, h, smooth((dt - tr) / 5.0))
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
