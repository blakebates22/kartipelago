# Dry Gulch Ghost Town's town (see dry_gulch.py): the frontier buildings (a kit of
# false-fronted, clapboard buildings with porches, balconies, lit and boarded windows and
# painted signs), Main Street, the town square, the saloon district and its side
# street, the chapel and its clock tower, the water tower, the windmill, the back lanes,
# the graveyard on its knoll, the start arch, and the mineworks round the Hazard Mine
# (the portal, the headframe, the ore bins, the railway and its trestle, the stamp mill).
# SPDX-License-Identifier: MIT

import math

import canyon_props as cp
import gulch_props as gp
from canyon_props import _beam, _cyl
from course_kit import Vector, bmesh, lerp, rnd
from props import cuboid, loft, ring

from gulch_scenery import Mesh, clear, game_entity, road_rot

TIMBER = ("weathered_timber", "wall")
# How many 64 px tiles each painted sign is cut into (see make_textures.py).
SIGN_TILES = {
    "sign_saloon": 2, "sign_general": 3, "sign_hotel": 2, "sign_sheriff": 2, "sign_jail": 1, "sign_bank": 1,
    "sign_assay": 3, "sign_livery": 2, "sign_undertaker": 3, "sign_barber": 2, "sign_drygulch": 4,
    "sign_ghosttown": 4, "sign_hazard": 4, "sign_keepout": 2, "sign_finish": 2, "sign_shaft": 3,
}
SIGNS = {  # sign id: (material, width / height of its picture)
    "saloon": ("sign_saloon", 4.0),
    "general": ("sign_general", 6.0),
    "hotel": ("sign_hotel", 4.0),
    "sheriff": ("sign_sheriff", 4.0),
    "jail": ("sign_jail", 2.0),
    "bank": ("sign_bank", 2.0),
    "assay": ("sign_assay", 6.0),
    "livery": ("sign_livery", 4.0),
    "undertaker": ("sign_undertaker", 6.0),
    "barber": ("sign_barber", 4.0),
    "keepout": ("sign_keepout", 4.0),
    "shaft": ("sign_shaft", 6.0),
}


# ------------------------------------------------------------------ the building kit


class Frame:
    """A building's own frame: u along its front, v back from it, origin at the front's
    middle on the ground."""

    def __init__(self, x, y, z, rot):
        self.x, self.y, self.z = x, y, z
        self.ca, self.sa = math.cos(rot), math.sin(rot)
        self.rot = rot

    def P(self, u, v, h=0.0):
        return (self.x + u * self.ca - v * self.sa, self.y + u * self.sa + v * self.ca, self.z + h)

    def N(self, nu, nv):
        """A direction in the frame, as world (x, y)."""
        return (nu * self.ca - nv * self.sa, nu * self.sa + nv * self.ca)


def face_quad(m, mat, cx, cy, nx, ny, hw, z0, z1, out=0.04, flip=False):
    """An upright picture quad (a window, a door, a sign) centred on (cx, cy), facing the
    outward normal (nx, ny), its picture once across it."""
    rx, ry = -ny, nx
    ox, oy = cx + nx * out, cy + ny * out
    n = SIGN_TILES.get(mat[0], 0)
    if n:
        # A painted sign: its tiles side by side, left to right.
        w = 2 * hw / n
        for k in range(n):
            a, b = -hw + k * w, -hw + (k + 1) * w
            pts = [(ox + rx * a, oy + ry * a, z0), (ox + rx * b, oy + ry * b, z0), (ox + rx * b, oy + ry * b, z1), (ox + rx * a, oy + ry * a, z1)]
            m.quad(("%s_%d" % (mat[0], k + 1), mat[1]), pts, [(0, 0), (1, 0), (1, 1), (0, 1)])
        return
    pts = [(ox - rx * hw, oy - ry * hw, z0), (ox + rx * hw, oy + ry * hw, z0), (ox + rx * hw, oy + ry * hw, z1), (ox - rx * hw, oy - ry * hw, z1)]
    uvs = [(0, 0), (1, 0), (1, 1), (0, 1)]
    if flip:
        uvs = [(1, 0), (0, 0), (0, 1), (1, 1)]
    m.quad(mat, pts, uvs)


def window(m, f, sc, u, v, nu, nv, z0, kind, frame=True):
    """A window on a wall (at (u, v) of the frame, facing (nu, nv)), its sill at z0."""
    cx, cy, _ = f.P(u, v)
    nx, ny = f.N(nu, nv)
    mat = {"lit": ("window_lit", "wall"), "dark": ("window_dark", "wall"), "ghost": ("window_ghost", "wall")}[kind]
    if frame:
        m.add(TIMBER, lambda bm: cuboid(bm, (cx + nx * 0.02, cy + ny * 0.02, z0 + 0.85), (1.6, 0.12, 2.0), f.rot + math.atan2(nv, nu) - math.pi / 2))
        m.add(TIMBER, lambda bm: cuboid(bm, (cx + nx * 0.12, cy + ny * 0.12, z0 - 0.12), (1.7, 0.3, 0.12), f.rot + math.atan2(nv, nu) - math.pi / 2))
    face_quad(m, mat, cx, cy, nx, ny, 0.65, z0, z0 + 1.7, out=0.1)
    if kind == "lit":
        sc.warm.append((cx + nx * 1.0, cy + ny * 1.0, z0 + 1.0))
    elif kind == "ghost":
        sc.green.append((cx + nx * 1.0, cy + ny * 1.0, z0 + 1.0))


def pick_window(seed, lit=0.5, ghost=0.08):
    r = rnd(seed)
    return "ghost" if r < ghost else "lit" if r < ghost + lit else "dark"


def gable(m, mat, f, w, d, z_eave, rise, over=0.5, v0=0.0):
    """A gable roof over a w x d body: its ridge runs back along v."""
    def make(bm):
        e = w / 2 + over
        for under in (False, True):
            a = [bm.verts.new(f.P(-e, v0 - over, z_eave - over * 0.4)), bm.verts.new(f.P(0, v0 - over, z_eave + rise)),
                 bm.verts.new(f.P(e, v0 - over, z_eave - over * 0.4))]
            b = [bm.verts.new(f.P(-e, d + over, z_eave - over * 0.4)), bm.verts.new(f.P(0, d + over, z_eave + rise)),
                 bm.verts.new(f.P(e, d + over, z_eave - over * 0.4))]
            if not under:
                bm.faces.new((a[0], b[0], b[1], a[1]))
                bm.faces.new((a[1], b[1], b[2], a[2]))
            else:
                # The underside, so the overhang reads from below.
                bm.faces.new((a[1], b[1], b[0], a[0]))
                bm.faces.new((a[2], b[2], b[1], a[1]))

    m.add(mat, make)


def gable_ends(m, mat, f, w, d, z_eave, rise):
    def make(bm):
        for v, flip in ((0.0, True), (d, False)):
            t = [bm.verts.new(f.P(-w / 2, v, z_eave)), bm.verts.new(f.P(w / 2, v, z_eave)), bm.verts.new(f.P(0, v, z_eave + rise))]
            bm.faces.new(list(reversed(t)) if flip else t)

    m.add(mat, make)


