# Oasis Haven's scenery (see oasis_haven.py): a small oasis in the deep desert. Mud-brick
# houses with lit windows and beam ends along the village street and a gateway over the
# start, a nomad camp of dark woven tents (rugs, cushions and hanging lanterns inside,
# a campfire, rugs airing on lines), palms round the green pool and through the grove,
# the wind-carved butte and arch, the ruined watchtower on its mesa, scrub and rocks on
# the dunes, and far buttes on the horizon.
# SPDX-License-Identifier: MIT
#
# All original designs. Every solid near the road keeps the footprint the greybox had,
# so the lap drives as it did.

import math

import oasis_props as op
from course_kit import Vector, bmesh, lerp, rnd
from props import _faces, blob, cuboid, loft, ring, tube


def road_rot(q):
    return math.atan2(q.t.y, q.t.x)


def ground(c, ter, x, y, default=None):
    z = c.ground_z(x, y, ter)
    return default if z is None else z


class Mesh:
    """Faces gathered by material into one object."""

    def __init__(self):
        self.bm = bmesh.new()
        self.mats = {}

    def add(self, mat, fn):
        k0 = len(self.bm.faces)
        fn(self.bm)
        self.mats.setdefault(mat, []).extend(range(k0, len(self.bm.faces)))

    def build(self, c, name, coll, role="both"):
        ob = c.mesh_object(name, self.bm, coll, role)
        for mat, faces in self.mats.items():
            c.assign(ob, c.lib(*mat), faces)
        ob.data.shade_flat()
        return ob


# ------------------------------------------------------------------ props


class Parts:
    """Faces of one prop, gathered by material while it's built."""

    def __init__(self, bm):
        self.bm = bm
        self.slots = {}

    def add(self, mat, fn, *a, **k):
        k0 = len(self.bm.faces)
        fn(self.bm, *a, **k)
        self.slots.setdefault(mat, []).extend(range(k0, len(self.bm.faces)))

    def poly(self, mat, pts, both=False):
        k0 = len(self.bm.faces)
        vs = [self.bm.verts.new(p) for p in pts]
        self.bm.faces.new(vs)
        if both:
            self.bm.faces.new([self.bm.verts.new(p) for p in reversed(pts)])
        self.slots.setdefault(mat, []).extend(range(k0, len(self.bm.faces)))

    def out(self, c):
        return [(c.lib(m), f) for m, f in self.slots.items() if f]


def _arch(cx, y, z0, w, h, n=6, point=0.3):
    """The outline of a pointed arch (a doorway or window) on the plane at depth y,
    from its sill z0, w wide and h tall: straight sides, then two arcs, each centred
    `point` of the half-width across the middle, meeting in a point."""
    e = point * w / 2
    r = w / 2 + e
    rise = math.sqrt(r * r - e * e)
    spring = z0 + h - rise
    top = math.acos(e / r)
    right = [(cx - e + r * math.cos(top * k / n), y, spring + r * math.sin(top * k / n)) for k in range(n + 1)]
    left = [(2 * cx - x, y, z) for x, y, z in reversed(right[:-1])]
    return [(cx - w / 2, y, z0), (cx + w / 2, y, z0)] + right + left[: -1] + [(cx - w / 2, y, spring)]


def _merlons(P, mat, x0, x1, y0, y1, z, every=1.3):
    """Stepped merlons (two tiers) along the four edges of a roof at height z."""
    def row(a, b, fixed, along_x):
        n = max(2, int(abs(b - a) / every))
        for i in range(n):
            u = a + (b - a) * (i + 0.5) / n
            x, y = (u, fixed) if along_x else (fixed, u)
            P.add(mat, cuboid, (x, y, z + 0.3), (0.75, 0.42, 0.6) if along_x else (0.42, 0.75, 0.6))
            P.add(mat, cuboid, (x, y, z + 0.8), (0.4, 0.42, 0.45) if along_x else (0.42, 0.4, 0.45))

    row(x0, x1, y0, True)
    row(x0, x1, y1, True)
    row(y0, y1, x0, False)
    row(y0, y1, x1, False)


