# Frostveil's finer pieces (review-snow_region 12, Nov 1): the ice dragon on its carved
# pedestal in the Frost Cove, and the Frost Chapel's great wooden door.
# SPDX-License-Identifier: MIT
#
# Same rules as props.py: each prop is one mesh built once (Course.proto) and placed as
# copies, all original designs. (Their own file, so the courses built from keep_props.py
# stay in sync: the sync rule.)

import math

from course_kit import Vector, bmesh
from hearthglow_props import Parts, _p
from props import blob, cuboid, loft, ring, tube

STONE = "citadel_stone"
CARVED = "citadel_carved"
DARKSTONE = "citadel_dark"
ICE = "glacier_ice"
CLEAR = "lake_ice"
WOOD = "keep_door"
IRON = "keep_iron"


def _spike(bm, base, tip, r, segs=6):
    """A cone from base (r) to a point at tip."""
    b, t = Vector(base), Vector(tip)
    d = t - b
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=0.0, depth=d.length)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    for v in res["verts"]:
        v.co = b + d / 2 + q @ v.co


def _curve(pts, n):
    """n points along a smooth curve through pts (Catmull-Rom)."""
    P = [Vector(p) for p in pts]
    P = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
    out = []
    segs = len(pts) - 1
    for k in range(n):
        u = k / (n - 1) * segs
        i = min(int(u), segs - 1)
        t = u - i
        p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
        out.append(tuple(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t)))
    return out


def _octagon(bm, r, z0, z1, r1=None):
    loft(bm, [ring(bm, (0, 0), r, z0, 8, phase=math.pi / 8), ring(bm, (0, 0), r1 or r, z1, 8, phase=math.pi / 8)],
         cap_top=True, cap_bottom=True)


