# The Christmas-village kit for Hearthglow Hollow: alpine cottages with glowing windows,
# smoking chimneys and lights along the eaves, market stalls, lantern posts, decorated
# pines, the giant Christmas tree, presents, snowmen, candy canes, wooden Christmas
# arches, the bell tower, a frozen fountain, logs, and strings of coloured lights.
# SPDX-License-Identifier: MIT
#
# Same rules as props.py: each prop is one mesh built once (Course.proto) and placed as
# copies, chunky and low-poly, all original designs. One-off pieces built in place (the
# strings of lights) collect into a single mesh.

import math

from course_kit import Vector, bmesh, rnd
from props import _faces, blob, cuboid, loft, ring, tube

SNOW = "summit_snow"
BEAM = "timber_beam"
GLOW = "window_warm"
LAMP = "lantern_glow"

# Where each cottage's chimney puffs from (local, at its top), for the smoke entities.
CHIMNEY = {}


def _p(c, name, build):
    return c.proto(name, build) and name


class Parts:
    """Faces grouped by material while a prop is built."""

    def __init__(self, bm):
        self.bm = bm
        self.groups = {}

    def add(self, mat, make):
        k0 = len(self.bm.faces)
        make(self.bm)
        self.groups.setdefault(mat, []).extend(_faces(self.bm, k0))

    def box(self, mat, centre, size, rot=0.0, tilt=(0.0, 0.0)):
        self.add(mat, lambda bm: cuboid(bm, centre, size, rot, tilt))

    def quad(self, mat, pts):
        def make(bm):
            bm.faces.new([bm.verts.new(p) for p in pts])

        self.add(mat, make)

    def slots(self, c):
        return [(c.lib(m) if isinstance(m, str) else c.lib(*m), f) for m, f in self.groups.items() if f]


def _icicle_row(bm, x0, x1, y, z, n, length, seed=0):
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        ln = length * (0.4 + 0.6 * rnd(i * 3 + seed))
        res = bmesh.ops.create_cone(bm, cap_ends=False, segments=4, radius1=0.0, radius2=0.1, depth=ln)
        for v in res["verts"]:
            v.co += Vector((x, y, z - ln / 2))


def _gable(k, w, d, h, rh, wall, over=1.0, snow=0.8):
    """A steep gabled roof thick with snow over a w x d box of height h (ridge along X),
    with its gable ends filled in `wall`, and icicles under both eaves."""
    D = d / 2 + over
    th = math.atan2(rh, D)
    ln = math.hypot(D, rh)
    for sd in (-1, 1):
        k.box(SNOW, (0, sd * D / 2, h + rh / 2 + snow * 0.4), (w + 2 * over, ln + 0.4, snow), tilt=(-sd * th, 0.0))
    for sx in (-1, 1):
        x = sx * w / 2
        pts = [(x, -d / 2, h), (x, d / 2, h), (x, 0.0, h + rh)]
        k.quad(wall, pts if sx > 0 else list(reversed(pts)))
    k.add("icefall_blue", lambda bm: [_icicle_row(bm, -w / 2 - over, w / 2 + over, sd * (D + 0.1), h - 0.1, 5, 1.2, int(w) + sd) for sd in (-1, 1)])


# ------------------------------------------------------------------ cottages and shops


