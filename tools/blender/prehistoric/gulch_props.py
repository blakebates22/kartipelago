# Dry Gulch Ghost Town's props: lanterns, barrels, wagons, the graveyard's headstones,
# crosses and crypts, dead trees, ore carts, mining gear, spectral crystals, cattle
# skulls. Each builds one mesh (a prototype) that every copy shares; origins are at the
# ground. All our own designs.
# SPDX-License-Identifier: MIT

import math

from canyon_props import _beam, _cyl
from course_kit import Vector, bmesh
from props import _faces, blob, cuboid, loft, ring, tube


def _p(c, name, build):
    return c.proto(name, build) and name


def _lantern(bm, x, y, z, s=1.0):
    """A little lantern hanging at (x, y, z) (its top): an iron cap and base, the glass
    between. Returns (iron faces, glass faces) index ranges."""
    k0 = len(bm.faces)
    _cyl(bm, x, y, z - 0.18 * s, z, 0.2 * s, 0.05 * s, n=4)
    _cyl(bm, x, y, z - 0.75 * s, z - 0.65 * s, 0.2 * s, 0.2 * s, n=4)
    k1 = len(bm.faces)
    _cyl(bm, x, y, z - 0.65 * s, z - 0.18 * s, 0.16 * s, 0.16 * s, n=4, phase=math.pi / 4)
    k2 = len(bm.faces)
    return list(range(k0, k1)), list(range(k1, k2))


def lantern_post(c, green=False):
    """A tall timber post with an arm and a lantern hanging off it (lantern 3.6 m up,
    1.1 m out along +X)."""
    name = "Lantern Post" + (" Green" if green else "")

    def build(bm):
        _beam(bm, (0, 0, -0.4), (0, 0, 4.2), 0.22)
        _beam(bm, (-0.1, 0, 4.0), (1.3, 0, 4.0), 0.14)
        _beam(bm, (0, 0, 3.3), (0.7, 0, 3.95), 0.1)
        wood = list(range(len(bm.faces)))
        iron, glass = _lantern(bm, 1.1, 0, 3.95)
        return [(c.lib("weathered_timber"), wood), (c.lib("iron"), iron), (c.lib("lantern_green" if green else "lantern_glass"), glass)]

    return _p(c, name, build)


LANTERN_POST_LIGHT = (1.1, 0.0, 3.55)


def hanging_lantern(c, green=False):
    """A lantern on a short chain (its hook at the origin, hanging down 1 m)."""
    name = "Hanging Lantern" + (" Green" if green else "")

    def build(bm):
        _beam(bm, (0, 0, 0), (0, 0, -0.3), 0.04)
        chain = list(range(len(bm.faces)))
        iron, glass = _lantern(bm, 0, 0, -0.28, 1.2)
        return [(c.lib("iron"), chain + iron), (c.lib("lantern_green" if green else "lantern_glass"), glass)]

    return _p(c, name, build)


def barrel(c, variant=0):
    name = "Barrel %d" % variant

    def build(bm):
        r = 0.45
        loft(bm, [ring(bm, (0, 0), r * 0.86, 0.0, 8), ring(bm, (0, 0), r, 0.55, 8), ring(bm, (0, 0), r * 0.86, 1.1, 8)], cap_top=True, cap_bottom=True)
        if variant % 2:
            # A second one, tipped over beside it.
            k0 = len(bm.faces)
            tube(bm, [(0.7, -0.2, 0.42), (0.9, 0.8, 0.42)], 0.42, n=8)
        return [(c.lib("barrel_wood"), list(range(len(bm.faces))))]

    return _p(c, name, build)


def crate_stack(c, variant=0):
    name = "Crate Stack %d" % variant

    def build(bm):
        cuboid(bm, (0, 0, 0.5), (1.0, 1.0, 1.0), rot=0.1 * variant)
        if variant % 2 == 0:
            cuboid(bm, (1.1, 0.15, 0.4), (0.8, 0.8, 0.8), rot=0.3)
            cuboid(bm, (0.2, 0.0, 1.4), (0.8, 0.8, 0.8), rot=-0.25)
        else:
            cuboid(bm, (0.15, 0.95, 0.45), (0.9, 0.9, 0.9), rot=-0.2)
        return [(c.lib("board_walk"), list(range(len(bm.faces))))]

    return _p(c, name, build)


