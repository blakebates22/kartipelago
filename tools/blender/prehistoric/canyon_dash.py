# Canyon Dash: Desert World, course 1. A short, fast lap round a great red-rock canyon.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/canyon_dash.py      (the bpy module)
#
# A lap of about 1.9 km (around 75 s) on a warm desert afternoon, all round one canyon:
# a wide outer canyon (the plateau's rim, then a broad sandstone terrace) with a deep
# inner gorge cut into its floor, a turquoise river far below, and a great waterfall at
# its head where a river off the eastern plateau pours in.
#
#   1  The Canyon Overlook: the start, on the south rim's plateau at a desert racing
#      outpost (a timber arch, banners, a windmill and a lookout tower), the whole
#      canyon dropping away to the right and the great bridge in the distance.
#   2  The Great Canyon Descent: off the rim onto a road carved into the canyon's south
#      wall, down broad, banked cliffside corners to the terrace below...
#   3  ...and round the last great bend the Sandstone Arch comes into view, framing the
#      canyon as it opens out west toward distant mountains. The road runs right under
#      it, fast.
#   4  The Great Canyon Bridge: a long timber trestle on stone piers, 60 m over the
#      inner gorge and the river, waterfalls on the terraces downstream.
#   5  The Red-Rock Pass: a broad banked turn east, then a winding slot between towering
#      walls cut into the north mesa, and a short natural tunnel.
#   6  The Waterfall Overlook: out along the inner gorge's north rim, the great
#      waterfall at the canyon's head straight ahead; round the head over a stone bridge
#      just above the brink, the falls plunging beside you.
#   7  The Mesa Run: the open eastern plateau, fast between towering buttes, round a
#      great butte (or through the narrow slot in it: the shortcut).
#   8  The Final Sprint: rising back to the rim, the start arch ahead, onto the line.
#
# Saves tracks-src/canyon_dash.blend and exports public/tracks/canyon_dash/. The scenery
# is canyon_scenery.py, built from the kit in canyon_props.py.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import ruin_mode  # noqa: E402
from course_kit import lerp, smooth  # noqa: E402

# The ruin (canyon_ruins.py): the dragons broke the Great Canyon Bridge in the middle and
# wrecked the canyon's far side. You jump the gap; past it the north mesa's lobe has come
# down (the pass is buried), so a steep cutting through the rockslide dives down the
# gorge's north wall to the river, the fallen rock crosses it, and another wrecked
# tunnel (its roof caved in) climbs the far wall back up to the south rim. Everything
# else (the land, the landmarks) is the course's own.
RUIN = ruin_mode.ON
TRACK_ID = "canyon_dash_ruin" if RUIN else "canyon_dash"

# ---------------------------------------------------------------- the layout

START = (150.0, -150.0)
LAYOUT = [
    ("S", 25),  # 0  1: the start, west along the south rim
    ("R", 110, 25),  # 1  toward the edge...
    ("S", 30),  # 2  2: ...and off it, onto the road carved into the wall
    ("L", 120, 40),  # 3  the great cliffside bend
    ("S", 25),  # 4  over a side ravine on a timber trestle
    ("R", 100, 15),  # 5
    ("S", 50),  # 6  3: under the Sandstone Arch
    ("R", 65, 90),  # 7  4: across the terrace onto the bridge
    ("S", 150),  # 8  the Great Canyon Bridge
    ("R", 65, 90),  # 9  the banked turn east off it
    ("S", 30),  # 10
    ("L", 60, 35),  # 11 5: the Red-Rock Pass
    ("R", 60, 60),  # 12
    ("S", 50),  # 13 the tunnel
    ("L", 80, 25),  # 14
    ("S", 250),  # 15 6: the Waterfall Overlook (stretched to close the lap)
    ("R", 200, 20),  # 16
    ("L", 200, 20),  # 17
    ("R", 85, 90),  # 18 round the canyon's head, over the brink
    ("S", 90),  # 19 7: the Mesa Run, south (stretched to close the lap)
    ("R", 85, 90),  # 20 west
    ("S", 12),  # 21
    ("L", 72, 45),  # 22 round the great butte (the shortcut goes through it)
    ("R", 72, 90),  # 23
    ("L", 72, 45),  # 24
    ("S", 25),  # 25 8: the final sprint onto the line
]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 15, 19, START, 180.0)
SEG = kit.segment_starts(PATH)
LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))
# (The standard lap: the canyon's landmarks are laid out from it, in the ruin too.)
STD_LAYOUT, STD_PATH, STD_SEG = LAYOUT, PATH, SEG


def _seg_point(i):
    return next(p for p in STD_PATH if p[3] == i)


def _seg_points(i):
    return [p for p in STD_PATH if p[3] == i]


def _arc_centre(i):
    x, y, h, _ = _seg_point(i)
    sg = STD_LAYOUT[i]
    a = math.radians(h + (90 if sg[0] == "L" else -90))
    return (x + sg[1] * math.cos(a), y + sg[1] * math.sin(a))


BUTTE_R = 46.0  # (set from the shortcut below: the great butte the Mesa Run sweeps round)

# ---------------------------------------------------------------- heights

