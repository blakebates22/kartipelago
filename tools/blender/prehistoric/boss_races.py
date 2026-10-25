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

# Each: layout, closing straights, start pose, heights at segment starts, decked segments
# (bridges, the road on posts), jumps (segment, metres into it, gap, drop, kick), zippers
# (segment, metres into it), laps, materials, and the ground's base level.
PREHISTORIC = {
    "name": "Tyrant's Gorge (boss, proto)",
    "theme": "river_valley",
    "laps": 3,
    "start": (0.0, 0.0), "head": 45.0,
    "layout": [("S", 150), ("L", 55, 270), ("S", 150), ("R", 55, 270)],
    "close": (0, 2),
    "heights": {0: 1.0, 1: 2.0, 2: 9.0, 3: 6.0},
    "deck": [2],
    "jumps": [(3, 150.0, 12.0, 2.0, 0.9)],
    "zippers": [(0, 30), (3, 110)],
    "mats": {"road": "valley_road", "ground": ("valley_grass", "grass"), "shoulder": ("valley_grass", "dirt"), "wall": ("valley_cliff", "wall"),
             "deck": "wood_planks", "rail": ("palm_bark", "wall")},
    "base": 0.0,
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
    "deck": [1, 5],
    "humps": {9: (4, 1.0)},
    "jumps": [(5, 50.0, 12.0, 2.0, 0.9)],
    "zippers": [(0, 20), (4, 20), (8, 10)],
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
        h = lerp(best - 0.5, sp["base"] + max(0.0, best - sp["base"]) * 0.6 + hills, smooth((d - 16) / 50))
        dk = dtree.find((x, y, 0.0))[2] if deck_pts else 1e9
        if dk < 30 and dk < d:
            h = lerp(h, sp["base"] - (12.0 if sp.get("chasm") else 0.0), smooth((30 - dk) / 18))
        return h

    m = sp["mats"]

    def classify(c, nrm, info):
        if nrm.z < 0.6:
            return m["wall"]
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
    gaps = [(to_road(l), to_road(r)) for l, r, _, _ in jumps]

    def label(smp):
        s = smp.s
        for l, r in gaps:
            if l <= s <= r:
                return "gap"
            if l - 12 <= s < l:
                return "kicker"
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
    for k, (l, r) in enumerate(gaps):
        c.entity("respawn", **{"from": round(l - 20, 1), "to": round(r + 4, 1), "at": round(r + 18, 1)})
    for i in range(1, n, 3):
        c.balloon(to_road(seg_d[i]) + 10, 0, ("red", "blue", "green", "yellow", "rainbow")[i % 5])
    c.checkpoints(extra=[to_road(seg_d[i]) + 5 for i in range(1, n, 2)], avoid=[(l - 16, r + 10) for l, r in gaps], height=10.0)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish(extra={"race": {"laps": sp["laps"]}})
    print(track_id, "lap", round(c.length, 1), "laps", sp["laps"])


if __name__ == "__main__":
    build(sys.argv[-1])