def building(m, sc, x, y, z0, rot, w, d, *, storeys=1, siding="siding_brown", sign=None, porch=True, balcony=False,
             false_front=True, roof="shingle_roof", lit=0.5, ghost=0.08, seed=0, door=True, lanterns=True, stilts=0.0):
    """A frontier building facing the street (the front at the frame's origin): a stone
    footing, a clapboard body, a gable roof, a false front with its sign and a cornice,
    a boardwalk porch on posts (a balcony over it on a taller building), lit, boarded and
    haunted windows, a door, lanterns hanging off the porch."""
    f = Frame(x, y, z0, rot)
    H = 0.5 + storeys * 3.6
    wall = (siding, "wall")
    sc.footprints.append((f.P(0, d / 2)[0], f.P(0, d / 2)[1], math.hypot(w, d) / 2 + 1.0))
    # The footing and the body.
    m.add(("masonry", "wall"), lambda bm: cuboid(bm, f.P(0, d / 2, -1.2 - stilts / 2), (w + 0.3, d + 0.3, 2.0 + stilts), rot))
    m.add(wall, lambda bm: cuboid(bm, f.P(0, d / 2, H / 2 + 0.2), (w, d, H - 0.4), rot))
    rise = min(4.0, w * 0.32)
    gable(m, (roof, "wall"), f, w, d, H, rise, v0=0.0 if not false_front else 0.3)
    gable_ends(m, wall, f, w, d, H, rise)
    top = H
    if false_front:
        top = max(H + 2.6, H + rise + 0.8)
        m.add(wall, lambda bm: cuboid(bm, f.P(0, 0.0, (H + top) / 2), (w + 0.6, 0.4, top - H), rot))
        m.add(TIMBER, lambda bm: cuboid(bm, f.P(0, -0.15, top + 0.15), (w + 1.0, 0.7, 0.3), rot))
        if w > 9:
            m.add(wall, lambda bm: cuboid(bm, f.P(0, 0.0, top + 0.8), (w * 0.45, 0.4, 1.3), rot))
            m.add(TIMBER, lambda bm: cuboid(bm, f.P(0, -0.15, top + 1.55), (w * 0.45 + 0.5, 0.6, 0.25), rot))
        # Brackets under the cornice.
        for k in range(int(w / 2.5) + 1):
            u = -w / 2 + k * w / int(w / 2.5)
            m.add(TIMBER, lambda bm, u=u: cuboid(bm, f.P(u, -0.35, top - 0.25), (0.2, 0.4, 0.5), rot))
    # Windows: across the front on every storey (the door in the middle downstairs), and
    # along the sides.
    fn = f.N(0, -1)
    for st in range(storeys):
        zs = 0.5 + st * 3.6 + 1.0
        n = max(1, int((w - 1.5) / 3.0))
        for k in range(n):
            u = -w / 2 + (k + 0.5) * w / n
            if st == 0 and door and abs(u) < 1.6:
                continue
            window(m, f, sc, u, 0.0, 0, -1, z0 + zs, pick_window(seed * 31 + st * 7 + k, lit, ghost))
        for side in (-1, 1):
            nk = max(1, int((d - 2.0) / 4.5))
            for k in range(nk):
                v = (k + 0.5) * d / nk
                window(m, f, sc, side * w / 2, v, side, 0, z0 + zs, pick_window(seed * 37 + st * 11 + k * 3 + side, lit * 0.8, ghost))
    if door:
        cx, cy, _ = f.P(0, 0)
        face_quad(m, ("door_wood", "wall"), cx, cy, fn[0], fn[1], 1.0, z0 + 0.5, z0 + 3.1, out=0.06)
    # The sign.
    if sign:
        mat, aspect = SIGNS[sign]
        sw = min(w * 0.85, 2.0 * aspect) if aspect > 2 else min(w * 0.5, 3.0)
        sh = sw / aspect * (1.0 if aspect > 2 else 1.0)
        zc = (H + top) / 2 + 0.3 if false_front else H - 0.2
        cx, cy, _ = f.P(0, -0.2 if false_front else -3.3)
        face_quad(m, (mat, "wall"), cx, cy, fn[0], fn[1], sw / 2, zc - sh / 2, zc + sh / 2, out=0.06)
    # The porch: a boardwalk, posts, a sloping roof (or the balcony's floor over it).
    if porch:
        pd = 3.2
        m.add(("board_walk", "wall"), lambda bm: cuboid(bm, f.P(0, -pd / 2, 0.25), (w + 1.2, pd, 0.5), rot))
        m.add(TIMBER, lambda bm: cuboid(bm, f.P(0, -pd - 0.15, 0.1), (w + 1.2, 0.5, 0.3), rot))
        posts = [-w / 2 - 0.3] + [-w / 2 + k * w / max(1, int(w / 4.5)) for k in range(1, int(w / 4.5))] + [w / 2 + 0.3]
        roof_z = 0.5 + 3.4
        for u in posts:
            m.add(TIMBER, lambda bm, u=u: cuboid(bm, f.P(u, -pd + 0.2, roof_z / 2 + 0.25), (0.28, 0.28, roof_z - 0.5), rot))
        if balcony and storeys >= 2:
            fl = 0.5 + 3.6
            m.add(("board_walk", "wall"), lambda bm: cuboid(bm, f.P(0, -pd / 2, fl), (w + 1.2, pd + 0.2, 0.3), rot))
            for u in posts:
                m.add(TIMBER, lambda bm, u=u: cuboid(bm, f.P(u, -pd + 0.2, fl + 0.6), (0.18, 0.18, 1.2), rot))
            m.add(TIMBER, lambda bm: cuboid(bm, f.P(0, -pd + 0.2, fl + 1.15), (w + 1.2, 0.14, 0.14), rot))
            for k in range(int((w + 1.2) / 0.6)):
                u = -w / 2 - 0.6 + k * 0.6
                m.add(TIMBER, lambda bm, u=u: cuboid(bm, f.P(u, -pd + 0.2, fl + 0.6), (0.07, 0.07, 1.0), rot))
            # Its own little roof, over the balcony.
            m.add((roof, "wall"), lambda bm: cuboid(bm, f.P(0, -pd / 2, fl + 3.3), (w + 1.4, pd + 0.6, 0.18), rot, tilt=(-0.14, 0.0)))
            for u in (posts[0], posts[-1]):
                m.add(TIMBER, lambda bm, u=u: cuboid(bm, f.P(u, -pd + 0.2, fl + 1.6), (0.2, 0.2, 3.2), rot))
        else:
            m.add((roof, "wall"), lambda bm: cuboid(bm, f.P(0, -pd / 2 - 0.2, roof_z + 0.25), (w + 1.4, pd + 0.8, 0.16), rot, tilt=(-0.16, 0.0)))
        if lanterns:
            for u in (posts[0], posts[-1]):
                hx, hy, _ = f.P(u * 0.92, -pd + 0.6)
                sc.put("Hanging Lantern", hx, hy, z0 + roof_z - 0.05, f.rot, coll="Town Props", role="both")
                sc.warm.append((hx, hy, z0 + roof_z - 0.8))
            hx, hy, _ = f.P(posts[0] * 0.92, -pd + 0.6)
            sc.lanterns.append((hx, hy, z0 + roof_z - 0.8))
    return f, top


# ------------------------------------------------------------------ special buildings


def saloon(m, sc, x, y, z, rot):
    """The Dry Gulch Saloon: a big two-storey building with a balcony round its front,
    a tall stepped false front with the SALOON sign, swinging doors, warm light in every
    window downstairs and something pale moving behind one upstairs."""
    f, top = building(m, sc, x, y, z, rot, 22.0, 18.0, storeys=2, siding="siding_red", sign="saloon", balcony=True, lit=0.85, ghost=0.0,
                      seed=1, door=False)
    fn = f.N(0, -1)
    # The batwing doors (the doors themselves are the "door" entity: they swing).
    cx, cy, _ = f.P(0, 0)
    face_quad(m, ("window_lit", "wall"), cx, cy, fn[0], fn[1], 1.2, z + 0.5, z + 3.2, out=0.03)
    sc.doors.append((cx + fn[0] * 0.25, cy + fn[1] * 0.25, z + 0.55, f.rot))
    # The ghost upstairs: behind the second window from the left.
    gx, gy, _ = f.P(-5.5, -0.3)
    sc.ghosts.append({"look": "window", "x": gx, "y": gy, "z": z + 0.5 + 3.6 + 0.9, "heading": f.rot - math.pi / 2, "period": 11.0, "offset": 2.0})
    # A piano-shaped glow... and a cattle skull over the sign.
    sx, sy, _ = f.P(0, -0.5)
    sc.put("Cattle Skull", sx, sy, z + top + 1.9, f.rot, scale=1.4, coll="Town Props", role="both")
    return f


def hotel(m, sc, x, y, z, rot):
    f, top = building(m, sc, x, y, z, rot, 20.0, 16.0, storeys=3, siding="siding_ochre", sign="hotel", balcony=True, lit=0.45, ghost=0.12,
                      seed=2)
    gx, gy, _ = f.P(20.0 / 2 - 20.0 / 6 * 1.5, -0.3)
    sc.ghosts.append({"look": "window", "x": gx, "y": gy, "z": z + 0.5 + 7.2 + 0.9, "heading": f.rot - math.pi / 2, "period": 14.0, "offset": 7.0})
    return f


