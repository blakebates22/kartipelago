# Celestial Dragon Festival's props: the celestial palace's domed halls and towers, the
# golden arches over the road, the observatory, the colossal golden dragons, the altar,
# the gongs, the dragon floats, the grandstands, the murals, the braziers and the star
# pillars. Each builds one mesh (a prototype) every copy shares; origins at the ground,
# fronts face +Y. All our own designs (with Dragon Isles' isles_props.py for the rest).
# SPDX-License-Identifier: MIT

import math

from canyon_props import _beam, _cyl
from isles_props import _box, _lantern, _p, fit_uvs, pillars, ridge, roof
from props import _faces, blob, cuboid, loft, ring, tube


def _dome(bm, cx, cy, z, r, h=None, n=12, onion=False):
    """A dome over a circle of radius r at height z (h tall); an onion bulges first.
    Returns its faces."""
    k0 = len(bm.faces)
    h = h or r
    rings = []
    steps = 6
    for i in range(steps + 1):
        t = i / steps
        a = t * math.pi / 2
        rr = r * math.cos(a)
        if onion:
            rr *= 1.0 + 0.25 * math.sin(t * math.pi) - 0.0 * t
        rings.append(ring(bm, (cx, cy), max(0.05, rr), z + h * math.sin(a), n))
    loft(bm, rings, cap_top=True)
    return _faces(bm, k0)


def _spire(bm, x, y, z, h, r=0.3):
    k0 = len(bm.faces)
    _cyl(bm, x, y, z, z + h * 0.35, r * 1.6, r, n=6)
    blob(bm, (x, y, z + h * 0.45), r * 1.4)
    _cyl(bm, x, y, z + h * 0.5, z + h, r * 0.6, 0.02, n=6)
    return _faces(bm, k0)


# ------------------------------------------------------------------ the palace


def dome_hall(c, w=24.0, d=16.0, h=9.0, domes=1):
    """A palace hall in white marble: a stepped plinth, a colonnade of gold-capped columns,
    tall arched windows blazing with light, a gold cornice, and one (or three) deep blue
    star-tiled domes with gold finials."""
    name = "Dome Hall %g %g %g %d" % (w, d, h, domes)

    def build(bm):
        marble, glass, gold, dome = [], [], [], []
        k = len(bm.faces)
        _box(bm, -w / 2 - 3, -d / 2 - 3, -2.0, w / 2 + 3, d / 2 + 3, 0.6)
        _box(bm, -w / 2 - 1.5, -d / 2 - 1.5, 0.6, w / 2 + 1.5, d / 2 + 1.5, 1.2)
        _box(bm, -w / 2, -d / 2, 1.2, w / 2, d / 2, 1.2 + h)
        marble += _faces(bm, k)
        k = len(bm.faces)
        n = max(2, int(w / 4.0))
        for i in range(n):
            x = -w / 2 + (i + 0.5) * w / n
            _box(bm, x - w / n * 0.3, d / 2, 2.4, x + w / n * 0.3, d / 2 + 0.1, 1.2 + h * 0.85)
            _box(bm, x - w / n * 0.3, -d / 2 - 0.1, 2.4, x + w / n * 0.3, -d / 2, 1.2 + h * 0.85)
        glass += _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -w / 2 - 0.8, -d / 2 - 0.8, 1.2 + h, w / 2 + 0.8, d / 2 + 0.8, 2.2 + h)
        gold += _faces(bm, k)
        k = len(bm.faces)
        xs = [-w / 2 - 0.9 + (w + 1.8) * i / n for i in range(n + 1)]
        for x in xs:
            _cyl(bm, x, d / 2 + 1.0, 1.2, 1.2 + h, 0.45, 0.4, n=8)
        marble += _faces(bm, k)
        k = len(bm.faces)
        for x in xs:
            _box(bm, x - 0.6, d / 2 + 0.4, 1.2 + h - 0.6, x + 0.6, d / 2 + 1.6, 1.2 + h)
        gold += _faces(bm, k)
        top = 2.2 + h
        spots = [(0.0, 0.0, min(w, d) * 0.36)] if domes == 1 else [(0.0, 0.0, min(w, d) * 0.3), (-w * 0.34, 0.0, min(w, d) * 0.17),
                                                                  (w * 0.34, 0.0, min(w, d) * 0.17)]
        for x, y, r in spots:
            k = len(bm.faces)
            _cyl(bm, x, y, top, top + r * 0.5, r * 1.02, r * 1.02, n=12)
            marble += _faces(bm, k)
            k = len(bm.faces)
            _cyl(bm, x, y, top + r * 0.5, top + r * 0.62, r * 1.1, r * 1.1, n=12)
            gold += _faces(bm, k)
            dome += _dome(bm, x, y, top + r * 0.62, r, r * 0.95, n=12)
            gold += _spire(bm, x, y, top + r * 1.55, r * 0.8, r * 0.07)
        return [(c.lib("cdf_marble"), marble), (c.lib("cdf_window"), glass), (c.lib("cdf_gold"), gold), (c.lib("cdf_dome"), dome)]

    return _p(c, name, build)


