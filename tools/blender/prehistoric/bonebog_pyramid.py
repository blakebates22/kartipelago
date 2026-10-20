# Bonebog Pyramid: Prehistoric World, course 3. A living swamp, a dinosaur graveyard
# and a colossal overgrown pyramid you drive straight through.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/bonebog_pyramid.py      (the bpy module)
#
# A lap of about 1.7 km, almost all of it raised above deep green swamp water (fall in
# and you're fished out at the last checkpoint), under a vast canopy of giant trees:
#
#   A  The Old Dike: the start, on a raised stone road along an earthen dike, heading
#      north through the ribs of a fallen giant.
#   B  The Boardwalks: railed wooden walkways winding east between giant trees, bone
#      piles and bubbling pools, under the canopy.
#   C  The Rib Bridge: a high trestle north across Rib Lagoon, straight through the
#      rib cage of a colossal skeleton, the pyramid revealed across the water.
#   D  The Grand Causeway: a raised stone causeway west across the lagoon, straight at
#      the pyramid's carved face and its waterfalls.
#   E  The Pyramid: about ten seconds inside: a torchlit entry corridor, a turning
#      chamber, the Great Hall (pillars, waterfalls from the roof, shafts of light) and
#      out of the south face.
#   F  Skull Lagoon: a high trestle down past a colossal skull, then winding
#      mangrove boardwalks under the treehouse village, and home along the dike.
#
# The pyramid stands on a stone foundation rising out of the swamp: 190 x 210 m at
# its base and 90 m tall. Every corner is a 45-55 m arc. Saves
# tracks-src/bonebog_pyramid.blend and exports public/tracks/bonebog_pyramid/. The
# scenery is bonebog_scenery.py, built from the swamp kit in swamp_props.py.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp, smooth  # noqa: E402

TRACK_ID = "bonebog_pyramid"
WATER_Z = 0.0

# ---------------------------------------------------------------- the layout

START = (0.0, -200.0)
LAYOUT = [
    ("S", 135),  # 0  A: the start straight, north along the dike
    ("R", 50, 90),  # 1  east onto the boardwalks
    ("S", 30),  # 2  B
    ("L", 45, 55),  # 3  between the giant trees...
    ("R", 45, 55),  # 4
    ("S", 40),  # 5
    ("L", 55, 90),  # 6  north, climbing
    ("S", 90),  # 7  C: the Rib Bridge
    ("L", 55, 90),  # 8  west, the pyramid ahead
    ("S", 90),  # 9  D: the Grand Causeway
    ("R", 120, 20),  # 10
    ("L", 120, 20),  # 11
    ("S", 40),  # 12 up to the carved face
    ("S", 75),  # 13 E: the entry corridor
    ("L", 45, 90),  # 14 the turning chamber
    ("S", 60),  # 15 the Great Hall, and out of the south face
    ("S", 30),  # 16 F: the trestle down into Skull Lagoon
    ("R", 45, 50),  # 17
    ("L", 45, 100),  # 18 round the skull
    ("R", 45, 50),  # 19
    ("S", 40),  # 20 (stretched to close the loop)
    ("L", 50, 40),  # 21 the mangrove boardwalks
    ("R", 50, 80),  # 22
    ("L", 50, 40),  # 23
    ("S", 25),  # 24
    ("L", 45, 90),  # 25 east, back onto the dike
    ("S", 30),  # 26 (stretched to close the loop)
    ("L", 45, 90),  # 27 north onto the start
    ("S", 10),  # 28
]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 20, 26, START, 90.0)
SEG = kit.segment_starts(PATH)
LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))

# The pyramid: centred on the entry corridor's line, its east face where the corridor
# begins and its south face where the Great Hall comes out.
_entry = next(p for p in PATH if p[3] == 13)
PYR_HX, PYR_HY = 95.0, 105.0
PYR = (_entry[0] - PYR_HX, _entry[1])
FOUND_Z = 6.5  # the top of the stone foundation the pyramid stands on
FOUND_PAD = 16.0  # how far the foundation reaches beyond the pyramid
# Tiers: (half-size inset, top height). The lowest is tallest: the doorways are in it.
TIERS = [(0.0, 22.5), (12.0, 33.5), (24.0, 44.5), (36.0, 55.5), (48.0, 66.5), (60.0, 77.5)]
SHRINE = (10.0, 12.0, 12.0)  # half-sizes and height of the shrine on top
INSIDE = (SEG[13], SEG[16])  # the route inside the pyramid

# Heights along the lap (metres along it, height); the road eases between them.
ANCHORS = [
    (0.0, 2.6),
    (SEG[1] + 20, 2.6),
    (SEG[2] + 10, 4.0),
    (SEG[6], 4.5),
    (SEG[7] + 5, 12.0),
    (SEG[8] - 5, 12.0),
    (SEG[9] + 30, 8.5),
    (SEG[12], 8.5),
    (SEG[13], 8.6),
    (SEG[16], 9.6),
    (SEG[17] + 10, 7.0),
    (SEG[19] + 10, 4.2),
    (SEG[24] + 20, 3.8),
    (SEG[26], 2.6),
    (LENGTH, 2.6),
]


