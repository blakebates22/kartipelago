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
HUB = (-262.0, 0.0, 24.0, 10.0)  # x, y, radius, height: the post's square
POST = HUB
POOL = (250.0, 228.0, 18.0, 5.0)  # the oasis pool: x, y, radius, water height
CRATER = (-10.0, -215.0)  # the crater's middle

POCKETS = [
    ("post", "post", [(-260.0, 0.0, 55.0, 10.0), (-222.0, 42.0, 32.0, 10.0), (-225.0, -42.0, 32.0, 10.0)]),
    # (the Frozen Pass, west, up to the snow)
    ("pass", "post", [(-330.0, 4.0, 22.0, 12.0), (-375.0, -4.0, 21.0, 14.0), (-420.0, 4.0, 21.0, 16.0),
                      (-462.0, 0.0, 24.0, 18.0)]),
    ("slot", "canyon", [(-214.0, 70.0, 18.0, 11.0), (-206.0, 92.0, 19.0, 12.0), (-182.0, 125.0, 18.0, 13.0),
                        (-196.0, 145.0, 17.0, 14.0), (-200.0, 160.0, 19.0, 15.0), (-185.0, 178.0, 17.0, 15.5),
                        (-170.0, 192.0, 20.0, 16.0), (-152.0, 212.0, 20.0, 16.5)]),
    ("canyon", "canyon", [(-90.0, 240.0, 70.0, 18.0), (-10.0, 280.0, 52.0, 19.0), (-150.0, 255.0, 38.0, 17.0)]),
    ("oasis", "oasis", [(170.0, 260.0, 40.0, 6.0), (230.0, 200.0, 70.0, 6.0), (290.0, 130.0, 45.0, 7.0)]),
    ("gulch", "gulch", [(285.0, -60.0, 40.0, 13.0), (230.0, -150.0, 70.0, 14.0), (150.0, -230.0, 42.0, 14.0),
                        (198.0, -214.0, 28.0, 14.0)]),
    ("rim", "crater", [(100.0, -262.0, 20.0, 16.0), (62.0, -262.0, 20.0, 13.5), (30.0, -266.0, 22.0, 10.5)]),
    ("crater", "crater", [(-10.0, -215.0, 64.0, 6.0), (-70.0, -170.0, 36.0, 7.0), (40.0, -180.0, 36.0, 7.0)]),
    ("wash", "post", [(-105.0, -150.0, 22.0, 7.5), (-130.0, -112.0, 20.0, 8.0), (-172.0, -118.0, 20.0, 8.5),
                      (-195.0, -82.0, 22.0, 9.5), (-215.0, -62.0, 24.0, 10.0)]),
]

ROUTE = [
    (-235.0, -10.0, None),  # 0: the start, the post's east side, northbound
    (-228.0, 35.0, None),
    (-206.0, 90.0, None),  # 2: the Slot
    (-182.0, 125.0, None),
    (-200.0, 160.0, None),
    (-168.0, 192.0, None),
    (-130.0, 238.0, None),  # 6: the canyon
    (-80.0, 262.0, None),
    (-60.0, 215.0, None),
    (-10.0, 240.0, None),
    (20.0, 288.0, None),
    (48.0, 282.0, 18.6),  # 11: the Arch
    (100.0, 268.0, 12.0),
    (150.0, 255.0, None),  # 13: the oasis
    (192.0, 240.0, None),
    (212.0, 196.0, None),
    (252.0, 184.0, None),
    (272.0, 148.0, None),
    (300.0, 110.0, None),
    (296.0, 70.0, 8.6),  # 19: the Mine
    (290.0, 22.0, 10.4),
    (285.0, -24.0, 12.2),
    (275.0, -70.0, None),  # 21: the ghost town's street
    (240.0, -120.0, None),
    (200.0, -150.0, None),
    (230.0, -195.0, None),
    (180.0, -240.0, None),
    (140.0, -236.0, None),
    (100.0, -262.0, None),  # 27: over the rim
    (62.0, -262.0, None),
    (28.0, -262.0, None),
    (-5.0, -250.0, None),  # 30: the crater
    (25.0, -205.0, None),
    (-20.0, -180.0, None),
    (-70.0, -170.0, None),
    (-105.0, -150.0, None),  # 34: the Wash
    (-130.0, -112.0, None),
    (-172.0, -118.0, None),
    (-195.0, -82.0, None),
    (-215.0, -62.0, None),
    (-235.0, -40.0, None),
]
TUNNELS = [("The Arch", "arch", 11, 12), ("The Mine", "mine", 19, 21)]

L = Layout(POCKETS, TOP, ROUTE, TUNNELS, hub=HUB, lakes=[POOL], roll=4.0, flat=("post",), mountains=40.0,
           water_floor=1.2)

GATES = {
    "canyon": (-60.0, 322.0),  # the slot canyon's mouth in the north wall
    "oasis": (312.0, 172.0),  # the palm grove by the spring
    "gulch": (238.0, -228.0),  # the end of the false-front street
    "impact": (-40.0, -244.0),  # the shards in the crater's floor
}
LAIR = (-190.0, 270.0)  # Scorchwind's lair (the ruin's boss gateway): a rock arch in the canyon's west wall
DUST_ROAD = (0.0, -280.0)  # where the Dust Road leaves the crater (the ruin), on south
DUST_END = (0.0, -460.0)
PASS_END = (-470.0, 0.0)  # the Frozen Pass's far end: the passage back to the snow


def natural(x, y):
    h = L.natural(x, y)
    # The crater's bowl: its floor dips to the middle.
    cx, cy = CRATER
    d = math.hypot(x - cx, y - cy)
    if d < 60:
        h -= 3.0 * (1.0 - smooth(d / 60.0))
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