def dome_tower(c, h=26.0, r=4.0, onion=True):
    """A slender round tower: marble drum, a band of lit windows near the top, a gold
    gallery, a blue onion dome and a tall gold spire."""
    name = "Dome Tower %g %g %d" % (h, r, onion)

    def build(bm):
        marble, glass, gold, dome = [], [], [], []
        k = len(bm.faces)
        _cyl(bm, 0, 0, -2.0, 1.0, r * 1.4, r * 1.3, n=10)
        _cyl(bm, 0, 0, 1.0, h, r, r * 0.9, n=10)
        marble += _faces(bm, k)
        k = len(bm.faces)
        _cyl(bm, 0, 0, h * 0.62, h * 0.86, r * 0.92, r * 0.91, n=10)
        glass += _faces(bm, k)
        k = len(bm.faces)
        _cyl(bm, 0, 0, h, h + 0.8, r * 1.25, r * 1.25, n=10)
        for i in range(8):
            a = i * math.tau / 8
            _cyl(bm, r * 1.1 * math.cos(a), r * 1.1 * math.sin(a), h + 0.8, h + 2.6, 0.18, 0.18, n=4)
        _cyl(bm, 0, 0, h + 2.6, h + 3.0, r * 1.2, r * 1.2, n=10)
        gold += _faces(bm, k)
        k = len(bm.faces)
        _cyl(bm, 0, 0, h + 0.8, h + 3.0, r * 0.8, r * 0.8, n=10)
        marble += _faces(bm, k)
        dome += _dome(bm, 0, 0, h + 3.0, r * 0.95, r * 1.6, n=10, onion=onion)
        gold += _spire(bm, 0, 0, h + 3.0 + r * 1.55, r * 2.0, 0.22)
        return [(c.lib("cdf_marble"), marble), (c.lib("cdf_window"), glass), (c.lib("cdf_gold"), gold), (c.lib("cdf_dome"), dome)]

    return _p(c, name, build)


def terrace(c, w, d, h):
    """A marble terrace block the palace stands on, gold-railed."""
    name = "Terrace %g %g %g" % (w, d, h)

    def build(bm):
        k = len(bm.faces)
        _box(bm, -w / 2, -d / 2, -h, w / 2, d / 2, 0.0)
        marble = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -w / 2 - 0.6, -d / 2 - 0.6, -1.0, w / 2 + 0.6, d / 2 + 0.6, 0.4)
        gold = _faces(bm, k)
        k = len(bm.faces)
        for x in (-w / 2, w / 2):
            _box(bm, x - 0.25, -d / 2, 0.4, x + 0.25, d / 2, 1.4)
        for y in (-d / 2, d / 2):
            _box(bm, -w / 2, y - 0.25, 0.4, w / 2, y + 0.25, 1.4)
        rail = _faces(bm, k)
        return [(c.lib("cdf_marble"), marble), (c.lib("cdf_gold"), gold), (c.lib("cdf_balustrade"), rail)]

    return _p(c, name, build)