def cottage(c, variant=0):
    """An alpine cottage (origin at the ground, its front toward -Y): walls of plaster
    and dark beams or of logs, a steep roof deep in snow, a brick chimney, glowing
    windows, a door with a wreath, and a string of lights along the front eave."""
    name = "Cottage %d" % variant
    w, d, h, rh, walls, storeys = (
        (11.0, 8.0, 6.5, 5.5, "cabin_plaster", 2),
        (9.0, 8.0, 4.6, 4.5, "cabin_wall", 1),
        (8.0, 8.0, 9.5, 6.0, "cabin_plaster", 3),
        (14.0, 9.0, 6.0, 5.5, "cabin_wall", 2),
        (10.0, 9.0, 7.0, 6.5, "cabin_plaster", 2),
    )[variant % 5]

    def build(bm):
        k = Parts(bm)
        k.box("hearth_stone", (0, 0, 0.6), (w + 0.4, d + 0.4, 1.6))
        k.box(walls, (0, 0, (h + 1.0) / 2 + 0.2), (w, d, h - 1.0))
        _gable(k, w, d, h, rh, walls)
        # The chimney.
        cx, cy = w * 0.25, d * 0.18
        top = h + rh * 0.7 + 2.0
        k.box("brick", (cx, cy, (h + top) / 2), (1.4, 1.4, top - h))
        k.box(SNOW, (cx, cy, top + 0.15), (1.7, 1.7, 0.35))
        CHIMNEY[variant % 5] = (cx, cy, top + 0.4)
        # Windows: front, back and sides, storey by storey.
        for st in range(storeys):
            z = 2.2 + st * 2.6
            if z > h - 1.0:
                break
            for x in [(-w / 2 + 1.8) + j * 3.0 for j in range(max(1, int((w - 2.5) / 3.0)))]:
                if st == 0 and abs(x) < 1.4:
                    continue  # the door
                for sd in (-1, 1):
                    y0 = sd * (d / 2 + 0.04)
                    pts = [(x - 0.75, y0, z - 0.4), (x + 0.75, y0, z - 0.4), (x + 0.75, y0, z + 1.2), (x - 0.75, y0, z + 1.2)]
                    k.quad(GLOW, pts if sd < 0 else list(reversed(pts)))
            for sx in (-1, 1):
                x0 = sx * (w / 2 + 0.04)
                pts = [(x0, -0.75, z - 0.4), (x0, 0.75, z - 0.4), (x0, 0.75, z + 1.2), (x0, -0.75, z + 1.2)]
                k.quad(GLOW, pts if sx > 0 else list(reversed(pts)))
        # The door, with a wreath and a lamp.
        k.box(BEAM, (0, -d / 2 - 0.05, 1.9), (1.8, 0.15, 2.8))
        k.add("wreath", lambda bm: _ring_wreath(bm, (0, -d / 2 - 0.25, 3.7), 0.55))
        k.box(LAMP, (1.4, -d / 2 - 0.3, 3.0), (0.3, 0.3, 0.45))
        # Lights along the front eave.
        D = d / 2 + 1.0
        k.quad("xmas_lights", [(-w / 2 - 1.0, -D - 0.05, h - 0.55), (w / 2 + 1.0, -D - 0.05, h - 0.55), (w / 2 + 1.0, -D - 0.05, h - 0.15), (-w / 2 - 1.0, -D - 0.05, h - 0.15)])
        return k.slots(c)

    return _p(c, name, build)


def cottage_block(c, variant=0):
    """The cottage's collision: just its walls as one box (the roof, windows and lights
    are only for looking at)."""
    name = "Cottage Block %d" % variant
    w, d, h = ((11.0, 8.0, 6.5), (9.0, 8.0, 4.6), (8.0, 8.0, 9.5), (14.0, 9.0, 6.0), (10.0, 9.0, 7.0))[variant % 5]

    def build(bm):
        cuboid(bm, (0, 0, h / 2), (w + 0.4, d + 0.4, h + 2))
        return [(c.lib("cabin_wall", "wall"), _faces(bm, 0))]

    return _p(c, name, build)


