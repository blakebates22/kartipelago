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
HUB = (0.0, 162.4, 19.2, 12.0)  # x, y, radius, height: the village square
VILLAGE = HUB
LAGOON = (57.0, -13.6, 24.8, -0.5)  # the lagoon's water: x, y, radius, height

POCKETS = [
    ("village", "village", [(0.0, 161.2, 40.7, 12.0), (27.9, 141.4, 22.2, 12.0), (-27.9, 142.6, 22.2, 12.0)]),
    # (the Dust Road, north, up to the desert)
    ("dust", "village", [(2.5, 204.6, 16.3, 13.0), (-3.7, 232.5, 15.5, 15.0), (3.7, 260.4, 15.5, 17.0),
                         (0.0, 286.4, 17.8, 19.0)]),
    ("splash", "splash", [(-141.4, 84.3, 44.4, 8.0), (-179.8, 44.6, 32.6, 7.0), (-112.8, 119.0, 25.2, 9.0)]),
    ("shipwreck", "shipwreck", [(-143.8, -57.0, 38.5, 3.9), (-106.6, -99.2, 28.1, 3.7), (-133.3, -108.5, 29.6, 3.3),
                                (-186.0, -127.1, 55.8, -6.0), (-241.8, -179.8, 55.8, -9.0)]),
    ("pier", "pier", [(0.0, -141.4, 37.0, 3.9), (36.0, -158.7, 25.2, 3.7), (-24.8, -160.0, 22.2, 3.5),
                      (0.0, -207.7, 54.5, -6.0), (0.0, -275.9, 55.8, -9.0)]),
    ("coral", "coral", [(142.6, -73.2, 38.5, 3.9), (110.4, -106.6, 29.6, 3.7), (155.0, -108.5, 29.6, 3.3),
                        (186.0, -127.1, 55.8, -6.0), (241.8, -179.8, 55.8, -9.0)]),
    ("lagoon", "lagoon", [(57.0, -13.6, 45.9, 1.0), (31.0, 12.4, 22.2, 1.4)]),
    ("steps", "village", [(49.6, 36.0, 17.8, 3.0), (37.2, 65.7, 16.3, 6.0), (50.8, 91.8, 16.3, 9.0),
                          (34.7, 117.8, 17.8, 11.0)]),
]

ROUTE = [
    (15.5, 139.5, None),  # 0: the start, south of the village square, westbound
    (-15.5, 137.6, None),
    (-37.2, 140.1, None),
    (-57.0, 135.2, 12.6),  # 3: the Vine Tunnel
    (-88.0, 127.1, 10.2),
    (-114.7, 122.8, None),  # 5: the water park
    (-140.1, 104.2, None),
    (-153.5, 81.5, None),
    (-153.3, 60.6, None),
    (-168.6, 39.7, None),
    (-185.2, 24.1, None),
    (-184.8, 5.0, 5.8),  # 11: the Falls
    (-174.8, -12.4, 4.2),
    (-162.4, -28.5, 2.8),
    (-145.1, -52.1, None),  # 14: Shipwreck's beach
    (-136.5, -80.8, None),
    (-132.5, -95.8, None),
    (-120.3, -106.7, None),
    (-99.2, -106.6, None),
    (-76.9, -117.8, 2.4),  # 19: the Hull
    (-47.1, -132.7, 2.4),
    (-26.0, -141.4, None),  # 21: the pier's cove
    (-0.1, -133.6, None),
    (24.8, -151.3, None),
    (47.1, -156.2, None),
    (63.2, -146.3, 2.4),  # 25: the Sea Arch
    (88.0, -126.5, 2.4),
    (111.6, -112.8, None),  # 27: Coral's beach
    (140.0, -94.0, 1.6),
    (160.0, -74.0, 1.9),
    (150.5, -51.6, None),
    (124.0, -48.0, None),
    (100.4, -38.4, 2.0),  # 32: the Mangroves
    (85.6, -24.8, 1.8),
    (62.0, -6.2, None),  # 34: round the lagoon
    (46.6, 13.3, None),
    (47.9, 36.4, None),  # 36: the Tiki Steps
    (39.0, 65.5, None),
    (48.7, 91.8, None),
    (34.7, 117.8, None),
]
TUNNELS = [("Vine Tunnel", "vine", 3, 4), ("The Falls", "falls", 11, 13), ("The Hull", "hull", 19, 20),
           ("Sea Arch", "arch", 25, 26), ("The Mangroves", "mangrove", 32, 33)]

L = Layout(POCKETS, TOP, ROUTE, TUNNELS, hub=HUB, lakes=[LAGOON], roll=3.0, flat=("village", "lagoon"), mountains=30.0,
           water_floor=1.2, tiers=True)

GATES = {
    "splash": (-186.0, 76.9),  # the water park's slide tower
    "wreck": (-162.4, -93.0),  # the wrecked hull up the beach
    "volcano": (0.0, -189.7),  # the end of the pier, Volcano Isle offshore
    "coral": (130.0, -128.0),  # the coral heads in the shallows
}
LAIR = (189.7, -54.6)  # Tidewyrm's sea cave (the ruin's boss gateway), Coral's east headland
CAUSEWAY = (0.0, -186.0)  # Tidewyrm's Causeway (the ruin): out from the pier over the sea, south
CAUSEWAY_END = (0.0, -291.4)
VOLCANO = (24.8, -396.8)  # Volcano Isle, smoking offshore (seen from the pier's cove)
DUST_END = (0.0, 291.4)  # the Dust Road's far end: the passage back to the desert


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
