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
#     the Wreck Hall   a cavern with old ships' hulls set in its walls,
#     Undertown        the tunnel folk's town round a great cavern, its roof open to the sea
#                      overhead (a skylight of water), homes carved in its walls, coral and
#                      crystals glowing, then
#     the Long Stair   climbing up and out through a knoll of rock into the light, onto
#   the Edge           a reef of rock at the very edge of the world: the sea pours off its
#                      rim into the clouds, and across the void the Dragon Kingdom's isles
#                      hang in the sky; then
#   the Sky Bridge     out over the void on chains between stone towers, to
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

TRACK_ID = "journey_cause" + os.environ.get("KP_REGION_SUFFIX", "")
HZ = 260.0
DEPTH = -22.0  # the underground road's height (under the seabed)
SEABED = -3.0  # the slab's top: the sea floor, under the sea
WATER_Z = 0.0
SLAB_N = 40.0  # the slab (the seabed's rock, the underground in it) runs north to here
VOID_Z = -170.0

ROUTE = [
    (-70.0, -490.0, DEPTH),  # 0: lead-in (no road): back towards the isles' sea door
    (-60.0, -440.0, DEPTH),  # 1: START, from Tropic Isles
    (-40.0, -385.0, DEPTH),
    (10.0, -332.0, DEPTH),  # 3: into the Wreck Hall
    (70.0, -302.0, DEPTH),
    (96.0, -250.0, DEPTH),
    (82.0, -196.0, DEPTH),  # 6: the narrows
    (44.0, -150.0, DEPTH),  # 7: into Undertown
    (-24.0, -142.0, DEPTH),
    (-66.0, -92.0, DEPTH),
    (-42.0, -40.0, DEPTH),
    (8.0, -26.0, DEPTH),  # 11: out of Undertown, the Long Stair
    (36.0, 6.0, -16.0),
    (56.0, 46.0, -6.0),
    (72.0, 90.0, 3.0),  # 14: up into the light, out of the knoll
    (122.0, 120.0, 5.0),  # 15: the Edge
    (112.0, 156.0, 6.0),
    (52.0, 166.0, 7.0),  # 17: along the rim
    (6.0, 186.0, 9.0),  # 18: the bridgehead
    (-26.0, 250.0, 12.0),  # 19: the Sky Bridge
    (10.0, 320.0, 15.0),
    (-10.0, 390.0, 18.0),
    (0.0, 445.0, 20.0),  # 22: END, at the Sky Gate
    (0.0, 476.0, 20.0),  # 23: lead-out (no road)
    (250.0, 520.0, HZ),
    (480.0, 200.0, HZ),
    (450.0, -300.0, HZ),
    (150.0, -530.0, HZ),
    (-150.0, -530.0, HZ),
]
START, END = 1, 22
ENDS = {"start": ((-60.0, -440.0), (-70.0, -490.0)), "end": ((0.0, 445.0), (0.0, 476.0))}

# The caverns: (name, x, y, rx, ry, roof height over the road).
CAVERNS = [
    ("Wreck Hall", 52.0, -278.0, 64.0, 56.0, 16.0),
    ("Undertown", -6.0, -96.0, 84.0, 74.0, 21.0),  # (its roof breaks the seabed: the skylight)
    ("Sea Door Grotto", -55.0, -430.0, 30.0, 38.0, 31.0),  # (open overhead too: where you come in)
]
# The holes in the seabed over Undertown and the grotto: open to the sea overhead.
SKYLIGHTS = [(-6.0, -96.0, 34.0), (-55.0, -430.0, 20.0)]
SKYLIGHT = SKYLIGHTS[0]
KNOLL = (58.0, 52.0, 48.0, 44.0, 14.0)  # the rock the Long Stair climbs out through
# The Edge: the reef the road runs on, and the rim where the sea falls off the world.
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


def cavern_at(x, y):
    for name, cx, cy, rx, ry, _h in CAVERNS:
        e = math.hypot((x - cx) / rx, (y - cy) / ry)
        if e < 1.0:
            return name, e
    return None, 9.0


