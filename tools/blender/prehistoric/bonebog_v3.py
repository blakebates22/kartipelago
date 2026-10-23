# Bonebog Pyramid v3.1: the GREYBOX of the new layout (Blake's driving notes, 2026-10-23).
# Driving first: the new lap, playable with plain shapes, so it can be driven and changed
# quickly; the swamp's look comes back once the lap is fun. Builds its own package,
# bonebog_pyramid_v3 (?track=bonebog_pyramid_v3); the current Bonebog stays as it is.
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/bonebog_v3.py      (the bpy module)
#
# About 1.5 km (v3.1: 25% shorter than the first greybox), nearly all of it bends:
#
#   A  The start along the old dike and the first S-bends (unchanged), then the first
#      green balloon is a zipper now.
#   B  A big hairpin back west and a weave across the heart of the swamp.
#   C  The Rib Bridge, climbing north.
#   D  The spiral: one and a quarter turns up round the great tree (+10 m) to the
#      treehouse village, then a fast drop to the pyramid's face.
#   E  The pyramid: rolling hills down the corridor, the turning chamber, and the great
#      hall: more hills and a jump over the river that runs through it and pours out of
#      the pyramid's side into the swamp.
#   F  Down the trestle and weaving home through the swamp to the dike.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import Vector, bmesh, lerp, smooth  # noqa: E402
from mathutils import kdtree  # noqa: E402

TRACK_ID = "bonebog_pyramid_v3"
WATER_Z = 0.0

