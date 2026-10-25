# Emberdeep Hold's own props (the towers, walls, gates, banners, torches, braziers,
# barrels, crates and pines are keep_props.py's, built in Emberdeep's stone through
# keep_props.use_palette): great fluted pillars, iron chandeliers on chains, the
# portcullis, the dragon's hoard of gold with its chests, lantern posts and ruined arches.
# Origins at the ground, fronts face +Y; all our own designs.
# SPDX-License-Identifier: MIT

import math

from canyon_props import _beam, _cyl
from keep_props import _p, _cone, _flame
from props import blob, cuboid

SAND = "ember_ashlar"
PILLAR = "ember_pillar"
IRON = "keep_iron"
GOLD = "ember_gold"
WOOD = "keep_barrel"


def pillar(c, h=12.0, r=1.1):
    """A great fluted pillar: a square plinth, the shaft, a flared capital."""
    name = "Hold Pillar %.1f %.1f" % (h, r)

    def build(P, bm):
        P.add(SAND, lambda: cuboid(bm, (0, 0, 0.2), (r * 2.8, r * 2.8, 1.2)))
        P.add(PILLAR, lambda: _cyl(bm, 0, 0, 0.8, h - 1.2, r, r * 0.92, n=8))
        P.add(SAND, lambda: _cyl(bm, 0, 0, h - 1.3, h - 0.4, r * 0.95, r * 1.6, n=8))
        P.add(SAND, lambda: cuboid(bm, (0, 0, h - 0.1), (r * 3.4, r * 3.4, 0.7)))

    return _p(c, name, build)


def chandelier(c, r=2.4, drop=5.0):
    """An iron ring of candles hanging on a chain (origin at the chain's top)."""
    name = "Chandelier %.1f" % r

    def build(P, bm):
        P.add(IRON, lambda: _beam(bm, (0, 0, 0), (0, 0, -drop), 0.08))
        for k in range(4):
            a = k * math.pi / 2
            P.add(IRON, lambda a=a: _beam(bm, (0, 0, -drop + 1.2), (r * math.cos(a), r * math.sin(a), -drop), 0.06))
        P.add(IRON, lambda: _cyl(bm, 0, 0, -drop - 0.15, -drop + 0.1, r, r, n=10))
        for k in range(6):
            a = k * math.tau / 6
            _flame(P, bm, r * math.cos(a), r * math.sin(a), -drop + 0.1, 0.45)

    return _p(c, name, build)


def portcullis(c, w=14.0, h=6.0):
    """An iron portcullis, raised: its grid along X (it hangs above the road)."""
    name = "Portcullis %.1f %.1f" % (w, h)

    def build(P, bm):
        n = int(w / 1.2)
        for k in range(n + 1):
            x = -w / 2 + w * k / n
            P.add(IRON, lambda x=x: _beam(bm, (x, 0, 0), (x, 0, h), 0.18))
            P.add(IRON, lambda x=x: _cyl(bm, x, 0, -0.6, 0.0, 0.02, 0.14, n=4))  # the spikes, down
        for j in range(5):
            z = 0.4 + j * (h - 0.6) / 4
            P.add(IRON, lambda z=z: _beam(bm, (-w / 2, 0, z), (w / 2, 0, z), 0.16))

    return _p(c, name, build)


def hoard(c, r=7.0):
    """The dragon's hoard: a low mound of gold, chests spilling more, a few goblets."""
    name = "Dragon Hoard %.1f" % r

    def build(P, bm):
        P.add(GOLD, lambda: blob(bm, (0, 0, -r * 0.18), r, sz=0.38))
        for k, (x, y, s) in enumerate(((r * 0.7, r * 0.3, 1.0), (-r * 0.6, r * 0.5, 1.2), (r * 0.1, -r * 0.8, 0.9))):
            rot = 0.6 * k
            P.add(WOOD, lambda x=x, y=y, s=s, rot=rot: cuboid(bm, (x, y, 0.45 * s), (1.8 * s, 1.2 * s, 0.9 * s), rot=rot))
            P.add(GOLD, lambda x=x, y=y, s=s, rot=rot: cuboid(bm, (x, y, 0.95 * s), (1.6 * s, 1.0 * s, 0.25 * s), rot=rot))
        for k in range(5):
            a = k * 1.3
            x, y = r * 0.5 * math.cos(a), r * 0.5 * math.sin(a)
            P.add(GOLD, lambda x=x, y=y: _cyl(bm, x, y, 0.6, 1.4, 0.15, 0.35, n=6))

    return _p(c, name, build)


def lantern_post(c):
    """A tall iron lamp post with a hanging lantern (the board's lantern posts; the
    flame's foot 4.2 m up and 0.9 m out)."""
    name = "Hold Lantern Post"

    def build(P, bm):
        P.add(SAND, lambda: cuboid(bm, (0, 0, 0.2), (0.9, 0.9, 0.8)))
        P.add(IRON, lambda: _cyl(bm, 0, 0, 0.5, 5.2, 0.12, 0.1, n=6))
        P.add(IRON, lambda: _beam(bm, (0, 0, 5.0), (0, 1.0, 5.0), 0.08))
        P.add(IRON, lambda: _cyl(bm, 0, 0.9, 3.9, 4.8, 0.32, 0.32, n=4))
        P.add(IRON, lambda: _cone(bm, 0, 0.9, 4.8, 0.5, 0.42, n=4))
        _flame(P, bm, 0, 0.9, 4.1, 0.5)

    return _p(c, name, build)


def ruined_arch(c, span=10.0, h=9.0):
    """A broken arch: one pier standing to full height with half its arch, the other
    stub low, blocks fallen at its foot."""
    name = "Ruined Arch %.1f" % span

    def build(P, bm):
        half = span / 2
        P.add(SAND, lambda: cuboid(bm, (-half - 0.9, 0, h / 2 - 0.5), (1.8, 2.4, h + 1.0)))
        P.add(SAND, lambda: cuboid(bm, (half + 0.9, 0, 1.4), (1.8, 2.4, 3.6)))
        for j in range(5):
            a = math.pi - j * math.pi / 10
            x, z = half * math.cos(a), h + half * 0.55 * math.sin(a)
            P.add(SAND, lambda x=x, z=z, a=a: cuboid(bm, (x, 0, z), (1.8, 2.4, 1.3), tilt=(0.0, a - math.pi / 2)))
        for k, (x, y) in enumerate(((half - 1, 2.2), (half + 2.5, -1.8), (1.0, 2.6))):
            P.add(SAND, lambda x=x, y=y, k=k: cuboid(bm, (x, y, 0.5), (1.4, 1.2, 1.0), rot=0.5 * k))

    return _p(c, name, build)
