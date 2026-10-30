# Dinosaur Valley's layout (v3): pure geometry, no Blender, so it can be drawn and checked
# on its own (valley_region.py builds it).
# SPDX-License-Identifier: MIT
#
# Blake (Oct 26): segments that capture each course's flavour; driving that isn't straight
# lines and circles; not one big circle but a shape of its own; varied ground; "think of
# kokiri forest", a world that feels big but isn't. And: separate the worlds the way the
# old kart-racer hubs did, with tunnels you can't see through and steep changes of height,
# so in the swamp you only see the swamp, with maybe an inkling of what lies beyond the
# tunnel or down the hill. The walls are landscape: rock, ridges, a fallen giant of a tree.
#
# So the valley is POCKETS: each a hollow of its own world, walled all round by high ground
# (the land's height is the lowest of each pocket's floor rising into its walls, so two
# pockets apart make a ridge between them, two at different heights a cliff), and the main
# road, one winding loop (the champion's 1-on-1 is raced on it), goes from pocket to pocket
# through a THRESHOLD each time:
#
#   the camp (hub)  Elder Mossback's camp, high on a plateau in the middle
#     the Switchbacks  over the plateau's edge and down a steep winding road, Riverbend
#                      opening below (the one view of another world: the hub's lookout)
#   Riverbend (W)   a palm-lined river bend, the river falling out of the north cliff
#     the Fallen Giant  a colossal hollow log through the ridge, the dinosaurs' tunnel
#   Bonebog (SW)    sunken swamp: pools, mud, dead trees, bones, the pyramid's tip
#     the Lava Tube    bored through a basalt ridge, red light at its far end
#   Ember (SE)      ash slopes rising to the volcano (its plume the valley's landmark,
#                   seen over every wall)
#     Smoke Gulch      a narrow S-bend ash canyon climbing north: its bends hide both ends
#   Cascade (NE)    a jungle canyon climbing to the falls, temple ruins in the trees
#     the Temple Steps  a carved tunnel back up onto the camp's plateau
#
# Blender coordinates (x east, y north, z up).

import math

from pocket_kit import rim_crags, tier_of, tiered_walls  # noqa: F401

WATER_Z = -0.8  # the bog's water
CAMP = (0.0, 3.0, 22.0)  # x, y, radius (the town square)
CAMP_Z = 26.0
TOP = 52.0  # the high ground between the pockets
RISE = 26.0  # how far a pocket's wall takes to rise to it
RIM_Z = TOP  # (the old name)

# v4 (Blake, Oct 28: "travel takes a while"): the whole valley drawn in to about 0.62 of its
# size, the loop some 40% shorter (its bends eased to a 12 m radius at least), the camp a little less (it has the village in it now),
# every world still its own pocket behind its own threshold. The walls rise in tiers with
# shelves (pocket_kit.terrace: "we need some ledges").
#
# The pockets: (name, the lobe whose look it has, circles (x, y, radius, floor height)).
# A pocket is the union of its circles (rounded where they join); its floor blends the
# circles' heights, so a pocket can slope (the Switchbacks fall from the camp to the river).
POCKETS = [
    ("camp", "camp", [(0.0, 0.0, 46.0, 26.0), (33.6, 36.8, 31.0, 26.0), (-22.4, 33.6, 25.0, 26.0), (54.4, 60.8, 20.0, 26.0)]),
    ("switchbacks", "riverbend",
     [(-40.0, -10.0, 20.0, 25.0), (-60.0, -13.0, 21.0, 18.0), (-74.0, 11.0, 21.0, 11.0), (-94.0, 28.0, 22.0, 5.0)]),
    ("riverbend", "riverbend",
     [(-128.0, 28.0, 50.0, 3.0), (-167.0, 74.0, 39.0, 3.5), (-94.0, 74.0, 27.0, 4.0), (-160.0, -19.0, 36.0, 2.5),
      (-130.0, 85.0, 25.0, 3.5), (-183.0, 37.0, 21.0, 3.0), (-126.0, -15.0, 20.0, 2.5)]),
    ("bonebog", "bonebog",
     [(-147.6, -106.0, 24.0, 0.4), (-110.0, -148.0, 51.0, 0.0), (-166.0, -162.0, 36.0, 0.0), (-61.0, -180.0, 33.0, 0.3)]),
    ("ember", "ember",
     [(61.0, -161.0, 31.0, 8.0), (109.0, -128.0, 51.0, 12.0), (159.0, -92.0, 37.0, 18.0), (148.0, -185.0, 36.0, 16.0),
      (163.0, -145.0, 22.0, 17.0)]),
    ("gulch", "ember",
     [(180.0, -47.0, 18.0, 19.0), (171.0, -30.0, 16.0, 19.5), (165.0, -15.0, 17.5, 20.0), (176.0, 1.0, 16.0, 20.5),
      (182.0, 16.0, 17.5, 21.0), (175.0, 33.5, 16.0, 21.0), (169.0, 50.0, 18.0, 21.0)]),
    ("cascade", "cascade",
     [(169.0, 86.0, 31.0, 21.0), (122.0, 128.0, 48.0, 23.0), (160.0, 181.0, 36.0, 29.0), (69.0, 175.0, 32.0, 25.0),
      (115.0, 189.0, 23.0, 27.0)]),
]
LOBES = [("riverbend",), ("cascade",), ("ember",), ("bonebog",)]  # (the lobes, by look)
NAMES = ["riverbend", "cascade", "ember", "bonebog", "camp"]


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def _smin(a, b, k):
    h = max(0.0, min(1.0, 0.5 + 0.5 * (b - a) / k))
    return lerp(b, a, h) - k * h * (1 - h)


