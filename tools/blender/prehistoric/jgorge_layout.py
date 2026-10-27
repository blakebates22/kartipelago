# The Burnt Gorge: the journey from Dinosaur Valley up to the Snow Kingdom (its own
# section: Blake, Oct 26, "we hit a loading zone, then we go to the connecting segment,
# and then drive the segment to the next loading zone"). Pure geometry, no Blender
# (journey_region.py builds it).
# SPDX-License-Identifier: MIT
#
# Cinderjaw's burnt trench out of the valley, then up out of the heat into the first snow:
#
#   the Gorge        a scorched canyon winding north-east, lava pooled in its alcoves,
#                    charred trees, steam
#     the Ash Tube   a lava tube through the ridge
#   the Stair        switchbacks up a basalt slope, the gorge smoking below
#   the Frostline    an upland meadow at the snow's edge: frosted pines, Frost Creek
#                    (frozen) under a timber bridge
#     the Snow Arch  an ice arch through the col
#   the Snowgate     a snow bowl climbing to the gate into the Snow Kingdom
#
# Blender coordinates (x east, y north, z up). The route is a loop (the kit's courses are),
# the road only from START to END: the rest goes round out of sight over the mountains.

from pocket_kit import Layout, catmull, lerp, smooth  # noqa: F401

TOP = 100.0
HIDDEN_Z = 190.0

POCKETS = [
    ("gorge", "ember", [(-392, -374, 18, 4.0), (-385, -342, 24, 4.0), (-352, -285, 24, 5.0), (-322, -240, 22, 6.0),
                        (-338, -192, 24, 7.0), (-300, -152, 24, 8.0), (-252, -166, 24, 9.0), (-212, -152, 20, 10.0),
                        (-378, -252, 16, 4.0), (-276, -204, 15, 6.5), (-368, -318, 20, 4.5), (-334, -264, 16, 5.5),
                        (-326, -168, 18, 7.5)]),
    ("stair", "basalt", [(-108, -128, 22, 13.0), (-62, -108, 20, 18.0), (-100, -70, 20, 23.0), (-52, -40, 20, 28.0),
                         (-96, -4, 20, 33.0), (-56, 30, 22, 38.0), (-80, -92, 16, 20.5), (-84, -120, 14, 15.0),
                         (-76, -55, 16, 25.5), (-78, 12, 16, 35.5), (-84, -18, 14, 33.5), (-32, 52, 18, 40.0)]),
    ("frostline", "frost", [(-10, 72, 30, 42.0), (48, 90, 32, 43.0), (100, 62, 28, 44.0), (142, 96, 28, 45.0),
                            (128, 150, 28, 46.0), (172, 190, 26, 47.0), (70, 130, 30, 44.0)]),
    ("snowgate", "snow", [(282, 282, 26, 52.0), (322, 272, 24, 53.0), (352, 312, 24, 55.0), (332, 352, 24, 56.0),
                          (362, 394, 26, 57.0), (372, 428, 18, 57.0)]),
]

ROUTE = [
    (-392.0, -378.0, None),  # 0: lead-in (no road): the valley's end of the gorge
    (-385.0, -345.0, None),  # 1: START: in from the valley, northbound
    (-352.0, -285.0, None),
    (-318.0, -238.0, None),
    (-340.0, -190.0, None),
    (-300.0, -150.0, None),
    (-250.0, -168.0, None),
    (-204.0, -150.0, 10.6),  # 7: the Ash Tube
    (-150.0, -138.0, 12.4),
    (-108.0, -128.0, None),  # 9: the Stair
    (-60.0, -108.0, None),
    (-100.0, -70.0, None),
    (-50.0, -40.0, None),
    (-96.0, -4.0, None),
    (-54.0, 30.0, None),
    (-10.0, 70.0, None),  # 15: the Frostline
    (50.0, 92.0, None),
    (98.0, 62.0, None),
    (144.0, 96.0, None),
    (128.0, 150.0, None),  # 19: over Frost Creek
    (172.0, 190.0, None),
    (204.0, 222.0, 48.4),  # 21: the Snow Arch
    (244.0, 254.0, 51.0),
    (282.0, 282.0, None),  # 23: the Snowgate
    (322.0, 270.0, None),
    (352.0, 312.0, None),
    (330.0, 352.0, None),
    (362.0, 394.0, None),  # 27: END: the gate into the Snow Kingdom
    (372.0, 428.0, None),  # 28: lead-out (no road)
    # The way round, unseen (no road): over the mountains back to the start.
    (430.0, 470.0, HIDDEN_Z),
    (470.0, 200.0, HIDDEN_Z),
    (460.0, -250.0, HIDDEN_Z),
    (200.0, -470.0, HIDDEN_Z),
    (-200.0, -470.0, HIDDEN_Z),
    (-440.0, -455.0, HIDDEN_Z),
]
START, END = 1, 27
HIDDEN = range(END + 2, len(ROUTE))
TUNNELS = [("Ash Tube", "lava", 7, 8), ("Snow Arch", "ice", 21, 22)]
RIVERS = [[(78.0, 165.0, 44.8), (128.0, 128.0, 44.6), (182.0, 102.0, 44.4)]]
RIVER_HW = 7.0
LAKES = []
POOLS = []
LAVA = [(-382.0, -256.0, 11.0), (-279.0, -208.0, 10.0), (-330.0, -320.0, 0.0)][:2]

L = Layout(POCKETS, TOP, ROUTE, TUNNELS, rivers=RIVERS, river_hw=RIVER_HW, roll=3.0, mountains=40.0, hidden=HIDDEN)

# The ends: where each loading zone is (the road's last metres) and the landmark beyond.
ENDS = {"start": ((-385.0, -345.0), (-392.0, -378.0)), "end": ((362.0, 394.0), (372.0, 428.0))}
GATES = {}
WATER_Z = -99.0


def natural(x, y):
    h = L.natural(x, y)
    for lx, ly, lr in LAVA:
        d = ((x - lx) ** 2 + (y - ly) ** 2) ** 0.5
        if d < lr + 6:
            h = lerp(h, h - 2.2, smooth((lr + 6 - d) / 6.0))
    return h


route_points = L.route_points
wall_sd = L.wall_sd
pocket_at = L.pocket_at
lobe_weights = L.look_weights
look_at = L.look_at
tunnel_floor = L.tunnel_floor


def river_d(x, y):
    return L.water_d(x, y)
