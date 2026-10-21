# Oasis Haven's scenery (see oasis_haven.py): the land and the desert beyond, the lake
# and its shore foam, the spring and the cascades down the terraces, the aqueduct and its
# curtain, the canals, the pavilion on its island, the Grand Arched Bridge and the
# causeway, the start gate, the market, the palace, the resort round the shore, the
# beach, the docks and the boats, the gardens, and the gameplay entities. Built from the
# kit in oasis_props.py.
# SPDX-License-Identifier: MIT

import math

import oasis_props as op
import course_kit as kit
from course_kit import Vector, bmesh, lerp, materials, rnd
from props import blob, cuboid, loft, ring

COLL = "Resort"


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
        """One quad with its own UVs."""
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
    def __init__(self, c, oh):
        self.c = c
        self.oh = oh
        self.falls = []  # (x, y, foot, top, width, heading) for waterfall entities
        self.fountains = []  # (x, y, z, height, jets, radius)
        self.guests = []  # (x, y, z, heading, dance)
        self.lamps = []

    def put(self, proto, x, y, z, rot=0.0, scale=1.0, coll="Props", role="visual"):
        return self.c.place(proto, x, y, z, rot, scale, coll=coll, role=role)

    def ground(self, x, y):
        z = self.c.ground_z(x, y, self.ground_obs)
        return z if z is not None else self.oh.natural(x, y)


# ------------------------------------------------------------------ architecture


