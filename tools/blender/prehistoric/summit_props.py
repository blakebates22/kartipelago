# The sunny-mountain kit for Snowy Summit Pass: bright snowy pines and half-thawed
# broadleaf trees, boulders, icebergs and ice floes, natural ice arches, geyser cones and
# travertine pools, a pirate ship wrecked in the ice, a giant mammoth skull and its tusk
# arches, frozen tower ruins, chevron signs, prayer-flag bunting and floating ice islands.
# SPDX-License-Identifier: MIT
#
# Same rules as props.py: each prop is one mesh built once (Course.proto) and placed as
# copies, chunky and low-poly, all original designs. One-off pieces built in place (the
# bunting lines) collect into a single mesh.

import math

from course_kit import Vector, bmesh, rnd
from props import _faces, blob, cuboid, loft, ring, tube
from volcano_props import prism

SNOW = "summit_snow"
ICE = "glacier_ice"
ROCK = "summit_rock"
BONE = "mammoth_bone"
STONE = "frost_stone"
BARK = "giant_bark"


def _p(c, name, build):
    return c.proto(name, build) and name


def _cap(bm, centre, r, h=0.5, sx=1.0, sy=1.0, subdiv=1):
    """A soft snow cap (a flattened blob)."""
    blob(bm, centre, r, sx=sx, sy=sy, sz=h / r, subdiv=subdiv)


def _icicles(bm, pts, length, seed=0):
    """Icicles hanging from points along an edge."""
    for i, (x, y, z) in enumerate(pts):
        ln = length * (0.4 + 0.6 * rnd(i * 3 + seed))
        res = bmesh.ops.create_cone(bm, cap_ends=False, segments=4, radius1=0.0, radius2=0.1 + 0.08 * rnd(i + seed), depth=ln)
        for v in res["verts"]:
            v.co += Vector((x, y, z - ln / 2))


# ------------------------------------------------------------------ trees and plants


def pine(c, variant=0, height=12.0, snowy=True):
    """A bright conifer: a trunk and five stacked boughs, snow lying on them (or, in the
    thawed forest, fresh green)."""
    name = "Pine %d %d %s" % (variant, int(height), "snow" if snowy else "thaw")

    def build(bm):
        tube(bm, [(0, 0, -0.5), (0, 0, height * 0.3)], [0.45, 0.32], n=6)
        trunk = _faces(bm, 0)
        k0 = len(bm.faces)
        for i in range(4):
            t = i / 4
            r = height * 0.3 * (1 - t * 0.75)
            res = bmesh.ops.create_cone(bm, cap_ends=True, segments=7, radius1=r, radius2=r * 0.12, depth=height * 0.34)
            for v in res["verts"]:
                v.co += Vector((0, 0, height * (0.17 + 0.2 * i) + height * 0.17))
                v.co.x += 0.18 * math.sin(v.co.z * 1.3 + variant)
        return [(c.lib(BARK), trunk), (c.lib("pine_bright" if snowy else "leaf_bright"), _faces(bm, k0))]

    return _p(c, name, build)


def broadleaf(c, variant=0, frosted=False):
    """A thawing broadleaf tree (about 11 m): a forked trunk under a round crown of fresh
    leaves, with the last of the snow lying on top if `frosted`."""
    name = "Broadleaf %d %s" % (variant, "frost" if frosted else "green")

    def build(bm):
        lean = 0.6 * math.sin(variant * 1.9)
        tube(bm, [(0, 0, -0.5), (lean * 0.3, 0, 3.5), (lean, 0.2, 6.5)], [0.55, 0.42, 0.3], n=6)
        for a in (0.4, 2.5, 4.4):
            tube(bm, [(lean * 0.4, 0, 4.0), (lean + 2.2 * math.cos(a + variant), 2.2 * math.sin(a + variant), 7.0)], [0.25, 0.15], n=5)
        trunk = _faces(bm, 0)
        k0 = len(bm.faces)
        crown = [(lean, 0.2, 8.0, 3.6)] + [(lean + 2.4 * math.cos(a + variant), 2.4 * math.sin(a + variant), 7.4, 2.7) for a in (0.4, 2.5, 4.4)]
        for x, y, z, r in crown:
            blob(bm, (x, y, z), r, sz=0.8, subdiv=0)
        leaves = _faces(bm, k0)
        k1 = len(bm.faces)
        if frosted:
            for x, y, z, r in crown[:2]:
                _cap(bm, (x, y, z + r * 0.62), r * 0.8, 0.6, subdiv=0)
        return [(c.lib(BARK), trunk), (c.lib("leaf_bright"), leaves), (c.lib(SNOW), _faces(bm, k1))]

    return _p(c, name, build)


