# Dragonspire Keep's kit: round and square towers with slate spires and battlements,
# curtain walls, the gatehouse's towers and arch, town houses (stone below, timber above,
# steep roofs), dragon banners on poles and walls, torches and braziers, barrels, crates,
# hanging cages and stone spikes, mountain pines, the fountain, stone dragon statues and
# the great red dragon. Each builds one mesh (a prototype) that every copy shares; origins
# are at the ground, fronts face +Y. All our own designs, chunky and low-poly.
# SPDX-License-Identifier: MIT

import math

from canyon_props import _beam, _cyl
from course_kit import Vector
from props import _faces, blob, cuboid, loft, ring, tube

ASHLAR = "keep_ashlar"
DARK = "keep_ashlar_dark"
SLATE = "keep_slate"
ROOF = "keep_roof"
TIMBER = "keep_timber"
DOOR = "keep_door"
WINDOW = "keep_window"
PARAPET = "keep_parapet"
GOLD = "keep_gold"
IRON = "keep_iron"
FLAME = "keep_flame"
BANNER = "keep_banner"
PINE = "keep_pine"


# A palette swap for another course (Emberdeep Hold builds the same castle kit in its own
# stone): material id -> the id to use instead. Set before building any prototype.
REMAP = {}


def use_palette(remap):
    REMAP.clear()
    REMAP.update(remap)


class Parts:
    """Faces of one prototype, gathered by material."""

    def __init__(self, c, bm):
        self.c = c
        self.bm = bm
        self.slots = {}

    def add(self, mat, make):
        k = len(self.bm.faces)
        make()
        self.slots.setdefault(mat, []).extend(_faces(self.bm, k))

    def out(self):
        return [(self.c.lib(REMAP.get(m, m)), f) for m, f in self.slots.items()]


def fit_whole(c, name, faces):
    """Stretch each of these faces' UVs over the whole picture (0..1 both ways): a banner
    shows its dragon once, whatever its size."""
    me = c.protos[name]
    uv = me.uv_layers.active
    if uv is None:
        return
    for i in faces:
        p = me.polygons[i]
        vs = [me.vertices[me.loops[li].vertex_index].co for li in p.loop_indices]
        # The panel's own axes: across from its first edge, down from its normal.
        a = (vs[1] - vs[0]).normalized()
        n = p.normal
        b = n.cross(a).normalized()
        us = [v.dot(a) for v in vs]
        ws = [v.dot(b) for v in vs]
        u0, u1, w0, w1 = min(us), max(us), min(ws), max(ws)
        for li, u, w in zip(p.loop_indices, us, ws):
            uv.data[li].uv = ((u - u0) / max(1e-6, u1 - u0), (w - w0) / max(1e-6, w1 - w0))


def _p(c, name, build, fit=None):
    """Build a prototype once; `fit` lists materials whose faces show their picture whole
    (banners)."""
    if name in c.protos:
        return name
    got = {}

    def b(bm):
        P = Parts(c, bm)
        build(P, bm)
        got.update(P.slots)
        return P.out()

    c.proto(name, b)
    for m in fit or ():
        fit_whole(c, name, got.get(m, []))
    return name


def _cone(bm, x, y, z0, h, r, n=10, phase=0.0):
    _cyl(bm, x, y, z0, z0 + h, r, 0.04, n=n, phase=phase)


def _merlons(bm, r, z, n, size=(1.0, 0.8, 1.1), x=0.0, y=0.0):
    """Battlements round a circle: n merlons on the rim."""
    for i in range(n):
        a = i * math.tau / n
        cuboid(bm, (x + r * math.cos(a), y + r * math.sin(a), z + size[2] / 2), size, rot=a + math.pi / 2)


def _quad(bm, pts, both=True, gap=0.04, normal=(0, 1, 0)):
    """A flat panel (banners, flames); `both`: a second one just behind, facing back."""
    a = [bm.verts.new(p) for p in pts]
    bm.faces.new(a)
    if both:
        n = Vector(normal) * gap
        b = [bm.verts.new(Vector(p) - n) for p in pts]
        bm.faces.new(list(reversed(b)))


def _flame(P, bm, x, y, z, s=1.0):
    """A torch flame: two crossed panels."""
    for a in (0.0, math.pi / 2):
        ca, sa = math.cos(a), math.sin(a)
        pts = [(x - 0.35 * s * ca, y - 0.35 * s * sa, z), (x + 0.35 * s * ca, y + 0.35 * s * sa, z),
               (x + 0.1 * s * ca, y + 0.1 * s * sa, z + 1.1 * s), (x - 0.1 * s * ca, y - 0.1 * s * sa, z + 1.1 * s)]
        P.add(FLAME, lambda pts=pts, a=a: _quad(bm, pts, normal=(-math.sin(a), math.cos(a), 0)))


