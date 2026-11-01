# The Aurora Rift's part of the Snow Kingdom (review-snow_region 13, Nov 1): a crystal
# hut the rift folk built out of the crystals themselves, ice columns whose crystals grow
# out of them (not beside them).
# SPDX-License-Identifier: MIT
#
# Same rules as props.py: each prop is one mesh built once (Course.proto) and placed as
# copies, all original designs. (Their own file, so the course built from aurora_props.py
# stays in sync: the sync rule.)

import math

from aurora_props import CYAN, ICE, TEAL, VIOLET, shard, _lean
from course_kit import Vector, rnd
from hearthglow_props import Parts, _p
from props import blob, cuboid, loft, ring, tube


def column_at(variant, height, radius, t):
    """An ice column's middle and radius at t (0 foot, 1 top) as aurora_props.ice_column
    makes it (before its wobble)."""
    n = 10
    k = t * n
    cx, cy = 1.5 * math.sin(t * 3 + variant), 1.2 * math.cos(t * 2 + variant)
    r = radius * (1.25 - 0.55 * math.sin(math.pi * t)) * (1 + 0.15 * math.sin(k * 1.7 + variant))
    return cx, cy, r


def rift_column(c, variant=0, height=30.0, radius=4.0):
    """A natural column of ice, waisted and lumpy, its crystals growing out of it: each
    rooted well inside the column's surface where it stands (review-snow_region 13 note 5:
    "lets make sure all of the crystals are rooted in the pillar"). Origin at the floor."""
    name = "Rift Column %d %d" % (variant, int(height))

    def build(bm):
        k = Parts(bm)

        def col(bm):
            pts, radii = [], []
            n = 10
            for i in range(n + 1):
                t = i / n
                cx, cy, r = column_at(variant, height, radius, t)
                pts.append((cx, cy, -6 + (height + 12) * t))
                radii.append(r)
            tube(bm, pts, radii, n=10)
        k.add(ICE, col)

        def crystals(bm):
            for i in range(6):
                a = i * 1.9 + variant
                z = height * (0.12 + 0.14 * i)
                t = (z + 6) / (height + 12)
                cx, cy, r = column_at(variant, height, radius, t)
                # (its root 40% of the way in from the column's skin: always in the ice,
                # even where the column's lumpy)
                rr = r * 0.6
                bx, by = cx + rr * math.cos(a), cy + rr * math.sin(a)
                shard(bm, (bx, by, z), (math.cos(a), math.sin(a), 0.6), r * 0.4 + 2.5 + 2 * rnd(i + variant), 0.8, tip=0.3, twist=a)
                # (a smaller one beside it from the same root)
                shard(bm, (bx, by, z - 0.4), (math.cos(a + 0.5), math.sin(a + 0.5), 0.2), r * 0.4 + 1.2 + rnd(i * 3), 0.45,
                      tip=0.35, twist=a + 1)
        k.add((CYAN, VIOLET, TEAL)[variant % 3], crystals)

        def sockets(bm):
            # (the ice swollen round each root, so they're plainly grown out of it)
            for i in range(6):
                a = i * 1.9 + variant
                z = height * (0.12 + 0.14 * i)
                t = (z + 6) / (height + 12)
                cx, cy, r = column_at(variant, height, radius, t)
                blob(bm, (cx + r * 0.85 * math.cos(a), cy + r * 0.85 * math.sin(a), z + 0.2), 1.3, sx=1.0, sy=1.0, sz=1.3,
                     subdiv=1)
        k.add(ICE, sockets)
        return k.slots(c)

    return _p(c, name, build)


