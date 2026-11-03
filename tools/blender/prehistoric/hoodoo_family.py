# A family of desert rock formations (Blake, review-desert_region 3, note 5: "we need to add
# more variety of these structures. currently we have only different sizes of these
# columns, but lets get a family of varying structures"). Each is a prop (built once per
# shape and size), origin at the ground, sunk a little; canyon_props.hoodoo's stacked
# column is one of the family.
# SPDX-License-Identifier: MIT

import math

from props import _faces, blob, loft, ring, tube

BANDS = ("strata_red", "strata_orange", "strata_rust")
CAP = "strata_cream"


def _p(c, name, build):
    return c.proto(name, build) and name


def _wob(k, v):
    return 1.0 + 0.12 * math.sin(k * 2.3 + v * 1.7) + 0.06 * math.sin(k * 5.1 + v)


def _column(bm, x, y, z0, z1, r0, r1, v, n=8, bands=6, waist=0.3, lean=(0.0, 0.0)):
    """A banded, waisted column from z0 to z1 (radius r0 at its foot to r1 at its top)."""
    rings = []
    for k in range(bands + 1):
        t = k / bands
        z = z0 + (z1 - z0) * t
        r = (r0 + (r1 - r0) * t) * (1.0 - waist * math.sin(math.pi * t) * (0.6 + 0.4 * math.sin(k * 1.9 + v))) * _wob(k, v)
        rings.append(ring(bm, (x + lean[0] * t, y + lean[1] * t), r, z, n, phase=v * 0.7))
    loft(bm, rings, cap_top=True, cap_bottom=True)


def mushroom(c, v=0, height=7.0):
    """A mushroom rock: a short pale-waisted stem worn thin, a broad flat cap of hard
    caprock overhanging all round."""
    name = "Rock Mushroom %d %d" % (v, int(height))

    def build(bm):
        stem = height * 0.72
        _column(bm, 0, 0, -1.5, stem, 2.6, 1.3, v, bands=5, waist=0.35)
        body = _faces(bm, 0)
        k0 = len(bm.faces)
        cr = 3.6 + 0.5 * (v % 2)
        loft(bm, [ring(bm, (0.3, 0), cr * 0.6, stem - 0.3, 9), ring(bm, (0.3, 0), cr, stem + 0.5, 9, rx=cr * 1.2),
                  ring(bm, (0.3, 0), cr * 0.95, stem + 1.4, 9, rx=cr * 1.12), ring(bm, (0.3, 0), cr * 0.6, stem + 1.8, 9)], cap_top=True)
        return [(c.lib(BANDS[v % 3]), body), (c.lib(CAP), _faces(bm, k0))]

    return _p(c, name, build)


def balanced(c, v=0, height=9.0):
    """A balanced rock: a slender pedestal, a great rounded boulder perched on its top,
    a little off its middle."""
    name = "Rock Balanced %d %d" % (v, int(height))

    def build(bm):
        ped = height * 0.62
        _column(bm, 0, 0, -1.5, ped, 2.2, 0.9, v, bands=5, waist=0.25)
        body = _faces(bm, 0)
        k0 = len(bm.faces)
        br = height * 0.26
        blob(bm, (0.6, 0.2, ped + br * 0.8), br, sx=1.25, sy=1.0, sz=0.85, subdiv=2)
        return [(c.lib(BANDS[(v + 1) % 3]), body), (c.lib("desert_strata"), _faces(bm, k0))]

    return _p(c, name, build)


def spires(c, v=0, height=14.0):
    """A cluster of spires grown from one footing: three or four thin columns of different
    heights, each with its cap."""
    name = "Rock Spires %d %d" % (v, int(height))

    def build(bm):
        _column(bm, 0, 0, -1.5, 2.0, 4.2, 3.6, v, bands=2, waist=0.05)
        n = 3 + v % 2
        caps = []
        for k in range(n):
            a = k * math.tau / n + v
            h = height * (1.0 - 0.22 * ((k + v) % 3))
            x, y = 1.9 * math.cos(a), 1.9 * math.sin(a)
            _column(bm, x, y, 1.0, h, 1.5, 0.7, v + k, bands=6, waist=0.3, lean=(0.4 * math.cos(a), 0.4 * math.sin(a)))
            caps.append((x + 0.4 * math.cos(a), y + 0.4 * math.sin(a), h))
        body = _faces(bm, 0)
        k0 = len(bm.faces)
        for x, y, h in caps:
            loft(bm, [ring(bm, (x, y), 0.7, h - 0.2, 6), ring(bm, (x, y), 1.1, h + 0.3, 6), ring(bm, (x, y), 0.9, h + 1.0, 6)], cap_top=True)
        return [(c.lib(BANDS[(v + 2) % 3]), body), (c.lib(CAP), _faces(bm, k0))]

    return _p(c, name, build)


