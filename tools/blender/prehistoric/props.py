# Reusable low-poly props for the Prehistoric World courses: palms, jungle trees, ferns,
# huts, totems, boulders, bones, swamp trees, reeds, glowing caps, basalt columns...
# SPDX-License-Identifier: MIT
#
# Each builder makes one mesh (once per course, through Course.proto) that every copy
# shares, so in the .blend you can edit "Prop Palm" and every palm changes. All original
# designs, kept to a few dozen faces each, in the spirit of late-90s console scenery.

import math

from course_kit import Vector, bmesh, rnd


def _faces(bm, before):
    """Faces added to bm since `before` faces existed."""
    bm.faces.ensure_lookup_table()
    return list(range(before, len(bm.faces)))


def ring(bm, centre, r, z, n, rx=None, phase=0.0):
    rx = rx or r
    return [bm.verts.new((centre[0] + rx * math.cos(phase + i * math.tau / n), centre[1] + r * math.sin(phase + i * math.tau / n), z)) for i in range(n)]


def loft(bm, rings, cap_top=True, cap_bottom=False):
    n = len(rings[0])
    for lo, hi in zip(rings, rings[1:]):
        for i in range(n):
            bm.faces.new((lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i]))
    if cap_top:
        bm.faces.new(rings[-1])
    if cap_bottom:
        bm.faces.new(list(reversed(rings[0])))


def tube(bm, path, radii, n=6):
    """A tube along a list of points (bones, trunks)."""
    rings = []
    for i, p in enumerate(path):
        a = path[max(0, i - 1)]
        b = path[min(len(path) - 1, i + 1)]
        t = (Vector(b) - Vector(a)).normalized()
        side = t.cross(Vector((0, 0, 1)))
        if side.length < 1e-3:
            side = Vector((1, 0, 0))
        side.normalize()
        up = side.cross(t).normalized()
        r = radii[i] if isinstance(radii, (list, tuple)) else radii
        rings.append([bm.verts.new(Vector(p) + (side * math.cos(k * math.tau / n) + up * math.sin(k * math.tau / n)) * r) for k in range(n)])
    loft(bm, rings, cap_top=True, cap_bottom=True)


def blob(bm, centre, r, sx=1.0, sy=1.0, sz=1.0, subdiv=1):
    res = bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    for v in res["verts"]:
        v.co = Vector((centre[0] + v.co.x * sx, centre[1] + v.co.y * sy, centre[2] + v.co.z * sz))
    return res


def frond(bm, base, angle, length, droop, width, segs=5):
    """A drooping palm or fern leaf: a folded strip."""
    d = Vector((math.cos(angle), math.sin(angle), 0))
    side = Vector((-d.y, d.x, 0))
    rows = []
    for k in range(segs + 1):
        t = k / segs
        c = Vector(base) + d * length * t + Vector((0, 0, droop * (0.6 * t - 1.6 * t * t)))
        w = width * (1 - t) ** 0.7 * (0.4 + 2.4 * t * (1 - t) + 0.3)
        fold = Vector((0, 0, 0.25 * w))
        rows.append((bm.verts.new(c - side * w), bm.verts.new(c + fold), bm.verts.new(c + side * w)))
    for a, b in zip(rows, rows[1:]):
        bm.faces.new((a[0], b[0], b[1], a[1]))
        bm.faces.new((a[1], b[1], b[2], a[2]))


# ------------------------------------------------------------------ builders


def palm(c, height=9.0, lean=1.6, variant=0):
    name = "Palm %d" % variant

    def build(bm):
        rings = []
        n = 6
        top = None
        for k in range(9):
            t = k / 8
            cx = lean * t * t + 0.3 * math.sin(variant + t * 3)
            z = height * t
            rings.append(ring(bm, (cx, 0), 0.42 - 0.14 * t, z, n))
            top = (cx, 0, z)
        loft(bm, rings)
        trunk = _faces(bm, 0)
        k0 = len(bm.faces)
        for i in range(7):
            a = i * math.tau / 7 + variant * 0.4
            frond(bm, top, a, 4.6 + 0.6 * rnd(i + variant), 2.6, 0.95)
        for i in range(3):
            a = i * math.tau / 3 + 0.5
            blob(bm, (top[0] + 0.45 * math.cos(a), 0.45 * math.sin(a), top[2] - 0.35), 0.3, subdiv=1)
        leaves = _faces(bm, k0)
        return [(c.lib("palm_bark"), trunk), (c.lib("palm_frond"), leaves)]

    return c.proto(name, build) and name


