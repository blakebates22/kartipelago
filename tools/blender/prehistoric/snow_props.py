# Snow Dragon Pass's props: the mountain village's houses half buried in snow, ration
# stalls and storehouses, sledges and sacks, snowy pines, the monastery's chortens and
# halls, prayer-flag poles and bells, the citadel's red towers, icicles, broken arches,
# guard posts and the fork signs. Each builds one mesh (a prototype) that every copy
# shares; origins are at the ground, fronts face +Y. All our own designs.
# SPDX-License-Identifier: MIT

import math

from canyon_props import _beam, _cyl
from course_kit import Vector, bmesh, rnd
from isles_props import _box, _p, fit_uvs, roof
from props import _faces, blob, cuboid, loft, ring, tube

# ------------------------------------------------------------------ the village


def _gable(bm, w, d, z, h, over=0.6):
    """A steep gabled roof along X over a w x d body, eaves at z: two slabs and the snow
    lying thick on them."""
    W, D = w / 2 + over, d / 2 + over
    k = len(bm.faces)
    for s in (-1, 1):
        a = [bm.verts.new(p) for p in ((-W, s * D, z), (W, s * D, z), (W, 0, z + h), (-W, 0, z + h))]
        bm.faces.new(a if s > 0 else list(reversed(a)))
        b = [bm.verts.new((v.co.x, v.co.y, v.co.z - 0.25)) for v in a]
        bm.faces.new(list(reversed(b)) if s > 0 else b)
    for x in (-W, W):
        g = [bm.verts.new(p) for p in ((x, -d / 2, z), (x, d / 2, z), (x, 0, z + h * (d / 2) / D))]
        bm.faces.new(g if x > 0 else list(reversed(g)))
    return _faces(bm, k)


def snow_house(c, variant=0):
    """A mountain house: a stone ground floor, whitewashed or timber walls, small warm
    windows, a steep roof under thick snow (bigger ones have a second storey)."""
    name = "Snow House %d" % variant

    def build(bm):
        w = 7.0 + variant % 3 * 1.6
        d = 6.0 + variant % 2 * 1.2
        h = 3.2 + (2.6 if variant % 4 == 3 else 0.0)
        k = len(bm.faces)
        _box(bm, -w / 2, -d / 2, -1.0, w / 2, d / 2, 1.2)
        stone = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -w / 2 + 0.1, -d / 2 + 0.1, 1.2, w / 2 - 0.1, d / 2 - 0.1, 1.2 + h)
        walls = _faces(bm, k)
        k = len(bm.faces)
        for x in (-w * 0.28, w * 0.28):
            _box(bm, x - 0.5, d / 2 - 0.05, 1.9, x + 0.5, d / 2 + 0.06, 2.8)
        if h > 4:
            _box(bm, -0.5, d / 2 - 0.05, 4.4, 0.5, d / 2 + 0.06, 5.2)
        win = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -0.7, d / 2 - 0.05, 0.6, 0.7, d / 2 + 0.08, 2.6)
        door = _faces(bm, k)
        roofs = _gable(bm, w, d, 1.2 + h, d * 0.55)
        wall_mat = "sdp_whitewash" if variant % 2 == 0 else "wood_wall"
        return [(c.lib("stone_base"), stone), (c.lib(wall_mat), walls), (c.lib("lantern_amber"), win), (c.lib("door_wood"), door),
                (c.lib("sdp_roof"), roofs)]

    return _p(c, name, build)


HOUSE_WINDOW = (0.0, 0.0, 2.4)


