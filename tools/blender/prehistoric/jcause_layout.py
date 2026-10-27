# Tidewyrm's Causeway: the journey from Tropic Isles over the sea to the Dragon Kingdom
# (its own section between the two). Pure geometry (journey_region.py builds it).
# SPDX-License-Identifier: MIT
#
# Out over the sea on the reef Tidewyrm raised:
#
#   the Reef         the causeway over the shallows, coral under the water
#     the Sea Cave   bored through a headland
#   the Stacks       a basin of sea stacks, the causeway weaving between them
#   the Isle         a rocky islet, a ruined lighthouse on its crest
#   the Ribs         a strait between two headlands, a sea serpent's giant ribs over it
#   the Crags        dark crags rising out of the sea, the road up onto the cliffs to the
#                    gate into the Dragon Kingdom
#
# Blender coordinates (x east, y north, z up). The route is a loop; the road only from
# START to END (the rest is out of sight over the mountains).

from pocket_kit import Layout, catmull, lerp, smooth  # noqa: F401

TOP = 44.0
HIDDEN_Z = 140.0
WATER_Z = -0.8
DECK = 2.6

POCKETS = [
    ("reef", "reef", [(0, 438, 18, -2.0), (8, 392, 36, -2.5), (-36, 324, 40, -3.0), (20, 272, 36, -3.0), (-18, 364, 26, -2.8)]),
    ("stacks", "stacks", [(92, 140, 40, -6.0), (56, 84, 40, -7.0), (108, 30, 36, -6.0)]),
    ("isle", "isle", [(92, -12, 26, 2.0), (66, -32, 28, 4.5), (20, -62, 28, 6.0), (-28, -36, 24, 3.0)]),
    ("strait", "strait", [(-56, -78, 22, -5.0), (-62, -120, 22, -5.0), (-48, -160, 22, -5.0)]),
    ("crags", "crags", [(-18, -208, 34, -6.0), (30, -250, 30, -1.0), (70, -300, 26, 5.0), (40, -350, 24, 9.0),
                        (70, -390, 22, 12.0), (78, -422, 16, 12.0), (56, -326, 18, 7.0)]),
]

ROUTE = [
    (0.0, 448.0, DECK),  # 0: lead-in (no road): Tropic Isles' end of the causeway
    (2.0, 400.0, DECK),  # 1: START, from Tropic Isles
    (-36.0, 330.0, DECK),
    (20.0, 270.0, DECK),
    (42.0, 228.0, DECK),  # 4: the Sea Cave
    (72.0, 178.0, DECK),
    (92.0, 140.0, DECK),  # 6: the Stacks
    (48.0, 86.0, DECK),
    (106.0, 30.0, DECK),
    (70.0, -28.0, None),  # 9: the Isle
    (20.0, -62.0, None),
    (-28.0, -34.0, None),
    (-58.0, -80.0, DECK),  # 12: the Ribs
    (-62.0, -122.0, DECK),
    (-46.0, -162.0, DECK),
    (-18.0, -208.0, DECK),  # 15: the Crags
    (30.0, -250.0, 3.0),
    (70.0, -300.0, None),
    (40.0, -350.0, None),
    (70.0, -390.0, None),  # 19: END, into the Dragon Kingdom
    (78.0, -424.0, None),  # 20: lead-out (no road)
    (120.0, -470.0, HIDDEN_Z),
    (400.0, -466.0, HIDDEN_Z),
    (466.0, 0.0, HIDDEN_Z),
    (400.0, 460.0, HIDDEN_Z),
    (100.0, 474.0, HIDDEN_Z),
]
START, END = 1, 19
HIDDEN = range(END + 2, len(ROUTE))
TUNNELS = [("Sea Cave", "cave", 4, 5)]
RIVERS = []
RIVER_HW = 9.0
LAKES = []
POOLS = []
LAVA = []

L = Layout(POCKETS, TOP, ROUTE, TUNNELS, roll=2.0, mountains=30.0, hidden=HIDDEN)

ENDS = {"start": ((2.0, 400.0), (0.0, 448.0)), "end": ((70.0, -390.0), (78.0, -424.0))}
GATES = {}
# Sea stacks in the basin (x, y, radius, height).
STACKS = [(62, 136, 7, 26), (120, 104, 6, 22), (28, 58, 8, 30), (84, 60, 5, 18), (132, 52, 7, 24), (70, 6, 5, 16),
          (-20, 300, 6, 20), (40, 330, 5, 16)]


def natural(x, y):
    return L.natural(x, y)


route_points = L.route_points
wall_sd = L.wall_sd
pocket_at = L.pocket_at
lobe_weights = L.look_weights
look_at = L.look_at
tunnel_floor = L.tunnel_floor


def river_d(x, y):
    return 1e9, 0.0