def jungle_tree(c, variant=0):
    name = "Jungle Tree %d" % variant

    def build(bm):
        h = 7.5 + variant
        tube(bm, [(0, 0, 0), (0.3, 0, h * 0.5), (-0.2, 0.2, h)], [0.7, 0.5, 0.4], n=6)
        trunk = _faces(bm, 0)
        k0 = len(bm.faces)
        for i, (dx, dy, dz, r) in enumerate(((0, 0, h + 1.2, 3.6), (2.2, 1.0, h - 0.4, 2.6), (-2.0, -1.2, h - 0.2, 2.8), (0.4, -2.2, h + 0.4, 2.4))):
            blob(bm, (dx, dy, dz), r, sz=0.7, subdiv=1)
        leaves = _faces(bm, k0)
        return [(c.lib("palm_bark"), trunk), (c.lib("jungle_leafcover"), leaves)]

    return c.proto(name, build) and name


def fern(c, mat="jungle_fern"):
    name = "Fern " + mat

    def build(bm):
        for i in range(7):
            a = i * math.tau / 7
            frond(bm, (0, 0, 0.3), a, 1.9, 0.9, 0.45, segs=4)
        return [(c.lib(mat), _faces(bm, 0))]

    return c.proto(name, build) and name


def flowers(c):
    name = "Flowers"

    def build(bm):
        for i in range(5):
            a = i * 1.7
            r = 0.7 * (i % 3)
            blob(bm, (r * math.cos(a), r * math.sin(a), 0.35), 0.38, sz=0.6, subdiv=1)
        return [(c.lib("blossom"), _faces(bm, 0))]

    return c.proto(name, build) and name


def cattails(c, variant=0):
    """A clump of cattails: long arching blades and stalks topped with brown heads."""
    name = "Cattails %d" % variant

    def build(bm):
        for i in range(12):
            a = rnd(i * 4.1 + variant * 9) * math.tau
            r = 0.6 * rnd(i * 2.3 + variant)
            x, y = r * math.cos(a), r * math.sin(a)
            h = 1.7 + 1.0 * rnd(i * 6.7 + variant * 3)
            out = Vector((math.cos(a), math.sin(a), 0))
            w = 0.11
            side = Vector((-math.sin(a), math.cos(a), 0)) * w
            base = Vector((x, y, -0.3))
            mid = base + Vector((0, 0, h * 0.6)) + out * 0.25
            tip = base + Vector((0, 0, h)) + out * (0.55 + 0.4 * rnd(i + variant))
            v = [bm.verts.new(base - side), bm.verts.new(base + side), bm.verts.new(mid + side * 0.8), bm.verts.new(mid - side * 0.8)]
            bm.faces.new(v)
            bm.faces.new((v[3], v[2], bm.verts.new(tip)))
        blades = _faces(bm, 0)
        k0 = len(bm.faces)
        heads = []
        for i in range(5):
            a = rnd(i * 3.7 + variant * 5 + 1) * math.tau
            r = 0.45 * rnd(i * 1.9 + variant * 2)
            x, y = r * math.cos(a), r * math.sin(a)
            h = 2.1 + 0.8 * rnd(i * 8.1 + variant)
            lean = 0.12 * h
            tube(bm, [(x, y, -0.3), (x + lean * math.cos(a), y + lean * math.sin(a), h + 0.45)], 0.035, n=4)
            heads.append((x + lean * 0.8 * math.cos(a), y + lean * 0.8 * math.sin(a), h))
        stalks = _faces(bm, k0)
        k1 = len(bm.faces)
        for x, y, h in heads:
            tube(bm, [(x, y, h - 0.35), (x, y, h - 0.25), (x, y, h + 0.2), (x, y, h + 0.3)], [0.07, 0.12, 0.12, 0.06], n=6)
        brown = _faces(bm, k1)
        return [(c.lib("cattail_leaf"), blades + stalks), (c.lib("cattail_head"), brown)]

    return c.proto(name, build) and name