Z_RIM = 56.0  # the south rim's plateau (the start)
Z_TERRACE = 24.0  # the terrace at the foot of the descent, and the bridge
Z_RIVER = -40.0  # the river at the bottom of the inner gorge
Z_EAST = 50.0  # the eastern plateau
ANCHORS = STANDARD_ANCHORS = [
    (0.0, Z_RIM),
    (SEG[1] + 20, Z_RIM),
    (SEG[3], 51.0),  # down the wall
    (SEG[5], 36.0),
    (SEG[6] + 20, 28.0),
    (SEG[7] + 25, Z_TERRACE),
    (SEG[9] + 60, Z_TERRACE),  # the bridge: dead level
    (SEG[11], 26.0),
    (SEG[14], 37.0),  # up through the pass
    (SEG[15] + 120, 44.0),
    (SEG[18], 46.0),
    (SEG[19], 47.5),  # over the brink
    (SEG[21], 49.0),
    (SEG[23], 51.0),
    (SEG[25], 54.5),  # the final rise
    (LENGTH, Z_RIM),
]
LEVEL = [(SEG[7] + 25, SEG[9] + 60)]


def _lin(d):
    d = min(max(d, 0.0), LENGTH)
    for (d0, z0), (d1, z1) in zip(ANCHORS, ANCHORS[1:]):
        if d0 <= d <= d1:
            return lerp(z0, z1, (d - d0) / max(1e-6, d1 - d0))
    return Z_RIM


# Blake's review (Oct 23): rolling hills along the overlook, and on the Mesa Run a crest
# and then a sharp one you hop off (a small jump: no gap, the road just drops away
# faster than you fall).
OVER_HILLS = (SEG[15] + 30, SEG[15] + 230, 3, 1.7)  # from, to, how many, how high
MESA_CREST = (SEG[19] + 6, SEG[19] + 30, 1.4)  # a gentle crest
MESA_KICK = (SEG[19] + 44, 22.0, 2.2, 14.0, 3.0)  # start, rise over, rise, fall over, fall


def hills(d):
    """The review's hills, on top of the eased anchors."""
    z = 0.0
    a, b, n, h = OVER_HILLS
    if a <= d <= b:
        z += h * math.sin(math.pi * n * (d - a) / (b - a)) ** 2
    a, b, h = MESA_CREST
    if a <= d <= b:
        z += h * math.sin(math.pi * (d - a) / (b - a)) ** 2
    a, up, rise, down, fall = MESA_KICK
    if a <= d <= a + up:
        z += rise * smooth((d - a) / up)
    elif a + up < d <= a + up + down:
        # Off the lip: down faster than it went up (a little lower than before, then back).
        u = (d - a - up) / down
        z += rise - fall * u ** 1.6
    elif a + up + down < d <= a + up + down + 20.0:
        z += (rise - fall) * (1 - smooth((d - a - up - down) / 20.0))
    return z


def road_z(d, seg=None):
    """The road's height d metres along the lap: the anchors, eased over 30 m (exactly
    level across the bridge), and the review's hills."""
    for a, b in LEVEL:
        if a <= d <= b:
            return _lin(d)
    return sum(_lin((d + k) % LENGTH if 0 <= d + k <= LENGTH else d + k) for k in range(-15, 16, 3)) / 11 + hills(d)


def road_w(d, seg):
    if RUIN and seg >= 9:
        if seg in (15, 16):
            return 16.0  # across the river
        return 20.0 if seg >= 21 else 15.0
    if seg in (0, 25, 24):
        return 20.0  # the start and finish: room for the pack
    if seg in (8,):
        return 15.0  # the bridge
    if seg in (11, 12, 13, 14):
        return 15.0  # the pass and the tunnel
    if seg in (2, 3, 4, 5, 6):
        return 16.0  # the ledge down the wall
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


def wob(x, seed=0.0, a=1.0):
    """A wavy edge: big bays and buttresses, smaller notches."""
    return a * (7.0 * math.sin(x / 31.0 + seed) + 4.0 * math.sin(x / 13.0 + 2 * seed + 1) + 2.0 * math.sin(x / 5.3 + seed))


# The road's y for each metre of x along given segments (for edges that hug it).
def _track_y(segs, pick=min):
    out = {}
    for p in STD_PATH:
        if p[3] in segs:
            k = int(round(p[0]))
            out[k] = pick(out.get(k, p[1]), p[1]) if k in out else p[1]
    return out


_LEDGE = _track_y((2, 3, 4, 5, 6))  # the descent
_OVER = _track_y((15, 16, 17), max)  # the overlook


def _near_y(table, x, r=3):
    ys = [table[k] for k in range(int(x) - r, int(x) + r + 1) if k in table]
    return sum(ys) / len(ys) if ys else None


# The inner gorge: a centre line west from the waterfall at its head, and a half-width.
# Its head sits inside the road's turn round it (segment 18), the falls' lip ~30 m from
# the road.
_C18 = _arc_centre(18)
X_HEAD = _C18[0] + 18.0
Y_HEAD = _C18[1] + 24.0


def _gorge_base(x):
    return 8.0 + 14.0 * math.sin(x / 210.0)


