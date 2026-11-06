# The Lucky Bone made the smugglers' treasure hoard (Blake, Nov 5: "lets change this to be
# maybe more kid appropriate ... something pirate related. but not drugs, alcohol,
# gambling etc"; he picked the treasure hoard cave): the last cavern before the Dragon
# Isles' reveal.
# SPDX-License-Identifier: MIT
#
#   the hoard     mountains of gold coin heaped either side of the road, chests open and
#                 spilling over, crowns, goblets, gems in every colour, stacks of coin;
#   the counting  crocs at the counting tables stacking coin, at the scales weighing gems,
#                 polishing goblets; a guard asleep on top of the biggest pile;
#   the pearl     a giant pearl in its open clam on a plinth, lit;
#   the gate      THE HOARD over the road, a round vault door swung open beside it.
#
# jedge_districts.den() calls hoard().

import math

from gulch_scenery import Mesh
import props
from props import cuboid
import harbour_props as hp
import tropic_props as tp
import region_paint as paint
import jedge_districts as D
import jedge_rookery as R
import jedge_layout as L
from jedge_layout import DEN, DEN_Z

GEMS = ("crystal_red", "crystal_blue", "crystal_cyan", "crystal_magenta", "crystal_teal", "crystal_amethyst", "crystal_gold")
GOLD = ("wreck_gold", "wall")


def crown(m, x, y, z, r, k):
    """A crown: its gold band, its points, a gem on each."""
    pts = [(x + r * math.cos(a), y + r * math.sin(a), z + 0.12) for a in [q * math.tau / 12 for q in range(13)]]
    m.add(("gold_trim", "wall"), lambda bm: props.tube(bm, pts, 0.07, n=4))
    for q in range(6):
        a = q * math.tau / 6
        px, py = x + r * math.cos(a), y + r * math.sin(a)
        m.add(("gold_trim", "wall"), lambda bm, px=px, py=py: R.bmesh_cone(bm, px, py, z + 0.15, 0.07, 0.28, n=5))
        m.add((GEMS[(q + k) % len(GEMS)], "wall"), lambda bm, px=px, py=py: props.blob(bm, (px, py, z + 0.48), 0.06, subdiv=1))


def goblet(m, x, y, z):
    m.add(("gold_trim", "wall"), lambda bm: props.tube(bm, [(x, y, z), (x, y, z + 0.05), (x, y, z + 0.25), (x, y, z + 0.32), (x, y, z + 0.5)],
                                                        [0.12, 0.1, 0.03, 0.06, 0.13], n=8))


def heap(c, m, x, y, z, r, k, ground):
    """A mound of gold coin, chests and treasure spilling down it, gems strewn on it."""
    h = r * 0.55
    m.add(GOLD, lambda bm: props.blob(bm, (x, y, z - h * 0.15), r, sx=1.0, sy=0.85, sz=h / r, subdiv=2))
    for q in range(3):
        a = q * 2.1 + k
        ox, oy = x + r * 0.75 * math.cos(a), y + r * 0.6 * math.sin(a)
        m.add(GOLD, lambda bm, ox=ox, oy=oy: props.blob(bm, (ox, oy, z), r * 0.4, sz=0.45, subdiv=1))
    # (chests on and round it, open and spilling)
    for q in range(1 + k % 2):
        a = q * 2.6 + k * 1.3
        cx, cy = x + r * 0.95 * math.cos(a), y + r * 0.8 * math.sin(a)
        c.place(tp.chest(c), cx, cy, ground(cx, cy), rot=a + math.pi / 2, role="visual")
    # (gems, a crown, goblets, coin stacks on its slopes)
    for q in range(10):
        a = q * 2.399 + k
        rr = r * (0.2 + 0.6 * ((q * 0.618) % 1.0))
        gx, gy = x + rr * math.cos(a), y + rr * 0.85 * math.sin(a)
        gz = z - h * 0.15 + h * math.sqrt(max(0.0, 1.0 - (rr / r) ** 2)) - 0.05
        if q % 4 == 0:
            goblet(m, gx, gy, gz)
        elif q == 5:
            crown(m, gx, gy, gz, 0.32, k)
        else:
            m.add((GEMS[(q + k) % len(GEMS)], "wall"), lambda bm, gx=gx, gy=gy, gz=gz: props.blob(bm, (gx, gy, gz + 0.1), 0.16, subdiv=1))
    for q in range(5):
        a = q * 1.3 + k * 0.7
        sx, sy = x + (r + 0.8) * math.cos(a), y + (r * 0.85 + 0.8) * math.sin(a)
        gz = ground(sx, sy)
        hgt = 0.15 + 0.12 * (q % 3)
        m.add(("gold_trim", "wall"), lambda bm, sx=sx, sy=sy, gz=gz, hgt=hgt: props.tube(bm, [(sx, sy, gz), (sx, sy, gz + hgt)], 0.13, n=8))
    D.light(c, "glow", x, y, z + h + 1.5)
    return z - h * 0.15 + h


