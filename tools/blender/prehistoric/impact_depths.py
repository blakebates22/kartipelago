# Impact Depths: the new lap (v3, Blake's notes, 2026-10-23): down deep. Greyboxed
# first for driving, then dressed (impact_depths_dress.py); it replaced the first lap
# in the Desert World on 2026-10-24, which is kept as impact_depths_v2 (impact_depths_v2.py,
# ?track=impact_depths_v2).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/impact_depths.py      (the bpy module)
#
# The asteroid's crater has broken open a great pit, and the lap goes all the way down
# it: about 2.3 km, 118 m from the rim to the bottom.
#
#   A  The rim: the start on the desert at the pit's edge, sweeping round it.
#   B  Terrace one (the crystal wall): a hairpin over the edge and back round the pit's
#      wall the other way, weaving, ducking into the rock.
#   C  Terrace two (the jungle ledge): another hairpin, round the other way again, a
#      jump over a crevasse.
#   D  The bottom (the lava ring): a last hairpin down to the ring round the core, over
#      the crests between the lava.
#   E  The updraft: into the roaring column of wind beside the core, which shoots you up
#      the corkscrew to the top in about 7 s, and out along the bridge across the pit
#      to the rim and the line.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import ruin_mode  # noqa: E402
from course_kit import Vector, bmesh, lerp, smooth  # noqa: E402

# The ruin (impact_depths_ruins.py): much of the cave's roof has come down. The same lap,
# but the terraces' roads are broken where the roof fell through them (a run of jumps on
# the way down), the sky shows through great holes, and rock keeps falling from their
# edges (a shadow on the road first). Everything else is the course's own.
RUIN = ruin_mode.ON
TRACK_ID = "impact_depths_ruin" if RUIN else "impact_depths"

# ---------------------------------------------------------------- the layout
#
# Built straight from the pit's geometry (its centre at the origin): the terraces are
# arcs round it (radius gently weaving: sweeping S-bends), joined by hairpins; the
# updraft is a corkscrew round the core's pillar; the bridge runs straight out to the
# rim. PATH: (x, y, heading, segment) every metre or so, like the kit's turtle.

R_RIM, R_T1, R_T2, R_BOT = 240.0, 190.0, 140.0, 90.0
R_HELIX = 24.0
TH_B = -90.0  # the bridge's bearing (and the start's)
TERRACES = [
    # (segment kind, radius, from bearing, to bearing, weave amplitude, weave count)
    ("rim", R_RIM, TH_B + 12.0, 10.0, 10.0, 6),
    ("t1", R_T1, 10.0, -140.0, 12.0, 7),
    ("t2", R_T2, -140.0, 10.0, 10.0, 8),
    ("bottom", R_BOT, 10.0, -140.0, 7.0, 6),
]


def _arc(r, a0, a1, amp, n, step=1.0):
    """Points round the pit at radius r (weaving by amp, n times round a full turn) from
    bearing a0 to a1 (degrees)."""
    out = []
    span = math.radians(a1 - a0)
    k = max(8, int(abs(span) * r / step))
    for i in range(k + 1):
        t = i / k
        a = math.radians(a0) + span * t
        # The weave fades in and out at the ends (so the hairpins meet the true radius).
        w = amp * math.sin(n * (a - math.radians(a0))) * min(1.0, 6 * t, 6 * (1 - t))
        out.append(((r + w) * math.cos(a), (r + w) * math.sin(a)))
    return out


def _hairpin(r1, r2, a, step=1.0):
    """A half circle at bearing a from radius r1 to r2 (it bulges in the direction you
    were going)."""
    rc = (r1 + r2) / 2
    hr = abs(r1 - r2) / 2
    cx, cy = rc * math.cos(math.radians(a)), rc * math.sin(math.radians(a))
    ux, uy = math.cos(math.radians(a)), math.sin(math.radians(a))  # radial out
    tx, ty = -uy, ux  # tangent (anticlockwise)
    return ux, uy, tx, ty, cx, cy, hr


