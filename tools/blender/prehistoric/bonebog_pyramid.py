# Bonebog Pyramid: Prehistoric World, course 3. A living swamp, a dinosaur graveyard
# and a colossal overgrown pyramid you drive straight through.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/bonebog_pyramid.py      (the bpy module)
#
# v3 (Blake's driving notes, 2026-10-23, from the greybox bonebog_v3.py): the same swamp,
# graveyard and pyramid as v2 (kept playable as bonebog_pyramid_v2), round a new lap of
# about 1.5 km that's nearly all bends:
#
#   A  The Old Dike: the start, north along the dike, and the first S-bends east over
#      the boardwalks; the first green balloon's spot is a zipper.
#   B  A big hairpin back west, and a weave across the heart of the swamp.
#   C  The Rib Bridge: north through the rib cage of a colossal skeleton.
#   D  The great tree: one and a quarter turns up round its trunk to the treehouse
#      village in its limbs, then a fast drop down a stone causeway to the pyramid.
#   E  The Pyramid: rolling crests down the torchlit corridor, the turning chamber, and
#      the Great Hall: more crests, and a jump over the river that runs through it and
#      pours out of the pyramid's side into the swamp.
#   F  Skull Lagoon: an S down the trestle past the great skull, weaving home under the
#      stilt village, and onto the dike.
#
# Saves tracks-src/bonebog_pyramid.blend and exports public/tracks/bonebog_pyramid/. The
# scenery is bonebog_scenery.py (built round the old lap's sections, mapped onto the new
# ones by SCENE_SEG), from the swamp kit in swamp_props.py.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import Vector, bmesh, lerp, smooth  # noqa: E402

TRACK_ID = "bonebog_pyramid"
WATER_Z = 0.0

# ---------------------------------------------------------------- the layout

START = (0.0, -200.0)
LAYOUT = [
    ("S", 95),  # 0  the start, north along the dike
    ("R", 50, 90),  # 1  east onto the boardwalks
    ("S", 30),  # 2
    ("L", 45, 55),  # 3  the first S-bends
    ("R", 45, 55),  # 4
    ("S", 40),  # 5  (the green balloon's spot: a zipper now)
    ("L", 28, 180),  # 6  a big hairpin back west
    ("R", 26, 60),  # 7  weaving west across the heart of the swamp
    ("L", 26, 120),  # 8
    ("R", 26, 60),  # 9
    ("S", 21),  # 10
    ("R", 26, 90),  # 11 north
    ("S", 42),  # 12 the Rib Bridge, climbing
    ("L", 31.5, 90),  # 13 west
    ("S", 14),  # 14 to the great tree
    ("L", 26, 450),  # 15 the spiral up round the great tree
    ("R", 28, 90),  # 16 out along the treehouse village
    ("S", 28),  # 17 the drop to the pyramid's face
    ("S", 42),  # 18 the corridor: rolling hills
    ("L", 31.5, 90),  # 19 the turning chamber
    ("S", 63),  # 20 the great hall: hills, and the jump over the river
    ("S", 21),  # 21 the trestle down out of the pyramid (stretched to close)
    ("R", 28, 45),  # 22 an S down the trestle
    ("L", 28, 90),  # 23
    ("R", 28, 45),  # 24
    ("L", 31.5, 60),  # 25 weaving home through the swamp
    ("R", 28, 60),  # 26
    ("L", 28, 80),  # 27
    ("S", 28),  # 28 (stretched to close)
    ("L", 31.5, 100),  # 29 north onto the dike
    ("S", 7),  # 30
]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 21, 28, START, 90.0)
SEG = kit.segment_starts(PATH)
LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))

# The jump in the great hall: where along the hall, and its gap.
HALL = (SEG[20], SEG[21])
GAP = (lerp(HALL[0], HALL[1], 0.55), lerp(HALL[0], HALL[1], 0.55) + 8.0)

# Heights at segment starts; between them the road eases (the spiral climbs steadily).
HEIGHT = {
    0: 2.6, 1: 2.6, 2: 3.2, 3: 3.6, 4: 3.6, 5: 3.6, 6: 3.8, 7: 4.2, 8: 4.0, 9: 4.4, 10: 4.2, 11: 4.2,
    12: 5.0, 13: 10.0, 14: 9.5, 15: 9.0, 16: 19.0, 17: 14.0, 18: 8.6, 19: 8.6, 20: 8.6, 21: 8.6,
    22: 7.4, 23: 6.2, 24: 5.2, 25: 4.6, 26: 4.0, 27: 3.6, 28: 3.2, 29: 2.8, 30: 2.6,
}


