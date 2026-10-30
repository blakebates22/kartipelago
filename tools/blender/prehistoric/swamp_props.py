# The swamp kit for Bonebog Pyramid: boardwalk posts and rope rails, giant swamp trees
# and the canopy, hanging moss and vines, cobwebs, rotting logs and sunken timber,
# cattails and lily pads, stilt huts and watchtowers, rope bridges, giant skeletons
# (ribs, skulls, vertebrae), a carved guardian face, a lurking croc and light shafts.
# SPDX-License-Identifier: MIT
#
# Each builder makes one mesh (once per course, through Course.proto) that every copy
# shares, so editing "Prop Swamp Giant 0" in the .blend edits every copy. All original
# designs, kept low-poly in the spirit of late-90s console scenery.

import math

from course_kit import Vector, bmesh, rnd
from props import _faces, blob, cuboid, leaf_card, loft, ring, tube


def _p(c, name, build):
    return c.proto(name, build) and name


def cone(bm, base, tip, r, n=5):
    """A cone from a circle round `base` (radius r, square to the axis) to `tip`."""
    a, b = Vector(base), Vector(tip)
    t = (b - a).normalized()
    side = t.cross(Vector((0, 0, 1)))
    if side.length < 1e-3:
        side = Vector((1, 0, 0))
    side.normalize()
    up = side.cross(t).normalized()
    rim = [bm.verts.new(a + (side * math.cos(k * math.tau / n) + up * math.sin(k * math.tau / n)) * r) for k in range(n)]
    tv = bm.verts.new(b)
    for k in range(n):
        bm.faces.new((rim[k], rim[(k + 1) % n], tv))
    bm.faces.new(list(reversed(rim)))


# ------------------------------------------------------------------ the canopy


