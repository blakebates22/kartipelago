# The Dust Road: the journey from Desert World down to Tropic Isles (its own section
# between the two). Pure geometry (journey_region.py builds it).
# SPDX-License-Identifier: MIT
#
# Out of the sand into the jungle:
#
#   the Dunes          the road threading the troughs between great dunes
#     the Mesa Tunnel  bored through a red mesa
#   the Scrub          dry grassland, thorn trees, a dry wash, the first green
#   the Ford           a jungle river, a timber bridge over it, palms
#     the Vine Gorge   a tunnel of roots and vines
#   the Jungle         dense jungle, down to the gate into Tropic Isles
#
# Blender coordinates (x east, y north, z up). The route is a loop; the road only from
# START to END (the rest is out of sight over the mountains).

from pocket_kit import Layout, catmull, lerp, smooth  # noqa: F401

TOP = 70.0
HIDDEN_Z = 170.0

POCKETS = [
    ("dunes", "dunes", [(-408, -60, 18, 10.0), (-370, -50, 32, 10.0), (-310, -90, 34, 11.0), (-250, -48, 32, 12.0),
                        (-198, -102, 30, 12.5), (-280, -70, 22, 10.5)]),
    ("scrub", "scrub", [(-70, -140, 30, 13.0), (-20, -100, 34, 14.0), (-52, -40, 30, 15.0), (0, 12, 30, 15.5),
                        (52, -22, 30, 16.0), (-30, -8, 22, 15.2)]),
    ("ford", "ford", [(100, -8, 30, 16.5), (142, 40, 30, 17.0), (108, 100, 30, 17.5)]),
    ("jungle", "jungle", [(210, 222, 30, 20.0), (262, 198, 28, 21.0), (302, 252, 30, 22.0), (340, 300, 26, 23.0),
                          (380, 322, 22, 23.0), (412, 334, 16, 23.0)]),
]

ROUTE = [
    (-412.0, -62.0, None),  # 0: lead-in (no road): the desert's end of the road
    (-372.0, -52.0, None),  # 1: START, from Desert World
    (-312.0, -92.0, None),
    (-250.0, -48.0, None),
    (-198.0, -102.0, None),
    (-160.0, -128.0, 12.9),  # 5: the Mesa Tunnel
    (-110.0, -140.0, 13.0),
    (-70.0, -140.0, None),  # 7: the Scrub
    (-18.0, -102.0, None),
    (-52.0, -40.0, None),
    (0.0, 12.0, None),
    (52.0, -22.0, None),
    (100.0, -8.0, None),  # 12: the Ford
    (142.0, 40.0, None),
    (108.0, 100.0, None),
    (132.0, 152.0, 18.4),  # 15: the Vine Gorge
    (172.0, 192.0, 19.6),
    (210.0, 222.0, None),  # 17: the Jungle
    (262.0, 198.0, None),
    (302.0, 252.0, None),
    (340.0, 300.0, None),
    (380.0, 322.0, None),  # 21: END, into Tropic Isles
    (414.0, 336.0, None),  # 22: lead-out (no road)
    (452.0, 400.0, HIDDEN_Z),
    (400.0, 472.0, HIDDEN_Z),
    (0.0, 470.0, HIDDEN_Z),
    (-330.0, 462.0, HIDDEN_Z),
    (-472.0, 250.0, HIDDEN_Z),
    (-470.0, -20.0, HIDDEN_Z),
]
START, END = 1, 21
HIDDEN = range(END + 2, len(ROUTE))
TUNNELS = [("Mesa Tunnel", "mesa", 5, 6), ("Vine Gorge", "vine", 15, 16)]
RIVERS = [[(78.0, 52.0, 15.6), (120.0, 58.0, 15.4), (166.0, 76.0, 15.2)]]
RIVER_HW = 8.0
LAKES = []
POOLS = []
LAVA = []

L = Layout(POCKETS, TOP, ROUTE, TUNNELS, rivers=RIVERS, river_hw=RIVER_HW, roll=4.0, mountains=34.0, hidden=HIDDEN)

ENDS = {"start": ((-372.0, -52.0), (-412.0, -62.0)), "end": ((380.0, 322.0), (414.0, 336.0))}
GATES = {}
WATER_Z = -99.0


def natural(x, y):
    h = L.natural(x, y)
    # The dunes: big swells either side of the troughs the road threads.
    if L.look_at(x, y) == "dunes":
        d = L.wall_sd(x, y)
        h += 4.0 * smooth((d + 22.0) / 16.0) * (0.6 + 0.4 * __import__("math").sin(x / 19.0 + y / 31.0))
    return h


route_points = L.route_points
wall_sd = L.wall_sd
pocket_at = L.pocket_at
lobe_weights = L.look_weights
look_at = L.look_at
tunnel_floor = L.tunnel_floor


def river_d(x, y):
    return L.water_d(x, y)