def _land(x, y):
    ry = rim_y(x)
    if y > ry:
        # Over the edge: a sheer fall to the void.
        return lerp(-2.0, VOID_Z, smooth((y - ry) / 7.0))
    if y < SLAB_N:
        # Under the seabed's slab: the caverns' floors; elsewhere hidden in the rock.
        name, e = cavern_at(x, y)
        if name:
            return DEPTH - 0.6 + 1.4 * smooth((e - 0.55) / 0.45) + 0.4 * math.sin(x / 7.0) * math.cos(y / 9.0)
        return DEPTH - 8.0
    # The Edge: the sea floor, and the reef the road runs on.
    sx, sy, sr = SHELF
    d = math.hypot((x - sx) * 0.9, y - sy)
    h = SEABED - 0.6 * smooth((y - SLAB_N) / 30.0)
    reef = 4.5 + 1.6 * math.sin(x / 9.0) * math.cos(y / 11.0) + 2.0 * smooth((60.0 - abs(x - 120.0)) / 40.0) * 0.0
    h = lerp(h, reef, smooth((sr - d) / 22.0))
    # (Rocks standing out of the sea along the rim, here and there.)
    h = max(h, (ry - y < 14.0) * (2.0 + 5.0 * max(0.0, math.sin(x / 23.0 + 1.3)) ** 3))
    return h


def natural(x, y):
    h = _land(x, y)
    d, z = road_floor(x, y)
    if y > rim_y(x) - 2.0 and d < 30.0:
        return h  # (the bridge: open under it)
    if d < 8.0:
        return z - 0.25
    if d < 20.0:
        return lerp(z - 0.25, h, smooth((d - 8.0) / 12.0))
    return h


def classify(c, n, info):
    ry = rim_y(c.x)
    if c.y > ry + 4.0 and c.z < -20.0:
        return ("cloud_bank", "abyss")  # (off the edge of the world: put back)
    if n.z < 0.62:
        return ("cave_rock", "wall") if c.y < SLAB_N else ("keep_rock", "wall")
    if c.y < SLAB_N:
        name, _ = cavern_at(c.x, c.y)
        if any(math.hypot(c.x - sx, c.y - sy) < sr + 6.0 for sx, sy, sr in SKYLIGHTS):
            return ("wreck_sand", "sand")  # (the floor under a skylight, sea-wet sand)
        return ("cave_rock", "dirt")
    if c.z < WATER_Z - 0.4:
        return ("cove_wet_sand", "deep_water")  # (off the reef into the sea)
    if math.sin(c.x / 17.0) * math.cos(c.y / 13.0) > 0.45:
        return ("keep_grass", "grass")
    return ("cove_rock", "dirt")