def grand_tree(c, variant=0):
    """A towering canopy tree: a thick trunk on buttress roots, spreading limbs and a
    huge layered crown. The landmark trees of the valley."""
    name = "Grand Tree %d" % variant

    def build(bm):
        h = 13.0 + 2.5 * variant
        tube(bm, [(0, 0, -0.5), (0.2, 0.1, h * 0.35), (-0.1, 0.3, h * 0.7), (0.1, 0.2, h)], [1.35, 1.0, 0.8, 0.6], n=9)
        # Buttress roots: fins flaring out round the foot.
        for i in range(6):
            a = i * math.tau / 6 + variant
            ca, sa = math.cos(a), math.sin(a)
            fin = [(0.6 * ca, 0.6 * sa, 3.2), (2.6 * ca, 2.6 * sa, -0.3), (0.6 * ca, 0.6 * sa, -0.3)]
            off = Vector((-sa, ca, 0)) * 0.22
            vs = [bm.verts.new(Vector(q) + off) for q in fin] + [bm.verts.new(Vector(q) - off) for q in fin]
            bm.faces.new((vs[0], vs[1], vs[2]))
            bm.faces.new((vs[5], vs[4], vs[3]))
            bm.faces.new((vs[0], vs[3], vs[4], vs[1]))
        # Limbs reaching out to the crown.
        limbs = []
        for i in range(4):
            a = i * math.tau / 4 + 0.6 + variant * 0.7
            reach = 4.5 + 1.5 * rnd(i + variant * 4)
            end = (reach * math.cos(a), reach * math.sin(a), h * (0.8 + 0.12 * rnd(i * 3 + variant)))
            tube(bm, [(0, 0.2, h * 0.62), (end[0] * 0.5, end[1] * 0.5, end[2] - 0.6), end], [0.5, 0.36, 0.25], n=6)
            limbs.append(end)
        trunk = _faces(bm, 0)
        k0 = len(bm.faces)
        crown = [(0, 0, h + 2.4, 5.2)] + [(x, y, z + 1.0, 3.6 + 0.8 * rnd(k + variant)) for k, (x, y, z) in enumerate(limbs)]
        for x, y, z, r in crown:
            blob(bm, (x, y, z), r, sz=0.62, subdiv=2)
        top = _faces(bm, k0)
        k1 = len(bm.faces)
        # A darker under-layer, so the crown has depth.
        for x, y, z, r in crown[1:]:
            blob(bm, (x * 0.8, y * 0.8, z - 1.4), r * 0.85, sz=0.45, subdiv=1)
        under = _faces(bm, k1)
        return [(c.lib("palm_bark"), trunk), (c.lib("canopy_bright"), top), (c.lib("jungle_leafcover"), under)]

    return c.proto(name, build) and name


def bush(c, variant=0):
    """A round leafy bush."""
    name = "Bush %d" % variant

    def build(bm):
        for i in range(4):
            a = i * 2.1 + variant
            r = 0.7 * (i > 0)
            blob(bm, (r * math.cos(a), r * math.sin(a), 0.7 - 0.15 * (i > 0)), 1.0 - 0.18 * (i > 0), sz=0.8, subdiv=1)
        return [(c.lib("canopy_bright" if variant % 2 else "jungle_leafcover"), _faces(bm, 0))]

    return c.proto(name, build) and name


