# Dragon Isles' props: the kingdom's buildings (halls, pagodas, pavilions, houses, shops,
# gates, walls), its statues and lanterns, its banners and bunting, blossom trees, pines,
# bamboo, karst pillars, boats and the passage's sealed door. Each builds one mesh (a
# prototype) that every copy shares; origins are at the ground, fronts face +Y.
# All our own designs.
# SPDX-License-Identifier: MIT

import math

from canyon_props import _beam, _cyl
from course_kit import Vector, bmesh, rnd
from props import _faces, blob, cuboid, loft, ring, tube


def _p(c, name, build):
    return c.proto(name, build) and name


def fit_uvs(c, name, faces):
    """Shift each of these faces' UVs so the face starts at (0, 0): plaques and banners
    then show their picture whole instead of wherever the projection happened to fall."""
    me = c.protos[name]
    uv = me.uv_layers.active
    if uv is None:
        return
    for i in faces:
        p = me.polygons[i]
        us = [uv.data[li].uv[0] for li in p.loop_indices]
        vs = [uv.data[li].uv[1] for li in p.loop_indices]
        du, dv = math.floor(min(us) + 1e-4), math.floor(min(vs) + 1e-4)
        du = min(us) if max(us) - min(us) <= 1.001 else du
        dv = min(vs) if max(vs) - min(vs) <= 1.001 else dv
        for li in p.loop_indices:
            uv.data[li].uv = (uv.data[li].uv[0] - du, uv.data[li].uv[1] - dv)


def facing(x, y, tx, ty):
    """The turn that points a prop's front (+Y) from (x, y) toward (tx, ty)."""
    return math.atan2(ty - y, tx - x) - math.pi / 2


# ------------------------------------------------------------------ building parts


def _box(bm, x0, y0, z0, x1, y1, z1):
    cuboid(bm, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0))


def roof(bm, cx, cy, z, w, d, h, over=1.0, curl=0.7):
    """A hipped roof with upswept corners over a w x d body, its eaves at z (the curve
    sags between the eaves and the ridge). Returns the new faces."""
    k0 = len(bm.faces)
    W, D = w / 2 + over, d / 2 + over

    def rect(hw, hd, zz, lift):
        pts = [(hw, hd, lift), (0, hd, 0), (-hw, hd, lift), (-hw, 0, 0), (-hw, -hd, lift), (0, -hd, 0), (hw, -hd, lift), (hw, 0, 0)]
        return [bm.verts.new((cx + px, cy + py, zz + pl)) for px, py, pl in pts]

    long_x = W >= D
    ridge_w = (W - D * 0.85) if long_x else 0.08 * W
    ridge_d = 0.08 * D if long_x else (D - W * 0.85)
    r0 = rect(W, D, z, curl)
    r1 = rect(W * 0.78 + ridge_w * 0.1, D * 0.74 + ridge_d * 0.1, z + h * 0.32, curl * 0.35)
    r2 = rect(max(ridge_w, 0.08 * W), max(ridge_d, 0.08 * D), z + h, 0.0)
    loft(bm, [r0, r1, r2], cap_top=True)
    bm.faces.new(list(reversed(r0)))  # the soffit, seen from below
    return _faces(bm, k0)


def ridge(bm, cx, cy, z, w, d, over=1.0):
    """The gold ridge ornament: a bar along the top and a curl at each end."""
    k0 = len(bm.faces)
    W, D = w / 2 + over, d / 2 + over
    if W >= D:
        L = max(0.4, W - D * 0.85)
        _box(bm, cx - L, cy - 0.18, z - 0.1, cx + L, cy + 0.18, z + 0.35)
        for s in (-1, 1):
            tube(bm, [(cx + s * L, cy, z + 0.2), (cx + s * (L + 0.4), cy, z + 0.75), (cx + s * (L + 0.15), cy, z + 1.2)], [0.22, 0.17, 0.08], n=4)
    else:
        L = max(0.4, D - W * 0.85)
        _box(bm, cx - 0.18, cy - L, z - 0.1, cx + 0.18, cy + L, z + 0.35)
        for s in (-1, 1):
            tube(bm, [(cx, cy + s * L, z + 0.2), (cx, cy + s * (L + 0.4), z + 0.75), (cx, cy + s * (L + 0.15), z + 1.2)], [0.22, 0.17, 0.08], n=4)
    return _faces(bm, k0)


def pillars(bm, xs, ys, z0, z1, r=0.32):
    k0 = len(bm.faces)
    for x in xs:
        for y in ys:
            _cyl(bm, x, y, z0, z1, r, r, n=6)
    return _faces(bm, k0)


def _lantern(bm, x, y, z, s=1.0):
    """A round paper lantern hanging from (x, y, z): returns (cap faces, paper faces)."""
    k0 = len(bm.faces)
    _cyl(bm, x, y, z - 0.12 * s, z, 0.14 * s, 0.14 * s, n=5)
    _cyl(bm, x, y, z - 0.92 * s, z - 0.82 * s, 0.14 * s, 0.14 * s, n=5)
    k1 = len(bm.faces)
    blob(bm, (x, y, z - 0.47 * s), 0.38 * s, 1.0, 1.0, 1.0, subdiv=1)
    return list(range(k0, k1)), _faces(bm, k1)


# ------------------------------------------------------------------ buildings


def hall(c, w=14.0, d=9.0, h=5.0, roof_mat="roof_blue", tiers=1, variant=0):
    """A grand hall: a stone platform with steps, red pillars round a plastered body with
    lattice windows, one or two hipped roofs with gold ridges."""
    name = "Hall %g %g %s %d %d" % (w, d, roof_mat, tiers, variant)

    def build(bm):
        base = 1.0
        stone = []
        k = len(bm.faces)
        _box(bm, -w / 2 - 2.2, -d / 2 - 2.2, -1.0, w / 2 + 2.2, d / 2 + 2.2, base)
        _box(bm, -w * 0.18, d / 2 + 2.2, -1.0, w * 0.18, d / 2 + 3.4, base * 0.5)
        stone += _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -w / 2, -d / 2, base, w / 2, d / 2, base + h)
        plaster = _faces(bm, k)
        k = len(bm.faces)
        for x in (-w * 0.3, w * 0.3):
            _box(bm, x - w * 0.12, d / 2, base + h * 0.25, x + w * 0.12, d / 2 + 0.12, base + h * 0.8)
        lattice = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -w * 0.09, d / 2, base, w * 0.09, d / 2 + 0.15, base + h * 0.78)
        n = max(2, int(w / 3.2))
        xs = [-w / 2 - 0.9 + (w + 1.8) * i / n for i in range(n + 1)]
        red = _faces(bm, k) + pillars(bm, xs, (d / 2 + 0.9, -d / 2 - 0.9), base, base + h + 0.2)
        k = len(bm.faces)
        _box(bm, -w / 2 - 1.3, -d / 2 - 1.3, base + h, w / 2 + 1.3, d / 2 + 1.3, base + h + 0.7)
        red += _faces(bm, k)
        rh = 0.42 * min(w, d) + 1.2
        top = base + h + 0.7
        roofs = []
        gold = []
        if tiers == 2:
            roofs += roof(bm, 0, 0, top, w + 1.4, d + 1.4, rh * 0.45, over=1.6, curl=0.8)
            k = len(bm.faces)
            _box(bm, -w * 0.36, -d * 0.36, top + rh * 0.3, w * 0.36, d * 0.36, top + rh * 0.3 + h * 0.5)
            plaster += _faces(bm, k)
            top2 = top + rh * 0.3 + h * 0.5
            roofs += roof(bm, 0, 0, top2, w * 0.72 + 1.0, d * 0.72 + 1.0, rh * 0.75, over=1.5, curl=0.8)
            gold += ridge(bm, 0, 0, top2 + rh * 0.75, w * 0.72 + 1.0, d * 0.72 + 1.0, 1.5)
        else:
            roofs += roof(bm, 0, 0, top, w + 1.4, d + 1.4, rh, over=1.6, curl=0.9)
            gold += ridge(bm, 0, 0, top + rh, w + 1.4, d + 1.4, 1.6)
        return [(c.lib("stone_base"), stone), (c.lib("white_plaster"), plaster), (c.lib("lattice_window"), lattice), (c.lib("red_lacquer"), red),
                (c.lib(roof_mat), roofs), (c.lib("isle_gold"), gold)]

    return _p(c, name, build)


