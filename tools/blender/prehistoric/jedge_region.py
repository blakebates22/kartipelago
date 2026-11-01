# The last journey: Tropic Isles to the Dragon Kingdom, v2 (Blake, Oct 31: "tunnel through
# smugglers underground layer, to 'edge of the world' to sky bridge to dragon island";
# "having a below ground tunnel could offer a crazy new immersive environment with 'tunnel
# people'"). Builds journey_cause (it replaces Tidewyrm's Causeway, jcause_layout.py, kept
# unused).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/jedge_region.py
#
# The story's last smugglers' tunnel ("THE ONE UNDER THE BORDER"), driven:
#
#   the Underground    in from the isles' sea door under the seabed: lantern-lit bores,
#     the Wreck Hall   a cavern with old ships' hulls set in its walls, then
#     the Sump         (v3, Blake: "the tunnel to descend leading to a massive underground
#                      trade hub of scum and villainy"; the Sump, loot from the kingdoms,
#                      Tortuga, a crime boss) a vast pit under the seabed, the road spiralling
#                      down its wall like a haul road past shacks and taverns stacked on its
#                      ledges, rope bridges and cranes across it, to the black-water harbour
#                      and the loot market on its floor; the Broker's gilded ship hanging
#                      over it all on chains; the Eye, a hole to the sea, high overhead;
#     the Long Bore    out of the Sump's foot and on under the reef, to come out through
#   the Edge           the very cliff of the world's edge, the sea pouring off the rim over
#                      you into the clouds, the Dragon Kingdom's isles hanging above; then
#   the Sky Bridge     climbing out over the void on chains between stone towers, to
#   the Sky Gate       the Dragon Kingdom's gate, colossal: the loading zone.
#
# Blender coordinates (x east, y north, z up). The route is a loop (the kit's courses are),
# the road only from START to END; the rest goes round out of sight, high over everything.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import Vector, bmesh, lerp, smooth  # noqa: E402
import pocket_build as pb  # noqa: E402
from pocket_build import box, cone  # noqa: E402
import props  # noqa: E402
import beach_props as bp  # noqa: E402
import tropic_props as tp  # noqa: E402
import gulch_props as gp  # noqa: E402
import region_paint as paint  # noqa: E402
import region_ruin as rr  # noqa: E402

TRACK_ID = "journey_cause" + os.environ.get("KP_REGION_SUFFIX", "")
HZ = 260.0
DEPTH = -22.0  # the underground road's height (under the seabed)
SEABED = -3.0  # the slab's top: the sea floor, under the sea
WATER_Z = 0.0
SLAB_N = 40.0  # the slab (the seabed's rock, the underground in it) runs north to here
VOID_Z = -170.0

# The Sump: the pit's middle, its floor, the rim's height and radius, the cavern's.
SUMP = (0.0, -130.0)
SUMP_FLOOR = -68.0
SUMP_RIM = DEPTH
SUMP_R = (48.0, 88.0, 104.0)  # floor edge, rim, cavern wall
HARBOUR = (-22.0, -150.0, 24.0)  # the black water on its floor
HARBOUR_Z = SUMP_FLOOR - 1.4


def _spiral():
    """The road down the Sump's wall: from the rim (south-east), clockwise 300 degrees,
    tightening, to the floor."""
    out = []
    for k in range(13):
        a = math.radians(-30.0 - 25.0 * k)
        r = 84.0 - 30.0 * k / 12.0
        out.append((SUMP[0] + r * math.cos(a), SUMP[1] + r * math.sin(a), SUMP_RIM - 44.0 * k / 12.0))
    return out


MOUTH = (24.0, 190.0)  # where the Long Bore comes out of the world's edge
ROUTE = [
    (-70.0, -490.0, DEPTH),  # 0: lead-in (no road): back towards the isles' sea door
    (-60.0, -440.0, DEPTH),  # 1: START, from Tropic Isles
    (-40.0, -385.0, DEPTH),
    (10.0, -332.0, DEPTH),  # 3: into the Wreck Hall
    (70.0, -302.0, DEPTH),
    (96.0, -250.0, DEPTH),
    (88.0, -205.0, DEPTH),  # 6: the narrows, to the Sump's rim
] + _spiral() + [  # 7-19: down the Sump's wall
    (62.0, -121.0, SUMP_FLOOR + 1.4),  # 20: across its floor
    (88.0, -130.0, SUMP_FLOOR + 1.8),  # 21: the Long Bore, out of its foot
    (112.0, -126.0, -65.0),
    (152.0, -86.0, -63.0),
    (166.0, -16.0, -60.0),
    (140.0, 62.0, -56.0),
    (92.0, 132.0, -52.0),
    (46.0, 172.0, -50.0),  # 27: out through the cliff of the world's edge
    (14.0, 214.0, -48.0),  # 28: the Sky Bridge, climbing
    (-22.0, 270.0, -42.0),
    (10.0, 330.0, -34.0),
    (-10.0, 392.0, -26.0),
    (0.0, 445.0, -20.0),  # 32: END, at the Sky Gate
    (0.0, 476.0, -20.0),  # 33: lead-out (no road)
    (250.0, 520.0, HZ),
    (480.0, 200.0, HZ),
    (450.0, -300.0, HZ),
    (150.0, -530.0, HZ),
    (-150.0, -530.0, HZ),
]
START, END = 1, 32
ENDS = {"start": ((-60.0, -440.0), (-70.0, -490.0)), "end": ((0.0, 445.0), (0.0, 476.0))}

# The caverns: (name, x, y, rx, ry, roof height over the road).
CAVERNS = [
    ("Wreck Hall", 52.0, -278.0, 64.0, 56.0, 16.0),
    ("Sea Door Grotto", -55.0, -430.0, 30.0, 38.0, 31.0),  # (open overhead too: where you come in)
]
# The holes in the seabed over the Sump (the Eye) and the grotto: open to the sea overhead.
SKYLIGHTS = [(SUMP[0], SUMP[1], 26.0), (-55.0, -430.0, 20.0)]
SKYLIGHT = SKYLIGHTS[0]
# The Edge: the reef standing out of the sea on the slab, the rim where the sea falls off.
SHELF = (64.0, 122.0, 118.0)  # x, y, radius


def rim_y(x):
    return 174.0 + 8.0 * math.sin(x / 41.0) + 4.0 * math.sin(x / 13.0 + 1.0)


def _seg(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / L2))
    return math.hypot(px - a[0] - t * dx, py - a[1] - t * dy), t


def _dense(points, every=4.0):
    n = len(points)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = points[(i - 1) % n], points[i], points[(i + 1) % n], points[(i + 2) % n]
        L = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        k = max(2, int(L / every))
        for j in range(k):
            t = j / k
            t2, t3 = t * t, t * t * t
            x = 0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y, lerp(p1[2], p2[2], t), i))
    return out


LINE = [p for p in _dense(ROUTE) if START - 1 <= p[3] <= END]
_GRID = {}
for _a, _b in zip(LINE, LINE[1:]):
    for _gx in range(int(math.floor(min(_a[0], _b[0]) / 24)) - 1, int(math.floor(max(_a[0], _b[0]) / 24)) + 2):
        for _gy in range(int(math.floor(min(_a[1], _b[1]) / 24)) - 1, int(math.floor(max(_a[1], _b[1]) / 24)) + 2):
            _GRID.setdefault((_gx, _gy), []).append((_a, _b))


