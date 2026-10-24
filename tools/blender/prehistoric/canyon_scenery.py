# Canyon Dash's scenery (see canyon_dash.py): the land near and far, the river and the
# waterfalls, the Sandstone Arch, the Great Canyon Bridge, the pass and its tunnel, the
# buttes and the great butte's slot, the outpost at the start, the plants, the light,
# and the gameplay entities. Built from the kit in canyon_props.py.
# SPDX-License-Identifier: MIT

import math

import canyon_props as cp
import course_kit as kit
from course_kit import Vector, bmesh, lerp, rnd
from props import blob, cuboid, loft

FAR = (-2600.0, 2000.0, -1900.0, 1900.0)
NEAR = (-420.0, 680.0, -330.0, 330.0)


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


def game_entity(c, kind, x, y, z, **extra):
    gx, gy, gz = c.game(x, y, z)
    c.entity(kind, x=gx, y=gy, z=gz, **extra)


def road_rot(q):
    return math.atan2(q.t.y, q.t.x)


class Scene:
    """What the scenery builders share: copies to place, lights, the waterfalls."""

    def __init__(self, c, cd):
        self.c = c
        self.cd = cd
        self.fires = []
        self.falls = []

    def put(self, proto, x, y, z, rot=0.0, scale=1.0, coll="Props", role="visual"):
        return self.c.place(proto, x, y, z, rot, scale, coll=coll, role=role)


def clear(c, x, y, margin):
    return c.nearest(x, y)[1] > margin


# ------------------------------------------------------------------ the land


def far_natural(cd):
    """Beyond the race: the canyon running on west to the horizon, widening, with its
    temples (isolated buttes) standing in it, and mesas and buttes all round."""

    def f(x, y):
        h = cd.natural(x, y)
        # Far mesas: flat-topped blocks rising out of the plateau, in a broken ring.
        for (mx, my, r, top) in FAR_MESAS:
            d = math.hypot((x - mx) / r[0], (y - my) / r[1])
            if d < 1.25:
                edge = 1.0 + 0.08 * math.sin(math.atan2(y - my, x - mx) * 5 + mx)
                k = kit.smooth(max(0.0, min(1.0, (edge - d) / 0.12)))
                h = max(h, lerp(h, top, k))
        return h

    return f


# (x, y, (radius x, radius y), top) — big flat-topped mesas far off, all round.
FAR_MESAS = [
    (-900.0, 620.0, (260.0, 160.0), 150.0),
    (-300.0, 760.0, (300.0, 140.0), 175.0),
    (420.0, 820.0, (240.0, 170.0), 160.0),
    (1150.0, 520.0, (200.0, 260.0), 190.0),
    (1300.0, -300.0, (180.0, 300.0), 170.0),
    (900.0, -950.0, (300.0, 160.0), 185.0),
    (100.0, -1050.0, (260.0, 140.0), 160.0),
    (-700.0, -800.0, (240.0, 180.0), 175.0),
    (-1500.0, -500.0, (300.0, 160.0), 165.0),
    (-1700.0, 600.0, (260.0, 200.0), 180.0),
    (-2200.0, 0.0, (200.0, 380.0), 200.0),
    (700.0, 260.0, (70.0, 110.0), 110.0),
    (820.0, -420.0, (90.0, 70.0), 115.0),
]


def land(c, cd, sc):
    X0, X1, Y0, Y1 = NEAR
    c.terrain("Land", X0, X1, Y0, Y1, 5.0, cd.natural, cd.classify, near=9.0, fade=5.0)
    # The far land: coarse, only to be seen (no collision), with a hole over the near.
    nat = far_natural(cd)

    def far_classify(cen, n, info):
        if X0 + 22 < cen.x < X1 - 22 and Y0 + 22 < cen.y < Y1 - 22:
            return None
        if cd.walled(cen.x, cen.y, 0.0):
            return None
        if n.z < 0.55:
            return (cd._layer(cen.z), "wall")
        if n.z < 0.8:
            return ("talus", "loose_sand")
        if cd.gorge_u(cen.x, cen.y) > 3 and cen.z < cd.Z_RIVER + 3:
            return ("strata_purple", "wall")
        return (cd.ground_mat(cen.x, cen.y), "loose_sand")

    def nat_far(x, y):
        # A little lower just outside the near land, so the two never fight.
        dx = max(X0 - x, x - X1, 0.0)
        dy = max(Y0 - y, y - Y1, 0.0)
        d = max(dx, dy)
        return nat(x, y) - (1.5 * (1.0 - min(1.0, d / 45.0)) if d > 0 or (X0 <= x <= X1 and Y0 <= y <= Y1) else 0.0)

    fx0, fx1, fy0, fy1 = FAR
    far = c.terrain("Far Land", fx0, fx1, fy0, fy1, 36.0, nat_far, far_classify, near=0.0, fade=1.0)
    far["kp_role"] = "visual"

    def under(x, y):
        if c.nearest(x, y)[1] > 60:
            return None
        h = cd.underfloor_z(x, y)
        if h is None:
            return None
        nt = cd.natural(x, y)
        w, z = c.road_height(x, y, 9.0, 5.0, 0.2, nt)
        return min(h, lerp(nt, z, w) - 0.6)

    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 5.0, under, c.lib("desert_sand", "loose_sand"))
    c.underfloor_flat("Gorge Floor", X0, X1, Y0, Y1, 6.0, cd.abyss_z, c.lib("strata_purple", "abyss"))


# ------------------------------------------------------------------ rock


def strata_paint(c, ob, cd, top=("slickrock", "dirt"), shift=0.0):
    """Paint a rock solid like the canyon walls: its faces by height in the same layers,
    flat tops as slickrock."""
    groups = {}
    for p in ob.data.polygons:
        if p.normal.z > 0.75:
            m = top
        else:
            m = (cd._layer(p.center.z + shift), "wall")
        groups.setdefault(m, []).append(p.index)
    for m, faces in groups.items():
        c.assign(ob, c.lib(*m), faces)
    ob.data.shade_flat()


BUTTE_BANDS = [(1.0, 0.0), (0.9, 0.08), (0.72, 0.2), (0.66, 0.26), (0.64, 0.6), (0.6, 0.66), (0.58, 0.9), (0.62, 0.94), (0.6, 1.0)]
SPIRE_BANDS = [(1.0, 0.0), (0.8, 0.12), (0.55, 0.22), (0.5, 0.5), (0.42, 0.56), (0.4, 0.86), (0.45, 0.9), (0.4, 1.0)]


