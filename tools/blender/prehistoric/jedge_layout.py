# The Edge of the World's layout, v4 (Blake, Nov 2: "the driving is very boring and the
# inside is lacking. we need to completely rework it. it should be crawling with black
# market activity ... different areas that are distinct"; "the drive to the dragon isle is
# also boring"). Pure Python (no Blender): jedge_region.py builds it.
# SPDX-License-Identifier: MIT
#
# A chain of districts under the seabed, driven fast and wild (Blake chose "Chain of
# districts"; "Smugglers' docks, Night Bazaar, Fighting pits & gambling"; "Fast & wild"):
#
#   the Sea Door Grotto   in from the isles, a short bore down to
#   the Smugglers' Docks  a black-water harbour: the quay road past the cranes and the
#                         moored ships, over the canal's hump-backed bridge, out past the
#                         warehouses;
#   Smugglers' Alley      S-bends down a crooked bore, the Stair down the market's wall into
#   the Night Bazaar      a slalom through the lantern-lit market lanes, the Broker's ship
#                         hanging over it all, to the gate of
#   the Fighting Pits     the arena: the road corkscrews down its wall through the stands,
#                         the crowd on every side, the fight ring on its floor; out through
#   the Lucky Bone        the gambling den, then the Long Bore climbing to the cliff of
#   the Edge              the world's edge, and the Edge Bridge off it, out over nothing, to
#   the Sky Islands       floating rocks joined by chained bridges, dragons flying, up to
#   the Sky Gate          the Dragon Kingdom's gate: the loading zone.
#
# No jumps (Blake, Nov 3: "you cant actually traverse backwards. lets just remove the jumps
# completely ... we need to make the immersiveness so great such that the boring driving is
# justified"): one road, every metre of it drivable both ways.
#
# Blender coordinates (x east, y north, z up). The route is a loop (the kit's courses are),
# the road only from START to END; the rest goes round out of sight, high over everything.

import math

HZ = 260.0
DEPTH = -22.0  # the grotto's road (under the seabed)
SEABED = -3.0  # the slab's top: the sea floor, under the sea
WATER_Z = 0.0
VOID_Z = -170.0
SKY_FLOOR = -105.0  # under the sky islands: the abyss, hidden in the cloud sea
CLOUD_Z = VOID_Z + 70.0

# The districts: their middles, sizes and floors.
GROTTO = (-55.0, -430.0, 30.0, 38.0)
DOCKS = (-14.0, -300.0, 66.0, 54.0)
DOCK_Z = -24.0
DOCK_FLOOR = DOCK_Z - 0.6
DOCK_WATER = DOCK_Z - 2.0
BASIN = (-46.0, -302.0, 22.0)  # the harbour's black water (west of the quay)
CANAL = (-300.0, 5.0, -26.0, 49.0)  # y, half width, from x, to x: the harbour's outflow, under the bridge
# The harbour's water (Blake, Nov 4: "theres a harbor that makes no sense. the boats are
# passing through bridges, the river is coming from no where"): the sea leaks in through a
# crack in the roof over the basin's west side (SEA_LEAK: x, y, the crack's height), and
# runs out east down the canal, under the road's stone bridge, over a weir (WEIR_X) into
# the sump pool, and away through the iron water gate in the cavern's east wall.
SEA_LEAK = (-60.0, -304.0, -11.0)
WEIR_X = 41.0
SUMP_DROP = 2.4  # (the sump pool under the weir: how far below the harbour's water)
BAZAAR = (140.0, -145.0, 64.0, 76.0)
BAZ_Z = -34.0
BAZ_FLOOR = BAZ_Z - 0.6
PIT = (40.0, -10.0)
PIT_R = (34.0, 66.0, 82.0)  # the floor's edge, the stands' top, the wall
PIT_RIM = -34.0
PIT_FLOOR = -61.5
DEN = (152.0, 36.0, 30.0, 26.0)
DEN_Z = -57.0
DEN_FLOOR = DEN_Z - 0.6
MOUTH = (24.0, 182.0)  # where the Long Bore comes out of the world's edge
# The Rookery (Nov 4): the canyon street from the docks to the Gallery, its walls ROOK_N to
# the left of the road and ROOK_S to its right, ROOK_ROOF over it; the water street down
# its right side (its middle ROOK_CANAL[0] right of the road, ROOK_CANAL[1] half wide), its
# water level all the way (the street climbs: its banks stand higher and higher over it).
ROOK_N, ROOK_S = 13.0, 26.0
ROOK_ROOF = 16.0  # (the seabed's top is only some 20 m over the road)
ROOK_CANAL = (17.0, 3.8)
ROOK_WATER = -27.6
# The Beast Market: the Night Bazaar's other lane, off the road at the fork, round the
# Broker's ship's other side, back on at the join (a side road: jedge_region.py).
BEAST_MARKET = [(171.0, -137.0, BAZ_Z), (160.0, -126.0, BAZ_Z), (142.0, -122.0, BAZ_Z), (124.0, -116.0, BAZ_Z),
                (113.0, -101.0, BAZ_Z), (112.0, -86.0, BAZ_Z), (106.0, -76.0, BAZ_Z)]