def pocket_sd(p, x, y):
    """Signed distance from the pocket's edge (< 0 inside), and its floor height there."""
    sd = None
    fw = fz = 0.0
    for cx, cy, r, f in p[2]:
        d = math.hypot(x - cx, y - cy) - r
        sd = d if sd is None else _smin(sd, d, 22.0)
        w = math.exp(-max(0.0, d + r * 0.6) / 30.0)
        fw += w
        fz += w * f
    return sd, fz / fw


def wall_sd(x, y):
    """How far into the high ground (x, y) is: < 0 inside some pocket."""
    return min(pocket_sd(p, x, y)[0] for p in POCKETS)


def lobe_weights(x, y):
    """How much (x, y) belongs to each world's look (they sum to 1)."""
    acc = {n: 0.0 for n in NAMES}
    for p in POCKETS:
        sd, _ = pocket_sd(p, x, y)
        acc[p[1]] += math.exp(-max(-40.0, sd) / 14.0)
    tot = sum(acc.values()) or 1.0
    return {n: w / tot for n, w in acc.items()}


def pocket_at(x, y):
    return min(POCKETS, key=lambda p: pocket_sd(p, x, y)[0])[0]


def _seg_d(px, py, a, b):
    ax, ay = a[0], a[1]
    bx, by = b[0], b[1]
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy), t


# The rivers (x, y, water height): Riverbend's falls out of its north cliff and winds
# south to its lagoon; the Cascade's out of the canyon's head, down to its plunge pool.
RIVERS = [
    [(-181.0, 108.0, 4.0), (-166.0, 80.0, 2.9), (-140.0, 57.0, 2.0), (-121.5, 32.0, 1.4), (-133.0, 5.0, 1.0),
     (-160.0, -21.0, 0.7), (-172.0, -34.0, 0.6)],
    [(177.0, 207.0, 27.0), (162.0, 186.0, 25.6), (144.0, 162.0, 23.2), (126.5, 144.0, 21.4), (115.0, 128.0, 20.6)],
]
RIVER = RIVERS[0]  # (the old name: the first)
RIVER_HW = 8.0
FALLS = [(-182.0, 113.0), (178.6, 212.0)]  # each river's falls' foot, at its cliff
# Still water (x, y, radius, height): Riverbend's lagoon, the Cascade's plunge pool.
LAKES = [(-176.0, -39.0, 15.0, 0.5), (114.0, 124.0, 16.0, 20.5)]


