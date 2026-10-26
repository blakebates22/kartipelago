# Oasis Haven in ruins: Adventure's treasure map course for the desert oasis
# (?track=oasis_haven_ruin; in dev builds the course's menu entry asks Standard or Ruined).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/oasis_ruins.py      (the bpy module)
#
# The dragons came over the dunes (Blake: about the same length, but it drives quite
# differently and more fun). The watchtower has toppled across its mesa and taken the
# spiral with it: the lap climbs the rubble of its fallen decks onto the tower's broken
# body and jumps off its top, down onto the chute (and its own jump over the wash). The
# camp burned and its tents came down across the weave, so the lap follows the dragon's
# scorched track out over the dunes and back west through the burnt camp. The arch's span
# has fallen across the road beyond the butte: the lap rides up over it. About 1550 m
# (the full lap is 1559 m).
#
# oasis_haven.py lays the lap out (ruin_mode.ON); the oasis (the village, the pool and
# its grove, the camp, the butte, the dunes) is the course's own scenery code along the
# standard lap (ruin_kit.ghost); here are the fallen tower, the spiral's wreck, the
# fallen arch, the burnt tents and the fires.

import importlib
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ruin_mode  # noqa: E402

# The standard course first (its route and landmarks), then the ruin's lap.
ruin_mode.ON = False
import oasis_haven as std  # noqa: E402

sys.modules.pop("oasis_haven")
ruin_mode.ON = True
oh = importlib.import_module("oasis_haven")

import oasis_desert as od  # noqa: E402
import props  # noqa: E402
import ruin_kit as rk  # noqa: E402
from course_kit import Vector, bmesh, rnd  # noqa: E402
from oasis_desert import Mesh, Parts  # noqa: E402
from props import blob, cuboid, tube  # noqa: E402

ADOBE = ("adobe", "wall")
DARK = ("adobe_dark", "wall")
# Where the fire fell: the camp, the dragon's scorch over the dunes, round the fallen
# tower, by the fallen arch, the village's south end.
BURNS = [(345.0, -40.0, 30.0), (420.0, -75.0, 24.0), (465.0, -30.0, 22.0), (400.0, 10.0, 22.0), (134.0, 118.0, 34.0),
         (350.0, 160.0, 18.0), (30.0, -60.0, 18.0)]


def burnt_tent(c, variant=0, w=14.0, d=9.0):
    """A pavilion the fire took: its poles charred and leaning, one fallen, the roof
    burnt away but for scorched rags hanging off the ridge and heaped on the carpet,
    embers glowing in them. (The grand tent's footprint, facing -Y.)"""
    name = "Burnt Tent %d" % variant
    cloth = ("tent_cloth", "tent_cloth_red")[variant % 2]

    def build(bm):
        P = Parts(bm)
        H = 5.2
        P.add("royal_carpet", cuboid, (0, -0.6, 0.05), (w - 1.4, d + 1.6, 0.1))
        for i, x in enumerate((-w / 3, 0.0, w / 3)):
            lean = (0.0, 0.9, -1.4)[(i + variant) % 3]
            if (i + variant) % 3 == 2:
                # This one has come down across the carpet.
                P.add("ruin_char", tube, [(x - 0.3, -d / 2 + 0.5, 0.25), (x + 1.2, d / 2 - 0.5, 0.6)], 0.14, n=5)
                continue
            P.add("ruin_char", tube, [(x, 0.0, 0.0), (x + lean, 0.3, H * (0.8 + 0.2 * rnd(i + variant)))], 0.14, n=5)
        # The ridge beam, broken, and rags of cloth hanging off it.
        P.add("ruin_char", tube, [(-w / 3, 0.2, H * 0.92), (w / 6, 0.6, H * 0.7)], 0.1, n=4)
        for k in range(4):
            x = -w / 3 + 0.8 + k * 1.4
            P.add(cloth, cuboid, (x, 0.4 + 0.4 * (k % 2), H * 0.55), (0.9 + 0.4 * rnd(k), 0.06, 1.8 + 0.8 * rnd(k + 2)), 0.2 * (k - 1.5))
        # The roof that fell in, charred, in heaps on the carpet, and embers in it.
        for k in range(5):
            x = -w / 2 + 2.0 + k * (w - 4) / 4
            P.add("ruin_char", blob, (x, (rnd(k * 3.3 + variant) - 0.5) * d * 0.6, 0.45), 1.3 + 0.5 * rnd(k), sx=1.4, sz=0.4, subdiv=0)
            if k % 2 == variant % 2:
                P.add("ruin_ember", blob, (x + 0.4, 0.3, 0.55), 0.6, sx=1.3, sz=0.5, subdiv=0)
        P.add(cloth, cuboid, (w / 4, -d / 2 + 1.0, 0.3), (w / 3, d / 3, 0.12), 0.3, (0.1, 0.05))
        return P.out(c)

    return c.proto(name, build) and name


