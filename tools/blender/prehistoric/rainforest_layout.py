# Rainforest Rush: the Tropic Isles' fourth course, in the heart of the island's jungle
# (Blake, Nov 1: "I dont like splash lagoon. it reminds me of a cheap water park. ... maybe
# this becomes a super fast island tropical jungle course ... think tropical jungle
# rainforest vibe. we can rename it too"). It replaces Splash Lagoon; its gateway is in the
# Jungle Heart, at the old temple's steps. Pure geometry (rainforest_rush.py builds it).
# SPDX-License-Identifier: MIT
#
# Fast: a wide road, long sweeps, boost pads, a lap near 40 s:
#
#   1  The Temple Steps: off the start on the old temple's paving, east, a boost pad.
#   2  The Canopy Dive: down a long sweeping S through the giant trees.
#   3  The River Run: north beside the river, flat out.
#   4  The Falls Cave: in behind the great falls, through the rock.
#   5  The Rope Bridge: dead straight across the gorge, high over the river, a boost pad.
#   6  The Hollow Log: through a colossal fallen tree.
#   7  The Kapok Turn: a big banked hairpin round the kapok's buttress roots.
#   8  The Temple Run: up through the ruins and the temple's gate, onto the line.
#
# Blender coordinates (x east, y north, z up).

import math

from pocket_kit import Layout, catmull, lerp, smooth, seg_d  # noqa: F401

TOP = 46.0
WIDTH = 16.0

POCKETS = [
    ("temple", "temple", [(-40.0, -176.0, 26.0, 20.0), (8.0, -180.0, 26.0, 20.0), (52.0, -176.0, 24.0, 19.5)]),
    ("canopy", "canopy", [(96.0, -160.0, 26.0, 16.5), (134.0, -132.0, 26.0, 12.5), (152.0, -98.0, 24.0, 9.5),
                          (176.0, -56.0, 24.0, 7.5)]),
    ("river", "river", [(186.0, -6.0, 26.0, 6.0), (182.0, 42.0, 26.0, 6.0), (168.0, 80.0, 22.0, 6.5)]),
    ("gorge", "gorge", [(72.0, 150.0, 20.0, 9.0), (0.0, 156.0, 28.0, -8.0), (-62.0, 150.0, 22.0, 9.5)]),
    ("hollow", "hollow", [(-104.0, 140.0, 22.0, 10.0), (-142.0, 120.0, 22.0, 10.0)]),
    ("kapok", "kapok", [(-172.0, 92.0, 22.0, 11.0), (-186.0, 54.0, 24.0, 11.0), (-168.0, 22.0, 22.0, 11.5),
                        (-145.0, 58.0, 14.0, 11.0)]),
    ("avenue", "avenue", [(-130.0, 8.0, 22.0, 12.0), (-84.0, 6.0, 24.0, 12.5), (-40.0, 0.0, 24.0, 13.0),
                          (0.0, -10.0, 22.0, 13.5)]),
    ("ruins", "ruins", [(28.0, -36.0, 20.0, 14.0), (30.0, -66.0, 22.0, 14.5), (8.0, -60.0, 14.0, 14.5), (10.0, -88.0, 20.0, 15.0),
                        (-24.0, -92.0, 20.0, 15.5), (-62.0, -104.0, 20.0, 16.5), (-84.0, -132.0, 20.0, 18.0),
                        (-72.0, -160.0, 18.0, 19.5)]),
]

ROUTE = [
    (0.0, -180.0, 20.2),  # 0: the start, on the temple's paving, east
    (40.0, -178.0, 20.0),
    (80.0, -168.0, None),  # 2: the Canopy Dive
    (114.0, -150.0, None),
    (138.0, -124.0, None),
    (146.0, -96.0, None),
    (166.0, -70.0, None),
    (184.0, -36.0, None),  # 7: the River Run
    (186.0, 4.0, None),
    (182.0, 44.0, None),
    (170.0, 78.0, None),  # 10: the Falls Cave
    (148.0, 112.0, 8.4),
    (116.0, 140.0, 9.0),
    (78.0, 152.0, None),  # 13: the Rope Bridge
    (36.0, 154.0, 12.0),
    (0.0, 154.0, 12.0),
    (-36.0, 152.0, 12.0),
    (-70.0, 150.0, None),
    (-104.0, 140.0, None),  # 18: the Hollow Log
    (-140.0, 120.0, None),
    (-170.0, 92.0, None),  # 20: the Kapok Turn
    (-182.0, 56.0, None),
    (-170.0, 24.0, None),
    (-138.0, 10.0, None),  # 23: the Avenue of Giants, east through the middle
    (-96.0, 6.0, None),
    (-50.0, 0.0, None),
    (-10.0, -8.0, None),
    (24.0, -30.0, None),  # 27: the Ruins Hairpin, round the fallen pyramid
    (36.0, -62.0, None),
    (16.0, -86.0, None),
    (-20.0, -90.0, None),
    (-60.0, -100.0, None),
    (-84.0, -130.0, 18.4),  # 32: the Temple Run, up
    (-72.0, -164.0, 19.8),  # 33: the temple's gate
    (-40.0, -180.0, 20.2),
]
TUNNELS = [("Falls Cave", "cave", 11, 12)]
BRIDGE = (14, 16)  # the rope bridge's route points
LOG = (18, 19)  # the hollow log round these
KAPOK = (-145.0, 58.0)  # the colossal kapok the hairpin turns round
PYRAMID = (8.0, -58.0)  # the fallen pyramid inside the Ruins Hairpin
FALLS = (196.0, 108.0)  # the great falls' foot (off the river valley's north wall, beside the cave's mouth)
RIVER = [(190.0, 112.0, 4.6), (200.0, 60.0, 4.0), (206.0, 0.0, 3.4), (204.0, -40.0, 3.0), (190.0, -80.0, 2.6)]
RIVER_HW = 7.0
GORGE_RIVER = [(4.0, 230.0, -2.0), (0.0, 156.0, -4.0), (-6.0, 80.0, -6.0)]
TEMPLE = (-6.0, -214.0)  # the temple's front, south of the start
ZIPPERS = [(0, 0.6, 0.0), (6, 0.5, -3.0), (8, 0.3, 3.0), (14, 0.5, 0.0), (24, 0.5, 0.0), (30, 0.4, -3.0)]


class _Rain(Layout):
    def natural(self, x, y):
        h = Layout.natural(self, x, y)
        # The gorge's river, deep under the bridge.
        for (ax, ay, az), (bx, by, bz) in zip(GORGE_RIVER, GORGE_RIVER[1:]):
            d, t = seg_d(x, y, (ax, ay), (bx, by))
            if d < 30.0:
                h = lerp(h, min(h, lerp(az, bz, t) - 1.6), smooth((30.0 - d) / 16.0))
        return h


L = _Rain(POCKETS, TOP, ROUTE, TUNNELS, rivers=[RIVER], river_hw=RIVER_HW, roll=1.4, mountains=60.0, tiers=True)


def natural(x, y):
    return L.natural(x, y)


route_points = L.route_points
wall_sd = L.wall_sd
pocket_at = L.pocket_at
look_at = L.look_at
look_weights = L.look_weights
tunnel_floor = L.tunnel_floor