def road_floor(x, y):
    best = (1e9, 0.0)
    for a, b in _GRID.get((int(math.floor(x / 24)), int(math.floor(y / 24))), ()):
        d, t = _seg(x, y, a, b)
        if d < best[0]:
            best = (d, lerp(a[2], b[2], t))
    return best


def sump_r(x, y):
    return math.hypot(x - SUMP[0], y - SUMP[1])


def cavern_at(x, y):
    r = sump_r(x, y)
    if r < SUMP_R[2]:
        return "Sump", r / SUMP_R[2]
    for name, cx, cy, rx, ry, _h in CAVERNS:
        e = math.hypot((x - cx) / rx, (y - cy) / ry)
        if e < 1.0:
            return name, e
    return None, 9.0


def reef_z(x, y):
    """The slab's top: the sea floor, and the reef standing out of the sea by the rim."""
    sx, sy, sr = SHELF
    d = math.hypot((x - sx) * 0.9, y - sy)
    reef = 4.5 + 1.6 * math.sin(x / 9.0) * math.cos(y / 11.0)
    return lerp(SEABED, reef, smooth((sr - d) / 22.0))


def _land(x, y):
    """The ground under the slab (the slab is the rock: its own mesh): the caverns' floors,
    the Sump's pit; elsewhere hidden in the rock. Off the edge: the void."""
    if y > rim_y(x):
        return VOID_Z
    r = sump_r(x, y)
    f0, f1, f2 = SUMP_R
    if r < f2:
        dh = math.hypot(x - HARBOUR[0], y - HARBOUR[1])
        if dh < HARBOUR[2] + 4.0:
            return lerp(HARBOUR_Z - 1.5, SUMP_FLOOR, smooth((dh - HARBOUR[2] + 2.0) / 6.0))
        if r < f0:
            return SUMP_FLOOR + 0.4 * math.sin(x / 7.0) * math.cos(y / 9.0)
        if r < f1:
            return lerp(SUMP_FLOOR, SUMP_RIM, (r - f0) / (f1 - f0))
        return SUMP_RIM - 0.5
    name, e = cavern_at(x, y)
    if name:
        return DEPTH - 0.6 + 1.4 * smooth((e - 0.55) / 0.45) + 0.4 * math.sin(x / 7.0) * math.cos(y / 9.0)
    return -100.0


def natural(x, y):
    h = _land(x, y)
    d, z = road_floor(x, y)
    if y > rim_y(x) - 1.0:
        return h  # (the bridge: open under it)
    if d < 8.0:
        return z - 0.25
    if d < 20.0:
        return lerp(z - 0.25, h, smooth((d - 8.0) / 12.0))
    return h


def classify(c, n, info):
    if c.y > rim_y(c.x) - 1.0:
        return ("cloud_bank", "abyss")  # (off the edge of the world: put back)
    if n.z < 0.62:
        return ("cave_rock", "wall")
    if math.hypot(c.x - HARBOUR[0], c.y - HARBOUR[1]) < HARBOUR[2] + 2.0 and c.z < HARBOUR_Z:
        return ("bog_mud", "deep_water")  # (into the harbour's black water: put back)
    if any(math.hypot(c.x - sx, c.y - sy) < sr + 6.0 for sx, sy, sr in SKYLIGHTS):
        return ("bog_mud", "dirt")  # (the floor under a skylight, sea-wet muck)
    if sump_r(c.x, c.y) < SUMP_R[2] and math.sin(c.x / 9.0 + c.y / 13.0) * math.cos(c.y / 7.0) > -0.2:
        return ("ash_soil", "dirt")  # (the Sump's floor and ledges: soot, ash, trodden filth)
    if math.sin(c.x / 9.0 + c.y / 13.0) * math.cos(c.y / 7.0) > 0.25:
        return ("bog_mud", "dirt")  # (trodden mud, oil, muck)
    return ("cave_rock", "dirt")


def main():
    c = kit.Course(TRACK_ID, "The Edge of the World", "dragon_isles")
    c.route(ROUTE, width=14.0, bank=5.0)
    c.kinds = {
        # (v2, Blake: "grungy, dirty, but a thriving underworld": old setts worn to mud)
        "under": {"mat": "ruin_road", "shoulder": 1.6, "shoulder_mat": ("bog_mud", "dirt")},
        # (down the Sump's wall: railed against the drop)
        "ledge": {"mat": "ruin_road", "surface": "road", "shoulder": 1.0, "shoulder_mat": ("bog_mud", "dirt"), "barrier": 1.1,
                  "barrier_mat": ("weathered_timber", "wall")},
        "bridge": {"mat": "plank_road", "surface": "road", "shoulder": 0.6, "shoulder_mat": ("plank_road", "road"), "barrier": 1.2,
                   "barrier_mat": ("rope_rail", "wall"), "deck": 1.4, "deck_mat": ("weathered_timber", "wall"), "ground": False},
    }
    s_start = c.nearest(*ROUTE[START][:2])[0].s
    s_end = c.nearest(*ROUTE[END][:2])[0].s

    def label(q):
        if not s_start <= q.s <= s_end:
            return None
        if q.p.y > rim_y(q.p.x) - 2.0:
            return "bridge"
        if sump_r(q.p.x, q.p.y) < SUMP_R[1] + 2.0 and q.p.z > SUMP_FLOOR + 4.0:
            return "ledge"
        return "under"

    c.roads(kit.plan(c, [(s0, s1, k) for s0, s1, k in kit.runs(c, label)], "under", max_len=160.0))

    X0, X1, Y0, Y1 = -490, 490, -490, 490
    ter = c.terrain("The Edge of the World", X0, X1, Y0, Y1, 4.0, natural, classify, near=8.0, fade=16.0)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 6.0, lambda x, y: natural(x, y) - 0.5, c.lib("cave_rock", "dirt"))

    def ground(x, y):
        z = c.ground_z(x, y, [ter])
        return natural(x, y) if z is None else z

    s_light = c.nearest(*ROUTE[27][:2])[0].s
    underground(c, s_start, s_light)
    sea_and_sky(c)
    skylights(c, ground)
    sump(c, ground)
    wreck_hall(c, ground)
    grime(c, ground, s_start, s_light)
    the_edge(c, ground)
    sky_bridge(c, s_end)
    ends(c)
    far_kingdom(c)
    # The air: the underground's dark, lantern-lit; the sky's bright, out at the edge.
    for x, y, look in ((-55.0, -430.0, "under"), (52.0, -278.0, "under"), (0.0, -130.0, "sump"), (60.0, -200.0, "sump"),
                       (-60.0, -90.0, "sump"), (160.0, -40.0, "under"), (110.0, 110.0, "under"), (20.0, 230.0, "edge"),
                       (0.0, 380.0, "edge")):
        g = c.game(x, y, 0.0)
        c.entity("air_spot", x=round(g[0], 1), z=round(g[2], 1), look=LOOKS[look])

    gts = c.checkpoints(height=10.0)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish(extra={"race": {"laps": 1}, "journey": {"from": round(s_start, 1), "to": round(s_end, 1)}})
    print("road %.0f m (s %.0f..%.0f), loop %.0f, gates %d" % (s_end - s_start, s_start, s_end, c.length, len(gts)))
    for name, (zone, beyond) in ENDS.items():
        g = c.game(zone[0], zone[1], 0.0)
        q, _ = c.nearest(*zone)
        tx, ty = (q.t.x, q.t.y) if name == "start" else (-q.t.x, -q.t.y)
        print("passage %s: x %.1f z %.1f heading %.4f" % (name, g[0], g[2], math.atan2(tx, -ty)))
    g = c.game(*ROUTE[START][:2], 0.0)
    print("spawn x %.1f z %.1f" % (g[0], g[2]))


