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

WATER_Z = -0.8  # the bog's water
CAMP = (0.0, 4.0, 24.0)  # x, y, radius (the town square)
CAMP_Z = 26.0
TOP = 52.0  # the high ground between the pockets
RISE = 26.0  # how far a pocket's wall takes to rise to it
RIM_Z = TOP  # (the old name)

# The pockets: (name, the lobe whose look it has, circles (x, y, radius, floor height)).
# A pocket is the union of its circles (rounded where they join); its floor blends the
# circles' heights, so a pocket can slope (the Switchbacks fall from the camp to the river).
POCKETS = [
    ("camp", "camp", [(0.0, 0.0, 56.0, 26.0), (42.0, 46.0, 38.0, 26.0), (-28.0, 42.0, 30.0, 26.0), (68.0, 76.0, 24.0, 26.0)]),
    ("switchbacks", "riverbend",
     [(-62.0, -14.0, 30.0, 25.0), (-96.0, -20.0, 32.0, 18.0), (-118.0, 18.0, 32.0, 11.0), (-150.0, 44.0, 34.0, 5.0)]),
    ("riverbend", "riverbend",
     [(-205.0, 45.0, 75.0, 3.0), (-270.0, 118.0, 58.0, 3.5), (-150.0, 118.0, 40.0, 4.0), (-258.0, -32.0, 54.0, 2.5),
      (-210.0, 134.0, 36.0, 3.5), (-292.0, 60.0, 30.0, 3.0), (-204.0, -24.0, 28.0, 2.5)]),
    ("bonebog", "bonebog",
     [(-238.0, -168.0, 36.0, 0.4), (-178.0, -236.0, 78.0, 0.0), (-268.0, -258.0, 54.0, 0.0), (-98.0, -288.0, 50.0, 0.3)]),
    ("ember", "ember",
     [(98.0, -258.0, 46.0, 8.0), (176.0, -206.0, 78.0, 12.0), (256.0, -148.0, 56.0, 18.0), (238.0, -296.0, 54.0, 16.0), (262.0, -232.0, 32.0, 17.0)]),
    ("gulch", "ember",
     [(290.0, -76.0, 26.0, 19.0), (276.0, -48.0, 22.0, 19.5), (266.0, -24.0, 25.0, 20.0), (284.0, 2.0, 22.0, 20.5),
      (294.0, 26.0, 25.0, 21.0), (282.0, 54.0, 22.0, 21.0), (272.0, 80.0, 26.0, 21.0)]),
    ("cascade", "cascade",
     [(272.0, 138.0, 46.0, 21.0), (196.0, 206.0, 74.0, 23.0), (258.0, 292.0, 54.0, 29.0), (112.0, 282.0, 48.0, 25.0), (186.0, 304.0, 34.0, 27.0)]),
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
    [(-290.0, 172.0, 4.0), (-268.0, 128.0, 2.9), (-226.0, 92.0, 2.0), (-196.0, 52.0, 1.4), (-214.0, 8.0, 1.0),
     (-258.0, -34.0, 0.7), (-276.0, -54.0, 0.6)],
    [(286.0, 334.0, 27.0), (262.0, 300.0, 25.6), (232.0, 262.0, 23.2), (204.0, 232.0, 21.4), (186.0, 206.0, 20.6)],
]
RIVER = RIVERS[0]  # (the old name: the first)
RIVER_HW = 9.0
FALLS = [(-292.0, 180.0), (288.0, 342.0)]  # each river's falls' foot, at its cliff
# Still water (x, y, radius, height): Riverbend's lagoon, the Cascade's plunge pool.
LAKES = [(-282.0, -62.0, 18.0, 0.5), (184.0, 200.0, 24.0, 20.5)]


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
POOLS = [(-290.0, -236.0, 24.0), (-196.0, -292.0, 22.0), (-150.0, -222.0, 18.0), (-232.0, -200.0, 12.0),
         (-110.0, -300.0, 14.0), (-196.0, -186.0, 10.0), (-252.0, -290.0, 12.0)]
PYRAMID = (-298.0, -298.0)
LAVA = [(300.0, -150.0, 9.0), (270.0, -318.0, 12.0), (150.0, -205.0, 7.0)]