# ------------------------------------------------------------------ towers and walls


def round_tower(c, r=4.0, h=18.0, roof=True, variant=0, mat=ASHLAR):
    """A round tower: battlements round the top, a tall slate spire with a gold finial
    (or an open fighting top), lit arrow-slit windows."""
    name = "Round Tower %.1f %.1f %d %d %s" % (r, h, roof, variant, mat)
    n = 10

    def build(P, bm):
        P.add(mat, lambda: _cyl(bm, 0, 0, -2.0, h, r, r * 0.94, n=n))
        P.add(mat, lambda: _cyl(bm, 0, 0, h - 0.8, h + 0.6, r + 0.5, r + 0.5, n=n))  # the corbelled top
        P.add(PARAPET, lambda: _merlons(bm, r + 0.2, h + 0.6, 8 + 2 * (variant % 2), (1.1, 0.7, 1.2)))
        if roof:
            rh = r * (3.2 + 0.5 * (variant % 3))
            P.add(SLATE, lambda: _cone(bm, 0, 0, h + 0.5, rh, r + 0.3, n=n))
            P.add(GOLD, lambda: blob(bm, (0, 0, h + 0.6 + rh), 0.35))
        # Windows: tall slits, two rows, staggered.
        for k in range(4):
            a = k * math.tau / 4 + 0.4 * (variant % 2)
            for zz in (h * 0.45, h * 0.75):
                aa = a + (0.6 if zz > h * 0.6 else 0.0)
                P.add(WINDOW, lambda aa=aa, zz=zz: cuboid(bm, ((r - 0.05) * math.cos(aa), (r - 0.05) * math.sin(aa), zz), (0.25, 1.0, 2.0), rot=aa))

    return _p(c, name, build)


def square_tower(c, w=7.0, h=20.0, roof=True, variant=0, mat=ASHLAR):
    """A square tower: a corbelled top with battlements, a slate pyramid spire with
    turrets at the corners (or an open top), rows of lit windows."""
    name = "Square Tower %.1f %.1f %d %d %s" % (w, h, roof, variant, mat)

    def build(P, bm):
        P.add(mat, lambda: cuboid(bm, (0, 0, h / 2 - 1.0), (w, w, h + 2.0)))
        P.add(mat, lambda: cuboid(bm, (0, 0, h + 0.1), (w + 1.0, w + 1.0, 1.4)))
        for k in range(5):
            t = -w / 2 + (k + 0.5) * w / 5
            for x, y, rot in ((t, w / 2 + 0.5, 0), (t, -w / 2 - 0.5, 0), (w / 2 + 0.5, t, math.pi / 2), (-w / 2 - 0.5, t, math.pi / 2)):
                if k % 2 == 0:
                    P.add(PARAPET, lambda x=x, y=y, rot=rot: cuboid(bm, (x, y, h + 1.4), (1.1, 0.5, 1.2), rot=rot))
        if roof:
            rh = w * (1.5 + 0.3 * (variant % 2))
            P.add(SLATE, lambda: _cyl(bm, 0, 0, h + 0.8, h + 0.8 + rh, w * 0.62, 0.05, n=4, phase=math.pi / 4))
            P.add(GOLD, lambda: blob(bm, (0, 0, h + 1.0 + rh), 0.4))
            for sx in (-1, 1):
                for sy in (-1, 1):
                    P.add(mat, lambda sx=sx, sy=sy: _cyl(bm, sx * w / 2, sy * w / 2, h - 2.0, h + 2.0, 1.1, 1.1, n=6))
                    P.add(SLATE, lambda sx=sx, sy=sy: _cone(bm, sx * w / 2, sy * w / 2, h + 2.0, 3.4, 1.3, n=6))
        rows = max(2, int(h / 6))
        for j in range(rows):
            zz = 4.0 + j * (h - 6.0) / max(1, rows - 1)
            for side in range(4):
                rot = side * math.pi / 2
                for k in (-1, 1) if w > 6 else (0,):
                    off = k * w / 4
                    dx, dy = -math.sin(rot), math.cos(rot)
                    px, py = dx * (w / 2 + 0.02) + math.cos(rot) * off, dy * (w / 2 + 0.02) + math.sin(rot) * off
                    if (j + side + variant) % 3 != 0:
                        P.add(WINDOW, lambda px=px, py=py, zz=zz, rot=rot: cuboid(bm, (px, py, zz), (1.0, 0.2, 2.0), rot=rot))

    return _p(c, name, build)