LOOKS = {
    # (overworld/air.ts: an area's look, blended as you drive between them)
    # (v2: smoky, the lamps' oily light)
    "under": {"sky": "#120e09", "fog": {"enabled": True, "color": "#2a2116", "near": 24, "far": 220},
              "sun": {"color": "#ffc98a", "intensity": 0.5, "direction": [-0.3, 0.9, 0.2]},
              "ambient": {"sky": "#9a7a58", "ground": "#2a1c10", "intensity": 0.8}},
    # (the Sump: smoke and lamplight, the Eye's sea-green light falling through it)
    "sump": {"sky": "#1a140c", "fog": {"enabled": True, "color": "#3a2c1a", "near": 40, "far": 320},
             "sun": {"color": "#c8f0e0", "intensity": 0.9, "direction": [-0.15, 0.97, 0.1]},
             "ambient": {"sky": "#b08a5c", "ground": "#2c2012", "intensity": 0.9}},
    "skylight": {"sky": "#123a4a", "fog": {"enabled": True, "color": "#1d4a58", "near": 40, "far": 300},
                 "sun": {"color": "#bff0ff", "intensity": 1.2, "direction": [-0.2, 0.95, 0.1]},
                 "ambient": {"sky": "#7fd0e0", "ground": "#2a3a34", "intensity": 0.95}},
    "edge": {"sky": "#7ab8f0", "fog": {"enabled": True, "color": "#f2d9c4", "near": 600, "far": 3200},
             "sun": {"color": "#fff0d8", "intensity": 2.6, "direction": [-0.3, 0.55, -0.8]},
             "ambient": {"sky": "#d8e6ff", "ground": "#c49a7a", "intensity": 1.3},
             "skyDome": {"top": "#2f72d0", "horizon": "#ffe2c8", "bottom": "#f6efe6",
                         "sun": {"color": "#fff6e0", "size": 9, "glow": "#ffd9a8", "elevation": 24},
                         "clouds": {"count": 40, "color": "#ffffff", "shade": "#f0dccc", "seed": 77, "low": -14, "high": 26,
                                    "drift": 0.003}}},
}


# ------------------------------------------------------------------ the underground


def underground(c, s0, s1):
    """The seabed's rock: a slab over the whole underground out to the world's edge (its top
    the sea floor and the reef, its north face the cliff of the edge), and the bores, the
    caverns and the Sump cut out of it."""
    bm = bmesh.new()
    zb = -115.0
    n = 60
    top = []
    for j in range(n + 1):
        row = []
        for i in range(n + 1):
            x = lerp(-490.0, 490.0, i / n)
            y = lerp(-490.0, rim_y(x), j / n)
            row.append(bm.verts.new((x, y, reef_z(x, y) + (0.0 if j < n else -0.5))))
        top.append(row)
    for j in range(n):
        for i in range(n):
            bm.faces.new((top[j][i], top[j][i + 1], top[j + 1][i + 1], top[j + 1][i]))
    ring = ([top[0][i] for i in range(n + 1)] + [top[j][n] for j in range(1, n + 1)] + [top[n][i] for i in range(n - 1, -1, -1)]
            + [top[j][0] for j in range(n - 1, 0, -1)])
    low = [bm.verts.new((v.co.x, v.co.y, zb)) for v in ring]
    m = len(ring)
    for k in range(m):
        bm.faces.new((ring[(k + 1) % m], ring[k], low[k], low[(k + 1) % m]))
    bm.faces.new(low)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    slab = c.mesh_object("Seabed Rock", bm, "Rocks", "both")
    # The caverns: domes cut up from under the floor to their roofs.
    for name, cx, cy, rx, ry, h in CAVERNS:
        dm = bmesh.new()
        res = bmesh.ops.create_uvsphere(dm, u_segments=28, v_segments=14, radius=1.0)
        for v in res["verts"]:
            wob = 1.0 + 0.08 * math.sin(v.co.x * 7.0 + v.co.y * 5.0) * (v.co.z > -0.2)
            v.co = Vector((cx + v.co.x * rx * wob, cy + v.co.y * ry * wob, DEPTH - 3.0 + (v.co.z + 0.2) / 1.2 * (h + 3.0) * wob))
        _subtract(slab, c.mesh_object(name + " Cutter", dm, "Rocks", "visual"))
    # The Sump: a great drum of a cavern, its roof domed up to the Eye.
    dm = bmesh.new()
    prof = [(0.0, SUMP_FLOOR - 12.0), (SUMP_R[2], SUMP_FLOOR - 12.0), (SUMP_R[2], -16.0), (SUMP_R[2] - 12.0, -9.0), (66.0, -5.5),
            (36.0, -3.6), (24.0, 2.0), (0.0, 4.0)]
    rings = []
    for r, z in prof:
        if r == 0.0:
            rings.append([dm.verts.new((SUMP[0], SUMP[1], z))])
            continue
        rings.append([dm.verts.new((SUMP[0] + r * (1.0 + 0.04 * math.sin(3 * a)) * math.cos(a),
                                    SUMP[1] + r * (1.0 + 0.04 * math.sin(3 * a)) * math.sin(a), z))
                      for a in [k * math.tau / 40 for k in range(40)]])
    for lo, hi in zip(rings, rings[1:]):
        if len(lo) == 1:
            for k in range(40):
                dm.faces.new((lo[0], hi[(k + 1) % 40], hi[k]))
        elif len(hi) == 1:
            for k in range(40):
                dm.faces.new((lo[k], lo[(k + 1) % 40], hi[0]))
        else:
            for k in range(40):
                dm.faces.new((lo[k], lo[(k + 1) % 40], hi[(k + 1) % 40], hi[k]))
    bmesh.ops.recalc_face_normals(dm, faces=dm.faces)
    _subtract(slab, c.mesh_object("Sump Cutter", dm, "Rocks", "visual"))
    c.tunnel(slab, s0 - 30.0, s1 + 24.0, half=c.width / 2 + 4.0, height=11.0, pad=6.0)
    groups = {}
    for p in slab.data.polygons:
        z = p.center.z
        if p.normal.z > 0.6 and z > 1.0:
            k = ("cove_rock", "dirt")  # (the reef, out of the sea)
        elif p.normal.z > 0.6 and z > SEABED - 1.5:
            k = ("cove_wet_sand", "deep_water")  # (the sea floor)
        elif p.center.y > rim_y(p.center.x) - 3.0 and p.normal.y > 0.5:
            k = ("keep_rock", "wall")  # (the cliff of the world's edge)
        else:
            k = ("cave_rock", "wall")
        groups.setdefault(k, []).append(p.index)
    for k, faces in groups.items():
        c.assign(slab, c.lib(*k), faces)
    slab.data.shade_flat()
    # Lanterns down the bores, both sides by turns.
    s = s0 + 6.0
    k = 0
    while s < s1 - 4.0:
        q = c.at(s)
        if cavern_at(q.p.x, q.p.y)[0] is None:
            sd = 1 if k % 2 else -1
            g = c.game(q.p.x + q.r.x * sd * (c.width / 2 + 3.0), q.p.y + q.r.y * sd * (c.width / 2 + 3.0), q.p.z + 5.0)
            c.entity("lantern", x=g[0], y=g[1], z=g[2])
        s += 14.0
        k += 1