def _ring_wreath(bm, centre, r):
    """A chunky wreath standing upright, facing -Y: a flat ring of eight segments, thick
    enough to see from the side."""
    cx, cy, cz = centre
    n = 8
    outer = [Vector((cx + r * 1.25 * math.cos(i * math.tau / n), cy, cz + r * 1.25 * math.sin(i * math.tau / n))) for i in range(n)]
    inner = [Vector((cx + r * 0.6 * math.cos(i * math.tau / n), cy, cz + r * 0.6 * math.sin(i * math.tau / n))) for i in range(n)]
    for dy in (-0.12, 0.12):
        o = [bm.verts.new(v + Vector((0, dy, 0))) for v in outer]
        q = [bm.verts.new(v + Vector((0, dy, 0))) for v in inner]
        for i in range(n):
            f = (o[i], o[(i + 1) % n], q[(i + 1) % n], q[i])
            bm.faces.new(f if dy > 0 else tuple(reversed(f)))


def stall(c, variant=0):
    """A Christmas market stall: a wooden booth, a striped awning, a counter of
    presents and goodies, a lantern (origin at the ground, the front toward -Y)."""
    name = "Stall %d" % variant
    aw = ("awning_red", "awning_green")[variant % 2]

    def build(bm):
        k = Parts(bm)
        for x in (-2.4, 2.4):
            for y in (-1.6, 1.6):
                k.box(BEAM, (x, y, 1.6), (0.3, 0.3, 3.2))
        k.box("cabin_wall", (0, 1.7, 1.6), (5.0, 0.2, 3.2))
        k.box(BEAM, (0, -1.0, 0.6), (4.8, 1.0, 1.2))
        k.quad(aw, [(-2.9, -2.6, 2.7), (2.9, -2.6, 2.7), (2.9, 1.9, 3.8), (-2.9, 1.9, 3.8)])
        k.box(SNOW, (0, -0.35, 3.45), (6.0, 4.7, 0.25), tilt=(-0.24, 0.0))
        for i, wr in enumerate(("wrap_red", "wrap_green", "wrap_gold", "wrap_blue")):
            s = 0.45 + 0.15 * ((i + variant) % 3)
            k.box(wr, (-1.6 + i * 1.05, -1.0, 1.2 + s / 2), (s, s, s), rot=0.3 * i)
        k.box(LAMP, (2.2, -1.8, 2.4), (0.3, 0.3, 0.45))
        k.quad("xmas_lights", [(-2.9, -2.62, 2.35), (2.9, -2.62, 2.35), (2.9, -2.62, 2.7), (-2.9, -2.62, 2.7)])
        return k.slots(c)

    return _p(c, name, build)


def lantern_post(c, variant=0):
    """A street lantern on a dark post, with a red bow and holly (lamp at about 4.6 m)."""
    name = "Lantern Post %d" % variant

    def build(bm):
        k = Parts(bm)
        k.add("ship_hull", lambda bm: tube(bm, [(0, 0, -0.3), (0, 0, 4.2)], [0.16, 0.12], n=6))
        k.box("ship_hull", (0, 0, 4.25), (0.7, 0.7, 0.12))
        k.box(LAMP, (0, 0, 4.65), (0.55, 0.55, 0.75))
        k.add("ship_hull", lambda bm: _roof4(bm, 0, 0, 5.02, 0.48, 0.5))
        k.box("wreath", (0, -0.12, 2.8), (0.5, 0.12, 0.5))
        k.box("awning_red", (0, -0.2, 3.1), (0.5, 0.06, 0.3))
        return k.slots(c)

    return _p(c, name, build)


def _roof4(bm, x, y, z, r, h):
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=r * 1.41, radius2=0.0, depth=h)
    for v in res["verts"]:
        v.co = Vector((x + v.co.x * 0.707 - v.co.y * 0.707, y + v.co.x * 0.707 + v.co.y * 0.707, z + h / 2 + v.co.z))


# ------------------------------------------------------------------ trees