def _wheel(bm, x, y, z, r, axis_x=False, spokes=8):
    """A wooden wheel standing up (its axle along Y, or X): a rim of blocks and spokes."""
    n = 12
    for k in range(n):
        a0, a1 = k * math.tau / n, (k + 1) * math.tau / n
        p0 = (math.cos(a0) * r, math.sin(a0) * r)
        p1 = (math.cos(a1) * r, math.sin(a1) * r)
        if axis_x:
            _beam(bm, (x, y + p0[0], z + p0[1]), (x, y + p1[0], z + p1[1]), 0.12, 0.14)
        else:
            _beam(bm, (x + p0[0], y, z + p0[1]), (x + p1[0], y, z + p1[1]), 0.14, 0.12)
    for k in range(spokes):
        a = k * math.tau / spokes
        p = (math.cos(a) * r * 0.95, math.sin(a) * r * 0.95)
        if axis_x:
            _beam(bm, (x, y, z), (x, y + p[0], z + p[1]), 0.06)
        else:
            _beam(bm, (x, y, z), (x + p[0], y, z + p[1]), 0.06)


def wagon_wheel(c):
    """A loose wagon wheel leaning against a wall (origin at the ground)."""
    name = "Wagon Wheel"

    def build(bm):
        _wheel(bm, 0, 0, 0.62, 0.62)
        for v in bm.verts:
            v.co.y += (v.co.z) * 0.18
        return [(c.lib("weathered_timber"), list(range(len(bm.faces))))]

    return _p(c, name, build)


def wagon(c, covered=True, broken=False):
    """A wagon (long along X): its bed, four wheels (one off and lying by it if broken),
    the tongue on the ground, and its torn canvas cover on hoops."""
    name = "Wagon" + (" Covered" if covered else "") + (" Broken" if broken else "")

    def build(bm):
        tilt = 0.35 if broken else 0.0
        cuboid(bm, (0, 0, 1.25 - tilt * 0.5), (4.2, 1.8, 0.7), tilt=(0.0, 0.0))
        cuboid(bm, (0, 0, 0.88 - tilt * 0.5), (4.0, 1.6, 0.12))
        _beam(bm, (2.1, 0, 0.9), (4.6, 0, 0.1), 0.14)
        for wx, wy, r in ((-1.5, -1.0, 0.75), (-1.5, 1.0, 0.75), (1.4, -1.0, 0.55), (1.4, 1.0, 0.55)):
            if broken and wx > 0 and wy > 0:
                continue  # this wheel's off: it lies on the ground beside the wagon
            _wheel(bm, wx, wy, r, r)
        if broken:
            k0 = len(bm.verts)
            _wheel(bm, 2.2, 1.9, 0.0, 0.55)
            bm.verts.ensure_lookup_table()
            for v in bm.verts[k0:]:
                # Laid flat: its upright plane turned down onto the ground.
                v.co.y, v.co.z = 1.9 + v.co.z, 0.1 + (v.co.y - 1.9)
        wood = list(range(len(bm.faces)))
        cover = []
        if covered:
            k0 = len(bm.faces)
            rings_ = []
            for x in (-1.9, -0.9, 0.1, 1.1, 1.9):
                pts = []
                for k in range(7):
                    a = math.pi * k / 6
                    pts.append(bm.verts.new((x, -math.cos(a) * 0.95, 1.6 + math.sin(a) * 1.25 - (0.15 if x in (-0.9, 1.1) else 0.0))))
                rings_.append(pts)
            for lo, hi in zip(rings_, rings_[1:]):
                for k in range(6):
                    if broken and lo[k].co.x > 0.5 and k in (2, 3):
                        continue  # torn through
                    bm.faces.new((lo[k], lo[k + 1], hi[k + 1], hi[k]))
            cover = _faces(bm, k0)
        slots = [(c.lib("weathered_timber"), wood)]
        if cover:
            slots.append((c.lib("canvas_torn"), cover))
        return slots

    return _p(c, name, build)


