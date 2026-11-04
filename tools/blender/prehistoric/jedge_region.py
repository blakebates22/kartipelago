# The last journey: Tropic Isles to the Dragon Kingdom, v4 (Blake, Nov 2: "rework the edge
# of the world passageway. the driving is very boring and the inside is lacking ... it
# should be crawling with black market activity. we need npcs, alot of them, and all sorts
# of stuff going on. different areas that are distinct ... and the drive to the dragon
# isle is also boring"). Builds journey_cause (it replaces Tidewyrm's Causeway,
# jcause_layout.py, kept unused).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/jedge_region.py
#
# The story's last smugglers' tunnel ("THE ONE UNDER THE BORDER"), driven: a chain of
# black-market districts under the seabed (jedge_layout.py has the road; jedge_districts.py
# dresses them), out through the cliff of the world's edge and a leap into the sky, then
# hopping the floating islands up to the Dragon Kingdom's Sky Gate.
#
# Blender coordinates (x east, y north, z up). The route is a loop (the kit's courses are),
# the road only from START to END; the rest goes round out of sight, high over everything.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import Vector, bmesh, lerp  # noqa: E402
from pocket_build import box, cone  # noqa: E402
import props  # noqa: E402
import region_paint as paint  # noqa: E402
import jedge_layout as L  # noqa: E402
from jedge_layout import (  # noqa: E402
    AT, CAVERNS, CLOUD_Z, ENDS, END, ISLES, MOUTH, isle_top, PIT, PIT_FLOOR, PIT_R, ROUTE, SEABED, SHELF, SKYLIGHTS,
    START, VOID_Z, WATER_Z, cavern_at, classify, isle_at, natural, over_canal, reef_z, rim_y)
import jedge_districts as D  # noqa: E402
import jedge_life as LIFE  # noqa: E402

TRACK_ID = "journey_cause" + os.environ.get("KP_REGION_SUFFIX", "")


def _s(c, tag, f=0.0):
    """The road's distance at a route point (or a fraction of the way to the next)."""
    i = AT[tag]
    (ax, ay, _, _), (bx, by, _, _) = ROUTE[i], ROUTE[(i + 1) % len(ROUTE)]
    return c.nearest(ax + (bx - ax) * f, ay + (by - ay) * f)[0].s