def swamp_giant(c, variant=0):
    """A colossal swamp tree, 50-60 m: a vast mossy trunk on buttress roots that reach
    far out into the water, great limbs, a broad crown and long vines and beards of moss
    hanging from the limbs (origin at the water line)."""
    name = "Swamp Giant %d" % variant

    def build(bm):
        h = 50.0 + 5.0 * variant
        lean = (1.5 * math.sin(variant * 2.3), 1.5 * math.cos(variant * 1.9))
        L = lambda t: (lean[0] * t, lean[1] * t)  # noqa: E731
        tube(bm, [(0, 0, -2.0), (*L(0.2), h * 0.25), (*L(0.5), h * 0.55), (*L(0.85), h * 0.82), (*L(1.0), h)], [4.6, 3.4, 2.7, 2.0, 1.4], n=12)
        # Buttress roots: tall fins running out into the water, and arching stilt roots.
        for i in range(9):
            a = i * math.tau / 9 + variant * 0.7
            ca, sa = math.cos(a), math.sin(a)
            reach = 10.0 + 5.0 * rnd(i + variant * 3)
            # A curved fin: thick at the trunk, sweeping down and out to the water.
            # (Low, close to the mud: Blake, Bonebog note 17, "lets lower the roots".)
            top_z = 3.6 + 1.4 * rnd(i * 2 + variant)
            prof = [(3.2, top_z), (reach * 0.35, top_z * 0.45), (reach * 0.7, top_z * 0.15), (reach, -1.5)]
            off = Vector((-sa, ca, 0)) * 0.7
            up = [bm.verts.new(Vector((r * ca, r * sa, z)) + off * (1.2 - 0.25 * k)) for k, (r, z) in enumerate(prof)]
            dn = [bm.verts.new(Vector((r * ca, r * sa, z)) - off * (1.2 - 0.25 * k)) for k, (r, z) in enumerate(prof)]
            base = [bm.verts.new(Vector((r * ca * 0.6 + 2.2 * ca * 0.4, r * sa * 0.6 + 2.2 * sa * 0.4, -1.5))) for r, _ in prof]
            for k in range(len(prof) - 1):
                bm.faces.new((up[k], up[k + 1], dn[k + 1], dn[k]))
                bm.faces.new((up[k], base[k], base[k + 1], up[k + 1]))
                bm.faces.new((dn[k + 1], base[k + 1], base[k], dn[k]))
            if i % 2 == 0:
                b = a + 0.35
                r2 = reach * 0.8
                tube(bm, [(3.0 * math.cos(b), 3.0 * math.sin(b), 4.2), (r2 * 0.6 * math.cos(b), r2 * 0.6 * math.sin(b), 2.4), (r2 * math.cos(b), r2 * math.sin(b), -1.5)], [0.9, 0.7, 0.6], n=6)
        limbs = []
        for i in range(6):
            a = i * math.tau / 6 + 0.3 + variant
            reach = 16.0 + 6.0 * rnd(i * 5 + variant)
            z0 = h * (0.62 + 0.07 * (i % 3))
            x0, y0 = L(0.7)
            end = (x0 + reach * math.cos(a), y0 + reach * math.sin(a), z0 + 6.0 + 4 * rnd(i + 9))
            tube(bm, [(x0, y0, z0), ((x0 + end[0]) * 0.5, (y0 + end[1]) * 0.5, z0 + 5.0), end], [1.6, 1.0, 0.55], n=6)
            limbs.append(end)
        trunk = _faces(bm, 0)
        k0 = len(bm.faces)
        tx, ty = L(1.0)
        crown = [(tx, ty, h + 5.0, 14.0)] + [(x, y, z + 3.0, 10.0 + 3.0 * rnd(k + variant)) for k, (x, y, z) in enumerate(limbs)]
        for x, y, z, r in crown:
            blob(bm, (x, y, z), r, sz=0.62, subdiv=1)
        top = _faces(bm, k0)
        k1 = len(bm.faces)
        for k, (x, y, z, r) in enumerate(crown[1:]):
            mx, my = (x + tx) / 2, (y + ty) / 2
            blob(bm, (mx, my, z + 4.0), r * 0.9, sz=0.55, subdiv=0)
        under = _faces(bm, k1)
        k2 = len(bm.faces)
        for k, (x, y, z) in enumerate(limbs):
            for j in range(2):
                vx = x * (0.45 + 0.25 * j) + (rnd(k * 7 + j) - 0.5) * 3
                vy = y * (0.45 + 0.18 * j) + (rnd(k * 11 + j) - 0.5) * 3
                top_z = z - 1.5 - j
                ln = 14.0 + 16.0 * rnd(k * 3 + j * 5 + variant)
                tube(bm, [(vx, vy, top_z), (vx + 0.4, vy, top_z - ln * 0.5), (vx, vy + 0.3, top_z - ln)], [0.22, 0.17, 0.1], n=3)
                for q in range(5):
                    leaf_card(bm, (vx + 0.2 * (q % 2), vy, top_z - ln * (0.15 + 0.17 * q)), q * 2.1 + k, 1.4, droop=0.9)
        vines = _faces(bm, k2)
        k3 = len(bm.faces)
        for k, (x, y, z) in enumerate(limbs):
            for j in range(2):
                bx = x * (0.35 + 0.3 * j)
                by = y * (0.35 + 0.3 * j)
                bz = z * (0.9 - 0.05 * j) - 1.0
                for q in range(4):
                    a = q * math.tau / 4 + k
                    v0 = bm.verts.new((bx + 0.9 * math.cos(a), by + 0.9 * math.sin(a), bz))
                    v1 = bm.verts.new((bx + 0.9 * math.cos(a + 0.9), by + 0.9 * math.sin(a + 0.9), bz))
                    v2 = bm.verts.new((bx + 0.5 * math.cos(a + 0.4), by + 0.5 * math.sin(a + 0.4), bz - 5.0 - 4.0 * rnd(k + q + j)))
                    bm.faces.new((v0, v1, v2))
        beard = _faces(bm, k3)
        return [(c.lib("bog_root"), trunk), (c.lib("bog_canopy"), top + under), (c.lib("vine_leaf"), vines + beard)]

    return _p(c, name, build)


def canopy_patch(c, variant=0):
    """A clump of the high canopy, about 40 m across: flattened leafy masses with a few
    strands of moss hanging below (origin at its underside). For the canopy's edges,
    where the ceiling of leaves gives way to open sky."""
    name = "Canopy %d" % variant

    def build(bm):
        n = 6
        for k in range(n):
            a = k * math.tau / (n - 1) + variant
            r = 0.0 if k == 0 else 11.0 + 7.0 * rnd(k * 3 + variant)
            x, y = r * math.cos(a), r * math.sin(a)
            blob(bm, (x, y, 2.5 + 3.0 * rnd(k + variant * 5)), 10.0 + 4.0 * rnd(k * 7 + variant), sz=0.4, subdiv=0)
        top = _faces(bm, 0)
        k1 = len(bm.faces)
        for k in range(6):
            a = k * 2.39 + variant
            r = 4.0 + 14.0 * rnd(k * 9 + variant)
            x, y = r * math.cos(a), r * math.sin(a)
            v0 = bm.verts.new((x - 0.6, y, 0.5))
            v1 = bm.verts.new((x + 0.6, y + 0.3, 0.5))
            v2 = bm.verts.new((x, y + 0.1, -5.0 - 6.0 * rnd(k + variant * 3)))
            bm.faces.new((v0, v1, v2))
        beard = _faces(bm, k1)
        return [(c.lib("bog_canopy"), top), (c.lib("bog_moss_hang"), beard)]

    return _p(c, name, build)


