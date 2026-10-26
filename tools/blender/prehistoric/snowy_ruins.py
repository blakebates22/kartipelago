# Snowy Summit Pass in ruins: Adventure's treasure map course for the frozen lake
# (?track=snowy_summit_ruin; in dev builds the course's menu entry asks Standard or Ruined).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/snowy_ruins.py      (the bpy module)
#
# The dragons brought the great hollow tree down (Blake: about half as long; the tree we
# spiralled up destroyed and fallen towards the start, and we drive through it like a
# tunnel). It fell south-west across the forest, its top over the crevasse, and with it
# went the spiral, the rope bridge, the treetop bridges and the road down from the
# lookout. The lap is the course's own as far as the tree's door; then across its broken
# stump and out through the breach the fall tore in its wall, straight through the fallen
# trunk on its rotten floor, up the trunk's shattered top and off it over the crevasse
# onto the crown's limbs, and down onto the old landing and the glacier fields home.
# About 1430 m (the full lap is 2185 m).
#
# snowy_summit.py lays the lap out (ruin_mode.ON); the rest of the valley (the lake, the
# springs, the caves, the canyons, the forest, the other giants, the lookout) is placed by
# the course's own scenery code along the standard lap (ruin_kit.ghost), with the great
# tree a stump; here are the fallen trunk, its crown, the ploughed snow and the fires.

import importlib
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ruin_mode  # noqa: E402

# The standard course first (its route and landmarks), then the ruin's lap.
ruin_mode.ON = False
import snowy_summit as std  # noqa: E402

sys.modules.pop("snowy_summit")
ruin_mode.ON = True
ss = importlib.import_module("snowy_summit")

import props  # noqa: E402
import ruin_kit as rk  # noqa: E402
import summit_scenery as sc  # noqa: E402
from course_kit import Vector, rnd  # noqa: E402

# Where the fire fell: round the stump, along the trunk, and where the crown came down.
BURNS = [(40.0, 120.0, 30.0), (-20.0, 100.0, 22.0), (-55.0, 45.0, 22.0), (-140.0, -55.0, 24.0), (-80.0, -50.0, 18.0)]


def _frame(m):
    """The trunk's frame: a point at t metres along it (the straight through it), lat
    across (positive to the right), h up from its axis."""
    (ax, ay), (dx, dy), t0, t1 = m.TRUNK

    def axis_z(t):
        return m.road_z(m.SEG[23] + min(t, m.SEG[24] - m.SEG[23])) + m.TRUNK_AXIS

    def at(t, lat=0.0, h=0.0):
        return Vector((ax + dx * t + dy * lat, ay + dy * t - dx * lat, axis_z(t) + h))

    return at, axis_z, t0, t1


def stump_shape(m):
    """The stump's broken top (a jagged ring 7-28 m up) and the breach the fall tore."""

    def top(a):
        return 18.0 + 6 * math.sin(3 * a + 1) + 3 * math.sin(7 * a + 2) + 2 * math.sin(13 * a)

    def breach(x, y, z):
        p = m.trunk_at(x, y)
        return p is not None and p[0] > 0 and abs(p[1]) < 15.0

    return {"top": top, "breach": breach}