def gorge_c(x):
    """The inner gorge's centre line (y) at x: swinging north toward its head."""
    return _gorge_base(x) + (Y_HEAD - _gorge_base(X_HEAD)) * sm((x - 60.0) / (X_HEAD - 60.0))


def gorge_hw(x):
    """Half-width of the inner gorge at its rim."""
    w = 70.0 + 0.11 * max(0.0, -400.0 - x)  # it widens far downstream
    w = lerp(w, 30.0, sm((x - 150.0) / 280.0))  # and narrows to the head
    return w


def gorge_u(x, y):
    """How far inside the inner gorge (x, y) is, from its rim (negative: outside)."""
    if x > X_HEAD:
        d = math.hypot(x - X_HEAD, y - gorge_c(X_HEAD))
        hw = gorge_hw(X_HEAD)
    else:
        d = abs(y - gorge_c(x))
        hw = gorge_hw(x)
    side = 1.0 if y > gorge_c(min(x, X_HEAD)) else -1.0
    return hw + wob(x + (300 if side > 0 else 0), 1.7 if side > 0 else 0.4, 0.8) - d


def terrace_z(x):
    """The outer canyon's floor (the terrace): low by the bridge, rising up-canyon with
    the road along the north rim."""
    return Z_TERRACE - 2.0 + 16.0 * sm((x + 140.0) / 200.0) + 8.0 * sm((x - 60.0) / 270.0)


def south_rim(x):
    """The south rim: where the plateau breaks off into the outer canyon. Along the
    descent it hugs the road (the road is carved into the wall just below it)."""
    base = lerp(-112.0, -52.0, sm((x - 200.0) / 130.0)) + 0.5 * wob(x, 3.1)
    if x < -120:
        base = lerp(-150.0, -230.0, sm((-150.0 - x) / 260.0)) + wob(x, 3.1)
    ly = _near_y(_LEDGE, x)
    if ly is not None and -170 <= x <= 70:
        return min(base, ly - 10.5)
    if 70 < x < 110:
        return lerp(-150.5, base, sm((x - 70) / 40.0))
    return base


def north_rim(x):
    """The outer canyon's north edge: the north mesa's cliffs (the pass cuts through
    the mesa's southern lobe) or, east of it, the low edge of the plateau."""
    if x < -150:
        return 196.0 + wob(x, 5.2)
    if x < 70:
        return lerp(196.0, 112.0, sm((x + 150) / 14.0)) + 0.6 * wob(x, 5.2)
    oy = _near_y(_OVER, x, 6)
    if oy is not None:
        return oy + 40.0 + 0.5 * wob(x, 5.2)
    return 150.0 + wob(x, 5.2)


MESA_TOP = 84.0  # the north mesa (its top under 60 m over the pass road)


def mesa_top(x, y):
    """The north mesa's top, or None where there's no mesa: a great flat-topped block
    north of the canyon, its southern lobe reaching the inner gorge (the pass is cut
    through that lobe)."""
    if x > 380 or x < -900:
        return None
    top = MESA_TOP + 4.0 * math.sin(x / 47.0) * math.cos(y / 39.0)
    return lerp(top, Z_EAST + 4.0, sm((x - 250) / 120.0))


def steps(u, top, foot, bands):
    """A stepped canyon wall from `top` (at u = 0) down to `foot`: bands of
    (u width, share of the drop) pairs: a cliff is a narrow band, a talus slope or
    ledge a wide one."""
    z = top
    drop = top - foot
    at = 0.0
    for w, share in bands:
        if u <= at + w:
            return z - drop * share * sm((u - at) / w)
        z -= drop * share
        at += w
    return foot


OUTER_BANDS = ((3.5, 0.42), (7.0, 0.16), (3.0, 0.3), (9.0, 0.12))
INNER_BANDS = ((3.0, 0.22), (8.0, 0.12), (3.5, 0.24), (8.0, 0.08), (3.0, 0.3), (4.0, 0.04))
MESA_BANDS = ((4.0, 0.38), (10.0, 0.16), (4.0, 0.36), (12.0, 0.1))


def plateau(x, y):
    """The desert plateau round the canyon: the south rim (the start), the east."""
    h = Z_RIM + 1.5 * math.sin(x / 37.0) * math.cos(y / 29.0) + 0.8 * math.sin((x - y) / 17.0)
    h = lerp(h, Z_EAST + 1.2 * math.sin(x / 23.0), sm((x - 260.0) / 160.0))
    # The Mesa Run's plateau rises gently to the south-east, toward far mesas.
    h += 6.0 * sm((-y - 260.0) / 200.0) + 4.0 * sm((x - 640.0) / 200.0)
    return h


# The East Shelf: a high mesa east of the canyon's head. The river comes off its top in
# a great fall beside the road (on the left as you round the head), runs under the
# road's stone bridge and plunges over the gorge's head on the right.
SHELF_TOP = 98.0


def shelf_x(y):
    """The East Shelf's west rim (x) at y."""
    return 548.0 + 0.8 * wob(y + 77.0, 2.3) - 30.0 * sm((y + 40.0) / -90.0) * 0.0


def shelf_top(x, y):
    return SHELF_TOP + 3.0 * math.sin(x / 41.0) * math.cos(y / 33.0)


def river_y(x):
    return Y_HEAD + 4.0 * math.sin((x - X_HEAD) / 37.0)


