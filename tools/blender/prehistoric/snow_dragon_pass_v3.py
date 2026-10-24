# Snow Dragon Pass v3: a greybox of a new lap, to drive before it's dressed
# (?track=snow_dragon_pass_v3).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/snow_dragon_pass_v3.py      (the bpy module)
#
# Blake: the third dragon course isn't fun to drive, and it's long; make the driving much
# better and the lap about 20% shorter. The same story in the same order, in plain shapes,
# on a lap of about 1.9 km (from 2.38) that's nearly all corners, with its two choices of
# road kept:
#
#   1  The Frozen Gate: the start, east, down out of the gate.
#   2  The Windy Village: an S down through the village.
#   3  First choice.
#      The High Cliff Road (the lap): a stack of three hairpins up the mountain's face.
#      The Frozen Supply Road: round the mountain's foot, wide and flowing, through the
#      ice cavern: about as quick.
#   4  Starvation Road: west along the top, a weave between the storehouses.
#   5  The Broken Bridges: over the frozen gorge, a span missing: a jump (miss it and
#      you're put back on the far side).
#   6  The Avalanche Run: south, down the windswept pass, sweepers over crests.
#   7  Second choice.
#      The Monastery Ridge (the lap): a zigzag up over the monastery's bridge and down.
#      The Frozen Aqueduct: straight on along the old channel, through its tunnel: a
#      little quicker.
#   8  The Final Ascent: a spiral up round the Dragon Citadel's bastion to the gate.
#
# The current Snow Dragon Pass is untouched (snow_dragon_pass.py).

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp, smooth  # noqa: E402

TRACK_ID = "snow_dragon_pass_v3"

K = 1.05
START = (0.0, 0.0)
_PLAN = [
    ("S", 60),  # 0  1: the Frozen Gate, east
    ("R", 35, 50),  # 1  2: down through the village...
    ("L", 30, 100),  # 2
    ("R", 30, 50),  # 3
    ("S", 30),  # 4
    ("L", 40, 90),  # 5  north
    ("S", 60),  # 6  3: the first choice (the supply road leaves at the start of this)
    ("R", 24, 90),  # 7  the High Cliff Road: east across the face...
    ("S", 40),  # 8
    ("L", 24, 180),  # 9  ...hairpin...
    ("S", 60),  # 10
    ("R", 24, 180),  # 11 ...hairpin...
    ("S", 40),  # 12
    ("L", 24, 90),  # 13 ...and north
    ("S", 60),  # 14
    ("L", 40, 90),  # 15 4: onto Starvation Road, west (the supply road comes back in here)
    ("S", 120),  # 16 (closes the lap)
    ("R", 45, 40),  # 17 a weave between the storehouses
    ("L", 45, 80),  # 18
    ("R", 45, 40),  # 19
    ("S", 70),  # 20 5: the Broken Bridges: the jump
    ("L", 40, 90),  # 21 6: the Avalanche Run, south
    ("S", 10),  # 22
    ("R", 50, 50),  # 23 sweepers over crests
    ("L", 50, 100),  # 24
    ("R", 50, 50),  # 25
    ("S", 80),  # 26 (closes the lap)
    ("L", 24, 90),  # 27 7: the Monastery Ridge: east...
    ("S", 30),  # 28
    ("R", 24, 180),  # 29 ...over the monastery's bridge and back...
    ("S", 30),  # 30
    ("L", 24, 90),  # 31 ...and south (the aqueduct comes back in here)
    ("S", 10),  # 32
    ("L", 30, 450),  # 33 8: the Final Ascent: the spiral up round the bastion
    ("S", 20),  # 34 to the gate
]
LAYOUT = [(s[0], s[1] * K) if s[0] == "S" else (s[0], s[1] * K, s[2]) for s in _PLAN]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 16, 26, START, 0.0)
SEG = kit.segment_starts(PATH)
LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))

# The broken bridge's jump: (lip, landing).
LIP = SEG[20] + 0.5 * (SEG[21] - SEG[20]) - 7.0
LAND = LIP + 9.0

HEIGHT = {
    0: 50.0, 1: 48.0, 2: 45.0, 3: 42.0, 4: 40.5, 5: 40.0, 6: 40.0, 7: 42.0, 8: 44.0, 9: 46.0, 10: 50.0,
    11: 53.0, 12: 57.0, 13: 59.0, 14: 60.5, 15: 62.0, 16: 62.0, 17: 61.5, 18: 61.0, 19: 61.0, 20: 61.5,
    21: 60.0, 22: 58.0, 23: 56.0, 24: 48.0, 25: 39.0, 26: 33.0, 27: 30.0, 28: 32.0, 29: 34.5, 30: 33.0,
    31: 30.0, 32: 27.0, 33: 26.0, 34: 50.0,
}
CRESTS = {2: (1, 0.8), 17: (1, 0.8), 18: (1, 1.0), 23: (1, 1.6), 24: (2, 1.8), 25: (1, 1.6), 26: (2, 1.4), 29: (1, 1.0)}


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
    z = lerp(z0, z1, t if seg == 33 else smooth(t))
    if seg in CRESTS:
        n, h = CRESTS[seg]
        z += h * math.sin(t * math.pi * n) ** 2
    return z