def sheriff(m, sc, x, y, z, rot):
    """The sheriff's office and the jail beside it: barred windows, a crooked sign, and a
    shape that sometimes stands at the bars."""
    f, top = building(m, sc, x, y, z, rot, 11.0, 12.0, siding="siding_grey", sign="sheriff", lit=0.6, ghost=0.0, seed=3)
    # The jail: a low stone block with barred windows.
    j = Frame(*f.P(11.0 / 2 + 5.0, 1.0), rot)
    m.add(("masonry", "wall"), lambda bm: cuboid(bm, j.P(0, 5.0, 1.8), (8.0, 10.0, 4.4), rot))
    m.add(("tin_roof", "wall"), lambda bm: cuboid(bm, j.P(0, 5.0, 4.15), (8.8, 10.8, 0.3), rot, tilt=(0.06, 0.0)))
    fn = j.N(0, -1)
    for u in (-2.0, 2.0):
        cx, cy, _ = j.P(u, 0)
        face_quad(m, ("window_dark", "wall"), cx, cy, fn[0], fn[1], 0.7, z + 1.4, z + 2.8, out=0.05)
        for k in range(5):
            bx, by, _ = j.P(u - 0.56 + k * 0.28, -0.15)
            m.add(("iron", "wall"), lambda bm, bx=bx, by=by: cuboid(bm, (bx, by, z + 2.1), (0.07, 0.07, 1.5)))
    cx, cy, _ = j.P(0, 0)
    face_quad(m, ("sign_jail", "wall"), cx, cy, fn[0], fn[1], 1.4, z + 3.1, z + 3.8, out=0.06)
    gx, gy, _ = j.P(2.0, -0.3)
    sc.ghosts.append({"look": "window", "x": gx, "y": gy, "z": z + 1.3, "heading": rot - math.pi / 2, "period": 17.0, "offset": 4.0, "scale": 0.8})
    sc.footprints.append((j.P(0, 5)[0], j.P(0, 5)[1], 7.0))
    return f


def livery(m, sc, x, y, z, rot):
    """The livery stable: a big barn, a hayloft door, a corral fence out front."""
    f = Frame(x, y, z, rot)
    w, d, H = 16.0, 20.0, 6.0
    sc.footprints.append((f.P(0, d / 2)[0], f.P(0, d / 2)[1], 14.0))
    m.add(("siding_red", "wall"), lambda bm: cuboid(bm, f.P(0, d / 2, H / 2), (w, d, H), rot))
    gable(m, ("shingle_roof", "wall"), f, w, d, H, 6.0, over=0.7)
    gable_ends(m, ("siding_red", "wall"), f, w, d, H, 6.0)
    fn = f.N(0, -1)
    cx, cy, _ = f.P(0, 0)
    face_quad(m, ("door_wood", "wall"), cx, cy, fn[0], fn[1], 2.6, z, z + 4.4, out=0.06)
    face_quad(m, ("window_dark", "wall"), cx, cy, fn[0], fn[1], 1.1, z + 7.2, z + 9.0, out=0.06)
    face_quad(m, ("sign_livery", "wall"), cx, cy, fn[0], fn[1], 2.4, z + 4.9, z + 6.1, out=0.08)
    sc.put("Hanging Lantern", *f.P(-3.5, -0.4), z + 4.6, rot, coll="Town Props", role="both")
    sc.warm.append(f.P(-3.5, -0.6, 4.0))
    return f