def shrub(c, variant=0, frosted=True):
    name = "Shrub %d %s" % (variant, "frost" if frosted else "green")

    def build(bm):
        for i in range(3 + variant % 2):
            a = i * 2.2 + variant
            blob(bm, (0.9 * math.cos(a) * (i > 0), 0.9 * math.sin(a) * (i > 0), 0.7), 1.1 - 0.15 * i, sz=0.75, subdiv=0)
        green = _faces(bm, 0)
        k0 = len(bm.faces)
        if frosted:
            _cap(bm, (0.2, 0, 1.4), 0.9, 0.35, subdiv=0)
        return [(c.lib("pine_bright" if frosted else "leaf_bright"), green), (c.lib(SNOW), _faces(bm, k0))]

    return _p(c, name, build)


def boulder(c, variant=0):
    name = "Summit Boulder %d" % variant

    def build(bm):
        blob(bm, (0, 0, 0.6), 2.4 + variant * 0.6, sx=1.3, sy=1.0, sz=0.7, subdiv=1)
        for v in bm.verts:
            v.co += Vector((0.3 * math.sin(v.co.y * 2 + variant), 0.3 * math.cos(v.co.x * 2), 0.2 * math.sin(v.co.x + v.co.y)))
        rock = _faces(bm, 0)
        k0 = len(bm.faces)
        _cap(bm, (0.2, 0, 0.6 + (2.4 + variant * 0.6) * 0.62), (2.4 + variant * 0.6) * 0.85, 0.45, sx=1.2)
        return [(c.lib(ROCK), rock), (c.lib(SNOW), _faces(bm, k0))]

    return _p(c, name, build)


# ------------------------------------------------------------------ ice


def iceberg(c, variant=0):
    """A chunky iceberg frozen into the lake (10-18 m tall): leaning blue prisms with snow
    on their tops."""
    name = "Iceberg %d" % variant

    def build(bm):
        tops = []
        for k in range(4 + variant % 3):
            a = k * 1.7 + variant
            d = 0.0 if k == 0 else 4.0 + 3.0 * rnd(k + variant * 5)
            bx, by = d * math.cos(a), d * math.sin(a)
            h = (16.0 + 4 * (variant % 2)) * (1.0 if k == 0 else 0.35 + 0.4 * rnd(k * 7 + variant))
            r = (6.0 if k == 0 else 3.0 + 1.5 * rnd(k * 3)) * (1.0 + 0.1 * variant % 3)
            lean = 0.12 * (rnd(k * 11 + variant) - 0.5) * h
            prism(bm, (bx, by, -2.0), (bx + lean, by + lean * 0.5, h), r, r * 0.45, n=5 + k % 2, phase=a)
            tops.append((bx + lean, by + lean * 0.5, h, r * 0.45))
        ice = _faces(bm, 0)
        k0 = len(bm.faces)
        for x, y, z, r in tops:
            _cap(bm, (x, y, z + 0.1), r * 1.1, 0.7)
        return [(c.lib(ICE), ice), (c.lib(SNOW), _faces(bm, k0))]

    return _p(c, name, build)


def floe(c, variant=0):
    """A flat ice floe floating on the hot water (5-8 m across), with a little snow."""
    name = "Floe %d" % variant

    def build(bm):
        n = 7
        r = 4.5 + 1.5 * (variant % 3)
        top = [bm.verts.new((r * (0.8 + 0.3 * rnd(i + variant * 9)) * math.cos(i * math.tau / n), r * (0.8 + 0.3 * rnd(i * 3 + variant)) * math.sin(i * math.tau / n), 0.35)) for i in range(n)]
        bot = [bm.verts.new((v.co.x * 0.9, v.co.y * 0.9, -0.7)) for v in top]
        bm.faces.new(top)
        sides_from = len(bm.faces)
        for i in range(n):
            bm.faces.new((bot[i], bot[(i + 1) % n], top[(i + 1) % n], top[i]))
        bm.faces.new(list(reversed(bot)))
        bm.faces.ensure_lookup_table()
        k0 = len(bm.faces)
        _cap(bm, (0.6, 0.3, 0.35), r * 0.45, 0.25, sx=1.3)
        return [(c.lib("lake_ice", "ice"), [0]), (c.lib(ICE), list(range(sides_from, k0))), (c.lib(SNOW, "packed_snow"), _faces(bm, k0))]

    return _p(c, name, build)


