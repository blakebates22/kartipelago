# The Island Hop: the journey from Desert World over the sea to Tropic Isles (its own
# section between the two; Blake, Nov 1: "now back to the islands that connect desert to
# tropics. Let's build it"; claude/tropic-isles-v4-vision.md). Pure geometry
# (journey_region.py hop builds it, as the package journey_dust: the Dust Road's id).
# SPDX-License-Identifier: MIT
#
# Out of the desert's smugglers' tunnel at the foot of a red headland, and island to
# island east over the sea:
#
#   the Dock          a smugglers' timber dock along the headland's foot, out of the tunnel
#   Sandbar Key       a low tide sandbar, driftwood, gulls
#     the Causeway    an old stone causeway over the shallows
#   Mangrove Cay      the road through the mangroves on their roots
#     the Rope Bridge over the channel to Fishers' Isle
#   Fishers' Isle     the stilt fishing village round its lagoon; the bridge it rebuilt
#                     (the broken bridge, mended: the mission's for later)
#   Turtle Rocks      sea stacks, rope bridges from rock to rock, the great turtle rock
#   Palm Cay          palms, the last pier, the big island's peak ahead; the long pier on
#                     into Tropic Isles
#
# Blender coordinates (x east, y north, z up). The route is a loop; the road only from
# START to END (the rest goes round out of sight). The land isn't pocket_kit's basins
# (that's walls round low floors): here the islands rise out of the sea floor, so the
# Layout's natural() is our own.

import math

from pocket_kit import Layout, catmull, lerp, smooth  # noqa: F401

TOP = 30.0
HIDDEN_Z = 150.0
WATER_Z = -0.8
SEABED = -7.0
DECK = 2.6  # (the docks, piers and the causeway, over the water)
ROPE = 3.4  # (the rope bridges, a little higher over the channels)

# The islands: (name, look, [(x, y, radius, height)], how wide their shore slopes are (m)).
ISLANDS = [
    ("cliffs", "cliffs", [(-470.0, -360.0, 46.0, 34.0), (-450.0, -300.0, 34.0, 30.0), (-455.0, -415.0, 34.0, 28.0)], 5.0),
    ("dock", "dock", [(-408.0, -318.0, 12.0, 1.2)], 6.0),
    ("sandbar", "sandbar", [(-300.0, -294.0, 24.0, 0.5), (-250.0, -282.0, 26.0, 0.6), (-200.0, -268.0, 22.0, 0.5),
                            (-226.0, -300.0, 14.0, 0.3)], 14.0),
    ("mangrove", "mangrove", [(-52.0, -124.0, 30.0, 1.3), (-22.0, -82.0, 32.0, 1.5), (-38.0, -40.0, 24.0, 1.3),
                              (-80.0, -92.0, 18.0, 1.0)], 10.0),
    ("fishers", "fishers", [(58.0, 38.0, 34.0, 2.4), (106.0, 66.0, 30.0, 2.6), (74.0, 96.0, 22.0, 2.4),
                            (126.0, 104.0, 18.0, 2.4)], 9.0),
    ("rocks", "rocks", [(214.0, 186.0, 15.0, 6.0), (266.0, 216.0, 15.0, 6.5)], 4.0),
    ("palm", "palm", [(330.0, 272.0, 30.0, 2.0), (370.0, 292.0, 26.0, 2.0), (342.0, 240.0, 16.0, 1.6)], 12.0),
]
POCKETS = [(name, look, circles) for name, look, circles, _w in ISLANDS]
# (The lagoon in Fishers' Isle: the village's stilts stand round it.)
LAGOON = (92.0, 78.0, 16.0)
# Far islands on the horizon (out past the land's edge, built as rock: journey_region's
# dress_hop): the big island's jungle peak ahead (east), Volcano Isle smoking to the north,
# the desert's red cliffs falling away behind (west). (x, y, rx, ry, height, kind)
HORIZON = [(820.0, 470.0, 300.0, 240.0, 210.0, "jungle"), (700.0, 210.0, 120.0, 90.0, 60.0, "jungle"),
           (380.0, 860.0, 120.0, 110.0, 150.0, "volcano"), (-160.0, 820.0, 90.0, 60.0, 40.0, "jungle"),
           (-820.0, -200.0, 260.0, 340.0, 90.0, "desert"), (120.0, -800.0, 110.0, 70.0, 34.0, "jungle")]