def build_path():
    segs = []  # lists of (x, y)
    kinds = []
    for k, (kind, r, a0, a1, amp, n) in enumerate(TERRACES):
        segs.append(_arc(r, a0, a1, amp, n))
        kinds.append(kind)
        if k + 1 < len(TERRACES):
            r2 = TERRACES[k + 1][1]
            ux, uy, tx, ty, cx, cy, hr = _hairpin(r, r2, a1)
            # Going anticlockwise (a1 > a0) the hairpin bulges anticlockwise.
            sgn = 1.0 if a1 > a0 else -1.0
            pts = []
            m = max(12, int(math.pi * hr))
            for i in range(m + 1):
                t = i / m * math.pi
                # From radius r (outer) round to r2 (inner).
                o = hr * math.cos(t)
                f = hr * math.sin(t)
                pts.append((cx + ux * o + tx * f * sgn, cy + uy * o + ty * f * sgn))
            segs.append(pts)
            kinds.append("hairpin")
    # The link from the bottom ring in towards the updraft: off the ring (heading
    # clockwise at bearing -140), a right turn towards the centre, onto the corkscrew.
    end = segs[-1][-1]
    a = math.atan2(end[1], end[0])
    # Spiral in from the ring's radius to the helix's over 70 degrees of bearing.
    link = []
    m = 80
    for i in range(1, m + 1):
        t = i / m
        rr = lerp(R_BOT, R_HELIX, smooth(t))
        aa = a - math.radians(70.0) * t
        link.append((rr * math.cos(aa), rr * math.sin(aa)))
    segs.append(link)
    kinds.append("link")
    # The corkscrew: clockwise (the way the link turns), 1.4 turns, from its bearing.
    a0 = a - math.radians(70.0)
    turns = 1.4
    # End it so its exit, turning off it, points along the bridge's bearing.
    helix = []
    m = int(turns * 2 * math.pi * R_HELIX)
    for i in range(1, m + 1):
        t = i / m
        aa = a0 - turns * 2 * math.pi * t
        helix.append((R_HELIX * math.cos(aa), R_HELIX * math.sin(aa)))
    segs.append(helix)
    kinds.append("helix")
    # Off the top: a curve out onto the bridge's line, and the bridge to the rim.
    hx, hy = helix[-1]
    bx, by = math.cos(math.radians(TH_B)), math.sin(math.radians(TH_B))
    p0 = Vector((hx, hy, 0))
    # Tangent at the helix's end (clockwise).
    aa = a0 - turns * 2 * math.pi
    t0 = Vector((math.sin(aa), -math.cos(aa), 0))
    q = Vector((bx, by, 0)) * (R_HELIX + 70.0)
    tq = Vector((bx, by, 0))
    curve = []
    m = 90
    L0 = (q - p0).length
    for i in range(1, m + 1):
        t = i / m
        h00, h10, h01, h11 = 2 * t**3 - 3 * t**2 + 1, t**3 - 2 * t**2 + t, -2 * t**3 + 3 * t**2, t**3 - t**2
        p = p0 * h00 + t0 * (L0 * h10) + q * h01 + tq * (L0 * h11)
        curve.append((p.x, p.y))
    segs.append(curve)
    kinds.append("exit")
    # The bridge: out across the pit along its bearing, curving left at the far end onto
    # the rim (where the lap starts).
    r0 = R_HELIX + 70.0
    a_rim = math.radians(TH_B + 12.0)
    p1 = Vector((R_RIM * math.cos(a_rim), R_RIM * math.sin(a_rim), 0))
    t1 = Vector((-math.sin(a_rim), math.cos(a_rim), 0))
    p0 = Vector((bx, by, 0)) * r0
    L1 = (p1 - p0).length
    bridge = []
    m = int(L1)
    for i in range(1, m):
        t = i / m
        h00, h10, h01, h11 = 2 * t**3 - 3 * t**2 + 1, t**3 - 2 * t**2 + t, -2 * t**3 + 3 * t**2, t**3 - t**2
        p = p0 * h00 + tq * (L1 * 0.9 * h10) + p1 * h01 + t1 * (L1 * 0.6 * h11)
        bridge.append((p.x, p.y))
    segs.append(bridge)
    kinds.append("bridge")
    # Into PATH, the rim first (the start is where the bridge lands on the rim).
    order = list(range(len(segs)))
    pts = []
    for si in order:
        for x, y in segs[si]:
            if pts and math.hypot(x - pts[-1][0], y - pts[-1][1]) < 0.3:
                continue
            pts.append((x, y, si))
    path = []
    for i, (x, y, si) in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        h = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        path.append((x, y, h, si))
    return path, kinds


