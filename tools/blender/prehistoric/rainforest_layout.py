# Rainforest Rush: the Tropic Isles' fourth course, in the heart of the island's jungle
# (Blake, Nov 1: "I dont like splash lagoon. it reminds me of a cheap water park. ... maybe
# this becomes a super fast island tropical jungle course ... think tropical jungle
# rainforest vibe. we can rename it too"). It replaces Splash Lagoon; its gateway is in the
# Jungle Heart, at the old temple's steps. Pure geometry (rainforest_rush.py builds it).
# SPDX-License-Identifier: MIT
#
# A rollercoaster (v2, Nov 2), a lap near 1 km, about 40 s:
#
#   1  The Temple Steps: off the line on the old temple's paving, a boost pad, and the
#      Temple Leap off the terrace's end.
#   2  The Canopy Dive: a plunging S through the giant trees, over two crests.
#   3  The River Run: a boost pad onto the whoops beside the river.
#   4  The Falls Cave: a climbing turn through the rock beside the great falls.
#   5  The Rope Bridge: over a crest onto it, high over the gorge, and a dive off its end.
#   6  The Hollow Log: through a colossal fallen tree.
#   7  The Kapok Turn: a tight banked hairpin round the kapok's buttress roots.
#   8  The Avenue of Giants: a slalom through the trunks, over a crest.
#   9  The Ruins Hairpin round the fallen pyramid, a boost pad, the Ruins Leap over the
#      sunken court.
#  10  The Temple Run: a boost pad up the stairs, through the temple's gate, onto the line.
#
# Blender coordinates (x east, y north, z up).

import math

from pocket_kit import Layout, catmull, lerp, smooth, seg_d  # noqa: F401

TOP = 40.0
# (v2: smooth green slopes, not tiers of rock: Blake, Nov 2, "it looks very similar to
# cascade cavern, can we make it a bit more distinct?")
WIDTH = 13.0

# (v2, Blake, Nov 2: "the rainforest rush course is more like rainforest snail ... this course
# has to be incredibly exciting from a driving perspective": a rollercoaster, a lap near
# 40 s. The same places and the same look; the drive is new: a leap off the temple's
# terrace, a plunging S through the canopy, whoops along the river, a climbing turn
# through the Falls Cave, a crest onto the Rope Bridge and a dive off it, a tight banked
# hairpin round the kapok, a slalom through the giants, the Ruins Leap over the sunken
# court, and the stairs home.)
POCKETS = [
    ("temple", "temple", [(-40.0, -176.0, 24.0, 22.0), (8.0, -180.0, 26.0, 22.0), (36.0, -180.0, 16.0, 22.0)]),
    ("canopy", "canopy", [(74.0, -168.0, 20.0, 15.0), (86.0, -146.0, 22.0, 13.5), (112.0, -136.0, 24.0, 11.5),
                          (130.0, -108.0, 22.0, 10.2), (156.0, -94.0, 22.0, 7.5), (174.0, -66.0, 22.0, 6.5)]),
    ("river", "river", [(186.0, -14.0, 24.0, 6.0), (184.0, 34.0, 24.0, 6.0), (172.0, 72.0, 20.0, 6.5)]),
    ("gorge", "gorge", [(78.0, 152.0, 18.0, 13.0), (0.0, 156.0, 28.0, -8.0), (-62.0, 150.0, 18.0, 12.5)]),
    ("hollow", "hollow", [(-96.0, 140.0, 20.0, 11.0), (-130.0, 120.0, 20.0, 10.5)]),
    ("kapok", "kapok", [(-158.0, 92.0, 20.0, 10.5), (-174.0, 58.0, 20.0, 10.5), (-160.0, 30.0, 20.0, 10.5),
                        (-145.0, 58.0, 14.0, 10.5)]),
    ("avenue", "avenue", [(-122.0, 14.0, 20.0, 11.0), (-80.0, 10.0, 22.0, 12.0), (-40.0, 8.0, 22.0, 13.0),
                          (-4.0, -2.0, 20.0, 13.5)]),
    ("ruins", "ruins", [(24.0, -32.0, 18.0, 14.5), (32.0, -64.0, 20.0, 15.0), (8.0, -60.0, 14.0, 15.0), (6.0, -88.0, 18.0, 15.5),
                        (-28.0, -94.0, 18.0, 16.0), (-62.0, -104.0, 18.0, 16.5), (-80.0, -130.0, 18.0, 18.5),
                        (-70.0, -160.0, 16.0, 20.5)]),
]

