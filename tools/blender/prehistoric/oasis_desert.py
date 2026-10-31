# Oasis Haven's scenery (see oasis_haven.py), v3: Havasu in a red-rock side canyon. Adobe
# homes along the village street (vigas, parapets, ladders, ristras, turquoise doors and
# window frames, portals, beehive ovens) under a log ranch gate; ramadas; the campground's
# canvas wall tents and shades; cottonwoods and reeds along the turquoise water, the
# travertine rims, the falls off the south wall; the butte and its arch in the canyon's
# bands; the old stone watchtower; sage, agave, cactus and boulders on the slickrock.
# SPDX-License-Identifier: MIT
#
# All original designs. Every solid near the road keeps the footprint the greybox had,
# so the lap drives as it did.

import math

import canyon_props as cp
import gulch_props as gp
import summit_props as smp_
from course_kit import Vector, bmesh, lerp, rnd
from props import _faces, blob, cuboid, loft, ring, tube

TURQ = "dome_teal"  # the turquoise of doors and window frames


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


def _log(P, mat, a, b, r, n=6):
    P.add(mat, tube, [a, b], r, n=n)


def house(c, variant=0, w=9.0, d=8.0, h=7.0):
    """An adobe home: a thick-walled block, its parapet stepping up at the corners, a
    smaller storey set back on its roof (most), roof beams (vigas) out through the walls
    under both roofs, canales spouting off the parapet, a plank door in a turquoise frame
    under a timber lintel, deep-set lit windows framed turquoise, ristras of red chiles
    by the door, and by variant a portal (a porch on posts and corbels under a roof of
    latillas), a ladder up to the roof, a beehive oven, a round kiva-fireplace chimney.
    Faces -Y (its door), origin at its foot. Visual only: collider is its solid."""
    name = "Adobe Home %d %d %d" % (variant, int(w), int(h))

    def build(bm):
        P = Parts(bm)
        h1 = h * 0.62 if variant % 4 != 2 else h * 0.8
        P.add("adobe", cuboid, (0, 0, h1 / 2 - 0.3), (w, d, h1 + 0.6))
        P.add("adobe_dark", cuboid, (0, 0, 0.25), (w + 0.25, d + 0.25, 0.5))
        # The parapet: low walls round the roof, up a step at the corners.
        t = 0.35
        for (cx, cy, sx, sy) in ((0, -d / 2 + t / 2, w, t), (0, d / 2 - t / 2, w, t), (-w / 2 + t / 2, 0, t, d), (w / 2 - t / 2, 0, t, d)):
            P.add("adobe", cuboid, (cx, cy, h1 + 0.25), (sx, sy, 0.5))
        for sx in (-1, 1):
            for sy in (-1, 1):
                P.add("adobe", cuboid, (sx * (w / 2 - 0.6), sy * (d / 2 - 0.6), h1 + 0.55), (1.2, 1.2, 1.1))
        # Vigas out the front and back under the roof.
        nb = max(3, int(w / 1.3))
        for j in range(nb):
            x = -w / 2 + 0.7 + j * (w - 1.4) / (nb - 1)
            for sy in (-1, 1):
                _log(P, "weathered_timber", (x, sy * (d / 2 - 0.1), h1 - 0.45), (x, sy * (d / 2 + 0.6), h1 - 0.5), 0.15, n=5)
        # Canales: timber spouts off the parapet.
        for x in (-w / 2 + 1.6, w / 2 - 1.6):
            P.add("weathered_timber", cuboid, (x, d / 2 + 0.5, h1 + 0.1), (0.3, 1.0, 0.2))
        # The upper storey, set back.
        if variant % 4 != 2:
            uw, ud, uh = w * 0.55, d * 0.55, h - h1
            ux, uy = w * 0.18 * (1 if variant % 2 else -1), d * 0.18
            P.add("adobe", cuboid, (ux, uy, h1 + uh / 2), (uw, ud, uh))
            for (cx, cy, sx, sy) in ((ux, uy - ud / 2 + 0.15, uw, 0.3), (ux, uy + ud / 2 - 0.15, uw, 0.3),
                                     (ux - uw / 2 + 0.15, uy, 0.3, ud), (ux + uw / 2 - 0.15, uy, 0.3, ud)):
                P.add("adobe", cuboid, (cx, cy, h + 0.2), (sx, sy, 0.4))
            for j in range(3):
                x = ux - uw / 2 + 0.6 + j * (uw - 1.2) / 2
                _log(P, "weathered_timber", (x, uy - ud / 2 + 0.1, h - 0.4), (x, uy - ud / 2 - 0.5, h - 0.45), 0.13, n=5)
            P.add("window_warm", cuboid, (ux, uy - ud / 2 - 0.02, h1 + uh * 0.5), (0.9, 0.06, 0.9))
            P.add(TURQ, cuboid, (ux, uy - ud / 2 - 0.05, h1 + uh * 0.5), (1.2, 0.04, 1.2))
        # The door: plank leaf, turquoise frame, timber lintel; windows either side.
        fy = -d / 2
        P.add(TURQ, cuboid, (0, fy - 0.04, 1.2), (1.7, 0.08, 2.5))
        P.add("door_wood", cuboid, (0, fy - 0.09, 1.1), (1.2, 0.06, 2.2))
        P.add("weathered_timber", cuboid, (0, fy - 0.15, 2.55), (2.4, 0.3, 0.3))
        for x in (-w / 2 + 1.7, w / 2 - 1.7):
            P.add(TURQ, cuboid, (x, fy - 0.04, h1 * 0.5), (1.4, 0.08, 1.3))
            P.add("window_warm", cuboid, (x, fy - 0.09, h1 * 0.5), (1.0, 0.06, 0.95))
            P.add("weathered_timber", cuboid, (x, fy - 0.14, h1 * 0.5 + 0.75), (1.7, 0.26, 0.22))
            P.add("window_warm", cuboid, (x, d / 2 + 0.03, h1 * 0.5), (0.9, 0.06, 0.9))
        # Ristras by the door.
        for sx in ((-1.3,) if variant % 2 else (-1.3, 1.3)):
            for k in range(7):
                P.add("party_red", blob, (sx, fy - 0.35, 2.2 - k * 0.22), 0.16 - 0.008 * k, sz=1.4, subdiv=0)
        if variant % 4 in (0, 3):
            # The portal: posts with corbels, a beam, a roof of latillas.
            py = fy - 2.2
            for x in (-w / 2 + 0.6, -1.6, 1.6, w / 2 - 0.6):
                _log(P, "weathered_timber", (x, py, 0.0), (x, py, 2.9), 0.16, n=6)
                P.add("weathered_timber", cuboid, (x, py, 2.95), (0.9, 0.3, 0.22))
            P.add("weathered_timber", cuboid, (0, py, 3.15), (w + 0.2, 0.32, 0.3))
            for k in range(int(w / 0.5)):
                x = -w / 2 + 0.25 + k * 0.5
                _log(P, "dead_wood", (x, py - 0.3, 3.35), (x, fy, 3.55), 0.07, n=4)
        if variant % 4 in (1, 2):
            # A ladder up to the roof, its rails long past the parapet.
            lx = w / 2 - 1.2 if variant % 2 else -w / 2 + 1.2
            for sx in (-0.35, 0.35):
                _log(P, "weathered_timber", (lx + sx, fy - 1.4, 0.0), (lx + sx * 0.8, fy - 0.2, h1 + 1.6), 0.07, n=4)
            for k in range(int(h1 / 0.6)):
                u = (k + 0.7) / (h1 / 0.6 + 1.5)
                P.add("weathered_timber", cuboid, (lx, fy - 1.4 + 1.2 * u, (h1 + 1.6) * u), (0.75, 0.08, 0.08))
        if variant % 4 == 2:
            # A beehive oven (horno) beside the door.
            P.add("adobe", blob, (w / 2 + 1.4, fy + 1.0, 0.6), 1.1, sz=0.9, subdiv=1)
            P.add("dark_corridor", cuboid, (w / 2 + 1.4, fy - 0.05, 0.5), (0.6, 0.1, 0.5))
        if variant % 4 == 3:
            # A round chimney off the roof's corner.
            cx, cy = (w / 2 - 1.0, d / 2 - 1.0)
            P.add("adobe", lambda bm: oasis_props_cyl(bm, cx, cy, h1, h1 + 2.0, 0.55, n=10))
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