def chapel(m, sc, x, y, z, rot):
    """The chapel at the edge of town: a white clapboard nave, and its tower rising
    above everything round it: the clock (stopped at a quarter to midnight), the open
    belfry with the bell, a tall spire."""
    f = Frame(x, y, z, rot)
    w, d, H = 10.0, 18.0, 6.0
    sc.footprints.append((f.P(0, d / 2)[0], f.P(0, d / 2)[1], 12.0))
    m.add(("masonry", "wall"), lambda bm: cuboid(bm, f.P(0, d / 2, -0.8), (w + 0.6, d + 0.6, 2.0), rot))
    m.add(("siding_grey", "wall"), lambda bm: cuboid(bm, f.P(0, d / 2, H / 2 + 0.2), (w, d, H - 0.4), rot))
    gable(m, ("shingle_roof", "wall"), f, w, d, H, 5.5, over=0.6)
    gable_ends(m, ("siding_grey", "wall"), f, w, d, H, 5.5)
    for side in (-1, 1):
        for k in range(3):
            window(m, f, sc, side * w / 2, 3.5 + k * 5.0, side, 0, z + 1.6, "ghost" if k == 1 and side > 0 else "lit", frame=True)
    # The tower, at the front.
    T = 5.6
    m.add(("siding_grey", "wall"), lambda bm: cuboid(bm, f.P(0, -T / 2 + 0.5, 10.0), (T, T, 20.0), rot))
    fn = f.N(0, -1)
    cx, cy, _ = f.P(0, -T + 0.5)
    face_quad(m, ("door_wood", "wall"), cx, cy, fn[0], fn[1], 1.1, z + 0.4, z + 3.2, out=0.05)
    # The clock: on three faces of the tower.
    for nu, nv, (u, v) in ((0, -1, (0, -T + 0.5)), (1, 0, (T / 2, -T / 2 + 0.5)), (-1, 0, (-T / 2, -T / 2 + 0.5))):
        cx, cy, _ = f.P(u, v)
        nx, ny = f.N(nu, nv)
        face_quad(m, ("clock_face", "wall"), cx, cy, nx, ny, 1.5, z + 15.0, z + 18.0, out=0.06)
        sc.warm.append((cx + nx * 2, cy + ny * 2, z + 16.5))
    # The belfry: corner posts, rails, a roof, then the spire.
    for su in (-1, 1):
        for sv in (-1, 1):
            m.add(TIMBER, lambda bm, su=su, sv=sv: cuboid(bm, f.P(su * (T / 2 - 0.3), -T / 2 + 0.5 + sv * (T / 2 - 0.3), 22.5), (0.45, 0.45, 5.0), rot))
    m.add(TIMBER, lambda bm: cuboid(bm, f.P(0, -T / 2 + 0.5, 20.15), (T + 0.4, T + 0.4, 0.3), rot))
    m.add(TIMBER, lambda bm: cuboid(bm, f.P(0, -T / 2 + 0.5, 25.1), (T + 0.6, T + 0.6, 0.35), rot))

    def spire(bm):
        c0 = f.P(0, -T / 2 + 0.5)
        base = [bm.verts.new(f.P(su * (T / 2 + 0.3), -T / 2 + 0.5 + sv * (T / 2 + 0.3), 25.3)) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        tip = bm.verts.new((c0[0], c0[1], z + 35.0))
        for i in range(4):
            bm.faces.new((base[i], base[(i + 1) % 4], tip))

    m.add(("shingle_roof", "wall"), spire)
    c0 = f.P(0, -T / 2 + 0.5)
    m.add(("iron", "wall"), lambda bm: cuboid(bm, (c0[0], c0[1], z + 36.0), (0.15, 0.15, 2.2), rot))
    m.add(("iron", "wall"), lambda bm: cuboid(bm, (c0[0], c0[1], z + 36.4), (1.2, 0.15, 0.15), rot))
    sc.bell = (c0[0], c0[1], z + 23.6, rot)
    sc.warm.append((c0[0], c0[1], z + 22.0))
    return f


def water_tower(c, sc, x, y, z):
    """The town's great water tower: four tall braced legs, a stave tank with iron hoops
    and a conical roof, a ladder, a lantern on the walkway."""
    m = Mesh()
    legs = [(sx * 4.2, sy * 4.2) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    H = 17.0
    for lx, ly in legs:
        m.add(TIMBER, lambda bm, lx=lx, ly=ly: _beam(bm, (x + lx * 1.15, y + ly * 1.15, z - 0.5), (x + lx * 0.85, y + ly * 0.85, z + H), 0.7))
        m.add(("masonry", "wall"), lambda bm, lx=lx, ly=ly: cuboid(bm, (x + lx * 1.15, y + ly * 1.15, z), (1.6, 1.6, 1.2)))
    for k in range(4):
        z0, z1 = z + k * H / 4, z + (k + 1) * H / 4
        f0, f1 = 1.15 - 0.3 * k / 4, 1.15 - 0.3 * (k + 1) / 4
        for i in range(4):
            (ax, ay), (bx, by) = legs[i], legs[(i + 1) % 4]
            m.add(TIMBER, lambda bm, ax=ax, ay=ay, bx=bx, by=by, z1=z1, f1=f1: _beam(bm, (x + ax * f1, y + ay * f1, z1), (x + bx * f1, y + by * f1, z1), 0.3))
            m.add(TIMBER, lambda bm, ax=ax, ay=ay, bx=bx, by=by, z0=z0, z1=z1, f0=f0, f1=f1: _beam(bm, (x + ax * f0, y + ay * f0, z0), (x + bx * f1, y + by * f1, z1), 0.18))
            m.add(TIMBER, lambda bm, ax=ax, ay=ay, bx=bx, by=by, z0=z0, z1=z1, f0=f0, f1=f1: _beam(bm, (x + bx * f0, y + by * f0, z0), (x + ax * f1, y + ay * f1, z1), 0.18))
    m.add(("board_walk", "wall"), lambda bm: _cyl(bm, x, y, z + H, z + H + 0.35, 6.4, 6.4, n=12))
    m.add(("tank_staves", "wall"), lambda bm: _cyl(bm, x, y, z + H + 0.35, z + H + 7.5, 5.2, 5.4, n=16))
    m.add(("iron", "wall"), lambda bm: [_cyl(bm, x, y, z + H + h, z + H + h + 0.25, 5.45, 5.45, n=16) for h in (1.6, 4.0, 6.4)])

    def roof(bm):
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=5.9, radius2=0.3, depth=3.2)
        for v in res["verts"]:
            v.co.x += x
            v.co.y += y
            v.co.z += z + H + 7.5 + 1.6

    m.add(("shingle_roof", "wall"), roof)
    for k in range(int(H / 0.5)):
        m.add(TIMBER, lambda bm, k=k: cuboid(bm, (x + 5.2, y - 0.6, z + k * 0.5), (0.1, 1.0, 0.08)))
    m.add(TIMBER, lambda bm: cuboid(bm, (x + 5.2, y - 1.1, z + H / 2), (0.12, 0.12, H)))
    m.add(TIMBER, lambda bm: cuboid(bm, (x + 5.2, y - 0.1, z + H / 2), (0.12, 0.12, H)))
    m.build(c, "Water Tower", "Town", role="both")
    sc.put("Hanging Lantern", x + 6.1, y, z + H + 2.0, coll="Town Props", role="both")
    sc.warm.append((x + 6.1, y, z + H + 1.0))
    sc.lanterns.append((x + 6.1, y, z + H + 1.0))
    sc.footprints.append((x, y, 8.0))


# ------------------------------------------------------------------ placing along the roads


def along(c, s0, s1, side, setback, kinds, sc, m, dg, gap=(1.5, 4.0), seed=0, z=None):
    """Buildings in a row along the route from s0 to s1 on one side (+1 right, -1 left),
    fronts `setback` metres from the centre line, facing the street. `kinds` cycles
    through (width, depth, options) tuples. Skips any that would crowd the road."""
    s = s0
    k = 0
    out = []
    while s < s1:
        w, d, opts = kinds[k % len(kinds)]
        mid = s + w / 2
        if mid + w / 2 > s1:
            break
        q = c.at(mid)
        h = road_rot(q)
        rot = h + math.pi if side > 0 else h
        nx, ny = (math.sin(h), -math.cos(h)) if side > 0 else (-math.sin(h), math.cos(h))
        x, y = q.p.x + nx * setback, q.p.y + ny * setback
        f = Frame(x, y, 0.0, rot)
        corners = [f.P(-w / 2 - 0.6, -3.4), f.P(w / 2 + 0.6, -3.4), f.P(-w / 2, d), f.P(w / 2, d)]
        ok = all(clear(c, px, py, 1.6) for px, py, _ in corners) and all(sc.free(px, py, 0.5) for px, py, _ in corners[2:])
        if ok:
            zz = z if z is not None else min(sc.ground(px, py) for px, py, _ in corners[:2]) + 0.05
            special = opts.get("special")
            if special:
                special(m, sc, x, y, zz, rot)
            else:
                building(m, sc, x, y, zz, rot, w, d, seed=seed * 50 + k, **opts)
            out.append((x, y, rot))
        s += w + gap[0] + (gap[1] - gap[0]) * rnd(seed * 13 + k)
        k += 1
    return out


def streets(c, dg):
    """Where the town's streets are along the lap (a course can say: dg.STREETS), and
    how far back from the road's centre the buildings stand."""
    S = dg.SEG
    st = {"main": (S[17] + 4.0 - c.length, S[1] - 6.0), "side": (S[2], S[6]), "main_back": 17.5, "side_back": 15.5,
          "square_back": 9.0 + 5.4, "dress": 12.4, "wagon": S[5] + 20.0}
    st.update(getattr(dg, "STREETS", {}))
    return st


def town(c, sc, dg):
    """Main Street, the square, the saloon district and its side street."""
    S = dg.SEG
    m = Mesh()
    # Main Street: both sides, from behind the grid to the square.
    L = c.length
    west = [
        (20.0, 16.0, {"special": hotel}),
        (10.0, 12.0, {"siding": "siding_green", "sign": "bank", "lit": 0.4}),
        (9.0, 11.0, {"siding": "siding_grey", "sign": "barber", "lit": 0.3}),
        (12.0, 13.0, {"siding": "siding_brown", "sign": "undertaker", "lit": 0.2, "ghost": 0.3}),
        (11.0, 12.0, {"siding": "siding_ochre", "storeys": 2, "balcony": True}),
        (8.0, 10.0, {"siding": "siding_red", "lit": 0.6}),
    ]
    east = [
        (11.0, 12.0, {"special": sheriff}),
        (6.0, 10.0, {"siding": "siding_brown", "lit": 0.3, "false_front": False, "porch": False}),
        (12.0, 13.0, {"siding": "siding_brown", "sign": "assay", "lit": 0.5}),
        (10.0, 12.0, {"siding": "siding_green", "storeys": 2, "balcony": True, "lit": 0.6}),
        (9.0, 11.0, {"siding": "siding_grey", "lit": 0.4, "ghost": 0.2}),
    ]
    # (The route's start is s = 0; Main Street runs from the end of the last corner,
    # through the line, to the square.)
    st = streets(c, dg)
    a0, a1 = st["main"]
    along(c, a0, a1, -1, st["main_back"], west, sc, m, dg, seed=1)
    along(c, a0 + 26.0, a1 + 2.0, 1, st["main_back"], east, sc, m, dg, seed=2)
    # The saloon, on the outside of the corner at the square, facing it.
    cx, cy = dg.SQUARE
    r = dg.LAYOUT[1][1] + st["square_back"]
    a = math.radians(45.0)
    z = sc.ground(cx + math.cos(a) * r, cy + math.sin(a) * r)
    saloon(m, sc, cx + math.cos(a) * r, cy + math.sin(a) * r, z + 0.05, a - math.pi / 2)
    # The saloon district: the commercial streets west from the square.
    north = [
        (16.0, 20.0, {"special": livery}),
        (10.0, 12.0, {"siding": "siding_grey", "storeys": 2, "balcony": True, "lit": 0.5}),
        (8.0, 10.0, {"siding": "siding_red", "lit": 0.4}),
        (11.0, 12.0, {"siding": "siding_ochre", "lit": 0.5, "ghost": 0.15}),
    ]
    south = [
        (18.0, 15.0, {"siding": "siding_ochre", "storeys": 2, "sign": "general", "lit": 0.7, "balcony": False}),
        (9.0, 11.0, {"siding": "siding_brown", "lit": 0.4}),
        (12.0, 12.0, {"siding": "siding_green", "storeys": 2, "balcony": True, "lit": 0.5}),
        (8.0, 10.0, {"siding": "siding_grey", "lit": 0.2, "ghost": 0.25}),
        (10.0, 11.0, {"siding": "siding_red", "lit": 0.5}),
    ]
    b0, b1 = st["side"]
    along(c, b0 - 4.0, b1 - 2.0, 1, st["side_back"], north, sc, m, dg, seed=3)
    along(c, b0 - 2.0, b1 - 6.0, -1, st["side_back"], south, sc, m, dg, seed=4)
    m.build(c, "Town Buildings", "Town", role="both")


def square(c, sc, dg):
    """The town square inside the first corner: a well, a dead tree, a hitching rail and
    a trough, a wagon left standing, benches, a lantern post."""
    cx, cy = dg.SQUARE
    m = Mesh()
    z = sc.ground(cx, cy)
    # The well: a stone ring, a little roof on two posts, a bucket.
    m.add(("masonry", "wall"), lambda bm: loft(bm, [ring(bm, (cx, cy), 1.8, z - 0.5, 10), ring(bm, (cx, cy), 1.8, z + 1.0, 10)], cap_top=False))
    m.add(("gulch_chasm", "wall"), lambda bm: bm.faces.new(ring(bm, (cx, cy), 1.75, z + 0.4, 10)))
    for s in (-1, 1):
        m.add(TIMBER, lambda bm, s=s: cuboid(bm, (cx + s * 1.6, cy, z + 2.0), (0.25, 0.25, 3.0)))
    m.add(("shingle_roof", "wall"), lambda bm: cuboid(bm, (cx, cy, z + 3.6), (4.2, 3.0, 0.2), tilt=(0.0, 0.0)))
    m.build(c, "Town Square", "Town", role="both")
    # The green glow from the well: something down there too.
    sc.green.append((cx, cy, z + 1.0))
    sc.put("Dead Tree 1", cx - 18.0, cy - 14.0, sc.ground(cx - 18.0, cy - 14.0), 0.7, coll="Town Props", role="both")
    sc.put("Hitching Rail", cx + 10.0, cy - 22.0, sc.ground(cx + 10.0, cy - 22.0), 0.3, coll="Town Props", role="both")
    sc.put("Water Trough", cx + 14.0, cy - 16.0, sc.ground(cx + 14.0, cy - 16.0), 0.8, coll="Town Props", role="both")
    sc.put("Wagon Covered", cx - 22.0, cy + 6.0, sc.ground(cx - 22.0, cy + 6.0), 2.0, coll="Town Props", role="both")
    sc.put("Bench", cx + 6.0, cy + 4.0, sc.ground(cx + 6.0, cy + 4.0), 2.4, coll="Town Props", role="both")
    sc.put("Lantern Post", cx + 4.0, cy - 6.0, sc.ground(cx + 4.0, cy - 6.0), 0.3, coll="Town Props", role="both")
    lx, ly, lz = gp.LANTERN_POST_LIGHT
    sc.warm.append((cx + 4.0 + lx * math.cos(0.3), cy - 6.0 + lx * math.sin(0.3), sc.ground(cx + 4.0, cy - 6.0) + lz))
    sc.ghosts.append({"look": "float", "x": cx - 10.0, "y": cy + 2.0, "z": z + 1.0, "heading": 0.0, "period": 19.0, "offset": 9.0})
    sc.wisps.append((cx, cy, z + 2.0, 14.0, 6))
    sc.footprints.append((cx, cy, 30.0))


def street_dressing(c, sc, dg):
    """Along the boardwalks: barrels, crates, benches, wagon wheels against the walls,
    hitching rails and troughs, and the abandoned wagon in the side street."""
    S = dg.SEG
    k = 0
    L = c.length
    st = streets(c, dg)
    for s in list(range(int(st["main"][0]) + 4, int(st["main"][1]) - 2, 9)) + list(range(int(st["side"][0]), int(st["side"][1]) - 4, 8)):
        q = c.at(s % L)
        for side in (-1, 1):
            k += 1
            r = rnd(k * 7 + 3)
            if r < 0.45:
                continue
            nx, ny = (math.sin(road_rot(q)), -math.cos(road_rot(q)))
            off = side * (st["dress"] + 0.6 * rnd(k))
            x, y = q.p.x + nx * off, q.p.y + ny * off
            if not clear(c, x, y, 2.4):
                continue
            proto = ("Barrel 0", "Barrel 1", "Crate Stack 0", "Crate Stack 1", "Hitching Rail", "Water Trough", "Bench", "Wagon Wheel")[k % 8]
            rot = road_rot(q) + (0 if proto in ("Hitching Rail", "Water Trough", "Bench") else rnd(k) * 6.0)
            sc.put(proto, x, y, sc.ground(x, y), rot, coll="Town Props", role="both")
    # The abandoned wagon at the mouth of an alley in the side street, a wheel off.
    q = c.at(st["wagon"])
    nx, ny = math.sin(road_rot(q)), -math.cos(road_rot(q))
    x, y = q.p.x - nx * (st["dress"] + 1.1), q.p.y - ny * (st["dress"] + 1.1)
    sc.put("Wagon Covered Broken", x, y, sc.ground(x, y), road_rot(q) + 0.25, coll="Town Props", role="both")
    sc.footprints.append((x, y, 4.0))


def start_arch(c, sc, dg):
    """The timber arch over the start line: great posts, a double crossbeam with the
    DRY GULCH sign on both faces and GHOST TOWN under it, a cattle skull over the middle,
    lanterns hanging off both ends."""
    q = c.at(3.0)
    rot = road_rot(q)
    m = Mesh()
    half = q.w / 2 + 2.6
    z = q.p.z
    for side in (-1, 1):
        p = q.side(side * half)
        for along_ in (-0.8, 0.8):
            pp = p + q.t * along_
            m.add(TIMBER, lambda bm, pp=pp: cuboid(bm, (pp.x, pp.y, z + 6.5), (0.9, 0.9, 13.5), rot))
        m.add(("masonry", "wall"), lambda bm, p=p: cuboid(bm, (p.x, p.y, z + 0.4), (2.6, 3.4, 1.2), rot))
        a, b = q.side(side * half), q.side(side * (half - 3.0))
        m.add(TIMBER, lambda bm, a=a, b=b: _beam(bm, (a.x, a.y, z + 8.0), (b.x, b.y, z + 11.0), 0.4))
    for dz in (11.0, 12.6):
        a, b = q.side(-half - 1.4), q.side(half + 1.4)
        m.add(TIMBER, lambda bm, a=a, b=b, dz=dz: _beam(bm, (a.x, a.y, z + dz), (b.x, b.y, z + dz), 0.6))
    # The signs: DRY GULCH on both faces, GHOST TOWN under it (facing the grid).
    nx, ny = -q.t.x, -q.t.y
    face_quad(m, ("sign_drygulch", "wall"), q.p.x, q.p.y, nx, ny, 6.5, z + 13.0, z + 15.4, out=0.55)
    face_quad(m, ("sign_drygulch", "wall"), q.p.x, q.p.y, -nx, -ny, 6.5, z + 13.0, z + 15.4, out=0.55)
    face_quad(m, ("sign_ghosttown", "wall"), q.p.x, q.p.y, nx, ny, 4.2, z + 9.6, z + 10.65, out=0.45)
    face_quad(m, ("sign_finish", "wall"), q.p.x, q.p.y, -nx, -ny, 2.6, z + 9.6, z + 10.9, out=0.45)
    for side in (-1, 1):
        a, b = q.side(side * 6.4), q.side(side * 6.4)
        m.add(TIMBER, lambda bm, a=a: _beam(bm, (a.x, a.y, z + 12.6), (a.x, a.y, z + 15.6), 0.25))
    m.build(c, "Start Arch", "Town", role="both")
    sc.put("Cattle Skull", q.p.x - q.t.x * 0.6, q.p.y - q.t.y * 0.6, z + 16.6, rot + math.pi / 2, scale=1.8, coll="Town Props", role="both")
    for side in (-1, 1):
        p = q.side(side * (half - 1.6))
        sc.put("Hanging Lantern", p.x - q.t.x * 0.8, p.y - q.t.y * 0.8, z + 10.6, rot, coll="Town Props", role="both")
        sc.warm.append((p.x, p.y, z + 9.6))
        sc.lanterns.append((p.x - q.t.x * 0.8, p.y - q.t.y * 0.8, z + 9.6))


def back_lanes(c, sc, dg):
    """North of the commercial streets: houses and shacks along the back lanes, the
    windmill, corrals; along the mine approach the backs of buildings, sheds and the
    miners' shacks."""
    m = Mesh()
    k = 0
    spots = []
    bx0, bx1, by0, by1 = getattr(dg, "BACK_LANES", (-200, 40, 232, 400))
    for gx in range(bx0, bx1, 22):
        for gy in range(by0, by1, 24):
            k += 1
            x = gx + 8.0 * (rnd(k * 3) - 0.5)
            y = gy + 8.0 * (rnd(k * 5) - 0.5)
            if rnd(k * 11) < 0.42:
                continue
            spots.append((x, y, k))
    for x, y, k in spots:
        w = 7.0 + 4.0 * rnd(k * 17)
        d = 8.0 + 4.0 * rnd(k * 19)
        if not sc.free(x, y, max(w, d) / 2 + 2.0) or not clear(c, x, y, max(w, d) / 2 + 6.0) or dg.ridge_d(x, y) > -14.0:
            continue
        if math.hypot(x - dg.GRAVEYARD[0], y - dg.GRAVEYARD[1]) < 80:
            continue
        # Face the nearest road.
        smp, _ = c.nearest(x, y)
        rot = math.atan2(smp.p.y - y, smp.p.x - x) + math.pi / 2
        z = sc.ground(x, y) + 0.05
        building(m, sc, x, y, z, rot, w, d, siding=("siding_grey", "siding_brown", "siding_red")[k % 3], false_front=rnd(k * 23) < 0.4,
                 porch=rnd(k * 29) < 0.5, lit=0.25, ghost=0.12, seed=100 + k, roof=("shingle_roof", "tin_roof")[k % 2],
                 lanterns=False)
    m.build(c, "Back Lanes", "Town", role="both")
    # The windmill, on the outskirts towards the graveyard.
    wx, wy, wrd = getattr(dg, "WINDMILL", (-120.0, 395.0, 200.0))
    wz = sc.ground(wx, wy)
    wr = math.radians(wrd)
    cp.windmill_tower(c)
    sc.put("Windmill Tower", wx, wy, wz, wr, coll="Town Props", role="both")
    sc.windmill = (wx, wy, wz + 14.6, wr)
    sc.footprints.append((wx, wy, 5.0))


def graveyard(c, sc, dg):
    """Boot Hill: the cemetery on its knoll inside Graveyard Bend. An iron fence and gate,
    rows of headstones and wooden crosses (tilted, half sunk), three crypts, twisted dead
    trees against the moon, green mist low over the graves."""
    gx, gy = dg.GRAVEYARD
    R = 42.0
    m = Mesh()
    # The fence: a ring of iron fence runs (a gap for the gate, facing town).
    n = 36
    gate_a = getattr(dg, "GRAVE_GATE", math.atan2(-1.0, 0.6))
    # Where the lap runs right through it, nothing stands in the road.
    through = getattr(dg, "GRAVE_THROUGH", False)
    for k in range(n):
        a0, a1 = k * math.tau / n, (k + 1) * math.tau / n
        am = (a0 + a1) / 2
        if abs(((am - gate_a + math.pi) % math.tau) - math.pi) < 0.08:
            continue
        x, y = gx + math.cos(am) * R, gy + math.sin(am) * R
        if not clear(c, x, y, 3.0):
            continue
        L = 2 * R * math.sin(math.pi / n)
        sc.put("Iron Fence 10", x, y, sc.ground(x, y), am + math.pi / 2, scale=(L / 10.0 * 1.02, 1.0, 1.0), coll="Graveyard")
    x, y = gx + math.cos(gate_a) * R, gy + math.sin(gate_a) * R
    sc.put("Cemetery Gate", x, y, sc.ground(x, y), gate_a + math.pi / 2, coll="Graveyard")
    # Rows of graves, all facing the gate's side, each a little skewed.
    k = 0
    for row in range(-6, 7):
        for col in range(-9, 10):
            k += 1
            u, v = col * 3.8 + 1.2 * (rnd(k * 3) - 0.5), row * 5.0 + 0.8 * (rnd(k * 5) - 0.5)
            x, y = gx + u * math.cos(gate_a + math.pi / 2) - v * math.sin(gate_a + math.pi / 2), gy + u * math.sin(gate_a + math.pi / 2) + v * math.cos(gate_a + math.pi / 2)
            if math.hypot(x - gx, y - gy) > R - 5 or rnd(k * 7) < 0.22:
                continue
            if any(math.hypot(x - px, y - py) < 7 for px, py in CRYPTS_AT(gx, gy)) or abs(u) < 3.0:
                continue
            if through and not clear(c, x, y, 1.6):
                continue
            proto = "Grave Cross %d" % (k % 3) if rnd(k * 13) < 0.35 else "Headstone %d" % (k % 6)
            sc.put(proto, x, y, sc.ground(x, y) - 0.15 * rnd(k * 17), gate_a + math.pi / 2 + 0.2 * (rnd(k * 19) - 0.5) - math.pi / 2,
                   scale=1.35 + 0.3 * rnd(k * 23), coll="Graveyard")
    for i, (x, y) in enumerate(CRYPTS_AT(gx, gy)):
        if through and not clear(c, x, y, 4.5):
            continue
        sc.put("Crypt %d" % (i % 2), x, y, sc.ground(x, y), gate_a - math.pi / 2 + (i - 1) * 0.5, scale=1.5, coll="Graveyard")
        sc.footprints.append((x, y, 4.0))
    for i, (dx, dy, v) in enumerate(((-18, 14, 1), (21, -8, 3), (6, 24, 0), (-24, -18, 2))):
        x, y = gx + dx, gy + dy
        if through and not clear(c, x, y, 3.0):
            continue
        sc.put("Dead Tree %d" % v, x, y, sc.ground(x, y), i * 1.7, scale=1.3, coll="Graveyard")
    # Green lanterns at the gate, and the light of the mist.
    for s in (-1, 1):
        a = gate_a + s * 0.07
        x, y = gx + math.cos(a) * (R + 1.0), gy + math.sin(a) * (R + 1.0)
        sc.put("Lantern Post Green", x, y, sc.ground(x, y), gate_a + s * 1.2, coll="Graveyard")
        sc.green.append((x, y, sc.ground(x, y) + 3.5))
    for k in range(10):
        a = gate_a + 0.6 + k * (math.tau - 1.2) / 9
        x, y = gx + math.cos(a) * (R + 1.5), gy + math.sin(a) * (R + 1.5)
        if clear(c, x, y, 2.0):
            sc.put("Lantern Post Green", x, y, sc.ground(x, y), a, coll="Graveyard")
            sc.green.append((x + math.cos(a) * 1.1, y + math.sin(a) * 1.1, sc.ground(x, y) + 3.5))
    # Boot Hill's overflow: old graves scattered on the outside of the bend too, so the
    # road runs right through the cemetery.
    if hasattr(dg, "GRAVE_STRETCH"):
        g0, g1, gside = dg.GRAVE_STRETCH
    else:
        sg_ = dg.LAYOUT[6]
        g0, g1, gside = dg.SEG[6], dg.SEG[6] + sg_[1] * math.radians(sg_[2]), -1
    for k in range(70):
        q = c.at(g0 + (g1 - g0) * rnd(k * 7 + 1))
        sd = gside if gside else (1 if k % 2 else -1)
        p = q.side(sd * (q.w / 2 + 5.0 + 16.0 * rnd(k * 11 + 2)))
        if clear(c, p.x, p.y, 3.5) and sc.free(p.x, p.y, 1.0):
            proto = "Grave Cross %d" % (k % 3) if rnd(k * 13) < 0.5 else "Headstone %d" % (k % 6)
            sc.put(proto, p.x, p.y, sc.ground(p.x, p.y) - 0.1, road_rot(q) + math.pi / 2 + 0.4 * (rnd(k * 5) - 0.5), scale=1.3, coll="Graveyard")
    # Dead trees round the outside of the bend, black against the moon.
    for k in range(9):
        q = c.at(g0 + (g1 - g0) * (k + 0.5) / 9)
        sd = gside if gside else (1 if k % 2 else -1)
        p = q.side(sd * (q.w / 2 + 9.0 + 6.0 * rnd(k * 3)))
        if clear(c, p.x, p.y, 4.0):
            sc.put("Dead Tree %d" % (k % 4), p.x, p.y, sc.ground(p.x, p.y), k * 1.3, scale=1.2 + 0.4 * rnd(k), coll="Graveyard")
    sc.green.append((gx, gy, sc.ground(gx, gy) + 2.0))
    sc.mist.append((gx, gy, sc.ground(gx, gy), R * 0.9, 20))
    sc.wisps.append((gx, gy, sc.ground(gx, gy) + 2.5, R * 0.8, 10))
    for i, (dx, dy) in enumerate(((-15, 8), (12, -18), (20, 20), (-8, -28))):
        x, y = gx + dx, gy + dy
        sc.ghosts.append({"look": "float", "x": x, "y": y, "z": sc.ground(x, y) + 0.8, "heading": 0.0, "period": 13.0 + i * 3.0,
                          "offset": i * 4.0})
    sc.whispers.append((gx, gy, sc.ground(gx, gy) + 2.0, 90.0))
    sc.footprints.append((gx, gy, R + 2.0))
    m.build(c, "Graveyard", "Graveyard")


def CRYPTS_AT(gx, gy):
    return [(gx - 20.0, gy + 20.0), (gx + 24.0, gy + 10.0), (gx - 3.0, gy + 30.0)]


def chapel_and_tower(c, sc, dg):
    m = Mesh()
    cx, cy = dg.CHAPEL
    z = sc.ground(cx, cy)
    chapel(m, sc, cx, cy, z + 0.05, math.radians(-25.0))
    m.build(c, "Chapel", "Town", role="both")
    # A few old graves round it.
    for k in range(6):
        x, y = cx + 14.0 + 3.0 * k * 0.7, cy - 8.0 + 4.0 * (k % 3)
        if clear(c, x, y, 3.0) and sc.free(x, y, 1.0):
            sc.put("Grave Cross %d" % (k % 3), x, y, sc.ground(x, y), math.radians(-25.0), coll="Town Props", role="both")
    wx, wy = dg.WATER_TOWER
    water_tower(c, sc, wx, wy, sc.ground(wx, wy))


# ------------------------------------------------------------------ the mineworks


def mine_portal(c, sc, dg):
    """The Hazard Mine's portal in the ridge's north face: the great timber frame, the
    HAZARD MINE sign, lanterns either side, KEEP OUT nailed up, chains hanging, rails
    running in, a cart left standing, the green glow pouring out."""
    line = c.mine
    i = dg.mine_index(line, dg.PORTAL_AT)
    p, q = line[i], line[i + 3]
    head = math.atan2(q[1] - p[1], q[0] - p[0])
    rot = head - math.pi / 2  # the frame's X across the tunnel, facing back out (-Y)
    gp.mine_portal(c)
    # Set it a little outside the rock's face.
    px, py = p[0] - math.cos(head) * 3.0, p[1] - math.sin(head) * 3.0
    sc.put("Mine Portal", px, py, p[2], rot, coll="Mineworks", role="both")
    m = Mesh()
    nx, ny = -math.cos(head), -math.sin(head)
    face_quad(m, ("sign_hazard", "wall"), px, py, nx, ny, 5.6, p[2] + 11.0, p[2] + 13.1, out=1.2)
    face_quad(m, ("sign_keepout", "wall"), px + math.cos(rot) * 5.2, py + math.sin(rot) * 5.2, nx, ny, 1.4, p[2] + 2.6, p[2] + 3.3, out=1.1)
    m.build(c, "Mine Signs", "Mineworks")
    for s in (-1, 1):
        x, y = px + math.cos(rot) * s * 9.2 + nx * 1.4, py + math.sin(rot) * s * 9.2 + ny * 1.4
        sc.put("Hanging Lantern", x, y, p[2] + 7.6, rot, coll="Mineworks")
        sc.warm.append((x, y, p[2] + 6.8))
        sc.lanterns.append((x, y, p[2] + 6.8))
    for s, L in ((-0.4, 3.0), (0.3, 5.0)):
        sc.put("Chain %.0f" % L, px + math.cos(rot) * s * 10.0, py + math.sin(rot) * s * 10.0, p[2] + 9.6, rot, coll="Mineworks")
    # The glow pouring out: veils of green light hanging in the tunnel's mouth, one behind
    # another, and crystals breaking out of the rock round it.
    m2 = Mesh()
    for k, depth in enumerate((5.0, 11.0, 18.0)):
        face_quad(m2, ("spectral_mist", "wall"), px - nx * depth, py - ny * depth, nx, ny, 6.2 - k * 0.4, p[2] - 0.2 - depth * 0.08,
                  p[2] + 8.6 - depth * 0.08, out=0.0)
    m2.build(c, "Mine Glow", "Mineworks")
    for s_, sc_ in ((-1, 1.3), (1, 1.0)):
        x, y = px + math.cos(rot) * s_ * 8.6 - nx * 0.5, py + math.sin(rot) * s_ * 8.6 - ny * 0.5
        sc.put("Spectral Crystals %d" % (1 if s_ > 0 else 2), x, y, p[2] - 0.5, head + s_ * 0.8, scale=sc_, coll="Mineworks")
    sc.green += [(px - nx * 6, py - ny * 6, p[2] + 4.0), (px - nx * 18, py - ny * 18, p[2] + 4.0), (px + nx * 3, py + ny * 3, p[2] + 2.0)]
    sc.mist.append((px - nx * 2, py - ny * 2, p[2], 9.0, 6))
    sc.whispers.append((px, py, p[2] + 3.0, 45.0))
    # A cart and an ore heap by the portal, off the road.
    for side, proto in ((1, "Ore Cart Glow"), (-1, "Ore Heap 1")):
        x, y = px + math.cos(rot) * side * 12.5 + nx * 4.0, py + math.sin(rot) * side * 12.5 + ny * 4.0
        sc.put(proto, x, y, sc.ground(x, y), head, coll="Mineworks")
    sc.portal = (px, py, p[2], head)


def headframe(c, sc, dg):
    """The headframe over the old shaft on the ridge's north rim: a tall timber A-frame,
    its sheave wheel, an ore bin, and a chute running down the cliff."""
    x, y, z = getattr(dg, "HEADFRAME", (150.0, 352.0, 66.0))
    m = Mesh()
    H = 18.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.add(("mine_timber", "wall"), lambda bm, sx=sx, sy=sy: _beam(bm, (x + sx * 4.5, y + sy * 4.5, z - 2), (x + sx * 1.2, y + sy * 1.2, z + H), 0.6))
        m.add(("mine_timber", "wall"), lambda bm, sx=sx: _beam(bm, (x + sx * 1.2, y - 11.0, z - 2), (x + sx * 1.2, y + 0.5, z + H - 1), 0.5))
    for h in (5.0, 10.0, 14.0):
        k = 1 - h / H * 0.75
        for sx, sy, tx, ty in ((-1, -1, 1, -1), (1, -1, 1, 1), (1, 1, -1, 1), (-1, 1, -1, -1)):
            m.add(("mine_timber", "wall"), lambda bm, sx=sx, sy=sy, tx=tx, ty=ty, h=h, k=k: _beam(bm, (x + sx * 4.5 * k, y + sy * 4.5 * k, z + h), (x + tx * 4.5 * k, y + ty * 4.5 * k, z + h), 0.3))
    # The sheave wheel at the top.
    m.add(("iron", "wall"), lambda bm: gp._wheel(bm, x, y, z + H + 1.4, 2.4, axis_x=True))
    # The ore bin and the chute down the cliff toward the chasm.
    m.add(("mine_timber", "wall"), lambda bm: cuboid(bm, (x, y + 9.0, z + 4.0), (7.0, 6.0, 6.0)))
    m.add(("tin_roof", "wall"), lambda bm: cuboid(bm, (x, y + 9.0, z + 7.3), (8.0, 7.0, 0.3), tilt=(0.15, 0.0)))
    for k in range(6):
        y0 = y + 12.0 + k * 6.0
        m.add(("mine_timber", "wall"), lambda bm, y0=y0, k=k: _beam(bm, (x, y0, z + 2.0 - k * 5.0), (x, y0 + 6.0, z - 3.0 - k * 5.0), 2.0, 0.4))
    m.build(c, "Headframe", "Mineworks", role="both")
    sc.put("Hanging Lantern", x + 1.5, y - 1.5, z + 12.0, coll="Mineworks")
    sc.warm.append((x + 1.5, y - 1.5, z + 11.0))
    sc.green.append((x, y, z + 1.0))


def railway(c, sc, dg):
    """The mine railway: out of the ridge's south adit, along the edge of town and over
    the road on a tall timber trestle to the stamp mill. Rails on sleepers all the way,
    an ore cart that rolls along it now and then by itself."""
    S = dg.SEG
    rw = getattr(dg, "RAILWAY", {})
    adit = rw.get("adit", (128.0, 96.0))
    # Where the road climbs out of the ravine: the trestle crosses it here.
    q = c.at(rw.get("cross", S[15] + 60.0))
    cross = (q.p.x, q.p.y)
    mill = (cross[0] - 4.0, cross[1] - 95.0)
    pts = [adit, rw.get("via", (130.0, 40.0)), (cross[0] + 2.0, cross[1] + 45.0), (cross[0], cross[1] - 6.0), (mill[0] + 2.0, mill[1] + 20.0), mill]
    dense = []
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(math.dist(a, b) / 2.0))
        for k in range(n):
            dense.append((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n))
    dense.append(pts[-1])
    deck = dg.Z_TOWN + 1.6
    m = Mesh()
    rail_pts = []
    for i, (x, y) in enumerate(dense):
        g = sc.ground(x, y)
        a = dense[max(0, i - 1)]
        b = dense[min(len(dense) - 1, i + 1)]
        h = math.atan2(b[1] - a[1], b[0] - a[0])
        z = max(deck, g + 0.4)
        rail_pts.append((x, y, z + 0.35))
        m.add(TIMBER, lambda bm, x=x, y=y, z=z, h=h: cuboid(bm, (x, y, z + 0.12), (0.3, 2.6, 0.22), h))
        if z - g > 1.2 and i % 3 == 0:
            # A trestle bent: four legs splayed, braced.
            rx, ry = -math.sin(h), math.cos(h)
            for o in (-1, 1):
                m.add(TIMBER, lambda bm, x=x, y=y, z=z, g=g, o=o, rx=rx, ry=ry: _beam(bm, (x + rx * o * (1.4 + (z - g) * 0.12), y + ry * o * (1.4 + (z - g) * 0.12), g - 0.5), (x + rx * o * 1.0, y + ry * o * 1.0, z), 0.4))
            m.add(TIMBER, lambda bm, x=x, y=y, z=z, rx=rx, ry=ry: _beam(bm, (x - rx * 1.6, y - ry * 1.6, z - 0.1), (x + rx * 1.6, y + ry * 1.6, z - 0.1), 0.35))
            for lv in range(1, int((z - g) / 4.0) + 1):
                zz = z - lv * 4.0
                spread = 1.0 + (z - zz) * 0.12
                m.add(TIMBER, lambda bm, x=x, y=y, zz=zz, rx=rx, ry=ry, spread=spread: _beam(bm, (x - rx * spread, y - ry * spread, zz), (x + rx * spread, y + ry * spread, zz), 0.25))
                m.add(TIMBER, lambda bm, x=x, y=y, zz=zz, rx=rx, ry=ry, spread=spread: _beam(bm, (x - rx * spread, y - ry * spread, zz), (x + rx * (spread - 0.5), y + ry * (spread - 0.5), zz + 4.0), 0.18))
    for o in (-0.75, 0.75):
        for (x0, y0, z0), (x1, y1, z1) in zip(rail_pts, rail_pts[1:]):
            h = math.atan2(y1 - y0, x1 - x0)
            rx, ry = -math.sin(h) * o, math.cos(h) * o
            m.add(("rail_iron", "wall"), lambda bm, x0=x0, y0=y0, z0=z0, x1=x1, y1=y1, z1=z1, rx=rx, ry=ry: _beam(bm, (x0 + rx, y0 + ry, z0), (x1 + rx, y1 + ry, z1), 0.14, 0.16))
    m.build(c, "Mine Railway", "Mineworks")
    sc.railway = rail_pts
    # The adit it comes out of: a small portal in the ridge's south face.
    sc.put("Mine Portal", adit[0], adit[1] + 2.0, deck - 0.3, math.radians(0.0), scale=0.55, coll="Mineworks")
    sc.green.append((adit[0], adit[1] + 4.0, deck + 2.0))
    stamp_mill(c, sc, dg, mill)


