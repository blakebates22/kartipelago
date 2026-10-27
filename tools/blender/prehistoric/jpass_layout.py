# The Frozen Pass: the journey from the Snow Kingdom down to Desert World (its own
# section between the two). Pure geometry (journey_region.py builds it).
# SPDX-License-Identifier: MIT
#
# Down out of the snow into the heat:
#
#   the Col          a wind-scoured saddle, ice spikes, the snow's last gate behind you
#     the Ice Cave   bored through blue ice
#   the Glacier      a glacier's tongue falling south, seracs standing out of it
#   the Melt         switchbacks down wet rock below the ice, meltwater falls, the last pines
#   the Red Cut      a slot canyon winding through red rock: the first heat
#   the Edge         the desert's edge: sand, saguaros, the gate into Desert World
#
# Blender coordinates (x east, y north, z up). The route is a loop; the road only from
# START to END (the rest is out of sight over the mountains).

from pocket_kit import Layout, catmull, lerp, smooth  # noqa: F401

TOP = 104.0
HIDDEN_Z = 200.0

POCKETS = [
    ("col", "snow", [(-390, 400, 18, 70.0), (-370, 362, 26, 70.0), (-320, 330, 28, 69.0), (-268, 352, 24, 68.0)]),
    ("glacier", "glacier", [(-140, 270, 34, 60.0), (-100, 222, 34, 54.0), (-132, 168, 34, 48.0), (-82, 112, 34, 42.0)]),
    ("melt", "melt", [(-30, 82, 22, 36.0), (20, 96, 20, 32.0), (8, 52, 20, 28.0), (60, 40, 20, 24.0), (48, 2, 20, 20.0),
                      (100, -12, 22, 17.0), (-6, 92, 14, 34.0), (14, 74, 14, 30.0), (34, 46, 14, 26.0), (54, 20, 14, 22.0),
                      (74, -6, 14, 18.5), (-55, 90, 16, 38.0)]),
    ("cut", "canyon", [(136, -40, 17, 14.5), (158, -82, 17, 13.5), (140, -122, 17, 12.5), (170, -160, 17, 11.5),
                       (200, -190, 18, 10.5), (146, -56, 15, 14.0), (150, -101, 15, 13.0), (154, -142, 15, 12.0), (214, -204, 18, 10.0)]),
    ("edge", "sand", [(250, -230, 40, 9.0), (310, -262, 34, 8.5), (330, -322, 30, 8.0), (368, -368, 26, 8.0),
                      (382, -404, 18, 8.0)]),
]

ROUTE = [
    (-392.0, 414.0, None),  # 0: lead-in (no road): the snow's end of the pass
    (-370.0, 362.0, None),  # 1: START, from the Snow Kingdom
    (-320.0, 330.0, None),
    (-268.0, 352.0, None),
    (-226.0, 320.0, 66.6),  # 4: the Ice Cave
    (-182.0, 292.0, 62.6),
    (-140.0, 270.0, None),  # 6: the Glacier
    (-92.0, 230.0, None),
    (-132.0, 170.0, None),
    (-80.0, 112.0, None),
    (-30.0, 80.0, None),  # 10: the Melt
    (20.0, 96.0, None),
    (8.0, 52.0, None),
    (60.0, 40.0, None),
    (48.0, 2.0, None),
    (100.0, -12.0, None),
    (136.0, -42.0, None),  # 16: the Red Cut
    (158.0, -82.0, None),
    (140.0, -122.0, None),
    (170.0, -160.0, None),
    (200.0, -190.0, None),
    (250.0, -228.0, None),  # 21: the Edge
    (310.0, -262.0, None),
    (330.0, -322.0, None),
    (368.0, -368.0, None),  # 24: END, into Desert World
    (382.0, -406.0, None),  # 25: lead-out (no road)
    (432.0, -462.0, HIDDEN_Z),
    (470.0, -100.0, HIDDEN_Z),
    (452.0, 250.0, HIDDEN_Z),
    (200.0, 470.0, HIDDEN_Z),
    (-150.0, 472.0, HIDDEN_Z),
    (-430.0, 462.0, HIDDEN_Z),
]
START, END = 1, 24
HIDDEN = range(END + 2, len(ROUTE))
TUNNELS = [("Ice Cave", "ice", 4, 5)]
RIVERS = []
RIVER_HW = 9.0
LAKES = []
POOLS = []
LAVA = []

L = Layout(POCKETS, TOP, ROUTE, TUNNELS, roll=3.0, mountains=40.0, hidden=HIDDEN)

ENDS = {"start": ((-370.0, 362.0), (-392.0, 414.0)), "end": ((368.0, -368.0), (382.0, -406.0))}
GATES = {}
WATER_Z = -99.0


def natural(x, y):
    return L.natural(x, y)


route_points = L.route_points
wall_sd = L.wall_sd
pocket_at = L.pocket_at
lobe_weights = L.look_weights
look_at = L.look_at
tunnel_floor = L.tunnel_floor


def river_d(x, y):
    return 1e9, 0.0
