# Celestial Dragon Festival: Dragon Kingdom, course 4, painted as the Moonstone Kingdom
# (Blake's two boards, Oct 25): a moonlit violet kingdom under a huge moon.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/celestial_dragon_festival.py      (the bpy module)
#
# The v3 greybox's lap (it was celestial_dragon_festival_v3.py), exactly: the same roads,
# heights, widths, the Star Leap, surfaces, barriers, pickups and checkpoints. moon_scenery.py
# dresses it with keep_props.py's castle kit in moonstone (a palette swap); moon_textures.py
# is the paint.
#
#   1  The Moonstone Gate: the start, east along the gate's terrace.
#   2  The lantern town: a chicane down through its streets to the lake.
#   3  The Lake Bridge: north over the glowing lake on a long S, then S-bends up the
#      shore past ruined arches.
#   4  The Palace Courtyard: a loop right round the winged dragon's fountain, climbing,
#      that crosses over its own way in.
#   5  The Crystal Climb: west, up the north face in big S-bends past crystal outcrops.
#   6  The Star Bridge and the Star Leap: west along the bridge over the Cloud Chasm, the
#      floating islands round it, up the ramp and off the broken end (miss it and you're
#      put back on the landing).
#   7  The Observatory Spiral: right, round the pinnacle and its great armillary sphere.
#   8  The Palace Terraces: south, a weave through the upper gardens under the palace and
#      the purple dragon on its tower.
#   9  The Procession Causeway: the broad way down, crescent banners either side.
#  10  The Overlook and the Final Ascension: along the cliff's edge, a rise round the
#      bastion, and down onto the straight to the line.
#
# The first lap is kept as celestial_dragon_festival_v2.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import ruin_mode  # noqa: E402
from course_kit import lerp, smooth  # noqa: E402

# The ruin (celestial_dragon_festival_ruins.py): the Chosen One's sacrifice split the
# Palace Mount. From the gate the lap turns north into the split and runs up through the
# mount's broken heart, west along the chasm's edge (a crack the blast tore across it: a
# leap), and down the terraces and the causeway home. About half the lap. Everything else
# is the course's own.
RUIN = ruin_mode.ON
TRACK_ID = "celestial_dragon_festival_ruin" if RUIN else "celestial_dragon_festival"

K = 1.13
START = (0.0, 0.0)
_PLAN = [
    ("S", 60),  # 0  1: the Festival Gate, east
    ("R", 35, 45),  # 1  2: the Lantern Market chicane...
    ("L", 30, 90),  # 2
    ("R", 30, 45),  # 3  ...down to the water
    ("S", 20),  # 4
    ("L", 60, 40),  # 5  3: the Waterfall Bridge, a long S over the lagoon
    ("S", 40),  # 6
    ("R", 60, 40),  # 7
    ("L", 50, 90),  # 8  north
    ("S", 40),  # 9  (closes the lap)
    ("L", 40, 40),  # 10 S-bends up the shore
    ("R", 40, 80),  # 11
    ("L", 40, 40),  # 12
    ("S", 20),  # 13
    ("R", 28, 270),  # 14 4: the loop round the Great Dragon Shrine, over its way in
    ("S", 30),  # 15
    ("R", 50, 70),  # 16 5: the Celestial Climb, west
    ("L", 50, 140),  # 17
    ("R", 50, 70),  # 18
    ("L", 45, 50),  # 19
    ("R", 45, 100),  # 20
    ("L", 45, 50),  # 21
    ("S", 90),  # 22 6: the Star Bridge and the Star Leap (closes the lap)
    ("R", 28, 270),  # 23 7: the Observatory Spiral, out over the Star Bridge's end
    ("S", 30),  # 24
    ("L", 35, 60),  # 25 8: the Palace Terraces, a weave south
    ("R", 35, 120),  # 26
    ("L", 35, 60),  # 27
    ("S", 80),  # 28 9: the Procession Causeway, down
    ("L", 40, 40),  # 29 10: the Fireworks Overlook...
    ("R", 40, 40),  # 30
    ("L", 40, 90),  # 31 ...round the bastion onto the straight
    ("S", 20),  # 32
]
LAYOUT = [(s[0], s[1] * K) if s[0] == "S" else (s[0], s[1] * K, s[2]) for s in _PLAN]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 9, 22, START, 0.0)
SEG = kit.segment_starts(PATH)
LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))

# The Star Leap: (lip, landing), two thirds of the way along the Star Bridge.
LIP = SEG[22] + 0.62 * (SEG[23] - SEG[22]) - 7.0
LAND = LIP + 10.0