PATH, KINDS = build_path()
SEG = kit.segment_starts(PATH)
_D = [0.0]
for _a, _b in zip(PATH, PATH[1:]):
    _D.append(_D[-1] + math.hypot(_b[0] - _a[0], _b[1] - _a[1]))
LENGTH = _D[-1] + math.hypot(PATH[0][0] - PATH[-1][0], PATH[0][1] - PATH[-1][1])
K = {k: i for i, k in enumerate(KINDS) if k != "hairpin"}
HP = [i for i, k in enumerate(KINDS) if k == "hairpin"]


def seg_of(s):
    k = 0
    for i, d in SEG.items():
        if d <= s:
            k = max(k, i)
    return k


# ---------------------------------------------------------------- heights

Z_RIM = 30.0
Z_BOTTOM = -86.0
Z_TOP = 32.0
# Heights at segment starts (and the end of the lap); between them the road eases.
HEIGHT = {
    K["rim"]: Z_RIM, HP[0]: 26.0, K["t1"]: 14.0, HP[1]: -22.0, K["t2"]: -32.0, HP[2]: -60.0, K["bottom"]: -68.0,
    K["link"]: -84.0, K["helix"]: Z_BOTTOM, K["exit"]: Z_TOP, K["bridge"]: Z_TOP,
}
# The crevasse jump on terrace two: (lip, landing).
GAP = (SEG[K["t2"]] + 230.0, SEG[K["t2"]] + 241.0)
CRESTS = {K["rim"]: (3, 1.6), K["t1"]: (4, 1.4), K["bottom"]: (4, 1.8)}
# (The ruin) where the fallen roof broke the terraces' roads: (lip, landing) in the
# plan's distances, the course's own crevasse among them.
BREAKS = []
HOLES = []  # (the ruin) [(x, y, ux, uy, z)]: each break's middle, the road's way there, its height
if RUIN:
    BREAKS = sorted([GAP] + [(SEG[K[k]] + at, SEG[K[k]] + at + 11.0) for k, at in (("rim", 190.0), ("t1", 180.0), ("t1", 380.0),
                                                                                    ("t2", 100.0), ("bottom", 150.0))])


def _break_z(d, seg):
    """(The ruin) the road over one of the breaks, else None: a kicker up to the lip, the
    landing well below it."""
    for g0, g1 in BREAKS:
        if g0 - 14 <= d <= g1 + 16:
            z_lip = _base(g0 - 14, seg) + 0.6
            if d <= g0:
                return lerp(_base(g0 - 14, seg), z_lip + 0.4, (d - (g0 - 14)) / 14)
            if d <= g1:
                return lerp(z_lip + 0.4, z_lip - 2.0, (d - g0) / (g1 - g0))
            return lerp(z_lip - 2.0, _base(g1 + 16, seg), smooth((d - g1) / 16))
    return None