def rim_y(x):
    return 174.0 + 8.0 * math.sin(x / 41.0) + 4.0 * math.sin(x / 13.0 + 1.0)


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


# The spiral down the Fighting Pits' wall: clockwise 300 degrees from its south-east gate,
# tightening, from the rim to the floor (the stands all round it).
SPIRAL_A0, SPIRAL_TURN = -60.0, 300.0
SPIRAL_R = (66.0, 36.0)
SPIRAL_Z = (PIT_RIM, PIT_FLOOR + 0.5)


def spiral_at(a_deg):
    """The spiral's (r, z) at angle a (degrees, decreasing from SPIRAL_A0): it tightens
    steadily, and drops the same every metre (the grade even all the way down)."""
    t = (SPIRAL_A0 - a_deg) / SPIRAL_TURN
    r0, r1 = SPIRAL_R
    run = (r0 * t - (r0 - r1) * t * t / 2.0) / ((r0 + r1) / 2.0)
    return lerp(r0, r1, t), lerp(SPIRAL_Z[0], SPIRAL_Z[1], run)


def _spiral():
    out = []
    for k in range(13):
        a = SPIRAL_A0 - SPIRAL_TURN * k / 12
        r, z = spiral_at(a)
        out.append((PIT[0] + r * math.cos(math.radians(a)), PIT[1] + r * math.sin(math.radians(a)), z,
                    "pit%d" % k))
    return out


