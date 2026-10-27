# Tropic Isles' layout (v3, on pocket_kit): pure geometry, no Blender (beach_region.py
# builds it).
# SPDX-License-Identifier: MIT
#
# Built like the other kingdoms' (Blake, Oct 26): a pocket for each of its worlds, walled
# off by jungle hills and rocky headlands (each beach cove open to the sea on its own
# side, the headlands between them reaching right out, so you see the ocean, not the next
# cove), the main road one loop through them (Raptor's 1-on-1), a threshold between each:
#
#   Raptor's village (hub, N)  boardwalks round a square on a jungle plateau; the Dust
#                              Road comes down into it from the desert, north
#     the Vine Tunnel    through the jungle ridge west, roots and vines
#   Splash (NW)       the water park in a jungle bowl, its slide tower
#     the Falls          behind a waterfall and down a cave, south
#   Shipwreck (SW)    a cove, wrecks on the beach, a pirate camp
#     the Hull           through a great wreck's hull lying across the headland
#   the Pier (S)      a cove, the long pier out towards Volcano Isle smoking offshore
#     the Sea Arch       through the headland's rock arch, east
#   Coral (SE)        a cove, coral heads in the shallows, beach huts (Tidewyrm's sea cave
#                     in its east headland, after his attack)
#     the Mangroves      a root tunnel through the mangrove ridge, north-west
#   the Lagoon (middle)  still water, sandbars, a boardwalk round it
#     the Tiki Steps     up a jungle ravine, torches, back to the village
#
# Blender coordinates (x east, y north, z up).

import math

from pocket_kit import Layout, catmull, lerp, smooth  # noqa: F401

TOP = 44.0
WATER_Z = -0.8
HUB = (0.0, 262.0, 24.0, 12.0)  # x, y, radius, height: the village square
VILLAGE = HUB
LAGOON = (92.0, -22.0, 40.0, -0.5)  # the lagoon's water: x, y, radius, height

POCKETS = [
    ("village", "village", [(0.0, 260.0, 55.0, 12.0), (45.0, 228.0, 30.0, 12.0), (-45.0, 230.0, 30.0, 12.0)]),
    # (the Dust Road, north, up to the desert)
    ("dust", "village", [(4.0, 330.0, 22.0, 13.0), (-6.0, 375.0, 21.0, 15.0), (6.0, 420.0, 21.0, 17.0),
                         (0.0, 462.0, 24.0, 19.0)]),
    ("splash", "splash", [(-228.0, 136.0, 60.0, 8.0), (-290.0, 72.0, 44.0, 7.0), (-182.0, 192.0, 34.0, 9.0)]),
    ("shipwreck", "shipwreck", [(-232.0, -92.0, 52.0, 1.4), (-172.0, -160.0, 38.0, 1.2), (-215.0, -175.0, 40.0, 0.8),
                                (-300.0, -205.0, 90.0, -6.0), (-390.0, -290.0, 90.0, -9.0)]),
    ("pier", "pier", [(0.0, -228.0, 50.0, 1.4), (58.0, -256.0, 34.0, 1.2), (-40.0, -258.0, 30.0, 1.0),
                      (0.0, -335.0, 88.0, -6.0), (0.0, -445.0, 90.0, -9.0)]),
    ("coral", "coral", [(230.0, -118.0, 52.0, 1.4), (178.0, -172.0, 40.0, 1.2), (250.0, -175.0, 40.0, 0.8),
                        (300.0, -205.0, 90.0, -6.0), (390.0, -290.0, 90.0, -9.0)]),
    ("lagoon", "lagoon", [(92.0, -22.0, 62.0, 1.0), (50.0, 20.0, 30.0, 1.4)]),
    ("steps", "village", [(80.0, 58.0, 24.0, 3.0), (60.0, 106.0, 22.0, 6.0), (82.0, 148.0, 22.0, 9.0),
                          (56.0, 190.0, 24.0, 11.0)]),
]

ROUTE = [
    (25.0, 225.0, None),  # 0: the start, south of the village square, westbound
    (-25.0, 222.0, None),
    (-60.0, 226.0, None),
    (-92.0, 218.0, 12.6),  # 3: the Vine Tunnel
    (-142.0, 205.0, 10.2),
    (-185.0, 198.0, None),  # 5: the water park
    (-226.0, 168.0, None),
    (-262.0, 130.0, None),
    (-230.0, 98.0, None),
    (-272.0, 64.0, None),
    (-304.0, 40.0, None),
    (-298.0, 8.0, 5.8),  # 11: the Falls
    (-282.0, -20.0, 4.2),
    (-262.0, -46.0, 2.8),
    (-234.0, -84.0, None),  # 14: Shipwreck's beach
    (-206.0, -138.0, None),
    (-246.0, -160.0, None),
    (-200.0, -182.0, None),
    (-160.0, -172.0, None),
    (-124.0, -190.0, 2.4),  # 19: the Hull
    (-76.0, -214.0, 2.4),
    (-42.0, -228.0, None),  # 21: the pier's cove
    (0.0, -212.0, None),
    (40.0, -244.0, None),
    (76.0, -252.0, None),
    (102.0, -236.0, 2.4),  # 25: the Sea Arch
    (142.0, -204.0, 2.4),
    (180.0, -182.0, None),  # 27: Coral's beach
    (226.0, -142.0, None),
    (262.0, -112.0, None),
    (232.0, -80.0, None),
    (192.0, -92.0, None),
    (162.0, -62.0, 2.0),  # 32: the Mangroves
    (138.0, -40.0, 1.8),
    (100.0, -10.0, None),  # 34: round the lagoon
    (58.0, 18.0, None),
    (80.0, 58.0, None),  # 36: the Tiki Steps
    (60.0, 106.0, None),
    (82.0, 148.0, None),
    (56.0, 190.0, None),
]
TUNNELS = [("Vine Tunnel", "vine", 3, 4), ("The Falls", "falls", 11, 13), ("The Hull", "hull", 19, 20),
           ("Sea Arch", "arch", 25, 26), ("The Mangroves", "mangrove", 32, 33)]

L = Layout(POCKETS, TOP, ROUTE, TUNNELS, hub=HUB, lakes=[LAGOON], roll=3.0, flat=("village", "lagoon"), mountains=30.0,
           water_floor=1.2)

GATES = {
    "splash": (-300.0, 124.0),  # the water park's slide tower
    "wreck": (-262.0, -150.0),  # the wrecked hull up the beach
    "volcano": (0.0, -306.0),  # the end of the pier, Volcano Isle offshore
    "coral": (262.0, -164.0),  # the coral heads in the shallows
}
LAIR = (306.0, -88.0)  # Tidewyrm's sea cave (the ruin's boss gateway), Coral's east headland
CAUSEWAY = (0.0, -300.0)  # Tidewyrm's Causeway (the ruin): out from the pier over the sea, south
CAUSEWAY_END = (0.0, -470.0)
VOLCANO = (40.0, -640.0)  # Volcano Isle, smoking offshore (seen from the pier's cove)
DUST_END = (0.0, 470.0)  # the Dust Road's far end: the passage back to the desert


def natural(x, y):
    return L.natural(x, y)


route_points = L.route_points
wall_sd = L.wall_sd
pocket_at = L.pocket_at
lobe_weights = L.look_weights
look_at = L.look_at
tunnel_floor = L.tunnel_floor
RIVERS = []
LAKES = [LAGOON]
POOLS = []
LAVA = []
RIVER_HW = 9.0


def river_d(x, y):
    return L.water_d(x, y)