def road_z(d, seg):
    if BREAKS:
        z = _break_z(d, seg)
        if z is not None:
            return z
    if seg == K["t2"] and GAP[0] - 14 <= d <= GAP[1] + 14:
        z_lip = _base(GAP[0] - 14, seg) + 0.6
        if d <= GAP[0]:
            return lerp(_base(GAP[0] - 14, seg), z_lip + 0.4, (d - (GAP[0] - 14)) / 14)
        if d <= GAP[1]:
            return lerp(z_lip + 0.4, z_lip - 1.2, (d - GAP[0]) / (GAP[1] - GAP[0]))
        return lerp(z_lip - 1.2, _base(GAP[1] + 14, seg), (d - GAP[1]) / 14)
    z = _base(d, seg)
    if seg in CRESTS:
        a, b = SEG[seg], SEG.get(seg + 1, LENGTH)
        t = (d - a) / max(1e-6, b - a)
        n, h = CRESTS[seg]
        z += h * math.sin(t * math.pi * n) ** 2
    return z


def _base(d, seg):
    a, b = SEG[seg], SEG.get(seg + 1, LENGTH)
    t = (d - a) / max(1e-6, b - a)
    z0 = HEIGHT[seg]
    z1 = HEIGHT.get(seg + 1, Z_RIM)
    if seg == K["bridge"]:
        return lerp(Z_TOP, Z_RIM, smooth(t))
    if seg == K["helix"]:
        return lerp(z0, z1, t)  # the corkscrew climbs steadily
    return lerp(z0, z1, smooth(t) if seg in HP else t)


def road_w(d, seg):
    if seg == K["helix"]:
        return 14.0
    if seg == K["bridge"]:
        return 14.0
    if seg in HP:
        return 17.0
    return 16.0


ROUTE = kit.route_points_by(PATH, road_z, every=6.0, width=road_w)
if RUIN:
    for _g0, _g1 in BREAKS:
        _m = (_g0 + _g1) / 2
        _i = min(range(len(PATH)), key=lambda i: abs(_D[i] - _m))
        _h = math.radians(PATH[_i][2])
        HOLES.append((PATH[_i][0], PATH[_i][1], math.cos(_h), math.sin(_h), road_z(_g0, seg_of(_g0))))
# The plan's distances (SEG, GAP) are flat; the course measures along the road, which
# is longer down the hairpins and up the corkscrew.
TO_ROAD, TO_PLAN = kit.along(PATH, road_z)

# ---------------------------------------------------------------- the land


def ring_z(kind, bearing):
    """The height of a terrace's road at a bearing (radians), roughly (for the walls)."""
    _, r, a0, a1, _, _ = next(t for t in TERRACES if t[0] == kind)
    seg = K[kind]
    a = math.degrees(bearing)
    # The bearing along the terrace, unwrapped towards its range.
    lo, hi = min(a0, a1), max(a0, a1)
    while a < lo - 180:
        a += 360
    while a > hi + 180:
        a -= 360
    t = max(0.0, min(1.0, (a - a0) / (a1 - a0)))
    return lerp(HEIGHT[seg], HEIGHT[seg + 1], t)


def ring_r(kind, bearing):
    """A terrace road's radius at a bearing (radians): its ring, weaving like _arc."""
    _, r, a0, a1, amp, n = next(t for t in TERRACES if t[0] == kind)
    a = math.degrees(bearing)
    lo, hi = min(a0, a1), max(a0, a1)
    while a < lo - 180:
        a += 360
    while a > hi + 180:
        a -= 360
    t = max(0.0, min(1.0, (a - a0) / (a1 - a0)))
    w = amp * math.sin(n * math.radians(a - a0)) * min(1.0, 6 * t, 6 * (1 - t))
    return r + w


# The cave over the pit: its roof, the desert above it, and where the crater broke
# through (the crack the sunlight pours in by) and a few smaller holes over the jungle.
Z_DESERT = 112.0
R_CAVE = 300.0


def roof_z(x, y):
    r = math.hypot(x, y)
    return 96.0 - 34.0 * (r / 290.0) ** 2 + 3.0 * math.sin(x / 23.0) * math.cos(y / 19.0) + 1.5 * math.sin((x - y) / 11.0)