# ------------------------------------------------------------------ over the road


def celestial_arch(c, span=24.0, height=14.0):
    """A great golden arch over the road: marble piers with star lamps, a gold arch band
    with a radiant star medallion at its crown, lanterns hanging under it (the road runs
    through along Y)."""
    name = "Celestial Arch %g %g" % (span, height)

    def build(bm):
        marble, gold, glass, paper = [], [], [], []
        half = span / 2
        for s in (-1, 1):
            k = len(bm.faces)
            _box(bm, s * half - 1.6, -1.6, -1.0, s * half + 1.6, 1.6, 1.2)
            _box(bm, s * half - 1.1, -1.1, 1.2, s * half + 1.1, 1.1, height * 0.62)
            marble += _faces(bm, k)
            k = len(bm.faces)
            _box(bm, s * half - 1.4, -1.4, height * 0.62, s * half + 1.4, 1.4, height * 0.62 + 0.8)
            gold += _faces(bm, k)
        # The arch: a band of gold, a semicircle from pier to pier.
        k = len(bm.faces)
        n = 16
        z0 = height * 0.62 + 0.8
        rise = height - z0
        inner, outer = [], []
        for i in range(n + 1):
            a = math.pi * i / n
            x = -math.cos(a) * half
            z = z0 + math.sin(a) * rise
            inner.append((x, z))
            outer.append((-math.cos(a) * (half + 1.6), z0 + math.sin(a) * (rise + 1.8)))
        for i in range(n):
            q = []
            for (x, z) in (inner[i], inner[i + 1], outer[i + 1], outer[i]):
                q.append((x, z))
            for y in (-0.7, 0.7):
                bm.faces.new([bm.verts.new((x, y, z)) for x, z in (q if y > 0 else q[::-1])])
            bm.faces.new([bm.verts.new((x, y, z)) for (x, z), y in ((inner[i], -0.7), (inner[i + 1], -0.7), (inner[i + 1], 0.7), (inner[i], 0.7))])
            bm.faces.new([bm.verts.new((x, y, z)) for (x, z), y in ((outer[i], 0.7), (outer[i + 1], 0.7), (outer[i + 1], -0.7), (outer[i], -0.7))])
        gold += _faces(bm, k)
        # The medallion: a star of glass in a gold ring at the crown.
        k = len(bm.faces)
        cz = height + 2.2
        pts = []
        for i in range(16):
            a = i * math.tau / 16
            r = 2.8 if i % 2 == 0 else 1.2
            pts.append((r * math.cos(a), cz + r * math.sin(a)))
        for y in (-0.5, 0.5):
            vs = [bm.verts.new((x, y, z)) for x, z in pts]
            bm.faces.new(vs if y > 0 else vs[::-1])
        glass += _faces(bm, k)
        # Star lamps on the piers, lanterns under the arch.
        k = len(bm.faces)
        for s in (-1, 1):
            blob(bm, (s * half, 0, height * 0.62 + 1.6), 0.8)
        glass += _faces(bm, k)
        for i in range(5):
            x = -half * 0.6 + i * half * 0.3
            z = z0 + math.sin(math.acos(max(-1, min(1, -x / half)))) * rise - 0.6
            cap, pp = _lantern(bm, x, 0, z, 1.4)
            gold += cap
            paper += pp
        return [(c.lib("cdf_marble"), marble), (c.lib("cdf_gold"), gold), (c.lib("cdf_star_glass"), glass), (c.lib("lantern_red"), paper)]

    return _p(c, name, build)


# ------------------------------------------------------------------ the observatory