def pagoda(c, tiers=5, w=7.0, roof_mat="roof_jade"):
    """A tall pagoda: tiers of red-pillared storeys under upswept roofs, a gold spire."""
    name = "Pagoda %d %g %s" % (tiers, w, roof_mat)

    def build(bm):
        stone, plaster, red, roofs, gold, lattice = [], [], [], [], [], []
        k = len(bm.faces)
        _box(bm, -w / 2 - 1.6, -w / 2 - 1.6, -1.0, w / 2 + 1.6, w / 2 + 1.6, 1.0)
        stone += _faces(bm, k)
        z = 1.0
        for i in range(tiers):
            s = w * (1.0 - 0.11 * i)
            hh = 3.4 if i == 0 else 2.4
            k = len(bm.faces)
            _box(bm, -s / 2, -s / 2, z, s / 2, s / 2, z + hh)
            plaster += _faces(bm, k)
            k = len(bm.faces)
            for a in range(4):
                ca, sa = math.cos(a * math.pi / 2), math.sin(a * math.pi / 2)
                cuboid(bm, (ca * (s / 2 + 0.06), sa * (s / 2 + 0.06), z + hh * 0.55), (0.12 if ca else s * 0.5, s * 0.5 if ca else 0.12, hh * 0.55))
            lattice += _faces(bm, k)
            red += pillars(bm, (-s / 2 - 0.2, s / 2 + 0.2), (-s / 2 - 0.2, s / 2 + 0.2), z, z + hh, r=0.25)
            z += hh
            roofs += roof(bm, 0, 0, z, s + 0.6, s + 0.6, 1.3 if i < tiers - 1 else s * 0.55, over=1.3, curl=0.75)
            z += 0.9
        k = len(bm.faces)
        top = z - 0.9 + w * (1.0 - 0.11 * (tiers - 1)) * 0.55
        _cyl(bm, 0, 0, top - 0.2, top + 3.5, 0.18, 0.05, n=6)
        for j in range(4):
            _cyl(bm, 0, 0, top + 0.4 + j * 0.6, top + 0.55 + j * 0.6, 0.45 - j * 0.07, 0.45 - j * 0.07, n=6)
        blob(bm, (0, 0, top + 3.6), 0.35)
        gold += _faces(bm, k)
        return [(c.lib("stone_base"), stone), (c.lib("white_plaster"), plaster), (c.lib("lattice_window"), lattice), (c.lib("red_lacquer"), red),
                (c.lib(roof_mat), roofs), (c.lib("isle_gold"), gold)]

    return _p(c, name, build)


def pavilion(c, w=6.0, roof_mat="roof_jade", rail=True):
    """An open pavilion: a stone platform, four red pillars, low rails, a hipped roof."""
    name = "Pavilion %g %s %d" % (w, roof_mat, rail)

    def build(bm):
        k = len(bm.faces)
        _box(bm, -w / 2 - 0.8, -w / 2 - 0.8, -0.8, w / 2 + 0.8, w / 2 + 0.8, 0.6)
        stone = _faces(bm, k)
        red = pillars(bm, (-w / 2, w / 2), (-w / 2, w / 2), 0.6, 4.2, r=0.26)
        k = len(bm.faces)
        _box(bm, -w / 2 - 0.3, -w / 2 - 0.3, 4.0, w / 2 + 0.3, w / 2 + 0.3, 4.5)
        if rail:
            for x0, y0, x1, y1 in ((-w / 2, -w / 2, w / 2, -w / 2), (-w / 2, -w / 2, -w / 2, w / 2), (w / 2, -w / 2, w / 2, w / 2)):
                _box(bm, min(x0, x1) - 0.08, min(y0, y1) - 0.08, 1.3, max(x0, x1) + 0.08, max(y0, y1) + 0.08, 1.45)
        red += _faces(bm, k)
        roofs = roof(bm, 0, 0, 4.5, w, w, w * 0.45 + 0.6, over=1.3, curl=0.8)
        k = len(bm.faces)
        _cyl(bm, 0, 0, 4.5 + w * 0.45 + 0.4, 4.5 + w * 0.45 + 1.6, 0.25, 0.05, n=6)
        gold = _faces(bm, k)
        return [(c.lib("stone_base"), stone), (c.lib("red_lacquer"), red), (c.lib(roof_mat), roofs), (c.lib("isle_gold"), gold)]

    return _p(c, name, build)