POOL = (520.0, 0.0, 15.0)  # the shelf fall's plunge pool: x, (y set below), radius


def upper_river(x, y):
    """The river: on the shelf (bed high up), and from the shelf fall's pool to the
    gorge's head (under the road): (distance from its middle, its bed), or None."""
    if x < X_HEAD + 10:
        return None
    ry = river_y(x)
    face = shelf_x(ry)
    if x > face - 1.0:
        return abs(y - ry), SHELF_TOP - 7.0
    foot = face - sum(w for w, _ in MESA_BANDS)
    px, py = POOL[0], river_y(POOL[0])
    dp = math.hypot(x - px, y - py) - POOL[2]
    if x < foot + 4.0:
        bed = lerp(41.0, 43.0, sm((x - X_HEAD) / (px - X_HEAD)))
        return min(abs(y - ry), dp + 6.0), bed
    if dp < 6.0:
        return dp + 6.0, 40.0
    return None


def natural_outer(x, y):
    """The land without the inner gorge: the plateau, the outer canyon and the mesa, the
    side ravines and the upper river's channel."""
    h = plateau(x, y)
    mt = mesa_top(x, y)
    # The outer canyon (west of the head): the plateau stepping down to the terrace in
    # the south, the mesa's cliffs in the north.
    if x < 420:
        zt = terrace_z(x)
        rs, rn = south_rim(x), north_rim(x)
        if y >= rn and mt is not None:
            hc = mt
        elif rs < y < rn:
            us, un = y - rs, rn - y
            if us < un:
                hc = steps(us, max(h, zt), zt, OUTER_BANDS)
            else:
                hc = steps(un, max(mt if mt is not None else h, zt), zt, MESA_BANDS)
        else:
            hc = h
        h = lerp(h, hc, sm((420.0 - x) / 70.0))
    # The East Shelf.
    if x > 420 and -260 < y < 420:
        u = shelf_x(y) - x
        top = shelf_top(x, y) * sm((y + 250.0) / 60.0) + h * (1 - sm((y + 250.0) / 60.0))
        if u <= 0:
            h = max(h, top)
        elif u < sum(w for w, _ in MESA_BANDS):
            h = max(h, steps(u, top, h, MESA_BANDS))
    # Side ravines notched into the walls (one under the descent's timber trestle).
    for ax, ay, bx, by, za, zb, hw in RAVINES:
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
        d = math.hypot(x - ax - t * dx, y - ay - t * dy)
        w = hw * (0.6 + 0.4 * t)
        if d < w + 6:
            bed = lerp(za, zb, t) + 1.5 * math.sin(t * 9.0)
            h = min(h, lerp(bed, h, sm((d - w * 0.4) / (w * 0.6 + 6))))
    # The upper river's channel, to the brink of the falls.
    r = upper_river(x, y)
    if r is not None:
        d, bed = r
        if d < 18:
            h = min(h, lerp(bed, h, sm((d - 8.0) / 10.0)))
    return h


def inner_scale(x):
    return max(0.7, min(1.7, gorge_hw(min(x, X_HEAD)) / 42.0))


def natural(x, y):
    """The land before it's shaped round the roads: the inner gorge cut into it all (and
    in the ruin, the rockslides the wrecked tunnels run down)."""
    h = natural_outer(x, y)
    u = gorge_u(x, y)
    if u > 0:
        k = inner_scale(x)
        h = min(h, steps(u, h, Z_RIVER, [(w * k, f) for w, f in INNER_BANDS]))
    if RUIN_SLIDE:
        h = min(h, slide(x, y))
    return h


# The ruin's rockslides: where the mesa's lobe and the gorge's walls came down, the land
# falls away round the ruin's cuttings in slopes of rubble (a talus cone round each point
# of their road). Kept on a grid, built the first time it's needed.
RUIN_SLIDE = []  # [(x, y, z)] along the ruin's cuttings (set below in the ruin)
_SLIDE = {}
SLIDE_GRADE, SLIDE_FLAT = 0.62, 12.0


def slide(x, y):
    g = _SLIDE
    if not g:
        xs = [p[0] for p in RUIN_SLIDE]
        ys = [p[1] for p in RUIN_SLIDE]
        g.update(x0=min(xs) - 120, y0=min(ys) - 120, cell=4.0)
        g["nx"] = int((max(xs) + 120 - g["x0"]) / 4.0) + 2
        g["ny"] = int((max(ys) + 120 - g["y0"]) / 4.0) + 2
        g["grid"] = [[min(z + SLIDE_GRADE * max(0.0, math.hypot(g["x0"] + i * 4.0 - px, g["y0"] + j * 4.0 - py) - SLIDE_FLAT)
                          for px, py, z in RUIN_SLIDE) for i in range(g["nx"])] for j in range(g["ny"])]
    u, v = (x - g["x0"]) / g["cell"], (y - g["y0"]) / g["cell"]
    if not (0 <= u < g["nx"] - 1 and 0 <= v < g["ny"] - 1):
        return 1e9
    i, j = int(u), int(v)
    fu, fv = u - i, v - j
    G = g["grid"]
    return lerp(lerp(G[j][i], G[j][i + 1], fu), lerp(G[j + 1][i], G[j + 1][i + 1], fu), fv)