# The crack: a jagged rift across the roof, from over the rim (by the start) across the
# pit towards the far side, widest over the core.
CRACK = [(-30.0, -262.0, 10.0), (-20.0, -200.0, 22.0), (-6.0, -120.0, 34.0), (6.0, -40.0, 40.0), (18.0, 30.0, 30.0),
         (40.0, 100.0, 18.0), (70.0, 150.0, 8.0)]
SKYLIGHTS = [(140.0 * math.cos(math.radians(a)), 140.0 * math.sin(math.radians(a)), rr)
             for a, rr in ((-105.0, 9.0), (-40.0, 12.0), (-10.0, 7.0), (160.0, 10.0))]


def _seg_d(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy + 1e-9)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy), t


if RUIN:
    # Where the roof came down: great holes over the terraces (and the ones already
    # there, wider).
    SKYLIGHTS = [(x, y, r * 1.8) for x, y, r in SKYLIGHTS] + [
        (150.0 * math.cos(math.radians(a)), 150.0 * math.sin(math.radians(a)), rr) for a, rr in ((-62.0, 46.0), (38.0, 40.0), (118.0, 34.0), (172.0, 50.0))]


def opening(x, y):
    """How far inside an opening in the roof (x, y) is, metres (negative: outside)."""
    best = -1e9
    jag = 4.0 * math.sin(x / 5.3 + y / 7.1) + 2.5 * math.sin(x / 2.9 - y / 3.7)
    for a, b in zip(CRACK, CRACK[1:]):
        d, t = _seg_d(x, y, a[0], a[1], b[0], b[1])
        best = max(best, lerp(a[2], b[2], t) / 2 - d + jag)
    for sx, sy, rr in SKYLIGHTS:
        best = max(best, rr - math.hypot(x - sx, y - sy) + 0.4 * jag)
    return best


def zone(x, y):
    """Which world a point is in, by how far down the pit it is."""
    r = math.hypot(x, y)
    if r > (R_RIM + R_T1) / 2:
        return "crater"
    if r > (R_T1 + R_T2) / 2:
        return "crystal"
    if r > (R_T2 + R_BOT) / 2:
        return "jungle"
    if r > R_HELIX + 18:
        return "volcanic"
    return "core"


RINGS = ["rim", "t1", "t2", "bottom"]


def _shape(x, y):
    """(height, crack): the land, and the floor of a crack at the foot of a cliff (or
    None). Each terrace is a ledge at its road's height. Off its inner side, a cliff
    drops to the next terrace down, and at that cliff's foot, just off the lower road,
    a crack down into the glow: fall off a ledge and you land in one, and you're put
    back on the road (no rails to catch on, nowhere to be stranded)."""
    r = math.hypot(x, y)
    b = math.atan2(y, x)
    desert = Z_RIM + 1.0 + 0.8 * math.sin(x / 41.0) * math.cos(y / 37.0)
    rr = [ring_r(k, b) for k in RINGS]
    zz = [ring_z(k, b) for k in RINGS]
    if r >= rr[0] + 14:
        # The cave's outer wall, up into the roof.
        u = (r - rr[0] - 14) / 34.0
        return lerp(desert, roof_z(x, y) + 4.0, smooth(min(1.0, max(0.0, u)) ** 0.8)), None
    if r >= rr[0] - 12.0:
        return zz[0] - 0.5, None
    for k in range(3):
        ra, za, rb, zb = rr[k], zz[k], rr[k + 1], zz[k + 1]
        if r < rb - 12.0:
            continue
        e_hi = ra - (12.0 if ra - rb > 40 else 10.5)
        # More room off the lower road's outside near its hairpins (where you swing wide).
        lo_kind = TERRACES[k + 1]
        near_pin = min(_bdist(b, lo_kind[2]), _bdist(b, lo_kind[3]))
        e_lo = rb + 12.0 + 7.0 * (1.0 - smooth(min(1.0, max(0.0, (near_pin - 18.0) / 22.0))))
        if lo_kind[0] == "t2":
            # And after the crevasse jump's landing, where you come down fast and wide.
            k_land = 1.0 - smooth(min(1.0, max(0.0, (_bdist(b, LANDING_B + 14.0) - 16.0) / 14.0)))
            e_lo = max(e_lo, rb + 12.0 + 14.0 * k_land)
        if r >= e_hi:
            return za - 0.5, None
        if r <= e_lo:
            return zb - 0.5, None
        # (From here out to the upper ledge: below the lower road, you're put back.)
        span = e_hi - e_lo
        # (Where two terraces weave close, the crack takes nearly all the room and the
        # cliff stands sheer.)
        tw = min(9.0, max(min(4.0, span - 0.8), 0.5 * span))
        zf = zb - 18.0
        if r < e_lo + tw:
            u = (r - e_lo) / tw
            # A steep lip down, the floor, and up into the cliff.
            z = zf + (zb - 0.5 - zf) * (1.0 - smooth(min(1.0, u / 0.25)))
            return z, zb
        u = (r - e_lo - tw) / max(1.0, span - tw)
        return lerp(zf, za - 1.5, smooth(min(1.0, u)) ** 0.6), zb
    if r >= rr[3] - 14:
        return zz[3] - 0.5, None
    # Inside the bottom ring: the lava lake round the core.
    return Z_BOTTOM - 8.0, None