def house(c, variant=0):
    """A village house: a plastered ground floor on a timber frame, lattice windows, a
    hipped tiled roof (blue, jade or terracotta); some have an upper storey."""
    name = "House %d" % variant
    w = (8.0, 10.0, 7.0, 9.0)[variant % 4]
    d = (6.0, 7.0, 6.0, 6.5)[variant % 4]
    two = variant % 3 == 1
    roof_mat = ("roof_blue", "terracotta", "roof_jade", "roof_blue", "terracotta")[variant % 5]

    def build(bm):
        h = 3.6
        k = len(bm.faces)
        _box(bm, -w / 2, -d / 2, -0.8, w / 2, d / 2, 0.4)
        stone = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -w / 2, -d / 2, 0.4, w / 2, d / 2, 0.4 + h)
        plaster = _faces(bm, k)
        k = len(bm.faces)
        for x in (-w / 2, w / 2):
            for y in (-d / 2, d / 2):
                _box(bm, x - 0.22, y - 0.22, 0.4, x + 0.22, y + 0.22, 0.4 + h)
        _box(bm, -w / 2 - 0.2, -d / 2 - 0.2, 0.4 + h - 0.35, w / 2 + 0.2, d / 2 + 0.2, 0.4 + h)
        _box(bm, -0.8, d / 2, 0.4, 0.8, d / 2 + 0.1, 2.7)
        wood = _faces(bm, k)
        k = len(bm.faces)
        for x in (-w * 0.3, w * 0.3):
            _box(bm, x - 0.9, d / 2, 1.5, x + 0.9, d / 2 + 0.08, 3.0)
        lattice = _faces(bm, k)
        z = 0.4 + h
        roofs = []
        if two:
            roofs += roof(bm, 0, 0, z, w, d, 0.9, over=0.9, curl=0.4)
            k = len(bm.faces)
            _box(bm, -w * 0.38, -d * 0.38, z + 0.5, w * 0.38, d * 0.38, z + 3.2)
            plaster += _faces(bm, k)
            k = len(bm.faces)
            _box(bm, -w * 0.2, d * 0.38, z + 1.2, w * 0.2, d * 0.38 + 0.08, z + 2.6)
            lattice += _faces(bm, k)
            z += 3.2
            roofs += roof(bm, 0, 0, z, w * 0.76, d * 0.76, 0.42 * d + 0.6, over=0.9, curl=0.5)
        else:
            roofs += roof(bm, 0, 0, z, w, d, 0.42 * d + 0.8, over=0.9, curl=0.5)
        return [(c.lib("stone_base"), stone), (c.lib("white_plaster"), plaster), (c.lib("wood_wall"), wood), (c.lib("lattice_window"), lattice),
                (c.lib(roof_mat), roofs)]

    return _p(c, name, build)


def shop(c, variant=0):
    """A market shop: open-fronted under an awning, its counter laid out with wares,
    lanterns hanging from the eaves."""
    name = "Shop %d" % variant
    w, d = (8.0, 6.0) if variant % 2 == 0 else (6.5, 5.5)
    awning = ("awning_red", "awning_teal", "sail_red", "awning_sun")[variant % 4]
    roof_mat = ("roof_blue", "terracotta", "roof_jade")[variant % 3]

    def build(bm):
        h = 3.8
        k = len(bm.faces)
        _box(bm, -w / 2, -d / 2, -0.8, w / 2, d / 2, 0.3)
        stone = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -w / 2, -d / 2, 0.3, w / 2, -d / 2 + 0.4, 0.3 + h)
        _box(bm, -w / 2, -d / 2, 0.3, -w / 2 + 0.4, d / 2, 0.3 + h)
        _box(bm, w / 2 - 0.4, -d / 2, 0.3, w / 2, d / 2, 0.3 + h)
        plaster = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -w / 2, -d / 2, 0.3 + h - 0.4, w / 2, d / 2, 0.3 + h)
        for x in (-w / 2 + 0.2, w / 2 - 0.2):
            _box(bm, x - 0.18, d / 2 - 0.2, 0.3, x + 0.18, d / 2 + 0.16, 0.3 + h)
        _box(bm, -w / 2 + 0.5, d / 2 - 1.3, 0.3, w / 2 - 0.5, d / 2 - 0.4, 1.3)
        wood = _faces(bm, k)
        k = len(bm.faces)
        for i in range(int(w / 1.3)):
            x = -w / 2 + 1.0 + i * 1.3
            cuboid(bm, (x, d / 2 - 0.85, 1.5), (0.9, 0.7, 0.4))
            blob(bm, (x, d / 2 - 0.85, 1.75), 0.32, 1.2, 0.9, 0.6)
        wares = _faces(bm, k)
        # The awning: sloping out from the eaves over the counter.
        k = len(bm.faces)
        a = [bm.verts.new(p) for p in ((-w / 2 - 0.2, d / 2, 3.4), (w / 2 + 0.2, d / 2, 3.4), (w / 2 + 0.2, d / 2 + 2.0, 2.7), (-w / 2 - 0.2, d / 2 + 2.0, 2.7))]
        bm.faces.new(a)
        bm.faces.new(list(reversed([bm.verts.new(v.co + Vector((0, 0, -0.04))) for v in a])))
        cloth = _faces(bm, k)
        roofs = roof(bm, 0, 0, 0.3 + h, w, d, 0.42 * d + 0.6, over=0.8, curl=0.45)
        caps, paper = [], []
        for x in (-w / 2 + 0.4, w / 2 - 0.4):
            cp, pp = _lantern(bm, x, d / 2 + 1.9, 2.7, 0.8)
            caps += cp
            paper += pp
        return [(c.lib("stone_base"), stone), (c.lib("white_plaster"), plaster), (c.lib("wood_wall"), wood), (c.lib("fruit"), wares),
                (c.lib(awning), cloth), (c.lib(roof_mat), roofs), (c.lib("timber_beam"), caps), (c.lib("lantern_red"), paper)]

    return _p(c, name, build)


def stall(c, variant=0):
    """A market stall: a trestle of wares under a cloth canopy on four poles."""
    name = "Stall %d" % variant
    cloth_mat = ("awning_red", "awning_teal", "awning_sun", "sail_red")[variant % 4]

    def build(bm):
        k = len(bm.faces)
        for x in (-1.6, 1.6):
            for y in (-1.0, 1.0):
                _beam(bm, (x, y, -0.2), (x, y, 2.7 if y < 0 else 2.4), 0.12)
        _box(bm, -1.7, -0.9, 0.85, 1.7, 0.9, 1.0)
        wood = _faces(bm, k)
        k = len(bm.faces)
        for i in range(5):
            blob(bm, (-1.3 + i * 0.65, 0.1 * (i % 2), 1.15), 0.3, 1.0, 1.0, 0.55)
        wares = _faces(bm, k)
        k = len(bm.faces)
        a = [bm.verts.new(p) for p in ((-1.9, -1.2, 2.75), (1.9, -1.2, 2.75), (1.9, 1.3, 2.35), (-1.9, 1.3, 2.35))]
        bm.faces.new(a)
        bm.faces.new(list(reversed([bm.verts.new(v.co + Vector((0, 0, -0.04))) for v in a])))
        cloth = _faces(bm, k)
        return [(c.lib("timber_beam"), wood), (c.lib("fruit"), wares), (c.lib(cloth_mat), cloth)]

    return _p(c, name, build)


def wall(c, length=12.0, h=4.0, roof_mat="roof_blue"):
    """A plastered wall with a little tiled roof along its top (along X)."""
    name = "Wall %g %g %s" % (length, h, roof_mat)

    def build(bm):
        k = len(bm.faces)
        _box(bm, -length / 2, -0.5, -1.0, length / 2, 0.5, h)
        plaster = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -length / 2, -0.62, -1.0, length / 2, 0.62, 0.7)
        stone = _faces(bm, k)
        roofs = roof(bm, 0, 0, h, length - 1.2, 1.0, 0.7, over=0.6, curl=0.0)
        return [(c.lib("white_plaster"), plaster), (c.lib("stone_base"), stone), (c.lib(roof_mat), roofs)]

    return _p(c, name, build)


