# Boss races: prototypes (greyboxes) of one boss race per world, to drive before anything
# else is decided (Blake, Oct 25: "lets get some prototypes of these. lets let 3 of them be
# 3 lappers, and 2 be a more of a line one lap style"). Working names; the bosses, the
# story round them and the dressing all come later.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/boss_races.py <id>      (the bpy module)
#
#   boss_prehistoric  Tyrant's Gorge, 3 laps: a figure of eight, the second loop crossing
#                     over the first on a bridge, a jump over the gully.
#   boss_desert       Mesa Rush, 3 laps: big banked sweepers round a mesa, a jump over a
#                     canyon on the back straight, a chicane.
#   boss_tropic       Atoll Dash, 3 laps: three islets, a plank bridge, a jump and a
#                     causeway of humps between them.
#   boss_snowy        Avalanche Run, one long lap: switchbacks down the mountain, an ice
#                     bridge, the ski jump onto the valley floor, the long climb back.
#   boss_dragon       The Citadel, one long lap: over the chasm bridge, up the castle hill,
#                     along the ramparts, the leap off the battlements, down through the town.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp, smooth  # noqa: E402
from pocket_build import box  # noqa: E402

# Each: layout, closing straights, start pose, heights at segment starts, decked segments
# (bridges, the road on posts), jumps (segment, metres into it, gap, drop, kick), zippers
# (segment, metres into it), laps, materials, and the ground's base level.
PREHISTORIC = {
    # Cinderjaw's Caldera (Blake, Oct 26: every boss race a mechanic to master): the
    # figure of eight now over a lava lake in a volcano's caldera. Cinderjaw's breath
    # sweeps across the straights on a beat (their glow first): drive through it burning
    # and you take heat; the cooled-crust vents on the bends' inside lines take it away
    # and fire a zipper; a full gauge overheats you. The alternative: the straights
    # crumble into the lava behind whoever's leading (game/bossMech.ts).
    "name": "Cinderjaw's Caldera",
    "theme": "ember_volcano",
    "laps": 3,
    "start": (0.0, 0.0), "head": 45.0,
    "layout": [("S", 150), ("L", 55, 270), ("S", 150), ("R", 55, 270)],
    "close": (0, 2),
    "heights": {0: 1.0, 1: 2.0, 2: 9.0, 3: 6.0},
    "deck": [2],
    "jumps": [(3, 150.0, 12.0, 2.0, 0.9)],
    "zippers": [(0, 30), (3, 110)],
    "mats": {"road": "basalt_road", "ground": ("ash_soil", "dirt"), "shoulder": ("scorched_ground", "dirt"),
             "wall": ("obsidian_cliff", "wall"), "deck": "wood_planks", "rail": ("palm_bark", "wall")},
    "base": -4.0,
    "lava": True,
    # Cinderjaw's mechanics: sweeps (segment, metres in, period, offset), vents (segment,
    # fraction round the bend, across), the crumbling stretches (segment, from, to).
    "sweeps": [(0, 55.0, 4.6, 0.0), (0, 105.0, 4.6, 2.3), (2, 45.0, 5.0, 1.2), (2, 110.0, 5.0, 3.7)],
    "vents": [(1, 0.35, -4.0), (1, 0.7, -4.0), (3, 0.35, 4.0), (3, 0.7, 4.0)],
    "crumble": [(0, 10.0, 140.0), (2, 10.0, 140.0)],
}
DESERT = {
    "name": "Mesa Rush (boss, proto)",
    "theme": "canyon_dash",
    "laps": 3,
    "start": (0.0, 0.0), "head": 0.0,
    "layout": [("S", 200), ("L", 60, 120), ("S", 60), ("R", 40, 40), ("L", 40, 80), ("R", 40, 40), ("S", 60), ("L", 60, 120), ("S", 120),
               ("L", 60, 120)],
    "close": (2, 8),
    "heights": {0: 2.0, 1: 2.0, 2: 6.0, 3: 7.0, 4: 7.0, 5: 6.0, 6: 5.0, 7: 4.0, 8: 3.0, 9: 2.0},
    "deck": [],
    "jumps": [(0, 110.0, 14.0, 2.0, 1.0)],
    "zippers": [(0, 50), (2, 10), (8, 20)],
    # Scorchwind's mechanics: crosswind gusts (the sand streams across first) shoving you
    # toward the quicksand on the road's edge, rock pillars to shelter behind, the canyon
    # jump carried further on a tailwind. The alternative: a sandstorm, beacon fires
    # marking the way.
    "gusts": [(0, 40.0, 1, 40.0, 5.5, 0.0), (0, 160.0, 1, 40.0, 5.5, 2.0), (8, 60.0, -1, 50.0, 6.0, 1.0),
              (6, 30.0, 1, 34.0, 5.0, 3.0)],
    "shelters": [(0, 30.0, -1, 11.0), (0, 150.0, -1, 11.0), (8, 50.0, 1, 11.0)],
    "tailwinds": [(0, 124.0)],
    "sandstorm": [(0.85, "alt")],
    "quicksand": True,
    "mats": {"road": "dash_road", "ground": ("red_sand", "loose_sand"), "shoulder": ("dash_shoulder", "dirt"), "wall": ("strata_orange", "wall"),
             "deck": "plank_deck", "rail": ("fence_rail", "wall")},
    "base": 0.0,
    "bank": 12.0,
}
TROPIC = {
    "name": "Atoll Dash (boss, proto)",
    "theme": "beach_party",
    "laps": 3,
    "start": (0.0, 0.0), "head": 0.0,
    "layout": [("S", 40), ("S", 70), ("S", 30), ("L", 30, 120), ("S", 40), ("S", 90), ("S", 20), ("L", 30, 120), ("S", 30), ("S", 80), ("S", 30),
               ("L", 30, 120)],
    "close": (4, 8),
    "heights": {0: 2.0, 1: 3.0, 2: 2.2, 3: 2.2, 4: 2.2, 5: 3.0, 6: 2.4, 7: 2.4, 8: 2.4, 9: 2.4, 10: 2.2, 11: 2.0},
    "deck": [1],
    "coil_segs": [5],
    "humps": {9: (4, 1.0)},
    "jumps": [(5, 50.0, 12.0, 2.0, 0.9)],
    "zippers": [(0, 20), (4, 20), (8, 10)],
    # Tidewyrm's mechanics: the tide rising and falling as he thrashes (the sandbar across
    # the lagoon a shortcut only at low tide), his coils surfacing as the bridge between
    # the islets (only while they're up). The alternative: whirlpools that swing you
    # round and fling you on.
    "tide": [(14.0, -1.4, 1.0)],
    "sandbars": [((2, 10.0), (4, 30.0))],
    "coils": [(5,)],
    "whirlpools": [(4, 50.0, "alt"), (8, 40.0, "alt"), (0, 60.0, "alt")],
    "mats": {"road": "beach_road", "ground": ("beach_sand", "soft_sand"), "shoulder": ("beach_sand", "sand"), "wall": ("valley_cliff", "wall"),
             "deck": "wood_planks", "rail": ("tiki_wood", "wall")},
    "base": -3.0,
    "sea": True,
}
SNOWY = {
    "name": "Avalanche Run (boss, proto)",
    "theme": "summit_pass",
    "laps": 1,
    "start": (0.0, 0.0), "head": 180.0,
    "layout": [("S", 140), ("L", 30, 180), ("S", 140), ("R", 30, 180), ("S", 140), ("L", 30, 180), ("S", 140), ("R", 40, 90),
               ("S", 260), ("L", 45, 90), ("S", 200), ("L", 45, 90), ("S", 100), ("R", 60, 50), ("L", 60, 100), ("R", 60, 50),
               ("S", 120), ("L", 45, 90), ("S", 100)],
    "close": (16, 18),
    "heights": {0: 40.0, 1: 38.0, 2: 36.0, 3: 30.0, 4: 28.0, 5: 22.0, 6: 20.0, 7: 15.0, 8: 14.0, 9: 4.0, 10: 4.0, 11: 4.0, 12: 6.0,
                13: 12.0, 14: 18.0, 15: 26.0, 16: 30.0, 17: 38.0, 18: 40.0},
    "deck": [6],
    "jumps": [(8, 120.0, 22.0, 4.0, 1.2)],
    "zippers": [(2, 20), (8, 70), (10, 20), (16, 20)],
    # Rimefang's mechanics: walls of ice rising across one lane of the divided straights
    # (the frost cracks first: be in the other lane), then his avalanche chasing you down
    # the mountain. The alternative: the valley floor a frozen lake that cracks if you
    # linger.
    "dividers": [(2, 15.0, 128.0), (4, 15.0, 128.0)],
    "ice_walls": [(2, 35.0, -1, 3.6, 0.0), (2, 70.0, 1, 3.6, 1.8), (2, 105.0, -1, 3.6, 0.9),
                  (4, 35.0, 1, 3.6, 0.4), (4, 70.0, -1, 3.6, 2.2), (4, 105.0, 1, 3.6, 1.3)],
    "avalanche": [(5, 9, 70.0, 26.0)],
    "thin_lake": [(9, 11, "alt")],
    "mats": {"road": "summit_road", "ground": ("summit_snow", "deep_snow"), "shoulder": ("summit_snow", "packed_snow"), "wall": ("summit_cliff", "wall"),
             "deck": "plank_road", "rail": ("rope_rail", "wall")},
    "base": 0.0,
}
DRAGON = {
    "name": "The Citadel (boss, proto)",
    "theme": "dragonspire_keep",
    "laps": 1,
    "start": (0.0, 0.0), "head": 90.0,
    "layout": [("S", 60), ("S", 160), ("S", 40), ("R", 45, 90), ("S", 60), ("L", 30, 180), ("S", 80), ("R", 30, 180), ("S", 80),
               ("L", 40, 90), ("S", 200), ("L", 40, 90), ("S", 60), ("S", 30), ("S", 80), ("L", 50, 90), ("S", 140), ("R", 40, 60),
               ("L", 40, 120), ("R", 40, 60), ("S", 120), ("L", 50, 90), ("S", 60)],
    "close": (16, 22),
    "heights": {0: 5.0, 1: 5.0, 2: 6.0, 3: 8.0, 4: 12.0, 5: 18.0, 6: 20.0, 7: 26.0, 8: 28.0, 9: 34.0, 10: 36.0, 11: 36.0, 12: 36.0,
                13: 37.0, 14: 22.0, 15: 18.0, 16: 15.0, 17: 11.0, 18: 9.0, 19: 7.0, 20: 6.0, 21: 5.0, 22: 5.0},
    "deck": [1, 10, 11, 12],
    "jumps": [(13, 30.0, 16.0, 6.0, 0.9)],
    "zippers": [(0, 20), (10, 40), (12, 20), (16, 30)],
    # King Pyrrhax: the first race, a wall of fire chasing you up the castle hill; the
    # rematch (the alternative), his fireballs (AURIN'S LIGHT sends them back) and a
    # gauntlet of each kingdom's trial: Cinderjaw's sweeps, Rimefang's walls, Scorchwind's
    # wind, Tidewyrm's whirlpool.
    "firewall": [(2, 12, 60.0, 25.0)],
    "fireball": [(5.0, 30.0, "alt")],
    "sweeps_alt": [(10, 60.0, 4.6, 0.0), (10, 140.0, 4.6, 2.3)],
    "dividers": [(16, 20.0, 120.0, "alt")],
    "ice_walls": [(16, 45.0, -1, 3.6, 0.0, "alt"), (16, 90.0, 1, 3.6, 1.8, "alt")],
    "gusts": [(20, 50.0, 1, 40.0, 5.5, 0.0, "alt")],
    "whirlpools": [(4, 30.0, "alt")],
    "mats": {"road": "keep_cobble", "ground": ("keep_grass", "grass"), "shoulder": ("keep_path", "dirt"), "wall": ("keep_rock", "wall"),
             "deck": "keep_flag", "rail": ("keep_parapet", "wall")},
    "base": 0.0,
    "chasm": 1,
}
SPECS = {"boss_prehistoric": PREHISTORIC, "boss_desert": DESERT, "boss_tropic": TROPIC, "boss_snowy": SNOWY, "boss_dragon": DRAGON}