def crystal_hut(c, variant=0):
    """A home grown from the rift's crystals (review-snow_region 13 note 2: "a nice crystal
    hut ... like they built a home from the crystals here"): a ring of six-sided crystal
    pillars standing shoulder to shoulder for its walls, cyan, violet and teal, their
    points ragged at the eaves; a roof of long crystals leant together to a crown of
    them; the warm glow of the inside showing between the pillars; a doorway (-Y) between
    two tall pillars under a lintel crystal laid across them, a door of clear ice stood
    open; a step of rift stone; crystal lamps either side of it. About 9 m across, 10 m
    to its crown. Origin on the ground."""
    name = "Crystal Hut %d" % variant
    R = 3.6
    N = 26
    door = (-math.pi / 2, 0.55)  # (its doorway: the angle, half its width in radians)
    mats = (CYAN, VIOLET, TEAL)

    def build(bm):
        k = Parts(bm)
        # The floor: a low plinth of rift stone, a step out of the door.
        k.add("rift_stone", lambda bm: loft(bm, [ring(bm, (0, 0), R + 0.7, -0.6, 12), ring(bm, (0, 0), R + 0.6, 0.25, 12)],
                                             cap_top=True))
        k.add("rift_stone", lambda bm: cuboid(bm, (0, -R - 1.1, 0.0), (2.4, 1.0, 0.4)))
        # The glow inside, seen between the pillars.
        k.add("window_warm", lambda bm: loft(bm, [ring(bm, (0, 0), R - 0.55, 0.2, 14), ring(bm, (0, 0), R - 0.55, 3.6, 14)],
                                              cap_top=True))
        # The walls: pillars round the ring, the doorway left open.
        pillars = {m: [] for m in mats}
        for i in range(N):
            a = i * math.tau / N
            off = math.atan2(math.sin(a - door[0]), math.cos(a - door[0]))
            if abs(off) < door[1]:
                continue
            h = 3.4 + 1.1 * rnd(i * 3 + variant) + (1.6 if abs(abs(off) - door[1]) < 0.25 else 0.0)
            r = 0.46 + 0.12 * rnd(i * 5 + variant)
            lean = 0.05 + 0.05 * rnd(i * 7)
            pillars[mats[(i + variant) % 3]].append((R * math.cos(a), R * math.sin(a), a, h, r, lean))

        for m in mats:
            def walls(bm, m=m):
                for x, y, a, h, r, lean in pillars[m]:
                    shard(bm, (x, y, -0.4), _lean(a, 0, lean), h + 0.4, r, tip=0.18, twist=a)
            k.add(m, walls)
        # The lintel over the door, a long crystal laid across the two door pillars, and a
        # little one stood up on it.
        da = door[0]
        lx0 = R * math.cos(da - door[1] - 0.1)
        lx1 = R * math.cos(da + door[1] + 0.1)
        ly = R * math.sin(da) - 0.1
        k.add(VIOLET, lambda bm: [shard(bm, (lx0 - 0.4, ly, 3.75), (1, 0, 0.02), (lx1 - lx0) + 1.0, 0.36, n=6, tip=0.12),
                                  shard(bm, (0, ly, 4.0), (0, -0.1, 1), 1.6, 0.25, tip=0.3)])
        # The roof: long crystals leant together from the wall tops to the crown.
        def roof(bm, m):
            for i in range(14):
                if i % 3 != mats.index(m):
                    continue
                a = i * math.tau / 14 + 0.2
                base = Vector(((R - 0.2) * math.cos(a), (R - 0.2) * math.sin(a), 3.6))
                top = Vector((0.35 * math.cos(a + 2.0), 0.35 * math.sin(a + 2.0), 8.1 + 0.6 * rnd(i)))
                shard(bm, tuple(base), tuple(top - base), (top - base).length + 0.8, 0.42, tip=0.25, twist=a)
        for m in mats:
            k.add(m, lambda bm, m=m: roof(bm, m))
        # The crown: a cluster of crystals up out of the roof's peak.
        k.add(CYAN, lambda bm: [shard(bm, (0, 0, 7.4), (0.05, 0.03, 1), 3.0, 0.5, tip=0.25),
                                *[shard(bm, (0.3 * math.cos(a), 0.3 * math.sin(a), 7.5), _lean(a, 0, 0.45), 1.8, 0.28, tip=0.3)
                                  for a in (0.4, 2.5, 4.6)]])
        # The door: a slab of clear ice stood open on the left.
        k.add("lake_ice", lambda bm: cuboid(bm, (lx0 + 0.35, ly - 0.55, 1.7), (0.15, 1.2, 3.3), rot=0.25))
        # Lamps: a glowing crystal on a post of stone either side of the step.
        for sd in (-1, 1):
            k.add("rift_stone", lambda bm, sd=sd: loft(bm, [ring(bm, (sd * 1.9, -R - 1.4), 0.22, -0.3, 6),
                                                           ring(bm, (sd * 1.9, -R - 1.4), 0.18, 1.4, 6)], cap_top=True))
            k.add("crystal_gold", lambda bm, sd=sd: shard(bm, (sd * 1.9, -R - 1.4, 1.3), (0, 0, 1), 0.9, 0.2, tip=0.35))
        # A garden of little crystals beside the path.
        def garden(bm, m):
            for i in range(9):
                if i % 3 != mats.index(m):
                    continue
                sd = 1 if i % 2 else -1
                x, y = sd * (2.6 + 0.8 * rnd(i)), -R - 0.4 - 1.6 * rnd(i * 3)
                shard(bm, (x, y, -0.2), _lean(i, 0, 0.25), 0.7 + 0.8 * rnd(i * 5), 0.14, tip=0.3, twist=i)
        for m in mats:
            k.add(m, lambda bm, m=m: garden(bm, m))
        # Snow drifted on the plinth round the back.
        k.add("rift_snow", lambda bm: [blob(bm, ((R + 0.4) * math.cos(a), (R + 0.4) * math.sin(a), 0.25), 0.8, sx=1.4,
                                            sy=0.9, sz=0.4, subdiv=1) for a in (0.3, 1.2, 2.3, 3.4)])
        return k.slots(c)

    return _p(c, name, build)


def stump_seat(c, variant=0):
    """A stump to sit on round a fire (review-snow_region 13 note 7): a sawn round of log,
    bark sides, its top whole end grain, a few roots out into the snow."""
    import ice_homes as ih

    def build(P, bm):
        h = 0.55 + 0.12 * (variant % 2)
        r = 0.42 + 0.06 * (variant % 3)
        P.add("giant_bark", lambda: tube(bm, [(0, 0, -0.2), (0, 0, 0.1), (0, 0, h)], [r * 1.2, r, r * 0.97], n=12))
        P.add(ih.LOGS, lambda: loft(bm, [ring(bm, (0, 0), r * 0.94, h + 0.005, 12), ring(bm, (0, 0), r * 0.94, h + 0.01, 12)],
                                   cap_top=True))
        for i in range(4):
            a = i * math.tau / 4 + 0.5 * variant
            P.add("giant_bark", lambda a=a: tube(bm, [(math.cos(a) * r * 0.7, math.sin(a) * r * 0.7, 0.12),
                                                      (math.cos(a) * (r + 0.4), math.sin(a) * (r + 0.4), -0.12)], [0.13, 0.06], n=6))

    return ih._p(c, "Stump Seat %d" % variant, build)
