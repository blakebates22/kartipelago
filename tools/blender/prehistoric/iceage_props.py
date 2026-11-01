# The ice age in the Snow Kingdom's summit (review-snow_region 9, Nov 1): bone huts of
# hides and tusks, hunters' hide tents and drying racks, waymark cairns, a hot spring in
# the snow, a mammoth's skull frozen in the lake.
# SPDX-License-Identifier: MIT
#
# Same rules as props.py: each prop is one mesh built once (Course.proto) and placed as
# copies, chunky and low-poly, all original designs. (Their own file, so the courses
# built from summit_props.py stay in sync: the sync rule.)

import math

from course_kit import rnd
from props import _faces, blob, cuboid, loft, ring, tube
from summit_props import BONE, ROCK, SNOW, STONE, _cap, _p

def bone_hut(c, variant=0):
    """An ice-age dwelling (review-snow_region 9 note 22: "stone huts ... that matches more
    ice age era"): a low dry-stone drum, a dome of hides over it, two great tusk hoops
    crossed over the dome holding them down, a tusk arch round a fire-lit doorway (-Y),
    snow on its crown. About 7 m across, 5 m high; its base sunk a metre (set level on
    its pad, nothing floating)."""
    name = "Bone Hut %d" % variant
    R = 3.3 + 0.2 * (variant % 2)
    N = 16

    def build(bm):
        # The stone drum: sunk 1 m, 0.9 m above ground, a slight batter.
        k0 = len(bm.faces)
        drum = [ring(bm, (0, 0), R + 0.25, -1.0, N), ring(bm, (0, 0), R + 0.15, 0.9, N), ring(bm, (0, 0), R - 0.1, 1.0, N)]
        loft(bm, drum, cap_top=False)
        stone = _faces(bm, k0)
        # The hide dome, from the drum's lip up.
        k1 = len(bm.faces)
        rings = [drum[-1]]
        H = 3.6 + 0.3 * (variant % 3)
        for t in (0.2, 0.4, 0.6, 0.78, 0.92):
            a = t * math.pi / 2
            rr = (R - 0.1) * math.cos(a)
            rg = ring(bm, (0, 0), rr, 1.0 + H * math.sin(a), N, phase=0.0)
            for i, v in enumerate(rg):  # (sagging between the hoops)
                v.co.x *= 1.0 - 0.04 * abs(math.sin(2 * i * math.tau / N))
                v.co.y *= 1.0 - 0.04 * abs(math.sin(2 * i * math.tau / N))
            rings.append(rg)
        loft(bm, rings, cap_top=True)
        hide = _faces(bm, k1)
        # Two tusk hoops crossed over the dome.
        k2 = len(bm.faces)
        for h in (math.pi / 4, -math.pi / 4):
            path = []
            for j in range(13):
                ang = (j / 12.0) * math.pi  # (side to side over the top)
                x = (R + 0.12) * math.cos(ang)
                zz = 0.7 + (H + 0.35) * math.sin(ang)
                path.append((x * math.cos(h), x * math.sin(h), zz))
            tube(bm, path, [0.22] * len(path), n=8)
        # The doorway's tusk arch (-Y), and its fire-lit opening.
        door = []
        for sd in (-1, 1):
            door.append([(sd * 1.0, -R - 0.15, 0.2), (sd * 1.05, -R - 0.35, 1.4), (sd * 0.75, -R - 0.4, 2.35),
                         (sd * 0.12, -R - 0.3, 2.75)])
        for pth in door:
            tube(bm, pth, [0.2, 0.18, 0.15, 0.1], n=8)
        ivory = _faces(bm, k2)
        k3 = len(bm.faces)
        cuboid(bm, (0, -R + 0.05, 1.25), (1.5, 0.5, 2.1))
        glow = _faces(bm, k3)
        k4 = len(bm.faces)
        _cap(bm, (0, 0, 1.0 + H - 0.15), 1.7, h=0.45, subdiv=2)
        snow = _faces(bm, k4)
        return [(c.lib(STONE), stone), (c.lib("mammoth_fur"), hide), (c.lib("bone_ivory"), ivory),
                (c.lib("fire_glow"), glow), (c.lib(SNOW), snow)]

    return _p(c, name, build)