def _light_spiral(bm, height, base_r, top_r, z0, turns, width=0.35, seg=48, phase=0.0, at=(0.0, 0.0)):
    """A ribbon of lights spiralling up a cone (centred on `at`)."""
    rows = []
    for i in range(seg + 1):
        t = i / seg
        a = phase + t * turns * math.tau
        z = z0 + t * height
        r = (base_r + (top_r - base_r) * t) + 0.35
        p = Vector((at[0] + r * math.cos(a), at[1] + r * math.sin(a), z))
        rows.append((bm.verts.new(p - Vector((0, 0, width / 2))), bm.verts.new(p + Vector((0, 0, width / 2)))))
    for (a0, a1), (b0, b1) in zip(rows, rows[1:]):
        bm.faces.new((a0, b0, b1, a1))


def xmas_pine(c, variant=0, height=14.0, lights=True):
    """A pine heavy with snow, optionally wound with coloured lights and a gold star."""
    name = "Xmas Pine %d %d %s" % (variant, int(height), "lit" if lights else "plain")

    def build(bm):
        k = Parts(bm)
        k.add("giant_bark", lambda bm: tube(bm, [(0, 0, -0.5), (0, 0, height * 0.3)], [0.45, 0.3], n=6))

        def boughs(bm):
            for i in range(4):
                t = i / 4
                r = height * 0.3 * (1 - t * 0.75)
                res = bmesh.ops.create_cone(bm, cap_ends=True, segments=7, radius1=r, radius2=r * 0.12, depth=height * 0.34)
                for v in res["verts"]:
                    v.co += Vector((0, 0, height * (0.17 + 0.2 * i) + height * 0.17))
                    v.co.x += 0.15 * math.sin(v.co.z * 1.3 + variant)

        k.add("pine_night", boughs)
        if lights:
            k.add("xmas_lights", lambda bm: _light_spiral(bm, height * 0.72, height * 0.27, height * 0.05, height * 0.18, 3.0, 0.4, 40, variant))
            k.add("star_gold", lambda bm: _star(bm, (0, 0, height * 1.0 + 0.4), height * 0.06))
        return k.slots(c)

    return _p(c, name, build)


def pine_lo(c, variant=0, height=14.0):
    """A cheap distant pine: two snowy cones on a stub of trunk (for the far woods)."""
    name = "Pine Lo %d %d" % (variant, int(height))

    def build(bm):
        k = Parts(bm)
        k.add("giant_bark", lambda bm: tube(bm, [(0, 0, -0.5), (0, 0, height * 0.25)], [0.4, 0.3], n=4))

        def boughs(bm):
            for i in range(2):
                r = height * 0.32 * (1 - i * 0.45)
                res = bmesh.ops.create_cone(bm, cap_ends=False, segments=6, radius1=r, radius2=0.0, depth=height * (0.6 - 0.15 * i))
                for v in res["verts"]:
                    v.co += Vector((0, 0, height * (0.18 + 0.36 * i) + height * (0.3 - 0.075 * i)))
                    v.co.x += 0.15 * math.sin(v.co.z + variant)

        k.add("pine_night", boughs)
        return k.slots(c)

    return _p(c, name, build)


def _star(bm, centre, r):
    """A chunky five-pointed star, upright, facing ±Y (a thick slab)."""
    cx, cy, cz = centre
    for sd in (-1, 1):
        vs = []
        for i in range(10):
            a = math.pi / 2 + i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.45
            vs.append(bm.verts.new((cx + rr * math.cos(a), cy + sd * r * 0.18, cz + rr * math.sin(a))))
        centre_v = bm.verts.new((cx, cy + sd * r * 0.35, cz))
        for i in range(10):
            f = (vs[i], vs[(i + 1) % 10], centre_v)
            bm.faces.new(f if sd < 0 else tuple(reversed(f)))


