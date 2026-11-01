# Hearthglow's finer Christmas things (review-snow_region 11, Nov 1): a grand snowman
# for the street.
# SPDX-License-Identifier: MIT
#
# Same rules as props.py: each prop is one mesh built once (Course.proto) and placed as
# copies, all original designs. (Their own file, so the courses built from
# hearthglow_props.py stay in sync: the sync rule.)

import math

from course_kit import Vector, bmesh
from hearthglow_props import SNOW, Parts, _p
from props import blob, loft, ring, tube


def _cone(bm, base, tip, r, segs=8):
    """A cone from base to tip (a carrot nose)."""
    b, t = Vector(base), Vector(tip)
    d = t - b
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=0.0, depth=d.length)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    for v in res["verts"]:
        v.co = b + d / 2 + q @ v.co


def grand_snowman(c, variant=0):
    """A grand snowman (note 5: "a high fidelity snowman here facing the road"): three
    smooth packed balls, a coal smile and coal eyes, a long carrot nose, coal buttons,
    twig arms with forked fingers (one waving), a knitted scarf with its tails blowing, red
    mittens, a top hat with a holly sprig. About 5.5 m tall; it faces -Y; its base sunk."""
    name = "Grand Snowman %d" % variant

    def build(bm):
        k = Parts(bm)
        balls = ((0.95, 1.35), (2.85, 1.0), (4.3, 0.72))
        k.add(SNOW, lambda bm: [blob(bm, (0, 0, z), r, sz=0.94, subdiv=3) for z, r in balls])
        hz, hr = balls[2]

        def coal(bm):
            for sx in (-1, 1):  # (eyes)
                blob(bm, (sx * 0.24, -hr * 0.88, hz + 0.18), 0.09, sy=0.6, subdiv=1)
            for i in range(7):  # (a smile)
                a = math.pi * (0.2 + 0.6 * i / 6)
                x, z = -0.34 * math.cos(a), hz - 0.12 - 0.17 * math.sin(a)
                y = -math.sqrt(max(0.0, hr * hr - x * x - (z - hz) ** 2)) - 0.01
                blob(bm, (x, y, z), 0.05, subdiv=1)
            for z, r in ((3.3, 0.11), (2.85, 0.12), (2.4, 0.11), (1.55, 0.13), (1.0, 0.13)):  # (buttons)
                ball = balls[1] if z > 2.0 else balls[0]
                y = -math.sqrt(max(0.0, ball[1] ** 2 - (z - ball[0]) ** 2)) * 0.97
                blob(bm, (0, y, z), r, sy=0.6, subdiv=1)
        k.add("ship_hull", coal)
        k.add("carrot", lambda bm: _cone(bm, (0, -hr * 0.85, hz), (0.05, -hr - 0.75, hz - 0.12), 0.12))

        def arms(bm):
            # (left arm out and down; right arm up, waving)
            for sx, up in ((-1, -0.3), (1, 1.0)):
                sh = (sx * 0.85, 0, 3.05)
                el = (sx * 1.7, -0.1, 3.05 + 0.55 * up)
                hd = (sx * 2.35, -0.15, 3.1 + 1.25 * up)
                tube(bm, [sh, el, hd], [0.09, 0.07, 0.055], n=6)
                for f in (-0.5, 0.0, 0.5):
                    tip = (hd[0] + sx * 0.35 * math.cos(f), hd[1] - 0.05, hd[2] + 0.35 * math.sin(f) + 0.2 * up)
                    tube(bm, [hd, tip], [0.04, 0.025], n=5)
        k.add("log_bark", arms)

        def scarf(bm):
            loft(bm, [ring(bm, (0, 0), 0.82, 3.48, 14), ring(bm, (0, 0), 0.86, 3.68, 14), ring(bm, (0, 0), 0.74, 3.86, 14)],
                 cap_top=False)
            for dx, sway in ((0.28, 0.25), (0.5, 0.45)):  # (its tails, blowing out to one side)
                tube(bm, [(dx, -0.72, 3.55), (dx + sway * 0.6, -0.95, 3.05), (dx + sway, -1.0, 2.5)], [0.14, 0.13, 0.12], n=4)
        k.add(("awning_red", "awning_green")[variant % 2], scarf)

        def mittens(bm):
            for sx, up in ((-1, -0.3), (1, 1.0)):
                blob(bm, (sx * 2.35, -0.15, 3.1 + 1.25 * up), 0.2, sx=0.8, sz=1.15, subdiv=1)
        k.add(("awning_red", "awning_green")[(variant + 1) % 2], mittens)

        def hat(bm):
            z0 = hz + hr * 0.78
            loft(bm, [ring(bm, (0, 0), 0.82, z0, 16), ring(bm, (0, 0), 0.82, z0 + 0.1, 16)], cap_top=True, cap_bottom=True)
            loft(bm, [ring(bm, (0, 0), 0.52, z0 + 0.1, 16), ring(bm, (0, 0), 0.55, z0 + 1.05, 16)], cap_top=True)
        k.add("ship_hull", hat)
        k.box("awning_red", (0, 0, hz + hr * 0.78 + 0.28), (1.13, 1.13, 0.2))  # (its band)

        def holly(bm):
            z = hz + hr * 0.78 + 0.32
            for a in (-0.5, 0.5):
                blob(bm, (0.45 + 0.12 * math.cos(a), -0.32 + 0.12 * math.sin(a), z), 0.13, sx=1.6, sy=0.6, sz=0.4, subdiv=1)
        k.add("awning_green", holly)
        k.add("awning_red", lambda bm: [blob(bm, (0.42 + dx, -0.42, hz + hr * 0.78 + 0.35 + dz), 0.06, subdiv=1)
                                         for dx, dz in ((0, 0), (0.08, 0.06), (-0.06, 0.07))])
        return k.slots(c)

    return _p(c, name, build)
