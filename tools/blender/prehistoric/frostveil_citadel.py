# Frostveil Citadel: Frostveil Peaks, course 1. A lost mountain civilization in the snow.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/frostveil_citadel.py      (the bpy module)
#
# A clockwise journey (about 2.0 km) round one moonlit mountain valley:
#
#   A  The Forgotten Entrance: the start, on the valley floor beside a fog-filled chasm,
#      through a great gate between two carved dinosaur heads, heading north, under
#      the Bridge of Giants. The temple glows high on the west mountain ahead.
#   B  The Frozen Causeway: a hairpin and a switchback up the east hillside, 0 -> 31 m.
#   C  The Bridge of Giants: 165 m of arched stone heading west at 32 m, over the start
#      straight and then a 130 m-deep chasm full of fog, straight at...
#   D  The Serpent Gate: the open mouth of a giant serpent carved into the west cliff.
#      A torchlit tunnel climbs inside the mountain, 32 -> 53 m, with an icy patch.
#   E  The Moonlit Temple: out into a great courtyard before the stepped temple; a broad
#      sweep round the ceremonial sun disk, with an icy inner line across the flagstones.
#   F  The High Labyrinth: walled lanes and arches, then an elevated causeway east over
#      the north gorge, looking down on the start valley.
#   G  The Frozen Waterfall Descent: down the east mountainside, 58 -> 10 m, past frozen
#      waterfalls, with a jump over a frozen gorge.
#   H  The Lower Ruins: west through the old lower town and round onto the start.
#
# Every corner is a 28-60 m arc. Saves tracks-src/frostveil_citadel.blend and exports
# public/tracks/frostveil_citadel/. The scenery is frostveil_scenery.py, built from the
# winter-ruin kit in winter_props.py.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp, smooth  # noqa: E402

TRACK_ID = "frostveil_citadel"
PLATEAU_Z = 54.0

# ---------------------------------------------------------------- the layout

START = (0.0, -214.0)
LAYOUT = [
    ("S", 244),  # 0  A: the start straight, north up the valley
    ("R", 34, 90),  # 1  B: climbing already, a hairpin round the head of the valley...
    ("S", 2),  # 2
    ("R", 30, 90),  # 3  ...back south
    ("S", 64.19),  # 4
    ("L", 30, 50),  # 5  the switchback...
    ("R", 30, 140),  # 6  ...round the cliff: the bridge appears
    ("S", 163.71),  # 7  C: the Bridge of Giants (it ends where it always did: the mouth)
    ("S", 30),  # 8  D: into the serpent's mouth
    ("R", 40, 90),  # 9  the tunnel turns north, climbing
    ("S", 50),  # 10
    ("L", 32, 45),  # 11 a technical S...
    ("R", 32, 45),  # 12
    ("S", 40),  # 13 out into the moonlight
    ("R", 60, 90),  # 14 E: the courtyard sweep round the sun disk
    ("S", 30),  # 15 F: the labyrinth
    ("L", 34, 45),  # 16
    ("R", 34, 90),  # 17
    ("L", 34, 45),  # 18
    ("S", 190),  # 19 the high causeway over the north gorge
    ("R", 50, 90),  # 20 G: over the brink, the descent begins
    ("S", 60),  # 21
    ("L", 45, 50),  # 22
    ("R", 45, 100),  # 23
    ("L", 45, 50),  # 24
    ("S", 60),  # 25 the run-up to the jump
    ("S", 16),  # 26 the gap, over the frozen gorge
    ("S", 36),  # 27 the landing
    ("R", 40, 90),  # 28 H: straight into the lower ruins
    ("S", 150),  # 29 (stretched to close the loop)
    ("R", 40, 90),  # 30 round onto the start straight
    ("S", 18),  # 31 (stretched to close the loop)
]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 29, 31, START, 90.0)
SEG = kit.segment_starts(PATH)
LIP = SEG[26]
LAND = SEG[27]
LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))

# Heights along the lap (metres along it, height); the road eases between them.
ANCHORS = [
    (0.0, 0.0),
    (SEG[1] + 10, 0.4),
    (SEG[7], 31.5),
    (SEG[8], 32.5),
    (SEG[14], 54.0),
    (SEG[15], 55.0),
    (SEG[19], 58.0),
    (SEG[20], 58.0),
    (SEG[25], 23.0),
    (LIP, 21.5),
    (LAND, 14.5),  # (7 m under the lip: a kart at top speed always clears the gap)
    (SEG[28], 11.5),
    (SEG[30], 1.5),
    (LENGTH, 0.0),
]


