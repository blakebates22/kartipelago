# Dragonspire Keep: Dragon Kingdom, course 1. A castle on its cliffs at sunset.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/dragon_isles.py      (the bpy module)
#
# The v3 greybox's lap (it was dragon_isles_v3.py), exactly: the same roads, heights, widths,
# jumps, surfaces, barriers, pickups, boosts and checkpoints, painted from Blake's
# Dragonspire Keep board (Oct 25): fantasy medieval, not the old Eastern kingdom.
# keep_scenery.py dresses it; keep_props.py is the kit, keep_textures.py the paint.
#
#   1  The Castle Gate: the start, north under the gatehouse between its twin towers.
#   2  The castle town: an S through the market streets, a hump over the town bridge,
#      round the market square.
#   3  The cliff road: two hairpins up the crag on ledges with parapets and torches.
#   4  The Waterfall Viaduct: east over the gorge on arches, broken in the middle: a
#      jump over the falls (miss it and you're put back on the far side).
#   5  The Keep's courtyard: a dip-and-weave S round the fountain under the great keep
#      (the Courtyard Passage, the shortcut, goes straight through).
#   6  The high viaducts: south over the lake on arches between rock spires: a jump
#      from span to span, then a weave on rolling bridges.
#   7  The Beacon Tower: a spiral down round the last great crag, to the lakeside docks;
#      an S past the boats and the humped harbour bridge.
#   8  The tunnel through the headland, under its portcullis.
#   9  The royal approach: up onto the overlook and down the red carpet to the gate.
#
# The first Dragonspire Keep lap (the old Dragon Isles) is kept as dragon_isles_v2.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import ruin_mode  # noqa: E402
from course_kit import lerp, smooth  # noqa: E402

# The ruin (dragon_isles_ruins.py): the Chosen One's sacrifice remade the kingdom. Past the
# gate and the town's first bend, the market streets are torn up; the lap turns south
# across the lowland over a split in the ground, east across the lake bed the blast heaved
# up dry, round the foot of the Beacon crag, and home by the harbour and the passage as
# ever. About half the lap. Everything else (the land, the landmarks) is the course's own.
RUIN = ruin_mode.ON
TRACK_ID = "dragon_isles_ruin" if RUIN else "dragon_isles"

K = 1.08  # the whole plan, scaled
START = (0.0, 0.0)
_PLAN = [
    ("S", 90),  # 0  1: the start, north under the gate
    ("R", 40, 60),  # 1  2: into the village
    ("L", 30, 80),  # 2  an S-chicane through the market streets
    ("R", 30, 80),  # 3
    ("S", 30),  # 4  the humped canal bridge
    ("L", 35, 60),  # 5  round the festival square
    ("S", 30),  # 6
    ("L", 26, 180),  # 7  3: hairpin one, climbing the cliff
    ("S", 50),  # 8  the lower ledge
    ("R", 26, 180),  # 9  hairpin two
    ("S", 50),  # 10 the upper ledge (through the outcrop)
    ("R", 45, 90),  # 11 onto the highland, east
    ("S", 90),  # 12 4: the Great Waterfall Bridge: the broken span
    ("R", 32, 60),  # 13 5: the Temple Gardens: down and round...
    ("L", 32, 120),  # 14
    ("R", 32, 60),  # 15 ...and back up (the Courtyard Passage cuts across)
    ("S", 25),  # 16
    ("R", 40, 90),  # 17 6: the Sky Paths: south
    ("S", 130),  # 18 pillar to pillar: the jump (closes the lap)
    ("L", 45, 70),  # 19 a weave across the pillars
    ("R", 45, 140),  # 20
    ("L", 45, 70),  # 21
    ("S", 50),  # 22
    ("R", 28, 450),  # 23 7: the spiral down round the last pillar
    ("S", 75),  # 24 the harbour boardwalk, west (closes the lap)
    ("L", 35, 60),  # 25 an S past the docks
    ("R", 35, 60),  # 26
    ("S", 50),  # 27 the humped harbour bridge
    ("R", 40, 90),  # 28 north
    ("S", 30),  # 29 8: the Ancient Dragon Passage
    ("L", 40, 60),  # 30 9: up onto the overlook
    ("R", 40, 60),  # 31 the royal approach, down to the gate
    ("S", 20),  # 32
]
LAYOUT = [(s[0], s[1] * K) if s[0] == "S" else (s[0], s[1] * K, s[2]) for s in _PLAN]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 18, 24, START, 90.0)
SEG = kit.segment_starts(PATH)
LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))

