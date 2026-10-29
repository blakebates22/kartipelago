# Dinosaur Valley's village, made over (Blake, Oct 28, review-valley_region 3): huts with
# real doorways, each one different ("lots of character"), hearths with plain logs, a well
# with a shaft going down, the kart shed with its sign and a real kart taken apart (the
# game's own kart: a `kart_wreck` entity), carved totems as detailed as the characters (a
# `village_totem` entity, built in src/render/villageDecor.ts), and dirt paths that curve
# between the huts as ribbons laid on the land.
# SPDX-License-Identifier: MIT

import math

import bpy

import gulch_scenery as gs
from course_kit import Vector, bmesh, materials, rnd
from props import _faces, blob, cuboid, loft, ring, tube
from region_props import _cyl


# ------------------------------------------------------------------ building blocks


def proto_mesh(c, name, fill, shade=None):
    """A prop prototype built with a gulch_scenery.Mesh (pieces with their own
    materials, some with their own UVs), shared by every copy like c.proto's. `shade(p)`:
    a brightness (0..1) for each corner at its prop-space position p, painted into the
    mesh's vertex colour (the dark down a well)."""
    if name in c.protos:
        return name
    m = gs.Mesh()
    fill(m)
    me = bpy.data.meshes.new("Prop " + name)
    m.bm.to_mesh(me)
    m.bm.free()
    tmp = bpy.data.objects.new("tmp", me)
    c.coll("Prop Library").objects.link(tmp)
    for mat, faces in m.slots.items():
        c.assign(tmp, c.lib(*mat), faces)
    for mat, faces in m.raw.items():
        lm = c.lib(*mat)
        names = [x.name if x else None for x in me.materials]
        if lm.name in names:
            slot = names.index(lm.name)
        else:
            me.materials.append(lm)
            slot = len(me.materials) - 1
        for i in faces:
            me.polygons[i].material_index = slot
    materials.keep_uvs(tmp, range(len(me.polygons)))
    if shade:
        materials.ensure_paint(me)
        ca = me.color_attributes.get(materials.PAINT)
        for lp in me.loops:
            k = max(0.0, min(1.0, shade(me.vertices[lp.vertex_index].co)))
            ca.data[lp.index].color = (k, k, k, 1.0)
    bpy.data.objects.remove(tmp)
    c.protos[name] = me
    return name


BARK = ("log_bark", "wall")
END = ("log_cut", "wall")


def log(m, a, b, r, seed=0, n=10, bark=BARK):
    """A log from a to b (radius r, a little lumpy), its bark round it and its cut ends
    in growth rings (their UVs made to fit each end)."""
    a, b = Vector(a), Vector(b)
    t = (b - a).normalized()
    side = t.cross(Vector((0, 0, 1)))
    if side.length < 1e-3:
        side = Vector((1, 0, 0))
    side.normalize()
    up = side.cross(t).normalized()
    steps = max(2, int((b - a).length / 0.6))
    rings = []

    def make(bm):
        for k in range(steps + 1):
            p = a + (b - a) * (k / steps)
            rr = []
            for i in range(n):
                ang = i * math.tau / n
                lump = 1.0 + 0.08 * (rnd(seed * 31 + k * 7 + i) - 0.5) * 2
                rr.append(bm.verts.new(p + (side * math.cos(ang) + up * math.sin(ang)) * r * lump))
            rings.append(rr)
        for lo, hi in zip(rings, rings[1:]):
            for i in range(n):
                bm.faces.new((lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i]))

    m.add(bark, make)
    for end, sgn in ((rings[0], -1), (rings[-1], 1)):
        centre = sum((v.co for v in end), Vector()) / n
        pts = [v.co.copy() for v in end]
        if sgn < 0:
            pts = list(reversed(pts))
        uvs = []
        for p in pts:
            d = p - centre
            u, v = d.dot(side) / r, d.dot(up) / r
            uvs.append((0.5 + 0.47 * u, 0.5 + 0.47 * v))
        m.quad(END, pts, uvs)


def both(bm, pts):
    """A face seen from both sides (inside a doorway, where either side may show)."""
    a = [bm.verts.new(p) for p in pts]
    b = [bm.verts.new(p) for p in reversed(pts)]
    bm.faces.new(a)
    bm.faces.new(b)


def stones_ring(m, r, n, z, size, seed, skip=None, mat=("ruin_stone", "wall")):
    for i in range(n):
        a = i * math.tau / n + 0.2 * rnd(seed + i)
        if skip and skip(a):
            continue
        s = size * (0.8 + 0.4 * rnd(seed * 3 + i))
        m.add(mat, lambda bm, a=a, s=s: blob(bm, (r * math.cos(a), r * math.sin(a), z), s, sx=1.3, sz=0.75, subdiv=1))


# ------------------------------------------------------------------ the hearth


def hearth(c):
    """A camp hearth (Blake, notes 2 and 6: the benches "should just be a normal log"): a
    ring of stones round a bed of coals, charred sticks crossed in it, the fire, and three
    log benches round it, plain felled logs with their cut ends showing."""

    def fill(m):
        stones_ring(m, 1.45, 12, 0.18, 0.36, 11)
        m.add(("charred_bark", "wall"), lambda bm: _cyl(bm, (0, 0, 0.02), 1.15, 0.12, n=12))
        for i in range(5):
            a = i * math.tau / 5 + 0.3
            ca, sa = math.cos(a), math.sin(a)
            m.add(("charred_bark", "wall"),
                  lambda bm, ca=ca, sa=sa: tube(bm, [(1.1 * ca, 1.1 * sa, 0.12), (0.1 * ca, 0.1 * sa, 1.2)], 0.11, n=6))

        def flames(bm):
            for i, (r, w, hh) in enumerate(((0.0, 0.5, 1.9), (0.32, 0.34, 1.35), (0.34, 0.32, 1.2), (0.3, 0.3, 1.45))):
                a = i * 2.4
                res = bmesh.ops.create_cone(bm, cap_ends=False, segments=6, radius1=w, radius2=0.0, depth=hh)
                for v in res["verts"]:
                    v.co += Vector((r * math.cos(a), r * math.sin(a), 0.2 + hh / 2))

        m.add(("campfire_flame", "wall"), flames)
        for i in range(3):
            a = i * math.tau / 3 + 0.5
            ca, sa = math.cos(a), math.sin(a)
            cx, cy = 3.2 * ca, 3.2 * sa
            tx, ty = -sa * 1.3, ca * 1.3
            rr = 0.3 + 0.03 * i
            log(m, (cx - tx, cy - ty, rr * 0.85), (cx + tx, cy + ty, rr * 0.85), rr, seed=i + 3)

    return proto_mesh(c, "Village Hearth", fill)


# ------------------------------------------------------------------ the well

WELL_R = 1.25  # the shaft's radius
KERB_R = 1.7


def well(c):
    """The camp's well (Blake, note 4: "lets make the well actually have a hole going
    down"): a stone kerb, and inside it a shaft of stone going down into the dark to the
    water, a bucket on its rope halfway down; two posts and a beam with a winding drum,
    under a little thatched roof. (well_hole cuts the land away under it.)"""

    def fill(m):
        n = 16
        stone = ("ruin_stone", "wall")
        deep = ("bog_dark_stone", "wall")

        def kerb(bm):
            lo = ring(bm, (0, 0), KERB_R, -0.6, n)
            hi = ring(bm, (0, 0), KERB_R, 1.0, n)
            ihi = ring(bm, (0, 0), WELL_R, 1.0, n)
            loft(bm, [lo, hi], cap_top=False)
            for i in range(n):
                bm.faces.new((hi[i], hi[(i + 1) % n], ihi[(i + 1) % n], ihi[i]))

        m.add(stone, kerb)

        # The shaft, seen from inside: stone going down, darker the deeper it goes.
        def shaft(bm, z0, z1):
            a = ring(bm, (0, 0), WELL_R, z0, n)
            b = ring(bm, (0, 0), WELL_R, z1, n)
            for i in range(n):
                bm.faces.new((a[i], b[i], b[(i + 1) % n], a[(i + 1) % n]))

        m.add(stone, lambda bm: shaft(bm, -0.8, 1.0))
        m.add(deep, lambda bm: shaft(bm, -3.4, -0.8))
        m.add(("dark_pool", "wall"), lambda bm: bm.faces.new(ring(bm, (0, 0), WELL_R, -3.0, n)))
        for i in range(10):
            a = i * math.tau / 10 + 0.2
            m.add(stone, lambda bm, a=a: blob(bm, (1.72 * math.cos(a), 1.72 * math.sin(a), 0.55 + 0.25 * (i % 2)), 0.32, sx=1.4,
                                              sz=0.8, subdiv=1))
        wood = ("palm_bark", "wall")
        for s in (-1, 1):
            m.add(wood, lambda bm, s=s: cuboid(bm, (s * 1.55, 0, 1.6), (0.26, 0.26, 3.2)))
        m.add(wood, lambda bm: cuboid(bm, (0, 0, 2.7), (3.4, 0.2, 0.2)))
        m.add(BARK, lambda bm: _cyl(bm, (0, 0, 2.45), 0.32, 0.1, n=8))
        # The rope down the shaft, and the bucket hanging in it.
        m.add(("rope_rail", "wall"), lambda bm: tube(bm, [(0, 0, 2.5), (0, 0, -0.9)], 0.03, n=4))
        m.add(("wood_planks", "wall"), lambda bm: _cyl(bm, (0, 0, -1.4), 0.28, 0.5, n=10, r2=0.34))
        m.add(("iron", "wall"), lambda bm: tube(bm, [(-0.3, 0, -0.85), (0, 0, -0.6), (0.3, 0, -0.85)], 0.025, n=4))

        def roof(bm):
            for s in (-1, 1):
                v = [bm.verts.new(q) for q in ((-2.0, s * 0.05, 3.0), (2.0, s * 0.05, 3.0), (2.0, s * 1.6, 2.35),
                                               (-2.0, s * 1.6, 2.35))]
                bm.faces.new(v if s > 0 else list(reversed(v)))

        m.add(("thatch", "wall"), roof)

    def shade(p):
        # (Darker down the shaft: only inside it.)
        if math.hypot(p.x, p.y) > WELL_R + 0.02 or p.z > 1.0:
            return 1.0
        return 0.18 + 0.82 * max(0.0, (p.z + 3.0) / 4.0) ** 1.6

    return proto_mesh(c, "Village Well", fill, shade)