# (x, y, z or None, tag): the tags name the places the course's pieces hang off.
_ROUTE = [
    (0.0, -180.0, 22.0, "start"),  # the Temple Steps: off the line, east, on the paving
    (20.0, -179.5, 22.0, "z_start"),
    (42.0, -178.5, 22.2, "leap1_lip"),  # the Temple Leap: off the terrace's end
    (60.0, -173.0, 15.6, "leap1_land"),
    (78.5, -142.5, 16.0, "crest1"),  # the Canopy Dive: a plunging S through the giant trees
    (112.0, -140.0, 11.8, None),
    (130.0, -108.0, 10.6, "crest2"),
    (159.5, -95.5, 7.4, "z_dive"),
    (170.0, -66.0, 6.8, None),
    (184.0, -40.0, 6.6, "z_river"),  # the River Run: the whoops
    (188.0, -22.0, 6.6, "whoop0"),
    (189.0, -8.0, 8.3, None),
    (189.0, 6.0, 6.7, None),
    (188.0, 20.0, 8.3, None),
    (186.0, 34.0, 6.7, None),
    (183.0, 48.0, 8.2, None),
    (178.0, 62.0, 6.9, "whoop1"),
    (170.0, 80.0, 7.2, "z_cave"),  # the Falls Cave: a climbing turn through the rock
    (150.0, 106.0, 9.6, "cave0"),
    (124.0, 130.0, 12.2, "cave1"),
    (98.0, 146.0, 13.6, None),
    (72.0, 153.0, 15.4, "crest3"),  # the crest onto the Rope Bridge
    (48.0, 155.0, 14.4, "bridge0"),
    (12.0, 155.5, 14.4, None),
    (-24.0, 155.0, 14.4, "bridge1"),
    (-52.0, 152.0, 14.2, "dive"),  # off the bridge's end: the dive to the Hollow Log
    (-76.0, 146.0, 10.6, None),
    (-100.0, 138.0, 10.5, "log0"),
    (-124.0, 124.0, 10.4, "log1"),
    (-146.0, 104.0, 10.4, "hairpin0"),  # the Kapok Turn: tight and banked round the roots
    (-164.0, 82.0, 10.5, None),
    (-170.0, 58.0, 10.5, None),
    (-162.0, 36.0, 10.5, None),
    (-142.0, 26.0, 10.6, "hairpin1"),
    (-118.0, 22.0, 11.0, "z_avenue"),  # the Avenue of Giants: a slalom through the trunks
    (-98.0, 12.0, 11.6, None),
    (-78.0, 18.0, 13.6, "crest4"),
    (-58.0, 6.0, 11.8, None),
    (-38.0, 14.0, 12.6, None),
    (-16.0, 2.0, 13.4, None),
    (4.0, -10.0, 13.8, None),
    (22.0, -30.0, 14.4, "pyr0"),  # the Ruins Hairpin round the fallen pyramid
    (32.0, -54.0, 14.8, None),
    (26.0, -76.0, 15.2, None),
    (8.0, -88.0, 15.6, "pyr1"),
    (-12.0, -92.0, 16.8, "z_leap2"),
    (-30.0, -96.0, 17.4, "leap2_lip"),  # the Ruins Leap: over the sunken court
    (-41.5, -99.0, 15.6, "leap2_land"),
    (-62.0, -108.0, 16.4, None),
    (-80.0, -132.0, 18.4, "z_stairs"),  # the Temple Run: up the stairs
    (-74.0, -160.0, 20.6, "gate"),  # the temple's gate
    (-46.0, -178.0, 21.8, None),
    (-22.0, -180.0, 22.0, None),
]
ROUTE = [p[:3] for p in _ROUTE]
AT = {p[3]: i for i, p in enumerate(_ROUTE) if p[3]}
JUMPS = [(AT["leap1_lip"], AT["leap1_land"], 0.8, False), (AT["leap2_lip"], AT["leap2_land"], 1.0, True)]
COURT = (-35.8, -97.6, 5.0, 11.5)  # the Ruins Leap's sunken court: (x, y, radius, floor)
KAPOK = (-145.0, 60.0)  # the colossal kapok the hairpin turns round
PYRAMID = (8.0, -58.0)  # the fallen pyramid inside the Ruins Hairpin
FALLS = (196.0, 108.0)  # the great falls' foot (off the river valley's north wall, beside the cave's mouth)
RIVER = [(190.0, 112.0, 4.6), (200.0, 60.0, 4.0), (206.0, 0.0, 3.4), (204.0, -40.0, 3.0), (190.0, -80.0, 2.6)]
RIVER_HW = 7.0
GORGE_RIVER = [(4.0, 230.0, -2.0), (0.0, 156.0, -4.0), (-6.0, 80.0, -6.0)]
TEMPLE = (-6.0, -214.0)  # the temple's front, south of the start
# Boost pads (route point, along, across): one before every jump and climb.
ZIPPERS = [(AT["z_start"], 0.4, 0.0), (AT["z_dive"], 0.5, 0.0), (AT["z_river"], 0.3, 0.0), (AT["z_cave"], 0.3, 0.0),
           (AT["crest3"] - 1, 0.5, 0.0), (AT["z_avenue"], 0.5, 0.0), (AT["z_leap2"], 0.2, 0.0), (AT["z_stairs"], 0.3, 0.0)]