def trough(c):
    name = "Water Trough"

    def build(bm):
        cuboid(bm, (0, 0, 0.45), (2.6, 0.9, 0.7))
        for x in (-1.1, 1.1):
            cuboid(bm, (x, 0, 0.1), (0.2, 1.0, 0.2))
        return [(c.lib("weathered_timber"), list(range(len(bm.faces))))]

    return _p(c, name, build)


def hitching_rail(c):
    name = "Hitching Rail"

    def build(bm):
        for x in (-1.6, 1.6):
            cuboid(bm, (x, 0, 0.55), (0.18, 0.18, 1.3))
        cuboid(bm, (0, 0, 1.05), (3.6, 0.14, 0.14))
        return [(c.lib("weathered_timber"), list(range(len(bm.faces))))]

    return _p(c, name, build)


def bench(c):
    name = "Bench"

    def build(bm):
        cuboid(bm, (0, 0, 0.45), (1.8, 0.45, 0.08))
        cuboid(bm, (0, 0.2, 0.75), (1.8, 0.06, 0.5))
        for x in (-0.8, 0.8):
            cuboid(bm, (x, 0, 0.22), (0.08, 0.4, 0.45))
        return [(c.lib("weathered_timber"), list(range(len(bm.faces))))]

    return _p(c, name, build)


def coffin(c, open_=False):
    """A pine coffin standing on end against a wall (the undertaker's)."""
    name = "Coffin" + (" Open" if open_ else "")

    def build(bm):
        pts = [(-0.3, 0), (0.3, 0), (0.42, 1.4), (0.25, 2.0), (-0.25, 2.0), (-0.42, 1.4)]
        lo = [bm.verts.new((x, 0.0, z)) for x, z in pts]
        hi = [bm.verts.new((x, 0.4, z)) for x, z in pts]
        loft(bm, [lo, hi], cap_top=True, cap_bottom=True)
        for v in bm.verts:
            v.co.y -= v.co.z * 0.12
        return [(c.lib("board_walk"), list(range(len(bm.faces))))]

    return _p(c, name, build)


# ------------------------------------------------------------------ the graveyard


def headstone(c, variant=0):
    """A weathered headstone: round-topped, square, a cross, or a little obelisk; each
    a little tilted (origin at the ground; faces -Y)."""
    name = "Headstone %d" % variant
    shape = variant % 4

    def build(bm):
        tilt = (0.08 * math.sin(variant * 2.3), 0.1 * math.cos(variant * 1.7))
        if shape == 0:
            cuboid(bm, (0, 0, 0.5), (0.75, 0.18, 1.0), tilt=tilt)
            res = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.375, radius2=0.375, depth=0.18)
            for v in res["verts"]:
                y, z = v.co.y, v.co.z
                v.co.y, v.co.z = z, y + 1.0
        elif shape == 1:
            cuboid(bm, (0, 0, 0.42), (0.85, 0.2, 0.85), tilt=tilt)
            cuboid(bm, (0, 0, 0.9), (0.95, 0.24, 0.12), tilt=tilt)
        elif shape == 2:
            cuboid(bm, (0, 0, 0.7), (0.18, 0.18, 1.4), tilt=tilt)
            cuboid(bm, (0, 0, 1.05), (0.75, 0.18, 0.18), tilt=tilt)
            cuboid(bm, (0, 0, 0.1), (0.5, 0.4, 0.2))
        else:
            cuboid(bm, (0, 0, 0.2), (0.7, 0.7, 0.4))
            _cyl(bm, 0, 0, 0.4, 2.2, 0.26, 0.12, n=4, phase=math.pi / 4)
            res = bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.17, radius2=0.0, depth=0.35)
            for v in res["verts"]:
                v.co.z += 2.37
        # A mound in front.
        blob(bm, (0, -0.9, -0.05), 0.5, sx=1.0, sy=2.0, sz=0.35, subdiv=1)
        return [(c.lib("tombstone"), list(range(len(bm.faces))))]

    return _p(c, name, build)


def grave_cross(c, variant=0):
    """A wooden grave marker: a cross, leaning, its mound in front."""
    name = "Grave Cross %d" % variant

    def build(bm):
        lean = 0.12 * math.sin(variant * 2.1 + 0.5)
        cuboid(bm, (0, 0, 0.75), (0.14, 0.12, 1.6), tilt=(0.0, lean))
        cuboid(bm, (math.sin(lean) * 1.1, 0, 1.15), (0.8, 0.1, 0.13), tilt=(0.0, lean))
        wood = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        blob(bm, (0, -0.9, -0.05), 0.5, sx=1.0, sy=2.0, sz=0.35, subdiv=1)
        return [(c.lib("dead_wood"), wood), (c.lib("graveyard_earth"), _faces(bm, k0))]

    return _p(c, name, build)