def butte(c, cd, name, x, y, rx, ry, top, base=None, seed=0, angle=0.0, bands=BUTTE_BANDS, coll="Buttes", role="both"):
    """A butte or spire: an irregular footprint (big lobes, smaller bays, vertical flutes
    down its cliffs), a talus skirt, a sheer layered cliff, ledges and the caprock, each
    level eroded a little differently. Painted in the canyon's layers."""
    base = cd.natural(x, y) if base is None else base
    n = 44
    r = rnd
    ph = [r(seed * 7 + k) * math.tau for k in range(8)]
    amp = (0.2 + 0.12 * r(seed * 3 + 1), 0.12 + 0.08 * r(seed * 3 + 2), 0.05, 0.035)

    def foot(a, lvl):
        return (1.0 + amp[0] * math.sin(2 * a + ph[0]) + amp[1] * math.sin(3 * a + ph[1] + 0.3 * lvl)
                + amp[2] * math.sin(7 * a + ph[2] + 0.8 * lvl) + amp[3] * math.sin(13 * a + ph[3] + 1.7 * lvl))

    ca, sa = math.cos(angle), math.sin(angle)
    bm = bmesh.new()
    rings = []
    z0 = base - 12.0
    for lvl, (scale, f) in enumerate([(bands[0][0], None)] + list(bands)):
        z = z0 if f is None else base + f * (top - base)
        ring_ = []
        for i in range(n):
            a = i * math.tau / n
            k = scale * foot(a, lvl) * (1.0 + 0.03 * (r(i * 13 + lvl * 7 + seed) - 0.5))
            px, py = rx * k * math.cos(a), ry * k * math.sin(a)
            ring_.append(bm.verts.new((x + px * ca - py * sa, y + px * sa + py * ca, z)))
        rings.append(ring_)
    for lo, hi in zip(rings, rings[1:]):
        for i in range(n):
            bm.faces.new((lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i]))
    bm.faces.new(list(reversed(rings[0])))
    # The top: a low dome to a centre point, a little off-centre.
    cv = bm.verts.new((x + rx * 0.1 * math.cos(ph[4]), y + ry * 0.1 * math.sin(ph[4]), top + 1.5))
    for i in range(n):
        bm.faces.new((rings[-1][i], rings[-1][(i + 1) % n], cv))
    ob = c.mesh_object(name, bm, coll, role)
    strata_paint(c, ob, cd)
    return ob


def white_paint(ob):
    """Booleans leave the new faces' vertex paint black: start every corner white again."""
    from course_kit import materials

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


def path_cutter(c, pts, half, z0, z1, name="Slot"):
    """A closed prism along a polyline (x, y, z_floor) points: a slot or a tunnel."""
    bm = bmesh.new()
    rings = []
    n = len(pts)
    for i, (x, y, zf) in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        t = Vector((b[0] - a[0], b[1] - a[1], 0)).normalized()
        r = Vector((t.y, -t.x, 0))
        p = Vector((x, y, 0))
        hw = half(i / (n - 1)) if callable(half) else half
        rings.append([bm.verts.new(p + r * o + Vector((0, 0, zf + dz))) for o, dz in ((-hw, z0), (hw, z0), (hw * 1.1, z1), (-hw * 1.1, z1))])
    for lo, hi in zip(rings, rings[1:]):
        for k in range(4):
            bm.faces.new((lo[k], lo[(k + 1) % 4], hi[(k + 1) % 4], hi[k]))
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return c.mesh_object(name, bm, "Buttes", "visual")


# ------------------------------------------------------------------ the arch


