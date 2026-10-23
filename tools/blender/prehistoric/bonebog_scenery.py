# Bonebog Pyramid's scenery (see bonebog_pyramid.py): the pyramid with its carved
# faces, stairs, waterfalls and halls; the giant trees and the canopy; the skeletons;
# the boardwalks' timber; the swamp's life and decay; and its lights. Built from the
# swamp kit in swamp_props.py.
# SPDX-License-Identifier: MIT

import math

import course_kit as kit
import props
import swamp_props as sp
from course_kit import Vector, bmesh, lerp, rnd

STONE = ("bog_stone", "wall")
CARVED = ("bog_carved", "wall")
DARK = ("bog_dark_stone", "wall")
MOSS = ("bog_bank", "grass")
BONE = ("bog_bone", "wall")

# Sunlight slants down along this (Blender axes): the theme's sun, reversed.
SUN_RAY = Vector((0.55, 0.55, -0.62)).normalized()


class Mesh:
    """One mesh built from many pieces, each with its own material."""

    def __init__(self):
        self.bm = bmesh.new()
        self.slots = {}

    def add(self, mat, make):
        k0 = len(self.bm.faces)
        make(self.bm)
        self.bm.faces.ensure_lookup_table()
        self.slots.setdefault(mat, []).extend(range(k0, len(self.bm.faces)))

    def box(self, mat, centre, size, rot=0.0, tilt=(0.0, 0.0)):
        self.add(mat, lambda bm: props.cuboid(bm, centre, size, rot, tilt))

    def tube(self, mat, path, radii, n=6):
        self.add(mat, lambda bm: props.tube(bm, path, radii, n=n))

    def build(self, c, name, coll, role="visual", flat=True):
        if not self.bm.faces:
            self.bm.free()
            return None
        ob = c.mesh_object(name, self.bm, coll, role)
        for mat, faces in self.slots.items():
            c.assign(ob, c.lib(*mat), faces)
        if flat:
            ob.data.shade_flat()
        return ob


# ------------------------------------------------------------------ the pyramid


def _S(bb):
    """Where each of the old lap's sections is (bonebog_pyramid.py's SCENE_SEG maps them
    onto v3's lap), by the old lap's segment numbers."""
    return getattr(bb, "SCENE_SEG", bb.SEG)


def _near_spiral(bb, x, y, m=0.0):
    f = getattr(bb, "near_spiral", None)
    return bool(f and f(x, y, m))


def _rect_ring(bm, cx, cy, hx, hy, z, per_side):
    """A rectangle of points (per_side along each side), anticlockwise from the
    south-west corner."""
    pts = []
    corners = [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]
    for k in range(4):
        (ax, ay), (bx, by) = corners[k], corners[(k + 1) % 4]
        for i in range(per_side):
            t = i / per_side
            pts.append(bm.verts.new((cx + ax + (bx - ax) * t, cy + ay + (by - ay) * t, z)))
    return pts


def halls(bb):
    """The spaces cut through the pyramid: (from, to, half-width, height), along the lap."""
    S = getattr(bb, "SCENE_SEG", bb.SEG)
    return [
        (bb.INSIDE[0], bb.INSIDE[1], 12.5, 11.0, 16.0),  # the corridor, open at both faces
        (S[14] - 4, S[15] + 2, 22.0, 24.0, 0.0),  # the turning chamber, round a great column
        (S[15] - 2, S[15] + 24, 28.0, 27.0, 0.0),  # the Great Hall
        (S[15] + 22, S[15] + 40, 24.0, 17.0, 0.0),  # its lower south end
    ]


