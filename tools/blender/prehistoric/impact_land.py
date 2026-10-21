# Impact Depths: the land, as plain data and functions (no Blender), shared by the course
# script (impact_depths.py), its scenery modules and the preview tools.
# SPDX-License-Identifier: MIT
#
# Three height fields on one grid make the whole world:
#
#   N  the top natural surface: the desert (with its mesas), the asteroid's crater
#      carved into it, and the Heart Shaft (a round pit with a ramp terrace spiralling up
#      its west wall).
#   Fc the caves' floor, from a set of "tubes": chains of nodes (x, y, radius, floor,
#      height) blended into one another. Inside a tube the floor sits at `floor` and
#      the roof domes up to floor + height; at its edge the floor rises to meet the
#      roof; outside, both turn back into solid rock.
#   C  the caves' roof.
#
# The ground you drive on is min(N, Fc). Where a cave is roofed (the rock above is at
# least ROOF_MIN thick and no skylight is cut there) the roof and the desert above it
# are separate meshes; where it isn't (the crater's floor, the shaft, the skylights) the
# cave simply opens to the sky.

import math

# ---------------------------------------------------------------- the layout (turtle)


def _turtle(segs, start, head, step=1.0):
    x, y = start
    h = head
    pts = [(x, y, h, 0)]
    for i, sg in enumerate(segs):
        if sg[0] == "S":
            n = max(1, int(sg[1] / step))
            for _ in range(n):
                x += math.cos(math.radians(h)) * sg[1] / n
                y += math.sin(math.radians(h)) * sg[1] / n
                pts.append((x, y, h, i))
        else:
            r, deg = sg[1], sg[2]
            sgn = 1 if sg[0] == "L" else -1
            n = max(2, int(r * math.radians(deg) / step))
            for _ in range(n):
                dh = sgn * deg / n
                chord = 2 * r * math.sin(math.radians(abs(dh)) / 2)
                x += math.cos(math.radians(h + dh / 2)) * chord
                y += math.sin(math.radians(h + dh / 2)) * chord
                h += dh
                pts.append((x, y, h, i))
    return pts


def _close(segs, a, b, start, head):
    segs = list(segs)
    for _ in range(40):
        p = _turtle(segs, start, head)
        ex, ey = p[-1][0] - p[0][0], p[-1][1] - p[0][1]
        if math.hypot(ex, ey) < 1e-4:
            break
        ha = next(q[2] for q in p if q[3] == a)
        hb = next(q[2] for q in p if q[3] == b)
        ua = (math.cos(math.radians(ha)), math.sin(math.radians(ha)))
        ub = (math.cos(math.radians(hb)), math.sin(math.radians(hb)))
        det = ua[0] * ub[1] - ua[1] * ub[0]
        segs[a] = ("S", segs[a][1] + (-ex * ub[1] + ey * ub[0]) / det)
        segs[b] = ("S", segs[b][1] + (-ua[0] * ey + ua[1] * ex) / det)
    return segs, _turtle(segs, start, head)


START = (0.0, 0.0)
LAYOUT = [
    ("S", 120),  # 0  1: the desert approach, east, the asteroid smoking ahead (closes the lap)
    ("R", 150, 90),  # 1  2: round the crater's rim...
    ("R", 120, 90),  # 2  ...and down its inner wall, banked
    ("S", 60),  # 3  along the crater floor's edge to the cave mouth
    ("L", 120, 35),  # 4  3: into the Crystal Descent
    ("S", 100),  # 5  the stone bridge over the underground river
    ("R", 120, 35),  # 6  past the blue lake
    ("S", 40),  # 7  a dark passage; the ancient gateway (the shortcut) at its end
    ("L", 130, 40),  # 8  4: the Lost World, the meadow on the left
    ("S", 90),  # 9  raptor crossing
    ("R", 130, 40),  # 10 along the turquoise lake
    ("S", 50),  # 11 the river bridge, the sauropod below
    ("R", 100, 90),  # 12 the corner under the sauropod; a tunnel down
    ("S", 150),  # 13 5: the Volcanic Depths: lava causeways (closes the lap)
    ("R", 100, 90),  # 14 6: the Dragon's Lair, bending round the perch
    ("S", 120),  # 15 the broad bridge over the lava gorge, then the portal
    ("S", 30),  # 16 7: into the Heart of the Earth
    ("R", 60, 180),  # 17 round the core
    ("R", 78, 180),  # 18 8: the spiral ascent up the shaft
    ("L", 150, 25),  # 19 out into the sunlight: the final high-speed curve
    ("R", 150, 25),  # 20
    ("S", 20),  # 21 the line
]
LAYOUT, PATH = _close(LAYOUT, 0, 13, START, 0.0)
_D = [0.0]
for _a, _b in zip(PATH, PATH[1:]):
    _D.append(_D[-1] + math.hypot(_b[0] - _a[0], _b[1] - _a[1]))