def house(c, variant=0, w=9.0, d=8.0, h=7.0):
    """A rich mud-brick town house: a ground floor and a set-back upper storey with a
    terrace in front, stepped merlons in white plaster on every roof line over a blue
    tiled frieze, a pointed-arch doorway in a framed, tiled surround with a studded
    door and lanterns either side, pointed lit windows, a latticed wooden oriel on the
    upper floor, and (by variant) a turquoise onion dome on a drum, a wind tower or a
    hanging carpet. Faces -Y (its door), origin at its foot. Visual only: house_collider
    is its solid."""
    name = "Town House %d %d %d" % (variant, int(w), int(h))

    def build(bm):
        P = Parts(bm)
        h1 = h * 0.58
        # The ground floor, its plinth, and the upper storey set back for a terrace.
        P.add("adobe", cuboid, (0, 0, h1 / 2), (w, d, h1))
        P.add("adobe_dark", cuboid, (0, 0, 0.45), (w + 0.3, d + 0.3, 0.9))
        uw, ud = w * 0.72, d * 0.7
        uy = d / 2 - ud / 2
        P.add("adobe", cuboid, (w * 0.08 * (1 if variant % 2 else -1), uy, h1 + (h - h1) / 2), (uw, ud, h - h1))
        ux = w * 0.08 * (1 if variant % 2 else -1)
        # Tiled friezes under each roof line, and white plaster cornices over them.
        P.add("tile_border", cuboid, (0, 0, h1 - 0.45), (w + 0.12, d + 0.12, 0.5))
        P.add("white_plaster", cuboid, (0, 0, h1 + 0.05), (w + 0.35, d + 0.35, 0.22))
        P.add("tile_border", cuboid, (ux, uy, h - 0.45), (uw + 0.12, ud + 0.12, 0.5))
        P.add("white_plaster", cuboid, (ux, uy, h + 0.05), (uw + 0.35, ud + 0.35, 0.22))
        _merlons(P, "white_plaster", -w / 2 + 0.25, w / 2 - 0.25, -d / 2 + 0.25, d / 2 - 0.25, h1 + 0.15)
        _merlons(P, "white_plaster", ux - uw / 2 + 0.25, ux + uw / 2 - 0.25, uy - ud / 2 + 0.25, uy + ud / 2 - 0.25, h + 0.15)
        # The doorway: a framed surround (white, then tile), a pointed arch, a studded door.
        fy = -d / 2 - 0.2
        P.add("white_plaster", cuboid, (0, -d / 2 - 0.08, 2.0), (3.2, 0.16, 4.0))
        P.add("tile_border", cuboid, (0, -d / 2 - 0.12, 2.0), (2.7, 0.12, 3.6))
        P.poly("door_wood", _arch(0.0, fy - 0.01, 0.0, 1.9, 3.3))
        for i in range(3):
            for j in range(4):
                P.add("gold_trim", cuboid, (-0.55 + i * 0.55, fy - 0.04, 0.5 + j * 0.6), (0.1, 0.06, 0.1))
        for side in (-1, 1):
            P.add("iron", cuboid, (side * 1.9, -d / 2 - 0.3, 2.9), (0.08, 0.5, 0.08))
            P.add("lantern_glow", blob, (side * 1.9, -d / 2 - 0.55, 2.6), 0.24, sz=1.5, subdiv=0)
        # Pointed windows, lit, either side of the door and round the back.
        for x in (-w / 2 + 1.5, w / 2 - 1.5):
            P.poly("lantern_glow", _arch(x, -d / 2 - 0.03, h1 * 0.38, 0.9, 1.6))
            P.poly("lantern_glow", list(reversed(_arch(x, d / 2 + 0.03, h1 * 0.38, 0.9, 1.6))))
        # The upper storey: windows, and a latticed oriel over the door.
        for x in (ux - uw / 2 + 1.2, ux + uw / 2 - 1.2):
            P.poly("lantern_glow", _arch(x, uy - ud / 2 - 0.03, h1 + 0.8, 0.8, 1.5))
        oy = uy - ud / 2
        P.add("door_wood", cuboid, (ux, oy - 0.4, h1 + 0.6), (2.0, 0.85, 0.3))
        P.add("door_wood", cuboid, (ux, oy - 0.4, h1 + 2.5), (2.2, 0.95, 0.25))
        for sx in (-0.95, 0.95):
            P.add("door_wood", cuboid, (ux + sx, oy - 0.75, h1 + 1.55), (0.14, 0.14, 1.9))
        P.poly("lattice_window", [(ux - 0.9, oy - 0.8, h1 + 0.75), (ux + 0.9, oy - 0.8, h1 + 0.75), (ux + 0.9, oy - 0.8, h1 + 2.4), (ux - 0.9, oy - 0.8, h1 + 2.4)])
        for sx in (-1, 1):
            P.poly("lattice_window", [(ux + sx * 0.92, oy - 0.05, h1 + 0.75), (ux + sx * 0.92, oy - 0.78, h1 + 0.75), (ux + sx * 0.92, oy - 0.78, h1 + 2.4), (ux + sx * 0.92, oy - 0.05, h1 + 2.4)][:: -sx])
        # Variants: a dome on a drum; a wind tower; a carpet hung over the terrace wall.
        if variant % 4 in (1, 3):
            dx, dy = ux - uw * 0.18, uy + ud * 0.1
            r = min(uw, ud) * 0.3
            P.add("white_plaster", lambda bm: oasis_props_cyl(bm, dx, dy, h, h + 1.1, r * 1.05, n=12))
            P.add("tile_border", lambda bm: oasis_props_cyl(bm, dx, dy, h + 1.1, h + 1.35, r * 1.12, n=12))
            P.add("dome_teal" if variant % 4 == 1 else "dome_blue", lambda bm: op.dome(bm, dx, dy, h + 1.35, r, h=r * 1.25, n=14, rings=6, onion=0.45))
            P.add("gold_trim", lambda bm: op.finial(bm, dx, dy, h + 1.35 + r * 1.25 * 1.4, 0.7))
        if variant % 4 == 2:
            tx, ty = ux + uw / 2 - 1.0, uy + ud / 2 - 1.0
            P.add("adobe", cuboid, (tx, ty, h + 2.2), (1.8, 1.8, 4.4))
            P.add("white_plaster", cuboid, (tx, ty, h + 4.55), (2.2, 2.2, 0.3))
            for a in range(4):
                nx, ny = (0, -1, 0, 1)[a], (-1, 0, 1, 0)[a]
                for k in (-0.45, 0.0, 0.45):
                    cx, cy = tx + nx * 0.91 + (ny != 0) * k, ty + ny * 0.91 + (nx != 0) * k
                    P.add("oasis_bark", cuboid, (cx, cy, h + 3.4), (0.22 if ny else 0.04, 0.22 if nx else 0.04, 1.6))
            _merlons(P, "white_plaster", tx - 0.9, tx + 0.9, ty - 0.9, ty + 0.9, h + 4.7, every=0.9)
        if variant % 4 in (0, 2):
            cx = -w / 2 + 1.8 if variant % 2 == 0 else w / 2 - 1.8
            P.poly("royal_carpet", [(cx - 0.9, -d / 2 - 0.2, h1 + 0.35), (cx + 0.9, -d / 2 - 0.2, h1 + 0.35), (cx + 0.9, -d / 2 - 0.24, h1 - 2.0), (cx - 0.9, -d / 2 - 0.24, h1 - 2.0)][::-1], both=True)
        # A striped awning over the door on some.
        if variant % 3 == 0:
            P.poly("awning_teal", [(-1.7, -d / 2 - 0.2, 4.2), (1.7, -d / 2 - 0.2, 4.2), (1.7, -d / 2 - 1.5, 3.6), (-1.7, -d / 2 - 1.5, 3.6)][::-1], both=True)
        return P.out(c)

    return c.proto(name, build) and name