def well_hole(c, x, y, ground):
    """Cut the land away under the well (the land, and the floor under it), and lay a
    cobbled apron from the kerb out over the cut's ragged edge."""
    import bmesh as bmm

    cut = WELL_R + 0.15
    far = KERB_R
    for name in ("Valley", "Underfloor"):
        ob = bpy.data.objects.get(name)
        if ob is None or ob.type != "MESH":
            continue
        bm = bmm.new()
        bm.from_mesh(ob.data)
        mw = ob.matrix_world
        doomed = []
        for f in bm.faces:
            pts = [mw @ v.co for v in f.verts]
            if _poly_dist(pts, x, y) < cut:
                doomed.append(f)
                if name == "Valley":
                    far = max(far, max(math.hypot(p.x - x, p.y - y) for p in pts))
        bmm.ops.delete(bm, geom=doomed, context="FACES")
        bm.to_mesh(ob.data)
        bm.free()
    # The apron: from the kerb out past the cut, on the land.
    m = gs.Mesh()
    n = 28
    outer = far + 0.4

    def apron(bm):
        rings = []
        for r in (KERB_R - 0.05, (KERB_R + outer) / 2, outer):
            rr = []
            for i in range(n):
                a = i * math.tau / n
                px, py = x + r * math.cos(a), y + r * math.sin(a)
                rr.append(bm.verts.new((px, py, ground(px, py) + 0.04)))
            rings.append(rr)
        for lo, hi in zip(rings, rings[1:]):
            for i in range(n):
                bm.faces.new((lo[i], hi[i], hi[(i + 1) % n], lo[(i + 1) % n]))

    m.add(("camp_earth", "dirt"), apron)

    def verge(bm):
        a = []
        b = []
        for i in range(n):
            ang = i * math.tau / n
            for r, lst in ((outer, a), (outer + 1.0 + 0.3 * math.sin(ang * 3), b)):
                px, py = x + r * math.cos(ang), y + r * math.sin(ang)
                lst.append(bm.verts.new((px, py, ground(px, py) + (0.04 if lst is a else 0.02))))
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], b[i], b[j], a[j]))

    import region_textures as TX

    m.add((TX.blend_id("valley_grass", "camp_earth", 50), "dirt"), verge)
    m.build(c, "Well Apron", coll="Village", role="both")


def _poly_dist(pts, x, y):
    """How far (x, y) is from a polygon (0 inside it), in plan."""
    inside = False
    n = len(pts)
    best = 1e9
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        if (a.y > y) != (b.y > y) and x < (b.x - a.x) * (y - a.y) / (b.y - a.y + 1e-12) + a.x:
            inside = not inside
        dx, dy = b.x - a.x, b.y - a.y
        t = max(0.0, min(1.0, ((x - a.x) * dx + (y - a.y) * dy) / (dx * dx + dy * dy + 1e-12)))
        best = min(best, math.hypot(x - a.x - t * dx, y - a.y - t * dy))
    return 0.0 if inside else best


# ------------------------------------------------------------------ the huts

# Each hut's look (Blake, note 9: "the same style but lets have them vary"): its size,
# walls, roof, thatch, doorway and what's about it.
HUTS = [
    dict(r=3.0, h=2.4, wall="daub_ochre", roof="tiered", thatch="thatch", door="open", band=True, win=1,
         extras=("gourds", "firewood")),
    dict(r=3.5, h=2.6, wall="daub_cream", roof="finial", thatch="thatch_dark", door="hide", band=False, win=2,
         extras=("pots", "rack")),
    dict(r=2.7, h=2.2, wall="daub_rose", roof="dome", thatch="thatch_pale", door="open", band=True, win=1,
         extras=("bench", "pots")),
    dict(r=3.8, h=2.8, wall="daub_ochre", roof="tiered", thatch="thatch_dark", door="porch", band=True, win=2,
         extras=("gourds", "bench", "chime")),
    dict(r=3.2, h=2.5, wall="daub_cream", roof="ragged", thatch="thatch_pale", door="hide", band=True, win=1,
         extras=("skull", "firewood")),
    dict(r=2.9, h=2.3, wall="daub_rose", roof="finial", thatch="thatch", door="shut", band=False, win=2,
         extras=("pots", "chime")),
    # The grand one (Blake, Riverbend note 11: "make this one more grand, keeping the same
    # style, but I would like a chimney with smoke coming out").
    dict(r=4.8, h=3.1, wall="daub_cream", roof="tiered", thatch="thatch_dark", door="porch", band=True, win=2,
         extras=("gourds", "pots", "firewood", "bench", "chime"), chimney=True),
]
GRAND = 99  # (asks for the grand one: the last look)


def _vi(v):
    """Which look: the grand one only when asked for; otherwise round the others."""
    return len(HUTS) - 1 if v == GRAND else v % (len(HUTS) - 1)
DOOR_HW = 0.7  # half the doorway's width
DOOR_H = 2.05


def hut_chimney(v):
    """Where a hut's chimney smokes from (its local x, y, z), or None."""
    s = HUTS[_vi(v)]
    if s.get("chimney"):
        return (-s["r"] * 0.46, 0.6, s["h"] + 3.65)
    if s["roof"] != "dome":
        return None
    return (-s["r"] * 0.35, 0.4, s["h"] + 3.0)