# The two jumps: (lip, landing) along the lap.
FALLS_LIP = SEG[12] + 0.5 * (SEG[13] - SEG[12]) - 7.0
FALLS_LAND = FALLS_LIP + 9.0
SKY_LIP = SEG[18] + 0.45 * (SEG[19] - SEG[18])
SKY_LAND = SKY_LIP + 10.0
GAPS = ((FALLS_LIP, FALLS_LAND), (SKY_LIP, SKY_LAND))

# Heights at segment starts; between them the road eases. The spiral drops steadily.
HEIGHT = STD_HEIGHT = {
    0: 8.0, 1: 8.0, 2: 7.2, 3: 6.6, 4: 6.5, 5: 6.5, 6: 6.6, 7: 7.0, 8: 14.0, 9: 20.0, 10: 27.0,
    11: 34.0, 12: 41.0, 13: 41.5, 14: 39.0, 15: 39.0, 16: 42.0, 17: 43.0, 18: 43.0, 19: 41.0,
    20: 40.0, 21: 39.0, 22: 38.0, 23: 37.0, 24: 4.0, 25: 3.6, 26: 3.6, 27: 3.8, 28: 4.4,
    29: 5.5, 30: 7.0, 31: 12.0, 32: 9.0,
}
# Humps and rolling crests: (segment, how many, how high).
CRESTS = {4: (1, 2.6), 12: (1, 1.2), 19: (1, 1.0), 20: (2, 1.2), 21: (1, 1.0), 27: (1, 3.2), 0: (1, 0.6)}


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
    z = lerp(z0, z1, t if seg == 23 else smooth(t))
    if seg in CRESTS:
        n, h = CRESTS[seg]
        z += h * math.sin(t * math.pi * n) ** 2
    return z


# The jumps: a kicker, the gap, and a landing in a dip below the road (2.5-3 m), so an
# ordinary run-up clears it.
road_z = kit.with_jumps(_base_z, seg_of, [(FALLS_LIP, FALLS_LAND, 2.5, 0.9), (SKY_LIP, SKY_LAND, 3.0, 0.9)])
# (The standard lap: the kingdom's landmarks are laid out from it, in the ruin too.)
STD_LAYOUT, STD_PATH, STD_SEG, STD_LENGTH = LAYOUT, PATH, SEG, LENGTH


def road_w(d, seg):
    if RUIN and LAYOUT is not STD_LAYOUT:
        if seg in (0, 15) or d < 40:
            return 20.0
        return 15.0 if seg in (1, 12) else 16.0
    if seg in (0, 32) or d < 40:
        return 20.0  # the start: room for the pack
    if seg in (1, 2, 3, 4, 5, 6):
        return 15.0  # the village streets
    if seg == 23:
        return 15.0  # the spiral
    if seg in (29,):
        return 15.0  # the passage
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


_D = [0.0]
for _a, _b in zip(STD_PATH, STD_PATH[1:]):
    _D.append(_D[-1] + math.hypot(_b[0] - _a[0], _b[1] - _a[1]))


def _at(d):
    i = min(range(len(_D)), key=lambda k: abs(_D[k] - d))
    return STD_PATH[i]


SPIRE = _arc_centre(23)  # the last great pillar the spiral winds round
TEMPLE = _arc_centre(14)  # inside the temple's S
SQUARE = _arc_centre(5)
_fl = _at(FALLS_LIP + 6.5)
GORGE_X = _fl[0]  # the gorge runs north-south under the broken bridge
_p13, _p16 = _seg_point(13), _seg_point(16)
COURTYARD = [(_p13[0] - 4.0, _p13[1]), ((_p13[0] + _p16[0]) / 2, (_p13[1] + _p16[1]) / 2 + 2.0), (_p16[0] + 4.0, _p16[1])]

