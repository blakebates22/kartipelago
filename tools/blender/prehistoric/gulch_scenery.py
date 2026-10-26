# Dry Gulch Ghost Town's scenery (see dry_gulch.py): the land near and far, Hazard Ridge
# and the haunted mine bored through it (tunnels, the old workings, the chasm cavern),
# the trestles, the ravine's glowing fissures, the light (moonlight, lanterns and the
# spectral green), and the gameplay entities. The town itself is gulch_town.py; the
# props are gulch_props.py.
# SPDX-License-Identifier: MIT

import math

import canyon_props as cp
import course_kit as kit
import gulch_props as gp
from course_kit import Vector, bmesh, lerp, materials, rnd
from props import blob, cuboid, loft, ring

NEAR = (-440.0, 440.0, -300.0, 640.0)
FAR = (-2800.0, 2800.0, -2400.0, 2800.0)
COLL = "Town"


class Mesh:
    """One mesh built from many pieces, each with its own material. Pieces added with
    `uv=True` carry their own UVs (made while building), which are kept as they are."""

    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new("UVMap")
        self.slots = {}
        self.raw = {}

    def add(self, mat, make, uv=False):
        k0 = len(self.bm.faces)
        make(self.bm)
        self.bm.faces.ensure_lookup_table()
        (self.raw if uv else self.slots).setdefault(mat, []).extend(range(k0, len(self.bm.faces)))

    def quad(self, mat, pts, uvs):
        """One quad (or triangle) with its own UVs."""
        def make(bm):
            f = bm.faces.new([bm.verts.new(p) for p in pts])
            for loop, uv in zip(f.loops, uvs):
                loop[self.uv].uv = uv

        self.add(mat, make, uv=True)

    def build(self, c, name, coll=COLL, role="visual", flat=True):
        if not self.bm.faces:
            self.bm.free()
            return None
        ob = c.mesh_object(name, self.bm, coll, role)
        for mat, faces in self.slots.items():
            c.assign(ob, c.lib(*mat), faces)
        me = ob.data
        for mat, faces in self.raw.items():
            m = c.lib(*mat)
            names = [x.name if x else None for x in me.materials]
            if m.name in names:
                slot = names.index(m.name)
            else:
                me.materials.append(m)
                slot = len(me.materials) - 1
            for i in faces:
                me.polygons[i].material_index = slot
            materials.keep_uvs(ob, faces)
        materials.ensure_paint(me)
        if flat:
            me.shade_flat()
        return ob


def game_entity(c, kind, x, y, z, **extra):
    gx, gy, gz = c.game(x, y, z)
    c.entity(kind, x=gx, y=gy, z=gz, **extra)


def road_rot(q):
    return math.atan2(q.t.y, q.t.x)


def clear(c, x, y, margin):
    """Far enough from the race line and the shortcut."""
    smp, d = c.nearest(x, y)
    if d <= smp.w / 2 + margin:
        return False
    return all((q.p.x - x) ** 2 + (q.p.y - y) ** 2 > (q.w / 2 + margin) ** 2 for q in c.extra_ground)


class Scene:
    """What the scenery builders share."""

    def __init__(self, c, dg):
        self.c = c
        self.dg = dg
        self.warm = []  # lantern light points (x, y, z): warm glow painted round them
        self.green = []  # spectral light points: green glow painted round them
        self.lanterns = []  # (x, y, z) for lantern entities (the light near the camera)
        self.ghosts = []  # ghost entities: dicts
        self.doors = []  # saloon doors: (x, y, z, heading)
        self.footprints = []  # (x, y, r) of buildings, to keep scatter clear
        self.ground_obs = []
        self.wisps = []  # (x, y, z, radius, count): glowing green motes drifting
        self.mist = []  # (x, y, z, radius, rate): green mist low over the ground
        self.whispers = []  # (x, y, z, radius): ghostly whispering when you're near
        self.creaks = []  # (x, y, z, radius): old timber creaking as you cross
        self.adits = []

    def put(self, proto, x, y, z, rot=0.0, scale=1.0, coll="Props", role="visual"):
        return self.c.place(proto, x, y, z, rot, scale, coll=coll, role=role)

    def ground(self, x, y):
        z = self.c.ground_z(x, y, self.ground_obs)
        return z if z is not None else self.dg.natural(x, y)

    def free(self, x, y, r):
        return all(math.hypot(x - fx, y - fy) > r + fr for fx, fy, fr in self.footprints)


# ------------------------------------------------------------------ the land


# (x, y, (radius x, radius y), top) — big flat-topped mesas far off, all round.
FAR_MESAS = [
    (-1000.0, 900.0, (280.0, 170.0), 150.0),
    (-250.0, 1150.0, (300.0, 150.0), 170.0),
    (650.0, 1100.0, (260.0, 180.0), 160.0),
    (1300.0, 500.0, (200.0, 280.0), 185.0),
    (1250.0, -400.0, (200.0, 300.0), 170.0),
    (700.0, -1100.0, (300.0, 160.0), 180.0),
    (-150.0, -1200.0, (280.0, 150.0), 160.0),
    (-900.0, -800.0, (240.0, 180.0), 175.0),
    (-1600.0, -200.0, (300.0, 180.0), 165.0),
    (-1500.0, 700.0, (260.0, 220.0), 180.0),
    (850.0, 300.0, (80.0, 120.0), 115.0),
    (-700.0, 350.0, (70.0, 60.0), 95.0),
]


def far_natural(dg):
    def f(x, y):
        h = dg.natural(x, y)
        for (mx, my, r, top) in FAR_MESAS:
            d = math.hypot((x - mx) / r[0], (y - my) / r[1])
            if d < 1.25:
                edge = 1.0 + 0.08 * math.sin(math.atan2(y - my, x - mx) * 5 + mx)
                k = kit.smooth(max(0.0, min(1.0, (edge - d) / 0.12)))
                h = max(h, lerp(h, top, k))
        return h

    return f


def near(dg):
    return getattr(dg, "NEAR", NEAR)


def land(c, dg, sc):
    X0, X1, Y0, Y1 = near(dg)
    ter = c.terrain("Land", X0, X1, Y0, Y1, 5.0, dg.natural, dg.classify, near=9.0, fade=6.0)
    sc.ground_obs = [ter]
    nat = far_natural(dg)

    def far_classify(cen, n, info):
        if X0 + 22 < cen.x < X1 - 22 and Y0 + 22 < cen.y < Y1 - 22:
            return None
        if n.z < 0.55:
            return (dg.layer(cen.z), "wall")
        if n.z < 0.8:
            return ("gulch_talus", "loose_sand")
        if cen.z < 0.0:
            return ("gulch_chasm", "wall")
        return (dg.ground_mat(cen.x, cen.y), "loose_sand")

    def nat_far(x, y):
        dx = max(X0 - x, x - X1, 0.0)
        dy = max(Y0 - y, y - Y1, 0.0)
        d = max(dx, dy)
        return nat(x, y) - (1.5 * (1.0 - min(1.0, d / 45.0)) if d > 0 or (X0 <= x <= X1 and Y0 <= y <= Y1) else 0.0)

    fx0, fx1, fy0, fy1 = FAR
    far = c.terrain("Far Land", fx0, fx1, fy0, fy1, 36.0, nat_far, far_classify, near=0.0, fade=1.0)
    far["kp_role"] = "visual"

    def under(x, y):
        if c.nearest(x, y)[1] > 70:
            return None
        h = dg.underfloor_z(x, y)
        if h is None:
            return None
        nt = dg.natural(x, y)
        w, z = c.road_height(x, y, 9.0, 6.0, 0.2, nt)
        return min(h, lerp(nt, z, w) - 0.6)

    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 5.0, under, c.lib("gulch_sand", "loose_sand"))
    c.underfloor_flat("Chasm Floor", X0, X1, Y0, Y1, 6.0, dg.abyss_z, c.lib("gulch_chasm", "abyss"))
    return ter