HEIGHT = {
    0: 20.0, 1: 19.0, 2: 15.0, 3: 10.0, 4: 6.5, 5: 5.5, 6: 5.5, 7: 6.0, 8: 7.0, 9: 8.0, 10: 9.0,
    11: 10.0, 12: 11.0, 13: 12.0, 14: 12.5, 15: 24.0, 16: 26.0, 17: 31.0, 18: 37.0, 19: 41.0,
    20: 44.0, 21: 46.5, 22: 48.0, 23: 48.0, 24: 63.0, 25: 62.0, 26: 61.0, 27: 60.0, 28: 59.0,
    29: 40.0, 30: 37.0, 31: 37.5, 32: 26.0,
}
CRESTS = {6: (1, 1.0), 11: (1, 0.8), 17: (1, 1.0), 20: (1, 1.0), 26: (1, 0.8), 28: (2, 1.4), 31: (1, 1.5)}


def seg_of(s):
    k = 0
    for i, d in SEG.items():
        if d <= s:
            k = max(k, i)
    return k


def _base_z(d, seg):
    a, b = SEG[seg], SEG.get(seg + 1, LENGTH)
    t = (d - a) / max(1e-6, b - a)
    z0, z1 = HEIGHT[seg], HEIGHT.get(seg + 1, HEIGHT[0])
    z = lerp(z0, z1, t if seg in (14, 23) else smooth(t))
    if seg in CRESTS:
        n, h = CRESTS[seg]
        z += h * math.sin(t * math.pi * n) ** 2
    return z


# The Star Leap: up the ramp, the gap, a landing in a dip 3 m below the road.
road_z = kit.with_jumps(_base_z, seg_of, [(LIP, LAND, 3.0, 1.2)], run=14.0)
# (The standard lap: the kingdom's landmarks are laid out from it, in the ruin too.)
STD_LAYOUT, STD_PATH, STD_SEG, STD_LENGTH, STD_HEIGHT = LAYOUT, PATH, SEG, LENGTH, HEIGHT


def road_w(d, seg):
    if RUIN and LAYOUT is not STD_LAYOUT:
        if seg in (0, 10) or d < 40:
            return 20.0
        return 17.0 if seg in (2, 4) else 16.0
    if seg in (0, 32) or d < 40:
        return 20.0
    if seg in (14, 23):
        return 15.0  # the loop and the spiral
    if seg in (1, 2, 3):
        return 15.0  # the market
    if seg == 28:
        return 20.0  # the causeway
    return 16.0


ROUTE = kit.route_points_by(PATH, road_z, every=8.0, width=road_w)
# The plan's distances (SEG, the jumps) are flat; the course measures along the road,
# which is longer where it climbs. These convert.
TO_ROAD, TO_PLAN = kit.along(PATH, road_z)


def _seg_point(i):
    return next(p for p in STD_PATH if p[3] == i)


def _arc_centre(i):
    x, y, h, _ = _seg_point(i)
    sg = STD_LAYOUT[i]
    a = math.radians(h + (90 if sg[0] == "L" else -90))
    return (x + sg[1] * math.cos(a), y + sg[1] * math.sin(a))


SHRINE = _arc_centre(14)  # the golden dragon, inside the loop
PINNACLE = _arc_centre(23)  # the observatory, inside the spiral
MOUNT = (sum(p[0] for p in STD_PATH) / len(STD_PATH), sum(p[1] for p in STD_PATH) / len(STD_PATH))
_lp = next(p for p in STD_PATH if p[3] == 22)
CHASM_Y = _lp[1]  # the Cloud Chasm, along under the Star Bridge
LAGOON_X = max(p[0] for p in STD_PATH if p[3] in (3, 4)) - 10.0

# ---------------------------------------------------------------- the ruin's lap