def hut(c, v):
    """A villager's hut, look `v` of HUTS (its doorway at +X): a stone plinth, daub walls
    with a real doorway (a frame and lintel, a door or a hide, a dark room behind it),
    windows, a painted band, the roof in its own style, and its odds and ends about it."""
    s = HUTS[_vi(v)]
    R, Hw = s["r"], s["h"]
    da = math.asin(DOOR_HW / R)
    T = 0.3  # the walls' thickness

    def P(r, a, z):
        return (r * math.cos(a), r * math.sin(a), z)

    def fill(m):
        wall = (s["wall"], "wall")
        thatch = (s["thatch"], "wall")
        timber = BARK
        dark = ("dark_corridor", "wall")
        # The walls, round from one side of the doorway to the other.
        n = 18

        def walls(bm):
            angs = [da + (math.tau - 2 * da) * k / n for k in range(n + 1)]
            lo = [bm.verts.new(P(R, a, -0.4)) for a in angs]
            hi = [bm.verts.new(P(R, a, Hw)) for a in angs]
            for k in range(n):
                bm.faces.new((lo[k], lo[k + 1], hi[k + 1], hi[k]))
            # Over the doorway.
            g = [-da + 2 * da * k / 3 for k in range(4)]
            a0 = [bm.verts.new(P(R, a, DOOR_H)) for a in g]
            a1 = [bm.verts.new(P(R, a, Hw)) for a in g]
            for k in range(3):
                bm.faces.new((a0[k], a0[k + 1], a1[k + 1], a1[k]))

        m.add(wall, walls)

        # The doorway's reveal (the walls' thickness) and the dark room behind.
        def reveal(bm):
            for sgn in (-1, 1):
                a = sgn * da
                o0, o1 = P(R, a, 0.0), P(R, a, DOOR_H)
                y = sgn * DOOR_HW
                i0, i1 = (R * math.cos(da) - T, y, 0.0), (R * math.cos(da) - T, y, DOOR_H)
                both(bm, (o0, i0, i1, o1))
            x0, x1 = R * math.cos(da), R * math.cos(da) - T
            both(bm, ((x0, -DOOR_HW, DOOR_H), (x0, DOOR_HW, DOOR_H), (x1, DOOR_HW, DOOR_H), (x1, -DOOR_HW, DOOR_H)))

        m.add(wall, reveal)

        def room(bm):
            x1, x2 = R * math.cos(da) - T, R * math.cos(da) - T - 1.8
            w = DOOR_HW + 0.5
            for q in (((x2, -w, 0), (x2, w, 0), (x2, w, DOOR_H), (x2, -w, DOOR_H)),  # back
                      ((x1, w, 0), (x2, w, 0), (x2, w, DOOR_H), (x1, w, DOOR_H)),  # sides
                      ((x2, -w, 0), (x1, -w, 0), (x1, -w, DOOR_H), (x2, -w, DOOR_H)),
                      ((x1, -w, 0.02), (x2, -w, 0.02), (x2, w, 0.02), (x1, w, 0.02)),  # floor, ceiling
                      ((x1, -w, DOOR_H), (x1, w, DOOR_H), (x2, w, DOOR_H), (x2, -w, DOOR_H))):
                both(bm, q)
            # (The wall face beside the doorway inside, so the room is closed.)
            for sgn in (-1, 1):
                both(bm, ((x1, sgn * DOOR_HW, 0), (x1, sgn * w, 0), (x1, sgn * w, DOOR_H), (x1, sgn * DOOR_HW, DOOR_H)))

        m.add(dark, room)

        # The frame: two posts and a lintel with carved ends, a threshold stone.
        xo = R * math.cos(da) + 0.06
        for sgn in (-1, 1):
            m.add(timber, lambda bm, sgn=sgn: cuboid(bm, (xo, sgn * (DOOR_HW + 0.08), DOOR_H / 2 + 0.05), (0.2, 0.2, DOOR_H + 0.1)))
        m.add(timber, lambda bm: cuboid(bm, (xo + 0.02, 0, DOOR_H + 0.16), (0.26, 2 * DOOR_HW + 0.7, 0.24)))
        for sgn in (-1, 1):
            m.add(END, lambda bm, sgn=sgn: blob(bm, (xo + 0.02, sgn * (DOOR_HW + 0.4), DOOR_H + 0.16), 0.17, subdiv=1))
        m.add(("ruin_stone", "wall"), lambda bm: cuboid(bm, (xo + 0.45, 0, 0.05), (0.9, 1.7, 0.16)))

        # The door.
        if s["door"] in ("open", "porch", "shut"):
            hinge = Vector((xo, DOOR_HW, 0.0))
            ang = 0.0 if s["door"] == "shut" else 1.15
            w, hh = 2 * DOOR_HW - 0.06, DOOR_H - 0.06
            d = Vector((math.sin(ang), -math.cos(ang), 0.0))  # along the door from its hinge
            nrm = Vector((math.cos(ang), math.sin(ang), 0.0))
            base = hinge + nrm * (-0.06 if s["door"] == "shut" else 0.02)
            up = Vector((0, 0, hh))
            front = [base + d * w, base, base + up, base + d * w + up]
            m.quad(("hut_door", "wall"), [tuple(p + nrm * 0.04) for p in front], [(1, 0), (0, 0), (0, 1), (1, 1)])
            m.quad(("wood_planks", "wall"), [tuple(p - nrm * 0.04) for p in reversed(front)], [(0, 0), (1, 0), (1, 1), (0, 1)])
        else:
            # A painted hide over the doorway, one corner tied back.
            x = xo + 0.05
            tl, tr = (x, DOOR_HW, DOOR_H), (x, -DOOR_HW, DOOR_H)
            br, bl = (x + 0.05, -DOOR_HW + 0.15, 0.95), (x + 0.02, DOOR_HW - 0.1, 0.15)
            m.quad(("painted_hide", "wall"), [bl, br, tr, tl], [(0.05, 0), (0.95, 0.4), (1, 1), (0, 1)])
            m.quad(("painted_hide", "wall"), [tl, tr, br, bl], [(0, 1), (1, 1), (0.95, 0.4), (0.05, 0)])
            m.add(("rope_rail", "wall"), lambda bm: tube(bm, [(x + 0.08, -DOOR_HW + 0.1, 0.95), (x + 0.05, -DOOR_HW - 0.06, 1.0)],
                                                        0.03, n=4))
        if s["door"] == "porch":
            # A little porch: two posts and a lean-to of thatch over the door.
            px = R + 1.7
            for sgn in (-1, 1):
                m.add(timber, lambda bm, sgn=sgn: tube(bm, [(px, sgn * 1.2, -0.1), (px, sgn * 1.2, 2.25)], 0.11, n=6))
            m.add(timber, lambda bm: cuboid(bm, (px, 0, 2.25), (0.16, 2.7, 0.16)))

            def lean(bm):
                v = [bm.verts.new(q) for q in ((R - 0.2, -1.5, Hw - 0.1), (R - 0.2, 1.5, Hw - 0.1), (px + 0.4, 1.5, 2.15),
                                               (px + 0.4, -1.5, 2.15))]
                bm.faces.new(v)
                v2 = [bm.verts.new(q) for q in ((R - 0.2, -1.5, Hw - 0.18), (px + 0.4, -1.5, 2.07), (px + 0.4, 1.5, 2.07),
                                                (R - 0.2, 1.5, Hw - 0.18))]
                bm.faces.new(v2)

            m.add(thatch, lean)

        # Windows: a timber frame round a dark (or lit) opening.
        wins = (1.85,) if s["win"] == 1 else (1.75, -1.75)
        for k, a in enumerate(wins):
            ca, sa = math.cos(a), math.sin(a)
            tx, ty = -sa, ca
            cx, cy = (R + 0.03) * ca, (R + 0.03) * sa
            z0, z1, hw = 1.25, 1.85, 0.32
            mat = ("window_lit", "wall") if (v + k) % 2 == 0 else ("dark_corridor", "wall")
            q = [(cx - tx * hw, cy - ty * hw, z0), (cx + tx * hw, cy + ty * hw, z0), (cx + tx * hw, cy + ty * hw, z1),
                 (cx - tx * hw, cy - ty * hw, z1)]
            m.quad(mat, q, [(0.25, 0), (0.75, 0), (0.75, 1), (0.25, 1)])
            rot = a - math.pi / 2
            for zz in (z0 - 0.05, z1 + 0.05):
                m.add(timber, lambda bm, zz=zz, rot=rot, cx=cx, cy=cy: cuboid(bm, (cx + ca * 0.05, cy + sa * 0.05, zz), (0.85, 0.12, 0.1),
                                                                              rot=rot))
            for sgn in (-1, 1):
                m.add(timber, lambda bm, sgn=sgn, rot=rot, cx=cx, cy=cy: cuboid(
                    bm, (cx + ca * 0.05 + tx * sgn * 0.37, cy + sa * 0.05 + ty * sgn * 0.37, (z0 + z1) / 2), (0.1, 0.12, 0.75), rot=rot))

        # The painted band round the walls.
        if s["band"]:
            def band(bm):
                angs = [da + 0.15 + (math.tau - 2 * da - 0.3) * k / n for k in range(n + 1)]
                lo = [bm.verts.new(P(R + 0.025, a, 1.0)) for a in angs]
                hi = [bm.verts.new(P(R + 0.025, a, 1.42)) for a in angs]
                for k in range(n):
                    # (Not over the windows.)
                    mid = (angs[k] + angs[k + 1]) / 2
                    if any(abs(math.atan2(math.sin(mid - w), math.cos(mid - w))) < 0.25 for w in wins):
                        continue
                    bm.faces.new((lo[k], lo[k + 1], hi[k + 1], hi[k]))

            m.add(("tribal_paint", "wall"), band)

        # The plinth: stones round the foot of the walls (not across the doorway).
        stones_ring(m, R + 0.12, 22, 0.12, 0.3, v * 7 + 3, skip=lambda a: abs(math.atan2(math.sin(a), math.cos(a))) < da + 0.25)

        # The roof.
        Re, ze = R + 1.05, Hw - 0.25
        roof_fill(m, s["roof"], R, Hw, Re, ze, thatch, v)
        if s.get("chimney"):
            cx, cy = -R * 0.46, 0.6
            m.add(("ruin_stone", "wall"), lambda bm: _cyl(bm, (cx, cy, Hw + 0.6), 0.5, 3.0, n=8, r2=0.42))
            m.add(("ruin_stone", "wall"), lambda bm: _cyl(bm, (cx, cy, Hw + 3.45), 0.5, 0.18, n=8))
            m.add(("charred_bark", "wall"), lambda bm: _cyl(bm, (cx, cy, Hw + 3.63), 0.3, 0.02, n=8))

        # What's about it.
        for e in s["extras"]:
            extra(m, e, R, Hw, Re, ze, v)

    return proto_mesh(c, "Village Hut %d" % _vi(v), fill)


