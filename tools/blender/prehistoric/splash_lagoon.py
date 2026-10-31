# Splash Lagoon: the beach world's fourth course, painted (the Tropic Isles). The
# greybox's lap exactly (it's kept as splash_lagoon_v2): the same roads, heights,
# surfaces, loop, plank, zippers and checkpoints; only the look is new
# (lagoon_scenery.py, tropic_textures.py): a seaside water park on a summer afternoon.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/splash_lagoon.py      (the bpy module)
#
# Blake (Oct 25): "start a 4th beach level greybox". Each beach course stands on its own
# pieces (Coral Cove: the boardwalk jump; Shipwreck Bay: the pier, the galleon, the mast;
# Volcano Isle: the geysers, the lava tube, the cliff jump), so this one is a seaside
# water park, none of those. About 830 m, a lap near 33 s:
#
#   1  The start along the beach, east, a boost pad, and the Big Curl: a loop-the-loop
#      round the inside of a breaking wave.
#   2  North up the long wooden ramp to the top of the slide tower, round its deck.
#   3  The Big Slide: the flume, down and west through four banked S-bends, high walls
#      either side, into the splashdown.
#   4  South round the lazy river's bend, or straight across its plank (narrow, no rails:
#      a short cut if you keep your nerve), and east onto the line.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import ruin_mode  # noqa: E402
from course_kit import lerp, smooth  # noqa: E402

import lagoon_scenery  # noqa: E402

# The ruin (splash_lagoon_ruins.py): Tidewyrm's raid toppled the slide tower down the
# length of its climbing ramp; the lap now climbs its wreck to the flume (the same line,
# the same heights). Pool tiles and park junk lie in the road. Everything else is the
# course's own.
RUIN = ruin_mode.ON
TRACK_ID = "splash_lagoon_ruin" if RUIN else "splash_lagoon"

LOOP_R, LOOP_RAMP, LOOP_SHIFT = 20.0, 24.0, 16.0
START = (0.0, 0.0)
LAYOUT = [
    ("S", 40),  # 0  1: the start along the beach, east
    ("S", 70),  # 1  the boost pad, into the curl
    ("LOOP", LOOP_R, LOOP_RAMP, LOOP_SHIFT),  # 2 the Big Curl
    ("S", 40),  # 3  out of it
    ("L", 30, 90),  # 4  north
    ("S", 52),  # 5  2: towards the slide tower...
    ("S", 78),  # 6  ...up its ramp
    ("L", 22, 90),  # 7  round the tower's deck, west
    ("S", 10),  # 8  the flume's mouth
    ("L", 30, 50),  # 9  3: the Big Slide, down through its S-bends
    ("R", 30, 100),  # 10
    ("L", 30, 100),  # 11
    ("R", 30, 50),  # 12
    ("S", 30),  # 13 the splashdown (closes the lap)
    ("L", 24, 90),  # 14 4: south
    ("S", 4),  # 15
    ("R", 24, 60),  # 16 round the lazy river's bend...
    ("L", 24, 120),  # 17
    ("R", 24, 60),  # 18 ...
    ("S", 20),  # 19 (closes the lap)
    ("L", 26, 90),  # 20 east onto the line
    ("S", 24),  # 21
]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 13, 19, START, 0.0)
SEG = kit.segment_starts(PATH)
LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))
LOOP_SEG = 2


def seg_of(s):
    k = 0
    for i, d in SEG.items():
        if d <= s:
            k = max(k, i)
    return k


def _seg_point(i):
    return next(p for p in PATH if p[3] == i)


def _arc_centre(i):
    x, y, h, _ = _seg_point(i)
    sg = LAYOUT[i]
    a = math.radians(h + (90 if sg[0] == "L" else -90))
    return (x + sg[1] * math.cos(a), y + sg[1] * math.sin(a))


def _plan_point(d):
    t = 0.0
    for a, b in zip(PATH, PATH[1:]):
        t += math.hypot(b[0] - a[0], b[1] - a[1])
        if t >= d:
            return b
    return PATH[-1]