def road_z(d, seg):
    a, b = SEG[seg], SEG.get(seg + 1, LENGTH)
    t = (d - a) / max(1e-6, b - a)
    z0, z1 = HEIGHT[seg], HEIGHT.get(seg + 1, HEIGHT[0])
    z = lerp(z0, z1, t if seg == 15 else smooth(t))
    if seg == 18:
        z += 2.2 * math.sin(t * math.pi * 2) ** 2  # two crests down the corridor
    if seg == 20:
        if GAP[0] <= d <= GAP[1]:
            return lerp(8.6, 8.4, (d - GAP[0]) / (GAP[1] - GAP[0]))
        u = (d - a) / max(1e-6, GAP[0] - a)
        if d < GAP[0]:
            # A crest down the hall, flattening out before the take-off ramp (which is
            # the ramp piece's own lift, so it's exact).
            z += 1.8 * math.sin(u * math.pi * 2.0) ** 2 * (1 - smooth((u - 0.55) / 0.3))
        else:
            v = (d - GAP[1]) / max(1e-6, b - GAP[1])
            z += -0.2 + 1.6 * math.sin(v * math.pi) ** 2 * smooth(v * 3)
    return z


def road_w(d, seg):
    if 18 <= seg <= 20:
        return 16.0
    if seg in (0, 29, 30) or (seg == 1 and d < SEG[1] + 20):
        return 16.0
    if seg in (12, 13, 21):
        return 15.0
    return 14.5


ROUTE = kit.route_points_by(PATH, road_z, every=10.0, width=road_w)



# The old lap's sections, as the scenery knows them, on the new lap: old segment ->
# where that section is now (bonebog_scenery.py places things by these).
_OLD_TO_NEW = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 11, 7: 12, 8: 13, 9: 14, 10: 15, 11: 16, 12: 17, 13: 18,
               14: 19, 15: 20, 16: 21, 17: 22, 18: 23, 19: 24, 20: 25, 21: 25, 22: 26, 23: 27, 24: 28, 25: 29, 26: 29, 27: 29, 28: 30}
SCENE_SEG = {o: SEG[n] for o, n in _OLD_TO_NEW.items()}
JAW_S = 62.0  # the Jawbone Gate, over the start straight
LONGNECK = False  # (its causeway is the great tree's spiral now)

# The pyramid: its east face where the corridor begins, its south face where the Great
# Hall comes out, centred over the hall.
_entry = next(p for p in PATH if p[3] == 18)
_exit = next(p for p in PATH if p[3] == 21)
PYR_HX = 72.0
PYR_HY = _entry[1] - _exit[1]
PYR = (_entry[0] - PYR_HX, _entry[1])
FOUND_Z = 6.5  # the top of the stone foundation the pyramid stands on
FOUND_PAD = 16.0  # how far the foundation reaches beyond the pyramid
# Tiers: (half-size inset, top height). The lowest is tallest: the doorways are in it.
TIERS = [(0.0, 22.5), (12.0, 33.5), (24.0, 44.5), (36.0, 55.5), (48.0, 66.5), (60.0, 77.5)]
SHRINE = (10.0, 12.0, 12.0)  # half-sizes and height of the shrine on top
INSIDE = (SEG[18], SEG[21])  # the route inside the pyramid

# The great tree, at the spiral's centre.
_h0 = next(p for p in PATH if p[3] == 15)
SPIRAL_R = LAYOUT[15][1]
TREE = (_h0[0], _h0[1] - SPIRAL_R)


def near_spiral(x, y, m=0.0):
    return math.hypot(x - TREE[0], y - TREE[1]) < SPIRAL_R + 22 + m


# ---------------------------------------------------------------- the land


def sm(t):
    return smooth(max(0.0, min(1.0, t)))


def in_pyramid(x, y, pad=0.0):
    return abs(x - PYR[0]) < PYR_HX + pad and abs(y - PYR[1]) < PYR_HY + pad


def on_foundation(x, y, pad=0.0):
    return in_pyramid(x, y, FOUND_PAD + pad)