def campfire(c):
    """A little bonfire: a ring of stones, crossed logs and glowing flame tongues."""
    name = "Campfire"

    def build(bm):
        for i in range(9):
            a = i * math.tau / 9
            blob(bm, (1.25 * math.cos(a), 1.25 * math.sin(a), 0.12), 0.32, sx=1.2, sz=0.75, subdiv=1)
        stones = _faces(bm, 0)
        k0 = len(bm.faces)
        for i in range(4):
            a = i * math.tau / 4 + 0.4
            ca, sa = math.cos(a), math.sin(a)
            tube(bm, [(0.95 * ca, 0.95 * sa, 0.15), (0.1 * ca, 0.1 * sa, 0.75)], 0.13, n=6)
        logs = _faces(bm, k0)
        k1 = len(bm.faces)
        for i, (r, h, w) in enumerate(((0.0, 1.9, 0.42), (0.35, 1.3, 0.3), (0.35, 1.45, 0.3), (0.35, 1.2, 0.28), (0.3, 1.1, 0.26))):
            a = i * 2.3
            cx, cy = r * math.cos(a), r * math.sin(a)
            base = [bm.verts.new((cx + w * math.cos(k * math.tau / 5 + a), cy + w * math.sin(k * math.tau / 5 + a), 0.25)) for k in range(5)]
            tip = bm.verts.new((cx + 0.15 * math.cos(a + 1), cy + 0.15 * math.sin(a + 1), 0.25 + h))
            for k in range(5):
                bm.faces.new((base[k], base[(k + 1) % 5], tip))
        flames = _faces(bm, k1)
        return [(c.lib("valley_cliff"), stones), (c.lib("palm_bark"), logs), (c.lib("campfire_flame"), flames)]

    return c.proto(name, build) and name


def lily_pad(c, variant=0):
    """A floating lily pad (a disc with a notch), at the water's surface."""
    name = "Lily Pad %d" % variant

    def build(bm):
        n = 12
        notch = 0.42 + 0.1 * variant
        centre = bm.verts.new((0, 0, 0.04))
        rim = []
        for i in range(n + 1):
            a = notch / 2 + (math.tau - notch) * i / n
            r = 1.0 + 0.06 * math.sin(a * 3 + variant)
            rim.append(bm.verts.new((r * math.cos(a), r * math.sin(a), 0.07)))
        for a, b in zip(rim, rim[1:]):
            bm.faces.new((centre, a, b))
        return [(c.lib("lily_pad"), _faces(bm, 0))]

    return c.proto(name, build) and name


def lotus(c):
    """A pink water flower on its pad: two rings of pointed petals round a pale heart."""
    name = "Lotus"

    def build(bm):
        n = 12
        centre = bm.verts.new((0, 0, 0.04))
        rim = [bm.verts.new((1.3 * math.cos(0.25 + (math.tau - 0.5) * i / n), 1.3 * math.sin(0.25 + (math.tau - 0.5) * i / n), 0.07)) for i in range(n + 1)]
        for a, b in zip(rim, rim[1:]):
            bm.faces.new((centre, a, b))
        pad = _faces(bm, 0)
        before = len(bm.faces)
        for ring_i, (count, length, tilt, width, phase) in enumerate(((7, 0.75, 0.75, 0.32, 0.0), (6, 0.6, 1.15, 0.26, 0.45))):
            for k in range(count):
                a = phase + k * math.tau / count
                ca, sa = math.cos(a), math.sin(a)
                base = Vector((0.12 * ca, 0.12 * sa, 0.1))
                out = Vector((ca * math.cos(tilt), sa * math.cos(tilt), math.sin(tilt)))
                side = Vector((-sa, ca, 0))
                mid = base + out * (length * 0.5)
                tip = base + out * length + Vector((0, 0, 0.05))
                v = [bm.verts.new(base), bm.verts.new(mid + side * width), bm.verts.new(tip), bm.verts.new(mid - side * width)]
                bm.faces.new(v)
        blob(bm, (0, 0, 0.22), 0.13, sz=0.7, subdiv=1)
        return [(c.lib("lily_pad"), pad), (c.lib("lotus"), _faces(bm, before))]

    return c.proto(name, build) and name


def boulder(c, mat="valley_cliff", variant=0):
    name = "Boulder %s %d" % (mat, variant)

    def build(bm):
        res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
        for i, v in enumerate(res["verts"]):
            k = 0.82 + 0.36 * rnd(i * 3.1 + variant * 17)
            v.co = Vector((v.co.x * k * 1.2, v.co.y * k, v.co.z * k * 0.75 + 0.25))
        return [(c.lib(mat), _faces(bm, 0))]

    return c.proto(name, build) and name


