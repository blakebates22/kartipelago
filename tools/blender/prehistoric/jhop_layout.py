# The Island Hop: the journey from Desert World down to the coast and over the sea to
# Tropic Isles (its own section between the two). Pure geometry (journey_region.py hop
# builds it, as the package journey_dust: the Dust Road's id).
# SPDX-License-Identifier: MIT
#
# v2, the Coast Road (Blake, Nov 1: "redo the island hop passage it is very boring. I want
# maybe only a couple islands, but before that we need to transistion from desert to
# coastline before going on the islands"; he chose the cliff version): the desert down to
# the sea a section at a time, then two islands, not eight.
#
#   the Last Dunes       out of the smugglers' tunnel into red dunes, bones bleaching,
#                        the wind; the sea not seen yet
#   the Salt Flats       a dried lagoon's white pan, the salt-rakers' village on its edge:
#                        flat and open, drifting turns
#     the Saddle         up over a ridge, and
#   the Cliff Road       the whole sea at once, the islands out on it; along the clifftops
#                        behind a dry stone wall, the lighthouse on the headland ahead
#     the Switchbacks    down the sea cliff's face
#   Shipwreck Cove       a beach, the first palms; the road through a wrecked ship's broken
#                        hull, the smugglers' boats pulled up on the sand
#     the Long Causeway  out over the shallows to
#   Fishers' Isle        hills, the stilt village round its lagoon, the bridge they rebuilt
#     the Rope Bridge    over the channel to
#   Turtle Isle          tall and green, a waterfall off its peak, the road under a great
#                        sea arch; the long pier on into Tropic Isles
#
# Blender coordinates (x east, y north, z up). The route is a loop; the road only from
# START to END (the rest goes round out of sight). The land's pocket_kit's basins (walls
# round low floors) on the west; the coast cuts them off, sheer cliffs to the sea but at
# the cove's beach; the islands rise out of the sea floor east of it.

import math

from pocket_kit import Layout, catmull, lerp, smooth  # noqa: F401

TOP = 74.0
HIDDEN_Z = 160.0
WATER_Z = -0.8
SEABED = -7.0
DECK = 2.6  # (the causeway and the pier, over the water)
ROPE = 3.6  # (the rope bridge, a little higher over the channel)

# The land's basins: (name, look, [(x, y, radius, floor)]).
LAND = [
    # The Last Dunes: out of the tunnel, winding north between the dunes.
    ("dunes", "dunes", [(-408, -398, 24, 50.2), (-372, -380, 30, 47.4), (-322, -372, 34, 47.0), (-286, -322, 32, 46.0),
                        (-300, -266, 26, 45.0)]),
    # The Salt Flats: down a neck into the dried lagoon's pan.
    ("salt", "salt", [(-318, -222, 16, 41.5), (-334, -186, 20, 38.0), (-348, -118, 66, 34.0), (-296, -64, 50, 34.0),
                      (-382, -50, 34, 34.2)]),
    # The Saddle: up out of the pan over the ridge (the sea hidden till its top).
    ("saddle", "saddle", [(-250, -40, 15, 36.5), (-228, -22, 15, 39.5), (-206, -6, 15, 40.5)]),
    # The Cliff Road: along the clifftops (the circles out past the coast, so no wall stands
    # between the road and the cliff's edge: a lip of rock, then the drop).
    ("cliff", "cliff", [(-180, 14, 20, 38.5), (-150, 46, 32, 38.0), (-148, 102, 32, 37.5), (-150, 156, 30, 37.0)]),
    # The Switchbacks: down the sea cliff's face, a circle a bend.
    ("stair", "stair", [(-124, 196, 15, 32.2), (-100, 216, 18, 29.2), (-126, 234, 15, 26.2), (-160, 238, 15, 22.7),
                        (-188, 254, 16, 19.2), (-166, 270, 15, 15.7), (-138, 272, 15, 12.2), (-97, 295, 18, 8.7),
                        (-126, 318, 15, 5.2)]),
    # Shipwreck Cove: the beach, facing the islands.
    ("cove", "cove", [(-138, 332, 22, 2.2), (-104, 350, 30, 1.8), (-66, 342, 26, 1.2)]),
]
# The islands: (name, look, [(x, y, radius, height)], how wide their shore slopes are (m)).
ISLANDS = [
    ("fishers", "fishers", [(92.0, 268.0, 40.0, 3.0), (136.0, 254.0, 34.0, 3.4), (88.0, 222.0, 28.0, 2.8),
                            (56.0, 252.0, 24.0, 2.6)], 10.0),
    ("turtle", "turtle", [(250.0, 246.0, 28.0, 4.0), (292.0, 268.0, 38.0, 5.0), (324.0, 238.0, 24.0, 4.0),
                          (282.0, 304.0, 34.0, 6.0)], 8.0),
]
POCKETS = LAND + [(name, look, circles) for name, look, circles, _w in ISLANDS]
# Fishers' Isle's hill (x, y, radius, height) and its lagoon (the sea let in, the village's
# stilts round it); Turtle Isle's peak, its falls coming down its south face to the pool.
HILL = (70.0, 222.0, 26.0, 7.0)
LAGOON = (108.0, 244.0, 14.0)
PEAK = (288.0, 312.0, 44.0, 46.0)
POOL = (294.0, 276.0, 7.0)
FALLS = (293.0, 288.0)  # (the lip's foot of the falls, on the peak's south face)