def _ravine_under(s, length=60.0, out=40.0):
    """A side ravine crossing the road at s: from the plateau behind (left) down past the
    road to the terrace (right)."""
    k = min(range(len(STD_PATH)), key=lambda i: abs(_D[i] - s))
    x, y, h, _ = STD_PATH[k]
    a = math.radians(h)
    rx, ry = math.sin(a), -math.cos(a)  # the road's right
    z = road_z(s)
    return (x - rx * length, y - ry * length, x + rx * out, y + ry * out, Z_RIM - 6.0, terrace_z(x) - 1.0, 9.0)


_D = [0.0]
for _a, _b in zip(PATH, PATH[1:]):
    _D.append(_D[-1] + math.hypot(_b[0] - _a[0], _b[1] - _a[1]))
RAVINES = [_ravine_under(SEG[4] + 12)]


def in_gorge_deep(x, y):
    """Well inside the inner gorge: anything that falls in here is put back on the road
    (by the abyss floor under it all; the two floors overlap round the rim)."""
    return gorge_u(x, y) > 14.0


# The tunnel's stretch of road: the land above it there is hidden (the tunnel's rock
# stands over it).
TUNNEL_S = (STD_SEG[13] - 6.0, STD_SEG[14] + 4.0)


def tunnel_rock():
    """The tunnel's rock: (centre x, y, heading, half-length, half-width) of the block of
    the mesa bridging the slot over the road (the land under it is left out)."""
    s0, s1 = TUNNEL_S
    k = min(range(len(STD_PATH)), key=lambda i: abs(_D[i] - (s0 + s1) / 2))
    x, y, h, _ = STD_PATH[k]
    return x, y, math.radians(h), (s1 - s0) / 2 + 16.0, 34.0


def under_tunnel_rock(x, y, k=0.8):
    mx, my, a, rx, ry = tunnel_rock()
    dx, dy = x - mx, y - my
    u = dx * math.cos(a) + dy * math.sin(a)
    v = -dx * math.sin(a) + dy * math.cos(a)
    return (u / (rx * k)) ** 2 + (v / (ry * k)) ** 2 < 1.0


# Where the wall meshes stand (canyon_walls.py fills these in before the land is
# built): x-spans of the south and north rim walls. The land grid leaves them out.
WALL_SPANS = {"south": [], "north": [], "east": []}


def walled(x, y, pad=0.4):
    """Is (x, y) on one of the wall meshes (so the land grid leaves it out)? (In the ruin
    the gorge's walls are down in a rockslide across RUIN_OPEN: the land grid has them.)"""
    if gorge_u(x, y) > pad and not (RUIN_OPEN and RUIN_OPEN[0] <= x <= RUIN_OPEN[1]):
        return True
    for side, rim, width in (("south", south_rim, sum(w for w, _ in OUTER_BANDS)), ("north", north_rim, sum(w for w, _ in MESA_BANDS))):
        for a, b in WALL_SPANS[side]:
            if a <= x <= b:
                u = (y - rim(x)) if side == "south" else (rim(x) - y)
                if pad < u < width - pad:
                    return True
                break
    for a, b in WALL_SPANS["east"]:
        if a <= y <= b:
            u = shelf_x(y) - x
            if pad < u < sum(w for w, _ in MESA_BANDS) - pad:
                return True
            break
    return False


def classify(c, n, info):
    if walled(c.x, c.y):
        return None
    smp = info["sample"]
    if c.z > smp.p.z + 0.8 and under_tunnel_rock(c.x, c.y):
        return None
    zt = terrace_z(c.x)
    if RUIN and info["d"] < 14.0 and c.z < smp.p.z + 1.5:
        # Beside the ruin's road down in the gorge: the rockslide's rubble (no abyss).
        return ("talus", "dirt")
    cut = (SEG[11] - 10, SEG[22] + 10) if RUIN else (SEG[11] - 10, SEG[15] + 10)
    if cut[0] <= smp.s <= cut[1] and n.z < 0.85 and c.z > smp.p.z + 0.6:
        # The pass's walls rise straight from the road's edge: rock, all the way down.
        return ("strata_orange" if c.z > 30 else "strata_red", "wall")
    if gorge_u(c.x, c.y) > 2.0 and c.z < min(zt, natural(c.x, c.y) + 1) - 8.0:
        # Down in the inner gorge: walls are walls, and the floor and its ledges put
        # you back on the road.
        if n.z < 0.55:
            return (_layer(c.z), "wall")
        return ("talus" if c.z > Z_RIVER + 2 else "strata_purple", "abyss")
    if n.z < 0.5:
        # Cuts in the land grid (the descent's wall, the pass): one rock, its own bands.
        return ("strata_orange" if c.z > 30 else "strata_red", "wall")
    if n.z < 0.8:
        return ("talus", "loose_sand")
    if info["d"] < 10.5:
        return ("dash_shoulder", "dirt")
    if c.z < zt + 3.0 and c.x < 400:
        return ("desert_sand", "loose_sand")
    return (ground_mat(c.x, c.y), "loose_sand")