def hanging_vine(c, variant=0, length=16.0):
    """One long vine hanging from the canopy, strung with leaves (origin at the top)."""
    name = "Hanging Vine %d %d" % (variant, int(length))

    def build(bm):
        ph = variant * 1.3
        n = max(3, int(length / 4.5))
        pts = [(0.6 * math.sin(ph + q * 0.9), 0.4 * math.cos(ph + q * 0.7), -length * q / n) for q in range(n + 1)]
        tube(bm, pts, [0.16 - 0.08 * q / n for q in range(n + 1)], n=3)
        q = 1.0
        j = 0
        while q < length:
            t = q / length
            x = 0.6 * math.sin(ph + t * n * 0.9)
            leaf_card(bm, (x, 0.0, -q), j * 2.3 + variant, 0.8 + 0.4 * rnd(j + variant), droop=0.8)
            q += 2.2 + 1.0 * rnd(j * 5 + variant)
            j += 1
        for a in range(2):
            leaf_card(bm, pts[-1], a * math.pi + variant, 1.0, droop=1.4)
        return [(c.lib("vine_leaf"), _faces(bm, 0))]

    return _p(c, name, build)


def moss_beard(c, variant=0, length=4.0):
    """A beard of hanging moss (origin at the top)."""
    name = "Moss Beard %d" % variant

    def build(bm):
        for k in range(6):
            a = k * math.tau / 6 + variant
            r = 0.4 + 0.5 * rnd(k + variant)
            x, y = r * math.cos(a), r * math.sin(a)
            v0 = bm.verts.new((x - 0.35 * math.sin(a), y + 0.35 * math.cos(a), 0))
            v1 = bm.verts.new((x + 0.35 * math.sin(a), y - 0.35 * math.cos(a), 0))
            v2 = bm.verts.new((x * 0.8, y * 0.8, -length * (0.5 + 0.5 * rnd(k * 3 + variant))))
            bm.faces.new((v0, v1, v2))
        return [(c.lib("bog_moss_hang"), _faces(bm, 0))]

    return _p(c, name, build)


# ------------------------------------------------------------------ webs and swamp clutter


def cobweb(c, variant=0):
    """A cobweb (about 4 m across) in the plane x-z, facing -Y: spokes from a corner hub
    and sagging threads between them. variant 0: a full round web; 1: a corner web."""
    name = "Cobweb %d" % variant

    def build(bm):
        full = variant == 0
        spokes = 9 if full else 5
        a0, a1 = (0.0, math.tau) if full else (math.pi, math.pi * 1.5)
        hub = Vector((0, 0, 0))
        R = 2.4 if full else 3.6
        w = 0.035

        def thread(p, q):
            d = (q - p)
            side = Vector((-d.z, 0, d.x)).normalized() * w
            vs = [bm.verts.new(p - side), bm.verts.new(q - side), bm.verts.new(q + side), bm.verts.new(p + side)]
            bm.faces.new(vs)

        ends = []
        for k in range(spokes):
            a = a0 + (a1 - a0) * (k / (spokes if full else spokes - 1))
            e = Vector((R * math.cos(a) * (0.85 + 0.3 * rnd(k + variant)), 0, R * math.sin(a) * (0.85 + 0.3 * rnd(k * 3 + variant))))
            thread(hub, e)
            ends.append(e)
        rings = 5
        for r in range(1, rings + 1):
            f = r / (rings + 0.6)
            pts = [hub.lerp(e, f) for e in ends]
            pairs = list(zip(pts, pts[1:] + (pts[:1] if full else [])))
            for p, q in pairs:
                mid = (p + q) / 2 * 0.93
                thread(p, mid)
                thread(mid, q)
        return [(c.lib("cobweb"), _faces(bm, 0))]

    return _p(c, name, build)


def sunken_timber(c, variant=0):
    """Rotting remains of an old walkway: leaning pilings and a few broken planks, half
    sunk in the swamp (origin at the water line)."""
    name = "Sunken Timber %d" % variant

    def build(bm):
        posts = []
        for k in range(4 + variant % 3):
            x = k * 3.2 + (rnd(k + variant) - 0.5)
            y = (rnd(k * 7 + variant) - 0.5) * 2.5
            h = 0.8 + 2.4 * rnd(k * 3 + variant * 5)
            tilt = (rnd(k * 11 + variant) - 0.5) * 0.7
            tube(bm, [(x, y, -2.0), (x + tilt, y, h)], [0.32, 0.26], n=6)
            posts.append((x + tilt, y, h))
        wood = _faces(bm, 0)
        k0 = len(bm.faces)
        for k in range(len(posts) - 1):
            if rnd(k * 13 + variant) < 0.35:
                continue
            a, b = posts[k], posts[k + 1]
            z = min(a[2], b[2]) - 0.3
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            cuboid(bm, (mx, my, z), (3.4, 1.2, 0.18), rot=math.atan2(b[1] - a[1], b[0] - a[0]), tilt=((rnd(k) - 0.5) * 0.4, (rnd(k + 5) - 0.5) * 0.3))
        planks = _faces(bm, k0)
        return [(c.lib("bog_root"), wood), (c.lib("bog_boards"), planks)]

    return _p(c, name, build)


