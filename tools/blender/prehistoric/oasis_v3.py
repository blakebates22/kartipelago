# Oasis Haven v3: the GREYBOX of the new lap (Blake's notes, 2026-10-23, and concept A/D).
# Driving first: the new lap, playable with plain shapes, so it can be driven and changed
# quickly; the look comes once the lap is fun. Builds its own package, oasis_haven_v3
# (?track=oasis_haven_v3); the current Oasis Haven stays as it is.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/oasis_v3.py      (the bpy module)
#
# Back in the desert: a small oasis (a pool, palms, a few mud-brick houses, a nomad camp),
# and all round it dunes and wind-carved rock under a bright turquoise sky. About 1.55 km,
# nearly all bends, like Bonebog:
#
#   A  The village gate: the start among the mud-brick houses, an S-bend, and a long
#      sweep south round the pool (or straight on through the palm grove on its north
#      bank: the shortcut).
#   B  The camp: weaving north between the tents and their lanterns.
#   C  The butte: a hairpin round it, then west under the wind-carved arch.
#   D  The dune sea: rolling crests over fast sweepers.
#   E  The watchtower: one and a quarter turns up round a ruined tower on its mesa (the
#      road passes over itself), then the chute down to the start, with a dune-lip jump.

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import bmesh, lerp, smooth  # noqa: E402

TRACK_ID = "oasis_haven_v3"

START = (0.0, 0.0)
LAYOUT = [
    ("S", 60),  # 0  A: the start, south out of the village
    ("L", 35, 50),  # 1  an S-bend past the houses
    ("R", 35, 50),  # 2
    ("L", 40, 90),  # 3  east
    ("S", 40),  # 4  (the palm-grove shortcut leaves straight on from the end of this)
    ("R", 45, 75),  # 5  the long sweep south round the pool...
    ("L", 45, 150),  # 6
    ("R", 45, 75),  # 7  ...and back
    ("S", 30),  # 8  (the shortcut comes back in here)
    ("L", 35, 90),  # 9  north
    ("R", 30, 60),  # 10 B: weaving north through the camp
    ("L", 30, 120),  # 11
    ("R", 30, 60),  # 12
    ("S", 20),  # 13
    ("L", 30, 60),  # 14
    ("R", 30, 60),  # 15
    ("R", 35, 90),  # 16 C: out of the camp, east
    ("S", 20),  # 17
    ("L", 28, 180),  # 18 the hairpin round the butte
    ("S", 30),  # 19 west, under the arch
    ("S", 30),  # 20 D: the dune sea: crests...
    ("R", 45, 40),  # 21 ...over the sweepers
    ("L", 45, 80),  # 22
    ("R", 45, 40),  # 23
    ("S", 80),  # 24 two big crests (stretched to close the loop)
    ("L", 30, 450),  # 25 E: the spiral up round the watchtower
    ("R", 26, 50),  # 26 off the mesa, away from the tower
    ("S", 80),  # 27 the chute: the dune-lip jump (stretched to close the loop)
    ("L", 40, 50),  # 28 onto the start
]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 24, 27, START, 270.0)
SEG = kit.segment_starts(PATH)
LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))

# The jump down the chute: (lip, landing). The chute eases off to a near-level kicker at
# the lip, a 14 m gap over a dry wash, and a long landing that runs on downhill.
LIP = SEG[27] + 45.0
LAND = LIP + 14.0

# Heights at segment starts; between them the road eases (the spiral climbs steadily).
HEIGHT = {
    0: 3.0, 1: 3.0, 2: 2.8, 3: 2.6, 4: 2.4, 5: 2.4, 6: 2.0, 7: 2.0, 8: 2.4, 9: 2.6,
    10: 3.0, 11: 3.4, 12: 3.8, 13: 4.2, 14: 4.6, 15: 5.0, 16: 5.6, 17: 6.5, 18: 7.0, 19: 8.0,
    20: 8.0, 21: 8.2, 22: 8.6, 23: 8.8, 24: 9.0, 25: 9.0, 26: 21.0, 27: 20.0, 28: 4.0,
}
# Rolling crests: (segment, how many, how high).
CRESTS = {4: (1, 1.2), 8: (1, 1.0), 19: (1, 1.4), 20: (1, 1.8), 21: (1, 1.2), 22: (2, 1.4), 23: (1, 1.2), 24: (2, 2.0)}