def giant_tree(c, name, x, y, z, height=44.0):
    """The giant Christmas tree in the square: a trunk, eight tiers of snowy boughs,
    three garlands of coloured lights spiralling up it, a great golden star on top, and a
    low fence round its foot. Built in place (it's one of a kind)."""
    bm = bmesh.new()
    k = Parts(bm)
    k.add("giant_bark", lambda bm: tube(bm, [(x, y, z - 1), (x, y, z + height * 0.25)], [2.2, 1.8], n=10))

    def boughs(bm):
        for i in range(8):
            t = i / 8
            r = height * 0.3 * (1 - t * 0.82)
            res = bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=r, radius2=r * 0.25, depth=height * 0.17)
            for v in res["verts"]:
                v.co += Vector((x, y, z + height * (0.12 + 0.105 * i) + height * 0.085))
                v.co.x += 0.35 * math.sin(v.co.z * 0.9 + i)

    k.add("pine_night", boughs)

    def garlands(bm):
        for g in range(3):
            _light_spiral(bm, height * 0.82, height * 0.28, height * 0.03, z + height * 0.12, 3.5, 0.7, 120, g * 2.1, (x, y))

    k.add("xmas_lights", garlands)
    k.add("star_gold", lambda bm: _star(bm, (x, y, z + height + 2.2), 3.4))
    # A low fence round its foot, with posts.
    k.add(BEAM, lambda bm: [cuboid(bm, (x + 12 * math.cos(a), y + 12 * math.sin(a), z + 0.6), (0.4, 0.4, 1.4)) for a in [i * math.tau / 16 for i in range(16)]])
    k.add("timber_rail", lambda bm: [cuboid(bm, (x + 12 * math.cos(a), y + 12 * math.sin(a), z + 0.95), (4.7, 0.2, 0.25), rot=a + math.pi / 2) for a in [(i + 0.5) * math.tau / 16 for i in range(16)]])
    ob = c.mesh_object(name, bm, "Village", "both")
    for mat, faces in k.groups.items():
        if faces:
            c.assign(ob, c.lib(mat), faces)
    ob.data.shade_flat()
    return ob


# ------------------------------------------------------------------ festive bits


def present_pile(c, variant=0):
    """A heap of wrapped presents (static decoration)."""
    name = "Present Pile %d" % variant

    def build(bm):
        k = Parts(bm)
        wraps = ("wrap_red", "wrap_green", "wrap_gold", "wrap_blue")
        for i in range(4 + variant % 3):
            s = 0.8 + 0.7 * rnd(i * 3 + variant)
            a = i * 2.1 + variant
            r = 0.0 if i == 0 else 1.2 + 0.4 * rnd(i)
            k.box(wraps[(i + variant) % 4], (r * math.cos(a), r * math.sin(a), s / 2), (s, s * (0.8 + 0.3 * rnd(i * 7)), s), rot=a)
        k.box(wraps[(variant + 1) % 4], (0.1, -0.1, 1.5 + 0.35), (0.7, 0.7, 0.7), rot=0.5)
        return k.slots(c)

    return _p(c, name, build)


def snowman(c, variant=0):
    name = "Snowman %d" % variant

    def build(bm):
        k = Parts(bm)
        k.add(SNOW, lambda bm: [blob(bm, (0, 0, zz), r, subdiv=1) for zz, r in ((0.9, 1.1), (2.4, 0.8), (3.5, 0.55))])
        k.add("ship_hull", lambda bm: [blob(bm, (sx * 0.2, -0.47, 3.62), 0.08, subdiv=0) for sx in (-1, 1)] + [blob(bm, (0, -0.79, zz), 0.09, subdiv=0) for zz in (2.2, 2.6)])
        k.add("carrot", lambda bm: _carrot(bm))
        k.box(("awning_red", "awning_green", "wrap_blue")[variant % 3], (0, 0, 2.95), (1.2, 1.2, 0.28))
        if variant % 2 == 0:
            k.add("ship_hull", lambda bm: loft(bm, [ring(bm, (0, 0), 0.62, 3.95, 8), ring(bm, (0, 0), 0.62, 4.05, 8)], cap_top=True) or loft(bm, [ring(bm, (0, 0), 0.4, 4.05, 8), ring(bm, (0, 0), 0.4, 4.75, 8)], cap_top=True))
        return k.slots(c)

    return _p(c, name, build)