def hut(c):
    name = "Hut"

    def build(bm):
        n = 10
        lo = ring(bm, (0, 0), 3.2, -0.3, n)
        hi = ring(bm, (0, 0), 3.2, 2.4, n)
        loft(bm, [lo, hi], cap_top=False)
        wall = _faces(bm, 0)
        k0 = len(bm.faces)
        eave = ring(bm, (0, 0), 4.3, 2.0, n)
        mid = ring(bm, (0, 0), 2.4, 4.0, n)
        tip = bm.verts.new((0, 0, 5.6))
        loft(bm, [eave, mid], cap_top=False)
        for i in range(n):
            bm.faces.new((mid[i], mid[(i + 1) % n], tip))
        bm.faces.new(list(reversed(eave)))
        roof = _faces(bm, k0)
        k1 = len(bm.faces)
        # A dark doorway.
        d0 = [bm.verts.new((3.25 * math.cos(a), 3.25 * math.sin(a), z)) for a, z in ((-0.25, 0), (0.25, 0), (0.25, 1.8), (-0.25, 1.8))]
        bm.faces.new(d0)
        door = _faces(bm, k1)
        return [(c.lib("tribal_paint"), wall), (c.lib("thatch"), roof), (c.lib("volcano_basalt"), door)]

    return c.proto(name, build) and name


def totem(c):
    name = "Totem"

    def build(bm):
        z = 0.0
        for k, (w, h) in enumerate(((0.8, 1.4), (0.7, 1.2), (0.75, 1.3))):
            res = bmesh.ops.create_cube(bm, size=1.0)
            for v in res["verts"]:
                v.co = Vector((v.co.x * w * 2, v.co.y * w * 2, z + (v.co.z + 0.5) * h))
            z += h
        body = _faces(bm, 0)
        k0 = len(bm.faces)
        # Wings at the top, and a beak.
        res = bmesh.ops.create_cube(bm, size=1.0)
        for v in res["verts"]:
            v.co = Vector((v.co.x * 4.2, v.co.y * 0.3, z - 0.9 + v.co.z * 0.5 + (0.4 if abs(v.co.x) > 0.4 and v.co.z > 0 else 0)))
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.35, radius2=0.0, depth=1.0)
        for v in res["verts"]:
            v.co = Vector((v.co.z + 0.5, v.co.x, v.co.y + z - 0.5))
            v.co.x += 0.7
        wings = _faces(bm, k0)
        return [(c.lib("tribal_paint"), body), (c.lib("thatch"), wings)]

    return c.proto(name, build) and name


def reeds(c):
    name = "Reeds"

    def build(bm):
        for i in range(9):
            a = rnd(i * 5.3) * math.tau
            r = 0.9 * rnd(i * 2.9)
            x, y = r * math.cos(a), r * math.sin(a)
            h = 1.6 + 1.4 * rnd(i * 7.7)
            lean = Vector((0.3 * math.cos(a), 0.3 * math.sin(a), 0))
            v0 = bm.verts.new((x - 0.08, y, 0))
            v1 = bm.verts.new((x + 0.08, y, 0))
            v2 = bm.verts.new(Vector((x, y, h)) + lean)
            bm.faces.new((v0, v1, v2))
        stalks = _faces(bm, 0)
        k0 = len(bm.faces)
        for i in range(3):
            a = rnd(i * 5.3) * math.tau
            r = 0.9 * rnd(i * 2.9)
            h = 1.6 + 1.4 * rnd(i * 7.7)
            tube(bm, [(r * math.cos(a) + 0.3 * math.cos(a), r * math.sin(a) + 0.3 * math.sin(a), h - 0.5), (r * math.cos(a) + 0.3 * math.cos(a), r * math.sin(a) + 0.3 * math.sin(a), h - 0.05)], 0.09, n=5)
        heads = _faces(bm, k0)
        return [(c.lib("palm_frond"), stalks), (c.lib("palm_bark"), heads)]

    return c.proto(name, build) and name