def main():
    c = kit.Course(TRACK_ID, "The Edge of the World", "dragon_isles")
    c.route(ROUTE, width=14.0, bank=5.0)
    c.kinds = {
        "under": {"mat": "keep_cobble", "shoulder": 1.4, "shoulder_mat": ("cave_rock", "dirt")},
        "edge": {"mat": "keep_cobble", "shoulder": 1.5, "shoulder_mat": ("cove_rock", "dirt")},
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
        return "under" if q.p.y < SLAB_N + 40.0 and q.p.z < 2.0 else "edge"

    c.roads(kit.plan(c, [(s0, s1, k) for s0, s1, k in kit.runs(c, label)], "under", max_len=160.0))

    X0, X1, Y0, Y1 = -490, 490, -490, 490
    ter = c.terrain("The Edge of the World", X0, X1, Y0, Y1, 4.0, natural, classify, near=8.0, fade=16.0)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 6.0, lambda x, y: natural(x, y) - 0.5, c.lib("cave_rock", "dirt"))

    def ground(x, y):
        z = c.ground_z(x, y, [ter])
        return natural(x, y) if z is None else z

    s_light = c.nearest(*ROUTE[14][:2])[0].s
    underground(c, s_start, s_light)
    sea_and_sky(c)
    undertown(c, ground)
    wreck_hall(c, ground)
    the_edge(c, ground)
    sky_bridge(c, s_end)
    ends(c)
    far_kingdom(c)
    # The air: the underground's dark, lantern-lit; the sky's bright, out at the edge.
    for x, y, look in ((-55.0, -430.0, "under"), (52.0, -278.0, "under"), (-6.0, -96.0, "skylight"), (20.0, -10.0, "under"),
                       (90.0, 120.0, "edge"), (0.0, 320.0, "edge")):
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
    "under": {"sky": "#0d1418", "fog": {"enabled": True, "color": "#14232a", "near": 30, "far": 260},
              "sun": {"color": "#9fd8ff", "intensity": 0.55, "direction": [-0.3, 0.9, 0.2]},
              "ambient": {"sky": "#5c8aa0", "ground": "#2a1c14", "intensity": 0.75}},
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
    """The seabed's rock, a slab over the whole underground, and the bores and caverns cut
    out of it; the knoll the Long Stair climbs out through."""
    bm = bmesh.new()
    x0, x1, y0, y1 = -490.0, 490.0, -490.0, SLAB_N
    zb, zt = DEPTH - 24.0, SEABED
    n = 24
    top = [[bm.verts.new((lerp(x0, x1, i / n), lerp(y0, y1, j / n), zt + 0.4 * math.sin(i * 1.7) * math.cos(j * 2.3)))
            for i in range(n + 1)] for j in range(n + 1)]
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
        cut = c.mesh_object(name + " Cutter", dm, "Rocks", "visual")
        _subtract(slab, cut)
    c.tunnel(slab, s0 - 30.0, s1, half=c.width / 2 + 4.0, height=11.0, pad=6.0)
    kx, ky, krx, kry, kz = KNOLL
    knoll = c.rock_mass("Knoll", kx, ky, krx, kry, kz, z0=DEPTH, n=22, seed=9,
                        bands=[(1.15, 0.0), (1.0, 0.3), (0.85, 0.7), (0.6, 1.0)])
    c.tunnel(knoll, s1 - 140.0, s1, half=c.width / 2 + 4.0, height=11.0, pad=10.0)
    c.paint_rock(knoll, ("keep_rock", "wall"), ("keep_grass", "grass"))
    groups = {}
    for p in slab.data.polygons:
        if p.normal.z > 0.6 and p.center.z > SEABED - 1.5:
            k = ("cove_wet_sand", "deep_water")
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