# The plan's regions (see the header): the lagoon to the east, the highland north.
HIGH_Y = min(p[1] for p in STD_PATH if p[3] == 11) - 4.0  # the cliff top
SHORE_Y = max(p[1] for p in STD_PATH if p[3] == 24) + 26.0  # the harbour's waterfront
LAGOON_X = min(p[0] for p in STD_PATH if p[3] in (18, 19, 20, 21)) - 45.0
SEA = -6.0


_DOCKS = [p for p in STD_PATH if p[3] in (24, 25, 26, 27, 28)]
_HY = {}


def HARBOUR_Y(x):
    """The docks' north edge at x (plus a margin), for the harbour's basin."""
    k = int(round(x / 2.0))
    if k not in _HY:
        best = max((p[1] for p in _DOCKS if abs(p[0] - k * 2.0) < 6.0), default=-175.0)
        _HY[k] = best + 15.0
    return _HY[k]


# ---------------------------------------------------------------- the ruin's lap

SPLIT_LINE = []  # (the ruin) the split in the ground the lap jumps: [(x, y)]
HEAVE = None  # (the ruin) the heaved lake bed: (x0, x1, y0, y1)
if RUIN:
    LAYOUT = STD_LAYOUT[:2] + [
        ("R", 40.0, 120),  # 2  out of the town's first bend, south: the torn market
        ("S", 140.0),  # 3  across the lowland, over the split (closes the loop)
        ("L", 34.0, 90),  # 4  east
        ("S", 175.0),  # 5  across the heaved lake bed (closes the loop)
        ("R", STD_LAYOUT[23][1], 180),  # 6  round the Beacon crag's foot
    ] + list(STD_LAYOUT[24:])  # 7-15: the harbour, the passage, the royal approach
    LAYOUT, PATH = kit.close_turtle(LAYOUT, 3, 5, START, 90.0)
    SEG = kit.segment_starts(PATH)
    LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))
    SPLIT = (SEG[3] + 70.0, SEG[3] + 82.0)
    GAPS = (SPLIT,)
    HEIGHT = {0: 8.0, 1: 8.0, 2: 7.4, 3: 6.0, 4: 5.0, 5: 5.0, 6: 4.4}
    HEIGHT.update({k + 7: STD_HEIGHT[k + 24] for k in range(9)})
    CRESTS = {0: (1, 0.6), 3: (2, 1.2), 5: (3, 2.2), 10: (1, 3.2)}
    road_z = kit.with_jumps(_base_z, seg_of, [(SPLIT[0], SPLIT[1], 2.5, 0.9)])
    ROUTE = kit.route_points_by(PATH, road_z, every=8.0, width=road_w)
    TO_ROAD, TO_PLAN = kit.along(PATH, road_z)
    _sx = [p for p in PATH if p[3] == 3]
    _mid = min(_sx, key=lambda p: abs(p[1] - _sx[0][1] + (SPLIT[0] + SPLIT[1]) / 2 - SEG[3]))
    SPLIT_LINE = [(_mid[0] - 50.0, _mid[1] + 6.0), (_mid[0] - 20.0, _mid[1] - 2.0), (_mid[0] + 20.0, _mid[1] + 3.0), (_mid[0] + 60.0, _mid[1] - 4.0)]
    _s5 = [p for p in PATH if p[3] == 5]
    HEAVE = (_s5[0][0] - 10.0, _s5[-1][0] + 4.0, _s5[0][1] - 34.0, _s5[0][1] + 30.0)