def gate(c, span=24.0, height=10.0, roof_mat="roof_blue", grand=True):
    """A ceremonial gate over the road: red pillars on stone feet, lintels, little roofs
    with gold ridges along the top and the royal emblem in the middle (the road runs
    through along Y)."""
    name = "Gate %g %g %s %d" % (span, height, roof_mat, grand)
    plaque = []

    def build(bm):
        half = span / 2
        xs = (-half - 1.0, half + 1.0) if not grand else (-half - 1.0, half + 1.0, -half - 5.5, half + 5.5)
        stone, red, roofs, gold = [], [], [], []
        for i, x in enumerate(xs):
            hh = height if i < 2 else height * 0.68
            k = len(bm.faces)
            _box(bm, x - 1.0, -1.0, -1.0, x + 1.0, 1.0, 1.4)
            stone += _faces(bm, k)
            red += pillars(bm, (x,), (0.0,), 1.4, hh + 0.3, r=0.65)
        k = len(bm.faces)
        _box(bm, -half - 2.2, -0.55, height - 1.6, half + 2.2, 0.55, height - 0.6)
        _box(bm, -half - 1.6, -0.45, height - 3.4, half + 1.6, 0.45, height - 2.6)
        if grand:
            for s in (-1, 1):
                _box(bm, s * (half + 0.3), -0.45, height * 0.68 - 1.3, s * (half + 6.6), 0.45, height * 0.68 - 0.6)
        red += _faces(bm, k)
        roofs += roof(bm, 0, 0, height - 0.6, span + 3.4, 1.2, 2.2, over=1.4, curl=0.8)
        gold += ridge(bm, 0, 0, height + 1.6, span + 3.4, 1.2, 1.4)
        if grand:
            for s in (-1, 1):
                roofs += roof(bm, s * (half + 3.5), 0, height * 0.68 - 0.6, 6.0, 1.0, 1.4, over=1.0, curl=0.6)
        k = len(bm.faces)
        _box(bm, -1.5, -0.62, height - 4.6, 1.5, 0.62, height - 1.6)
        plaque.extend(_faces(bm, k))
        return [(c.lib("stone_base"), stone), (c.lib("red_lacquer"), red), (c.lib(roof_mat), roofs), (c.lib("isle_gold"), gold),
                (c.lib("emblem_plaque"), plaque)]

    if name not in c.protos:
        _p(c, name, build)
        fit_uvs(c, name, plaque)
    return name


def gatehouse(c, w=10.0):
    """A royal gate in a wall, its doors shut: red leaves studded with gold, a roof over
    and the emblem above (side streets and the palace)."""
    name = "Closed Gate %g" % w
    plaque = []

    def build(bm):
        k = len(bm.faces)
        _box(bm, -w / 2 - 3, -1.2, -1.0, -w / 2 + 0.2, 1.2, 7.0)
        _box(bm, w / 2 - 0.2, -1.2, -1.0, w / 2 + 3, 1.2, 7.0)
        _box(bm, -w / 2, -1.0, 5.6, w / 2, 1.0, 7.0)
        plaster = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -w / 2 + 0.2, 0.3, 0.0, -0.05, 0.6, 5.6)
        _box(bm, 0.05, 0.3, 0.0, w / 2 - 0.2, 0.6, 5.6)
        red = _faces(bm, k)
        k = len(bm.faces)
        for side in (-1, 1):
            for i in range(3):
                for j in range(5):
                    cuboid(bm, (side * (0.8 + i * (w / 2 - 1.4) / 2.0), 0.66, 0.9 + j * 1.0), (0.18, 0.12, 0.18))
        gold = _faces(bm, k)
        roofs = roof(bm, 0, 0, 7.0, w + 6.0, 2.4, 2.0, over=1.2, curl=0.8)
        gold += ridge(bm, 0, 0, 9.0, w + 6.0, 2.4, 1.2)
        k = len(bm.faces)
        _box(bm, -1.2, 1.0, 5.65, 1.2, 1.1, 6.95)
        plaque.extend(_faces(bm, k))
        return [(c.lib("white_plaster"), plaster), (c.lib("red_lacquer"), red), (c.lib("isle_gold"), gold), (c.lib("roof_blue"), roofs),
                (c.lib("emblem_plaque"), plaque)]

    if name not in c.protos:
        _p(c, name, build)
        fit_uvs(c, name, plaque)
    return name


def dark_arch(c):
    """A doorway in a wall, opening onto a dark corridor (just a glimpse)."""
    name = "Dark Arch"

    def build(bm):
        k = len(bm.faces)
        _box(bm, -5, -1.0, -1.0, -1.6, 1.0, 6.0)
        _box(bm, 1.6, -1.0, -1.0, 5, 1.0, 6.0)
        _box(bm, -1.6, -1.0, 4.2, 1.6, 1.0, 6.0)
        stone = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -1.6, -1.0, -0.2, 1.6, 0.6, 4.2)
        dark = _faces(bm, k)
        roofs = roof(bm, 0, 0, 6.0, 10.0, 2.0, 1.2, over=0.6, curl=0.5)
        return [(c.lib("masonry"), stone), (c.lib("dark_corridor"), dark), (c.lib("roof_blue"), roofs)]

    return _p(c, name, build)


def sealed_door(c):
    """The Ancient Dragon Passage's sealed door: a great round stone set in a carved
    frame, a faint ring of old glyphs round it."""
    name = "Sealed Door"

    def build(bm):
        k = len(bm.faces)
        _box(bm, -5.0, -0.6, -1.0, 5.0, 0.6, 9.0)
        frame = _faces(bm, k)
        k = len(bm.faces)
        rg = [bm.verts.new((3.6 * math.cos(a * math.tau / 16), 0.62, 4.2 + 3.6 * math.sin(a * math.tau / 16))) for a in range(16)]
        rg2 = [bm.verts.new((3.0 * math.cos(a * math.tau / 16), 0.75, 4.2 + 3.0 * math.sin(a * math.tau / 16))) for a in range(16)]
        for i in range(16):
            bm.faces.new((rg[i], rg[(i + 1) % 16], rg2[(i + 1) % 16], rg2[i]))
        glyph = _faces(bm, k)
        k = len(bm.faces)
        disc = [bm.verts.new((3.0 * math.cos(a * math.tau / 16), 0.75, 4.2 + 3.0 * math.sin(a * math.tau / 16))) for a in range(16)]
        bm.faces.new(list(reversed(disc)))
        cuboid(bm, (0, 0.85, 4.2), (1.4, 0.2, 1.4), rot=0.0)
        door = _faces(bm, k)
        return [(c.lib("passage_stone"), frame), (c.lib("glyph_teal"), glyph), (c.lib("carved_relief"), door)]

    return _p(c, name, build)


# ------------------------------------------------------------------ statues and lanterns