def _subtract(target, cutter):
    import bpy

    mod = target.modifiers.new("Cut", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
    mod.object = cutter
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter)


def _glow_crystal(c, name, x, y, z, h, mat, lean=0.0):
    cone(c, name, x, y, h * 0.22, z - 0.3, h, (mat, "wall"), segs=5, role="visual")


def skylights(c, ground):
    """The holes in the seabed: the sea's water over them seen from below, and the sea
    spilling in round their rims in thin falls to pools on the floor."""
    for j, (sx, sy, sr) in enumerate(SKYLIGHTS):
        bm = bmesh.new()
        pts = [(sx + (sr + 6.0) * math.cos(a), sy + (sr + 6.0) * math.sin(a)) for a in [k * math.tau / 40 for k in range(40)]]
        bm.faces.new([bm.verts.new((x, y, SEABED + 1.2)) for x, y in pts])
        bm.faces.new([bm.verts.new((x, y, SEABED + 1.15)) for x, y in reversed(pts)])
        c.assign(c.mesh_object("Skylight %d" % j, bm, "Water", "visual"), c.lib("canyon_river", "water"))
        for k in range(3 + j % 2):
            a = k * math.tau / (3 + j % 2) + 0.7 * j
            lx, ly = sx + (sr - 2.0) * math.cos(a), sy + (sr - 2.0) * math.sin(a)
            if not paint.road_clear(c, lx, ly, 3.0):
                continue
            foot = ground(lx, ly)
            props.falls(c, "Skylight Falls %d %d" % (j, k), lx, ly, SEABED - 0.5, foot + 0.3, 1.6, 3.0, facing=1, throw=1.5, bulge=0.4,
                        veils=2, angle=a + math.pi / 2, mats=("falls_oasis", "falls_curtain_oasis", "falls_foam"))
            c.disc("Skylight Pool %d %d" % (j, k), lx, ly, 3.6, foot + 0.12, c.lib("lagoon_shallow", "water"), role="visual", n=16,
                   wobble=0.2, seed=k)


def _egg(c, name, x, y, z, r, mat):
    bm = bmesh.new()
    props.blob(bm, (x, y, z + r * 1.2), r, sz=1.35, subdiv=1)
    c.assign(c.mesh_object(name, bm, "Props", "visual"), c.lib(mat, "wall"))