def ice_arch(c, span=26.0, height=15.0, variant=0):
    """A natural arch of blue glacier ice over a road (origin at the road's middle; the
    arch spans along X), lumpy and leaning, snow on its back, icicles under it."""
    name = "Ice Arch %d %d %d" % (variant, int(span), int(height))

    def build(bm):
        pts, radii = [], []
        n = 14
        for k in range(n + 1):
            t = k / n
            a = math.pi * t
            x = -math.cos(a) * (span / 2 + 3.0)
            z = math.sin(a) ** 0.8 * height - 2.0 + 2.0 * (1 - math.sin(a))
            y = 1.6 * math.sin(a * 2 + variant)
            pts.append((x, y, z))
            radii.append((3.4 - 1.2 * math.sin(a)) * (1 + 0.18 * math.sin(k * 2.1 + variant)))
        tube(bm, pts, radii, n=7)
        for v in bm.verts:
            v.co += Vector((0.4 * math.sin(v.co.z * 0.7 + variant), 0.5 * math.cos(v.co.x * 0.5), 0.3 * math.sin(v.co.x * 0.9)))
        ice = _faces(bm, 0)
        k0 = len(bm.faces)
        for k in range(3, n - 2, 2):
            x, y, z = pts[k]
            _cap(bm, (x, y, z + radii[k] * 0.8), radii[k] * 0.9, 0.5)
        snow = _faces(bm, k0)
        k1 = len(bm.faces)
        _icicles(bm, [(pts[k][0], pts[k][1] + 0.5 * (k % 2), pts[k][2] - radii[k] * 0.8) for k in range(4, n - 3)], 2.6, variant)
        return [(c.lib(ICE), ice), (c.lib(SNOW), snow), (c.lib("icefall_blue"), _faces(bm, k1))]

    return _p(c, name, build)


def floating_island(c, variant=0):
    """A chunk of glacier floating in the sky (20-30 m across): a snowy top, an inverted
    craggy spike of ice and rock beneath, icefalls spilling off its edge."""
    name = "Floating Island %d" % variant

    def build(bm):
        r = 12.0 + 3.0 * variant
        n = 9
        top = ring(bm, (0, 0), r, 0.0, n, rx=r * 1.2, phase=variant)
        mid = ring(bm, (0.5, 0.3), r * 0.7, -6.0, n, rx=r * 0.85, phase=variant + 0.3)
        low = ring(bm, (1.0, -0.4), r * 0.3, -16.0 - variant * 3, n, rx=r * 0.35, phase=variant + 0.6)
        for ringv in (top, mid, low):
            for i, v in enumerate(ringv):
                v.co += Vector((0, 0, 1.4 * math.sin(i * 2.3 + variant)))
        tip = bm.verts.new((1.5, -0.6, -26.0 - variant * 4))
        loft(bm, [low, mid, top], cap_top=False)
        for i in range(n):
            bm.faces.new((low[(i + 1) % n], low[i], tip))
        rock = _faces(bm, 0)
        k0 = len(bm.faces)
        bm.faces.new(top)
        _cap(bm, (0, 0, 0.6), r * 0.85, 2.6, sx=1.15)
        snow = _faces(bm, k0)
        k1 = len(bm.faces)
        # Icefalls frozen over the edge.
        for j in range(3):
            a = variant + j * 2.1
            x, y = r * 1.05 * math.cos(a), r * 0.9 * math.sin(a)
            tube(bm, [(x, y, 0.5), (x * 1.08, y * 1.08, -5.0), (x * 1.02, y * 1.02, -11.0 - 3 * j)], [1.4, 1.1, 0.4], n=5)
        return [(c.lib(ICE), rock), (c.lib(SNOW), snow), (c.lib("icefall_blue"), _faces(bm, k1))]

    return _p(c, name, build)


