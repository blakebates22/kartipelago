# Bonebog Pyramid: Prehistoric World, course 3. "Mysterious swamp groove."
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/bonebog_pyramid.py      (the bpy module)
#
# A misty swamp of giant fossils. The old paved road starts in the south and runs north
# beneath the ribs of a long-dead giant, then out across the water on a wooden
# causeway, slithers through S-bends of slick mud and climbs to the ancient stepped
# pyramid, straight through its heart. Back on the swamp it crosses a lagoon on another
# causeway and slides through more mud to the line.
#
#   stone road   normal grip       wooden causeway  firm
#   wet mud      slippery          shallow water    slow (off the causeways)
#
# Saves tracks-src/bonebog_pyramid.blend and exports public/tracks/bonebog_pyramid/.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import props  # noqa: E402
from course_kit import Vector, bmesh, lerp, smooth  # noqa: E402

TRACK_ID = "bonebog_pyramid"
WATER_Z = -0.3
PYR = (-64.0, 186.0)  # the pyramid's centre
PYR_HALF = 42.0  # half the base
PYR_TIERS = 5
TIER_H = 6.0

ROUTE = [
    (0, -140, 0.6),  # start / finish: the old paved road, heading north
    (2, -84, 0.6),
    (0, -24, 0.6),  # under the giant's ribs
    (22, 22, 0.8),
    (70, 42, 1.0),  # the east causeway
    (128, 42, 1.0),
    (168, 70, 0.8),
    (166, 118, 0.7),  # mud S-bends
    (128, 146, 0.7),
    (82, 156, 1.2),
    (38, 182, 2.6),  # up the causeway to the pyramid
    (0, 188, 4.0),
    (-64, 186, 4.0),  # through the pyramid
    (-124, 182, 3.2),
    (-160, 156, 1.6),
    (-174, 110, 1.0),
    (-166, 56, 1.0),  # the lagoon causeway
    (-150, 4, 1.0),
    (-124, -44, 0.7),  # mud S-bends home
    (-92, -82, 0.7),
    (-70, -126, 0.6),
    (-36, -158, 0.6),
]


def natural(x, y):
    """Low muddy islands in shallow water, a ring of misty jungle cliffs round it."""
    h = -0.75 + 0.9 * math.sin(x / 23) * math.cos(y / 19) + 0.6 * math.sin((x - y) / 31) + 0.35 * math.sin(x / 7.0 + y / 9.0)
    # Two lagoons the causeways cross.
    for (cx, cy), r in (((95, 40), 52), ((-160, 30), 50)):
        d = math.hypot(x - cx, y - cy)
        h = lerp(h, -1.6, smooth((r - d) / 18))
    r = math.hypot(x * 0.9, (y - 20) * 0.95)
    h += 26 * smooth((r - 215) / 30) * (0.8 + 0.2 * math.sin(math.atan2(y, x) * 5 + 1))
    return h


def in_pyramid(x, y, pad=0.0):
    return abs(x - PYR[0]) < PYR_HALF + pad and abs(y - PYR[1]) < PYR_HALF + pad


def classify(c, n, info):
    if in_pyramid(c.x, c.y, -2):
        return None
    if n.z < 0.62:
        return ("fossil_strata", "wall")
    if c.z < WATER_Z + 0.05:
        return ("swamp_mud", "mud")  # the swamp bed, under the water
    if c.z > 8:
        return ("jungle_leafcover", "grass")
    return ("swamp_moss", "grass")