ROUTE = [
    (-70.0, -490.0, DEPTH, "lead_in"),  # (no road): back towards the isles' sea door
    (-60.0, -440.0, DEPTH, "start"),  # START, from Tropic Isles
    (-48.0, -404.0, DEPTH, "bore1"),
    (-36.0, -374.0, -23.0, "bore2"),
    # The Smugglers' Docks: up the quay, over the canal, out past the warehouses.
    (-20.0, -352.0, DOCK_Z, "dock0"),
    (-5.0, -332.0, DOCK_Z, "quay"),
    (-3.0, -318.0, DOCK_Z + 0.5, "canal_in"),
    # (the canal's stone bridge: up and over an arch the boats row under)
    (-3.0, -305.5, DOCK_Z + 1.3, "canal_a"),
    (-3.0, -300.0, DOCK_Z + 1.7, "canal"),
    (-3.0, -294.5, DOCK_Z + 1.3, "canal_b"),
    (-1.0, -281.0, DOCK_Z - 0.1, "dock1"),
    (16.0, -262.0, DOCK_Z - 0.9, "dock2"),
    (36.0, -252.0, DOCK_Z - 1.6, "dock3"),
    # The Rookery (Nov 4: "lets do all of it"): a crooked canyon street east through the
    # smugglers' slum, the shanties stacked up its walls, the water street beside it; in
    # the front door of the Rusty Anchor and out the back; climbing to the Gallery.
    # (rook0 where the old alley began, so the harbour's road out is just as it was)
    (58.0, -248.0, -26.5, "rook0"),
    (79.0, -256.0, -25.9, "rook1"),
    (97.0, -261.0, -25.3, "tav0"),  # the Rusty Anchor's front door
    (121.0, -262.0, -24.6, "tav1"),  # its back door
    (141.0, -261.0, -23.9, "rook2"),
    (160.0, -257.0, -23.0, "rook3"),
    (183.0, -253.0, -22.3, "rook4"),
    (201, -241, -21.8, "portal"),  # out on the Night Bazaar's wall: the whole market below
    # The Gallery: a scaffold ledge down the market's south wall, the hairpin round the
    # scaffold tower, back along under it.
    (207, -222, -21.9, "gal0"),
    (192, -206, -22.8, "gal1"),
    (140.0, -211.5, -24.7, "gal2"),
    (122.0, -208.0, -26.3, "gal3"),
    (105.5, -200.0, -27.6, "pin0"),
    (99.5, -186.5, -28.4, "pin1"),
    (105.5, -173.5, -29.2, "pin2"),
    (119.0, -168.0, -30.0, "pin3"),
    (137.0, -169.0, -31.5, "gal4"),
    (156.0, -164.0, -33.0, "gal5"),
    (168.0, -150.0, -33.8, "baz0"),
    # The Night Bazaar's lanes: Spice Row (this way) and the Beast Market (BEAST_MARKET, the
    # other) round the Broker's ship, to the Fighting Pits' gate.
    (172.0, -130.0, BAZ_Z, "fork"),
    (167.0, -108.0, BAZ_Z, "spice1"),
    (152.0, -91.0, BAZ_Z, "spice2"),
    (130.0, -81.0, BAZ_Z, "spice3"),
    (111.0, -77.0, BAZ_Z, "join"),
    (97.0, -74.0, PIT_RIM + 0.2, "pit_gate"),
] + _spiral() + [  # down the Fighting Pits' wall
    (77.0, -26.0, PIT_FLOOR + 0.5, "pit_floor"),
    (91.0, -38.0, PIT_FLOOR + 0.9, "pit_out0"),
    (106.0, -44.0, PIT_FLOOR + 1.4, "pit_out1"),
    (121.6, -48.0, PIT_FLOOR + 1.9, "pit_out2"),
    (140.0, -36.0, PIT_FLOOR + 2.6, "den_in0"),
    (152.0, -8.0, DEN_Z - 0.4, "den_in1"),
    # The Lucky Bone (the gambling den), and the Long Bore climbing out.
    (154.0, 18.0, DEN_Z, "den0"),
    (150.0, 40.0, DEN_Z, "den1"),
    (138.0, 60.0, DEN_Z + 0.6, "den2"),
    (118.0, 82.0, -54.0, "bore3"),
    (92.0, 112.0, -50.0, "bore4"),
    (66.0, 138.0, -47.0, "bore5"),
    (40.0, 150.0, -44.5, "bore6"),
    (28.0, 160.0, -43.4, "bore7"),
    (24.0, 171.0, -43.1, "mouth0"),
    (24.0, 184.0, -43.4, "mouth"),  # out of the edge of the world: the Edge Bridge
    (24.0, 196.0, -44.4, "edge_b"),
    # The Sky Islands.
    (22.0, 211.0, -45.0, "isle1"),
    (6.0, 226.0, -45.0, "isle1b"),
    (-10.0, 238.0, -43.4, "bridge1a"),
    (-28.0, 256.0, -40.4, "bridge1b"),
    (-36.0, 272.0, -40.0, "isle2"),
    (-36.5, 285.0, -40.2, "perch_a"),
    (-35.0, 297.5, -40.7, "perch_b"),
    (-33.4, 310.0, -41.3, "shrine_a"),
    (-30.0, 322.0, -41.5, "land4b"),
    (-20.0, 334.0, -41.5, "isle3"),
    (-10.0, 348.0, -41.5, "isle3c"),
    (2.0, 362.0, -39.8, "bridge2a"),
    (14.0, 378.0, -37.6, "bridge2b"),
    (16.0, 392.0, -37.2, "gk_a"),
    (16.0, 404.0, -37.5, "gk_b"),
    (16.0, 416.0, -38.2, "gate_a"),
    (8.0, 431.0, -38.5, "isle5"),
    (0.0, 445.0, -38.5, "end"),  # END, at the Sky Gate
    (0.0, 476.0, -38.5, "lead_out"),  # (no road)
    (250.0, 520.0, HZ, "away0"),
    (480.0, 200.0, HZ, "away1"),
    (450.0, -300.0, HZ, "away2"),
    (150.0, -530.0, HZ, "away3"),
    (-150.0, -530.0, HZ, "away4"),
]
AT = {p[3]: i for i, p in enumerate(ROUTE)}
START, END = AT["start"], AT["end"]
ENDS = {"start": ((-60.0, -440.0), (-70.0, -490.0)), "end": ((0.0, 445.0), (0.0, 476.0))}