def crypt(c, variant=0):
    """A little stone crypt (origin at the ground, door facing -Y): a plinth, walls, a
    pediment and a pitched stone roof, a dark iron door, an urn either side."""
    name = "Crypt %d" % variant
    w, d, h = (3.4, 4.2, 3.0) if variant == 0 else (2.8, 3.6, 2.6)

    def build(bm):
        cuboid(bm, (0, 0, 0.2), (w + 0.6, d + 0.6, 0.4))
        cuboid(bm, (0, 0, 0.4 + h / 2), (w, d, h))
        verts = [bm.verts.new(v) for v in ((-w / 2 - 0.3, -d / 2 - 0.3, h + 0.4), (w / 2 + 0.3, -d / 2 - 0.3, h + 0.4), (w / 2 + 0.3, d / 2 + 0.3, h + 0.4),
                                            (-w / 2 - 0.3, d / 2 + 0.3, h + 0.4), (0, -d / 2 - 0.3, h + 1.6), (0, d / 2 + 0.3, h + 1.6))]
        bm.faces.new((verts[0], verts[1], verts[4]))
        bm.faces.new((verts[2], verts[3], verts[5]))
        bm.faces.new((verts[1], verts[2], verts[5], verts[4]))
        bm.faces.new((verts[3], verts[0], verts[4], verts[5]))
        bm.faces.new((verts[0], verts[3], verts[2], verts[1]))
        for x in (-w / 2 - 0.1, w / 2 + 0.1):
            _cyl(bm, x, -d / 2 - 0.15, 0.4, 0.4 + h, 0.22, 0.22, n=6)
            blob(bm, (x * 1.5, -d / 2 - 0.9, 0.9), 0.35, sz=1.2, subdiv=0)
        stone = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        cuboid(bm, (0, -d / 2 - 0.02, 0.4 + 1.1), (1.3, 0.06, 2.2))
        return [(c.lib("tombstone"), stone), (c.lib("iron"), _faces(bm, k0))]

    return _p(c, name, build)


def iron_fence(c, length=6.0):
    """A run of iron graveyard fence along X: two rails, pickets with spear tips."""
    name = "Iron Fence %.0f" % length

    def build(bm):
        n = int(length / 0.5)
        for k in range(n + 1):
            x = -length / 2 + k * length / n
            h = 1.8 if k % 6 else 2.3
            cuboid(bm, (x, 0, h / 2), (0.06, 0.06, h))
            res = bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.08, radius2=0.0, depth=0.22)
            for v in res["verts"]:
                v.co.x += x
                v.co.z += h + 0.1
        for z in (0.3, 1.5):
            cuboid(bm, (0, 0, z), (length, 0.06, 0.07))
        return [(c.lib("iron"), list(range(len(bm.faces))))]

    return _p(c, name, build)


def cemetery_gate(c):
    """The cemetery's iron gateway: two stone piers and a high iron arch between them."""
    name = "Cemetery Gate"

    def build(bm):
        for x in (-2.6, 2.6):
            cuboid(bm, (x, 0, 1.4), (0.8, 0.8, 2.8))
            blob(bm, (x, 0, 3.1), 0.4, subdiv=0)
        stone = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        for k in range(10):
            a0, a1 = math.pi * k / 10, math.pi * (k + 1) / 10
            _beam(bm, (math.cos(a0) * 2.4, 0, 3.3 + math.sin(a0) * 1.4), (math.cos(a1) * 2.4, 0, 3.3 + math.sin(a1) * 1.4), 0.08)
        for k in range(9):
            x = -2.0 + k * 0.5
            cuboid(bm, (x, 0, 1.5), (0.05, 0.05, 2.6))
        cuboid(bm, (0, 0, 2.8), (4.4, 0.06, 0.07))
        return [(c.lib("tombstone"), stone), (c.lib("iron"), _faces(bm, k0))]

    return _p(c, name, build)