def dragon_statue(c, mat="jade_stone"):
    """A dragon statue: a long body coiled up from its plinth, rearing to look out over
    the road (its front), gold horns and mane."""
    name = "Dragon Statue " + mat

    def build(bm):
        k = len(bm.faces)
        _box(bm, -2.2, -2.2, -1.0, 2.2, 2.2, 1.8)
        _box(bm, -2.5, -2.5, -1.0, 2.5, 2.5, 0.5)
        plinth = _faces(bm, k)
        k = len(bm.faces)
        pts = []
        radii = []
        for i in range(14):
            t = i / 13
            a = -1.2 + t * 4.4
            r = 1.35 * (1 - 0.55 * t)
            pts.append((r * math.cos(a), r * math.sin(a) - 0.2, 2.2 + 3.0 * t ** 1.4))
            radii.append(0.55 - 0.18 * t)
        pts += [(0.0, 0.4, 6.0), (0.0, 1.0, 6.6)]
        radii += [0.42, 0.38]
        tube(bm, pts, radii, n=6)
        # The head: a long muzzle, the jaw open a little.
        cuboid(bm, (0, 1.55, 6.75), (0.9, 1.3, 0.7))
        cuboid(bm, (0, 2.35, 6.6), (0.7, 0.9, 0.38))
        cuboid(bm, (0, 2.2, 6.25), (0.6, 0.9, 0.18), tilt=(0.25, 0.0))
        body = _faces(bm, k)
        k = len(bm.faces)
        for s in (-1, 1):
            tube(bm, [(s * 0.3, 1.2, 7.05), (s * 0.55, 0.6, 7.6), (s * 0.6, 0.0, 8.1)], [0.12, 0.09, 0.04], n=4)
            tube(bm, [(s * 0.45, 2.7, 6.55), (s * 1.0, 2.9, 6.3), (s * 1.4, 2.6, 5.9)], [0.05, 0.04, 0.02], n=3)
            blob(bm, (s * 0.38, 1.75, 6.95), 0.14)
        for i in range(5):
            p = pts[8 + i]
            cuboid(bm, (p[0], p[1], p[2] + radii[8 + i] + 0.15), (0.12, 0.4, 0.35))
        tube(bm, [pts[0], (1.6, -1.6, 1.9), (2.1, -2.0, 2.1)], [0.4, 0.25, 0.06], n=5)
        gold = _faces(bm, k)
        return [(c.lib("stone_base"), plinth), (c.lib(mat), body), (c.lib("isle_gold"), gold)]

    return _p(c, name, build)


def guardian_statue(c):
    """A stone guardian: a robed warrior on a plinth, both hands on a tall halberd,
    looking straight ahead (its front)."""
    name = "Guardian Statue"

    def build(bm):
        k = len(bm.faces)
        _box(bm, -1.2, -1.2, -1.0, 1.2, 1.2, 1.2)
        plinth = _faces(bm, k)
        k = len(bm.faces)
        loft(bm, [ring(bm, (0, 0), 0.9, 1.2, 6), ring(bm, (0, 0), 0.75, 2.6, 6), ring(bm, (0, 0), 0.62, 3.8, 6), ring(bm, (0, 0), 0.4, 4.2, 6)])
        cuboid(bm, (0, 0, 3.6), (1.7, 0.8, 0.7))
        blob(bm, (0, 0.05, 4.6), 0.38, 1.0, 1.0, 1.15)
        cuboid(bm, (0, 0.0, 5.05), (0.95, 0.95, 0.22))
        _cyl(bm, 0, 0, 5.1, 5.6, 0.32, 0.08, n=6)
        for s in (-1, 1):
            tube(bm, [(s * 0.8, 0.0, 3.6), (s * 0.55, 0.45, 3.0), (s * 0.12, 0.6, 3.2)], [0.18, 0.16, 0.15], n=5)
        tube(bm, [(0.05, 0.62, 1.3), (0.05, 0.62, 6.2)], 0.06, n=4)
        cuboid(bm, (0.05, 0.62, 6.35), (0.08, 0.6, 0.5))
        body = _faces(bm, k)
        return [(c.lib("stone_base"), plinth), (c.lib("masonry"), body)]

    return _p(c, name, build)


def stone_lantern(c):
    """A garden lantern of stone: a footed post, a lit box, a little roof."""
    name = "Stone Lantern"

    def build(bm):
        k = len(bm.faces)
        _cyl(bm, 0, 0, -0.3, 0.3, 0.6, 0.55, n=6)
        _cyl(bm, 0, 0, 0.3, 1.5, 0.22, 0.22, n=6)
        _cyl(bm, 0, 0, 1.5, 1.7, 0.55, 0.55, n=6)
        _cyl(bm, 0, 0, 2.4, 2.55, 0.5, 0.75, n=6, phase=math.pi / 6)
        _cyl(bm, 0, 0, 2.55, 3.0, 0.75, 0.08, n=6, phase=math.pi / 6)
        blob(bm, (0, 0, 3.05), 0.13)
        stone = _faces(bm, k)
        k = len(bm.faces)
        _cyl(bm, 0, 0, 1.7, 2.4, 0.4, 0.4, n=6)
        glow = _faces(bm, k)
        return [(c.lib("stone_base"), stone), (c.lib("lantern_amber"), glow)]

    return _p(c, name, build)


STONE_LANTERN_LIGHT = (0.0, 0.0, 2.05)


def lantern_post(c):
    """A red post with a curved arm and a paper lantern (lantern 1.1 m out along +X)."""
    name = "Lantern Post"

    def build(bm):
        k = len(bm.faces)
        _cyl(bm, 0, 0, -0.4, 4.6, 0.16, 0.13, n=6)
        tube(bm, [(0, 0, 4.2), (0.6, 0, 4.6), (1.2, 0, 4.4)], 0.07, n=4)
        red = _faces(bm, k)
        k = len(bm.faces)
        _cyl(bm, 0, 0, 4.6, 5.0, 0.22, 0.04, n=6)
        gold = _faces(bm, k)
        caps, paper = _lantern(bm, 1.15, 0, 4.4, 1.0)
        return [(c.lib("red_lacquer"), red), (c.lib("isle_gold"), gold), (c.lib("timber_beam"), caps), (c.lib("lantern_red"), paper)]

    return _p(c, name, build)


LANTERN_POST_LIGHT = (1.15, 0.0, 3.9)


def lantern_string(c, span=20.0, sag=1.8, count=7):
    """Paper lanterns strung on a rope from (0, 0, 0) to (span, 0, 0)."""
    name = "Lantern String %g" % span

    def build(bm):
        pts = []
        for i in range(13):
            t = i / 12
            pts.append((span * t, 0, -sag * 4 * t * (1 - t)))
        k = len(bm.faces)
        tube(bm, pts, 0.04, n=3)
        rope = _faces(bm, k)
        caps, paper = [], []
        for i in range(count):
            t = (i + 1) / (count + 1)
            cp, pp = _lantern(bm, span * t, 0, -sag * 4 * t * (1 - t) - 0.05, 0.75)
            caps += cp
            paper += pp
        return [(c.lib("timber_beam"), rope + caps), (c.lib("lantern_red"), paper)]

    return _p(c, name, build)