def river_d(x, y):
    """Distance to the nearest river's middle, and the water's height there."""
    best, bz = 1e9, 0.0
    for riv in RIVERS:
        for a, b in zip(riv, riv[1:]):
            d, t = _seg_d(x, y, a, b)
            if d < best:
                best, bz = d, lerp(a[2], b[2], t)
    for lx, ly, lr, lz in LAKES:
        d = max(0.0, math.hypot(x - lx, y - ly) - lr + RIVER_HW)
        if d < best:
            best, bz = d, lz
    return best, bz


# The bog's pools (x, y, radius), its pyramid's tip; Ember's lava pools.
POOLS = [(-180.0, -147.0, 15.0), (-121.5, -182.0, 14.0), (-94.0, -137.0, 11.5), (-144.0, -125.0, 7.5),
         (-68.0, -187.0, 9.0), (-122.0, -116.0, 6.5), (-157.0, -181.0, 7.5)]
PYRAMID = (-202.0, -184.0)  # (Oct 28: moved back behind its gateway, and bigger)
LAVA = [(186.0, -93.0, 6.0), (167.0, -198.0, 8.0), (93.0, -127.0, 5.0)]


def natural(x, y):
    """The land's own height: the lowest of each pocket's floor rising into its walls (so
    ridges between pockets, cliffs between floors), rolling ground on the floors, the
    rivers' channels and the swamp's pools sunk in, mountains beyond the walls."""
    # (v4: the walls rise in tiers, steep risers and shelves between: pocket_kit.terrace)
    h, info = tiered_walls(POCKETS, TOP, x, y)
    best, past = info["best"], info["past"]
    w = lobe_weights(x, y)
    floor = 1.0 - smooth((best + 14.0) / 20.0)
    # Rolling ground (the swamp stays low and flat, the camp level, the switchbacks and the
    # gulch their own slopes).
    roll = (5.0 * math.sin(x / 61.0 + 0.6) * math.cos(y / 73.0 - 0.3) + 2.6 * math.sin((x - y) / 47.0)
            + 1.0 * math.sin(x / 23.0) * math.cos(y / 29.0))
    h += roll * floor * (1.0 - 0.85 * w["bonebog"]) * (1.0 - w["camp"])
    # The camp's square is level.
    cx, cy, cr = CAMP
    h = lerp(CAMP_Z, h, smooth((math.hypot(x - cx, y - cy) - cr) / 16.0))
    # The rivers' channels and the lakes.
    d, wz = river_d(x, y)
    if d < RIVER_HW + 8:
        # (Deeper than it was, 1.4 m: the water and the sand under its shallow edge fought,
        # Blake, Riverbend note 8, "perhaps we need to make the river deeper slightly".)
        # (Its banks steep, over 8 m, not 14: the gentle ones left a broad beach of sand
        # with the water a thin strip down the middle, Blake, valley polish 19, note 2,
        # "we need more water, there is way too much sand".)
        h = lerp(h, wz - 2.2, smooth((RIVER_HW + 8 - d) / 8.0))
    if d < RIVER_HW + 16:
        # (And a bank: where the land round the water lay barely over it, it was a broad
        # flat of sand; now it rises to 0.6 m over the water 7 m past the channel's
        # edge, so the water fills its bed right up to a grassy bank with a thin beach.)
        bank = wz - 2.2 + 2.8 * smooth((d - RIVER_HW - 1.5) / 6.0)
        h = max(h, min(bank, wz + 0.6))
    for px, py, pr in POOLS:
        dp = math.hypot(x - px, y - py)
        if dp < pr + 12:
            h = lerp(h, WATER_Z - 1.0, smooth((pr + 12 - dp) / 12.0))
    # Craggy tops, and mountains beyond.
    h += rim_crags(x, y, past, 40.0)
    return falls_cliff(h, x, y, info["floor"])


def falls_axis(j):
    """The falls' foot (x, y), and the way the water runs off it (unit x, y)."""
    fx, fy = FALLS[j]
    riv = RIVERS[j]
    dx, dy = riv[1][0] - riv[0][0], riv[1][1] - riv[0][1]
    d = math.hypot(dx, dy)
    return fx, fy, dx / d, dy / d


