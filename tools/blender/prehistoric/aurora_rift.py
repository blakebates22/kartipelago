# Aurora Rift: Frostveil Peaks, course 4. Down into a fractured glacier, through a
# crystal cathedral and a loop-the-loop, across a mirror lake and back up under the
# northern lights.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/aurora_rift.py      (the bpy module)
#
# A lap of about 2.45 km (around 90 s) in five connected regions, all one place: a great
# glacier (the "massif", north) split from the snowfield (south) by the Rift, a chasm
# running east-west whose floor is lost in glowing mist far below.
#
#   1  The Shattered Entrance: the start on the snowfield beneath the aurora, east along
#      the Rift's rim, a downhill run of banked turns carved into the ice wall over the
#      chasm, north across a natural ice bridge, under a colossal ice arch and into a
#      narrow tunnel that glows bluer and more crystalline the deeper it goes.
#   2  The Crystal Cathedral: the tunnel bursts out into an immense cavern inside the
#      glacier: an abyss in the middle, the Central Monolith (a crystal 290 m tall)
#      rising from it, ledges and bridges at several heights, waterfalls, crystal
#      forests, and the Rift Loop far across, framed by a hole in the ceiling open to
#      the aurora. The road sweeps round the east wall (the cliffside drift), crosses
#      the abyss on a suspended bridge, drifts round the Monolith (or cuts through its
#      glowing crystal arch), bridges to the north wall, runs behind the giant waterfall
#      curtain and out onto the causeway into the Loop.
#   3  Mirror Lake: down a crystal tunnel to an underground frozen lake that mirrors the
#      crystals and the ice columns rising from it; sweeping drifts across the ice, a
#      thin-ice shortcut, and cracked patches that give way if you keep driving on them.
#   4  The Aurora Ascent: up out of the lake through an ice tunnel, a fractured canyon
#      under natural arches and a gallery looking down into the Cathedral, and out of a
#      great opening in the glacier's face under the sky...
#   5  ...onto the Great Rift Bridge over the open chasm, then the final descent: fast,
#      broad curves back across the snowfield, the Rift and the glacier off to the left,
#      and a last drift onto the finish straight.
#
# Saves tracks-src/aurora_rift.blend and exports public/tracks/aurora_rift/. The scenery
# is aurora_scenery.py, built from the kit in aurora_props.py.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp, smooth  # noqa: E402

TRACK_ID = "aurora_rift"

# ---------------------------------------------------------------- the layout

# The Rift Loop: radius of its circular part, easing length at each end, sideways shift.
LOOP_R, LOOP_RAMP, LOOP_SHIFT = 24.0, 28.0, 18.0
START = (0.0, -270.0)
LAYOUT = [
    ("S", 40),  # 0  the start, north across the snowfield
    ("R", 45, 90),  # 1  east along the Rift's rim
    ("S", 30),  # 2  down the ice wall over the chasm...
    ("L", 45, 45),  # 3  ...banked turns carved into it...
    ("R", 45, 45),  # 4
    ("L", 40, 90),  # 5  ...and north
    ("S", 70),  # 6  the natural ice bridge across the Rift, under the great ice arch
    ("S", 65),  # 7  the tunnel into the glacier
    ("S", 25),  # 8  the reveal: out into the Crystal Cathedral
    ("L", 120, 50),  # 9  the cliffside drift round the east wall
    ("S", 25),  # 10
    ("L", 40, 90),  # 11 onto the suspended bridge
    ("S", 70),  # 12 the bridge over the abyss
    ("R", 50, 120),  # 13 the Monolith curve (the crystal arch shortcut cuts inside)
    ("S", 60),  # 14 the ice bridge to the north wall
    ("L", 40, 90),  # 15 into the waterfall gallery
    ("S", 65),  # 16 behind the waterfall curtain
    ("S", 55),  # 17 the causeway: the loop approach, the boost strip
    ("LOOP", LOOP_R, LOOP_RAMP, LOOP_SHIFT),  # 18 the Rift Loop
    ("S", 30),  # 19 out onto the far causeway
    ("R", 40, 20),  # 20 into the crystal tunnel, down
    ("S", 45),  # 21
    ("L", 70, 50),  # 22 Mirror Lake: round the shore onto the ice
    ("R", 80, 60),  # 23 sweeping out across the lake
    ("L", 60, 100),  # 24 between the ice columns, off the ice, south
    ("S", 60),  # 25 the ascent: the ice tunnel (stretched to close the lap)
    ("L", 50, 90),  # 26 the fractured canyon, east
    ("S", 45),  # 27 the gallery over the Cathedral
    ("R", 45, 90),  # 28 south, out of the great opening
    ("S", 120),  # 29 the Great Rift Bridge
    ("L", 60, 90),  # 30 east
    ("S", 80),  # 31 the final descent (stretched to close the lap)
    ("R", 90, 30),  # 32
    ("S", 40),  # 33
    ("L", 90, 30),  # 34
    ("S", 20),  # 35
    ("L", 50, 90),  # 36 the last drift
    ("S", 20),  # 37 onto the finish straight
]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 25, 31, START, 90.0)
SEG = kit.segment_starts(PATH)
LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))
LOOP_SEG = 18