def split_d(x, y):
    """(The ruin) how far (x, y) is from the split's line."""
    best = 1e9
    for a, b in zip(SPLIT_LINE, SPLIT_LINE[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        t = max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(x - a[0] - t * dx, y - a[1] - t * dy))
    return best


def natural(x, y):
    h = _natural(x, y)
    if HEAVE:
        # (The ruin) the lake bed thrown up dry in tilted slabs, and the split.
        x0, x1, y0, y1 = HEAVE
        k = smooth((x - x0) / 20.0) * smooth((x1 - x) / 20.0) * smooth((y - y0) / 14.0) * smooth((y1 - y) / 14.0)
        slab = 3.0 + 2.0 * math.sin(x / 17.0) + 1.2 * math.sin((x - y) / 9.0)
        h = lerp(h, max(h, slab), k)
        if split_d(x, y) < 10.0:
            h = lerp(h, -14.0, smooth((10.0 - split_d(x, y)) / 4.0))
    return h


def _natural(x, y):
    """The valley floor, the cliff up to the highland in the north, the gorge through it,
    and the lagoon (east, and south of the highland down to the harbour)."""
    h = 5.0 + 1.0 * math.sin(x / 31.0) * math.cos(y / 27.0) + 0.6 * math.sin((x + y) / 13.0)
    high = smooth((y - (HIGH_Y - 70.0)) / 70.0)
    h = lerp(h, 40.0 + 1.5 * math.sin(x / 23.0), high)
    gorge = smooth((26.0 - abs(x - GORGE_X)) / 12.0) * smooth((y - (HIGH_Y - 40.0)) / 30.0)
    h = lerp(h, -3.0, gorge)
    lagoon = smooth((x - LAGOON_X) / 40.0) * smooth((y - SHORE_Y) / 30.0) * (1 - 0.0 * high)
    # The harbour's basin, north of the docks (painting: the jetties need water; the docks
    # have barriers both sides, so nothing here is reachable from the road).
    basin = smooth((x - 92.0) / 16.0) * smooth((-44.0 - y) / 16.0) * smooth((y - HARBOUR_Y(x)) / 10.0)
    h = lerp(h, SEA, max(lagoon, basin))
    return h


def in_drop(x, y, z):
    """Fallen off the broken bridge or the pillar jump (put back past it); in the ruin,
    down the split."""
    if SPLIT_LINE and z < -4.0 and split_d(x, y) < 8.0:
        return True
    return z < 1.0 and (abs(x - GORGE_X) < 24.0 and y > HIGH_Y - 40.0)


def classify(c, n, info):
    if in_drop(c.x, c.y, c.z):
        return ("canyon_river", "abyss")
    if c.z < 0.4:
        return ("keep_lake_shallow", "water") if c.z > -1.0 else ("keep_lake", "deep_water")
    if n.z < 0.6:
        return ("keep_rock", "wall")
    if info["d"] < 11:
        return ("keep_path", "dirt")
    if c.z < 1.6:
        return ("keep_shore", "dirt")
    return ("keep_grass", "grass")


def pillars(c, m):
    """The spiral's great pillar and the karst spires along the sky paths (m: the standard
    course; in the ruin, under the standard lap's ghost)."""
    rad = m.STD_LAYOUT[23][1]
    sp = c.rock_mass("Great Pillar", m.SPIRE[0], m.SPIRE[1], rad - 14.0, rad - 14.0, 62.0, z0=SEA - 2, n=20, seed=4)
    c.paint_rock(sp, ("keep_rock", "wall"), ("keep_grass", "grass"))
    for k in range(9):
        d = m.STD_SEG[18] + (m.STD_SEG[23] - m.STD_SEG[18]) * (k + 0.5) / 9
        q = c.at(m.TO_ROAD(d))
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 16.0 + 6 * (k % 2)))
            r = c.rock_mass("Karst %d %d" % (k, side > 0), p.x, p.y, 7.0 + 2 * (k % 3), 6.0, q.p.z + 10 + 8 * ((k + side) % 3), z0=SEA - 2, n=12, seed=k * 3 + side)
            c.paint_rock(r, ("keep_rock", "wall"), ("keep_grass", "grass"))