def _carrot(bm):
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=5, radius1=0.11, radius2=0.0, depth=0.6)
    for v in res["verts"]:
        v.co = Vector((v.co.x, -0.55 - (v.co.z + 0.3), 3.5 + v.co.y))


def candy_cane(c, height=5.0):
    name = "Candy Cane %d" % int(height)

    def build(bm):
        pts = [(0, 0, -0.3), (0, 0, height * 0.75)]
        for i in range(1, 7):
            a = math.pi * i / 6
            pts.append((0.7 - 0.7 * math.cos(a), 0, height * 0.75 + 0.7 * math.sin(a)))
        pts.append((1.4, 0, height * 0.75 - 0.4))
        tube(bm, pts, 0.22, n=6)
        return [(c.lib("candy_stripe"), _faces(bm, 0))]

    return _p(c, name, build)


def xmas_arch(c, span=24.0, height=10.0, checker=False, variant=0):
    """A wooden Christmas archway over the road (origin at the road's middle; the arch
    spans X): two great posts, a snowy roof, a wreath with a bow, lanterns, banners, a
    string of lights, and (on the start arch) a checkered banner."""
    name = "Xmas Arch %d %d %d %d" % (int(span), int(height), checker, variant)

    def build(bm):
        k = Parts(bm)
        for sx in (-1, 1):
            x = sx * (span / 2 + 0.9)
            k.box("hearth_stone", (x, 0, 1.2), (2.6, 2.6, 2.4))
            k.box(BEAM, (x, 0, 2.4 + (height - 2.4) / 2), (1.5, 1.5, height - 2.4))
            k.box(SNOW, (x, 0, 2.55), (2.8, 2.8, 0.3))
            k.box(LAMP, (x - sx * 1.1, -0.9, height - 1.2), (0.5, 0.5, 0.7))
        k.box(BEAM, (0, 0, height + 0.5), (span + 4.2, 1.8, 1.2))
        k.box(SNOW, (0, 0, height + 1.35), (span + 5.0, 2.6, 0.6))
        # A little gabled roof on the beam.
        k.box("cabin_wall", (0, 0, height + 2.3), (span * 0.35, 1.0, 1.4))
        k.box(SNOW, (0, 0, height + 3.2), (span * 0.4, 2.2, 0.5))
        k.box("awning_red", (0, -1.3, height - 0.2), (1.2, 0.2, 0.8))
        for sd in (-1, 1):
            pts = [(-span / 2 - 2, sd * 0.95, height - 0.2), (span / 2 + 2, sd * 0.95, height - 0.2), (span / 2 + 2, sd * 0.95, height + 0.15), (-span / 2 - 2, sd * 0.95, height + 0.15)]
            k.quad("xmas_lights", pts if sd < 0 else list(reversed(pts)))
            k.add("wreath", lambda bm, sd=sd: _ring_wreath(bm, (0, sd * 1.1, height + 0.9), 1.4))
            for sx in (-1, 1):
                k.box("banner_tree", (sx * (span / 2 + 0.9), sd * 0.8, height - 3.4), (1.3, 0.08, 3.6))
        if checker:
            k.add("start_checker", lambda bm: _hang(bm, span * 0.75, height - 0.15, height - 2.0))
        return k.slots(c)

    return _p(c, name, build)


def _hang(bm, w, top, bottom):
    for sd in (-1, 1):
        vs = [bm.verts.new(p) for p in ((-w / 2, sd * 0.05, bottom), (w / 2, sd * 0.05, bottom), (w / 2, sd * 0.05, top), (-w / 2, sd * 0.05, top))]
        bm.faces.new(vs if sd < 0 else list(reversed(vs)))