# ------------------------------------------------------------------ the hot springs


def geyser_cone(c, variant=0, flush=False):
    """A geyser's cone of travertine with orange mineral rims and a steaming pool in its
    crater (about 9 m across). `flush` makes a low ring set into a road."""
    name = "Geyser Cone %d %s" % (variant, "flush" if flush else "cone")

    def build(bm):
        h = 0.15 if flush else 2.4 + 0.6 * variant
        r0 = 4.6 + variant * 0.8
        rings = [ring(bm, (0, 0), r0, -0.8, 10), ring(bm, (0, 0), r0 * 0.82, h * 0.5, 10, phase=0.2), ring(bm, (0, 0), 1.8, h, 10, phase=0.1), ring(bm, (0, 0), 1.3, h - 0.3, 10, phase=0.1)]
        for i, v in enumerate(rings[1]):
            v.co.z += 0.25 * math.sin(i * 1.9 + variant)
        loft(bm, rings[:3], cap_top=False)
        rims = _faces(bm, 0)
        k0 = len(bm.faces)
        loft(bm, rings[2:], cap_top=False)
        inner = _faces(bm, k0)
        k1 = len(bm.faces)
        bm.faces.new(rings[3])
        return [(c.lib("sinter_rim"), rims), (c.lib("sinter"), inner), (c.lib("hot_pool"), _faces(bm, k1))]

    return _p(c, name, build)


def terrace_pools(c, variant=0):
    """Stepped travertine terraces: three or four scalloped basins down a slope, each
    brimming with bright hot water, orange mineral rims (origin at the top basin)."""
    name = "Terrace Pools %d" % variant

    def build(bm):
        rims, pools = [], []
        for k in range(3 + variant % 2):
            cx, cy = 2.5 * k * math.cos(variant), 5.5 * k
            r = 4.0 + 1.2 * k
            z = -1.3 * k
            n = 9
            outer = ring(bm, (cx, cy), r, z - 2.5, n, rx=r * 1.25, phase=k)
            lip = ring(bm, (cx, cy), r * 0.98, z + 0.25, n, rx=r * 1.22, phase=k)
            for i, v in enumerate(lip):
                v.co.z += 0.12 * math.sin(i * 2.4 + k)
            k0 = len(bm.faces)
            loft(bm, [outer, lip], cap_top=False)
            rims += _faces(bm, k0)
            k1 = len(bm.faces)
            water = ring(bm, (cx, cy), r * 0.92, z + 0.12, n, rx=r * 1.15, phase=k)
            bm.faces.new(water)
            pools += _faces(bm, k1)
        return [(c.lib("sinter_rim"), rims), (c.lib("hot_pool"), pools)]

    return _p(c, name, build)


# ------------------------------------------------------------------ the shipwreck