def _cone(bm, rings_rz, n, tip=None, jag=0.0, seed=0):
    """A roof surface through rings (r, z), optionally to a tip; `jag`: how ragged the
    first ring (the eave) is."""
    rings = []
    for j, (r, z) in enumerate(rings_rz):
        rr = []
        for i in range(n):
            a = i * math.tau / n
            zz = z - (jag * (0.5 + 0.5 * rnd(seed + i)) if j == 0 and i % 2 == 0 else 0.0)
            rr.append(bm.verts.new((r * math.cos(a), r * math.sin(a), zz)))
        rings.append(rr)
    for lo, hi in zip(rings, rings[1:]):
        for i in range(n):
            bm.faces.new((lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i]))
    if tip is not None:
        t = bm.verts.new((0, 0, tip))
        last = rings[-1]
        for i in range(n):
            bm.faces.new((last[i], last[(i + 1) % n], t))
    return rings


def roof_fill(m, kind, R, Hw, Re, ze, thatch, v):
    n = 20
    under = ("thatch_dark", "wall")

    # The eaves' underside, from the eave in to the top of the walls.
    def soffit(bm):
        a = ring(bm, (0, 0), Re - 0.05, ze - 0.06, n)
        b = ring(bm, (0, 0), R - 0.1, Hw - 0.02, n)
        for i in range(n):
            bm.faces.new((a[i], b[i], b[(i + 1) % n], a[(i + 1) % n]))

    m.add(under, soffit)
    if kind == "tiered":
        m.add(thatch, lambda bm: _cone(bm, [(Re, ze), (R * 0.95, Hw + 0.7), (R * 0.5, Hw + 1.55)], n, jag=0.12, seed=v))
        m.add(thatch, lambda bm: _cone(bm, [(R * 0.82, Hw + 1.0), (R * 0.45, Hw + 2.3)], n, tip=Hw + 3.4, jag=0.1,
                                       seed=v + 40))
        m.add(("rope_rail", "wall"), lambda bm: _cone(bm, [(R * 0.32, Hw + 2.75), (R * 0.27, Hw + 2.95)], n))
        top = Hw + 3.4
    elif kind == "finial":
        m.add(thatch, lambda bm: _cone(bm, [(Re, ze), (R * 0.9, Hw + 1.0), (R * 0.5, Hw + 2.4)], n, tip=Hw + 3.9, jag=0.1,
                                       seed=v))
        m.add(("rope_rail", "wall"), lambda bm: _cone(bm, [(R * 0.36, Hw + 2.85), (R * 0.31, Hw + 3.05)], n))
        top = Hw + 3.9
    elif kind == "dome":
        prof = [(Re, ze), (R + 0.55, Hw + 0.55), (R * 0.85, Hw + 1.35), (R * 0.55, Hw + 1.9), (R * 0.22, Hw + 2.15)]
        m.add(thatch, lambda bm: _cone(bm, prof, n, tip=Hw + 2.22, jag=0.08, seed=v))
        # The chimney: a stack of stones through the thatch.
        cx, cy = -R * 0.35, 0.4
        m.add(("ruin_stone", "wall"), lambda bm: _cyl(bm, (cx, cy, Hw + 1.0), 0.4, 1.95, n=8, r2=0.33))
        m.add(("charred_bark", "wall"), lambda bm: _cyl(bm, (cx, cy, Hw + 2.95), 0.26, 0.04, n=8))
        top = None
    else:  # "ragged": a tall reed cone, its fringe in two shaggy layers
        m.add(thatch, lambda bm: _cone(bm, [(Re + 0.15, ze - 0.1), (R * 0.9, Hw + 0.9), (R * 0.45, Hw + 2.4)], 24,
                                       tip=Hw + 3.6, jag=0.35, seed=v))
        m.add(thatch, lambda bm: _cone(bm, [(R * 0.8, Hw + 1.4), (R * 0.55, Hw + 2.1)], 24, jag=0.3, seed=v + 9))
        top = Hw + 3.6
    if top is not None:
        # The finial: a pole out of the peak, and on it horns (or a carved bird).
        m.add(BARK, lambda bm: tube(bm, [(0, 0, top - 0.6), (0, 0, top + 0.7)], 0.08, n=6))
        if v % 2 == 0:
            for sgn in (-1, 1):
                m.add(("bone", "wall"), lambda bm, sgn=sgn: tube(
                    bm, [(0, 0, top + 0.6), (0, sgn * 0.3, top + 0.8), (0, sgn * 0.45, top + 1.15), (0.05, sgn * 0.4, top + 1.4)],
                    [0.07, 0.06, 0.045, 0.02], n=5))
        else:
            m.add(("tribal_paint", "wall"), lambda bm: cuboid(bm, (0, 0, top + 0.85), (0.4, 0.3, 0.3)))
            m.add(("tribal_paint", "wall"), lambda bm: cuboid(bm, (0.28, 0, top + 0.82), (0.25, 0.1, 0.1)))
            for sgn in (-1, 1):
                m.add(("tribal_paint", "wall"), lambda bm, sgn=sgn: cuboid(bm, (0, sgn * 0.45, top + 0.95), (0.25, 0.6, 0.06),
                                                                         tilt=(sgn * 0.4, 0)))


def extra(m, kind, R, Hw, Re, ze, v):
    def at(a, r, z):
        return (r * math.cos(a), r * math.sin(a), z)

    if kind == "gourds":
        for k, a in enumerate((0.9, 1.3, -1.1)):
            x, y, _ = at(a, Re - 0.35, 0)
            drop = 0.5 + 0.2 * k
            m.add(("rope_rail", "wall"), lambda bm, x=x, y=y, drop=drop: tube(bm, [(x, y, ze - 0.05), (x, y, ze - drop)], 0.02, n=3))
            m.add(("daub_ochre", "wall"), lambda bm, x=x, y=y, drop=drop: blob(bm, (x, y, ze - drop - 0.2), 0.17, sz=1.35,
                                                                              subdiv=1))
    elif kind == "firewood":
        a = -0.75
        ca, sa = math.cos(a), math.sin(a)
        cx, cy = (R + 0.45) * ca, (R + 0.45) * sa
        tx, ty = -sa, ca
        for row in range(3):
            for k in range(4 - row):
                off = (k - (3 - row) / 2) * 0.32
                z = 0.15 + row * 0.27
                px, py = cx + tx * off, cy + ty * off
                log(m, (px - ca * 0.6, py - sa * 0.6, z), (px + ca * 0.6, py + sa * 0.6, z), 0.14, seed=v * 13 + row * 5 + k,
                    n=7)
    elif kind == "pots":
        for k, a in enumerate((-0.6, -0.42, 0.75)):
            x, y, _ = at(a, R + 0.42, 0)
            sc = 0.8 + 0.25 * k

            def pot(bm, x=x, y=y, sc=sc):
                prof = [(0.2, 0.0), (0.32, 0.18), (0.36, 0.38), (0.28, 0.6), (0.17, 0.72), (0.21, 0.8)]
                rings = [ring(bm, (x, y), r * sc, z * sc, 10) for r, z in prof]
                loft(bm, rings, cap_top=True, cap_bottom=False)

            m.add(("daub_rose", "wall") if k % 2 else ("tribal_paint", "wall"), pot)
    elif kind == "bench":
        a = 0.55
        ca, sa = math.cos(a), math.sin(a)
        cx, cy = (R + 0.55) * ca, (R + 0.55) * sa
        tx, ty = -sa, ca
        for sgn in (-1, 1):
            m.add(("ruin_stone", "wall"), lambda bm, sgn=sgn: cuboid(bm, (cx + tx * sgn * 0.6, cy + ty * sgn * 0.6, 0.18),
                                                                    (0.35, 0.4, 0.36), rot=a))
        log(m, (cx - tx * 0.95, cy - ty * 0.95, 0.5), (cx + tx * 0.95, cy + ty * 0.95, 0.5), 0.16, seed=v + 70, n=8)
    elif kind == "rack":
        a = -1.05
        ca, sa = math.cos(a), math.sin(a)
        cx, cy = (R + 1.3) * ca, (R + 1.3) * sa
        tx, ty = -sa, ca
        for sgn in (-1, 1):
            m.add(BARK, lambda bm, sgn=sgn: tube(bm, [(cx + tx * sgn * 0.9, cy + ty * sgn * 0.9, -0.1),
                                                       (cx + tx * sgn * 0.9, cy + ty * sgn * 0.9, 1.9)], 0.07, n=5))
        m.add(BARK, lambda bm: tube(bm, [(cx - tx * 1.05, cy - ty * 1.05, 1.85), (cx + tx * 1.05, cy + ty * 1.05, 1.85)], 0.06, n=5))
        q = [(cx - tx * 0.7, cy - ty * 0.7, 0.55), (cx + tx * 0.7, cy + ty * 0.7, 0.55), (cx + tx * 0.75, cy + ty * 0.75, 1.82),
             (cx - tx * 0.75, cy - ty * 0.75, 1.82)]
        m.quad(("painted_hide", "wall"), q, [(0, 0), (1, 0), (1, 1), (0, 1)])
        m.quad(("painted_hide", "wall"), list(reversed(q)), [(0, 1), (1, 1), (1, 0), (0, 0)])
    elif kind == "chime":
        x = R + 0.25
        for k in range(4):
            y = -0.45 + k * 0.3
            ln = 0.35 + 0.12 * (k % 2)
            m.add(("bone", "wall"), lambda bm, y=y, ln=ln: tube(bm, [(x, y, DOOR_H - 0.05), (x, y, DOOR_H - 0.05 - ln)], 0.035,
                                                                n=4))
    elif kind == "skull":
        z = DOOR_H + 0.55
        x = R + 0.08
        m.add(("bone", "wall"), lambda bm: blob(bm, (x, 0, z), 0.28, sx=0.9, sy=1.1, sz=0.85, subdiv=1))
        m.add(("bone", "wall"), lambda bm: blob(bm, (x + 0.2, 0, z - 0.12), 0.16, sx=1.4, sz=0.7, subdiv=1))
        for sgn in (-1, 1):
            m.add(("bone", "wall"), lambda bm, sgn=sgn: tube(bm, [(x, sgn * 0.22, z + 0.12), (x + 0.15, sgn * 0.55, z + 0.3),
                                                                  (x + 0.35, sgn * 0.62, z + 0.55)], [0.07, 0.05, 0.02], n=5))
            m.add(("dark_corridor", "wall"), lambda bm, sgn=sgn: blob(bm, (x + 0.24, sgn * 0.11, z + 0.03), 0.06, subdiv=0))