def wall_tent(c, variant=0):
    """A campground site: a canvas wall tent (straight walls, a ridge roof, its door flaps
    tied back on a dark inside, its fly out front on two poles) and beside it a ramada
    (a shade of latillas on four posts) over a plank table and benches, a cooler, a
    folding chair. Faces -Y (its open front), origin at the middle of its foot; it fills
    the greybox tent's footprint (TENT_SOLID: 14 x 12.3, centred 0.85 back)."""
    name = "Camp Site %d" % variant
    cloth = "sail_cloth"

    def build(bm):
        P = Parts(bm)
        tx = -3.2 if variant % 2 == 0 else 3.2
        rx = -tx
        tw, td, wh, rh = 6.0, 8.0, 1.8, 3.6
        y0, y1 = -td / 2, td / 2
        # Walls and roof.
        for sx in (-1, 1):
            P.poly(cloth, [(tx + sx * tw / 2, y0, 0), (tx + sx * tw / 2, y1, 0), (tx + sx * tw / 2, y1, wh), (tx + sx * tw / 2, y0, wh)][:: sx], both=True)
            P.poly(cloth, [(tx + sx * (tw / 2 + 0.25), y0 - 0.2, wh - 0.15), (tx + sx * (tw / 2 + 0.25), y1 + 0.2, wh - 0.15),
                           (tx, y1 + 0.2, rh), (tx, y0 - 0.2, rh)][:: sx], both=True)
        P.poly(cloth, [(tx - tw / 2, y1, 0), (tx + tw / 2, y1, 0), (tx + tw / 2, y1, wh), (tx, y1, rh), (tx - tw / 2, y1, wh)], both=True)
        # The front: gable, the doorway dark, the flaps tied back.
        P.poly(cloth, [(tx - tw / 2, y0, wh), (tx + tw / 2, y0, wh), (tx, y0, rh)], both=True)
        P.poly("dark_corridor", [(tx - 1.6, y0 + 0.05, 0), (tx + 1.6, y0 + 0.05, 0), (tx + 1.6, y0 + 0.05, wh), (tx, y0 + 0.05, rh - 0.2), (tx - 1.6, y0 + 0.05, wh)])
        for sx in (-1, 1):
            P.poly(cloth, [(tx + sx * 1.6, y0, 0), (tx + sx * tw / 2, y0, 0), (tx + sx * tw / 2, y0, wh), (tx + sx * 1.6, y0, wh)][:: sx], both=True)
            P.add(cloth, blob, (tx + sx * 1.9, y0 - 0.15, 1.1), 0.35, sx=0.7, sz=2.6, subdiv=0)
        # The fly out front, on two poles, with guy lines.
        fy = y0 - 2.6
        P.poly(cloth, [(tx - tw / 2 - 0.3, y0, wh + 0.4), (tx + tw / 2 + 0.3, y0, wh + 0.4), (tx + tw / 2 + 0.3, fy, wh), (tx - tw / 2 - 0.3, fy, wh)], both=True)
        for sx in (-1, 1):
            _log(P, "weathered_timber", (tx + sx * (tw / 2 + 0.1), fy, 0), (tx + sx * (tw / 2 + 0.1), fy, wh + 0.1), 0.06, n=4)
            P.add("rope_rail", tube, [(tx + sx * (tw / 2 + 0.1), fy, wh), (tx + sx * (tw / 2 + 1.2), fy - 1.4, 0.0)], 0.025, n=3)
        _log(P, "weathered_timber", (tx, y0 - 0.2, 0), (tx, y0 - 0.2, rh + 0.4), 0.07, n=4)
        # The ramada: four posts, beams, latillas; under it the table, benches, a cooler.
        rw, rd, rz = 5.0, 6.0, 2.8
        for sx in (-1, 1):
            for sy in (-1, 1):
                _log(P, "weathered_timber", (rx + sx * rw / 2, sy * rd / 2, 0), (rx + sx * rw / 2, sy * rd / 2, rz), 0.13, n=6)
            P.add("weathered_timber", cuboid, (rx + sx * rw / 2, 0, rz + 0.1), (0.26, rd + 0.6, 0.26))
        for k in range(int(rd / 0.45)):
            y = -rd / 2 + 0.2 + k * 0.45
            _log(P, "dead_wood", (rx - rw / 2 - 0.3, y, rz + 0.3), (rx + rw / 2 + 0.3, y, rz + 0.3), 0.06, n=4)
        P.add("plank_deck", cuboid, (rx, 0, 0.8), (1.0, 3.2, 0.1))
        for sx in (-1, 1):
            P.add("plank_deck", cuboid, (rx + sx * 1.0, 0, 0.45), (0.35, 3.2, 0.08))
            for sy in (-1.2, 1.2):
                P.add("weathered_timber", cuboid, (rx + sx * 0.35, sy, 0.4), (0.1, 0.1, 0.8))
        P.add(("awning_red", "awning_teal")[variant % 2], cuboid, (rx + 1.8, -2.2, 0.3), (0.9, 0.6, 0.6))
        P.add("white_plaster", cuboid, (rx + 1.8, -2.2, 0.62), (0.95, 0.65, 0.06))
        return P.out(c)

    return c.proto(name, build) and name