def undertown(c, ground):
    """The tunnel folk's town round Undertown: homes carved into the cavern's walls in two
    tiers (doors, lit windows, timber lintels, ledges and ladders), stalls and crates on the
    floor, coral and crystals glowing, and over it all the skylight: the sea, lit from
    above."""
    name, cx, cy, rx, ry, h = CAVERNS[1]
    sx, sy, sr = SKYLIGHT
    skylights(c, ground)
    k = 0
    for j in range(22):
        a = j * math.tau / 22 + 0.2
        for tier in (0, 1):
            e = 0.93 - 0.06 * tier
            x, y = cx + rx * e * math.cos(a), cy + ry * e * math.sin(a)
            if not paint.road_clear(c, x, y, 5.0):
                continue
            z = ground(x, y) + tier * 6.0
            rot = a + math.pi  # (facing in)
            ox, oy = x - 1.2 * math.cos(a), y - 1.2 * math.sin(a)
            box(c, "Undertown Door %d" % k, ox, oy, 0.2, 1.0, z - 0.2, z + 2.4, ("dark_corridor", "wall"), rot=rot, role="visual")
            box(c, "Undertown Lintel %d" % k, ox - 0.15 * math.cos(a), oy - 0.15 * math.sin(a), 0.25, 1.6, z + 2.4, z + 2.8,
                ("weathered_timber", "wall"), rot=rot, role="visual")
            for sd in (-1, 1):
                wx, wy = ox - sd * 2.4 * math.sin(a), oy + sd * 2.4 * math.cos(a)
                box(c, "Undertown Window %d %d" % (k, sd), wx, wy, 0.2, 0.55, z + 1.1, z + 2.0, ("window_warm", "wall"), rot=rot,
                    role="visual")
            if tier:
                box(c, "Undertown Ledge %d" % k, x - 2.0 * math.cos(a), y - 2.0 * math.sin(a), 1.6, 3.6, z - 0.5, z - 0.1,
                    ("plank_deck", "wall"), rot=rot, role="visual")
                lx, ly = x - 3.6 * math.cos(a), y - 3.6 * math.sin(a)
                box(c, "Undertown Ladder %d" % k, lx, ly, 0.08, 0.5, z - 6.0, z, ("weathered_timber", "wall"), rot=rot, role="visual")
            g = c.game(ox - 1.0 * math.cos(a), oy - 1.0 * math.sin(a), z + 3.2)
            if k % 2 == 0:
                c.entity("lantern", x=g[0], y=g[1], z=g[2])
            k += 1
    # The floor: crates and barrels, rowboats on blocks, stalls' awnings, a fire in the middle.
    for j in range(16):
        a = j * 2.399
        r = 0.35 + 0.45 * ((j * 0.618) % 1.0)
        x, y = cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)
        if not paint.road_clear(c, x, y, 4.0):
            continue
        z = ground(x, y)
        if j % 4 == 0:
            c.place(tp.rowboat(c), x, y, z + 0.6, rot=a)
        elif j % 4 == 1:
            box(c, "Stall %d" % j, x, y, 2.2, 1.4, z, z + 1.0, ("plank_deck", "wall"), rot=a)
            box(c, "Stall Awning %d" % j, x, y, 2.6, 1.8, z + 2.6, z + 2.75, (("awning_red", "awning_teal")[j % 2], "wall"), rot=a,
                role="visual")
            for sx_ in (-1, 1):
                box(c, "Stall Post %d %d" % (j, sx_), x + sx_ * 2.2 * math.cos(a), y + sx_ * 2.2 * math.sin(a), 0.1, 0.1, z, z + 2.6,
                    ("weathered_timber", "wall"), role="visual")
        else:
            c.place(tp.barrel(c), x, y, z - 0.1, rot=a)
    g = c.game(cx, cy, ground(cx, cy) + 0.2)
    c.entity("campfire", x=g[0], y=g[1], z=g[2])
    c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=min(rx, ry) * 0.6, n=9, folk="beach",
             heading=0.0)
    # Coral and crystals glowing round the walls' feet, and under the skylight.
    for j in range(34):
        a = j * math.tau / 34 + 0.1
        e = 0.82 + 0.1 * math.sin(j * 1.3)
        x, y = cx + rx * e * math.cos(a), cy + ry * e * math.sin(a)
        if not paint.road_clear(c, x, y, 3.0):
            continue
        z = ground(x, y)
        if j % 3 == 0:
            c.place(tp.coral(c, j % 3), x, y, z - 0.2, rot=a, role="visual")
        else:
            _glow_crystal(c, "Undertown Crystal %d" % j, x, y, z, 2.5 + 2.0 * ((j * 0.37) % 1.0), ("crystal_cyan", "crystal_teal")[j % 2])
    g = c.game(sx, sy, SEABED - 2.0)
    c.entity("sparkles", x=g[0], y=g[1], z=g[2], r=sr, rate=20)


def skylights(c, ground):
    """The holes in the seabed: the sea's water over them seen from below, and the sea
    spilling in round their rims in thin falls to pools on the floor."""
    for j, (sx, sy, sr) in enumerate(SKYLIGHTS):
        bm = bmesh.new()
        pts = [(sx + (sr + 6.0) * math.cos(a), sy + (sr + 6.0) * math.sin(a)) for a in [k * math.tau / 40 for k in range(40)]]
        bm.faces.new([bm.verts.new((x, y, SEABED + 1.2)) for x, y in pts])
        bm.faces.new([bm.verts.new((x, y, SEABED + 1.15)) for x, y in reversed(pts)])
        c.assign(c.mesh_object("Skylight %d" % j, bm, "Water", "visual"), c.lib("lagoon", "water"))
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
        if not on_reef and abs(x) > 14.0:
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