def hut_collider(c, v):
    """What a kart hits at a hut: its walls, a plain round (the porch's posts too)."""
    s = HUTS[_vi(v)]
    name = "Village Hut Collider %d" % _vi(v)

    def build(bm):
        _cyl(bm, (0, 0, -0.4), s["r"] + 0.15, s["h"] + 0.4, n=14)
        if s["door"] == "porch":
            for sgn in (-1, 1):
                cuboid(bm, (s["r"] + 1.7, sgn * 1.2, 1.1), (0.3, 0.3, 2.4))
        return [(c.lib(s["wall"], "wall"), list(range(len(bm.faces))))]

    return c.proto(name, build) and name


def place_hut(c, v, x, y, z, rot, scale=1.0, coll="Village", name=None):
    """A hut (look v, its doorway turned to `rot`), its collider, and its chimney's
    smoke if it has one."""
    c.place(hut(c, v), x, y, z, rot=rot, scale=scale, coll=coll, role="visual", name=name)
    c.place(hut_collider(c, v), x, y, z, rot=rot, scale=scale, coll="Collision", role="collision")
    ch = hut_chimney(v)
    if ch:
        ca, sa = math.cos(rot), math.sin(rot)
        px, py = x + (ch[0] * ca - ch[1] * sa) * scale, y + (ch[0] * sa + ch[1] * ca) * scale
        g = c.game(px, py, z + ch[2] * scale)
        c.entity("chimney", x=g[0], y=g[1], z=g[2])


def house(c, name, x, y, z, rot, k):
    """villager_homes' house: the front (local -Y) to `rot`'s; our doorways face +X. Set a
    little up from the lowest ground round it (its walls run on down into the land), so
    it doesn't sink into a slope (Blake, Riverbend note 11)."""
    v = GRAND if name == "Home Riverbend 2" else k
    place_hut(c, v, x, y, z + 0.25, rot - math.pi / 2, coll="Props", name=name)


# ------------------------------------------------------------------ the kart shed