def curtain_wall(c, length=16.0, h=9.0, thick=3.0, mat=ASHLAR):
    """A stretch of curtain wall along +X, battlements on its outer (+Y) edge, a parapet
    walk behind them."""
    name = "Curtain Wall %.1f %.1f %s" % (length, h, mat)

    def build(P, bm):
        P.add(mat, lambda: cuboid(bm, (0, 0, h / 2 - 1.5), (length, thick, h + 3.0)))
        n = int(length / 2.0)
        for k in range(n):
            x = -length / 2 + (k + 0.5) * length / n
            if k % 2 == 0:
                P.add(PARAPET, lambda x=x: cuboid(bm, (x, thick / 2 - 0.3, h + 0.6), (1.0, 0.6, 1.2)))
            P.add(PARAPET, lambda x=x: cuboid(bm, (x, -thick / 2 + 0.25, h + 0.35), (length / n, 0.5, 0.7)))

    return _p(c, name, build)


def gate_arch(c, span=26.0, clear=11.0, depth=7.0, banners=True):
    """The span of the castle gate over the road: a battlemented bridge between the gate
    towers, a pointed arch under it (its lowest edge `clear` metres up at the middle),
    banners hanging on its face. Along X, the road passes along Y. Visual only."""
    name = "Gate Arch %.1f %.1f" % (span, clear)
    top = clear + 6.0

    def build(P, bm):
        half = span / 2
        rings = []
        steps = 12
        for j in range(steps + 1):
            x = -half + span * j / steps
            u = abs(x) / half
            z = clear - 3.0 + 3.0 * math.sqrt(max(0.0, 1 - u ** 1.6))
            rings.append([bm.verts.new((x, y, zz)) for y, zz in ((-depth / 2, z), (depth / 2, z), (depth / 2, top), (-depth / 2, top))])

        def body():
            for a, b in zip(rings, rings[1:]):
                for i in range(4):
                    bm.faces.new((a[i], b[i], b[(i + 1) % 4], a[(i + 1) % 4]))

        P.add(ASHLAR, body)
        n = int(span / 2.2)
        for k in range(n):
            x = -half + (k + 0.5) * span / n
            if k % 2 == 0:
                for y in (-depth / 2 - 0.2, depth / 2 + 0.2):
                    P.add(PARAPET, lambda x=x, y=y: cuboid(bm, (x, y, top + 0.6), (1.1, 0.6, 1.2)))
        P.add(GOLD, lambda: cuboid(bm, (0, -depth / 2 - 0.25, clear + 2.2), (4.5, 0.3, 3.0)))
        if banners:
            for x in (-half * 0.55, half * 0.55):
                for y, nrm in ((-depth / 2 - 0.15, -1), (depth / 2 + 0.15, 1)):
                    pts = [(x - 1.4, y, top - 0.3), (x + 1.4, y, top - 0.3), (x + 1.4, y, top - 6.5), (x - 1.4, y, top - 6.5)]
                    if nrm > 0:
                        pts = [pts[1], pts[0], pts[3], pts[2]]
                    P.add(BANNER, lambda pts=pts, nrm=nrm: _quad(bm, pts, both=False))

    return _p(c, name, build, fit=[BANNER])