def build(track_id):
    sp = SPECS[track_id]
    layout, path = kit.close_turtle(sp["layout"], sp["close"][0], sp["close"][1], sp["start"], sp["head"])
    seg_d = kit.segment_starts(path)
    length = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path, path[1:]))
    H = sp["heights"]
    n = len(layout)

    def seg_of(d):
        k = 0
        for i, s in seg_d.items():
            if s <= d:
                k = max(k, i)
        return k

    def base_z(d, seg):
        a, b = seg_d[seg], seg_d.get(seg + 1, length)
        t = (d - a) / max(1e-6, b - a)
        z = lerp(H[seg], H.get(seg + 1, H[0]) if seg + 1 < n else H[0], smooth(t))
        hm = sp.get("humps", {}).get(seg)
        if hm:
            z += hm[1] * math.sin(t * math.pi * hm[0]) ** 2
        return z

    jumps = [(seg_d[s] + off, seg_d[s] + off + gap, drop, kick) for s, off, gap, drop, kick in sp["jumps"]]
    road_z = kit.with_jumps(base_z, seg_of, jumps)
    route = kit.route_points_by(path, road_z, every=8.0, width=lambda d, s: 16.0 if s == 0 else 15.0)
    to_road, to_plan = kit.along(path, road_z)

    # The land: at about the road's height near it (never rising under a deck), the
    # base level away from it, gentle hills; the sea round the tropic islets; a chasm
    # under the citadel's bridge.
    pts = []
    dd = 0.0
    for i, p in enumerate(path):
        if i:
            dd += math.hypot(p[0] - path[i - 1][0], p[1] - path[i - 1][1])
        if i % 3 == 0 and p[3] not in sp["deck"]:
            pts.append((p[0], p[1], road_z(dd, p[3])))
    deck_pts = []
    dd = 0.0
    for i, p in enumerate(path):
        if i:
            dd += math.hypot(p[0] - path[i - 1][0], p[1] - path[i - 1][1])
        if i % 3 == 0 and p[3] in sp["deck"]:
            deck_pts.append((p[0], p[1]))

    from mathutils import kdtree

    tree = kdtree.KDTree(len(pts))
    for k, (px, py, _) in enumerate(pts):
        tree.insert((px, py, 0.0), k)
    tree.balance()
    dtree = kdtree.KDTree(max(1, len(deck_pts)))
    for k, (px, py) in enumerate(deck_pts):
        dtree.insert((px, py, 0.0), k)
    dtree.balance()

    def natural(x, y):
        _, k, d = tree.find((x, y, 0.0))
        best = pts[k][2]
        hills = 1.5 * math.sin(x / 37.0) * math.cos(y / 29.0) + 3.0 * smooth((d - 40) / 60)
        if sp.get("sea"):
            return lerp(best - 0.5, sp["base"], smooth((d - 14) / 14))
        if sp.get("lava"):
            # The lava lake round the road, the caldera's walls far out.
            h = lerp(best - 0.5, sp["base"], smooth((d - 13) / 10))
            return h + 40.0 * smooth((d - 120) / 60)
        h = lerp(best - 0.5, sp["base"] + max(0.0, best - sp["base"]) * 0.6 + hills, smooth((d - 16) / 50))
        dk = dtree.find((x, y, 0.0))[2] if deck_pts else 1e9
        if dk < 30 and dk < d:
            h = lerp(h, sp["base"] - (12.0 if sp.get("chasm") else 0.0), smooth((30 - dk) / 18))
        return h

    m = sp["mats"]

    def classify(c, nrm, info):
        if nrm.z < 0.6:
            return m["wall"]
        if sp.get("quicksand") and 9.0 < info["d"] < 30.0:
            return ("gold_sand", "mud")  # (Scorchwind's quicksand by the road)
        if sp.get("lava") and c.z < sp["base"] + 1.5 and info["d"] > 14:
            return ("volcano_lava", "lava")
        if sp.get("sea") and c.z < 0.4:
            return ("wet_sand", "deep_water") if c.z < -0.4 else ("wet_sand", "sand")
        if info["d"] < 12:
            return m["shoulder"]
        return m["ground"]

    c = kit.Course(track_id, sp["name"], sp["theme"])
    c.route(route, width=15.0, bank=sp.get("bank", 7.0))
    c.kinds = {
        "road": {"mat": m["road"], "surface": "road", "shoulder": 1.6, "shoulder_mat": m["shoulder"]},
        "deck": {"mat": m["deck"], "surface": "road", "shoulder": 0.4, "shoulder_mat": (m["deck"], "road"), "barrier": 1.1, "barrier_mat": m["rail"],
                 "deck": 2.0, "deck_mat": (m["deck"], "road"), "ground": False},
        "kicker": {"mat": m["deck"], "surface": "road", "shoulder": 0.4, "shoulder_mat": (m["deck"], "road"), "deck": 2.0,
                   "deck_mat": (m["deck"], "road"), "ground": False},
    }
    # Tidewyrm's coils: the bridge you drive along his back (scaly, no rails).
    c.kinds["coil"] = {"mat": "em_cliff", "surface": "road", "shoulder": 0.4, "shoulder_mat": ("em_cliff", "road"),
                       "deck": 2.0, "deck_mat": ("em_cliff", "road"), "ground": False}
    gaps = [(to_road(l), to_road(r)) for l, r, _, _ in jumps]

    def label(smp):
        s = smp.s
        for l, r in gaps:
            if l <= s <= r:
                return "gap"
            if l - 12 <= s < l:
                return "kicker"
        if seg_of(to_plan(s)) in sp.get("coil_segs", []):
            return "coil"
        return "deck" if seg_of(to_plan(s)) in sp["deck"] else "road"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "kicker":
            specials.append((s0, s1, "kicker", {"lift": lambda u, n: 0.6 * max(0.0, (u - (n - 8)) / 8) ** 2}))
        elif k != "road":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "road", max_len=150.0))

    xs = [p[0] for p in path]
    ys = [p[1] for p in path]
    X0, X1, Y0, Y1 = min(xs) - 160, max(xs) + 160, min(ys) - 160, max(ys) + 160
    ter = c.terrain("Land", X0, X1, Y0, Y1, 4.0, natural, classify, near=9.0, fade=12.0, under=0.2)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 4.0, lambda x, y: natural(x, y) - 0.6, c.lib(*m["ground"]))
    if sp.get("sea"):
        c.ribbon("Sea", [(x, (Y0 + Y1) / 2) for x in range(int(X0) - 1400, int(X1) + 1401, 200)], (Y1 - Y0) + 2800, 0.0, c.lib("sea_water"),
                 role="visual", steps=2)
    for piece in c.pieces:
        if piece.name.endswith("deck") or piece.name.endswith("kicker"):
            kit.clear_piers(c, piece, [ter], every=9.0, mat=m["rail"], size=0.9, inset=1.5)
    c.start_line()
    for seg, off in sp["zippers"]:
        c.zipper(to_road(seg_d[seg] + off), 0)
    mechanics(c, sp, seg_d, to_road, length)
    extra_mechanics(c, sp, seg_d, to_road, length, natural)
    for k, (l, r) in enumerate(gaps):
        c.entity("respawn", **{"from": round(l - 20, 1), "to": round(r + 4, 1), "at": round(r + 18, 1)})
    for i in range(1, n, 3):
        c.balloon(to_road(seg_d[i]) + 10, 0, ("red", "blue", "green", "yellow", "rainbow")[i % 5])
    c.checkpoints(extra=[to_road(seg_d[i]) + 5 for i in range(1, n, 2)], avoid=[(l - 16, r + 10) for l, r in gaps], height=10.0)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish(extra={"race": {"laps": sp["laps"]}})
    print(track_id, "lap", round(c.length, 1), "laps", sp["laps"])