def _lin(d):
    d = min(max(d, 0.0), LENGTH)
    for (d0, z0), (d1, z1) in zip(ANCHORS, ANCHORS[1:]):
        if d0 <= d <= d1:
            return lerp(z0, z1, (d - d0) / max(1e-6, d1 - d0))
    return 0.0


def road_z(d, seg):
    # The run-up, the gap and the landing are straight slopes; everywhere else the
    # height is smoothed over 30 m, so grades change gently.
    if LIP - 14 <= d <= LAND + 14:
        return _lin(d)
    return sum(_lin(d + k) for k in range(-15, 16, 3)) / 11


def road_w(d, seg):
    if seg == 27:
        return 24.0  # a wide landing
    if seg == 25 and d > LIP - 34:
        return 18.0
    if seg == 7:
        return 17.0  # the bridge
    if seg in (13, 14):
        return 18.0  # the courtyard
    if 15 <= seg <= 18:
        return 13.5  # the labyrinth's lanes
    if seg in (9, 10, 11, 12):
        return 14.0  # the tunnel
    return 15.0


ROUTE = kit.route_points_by(PATH, road_z, every=12.0, width=road_w)

# ---------------------------------------------------------------- the land


def _nearest(px, py, pts):
    """Distance to a polyline, the index of the nearest segment, and the nearest point."""
    best = (1e9, 0, (0.0, 0.0))
    for i, ((ax, ay), (bx, by)) in enumerate(zip(pts, pts[1:])):
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        qx, qy = ax + t * dx, ay + t * dy
        d = math.hypot(px - qx, py - qy)
        if d < best[0]:
            best = (d, i, (qx, qy))
    return best


# The great chasm (west of the start valley, 130 m deep, full of fog) bending east into
# the north gorge, which the high causeway crosses. CHASM_TO is where the chasm becomes
# the gorge (a waterfall drops from one to the other).
CHANNEL = [(-65, -290), (-66, -180), (-64, -100), (-60, -20), (-50, 50), (-25, 110), (20, 140), (90, 144), (160, 142), (222, 142)]
CHASM_TO = 4
CHASM_FLOOR = -100.0


def channel(x, y):
    """(distance from the channel's centre, its half-width, its bed height)."""
    d, i, (qx, qy) = _nearest(x, y, CHANNEL)
    if i < CHASM_TO:
        return d, 32.0 + 3 * math.sin(qy / 23), CHASM_FLOOR
    t = (qx + 25) / 245
    return d, 27.0 + 3 * math.sin(qx / 19), lerp(-32.0, 4.0, max(0.0, min(1.0, t)))


# The frozen gorge the descent jumps, running west into a frozen pond beside the start.
GORGE = [(345, -172), (282, -184), (232, -188), (170, -187), (112, -190)]
POND = (82.0, -190.0, 26.0)

# The descent's shelf on the east mountainside: the road's height there, by y.
SHELF = [(150, 58), (78, 54.5), (18, 48), (-16, 44), (-85, 31), (-120, 23), (-180, 21.5), (-196, 16), (-246, 10), (-300, 4)]


def shelf_z(y):
    for (y0, z0), (y1, z1) in zip(SHELF, SHELF[1:]):
        if y1 <= y <= y0:
            return lerp(z0, z1, (y0 - y) / (y0 - y1))
    return SHELF[0][1] if y > SHELF[0][0] else SHELF[-1][1]


def sm(t):
    return smooth(max(0.0, min(1.0, t)))


def massif(x, y):
    """How much of the west massif (the plateau at PLATEAU_Z) is here, 0..1."""
    return max(sm((-98 - x) / 7), sm((-28 - x) / 7) * sm((y - 112) / 8))


def terrace(v, step=16.0):
    """Mountainsides in ledges: mostly flat shelves (where snow lies) between short steep
    cliff bands, instead of one smooth slope."""
    if v <= 0:
        return v
    k = math.floor(v / step)
    f = v / step - k
    return (k + sm((f - 0.55) / 0.45)) * step