# ------------------------------------------------------------------ Hazard Ridge


RIDGE_BANDS = [  # (height, inset metres): the foot, a talus skirt, sheer walls, ledges, the caprock
    (-38.0, -1.0), (20.0, 0.0), (31.0, 1.6), (37.0, 2.4), (42.0, 5.0), (55.0, 6.0), (58.0, 8.8), (68.0, 9.6), (72.0, 12.0),
]


def ridge_mass(c, dg):
    """Hazard Ridge: its footprint inset in layered steps up to the caprock, the cliffs
    fluted and lumpy, the top a low dome."""
    outline = dg.RIDGE
    cx, cy = dg.RIDGE_C
    n = len(outline)
    bm = bmesh.new()
    rings = []
    for lvl, (z, inset) in enumerate(RIDGE_BANDS):
        ring_ = []
        for i, (x, y) in enumerate(outline):
            dx, dy = x - cx, y - cy
            L = math.hypot(dx, dy) or 1.0
            wob = 3.2 * math.sin(i * 0.37 + lvl * 1.3) + 1.8 * math.sin(i * 1.1 + lvl * 0.7) + 1.2 * math.sin(i * 2.9 + lvl) + 1.0 * (rnd(i * 11 + lvl * 3) - 0.5)
            k = inset + (wob if lvl > 0 else 0.0)
            zz = z + (0.6 * math.sin(i * 1.7 + lvl) if 0 < lvl < len(RIDGE_BANDS) - 1 else 0.0)
            ring_.append(bm.verts.new((x - dx / L * k, y - dy / L * k, zz)))
        rings.append(ring_)
    loft(bm, rings, cap_top=False, cap_bottom=True)
    top = rings[-1]
    cv = bm.verts.new((cx, cy, dg.Z_RIDGE + 2.5))
    for i in range(n):
        bm.faces.new((top[i], top[(i + 1) % n], cv))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = c.mesh_object("Hazard Ridge", bm, "Ridge", "both")
    return ob


def white_paint(ob):
    """Booleans leave the new faces' vertex paint black: start every corner white again."""
    materials.ensure_paint(ob.data)
    for attr in ob.data.color_attributes:
        for d in attr.data:
            d.color = (1.0, 1.0, 1.0, 1.0)