# ---------------------------------------------------------------- heights

WATER_Z = 0.0
BASE = 2.0
TOP = 14.0  # the slide tower's deck
CLIMB = (SEG[5] + 10.0, SEG[7])
SLIDE = (SEG[9], SEG[13] + 18.0)
SPLASH_Z = 2.6


def _ease(u):
    u = min(1.0, max(0.0, u))
    return 0.5 * u + 0.5 * smooth(u)


def road_z(d, seg):
    if seg == LOOP_SEG:
        return BASE
    if d < CLIMB[0]:
        return BASE
    if d < CLIMB[1]:
        return lerp(BASE, TOP, _ease((d - CLIMB[0]) / (CLIMB[1] - CLIMB[0])))
    if d < SLIDE[0]:
        return TOP
    if d < SLIDE[1]:
        return lerp(TOP, SPLASH_Z, _ease((d - SLIDE[0]) / (SLIDE[1] - SLIDE[0])))
    return lerp(SPLASH_Z, BASE, smooth((d - SLIDE[1]) / max(1e-6, LENGTH - 40.0 - SLIDE[1])))


def road_w(d, seg):
    if SEG[1] + 10 <= d <= SEG[3] + 30:
        return 14.0  # the loop's way in and out (the loop is 14 m wide)
    if d < 30:
        return 18.0
    if 7 <= seg <= 12:
        return 13.0  # the tower deck and the flume
    return 16.0


ROUTE, SHARP, LOOPS = kit.route_with_loops(PATH, LAYOUT, road_z, every=6.0, width=road_w)
TO_ROAD, TO_PLAN = kit.along(PATH, road_z)
LOOP_IN = PATH[[k for k, p in enumerate(PATH) if p[3] == LOOP_SEG][0] - 1]

# ---------------------------------------------------------------- the land

TOWER = _arc_centre(7)
# The lazy river: a pond inside the bend, and the plank straight across it (the cut).
_c17 = _arc_centre(17)
_a, _b = _plan_point(SEG[16] + 2.0), _plan_point(SEG[19] - 2.0)
CUT = [(_a[0], _a[1]), (_b[0], _b[1])]
_chord = ((_a[0] + _b[0]) / 2, (_a[1] + _b[1]) / 2)
POND_C = ((_c17[0] + _chord[0]) / 2, (_c17[1] + _chord[1]) / 2)
# The splashdown pool beside the flume's end, on its outside (north).
_sp = _plan_point(SEG[13] + 24.0)
SPLASH_POOL = (_sp[0], _sp[1] + 20.0, 10.0)

_PTS = None


def _road_pts():
    global _PTS
    if _PTS is None:
        _PTS = []
        d = 0.0
        for i, p in enumerate(PATH):
            if i:
                d += math.hypot(p[0] - PATH[i - 1][0], p[1] - PATH[i - 1][1])
            if i % 2 == 0 and p[3] != LOOP_SEG:
                _PTS.append((p[0], p[1], road_z(d, p[3])))
    return _PTS


def near_road_z(x, y):
    best = None
    bd = 1e18
    for px, py, pz in _road_pts():
        dd = (px - x) ** 2 + (py - y) ** 2
        if dd < bd:
            bd, best = dd, pz
    # The ground stays low under the decks (the ramp, the tower, the flume stand on posts).
    return min(best, 3.0), math.sqrt(bd)


def _pond_r():
    d = min(math.hypot(px - POND_C[0], py - POND_C[1]) for px, py, _ in _road_pts())
    return d - 8.0 - 4.0


POND_R = _pond_r()


def sea_d(x, y):
    """How far out to sea (negative: on land): south of the beach, and (the paint) round
    the rest of the headland's rounded shore, so the land never ends in a straight cut."""
    south = (-42.0 + 2.5 * math.sin(x / 23.0)) - y
    cx, cy, ax, ay = 65.0, 100.0, 215.0, 165.0
    u, v = abs(x - cx) / ax, abs(y - cy) / ay
    shore = ((u**4 + v**4) ** 0.25 - 1.0) * min(ax, ay) + 4.0 * math.sin(x / 19.0 + y / 27.0)
    return max(south, shore)