def wall_band(m, mat, a, b, z0, z1, bay, uv0=0.0):
    """A vertical wall quad from a to b (x, y), z0..z1, its texture repeating every `bay`
    metres along and once over its height. Returns the u where it ends."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    u1 = uv0 + L / bay
    m.quad(mat, [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], [(uv0, 0), (u1, 0), (u1, 1), (uv0, 1)])
    return u1


STYLES = {
    "cream": ("oasis_arcade", "oasis_windows"),
    "rose": ("arcade_rose", "windows_rose"),
    "white": ("arcade_white", "windows_white"),
    "ochre": ("arcade_ochre", "windows_ochre"),
}


def block(m, cx, cy, w, d, z0, h, rot=0.0, ground=5.0, storey=4.5, roof=True, parapet=True, base=None, style="cream"):
    """A resort building: an arcaded ground storey, window storeys above, a cornice of
    blue tiles and a parapet, a flat roof. (Footprint w x d, turned `rot`.)"""
    arc, win = STYLES.get(style, STYLES["cream"])
    ca, sa = math.cos(rot), math.sin(rot)

    def P(u, v):
        return (cx + u * ca - v * sa, cy + u * sa + v * ca)

    corners = [P(-w / 2, -d / 2), P(w / 2, -d / 2), P(w / 2, d / 2), P(-w / 2, d / 2)]
    zb = z0 - 3.0 if base is None else base
    top = z0 + h
    for k in range(4):
        a, b = corners[k], corners[(k + 1) % 4]
        # Foundations (hidden in the ground, or a plinth by the water).
        wall_band(m, ("oasis_stone", "wall"), a, b, zb, z0, 4.0)
        z = z0
        bands = [(z0, min(top, z0 + ground), (arc, "wall"), 10.4)]
        z = z0 + ground
        while z + 1.0 < top:
            bands.append((z, min(top, z + storey), (win, "wall"), 10.0))
            z += storey
        for za, zb2, mat, bay in bands:
            wall_band(m, mat, a, b, za, zb2, bay)
        # A blue-tiled frieze and the parapet.
        if parapet:
            wall_band(m, ("tile_border", "wall"), a, b, top, top + 0.6, 4.0)
            wall_band(m, ("oasis_stone", "wall"), a, b, top + 0.6, top + 1.4, 4.0)
    if roof:
        m.add(("oasis_stone", "wall"), lambda bm: bm.faces.new([bm.verts.new((x, y, top + (0.6 if parapet else 0.0))) for x, y in corners]))
    return top + (1.4 if parapet else 0.0)


def tower(m, x, y, z0, h, r=2.6, dome_mat="dome_blue", onion=0.6):
    """A slender tower: an octagonal shaft with a balcony, a lantern storey, an onion
    dome and a gold finial."""
    m.add(("oasis_stone", "wall"), lambda bm: op._cyl(bm, x, y, z0 - 2.0, z0 + h * 0.7, r, r * 0.9, n=8))
    m.add(("tile_border", "wall"), lambda bm: op._cyl(bm, x, y, z0 + h * 0.7, z0 + h * 0.74, r * 1.35, n=8))
    m.add(("oasis_arcade", "wall"), lambda bm: op._cyl(bm, x, y, z0 + h * 0.74, z0 + h * 0.9, r * 0.85, n=8))
    m.add(("gold_leaf", "wall"), lambda bm: op._cyl(bm, x, y, z0 + h * 0.9, z0 + h * 0.92, r * 1.0, n=8))
    m.add((dome_mat, "wall"), lambda bm: op.dome(bm, x, y, z0 + h * 0.92, r * 1.05, h=r * 1.7, n=10, rings=5, onion=onion))
    m.add(("gold_leaf", "wall"), lambda bm: op.finial(bm, x, y, z0 + h * 0.92 + r * 1.75, 0.8))


def great_dome(m, x, y, z, r, mat="dome_blue", drum=4.0, onion=0.3):
    """A drum with arched windows, a gold band, a great dome and its finial."""
    m.add(("oasis_arcade", "wall"), lambda bm: op._cyl(bm, x, y, z, z + drum, r, n=16))
    m.add(("gold_leaf", "wall"), lambda bm: op._cyl(bm, x, y, z + drum, z + drum + 0.5, r * 1.05, n=16))
    m.add((mat, "wall"), lambda bm: op.dome(bm, x, y, z + drum + 0.5, r, h=r * 1.05, n=20, rings=7, onion=onion))
    m.add(("gold_leaf", "wall"), lambda bm: op.finial(bm, x, y, z + drum + 0.5 + r * 1.1, r / 5.0))


def arch_gate(m, q, span, h, depth=3.5, towers=True, dome_mat="dome_blue"):
    """A great sandstone gateway over the road at route sample q: piers either side, a
    pointed arch, a tiled band, and towers with domes on the piers."""
    rot = road_rot(q)
    t = Vector((q.t.x, q.t.y, 0)).normalized()
    r = q.r
    base = q.p.z
    pier = 3.4
    for side in (-1, 1):
        c0 = q.p + r * side * (span / 2 + pier / 2)
        m.add(("oasis_stone", "wall"), lambda bm, c0=c0: cuboid(bm, (c0.x, c0.y, base + h / 2 - 1.5), (depth, pier, h + 3.0), rot))
        m.add(("tile_border", "wall"), lambda bm, c0=c0: cuboid(bm, (c0.x, c0.y, base + h * 0.55), (depth + 0.3, pier + 0.3, 0.6), rot))
        if towers:
            tower(m, c0.x, c0.y, base + h, 8.0, r=1.7, dome_mat=dome_mat, onion=0.7)
    # The arch: a pointed soffit lofted across, and the wall above it.
    rings_ = []

    def soffit(bm):
        rs = []
        n = 12
        for k in range(n + 1):
            a = math.pi * k / n
            o = -math.cos(a) * span / 2
            zz = base + h * 0.62 + math.sin(a) ** 0.7 * h * 0.3
            p = q.p + r * o
            rs.append([bm.verts.new((p.x + t.x * dd, p.y + t.y * dd, zz + dz)) for dd, dz in ((-depth / 2, 0), (depth / 2, 0), (depth / 2, -0.01), (-depth / 2, -0.01))])
        loft(bm, rs, cap_top=False)

    m.add(("oasis_stone", "wall"), soffit)
    m.add(("oasis_carved" if False else "oasis_stone", "wall"),
          lambda bm: cuboid(bm, (q.p.x, q.p.y, base + h + 0.6), (depth, span + pier * 2, 2.8), rot))
    m.add(("tile_border", "wall"), lambda bm: cuboid(bm, (q.p.x, q.p.y, base + h - 1.0), (depth + 0.2, span + pier * 2 + 0.2, 0.7), rot))


# ------------------------------------------------------------------ the land


FAR = (-2400.0, 2400.0, -2400.0, 2400.0)
NEAR = (-380.0, 440.0, -340.0, 560.0)

# Red mesas and buttes far out in the desert, beyond the golden cliffs.
FAR_MESAS = [
    (-1300.0, 900.0, (260.0, 160.0), 230.0),
    (-300.0, 1350.0, (320.0, 150.0), 260.0),
    (700.0, 1250.0, (240.0, 170.0), 240.0),
    (1400.0, 600.0, (200.0, 260.0), 270.0),
    (1500.0, -400.0, (180.0, 300.0), 240.0),
    (900.0, -1300.0, (300.0, 160.0), 260.0),
    (-200.0, -1450.0, (260.0, 140.0), 230.0),
    (-1100.0, -1100.0, (240.0, 180.0), 250.0),
    (-1700.0, -200.0, (300.0, 160.0), 240.0),
    (-900.0, 1100.0, (60.0, 50.0), 200.0),
    (1050.0, 900.0, (50.0, 60.0), 210.0),
    (-1250.0, -500.0, (45.0, 45.0), 190.0),
]


def far_natural(oh):
    def f(x, y):
        h = oh.natural(x, y)
        r = math.hypot(x, y)
        # Rolling golden dunes beyond the rim.
        if r > 700:
            crest = 1.0 - abs(math.sin(x / 120.0 + 0.6 * math.sin(y / 170.0)))
            h = max(h, 55.0 + 34.0 * crest * crest + 8.0 * math.sin(x / 47.0 - y / 63.0))
        for (mx, my, rr, top) in FAR_MESAS:
            d = math.hypot((x - mx) / rr[0], (y - my) / rr[1])
            if d < 1.25:
                edge = 1.0 + 0.08 * math.sin(math.atan2(y - my, x - mx) * 5 + mx)
                h = max(h, lerp(h, top, kit.smooth(max(0.0, min(1.0, (edge - d) / 0.12)))))
        return h

    return f


def land(c, oh, sc):
    X0, X1, Y0, Y1 = NEAR
    c.terrain("Land", X0, X1, Y0, Y1, 5.0, oh.natural, oh.classify, near=8.0, fade=6.0)
    nat = far_natural(oh)

    def far_classify(cen, n, info):
        if X0 + 22 < cen.x < X1 - 22 and Y0 + 22 < cen.y < Y1 - 22:
            return None
        if n.z < 0.6:
            return ("strata_red" if cen.z > 120 else "gold_cliff", "wall")
        return ("gold_sand", "loose_sand")

    def nat_far(x, y):
        dx = max(X0 - x, x - X1, 0.0)
        dy = max(Y0 - y, y - Y1, 0.0)
        d = max(dx, dy)
        return nat(x, y) - 1.5 * (1.0 - min(1.0, d / 45.0))

    fx0, fx1, fy0, fy1 = FAR
    far = c.terrain("Far Land", fx0, fx1, fy0, fy1, 36.0, nat_far, far_classify, near=0.0, fade=1.0)
    far["kp_role"] = "visual"

    def under(x, y):
        if c.nearest(x, y)[1] > 70:
            return None
        if oh.lake_d(x, y) > 3.0:
            return None  # the water's surface is the floor there (they overlap at the shore)
        nt = oh.natural(x, y)
        w, z = c.road_height(x, y, 8.0, 6.0, 0.2, nt)
        return min(nt, lerp(nt, z, w)) - 0.6

    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 5.0, under, c.lib("gold_sand", "loose_sand"))
    sc.ground_obs = list(c.coll("Terrain").objects)[:1]


# ------------------------------------------------------------------ the water


def lake(c, oh, sc):
    """The lake (and the canals) as one sheet of living water: shallow and bright at the
    shore, deepening to rich blue; foam lapping round the shore."""
    x0, x1, y0, y1 = oh._LAKE_BOX
    x1 = max(x1, max(p[0] for pts, _ in oh.CANALS for p in pts)) + 10
    cell = 4.0
    nx, ny = int((x1 - x0 + 16) / cell), int((y1 - y0 + 16) / cell)
    bm = bmesh.new()
    col = bm.loops.layers.color.new("Col")
    verts = {}
    depth = {}
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = x0 - 8 + i * cell
            y = y0 - 8 + j * cell
            d = oh.lake_d(x, y)
            if d > -3.0:
                verts[i, j] = bm.verts.new((x, y, 0.0))
                depth[i, j] = d
    shallow, deep = [], []
    for j in range(ny):
        for i in range(nx):
            q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            if not all(k in verts for k in q):
                continue
            f = bm.faces.new([verts[k] for k in q])
            dm = sum(depth[k] for k in q) / 4
            (deep if dm > 7.0 else shallow).append(f.index if f.index >= 0 else len(bm.faces) - 1)
            for loop, k in zip(f.loops, q):
                t = kit.smooth(max(0.0, min(1.0, (depth[k] - 1.0) / 38.0)))
                loop[col] = (lerp(1.0, 0.26, t), lerp(1.0, 0.52, t), lerp(0.94, 0.92, t), 1.0)
    bm.faces.index_update()
    shallow, deep = [], []
    for f in bm.faces:
        cx = sum(v.co.x for v in f.verts) / 4
        cy = sum(v.co.y for v in f.verts) / 4
        (deep if oh.lake_d(cx, cy) > 6.0 else shallow).append(f.index)
    me_name = "Lake"
    ob = c.mesh_object(me_name, bm, "Water", "both")
    c.assign(ob, c.lib("lagoon", "deep_water"), deep)
    c.assign(ob, c.lib("lagoon_shallow", "water"), shallow)
    # Our depth paint is the vertex colour: make it the painted layer.
    me = ob.data
    if "Col" in me.color_attributes:
        me.color_attributes.active_color = me.color_attributes["Col"]
    # Foam along the natural shores (beaches and banks; not the sea walls).
    foam = []
    run = []
    for p in oh.LAKE[::2]:
        if clear(c, p[0], p[1], 6.0) and math.hypot(p[0] - oh.PAVILION[0], p[1] - oh.PAVILION[1]) > 20:
            run.append((p[0], p[1], 2.4, 0.06))
        else:
            if len(run) > 3:
                foam.append(run)
            run = []
    if len(run) > 3:
        foam.append(run)
    for k, r in enumerate(foam):
        c.ribbon("Shore Foam %d" % (k + 1), r, 2.4, 0.06, c.lib("shore_foam"), role="visual")
    # Foam round the island.
    px, py = oh.PAVILION
    isle = [(px + (oh.ISLAND_R + 0.8) * math.cos(a), py + (oh.ISLAND_R + 0.8) * math.sin(a), 2.6, 0.06) for a in [k * math.tau / 72 for k in range(73)]]
    c.ribbon("Island Foam", isle, 2.6, 0.06, c.lib("shore_foam"), role="visual")


def falls(c, sc, name, x, lip_y, top, foot, w_top, w_bot, facing=-1, angle=0.0, throw=None, entity=True, veils=2):
    import props as pr

    th = throw if throw is not None else min(8.0, 2.0 + (top - foot) * 0.25)
    fx, fy = pr.falls(c, name, x, lip_y, top, foot, w_top, w_bot, facing=facing, throw=th, bulge=1.2, veils=veils,
                      foam_r=max(3.0, w_bot * 0.45), angle=angle, mats=("falls_oasis", "falls_veil", "falls_foam"))
    if entity:
        sc.falls.append((fx, fy, foot, top, w_bot, 0.0))
    return fx, fy


def mist(c, name, x, y, z, r, layers=2):
    return  # the spray is the waterfall entities' particles
    for k in range(layers):
        c.disc("%s %d" % (name, k + 1), x, y, r * (1 - 0.2 * k), z + 1.5 + k * 3.0, c.lib("canyon_mist"), role="visual", n=16, wobble=0.25, seed=k)


def channel(c, name, pts, z, w=6.0):
    """A stone-edged channel of flowing water along (x, y) points at height z."""
    c.ribbon(name, [(x, y, w, z) for x, y in pts], w, z, c.lib("canal_water", "water"), role="visual")
    m = Mesh()
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay) or 1.0
        nx, ny = -(by - ay) / L, (bx - ax) / L
        for side in (-1, 1):
            o = side * (w / 2 + 0.35)
            a = (ax + nx * o, ay + ny * o)
            b = (bx + nx * o, by + ny * o)
            m.add(("oasis_stone", "wall"), lambda bm, a=a, b=b: cuboid(bm, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, z + 0.1), (L + 0.6, 0.7, 0.9), math.atan2(by - ay, bx - ax)))
    m.build(c, name + " Edge", "Water")


def water_system(c, oh, sc):
    """The spring in the palace gardens and everything it feeds: the great cascades down
    the terraces east and west, the central stream into the aqueduct over the terrace
    road (its curtain) and its fall into the lake, the island's little falls."""
    T = oh.TERRACE_Y
    zt = (oh.Z_SHORE + 1.0, oh.Z_T1, oh.Z_T2, oh.Z_PALACE)
    # The spring: a pool in the palace gardens with a great fountain.
    sx, sy = 15.0, 424.0
    zs = oh.Z_PALACE
    c.disc("Spring Pool", sx, sy, 13.0, zs + 0.35, c.lib("canal_water", "water"), role="visual", n=28)
    m = Mesh()
    m.add(("oasis_stone", "wall"), lambda bm: loft(bm, [ring(bm, (sx, sy), r, z, 24) for r, z in ((13.6, zs - 0.5), (13.6, zs + 0.9), (12.8, zs + 0.9))], cap_top=False))
    m.add(("tile_border", "wall"), lambda bm: loft(bm, [ring(bm, (sx, sy), r, z, 24) for r, z in ((13.62, zs + 0.3), (13.62, zs + 0.8))], cap_top=False))
    m.build(c, "Spring Basin", "Water")
    sc.put(op.fountain(c, 1, 5.0), sx, sy, zs, coll="Water")
    sc.fountains.append((sx, sy, zs + 2.4 * 5.0 * 0.95, 9.0, 8, 7.0))
    # Channels east and west along the palace terrace to the cascade heads, and south to
    # the central fall.
    for side, xh in ((1, 160.0), (-1, -128.0)):
        channel(c, "Spring Channel %s" % ("East" if side > 0 else "West"), [(sx + side * 13.5, sy), (xh, sy), (xh, T[2] + 2.0)], zs + 0.25, 5.0)
    channel(c, "Spring Channel South", [(sx + 9.0, sy - 10.0), (24.0, T[2] + 2.0)], zs + 0.25, 4.0)
    # The great cascades: three tiers down the terraces, east and west, into the lake.
    for side, xc, wide in ((1, 160.0, 22.0), (-1, -128.0, 16.0)):
        for k in range(3):
            lip = T[2 - k]
            top = zt[3 - k]
            foot = zt[2 - k] if k < 2 else oh.Z_LAKE
            fy = lip - (5.0 + (top - foot) * 0.25 + 1.2)
            name = "Cascade %s %d" % ("East" if side > 0 else "West", k + 1)
            w = wide * (0.8 + 0.2 * k)
            fx_, fy_ = falls(c, sc, name, xc, lip, top - 0.1, foot + 0.2, w, w * 1.5, veils=3)
            if k < 2:
                # A pool at the foot, and the stream across the terrace to the next lip.
                c.disc(name + " Pool", fx_, fy_, w * 0.75, foot + 0.3, c.lib("canal_water", "water"), role="visual", n=20, wobble=0.15)
                channel(c, name + " Stream", [(fx_, fy_ - w * 0.4), (xc, T[1 - k] + 1.0)], foot + 0.25, w * 0.6)
            mist(c, name + " Mist", fx_, fy_, foot, w * 0.9)
        # A second, narrower fall beside the great one on the bottom tier.
        falls(c, sc, "Cascade %s Side" % ("East" if side > 0 else "West"), xc + side * 26.0, T[0], zt[1] - 0.2, 0.2, 6.0, 9.0, veils=1)
    # The central stream: from the T2 lip into the aqueduct over the terrace road.
    aq_x = 25.0
    channel(c, "Aqueduct Stream", [(24.0, T[2] - 2.0), (aq_x, T[1] + 2.0)], zt[2] + 0.25, 4.0)
    sc.aqueduct = aqueduct(c, oh, sc, aq_x)
    # The island's little falls, spilling off its garden terrace into the lake.
    px, py = oh.PAVILION
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        x = px + (oh.ISLAND_R - 1.0) * math.cos(a)
        y = py + (oh.ISLAND_R - 1.0) * math.sin(a)
        if not clear(c, x, y, 3.0):
            continue
        falls(c, sc, "Island Falls %d" % (k + 1), x, y, oh.Z_ISLAND - 0.3, 0.1, 8.0, 10.0, angle=a + math.pi / 2, veils=1, throw=2.5)