def tent(c, variant=0, w=14.0, d=9.0):
    return wall_tent(c, variant)


def ramada(c, variant=0):
    """A market shade at the roadside: four peeled posts, a roof of latillas over beams,
    and under it a plank counter laid with pots and woven blankets."""
    name = "Ramada %d" % variant

    def build(bm):
        P = Parts(bm)
        w, d, h = 5.0, 3.6, 2.8
        for sx in (-1, 1):
            for sy in (-1, 1):
                _log(P, "weathered_timber", (sx * w / 2, sy * d / 2, 0), (sx * w / 2, sy * d / 2, h), 0.13, n=6)
            P.add("weathered_timber", cuboid, (sx * w / 2, 0, h + 0.1), (0.24, d + 0.5, 0.24))
        for k in range(int(w / 0.42) + 2):
            x = -w / 2 - 0.3 + k * 0.42
            _log(P, "dead_wood", (x, -d / 2 - 0.3, h + 0.3), (x, d / 2 + 0.3, h + 0.3), 0.06, n=4)
        P.add("plank_deck", cuboid, (0, -d / 2 + 0.6, 0.95), (w - 0.6, 0.9, 0.1))
        for x in (-1.6, 1.6):
            P.add("weathered_timber", cuboid, (x, -d / 2 + 0.6, 0.45), (0.12, 0.7, 0.9))
        for k in range(5):
            x = -1.8 + k * 0.9
            r = 0.26 + 0.08 * ((k + variant) % 3)
            P.add("terracotta", blob, (x, -d / 2 + 0.6, 1.0 + r), r, sz=1.1 - 0.2 * (k % 2), subdiv=1)
        P.poly("rug", [(-w / 2 + 0.2, -d / 2 + 0.15, 0.95), (-w / 2 + 1.6, -d / 2 + 0.15, 0.95), (-w / 2 + 1.6, -d / 2 + 0.1, 0.1), (-w / 2 + 0.2, -d / 2 + 0.1, 0.1)][::-1], both=True)
        P.poly("rug", [(-1.4, d / 2 - 0.1, h - 0.1), (0.2, d / 2 - 0.1, h - 0.1), (0.2, d / 2 - 0.1, 0.6), (-1.4, d / 2 - 0.1, 0.6)], both=True)
        return P.out(c)

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
    """The adobe homes (where the greybox's blocks stood), lantern posts, ramadas and
    cottonwoods along the street, and the log ranch gate over the start."""
    s = 6.0
    k = 0
    while s < oh.SEG[3]:
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 9.0 + 3 * (k % 2)))
            h = 6.0 + 1.6 * ((k + (side > 0)) % 3)
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
        c.place(house(c, 1 + 2 * (side > 0), 10.0, 9.0, 7.5), p.x, p.y, q.p.z - 0.5, rot=rot, coll="Village", role="visual")
        c.place(collider(c, 10.0, 9.0, 7.5), p.x, p.y, q.p.z - 0.5, rot=rot, coll="Village", role="collision")
    # Lantern posts along the street (their lanterns out over it).
    post = gp.lantern_post(c)
    lx, ly, lz = gp.LANTERN_POST_LIGHT
    s = 4.0
    k = 0
    while s < oh.SEG[3] + 10:
        q = c.at(s)
        side = 1 if k % 2 else -1
        p = q.side(side * (q.w / 2 + 2.6))
        z = ground(c, ter, p.x, p.y, q.p.z) - 0.1
        rot = road_rot(q) + (math.pi / 2 if side > 0 else -math.pi / 2)
        c.place(post, p.x, p.y, z, rot=rot, coll="Village", role="visual")
        sc["lanterns"].append((p.x + lx * math.cos(rot), p.y + lx * math.sin(rot), z + lz))
        s += 24.0
        k += 1
    for k, s in enumerate((oh.SEG[1] + 8, oh.SEG[2] + 22)):
        q = c.at(s)
        p = q.side((1 if k else -1) * (q.w / 2 + 5.0))
        c.place(ramada(c, k), p.x, p.y, ground(c, ter, p.x, p.y, q.p.z) - 0.1, rot=road_rot(q) + (math.pi if k else 0.0), coll="Village", role="visual")
    trees = [smp_.broadleaf(c, v, frosted=False) for v in range(2)]
    for k in range(10):
        s = 12.0 + k * 17.0
        q = c.at(s)
        p = q.side((1 if k % 2 else -1) * (q.w / 2 + 22.0 + 4 * (k % 3)))
        z = ground(c, ter, p.x, p.y)
        if z is not None:
            c.place(trees[k % 2], p.x, p.y, z - 0.2, rot=k * 1.7, scale=0.9 + 0.1 * (k % 3), coll="Village", role="visual")
    # The ranch gate over the street at the start: two great log posts, a log lintel and a
    # second under it, the checkered board hung between, a cattle skull up top.
    q = c.at(8.0)
    m = Mesh()
    rot = road_rot(q)
    span = q.w + 6.0
    ends = []
    for side in (-1, 1):
        p = q.side(side * (span / 2))
        ends.append(p)
        m.add(("weathered_timber", "wall"), lambda bm, p=p: tube(bm, [(p.x, p.y, q.p.z - 1.0), (p.x, p.y, q.p.z + 11.5)], 0.55, n=8))
        m.add(("strata_red", "wall"), lambda bm, p=p: blob(bm, (p.x, p.y, q.p.z + 0.2), 1.6, sz=0.6, subdiv=0))
    a, b = ends
    for z, r, over in ((10.6, 0.5, 1.6), (8.4, 0.32, 0.6)):
        dx, dy = (b.x - a.x) / span, (b.y - a.y) / span
        m.add(("weathered_timber", "wall"), lambda bm, z=z, r=r, over=over: tube(
            bm, [(a.x - dx * over, a.y - dy * over, q.p.z + z), (b.x + dx * over, b.y + dy * over, q.p.z + z)], r, n=7))
    for o in (-q.w / 2 + 1.0, q.w / 2 - 1.0):
        p = q.side(o)
        m.add(("rope_rail", "wall"), lambda bm, p=p: tube(bm, [(p.x, p.y, q.p.z + 8.3), (p.x, p.y, q.p.z + 7.7)], 0.04, n=3))
    m.add(("start_checker", "wall"), lambda bm: cuboid(bm, (q.p.x, q.p.y, q.p.z + 6.9), (q.w - 1.0, 0.2, 1.6), rot + math.pi / 2))
    m.build(c, "Ranch Gate", "Village", "visual")
    c.place(gp.cattle_skull(c), q.p.x, q.p.y, q.p.z + 11.4, rot=rot - math.pi / 2, scale=2.2, coll="Village", role="visual")