def oasis_props_cyl(bm, x, y, z0, z1, r, n=10):
    loft(bm, [ring(bm, (x, y), r, z0, n), ring(bm, (x, y), r, z1, n)], cap_top=True, cap_bottom=False)


def collider(c, w, d, h, y0=0.0, mat="adobe"):
    """An invisible solid box (w across, d deep, h tall, its centre y0 along its depth):
    what a prop's footprint is to the karts, so its trim and cloth don't catch them."""
    name = "Collider %.1f %.1f %.1f %.1f %s" % (w, d, h, y0, mat)

    def build(bm):
        cuboid(bm, (0, y0, h / 2), (w, d, h))
        return [(c.lib(mat, "wall"), _faces(bm, 0))]

    return c.proto(name, build) and name


def tent(c, variant=0, w=14.0, d=9.0):
    """A grand nomad pavilion: a long striped roof over three tall poles (gold finials
    and pennants above), its back and sides pegged down with guy ropes, and a deep
    canopy out front on its own poles, hung with a scalloped, tasselled valance. Inside,
    a great carpet, heaps of cushions, a low brass table and lanterns. Faces -Y (its open
    front), origin at the middle of its foot; the body spans y in (-d/2, d/2) and the
    canopy reaches 2.5 m further out. Visual only: TENT_SOLID is its footprint."""
    name = "Grand Tent %d" % variant
    cloths = ("tent_cloth", "tent_cloth_red") if variant % 2 == 0 else ("tent_cloth_red", "tent_cloth")
    trim = ("banner_red", "banner_royal")[variant % 2]

    def build(bm):
        P = Parts(bm)
        H, E = 6.2, 2.6  # the poles' height and the eaves'
        xs = [-w / 2 + w * i / 8 for i in range(9)]
        # Peaks over the three poles (at -w/3, 0, w/3), dipping between.
        def ridge_z(x):
            return E + 1.0 + (H - E - 1.0) * max(0.0, 1 - min(abs(x - p) for p in (-w / 3, 0.0, w / 3)) / (w / 5)) ** 0.8

        front = [(x, -d / 2, E) for x in xs]
        ridge = [(x, 0.0, ridge_z(x)) for x in xs]
        back = [(x, d / 2, E - 0.2) for x in xs]
        foot = [(x, d / 2 + 0.8, 0.0) for x in xs]
        for i in range(8):
            m = cloths[i % 2]
            P.poly(m, [front[i], front[i + 1], ridge[i + 1], ridge[i]], both=True)
            P.poly(m, [ridge[i], ridge[i + 1], back[i + 1], back[i]], both=True)
            P.poly(m, [back[i], back[i + 1], foot[i + 1], foot[i]], both=True)
        for side, i in ((-1, 0), (1, 8)):
            fl = (side * (w / 2 + 0.7), -d / 2 + 0.6, 0.0)
            pts = [front[i], ridge[i], back[i], foot[i], fl]
            P.poly(cloths[0], pts if side < 0 else pts[::-1], both=True)
        # The canopy out front, sloping a little, and its valance.
        cz0, cz1, cy = E + 0.1, E - 0.3, -d / 2 - 2.5
        P.poly(cloths[1], [(-w / 2, -d / 2, cz0), (w / 2, -d / 2, cz0), (w / 2, cy, cz1), (-w / 2, cy, cz1)][::-1], both=True)
        n = 14
        for i in range(n):
            x0, x1 = -w / 2 + w * i / n, -w / 2 + w * (i + 1) / n
            P.poly(trim, [(x0, cy - 0.02, cz1), (x1, cy - 0.02, cz1), ((x0 + x1) / 2, cy - 0.02, cz1 - 0.6)], both=True)
            P.add("gold_trim", blob, ((x0 + x1) / 2, cy - 0.04, cz1 - 0.72), 0.09, subdiv=0)
        P.add("gold_trim", cuboid, (0, cy - 0.03, cz1 + 0.05), (w, 0.06, 0.12))
        # Poles: the three tall ones (through the roof, finials and pennants on top), the
        # canopy's, and the eave's.
        for x in (-w / 3, 0.0, w / 3):
            P.add("weathered_timber", tube, [(x, 0.0, 0.0), (x, 0.0, H + 1.6)], 0.14, n=6)
            P.add("gold_trim", lambda bm, x=x: op.finial(bm, x, 0.0, H + 1.6, 0.5))
            P.poly(trim, [(x, 0.0, H + 2.7), (x + 1.6, 0.0, H + 2.45), (x, 0.0, H + 2.15)], both=True)
        for x in (-w / 2, -w / 6, w / 6, w / 2):
            P.add("weathered_timber", tube, [(x, cy, 0.0), (x, cy, cz1)], 0.1, n=5)
            P.add("gold_trim", blob, (x, cy, cz1 + 0.12), 0.16, subdiv=0)
        P.add("weathered_timber", tube, [(-w / 2, -d / 2, E), (w / 2, -d / 2, E)], 0.08, n=4)
        # Guy ropes out to pegs at the back and sides.
        for x in (-w / 3, 0.0, w / 3):
            P.add("rope_rail", tube, [(x, d / 2 * 0.6, ridge_z(x) * 0.8), (x, d / 2 + 3.5, 0.0)], 0.03, n=3)
        for side in (-1, 1):
            P.add("rope_rail", tube, [(side * w / 2, cy, cz1), (side * (w / 2 + 2.2), cy - 1.2, 0.0)], 0.03, n=3)
        # Inside: the carpet, cushions, a low brass table, lanterns under the canopy.
        P.add("royal_carpet", cuboid, (0, -0.6, 0.05), (w - 1.4, d + 1.6, 0.1))
        for i in range(7):
            x = -w / 2 + 1.4 + i * (w - 2.8) / 6
            P.add(("awning_sun", "awning_red", "awning_teal")[i % 3], blob, (x, d / 2 - 1.0, 0.4), 0.6, sx=1.5, sz=0.6, subdiv=0)
            if i % 2 == 0:
                P.add(("awning_teal", "awning_sun")[i % 4 == 0], blob, (x + 0.4, d / 2 - 1.9, 0.3), 0.45, sx=1.2, sz=0.55, subdiv=0)
        P.add("gold_trim", lambda bm: oasis_props_cyl(bm, 0.0, 0.2, 0.0, 0.45, 1.1, n=12))
        P.add("gold_trim", lambda bm: oasis_props_cyl(bm, 0.0, 0.2, 0.45, 0.55, 1.35, n=12))
        for x in (-w / 3, 0.0, w / 3):
            P.add("iron", tube, [(x, cy + 0.3, cz1), (x, cy + 0.3, cz1 - 0.5)], 0.02, n=3)
            P.add("lantern_glow", loft, [ring(bm, (x, cy + 0.3), r, z, 6) for r, z in ((0.05, cz1 - 0.5), (0.26, cz1 - 0.75), (0.26, cz1 - 1.15), (0.05, cz1 - 1.35))], cap_top=True, cap_bottom=True)
        return P.out(c)

    return c.proto(name, build) and name