def toppled_tower(c, m, ter, fires):
    """The watchtower, down: its stump on the mesa (a broken ring of wall on the side away
    from the road), and its body lying where it fell, crushed oval and broken into drums,
    under the lap's road from the stump to the crenellated top the road jumps off."""
    tx, ty = std.TOWER
    me = Mesh()
    # The stump: what's left of the wall, standing on the side clear of the road.
    for k in range(28):
        a0, a1 = k * math.tau / 28, (k + 1) * math.tau / 28
        am = (a0 + a1) / 2
        x, y = tx + 16.6 * math.cos(am), ty + 16.6 * math.sin(am)
        if not props.clear_of_road(c, x, y, 3.0):
            continue
        z0 = od.ground(c, ter, x, y, m.natural(x, y)) - 1.0
        h = 5.0 + 11.0 * rnd(k * 1.37) * (0.5 + 0.5 * math.sin(k * 0.7))
        me.add(ADOBE, lambda bm, x=x, y=y, z0=z0, h=h, am=am: cuboid(bm, (x, y, z0 + h / 2), (1.6, 3.9, h), am))
        me.add(DARK, lambda bm, x=x, y=y, z0=z0, am=am: cuboid(bm, (x, y, z0 + 1.2), (1.9, 4.0, 2.4), am))
        if k % 5 == 0:
            fires.append((x, y, z0 + h + 0.6))
    # The body: from the stump to the top, under the road. Its crown sits just under the
    # road all along (crushed oval: wide, low), its sides falling away either hand.
    top = c.at(m.TLIP - 1.0).p
    a = Vector((tx, ty, 0.0))
    b = Vector((top.x, top.y, 0.0))
    ax = (b - a).normalized()
    side = Vector((-ax.y, ax.x, 0.0))
    up = Vector((0.0, 0.0, 1.0))
    RH, N = 15.5, 24
    n = 9
    rings = []
    for i in range(n + 1):
        t = i / n
        p = a.lerp(b, t)
        smp, _ = c.nearest(p.x, p.y)
        o = abs((Vector((smp.p.x, smp.p.y, 0)) - p).dot(side))
        near = max(0.0, o - smp.w / 2 - 1.0) / RH
        # Its crown under the road, its foot sunk a metre into the sand.
        crown = smp.p.z - 1.0
        rv = (crown - (m.natural(p.x, p.y) - 1.0)) / (1.0 + math.sqrt(max(0.05, 1 - near * near)))
        zc = crown - rv * math.sqrt(max(0.05, 1 - near * near))
        rings.append((p, zc, rv, 1.0 if i in (0, n) else 0.9 + 0.12 * rnd(i * 2.1)))
    bm_rings = []

    def body(bm):
        for i, (p, zc, rv, k) in enumerate(rings):
            vs = []
            for j in range(N):
                th = j * math.tau / N
                wob = 1.0 + 0.06 * math.sin(j * 2.3 + i * 1.7)
                q = p + side * (RH * k * wob * math.cos(th)) + up * (zc + rv * k * wob * math.sin(th))
                vs.append(bm.verts.new(q))
            bm_rings.append(vs)
        for lo, hi in zip(bm_rings, bm_rings[1:]):
            for j in range(N):
                bm.faces.new((lo[j], lo[(j + 1) % N], hi[(j + 1) % N], hi[j]))
        bm.faces.new(list(reversed(bm_rings[0])))
        bm.faces.new(bm_rings[-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    me.add(ADOBE, body)
    # Cracks between its drums: dark bands round the body where it broke.
    for i in (3, 6):
        p, zc, rv, k = rings[i]
        me.add(DARK, lambda bm, p=p, zc=zc, rv=rv, k=k: _band(bm, p, zc, side, up, ax, RH * k + 0.3, rv * k + 0.3))
    # The top: its crenellations round the end, splayed where they hit the ground.
    p, zc, RV, k = rings[-1]
    for j in range(16):
        th = j * math.tau / 16
        if j in (11, 12):
            continue
        q = p + ax * 1.0 + side * ((RH + 0.6) * math.cos(th)) + up * (zc + (RV + 0.6) * math.sin(th))
        if q.z > zc + RV - 1.5:
            continue  # (not up through the lip)
        me.add(ADOBE, lambda bm, q=q, th=th: cuboid(bm, (q.x, q.y, q.z), (2.6, 1.6, 2.8), math.atan2(ax.y, ax.x) + math.pi / 2,
                                                       (0.25 * math.sin(th), 0.2)))
    me.add(("oasis_banner", "wall"), lambda bm: cuboid(bm, tuple(p - ax * 8 + side * (RH * 0.8) + up * (zc + RV * 0.4)), (0.12, 2.0, 4.5),
                                                       math.atan2(ax.y, ax.x), (0.6, 0.0)))
    me.build(c, "Fallen Watchtower", "Wreck", "both")
    fires.append((top.x - side.x * 10, top.y - side.y * 10, top.z - 3.0))


def _band(bm, p, zc, side, up, ax, rh, rv, n=24, w=0.8):
    rs = []
    for o in (-w / 2, w / 2):
        rs.append([bm.verts.new(p + ax * o + side * (rh * math.cos(j * math.tau / n)) + up * (zc + rv * math.sin(j * math.tau / n))) for j in range(n)])
    for j in range(n):
        bm.faces.new((rs[0][j], rs[0][(j + 1) % n], rs[1][(j + 1) % n], rs[1][j]))


def spiral_wreck(c, m, ter, fires):
    """The spiral's decks, fallen with the tower: paving slabs and lengths of balustrade
    tumbled round the stump, clear of the road."""
    tx, ty = std.TOWER
    me = Mesh()
    k = 0
    for i in range(40):
        a = i * 2.39996
        r = 22.0 + 26.0 * math.sqrt(rnd(i * 1.91))
        x, y = tx + r * math.cos(a), ty + r * math.sin(a)
        if not props.clear_of_road(c, x, y, 4.0):
            continue
        k += 1
        z = od.ground(c, ter, x, y, m.natural(x, y))
        rot = a + math.pi / 2 + (rnd(i) - 0.5)
        tilt = ((rnd(i * 3) - 0.5) * 0.9, (rnd(i * 5) - 0.5) * 0.6)
        me.add(("oasis_paving", "road"), lambda bm, x=x, y=y, z=z, rot=rot, tilt=tilt: cuboid(bm, (x, y, z + 0.4), (7.0, 4.5, 0.6), rot, tilt))
        me.add(ADOBE, lambda bm, x=x, y=y, z=z, rot=rot, tilt=tilt: cuboid(bm, (x, y, z - 0.6), (7.2, 4.7, 1.6), rot, tilt))
        if k % 2:
            me.add(("balustrade", "wall"), lambda bm, x=x, y=y, z=z, rot=rot, tilt=tilt: cuboid(bm, (x + 1.8 * math.cos(rot + 1.57), y + 1.8 * math.sin(rot + 1.57), z + 1.1), (6.0, 0.4, 1.2), rot, tilt))
        if k % 6 == 0:
            fires.append((x, y, z + 1.4))
    me.build(c, "Spiral Wreck", "Wreck", "both")


def fallen_arch(c, m, fires):
    """The arch's legs, broken off, and its span down across the road: the lap rides up
    over it, its broken ends heaped either side."""
    at = max(m.HUMPS)[0] if m.HUMPS else m.SEG[19] + 20
    q = c.at(at)
    rot = od.road_rot(q)
    base = c.at(at - 12).p.z
    for side in (-1, 1):
        p = q.side(side * (q.w / 2 + 6.0))
        lg = c.rock_mass("Broken Arch Leg %d" % (side > 0), p.x, p.y, 5.0, 4.5, base + 5.5 + 2.5 * (side > 0), z0=base - 4.0, n=12,
                         seed=11 + side, angle=rot)
        c.paint_rock(lg, ("gold_cliff", "wall"), ("pale_sand", "dirt"))
        e = q.side(side * (q.w / 2 + 2.6))
        ch = c.rock_mass("Fallen Span %d" % (side > 0), e.x, e.y, 3.6, 2.6, q.p.z + 1.6, z0=base - 3.0, n=10, seed=21 + side, angle=rot)
        c.paint_rock(ch, ("gold_cliff", "wall"), ("pale_sand", "dirt"))
    for k in range(6):
        e = c.at(at + (k - 2.5) * 5.0).side((1 if k % 2 else -1) * (q.w / 2 + 4.0 + 5 * rnd(k)))
        bl = c.rock_mass("Arch Rubble %d" % k, e.x, e.y, 1.8 + rnd(k), 1.4 + rnd(k + 3), base + 1.0 + 1.5 * rnd(k * 2), z0=base - 2.0, n=8,
                         seed=31 + k, angle=k)
        c.paint_rock(bl, ("gold_cliff", "wall"), ("pale_sand", "dirt"))
    fires.append((q.side(q.w / 2 + 9).x, q.side(q.w / 2 + 9).y, base + 1.0))


def fallen_tents(c, ter):
    """Where the weave ran through the camp: the tents came down burning across it (why
    the lap goes round by the scorch now). On the standard lap."""
    S = std.SEG
    spots = []
    for k, s in enumerate((S[11] + 10, S[11] + 40, S[12] + 15, S[13] + 10, S[14] + 25)):
        q = c.at(s)
        p = q.side((rnd(k * 1.3) - 0.5) * 6)
        spots.append((p.x, p.y, od.road_rot(q) + 0.6 + 0.5 * k))
    return spots


def dress(c, m):
    ter = list(c.coll("Terrain").objects)

    def z_at(x, y):
        return od.ground(c, ter, x, y, m.natural(x, y))

    def clear(x, y, margin=4.0):
        return props.clear_of_road(c, x, y, margin)

    fires = []
    tent = lambda c, k: burnt_tent(c, k)  # noqa: E731
    # The oasis, from the course's own scenery code, along the standard lap.
    g = rk.ghost_route(c, std.ROUTE, width=15.0, bank=7.0)
    with rk.ghost(c, g):
        sc = od.build(c, std, ruin={"tent": tent})
        spots = fallen_tents(c, ter)
    for k, (x, y, rot) in enumerate(spots):
        if clear(x, y, 6.0):
            c.place(burnt_tent(c, k), x, y, z_at(x, y) - 0.1, rot=rot, coll="Wreck", role="visual")
            c.place(od.collider(c, 12.0, 9.0, 2.2, -0.5, "tent_cloth"), x, y, z_at(x, y) - 0.1, rot=rot, coll="Wreck", role="collision")
            fires.append((x, y, z_at(x, y) + 1.2))
    # The camp's lanterns are out where its tents burned (its own fire still burns).
    camp = sc["torches"]
    sc["lanterns"] = [p for p in sc["lanterns"] if p not in camp or camp.index(p) % 3 == 0]
    toppled_tower(c, m, ter, fires)
    spiral_wreck(c, m, ter, fires)
    fallen_arch(c, m, fires)
    # Along the dragon's scorch: burnt-out scrub and fires either side.
    S = m.SEG
    for k, s in enumerate(range(int(S[10]) + 10, int(S[16]), 26)):
        q = c.at(s)
        p = q.side((1 if k % 2 else -1) * (q.w / 2 + 4.0 + 3 * rnd(k)))
        if clear(p.x, p.y, 2.0):
            rk.rubble_heap(c, p.x, p.y, z_at, n=4, spread=2.5, size=1.0, role="visual", seed=k)
            if k % 2 == 0:
                fires.append((p.x, p.y, z_at(p.x, p.y) + 0.8))
    fires += rk.scorch(c, BURNS, z_at, clear, per=5, wet=lambda x, y, z: math.hypot(x - std.POOL[0], y - std.POOL[1]) < std.POOL[2] + 4)
    print("cleared off the new road:", rk.clear_new_road(c, ("Village", "Camp", "Grove", "Dunes")))
    od.finish(c, sc, keep=lambda x, y: clear(x, y, 2.0))
    rk.emit(c, fires, glow_on=ter)
    c.merge_props(("Wreck",))
    c.entity("ashfall", rate=20, radius=40)
    print("oasis ruin: fires", len(fires), "lap", round(c.length, 1))


ruin_mode.DRESS = dress

if __name__ == "__main__":
    oh.main()