# The bearing (degrees) round the pit of the crevasse jump's landing on terrace two.
LANDING_B = TERRACES[2][2] + math.degrees((GAP[1] - SEG[K["t2"]]) / R_T2)


def _bdist(b, deg):
    """Degrees between bearing b (radians) and a bearing in degrees."""
    return abs((math.degrees(b) - deg + 180.0) % 360.0 - 180.0)


def natural(x, y):
    h = _shape(x, y)[0]
    hb = in_break(x, y)
    if hb is not None:
        h = min(h, hb - 24.0)  # (the ruin) down through the broken ledge
    return h


def in_break(x, y):
    """(The ruin) the road's height at a break whose hole (x, y) is over, else None."""
    for hx, hy, ux, uy, z in HOLES:
        dx, dy = x - hx, y - hy
        along, across = dx * ux + dy * uy, -dx * uy + dy * ux
        if (along / 6.5) ** 2 + (across / 15.0) ** 2 < 1.0:
            return z
    return None


def crack_floor(x, y):
    """In a crack (between a lower road and the cliff up to the next ledge): the lower
    road's height there (anything well below it puts you back), else None."""
    return _shape(x, y)[1]


LAND = {
    "crater": ("crater_rock", "crater_ground"),
    "crystal": ("cave_ochre", "flowstone"),
    "jungle": ("moss_rock", "fern_floor"),
    "volcanic": ("black_rock", "lava_crust"),
    "core": ("black_rock", "lava_crust"),
}


def classify(c, n, info):
    if c.z < Z_BOTTOM - 4:
        return ("lava_flow", "lava")
    hb = in_break(c.x, c.y)
    if hb is not None and c.z < hb - 5.0:
        # Down through a break in the ledge, the glow far below: put back on the road.
        return ("lava_flow" if c.z < hb - 16.0 else "black_rock", "lava")
    zb = crack_floor(c.x, c.y)
    smp = info["sample"]
    if zb is not None and c.z < min(zb, smp.p.z) - 4.0 and info["d"] > smp.w / 2 + 3.0:
        # Down in a crack (its floor glowing, its walls dark), well below the road beside
        # it: put back on the road.
        return ("lava_flow" if c.z < zb - 12.0 else "black_rock", "lava")
    rock, floor = LAND[zone(c.x, c.y)]
    if n.z < 0.62:
        return (rock, "wall")
    if math.hypot(c.x, c.y) > R_RIM + 30:
        return (rock, "wall")
    if info["d"] < info["sample"].w / 2 + 1.5:
        return ("crater_ground" if rock == "crater_rock" else floor, "dirt")
    if zone(c.x, c.y) == "jungle":
        return (floor, "grass")
    if zone(c.x, c.y) == "crater":
        g = math.sin(c.x / 9.0) * math.cos(c.y / 11.0) + 0.6 * math.sin((c.x + c.y) / 7.0)
        return ("impact_glass" if g > 0.9 else floor, "loose_sand")
    return (floor, "dirt")