def ground_mat(x, y):
    """Patches of deeper red sand, pale drifts and bare rock across the plateaus."""
    v = math.sin(x / 41.0 + 0.7) * math.cos(y / 37.0) + 0.5 * math.sin((x - y) / 23.0) + 0.25 * math.sin(x / 9.0 + y / 11.0)
    if v > 0.9:
        return "slickrock"
    if v > 0.35:
        return "pale_sand"
    if v < -0.55:
        return "red_sand"
    return "desert_sand"


def _layer(z):
    """The canyon's rock layers, top to bottom."""
    if z > 62:
        return "strata_cream"
    if z > 44:
        return "strata_orange" if z < 50 or z > 80 else "strata_cream"
    if z > 22:
        return "strata_orange" if int(z / 7) % 3 else "strata_red"
    if z > 0:
        return "strata_red"
    if z > -22:
        return "strata_rust"
    return "strata_purple"


def underfloor_z(x, y):
    if in_gorge_deep(x, y):
        return None
    return natural(x, y) - 0.4


def abyss_z(x, y):
    """The invisible floor under the whole inner gorge: fall in anywhere (off a ledge,
    under a cliff) and you're put back on the road."""
    if gorge_u(x, y) < -14.0:
        return None
    return Z_RIVER - 0.6


# ---------------------------------------------------------------- the shortcut


def butte_shortcut():
    """Through the great butte: a narrow slot straight across from where the road starts
    round it to where it comes back, with a kink in the middle."""
    a = _seg_points(22)
    b = _seg_points(24)
    q0 = a[len(a) // 4]
    q1 = b[len(b) * 3 // 4]
    pts = []
    for k in range(9):
        t = k / 8
        x = q0[0] + (q1[0] - q0[0]) * t
        y = q0[1] + (q1[1] - q0[1]) * t
        # The kink: the slot jogs north then back through the rock.
        y += 4.5 * math.sin(math.pi * t) * math.sin(2 * math.pi * t)
        pts.append((x, y))
    return pts


BUTTE_SHORT = butte_shortcut()


def _butte():
    """The great butte: a long fin of rock across the bend's chord (the shortcut's slot
    runs down its length), as big as fits without crowding the main road round it."""
    (x0, y0), (x1, y1) = BUTTE_SHORT[0], BUTTE_SHORT[-1]
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2 + 3.0
    ang = math.atan2(y1 - y0, x1 - x0)
    best = None
    for rx in (56.0, 52.0, 48.0, 44.0, 40.0, 36.0, 32.0):
        for ry in (34.0, 30.0, 27.0, 24.0, 21.0):
            ok = True
            for p in STD_PATH:
                if p[3] not in (21, 22, 23, 24, 25):
                    continue
                dx, dy = p[0] - mx, p[1] - my
                u = dx * math.cos(ang) + dy * math.sin(ang)
                v = -dx * math.sin(ang) + dy * math.cos(ang)
                # Clear of the road's edge (and its shoulder) by a few metres, allowing
                # for the butte's lumpy outline.
                k = math.hypot(u / (rx * 1.2 + 12.0), v / (ry * 1.2 + 12.0))
                if k < 1.0:
                    ok = False
                    break
            if ok:
                best = (rx, ry)
                break
        if best:
            break
    return (mx, my), ang, best or (30.0, 20.0)


BUTTE, BUTTE_ANGLE, BUTTE_SIZE = _butte()


# ---------------------------------------------------------------- the ruin's lap

RUIN_OPEN = None  # (x0, x1): where the gorge's walls are down (the ruin)
RUIN_RIM_OPEN = {}  # {side: (x0, x1)}: where the rim walls are down (the ruin)
if RUIN:
    # Blake: the bridge broken (jump it); the far side wrecked: a steep tunnel down to
    # the river, rubble across it, another wrecked tunnel back up to the top (about a
    # fifth shorter: diving 60 m and climbing 90 m takes road). The course's own lap
    # over the bridge (0-8), then right along the foot of the fallen mesa (9-10), down
    # the cutting to the river (11-15), across it on the rockfall (16-17), and up the
    # wrecked tunnel (18-21) onto the rim and the start (22-23).
    LAYOUT = STD_LAYOUT[:9] + [
        ("R", 30, 90),  # 9  off the bridge, east
        ("S", 20),  # 10 along the fallen mesa's foot
        ("R", 100, 35),  # 11 the dive...
        ("S", 118),  # 12
        ("L", 100, 35),  # 13 ...down to the river
        ("S", 20),  # 14 the riverside
        ("R", 30, 90),  # 15 across the river on the rockfall
        ("S", 10),  # 16
        ("L", 30, 90),  # 17 into the wrecked tunnel, east
        ("S", 120),  # 18 the climb
        ("R", 40, 90),  # 19 round, south, still climbing...
        ("S", 10),  # 20 (closes the loop)
        ("R", 40, 90),  # 21 ...out onto the rim, west
        ("S", 100),  # 22 to the line (closes the loop)
    ]
    LAYOUT, PATH = kit.close_turtle(LAYOUT, 20, 22, START, 180.0)
    SEG = kit.segment_starts(PATH)
    LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))
    # The broken bridge's gap (12 m, over the gorge's middle), and the sagged far half.
    LIP = SEG[8] + 57.0
    LAND = LIP + 12.0
    Z_LOW = Z_RIVER + 4.0  # the river road, on the rockfall
    ANCHORS = [a for a in STANDARD_ANCHORS if a[0] <= SEG[7] + 25] + [
        (LIP, Z_TERRACE),
        (LAND, Z_TERRACE - 4.0),  # the far half, sagged at its broken end
        (SEG[9], Z_TERRACE - 1.0),
        (SEG[11], Z_TERRACE - 2.0),
        (SEG[14], Z_LOW),
        (SEG[17], Z_LOW),
        (SEG[21], Z_RIM - 1.5),
        (LENGTH, Z_RIM),
    ]
    LEVEL = [(SEG[7] + 25, SEG[9] + 10)]
    OVER_HILLS = (0.0, 1.0, 1, 0.0)
    MESA_CREST = (0.0, 1.0, 0.0)
    MESA_KICK = (-100.0, 1.0, 0.0, 1.0, 0.0)
    ROUTE = kit.route_points_by(PATH, road_z, every=8.0, width=road_w)
    RUIN_OPEN = (-175.0, 175.0)
    _d = 0.0
    for _i, (_x, _y, _h, _sg) in enumerate(PATH):
        if _i:
            _d += math.hypot(_x - PATH[_i - 1][0], _y - PATH[_i - 1][1])
        if SEG[10] <= _d <= SEG[21] and (not RUIN_SLIDE or math.hypot(_x - RUIN_SLIDE[-1][0], _y - RUIN_SLIDE[-1][1]) >= 6.0):
            RUIN_SLIDE.append((_x, _y, road_z(_d) - 0.6))
    RUIN_RIM_OPEN = {"north": (-200.0, 60.0), "south": (120.0, 380.0)}