def swamp_tree(c, variant=0):
    name = "Swamp Tree %d" % variant

    def build(bm):
        h = 8 + 2 * variant
        tube(bm, [(0, 0, -0.5), (0.8, 0.2, h * 0.35), (-0.6, -0.3, h * 0.7), (0.3, 0.4, h)], [1.0, 0.65, 0.5, 0.35], n=6)
        # Roots splaying into the water.
        for i in range(4):
            a = i * math.tau / 4 + 0.4
            tube(bm, [(0, 0, 1.2), (1.6 * math.cos(a), 1.6 * math.sin(a), 0.4), (2.4 * math.cos(a), 2.4 * math.sin(a), -0.6)], [0.3, 0.22, 0.15], n=4)
        trunk = _faces(bm, 0)
        k0 = len(bm.faces)
        for dx, dy, dz, r in ((0.3, 0.4, h + 0.6, 3.4), (2.6, -0.8, h - 1.0, 2.4), (-2.4, 1.0, h - 0.8, 2.6)):
            blob(bm, (dx, dy, dz), r, sz=0.45, subdiv=1)
        canopy = _faces(bm, k0)
        k1 = len(bm.faces)
        # Hanging moss.
        for i in range(6):
            a = i * math.tau / 6
            x, y = 2.2 * math.cos(a), 2.2 * math.sin(a)
            v0 = bm.verts.new((x - 0.3, y, h - 0.6))
            v1 = bm.verts.new((x + 0.3, y, h - 0.6))
            v2 = bm.verts.new((x, y + 0.05, h - 3.6 - rnd(i) * 1.5))
            bm.faces.new((v0, v1, v2))
        moss = _faces(bm, k1)
        return [(c.lib("palm_bark"), trunk), (c.lib("swamp_moss"), canopy + moss)]

    return c.proto(name, build) and name


def glow_caps(c):
    name = "Glow Caps"

    def build(bm):
        stems = []
        caps = []
        for i, (x, y, h, r) in enumerate(((0, 0, 1.6, 0.9), (1.1, 0.5, 1.0, 0.6), (-0.8, 0.9, 0.7, 0.45))):
            k0 = len(bm.faces)
            tube(bm, [(x, y, 0), (x, y, h)], 0.16, n=5)
            stems += _faces(bm, k0)
            k1 = len(bm.faces)
            blob(bm, (x, y, h), r, sz=0.55, subdiv=1)
            caps += _faces(bm, k1)
        return [(c.lib("bone"), stems), (c.lib("glow_cap"), caps)]

    return c.proto(name, build) and name


def skull(c):
    """A giant fossil skull: a frilled, horned plant-eater's head lying in the mud."""
    name = "Fossil Skull"

    def build(bm):
        blob(bm, (0, 0, 2.2), 3.0, sx=1.6, sy=1.05, sz=0.8, subdiv=2)  # the cranium
        blob(bm, (4.6, 0, 1.6), 1.8, sx=1.3, sy=0.7, sz=0.6, subdiv=1)  # the snout
        blob(bm, (-2.8, 0, 3.6), 3.6, sx=0.35, sy=1.4, sz=1.1, subdiv=1)  # the frill
        for y in (-1.2, 1.2):
            tube(bm, [(1.4, y, 3.4), (3.4, y * 1.3, 5.2), (5.2, y * 1.4, 6.0)], [0.45, 0.28, 0.05], n=5)  # horns
        tube(bm, [(5.6, 0, 2.2), (6.6, 0, 3.0)], [0.35, 0.05], n=5)
        bone = _faces(bm, 0)
        k0 = len(bm.faces)
        for y in (-1.6, 1.6):
            blob(bm, (2.0, y, 2.9), 0.75, subdiv=1)  # eye sockets
        dark = _faces(bm, k0)
        return [(c.lib("bone"), bone), (c.lib("volcano_basalt"), dark)]

    return c.proto(name, build) and name


def basalt_columns(c):
    name = "Basalt Columns"

    def build(bm):
        for i in range(6):
            a = i * 1.9
            r = 0.0 if i == 0 else 1.5 + 0.4 * rnd(i)
            x, y = r * math.cos(a), r * math.sin(a)
            h = 7 - i * 0.8 + 1.5 * rnd(i * 3)
            lo = ring(bm, (x, y), 0.85, -1.0, 6, phase=0.3 * i)
            hi = ring(bm, (x, y), 0.85, h, 6, phase=0.3 * i)
            loft(bm, [lo, hi])
        return [(c.lib("volcano_basalt"), _faces(bm, 0))]

    return c.proto(name, build) and name


