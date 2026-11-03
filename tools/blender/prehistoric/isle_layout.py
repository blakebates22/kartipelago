# Tropic Isles v5: the island lived in, not driven round (Blake, Nov 1: "I like the
# geograhpy in general, but the driving is terribly boring, the sections with the levels
# are not immersive. the only immersive aspect is being on an island. i want to also
# travel through the island. not just around it. maybe we can have some figure 8 type
# loop going through the island ... homeomorphic to a figure 8"; "all of the areas
# containing the levels need to be their own sub world"). Pure geometry, no Blender
# (isle_region.py builds it).
# SPDX-License-Identifier: MIT
#
# The same island (v4's coast, bays, headlands, lagoon, the jungle peak and its falls), the
# road a figure eight through it: two loops crossing at the island's middle, where the
# Ridge Road goes over the river gorge on a high bridge and the Gorge Road runs along the
# river under it. Each part of the island its own basin, walled by jungle ridges, the road
# squeezing between them from one to the next:
#
#   Raptor's Bay        the stilt village (the island hop's pier in to its square, east)
#     the Head Pass     behind Tidewyrm's Head, down into
#   Coral Cove          its reef, its beach, its bay (Coral Cove's gateway)
#     the Ridge Road    up a jungle ravine onto the mountain's flank, over
#     the High Bridge   across the river gorge, the falls up it, the lagoon down it
#     the Cloud Forest  down through the mist, giant trees, to
#   Shipwreck Bay       the galleon, the pirates' camp (Shipwreck Bay's gateway)
#   Smugglers' Point    down the west coast: the smugglers' Sea Cave
#   the Lagoon          round its shore, mangroves; in at the river's mouth
#     the Gorge Road    up the river, under the High Bridge, to
#   the Jungle Heart    the falls (the road under their arc), the old temple, the
#                       rainforest's own course's gateway (Rainforest Rush)
#     the Temple Gate   bored through the ridge, out into
#   the North Valley    down to
#   the Black Shore     the north coast facing Volcano Isle: black sand, lava rock, steam
#                       (Volcano Isle's gateway); then round the north-east coast home
#
# Blender coordinates (x east, y north, z up).

import math

from pocket_kit import Layout, Notches, catmull, lerp, smooth, seg_d  # noqa: F401

EXTENT = 470.0
WATER_Z = 0.0
TOP = 52.0
PEAK = (10.0, 62.0)  # the pinnacle (north of the heart: its falls into it)
PEAK_R = 34.0
PEAK_Z = 205.0


def _adiff(a, b):
    return (a - b + math.pi) % math.tau - math.pi


# ---------------------------------------------------------------- the coast (v4's)

BAYS = {
    "village": (math.radians(4.0), 0.22, 46.0),
    "coral": (math.radians(-52.0), 0.2, 54.0),
    "wreck": (math.radians(140.0), 0.24, 64.0),
}
HEAD = (math.radians(-22.0), 0.14, 40.0)
HEAD_Z = 24.0
POINT = (math.radians(-172.0), 0.11, 34.0)
POINT_Z = 18.0


def _reach(a, head):
    ha, hhw, reach = head
    d = abs(_adiff(a, ha))
    return reach * (0.5 + 0.5 * math.cos(math.pi * d / hhw)) if d < hhw else 0.0


def shore_r(a, point=True):
    r = 352.0 + 22.0 * math.sin(3.0 * a + 0.7) + 12.0 * math.sin(5.0 * a + 2.0) + 6.0 * math.sin(9.0 * a + 1.1)
    for ang, hw, depth in BAYS.values():
        d = abs(_adiff(a, ang))
        if d < hw:
            r -= depth * (0.5 + 0.5 * math.cos(math.pi * d / hw))
    r += _reach(a, HEAD)
    if point:
        r += _reach(a, POINT)
    return r


def inland(x, y):
    """How far inland (x, y) is from the shore (negative: out to sea)."""
    return shore_r(math.atan2(y, x)) - math.hypot(x, y)


def _coast(a_deg, back=46.0, point=False):
    a = math.radians(a_deg)
    r = shore_r(a, point) - back
    return (r * math.cos(a), r * math.sin(a))