def ration_stall(c, variant=0):
    """A ration stall: a trestle table, a tattered awning, a pot and a few bowls (most
    of them empty)."""
    name = "Ration Stall %d" % variant

    def build(bm):
        k = len(bm.faces)
        _box(bm, -2.2, -0.6, 0.9, 2.2, 0.6, 1.05)
        for x in (-1.9, 1.9):
            _beam(bm, (x, 0, -0.2), (x, 0, 0.9), 0.14)
        for x, y in ((-2.6, -1.6), (2.6, -1.6), (-2.6, 1.6), (2.6, 1.6)):
            _beam(bm, (x, y, -0.3), (x, y, 2.6 if y > 0 else 3.0), 0.12)
        wood = _faces(bm, k)
        k = len(bm.faces)
        a = [bm.verts.new(p) for p in ((-2.9, -1.9, 3.1), (2.9, -1.9, 3.1), (2.9, 1.9, 2.5), (-2.9, 1.9, 2.5))]
        bm.faces.new(a)
        bm.faces.new(list(reversed([bm.verts.new(v.co + Vector((0, 0, -0.05))) for v in a])))
        # A torn flap hanging from the front.
        for i in range(4):
            x = -2.6 + i * 1.5
            f = [bm.verts.new(p) for p in ((x, 1.92, 2.5), (x + 1.1, 1.92, 2.5), (x + 1.1, 1.95, 2.1 - 0.2 * (i % 2)), (x, 1.95, 2.0 + 0.1 * i))]
            bm.faces.new(f)
        cloth = _faces(bm, k)
        k = len(bm.faces)
        _cyl(bm, -1.1, 0, 1.05, 1.7, 0.45, 0.5, n=8)
        for i in range(3 + variant % 2):
            _cyl(bm, 0.2 + i * 0.5, 0.1, 1.05, 1.2, 0.18, 0.22, n=6)
        iron = _faces(bm, k)
        return [(c.lib("weathered_timber"), wood), (c.lib("sdp_awning"), cloth), (c.lib("iron"), iron)]

    return _p(c, name, build)


def storehouse(c, full=True):
    """An imperial storehouse: thick stone walls, a red door barred with iron and, when
    `full`, grain sacks stacked to the rafters behind an open grille (its front +Y)."""
    name = "Storehouse %d" % full

    def build(bm):
        w, d, h = 14.0, 9.0, 6.0
        k = len(bm.faces)
        _box(bm, -w / 2, -d / 2, -1.0, w / 2, d / 2, h)
        stone = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -w / 2 - 0.2, -d / 2 - 0.2, h - 1.0, w / 2 + 0.2, d / 2 + 0.2, h)
        band = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -1.6, d / 2, 0.0, 1.6, d / 2 + 0.15, 4.2)
        red = _faces(bm, k)
        k = len(bm.faces)
        for z in (1.2, 2.6, 3.8):
            _box(bm, -1.7, d / 2 + 0.15, z - 0.1, 1.7, d / 2 + 0.3, z + 0.1)
        for x in (-w * 0.32, w * 0.32):
            for i in range(5):
                _box(bm, x - 1.6 + i * 0.8 - 0.06, d / 2 + 0.05, 1.0, x - 1.6 + i * 0.8 + 0.06, d / 2 + 0.2, 4.0)
        iron = _faces(bm, k)
        k = len(bm.faces)
        if full:
            for x in (-w * 0.32, w * 0.32):
                for j in range(3):
                    for i in range(3):
                        blob(bm, (x - 1.0 + i * 1.0, d / 2 - 0.6, 1.4 + j * 0.9), 0.55, 1.0, 0.8, 0.8)
        else:
            for x in (-w * 0.32, w * 0.32):
                _box(bm, x - 1.6, d / 2 - 0.4, 0.0, x + 1.6, d / 2 - 0.2, 4.0)
        sacks = _faces(bm, k)
        roofs = _gable(bm, w, d, h, d * 0.42, over=0.9)
        return [(c.lib("sdp_aqueduct"), stone), (c.lib("sdp_redwall"), band + red), (c.lib("iron"), iron),
                (c.lib("sdp_burlap" if full else "wood_wall"), sacks), (c.lib("sdp_roof"), roofs)]

    return _p(c, name, build)