def mechanics(c, sp, seg_d, to_road, length):
    """The boss's mechanics as entities (src/game/bossMech.ts): Cinderjaw's fire sweeps
    and crust vents (main), the crumbling straights (alt)."""
    def heading(q):
        return math.atan2(q.t.x, -q.t.y)  # (game heading: x east, z = -blender y)

    sweeps = [(*e, {}) for e in sp.get("sweeps", [])] + [(*e, {"variant": "alt"}) for e in sp.get("sweeps_alt", [])]
    for seg, off, period, offset, var in sweeps:
        q = c.at(to_road(seg_d[seg] + off))
        g = c.game(q.p.x, q.p.y, q.p.z)
        c.entity("fire_sweep", x=round(g[0], 2), y=round(g[1], 2), z=round(g[2], 2), heading=round(heading(q), 4),
                 width=round(q.w + 4.0, 1), depth=4.0, period=period, offset=offset, warn=1.4, burn=1.3, **var)
        # The vents its fire comes up from, either side.
        for sd in (-1, 1):
            x, y = q.p.x + q.r.x * sd * (q.w / 2 + 3.0), q.p.y + q.r.y * sd * (q.w / 2 + 3.0)
            g2 = c.game(x, y, q.p.z + 0.5)
            c.entity("steam", x=g2[0], y=g2[1], z=g2[2])
    for seg, frac, across in sp.get("vents", []):
        a, b = seg_d[seg], seg_d.get(seg + 1, length)
        q = c.at(to_road(a + (b - a) * frac))
        x, y = q.p.x + q.r.x * across, q.p.y + q.r.y * across
        g = c.game(x, y, q.p.z)
        c.entity("crust_vent", x=round(g[0], 2), y=round(g[1], 2), z=round(g[2], 2), r=3.0)
    for seg, s0, s1 in sp.get("crumble", []):
        c.entity("crumble", variant="alt", **{"from": round(to_road(seg_d[seg] + s0), 1),
                                              "to": round(to_road(seg_d[seg] + s1), 1)}, gap=45.0)