def observatory(c):
    """The Celestial Observatory: a round tiered tower of marble and star glass on the
    pinnacle's top, a gold-ribbed dome open to the sky, and the great armillary's stand
    (its rings turn above it in the game: game/festivalLife.ts)."""
    name = "Observatory"

    def build(bm):
        marble, glass, gold, dome = [], [], [], []
        k = len(bm.faces)
        _cyl(bm, 0, 0, -6.0, 2.0, 22.0, 21.0, n=16)
        _cyl(bm, 0, 0, 2.0, 14.0, 15.0, 14.0, n=16)
        _cyl(bm, 0, 0, 20.0, 22.0, 11.5, 11.5, n=16)
        marble += _faces(bm, k)
        k = len(bm.faces)
        _cyl(bm, 0, 0, 4.0, 12.0, 14.6, 14.2, n=16)
        _cyl(bm, 0, 0, 14.0, 20.0, 10.5, 10.5, n=16)
        glass += _faces(bm, k)
        k = len(bm.faces)
        _cyl(bm, 0, 0, 2.0, 2.8, 22.5, 22.5, n=16)
        _cyl(bm, 0, 0, 14.0, 15.0, 15.6, 15.6, n=16)
        for i in range(16):
            a = i * math.tau / 16
            _cyl(bm, 13.2 * math.cos(a), 13.2 * math.sin(a), 14.0, 21.0, 0.5, 0.5, n=6)
        _cyl(bm, 0, 0, 22.0, 23.0, 12.2, 12.2, n=16)
        gold += _faces(bm, k)
        dome += _dome(bm, 0, 0, 23.0, 10.0, 6.5, n=16)
        k = len(bm.faces)
        for i in range(8):
            a = i * math.tau / 8
            tube(bm, [(10.2 * math.cos(a), 10.2 * math.sin(a), 23.0), (7.6 * math.cos(a), 7.6 * math.sin(a), 27.4),
                      (0.0, 0.0, 29.6)], [0.25, 0.22, 0.18], n=4)
        # The armillary's stand: a tall gold column on the dome's crown with four claws.
        _cyl(bm, 0, 0, 29.0, 44.0, 0.9, 0.7, n=8)
        for i in range(4):
            a = i * math.tau / 4 + 0.4
            tube(bm, [(0, 0, 42.0), (3.0 * math.cos(a), 3.0 * math.sin(a), 44.5), (4.2 * math.cos(a), 4.2 * math.sin(a), 47.0)],
                 [0.4, 0.3, 0.15], n=4)
        gold += _faces(bm, k)
        return [(c.lib("cdf_marble"), marble), (c.lib("cdf_star_glass"), glass), (c.lib("cdf_gold"), gold), (c.lib("cdf_dome"), dome)]

    return _p(c, name, build)


OBSERVATORY_RINGS_Z = 47.0  # the armillary's centre above the observatory's ground


# ------------------------------------------------------------------ worship


def altar(c):
    """The great altar: three marble steps, a gold table, two gold fire bowls and the
    glowing mural of the dragon among the stars behind (its front faces +Y)."""
    name = "Altar"
    face = []

    def build(bm):
        marble, gold = [], []
        k = len(bm.faces)
        for i, (w, d) in enumerate(((22.0, 14.0), (17.0, 10.0), (12.0, 7.0))):
            _box(bm, -w / 2, -d / 2, -1.0 + 0.9 * i, w / 2, d / 2, 0.9 * (i + 1))
        _box(bm, -7.0, -4.4, 2.7, 7.0, -3.4, 13.0)
        marble += _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -3.0, -1.0, 2.7, 3.0, 1.0, 3.9)
        for s in (-1, 1):
            _cyl(bm, s * 4.6, 1.2, 2.7, 4.4, 0.25, 0.5, n=6)
            _cyl(bm, s * 4.6, 1.2, 4.4, 5.0, 1.2, 1.4, n=8)
        _box(bm, -7.4, -4.6, 13.0, 7.4, -3.2, 13.8)
        gold += _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -6.0, -3.42, 4.0, 6.0, -3.32, 12.4)
        face.extend(_faces(bm, k))
        return [(c.lib("cdf_marble"), marble), (c.lib("cdf_gold"), gold), (c.lib("cdf_mural"), face)]

    if name not in c.protos:
        _p(c, name, build)
        fit_uvs(c, name, face)
    return name