# ------------------------------------------------------------------ the camp


def camp(c, oh, ter, sc, make=None):
    """The campground along the weave: a site (wall tent and ramada) where each of the
    greybox's tents stood, a lantern by each, blankets airing on lines and a campfire in
    the middle. (`make(c, k)`: another in each one's place: the ruin's burnt tents.)"""
    s = oh.SEG[10] + 8
    k = 0
    fire = None
    line = rug_line(c)
    while s < oh.SEG[16]:
        q = c.at(s)
        side = 1 if k % 2 else -1
        p = q.side(side * (q.w / 2 + 11.0))
        rot = road_rot(q) + (math.pi if side > 0 else 0.0)
        c.place((make or tent)(c, k % 2), p.x, p.y, q.p.z - 0.05, rot=rot, coll="Camp", role="visual")
        c.place(collider(c, 14.0, 12.3, 3.0, -0.85, "sail_cloth"), p.x, p.y, q.p.z - 0.05, rot=rot, coll="Camp", role="collision")
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


# ------------------------------------------------------------------ Havasu's water


def _trunk_solid(c):
    name = "Cottonwood Trunk Solid"

    def build(bm):
        oasis_props_cyl(bm, 0.0, 0.0, 0.0, 6.0, 0.55, n=8)
        return [(c.lib("weathered_timber", "wall"), _faces(bm, 0))]

    c.proto(name, build)
    return name