def _lin(d):
    d = min(max(d, 0.0), LENGTH)
    for (d0, z0), (d1, z1) in zip(ANCHORS, ANCHORS[1:]):
        if d0 <= d <= d1:
            return lerp(z0, z1, (d - d0) / max(1e-6, d1 - d0))
    return ANCHORS[-1][1]


def road_z(d, seg):
    # Smoothed over 30 m, so grades change gently.
    return sum(_lin(d + k) for k in range(-15, 16, 3)) / 11


def road_w(d, seg):
    if 13 <= seg <= 15:
        return 16.0  # inside the pyramid
    if seg in (0, 27, 28):
        return 16.0  # the dike
    if seg in (7, 8, 9, 10, 11, 12):
        return 15.0  # the bridge and the causeway
    return 14.5  # boardwalks


ROUTE = kit.route_points_by(PATH, road_z, every=12.0, width=road_w)

# ---------------------------------------------------------------- the land


def sm(t):
    return smooth(max(0.0, min(1.0, t)))


def in_pyramid(x, y, pad=0.0):
    return abs(x - PYR[0]) < PYR_HX + pad and abs(y - PYR[1]) < PYR_HY + pad


def on_foundation(x, y, pad=0.0):
    return in_pyramid(x, y, FOUND_PAD + pad)


def pyramid_top(x, y):
    """The height of the pyramid's stepped surface over (x, y) (None outside it)."""
    e = min(PYR_HX - abs(x - PYR[0]), PYR_HY - abs(y - PYR[1]))
    if e < 0:
        return None
    z = FOUND_Z
    for inset, top in TIERS:
        if e >= inset:
            z = top
    return z


# The old dike the start runs along: an earthen bank under the road from the end of
# the mangroves round to the start straight, (x, y, half-width of its top).
def _dike_line():
    out = []
    d = 0.0
    nxt = 0.0
    for i, (x, y, _, seg) in enumerate(PATH):
        if i:
            d += math.hypot(x - PATH[i - 1][0], y - PATH[i - 1][1])
        if d >= nxt:
            if d >= SEG[25] + 10:
                out.append((x, y, 20.0))
            nxt += 15.0
    d = 0.0
    nxt = 0.0
    for i, (x, y, _, seg) in enumerate(PATH):
        if i:
            d += math.hypot(x - PATH[i - 1][0], y - PATH[i - 1][1])
        if d > SEG[1] + 15:
            break
        if d >= nxt:
            out.append((x, y, 20.0 if d < SEG[1] else 12.0))
            nxt += 15.0
    return out


DIKE = _dike_line()


def _nearest(px, py, pts):
    best = (1e9, 0, 0.0)
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        ax, ay, bx, by = a[0], a[1], b[0], b[1]
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        d = math.hypot(px - ax - t * dx, py - ay - t * dy)
        if d < best[0]:
            best = (d, i, t)
    return best


def dike(x, y):
    """The dike's height (its top at 2.2 m, sloping into the water), or -inf."""
    d, i, t = _nearest(x, y, DIKE)
    hw = lerp(DIKE[i][2], DIKE[i + 1][2], t)
    return 2.2 - 3.4 * sm((d - hw) / 14.0) - 1.6 * sm((d - hw - 14) / 10)


# Mud islands in the swamp (x, y, radius): root mounds for the giant trees, bone banks.
ISLANDS = [
    (60, -120, 26), (-60, -110, 30), (-60, -190, 24), (90, 60, 22), (170, -60, 26), (230, -40, 24),
    (160, 120, 30), (320, 30, 30), (310, 160, 26), (120, 190, 22), (-230, 60, 30), (-220, -60, 28),
    (-210, -170, 26), (-70, 40, 26), (40, -230, 18), (230, 300, 30), (40, 330, 26),
]


# Keep the water open beside the road: no islands within 30 m of it.
ISLANDS = [(x, y, r) for x, y, r in ISLANDS if min(math.hypot(x - p[0], y - p[1]) for p in PATH[::4]) > r + 30]


def natural(x, y):
    """The swamp bed: deep under the water, with mud islands, the dike and, all round,
    the jungle rising on low hills."""
    h = -3.6 + 0.7 * math.sin(x / 19) * math.cos(y / 23) + 0.5 * math.sin((x - y) / 37)
    for ix, iy, r in ISLANDS:
        d = math.hypot(x - ix, y - iy)
        if d < r + 16:
            h = max(h, 1.0 + 0.6 * math.sin(x / 7 + y / 5) - 4.6 * sm((d - r * 0.55) / (r * 0.45 + 16)))
    h = max(h, dike(x, y))
    # The jungle all round, on rising ground.
    r = math.hypot((x - 20) / 1.0, (y - 30) / 1.12)
    rim = 300 + 25 * math.sin(math.atan2(y - 30, x - 20) * 5 + 1)
    h = max(h, -4 + 34 * sm((r - rim) / 60))
    return h