FALLS_HALF = 18.0  # half the cliff's width behind each falls


def falls_cliff(h, x, y, floor):
    """Behind each falls a sheer cliff, the whole height of the wall, the river coming over
    its rim in a shallow channel (Blake, note 43: "this needs to be magnificent"), and an
    alcove opened in the tiers before it."""
    for j in range(len(FALLS)):
        fx, fy, ux, uy = falls_axis(j)
        s = -((x - fx) * ux + (y - fy) * uy)  # (m upstream of the foot: behind it)
        lat = abs(-(x - fx) * uy + (y - fy) * ux)
        w = smooth((FALLS_HALF + 10.0 - lat) / 10.0) * smooth((s + 34.0) / 12.0) * smooth((60.0 - s) / 14.0)
        if w <= 0.0:
            continue
        f = RIVERS[j][0][2] - 0.6
        if s < -2.0:
            hc = min(h, f + 0.5 * smooth((-s - 2.0) / 10.0))
        else:
            hc = f + (TOP + 1.0 - f) * smooth((s + 2.0) / 5.0)
            if s > 3.0:
                hc -= 1.6 * smooth((9.0 - lat) / 4.0)  # (the river's channel to the lip)
        h = lerp(h, hc, w)
    return h


def wall_info(x, y):
    """Which pocket's wall (x, y) is on, its floor, how many tiers (pocket_kit)."""
    return tiered_walls(POCKETS, TOP, x, y)[1]


# The main road, one loop (x, y, height or None: None rides the land, a number is set by
# hand, through the tunnels). From the camp's south side, west to the plateau's edge.
ROUTE = [
    (22.0, -19.0, None),  # 0: the start, the camp's south side, westbound
    (-9.0, -25.0, None),
    (-35.5, -15.7, None),  # the plateau's edge: the Switchbacks
    (-52.9, -14.3, None),
    (-64.5, -4.3, None),
    (-69.1, 11.2, None),
    (-82.0, 31.0, None),
    (-102.0, 46.0, None),  # Riverbend
    (-115.0, 70.0, None),
    (-146.0, 93.0, None),
    (-181.0, 79.0, None),
    (-186.0, 47.0, None),
    (-166.0, 28.5, None),
    (-140.0, 28.0, None),  # over the river, straight across it
    (-115.0, 18.0, None),
    (-109.3, 1.7, None),
    (-123.0, -18.5, None),  # down the east bank, the lagoon over the water
    (-147.6, -54.6, 3.2),
    (-147.6, -73.2, 3.0),  # 18: the Fallen Giant
    (-146.3, -88.0, 1.8),
    (-141.9, -107.4, None),  # Bonebog
    (-152.5, -130.0, None),
    (-146.0, -154.0, None),
    (-121.5, -160.0, None),
    (-99.0, -154.0, None),
    (-78.0, -162.5, None),
    (-51.0, -167.5, None),
    (-32.2, -167.4, 2.2),  # 27: the Lava Tube
    (-2.5, -166.2, 4.4),
    (23.6, -163.7, 6.6),
    (49.6, -158.7, None),  # Ember
    (77.0, -144.0, None),
    (106.5, -160.0, None),
    (135.0, -186.0, None),
    (162.5, -171.0, None),
    (154.0, -137.5, None),
    (123.0, -120.0, None),
    (118.3, -94.9, None),
    (141.5, -79.5, None),
    (173.5, -69.5, None),
    (180.0, -43.5, None),  # 40: Smoke Gulch
    (166.6, -15.7, None),
    (182.0, 15.0, None),
    (167.5, 48.5, None),
    (162.5, 78.0, None),  # Cascade
    (171.0, 109.0, None),
    (152.5, 146.0, None),
    (157.9, 174.0, None),  # under the falls
    (140.0, 194.5, None),
    (100.5, 186.0, None),
    (72.9, 180.5, None),
    (66.0, 159.7, None),
    (80.5, 140.0, None),
    (90.8, 115.7, None),
    (75.6, 93.0, 25.0),  # 54: the Temple Steps
    (57.0, 69.4, 25.6),
    (43.5, 48.5, None),  # the camp
    (35.0, 13.5, None),
]
# The tunnels: (name, kind, first and last route point inside the rock).
TUNNELS = [("Fallen Giant", "log", 18, 19), ("Lava Tube", "lava", 27, 29), ("Temple Steps", "temple", 54, 55)]