def seg_of(s):
    k = 0
    for i, d in SEG.items():
        if d <= s:
            k = max(k, i)
    return k


def _chute(d):
    a, b = SEG[27], SEG[28]
    if d <= LIP - 12:
        return lerp(HEIGHT[27], 15.0, smooth((d - a) / (LIP - 12 - a)))
    if d <= LIP:
        return lerp(15.0, 14.6, (d - (LIP - 12)) / 12)
    if d <= LAND:
        return lerp(14.6, 10.0, (d - LIP) / (LAND - LIP))
    return lerp(10.0, HEIGHT[28], (d - LAND) / (b - LAND))


def road_z(d, seg):
    if seg == 27:
        return _chute(d)
    a, b = SEG[seg], SEG.get(seg + 1, LENGTH)
    t = (d - a) / max(1e-6, b - a)
    z0, z1 = HEIGHT[seg], HEIGHT.get(seg + 1, HEIGHT[0])
    z = lerp(z0, z1, t if seg == 25 else smooth(t))
    if seg in CRESTS:
        n, h = CRESTS[seg]
        z += h * math.sin(t * math.pi * n) ** 2
    return z


def road_w(d, seg):
    if seg in (0, 1, 2, 3, 28):
        return 16.0  # the village street
    if seg == 25:
        return 14.0  # the spiral
    if seg == 27:
        return 17.0  # the chute
    return 15.0


ROUTE = kit.route_points_by(PATH, road_z, every=10.0, width=road_w)


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
WASH = [(p[0], p[1]) for p, d in zip(PATH, _D) if LIP - 2 <= d <= LAND + 2][::2]

BUTTE = _arc_centre(18)
TOWER = _arc_centre(25)
_c6 = _arc_centre(6)
POOL = (_c6[0], _c6[1] - 8.0, 19.0)  # centre and radius: inside the sweep south
MID = (180.0, 0.0)

# The palm-grove shortcut: from the end of the street east (seg 4) straight on along the
# pool's north bank, between the palms, back onto the road at seg 8.
_p4, _p8 = _seg_point(5), _seg_point(8)
SHORTCUT = [(_p4[0] - 6.0, _p4[1]), (_p4[0] + 30.0, _p4[1] + 3.0), ((_p4[0] + _p8[0]) / 2, _p4[1] + 5.0),
            (_p8[0] - 30.0, _p8[1] + 3.0), (_p8[0] + 6.0, _p8[1])]


def natural(x, y):
    """The desert: dunes in long ridges, rising to a plateau in the north, the pool's
    basin, and mesas all round."""
    u = 0.5 + 0.5 * math.sin(x / 19.0 + 1.3 * math.sin(y / 37.0))
    h = 2.0 + 3.2 * u ** 3 + 1.2 * math.sin(y / 23.0 + x / 53.0) + 0.6 * math.sin(x / 7.3) * math.cos(y / 9.1)
    h += 6.0 * smooth((y - 60.0) / 90.0)
    dp = math.hypot(x - POOL[0], y - POOL[1])
    h = lerp(h, -1.6, smooth((POOL[2] + 10.0 - dp) / 12.0))
    if WASH:
        dw = min(math.hypot(x - p[0], y - p[1]) for p in WASH)
        h = lerp(h, 1.0, smooth((22.0 - dw) / 10.0))
    r = math.hypot((x - MID[0]) * 0.9, y - MID[1])
    h += 45.0 * smooth((r - 330.0) / 70.0) * (0.85 + 0.15 * math.sin(math.atan2(y, x) * 9))
    return h