def bell_tower(c):
    """The bell tower: a stone shaft, an open wooden belfry (the bell itself is a moving
    entity), a red spire with a gold finial, snow and lights (bell at about 19 m)."""
    name = "Bell Tower"

    def build(bm):
        k = Parts(bm)
        k.box("hearth_stone", (0, 0, 7.5), (7.0, 7.0, 16.0))
        k.box(SNOW, (0, 0, 15.65), (7.6, 7.6, 0.4))
        for sx in (-1, 1):
            for sy in (-1, 1):
                k.box(BEAM, (sx * 2.9, sy * 2.9, 18.6), (0.9, 0.9, 5.6))
        k.box(BEAM, (0, 0, 21.5), (7.4, 7.4, 0.8))
        k.add("wrap_red", lambda bm: _roof4(bm, 0, 0, 21.9, 4.6, 8.0))
        k.box("gold_trim", (0, 0, 30.3), (0.4, 0.4, 1.4))
        k.add("star_gold", lambda bm: _star(bm, (0, 0, 31.6), 0.9))
        for sd in (-1, 1):
            k.box(GLOW, (0, sd * 3.53, 9.0), (1.4, 0.08, 2.4))
            k.box(GLOW, (sd * 3.53, 0, 12.5), (0.08, 1.4, 2.0))
        k.box(BEAM, (0, -3.6, 1.6), (2.0, 0.2, 3.2))
        k.quad("xmas_lights", [(-3.8, -3.75, 15.2), (3.8, -3.75, 15.2), (3.8, -3.75, 15.55), (-3.8, -3.75, 15.55)])
        return k.slots(c)

    return _p(c, name, build)


def log(c, variant=0):
    name = "Snowy Log %d" % variant

    def build(bm):
        k = Parts(bm)
        ln = 5.0 + 2.0 * variant
        k.add("giant_bark", lambda bm: tube(bm, [(-ln / 2, 0, 0.5), (ln / 2, 0, 0.6)], 0.55, n=7))
        k.box(SNOW, (0, 0, 1.08), (ln * 0.85, 0.8, 0.25))
        return k.slots(c)

    return _p(c, name, build)


class Lights:
    """Strings of coloured lights slung between points (across streets, along bridges),
    all in one mesh: thin sagging ribbons of bulbs, their UVs running along so the
    lights chase."""

    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new("UVMap")

    def line(self, p0, p1, sag=1.2, width=0.35, tile=3.0):
        a, b = Vector(p0), Vector(p1)
        n = max(4, int((b - a).length / 1.5))
        along = 0.0
        prev = None
        rows = []
        for i in range(n + 1):
            t = i / n
            p = a.lerp(b, t)
            p.z -= sag * 4 * t * (1 - t)
            if prev is not None:
                along += (p - prev).length
            rows.append((p, along))
            prev = p
        for sd in (-1, 1):
            vs = [(self.bm.verts.new(p + Vector((0, 0, -width / 2))), self.bm.verts.new(p + Vector((0, 0, width / 2))), u) for p, u in rows]
            for (a0, a1, u0), (b0, b1, u1) in zip(vs, vs[1:]):
                quad = (a0, b0, b1, a1) if sd > 0 else (a1, b1, b0, a0)
                uvs = ((u0, 0.25), (u1, 0.25), (u1, 0.75), (u0, 0.75)) if sd > 0 else ((u0, 0.75), (u1, 0.75), (u1, 0.25), (u0, 0.25))
                f = self.bm.faces.new(quad)
                for loop, (u, v) in zip(f.loops, uvs):
                    loop[self.uv].uv = (u / tile, v)

    def build(self, c, name="Lights"):
        if not self.bm.faces:
            self.bm.free()
            return None
        from kartipelago_tools import materials

        ob = c.mesh_object(name, self.bm, "Lights", "visual")
        ob.data.materials.append(c.lib("xmas_lights"))
        materials.ensure_paint(ob.data)
        return ob