# The lagoon: still water behind the south-west shore, its inlet out to sea.
LAGOON = (-168.0, -150.0, 54.0)
LAGOON_INLET = [(-196.0, -178.0), (-262.0, -238.0)]
LAGOON_Z = -0.6
# The river: out of the falls' plunge pool, down its gorge to the lagoon (x, y, water z).
RIVER = [(8.0, -24.0, 9.4), (-18.0, -48.0, 8.0), (-48.0, -74.0, 6.2), (-80.0, -94.0, 4.2), (-110.0, -110.0, 2.2),
         (-140.0, -126.0, LAGOON_Z)]
RIVER_HW = 6.0
FALLS = (8.0, -24.0)  # the plunge pool's middle (the falls come off the pinnacle's south face)
FALLS_LIP = (8.0, 24.0)
POOL_R = 13.0


def river_d(x, y):
    best, tt, k = 1e9, 0.0, 0
    for i, (a, b) in enumerate(zip(RIVER, RIVER[1:])):
        d, t = seg_d(x, y, a, b)
        if d < best:
            best, tt, k = d, t, i
    return best, (k + tt) / (len(RIVER) - 1)


# ---------------------------------------------------------------- the basins

HUB = (252.0, 30.0, 20.0)  # Raptor's square (x, y, radius)
HOP_PIER = [(266.0, 30.0), (452.0, 26.0)]  # out east over the bay from the square to the island hop

POCKETS = [
    # Raptor's Bay: the village's flats above the east bay (the road on their inland side,
    # west of the square: the hop's pier goes out east, never across it).
    ("village", "village", [(214.0, 92.0, 26.0, 3.4), (214.0, 40.0, 30.0, 3.2), (250.0, 22.0, 30.0, 3.0),
                            (212.0, -18.0, 26.0, 3.4), (296.0, 30.0, 30.0, 2.4), (298.0, -14.0, 24.0, 2.6),
                            (290.0, 70.0, 24.0, 2.6)]),
    # The Head Pass: between Tidewyrm's Head and the mountain's spur.
    ("head", "head", [(212.0, -66.0, 16.0, 5.0), (212.0, -100.0, 16.0, 4.6)]),
    # Coral Cove: its bay's beach and flats.
    ("coral", "coral", [(206.0, -138.0, 22.0, 3.6), (172.0, -160.0, 30.0, 3.2), (130.0, -178.0, 28.0, 3.2),
                        (96.0, -176.0, 20.0, 4.2), (176.0, -194.0, 26.0, 2.4), (224.0, -186.0, 22.0, 2.6),
                        (140.0, -208.0, 24.0, 2.4)]),
    # The Ridge Road: up a jungle ravine onto the mountain's south flank.
    ("ridge", "ridge", [(66.0, -160.0, 15.0, 8.0), (36.0, -138.0, 14.0, 13.5), (8.0, -116.0, 14.0, 18.5),
                        (-20.0, -98.0, 14.0, 22.5), (-36.0, -87.0, 11.0, 16.8)]),
    # (the far side of the gorge: the Cloud Forest's top, the bridge between)
    ("cloud", "cloud", [(-80.0, -56.0, 14.0, 25.0), (-108.0, -34.0, 15.0, 23.5), (-140.0, -4.0, 16.0, 20.0),
                        (-164.0, 38.0, 17.0, 15.5), (-184.0, 86.0, 18.0, 10.0), (-124.0, -19.0, 13.0, 14.0),
                        (-131.0, -26.0, 15.0, 21.0), (-143.0, 22.0, 15.0, 17.0), (-183.0, 58.0, 15.0, 12.0),
                        (-153.0, 18.0, 13.0, 12.5), (-175.0, 62.0, 13.0, 11.0)]),
    # Shipwreck Bay.
    ("wreck", "wreck", [(-206.0, 132.0, 24.0, 4.0), (-238.0, 146.0, 28.0, 3.2), (-262.0, 106.0, 22.0, 3.2), (-232.0, 180.0, 28.0, 2.4), (-272.0, 150.0, 24.0, 2.6)]),
    # Smugglers' Point: down the west coast behind it.
    ("point", "point", [(-257.0, 78.0, 16.0, 3.4), (-286.0, 24.0, 16.0, 3.5), (-250.0, -30.0, 16.0, 3.4), (-270.0, 52.0, 20.0, 3.4), (-270.0, -4.0, 20.0, 3.6), (-260.0, -58.0, 24.0, 3.2), (-302.0, 62.0, 22.0, 2.6), (-292.0, -82.0, 22.0, 2.6)]),
    # The Lagoon: its north shore.
    ("lagoon", "lagoon", [(-236.0, -94.0, 20.0, 2.6), (-198.0, -84.0, 18.0, 2.4), (-158.0, -82.0, 18.0, 2.4),
                          (-168.0, -150.0, 50.0, -1.6)]),
    # The Gorge Road: up the river's north-west bank.
    ("gorge", "gorge", [(-122.0, -88.0, 15.0, 3.6), (-92.0, -74.0, 14.0, 5.6), (-64.0, -56.0, 14.0, 7.8),
                        (-38.0, -34.0, 15.0, 9.8), (-60.0, -78.0, 10.0, 5.0)]),
    # The Jungle Heart: the falls' basin under the pinnacle, the old temple.
    ("heart", "heart", [(-14.0, -10.0, 20.0, 11.6), (10.0, -14.0, 26.0, 11.6), (40.0, -14.0, 22.0, 12.0),
                        (64.0, -6.0, 16.0, 13.0)]),
    # The North Valley: out of the Temple Gate, down to the coast.
    # (v5c: wide open, a valley of meadows and groves, not a ravine: Blake, Nov 2)
    ("north", "north", [(84.0, 108.0, 24.0, 17.0), (64.0, 150.0, 34.0, 12.5), (36.0, 196.0, 34.0, 8.0),
                        (104.0, 152.0, 22.0, 13.0), (12.0, 166.0, 24.0, 10.5),
                        (84.0, 132.0, 18.0, 14.5), (31.0, 165.5, 18.0, 10.0), (38.0, 230.0, 16.0, 6.0)]),
    # The Black Shore: the north coast, facing Volcano Isle.
    ("volcano", "volcano", [(10.0, 246.0, 22.0, 4.0), (0.0, 280.0, 26.0, 3.0), (52.0, 282.0, 26.0, 3.0),
                            (100.0, 268.0, 24.0, 3.2), (2.0, 306.0, 26.0, 2.4), (46.0, 312.0, 24.0, 2.4),
                            (96.0, 300.0, 22.0, 2.5)]),
    # Round the north-east coast home.
    ("northeast", "northeast", [(180.0, 176.0, 16.0, 3.5), (215.0, 128.0, 16.0, 3.4), (148.0, 246.0, 22.0, 3.2), (182.0, 204.0, 22.0, 3.4), (200.0, 156.0, 22.0, 3.6), (162.0, 278.0, 22.0, 2.6), (214.0, 238.0, 22.0, 2.6)]),
]