def dead_tree(c, variant=0):
    """A twisted dead tree: a gnarled trunk splitting into crooked, bony branches
    reaching out (origin at the ground). Big, so it reads against the moon."""
    name = "Dead Tree %d" % variant

    def build(bm):
        h = (7.0, 9.5, 5.5, 8.0)[variant % 4]
        lean = 0.6 * math.sin(variant * 1.9)
        trunk = [(0, 0, -0.4), (lean * 0.3, 0.1, h * 0.35), (lean * 0.8, -0.2, h * 0.65), (lean, 0.2, h * 0.8)]
        tube(bm, trunk, [0.55, 0.42, 0.3, 0.2], n=6)
        for k in range(5 + variant % 3):
            a = k * 2.39 + variant * 0.8
            z = h * (0.45 + 0.08 * k)
            base = Vector((lean * z / h, 0, z))
            L = (3.5 - 0.3 * k) * (0.8 + 0.4 * ((k * 7 + variant) % 3) / 2)
            d = Vector((math.cos(a), math.sin(a), 0.55 + 0.25 * math.sin(k * 3.1)))
            d.normalize()
            p1 = base + d * L * 0.5 + Vector((0, 0, 0.3 * math.sin(k)))
            p2 = p1 + Vector((d.x, d.y, d.z + 0.4)).normalized() * L * 0.5
            tube(bm, [tuple(base), tuple(p1), tuple(p2)], [0.18, 0.11, 0.04], n=4)
            # A crooked twig off each.
            tw = p1 + Vector((-d.y, d.x, 0.6)).normalized() * L * 0.35
            tube(bm, [tuple(p1), tuple(tw)], [0.08, 0.03], n=3)
        # The roots, clawing at the ground.
        for k in range(4):
            a = k * math.tau / 4 + 0.4
            tube(bm, [(0, 0, 0.3), (math.cos(a) * 1.3, math.sin(a) * 1.3, -0.1), (math.cos(a) * 1.9, math.sin(a) * 1.9, -0.4)], [0.3, 0.15, 0.05], n=4)
        return [(c.lib("dead_wood"), list(range(len(bm.faces))))]

    return _p(c, name, build)


def cattle_skull(c):
    """A bleached cattle skull with long curving horns (origin at its back, facing -Y)."""
    name = "Cattle Skull"

    def build(bm):
        blob(bm, (0, -0.25, 0), 0.32, sx=0.9, sy=1.0, sz=0.75, subdiv=1)
        blob(bm, (0, -0.65, -0.12), 0.2, sx=0.75, sy=1.3, sz=0.7, subdiv=1)
        for s in (-1, 1):
            tube(bm, [(s * 0.2, -0.15, 0.12), (s * 0.55, -0.1, 0.18), (s * 0.85, -0.2, 0.42), (s * 0.9, -0.35, 0.62)], [0.09, 0.07, 0.05, 0.02], n=5)
        bone = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        for s in (-1, 1):
            blob(bm, (s * 0.15, -0.5, 0.05), 0.07, subdiv=0)
        return [(c.lib("bone"), bone), (c.lib("iron"), _faces(bm, k0))]

    return _p(c, name, build)


# ------------------------------------------------------------------ the mine


def ore_cart(c, glow=False, tipped=False):
    """An ore cart on its little wheels, full of glinting ore (along X)."""
    name = "Ore Cart" + (" Glow" if glow else "") + (" Tipped" if tipped else "")

    def build(bm):
        lo = [bm.verts.new(v) for v in ((-0.8, -0.55, 0.4), (0.8, -0.55, 0.4), (0.8, 0.55, 0.4), (-0.8, 0.55, 0.4))]
        hi = [bm.verts.new(v) for v in ((-1.05, -0.75, 1.3), (1.05, -0.75, 1.3), (1.05, 0.75, 1.3), (-1.05, 0.75, 1.3))]
        loft(bm, [lo, hi], cap_top=False, cap_bottom=True)
        for x in (-0.55, 0.55):
            for y in (-0.6, 0.6):
                tube(bm, [(x, y - 0.08, 0.28), (x, y + 0.08, 0.28)], 0.28, n=8)
        cuboid(bm, (0, 0, 0.36), (1.4, 0.9, 0.12))
        metal = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        blob(bm, (0, 0, 1.2), 0.75, sx=1.3, sy=0.9, sz=0.4, subdiv=1)
        ore = _faces(bm, k0)
        if tipped:
            for v in bm.verts:
                x, z = v.co.x, v.co.z
                v.co.x, v.co.z = x * math.cos(1.2) - z * math.sin(1.2), x * math.sin(1.2) + z * math.cos(1.2) + 0.7
        return [(c.lib("iron"), metal), (c.lib("ore_pile" if glow else "mine_floor"), ore)]

    return _p(c, name, build)