def keep_block(c, w=22.0, d=16.0, h=24.0):
    """The great keep: a tall hall block with corner turrets, buttresses, rows of lit
    windows, a steep slate roof and a gold dragon vane."""
    name = "Great Keep %.0f %.0f %.0f" % (w, d, h)

    def build(P, bm):
        P.add(DARK, lambda: cuboid(bm, (0, 0, h / 2 - 3.0), (w, d, h + 6.0)))
        P.add(ASHLAR, lambda: cuboid(bm, (0, 0, h + 0.2), (w + 1.0, d + 1.0, 1.4)))
        # The roof: a steep ridge along X.
        rh = d * 0.75

        def roof():
            hw, hd = w / 2, d / 2 + 0.6
            v = [bm.verts.new(p) for p in ((-hw, -hd, h + 0.8), (hw, -hd, h + 0.8), (hw, hd, h + 0.8), (-hw, hd, h + 0.8),
                                           (-hw + 1.0, 0, h + 0.8 + rh), (hw - 1.0, 0, h + 0.8 + rh))]
            bm.faces.new((v[0], v[1], v[5], v[4]))
            bm.faces.new((v[2], v[3], v[4], v[5]))
            bm.faces.new((v[1], v[2], v[5]))
            bm.faces.new((v[3], v[0], v[4]))

        P.add(SLATE, roof)
        for sx in (-1, 1):
            for sy in (-1, 1):
                x, y = sx * w / 2, sy * d / 2
                P.add(ASHLAR, lambda x=x, y=y: _cyl(bm, x, y, -3.0, h + 5.0, 2.2, 2.0, n=8))
                P.add(SLATE, lambda x=x, y=y: _cone(bm, x, y, h + 5.0, 8.0, 2.6, n=8))
                P.add(GOLD, lambda x=x, y=y: blob(bm, (x, y, h + 13.2), 0.3))
        for j in range(3):
            zz = 6.0 + j * (h - 9.0) / 2
            for k in range(5):
                x = -w / 2 + (k + 0.5) * w / 5
                P.add(WINDOW, lambda x=x, zz=zz: cuboid(bm, (x, -d / 2 - 0.05, zz), (1.4, 0.3, 3.2)))
                P.add(WINDOW, lambda x=x, zz=zz: cuboid(bm, (x, d / 2 + 0.05, zz), (1.4, 0.3, 3.2)))
            for k in range(3):
                y = -d / 2 + (k + 0.5) * d / 3
                for x in (-w / 2 - 0.05, w / 2 + 0.05):
                    P.add(WINDOW, lambda x=x, y=y, zz=zz: cuboid(bm, (x, y, zz), (0.3, 1.4, 3.2)))
        for k in range(4):
            x = -w / 2 + (k + 0.5) * w / 4
            pts = [(x - 1.6, -d / 2 - 0.3, h - 1.0), (x + 1.6, -d / 2 - 0.3, h - 1.0), (x + 1.6, -d / 2 - 0.3, h - 9.0), (x - 1.6, -d / 2 - 0.3, h - 9.0)]
            P.add(BANNER, lambda pts=pts: _quad(bm, pts, both=False))

    return _p(c, name, build, fit=[BANNER])


# ------------------------------------------------------------------ the town


def house(c, variant=0):
    """A town house: a stone ground floor with an oak door, a jettied timber upper
    storey, a steep tiled (or slate) roof and a chimney."""
    name = "Keep House %d" % variant
    w = (6.5, 8.0, 5.5, 7.0)[variant % 4]
    d = (6.0, 6.5, 5.5, 7.5)[variant % 4]
    h1, h2 = 3.2, 3.0 + (variant % 2)
    roof_mat = SLATE if variant % 3 == 2 else ROOF

    def build(P, bm):
        P.add(ASHLAR, lambda: cuboid(bm, (0, 0, h1 / 2 - 1.0), (w, d, h1 + 2.0)))
        P.add(TIMBER, lambda: cuboid(bm, (0, 0, h1 + h2 / 2), (w + 0.6, d + 0.6, h2)))
        z0 = h1 + h2
        rh = d * 0.75

        def roof():
            hw, hd = w / 2 + 0.6, d / 2 + 0.7
            v = [bm.verts.new(p) for p in ((-hw, -hd, z0), (hw, -hd, z0), (hw, hd, z0), (-hw, hd, z0), (-hw, 0, z0 + rh), (hw, 0, z0 + rh))]
            bm.faces.new((v[0], v[1], v[5], v[4]))
            bm.faces.new((v[2], v[3], v[4], v[5]))
            bm.faces.new((v[1], v[2], v[5]))
            bm.faces.new((v[3], v[0], v[4]))

        P.add(roof_mat, roof)
        # Gable ends in timber.
        def gables():
            for sx in (-1, 1):
                x = sx * (w / 2 + 0.3)
                v = [bm.verts.new(p) for p in ((x, -d / 2 - 0.3, z0), (x, d / 2 + 0.3, z0), (x, 0, z0 + rh - 0.3))]
                bm.faces.new(v if sx > 0 else list(reversed(v)))

        P.add(TIMBER, gables)
        cx = w / 2 - 1.2 if variant % 2 else -w / 2 + 1.2
        P.add(ASHLAR, lambda: cuboid(bm, (cx, 0.8, z0 + rh * 0.6), (1.0, 1.0, rh * 1.0 + 1.5)))
        P.add(DOOR, lambda: cuboid(bm, (-w / 4 if variant % 2 else w / 4, d / 2 + 0.05, 1.2), (1.4, 0.2, 2.4)))
        for x in (-w / 4, w / 4):
            P.add(WINDOW, lambda x=x: cuboid(bm, (x, d / 2 + 0.35, h1 + h2 / 2), (1.0, 0.2, 1.4)))
        P.add(WINDOW, lambda: cuboid(bm, (w / 4 if variant % 2 else -w / 4, d / 2 + 0.05, 1.8), (1.0, 0.2, 1.2)))

    return _p(c, name, build)