def mural_wall(c):
    """A wall panel with the glowing celestial dragon mural, gold-framed, under a little
    blue roof."""
    name = "Mural Wall"
    face = []

    def build(bm):
        k = len(bm.faces)
        _box(bm, -5.0, -0.8, -1.0, 5.0, 0.0, 9.0)
        marble = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -5.3, -0.9, 8.6, 5.3, 0.1, 9.2)
        gold = _faces(bm, k)
        roofs = roof(bm, 0, -0.4, 9.2, 10.6, 1.2, 1.6, over=0.9, curl=0.6)
        k = len(bm.faces)
        _box(bm, -4.2, 0.0, 0.8, 4.2, 0.08, 8.2)
        face.extend(_faces(bm, k))
        return [(c.lib("cdf_marble"), marble), (c.lib("cdf_gold"), gold), (c.lib("roof_blue"), roofs), (c.lib("cdf_mural"), face)]

    if name not in c.protos:
        _p(c, name, build)
        fit_uvs(c, name, face)
    return name


def gong(c):
    """A great gong in a red and gold frame."""
    name = "Gong"

    def build(bm):
        k = len(bm.faces)
        for s in (-1, 1):
            _cyl(bm, s * 2.4, 0, -0.5, 6.0, 0.22, 0.2, n=6)
        _beam(bm, (-3.0, 0, 6.0), (3.0, 0, 6.0), 0.3)
        red = _faces(bm, k)
        k = len(bm.faces)
        for y in (-0.08, 0.08):
            vs = ring(bm, (0, 0), 1.9, 0, 16)
            for v in vs:
                v.co = (v.co.x, y, 3.4 + v.co.y)
            bm.faces.new(vs if y > 0 else vs[::-1])
        blob(bm, (0, 0, 3.4), 0.5, 1, 0.4, 1)
        gold = _faces(bm, k)
        return [(c.lib("red_lacquer"), red), (c.lib("cdf_gold"), gold)]

    return _p(c, name, build)


def brazier(c):
    """A gold fire bowl on a tall tripod (its flame is a glow light)."""
    name = "Brazier"

    def build(bm):
        k = len(bm.faces)
        for i in range(3):
            a = i * math.tau / 3
            _beam(bm, (1.0 * math.cos(a), 1.0 * math.sin(a), -0.3), (0.3 * math.cos(a), 0.3 * math.sin(a), 3.0), 0.16)
        _cyl(bm, 0, 0, 3.0, 3.9, 0.5, 1.2, n=8)
        gold = _faces(bm, k)
        k = len(bm.faces)
        blob(bm, (0, 0, 4.0), 0.75, 1, 1, 1.3)
        fire = _faces(bm, k)
        return [(c.lib("cdf_gold"), gold), (c.lib("lantern_red"), fire)]

    return _p(c, name, build)


BRAZIER_LIGHT = 4.4