def aqueduct(c, oh, sc, x):
    """The aqueduct: a stone channel on arches carrying the stream from the second
    terrace's lip south over the terrace road and out over the first terrace's edge,
    where it pours into the lake. Where it crosses the road, water spills through a slot
    as a curtain the karts drive through."""
    T = oh.TERRACE_Y
    y0, y1 = T[1] - 1.0, T[0] - 4.0
    z = oh.Z_T2 - 1.0  # the channel's water
    m = Mesh()
    # The deck and its walls.
    m.add(("oasis_stone", "wall"), lambda bm: cuboid(bm, (x, (y0 + y1) / 2, z - 1.0), (7.0, y0 - y1, 1.6)))
    for side in (-1, 1):
        m.add(("oasis_stone", "wall"), lambda bm, side=side: cuboid(bm, (x + side * 3.2, (y0 + y1) / 2, z + 0.4), (0.6, y0 - y1, 1.6)))
        m.add(("tile_border", "wall"), lambda bm, side=side: cuboid(bm, (x + side * 3.55, (y0 + y1) / 2, z - 0.6), (0.1, y0 - y1, 0.6)))
    # Piers and arches down to the ground, leaving the road clear.
    road_y = [smp.p.y for smp in c.S if abs(smp.p.x - x) < 1.0 and y1 < smp.p.y < y0]
    ry = sum(road_y) / len(road_y) if road_y else (y0 + y1) / 2
    n = 6
    for k in range(n + 1):
        y = y0 + (y1 - y0) * k / n
        if abs(y - ry) < 13.0:
            continue
        g = oh.natural(x, y)
        m.add(("oasis_stone", "wall"), lambda bm, y=y, g=g: cuboid(bm, (x, y, (g - 2 + z - 1.8) / 2), (6.0, 3.0, z - 1.8 - g + 2)))
    # The great arch over the road.
    rz = c.nearest(x, ry)[0].p.z
    for side in (-1, 1):
        y = ry + side * 13.0
        m.add(("oasis_stone", "wall"), lambda bm, y=y: cuboid(bm, (x, y, (rz - 2 + z - 1.8) / 2), (6.5, 3.5, z - 1.8 - rz + 2)))

    def soffit(bm):
        rs = []
        for k in range(13):
            a = math.pi * k / 12
            y = ry - math.cos(a) * 11.25
            zz = rz + 6.5 + math.sin(a) * (z - 2.2 - rz - 6.5)
            rs.append([bm.verts.new((x + dx, y, zz + dz)) for dx, dz in ((-3.2, 0), (3.2, 0), (3.2, -0.01), (-3.2, -0.01))])
        loft(bm, rs, cap_top=False)

    m.add(("oasis_stone", "wall"), soffit)
    ob = m.build(c, "Aqueduct", COLL, "both")
    c.ribbon("Aqueduct Water", [(x, y0, 5.0, z), (x, y1, 5.0, z)], 5.0, z, c.lib("canal_water", "water"), role="visual")
    # The curtain over the road: a sheet falling from the slot to a grate in the road.
    w = c.nearest(x, ry)[0].w + 3.0
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    rows = []
    for j in range(7):
        t = j / 6
        zz = z - 1.8 - (z - 1.8 - rz) * t
        rows.append([bm.verts.new((x + (-w / 2 + w * i / 6), ry + 0.4 * math.sin(math.pi * t), zz)) for i in range(7)])
    for j in range(6):
        for i in range(6):
            f = bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
            for loop, (a, b) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                loop[uv].uv = (a / 6 * w / 6.0, -b / 6 * 2.0)
    cur = c.mesh_object("Aqueduct Curtain", bm, "Water", "visual")
    cur.data.materials.append(c.lib("falls_curtain_oasis"))
    materials.ensure_paint(cur.data)
    gx, gy, gz = c.game(x, ry, rz)
    c.entity("waterfall", x=gx, y=gy, z=gz, top=round(z - 1.5, 1), width=round(w, 1), heading=round(math.pi / 2, 3))
    # The aqueduct's end: its water pours over the first terrace's edge into the lake.
    falls(c, sc, "Aqueduct Falls", x, y1, z - 0.2, 0.2, 5.0, 9.0, veils=2)
    mist(c, "Aqueduct Mist", x, y1 - 8.0, 0.0, 9.0)
    return ob