LENGTH = _D[-1]
SEG = {}
for _i, _p in enumerate(PATH):
    SEG.setdefault(_p[3], _D[_i])


def seg_of(s):
    k = 0
    for i, d in SEG.items():
        if d <= s:
            k = max(k, i)
    return k


def path_at(s):
    """(x, y, heading degrees) s metres along the lap (wraps)."""
    s %= LENGTH
    lo, hi = 0, len(_D) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if _D[mid] <= s:
            lo = mid
        else:
            hi = mid
    a, b = PATH[lo], PATH[hi]
    t = (s - _D[lo]) / max(1e-9, _D[hi] - _D[lo])
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def side(s, o):
    """The point `o` metres to the right of the centre line, s metres along."""
    x, y, h = path_at(s)
    r = math.radians(h - 90.0)
    return (x + o * math.cos(r), y + o * math.sin(r))


def arc_centre(i):
    k = next(j for j, p in enumerate(PATH) if p[3] == i)
    x, y, h, _ = PATH[k]
    sg = LAYOUT[i]
    a = math.radians(h + (90 if sg[0] == "L" else -90))
    return (x + sg[1] * math.cos(a), y + sg[1] * math.sin(a))


S = SEG

# ---------------------------------------------------------------- helpers


def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v


def sm(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def rnd(k):
    return (math.sin(k * 12.9898 + 78.233) * 43758.5453) % 1


def noise(x, y, f=1.0, seed=0.0):
    """Cheap smooth value-ish noise in about [-1, 1]."""
    x *= f
    y *= f
    return (
        math.sin(x * 1.13 + seed) * math.cos(y * 0.91 - seed * 0.7)
        + 0.5 * math.sin(x * 2.37 - y * 1.71 + seed * 1.9)
        + 0.25 * math.cos(x * 4.11 + y * 3.53 - seed)
    ) / 1.75


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = clamp(((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy + 1e-9))
    return math.hypot(px - ax - t * dx, py - ay - t * dy), t


# ---------------------------------------------------------------- the road's height

Z_DESERT = 30.0
ANCHORS = [
    (0.0, 30.6),
    (S[1] + 60, 31.2),  # along the rim
    (S[1] + 120, 28.0),
    (S[2], 21.0),  # down the inner wall
    (S[3], 9.0),
    (S[4], 4.5),  # the cave mouth
    (S[5], 1.5),
    (S[6], 0.5),  # the stone bridge, near level
    (S[7], -0.5),
    (S[8], -1.5),
    (S[9], -4.5),
    (S[10], -6.5),
    (S[11], -7.5),  # the river bridge
    (S[12], -8.0),
    (S[13], -10.5),
    (S[14], -12.0),
    (S[15], -12.5),  # the dragon bridge
    (S[16], -13.5),
    (S[17], -14.5),  # round the core
    (S[18], -9.0),
    (S[19], 24.5),  # the ascent's top
    (S[20], 29.0),
    (LENGTH, 30.6),
]


def _lin(d):
    d = min(max(d, 0.0), LENGTH)
    for (d0, z0), (d1, z1) in zip(ANCHORS, ANCHORS[1:]):
        if d0 <= d <= d1:
            return lerp(z0, z1, (d - d0) / max(1e-6, d1 - d0))
    return ANCHORS[-1][1]


def road_z(d, seg=None):
    """The road's height d metres along the lap: the anchors, eased over ~24 m."""
    return sum(_lin(d + k) for k in range(-12, 13, 3)) / 9.0


def road_w(d, seg):
    if seg in (0, 21) or d > S[20]:
        return 20.0  # the start: room for the pack
    if seg in (1, 2, 3):
        return 17.0  # the crater's banked descent
    if seg == 7:
        return 14.0  # the passage
    if seg in (15,):
        return 20.0  # the broad dragon bridge
    if seg in (17,):
        return 15.0
    if seg in (18,):
        return 15.0
    return 16.0


# ---------------------------------------------------------------- landmarks

CRATER = (300.0, -170.0)  # the asteroid's crater
CRATER_FLOOR = -12.0
CRATER_R0 = 58.0  # the floor's edge
CRATER_R1 = 166.0  # the top of the inner wall
CRATER_LIP = 196.0  # the raised rim's crest
ASTEROID = (CRATER[0] + 6.0, CRATER[1] + 4.0)
CORE = arc_centre(17)  # the Heart of the Earth's crystal, inside the core ring
RAMP_C = arc_centre(18)  # the ascent's centre
SHAFT = ((CORE[0] + RAMP_C[0]) / 2, (CORE[1] + RAMP_C[1]) / 2 - 2.0)
SHAFT_R = 94.0
CORE_PIT_R = 42.0  # the glowing abyss round the core
CORE_FLOOR = -15.5
PERCH = (-318.0, -118.0)  # the dragon's crag, inside the lair's bend, by the gorge
LAVA_Z = -27.0  # the lair's lava lake
LAKE_BLUE = (176.0, -388.0)  # the Crystal Descent's lake
WATERFALL_CRYSTAL = (112.0, -262.0)
LAKE_JUNGLE = (-176.0, -566.0)
JUNGLE_WATER_Z = -11.0
CRYSTAL_WATER_Z = -7.0
MEADOW = (-34.0, -500.0)


# ---------------------------------------------------------------- the desert


MESAS = [  # (x, y, rx, ry, height above the desert, angle)
    (40.0, 175.0, 70.0, 42.0, 62.0, 0.2),
    (205.0, 215.0, 52.0, 78.0, 84.0, -0.3),
    (-150.0, 135.0, 84.0, 46.0, 48.0, 0.5),
    (470.0, 110.0, 48.0, 60.0, 70.0, 0.9),
    (-330.0, 120.0, 70.0, 52.0, 58.0, -0.6),
    (560.0, -260.0, 70.0, 50.0, 76.0, 0.3),
    (-560.0, -260.0, 60.0, 90.0, 64.0, 0.1),
    (-120.0, -760.0, 110.0, 60.0, 70.0, 0.0),
    (260.0, -560.0, 70.0, 56.0, 58.0, 0.4),
]


def mesa_h(x, y):
    h = 0.0
    for mx, my, rx, ry, top, a in MESAS:
        ca, sa = math.cos(a), math.sin(a)
        u = ((x - mx) * ca + (y - my) * sa) / rx
        v = (-(x - mx) * sa + (y - my) * ca) / ry
        d = math.sqrt(u * u + v * v) + 0.06 * noise(x, y, 0.05, mx)
        if d < 1.35:
            # Sheer sides, a talus skirt, a flat cap; banded ledges.
            k = 1.0 - sm((d - 0.86) / 0.14) if d > 0.86 else 1.0
            skirt = 0.18 * (1.0 - sm((d - 1.0) / 0.35))
            hh = top * max(k, skirt)
            if 0.2 < k < 1.0:
                hh = round(hh / 9.0) * 9.0 * 0.5 + hh * 0.5
            h = max(h, hh)
    return h


def desert(x, y):
    """The desert floor: low dunes and swells round the mesas."""
    z = Z_DESERT + 1.4 * noise(x, y, 0.018, 1.3) + 0.6 * noise(x, y, 0.06, 4.1)
    return z + mesa_h(x, y)


# ---------------------------------------------------------------- the crater


def crater_z(x, y):
    """The crater's own shape: floor, terraced inner wall, raised rim, ejecta beyond.
    None outside its influence."""
    r = math.hypot(x - CRATER[0], y - CRATER[1])
    if r > 290:
        return None
    a = math.atan2(y - CRATER[1], x - CRATER[0])
    r += 6.0 * noise(math.cos(a) * 9, math.sin(a) * 9, 1.0, 2.0)  # a ragged outline
    if r < CRATER_R0:
        return CRATER_FLOOR + 0.6 * noise(x, y, 0.08)
    if r < CRATER_R1:
        t = (r - CRATER_R0) / (CRATER_R1 - CRATER_R0)
        z = lerp(CRATER_FLOOR, Z_DESERT + 1.5, t ** 1.25)
        # Fractured terraces: the wall steps down in slumped layers.
        step = 7.5
        z = lerp(z, math.floor(z / step) * step + step * sm((z % step) / step * 3.0 - 2.0), 0.55)
        return z
    if r < CRATER_LIP:
        return lerp(Z_DESERT + 1.5, Z_DESERT + 5.0, sm((r - CRATER_R1) / (CRATER_LIP - CRATER_R1)))
    return lerp(Z_DESERT + 5.0, Z_DESERT, sm((r - CRATER_LIP) / 90.0))


# ---------------------------------------------------------------- the Heart Shaft


def _nearest_on_seg(i, x, y):
    """Distance from (x, y) to segment i's centre line, and the lap distance there."""
    best = (1e9, 0.0)
    k0 = next(j for j, p in enumerate(PATH) if p[3] == i)
    for j in range(k0, len(PATH), 2):
        p = PATH[j]
        if p[3] != i:
            break
        d = (p[0] - x) ** 2 + (p[1] - y) ** 2
        if d < best[0]:
            best = (d, _D[j])
    return math.sqrt(best[0]), best[1]


def shaft_z(x, y):
    """The shaft: a round pit to the core's level. Up its west wall a terrace carries the
    ascent; inside the core ring the floor falls away into the glowing abyss. None
    outside."""
    r = math.hypot(x - SHAFT[0], y - SHAFT[1])
    if r > SHAFT_R + 18.0:
        return None
    rim = desert(x, y)
    rc = math.hypot(x - CORE[0], y - CORE[1])
    floor = CORE_FLOOR + 0.4 * noise(x, y, 0.1)
    if rc < CORE_PIT_R + 4.0:
        floor = lerp(-46.0, CORE_FLOOR, sm((rc - CORE_PIT_R + 2.0) / 6.0))
    # The wall: sheer from the floor to the desert.
    jag = 3.0 * noise(x, y, 0.09, 7.0)
    wall = lerp(floor, rim, sm((r - (SHAFT_R - 7.0 + jag)) / 8.0))
    # The ascent's terrace, cut into the west wall (segment 18).
    d, s = _nearest_on_seg(18, x, y)
    if d < 40.0 and S[18] + 2.0 < s < S[19] - 2.0:
        rz = road_z(s) - 0.4
        half = 9.0
        if d < half:
            return rz
        out = math.hypot(x - RAMP_C[0], y - RAMP_C[1]) > LAYOUT[18][1]
        if out:
            return max(wall, min(rim, rz + (d - half) * 3.2))
        return max(wall, rz - (d - half) * 4.5)
    return wall


# ---------------------------------------------------------------- the natural top surface


def natural(x, y):
    """N: the top surface before the caves (and before the roads shape it)."""
    z = desert(x, y)
    c = crater_z(x, y)
    if c is not None:
        r = math.hypot(x - CRATER[0], y - CRATER[1])
        z = c if r < CRATER_LIP else max(z, c)
    h = shaft_z(x, y)
    if h is not None:
        z = min(z, h)
    return z


# ---------------------------------------------------------------- the caves


class Tube:
    """A chain of nodes (x, y, radius, floor, height): one cave, blended along."""

    def __init__(self, name, biome, nodes, wall=7.0, rough=1.0):
        self.name = name
        self.biome = biome
        self.nodes = nodes
        self.wall = wall
        self.rough = rough
        xs = [n[0] for n in nodes]
        ys = [n[1] for n in nodes]
        m = max(n[2] for n in nodes) + 40.0
        self.box = (min(xs) - m, max(xs) + m, min(ys) - m, max(ys) + m)

    def query(self, x, y):
        """(inside distance e, floor, height) at (x, y): e > 0 inside."""
        best = None
        ns = self.nodes
        if len(ns) == 1:
            n = ns[0]
            d = math.hypot(x - n[0], y - n[1])
            return n[2] - d, n[3], n[4]
        for a, b in zip(ns, ns[1:]):
            d, t = seg_dist(x, y, a[0], a[1], b[0], b[1])
            r = lerp(a[2], b[2], t)
            e = r - d
            if best is None or e > best[0]:
                best = (e, lerp(a[3], b[3], t), lerp(a[4], b[4], t))
        return best

    def fields(self, x, y):
        """(floor, roof, e) of this cave at (x, y), or None far outside it."""
        bx0, bx1, by0, by1 = self.box
        if not (bx0 < x < bx1 and by0 < y < by1):
            return None
        e, fl, ht = self.query(x, y)
        e += self.rough * (2.5 * noise(x, y, 0.07, len(self.name)) + 1.2 * noise(x, y, 0.19, 3.0))
        if e < -30.0:
            return None
        meet = fl + ht * 0.42  # where floor and roof meet at the edge
        w = self.wall
        if e >= 0:
            f = lerp(meet, fl, sm(e / w) ** 0.8)
            c = lerp(meet, fl + ht, sm(e / (w * 2.6 + ht * 0.6)) ** 0.7)
        else:
            f = meet - e * 6.0
            c = meet + e * 6.0
        return f, c, e


def _road_nodes(s0, s1, step, r, h, off=0.0, dz=0.6):
    out = []
    s = s0
    while s <= s1 + 1e-6:
        x, y = side(s, off)
        out.append((x, y, r, road_z(s) - dz, h))
        s += step
    return out


def _shortcut_layout():
    """The shortcut's centre line: from where the main road turns into the Lost World,
    straight on through the gateway, along the hidden cavern's causeway, and round onto
    the volcanic causeway."""
    x, y, h = path_at(S[8])
    segs = [("S", 70), ("L", 70, 14), ("R", 70, 28), ("L", 70, 14), ("S", 60), ("R", 48, 88)]
    # Close onto segment 13 (x = its line): stretch the straight before the last bend.
    x13 = path_at(S[13] + 20)[0]
    for _ in range(20):
        p = _turtle(segs, (x, y), h)
        err = p[-1][0] - x13
        if abs(err) < 0.01:
            break
        segs[4] = ("S", segs[4][1] + err)
    return [(q[0], q[1]) for q in _turtle(segs, (x, y), h, 2.0)]


SHORTCUT_LINE = _shortcut_layout()
SHORTCUT_END = SHORTCUT_LINE[-1]


def _short_nodes(r, h, every=8):
    out = []
    n = len(SHORTCUT_LINE)
    for i in range(0, n, every):
        x, y = SHORTCUT_LINE[i]
        out.append((x, y, r, shortcut_z(i / (n - 1)) - 0.6, h))
    x, y = SHORTCUT_LINE[-1]
    out.append((x, y, r, shortcut_z(1.0) - 0.6, h))
    return out


def shortcut_z(u):
    """The shortcut's height, u = 0..1 along it: down through the gateway from the main
    road's level, level along the causeway over the black pool, and gently down onto the
    volcanic causeway's level at the merge."""
    a = road_z(S[8])
    _, b = merge_s()
    lvl = -8.4
    if u < 0.2:
        return lerp(a, lvl, sm(u / 0.2))
    if u < 0.78:
        return lvl - 0.6 * (u - 0.2) / 0.58
    return lerp(lvl - 0.6, road_z(b), sm((u - 0.78) / 0.22))


def merge_s():
    """Lap distances where the shortcut leaves and rejoins the main road."""
    x, y = SHORTCUT_END
    best = min(range(len(PATH)), key=lambda j: (PATH[j][0] - x) ** 2 + (PATH[j][1] - y) ** 2 if PATH[j][3] == 13 else 1e18)
    return S[8], _D[best]


def _tubes():
    T = []
    # The crater's cave mouth and the passage down into the Crystal Descent.
    T.append(Tube("Mouth", "crater", _road_nodes(S[3] + 30, S[4] + 70, 10, 12.5, 12.0), wall=5.0, rough=0.6))
    # The Crystal Descent: a great warm-stone hall, the river and the blue lake.
    T.append(Tube("Crystal Hall", "crystal", [
        (226.0, -292.0, 34.0, 0.0, 22.0),
        (166.0, -330.0, 74.0, -6.0, 34.0),
        (92.0, -360.0, 56.0, -3.0, 28.0),
        (40.0, -372.0, 30.0, -1.5, 18.0),
    ], wall=6.0))
    T.append(Tube("Crystal Lake", "crystal", [
        (186.0, -372.0, 46.0, -8.0, 30.0),
        (166.0, -414.0, 40.0, -8.0, 26.0),
    ], wall=6.0))
    T.append(Tube("Falls Grotto", "crystal", [
        (100.0, -268.0, 26.0, -6.0, 30.0),
        (128.0, -310.0, 30.0, -7.0, 30.0),
    ], wall=5.0))
    # The passage to the Lost World, and the ancient gateway's little hall.
    T.append(Tube("Passage", "crystal", _road_nodes(S[6] + 40, S[8] + 10, 10, 13.0, 12.0), wall=5.0, rough=0.7))
    # The Lost World: a vast jungle cavern lit by shafts of sunlight.
    T.append(Tube("Jungle", "jungle", [
        (-22.0, -398.0, 34.0, -3.0, 20.0),
        (-50.0, -470.0, 72.0, -6.0, 36.0),
        (-150.0, -530.0, 92.0, -9.0, 40.0),
        (-262.0, -512.0, 58.0, -10.0, 32.0),
    ], wall=7.0))
    T.append(Tube("Jungle South", "jungle", [
        (-60.0, -560.0, 60.0, -7.0, 34.0),
        (-200.0, -600.0, 60.0, -11.0, 34.0),
    ], wall=7.0))
    # The river's channel out of the jungle, under the bridge, into the dark.
    T.append(Tube("River Gorge", "jungle", [
        (-268.0, -560.0, 26.0, -14.0, 30.0),
        (-318.0, -488.0, 26.0, -14.0, 30.0),
        (-372.0, -470.0, 22.0, -14.0, 22.0),
        (-430.0, -430.0, 20.0, -15.0, 18.0),
    ], wall=5.0))
    # The tunnel down from the Lost World to the Volcanic Depths.
    T.append(Tube("Down Tunnel", "volcanic", _road_nodes(S[12] + 50, S[13] + 20, 10, 14.0, 13.0), wall=5.0, rough=0.7))
    # The Volcanic Depths: black rock, lava rivers, steam.
    T.append(Tube("Volcanic", "volcanic", [
        (-404.0, -372.0, 34.0, -12.0, 22.0),
        (-410.0, -300.0, 58.0, -16.0, 34.0),
        (-392.0, -205.0, 60.0, -16.5, 38.0),
    ], wall=6.0))
    # The Dragon's Lair: the lava lake under the crag, the bend round it, the gorge.
    T.append(Tube("Lair", "lair", [
        (-346.0, -186.0, 66.0, LAVA_Z - 1.0, 54.0),
        (PERCH[0] - 6.0, PERCH[1] + 14.0, 56.0, LAVA_Z - 1.0, 56.0),
    ], wall=8.0))
    T.append(Tube("Lair Bend", "lair", _road_nodes(S[14] - 20, S[15] + 50, 10, 24.0, 22.0), wall=6.0))
    T.append(Tube("Lava Gorge", "lair", [
        (PERCH[0] + 14.0, PERCH[1] + 30.0, 26.0, LAVA_Z - 1.0, 44.0),
        (-282.0, -40.0, 22.0, LAVA_Z - 1.0, 40.0),
        (-276.0, -6.0, 16.0, LAVA_Z + 2.0, 34.0),
    ], wall=5.0))
    # The portal into the Heart Shaft (under the ascent's terrace).
    T.append(Tube("Portal", "core", _road_nodes(S[15] + 40, S[16] + 22, 8, 12.5, 11.0), wall=4.0, rough=0.4))
    # The hidden cavern of the shortcut: the gateway, the still pool and its causeway.
    T.append(Tube("Hidden Gate", "hidden", _short_nodes(10.0, 11.0, 6)[:4], wall=4.0, rough=0.5))
    hid = _short_nodes(14.0, 14.0, 10)
    T.append(Tube("Hidden Cavern", "hidden", [
        (hid[2][0], hid[2][1], 18.0, hid[2][3], 16.0),
        (hid[len(hid) // 2][0], hid[len(hid) // 2][1] - 4.0, 36.0, hid[len(hid) // 2][3] - 4.0, 22.0),
        (hid[-4][0], hid[-4][1], 20.0, hid[-4][3], 16.0),
    ], wall=5.0))
    T.append(Tube("Hidden Way", "hidden", hid, wall=4.0, rough=0.5))
    return T


TUBES = _tubes()

ROOF_MIN = 3.0  # the least rock over a roofed cave
SKYLIGHTS = [  # (x, y, r): holes in the jungle's roof, sunbeams pouring through
    (-70.0, -500.0, 13.0),
    (-150.0, -560.0, 16.0),
    (-232.0, -520.0, 11.0),
    (-110.0, -440.0, 8.0),
]


def cave(x, y):
    """(Fc, C, biome, e) at (x, y): the caves' floor and roof (None if no cave near)."""
    fl = None
    roof = None
    biome = None
    eb = -1e9
    for t in TUBES:
        q = t.fields(x, y)
        if q is None:
            continue
        f, c, e = q
        if fl is None or f < fl:
            fl = f
        if roof is None or c > roof:
            roof = c
        if e > eb:
            eb = e
            biome = t.biome
    if fl is None:
        return None
    return fl, roof, biome, eb


def skylit(x, y):
    for sx, sy, r in SKYLIGHTS:
        if math.hypot(x - sx, y - sy) < r + 1.5 * noise(x, y, 0.3):
            return True
    return False


HIDDEN_WATER_Z = min(shortcut_z(k / 40.0) for k in range(8, 34)) - 2.0
VOLCANIC_LAVA_Z = -17.5


def _poly_dist(x, y, pts):
    best = (1e9, 0.0)
    acc = 0.0
    total = sum(math.dist(a[:2], b[:2]) for a, b in zip(pts, pts[1:]))
    for a, b in zip(pts, pts[1:]):
        d, t = seg_dist(x, y, a[0], a[1], b[0], b[1])
        if d < best[0]:
            best = (d, (acc + t * math.dist(a[:2], b[:2])) / max(1e-9, total))
        acc += math.dist(a[:2], b[:2])
    return best


# The waters: lakes (ellipses) and channels (polylines), each lowering the cave floor
# under it to its bed. ("kind": water or lava; "z": the surface.)
WATERS = [
    {"name": "Blue Lake", "kind": "water", "biome": "crystal", "z": CRYSTAL_WATER_Z, "bed": CRYSTAL_WATER_Z - 3.0,
     "ellipse": (LAKE_BLUE[0], LAKE_BLUE[1], 44.0, 34.0)},
    {"name": "Crystal Stream", "kind": "water", "biome": "crystal", "z": CRYSTAL_WATER_Z, "bed": CRYSTAL_WATER_Z - 2.5,
     "channel": [WATERFALL_CRYSTAL, (126.0, -296.0), (140.0, -322.0), (152.0, -350.0), (LAKE_BLUE[0] - 14, LAKE_BLUE[1] + 18)], "hw": 7.0},
    {"name": "Turquoise Lake", "kind": "water", "biome": "jungle", "z": JUNGLE_WATER_Z, "bed": JUNGLE_WATER_Z - 3.0,
     "ellipse": (LAKE_JUNGLE[0], LAKE_JUNGLE[1], 78.0, 42.0)},
    {"name": "Jungle River", "kind": "water", "biome": "jungle", "z": JUNGLE_WATER_Z - 1.2, "bed": JUNGLE_WATER_Z - 3.6,
     "channel": [(-238.0, -578.0), (-268.0, -556.0), (-296.0, -520.0), (-318.0, -490.0), (-350.0, -474.0), (-380.0, -466.0),
                 (-432.0, -432.0)], "hw": 9.0},
    {"name": "Black Pool", "kind": "water", "biome": "hidden", "z": HIDDEN_WATER_Z, "bed": HIDDEN_WATER_Z - 2.5, "pool": True},
    {"name": "Lava Lake", "kind": "lava", "biome": "lair", "z": LAVA_Z, "bed": LAVA_Z - 1.5, "lair": True},
    {"name": "West Lava River", "kind": "lava", "biome": "volcanic", "z": VOLCANIC_LAVA_Z, "bed": VOLCANIC_LAVA_Z - 2.0,
     "channel": [(-448.0, -398.0), (-438.0, -340.0), (-432.0, -280.0), (-420.0, -246.0), (-396.0, -233.0), (-370.0, -226.0),
                 (-348.0, -212.0), (-330.0, -198.0)], "hw": 8.0},
    {"name": "East Lava River", "kind": "lava", "biome": "volcanic", "z": VOLCANIC_LAVA_Z, "bed": VOLCANIC_LAVA_Z - 2.0,
     "channel": [(-366.0, -384.0), (-366.0, -330.0), (-370.0, -276.0), (-374.0, -240.0)], "hw": 7.0},
]


def in_water(w, x, y, margin=0.0):
    """How deep inside water w the point is (metres; > 0 inside)."""
    if "ellipse" in w:
        cx, cy, rx, ry = w["ellipse"]
        d = math.hypot((x - cx) / rx, (y - cy) / ry)
        return (1.0 - d) * min(rx, ry) + margin
    if "channel" in w:
        d, _ = _poly_dist(x, y, w["channel"])
        return w["hw"] - d + margin
    if w.get("pool"):
        d, u = _poly_dist(x, y, SHORTCUT_LINE)
        if not 0.22 < u < 0.78:
            return -99.0
        return d - 7.5 + margin
    if w.get("lair"):
        return 99.0
    return -99.0


def water_floor(x, y, biome, fl):
    """Lakes, rivers and lava channels lower the cave floor under them."""
    for w in WATERS:
        if w["biome"] != biome or w.get("lair"):
            continue
        e = in_water(w, x, y)
        if e > -6.0:
            fl = min(fl, lerp(fl, w["bed"], sm((e + 6.0) / 9.0)))
    return fl


def ground(x, y):
    """(z, info): the surface you'd stand on before the roads shape it, and what's here:
    info = (biome, covered, roof, top)."""
    n = natural(x, y)
    q = cave(x, y)
    if q is None:
        return n, (None, False, None, n)
    fc, c, biome, e = q
    fc = water_floor(x, y, biome, fc)
    z = min(n, fc)
    c = min(c, n - ROOF_MIN)
    covered = fc < n - 0.05 and n - fc >= 9.0 and not skylit(x, y)
    if fc >= n - 0.05:
        biome = None
    return z, (biome, covered, c, n)


def biome_at(x, y):
    q = cave(x, y)
    if q is None:
        return "crater" if math.hypot(x - CRATER[0], y - CRATER[1]) < CRATER_LIP else ("core" if math.hypot(x - SHAFT[0], y - SHAFT[1]) < SHAFT_R else "desert")
    return q[2] if q[3] > -8 else ("crater" if math.hypot(x - CRATER[0], y - CRATER[1]) < CRATER_LIP else "desert")


# The biomes along the lap (for the road's surface, the sounds and the air).
ZONES = [
    (0.0, "desert"),
    (S[1] - 20, "crater"),
    (S[4] + 40, "crystal"),
    (S[8] + 10, "jungle"),
    (S[12] + 60, "volcanic"),
    (S[14] - 30, "lair"),
    (S[16] - 10, "core"),
    (S[18] + 140, "ascent"),
    (S[19] + 10, "desert"),
]


def zone_of(s):
    z = ZONES[0][1]
    for d, name in ZONES:
        if s >= d:
            z = name
    return z


def ribbon_path(w):
    """A channel's centre line as (x, y, width, z) points every ~4 m (for its ribbon)."""
    pts = w["channel"]
    z = w["z"]
    out = []
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(math.dist(a, b) / 4.0))
        for k in range(n):
            t = k / n
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, w["hw"] * 1.6, z))
    out.append((pts[-1][0], pts[-1][1], w["hw"] * 1.6, z))
    return out



GRID = (-540.0, 540.0, -720.0, 180.0)  # the land's extent (x0, x1, y0, y1)
CELL = 6.0