# The sky islands: (name, x, y, radius, the road's height on it).
ISLES = [
    ("Landing Rock", 18.0, 212.0, 21.0, -45.0),
    ("Dragon's Perch", -38.0, 280.0, 18.0, -40.0),
    ("Shrine Isle", -26.0, 326.0, 25.0, -41.5),
    ("Gatekeeper's Rock", 20.0, 390.0, 15.0, -37.0),
    ("Sky Gate Isle", 8.0, 434.0, 26.0, -38.5),
]

# The underground's caverns, cut out of the seabed's rock: (name, x, y, rx, ry, floor,
# roof over the floor). The Fighting Pits are a drum of their own (jedge_region.py).
CAVERNS = [
    ("Sea Door Grotto", GROTTO[0], GROTTO[1], GROTTO[2], GROTTO[3], DEPTH - 0.6, 31.0),
    ("Smugglers' Docks", DOCKS[0], DOCKS[1], DOCKS[2], DOCKS[3], DOCK_FLOOR, 19.0),
    ("Night Bazaar", BAZAAR[0], BAZAAR[1], BAZAAR[2], BAZAAR[3], BAZ_FLOOR, 28.0),
    ("Lucky Bone", DEN[0], DEN[1], DEN[2], DEN[3], DEN_FLOOR, 17.0),
]
# The holes in the seabed: the grotto's, open to the sea overhead (where you come in).
SKYLIGHTS = [(-55.0, -430.0, 20.0)]
# The Edge: the reef standing out of the sea on the slab, the rim where the sea falls off.
SHELF = (64.0, 122.0, 118.0)  # x, y, radius


# ------------------------------------------------------------------ the road


def _catmull_seg(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return tuple(0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                        + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in range(3))


def _dense():
    """The road every ~3 m (20 m on the way round out of sight) along the curve through
    ROUTE. Returns the points and the dense index of each ROUTE point."""
    n = len(ROUTE)
    pts, at = [], []
    for i in range(n):
        p0, p1, p2, p3 = (ROUTE[(i + k) % n][:3] for k in (-1, 0, 1, 2))
        at.append(len(pts))
        L = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        k = max(2, int(L / (20.0 if i > END else 3.0)))
        for j in range(k):
            x, y, z = _catmull_seg(p0, p1, p2, p3, j / k)
            # (z: straight between the two points' heights, never overshooting them)
            z = lerp(p1[2], p2[2], j / k)
            pts.append([x, y, z])
    cum = [0.0]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return [(round(x, 2), round(y, 2), round(z, 2)) for x, y, z in pts], at, cum


DENSE, DAT, CUM = _dense()


def _seg(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / L2))
    return math.hypot(px - a[0] - t * dx, py - a[1] - t * dy), t


_GRID = {}
for _k in range(DAT[START] - 8, DAT[END] + 10):
    _a, _b = DENSE[_k], DENSE[_k + 1]
    for _gx in range(int(math.floor(min(_a[0], _b[0]) / 24)) - 1, int(math.floor(max(_a[0], _b[0]) / 24)) + 2):
        for _gy in range(int(math.floor(min(_a[1], _b[1]) / 24)) - 1, int(math.floor(max(_a[1], _b[1]) / 24)) + 2):
            _GRID.setdefault((_gx, _gy), []).append((_a, _b, _k))


def road_floor(x, y):
    """How far (x, y) is from the road, and the road's height there."""
    best = (1e9, 0.0)
    _NEAR_K[0] = None
    for a, b, k in _GRID.get((int(math.floor(x / 24)), int(math.floor(y / 24))), ()):
        d, t = _seg(x, y, a, b)
        if d < best[0]:
            best = (d, lerp(a[2], b[2], t))
            _NEAR_K[0] = k
    return best


_NEAR_K = [None]  # (the dense index of the segment road_floor found last)


def flat_out(x, y):
    """How far out from the road the ground lies level with it: across the bores' floors,
    a little less in the open."""
    return 10.0 if cavern_at(x, y)[0] is None else 8.0