def stamp_mill(c, sc, dg, at):
    """The stamp mill: a big stepped timber building down the hillside, its roofs one
    over another, a tall iron stack, green light in its windows."""
    x, y = at
    z = sc.ground(x, y)
    m = Mesh()
    for k, (w, d, h, dy) in enumerate(((22.0, 12.0, 9.0, 0.0), (18.0, 12.0, 8.0, -10.0), (14.0, 10.0, 7.0, -19.0))):
        zz = z - k * 3.5
        f = Frame(x, y + dy, zz, 0.0)
        m.add(("siding_grey", "wall"), lambda bm, f=f, w=w, d=d, h=h: cuboid(bm, f.P(0, -d / 2, h / 2 - 1.0), (w, d, h + 2.0), 0.0))
        m.add(("tin_roof", "wall"), lambda bm, f=f, w=w, d=d, h=h: cuboid(bm, f.P(0, -d / 2, h + 0.9), (w + 1.0, d + 1.0, 0.3), 0.0, tilt=(-0.25, 0.0)))
        for u in range(int(w / 4)):
            window(m, f, sc, -w / 2 + 2.0 + u * 4.0, -d, 0, -1, zz + h * 0.45, "ghost" if (u + k) % 3 == 0 else "dark", frame=False)
    m.add(("iron", "wall"), lambda bm: _cyl(bm, x + 8.0, y + 3.0, z, z + 26.0, 0.9, 0.75, n=8))
    m.build(c, "Stamp Mill", "Mineworks", role="both")
    sc.footprints.append((x, y - 10.0, 18.0))