def scrub(c, variant=0):
    """A desert shrub: a low dusty clump."""
    name = "Desert Scrub %d" % variant

    def build(bm):
        for i in range(5):
            a = i * 1.3 + variant
            blob(bm, (0.7 * math.cos(a), 0.7 * math.sin(a), 0.4), 0.55 + 0.15 * rnd(i + variant), sz=0.7, subdiv=0)
        return [(c.lib("dry_grass"), _faces(bm, 0))]

    return c.proto(name, build) and name


def stones(c, variant=0):
    name = "Desert Stone %d" % variant

    def build(bm):
        res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
        for i, v in enumerate(res["verts"]):
            k = 0.75 + 0.5 * rnd(i * 3.1 + variant * 7)
            v.co = Vector((v.co.x * k * 1.3, v.co.y * k, v.co.z * k * 0.7 + 0.25))
        return [(c.lib("gold_cliff"), _faces(bm, 0))]

    return c.proto(name, build) and name


def rug_line(c):
    """Two posts and a line with rugs hung over it to air."""
    name = "Rug Line"

    def build(bm):
        for x in (-3.0, 3.0):
            tube(bm, [(x, 0, 0), (x, 0, 2.6)], 0.08, n=4)
        tube(bm, [(-3.0, 0, 2.5), (3.0, 0, 2.5)], 0.03, n=4)
        posts = _faces(bm, 0)
        k = len(bm.faces)
        for i, x in enumerate((-2.0, 0.0, 2.0)):
            v = [bm.verts.new(p) for p in ((x - 0.8, -0.02, 2.5), (x + 0.8, -0.02, 2.5), (x + 0.8, -0.1, 0.9 + 0.2 * i), (x - 0.8, -0.1, 0.9 + 0.2 * i))]
            bm.faces.new(v)
            bm.faces.new([bm.verts.new(q.co + Vector((0, 0.04, 0))) for q in reversed(v)])
        rugs = _faces(bm, k)
        return [(c.lib("weathered_timber"), posts), (c.lib("rug"), rugs)]

    return c.proto(name, build) and name