def sump(c, ground):
    """The Sump (Blake: "a massive underground trade hub of scum and villainy"; Tortuga, coming
    off the isles; loot from every kingdom; a crime boss): pirates' shacks and taverns stacked
    on its ledges, flags, lamps; rope bridges and cargo cranes across it; the black-water
    harbour on its floor, the smugglers' ships moored at its docks; the loot market (the
    Snow Kingdom's ice, the Valley's eggs, the desert's neon, the isles' coral and pearls,
    dragon light stolen in crystals, gold); the Broker's gilded ship hanging over it all on
    chains from the roof."""
    sx, sy = SUMP
    f0, f1, f2 = SUMP_R
    # Shacks and taverns along the ledges' wall side, a lamp at each, flags.
    k = 0
    for q in c.S[::12]:
        r = sump_r(q.p.x, q.p.y)
        if not (f0 + 4.0 < r < f1 + 2.0) or q.p.z < SUMP_FLOOR + 5.0:
            continue
        ox, oy = (q.p.x - sx) / r, (q.p.y - sy) / r
        x, y = q.p.x + ox * (q.w / 2 + 6.5), q.p.y + oy * (q.w / 2 + 6.5)
        rot = math.atan2(oy, ox) + math.pi / 2
        if k % 3 == 2:
            # A tavern: two storeys, balcony, lit windows all along.
            box(c, "Tavern %d" % k, x, y, 6.0, 3.6, q.p.z - 1.0, q.p.z + 9.0, ("wreck_planks", "wall"), rot=rot - math.pi / 2)
            box(c, "Tavern Balcony %d" % k, x - ox * 4.2, y - oy * 4.2, 6.2, 0.8, q.p.z + 4.6, q.p.z + 4.9, ("plank_deck", "wall"),
                rot=rot - math.pi / 2, role="visual")
            for w in (-3.6, 0.0, 3.6):
                for h in (1.4, 6.0):
                    wx, wy = x - ox * 3.65 + oy * w, y - oy * 3.65 - ox * w
                    box(c, "Tavern Window %d %d %d" % (k, int(w), int(h)), wx, wy, 0.8, 0.1, q.p.z + h, q.p.z + h + 1.4,
                        ("window_warm", "wall"), rot=rot - math.pi / 2, role="visual")
        else:
            c.place(tp.pirate_hut(c, k % 2), x, y, q.p.z - 0.3, rot=rot + math.pi, role="visual")
        # (its flag: black, on a pole off the roof)
        fx, fy = x + oy * 3.0, y - ox * 3.0
        box(c, "Flag Pole %d" % k, fx, fy, 0.08, 0.08, q.p.z, q.p.z + 13.0, ("weathered_timber", "wall"), role="visual")
        _cloth(c, "Flag %d" % k, [(fx, fy, q.p.z + 12.8), (fx + oy * 2.6, fy - ox * 2.6, q.p.z + 12.4),
                                  (fx + oy * 2.6, fy - ox * 2.6, q.p.z + 10.9), (fx, fy, q.p.z + 11.3)],
               ("dark_corridor", "banner_red", "dark_corridor", "awning_teal")[k % 4])
        g = c.game(q.p.x + ox * (q.w / 2 + 2.0), q.p.y + oy * (q.w / 2 + 2.0), q.p.z + 4.0)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
        k += 1
    # Rope bridges slung across the pit (high over the road), cargo cranes on the rim.
    for j, (a0, a1, z) in enumerate(((0.3, 2.6, -30.0), (1.4, 4.1, -38.0), (3.0, 5.4, -27.0), (4.6, 0.9, -44.0))):
        p0 = (sx + f1 * 0.98 * math.cos(a0), sy + f1 * 0.98 * math.sin(a0))
        p1 = (sx + f1 * 0.98 * math.cos(a1), sy + f1 * 0.98 * math.sin(a1))
        pts = []
        for i in range(17):
            t = i / 16
            pts.append((lerp(p0[0], p1[0], t), lerp(p0[1], p1[1], t), z - 6.0 * (1.0 - (2 * t - 1) ** 2)))
        for sd in (-1, 1):
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            L = math.hypot(dx, dy)
            nx, ny = -dy / L * sd * 1.2, dx / L * sd * 1.2
            bm = bmesh.new()
            props.tube(bm, [(x + nx, y + ny, zz + 1.1) for x, y, zz in pts], 0.06, n=3)
            c.assign(c.mesh_object("Rope Bridge Rope %d %d" % (j, sd), bm, "Props", "visual"), c.lib("rope_rail", "wall"))
        for i in range(0, 16):
            x, y, zz = pts[i]
            box(c, "Rope Bridge Plank %d %d" % (j, i), x, y, 1.3, 0.4, zz - 0.1, zz + 0.05, ("plank_deck", "wall"),
                rot=math.atan2(p1[1] - p0[1], p1[0] - p0[0]) + math.pi / 2, role="visual")
    for j in range(4):
        a = j * math.tau / 4 + 0.8
        x, y = sx + (f1 + 8.0) * math.cos(a), sy + (f1 + 8.0) * math.sin(a)
        if not paint.road_clear(c, x, y, 5.0):
            continue
        z = SUMP_RIM - 0.5
        box(c, "Crane Post %d" % j, x, y, 0.6, 0.6, z, z + 18.0, ("weathered_timber", "wall"))
        ax_, ay_ = sx + (f1 - 22.0) * math.cos(a), sy + (f1 - 22.0) * math.sin(a)
        bm = bmesh.new()
        props.tube(bm, [(x, y, z + 17.0), (ax_, ay_, z + 15.0)], 0.35, n=5)
        props.tube(bm, [(ax_, ay_, z + 15.0), (ax_, ay_, z - 6.0)], 0.05, n=3)
        c.assign(c.mesh_object("Crane Arm %d" % j, bm, "Props", "visual"), c.lib("weathered_timber", "wall"))
        box(c, "Crane Load %d" % j, ax_, ay_, 1.6, 1.6, z - 9.0, z - 6.0, ("wreck_planks", "wall"), role="visual")
    # The harbour: docks round the black water, the smugglers' ships moored.
    hx, hy, hr = HARBOUR
    c.disc("Harbour", hx, hy, hr + 3.0, HARBOUR_Z, c.lib("keep_lake", "water"), role="visual", n=32, wobble=0.1, seed=6)
    for j in range(10):
        a = j * math.tau / 10 + 0.2
        x, y = hx + (hr + 2.0) * math.cos(a), hy + (hr + 2.0) * math.sin(a)
        if paint.road_clear(c, x, y, 3.0):
            box(c, "Dock %d" % j, x, y, 4.0, 1.6, HARBOUR_Z - 1.0, SUMP_FLOOR + 0.3, ("plank_deck", "wall"), rot=a + math.pi / 2)
    for j, (dx, dy, a) in enumerate(((-6.0, 6.0, 0.4), (8.0, -8.0, 2.1))):
        x, y = hx + dx, hy + dy
        box(c, "Smuggler Ship %d" % j, x, y, 9.0, 2.8, HARBOUR_Z - 2.0, HARBOUR_Z + 2.6, ("wreck_hull", "wall"), rot=a, role="visual")
        c.place(tp.mast(c, h=16.0), x, y, HARBOUR_Z + 2.4, rot=a, role="visual")
        _cloth(c, "Ship Sail %d" % j, [(x - 3.0 * math.sin(a), y + 3.0 * math.cos(a), HARBOUR_Z + 15.0),
                                       (x + 3.0 * math.sin(a), y - 3.0 * math.cos(a), HARBOUR_Z + 15.0),
                                       (x + 3.4 * math.sin(a), y - 3.4 * math.cos(a), HARBOUR_Z + 6.0),
                                       (x - 3.4 * math.sin(a), y + 3.4 * math.cos(a), HARBOUR_Z + 6.0)], ("canvas_torn", "sail_cloth")[j])
    # The loot market on the floor: each stall's loot from another kingdom.
    loot = ("ice", "eggs", "neon", "coral", "crystals", "gold")
    k = 0
    for j in range(26):
        a = j * 2.399 + 0.3
        r = 10.0 + 34.0 * ((j * 0.618) % 1.0)
        x, y = sx + r * math.cos(a), sy + r * math.sin(a)
        if not paint.road_clear(c, x, y, 3.5) or math.hypot(x - hx, y - hy) < hr + 6.0:
            continue
        z = ground(x, y)
        rot = a
        box(c, "Loot Stall %d" % j, x, y, 2.6, 1.2, z - 0.2, z + 1.1, ("plank_deck", "wall"), rot=rot)
        _cloth(c, "Loot Awning %d" % j, [(x - 3.0 * math.cos(rot), y - 3.0 * math.sin(rot), z + 3.2),
                                         (x + 3.0 * math.cos(rot), y + 3.0 * math.sin(rot), z + 3.2),
                                         (x + 3.0 * math.cos(rot) - 2.0 * math.sin(rot), y + 3.0 * math.sin(rot) + 2.0 * math.cos(rot), z + 2.4),
                                         (x - 3.0 * math.cos(rot) - 2.0 * math.sin(rot), y - 3.0 * math.sin(rot) + 2.0 * math.cos(rot), z + 2.4)],
               ("canvas_torn", "awning_red", "sail_cloth", "awning_teal", "rug")[j % 5])
        kind = loot[k % len(loot)]
        for i in range(3):
            lx, ly = x + (i - 1) * 1.5 * math.cos(rot), y + (i - 1) * 1.5 * math.sin(rot)
            if kind == "ice":
                box(c, "Loot Ice %d %d" % (j, i), lx, ly, 0.6, 0.6, z + 1.1, z + 2.2, ("glacier_ice", "wall"), rot=rot + i, role="visual")
            elif kind == "eggs":
                _egg(c, "Loot Egg %d %d" % (j, i), lx, ly, z + 1.1, 0.4, ("party_white", "party_red", "lush_grass")[i])
            elif kind == "neon":
                box(c, "Loot Neon %d %d" % (j, i), lx, ly, 0.6, 0.08, z + 1.2, z + 2.0, (("lantern_amber", "fire_glow", "crystal_magenta")[i], "wall"),
                    rot=rot, role="visual")
            elif kind == "coral":
                c.place(tp.coral(c, i % 3), lx, ly, z + 1.1, rot=i, scale=0.35, role="visual")
            elif kind == "crystals":
                cone(c, "Loot Crystal %d %d" % (j, i), lx, ly, 0.35, z + 1.1, 1.4, ("crystal_cyan", "wall"), segs=5, role="visual")
            else:
                cone(c, "Loot Gold %d %d" % (j, i), lx, ly, 0.6, z + 1.1, 0.6, ("gold_trim", "wall"), segs=8, role="visual")
        g = c.game(x, y, z + 2.8)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
        k += 1
    # Fires on the floor, smoke rising to the Eye; the stolen dragon light glowing in heaps.
    for j in range(6):
        a = j * 1.05 + 0.4
        x, y = sx + 30.0 * math.cos(a), sy + 30.0 * math.sin(a)
        if paint.road_clear(c, x, y, 5.0) and math.hypot(x - hx, y - hy) > hr + 6.0:
            g = c.game(x, y, ground(x, y) + 0.2)
            c.entity("campfire", x=g[0], y=g[1], z=g[2])
            rr.smoke(c, x, y, ground(x, y) + 0.5)
    for j in range(16):
        a = j * math.tau / 16 + 0.1
        x, y = sx + (f0 - 2.0) * math.cos(a), sy + (f0 - 2.0) * math.sin(a)
        if paint.road_clear(c, x, y, 3.0):
            cone(c, "Dragon Light Heap %d" % j, x, y, 1.6, ground(x, y) - 0.4, 3.0 + 1.5 * (j % 3), ("crystal_cyan", "wall"), segs=5,
                 role="visual")
    g = c.game(sx, sy, SUMP_FLOOR + 2.0)
    c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=f0 - 8.0, n=12, folk="beach", heading=0.0)
    broker(c)


