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
#                         moored ships, a jump over the canal, out past the warehouses;
#   Smugglers' Alley      S-bends down a crooked bore to the Drop: off a ledge, over a
#                         crack, down into
#   the Night Bazaar      a slalom through the lantern-lit market lanes, the Broker's ship
#                         hanging over it all, to the gate of
#   the Fighting Pits     the arena: the road corkscrews down its wall through the stands,
#                         the crowd on every side, the fight ring on its floor; out through
#   the Lucky Bone        the gambling den, then the Long Bore climbing to the cliff of
#   the Edge              the world's edge, and a leap off it to
#   the Sky Islands       island hopping (Blake chose "Sky-island hopping"): floating rocks
#                         joined by chained bridges and jumps, dragons flying, up to
#   the Sky Gate          the Dragon Kingdom's gate: the loading zone.
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
CANAL = (-300.0, 3.5, -26.0, 50.0)  # y, half width, from x, to x (under the jump)
BAZAAR = (108.0, -140.0, 46.0, 66.0)
BAZ_Z = -33.0
BAZ_FLOOR = BAZ_Z - 0.6
PIT = (40.0, -10.0)
PIT_R = (34.0, 66.0, 82.0)  # the floor's edge, the stands' top, the wall
PIT_RIM = -34.0
PIT_FLOOR = -61.5
DEN = (152.0, 36.0, 30.0, 26.0)
DEN_Z = -57.0
DEN_FLOOR = DEN_Z - 0.6
MOUTH = (24.0, 182.0)  # where the Long Bore comes out of the world's edge


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
    (-3.0, -318.0, DOCK_Z, "runup1"),
    (-3.0, -305.5, DOCK_Z, "lip1"),
    (-3.0, -294.5, DOCK_Z - 1.2, "land1"),
    (-1.0, -281.0, DOCK_Z - 1.2, "dock1"),
    (16.0, -262.0, DOCK_Z - 1.4, "dock2"),
    (36.0, -252.0, DOCK_Z - 1.6, "dock3"),
    # Smugglers' Alley: S-bends down to the Drop.
    (58.0, -248.0, -26.0, "alley0"),
    (70.0, -239.0, -26.5, "alley1"),
    (75.2, -221.0, -27.4, "alley2"),
    (76.2, -206.9, -28.0, "runup2"),
    (78.0, -194.0, -28.0, "lip2"),
    (79.3, -185.6, BAZ_Z, "land2"),
    # The Night Bazaar: a slalom through the lanes.
    (89.0, -172.0, BAZ_Z, "baz0"),
    (103.0, -154.0, BAZ_Z, "baz1"),
    (110.0, -132.0, BAZ_Z, "baz2"),
    (108.0, -114.0, BAZ_Z, "baz3"),
    (104.0, -92.0, BAZ_Z, "baz4"),
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
    (28.0, 160.0, -42.6, "bore7"),
    (24.0, 171.0, -42.0, "runup3"),
    (24.0, 184.0, -42.0, "lip3"),  # off the edge of the world
    (24.0, 196.0, -45.0, "land3"),
    # The Sky Islands.
    (22.0, 211.0, -45.0, "isle1"),
    (6.0, 226.0, -45.0, "isle1b"),
    (-10.0, 238.0, -43.4, "bridge1a"),
    (-28.0, 256.0, -40.4, "bridge1b"),
    (-36.0, 272.0, -40.0, "isle2"),
    (-36.5, 285.0, -40.0, "runup4"),
    (-35.0, 297.5, -40.0, "lip4"),
    (-33.4, 310.0, -41.5, "land4"),
    (-30.0, 322.0, -41.5, "land4b"),
    (-20.0, 334.0, -41.5, "isle3"),
    (-10.0, 348.0, -41.5, "isle3c"),
    (2.0, 362.0, -39.8, "bridge2a"),
    (14.0, 378.0, -37.6, "bridge2b"),
    (16.0, 392.0, -37.0, "runup5"),
    (16.0, 404.0, -37.0, "lip5"),
    (16.0, 416.0, -38.5, "land5"),
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

