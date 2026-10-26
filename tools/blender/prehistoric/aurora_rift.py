# Aurora Rift: Frostveil Peaks, course 4. Down into a fractured glacier, through a
# crystal cathedral and a loop-the-loop, across a mirror lake and back up under the
# northern lights. The second lap (Blake, Oct 24: about 20% shorter, nearly all corners,
# more going on in the cave and less after it), greyboxed for driving first and then
# dressed like the first one (aurora_scenery.py); the first lap is kept as
# aurora_rift_v2 (aurora_rift_v2.py, ?track=aurora_rift_v2).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/aurora_rift.py      (the bpy module)
#
# The same places in the same order, about 1.96 km:
#
#   1  The Shattered Entrance: the start on the snowfield, east along the Rift's rim, and
#      a tight S down the ice wall onto the natural ice bridge, north into the glacier.
#   2  The Crystal Cathedral: out of the tunnel onto the cliffside drift, a hairpin round
#      the Monolith, the broken bridge over the abyss (a jump), up onto the north wall
#      and the causeway into the Rift Loop.
#   3  Mirror Lake: down the crystal tunnel to the frozen lake, an S of drifts on the ice.
#   4  The Aurora Ascent and the Great Rift Bridge: a long ice tunnel west, the climbing
#      canyon south under its arches, out of the great opening and over the bridge.
#   5  The final descent: an S back down the snowfield and the last drift to the line.
#
# The land is the first lap's: the snowfield (south), the Rift, and the glacier (the
# massif, north) that the caverns are cut out of; only where its edges run is this
# lap's. The driving is the greybox's: the same roads, kinds, pickups and checkpoints.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import ruin_mode  # noqa: E402
from course_kit import lerp, smooth  # noqa: E402

# The ruin (aurora_ruins.py): the dragons brought the glacier's roof down. The caverns lie
# open to the sky, the ice bridge's tunnel is a cutting, Mirror Lake's cavern and the
# ascent are buried, and the Loop has lost half its top. The lap stays in the wrecked
# Cathedral: in at the old tunnel, round the Monolith, over the broken bridge, along the
# causeway and round the Loop (it still carries you across the missing top), then back
# over the fallen ice: down the Cathedral's broken east end and along the glacier's face,
# fallen into the Rift. Everything else (the land, the landmarks) is the course's own.
RUIN = ruin_mode.ON
TRACK_ID = "aurora_rift_ruin" if RUIN else "aurora_rift"

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
STANDARD_LAYOUT, STANDARD_PATH = LAYOUT, PATH
SEG = kit.segment_starts(PATH)
LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))
LOOP_SEG = 12
if RUIN:
    # Blake: about 45% shorter, the whole cavern decimated, the Loop's top half missing.
    # The course's own road from 20 m into the old tunnel to the Loop's exit (0-7: its
    # segments 6-13, exactly where they were), then the way back over the fallen ice
    # (8-13). The start is in the tunnel.
    _p6 = next(p for p in STANDARD_PATH if p[3] == 6)
    START_IN = 20.0
    START = (_p6[0], _p6[1] + START_IN)
    LAYOUT = [("S", STANDARD_LAYOUT[6][1] - START_IN)] + STANDARD_LAYOUT[7:14] + [
        ("R", 40, 180),  # 8  round through the Cathedral's broken east end...
        ("S", 248.69),  # 9  ...south down it over the fallen ice (closes the loop)
        ("R", 40, 90),  # 10 out over the Rift, west...
        ("S", 88.0),  # 11 ...along the glacier's face, fallen into it (closes the loop)
        ("R", 40, 90),  # 12 north, onto the ice bridge's end
        ("S", 15),  # 13 into the old tunnel to the line
    ]
    LAYOUT, PATH = kit.close_turtle(LAYOUT, 9, 11, START, 90.0)
    SEG = kit.segment_starts(PATH)
    LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))
    LOOP_SEG = 6


def seg_of(s):
    k = 0
    for i, d in SEG.items():
        if d <= s:
            k = max(k, i)
    return k


def _seg_point(i):
    return next(p for p in STANDARD_PATH if p[3] == i)


def _seg_points(i):
    return [p for p in STANDARD_PATH if p[3] == i]


def _arc_centre(i):
    """The centre of the standard lap's arc segment i (the landmarks stay put in the ruin)."""
    x, y, h, _ = _seg_point(i)
    sg = STANDARD_LAYOUT[i]
    a = math.radians(h + (90 if sg[0] == "L" else -90))
    return (x + sg[1] * math.cos(a), y + sg[1] * math.sin(a))