def pool(c, oh, ter, sc):
    """Cottonwoods round the pool (where the greybox's palms stood) and two in the grove
    to dodge, more back from the grove, reeds in the shallows; the travertine rims along
    the creek's terraces; cottonwoods and reeds round the plunge pool."""
    import props  # noqa: E402

    trees = [smp_.broadleaf(c, v, frosted=False) for v in range(2)]
    trunk = _trunk_solid(c)
    for k in range(22):
        a = k * math.tau / 22
        r = oh.POOL[2] + 9.0 + 4.0 * math.sin(k * 2.1)
        x, y = oh.POOL[0] + r * math.cos(a), oh.POOL[1] + r * math.sin(a)
        if props.clear_of_road(c, x, y, 3.0) and oh.creek_d(x, y) > oh.CREEK_HW + 2:
            z = ground(c, ter, x, y, 1.0)
            c.place(trees[k % 2], x, y, z - 0.2, rot=a * 3, scale=0.8 + 0.25 * math.sin(k), coll="Grove", role="visual")
            c.place(trunk, x, y, z - 0.2, coll="Grove", role="collision")
    for f, off in ((0.38, 1.8), (0.66, -1.8)):
        i = int(f * (len(oh.SHORTCUT) - 1))
        x0, y0 = oh.SHORTCUT[i]
        x1, y1 = oh.SHORTCUT[i + 1]
        t = f * (len(oh.SHORTCUT) - 1) - i
        x, y = lerp(x0, x1, t), lerp(y0, y1, t) + off
        z = ground(c, ter, x, y, 2.0)
        c.place(trees[i % 2], x, y, z - 0.2, rot=f * 9, scale=1.0, coll="Grove", role="visual")
        c.place(trunk, x, y, z - 0.2, coll="Grove", role="collision")
    for k in range(14):
        t = (k + 0.5) / 14
        i = min(len(oh.SHORTCUT) - 2, int(t * (len(oh.SHORTCUT) - 1)))
        u = t * (len(oh.SHORTCUT) - 1) - i
        x = lerp(oh.SHORTCUT[i][0], oh.SHORTCUT[i + 1][0], u)
        y = lerp(oh.SHORTCUT[i][1], oh.SHORTCUT[i + 1][1], u) + (9.0 + 4 * rnd(k)) * (1 if k % 2 else -1) * (1 if k % 4 < 2 else 1.6)
        if props.clear_of_road(c, x, y, 5.0) and math.hypot(x - oh.POOL[0], y - oh.POOL[1]) > oh.POOL[2] + 3:
            z = ground(c, ter, x, y)
            if z is not None:
                c.place(trees[k % 2], x, y, z - 0.2, rot=k * 2.3, scale=0.8 + 0.3 * rnd(k + 3), coll="Grove", role="visual")
    reeds = props.reeds(c)
    for cx, cy, r0, n in ((oh.POOL[0], oh.POOL[1], oh.POOL[2], 16), (oh.FALLS[0], oh.FALLS[1], oh.FALLS[2], 14)):
        for k in range(n):
            a = k * math.tau / n + 0.2
            r = r0 + 2.5 + 1.5 * rnd(k)
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            if props.clear_of_road(c, x, y, 2.0) and oh.creek_d(x, y) > oh.CREEK_HW:
                c.place(reeds, x, y, ground(c, ter, x, y, 0.0) - 0.2, rot=k, coll="Grove", role="visual")
    # Cottonwoods round the plunge pool, clear of the falls' side.
    fx, fy, fr = oh.FALLS
    for k in range(9):
        a = math.pi / 2 + (k - 4) * 0.42
        r = fr + 9.0 + 2.0 * math.sin(k * 1.7)
        x, y = fx + r * math.cos(a) * 1.15, fy + r * math.sin(a) * 0.7 + 4.0
        if props.clear_of_road(c, x, y, 4.0) and oh.creek_d(x, y) > oh.CREEK_HW + 3:
            z = ground(c, ter, x, y)
            if z is not None:
                c.place(trees[k % 2], x, y, z - 0.2, rot=k, scale=0.85 + 0.2 * rnd(k), coll="Grove", role="visual")