# ------------------------------------------------------------------ banners and fire


def banner_pole(c, mat=BANNER, h=9.0):
    """An iron pole with a crossbar and a long dragon banner, a gold spike on top."""
    name = "Keep Banner Pole %s %.0f" % (mat, h)

    def build(P, bm):
        P.add(IRON, lambda: _cyl(bm, 0, 0, -0.5, h, 0.12, 0.09, n=6))
        P.add(IRON, lambda: _beam(bm, (-0.2, 0, h - 0.6), (2.2, 0, h - 0.6), 0.1))
        P.add(GOLD, lambda: _cone(bm, 0, 0, h, 0.6, 0.18, n=5))
        P.add(mat, lambda: _quad(bm, [(0.1, 0.05, h - 0.7), (2.1, 0.05, h - 0.7), (2.1, 0.05, h - 5.7), (0.1, 0.05, h - 5.7)], gap=0.1))

    return _p(c, name, build, fit=[mat])


def wall_banner(c, mat=BANNER, w=2.6, h=6.0):
    """A banner hung on a wall from an iron rod (origin: the rod's middle; it hangs down,
    facing +Y)."""
    name = "Wall Banner %s %.1f %.1f" % (mat, w, h)

    def build(P, bm):
        P.add(IRON, lambda: _beam(bm, (-w / 2 - 0.3, 0.15, 0), (w / 2 + 0.3, 0.15, 0), 0.12))
        P.add(mat, lambda: _quad(bm, [(-w / 2, 0.2, -0.1), (w / 2, 0.2, -0.1), (w / 2, 0.2, -h), (-w / 2, 0.2, -h)], both=False))

    return _p(c, name, build, fit=[mat])


def flag_pole(c, mat="keep_flag_blue", h=7.0):
    """A flag on a pole (on the ramparts)."""
    name = "Flag Pole %s" % mat

    def build(P, bm):
        P.add(IRON, lambda: _cyl(bm, 0, 0, 0, h, 0.1, 0.08, n=5))
        P.add(GOLD, lambda: blob(bm, (0, 0, h + 0.1), 0.2))
        P.add(mat, lambda: _quad(bm, [(0.1, 0, h - 0.2), (3.4, 0, h - 0.5), (3.4, 0, h - 2.4), (0.1, 0, h - 2.2)]))

    return _p(c, name, build, fit=[mat])


def torch_post(c, h=2.6):
    """A stone post with an iron bowl of fire on top (the flame's foot `h`+0.1 up)."""
    name = "Torch Post %.1f" % h

    def build(P, bm):
        P.add(ASHLAR, lambda: cuboid(bm, (0, 0, (h - 0.4) / 2 - 0.3), (0.7, 0.7, h - 0.4 + 0.6)))
        P.add(ASHLAR, lambda: cuboid(bm, (0, 0, h - 0.45), (0.95, 0.95, 0.2)))
        P.add(IRON, lambda: _cyl(bm, 0, 0, h - 0.35, h + 0.15, 0.25, 0.5, n=6))
        _flame(P, bm, 0, 0, h + 0.05, 1.0)

    return _p(c, name, build)


def wall_torch(c):
    """A torch in an iron bracket on a wall (origin on the wall, facing +Y; the flame's
    foot is 0.4 m up and 0.6 m out)."""
    name = "Wall Torch"

    def build(P, bm):
        P.add(IRON, lambda: _beam(bm, (0, 0, -0.4), (0, 0.6, 0.3), 0.12))
        P.add(IRON, lambda: _cyl(bm, 0, 0.6, 0.2, 0.45, 0.14, 0.24, n=5))
        _flame(P, bm, 0, 0.6, 0.4, 0.7)

    return _p(c, name, build)


def brazier(c):
    """A great brazier: a stepped stone pedestal and a wide iron bowl of fire (the fire's
    foot 2.6 m up)."""
    name = "Brazier"

    def build(P, bm):
        P.add(ASHLAR, lambda: cuboid(bm, (0, 0, 0.0), (2.2, 2.2, 1.4)))
        P.add(ASHLAR, lambda: cuboid(bm, (0, 0, 1.1), (1.2, 1.2, 1.4)))
        P.add(ASHLAR, lambda: cuboid(bm, (0, 0, 1.9), (1.7, 1.7, 0.3)))
        P.add(IRON, lambda: _cyl(bm, 0, 0, 2.0, 2.7, 0.6, 1.1, n=8))
        _flame(P, bm, 0, 0, 2.5, 1.8)

    return _p(c, name, build)


# ------------------------------------------------------------------ odds and ends