def ore_heap(c, variant=0):
    name = "Ore Heap %d" % variant

    def build(bm):
        for k in range(3 + variant):
            a = k * 2.2 + variant
            blob(bm, (math.cos(a) * 0.9, math.sin(a) * 0.9, 0.2), 1.0 + 0.3 * (k % 2), sz=0.55, subdiv=1)
        return [(c.lib("ore_pile"), list(range(len(bm.faces))))]

    return _p(c, name, build)


def pick_and_shovel(c):
    """A pickaxe and a shovel leaning together, a lantern beside them on the ground."""
    name = "Pick And Shovel"

    def build(bm):
        _beam(bm, (0, 0, 0), (0.2, 0.25, 1.3), 0.06)
        cuboid(bm, (0.2, 0.25, 1.32), (0.12, 0.9, 0.1), tilt=(0.15, 0.0))
        _beam(bm, (0.5, 0, 0), (0.35, 0.25, 1.4), 0.06)
        wood = list(range(len(bm.faces)))
        k0 = len(bm.faces)
        cuboid(bm, (0.53, -0.04, 0.2), (0.32, 0.06, 0.42), tilt=(0.18, 0.0))
        iron = _faces(bm, k0)
        i2, glass = _lantern(bm, -0.5, -0.2, 0.75)
        return [(c.lib("weathered_timber"), wood), (c.lib("iron"), iron + i2), (c.lib("lantern_glass"), glass)]

    return _p(c, name, build)


def spectral_crystals(c, variant=0):
    """A cluster of glowing green crystals growing out of the rock: a few long pointed
    prisms leaning out from a common root (origin at the root; grows up +Z)."""
    name = "Spectral Crystals %d" % variant

    def build(bm):
        n = 4 + variant % 3
        for k in range(n):
            a = k * 2.39 + variant
            tilt = 0.25 + 0.3 * ((k * 5 + variant) % 3) / 2
            L = (1.6 + 1.4 * ((k * 3 + variant) % 4) / 3) * (1.3 if k == 0 else 1.0)
            r = 0.22 + 0.12 * (k == 0)
            d = Vector((math.cos(a) * math.sin(tilt), math.sin(a) * math.sin(tilt), math.cos(tilt)))
            side = d.cross(Vector((0, 0, 1)))
            if side.length < 1e-3:
                side = Vector((1, 0, 0))
            side.normalize()
            up = side.cross(d).normalized()
            base = [bm.verts.new(side * math.cos(j * math.tau / 6) * r + up * math.sin(j * math.tau / 6) * r - d * 0.2) for j in range(6)]
            mid = [bm.verts.new(side * math.cos(j * math.tau / 6) * r + up * math.sin(j * math.tau / 6) * r + d * L * 0.75) for j in range(6)]
            tip = bm.verts.new(d * L)
            for j in range(6):
                bm.faces.new((base[j], base[(j + 1) % 6], mid[(j + 1) % 6], mid[j]))
                bm.faces.new((mid[j], mid[(j + 1) % 6], tip))
        return [(c.lib("crystal_ghost"), list(range(len(bm.faces))))]

    return _p(c, name, build)