def pyramid_top(x, y):
    """The height of the pyramid's stepped surface over (x, y) (None outside it)."""
    e = min(PYR_HX - abs(x - PYR[0]), PYR_HY - abs(y - PYR[1]))
    if e < 0:
        return None
    z = FOUND_Z
    for inset, top in TIERS:
        if e >= inset:
            z = top
    return z


# The old dike the start runs along: an earthen bank under the road from the end of
# the mangroves round to the start straight, (x, y, half-width of its top).
def _dike_line():
    out = []
    d = 0.0
    nxt = 0.0
    for i, (x, y, _, seg) in enumerate(PATH):
        if i:
            d += math.hypot(x - PATH[i - 1][0], y - PATH[i - 1][1])
        if d >= nxt:
            if d >= SEG[28]:
                out.append((x, y, 20.0))
            nxt += 15.0
    d = 0.0
    nxt = 0.0
    for i, (x, y, _, seg) in enumerate(PATH):
        if i:
            d += math.hypot(x - PATH[i - 1][0], y - PATH[i - 1][1])
        if d > SEG[1] + 15:
            break
        if d >= nxt:
            out.append((x, y, 20.0 if d < SEG[1] else 12.0))
            nxt += 15.0
    return out


DIKE = _dike_line()


def _nearest(px, py, pts):
    best = (1e9, 0, 0.0)
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        ax, ay, bx, by = a[0], a[1], b[0], b[1]
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        d = math.hypot(px - ax - t * dx, py - ay - t * dy)
        if d < best[0]:
            best = (d, i, t)
    return best


def dike(x, y):
    """The dike's height (its top at 2.2 m, sloping into the water), or -inf."""
    d, i, t = _nearest(x, y, DIKE)
    hw = lerp(DIKE[i][2], DIKE[i + 1][2], t)
    return 2.2 - 3.4 * sm((d - hw) / 14.0) - 1.6 * sm((d - hw - 14) / 10)


# Mud islands in the swamp (x, y, radius): root mounds for the giant trees, bone banks.
ISLANDS = [
    (60, -120, 26), (-60, -110, 30), (-60, -190, 24), (90, 60, 22), (170, -60, 26), (230, -40, 24),
    (160, 120, 30), (320, 30, 30), (310, 160, 26), (120, 190, 22), (-230, 60, 30), (-220, -60, 28),
    (-210, -170, 26), (-70, 40, 26), (40, -230, 18), (230, 300, 30), (40, 330, 26),
]


# Keep the water open beside the road: no islands within 30 m of it.
ISLANDS = [(x, y, r) for x, y, r in ISLANDS if min(math.hypot(x - p[0], y - p[1]) for p in PATH[::4]) > r + 30]


def natural(x, y):
    """The swamp bed: deep under the water, with mud islands, the dike and, all round,
    the jungle rising on low hills."""
    h = -3.6 + 0.7 * math.sin(x / 19) * math.cos(y / 23) + 0.5 * math.sin((x - y) / 37)
    for ix, iy, r in ISLANDS:
        d = math.hypot(x - ix, y - iy)
        if d < r + 16:
            h = max(h, 1.0 + 0.6 * math.sin(x / 7 + y / 5) - 4.6 * sm((d - r * 0.55) / (r * 0.45 + 16)))
    h = max(h, dike(x, y))
    # The jungle all round, on rising ground.
    r = math.hypot((x - 20) / 1.0, (y - 30) / 1.12)
    rim = 300 + 25 * math.sin(math.atan2(y - 30, x - 20) * 5 + 1)
    h = max(h, -4 + 34 * sm((r - rim) / 60))
    return h


def classify(c, n, info):
    if on_foundation(c.x, c.y, -2):
        return None  # under the pyramid's foundation
    if c.z < WATER_Z - 0.4:
        return ("bog_mud", "mud")  # the swamp bed, under the water
    if n.z < 0.62:
        return ("bog_root", "wall")
    if info["d"] < 13 and c.z > 1.5:
        return ("bog_moss_ground", "grass")
    return ("bog_bank", "grass")



def seg_of(s):
    k = 0
    for i, d in SEG.items():
        if d <= s:
            k = max(k, i)
    return k