def ice_dragon(c):
    """The Frost Cove's ice dragon (review-snow_region 12 note 9: "high quality dragon
    statue, and a high quality pedastal it is on"): a dragon of clear blue ice rearing on a
    crag, its tail coiled round it, wings half raised, a crest of spines down its neck and
    back, swept horns, glowing eyes, its forefeet gripping the crag's edge; on a stepped,
    moulded octagonal pedestal of the citadel's stone, carved panels on its faces, ice
    crystals at its foot. Faces +Y. About 12 m high (at scale 1); origin on the ground."""
    name = "Ice Dragon Statue"

    def build(bm):
        k = Parts(bm)
        # ---- the pedestal
        k.add(DARKSTONE, lambda bm: _octagon(bm, 3.3, -0.8, 0.05))  # (the bottom step)
        k.add(STONE, lambda bm: _octagon(bm, 2.85, 0.05, 0.45))
        k.add(CARVED, lambda bm: loft(bm, [ring(bm, (0, 0), 2.6, 0.45, 8, phase=math.pi / 8),
                                          ring(bm, (0, 0), 2.45, 0.7, 8, phase=math.pi / 8),
                                          ring(bm, (0, 0), 2.25, 0.85, 8, phase=math.pi / 8)], cap_top=True))  # (base moulding)
        k.add(STONE, lambda bm: _octagon(bm, 2.15, 0.85, 3.0, 2.05))  # (the die)
        k.add(CARVED, lambda bm: loft(bm, [ring(bm, (0, 0), 2.1, 3.0, 8, phase=math.pi / 8),
                                          ring(bm, (0, 0), 2.35, 3.2, 8, phase=math.pi / 8),
                                          ring(bm, (0, 0), 2.6, 3.45, 8, phase=math.pi / 8)], cap_top=False))  # (cornice)
        k.add(STONE, lambda bm: _octagon(bm, 2.7, 3.45, 3.75))  # (the top slab)

        # Sunk panels on its eight faces, an ice diamond set in each.
        def panels(bm):
            for i in range(8):
                a = i * math.tau / 8
                r = 2.1 * math.cos(math.pi / 8) + 0.01
                cuboid(bm, (r * math.cos(a), r * math.sin(a), 1.9), (0.06, 1.15, 1.6), rot=a)
        k.add(DARKSTONE, panels)

        def gems(bm):
            for i in range(8):
                a = i * math.tau / 8
                r = 2.1 * math.cos(math.pi / 8) + 0.08
                blob(bm, (r * math.cos(a), r * math.sin(a), 1.9), 0.32, sx=0.5, sy=0.5, sz=1.0, subdiv=0)
        k.add(CLEAR, gems)

        # Ice crystals grown at its foot, at four corners.
        def crystals(bm):
            for i in range(4):
                a = i * math.tau / 4 + math.pi / 4
                bx, by = 3.0 * math.cos(a), 3.0 * math.sin(a)
                for j in range(3):
                    tilt = 0.35 + 0.2 * j
                    aa = a + (j - 1) * 0.6
                    _spike(bm, (bx, by, -0.3), (bx + tilt * math.cos(aa), by + tilt * math.sin(aa), 0.9 + 0.5 * (j == 1)),
                           0.22 + 0.06 * (j == 1))
        k.add(ICE, crystals)
        # ---- the crag it rears on
        top = 3.75
        k.add("frost_rock", lambda bm: [blob(bm, (0.0, -0.2, top + 0.35), 1.7, sx=1.1, sy=1.25, sz=0.55, subdiv=2),
                                        blob(bm, (0.5, 0.9, top + 0.55), 0.85, sx=1.0, sy=0.9, sz=0.7, subdiv=2)])

        # ---- the dragon
        def body(bm):
            # The tail coiled round the crag, into the haunches, up through the chest, the
            # neck arched up and forward to the head.
            spine = []
            for j in range(9):
                t = j / 8
                a = -math.pi * 0.35 + t * math.pi * 1.45
                rr = 2.05 - 0.4 * t
                spine.append((rr * math.cos(a) * -1.0, rr * math.sin(a) * -1.0 - 0.3, top + 0.35 + 0.35 * t))
            spine += [(0.0, -1.3, top + 1.4), (0.0, -0.8, top + 2.4), (0.0, -0.1, top + 3.6), (0.0, 0.35, top + 4.6),
                      (0.0, 0.55, top + 5.6), (0.0, 0.9, top + 6.4), (0.0, 1.55, top + 6.8)]
            pts = _curve(spine, 60)
            radii = []
            for i in range(len(pts)):
                t = i / (len(pts) - 1)
                if t < 0.45:  # (the tail, thickening)
                    r = 0.08 + 0.55 * (t / 0.45) ** 1.3
                elif t < 0.72:  # (haunches to chest)
                    r = 0.63 + 0.32 * math.sin(math.pi * (t - 0.45) / 0.27)
                else:  # (the neck, thinning to the head)
                    r = 0.62 - 0.28 * (t - 0.72) / 0.28
                radii.append(r)
            tube(bm, pts, radii, n=14)
            # Belly and haunches filled out.
            blob(bm, (0.0, -0.9, top + 1.6), 1.05, sx=1.05, sy=0.9, sz=1.0, subdiv=3)
            blob(bm, (0.0, -0.3, top + 2.9), 0.95, sx=1.0, sy=0.95, sz=1.2, subdiv=3)
            # The head: a long skull, a tapered snout, a jaw a little open, brows.
            hx, hy, hz = 0.0, 1.75, top + 6.85
            blob(bm, (hx, hy, hz + 0.1), 0.52, sx=0.92, sy=1.1, sz=0.85, subdiv=3)
            tube(bm, [(hx, hy + 0.2, hz), (hx, hy + 0.8, hz - 0.08), (hx, hy + 1.35, hz - 0.2)], [0.4, 0.31, 0.22], n=12)
            blob(bm, (hx, hy + 1.38, hz - 0.18), 0.23, sx=1.0, sy=0.8, sz=0.85, subdiv=2)  # (its nose)
            blob(bm, (hx, hy + 0.85, hz - 0.42), 0.32, sx=0.75, sy=1.6, sz=0.35, subdiv=2)  # (the lower jaw)
            for sx in (-1, 1):
                blob(bm, (sx * 0.28, hy + 0.15, hz + 0.38), 0.18, sx=1.0, sy=1.6, sz=0.6, subdiv=2)  # (brows)
                # Its forelegs, gripping the crag's front edge.
                tube(bm, [(sx * 0.55, 0.15, top + 3.4), (sx * 0.85, 0.75, top + 2.5), (sx * 0.75, 1.05, top + 1.55),
                          (sx * 0.7, 1.25, top + 1.05)], [0.34, 0.28, 0.22, 0.2], n=10)
                # Its hind legs: a haunch, the shin, the foot on the crag.
                blob(bm, (sx * 0.75, -1.0, top + 1.55), 0.62, sx=0.8, sy=1.1, sz=1.0, subdiv=2)
                tube(bm, [(sx * 0.85, -0.85, top + 1.3), (sx * 1.0, -0.2, top + 0.95), (sx * 0.95, 0.05, top + 0.7)],
                     [0.3, 0.22, 0.2], n=10)
        k.add(ICE, body)

        # Claws, horns, the crest of spines: clear ice.

        def points(bm):
            for sx in (-1, 1):
                for j in (-1, 0, 1):
                    _spike(bm, (sx * 0.7 + 0.1 * j, 1.3, top + 0.95), (sx * 0.72 + 0.16 * j, 1.75, top + 0.75), 0.07)
                    _spike(bm, (sx * 0.95 + 0.1 * j, 0.15, top + 0.65), (sx * 0.98 + 0.16 * j, 0.6, top + 0.55), 0.07)
                # Horns: swept back and up from the crown, a smaller pair under them.
                hx, hy, hz = 0.0, 1.75, top + 6.85
                tube(bm, _curve([(sx * 0.25, hy - 0.1, hz + 0.35), (sx * 0.45, hy - 0.7, hz + 0.75), (sx * 0.55, hy - 1.45, hz + 0.85),
                                 (sx * 0.5, hy - 1.9, hz + 1.2)], 10), [0.13 - 0.012 * i for i in range(10)], n=8)
                _spike(bm, (sx * 0.4, hy - 0.2, hz + 0.05), (sx * 0.75, hy - 0.85, hz + 0.25), 0.07)
                # The wings, half raised: an arm up and back, three fingers fanned, the
                # membrane between them down to the flank (both faces, so it's seen from
                # either side).
                sh = (sx * 0.55, -0.35, top + 4.0)
                el = (sx * 1.6, -1.0, top + 5.4)
                wr = (sx * 2.3, -1.6, top + 6.6)
                tube(bm, [sh, el, wr], [0.18, 0.14, 0.1], n=8)
                tips = [(sx * 3.4, -2.6, top + 6.9), (sx * 3.3, -3.1, top + 5.4), (sx * 2.7, -3.0, top + 3.9)]
                roots = [(sx * 0.7, -1.0, top + 3.6), (sx * 0.6, -1.6, top + 2.6), (sx * 0.4, -1.9, top + 1.8)]
                for tip in tips:
                    tube(bm, [wr, tip], [0.08, 0.03], n=6)
                prev = (wr, el)
                for tip, root in zip(tips, roots):
                    for face in ((prev[0], tip, root, prev[1]),):
                        vs = [bm.verts.new(p) for p in face]
                        bm.faces.new(vs)
                        vs2 = [bm.verts.new(p) for p in reversed(face)]
                        bm.faces.new(vs2)
                    prev = (tip, root)
            # The crest: spines down the neck and back, biggest at the shoulders.
            sp = _curve([(0.0, 1.35, top + 7.25), (0.0, 0.85, top + 6.95), (0.0, 0.5, top + 6.0), (0.0, 0.3, top + 4.9),
                         (0.0, -0.3, top + 3.6), (0.0, -1.1, top + 2.5), (0.0, -1.85, top + 1.3)], 15)
            for i, (x, y, z) in enumerate(sp):
                h = 0.25 + 0.3 * math.sin(math.pi * i / 14)
                _spike(bm, (x, y, z - 0.05), (x, y - 0.35, z + h), 0.11 + 0.05 * math.sin(math.pi * i / 14))
        k.add(CLEAR, points)

        def eyes(bm):
            hx, hy, hz = 0.0, 1.75, top + 6.85
            for sx in (-1, 1):
                blob(bm, (sx * 0.33, hy + 0.3, hz + 0.18), 0.1, sx=0.6, sy=1.0, sz=0.7, subdiv=1)
        k.add("bulb_blue", eyes)
        return k.slots(c)

    return _p(c, name, build)


