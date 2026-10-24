# Aurora Rift v3: a greybox of a new lap, to drive before it's dressed (?track=aurora_rift_v3).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/aurora_rift_v3.py      (the bpy module)
#
# Blake: redo Aurora Rift (Oct 24): a new lap, about 20% shorter (2.45 km -> about 1.95),
# nearly all corners, more going on in the cave, and less after it. The same places in
# the same order, in plain shapes:
#
#   1  The Shattered Entrance: the start on the snowfield, east along the Rift's rim, and
#      a tight S down the ice wall onto the natural ice bridge, north into the glacier.
#   2  The Crystal Cathedral (the cave): out of the tunnel onto the cliffside drift, a
#      hairpin round the Monolith, the broken bridge over the abyss (a jump), up onto the
#      north wall and the causeway into the Rift Loop.
#   3  Mirror Lake: down the crystal tunnel to the frozen lake, an S of drifts on the ice.
#   4  The Aurora Ascent and the Great Rift Bridge: one climbing hairpin up the canyon,
#      out under the sky and south over the bridge.
#   5  The final descent: an S back down the snowfield and the last drift to the line.
#
# The current Aurora Rift is untouched (aurora_rift.py).

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp, smooth  # noqa: E402

TRACK_ID = "aurora_rift_v3"

LOOP_R, LOOP_RAMP, LOOP_SHIFT = 24.0, 28.0, 18.0
START = (0.0, -250.0)
LAYOUT = [
    ("S", 40),  # 0  1: the start, north across the snowfield
    ("R", 40, 90),  # 1  east along the Rift's rim
    ("L", 30, 50),  # 2  a tight S down the ice wall...
    ("R", 30, 100),  # 3
    ("L", 30, 140),  # 4  ...and north
    ("S", 45),  # 5  the natural ice bridge across the Rift
    ("S", 35),  # 6  the tunnel into the glacier, down
    ("L", 35, 90),  # 7  2: the Cathedral: the cliffside drift, west
    ("R", 28, 180),  # 8  the hairpin round the Monolith
    ("S", 70),  # 9  the broken bridge over the abyss (the jump)
    ("L", 35, 90),  # 10 up onto the north wall
    ("S", 40),  # 11 the causeway: the loop approach
    ("LOOP", LOOP_R, LOOP_RAMP, LOOP_SHIFT),  # 12 the Rift Loop
    ("S", 25),  # 13
    ("L", 35, 90),  # 14 3: down the crystal tunnel, west
    ("R", 50, 70),  # 15 Mirror Lake: a weave of drifts on the ice
    ("L", 50, 140),  # 16
    ("R", 55, 70),  # 17
    ("S", 60),  # 18 off the ice into the ascent (closes the lap)
    ("L", 30, 90),  # 19 4: the climbing turn, south
    ("S", 40),  # 20 up the canyon...
    ("R", 40, 70),  # 21 ...weaving under the arches
    ("L", 40, 140),  # 22
    ("R", 40, 70),  # 23
    ("S", 120),  # 24 out under the sky and over the Great Rift Bridge (closes the lap)
    ("L", 45, 60),  # 25 5: the final descent, an S...
    ("R", 45, 60),  # 26
    ("L", 40, 90),  # 27 ...east
    ("S", 40),  # 28
    ("L", 40, 90),  # 29 the last drift
    ("S", 30),  # 30 onto the finish straight
]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 18, 24, START, 90.0)
SEG = kit.segment_starts(PATH)
LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))
LOOP_SEG = 12


def seg_of(s):
    k = 0
    for i, d in SEG.items():
        if d <= s:
            k = max(k, i)
    return k


def _seg_point(i):
    return next(p for p in PATH if p[3] == i)


def _seg_points(i):
    return [p for p in PATH if p[3] == i]


def _arc_centre(i):
    x, y, h, _ = _seg_point(i)
    sg = LAYOUT[i]
    a = math.radians(h + (90 if sg[0] == "L" else -90))
    return (x + sg[1] * math.cos(a), y + sg[1] * math.sin(a))


MONOLITH = _arc_centre(8)
LOOP_IN = PATH[[k for k, p in enumerate(PATH) if p[3] == LOOP_SEG][0] - 1]
LOOP_HEAD = LOOP_IN[2]

# ---------------------------------------------------------------- heights