def havasu(c, oh):
    """The falls off the south wall into the plunge pool (a second thinner fall beside
    it), the travertine rim holding the plunge pool, and the rims across the creek where
    it steps down, white water spilling over each."""
    import props  # noqa: E402

    fx, fy, fr = oh.FALLS
    zp, zc, zf = oh.WATER_Z
    lip = fy - oh.ALCOVE - 1.5
    top = oh.natural(fx, lip - 5.0) - 0.4
    props.falls(c, "Havasu Falls", fx, lip, top, zf, 9.0, 15.0, facing=1, throw=4.0, bulge=1.2, veils=3,
                mats=("falls_oasis", "falls_curtain_oasis", "falls_foam"))
    lip2 = fy - oh.ALCOVE * 0.85
    x2 = fx + 14.0
    top2 = oh.natural(x2, lip2 - 5.0) - 0.4
    props.falls(c, "Havasu Falls Twin", x2, lip2, top2, zf, 2.5, 5.0, facing=1, throw=2.0, bulge=0.6, veils=2,
                mats=("falls_oasis", "falls_curtain_oasis", "falls_foam"))
    g = c.game(fx, lip + 6.0, zf)
    c.entity("waterfall", x=g[0], y=g[1], z=g[2], top=round(top - zf, 1), width=14.0, heading=round(math.pi, 4))
    # The rims: a travertine lip round the plunge pool's north side (the creek spills over
    # it) and two more across the creek, each a step down.
    m = Mesh()
    for k in range(13):
        a = math.pi / 2 + (k - 6) * 0.2
        x, y = fx + (fr + 2.6) * math.cos(a), fy + (fr + 2.6) * math.sin(a)
        if abs(x - fx) < oh.CREEK_HW + 1:
            continue
        m.add(("sinter_rim", "wall"), lambda bm, x=x, y=y, a=a: blob(bm, (x, y, zf - 0.2), 1.8, sx=1.4, sz=0.45, subdiv=0))
    for t in (0.0, 0.4, 0.78):
        x, y = lerp(oh.CREEK[0][0], oh.CREEK[-1][0], t), lerp(oh.CREEK[0][1], oh.CREEK[-1][1], t)
        if not props.clear_of_road(c, x, y, 2.0):
            continue
        z = lerp(zf, zp, t) + 0.15
        m.add(("sinter_rim", "wall"), lambda bm, x=x, y=y, z=z: cuboid(bm, (x, y, z - 0.9), (oh.CREEK_HW * 2 + 2.0, 1.4, 1.8)))
        m.add(("falls_curtain_oasis", "wall"), lambda bm, x=x, y=y, z=z: bm.faces.new([bm.verts.new(v) for v in (
            (x - oh.CREEK_HW, y + 0.72, z), (x + oh.CREEK_HW, y + 0.72, z), (x + oh.CREEK_HW, y + 1.6, z - 0.55), (x - oh.CREEK_HW, y + 1.6, z - 0.55))]))
    m.build(c, "Travertine Rims", "Grove", "visual")