def hide_tent(c, variant=0):
    """A hunters' hide tent: a cone of painted hides on poles, the poles crossed out of its
    top, the flap open (-Y) on a warm glow, stones on its skirt. About 5 m tall; its skirt
    sunk into the snow."""
    name = "Hide Tent %d" % variant
    R = 2.4 + 0.3 * (variant % 2)
    H = 4.6 + 0.4 * (variant % 2)
    N = 10

    def build(bm):
        k0 = len(bm.faces)
        base = ring(bm, (0, 0), R, -0.4, N, phase=math.pi / N)
        mid = ring(bm, (0, 0), R * 0.55, H * 0.5, N, phase=math.pi / N)
        top = ring(bm, (0, 0), 0.22, H - 0.3, N, phase=math.pi / N)
        loft(bm, [base, mid, top], cap_top=True)
        hide = _faces(bm, k0)
        k1 = len(bm.faces)
        for i in range(6):
            a = i * math.tau / 6 + 0.2
            tube(bm, [(R * 0.98 * math.cos(a), R * 0.98 * math.sin(a), -0.3),
                      (-0.55 * math.cos(a), -0.55 * math.sin(a), H + 0.9)], [0.07, 0.05], n=5)
        poles = _faces(bm, k1)
        k2 = len(bm.faces)
        vs = [bm.verts.new(p) for p in ((-0.55, -R * 0.93, 0.0), (0.55, -R * 0.93, 0.0), (0.12, -R * 0.62, 1.6),
                                        (-0.12, -R * 0.62, 1.6))]
        bm.faces.new(vs)
        glow = _faces(bm, k2)
        k3 = len(bm.faces)
        for i in range(8):
            a = i * math.tau / 8 + 0.5
            if math.sin(a) < -0.85:
                continue  # (the door)
            blob(bm, ((R + 0.1) * math.cos(a), (R + 0.1) * math.sin(a), 0.05), 0.32, sx=1.2, sz=0.7, subdiv=1)
        stones = _faces(bm, k3)
        return [(c.lib("painted_hide"), hide), (c.lib("log_bark"), poles), (c.lib("fire_glow"), glow), (c.lib(STONE), stones)]

    return _p(c, name, build)


def hide_rack(c):
    """A drying rack: two A-frames of poles, a pole across, hides hung over it."""
    name = "Hide Rack"

    def build(bm):
        k0 = len(bm.faces)
        for sx in (-1.8, 1.8):
            for sy in (-0.7, 0.7):
                tube(bm, [(sx, sy, -0.3), (sx, 0, 2.3)], [0.07, 0.06], n=5)
        tube(bm, [(-2.1, 0, 2.2), (2.1, 0, 2.2)], [0.07, 0.07], n=5)
        poles = _faces(bm, k0)
        k1 = len(bm.faces)
        for x0, w, drop in ((-1.3, 1.1, 1.3), (0.1, 1.2, 1.5), (1.25, 0.9, 1.1)):
            for sd in (-1, 1):
                vs = [bm.verts.new(p) for p in ((x0 - w / 2, 0.02 * sd, 2.25), (x0 + w / 2, 0.02 * sd, 2.25),
                                                (x0 + w / 2 - 0.1, 0.25 * sd, 2.25 - drop),
                                                (x0 - w / 2 + 0.1, 0.25 * sd, 2.25 - drop))]
                bm.faces.new(vs if sd > 0 else list(reversed(vs)))
        hides = _faces(bm, k1)
        return [(c.lib("log_bark"), poles), (c.lib("painted_hide"), hides)]

    return _p(c, name, build)


def cairn(c, variant=0):
    """A waymark cairn: flat stones stacked, a cap of snow (about 2.5 m)."""
    name = "Cairn %d" % variant

    def build(bm):
        z = -0.3
        for k in range(5):
            r = 1.0 - 0.15 * k
            h = 0.32 + 0.06 * rnd(k + variant)
            blob(bm, (0.12 * (rnd(k * 7 + variant) - 0.5), 0.12 * (rnd(k * 3 + variant) - 0.5), z + h), r, sx=1.0 + 0.2 * rnd(k),
                 sy=0.9, sz=h / r, subdiv=1)
            z += 2 * h * 0.85
        stones = _faces(bm, 0)
        k0 = len(bm.faces)
        _cap(bm, (0, 0, z + 0.05), 0.5, 0.18)
        return [(c.lib(STONE), stones), (c.lib(SNOW), _faces(bm, k0))]

    return _p(c, name, build)