Z_START = 44.0  # the snowfield
Z_CATH = 24.0  # the Cathedral's roads (and the Loop)
Z_LAKE = 11.0  # Mirror Lake's ice
Z_BRIDGE = 56.0  # the Great Rift Bridge
HEIGHT = {
    0: Z_START, 1: Z_START, 2: 42.0, 3: 39.0, 4: 36.0, 5: 34.0, 6: 33.5, 7: Z_CATH + 3.0, 8: Z_CATH + 1.0,
    9: Z_CATH + 1.0, 10: Z_CATH + 1.0, 11: Z_CATH, 12: Z_CATH, 13: Z_CATH, 14: Z_CATH, 15: Z_LAKE + 0.4,
    16: Z_LAKE + 0.4, 17: Z_LAKE + 0.4, 18: Z_LAKE + 0.4, 19: 22.0, 20: 27.0, 21: 34.0, 22: 42.0, 23: 51.0,
    24: Z_BRIDGE, 25: 53.0, 26: 50.0, 27: 47.0, 28: 46.0, 29: 45.0, 30: Z_START,
}
# The broken bridge's jump: (lip, landing) along the lap.
LIP = SEG[9] + 30.0
LAND = LIP + 10.0


def _base_z(d, seg):
    a, b = SEG[seg], SEG.get(seg + 1, LENGTH)
    t = (d - a) / max(1e-6, b - a)
    z0, z1 = HEIGHT[seg], HEIGHT.get(seg + 1, HEIGHT[0])
    if seg == 24:
        # Dead level across the bridge, easing down off its far end.
        return lerp(Z_BRIDGE, z1, smooth(max(0.0, (d - (b - 30)) / 30.0)))
    if seg in (11, 12, 13) or seg in (16, 17):
        return z0
    return lerp(z0, z1, smooth(t))


road_z = kit.with_jumps(_base_z, seg_of, [(LIP, LAND, 2.5, 0.9)])


def road_w(d, seg):
    if seg in (0, 30) or d < 40:
        return 18.0
    if seg in (11, 12, 13):
        return 14.0  # the causeway: as wide as the Loop
    if seg in (15, 16, 17):
        return 18.0  # the lake
    if seg in (5, 6, 9):
        return 15.0
    return 16.0


ROUTE, SHARP, LOOPS = kit.route_with_loops(PATH, LAYOUT, road_z, every=8.0, width=road_w)
TO_ROAD, TO_PLAN = kit.along(PATH, road_z)

# ---------------------------------------------------------------- the land

# The Rift: the chasm running east-west between the snowfield (south) and the glacier.
RIFT_Y = (_seg_point(5)[1] + _seg_point(6)[1]) / 2
RIFT_HALF = 26.0
LAKE = _arc_centre(16)


def _lap_index():
    pts = [(p[0], p[1], road_z(SEG[p[3]] + 0.0, p[3])) for p in PATH[::3]]
    return pts


_PTS = None


def near_road_z(x, y):
    global _PTS
    if _PTS is None:
        _PTS = []
        d = 0.0
        for i, p in enumerate(PATH):
            if i:
                d += math.hypot(p[0] - PATH[i - 1][0], p[1] - PATH[i - 1][1])
            if i % 3 == 0:
                _PTS.append((p[0], p[1], road_z(d, p[3])))
    best = None
    bd = 1e18
    for px, py, pz in _PTS:
        dd = (px - x) ** 2 + (py - y) ** 2
        if dd < bd:
            bd, best = dd, pz
    return best, math.sqrt(bd)


def natural(x, y):
    """Plain ground: the height of the nearest road (so each part of the lap has its
    own level, cliffs between), the Rift's chasm, the abyss round the Monolith, and
    Mirror Lake's ice."""
    z, d = near_road_z(x, y)
    if abs(y - RIFT_Y) < RIFT_HALF and d > 12:
        return -40.0
    if math.hypot(x - MONOLITH[0], y - MONOLITH[1]) < 18:
        return -40.0
    if abs(z - (Z_CATH + 1.0)) < 2.0 and d > 16 and y > RIFT_Y + RIFT_HALF:
        return -40.0  # the Cathedral's floor is an abyss off the roads
    if math.hypot(x - LAKE[0], y - LAKE[1]) < 90 and abs(z - (Z_LAKE + 0.4)) < 1.0:
        return Z_LAKE
    return z - 1.0 + 0.6 * math.sin(x / 23.0) * math.cos(y / 19.0)