def pyramid(c, bb):
    """The pyramid and its foundation as one solid of stepped tiers (each tier's walls
    split every few metres, so torchlight and shade can vary across them), with the
    corridor, the turning chamber and the Great Hall cut through it."""
    cx, cy = bb.PYR
    HX, HY = bb.PYR_HX, bb.PYR_HY
    pad = bb.FOUND_PAD
    n = 24
    bm = bmesh.new()
    rings = []
    # The foundation: from deep in the swamp up to a ledge just above the water, then
    # up to the terrace the pyramid stands on.
    prof = [(pad, -9.0), (pad, 1.2), (pad - 5, 1.2), (pad - 5, bb.FOUND_Z), (0.0, bb.FOUND_Z)]
    z = bb.FOUND_Z
    for inset, top in bb.TIERS:
        if prof[-1] != (-inset, z):
            prof.append((-inset, z))
        k = max(1, round((top - z) / 5.5))
        for j in range(1, k + 1):
            prof.append((-inset, z + (top - z) * j / k))
        z = top
    hx0, hy0, sh = bb.SHRINE
    for o, zz in prof:
        rings.append(_rect_ring(bm, cx, cy, HX + o, HY + o, zz, n))
    rings.append(_rect_ring(bm, cx, cy, hx0 + 6, hy0 + 6, z, n))
    rings.append(_rect_ring(bm, cx, cy, hx0, hy0, z, n))
    rings.append(_rect_ring(bm, cx, cy, hx0, hy0, z + sh, n))
    m = len(rings[0])
    for lo, hi in zip(rings, rings[1:]):
        for i in range(m):
            bm.faces.new((lo[i], lo[(i + 1) % m], hi[(i + 1) % m], hi[i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    pyr = c.mesh_object("Pyramid", bm, "Pyramid")
    for s0, s1, half, height, pad_ in halls(bb):
        c.tunnel(pyr, s0, s1, half=half, height=height, pad=pad_)
    paint_pyramid(c, pyr, bb)
    return pyr


def interior(c, bb, w, slack=1.0):
    """Is the world point w inside the pyramid's halls (or on their walls)?"""
    if not bb.in_pyramid(w.x, w.y, 2.0):
        return False
    smp, d = c.nearest(w.x, w.y)
    if not (bb.INSIDE[0] - 20 <= smp.s <= bb.INSIDE[1] + 20):
        return False
    return d < 30 + slack and w.z < smp.p.z + 29


def paint_pyramid(c, pyr, bb):
    groups = {"stone": [], "moss": [], "found": [], "found_top": [], "inner": [], "floor": []}
    for p in pyr.data.polygons:
        w = p.center
        if interior(c, bb, w) and w.z > bb.FOUND_Z + 0.5:
            groups["floor" if p.normal.z > 0.7 else "inner"].append(p.index)
        elif not bb.in_pyramid(w.x, w.y, 0.5):
            groups["found_top" if p.normal.z > 0.7 else "found"].append(p.index)
        elif p.normal.z > 0.7:
            groups["moss"].append(p.index)
        else:
            groups["stone"].append(p.index)
    c.assign(pyr, c.lib(*STONE), groups["stone"])
    c.assign(pyr, c.lib(*MOSS), groups["moss"])
    c.assign(pyr, c.lib(*STONE), groups["found"])
    c.assign(pyr, c.lib("bog_paving", "road"), groups["found_top"])
    c.assign(pyr, c.lib(*DARK), groups["inner"])
    c.assign(pyr, c.lib("bog_dark_stone", "road"), groups["floor"])
    pyr.data.shade_flat()


def drape(c, name, edges, mat=("vine_leaf", "grass"), lo=2.0, hi=8.0, every=1.4, seed=0, coll="Pyramid Dressing"):
    """Greenery hanging over edges: a fringe of long leafy points down each edge, given
    as [(start, end, outward)] (outward: the direction it hangs out toward)."""
    bm = bmesh.new()
    k = 0
    for a, b, out in edges:
        a, b, out = Vector(a), Vector(b), Vector(out)
        L = (b - a).length
        n = max(1, int(L / every))
        for i in range(n):
            t0, t1 = i / n, (i + 1) / n
            p0, p1 = a.lerp(b, t0) + out * 0.25, a.lerp(b, t1) + out * 0.25
            ln = lo + (hi - lo) * rnd(k * 1.7 + seed) ** 1.5
            tip = (p0 + p1) / 2 + out * (0.4 + 0.5 * rnd(k + seed)) + Vector((0, 0, -ln))
            bm.faces.new((bm.verts.new(p0), bm.verts.new(p1), bm.verts.new(tip)))
            k += 1
    if not bm.faces:
        bm.free()
        return None
    ob = c.mesh_object(name, bm, coll, "visual")
    c.assign(ob, c.lib(*mat))
    return ob


def tier_drapes(c, bb):
    """Vines and moss spilling over every tier's edge."""
    cx, cy = bb.PYR
    edges = []
    for k, (inset, top) in enumerate(bb.TIERS):
        hx, hy = bb.PYR_HX - inset, bb.PYR_HY - inset
        corners = [(cx - hx, cy - hy), (cx + hx, cy - hy), (cx + hx, cy + hy), (cx - hx, cy + hy)]
        outs = [(0, -1, 0), (1, 0, 0), (0, 1, 0), (-1, 0, 0)]
        for i in range(4):
            a, b = corners[i], corners[(i + 1) % 4]
            edges.append(((a[0], a[1], top + 0.1), (b[0], b[1], top + 0.1), outs[i]))
    drape(c, "Tier Vines", edges, ("vine_leaf", "grass"), 2.0, 9.0, 1.6, seed=3)
    drape(c, "Tier Moss", edges, ("bog_moss_hang", "grass"), 1.0, 4.0, 2.3, seed=9)
    # The foundation's edges too, trailing into the water.
    hx, hy = bb.PYR_HX + bb.FOUND_PAD - 5, bb.PYR_HY + bb.FOUND_PAD - 5
    corners = [(cx - hx, cy - hy), (cx + hx, cy - hy), (cx + hx, cy + hy), (cx - hx, cy + hy)]
    outs = [(0, -1, 0), (1, 0, 0), (0, 1, 0), (-1, 0, 0)]
    edges = [((corners[i][0], corners[i][1], bb.FOUND_Z + 0.1), (corners[(i + 1) % 4][0], corners[(i + 1) % 4][1], bb.FOUND_Z + 0.1), outs[i]) for i in range(4)]
    drape(c, "Foundation Vines", edges, ("vine_leaf", "grass"), 1.5, 5.0, 2.0, seed=5)


def facade(c, bb, at, facing, name, face_scale=1.0):
    """A great carved front round a doorway: two piers, a lintel carved as a guardian's
    face (heavy brow, glowing eyes, a nose, cheeks and a row of fangs over the door),
    a stepped crown, and spouts each side pouring waterfalls down the pyramid.
    `at`: the doorway's centre on the face (x, y), facing: its outward direction."""
    out = Vector((facing[0], facing[1], 0)).normalized()
    side = Vector((-out.y, out.x, 0))
    rot = math.atan2(side.y, side.x)
    base = Vector((at[0], at[1], 0))
    door_half, door_top = 12.5, c.at(bb.INSIDE[0] if facing[0] > 0 else bb.INSIDE[1]).p.z + 11.0
    m = Mesh()
    depth = 7.0
    W = 22.0 * face_scale
    top = door_top + 30.0 * face_scale
    z0 = bb.FOUND_Z

    def P(u, o, z):
        """u along the face (side), o out from it, z up."""
        q = base + side * u + out * o
        return (q.x, q.y, z)

    # Piers and lintel.
    for s in (-1, 1):
        u = s * (door_half + (W - door_half) / 2)
        m.box(STONE, P(u, depth / 2 - 1, (z0 + top) / 2), (W - door_half, depth, top - z0), rot)
        m.box(CARVED, P(s * (door_half + 1.2), depth - 0.4, (z0 + door_top) / 2), (2.4, 1.2, door_top - z0), rot)
    m.box(STONE, P(0, depth / 2 - 1, (door_top + top) / 2), (2 * door_half + 0.2, depth, top - door_top), rot)
    # The face, on the lintel: brow, eye sockets and eyes, nose, cheeks, fangs.
    f = face_scale
    zf = door_top + 3.0 * f
    m.box(CARVED, P(0, depth + 1.0, zf + 15 * f), (30 * f, 2.6, 3.2 * f), rot)  # the brow
    for s in (-1, 1):
        m.box(DARK, P(s * 7.5 * f, depth + 0.3, zf + 10.5 * f), (8 * f, 1.0, 6 * f), rot)  # sockets
        m.box(("bog_eye", "wall"), P(s * 7.5 * f, depth + 0.9, zf + 10.5 * f), (4.2 * f, 0.6, 3.4 * f), rot)  # eyes
        m.box(CARVED, P(s * 12.5 * f, depth + 0.8, zf + 4.5 * f), (5 * f, 2.2, 8 * f), rot)  # cheeks
        m.box(CARVED, P(s * 15.5 * f, depth + 0.4, zf + 12 * f), (2.4 * f, 1.4, 12 * f), rot)  # ear plugs
    m.box(CARVED, P(0, depth + 1.6, zf + 7 * f), (5.2 * f, 3.4, 8 * f), rot, tilt=(0.0, 0.0))  # the nose
    m.box(DARK, P(0, depth + 0.6, zf + 1.4 * f), (20 * f, 1.2, 2.6 * f), rot)  # the mouth
    # The crown: stepped blocks with a carved band.
    for k, (w, h) in enumerate(((34, 3.0), (28, 3.0), (20, 3.5))):
        zz = top + 1.5 + sum(x[1] for x in ((34, 3.0), (28, 3.0), (20, 3.5))[:k])
        m.box(CARVED if k == 1 else STONE, P(0, depth / 2 - 1.5, zz + h / 2 - 1.5), (w * f + 8, depth - 1, h), rot)
    ob = m.build(c, name, "Pyramid Dressing", role="both")
    # Fangs over the door, hanging from the lintel.
    teeth = Mesh()
    for k in range(9):
        u = (k - 4) * 2.5
        ln = 3.2 - 0.25 * abs(k - 4)
        p0 = P(u, depth - 0.2, door_top + 0.6)
        teeth.add(BONE, lambda bm, p0=p0, ln=ln: sp.cone(bm, p0, (p0[0], p0[1], p0[2] - ln), 0.8, n=5))
    teeth.build(c, name + " Fangs", "Pyramid Dressing")
    # Spouts high either side, pouring down the front onto the foundation.
    falls = []
    for s in (-1, 1):
        u = s * (W + 3.5)
        lip = base + side * u + out * 0.5
        zt = top - 6.0
        ang = math.atan2(out.y, out.x) + math.pi / 2  # turn the -Y facing to `out`
        fx, fy = props.falls(c, "%s Falls %d" % (name, (s + 3) // 2), lip.x, lip.y, zt, bb.FOUND_Z + 0.05, 5.0, 9.0, facing=-1, throw=4.0, bulge=1.0, veils=2, angle=ang, foam_r=6.0)
        falls.append((fx, fy, bb.FOUND_Z, zt, 9.0))
        m2 = Mesh()
        spout = base + side * u
        m2.box(CARVED, (spout.x + out.x * 1.5, spout.y + out.y * 1.5, zt - 0.4), (4.0, 4.0, 2.4), rot)
        m2.build(c, name + " Spout %d" % ((s + 3) // 2), "Pyramid Dressing")
        # On across the terrace and over its edge into the swamp.
        edge = base + side * u + out * (bb.FOUND_PAD - 4.6)
        fx2, fy2 = props.falls(c, "%s Overflow %d" % (name, (s + 3) // 2), edge.x, edge.y, bb.FOUND_Z + 0.1, 0.0, 7.0, 9.0, facing=-1, throw=2.0, bulge=0.6, veils=1, angle=ang, foam_r=7.0)
        falls.append((fx2, fy2, 0.0, bb.FOUND_Z, 9.0))
        c.ribbon("%s Runoff %d" % (name, (s + 3) // 2), [(spout.x + out.x * 5, spout.y + out.y * 5), (edge.x, edge.y)], 6.0, bb.FOUND_Z + 0.08, c.lib("falls_veil"), role="visual")
    return ob, falls


def stairs(c, bb):
    """Grand staircases up the middle of the north and west faces to the shrine, with
    sloping balustrades."""
    cx, cy = bb.PYR
    m = Mesh()
    for face in ("north", "west"):
        if face == "north":
            out, edge = Vector((0, 1, 0)), bb.PYR_HY
        else:
            out, edge = Vector((-1, 0, 0)), bb.PYR_HX
        side = Vector((-out.y, out.x, 0))
        rot = math.atan2(side.y, side.x)
        z = bb.FOUND_Z
        top = bb.TIERS[-1][1]
        run = bb.TIERS[-1][0]  # the stairs climb this far in, to the top tier
        steps = 40
        for k in range(steps):
            z1 = bb.FOUND_Z + (top - bb.FOUND_Z) * (k + 1) / steps
            o = edge + 4.0 - (run + 4.0) * k / steps
            p = Vector((cx, cy, 0)) + out * (o - 0.5 * (run + 4.0) / steps)
            m.box(STONE if k % 4 else CARVED, (p.x, p.y, (bb.FOUND_Z + z1) / 2), (16.0, (run + 4.0) / steps + 0.05, z1 - bb.FOUND_Z), rot)
        # Balustrades: sloping blocks either side.
        for s in (-1, 1):
            a = Vector((cx, cy, 0)) + out * (edge + 4.0) + side * s * 9.0
            b = Vector((cx, cy, 0)) + out * (edge - run) + side * s * 9.0
            for k in range(10):
                t0, t1 = k / 10, (k + 1) / 10
                pa, pb = a.lerp(b, t0), a.lerp(b, t1)
                za = lerp(bb.FOUND_Z, top, t0) + 1.5
                zb = lerp(bb.FOUND_Z, top, t1) + 1.5
                mid = (pa + pb) / 2
                L = math.hypot((pb - pa).length, zb - za)
                ang = math.atan2(zb - za, (pb - pa).length)
                m.add(CARVED, lambda bm, mid=mid, za=za, zb=zb, L=L, ang=ang, s=s: _slab(bm, (mid.x, mid.y, (za + zb) / 2 - 2.0), (2.4, L + 0.4, 5.0), out, ang))
    m.build(c, "Grand Stairs", "Pyramid Dressing", role="visual")


def _slab(bm, centre, size, out, ang):
    """A box (w, length, h) running inward from `out` (along -out), tilted up by ang."""
    res = bmesh.ops.create_cube(bm, size=1.0)
    fwd = -out
    side = Vector((-fwd.y, fwd.x, 0))
    up = Vector((0, 0, 1))
    f2 = fwd * math.cos(ang) + up * math.sin(ang)
    u2 = -fwd * math.sin(ang) + up * math.cos(ang)
    for v in res["verts"]:
        v.co = Vector(centre) + side * v.co.x * size[0] + f2 * v.co.y * size[1] + u2 * v.co.z * size[2]


def terrace(c, bb, lights):
    """The foundation's terrace: braziers along its edges, colossal heads at its
    corners, and a carved shrine on the summit with a beacon fire."""
    cx, cy = bb.PYR
    hx, hy = bb.PYR_HX + bb.FOUND_PAD - 8, bb.PYR_HY + bb.FOUND_PAD - 8
    br = sp.stone_brazier(c)
    k = 0
    for (ax, ay), (bx, by) in (((-hx, -hy), (hx, -hy)), ((hx, -hy), (hx, hy)), ((hx, hy), (-hx, hy)), ((-hx, hy), (-hx, -hy))):
        L = math.hypot(bx - ax, by - ay)
        n = int(L / 34)
        for i in range(n + 1):
            x, y = cx + lerp(ax, bx, i / n), cy + lerp(ay, by, i / n)
            sm, d = c.nearest(x, y)
            if d < sm.w / 2 + 8:
                continue
            c.place(br, x, y, bb.FOUND_Z, rot=k * 0.7, scale=1.4, coll="Pyramid Dressing", role="visual")
            lights.append((x, y, bb.FOUND_Z + 3.6))
            k += 1
    head = props.idol_head(c)
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        x, y = cx + sx * (bb.PYR_HX + 7), cy + sy * (bb.PYR_HY + 7)
        c.place(head, x, y, bb.FOUND_Z, rot=math.atan2(sy, sx) + math.pi / 2, scale=2.6, coll="Pyramid Dressing", role="visual")
    top = bb.TIERS[-1][1] + bb.SHRINE[2]
    c.place(br, cx, cy, top, rot=0.3, scale=3.0, coll="Pyramid Dressing", role="visual")


# ------------------------------------------------------------------ inside the pyramid


def inside_dressing(c, bb, lights, falls):
    """The corridor's carved pilasters and torches, cobwebs in the corners, roots and
    vines through the roof; the great column in the turning chamber with a guardian
    head; the Great Hall's two rows of pillars, its side pools fed by waterfalls from
    the roof, and shafts of light."""
    S = getattr(bb, "SCENE_SEG", bb.SEG)
    m = Mesh()
    torch = props.torch(c)
    web_full, web_corner = sp.cobweb(c, 0), sp.cobweb(c, 1)
    roots = [props.hanging_roots(c, v, 3.0 + v) for v in range(3)]
    vines = [sp.hanging_vine(c, v, 4.0 + 1.5 * v) for v in range(3)]
    # The corridor: pilasters every 9 m, each with a torch; a frieze; webs in the
    # upper corners; roots through the roof.
    half = 12.5
    s0, s1 = bb.INSIDE[0] + 3, S[14] - 4
    k = 0
    s = s0
    while s < s1:
        q = c.at(s)
        rot = math.atan2(q.t.y, q.t.x)
        for sd in (-1, 1):
            p = q.side(sd * (half - 0.6), 0.0)
            m.box(DARK, (p.x, p.y, p.z + 3.0), (2.2, 1.4, 7.0), rot)
            m.box(CARVED, (p.x, p.y, p.z + 6.9), (2.8, 1.8, 1.0), rot)
        sd = 1 if k % 2 else -1
        p = q.side(sd * (half - 1.4), 3.8)
        c.place(torch, p.x, p.y, p.z, rot=math.atan2(q.r.x * -sd, q.r.y * sd) if False else rot + (math.pi / 2 if sd > 0 else -math.pi / 2), scale=1.7, coll="Pyramid Inside", role="visual")
        lights.append(tuple(q.side(sd * (half - 2.8), 6.0)))
        if k % 2 == 0:
            w = q.side(-sd * (half - 0.4), 8.4)
            c.place(web_corner, w.x, w.y, w.z, rot=rot + (0 if sd < 0 else math.pi), scale=(1.2, 1.2, 1.2), coll="Pyramid Inside", role="visual")
        r = q.side((rnd(k * 3.3) - 0.5) * 12, 10.6)
        c.place(roots[k % 3] if k % 2 else vines[k % 3], r.x, r.y, r.z, rot=k * 1.3, scale=0.9 + 0.3 * rnd(k), coll="Pyramid Inside", role="visual")
        s += 9.0
        k += 1
    s = s0
    while s < s1:
        q, q2 = c.at(s), c.at(s + 4.5)
        for sd in (-1, 1):
            a, b = q.side(sd * (half - 0.3), 7.6), q2.side(sd * (half - 0.3), 7.6)
            mid = (a + b) / 2
            m.box(CARVED, (mid.x, mid.y, mid.z), ((b - a).length + 0.05, 0.6, 1.2), math.atan2((b - a).y, (b - a).x))
        s += 4.5
    # The turning chamber: the great column at the arc's centre wears a guardian's
    # head, and torches ring it.
    a0 = c.at(S[14])
    a1 = c.at(S[15])
    # The arc's centre: from the turn's start, one radius to its left.
    centre = a0.p + Vector((-a0.r.x, -a0.r.y, 0)) * 45.0
    head = props.idol_head(c)
    mid = c.at((S[14] + S[15]) / 2)
    face = (mid.p - centre)
    face.z = 0
    face.normalize()
    hp = centre + face * 20.5
    c.place(head, hp.x, hp.y, mid.p.z - 0.5, rot=math.atan2(face.y, face.x) + math.pi / 2, scale=2.0, coll="Pyramid Inside", role="visual")
    for j in range(5):
        t = (j + 0.5) / 5
        q = c.at(S[14] + (S[15] - S[14]) * t)
        p = q.side(-21.0, 4.2)  # on the column's face (the left of the road)
        lights.append(tuple(q.side(-19.5, 6.0)))
        c.place(torch, p.x, p.y, p.z, rot=math.atan2(q.t.y, q.t.x) + math.pi / 2, scale=1.8, coll="Pyramid Inside", role="visual")
        o = q.side(21.0, 4.2)
        lights.append(tuple(q.side(19.5, 6.0)))
        c.place(torch, o.x, o.y, o.z, rot=math.atan2(q.t.y, q.t.x) - math.pi / 2, scale=1.8, coll="Pyramid Inside", role="visual")
        w = q.side(21.0, 15.0)
        c.place(web_full, w.x, w.y, w.z, rot=math.atan2(q.t.y, q.t.x), scale=1.6, coll="Pyramid Inside", role="visual")
    # The Great Hall: pillars, pools, falls from the roof, shafts of light, webs.
    pil = sp.pillar(c, 24.0)
    pil_lo = sp.pillar(c, 15.0)
    h0, h1 = S[15], S[15] + 40
    s = h0 + 2
    k = 0
    while s < h1 - 2:
        q = c.at(s)
        rot = math.atan2(q.t.y, q.t.x)
        tall = s < S[15] + 22
        for sd in (-1, 1):
            p = q.side(sd * 17.0, -0.4)
            c.place(pil if tall else pil_lo, p.x, p.y, p.z, rot=rot, coll="Pyramid Inside", role="both")
            t = q.side(sd * 14.8, 5.0)
            c.place(torch, t.x, t.y, t.z, rot=rot + (math.pi / 2 if sd > 0 else -math.pi / 2), scale=1.7, coll="Pyramid Inside", role="visual")
            lights.append(tuple(q.side(sd * 13.6, 7.0)))
        if tall and k % 2 == 0:
            for sd in (-1, 1):
                w = q.side(sd * 17.0, 17.5)
                c.place(web_full, w.x + q.t.x * 5, w.y + q.t.y * 5, w.z, rot=rot + math.pi / 2, scale=2.0, coll="Pyramid Inside", role="visual")
        s += 10.0
        k += 1
    # The pools along both walls, outside the pillars, and the falls feeding them.
    for sd in (-1, 1):
        path = []
        s = h0 - 2
        while s <= h1 + 1:
            q = c.at(s)
            p = q.side(sd * 23.0, -0.25)
            path.append((p.x, p.y, 9.0, p.z))
            s += 4.0
        c.ribbon("Hall Pool %d" % ((sd + 3) // 2), path, 9.0, 0, c.lib("bog_glow_pool", "water"), coll="Water", role="visual")
        for j, f in enumerate((0.3, 0.75)):
            q = c.at(h0 + 22 * f + 2)
            lip = q.side(sd * 26.5, 15.5)
            ang = math.atan2(-sd * q.r.y, -sd * q.r.x) + math.pi / 2
            fx, fy = props.falls(c, "Hall Falls %d%d" % ((sd + 3) // 2, j), lip.x, lip.y, lip.z, q.p.z - 0.2, 4.0, 6.0, facing=-1, throw=2.5, bulge=0.6, veils=1, angle=ang, foam_r=4.0)
            falls.append((fx, fy, q.p.z - 0.2, lip.z, 6.0))
    # Shafts of light from cracks in the roof.
    shafts = Mesh()
    for j in range(5):
        q = c.at(h0 + 2 + j * 5.0)
        top = q.side((j - 2) * 6.0, 26.0)
        foot = q.side((j - 2) * 6.0 + 4.0, 0.0) + q.t * 6.0
        _shaft(shafts, top, foot, 3.0, 4.5)
    shafts.build(c, "Hall Light", "Light", role="visual")
    # The exit: webs and roots by the south door.
    q = c.at(bb.INSIDE[1] - 8)
    for sd in (-1, 1):
        w = q.side(sd * (half - 0.4), 8.4)
        c.place(web_corner, w.x, w.y, w.z, rot=math.atan2(q.t.y, q.t.x) + (0 if sd < 0 else math.pi), scale=1.2, coll="Pyramid Inside", role="visual")
    m.build(c, "Pyramid Halls", "Pyramid Inside", role="visual")


def _shaft(m, top, foot, w0, w1):
    """A shaft of light: two crossed see-through quads from top to foot, widening."""
    top, foot = Vector(top), Vector(foot)
    d = (foot - top).normalized()
    a = d.cross(Vector((0, 0, 1)))
    if a.length < 1e-3:
        a = Vector((1, 0, 0))
    a.normalize()
    b = d.cross(a).normalized()
    for ax in (a, b):
        def make(bm, ax=ax):
            vs = [bm.verts.new(top - ax * w0), bm.verts.new(top + ax * w0), bm.verts.new(foot + ax * w1), bm.verts.new(foot - ax * w1)]
            bm.faces.new(vs)
        m.add(("light_shaft", "wall"), make)


# ------------------------------------------------------------------ skeletons


def rib_cage(c, bb, s0, s1, name, spine_up=24.0, reach=22.0, every=9.0):
    """A colossal rib cage the road runs straight through: pairs of ribs arching from
    the swamp on both sides up to a spine high overhead, biggest in the middle."""
    m = Mesh()
    n = int((s1 - s0) / every)
    spine = []
    for k in range(n + 1):
        t = k / n
        q = c.at(s0 + (s1 - s0) * t)
        size = 0.6 + 0.4 * math.sin(math.pi * min(1.0, t * 1.1))
        apex = q.p.z + spine_up * (0.8 + 0.2 * size)
        spine.append(Vector((q.p.x, q.p.y, apex + 1.4)))
        for sd in (-1, 1):
            pts = []
            for j in range(9):
                u = j / 8
                o = sd * (reach * (0.7 + 0.3 * size)) * (1 - u) ** 0.85
                z = -2.0 + (apex + 2.0) * math.sin(u * math.pi / 2) ** 0.7
                p = q.p + q.r * o - q.t * (2.5 * u)
                pts.append((p.x, p.y, z))
            r0 = 1.25 * (0.75 + 0.4 * size)
            m.tube(BONE, pts, [r0 * (1.15 - 0.5 * j / 8) for j in range(9)], n=7)
    m.tube(BONE, [tuple(p) for p in spine], 1.6, n=8)
    for k, p in enumerate(spine):
        m.add(BONE, lambda bm, p=p: props.blob(bm, (p.x, p.y, p.z + 0.4), 1.9, sx=1.2, subdiv=1))
        m.add(BONE, lambda bm, p=p, k=k: sp.cone(bm, (p.x, p.y, p.z + 1.2), (p.x, p.y, p.z + 4.5 + 1.5 * math.sin(k)), 0.8, n=5))
    return m.build(c, name, "Bones", role="visual")


def neck_arch(c, pts, name, size=1.0, head=True):
    """A long neck (or tail) of vertebrae along a curve of (x, y, z) points, ending in
    a small skull."""
    vert = sp.vertebra(c, 0)
    path = [Vector(p) for p in pts]
    total = sum((b - a).length for a, b in zip(path, path[1:]))
    k = 0
    d = 0.0
    while d < total:
        acc = 0.0
        for a, b in zip(path, path[1:]):
            L = (b - a).length
            if acc + L >= d:
                p = a.lerp(b, (d - acc) / L)
                t = (b - a).normalized()
                break
            acc += L
        sc = size * (1.5 - 0.7 * d / total)
        c.place(vert, p.x, p.y, p.z, rot=math.atan2(t.y, t.x), scale=sc, coll="Bones", role="visual")
        d += 3.4 * sc
        k += 1
    # The spinal column joining them, so it reads as one long neck.
    m = Mesh()
    m.tube(BONE, [tuple(p) for p in path], [size * (1.0 - 0.45 * k / max(1, len(path) - 1)) for k in range(len(path))], n=6)
    m.build(c, name + " Spine", "Bones", role="visual")
    if head:
        c.place(sp.horned_skull(c), path[-1].x, path[-1].y, path[-1].z - 1.0, rot=math.atan2(t.y, t.x), scale=size * 0.8, coll="Bones", role="visual")


def jaw_gate(c, s, name):
    """A colossal lower jaw stood on end over the road as an arch: its two arms rise
    from the dike and meet at the chin high overhead, lined with teeth."""
    q = c.at(s)
    m = Mesh()
    half = q.w / 2 + 6.0
    apex = q.p.z + 24.0
    for sd in (-1, 1):
        pts = []
        for j in range(10):
            u = j / 9
            o = sd * half * math.cos(u * math.pi / 2) ** 0.8
            z = q.p.z - 1.0 + (apex - q.p.z + 1.0) * math.sin(u * math.pi / 2) ** 1.1
            p = q.p + q.r * o
            pts.append((p.x, p.y, z))
        m.tube(BONE, pts, [2.4 - 0.9 * j / 9 for j in range(10)], n=8)
        # The jaw joint and its hook at the foot, and teeth along the inside.
        p = q.p + q.r * (sd * half)
        m.add(BONE, lambda bm, p=p: props.blob(bm, (p.x, p.y, q.p.z + 1.5), 2.6, sx=1.2, sz=1.4, subdiv=1))
        hook = q.p + q.r * (sd * (half - 1.0))
        m.add(BONE, lambda bm, hook=hook: sp.cone(bm, (hook.x, hook.y, q.p.z + 5.0), (hook.x - q.t.x * 3.0, hook.y - q.t.y * 3.0, q.p.z + 11.0), 1.4, n=5))
        for j in range(2, 9):
            a = Vector(pts[j])
            inward = (q.p + Vector((0, 0, a.z)) - a)
            inward.z = 0
            if inward.length < 0.1:
                continue
            inward.normalize()
            tip = a + inward * (2.6 - 0.12 * j) + Vector((0, 0, -0.8))
            m.add(("bone", "wall"), lambda bm, a=a, tip=tip, j=j: sp.cone(bm, a + inward * 1.0, tip, 0.6, n=5))
    m.add(BONE, lambda bm: props.blob(bm, (q.p.x, q.p.y, apex + 0.8), 2.8, sx=1.3, sz=0.9, subdiv=1))
    return m.build(c, name, "Bones", role="visual")


def bones(c, bb, ter):
    """The graveyard: the Rib Bridge's colossal cage and its skull, the Jawbone Gate,
    a long-neck whose neck arches over the Grand Causeway, the great skull of Skull
    Lagoon, and bones scattered everywhere else."""
    S = getattr(bb, "SCENE_SEG", bb.SEG)
    rib_cage(c, bb, S[7] + 4, min(S[7] + 86, S[8] + 6), "Rib Bridge Cage", spine_up=24.0, reach=24.0)
    # Its skull in the water at the north end, its tail trailing off to the south.
    q = c.at(S[8] + 20)
    p = q.side(-36.0)
    if _near_spiral(bb, p.x, p.y, 10):
        p = q.side(36.0)
    c.place(sp.great_skull(c), p.x, p.y, -3.0, rot=math.atan2(-q.r.y, -q.r.x) + 0.5, scale=0.9, coll="Bones", role="visual")
    t0 = c.at(S[7] + 2)
    tail = []
    for k in range(9):
        p = t0.p - t0.t * (7.0 * k) + t0.r * (6.0 * math.sin(k * 0.6))
        tail.append((p.x, p.y, t0.p.z + 18.0 - 2.4 * k))
    neck_arch(c, tail, "Rib Tail", size=1.0, head=False)
    jaw_gate(c, getattr(bb, "JAW_S", 95.0), "Jawbone Gate")
    # A long-neck: its body half sunk in the lagoon, its neck arching high over the
    # causeway and its head resting on the far bank.
    if getattr(bb, "LONGNECK", True):
        long_neck(c, S)
    _skull_lagoon(c, bb, S, ter)


def long_neck(c, S):
    cw = c.at(S[9] + 60)
    body = cw.side(-60.0)
    over = cw.p
    far = cw.side(48.0)
    neck = []
    for k in range(13):
        t = k / 12
        p = body.lerp(far, t)
        z = 2.0 + 30.0 * math.sin(math.pi * min(1.0, t * 1.05)) ** 0.9 - 4.0 * t
        neck.append((p.x, p.y, z))
    neck_arch(c, neck, "Long-Neck", size=1.3)
    rp = sp.rib_pair(c, 0)
    for k in range(7):
        p = body + Vector((-cw.r.x, -cw.r.y, 0)) * (6.0 * k + 4.0)
        c.place(rp, p.x, p.y, -1.5, rot=math.atan2(cw.r.y, cw.r.x), scale=(14.0, 12.0 - k, 13.0 - k * 1.2), coll="Bones", role="visual")


def _skull_lagoon(c, bb, S, ter):
    rp = sp.rib_pair(c, 0)
    # Skull Lagoon: the great skull on the outside of the bend, jaws open toward you.
    s18 = (S[18] + S[19]) / 2
    q = c.at(s18)
    p = q.side(-44.0)
    c.place(sp.great_skull(c), p.x, p.y, -2.6, rot=math.atan2(q.r.y, q.r.x) - 0.4, scale=1.3, coll="Bones", role="visual")
    # Scattered: horned skulls, rib pairs, femurs, bone piles and lone vertebrae.
    hs, fem = sp.horned_skull(c), sp.femur(c)
    piles = [sp.bone_pile(c, v) for v in range(3)]
    for k, (x, y, rot, sc) in enumerate(((70, -95, 1.0, 1.0), (-62, -120, 2.5, 1.2), (175, 140, 4.0, 1.1), (300, 40, 0.5, 1.3), (-215, 70, 3.0, 1.0), (40, 320, 1.8, 1.2), (150, 290, 2.2, 0.9))):
        if props.clear_of_road(c, x, y, 14):
            c.place(hs, x, y, (c.ground_z(x, y, ter) or -1.0) - 0.6, rot=rot, scale=sc * 1.4, coll="Bones", role="visual")

    def wet_or_bank(m0, m1):
        def ok(x, y, z):
            if bb.on_foundation(x, y, 6):
                return False
            smp, d = c.nearest(x, y)
            return smp.w / 2 + m0 < d < smp.w / 2 + m1
        return ok

    area = (-300, 340, -300, 330)
    props.scatter(c, rp, 12, area, wet_or_bank(16, 90), ter, seed=410, scale=(5.0, 9.0), coll="Bones", role="visual", sink=1.2)
    props.scatter(c, fem, 7, area, wet_or_bank(12, 80), ter, seed=420, scale=(0.8, 1.4), coll="Bones", role="visual", sink=0.5)
    for v, pl in enumerate(piles):
        props.scatter(c, pl, 4, area, wet_or_bank(10, 60), ter, seed=430 + v, scale=(1.0, 1.8), coll="Bones", role="visual", sink=0.2)
    props.scatter(c, sp.vertebra(c, 1), 14, area, wet_or_bank(10, 70), ter, seed=440, scale=(0.8, 1.6), coll="Bones", role="visual", sink=0.8)


# ------------------------------------------------------------------ trees and canopy


def covered(bb, c, x, y, gaps):
    """Is the canopy overhead here? (Not over the pyramid, the open lagoon or the far
    swamp, nor in a gap.)"""
    if bb.on_foundation(x, y, 26) or open_lagoon(bb, x - 10, y + 10):
        return False
    if c.nearest(x, y)[1] > 175:
        return False
    return all((x - gx) ** 2 + (y - gy) ** 2 > 18.0 ** 2 for gx, gy in gaps)


def canopy_z(x, y):
    return 50.0 + 6.0 * math.sin(x / 23.0 + 1.3) * math.cos(y / 19.0) + 3.5 * math.sin((x + y) / 9.0) + 2.0 * math.cos(x / 6.0 - y / 7.0)


def canopy_sheet(c, bb, gaps, cell=10.0):
    """The ceiling of leaves: a lumpy sheet of foliage (seen from below) wherever
    covered() says, in two greens. Returns where it is (for shading, vines) and its
    edges (for the clumps that soften them)."""
    x0, x1, y0, y1 = -330, 380, -330, 420
    nx, ny = int((x1 - x0) / cell), int((y1 - y0) / cell)
    on = {}
    for j in range(ny):
        for i in range(nx):
            x, y = x0 + (i + 0.5) * cell, y0 + (j + 0.5) * cell
            on[i, j] = covered(bb, c, x, y, gaps)
    bm = bmesh.new()
    verts = {}

    def V(i, j):
        if (i, j) not in verts:
            x = x0 + i * cell + (rnd(i * 3.1 + j * 7.3) - 0.5) * cell * 0.5
            y = y0 + j * cell + (rnd(i * 5.7 + j * 1.9) - 0.5) * cell * 0.5
            verts[i, j] = bm.verts.new((x, y, canopy_z(x, y) + 6.0 * (rnd(i * 1.1 + j * 2.3) - 0.5)))
        return verts[i, j]

    cells, edges = [], []
    for (i, j), yes in on.items():
        if not yes:
            continue
        bm.faces.new((V(i, j), V(i + 1, j), V(i + 1, j + 1), V(i, j + 1)))
        x, y = x0 + (i + 0.5) * cell, y0 + (j + 0.5) * cell
        cells.append((x, y))
        if any(not on.get((i + di, j + dj), False) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1))) and (i * 7 + j * 3) % 8 == 0:
            edges.append((x, y, canopy_z(x, y)))
    ob = c.mesh_object("Canopy Ceiling", bm, "Canopy Sheet", "visual")
    lightf = []
    darkf = []
    for p in ob.data.polygons:
        (darkf if rnd(p.center.x * 0.7 + p.center.y * 1.3) < 0.35 else lightf).append(p.index)
    c.assign(ob, c.lib("bog_canopy", "grass"), lightf)
    c.assign(ob, c.lib("canopy_dark", "grass"), darkf)
    ob.data.shade_smooth()
    return {"cells": cells, "edges": edges}


def open_lagoon(bb, x, y):
    """The open water inside the loop, kept clear of trees and canopy so the pyramid
    shows across it."""
    return -40 < x < 228 and 45 < y < 205


def trees(c, bb, ter):
    """Giant swamp trees all along the route and round the edge of the swamp, and the
    canopy over them: a ceiling of leaves with gaps for shafts of sunlight. Returns the
    canopy's footprint (for shading) and its gaps (for the light)."""
    giants = [sp.swamp_giant(c, v) for v in range(3)]
    placed = []

    def free(x, y, gap):
        return all((x - px) ** 2 + (y - py) ** 2 > gap * gap for px, py, _ in placed)

    def plant(x, y, sc, margin):
        if bb.on_foundation(x, y, 22) or open_lagoon(bb, x, y) or _near_spiral(bb, x, y, 14):
            return False
        if not props.clear_of_road(c, x, y, margin) or not free(x, y, 30 * sc):
            return False
        z = max(0.0, bb.natural(x, y))
        k = len(placed)
        c.place(giants[k % 3], x, y, z, rot=rnd(k * 3.3) * math.tau, scale=sc, coll="Trees", role="visual")
        placed.append((x, y, sc))
        return True

    # Along the route: alternate sides, 18-38 m out.
    s = 10.0
    k = 0
    while s < c.length:
        q = c.at(s)
        sd = 1 if k % 2 else -1
        for tries in range(3):
            off = q.w / 2 + 18 + 22 * rnd(k * 1.7 + tries)
            p = q.side(sd * off)
            if plant(p.x, p.y, 0.85 + 0.35 * rnd(k * 2.9), 16.0):
                break
        s += 30.0 + 14.0 * rnd(k * 4.1)
        k += 1
    # The jungle's edge, all round.
    for k in range(40):
        a = k * math.tau / 40
        r = 270 + 30 * rnd(k * 5.5)
        plant(20 + r * math.cos(a), 30 + 1.12 * r * math.sin(a), 0.9 + 0.3 * rnd(k), 20.0)
    # The canopy: a ceiling of leaves at 44-56 m over everything near the route but the
    # pyramid and the open lagoon, with gaps for shafts of sunlight; clumps of leaves
    # along its ragged edges.
    gaps = []
    k = 0
    for gx in range(-300, 360, 55):
        for gy in range(-300, 380, 55):
            k += 1
            x = gx + (rnd(k * 1.3) - 0.5) * 30
            y = gy + (rnd(k * 2.1) - 0.5) * 30
            if rnd(k * 7.7) < 0.22 and covered(bb, c, x, y, gaps=()):
                gaps.append((x, y))
    cover = canopy_sheet(c, bb, gaps)
    patches = [sp.canopy_patch(c, v) for v in range(3)]
    for k, (x, y, z) in enumerate(cover["edges"]):
        c.place(patches[k % 3], x, y, z - 3.0, rot=rnd(k * 9.1) * math.tau, scale=0.9 + 0.4 * rnd(k * 5.3), coll="Canopy", role="visual")
    return placed, cover, gaps


def hanging_life(c, bb, cover):
    """Vines and moss hanging from the canopy, long over the water, shorter over the
    road (never low enough to touch a kart)."""
    vines = [sp.hanging_vine(c, v, L) for v, L in enumerate((12.0, 18.0, 26.0))]
    beards = [sp.moss_beard(c, v, 5.0 + 2 * v) for v in range(2)]
    cells = cover["cells"]
    k = 0
    for n, (x, y) in enumerate(cells):
        if n % 19:
            continue
        k += 1
        px = x + (rnd(k * 1.9) - 0.5) * 8
        py = y + (rnd(k * 2.7) - 0.5) * 8
        smp, d = c.nearest(px, py)
        top = canopy_z(px, py) - 0.5
        clear = smp.p.z + 9.0 if d < smp.w / 2 + 4 else 1.5
        room = top - clear
        if room < 13:
            continue
        choice = 2 if room > 30 else 1 if room > 21 else 0
        c.place(vines[choice], px, py, top, rot=rnd(k) * math.tau, scale=1.0, coll="Vines", role="visual")
        if k % 2 == 0:
            c.place(beards[k % 4 // 2], px + 3, py - 2, top - 1, rot=k, scale=1.3, coll="Vines", role="visual")


def canopy_shade(c, obs, cover, gaps, bb):
    """Dappled shade under the canopy: everything under it is a little darker and
    greener, brighter in the sunlit gaps."""
    from mathutils import kdtree
    from kartipelago_tools import paint as _paint

    cells = cover["cells"]
    tc = kdtree.KDTree(max(1, len(cells)))
    for i, (x, y) in enumerate(cells):
        tc.insert(Vector((x, y, 0)), i)
    tc.balance()
    tg = kdtree.KDTree(max(1, len(gaps)))
    for i, (x, y) in enumerate(gaps):
        tg.insert(Vector((x, y, 0)), i)
    tg.balance()
    shade = (0.66, 0.78, 0.6)
    for ob in obs:
        t = _paint.Target(ob, None)
        for li, v, _ in t.corners:
            w = t.world[v]
            if interior(c, bb, w):
                continue
            _, _, dc = tc.find(Vector((w.x, w.y, 0)))
            k = max(0.0, 1.0 - max(0.0, (dc or 99) - 6) / 16)
            if gaps:
                _, _, dg = tg.find(Vector((w.x, w.y, 0)))
                k *= min(1.0, max(0.0, ((dg or 99) - 8) / 14))
            k *= 0.8 + 0.2 * math.sin(w.x * 0.21) * math.cos(w.y * 0.17)
            t.mul(li, [lerp(1.0, shade[i], k) for i in range(3)])
        t.write()


def light_shafts(c, bb, gaps):
    """Shafts of sunlight slanting down through the gaps in the canopy."""
    m = Mesh()
    for k, (x, y) in enumerate(gaps):
        top = Vector((x, y, 48.0 + 6 * rnd(k)))
        foot = top + SUN_RAY * ((top.z - 0.3) / -SUN_RAY.z)
        _shaft(m, top, foot, 5.0 + 3 * rnd(k * 3), 9.0 + 4 * rnd(k * 5))
    m.build(c, "Sun Shafts", "Light", role="visual")


# ------------------------------------------------------------------ the boardwalks


def timber(c, bb, ter, lights):
    """Every raised walkway's timber: pilings down into the swamp, cross-braces on the
    high trestles, rail posts with a sagging rope between, and torch posts; stone
    balustrade posts and braziers along the causeway; torch posts along the dike."""
    m = Mesh()
    tp = sp.torch_post(c, 2.8)
    br = sp.stone_brazier(c)
    web = sp.cobweb(c, 0)
    for piece in c.pieces:
        kind = piece.name.split()[-1]
        s0, s1 = piece["kp_from"], piece["kp_to"]
        if s1 < s0:
            s1 += c.length
        if bb.INSIDE[0] - 4 <= s0 and s1 <= bb.INSIDE[1] + 4:
            continue
        if kind in ("boardwalk", "bridge"):
            deck = 2.4 if kind == "boardwalk" else 3.0
            # Pilings and braces.
            s = s0 + 3.0
            prev = {}
            while s < s1 - 1:
                q = c.at(s)
                for sd in (-1, 1):
                    p = q.side(sd * (q.w / 2 - 0.6))
                    bot = min(-1.5, (bb.natural(p.x, p.y) if bb.natural(p.x, p.y) < 0 else -1.5))
                    tz = p.z - deck + 0.2
                    m.tube(("bog_root", "wall"), [(p.x, p.y, bot), (p.x, p.y, tz)], 0.55, n=5)
                    if sd in prev and tz - bot > 6:
                        a = prev[sd]
                        m.tube(("bog_root", "wall"), [(a[0], a[1], bot + 0.8), (p.x, p.y, tz - 0.6)], 0.2, n=4)
                        m.tube(("bog_root", "wall"), [(a[0], a[1], a[2] - 0.6), (p.x, p.y, bot + 0.8)], 0.2, n=4)
                    prev[sd] = (p.x, p.y, tz)
                s += 10.0
            # Rail posts and rope.
            s = s0 + 1.0
            tops = {-1: [], 1: []}
            while s < s1:
                q = c.at(s)
                for sd in (-1, 1):
                    p = q.side(sd * (q.w / 2 + 0.85), 0.0)
                    m.tube(("bog_rail", "wall"), [(p.x, p.y, p.z - 0.6), (p.x, p.y, p.z + 1.9)], 0.2, n=4)
                    tops[sd].append(Vector((p.x, p.y, p.z + 1.75)))
                s += 7.0
            for sd in (-1, 1):
                for a, b in zip(tops[sd], tops[sd][1:]):
                    m.tube(("thatch", "wall"), [tuple(a), tuple(b - Vector((0, 0, 0.25)))], 0.07, n=3)
            # The odd cobweb strung between the rail posts.
            for sd in (-1, 1):
                for j in range(3 if sd < 0 else 5, len(tops[sd]) - 1, 9):
                    a, b = tops[sd][j], tops[sd][j + 1]
                    mid = (a + b) / 2 - Vector((0, 0, 0.9))
                    c.place(web, mid.x, mid.y, mid.z, rot=math.atan2((b - a).y, (b - a).x), scale=0.55, coll="Boardwalk", role="visual")
            # Torch posts.
            s = s0 + 12.0
            k = 0
            while s < s1 - 4:
                q = c.at(s)
                sd = 1 if k % 2 else -1
                p = q.side(sd * (q.w / 2 + 1.7))
                c.place(tp, p.x, p.y, p.z - 0.4, rot=k, coll="Boardwalk", role="visual")
                lights.append((p.x, p.y, p.z + 3.0))
                s += 26.0
                k += 1
        elif kind == "causeway":
            s = s0 + 2.0
            k = 0
            while s < s1 - 1:
                q = c.at(s)
                rot = math.atan2(q.t.y, q.t.x)
                for sd in (-1, 1):
                    p = q.side(sd * (q.w / 2 + 1.6))
                    m.box(CARVED, (p.x, p.y, p.z + 1.0), (1.6, 1.6, 2.8), rot)
                    m.box(STONE, (p.x, p.y, p.z + 2.6), (2.0, 2.0, 0.5), rot)
                    if k % 3 == 1:
                        m.add(BONE, lambda bm, p=p: props.blob(bm, (p.x, p.y, p.z + 3.4), 0.7, sx=1.2, sz=0.9, subdiv=1))
                if k % 4 == 2:
                    sd = 1 if (k // 4) % 2 else -1
                    p = q.side(sd * (q.w / 2 + 4.0))
                    m.box(STONE, (p.x, p.y, p.z - 1.0), (3.4, 3.4, 2.6), rot)
                    c.place(br, p.x, p.y, p.z + 0.3, rot=rot, coll="Boardwalk", role="visual")
                    lights.append((p.x, p.y, p.z + 3.4))
                s += 10.0
                k += 1
            # Arches along the causeway's sides, and vines spilling over them.
            edges = []
            s = s0
            while s < s1 - 6:
                q, q2 = c.at(s), c.at(s + 6)
                for sd in (-1, 1):
                    a, b = q.side(sd * (q.w / 2 + 2.1), -0.2), q2.side(sd * (q.w / 2 + 2.1), -0.2)
                    edges.append((tuple(a), tuple(b), (q.r.x * sd, q.r.y * sd, 0)))
                s += 6.0
            drape(c, piece.name + " Vines", edges, ("vine_leaf", "grass"), 1.5, 7.0, 1.5, seed=int(s0), coll="Boardwalk")
        elif kind == "dike":
            s = s0 + 8.0
            k = 0
            while s < s1 - 4:
                q = c.at(s)
                sd = 1 if k % 2 else -1
                p = q.side(sd * (q.w / 2 + 3.0))
                z = c.ground_z(p.x, p.y, ter) or p.z
                c.place(tp, p.x, p.y, z - 0.3, rot=k, coll="Boardwalk", role="visual")
                lights.append((p.x, p.y, z + 3.1))
                s += 24.0
                k += 1
    m.build(c, "Boardwalk Timber", "Boardwalk", role="visual")


# ------------------------------------------------------------------ the living swamp


def swamp_life(c, bb, ter, lights):
    """Lily pads and flowers, cattails and reeds, rotting logs, stumps and sunken
    timber, bubbling glowing pools, mist, crocodiles and frogs; the stilt village and
    the watchtowers; glowing caps and big leaves on the banks."""
    S = getattr(bb, "SCENE_SEG", bb.SEG)
    area = (-300, 340, -300, 340)

    def water(m0, m1):
        def ok(x, y, z):
            if z > -0.2 or bb.on_foundation(x, y, 4):
                return False
            smp, d = c.nearest(x, y)
            return smp.w / 2 + m0 < d < smp.w / 2 + m1
        return ok

    def bank(m0, m1):
        def ok(x, y, z):
            if z < 0.3 or bb.on_foundation(x, y, 4):
                return False
            smp, d = c.nearest(x, y)
            return smp.w / 2 + m0 < d < smp.w / 2 + m1
        return ok

    def at_water(fn):
        """scatter() puts things on the ground; for things that float, lift to 0."""
        return fn

    pads = [props.lily_pad(c, v) for v in range(2)]
    for v, pd in enumerate(pads):
        for x, y in props.scatter(c, pd, 110, area, water(3, 70), ter, seed=500 + v, scale=(0.8, 2.2), coll="Swamp", role="visual", sink=0.0):
            pass
    # (scatter sets z from the swamp bed; float the pads, lotuses and timber.)
    lotus = props.lotus(c)
    props.scatter(c, lotus, 12, area, water(4, 50), ter, seed=510, scale=(0.9, 1.5), coll="Swamp", role="visual", sink=0.0)
    for ob in list(c.coll("Swamp").objects):
        ob.location.z = 0.02
    cat = [sp.cattail_clump(c, v) for v in range(2)]
    for v, ct in enumerate(cat):
        props.scatter(c, ct, 38, area, water(2.5, 45), ter, seed=520 + v, scale=(1.3, 2.2), coll="Reeds", role="visual", sink=0.0)
        props.scatter(c, ct, 14, area, bank(4, 40), ter, seed=525 + v, scale=(1.3, 2.2), coll="Reeds", role="visual", sink=0.0)
    reeds = props.reeds(c)
    props.scatter(c, reeds, 40, area, water(2.5, 50), ter, seed=530, scale=(1.4, 2.4), coll="Reeds", role="visual", sink=0.0)
    for ob in list(c.coll("Reeds").objects):
        if ob.location.z < 0:
            ob.location.z = -0.4
    logs = [props.log(c, v) for v in range(2)]
    stumps = [props.stump(c, v) for v in range(2)]
    timber_ = [sp.sunken_timber(c, v) for v in range(3)]
    float_from = len(c.coll("Swamp").objects)
    for v, lg in enumerate(logs):
        props.scatter(c, lg, 10, area, water(5, 60), ter, seed=540 + v, scale=(1.2, 2.0), coll="Swamp", role="visual", sink=0.0)
    for v, st in enumerate(stumps):
        props.scatter(c, st, 10, area, water(4, 60), ter, seed=550 + v, scale=(1.2, 2.2), coll="Swamp", role="visual", sink=0.0)
    for v, tb in enumerate(timber_):
        props.scatter(c, tb, 6, area, water(8, 70), ter, seed=560 + v, scale=(1.0, 1.4), coll="Swamp", role="visual", sink=0.0)
    for ob in list(c.coll("Swamp").objects)[float_from:]:
        ob.location.z = -0.5 if "Log" in ob.name else -0.3
    caps = props.glow_caps(c)
    props.scatter(c, caps, 8, area, bank(3, 60), ter, seed=570, scale=(1.0, 2.0), coll="Swamp", role="visual", sink=0.1)
    leaves = [props.big_leaf_plant(c, v) for v in range(2)]
    for v, lf in enumerate(leaves):
        props.scatter(c, lf, 22, area, bank(3, 60), ter, seed=580 + v, scale=(1.2, 2.2), coll="Swamp", role="visual", sink=0.1)
    fern = props.fern(c, "jungle_fern")
    props.scatter(c, fern, 30, area, bank(2.5, 50), ter, seed=590, scale=(1.2, 2.0), coll="Swamp", role="visual", sink=0.1)
    frog = props.frog(c)
    props.scatter(c, frog, 4, area, bank(2, 14), ter, seed=600, scale=(1.4, 2.0), coll="Swamp", role="visual", sink=0.0)
    # Crocodiles, lurking beside the walkways.
    croc = sp.croc(c)
    for k, s in enumerate((S[3] + 10, S[7] + 30, S[18] + 20, S[22] + 30, S[10])):
        q = c.at(s)
        sd = -1 if k % 2 else 1
        p = q.side(sd * (q.w / 2 + 9 + 4 * rnd(k)))
        if bb.natural(p.x, p.y) < -0.5 and not bb.on_foundation(p.x, p.y, 4):
            c.place(croc, p.x, p.y, 0.0, rot=math.atan2(q.t.y, q.t.x) + (0.3 if k % 2 else -2.8), scale=1.6, coll="Swamp", role="visual")
    # Bubbling pools, glowing in the murk.
    pools = []
    k = 0
    s = 40.0
    while s < c.length:
        q = c.at(s)
        sd = 1 if k % 2 else -1
        p = q.side(sd * (q.w / 2 + 10 + 14 * rnd(k * 3.7)))
        k += 1
        s += 55.0 + 40 * rnd(k)
        if bb.natural(p.x, p.y) > -0.8 or bb.on_foundation(p.x, p.y, 8):
            continue
        r = 3.5 + 3.5 * rnd(k * 1.1)
        c.disc("Glow Pool %d" % k, p.x, p.y, r, 0.04, c.lib("bog_glow_pool"), coll="Water", role="visual", n=14, wobble=0.25, seed=k)
        pools.append((p.x, p.y, r))
    # Swamp mist, drifting low over the water.
    mk = 0
    for x in range(-260, 320, 70):
        for y in range(-260, 330, 70):
            mk += 1
            px, py = x + (rnd(mk) - 0.5) * 40, y + (rnd(mk * 3) - 0.5) * 40
            if bb.natural(px, py) > -0.5 or bb.on_foundation(px, py, 6) or rnd(mk * 7) < 0.35:
                continue
            c.disc("Mist %d" % mk, px, py, 18 + 16 * rnd(mk * 5), 0.9 + 1.2 * rnd(mk * 9), c.lib("bog_mist"), coll="Mist", role="visual", n=16, wobble=0.3, seed=mk)
    # The stilt village along the mangrove boardwalks, and lookouts along the others.
    hut = [sp.stilt_hut(c, v) for v in range(2)]
    for k, (s, sd, off) in enumerate(((S[21] + 10, 1, 22), (S[22] + 20, -1, 24), (S[22] + 55, 1, 20), (S[23] + 20, -1, 26), (S[20] + 5, 1, 30), (S[24] + 10, 1, 24), (S[17] + 10, -1, 26))):
        q = c.at(s)
        p = q.side(sd * (q.w / 2 + off))
        if bb.on_foundation(p.x, p.y, 6) or not props.clear_of_road(c, p.x, p.y, 10):
            continue
        c.place(hut[k % 2], p.x, p.y, 0.0, rot=math.atan2(-sd * q.r.y, -sd * q.r.x) - math.pi / 2, coll="Village", role="visual")
        lights.append((p.x, p.y - 0.0, 7.0 + 2.0 * (k % 2) + 1.5))
    tower = sp.watchtower(c)
    for k, (s, sd, off) in enumerate(((S[2] + 15, -1, 14), (S[5] + 20, 1, 16), (S[26] + 20, -1, 24), (S[19] + 20, 1, 16))):
        q = c.at(s)
        p = q.side(sd * (q.w / 2 + off))
        if not props.clear_of_road(c, p.x, p.y, 7):
            continue
        c.place(tower, p.x, p.y, max(0.0, bb.natural(p.x, p.y)), rot=k * 0.6, coll="Village", role="visual")
        lights.append((p.x, p.y, 15.0))
    return pools


def treehouses(c, bb, placed, lights):
    """Plank platforms round the giant trunks near the mangrove boardwalks, with rope
    bridges slung between them, some right over the road."""
    plat = sp.platform(c, 0)
    near = []
    for x, y, sc in placed:
        smp, d = c.nearest(x, y)
        if len(near) < 10 and (_S(bb)[17] - 10 <= smp.s <= _S(bb)[25] + 10 or _S(bb)[1] <= smp.s <= _S(bb)[5]):
            z = 18.0 + 4.0 * rnd(x * 0.1 + y)
            c.place(plat, x, y, z, rot=rnd(x) * math.tau, scale=sc, coll="Village", role="visual")
            near.append((x, y, z, sc))
            lights.append((x, y, z + 2.0))
    m = Mesh()
    pairs = set()
    for i, (x, y, z, sc) in enumerate(near):
        others = sorted((math.hypot(o[0] - x, o[1] - y), j) for j, o in enumerate(near) if j != i)
        for d, j in others[:1]:
            if 30 < d < 95:
                pairs.add((min(i, j), max(i, j)))
    for i, j in sorted(pairs)[:9]:
        x, y, z, sc = near[i]
        if True:
            x2, y2, z2, sc2 = near[j]
            if True:
                a = Vector((x, y, z))
                b = Vector((x2, y2, z2))
                f = (b - a)
                f.z = 0
                f.normalize()
                a += f * 8.8 * sc
                b -= f * 8.8 * sc2
                _rope_bridge(m, a, b)
    m.build(c, "Rope Bridges", "Village", role="visual")


def _rope_bridge(m, a, b, width=2.2, sag=2.5):
    """A rope bridge from a to b: a sagging strip of planks with a rope rail each side."""
    f = (b - a)
    f.z = 0
    L = f.length
    f.normalize()
    side = Vector((-f.y, f.x, 0))
    n = max(4, int(L / 3.0))
    pts = [a.lerp(b, k / n) - Vector((0, 0, sag * 4 * (k / n) * (1 - k / n))) for k in range(n + 1)]

    def deck(bm):
        rows = [(bm.verts.new(p - side * width / 2), bm.verts.new(p + side * width / 2)) for p in pts]
        for r0, r1 in zip(rows, rows[1:]):
            bm.faces.new((r0[0], r1[0], r1[1], r0[1]))

    m.add(("bog_boards", "wall"), deck)
    for sd in (-1, 1):
        m.tube(("thatch", "wall"), [tuple(p + side * sd * width / 2 + Vector((0, 0, 1.1))) for p in pts], 0.06, n=3)


# ------------------------------------------------------------------ build


def build(c, pyr, bb):
    ter = list(c.coll("Terrain").objects)
    lights = []
    inner = []
    falls = []
    S = getattr(bb, "SCENE_SEG", bb.SEG)
    # The pyramid: its two carved faces with their waterfalls, the stairs, the vines
    # over every tier, the terrace and its fires, trees growing on the tiers.
    e = c.at(bb.INSIDE[0])
    _, f1 = facade(c, bb, (e.p.x, e.p.y), (1.0, 0.0), "East Face", 1.0)
    x = c.at(bb.INSIDE[1])
    _, f2 = facade(c, bb, (x.p.x, x.p.y), (0.0, -1.0), "South Face", 0.8)
    falls += f1 + f2
    stairs(c, bb)
    tier_drapes(c, bb)
    terrace(c, bb, lights)
    tr = [sp.tier_tree(c, v) for v in range(2)]
    jt = sp.tier_tree(c, 2)
    k = 0
    cx, cy = bb.PYR
    for i in range(160):
        x = cx + (rnd(i * 1.7) - 0.5) * 2 * (bb.PYR_HX - 3)
        y = cy + (rnd(i * 2.9) - 0.5) * 2 * (bb.PYR_HY - 3)
        z = bb.pyramid_top(x, y)
        e_ = min(bb.PYR_HX - abs(x - cx), bb.PYR_HY - abs(y - cy))
        if z is None or abs(x - cx) < 14 or abs(y - cy) < 14:
            continue  # leave the stairs and the doors clear
        inset = max(i_ for i_, _ in bb.TIERS if e_ >= i_)
        if e_ - inset > 7.0:  # only on the outer part of each step
            continue
        c.place((tr + [jt])[k % 3], x, y, z - 0.3, rot=rnd(i) * math.tau, scale=1.6 + 0.8 * rnd(i * 3), coll="Pyramid Dressing", role="visual")
        k += 1
        if k > 34:
            break
    inside_dressing(c, bb, inner, falls)

    bones(c, bb, ter)
    placed, cover, gaps = trees(c, bb, ter)
    hanging_life(c, bb, cover)
    timber(c, bb, ter, lights)
    pools = swamp_life(c, bb, ter, lights)
    treehouses(c, bb, placed, lights)
    light_shafts(c, bb, gaps)

    # Light and shade: the hand-painted firelight inside the pyramid (dark stone, warm
    # pools of torchlight), warm light round every fire outside, and dappled canopy
    # shade over the swamp.
    c.preset("sun", ter + [pyr], 0.3)
    c.preset("bottoms", ter, 0.45)
    c.glow([pyr], inner, 13.0, (1.35, 1.0, 0.62), base=0.4, region=lambda w: interior(c, bb, w))
    canopy_shade(c, ter, cover, gaps, bb)
    c.glow(ter + [pyr], lights, 14.0, (1.3, 1.05, 0.72), base=1.0, region=lambda w: not interior(c, bb, w))
    for x, y, z in lights + inner:
        gx, gy, gz = c.game(x, y, z)
        c.entity("torch", x=gx, y=gy, z=gz)
    for fx, fy, foot, top, w in falls:
        gx, gy, gz = c.game(fx, fy, foot)
        c.entity("waterfall", x=gx, y=gy, z=gz, top=round(top, 1), width=w, heading=0)
    for x, y, r in pools:
        gx, gy, gz = c.game(x, y, 0.1)
        c.entity("bubbles", x=gx, y=gy, z=gz, r=round(r, 1))
    c.entity("fireflies", rate=40, radius=36)
    sky = [(40 + 170 * math.cos(a), 60 + 150 * math.sin(a), 62 + 8 * math.sin(3 * a)) for a in [k * math.tau / 16 for k in range(16)]]
    c.path_curve("Flyer Path", sky)
    c.entity("pterosaur", route="Flyer Path", speed=13.0, scale=1.7)

    # Fewer things to draw: join the copies in each collection, map square by square.
    c.merge_props(("Bones", "Swamp", "Reeds", "Vines", "Canopy", "Boardwalk", "Village", "Pyramid Dressing", "Pyramid Inside"))