def arch(c, cd, name, centre, axis, span, rise, base, width, rib, seed=0, lean=0.0, role="both", coll="Arch", up_into=0.0):
    """A natural sandstone arch: a thick rib of layered rock springing from `base` at
    both feet, `span` metres apart along `axis` (a unit (x, y) vector), its soffit
    `rise` metres up; `width` thick (across the axis) and `rib` deep. Irregular: it
    thickens to its feet, its section wobbles, one side can lean. `up_into` extends the
    second foot up into a cliff (it springs from a wall)."""
    ax = Vector((axis[0], axis[1], 0)).normalized()
    across = Vector((-ax.y, ax.x, 0))
    cx, cy = centre
    bm = bmesh.new()
    rings = []
    N = 26
    sec = 10
    for k in range(N + 1):
        t = k / N
        ang = math.pi * (1 - t)
        # The centre line of the rib: an ellipse over the soffit, feet sunk into the ground.
        o = math.cos(ang) * (span / 2 + rib / 2)
        zc = base + math.sin(ang) * (rise + rib / 2)
        if t > 0.5:
            zc += up_into * kit.smooth((t - 0.5) * 2) ** 2
        foot = 1.0 + 0.5 * (1 - math.sin(ang)) ** 2
        p = Vector((cx, cy, 0)) + ax * o + Vector((0, 0, zc)) + across * lean * math.sin(ang)
        # The section's own frame: radial (out from the ellipse) and across.
        nrm = Vector((math.cos(ang) * (rise + rib / 2), 0, math.sin(ang) * (span / 2 + rib / 2)))
        radial = (ax * nrm.x + Vector((0, 0, nrm.z))).normalized()
        ring_ = []
        for j in range(sec):
            a = j * math.tau / sec
            wob = 1.0 + 0.14 * math.sin(a * 3 + k * 0.9 + seed) + 0.08 * math.sin(a * 5 - k * 1.3 + seed * 2)
            ring_.append(bm.verts.new(p + across * math.cos(a) * width / 2 * foot * wob + radial * math.sin(a) * rib / 2 * foot ** 0.6 * wob))
        rings.append(ring_)
    loft(bm, rings, cap_top=True, cap_bottom=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = c.mesh_object(name, bm, coll, role)
    strata_paint(c, ob, cd, top=("strata_cream", "wall"))
    return ob


# ------------------------------------------------------------------ water


def river(c, sc, cd):
    """The river at the bottom of the inner gorge, from the plunge pool at its head west
    to the horizon; the river above the falls, across the eastern plateau."""
    pts = []
    x = cd.X_HEAD - 4.0
    while x > FAR[0] + 40:
        k = max(0.7, min(1.7, cd.gorge_hw(min(x, cd.X_HEAD)) / 42.0))
        floor = max(8.0, cd.gorge_hw(x) - 29.5 * k)
        w = max(10.0, min(46.0, floor * 1.3))
        pts.append((x, cd.gorge_c(x) + 4.0 * math.sin(x / 47.0), w))
        x -= 12.0 if x > -600 else 30.0
    c.ribbon("River", list(reversed(pts)), 20.0, cd.Z_RIVER + 0.5, c.lib("canyon_river", "abyss"), role="visual", steps=2)
    # From the shelf fall's pool to the gorge's lip (under the road), and on the shelf.
    lx, _ = sc.lip
    px = cd.POOL[0]
    low = [(x, cd.river_y(x), 13.0) for x in [lx - 2.0 + k * 4.0 for k in range(int((px - lx) / 4.0) + 1)]]
    c.ribbon("Upper River", low, 13.0, 41.9, c.lib("canyon_river", "water"), role="visual")
    c.disc("Shelf Pool", px, cd.river_y(px), cd.POOL[2] + 2.0, 42.4, c.lib("canyon_river", "water"), role="visual", n=24, wobble=0.15)
    face = cd.shelf_x(cd.river_y(px + 30))
    hi = []
    x = face - 1.0
    while x < FAR[1] - 40:
        hi.append((x, cd.river_y(x), 12.0))
        x += 8.0 if x < 760 else 40.0
    c.ribbon("Shelf River", hi, 12.0, cd.SHELF_TOP - 6.4, c.lib("canyon_river", "water"), role="visual")


def head_falls(c, sc, cd):
    """The twin falls at the canyon's head. The river leaps off the East Shelf beside the
    road into its pool, runs under the road's stone bridge, then plunges 80 m over the
    gorge's head into the river below."""
    import props as pr

    mats = ("falls_dash", "falls_veil", "falls_foam")
    lx, ly = sc.lip
    fx, fy = pr.falls(c, "Head Falls", lx, ly, 41.8, cd.Z_RIVER + 0.4, 15.0, 30.0, facing=-1, throw=10.0, bulge=2.2, veils=3,
                      foam_r=24.0, angle=-math.pi / 2, mats=mats)
    sc.falls.append((fx, fy, cd.Z_RIVER, 41.6, 26.0, -math.pi / 2))
    for k, off in enumerate((-13.0, 12.0)):
        pr.falls(c, "Head Falls Side %d" % (k + 1), lx - 1.5, ly + off, 41.4, cd.Z_RIVER + 0.4, 3.5, 7.0, facing=-1, throw=6.5, bulge=0.8,
                 veils=1, foam=False, angle=-math.pi / 2, mats=mats)
    # The shelf fall: off the East Shelf's rim, beside the road.
    py = cd.river_y(cd.POOL[0])
    face = cd.shelf_x(py)
    top = cd.SHELF_TOP - 6.6
    sx, sy = pr.falls(c, "Shelf Falls", face + 0.5, py, top, 42.6, 13.0, 24.0, facing=-1, throw=8.0, bulge=2.0, veils=3,
                      foam_r=15.0, angle=-math.pi / 2, mats=mats)
    sc.falls.append((sx, sy, 42.4, top, 20.0, -math.pi / 2))
    for k, off in enumerate((-10.0, 11.0)):
        pr.falls(c, "Shelf Falls Side %d" % (k + 1), face + 0.5, py + off, top - 2.0, 42.6, 3.0, 6.0, facing=-1, throw=5.0, bulge=0.6,
                 veils=1, foam=False, angle=-math.pi / 2, mats=mats)


def side_falls(c, sc, cd):
    """Waterfalls downstream: off the north mesa's cliff onto the terrace, a creek across
    the terrace, and over the inner gorge's rim into the river; and others spilling off
    the terraces into the gorge."""
    import props as pr

    mats = ("falls_dash", "falls_veil", "falls_foam")
    for x, side, wtop, mesa in ((-330.0, 1, 8.0, True), (-560.0, -1, 9.0, False), (-70.0, 1, 5.0, False), (-820.0, 1, 10.0, True)):
        cy = cd.gorge_c(x)
        y = cy
        while cd.gorge_u(x, y) > 0.5:
            y += side * 1.0
        top = cd.natural_outer(x, y + side * 4.0) - 0.2
        foot = cd.Z_RIVER + 0.4
        pr.falls(c, "Gorge Falls %d" % int(-x), x, y, top, foot, wtop, wtop * 2.0, facing=-side, throw=5.0, bulge=1.2, veils=2, foam_r=wtop * 1.4,
                 mats=mats)
        sc.falls.append((x, y - side * 8.0, foot, top, wtop * 1.5, 0.0 if side > 0 else math.pi))
        # The creek across the terrace, from the foot of the mesa's fall (or a spring).
        if mesa and side > 0:
            rim = cd.north_rim(x)
            foot_y = rim - sum(w for w, _ in cd.MESA_BANDS)
            n = max(3, int((foot_y - y) / 8.0))
            creek = [(x + 2.5 * math.sin(k * 0.9), y + 1.0 + (foot_y - 4.0 - y) * k / n, 5.0) for k in range(n + 1)]
            mt = cd.mesa_top(x, rim + 2.0) or cd.natural_outer(x, rim + 2.0)
            pr.falls(c, "Mesa Falls %d" % int(-x), x, rim + 1.0, mt - 0.3, top + 0.3, 6.0, 12.0, facing=-1, throw=6.0, bulge=1.4, veils=2,
                     foam_r=8.0, mats=mats)
            sc.falls.append((x, foot_y - 6.0, top, mt, 10.0, 0.0))
        else:
            creek = [(x + 3.0 * math.sin(k * 0.7), y + side * (2.0 + k * 9.0), 4.5) for k in range(9)]
        c.ribbon("Creek %d" % int(-x), creek, 4.5, top + 0.15, c.lib("canyon_river", "water"), role="visual")


# ------------------------------------------------------------------ the big landmarks


def great_arch(c, sc, cd):
    """The Sandstone Arch: springing from the terrace on the canyon side of the road,
    over it, into the rim's cliff on the other: the road runs right under it."""
    S = cd.SEG
    q = c.at(S[6] + 26.0)
    across = q.r  # toward the canyon (north)
    mid = q.p + across * 1.0
    base = cd.terrace_z(mid.x) - 8.0
    rise = q.p.z - base + 30.0
    rise = q.p.z - base + 38.0
    ob = arch(c, cd, "Sandstone Arch", (mid.x, mid.y), (across.x, across.y), 54.0, rise, base, 24.0, 17.0, seed=3, lean=2.5,
              up_into=10.0)
    sc.arch = ob
    # Smaller arches and windows out in the canyon (scenery only).
    arch(c, cd, "Window Arch", (-470.0, -175.0), (0.8, 0.6), 30.0, 26.0, cd.terrace_z(-470) - 4, 10.0, 8.0, seed=7, role="visual", coll="Buttes")
    arch(c, cd, "Far Arch", (-1120.0, 260.0), (1.0, 0.2), 60.0, 50.0, 18.0, 16.0, 14.0, seed=11, role="visual", coll="Buttes")
    return ob


def buttes(c, sc, cd):
    """The buttes and spires: temples standing in the outer canyon west of the bridge,
    towers along the Mesa Run, and the great butte with the slot through it."""
    # In the canyon (on the terraces), seen from the bridge and through the arch.
    for k, (x, y, rx, ry, top) in enumerate(((-440.0, 150.0, 34.0, 26.0, 84.0), (-620.0, -150.0, 46.0, 30.0, 92.0), (-860.0, 175.0, 52.0, 40.0, 100.0),
                                              (-1150.0, -185.0, 70.0, 46.0, 110.0), (-1500.0, 140.0, 80.0, 50.0, 120.0), (-330.0, -175.0, 22.0, 18.0, 70.0),
                                              (-760.0, -70.0, 26.0, 20.0, 46.0), (-1000.0, 40.0, 30.0, 24.0, 40.0))):
        butte(c, cd, "Temple %d" % (k + 1), x, y, rx, ry, top, base=cd.terrace_z(x) - 10.0 if abs(y - cd.gorge_c(x)) > cd.gorge_hw(x) else cd.Z_RIVER,
              seed=k * 3 + 1, angle=k * 0.7, role="visual")
    # Along the Mesa Run and round the start.
    for k, (x, y, rx, ry, top, sp) in enumerate(((620.0, 120.0, 26.0, 22.0, 170.0, 1), (650.0, -140.0, 44.0, 30.0, 150.0, 0), (480.0, -260.0, 18.0, 15.0, 120.0, 1),
                                                  (350.0, -300.0, 48.0, 34.0, 112.0, 0), (140.0, -275.0, 36.0, 26.0, 104.0, 0), (20.0, -240.0, 16.0, 14.0, 108.0, 1),
                                                  (590.0, -40.0, 12.0, 10.0, 150.0, 1), (420.0, -330.0, 12.0, 11.0, 104.0, 1), (690.0, 20.0, 30.0, 24.0, 160.0, 0),
                                                  (595.0, 210.0, 14.0, 12.0, 160.0, 1), (450.0, -205.0, 9.0, 8.0, 86.0, 1))):
        butte(c, cd, "Butte %d" % (k + 1), x, y, rx, ry, top, seed=k * 5 + 2, angle=k * 1.1, bands=SPIRE_BANDS if sp else BUTTE_BANDS,
              role="both" if c.nearest(x, y)[1] < max(rx, ry) + 60 else "visual")
    # The great butte, and the slot through it.
    bx, by = cd.BUTTE
    rx, ry = cd.BUTTE_SIZE
    g = butte(c, cd, "Great Butte", bx, by, rx, ry, 98.0, seed=17, angle=cd.BUTTE_ANGLE)
    pts = [(x, y, c.nearest(x, y)[0].p.z if False else _short_z(c, cd, x, y)) for x, y in cd.BUTTE_SHORT]
    cutter = path_cutter(c, pts, lambda t: 4.8 + 1.0 * math.sin(t * 7.0), -0.35, 140.0, name="Slot Cutter")
    cut(c, g, cutter)
    white_paint(g)
    strata_paint(c, g, cd)
    rough_slot(c, g, pts, 4.8 + 1.0)
    sc.butte = g
    # A boulder wedged high in the slot.
    m = Mesh()
    mx, my = cd.BUTTE_SHORT[len(cd.BUTTE_SHORT) // 2]
    m.add(("strata_orange", "wall"), lambda bm: blob(bm, (mx, my, 84.0), 6.5, sx=0.9, sy=1.2, sz=0.8))
    m.build(c, "Chockstone", "Buttes", "visual")


def rough_slot(c, solid, pts, half):
    """The boolean leaves the slot's walls (and where it cuts the talus skirt) as big flat
    planes. Break them up for the eye only: a visual copy of the butte with those faces
    cut finer and pushed back into the rock by up to a metre, in lumps; the original
    stays as the collision (so the slot drives exactly as before)."""
    me = solid.data.copy()
    look = kit.bpy.data.objects.new(solid.name + " Look", me)
    look.matrix_world = solid.matrix_world.copy()
    for coll in solid.users_collection:
        coll.objects.link(look)
    solid["kp_role"] = "collision"
    look["kp_role"] = "visual"
    line = [(x, y) for x, y, _ in pts]

    def near(x, y):
        best = (1e9, 0.0, 0.0)
        for (ax, ay), (bx, by) in zip(line, line[1:]):
            dx, dy = bx - ax, by - ay
            t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
            qx, qy = ax + t * dx, ay + t * dy
            d = math.hypot(x - qx, y - qy)
            if d < best[0]:
                best = (d, qx, qy)
        return best

    bm = bmesh.new()
    bm.from_mesh(me)
    faces = []
    for f in bm.faces:
        cx, cy, _ = f.calc_center_median()
        if abs(f.normal.z) < 0.85 and near(cx, cy)[0] < half + 2.5:
            faces.append(f)
    bmesh.ops.triangulate(bm, faces=faces)
    edges = {e for f in bm.faces for e in f.edges if all(near(v.co.x, v.co.y)[0] < half + 2.5 for v in e.verts)}
    long = [e for e in edges if e.calc_length() > 2.5]
    for _ in range(3):
        if not long:
            break
        bmesh.ops.subdivide_edges(bm, edges=long, cuts=1, use_grid_fill=False)
        bm.edges.ensure_lookup_table()
        long = [e for e in bm.edges if e.calc_length() > 2.5 and all(near(v.co.x, v.co.y)[0] < half + 2.5 for v in e.verts)]
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    for v in bm.verts:
        d, qx, qy = near(v.co.x, v.co.y)
        if d > half + 2.5 or d < 0.3:
            continue
        ox, oy = (v.co.x - qx) / d, (v.co.y - qy) / d
        x, y, z = v.co
        lump = 0.5 + 0.5 * math.sin(x * 0.55 + z * 0.8) * math.cos(y * 0.6 - z * 0.45)
        push = 1.0 * lump * min(1.0, (half + 2.5 - d) / 1.5)
        v.co.x += ox * push
        v.co.y += oy * push
    bm.to_mesh(me)
    bm.free()
    me.shade_flat()
    return look


def _short_z(c, cd, x, y):
    smp, _ = c.nearest(x, y)
    return smp.p.z


def tunnel(c, sc, cd):
    """The natural tunnel in the pass: a great block of the mesa's rock bridging the slot,
    the road bored through it, a shaft of daylight through its roof."""
    s0, s1 = cd.TUNNEL_S
    mid = c.at((s0 + s1) / 2)
    L = s1 - s0
    mx, my, ang, rx, ry = cd.tunnel_rock()
    rock = c.rock_mass("Tunnel Rock", mx, my, rx, ry, cd.MESA_TOP - 4.0, z0=mid.p.z - 10.0, n=24, seed=5, angle=ang,
                       bands=[(1.0, 0.0), (1.0, 0.4), (0.95, 0.7), (0.85, 1.0)], base=mid.p.z - 10.0)
    c.link(rock, "Pass")
    rock["kp_role"] = "both"
    c.tunnel(rock, s0, s1, half=c.width / 2 + 3.0, height=11.0, pad=34.0)
    # A shaft of daylight down through the roof, near the middle.
    q = c.at(s0 + L * 0.55)
    bm = bmesh.new()
    lo = [bm.verts.new((q.p.x + 5.5 * math.cos(k * math.tau / 10), q.p.y + 4.0 * math.sin(k * math.tau / 10), q.p.z + 6.0)) for k in range(10)]
    hi = [bm.verts.new((q.p.x + 2.0 + 7.5 * math.cos(k * math.tau / 10), q.p.y + 6.0 * math.sin(k * math.tau / 10), cd.MESA_TOP + 20)) for k in range(10)]
    loft(bm, [lo, hi], cap_top=True, cap_bottom=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cut(c, rock, c.mesh_object("Shaft Cutter", bm, "Pass", "visual"))
    white_paint(rock)
    strata_paint(c, rock, cd)
    sc.tunnel = (s0, s1, rock)
    sc.tunnel_light = [(c.at(s).p.x, c.at(s).p.y, c.at(s).p.z + 4) for s in (s0 - 6, s1 + 6)] + [(q.p.x, q.p.y, q.p.z + 3)]
    return rock


# ------------------------------------------------------------------ timber and stone


def pieces_of(c, kind):
    return [ob for ob in c.pieces if ob.name.endswith(" " + kind)]


def ground_at(c, cd, x, y):
    """The land under (x, y) (the terrain as built, else the natural land)."""
    z = c.ground_z(x, y, list(c.coll("Terrain").objects)[:1])
    return z if z is not None else cd.natural(x, y)


def great_bridge(c, sc, cd):
    """The Great Canyon Bridge: masonry piers rising out of the river and off the
    gorge's ledges, timber towers on them carrying a lattice of trusses under the deck,
    and timber portals with banners at both ends."""
    timber = ("weathered_timber", "wall")
    stone = ("masonry", "wall")
    m = Mesh()
    for ob in pieces_of(c, "bridge"):
        s0, s1 = ob["kp_from"], ob["kp_to"]
        if s1 < s0:
            s1 += c.length
        L = s1 - s0
        n = max(2, int(round(L / 26.0)))
        tops = []
        for k in range(n + 1):
            q = c.at(s0 + L * k / n)
            rot = road_rot(q)
            g = ground_at(c, cd, q.p.x, q.p.y)
            deck = q.p.z - 2.4
            stone_top = min(deck - 12.0, g + 48.0) if deck - g > 20 else g + 1.0
            if stone_top > g + 1.0:
                # A tapering masonry pier with a cutwater, a cornice under the timber.
                hgt = stone_top - g + 6.0
                m.add(stone, lambda bm, q=q, g=g, hgt=hgt, rot=rot: cuboid(bm, (q.p.x, q.p.y, g - 6.0 + hgt / 2), (9.0, 15.0, hgt), rot))
                m.add(stone, lambda bm, q=q, g=g, rot=rot: cuboid(bm, (q.p.x, q.p.y, g + 4.0), (11.0, 17.0, 20.0), rot))
                m.add(stone, lambda bm, q=q, st=stone_top, rot=rot: cuboid(bm, (q.p.x, q.p.y, st - 0.6), (9.4, 14.4, 1.2), rot))
            tops.append((q, stone_top, deck, rot))
        # Timber towers on the piers: four posts across, girts, X bracing.
        for q, st, deck, rot in tops:
            if deck - st < 2.0:
                continue
            posts = [q.side(o) for o in (-5.5, -2.0, 2.0, 5.5)]
            for p in posts:
                m.add(timber, lambda bm, p=p, st=st, deck=deck: cp._beam(bm, (p.x, p.y, st), (p.x, p.y, deck), 0.9))
            levels = max(1, int((deck - st) / 6.0))
            for j in range(levels + 1):
                z = st + (deck - st) * j / levels
                m.add(timber, lambda bm, a=posts[0], b=posts[-1], z=z: cp._beam(bm, (a.x, a.y, z), (b.x, b.y, z), 0.45))
                if j < levels:
                    z2 = st + (deck - st) * (j + 1) / levels
                    for pa, pb in zip(posts, posts[1:]):
                        m.add(timber, lambda bm, pa=pa, pb=pb, z=z, z2=z2: cp._beam(bm, (pa.x, pa.y, z), (pb.x, pb.y, z2), 0.3))
                        m.add(timber, lambda bm, pa=pa, pb=pb, z=z, z2=z2: cp._beam(bm, (pb.x, pb.y, z), (pa.x, pa.y, z2), 0.3))
        # Trusses between the towers under each side of the deck.
        for (qa, _, da, _), (qb, _, db, _) in zip(tops, tops[1:]):
            for o in (-5.5, 5.5):
                a, b = qa.side(o), qb.side(o)
                top_a, top_b = da, db
                bot_a, bot_b = da - 6.0, db - 6.0
                m.add(timber, lambda bm, a=a, b=b, za=bot_a, zb=bot_b: cp._beam(bm, (a.x, a.y, za), (b.x, b.y, zb), 0.55))
                m.add(timber, lambda bm, a=a, b=b, za=top_a, zb=top_b: cp._beam(bm, (a.x, a.y, za), (b.x, b.y, zb), 0.55))
                panels = 4
                for j in range(panels):
                    t0, t1 = j / panels, (j + 1) / panels
                    pa = a.lerp(b, t0)
                    pb = a.lerp(b, t1)
                    z0t, z1t = lerp(top_a, top_b, t0), lerp(top_a, top_b, t1)
                    z0b, z1b = z0t - 6.0, z1t - 6.0
                    m.add(timber, lambda bm, pa=pa, pb=pb, z0b=z0b, z1t=z1t: cp._beam(bm, (pa.x, pa.y, z0b), (pb.x, pb.y, z1t), 0.35))
                    m.add(timber, lambda bm, pa=pa, z0b=z0b, z0t=z0t: cp._beam(bm, (pa.x, pa.y, z0b), (pa.x, pa.y, z0t), 0.35))
            # Cross ties under the deck.
            for j in range(5):
                t = j / 5
                pa, pb = qa.side(-5.5).lerp(qb.side(-5.5), t), qa.side(5.5).lerp(qb.side(5.5), t)
                z = lerp(da, db, t) - 0.2
                m.add(timber, lambda bm, pa=pa, pb=pb, z=z: cp._beam(bm, (pa.x, pa.y, z), (pb.x, pb.y, z), 0.4))
        # Railing posts along both edges.
        for k in range(int(L / 4.0) + 1):
            q = c.at(s0 + k * 4.0)
            for side in (-1, 1):
                p = q.side(side * (q.w / 2 + 0.65))
                m.add(timber, lambda bm, p=p, z=q.p.z, rot=road_rot(q): cuboid(bm, (p.x, p.y, z + 0.9), (0.32, 0.32, 1.9), rot))
        # Portals at both ends.
        for sp in (s0 + 2.0, s1 - 2.0):
            q = c.at(sp)
            portal(c, sc, m, q)
    m.build(c, "Great Canyon Bridge", "Bridge", "visual")


def portal(c, sc, m, q, h=9.0, banners=True, post=0.7):
    """A timber gateway over the road: two posts each side, a double crossbeam with a sign
    board, braced corners."""
    timber = ("weathered_timber", "wall")
    rot = road_rot(q)
    half = q.w / 2 + 1.6
    for side in (-1, 1):
        for along in (-0.8, 0.8):
            p = q.side(side * half) + q.t * along
            m.add(timber, lambda bm, p=p, z=q.p.z, rot=rot: cuboid(bm, (p.x, p.y, z + h / 2 - 0.5), (post, post, h + 1.0), rot))
        a = q.side(side * half)
        b = q.side(side * (half - 2.6))
        m.add(timber, lambda bm, a=a, b=b, z=q.p.z: cp._beam(bm, (a.x, a.y, z + h - 3.0), (b.x, b.y, z + h - 0.4), 0.35))
    for dz in (h - 0.4, h + 0.6):
        a, b = q.side(-half - 1.2), q.side(half + 1.2)
        m.add(timber, lambda bm, a=a, b=b, z=q.p.z + dz: cp._beam(bm, (a.x, a.y, z), (b.x, b.y, z), 0.55))
    if banners:
        for o in (-half * 0.55, half * 0.55):
            p = q.side(o)
            m.add(("canvas_sun", "wall"), lambda bm, p=p, z=q.p.z, rot=rot: cuboid(bm, (p.x, p.y, z + h - 2.0), (0.08, 2.6, 3.0), rot + math.pi / 2))
        p = q.side(0)
        m.add(("chevron_amber", "wall"), lambda bm, p=p, z=q.p.z, rot=rot: cuboid(bm, (p.x, p.y, z + h + 1.6), (0.12, 7.0, 1.4), rot + math.pi / 2))


def descent_trestle(c, sc, cd):
    """Timber bents under the descent's short trestle over the side ravine."""
    timber = ("weathered_timber", "wall")
    m = Mesh()
    for ob in pieces_of(c, "trestle"):
        s0, s1 = ob["kp_from"], ob["kp_to"]
        for k in range(int((s1 - s0) / 5.0) + 1):
            q = c.at(s0 + 2.5 + k * 5.0)
            posts = [q.side(o) for o in (-6.5, -2.2, 2.2, 6.5)]
            for p in posts:
                g = cd.natural(p.x, p.y) - 1.0
                top = q.p.z - 1.7
                if top - g < 1.0:
                    continue
                m.add(timber, lambda bm, p=p, g=g, top=top: cp._beam(bm, (p.x, p.y, g), (p.x, p.y, top), 0.5))
                if top - g > 5:
                    mid = (g + top) / 2
                    m.add(timber, lambda bm, a=posts[0], b=posts[-1], z=mid: cp._beam(bm, (a.x, a.y, z), (b.x, b.y, z), 0.3))
            a, b = posts[0], posts[-1]
            z = q.p.z - 1.7
            m.add(timber, lambda bm, a=a, b=b, z=z: cp._beam(bm, (a.x, a.y, z), (b.x, b.y, z), 0.5))
    m.build(c, "Descent Trestle", "Bridge", "visual")
    # Timber struts under the ledge here and there, where the road juts over the drop.
    m = Mesh()
    S = cd.SEG
    for s in (S[3] + 30, S[3] + 52, S[5] + 10, S[6] + 4):
        q = c.at(s)
        for along in (-3.0, 3.0):
            p = q.side(q.w / 2 + 1.0) + q.t * along
            g = q.p.z - 9.0
            wall = q.side(q.w / 2 - 5.0) + q.t * along
            m.add(timber, lambda bm, p=p, wall=wall, z=q.p.z, g=g: cp._beam(bm, (wall.x, wall.y, g), (p.x, p.y, z - 1.0), 0.45))
            m.add(timber, lambda bm, p=p, z=q.p.z: cp._beam(bm, (p.x, p.y, z - 1.0), (p.x, p.y, z - 7.0), 0.45))
    m.build(c, "Ledge Struts", "Bridge", "visual")


def brink_bridge(c, sc, cd):
    """The stone bridge over the river just above the falls: arches under the deck."""
    stone = ("masonry", "wall")
    m = Mesh()
    for ob in pieces_of(c, "brink"):
        s0, s1 = ob["kp_from"], ob["kp_to"]
        L = s1 - s0
        for k in range(3):
            q = c.at(s0 + L * (k + 0.5) / 3)
            rot = road_rot(q)
            g = 39.0
            # Piers either side of the arch openings.
        for k in range(4):
            q = c.at(s0 + L * k / 3)
            m.add(stone, lambda bm, q=q: cuboid(bm, (q.p.x, q.p.y, (q.p.z - 3.5 + 36.0) / 2), (4.0, q.w + 2.0, q.p.z - 3.5 - 36.0), road_rot(q)))
    m.build(c, "Brink Bridge", "Bridge", "visual")


# ------------------------------------------------------------------ the outpost


def outpost(c, sc, cd):
    """The desert racing outpost at the start: the timber start arch with its banners and
    checkered board, banner poles down the straight, the windmill, the lookout tower,
    the water tank, braziers, crates and fences."""
    S = cd.SEG
    m = Mesh()
    q = c.at(10.0)
    portal(c, sc, m, q, h=10.0, post=1.2)
    p = q.side(0)
    m.add(("start_checker", "wall"), lambda bm, p=p, z=q.p.z, rot=road_rot(q): cuboid(bm, (p.x, p.y, z + 8.6), (0.16, 12.0, 2.0), rot + math.pi / 2))
    m.build(c, "Start Arch", "Outpost", "visual")
    # Banner poles and braziers down both sides of the straight.
    for k, s in enumerate((-60.0, -40.0, -20.0, 25.0, 45.0)):
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 3.0))
            sc.put(cp.banner_pole(c, (k + (side > 0)) % 2), p.x, p.y, q.p.z - 0.2, rot=road_rot(q) + (math.pi if side < 0 else 0.0), coll="Outpost", role="both")
    for s in (-8.0, 16.0):
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 2.2))
            sc.put(cp.brazier(c), p.x, p.y, q.p.z - 0.1, coll="Outpost", role="both")
            sc.fires.append((p.x, p.y, q.p.z + 2.4))
    q0 = c.at(-30.0)
    south = q0.side(-(q0.w / 2 + 26.0))
    sc.put(cp.windmill_tower(c), south.x, south.y, cd.natural(south.x, south.y) - 0.3, rot=road_rot(q0) + 0.4, coll="Outpost", role="both")
    sc.windmill = (south.x, south.y, cd.natural(south.x, south.y) - 0.3 + 14.6, road_rot(q0) + 0.4)
    t = c.at(40.0).side(-(c.at(40.0).w / 2 + 18.0))
    sc.put(cp.water_tank(c), t.x, t.y, cd.natural(t.x, t.y) - 0.3, coll="Outpost", role="both")
    look = c.at(-75.0).side(c.at(-75.0).w / 2 + 16.0)
    sc.put(cp.lookout_tower(c), look.x, look.y, cd.natural(look.x, look.y) - 0.3, rot=0.3, coll="Outpost", role="both")
    for k, s in enumerate((-50.0, 5.0, 60.0)):
        q = c.at(s)
        p = q.side(-(q.w / 2 + 6.0 + 3 * k))
        sc.put(cp.crates(c, k % 2), p.x, p.y, cd.natural(p.x, p.y) - 0.2, rot=k, coll="Outpost", role="both")