def croc(c):
    """A big swamp crocodile lurking at the surface: just its back, snout and eyes show
    (origin at the water line, facing +X)."""
    name = "Croc"

    def build(bm):
        blob(bm, (0, 0, -0.15), 1.0, sx=3.2, sy=1.0, sz=0.35, subdiv=1)  # back
        blob(bm, (3.6, 0, -0.05), 0.6, sx=1.9, sy=0.65, sz=0.3, subdiv=1)  # snout
        tube(bm, [(-2.8, 0, -0.1), (-5.0, 0.6, -0.1), (-7.0, 0.2, -0.25)], [0.6, 0.4, 0.15], n=5)  # tail
        for k in range(7):
            cone(bm, (-2.5 + k * 0.8, 0, 0.12), (-2.5 + k * 0.8, 0, 0.42), 0.18, n=4)  # scutes
        skin = _faces(bm, 0)
        k0 = len(bm.faces)
        for s in (-1, 1):
            blob(bm, (2.5, s * 0.35, 0.25), 0.2, subdiv=1)
        eyes = _faces(bm, k0)
        return [(c.lib("croc_skin"), skin), (c.lib("bog_eye"), eyes)]

    return _p(c, name, build)


def torch_post(c, height=2.8):
    """A thick post with a fire bowl on top (the flame at height + 0.6)."""
    name = "Torch Post %d" % int(height * 10)

    def build(bm):
        tube(bm, [(0, 0, -0.3), (0, 0, height)], [0.22, 0.18], n=6)
        for z in (height * 0.35, height * 0.7):
            tube(bm, [(0, 0, z - 0.12), (0, 0, z + 0.12)], 0.26, n=6)  # rope bindings
        wood = _faces(bm, 0)
        k0 = len(bm.faces)
        lo = ring(bm, (0, 0), 0.25, height, 6)
        hi = ring(bm, (0, 0), 0.55, height + 0.45, 6)
        loft(bm, [lo, hi], cap_top=False, cap_bottom=True)
        bowl = _faces(bm, k0)
        k1 = len(bm.faces)
        for k, (r, hgt, ox) in enumerate(((0.42, 1.1, 0.0), (0.25, 0.8, 0.12), (0.25, 0.7, -0.14))):
            res = bmesh.ops.create_cone(bm, cap_ends=False, segments=5, radius1=r, radius2=0.0, depth=hgt)
            for v in res["verts"]:
                v.co += Vector((ox, 0.05 * k, height + 0.35 + hgt / 2))
        flame = _faces(bm, k1)
        return [(c.lib("bog_rail"), wood), (c.lib("ruin_dark"), bowl), (c.lib("torch_glow"), flame)]

    return _p(c, name, build)


def stone_brazier(c):
    """A squat carved stone brazier with a big fire (the flame top at about 3 m)."""
    name = "Stone Brazier"

    def build(bm):
        cuboid(bm, (0, 0, 0.4), (2.4, 2.4, 0.8))
        cuboid(bm, (0, 0, 1.2), (1.4, 1.4, 0.9))
        lo = ring(bm, (0, 0), 0.9, 1.6, 8)
        hi = ring(bm, (0, 0), 1.5, 2.3, 8)
        loft(bm, [lo, hi], cap_top=False, cap_bottom=True)
        stone = _faces(bm, 0)
        k0 = len(bm.faces)
        for k, (r, hgt, ox, oy) in enumerate(((0.95, 2.0, 0, 0), (0.55, 1.4, 0.45, 0.2), (0.5, 1.2, -0.4, -0.3), (0.45, 1.3, 0.1, -0.5))):
            res = bmesh.ops.create_cone(bm, cap_ends=False, segments=6, radius1=r, radius2=0.0, depth=hgt)
            for v in res["verts"]:
                v.co += Vector((ox, oy, 2.0 + hgt / 2))
        flame = _faces(bm, k0)
        return [(c.lib("bog_carved"), stone), (c.lib("torch_glow"), flame)]

    return _p(c, name, build)