def cut(c, solid, cutter):
    mod = solid.modifiers.new("Cut", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
    mod.object = cutter
    kit.bpy.context.view_layer.objects.active = solid
    kit.bpy.ops.object.modifier_apply(modifier=mod.name)
    kit.bpy.data.objects.remove(cutter)


def path_cutter(c, pts, half, z0, z1, name="Bore"):
    """A closed prism along a polyline of (x, y, z_floor) points: a tunnel's bore."""
    bm = bmesh.new()
    rings = []
    n = len(pts)
    for i, p in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        t = Vector((b[0] - a[0], b[1] - a[1], 0)).normalized()
        r = Vector((t.y, -t.x, 0))
        o = Vector((p[0], p[1], 0))
        hw = half(i / (n - 1)) if callable(half) else half
        zf = p[2]
        rings.append([bm.verts.new(o + r * u + Vector((0, 0, zf + dz))) for u, dz in
                      ((-hw, z0), (hw, z0), (hw, z1 * 0.72), (hw * 0.7, z1), (-hw * 0.7, z1), (-hw, z1 * 0.72))])
    for lo, hi in zip(rings, rings[1:]):
        for k in range(6):
            bm.faces.new((lo[k], lo[(k + 1) % 6], hi[(k + 1) % 6], hi[k]))
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return c.mesh_object(name, bm, "Ridge", "visual")


def cave_cutter(c, cx, cy, heading, length, width, floor, height, slope=0.0, n=20, seed=0, name="Cave"):
    """A rough cave: an elliptical chamber (length along `heading`, width across), its
    floor flat (rising by `slope` per metre along it), walls bulging, a domed roof."""
    bm = bmesh.new()
    ca, sa = math.cos(heading), math.sin(heading)
    levels = [(0.0, 1.0), (0.18, 1.06), (0.5, 1.08), (0.72, 1.0), (0.88, 0.7), (1.0, 0.3)]
    rings = []
    for lvl, (f, k) in enumerate(levels):
        ring_ = []
        for i in range(n):
            a = i * math.tau / n
            wob = 1.0 + 0.08 * math.sin(3 * a + seed + lvl) + 0.05 * math.sin(7 * a + seed * 2)
            u = math.cos(a) * length / 2 * k * wob
            v = math.sin(a) * width / 2 * k * wob
            z = floor + slope * u + f * height
            ring_.append(bm.verts.new((cx + u * ca - v * sa, cy + u * sa + v * ca, z - (0.6 if lvl == 0 else 0.0))))
        rings.append(ring_)
    loft(bm, rings, cap_top=True, cap_bottom=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return c.mesh_object(name, bm, "Ridge", "visual")


def mine_cut(c, dg, sc, ridge):
    """Bore the mine through the ridge: the tunnels along the shortcut, the old workings'
    chamber with the cart crossing's side tunnel through it, and the great cavern over
    the chasm."""
    line = c.mine
    i_portal = dg.mine_index(line, dg.PORTAL_AT)
    i_gate = dg.mine_index(line, dg.GATEWAY_AT)
    i_d0 = dg.mine_index(line, 8)
    i_d3 = dg.mine_index(line, 11)
    # The tunnels: from outside the portal to the cavern, and from the cavern out of the
    # gateway (each runs a little into the cavern so the two meet cleanly).
    for a, b, name in ((i_portal - 18, i_d0 + 18, "Bore In"), (i_d3 - 18, i_gate + 18, "Bore Out")):
        pts = [(p[0], p[1], p[2]) for p in line[max(0, a):min(len(line), b) + 1:2]]
        cut(c, ridge, path_cutter(c, pts, 6.6, -0.3, 9.0, name))
    # The old workings: a broad chamber along the road.
    i_b = dg.mine_index(line, dg.CART_AT)
    q = line[i_b]
    a, b = line[i_b - 6], line[i_b + 6]
    head = math.atan2(b[1] - a[1], b[0] - a[0])
    slope = (b[2] - a[2]) / max(1.0, math.dist(a[:2], b[:2]))
    cut(c, ridge, cave_cutter(c, q[0], q[1], head, 54.0, 34.0, q[2] - 0.3, 15.0, slope, seed=2, name="Workings"))
    # The cart's tunnel, straight across the road through the chamber.
    rx, ry = math.cos(head - math.pi / 2), math.sin(head - math.pi / 2)
    side = [(q[0] + rx * u, q[1] + ry * u, q[2]) for u in range(-46, 47, 4)]
    cut(c, ridge, path_cutter(c, side, 3.0, -0.3, 5.2, "Cart Tunnel"))
    sc.cart = (q[0], q[1], q[2], head)
    # The chasm cavern: from far below the trestle up to a high roof.
    cx, cy = dg.CAVERN
    a, b = line[i_d0], line[i_d3]
    head = math.atan2(b[1] - a[1], b[0] - a[0])
    cut(c, ridge, cave_cutter(c, cx, cy, head, 104.0, 76.0, -31.0, 66.0, 0.0, n=28, seed=5, name="Chasm Cavern"))
    white_paint(ridge)


_MINE_TREE = {}


def in_mine(c, dg, x, y, z):
    """Is (x, y, z) inside the mine (a tunnel, the workings, the cavern)?"""
    bx0, bx1, by0, by1 = getattr(dg, "MINE_BOX", (30.0, 260.0, 70.0, 420.0))
    if not (bx0 < x < bx1 and by0 < y < by1) or z > 44.0:
        return False
    cx, cy = dg.CAVERN
    if ((x - cx) / 50.0) ** 2 + ((y - cy) / 50.0) ** 2 < 1.0 and z < 42.0:
        return True
    wx, wy = dg.WORKINGS
    if math.hypot(x - wx, y - wy) < 50.0 and z < dg.MINE[dg.CART_AT][2] + 17:
        return True
    tree = _MINE_TREE.get(id(c.mine))
    if tree is None:
        tree = kit.kdtree.KDTree(len(c.mine))
        for i, p in enumerate(c.mine):
            tree.insert(Vector((p[0], p[1], 0.0)), i)
        tree.balance()
        _MINE_TREE.clear()
        _MINE_TREE[id(c.mine)] = tree
    _, i, d = tree.find(Vector((x, y, 0.0)))
    best = c.mine[i]
    return d < 9.0 and best[2] - 2.0 < z < best[2] + 11.0


def paint_ridge(c, dg, ridge):
    groups = {}
    for p in ridge.data.polygons:
        x, y, z = p.center
        if dg.ridge_d(x, y) > 1.5 and in_mine(c, dg, x, y, z):
            if p.normal.z > 0.6:
                m = ("gulch_chasm", "abyss") if z < -10.0 else ("mine_floor", "packed_dirt")
            else:
                m = ("mine_rock", "wall")
        elif p.normal.z > 0.75 and z > 45:
            m = ("slickrock", "dirt")
        else:
            m = (dg.layer(z), "wall")
        groups.setdefault(m, []).append(p.index)
    for m, faces in groups.items():
        c.assign(ridge, c.lib(*m), faces)
    ridge.data.shade_flat()


# ------------------------------------------------------------------ props


def protos(c):
    for g in (False, True):
        gp.lantern_post(c, g)
        gp.hanging_lantern(c, g)
    for v in range(2):
        gp.barrel(c, v)
        gp.crate_stack(c, v)
        gp.ore_heap(c, v)
        gp.crypt(c, v)
    gp.wagon_wheel(c)
    gp.wagon(c, True)
    gp.wagon(c, True, True)
    gp.trough(c)
    gp.hitching_rail(c)
    gp.bench(c)
    gp.coffin(c)
    for v in range(6):
        gp.headstone(c, v)
    for v in range(3):
        gp.grave_cross(c, v)
    gp.iron_fence(c, 10.0)
    gp.cemetery_gate(c)
    for v in range(4):
        gp.dead_tree(c, v)
        gp.spectral_crystals(c, v)
        cp.saguaro(c, v)
    gp.cattle_skull(c)
    gp.ore_cart(c, glow=True)
    gp.ore_cart(c)
    gp.ore_cart(c, tipped=True)
    gp.pick_and_shovel(c)
    gp.timber_set(c)
    gp.timber_set(c, broken=True)
    gp.timber_set(c, 3.4, 5.8)
    gp.mine_portal(c)
    gp.winch(c)
    gp.chain_hang(c, 3.0)
    gp.chain_hang(c, 5.0)
    gp.chain_hang(c, 12.0)
    for v in range(2):
        gp.tumbleweed(c, v)
        cp.barrel_cactus(c, v)
        cp.sagebrush(c, v)
        cp.dry_grass(c, v)
        cp.chevron_sign(c, v)
        cp.boulder(c, v)
    cp.hoodoo(c, 0, 14.0)
    cp.hoodoo(c, 1, 20.0)


# ------------------------------------------------------------------ trestles


def pieces_of(c, kind):
    return [ob for ob in c.pieces if ob.name.endswith(" " + kind)]


def bent(m, a, b, top, ground_at, levels=6.0, posts=4, mat=("weathered_timber", "wall"), splay=0.1, foot=True):
    """A timber trestle bent from deck level `top` down to the ground: `posts` posts
    between a and b (x, y), splayed out as they go down, girts every `levels` metres,
    X-braced between neighbouring posts."""
    ax, ay = a
    bx, by = b
    cx, cy = (ax + bx) / 2, (ay + by) / 2
    px = [(lerp(ax, bx, k / (posts - 1)), lerp(ay, by, k / (posts - 1))) for k in range(posts)]
    g = min(ground_at(x, y) for x, y in px)
    H = top - g
    if H < 1.0:
        return
    ux, uy = (bx - ax), (by - ay)
    L = math.hypot(ux, uy) or 1.0
    ux, uy = ux / L, uy / L

    def at(k, z):
        x, y = px[k]
        o = (k - (posts - 1) / 2) / ((posts - 1) / 2)
        spread = (top - z) * splay * o
        return (x + ux * spread, y + uy * spread, z)

    for k in range(posts):
        x, y = px[k]
        gk = ground_at(x, y)
        m.add(mat, lambda bm, k=k, gk=gk: _beam_pts(bm, at(k, gk - 0.6), at(k, top), 0.55))
        if foot:
            m.add(("masonry", "wall"), lambda bm, k=k, gk=gk: cuboid(bm, at(k, gk), (1.5, 1.5, 1.4)))
    n = max(1, int(H / levels))
    for j in range(n + 1):
        z = top - j * H / n
        m.add(mat, lambda bm, z=z: _beam_pts(bm, at(0, z), at(posts - 1, z), 0.35))
        if j < n:
            z2 = top - (j + 1) * H / n
            for k in range(posts - 1):
                m.add(mat, lambda bm, k=k, z=z, z2=z2: _beam_pts(bm, at(k, z), at(k + 1, z2), 0.22))
                m.add(mat, lambda bm, k=k, z=z, z2=z2: _beam_pts(bm, at(k + 1, z), at(k, z2), 0.22))


def _beam_pts(bm, a, b, w):
    cp._beam(bm, a, b, w)


def trestles(c, sc, dg):
    """The Rickety Trestle over the chasm and the trestles along the ravine's east wall:
    tall timber bents all the way down to the rock, braced in tiers, stone footings,
    stringers between the bents, lanterns along the rails."""
    m = Mesh()
    ground_at = lambda x, y: dg.natural(x, y)  # noqa: E731
    for ob in pieces_of(c, "trestle"):
        s0, s1 = ob["kp_from"], ob["kp_to"]
        if s1 < s0:
            s1 += c.length
        L = s1 - s0
        n = max(2, int(round(L / 7.5)))
        tops = []
        for k in range(n + 1):
            q = c.at(s0 + L * k / n)
            top = q.p.z - 1.9
            a, b = q.side(-q.w / 2 - 0.8), q.side(q.w / 2 + 0.8)
            bent(m, (a.x, a.y), (b.x, b.y), top, ground_at, splay=0.05)
            tops.append((q, top))
            if k % 4 == 2:
                sc.creaks.append((q.p.x, q.p.y, q.p.z, 30.0))
        # Stringers and longitudinal bracing between the bents, the top two tiers.
        for (qa, ta), (qb, tb) in zip(tops, tops[1:]):
            for o in (-q.w / 2 - 0.8, 0.0, q.w / 2 + 0.8):
                pa, pb = qa.side(o), qb.side(o)
                m.add(TIMBER, lambda bm, pa=pa, pb=pb, ta=ta, tb=tb: _beam_pts(bm, (pa.x, pa.y, ta + 0.4), (pb.x, pb.y, tb + 0.4), 0.45))
                for dz in (6.0, 12.0):
                    if min(ta, tb) - dz > dg.natural(pa.x, pa.y):
                        m.add(TIMBER, lambda bm, pa=pa, pb=pb, ta=ta, tb=tb, dz=dz: _beam_pts(bm, (pa.x, pa.y, ta - dz), (pb.x, pb.y, tb - dz + 6.0), 0.2))
        # Lanterns on the rail posts, alternating sides, every 30 m.
        for k in range(int(L / 30.0) + 1):
            q = c.at(s0 + 6.0 + k * 30.0)
            side = 1 if k % 2 else -1
            p = q.side(side * (q.w / 2 + 0.9))
            m.add(TIMBER, lambda bm, p=p, q=q: cuboid(bm, (p.x, p.y, q.p.z + 1.6), (0.3, 0.3, 3.2)))
            sc.put("Hanging Lantern", p.x, p.y, q.p.z + 3.2, road_rot(q), coll="Bridges")
            sc.warm.append((p.x, p.y, q.p.z + 2.4))
            sc.lanterns.append((p.x, p.y, q.p.z + 2.4))
    m.build(c, "Trestles", "Bridges", role="both")


TIMBER = ("weathered_timber", "wall")


# ------------------------------------------------------------------ the mine's insides


def mine_interior(c, sc, dg):
    """Inside the Hazard Mine: timber sets along the tunnels (a few broken), rails down
    the middle on sleepers, lanterns on the sets (orange, and the odd spectral green),
    glowing crystals breaking out of the walls; the old workings (carts, ore heaps,
    tools, the cart crossing's rails); the spectral trestle's bents plunging into the
    glowing chasm, chains, layers of green mist below; the broken gateway out."""
    line = c.mine
    i_portal = dg.mine_index(line, dg.PORTAL_AT)
    i_gate = dg.mine_index(line, dg.GATEWAY_AT)
    i_b0, i_b2 = dg.mine_index(line, 4), dg.mine_index(line, 6)
    i_d0, i_d3 = dg.mine_index(line, 8), dg.mine_index(line, 11)
    m = Mesh()
    sets = 0

    def frame_at(i):
        a, b = line[max(0, i - 2)], line[min(len(line) - 1, i + 2)]
        return math.atan2(b[1] - a[1], b[0] - a[0])

    # Timber sets and lanterns in the tunnels.
    for i in list(range(i_portal + 4, i_d0 - 2, 6)) + list(range(i_d3 + 4, i_gate - 4, 6)):
        if i_b0 - 4 <= i <= i_b2 + 4:
            continue
        p = line[i]
        h = frame_at(i)
        sets += 1
        broken = sets % 7 == 3
        sc.put("Timber Set 6.4 8.2" + (" Broken" if broken else ""), p[0], p[1], p[2] - 0.3, h - math.pi / 2, coll="Mine")
        if sets % 3 == 0:
            side = 1 if sets % 2 else -1
            rx, ry = math.cos(h - math.pi / 2) * side * 5.2, math.sin(h - math.pi / 2) * side * 5.2
            green = sets % 9 == 0
            sc.put("Hanging Lantern" + (" Green" if green else ""), p[0] + rx, p[1] + ry, p[2] + 7.6, h, coll="Mine")
            (sc.green if green else sc.warm).append((p[0] + rx, p[1] + ry, p[2] + 6.8))
            sc.lanterns.append((p[0] + rx, p[1] + ry, p[2] + 6.8))
    # Crystals breaking out of the walls, every so often, both sides.
    k = 0
    for i in range(i_portal + 30, i_gate - 10, 13):
        if i_d0 - 3 <= i <= i_d3 + 3:
            continue
        k += 1
        p = line[i]
        h = frame_at(i)
        side = 1 if k % 2 else -1
        w = 7.5 if not (i_b0 - 4 <= i <= i_b2 + 4) else 15.0
        x, y = p[0] + math.cos(h - math.pi / 2) * side * w, p[1] + math.sin(h - math.pi / 2) * side * w
        sc.put("Spectral Crystals %d" % (k % 4), x, y, p[2] + 0.5 + (k % 3) * 1.5, h + side, scale=(0.9 + 0.3 * (k % 3)), coll="Mine")
        sc.green.append((x, y, p[2] + 2.0))
    # Rails down the middle, on sleepers, from the portal to the cavern and on out.
    for a, b in ((i_portal - 12, i_d0), (i_d3, i_gate + 8)):
        pts = line[max(0, a):b + 1]
        for j in range(0, len(pts) - 1, 1):
            p0, p1 = pts[j], pts[j + 1]
            h = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
            rx, ry = -math.sin(h), math.cos(h)
            if j % 2 == 0:
                m.add(("mine_timber", "wall"), lambda bm, p0=p0, h=h: cuboid(bm, (p0[0], p0[1], p0[2] + 0.06), (0.35, 2.4, 0.12), h))
            for o in (-0.72, 0.72):
                m.add(("rail_iron", "wall"), lambda bm, p0=p0, p1=p1, o=o, rx=rx, ry=ry: cp._beam(bm, (p0[0] + rx * o, p0[1] + ry * o, p0[2] + 0.2), (p1[0] + rx * o, p1[1] + ry * o, p1[2] + 0.2), 0.12, 0.14))
    # The old workings: the cart crossing's rails across the road, carts, ore, tools.
    cx, cy, cz, ch = sc.cart
    rx, ry = math.cos(ch - math.pi / 2), math.sin(ch - math.pi / 2)
    for u in range(-44, 45, 1):
        x, y = cx + rx * u, cy + ry * u
        if u % 2 == 0:
            m.add(("mine_timber", "wall"), lambda bm, x=x, y=y: cuboid(bm, (x, y, cz + 0.07), (2.4, 0.35, 0.12), ch))
        for o in (-0.72, 0.72):
            ox, oy = math.cos(ch) * o, math.sin(ch) * o
            m.add(("rail_iron", "wall"), lambda bm, x=x, y=y, ox=ox, oy=oy: cp._beam(bm, (x + ox, y + oy, cz + 0.2), (x + ox + rx, y + oy + ry, cz + 0.2), 0.12, 0.14))
    for k, (u, v, proto) in enumerate(((-12, 14, "Ore Cart"), (11, -16, "Ore Heap 0"), (13, 10, "Ore Heap 1"), (-14, -9, "Barrel 1"), (-11, -18, "Pick And Shovel"),
                                       (12, 18, "Crate Stack 0"), (-15, 4, "Ore Cart Tipped"))):
        x, y = cx + rx * u + math.cos(ch) * v, cy + ry * u + math.sin(ch) * v
        sc.put(proto, x, y, cz - 0.3, ch + k * 0.9, coll="Mine")
    # The shaft sign, and a warning light either side of the crossing.
    nx, ny = -math.cos(ch), -math.sin(ch)
    sx, sy = cx + rx * 9.0 - math.cos(ch) * 10, cy + ry * 9.0 - math.sin(ch) * 10
    import gulch_town as gt
    gt.face_quad(m, ("sign_shaft", "wall"), sx, sy, nx, ny, 2.0, cz + 3.0, cz + 3.7, out=0.0)
    m.add(TIMBER, lambda bm: cuboid(bm, (sx - nx * 0.2, sy - ny * 0.2, cz + 1.8), (0.25, 0.25, 3.6)))
    for side in (-1, 1):
        x, y = cx + rx * side * 7.5 - math.cos(ch) * 4.0, cy + ry * side * 7.5 - math.sin(ch) * 4.0
        sc.put("Lantern Post Green", x, y, cz - 0.3, ch + (0 if side > 0 else math.pi), coll="Mine")
        sc.green.append((x, y, cz + 3.6))
    sc.mist.append((cx, cy, cz, 16.0, 6))
    # The spectral trestle's bents, down to the cavern's floor.
    i0, i1 = i_d0, i_d3
    for i in range(i0 + 3, i1 - 2, 8):
        p = line[i]
        h = frame_at(i)
        rx_, ry_ = math.cos(h - math.pi / 2), math.sin(h - math.pi / 2)
        a = (p[0] - rx_ * 5.3, p[1] - ry_ * 5.3)
        b = (p[0] + rx_ * 5.3, p[1] + ry_ * 5.3)
        bent(m, a, b, p[2] - 1.7, lambda x, y: -31.0, posts=3, mat=("mine_timber", "wall"), splay=0.08, levels=7.0, foot=False)
        sc.creaks.append((p[0], p[1], p[2], 24.0))
    for k, i in enumerate(range(i0 + 6, i1 - 4, 12)):
        p = line[i]
        h = frame_at(i)
        side = 1 if k % 2 else -1
        x, y = p[0] + math.cos(h - math.pi / 2) * side * 5.0, p[1] + math.sin(h - math.pi / 2) * side * 5.0
        sc.put("Chain 12", x, y, p[2] - 1.8, h, coll="Mine")
        sc.put("Hanging Lantern Green" if k % 2 else "Hanging Lantern", x, y, p[2] + 2.6, h, coll="Mine")
        m.add(TIMBER, lambda bm, x=x, y=y, p=p: cuboid(bm, (x, y, p[2] + 1.4), (0.3, 0.3, 2.8)))
        (sc.green if k % 2 else sc.warm).append((x, y, p[2] + 1.8))
        sc.lanterns.append((x, y, p[2] + 1.8))
    # Crystal formations round the cavern's walls, and its green mist in layers below.
    ccx, ccy = dg.CAVERN
    for k in range(14):
        a = k * math.tau / 14 + 0.2
        x, y = ccx + math.cos(a) * 41.0, ccy + math.sin(a) * 33.0
        z = -24.0 + (k * 7) % 5 * 9.0
        sc.put("Spectral Crystals %d" % (k % 4), x, y, z, a + math.pi, scale=2.2 + 0.8 * (k % 3), coll="Mine")
        sc.green.append((ccx + math.cos(a) * 34.0, ccy + math.sin(a) * 27.0, z + 3.0))
    for z, r in ((-26.0, 1.0), (-14.0, 0.9), (-3.0, 0.75)):
        m.add(("spectral_mist", "wall"), lambda bm, z=z, r=r: bm.faces.new(ring(bm, (ccx, ccy), 30.0 * r, z, 20, rx=38.0 * r)))
    sc.green += [(ccx, ccy, -20.0), (ccx, ccy, -6.0)]
    sc.wisps.append((ccx, ccy, -2.0, 34.0, 18))
    sc.whispers.append((ccx, ccy, 10.0, 70.0))
    # The broken gateway out, on the ridge's east face.
    p = line[i_gate]
    h = frame_at(i_gate)
    x, y = p[0] - math.cos(h) * 6.0, p[1] - math.sin(h) * 6.0
    sc.put("Timber Set 6.4 8.2 Broken", x, y, p[2] - 0.3, h - math.pi / 2, scale=1.15, coll="Mine")
    sc.put("Timber Set 6.4 8.2", x - math.cos(h) * 4.0, y - math.sin(h) * 4.0, p[2] - 0.3, h - math.pi / 2, scale=1.1, coll="Mine")
    sc.green.append((x - math.cos(h) * 8.0, y - math.sin(h) * 8.0, p[2] + 4.0))
    sc.gateway = (x, y, p[2], h)
    m.build(c, "Mine Works", "Mine")
    # Ghost miners at the edges of the tunnels and the workings; the great shadow on the
    # wall as you climb towards the way out.
    for k, i in enumerate((i_portal + 40, i_b0 + 6, i_b2 + 14, i_d3 + 30)):
        p = line[i]
        h = frame_at(i)
        side = 1 if k % 2 else -1
        w = 5.4 if not (i_b0 - 4 <= i <= i_b2 + 4) else 12.0
        x, y = p[0] + math.cos(h - math.pi / 2) * side * w, p[1] + math.sin(h - math.pi / 2) * side * w
        sc.ghosts.append({"look": "miner", "x": x, "y": y, "z": p[2] - 0.2, "heading": h + math.pi, "period": 9.0 + k * 2.5, "offset": k * 2.0,
                          "vanish": 22.0})
    for k, (dx, dy, dz) in enumerate(((-18, 8, 0), (14, -10, 6), (4, 20, -6))):
        sc.ghosts.append({"look": "float", "x": ccx + dx, "y": ccy + dy, "z": 8.0 + dz, "heading": k * 2.0, "period": 12.0 + k * 3.0,
                          "offset": k * 3.5, "drift": 6.0})
    i = i_gate - 26
    p = line[i]
    h = frame_at(i)
    x, y = p[0] + math.cos(h + math.pi / 2) * 6.45, p[1] + math.sin(h + math.pi / 2) * 6.45
    sc.ghosts.append({"look": "shadow", "x": x, "y": y, "z": p[2] - 0.2, "heading": h - math.pi / 2, "period": 16.0, "offset": 3.0,
                      "scale": 2.4})
    # Where you're underground (for the sound).
    sc.caves = [(p[0], p[1], p[2] + 4.0, 13.0) for p in line[i_portal + 8:i_gate - 4:10]]
    sc.caves.append((ccx, ccy, 0.0, 42.0))


# ------------------------------------------------------------------ the ravine


def chasm_mist(c, sc, dg):
    """Layers of green mist filling the chasm under the Rickety Trestle and away north,
    glowing, drifting, so the deep floor is only glimpsed through it."""
    path = []
    for (ax, ay, ahw, af), (bx, by, bhw, bf) in zip(dg.RAVINE, dg.RAVINE[1:]):
        n = max(1, int(math.hypot(bx - ax, by - ay) / 20.0))
        for j in range(n):
            t = j / n
            fl = lerp(af, bf, t)
            if fl < -4.0:
                path.append((lerp(ax, bx, t), lerp(ay, by, t), lerp(ahw, bhw, t), fl))
    for k, (dz, wk) in enumerate(((5.0, 1.0), (14.0, 1.25), (24.0, 1.5))):
        pts = [(x, y, hw * wk, fl + dz) for x, y, hw, fl in path]
        if len(pts) > 1:
            c.ribbon("Chasm Mist %d" % k, pts, 0.0, 0.0, c.lib("spectral_mist"), coll="Mist", role="visual", steps=2)
    for x, y, hw, fl in path[::3]:
        sc.green.append((x, y, fl + 6.0))
        if y < 520:
            sc.mist.append((x, y, fl + 2.0, hw * 0.6, 4))


def ravine(c, sc, dg):
    """The ravine: glowing fissures splitting its walls and floor, old adits with green
    light inside, mining machinery, rails, Dead Man's Rock at the bend."""
    m = Mesh()
    k = 0
    for (ax, ay, ahw, af), (bx, by, bhw, bf) in zip(dg.RAVINE[2:], dg.RAVINE[3:]):
        L = math.hypot(bx - ax, by - ay)
        n = max(1, int(L / 26.0))
        for j in range(n):
            k += 1
            t = (j + 0.5) / n
            x, y = lerp(ax, bx, t), lerp(ay, by, t)
            hw = lerp(ahw, bhw, t)
            fl = lerp(af, bf, t)
            ux, uy = (bx - ax) / L, (by - ay) / L
            side = 1 if k % 2 else -1
            nx, ny = -uy * side, ux * side  # out from the centre line toward a wall
            u = hw - dg.WALLW + 2.0 + 3.0 * rnd(k)
            px, py = x + nx * u, y + ny * u
            if dg.ridge_d(px, py) > -4.0 or not clear(c, px, py, 4.0):
                continue
            g = dg.natural(px, py)
            hgt = 6.0 + 9.0 * rnd(k * 3)
            # A fissure split up the wall's face: a glowing crack laid on the rock, from
            # its foot up the slope, facing back into the ravine.
            hw_ = 0.8 + 0.9 * rnd(k * 5)
            top_u = 2.0
            while top_u < 24.0 and dg.natural(px + nx * top_u, py + ny * top_u) < g + hgt:
                top_u += 1.0
            tx, ty = px + nx * top_u, py + ny * top_u
            tz = dg.natural(tx, ty)
            rx, ry = -ny, nx
            m.quad(("fissure_glow", "wall"),
                   [(px - rx * hw_ - nx * 0.6, py - ry * hw_ - ny * 0.6, g - 0.5), (px + rx * hw_ - nx * 0.6, py + ry * hw_ - ny * 0.6, g - 0.5),
                    (tx + rx * hw_ * 0.6 - nx * 0.6, ty + ry * hw_ * 0.6 - ny * 0.6, tz + 0.4), (tx - rx * hw_ * 0.6 - nx * 0.6, ty - ry * hw_ * 0.6 - ny * 0.6, tz + 0.4)],
                   [(0, 0), (1, 0), (1, 1), (0, 1)])
            sc.green.append((px - nx * 4.0, py - ny * 4.0, g + 3.0))
            if k % 3 == 0 and fl > -10:
                # A crack across the floor too.
                fx, fy = x + nx * u * 0.5, y + ny * u * 0.5
                if clear(c, fx, fy, 2.0):
                    m.add(("fissure_glow", "wall"), lambda bm, fx=fx, fy=fy, a=math.atan2(ny, nx): cuboid(bm, (fx, fy, dg.natural(fx, fy) + 0.05), (10.0, 0.9, 0.08), a))
                    sc.mist.append((fx, fy, dg.natural(fx, fy), 8.0, 3))
            if k % 4 == 1 and fl > -10:
                # An old adit: a small portal, dark inside, a green light deep in it.
                sc.put("Mine Portal", px - nx * 1.5, py - ny * 1.5, g - 0.3, math.atan2(-ny, -nx) + math.pi / 2, scale=0.42, coll="Ravine")
                gt_face(m, ("mine_rock", "wall"), px + nx * 0.6, py + ny * 0.6, -nx, -ny, 2.6, g, g + 3.8)
                sc.green.append((px - nx * 3.0, py - ny * 3.0, g + 2.0))
    m.build(c, "Ravine Fissures", "Ravine")
    # Dead Man's Rock, inside the bend.
    import canyon_scenery as cs
    rx, ry = dg.DEAD_MANS_ROCK
    cs.butte(c, dg, "Dead Man's Rock", rx - 4.0, ry + 4.0, 26.0, 20.0, 58.0, base=dg.natural(rx, ry) - 2.0, seed=7, angle=0.6,
             bands=cs.SPIRE_BANDS, coll="Rocks")
    # Machinery and leftovers along the floor.
    S = dg.SEG
    junk = getattr(dg, "RAVINE_JUNK", None) or ((S[13] + 40, -19, "Winch"), (S[13] + 95, 18, "Ore Cart Tipped"), (S[13] + 120, -17, "Ore Heap 1"),
                                                (S[12] + 20, -18, "Crate Stack 0"), (S[14] + 70, 18, "Ore Cart"), (S[15] + 30, -17, "Barrel 1"))
    for k, (s, off, proto) in enumerate(junk):
        q = c.at(s)
        p = q.side(off)
        if clear(c, p.x, p.y, 3.0):
            sc.put(proto, p.x, p.y, dg.natural(p.x, p.y), road_rot(q) + k, coll="Ravine")
    sc.whispers.append(getattr(dg, "RAVINE_WHISPER", (250.0, 140.0, 14.0, 60.0)))


def gt_face(m, mat, cx, cy, nx, ny, hw, z0, z1):
    import gulch_town as gt

    gt.face_quad(m, mat, cx, cy, nx, ny, hw, z0, z1, out=0.0)


# ------------------------------------------------------------------ rocks and plants


def rocks(c, sc, dg):
    """Crags on Hazard Ridge, hoodoos and boulders round the plateau, buttes and spires
    standing round the land."""
    import canyon_scenery as cs
    for k, (x, y, rx, ry, top) in enumerate(getattr(dg, "CRAGS", ((120.0, 320.0, 22.0, 16.0, 94.0), (185.0, 240.0, 18.0, 15.0, 88.0),
                                                                   (110.0, 180.0, 16.0, 12.0, 84.0), (190.0, 150.0, 12.0, 10.0, 82.0)))):
        cs.butte(c, dg, "Crag %d" % k, x, y, rx, ry, top, base=dg.Z_RIDGE - 4.0, seed=20 + k, angle=k * 0.9, bands=cs.SPIRE_BANDS,
                 coll="Rocks")
    for k, (x, y, rx, ry, top) in enumerate(getattr(dg, "BUTTES", ((-420.0, 120.0, 40.0, 30.0, 85.0), (-380.0, 520.0, 34.0, 26.0, 80.0),
                                                                    (420.0, 180.0, 30.0, 40.0, 92.0), (400.0, -200.0, 36.0, 28.0, 86.0),
                                                                    (-140.0, -260.0, 30.0, 24.0, 74.0), (380.0, 560.0, 26.0, 20.0, 88.0)))):
        if clear(c, x, y, max(rx, ry) * 1.5 + 10):
            cs.butte(c, dg, "Butte %d" % k, x, y, rx, ry, top, seed=40 + k, angle=k * 1.3, coll="Rocks")
    ter = sc.ground_obs
    for proto, n, sc_ in (("Hoodoo 0 14", 14, (0.8, 1.4)), ("Hoodoo 1 20", 8, (0.8, 1.2)), ("Sandstone Boulder 0", 40, (0.8, 2.0)),
                          ("Sandstone Boulder 1", 40, (0.8, 2.0))):
        _scatter(c, sc, dg, proto, n, sc_, ter, margin=12.0, seed=sum(map(ord, proto)) % 97)


def _ok_plant(c, sc, dg, x, y, z, margin):
    if not clear(c, x, y, margin) or not sc.free(x, y, 2.0):
        return False
    if dg.ridge_d(x, y) > -3.0:
        return False
    d, hw, fl, _ = dg.ravine_q(x, y)
    if hw - d > 0 and z < fl + 2 and fl < 2:
        return False  # not down in the chasm
    return True


def _scatter(c, sc, dg, proto, n, scale, ter, margin=6.0, seed=0, coll="Plants", area=None):
    from props import scatter

    N = near(dg)
    area = area or (N[0] + 10, N[1] - 10, N[2] + 10, N[3] - 10)
    return scatter(c, proto, n, area, lambda x, y, z: _ok_plant(c, sc, dg, x, y, z, margin), ter, seed=seed, scale=scale, role="visual",
                   coll=coll)


def plants(c, sc, dg):
    """Saguaros standing like sentinels, barrel cactus, scrub, dry grass, dead trees,
    tumbleweeds caught against things."""
    ter = sc.ground_obs
    for k, (proto, n, s) in enumerate((("Saguaro 0", 30, (0.9, 1.3)), ("Saguaro 1", 30, (0.9, 1.3)), ("Saguaro 2", 26, (0.9, 1.2)),
                                       ("Saguaro 3", 20, (0.9, 1.2)), ("Barrel Cactus 0", 40, (0.8, 1.2)), ("Barrel Cactus 1", 30, (0.8, 1.2)),
                                       ("Sagebrush 0", 90, (0.7, 1.2)), ("Sagebrush 1", 90, (0.7, 1.2)), ("Dry Grass 0", 160, (0.8, 1.3)),
                                       ("Dry Grass 1", 160, (0.8, 1.3)), ("Dead Tree 0", 14, (0.8, 1.2)), ("Dead Tree 2", 14, (0.8, 1.2)),
                                       ("Tumbleweed 0", 24, (0.8, 1.2)), ("Tumbleweed 1", 24, (0.8, 1.2)))):
        _scatter(c, sc, dg, proto, n, s, ter, margin=5.0 if "Grass" in proto else 7.0, seed=k * 11 + 3)


def road_furniture(c, sc, dg):
    """Lantern posts along the roads out of town (they light the way), and amber chevron
    boards round the corners."""
    S = dg.SEG
    L = c.length
    k = 0
    l0, l1 = getattr(dg, "LANTERNS", (S[6], S[16]))
    for s in range(int(l0), int(l1), 34):
        q = c.at(s)
        k += 1
        if q.p.z - dg.natural(q.p.x, q.p.y) > 4.0:
            continue  # on a trestle (its own lanterns)
        side = 1 if k % 2 else -1
        p = q.side(side * (q.w / 2 + 3.6))
        if not clear(c, p.x, p.y, 2.5) or not sc.free(p.x, p.y, 1.0):
            continue
        rot = road_rot(q) + (math.pi / 2 if side < 0 else -math.pi / 2)
        green = dg.ridge_d(p.x, p.y) > -40 and dg.ravine_q(p.x, p.y)[2] < 12
        z = sc.ground(p.x, p.y)
        sc.put("Lantern Post" + (" Green" if green else ""), p.x, p.y, z, rot, coll="Props")
        lx, _, lz = gp.LANTERN_POST_LIGHT
        wx, wy = p.x + math.cos(rot) * lx, p.y + math.sin(rot) * lx
        (sc.green if green else sc.warm).append((wx, wy, z + lz))
        if k % 2 == 0:
            sc.lanterns.append((wx, wy, z + lz))
    # Chevrons round the outside of the big corners.
    for seg, n in getattr(dg, "CHEVRONS", ((6, 6), (9, 3), (14, 3), (16, 3))):
        sg = dg.LAYOUT[seg]
        s0 = S[seg]
        arc = sg[1] * math.radians(sg[2])
        right = sg[0] == "R"
        for j in range(n):
            q = c.at(s0 + arc * (j + 0.5) / n)
            off = (q.w / 2 + 3.0) * (-1 if right else 1)
            p = q.side(off)
            if clear(c, p.x, p.y, 2.0) and q.p.z - dg.natural(p.x, p.y) < 3.0:
                rot = road_rot(q) + (0.0 if right else math.pi)
                sc.put("Chevron Sign %d" % (j % 2), p.x, p.y, sc.ground(p.x, p.y), rot, coll="Props")
                sc.warm.append((p.x, p.y, sc.ground(p.x, p.y) + 2.0))


# ------------------------------------------------------------------ gameplay


def gameplay(c, sc, dg):
    """Boosts, pickups, checkpoints (with a twin gate in the mine), the cart crossing and
    the haunt: ghosts, wisps, mist, lanterns, tumbleweeds, the windmill, the bell."""
    S = dg.SEG
    line = c.mine
    if hasattr(dg, "pickups"):
        # The course's own boosts, pickups and checkpoints.
        gates, apex = dg.pickups(c)
    else:
        gates, apex = _pickups(c, dg)
    sc.apex = apex
    if apex is not None:  # (none in the ruin: the mine is gone)
        main_gate = min(gates.items(), key=lambda kv: abs(kv[0] - apex))[1]
        # The twin gate: in the tunnel just before the chasm cavern, so a fall from the
        # spectral trestle puts you back there.
        k = dg.mine_index(line, 7)
        pts = [line[k - 4][:3], line[k][:3], line[k + 4][:3]]
        c.alt_gate(main_gate, "haunted_mine", pts, width=13.0, height=8.0)
        # The shortcut's line, as a path (route.json): for tools and tests.
        c.path_curve("Haunted Mine Path", [p[:3] for p in line[::4]] + [line[-1][:3]], closed=False)
    if getattr(sc, "cart", None):
        # ---- the runaway ore cart across the old workings (solid: a knock and a slowdown)
        cx, cy, cz, ch = sc.cart
        rx, ry = math.cos(ch - math.pi / 2), math.sin(ch - math.pi / 2)
        A = c.game(cx - rx * 22.0, cy - ry * 22.0, cz)
        B = c.game(cx + rx * 22.0, cy + ry * 22.0, cz)
        c.entity("minecart", ax=A[0], ay=A[1], az=A[2], bx=B[0], by=B[1], bz=B[2], period=7.0, offset=1.5, travel=3.0, warn=1.8)
    # ---- an ore cart rolling along the mine railway by itself now and then
    rp = sc.railway
    c.path_curve("Railway", [(x, y, z) for x, y, z in rp[::3]] + [rp[-1]], closed=False)
    c.entity("railcart", route="Railway", period=34.0, offset=5.0, travel=13.0, pause=4.0)
    # ---- the ghost rider: across the far hills beyond the graveyard
    gx, gy = dg.GRAVEYARD
    rider = []
    for k in range(9):
        t = k / 8
        x = gx - 430.0 + 60.0 * math.sin(t * 2.4)
        y = gy - 240.0 + 520.0 * t
        rider.append((x, y, dg.natural(x, y) + 0.2))
    c.path_curve("Ghost Rider Path", rider, closed=False)
    c.entity("ghostrider", route="Ghost Rider Path", period=38.0, offset=10.0, travel=14.0)
    # ---- ghosts, wisps, mist, whispers, creaks
    for g in sc.ghosts:
        gx_, gy_, gz_ = c.game(g["x"], g["y"], g["z"])
        extra = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in g.items() if k not in ("x", "y", "z", "heading")}
        c.entity("ghost", x=gx_, y=gy_, z=gz_, heading=round(_game_heading(g["heading"]), 3), **extra)
    for x, y, z, r, n in sc.wisps:
        game_entity(c, "wisps", x, y, z, radius=round(r, 1), count=n)
    for x, y, z, r, rate in sc.mist:
        game_entity(c, "mist", x, y, z, radius=round(r, 1), rate=rate)
    for x, y, z, r in sc.whispers:
        game_entity(c, "whispers", x, y, z, radius=round(r, 1))
    for x, y, z, r in sc.creaks[::2]:
        game_entity(c, "creak", x, y, z, radius=round(r, 1))
    for x, y, z, h in sc.doors:
        # (The doors' leaves lie along the front: their heading is the front's own line.)
        game_entity(c, "door", x, y, z, heading=round(h, 3), width=2.4, period=9.0)
    for x, y, z in sc.lanterns:
        game_entity(c, "lantern", x, y, z, flicker=True)
    bx, by, bz, br = sc.bell
    game_entity(c, "bell", bx, by, bz, heading=round(_game_heading(br), 3), period=31.0, offset=12.0, ring=4.0, scale=1.3)
    wx, wy, wz, wr = sc.windmill
    game_entity(c, "windmill", wx + math.cos(wr) * 1.4, wy + math.sin(wr) * 1.4, wz, heading=round(wr, 3), radius=3.2, speed=0.6, gusty=True)
    # Tumbleweeds blowing across the roads now and then (they roll through: no harm).
    for k, s in enumerate(getattr(dg, "TUMBLEWEEDS", (S[0] + 60, S[3] + 10, S[6] + 140, S[13] + 60, S[15] + 110, S[17] - 30))):
        q = c.at(s % c.length)
        a_, b_ = q.side(-30.0), q.side(30.0)
        if k % 2:
            a_, b_ = b_, a_
        A = c.game(a_.x, a_.y, q.p.z)
        B = c.game(b_.x, b_.y, q.p.z)
        c.entity("tumbleweed", ax=A[0], ay=A[1], az=A[2], bx=B[0], by=B[1], bz=B[2], period=round(17.0 + k * 3.3, 1), offset=round(k * 4.1, 1),
                 travel=round(6.0 + k % 3, 1), r=0.8)
    # The underground, for the sound.
    caves = [[*c.game(x, y, z), round(r, 1)] for x, y, z, r in sc.caves]
    c.entity("ambience", wind=0.55, caves=caves)
    # Dust behind the karts; dust blowing across the land; bats over the ridge.
    c.entity("dust", color="#b8704e", rate=0.9)
    c.entity("dustwind", rate=8, radius=60, color="#9a6a62")
    birds = getattr(dg, "BIRDS", ((150.0, 260.0), (230.0, -60.0)))
    for k, (x, y, z, r, n) in enumerate(((birds[0][0], birds[0][1], 120.0, 70.0, 6), (gx, gy, 70.0, 50.0, 5), (birds[1][0], birds[1][1], 70.0, 40.0, 4))):
        game_entity(c, "birds", x, y, z, radius=r, count=n, speed=round(0.35 + 0.05 * k, 2), seed=k + 1, color="#1e1424")


def _pickups(c, dg):
    """Dry Gulch's boosts, pickups and checkpoints (a twin gate in the mine)."""
    S = dg.SEG
    for at, across in ((30, 0), (S[2] + 10, 0), (S[7] + 40, 0), (S[8] + 40, 0), (S[10] + 70, -2), (S[13] + 80, 0), (S[15] + 50, 0),
                       (S[17] + 10, 0)):
        c.zipper(at, across)
    for at, across in ((80, 0), (S[3] + 30, 3), (S[5] + 25, -3), (S[6] + 120, 0), (S[7] + 150, 3), (S[8] + 100, 0), (S[11] + 40, 0),
                       (S[13] + 130, -3), (S[16] + 20, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in ((95, -5, "red"), (95, 5, "blue"), (S[2] + 30, 0, "green"), (S[5] + 10, 0, "yellow"), (S[6] + 60, -4, "rainbow"),
                            (S[6] + 60, 4, "red"), (S[7] + 100, 0, "blue"), (S[8] + 80, 0, "green"), (S[10] + 30, 0, "yellow"),
                            (S[12] + 30, -4, "rainbow"), (S[12] + 30, 4, "red"), (S[14] + 30, 0, "blue"), (S[15] + 90, -4, "green"),
                            (S[15] + 90, 4, "yellow")):
        c.balloon(at, across, col)

    line = c.mine
    a = kit.s_near(c, *line[0][:2])
    b = kit.s_near(c, *line[-1][:2])
    apex = S[10] + 100.0
    gates = c.checkpoints(
        extra=[S[1] + 30, S[3] + 20, S[5] + 20, S[6] + 80, S[6] + 160, S[7] + 120, a - 8, apex, b + 10, S[14] + 40, S[15] + 80,
               S[16] + 40],
        avoid=[(a - 2, apex - 8), (apex + 8, b + 2)],
        height=9.0,
    )
    return gates, apex


def _game_heading(rot):
    """A Blender facing angle (radians from +X toward +Y) to the game's heading (atan2 of
    x, z: 0 faces +Z)."""
    fx, fy = math.cos(rot), math.sin(rot)
    return math.atan2(fx, -fy)


# ------------------------------------------------------------------ light


def light(c, sc, dg, ter, ridge):
    """Paint the night: everything cool and moonlit, warm pools round every lantern and
    lit window, cold green round the mine, the fissures and the graveyard; inside the
    mine dark but for its lanterns and the green."""
    groups = ("Props", "Plants", "Town Props", "Graveyard", "Mineworks", "Mine", "Ravine", "Bridges")
    # Big squares: fewer meshes to draw (the plants and road props are spread thin).
    c.merge_props(("Plants", "Props"), cell=460.0)
    c.merge_props(("Town Props", "Graveyard", "Mineworks", "Mine", "Ravine", "Bridges"), cell=240.0)
    joined = [o for name in groups for o in c.coll(name).objects if o.type == "MESH" and o.data.users == 1]
    built = [o for name in ("Town", "Mineworks", "Mine", "Bridges", "Ravine", "Rocks", "Graveyard") for o in c.coll(name).objects if o.type == "MESH"]
    allobs = [ter, ridge] + built + joined
    allobs = list({id(o): o for o in allobs}.values())
    rocky = [ter, ridge] + list(c.coll("Rocks").objects)
    c.preset("sun", rocky, 0.3)
    c.preset("bottoms", rocky, 0.35)
    c.glow(allobs, [], 1.0, (1, 1, 1), base=(0.8, 0.8, 1.0))
    inside = lambda w: in_mine(c, dg, w.x, w.y, w.z) and dg.ridge_d(w.x, w.y) > 1.0  # noqa: E731
    mine_obs = [ridge] + [o for o in c.coll("Mine").objects if o.type == "MESH"]
    c.glow(mine_obs, [], 1.0, (1, 1, 1), base=(0.7, 0.64, 0.78), region=inside)
    c.glow(allobs, sc.green, 26.0, (0.75, 1.55, 1.1), base=1.0)
    c.glow(allobs, sc.warm, 18.0, (1.75, 1.2, 0.7), base=1.0)
    lanes = getattr(c, "lanes", [])
    kit.paint.shade_roads(c.pieces + lanes, 0.3)


# ------------------------------------------------------------------ build


def build(c, dg):
    import gulch_town as gt

    sc = Scene(c, dg)
    protos(c)
    ter = land(c, dg, sc)
    c.start_line()
    ridge = ridge_mass(c, dg)
    mine_cut(c, dg, sc, ridge)
    paint_ridge(c, dg, ridge)
    gt.start_arch(c, sc, dg)
    gt.town(c, sc, dg)
    gt.square(c, sc, dg)
    gt.chapel_and_tower(c, sc, dg)
    gt.street_dressing(c, sc, dg)
    gt.graveyard(c, sc, dg)
    gt.back_lanes(c, sc, dg)
    gt.mine_portal(c, sc, dg)
    gt.headframe(c, sc, dg)
    gt.railway(c, sc, dg)
    gt.mine_approach(c, sc, dg)
    trestles(c, sc, dg)
    mine_interior(c, sc, dg)
    ravine(c, sc, dg)
    chasm_mist(c, sc, dg)
    rocks(c, sc, dg)
    road_furniture(c, sc, dg)
    plants(c, sc, dg)
    gameplay(c, sc, dg)
    light(c, sc, dg, ter, ridge)
