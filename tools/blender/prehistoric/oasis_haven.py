# Oasis Haven: Desert World, course 2. A sun-drenched resort round a great turquoise lake.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/oasis_haven.py      (the bpy module)
#
# A lap of about 2.1 km (around 90 s) on a perfect summer afternoon, all round one great
# lake in a desert basin. A spring high in the palace gardens feeds everything: it spills
# down the terraces in great cascades into the lake, runs through the market's canals,
# and plays in the fountains. Beyond the gardens the green gives way to sand, dunes and
# golden cliffs.
#
#   1  The Grand Resort Entrance: the start, on a raised plaza at the south shore, under
#      a great sandstone gateway, the lake and the palace across it ahead; down to the
#      waterfront.
#   2  The Great Lagoon Promenade: sweeping curves along the south and east shore, the
#      lake on the left all the way, the pavilion and the falls across the water.
#   3  The Waterfront Market: a tighter run between market halls and stalls, over the
#      canals that run in from the lake.
#   4  The Grand Arched Bridge: west across the lake on great stone arches, rising and
#      falling, to...
#   5  The Central Pavilion: round the blue-domed pavilion on its island, its fountains
#      and falls beside you; north over the causeway.
#   6  The Waterfall Terraces: up the terraced gardens, through a waterfall curtain,
#      round a broad turn beside the great cascades.
#   7  The Palace Heights: past the palace gateway along its gardens, the lake far below.
#   8  The Lakeside Return: down the west shore (or straight through the canal passage
#      under the hotel: the shortcut), round the beach headland, and back to the gate.
#
# Saves tracks-src/oasis_haven.blend and exports public/tracks/oasis_haven/. The scenery
# is oasis_scenery.py, built from the kit in oasis_props.py.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp, smooth  # noqa: E402

TRACK_ID = "oasis_haven"

# ---------------------------------------------------------------- the layout

START = (-80.0, -215.0)
LAYOUT = [
    ("S", 55),  # 0  1: the start plaza, east
    ("L", 150, 40),  # 1  2: down onto the promenade
    ("S", 75),  # 2
    ("L", 120, 40),  # 3  up the east shore
    ("R", 55, 50),  # 4  3: into the market
    ("L", 55, 60),  # 5
    ("S", 30),  # 6
    ("L", 60, 90),  # 7  round onto the bridge, heading west
    ("S", 90),  # 8  4: the Grand Arched Bridge (stretched to close the lap)
    ("L", 45, 50),  # 9  5: onto the island
    ("R", 50, 140),  # 10 round the pavilion
    ("S", 110),  # 11 the causeway north
    ("R", 50, 90),  # 12 6: up onto the first terrace, east
    ("S", 50),  # 13 through the waterfall curtain
    ("L", 45, 180),  # 14 the terrace turn, beside the great cascades
    ("S", 100),  # 15 7: up to the palace, west
    ("S", 60),  # 16 the palace gateway
    ("L", 80, 90),  # 17 8: south, down the west shore
    ("S", 250),  # 18 (stretched to close the lap)
    ("L", 60, 50),  # 19 out round the beach headland (the shortcut goes straight on)
    ("R", 60, 100),  # 20
    ("L", 60, 50),  # 21
    ("L", 80, 90),  # 22 east onto the south shore
    ("S", 30),  # 23 up to the gate
]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 8, 18, START, 0.0)
SEG = kit.segment_starts(PATH)
LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))
_D = [0.0]
for _a, _b in zip(PATH, PATH[1:]):
    _D.append(_D[-1] + math.hypot(_b[0] - _a[0], _b[1] - _a[1]))


def _seg_point(i):
    return next(p for p in PATH if p[3] == i)


def _seg_points(i):
    return [p for p in PATH if p[3] == i]


def _arc_centre(i):
    x, y, h, _ = _seg_point(i)
    sg = LAYOUT[i]
    a = math.radians(h + (90 if sg[0] == "L" else -90))
    return (x + sg[1] * math.cos(a), y + sg[1] * math.sin(a))


def path_at(s):
    """(x, y, heading degrees) of the layout s metres along the lap."""
    k = min(range(len(PATH)), key=lambda i: abs(_D[i] - s))
    return PATH[k][:3]


PAVILION = _arc_centre(10)  # the domed pavilion on its island
ISLAND_R = 74.0
HAIRPIN = _arc_centre(14)

# ---------------------------------------------------------------- heights