def classify(c, n, info):
    if c.z < -10:
        return ("rift_mist", "abyss")
    if n.z < 0.6:
        return ("glacier_wall", "wall")
    if abs(c.z - Z_LAKE) < 0.8 and math.hypot(c.x - LAKE[0], c.y - LAKE[1]) < 90:
        return ("mirror_ice", "ice")
    if info["d"] < 11:
        return ("rift_stone", "snow_stone")
    return ("rift_snow", "packed_snow")


def main():
    import props  # noqa: E402
    from course_kit import bmesh  # noqa: E402

    c = kit.Course(TRACK_ID, "Aurora Rift (v3 greybox)", "aurora_rift")
    (ex, ey, _), (xx, xy, _) = LOOPS[0]
    c.route(ROUTE, width=16.0, bank=6.0, sharp=SHARP, flat=[(ex, ey, 46), (xx, xy, 46)])
    lamps = ("edge_amber", "wall")
    snowbank = ("rift_snow", "packed_snow")
    stone = ("rift_stone", "wall")
    ice_wall = ("glacier_wall", "wall")
    c.kinds = {
        "snowfield": {"mat": "rift_road", "shoulder": 1.8, "shoulder_mat": snowbank},
        "ledge": {"mat": "rift_road", "shoulder": 1.0, "shoulder_mat": snowbank, "barrier": 1.0, "barrier_mat": lamps,
                  "deck": 7.0, "deck_mat": ("rift_cliff", "wall"), "ground": False},
        "icebridge": {"mat": "rift_road", "shoulder": 1.0, "shoulder_mat": ("glacier_wall", "snow_stone"), "barrier": 0.9,
                      "barrier_mat": ice_wall, "deck": 9.0, "deck_mat": ice_wall, "ground": False},
        "tunnel": {"mat": "rift_road", "shoulder": 1.2, "shoulder_mat": ("cavern_ice", "snow_stone")},
        "cathedral": {"mat": "rift_road", "shoulder": 1.0, "shoulder_mat": ("rift_stone", "snow_stone"), "barrier": 1.0, "barrier_mat": lamps,
                      "deck": 8.0, "deck_mat": ("rift_rock", "wall"), "ground": False},
        "bridge": {"mat": "rift_road", "shoulder": 0.8, "shoulder_mat": ("rift_stone", "snow_stone"), "barrier": 1.2, "barrier_mat": stone,
                   "deck": 3.5, "deck_mat": stone, "ground": False},
        "kicker": {"mat": "rift_road", "shoulder": 0.8, "shoulder_mat": ("rift_stone", "snow_stone"), "deck": 3.5, "deck_mat": stone,
                   "ground": False},
        "causeway": {"mat": "rift_road", "shoulder": 0.8, "shoulder_mat": ("rift_stone", "snow_stone"), "barrier": 1.1, "barrier_mat": lamps,
                     "deck": 4.5, "deck_mat": stone, "ground": False, "exact": True},
        "lake": {"mat": "rift_ice_road", "shoulder": 2.0, "shoulder_mat": ("mirror_ice", "ice")},
        "climb": {"mat": "rift_road", "shoulder": 1.2, "shoulder_mat": snowbank},
        "greatbridge": {"mat": "rift_road", "shoulder": 0.8, "shoulder_mat": ("rift_stone", "snow_stone"), "barrier": 1.3,
                        "barrier_mat": ("rift_carved", "wall"), "deck": 4.0, "deck_mat": stone, "ground": False},
    }
    s_in = kit.s_near(c, ex, ey)
    s_out = kit.s_near(c, xx, xy)
    lip, land = TO_ROAD(LIP), TO_ROAD(LAND)

    def label(smp):
        s = smp.s
        if s_in <= s <= s_out or lip <= s <= land:
            return "gap"
        if lip - 12 <= s < lip:
            return "kicker"
        seg = seg_of(TO_PLAN(s))
        x, y = smp.p.x, smp.p.y
        if seg in (2, 3, 4):
            return "ledge"
        if seg == 5:
            return "icebridge" if abs(y - RIFT_Y) < RIFT_HALF + 4 else "tunnel"
        if seg == 6:
            return "tunnel"
        if seg in (7, 8, 10):
            return "cathedral"
        if seg == 9:
            return "bridge"
        if seg in (11, 12, 13):
            return "causeway"
        if seg == 14:
            return "tunnel"
        if seg in (15, 16, 17):
            return "lake"
        if seg in (18, 19, 20, 21, 22, 23):
            return "climb"
        if seg == 24:
            return "greatbridge" if abs(y - RIFT_Y) < RIFT_HALF + 6 else "climb"
        return "snowfield"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "kicker":
            specials.append((s0, s1, "kicker", {"lift": lambda u, n: 0.6 * max(0.0, (u - (n - 8)) / 8) ** 2}))
        elif k != "snowfield":
            specials.append((s0, s1, k))
    snap = lambda v: s_in if abs(v - s_in) < 3 else s_out if abs(v - s_out) < 3 else v  # noqa: E731
    specials = [(snap(a), snap(b)) + tuple(rest) for a, b, *rest in specials]
    c.roads(kit.plan(c, specials, "snowfield", max_len=200.0))

    lp = kit.LoopPath(ex, ey, Z_CATH, LOOP_HEAD, LOOP_R, LOOP_RAMP, LOOP_SHIFT, 14.0)
    c.loop(lp, road_mat=("rift_road", "snow_stone"), side_mat=("glacier_wall", "wall"), rail_mat=("rift_stone", "wall"),
           glow_mat=("edge_amber", "wall"), thickness=1.8, rail=1.0, min_speed=15.0, commit=20.0, boost=(1.4, 2.0), gravity=8.0)

    X0, X1, Y0, Y1 = -420, 420, -420, 420
    ter = c.terrain("Land", X0, X1, Y0, Y1, 6.0, natural, classify, near=9.0, fade=12.0, under=0.2)
    c.underfloor_flat("Abyss Floor", X0, X1, Y0, Y1, 6.0, lambda x, y: -38.0 if natural(x, y) < -20 else None, c.lib("rift_mist", "abyss"))

    # Piers under the bridges, the Monolith, the tunnel rock round the glacier tunnel.
    for piece in c.pieces:
        for kind, size, every in (("bridge", 2.2, 18.0), ("greatbridge", 2.6, 22.0), ("causeway", 2.0, 16.0), ("kicker", 2.2, 10.0)):
            if piece.name.endswith(kind):
                kit.clear_piers(c, piece, [ter], every=every, mat=("rift_stone", "wall"), size=size, inset=size + 1.0)
    mono = c.rock_mass("Monolith", MONOLITH[0], MONOLITH[1], 12.0, 12.0, 90.0, z0=-40.0, n=8, seed=3)
    c.assign(mono, c.lib("crystal_cyan", "wall"))
    q0, q1 = c.at(TO_ROAD(SEG[6] - 6)), c.at(TO_ROAD(SEG[7] + 4))
    rock = c.rock_mass("Glacier Face", (q0.p.x + q1.p.x) / 2, (q0.p.y + q1.p.y) / 2, 30.0, 34.0, 30.0, z0=0.0, n=20, seed=5)
    c.tunnel(rock, TO_ROAD(SEG[6] - 6), TO_ROAD(SEG[7] + 2), half=c.width / 2 + 2.5, height=10.0, pad=14.0)
    c.paint_rock(rock, ice_wall, ("rift_snow", "packed_snow"), floor=("rift_road", "road"), floor_z=q0.p.z + 1.5)

    c.start_line()
    S = lambda i: TO_ROAD(SEG[i])  # noqa: E731
    # Zippers: down the ice wall onto the ice bridge, the jump's run-up, the causeway
    # into the Loop (it needs speed), off the lake into the climb, onto the bridge.
    for at in (S(5) + 5, TO_ROAD(LIP - 36), S(11) + 8, S(18) + 5, S(24) + 20):
        c.zipper(at, 0)
    for at, across in ((S(3) + 20, 0), (S(8) + 30, 0), (S(16) + 30, 0), (S(22) + 20, 0), (S(26) + 20, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (S(1) + 20, -4, "red"),
        (S(1) + 20, 4, "blue"),
        (S(7) + 20, 0, "green"),
        (S(14) + 20, 0, "yellow"),
        (S(15) + 20, 0, "rainbow"),
        (S(25) + 20, -4, "red"),
        (S(25) + 20, 4, "blue"),
    ):
        c.balloon(at, across, col)
    c.entity("respawn", **{"from": round(lip - 20, 1), "to": round(land + 4, 1), "at": round(land + 18, 1)})
    c.checkpoints(
        extra=[S(2), S(5) + 30, S(7) + 30, S(8) + 40, S(10) + 20, S(14) + 10, S(16) + 40, S(19) + 20, S(22), S(24) + 60, S(26)],
        avoid=[(s_in - 6, s_out + 6), (lip - 14, land + 8)],
        height=10.0,
    )

    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish()
    print("lap", round(c.length, 1))


if __name__ == "__main__":
    main()