def main():
    import props  # noqa: E402

    c = kit.Course(TRACK_ID, "Impact Depths (Ruined)" if RUIN else "Impact Depths", "impact_ruins" if RUIN else "impact_depths")
    c.route(ROUTE, width=16.0, bank=7.0)
    rock = ("crater_rock", "wall")
    # No rails on the terraces (karts hopped them and were stranded): off the edge is a
    # crack, and you're put back. The bridge and the corkscrew keep theirs.
    c.kinds = {
        "crater": {"mat": "crater_road", "shoulder": 1.6, "shoulder_mat": ("crater_ground", "dirt")},
        "crystal": {"mat": "cave_road", "shoulder": 1.6, "shoulder_mat": ("flowstone", "dirt")},
        "jungle": {"mat": "jungle_track", "surface": "packed_dirt", "shoulder": 1.8, "shoulder_mat": ("fern_floor", "grass")},
        "volcanic": {"mat": "basalt_slab", "shoulder": 1.5, "shoulder_mat": ("lava_crust", "dirt")},
        "helix": {"mat": "core_road", "surface": "road", "shoulder": 0.6, "shoulder_mat": ("core_glass", "road"), "barrier": 1.3,
                  "barrier_mat": ("core_glass", "wall"), "deck": 2.0, "deck_mat": ("black_rock", "wall"), "ground": False},
        "bridge": {"mat": "bridge_stone", "surface": "road", "shoulder": 0.6, "shoulder_mat": ("bridge_stone", "road"), "barrier": 1.2,
                   "barrier_mat": ("bridge_stone", "wall"), "deck": 3.0, "deck_mat": ("bridge_stone", "wall"), "ground": False},
        "ramp": {"mat": "jungle_track", "surface": "packed_dirt", "shoulder": 1.8, "shoulder_mat": ("fern_floor", "grass")},
    }
    world = {K["rim"]: "crater", HP[0]: "crystal", K["t1"]: "crystal", HP[1]: "jungle", K["t2"]: "jungle", HP[2]: "volcanic",
             K["bottom"]: "volcanic", K["link"]: "volcanic"}

    def label(smp):
        s = TO_PLAN(smp.s)
        seg = seg_of(s)
        if any(g0 <= s <= g1 for g0, g1 in BREAKS or [GAP]):
            return "gap"
        if any(g0 - 10 <= s < g0 for g0, g1 in BREAKS or [GAP]):
            return "ramp"
        if seg in (K["helix"], K["exit"]):
            return "helix"
        if seg == K["bridge"]:
            # Onto the rim at the end: the rim's own road, so the start is on dirt.
            return "crater" if s > LENGTH - 30 else "bridge"
        return world.get(seg, "crater")

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "ramp":
            # (The ruin's kickers lift harder: the AI fell short of the roof's breaks.)
            lift = 1.3 if RUIN else 0.9
            specials.append((s0, s1, "ramp", {"lift": lambda u, n, lift=lift: lift * max(0.0, (u - (n - 8)) / 8) ** 2}))
        elif k != "crater":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "crater", max_len=200.0))

    X0, X1, Y0, Y1 = -560, 560, -560, 560
    ter = c.terrain("Land", X0, X1, Y0, Y1, 6.0, natural, classify, near=10.0, fade=14.0, under=0.2, fine=3)

    def under(x, y):
        return natural(x, y) - 0.4

    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 6.0, under, c.lib("crater_ground", "dirt"))

    # The core: a pillar of glowing crystal in the lava, the updraft's corkscrew round it.
    bm = bmesh.new()
    props.loft(bm, [props.ring(bm, (0.0, 0.0), 14.0, Z_BOTTOM - 10, 10), props.ring(bm, (0.0, 0.0), 11.0, Z_TOP - 6, 10),
                    props.ring(bm, (0.0, 0.0), 2.0, Z_TOP + 12, 10)], cap_top=True, cap_bottom=True)
    core = c.mesh_object("Core Pillar", bm, "Rocks")
    c.assign(core, c.lib("core_crystal", "wall"))

    c.start_line()
    S = {k: TO_ROAD(v) for k, v in SEG.items()}
    # The updraft: a ride up the corkscrew (src/game/loops.ts), in at its foot and out
    # at the top, carried the whole way at about 34 m/s (about 7 s).
    a, b = TO_ROAD(SEG[K["helix"]]), TO_ROAD(SEG[K["exit"]] + 12)
    ride = []
    s = a
    while s < b:
        q = c.at(s)
        ride.append([round(v, 2) for v in c.game(q.p.x, q.p.y, q.p.z)] + [round(q.bank, 2)])
        s += 1.5
    q = c.at(b)
    ride.append([round(v, 2) for v in c.game(q.p.x, q.p.y, q.p.z)] + [round(q.bank, 2)])
    c.entity("ride", id="updraft", points=ride, width=14.0, minSpeed=34.0, outSpeed=26.0, commit=0.0, boostMult=1.6,
             boostSec=round((b - a - 40.0) / 34.0, 1), gravity=0.0)
    # Zippers: along the rim, down each hairpin's exit, along the bottom, and across the
    # bridge.
    for at in (S[K["rim"]] + 120, S[K["t1"]] + 30, S[K["t1"]] + 300, S[K["t2"]] + 30, S[K["t2"]] + 300, S[K["bottom"]] + 30, S[K["bridge"]] + 30):
        c.zipper(at, 0)
    # (The ruin) a zipper into every break the roof made (the crevasse has its own).
    for gp0, _gp1 in BREAKS:
        if (gp0, _gp1) != GAP:
            c.zipper(TO_ROAD(gp0) - 22.0, 0)
    for at, across in ((S[K["rim"]] + 250, 0), (S[K["t1"]] + 150, -3), (S[K["t2"]] + 120, 3), (S[K["bottom"]] + 120, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in ((S[K["rim"]] + 60, -4, "red"), (S[K["rim"]] + 60, 4, "blue"), (S[K["t1"]] + 220, 0, "green"), (S[K["t2"]] + 60, 0, "yellow"),
                            (S[K["t2"]] + 300, -4, "rainbow"), (S[K["t2"]] + 300, 4, "red"), (S[K["bottom"]] + 180, 0, "blue")):
        c.balloon(at, across, col)
    for gp0, gp1 in BREAKS or [GAP]:
        g0, g1 = TO_ROAD(gp0), TO_ROAD(gp1)
        c.entity("respawn", **{"from": round(g0 - 20, 1), "to": round(g1 + 4, 1), "at": round(g1 + 20, 1)})
    c.checkpoints(extra=[S[HP[0]] + 40, S[K["t1"]] + 200, S[HP[1]] + 40, S[K["t2"]] + 150, S[HP[2]] + 40, S[K["bottom"]] + 120, S[K["link"]] + 30,
                         S[K["bridge"]] + 60], avoid=[(a - 4, b + 4)], height=12.0)

    import impact_depths_dress  # noqa: E402

    d = impact_depths_dress.build(c, sys.modules[__name__], ter)
    if RUIN:
        ruin_mode.DRESS(c, sys.modules[__name__], d)
    c.finish()
    print("lap", round(c.length, 1), "updraft", round(b - a, 1), "m")


if __name__ == "__main__":
    main()
