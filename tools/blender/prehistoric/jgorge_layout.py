# The Burnt Gorge: the journey from Dinosaur Valley up to the Snow Kingdom (its own
# section: Blake, Oct 26, "we hit a loading zone, then we go to the connecting segment,
# and then drive the segment to the next loading zone"). Pure geometry, no Blender
# (journey_region.py builds it).
# SPDX-License-Identifier: MIT
#
# v2, the pilgrimage (Blake, Oct 31: "way less claustrophobic ... a real pilgrimage, like
# we are leaving the shire and the world opens up truly ... a few areas that are quite
# open, we go into a tunnel or a bend, into a new large open area ... capture the awe
# moment the dinos are feeling when they first leave their village"; he chose three
# basins, a green river valley first): squeeze, then release, three times. Each squeeze
# hides the next space whole; each basin is entered high and seen at once; the Snow
# Kingdom's peaks stand ahead the whole way.
#
#   the Ember Narrows   Cinderjaw's burnt trench out of the valley: short and tight on
#                       purpose, the last of home; climbing to
#     the Ash Tube      a lava tube through the ridge, dark, out onto
#   the Long Meadow     the first reveal: a ledge high over a wide green river valley,
#                       the river falling into it off the steppe, herds grazing, the
#                       traders' camp by the ford; the road down across it and over the
#                       river, to
#     the Cleft         a narrow cleft under a stone arch, switchbacks up its walls, a
#                       look back over the meadow at the top, into
#   the High Steppe     windy uplands, the volcanic giving way to the alpine: basalt
#                       columns, hot springs, prayer flags, the herders' village, the
#                       first frost; across it to
#     the Snow Arch     an ice tunnel through the col, into
#   the Snowgate        first snow, the pilgrims' hostel, the Snow Kingdom's mountains
#                       rising straight above: the gate.
#
# Blender coordinates (x east, y north, z up). The route is a loop (the kit's courses are),
# the road only from START to END: the rest goes round out of sight over the mountains.

import math

from pocket_kit import Layout, catmull, lerp, smooth  # noqa: F401

TOP = 84.0
HIDDEN_Z = 190.0

POCKETS = [
    ("narrows", "ember", [(-392, -374, 16, 4.0), (-385, -342, 18, 5.0), (-366, -302, 17, 8.0), (-352, -266, 17, 12.0),
                          (-340, -236, 15, 15.0)]),
    # The Long Meadow: its floor low and wide, the ledge it's entered from high on its
    # south-west side, sloping down into it.
    ("meadow", "meadow", [(-292, -150, 14, 24.0), (-266, -116, 18, 18.0), (-238, -84, 26, 10.0), (-160, -40, 100, 3.0),
                          (-60, -96, 62, 4.0), (-96, 52, 62, 5.0), (-226, 26, 58, 4.0), (-170, -130, 46, 3.0),
                          (-20, -10, 40, 5.0)]),
    # The Cleft: narrow, climbing in switchbacks from the meadow's north-east corner.
    ("cleft", "basalt", [(6, 26, 13, 8), (40, 56, 14, 16.5), (60, 68, 14, 19.2), (62, 82, 14, 20.8), (46, 90, 14, 22.8), (16, 98, 14, 26.3), (-2, 106, 14, 28.6), (-2, 120, 14, 30.2), (12, 128, 14, 32), (40, 138, 14, 35.4), (56, 150, 14, 37.6), (64, 166, 15, 40)]),
    ("steppe", "steppe", [(120, 196, 64, 46.0), (60, 236, 44, 47.0), (190, 160, 54, 48.0), (176, 246, 52, 51.0),
                          (240, 210, 40, 53.0), (96, 160, 30, 44.5)]),
    ("snowgate", "snow", [(290, 300, 28, 60.0), (326, 334, 46, 63.0), (352, 374, 40, 67.0), (366, 410, 26, 70.0),
                          (374, 436, 14, 71.0), (300, 368, 30, 64.0)]),
]