def shipwreck(c):
    """A pirate ship wrecked and frozen into the lake ice: a long curved hull of tarred
    planks rising to a high stern castle with glowing windows and to a pointed bow with
    a bowsprit, a main mast still standing with its yards and a torn sail, the fore mast
    snapped off and lying on the ice, snow on the decks, icicles along the rails. About
    40 m long; origin at the waterline amidships, bow toward +X."""
    name = "Shipwreck"

    def build(bm):
        L, B, D = 40.0, 10.5, 8.0
        n = 16
        secs = []
        for k in range(n + 1):
            t = k / n
            x = -L / 2 + L * t
            if t < 0.4:
                w = B / 2 * (0.8 + 0.2 * math.sin(math.pi / 2 * t / 0.4))
            else:
                w = B / 2 * max(0.06, 1 - ((t - 0.4) / 0.6) ** 2)
            sheer = D * 0.55 + 3.2 * (1 - t) ** 5 + 2.2 * t ** 4
            keel = -D * 0.45 + 3.5 * max(0.0, (t - 0.72) / 0.28) ** 2
            prof = [(w * 0.95, sheer), (w * 1.05, sheer * 0.5), (w * 0.85, keel * 0.35), (w * 0.35, keel * 0.92), (0.0, keel - 0.5)]
            prof = [(-y, z) for y, z in prof] + [(y, z) for y, z in reversed(prof[:-1])]
            secs.append([bm.verts.new((x, y, z)) for y, z in prof])
        m = len(secs[0])
        for sa, sb in zip(secs, secs[1:]):
            for j in range(m - 1):
                bm.faces.new((sa[j], sa[j + 1], sb[j + 1], sb[j]))
        bm.faces.new(list(reversed(secs[0])))  # the transom
        hull = _faces(bm, 0)
        bm.faces.ensure_lookup_table()
        bmesh.ops.recalc_face_normals(bm, faces=[bm.faces[i] for i in hull])
        k0 = len(bm.faces)
        # The deck, a little below the rails.
        rows = []
        for sec in secs[:-1]:
            ya, yb = sec[0].co.y * 0.9, sec[-1].co.y * 0.9
            zz = sec[0].co.z - 0.8
            rows.append((bm.verts.new((sec[0].co.x, ya, zz)), bm.verts.new((sec[0].co.x, yb, zz))))
        for ra, rb in zip(rows, rows[1:]):
            bm.faces.new((ra[0], rb[0], rb[1], ra[1]))
        # The stern castle.
        cuboid(bm, (-L / 2 + 4.0, 0, D * 0.55 + 3.2 + 1.6), (7.0, B * 0.82, 3.2))
        planks = _faces(bm, k0)
        k1 = len(bm.faces)
        # Windows across the stern and along the castle's sides, lit from inside.
        for y in (-3.0, -1.0, 1.0, 3.0):
            cuboid(bm, (-L / 2 - 0.05, y, D * 0.55 + 1.6), (0.2, 1.1, 1.3))
        for x in (-L / 2 + 2.5, -L / 2 + 5.5):
            for side in (-1, 1):
                cuboid(bm, (x, side * B * 0.41, D * 0.55 + 4.6), (1.2, 0.15, 1.0))
        windows = _faces(bm, k1)
        k2 = len(bm.faces)
        # The main mast (standing), its yards and crow's nest, and the bowsprit.
        tube(bm, [(-3.0, 0, 2.0), (-3.0, 0, 30.0)], [0.6, 0.32], n=6)
        tube(bm, [(-3.0, -8.5, 23.0), (-3.0, 8.5, 23.0)], 0.22, n=5)
        tube(bm, [(-3.0, -7.0, 14.0), (-3.0, 7.5, 14.0)], 0.26, n=5)
        loft(bm, [ring(bm, (-3.0, 0), 1.3, 25.0, 8), ring(bm, (-3.0, 0), 1.5, 26.6, 8)], cap_top=False)
        tube(bm, [(L / 2 - 2.0, 0, D * 0.55 + 1.2), (L / 2 + 10.0, 0, D * 0.55 + 6.0)], [0.45, 0.16], n=5)
        # The fore mast, snapped: a stump, and the rest lying out across the ice.
        tube(bm, [(8.0, 0, 2.0), (8.2, 0.2, 10.0)], [0.55, 0.45], n=6)
        tube(bm, [(9.0, 2.0, 0.2), (14.0, 9.0, -0.2), (17.0, 14.0, -0.4)], [0.42, 0.36, 0.28], n=5)
        tube(bm, [(12.0, 4.0, -0.2), (16.0, 2.0, -0.3)], 0.2, n=4)
        wood = _faces(bm, k2)
        k3 = len(bm.faces)
        # The torn sail on the main mast: ragged along the bottom, both sides.
        for side in (1, -1):
            top = [bm.verts.new((-3.0 + 0.2 * side, -7.6 + 15.2 * i / 5, 22.6)) for i in range(6)]
            bot = [bm.verts.new((-2.0 + 0.2 * side, -7.0 + 14.0 * i / 5, 14.6 + (2.2 if i % 2 else 0.0) + (1.4 if i == 3 else 0.0))) for i in range(6)]
            for i in range(5):
                q = (top[i], top[i + 1], bot[i + 1], bot[i])
                bm.faces.new(q if side > 0 else tuple(reversed(q)))
        # A tattered pennant at the masthead.
        for side in (1, -1):
            vs = [bm.verts.new(p) for p in ((-3.0, 0.03 * side, 30.0), (-3.0, 0.03 * side, 28.6), (-0.2, 0.03 * side, 29.0), (-1.2, 0.03 * side, 29.4), (0.4, 0.03 * side, 29.8))]
            bm.faces.new(vs if side > 0 else list(reversed(vs)))
        sail = _faces(bm, k3)
        sail_n = len(sail) - 2
        k4 = len(bm.faces)
        # Snow on the decks and the castle; icicles all along both rails.
        _cap(bm, (-L / 2 + 4.0, 0, D * 0.55 + 6.4), 3.8, 0.5, sx=1.0, sy=1.2)
        for x in (-10.0, -2.0, 6.0, 13.0):
            _cap(bm, (x, 0, D * 0.55 - 0.6), 3.2, 0.45, sx=1.3)
        snow = _faces(bm, k4)
        k5 = len(bm.faces)
        for j in (0, m - 1):
            _icicles(bm, [(sec[j].co.x, sec[j].co.y * 1.03, sec[j].co.z - 0.2) for sec in secs[1:-2]], 2.2, j)
        return [(c.lib("ship_hull"), hull), (c.lib("plank_road"), planks), (c.lib("glow_moss"), windows), (c.lib(BARK), wood),
                (c.lib("sail_cloth"), sail[:sail_n]), (c.lib("ship_hull"), sail[sail_n:]), (c.lib(SNOW), snow), (c.lib("icefall_blue"), _faces(bm, k5))]

    return _p(c, name, build)