def fallen_trunk(c, m, glow):
    """The fallen trunk: a hollow log of bark outside and rotten heartwood inside, lying
    along the road, sunk into the forest floor (its rotten floor is the road's). Its top
    end is split open (only the lower half lies there) and broken off jagged over the
    crevasse; a few burnt holes in its roof let the daylight in, and it smoulders."""
    import bmesh

    at, axis_z, t0, t1 = _frame(m)
    N = 44
    ts = [t0 + k * 4.0 for k in range(int((t1 - t0) / 4.0) + 1)]
    if ts[-1] < t1:
        ts.append(t1)
    m_ = sc.Mesh()
    bm = m_.bm
    O, I = {}, {}
    for i, t in enumerate(ts):
        for j in range(N):
            a = j * math.tau / N
            # The broken ends are jagged: each end's vertices pushed in and out along it.
            jag = 0.0
            if i == 0:
                jag = 3.0 * rnd(j * 1.3)
            elif i == len(ts) - 1:
                jag = -5.0 * rnd(j * 2.1)
            ro = m.trunk_radius(t) * (1.0 + 0.03 * math.sin(a * 5 + t / 9) + 0.02 * math.sin(a * 11))
            ri = m.TRUNK_BORE * (1.0 + 0.04 * math.sin(a * 4 + t / 7))
            O[i, j] = bm.verts.new(at(t + jag, ro * math.cos(a), 0.92 * ro * math.sin(a)))
            I[i, j] = bm.verts.new(at(t + jag, ri * math.cos(a), ri * math.sin(a)))

    def present(i, j):
        if not (0 <= i < len(ts) - 1):
            return False
        j %= N
        t = (ts[i] + ts[i + 1]) / 2
        a = (j + 0.5) * math.tau / N
        # The split top: only the lower half (a ragged edge) the last OPEN metres.
        if t > t1 - m.TRUNK_OPEN and math.sin(a) > -0.1 + 0.35 * math.sin(t / 3.1 + j * 1.7) * 0.5:
            return False
        # Burnt holes in the roof.
        if math.sin(a) > 0.55 and rnd(i * 7.3 + j * 3.1) > 0.93:
            return False
        return True

    bark, wood, char, ember = [], [], [], []
    for i in range(len(ts) - 1):
        for j in range(N):
            if not present(i, j):
                continue
            j1 = (j + 1) % N
            k0 = len(bm.faces)
            bm.faces.new((O[i, j], O[i + 1, j], O[i + 1, j1], O[i, j1]))
            burnt = rnd(i * 1.9 + j * 5.7) > 0.8 and math.sin(j * math.tau / N) > -0.3
            (char if burnt else bark).append(k0)
            if burnt and rnd(i * 3.3 + j) > 0.8:
                ember.append(k0)
                char.pop()
            k1 = len(bm.faces)
            bm.faces.new((I[i, j], I[i, j1], I[i + 1, j1], I[i + 1, j]))
            wood.append(k1)
            # Jambs where the next cell is gone: the broken ends, the split, the holes.
            for (ni, nj), q in (
                ((i, j + 1), (O[i, j1], O[i + 1, j1], I[i + 1, j1], I[i, j1])),
                ((i, j - 1), (O[i + 1, j], O[i, j], I[i, j], I[i + 1, j])),
                ((i + 1, j), (O[i + 1, j], O[i + 1, j1], I[i + 1, j1], I[i + 1, j])),
                ((i - 1, j), (O[i, j1], O[i, j], I[i, j], I[i, j1])),
            ):
                if present(ni, nj):
                    continue
                k2 = len(bm.faces)
                bm.faces.new(q)
                (char if ni == i and math.sin(j * math.tau / N) > 0.55 else wood).append(k2)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    m_.slots[("giant_bark", "wall")] = bark
    m_.slots[("heartwood", "wall")] = wood
    m_.slots[("ruin_char", "wall")] = char
    m_.slots["ruin_ember"] = ember
    ob = m_.build(c, "Fallen Trunk", "Fallen Tree", "both", flat=False)
    # Glowing moss and shelf fungi down both walls inside, and the light through the holes.
    t = t0 + 8.0
    k = 0
    while t < t1 - m.TRUNK_OPEN:
        side = 1 if k % 2 else -1
        a = math.radians(-20 + 50 * rnd(k * 1.7)) if side > 0 else math.radians(200 - 50 * rnd(k * 1.7))
        glow.append(tuple(at(t, (m.TRUNK_BORE - 0.6) * math.cos(a), (m.TRUNK_BORE - 0.6) * math.sin(a))))
        t += 9.0
        k += 1
    blobs = sc.Mesh()
    for k, p in enumerate(glow):
        k0 = len(blobs.bm.faces)
        props.blob(blobs.bm, p, 1.4 + 0.8 * rnd(k), sx=1.0, sy=1.0, sz=0.6, subdiv=1)
        blobs.mark("glow_moss", k0)
    blobs.build(c, "Fallen Trunk Moss", "Fallen Tree", "visual")
    return ob


