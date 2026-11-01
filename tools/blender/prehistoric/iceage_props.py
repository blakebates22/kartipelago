# The ice age in the Snow Kingdom's summit (review-snow_region 9, Nov 1): bone huts of
# hides and tusks, hunters' hide tents and drying racks, waymark cairns, a hot spring in
# the snow, a mammoth's skull frozen in the lake.
# SPDX-License-Identifier: MIT
#
# Same rules as props.py: each prop is one mesh built once (Course.proto) and placed as
# copies, chunky and low-poly, all original designs. (Their own file, so the courses
# built from summit_props.py stay in sync: the sync rule.)

import math

from mathutils import Vector

from course_kit import rnd
from props import _faces, blob, cuboid, loft, ring, tube
from summit_props import BONE, ROCK, SNOW, STONE, _cap, _p

def bone_hut(c, variant=0):
    """An ice-age dwelling (review-snow_region 9 note 22: "stone huts ... that matches more
    ice age era"): a low dry-stone drum, a dome of hides over it, two great tusk hoops
    crossed over the dome holding them down, a hide porch with a tusk arch and a flap (-Y),
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
        ivory = _faces(bm, k2)
        k2 = len(bm.faces)
        # The doorway (-Y): a short hide-covered porch out of the drum, a tusk arch round its
        # mouth, a hide flap hung across most of it and tied back, a warm glow from the
        # fire inside past it, a stone step (review-snow_region 10 note 3: "we need to
        # improve the doors on these huts. they look terrible": it was a flat glow box).
        y0, y1 = -(R - 0.7), -(R + 0.75)
        W, HH, Z0, M = 1.2, 2.45, -0.3, 10

        def arch(w, h, y):
            return [bm.verts.new((w * math.cos(j * math.pi / M), y, Z0 + h * math.sin(j * math.pi / M))) for j in range(M + 1)]

        def face(vs, out):
            f = bm.faces.new(vs)
            f.normal_update()
            if f.normal.dot(Vector(out)) < 0:
                f.normal_flip()
            return f

        out0, out1 = arch(W, HH, y0), arch(W, HH, y1)
        in1, in0 = arch(W - 0.24, HH - 0.22, y1), arch(W - 0.24, HH - 0.22, y0 + 0.2)
        for j in range(M):
            a = (j + 0.5) * math.pi / M
            face([out0[j], out0[j + 1], out1[j + 1], out1[j]], (math.cos(a), 0, math.sin(a)))
        porch = _faces(bm, k2)
        k2b = len(bm.faces)
        for j in range(M):
            a = (j + 0.5) * math.pi / M
            face([out1[j], out1[j + 1], in1[j + 1], in1[j]], (0, -1, 0))  # (the frame round its mouth)
        frame = _faces(bm, k2b)
        k2c = len(bm.faces)
        for j in range(M):
            a = (j + 0.5) * math.pi / M
            face([in1[j], in1[j + 1], in0[j + 1], in0[j]], (-math.cos(a), 0, -math.sin(a)))  # (inside it)
        face(list(in0), (0, -1, 0))  # (the dark back of it)
        dark = _faces(bm, k2c)
        # The flap: hung from the frame's top left, across to just past the middle, its
        # foot tied back to the left post, so a wedge of the inside shows on the right.
        k2d = len(bm.faces)
        yf = y1 + 0.1
        top = [(in1[j].co.x * 0.98, yf, in1[j].co.z - 0.02) for j in range(M // 2 - 1, M + 1)]
        flap = [bm.verts.new(p) for p in top + [(-(W - 0.3), yf - 0.04, Z0 + 0.35), (-0.15, yf - 0.12, Z0 + 0.7),
                                               (0.22, yf - 0.06, Z0 + 1.7)]]
        face(flap, (0, -1, 0))
        flaps = _faces(bm, k2d)
        k2e = len(bm.faces)
        glow = [bm.verts.new(p) for p in ((0.1, y0 + 0.16, Z0 + 0.3), (W - 0.45, y0 + 0.16, Z0 + 0.3),
                                         (W - 0.5, y0 + 0.16, Z0 + 1.4), (0.3, y0 + 0.16, Z0 + 1.6))]
        face(glow, (0, -1, 0))
        glows = _faces(bm, k2e)
        k2f = len(bm.faces)
        # (A bone toggle on the tie, and the tusk arch round the porch's mouth.)
        blob(bm, (-(W - 0.32), yf - 0.12, Z0 + 0.45), 0.12, sx=0.6, sz=1.6, subdiv=1)
        for sd in (-1, 1):
            tube(bm, [(sd * 1.32, y1 - 0.08, -0.4), (sd * 1.38, y1 - 0.14, 1.1), (sd * 1.08, y1 - 0.16, 2.2),
                      (sd * 0.15, y1 - 0.1, 2.75)], [0.2, 0.18, 0.15, 0.1], n=8)
        ivory += _faces(bm, k2f)
        k2g = len(bm.faces)
        cuboid(bm, (0, y1 - 0.45, -0.12), (1.9, 0.9, 0.3), rot=0.04)  # (the step)
        stone += _faces(bm, k2g)
        k2h = len(bm.faces)
        _cap(bm, (0, (y0 + y1) / 2 - 0.15, Z0 + HH + 0.05), 0.9, h=0.22, sx=1.25, subdiv=2)
        porch_snow = _faces(bm, k2h)
        k4 = len(bm.faces)
        _cap(bm, (0, 0, 1.0 + H - 0.15), 1.7, h=0.45, subdiv=2)
        snow = _faces(bm, k4)
        return [(c.lib(STONE), stone), (c.lib("mammoth_fur"), hide + porch), (c.lib("bone_ivory"), ivory),
                (c.lib("log_bark"), frame), (c.lib("ship_hull"), dark), (c.lib("painted_hide"), flaps),
                (c.lib("fire_glow"), glows), (c.lib(SNOW), snow + porch_snow)]

    return _p(c, name, build)


def _pot(bm, x, y, r, h):
    """A coil-built clay pot: a round belly, a narrow neck, a lip (lathed, low-poly)."""
    prof = [(0.55, -0.05), (0.95, 0.25), (1.0, 0.5), (0.8, 0.78), (0.55, 0.9), (0.62, 1.0), (0.48, 0.97)]
    rings = [ring(bm, (x, y), r * pr_, h * pz, 9) for pr_, pz in prof]
    loft(bm, rings, cap_top=True, cap_bottom=True)


def _bucket(bm, x, y, r, h):
    """A stave bucket: a short tapered drum, open, a rope bail over it."""
    loft(bm, [ring(bm, (x, y), r * 0.85, -0.05, 10), ring(bm, (x, y), r, h, 10), ring(bm, (x, y), r * 0.9, h, 10),
              ring(bm, (x, y), r * 0.78, 0.12, 10)], cap_top=True, cap_bottom=True)


def _kit():
    import ice_homes  # (the carvers' kit: logs with whole end grain on their sawn ends)
    return ice_homes


def camp_pots(c, variant=0):
    """Coil-built clay pots, one big and one or two small, standing together (review-
    snow_region 10 note 4). Origin on the ground under them; set each on its own spot."""
    ih = _kit()
    name = "Camp Pots %d" % variant

    def build(P, bm):
        P.add("terracotta", lambda: _pot(bm, 0.0, 0.0, 0.4, 0.9))
        P.add("terracotta", lambda: _pot(bm, 0.62, 0.3, 0.27, 0.58))
        if variant % 2:
            P.add("terracotta", lambda: _pot(bm, -0.25, 0.65, 0.22, 0.48))

    return ih._p(c, name, build)


def camp_bucket(c):
    """A stave bucket with its rope bail."""
    ih = _kit()

    def build(P, bm):
        P.add("barrel_wood", lambda: _bucket(bm, 0.0, 0.0, 0.34, 0.6))
        P.add("iron", lambda: loft(bm, [ring(bm, (0, 0), 0.36, 0.42, 12), ring(bm, (0, 0), 0.36, 0.48, 12)], cap_top=False))
        P.add("log_bark", lambda: tube(bm, [(-0.33, 0, 0.55), (-0.2, 0, 0.85), (0.2, 0, 0.85), (0.33, 0, 0.55)], 0.025, n=4))

    return ih._p(c, "Camp Bucket", build)


def camp_woodpile(c):
    """A stack of split logs on sleepers, their cut ends whole end grain (review-snow_region
    12 note 6: "lets improve the quality of these logs. make sure the textures at the end of
    the logs are right"): the carvers' woodpile."""
    ih = _kit()
    return ih._p(c, "Camp Woodpile", lambda P, bm: ih.woodpile(P, bm, 0.0, 0.0, 0.0, n=4))


def camp_block(c):
    """A chopping block (a sawn round of log, end grain on top), a stone axe sunk in it, a
    bone shovel and a spear leant against it."""
    ih = _kit()

    def build(P, bm):
        ih._log(P, bm, (0.0, 0.0, 0.75), (0.0, 0.0, -0.1), 0.42, 0)
        P.add("log_bark", lambda: tube(bm, [(0.05, -0.05, 0.75), (0.35, -0.3, 1.45)], [0.045, 0.04], n=6))  # (the axe's haft)
        P.add(STONE, lambda: blob(bm, (0.06, -0.04, 0.82), 0.16, sx=1.4, sy=0.55, sz=0.9, subdiv=2))
        P.add("log_bark", lambda: tube(bm, [(0.55, 0.15, 0.0), (0.42, 0.05, 1.5)], [0.045, 0.04], n=6))  # (the shovel's)
        P.add("bone_ivory", lambda: cuboid(bm, (0.57, 0.17, 0.25), (0.34, 0.07, 0.46), tilt=(0.0, 0.08)))
        P.add("log_bark", lambda: tube(bm, [(-0.45, 0.35, 0.0), (-0.3, 0.2, 2.3)], [0.04, 0.03], n=5))  # (a spear)
        P.add(STONE, lambda: blob(bm, (-0.3, 0.2, 2.42), 0.08, sx=0.6, sy=0.6, sz=2.0, subdiv=1))

    return ih._p(c, "Camp Chopping Block", build)


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


def spring_edge(r, a):
    """The hot spring's water's edge at angle a: a rounded, lopsided natural pool."""
    return r * (1.0 + 0.16 * math.sin(2 * a + 0.6) + 0.08 * math.sin(3 * a + 1.7))


def hot_spring(c, r=7.0):
    """A hot spring in the snow (review-snow_region 10 note 11: "this needs to look more
    like a hot spring"; it was a neat ring of stones round flat water): a lopsided natural
    pool in a bowl of white travertine, orange mineral staining at the waterline, the deep
    blue of its vent in the middle, a little upper pool spilling into it over a mineral
    lip, a bank of boulders on its far side only, snow melted off in a ring round it, steam
    rising in veils (spring_steam). Origin at the water."""
    name = "Hot Spring %.0f" % r
    n = 28

    def build(bm):
        def edge(k, f, z, dr=0.0):
            a = k * math.tau / n
            e = spring_edge(r, a) * f + dr
            return bm.verts.new((e * math.cos(a), e * math.sin(a), z))

        # The bowl: thawed ground falling to a travertine shelf, the stained waterline,
        # then down under the water.
        k0 = len(bm.faces)
        melt = [edge(k, 1.0, 0.02, 1.5 + 0.3 * math.sin(k * 1.3)) for k in range(n)]
        bank = [edge(k, 1.0, 0.08, 0.9) for k in range(n)]
        loft(bm, [melt, bank], cap_top=False)
        thaw = _faces(bm, k0)
        k1 = len(bm.faces)
        shelf = [edge(k, 1.0, 0.04, 0.35) for k in range(n)]
        loft(bm, [bank, shelf], cap_top=False)
        trav = _faces(bm, k1)
        k2 = len(bm.faces)
        stain = [edge(k, 1.0, -0.02) for k in range(n)]
        deep = [edge(k, 0.8, -0.9) for k in range(n)]
        loft(bm, [shelf, stain, deep], cap_top=True)
        rim = _faces(bm, k2)
        k3 = len(bm.faces)
        bm.faces.new([edge(k, 0.995, -0.06) for k in range(n)])
        water = _faces(bm, k3)
        # The vent: a deep blue eye in it, off the middle.
        k4 = len(bm.faces)
        bm.faces.new(ring(bm, (-r * 0.12, r * 0.08), r * 0.34, -0.04, 14, rx=r * 0.4))
        vent = _faces(bm, k4)
        # The upper pool, spilling in over a stained lip (+X).
        k5 = len(bm.faces)
        ux, uy, ur = r * 1.12, -r * 0.35, r * 0.34
        loft(bm, [ring(bm, (ux, uy), ur + 1.0, -0.1, 12), ring(bm, (ux, uy), ur + 0.25, 0.5, 12, phase=0.1),
                  ring(bm, (ux, uy), ur, 0.42, 12)], cap_top=False)
        trav += _faces(bm, k5)
        k6 = len(bm.faces)
        bm.faces.new(ring(bm, (ux, uy), ur + 0.02, 0.38, 12))
        water += _faces(bm, k6)
        k7 = len(bm.faces)
        # (the spill: a sloped tongue of mineral down into the pool)
        vs = [bm.verts.new(p) for p in ((ux - ur * 0.9, uy - 0.6, 0.42), (ux - ur * 0.9, uy + 0.6, 0.42),
                                       (ux - ur - 1.3, uy + 0.9, -0.04), (ux - ur - 1.3, uy - 0.9, -0.04))]
        bm.faces.new(vs)
        rim += _faces(bm, k7)
        # Boulders banked up on its far side (-X, -Y), big and small, snow on the big ones.
        k8 = len(bm.faces)
        caps = []
        for i in range(11):
            a = 2.3 + i * 0.22 + 0.1 * rnd(i * 5)
            e = spring_edge(r, a) + 0.9 + 0.9 * rnd(i * 7 + 2)
            br = 0.55 + 1.05 * rnd(i * 3 + 1) * (1.0 - abs(i - 5) / 7.0)
            x, y = e * math.cos(a), e * math.sin(a)
            blob(bm, (x, y, br * 0.25), br, sx=1.25, sy=1.0, sz=0.8, subdiv=1)
            if br > 0.9:
                caps.append((x, y, br * 0.25 + br * 0.72, br * 0.65))
        stones = _faces(bm, k8)
        k9 = len(bm.faces)
        for x, y, z, cr in caps:
            _cap(bm, (x, y, z), cr, h=0.2)
        snow = _faces(bm, k9)
        return [(c.lib("thaw_grass"), thaw), (c.lib("sinter"), trav), (c.lib("sinter_rim"), rim),
                (c.lib("hot_spring"), water), (c.lib("hot_pool"), vent), (c.lib(STONE), stones), (c.lib(SNOW), snow)]

    return _p(c, name, build)


def spring_steam(c, r=7.0):
    """The hot spring's steam, rising in veils off it (only seen: set role="visual")."""
    name = "Hot Spring Steam %.0f" % r
    ux, uy, ur = r * 1.12, -r * 0.35, r * 0.34

    def build(bm):
        k10 = 0
        # Open, wobbly, tapering columns off the water.
        for j, (x, y, sr, h) in enumerate(((-r * 0.12, r * 0.08, r * 0.45, 4.5), (r * 0.4, -r * 0.3, r * 0.3, 3.2),
                                           (ux, uy, ur * 0.8, 2.6))):
            rings = []
            for t in range(4):
                tt = t / 3
                rg = ring(bm, (x + 0.4 * math.sin(j + tt * 2), y + 0.3 * math.cos(j + tt * 3)), sr * (1.0 - 0.45 * tt),
                          0.1 + h * tt, 10, phase=j)
                rings.append(rg)
            loft(bm, rings, cap_top=False)
        steam = _faces(bm, k10)
        return [(c.lib("steam_mist"), steam)]

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