def sack_pile(c, variant=0):
    name = "Sack Pile %d" % variant

    def build(bm):
        n = 4 + variant % 3 * 2
        for i in range(n):
            x = (i % 3 - 1) * 0.9 + 0.2 * rnd(i + variant * 7)
            y = (i // 3 % 2 - 0.5) * 0.9
            z = 0.35 + (i // 6) * 0.6
            blob(bm, (x, y, z), 0.5, 1.0, 0.75, 0.7)
        return [(c.lib("sdp_burlap"), _faces(bm, 0))]

    return _p(c, name, build)


def sled(c, variant=0):
    """A hauling sledge: two runners, a slatted bed, sacks or a crate lashed on, a tow
    rope out in front (+Y)."""
    name = "Sled %d" % variant

    def build(bm):
        k = len(bm.faces)
        for x in (-0.7, 0.7):
            tube(bm, [(x, -1.6, 0.1), (x, 1.2, 0.1), (x, 1.7, 0.45)], 0.08, n=4)
        for y in (-1.3, -0.5, 0.3, 1.0):
            _box(bm, -0.85, y - 0.15, 0.25, 0.85, y + 0.15, 0.35)
        wood = _faces(bm, k)
        k = len(bm.faces)
        if variant % 2:
            cuboid(bm, (0, -0.2, 0.9), (1.4, 1.6, 1.1))
            load = [(c.lib("barrel_wood"), _faces(bm, k))]
        else:
            for i in range(4):
                blob(bm, ((i % 2 - 0.5) * 0.7, -0.6 + (i // 2) * 0.9, 0.7), 0.45, 1.0, 0.8, 0.7)
            load = [(c.lib("sdp_burlap"), _faces(bm, k))]
        k = len(bm.faces)
        tube(bm, [(0, 1.7, 0.45), (0, 3.4, 0.6)], 0.04, n=3)
        rope = _faces(bm, k)
        return [(c.lib("weathered_timber"), wood + rope)] + load

    return _p(c, name, build)


def snow_pine(c, variant=0):
    """A mountain pine under snow: tiers of drooping boughs, white on top."""
    name = "Snow Pine %d" % variant

    def build(bm):
        h = 7.0 + variant % 4 * 1.8
        k = len(bm.faces)
        _cyl(bm, 0, 0, -0.4, h * 0.35, 0.32, 0.22, n=6)
        bark = _faces(bm, k)
        k = len(bm.faces)
        tiers = 4 + variant % 2
        for i in range(tiers):
            t = i / tiers
            r = (2.8 - 1.8 * t) * (1 + 0.1 * (variant % 3))
            z0 = h * (0.22 + 0.68 * t)
            loft(bm, [ring(bm, (0, 0), r, z0, 8, phase=i * 0.4), ring(bm, (0, 0), r * 0.25, z0 + h * 0.24, 8, phase=i * 0.4)], cap_top=True,
                 cap_bottom=True)
        green = _faces(bm, k)
        return [(c.lib("jungle_bark"), bark), (c.lib("pine_snow"), green)]

    return _p(c, name, build)


def snow_mound(c, variant=0):
    """A drift of snow (against a wall, burying a cart, round a fallen stall)."""
    name = "Snow Mound %d" % variant

    def build(bm):
        for i in range(3):
            blob(bm, (i * 1.6 - 1.6, 0.4 * rnd(i + variant), 0.0), 1.8 - 0.3 * i, 1.4, 1.0, 0.55)
        return [(c.lib("sdp_snowbank"), _faces(bm, 0))]

    return _p(c, name, build)


# ------------------------------------------------------------------ the monastery


def chorten(c, scale=1.0):
    """A white stupa: stepped base, a round body, a gold spire of rings."""
    name = "Chorten %g" % scale

    def build(bm):
        s = scale
        k = len(bm.faces)
        _box(bm, -2.4 * s, -2.4 * s, -0.8, 2.4 * s, 2.4 * s, 1.0 * s)
        _box(bm, -1.9 * s, -1.9 * s, 1.0 * s, 1.9 * s, 1.9 * s, 1.8 * s)
        _box(bm, -1.5 * s, -1.5 * s, 1.8 * s, 1.5 * s, 1.5 * s, 2.4 * s)
        loft(bm, [ring(bm, (0, 0), 1.3 * s, 2.4 * s, 10), ring(bm, (0, 0), 1.6 * s, 3.2 * s, 10), ring(bm, (0, 0), 1.3 * s, 4.3 * s, 10),
                  ring(bm, (0, 0), 0.6 * s, 4.7 * s, 10)])
        white = _faces(bm, k)
        k = len(bm.faces)
        _cyl(bm, 0, 0, 4.7 * s, 7.4 * s, 0.45 * s, 0.12 * s, n=8)
        blob(bm, (0, 0, 7.6 * s), 0.25 * s)
        gold = _faces(bm, k)
        return [(c.lib("white_plaster"), white), (c.lib("isle_gold"), gold)]

    return _p(c, name, build)


def monastery_hall(c, w=14.0, d=10.0, h=8.0, variant=0):
    """A monastery hall: battered whitewashed walls tapering up, a deep red band under
    the flat roof, small dark windows in rows, gold finials on the roof corners."""
    name = "Monastery Hall %g %g %g %d" % (w, d, h, variant)

    def build(bm):
        k = len(bm.faces)
        bot = [bm.verts.new(p) for p in ((-w / 2, -d / 2, -1.0), (w / 2, -d / 2, -1.0), (w / 2, d / 2, -1.0), (-w / 2, d / 2, -1.0))]
        ti = 0.6
        top = [bm.verts.new(p) for p in ((-w / 2 + ti, -d / 2 + ti, h), (w / 2 - ti, -d / 2 + ti, h), (w / 2 - ti, d / 2 - ti, h),
                                          (-w / 2 + ti, d / 2 - ti, h))]
        for i in range(4):
            bm.faces.new((bot[i], bot[(i + 1) % 4], top[(i + 1) % 4], top[i]))
        bm.faces.new(list(reversed(bot)))
        white = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -w / 2 + ti, -d / 2 + ti, h, w / 2 - ti, d / 2 - ti, h + 1.6)
        red = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -w / 2 + ti - 0.3, -d / 2 + ti - 0.3, h + 1.6, w / 2 - ti + 0.3, d / 2 - ti + 0.3, h + 2.0)
        roofk = _faces(bm, k)
        k = len(bm.faces)
        rows = max(1, int(h / 3))
        cols = max(2, int(w / 2.6))
        for j in range(rows):
            for i in range(cols):
                x = -w / 2 + (i + 0.5) * w / cols
                z = 1.6 + j * 2.8
                inset = ti * (z + 1) / (h + 1)
                _box(bm, x - 0.35, d / 2 - inset - 0.02, z, x + 0.35, d / 2 - inset + 0.1, z + 1.1)
        win = _faces(bm, k)
        k = len(bm.faces)
        for x, y in ((-w / 2 + 1, -d / 2 + 1), (w / 2 - 1, -d / 2 + 1), (w / 2 - 1, d / 2 - 1), (-w / 2 + 1, d / 2 - 1)):
            _cyl(bm, x, y, h + 2.0, h + 3.2, 0.35, 0.1, n=6)
        gold = _faces(bm, k)
        return [(c.lib("sdp_whitewash"), white), (c.lib("sdp_redwall"), red), (c.lib("sdp_snowbank"), roofk), (c.lib("lantern_amber" if variant else "lattice_window"), win),
                (c.lib("isle_gold"), gold)]

    return _p(c, name, build)


def flag_pole(c, variant=0):
    """A tall prayer-flag pole: a long vertical strip of flags down one side."""
    name = "Flag Pole %d" % variant
    cloth = []

    def build(bm):
        h = 7.0 + variant % 3
        k = len(bm.faces)
        _cyl(bm, 0, 0, -0.5, h, 0.12, 0.08, n=6)
        wood = _faces(bm, k)
        k = len(bm.faces)
        a = [bm.verts.new(p) for p in ((0.1, 0.02, h - 0.2), (1.0, 0.02, h - 0.2), (1.0, 0.02, h * 0.35), (0.1, 0.02, h * 0.35))]
        bm.faces.new(a)
        bm.faces.new(list(reversed([bm.verts.new(v.co + Vector((0, -0.04, 0))) for v in a])))
        cloth.extend(_faces(bm, k))
        return [(c.lib("weathered_timber"), wood), (c.lib("sdp_flags"), cloth)]

    if name not in c.protos:
        _p(c, name, build)
    return name


def bell_frame(c):
    """A monastery bell under a little roof on two posts."""
    name = "Bell Frame"

    def build(bm):
        k = len(bm.faces)
        for x in (-1.2, 1.2):
            _beam(bm, (x, 0, -0.4), (x, 0, 3.6), 0.22)
        _beam(bm, (-1.5, 0, 3.6), (1.5, 0, 3.6), 0.25)
        red = _faces(bm, k)
        k = len(bm.faces)
        loft(bm, [ring(bm, (0, 0), 0.25, 3.5, 8), ring(bm, (0, 0), 0.55, 2.8, 8), ring(bm, (0, 0), 0.75, 2.1, 8)], cap_top=True, cap_bottom=True)
        gold = _faces(bm, k)
        roofs = roof(bm, 0, 0, 3.85, 3.2, 1.4, 0.9, over=0.4, curl=0.5)
        return [(c.lib("red_lacquer"), red), (c.lib("isle_gold"), gold), (c.lib("sdp_roof"), roofs)]

    return _p(c, name, build)


# ------------------------------------------------------------------ the citadel


def citadel_tower(c, h=26.0, w=12.0):
    """A citadel tower: great red walls, tiers of blazing gold windows, a gold-tiled
    upswept roof."""
    name = "Citadel Tower %g %g" % (h, w)

    def build(bm):
        k = len(bm.faces)
        _box(bm, -w / 2 - 1.5, -w / 2 - 1.5, -2.0, w / 2 + 1.5, w / 2 + 1.5, 2.0)
        stone = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -w / 2, -w / 2, 2.0, w / 2, w / 2, h)
        red = _faces(bm, k)
        k = len(bm.faces)
        for z in range(5, int(h) - 3, 5):
            for s in (-1, 1):
                _box(bm, -w * 0.3, s * (w / 2) - (0.1 if s > 0 else 0.0), z, w * 0.3, s * (w / 2) + (0.1 if s > 0 else 0.0) + (0.0 if s > 0 else -0.1), z + 2.4)
                _box(bm, s * (w / 2) - (0.1 if s > 0 else 0.0), -w * 0.3, z, s * (w / 2) + (0.1 if s > 0 else 0.0) + (0.0 if s > 0 else -0.1), w * 0.3, z + 2.4)
        win = _faces(bm, k)
        roofs = roof(bm, 0, 0, h, w + 1.0, w + 1.0, w * 0.5, over=1.8, curl=0.9)
        k = len(bm.faces)
        _cyl(bm, 0, 0, h + w * 0.5 - 0.2, h + w * 0.5 + 4.0, 0.3, 0.06, n=6)
        blob(bm, (0, 0, h + w * 0.5 + 4.2), 0.45)
        gold = _faces(bm, k)
        return [(c.lib("citadel_stone"), stone), (c.lib("sdp_redwall"), red), (c.lib("sdp_window"), win), (c.lib("roof_gold"), roofs),
                (c.lib("sdp_gold_trim"), gold)]

    return _p(c, name, build)


def citadel_hall(c, w=30.0, d=18.0, h=12.0):
    """The citadel's great hall: a red body full of gold light, two roofs of gold."""
    name = "Citadel Hall %g %g %g" % (w, d, h)

    def build(bm):
        k = len(bm.faces)
        _box(bm, -w / 2 - 3, -d / 2 - 3, -3.0, w / 2 + 3, d / 2 + 3, 2.0)
        stone = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -w / 2, -d / 2, 2.0, w / 2, d / 2, 2.0 + h)
        red = _faces(bm, k)
        k = len(bm.faces)
        n = int(w / 4)
        for i in range(n):
            x = -w / 2 + (i + 0.5) * w / n
            _box(bm, x - 1.2, d / 2, 4.0, x + 1.2, d / 2 + 0.12, 2.0 + h - 2.0)
        win = _faces(bm, k)
        rh = d * 0.35
        roofs = roof(bm, 0, 0, 2.0 + h, w + 2, d + 2, rh * 0.5, over=2.4, curl=0.9)
        k = len(bm.faces)
        _box(bm, -w * 0.32, -d * 0.32, 2.0 + h + rh * 0.35, w * 0.32, d * 0.32, 2.0 + h + rh * 0.35 + h * 0.45)
        red += _faces(bm, k)
        roofs += roof(bm, 0, 0, 2.0 + h + rh * 0.35 + h * 0.45, w * 0.7, d * 0.7, rh * 0.8, over=2.0, curl=0.9)
        return [(c.lib("citadel_stone"), stone), (c.lib("sdp_redwall"), red), (c.lib("sdp_window"), win), (c.lib("roof_gold"), roofs)]

    return _p(c, name, build)


# ------------------------------------------------------------------ ice, ruins, signs


def icicles(c, length=6.0, variant=0):
    """A fringe of icicles along X (hang it under an eave, a bridge, a ledge)."""
    name = "Icicles %g %d" % (length, variant)

    def build(bm):
        n = max(3, int(length / 0.5))
        for i in range(n):
            x = -length / 2 + (i + 0.5) * length / n
            h = 0.6 + 2.2 * rnd(i * 3.1 + variant) ** 2
            res = bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.12 + 0.08 * rnd(i + 9), radius2=0.0, depth=h)
            for v in res["verts"]:
                v.co.z = -v.co.z
                v.co += Vector((x, 0, -h / 2))
        return [(c.lib("sdp_icicle"), _faces(bm, 0))]

    return _p(c, name, build)