START = (0.0, -200.0)
LAYOUT = [
    # v3.1 (Blake: "25% shorter, cut from the boring parts"): the start straight is 40 m
    # shorter, everything after the first S-bends is 70% of its old size (no corner
    # tighter than 26 m), and the long straight trestle out of the pyramid is an S now.
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


def _seg_pts(seg):
    return [p for p in PATH if p[3] == seg]


# The pyramid: round the corridor, the chamber and the hall, padded.
_pp = _seg_pts(18) + _seg_pts(19) + _seg_pts(20)
PYR_X0 = min(p[0] for p in _pp) - 30.0
PYR_X1 = max(p[0] for p in _pp) + 1.0
PYR_Y0 = min(p[1] for p in _pp) - 1.0
PYR_Y1 = max(p[1] for p in _pp) + 26.0
PYR_TOP = 58.0
FOUND_Z = 6.0


def in_pyramid(x, y, pad=0.0):
    return PYR_X0 - pad < x < PYR_X1 + pad and PYR_Y0 - pad < y < PYR_Y1 + pad


# The great tree, at the spiral's centre.
_h0 = _seg_pts(15)[0]
TREE = (_h0[0], _h0[1] - 30.0)

# The river through the great hall: west out of the pyramid's side.
_gx = None


# Route samples (every 4 m) with heights, and which are on the dike.
_samples = []
_d = 0.0
for _i, (_x, _y, _h, _s) in enumerate(PATH):
    if _i:
        _d += math.hypot(_x - PATH[_i - 1][0], _y - PATH[_i - 1][1])
    if not _samples or _d - _samples[-1][3] >= 4.0:
        dike = _s in (0, 29, 30) or (_s == 1 and _d < SEG[1] + 20)
        _samples.append((_x, _y, road_z(_d, _s), _d, dike))
_dike = [s for s in _samples if s[4]]
_tree = kdtree.KDTree(len(_dike))
for _i, s in enumerate(_dike):
    _tree.insert((s[0], s[1], 0.0), _i)
_tree.balance()

# Mud islands with giant trees, off the road, for the weave to wind between.
ISLANDS = []
for k in range(70):
    a = k * 2.399963
    r = 30 + 9.0 * math.sqrt(k) * 3.2
    x, y = 0.0 + r * math.cos(a) - 60, 0.0 + r * math.sin(a)
    near = min(math.hypot(x - s[0], y - s[1]) for s in _samples[::3])
    if 20 < near < 60 and not in_pyramid(x, y, 20) and math.hypot(x - TREE[0], y - TREE[1]) > 45:
        ISLANDS.append((x, y, 9 + 6 * ((k * 7) % 5) / 4))


def natural(x, y):
    """The swamp bed under the water, the dike under the start, mud islands, and the
    jungle rising on low hills all round."""
    h = -3.6 + 0.7 * math.sin(x / 19) * math.cos(y / 23)
    _, i, d = _tree.find((x, y, 0.0))
    h = max(h, 2.2 - 3.4 * smooth((d - 14.0) / 12.0) - 1.6 * smooth((d - 26.0) / 10.0))
    for ix, iy, r in ISLANDS:
        di = math.hypot(x - ix, y - iy)
        if di < r + 12:
            h = max(h, 1.2 - 4.8 * smooth((di - r * 0.6) / (r * 0.4 + 12)))
    if in_pyramid(x, y, 14):
        h = max(h, FOUND_Z - 1.0)
    rr = math.hypot((x + 40) / 1.0, (y - 0) / 1.0)
    h = max(h, -4 + 30 * smooth((rr - 380) / 60))
    return h


def classify(c, n, info):
    if in_pyramid(c.x, c.y, -2):
        return None
    if c.z < WATER_Z - 0.4:
        return ("bog_mud", "mud")
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


def stepped_pyramid(c, name):
    """One closed mesh: a foundation and six stepped tiers (so the tunnel can be cut)."""
    bm = bmesh.new()
    x0, x1, y0, y1 = PYR_X0, PYR_X1, PYR_Y0, PYR_Y1
    tiers = [(-14.0, -4.0, FOUND_Z), (0.0, FOUND_Z, 24.0)]
    z = 24.0
    for k in range(1, 6):
        tiers.append((10.0 * k, z, z + 7.0))
        z += 7.0
    rings = []
    for inset, zb, zt in tiers:
        q = [(x0 + inset, y0 + inset), (x1 - inset, y0 + inset), (x1 - inset, y1 - inset), (x0 + inset, y1 - inset)]
        rings.append([bm.verts.new((px, py, zb)) for px, py in q])
        rings.append([bm.verts.new((px, py, zt)) for px, py in q])
    for lo, hi in zip(rings, rings[1:]):
        for i in range(4):
            bm.faces.new((lo[i], lo[(i + 1) % 4], hi[(i + 1) % 4], hi[i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return c.mesh_object(name, bm, "Rocks")


def boolean_cut(ob, bm, name="Cut"):
    import bpy  # noqa: E402

    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    cutter = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(cutter)
    mod = ob.modifiers.new(name, "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
    mod.object = cutter
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter)


def main():
    import props  # noqa: E402

    c = kit.Course(TRACK_ID, "Bonebog Pyramid (v3 greybox)", "bonebog_swamp")
    c.route(ROUTE, width=14.5, bank=6.0)
    rail = ("bog_rail", "wall")
    stone = ("bog_carved", "wall")
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
        "temple": {"mat": "bog_paving", "surface": "road", "shoulder": 2.5, "shoulder_mat": ("bog_dark_stone", "road")},
        "ramp": {"mat": "bog_paving", "surface": "road", "shoulder": 2.5, "shoulder_mat": ("bog_dark_stone", "road"), "barrier": 1.0, "barrier_mat": stone},
    }

    def label(smp):
        s = smp.s
        seg = seg_of(s)
        if GAP[0] <= s <= GAP[1]:
            return "gap"
        if seg == 20 and GAP[0] - 12 <= s < GAP[0]:
            return "ramp"
        if 18 <= seg <= 20:
            return "temple"
        if seg in (0, 29, 30) or (seg == 1 and s < SEG[1] + 20):
            return "dike"
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
            # foot (never a kicker curling up at the end: that stops karts dead or fires
            # them straight up).
            def lift(u, n, w=12.0, rise=1.6, t0=0.35):
                v = max(0.0, min(1.0, (u - (n - w)) / w))
                k = 1.0 / (1.0 - t0 / 2.0)
                return rise * (k * v * v / (2 * t0) if v < t0 else k * (v - t0 / 2.0))

            specials.append((s0, s1, "ramp", {"lift": lift}))
        elif k != "boardwalk":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "boardwalk", max_len=200.0))

    X0, X1, Y0, Y1 = -420, 340, -380, 400
    c.terrain("Swamp", X0, X1, Y0, Y1, 6.0, natural, classify, near=10.0, fade=16.0, under=0.2)
    c.disc("Swamp Water", -40, 10, 470, WATER_Z, c.lib("bog_water", "deep_water"), n=64)

    def under(x, y):
        if in_pyramid(x, y, -1):
            return None
        return natural(x, y) - 0.4

    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 6.0, under, c.lib("bog_bank", "grass"))

    # The pyramid, with its passage cut through: corridor, chamber, hall.
    pyr = stepped_pyramid(c, "Pyramid")
    t0, t1 = SEG[18] - 4, SEG[21] + 4
    c.tunnel(pyr, t0, t1, half=c.width / 2 + 3.0, height=15.0, pad=8.0)
    # The river across the hall, at the jump: a channel west out of the pyramid's side.
    q = c.at((GAP[0] + GAP[1]) / 2)
    gx, gy = q.p.x, q.p.y
    cut = bmesh.new()
    props.cuboid(cut, ((PYR_X0 - 10 + gx + 12) / 2, gy, FOUND_Z + 2.0), (gx + 12 - PYR_X0 + 10, 12.0, 6.0))
    boolean_cut(pyr, cut, "River Cut")
    c.paint_rock(pyr, ("bog_stone", "wall"), ("bog_moss_ground", "grass"), floor=("bog_dark_stone", "road"), top_z=PYR_TOP - 4, floor_z=FOUND_Z + 6)
    c.ribbon("Hall River", [(gx + 10, gy, 11), (PYR_X0 + 2, gy, 11)], 11, FOUND_Z + 0.4, c.lib("bog_water", "deep_water"), steps=2)
    props.falls(c, "Pyramid Falls", PYR_X0 - 0.5, gy, FOUND_Z + 0.6, WATER_Z, 9.0, 12.0, facing=-1, throw=3.0, angle=-math.pi / 2, veils=2)
    # Its hidden floor (not across the river channel, so missing the jump drops you in).
    floor = []
    s = t0 - 8
    while s <= t1 + 8:
        if not (GAP[0] - 1 <= s <= GAP[1] + 1):
            q = c.at(s)
            floor.append((q.p.x, q.p.y, 2 * (c.width / 2 + 3.0) + 2.0, q.p.z - 0.25))
        else:
            if floor:
                c.ribbon("Hall Floor %d" % len(floor), floor, 26, 0, c.lib("bog_dark_stone", "road"), coll="Collision", role="collision", steps=4)
            floor = []
        s += 2.0
    if floor:
        c.ribbon("Hall Floor End", floor, 26, 0, c.lib("bog_dark_stone", "road"), coll="Collision", role="collision", steps=4)
    lights = []
    s = t0 + 6
    k = 0
    while s < t1 - 4:
        q = c.at(s)
        lights.append(tuple(q.side((1 if k % 2 else -1) * (c.width / 2 + 2.0), 6.0)))
        s += 11.0
        k += 1
    c.glow([pyr], lights, 12.0, (1.3, 0.95, 0.6), base=0.45, region=lambda w: in_pyramid(w.x, w.y) and w.z < 24)
    for x, y, z in lights:
        g = c.game(x, y, z)
        c.entity("torch", x=g[0], y=g[1], z=g[2])

    # The great tree the spiral climbs, its crown high over the village.
    bm = bmesh.new()
    tr = props.ring(bm, TREE, 11.0, -4.0, 14)
    top = props.ring(bm, TREE, 8.0, 46.0, 14)
    props.loft(bm, [tr, top])
    trunk = c.mesh_object("Great Tree", bm, "Props")
    c.assign(trunk, c.lib("giant_bark", "wall"))
    bm = bmesh.new()
    for k in range(6):
        a = k * math.tau / 6
        props.blob(bm, (TREE[0] + 16 * math.cos(a), TREE[1] + 16 * math.sin(a), 50.0), 14.0, sz=0.45, subdiv=1)
    props.blob(bm, (TREE[0], TREE[1], 56.0), 18.0, sz=0.5, subdiv=2)
    crown = c.mesh_object("Great Tree Crown", bm, "Props", "visual")
    c.assign(crown, c.lib("canopy_dark"))
    # The treehouse village: huts on stilts beside the road out of the spiral.
    huts = bmesh.new()
    s = SEG[16] + 6
    k = 0
    while s < SEG[17] - 4:
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 6.5))
            props.cuboid(huts, (p.x, p.y, p.z - 6.0), (0.8, 0.8, 14.0))
            props.cuboid(huts, (p.x, p.y, p.z + 0.6), (6.0, 5.0, 0.5))
            props.cuboid(huts, (p.x, p.y, p.z + 2.4), (4.4, 3.8, 3.4))
        s += 14.0
        k += 1
    hut = c.mesh_object("Treehouses", huts, "Props")
    c.assign(hut, c.lib("bog_boards", "wall"))
    # Giant trees on the islands, for the weave to wind between.
    bm = bmesh.new()
    for x, y, r in ISLANDS:
        props.loft(bm, [props.ring(bm, (x, y), 3.2, -2.0, 8), props.ring(bm, (x, y), 2.2, 30.0, 8)])
    trunks = c.mesh_object("Swamp Trees", bm, "Props")
    c.assign(trunks, c.lib("giant_bark", "wall"))
    bm = bmesh.new()
    for x, y, r in ISLANDS:
        props.blob(bm, (x, y, 32.0), 10.0, sz=0.45, subdiv=1)
    cano = c.mesh_object("Swamp Canopy", bm, "Props", "visual")
    c.assign(cano, c.lib("canopy_dark"))

    c.start_line()
    # Zippers: off the start, the first green balloon's spot (Blake's note), on the Rib
    # Bridge's climb, out of the spiral and down out of the pyramid.
    c.zipper(55, 0)
    c.zipper(SEG[5] + 15, 0)
    c.zipper(SEG[12] + 15, 0)
    c.zipper(SEG[17] + 5, 0)
    c.zipper(SEG[20] + 4, 0)  # into the hall, up to speed for the jump
    c.zipper(SEG[21] + 13, 0)  # (3 m further on than at first: Blake's note)
    for at, across in ((95, -3), (SEG[3] + 20, 0), (SEG[8] + 20, 0), (SEG[15] + 80, 0), (SEG[18] + 30, 0), (SEG[26] + 10, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (130, -4, "red"),
        (130, 4, "blue"),
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

    kit.paint.shade_roads(c.pieces, 0.35)
    c.finish()
    print("lap", round(c.length, 1))


if __name__ == "__main__":
    main()
