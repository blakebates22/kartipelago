# The Sky Islands' dragon pillars (Blake, Nov 6, review journey_cause 2 note 3: "lets make
# this a spectavular dragon pillar"): on each island, in place of a broken column, a tall
# stone pillar on its stepped plinth with a carved dragon coiled up it, red-scaled, its
# wings spread from the pillar's top and its head reared over the road, roaring, eyes
# lit; a fire burning in a bowl in its claws.
# SPDX-License-Identifier: MIT

import math

from gulch_scenery import Mesh
import props
from props import cuboid

SCALE = ("dragon_red", "wall")
BELLY = ("dragon_belly", "wall")
WING = ("dragon_wing", "wall")
BONE = ("bone_ivory", "wall")
STONE = ("keep_rock", "wall")


def _cone(bm, base, tip, r, n=6):
    """A cone from a circle round `base` to a point `tip` (a horn, a claw, a spine)."""
    import mathutils

    b, t = mathutils.Vector(base), mathutils.Vector(tip)
    axis = (t - b).normalized()
    side = axis.cross(mathutils.Vector((0, 0, 1)))
    if side.length < 1e-3:
        side = mathutils.Vector((1, 0, 0))
    side.normalize()
    up = side.cross(axis)
    ring = [bm.verts.new(b + (side * math.cos(a) + up * math.sin(a)) * r) for a in [i * math.tau / n for i in range(n)]]
    tv = bm.verts.new(t)
    for i in range(n):
        bm.faces.new((ring[i], ring[(i + 1) % n], tv))
    bm.faces.new(ring[::-1])


