# Cascade Caverns: Prehistoric World, course 2. A lost temple in a jungle canyon.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/cascade_caverns.py      (the bpy module)
#
# v2 (v1 is git tag cascade-v1): a deep, overgrown canyon with a river along its floor,
# giant trees, vines, waterfalls and the ruins of an old temple city. The road starts
# on the canyon floor, sweeps up a stone viaduct at the east end, runs along a ledge on
# the north wall, crosses the whole canyon on a great Mayan-style bridge (right over the
# start), dives into a long torchlit temple tunnel through the south wall, leaps the
# river gorge through a waterfall at the west end, and winds back down past the ruins.
# Every corner is a 32-60 m arc you can hold a drift through.
#
# Saves tracks-src/cascade_caverns.blend and exports public/tracks/cascade_caverns/.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import props  # noqa: E402
import ruin_mode  # noqa: E402
from course_kit import Vector, bmesh, lerp, smooth  # noqa: E402

# The ruin (cascade_ruins.py): the viaduct and the ledge have fallen; the lap climbs their
# rubble straight across the canyon to the temple bridge. Otherwise the same course.
RUIN = ruin_mode.ON
TRACK_ID = "cascade_caverns_ruin" if RUIN else "cascade_caverns"
WATER_Z = -1.6

# ---------------------------------------------------------------- the layout

START = (-40.0, -42.0)
LAYOUT = [
    ("S", 60),  # 0  the start straight, east along the canyon floor
    ("R", 40, 30),  # 1
    ("L", 45, 60),  # 2
    ("S", 20),  # 3
    ("L", 50, 150),  # 4  the viaduct: one long sweeping climb round the east end
    ("S", 40),  # 5  the ledge along the north wall
    ("R", 40, 25),  # 6
    ("L", 40, 25),  # 7
    ("S", 30),  # 8
    ("L", 32, 90),  # 9  onto the temple bridge
    ("S", 95),  # 10 the bridge, over the river and the start
    ("R", 36, 90),  # 11 into the temple tunnel
    ("S", 17),  # 12 (closes the loop)
    ("L", 60, 28),  # 13 an S through the tunnel
    ("R", 60, 28),  # 14
    ("S", 42),  # 15
    ("R", 36, 90),  # 16 out of the tunnel, onto the west plateau
    ("S", 60),  # 17 the run-up to the leap (a stone ramp at the end)
    ("S", 16),  # 18 the gap: over the gorge, through the waterfall
    ("S", 50),  # 19 the landing strip
    ("R", 34, 90),  # 20
    ("L", 34, 25),  # 21
    ("R", 34, 25),  # 22
    ("S", 45),  # 23 the north road, past the ruins
    ("R", 38, 90),  # 24
    ("S", 53),  # 25 over the river on a low stone bridge (closes the loop)
    ("L", 40, 90),  # 26 under the temple bridge
    ("S", 20),  # 27
]
STANDARD_LAYOUT = list(LAYOUT)
if RUIN:
    # Segments 1-8 (the viaduct's sweep round the east end and the ledge) become the climb
    # north across the canyon; 5-8 are left as stubs so the later segments keep their
    # numbers (the scenery and gameplay below are placed by them).
    # v2 of the ruin (Blake: "after the waterfall jump, we cut to the finish line quicker",
    # about 20% shorter than the full lap): the start straight and the climb's top are 30 m
    # shorter (the course past them stays where it was), and past the leap the north road
    # is gone: a hairpin off the landing, then straight down across the canyon, over the
    # river on the old city's fallen stones, to the start. 20-27 keep their numbers (21 and
    # 22 are stubs). The tunnel's straight (12) keeps the length it had, so everything from
    # the bridge to the landing is exactly where it was.
    LAYOUT[0] = ("S", 30)
    LAYOUT[1:9] = [("L", 30, 90), ("S", 45), ("L", 30, 90), ("S", 17), ("S", 0.5), ("S", 0.5), ("S", 0.5), ("S", 0.5)]
    LAYOUT[12] = ("S", 14.401454264062872)
    LAYOUT[20:28] = [("R", 34, 140), ("S", 0.5), ("S", 0.5), ("S", 50), ("L", 60, 10), ("S", 80), ("L", 30, 40), ("S", 20)]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 23 if RUIN else 12, 25, START, 0.0)
STANDARD_PATH = kit.close_turtle(STANDARD_LAYOUT, 12, 25, START, 0.0)[1]
SEG = kit.segment_starts(PATH)
LIP = SEG[18]
LAND = SEG[19]