# The route: the figure eight. (x, y, height or None: the land's, a tag naming the point.)
# (v6, Blake, Nov 2: "the driving of the figure 8 is horibly boring. lets make it mor hilly with
# zippers scattered throughout and some more turns, but still the figure 8 structure": S-bends
# through the Cloud Forest, down the Smugglers' coast, across the North Valley and round the
# north-east coast (the "(v6)" points); hills along the way, HILLS below; zippers, ZIPPER_EVERY.)
_ROUTE = [
    (204.0, 40.0, None, "start"),  # Raptor's Bay (the start line), south past the square
    (210.0, -14.0, None, None),
    (212.0, -64.0, None, "head"),  # the Head Pass
    (210.0, -102.0, None, None),
    (196.0, -138.0, None, "coral"),  # Coral Cove
    (162.0, -164.0, None, "coral_gate"),
    (124.0, -176.0, None, None),
    (94.0, -174.0, None, None),
    (66.0, -160.0, 8.6, "ridge"),  # the Ridge Road, up the ravine
    (36.0, -138.0, 13.0, None),
    (8.0, -116.0, 16.6, None),
    (-20.0, -98.0, 17.0, "br0"),
    (-52.0, -76.0, 17.4, None),  # the High Bridge, over the gorge
    (-80.0, -56.0, 16.8, "br1"),
    (-108.0, -34.0, 15.0, "cloud"),  # the Cloud Forest, down
    (-131.0, -26.0, 13.8, "cloud_s1"),  # (v6) an S-bend
    (-140.0, -4.0, 12.6, None),
    (-143.0, 22.0, None, "cloud_s2"),  # (v6) an S-bend
    (-164.0, 38.0, None, "cloud2"),
    (-183.0, 58.0, None, "cloud_s3"),  # (v6) an S-bend
    (-184.0, 86.0, None, None),
    (-208.0, 128.0, None, "wreck"),  # Shipwreck Bay
    (-240.0, 140.0, None, "wreck_gate"),
    (-264.0, 104.0, None, "point0"),
    (-257.0, 78.0, None, "point_s1"),  # (v6) an S-bend
    (-270.0, 52.0, None, "point"),  # Smugglers' Point
    (-286.0, 24.0, None, "point_s2"),  # (v6) an S-bend
    (-270.0, -4.0, None, "point2"),
    (-250.0, -30.0, None, "point_s3"),  # (v6) an S-bend
    (-260.0, -56.0, None, "cave"),
    (-236.0, -92.0, 3.4, "lagoon"),  # the Lagoon's north shore
    (-198.0, -84.0, 3.2, None),
    (-158.0, -82.0, 3.4, None),
    (-122.0, -88.0, 4.4, "gorge"),  # the Gorge Road, up the river
    (-92.0, -74.0, 6.4, None),
    (-64.0, -56.0, 8.6, None),  # under the High Bridge
    (-38.0, -34.0, 10.6, None),
    (-14.0, -10.0, None, "heart"),  # the Jungle Heart: under the falls' arc
    (10.0, -2.0, None, None),
    (40.0, -10.0, None, "rain_gate"),
    (64.0, -4.0, None, None),
    (80.0, 26.0, 15.0, "gate0"),  # the Temple Gate (bored through the ridge)
    (88.0, 66.0, 16.5, "gate1"),
    (84.0, 104.0, None, "north"),  # the North Valley
    (84.0, 132.0, None, "north_s1"),  # (v6) an S-bend
    (60.0, 150.0, None, "north2"),
    (31.0, 165.5, None, "north_s2"),  # (v6) an S-bend
    (34.0, 198.0, None, "north3"),
    (38.0, 230.0, None, "north_s3"),  # (v6) an S-bend
    (10.0, 246.0, None, "black"),  # the Black Shore
    (6.0, 280.0, None, "volcano_gate"),
    (52.0, 284.0, None, "secret"),
    (100.0, 270.0, None, None),
    (148.0, 246.0, None, "camp"),  # the north-east coast
    (182.0, 204.0, None, "ne2"),
    (180.0, 176.0, None, "ne_s1"),  # (v6) an S-bend
    (200.0, 156.0, None, "ne3"),
    (215.0, 128.0, None, "ne_s2"),  # (v6) an S-bend
    (210.0, 96.0, None, None),
]
ROUTE = [p[:3] for p in _ROUTE]
AT = {p[3]: i for i, p in enumerate(_ROUTE) if p[3]}
# The road the land is laid to (v6): the old smooth road through ROUTE (its heights the
# land's round each point, or set by hand), DENSE_PER points to a span, with the hills added
# on (the land has them too), so it rides over each crest.
DENSE_PER = 4
TUNNELS = [("Temple Gate", "temple", AT["gate0"], AT["gate1"])]
BRIDGE = (AT["br0"], AT["br1"])  # the High Bridge's route points (its deck)
CROSS = (-58.0, -66.0)  # where the figure eight crosses itself (the bridge over the gorge road)
BRIDGE_HALF = 28.0  # (the bridge's half length, round CROSS)