def bunting_string(c, span=20.0, sag=1.4):
    """Little festival flags on a line from (0, 0, 0) to (span, 0, 0)."""
    name = "Bunting %g" % span

    def build(bm):
        n = int(span / 0.9)
        k = len(bm.faces)
        for i in range(n):
            t0, t1 = i / n, (i + 0.8) / n
            z0 = -sag * 4 * t0 * (1 - t0)
            z1 = -sag * 4 * t1 * (1 - t1)
            tm = (t0 + t1) / 2
            a = bm.verts.new((span * t0, 0, z0))
            b = bm.verts.new((span * t1, 0, z1))
            m = bm.verts.new((span * tm, 0, (z0 + z1) / 2 - 0.7))
            bm.faces.new((a, b, m))
            a2, b2, m2 = (bm.verts.new(v.co.copy()) for v in (a, b, m))
            bm.faces.new((b2, a2, m2))
        return [(c.lib("isle_bunting"), _faces(bm, k))]

    return _p(c, name, build)


def banner_pole(c, mat="banner_royal"):
    """A tall red pole with a gold finial and a long hanging banner."""
    name = "Banner Pole " + mat
    cloth = []

    def build(bm):
        k = len(bm.faces)
        _cyl(bm, 0, 0, -0.5, 8.6, 0.13, 0.1, n=6)
        _beam(bm, (-0.1, 0, 8.1), (1.9, 0, 8.1), 0.1)
        red = _faces(bm, k)
        k = len(bm.faces)
        blob(bm, (0, 0, 8.75), 0.22)
        gold = _faces(bm, k)
        k = len(bm.faces)
        a = [bm.verts.new(p) for p in ((0.2, 0.05, 8.0), (1.7, 0.05, 8.0), (1.7, 0.05, 3.5), (0.2, 0.05, 3.5))]
        bm.faces.new(a)
        b = [bm.verts.new(p) for p in ((0.2, -0.05, 8.0), (1.7, -0.05, 8.0), (1.7, -0.05, 3.5), (0.2, -0.05, 3.5))]
        bm.faces.new(list(reversed(b)))
        cloth.extend(_faces(bm, k))
        return [(c.lib("red_lacquer"), red), (c.lib("isle_gold"), gold), (c.lib(mat), cloth)]

    if name not in c.protos:
        _p(c, name, build)
        fit_uvs(c, name, cloth)
    return name


def emblem_plaque(c):
    """The royal emblem on a red board with a gold frame (on walls, posts, the passage)."""
    name = "Emblem Plaque"
    face = []

    def build(bm):
        k = len(bm.faces)
        _box(bm, -1.7, -0.2, -1.7, 1.7, 0.0, 1.7)
        frame = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -1.5, 0.0, -1.5, 1.5, 0.08, 1.5)
        face.extend(_faces(bm, k))
        return [(c.lib("isle_gold"), frame), (c.lib("emblem_plaque"), face)]

    if name not in c.protos:
        _p(c, name, build)
        fit_uvs(c, name, face)
    return name


def drum_stage(c):
    """The festival square's stage: a red platform with a great drum on a stand and two
    smaller ones, a canopy over."""
    name = "Drum Stage"

    def build(bm):
        k = len(bm.faces)
        _box(bm, -5, -3.5, -0.8, 5, 3.5, 1.2)
        red = _faces(bm, k) + pillars(bm, (-4.6, 4.6), (-3.1, 3.1), 1.2, 5.6, 0.22)
        k = len(bm.faces)
        loft(bm, [ring(bm, (0, 0), 1.3, 0, 10), ring(bm, (0, 0), 1.5, 0.8, 10), ring(bm, (0, 0), 1.3, 1.6, 10)], cap_top=True, cap_bottom=True)
        drum = _faces(bm, k)
        for v in bm.verts[-30:]:
            pass
        # Turn the big drum on its side, on a stand.
        verts = set()
        for i in drum:
            for v in bm.faces[i].verts:
                verts.add(v)
        for v in verts:
            x, y, z = v.co
            v.co = Vector((x, z - 0.8, y + 3.4))
        k = len(bm.faces)
        _beam(bm, (-1.6, 0, 1.2), (-1.6, 0, 3.4), 0.18)
        _beam(bm, (1.6, 0, 1.2), (1.6, 0, 3.4), 0.18)
        wood = _faces(bm, k)
        k = len(bm.faces)
        for x in (-3.2, 3.2):
            _cyl(bm, x, 0.5, 1.2, 2.2, 0.55, 0.6, n=8)
        drum += _faces(bm, k)
        roofs = roof(bm, 0, 0, 5.6, 10.0, 7.0, 2.6, over=1.0, curl=0.7)
        return [(c.lib("red_lacquer"), red), (c.lib("barrel_wood"), drum), (c.lib("timber_beam"), wood), (c.lib("roof_jade"), roofs)]

    return _p(c, name, build)


# ------------------------------------------------------------------ plants


def blossom_tree(c, variant=0):
    """A cherry-blossom tree: a crooked trunk splitting into branches, clouds of pink."""
    name = "Blossom Tree %d" % variant

    def build(bm):
        h = 4.5 + variant % 3 * 0.8
        k = len(bm.faces)
        tube(bm, [(0, 0, -0.3), (0.3, 0.1, 1.6), (0.1, 0.3, h * 0.6)], [0.38, 0.3, 0.24], n=6)
        tips = []
        for i in range(3 + variant % 2):
            a = i * math.tau / (3 + variant % 2) + variant
            r = 2.0 + rnd(variant * 7 + i) * 1.2
            tip = (math.cos(a) * r, math.sin(a) * r, h + rnd(variant * 3 + i) * 1.3)
            tube(bm, [(0.1, 0.3, h * 0.55), (math.cos(a) * r * 0.5, math.sin(a) * r * 0.5, h * 0.85), tip], [0.2, 0.14, 0.08], n=5)
            tips.append(tip)
        bark = _faces(bm, k)
        k = len(bm.faces)
        for i, (x, y, z) in enumerate(tips):
            blob(bm, (x, y, z + 0.4), 1.6 + rnd(i + variant) * 0.5, 1.2, 1.2, 0.8)
        blob(bm, (0, 0, h + 1.2), 2.2, 1.0, 1.0, 0.75)
        bloom = _faces(bm, k)
        return [(c.lib("jungle_bark"), bark), (c.lib("blossom_pink"), bloom)]

    return _p(c, name, build)


def pine(c, variant=0):
    """A windswept pine: a leaning trunk, its needles in flat pads at the branch ends."""
    name = "Pine %d" % variant

    def build(bm):
        h = 6.0 + variant % 3 * 1.5
        lean = (variant % 2 * 2 - 1) * 1.2
        k = len(bm.faces)
        tube(bm, [(0, 0, -0.3), (lean * 0.3, 0, h * 0.4), (lean, 0.3, h * 0.8), (lean * 0.8, 0.2, h)], [0.4, 0.32, 0.22, 0.12], n=6)
        pads = []
        for i in range(4):
            t = 0.45 + i * 0.17
            a = i * 2.3 + variant
            r = 2.6 - i * 0.4
            base = (lean * t, 0.2 * t, h * t)
            tip = (base[0] + math.cos(a) * r, base[1] + math.sin(a) * r, base[2] + 0.4)
            tube(bm, [base, tip], [0.14, 0.07], n=4)
            pads.append(tip)
        pads.append((lean * 0.8, 0.2, h + 0.3))
        bark = _faces(bm, k)
        k = len(bm.faces)
        for i, (x, y, z) in enumerate(pads):
            blob(bm, (x, y, z), 1.5 - i * 0.12, 1.3, 1.3, 0.38)
        green = _faces(bm, k)
        return [(c.lib("jungle_bark"), bark), (c.lib("pine_bright"), green)]

    return _p(c, name, build)