def in_wash(x, y, z):
    """In the dry wash under the chute's jump (fall in and you're put back past it)."""
    return any(math.hypot(x - p[0], y - p[1]) < 16.0 for p in WASH) and z < 8.0


def classify(c, n, info):
    if in_wash(c.x, c.y, c.z):
        return ("gold_sand", "abyss")
    if n.z < 0.62:
        return ("gold_cliff", "wall")
    if math.hypot(c.x - POOL[0], c.y - POOL[1]) < POOL[2] + 5 and c.z < 0.5:
        return ("lake_sand", "water")
    if math.hypot(c.x - POOL[0], c.y - POOL[1]) < POOL[2] + 22:
        return ("oasis_lawn", "grass")
    if info["d"] < 11:
        return ("pale_sand", "dirt")
    return ("gold_sand", "loose_sand")


def box(bm, centre, size, rot=0.0):
    import props  # noqa: E402

    props.cuboid(bm, centre, size, rot=rot)


def main():
    import props  # noqa: E402

    c = kit.Course(TRACK_ID, "Oasis Haven (v3 greybox)", "oasis_haven")
    c.route(ROUTE, width=15.0, bank=7.0)
    wall = ("oasis_stone", "wall")
    c.kinds = {
        "street": {"mat": "oasis_paving", "shoulder": 1.4, "shoulder_mat": ("tile_border", "road"), "barrier": 0.8, "barrier_mat": wall},
        "trail": {"mat": "dash_road", "surface": "road", "shoulder": 1.6, "shoulder_mat": ("pale_sand", "dirt")},
        "spiral": {
            "mat": "oasis_paving",
            "surface": "road",
            "shoulder": 0.6,
            "shoulder_mat": ("tile_border", "road"),
            "barrier": 1.3,
            "barrier_mat": ("balustrade", "wall"),
            "deck": 2.2,
            "deck_mat": wall,
            "ground": False,
        },
        "ramp": {"mat": "dash_road", "surface": "road", "shoulder": 1.6, "shoulder_mat": ("pale_sand", "dirt")},
    }

    def label(smp):
        s = smp.s
        seg = seg_of(s)
        if LIP <= s <= LAND:
            return "gap"
        if LIP - 12 <= s < LIP:
            return "ramp"
        if seg in (0, 1, 2, 28):
            return "street"
        if seg == 25 or (seg == 26 and s < SEG[26] + 12):
            return "spiral"
        return "trail"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "ramp":
            specials.append((s0, s1, "ramp", {"lift": lambda u, n: 0.8 * max(0.0, (u - (n - 8)) / 8) ** 2}))
        elif k != "trail":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "trail", max_len=200.0))

    # The shortcut along the pool's bank, at the road's height where it leaves and rejoins.
    za, zb = road_z(SEG[5], 4), road_z(SEG[8], 8)
    sc = [(x, y, lerp(za, zb, i / (len(SHORTCUT) - 1)) - 0.05) for i, (x, y) in enumerate(SHORTCUT)]
    c.shortcut("Palm Grove", sc, "dash_road", "road", width=8.0, shoulder=0.8, shoulder_mat=("oasis_lawn", "grass"))

    X0, X1, Y0, Y1 = -260, 620, -440, 420
    c.terrain("Desert", X0, X1, Y0, Y1, 6.0, natural, classify, near=10.0, fade=18.0, under=0.2)
    c.disc("Pool", POOL[0], POOL[1], POOL[2] + 4.0, 0.0, c.lib("lagoon", "deep_water"), n=40)

    def under(x, y):
        return natural(x, y) - 0.4

    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 6.0, under, c.lib("gold_sand", "loose_sand"))

    # The butte inside the hairpin, and the arch over the road beyond it.
    bt = c.rock_mass("Butte", BUTTE[0], BUTTE[1], 15.0, 14.0, 34.0, z0=-4, n=14, seed=5)
    c.paint_rock(bt, ("gold_cliff", "wall"), ("pale_sand", "dirt"))
    q = c.at(SEG[19] + 20)
    bm = bmesh.new()
    for side in (-1, 1):
        p = q.side(side * (q.w / 2 + 6.0))
        box(bm, (p.x, p.y, q.p.z + 5.0), (8.0, 9.0, 16.0), rot=math.atan2(q.t.y, q.t.x))
    box(bm, (q.p.x, q.p.y, q.p.z + 14.5), (8.0, q.w + 20.0, 5.0), rot=math.atan2(q.t.y, q.t.x))
    arch = c.mesh_object("Rock Arch", bm, "Rocks")
    c.assign(arch, c.lib("gold_cliff", "wall"))

    # The ruined watchtower the spiral climbs round.
    bm = bmesh.new()
    props.loft(bm, [props.ring(bm, TOWER, 17.0, -2.0, 16), props.ring(bm, TOWER, 15.5, 24.0, 16)], cap_top=True)
    for k in range(12):
        a = k * math.tau / 12
        box(bm, (TOWER[0] + 14.8 * math.cos(a), TOWER[1] + 14.8 * math.sin(a), 25.5), (3.0, 3.0, 3.0), rot=a)
    tower = c.mesh_object("Watchtower", bm, "Rocks")
    c.assign(tower, c.lib("arcade_ochre", "wall"))

    # The village: a few mud-brick houses along the street.
    bm = bmesh.new()
    s = 6.0
    k = 0
    while s < SEG[3]:
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 9.0 + 3 * (k % 2)))
            h = 6.0 + 2.5 * ((k + (side > 0)) % 3)
            box(bm, (p.x, p.y, q.p.z + h / 2 - 0.5), (9.0, 8.0, h), rot=math.atan2(q.t.y, q.t.x))
        s += 16.0
        k += 1
    q = c.at(LENGTH - 30)
    for side in (-1, 1):
        p = q.side(side * (q.w / 2 + 10.0))
        box(bm, (p.x, p.y, q.p.z + 3.5), (10.0, 9.0, 8.0), rot=math.atan2(q.t.y, q.t.x))
    houses = c.mesh_object("Houses", bm, "Props")
    c.assign(houses, c.lib("terracotta", "wall"))

    # The camp: tents either side of the weave, with lanterns.
    bm = bmesh.new()
    roofs = bmesh.new()
    s = SEG[10] + 8
    k = 0
    lanterns = []
    while s < SEG[16]:
        q = c.at(s)
        side = 1 if k % 2 else -1
        p = q.side(side * (q.w / 2 + 8.0))
        rot = math.atan2(q.t.y, q.t.x)
        box(bm, (p.x, p.y, q.p.z + 1.5), (9.0, 7.0, 3.0), rot=rot)
        box(roofs, (p.x, p.y, q.p.z + 3.6), (11.0, 9.0, 1.2), rot=rot)
        lp = q.side(side * (q.w / 2 + 2.2))
        lanterns.append((lp.x, lp.y, q.p.z + 3.2))
        s += 18.0
        k += 1
    tents = c.mesh_object("Tents", bm, "Props")
    c.assign(tents, c.lib("rug", "wall"))
    tr = c.mesh_object("Tent Roofs", roofs, "Props")
    c.assign(tr, c.lib("awning_rose", "wall"))
    for x, y, z in lanterns:
        g = c.game(x, y, z)
        c.entity("torch", x=g[0], y=g[1], z=g[2])

    # Palms round the pool and along the shortcut (two in it to dodge).
    palm = props.palm(c, 10.0)
    ter = list(c.coll("Terrain").objects)
    for k in range(22):
        a = k * math.tau / 22
        r = POOL[2] + 9.0 + 4.0 * math.sin(k * 2.1)
        x, y = POOL[0] + r * math.cos(a), POOL[1] + r * math.sin(a)
        if props.clear_of_road(c, x, y, 3.0):
            z = c.ground_z(x, y, ter) or 1.0
            c.place(palm, x, y, z - 0.2, rot=a * 3, scale=0.9 + 0.3 * math.sin(k))
    for f, off in ((0.38, 1.8), (0.66, -1.8)):
        i = int(f * (len(SHORTCUT) - 1))
        x0, y0 = SHORTCUT[i]
        x1, y1 = SHORTCUT[i + 1]
        t = f * (len(SHORTCUT) - 1) - i
        x, y = lerp(x0, x1, t), lerp(y0, y1, t) + off
        z = c.ground_z(x, y, ter) or 2.0
        c.place(palm, x, y, z - 0.2, rot=f * 9, scale=1.1)

    c.start_line()
    S = lambda i: SEG[i]  # noqa: E731
    # Zippers: onto the sweep round the pool, out of it, out of the camp, west under the
    # arch, and onto the spiral.
    for at in (S(4) + 6, S(8) + 6, S(13) + 4, S(19) + 4, S(24) + 40):
        c.zipper(at, 0)
    for at, across in ((S(6) + 40, 0), (S(11) + 30, 0), (S(18) + 40, 0), (S(22) + 30, 0), (S(28) + 10, -3)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (S(1) + 20, -4, "red"),
        (S(1) + 20, 4, "blue"),
        (S(7) + 20, 0, "green"),
        (S(12) + 10, 0, "yellow"),
        (S(17) + 10, 0, "rainbow"),
        (S(21) + 10, -4, "red"),
        (S(21) + 10, 4, "blue"),
        (S(25) + 120, 0, "green"),
    ):
        c.balloon(at, across, col)
    # A missed jump: put down past it.
    c.entity("respawn", **{"from": round(LIP - 20, 1), "to": round(LAND + 4, 1), "at": round(LAND + 20, 1)})

    # Checkpoints: one in the middle of the stretch the shortcut skips, with a twin gate
    # across the shortcut (either counts), and none elsewhere in that stretch.
    s_in, s_out = kit.s_near(c, *SHORTCUT[0]), kit.s_near(c, *SHORTCUT[-1])
    apex = (s_in + s_out) / 2
    gates = c.checkpoints(
        extra=[S(2), apex, S(10) + 30, S(13), S(16) + 20, S(18) + 50, S(21), S(24) + 20, S(25) + 100, S(25) + 200, LAND + 25],
        avoid=[(s_in - 4, apex - 8), (apex + 8, s_out + 4)],
        height=10.0,
    )
    main_gate = min(gates.items(), key=lambda kv: abs(kv[0] - apex))[1]
    mid = SHORTCUT[2]
    c.alt_gate(main_gate, "palm_grove", [(SHORTCUT[1][0], SHORTCUT[1][1], za), (mid[0], mid[1], za), (SHORTCUT[3][0], SHORTCUT[3][1], zb)], width=14.0)

    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish()
    # A bright turquoise desert afternoon (Blake's pick of the concept skies).
    path = os.path.join(kit.TRACKS_DIR, TRACK_ID, "look.json")
    with open(path, encoding="utf-8") as f:
        look = json.load(f)
    look["sky"] = "#2fb8cf"
    look.setdefault("fog", {}).update({"enabled": True, "color": "#cdeee6", "near": 500, "far": 2600})
    dome = look.setdefault("skyDome", {})
    dome.update({"top": "#0f8fb0", "horizon": "#bfe8df", "bottom": "#f6e2b0"})
    dome.setdefault("sun", {}).update({"color": "#fffdf2", "glow": "#fff3c4", "elevation": 52})
    dome.setdefault("hills", {}).update({"color": "#c98a63", "far": "#e9b27e", "style": "mesas"})
    look.setdefault("ambient", {}).update({"sky": "#c8f0ec"})
    with open(path, "w", encoding="utf-8") as f:
        json.dump(look, f, indent=2)
        f.write("\n")
    print("lap", round(c.length, 1))


if __name__ == "__main__":
    main()
