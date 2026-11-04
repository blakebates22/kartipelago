# The pueblo's everyday things (Blake, review-desert_region 4, note 4: "we need more props
# here. a few more fires, other things that would be present"): fire rings, ristra racks
# of drying chiles, ollas, woodpiles, blankets airing on a line, grinding stones, baskets,
# corn heaps. Each a prop, origin at the ground, built once.
# SPDX-License-Identifier: MIT

import math

from course_kit import rnd
from oasis_desert import Parts, _log
from props import blob, cuboid, loft, ring


def _p(c, name, build):
    return c.proto(name, build) and name


def fire_ring(c, variant=0):
    """A hearth on the plaza: a ring of fire-blackened stones round a bed of ash and a few
    charred logs (the flames are a campfire entity)."""
    name = "Pueblo Fire Ring %d" % variant

    def build(bm):
        P = Parts(bm)
        n = 9 + variant % 3
        for k in range(n):
            a = k * math.tau / n + 0.2 * rnd(k + variant)
            r = 0.26 + 0.08 * rnd(k * 2 + variant)
            P.add("canyon_rock_ochre" if k % 3 else "ember_rock", blob, (1.15 * math.cos(a), 1.15 * math.sin(a), 0.12), r,
                  sx=1.2, sy=1.0, sz=0.7, subdiv=1)
        P.add("ember_ash", loft, [ring(bm, (0, 0), 1.0, 0.02, 12), ring(bm, (0, 0), 0.5, 0.1, 12)], cap_top=True)
        for k in range(3):
            a = k * 2.1 + variant
            _log(P, "charred_bark", (0.6 * math.cos(a), 0.6 * math.sin(a), 0.12), (-0.2 * math.cos(a), -0.2 * math.sin(a), 0.32),
                 0.09, n=5)
        return P.out(c)

    return _p(c, name, build)


def ristra_rack(c, variant=0):
    """A drying rack: two peeled posts and a pole between, strings of red chiles (ristras)
    hanging from it, a few corn cobs tied in pairs."""
    name = "Pueblo Ristra Rack %d" % variant

    def build(bm):
        P = Parts(bm)
        w, h = 3.2 + 0.4 * (variant % 2), 2.3
        for sx in (-1, 1):
            _log(P, "weathered_timber", (sx * w / 2, 0, -0.2), (sx * w / 2, 0, h), 0.08, n=6)
        _log(P, "weathered_timber", (-w / 2 - 0.2, 0, h - 0.1), (w / 2 + 0.2, 0, h - 0.1), 0.06, n=5)
        n = 6 + variant % 3
        for k in range(n):
            x = -w / 2 + 0.35 + k * (w - 0.7) / (n - 1)
            ln = 0.9 + 0.5 * rnd(k + 3 * variant)
            corn = k % 4 == 3
            for j in range(int(ln / 0.16)):
                z = h - 0.25 - j * 0.16
                r = (0.11 if corn else 0.08) * (1.0 - 0.3 * j / 8)
                P.add("awning_sun" if corn else "awning_red", blob, (x + 0.03 * math.sin(j * 2.1), 0.03 * math.cos(j * 1.7), z), r,
                      sx=0.9, sy=0.9, sz=1.4, subdiv=0)
        return P.out(c)

    return _p(c, name, build)


def ollas(c, variant=0):
    """A cluster of ollas, the pueblo's water and storage jars: round bellies, narrow necks,
    flared lips, the biggest half sunk in the sand, one lying on its side."""
    name = "Pueblo Ollas %d" % variant

    def build(bm):
        P = Parts(bm)
        n = 4 + variant % 3
        for k in range(n):
            a = k * 2.399 + variant
            r = 0.25 + 0.55 * math.sqrt(k / n)
            x, y = r * math.cos(a), r * math.sin(a)
            s = 0.45 - 0.05 * k + 0.08 * rnd(k + variant)
            prof = [(0.35, 0.0), (0.8, 0.25), (1.0, 0.6), (0.85, 0.95), (0.42, 1.2), (0.36, 1.42), (0.5, 1.55)]
            rings = [ring(bm, (x, y), s * rr, s * zz - 0.08, 12) for rr, zz in prof]
            mat = ("terracotta", "adobe", "adobe_dark")[(k + variant) % 3]
            P.add(mat, lambda b, rings=rings: loft(b, rings, cap_top=False, cap_bottom=True))
        return P.out(c)

    return _p(c, name, build)