# Heights at segment starts (the road eases between them).
HEIGHT = [
    (0, 0.0),
    (3, 0.6),
    (4, 1.0),
    (5, 12.0),
    (9, 14.5),
    (10, 15.5),
    (11, 15.5),
    (12, 15.0),
    (16, 14.2),
    (17, 14.0),
    (18, 14.8),
    (19, 9.4),
    (20, 7.0),
    (21, 6.2),
    (23, 4.8),
    (24, 3.8),
    (25, 2.6),
    (26, 1.4),
    (27, 0.3),
]
if RUIN:
    # The climb: off the canyon floor, up the rubble over the river, onto the bridge.
    HEIGHT[1:5] = [(1, 0.4), (2, 3.0), (3, 8.4), (4, 12.6)]
    # Off the plateau round the hairpin, then gently down to the river and the start.
    HEIGHT[-7:] = [(20, 7.0), (21, 4.6), (23, 4.0), (24, 2.8), (25, 2.6), (26, 1.4), (27, 0.3)]


def road_z(d, seg):
    if 18 <= seg < 19:
        return lerp(14.8, 9.4, (d - LIP) / (LAND - LIP))
    if d >= SEG[27]:
        return lerp(0.3, 0.0, smooth((d - SEG[27]) / 20))
    for (s0, z0), (s1, z1) in zip(HEIGHT, HEIGHT[1:]):
        if s0 <= seg < s1:
            a, b = SEG[s0], SEG[s1]
            t = (d - a) / max(1e-6, b - a)
            # The ramp and the landing are straight slopes; everything else eases.
            return lerp(z0, z1, t if s0 in (17, 19) else smooth(t))
    return 0.0


def road_w(d, seg):
    if seg == 19:
        return 22.0  # a wide landing: wherever you land, you're on the road
    if seg == 17 and d > SEG[18] - 34:
        return 18.0
    return 14.0


ROUTE = kit.route_points_by(PATH, road_z, every=12.0, width=road_w)

# ---------------------------------------------------------------- the land


def river_y(x):
    y = 2.0 + 3.0 * math.sin(x / 50.0) + 2.0 * math.sin(x / 23.0 + 0.7)
    # At the west end the river swings south into the gorge under the leap.
    return lerp(y, -9.0, smooth((-x - 215) / 22))


def river_half(x):
    """Half the river's width: narrow in the gorge."""
    return lerp(15.0, 6.5, smooth((-x - 225) / 14))


def wall_n(x):
    w = 72 + 5 * math.sin(x / 37) + 3 * math.sin(x / 11)
    return w + 34 * smooth((-x - 80) / 45)  # the canyon opens out in the west


def wall_s(x):
    return -70 + 6 * math.sin(x / 29 + 1) + 3 * math.sin(x / 13)


def plateau(x, y):
    """The high ground at the west end, cut by the gorge: the run-up on the south side,
    the landing on the north."""
    south = 13.0 * smooth((-x - 205) / 22)
    north = 8.6 * smooth((-x - 200) / 26)
    k = smooth((y - river_y(x)) / 10 + 0.5)
    return lerp(south, north, k)


# Tiers of the canyon walls: (distance into the wall, rise). Flat shelves between the
# rises are ledges you can see plants and ruins on.
TIERS = ((0, 9), (6, 8), (13, 10), (22, 9), (30, 8))


def walls(x, y):
    rise = 0.0
    for edge, sign, ph in ((wall_n(x), 1, 0.0), (wall_s(x), -1, 2.0)):
        d = (y - edge) * sign
        for k, (step, up) in enumerate(TIERS):
            wob = 1.6 * math.sin(x / (13 + k * 3) + ph + k)
            rise += up * smooth((d - step - wob) / 2.6)
    for edge, sign in ((200, 1), (-276, -1)):
        d = (x - edge) * sign
        for step, up in ((0, 12), (7, 12), (16, 14), (26, 10)):
            rise += up * smooth((d - step) / 3.5)
    return rise


def base_floor(x, y):
    """The land without its walls: canyon floor, plateau and river bed."""
    h = 0.35 * math.sin(x / 17) * math.cos(y / 13) + plateau(x, y)
    d = abs(y - river_y(x))
    hw = river_half(x)
    if d < hw:
        bed = -4.0 if x > -205 else -7.0
        h = lerp(h, bed, smooth((hw - d) / 5.5))
    return h