ROUTE = [
    (-392.0, -378.0, None),  # 0: lead-in (no road): the valley's end of the gorge
    (-385.0, -345.0, None),  # 1: START: in from the valley, northbound
    (-368.0, -304.0, None),
    (-352.0, -266.0, None),
    (-338.0, -232.0, 15.4),  # 4: the Ash Tube, in
    (-312.0, -190.0, 21.0),  # 5: out
    (-294.0, -160.0, 24.4),  # 6: the ledge over the Long Meadow
    (-270.0, -122.0, None),  # 7: down off the ledge
    (-244.0, -78.0, None),
    (-206.0, -36.0, None),  # 9: over the river
    (-150.0, 0.0, None),
    (-100.0, -40.0, None),
    (-56.0, -70.0, None),
    (-20.0, -24.0, None),
    (6.0, 30.0, None),  # 14: into the Cleft, under the arch
    (40.0, 56.0, 16.8),  # 15: up its switchbacks, rounded hairpins (the road's wide)
    (60.0, 68.0, 19.5),
    (62.0, 82.0, 21.1),
    (46.0, 90.0, 23.1),
    (16.0, 98.0, 26.6),
    (-2.0, 106.0, 28.9),
    (-2.0, 120.0, 30.5),
    (12.0, 128.0, 32.3),
    (40.0, 138.0, 35.7),
    (56.0, 150.0, 37.9),  # 24: the top: the look back
    (72.0, 172.0, None),  # 25: the High Steppe
    (116.0, 210.0, None),
    (168.0, 192.0, None),
    (200.0, 146.0, None),
    (240.0, 190.0, None),
    (258.0, 236.0, 54.6),  # 30: the Snow Arch, in
    (282.0, 272.0, 58.6),  # 31: out
    (318.0, 318.0, None),  # 32: the Snowgate
    (340.0, 352.0, None),
    (360.0, 396.0, None),  # 34: END: the gate into the Snow Kingdom
    (372.0, 430.0, None),  # 35: lead-out (no road)
    # The way round, unseen (no road): over the mountains back to the start.
    (430.0, 470.0, HIDDEN_Z),
    (470.0, 200.0, HIDDEN_Z),
    (460.0, -250.0, HIDDEN_Z),
    (200.0, -470.0, HIDDEN_Z),
    (-200.0, -470.0, HIDDEN_Z),
    (-440.0, -455.0, HIDDEN_Z),
]
START, END = 1, 34
HIDDEN = range(END + 2, len(ROUTE))
TUNNELS = [("Ash Tube", "lava", 4, 5), ("Snow Arch", "ice", 30, 31)]
# The river: off the steppe's edge in a fall into the meadow's north, across it south-west
# and out under the ledge.
RIVERS = [[(-120.0, 116.0, 4.6), (-150.0, 60.0, 3.4), (-186.0, -2.0, 2.4), (-196.0, -70.0, 1.8), (-170.0, -150.0, 1.2),
           (-150.0, -190.0, 0.8)]]
RIVER_HW = 8.0
LAKES = []
POOLS = []
LAVA = [(-376.0, -322.0, 7.0), (-356.0, -246.0, 6.0)]
# The meadow's walls fall away gently (no cliffs: a valley, not a pit), steepening only
# near the ridge-line; the other basins' edges are the kit's.
SOFT = {"meadow": (26.0, 0.42), "steppe": (18.0, 0.5)}

L = Layout(POCKETS, TOP, ROUTE, TUNNELS, rivers=RIVERS, river_hw=RIVER_HW, roll=3.5, mountains=60.0, hidden=HIDDEN)

# The ends: where each loading zone is (the road's last metres) and the landmark beyond.
ENDS = {"start": ((-385.0, -345.0), (-392.0, -378.0)), "end": ((360.0, 396.0), (372.0, 430.0))}
GATES = {}
WATER_Z = -99.0
# Landmarks: the stone arch over the cleft's mouth, the falls, the look back.
ARCH = (6.0, 30.0)
FALLS = (-120.0, 116.0)
LOOKBACK = (56.0, 150.0)
# The villages: the traders' camp by the ford, the herders' on the steppe, the pilgrims'
# hostel under the Snowgate.
VILLAGES = {"traders": (-232.0, 10.0, 18.0), "herders": (82.0, 240.0, 20.0), "hostel": (330.0, 330.0, 12.0)}


def _soft(h, x, y):
    """The meadow's and the steppe's sides as long slopes up to their rims."""
    for p in POCKETS:
        if p[0] not in SOFT:
            continue
        sd, f = L.pocket_sd(p, x, y)
        if sd < -12.0 or sd > 90.0:
            continue
        if L.pocket_at(x, y) != p[0] and sd > 4.0:
            # (only where this basin's the nearest: the ridges to the others stay)
            continue
        lift, grade = SOFT[p[0]]
        soft = f + grade * max(0.0, sd + 12.0) + lift * smooth((sd - 30.0) / 50.0)
        if soft < h:
            h = lerp(h, soft, smooth((40.0 - sd) / 30.0) if sd > 10.0 else 1.0)
    return h


# The look back: from the cleft's top, a notch cut through its south-west wall, the meadow
# laid out below it.
LOOK_NOTCH = (230.0, 250.0, 100.0, 31.0)  # degrees from, to; reach; floor


def _notch(h, x, y):
    lx, ly = LOOKBACK
    a0, a1, reach, fz = LOOK_NOTCH
    d = math.hypot(x - lx, y - ly)
    if d < 8.0 or d > reach:
        return h
    a = math.degrees(math.atan2(y - ly, x - lx)) % 360.0
    mid, half = (a0 + a1) / 2, (a1 - a0) / 2
    off = abs((a - mid + 180.0) % 360.0 - 180.0)
    if off > half + 6.0:
        return h
    w = smooth((half + 6.0 - off) / 6.0) * smooth((d - 8.0) / 8.0)
    return lerp(h, min(h, fz), w)


def natural(x, y):
    h = L.natural(x, y)
    h = _soft(h, x, y)
    h = _notch(h, x, y)
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