def main():
    def at(d):
        return c.at(TO_ROAD(d))

    c = kit.Course(TRACK_ID, "Dragonspire Keep (Ruined)" if RUIN else "Dragonspire Keep", "keep_ruins" if RUIN else "dragonspire_keep")
    c.route(ROUTE, width=16.0, bank=7.0)
    curb = ("keep_kerb", "road")
    bal = ("keep_parapet", "wall")
    rail = ("keep_parapet", "wall")
    stone = ("keep_ashlar", "wall")
    c.kinds = {
        "gate": {"mat": "keep_flag", "shoulder": 1.6, "shoulder_mat": curb},
        "village": {"mat": "keep_cobble", "shoulder": 1.2, "shoulder_mat": curb, "barrier": 1.0, "barrier_mat": rail},
        "canal": {"mat": "keep_flag", "shoulder": 0.8, "shoulder_mat": curb, "barrier": 1.2, "barrier_mat": bal, "deck": 2.4,
                  "deck_mat": stone, "ground": False},
        "cliff": {"mat": "keep_path", "shoulder": 1.2, "shoulder_mat": ("keep_path", "dirt"), "barrier": 1.1, "barrier_mat": bal},
        "bridge": {"mat": "keep_flag", "shoulder": 1.0, "shoulder_mat": curb, "barrier": 1.3, "barrier_mat": bal, "deck": 4.0,
                   "deck_mat": stone, "ground": False},
        "kicker": {"mat": "keep_flag", "shoulder": 1.0, "shoulder_mat": curb, "deck": 4.0, "deck_mat": stone, "ground": False},
        "temple": {"mat": "keep_flag", "shoulder": 1.6, "shoulder_mat": ("keep_grass", "grass")},
        "sky": {"mat": "keep_flag", "shoulder": 0.8, "shoulder_mat": curb, "barrier": 1.2, "barrier_mat": rail, "deck": 3.5,
                "deck_mat": stone, "ground": False},
        "spiral": {"mat": "keep_flag", "shoulder": 0.8, "shoulder_mat": curb, "barrier": 1.3, "barrier_mat": bal, "deck": 3.0,
                   "deck_mat": stone, "ground": False},
        "harbour": {"mat": "keep_dock", "shoulder": 1.0, "shoulder_mat": ("keep_dock", "road"), "barrier": 1.0,
                    "barrier_mat": ("weathered_timber", "wall")},
        "passage": {"mat": "keep_flag", "shoulder": 1.0, "shoulder_mat": ("keep_path", "dirt")},
        "royal": {"mat": "keep_carpet", "shoulder": 2.0, "shoulder_mat": curb},
    }

    if RUIN:
        ruin_course(c)
        return

    def label(smp):
        s = TO_PLAN(smp.s)
        seg = seg_of(s)
        for lip, land in GAPS:
            if lip <= s <= land:
                return "gap"
            if lip - 12 <= s < lip:
                return "kicker"
        if seg in (1, 2, 3, 5, 6):
            return "village"
        if seg == 4:
            return "canal"
        if seg in (7, 8, 9, 10, 11):
            return "cliff"
        if seg == 12:
            return "bridge"
        if seg in (13, 14, 15, 16):
            return "temple"
        if seg in (17, 18, 19, 20, 21, 22):
            return "sky"
        if seg == 23:
            return "spiral"
        if seg in (24, 25, 26, 27, 28):
            return "harbour"
        if seg in (29, 30):
            return "passage"
        if seg in (31, 32) and s > SEG[31] + 20:
            return "royal"
        return "gate"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "kicker":
            specials.append((s0, s1, "kicker", {"lift": lambda u, n: 0.6 * max(0.0, (u - (n - 8)) / 8) ** 2}))
        elif k != "gate":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "gate", max_len=200.0))

    # The Courtyard Passage: straight across the temple's S, at the road's height.
    za, zb = road_z(SEG[13], 13), road_z(SEG[16], 16)
    sc = [(x, y, lerp(za, zb, i / (len(COURTYARD) - 1)) - 0.05) for i, (x, y) in enumerate(COURTYARD)]
    c.shortcut("Courtyard Passage", sc, "keep_flag", "road", width=10.0, shoulder=0.8, shoulder_mat=curb, flush=True)

    X0, X1, Y0, Y1 = -220, 560, -320, 520
    ter = c.terrain("Land", X0, X1, Y0, Y1, 6.0, natural, classify, near=9.0, fade=14.0, under=0.2, fine=3)
    c.disc("Lagoon", (LAGOON_X + X1) / 2 + 40, (SHORE_Y + Y1) / 2, 520.0, 0.0, c.lib("keep_lake", "deep_water"), n=48)

    def under(x, y):
        return natural(x, y) - 0.4

    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 6.0, under, c.lib("keep_grass", "grass"))

    # Piers under every bridge, the sky paths' pillars, the spiral's great pillar.
    for piece in c.pieces:
        for kind, size, every in (("sky", 3.0, 26.0), ("bridge", 2.2, 18.0), ("spiral", 1.6, 14.0), ("canal", 1.0, 10.0), ("kicker", 2.2, 10.0)):
            if piece.name.endswith(kind):
                kit.clear_piers(c, piece, [ter], every=every, mat=("keep_ashlar", "wall"), size=size, inset=size + 1.0)
    pillars(c, sys.modules[__name__])

    # The headland the passage bores through.
    q0, q1 = at(SEG[29] - 10), at(SEG[30] + 20)
    hx, hy = (q0.p.x + q1.p.x) / 2, (q0.p.y + q1.p.y) / 2
    head = c.rock_mass("Headland", hx, hy, 34.0, 30.0, 30.0, z0=-4.0, n=24, seed=7)
    c.tunnel(head, SEG[29] - 8, SEG[30] + 14, half=c.width / 2 + 2.5, height=10.0, pad=16.0)
    c.paint_rock(head, ("keep_rock", "wall"), ("keep_grass", "grass"), floor=("keep_flag", "road"), floor_z=q0.p.z + 1.5)
    c.start_line()
    S = lambda i: TO_ROAD(SEG[i])  # noqa: E731
    # Zippers: out of the village onto the cliff, on the broken bridge's run-up, out of the
    # temple onto the sky paths, on the pillar jump's run-up, out of the harbour.
    for at in (S(6) + 4, TO_ROAD(FALLS_LIP - 40), S(17) + 10, TO_ROAD(SKY_LIP - 36), S(28) + 10):
        c.zipper(at, 0)
    for at, across in ((S(2) + 20, 0), (S(9) + 30, 0), (S(14) + 30, 0), (S(20) + 40, 0), (S(25) + 20, 0), (S(31) + 20, -3)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (S(1) + 20, -4, "red"),
        (S(1) + 20, 4, "blue"),
        (S(8) + 25, 0, "green"),
        (S(13) + 10, 0, "yellow"),
        (S(19) + 20, 0, "rainbow"),
        (S(22) + 20, -4, "red"),
        (S(22) + 20, 4, "blue"),
        (S(26) + 20, 0, "green"),
    ):
        c.balloon(at, across, col)
    for lip, land in GAPS:
        c.entity("respawn", **{"from": round(TO_ROAD(lip - 20), 1), "to": round(TO_ROAD(land + 4), 1), "at": round(TO_ROAD(land + 18), 1)})

    # Checkpoints: one in the middle of the stretch the courtyard skips, with a twin gate
    # across the courtyard (either counts), and none elsewhere in that stretch.
    s_in, s_out = kit.s_near(c, *COURTYARD[0]), kit.s_near(c, *COURTYARD[-1])
    apex = (s_in + s_out) / 2
    gates = c.checkpoints(
        extra=[S(3), S(7) + 40, S(10), S(12) + 10, apex, S(18) + 20, S(20) + 40, S(23) + 120, S(25), S(29), S(31)],
        avoid=[(s_in - 4, apex - 8), (apex + 8, s_out + 4)] + [(TO_ROAD(lip - 14), TO_ROAD(land + 8)) for lip, land in GAPS],
        height=10.0,
    )
    main_gate = min(gates.items(), key=lambda kv: abs(kv[0] - apex))[1]
    m = COURTYARD[1]
    c.alt_gate(main_gate, "courtyard_passage", [(COURTYARD[0][0], COURTYARD[0][1], za), (m[0], m[1], (za + zb) / 2), (COURTYARD[2][0], COURTYARD[2][1], zb)], width=12.0)

    import keep_scenery  # noqa: E402

    keep_scenery.build(c, sys.modules[__name__], ter)
    c.finish()
    print("lap", round(c.length, 1))