ROUTE = [
    (-430.0, -330.0, 1.2),  # 0: lead-in (no road): the smugglers' tunnel, in the headland
    (-402.0, -318.0, None),  # 1: START, out of the tunnel's mouth onto the dock
    (-366.0, -306.0, DECK),  # 2: the Dock
    (-330.0, -298.0, DECK),
    (-296.0, -294.0, None),  # 4: Sandbar Key
    (-250.0, -282.0, None),
    (-202.0, -268.0, None),
    (-160.0, -244.0, DECK),  # 7: the Causeway
    (-120.0, -206.0, DECK),
    (-88.0, -166.0, DECK),
    (-54.0, -124.0, None),  # 10: Mangrove Cay
    (-24.0, -84.0, None),
    (-14.0, -42.0, None),
    (10.0, -4.0, ROPE),  # 13: the Rope Bridge
    (36.0, 24.0, None),  # 14: Fishers' Isle
    (62.0, 44.0, None),
    (104.0, 58.0, None),
    (130.0, 100.0, None),
    (156.0, 130.0, DECK),  # 18: Fishers' Bridge (rebuilt)
    (184.0, 158.0, DECK),
    (214.0, 186.0, None),  # 20: Turtle Rocks
    (240.0, 202.0, 6.6),  # 21: the rope bridge from rock to rock
    (266.0, 216.0, None),
    (298.0, 244.0, ROPE),  # 23: down onto Palm Cay
    (330.0, 268.0, None),  # 24: Palm Cay
    (370.0, 290.0, None),
    (404.0, 302.0, DECK),  # 26: the long pier
    (440.0, 314.0, DECK),  # 27: END, on into Tropic Isles
    (476.0, 326.0, DECK),  # 28: lead-out (no road)
    (486.0, 420.0, HIDDEN_Z),
    (300.0, 484.0, HIDDEN_Z),
    (-100.0, 486.0, HIDDEN_Z),
    (-484.0, 300.0, HIDDEN_Z),
    (-486.0, 0.0, HIDDEN_Z),
    (-486.0, -250.0, HIDDEN_Z),
    (-470.0, -470.0, HIDDEN_Z),
]
START, END = 1, 27
HIDDEN = range(END + 2, len(ROUTE))
TUNNELS = []
# The stretches over the water and what's built for them: (first route point, last, kind).
BRIDGES = [(1, 4, "dock"), (6, 10, "causeway"), (12, 14, "rope"), (17, 20, "mended"), (20, 22, "rope"), (22, 24, "rope"),
           (25, 28, "pier")]
RIVERS = []
RIVER_HW = 9.0
LAKES = []
POOLS = []
LAVA = []

ENDS = {"start": ((-402.0, -318.0), (-430.0, -330.0)), "end": ((440.0, 314.0), (476.0, 326.0))}
GATES = {}


def _island_h(x, y):
    """The land: the sea floor, and each island rising out of it (its shore a slope as wide
    as its kind's), the highest of them where they meet."""
    h = SEABED
    best = 1e9
    for _name, _look, circles, w in ISLANDS:
        for cx, cy, r, top in circles:
            d = math.hypot(x - cx, y - cy) - r
            best = min(best, d)
            hi = lerp(top, SEABED, smooth((d + w * 0.5) / w))
            h = max(h, hi)
    # (Fishers' Isle's lagoon, the sea let in through a gap in its south shore.)
    lx, ly, lr = LAGOON
    d = math.hypot(x - lx, y - ly)
    if d < lr + 8.0:
        h = lerp(min(h, WATER_Z - 1.6), h, smooth((d - lr) / 8.0))
    return h, best


class _HopLayout(Layout):
    def natural(self, x, y):
        h, best = _island_h(x, y)
        if h > WATER_Z + 0.5:
            # (a little roll on the land: dunes on the sandbar, hummocks elsewhere)
            h += 0.5 * math.sin(x / 13.0 + 0.4) * math.cos(y / 17.0) * smooth((h - WATER_Z) / 3.0)
        return h


L = _HopLayout(POCKETS, TOP, ROUTE, TUNNELS, roll=0.0, mountains=0.0, hidden=HIDDEN)


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