# The coast: land inside this outline, sea outside. Cliffs all along, but at the cove's beach.
COAST = [(-500.0, -500.0), (-20.0, -500.0), (-70.0, -280.0), (-104.0, -100.0), (-122.0, -20.0), (-122.0, 60.0),
         (-122.0, 172.0), (-96.0, 192.0), (-86.0, 214.0), (-88.0, 250.0), (-90.0, 282.0), (-86.0, 300.0),
         (-16.0, 312.0), (-10.0, 362.0), (-58.0, 384.0), (-110.0, 400.0), (-160.0, 440.0), (-220.0, 500.0),
         (-500.0, 500.0)]
BEACH = (-36.0, 348.0, 46.0)  # (where the coast is a beach, not a cliff: x, y, radius)
# (Far islands on the horizon, past the land's edge: dress_hop builds them as rock masses:
# the big island's jungle ahead (east), Volcano Isle smoking to the north.)
HORIZON = [(860.0, 360.0, 300.0, 240.0, 210.0, "jungle"), (700.0, 60.0, 120.0, 90.0, 60.0, "jungle"),
           (420.0, 860.0, 120.0, 110.0, 150.0, "volcano"), (40.0, 820.0, 90.0, 60.0, 40.0, "jungle"),
           (640.0, -520.0, 140.0, 90.0, 50.0, "jungle")]

ROUTE = [
    (-432.0, -428.0, 50.4),  # 0: lead-in (no road): the smugglers' tunnel, in the dunes' rock
    (-410.0, -402.0, None),  # 1: START, out of the tunnel's mouth into the Last Dunes
    (-376.0, -378.0, None),
    (-334.0, -384.0, None),
    (-296.0, -352.0, None),
    (-282.0, -306.0, None),
    (-302.0, -262.0, None),
    (-318.0, -222.0, None),  # 7: down the neck
    (-340.0, -180.0, None),  # 8: the Salt Flats
    (-372.0, -120.0, None),
    (-360.0, -64.0, None),
    (-318.0, -40.0, None),
    (-282.0, -66.0, None),
    (-250.0, -40.0, None),  # 13: up the Saddle
    (-228.0, -22.0, None),
    (-206.0, -6.0, None),  # 15: its top: the sea
    (-176.0, 18.0, None),  # 16: the Cliff Road
    (-150.0, 52.0, None),
    (-148.0, 102.0, None),
    (-150.0, 150.0, None),
    (-146.0, 186.0, 35.4),  # 20: down the Switchbacks
    (-124.0, 196.0, 32.4),
    (-100.0, 216.0, 29.4),
    (-126.0, 234.0, 26.4),
    (-160.0, 238.0, 22.9),
    (-188.0, 254.0, 19.4),
    (-166.0, 270.0, 15.9),
    (-138.0, 272.0, 12.4),
    (-97.0, 295.0, 8.9),
    (-126.0, 318.0, 5.4),
    (-140.0, 342.0, None),  # 30: Shipwreck Cove
    (-110.0, 357.0, None),
    (-80.0, 348.0, None),  # 32: through the wreck
    (-48.0, 336.0, None),
    (-14.0, 318.0, DECK),  # 34: the Long Causeway
    (24.0, 296.0, DECK),
    (60.0, 270.0, None),  # 36: Fishers' Isle
    (98.0, 290.0, None),
    (136.0, 272.0, None),
    (164.0, 252.0, None),
    (194.0, 248.0, ROPE),  # 40: the Rope Bridge
    (230.0, 246.0, None),  # 41: Turtle Isle
    (254.0, 248.0, None),  # 42: under the sea arch
    (290.0, 258.0, None),  # 43: by the falls' pool
    (326.0, 248.0, None),
    (360.0, 252.0, DECK),  # 45: the long pier
    (396.0, 258.0, DECK),
    (430.0, 262.0, DECK),  # 47: END, on into Tropic Isles
    (466.0, 266.0, DECK),  # 48: lead-out (no road)
    (484.0, 380.0, HIDDEN_Z),
    (300.0, 486.0, HIDDEN_Z),
    (-100.0, 486.0, HIDDEN_Z),
    (-486.0, 300.0, HIDDEN_Z),
    (-486.0, 0.0, HIDDEN_Z),
    (-486.0, -300.0, HIDDEN_Z),
    (-474.0, -474.0, HIDDEN_Z),
]
# (The Switchbacks' heights set by the way along them: an even grade, hairpins and all.)
# (Its hairpins nearly level, so the bends aren't steep where the road turns on itself.)
STAIR = (20, 29, 36.0, 5.0)
HAIRPINS = (22, 25, 28)