MONOLITH = _arc_centre(8)
LOOP_IN = STANDARD_PATH[[k for k, p in enumerate(STANDARD_PATH) if p[3] == 12][0] - 1]
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
if RUIN:
    # The course's own heights, segment for segment, to the Loop's exit; then gently up
    # over the fallen ice to the tunnel's height at the line.
    _std_h = HEIGHT
    Z_LINE = lerp(_std_h[6], _std_h[7], smooth(START_IN / STANDARD_LAYOUT[6][1]))
    HEIGHT = {0: Z_LINE, **{i - 6: _std_h[i] for i in range(7, 14)}, 8: Z_CATH, 9: Z_CATH + 0.5, 10: Z_CATH + 3.0,
              11: Z_CATH + 4.0, 12: Z_LINE - 1.5, 13: Z_LINE - 0.5}
    LIP = SEG[3] + 30.0
    LAND = LIP + 10.0


def _base_z(d, seg):
    a, b = SEG[seg], SEG.get(seg + 1, LENGTH)
    t = (d - a) / max(1e-6, b - a)
    z0, z1 = HEIGHT[seg], HEIGHT.get(seg + 1, HEIGHT[0])
    if RUIN:
        if seg in (5, 6, 7):
            return z0  # the causeway and the Loop, level
        return lerp(z0, z1, smooth(t))
    if seg == 24:
        # Dead level across the bridge, easing down off its far end.
        return lerp(Z_BRIDGE, z1, smooth(max(0.0, (d - (b - 30)) / 30.0)))
    if seg in (11, 12, 13) or seg in (16, 17):
        return z0
    return lerp(z0, z1, smooth(t))


road_z = kit.with_jumps(_base_z, seg_of, [(LIP, LAND, 2.5, 0.9)])


def road_w(d, seg):
    if RUIN:
        if seg in (5, 6, 7):
            return 14.0  # the causeway: as wide as the Loop
        return 15.0 if seg in (0, 3) else 17.0
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


def sm(t):
    return smooth(max(0.0, min(1.0, t)))


# The Rift's band as the greybox laid out its kinds (the ice bridge, the Great Rift
# Bridge): the dressed Rift's walls follow it.
RIFT_Y = (_seg_point(5)[1] + _seg_point(6)[1]) / 2  # (the standard lap's)
RIFT_HALF = 26.0
ABYSS = -150.0  # the floor of the Rift and the Cathedral, lost in mist
FACE = -92.0  # the glacier's south face (the Rift's north wall), on average


def face_y(x):
    """Where the glacier's south face is: the ice bridge goes into it at the tunnel, the
    Great Rift Bridge comes out of it."""
    return FACE + 3.0 * math.sin(x / 37.0) + 2.0 * math.sin(x / 13.0 + 1.0)


# The descent's line along the wall: road y for each metre of x (the S, segments 2-4).
_LEDGE = {}
for _p in STANDARD_PATH:
    if 2 <= _p[3] <= 4:
        _k = int(round(_p[0]))
        _LEDGE[_k] = min(_LEDGE.get(_k, 1e9), _p[1])


def rim_y(x):
    """The Rift's south rim, where the snowfield breaks off. Along the ice-wall descent it
    hugs the road, so the road is carved into the wall with the chasm beside it."""
    base = -145.0 + 4.0 * math.sin(x / 41.0) + 2.0 * math.sin(x / 11.0)
    ys = [_LEDGE[k] for k in range(int(x) - 2, int(x) + 3) if k in _LEDGE]
    if ys and 30.0 <= x <= 170.0:
        return min(base + 8.0, min(ys) - 10.5)
    return base


# The glacier (massif): from the Rift's north face to the north edge, west to east.
MASSIF = (-780.0, 340.0, FACE, 390.0)


def in_massif(x, y, pad=0.0):
    x0, x1, y0, y1 = MASSIF
    return x0 - pad <= x <= x1 + pad and face_y(x) - pad <= y <= y1 + pad


def glacier_top(x, y):
    """The glacier's surface: rising from its broken south face to a great dome over the
    caverns, ridged and crevassed."""
    rise = sm((y - FACE) / 140.0)
    dome = 50.0 * math.exp(-(((x - 40.0) / 300.0) ** 2) - ((y - 140.0) / 220.0) ** 2)
    ridges = 6.0 * math.sin(x / 47.0 + y / 61.0) + 4.0 * math.sin(x / 19.0 - y / 23.0)
    return 108.0 + 30.0 * rise + dome + ridges * (0.4 + 0.6 * rise)