# ------------------------------------------------------------------ the polar ruins


def tusk_gate(c, span=36.0, height=15.0):
    """The Polar Ruins' great gate: a colossal mammoth skull (about 18 m tall) lying
    beside the road, half sunk in the ice and facing across it, its two tusks sweeping
    out of their sockets, right over the road and down into the ice beyond, their tips
    curling up. Origin at the middle of the road, the road along Y."""
    name = "Tusk Gate %d %d" % (int(span), int(height))

    def build(bm):
        sx0 = -(span / 2 + 10.0)  # the skull's centre
        # The skull, facing +X: a tall domed crown, the face sloping down to the tusk
        # sockets, cheekbones, dark eye sockets and nasal opening.
        blob(bm, (sx0, 0, 10.5), 7.5, sx=0.78, sy=0.88, sz=1.2, subdiv=2)
        blob(bm, (sx0 + 4.5, 0, 6.5), 5.2, sx=0.72, sy=1.0, sz=1.0, subdiv=2)
        for side in (-1, 1):
            tube(bm, [(sx0 + 4.0, side * 3.4, 6.0), (sx0 + 9.5, side * 4.6, 2.0)], [2.6, 2.2], n=8)
            blob(bm, (sx0 + 1.5, side * 6.2, 7.0), 2.4, sx=0.8, sy=0.55, sz=1.1, subdiv=1)
        bone = _faces(bm, 0)
        k0 = len(bm.faces)
        for side in (-1, 1):
            blob(bm, (sx0 + 5.0, side * 4.4, 10.0), 1.7, sx=0.55, sy=0.9, sz=0.85, subdiv=1)
            blob(bm, (sx0 + 9.6, side * 4.6, 2.0), 1.6, sx=0.35, sy=1.0, sz=1.0, subdiv=1)  # the sockets' mouths
        blob(bm, (sx0 + 7.6, 0, 8.4), 1.5, sx=0.45, sy=1.0, sz=1.5, subdiv=1)
        dark = _faces(bm, k0)
        # The tusks: out of the sockets, up over the road, down beyond it, tips curling up.
        k1 = len(bm.faces)
        for side in (-1, 1):
            pts, radii = [], []
            x0, x1 = sx0 + 9.5, span / 2 + 7.0
            m = 20
            for k in range(m + 1):
                t = k / m
                x = x0 + (x1 - x0) * t
                z = 2.0 + height * math.sin(math.pi * min(1.0, t * 1.08)) ** 0.9 + (5.0 * ((t - 0.88) / 0.12) ** 2 if t > 0.88 else 0.0)
                y = side * (4.6 + 4.5 * t)
                pts.append((x, y, z))
                radii.append(2.1 - 1.65 * t ** 1.3)
            tube(bm, pts, radii, n=8)
        ivory = _faces(bm, k1)
        k2 = len(bm.faces)
        _cap(bm, (sx0 - 0.5, 0, 19.0), 5.5, 1.2, sx=1.0, sy=1.1)
        for side in (-1, 1):
            _cap(bm, (0.0, side * 7.0, height + 3.3), 2.0, 0.4, sx=2.2)
        return [(c.lib(BONE), bone + ivory), (c.lib("ship_hull"), dark), (c.lib(SNOW), _faces(bm, k2))]

    return _p(c, name, build)