# ------------------------------------------------------------------ rock


def paint_strata(c, ob, layer):
    """A rock's faces by the canyon's bands (its flat tops slickrock)."""
    groups = {}
    for p in ob.data.polygons:
        z = (ob.matrix_world @ p.center).z
        mat = "slickrock" if p.normal.z > 0.75 else layer(z)
        groups.setdefault(mat, []).append(p.index)
    for mat, faces in groups.items():
        c.assign(ob, c.lib(mat, "dirt" if mat == "slickrock" else "wall"), faces)
    ob.data.shade_flat()


def butte_and_arch(c, oh, ter, span=True):
    """The butte inside the hairpin, in the canyon's bands, and the sandstone arch over the
    road beyond it (its legs where the greybox's stood). (No span: only the butte, the
    ruin's arch has fallen.)"""
    bt = c.rock_mass("Butte", oh.BUTTE[0], oh.BUTTE[1], 15.0, 14.0, 40.0, z0=-4, n=18, seed=5,
                     bands=[(1.15, 0.0), (1.0, 0.1), (0.92, 0.45), (0.88, 0.5), (0.86, 0.9), (0.8, 1.0)])
    paint_strata(c, bt, oh.layer)
    if not span:
        return
    q = c.at(oh.SEG[19] + 20)
    rot = road_rot(q)
    legs = []
    for side in (-1, 1):
        p = q.side(side * (q.w / 2 + 6.0))
        legs.append(p)
        lg = c.rock_mass("Arch Leg %d" % (side > 0), p.x, p.y, 5.0, 4.5, q.p.z + 13.0, z0=q.p.z - 4.0, n=12, seed=11 + side, angle=rot)
        paint_strata(c, lg, oh.layer)
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
    c.paint_rock(span, ("strata_orange", "wall"), ("slickrock", "dirt"))