def main():
    c = kit.Course(TRACK_ID, "The Edge of the World", "dragon_isles")
    c.route(L.DENSE, width=14.0, bank=6.0)
    kinds = {
        # (the bores: old setts worn to mud)
        "under": {"mat": "ruin_road", "shoulder": 1.6, "shoulder_mat": ("bog_mud", "dirt")},
        # (the docks: plank quays)
        "quay": {"mat": "dock_cobble", "surface": "road", "shoulder": 1.2, "shoulder_mat": ("bog_dark_stone", "road")},
        # (the Night Bazaar: the market's old setts)
        "bazaar": {"mat": "imperial_setts", "surface": "road", "shoulder": 1.4, "shoulder_mat": ("ash_soil", "dirt")},
        # (the Fighting Pits: the arena's sand road, railed red and white down the wall)
        "pit": {"mat": "gulch_road", "surface": "road", "shoulder": 1.0, "shoulder_mat": ("gulch_sand", "dirt"), "barrier": 1.1,
                "barrier_mat": ("kerb_redwhite", "wall")},
        # (the Lucky Bone: the house's carpet)
        "den": {"mat": "palace_paving", "surface": "road", "shoulder": 1.4, "shoulder_mat": ("royal_carpet", "road")},
        # (the sky: the chained bridges, and the islands' stone roads)
        "bridge": {"mat": "plank_road", "surface": "road", "shoulder": 0.8, "shoulder_mat": ("plank_road", "road"), "barrier": 1.2,
                   "barrier_mat": ("rope_rail", "wall"), "deck": 1.4, "deck_mat": ("weathered_timber", "wall"), "ground": False},
        # (the canal's stone bridge: setts on a stone deck, a parapet, the water open under
        # its arch: jedge_harbour.bridge)
        "canal bridge": {"mat": "bridge_stone", "surface": "road", "shoulder": 0.8, "shoulder_mat": ("causeway_stone", "road"),
                         "barrier": 1.0, "barrier_mat": ("bog_stone", "wall"), "deck": 1.2,
                         "deck_mat": ("bog_stone", "wall"), "ground": False},
        # (low parapets along the islands' roads)
        "isle": {"mat": "keep_cobble", "surface": "road", "shoulder": 0.8, "shoulder_mat": ("keep_kerb", "road"), "barrier": 0.8,
                 "barrier_mat": ("keep_parapet", "wall"), "deck": 1.6, "deck_mat": ("keep_rock", "wall"), "ground": False},
    }
    c.kinds = kinds
    s_start = _s(c, "start")
    s_end = _s(c, "end")

    def place_kind(x, y):
        if y > rim_y(x) - 2.0:
            return "bridge" if isle_at(x, y, -1.0) is None else "isle"
        if over_canal(x, y):
            return "canal bridge"
        return {"Smugglers' Docks": "quay", "Night Bazaar": "bazaar", "Fighting Pits": "pit", "Lucky Bone": "den"}.get(
            cavern_at(x, y)[0], "under")

    def label(q):
        if not s_start <= q.s <= s_end:
            return None
        return place_kind(q.p.x, q.p.y)

    c.roads(kit.plan(c, list(kit.runs(c, label)), "under", max_len=150.0))

    X0, X1, Y0, Y1 = -490, 490, -490, 490
    ter = c.terrain("The Edge of the World", X0, X1, Y0, Y1, 4.0, natural, classify, near=8.0, fade=16.0, fine=2)
    sink_water(c, ter)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 6.0, lambda x, y: natural(x, y) - 0.5, c.lib("cave_rock", "dirt"))

    def ground(x, y):
        z = c.ground_z(x, y, [ter])
        return natural(x, y) if z is None else z

    s_mouth = _s(c, "mouth")
    underground(c, s_start, s_mouth)
    sea_and_sky(c)
    skylights(c, ground)
    D.dress(c, ground, s_start, s_mouth)
    the_edge(c)
    spans = sky(c, ground)
    ends(c)
    LIFE.all_life(c, ground, s_start, s_mouth, s_end, spans)
    far_kingdom(c)
    # The air: each district its own; the sky's bright, out at the edge.
    for x, y, look in ((-55.0, -430.0, "under"), (-40.0, -380.0, "under"), (-14.0, -300.0, "docks"), (60.0, -232.0, "under"),
                       (108.0, -140.0, "bazaar"), (40.0, -10.0, "pits"), (120.0, -40.0, "pits"), (152.0, 36.0, "den"),
                       (92.0, 112.0, "under"), (20.0, 220.0, "edge"), (0.0, 380.0, "edge")):
        g = c.game(x, y, 0.0)
        c.entity("air_spot", x=round(g[0], 1), z=round(g[2], 1), look=LOOKS[look])

    # (No zippers for now: Blake, Nov 4, "lets also remove the zippers for now".)
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
    print("people %d, talkers %d" % (D.CROWD_N[0], D.CROWD_N[1]))