def crown(c, m, ter, z_at):
    """The crown, broken off where the trunk hit the crevasse's far side: great limbs
    across the crevasse (the landing lies on them) and sprawled beyond, its leaves heaped
    and burning, and limbs hanging down into the crevasse."""
    at, axis_z, t0, t1 = _frame(m)
    me = sc.Mesh()
    lip, land = m.R(m.JUMPS[2][0]), m.R(m.JUMPS[2][1])
    # Under the landing: limbs lying across the crevasse's far half, the deck on them.
    s = land - 2.0
    k = 0
    while s < land + 16.0:
        q = c.at(s)
        if m.in_abyss(q.p.x, q.p.y, 4.0):
            a, b = q.side(-(q.w / 2 + 9.0), -2.6), q.side(q.w / 2 + 9.0, -2.6)
            k0 = len(me.bm.faces)
            props.tube(me.bm, [tuple(a + Vector((0, 0, -1.5))), tuple((a + b) / 2), tuple(b + Vector((0, 0, -2.0)))], [2.4, 2.8, 2.0], n=7)
            me.mark(("giant_bark", "wall"), k0)
            k += 1
        s += 4.5
    # The sprawl beyond: limbs from where the crown's heart came to rest, west of the
    # landing, and its leaves (half of them burnt).
    hx, hy = tuple(at(t1 + 40.0, 34.0))[:2]
    hz = z_at(hx, hy)
    leaves = sc.Mesh()
    fires = []
    for k in range(9):
        a = k * math.tau / 9 + 0.4
        reach = 34.0 + 14 * rnd(k * 3.1)
        end = (hx + reach * math.cos(a), hy + reach * math.sin(a))
        mid = (hx + reach * 0.5 * math.cos(a), hy + reach * 0.5 * math.sin(a))
        if any(c.nearest(x, y)[1] < c.at(0).w / 2 + 6.0 for x, y in (end, mid)):
            continue
        ze = z_at(*end)
        k0 = len(me.bm.faces)
        props.tube(me.bm, [(hx, hy, hz + 3.0), (mid[0], mid[1], (hz + ze) / 2 + 4.0), (end[0], end[1], ze + 1.0)], [4.2, 2.8, 1.2], n=6)
        me.mark(("giant_bark", "wall"), k0)
        k0 = len(leaves.bm.faces)
        props.blob(leaves.bm, (end[0], end[1], ze + 4.0), 9.0 + 5 * rnd(k), sz=0.45, subdiv=2)
        leaves.mark("leaf_bright" if k % 2 else "ruin_char", k0)
        if k % 2 == 0:
            fires.append((end[0], end[1], ze + 6.0))
    k0 = len(leaves.bm.faces)
    props.blob(leaves.bm, (hx, hy, hz + 6.0), 18.0, sz=0.5, subdiv=2)
    leaves.mark("ruin_char", k0)
    fires.append((hx, hy, hz + 12.0))
    # Limbs hanging down into the crevasse either side of the jump.
    for k, side in enumerate((-1, 1, -1)):
        q = c.at(lip + 4 + 5 * k)
        p = q.side(side * (q.w / 2 + 12 + 6 * k), -1.0)
        k0 = len(me.bm.faces)
        props.tube(me.bm, [tuple(p), tuple(p + Vector((3 * side, -4, -12))), tuple(p + Vector((5 * side, -6, -22)))], [2.6, 1.8, 0.8], n=6)
        me.mark(("giant_bark", "wall"), k0)
    me.build(c, "Fallen Crown Limbs", "Fallen Tree", "both", flat=False)
    leaves.build(c, "Fallen Crown Leaves", "Fallen Tree", "visual", flat=False)
    return fires


