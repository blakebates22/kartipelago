# The Snow Kingdom's layout (v3, on pocket_kit): pure geometry, no Blender (snow_region.py
# builds it).
# SPDX-License-Identifier: MIT
#
# Built like Dinosaur Valley's (Blake, Oct 26): a pocket for each of the kingdom's worlds,
# walled off by the mountains so you only see the one you're in, and the main road one
# winding loop through them (Brachio's 1-on-1), a threshold between each:
#
#   Hearthglow (hub)  the village in its hollow, warm lights, the great tree; the Burnt
#                     Gorge comes up into it from the valley, south
#     the Gatehouse     through Frostveil's curtain wall, a portcullis at each end
#   Frostveil (W)     the citadel's bailey: battlements, towers, the keep's gate
#     the Climb         a switchback ravine up out of the bailey, north
#   Summit (NW)       the high meadow under the giant tree, mammoths, snowy pines (Rimefang's
#                     lair in its north wall, after his attack)
#     the Ice Cave      bored through the glacier's tongue, blue light in its walls
#   Aurora (NE)       the glacier: blue ice, crevasses, the rift, the sky alight
#     the Snowshed      down a timber avalanche gallery cut into the cliff, the frozen lake
#                       below (the one view of another world: down the hill)
#   the Lake (E)      the frozen lake, the Ice Bells' hut on its shore, the Frozen Pass out
#                     east to Desert World (after Rimefang falls)
#     the Frozen Falls  up a tunnel behind a frozen waterfall, back into the village
#
# Blender coordinates (x east, y north, z up).

import math

from pocket_kit import Layout, catmull, lerp, smooth  # noqa: F401

TOP = 78.0
HUB = (0.0, -244.0, 26.0, 20.0)  # x, y, radius, height: the village square
VILLAGE = HUB
LAKE = (115.0, -88.0, 52.0, 12.0)  # the frozen lake's ice: x, y, radius, height

POCKETS = [
    ("hearth", "hearth", [(0.0, -240.0, 58.0, 20.0), (40.0, -200.0, 30.0, 20.0), (-45.0, -205.0, 32.0, 20.0)]),
    # (the Burnt Gorge, south, down to the valley's passage)
    ("gorge", "hearth", [(4.0, -330.0, 20.0, 18.0), (-6.0, -375.0, 19.0, 16.0), (6.0, -420.0, 19.0, 14.0),
                         (0.0, -462.0, 22.0, 12.0)]),
    ("frostveil", "frostveil",
     [(-235.0, -120.0, 62.0, 26.0), (-290.0, -50.0, 52.0, 28.0), (-190.0, -190.0, 36.0, 25.0),
      (-300.0, 30.0, 40.0, 32.0)]),
    ("climb", "summit",
     [(-298.0, 68.0, 22.0, 35.0), (-305.0, 95.0, 25.0, 38.0), (-280.0, 132.0, 23.0, 44.0), (-300.0, 172.0, 24.0, 50.0),
      (-262.0, 208.0, 25.0, 54.0)]),
    ("summit", "summit",
     [(-150.0, 230.0, 72.0, 58.0), (-60.0, 270.0, 52.0, 58.0), (-225.0, 255.0, 45.0, 56.0),
      (-90.0, 190.0, 40.0, 57.0)]),
    ("aurora", "aurora",
     [(190.0, 170.0, 70.0, 44.0), (260.0, 100.0, 50.0, 42.0), (135.0, 245.0, 42.0, 48.0),
      (278.0, 30.0, 34.0, 40.0)]),
    ("snowshed", "aurora",
     [(302.0, -22.0, 25.0, 34.0), (306.0, -68.0, 24.0, 27.0), (284.0, -110.0, 24.0, 20.0),
      (250.0, -140.0, 26.0, 15.0)]),
    ("lake", "lake",
     [(115.0, -88.0, 78.0, 12.0), (185.0, -45.0, 40.0, 12.0), (200.0, -128.0, 40.0, 12.0),
      (70.0, -140.0, 36.0, 12.0)]),
]

ROUTE = [
    (25.0, -205.0, None),  # 0: the start, the village's north side, westbound
    (-30.0, -200.0, None),
    (-72.0, -212.0, 20.3),
    (-96.0, -210.0, 20.6),  # 3: the Gatehouse
    (-138.0, -200.0, 23.4),
    (-176.0, -186.0, None),  # Frostveil's bailey
    (-222.0, -152.0, None),
    (-262.0, -118.0, None),
    (-246.0, -72.0, None),
    (-290.0, -40.0, None),
    (-312.0, 4.0, None),
    (-286.0, 44.0, None),
    (-305.0, 95.0, None),  # 12: the Climb
    (-276.0, 132.0, None),
    (-300.0, 172.0, None),
    (-262.0, 208.0, None),
    (-214.0, 246.0, None),  # 16: the summit meadow
    (-165.0, 272.0, None),
    (-148.0, 214.0, None),
    (-100.0, 186.0, None),
    (-62.0, 228.0, None),
    (-40.0, 276.0, None),
    (-4.0, 282.0, 57.0),  # 22: the Ice Cave
    (42.0, 270.0, 53.0),
    (86.0, 255.0, 49.0),
    (130.0, 240.0, None),  # 25: the glacier
    (176.0, 214.0, None),
    (222.0, 180.0, None),
    (196.0, 130.0, None),
    (240.0, 94.0, None),
    (284.0, 108.0, None),
    (292.0, 50.0, None),
    (270.0, 14.0, None),
    (302.0, -22.0, None),  # 33: the Snowshed, down the cliff
    (306.0, -68.0, None),
    (282.0, -112.0, None),
    (248.0, -142.0, None),
    (204.0, -146.0, None),  # 37: the lake
    (178.0, -100.0, None),
    (160.0, -40.0, None),
    (110.0, -26.0, None),
    (62.0, -66.0, None),
    (62.0, -122.0, None),
    (96.0, -158.0, None),
    (90.0, -188.0, 15.6),  # 44: the Frozen Falls
    (60.0, -212.0, 19.0),
]
TUNNELS = [("Gatehouse", "gatehouse", 3, 4), ("Ice Cave", "ice", 22, 24), ("Frozen Falls", "icefall", 44, 45)]

L = Layout(POCKETS, TOP, ROUTE, TUNNELS, hub=HUB, roll=4.0, flat=("hearth", "lake"), mountains=50.0)

# The gateways' landmarks (x, y), each at the end of a short spur off the road.
GATES = {
    "hearthglow": (-64.0, -182.0),  # the village's great tree
    "frostveil": (-342.0, -62.0),  # the keep's gate in the bailey's west wall
    "summit": (-250.0, 288.0),  # the giant tree
    "aurora": (318.0, 104.0),  # the rift in the glacier
}
LAIR = (-110.0, 318.0)  # Rimefang's lair (the ruin's boss gateway), the summit's north wall
FROZEN_PASS = (246.0, -170.0)  # where the Frozen Pass leaves the lake (the ruin), on east
PASS_END = (420.0, -190.0)
GORGE_END = (0.0, -470.0)  # the Burnt Gorge's far end: the passage back to the valley


def natural(x, y):
    """The land, with the frozen lake's ice laid level in its hollow."""
    h = L.natural(x, y)
    lx, ly, lr, lz = LAKE
    d = math.hypot(x - lx, y - ly)
    if d < lr + 14:
        h = lerp(lz - 0.4, h, smooth((d - lr) / 14.0))
    return h


# (The names the checker and the build read.)
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