# ------------------------------------------------------------------ the village


def village(c, oh, ter, sc):
    """The mud-brick houses (where the greybox's blocks stood), lantern posts, palms and
    a couple of stalls along the street, and the gateway over the start."""
    s = 6.0
    k = 0
    while s < oh.SEG[3]:
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 9.0 + 3 * (k % 2)))
            h = 6.0 + 2.5 * ((k + (side > 0)) % 3)
            rot = road_rot(q) + (math.pi if side > 0 else 0.0)
            c.place(house(c, (k + (side > 0)) % 4, 9.0, 8.0, h), p.x, p.y, q.p.z - 0.5, rot=rot, coll="Village", role="visual")
            c.place(collider(c, 9.0, 8.0, h), p.x, p.y, q.p.z - 0.5, rot=rot, coll="Village", role="collision")
            sc["lights"].append((p.x, p.y, q.p.z + h * 0.6))
        s += 16.0
        k += 1
    q = c.at(oh.LENGTH - 30)
    for side in (-1, 1):
        p = q.side(side * (q.w / 2 + 10.0))
        rot = road_rot(q) + (math.pi if side > 0 else 0.0)
        c.place(house(c, 1 + 2 * (side > 0), 10.0, 9.0, 8.0), p.x, p.y, q.p.z - 0.5, rot=rot, coll="Village", role="visual")
        c.place(collider(c, 10.0, 9.0, 8.0), p.x, p.y, q.p.z - 0.5, rot=rot, coll="Village", role="collision")
    # Lantern posts along the street, a stall or two and some palms behind the houses.
    post = op.lantern_post(c)
    s = 4.0
    k = 0
    while s < oh.SEG[3] + 10:
        q = c.at(s)
        side = 1 if k % 2 else -1
        p = q.side(side * (q.w / 2 + 2.6))
        c.place(post, p.x, p.y, ground(c, ter, p.x, p.y, q.p.z) - 0.1, rot=road_rot(q), coll="Village", role="visual")
        sc["lanterns"].append((p.x, p.y, ground(c, ter, p.x, p.y, q.p.z) + 4.4))
        s += 24.0
        k += 1
    for k, s in enumerate((oh.SEG[1] + 8, oh.SEG[2] + 22)):
        q = c.at(s)
        p = q.side((1 if k else -1) * (q.w / 2 + 5.0))
        c.place(op.market_stall(c, k), p.x, p.y, ground(c, ter, p.x, p.y, q.p.z) - 0.1, rot=road_rot(q) + (math.pi if k else 0.0), coll="Village", role="visual")
    palms = [op.palm(c, v, 9.0 + 2 * v) for v in range(4)]
    for k in range(10):
        s = 12.0 + k * 17.0
        q = c.at(s)
        p = q.side((1 if k % 2 else -1) * (q.w / 2 + 22.0 + 4 * (k % 3)))
        z = ground(c, ter, p.x, p.y)
        if z is not None:
            c.place(palms[k % 4], p.x, p.y, z - 0.2, rot=k * 1.7, coll="Village", role="visual")
    # The gateway over the street at the start: two towers and a crenellated span with the
    # checkered board.
    q = c.at(8.0)
    m = Mesh()
    rot = road_rot(q)
    for side in (-1, 1):
        p = q.side(side * (q.w / 2 + 2.6))
        m.add(("adobe", "wall"), lambda bm, p=p: cuboid(bm, (p.x, p.y, q.p.z + 5.5), (3.6, 3.6, 12.0), rot))
        m.add(("adobe_dark", "wall"), lambda bm, p=p: cuboid(bm, (p.x, p.y, q.p.z + 0.4), (4.0, 4.0, 1.4), rot))
    span = q.w + 8.8
    m.add(("adobe", "wall"), lambda bm: cuboid(bm, (q.p.x, q.p.y, q.p.z + 10.4), (span, 2.6, 2.4), rot + math.pi / 2))
    for i in range(7):
        o = -span / 2 + 0.8 + i * (span - 1.6) / 6
        p = q.side(o, 0.0)
        m.add(("adobe", "wall"), lambda bm, p=p: cuboid(bm, (p.x, p.y, q.p.z + 12.1), (0.9, 2.2, 1.0), rot))
    m.add(("start_checker", "wall"), lambda bm: cuboid(bm, (q.p.x + q.t.x * -1.4, q.p.y + q.t.y * -1.4, q.p.z + 9.0), (q.w - 1.0, 0.2, 1.8), rot + math.pi / 2))
    m.build(c, "Village Gate", "Village", "visual")