# ---------------------------------------------------------------- the course


def main():
    c = kit.Course(TRACK_ID, "Canyon Dash (Ruined)" if RUIN else "Canyon Dash", "canyon_ruins" if RUIN else "canyon_dash")
    c.route(ROUTE, width=18.0, bank=7.0)
    fence = ("fence_rail", "wall")
    verge = ("dash_shoulder", "dirt")
    stone = ("masonry", "wall")
    timber = ("weathered_timber", "wall")
    c.kinds = {
        # On the plateau: wide dirt road, ranch fences.
        "plateau": {"mat": "dash_road", "shoulder": 2.0, "shoulder_mat": verge, "barrier": 1.0, "barrier_mat": fence},
        # Carved into the canyon wall: a rock edge under the road on the drop side.
        "ledge": {"mat": "dash_road", "shoulder": 1.2, "shoulder_mat": verge, "barrier": 1.1, "barrier_mat": fence,
                  "deck": 3.0, "deck_mat": ("strata_red", "wall")},
        # A short timber trestle over a side ravine on the way down.
        "trestle": {"mat": "plank_deck", "shoulder": 0.6, "shoulder_mat": ("plank_deck", "road"), "barrier": 1.2,
                    "barrier_mat": timber, "deck": 1.6, "deck_mat": timber, "ground": False},
        # The terraces either end of the bridge.
        "terrace": {"mat": "dash_road", "shoulder": 1.8, "shoulder_mat": verge, "barrier": 1.0, "barrier_mat": fence,
                    "deck": 2.5, "deck_mat": ("strata_red", "wall")},
        # The Great Canyon Bridge.
        "bridge": {"mat": "plank_deck", "shoulder": 0.6, "shoulder_mat": ("plank_deck", "road"), "barrier": 1.3,
                   "barrier_mat": timber, "deck": 2.2, "deck_mat": timber, "ground": False},
        # The pass and its tunnel: rock walls do the fencing.
        "pass": {"mat": "dash_road", "shoulder": 1.6, "shoulder_mat": verge},
        # Along the gorge's rim.
        "overlook": {"mat": "dash_road", "shoulder": 1.6, "shoulder_mat": verge, "barrier": 1.1, "barrier_mat": fence,
                     "deck": 3.0, "deck_mat": ("strata_orange", "wall")},
        # The stone bridge over the river above the falls.
        "brink": {"mat": "dash_road", "shoulder": 0.8, "shoulder_mat": ("masonry", "road"), "barrier": 1.2, "barrier_mat": stone,
                  "deck": 3.5, "deck_mat": stone, "ground": False},
        # The Mesa Run, and an open stretch where the shortcut leaves and rejoins.
        "mesa": {"mat": "dash_road", "shoulder": 2.2, "shoulder_mat": verge, "barrier": 1.0, "barrier_mat": fence},
        "open": {"mat": "dash_road", "shoulder": 2.6, "shoulder_mat": verge},
    }
    S = SEG
    trestle = (S[4] - 4, S[5] + 6)
    if RUIN:
        ruin_course(c, trestle)
        return
    sc_a = kit.s_near(c, *BUTTE_SHORT[0])
    sc_b = kit.s_near(c, *BUTTE_SHORT[-1])
    # No fence anywhere the slot's road runs beside the main road (Blake's review: the
    # fence on the finish side was in the way coming out of the slot): from where the
    # slot's road first comes within reach of the road's edge to where it leaves it.
    near = [kit.s_near(c, x, y) for x, y in BUTTE_SHORT if c.nearest(x, y)[1] < 9.0 + 2.6 + 4.0 + 6.0]
    open_from = min([sc_a - 22] + [s for s in near if s < (sc_a + sc_b) / 2])
    open_to_from = min([sc_b - 22] + [s for s in near if s > (sc_a + sc_b) / 2]) - 14.0

    def label(smp):
        s = smp.s
        seg = seg_of(s)
        x, y = smp.p.x, smp.p.y
        if trestle[0] <= s <= trestle[1]:
            return "trestle"
        if seg in (2, 3, 4, 5, 6) or (seg == 7 and s < S[7] + 10):
            return "ledge"
        if gorge_u(x, y) > -3.0 and seg in (7, 8, 9):
            return "bridge"
        if seg in (7, 9, 10):
            return "terrace"
        if seg in (11, 12, 13, 14):
            return "pass"
        if seg in (15, 16, 17):
            return "overlook"
        if seg in (18, 19) and upper_river(x, y) is not None and upper_river(x, y)[0] < 22:
            return "brink"
        if open_from <= s <= sc_a + 22 or open_to_from <= s <= sc_b + 22:
            return "open"
        if seg >= 18:
            return "mesa"
        return "plateau"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k != "plateau":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "plateau", max_len=200.0))

    sc = [(x, y, _short_z(c, x, y)) for x, y in BUTTE_SHORT]
    c.shortcut("Butte Slot", sc, "dash_road", "packed_dirt", width=8.0, shoulder=0.8, shoulder_mat=verge)

    import canyon_scenery  # noqa: E402

    canyon_scenery.build(c, sys.modules[__name__])
    c.finish()