def barrel(c):
    name = "Keep Barrel"

    def build(P, bm):
        P.add("keep_barrel", lambda: loft(bm, [ring(bm, (0, 0), r, z, 8) for r, z in ((0.45, 0.0), (0.56, 0.6), (0.45, 1.2))], cap_top=True, cap_bottom=True))

    return _p(c, name, build)


def crate(c, s=1.1):
    name = "Keep Crate %.1f" % s

    def build(P, bm):
        P.add("keep_crate", lambda: cuboid(bm, (0, 0, s / 2), (s, s, s)))

    return _p(c, name, build)


def cage(c):
    """An iron cage hanging from a gibbet arm (origin at the post's foot)."""
    name = "Hanging Cage"

    def build(P, bm):
        P.add("keep_barrel", lambda: _beam(bm, (0, 0, -0.3), (0, 0, 5.6), 0.35))
        P.add("keep_barrel", lambda: _beam(bm, (0, -0.1, 5.4), (0, 2.4, 5.4), 0.28))
        P.add(IRON, lambda: _beam(bm, (0, 2.1, 5.3), (0, 2.1, 4.4), 0.05))
        for k in range(8):
            a = k * math.tau / 8
            x, y = 0.55 * math.cos(a), 2.1 + 0.55 * math.sin(a)
            P.add(IRON, lambda x=x, y=y: _beam(bm, (x, y, 4.4), (x, y, 2.4), 0.06))
        P.add(IRON, lambda: _cyl(bm, 0, 2.1, 2.3, 2.45, 0.62, 0.62, n=8))
        P.add(IRON, lambda: _cone(bm, 0, 2.1, 4.35, 0.5, 0.62, n=8))

    return _p(c, name, build)


def spike(c, h=4.5):
    """A stone obelisk: a square shaft on a plinth, a pointed cap."""
    name = "Stone Spike %.1f" % h

    def build(P, bm):
        P.add(ASHLAR, lambda: cuboid(bm, (0, 0, 0.2), (1.6, 1.6, 0.8)))
        P.add(DARK, lambda: _cyl(bm, 0, 0, 0.6, h, 0.55, 0.4, n=4, phase=math.pi / 4))
        P.add(DARK, lambda: _cone(bm, 0, 0, h, 1.2, 0.42, n=4, phase=math.pi / 4))

    return _p(c, name, build)


def pine(c, variant=0, h=9.0):
    """A dark mountain pine: a trunk and four stacked cones."""
    name = "Keep Pine %d %.0f" % (variant, h)

    def build(P, bm):
        P.add("keep_barrel", lambda: _cyl(bm, 0, 0, -0.5, h * 0.3, 0.35, 0.25, n=5))
        for k in range(4):
            z = h * (0.18 + 0.2 * k)
            r = h * (0.3 - 0.06 * k) * (1.0 + 0.1 * (variant % 3))
            P.add(PINE, lambda z=z, r=r, k=k: _cone(bm, 0, 0, z, h * 0.34, r, n=7, phase=0.4 * k + variant))

    return _p(c, name, build)


def boat(c, variant=0):
    """A lake boat: a clinker hull, a mast and a striped sail."""
    name = "Keep Boat %d" % variant
    L = 7.0 + 2 * (variant % 2)

    def build(P, bm):
        rings = []
        for j in range(7):
            t = j / 6
            y = -L / 2 + L * t
            w = 1.6 * math.sin(math.pi * (0.12 + 0.76 * t)) + 0.1
            rings.append([bm.verts.new(p) for p in ((-w, y, 1.2), (-w * 0.6, y, 0.0), (w * 0.6, y, 0.0), (w, y, 1.2))])

        def hull():
            for a, b in zip(rings, rings[1:]):
                for i in range(3):
                    bm.faces.new((a[i], b[i], b[i + 1], a[i + 1]))
            bm.faces.new([rings[0][i] for i in range(4)])
            bm.faces.new([rings[-1][i] for i in reversed(range(4))])

        P.add("keep_barrel", hull)
        P.add("keep_barrel", lambda: _cyl(bm, 0, 0.3, 0.5, 7.5, 0.12, 0.1, n=5))
        P.add("keep_banner_dark" if variant % 2 else BANNER, lambda: _quad(bm, [(0, 0.5, 7.0), (0, 0.5, 2.0), (0, 3.6, 2.2), (0, 3.2, 6.6)], normal=(1, 0, 0)))

    return _p(c, name, build, fit=[BANNER, "keep_banner_dark"])


