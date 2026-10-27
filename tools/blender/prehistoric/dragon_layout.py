# The Dragon Kingdom's layout (v3, on pocket_kit): pure geometry, no Blender
# (dragon_region.py builds it).
# SPDX-License-Identifier: MIT
#
# Built like the other kingdoms' (Blake, Oct 26): a pocket for each of its worlds walled
# off by dark crags, the main road one loop through them, a threshold between each:
#
#   the Harbour (hub, S)  where Tidewyrm's Causeway comes in over the sea; Dragonfire
#                         Square and the great dragon statue
#     the Dragon Gate     through the harbour's sea wall, west
#   Moonstone (W)      the moon festival: violet lanterns, pagodas, the moon gate
#     the Climb           a switchback ravine up to the crag
#   Dragonspire (NW)   the keep's town on its crag, towers and banners
#     the Keep Gate       through the curtain wall onto the high road
#   the Citadel (N)    the approach to King Pyrrhax's Citadel, its gate in the north wall
#     the Lava Tube       down through the mountain, east
#   Emberdeep (NE)     the hold's black fortress walls, lava, the storm over it
#     the Storm Pass      an S-bend gulch south, lightning on the rim
#   the Emerald Canyon (E)  the overgrown jungle castle's canyon
#     the Root Tunnel     through the jungle ridge, back to the harbour
#
# Blender coordinates (x east, y north, z up).

import math

from pocket_kit import Layout, catmull, lerp, smooth  # noqa: F401

TOP = 70.0
WATER_Z = -0.8
HUB = (0.0, -212.0, 24.0, 3.0)  # x, y, radius, height: Dragonfire Square

POCKETS = [
    ("harbour", "harbour", [(0.0, -218.0, 58.0, 3.0), (55.0, -248.0, 32.0, 2.5), (-55.0, -248.0, 32.0, 2.5),
                            (-95.0, -214.0, 26.0, 4.0), (-50.0, -204.0, 26.0, 3.0), (0.0, -330.0, 88.0, -6.0), (0.0, -445.0, 90.0, -9.0)]),
    ("moon", "moon", [(-250.0, -40.0, 60.0, 14.0), (-300.0, 30.0, 40.0, 15.0), (-205.0, 18.0, 34.0, 14.0),
                      (-200.0, -108.0, 34.0, 10.0)]),
    ("climb", "keep", [(-285.0, 62.0, 22.0, 16.5), (-292.0, 82.0, 22.0, 18.0), (-262.0, 115.0, 21.0, 22.0), (-290.0, 150.0, 22.0, 26.0),
                       (-256.0, 176.0, 24.0, 29.0)]),
    ("keep", "keep", [(-200.0, 210.0, 56.0, 31.0), (-135.0, 252.0, 40.0, 32.0), (-262.0, 236.0, 34.0, 30.0)]),
    ("citadel", "citadel", [(-12.0, 292.0, 46.0, 35.0), (46.0, 300.0, 34.0, 35.0)]),
    ("hold", "hold", [(195.0, 182.0, 60.0, 22.0), (262.0, 122.0, 38.0, 20.0), (150.0, 232.0, 34.0, 28.0)]),
    ("storm", "hold", [(290.0, 82.0, 22.0, 18.0), (266.0, 40.0, 21.0, 15.0), (292.0, 0.0, 22.0, 13.0),
                       (268.0, -25.0, 24.0, 11.0)]),
    ("canyon", "canyon", [(245.0, -62.0, 56.0, 9.0), (288.0, -130.0, 38.0, 8.0), (205.0, -140.0, 34.0, 6.0), (240.0, -160.0, 30.0, 7.0)]),
]

ROUTE = [
    (20.0, -192.0, None),  # 0: the start, north of Dragonfire Square, westbound
    (-40.0, -196.0, None),
    (-95.0, -212.0, None),
    (-122.0, -190.0, 5.4),  # 3: the Dragon Gate
    (-170.0, -140.0, 8.6),
    (-205.0, -105.0, None),  # 5: Moonstone
    (-250.0, -75.0, None),
    (-214.0, -30.0, None),
    (-260.0, 0.0, None),
    (-305.0, 25.0, None),
    (-282.0, 60.0, None),
    (-292.0, 84.0, None),  # 11: the Climb
    (-262.0, 115.0, None),
    (-290.0, 150.0, None),
    (-256.0, 176.0, None),
    (-226.0, 200.0, None),  # 15: Dragonspire's town
    (-180.0, 232.0, None),
    (-132.0, 250.0, None),
    (-96.0, 264.0, 33.0),  # 18: the Keep Gate
    (-56.0, 280.0, 34.6),
    (-10.0, 294.0, None),  # 20: the Citadel's approach
    (40.0, 306.0, None),
    (80.0, 290.0, 33.6),  # 22: the Lava Tube
    (114.0, 262.0, 29.6),
    (150.0, 236.0, None),  # 24: Emberdeep
    (200.0, 200.0, None),
    (240.0, 160.0, None),
    (272.0, 124.0, None),
    (290.0, 82.0, None),  # 28: the Storm Pass
    (266.0, 40.0, None),
    (292.0, 0.0, None),
    (268.0, -25.0, None),
    (244.0, -62.0, None),  # 32: the Emerald Canyon
    (284.0, -102.0, None),
    (264.0, -150.0, None),
    (206.0, -140.0, None),
    (172.0, -164.0, 4.8),  # 36: the Root Tunnel
    (110.0, -210.0, 3.6),
    (64.0, -228.0, None),
]
TUNNELS = [("Dragon Gate", "gate", 3, 4), ("Keep Gate", "gate", 18, 19), ("Lava Tube", "lava", 22, 23),
           ("Root Tunnel", "roots", 36, 37)]

L = Layout(POCKETS, TOP, ROUTE, TUNNELS, hub=HUB, roll=3.5, flat=("harbour",), mountains=50.0)

GATES = {
    "keep": (-214.0, 266.0),  # Dragonspire Keep's tower on its crag
    "canyon": (330.0, -112.0),  # the overgrown jungle castle's gate
    "hold": (214.0, 238.0),  # Emberdeep Hold's fortress gate
    "moon": (-338.0, 18.0),  # the moon gate among the lanterns
}
CITADEL = (6.0, 338.0)  # King Pyrrhax's Citadel's gate, in the north wall
CAUSEWAY_END = (0.0, -470.0)  # where the Causeway comes in over the sea: the passage back


def natural(x, y):
    return L.natural(x, y)


route_points = L.route_points
wall_sd = L.wall_sd
pocket_at = L.pocket_at
lobe_weights = L.look_weights
look_at = L.look_at
tunnel_floor = L.tunnel_floor
RIVERS = []
LAKES = []
POOLS = []
LAVA = []
RIVER_HW = 9.0


def river_d(x, y):
    return 1e9, 0.0