def dragon_pillar(c, x, y, z, face, k):
    """The pillar at (x, y) on ground z, the dragon's head toward `face` (radians)."""
    m, solid = Mesh(), Mesh()
    H = 12.0 + 1.5 * (k % 2)
    R = 0.85
    # (the plinth, stepped; the column; its capital)
    for i, (w, h) in enumerate(((4.2, 0.6), (3.4, 0.6), (2.6, 0.5))):
        zz = z + sum(hh for _, hh in ((4.2, 0.6), (3.4, 0.6), (2.6, 0.5))[:i])
        solid.add(STONE, lambda bm, w=w, h=h, zz=zz: cuboid(bm, (x, y, zz + h / 2 - 0.2), (w, w, h + 0.2), face))
    z0 = z + 1.7
    solid.add(STONE, lambda bm: props.tube(bm, [(x, y, z0 - 0.2), (x, y, z0 + H)], [R * 1.05, R, R * 0.95], n=12))
    m.add(("gold_trim", "wall"), lambda bm: props.tube(bm, [(x, y, z0 + H), (x, y, z0 + H + 0.5)], [R * 1.35, R * 1.35], n=12))
    m.add(STONE, lambda bm: cuboid(bm, (x, y, z0 + H + 0.7), (2.4, 2.4, 0.4), face))
    # The dragon: its body coiling up the pillar two and a half turns, thickening upward,
    # from its tail's spade at the plinth to its shoulders over the capital.
    turns = 2.4
    n = 60
    pts, rads = [], []
    for i in range(n + 1):
        t = i / n
        a = face + math.pi + turns * math.tau * (t - 1.0)
        r = R + 0.55 + 0.25 * t
        pts.append((x + r * math.cos(a), y + r * math.sin(a), z0 + 0.2 + (H + 0.6) * t))
        rads.append(0.12 + 0.48 * t ** 0.8)
    m.add(SCALE, lambda bm: props.tube(bm, pts, rads, n=10))
    # (its belly plates down the inside of the coil, spines down its back)
    for i in range(6, n, 3):
        px, py, pz = pts[i]
        ox, oy = px - x, py - y
        d = math.hypot(ox, oy) or 1.0
        r_ = rads[i]
        m.add(BELLY, lambda bm, px=px, py=py, pz=pz, ox=ox, oy=oy, d=d, r_=r_: cuboid(bm, (px - ox / d * r_ * 0.8, py - oy / d * r_ * 0.8, pz), (r_ * 0.9, 0.08, r_ * 0.7), math.atan2(oy, ox) + math.pi / 2))
        m.add(BONE, lambda bm, px=px, py=py, pz=pz, ox=ox, oy=oy, d=d, r_=r_: _cone(bm, (px + ox / d * r_ * 0.7, py + oy / d * r_ * 0.7, pz + r_ * 0.4),
                                                                                    (px + ox / d * (r_ + 0.35), py + oy / d * (r_ + 0.35), pz + r_ * 0.4 + 0.35), r_ * 0.25, n=4))
    tx, ty, tz = pts[0]
    m.add(SCALE, lambda bm: _cone(bm, (tx, ty, tz), (tx + 0.6 * math.cos(face), ty + 0.6 * math.sin(face), tz - 0.1), 0.3, n=4))
    # The shoulders and the head, reared out over the road toward `face`, jaws open.
    sx, sy, sz = pts[-1]
    fx, fy = math.cos(face), math.sin(face)
    nx, ny, nz = sx + fx * 1.4, sy + fy * 1.4, sz + 1.6
    hx, hy, hz = sx + fx * 2.6, sy + fy * 2.6, sz + 2.4
    m.add(SCALE, lambda bm: props.tube(bm, [(sx, sy, sz), (nx, ny, nz), (hx, hy, hz)], [0.62, 0.5, 0.42], n=10))
    m.add(SCALE, lambda bm: props.blob(bm, (hx, hy, hz), 0.62, sx=1.0, sy=1.0, sz=0.8, subdiv=2))
    m.add(SCALE, lambda bm: props.tube(bm, [(hx, hy, hz + 0.05), (hx + fx * 1.1, hy + fy * 1.1, hz + 0.05)], [0.42, 0.22], n=8))
    m.add(BELLY, lambda bm: props.tube(bm, [(hx, hy, hz - 0.3), (hx + fx * 1.0, hy + fy * 1.0, hz - 0.75)], [0.32, 0.16], n=8))
    rx, ry = -fy, fx
    for sd in (-1, 1):
        m.add(BONE, lambda bm, sd=sd: _cone(bm, (hx - fx * 0.2 + rx * sd * 0.3, hy - fy * 0.2 + ry * sd * 0.3, hz + 0.4),
                                            (hx - fx * 1.3 + rx * sd * 0.7, hy - fy * 1.3 + ry * sd * 0.7, hz + 1.2), 0.12))
        m.add(BONE, lambda bm, sd=sd: _cone(bm, (hx + rx * sd * 0.5, hy + ry * sd * 0.5, hz), (hx - fx * 0.6 + rx * sd * 1.1, hy - fy * 0.6 + ry * sd * 1.1, hz - 0.1), 0.08))
        for q in range(3):
            u = 0.45 + q * 0.22
            m.add(BONE, lambda bm, sd=sd, u=u: _cone(bm, (hx + fx * u + rx * sd * 0.18, hy + fy * u + ry * sd * 0.18, hz - 0.12),
                                                     (hx + fx * u + rx * sd * 0.18, hy + fy * u + ry * sd * 0.18, hz - 0.32), 0.04, n=4))
        ex, ey = hx + fx * 0.25 + rx * sd * 0.36, hy + fy * 0.25 + ry * sd * 0.36
        m.add(("fire_glow", "wall"), lambda bm, ex=ex, ey=ey: props.blob(bm, (ex, ey, hz + 0.25), 0.11, subdiv=1))
    # (its wings spread from the shoulders, bat-ribbed: a fan of membrane each side)
    for sd in (-1, 1):
        base = (sx - fx * 0.2 + rx * sd * 0.5, sy - fy * 0.2 + ry * sd * 0.5, sz + 0.6)
        wrist = (sx - fx * 0.6 + rx * sd * 3.2, sy - fy * 0.6 + ry * sd * 3.2, sz + 3.4)
        tips = [(sx - fx * (0.4 + 1.1 * q) + rx * sd * (5.2 - 0.9 * q), sy - fy * (0.4 + 1.1 * q) + ry * sd * (5.2 - 0.9 * q), sz + 2.4 - 0.9 * q)
                for q in range(4)]
        m.add(SCALE, lambda bm, base=base, wrist=wrist: props.tube(bm, [base, wrist], [0.22, 0.14], n=6))
        for tp_ in tips:
            m.add(SCALE, lambda bm, wrist=wrist, tp_=tp_: props.tube(bm, [wrist, tp_], [0.09, 0.04], n=5))
        fan = [wrist] + tips + [(sx - fx * 2.0 + rx * sd * 0.6, sy - fy * 2.0 + ry * sd * 0.6, sz - 0.6)]
        for a, b in zip(fan[1:], fan[2:]):
            for tri in ((wrist, a, b), (wrist, b, a)):
                m.add(WING, lambda bm, tri=tri: bm.faces.new([bm.verts.new(p) for p in tri]))
        for tri in ((base, wrist, fan[-1]), (base, fan[-1], wrist)):
            m.add(WING, lambda bm, tri=tri: bm.faces.new([bm.verts.new(p) for p in tri]))
    # (a fire burning in a bronze bowl on the capital, under its chin)
    bx, by = x + fx * 0.6, y + fy * 0.6
    m.add(("gold_trim", "wall"), lambda bm: props.blob(bm, (bx, by, z0 + H + 1.0), 0.55, sz=0.4, subdiv=1))
    g = c.game(bx, by, z0 + H + 1.4)
    c.entity("campfire", x=g[0], y=g[1], z=g[2])
    g = c.game(hx + fx * 0.8, hy + fy * 0.8, hz)
    c.entity("glow", x=g[0], y=g[1], z=g[2])
    m.build(c, "Dragon Pillar %d" % k, coll="Props", role="visual")
    solid.build(c, "Dragon Pillar Stone %d" % k, coll="Props", role="both")