_ROOK = {}
for _k in range(DAT[AT["rook0"]] - 2, DAT[AT["portal"]] + 3):
    _a, _b = DENSE[_k], DENSE[_k + 1]
    for _gx in range(int(math.floor(min(_a[0], _b[0]) / 24)) - 2, int(math.floor(max(_a[0], _b[0]) / 24)) + 3):
        for _gy in range(int(math.floor(min(_a[1], _b[1]) / 24)) - 2, int(math.floor(max(_a[1], _b[1]) / 24)) + 3):
            _ROOK.setdefault((_gx, _gy), []).append((_a, _b, _k))


def rook_at(x, y):
    """In the Rookery? (its lateral offset from the road, + to the right; the road's height
    there; the dense index), or None."""
    best = None
    for a, b, k in _ROOK.get((int(math.floor(x / 24)), int(math.floor(y / 24))), ()):
        d, t = _seg(x, y, a, b)
        if best is None or d < best[0]:
            dx, dy = b[0] - a[0], b[1] - a[1]
            n = math.hypot(dx, dy) or 1.0
            lat = ((x - a[0]) * dy - (y - a[1]) * dx) / n  # (+: right of the way along)
            best = (d, lat, lerp(a[2], b[2], t), k, t)
    if best is None:
        return None
    d, lat, z, k, t = best
    if (k <= DAT[AT["rook0"]] and t == 0.0) or (k >= DAT[AT["portal"]] and t == 1.0) or k < DAT[AT["rook0"]]:
        return None
    if not -ROOK_N < lat < ROOK_S:
        return None
    return lat, z, k


def rook_canal(x, y):
    """In the Rookery's water street (between rook0 and rook3)? Its water's (lateral
    distance from the middle, half width), else None."""
    r = rook_at(x, y)
    if r is None or not DAT[AT["rook1"]] <= r[2] < DAT[AT["rook3"]]:
        return None
    return abs(r[0] - ROOK_CANAL[0]), r[1]


def gallery_up(x, y):
    """How far the road near (x, y) is up over the Night Bazaar's floor (the Gallery)."""
    d, z = road_floor(x, y)
    return z - BAZ_FLOOR if d < 30.0 else 0.0


# ------------------------------------------------------------------ the land


def pit_r(x, y):
    return math.hypot(x - PIT[0], y - PIT[1])


def ellipse(x, y, cx, cy, rx, ry):
    return math.hypot((x - cx) / rx, (y - cy) / ry)


def cavern_at(x, y):
    """The district (x, y) is in, and how far out in it (0 the middle, 1 its wall)."""
    r = pit_r(x, y)
    if r < PIT_R[2]:
        return "Fighting Pits", r / PIT_R[2]
    rk = rook_at(x, y)
    if rk is not None:
        return "Rookery", (rk[0] / ROOK_S if rk[0] > 0 else -rk[0] / ROOK_N)
    for name, cx, cy, rx, ry, _f, _h in CAVERNS:
        e = ellipse(x, y, cx, cy, rx, ry)
        if e < 1.0:
            return name, e
    return None, 9.0


def pit_cone(r):
    """The Fighting Pits' ground: the sand floor, the slope of the stands up to the rim."""
    f0, f1, f2 = PIT_R
    if r < f0:
        return PIT_FLOOR
    if r < f1:
        return lerp(PIT_FLOOR, PIT_RIM - 0.5, (r - f0) / (f1 - f0))
    return PIT_RIM - 0.5


def _pit_surface(r, a_s):
    """The stands' ground at radius r beside the spiral where it's at angle a_s: down
    from the road to the floor's edge inside, up from it to the wall outside."""
    f0, f1, f2 = PIT_R
    r_road, z_road = spiral_at(a_s)
    shelf = 8.5  # (level with the road out to its rails)
    if r < r_road - shelf:
        return max(PIT_FLOOR, lerp(PIT_FLOOR, z_road, (r - f0) / max(1.0, r_road - shelf - f0)))
    if r < r_road + shelf:
        return max(PIT_FLOOR, z_road)
    return lerp(z_road, PIT_RIM - 0.5, min(1.0, (r - r_road - shelf) / max(1.0, f2 - 2.0 - r_road - shelf)))


