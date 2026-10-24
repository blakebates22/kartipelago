# Dragon Isles v3: a greybox of a new lap, to drive before it's dressed (?track=dragon_isles_v3).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/dragon_isles_v3.py      (the bpy module)
#
# Blake: the first dragon course isn't fun to drive, and it's long; make the driving much
# better and the lap about 20% shorter. This keeps the course's story in the same order,
# in plain shapes, on a lap of about 2.15 km (from 2.69) that's nearly all corners:
#
#   1  The Grand Ceremonial Gate: the start, north.
#   2  The Riverside Festival Village: an S-chicane through the market streets, a hop
#      over the humped canal bridge, round the festival square.
#   3  The Cliffside Ascent: two hairpins up the cliff, linked by ledges.
#   4  The Great Waterfall Bridge: east over the gorge, and the bridge is broken in the
#      middle: a jump over the falls (miss it and you're put back on the far side).
#   5  The Temple Gardens: a dip-and-weave S round the temple (the Courtyard Passage, the
#      shortcut, goes straight through).
#   6  The Sky Paths: south along the karst pillars over the lagoon: a jump from pillar
#      to pillar, then a weave across three more on rolling bridges.
#   7  The Lantern Harbour: a spiral down round the last great pillar, one and a quarter
#      turns, to the boardwalk; an S past the docks and the humped harbour bridge.
#   8  The Ancient Dragon Passage: north through the headland's tunnel.
#   9  The Grand Reveal and the Royal Approach: up onto the overlook and an S down to the
#      gate and the line.
#
# The current Dragon Isles is untouched (dragon_isles.py).

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp, smooth  # noqa: E402