def _seg_point(i):
    return next(p for p in PATH if p[3] == i)


def _seg_points(i):
    return [p for p in PATH if p[3] == i]


def _arc_centre(i):
    x, y, h, _ = _seg_point(i)
    sg = LAYOUT[i]
    a = math.radians(h + (90 if sg[0] == "L" else -90))
    return (x + sg[1] * math.cos(a), y + sg[1] * math.sin(a))


MONOLITH = _arc_centre(13)
# The loop's entry (the end of the causeway) and its heading (turtle degrees).
LOOP_IN = PATH[[k for k, p in enumerate(PATH) if p[3] == LOOP_SEG][0] - 1]
LOOP_HEAD = LOOP_IN[2]
LOOP_OUT = _seg_points(LOOP_SEG)[-1]

# ---------------------------------------------------------------- heights

Z_START = 44.0  # the snowfield
Z_CATH = 24.0  # the Cathedral's roads (and the Loop)
Z_LAKE = 11.0  # Mirror Lake's ice
Z_BRIDGE = 56.0  # the Great Rift Bridge
ANCHORS = [
    (0.0, Z_START),
    (SEG[1] + 20, Z_START),
    (SEG[2], 42.0),  # down the ice wall
    (SEG[5], 35.0),
    (SEG[6], 33.5),  # the ice bridge
    (SEG[7], 32.5),
    (SEG[8] - 5, Z_CATH),  # down the tunnel into the Cathedral
    (SEG[19] + 8, Z_CATH),
    (SEG[22], Z_LAKE + 0.4),  # down the crystal tunnel
    (SEG[24] + 40, Z_LAKE + 0.4),
    (SEG[26], 30.0),  # the ascent
    (SEG[27], 40.0),
    (SEG[28], 50.0),
    (SEG[29], Z_BRIDGE),
    (SEG[30], Z_BRIDGE),  # the Great Rift Bridge
    (SEG[31], 55.0),
    (SEG[32], 52.0),  # the final descent
    (SEG[34], 47.0),
    (SEG[36], Z_START),
    (LENGTH, Z_START),
]
# Stretches that must be dead level: the Cathedral round the Loop, the lake.
LEVEL = [(SEG[8] + 10, SEG[19] + 5), (SEG[22] + 6, SEG[24] + 36)]


def _lin(d):
    d = min(max(d, 0.0), LENGTH)
    for (d0, z0), (d1, z1) in zip(ANCHORS, ANCHORS[1:]):
        if d0 <= d <= d1:
            return lerp(z0, z1, (d - d0) / max(1e-6, d1 - d0))
    return Z_START