def dress(c, m, rock, t0, t1):
    ter = list(c.coll("Terrain").objects)

    def z_at(x, y):
        z = c.ground_z(x, y, ter)
        return z if z is not None else m.natural(x, y)

    # The ruin's own road past the door: the course's scenery keeps off it, and off the
    # trunk and the crown.
    new = [(smp.p.x, smp.p.y, smp.w / 2) for smp in c.S if smp.s > m.R(m.SEG[22]) - 4][::2]
    at, axis_z, T0, T1 = _frame(m)
    hx, hy = tuple(at(T1 + 40.0, 34.0))[:2]

    def blocked(x, y, margin):
        if m.in_trunk(x, y, margin + 3.0) or math.hypot(x - hx, y - hy) < 50.0 + margin:
            return True
        return any((x - px) ** 2 + (y - py) ** 2 < (w + margin) ** 2 for px, py, w in new)

    # The valley, from the course's own scenery code, along the standard lap.
    g = rk.ghost_route(c, std.ROUTE, width=15.0, bank=6.0)
    with rk.ghost(c, g):
        sc.build(c, rock, t0, t1, std, ruin={"stump": stump_shape(m), "blocked": blocked})

    glow = []
    trunk = fallen_trunk(c, m, glow)
    fires = crown(c, m, ter, z_at)

    def clear(x, y, margin=4.0):
        return props.clear_of_road(c, x, y, margin) and not m.in_trunk(x, y, 4.0)

    # Snow and earth ploughed up along the trunk's sides, and splinters round the stump.
    k = 0
    t = T0 + 6.0
    while t < T1 - 10:
        for side in (-1, 1):
            p = at(t, side * (m.trunk_radius(t) + 3.0 + 3 * rnd(k)))
            k += 1
            if clear(p.x, p.y, 3.0):
                rk.rubble_heap(c, p.x, p.y, z_at, n=6, spread=6.0, size=2.4, role="visual", seed=k)
        t += 18.0
    cx, cy = std.TREE1
    st = rk.stub(c)
    for k in range(14):
        a = k * 2.39996
        r = std.TREE1_R[1] + 6 + 14 * rnd(k * 1.3)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        if clear(x, y, 3.0):
            c.place(st, x, y, z_at(x, y) - 0.4, rot=k, scale=2.2 + 1.2 * rnd(k), coll="Wreck", role="visual")
    # Fires: on the trunk's back, on the stump's broken top, round about.
    for k, t in enumerate((T0 + 30, T0 + 75, T0 + 120, T1 - 20)):
        p = at(t, 6.0 * (1 if k % 2 else -1), 0.92 * m.trunk_radius(t) - 1.0)
        fires.append(tuple(p))
    top = stump_shape(m)["top"]
    for k in range(5):
        a = k * 1.3 + 0.3
        r = std.TREE1_R[0] + 2.5
        fires.append((cx + r * math.cos(a), cy + r * math.sin(a), top(a) + 0.5))
    fires += rk.scorch(c, BURNS, z_at, clear, per=5, wet=lambda x, y, z: z < 0.5)
    print("cleared off the new road:", rk.clear_new_road(c, ("Forest", "Pines", "Trees", "Canyons", "Ruins", "Flags", "Bridges")))
    rk.emit(c, fires)
    c.merge_props(("Wreck",))

    # Inside the trunk it's dark but for the moss and the holes' daylight.
    def inside(w):
        p = m.trunk_at(w.x, w.y)
        return p is not None and T0 - 2 <= p[0] <= T1 - m.TRUNK_OPEN + 4 and math.hypot(p[1], w.z - axis_z(p[0])) < m.TRUNK_BORE + 0.6

    c.glow(ter + [trunk], glow, 14.0, (1.3, 1.15, 0.8), base=(0.42, 0.38, 0.36), region=inside)
    c.glow(ter + [trunk], fires, 12.0, (1.6, 0.9, 0.5), base=1.0)
    c.entity("snowfall", rate=60, radius=40)
    c.entity("ashfall", rate=24, radius=40)
    print("snowy summit ruin: fires", len(fires), "lap", round(c.length, 1))
    return [trunk]


ruin_mode.DRESS = dress

if __name__ == "__main__":
    ss.main()