def hot_spring(c, r=7.0):
    """A hot spring in the snow (review-snow_region 9 note 24: "maybe a hot spring
    pool"): a ring of round boulders, steaming turquoise water sunk a little inside,
    a flat stone to sit on; snow drifted on the stones. Origin at the water."""
    name = "Hot Spring %.0f" % r

    def build(bm):
        k0 = len(bm.faces)
        n = 18
        outer = ring(bm, (0, 0), r + 1.6, -1.2, n, rx=(r + 1.6) * 1.15)
        lip = ring(bm, (0, 0), r + 0.2, 0.35, n, rx=(r + 0.2) * 1.15)
        inner = ring(bm, (0, 0), r - 0.2, -0.4, n, rx=(r - 0.2) * 1.15)
        loft(bm, [outer, lip, inner], cap_top=False)
        basin = _faces(bm, k0)
        k1 = len(bm.faces)
        bm.faces.new(ring(bm, (0, 0), r - 0.05, -0.05, n, rx=(r - 0.05) * 1.15))
        water = _faces(bm, k1)
        k2 = len(bm.faces)
        m = 22
        for i in range(m):
            a = i * math.tau / m
            br = 0.7 + 0.35 * rnd(i * 3 + 1)
            blob(bm, ((r + 0.4) * 1.15 * math.cos(a), (r + 0.4) * math.sin(a), 0.25 + 0.2 * rnd(i)), br, sx=1.2, sy=1.0,
                 sz=0.75, subdiv=1)
        cuboid(bm, (r * 0.95, -1.5, 0.45), (2.4, 1.6, 0.5), rot=0.3)
        stones = _faces(bm, k2)
        k3 = len(bm.faces)
        for i in range(0, m, 3):
            a = i * math.tau / m + 0.1
            _cap(bm, ((r + 0.5) * 1.15 * math.cos(a), (r + 0.5) * math.sin(a), 0.75 + 0.2 * rnd(i)), 0.6, h=0.2)
        snow = _faces(bm, k3)
        return [(c.lib(ROCK), basin), (c.lib("hot_spring"), water), (c.lib(STONE), stones), (c.lib(SNOW), snow)]

    return _p(c, name, build)


def frozen_skull(c):
    """A mammoth's skull frozen in the lake (review-snow_region 9 note 21): the crown, the
    brow and the eye sockets breaking the ice, the face sloping down under it, its two
    tusks curling up out of the ice ahead, frost on top. Facing +X; origin at the ice
    (everything under z 0 is in the ice). About 6 m high, 14 m tip to crown."""
    name = "Frozen Mammoth Skull"

    def build(bm):
        blob(bm, (0, 0, 1.2), 3.0, sx=0.8, sy=0.9, sz=1.15, subdiv=3)
        for side in (-1, 1):
            blob(bm, (-0.2, side * 1.05, 3.9), 1.45, sx=0.9, sy=0.8, sz=0.7, subdiv=2)  # the crown's domes
            blob(bm, (1.6, side * 1.85, 2.2), 0.8, sx=1.0, sy=0.9, sz=0.45, subdiv=2)  # brow ridge
            tube(bm, [(1.6, side * 1.35, 0.2), (2.8, side * 1.6, -0.5), (3.8, side * 1.85, -1.2)], [1.05, 0.95, 0.85], n=12)
        blob(bm, (1.8, 0, -0.4), 2.1, sx=0.72, sy=1.0, sz=1.0, subdiv=3)
        bone = _faces(bm, 0)
        k0 = len(bm.faces)
        for side in (-1, 1):
            blob(bm, (2.0, side * 1.75, 1.6), 0.68, sx=0.55, sy=0.9, sz=0.85, subdiv=1)  # eye sockets
        blob(bm, (3.0, 0, 0.9), 0.6, sx=0.45, sy=1.0, sz=1.5, subdiv=1)
        dark = _faces(bm, k0)
        k1 = len(bm.faces)
        # The tusks: down from the sockets under the ice, out ahead, curling up out of it.
        for side in (-1, 1):
            pts, radii = [], []
            m = 24
            for k in range(m + 1):
                t = k / m
                a = t * math.pi * 1.15
                x = 3.8 + 5.2 * math.sin(a) + 2.0 * t
                z = -1.4 + 4.8 * (1 - math.cos(a)) * 0.5 + 1.2 * t
                y = side * (1.9 + 2.6 * t - 1.6 * t * t)
                pts.append((x, y, z))
                radii.append(0.85 - 0.65 * t ** 1.2)
            tube(bm, pts, radii, n=12)
        ivory = _faces(bm, k1)
        k2 = len(bm.faces)
        _cap(bm, (-0.2, 0, 4.6), 2.0, 0.45, sx=1.0, sy=1.3, subdiv=2)
        # (a drift against its back, where the wind left it)
        _cap(bm, (-2.4, 0, 0.0), 2.6, 0.7, sx=1.0, sy=1.4, subdiv=2)
        return [(c.lib(BONE), bone + ivory), (c.lib("ship_hull"), dark), (c.lib(SNOW), _faces(bm, k2))]

    return _p(c, name, build)