def woodpile(c, variant=0):
    """Firewood stacked against a wall: split logs in rows, cut ends out, a few leaning."""
    name = "Pueblo Woodpile %d" % variant

    def build(bm):
        P = Parts(bm)
        L = 2.4 + 0.4 * (variant % 2)
        rows = 4
        for r in range(rows):
            n = 6 - r
            for k in range(n):
                x = -L / 2 + 0.1 + (k + 0.5 * (r % 2)) * (L - 0.2) / 6
                z = 0.13 + r * 0.22
                _log(P, "log_bark", (x, -0.55, z), (x + 0.05 * rnd(k + r), 0.55, z), 0.11, n=6)
        for k in range(2):
            x = L / 2 + 0.3 + 0.2 * k
            _log(P, "log_bark", (x, -0.2 + 0.4 * k, 0.0), (x - 0.4, -0.2 + 0.4 * k, 1.3), 0.08, n=5)
        return P.out(c)

    return _p(c, name, build)


def blanket_line(c, variant=0, length=6.0):
    """Woven blankets airing on a line between two posts."""
    name = "Pueblo Blanket Line %d %d" % (variant, int(length))

    def build(bm):
        P = Parts(bm)
        h = 2.2
        for sx in (-1, 1):
            _log(P, "weathered_timber", (sx * length / 2, 0, -0.2), (sx * length / 2, 0, h + 0.1), 0.07, n=6)
        _log(P, "rope_rail", (-length / 2, 0, h), (length / 2, 0, h), 0.02, n=3)
        n = 3 + variant % 2
        for k in range(n):
            x0 = -length / 2 + 0.3 + k * (length - 0.6) / n
            x1 = x0 + (length - 0.6) / n - 0.25
            sag = lambda x: h - 0.25 * (1.0 - (2 * x / length) ** 2)
            mat = ("rug", "awning_red", "awning_teal", "rug")[(k + variant) % 4]
            P.poly(mat, [(x0, 0, sag(x0)), (x1, 0, sag(x1)), (x1, 0.02, sag(x1) - 1.3 - 0.2 * (k % 2)), (x0, 0.02, sag(x0) - 1.3)],
                   both=True)
        return P.out(c)

    return _p(c, name, build)


def grinding(c, variant=0):
    """A grinding place: metates (sloping stone slabs) with their manos, a basket of corn
    beside them, a little heap of meal."""
    name = "Pueblo Grinding %d" % variant

    def build(bm):
        P = Parts(bm)
        for k in range(2 + variant % 2):
            x = -0.7 + k * 0.75
            P.add("canyon_rock_ochre", cuboid, (x, 0, 0.18), (0.5, 0.8, 0.36))
            P.add("adobe_dark", cuboid, (x, -0.1, 0.42), (0.14, 0.22, 0.12))
        P.add("thatch", loft, [ring(bm, (1.3, 0.2), 0.32, 0.0, 10), ring(bm, (1.3, 0.2), 0.42, 0.45, 10)], cap_bottom=True)
        for j in range(5):
            P.add("awning_sun", blob, (1.3 + 0.12 * math.cos(j * 1.3), 0.2 + 0.12 * math.sin(j * 1.3), 0.45), 0.12, sz=1.5, subdiv=0)
        P.add("canvas_sun", blob, (-0.2, 0.75, 0.0), 0.35, sz=0.35, subdiv=1)
        return P.out(c)

    return _p(c, name, build)


def corn_heap(c, variant=0):
    """A heap of dried corn on a blanket, ready to be shelled."""
    name = "Pueblo Corn Heap %d" % variant

    def build(bm):
        P = Parts(bm)
        P.poly("rug", [(-1.0, -0.8, 0.03), (1.0, -0.8, 0.03), (1.0, 0.8, 0.03), (-1.0, 0.8, 0.03)])
        for k in range(14):
            a = k * 2.399 + variant
            r = 0.6 * math.sqrt(k / 14)
            P.add(("awning_sun", "awning_red", "terracotta")[k % 3], blob, (r * math.cos(a), r * math.sin(a), 0.12 + 0.18 * (1 - r / 0.6)),
                  0.11, sx=1.0, sy=1.0, sz=1.6, subdiv=0)
        return P.out(c)

    return _p(c, name, build)