def stilt_hut(c, variant=0):
    """A swamp-dweller's hut on a plank platform on stilts, with a glowing doorway
    and a lantern (origin at the water line; platform at about 7 m)."""
    name = "Stilt Hut %d" % variant

    def build(bm):
        top = 7.0 + 2.0 * variant
        for sx in (-2.8, 2.8):
            for sy in (-2.8, 2.8):
                tube(bm, [(sx, sy, -2.0), (sx * 1.03, sy * 1.03, top)], 0.28, n=5)
        tube(bm, [(-2.8, -2.8, top * 0.4), (2.8, 2.8, top * 0.75)], 0.12, n=4)
        tube(bm, [(2.8, -2.8, top * 0.4), (-2.8, 2.8, top * 0.75)], 0.12, n=4)
        stilts = _faces(bm, 0)
        k0 = len(bm.faces)
        cuboid(bm, (0, 0, top + 0.15), (7.4, 7.4, 0.3))
        cuboid(bm, (0, -4.4, top + 0.15), (2.0, 1.6, 0.3))
        planks = _faces(bm, k0)
        k1 = len(bm.faces)
        lo = ring(bm, (0, 0), 2.4, top + 0.3, 8, phase=0.39)
        hi = ring(bm, (0, 0), 2.2, top + 2.6, 8, phase=0.39)
        loft(bm, [lo, hi], cap_top=False)
        walls = _faces(bm, k1)
        k2 = len(bm.faces)
        eave = ring(bm, (0, 0), 3.6, top + 2.3, 8, phase=0.39)
        apex = bm.verts.new((0, 0, top + 5.4))
        for k in range(8):
            bm.faces.new((eave[k], eave[(k + 1) % 8], apex))
        roof = _faces(bm, k2)
        k3 = len(bm.faces)
        cuboid(bm, (0, -2.32, top + 1.15), (1.2, 0.12, 1.7))
        tube(bm, [(2.6, -3.0, top + 2.5), (2.6, -3.0, top + 2.0)], 0.02, n=3)
        blob(bm, (2.6, -3.0, top + 1.7), 0.32, sz=1.3, subdiv=1)
        glow = _faces(bm, k3)
        return [(c.lib("bog_root"), stilts), (c.lib("bog_boards"), planks), (c.lib("palm_bark"), walls), (c.lib("thatch"), roof), (c.lib("window_glow"), glow)]

    return _p(c, name, build)


def watchtower(c):
    """A tall lookout on four leaning stilts, with a thatched roof and a lantern (origin
    at the water line; its deck at 13 m)."""
    name = "Watchtower"

    def build(bm):
        deck = 13.0
        for sx in (-1, 1):
            for sy in (-1, 1):
                tube(bm, [(sx * 3.4, sy * 3.4, -2.0), (sx * 1.9, sy * 1.9, deck + 3.2)], 0.3, n=5)
        for z0 in (3.0, 8.0):
            for k in range(4):
                a = k * math.pi / 2
                f0 = 3.4 - 1.5 * z0 / (deck + 5)
                f1 = 3.4 - 1.5 * (z0 + 4.5) / (deck + 5)
                p0 = (f0 * math.cos(a + math.pi / 4) * 1.41, f0 * math.sin(a + math.pi / 4) * 1.41, z0)
                p1 = (f1 * math.cos(a + 3 * math.pi / 4) * 1.41, f1 * math.sin(a + 3 * math.pi / 4) * 1.41, z0 + 4.5)
                tube(bm, [p0, p1], 0.13, n=4)
        wood = _faces(bm, 0)
        k0 = len(bm.faces)
        cuboid(bm, (0, 0, deck), (5.6, 5.6, 0.35))
        for k in range(4):
            a = k * math.pi / 2
            cuboid(bm, (2.7 * math.cos(a), 2.7 * math.sin(a), deck + 0.6), (0.2 if k % 2 == 0 else 5.4, 5.4 if k % 2 == 0 else 0.2, 0.9))
        planks = _faces(bm, k0)
        k1 = len(bm.faces)
        eave = ring(bm, (0, 0), 4.6, deck + 3.0, 4, phase=math.pi / 4)
        apex = bm.verts.new((0, 0, deck + 6.5))
        for k in range(4):
            bm.faces.new((eave[k], eave[(k + 1) % 4], apex))
        roof = _faces(bm, k1)
        k2 = len(bm.faces)
        blob(bm, (0, 0, deck + 2.0), 0.45, sz=1.3, subdiv=1)
        glow = _faces(bm, k2)
        return [(c.lib("bog_root"), wood), (c.lib("bog_boards"), planks), (c.lib("thatch"), roof), (c.lib("window_glow"), glow)]

    return _p(c, name, build)