# The gateways' landmarks: (route point, along to the next, side +1 right/-1 left of the
# way of travel, how far from the road's middle). Each gateway stands at the end of a short
# path off the road (Blake, Nov 1: "never on the road intersecting, but off on the side of
# the road with a short path, a few meters to get to it").
GATE_AT = {
    "coral": (AT["coral_gate"], 0.5, -1, 30.0),  # on the cove's beach, the reef off it
    "wreck": (AT["wreck_gate"], 0.4, 1, 30.0),  # down Shipwreck Bay's beach toward the galleon
    "volcano": (AT["volcano_gate"], 0.6, -1, 30.0),  # on the Black Shore, toward Volcano Isle
    "rainforest": (AT["rain_gate"], 0.4, 1, 28.0),  # in the Jungle Heart, the temple's steps (south)
}
LAIR_AT = (AT["coral"], 0.3, -1, 34.0)  # Tidewyrm's sea cave, in the Head's south cliff
CAVE_AT = (AT["cave"], 0.5, 1, 40.0)  # the smugglers' Sea Cave's yard, under the Point
SECRET_AT = (AT["secret"], 0.5, -1, 30.0)  # the hidden cove behind the Black Shore


def _gate_xy(spec):
    i, f, side, dist = spec
    (ax, ay, _), (bx, by, _) = ROUTE[i], ROUTE[i + 1]
    x, y = lerp(ax, bx, f), lerp(ay, by, f)
    tx, ty = bx - ax, by - ay
    L_ = math.hypot(tx, ty)
    rx, ry = ty / L_, -tx / L_  # (right of the way of travel)
    return (x + rx * side * dist, y + ry * side * dist)