def timber_set(c, half=6.4, height=8.2, broken=False):
    """A mine's timber set: two posts, a cap beam and lagging boards over it, braced at
    the corners (across X, origin on the floor at its middle). `broken`: the cap
    snapped and hanging."""
    name = "Timber Set %.1f %.1f%s" % (half, height, " Broken" if broken else "")

    def build(bm):
        for s in (-1, 1):
            _beam(bm, (s * half, 0, -0.4), (s * (half - 0.4), 0, height), 0.45)
            _beam(bm, (s * (half - 0.3), 0, height - 1.6), (s * (half - 1.8), 0, height - 0.2), 0.25)
        if broken:
            _beam(bm, (-half, 0, height), (0.4, 0.3, height - 0.5), 0.5)
            _beam(bm, (0.6, -0.2, height - 0.7), (half - 0.4, 0, height - 3.0), 0.5)
        else:
            _beam(bm, (-half - 0.2, 0, height), (half + 0.2, 0, height), 0.55)
            for k in range(5):
                x = -half + 0.8 + k * (2 * half - 1.6) / 4
                cuboid(bm, (x, 0, height + 0.38), (0.5, 2.6, 0.12))
        return [(c.lib("mine_timber"), list(range(len(bm.faces))))]

    return _p(c, name, build)


def mine_portal(c, half=7.4, height=9.5):
    """The mine's great timber portal: doubled posts, a heavy cap, raked struts, lagging
    over the top and a beam for the sign (across X, origin on the floor; faces -Y)."""
    name = "Mine Portal"

    def build(bm):
        for s in (-1, 1):
            for dy in (-0.5, 0.5):
                _beam(bm, (s * half, dy, -0.5), (s * (half - 0.5), dy, height), 0.8)
            _beam(bm, (s * (half + 3.5), -2.5, -0.5), (s * (half - 0.2), -0.2, height - 2.0), 0.5)
        for dy in (-0.6, 0.6):
            _beam(bm, (-half - 1.2, dy, height + 0.3), (half + 1.2, dy, height + 0.3), 0.9)
        for k in range(9):
            x = -half + k * 2 * half / 8
            cuboid(bm, (x, 0, height + 1.0), (0.9, 3.4, 0.25), rot=0.05 * math.sin(k * 2.0))
        # Broken planks hanging off one side, and the sign's beam.
        _beam(bm, (half - 1.0, -1.6, height + 0.9), (half + 0.6, -1.9, height - 2.4), 0.3, 0.12)
        _beam(bm, (-half - 1.4, -0.95, height + 2.6), (half + 1.4, -0.95, height + 2.6), 0.4)
        return [(c.lib("mine_timber"), list(range(len(bm.faces))))]

    return _p(c, name, build)


def winch(c):
    """An old steam winch: a boiler on skids, its stack, and a cable drum."""
    name = "Winch"

    def build(bm):
        cuboid(bm, (0, 0, 0.2), (4.0, 1.8, 0.4))
        tube(bm, [(-1.6, 0, 1.3), (0.8, 0, 1.3)], 0.9, n=10)
        _cyl(bm, -1.0, 0, 2.0, 5.5, 0.28, 0.24, n=8)
        tube(bm, [(1.5, -0.8, 1.0), (1.5, 0.8, 1.0)], 0.55, n=10)
        return [(c.lib("iron"), list(range(len(bm.faces))))]

    return _p(c, name, build)


def chain_hang(c, length=4.0):
    """A chain hanging from a beam (links as little boxes, origin at the top)."""
    name = "Chain %.0f" % length

    def build(bm):
        n = int(length / 0.22)
        for k in range(n):
            z = -k * 0.22
            cuboid(bm, (0, 0, z - 0.11), (0.06 if k % 2 else 0.16, 0.16 if k % 2 else 0.06, 0.26))
        return [(c.lib("iron"), list(range(len(bm.faces))))]

    return _p(c, name, build)


def tumbleweed(c, variant=0):
    """A tumbleweed at rest (a ball of thin twigs)."""
    name = "Tumbleweed %d" % variant

    def build(bm):
        r = 0.7 + 0.15 * variant
        for k in range(14):
            a = k * 2.39
            b = math.acos(1 - 2 * (k + 0.5) / 14)
            p = Vector((math.sin(b) * math.cos(a), math.sin(b) * math.sin(a), math.cos(b))) * r
            q = Vector((math.sin(b + 1.4) * math.cos(a + 2.0), math.sin(b + 1.4) * math.sin(a + 2.0), math.cos(b + 1.4))) * r
            _beam(bm, tuple(p + Vector((0, 0, r))), tuple(q + Vector((0, 0, r))), 0.05)
        return [(c.lib("dead_wood"), list(range(len(bm.faces))))]

    return _p(c, name, build)