def platform(c, variant=0):
    """A round plank platform round a giant trunk, with a rail (origin at its centre;
    radius 9 m, so it rings a trunk up to about 7 m across)."""
    name = "Tree Platform %d" % variant

    def build(bm):
        n = 12
        inner = ring(bm, (0, 0), 5.0, 0, n)
        outer = ring(bm, (0, 0), 9.0, 0, n)
        for k in range(n):
            bm.faces.new((inner[k], outer[k], outer[(k + 1) % n], inner[(k + 1) % n]))
        inner2 = ring(bm, (0, 0), 5.0, -0.35, n)
        outer2 = ring(bm, (0, 0), 9.0, -0.35, n)
        for k in range(n):
            bm.faces.new((outer[k], outer2[k], outer2[(k + 1) % n], outer[(k + 1) % n]))
            bm.faces.new((inner2[k], inner2[(k + 1) % n], outer2[(k + 1) % n], outer2[k]))
        planks = _faces(bm, 0)
        k0 = len(bm.faces)
        for k in range(n):
            a = k * math.tau / n
            tube(bm, [(8.7 * math.cos(a), 8.7 * math.sin(a), 0), (8.7 * math.cos(a), 8.7 * math.sin(a), 1.3)], 0.12, n=4)
            b = a + math.tau / n
            tube(bm, [(8.7 * math.cos(a), 8.7 * math.sin(a), 1.2), (8.7 * math.cos(b), 8.7 * math.sin(b), 1.2)], 0.07, n=3)
            tube(bm, [(8.7 * math.cos(a), 8.7 * math.sin(a), -0.3), (5.2 * math.cos(a + 0.3), 5.2 * math.sin(a + 0.3), -4.0)], 0.15, n=4)
        rail = _faces(bm, k0)
        return [(c.lib("bog_boards"), planks), (c.lib("bog_root"), rail)]

    return _p(c, name, build)


# ------------------------------------------------------------------ bones


def vertebra(c, variant=0):
    """One huge vertebra (about 3 m across, origin at its centre, the spine along X)."""
    name = "Vertebra %d" % variant

    def build(bm):
        blob(bm, (0, 0, 0), 1.0, sx=0.9, sy=1.1, sz=1.1, subdiv=0)  # the body
        cone(bm, (0, 0, 0.6), (-0.3, 0, 3.0 + 0.8 * variant), 0.45, n=5)  # spine
        for s in (-1, 1):
            cone(bm, (0, s * 0.5, 0.3), (0.1, s * 2.4, 0.9), 0.35, n=4)  # wings
        return [(c.lib("bog_bone"), _faces(bm, 0))]

    return _p(c, name, build)


def femur(c):
    """A giant thigh bone, about 9 m (along X)."""
    name = "Femur"

    def build(bm):
        tube(bm, [(-4.2, 0, 0), (-3.0, 0, 0.1), (3.0, 0, 0.1), (4.2, 0, 0)], [0.9, 0.55, 0.5, 0.8], n=7)
        for x, s in ((-4.4, 1), (4.4, -1)):
            blob(bm, (x, 0.45, 0.1), 0.85, subdiv=0)
            blob(bm, (x, -0.45, 0.1), 0.75, subdiv=0)
        return [(c.lib("bog_bone"), _faces(bm, 0))]

    return _p(c, name, build)


def horned_skull(c):
    """A frilled, three-horned skull lying in the mud (about 9 m long, facing +X)."""
    name = "Horned Skull"

    def build(bm):
        blob(bm, (0, 0, 1.6), 2.2, sx=1.5, sy=1.0, sz=0.8, subdiv=1)
        blob(bm, (3.4, 0, 1.1), 1.3, sx=1.4, sy=0.7, sz=0.6, subdiv=1)
        blob(bm, (5.0, 0, 0.9), 0.6, sx=1.0, sy=0.5, sz=0.7, subdiv=0)  # beak
        # The frill: a fan of bone behind the head.
        rim = []
        for k in range(9):
            a = math.pi * 0.15 + math.pi * 0.7 * k / 8
            rim.append(bm.verts.new((-2.6 - 2.0 * math.sin(a), 4.2 * math.cos(a) - 0.0, 2.2 + 3.6 * math.sin(a))))
        hub = bm.verts.new((-1.6, 0, 2.4))
        for a, b in zip(rim, rim[1:]):
            bm.faces.new((hub, a, b))
        for k in range(0, 9, 2):
            cone(bm, rim[k].co, rim[k].co + (rim[k].co - hub.co).normalized() * 0.9, 0.25, n=4)
        for s in (-1, 1):
            cone(bm, (0.8, s * 0.9, 2.6), (3.8, s * 1.3, 5.2), 0.45, n=5)  # brow horns
            blob(bm, (1.4, s * 1.25, 1.9), 0.45, subdiv=0)  # eye socket rims
        cone(bm, (4.0, 0, 1.6), (4.9, 0, 2.9), 0.3, n=4)  # nose horn
        return [(c.lib("bog_bone"), _faces(bm, 0))]

    return _p(c, name, build)