def classify(c, n, info):
    if on_foundation(c.x, c.y, -2):
        return None  # under the pyramid's foundation
    if c.z < WATER_Z - 0.4:
        return ("bog_mud", "mud")  # the swamp bed, under the water
    if n.z < 0.62:
        return ("bog_root", "wall")
    if info["d"] < 13 and c.z > 1.5:
        return ("bog_moss_ground", "grass")
    return ("bog_bank", "grass")


# ---------------------------------------------------------------- the course


def seg_of(s):
    k = 0
    for i, d in SEG.items():
        if d <= s:
            k = max(k, i)
    return k


def main():
    c = kit.Course(TRACK_ID, "Bonebog Pyramid", "bonebog_swamp")
    c.route(ROUTE, width=15.0, bank=6.0)
    rail = ("bog_rail", "wall")
    stone_rail = ("bog_carved", "wall")
    c.kinds = {
        "dike": {"mat": "bog_paving", "shoulder": 1.8, "shoulder_mat": ("bog_moss_ground", "dirt"), "barrier": 0.7, "barrier_mat": ("bog_stone", "wall")},
        "boardwalk": {
            "mat": "bog_boards",
            "shoulder": 0.5,
            "shoulder_mat": ("bog_boards", "road"),
            "barrier": 1.2,
            "barrier_mat": rail,
            "deck": 2.4,
            "deck_mat": ("bog_root", "wall"),
            "ground": False,
        },
        "bridge": {
            "mat": "bog_boards",
            "shoulder": 0.6,
            "shoulder_mat": ("bog_boards", "road"),
            "barrier": 1.3,
            "barrier_mat": rail,
            "deck": 3.0,
            "deck_mat": ("bog_root", "wall"),
            "ground": False,
        },
        "causeway": {
            "mat": "bog_paving",
            "shoulder": 1.0,
            "shoulder_mat": ("bog_stone", "road"),
            "barrier": 1.3,
            "barrier_mat": stone_rail,
            "deck": 12.0,
            "deck_mat": ("bog_stone", "wall"),
            "ground": False,
        },
        "temple": {"mat": "bog_paving", "shoulder": 2.5, "shoulder_mat": ("bog_dark_stone", "road")},
    }

    def label(smp):
        s = smp.s
        seg = seg_of(s)
        if INSIDE[0] - 2 <= s <= INSIDE[1] + 2:
            return "temple"
        if seg in (0, 27, 28) or (seg == 1 and s < SEG[1] + 20) or (seg == 26):
            return "dike"
        if seg in (9, 10, 11, 12) or (seg == 8 and s > SEG[9] - 30):
            return "causeway"
        if seg in (7, 8) or (seg == 6 and s > SEG[6] + 40) or seg in (16, 17):
            return "bridge"
        return "boardwalk"

    specials = [(s0, s1, k) for s0, s1, k in kit.runs(c, label) if k != "boardwalk"]
    c.roads(kit.plan(c, specials, "boardwalk", max_len=200.0))

    X0, X1, Y0, Y1 = -360, 400, -360, 450
    c.terrain("Swamp", X0, X1, Y0, Y1, 6.0, natural, classify, near=10.0, fade=16.0, under=0.2)
    # The swamp water: deep and murky. Fall in and you're fished out.
    c.disc("Swamp Water", 20, 40, 520, WATER_Z, c.lib("bog_water", "deep_water"), n=64)

    import bonebog_scenery  # noqa: E402

    pyr = bonebog_scenery.pyramid(c, sys.modules[__name__])

    c.start_line()
    # Zippers: off the start, at the top of the climb to the Rib Bridge, on the causeway
    # and down the trestle out of the pyramid.
    c.zipper(55, 0)
    c.zipper(SEG[7] + 20, 0)
    c.zipper(SEG[9] + 40, 0)
    c.zipper(SEG[16] + 22, 0)
    for at, across in ((95, -3), (SEG[3] + 20, 0), (SEG[7] + 70, 2), (SEG[10] + 20, 0), (SEG[13] + 40, 0), (SEG[15] + 20, -2), (SEG[18] + 40, 0), (SEG[22] + 30, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (130, -4, "red"),
        (130, 4, "blue"),
        (SEG[5] + 15, 0, "green"),
        (SEG[8] + 30, 0, "yellow"),
        (SEG[14] + 30, -4, "rainbow"),
        (SEG[14] + 30, 4, "red"),
        (SEG[19] + 20, 0, "blue"),
        (SEG[23] + 20, 0, "green"),
    ):
        c.balloon(at, across, col)

    c.checkpoints(
        extra=[SEG[2] + 10, SEG[5], SEG[7] + 45, SEG[9] + 20, SEG[13] + 10, SEG[15] + 10, SEG[17] + 20, SEG[21] + 10, SEG[24]],
        height=10.0,
    )

    bonebog_scenery.build(c, pyr, sys.modules[__name__])

    kit.paint.shade_roads(c.pieces, 0.35)
    c.finish()


if __name__ == "__main__":
    main()