def kart_shed(c):
    """Where the camp works on its karts (Blake, note 1; Oct 28: "lets add more detail to
    this garage"): an open-fronted timber shed of plank walls under a thatched gable on
    rafters, a plank floor, a kart up on blocks under a timber hoist with its chain and
    hook, a wheel off; a long workbench with a vice, an engine on it and tools; shelves of
    paint pots and jars; tyres stacked and hung on pegs; barrels, a toolbox, a jack, crates;
    a lantern hanging from the beam and a carved sign over the front. Its open side faces
    -Y."""
    name = "Village Kart Shed"

    def build(bm):
        W, D, H = 10.0, 6.5, 3.6
        k0 = len(bm.faces)
        for sx in (-1, 1):
            for sy in (-1, 1):
                cuboid(bm, (sx * W / 2, sy * D / 2, H / 2 - 0.3), (0.4, 0.4, H + 0.6))
        cuboid(bm, (0, -D / 2, H / 2 - 0.3), (0.3, 0.3, H + 0.6))  # (a middle post at the front)
        # Plank walls: the back, and the sides halfway, slats with gaps.
        for k in range(7):
            z = 0.2 + k * 0.48
            cuboid(bm, (0, D / 2, z), (W, 0.14, 0.42), tilt=(0.0, 0.01 * ((k % 3) - 1)))
            for sx in (-1, 1):
                cuboid(bm, (sx * W / 2, D / 4, z), (0.14, D / 2, 0.42))
        cuboid(bm, (0, -D / 2, H - 0.1), (W + 0.4, 0.34, 0.34))  # the front beam
        cuboid(bm, (0, D / 2, H - 0.1), (W + 0.4, 0.3, 0.3))
        for k in range(6):  # rafters under the thatch
            x = -W / 2 + k * W / 5
            for s in (-1, 1):
                tube(bm, [(x, s * (D / 2 + 0.6), H - 0.2), (x, 0.0, H + 2.0)], 0.12, n=4)
        cuboid(bm, (0, 0, H + 2.05), (W + 1.4, 0.24, 0.24))  # the ridge beam
        # The plank floor.
        for k in range(9):
            cuboid(bm, (-W / 2 + 0.55 + k * (W - 1.1) / 8, 0, -0.08), ((W - 1.1) / 8 - 0.06, D - 0.2, 0.12))
        # The workbench (with a vice), shelves, the hoist's frame.
        bx, by = W * 0.22, D / 2 - 0.75
        cuboid(bm, (bx, by, 0.95), (4.2, 1.0, 0.14))
        for sx in (-1, 1):
            cuboid(bm, (bx + sx * 1.9, by, 0.45), (0.16, 0.9, 0.9))
        cuboid(bm, (bx, by, 0.3), (3.8, 0.9, 0.08))  # the shelf under it
        for k in range(3):  # wall shelves
            cuboid(bm, (bx, D / 2 - 0.25, 1.75 + k * 0.55), (3.6, 0.36, 0.06))
        hx = -1.9
        for sy in (-1, 1):  # the hoist: an A-frame over the kart
            tube(bm, [(hx - 1.4, sy * 1.6, -0.05), (hx, sy * 0.2, H + 0.4)], 0.12, n=5)
            tube(bm, [(hx + 1.4, sy * 1.6, -0.05), (hx, sy * 0.2, H + 0.4)], 0.12, n=5)
        tube(bm, [(hx, -0.3, H + 0.4), (hx, 0.7, H + 0.4)], 0.14, n=5)
        k_sign = len(bm.faces)
        cuboid(bm, (0.0, -D / 2 - 0.25, H + 0.75), (3.4, 0.14, 0.8))  # the sign board
        for sx in (-1, 1):
            tube(bm, [(sx * 1.4, -D / 2 - 0.25, H + 0.1), (sx * 1.4, -D / 2 - 0.25, H + 0.4)], 0.04, n=4)
        for sx in (-1, 1):  # the blocks the kart stands on
            for sy in (-1, 1):
                cuboid(bm, (hx + sx * 0.55, sy * 0.75, 0.15), (0.4, 0.45, 0.3), rot=0.1 * sx * sy)
        wood = _faces(bm, k0)
        k1 = len(bm.faces)
        for s in (-1, 1):
            v = [bm.verts.new(q) for q in ((-W / 2 - 0.9, 0.0, H + 2.3), (W / 2 + 0.9, 0.0, H + 2.3),
                                           (W / 2 + 0.9, s * (D / 2 + 1.3), H - 0.4), (-W / 2 - 0.9, s * (D / 2 + 1.3), H - 0.4))]
            bm.faces.new(v if s < 0 else list(reversed(v)))
        for s in (-1, 1):  # gable ends
            v = [bm.verts.new(q) for q in ((s * W / 2, -D / 2, H - 0.2), (s * W / 2, D / 2, H - 0.2), (s * W / 2, 0.0, H + 2.2))]
            bm.faces.new(v)
        roof = _faces(bm, k1)
        k2 = len(bm.faces)
        # (The kart itself is the game's own, taken apart: a kart_wreck entity on the
        # blocks under the hoist. Blake, note 12.)
        kx = hx
        # Paint pots and jars on the shelves, a toolbox on the bench.
        for k in range(10):
            x = bx - 1.6 + (k % 5) * 0.75 + 0.1 * rnd(k)
            z = 1.78 + (k // 5) * 0.55
            _cyl(bm, (x, D / 2 - 0.25, z), 0.13 + 0.04 * rnd(k + 3), 0.3 + 0.1 * rnd(k + 5), n=6)
        cuboid(bm, (bx - 1.2, by, 1.17), (0.8, 0.4, 0.3))
        paint = _faces(bm, k2)
        k3 = len(bm.faces)
        for k in range(5):  # a stack of tyres, and the one off the kart
            _cyl(bm, (W / 2 - 1.1, -D / 2 + 1.3, -0.02 + 0.34 * k), 0.5, 0.32, n=10)
        for k in range(3):  # tyres hung on pegs on the side wall
            res = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.45, radius2=0.45, depth=0.3)
            for v in res["verts"]:
                v.co = Vector((-W / 2 + 0.3 + v.co.z, D / 2 - 1.2 - k * 1.05, 2.2 + v.co.y + 0.0 * v.co.x))
        # The hoist's chain and hook, the vice, the jack.
        for k in range(8):
            _cyl(bm, (hx + 0.04 * (k % 2), 0.2, H + 0.25 - k * 0.3), 0.06, 0.24, n=4)
        tube(bm, [(hx, 0.2, H - 2.1), (hx + 0.15, 0.2, H - 2.35), (hx, 0.2, H - 2.5)], 0.05, n=4)
        cuboid(bm, (bx + 1.7, by - 0.35, 1.15), (0.35, 0.3, 0.3))
        cuboid(bm, (kx + 1.3, 0.8, 0.12), (0.5, 0.9, 0.2))
        tube(bm, [(kx + 1.3, 0.4, 0.2), (kx + 1.3, -0.4, 0.75)], 0.04, n=4)
        rubber = _faces(bm, k3)
        k4 = len(bm.faces)
        # The engine on the bench: a block, its head, a flywheel.
        cuboid(bm, (bx + 0.5, by, 1.3), (0.8, 0.6, 0.55))
        cuboid(bm, (bx + 0.5, by, 1.66), (0.7, 0.5, 0.18))
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.3, radius2=0.3, depth=0.1)
        for v in res["verts"]:
            v.co = Vector((bx + 0.95 + v.co.z, by + v.co.x, 1.3 + v.co.y))
        for k in range(3):  # spanners on the back wall
            cuboid(bm, (bx - 0.9 + k * 0.45, D / 2 - 0.12, 2.9), (0.07, 0.05, 0.7 - 0.12 * k))
        metal = _faces(bm, k4)
        k5 = len(bm.faces)
        for k in range(3):  # barrels
            _cyl(bm, (-W / 2 + 0.9 + k * 1.0, D / 2 - 0.9, -0.02), 0.45, 1.1, n=8, r2=0.42)
        for k in range(2):  # crates
            cuboid(bm, (W / 2 - 1.0, D / 2 - 1.0 - k * 0.2, 0.4 + k * 0.8), (1.0, 1.0, 0.8), rot=0.2 * k)
        barrels = _faces(bm, k5)
        k6 = len(bm.faces)
        # The lantern under the beam.
        tube(bm, [(W * 0.1, -D / 2 + 0.2, H - 0.25), (W * 0.1, -D / 2 + 0.2, H - 0.75)], 0.03, n=4)
        blob(bm, (W * 0.1, -D / 2 + 0.2, H - 0.95), 0.22, sz=1.3, subdiv=1)
        light = _faces(bm, k6)
        _ = k_sign
        return [(c.lib("wood_planks"), wood), (c.lib("thatch"), roof), (c.lib("tribal_paint"), paint),
                (c.lib("black_rock"), rubber), (c.lib("obsidian_cliff"), metal), (c.lib("palm_bark"), barrels),
                (c.lib("lantern_glow"), light)]

    return c.proto(name, build) and name


def repair_sign(c):
    """The shed's sign, KART REPAIR (Blake, note 5), on the front of its board."""
    D, H = 6.5, 3.6

    def fill(m):
        y = -D / 2 - 0.33
        hw, z0, z1 = 1.62, H + 0.48, H + 1.02
        for k in range(3):
            a, b = -hw + k * 2 * hw / 3, -hw + (k + 1) * 2 * hw / 3
            m.quad(("sign_repair_%d" % (k + 1), "wall"), [(a, y, z0), (b, y, z0), (b, y, z1), (a, y, z1)],
                   [(0, 0), (1, 0), (1, 1), (0, 1)])

    return proto_mesh(c, "Kart Repair Sign", fill)


# ------------------------------------------------------------------ the totems


def totem(c, x, y, z, rot, variant):
    """A carved totem: the carving is built in the game (src/render/villageDecor.ts, as
    finely as the characters); here, its collider and its `village_totem` entity. Its
    carved faces look along local -Y turned by `rot`."""
    name = "Totem Collider"

    def build(bm):
        _cyl(bm, (0, 0, -0.3), 1.0, 9.0, n=10)
        return [(c.lib("palm_bark", "wall"), list(range(len(bm.faces))))]

    c.proto(name, build)
    c.place(name, x, y, z, rot=rot, coll="Collision", role="collision")
    face = rot - math.pi / 2
    g = c.game(x, y, z)
    c.entity("village_totem", x=g[0], y=g[1], z=g[2], variant=variant,
             heading=round(math.atan2(math.cos(face), -math.sin(face)), 3))


# ------------------------------------------------------------------ the paths


def _catmull(pts, step=0.7):
    """A smooth curve through the points, sampled every `step` metres or so."""
    if len(pts) < 2:
        return list(pts)
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = (Vector((p[0], p[1], 0)) for p in P[i - 1:i + 3])
        n = max(2, int((p2 - p1).length / step))
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            q = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
            out.append((q.x, q.y))
    out.append(tuple(pts[-1][:2]))
    return out


def wander(a, b, bend=0.0, seed=0):
    """A path's points from a to b, bowed `bend` metres to one side, with a little wander."""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    n = max(2, int(L / 6.0))
    pts = []
    for k in range(n + 1):
        t = k / n
        off = bend * math.sin(math.pi * t) + (0.6 * math.sin(t * 7.0 + seed) if 0 < k < n else 0.0)
        pts.append((ax + dx * t + nx * off, ay + dy * t + ny * off))
    return pts