def watchtower(c, oh):
    """The old stone watchtower the spiral climbs round: a tapering round tower of laid
    sandstone, banded with darker courses, its top an uneven parapet (stepped, a bite out
    of one side), small dark windows in rings up it, a T-shaped doorway at its foot."""
    tx, ty = oh.TOWER
    m = Mesh()
    TOP = 36.0
    m.add(("masonry", "wall"), lambda bm: loft(bm, [ring(bm, (tx, ty), 17.0, -2.0, 28), ring(bm, (tx, ty), 16.2, 10.0, 28),
                                                     ring(bm, (tx, ty), 15.5, 24.0, 28), ring(bm, (tx, ty), 14.2, TOP, 28)], cap_top=True))
    for z0, z1, r in ((-2.0, 1.2, 17.4), (9.6, 10.4, 16.35), (17.8, 18.6, 15.95), (28.0, 28.8, 15.1), (TOP - 1.2, TOP, 14.5)):
        m.add(("strata_rust", "wall"), lambda bm, z0=z0, z1=z1, r=r: loft(bm, [ring(bm, (tx, ty), r, z0, 28), ring(bm, (tx, ty), r, z1, 28)], cap_top=True))
    for k in range(20):
        a = k * math.tau / 20
        if k in (6, 7):
            continue  # the bite out of its top
        hgt = 2.4 + (1.3 if k % 5 == 0 else 0.0) - (1.0 if k in (5, 8, 14) else 0.0)
        m.add(("masonry", "wall"), lambda bm, a=a, hgt=hgt: cuboid(bm, (tx + 13.8 * math.cos(a), ty + 13.8 * math.sin(a), TOP + hgt / 2),
                                                                   (4.4, 1.3, hgt), a + math.pi / 2))
    for k in range(10):
        a = k * math.tau / 10 + 0.15
        for z in (6.5, 14.0, 21.0, 31.0):
            r = 16.6 if z < 10 else (16.0 if z < 18 else (15.6 if z < 24 else 14.8))
            x, y = tx + r * math.cos(a), ty + r * math.sin(a)
            n = Vector((math.cos(a), math.sin(a), 0))
            t = Vector((-math.sin(a), math.cos(a), 0))

            def win(bm, x=x, y=y, z=z, n=n, t=t):
                c0 = Vector((x, y, z)) + n * 0.06
                v = [bm.verts.new(c0 + t * dx + Vector((0, 0, dz))) for dx, dz in ((-0.45, -0.7), (0.45, -0.7), (0.45, 0.7), (-0.45, 0.7))]
                bm.faces.new(v)

            m.add(("dark_corridor", "wall"), win)
    m.build(c, "Watchtower", "Rocks", "both")


# ------------------------------------------------------------------ the floor


def desert(c, oh, ter):
    """Sage, agave, barrel cactus, dry grass, the odd joshua tree, boulders and tumbleweeds
    on the canyon floor and its ledges; a cattle skull or two."""
    import props  # noqa: E402

    def floor(x, y, z):
        return props.clear_of_road(c, x, y, 8.0) and not oh.in_water(x, y) and oh.creek_d(x, y) > oh.CREEK_HW + 6 and z < 14.0

    def anywhere(x, y, z):
        return props.clear_of_road(c, x, y, 8.0) and not oh.in_water(x, y)

    area = (-240, 600, -420, 400)
    for v in range(2):
        props.scatter(c, cp.sagebrush(c, v), 160, area, anywhere, ter, seed=40 + v, scale=(0.8, 1.5), coll="Dunes", role="visual")
        props.scatter(c, cp.barrel_cactus(c, v), 40, area, floor, ter, seed=44 + v, scale=(0.8, 1.3), coll="Dunes", role="visual")
        props.scatter(c, cp.boulder(c, v), 40, area, anywhere, ter, seed=50 + v, scale=(0.9, 2.4), coll="Dunes", role="visual")
        props.scatter(c, cp.joshua_tree(c, v), 8, area, floor, ter, seed=46 + v, scale=(0.8, 1.2), coll="Dunes", role="visual")
    props.scatter(c, cp.agave(c, 0), 70, area, floor, ter, seed=52, scale=(0.8, 1.4), coll="Dunes", role="visual")
    props.scatter(c, cp.dry_grass(c, 0), 140, area, floor, ter, seed=53, coll="Dunes", role="visual")
    props.scatter(c, gp.tumbleweed(c, 0), 16, area, floor, ter, seed=54, coll="Dunes", role="visual")
    props.scatter(c, gp.cattle_skull(c), 5, area, floor, ter, seed=55, coll="Dunes", role="visual")


def dunes(c, oh, ter):
    desert(c, oh, ter)


# ------------------------------------------------------------------ build


def build(c, oh, ruin=None):
    """Havasu. (`ruin`: {"tent": the burnt tent}; then the arch and the watchtower are
    left to the ruin, and its lights and merging too: returns what finish needs.)"""
    ter = list(c.coll("Terrain").objects)
    sc = {"lights": [], "lanterns": [], "torches": [], "fires": []}
    village(c, oh, ter, sc)
    camp(c, oh, ter, sc, make=ruin and ruin["tent"])
    pool(c, oh, ter, sc)
    havasu(c, oh)
    butte_and_arch(c, oh, ter, span=not ruin)
    if ruin:
        desert(c, oh, ter)
        return sc
    watchtower(c, oh)
    desert(c, oh, ter)
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