# The hills (v6): knolls and dunes the road rides over, crest after crest. (route point,
# along to the next, radius, height); none by the gateways, the bridge, the Temple Gate
# or the square.
HILLS_AT = [
    ("head", -0.35, 22.0, 3.5), ("head", 0.55, 18.0, 2.9),  # over the Head Pass's saddle
    ("coral_gate", 0.95, 14.0, 2.2),  # a dune on the cove's beach
    ("cloud_s2", 0.15, 16.0, 2.6), ("cloud2", 0.55, 16.0, 2.6), ("cloud_s3", 0.7, 15.0, 2.4),  # the Cloud Forest's knolls
    ("wreck", -0.35, 14.0, 2.2),  # a dune into Shipwreck Bay
    ("point_s1", 0.1, 18.0, 2.9), ("point", 0.55, 18.0, 2.9), ("point2", 0.4, 18.0, 2.9),  # the Smugglers' coast road
    ("north", 0.55, 20.0, 3.2), ("north2", 0.5, 20.0, 3.2), ("north3", 0.25, 20.0, 3.2),  # the North Valley's meadows
    ("black", 0.25, 14.0, 2.2),  # a black dune
    ("ne2", 0.4, 16.0, 2.6), ("ne3", 0.15, 16.0, 2.6), ("ne_s2", 0.6, 16.0, 2.6),  # the north-east coast's bluffs
]


def _hill_xy(tag, f):
    i = AT[tag]
    if f < 0:
        i, f = i - 1, 1.0 + f
    (ax, ay, _), (bx, by, _) = ROUTE[i], ROUTE[(i + 1) % len(ROUTE)]
    return lerp(ax, bx, f), lerp(ay, by, f)


HILLS = [_hill_xy(t, f) + (r, h) for t, f, r, h in HILLS_AT]


def _hills(x, y):
    h = 0.0
    for hx, hy, r, hh in HILLS:
        d = math.hypot(x - hx, y - hy)
        if d < r:
            h += hh * math.cos(math.pi * d / (2.0 * r)) ** 2
    return h


GATES = {k: _gate_xy(v) for k, v in GATE_AT.items()}
LAIR = _gate_xy(LAIR_AT)
CAVE = _gate_xy(CAVE_AT)
SECRET = _gate_xy(SECRET_AT)
VOLCANO = (250.0, 640.0)  # Volcano Isle, smoking offshore north
TEMPLE = (34.0, -40.0)  # the old temple, its steps up from the heart's floor (south side)


# ---------------------------------------------------------------- the land


def _spire(x, y):
    """The pinnacle: a green spire, sheer, its falls off the south face."""
    px, py = PEAK
    r = math.hypot(x - px, y - py)
    if r > PEAK_R + 26.0:
        return 0.0
    a = math.atan2(y - py, x - px)
    wob = 1.0 + 0.08 * math.sin(5.0 * a) + 0.05 * math.sin(11.0 * a + 1.0)
    return PEAK_Z * smooth((PEAK_R * wob + 10.0 - r) / 18.0) * (0.92 + 0.08 * math.sin(a * 3.0 + r / 9.0))


def _sea_cap(x, y, wallness):
    """The coast: the shallows and the deep out to sea; a beach up from the water; behind
    it the basins' floors, or (where a ridge comes down to the sea) a rocky bluff."""
    s = inland(x, y)
    if s < 0.0:
        h = WATER_Z - 0.35 + s * 0.045
        h = max(h, WATER_Z - 2.2 + s * 0.12)
        return max(h, -40.0)
    beach = WATER_Z - 0.3 + 2.6 * smooth(s / 30.0)
    return beach + max(0.0, s - 26.0) * lerp(0.06, 1.6, wallness)