# ------------------------------------------------------------------ the camp


def camp(c, oh, ter, sc, make=None):
    """The nomad camp along the weave: a tent where each of the greybox's stood, a
    lantern by each, rugs airing on lines and a campfire in the middle. (`make(c, k)`:
    another tent in each one's place: the ruin's burnt ones.)"""
    s = oh.SEG[10] + 8
    k = 0
    fire = None
    line = rug_line(c)
    while s < oh.SEG[16]:
        q = c.at(s)
        side = 1 if k % 2 else -1
        # The canopy's front is where the greybox tent's front was (4 m off the road);
        # the solid covers the canopy and the body.
        p = q.side(side * (q.w / 2 + 11.0))
        rot = road_rot(q) + (math.pi if side > 0 else 0.0)
        c.place((make or tent)(c, k % 2), p.x, p.y, q.p.z - 0.05, rot=rot, coll="Camp", role="visual")
        c.place(collider(c, 14.0, 12.3, 3.0, -0.85, "tent_cloth"), p.x, p.y, q.p.z - 0.05, rot=rot, coll="Camp", role="collision")
        lp = q.side(side * (q.w / 2 + 2.2))
        sc["torches"].append((lp.x, lp.y, q.p.z + 3.2))
        sc["lanterns"].append((lp.x, lp.y, q.p.z + 3.2))
        if k % 2 == 0:
            b = q.side(side * (q.w / 2 + 21.0))
            z = ground(c, ter, b.x, b.y)
            if z is not None:
                c.place(line, b.x, b.y, z - 0.1, rot=road_rot(q), coll="Camp", role="visual")
        if k == 2:
            fire = q.side(-side * (q.w / 2 + 14.0))
        s += 18.0
        k += 1
    for x in range(len(sc["torches"])):
        tx, ty, tz = sc["torches"][x]
        post = Mesh()
        post.add(("weathered_timber", "wall"), lambda bm, tx=tx, ty=ty, tz=tz: tube(bm, [(tx, ty, tz - 3.4), (tx, ty, tz + 0.3)], 0.09, n=4))
        post.add(("lantern_glow", "wall"), lambda bm, tx=tx, ty=ty, tz=tz: blob(bm, (tx, ty, tz), 0.32, sz=1.4, subdiv=0))
        post.build(c, "Camp Lantern %d" % x, "Camp", "visual")
    if fire is not None:
        import props  # noqa: E402

        z = ground(c, ter, fire.x, fire.y, 3.0)
        c.place(props.campfire(c), fire.x, fire.y, z - 0.05, coll="Camp", role="visual")
        sc["fires"].append((fire.x, fire.y, z))


# ------------------------------------------------------------------ the pool and the grove