# ------------------------------------------------------------------ plants and signs


def plants(c, sc, cd):
    """Saguaros, barrel cacti, agaves, sagebrush, dry grass and desert trees on the
    plateaus and terraces, thinning out on rock and never near the roads."""
    import props as pr

    ter = list(c.coll("Terrain").objects)[:1]

    def ok(margin, lo=-999.0):
        def f(x, y, z):
            if z < lo or cd.gorge_u(x, y) > -6.0:
                return False
            # Not on steep ground.
            dz = abs(cd.natural(x + 3, y) - cd.natural(x - 3, y)) + abs(cd.natural(x, y + 3) - cd.natural(x, y - 3))
            if dz > 2.5:
                return False
            return pr.clear_of_road(c, x, y, margin)

        return f

    X0, X1, Y0, Y1 = NEAR
    kinds = [
        (lambda k: cp.saguaro(c, k % 4), 120, 7.0, (0.8, 1.25), "both"),
        (lambda k: cp.barrel_cactus(c, k % 2), 70, 5.0, (0.8, 1.3), "visual"),
        (lambda k: cp.agave(c, k % 2), 110, 4.0, (0.8, 1.3), "visual"),
        (lambda k: cp.sagebrush(c, k % 2), 240, 4.0, (0.7, 1.4), "visual"),
        (lambda k: cp.dry_grass(c, k % 2), 320, 3.0, (0.8, 1.5), "visual"),
        (lambda k: cp.joshua_tree(c, k % 2), 26, 9.0, (0.9, 1.2), "both"),
        (lambda k: cp.boulder(c, k % 3), 90, 6.0, (0.7, 1.8), "both"),
        (lambda k: cp.boulder(c, 3 + k % 2), 44, 14.0, (3.0, 6.5), "both"),
    ]
    for j, (make, n, margin, scale, role) in enumerate(kinds):
        for v in range(2):
            proto = make(v)
            pr.scatter(c, proto, n // 2, (X0 + 10, X1 - 10, Y0 + 10, Y1 - 10), ok(margin), ter, seed=j * 13 + v * 5 + 1, scale=scale, role=role, coll="Plants")
    # Hoodoos in little groups on the terraces and the plateau.
    for k, (x, y, h) in enumerate(((-300.0, 175.0, 16.0), (-280.0, 160.0, 11.0), (-120.0, -175.0, 14.0), (230.0, -40.0, 12.0), (250.0, -52.0, 18.0), (420.0, -60.0, 10.0),
                                   (560.0, 160.0, 20.0), (580.0, 140.0, 13.0), (90.0, -230.0, 15.0), (-350.0, -200.0, 18.0), (-60.0, 200.0, 12.0))):
        if not pr.clear_of_road(c, x, y, 6.0) or cd.gorge_u(x, y) > -4:
            continue
        sc.put(cp.hoodoo(c, k % 3, h), x, y, cd.natural(x, y) - 0.5, rot=k, coll="Plants", role="both")


def chevrons(c, sc, cd):
    """Amber chevron boards on the outside of the big corners, facing the drivers."""
    S = cd.SEG
    for seg, frac in ((3, 0.35), (3, 0.7), (7, 0.3), (7, 0.7), (9, 0.3), (9, 0.75), (18, 0.25), (18, 0.6), (20, 0.4), (20, 0.75), (23, 0.5), (12, 0.5)):
        s0 = S[seg]
        s1 = S.get(seg + 1, c.length)
        s = s0 + (s1 - s0) * frac
        q = c.at(s)
        turn = cd.LAYOUT[seg][0]
        side = -1 if turn == "R" else 1  # the outside of the turn (R turns: left)
        p = q.side(side * (q.w / 2 + 3.2))
        back = c.at(s - 30.0).p
        n = Vector((back.x - p.x, back.y - p.y, 0)).normalized()
        rot = math.atan2(-n.x, n.y)
        sc.put(cp.chevron_sign(c, 1), p.x, p.y, q.p.z - 0.2, rot=rot, coll="Props", role="both")


# ------------------------------------------------------------------ gameplay


def gameplay(c, sc, cd):
    """Boosts, pickups, checkpoints (with a twin gate in the butte's slot), and the
    living parts: dust, birds, the windmill, the waterfalls' spray and roar."""
    S = cd.SEG
    # Zippers: off the start, down the wall, onto the bridge and along it, out of the tunnel, along
    # the overlook, off the head, out on the Mesa Run, and on the final rise.
    for at, across in ((28, 0), (S[3] + 20, 0), (S[7] + 30, 0), (S[8] + 60, 0), (S[14] + 10, 0), (S[15] + 140, -3), (S[19] + 20, 0), (S[21] + 4, 0), (S[25] - 30, 0)):
        c.zipper(at, across)
    for at, across in ((70, 0), (S[4] + 30, 3), (S[8] + 40, -3), (S[8] + 110, 3), (S[11] + 20, 0), (S[15] + 60, 0), (S[16] + 30, 3), (S[20] + 20, 0), (S[23] + 30, -3)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in ((90, -5, "red"), (90, 5, "blue"), (S[3] + 50, 0, "green"), (S[7] + 10, 0, "yellow"), (S[8] + 75, -4, "rainbow"), (S[8] + 75, 4, "red"),
                            (S[10] + 10, 0, "blue"), (S[13] + 30, 0, "green"), (S[15] + 100, -4, "yellow"), (S[15] + 100, 4, "red"), (S[18] + 40, 0, "rainbow"),
                            (S[20] + 60, -4, "blue"), (S[20] + 60, 4, "green"), (S[23] + 60, 0, "yellow")):
        c.balloon(at, across, col)

    a = kit.s_near(c, *cd.BUTTE_SHORT[0])
    b = kit.s_near(c, *cd.BUTTE_SHORT[-1])
    apex = (a + b) / 2
    gates = c.checkpoints(
        extra=[S[2] + 10, S[4], S[6] + 10, S[8] + 20, S[8] + 120, S[10], S[12], S[14] + 10, S[15] + 90, S[16] + 30, S[18] + 30, S[19] + 30, S[20] + 50,
               a - 6, apex, b + 6, S[25]],
        avoid=[(a - 2, apex - 8), (apex + 8, b + 2)],
        height=9.0,
    )
    main_gate = min(gates.items(), key=lambda kv: abs(kv[0] - apex))[1]
    pts = cd.BUTTE_SHORT
    mid = len(pts) // 2
    z = c.nearest(*pts[mid])[0].p.z
    c.alt_gate(main_gate, "butte_slot", [(x, y, z) for x, y in pts[mid - 1:mid + 2]], width=14.0)

    # The living parts. Dust kicked up behind karts on the dirt; wisps of dust blowing
    # across the land; the windmill's wheel; birds circling over the canyon; the
    # waterfalls' spray and roar.
    c.entity("dust", color="#d89a6a", rate=1.0)
    c.entity("dustwind", rate=10, radius=60, color="#e0a878")
    wx, wy, wz, wr = sc.windmill
    game_entity(c, "windmill", wx + math.cos(wr) * 1.4, wy + math.sin(wr) * 1.4, wz, heading=round(wr, 3), radius=3.2, speed=1.4)
    for k, (x, y, z, r, n) in enumerate(((-150.0, 10.0, 110.0, 70.0, 3), (300.0, 60.0, 120.0, 55.0, 2), (-600.0, 0.0, 140.0, 90.0, 4), (520.0, -180.0, 130.0, 60.0, 2))):
        game_entity(c, "birds", x, y, z, radius=r, count=n, speed=round(0.16 + 0.04 * k, 2), seed=k + 1)
    for x, y, foot, top, w, h in sc.falls:
        gx, gy, gz = c.game(x, y, foot)
        c.entity("waterfall", x=gx, y=gy, z=gz, top=round(top, 1), width=round(w, 1), heading=0)
    for x, y, z in sc.fires:
        game_entity(c, "torch", x, y, z)


def find_lip(cd):
    """Where the upper river leaps off into the head of the gorge."""
    y = cd.Y_HEAD
    x = cd.X_HEAD
    while cd.gorge_u(x, y) > 0.0:
        x += 0.5
    return (x - 1.0, y)


def build(c, cd):
    sc = Scene(c, cd)
    sc.lip = find_lip(cd)
    import canyon_walls as cw

    cw.gorge(c, cd)
    cd.WALL_SPANS.update(cw.rim_walls(c, cd))
    land(c, cd, sc)
    c.start_line()
    river(c, sc, cd)
    head_falls(c, sc, cd)
    side_falls(c, sc, cd)
    great_arch(c, sc, cd)
    buttes(c, sc, cd)
    tunnel(c, sc, cd)
    great_bridge(c, sc, cd)
    descent_trestle(c, sc, cd)
    brink_bridge(c, sc, cd)
    outpost(c, sc, cd)
    plants(c, sc, cd)
    chevrons(c, sc, cd)
    gameplay(c, sc, cd)
    groups = ("Props", "Plants", "Outpost")
    c.merge_props(groups)
    joined = [o for name in groups for o in c.coll(name).objects if o.type == "MESH" and o.data.users == 1]
    ter = list(c.coll("Terrain").objects)
    rocks = list(c.coll("Buttes").objects) + list(c.coll("Arch").objects) + list(c.coll("Pass").objects)
    c.preset("sun", ter + rocks, 0.32)
    c.preset("bottoms", ter + rocks, 0.35)
    # Deep in the canyon the shadows go blue and violet; warm light glows in the tunnel
    # and round the braziers.
    deep = lambda w: w.z < 12.0  # noqa: E731
    c.glow(ter + rocks, [], 1.0, (1, 1, 1), base=(0.8, 0.8, 1.0), region=lambda w: w.z < 12.0 and w.z > -10.0)
    c.glow(ter + rocks, [], 1.0, (1, 1, 1), base=(0.66, 0.66, 0.95), region=lambda w: w.z <= -10.0)
    c.glow(rocks, sc.tunnel_light, 26.0, (1.25, 1.0, 0.75), base=(0.55, 0.5, 0.55), region=lambda w: _in_tunnel(c, sc, w))
    c.glow(joined, sc.fires, 9.0, (1.4, 1.1, 0.75), base=1.0)
    kit.paint.shade_roads(c.pieces, 0.3)


def _in_tunnel(c, sc, w):
    s0, s1, _ = sc.tunnel
    smp, d = c.nearest(w.x, w.y)
    return s0 - 10 <= smp.s <= s1 + 10 and d < 14 and w.z < smp.p.z + 12