def ruin_course(c):
    """The ruin's roads, land and gameplay (dragon_isles_ruins.py dresses it)."""
    rubble = ("keep_rock", "dirt")
    c.kinds.update({
        "torn": {"mat": "keep_path", "shoulder": 1.6, "shoulder_mat": rubble},
        "lakebed": {"mat": "keep_shore", "surface": "dirt", "shoulder": 1.8, "shoulder_mat": rubble},
        "kicker": {"mat": "keep_path", "shoulder": 1.4, "shoulder_mat": rubble},
    })

    def label(smp):
        s = TO_PLAN(smp.s)
        seg = seg_of(s)
        for lip, land in GAPS:
            if lip <= s <= land:
                return "gap"
            if lip - 12 <= s < lip:
                return "kicker"
        if seg == 1:
            return "village"
        if seg in (2, 3, 4):
            return "torn"
        if seg in (5, 6):
            return "lakebed"
        if 7 <= seg <= 11:
            return "harbour"
        if seg in (12, 13):
            return "passage"
        if seg in (14, 15) and s > SEG[14] + 20:
            return "royal"
        return "gate"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "kicker":
            specials.append((s0, s1, "kicker", {"lift": lambda u, n: 0.9 * max(0.0, (u - (n - 8)) / 8) ** 2}))
        elif k != "gate":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "gate", max_len=200.0))
    X0, X1, Y0, Y1 = -220, 560, -320, 520
    ter = c.terrain("Land", X0, X1, Y0, Y1, 6.0, natural, classify, near=9.0, fade=14.0, under=0.2, fine=3)
    c.disc("Lagoon", (LAGOON_X + X1) / 2 + 40, (SHORE_Y + Y1) / 2, 520.0, 0.0, c.lib("keep_lake", "deep_water"), n=48)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 6.0, lambda x, y: natural(x, y) - 0.4, c.lib("keep_grass", "grass"))
    S = lambda i: TO_ROAD(SEG[i])  # noqa: E731
    # The headland the passage bores through, as ever.
    q0, q1 = c.at(S(12) - 10), c.at(S(13) + 20)
    hx, hy = (q0.p.x + q1.p.x) / 2, (q0.p.y + q1.p.y) / 2
    head = c.rock_mass("Headland", hx, hy, 34.0, 30.0, 30.0, z0=-4.0, n=24, seed=7)
    c.tunnel(head, SEG[12] - 8, SEG[13] + 14, half=c.width / 2 + 2.5, height=10.0, pad=16.0)
    c.paint_rock(head, ("keep_rock", "wall"), ("keep_grass", "grass"), floor=("keep_flag", "road"), floor_z=q0.p.z + 1.5)
    ruin_mode.DRESS(c, sys.modules[__name__], ter)
    c.start_line()
    for at in (S(2) + 10, TO_ROAD(SPLIT[0] - 30), S(5) + 10, S(11) + 10):
        c.zipper(at, 0)
    for at, across in ((S(3) + 20, 0), (S(5) + 80, 3), (S(8) + 20, 0), (S(14) + 20, -3)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in ((S(1) + 20, -4, "red"), (S(1) + 20, 4, "blue"), (S(3) + 110, 0, "green"), (S(5) + 40, 0, "yellow"),
                            (S(5) + 130, -4, "rainbow"), (S(5) + 130, 4, "red"), (S(9) + 20, 0, "blue")):
        c.balloon(at, across, col)
    for lip, land in GAPS:
        c.entity("respawn", **{"from": round(TO_ROAD(lip - 20), 1), "to": round(TO_ROAD(land + 4), 1), "at": round(TO_ROAD(land + 18), 1)})
    c.checkpoints(extra=[S(2) + 20, S(3) + 40, S(4) + 20, S(5) + 60, S(6) + 40, S(8), S(12), S(14)],
                  avoid=[(TO_ROAD(lip - 14), TO_ROAD(land + 8)) for lip, land in GAPS], height=10.0)
    c.finish()
    print("lap", round(c.length, 1))


if __name__ == "__main__":
    main()