def mine_approach(c, sc, dg):
    """Along the mine approach: ore bins, sheds, crates, a winch, lantern posts."""
    S = dg.SEG
    m = Mesh()
    a0, a1 = getattr(dg, "APPROACH", (S[7] + 200, S[8] - 10))
    for k, s in enumerate(range(int(a0), int(a1), 28)):
        q = c.at(s)
        nx, ny = math.sin(road_rot(q)), -math.cos(road_rot(q))
        x, y = q.p.x - nx * 20.0, q.p.y - ny * 20.0
        if clear(c, x, y, 7.0) and sc.free(x, y, 5.0) and dg.ridge_d(x, y) < -6.0:
            building(m, sc, x, y, sc.ground(x, y) + 0.05, road_rot(q), 8.0, 7.0, siding="siding_grey", false_front=False, porch=False,
                     roof="tin_roof", lit=0.3, ghost=0.2, seed=300 + k, lanterns=False)
    m.build(c, "Mine Sheds", "Mineworks", role="both")
    for k, (dx, dy, proto) in enumerate(getattr(dg, "APPROACH_PROPS", ((20.0, 450.0, "Winch"), (-6.0, 452.0, "Ore Heap 0"), (32.0, 448.0, "Crate Stack 1"),
                                                                       (52.0, 446.0, "Ore Cart Tipped")))):
        if clear(c, dx, dy, 3.0):
            sc.put(proto, dx, dy, sc.ground(dx, dy), k * 1.3, coll="Mineworks")