def boolean_cut(ob, bm, name="Cut", mat=None):
    import bpy  # noqa: E402

    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if mat is not None:
        me.materials.append(mat)  # the faces the cut makes get this
    cutter = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(cutter)
    mod = ob.modifiers.new(name, "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
    mod.object = cutter
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter)



def great_tree(c, lights):
    """The great tree the spiral climbs, and the treehouse village in its limbs: plank
    platforms ringing its trunk at three heights, plank huts on them, rope bridges out to
    the nearest giants, and lanterns."""
    import props  # noqa: E402
    import swamp_props as sp  # noqa: E402

    c.place(sp.swamp_giant(c, 1), TREE[0], TREE[1], 0.0, rot=0.7, scale=1.0, coll="Trees", role="both")
    plat = sp.platform(c, 0)
    huts = bmesh.new()
    roofs = bmesh.new()
    for k, (z, a) in enumerate(((21.0, 0.4), (28.0, 2.5), (35.0, 4.4))):
        c.place(plat, TREE[0], TREE[1], z, rot=a, scale=1.0, coll="Village", role="visual")
        for j in range(2):
            b = a + j * math.pi
            hx, hy = TREE[0] + 7.0 * math.cos(b), TREE[1] + 7.0 * math.sin(b)
            props.cuboid(huts, (hx, hy, z + 1.6), (3.2, 3.0, 3.2), rot=b)
            props.cuboid(roofs, (hx, hy, z + 3.6), (4.0, 3.8, 0.9), rot=b, tilt=(0.25, 0))
            lights.append((hx, hy, z + 2.4))
    hut = c.mesh_object("Great Tree Huts", huts, "Village", "visual")
    c.assign(hut, c.lib("bog_boards", "wall"))
    roof = c.mesh_object("Great Tree Roofs", roofs, "Village", "visual")
    c.assign(roof, c.lib("bog_rail", "wall"))


# ---------------------------------------------------------------- the course