def fin(c, v=0, height=10.0):
    """A fin: a thin wall of banded sandstone left standing, long and narrow, its top
    ragged."""
    name = "Rock Fin %d %d" % (v, int(height))

    def build(bm):
        rings = []
        bands = 6
        for k in range(bands + 1):
            t = k / bands
            z = -1.5 + (height + 1.5) * t * (1.0 - 0.08 * math.sin(k * 3.0 + v))
            L = (7.0 + 1.5 * (v % 2)) * (1.0 - 0.35 * t) * _wob(k, v)
            W = 1.6 * (1.0 - 0.45 * t)
            rings.append(ring(bm, (0.5 * math.sin(t * 2 + v), 0), W, z, 10, rx=L))
        loft(bm, rings, cap_top=True, cap_bottom=True)
        return [(c.lib("desert_strata"), _faces(bm, 0))]

    return _p(c, name, build)


def arch(c, v=0, height=9.0):
    """A little natural arch: two worn legs and the span of rock between them."""
    name = "Rock Arch %d %d" % (v, int(height))

    def build(bm):
        span = 7.0 + 2.0 * (v % 2)
        for sx in (-1, 1):
            _column(bm, sx * span / 2, 0, -1.5, height * 0.75, 2.2, 1.6, v + sx, bands=4, waist=0.18)
        legs = _faces(bm, 0)
        k0 = len(bm.faces)
        pts = []
        for k in range(9):
            t = k / 8
            a = math.pi * t
            pts.append((-math.cos(a) * span / 2, 0.0, height * 0.68 + math.sin(a) * height * 0.32))
        tube(bm, pts, [1.7, 1.5, 1.3, 1.2, 1.2, 1.2, 1.3, 1.5, 1.7], n=8)
        return [(c.lib(BANDS[v % 3]), legs), (c.lib("desert_strata"), _faces(bm, k0))]

    return _p(c, name, build)


def goblin(c, v=0, height=6.0):
    """A goblin: a squat knobbly lump, rounded knobs heaped on one another (Goblin Valley)."""
    name = "Rock Goblin %d %d" % (v, int(height))

    def build(bm):
        blob(bm, (0, 0, height * 0.25), height * 0.42, sx=1.3, sy=1.1, sz=0.8, subdiv=2)
        blob(bm, (0.4, 0.2, height * 0.62), height * 0.28, sx=1.0, sy=0.9, sz=0.9, subdiv=2)
        blob(bm, (0.2, -0.1, height * 0.9), height * 0.17, subdiv=1)
        return [(c.lib(BANDS[(v + 1) % 3]), _faces(bm, 0))]

    return _p(c, name, build)


def totem(c, v=0, height=12.0):
    """A totem: discs of hard and soft rock stacked, the soft worn deep between the hard,
    a cap on top."""
    name = "Rock Totem %d %d" % (v, int(height))

    def build(bm):
        rings = []
        n = 9
        for k in range(n + 1):
            t = k / n
            z = -1.5 + (height + 1.5) * t
            r = (2.0 if k % 2 == 0 else 1.2) * (1.0 - 0.3 * t) * _wob(k, v)
            rings.append(ring(bm, (0.3 * math.sin(t * 4 + v), 0), r, z, 8, phase=v))
        loft(bm, rings, cap_top=False, cap_bottom=True)
        body = _faces(bm, 0)
        k0 = len(bm.faces)
        loft(bm, [ring(bm, (0, 0), 1.2, height - 0.1, 8), ring(bm, (0, 0), 1.9, height + 0.4, 8), ring(bm, (0, 0), 1.6, height + 1.3, 8)],
             cap_top=True)
        return [(c.lib(BANDS[(v + 2) % 3]), body), (c.lib(CAP), _faces(bm, k0))]

    return _p(c, name, build)


FAMILY = (mushroom, balanced, spires, fin, arch, goblin, totem)