def extra_mechanics(c, sp, seg_d, to_road, length, natural):
    """The other bosses' mechanics (src/game/bossMechs.ts) from the spec: Rimefang's ice
    walls (and the lane dividers they need), avalanche and thin lake; Scorchwind's gusts,
    shelters, tailwinds and sandstorm; Tidewyrm's tide, sandbars and coils, and his
    whirlpools; the King's fire wall and fireballs. Each spec entry may end in "alt"."""
    def at(seg, off):
        return c.at(to_road(seg_d[seg] + off))

    def seglen(seg):
        return seg_d.get(seg + 1, length) - seg_d[seg]

    def heading(q):
        return math.atan2(q.t.x, -q.t.y)

    def var(e):
        return {"variant": "alt"} if e and e[-1] == "alt" else {}

    def G(x, y, z):
        g = c.game(x, y, z)
        return {"x": round(g[0], 2), "y": round(g[1], 2), "z": round(g[2], 2)}

    for seg, s0, s1, *rest in sp.get("dividers", []):
        q0 = at(seg, s0)
        k = 0
        s = s0
        while s < s1:
            q = at(seg, s)
            # (Only seen: a ridge of ice down the middle marking the lanes; a solid one would
            # stand in the boss's racing line.)
            box(c, "Divider %d %d" % (seg, k), q.p.x, q.p.y, 0.4, 1.6, q.p.z - 1.0, q.p.z + 0.5, ("rift_snow", "wall"),
                rot=math.atan2(q.t.y, q.t.x) - math.pi / 2, role="visual")
            s += 4.0
            k += 1
        del q0
    for seg, off, side, period, offset, *rest in sp.get("ice_walls", []):
        q = at(seg, off)
        c.entity("ice_wall", **G(q.p.x, q.p.y, q.p.z), heading=round(heading(q), 4), width=round(q.w / 2 - 0.6, 1),
                 across=round(side * q.w / 4, 2), period=period, offset=offset, warn=1.3, up=1.9, **var(rest))
    for a, b, gap, speed, *rest in sp.get("avalanche", []):
        c.entity("avalanche", **{"from": round(to_road(seg_d[a]), 1), "to": round(to_road(seg_d[b]), 1)}, gap=gap,
                 speed=speed, **var(rest))
    for a, b, gap, speed, *rest in sp.get("firewall", []):
        c.entity("firewall", **{"from": round(to_road(seg_d[a]), 1), "to": round(to_road(seg_d[b]), 1)}, gap=gap,
                 speed=speed, **var(rest))
    for a, b, *rest in sp.get("thin_lake", []):
        pts = [at(seg, seglen(seg) * f) for seg in range(a, b + 1) for f in (0.0, 0.5, 1.0)]
        cx = sum(q.p.x for q in pts) / len(pts)
        cy = sum(q.p.y for q in pts) / len(pts)
        r = max(math.hypot(q.p.x - cx, q.p.y - cy) for q in pts) + 12.0
        z = min(q.p.z for q in pts)
        c.disc("Frozen Lake", cx, cy, r, z - 0.25, c.lib("lake_ice", "ice"), role="visual", n=40)
        c.entity("thin_lake", **G(cx, cy, z), r=round(r, 1), **var(rest))
    for seg, off, side, r, period, offset, *rest in sp.get("gusts", []):
        q = at(seg, off)
        # The wind blows across the road toward `side` (+1: to the right).
        rx, ry = q.r.x * side, q.r.y * side
        c.entity("gust", **G(q.p.x, q.p.y, q.p.z), r=r, dx=round(rx, 3), dz=round(-ry, 3), period=period, offset=offset,
                 warn=1.2, on=2.6, strength=7.5, **var(rest))
    for seg, off, side, dist, *rest in sp.get("shelters", []):
        q = at(seg, off)
        x, y = q.p.x + q.r.x * side * dist, q.p.y + q.r.y * side * dist
        c.assign(c.rock_mass("Shelter %d %d" % (seg, int(off)), x, y, 3.0, 2.4, q.p.z + 9.0, z0=q.p.z - 3.0, n=10,
                             seed=int(off) + seg), c.lib(*sp["mats"]["wall"]))
        g = c.game(x, y, q.p.z)
        c.entity("shelter", x=round(g[0], 2), z=round(g[2], 2), r=4.5, **var(rest))
    for seg, off, *rest in sp.get("tailwinds", []):
        q = at(seg, off)
        c.entity("tailwind", **G(q.p.x, q.p.y, q.p.z), r=10.0, **var(rest))
    for e in sp.get("sandstorm", []):
        c.entity("sandstorm", density=e[0], **var(e))
        # The beacon fires marking the way.
        s = 0.0
        while s < length:
            q = c.at(s)
            for sd in (-1, 1):
                x, y = q.p.x + q.r.x * sd * (q.w / 2 + 2.5), q.p.y + q.r.y * sd * (q.w / 2 + 2.5)
                box(c, "Beacon %d %d" % (int(s), sd), x, y, 0.4, 0.4, q.p.z - 1.0, q.p.z + 2.4, ("weathered_timber", "wall"))
                g = c.game(x, y, q.p.z + 2.8)
                c.entity("torch", x=g[0], y=g[1], z=g[2])
            s += 36.0
    for e in sp.get("tide", []):
        period, low, high, *rest = e
        c.entity("tide", period=period, low=low, high=high, **var(rest))
    for (sa, oa), (sb, ob), *rest in sp.get("sandbars", []):
        qa, qb = at(sa, oa), at(sb, ob)
        n = max(2, int(math.hypot(qb.p.x - qa.p.x, qb.p.y - qa.p.y) / 8))
        pts = [(kit.lerp(qa.p.x, qb.p.x, k / n), kit.lerp(qa.p.y, qb.p.y, k / n),
                kit.lerp(qa.p.z, qb.p.z, k / n) if k in (0, n) else 0.35) for k in range(n + 1)]
        c.side_road("Sandbar %d" % sa, pts, "beach_road", "road", width=9.0, shoulder=1.2, shoulder_mat=("wet_sand", "sand"))
        for x, y, z in pts[1:-1]:
            c.entity("sandbar", **G(x, y, 0.0), r=6.0, **var(rest))
    for seg, *rest in sp.get("coils", []):
        c.entity("coil", **{"from": round(to_road(seg_d[seg]) + 2.0, 1), "to": round(to_road(seg_d[seg] + seglen(seg)) - 2.0, 1)},
                 period=8.0, offset=0.0, up=5.0, **var(rest))
    for seg, off, *rest in sp.get("whirlpools", []):
        q = at(seg, off)
        c.entity("whirlpool", **G(q.p.x, q.p.y, q.p.z), r=round(q.w / 2 + 1.0, 1), spin=1.5, **var(rest))
    for e in sp.get("fireball", []):
        period, speed, *rest = e
        c.entity("fireball", period=period, speed=speed, **var(rest))


if __name__ == "__main__":
    build(sys.argv[-1])
