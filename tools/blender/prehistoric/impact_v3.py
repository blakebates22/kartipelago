# Impact Depths v3: the GREYBOX of the new lap (Blake's notes, 2026-10-23): down deep.
# Driving first: the new lap, playable with plain shapes, so it can be driven and changed
# quickly; the look comes once the lap is fun. Builds its own package, impact_depths_v3
# (?track=impact_depths_v3); the current Impact Depths stays as it is.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/impact_v3.py      (the bpy module)
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
from course_kit import Vector, bmesh, lerp, smooth  # noqa: E402

TRACK_ID = "impact_depths_v3"

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


def road_z(d, seg):
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


def natural(x, y):
    """The desert, and the pit stepping down in terraces to the lava floor: each
    terrace's ledge at its road's height, a cliff down to the next."""
    r = math.hypot(x, y)
    b = math.atan2(y, x)
    desert = Z_RIM + 1.0 + 0.8 * math.sin(x / 41.0) * math.cos(y / 37.0)
    rings = [(R_RIM, ring_z("rim", b)), (R_T1, ring_z("t1", b)), (R_T2, ring_z("t2", b)), (R_BOT, ring_z("bottom", b))]
    if r >= R_RIM + 14:
        return desert + 6.0 * smooth((r - 420.0) / 120.0)
    z = desert
    for (ra, za), (rb, zb) in zip([(R_RIM + 14, desert)] + rings, rings):
        if rb - 14 < r <= ra:
            # The ledge (14 m inside the road and out to the cliff's foot), then the cliff.
            if r > rb + 14:
                u = (r - (rb + 14)) / max(1.0, (ra - 14) - (rb + 14))
                z = lerp(zb + 1.0, za - 1.5, smooth(min(1.0, max(0.0, u)) ** 0.6))
            else:
                z = zb - 0.5
            return z
    # Inside the bottom ring: the lava lake round the core.
    return Z_BOTTOM - 8.0


def classify(c, n, info):
    if c.z < Z_BOTTOM - 4:
        return ("lava_flow", "lava")
    if n.z < 0.62:
        return ("crater_rock", "wall")
    if math.hypot(c.x, c.y) > R_RIM + 14:
        return ("desert_sand", "loose_sand")
    if info["d"] < 11:
        return ("crater_ground", "dirt")
    return ("crater_ground", "dirt")


def main():
    import props  # noqa: E402

    c = kit.Course(TRACK_ID, "Impact Depths (v3 greybox)", "impact_depths")
    c.route(ROUTE, width=16.0, bank=7.0)
    rock = ("crater_rock", "wall")
    c.kinds = {
        "ledge": {"mat": "crater_road", "shoulder": 1.4, "shoulder_mat": ("crater_ground", "dirt"), "barrier": 1.0, "barrier_mat": rock},
        "rim": {"mat": "depths_road", "surface": "packed_dirt", "shoulder": 2.0, "shoulder_mat": ("desert_sand", "loose_sand")},
        "helix": {"mat": "cave_road", "surface": "road", "shoulder": 0.6, "shoulder_mat": ("crater_ground", "road"), "barrier": 1.3,
                  "barrier_mat": rock, "deck": 2.0, "deck_mat": rock, "ground": False},
        "bridge": {"mat": "bridge_stone", "surface": "road", "shoulder": 0.6, "shoulder_mat": ("bridge_stone", "road"), "barrier": 1.2,
                   "barrier_mat": ("bridge_stone", "wall"), "deck": 3.0, "deck_mat": ("bridge_stone", "wall"), "ground": False},
        "ramp": {"mat": "crater_road", "shoulder": 1.4, "shoulder_mat": ("crater_ground", "dirt"), "barrier": 1.0, "barrier_mat": rock},
    }

    def label(smp):
        s = TO_PLAN(smp.s)
        seg = seg_of(s)
        if GAP[0] <= s <= GAP[1]:
            return "gap"
        if GAP[0] - 10 <= s < GAP[0]:
            return "ramp"
        if seg in (K["helix"], K["exit"]):
            return "helix"
        if seg == K["bridge"]:
            return "bridge"
        if seg == K["rim"]:
            return "rim"
        return "ledge"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "ramp":
            specials.append((s0, s1, "ramp", {"lift": lambda u, n: 0.9 * max(0.0, (u - (n - 8)) / 8) ** 2}))
        elif k != "ledge":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "ledge", max_len=200.0))

    X0, X1, Y0, Y1 = -560, 560, -560, 560
    c.terrain("Land", X0, X1, Y0, Y1, 6.0, natural, classify, near=10.0, fade=14.0, under=0.2)

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
    for at in (S[K["rim"]] + 120, S[K["t1"]] + 30, S[K["t1"]] + 300, S[K["t2"]] + 30, S[K["t2"]] + 200, S[K["bottom"]] + 30, S[K["bridge"]] + 30):
        c.zipper(at, 0)
    for at, across in ((S[K["rim"]] + 250, 0), (S[K["t1"]] + 150, -3), (S[K["t2"]] + 120, 3), (S[K["bottom"]] + 120, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in ((S[K["rim"]] + 60, -4, "red"), (S[K["rim"]] + 60, 4, "blue"), (S[K["t1"]] + 220, 0, "green"), (S[K["t2"]] + 60, 0, "yellow"),
                            (S[K["t2"]] + 300, -4, "rainbow"), (S[K["t2"]] + 300, 4, "red"), (S[K["bottom"]] + 180, 0, "blue")):
        c.balloon(at, across, col)
    g0, g1 = TO_ROAD(GAP[0]), TO_ROAD(GAP[1])
    c.entity("respawn", **{"from": round(g0 - 20, 1), "to": round(g1 + 4, 1), "at": round(g1 + 20, 1)})
    c.checkpoints(extra=[S[HP[0]] + 40, S[K["t1"]] + 200, S[HP[1]] + 40, S[K["t2"]] + 150, S[HP[2]] + 40, S[K["bottom"]] + 120, S[K["link"]] + 30,
                         S[K["bridge"]] + 60], avoid=[(a - 4, b + 4)], height=12.0)

    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish()
    print("lap", round(c.length, 1), "updraft", round(b - a, 1), "m")


if __name__ == "__main__":
    main()