def star_pillar(c, h=7.0):
    """A navy and gold column with a glowing star lamp on top (along the high roads)."""
    name = "Star Pillar %g" % h

    def build(bm):
        k = len(bm.faces)
        _box(bm, -0.8, -0.8, -0.8, 0.8, 0.8, 0.6)
        _cyl(bm, 0, 0, h - 0.4, h, 0.6, 0.7, n=6)
        gold = _faces(bm, k)
        k = len(bm.faces)
        _cyl(bm, 0, 0, 0.6, h - 0.4, 0.42, 0.36, n=6)
        dome = _faces(bm, k)
        k = len(bm.faces)
        for i in range(8):
            a = i * math.tau / 8
            r = 1.0 if i % 2 == 0 else 0.42
            tube(bm, [(0, 0, h + 0.9), (r * math.cos(a), r * math.sin(a) * 0.3, h + 0.9 + r * math.sin(a))], [0.2, 0.06], n=3)
        blob(bm, (0, 0, h + 0.9), 0.42)
        glass = _faces(bm, k)
        return [(c.lib("cdf_gold"), gold), (c.lib("cdf_dome"), dome), (c.lib("cdf_star_glass"), glass)]

    return _p(c, name, build)


STAR_LIGHT = 7.9


def grandstand(c, length=24.0, rows=4):
    """Stepped marble seating for the crowds, a red and gold awning on posts over the top
    row (its front, the lowest row, faces +Y; the villagers stand on it in the game)."""
    name = "Grandstand %g %d" % (length, rows)

    def build(bm):
        marble, red, gold = [], [], []
        k = len(bm.faces)
        for i in range(rows):
            _box(bm, -length / 2, -1.6 * (i + 1), -1.0, length / 2, -1.6 * i, 0.7 * (i + 1))
        marble += _faces(bm, k)
        k = len(bm.faces)
        back = -1.6 * rows
        for x in (-length / 2, 0.0, length / 2):
            _cyl(bm, x, back + 0.3, 0.7 * rows, 0.7 * rows + 4.2, 0.15, 0.15, n=4)
        red += _faces(bm, k)
        k = len(bm.faces)
        a = [bm.verts.new(p) for p in ((-length / 2 - 0.5, back - 0.2, 0.7 * rows + 4.2), (length / 2 + 0.5, back - 0.2, 0.7 * rows + 4.2),
                                        (length / 2 + 0.5, back + 3.6, 0.7 * rows + 3.4), (-length / 2 - 0.5, back + 3.6, 0.7 * rows + 3.4))]
        bm.faces.new(a)
        bm.faces.new(list(reversed([bm.verts.new(v.co.copy()) for v in a])))
        red += _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -length / 2 - 0.5, back + 3.4, 0.7 * rows + 3.0, length / 2 + 0.5, back + 3.7, 0.7 * rows + 3.5)
        gold += _faces(bm, k)
        return [(c.lib("cdf_marble"), marble), (c.lib("red_lacquer"), red), (c.lib("cdf_gold"), gold)]

    return _p(c, name, build)


def grandstand_rows(length=24.0, rows=4):
    """Where the villagers stand on a grandstand: [(local x, local y, z)]."""
    out = []
    for i in range(rows):
        y = -1.6 * i - 0.8
        z = 0.7 * (i + 1)
        n = int(length / 1.6)
        for j in range(n):
            out.append((-length / 2 + (j + 0.5) * length / n, y, z))
    return out