def pool(c, oh, ter, sc):
    """Palms round the pool (where the greybox's stood) and two in the grove to dodge,
    reeds in the shallows and a few rocks on the bank."""
    import props  # noqa: E402

    palms = [op.palm(c, v, 10.0 + 1.5 * v) for v in range(4)]
    # Only a palm's trunk is solid: its fronds are leaves, not something to land on.
    trunk = "Palm Trunk Solid"

    def _trunk(bm):
        op._cyl(bm, 0.0, 0.0, 0.0, 6.0, 0.55, 0.45, n=8)
        return [(c.lib("oasis_bark", "wall"), _faces(bm, 0))]

    c.proto(trunk, _trunk)
    for k in range(22):
        a = k * math.tau / 22
        r = oh.POOL[2] + 9.0 + 4.0 * math.sin(k * 2.1)
        x, y = oh.POOL[0] + r * math.cos(a), oh.POOL[1] + r * math.sin(a)
        if props.clear_of_road(c, x, y, 3.0):
            z = ground(c, ter, x, y, 1.0)
            c.place(palms[k % 4], x, y, z - 0.2, rot=a * 3, scale=0.9 + 0.3 * math.sin(k), coll="Grove", role="visual")
            c.place(trunk, x, y, z - 0.2, coll="Grove", role="collision")
    for f, off in ((0.38, 1.8), (0.66, -1.8)):
        i = int(f * (len(oh.SHORTCUT) - 1))
        x0, y0 = oh.SHORTCUT[i]
        x1, y1 = oh.SHORTCUT[i + 1]
        t = f * (len(oh.SHORTCUT) - 1) - i
        x, y = lerp(x0, x1, t), lerp(y0, y1, t) + off
        z = ground(c, ter, x, y, 2.0)
        c.place(palms[(i + 1) % 4], x, y, z - 0.2, rot=f * 9, scale=1.1, coll="Grove", role="visual")
        c.place(trunk, x, y, z - 0.2, coll="Grove", role="collision")
    # More palms back from the grove, either side of the shortcut.
    for k in range(14):
        t = (k + 0.5) / 14
        i = min(len(oh.SHORTCUT) - 2, int(t * (len(oh.SHORTCUT) - 1)))
        u = t * (len(oh.SHORTCUT) - 1) - i
        x = lerp(oh.SHORTCUT[i][0], oh.SHORTCUT[i + 1][0], u)
        y = lerp(oh.SHORTCUT[i][1], oh.SHORTCUT[i + 1][1], u) + (9.0 + 4 * rnd(k)) * (1 if k % 2 else -1) * (1 if k % 4 < 2 else 1.6)
        if props.clear_of_road(c, x, y, 5.0) and math.hypot(x - oh.POOL[0], y - oh.POOL[1]) > oh.POOL[2] + 3:
            z = ground(c, ter, x, y)
            if z is not None:
                c.place(palms[k % 4], x, y, z - 0.2, rot=k * 2.3, scale=0.85 + 0.3 * rnd(k + 3), coll="Grove", role="visual")
    reeds = props.reeds(c)
    for k in range(16):
        a = k * math.tau / 16 + 0.2
        r = oh.POOL[2] + 2.0 + 1.5 * rnd(k)
        x, y = oh.POOL[0] + r * math.cos(a), oh.POOL[1] + r * math.sin(a)
        c.place(reeds, x, y, ground(c, ter, x, y, 0.0) - 0.2, rot=k, coll="Grove", role="visual")


# ------------------------------------------------------------------ rock