def path_ribbons(c, paths, ground, look=None, width=2.4, verge=0.8, coll="Village", name="Village Paths"):
    """Dirt paths laid on the land as ribbons (Blake, notes 1, 3, 8: the painted ones
    "look horrible"): smooth curves through each path's points, a hand's breadth above the
    ground, their width wandering slowly, a soft verge either side where the grass grows
    into the dirt, and round ends. `look(x, y)` -> (dirt material, verge material or None)
    for where a path runs."""
    import region_textures as TX

    look = look or (lambda x, y: (("camp_earth", "dirt"), (TX.blend_id("valley_grass", "camp_earth", 50), "dirt")))
    m = gs.Mesh()

    def P(x, y, lift):
        return (x, y, ground(x, y) + lift)

    for pi, path in enumerate(paths):
        line = _catmull(path)
        if len(line) < 2:
            continue
        mid = line[len(line) // 2]
        dirt, edge = look(*mid)
        L = len(line)
        rows = []
        for k, (x, y) in enumerate(line):
            a = line[max(0, k - 1)]
            b = line[min(L - 1, k + 1)]
            tx, ty = b[0] - a[0], b[1] - a[1]
            tl = math.hypot(tx, ty) or 1.0
            nx, ny = -ty / tl, tx / tl
            wl = width / 2 * (1.0 + 0.12 * math.sin(k * 0.21 + pi) + 0.05 * math.sin(k * 0.67 + pi * 3))
            wr = width / 2 * (1.0 + 0.12 * math.sin(k * 0.19 + pi * 2) + 0.05 * math.sin(k * 0.71 + pi))
            vl = verge * (0.8 + 0.4 * (0.5 + 0.5 * math.sin(k * 0.5 + pi)))
            vr = verge * (0.8 + 0.4 * (0.5 + 0.5 * math.sin(k * 0.43 + pi * 5)))
            rows.append([P(x - nx * (wl + vl), y - ny * (wl + vl), 0.04), P(x - nx * wl, y - ny * wl, 0.07), P(x, y, 0.08),
                         P(x + nx * wr, y + ny * wr, 0.07), P(x + nx * (wr + vr), y + ny * (wr + vr), 0.04)])

        def strip(bm, js, rows=rows):
            vs = [[bm.verts.new(p) for p in row] for row in rows]
            for r0, r1 in zip(vs, vs[1:]):
                for j in js:
                    bm.faces.new((r0[j], r1[j], r1[j + 1], r0[j + 1]))

        m.add(dirt, lambda bm: strip(bm, (1, 2)))
        if edge:
            m.add(edge, lambda bm: strip(bm, (0, 3)))
        # Round ends: a half disc of dirt, and its verge round it.
        for end, (x, y), (px, py) in ((0, line[0], line[1]), (1, line[-1], line[-2])):
            ux, uy = x - px, y - py
            ul = math.hypot(ux, uy) or 1.0
            ux, uy = ux / ul, uy / ul
            nx, ny = -uy, ux
            row = rows[0] if end == 0 else rows[-1]
            wi = math.hypot(row[1][0] - x, row[1][1] - y)
            wo = math.hypot(row[0][0] - x, row[0][1] - y)
            K = 6
            inner, outer = [], []
            for i in range(K + 1):
                th = -math.pi / 2 + math.pi * i / K
                dx, dy = ux * math.cos(th) + nx * math.sin(th), uy * math.cos(th) + ny * math.sin(th)
                inner.append(P(x + dx * wi, y + dy * wi, 0.07))
                outer.append(P(x + dx * wo, y + dy * wo, 0.04))

            def cap(bm, inner=inner, x=x, y=y):
                cv = bm.verts.new(P(x, y, 0.08))
                iv = [bm.verts.new(p) for p in inner]
                for i in range(K):
                    bm.faces.new((cv, iv[i + 1], iv[i]) if end == 0 else (cv, iv[i], iv[i + 1]))

            def rim(bm, inner=inner, outer=outer):
                iv = [bm.verts.new(p) for p in inner]
                ov = [bm.verts.new(p) for p in outer]
                for i in range(K):
                    q = (iv[i], ov[i], ov[i + 1], iv[i + 1])
                    bm.faces.new(q if end == 1 else tuple(reversed(q)))

            m.add(dirt, cap)
            if edge:
                m.add(edge, rim)
    return m.build(c, name, coll=coll, role="visual")


def plaza(c, x, y, r, ground, dirt=("camp_earth", "dirt"), edge=None, verge=1.2, name="Plaza"):
    """A round of trodden earth (round a hearth, where the paths meet), with its verge."""
    import region_textures as TX

    edge = edge or (TX.blend_id("valley_grass", "camp_earth", 50), "dirt")
    m = gs.Mesh()
    n = 28

    def P(r_, a, lift):
        rr = r_ * (1.0 + 0.06 * math.sin(a * 3 + x) + 0.04 * math.sin(a * 7 + y))
        px, py = x + rr * math.cos(a), y + rr * math.sin(a)
        return (px, py, ground(px, py) + lift)

    def disc(bm):
        cv = bm.verts.new((x, y, ground(x, y) + 0.09))
        mid = [bm.verts.new(P(r * 0.55, i * math.tau / n, 0.085)) for i in range(n)]
        rim = [bm.verts.new(P(r, i * math.tau / n, 0.075)) for i in range(n)]
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((cv, mid[i], mid[j]))
            bm.faces.new((mid[i], rim[i], rim[j], mid[j]))

    def ring_(bm):
        a = [bm.verts.new(P(r, i * math.tau / n, 0.075)) for i in range(n)]
        b = [bm.verts.new(P(r + verge, i * math.tau / n, 0.045)) for i in range(n)]
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], b[i], b[j], a[j]))

    m.add(dirt, disc)
    m.add(edge, ring_)
    return m.build(c, name, coll="Village", role="visual")


def home_path(c, x, y, _r=0.0):
    """A home's path, from before its door to the nearest road on the land (not one in a
    tunnel or on a bridge), running a little way in under the road's edge (Blake,
    Riverbend notes 2 and 9: "the path fully going into the road")."""
    best, bd = None, 1e9
    for q in [s for s in c.S if getattr(s, "ground", True)] + list(getattr(c, "extra_ground", [])):
        d = math.hypot(q.p.x - x, q.p.y - y)
        if d < bd:
            best, bd = q, d
    q, d = best, bd
    ux, uy = (q.p.x - x) / (d or 1.0), (q.p.y - y) / (d or 1.0)
    # (From its door, which villager_homes turned to the race line's nearest point.)
    f, fd = c.nearest(x, y)
    fx, fy = (f.p.x - x) / (fd or 1.0), (f.p.y - y) / (fd or 1.0)
    start = (x + fx * 4.4, y + fy * 4.4)
    end = (q.p.x - ux * max(1.0, q.w / 2 - 1.2), q.p.y - uy * max(1.0, q.w / 2 - 1.2))
    return wander(start, end, bend=1.5 * math.sin(x * 0.37 + y * 0.11), seed=int(abs(x) * 3) % 17)


def road_apron(c, start, end, mat, ground, width=15.0, past=6.0, name="Gateway Apron"):
    """The road carried right up into a gateway's mouth (Blake, Riverbend notes 6 and 7:
    a green patch on the road before the gate, the land before it to be "the same
    texture as the road"): a strip of the road's own surface over the last stretch and
    on past the road's end into the arch, its texture running along it like the road's."""
    import course_kit as ck

    e = ck.materials.entry(mat[0])
    tile = e["tileMetres"]
    sx, sy = start
    ex, ey = end
    L = math.hypot(ex - sx, ey - sy) or 1.0
    ux, uy = (ex - sx) / L, (ey - sy) / L
    nx, ny = -uy, ux
    total = L + past
    m = gs.Mesh()
    steps = max(2, int(total / 1.0))
    cols = (-1.0, -0.5, 0.0, 0.5, 1.0)
    rows = []
    for k in range(steps + 1):
        s = total * k / steps
        # (Round ends: narrower toward its far end, into the mouth.)
        w = width / 2 * (1.0 if s < total - 3.0 else max(0.55, 1.0 - (s - (total - 3.0)) / 6.0))
        row = []
        for f in cols:
            x, y = sx + ux * s + nx * f * w, sy + uy * s + ny * f * w
            row.append(((x, y, ground(x, y) + 0.16), (s / tile, (f * w + width / 2) / tile)))
        rows.append(row)
    for r0, r1 in zip(rows, rows[1:]):
        for j in range(len(cols) - 1):
            q = [r0[j], r1[j], r1[j + 1], r0[j + 1]]
            m.quad(mat, [p for p, _ in q], [uv for _, uv in q])
    return m.build(c, name, coll="Props", role="visual")


def clear_paths(c, paths, room=2.6):
    """Nothing growing in a path (Blake, Riverbend note 9: "move this bush out of the
    path"): bushes, ferns, leafy plants, flowers and small rocks within `room` of a
    path's line are taken away."""
    from mathutils import kdtree

    pts = [p for path in paths for p in _catmull(path, step=1.0)]
    if not pts:
        return
    tree = kdtree.KDTree(len(pts))
    for i, (x, y) in enumerate(pts):
        tree.insert((x, y, 0.0), i)
    tree.balance()
    small = ("Bush", "Fern", "Big Leaf", "Flower", "Grass", "Tuft", "Pebble", "Boulder", "Reeds", "Shrub")
    gone = 0
    for ob in list(bpy.data.objects):
        if ob.type != "MESH" or not ob.name.startswith(small):
            continue
        p = ob.matrix_world.translation
        _, _, d = tree.find((p.x, p.y, 0.0))
        if d < room:
            bpy.data.objects.remove(ob)
            gone += 1
    print("paths cleared of %d plants" % gone)


# ------------------------------------------------------------------ the swamp hut