def natural(x, y):
    """Sand at about the road's level, dunes away from it, sloping into the sea south; the
    lazy river's pond and the splash pool sunk into it."""
    z, d = near_road_z(x, y)
    h = z - 0.5 + 0.4 * math.sin(x / 17.0) * math.cos(y / 13.0) * smooth((d - 12) / 20)
    h += 2.5 * smooth((d - 25) / 40)
    s = sea_d(x, y)
    if s > -14:
        h = lerp(h, WATER_Z - 2.0 - 0.04 * max(0.0, s), smooth((s + 14) / 14))
    w = math.hypot(x - POND_C[0], y - POND_C[1]) - POND_R
    if w < 5:
        h = lerp(h, WATER_Z - 2.0, smooth((5 - w) / 5))
    px, py, pr = SPLASH_POOL
    w = math.hypot(x - px, y - py) - pr
    if w < 4:
        h = lerp(h, WATER_Z - 1.5, smooth((4 - w) / 4))
    return h


def classify(c, n, info):
    if n.z < 0.6:
        return ("valley_cliff", "wall")
    if c.z < WATER_Z - 0.4:
        return ("wet_sand", "deep_water")
    if c.z < WATER_Z + 0.6:
        return ("wet_sand", "sand")
    # Soft ground off the road (cutting across mustn't pay); the shoulders stay sand.
    # (The paint: lawns inland, sand by the sea; the same surface.)
    if sea_d(c.x, c.y) < -40 and info["d"] > info["sample"].w / 2 + 6:
        return ("splash_grass", "soft_sand")
    return ("beach_sand", "soft_sand")


# The paint: each greybox material -> Splash Lagoon's own (Course.lib keeps the old surface).
PAINT = {
    "beach_road": "splash_path",
    "beach_sand": "splash_sand",
    "wet_sand": "splash_wet_sand",
    "sea_water": "splash_sea",
    "lagoon_shallow": "splash_pool",
    "wood_planks": "splash_deck",
    "valley_cliff": "splash_rock",
}