def fountain(c):
    """The courtyard fountain: an octagonal basin, a pillar with a bowl, and on top a
    small rearing dragon (the jets are game entities)."""
    name = "Keep Fountain"

    def build(P, bm):
        P.add(ASHLAR, lambda: loft(bm, [ring(bm, (0, 0), 5.0, -0.5, 8, phase=math.pi / 8), ring(bm, (0, 0), 5.0, 0.9, 8, phase=math.pi / 8),
                                        ring(bm, (0, 0), 4.3, 0.9, 8, phase=math.pi / 8), ring(bm, (0, 0), 4.3, 0.2, 8, phase=math.pi / 8)], cap_top=True))
        P.add("keep_lake_shallow", lambda: _cyl(bm, 0, 0, 0.1, 0.55, 4.3, 4.3, n=8, phase=math.pi / 8))
        P.add(ASHLAR, lambda: _cyl(bm, 0, 0, 0.5, 3.4, 0.7, 0.5, n=8))
        P.add(ASHLAR, lambda: _cyl(bm, 0, 0, 3.2, 3.8, 0.6, 1.8, n=8))
        _dragon(P, bm, (0, 0, 3.8), 0.32, DARK, DARK, GOLD)

    return _p(c, name, build)


# ------------------------------------------------------------------ dragons


def _dragon(P, bm, at, s, scale_mat, wing_mat, horn_mat, wings=0.8):
    """A western dragon perched on its hind legs, wings half raised, head up and looking
    ahead (+Y), its tail curled round to one side. `at`: its feet; `s`: size (1 is about
    14 m from nose to tail tip)."""
    ox, oy, oz = at

    def V(x, y, z):
        return (ox + x * s, oy + y * s, oz + z * s)

    # Body, neck and head as one tube.
    spine = [V(0, -3.6, 2.4), V(0, -1.6, 3.4), V(0, 0.6, 4.2), V(0, 2.2, 5.6), V(0, 3.0, 7.4), V(0, 3.4, 8.9)]
    rad = [1.2 * s, 1.9 * s, 1.9 * s, 1.2 * s, 0.85 * s, 0.7 * s]
    P.add(scale_mat, lambda: tube(bm, spine, rad, n=8))
    # The head: a long box with a snout and an open jaw.
    P.add(scale_mat, lambda: cuboid(bm, V(0, 4.3, 9.1), (1.5 * s, 2.2 * s, 1.3 * s)))
    P.add(scale_mat, lambda: cuboid(bm, V(0, 5.8, 8.9), (1.1 * s, 1.6 * s, 0.85 * s)))
    P.add(scale_mat, lambda: cuboid(bm, V(0, 5.5, 8.15), (1.0 * s, 1.9 * s, 0.35 * s), tilt=(0.3, 0.0)))
    for sx in (-1, 1):
        P.add(horn_mat, lambda sx=sx: tube(bm, [V(sx * 0.5, 3.8, 9.6), V(sx * 0.9, 2.8, 10.6), V(sx * 1.0, 1.7, 11.0)], [0.25 * s, 0.16 * s, 0.03 * s], n=4))
        P.add(horn_mat, lambda sx=sx: blob(bm, V(sx * 0.55, 4.9, 9.55), 0.18 * s))
        # Legs: front legs braced, hind legs crouched, claws gold.
        P.add(scale_mat, lambda sx=sx: tube(bm, [V(sx * 1.1, 1.3, 3.6), V(sx * 1.5, 2.2, 1.6), V(sx * 1.4, 2.6, 0.3)], [0.6 * s, 0.45 * s, 0.35 * s], n=6))
        P.add(scale_mat, lambda sx=sx: tube(bm, [V(sx * 1.4, -2.0, 3.0), V(sx * 2.1, -0.8, 1.8), V(sx * 1.9, -1.4, 0.3)], [0.9 * s, 0.6 * s, 0.4 * s], n=6))
        for fy in (2.9, -1.0):
            P.add(horn_mat, lambda sx=sx, fy=fy: cuboid(bm, V(sx * 1.6, fy, 0.15), (0.9 * s, 1.0 * s, 0.3 * s)))
        # Wings: an arm (shoulder, elbow, wrist) and three fingers, membrane between.
        sh, el, wr = V(sx * 1.2, 0.8, 5.2), V(sx * 4.4, -0.2, 5.2 + 3.6 * wings), V(sx * 7.6, -1.2, 5.2 + 6.0 * wings)
        tips = [V(sx * 12.0, -3.0, 5.2 + 4.4 * wings), V(sx * 11.0, -5.6, 5.2 + 1.2 * wings), V(sx * 8.0, -6.2, 3.2), V(sx * 1.4, -2.6, 4.0)]
        P.add(scale_mat, lambda sh=sh, el=el, wr=wr: tube(bm, [sh, el, wr], [0.45 * s, 0.35 * s, 0.25 * s], n=5))
        for t in tips[:3]:
            P.add(scale_mat, lambda wr=wr, t=t: tube(bm, [wr, t], [0.18 * s, 0.05 * s], n=4))

        def membrane(sx=sx, sh=sh, el=el, wr=wr, tips=tips):
            S_, E_, W_ = Vector(sh), Vector(el), Vector(wr)
            t1, t2, t3, tb = (Vector(t) for t in tips)

            def sag(a, b):
                # The skin between two fingers: its edge scalloped in toward the wrist.
                return (a + b) / 2 + (W_ - (a + b) / 2) * 0.28

            m12, m23, m3b = sag(t1, t2), sag(t2, t3), sag(t3, tb)
            tris = [(S_, E_, tb), (E_, m3b, tb), (E_, t3, m3b), (E_, W_, t3), (W_, m23, t3), (W_, t2, m23), (W_, m12, t2), (W_, t1, m12)]
            for tri in tris:
                n = (tri[1] - tri[0]).cross(tri[2] - tri[0])
                if n.length < 1e-6:
                    continue
                n.normalize()
                bm.faces.new([bm.verts.new(p) for p in tri])
                bm.faces.new(list(reversed([bm.verts.new(p - n * 0.06 * s) for p in tri])))

        P.add(wing_mat, membrane)
    # Spines down the back, and the tail curling round to its right with a barb.
    for k in range(6):
        p = spine[k]
        P.add(horn_mat, lambda p=p, k=k: _cone(bm, p[0], p[1], p[2] + rad[k] * 0.85, 0.9 * s, 0.3 * s, n=4))
    tail = [V(0, -3.6, 2.4), V(0.8, -6.0, 1.4), V(2.6, -7.8, 0.7), V(4.8, -7.4, 0.5), V(5.8, -5.4, 0.6), V(5.6, -3.6, 0.9)]
    P.add(scale_mat, lambda: tube(bm, tail, [1.1 * s, 0.85 * s, 0.6 * s, 0.42 * s, 0.28 * s, 0.12 * s], n=6))
    P.add(horn_mat, lambda: _cone(bm, V(5.6, -3.4, 0.6)[0], V(5.6, -3.4, 0.6)[1], V(5.6, -3.4, 0.6)[2], 1.0 * s, 0.45 * s, n=4))