LOOKS = {
    # (overworld/air.ts: an area's look, blended as you drive between them)
    # (the bores: smoky, the lamps' oily light)
    "under": {"sky": "#120e09", "fog": {"enabled": True, "color": "#2a2116", "near": 24, "far": 220},
              "sun": {"color": "#ffc98a", "intensity": 0.5, "direction": [-0.3, 0.9, 0.2]},
              "ambient": {"sky": "#9a7a58", "ground": "#2a1c10", "intensity": 0.8}},
    # (the docks: the black water's cold green light, mist off it)
    "docks": {"sky": "#0c1614", "fog": {"enabled": True, "color": "#24403a", "near": 40, "far": 300},
              "sun": {"color": "#c8f4e4", "intensity": 0.9, "direction": [-0.2, 0.95, 0.15]},
              "ambient": {"sky": "#8ac0b0", "ground": "#2a3a32", "intensity": 1.05}},
    # (the Night Bazaar: red and amber lantern light, cookfire smoke)
    "bazaar": {"sky": "#1a0c08", "fog": {"enabled": True, "color": "#4a2416", "near": 30, "far": 260},
               "sun": {"color": "#ffb27a", "intensity": 0.8, "direction": [-0.2, 0.95, 0.1]},
               "ambient": {"sky": "#e08a5a", "ground": "#3a1c10", "intensity": 0.95}},
    # (the Fighting Pits: brazier fire, dust over the sand)
    "pits": {"sky": "#1c0e06", "fog": {"enabled": True, "color": "#5a3418", "near": 40, "far": 320},
             "sun": {"color": "#ffcc80", "intensity": 1.0, "direction": [-0.15, 0.97, 0.1]},
             "ambient": {"sky": "#f0b070", "ground": "#5a3218", "intensity": 1.25}},
    # (the Lucky Bone: gold and plum)
    "den": {"sky": "#140a14", "fog": {"enabled": True, "color": "#3a1e34", "near": 24, "far": 200},
            "sun": {"color": "#ffd890", "intensity": 0.8, "direction": [-0.2, 0.95, 0.1]},
            "ambient": {"sky": "#c08ab0", "ground": "#2a1424", "intensity": 0.95}},
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
    districts' caverns and the Fighting Pits' drum cut out of it."""
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
    # The caverns: domes cut up from under their floors to their roofs.
    for name, cx, cy, rx, ry, floor, h in CAVERNS:
        dm = bmesh.new()
        res = bmesh.ops.create_uvsphere(dm, u_segments=32, v_segments=14, radius=1.0)
        for v in res["verts"]:
            wob = 1.0 + 0.07 * math.sin(v.co.x * 7.0 + v.co.y * 5.0) * (v.co.z > -0.2)
            v.co = Vector((cx + v.co.x * rx * wob, cy + v.co.y * ry * wob, floor - 3.0 + (v.co.z + 0.2) / 1.2 * (h + 3.0) * wob))
        _subtract(slab, c.mesh_object(name + " Cutter", dm, "Rocks", "visual"))
    # The Fighting Pits: a great drum, its roof domed over the arena.
    dm = bmesh.new()
    R = PIT_R[2]
    prof = [(0.0, PIT_FLOOR - 12.0), (R, PIT_FLOOR - 12.0), (R, -24.0), (R - 14.0, -12.0), (52.0, -8.0), (24.0, -6.0), (0.0, -5.4)]
    rings = []
    for r, z in prof:
        if r == 0.0:
            rings.append([dm.verts.new((PIT[0], PIT[1], z))])
            continue
        rings.append([dm.verts.new((PIT[0] + r * (1.0 + 0.03 * math.sin(3 * a)) * math.cos(a),
                                    PIT[1] + r * (1.0 + 0.03 * math.sin(3 * a)) * math.sin(a), z))
                      for a in [k * math.tau / 48 for k in range(48)]])
    for lo, hi in zip(rings, rings[1:]):
        if len(lo) == 1:
            for k in range(48):
                dm.faces.new((lo[0], hi[(k + 1) % 48], hi[k]))
        elif len(hi) == 1:
            for k in range(48):
                dm.faces.new((lo[k], lo[(k + 1) % 48], hi[0]))
        else:
            for k in range(48):
                dm.faces.new((lo[k], lo[(k + 1) % 48], hi[(k + 1) % 48], hi[k]))
    bmesh.ops.recalc_face_normals(dm, faces=dm.faces)
    _subtract(slab, c.mesh_object("Fighting Pits Cutter", dm, "Rocks", "visual"))
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


def _subtract(target, cutter):
    import bpy

    mod = target.modifiers.new("Cut", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
    mod.object = cutter
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter)


def skylights(c, ground):
    """The hole in the seabed over the grotto: the sea's water over it seen from below, and
    the sea spilling in round its rim in thin falls to pools on the floor."""
    for j, (sx, sy, sr) in enumerate(SKYLIGHTS):
        bm = bmesh.new()
        pts = [(sx + (sr + 6.0) * math.cos(a), sy + (sr + 6.0) * math.sin(a)) for a in [k * math.tau / 40 for k in range(40)]]
        bm.faces.new([bm.verts.new((x, y, SEABED + 1.2)) for x, y in pts])
        bm.faces.new([bm.verts.new((x, y, SEABED + 1.15)) for x, y in reversed(pts)])
        c.assign(c.mesh_object("Skylight %d" % j, bm, "Water", "visual"), c.lib("canyon_river", "water"))
        for k in range(4):
            a = k * math.tau / 4 + 0.7 * j
            lx, ly = sx + (sr - 2.0) * math.cos(a), sy + (sr - 2.0) * math.sin(a)
            if not paint.road_clear(c, lx, ly, 3.0):
                continue
            foot = ground(lx, ly)
            props.falls(c, "Skylight Falls %d %d" % (j, k), lx, ly, SEABED - 0.5, foot + 0.3, 1.6, 3.0, facing=1, throw=1.5, bulge=0.4,
                        veils=2, angle=a + math.pi / 2, mats=("falls_oasis", "falls_curtain_oasis", "falls_foam"))
            c.disc("Skylight Pool %d %d" % (j, k), lx, ly, 3.6, foot + 0.12, c.lib("lagoon_shallow", "water"), role="visual", n=16,
                   wobble=0.2, seed=k)


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
    c.disc("Cloud Sea", 0.0, 400.0, 1600.0, CLOUD_Z, c.lib("cloud_bank", "abyss"), role="visual", n=64)


def the_edge(c):
    """The sea falling off the rim of the world: falls all along it but where the reef is
    and over the Long Bore's mouth, pouring down into the clouds."""
    x = -470.0
    k = 0
    while x < 470.0:
        w = 34.0 + 10.0 * math.sin(x / 31.0)
        ry = rim_y(x)
        on_reef = math.hypot((x - SHELF[0]) * 0.9, ry - SHELF[1]) < SHELF[2] - 6.0
        if not on_reef and abs(x - MOUTH[0]) > 26.0:
            props.falls(c, "Edge Falls %d" % k, x, ry + 1.0, WATER_Z + 0.2, CLOUD_Z + 2.0, w, w * 1.3, facing=1, throw=8.0, bulge=1.8,
                        veils=3 if k % 2 else 2, foam=False, mats=("falls_oasis", "falls_curtain_oasis", "falls_foam"))
        x += w * 0.92
        k += 1
    for j in range(8):
        g = c.game(-300.0 + j * 85.0, rim_y(-300.0 + j * 85.0) + 6.0, WATER_Z - 6.0)
        c.entity("steam", x=g[0], y=g[1], z=g[2])
    # The mouth: timber shoring round the bore's end in the cliff, lanterns, a warning skull.
    q, _ = c.nearest(MOUTH[0], rim_y(MOUTH[0]) - 1.0)
    rot = math.atan2(q.t.y, q.t.x)
    for sd in (-1, 1):
        px, py = q.p.x + q.r.x * sd * (q.w / 2 + 10.0), q.p.y + q.r.y * sd * (q.w / 2 + 10.0)
        box(c, "Mouth Post %d" % sd, px, py, 0.7, 0.7, q.p.z - 1.0, q.p.z + 10.0, ("weathered_timber", "wall"), rot=rot)
        g = c.game(px - q.t.x * 1.0, py - q.t.y * 1.0, q.p.z + 7.0)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
    box(c, "Mouth Lintel", q.p.x, q.p.y, 0.8, q.w / 2 + 11.0, q.p.z + 10.0, q.p.z + 11.0, ("weathered_timber", "wall"), rot=rot,
        role="visual")


def sink_water(c, ter):
    """The land kept under the docks' water (review 1 note 1, "the water looks weird here"):
    near the canal's bridge the roads pulled the land up through the water. Every vertex in
    the water (or on its very edge) goes back down to the land's own height, and a face left
    under the water is the black water (put back if you fall in)."""
    mw = ter.matrix_world
    inv = mw.inverted()
    n = 0
    for v in ter.data.vertices:
        p = mw @ v.co
        if L.in_water(p.x, p.y) or L.in_water(p.x + 0.7, p.y) or L.in_water(p.x - 0.7, p.y) or L.in_water(p.x, p.y + 0.7) \
                or L.in_water(p.x, p.y - 0.7):
            z = natural(p.x, p.y)
            if p.z > z + 0.05:
                v.co = inv @ Vector((p.x, p.y, z))
                n += 1
    deep = c.lib("bog_mud", "deep_water")
    mats = ter.data.materials
    idx = next((i for i, m in enumerate(mats) if m == deep), None)
    if idx is None:
        mats.append(deep)
        idx = len(mats) - 1
    k = 0
    for f in ter.data.polygons:
        p = mw @ f.center
        if L.in_water(p.x, p.y) and p.z < L.DOCK_WATER - 0.2 and f.material_index != idx:
            f.material_index = idx
            k += 1
    ter.data.update()
    print("water: %d land vertices sunk, %d faces made black water" % (n, k))


def _float_isle(c, name, x, y, r, top, seed):
    """A floating island: a grassy top, its rock tapering away beneath to a crag."""
    depth = r * 1.5
    bm = bmesh.new()
    n = 24
    rings = []
    for scale, dz in ((0.96, 0.0), (1.0, -0.8), (0.97, -2.2), (0.8, -0.25 * depth), (0.55, -0.5 * depth), (0.3, -0.75 * depth),
                      (0.08, -depth)):
        ring = []
        for i in range(n):
            a = i * math.tau / n
            k = scale * (1 + 0.08 * math.sin(3 * a + seed) + 0.06 * math.sin(7 * a + seed * 1.7)) if dz else scale
            ring.append(bm.verts.new((x + r * k * math.cos(a), y + r * k * 0.95 * math.sin(a), top + dz * (1 + 0.1 * math.sin(5 * a + seed)))))
        rings.append(ring)
    for hi, lo in zip(rings, rings[1:]):
        for i in range(n):
            bm.faces.new((hi[i], hi[(i + 1) % n], lo[(i + 1) % n], lo[i]))
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return c.mesh_object(name, bm, "Rocks")


def _tower(c, name, x, y, z, rot, foot):
    """A stone tower on an island's rim, the bridge's chains slung from its top."""
    box(c, name, x, y, 1.6, 1.6, foot, z + 16.0, ("keep_rock", "wall"), rot=rot)
    cone(c, name + " Cap", x, y, 2.4, z + 16.0, 4.5, ("roof_jade", "wall"), segs=4, role="visual")
    g = c.game(x, y, z + 6.0)
    c.entity("torch", x=g[0], y=g[1], z=g[2])


def sky(c, ground):
    """The Sky Islands: floating rocks under the islands' roads (grass on top, falls off
    them into the clouds), the chained bridges between them on stone towers, and the
    islands' life (jedge_districts.sky_life)."""
    for k, (name, x, y, r, z) in enumerate(ISLES):
        top = isle_top(k)  # (the grass all but flush with the road, never over it)
        rm = _float_isle(c, name, x, y, r, top, 60 + k)
        c.paint_rock(rm, ("keep_rock", "wall"), ("keep_grass", "grass"))
        for j in range(2 + k % 2):
            a = j * 2.4 + k
            fx, fy = x + r * 0.9 * math.cos(a), y + r * 0.9 * math.sin(a)
            if paint.road_clear(c, fx, fy, 3.0):
                props.falls(c, "Isle Falls %d %d" % (k, j), fx, fy, top - 0.2, CLOUD_Z + 4.0, 2.6, 5.0, facing=1, throw=3.0, veils=2,
                            foam=False, angle=a + math.pi / 2, mats=("falls_oasis", "falls_curtain_oasis", "falls_foam"))
    # The chained bridges: a tower each side at both ends, the chains between.
    spans = []
    s = None
    s_end = c.nearest(*ROUTE[END][:2])[0].s
    for q in c.S:
        if q.s > s_end + 2.0:
            break
        on = q.p.y > rim_y(q.p.x) + 1.0 and isle_at(q.p.x, q.p.y, -1.0) is None
        if on and s is None:
            s = q.s
        elif not on and s is not None:
            if q.s - s > 6.0:
                spans.append((s, q.s))
            s = None
    out = []
    for a_s, b_s in spans:
        ends = [c.at(a_s - 2.0), c.at(b_s + 2.0)]
        tops = []
        for e, q in enumerate(ends):
            rot = math.atan2(q.t.y, q.t.x)
            pair = []
            for sd in (-1, 1):
                px, py = q.p.x + q.r.x * sd * (q.w / 2 + 3.4), q.p.y + q.r.y * sd * (q.w / 2 + 3.4)
                _tower(c, "Bridge Tower %d %d %d" % (int(a_s), e, sd), px, py, q.p.z, rot, q.p.z - 8.0)
                pair.append((px, py, q.p.z + 15.0))
            tops.append(pair)
        out.append((a_s, b_s, (tops[0], tops[1])))
        for sd in (0, 1):
            pts = []
            for j in range(15):
                t = j / 14
                q = c.at(lerp(a_s - 2.0, b_s + 2.0, t))
                sg = 1 if sd else -1
                sag = min(13.0, 0.3 * (b_s - a_s + 4.0)) * (1.0 - (2 * t - 1) ** 2)
                pts.append((q.p.x + q.r.x * sg * (q.w / 2 + 1.4), q.p.y + q.r.y * sg * (q.w / 2 + 1.4), lerp(tops[0][sd][2], tops[1][sd][2], t)
                            - sag))
            pts[0], pts[-1] = tops[0][sd], tops[1][sd]
            bm = bmesh.new()
            props.tube(bm, pts, 0.32, n=6)
            c.assign(c.mesh_object("Bridge Chain %d %d" % (int(a_s), sd), bm, "Props", "visual"), c.lib("iron", "wall"))
            for j in range(2, 13, 2):
                x, y, z = pts[j]
                q = c.at(lerp(a_s - 2.0, b_s + 2.0, j / 14))
                bm = bmesh.new()
                props.tube(bm, [(x, y, z), (x, y, q.p.z + 1.2)], 0.07, n=4)
                c.assign(c.mesh_object("Bridge Hanger %d %d %d" % (int(a_s), sd, j), bm, "Props", "visual"), c.lib("iron", "wall"))
    D.sky_life(c, ground)
    return out


def ends(c):
    """The start: the bore back to the isles' sea door, walled off past its gate. The end:
    the Sky Gate, colossal, two great piers and a lintel over the road's end, dragon heads
    on them, the Dragon Kingdom beyond (the loading zone just before it)."""
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
    z = q.p.z
    gx, gy = zx, zy + 12.0
    for sd in (-1, 1):
        px = gx + sd * 15.0
        box(c, "Sky Gate Pier %d" % sd, px, gy, 4.0, 4.0, z - 40.0, z + 44.0, ("keep_rock", "wall"))
        cone(c, "Sky Gate Head %d" % sd, px, gy - 4.0, 3.2, z + 30.0, 12.0, ("gold_trim", "wall"), segs=6, role="visual")
        g = c.game(px, gy - 5.0, z + 8.0)
        c.entity("torch", x=g[0], y=g[1], z=g[2])
    box(c, "Sky Gate Lintel", gx, gy, 19.0, 4.5, z + 40.0, z + 46.0, ("keep_rock", "wall"), role="visual")
    box(c, "Sky Gate Floor", gx, zy + 16.0, 13.0, 17.0, z - 12.0, z - 0.15, ("keep_cobble", "road"))


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