def broker(c):
    """The Broker's palace: a gilded ship hanging over the middle of the Sump on four chains
    from the roof, lit from within, its stern galleries gold, a gangway hanging down."""
    sx, sy = SUMP
    z = -26.0
    rot = 0.6
    ca, sa = math.cos(rot), math.sin(rot)

    def at(lx, ly):
        return sx + lx * ca - ly * sa, sy + lx * sa + ly * ca

    box(c, "Broker Hull", sx, sy, 16.0, 5.0, z - 4.0, z + 2.0, ("wreck_hull", "wall"), rot=rot, role="visual")
    box(c, "Broker Keel", sx, sy, 13.0, 2.0, z - 6.0, z - 4.0, ("wreck_hull", "wall"), rot=rot, role="visual")
    box(c, "Broker Deck", sx, sy, 16.4, 5.4, z + 2.0, z + 2.4, ("plank_deck", "wall"), rot=rot, role="visual")
    bx, by = at(-8.0, 0.0)
    box(c, "Broker Cabin", bx, by, 6.0, 4.6, z + 2.4, z + 9.0, ("door_wood", "wall"), rot=rot, role="visual")
    box(c, "Broker Cabin Roof", bx, by, 6.6, 5.2, z + 9.0, z + 9.8, ("gold_trim", "wall"), rot=rot, role="visual")
    for w in (-3.0, -1.0, 1.0, 3.0):
        for sd in (-1, 1):
            wx, wy = at(-8.0 + w, sd * 4.65)
            box(c, "Broker Window %d %d" % (int(w), sd), wx, wy, 0.6, 0.08, z + 4.0, z + 6.6, ("window_warm", "wall"), rot=rot, role="visual")
    gx, gy = at(-16.2, 0.0)
    box(c, "Broker Gallery", gx, gy, 0.4, 5.0, z - 1.0, z + 8.0, ("gold_trim", "wall"), rot=rot, role="visual")
    for sd in (-1, 1):
        mx, my = at(4.0 * sd, 0.0)
        box(c, "Broker Lantern %d" % sd, mx, my, 0.5, 0.5, z + 2.4, z + 4.0, ("lantern_amber", "wall"), role="visual")
        g = c.game(mx, my, z + 4.4)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
    for lx, ly in ((-14.0, -4.0), (-14.0, 4.0), (14.0, -4.0), (14.0, 4.0)):
        px, py = at(lx, ly)
        tx, ty = at(lx * 1.9, ly * 3.5)
        bm = bmesh.new()
        props.tube(bm, [(px, py, z + 2.0), (tx, ty, -6.0)], 0.4, n=6)
        c.assign(c.mesh_object("Broker Chain %d %d" % (int(lx), int(ly)), bm, "Props", "visual"), c.lib("iron", "wall"))
    gx, gy = at(10.0, 5.0)
    box(c, "Broker Gangway", gx, gy, 0.8, 0.3, z - 22.0, z + 2.0, ("weathered_timber", "wall"), rot=rot, role="visual")


def wreck_hall(c, ground):
    """The Wreck Hall: old ships' hulls set into the cavern's walls, masts broken across it,
    lanterns hung on them, barrels and a rowboat or two."""
    name, cx, cy, rx, ry, h = CAVERNS[0]
    for k, a in enumerate((0.4, 1.9, 3.3, 4.6)):
        x, y = cx + rx * 0.86 * math.cos(a), cy + ry * 0.86 * math.sin(a)
        z = ground(x, y)
        rot = a + math.pi / 2
        box(c, "Hull %d" % k, x, y, 14.0, 4.0, z - 2.0, z + 7.0 + 2.0 * (k % 2), ("wreck_hull", "wall"), rot=rot)
        c.place(tp.mast(c, h=12.0, broken=True), x - 4.0 * math.cos(a), y - 4.0 * math.sin(a), z + 5.0, rot=rot + 0.4, role="visual")
        g = c.game(x - 6.0 * math.cos(a), y - 6.0 * math.sin(a), z + 6.0)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
    for j in range(10):
        a = j * 2.399 + 0.5
        r = 0.4 + 0.4 * ((j * 0.618) % 1.0)
        x, y = cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)
        if paint.road_clear(c, x, y, 4.0):
            z = ground(x, y)
            c.place(tp.barrel(c) if j % 3 else tp.rowboat(c), x, y, z - 0.1, rot=a)
    for j in range(14):
        a = j * math.tau / 14
        x, y = cx + rx * 0.78 * math.cos(a), cy + ry * 0.78 * math.sin(a)
        if paint.road_clear(c, x, y, 3.0):
            _glow_crystal(c, "Wreck Crystal %d" % j, x, y, ground(x, y), 2.0 + 1.5 * (j % 3), "crystal_teal")


# ------------------------------------------------------------------ the grime


def _cloth(c, name, pts, mat):
    bm = bmesh.new()
    bm.faces.new([bm.verts.new(p) for p in pts])
    bm.faces.new([bm.verts.new(p) for p in reversed(pts)])
    c.assign(c.mesh_object(name, bm, "Props", "visual"), c.lib(mat, "wall"))