def land(x, y):
    """The mountains without the chasm and gorges."""
    h = 0.6 * math.sin(x / 23) * math.cos(y / 19) + 0.4 * math.sin((x + y) / 31)
    # The east hillside the causeway climbs, fading out in the south (the lower town).
    east = min(36.0, 0.36 * max(0.0, x - 8)) * sm((y + 222) / 40)
    # The descent's shelf, and the mountains rising steeply behind it.
    shelf = sm((x - 188) / 10) * shelf_z(y)
    h += max(east, shelf)
    # The mountains all round, their feet wandering (no straight walls), rising in
    # snowy ledges to jagged summits.
    east = 2.4 * max(0.0, x - (300 + 22 * math.sin(y / 43) + 10 * math.sin(y / 13)))
    rise = terrace(min(240.0, east), 18.0)
    # The west massif: the temple plateau, rising to peaks in the far west.
    m = massif(x, y)
    h += rise
    h = lerp(h, PLATEAU_Z + 1.2 * math.sin(x / 13) * math.cos(y / 17), m)
    west = 2.2 * max(0.0, -x - (300 + 25 * math.sin(y / 39) + 10 * math.sin(y / 15)))
    h += terrace(min(260.0, west), 20.0)
    # The north mountains (further back behind the temple), and the southern hills.
    north = 190 + 60 * sm((-x - 100) / 40) + 28 * math.sin(x / 53) + 12 * math.sin(x / 17 + 1)
    n_rise = 1.5 * max(0.0, y - north)
    h += terrace(min(280.0, n_rise), 16.0)
    s_rise = 0.9 * max(0.0, -y - (340 + 20 * math.sin(x / 31)))
    h += terrace(min(140.0, s_rise), 14.0)
    # Jagged summits on the high ground.
    hi = max(east, west, n_rise, s_rise)
    h += 45 * (0.5 + 0.5 * math.sin(x / 37 + 0.7) * math.cos(y / 29)) * sm((hi - 60) / 80)
    return h


def natural(x, y):
    h = land(x, y)
    d, hw, bed = channel(x, y)
    if d < hw + 12:
        h = lerp(h, bed, sm((hw + 12 - d) / 12))
    d, i, (qx, qy) = _nearest(x, y, GORGE)
    if d < 9 + 6:
        gbed = lerp(46.0, -4.0, sm((345 - qx) / 113)) if qx > 232 else -4.0
        h = lerp(h, min(h, gbed), sm((15 - d) / 6))
    px, py, pr = POND
    dp = math.hypot(x - px, y - py)
    if dp < pr + 6:
        h = lerp(h, -2.0, sm((pr + 6 - dp) / 6))
    return h


# The rock the Serpent Gate's tunnel runs through: the east face of the west massif.
TUNNEL = ((-160.0, -45.0), 62.0, 82.0)


def in_tunnel_rock(x, y, shrink=1.0):
    (cx, cy), rx, ry = TUNNEL
    return ((x - cx) / (rx * shrink)) ** 2 + ((y - cy) / (ry * shrink)) ** 2 < 1


TUNNEL_S = [0.0, 0.0]


def classify(c, n, info):
    if in_tunnel_rock(c.x, c.y, 0.8):
        return None
    smp = info["sample"]
    if TUNNEL_S[0] <= smp.s <= TUNNEL_S[1] and info["d"] < 18 and c.z > smp.p.z - 1.0:
        return None
    # The chasm's and gorges' floors are bottomless: touching them puts you back.
    if c.z < -12 or (c.z < 0 and _nearest(c.x, c.y, GORGE)[0] < 10):
        return ("frost_rock", "abyss")
    if n.z < 0.62:
        return ("frost_cliff" if (int(c.z / 7) + int(c.x / 40)) % 2 else "frost_rock", "wall")
    px, py, pr = POND
    if math.hypot(c.x - px, c.y - py) < pr and c.z < 0:
        return ("frost_pool", "ice")
    if info["d"] < 11:
        return ("packed_snow_road", "packed_snow")
    return ("snow_ground", "deep_snow")


def in_abyss(x, y, margin=0.0):
    """Over the chasm, the north gorge or the frozen gorge (and their walls)."""
    d, hw, bed = channel(x, y)
    return d < hw + 13 + margin or _nearest(x, y, GORGE)[0] < 16 + margin


def underfloor_z(x, y):
    # (Overlapping the abyss floor by a few metres, so there's no crack between them.)
    if in_tunnel_rock(x, y, 0.8) or in_abyss(x, y, -5.0):
        return None
    return min(land(x, y), natural(x, y)) - 0.35