def broken_arch(c, span=24.0, h=26.0, variant=0):
    """A ruined stone bridge across a gap (along X): its piers and the stubs of its deck,
    the middle fallen away; icicles hanging from the broken ends."""
    name = "Broken Arch %g %g %d" % (span, h, variant)

    def build(bm):
        k = len(bm.faces)
        for s in (-1, 1):
            _box(bm, s * span / 2 - 2.2, -2.0, -h, s * span / 2 + 2.2, 2.0, 0.0)
            reach = span * (0.22 + 0.1 * rnd(variant + s))
            x0 = s * (span / 2 - 2.2)
            x1 = s * (span / 2 - 2.2 - reach)
            _box(bm, min(x0, x1), -2.3, -1.8, max(x0, x1), 2.3, 0.0)
            _box(bm, min(x0, x1), -2.3, 0.0, max(x0, x1), -1.8, 1.0)
            _box(bm, min(x0, x1), 1.8, 0.0, max(x0, x1), 2.3, 1.0)
            # Its arch's springing, curving out under the stub.
            pts = [(s * (span / 2 - 2.2 - reach * t), 0, -1.8 - 6.0 * (1 - t) ** 2) for t in [j / 5 for j in range(6)]]
            tube(bm, pts, 0.9, n=4)
        stone = _faces(bm, k)
        k = len(bm.faces)
        for s in (-1, 1):
            x = s * (span / 2 - 2.2 - span * (0.22 + 0.1 * rnd(variant + s)))
            for i in range(4):
                hh = 1.0 + 2.5 * rnd(i + s * 5 + variant)
                res = bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.25, radius2=0.0, depth=hh)
                for v in res["verts"]:
                    v.co.z = -v.co.z
                    v.co += Vector((x - s * i * 0.6, -1.5 + i, -1.8 - hh / 2))
        ice = _faces(bm, k)
        return [(c.lib("sdp_aqueduct"), stone), (c.lib("sdp_icicle"), ice)]

    return _p(c, name, build)