def hoard(c, ground, taken):
    """The hoard cave: the heaps, the counting tables, the scales, the polishers, the
    sleeping guard, the pearl in its clam, the gate."""
    dx, dy, rx, ry = DEN
    m, solid, hidden = Mesh(), Mesh(), Mesh()

    def ok(x, y, r):
        return paint.road_clear(c, x, y, r + 1.5) and taken.clear(x, y, r) and L.ellipse(x, y, *DEN) < 0.86

    # The heaps, big ones first, either side of the road.
    heaps = []

    def place_heaps(sizes, k0):
        for k, r in enumerate(sizes, k0):
            for j in range(60):
                a = j * 2.399 + k * 0.9
                e = 0.2 + 0.65 * ((j * 0.618 + k * 0.31) % 1.0)
                x, y = dx + rx * e * math.cos(a), dy + ry * e * math.sin(a)
                if ok(x, y, r + 1.0):
                    z = ground(x, y)
                    top = heap(c, m, x, y, z, r, k, ground)
                    hidden.add(("cave_rock", "wall"), lambda bm, x=x, y=y, z=z, r=r: cuboid(bm, (x, y, z + r * 0.25), (r * 1.6, r * 1.4, r * 0.5)))
                    heaps.append((x, y, z, r, top))
                    taken.add(x, y, r + 1.0)
                    break

    place_heaps((5.5, 4.5, 4.0), 0)
    # (the guard asleep on top of the biggest)
    if heaps:
        x, y, z, r, top = heaps[0]
        D.folk(c, x, y, top - 0.15, "kneel", x + 3.0, y, seed=480, at=(x + 1.0, y, top - 1.0))
        # (crocs about its foot, admiring it, pointing out the best bits)
        for q, pose in enumerate(("point", "chat", "chat")):
            a = q * 0.6 + 2.2
            fx, fy = x + (r + 1.8) * math.cos(a), y + (r * 0.85 + 1.8) * math.sin(a)
            if paint.road_clear(c, fx, fy, 0.8):
                D.folk(c, fx, fy, ground(fx, fy), pose, x, y, seed=482 + q, at=(x, y, top))
    # The counting tables: coin stacked in towers, the counters at work; the scales,
    # weighing gems; the polishers.
    n_tab = 0
    for j in range(40):
        if n_tab >= 4:
            break
        a = j * 2.399 + 0.5
        e = 0.3 + 0.5 * ((j * 0.618) % 1.0)
        x, y = dx + rx * e * math.cos(a), dy + ry * e * math.sin(a)
        if not ok(x, y, 2.4):
            continue
        z = ground(x, y)
        rot = a
        solid.add(("door_wood", "wall"), lambda bm, x=x, y=y, z=z, rot=rot: cuboid(bm, (x, y, z + 0.45), (2.4, 1.1, 0.9), rot))
        m.add(("royal_carpet", "wall"), lambda bm, x=x, y=y, z=z, rot=rot: cuboid(bm, (x, y, z + 0.91), (2.2, 0.9, 0.03), rot))
        ca, sa = math.cos(rot), math.sin(rot)
        kind = ("count", "scales", "polish", "count")[n_tab]
        if kind == "count":
            for q in range(6):
                lx = -0.9 + q * 0.36
                tx_, ty_ = x + lx * ca, y + lx * sa
                hgt = 0.1 + 0.08 * ((q * 3) % 5)
                m.add(("gold_trim", "wall"), lambda bm, tx_=tx_, ty_=ty_, z=z, hgt=hgt: props.tube(bm, [(tx_, ty_, z + 0.93), (tx_, ty_, z + 0.93 + hgt)], 0.09, n=8))
            c.place(tp.chest(c), x - sa * 1.6, y + ca * 1.6, z, rot=rot, role="visual")
            for sd in (-1, 1):
                D.folk(c, x + sa * 1.0 + ca * sd * 0.6, y - ca * 1.0 + sa * sd * 0.6, z, "work", x, y, seed=490 + n_tab * 3 + (sd > 0), at=(x, y, z + 1.0))
        elif kind == "scales":
            m.add(("gold_trim", "wall"), lambda bm, x=x, y=y, z=z: props.tube(bm, [(x, y, z + 0.92), (x, y, z + 1.8)], 0.05, n=6))
            b0, b1 = (x - ca * 0.7, y - sa * 0.7, z + 1.75), (x + ca * 0.7, y + sa * 0.7, z + 1.85)
            m.add(("gold_trim", "wall"), lambda bm, b0=b0, b1=b1: props.tube(bm, [b0, b1], 0.03, n=4))
            for i, b in enumerate((b0, b1)):
                m.add(("rope_rail", "wall"), lambda bm, b=b: props.tube(bm, [b, (b[0], b[1], b[2] - 0.5)], 0.01, n=3))
                m.add(("gold_trim", "wall"), lambda bm, b=b: props.tube(bm, [(b[0], b[1], b[2] - 0.55), (b[0], b[1], b[2] - 0.5)], 0.22, n=10))
                m.add((GEMS[i * 3], "wall"), lambda bm, b=b: props.blob(bm, (b[0], b[1], b[2] - 0.42), 0.1, subdiv=1))
            D.folk(c, x + sa * 1.0, y - ca * 1.0, z, "think", x, y, seed=497, at=(x, y, z + 1.7))
            D.folk(c, x + sa * 1.0 + ca * 1.0, y - ca * 1.0 + sa * 1.0, z, "point", x, y, seed=498, at=(x, y, z + 1.7))
        else:
            for q in range(5):
                lx = -0.8 + q * 0.4
                goblet(m, x + lx * ca, y + lx * sa, z + 0.93)
            for sd in (-1, 1):
                D.folk(c, x + sa * 1.0 + ca * sd * 0.7, y - ca * 1.0 + sa * sd * 0.7, z, "cook", x, y, seed=500 + (sd > 0), at=(x, y, z + 1.0))
        c.place(hp.cage_lantern(c, j), x, y, z + 3.0, role="visual")
        D.light(c, "lantern", x, y, z + 2.8)
        taken.add(x, y, 3.0)
        n_tab += 1
    # The giant pearl in its open clam, on a plinth, lit.
    for j in range(40):
        a = j * 2.399 + 2.0
        e = 0.35 + 0.4 * ((j * 0.618) % 1.0)
        x, y = dx + rx * e * math.cos(a), dy + ry * e * math.sin(a)
        if ok(x, y, 3.0):
            z = ground(x, y)
            solid.add(("palace_paving", "wall"), lambda bm: cuboid(bm, (x, y, z + 0.6), (2.6, 2.6, 1.2)))
            m.add(("gold_trim", "wall"), lambda bm: cuboid(bm, (x, y, z + 1.22), (2.8, 2.8, 0.08)))
            m.add(("lantern_glass", "wall"), lambda bm: props.blob(bm, (x, y, z + 1.45), 1.1, sz=0.35, subdiv=2))
            m.add(("lantern_glass", "wall"), lambda bm: props.blob(bm, (x - 0.5, y, z + 2.2), 1.1, sx=0.35, sz=0.95, subdiv=2))
            m.add(("party_white", "wall"), lambda bm: props.blob(bm, (x + 0.15, y, z + 2.05), 0.62, subdiv=2))
            D.light(c, "glow", x, y, z + 3.0)
            for q in range(3):
                b = q * 0.7 + a + math.pi
                fx, fy = x + 3.2 * math.cos(b), y + 3.2 * math.sin(b)
                if paint.road_clear(c, fx, fy, 0.8):
                    D.folk(c, fx, fy, ground(fx, fy), ("point", "chat", "think")[q], x, y, seed=504 + q, at=(x, y, z + 2.0))
            taken.add(x, y, 4.0)
            break
    # (smaller heaps wherever there's room left)
    place_heaps((3.5, 3.0, 3.0, 2.5, 2.5, 2.0, 2.0), 3)
    # The gate: THE HOARD over the road, the vault door swung open beside it.
    q, _ = c.nearest(*L.ROUTE[L.AT["den0"]][:2])
    f = R.Frame(q)
    R._gate(m, f, "sign_hoard", q.p.z, q.w / 2 + 2.0)
    vx, vy = f.P(1.5, -(q.w / 2 + 4.2))
    rot = math.atan2(f.ty, f.tx) + 0.9
    m.add(("keep_iron", "wall"), lambda bm: props.tube(bm, [(vx - math.cos(rot) * 0.3, vy - math.sin(rot) * 0.3, q.p.z + 2.6),
                                                          (vx + math.cos(rot) * 0.3, vy + math.sin(rot) * 0.3, q.p.z + 2.6)], 2.4, n=16))
    for i in range(6):
        b = i * math.tau / 6
        bx, by = vx + math.cos(rot) * 0.35, vy + math.sin(rot) * 0.35
        oz, oy = 1.6 * math.cos(b), 1.6 * math.sin(b)
        m.add(("gold_trim", "wall"), lambda bm, bx=bx, by=by, oz=oz, oy=oy: props.blob(bm, (bx - math.sin(rot) * oy, by + math.cos(rot) * oy, q.p.z + 2.6 + oz), 0.18, subdiv=1))
    m.add(("gold_trim", "wall"), lambda bm: props.tube(bm, [(vx + math.cos(rot) * 0.3, vy + math.sin(rot) * 0.3, q.p.z + 2.6),
                                                          (vx + math.cos(rot) * 0.55, vy + math.sin(rot) * 0.55, q.p.z + 2.6)], 0.5, n=8))
    for sd in (-1, 1):
        gx, gy = f.P(-1.0, sd * (q.w / 2 + 2.0))
        D.light(c, "torch", gx, gy, q.p.z + 6.5)
    m.build(c, "Hoard", coll="Props", role="visual")
    solid.build(c, "Hoard Solids", coll="Props", role="both")
    hidden.build(c, "Hoard Heaps", coll="Collision", role="collision")
    print("hoard: %d heaps, %d tables" % (len(heaps), n_tab))