def great_skull(c):
    """A colossal predator's skull, jaws agape (an original design, about 30 m long at
    scale 1, facing +X, origin under its jaw joint): a long, deep snout, big round eye
    holes, a ridge of brow knobs and rows of curved teeth, lying half sunk."""
    name = "Great Skull"

    def build(bm):
        # The upper skull: cranium, cheeks and the long snout, tipped up (jaws open).
        up = 0.32
        cu, su = math.cos(up), math.sin(up)

        def U(x, y, z):
            return (x * cu - z * su, y, x * su + z * cu + 4.0)

        for (x, y, z), r, (sx, sy, sz) in (((-2, 0, 3.0), 6.0, (1.3, 1.05, 1.0)), ((8, 0, 2.0), 5.0, (1.5, 0.75, 0.75)), ((17, 0, 1.0), 3.6, (1.4, 0.6, 0.6))):
            res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
            for v in res["verts"]:
                v.co = Vector(U(x + v.co.x * sx, y + v.co.y * sy, z + v.co.z * sz))
        for s in (-1, 1):
            for k in range(4):
                blob(bm, U(-4 + k * 3.5, s * 3.2, 7.4 - k * 0.4), 1.1, subdiv=0)  # brow knobs
        upper = _faces(bm, 0)
        k0 = len(bm.faces)
        # The lower jaw: two long bones joined at the chin, resting in the swamp.
        for s in (-1, 1):
            tube(bm, [(-3, s * 4.5, 0.5), (6, s * 3.6, 0.0), (14, s * 2.4, -0.4), (21, s * 1.2, -0.6)], [2.0, 1.7, 1.3, 1.0], n=7)
        blob(bm, (21.5, 0, -0.6), 1.4, sx=1.2, sy=1.2, sz=0.8, subdiv=1)
        lower = _faces(bm, k0)
        k1 = len(bm.faces)
        # Teeth: down from the upper jaw and up from the lower.
        for s in (-1, 1):
            for k in range(9):
                x = 2 + k * 2.2
                base = U(x, s * (3.6 - k * 0.22), -1.4 - 0.1 * k)
                tip = U(x + 0.5, s * (3.4 - k * 0.22), -4.2 + 0.08 * k)
                cone(bm, base, tip, 0.7 - 0.03 * k, n=5)
            for k in range(8):
                x = 3 + k * 2.3
                y = s * (3.5 - k * 0.3)
                cone(bm, (x, y, 0.8 - 0.15 * k), (x + 0.4, y, 3.6 - 0.15 * k), 0.6 - 0.03 * k, n=5)
        teeth = _faces(bm, k1)
        k2 = len(bm.faces)
        for s in (-1, 1):
            res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=2.0)
            for v in res["verts"]:
                v.co = Vector(U(1.0 + v.co.x * 0.9, s * 5.6 + v.co.y * 0.25, 4.5 + v.co.z))
            res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.3)
            for v in res["verts"]:
                v.co = Vector(U(9.0 + v.co.x * 1.4, s * 3.8 + v.co.y * 0.25, 2.8 + v.co.z * 0.8))
        holes = _faces(bm, k2)
        return [(c.lib("bog_bone"), upper + lower), (c.lib("bone"), teeth), (c.lib("bog_dark_stone"), holes)]

    return _p(c, name, build)


def rib_pair(c, variant=0):
    """A pair of giant ribs rising from the swamp (unit size: 1 m half-width, 1 m tall
    to the spine; scale per copy), origin under the spine, ribs across Y."""
    name = "Rib Pair %d" % variant

    def build(bm):
        for s in (-1, 1):
            pts = []
            for j in range(8):
                u = j / 7
                y = s * (1.0 - u) ** 0.8 * (1.0 + 0.08 * math.sin(u * 3))
                z = math.sin(u * math.pi / 2) ** 0.75
                pts.append((-0.06 * u, y, z))
            tube(bm, pts, [0.06 * (1.15 - 0.45 * j / 7) for j in range(8)], n=6)
        blob(bm, (0, 0, 1.02), 0.09, sx=1.4, subdiv=1)
        cone(bm, (0, 0, 1.05), (-0.05, 0, 1.25), 0.04, n=4)
        return [(c.lib("bog_bone"), _faces(bm, 0))]

    return _p(c, name, build)