def fork_sign(c):
    """A signpost where the road splits: two arrow boards, one pointing each way (+X and
    -X), both red and white: either road is the race."""
    name = "Fork Sign"

    def build(bm):
        k = len(bm.faces)
        _beam(bm, (0, 0, -0.6), (0, 0, 4.6), 0.3)
        wood = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, 0.2, -0.08, 3.4, 4.6, 0.08, 4.4)
        right = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -4.6, -0.08, 2.1, -0.2, 0.08, 3.1)
        left = _faces(bm, k)
        return [(c.lib("weathered_timber"), wood), (c.lib("sdp_chevron"), right + left)]

    return _p(c, name, build)


def guard_post(c):
    """A sentry shelter: a timber box with a snowy roof and an open front (+Y)."""
    name = "Guard Post"

    def build(bm):
        k = len(bm.faces)
        _box(bm, -1.4, -1.4, -0.5, 1.4, -1.2, 2.8)
        _box(bm, -1.4, -1.4, -0.5, -1.2, 1.4, 2.8)
        _box(bm, 1.2, -1.4, -0.5, 1.4, 1.4, 2.8)
        wood = _faces(bm, k)
        roofs = _gable(bm, 2.8, 2.8, 2.8, 1.2, over=0.4)
        return [(c.lib("weathered_timber"), wood), (c.lib("sdp_roof"), roofs)]

    return _p(c, name, build)


def ice_spike(c, variant=0):
    """A blue ice formation rising from a cavern floor or a frozen fall's foot."""
    name = "Ice Spike %d" % variant

    def build(bm):
        for i in range(3):
            h = 3.0 + 4.0 * rnd(i + variant * 5)
            res = bmesh.ops.create_cone(bm, cap_ends=True, segments=5, radius1=0.7 + 0.4 * rnd(i + 3), radius2=0.0, depth=h)
            for v in res["verts"]:
                v.co += Vector((1.2 * math.cos(i * 2.1), 1.2 * math.sin(i * 2.1), h / 2 - 0.4))
        return [(c.lib("glacier_ice"), _faces(bm, 0))]

    return _p(c, name, build)


__all__ = [n for n in dir() if not n.startswith("__")]
_unused = (cuboid, fit_uvs)