# The broken bridge: a kicker, the gap, a landing in a dip 2.5 m below the road.
road_z = kit.with_jumps(_base_z, seg_of, [(LIP, LAND, 2.5, 0.9)])


def road_w(d, seg):
    if seg in (0, 34) or d < 40:
        return 20.0
    if seg in (1, 2, 3, 4):
        return 15.0
    if seg in (7, 8, 9, 10, 11, 12, 13, 29, 33):
        return 15.0  # the hairpins, the monastery's bridge, the spiral
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


BASTION = _arc_centre(33)
GORGE_X = _at(LIP + 6.5)[0]  # the frozen gorge runs north-south under the broken bridge
PEAK = (sum(p[0] for p in PATH) / len(PATH) + 20.0, sum(p[1] for p in PATH) / len(PATH) + 20.0)

# The Frozen Supply Road: round the east of the hairpin stack, from the start of seg 6 to
# Starvation Road, wide and flowing.
_a6, _a16 = _seg_point(6), _seg_point(16)
_east = max(p[0] for p in PATH if p[3] in (8, 9, 10, 11, 12)) + 34.0
SUPPLY = [(_a6[0], _a6[1] + 4.0), (_a6[0] + 30.0, _a6[1] + 40.0), (_east, _a6[1] + 90.0), (_east + 6.0, (_a6[1] + _a16[1]) / 2 + 30.0),
          (_east, _a16[1] - 10.0), (_east - 36.0, _a16[1] + 17.0), (_a16[0] + 8.0, _a16[1] + 15.0), (_a16[0] - 16.0, _a16[1] + 1.0)]
# The Frozen Aqueduct: west of the monastery's zigzag, from seg 27 to seg 32.
_a27, _a32 = _seg_point(27), _seg_point(32)
_west = min(p[0] for p in PATH if p[3] in (25, 26)) - 34.0
AQUEDUCT = [(_a27[0], _a27[1] + 4.0), (_west + 10.0, _a27[1] - 25.0), (_west, (_a27[1] + _a32[1]) / 2), (_west + 10.0, _a32[1] + 18.0),
            (_a32[0], _a32[1] - 2.0)]


def natural(x, y):
    """The mountainside: rising to the north, a great peak in the middle of the lap, the
    frozen gorge through the top, falling away to the west."""
    h = 36.0 + 0.075 * y + 1.5 * math.sin(x / 21.0) * math.cos(y / 17.0)
    dp = math.hypot(x - PEAK[0], y - PEAK[1])
    h += 55.0 * smooth((110.0 - dp) / 80.0)
    gorge = smooth((26.0 - abs(x - GORGE_X)) / 12.0) * smooth((y - 250.0) / 40.0)
    h = lerp(h, 18.0, gorge)
    h -= 14.0 * smooth((-x - 60.0) / 80.0)
    # The spiral climbs out of a hollow round the bastion's foot.
    db = math.hypot(x - BASTION[0], y - BASTION[1])
    h = lerp(h, 18.0, smooth((LAYOUT[33][1] + 26.0 - db) / 16.0))
    return h


def classify(c, n, info):
    if abs(c.x - GORGE_X) < 24.0 and c.y > 240.0 and c.z < 30.0:
        return ("sdp_ice_channel", "abyss")
    if n.z < 0.5:
        return ("sdp_slate", "wall")
    if n.z < 0.78:
        return ("sdp_scree", "deep_snow")
    if info["d"] < info["sample"].w / 2 + 2.0:
        return ("sdp_snowbank", "packed_snow")
    return ("sdp_snowfield", "deep_snow")


def box(bm, centre, size, rot=0.0):
    import props  # noqa: E402

    props.cuboid(bm, centre, size, rot=rot)