def bamboo(c, variant=0):
    """A clump of bamboo: tall green canes, leaves at their tops."""
    name = "Bamboo %d" % variant

    def build(bm):
        k = len(bm.faces)
        tops = []
        for i in range(7):
            a = rnd(variant * 11 + i) * math.tau
            r = rnd(variant * 5 + i * 3) * 1.1
            x, y = math.cos(a) * r, math.sin(a) * r
            h = 6.5 + rnd(i + variant) * 3.5
            lx, ly = math.cos(a) * 0.9, math.sin(a) * 0.9
            tube(bm, [(x, y, -0.3), (x + lx * 0.3, y + ly * 0.3, h * 0.5), (x + lx, y + ly, h)], [0.1, 0.09, 0.05], n=4)
            tops.append((x + lx, y + ly, h))
        canes = _faces(bm, k)
        k = len(bm.faces)
        for x, y, z in tops:
            blob(bm, (x, y, z - 0.8), 0.9, 1.0, 1.0, 1.6)
        leaves = _faces(bm, k)
        return [(c.lib("bamboo"), canes), (c.lib("leaf_bright"), leaves)]

    return _p(c, name, build)


def hedge_box(c, length=4.0):
    name = "Hedge %g" % length

    def build(bm):
        cuboid(bm, (0, 0, 0.5), (length, 1.0, 1.4))
        return [(c.lib("hedge"), _faces(bm, 0))]

    return _p(c, name, build)


def karst(c, variant=0):
    """A karst tower: a tall lumpy limestone pillar, wider at the waist than the foot,
    moss and a pine or two on its rounded top. 40 m tall (scale it)."""
    name = "Karst %d" % variant

    def build(bm):
        n = 10
        rings = []
        prof = [(-6.0, 1.0), (0.0, 0.9), (6.0, 0.82), (14.0, 0.86), (24.0, 0.78), (32.0, 0.7), (37.0, 0.55), (40.0, 0.25)]
        k = len(bm.faces)
        for j, (z, s) in enumerate(prof):
            rg = []
            for i in range(n):
                a = i * math.tau / n
                r = 10.0 * s * (1 + 0.16 * math.sin(3 * a + variant * 1.3 + j) + 0.12 * (rnd(variant * 31 + i * 7 + j) - 0.5))
                rg.append(bm.verts.new((r * math.cos(a), r * 0.85 * math.sin(a), z + 1.2 * (rnd(i + j * 5 + variant) - 0.5))))
            rings.append(rg)
        loft(bm, rings, cap_top=True)
        rock = _faces(bm, k)
        top = [f for f in rock if bm.faces[f].normal.z > 0.55] if False else []
        k = len(bm.faces)
        for i in range(2):
            a = rnd(variant + i * 9) * math.tau
            blob(bm, (math.cos(a) * 2.0, math.sin(a) * 2.0, 39.5 + i), 2.4, 1.2, 1.2, 0.45)
        moss = _faces(bm, k)
        return [(c.lib("limestone"), rock), (c.lib("limestone_moss"), moss)]

    me = _p(c, name, build)
    return me


# ------------------------------------------------------------------ boats


def junk(c, variant=0):
    """A junk: a broad wooden hull with a raised stern, a little deck house, two or three
    masts of red battened sails (the bow points +Y)."""
    name = "Junk %d" % variant

    def build(bm):
        L = 16.0 if variant % 2 == 0 else 12.0
        B = 4.4 if variant % 2 == 0 else 3.6
        k = len(bm.faces)
        rings = []
        for j, (y, s, zt, zb) in enumerate(((-L / 2, 0.75, 3.4, 0.4), (-L / 4, 1.0, 2.0, -0.9), (L / 6, 1.0, 1.9, -0.9), (L / 2 - 1.0, 0.5, 2.6, 0.0), (L / 2, 0.1, 2.9, 1.2))):
            rg = [bm.verts.new((-B / 2 * s, y, zt)), bm.verts.new((-B / 2 * s * 0.85, y, zb * 0.5 + zt * 0.1)), bm.verts.new((0, y, zb)),
                  bm.verts.new((B / 2 * s * 0.85, y, zb * 0.5 + zt * 0.1)), bm.verts.new((B / 2 * s, y, zt))]
            rings.append(rg)
        for a, b in zip(rings, rings[1:]):
            for i in range(4):
                bm.faces.new((a[i], b[i], b[i + 1], a[i + 1]))
        bm.faces.new([v for v in rings[0]])
        hull = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -B / 2 + 0.3, -L / 2 + 0.3, 1.6, B / 2 - 0.3, L / 2 - 1.2, 1.95)
        deck = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -B * 0.35, -L / 2 + 0.6, 1.9, B * 0.35, -L / 2 + 3.6, 3.9)
        house_f = _faces(bm, k)
        roofs = roof(bm, 0, -L / 2 + 2.1, 3.9, B * 0.7, 3.0, 0.8, over=0.4, curl=0.3)
        masts = (L * 0.18, -L * 0.12) + ((L * 0.36,) if variant % 2 == 0 else ())
        k = len(bm.faces)
        for y in masts:
            _cyl(bm, 0, y, 1.9, 13.0 if y == masts[0] else 10.0, 0.16, 0.1, n=5)
        wood = _faces(bm, k)
        k = len(bm.faces)
        for i, y in enumerate(masts):
            top = (12.4 if i == 0 else 9.5)
            wd = (4.6 if i == 0 else 3.6)
            pts = [(0.15, y - 0.3, top), (0.15, y + wd * 0.9, top - 0.6), (0.15, y + wd, 3.6), (0.15, y - 0.4, 3.4)]
            a = [bm.verts.new(p) for p in pts]
            bm.faces.new(a)
            b = [bm.verts.new((-p[0], p[1], p[2])) for p in pts]
            bm.faces.new(list(reversed(b)))
        sails = _faces(bm, k)
        return [(c.lib("ship_hull"), hull), (c.lib("plank_deck"), deck), (c.lib("wood_wall"), house_f), (c.lib("roof_jade"), roofs),
                (c.lib("timber_beam"), wood), (c.lib("sail_red"), sails)]

    return _p(c, name, build)