def snowfield(x, y):
    """The snowfield south of the Rift: level round the start, rising east into an ice
    ridge over the descent's wall, a high shoulder in the west where the Great Rift
    Bridge lands, and mountains far off."""
    h = Z_START - 1.5 + 1.2 * math.sin(x / 31.0) * math.cos(y / 27.0)
    ridge = sm((x - 20.0) / 60.0) * sm((-120.0 - y) / 40.0 + 1.0) * sm((y + 330.0) / 60.0)
    h += 34.0 * ridge * sm((x - 10) / 120.0)
    h += 14.0 * sm((-100.0 - x) / 80.0) * sm((y + 330.0) / 100.0)
    far = max(0.0, x - 420.0) * 0.7 + max(0.0, -820.0 - x) * 0.7 + max(0.0, -430.0 - y) * 0.8
    h += min(260.0, far) + 30.0 * sm((far - 40.0) / 120.0) * (0.5 + 0.5 * math.sin(x / 53.0 + y / 41.0))
    return h


def natural(x, y):
    """The land, before it's shaped round the roads."""
    if in_massif(x, y):
        return ABYSS  # under the glacier (only seen through the Cathedral's abyss)
    fy, ry = face_y(x), rim_y(x)
    if y > fy:
        return glacier_top(x, y)  # north of the Rift beyond the glacier's ends
    if y > ry:
        return ABYSS + 6.0 * math.sin(x / 23.0) * math.cos(y / 17.0)  # the Rift
    return snowfield(x, y)


def classify(c, n, info):
    if c.z < ABYSS + 30:
        return ("abyss_glow", "abyss")
    if n.z < 0.55:
        if c.z > Z_START + 4 or c.y > FACE - 20:
            return ("glacier_wall" if (int(c.z / 14) + int(c.x / 50)) % 3 == 0 else "rift_cliff", "wall")
        return ("rift_cliff" if (int(c.z / 9) + int(c.x / 40)) % 3 else "rift_rock", "wall")
    if info["d"] < 10.5:
        return ("rift_road", "snow_stone")
    # Off the road, packed snow (as the greybox drove).
    return ("rift_snow", "packed_snow")


# ---------------------------------------------------------------- the dressing's spots


def _cross(c, s0, test, limit=400.0):
    """The first road distance from s0 where test(point) holds."""
    s = s0
    while s < s0 + limit and not test(c.at(s).p):
        s += 1.0
    return s


def scenery_spots(c, s_in, s_out):
    """Where aurora_scenery.py puts things on this lap (road distances)."""
    R = lambda i: TO_ROAD(SEG[i])  # noqa: E731
    lip, land = TO_ROAD(LIP), TO_ROAD(LAND)
    # Where the Great Rift Bridge leaves the glacier's face and reaches the far rim.
    sf = _cross(c, R(24), lambda p: p.y < face_y(p.x))
    sr = _cross(c, sf, lambda p: p.y < rim_y(p.x))
    return {
        "entrance_cut": (R(6) - 2, R(7) + 10),
        "cath_segs": (7, 13),
        "cath_extra": [(40.0, -10.0), (50.0, 110.0), (160.0, 170.0)],
        "crystal_tunnel": (R(13) + 5, R(15) + 10),
        "lake_segs": (15, 17),
        "ice_tunnel": (R(17) + 30, R(19) + 10),  # from inside the lake cavern (no wall across the road)
        "canyon_cut": (R(19) + 4, R(23) + 20),
        "opening_cut": (R(23) + 14, sf + 22),
        "face_fractures": (60.0, 215.0),
        "snow_lamps": [(20.0, R(2), 26.0), (R(25) + 10, c.length - 30, 30.0)],
        "ledge": (R(2), int((R(5) - R(2)) / 10)),
        "ice_bridge": (R(5) - 2, R(5) + 10, R(7)),
        "tunnel_end": R(7) + 4,
        # The hairpin goes round the Monolith on a ledge: its pillar stays under the road
        # (scenery only: the inside of the hairpin is the abyss, as the greybox drove).
        "island_r": 44.0,
        "island_drop": 6.0,
        "island_role": "visual",
        "mono_r": 12.0,
        "mono_foot": 14.0,
        # The broken bridge: arches either side of the gap it jumps.
        "cath_bridges": [(R(9) - 4, lip - 1), (land + 1, R(10) + 4)],
        "north_span": None,
        "cath_ledges": [(R(7) + 8, R(8)), (R(10), R(11))],
        "curtain": None,
        "causeway": R(11) - 2,
        "far_causeway": R(14),
        "deco_spans": [(95.0, 40.0, 9.0, "High Bridge"), (205.0, -34.0, 7.0, "Low Bridge")],
        "ascent_crystals": (R(18) + 24, R(19) + 6),
        "canyon_arches": (R(20) + 14, R(21) + 30, R(22) + 50),
        "canyon_lamps": (R(19) + 10, sf + 20),
        "canyon_falls": R(20) + 6,
        "opening_at": sf - 8,
        "great_bridge": (sf - 6, sr + 6),
        # No new hazards on the road (the greybox's driving): no falling ice there, no
        # cracking ice on the lake's line.
        "road_icicles": [],
        "lake_crack": None,
    }