def main():
    import props  # noqa: E402
    from course_kit import bmesh  # noqa: E402

    def at(d):
        return c.at(TO_ROAD(d))

    c = kit.Course(TRACK_ID, "Snow Dragon Pass (v3 greybox)", "snow_dragon_pass")
    c.route(ROUTE, width=16.0, bank=7.0)
    snowbank = ("sdp_snowbank", "packed_snow")
    timber = ("timber_rail", "wall")
    parapet = ("sdp_redwall", "wall")
    c.kinds = {
        "gate": {"mat": "sdp_setts", "shoulder": 1.3, "shoulder_mat": ("kerb_redwhite", "road"), "barrier": 1.2, "barrier_mat": parapet},
        "village": {"mat": "sdp_setts", "shoulder": 1.3, "shoulder_mat": snowbank, "barrier": 0.9, "barrier_mat": timber},
        "road": {"mat": "sdp_road", "shoulder": 1.3, "shoulder_mat": snowbank},
        "cliff": {"mat": "sdp_road", "shoulder": 1.3, "shoulder_mat": snowbank, "barrier": 1.2, "barrier_mat": parapet, "deck": 4.0,
                  "deck_mat": ("sdp_slate", "wall")},
        "bridge": {"mat": "sdp_setts", "shoulder": 1.3, "shoulder_mat": ("sdp_aqueduct", "road"), "barrier": 1.3, "barrier_mat": parapet,
                   "deck": 4.0, "deck_mat": parapet, "ground": False},
        "kicker": {"mat": "sdp_setts", "shoulder": 1.3, "shoulder_mat": ("sdp_aqueduct", "road"), "deck": 4.0, "deck_mat": parapet,
                   "ground": False},
        "spiral": {"mat": "sdp_setts", "shoulder": 1.0, "shoulder_mat": ("kerb_redwhite", "road"), "barrier": 1.3, "barrier_mat": parapet,
                   "deck": 3.0, "deck_mat": parapet, "ground": False},
    }

    def label(smp):
        s = TO_PLAN(smp.s)
        seg = seg_of(s)
        if LIP <= s <= LAND:
            return "gap"
        if LIP - 12 <= s < LIP:
            return "kicker"
        if seg == 20:
            return "bridge"
        if seg in (1, 2, 3, 4):
            return "village"
        if seg in (8, 9, 10, 11, 12) or (seg == 29 and SEG[29] + 15 < s < SEG[30] - 15):
            return "cliff"
        if seg == 33:
            return "spiral"
        if seg in (0, 34):
            return "gate"
        return "road"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "kicker":
            specials.append((s0, s1, "kicker", {"lift": lambda u, n: 0.6 * max(0.0, (u - (n - 8)) / 8) ** 2}))
        elif k != "road":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "road", max_len=200.0))

    # The two other roads, at heights easing between where they leave and rejoin.
    def side_road(name, pts, s_from, s_to, mat):
        za, zb = road_z(SEG[s_from], s_from), road_z(SEG[s_to], s_to)
        out = []
        for i, (x, y) in enumerate(pts):
            out.append((x, y, lerp(za, zb, smooth(i / (len(pts) - 1))) - 0.05))
        c.shortcut(name, out, mat, "road", width=14.0, shoulder=1.0, shoulder_mat=snowbank)
        return za, zb

    za1, zb1 = side_road("Frozen Supply Road", SUPPLY, 6, 16, "sdp_road")
    za2, zb2 = side_road("Frozen Aqueduct", AQUEDUCT, 27, 32, "sdp_ice_channel")

    X0, X1, Y0, Y1 = -260, 480, -160, 520
    ter = c.terrain("Land", X0, X1, Y0, Y1, 6.0, natural, classify, near=10.0, fade=14.0, under=0.2)

    def under(x, y):
        return natural(x, y) - 0.4

    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 6.0, under, c.lib("sdp_snowfield", "deep_snow"))

    for piece in c.pieces:
        for kind, size in (("bridge", 2.0), ("kicker", 2.0), ("spiral", 1.4)):
            if piece.name.endswith(kind):
                kit.clear_piers(c, piece, [ter], every=14.0, mat=("sdp_slate", "wall"), size=size, inset=size + 1.0)
    # The bastion the spiral climbs round.
    rad = LAYOUT[33][1]
    bs = c.rock_mass("Bastion", BASTION[0], BASTION[1], rad - 14.0, rad - 14.0, 62.0, z0=10.0, n=20, seed=8)
    c.paint_rock(bs, ("sdp_redwall", "wall"), ("sdp_snowfield", "deep_snow"))

    # The ice cavern on the supply road, and the aqueduct's tunnel: arches over them.
    bm = bmesh.new()
    for pts, za, zb, f in ((SUPPLY, za1, zb1, 0.55), (AQUEDUCT, za2, zb2, 0.5)):
        i = int(f * (len(pts) - 1))
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        rot = math.atan2(y1 - y0, x1 - x0)
        for k in range(6):
            u = (k + 0.5) / 6
            x, y = lerp(x0, x1, u), lerp(y0, y1, u)
            z = lerp(za, zb, smooth(f)) - 0.5
            nx, ny = -math.sin(rot), math.cos(rot)
            for side in (-1, 1):
                box(bm, (x + nx * side * 9.5, y + ny * side * 9.5, z + 4.0), (6.0, 2.0, 9.0), rot=rot)
            box(bm, (x, y, z + 9.5), (6.0, 21.0, 2.0), rot=rot)
    arches = c.mesh_object("Caverns", bm, "Props")
    c.assign(arches, c.lib("glacier_ice", "wall"))

    # Plain blocks: the village, the storehouses, the monastery, the gate.
    bm = bmesh.new()
    s = 24.0
    k = 0
    while s < SEG[5]:
        q = at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 8.0 + 2 * (k % 2)))
            h = 5.0 + 2.0 * ((k + (side > 0)) % 3)
            box(bm, (p.x, p.y, q.p.z + h / 2 - 0.5), (8.0, 8.0, h), rot=math.atan2(q.t.y, q.t.x))
        s += 14.0
        k += 1
    s = SEG[16] + 10
    k = 0
    while s < SEG[20] - 6:
        q = at(s)
        side = 1 if k % 2 else -1
        p = q.side(side * (q.w / 2 + 9.0))
        box(bm, (p.x, p.y, q.p.z + 2.5), (12.0, 8.0, 5.0), rot=math.atan2(q.t.y, q.t.x))
        s += 22.0
        k += 1
    mc = _arc_centre(29)
    zm = road_z(SEG[29], 29)
    box(bm, (mc[0], mc[1], zm + 7.0), (14.0, 14.0, 16.0))
    q = at(10.0)
    for side in (-1, 1):
        p = q.side(side * (q.w / 2 + 3.0))
        box(bm, (p.x, p.y, q.p.z + 6.0), (4.0, 4.0, 13.0), rot=math.atan2(q.t.y, q.t.x))
    box(bm, (q.p.x, q.p.y, q.p.z + 13.5), (4.0, q.w + 10.0, 2.5), rot=math.atan2(q.t.y, q.t.x))
    blocks = c.mesh_object("Buildings", bm, "Props")
    c.assign(blocks, c.lib("sdp_slate", "wall"))

    c.start_line()
    S = lambda i: TO_ROAD(SEG[i])  # noqa: E731
    # Zippers: out of the village, onto Starvation Road, on the broken bridge's run-up,
    # down the Avalanche Run, out of the second choice.
    for at in (S(5) + 4, S(16) + 6, TO_ROAD(LIP - 40), S(24) + 20, S(32) + 2):
        c.zipper(at, 0)
    for at, across in ((S(2) + 20, 0), (S(10) + 20, 0), (S(18) + 30, 0), (S(25) + 20, 0), (S(28) + 10, 0), (S(33) + 120, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (S(1) + 20, -4, "red"),
        (S(1) + 20, 4, "blue"),
        (S(12) + 10, 0, "green"),
        (S(17) + 10, 0, "yellow"),
        (S(22) + 6, 0, "rainbow"),
        (S(26) + 30, -4, "red"),
        (S(26) + 30, 4, "blue"),
        (S(33) + 60, 0, "green"),
    ):
        c.balloon(at, across, col)
    c.entity("respawn", **{"from": round(TO_ROAD(LIP - 20), 1), "to": round(TO_ROAD(LAND + 4), 1), "at": round(TO_ROAD(LAND + 18), 1)})

    # Checkpoints, with a twin gate across each other road (either counts), none
    # elsewhere in the stretches they skip.
    s1_in, s1_out = kit.s_near(c, *SUPPLY[0], za1), kit.s_near(c, *SUPPLY[-1], zb1)
    s2_in, s2_out = kit.s_near(c, *AQUEDUCT[0], za2), kit.s_near(c, *AQUEDUCT[-1], zb2)
    m1, m2 = (s1_in + s1_out) / 2, (s2_in + s2_out) / 2
    gates = c.checkpoints(
        extra=[S(2), m1, S(18), S(21) + 10, S(24), m2, S(33) + 80, S(33) + 180],
        avoid=[(s1_in - 4, m1 - 8), (m1 + 8, s1_out + 4), (s2_in - 4, m2 - 8), (m2 + 8, s2_out + 4), (TO_ROAD(LIP - 14), TO_ROAD(LAND + 8))],
        height=10.0,
    )
    for m, pts, za, zb, name in ((m1, SUPPLY, za1, zb1, "frozen_supply_road"), (m2, AQUEDUCT, za2, zb2, "frozen_aqueduct")):
        main_gate = min(gates.items(), key=lambda kv: abs(kv[0] - m))[1]
        j = len(pts) // 2
        c.alt_gate(main_gate, name, [(pts[j - 1][0], pts[j - 1][1], lerp(za, zb, 0.4)), (pts[j][0], pts[j][1], lerp(za, zb, 0.5)),
                                     (pts[j + 1][0], pts[j + 1][1], lerp(za, zb, 0.6))], width=16.0)

    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish()
    print("lap", round(c.length, 1))


if __name__ == "__main__":
    main()