def ribs(c, variant=0):
    """A giant's ribs curving up out of the ice (about 12 m)."""
    name = "Ribs %d" % variant

    def build(bm):
        for k in range(4):
            x = k * 3.4
            h = 12.0 - abs(k - 1.5) * 1.6
            for side in (-1, 1):
                tube(bm, [(x, side * 1.0, -0.5), (x, side * 5.5, h * 0.55), (x + 0.6, side * 3.5, h)], [0.7, 0.55, 0.3], n=6)
        tube(bm, [(-1.5, 0, 1.0), (12.0, 0, 0.6)], 0.9, n=7)  # the backbone
        return [(c.lib(BONE), _faces(bm, 0))]

    return _p(c, name, build)


def tower_ruin(c, variant=0, height=20.0):
    """A ruined round tower of pale stone, its top broken off in steps, snow on every
    ledge and icicles under the window arches."""
    name = "Tower Ruin %d %d" % (variant, int(height))

    def build(bm):
        n = 10
        r = 5.0
        rings = []
        for k, z in enumerate((-1.0, height * 0.3, height * 0.6)):
            rings.append(ring(bm, (0, 0), r * (1.08 - 0.04 * k), z, n))
        loft(bm, rings, cap_top=False)
        # The broken top: blocks round the rim at different heights.
        for i in range(n):
            a = (i + 0.5) * math.tau / n
            h = height * 0.6 + height * 0.4 * (0.25 + 0.75 * rnd(i * 3 + variant)) * (1.0 if i < n * 0.6 else 0.3)
            cuboid(bm, (r * 0.95 * math.cos(a), r * 0.95 * math.sin(a), height * 0.6 + (h - height * 0.6) / 2), (2.8, 1.4, h - height * 0.6), rot=a + math.pi / 2)
        stone = _faces(bm, 0)
        k0 = len(bm.faces)
        for i in range(n):
            a = (i + 0.5) * math.tau / n
            h = height * 0.6 + height * 0.4 * (0.25 + 0.75 * rnd(i * 3 + variant)) * (1.0 if i < n * 0.6 else 0.3)
            cuboid(bm, (r * 0.95 * math.cos(a), r * 0.95 * math.sin(a), h + 0.15), (3.0, 1.7, 0.35), rot=a + math.pi / 2)
        cuboid(bm, (0, 0, height * 0.6 + 0.2), (r * 1.6, r * 1.6, 0.4))
        snow = _faces(bm, k0)
        k1 = len(bm.faces)
        for z in (height * 0.32, height * 0.55):
            for a in (0.3 + variant, 2.4 + variant, 4.4 + variant):
                cuboid(bm, (r * 1.03 * math.cos(a), r * 1.03 * math.sin(a), z), (1.4, 0.3, 2.4), rot=a + math.pi / 2)
        dark = _faces(bm, k1)
        k2 = len(bm.faces)
        _icicles(bm, [(r * 1.08 * math.cos(a) + 0.4 * j, r * 1.08 * math.sin(a), z - 1.2) for z in (height * 0.32, height * 0.55) for a in (0.3 + variant, 2.4 + variant) for j in (-1, 0, 1)], 1.4, variant)
        return [(c.lib(STONE), stone), (c.lib(SNOW), snow), (c.lib("summit_rock"), dark), (c.lib("icefall_blue"), _faces(bm, k2))]

    return _p(c, name, build)


def ruin_column(c, variant=0):
    """A broken column of pale stone with a snow cap (4-9 m)."""
    name = "Ruin Column %d" % variant

    def build(bm):
        h = 4.0 + 5.0 * rnd(variant * 3 + 1)
        cuboid(bm, (0, 0, 0.4), (2.6, 2.6, 0.8))
        rings = [ring(bm, (0, 0), 0.95, 0.8, 8), ring(bm, (0, 0), 0.85, h, 8, phase=0.1)]
        loft(bm, rings, cap_top=True)
        stone = _faces(bm, 0)
        k0 = len(bm.faces)
        _cap(bm, (0, 0, h + 0.1), 1.0, 0.35)
        return [(c.lib(STONE), stone), (c.lib(SNOW), _faces(bm, k0))]

    return _p(c, name, build)