def great_dragon(c):
    """The red dragon of Dragonspire: perched, wings half spread, looking out (+Y)."""
    name = "Great Red Dragon"

    def build(P, bm):
        _dragon(P, bm, (0, 0, 0), 1.0, "dragon_red", "dragon_wing", "dragon_belly", wings=1.0)

    return _p(c, name, build)


def dragon_statue(c, mat=DARK):
    """A stone dragon on a plinth (smaller, wings folded higher)."""
    name = "Dragon Statue %s" % mat

    def build(P, bm):
        P.add(ASHLAR, lambda: cuboid(bm, (0, 0, 0.6), (3.6, 4.4, 2.2)))
        P.add(ASHLAR, lambda: cuboid(bm, (0, 0, 1.75), (4.0, 4.8, 0.3)))
        _dragon(P, bm, (0, 0.3, 1.9), 0.42, mat, mat, mat, wings=1.2)

    return _p(c, name, build)


def stone_arch(c, span=12.0, h=9.0, depth=3.0):
    """A freestanding stone archway (portals, the royal approach): two piers and a round
    arch, along X. Visual over the road."""
    name = "Stone Arch %.1f %.1f" % (span, h)

    def build(P, bm):
        half = span / 2
        rings = []
        steps = 10
        for j in range(steps + 1):
            a = math.pi * j / steps
            x = -half * math.cos(a)
            z = h - half + half * math.sin(a) if h > half else h * math.sin(a)
            rings.append([bm.verts.new((x, y, zz)) for y, zz in ((-depth / 2, z), (depth / 2, z), (depth / 2, h + 2.0), (-depth / 2, h + 2.0))])

        def body():
            for a, b in zip(rings, rings[1:]):
                for i in range(4):
                    bm.faces.new((a[i], b[i], b[(i + 1) % 4], a[(i + 1) % 4]))

        P.add(ASHLAR, body)
        for sx in (-1, 1):
            P.add(ASHLAR, lambda sx=sx: cuboid(bm, (sx * (half + 1.0), 0, (h - half) / 2 - 0.5), (2.0, depth + 0.4, h - half + 1.0)))
        P.add(PARAPET, lambda: cuboid(bm, (0, 0, h + 2.3), (span + 4.0, depth + 0.6, 0.6)))

    return _p(c, name, build)
