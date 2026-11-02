# The Frozen Pass: the journey from the Snow Kingdom down to Desert World (its own
# section between the two). Pure geometry (journey_region.py builds it).
# SPDX-License-Identifier: MIT
#
# v2, the Great Descent (Blake, Nov 1: "between snow world and desert world, the passage
# is very small and boring. lets do what we did for the passage between the dino valley and
# snow. a sequence of open basins and turns"; he chose the Steaming Valley for the middle):
# snow to sand, a climate a basin, squeeze then release three times, as the Burnt Gorge
# v2. Each basin is entered high and seen whole; the snow peaks fall away behind and the
# desert's mesas rise ahead.
#
#   the Ledge            out of the smugglers' tunnel high on the cirque's wall, down into
#   the Frost Cirque     a great bowl of glacier ice under the peaks: a frozen tarn and
#                        the ice-fishers' camp on it, frozen falls hanging off the walls,
#                        seracs, ice columns; out through
#     the Icefall Cave   bored down through the glacier's tongue, onto a ledge over
#   the Steaming Valley  where the mountain's warmth melts the snow: geysers blowing in
#                        their cones, terraced hot pools, steam vents, green grass through
#                        the last snow, the bathers' village by the springs; to its edge,
#     the Stair          switchbacks down a red cliff, the desert seen far below from its
#                        top, into
#   the Painted Badlands the first desert: red and orange hoodoos, a dry wash, the
#                        caravanserai where snow folk and desert folk trade; through
#     the Red Cut        a slot canyon, out into Desert World.
#
# Blender coordinates (x east, y north, z up). The route is a loop; the road only from
# START to END (the rest is out of sight over the mountains).

import math

from pocket_kit import Layout, catmull, lerp, smooth  # noqa: F401

TOP = 104.0
HIDDEN_Z = 200.0

POCKETS = [
    # The Ledge: down the cirque's north-west wall from the tunnel's mouth.
    ("ledge", "snow", [(-376, 372, 15, 72.0), (-350, 344, 15, 68.0), (-326, 318, 17, 62.0), (-306, 300, 18, 56.0)]),
    # The Frost Cirque: a wide bowl, its tarn in the middle.
    ("cirque", "cirque", [(-246, 252, 64, 50.0), (-196, 286, 40, 50.5), (-290, 214, 40, 50.0), (-206, 206, 44, 49.0),
                          (-268, 300, 34, 51.0)]),
    # The Steaming Valley: entered on a ledge from the Icefall Cave, its floor wide and warm.
    ("steam", "steam", [(-104, 104, 14, 38.0), (-82, 80, 16, 33.0), (-10, 30, 66, 26.0), (40, 60, 46, 27.0),
                        (-40, -16, 44, 26.0), (52, -18, 40, 25.0), (-62, 44, 30, 28.0)]),
    # The Stair: switchbacks down the red cliff from the valley's south-east lip.
    ("stair", "stair", [(94, -52, 14, 23.5), (118, -58, 13, 22.0), (130, -74, 13, 20.5), (118, -90, 13, 19.0),
                        (98, -98, 13, 17.4), (90, -114, 13, 15.8), (104, -128, 13, 14.3), (128, -134, 13, 13.0)]),
    # The Painted Badlands.
    ("badlands", "badlands", [(156, -152, 22, 11.5), (204, -186, 52, 10.5), (252, -214, 40, 10.0), (230, -150, 32, 11.0),
                              (178, -226, 34, 10.0)]),
    # The Red Cut: the slot out to Desert World.
    ("cut", "canyon", [(282, -276, 14, 9.5), (312, -306, 14, 9.0), (338, -330, 14, 8.6), (368, -368, 16, 8.0),
                       (382, -404, 14, 8.0)]),
]

ROUTE = [
    (-392.0, 414.0, None),  # 0: lead-in (no road): the smugglers' tunnel, in the mountain
    (-370.0, 362.0, None),  # 1: START, out of the tunnel's mouth onto the Ledge
    (-346.0, 338.0, None),
    (-318.0, 308.0, None),
    (-278.0, 296.0, None),  # 4: the Frost Cirque, round its tarn
    (-232.0, 302.0, None),
    (-194.0, 278.0, None),
    (-192.0, 236.0, None),
    (-178.0, 198.0, None),
    (-160.0, 168.0, 47.0),  # 9: the Icefall Cave, in
    (-124.0, 128.0, 40.5),  # 10: out
    (-102.0, 102.0, None),  # 11: the ledge over the Steaming Valley
    (-74.0, 72.0, None),
    (-32.0, 50.0, None),
    (14.0, 66.0, None),
    (52.0, 42.0, None),
    (38.0, 2.0, None),
    (62.0, -30.0, None),
    (94.0, -52.0, None),  # 18: the top of the Stair: the desert below
    (118.0, -58.0, 22.0),  # 19: down its switchbacks
    (130.0, -74.0, 20.5),
    (118.0, -90.0, 19.0),
    (98.0, -98.0, 17.4),
    (90.0, -114.0, 15.8),
    (104.0, -128.0, 14.3),
    (128.0, -134.0, 13.0),
    (156.0, -152.0, None),  # 26: the Painted Badlands
    (196.0, -176.0, None),
    (236.0, -160.0, None),
    (264.0, -196.0, None),
    (250.0, -238.0, None),
    (282.0, -276.0, None),  # 31: the Red Cut
    (312.0, -306.0, None),
    (338.0, -330.0, None),
    (368.0, -368.0, None),  # 34: END, into Desert World
    (382.0, -406.0, None),  # 35: lead-out (no road)
    (432.0, -462.0, HIDDEN_Z),
    (470.0, -100.0, HIDDEN_Z),
    (452.0, 250.0, HIDDEN_Z),
    (200.0, 470.0, HIDDEN_Z),
    (-150.0, 472.0, HIDDEN_Z),
    (-430.0, 462.0, HIDDEN_Z),
]
START, END = 1, 34
HIDDEN = range(END + 2, len(ROUTE))
TUNNELS = [("Icefall Cave", "ice", 9, 10)]
RIVERS = []
RIVER_HW = 9.0
LAKES = []
POOLS = []
LAVA = []
# The basins' sides as long slopes up to their rims (no pits): (lift, grade).
SOFT = {"steam": (20.0, 0.45), "badlands": (14.0, 0.5)}