# ------------------------------------------------------------------ gameplay


def gameplay(c, sc, oh):
    S = oh.SEG
    for at, across in ((32, 0), (S[2] + 20, 0), (S[7] + 40, 0), (S[11] + 30, 0), (S[13] + 30, 0), (S[16] + 20, 0), (S[18] + 80, 0), (S[22] + 50, 0)):
        c.zipper(at, across)
    for at, across in ((80, 0), (S[3] + 20, -3), (S[5] + 25, 0), (S[8] + 20, 3), (S[10] + 60, 0), (S[12] + 40, 0), (S[15] + 40, 3), (S[18] + 150, 0), (S[21] + 15, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in ((105, -5, "red"), (105, 5, "blue"), (S[2] + 50, 0, "green"), (S[4] + 20, 0, "yellow"), (S[8] + 50, -4, "rainbow"),
                            (S[8] + 50, 4, "red"), (S[10] + 30, 0, "blue"), (S[11] + 70, 0, "green"), (S[14] + 70, 0, "yellow"), (S[16] + 40, -4, "red"),
                            (S[16] + 40, 4, "rainbow"), (S[18] + 120, 0, "blue"), (S[20] + 50, 0, "green")):
        c.balloon(at, across, col)

    a = kit.s_near(c, *oh.SHORT[0])
    b = kit.s_near(c, *oh.SHORT[-1])
    apex = (a + b) / 2
    gates = c.checkpoints(
        extra=[S[1] + 40, S[3], S[4] + 30, S[7] + 20, S[8] + 40, S[10] + 40, S[11] + 60, S[12] + 50, S[14] + 40, S[15] + 50, S[17] + 30,
               S[18] + 100, a - 6, apex, b + 6, S[23]],
        avoid=[(a - 2, apex - 8), (apex + 8, b + 2)],
        height=9.0,
    )
    main_gate = min(gates.items(), key=lambda kv: abs(kv[0] - apex))[1]
    pts = oh.SHORT
    mid = len(pts) // 2
    z = c.nearest(*pts[mid])[0].p.z
    c.alt_gate(main_gate, "canal_passage", [(x, y, z) for x, y in pts[mid - 1:mid + 2]], width=14.0)

    # The living resort.
    for x, y, foot, top, w, h in sc.falls:
        gx, gy, gz = c.game(x, y, foot)
        c.entity("waterfall", x=gx, y=gy, z=gz, top=round(top, 1), width=round(w, 1), heading=0)
    for x, y, z, hgt, jets, r in sc.fountains:
        game_entity(c, "fountain", x, y, z, height=hgt, jets=jets, radius=r)
    for k, (x, y, z, hd, dance) in enumerate(sc.guests):
        gx, gy, gz = c.game(x, y, z)
        c.entity("partygoer", x=gx, y=gy, z=gz, heading=round(hd, 3), variant=k % 6, dance=dance)
    # Gulls wheeling over the lake.
    for k, (x, y, z, r, n) in enumerate(((0.0, -60.0, 45.0, 70.0, 3), (110.0, 190.0, 55.0, 50.0, 2), (-110.0, 60.0, 50.0, 60.0, 3))):
        game_entity(c, "birds", x, y, z, radius=r, count=n, speed=round(0.2 + 0.04 * k, 2), seed=k + 4, color="#f6f8fa")
    c.entity("sparkles", rate=6, radius=40)


def boats(c, oh, sc):
    """Little sailing boats going round the open water (paths that keep clear of the
    island, the bridge and the causeway)."""
    loops = [((-20.0, -70.0), 105.0, 55.0, 3.6, ["#e02a2a", "#f6c03a"]), ((-60.0, 30.0), 60.0, 35.0, 3.0, ["#2a6ad8", "#f6f2e6"]),
             ((120.0, 200.0), 45.0, 28.0, 3.2, ["#16a8a0", "#ff8a2a"]), ((-110.0, 195.0), 34.0, 26.0, 2.6, ["#e8388a", "#ffe050"]),
             ((40.0, -110.0), 60.0, 30.0, 4.0, ["#f6f2e6", "#2a6ad8"])]
    for k, ((cx, cy), rx, ry, speed, cols) in enumerate(loops):
        pts = [(cx + rx * math.cos(a), cy + ry * math.sin(a), 0.0) for a in [j * math.tau / 24 for j in range(24)]]
        c.path_curve("Boat Path %d" % (k + 1), pts, z=0.0, closed=True)
        c.entity("boat", route="Boat Path %d" % (k + 1), speed=speed, start=round(k * 37.0, 1), colors=cols, scale=1.0 + 0.15 * (k % 2))


def build(c, oh):
    sc = Scene(c, oh)
    land(c, oh, sc)
    c.start_line()
    lake(c, oh, sc)
    water_system(c, oh, sc)
    import oasis_resort as res

    res.build(c, oh, sc)
    boats(c, oh, sc)
    gameplay(c, sc, oh)
    groups = ("Props", "Plants", "Market", "Gardens")
    c.merge_props(groups)
    ter = list(c.coll("Terrain").objects)
    built = list(c.coll(COLL).objects)
    c.preset("sun", ter + built, 0.22)
    c.preset("bottoms", ter, 0.3)
    kit.paint.shade_roads(c.pieces, 0.2)