def abyss_z(x, y):
    """The invisible floor of the drops: just under their beds. Touch it and you're put
    back on the road."""
    if not in_abyss(x, y, 5.0) or in_tunnel_rock(x, y, 0.8):
        return None
    return min(natural(x, y), channel(x, y)[2]) - 1.5


# ---------------------------------------------------------------- the course


def seg_of(s):
    k = 0
    for i, d in SEG.items():
        if d <= s:
            k = max(k, i)
    return k


def main():
    c = kit.Course(TRACK_ID, "Frostveil Citadel", "frost_citadel")
    c.route(ROUTE, width=15.0, bank=6.0)
    carved = ("citadel_carved", "wall")
    stone = ("citadel_stone", "wall")
    c.kinds = {
        "road": {"mat": "snow_stone_road", "shoulder": 1.8, "shoulder_mat": ("packed_snow_road", "packed_snow"), "barrier": 0.9, "barrier_mat": stone},
        "lower": {"mat": "packed_snow_road", "shoulder": 1.6, "shoulder_mat": ("snow_ground", "packed_snow")},
        "climb": {"mat": "snow_stone_road", "shoulder": 1.2, "shoulder_mat": ("packed_snow_road", "packed_snow"), "barrier": 1.1, "barrier_mat": stone},
        "bridge": {
            "mat": "snow_stone_road",
            "shoulder": 0.8,
            "shoulder_mat": ("citadel_stone", "snow_stone"),
            "barrier": 1.4,
            "barrier_mat": carved,
            "deck": 4.0,
            "deck_mat": stone,
            "ground": False,
        },
        "cave": {"mat": "snow_stone_road", "shoulder": 3.4, "shoulder_mat": ("citadel_dark", "snow_stone")},
        "cave_ice": {"mat": "icy_stone_road", "shoulder": 3.4, "shoulder_mat": ("citadel_dark", "snow_stone")},
        "court": {"mat": "snow_stone_road", "shoulder": 2.5, "shoulder_mat": ("citadel_stone", "snow_stone")},
        "maze": {"mat": "snow_stone_road", "shoulder": 1.0, "shoulder_mat": ("citadel_dark", "snow_stone"), "barrier": 1.6, "barrier_mat": stone},
        "causeway": {
            "mat": "snow_stone_road",
            "shoulder": 0.8,
            "shoulder_mat": ("citadel_stone", "snow_stone"),
            "barrier": 1.4,
            "barrier_mat": carved,
            "deck": 3.0,
            "deck_mat": stone,
            "ground": False,
        },
        "descent": {"mat": "snow_stone_road", "shoulder": 1.2, "shoulder_mat": ("packed_snow_road", "packed_snow"), "barrier": 1.0, "barrier_mat": stone},
        "icebridge": {
            "mat": "icy_stone_road",
            "shoulder": 0.6,
            "shoulder_mat": ("citadel_stone", "icy_stone"),
            "barrier": 1.2,
            "barrier_mat": carved,
            "deck": 2.4,
            "deck_mat": stone,
            "ground": False,
        },
        "ramp": {
            "mat": "snow_stone_road",
            "shoulder": 0.6,
            "shoulder_mat": ("citadel_stone", "snow_stone"),
            "barrier": 1.2,
            "barrier_mat": carved,
            "deck": 6.0,
            "deck_mat": stone,
            "ground": False,
        },
        "landing": {"mat": "snow_stone_road", "shoulder": 1.0, "shoulder_mat": ("citadel_stone", "snow_stone"), "barrier": 1.4, "barrier_mat": stone},
    }

    def label(smp):
        x, y, s = smp.p.x, smp.p.y, smp.s
        seg = seg_of(s)
        if LIP <= s <= LAND:
            return "gap"
        if seg == 25 and s >= LIP - 34:
            return "ramp"
        if seg == 27:
            return "landing"
        if in_tunnel_rock(x, y, 0.98):
            # One icy patch, on the S-bend.
            return "cave_ice" if SEG[11] + 6 <= s <= SEG[11] + 30 else "cave"
        above = smp.p.z - natural(x, y)
        if seg in (7, 8) and above > 3.0:
            return "bridge"
        if 19 <= seg <= 20 and above > 3.0:
            return "causeway"
        if 21 <= seg <= 24 and above > 4.0:
            return "icebridge"
        if seg in (13, 14):
            return "court"
        if 15 <= seg <= 18:
            return "maze"
        if 2 <= seg <= 6:
            return "climb"
        if 20 <= seg <= 25:
            return "descent"
        if 28 <= seg <= 30:
            return "lower"
        return "road"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "ramp":
            specials.append((s0, s1, "ramp", {"lift": lambda u, n: 1.0 * max(0.0, (u - (n - 10)) / 10) ** 2}))
        elif k != "road":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "road"))

    inside = kit.crossings(c, lambda smp: in_tunnel_rock(smp.p.x, smp.p.y, 1.0), margin=0)
    t0, t1 = max(inside, key=lambda r: r[1] - r[0])
    TUNNEL_S[:] = [t0 - 16, t1 + 16]
    X0, X1, Y0, Y1 = -420, 420, -420, 400
    c.terrain("Mountains", X0, X1, Y0, Y1, 5.0, natural, classify, near=9.0, fade=20.0)
    # The hidden floors only where a kart could ever be: within 80 m of the road.

    def near(fn):
        return lambda x, y: fn(x, y) if c.nearest(x, y)[1] < 80 else None

    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 4.0, near(underfloor_z), c.lib("snow_ground", "deep_snow"))
    c.underfloor_flat("Abyss Floor", X0, X1, Y0, Y1, 4.0, near(abyss_z), c.lib("frost_rock", "abyss"))

    # The tunnel rock: the massif's east face, cut through along the route.
    (cx, cy), rx, ry = TUNNEL
    rock = c.rock_mass("Serpent Rock", cx, cy, rx, ry, 108.0, z0=-104.0, n=36, seed=7,
                       bands=[(1.0, 0.0), (1.0, 0.45), (0.97, 0.5), (0.95, 0.72), (0.9, 0.76), (0.82, 1.0)])
    c.tunnel(rock, t0, t1, half=c.width / 2 + 3.4, height=11.5, pad=14.0)
    c.paint_rock(rock, ("frost_cliff", "wall"), ("snow_ground", "deep_snow"), floor=("citadel_dark", "snow_stone"), top_z=60, floor_z=56)
    floor = []
    s = t0 - 22
    while s <= t1 + 22:
        q = c.at(s)
        floor.append((q.p.x, q.p.y, 2 * (c.width / 2 + 3.4) + 14, q.p.z - 0.25))
        s += 2.0
    c.ribbon("Tunnel Floor", floor, 26, 0, c.lib("citadel_dark", "snow_stone"), coll="Collision", role="collision", steps=4)

    c.start_line()
    L = c.length
    # Zippers: off the start, on the bridge, on the courtyard's exit, and
    # half-way down the descent (as the S-bends open out).
    c.zipper(40, 0)
    c.zipper(SEG[7] + 30, 0)
    c.zipper(SEG[15] + 4, 0)
    c.zipper(SEG[23] + 40, 0)
    for at, across in ((90, -3), (SEG[4] + 10, 0), (SEG[7] + 125, 2), (SEG[10] + 15, 0), (SEG[19] + 90, 0), (SEG[21] + 20, -2), (SEG[29] + 30, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (150, -4, "red"),
        (150, 4, "blue"),
        (SEG[7] + 80, 0, "green"),
        (SEG[14] + 50, -4, "yellow"),
        (SEG[14] + 50, 4, "red"),
        (SEG[19] + 150, 0, "rainbow"),
        (SEG[24] + 10, 0, "blue"),
        (SEG[29] + 70, 3, "green"),
    ):
        c.balloon(at, across, col)

    # Missing the jump drops you into the frozen gorge: you're put down on the landing.
    c.entity("respawn", **{"from": round(LIP - 40, 1), "to": round(LAND + 8, 1), "at": round(LAND + 30, 1)})

    c.checkpoints(
        extra=[SEG[4], SEG[7] + 40, SEG[7] + 150, SEG[10], SEG[13] + 10, SEG[16], SEG[19] + 100, SEG[22], LAND + 52, SEG[29]],
        height=10.0,
    )

    import frostveil_scenery  # noqa: E402

    frostveil_scenery.build(c, rock, t0, t1, sys.modules[__name__])

    ter = list(c.coll("Terrain").objects)
    c.preset("sun", ter + [rock], 0.3)
    c.preset("bottoms", ter, 0.55)
    kit.paint.shade_roads(c.pieces, 0.6)
    c.finish()


if __name__ == "__main__":
    main()