def main():
    import props  # noqa: E402

    c = kit.Course(TRACK_ID, "Bonebog Pyramid", "bonebog_swamp")
    c.route(ROUTE, width=14.5, bank=6.0)
    rail = ("bog_rail", "wall")
    stone_rail = ("bog_carved", "wall")
    board = {
        "mat": "bog_boards",
        "shoulder": 0.5,
        "shoulder_mat": ("bog_boards", "road"),
        "barrier": 1.2,
        "barrier_mat": rail,
        "deck": 2.4,
        "deck_mat": ("bog_root", "wall"),
        "ground": False,
    }
    c.kinds = {
        "dike": {"mat": "bog_paving", "shoulder": 1.8, "shoulder_mat": ("bog_moss_ground", "dirt"), "barrier": 0.7, "barrier_mat": ("bog_stone", "wall")},
        "boardwalk": board,
        "bridge": dict(board, barrier=1.3, deck=3.0),
        "spiral": dict(board, barrier=1.4, deck=2.0),
        "causeway": {
            "mat": "bog_paving",
            "shoulder": 1.0,
            "shoulder_mat": ("bog_stone", "road"),
            "barrier": 1.3,
            "barrier_mat": stone_rail,
            "deck": 12.0,
            "deck_mat": ("bog_stone", "wall"),
            "ground": False,
        },
        "temple": {"mat": "bog_paving", "surface": "road", "shoulder": 2.5, "shoulder_mat": ("bog_dark_stone", "road")},
        "ramp": {"mat": "bog_paving", "surface": "road", "shoulder": 2.5, "shoulder_mat": ("bog_dark_stone", "road"), "barrier": 1.0, "barrier_mat": stone_rail},
    }

    def label(smp):
        s = smp.s
        seg = seg_of(s)
        if GAP[0] <= s <= GAP[1]:
            return "gap"
        if seg == 20 and GAP[0] - 12 <= s < GAP[0]:
            return "ramp"
        if INSIDE[0] - 2 <= s <= INSIDE[1] + 2:
            return "temple"
        if seg in (0, 29, 30) or (seg == 1 and s < SEG[1] + 20):
            return "dike"
        if seg == 17:
            return "causeway"
        if seg in (12, 13, 21):
            return "bridge"
        if seg in (15, 16):
            return "spiral"
        return "boardwalk"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "ramp":
            # The take-off: a straight incline rising 1.6 m to a clean lip, eased in at its
            # foot (never a kicker curling up at the end).
            def lift(u, n, w=12.0, rise=1.6, t0=0.35):
                v = max(0.0, min(1.0, (u - (n - w)) / w))
                k = 1.0 / (1.0 - t0 / 2.0)
                return rise * (k * v * v / (2 * t0) if v < t0 else k * (v - t0 / 2.0))

            specials.append((s0, s1, "ramp", {"lift": lift}))
        elif k != "boardwalk":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "boardwalk", max_len=200.0))

    X0, X1, Y0, Y1 = -360, 400, -360, 450
    c.terrain("Swamp", X0, X1, Y0, Y1, 6.0, natural, classify, near=10.0, fade=16.0, under=0.2)
    # The swamp water: deep and murky. Fall in and you're fished out.
    c.disc("Swamp Water", 20, 40, 520, WATER_Z, c.lib("bog_water", "deep_water"), n=64)

    import bonebog_scenery  # noqa: E402

    me = sys.modules[__name__]
    pyr = bonebog_scenery.pyramid(c, me)
    # The river across the Great Hall, at the jump: a channel west out of the pyramid's
    # side, pouring into the swamp.
    q = c.at((GAP[0] + GAP[1]) / 2)
    gx, gy = q.p.x, q.p.y
    west = PYR[0] - PYR_HX
    cut = bmesh.new()
    props.cuboid(cut, ((west - 10 + gx + 14) / 2, gy, FOUND_Z + 2.0), (gx + 14 - west + 10, 10.0, 6.0))
    boolean_cut(pyr, cut, "River Cut", c.lib("bog_dark_stone", "wall"))
    c.ribbon("Hall River", [(gx + 12, gy, 9), (west + 1, gy, 9)], 9, FOUND_Z + 0.4, c.lib("bog_water", "deep_water"), steps=2)
    falls = props.falls(c, "Hall River Falls", west - 0.5, gy, FOUND_Z + 0.6, WATER_Z, 7.0, 10.0, facing=-1, throw=3.0, angle=-math.pi / 2, veils=2)
    g = c.game(falls[0], falls[1], WATER_Z)
    c.entity("waterfall", x=g[0], y=g[1], z=g[2], top=round(FOUND_Z + 0.6, 1), width=10.0, heading=0)

    c.start_line()
    # Zippers: off the start, at the first green balloon's spot (Blake's note), on the
    # Rib Bridge's climb, down the drop to the pyramid, into the Great Hall (up to speed
    # for the jump) and down the trestle out of it.
    c.zipper(55, 0)
    c.zipper(SEG[5] + 15, 0)
    c.zipper(SEG[12] + 15, 0)
    c.zipper(SEG[17] + 5, 0)
    c.zipper(SEG[20] + 4, 0)
    c.zipper(SEG[21] + 13, 0)
    for at, across in ((95, -3), (SEG[3] + 20, 0), (SEG[8] + 20, 0), (SEG[15] + 80, 0), (SEG[18] + 30, 0), (SEG[26] + 10, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (75, -4, "red"),
        (75, 4, "blue"),
        (SEG[7] + 15, 0, "green"),
        (SEG[13] + 20, 0, "yellow"),
        (SEG[16] + 30, -3, "rainbow"),
        (SEG[16] + 30, 3, "red"),
        (SEG[25] + 15, 0, "blue"),
        (SEG[27] + 10, 0, "green"),
    ):
        c.balloon(at, across, col)
    # Missing the hall's jump drops you in the river: back out past it.
    c.entity("respawn", **{"from": round(GAP[0] - 20, 1), "to": round(GAP[1] + 4, 1), "at": round(GAP[1] + 20, 1)})
    c.checkpoints(extra=[SEG[2] + 10, SEG[6] + 30, SEG[9], SEG[12] + 30, SEG[15] + 60, SEG[15] + 140, SEG[17], SEG[19] + 10, SEG[21] + 10, SEG[25], SEG[27]], height=10.0)

    lights = []
    great_tree(c, lights)
    for x, y, z in lights:
        g = c.game(x, y, z)
        c.entity("torch", x=g[0], y=g[1], z=g[2])
    bonebog_scenery.build(c, pyr, me)

    kit.paint.shade_roads(c.pieces, 0.35)
    c.finish()
    print("lap", round(c.length, 1))


if __name__ == "__main__":
    main()