def dragon_float(c):
    """A parade float: a red and gold wagon carrying a great dragon's head and coils
    hung with lanterns (parked along the market)."""
    name = "Dragon Float"

    def build(bm):
        red, gold, scales, paper = [], [], [], []
        k = len(bm.faces)
        _box(bm, -2.4, -5.0, 0.8, 2.4, 5.0, 2.0)
        red += _faces(bm, k)
        k = len(bm.faces)
        for x in (-2.5, 2.5):
            for y in (-3.6, 3.6):
                vs = ring(bm, (0, 0), 0.8, 0, 8)
                for v in vs:
                    v.co = (x, y + v.co.x, 0.8 + v.co.y)
                bm.faces.new(vs if x > 0 else vs[::-1])
        _box(bm, -2.6, -5.1, 1.9, 2.6, 5.1, 2.2)
        gold += _faces(bm, k)
        k = len(bm.faces)
        pts = []
        rad = []
        for i in range(12):
            t = i / 11
            pts.append((1.2 * math.sin(t * 7.0), -4.4 + t * 7.4, 2.4 + 1.6 * abs(math.sin(t * 5.5)) + t * 1.6))
            rad.append(0.75 - 0.25 * (1 - t))
        tube(bm, pts, rad, n=6)
        cuboid(bm, (pts[-1][0], pts[-1][1] + 1.2, pts[-1][2] + 0.6), (1.6, 2.2, 1.3))
        cuboid(bm, (pts[-1][0], pts[-1][1] + 2.4, pts[-1][2] + 0.3), (1.1, 1.4, 0.6))
        scales += _faces(bm, k)
        k = len(bm.faces)
        for s in (-1, 1):
            tube(bm, [(pts[-1][0] + s * 0.4, pts[-1][1] + 0.8, pts[-1][2] + 1.2), (pts[-1][0] + s * 0.9, pts[-1][1] - 0.2, pts[-1][2] + 2.4)],
                 [0.15, 0.05], n=4)
        gold += _faces(bm, k)
        for i in (2, 5, 8):
            cap, pp = _lantern(bm, pts[i][0], pts[i][1], pts[i][2] + 2.6, 1.2)
            gold += cap
            paper += pp
        return [(c.lib("red_lacquer"), red), (c.lib("cdf_gold"), gold), (c.lib("dragon_scales"), scales), (c.lib("lantern_red"), paper)]

    return _p(c, name, build)


def shrine_base(c, r=22.0):
    """The Great Dragon Shrine's platform: three round marble tiers with gold rims, steps
    on four sides, a ring of gold fire bowls on the top tier (the colossal dragon stands
    in the middle)."""
    name = "Shrine Base %g" % r

    def build(bm):
        marble, gold, fire = [], [], []
        k = len(bm.faces)
        for i, (rr, z0, z1) in enumerate(((r, -2.0, 1.4), (r * 0.8, 1.4, 2.8), (r * 0.6, 2.8, 4.2))):
            _cyl(bm, 0, 0, z0, z1, rr, rr, n=24)
        for a in range(4):
            ang = a * math.pi / 2 + math.pi / 4
            ca, sa = math.cos(ang), math.sin(ang)
            for j in range(6):
                d = r + 1.0 - j * (r * 0.4 / 5)
                z = 0.7 * j
                cuboid(bm, (ca * d, sa * d, z + 0.35), (7.0, 2.2, 0.7), rot=ang + math.pi / 2)
        marble += _faces(bm, k)
        k = len(bm.faces)
        for rr, z in ((r, 1.4), (r * 0.8, 2.8), (r * 0.6, 4.2)):
            _cyl(bm, 0, 0, z, z + 0.35, rr + 0.3, rr + 0.3, n=24)
        for i in range(12):
            a = i * math.tau / 12
            _cyl(bm, r * 0.55 * math.cos(a), r * 0.55 * math.sin(a), 4.2, 6.0, 0.2, 0.6, n=6)
            _cyl(bm, r * 0.55 * math.cos(a), r * 0.55 * math.sin(a), 6.0, 6.6, 1.0, 1.2, n=8)
        gold += _faces(bm, k)
        k = len(bm.faces)
        for i in range(12):
            a = i * math.tau / 12
            blob(bm, (r * 0.55 * math.cos(a), r * 0.55 * math.sin(a), 7.0), 0.75, 1, 1, 1.4)
        fire += _faces(bm, k)
        return [(c.lib("cdf_marble"), marble), (c.lib("cdf_gold"), gold), (c.lib("lantern_red"), fire)]

    return _p(c, name, build)


def colossus(c):
    """A colossal golden dragon: Dragon Isles' coiled statue in gold on a tall marble
    pedestal (placed at three to four times size)."""
    import isles_props as ip

    return ip.dragon_statue(c, "cdf_gold")


__all__ = ["pillars", "ridge", "fit_uvs"]