# The jumps: (lip, landing, the kicker's lift (m), what's under it).
JUMPS = [
    ("lip1", "land1", 0.8, "canal"),  # over the docks' canal
    ("lip2", "land2", 0.5, "crack"),  # the Drop, over a crack into the Night Bazaar
    ("lip3", "land3", 0.8, "sky"),  # off the edge of the world
    ("lip4", "land4", 1.0, "sky"),
    ("lip5", "land5", 1.0, "sky"),
]
RUN_UP = 14.0

# The sky islands: (name, x, y, radius, the road's height on it).
ISLES = [
    ("Landing Rock", 18.0, 212.0, 21.0, -45.0),
    ("Dragon's Perch", -38.0, 280.0, 18.0, -40.0),
    ("Shrine Isle", -26.0, 326.0, 25.0, -41.5),
    ("Gatekeeper's Rock", 16.0, 392.0, 12.0, -37.0),
    ("Sky Gate Isle", 8.0, 434.0, 24.0, -38.5),
]

# The underground's caverns, cut out of the seabed's rock: (name, x, y, rx, ry, floor,
# roof over the floor). The Fighting Pits are a drum of their own (jedge_region.py).
CAVERNS = [
    ("Sea Door Grotto", GROTTO[0], GROTTO[1], GROTTO[2], GROTTO[3], DEPTH - 0.6, 31.0),
    ("Smugglers' Docks", DOCKS[0], DOCKS[1], DOCKS[2], DOCKS[3], DOCK_FLOOR, 19.0),
    ("Night Bazaar", BAZAAR[0], BAZAAR[1], BAZAAR[2], BAZAAR[3], BAZ_FLOOR, 27.0),
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
    ROUTE, each jump cut in: a level run up to its lip (the kicker lifts its last metres),
    the straight flight line over the gap (no road there), the land beyond. Returns the
    points and the dense index of each ROUTE point."""
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
    for lip, land, _, _ in JUMPS:
        i, j = at[AT[lip]], at[AT[land]]
        zl, zd = ROUTE[AT[lip]][2], ROUTE[AT[land]][2]
        for k in range(len(pts)):
            d = cum[k]
            if cum[i] - RUN_UP - 10.0 <= d < cum[i] - RUN_UP:
                pts[k][2] = lerp(pts[k][2], zl, smooth((d - (cum[i] - RUN_UP - 10.0)) / 10.0))
            elif cum[i] - RUN_UP <= d <= cum[i]:
                pts[k][2] = zl
            elif cum[i] < d <= cum[j]:
                pts[k][2] = lerp(zl, zd, (d - cum[i]) / (cum[j] - cum[i]))
    return [(round(x, 2), round(y, 2), round(z, 2)) for x, y, z in pts], at, cum


DENSE, DAT, CUM = _dense()
GAPS = [(DAT[AT[lip]], DAT[AT[land]], under) for lip, land, _, under in JUMPS]


# Each jump's gap as a box on the ground: from its lip's line to its landing's, so far
# either side (what's under it: the canal's water, the crack, the sky).
GAP_BOXES = [(ROUTE[AT[lip]][:2], ROUTE[AT[land]][:2], under) for lip, land, _, under in JUMPS]


def gap_box(x, y, side=16.0):
    """The jump whose gap (x, y) is over, if any (None)."""
    for (ax, ay), (bx, by), under in GAP_BOXES:
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy)
        t = ((x - ax) * dx + (y - ay) * dy) / (L * L)
        if 0.0 < t < 1.0 and abs((x - ax) * dy - (y - ay) * dx) / L < side:
            return under
    return None


def _gap_of(k):
    for i, j, under in GAPS:
        if i <= k < j:
            return under
    return None


def _seg(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / L2))
    return math.hypot(px - a[0] - t * dx, py - a[1] - t * dy), t


_GRID = {}
for _k in range(DAT[START] - 8, DAT[END] + 10):
    _a, _b = DENSE[_k], DENSE[_k + 1]
    _g = _gap_of(_k)
    for _gx in range(int(math.floor(min(_a[0], _b[0]) / 24)) - 1, int(math.floor(max(_a[0], _b[0]) / 24)) + 2):
        for _gy in range(int(math.floor(min(_a[1], _b[1]) / 24)) - 1, int(math.floor(max(_a[1], _b[1]) / 24)) + 2):
            _GRID.setdefault((_gx, _gy), []).append((_a, _b, _g))


def road_floor(x, y):
    """How far (x, y) is from the road, the road's height there, and what's under it if
    that's a jump's gap (None: road)."""
    best = (1e9, 0.0, None)
    for a, b, g in _GRID.get((int(math.floor(x / 24)), int(math.floor(y / 24))), ()):
        d, t = _seg(x, y, a, b)
        if d < best[0]:
            best = (d, lerp(a[2], b[2], t), g)
    return best


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
    return abs(y - cy) < hw and cx0 - 2.0 < x < cx1 and ellipse(x, y, *DOCKS) < 0.98


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
        if d < 3.0:
            return lerp(DOCK_WATER - 5.0, DOCK_FLOOR, smooth((d + 1.0) / 4.0))
        return DOCK_FLOOR
    if name == "Night Bazaar":
        return BAZ_FLOOR + 0.5 * smooth((e - 0.8) / 0.2) + 0.15 * wob
    if name == "Lucky Bone":
        return DEN_FLOOR + 0.8 * smooth((e - 0.75) / 0.25)
    if name == "Sea Door Grotto":
        return DEPTH - 0.6 + 1.4 * smooth((e - 0.55) / 0.45) + wob
    return -100.0


def natural(x, y):
    h = _land(x, y)
    d, z, gap = road_floor(x, y)
    if y > rim_y(x) - 1.0:
        return h  # (the sky: open under the road)
    if gap is not None and d < 16.0:
        # (a jump's gap: what's under it: the canal's water, the Drop's crack)
        under = gap_box(x, y)
        if under == "canal":
            return h
        if under == "crack":
            return z - 26.0
    if d < 8.0:
        return z - 0.25
    if d < 20.0:
        return lerp(z - 0.25, h, smooth((d - 8.0) / 12.0))
    return h


def classify(c, n, info):
    """A terrain face's look and surface (c its middle, n its normal)."""
    if c.y > rim_y(c.x) - 1.0:
        return ("cloud_bank", "abyss")  # (off the edge of the world: put back)
    d, z, gap = road_floor(c.x, c.y)
    if gap_box(c.x, c.y, 17.0) == "crack" and c.z < z - 4.0:
        return ("abyss_fog", "abyss")  # (down the Drop's crack: put back)
    if in_water(c.x, c.y) and c.z < DOCK_WATER - 0.2:
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
    zs = [p[2] for j, p in enumerate(DENSE[DAT[START]:DAT[END]]) if math.hypot(p[0] - ix, p[1] - iy) < r + 3.0
          and _gap_of(j + DAT[START]) is None]
    return min(zs + [z]) - 0.3


def isle_at(x, y, margin=0.0):
    for k, (name, ix, iy, r, z) in enumerate(ISLES):
        if math.hypot(x - ix, y - iy) < r + margin:
            return k
    return None


if __name__ == "__main__":
    # (A quick check of the road without Blender: its length, the grades, the jumps.)
    a, b = DAT[START], DAT[END]
    L = CUM[b] - CUM[a]
    worst = 0.0
    for k in range(a, b):
        if _gap_of(k):
            continue
        p, q = DENSE[k], DENSE[k + 1]
        h = math.hypot(q[0] - p[0], q[1] - p[1])
        if h > 0.5:
            worst = max(worst, abs(q[2] - p[2]) / h)
    print("road %.0f m, %d points, steepest %.0f%%" % (L, b - a, worst * 100))
    for lip, land, kick, under in JUMPS:
        i, j = DAT[AT[lip]], DAT[AT[land]]
        print("jump %s: gap %.1f m, drop %.1f m, %s" % (lip, CUM[j] - CUM[i], DENSE[i][2] - DENSE[j][2], under))
    for name in ("dock0", "land2", "pit_gate", "pit12", "den0", "lip3", "end"):
        print(name, round(CUM[DAT[AT[name]]] - CUM[a]))