NEW = []  # (the ruin) [(x, y, z)] along its new road: the land meets it
CRACK = None  # (the ruin) the crack across the chasm's edge the lap leaps: (x, y)
if RUIN:
    LAYOUT = [STD_LAYOUT[0]] + [
        ("L", 50.0, 90),  # 1  north from the gate
        ("S", 250.0),  # 2  up through the split mount
        ("L", 50.0, 90),  # 3  west
        ("S", 117.0),  # 4  along the chasm's edge: the leap (closes the loop)
        ("L", 40.0, 90),  # 5  south
        ("S", 207.0),  # 6  down past the terraces (closes the loop)
    ] + list(STD_LAYOUT[29:])  # 7-10: the overlook, round the bastion, the line
    LAYOUT, PATH = kit.close_turtle(LAYOUT, 4, 6, START, 0.0)
    SEG = kit.segment_starts(PATH)
    LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))
    LIP = SEG[4] + 0.55 * (SEG[5] - SEG[4]) - 5.0
    LAND = LIP + 11.0
    HEIGHT = {0: 20.0, 1: 20.0, 2: 24.0, 3: 44.0, 4: 48.0, 5: 47.0, 6: 46.0}
    HEIGHT.update({k + 7: STD_HEIGHT[k + 29] for k in range(4)})
    CRESTS = {2: (2, 1.2), 6: (2, 1.4), 9: (1, 1.5)}
    road_z = kit.with_jumps(_base_z, seg_of, [(LIP, LAND, 3.0, 1.2)], run=14.0)
    ROUTE = kit.route_points_by(PATH, road_z, every=8.0, width=road_w)
    TO_ROAD, TO_PLAN = kit.along(PATH, road_z)
    _d = 0.0
    for _i, (_x, _y, _h, _sg) in enumerate(PATH):
        if _i:
            _d += math.hypot(_x - PATH[_i - 1][0], _y - PATH[_i - 1][1])
        if 1 <= _sg <= 6 and (not NEW or math.hypot(_x - NEW[-1][0], _y - NEW[-1][1]) >= 5.0):
            NEW.append((_x, _y, road_z(_d, _sg)))
        if CRACK is None and _d >= (LIP + LAND) / 2:
            CRACK = (_x, _y)


def natural(x, y):
    h = _natural(x, y)
    if NEW:
        # (The ruin) the split through the mount: the land meets the new road, sheer
        # within a few metres where the mount stands over it; the crack at the leap.
        best = min(NEW, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)
        d = math.hypot(best[0] - x, best[1] - y)
        if d < 60.0:
            k = smooth((d - 14.0) / (12.0 if h > best[2] + 10 else 40.0))
            h = lerp(best[2] - 0.6, h, k)
        if abs(x - CRACK[0]) < 6.0 and abs(y - CRACK[1]) < 30.0:
            h = lerp(h, -40.0, smooth((6.0 - abs(x - CRACK[0])) / 2.5))
    return h


def _natural(x, y):
    """The Palace Mount in the middle of the lap, the lagoon to the south-east, the Cloud
    Chasm along the north-west, the cliff edge west."""
    h = 8.0 + 1.0 * math.sin(x / 25.0) * math.cos(y / 19.0)
    dm = math.hypot((x - MOUNT[0]) * 0.9, y - MOUNT[1])
    h += 70.0 * smooth((150.0 - dm) / 100.0)
    lagoon = smooth((x - LAGOON_X) / 30.0) * smooth((MOUNT[1] + 60.0 - y) / 40.0)
    h = lerp(h, -5.0, lagoon)
    chasm = smooth((y - (CHASM_Y + 25.0)) / 25.0) * smooth((MOUNT[0] + 40.0 - x) / 60.0)
    h = lerp(h, -40.0, chasm)
    # Low ground round the shrine, so its loop's way in runs under the loop in the open.
    ds = math.hypot(x - SHRINE[0], y - SHRINE[1])
    h = lerp(h, 4.0, smooth((STD_LAYOUT[14][1] + 40.0 - ds) / 25.0))
    return h


def classify(c, n, info):
    if c.z < -12.0:
        return ("cdf_abyss", "abyss")
    if c.z < -1.0:
        return ("moon_lake", "deep_water")
    if n.z < 0.6:
        return ("moon_rock", "wall")
    if n.z < 0.8:
        return ("moon_rock", "dirt")
    if c.z < 1.2:
        return ("pale_beach", "sand")
    return ("moon_grass", "grass")