def _stair():
    a, b, z0, z1 = STAIR
    ds = [0.0]
    for i in range(a, b):
        w = 0.4 if i in HAIRPINS or i + 1 in HAIRPINS else 1.0
        ds.append(ds[-1] + w * math.hypot(ROUTE[i + 1][0] - ROUTE[i][0], ROUTE[i + 1][1] - ROUTE[i][1]))
    for k, i in enumerate(range(a, b + 1)):
        ROUTE[i] = (ROUTE[i][0], ROUTE[i][1], round(lerp(z0, z1, ds[k] / ds[-1]), 2))


_stair()
START, END = 1, 47
HIDDEN = range(END + 2, len(ROUTE))
TUNNELS = []
# The stretches over the water and what's built for them: (first route point, last, kind).
BRIDGES = [(33, 36, "causeway"), (39, 41, "rope"), (44, 48, "pier")]
WRECK = (31, 33)  # (the road through the wreck's hull: route points)
RIVERS = []
RIVER_HW = 9.0
LAKES = []
POOLS = []
LAVA = []

ENDS = {"start": ((-410.0, -402.0), (-432.0, -428.0)), "end": ((430.0, 262.0), (466.0, 266.0))}
END_WALLS = ("start",)  # (the end's the pier going on: no wall)
GATES = {}
# Landmarks.
LIGHTHOUSE = (-130.0, 176.0)  # on the clifftop, at the Switchbacks' head
SALT_VILLAGE = (-388.0, -134.0, 18.0)  # the salt-rakers' (x, y, r)
DUNE_CAMP = (-332.0, -330.0)  # bones in the dunes
ARCH = (254.0, 248.0)  # the sea arch over the road


def _poly_inland(x, y):
    """Signed distance into the land from the coast (> 0 on land)."""
    inside = False
    best = 1e9
    n = len(COAST)
    for i in range(n):
        ax, ay = COAST[i]
        bx, by = COAST[(i + 1) % n]
        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
            inside = not inside
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(x - ax - dx * t, y - ay - dy * t))
    return best if inside else -best


def inland(x, y):
    # (the coast's line wobbling a little, so the cliffs aren't ruled straight)
    return _poly_inland(x, y) + 3.0 * math.sin(y / 17.0 + 0.3) * math.cos(x / 23.0)


def beach_w(x, y):
    bx, by, br = BEACH
    return 1.0 - smooth((math.hypot(x - bx, y - by) - br) / 30.0)


def _sea_cap(x, y):
    """The coast's profile: the sea floor out at sea; at the coast a sheer cliff, or (at the
    cove) a beach shelving gently into the sea."""
    d = inland(x, y)
    if d <= 0.0:
        return SEABED - min(4.0, -d * 0.02)
    bw = beach_w(x, y)
    return SEABED + d * lerp(7.0, 0.3, bw)