class _IsleLayout(Layout):
    def natural(self, x, y):
        h = Layout.natural(self, x, y)
        best = self.wall_sd(x, y)
        # The pinnacle, over everything round it.
        h = max(h, _spire(x, y))
        # The coast cuts it all off: beaches into the coves, bluffs at the ridges' ends.
        h = min(h, _sea_cap(x, y, smooth((best + 2.0) / 18.0)))
        a = math.atan2(y, x)
        s = inland(x, y)
        # Tidewyrm's Head: the headland's top a grassy shelf, cliffs to the sea.
        ha, hhw, _ = HEAD
        d = abs(_adiff(a, ha))
        if d < hhw * 1.6 and s < 80.0 and best > 4.0:
            w = smooth((hhw * 1.4 - d) / (hhw * 0.6)) * smooth(s / 6.0) * smooth((best - 4.0) / 8.0)
            h = lerp(h, max(h, HEAD_Z + 3.0 * math.sin(x / 11.0)), w)
        # Smugglers' Point: the same, smaller.
        pa, phw, _ = POINT
        d = abs(_adiff(a, pa))
        if d < phw * 1.6 and best > 4.0:
            sb = shore_r(a, point=False) - math.hypot(x, y)
            w = smooth((phw * 1.4 - d) / (phw * 0.6)) * smooth(s / 5.0) * smooth((16.0 - sb) / 10.0) * smooth((best - 4.0) / 8.0)
            h = lerp(h, max(h, POINT_Z + 2.0 * math.sin(y / 9.0)), w)
        # The lagoon's inlet out to sea.
        di, _ = seg_d(x, y, *LAGOON_INLET)
        if di < 30.0:
            h = lerp(h, min(h, LAGOON_Z - 1.4), smooth((22.0 - di) / 10.0))
        # The falls' plunge pool.
        fx, fy = FALLS
        df = math.hypot(x - fx, y - fy)
        if df < POOL_R + 10.0:
            h = lerp(h, min(h, RIVER[0][2] - 1.6), smooth((POOL_R + 10.0 - df) / 10.0))
        # The hills (v6), inside the basins, up off the beaches.
        if _HILLS_ON and h > WATER_Z + 0.5:
            bump = _hills(x, y)
            if bump > 0.0:
                h += bump * smooth((-best - 2.0) / 10.0) * smooth((s - 8.0) / 12.0)
        # The gateways' ways in, level with the road.
        h = _NOTCHES.apply(h, x, y)
        return h


_HILLS_ON = False
L = _IsleLayout(POCKETS, TOP, ROUTE, TUNNELS, rivers=[RIVER], river_hw=RIVER_HW, roll=1.6, mountains=70.0,
                flat=("lagoon",), tiers=True)
_NOTCHES = Notches([], {})


def _init_notches():
    global _NOTCHES
    rp = L.route_points()
    _NOTCHES = Notches(rp, dict(GATES, lair=LAIR, cave=CAVE, secret=SECRET), reach=6.0, flat=7.0, blend=8.0)


_init_notches()
L._rp = None  # (the road's heights again, with the notches in)


def _hill_on(x, y):
    """How much of the hills the land (and so the road) has at (x, y)."""
    bump = _hills(x, y)
    if bump <= 0.0:
        return 0.0
    return bump * smooth((-L.wall_sd(x, y) - 2.0) / 10.0) * smooth((inland(x, y) - 8.0) / 12.0)


def _dense():
    rp = L.route_points()
    out = []
    for x, y, z in catmull(rp, DENSE_PER):
        out.append((round(x, 2), round(y, 2), round(z + _hill_on(x, y), 2)))
    return out


DENSE = _dense()
_HILLS_ON = True
TUNNELS = [(n, k, a * DENSE_PER, b * DENSE_PER) for n, k, a, b in TUNNELS]
L = _IsleLayout(POCKETS, TOP, DENSE, TUNNELS, rivers=[RIVER], river_hw=RIVER_HW, roll=1.6, mountains=70.0,
                flat=("lagoon",), tiers=True)


def natural(x, y):
    return L.natural(x, y)


def route_points():
    return L.route_points()


route_line = route_points
wall_sd = L.wall_sd
pocket_at = L.pocket_at
look_weights = L.look_weights


def look_at(x, y):
    return L.look_at(x, y)


def tunnel_floor(x, y):
    return L.tunnel_floor(x, y)


def is_bridge(x, y, z):
    """Over the gorge on the High Bridge (the land well below the road)."""
    return math.hypot(x - CROSS[0], y - CROSS[1]) < BRIDGE_HALF and z > 13.0