# ------------------------------------------------------------------ signs, flags and huts


def chevron(c, width=5.0):
    """A turn sign: a board of white chevrons on blue between two posts (facing -Y,
    origin at its foot)."""
    name = "Chevron %d" % int(width)

    def build(bm):
        cuboid(bm, (0, 0, 2.6), (width, 0.25, 1.6))
        board = _faces(bm, 0)
        k0 = len(bm.faces)
        for x in (-width / 2 + 0.4, width / 2 - 0.4):
            cuboid(bm, (x, 0.2, 1.2), (0.25, 0.25, 2.6))
        posts = _faces(bm, k0)
        k1 = len(bm.faces)
        _cap(bm, (0, 0, 3.45), width * 0.5, 0.18, sx=1.0, sy=0.12)
        return [(c.lib("chevron_sign"), board), (c.lib(BARK), posts), (c.lib(SNOW), _faces(bm, k1))]

    return _p(c, name, build)


def flag_pole(c, height=9.0):
    """A plain pole for stringing bunting from."""
    name = "Flag Pole %d" % int(height)

    def build(bm):
        tube(bm, [(0, 0, -0.5), (0, 0, height)], [0.18, 0.12], n=5)
        k0 = len(bm.faces)
        blob(bm, (0, 0, height + 0.2), 0.32, subdiv=0)
        return [(c.lib(BARK), _faces(bm, 0)[:k0]), (c.lib("bunting"), _faces(bm, k0))]

    return _p(c, name, build)


def lookout_hut(c):
    """A little stone hut with a steep snowy roof and a glowing window (about 7 m)."""
    name = "Lookout Hut"

    def build(bm):
        cuboid(bm, (0, 0, 2.0), (6.0, 5.0, 4.0))
        stone = _faces(bm, 0)
        k0 = len(bm.faces)
        for side in (-1, 1):
            vs = [bm.verts.new(p) for p in ((-3.6, side * 0.1, 7.2), (3.6, side * 0.1, 7.2), (3.6, side * 3.2, 3.6), (-3.6, side * 3.2, 3.6))]
            bm.faces.new(vs if side > 0 else list(reversed(vs)))
        roof = _faces(bm, k0)
        k1 = len(bm.faces)
        cuboid(bm, (0, -2.52, 2.2), (1.6, 0.06, 1.4))
        glow = _faces(bm, k1)
        return [(c.lib(STONE), stone), (c.lib(SNOW), roof), (c.lib("glow_moss"), glow)]

    return _p(c, name, build)


class Bunting:
    """Lines of prayer flags strung between points, all in one mesh: little triangles in
    bright colours hanging from a sagging line (both faces, so they show from either side)."""

    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new("UVMap")
        self.k = 0

    def line(self, p0, p1, sag=1.5, spacing=1.3, size=0.9):
        a, b = Vector(p0), Vector(p1)
        n = max(2, int((b - a).length / spacing))
        side = (b - a)
        side.z = 0
        side = side.normalized() if side.length > 1e-6 else Vector((1, 0, 0))
        for i in range(n):
            t0, t1 = (i + 0.1) / n, (i + 0.9) / n
            q0, q1 = a.lerp(b, t0), a.lerp(b, t1)
            q0.z -= sag * 4 * t0 * (1 - t0)
            q1.z -= sag * 4 * t1 * (1 - t1)
            tip = (q0 + q1) / 2 + Vector((0, 0, -size))
            u = ((self.k % 8) + 0.5) / 8
            self.k += 1
            # Front and back (bmesh can't share the corners between them).
            front = [self.bm.verts.new(v) for v in (q0, q1, tip)]
            back = [self.bm.verts.new(v) for v in (tip, q1, q0)]
            for face in (front, back):
                f = self.bm.faces.new(face)
                for loop in f.loops:
                    loop[self.uv].uv = (u, 0.5)

    def build(self, c, name="Bunting"):
        if not self.bm.faces:
            self.bm.free()
            return None
        from kartipelago_tools import materials

        ob = c.mesh_object(name, self.bm, "Flags", "visual")
        ob.data.materials.append(c.lib("bunting"))
        materials.ensure_paint(ob.data)
        return ob