def build_pyramid(c):
    """Five stepped tiers of carved blocks."""
    bm = bmesh.new()
    for k in range(PYR_TIERS):
        half = PYR_HALF - k * 7.0
        z0, z1 = k * TIER_H - (1.5 if k == 0 else 0.0), (k + 1) * TIER_H
        cx, cy = PYR
        lo = [bm.verts.new((cx + sx * half, cy + sy * half, z0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        hi = [bm.verts.new((v.co.x, v.co.y, z1)) for v in lo]
        bm.faces.new(list(reversed(lo)))
        bm.faces.new(hi)
        for i in range(4):
            bm.faces.new((lo[i], lo[(i + 1) % 4], hi[(i + 1) % 4], hi[i]))
    # A little shrine on top.
    half = 6.0
    z0, z1 = PYR_TIERS * TIER_H, PYR_TIERS * TIER_H + 7.0
    cx, cy = PYR
    lo = [bm.verts.new((cx + sx * half, cy + sy * half, z0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    hi = [bm.verts.new((v.co.x, v.co.y, z1)) for v in lo]
    bm.faces.new(list(reversed(lo)))
    bm.faces.new(hi)
    for i in range(4):
        bm.faces.new((lo[i], lo[(i + 1) % 4], hi[(i + 1) % 4], hi[i]))
    ob = c.mesh_object("Pyramid", bm, "Landmarks")
    return ob


def skeleton(c, s0, s1, every=7.0):
    """The giant's ribs arching over the road from s0 to s1, joined by its spine, with
    its tail trailing off behind and its skull at the far end."""
    bm = bmesh.new()
    n = int((s1 - s0) / every)
    spine = []
    for k in range(n + 1):
        t = k / n
        smp = c.at(s0 + (s1 - s0) * t)
        size = 0.55 + 0.45 * math.sin(math.pi * min(1, t * 1.15))  # biggest in the middle
        half = smp.w / 2 + 2.5
        apex = smp.p.z + 7 + 6 * size
        spine.append(smp.p + Vector((0, 0, apex - smp.p.z + 0.6)))
        for side in (-1, 1):
            pts = []
            for j in range(7):
                u = j / 6
                o = side * half * (1 - u) ** 0.9
                z = smp.p.z - 1.0 + (apex - smp.p.z + 1.0) * math.sin(u * math.pi / 2) ** 0.8
                p = smp.p + smp.r * o + Vector((0, 0, z - smp.p.z)) + smp.t * (-1.5 * u)
                pts.append(p)
            props.tube(bm, pts, [0.55 * (1.2 - 0.5 * j / 6) * (0.7 + 0.5 * size) for j in range(7)], n=6)
    props.tube(bm, spine, 0.9, n=6)
    # Vertebrae knobs along the spine.
    for p in spine:
        props.blob(bm, (p.x, p.y, p.z + 0.6), 0.9, subdiv=1)
    # The tail: off behind the first rib, sinking into the swamp.
    a = c.at(s0)
    tail = [a.p + Vector((0, 0, 8)) - a.t * (6 * k) + a.r * (2.5 * math.sin(k * 0.8)) + Vector((0, 0, -1.6 * k)) for k in range(7)]
    props.tube(bm, tail, [0.8 - 0.1 * k for k in range(7)], n=6)
    ob = c.mesh_object("Giant Skeleton", bm, "Landmarks")
    c.assign(ob, c.lib("bone"))
    ob.data.shade_flat()
    return ob


def scenery(c):
    ter = list(c.coll("Terrain").objects)
    for piece in c.pieces:
        if "causeway" in piece.name:
            props.piers(c, piece, every=7, mat=("palm_bark", "wall"), size=0.35, terrain=ter, inset=0.8)
    skeleton(c, kit.s_near(c, 2, -100), kit.s_near(c, 0, -20))
    sk = props.skull(c)
    smp = c.at(kit.s_near(c, 0, -14))
    p = smp.side(smp.w / 2 + 9)
    c.place(sk, p.x, p.y, -0.6, rot=math.atan2(smp.t.y, smp.t.x) + 2.6, scale=1.4, coll="Landmarks")
    for x, y, rot, sc in ((150, 0, 1.0, 1.0), (-110, 120, 2.5, 1.2), (60, 200, 4.0, 0.9)):
        if props.clear_of_road(c, x, y, 10):
            c.place(sk, x, y, -0.8, rot=rot, scale=sc, coll="Landmarks")
    trees = [props.swamp_tree(c, v) for v in range(2)]
    reeds, caps = props.reeds(c), props.glow_caps(c)
    fern = props.fern(c, "swamp_moss")
    rocks = [props.boulder(c, "swamp_stone", v) for v in range(2)]

    def near_road(m0, m1, wet=None):
        def ok(x, y, z):
            smp, d = c.nearest(x, y)
            if in_pyramid(x, y, 6) or not (smp.w / 2 + m0 < d < smp.w / 2 + m1):
                return False
            return wet is None or ((z < WATER_Z + 0.3) == wet)
        return ok

    for v, t in enumerate(trees):
        props.scatter(c, t, 26, (-215, 215, -200, 250), near_road(8, 60), ter, seed=110 + v, scale=(0.9, 1.5), sink=0.3)
    props.scatter(c, reeds, 90, (-215, 215, -200, 250), near_road(2.5, 45, wet=True), ter, seed=120, role="visual", sink=0.0)
    props.scatter(c, caps, 40, (-215, 215, -200, 250), near_road(3, 35, wet=False), ter, seed=130, role="visual")
    props.scatter(c, fern, 50, (-215, 215, -200, 250), near_road(2.5, 40, wet=False), ter, seed=140, role="visual")
    for v, r in enumerate(rocks):
        props.scatter(c, r, 8, (-215, 215, -200, 250), near_road(6, 50), ter, seed=150 + v, scale=(1.2, 2.5))


def main():
    c = kit.Course(TRACK_ID, "Bonebog Pyramid", "fossil_swamp")
    c.route(ROUTE, width=14.0, bank=6.0)
    c.kinds = {
        "stone": {"mat": "swamp_stone", "surface": "road", "shoulder": 1.5, "shoulder_mat": ("swamp_moss", "dirt")},
        "mud": {"mat": "swamp_mud", "surface": "mud", "shoulder": 1.5, "shoulder_mat": ("swamp_mud", "mud")},
        "causeway": {
            "mat": "wood_planks",
            "surface": "road",
            "shoulder": 0.4,
            "shoulder_mat": ("wood_planks", "road"),
            "deck": 1.6,
            "deck_mat": ("palm_bark", "wall"),
            "ground": False,
        },
        "temple": {"mat": "pyramid_step", "surface": "road", "shoulder": 1.0, "shoulder_mat": ("swamp_stone", "road")},
    }

    def label(smp):
        x, y = smp.p.x, smp.p.y
        if in_pyramid(x, y, 2):
            return "temple"
        if natural(x, y) < WATER_Z - 0.15 and smp.p.z - natural(x, y) > 1.0:
            return "causeway"
        if (x > 60 and y > 80) or (x < -60 and y < -20):
            return "mud"
        return "stone"

    specials = [r for r in kit.runs(c, label) if r[2] != "stone"]
    c.roads(kit.plan(c, specials, "stone"))

    c.terrain("Swamp", -250, 250, -230, 270, 3.3, natural, classify, near=8.5, fade=14.0, under=0.15)
    c.disc("Swamp Water", 0, 20, 260, WATER_Z, c.lib("swamp_water"), n=48)

    pyr = build_pyramid(c)
    inside = kit.crossings(c, lambda s: in_pyramid(s.p.x, s.p.y, 0.5), margin=0)
    s0, s1 = max(inside, key=lambda r: r[1] - r[0])
    c.tunnel(pyr, s0, s1, height=9.5, pad=10.0)
    c.paint_rock(pyr, ("pyramid_step", "wall"), ("swamp_stone", "road"), floor=("swamp_stone", "road"), floor_z=6)

    c.start_line()
    scenery(c)
    L = c.length
    c.zipper(kit.s_near(c, 1, -60), 0)  # under the ribs
    c.zipper(kit.s_near(c, 0, 188) - 10, 0)  # into the pyramid
    c.zipper(L - 60, -3)
    for at, across in ((kit.s_near(c, 98, 42), 0), (kit.s_near(c, 128, 146), 2), (s1 + 20, -2), (kit.s_near(c, -166, 56), 0), (kit.s_near(c, -92, -82), 2)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (kit.s_near(c, 0, -24), -4, "red"),
        (kit.s_near(c, 0, -24), 4, "blue"),
        (kit.s_near(c, 166, 118), 0, "green"),
        (kit.s_near(c, -174, 110), 0, "yellow"),
        (kit.s_near(c, -124, -44), -3, "rainbow"),
    ):
        c.balloon(at, across, col)

    ter = list(c.coll("Terrain").objects)
    c.preset("sun", ter + [pyr], 0.3)
    c.preset("bottoms", [pyr], 0.4)
    c.preset("cover", [pyr], 0.7)
    kit.paint.shade_roads(c.pieces, 0.6)
    c.finish()


main()