def natural(x, y):
    return base_floor(x, y) + walls(x, y)


# The rock the temple tunnel runs through, part of the south wall.
TUNNEL = ((-152.0, -108.0), 88.0, 34.0)


def in_tunnel_rock(x, y, shrink=1.0):
    (cx, cy), rx, ry = TUNNEL
    return ((x - cx) / (rx * shrink)) ** 2 + ((y - cy) / (ry * shrink)) ** 2 < 1


def wall_tier(x, y):
    """Which rise of the canyon wall (0 = the first above the floor) the point (x, y) is on,
    or None on the open floor."""
    best = None
    for edge, sign, ph in ((wall_n(x), 1, 0.0), (wall_s(x), -1, 2.0)):
        d = (y - edge) * sign
        if d < -3:
            continue
        k = 0
        for t, (step, _) in enumerate(TIERS):
            wob = 1.6 * math.sin(x / (13 + t * 3) + ph + t)
            if d > step + wob + 1.3:
                k = t + 1
        k = min(k, len(TIERS) - 1)
        best = k if best is None else max(best, k)
    for edge, sign in ((200, 1), (-276, -1)):
        d = (x - edge) * sign
        if d < -3:
            continue
        k = sum(1 for step in (0, 7, 16, 26) if d > step + 1.75) - 1
        best = max(best or 0, max(0, k))
    return best


def rock_mat(c):
    """Rock in beds (v3, Blake's review: the old patchwork of grey, moss and ochre faces
    didn't blend). Each rise of the stepped walls is one kind of rock, so the changes run
    along the shelf edges like real strata instead of zig-zagging across the faces: mossy
    rock at the damp foot and toward the rim, grey beds between, and a bed of ochre
    sandstone on the third rise along most of the canyon."""
    k = wall_tier(c.x, c.y)
    if k is None or k == 0 or k >= 4:
        return "canyon_rock_moss"
    if k == 2 and math.sin(c.x / 95.0 + 0.8) > -0.45:
        return "canyon_rock_ochre"
    return "canyon_rock_grey"


# The stretch of route through the tunnel (set once the route is built), padded.
TUNNEL_S = [0.0, 0.0]


def classify(c, n, info):
    # Inside the tunnel rock (which covers it), and along the tunnel's passage (where the
    # land would poke through the floor), the land is left out. The rock's lumpy edge
    # always reaches past 0.86 of its radius, so there's never a gap between them.
    if in_tunnel_rock(c.x, c.y, 0.86):
        return None
    # (v3: only inside the rock's outline. Out in the open before the mouths this used to
    # cut holes in the wall beside the road, where you could see the sky through the
    # world and fall in: Blake's note 1.)
    smp = info["sample"]
    if TUNNEL_S[0] <= smp.s <= TUNNEL_S[1] and info["d"] < 16 and c.z > smp.p.z - 1.0 and in_tunnel_rock(c.x, c.y, 1.04):
        return None
    if n.z < 0.62:
        return (rock_mat(c), "wall")
    if c.z < WATER_Z + 0.5 and abs(c.y - river_y(c.x)) < river_half(c.x) + 3:
        return ("jungle_mud", "mud")
    if c.z > 24:
        return ("canopy_dark" if math.sin(c.x / 9) * math.cos(c.y / 7) > 0.3 else "jungle_leafcover", "grass")
    if info["d"] < 12:
        return ("jungle_path", "dirt")
    return ("jungle_leafcover", "grass")


def underfloor_z(x, y):
    """The hidden floor: just under the land's own floor, never above the visible land.
    It runs on under the tunnel rock too (below the tunnel's road, hidden in the rock),
    so there's no crack anywhere round the rock's lumpy foot."""
    return min(base_floor(x, y), natural(x, y)) - 0.35