def swamp_hut(c):
    """A swamp-dweller's hut (Blake, Bonebog notes 9 and 10: "think yodas house on dagoa
    ... make the hut nice"): a low lumpy dome of mud and wattle grown over with moss,
    old roots arching over it and down into the bog, a round doorway with a bent-wood
    frame, two round windows glowing, a crooked clay chimney, a lantern on a crook by the
    door, stepping stones up to it, pots and a stool. Its door faces +X."""

    def fill(m):
        mud = ("swamp_mud", "wall")
        moss = ("bog_moss_ground", "grass")
        root = ("bog_root", "wall")
        R = 3.6

        def dome(bm):
            res = bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
            for i, v in enumerate(res["verts"]):
                p = v.co.copy()
                lump = 1.0 + 0.08 * math.sin(p.x * 7 + p.y * 3) * math.cos(p.z * 5 + p.x * 2) + 0.05 * (rnd(i) - 0.5)
                v.co = Vector((p.x * R * 1.15 * lump, p.y * R * lump, max(-0.6, p.z * 3.1 * lump + 0.2)))

        k0 = len(m.bm.faces)
        m.add(mud, dome)
        # (Moss on what faces up: those faces to the moss.)
        m.bm.faces.ensure_lookup_table()
        m.bm.normal_update()
        mud_faces = m.slots[mud]
        moved = [i for i in mud_faces[-(len(m.bm.faces) - k0):] if m.bm.faces[i].normal.z > 0.72]
        m.slots[mud] = [i for i in mud_faces if i not in set(moved)]
        m.slots.setdefault(moss, []).extend(moved)
        # Roots arching over it and down into the bog.
        for k in range(7):
            a = k * math.tau / 7 + 0.4
            if abs(math.atan2(math.sin(a), math.cos(a))) < 0.5:
                continue  # (clear of the door)
            ca, sa = math.cos(a), math.sin(a)
            r0 = 0.6 + 0.4 * rnd(k + 3)
            m.add(root, lambda bm, ca=ca, sa=sa, r0=r0: tube(bm, [
                (ca * r0, sa * r0, 3.4), (ca * R * 0.7, sa * R * 0.6, 3.0), (ca * R * 1.25, sa * R * 1.1, 1.6),
                (ca * R * 1.55, sa * R * 1.4, 0.2), (ca * R * 1.75, sa * R * 1.6, -0.6)], [0.45, 0.4, 0.33, 0.25, 0.18], n=7))
        # The stump of the old tree it grew under, out of the top.
        m.add(root, lambda bm: tube(bm, [(0.3, -0.2, 2.6), (0.2, -0.1, 4.2), (0.6, 0.1, 5.2)], [1.0, 0.75, 0.45], n=9))
        # The doorway: dark, round, under a bent-wood frame, stones up to it.
        dx = R * 1.15 - 0.15
        m.add(("dark_corridor", "wall"), lambda bm: _round(bm, (dx, 0, 1.05), 0.85, 1.0, 14))
        m.add(BARK, lambda bm: tube(bm, [(dx + 0.08, 0.85 * math.cos(t), 1.05 + 1.0 * math.sin(t))
                                         for t in [i * math.pi / 10 for i in range(-1, 12)]], 0.11, n=6))
        for k in range(3):
            m.add(("ruin_stone", "wall"), lambda bm, k=k: blob(bm, (dx + 0.9 + k * 0.8, 0.15 * (k % 2), 0.0), 0.45, sx=1.2,
                                                                sz=0.4, subdiv=1))
        # Round windows, glowing, framed.
        for a in (0.95, -1.2):
            wx, wy = math.cos(a) * R * 1.12, math.sin(a) * R * 0.97
            m.add(("lantern_glow", "wall"), lambda bm, a=a, wx=wx, wy=wy: _round_at(bm, (wx, wy, 1.7), a, 0.38, 10))
            m.add(BARK, lambda bm, a=a, wx=wx, wy=wy: tube(bm, [
                (wx + math.cos(a) * 0.05 - math.sin(a) * 0.4 * math.cos(t), wy + math.sin(a) * 0.05 + math.cos(a) * 0.4 * math.cos(t),
                 1.7 + 0.4 * math.sin(t)) for t in [i * math.tau / 10 for i in range(11)]], 0.06, n=4))
        # The chimney: a crooked clay pipe out of the roof.
        m.add(("daub_rose", "wall"), lambda bm: tube(bm, [(-1.4, 0.9, 2.4), (-1.6, 1.0, 3.6), (-1.4, 1.2, 4.3)], [0.32, 0.28, 0.3],
                                                       n=8))
        # A lantern on a crook by the door.
        m.add(BARK, lambda bm: tube(bm, [(dx + 0.6, -1.4, -0.3), (dx + 0.7, -1.4, 2.4), (dx + 1.2, -1.2, 2.7)], 0.07, n=5))
        m.add(("lantern_glow", "wall"), lambda bm: blob(bm, (dx + 1.25, -1.2, 2.2), 0.2, sz=1.3, subdiv=1))
        # Pots and a stool.
        for k, (px, py) in enumerate(((dx + 0.3, 1.6), (dx - 0.2, 2.1))):
            m.add(("daub_ochre", "wall"), lambda bm, px=px, py=py, k=k: loft(bm, [
                ring(bm, (px, py), r * (0.9 + 0.2 * k), z, 10) for r, z in ((0.22, 0.0), (0.34, 0.25), (0.3, 0.55), (0.2, 0.7))],
                cap_top=True))
        log(m, (dx + 1.6, 1.0, 0.25), (dx + 1.6, 1.0, 0.65), 0.28, seed=91, n=9)

    return proto_mesh(c, "Swamp Hut", fill)


def _round(bm, centre, rw, rh, n):
    """An upright oval facing +X (a doorway)."""
    cx, cy, cz = centre
    vs = [bm.verts.new((cx, cy + rw * math.cos(i * math.tau / n), max(0.0, cz + rh * math.sin(i * math.tau / n))))
          for i in range(n)]
    bm.faces.new(vs)


def _round_at(bm, centre, a, r, n):
    """An upright disc facing out along angle a (a round window)."""
    cx, cy, cz = centre
    tx, ty = -math.sin(a), math.cos(a)
    vs = [bm.verts.new((cx + math.cos(a) * 0.04 + tx * r * math.cos(i * math.tau / n),
                        cy + math.sin(a) * 0.04 + ty * r * math.cos(i * math.tau / n), cz + r * math.sin(i * math.tau / n)))
          for i in range(n)]
    bm.faces.new(vs)


def place_swamp_hut(c, x, y, z, rot):
    """The swamp hut, its collider, its chimney smoking, and its folk's home before it.
    Trees standing where it goes are taken away (Blake: "move the tree")."""
    for ob in list(bpy.data.objects):
        near = math.hypot(ob.matrix_world.translation.x - x, ob.matrix_world.translation.y - y) < 8.0
        if ob.type == "MESH" and ("Tree" in ob.name or "Giant" in ob.name) and near:
            bpy.data.objects.remove(ob)
    c.place(swamp_hut(c), x, y, z, rot=rot, coll="Props", role="visual", name="Swamp Hut")

    def build(bm):
        _cyl(bm, (0, 0, -0.6), 3.9, 3.6, n=14)
        return [(c.lib("swamp_mud", "wall"), list(range(len(bm.faces))))]

    c.proto("Swamp Hut Collider", build)
    c.place("Swamp Hut Collider", x, y, z, rot=rot, coll="Collision", role="collision")
    ca, sa = math.cos(rot), math.sin(rot)
    g = c.game(x + (-1.4 * ca - 1.2 * sa), y + (-1.4 * sa + 1.2 * ca), z + 4.4)
    c.entity("chimney", x=g[0], y=g[1], z=g[2])
    hx, hy = x + ca * 7.0, y + sa * 7.0
    g = c.game(hx, hy, z)
    c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=9.0, n=1, folk="valley",
             heading=round(math.atan2(-math.cos(rot), math.sin(rot)), 3))


def fossil_skulls(c, sink=0.9):
    """The bog's fossil skulls carved finely in the game (Blake, Bonebog note 8: "lets
    increase the fidelity of this bone model"): each Fossil Skull the dressing scattered
    becomes a horned_skull entity where it lay (render/villageDecor.ts), half sunk, with a
    plain collider."""

    def build(bm):
        _cyl(bm, (0, 0, -0.5), 1.0, 2.2, n=10)
        return [(c.lib("bog_bone", "wall"), list(range(len(bm.faces))))]

    c.proto("Skull Collider", build)
    n = 0
    for ob in list(bpy.data.objects):
        if ob.type != "MESH" or not ob.name.startswith("Fossil Skull"):
            continue
        p = ob.matrix_world.translation.copy()
        rot = ob.rotation_euler.z
        sc = ob.scale.x
        bpy.data.objects.remove(ob)
        g = c.game(p.x, p.y, p.z - sink * sc)
        c.entity("horned_skull", x=g[0], y=g[1], z=g[2], scale=round(0.85 * sc, 3),
                 heading=round(math.atan2(math.cos(rot), -math.sin(rot)), 3))
        c.place("Skull Collider", p.x, p.y, p.z - 0.3, rot=rot, scale=(2.2 * sc, 1.6 * sc, 1.0), coll="Collision",
                role="collision")
        n += 1
    print("fossil skulls: %d" % n)