def pickups(c, s_in, s_out):
    """The greybox's pickups, boosts, respawn zone and checkpoints (aurora_scenery.py
    calls this instead of the first lap's)."""
    lip, land = TO_ROAD(LIP), TO_ROAD(LAND)
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


# ---------------------------------------------------------------- the course


def main():
    c = kit.Course(TRACK_ID, "Aurora Rift (Ruined)" if RUIN else "Aurora Rift", "aurora_ruins" if RUIN else "aurora_rift")
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
    if RUIN:
        # The new road over the fallen ice: slabs of the glacier lying across the abyss.
        c.kinds["icefall"] = {"mat": "rift_road", "shoulder": 1.0, "shoulder_mat": ("glacier_wall", "snow_stone"), "barrier": 1.0,
                              "barrier_mat": ice_wall, "deck": 10.0, "deck_mat": ice_wall, "ground": False}
    s_in = kit.s_near(c, ex, ey)
    s_out = kit.s_near(c, xx, xy)
    lip, land = TO_ROAD(LIP), TO_ROAD(LAND)

    def ruin_label(smp):
        s = smp.s
        if s_in <= s <= s_out or lip <= s <= land:
            return "gap"
        if lip - 12 <= s < lip:
            return "kicker"
        seg = seg_of(TO_PLAN(s))
        if seg in (0, 13):
            return "tunnel"
        if seg in (1, 2, 4):
            return "cathedral"
        if seg == 3:
            return "bridge"
        if seg in (5, 6, 7):
            return "causeway"
        if seg == 12:
            return "icebridge" if abs(smp.p.y - RIFT_Y) < RIFT_HALF + 4 else "tunnel"
        return "icefall"

    def label(smp):
        if RUIN:
            return ruin_label(smp)
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
    # (The ruin's Loop has lost the top of its far side; the game still carries you over.)
    c.loop(lp, road_mat=("rift_road", "snow_stone"), side_mat=("glacier_wall", "wall"), rail_mat=("rift_stone", "wall"),
           glow_mat=("edge_amber", "wall"), thickness=1.8, rail=1.0, min_speed=15.0, commit=20.0, boost=(1.4, 2.0), gravity=8.0,
           gaps=[(0.42, 0.68)] if RUIN else ())
    if RUIN:
        ruin_mode.DRESS(c, sys.modules[__name__], lp, s_in, s_out)
        c.finish()
        print("lap", round(c.length, 1))
        return

    import aurora_scenery  # noqa: E402

    aurora_scenery.build(c, sys.modules[__name__], lp, s_in, s_out)
    c.finish()
    print("lap", round(c.length, 1))


def ruin_pickups(c, s_in, s_out):
    """The ruin's zippers, items, respawn zone and checkpoints."""
    lip, land = TO_ROAD(LIP), TO_ROAD(LAND)
    S = lambda i: TO_ROAD(SEG[i])  # noqa: E731
    # Zippers: the jump's run-up, the causeway into the Loop (it needs speed), down the
    # fallen east end, along the fallen face.
    for at in (TO_ROAD(LIP - 36), S(5) + 8, S(9) + 60, S(11) + 10):
        c.zipper(at, 0)
    for at, across in ((S(2) + 30, 0), (S(9) + 140, 0), (S(11) + 50, 2)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (S(1) + 20, 0, "green"),
        (S(4) + 20, -3, "red"),
        (S(4) + 20, 3, "blue"),
        (S(8) + 50, 0, "rainbow"),
        (S(9) + 200, 0, "yellow"),
        (S(12) + 20, 0, "red"),
    ):
        c.balloon(at, across, col)
    c.entity("respawn", **{"from": round(lip - 20, 1), "to": round(land + 4, 1), "at": round(land + 18, 1)})
    c.checkpoints(
        extra=[S(1) + 20, S(2) + 40, S(4) + 20, S(8) + 40, S(9) + 80, S(9) + 200, S(11) + 40, S(12) + 30],
        avoid=[(s_in - 6, s_out + 6), (lip - 14, land + 8)],
        height=10.0,
    )


if __name__ == "__main__":
    main()