def sampan(c, variant=0):
    """A little fishing boat with an arched canopy (the bow points +Y)."""
    name = "Sampan %d" % variant

    def build(bm):
        L, B = 7.0, 1.8
        k = len(bm.faces)
        rings = []
        for y, s, zt in ((-L / 2, 0.4, 1.0), (-L / 4, 1.0, 0.8), (L / 4, 1.0, 0.8), (L / 2, 0.15, 1.2)):
            rings.append([bm.verts.new((-B / 2 * s, y, zt)), bm.verts.new((0, y, -0.3)), bm.verts.new((B / 2 * s, y, zt))])
        for a, b in zip(rings, rings[1:]):
            for i in range(2):
                bm.faces.new((a[i], b[i], b[i + 1], a[i + 1]))
        hull = _faces(bm, k)
        k = len(bm.faces)
        rows = []
        for y in (-1.6, 1.0):
            rows.append([bm.verts.new((math.cos(a) * 0.95, y, 0.7 + math.sin(a) * 1.2)) for a in [i * math.pi / 6 for i in range(7)]])
        back = [[bm.verts.new(v.co.copy()) for v in r] for r in rows]
        for i in range(6):
            bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
            bm.faces.new((back[1][i], back[1][i + 1], back[0][i + 1], back[0][i]))
        canopy = _faces(bm, k)
        return [(c.lib("ship_hull"), hull), (c.lib("thatch"), canopy)]

    return _p(c, name, build)


def dragon_boat(c):
    """A long festival boat, its prow a carved dragon head, its tail curled at the stern
    (the bow points +Y)."""
    name = "Dragon Boat"

    def build(bm):
        L = 18.0
        k = len(bm.faces)
        rings = []
        for y, s, zt in ((-L / 2, 0.3, 1.2), (-L / 3, 1.0, 0.7), (L / 3, 1.0, 0.7), (L / 2, 0.3, 1.0)):
            rings.append([bm.verts.new((-0.9 * s, y, zt)), bm.verts.new((0, y, -0.3)), bm.verts.new((0.9 * s, y, zt))])
        for a, b in zip(rings, rings[1:]):
            for i in range(2):
                bm.faces.new((a[i], b[i], b[i + 1], a[i + 1]))
        hull = _faces(bm, k)
        k = len(bm.faces)
        tube(bm, [(0, L / 2 - 0.5, 0.9), (0, L / 2 + 0.6, 2.0), (0, L / 2 + 0.9, 2.9)], [0.35, 0.3, 0.25], n=5)
        cuboid(bm, (0, L / 2 + 1.4, 3.1), (0.7, 1.4, 0.6))
        tube(bm, [(0, -L / 2 + 0.3, 1.0), (0, -L / 2 - 0.6, 2.0), (0, -L / 2 - 0.2, 2.9), (0, -L / 2 + 0.3, 2.6)], [0.3, 0.22, 0.12, 0.05], n=4)
        head = _faces(bm, k)
        k = len(bm.faces)
        for s in (-1, 1):
            tube(bm, [(s * 0.2, L / 2 + 1.0, 3.4), (s * 0.4, L / 2 + 0.4, 4.0)], [0.08, 0.03], n=3)
        gold = _faces(bm, k)
        return [(c.lib("red_lacquer"), hull), (c.lib("dragon_scales"), head), (c.lib("isle_gold"), gold)]

    return _p(c, name, build)


# ------------------------------------------------------------------ water and harbour


def dock(c, length=14.0, width=4.0):
    """A wooden jetty on posts (out along +Y), a mooring post at the end."""
    name = "Dock %g %g" % (length, width)

    def build(bm):
        k = len(bm.faces)
        _box(bm, -width / 2, 0, 1.8, width / 2, length, 2.2)
        deck = _faces(bm, k)
        k = len(bm.faces)
        for y in range(0, int(length) + 1, 4):
            for x in (-width / 2 + 0.2, width / 2 - 0.2):
                _cyl(bm, x, y, -4.0, 2.6, 0.18, 0.18, n=5)
        posts = _faces(bm, k)
        return [(c.lib("wood_dock"), deck), (c.lib("timber_beam"), posts)]

    return _p(c, name, build)


def waterwheel_house(c):
    """A mill on the canal bank: a little house, its wheel's axle sticking out over the
    water toward +X (the wheel itself turns in the game; it sits at (3.6, 0, 1.8))."""
    name = "Mill House"

    def build(bm):
        k = len(bm.faces)
        _box(bm, -3.5, -3.0, -1.0, 2.5, 3.0, 3.8)
        plaster = _faces(bm, k)
        k = len(bm.faces)
        _beam(bm, (2.5, 0, 1.8), (4.4, 0, 1.8), 0.25)
        _beam(bm, (4.4, -0.2, -1.5), (4.4, -0.2, 2.2), 0.25)
        _beam(bm, (2.8, 1.7, -1.5), (2.8, 1.7, 3.6), 0.2)
        wood = _faces(bm, k)
        roofs = roof(bm, -0.5, 0, 3.8, 6.0, 6.0, 2.6, over=0.8, curl=0.4)
        return [(c.lib("white_plaster"), plaster), (c.lib("timber_beam"), wood), (c.lib("terracotta"), roofs)]

    return _p(c, name, build)


WHEEL_AT = (3.6, 0.0, 1.8)


def lotus_pool(c, r=6.0):
    """A round stone-rimmed pool (its water is the lagoon material), lotus leaves on it."""
    name = "Lotus Pool %g" % r

    def build(bm):
        k = len(bm.faces)
        loft(bm, [ring(bm, (0, 0), r + 0.8, -0.6, 16), ring(bm, (0, 0), r + 0.8, 0.5, 16), ring(bm, (0, 0), r, 0.5, 16), ring(bm, (0, 0), r, 0.1, 16)], cap_top=False)
        rim = _faces(bm, k)
        k = len(bm.faces)
        bm.faces.new(ring(bm, (0, 0), r, 0.25, 16))
        water = _faces(bm, k)
        k = len(bm.faces)
        for i in range(int(r * 1.2)):
            a = rnd(i * 3 + r) * math.tau
            rr = rnd(i * 7 + 1) * (r - 1.0)
            bm.faces.new(ring(bm, (math.cos(a) * rr, math.sin(a) * rr), 0.55, 0.3, 6))
        pads = _faces(bm, k)
        return [(c.lib("stone_base"), rim), (c.lib("lagoon_shallow"), water), (c.lib("lily_pad"), pads)]

    return _p(c, name, build)


def bridge_arch(c, span=10.0):
    """A little humpbacked footbridge over the canal (across along X), red rails."""
    name = "Footbridge %g" % span

    def build(bm):
        k = len(bm.faces)
        n = 8
        prev = None
        for i in range(n + 1):
            t = i / n
            x = -span / 2 + span * t
            z = 1.0 + 1.8 * math.sin(math.pi * t)
            row = [bm.verts.new((x, y, zz)) for y, zz in ((-1.4, z - 0.6), (-1.4, z), (1.4, z), (1.4, z - 0.6))]
            if prev:
                for j in range(3):
                    bm.faces.new((prev[j], row[j], row[j + 1], prev[j + 1]))
            prev = row
        stone = _faces(bm, k)
        k = len(bm.faces)
        for y in (-1.3, 1.3):
            tube(bm, [(-span / 2 + span * i / n, y, 1.9 + 1.8 * math.sin(math.pi * i / n)) for i in range(n + 1)], 0.07, n=4)
        red = _faces(bm, k)
        return [(c.lib("stone_base"), stone), (c.lib("red_rail"), red)]

    return _p(c, name, build)