def _island_h(x, y):
    """The islands rising out of the sea floor (their shores sloping as wide as their kind's),
    Fishers' Isle's hill and lagoon, Turtle Isle's peak and its pool."""
    h = -1e9
    for _name, _look, circles, w in ISLANDS:
        for cx, cy, r, top in circles:
            d = math.hypot(x - cx, y - cy) - r
            h = max(h, lerp(top, SEABED, smooth((d + w * 0.5) / w)))
    hx, hy, hr, hh = HILL
    d = math.hypot(x - hx, y - hy)
    if d < hr and h > 0:
        h += hh * smooth(1.0 - d / hr) * (0.85 + 0.15 * math.sin(x / 7.0) * math.cos(y / 9.0))
    px, py, pr, ph = PEAK
    d = math.hypot(x - px, y - py)
    if d < pr and h > 0:
        k = 1.0 - d / pr
        h += ph * (k ** 1.4) * (0.85 + 0.15 * math.sin(x / 6.0 + y / 9.0))
    lx, ly, lr = LAGOON
    d = math.hypot(x - lx, y - ly)
    if d < lr + 8.0:
        h = lerp(min(h, WATER_Z - 1.6), h, smooth((d - lr) / 8.0))
    ox, oy, orr = POOL
    d = math.hypot(x - ox, y - oy)
    if d < orr + 5.0:
        h = lerp(min(h, WATER_Z + 1.8), h, smooth((d - orr) / 5.0))
    return h


def _dunes(h, x, y, w):
    """The dunes' swells (crescent ridges across the wind), on the dunes' floor."""
    if w < 0.05:
        return h
    a = x * 0.8 + y * 0.6
    b = -x * 0.6 + y * 0.8
    ridge = (0.5 + 0.5 * math.sin(a / 21.0 + 1.3 * math.sin(b / 37.0))) ** 2
    return h + w * (3.2 * ridge + 1.2 * math.sin(b / 13.0) * math.cos(a / 17.0))


def _stair_slope(h, x, y):
    """The Switchbacks' hillside: the cliff's face here one long slope down to the cove (not
    walls between the bends), the road's terraces cut into it."""
    w = smooth((x + 215.0) / 20.0) * smooth((y - 172.0) / 14.0) * smooth((334.0 - y) / 16.0)
    if w <= 0.0:
        return h
    slope = 36.0 - 0.25 * (y - 186.0) + 1.5 * math.sin(x / 13.0) * math.cos(y / 11.0) + 0.06 * max(0.0, -150.0 - x)
    return lerp(h, min(h, slope), w)


class _CoastLayout(Layout):
    def natural(self, x, y):
        h = Layout.natural(self, x, y)
        lw = self.look_weights(x, y)
        # (no swells by the tunnel's mouth: you come out onto level sand, not rolling back)
        calm = smooth((math.hypot(x - ROUTE[START][0], y - ROUTE[START][1]) - 26.0) / 30.0)
        h = _dunes(h, x, y, lw.get("dunes", 0.0) * (1.0 - smooth((self.wall_sd(x, y) + 4.0) / 10.0)) * calm)
        h = _stair_slope(h, x, y)
        h = min(h, _sea_cap(x, y))
        return max(h, _island_h(x, y))


L = _CoastLayout(POCKETS, TOP, ROUTE, TUNNELS, roll=2.0, mountains=40.0, hidden=HIDDEN, flat=("salt", "cove"))


def natural(x, y):
    return L.natural(x, y)


def bridge_kind(x, y):
    """Which of BRIDGES the road over the water near (x, y) is (the nearest route stretch)."""
    best, kind = 1e9, "pier"
    for a, b, k in BRIDGES:
        for i in range(a, b):
            (ax, ay, _), (bx, by, _) = ROUTE[i], ROUTE[i + 1]
            dx, dy = bx - ax, by - ay
            t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
            d = math.hypot(x - ax - dx * t, y - ay - dy * t)
            if d < best:
                best, kind = d, k
    return kind


route_points = L.route_points
wall_sd = L.wall_sd
pocket_at = L.pocket_at
lobe_weights = L.look_weights
look_at = L.look_at
tunnel_floor = L.tunnel_floor


def river_d(x, y):
    return 1e9, 0.0