def bone_pile(c, variant=0):
    """A heap of old bones on a mud bank."""
    name = "Bone Pile %d" % variant

    def build(bm):
        for k in range(5):
            a = rnd(k * 3 + variant) * math.tau
            r = 1.8 * rnd(k * 7 + variant)
            x, y = r * math.cos(a), r * math.sin(a)
            L = 1.5 + 2.0 * rnd(k * 5 + variant)
            d = Vector((math.cos(a + 1), math.sin(a + 1), 0.2 * (rnd(k) - 0.5)))
            p0 = Vector((x, y, 0.3 + 0.3 * k / 6)) - d * L / 2
            p1 = p0 + d * L
            tube(bm, [tuple(p0), tuple(p1)], 0.2, n=4)
            blob(bm, tuple(p0), 0.32, sx=1.3, subdiv=0)
        if variant % 2 == 0:
            blob(bm, (0.5, 0.3, 0.9), 0.9, sx=1.4, sz=0.8, subdiv=1)  # a small skull
        return [(c.lib("bog_bone"), _faces(bm, 0))]

    return _p(c, name, build)


# ------------------------------------------------------------------ the pyramid's furniture


def pillar(c, height=24.0):
    """A massive carved pillar for the Great Hall (4 m square), with a stepped capital
    and base (origin at its foot)."""
    name = "Hall Pillar %d" % int(height)

    def build(bm):
        cuboid(bm, (0, 0, 0.6), (5.6, 5.6, 1.2))
        cuboid(bm, (0, 0, 1.6), (4.8, 4.8, 0.8))
        cuboid(bm, (0, 0, height - 1.4), (5.0, 5.0, 1.0))
        cuboid(bm, (0, 0, height - 0.5), (6.0, 6.0, 1.0))
        plain = _faces(bm, 0)
        k0 = len(bm.faces)
        cuboid(bm, (0, 0, height / 2), (4.0, 4.0, height - 3.6))
        carved = _faces(bm, k0)
        return [(c.lib("bog_dark_stone"), plain), (c.lib("bog_carved"), carved)]

    return _p(c, name, build)


def cattail_clump(c, variant=0):
    """A light clump of cattails: arching blades and a few stalks with brown heads."""
    name = "Swamp Cattails %d" % variant

    def build(bm):
        for i in range(9):
            a = rnd(i * 4.1 + variant * 9) * math.tau
            r = 0.6 * rnd(i * 2.3 + variant)
            x, y = r * math.cos(a), r * math.sin(a)
            h = 1.8 + 1.2 * rnd(i * 6.7 + variant * 3)
            out = Vector((math.cos(a), math.sin(a), 0))
            side = Vector((-math.sin(a), math.cos(a), 0)) * 0.12
            base = Vector((x, y, -0.3))
            tip = base + Vector((0, 0, h)) + out * (0.6 + 0.4 * rnd(i + variant))
            bm.faces.new((bm.verts.new(base - side), bm.verts.new(base + side), bm.verts.new(tip)))
        blades = _faces(bm, 0)
        k0 = len(bm.faces)
        heads = []
        for i in range(4):
            a = rnd(i * 3.7 + variant * 5 + 1) * math.tau
            r = 0.4 * rnd(i * 1.9 + variant * 2)
            x, y = r * math.cos(a), r * math.sin(a)
            h = 2.2 + 0.8 * rnd(i * 8.1 + variant)
            v0 = bm.verts.new((x - 0.03, y, -0.3))
            v1 = bm.verts.new((x + 0.03, y, -0.3))
            v2 = bm.verts.new((x, y, h + 0.5))
            bm.faces.new((v0, v1, v2))
            heads.append((x, y, h))
        stalks = _faces(bm, k0)
        k1 = len(bm.faces)
        for x, y, h in heads:
            tube(bm, [(x, y, h - 0.3), (x, y, h + 0.25)], [0.11, 0.1], n=4)
        brown = _faces(bm, k1)
        return [(c.lib("cattail_leaf"), blades + stalks), (c.lib("cattail_head"), brown)]

    return _p(c, name, build)


def tier_tree(c, variant=0):
    """A small, scrubby tree clinging to the pyramid's tiers (light: a few big leafy
    masses on a crooked trunk)."""
    name = "Tier Tree %d" % variant

    def build(bm):
        h = 6.0 + 2.0 * variant
        tube(bm, [(0, 0, -0.5), (0.8, 0.3, h * 0.5), (-0.3, 0.5, h)], [0.6, 0.45, 0.3], n=5)
        trunk = _faces(bm, 0)
        k0 = len(bm.faces)
        for dx, dy, dz, r in ((0, 0.4, h + 0.8, 3.4), (2.4, -0.6, h - 0.6, 2.6), (-2.2, 1.2, h - 0.2, 2.6)):
            blob(bm, (dx, dy, dz), r, sz=0.6, subdiv=0)
        leaves = _faces(bm, k0)
        return [(c.lib("bog_root"), trunk), (c.lib("bog_canopy"), leaves)]

    return _p(c, name, build)