def chapel_door(c, w=4.0, h=6.1):
    """The Frost Chapel's great door (review-snow_region 12 note 10: "a nice wooden castle
    door"): two leaves of oak planks under a pointed arch, black iron strap hinges with
    scrolled ends, rows of studs, ring pulls and a lock plate, in a moulded stone surround
    of voussoirs; a stone sill. Its back on local y = 0 (the wall), front toward -Y; origin
    at the sill."""
    name = "Chapel Door %.0f %.0f" % (w, h)
    spring = h - w * 0.55  # (where the arch springs)

    def top_at(x):
        """The arch's height over x (a pointed arch: two arcs of radius w*0.8)."""
        R = w * 0.8
        cx = w / 2 - R if x >= 0 else -(w / 2 - R)
        dx = x - cx
        return spring + math.sqrt(max(0.0, R * R - dx * dx)) * (h - spring) / math.sqrt(R * R - (w / 2 - R) ** 2)

    def build(bm):
        k = Parts(bm)
        k.quad("dark_corridor", [(-w / 2, -0.02, 0.0), (w / 2, -0.02, 0.0), (w / 2, -0.02, h), (-w / 2, -0.02, h)])
        # The planks: two leaves, eight planks each, their tops cut to the arch.
        n = 10
        pw = w / n

        def planks(bm):
            for i in range(n):
                x = -w / 2 + pw * (i + 0.5)
                tp = min(top_at(x - pw / 2), top_at(x + pw / 2)) - 0.02
                cuboid(bm, (x, -0.16, tp / 2), (pw - 0.04, 0.16, tp))
        k.add(WOOD, planks)
        # A seam down the middle (the two leaves).
        k.add("dark_corridor", lambda bm: cuboid(bm, (0, -0.25, top_at(0.0) / 2), (0.05, 0.02, top_at(0.0) - 0.2)))

        def iron(bm):
            for sd in (-1, 1):
                for z in (0.9, h * 0.5, spring - 0.2):
                    L = w / 2 - 0.35
                    cuboid(bm, (sd * (w / 2 - L / 2 - 0.1), -0.27, z), (L, 0.05, 0.18))
                    # (the strap's scrolled end: a little ring of studs)
                    for t in range(6):
                        a = t * math.tau / 6
                        blob(bm, (sd * 0.55 + 0.14 * math.cos(a), -0.29, z + 0.14 * math.sin(a)), 0.045, subdiv=1)
                    blob(bm, (sd * (w / 2 - 0.12), -0.3, z), 0.1, sx=1.0, sy=0.6, sz=1.6, subdiv=1)  # (the hinge pin)
                # Rows of studs between the straps.
                for z in (1.9, 2.8, h * 0.5 + 0.9):
                    for i in range(4):
                        x = sd * (0.4 + i * (w / 2 - 0.8) / 3)
                        blob(bm, (x, -0.27, z), 0.055, subdiv=1)
                # Ring pulls: a boss and a hanging ring.
                blob(bm, (sd * 0.4, -0.29, 2.6), 0.12, sy=0.5, subdiv=1)
                pts = [(sd * 0.4 + 0.22 * math.sin(a), -0.33, 2.4 - 0.22 * math.cos(a)) for a in [j * math.tau / 12 for j in range(13)]]
                tube(bm, pts, 0.03, n=5)
            cuboid(bm, (0.35, -0.28, 2.2), (0.32, 0.04, 0.45))  # (the lock plate)
        k.add(IRON, iron)

        # The stone surround: voussoirs round the arch, a jamb either side, a sill.
        def surround(bm):
            for sd in (-1, 1):
                for j in range(4):
                    z = j * spring / 4
                    cuboid(bm, (sd * (w / 2 + 0.35), -0.3, z + spring / 8), (0.7 + 0.15 * (j % 2), 0.6, spring / 4 - 0.04))
            m = 13
            for j in range(m):
                t = (j + 0.5) / m
                x = -w / 2 + w * t
                z = top_at(x)
                x1 = -w / 2 + w * (j + 1) / m
                x0 = -w / 2 + w * j / m
                ang = math.atan2(top_at(x1) - top_at(x0), x1 - x0)
                nx, nz = -math.sin(ang), math.cos(ang)
                cuboid(bm, (x + nx * 0.38, -0.3, z + nz * 0.38), (w / m * 1.25 + 0.1, 0.62, 0.72), tilt=(0.0, -ang))
            cuboid(bm, (0, -0.45, -0.1), (w + 1.8, 0.9, 0.3))
        k.add(CARVED, surround)
        # The keystone, proud of the rest.
        k.add(STONE, lambda bm: cuboid(bm, (0, -0.42, h + 0.42), (0.6, 0.8, 0.95)))
        return k.slots(c)

    return _p(c, name, build)