def main():
    c = kit.Course(TRACK_ID, "Moonstone Kingdom (Ruined)" if RUIN else "Moonstone Kingdom", "moon_ruins" if RUIN else "moonstone_kingdom")
    c.route(ROUTE, width=16.0, bank=6.0)
    kerb = ("moon_kerb", "road")
    bal = ("moon_stone", "wall")
    lanterns = ("moon_stone_dark", "wall")
    marble = ("moon_stone", "wall")
    c.kinds = {
        "gate": {"mat": "moon_paving", "shoulder": 1.6, "shoulder_mat": kerb, "barrier": 1.1, "barrier_mat": lanterns},
        "market": {"mat": "moon_paving", "shoulder": 1.4, "shoulder_mat": kerb, "barrier": 1.0, "barrier_mat": lanterns},
        "bridge": {"mat": "moon_paving", "shoulder": 1.2, "shoulder_mat": kerb, "barrier": 1.3, "barrier_mat": bal, "deck": 4.5,
                   "deck_mat": marble, "ground": False},
        "plaza": {"mat": "moon_paving", "shoulder": 1.6, "shoulder_mat": kerb, "barrier": 1.0, "barrier_mat": bal},
        "high": {"mat": "moon_tiles", "shoulder": 1.2, "shoulder_mat": kerb, "barrier": 1.2, "barrier_mat": bal},
        "high_bridge": {"mat": "moon_tiles", "shoulder": 1.0, "shoulder_mat": kerb, "barrier": 1.3, "barrier_mat": bal, "deck": 5.0,
                        "deck_mat": marble, "ground": False},
        "ramp": {"mat": "moon_tiles", "shoulder": 1.0, "shoulder_mat": kerb, "deck": 6.0, "deck_mat": marble, "ground": False},
        "royal": {"mat": "moon_tiles", "shoulder": 1.6, "shoulder_mat": kerb, "barrier": 1.1, "barrier_mat": lanterns},
    }

    if RUIN:
        ruin_course(c)
        return

    def label(smp):
        s = TO_PLAN(smp.s)
        seg = seg_of(s)
        if LIP <= s <= LAND:
            return "gap"
        if LIP - 14 <= s < LIP:
            return "ramp"
        if seg in (1, 2, 3):
            return "market"
        if seg in (5, 6, 7):
            return "bridge"
        # The loop and the spiral, and on past where each crosses over its own way in
        # (a bridge there, so the land isn't raised under it onto the road below).
        if seg in (14, 15, 22, 23, 24) or (seg == 16 and s < SEG[16] + 30) or (seg == 25 and s < SEG[25] + 30):
            return "high_bridge"
        if seg in (16, 17, 18, 19, 20, 21):
            return "high"
        if seg in (25, 26, 27, 29, 30):
            return "plaza"
        if seg in (28, 31):
            return "royal"
        if seg in (0, 32):
            return "gate"
        return "plaza"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "ramp":
            specials.append((s0, s1, "ramp", {"lift": lambda u, n: 0.8 * max(0.0, (u - (n - 8)) / 8) ** 2}))
        elif k != "plaza":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "plaza", max_len=200.0))

    X0, X1, Y0, Y1 = -260, 560, -160, 560
    ter = c.terrain("Land", X0, X1, Y0, Y1, 6.0, natural, classify, near=9.0, fade=14.0, under=0.2)
    c.disc("Lagoon", LAGOON_X + 160.0, MOUNT[1] - 120.0, 240.0, -1.5, c.lib("moon_lake", "deep_water"), n=40)

    def under(x, y):
        return natural(x, y) - 0.4

    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 6.0, under, c.lib("moon_grass", "grass"))

    for piece in c.pieces:
        for kind, size in (("high_bridge", 2.2), ("bridge", 2.0), ("ramp", 2.2)):
            if piece.name.endswith(kind) and not (kind == "bridge" and piece.name.endswith("high_bridge")):
                kit.clear_piers(c, piece, [ter], every=14.0, mat=("moon_stone", "wall"), size=size, inset=size + 1.0)

    # The observatory pinnacle inside the spiral (the shrine, the palace and the town are
    # moon_scenery's).
    zp = road_z(SEG[23], 23)
    pin = c.rock_mass("Observatory Pinnacle", PINNACLE[0], PINNACLE[1], LAYOUT[23][1] - 14.0, LAYOUT[23][1] - 14.0, zp + 40.0, z0=-40.0, n=18, seed=6)
    c.paint_rock(pin, ("moon_rock", "wall"), ("moon_grass", "grass"))
    c.start_line()
    S = lambda i: TO_ROAD(SEG[i])  # noqa: E731
    # Zippers: out of the market onto the bridge, up the shore, out of the shrine's loop,
    # on the Star Leap's run-up, down the causeway.
    for at in (S(4) + 2, S(10) + 10, S(15) + 14, TO_ROAD(LIP - 44), S(28) + 20):
        c.zipper(at, 0)
    for at, across in ((S(2) + 15, 0), (S(11) + 25, 0), (S(17) + 40, 0), (S(20) + 30, 0), (S(26) + 30, 0), (S(30) + 20, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (S(1) + 15, -4, "red"),
        (S(1) + 15, 4, "blue"),
        (S(9) + 15, 0, "green"),
        (S(16) + 20, 0, "yellow"),
        (S(21) + 20, 0, "rainbow"),
        (S(25) + 10, -4, "red"),
        (S(25) + 10, 4, "blue"),
        (S(29) + 20, 0, "green"),
    ):
        c.balloon(at, across, col)
    c.entity("respawn", **{"from": round(TO_ROAD(LIP - 20), 1), "to": round(TO_ROAD(LAND + 4), 1), "at": round(TO_ROAD(LAND + 18), 1)})

    c.checkpoints(
        extra=[S(2), S(6), S(11), S(14) + 60, S(16) + 40, S(19), S(23) + 60, S(26), S(28) + 40, S(31)],
        avoid=[(TO_ROAD(LIP - 16), TO_ROAD(LAND + 8))],
        height=10.0,
    )

    import moon_scenery  # noqa: E402

    moon_scenery.build(c, sys.modules[__name__], ter)
    c.finish()
    print("lap", round(c.length, 1))


def ruin_course(c):
    """The ruin's roads, land and gameplay (celestial_dragon_festival_ruins.py dresses it)."""
    kerb = ("moon_kerb", "road")
    c.kinds["split"] = {"mat": "moon_tiles", "shoulder": 1.6, "shoulder_mat": ("moon_rock", "dirt")}
    c.kinds["ramp"] = {"mat": "moon_tiles", "shoulder": 1.0, "shoulder_mat": kerb}

    def label(smp):
        s = TO_PLAN(smp.s)
        seg = seg_of(s)
        if LIP <= s <= LAND:
            return "gap"
        if LIP - 14 <= s < LIP:
            return "ramp"
        if 1 <= seg <= 6:
            return "split"
        if seg in (7, 8):
            return "plaza"
        if seg == 9:
            return "royal"
        return "gate"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "ramp":
            specials.append((s0, s1, "ramp", {"lift": lambda u, n: 0.8 * max(0.0, (u - (n - 8)) / 8) ** 2}))
        elif k != "plaza":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "plaza", max_len=200.0))
    X0, X1, Y0, Y1 = -260, 560, -160, 560
    ter = c.terrain("Land", X0, X1, Y0, Y1, 6.0, natural, classify, near=9.0, fade=14.0, under=0.2)
    c.disc("Lagoon", LAGOON_X + 160.0, MOUNT[1] - 120.0, 240.0, -1.5, c.lib("moon_lake", "deep_water"), n=40)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 6.0, lambda x, y: natural(x, y) - 0.4, c.lib("moon_grass", "grass"))
    zp = STD_HEIGHT[23]
    pin = c.rock_mass("Observatory Pinnacle", PINNACLE[0], PINNACLE[1], STD_LAYOUT[23][1] - 14.0, STD_LAYOUT[23][1] - 14.0, zp + 40.0, z0=-40.0, n=18,
                      seed=6)
    c.paint_rock(pin, ("moon_rock", "wall"), ("moon_grass", "grass"))
    ruin_mode.DRESS(c, sys.modules[__name__], ter)
    c.start_line()
    S = lambda i: TO_ROAD(SEG[i])  # noqa: E731
    for at in (S(1) + 10, S(2) + 120, TO_ROAD(LIP - 40), S(6) + 20):
        c.zipper(at, 0)
    for at, across in ((S(2) + 60, 0), (S(4) + 10, 3), (S(6) + 120, 0), (S(8) + 20, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in ((S(0) + 30, -4, "red"), (S(0) + 30, 4, "blue"), (S(2) + 180, 0, "green"), (S(5) + 20, 0, "yellow"),
                            (S(6) + 80, -4, "rainbow"), (S(6) + 80, 4, "red"), (S(9) + 20, 0, "blue")):
        c.balloon(at, across, col)
    c.entity("respawn", **{"from": round(TO_ROAD(LIP - 20), 1), "to": round(TO_ROAD(LAND + 4), 1), "at": round(TO_ROAD(LAND + 18), 1)})
    c.checkpoints(extra=[S(1) + 20, S(2) + 90, S(2) + 200, S(3) + 30, S(5) + 20, S(6) + 100, S(8)], avoid=[(TO_ROAD(LIP - 16), TO_ROAD(LAND + 8))],
                  height=10.0)
    c.finish()
    print("lap", round(c.length, 1))


if __name__ == "__main__":
    main()