def pit_ground(x, y):
    """The Fighting Pits' ground: the sand floor, and the stands rising round the spiral
    like a helter-skelter's (between its two ends, eased from the one to the other)."""
    r = pit_r(x, y)
    if r < PIT_R[0]:
        return PIT_FLOOR
    a = math.degrees(math.atan2(y - PIT[1], x - PIT[0]))
    a0 = SPIRAL_A0
    a1 = SPIRAL_A0 - SPIRAL_TURN
    if a0 < a < a0 + 360.0 - SPIRAL_TURN:
        # (the gap between the spiral's top and its foot)
        t = (a - a0) / (360.0 - SPIRAL_TURN)
        return lerp(_pit_surface(r, a0), _pit_surface(r, a1), smooth(t))
    a_s = a if a <= a0 else a - 360.0
    return _pit_surface(r, max(a1, a_s))


def in_water(x, y):
    """In the docks' black water (the harbour basin or the canal)?"""
    bx, by, br = BASIN
    if math.hypot(x - bx, y - by) < br:
        return True
    cy, hw, cx0, cx1 = CANAL
    if abs(y - cy) < hw and cx0 - 2.0 < x < cx1 and ellipse(x, y, *DOCKS) < 0.98:
        return True
    rc = rook_canal(x, y)
    return rc is not None and rc[0] < ROOK_CANAL[1]


def water_z(x, y):
    """The water's level where in_water: the docks', or the Rookery's water street's."""
    return ROOK_WATER if rook_canal(x, y) is not None else DOCK_WATER


def over_canal(x, y, margin=2.5):
    """Over the canal (or just short of its edges): where the road's on its bridge."""
    cy, hw, cx0, cx1 = CANAL
    return abs(y - cy) < hw + margin and cx0 < x < cx1


def reef_z(x, y):
    """The slab's top: the sea floor, and the reef standing out of the sea by the rim."""
    sx, sy, sr = SHELF
    d = math.hypot((x - sx) * 0.9, y - sy)
    reef = 4.5 + 1.6 * math.sin(x / 9.0) * math.cos(y / 11.0)
    return lerp(SEABED, reef, smooth((sr - d) / 22.0))


def _land(x, y):
    """The ground under the slab (the slab is the rock: its own mesh): the districts'
    floors; elsewhere hidden in the rock. Off the edge: the abyss."""
    if y > rim_y(x):
        return SKY_FLOOR
    name, e = cavern_at(x, y)
    wob = 0.4 * math.sin(x / 7.0) * math.cos(y / 9.0)
    if name == "Fighting Pits":
        return pit_ground(x, y) + (0.2 * wob if pit_r(x, y) > PIT_R[0] else 0.0)
    if name == "Smugglers' Docks":
        bx, by, br = BASIN
        cy, hw, cx0, cx1 = CANAL
        d = min(math.hypot(x - bx, y - by) - br, abs(y - cy) - hw if cx0 - 2.0 < x < cx1 else 1e9)
        if d < 0.8:
            # (the quay's edge straight down into the black water)
            return lerp(DOCK_WATER - 5.0, DOCK_FLOOR, smooth((d + 0.2) / 1.0))
        return DOCK_FLOOR
    if name == "Rookery":
        rk = rook_at(x, y)
        rc = rook_canal(x, y)
        if rc is not None and rc[0] < ROOK_CANAL[1] + 0.6:
            # (the water street: its stone banks straight down into it)
            return lerp(ROOK_WATER - 3.0, rk[1] - 0.3, smooth((rc[0] - ROOK_CANAL[1] + 0.2) / 0.8))
        return rk[1] - 0.3
    if name == "Night Bazaar":
        return BAZ_FLOOR + 0.5 * smooth((e - 0.8) / 0.2) + 0.15 * wob
    if name == "Lucky Bone":
        return DEN_FLOOR + 0.8 * smooth((e - 0.75) / 0.25)
    if name == "Sea Door Grotto":
        return DEPTH - 0.6 + 1.4 * smooth((e - 0.55) / 0.45) + wob
    # (just past a cavern's edge, under its wall (which wobbles out up to 7%): the land
    # climbs steeply up into the rock, so there's no trench at the wall's foot to drop into
    # and slide under the floor by; Nov 4's bounds audit)
    if pit_r(x, y) < PIT_R[2] * 1.08:
        return PIT_RIM - 0.5 + 30.0 * smooth((pit_r(x, y) / PIT_R[2] - 1.0) / 0.05)
    for cname, cx, cy, rx, ry, floor, _h in CAVERNS:
        e = ellipse(x, y, cx, cy, rx, ry)
        if e < 1.16:
            return floor + 1.0 + 30.0 * smooth((e - 1.0) / 0.12)
    return -100.0