def butte_and_arch(c, oh, ter, span=True):
    """The butte inside the hairpin, banded like the canyons, and the wind-carved arch
    over the road beyond it (its legs where the greybox's stood). (No span: only the
    butte, the ruin's arch has fallen.)"""
    bt = c.rock_mass("Butte", oh.BUTTE[0], oh.BUTTE[1], 15.0, 14.0, 34.0, z0=-4, n=18, seed=5,
                     bands=[(1.15, 0.0), (1.0, 0.1), (0.92, 0.45), (0.88, 0.5), (0.86, 0.9), (0.8, 1.0)])
    c.paint_rock(bt, ("gold_cliff", "wall"), ("pale_sand", "dirt"))
    if not span:
        return
    q = c.at(oh.SEG[19] + 20)
    rot = road_rot(q)
    legs = []
    for side in (-1, 1):
        p = q.side(side * (q.w / 2 + 6.0))
        legs.append(p)
        lg = c.rock_mass("Arch Leg %d" % (side > 0), p.x, p.y, 5.0, 4.5, q.p.z + 13.0, z0=q.p.z - 4.0, n=12, seed=11 + side, angle=rot)
        c.paint_rock(lg, ("gold_cliff", "wall"), ("pale_sand", "dirt"))
    # The span: a thick rib of rock arching from leg to leg, sagging a little.
    (a, b) = legs
    bm = bmesh.new()
    rings = []
    n = 14
    for k in range(n + 1):
        t = k / n
        x, y = lerp(a.x, b.x, t), lerp(a.y, b.y, t)
        z = q.p.z + 12.0 + 3.2 * math.sin(math.pi * t) - 0.8 * math.sin(math.pi * t) ** 6
        thick = 3.6 - 1.2 * math.sin(math.pi * t)
        rings.append((x, y, z, thick))
    ax = Vector((b.x - a.x, b.y - a.y, 0)).normalized()
    side = Vector((-ax.y, ax.x, 0))
    vs = []
    for k, (x, y, z, th) in enumerate(rings):
        wob = 0.4 * math.sin(k * 1.7)
        vs.append([bm.verts.new(Vector((x, y, z)) + side * (o + wob) + Vector((0, 0, dz))) for o, dz in ((-3.4, -th * 0.5), (3.4, -th * 0.5), (3.0, th * 0.5), (-3.0, th * 0.5))])
    for lo, hi in zip(vs, vs[1:]):
        for i in range(4):
            bm.faces.new((lo[i], lo[(i + 1) % 4], hi[(i + 1) % 4], hi[i]))
    bm.faces.new(list(reversed(vs[0])))
    bm.faces.new(vs[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    span = c.mesh_object("Rock Arch", bm, "Rocks", "both")
    c.paint_rock(span, ("gold_cliff", "wall"), ("pale_sand", "dirt"))


def watchtower(c, oh):
    """The ruined watchtower the spiral climbs round: a tapering round tower of mud
    brick, its top broken (merlons fallen here and there, a bite out of one side), dark
    arched windows, and a faded banner."""
    tx, ty = oh.TOWER
    m = Mesh()

    def body(bm):
        loft(bm, [ring(bm, (tx, ty), 17.0, -2.0, 24), ring(bm, (tx, ty), 16.2, 10.0, 24), ring(bm, (tx, ty), 15.5, 24.0, 24)], cap_top=True)

    m.add(("adobe", "wall"), body)
    m.add(("adobe_dark", "wall"), lambda bm: loft(bm, [ring(bm, (tx, ty), 17.4, -2.0, 24), ring(bm, (tx, ty), 17.4, 1.5, 24)], cap_top=True))
    for k in range(18):
        a = k * math.tau / 18
        if k in (5, 6, 7):
            continue  # the broken side
        hgt = 3.0 - (1.4 if k in (4, 8, 13) else 0.0)
        m.add(("adobe", "wall"), lambda bm, a=a, hgt=hgt: cuboid(bm, (tx + 14.9 * math.cos(a), ty + 14.9 * math.sin(a), 24.0 + hgt / 2), (2.6, 1.6, hgt), a + math.pi / 2))
    for k in range(8):
        a = k * math.tau / 8 + 0.2
        for z in (8.0, 17.0):
            r = 16.6 if z < 10 else 15.9
            x, y = tx + r * math.cos(a), ty + r * math.sin(a)
            n = Vector((math.cos(a), math.sin(a), 0))
            t = Vector((-math.sin(a), math.cos(a), 0))

            def win(bm, x=x, y=y, z=z, n=n, t=t):
                c0 = Vector((x, y, z)) + n * 0.05
                v = [bm.verts.new(c0 + t * dx + Vector((0, 0, dz))) for dx, dz in ((-0.7, -1.4), (0.7, -1.4), (0.7, 0.6), (0.0, 1.4), (-0.7, 0.6))]
                bm.faces.new(v)

            m.add(("oasis_bark", "wall"), win)
    m.add(("oasis_banner", "wall"), lambda bm: cuboid(bm, (tx + 15.9, ty, 19.0), (0.12, 2.0, 5.0)))
    m.build(c, "Watchtower", "Rocks", "both")


# ------------------------------------------------------------------ the dunes


def dunes(c, oh, ter):
    """Scrub, stones and the odd palm out on the dunes, and far buttes on the horizon."""
    import props  # noqa: E402

    sc_ = [scrub(c, v) for v in range(3)]
    st = [stones(c, v) for v in range(3)]

    def ok(x, y, z):
        return props.clear_of_road(c, x, y, 8.0) and math.hypot(x - oh.POOL[0], y - oh.POOL[1]) > oh.POOL[2] + 14

    for v in range(3):
        props.scatter(c, sc_[v], 70, (-200, 560, -380, 360), ok, ter, seed=40 + v, scale=(0.8, 1.6), coll="Dunes", role="visual")
        props.scatter(c, st[v], 40, (-200, 560, -380, 360), ok, ter, seed=50 + v, scale=(0.7, 2.2), coll="Dunes", role="visual")
    for k, (x, y, rx, ry, h) in enumerate(((-230.0, 330.0, 40.0, 30.0, 70.0), (560.0, 280.0, 50.0, 34.0, 80.0), (600.0, -260.0, 36.0, 28.0, 64.0),
                                           (-210.0, -360.0, 46.0, 30.0, 58.0), (250.0, 420.0, 30.0, 24.0, 76.0), (90.0, -430.0, 40.0, 26.0, 50.0))):
        r = c.rock_mass("Far Butte %d" % k, x, y, rx, ry, h + 40.0, z0=0.0, n=16, seed=20 + k,
                        bands=[(1.0, 0.0), (0.9, 0.12), (0.72, 0.25), (0.7, 0.85), (0.64, 1.0)])
        c.paint_rock(r, ("gold_cliff", "wall"), ("pale_sand", "dirt"))


# ------------------------------------------------------------------ build


def build(c, oh, ruin=None):
    """The oasis. (`ruin`: {"tent": the burnt tent}; then the arch and the watchtower are
    left to the ruin, and its lights and merging too: returns what finish needs.)"""
    ter = list(c.coll("Terrain").objects)
    sc = {"lights": [], "lanterns": [], "torches": [], "fires": []}
    village(c, oh, ter, sc)
    camp(c, oh, ter, sc, make=ruin and ruin["tent"])
    pool(c, oh, ter, sc)
    butte_and_arch(c, oh, ter, span=not ruin)
    if ruin:
        dunes(c, oh, ter)
        return sc
    watchtower(c, oh)
    dunes(c, oh, ter)
    finish(c, sc)


def finish(c, sc, keep=lambda x, y: True):
    """The lanterns' and the campfire's game lights, and the props merged."""
    for x, y, z in sc["lanterns"]:
        if not keep(x, y):
            continue
        g = c.game(x, y, z)
        c.entity("torch", x=g[0], y=g[1], z=g[2])
    for x, y, z in sc["fires"]:
        if not keep(x, y):
            continue
        g = c.game(x, y, z)
        c.entity("campfire", x=g[0], y=g[1], z=g[2])
    groups = ("Village", "Camp", "Grove", "Dunes")
    c.merge_props(groups)