BANKS = [(KAPOK[0] - 4.0, KAPOK[1], 46.0, 16.0), (20.0, -60.0, 34.0, 13.0), (137.0, 120.0, 30.0, 11.0)]


# (v2: the whole map drawn at 0.8 its first size: a lap near 1 km, about 40 s.)
K = 0.8


def _k(p, n=2):
    return tuple(v * K for v in p[:n]) + tuple(p[n:])


POCKETS = [(n, lk, [_k(c, 3)[:2] + (c[2] * 0.88, c[3]) for c in cs]) for n, lk, cs in POCKETS]
ROUTE = [_k(p) for p in ROUTE]
COURT, KAPOK, PYRAMID, FALLS, TEMPLE = _k(COURT), _k(KAPOK), _k(PYRAMID), _k(FALLS), _k(TEMPLE)
RIVER = [_k(p) for p in RIVER]
GORGE_RIVER = [_k(p) for p in GORGE_RIVER]
BANKS = [_k(b)[:2] + (b[2] * K, b[3]) for b in BANKS]


# The road itself, every ~6 m along the curve through ROUTE, with each jump cut in: a
# level run up to its lip (the kicker lifts its last metres), the straight flight line
# over the gap (no road there), and the land beyond. TUNNELS index into it; ROUTE (the
# control points) is what the course's pieces hang off.
RUN_UP = 14.0


def _dense():
    pts = catmull(ROUTE, 5)
    n = len(pts)
    cum = [0.0]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    at = [min(range(n), key=lambda k: (pts[k][0] - p[0]) ** 2 + (pts[k][1] - p[1]) ** 2) for p in ROUTE]
    zs = [p[2] for p in pts]
    for lip, land, _, _ in JUMPS:
        i, j = at[lip], at[land]
        zl, zd = ROUTE[lip][2], ROUTE[land][2]
        for k in range(n):
            d = cum[k]
            if cum[i] - RUN_UP - 10.0 <= d < cum[i] - RUN_UP:
                zs[k] = lerp(zs[k], zl, smooth((d - (cum[i] - RUN_UP - 10.0)) / 10.0))
            elif cum[i] - RUN_UP <= d <= cum[i]:
                zs[k] = zl
            elif cum[i] < d <= cum[j]:
                zs[k] = lerp(zl, zd, (d - cum[i]) / (cum[j] - cum[i]))
    return [(round(x, 2), round(y, 2), round(z, 2)) for (x, y, _), z in zip(pts, zs)], at


DENSE, DAT = _dense()
TUNNELS = [("Falls Cave", "cave", DAT[AT["cave0"]], DAT[AT["cave1"]])]
BRIDGE = (AT["bridge0"], AT["bridge1"])  # the rope bridge's route points
LOG = (AT["log0"], AT["log1"])  # the hollow log round these
GATE = AT["gate"]
SIDE_FALLS = (AT["z_river"], AT["whoop0"] + 2, AT["whoop0"] + 4)  # thin falls off the river valley's wall
# The jumps: (lip, landing route points, the kicker's lift, a respawn past a miss).


class _Rain(Layout):
    def natural(self, x, y):
        h = Layout.natural(self, x, y)
        # The gorge's river, deep under the bridge.
        for (ax, ay, az), (bx, by, bz) in zip(GORGE_RIVER, GORGE_RIVER[1:]):
            d, t = seg_d(x, y, (ax, ay), (bx, by))
            if d < 30.0:
                h = lerp(h, min(h, lerp(az, bz, t) - 1.6), smooth((30.0 - d) / 16.0))
        # The Ruins Leap's sunken court.
        cx, cy, cr, cz = COURT
        d = math.hypot(x - cx, y - cy)
        if d < cr + 8.0:
            h = lerp(h, min(h, cz), smooth((cr + 8.0 - d) / 8.0))
        return h


L = _Rain(POCKETS, TOP, DENSE, TUNNELS, rivers=[RIVER], river_hw=RIVER_HW, roll=2.2, mountains=50.0, tiers=False)


def natural(x, y):
    return L.natural(x, y)


route_points = L.route_points
wall_sd = L.wall_sd
pocket_at = L.pocket_at
look_at = L.look_at
look_weights = L.look_weights
tunnel_floor = L.tunnel_floor
