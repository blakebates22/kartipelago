# The Canyon Dash kit: saguaros, barrel cacti, agaves, sagebrush and dry grass, sandstone
# boulders and hoodoos, chevron signs, braziers, banner poles, the outpost's windmill
# tower, lookout tower and water tank, crates and barrels, and timber trestle bents.
# SPDX-License-Identifier: MIT
#
# Same rules as props.py: each prop is one mesh built once (Course.proto) and placed as
# copies, chunky and low-poly, all original designs. Big one-offs (the arch, the bridge,
# the start arch) are built in place by canyon_scenery.py.

import math

from course_kit import Matrix, Vector, bmesh, rnd
from props import _faces, blob, cuboid, loft, ring, tube


def _p(c, name, build):
    return c.proto(name, build) and name


def _cyl(bm, x, y, z0, z1, r0, r1=None, n=6, phase=0.0):
    r1 = r0 if r1 is None else r1
    loft(bm, [ring(bm, (x, y), r0, z0, n, phase=phase), ring(bm, (x, y), r1, z1, n, phase=phase)], cap_top=True, cap_bottom=True)


def _beam(bm, a, b, w, h=None):
    """A square timber from a to b (any direction)."""
    h = h or w
    a, b = Vector(a), Vector(b)
    d = (b - a)
    L = d.length
    d.normalize()
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 1e-3:
        side = Vector((1, 0, 0))
    side.normalize()
    up = side.cross(d).normalized()
    rings = []
    for p in (a, b):
        rings.append([bm.verts.new(p + side * sx * w / 2 + up * sy * h / 2) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    loft(bm, rings, cap_top=True, cap_bottom=True)


# ------------------------------------------------------------------ plants


def saguaro(c, variant=0):
    """A saguaro: a ribbed column with two or three upturned arms (origin at the ground)."""
    name = "Saguaro %d" % variant
    h = (7.5, 9.5, 6.0, 11.0)[variant % 4]

    def build(bm):
        r = 0.55 + 0.05 * variant
        _cyl(bm, 0, 0, -0.3, h - 0.5, r * 1.05, r * 0.9, n=8)
        blob(bm, (0, 0, h - 0.5), r * 0.92, sz=0.9, subdiv=0)
        arms = ((0.0, 0.42, 1.0), (math.pi, 0.55, 0.8), (math.pi * 0.5, 0.3, 0.7))[: 2 + variant % 2]
        for a, at, k in arms:
            a += variant * 0.7
            ca, sa = math.cos(a), math.sin(a)
            z = h * at
            out = 1.6 * k
            up = h * 0.33 * k
            ra = r * 0.7
            tube(bm, [(ca * r * 0.6, sa * r * 0.6, z), (ca * out, sa * out, z + 0.2), (ca * out * 1.05, sa * out * 1.05, z + 0.9), (ca * out, sa * out, z + up)], ra, n=6)
            blob(bm, (ca * out, sa * out, z + up), ra * 0.95, sz=0.9, subdiv=0)
        # A few flowers on the crown.
        k0 = len(bm.faces)
        for j in range(3):
            a = j * 2.1 + variant
            blob(bm, (math.cos(a) * r * 0.6, math.sin(a) * r * 0.6, h - 0.05), 0.2, subdiv=0)
        flowers = _faces(bm, k0)
        body = [i for i in range(len(bm.faces)) if i not in set(flowers)]
        return [(c.lib("saguaro"), body), (c.lib("canvas_sun"), flowers)]

    return _p(c, name, build)


def barrel_cactus(c, variant=0):
    name = "Barrel Cactus %d" % variant

    def build(bm):
        r = 0.6 + 0.15 * variant
        blob(bm, (0, 0, r * 0.7), r, sz=1.05)
        k0 = len(bm.faces)
        blob(bm, (0, 0, r * 1.7), r * 0.35, sz=0.5)
        top = _faces(bm, k0)
        return [(c.lib("saguaro"), list(range(k0))), (c.lib("chevron_amber"), top)]

    return _p(c, name, build)


def agave(c, variant=0):
    """A rosette of stiff pointed leaves (origin at the ground)."""
    name = "Agave %d" % variant

    def build(bm):
        n = 9 + variant * 2
        for k in range(n):
            a = k * math.tau / n + variant * 0.4
            tilt = 0.5 + 0.35 * ((k * 7) % 3) / 2
            L = 1.6 + 0.4 * ((k * 5) % 3)
            d = Vector((math.cos(a) * math.sin(tilt), math.sin(a) * math.sin(tilt), math.cos(tilt)))
            side = Vector((-math.sin(a), math.cos(a), 0))
            base = Vector((0, 0, 0.05))
            tip = base + d * L
            v = [bm.verts.new(base - side * 0.22), bm.verts.new(base + side * 0.22), bm.verts.new(tip), bm.verts.new(base + d * L * 0.4 + Vector((0, 0, 0.12)))]
            bm.faces.new((v[0], v[1], v[3]))
            bm.faces.new((v[0], v[3], v[2]))
            bm.faces.new((v[3], v[1], v[2]))
        return [(c.lib("agave"), list(range(len(bm.faces))))]

    return _p(c, name, build)


def sagebrush(c, variant=0):
    """A rounded clump of grey-green desert scrub."""
    name = "Sagebrush %d" % variant

    def build(bm):
        for k in range(3 + variant % 2):
            a = k * 2.3 + variant
            r = 0.9 + 0.3 * (k % 2)
            blob(bm, (math.cos(a) * 0.7, math.sin(a) * 0.7, r * 0.5), r, sz=0.7, subdiv=0)
        return [(c.lib("sagebrush"), list(range(len(bm.faces))))]

    return _p(c, name, build)


def dry_grass(c, variant=0):
    """A tuft of dry golden grass: crossed blades."""
    name = "Dry Grass %d" % variant

    def build(bm):
        n = 7
        for k in range(n):
            a = k * math.tau / n + variant
            lean = 0.4 + 0.2 * (k % 3)
            h = 0.9 + 0.25 * ((k + variant) % 3)
            d = Vector((math.cos(a) * math.sin(lean), math.sin(a) * math.sin(lean), math.cos(lean)))
            side = Vector((-math.sin(a), math.cos(a), 0)) * 0.18
            b = Vector((0, 0, 0))
            v = [bm.verts.new(b - side), bm.verts.new(b + side), bm.verts.new(b + d * h)]
            bm.faces.new(v)
            w = [bm.verts.new(b - side), bm.verts.new(b + side), bm.verts.new(b + d * h)]
            bm.faces.new(list(reversed(w)))
        return [(c.lib("dry_grass"), list(range(len(bm.faces))))]

    return _p(c, name, build)


def joshua_tree(c, variant=0):
    """A shaggy, forking desert tree with spiky leaf clusters (origin at the ground)."""
    name = "Desert Tree %d" % variant

    def build(bm):
        h = 4.5 + variant
        tube(bm, [(0, 0, -0.2), (0.2, 0, h * 0.5), (0.1, 0.1, h * 0.7)], [0.45, 0.36, 0.3], n=6)
        tips = []
        for k in range(3):
            a = k * 2.2 + variant
            tip = (math.cos(a) * 1.8, math.sin(a) * 1.8, h + 0.6 * (k % 2))
            tube(bm, [(0.1, 0.1, h * 0.7), (math.cos(a) * 0.9, math.sin(a) * 0.9, h * 0.85), tip], [0.28, 0.22, 0.18], n=5)
            tips.append(tip)
        trunk = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        for t in tips:
            blob(bm, (t[0], t[1], t[2] + 0.4), 0.8, sz=0.8)
        crown = _faces(bm, k0)
        return [(c.lib("weathered_timber"), trunk), (c.lib("agave"), crown)]

    return _p(c, name, build)


# ------------------------------------------------------------------ rocks


def boulder(c, variant=0):
    """A sandstone boulder, rounded by the wind, a darker band round it."""
    name = "Sandstone Boulder %d" % variant

    def build(bm):
        r = 1.0 + 0.5 * (variant % 3)
        blob(bm, (0, 0, r * 0.45), r, sx=1.25, sy=1.0, sz=0.7, subdiv=1)
        for v in bm.verts:
            v.co.x += 0.15 * math.sin(v.co.y * 3 + variant)
            v.co.z += 0.1 * math.cos(v.co.x * 2.5 + variant)
        return [(c.lib("strata_orange" if variant % 2 else "strata_red"), list(range(len(bm.faces))))]

    return _p(c, name, build)


def hoodoo(c, variant=0, height=14.0):
    """A hoodoo: a stack of eroded sandstone discs, waisted, a pale capstone on top."""
    name = "Hoodoo %d %d" % (variant, int(height))

    def build(bm):
        n = 5
        z = -2.0
        rings = []
        bands = 6
        for k in range(bands + 1):
            t = k / bands
            zz = z + (height + 2.0) * t
            r = (2.2 + 0.4 * variant) * (1.0 - 0.35 * math.sin(math.pi * t) + 0.18 * math.sin(k * 2.1 + variant)) * (1.0 - 0.3 * t)
            rings.append(ring(bm, (0.4 * math.sin(t * 3 + variant), 0.3 * math.cos(t * 2), ), r, zz, 7, phase=variant))
        loft(bm, rings, cap_top=False, cap_bottom=True)
        body = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        cr = (2.2 + 0.4 * variant) * 0.95
        loft(bm, [ring(bm, (0, 0), cr * 0.75, height - 0.2, 7), ring(bm, (0.2, 0), cr, height + 0.4, 7), ring(bm, (0.2, 0), cr * 0.9, height + 1.6, 7)])
        cap = _faces(bm, k0)
        return [(c.lib("strata_red"), body), (c.lib("strata_cream"), cap)]

    return _p(c, name, build)


# ------------------------------------------------------------------ the outpost and the road


def chevron_sign(c, variant=0):
    """A turn sign on two timber posts: amber with black chevrons (both faces). Origin at
    the ground; the board faces +Y (turn it to face the drivers)."""
    name = "Chevron Sign %d" % variant
    w = (4.0, 6.0)[variant % 2]

    def build(bm):
        for x in (-w / 2 + 0.3, w / 2 - 0.3):
            cuboid(bm, (x, 0.05, 0.9), (0.25, 0.25, 1.9))
        posts = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        cuboid(bm, (0, 0, 1.75), (w, 0.15, 1.2))
        board = _faces(bm, k0)
        return [(c.lib("weathered_timber"), posts), (c.lib("chevron_amber"), board)]

    return _p(c, name, build)


def brazier(c):
    """A stone fire bowl on a short pillar, the flame rising out of it (2.6 m tall)."""
    name = "Brazier"

    def build(bm):
        _cyl(bm, 0, 0, 0.0, 1.2, 0.45, 0.4, n=6)
        loft(bm, [ring(bm, (0, 0), 0.4, 1.2, 8), ring(bm, (0, 0), 0.85, 1.7, 8), ring(bm, (0, 0), 0.9, 1.9, 8)], cap_top=False, cap_bottom=True)
        stone = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        res = bmesh.ops.create_cone(bm, cap_ends=False, segments=6, radius1=0.7, radius2=0.05, depth=1.4)
        for v in res["verts"]:
            v.co.z += 2.45
        flame = _faces(bm, k0)
        return [(c.lib("masonry"), stone), (c.lib("torch_glow"), flame)]

    return _p(c, name, build)


def banner_pole(c, variant=0):
    """A tall timber pole with a hanging race banner (red or blue)."""
    name = "Banner Pole %d" % variant

    def build(bm):
        _cyl(bm, 0, 0, -0.3, 7.5, 0.18, 0.14, n=6)
        cuboid(bm, (0.8, 0, 7.1), (1.9, 0.14, 0.14))
        blob(bm, (0, 0, 7.6), 0.25)
        pole = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        cuboid(bm, (0.85, 0, 5.4), (1.6, 0.06, 3.2))
        cloth = _faces(bm, k0)
        return [(c.lib("weathered_timber"), pole), (c.lib("canvas_sun" if variant % 2 == 0 else "canvas_blue"), cloth)]

    return _p(c, name, build)


def windmill_tower(c):
    """A ranch windmill's timber tower and its platform (the turning wheel is drawn by
    the game: the "windmill" entity, at the hub 14.6 m up, facing +X)."""
    name = "Windmill Tower"

    def build(bm):
        h = 13.5
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            _beam(bm, (sx * 2.2, sy * 2.2, 0), (sx * 0.55, sy * 0.55, h), 0.28)
        for k in range(4):
            z0, z1 = k * h / 4, (k + 1) * h / 4
            f0, f1 = 2.2 - 1.65 * z0 / h, 2.2 - 1.65 * z1 / h
            for (ax, ay), (bx, by) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
                _beam(bm, (ax * f0, ay * f0, z0), (bx * f1, by * f1, z1), 0.14)
                _beam(bm, (ax * f1, ay * f1, z1), (bx * f1, by * f1, z1), 0.14)
        cuboid(bm, (0, 0, h + 0.1), (1.8, 1.8, 0.25))
        cuboid(bm, (0.2, 0, h + 1.1), (1.6, 0.5, 0.6))
        wood = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        # The tail vane, pointing away from the wheel.
        cuboid(bm, (-2.4, 0, h + 1.2), (3.2, 0.1, 0.15))
        cuboid(bm, (-4.1, 0, h + 1.4), (1.6, 0.08, 1.4))
        vane = _faces(bm, k0)
        return [(c.lib("weathered_timber"), wood), (c.lib("windmill_blade"), vane)]

    return _p(c, name, build)


def lookout_tower(c):
    """A timber lookout tower: four legs, a cabin on top with a pitched roof, a ladder."""
    name = "Lookout Tower"

    def build(bm):
        h = 11.0
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            _beam(bm, (sx * 3.0, sy * 3.0, -0.3), (sx * 2.2, sy * 2.2, h), 0.4)
        for z in (3.0, 7.0):
            for (ax, ay), (bx, by) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
                f = 3.0 - 0.8 * z / h
                _beam(bm, (ax * f, ay * f, z), (bx * f, by * f, z), 0.2)
                _beam(bm, (ax * f, ay * f, z), (bx * (f - 0.3), by * (f - 0.3), z + 4), 0.15)
        cuboid(bm, (0, 0, h + 0.15), (6.2, 6.2, 0.3))
        for k in range(4):
            a = k * math.pi / 2
            cuboid(bm, (math.cos(a) * 2.9, math.sin(a) * 2.9, h + 0.8), (6.0 if k % 2 == 0 else 0.2, 0.2 if k % 2 == 0 else 6.0, 1.0))
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            cuboid(bm, (sx * 2.9, sy * 2.9, h + 1.8), (0.25, 0.25, 3.0))
        _beam(bm, (3.4, 0.0, 0.0), (3.0, 0.0, h), 0.12)
        wood = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        verts = [bm.verts.new(v) for v in ((-3.6, -3.6, h + 3.2), (3.6, -3.6, h + 3.2), (3.6, 3.6, h + 3.2), (-3.6, 3.6, h + 3.2), (0, 0, h + 5.4))]
        for i in range(4):
            bm.faces.new((verts[i], verts[(i + 1) % 4], verts[4]))
        bm.faces.new(list(reversed(verts[:4])))
        roof = _faces(bm, k0)
        k1 = len(bm.faces)
        cuboid(bm, (0, 2.95, h + 0.95), (2.0, 0.12, 0.9))
        flag = _faces(bm, k1)
        return [(c.lib("weathered_timber"), wood), (c.lib("canvas_sun"), roof + flag)]

    return _p(c, name, build)


def water_tank(c):
    """A timber water tank on stilts, iron hoops round it."""
    name = "Water Tank"

    def build(bm):
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            _beam(bm, (sx * 1.8, sy * 1.8, -0.3), (sx * 1.6, sy * 1.6, 5.0), 0.3)
        _cyl(bm, 0, 0, 5.0, 8.6, 2.5, 2.6, n=10)
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=2.8, radius2=0.2, depth=1.2)
        for v in res["verts"]:
            v.co.z += 9.2
        wood = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        for z in (5.8, 7.8):
            _cyl(bm, 0, 0, z, z + 0.2, 2.62, 2.62, n=10)
        hoops = _faces(bm, k0)
        return [(c.lib("weathered_timber"), wood), (c.lib("windmill_blade"), hoops)]

    return _p(c, name, build)


def crates(c, variant=0):
    """A stack of crates and a barrel."""
    name = "Crates %d" % variant

    def build(bm):
        cuboid(bm, (0, 0, 0.6), (1.2, 1.2, 1.2), rot=0.1 * variant)
        cuboid(bm, (1.3, 0.2, 0.5), (1.0, 1.0, 1.0), rot=0.4)
        cuboid(bm, (0.4, 0.1, 1.65), (0.9, 0.9, 0.9), rot=-0.3)
        wood = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        _cyl(bm, -1.2, 0.4, 0.0, 1.3, 0.5, 0.5, n=8)
        barrel = _faces(bm, k0)
        return [(c.lib("plank_deck"), wood), (c.lib("weathered_timber"), barrel)]

    return _p(c, name, build)


def fence_post(c):
    """A ranch-fence post with two rails stubs (lines the plateau roads)."""
    name = "Fence Post"

    def build(bm):
        cuboid(bm, (0, 0, 0.7), (0.3, 0.3, 1.6))
        return [(c.lib("weathered_timber"), list(range(len(bm.faces))))]

    return _p(c, name, build)