def grime(c, ground, s0, s1):
    """The underworld lived in (Blake: "grungy, dirty, but a thriving underworld"): along
    the bores, timber shoring, pipes down the walls, puddles of oily water, junk heaped in
    the corners, crates; in the caverns, stalls crammed along the road under patched
    awnings, laundry strung across between the homes, scaffold walkways along the walls,
    soot streaking them, smoke from the cookfires and the lamps."""
    sets = gp.timber_set(c, half=c.width / 2 + 3.4, height=10.4)
    s = s0 + 4.0
    k = 0
    while s < s1 - 10.0:
        q = c.at(s)
        rot = math.atan2(q.t.y, q.t.x)
        cav = cavern_at(q.p.x, q.p.y)[0]
        if cav is None:
            if k % 2 == 0:
                c.place(sets, q.p.x, q.p.y, q.p.z - 0.3, rot=rot - math.pi / 2, role="visual")
            sd = 1 if k % 2 else -1
            ex, ey = q.p.x + q.r.x * sd * (c.width / 2 + 2.6), q.p.y + q.r.y * sd * (c.width / 2 + 2.6)
            bm = bmesh.new()
            props.tube(bm, [(ex - q.t.x * 4.5, ey - q.t.y * 4.5, q.p.z + 6.5), (ex + q.t.x * 4.5, ey + q.t.y * 4.5, q.p.z + 6.5)], 0.35,
                       n=6)
            c.assign(c.mesh_object("Pipe %d" % k, bm, "Props", "visual"), c.lib("iron", "wall"))
            if k % 3 == 0:
                c.disc("Puddle %d" % k, q.p.x - q.r.x * sd * 3.0, q.p.y - q.r.y * sd * 3.0, 2.2, q.p.z + 0.04,
                       c.lib("bog_water", "water"), role="visual", n=12, wobble=0.25, seed=k)
            if k % 4 == 1:
                jx, jy = q.p.x + q.r.x * sd * (c.width / 2 + 1.8), q.p.y + q.r.y * sd * (c.width / 2 + 1.8)
                c.place(tp.barrel(c), jx, jy, ground(jx, jy) - 0.1, rot=k)
        s += 9.0
        k += 1
    # The caverns: stalls along the road, laundry overhead, scaffolds, soot, smoke.
    for name, cx, cy, rx, ry, h in CAVERNS:
        if name != "Wreck Hall":
            continue
        ss = [q.s for q in c.S if s0 <= q.s <= s1 and cavern_at(q.p.x, q.p.y)[0] == name]
        if not ss:
            continue
        s = min(ss) + 6.0
        j = 0
        while s < max(ss) - 6.0:
            q = c.at(s)
            rot = math.atan2(q.t.y, q.t.x)
            for sd in (-1, 1):
                if (j + (sd > 0)) % 2:
                    continue
                x, y = q.p.x + q.r.x * sd * (c.width / 2 + 5.0), q.p.y + q.r.y * sd * (c.width / 2 + 5.0)
                if not paint.road_clear(c, x, y, 2.5):
                    continue
                z = ground(x, y)
                box(c, "Stall Counter %s %d %d" % (name, j, sd), x, y, 2.6, 1.0, z - 0.2, z + 1.1, ("plank_deck", "wall"), rot=rot)
                for px in (-2.4, 2.4):
                    box(c, "Stall Pole %s %d %d %d" % (name, j, sd, px), x + q.t.x * px, y + q.t.y * px, 0.1, 0.1, z, z + 3.0,
                        ("weathered_timber", "wall"), role="visual")
                ax_, ay_ = x - q.r.x * sd * 1.4, y - q.r.y * sd * 1.4
                _cloth(c, "Stall Awning %s %d %d" % (name, j, sd),
                       [(x + q.t.x * 2.8 + q.r.x * sd * 1.2, y + q.t.y * 2.8 + q.r.y * sd * 1.2, z + 3.2),
                        (x - q.t.x * 2.8 + q.r.x * sd * 1.2, y - q.t.y * 2.8 + q.r.y * sd * 1.2, z + 3.2),
                        (ax_ - q.t.x * 2.8, ay_ - q.t.y * 2.8, z + 2.5), (ax_ + q.t.x * 2.8, ay_ + q.t.y * 2.8, z + 2.5)],
                       ("canvas_torn", "awning_red", "sail_cloth", "awning_teal")[j % 4])
                for b in range(2):
                    bx_, by_ = x + q.r.x * sd * 2.4 + q.t.x * (b * 1.6 - 0.8), y + q.r.y * sd * 2.4 + q.t.y * (b * 1.6 - 0.8)
                    c.place(tp.barrel(c), bx_, by_, ground(bx_, by_) - 0.1, rot=b + j, role="visual")
                g = c.game(x, y, z + 2.8)
                c.entity("lantern", x=g[0], y=g[1], z=g[2])
            s += 9.0
            j += 1
        # Laundry strung across between the walls' homes, over the floor (not the road).
        for j in range(10):
            a = j * 0.63 + 0.3
            p0 = (cx + rx * 0.9 * math.cos(a), cy + ry * 0.9 * math.sin(a))
            p1 = (cx + rx * 0.9 * math.cos(a + 0.5), cy + ry * 0.9 * math.sin(a + 0.5))
            mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
            if not paint.road_clear(c, mid[0], mid[1], 6.0):
                continue
            z = DEPTH + 7.0
            bm = bmesh.new()
            props.tube(bm, [(p0[0], p0[1], z), (mid[0], mid[1], z - 1.2), (p1[0], p1[1], z)], 0.04, n=3)
            c.assign(c.mesh_object("Line %s %d" % (name, j), bm, "Props", "visual"), c.lib("rope_rail", "wall"))
            for f in range(4):
                t = (f + 0.5) / 4
                x, y = lerp(p0[0], p1[0], t), lerp(p0[1], p1[1], t)
                zz = z - 1.2 * (1.0 - (2 * t - 1) ** 2)
                dx, dy = (p1[0] - p0[0]), (p1[1] - p0[1])
                L = math.hypot(dx, dy) or 1.0
                ux, uy = dx / L * 0.6, dy / L * 0.6
                _cloth(c, "Wash %s %d %d" % (name, j, f), [(x - ux, y - uy, zz), (x + ux, y + uy, zz), (x + ux, y + uy, zz - 1.4),
                                                          (x - ux, y - uy, zz - 1.2)],
                       ("rug", "canvas_torn", "awning_red", "sail_cloth")[(j + f) % 4])
        # Scaffold walkways along the walls, and soot streaking them over the homes' doors.
        for j in range(18):
            a = j * math.tau / 18 + 0.15
            x, y = cx + rx * 0.97 * math.cos(a), cy + ry * 0.97 * math.sin(a)
            if not paint.road_clear(c, x, y, 5.0):
                continue
            z = ground(x, y)
            rot = a + math.pi / 2
            box(c, "Scaffold %s %d" % (name, j), x - 3.0 * math.cos(a), y - 3.0 * math.sin(a), 4.0, 1.2, z + 11.5, z + 11.8,
                ("plank_deck", "wall"), rot=rot, role="visual")
            for sx in (-1, 1):
                box(c, "Scaffold Post %s %d %d" % (name, j, sx), x - 3.6 * math.cos(a) + sx * 3.6 * math.cos(rot),
                    y - 3.6 * math.sin(a) + sx * 3.6 * math.sin(rot), 0.12, 0.12, z, z + 11.8, ("weathered_timber", "wall"), role="visual")
            box(c, "Soot %s %d" % (name, j), x - 0.6 * math.cos(a), y - 0.6 * math.sin(a), 1.4, 0.1, z + 3.0, z + 10.0,
                ("ash_soil", "wall"), rot=rot, role="visual")
        # Smoke from the cookfires, junk heaped by the walls.
        for j in range(5):
            a = j * 1.37 + 0.6
            x, y = cx + rx * 0.6 * math.cos(a), cy + ry * 0.6 * math.sin(a)
            if paint.road_clear(c, x, y, 5.0):
                rr.smoke(c, x, y, ground(x, y) + 0.5)
            x, y = cx + rx * 0.84 * math.cos(a + 0.6), cy + ry * 0.84 * math.sin(a + 0.6)
            if paint.road_clear(c, x, y, 6.0):
                rr.rubble(c, "Junk %s %d" % (name, j), x, y, ground, ("wreck_planks", "wall"), n=6, spread=3.0, size=1.0, seed=j + 3)


# ------------------------------------------------------------------ the edge


def sea_and_sky(c):
    """The sea over the seabed, ending at the rim; the cloud sea far below the edge."""
    bm = bmesh.new()
    xs = [x for x in range(-490, 491, 20)]
    north = [bm.verts.new((x, rim_y(x) + 1.0, WATER_Z)) for x in xs]
    south = [bm.verts.new((x, -490.0, WATER_Z)) for x in xs]
    for i in range(len(xs) - 1):
        bm.faces.new((south[i], south[i + 1], north[i + 1], north[i]))
    c.assign(c.mesh_object("Sea", bm, "Water", "visual"), c.lib("sea_water", "water"))
    c.disc("Cloud Sea", 0.0, 400.0, 1600.0, VOID_Z + 70.0, c.lib("cloud_bank", "abyss"), role="visual", n=64)


def the_edge(c, ground):
    """The sea falling off the rim of the world: falls all along it but where the reef is,
    pouring down into the clouds; the bridgehead tower."""
    x = -470.0
    k = 0
    while x < 470.0:
        w = 34.0 + 10.0 * math.sin(x / 31.0)
        ry = rim_y(x)
        on_reef = math.hypot((x - SHELF[0]) * 0.9, ry - SHELF[1]) < SHELF[2] - 6.0
        if not on_reef and abs(x - MOUTH[0]) > 26.0:
            props.falls(c, "Edge Falls %d" % k, x, ry + 1.0, WATER_Z + 0.2, VOID_Z + 72.0, w, w * 1.3, facing=1, throw=8.0, bulge=1.8,
                        veils=3 if k % 2 else 2, foam=False, mats=("falls_oasis", "falls_curtain_oasis", "falls_foam"))
        x += w * 0.92
        k += 1
    for j in range(8):
        a = j * 0.9
        g = c.game(-300.0 + j * 85.0, rim_y(-300.0 + j * 85.0) + 6.0, WATER_Z - 6.0)
        c.entity("steam", x=g[0], y=g[1], z=g[2])


