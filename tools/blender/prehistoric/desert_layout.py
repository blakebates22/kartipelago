# Desert World's layout (v3, on pocket_kit): pure geometry, no Blender (desert_region.py
# builds it).
# SPDX-License-Identifier: MIT
#
# Built like the valley's and the Snow Kingdom's (Blake, Oct 26): a pocket for each of the
# kingdom's worlds walled off by red rock, the main road one loop through them (Stego's
# 1-on-1), a threshold between each:
#
#   the Trading Post (hub, W)  Stego's post round its square; the Frozen Pass comes down
#                              into it out of the snow, west
#     the Slot           a narrow winding slot canyon north, light falling into it
#   Canyon (N)        banded red cliffs, hoodoos, arches (Scorchwind's lair in its west
#                     wall, after his attack)
#     the Arch           a tunnel through a sandstone fin, east
#   the Oasis (NE)    palms round a spring-fed pool, adobe walls, green
#     the Mine           a timber-shored mine tunnel south under the ridge
#   the Gulch (SE)    the ghost town: false fronts, a water tower, tumbleweeds
#     the Rim            up over the meteor crater's rim and down inside it (the one view
#                        of another world: down into the crater)
#   the Crater (S)    the impact's bowl, glowing shards in its floor (the Dust Road out
#                     south to Tropic Isles, after Scorchwind falls)
#     the Wash           a dry riverbed's S-bends back west to the post
#
# Blender coordinates (x east, y north, z up).

import math

from pocket_kit import Layout, catmull, lerp, smooth  # noqa: F401

TOP = 64.0
HUB = (-162.4, 0.0, 19.2, 10.0)  # x, y, radius, height: the post's square
POST = HUB
POOL = (155.0, 141.4, 11.2, 5.0)  # the oasis pool: x, y, radius, water height
CRATER = (-6.2, -133.3)  # the crater's middle

POCKETS = [
    ("post", "post", [(-161.2, 0.0, 40.7, 10.0), (-137.6, 26.0, 23.7, 10.0), (-139.5, -26.0, 23.7, 10.0)]),
    # (the Frozen Pass, west, up to the snow)
    ("pass", "post", [(-204.6, 2.5, 16.3, 12.0), (-232.5, -2.5, 15.5, 14.0), (-260.4, 2.5, 15.5, 16.0),
                      (-286.4, 0.0, 17.8, 18.0)]),
    ("slot", "canyon", [(-132.7, 43.4, 13.3, 11.0), (-127.7, 57.0, 14.1, 12.0), (-112.8, 77.5, 13.3, 13.0),
                        (-121.5, 89.9, 12.6, 14.0), (-124.0, 99.2, 14.1, 15.0), (-114.7, 110.4, 12.6, 15.5),
                        (-105.4, 119.0, 14.8, 16.0), (-94.2, 131.4, 14.8, 16.5)]),
    ("canyon", "canyon", [(-55.8, 148.8, 51.8, 18.0), (-6.2, 173.6, 38.5, 19.0), (-93.0, 158.1, 28.1, 17.0)]),
    ("oasis", "oasis", [(105.4, 161.2, 29.6, 6.0), (142.6, 124.0, 51.8, 6.0), (179.8, 80.6, 33.3, 7.0)]),
    ("gulch", "gulch", [(176.7, -37.2, 29.6, 13.0), (142.6, -93.0, 51.8, 14.0), (93.0, -142.6, 31.1, 14.0),
                        (122.8, -132.7, 20.7, 14.0)]),
    ("rim", "crater", [(62.0, -162.4, 14.8, 16.0), (38.4, -162.4, 14.8, 13.5), (18.6, -164.9, 16.3, 10.5)]),
    ("crater", "crater", [(-6.2, -133.3, 47.4, 6.0), (-43.4, -105.4, 26.6, 7.0), (24.8, -111.6, 26.6, 7.0)]),
    ("wash", "post", [(-65.1, -93.0, 16.3, 7.5), (-80.6, -69.4, 14.8, 8.0), (-106.6, -73.2, 14.8, 8.5),
                      (-120.9, -50.8, 16.3, 9.5), (-133.3, -38.4, 17.8, 10.0)]),
]

ROUTE = [
    (-145.7, -6.2, None),  # 0: the start, the post's east side, northbound
    (-141.4, 21.7, None),
    (-127.7, 55.8, None),  # 2: the Slot
    (-116.3, 77.5, None),
    (-118.6, 98.8, None),
    (-104.2, 119.0, None),
    (-80.6, 147.6, None),  # 6: the canyon
    (-53.6, 153.0, None),
    (-33.5, 142.3, None),
    (-6.2, 148.8, None),
    (12.2, 172.1, None),
    (29.8, 174.8, 18.6),  # 11: the Arch
    (62.0, 166.2, 12.0),
    (93.0, 158.1, None),  # 13: the oasis
    (119.0, 148.8, None),
    (132.3, 123.0, None),
    (156.2, 114.1, None),
    (168.6, 91.8, None),
    (186.0, 68.2, None),
    (183.5, 43.4, 8.6),  # 19: the Mine
    (179.8, 13.6, 10.4),
    (176.7, -14.9, 12.2),
    (170.5, -43.4, None),  # 21: the ghost town's street
    (148.8, -74.4, None),
    (131.7, -94.8, None),
    (134.2, -121.2, None),
    (111.4, -146.6, None),
    (86.8, -147.7, None),
    (62.0, -162.4, None),  # 27: over the rim
    (38.4, -162.4, None),
    (17.4, -162.4, None),
    (6.1, -149.7, None),  # 30: the crater
    (4.5, -129.5, None),
    (-12.4, -111.6, None),
    (-43.4, -105.4, None),
    (-65.1, -93.0, None),  # 34: the Wash
    (-82.0, -73.1, None),
    (-105.1, -70.0, None),
    (-120.9, -50.8, None),
    (-133.3, -38.4, None),
    (-145.7, -24.8, None),
]
TUNNELS = [("The Arch", "arch", 11, 12), ("The Mine", "mine", 19, 21)]

L = Layout(POCKETS, TOP, ROUTE, TUNNELS, hub=HUB, lakes=[POOL], roll=4.0, flat=("post",), mountains=40.0,
           water_floor=1.2, tiers=True)

GATES = {
    "canyon": (-37.2, 199.6),  # the slot canyon's mouth in the north wall
    "oasis": (193.4, 106.6),  # the palm grove by the spring
    "gulch": (147.6, -141.4),  # the end of the false-front street
    "impact": (-24.8, -151.3),  # the shards in the crater's floor
}
LAIR = (-117.8, 167.4)  # Scorchwind's lair (the ruin's boss gateway): a rock arch in the canyon's west wall
DUST_ROAD = (0.0, -173.6)  # where the Dust Road leaves the crater (the ruin), on south
DUST_END = (0.0, -285.2)
PASS_END = (-291.4, 0.0)  # the Frozen Pass's far end: the passage back to the snow


def natural(x, y):
    h = L.natural(x, y)
    # The crater's bowl: its floor dips to the middle.
    cx, cy = CRATER
    d = math.hypot(x - cx, y - cy)
    if d < 37:
        h -= 3.0 * (1.0 - smooth(d / 37.0))
    return h


route_points = L.route_points
wall_sd = L.wall_sd
pocket_at = L.pocket_at
lobe_weights = L.look_weights
look_at = L.look_at
tunnel_floor = L.tunnel_floor
RIVERS = []
LAKES = [POOL]
POOLS = []
LAVA = []
RIVER_HW = 9.0


def river_d(x, y):
    return L.water_d(x, y)