def road_z(d, seg=None):
    """The road's height d metres along the lap: the anchors, eased over 30 m (exactly
    level round the Loop and on the lake)."""
    for a, b in LEVEL:
        if a <= d <= b:
            return _lin(d)
    return sum(_lin(d + k) for k in range(-15, 16, 3)) / 11


def road_w(d, seg):
    if seg in (0, 36, 37):
        return 18.0  # the start and finish
    if seg in (12, 14):
        return 14.0  # the bridges in the Cathedral
    if seg in (17, 18, 19):
        return 14.0  # the causeway: as wide as the Loop
    if seg in (22, 23, 24):
        return 18.0  # Mirror Lake
    if seg == 29:
        return 15.0  # the Great Rift Bridge
    if seg in (6, 7):
        return 14.0  # the ice bridge and the tunnel
    return 16.0


ROUTE, SHARP, LOOPS = kit.route_with_loops(PATH, LAYOUT, road_z, every=10.0, width=road_w)


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
    """Distance from points to a polyline (the lap), fast: a grid of its points."""

    def __init__(self, pts, cell=24.0):
        self.cell = cell
        self.pts = pts
        self.grid = {}
        for k, p in enumerate(pts):
            self.grid.setdefault((int(p[0] // cell), int(p[1] // cell)), []).append(k)

    def find(self, x, y, reach=2):
        """(distance, index of the nearest point), or (inf, -1) if none nearby."""
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


NEAR = Near(PATH)
_D = [0.0]
for _a, _b in zip(PATH, PATH[1:]):
    _D.append(_D[-1] + math.hypot(_b[0] - _a[0], _b[1] - _a[1]))


def lap_near(x, y, reach=2):
    """(distance to the lap, distance along it, segment) for the nearest lap point."""
    d, k = NEAR.find(x, y, reach)
    if k < 0:
        return d, 0.0, -1
    return d, _D[k], PATH[k][3]


# The Rift: the chasm from west to east between the snowfield (south) and the glacier.
RIFT_N = -95.0  # the glacier's face
ABYSS = -150.0  # the floor, lost in mist


def face_y(x):
    """Where the glacier's south face is (the Rift's north wall): the chasm is widest in
    the east, where the ice bridge crosses it, narrowest in the west under the Great Rift
    Bridge."""
    return lerp(RIFT_N, RIFT_N + 55.0, sm((x + 300.0) / 220.0)) + 3.0 * math.sin(x / 37.0) + 2.0 * math.sin(x / 13.0 + 1.0)


# The descent's line along the wall: road y for each metre of x (segments 1-5).
_LEDGE = {}
for _p in PATH:
    if 1 <= _p[3] <= 5:
        _k = int(round(_p[0]))
        _LEDGE[_k] = min(_LEDGE.get(_k, 1e9), _p[1])


def rim_y(x):
    """The Rift's south rim, where the snowfield breaks off. Along the ice-wall descent it
    hugs the road, so the road is carved into the wall with the chasm beside it."""
    base = -186.0 + 4.0 * math.sin(x / 41.0) + 2.0 * math.sin(x / 11.0)
    ys = [_LEDGE[k] for k in range(int(x) - 2, int(x) + 3) if k in _LEDGE]
    if ys and 25.0 <= x <= 175.0:
        return min(base + 8.0, min(ys) - 10.5)
    return base


# The glacier (massif): from the Rift's north face to the north edge, west to east.
MASSIF = (-780.0, 300.0, RIFT_N, 390.0)


def in_massif(x, y, pad=0.0):
    x0, x1, y0, y1 = MASSIF
    return x0 - pad <= x <= x1 + pad and face_y(x) - pad <= y <= y1 + pad


def glacier_top(x, y):
    """The glacier's surface (the massif's top, and the land round it): rising from its
    broken south face to a great dome over the Cathedral, ridged and crevassed."""
    rise = sm((y - RIFT_N) / 140.0)
    dome = 50.0 * math.exp(-(((x + 60.0) / 300.0) ** 2) - ((y - 160.0) / 220.0) ** 2)
    ridges = 6.0 * math.sin(x / 47.0 + y / 61.0) + 4.0 * math.sin(x / 19.0 - y / 23.0)
    return 108.0 + 30.0 * rise + dome + ridges * (0.4 + 0.6 * rise)


def snowfield(x, y):
    """The snowfield south of the Rift: level round the start, rising east into an ice
    ridge over the descent's wall, and into mountains far off."""
    h = Z_START - 1.5 + 1.2 * math.sin(x / 31.0) * math.cos(y / 27.0)
    # The ice ridge above the wall the descent is carved into.
    ridge = sm((x - 20.0) / 60.0) * sm((-120.0 - y) / 40.0 + 1.0) * sm((y + 330.0) / 60.0)
    h += 34.0 * ridge * sm((x - 10) / 120.0)
    # The west: the Great Rift Bridge lands on a high shoulder.
    h += 14.0 * sm((-260.0 - x) / 120.0) * sm((y + 330.0) / 120.0)
    # Mountains all round the far edges.
    far = max(0.0, x - 420.0) * 0.7 + max(0.0, -820.0 - x) * 0.7 + max(0.0, -430.0 - y) * 0.8
    h += min(260.0, far) + 30.0 * sm((far - 40.0) / 120.0) * (0.5 + 0.5 * math.sin(x / 53.0 + y / 41.0))
    return h


def natural(x, y):
    """The land, before it's shaped round the roads."""
    if in_massif(x, y):
        return ABYSS  # under the glacier (only seen through the Cathedral's abyss)
    fy, ry = face_y(x), rim_y(x)
    if y > fy:
        # North of the Rift beyond the glacier's ends: more glacier.
        return glacier_top(x, y)
    if y > ry:
        # The Rift: sheer walls, a jagged floor far below.
        return ABYSS + 6.0 * math.sin(x / 23.0) * math.cos(y / 17.0)
    return snowfield(x, y)


def classify(c, n, info):
    if c.z < ABYSS + 30:
        return ("abyss_glow", "abyss")
    if n.z < 0.55:
        if c.z > Z_START + 4 or c.y > RIFT_N - 20:
            return ("glacier_wall" if (int(c.z / 14) + int(c.x / 50)) % 3 == 0 else "rift_cliff", "wall")
        return ("rift_cliff" if (int(c.z / 9) + int(c.x / 40)) % 3 else "rift_rock", "wall")
    if info["d"] < 10.5:
        return ("rift_road", "snow_stone")
    return ("rift_snow", "deep_snow")


# ---------------------------------------------------------------- shortcuts


def _arc_pts(cx, cy, r, a0, a1, n):
    return [(cx + r * math.cos(a0 + (a1 - a0) * k / n), cy + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]


def monolith_shortcut():
    """Through the glowing crystal arch: a chord across the Monolith's island, inside the
    curve, from where the road starts round it to where it leaves."""
    a = _seg_points(13)
    p0, p1 = a[0], a[-1]
    cx, cy = MONOLITH
    # Leave the road a little after the curve starts, rejoin a little before it ends.
    k0, k1 = len(a) // 7, len(a) - 1 - len(a) // 7
    q0, q1 = a[k0], a[k1]
    pts = [(q0[0], q0[1])]
    # Bow gently away from the Monolith (it mustn't graze the base crystals).
    for t in (0.25, 0.5, 0.75):
        x = q0[0] + (q1[0] - q0[0]) * t
        y = q0[1] + (q1[1] - q0[1]) * t
        dx, dy = x - cx, y - cy
        dl = math.hypot(dx, dy) or 1.0
        pull = 6.0 * math.sin(math.pi * t)
        pts.append((x + dx / dl * pull, y + dy / dl * pull))
    pts.append((q1[0], q1[1]))
    return pts, (p0, p1)


def lake_shortcut():
    """The thin-ice shortcut: straight across the lake, inside the sweep."""
    a = _seg_points(22)
    b = _seg_points(24)
    q0 = a[len(a) // 3]
    q1 = b[len(b) * 2 // 3]
    pts = []
    for k in range(7):
        t = k / 6
        pts.append((q0[0] + (q1[0] - q0[0]) * t, q0[1] + (q1[1] - q0[1]) * t))
    return pts


MONO_SHORT, _ = monolith_shortcut()
LAKE_SHORT = lake_shortcut()


# ---------------------------------------------------------------- the course


def main():
    c = kit.Course(TRACK_ID, "Aurora Rift", "aurora_rift")
    (ex, ey, _), (xx, xy, _) = LOOPS[0]
    c.route(ROUTE, width=16.0, bank=6.0, sharp=SHARP, flat=[(ex, ey, 46), (xx, xy, 46)])
    lamps = ("edge_amber", "wall")
    snowbank = ("rift_snow", "packed_snow")
    stone = ("rift_stone", "wall")
    ice_wall = ("glacier_wall", "wall")
    c.kinds = {
        # On the snowfield: glacier road, snow banks.
        "snowfield": {"mat": "rift_road", "shoulder": 1.8, "shoulder_mat": snowbank, "barrier": 0.8, "barrier_mat": ("rift_snow", "wall")},
        # Carved into the Rift's ice wall: amber edge lamps on the chasm side.
        "ledge": {"mat": "rift_road", "shoulder": 1.0, "shoulder_mat": snowbank, "barrier": 1.0, "barrier_mat": lamps,
                  "deck": 7.0, "deck_mat": ("rift_cliff", "wall"), "ground": False},
        # The natural ice bridge over the Rift.
        "icebridge": {"mat": "rift_road", "shoulder": 1.0, "shoulder_mat": ("glacier_wall", "snow_stone"), "barrier": 0.9,
                      "barrier_mat": ice_wall, "deck": 9.0, "deck_mat": ice_wall, "ground": False},
        # Tunnels and galleries in the ice.
        "tunnel": {"mat": "rift_road", "shoulder": 1.2, "shoulder_mat": ("cavern_ice", "snow_stone"), "barrier": 0.7, "barrier_mat": lamps},
        # The Cathedral's cliff ledges and the causeways: lamps along the abyss.
        "cathedral": {"mat": "rift_road", "shoulder": 1.0, "shoulder_mat": ("rift_stone", "snow_stone"), "barrier": 1.0, "barrier_mat": lamps,
                      "deck": 8.0, "deck_mat": ("rift_rock", "wall"), "ground": False},
        "causeway": {"mat": "rift_road", "shoulder": 0.8, "shoulder_mat": ("rift_stone", "snow_stone"), "barrier": 1.1, "barrier_mat": lamps,
                     "deck": 4.5, "deck_mat": stone, "ground": False, "exact": True},
        # The suspended stone bridge, and the ice bridge to the north wall.
        "bridge": {"mat": "rift_road", "shoulder": 0.8, "shoulder_mat": ("rift_stone", "snow_stone"), "barrier": 1.2, "barrier_mat": stone,
                   "deck": 3.5, "deck_mat": stone, "ground": False},
        "icespan": {"mat": "rift_road", "shoulder": 0.8, "shoulder_mat": ("glacier_wall", "snow_stone"), "barrier": 1.0, "barrier_mat": ice_wall,
                    "deck": 6.0, "deck_mat": ice_wall, "ground": False},
        # The Monolith's island.
        "island": {"mat": "rift_road", "shoulder": 1.6, "shoulder_mat": ("rift_stone", "snow_stone"), "barrier": 0.9, "barrier_mat": lamps,
                   "deck": 6.0, "deck_mat": ("rift_rock", "wall"), "ground": False},
        # Mirror Lake: slippery clear ice.
        "lake": {"mat": "rift_ice_road", "shoulder": 2.0, "shoulder_mat": ("mirror_ice", "ice")},
        # The ascent, and the Great Rift Bridge.
        "climb": {"mat": "rift_road", "shoulder": 1.2, "shoulder_mat": snowbank, "barrier": 0.9, "barrier_mat": lamps},
        "greatbridge": {"mat": "rift_road", "shoulder": 0.8, "shoulder_mat": ("rift_stone", "snow_stone"), "barrier": 1.3, "barrier_mat": ("rift_carved", "wall"),
                        "deck": 4.0, "deck_mat": stone, "ground": False},
    }
    s_in = kit.s_near(c, ex, ey)
    s_out = kit.s_near(c, xx, xy)

    def label(smp):
        s = smp.s
        if s_in <= s <= s_out:
            return "gap"
        seg = seg_of(s)
        if seg in (2, 3, 4) or (seg == 1 and s > SEG[1] + 40) or (seg == 5 and s < SEG[5] + 20):
            return "ledge"
        if seg == 6:
            return "icebridge" if smp.p.y < face_y(smp.p.x) - 4 else "tunnel"
        if seg == 7 or (seg == 8 and s < SEG[8] + 8):
            return "tunnel"
        if seg in (8, 9, 10, 11):
            return "cathedral"
        if seg == 12:
            return "bridge"
        if seg == 13:
            return "island"
        if seg == 14:
            return "icespan"
        if seg in (15, 16):
            return "cathedral"
        if seg in (17, 19) or seg == LOOP_SEG:
            return "causeway"
        if seg in (20, 21) or (seg == 22 and s < SEG[22] + 15):
            return "tunnel"
        if seg in (22, 23) or (seg == 24 and s < SEG[24] + 60):
            return "lake"
        if seg in (24, 25, 26, 27, 28):
            return "climb"
        if seg == 29:
            return "greatbridge"
        return "snowfield"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k != "snowfield":
            specials.append((s0, s1, k))
    # The roads stop exactly at the Loop's ends.
    snap = lambda v: s_in if abs(v - s_in) < 3 else s_out if abs(v - s_out) < 3 else v  # noqa: E731
    specials = [(snap(a), snap(b)) + tuple(rest) for a, b, *rest in specials]
    c.roads(kit.plan(c, specials, "snowfield", max_len=200.0))

    lp = kit.LoopPath(ex, ey, Z_CATH, LOOP_HEAD, LOOP_R, LOOP_RAMP, LOOP_SHIFT, 14.0)
    c.loop(lp, road_mat=("rift_road", "snow_stone"), side_mat=("glacier_wall", "wall"), rail_mat=("rift_stone", "wall"),
           glow_mat=("edge_amber", "wall"), thickness=1.8, rail=1.0, min_speed=15.0, commit=20.0, boost=(1.4, 2.0), gravity=8.0)

    # The shortcuts: through the Monolith's crystal arch (cut stone on the island), and
    # across the thin ice on Mirror Lake.
    mono = [(x, y, Z_CATH) for x, y in MONO_SHORT]
    c.shortcut("Crystal Arch", mono, "rift_ice_road", "icy_stone", width=9.0, shoulder=0.6, shoulder_mat=("rift_stone", "snow_stone"))
    lake = [(x, y, Z_LAKE + 0.25) for x, y in LAKE_SHORT]
    c.shortcut("Thin Ice", lake, "thin_ice", "ice", width=8.0, shoulder=0.5, shoulder_mat=("thin_ice", "ice"))

    import aurora_scenery  # noqa: E402

    aurora_scenery.build(c, sys.modules[__name__], lp, s_in, s_out)
    c.finish()


if __name__ == "__main__":
    main()