def sky_bridge(c, s_end):
    """The Sky Bridge's stone towers (the road through their arches, every 70 m or so), their
    feet going down into the clouds, the chains slung from tower to tower."""
    import props as P  # noqa: F401

    s0 = next(q.s for q in c.S if q.p.y > rim_y(q.p.x) - 2.0)
    towers = []
    s = s0 + 8.0
    while s < s_end - 30.0:
        towers.append(c.at(s))
        s += 72.0
    for k, q in enumerate(towers):
        rot = math.atan2(q.t.y, q.t.x)
        for sd in (-1, 1):
            px, py = q.p.x + q.r.x * sd * (q.w / 2 + 2.6), q.p.y + q.r.y * sd * (q.w / 2 + 2.6)
            box(c, "Tower %d %d" % (k, sd), px, py, 1.8, 1.8, VOID_Z + 60.0, q.p.z + 22.0, ("keep_rock", "wall"), rot=rot)
            cone(c, "Tower Cap %d %d" % (k, sd), px, py, 2.6, q.p.z + 22.0, 5.0, ("keep_rock", "wall"), segs=4, role="visual")
            g = c.game(px - q.t.x * 2.2, py - q.t.y * 2.2, q.p.z + 6.0)
            c.entity("torch", x=g[0], y=g[1], z=g[2])
        box(c, "Tower Arch %d" % k, q.p.x, q.p.y, 1.6, q.w / 2 + 4.4, q.p.z + 15.0, q.p.z + 18.0, ("keep_rock", "wall"), rot=rot,
            role="visual")
        # (The tower's foot: a column of rock going down into the clouds under the deck.)
        box(c, "Tower Foot %d" % k, q.p.x, q.p.y, 3.4, q.w / 2 + 4.4, VOID_Z + 60.0, q.p.z - 1.8, ("keep_rock", "wall"), rot=rot)
    # The chains: from each tower's top down to the deck's edge and up to the next.
    for a, b in zip(towers, towers[1:]):
        for sd in (-1, 1):
            pts = []
            for j in range(13):
                t = j / 12
                q = c.at(lerp(a.s, b.s, t))
                sag = 18.0 * (1.0 - (2 * t - 1) ** 2)
                pts.append((q.p.x + q.r.x * sd * (q.w / 2 + 1.2), q.p.y + q.r.y * sd * (q.w / 2 + 1.2), q.p.z + 20.0 - sag))
            bm = bmesh.new()
            props.tube(bm, pts, 0.35, n=6)
            c.assign(c.mesh_object("Chain %d %d" % (int(a.s), sd), bm, "Props", "visual"), c.lib("iron", "wall"))
            for j in range(1, 12, 2):
                x, y, z = pts[j]
                q = c.at(lerp(a.s, b.s, j / 12))
                bm = bmesh.new()
                props.tube(bm, [(x, y, z), (x, y, q.p.z + 1.2)], 0.08, n=4)
                c.assign(c.mesh_object("Hanger %d %d %d" % (int(a.s), sd, j), bm, "Props", "visual"), c.lib("iron", "wall"))


def ends(c):
    """The start: the bore back to the isles' sea door, walled off past its gate. The end:
    the Sky Gate, colossal, two great piers and a lintel over the bridge's end, dragon
    heads on them, the Dragon Kingdom beyond (the loading zone just before it)."""
    (zx, zy), (bx, by) = ENDS["start"]
    q, _ = c.nearest(zx, zy)
    ux, uy = bx - zx, by - zy
    d = math.hypot(ux, uy)
    ux, uy = ux / d, uy / d
    rot = math.atan2(uy, ux)
    z = q.p.z
    gx, gy = zx + ux * 10.0, zy + uy * 10.0
    for sd in (-1, 1):
        px, py = gx - uy * sd * 9.5, gy + ux * sd * 9.5
        box(c, "Sea Door Post %d" % sd, px, py, 1.0, 1.0, z - 1.0, z + 9.0, ("weathered_timber", "wall"), rot=rot)
    box(c, "Sea Door Lintel", gx, gy, 1.0, 10.5, z + 9.0, z + 10.2, ("weathered_timber", "wall"), rot=rot, role="visual")
    box(c, "Sea Door", zx + ux * 20.0, zy + uy * 20.0, 1.5, 12.0, z - 2.0, z + 12.0, ("wreck_hull", "wall"), rot=rot)
    (zx, zy), (bx, by) = ENDS["end"]
    q, _ = c.nearest(zx, zy)
    rot = math.atan2(by - zy, bx - zx)
    z = q.p.z
    gx, gy = zx, zy + 12.0
    for sd in (-1, 1):
        px = gx + sd * 15.0
        box(c, "Sky Gate Pier %d" % sd, px, gy, 4.0, 4.0, VOID_Z + 60.0, z + 44.0, ("keep_rock", "wall"))
        cone(c, "Sky Gate Head %d" % sd, px, gy - 4.0, 3.2, z + 30.0, 12.0, ("gold_trim", "wall"), segs=6,
             role="visual")
        g = c.game(px, gy - 5.0, z + 8.0)
        c.entity("torch", x=g[0], y=g[1], z=g[2])
    box(c, "Sky Gate Lintel", gx, gy, 19.0, 4.5, z + 40.0, z + 46.0, ("keep_rock", "wall"), role="visual")
    box(c, "Sky Gate Floor", gx, gy + 6.0, 13.0, 14.0, VOID_Z + 60.0, z - 0.15, ("keep_cobble", "road"))


def far_kingdom(c):
    """The Dragon Kingdom across the void (the region itself is beyond the gate): floating
    isles at their heights, falls off them, the Citadel's spire in the middle."""
    isles = [(-220.0, 640.0, 70.0, 40.0), (180.0, 620.0, 60.0, 70.0), (-120.0, 860.0, 80.0, 110.0), (240.0, 860.0, 66.0, 150.0),
             (0.0, 1000.0, 90.0, 60.0)]
    for k, (x, y, r, z) in enumerate(isles):
        rm = c.rock_mass("Far Isle %d" % k, x, y, r, r * 0.8, z + 10.0, z0=z - r * 0.9, n=18, seed=40 + k,
                         bands=[(0.2, 0.0), (0.6, 0.35), (0.95, 0.75), (1.0, 0.9), (0.96, 1.0)])
        c.paint_rock(rm, ("keep_rock", "wall"), ("keep_grass", "grass"))
        props.falls(c, "Far Falls %d" % k, x, y - r * 0.75, z + 9.0, z - r * 0.8, 6.0, 9.0, facing=-1, throw=4.0, veils=2, foam=False,
                    mats=("falls_oasis", "falls_curtain_oasis", "falls_foam"))
    sp = c.rock_mass("Citadel Spire", 30.0, 780.0, 40.0, 40.0, 300.0, z0=VOID_Z + 60.0, n=16, seed=3,
                     bands=[(1.0, 0.0), (0.7, 0.4), (0.45, 0.8), (0.3, 1.0)])
    c.assign(sp, c.lib("keep_rock", "wall"))
    box(c, "Citadel", 30.0, 780.0, 22.0, 22.0, 290.0, 330.0, ("keep_rock", "wall"), role="visual")
    cone(c, "Citadel Roof", 30.0, 780.0, 26.0, 330.0, 40.0, ("gold_trim", "wall"), segs=8, role="visual")


if __name__ == "__main__":
    main()