Z_LAKE = 0.0  # the lake's surface
Z_SHORE = 3.0  # the promenade and the market
Z_ISLAND = 4.0
Z_T1, Z_T2, Z_PALACE = 14.0, 30.0, 42.0  # the terraces, and the palace plateau
Z_GATE = 9.0  # the start plaza
S = SEG
ANCHORS = [
    (0.0, Z_GATE),
    (S[0] + 30, Z_GATE),
    (S[1] + 75, Z_SHORE),  # down to the waterfront
    (S[7] + 30, Z_SHORE + 0.5),
    (S[8] + 30, 10.0),  # over the bridge's crown
    (S[9] + 10, Z_ISLAND),
    (S[11] + 70, Z_ISLAND + 1.0),  # the causeway
    (S[12] + 60, Z_T1),  # up onto the first terrace
    (S[14], Z_T1 + 1.0),
    (S[15], Z_T2 + 1.0),  # round the terrace turn
    (S[16], 35.0),
    (S[17], 36.0),  # the palace heights
    (S[18] + 30, 33.0),
    (S[19], 6.0),  # down the west shore
    (S[19] + 20, Z_SHORE),
    (S[22], Z_SHORE),
    (LENGTH - 25, Z_GATE),
    (LENGTH, Z_GATE),
]


def _lin(d):
    d = min(max(d, 0.0), LENGTH)
    for (d0, z0), (d1, z1) in zip(ANCHORS, ANCHORS[1:]):
        if d0 <= d <= d1:
            return lerp(z0, z1, (d - d0) / max(1e-6, d1 - d0))
    return Z_GATE


def road_z(d, seg=None):
    """The road's height d metres along the lap: the anchors, eased over 30 m."""
    return sum(_lin(d + k) for k in range(-15, 16, 3)) / 11


def road_w(d, seg):
    if seg in (0, 23):
        return 20.0  # the start plaza: room for the pack
    if seg in (4, 5, 6):
        return 16.0  # the market street
    if seg in (8,):
        return 16.0  # the bridge
    if seg in (11,):
        return 15.0  # the causeway
    return 18.0


ROUTE = kit.route_points_by(PATH, road_z, every=8.0, width=road_w)


def seg_of(s):
    k = 0
    for i, d in SEG.items():
        if d <= s:
            k = max(k, i)
    return k


# ---------------------------------------------------------------- the land


def sm(t):
    return smooth(max(0.0, min(1.0, t)))