def natural(x, y):
    h = _land(x, y)
    d, z = road_floor(x, y)
    if y > rim_y(x) - 1.0:
        return h  # (the sky: open under the road)
    if in_water(x, y):
        return h  # (the canal, open under its bridge)
    w = flat_out(x, y)
    if cavern_at(x, y)[0] == "Night Bazaar" and z - BAZ_FLOOR > 1.2:
        # (the Gallery: up on its scaffold, the market's floor under it, eased up to the
        # road where it comes down to the floor)
        up = z - BAZ_FLOOR
        if d < w + 12.0:
            return lerp(z - 0.25, h, smooth((up - 1.2) / 1.6)) if up < 2.8 else h
        return h
    if d < w:
        return z - 0.25
    if d < w + 12.0:
        return lerp(z - 0.25, h, smooth((d - w) / 12.0))
    return h


def classify(c, n, info):
    """A terrain face's look and surface (c its middle, n its normal)."""
    if c.y > rim_y(c.x) - 1.0:
        return ("cloud_bank", "abyss")  # (off the edge of the world: put back)
    if in_water(c.x, c.y) and c.z < water_z(c.x, c.y) - 0.2:
        return ("bog_mud", "deep_water")  # (into the docks' black water: put back)
    name, e = cavern_at(c.x, c.y)
    if n.z < 0.62:
        # (the arena's walls dressed stone, like its stands)
        return ("sandstone_block", "wall") if name == "Fighting Pits" else ("cave_rock", "wall")
    muck = math.sin(c.x / 9.0 + c.y / 13.0) * math.cos(c.y / 7.0)
    if any(math.hypot(c.x - sx, c.y - sy) < sr + 6.0 for sx, sy, sr in SKYLIGHTS):
        return ("bog_mud", "dirt")  # (the floor under a skylight, sea-wet muck)
    if name == "Smugglers' Docks":
        return ("keep_dock", "dirt") if muck > -0.3 else ("bog_paving", "dirt")
    if name == "Rookery":
        return ("bog_paving", "dirt") if muck > -0.1 else ("bog_mud", "dirt")
    if name == "Night Bazaar":
        return ("village_cobble", "dirt") if muck > -0.2 else ("ash_soil", "dirt")
    if name == "Fighting Pits":
        if pit_r(c.x, c.y) < PIT_R[0] + 1.0:
            return ("gulch_sand", "dirt")  # (the arena's sand)
        return ("sandstone_block", "dirt") if muck > -0.4 else ("gulch_sand", "dirt")
    if name == "Lucky Bone":
        return ("keep_carpet", "dirt") if e < 0.7 else ("palace_paving", "dirt")
    if muck > 0.25:
        return ("bog_mud", "dirt")  # (trodden mud, oil, muck)
    return ("cave_rock", "dirt")


def isle_top(k):
    """Island k's grass: just under the lowest of the road over it."""
    name, ix, iy, r, z = ISLES[k]
    zs = [p[2] for p in DENSE[DAT[START]:DAT[END]] if math.hypot(p[0] - ix, p[1] - iy) < r - 1.0]
    return min(zs + [z]) - 0.9  # (under the banked road's low edge too)


def isle_at(x, y, margin=0.0):
    for k, (name, ix, iy, r, z) in enumerate(ISLES):
        if math.hypot(x - ix, y - iy) < r + margin:
            return k
    return None


if __name__ == "__main__":
    # (A quick check of the road without Blender: its length and grades.)
    a, b = DAT[START], DAT[END]
    L = CUM[b] - CUM[a]
    worst = 0.0
    for k in range(a, b):
        p, q = DENSE[k], DENSE[k + 1]
        h = math.hypot(q[0] - p[0], q[1] - p[1])
        if h > 0.5:
            worst = max(worst, abs(q[2] - p[2]) / h)
    print("road %.0f m, %d points, steepest %.0f%%" % (L, b - a, worst * 100))
    for name in ("dock0", "canal", "tav0", "portal", "baz0", "pit_gate", "pit12", "den0", "mouth", "end"):
        print(name, round(CUM[DAT[AT[name]]] - CUM[a]))