TRACK_ID = "dragon_isles_v3"

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
HEIGHT = {
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


def road_w(d, seg):
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
    return next(p for p in PATH if p[3] == i)


def _arc_centre(i):
    x, y, h, _ = _seg_point(i)
    sg = LAYOUT[i]
    a = math.radians(h + (90 if sg[0] == "L" else -90))
    return (x + sg[1] * math.cos(a), y + sg[1] * math.sin(a))


_D = [0.0]
for _a, _b in zip(PATH, PATH[1:]):
    _D.append(_D[-1] + math.hypot(_b[0] - _a[0], _b[1] - _a[1]))


def _at(d):
    i = min(range(len(_D)), key=lambda k: abs(_D[k] - d))
    return PATH[i]


SPIRE = _arc_centre(23)  # the last great pillar the spiral winds round
TEMPLE = _arc_centre(14)  # inside the temple's S
SQUARE = _arc_centre(5)
_fl = _at(FALLS_LIP + 6.5)
GORGE_X = _fl[0]  # the gorge runs north-south under the broken bridge
_p13, _p16 = _seg_point(13), _seg_point(16)
COURTYARD = [(_p13[0] - 4.0, _p13[1]), ((_p13[0] + _p16[0]) / 2, (_p13[1] + _p16[1]) / 2 + 2.0), (_p16[0] + 4.0, _p16[1])]

# The plan's regions (see the header): the lagoon to the east, the highland north.
HIGH_Y = min(p[1] for p in PATH if p[3] == 11) - 4.0  # the cliff top
SHORE_Y = max(p[1] for p in PATH if p[3] == 24) + 26.0  # the harbour's waterfront
LAGOON_X = min(p[0] for p in PATH if p[3] in (18, 19, 20, 21)) - 45.0
SEA = -6.0


def natural(x, y):
    """The valley floor, the cliff up to the highland in the north, the gorge through it,
    and the lagoon (east, and south of the highland down to the harbour)."""
    h = 5.0 + 1.0 * math.sin(x / 31.0) * math.cos(y / 27.0) + 0.6 * math.sin((x + y) / 13.0)
    high = smooth((y - (HIGH_Y - 70.0)) / 70.0)
    h = lerp(h, 40.0 + 1.5 * math.sin(x / 23.0), high)
    gorge = smooth((26.0 - abs(x - GORGE_X)) / 12.0) * smooth((y - (HIGH_Y - 40.0)) / 30.0)
    h = lerp(h, -3.0, gorge)
    lagoon = smooth((x - LAGOON_X) / 40.0) * smooth((y - SHORE_Y) / 30.0) * (1 - 0.0 * high)
    h = lerp(h, SEA, lagoon)
    return h


def in_drop(x, y, z):
    """Fallen off the broken bridge or the pillar jump (put back past it)."""
    return z < 1.0 and (abs(x - GORGE_X) < 24.0 and y > HIGH_Y - 40.0)


def classify(c, n, info):
    if in_drop(c.x, c.y, c.z):
        return ("canyon_river", "abyss")
    if c.z < 0.4:
        return ("lagoon_shallow", "water") if c.z > -1.0 else ("lagoon", "deep_water")
    if n.z < 0.6:
        return ("limestone", "wall")
    if info["d"] < 11:
        return ("pale_sand", "dirt")
    if c.z < 1.6:
        return ("pale_beach", "dirt")
    return ("lush_grass", "grass")


def box(bm, centre, size, rot=0.0):
    import props  # noqa: E402

    props.cuboid(bm, centre, size, rot=rot)


def main():
    import props  # noqa: E402
    from course_kit import bmesh  # noqa: E402

    def at(d):
        return c.at(TO_ROAD(d))

    c = kit.Course(TRACK_ID, "Dragon Isles (v3 greybox)", "dragon_isles")
    c.route(ROUTE, width=16.0, bank=7.0)
    curb = ("stone_curb", "road")
    bal = ("isle_balustrade", "wall")
    rail = ("red_rail", "wall")
    stone = ("stone_base", "wall")
    c.kinds = {
        "gate": {"mat": "isle_paving", "shoulder": 1.6, "shoulder_mat": curb},
        "village": {"mat": "village_cobble", "shoulder": 1.2, "shoulder_mat": curb, "barrier": 1.0, "barrier_mat": rail},
        "canal": {"mat": "isle_paving", "shoulder": 0.8, "shoulder_mat": curb, "barrier": 1.2, "barrier_mat": bal, "deck": 2.4,
                  "deck_mat": stone, "ground": False},
        "cliff": {"mat": "cliff_road", "shoulder": 1.2, "shoulder_mat": ("cliff_road", "dirt"), "barrier": 1.1, "barrier_mat": bal},
        "bridge": {"mat": "isle_paving", "shoulder": 1.0, "shoulder_mat": curb, "barrier": 1.3, "barrier_mat": bal, "deck": 4.0,
                   "deck_mat": stone, "ground": False},
        "kicker": {"mat": "isle_paving", "shoulder": 1.0, "shoulder_mat": curb, "deck": 4.0, "deck_mat": stone, "ground": False},
        "temple": {"mat": "temple_flag", "shoulder": 1.6, "shoulder_mat": ("flowerbed", "grass")},
        "sky": {"mat": "isle_paving", "shoulder": 0.8, "shoulder_mat": curb, "barrier": 1.2, "barrier_mat": rail, "deck": 3.5,
                "deck_mat": stone, "ground": False},
        "spiral": {"mat": "isle_paving", "shoulder": 0.8, "shoulder_mat": curb, "barrier": 1.3, "barrier_mat": bal, "deck": 3.0,
                   "deck_mat": stone, "ground": False},
        "harbour": {"mat": "wood_dock", "shoulder": 1.0, "shoulder_mat": ("wood_dock", "road"), "barrier": 1.0,
                    "barrier_mat": ("weathered_timber", "wall")},
        "passage": {"mat": "passage_stone", "shoulder": 1.0, "shoulder_mat": ("passage_stone", "dirt")},
        "royal": {"mat": "royal_carpet", "shoulder": 2.0, "shoulder_mat": curb},
    }

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
    c.shortcut("Courtyard Passage", sc, "temple_flag", "road", width=10.0, shoulder=0.8, shoulder_mat=curb)

    X0, X1, Y0, Y1 = -220, 560, -320, 520
    ter = c.terrain("Land", X0, X1, Y0, Y1, 6.0, natural, classify, near=9.0, fade=14.0, under=0.2)
    c.disc("Lagoon", (LAGOON_X + X1) / 2 + 40, (SHORE_Y + Y1) / 2, 520.0, 0.0, c.lib("lagoon", "deep_water"), n=48)

    def under(x, y):
        return natural(x, y) - 0.4

    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 6.0, under, c.lib("lush_grass", "grass"))

    # Piers under every bridge, the sky paths' pillars, the spiral's great pillar.
    for piece in c.pieces:
        for kind, size, every in (("sky", 3.0, 26.0), ("bridge", 2.2, 18.0), ("spiral", 1.6, 14.0), ("canal", 1.0, 10.0), ("kicker", 2.2, 10.0)):
            if piece.name.endswith(kind):
                kit.clear_piers(c, piece, [ter], every=every, mat=("limestone", "wall"), size=size, inset=size + 1.0)
    rad = LAYOUT[23][1]
    sp = c.rock_mass("Great Pillar", SPIRE[0], SPIRE[1], rad - 14.0, rad - 14.0, 62.0, z0=SEA - 2, n=20, seed=4)
    c.paint_rock(sp, ("limestone", "wall"), ("lush_grass", "grass"))
    for k in range(9):
        d = SEG[18] + (SEG[23] - SEG[18]) * (k + 0.5) / 9
        q = at(d)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 16.0 + 6 * (k % 2)))
            r = c.rock_mass("Karst %d %d" % (k, side > 0), p.x, p.y, 7.0 + 2 * (k % 3), 6.0, q.p.z + 10 + 8 * ((k + side) % 3), z0=SEA - 2, n=12, seed=k * 3 + side)
            c.paint_rock(r, ("limestone", "wall"), ("lush_grass", "grass"))

    # The headland the passage bores through.
    q0, q1 = at(SEG[29] - 10), at(SEG[30] + 20)
    hx, hy = (q0.p.x + q1.p.x) / 2, (q0.p.y + q1.p.y) / 2
    head = c.rock_mass("Headland", hx, hy, 34.0, 30.0, 30.0, z0=-4.0, n=24, seed=7)
    c.tunnel(head, SEG[29] - 8, SEG[30] + 14, half=c.width / 2 + 2.5, height=10.0, pad=16.0)
    c.paint_rock(head, ("limestone", "wall"), ("lush_grass", "grass"), floor=("passage_stone", "road"), floor_z=q0.p.z + 1.5)
    # Plain blocks for the buildings: the village, the gate, the temple, the harbour.
    bm = bmesh.new()
    s = 30.0
    k = 0
    while s < SEG[7]:
        q = at(s)
        if not (SEG[4] - 4 <= s <= SEG[5] + 4):  # not on the canal bridge
            for side in (-1, 1):
                p = q.side(side * (q.w / 2 + 8.0 + 2 * (k % 2)))
                h = 6.0 + 2.0 * ((k + (side > 0)) % 3)
                box(bm, (p.x, p.y, q.p.z + h / 2 - 0.5), (8.0, 8.0, h), rot=math.atan2(q.t.y, q.t.x))
        s += 14.0
        k += 1
    q = at(12.0)
    for side in (-1, 1):
        p = q.side(side * (q.w / 2 + 3.0))
        box(bm, (p.x, p.y, q.p.z + 6.0), (4.0, 4.0, 13.0), rot=math.atan2(q.t.y, q.t.x))
    box(bm, (q.p.x, q.p.y, q.p.z + 13.5), (4.0, q.w + 10.0, 2.5), rot=math.atan2(q.t.y, q.t.x))
    zt = road_z(SEG[14], 14)
    box(bm, (TEMPLE[0], TEMPLE[1], zt + 10.0), (12.0, 12.0, 22.0))
    for k in range(5):
        box(bm, (TEMPLE[0], TEMPLE[1], zt + 21.5 + 3.2 * k), (16.0 - 2.4 * k, 16.0 - 2.4 * k, 0.8))
    s = SEG[24] + 6
    k = 0
    while s < SEG[28]:
        q = at(s)
        p = q.side(-(q.w / 2 + 9.0))  # the town on the shore side
        box(bm, (p.x, p.y, q.p.z + 3.0), (9.0, 8.0, 6.0 + 2 * (k % 2)), rot=math.atan2(q.t.y, q.t.x))
        s += 16.0
        k += 1
    blocks = c.mesh_object("Buildings", bm, "Props")
    c.assign(blocks, c.lib("roof_jade", "wall"))

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

    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish()
    print("lap", round(c.length, 1))


if __name__ == "__main__":
    main()