def box(c, name, cx, cy, hx, hy, z0, z1, mat, role="both"):
    from course_kit import bmesh

    bm = bmesh.new()
    vs = [bm.verts.new((cx + sx * hx, cy + sy * hy, z)) for z in (z0, z1) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([vs[i] for i in f])
    ob = c.mesh_object(name, bm, "Props", role)
    c.assign(ob, c.lib(*mat))
    return ob


def main():
    kit.MAT_REMAP.clear()
    kit.MAT_REMAP.update(PAINT)
    c = kit.Course(TRACK_ID, "Splash Lagoon (Ruined)" if RUIN else "Splash Lagoon", "splash_ruins" if RUIN else "splash_lagoon")
    (ex, ey, _), (xx, xy, _) = LOOPS[0]
    banks = [(_arc_centre(i)[0], _arc_centre(i)[1], 44.0, 18.0) for i in (9, 10, 11, 12)]
    # The lazy river's bend stays level, so the plank leaves and rejoins it flush.
    flat = [(ex, ey, 40), (xx, xy, 40), (_c17[0], _c17[1], 58)]
    c.route(ROUTE, width=16.0, bank=6.0, sharp=SHARP, flat=flat, banks=banks)
    sand = ("beach_sand", "sand")
    planks = ("wood_planks", "road")
    tiki = ("tiki_wood", "wall")
    c.kinds = {
        "road": {"mat": "beach_road", "shoulder": 1.6, "shoulder_mat": sand},
        "straight": {"mat": "beach_road", "shoulder": 1.6, "shoulder_mat": sand, "exact": True},
        "ramp": {"mat": "wood_planks", "surface": "road", "shoulder": 0.4, "shoulder_mat": planks, "barrier": 1.0,
                 "barrier_mat": tiki, "deck": 2.0, "deck_mat": planks, "ground": False},
        # (The ruin) the toppled tower's side, the way up: its panels, no rails.
        "wreck": {"mat": "splash_slide_yellow", "surface": "road", "shoulder": 0.6, "shoulder_mat": ("splash_slide_red", "road"), "deck": 3.0,
                  "deck_mat": ("splash_slide_red", "road"), "ground": False},
        "flume": {"mat": "party_teal", "surface": "road", "shoulder": 0.4, "shoulder_mat": ("party_white", "road"),
                  "barrier": 2.2, "barrier_mat": ("party_white", "wall"), "deck": 1.6, "deck_mat": ("party_teal", "road"),
                  "ground": False},
    }
    s_in, s_out = kit.s_near(c, ex, ey), kit.s_near(c, xx, xy)
    r0 = TO_ROAD(CLIMB[0]) + 6.0
    t0 = TO_ROAD(SEG[7])
    f1 = TO_ROAD(SLIDE[1]) - 4.0

    def label(smp):
        s = smp.s
        if s_in <= s <= s_out:
            return "gap"
        if s_in - 60 <= s < s_in or s_out < s <= s_out + 45:
            return "straight"
        if r0 <= s < t0:
            return "wreck" if RUIN else "ramp"
        if t0 <= s < f1:
            return "flume"
        return "road"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k != "road":
            specials.append((s0, s1, k))
    snap = lambda v: s_in if abs(v - s_in) < 3 else s_out if abs(v - s_out) < 3 else v  # noqa: E731
    specials = [(snap(a), snap(b)) + tuple(rest) for a, b, *rest in specials]
    c.roads(kit.plan(c, specials, "road", max_len=150.0))

    # The Big Curl: the loop round the inside of a breaking wave.
    lp = kit.LoopPath(ex, ey, BASE, LOOP_IN[2], LOOP_R, LOOP_RAMP, LOOP_SHIFT, 14.0)
    c.loop(lp, road_mat=("sea_water", "road"), side_mat=("surf_foam", "wall"), rail_mat=("party_white", "wall"),
           glow_mat=("party_teal", "wall"), thickness=1.6, rail=1.0, min_speed=14.0, commit=18.0, boost=(1.45, 2.2),
           gravity=8.0, name="Big Curl")

    # The lazy river's plank: straight across the pond, narrow, no rails.
    za, zb = c.at(kit.s_near(c, *CUT[0])).p.z, c.at(kit.s_near(c, *CUT[1])).p.z
    n = 8
    cut = [(lerp(CUT[0][0], CUT[1][0], k / n), lerp(CUT[0][1], CUT[1][1], k / n), lerp(za, zb, k / n) - 0.05) for k in range(n + 1)]
    c.side_road("Lazy River Plank", cut, "wood_planks", "road", width=6.0, shoulder=0.3, shoulder_mat=planks,
                deck=1.2, deck_mat=planks, ground=False)

    X0, X1, Y0, Y1 = -200, 330, -200, 300
    ter = c.terrain("Sand", X0, X1, Y0, Y1, 4.0, natural, classify, near=9.0, fade=10.0, under=0.2, verge_fill=1.5, fine=3)
    c.underfloor_flat("Seabed", X0, X1, Y0, Y1, 4.0, lambda x, y: natural(x, y) - 0.6, c.lib("wet_sand", "deep_water"))
    c.ribbon("Sea South", [(x, -1340.0) for x in range(-1600, 1801, 200)], 2600.0, WATER_Z, c.lib("sea_water"), role="visual", steps=2)
    # (The paint: the sea all round the headland.)
    c.ribbon("Sea North", [(x, 1500.0) for x in range(-1600, 1801, 200)], 2600.0, WATER_Z, c.lib("sea_water"), role="visual", steps=2)
    c.ribbon("Sea West", [(-1200.0, y) for y in range(-60, 261, 80)], 2200.0, WATER_Z, c.lib("sea_water"), role="visual", steps=2)
    c.ribbon("Sea East", [(1380.0, y) for y in range(-60, 261, 80)], 2200.0, WATER_Z, c.lib("sea_water"), role="visual", steps=2)
    c.disc("Lazy River", POND_C[0], POND_C[1], POND_R + 3.0, WATER_Z, c.lib("lagoon_shallow", "deep_water"), role="visual", n=32)
    px, py, pr = SPLASH_POOL
    c.disc("Splash Pool", px, py, pr + 2.0, WATER_Z, c.lib("lagoon_shallow", "deep_water"), role="visual", n=24)

    # Posts under the ramp, the tower deck and the flume; the tower itself inside its turn.
    for piece in c.pieces:
        for kind, size, every in (("ramp", 0.9, 8.0), ("flume", 0.8, 7.0), ("wreck", 1.6, 9.0)):
            if piece.name.endswith(kind):
                kit.clear_piers(c, piece, [ter], every=every, mat=("party_white", "wall"), size=size, inset=size + 0.6)
    tx, ty = TOWER
    if not RUIN:  # (the ruin's has toppled: splash_lagoon_ruins.py)
        box(c, "Slide Tower", tx, ty, 9.0, 9.0, 0.0, TOP + 9.0, ("party_yellow", "wall"))
        box(c, "Slide Tower Canopy", tx, ty, 12.0, 12.0, TOP + 9.0, TOP + 10.0, ("party_red", "wall"), role="visual")

    c.start_line()
    S = lambda i: TO_ROAD(SEG[i])  # noqa: E731
    # Zippers: into the curl, up the ramp, down the flume's mouth.
    for at in (s_in - 45, S(5) + 18, S(9) + 2):
        c.zipper(at, 0)
    for at, across in ((s_out + 30, 0), (S(6) + 30, 0), (S(13) + 10, 0), (S(20) + 12, 3)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in ((S(0) + 24, -4, "red"), (S(0) + 24, 4, "blue"), (S(4) + 20, 0, "green"), (S(8) + 4, 0, "yellow"),
                            (S(17) + 20, 0, "rainbow"), (S(21) + 8, 0, "red")):
        c.balloon(at, across, col)

    # Checkpoints: one at the bend's apex with a twin across the plank (either counts),
    # none elsewhere along the stretch the plank skips.
    a_in, a_out = kit.s_near(c, *CUT[0]), kit.s_near(c, *CUT[1])
    apex = TO_ROAD(SEG[17]) + (TO_ROAD(SEG[18]) - TO_ROAD(SEG[17])) / 2
    gates = c.checkpoints(
        extra=[S(4) + 10, S(5) + 30, S(7) + 10, S(10) + 10, S(12) + 10, S(14) + 10, apex, S(20) + 10],
        avoid=[(s_in - 10, s_out + 10), (a_in - 4, apex - 8), (apex + 8, a_out + 4)],
        height=10.0,
    )
    main_gate = min(gates.items(), key=lambda kv: abs(kv[0] - apex))[1]
    mid = ((CUT[0][0] + CUT[1][0]) / 2, (CUT[0][1] + CUT[1][1]) / 2)
    zm = (za + zb) / 2
    c.alt_gate(main_gate, "lazy_river_plank",
               [(lerp(CUT[0][0], mid[0], 0.5), lerp(CUT[0][1], mid[1], 0.5), zm), (mid[0], mid[1], zm),
                (lerp(mid[0], CUT[1][0], 0.5), lerp(mid[1], CUT[1][1], 0.5), zm)], width=10.0)

    sc = lagoon_scenery.build(c, sys.modules[__name__], ter)
    if RUIN:
        ruin_mode.DRESS(c, sys.modules[__name__], sc)
    c.finish()
    print("lap", round(c.length, 1), "pond r", round(POND_R, 1))


if __name__ == "__main__":
    main()