FIXED = {}
_CORRIDORS = []


_BRIDGES = []


def bridge_floor(x, y):
    """Under a bridge: the deck's underside if (x, y) is within 13 m of the road where it
    crosses the water (the banks are kept down under it, out past its barriers: a bank
    standing up into a bridge shoved karts sideways through its rail), else None."""
    if not _BRIDGES:
        for p in catmull(route_points(), 8):
            d, wz = river_d(p[0], p[1])
            if d < RIVER_HW + 12 and p[2] > wz + 0.9:
                _BRIDGES.append(p)
    best = None
    for p in _BRIDGES:
        d = math.hypot(x - p[0], y - p[1])
        if d < 13.0 and (best is None or d < best[0]):
            best = (d, p[2] - 1.9)
    return None if best is None else best[1]


def tunnel_floor(x, y):
    """Under a tunnel's rock: the road's height there if (x, y) is within 18 m of the road
    through it (the land is sunk below it, so none shows inside the bore), else None."""
    if not _CORRIDORS:
        rp = route_points()
        n = len(rp)
        for _, _, a, b in TUNNELS:
            sub = [rp[i % n] for i in range(a - 2, b + 4)]
            pts = catmull(sub, 8)[8:-16]
            _CORRIDORS.append([p for p in pts if wall_sd(p[0], p[1]) > -14.0])
    best = None
    for pts in _CORRIDORS:
        for p, q in zip(pts, pts[1:]):
            d, t = _seg_d(x, y, p, q)
            if d < 18.0 and (best is None or d < best[0]):
                best = (d, lerp(p[2], q[2], t))
    return None if best is None else best[1]


def route_points():
    """The main road's control points at the land's height round each (a ring average,
    smoothed, so the road rides the swells), the hand-set ones as set, over the rivers on
    bridges, above the bog."""
    n = len(ROUTE)
    zs = []
    for x, y, z in ROUTE:
        if z is None:
            ring = [natural(x + 12 * math.cos(a), y + 12 * math.sin(a)) for a in (0, 1.57, 3.14, 4.71)] + [natural(x, y)]
            z = sum(ring) / len(ring) + 0.3
        zs.append(z)
    for _ in range(2):
        zs = [z if ROUTE[i][2] is not None else 0.25 * zs[i - 1] + 0.5 * z + 0.25 * zs[(i + 1) % n]
              for i, z in enumerate(zs)]
    out = []
    for i, (x, y, _) in enumerate(ROUTE):
        z = zs[i]
        d, wz = river_d(x, y)
        if d < RIVER_HW + 24:
            z = max(z, wz + 2.4)
        z = max(z, WATER_Z + 0.8)
        out.append((x, y, round(FIXED.get(i, z), 2)))
    return out


def catmull(points, per=12):
    """A closed Catmull-Rom curve through (x, y, z) points (a stand-in for Blender's AUTO
    Bezier, for checking the layout without Blender)."""
    out = []
    n = len(points)
    for i in range(n):
        p0, p1, p2, p3 = (points[(i + k) % n] for k in (-1, 0, 1, 2))
        for s in range(per):
            t = s / per
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in range(3)))
    return out


# The gateways' landmarks (x, y): each world's, at the end of a short spur off the road.
GATES = {
    "riverbend": (-205.0, 75.0),  # the palms on the bend's far bank, by the falls
    "cascade": (188.0, 160.0),  # the cave mouth in the canyon wall, by the falls
    "bonebog": (-169.0, -188.0),  # the pyramid's tip, out in the bog
    "ember": (186.0, -186.0),  # the lava-lit cave in the volcano's foot
}
SCAR = (93.0, -205.0)  # Cinderjaw's Scar (the ruin's boss gateway), Ember's south wall
GORGE = (-93.0, 93.0)  # where the Burnt Gorge leaves Riverbend north (the ruin)
GORGE_END = 270.0