def natural(x, y):
    """The land's own height: the lowest of each pocket's floor rising into its walls (so
    ridges between pockets, cliffs between floors), rolling ground on the floors, the
    rivers' channels and the swamp's pools sunk in, mountains beyond the walls."""
    h = None
    best = 1e9
    for p in POCKETS:
        sd, f = pocket_sd(p, x, y)
        best = min(best, sd)
        # (the wall's rise in proportion to its height, so every wall's as steep: too
        # steep to drive up, the high ground out of reach)
        rise = max(10.0, 0.42 * (TOP - f))
        hp = lerp(f, TOP, smooth((sd + 8.0) / rise))
        h = hp if h is None else min(h, hp)
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
    if d < RIVER_HW + 14:
        h = lerp(h, wz - 1.4, smooth((RIVER_HW + 14 - d) / 14.0))
    for px, py, pr in POOLS:
        dp = math.hypot(x - px, y - py)
        if dp < pr + 12:
            h = lerp(h, WATER_Z - 1.0, smooth((pr + 12 - dp) / 12.0))
    # Craggy tops, and mountains beyond.
    if best > 0:
        h += 5.0 * smooth(best / 30.0) * (0.5 + 0.5 * math.sin(x / 17.0 + math.cos(y / 23.0) * 2.0))
        h += 40.0 * smooth((best - 70.0) / 110.0)
    return h


# The main road, one loop (x, y, height or None: None rides the land, a number is set by
# hand, through the tunnels). From the camp's south side, west to the plateau's edge.
ROUTE = [
    (36.0, -30.0, None),  # 0: the start, the camp's south side, westbound
    (-14.0, -40.0, None),
    (-58.0, -22.0, None),  # the plateau's edge: the Switchbacks
    (-92.0, -40.0, None),
    (-120.0, -14.0, None),
    (-104.0, 18.0, None),
    (-132.0, 50.0, None),
    (-164.0, 74.0, None),  # Riverbend
    (-186.0, 112.0, None),
    (-236.0, 150.0, None),
    (-292.0, 128.0, None),
    (-300.0, 76.0, None),
    (-268.0, 46.0, None),
    (-226.0, 45.0, None),  # over the river, straight across it
    (-186.0, 29.0, None),
    (-162.0, 6.0, None),
    (-198.0, -30.0, None),  # down the east bank, the lagoon over the water
    (-238.0, -88.0, 3.2),
    (-238.0, -118.0, 3.0),  # 17: the Fallen Giant
    (-236.0, -142.0, 1.8),
    (-218.0, -170.0, None),  # Bonebog
    (-246.0, -210.0, None),
    (-236.0, -248.0, None),
    (-196.0, -258.0, None),
    (-160.0, -248.0, None),
    (-126.0, -262.0, None),
    (-82.0, -270.0, None),
    (-52.0, -270.0, 2.2),  # 26: the Lava Tube
    (-4.0, -268.0, 4.4),
    (38.0, -264.0, 6.6),
    (80.0, -256.0, None),  # Ember
    (124.0, -232.0, None),
    (172.0, -258.0, None),
    (218.0, -300.0, None),
    (262.0, -276.0, None),
    (248.0, -222.0, None),
    (198.0, -194.0, None),
    (182.0, -150.0, None),
    (228.0, -128.0, None),
    (280.0, -112.0, None),
    (290.0, -70.0, None),  # 39: Smoke Gulch
    (264.0, -26.0, None),
    (294.0, 24.0, None),
    (270.0, 78.0, None),
    (262.0, 126.0, None),  # Cascade
    (276.0, 176.0, None),
    (246.0, 236.0, None),
    (272.0, 286.0, None),  # under the falls
    (226.0, 314.0, None),
    (162.0, 300.0, None),
    (112.0, 296.0, None),
    (92.0, 256.0, None),
    (130.0, 226.0, None),
    (150.0, 186.0, None),
    (122.0, 150.0, 25.0),  # 53: the Temple Steps
    (92.0, 112.0, 25.6),
    (70.0, 78.0, None),  # the camp
    (56.0, 22.0, None),
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
    "riverbend": (-330.0, 120.0),  # the palms on the bend's far bank, by the falls
    "cascade": (300.0, 300.0),  # the cave mouth beside the falls
    "bonebog": (-272.0, -302.0),  # the pyramid's tip, out in the bog
    "ember": (300.0, -300.0),  # the lava-lit cave in the volcano's foot
}
SCAR = (150.0, -330.0)  # Cinderjaw's Scar (the ruin's boss gateway), Ember's south wall
GORGE = (-150.0, 150.0)  # where the Burnt Gorge leaves Riverbend north (the ruin)
GORGE_END = 420.0
