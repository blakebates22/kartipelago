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
HUB = (0.0, -131.4, 19.2, 3.0)  # x, y, radius, height: Dragonfire Square

POCKETS = [
    ("harbour", "harbour", [(0.0, -135.2, 42.9, 3.0), (34.1, -153.8, 23.7, 2.5), (-34.1, -153.8, 23.7, 2.5),
                            (-58.9, -132.7, 19.2, 4.0), (-31.0, -126.5, 19.2, 3.0), (0.0, -204.6, 65.1, -6.0), (0.0, -275.9, 66.6, -9.0)]),
    ("moon", "moon", [(-155.0, -24.8, 44.4, 14.0), (-186.0, 18.6, 29.6, 15.0), (-127.1, 11.2, 25.2, 14.0),
                      (-124.0, -67.0, 25.2, 10.0)]),
    ("climb", "keep", [(-176.7, 38.4, 16.3, 16.5), (-181.0, 50.8, 16.3, 18.0), (-162.4, 71.3, 15.5, 22.0), (-179.8, 93.0, 16.3, 26.0),
                       (-158.7, 109.1, 17.8, 29.0)]),
    ("keep", "keep", [(-124.0, 130.2, 41.4, 31.0), (-83.7, 156.2, 29.6, 32.0), (-162.4, 146.3, 25.2, 30.0)]),
    ("citadel", "citadel", [(-7.4, 181.0, 34.0, 35.0), (28.5, 186.0, 25.2, 35.0)]),
    ("hold", "hold", [(120.9, 112.8, 44.4, 22.0), (162.4, 75.6, 28.1, 20.0), (93.0, 143.8, 25.2, 28.0)]),
    ("storm", "hold", [(179.8, 50.8, 16.3, 18.0), (164.9, 24.8, 15.5, 15.0), (181.0, 0.0, 16.3, 13.0),
                       (166.2, -15.5, 17.8, 11.0)]),
    ("canyon", "canyon", [(151.9, -38.4, 41.4, 9.0), (178.6, -80.6, 28.1, 8.0), (127.1, -86.8, 25.2, 6.0), (148.8, -99.2, 22.2, 7.0)]),
]

ROUTE = [
    (12.4, -119.0, None),  # 0: the start, north of Dragonfire Square, westbound
    (-24.8, -121.5, None),
    (-57.6, -129.6, None),
    (-75.6, -117.8, 5.4),  # 3: the Dragon Gate
    (-105.4, -86.8, 8.6),
    (-127.1, -65.1, None),  # 5: Moonstone
    (-144.2, -44.5, None),
    (-142.9, -20.5, None),
    (-161.2, 0.0, None),
    (-177.8, 17.0, None),
    (-176.9, 36.4, None),
    (-177.1, 52.8, None),  # 11: the Climb
    (-169.3, 71.9, None),
    (-170.7, 91.6, None),
    (-158.7, 109.1, None),
    (-140.1, 124.0, None),  # 15: Dragonspire's town
    (-111.6, 143.8, None),
    (-81.8, 155.0, None),
    (-59.5, 163.7, 33.0),  # 18: the Keep Gate
    (-34.7, 173.6, 34.6),
    (-6.2, 182.3, None),  # 20: the Citadel's approach
    (24.8, 189.7, None),
    (49.6, 179.8, 33.6),  # 22: the Lava Tube
    (70.7, 162.4, 29.6),
    (93.0, 146.3, None),  # 24: Emberdeep
    (124.0, 124.0, None),
    (148.8, 99.2, None),
    (168.6, 76.9, None),
    (179.8, 50.8, None),  # 28: the Storm Pass
    (169.0, 25.0, None),
    (174.5, 2.3, None),
    (166.2, -15.5, None),
    (158.6, -38.8, None),  # 32: the Emerald Canyon
    (169.5, -63.4, None),
    (157.0, -84.5, None),
    (127.7, -86.8, None),
    (106.6, -101.7, 4.8),  # 36: the Root Tunnel
    (68.2, -130.2, 3.6),
    (39.7, -141.4, None),
]
TUNNELS = [("Dragon Gate", "gate", 3, 4), ("Keep Gate", "gate", 18, 19), ("Lava Tube", "lava", 22, 23),
           ("Root Tunnel", "roots", 36, 37)]

L = Layout(POCKETS, TOP, ROUTE, TUNNELS, hub=HUB, roll=3.5, flat=("harbour",), mountains=50.0, tiers=True)

GATES = {
    "keep": (-132.7, 164.9),  # Dragonspire Keep's tower on its crag
    "canyon": (204.6, -69.4),  # the overgrown jungle castle's gate
    "hold": (132.7, 147.6),  # Emberdeep Hold's fortress gate
    "moon": (-209.6, 11.2),  # the moon gate among the lanterns
}
CITADEL = (3.7, 209.6)  # King Pyrrhax's Citadel's gate, in the north wall
CAUSEWAY_END = (0.0, -291.4)  # where the Causeway comes in over the sea: the passage back


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