def dead_tree(c):
    name = "Charred Tree"

    def build(bm):
        tube(bm, [(0, 0, -0.3), (0.2, 0, 3), (-0.2, 0.1, 6.5)], [0.4, 0.3, 0.12], n=5)
        tube(bm, [(0.1, 0, 3.2), (1.6, 0.4, 4.6), (2.4, 0.5, 5.8)], [0.18, 0.12, 0.04], n=4)
        tube(bm, [(0, 0, 4.4), (-1.4, -0.6, 5.6), (-1.9, -0.8, 6.8)], [0.15, 0.1, 0.03], n=4)
        return [(c.lib("volcano_crust"), _faces(bm, 0))]

    return c.proto(name, build) and name


def crystals(c, mat="volcano_lava"):
    name = "Crystals " + mat

    def build(bm):
        for i in range(5):
            a = i * 1.3
            x, y = 0.9 * math.cos(a) * (i > 0), 0.9 * math.sin(a) * (i > 0)
            h = 2.6 - 0.35 * i
            tilt = Vector((0.5 * math.cos(a), 0.5 * math.sin(a), 0)) * (i > 0)
            base = ring(bm, (x, y), 0.35, 0.0, 4, phase=a)
            mid = ring(bm, (x + tilt.x * 0.5, y + tilt.y * 0.5), 0.42, h * 0.6, 4, phase=a)
            tip = bm.verts.new((x + tilt.x, y + tilt.y, h))
            loft(bm, [base, mid], cap_top=False)
            for k in range(4):
                bm.faces.new((mid[k], mid[(k + 1) % 4], tip))
        return [(c.lib(mat), _faces(bm, 0))]

    return c.proto(name, build) and name


# ------------------------------------------------------------------ placement


def scatter(c, proto, n, area, ok, terrain, seed=0, scale=(0.8, 1.3), role="both", coll="Props", sink=0.2, tries=40):
    """Place up to n copies at random spots in area (x0, x1, y0, y1) where ok(x, y, z)."""
    x0, x1, y0, y1 = area
    placed = []
    k = 0
    while len(placed) < n and k < n * tries:
        k += 1
        x = x0 + (x1 - x0) * rnd(k * 1.31 + seed * 7.7)
        y = y0 + (y1 - y0) * rnd(k * 2.17 + seed * 3.3)
        if any((x - px) ** 2 + (y - py) ** 2 < 9 for px, py in placed):
            continue
        z = c.ground_z(x, y, terrain)
        if z is None or not ok(x, y, z):
            continue
        s = scale[0] + (scale[1] - scale[0]) * rnd(k * 5.9 + seed)
        c.place(proto, x, y, z - sink, rot=rnd(k * 3.7 + seed) * math.tau, scale=s, role=role, coll=coll)
        placed.append((x, y))
    return placed


def clear_of_road(c, x, y, margin):
    """Far enough from the race line, and from any shortcut."""
    smp, d = c.nearest(x, y)
    if d <= smp.w / 2 + margin:
        return False
    return all((q.p.x - x) ** 2 + (q.p.y - y) ** 2 > (q.w / 2 + margin) ** 2 for q in c.extra_ground)


def piers(c, piece, every=12.0, mat=("palm_bark", "wall"), size=0.8, terrain=(), inset=1.2):
    """Posts under a bridge piece, down to whatever is below."""
    s0, s1 = piece["kp_from"], piece["kp_to"]
    if s1 < s0:
        s1 += c.length
    bm = bmesh.new()
    n = max(1, int((s1 - s0) / every))
    for k in range(1, n):
        smp = c.at(s0 + (s1 - s0) * k / n)
        for side in (-1, 1):
            p = smp.side(side * (smp.w / 2 - inset))
            bottom = c.ground_z(p.x, p.y, terrain)
            bottom = (bottom if bottom is not None else p.z - 20) - 1.0
            top = p.z - 0.6
            if top - bottom < 1.0:
                continue
            lo = ring(bm, (p.x, p.y), size, bottom, 4, phase=math.pi / 4)
            hi = ring(bm, (p.x, p.y), size, top, 4, phase=math.pi / 4)
            loft(bm, [lo, hi])
    if not bm.faces:
        bm.free()
        return None
    ob = c.mesh_object(piece.name + " Piers", bm, "Props")
    c.assign(ob, c.lib(*mat))
    return ob