L = Layout(POCKETS, TOP, ROUTE, TUNNELS, roll=3.0, mountains=40.0, hidden=HIDDEN)

ENDS = {"start": ((-370.0, 362.0), (-392.0, 414.0)), "end": ((368.0, -368.0), (382.0, -406.0))}
GATES = {}
WATER_Z = -99.0
# Landmarks.
TARN = (-244.0, 250.0, 30.0)  # the Frost Cirque's frozen tarn (x, y, radius)
STEAM = (-6.0, 24.0)  # the Steaming Valley's springs (its middle)
LOOKOUT = (94.0, -52.0)  # the Stair's top: the desert below
WASH = [(150.0, -120.0), (200.0, -200.0), (230.0, -250.0), (280.0, -262.0)]  # the badlands' dry wash
VILLAGES = {"fishers": (-250.0, 214.0, 14.0), "bathers": (-8.0, -10.0, 18.0), "caravanserai": (214.0, -214.0, 18.0)}
# Desert World's mesas on the skyline ahead (out past the land's edge): (x, y, rx, ry, h).
MESAS = [(600.0, -560.0, 110.0, 70.0, 70.0), (520.0, -700.0, 80.0, 60.0, 55.0), (720.0, -420.0, 90.0, 80.0, 85.0)]


def _soft(h, x, y):
    """The valley's and the badlands' sides as long slopes up to their rims."""
    for p in POCKETS:
        if p[0] not in SOFT:
            continue
        sd, f = L.pocket_sd(p, x, y)
        if sd < -12.0 or sd > 90.0:
            continue
        if L.pocket_at(x, y) != p[0] and sd > 4.0:
            continue
        lift, grade = SOFT[p[0]]
        soft = f + grade * max(0.0, sd + 12.0) + lift * smooth((sd - 30.0) / 50.0)
        if soft < h:
            h = lerp(h, soft, smooth((40.0 - sd) / 30.0) if sd > 10.0 else 1.0)
    return h


def ridges(h, x, y):
    """The mountains beyond the basins in ranges running with the descent (north-west to
    south-east), their peaks highest toward the snow behind, falling toward the desert."""
    best = L.wall_sd(x, y)
    if best < 8.0:
        return h
    a = (x - y) * 0.7071  # (along the descent: + toward the desert)
    b = (x + y) * 0.7071
    w = smooth((best - 8.0) / 55.0)
    r = 0.0
    for wl, amp, ph in ((150.0, 1.0, 0.9), (71.0, 0.5, 2.3), (33.0, 0.22, 4.7)):
        n = 1.0 - abs(math.sin(b / wl * math.pi + ph + 0.4 * math.sin(a / 97.0 + ph)))
        r += amp * n * n
    peaks = 0.62 + 0.38 * math.sin(a / 83.0 + 1.1) * math.cos(a / 211.0)
    snowward = 0.45 + 0.95 * smooth((250.0 - a) / 650.0)
    return h + w * r * 62.0 * peaks * snowward


def _tarn(h, x, y):
    tx, ty, tr = TARN
    d = math.hypot(x - tx, y - ty)
    if d < tr + 10.0:
        h = lerp(min(h, 49.2), h, smooth((d - tr) / 10.0))
    return h


def _wash(h, x, y):
    """The badlands' dry wash: a shallow sandy channel winding across the floor."""
    best = 1e9
    for a, b in zip(WASH, WASH[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        t = max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(x - a[0] - dx * t, y - a[1] - dy * t))
    if best < 14.0:
        h -= 1.6 * smooth((14.0 - best) / 8.0)
    return h


# The look out from the Stair's top: a notch through the valley's south-east lip, the
# badlands laid out below it. (degrees from, to; reach; floor)
LOOK_NOTCH = (275.0, 335.0, 150.0, 21.0)


def _notch(h, x, y):
    lx, ly = LOOKOUT
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


def _open_south(h, x, y):
    """Past the badlands, south and east, the land falls away to the desert plain (low
    buttes), so Desert World's mesas stand on the skyline ahead."""
    a = (x - y) * 0.7071
    if a < 330.0 or L.pocket_at(x, y) == "cut" and L.wall_sd(x, y) < 10.0:
        return h
    low = 16.0 + 14.0 * (0.5 + 0.5 * math.sin(x / 37.0) * math.cos(y / 29.0))
    return lerp(h, min(h, low), smooth((a - 330.0) / 60.0))


def natural(x, y):
    h = L.natural(x, y)
    h = _soft(h, x, y)
    h = ridges(h, x, y)
    h = _tarn(h, x, y)
    h = _wash(h, x, y)
    h = _notch(h, x, y)
    h = _open_south(h, x, y)
    return h


def wash_d(x, y):
    best = 1e9
    for a, b in zip(WASH, WASH[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        t = max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(x - a[0] - dx * t, y - a[1] - dy * t))
    return best


route_points = L.route_points
wall_sd = L.wall_sd
pocket_at = L.pocket_at
lobe_weights = L.look_weights
look_at = L.look_at
tunnel_floor = L.tunnel_floor


def river_d(x, y):
    return 1e9, 0.0