class Near:
    """Distance from points to a set of points (a polyline sampled densely), fast."""

    def __init__(self, pts, cell=24.0):
        self.cell = cell
        self.pts = pts
        self.grid = {}
        for k, p in enumerate(pts):
            self.grid.setdefault((int(p[0] // cell), int(p[1] // cell)), []).append(k)

    def find(self, x, y, reach=3):
        gx, gy = int(x // self.cell), int(y // self.cell)
        best = (float("inf"), -1)
        for i in range(gx - reach, gx + reach + 1):
            for j in range(gy - reach, gy + reach + 1):
                for k in self.grid.get((i, j), ()):
                    p = self.pts[k]
                    d = (p[0] - x) ** 2 + (p[1] - y) ** 2
                    if d < best[0]:
                        best = (d, k)
        return (math.sqrt(best[0]), best[1]) if best[1] >= 0 else best


ROAD_NEAR = Near(PATH)


def road_near(x, y):
    """(distance to the lap's centre line, distance along it, segment)."""
    d, k = ROAD_NEAR.find(x, y)
    if k < 0:
        return d, 0.0, -1
    return d, _D[k], PATH[k][3]


def _smooth_loop(pts, n=6):
    """A closed polyline rounded by Chaikin's corner cutting, then sampled every ~2 m."""
    for _ in range(n):
        out = []
        for a, b in zip(pts, pts[1:] + pts[:1]):
            out.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            out.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        pts = out
    dense = []
    for a, b in zip(pts, pts[1:] + pts[:1]):
        k = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 2.0))
        for j in range(k):
            dense.append((a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k))
    return dense


def _shore_from_route(segs, gap, step=10.0):
    """Points `gap` metres to the left of the route over the given segments."""
    out = []
    last = -1e9
    for p, d in zip(PATH, _D):
        if p[3] in segs and d - last >= step:
            a = math.radians(p[2])
            out.append((p[0] - math.sin(a) * gap, p[1] + math.cos(a) * gap))
            last = d
    return out


def _lake_outline():
    """The lake's shore, anticlockwise: just inside the promenade (south and east), off
    the market's waterfront, round the north-east beaches, along the foot of the
    terraces, down the west shore under the descent, round the headland."""
    pts = []
    pts += _shore_from_route((0, 1, 2, 3), 13.0)  # the promenade's sea wall
    pts += _shore_from_route((4, 5, 6), 30.0)  # off the market's waterfront terraces
    pts += [(200.0, 120.0), (215.0, 170.0), (205.0, 225.0), (170.0, 255.0), (110.0, 258.0)]  # the north-east beaches
    pts += [(60.0, 250.0), (0.0, 252.0), (-40.0, 238.0), (-90.0, 246.0), (-140.0, 256.0)]  # the foot of the terraces
    # The west shore: the descent runs along the cliffs above it (the road's left).
    pts += [p for p in _shore_from_route((18,), 24.0) if p[1] < 240.0]
    pts += _shore_from_route((19, 20, 21), 14.0)  # round the headland (a sea wall)
    pts += _shore_from_route((22,), 16.0)
    return _smooth_loop(pts, 3)


LAKE = _lake_outline()
LAKE_NEAR = Near(LAKE, 20.0)


def _inside(poly, x, y):
    c = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            c = not c
        j = i
    return c


_LAKE_BOX = (min(p[0] for p in LAKE), max(p[0] for p in LAKE), min(p[1] for p in LAKE), max(p[1] for p in LAKE))


def lake_d(x, y):
    """Signed distance to the lake's shore: positive in the water (and in the canals),
    negative on land. The island is land."""
    x0, x1, y0, y1 = _LAKE_BOX
    if x0 - 60 <= x <= x1 + 60 and y0 - 60 <= y <= y1 + 60:
        d, _ = LAKE_NEAR.find(x, y, 4)
        d = min(d, 120.0)
        s = d if _inside(LAKE, x, y) else -d
    else:
        s = -120.0
    # The island.
    di = math.hypot(x - PAVILION[0], y - PAVILION[1]) - ISLAND_R
    s = min(s, di)
    # The canals: water too.
    s = max(s, canal_d(x, y))
    return s


# The canals: from the lake east into the market (under the road), and the passage
# through the headland beside the shortcut. Each a polyline and a half-width.
def _canals():
    out = []
    for frac in (0.25, 0.75):
        s = SEG[4] + (SEG[7] - SEG[4]) * frac
        x, y, h = path_at(s)
        a = math.radians(h)
        rx, ry = math.sin(a), -math.cos(a)  # the road's right (inland)
        out.append(([(x - rx * 34, y - ry * 34), (x + rx * 40, y + ry * 40), (x + rx * 80, y + ry * 70 + 10)], 5.5))
    return out


CANALS = _canals()


def _seg_d(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy + 1e-9)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy), t


def canal_d(x, y):
    best = -1e9
    for pts, hw in CANALS + PASSAGE_CANAL:
        for a, b in zip(pts, pts[1:]):
            d, _ = _seg_d(x, y, a[0], a[1], b[0], b[1])
            best = max(best, hw - d)
    return best


def lake_bed(x, y, d):
    """The lake's bed d metres from the shore: a bright sandy shelf, then deep blue."""
    if d < 0:
        return None
    return -0.6 - 7.0 * sm((d - 4.0) / 40.0)


# The terraces: the north shore rises in steps to the palace plateau.
TERRACE_Y = (262.0, 340.0, 400.0)


def terraces(x, y):
    z = Z_SHORE + 1.0
    for edge, top in zip(TERRACE_Y, (Z_T1, Z_T2, Z_PALACE)):
        z = lerp(z, top, sm((y - edge) / 7.0))
    return z


def desert(x, y, d):
    """Beyond the gardens: the land rises from the oasis floor into dunes, then the
    golden cliffs of the basin's rim."""
    r = math.hypot(x / 1.15, y + 20.0)
    dunes = 3.0 * math.sin(x / 37.0 + y / 53.0) + 2.0 * math.sin(x / 19.0 - y / 29.0)
    h = Z_SHORE + 1.0 + (6.0 + dunes) * sm((-d - 90.0) / 120.0)
    ang = math.atan2(y + 20.0, x / 1.15)
    rim = 470.0 + 30.0 * math.sin(ang * 3 + 1.0) + 15.0 * math.sin(ang * 7) + 150.0 * max(0.0, math.sin(ang)) ** 2
    if r > rim:
        h = max(h, h + steps((r - rim), 70.0))
    return h


def steps(u, top):
    """Golden sandstone cliffs in steps: sheer bands with ledges, up to `top`."""
    out = 0.0
    for w, f in ((5.0, 0.45), (14.0, 0.1), (5.0, 0.35), (16.0, 0.1)):
        out += top * f * sm(u / w)
        u -= w
        if u <= 0:
            break
    return out


def west_ridge(x, y):
    """The ridge the descent runs down: high at the palace, falling south to the
    headland."""
    k = sm((y - 20.0) / 300.0)
    return lerp(Z_SHORE + 2.0, Z_PALACE - 2.0, k) + 3.0 * sm((-x - 220.0) / 60.0)


def natural(x, y):
    """The land before it's shaped round the roads."""
    d = lake_d(x, y)
    if d > 0:
        return lake_bed(x, y, d)
    h = desert(x, y, d)
    # The oasis floor round the shore: low and level (gardens, promenades, the market).
    h = lerp(Z_SHORE + 0.4, h, sm((-d - 40.0) / 80.0))
    if y > 230 and x > -230 and x < 260:
        h = max(h, terraces(x, y) * sm((260.0 - abs(x - 15.0)) / 30.0) + h * (1 - sm((260.0 - abs(x - 15.0)) / 30.0)))
    if x < -160 and y > -60:
        h = max(h, west_ridge(x, y) * sm((-x - 160.0) / 20.0))
    # A low sea wall: the shore drops to the water in a short bank.
    if -6.0 < d <= 0:
        h = lerp(h, 0.6, sm((d + 6.0) / 6.0))
    if h > 0 and d > -1:
        h = min(h, 0.6)
    if x < -160 and y > -60:
        h = max(h, west_ridge(x, y) * sm((-x - 175.0) / 8.0)) if d < -4 else h
    return h


# ---------------------------------------------------------------- the shortcut

def _passage():
    """The canal passage: straight on where the main road swings out round the
    headland, under the beach hotel beside a canal, back onto the road before the last
    corner."""
    a = _seg_points(19)
    b = _seg_points(22)
    q0 = a[4]
    q1 = b[3]
    pts = []
    for k in range(9):
        t = k / 8
        pts.append((q0[0] + (q1[0] - q0[0]) * t + 4.0 * math.sin(math.pi * t), q0[1] + (q1[1] - q0[1]) * t))
    return pts


SHORT = _passage()


def _passage_canal():
    """The canal beside the shortcut, inside the headland: it leaves the lake north of
    the headland (under the main road), runs along the passage and back out to the lake
    in the south (under the road again)."""
    off = 11.0
    mid = [(p[0] + off, p[1]) for p in SHORT[1:-1]]
    n0 = path_at(SEG[19] + 18.0)
    n1 = path_at(SEG[21] + 34.0)
    return [([(n0[0] + 30.0, n0[1] + 6.0), mid[0]] + mid + [(n1[0] + 30.0, n1[1] - 6.0)], 4.0)]


PASSAGE_CANAL = _passage_canal()


# ---------------------------------------------------------------- materials


def classify(c, n, info):
    d = lake_d(c.x, c.y)
    if d > 0.5 and c.z < 0.2:
        return ("lake_sand", "water")  # the bed (under the water's surface)
    if n.z < 0.55:
        if c.z > 30 or (c.y > 230 and c.z > 6):
            return ("oasis_stone", "wall")  # terrace walls
        return ("gold_cliff", "wall")
    if n.z < 0.8:
        if garden_k(c.x, c.y, d) > 0.4:
            return ("hedge", "grass")  # planted banks in the gardens and terraces
        return ("gold_sand", "loose_sand")
    if info["d"] < info["sample"].w / 2 + 1.5:
        return ("oasis_paving", "road")
    garden = garden_k(c.x, c.y, d)
    if garden > 0.5:
        return ("oasis_lawn", "grass")
    if garden > 0.15:
        return ("garden_soil", "dirt")
    return ("gold_sand", "loose_sand")


def garden_k(x, y, d=None):
    """How lush the ground is: green near the water and in the terraces, fading to sand
    beyond (the oasis stands out against the desert)."""
    d = lake_d(x, y) if d is None else d
    k = 1.0 - sm((-d - 55.0) / 45.0)
    if y > 240 and abs(x - 15.0) < 260:
        k = max(k, 1.0 - sm((y - 470.0) / 30.0))
    k *= 1.0 - 0.35 * (0.5 + 0.5 * math.sin(x / 13.0) * math.cos(y / 17.0)) * sm((-d - 25.0) / 30.0)
    return k


# ---------------------------------------------------------------- the course


def main():
    c = kit.Course(TRACK_ID, "Oasis Haven", "oasis_haven")
    c.route(ROUTE, width=18.0, bank=6.0)
    tiles = ("tile_border", "road")
    rail = ("balustrade", "wall")
    stone = ("oasis_stone", "wall")
    c.kinds = {
        # Cream paving with a blue-tiled border, stone balustrades.
        "plaza": {"mat": "oasis_paving", "shoulder": 1.6, "shoulder_mat": tiles, "barrier": 1.1, "barrier_mat": rail},
        "promenade": {"mat": "oasis_paving", "shoulder": 1.4, "shoulder_mat": tiles, "barrier": 1.0, "barrier_mat": rail,
                      "deck": 3.0, "deck_mat": stone},
        "market": {"mat": "oasis_paving", "shoulder": 1.4, "shoulder_mat": tiles, "barrier": 0.9, "barrier_mat": ("market_rail", "wall")},
        "bridge": {"mat": "oasis_paving", "shoulder": 1.0, "shoulder_mat": tiles, "barrier": 1.2, "barrier_mat": rail,
                   "deck": 2.6, "deck_mat": stone, "ground": False},
        "island": {"mat": "oasis_paving", "shoulder": 1.4, "shoulder_mat": tiles, "barrier": 1.0, "barrier_mat": rail},
        "causeway": {"mat": "oasis_paving", "shoulder": 1.0, "shoulder_mat": tiles, "barrier": 1.1, "barrier_mat": rail,
                     "deck": 6.0, "deck_mat": stone, "ground": False},
        "terrace": {"mat": "oasis_paving", "shoulder": 1.4, "shoulder_mat": tiles, "barrier": 1.1, "barrier_mat": rail},
        "palace": {"mat": "palace_paving", "shoulder": 1.6, "shoulder_mat": tiles, "barrier": 1.2, "barrier_mat": rail},
        "descent": {"mat": "oasis_paving", "shoulder": 1.4, "shoulder_mat": tiles, "barrier": 1.1, "barrier_mat": rail,
                    "deck": 5.0, "deck_mat": stone},
        "canalbridge": {"mat": "oasis_paving", "shoulder": 1.0, "shoulder_mat": tiles, "barrier": 1.0, "barrier_mat": rail,
                        "deck": 2.0, "deck_mat": stone, "ground": False},
        "open": {"mat": "oasis_paving", "shoulder": 2.0, "shoulder_mat": tiles},
    }
    sa = kit.s_near(c, *SHORT[0])
    sb = kit.s_near(c, *SHORT[-1])

    def label(smp):
        s = smp.s
        seg = seg_of(s)
        x, y = smp.p.x, smp.p.y
        wet = lake_d(x, y) > -4.0
        if seg in (7, 8, 9) and wet:
            return "bridge"
        if seg == 11 and wet:
            return "causeway"
        if abs(s - sa) < 16 or abs(s - sb) < 16:
            return "open"
        if wet and seg not in (9, 10):
            return "canalbridge"
        if seg in (0, 23) or (seg == 1 and s < SEG[1] + 30):
            return "plaza"
        if seg in (1, 2, 3, 19, 20, 21, 22):
            return "promenade"
        if seg in (4, 5, 6, 7):
            return "market"
        if seg in (9, 10, 11):
            return "island"
        if seg in (12, 13, 14):
            return "terrace"
        if seg in (15, 16, 17):
            return "palace"
        return "descent"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k != "plaza":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "plaza", max_len=200.0))

    z = [c.nearest(x, y)[0].p.z for x, y in SHORT]
    c.shortcut("Canal Passage", [(x, y, zz) for (x, y), zz in zip(SHORT, z)], "oasis_paving", "road", width=9.0, shoulder=0.8,
               shoulder_mat=tiles)

    import oasis_scenery  # noqa: E402

    oasis_scenery.build(c, sys.modules[__name__])
    c.finish()


if __name__ == "__main__":
    main()