def main():
    c = kit.Course(TRACK_ID, "Cascade Caverns (Ruined)" if RUIN else "Cascade Caverns", "cascade_ruins" if RUIN else "jungle_cascade")
    c.route(ROUTE, width=14.0, bank=7.0)
    stone = ("ruin_stone", "wall")
    c.kinds = {
        "path": {"mat": "jungle_path", "shoulder": 1.5, "shoulder_mat": ("jungle_leafcover", "dirt")},
        "ledge": {"mat": "jungle_path", "shoulder": 1.0, "shoulder_mat": ("jungle_mossstone", "dirt"), "barrier": 1.2, "barrier_mat": stone},
        "viaduct": {
            "mat": "jungle_temple",
            "surface": "road",
            "shoulder": 0.6,
            "shoulder_mat": ("ruin_stone", "road"),
            "barrier": 1.3,
            "barrier_mat": ("ruin_glyph", "wall"),
            "deck": 3.0,
            "deck_mat": stone,
            "ground": False,
        },
        "cave": {"mat": "jungle_temple", "surface": "road", "shoulder": 3.6, "shoulder_mat": ("ruin_dark", "road")},
        "ramp": {
            "mat": "jungle_temple",
            "surface": "road",
            "shoulder": 0.6,
            "shoulder_mat": ("ruin_stone", "road"),
            "barrier": 1.2,
            "barrier_mat": ("ruin_glyph", "wall"),
            "deck": 6.0,
            "deck_mat": stone,
            "ground": False,
        },
        "landing": {"mat": "jungle_temple", "surface": "road", "shoulder": 1.0, "shoulder_mat": ("ruin_stone", "road"), "barrier": 1.4, "barrier_mat": stone},
        "lowbridge": {
            "mat": "jungle_temple",
            "surface": "road",
            "shoulder": 0.6,
            "shoulder_mat": ("ruin_stone", "road"),
            "barrier": 1.1,
            "barrier_mat": ("ruin_glyph", "wall"),
            "deck": 2.4,
            "deck_mat": stone,
            "ground": False,
        },
    }

    # The ruin's river crossing isn't a bridge: the north road's fallen stones, heaped in
    # the river and driven over (the destruction rule: nothing new looks built).
    c.kinds["causeway"] = {
        "mat": "ruin_road",
        "surface": "road",
        "shoulder": 1.4,
        "shoulder_mat": ("ruin_rubble", "road"),
        "barrier": 0.6,
        "barrier_mat": ("ruin_rubble", "wall"),
        "deck": 3.0,
        "deck_mat": ("ruin_rubble", "road"),
        "ground": False,
    }

    # The ruin's climb isn't a bridge either: the fallen viaduct's own stones, heaped up out
    # of the canyon (cascade_ruins.py piles rubble under it, where the bridge had pylons).
    c.kinds["rubble"] = dict(c.kinds["causeway"], barrier=1.1)

    def seg_of(s):
        k = 0
        for i, d in SEG.items():
            if d <= s:
                k = max(k, i)
        return k

    def label(smp):
        x, y, s = smp.p.x, smp.p.y, smp.s
        seg = seg_of(s)
        if LIP <= s <= LAND:
            return "gap"
        if seg == 17 and s >= LIP - 34:
            return "ramp"
        if seg == 19:
            return "landing"
        if in_tunnel_rock(x, y, 0.98):
            return "cave"
        above = smp.p.z - natural(x, y)
        if 9 <= seg <= 11 and above > 3.0:
            return "viaduct"
        if RUIN and 1 <= seg <= 8:
            return "rubble" if above > 3.0 else "path"  # the rubble climb
        if seg == 4 and above > 3.0:
            return "viaduct"
        if 5 <= seg <= 8:
            return "ledge"
        if seg == 25 and abs(y - river_y(x)) < river_half(x) + 16:
            return "causeway" if RUIN else "lowbridge"
        return "path"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "ramp":
            # A gentle kicker: the last 10 m of the ramp curve up by 1 m.
            specials.append((s0, s1, "ramp", {"lift": lambda u, n: 1.0 * max(0.0, (u - (n - 10)) / 10) ** 2}))
        elif k != "path":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "path"))

    inside = kit.crossings(c, lambda smp: in_tunnel_rock(smp.p.x, smp.p.y, 1.0), margin=0)
    t0, t1 = max(inside, key=lambda r: r[1] - r[0])
    TUNNEL_S[:] = [t0 - 16, t1 + 16]
    c.terrain("Canyon", -300, 225, -165, 165, 3.0, natural, classify, near=8.5, fade=16.0)
    # A hidden floor under it all: nowhere to fall through the world. (v3: under the land
    # as it's shaped round the roads, so it never comes up through a road in a cutting.)
    import cascade_review  # noqa: E402

    c.underfloor("Underfloor", -300, 225, -165, 165, 3.0, cascade_review.underfloor_height(c, sys.modules[__name__]), c.lib("jungle_leafcover", "grass"))
    river = [(x, river_y(x), 2 * river_half(x) + 2) for x in range(-292, 222, 4)]
    c.ribbon("River", river, 30, WATER_Z, c.lib("valley_water", "deep_water"), steps=3)

    # The tunnel rock, cut through along the route: a long torchlit temple passage.
    (cx, cy), rx, ry = TUNNEL
    rock = c.rock_mass("Tunnel Rock", cx, cy, rx, ry, 40.0, z0=-2.0, n=32, seed=3,
                       bands=[(1.0, 0.0), (1.0, 0.3), (0.96, 0.34), (0.94, 0.62), (0.88, 0.66), (0.84, 1.0)])
    c.tunnel(rock, t0, t1, half=c.width / 2 + 3.6, height=11.0, pad=14.0)
    c.paint_rock(rock, ("canyon_rock_grey", "wall"), ("canopy_dark", "grass"), floor=("ruin_dark", "road"), top_z=32, floor_z=19)
    # A hidden floor the full width of the tunnel and out past both mouths, just under
    # the road: no gaps at the sides or where the mouths were cut.
    # (v3: wide inside the rock, where the passage's walls bound it, but outside the rock
    # no wider than the road's shoulders, so it never makes an invisible shelf out over
    # a drop at the mouths: Blake's notes 8 and 9.)
    floor = []
    s = t0 - 22
    while s <= t1 + 22:
        q = c.at(s)
        inside_rock = in_tunnel_rock(q.p.x, q.p.y, 0.85)
        floor.append((q.p.x, q.p.y, 2 * (c.width / 2 + 3.6) + (14.0 if inside_rock else 0.0), q.p.z - 0.25))
        s += 2.0
    c.ribbon("Tunnel Floor", floor, 26, 0, c.lib("ruin_dark", "road"), coll="Collision", role="collision", steps=4)

    c.start_line()
    L = c.length
    # Gameplay: a zipper down the start straight, one along the ledge, one onto the
    # run-up to the leap (so everyone reaches the lip at about the same speed).
    c.zipper(12 if RUIN else 40, 0)
    if RUIN:
        c.zipper(SEG[2] + 4, 0)  # up the rubble climb
    else:
        c.zipper(kit.s_near(c, 20, 62), 0)
    c.zipper(SEG[17] + 6, 0)
    for at, across in ((SEG[1] + 10, 0), (SEG[3] + 10, 2) if RUIN else (SEG[5] + 10, 2), (SEG[10] + 45, 0), (SEG[15] + 10, -2), (SEG[23] + 15, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (SEG[3], -3, "red"),
        (SEG[3], 3, "blue"),
        (SEG[4] + 10, 0, "green") if RUIN else (SEG[8] + 10, 0, "green"),
        (SEG[13] + 10, 0, "yellow"),
        (SEG[21] + 10, 0, "rainbow"),
    ):
        c.balloon(at, across, col)

    # Missing the leap drops you in the gorge: you're fished out at the end of the
    # landing strip, never before the jump.
    c.entity("respawn", **{"from": round(LIP - 40, 1), "to": round(LAND + 8, 1), "at": round(LAND + 44, 1)})

    # Checkpoints: up the viaduct, along the ledge, on the bridge, in and out of the
    # tunnel, well past the leap's landing, along the north road and over the low bridge.
    # Tall gates, so nobody can fly over one.
    c.checkpoints(
        extra=([SEG[2] + 20, SEG[4] + 10] if RUIN else [SEG[5], SEG[8]])
        + [SEG[10] + 50, SEG[13], SEG[16] + 30, LAND + 52, SEG[23] + 20, SEG[26]],
        height=10.0,
    )

    import cascade_scenery  # noqa: E402

    cascade_scenery.build(c, rock, t0, t1, sys.modules[__name__])
    # Rails wherever the road runs along a drop (Blake's notes 1, 2, 8, 9).
    new_road = (lambda s: seg_of(s) >= 20 or seg_of(s) <= 4) if RUIN else None  # the ruin's own new stretches
    print("edge rails:", cascade_review.edge_rails(c, sys.modules[__name__], list(c.coll("Terrain").objects) + [rock], rubble=new_road))

    ter = list(c.coll("Terrain").objects)
    c.preset("sun", ter + [rock], 0.35)
    c.preset("bottoms", ter, 0.5)
    c.preset("cover", [rock], 0.6)
    kit.paint.shade_roads(c.pieces, 0.6)
    if RUIN and ruin_mode.DRESS:
        ruin_mode.DRESS(c, sys.modules[__name__])
    c.finish()


if __name__ == "__main__":
    main()