def ruin_course(c, trestle):
    """The ruin's roads and gameplay (canyon_ruins.py builds the land and the wreckage)."""
    S = SEG
    rubble = ("talus", "dirt")
    c.kinds.update({
        # The cuttings through the rockslide, down to the river and back up.
        "slide": {"mat": "dash_road", "shoulder": 1.6, "shoulder_mat": rubble},
        # The rockfall across the river: boulders under a rough deck.
        "causeway": {"mat": "dash_road", "shoulder": 1.0, "shoulder_mat": rubble, "deck": 3.5, "deck_mat": ("strata_red", "wall"),
                     "ground": False},
        # The broken bridge's lip: the deck kicks up at its broken end.
        "kicker": {"mat": "plank_deck", "shoulder": 0.6, "shoulder_mat": ("plank_deck", "road"), "barrier": 1.3,
                   "barrier_mat": ("weathered_timber", "wall"), "deck": 2.2, "deck_mat": ("weathered_timber", "wall"), "ground": False},
    })

    def label(smp):
        s = smp.s
        seg = seg_of(s)
        x, y = smp.p.x, smp.p.y
        if LIP <= s <= LAND:
            return "gap"
        if LIP - 12 <= s < LIP:
            return "kicker"
        if trestle[0] <= s <= trestle[1]:
            return "trestle"
        if seg in (2, 3, 4, 5, 6) or (seg == 7 and s < S[7] + 10):
            return "ledge"
        if gorge_u(x, y) > -3.0 and seg in (7, 8):
            return "bridge"
        if seg in (7, 9, 10):
            return "terrace"
        if seg in (15, 16) and gorge_u(x, y) > 40.0:
            return "causeway"
        if 11 <= seg <= 20:
            return "slide"
        return "plateau"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "kicker":
            specials.append((s0, s1, k, {"lift": lambda u, n: 1.4 * max(0.0, (u - (n - 8)) / 8) ** 2}))
        elif k != "plateau":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "plateau", max_len=200.0))
    ruin_mode.DRESS(c, sys.modules[__name__])
    c.finish()


def ruin_gameplay(c):
    """The ruin's zippers, items, respawn and checkpoints."""
    S = SEG
    for at in (28, S[3] + 20, LIP - 22, S[12] + 20, S[18] + 10, S[21] + 10):
        c.zipper(at, 0)
    for at, across in ((70, 0), (S[4] + 30, 3), (S[9] + 20, 0), (S[14] + 10, 0), (S[18] + 80, 0), (S[22] + 40, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in ((90, -5, "red"), (90, 5, "blue"), (S[3] + 50, 0, "green"), (S[7] + 10, 0, "yellow"), (S[10] + 10, 0, "rainbow"),
                            (S[13] + 20, 0, "blue"), (S[17] + 10, -4, "green"), (S[17] + 10, 4, "red"), (S[19] + 20, 0, "yellow")):
        c.balloon(at, across, col)
    c.entity("respawn", **{"from": round(LIP - 30, 1), "to": round(LAND + 6, 1), "at": round(LAND + 24, 1)})
    c.checkpoints(extra=[S[2] + 10, S[4], S[6] + 10, S[8] + 20, LAND + 30, S[10], S[12] + 40, S[14] + 10, S[17], S[18] + 60, S[19] + 30, S[22] + 20],
                  avoid=[(LIP - 16, LAND + 10)], height=10.0)


def _short_z(c, x, y):
    smp, _ = c.nearest(x, y)
    return smp.p.z


if __name__ == "__main__":
    main()
