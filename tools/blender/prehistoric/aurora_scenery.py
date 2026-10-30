# Aurora Rift's scenery (see aurora_rift.py): the glacier with its caverns cut out of
# it (the entrance tunnel, the Crystal Cathedral, the crystal tunnel, Mirror Lake's
# cavern, the ascent), the Rift, the Monolith, the bridges and the Loop's pedestal, the
# waterfalls, the crystal forests, the lake and its reflections, the light, and the
# gameplay entities. Built from the kit in aurora_props.py.
# SPDX-License-Identifier: MIT

import math

import aurora_props as ap
import course_kit as kit
from course_kit import Vector, bmesh, lerp, rnd
from props import _faces, blob, cuboid, loft, tube

ROCK = ("rift_rock", "wall")
CLIFF = ("rift_cliff", "wall")
ICEWALL = ("glacier_wall", "wall")
CAVE = ("cavern_ice", "wall")
STONE = ("rift_stone", "wall")
CARVED = ("rift_carved", "wall")
SNOW = ("rift_snow", "deep_snow")


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


def apply_cut(c, solid, cutter):
    """Subtract `cutter` (a closed mesh object) from `solid`, and delete it."""
    import bpy

    mod = solid.modifiers.new("Cut", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
    mod.object = cutter
    bpy.context.view_layer.objects.active = solid
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter)


def closed(c, bm, name="Cutter"):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return c.mesh_object(name, bm, "Rocks", "visual")


# ------------------------------------------------------------------ outlines


def hull(pts):
    """Convex hull of 2D points (anticlockwise)."""
    pts = sorted(set((round(x, 2), round(y, 2)) for x, y in pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


def outline(pts, pad, n=72, wobble=0.0, seed=0):
    """A smooth closed outline round points: their hull, padded by `pad`, resampled to n
    points by angle round its centroid (so it can be lofted), roughened by `wobble`."""
    h = hull(pts)
    cx = sum(p[0] for p in h) / len(h)
    cy = sum(p[1] for p in h) / len(h)
    out = []
    for k in range(n):
        a = k * math.tau / n
        dx, dy = math.cos(a), math.sin(a)
        # Furthest hull point along this ray (support), then pad.
        best = 0.0
        for i in range(len(h)):
            (x0, y0), (x1, y1) = h[i], h[(i + 1) % len(h)]
            # Ray-segment intersection from the centroid.
            ex, ey = x1 - x0, y1 - y0
            den = dx * ey - dy * ex
            if abs(den) < 1e-9:
                continue
            t = ((x0 - cx) * ey - (y0 - cy) * ex) / den
            u = ((x0 - cx) * dy - (y0 - cy) * dx) / den
            if t > 0 and -1e-6 <= u <= 1 + 1e-6:
                best = max(best, t)
        r = best + pad * (1 + wobble * (0.6 * math.sin(3 * a + seed) + 0.4 * math.sin(7 * a + seed * 2)))
        out.append((cx + dx * r, cy + dy * r))
    return out, (cx, cy)


def roof_z(ring, centre, eave, apex, x, y):
    """The height of a chamber's domed roof over (x, y) (see chamber_cutter), or None
    outside it."""
    cx, cy = centre
    a = math.atan2(y - cy, x - cx)
    n = len(ring)
    k = int(round((a % math.tau) / math.tau * n)) % n
    rx, ry = ring[k]
    edge = math.hypot(rx - cx, ry - cy)
    f = math.hypot(x - cx, y - cy) / max(1e-6, edge)
    if f >= 1.0:
        return None
    t = (2 / math.pi) * math.acos(min(1.0, f) ** (1 / 0.7))
    return eave + (apex - eave) * math.sin(t * math.pi / 2)


def chamber_cutter(c, ring, centre, z0, eave, apex, layers=6, wobble=1.0, seed=0, name="Chamber"):
    """A cavern: walls straight up from z0 to `eave` round the outline `ring`, roughened,
    then a dome rising to `apex` over its centre."""
    bm = bmesh.new()
    cx, cy = centre
    rings = []
    n = len(ring)
    # Walls: a few rings with the rock bulging in and out.
    zs = [z0 + (eave - z0) * f for f in (0.0, 0.4, 0.72, 0.9, 1.0)]
    for j, z in enumerate(zs):
        r = []
        for k, (x, y) in enumerate(ring):
            dx, dy = x - cx, y - cy
            f = 1.0 + (wobble * 0.05 * math.sin(k * 1.7 + j * 2.3 + seed) if 0 < j < len(zs) - 1 else 0.0)
            r.append(bm.verts.new((cx + dx * f, cy + dy * f, z)))
        rings.append(r)
    # The dome.
    for j in range(1, layers):
        t = j / layers
        s = math.cos(t * math.pi / 2) ** 0.7
        z = eave + (apex - eave) * math.sin(t * math.pi / 2)
        r = []
        for k, (x, y) in enumerate(ring):
            dx, dy = x - cx, y - cy
            f = s * (1 + wobble * 0.04 * math.sin(k * 2.1 + j + seed))
            r.append(bm.verts.new((cx + dx * f, cy + dy * f, z)))
        rings.append(r)
    for lo, hi in zip(rings, rings[1:]):
        for k in range(n):
            bm.faces.new((lo[k], lo[(k + 1) % n], hi[(k + 1) % n], hi[k]))
    top = bm.verts.new((cx, cy, apex))
    for k in range(n):
        bm.faces.new((rings[-1][k], rings[-1][(k + 1) % n], top))
    bm.faces.new(list(reversed(rings[0])))
    return closed(c, bm, name + " Cutter")


def route_cutter(c, s0, s1, prof, pad=0.0, step=2.5, wobble=0.0, name="Tunnel", grow=None):
    """A passage along the route from s0 to s1 with the cross-section `prof` [(across, up)]
    (relative to the road), roughened by `wobble`; `grow(t)` scales it along the way."""
    bm = bmesh.new()
    rings = []
    n = max(3, math.ceil((s1 - s0 + 2 * pad) / step))
    for k in range(n + 1):
        t = k / n
        s = s0 - pad + (s1 - s0 + 2 * pad) * t
        q = c.at(s)
        g = grow(t) if grow else 1.0
        ring = []
        # (The floor banks with the road: flat, it left a gutter along a banked road's high
        # side a metre and a half deep, and a kart that slid off couldn't climb back.)
        tb = math.tan(math.radians(q.bank))
        for j, (o, z) in enumerate(prof):
            w = 1.0 + wobble * (math.sin(s * 0.21 + j * 1.9) * 0.6 + math.sin(s * 0.07 + j) * 0.4) if z > 0 else 1.0
            lift = z * w * g if z > 0 else z - o * g * tb
            ring.append(bm.verts.new(q.p + q.r * (o * w * g) + Vector((0, 0, lift))))
        rings.append(ring)
    m = len(prof)
    for lo, hi in zip(rings, rings[1:]):
        for j in range(m):
            bm.faces.new((lo[j], lo[(j + 1) % m], hi[(j + 1) % m], hi[j]))
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    return closed(c, bm, name + " Cutter")


def tunnel_prof(half, h, depth=0.25):
    return [(-half, -depth), (half, -depth), (half * 1.05, 0.55 * h), (0.75 * half, 0.9 * h), (0.3 * half, h),
            (-0.3 * half, h), (-0.75 * half, 0.9 * h), (-half * 1.05, 0.55 * h)]


def shaft(c, x, y, z0, z1, r, n=16, wobble=0.25, seed=0, name="Shaft"):
    """A rough vertical hole (a ceiling aperture or a fracture), as a cutter."""
    bm = bmesh.new()
    rings = []
    for j, z in enumerate((z0, (z0 + z1) / 2, z1)):
        ring = []
        for k in range(n):
            a = k * math.tau / n
            rr = r * (1 + wobble * (0.6 * math.sin(3 * a + seed + j) + 0.4 * math.sin(5 * a + seed * 2))) * (1.0 + 0.25 * j)
            ring.append(bm.verts.new((x + rr * math.cos(a), y + rr * 0.8 * math.sin(a), z)))
        rings.append(ring)
    loft(bm, rings, cap_top=True, cap_bottom=True)
    return closed(c, bm, name + " Cutter")


def slab(c, centre, size, rot, name="Slit"):
    bm = bmesh.new()
    cuboid(bm, centre, size, rot)
    return closed(c, bm, name + " Cutter")


# ------------------------------------------------------------------ the glacier


def glacier(c, ar, cell=12.0):
    """The massif: one solid of glacier from the Rift's face north, its top the glacier's
    surface, its bottom well under the abyss (so nothing shows beneath it)."""
    x0, x1, y0, y1 = ar.MASSIF
    nx = int(round((x1 - x0) / cell))
    ny = int(round((y1 - y0) / cell))
    bot = ar.ABYSS - 30.0
    bm = bmesh.new()
    top = {}
    low = {}
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx
            t = j / ny
            yb = ar.face_y(x)
            y = yb + (y1 - yb) * t
            # A rough, broken face: the south edge juts in and out.
            if j == 0:
                y += 2.5 * math.sin(x / 7.3) + 1.5 * math.sin(x / 3.1)
            if i in (0, nx):
                x += 4.0 * math.sin(y / 9.0)
            top[i, j] = bm.verts.new((x, y, ar.glacier_top(x, y)))
            low[i, j] = bm.verts.new((x, y, bot))
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((top[i, j], top[i + 1, j], top[i + 1, j + 1], top[i, j + 1]))
            bm.faces.new((low[i, j + 1], low[i + 1, j + 1], low[i + 1, j], low[i, j]))
    # The sides. The south one is the face over the Rift: broken into buttresses and
    # ledges (rows of vertices pushed in and out), not one flat wall.
    rows = [low[i, 0] for i in range(nx + 1)]
    levels = (-110.0, -50.0, 0.0, 40.0, 75.0)
    for lv, zz in enumerate(levels):
        nxt = []
        for i in range(nx + 1):
            v = top[i, 0]
            x = v.co.x
            zt = v.co.z
            z = min(zz + 6 * math.sin(x / 17.0 + lv), zt - 6.0)
            out = 6.0 * math.sin(x / 23.0 + lv * 1.7) + 4.0 * math.sin(x / 7.0 + lv) + (5.0 if (i // 3 + lv) % 2 else -2.0)
            nxt.append(bm.verts.new((x, v.co.y - max(-3.0, out), z)))
        for i in range(nx):
            bm.faces.new((rows[i], rows[i + 1], nxt[i + 1], nxt[i]))
        rows = nxt
    for i in range(nx):
        bm.faces.new((rows[i], rows[i + 1], top[i + 1, 0], top[i, 0]))
        bm.faces.new((top[i, ny], top[i + 1, ny], low[i + 1, ny], low[i, ny]))
    for j in range(ny):
        bm.faces.new((top[0, j], top[0, j + 1], low[0, j + 1], low[0, j]))
        bm.faces.new((low[nx, j], low[nx, j + 1], top[nx, j + 1], top[nx, j]))
    # Give the face some depth: rows of vertices just behind it, sheared.
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return c.mesh_object("Glacier", bm, "Glacier")


def caverns(c, ar, P, more=None):
    """Cut the caverns out of the glacier. Returns (solid, info) where info has the
    Cathedral's and the lake cavern's outlines (for dressing them). `more(solid)`: more
    cuts before it's painted (the ruin's fallen roof)."""
    solid = glacier(c, ar)
    info = {}
    # 1. The entrance tunnel: from the face, growing taller and wider toward the Cathedral.
    t0, t1 = P["entrance_cut"]
    apply_cut(c, solid, route_cutter(c, t0, t1, tunnel_prof(12.5, 15.0), pad=14.0, wobble=0.12, name="Entrance",
                                     grow=lambda t: 1.0 + 0.6 * t ** 3))
    # 2. The Crystal Cathedral: a vast hall round the roads from the reveal to the Loop,
    # reaching south-west under the ascent's gallery; a domed roof.
    pts = []
    a, b = P["cath_segs"]
    for p in ar.PATH:
        if a <= p[3] <= b:
            pts.append((p[0], p[1]))
    # The Loop's own footprint, and the abyss reaching south and west.
    lp_pts = [(ar.LOOP_IN[0] + dx, ar.LOOP_IN[1] + dy) for dx in (-40, 40) for dy in (-40, 40)]
    extra = P["cath_extra"]
    ring, centre = outline(pts + lp_pts + extra, 22.0, n=96, wobble=0.25, seed=3)
    info["cathedral"] = (ring, centre)
    apply_cut(c, solid, chamber_cutter(c, ring, centre, ar.ABYSS - 60, ar.Z_CATH + 62, ar.Z_CATH + 128, wobble=1.0, seed=3, name="Cathedral"))
    # 3. The crystal tunnel down to the lake.
    apply_cut(c, solid, route_cutter(c, *P["crystal_tunnel"], tunnel_prof(12.0, 14.0), pad=10.0, wobble=0.15, name="Crystal Tunnel"))
    # 4. Mirror Lake's cavern.
    a, b = P["lake_segs"]
    lpts = [(p[0], p[1]) for p in ar.PATH if a <= p[3] <= b] + [(x, y) for x, y in getattr(ar, "LAKE_SHORT", [])]
    lring, lcentre = outline(lpts, 34.0, n=72, wobble=0.3, seed=7)
    info["lake"] = (lring, lcentre)
    apply_cut(c, solid, chamber_cutter(c, lring, lcentre, ar.Z_LAKE - 9.0, ar.Z_LAKE + 30, ar.Z_LAKE + 64, wobble=1.2, seed=7, name="Lake Cavern"))
    # 5. The ascent: an ice tunnel up from the lake, a fractured canyon open to the sky
    # (the cutter rises clear of the glacier's top), a gallery and the great opening.
    apply_cut(c, solid, route_cutter(c, *P["ice_tunnel"], tunnel_prof(12.0, 15.0), pad=8.0, wobble=0.15, name="Ice Tunnel"))
    canyon = [(-11.0, -0.25), (11.0, -0.25), (13.0, 30.0), (24.0, 200.0), (-24.0, 200.0), (-13.0, 30.0)]
    apply_cut(c, solid, route_cutter(c, *P["canyon_cut"], canyon, pad=6.0, wobble=0.1, name="Canyon"))
    apply_cut(c, solid, route_cutter(c, *P["opening_cut"], tunnel_prof(16.0, 30.0), pad=6.0, wobble=0.12, name="Great Opening",
                                     grow=lambda t: 1.0 + 0.5 * t))
    # 6. Holes in the roof: over the Loop (the aurora frames it), over the Monolith, and
    # a long fracture; and where the lake cavern's roof has fallen in.
    lx, ly = ar.LOOP_IN[0], ar.LOOP_IN[1]
    apply_cut(c, solid, shaft(c, lx - 10, ly + 4, ar.Z_CATH + 70, 400, 40.0, seed=1, name="Loop Aperture"))
    # ...and a great slanting window beyond the Loop, lined up with the view from the
    # causeway, so the Loop is framed against the sky and the aurora as you approach.
    hx, hy = math.cos(math.radians(ar.LOOP_HEAD)), math.sin(math.radians(ar.LOOP_HEAD))
    base = Vector((lx + hx * 40, ly + hy * 40, ar.Z_CATH + 70))
    d = Vector((hx * 0.85, hy * 0.85, 0.55)).normalized()
    bm = bmesh.new()
    rings = []
    for j, t in enumerate((-20.0, 120.0, 320.0)):
        ctr = base + d * t
        side = Vector((-hy, hx, 0.0))
        up = d.cross(side).normalized()
        r = 34.0 + 0.12 * max(0.0, t)
        rings.append([bm.verts.new(ctr + (side * math.cos(k * math.tau / 14) * 1.4 + up * math.sin(k * math.tau / 14)) * r * (1 + 0.15 * math.sin(k * 2.3 + j)))
                      for k in range(14)])
    loft(bm, rings, cap_top=True, cap_bottom=True)
    apply_cut(c, solid, closed(c, bm, "Aurora Window Cutter"))
    mx, my = ar.MONOLITH
    apply_cut(c, solid, shaft(c, mx + 6, my + 10, ar.Z_CATH + 90, 400, 26.0, seed=4, name="Monolith Aperture"))
    apply_cut(c, solid, slab(c, (mx + 120, my + 40, 260), (16, 140, 300), 0.6, name="Roof Fracture"))
    for k, (dx, dy, r) in enumerate(((20, 10, 22), (-60, -30, 16))):
        apply_cut(c, solid, shaft(c, lcentre[0] + dx, lcentre[1] + dy, ar.Z_LAKE + 40, 400, r, seed=9 + k, name="Lake Opening"))
    # 7. Fractures in the face: slits from the Rift into the Cathedral (its glow shows
    # through them from the bridges).
    for k, x in enumerate(P["face_fractures"]):
        apply_cut(c, solid, slab(c, (x, -40.0, ar.Z_CATH + 10), (5.0 + k, 170.0, 110.0), 0.12 * (k - 1), name="Face Fracture"))
    if more:
        more(solid)
    paint_glacier(c, ar, solid, info)
    return solid, info


def inside(poly, x, y):
    n = len(poly)
    j = n - 1
    hit = False
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            hit = not hit
        j = i
    return hit


def paint_glacier(c, ar, solid, info):
    """Texture the glacier: snow on top, blue glacier ice on its outer faces, crystal-veined
    ice inside the caverns, dark rock low down, the lake bed."""
    cath = info["cathedral"][0]
    lake = info["lake"][0]
    g = {k: [] for k in ("snow", "face", "cave", "rock", "bed", "deep", "roof")}
    for p in solid.data.polygons:
        w = p.center
        top = ar.glacier_top(w.x, w.y)
        if w.z > top - 2.0 and p.normal.z > 0.5:
            g["snow"].append(p.index)
            continue
        in_lake = inside(lake, w.x, w.y) and w.z < ar.Z_LAKE + 70
        if in_lake and p.normal.z > 0.6 and w.z < ar.Z_LAKE:
            g["bed"].append(p.index)
        elif (inside(cath, w.x, w.y) or in_lake) and p.normal.z < -0.25 and w.z > ar.Z_LAKE + 20:
            g["roof"].append(p.index)
        elif inside(cath, w.x, w.y) or in_lake:
            g["deep" if w.z < ar.Z_CATH - 40 else "face"].append(p.index)
        elif w.z < ar.Z_CATH - 40:
            g["rock"].append(p.index)
        elif p.normal.z < -0.3:
            g["cave"].append(p.index)
        else:
            g["face"].append(p.index)
    c.assign(solid, c.lib("rift_snow", "deep_snow"), g["snow"])
    c.assign(solid, c.lib(*ICEWALL), g["face"])
    c.assign(solid, c.lib(*CAVE), g["cave"])
    c.assign(solid, c.lib(*ROCK), g["rock"])
    c.assign(solid, c.lib(*CLIFF), g["deep"])
    c.assign(solid, c.lib("abyss_glow", "wall"), g["bed"])
    c.assign(solid, c.lib("rift_roof", "wall"), g["roof"])
    solid.data.shade_flat()


# ------------------------------------------------------------------ helpers


class Scene:
    """What the dressing functions share: the course, the layout module, and lists of
    lights (for painting) and entities to add at the end."""

    def __init__(self, c, ar):
        self.c = c
        self.ar = ar
        self.warm = []  # lantern light (x, y, z)
        self.cold = []  # crystal light
        self.violet = []
        self.lanterns = []  # lantern entities (game lights)
        self.shimmer = []
        self.mirror = []  # (proto, x, y, z, rot, scale) to reflect in the lake

    def land(self, x, y):
        nat = self.ar.natural(x, y)
        w, z = self.c.road_height(x, y, 8.5, 7.0, 0.2, nat)
        return lerp(nat, z, w)

    def put(self, proto, x, y, z, rot=0.0, scale=1.0, coll="Crystals", role="visual", mirror=False):
        ob = self.c.place(proto, x, y, z, rot=rot, scale=scale, coll=coll, role=role)
        if mirror:
            self.mirror.append((proto, x, y, z, rot, scale))
        return ob


def clear(c, x, y, margin, extra=()):
    """Far enough from the road (and any extra polylines)?"""
    smp, d = c.nearest(x, y)
    if d < smp.w / 2 + margin:
        return False
    for pts in extra:
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            dx, dy = bx - ax, by - ay
            t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy + 1e-9)))
            if math.hypot(x - ax - t * dx, y - ay - t * dy) < margin + 6:
                return False
    return True


def road_rot(q):
    return math.atan2(q.t.y, q.t.x)


# ------------------------------------------------------------------ structures


def arch_bridge(c, sc, s0, s1, depth, every=24.0, pier=(7.0, 9.0), mat=STONE, accent=CARVED, name="Bridge", lamps=12.0):
    """Stone arches and piers under a road piece from s0 to s1 (the deck itself is the
    road's), the piers going down `depth` metres into the mist; lantern posts along both
    parapets; icicles hanging from the arches."""
    m = Mesh()
    L = s1 - s0
    n = max(1, int(round(L / every)))
    for k in range(n + 1):
        q = c.at(s0 + L * k / n)
        top = q.p.z - 3.4
        m.add(mat, lambda bm, q=q, top=top: cuboid(bm, (q.p.x, q.p.y, top - depth / 2), (pier[0], pier[1], depth), road_rot(q)))
        # A cap with carved stones.
        m.add(accent, lambda bm, q=q, top=top: cuboid(bm, (q.p.x, q.p.y, top - 1.0), (pier[0] + 1.2, pier[1] + 1.2, 2.0), road_rot(q)))
    # The arches: a curved soffit between each pair of piers (a lofted ring of stone).
    for k in range(n):
        a, b = s0 + L * k / n, s0 + L * (k + 1) / n
        half = min(c.at(a).w, c.at(b).w) / 2 + 0.6
        rings = []

        def arc(bm, a=a, b=b, half=half):
            pts = []
            steps = 10
            for j in range(steps + 1):
                t = j / steps
                q = c.at(a + (b - a) * t)
                rise = math.sin(math.pi * t)
                z = q.p.z - 3.4 - (1 - rise) * ((b - a) * 0.45)
                pts.append((q, z))
            ringsl = []
            for q, z in pts:
                ringsl.append([bm.verts.new(q.p + q.r * o + Vector((0, 0, z - q.p.z + dz))) for o, dz in ((-half, 0), (half, 0), (half, 1.6), (-half, 1.6))])
            loft(bm, ringsl, cap_top=False)

        m.add(mat, arc)
    ob = m.build(c, name + " Arches", "Bridges", "visual")
    for k in range(int(L / lamps) + 1):
        q = c.at(s0 + 4 + k * lamps)
        if q.s > s1:
            break
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 0.9))
            sc.put(ap.lantern_post(c), p.x, p.y, q.p.z - 0.1, rot=road_rot(q), coll="Bridges")
            sc.warm.append((p.x, p.y, q.p.z + 2.4))
            if (k + (side > 0)) % 2 == 0:
                sc.lanterns.append((p.x, p.y, q.p.z + 2.4))
        if k % 2 == 0:
            for side in (-1, 1):
                p = q.side(side * (q.w / 2 + 0.2))
                sc.put(ap.icicle_fringe(c, k % 3, 6.0, 3.5), p.x, p.y, q.p.z - 3.6, rot=road_rot(q), coll="Bridges")
    return ob


def ice_span(c, sc, s0, s1, depth=14.0, name="Ice Span"):
    """A natural bridge of glacier ice: a thick, lumpy belly under the road with icicles
    and crystals hanging from it."""
    m = Mesh()
    L = s1 - s0
    n = max(2, int(L / 6))
    for k in range(n + 1):
        q = c.at(s0 + L * k / n)
        t = k / n
        sag = depth * (0.5 + 0.5 * math.sin(math.pi * t)) * (1.0 - 0.6 * (abs(t - 0.5) * 2) ** 3)
        w = q.w / 2 + 2.0
        sz = sag * 0.5 + 1.0
        m.add(ICEWALL, lambda bm, q=q, sz=sz, w=w: blob(bm, (q.p.x, q.p.y, q.p.z - 1.3 - sz), 1.0, sx=w, sy=w * 0.8, sz=sz))
    ob = m.build(c, name, "Bridges", "visual")
    for k in range(int(L / 9)):
        q = c.at(s0 + 4 + k * 9)
        sc.put(ap.hanging(c, k % 3, 10.0 + 4 * (k % 2), ap.CRYSTALS[k % 4]), q.p.x, q.p.y, q.p.z - 6.0, rot=k, coll="Bridges")
        sc.cold.append((q.p.x, q.p.y, q.p.z - 8))
    return ob


def island(c, sc, ar, r_top=66.0, gaps=(), drop=0.25, role="both"):
    """The Monolith's island: a pillar of rock rising from the abyss, its top level with the
    road (a little under it), a low parapet round its rim with gaps for the bridges."""
    mx, my = ar.MONOLITH
    z = ar.Z_CATH - drop
    bm = bmesh.new()
    n = 48
    rings = []
    for j, (zz, rr) in enumerate(((ar.ABYSS - 20, 0.55), (-60, 0.62), (-10, 0.72), (z - 14, 0.86), (z - 3, 0.97), (z, 1.0))):
        ring = []
        for k in range(n):
            a = k * math.tau / n
            f = rr * (1 + 0.06 * math.sin(3 * a + j) + 0.04 * math.sin(7 * a + 2 * j))
            ring.append(bm.verts.new((mx + r_top * f * math.cos(a), my + r_top * f * math.sin(a), zz)))
        rings.append(ring)
    loft(bm, rings, cap_top=True, cap_bottom=True)
    ob = c.mesh_object("Monolith Island", bm, "Island", role)
    top = [p.index for p in ob.data.polygons if p.normal.z > 0.9]
    side = [p.index for p in ob.data.polygons if p.normal.z <= 0.9]
    c.assign(ob, c.lib("rift_rock", "snow_stone"), top)
    c.assign(ob, c.lib(*CLIFF), side)
    ob.data.shade_flat()
    # The parapet: low walls round the rim, open where the bridges come in.
    m = Mesh()
    segs = 72
    for k in range(segs):
        a0, a1 = k * math.tau / segs, (k + 1) * math.tau / segs
        mid = (a0 + a1) / 2
        if any(abs(math.atan2(math.sin(mid - g), math.cos(mid - g))) < w for g, w in gaps):
            continue
        r = r_top - 1.0
        p0 = (mx + r * math.cos(a0), my + r * math.sin(a0))
        p1 = (mx + r * math.cos(a1), my + r * math.sin(a1))
        cxp, cyp = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        ln = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        m.add(("edge_amber", "wall"), lambda bm, cxp=cxp, cyp=cyp, ln=ln, mid=mid: cuboid(bm, (cxp, cyp, z + 0.55), (ln + 0.1, 0.9, 1.1), mid + math.pi / 2))
        if k % 6 == 0:
            sc.put(ap.lantern_post(c), cxp, cyp, z, rot=mid, coll="Bridges")
            sc.warm.append((cxp, cyp, z + 2.4))
    m.build(c, "Island Parapet", "Island", role)
    return ob


def monolith(c, sc, ar):
    """The Central Monolith: a colossal six-sided crystal rising from the abyss through the
    island and up into the hole in the roof, crystals branching from it, amber crystals
    glowing gold at its foot."""
    mx, my = ar.MONOLITH
    z0 = ar.ABYSS - 10
    R = sc.p["mono_r"]
    f = R / 22.0
    m = Mesh()
    m.add(("monolith_core", "wall"), lambda bm: ap.shard(bm, (mx, my, z0), (0.015, 0.02, 1), 330.0, R, n=6, tip=0.16, twist=0.3, flare=0.7))
    # Secondary shafts leaning against it, and branches growing out at several heights.
    for k in range(3):
        a = k * math.tau / 3 + 0.9
        m.add(("monolith_core", "wall"), lambda bm, a=a, k=k: ap.shard(bm, (mx + 20 * f * math.cos(a), my + 20 * f * math.sin(a), z0 + 20),
                                                                     (0.12 * math.cos(a), 0.12 * math.sin(a), 1), 190.0 + 40 * k, 9.0 * f, n=6, tip=0.18, twist=a))
    for k in range(12):
        a = k * 2.2 + 0.4
        zz = ar.Z_CATH + 22 + k * 9
        r = R * (1 - 0.3 * (zz - z0) / 330.0)
        mat = ("crystal_violet2" if k % 3 == 1 else "crystal_magenta" if k % 3 == 2 else "crystal_cyan", "wall")
        m.add(mat, lambda bm, a=a, zz=zz, r=r, k=k: ap.shard(bm, (mx + r * 0.8 * math.cos(a), my + r * 0.8 * math.sin(a), zz),
                                                       (math.cos(a), math.sin(a), 1.0 + 0.25 * (k % 3)), (40.0 + 10 * (k % 3)) * f, 5.0 * f, n=6, tip=0.2, twist=a))
    # Below the island: crystals down the shaft into the mist.
    for k in range(5):
        a = k * 1.3 + 1.0
        zz = -20.0 - k * 22
        m.add(("crystal_teal", "wall"), lambda bm, a=a, zz=zz: ap.shard(bm, (mx + 13 * f * math.cos(a), my + 13 * f * math.sin(a), zz),
                                                                      (math.cos(a), math.sin(a), 0.9), 30.0, 3.6, n=6, tip=0.22, twist=a))
    m.build(c, "Central Monolith", "Monolith", "visual")
    # Its foot on the island: amber crystals glowing gold, cyan clusters (kept clear of
    # the road ring and the crystal-arch shortcut).
    for k in range(9):
        a = k * math.tau / 9 + 0.2
        r = sc.p["mono_foot"] + 3.0 * (k % 2)
        x, y = mx + r * math.cos(a), my + r * math.sin(a)
        if not clear(c, x, y, 3.0, [getattr(ar, "MONO_SHORT", [])]):
            continue
        sc.put(ap.amber_cluster(c, k % 3, 7.0 + 2 * (k % 2)), x, y, ar.Z_CATH - 0.3, rot=a, coll="Monolith")
        sc.warm.append((x, y, ar.Z_CATH + 4))
    for k in range(8):
        a = k * math.tau / 8
        sc.cold.append((mx + (R + 8) * math.cos(a), my + (R + 8) * math.sin(a), ar.Z_CATH + 2))
    for k in range(6):
        sc.cold.append((mx, my, ar.Z_CATH + 20 + k * 25))


def crystal_arch(c, sc, ar):
    """The glowing crystal arch over the Monolith shortcut: two leaning crystal clusters
    meeting overhead, with an arch of crystals between them."""
    pts = ar.MONO_SHORT
    mid = pts[len(pts) // 2]
    a, b = pts[len(pts) // 2 - 1], pts[len(pts) // 2 + 1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    dl = math.hypot(dx, dy) or 1
    nx, ny = -dy / dl, dx / dl
    z = ar.Z_CATH
    m = Mesh()
    span = 7.5
    for side in (-1, 1):
        bx, by = mid[0] + nx * span * side, mid[1] + ny * span * side
        m.add(("crystal_cyan", "wall"), lambda bm, bx=bx, by=by, side=side: ap.shard(bm, (bx, by, z - 1), (-nx * side * 0.55, -ny * side * 0.55, 1), 13.0, 1.8, n=6, tip=0.25))
        m.add(("crystal_violet2", "wall"), lambda bm, bx=bx, by=by, side=side: ap.shard(bm, (bx + nx * side * 1.5, by + ny * side * 1.5, z - 1), (nx * side * 0.2, ny * side * 0.2, 1), 9.0, 1.4, n=6, tip=0.3))
    # The keystone crystals across the top.
    for k in range(7):
        t = k / 6 - 0.5
        x, y = mid[0] + nx * span * t * 1.6, mid[1] + ny * span * t * 1.6
        h = z + 10.5 - 3.0 * (2 * t) ** 2
        m.add(("crystal_cyan" if k % 2 else "crystal_magenta", "wall"), lambda bm, x=x, y=y, h=h, k=k: ap.shard(bm, (x, y, h - 1.5), (0.1 * math.sin(k), 0.1, 1), 4.0, 0.9, n=5, tip=0.35))
    m.build(c, "Crystal Arch", "Monolith", "both")
    sc.cold.append((mid[0], mid[1], z + 8))
    sc.violet.append((mid[0], mid[1], z + 4))


def curtain(c, sc, ar, s0, s1, name="Waterfall Curtain"):
    """The giant waterfall: a sheet pouring out from the wall high above the gallery road,
    arching out over it and falling past the road's outer edge into the abyss. The road
    runs behind it; the sheet is part see-through."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    # (across: + toward the wall on the right, height above the road)
    prof = [(22.0, 66.0), (16.0, 50.0), (10.0, 36.0), (4.0, 26.0), (-1.5, 19.0), (-6.0, 13.5), (-9.5, 9.0), (-12.0, 4.5),
            (-13.0, -4.0), (-13.6, -24.0), (-14.0, -70.0), (-14.5, -140.0)]
    n = max(4, int((s1 - s0) / 2.0))
    rows = []
    for k in range(n + 1):
        q = c.at(s0 + (s1 - s0) * k / n)
        rows.append([bm.verts.new(q.p + q.r * o * (1 + 0.04 * math.sin(k * 0.9)) + Vector((0, 0, h))) for o, h in prof])
    lens = [0.0]
    for (a0, h0), (a1, h1) in zip(prof, prof[1:]):
        lens.append(lens[-1] + math.hypot(a1 - a0, h1 - h0))
    for k in range(n):
        u0, u1 = (s1 - s0) * k / n / 12.0, (s1 - s0) * (k + 1) / n / 12.0
        for j in range(len(prof) - 1):
            f = bm.faces.new((rows[k][j], rows[k + 1][j], rows[k + 1][j + 1], rows[k][j + 1]))
            for loop, uvp in zip(f.loops, ((u0, -lens[j] / 12), (u1, -lens[j] / 12), (u1, -lens[j + 1] / 12), (u0, -lens[j + 1] / 12))):
                loop[uv].uv = uvp
    ob = c.mesh_object(name, bm, "Water", "visual")
    ob.data.materials.append(c.lib("falls_curtain", "water"))
    kit.materials.ensure_paint(ob.data)
    kit.materials.keep_uvs(ob, range(len(ob.data.polygons)))
    # Mist where it pours past the road; spray and roar (the waterfall entity).
    q = c.at((s0 + s1) / 2)
    p = q.side(-12.5)
    gx, gy, gz = c.game(p.x, p.y, q.p.z + 3.5)
    c.entity("waterfall", x=gx, y=gy, z=gz, top=round(gz + 40, 1), width=round(s1 - s0, 1), heading=round(math.atan2(q.t.y, q.t.x), 3))
    return ob


def falls_sheet(c, x, y, top, foot, width, facing, mat=("icefall_rift", "wall"), name="Frozen Falls", bulge=2.5):
    """A waterfall (frozen or running) down a wall: a sheet from `top` to `foot`, bulging out
    from the wall a little, `facing` (dx, dy) out from the wall."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    fx, fy = facing
    fl = math.hypot(fx, fy) or 1
    fx, fy = fx / fl, fy / fl
    sx, sy = -fy, fx
    cols = 6
    rows = 8
    grid = []
    for j in range(rows + 1):
        t = j / rows
        z = top + (foot - top) * t
        out = bulge * math.sin(math.pi * min(1.0, t * 1.2)) + 0.8
        w = width * (0.8 + 0.4 * t)
        grid.append([bm.verts.new((x + sx * w * (i / cols - 0.5) + fx * out, y + sy * w * (i / cols - 0.5) + fy * out, z)) for i in range(cols + 1)])
    for j in range(rows):
        for i in range(cols):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            for loop, (u, v) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                loop[uv].uv = (u * width / cols / 7.0, v * (top - foot) / rows / 7.0)
    ob = c.mesh_object(name, bm, "Water", "visual")
    ob.data.materials.append(c.lib(*mat))
    kit.materials.ensure_paint(ob.data)
    kit.materials.keep_uvs(ob, range(len(ob.data.polygons)))
    return ob


def sheet(c, ring, z, mat, name, coll="Water", role="visual", hug=0.0):
    """A flat sheet over a closed outline (fog layers, the lake's ice). `hug`: cut into
    cells that size, and brought up beside the roads to meet their banked edges (the lake's
    ice: the road over it banks, and its high side stood a metre and more over the ice, a
    wall a kart that slid off couldn't climb back over)."""
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, z)) for x, y in ring]
    bm.faces.new(vs)
    if hug:
        c.hug(bm, z, hug)
    else:
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
    ob = c.mesh_object(name, bm, coll, role)
    c.assign(ob, c.lib(*mat))
    return ob


def rect(x0, x1, y0, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# ------------------------------------------------------------------ regions


def entrance(c, sc, ar):
    """The Shattered Entrance: the start gate, the snowfield's ice spikes and lanterns, the
    Rift's rim, the ice bridge, the great ice arch over the tunnel mouth, the tunnel's
    crystals (more and brighter the deeper it goes)."""
    P = sc.p
    # The start gate: two carved pylons topped with crystals, a banner between them.
    q = c.at(0.0)
    m = Mesh()
    for side in (-1, 1):
        p = q.side(side * (q.w / 2 + 3.5))
        m.add(CARVED, lambda bm, p=p: cuboid(bm, (p.x, p.y, q.p.z + 6.0), (3.2, 3.2, 13.0), road_rot(q)))
        m.add(STONE, lambda bm, p=p: cuboid(bm, (p.x, p.y, q.p.z + 12.9), (4.2, 4.2, 1.0), road_rot(q)))
        m.add(("crystal_cyan", "wall"), lambda bm, p=p: ap.shard(bm, (p.x, p.y, q.p.z + 13.2), (0, 0, 1), 7.0, 1.4, n=6, tip=0.35))
        sc.cold.append((p.x, p.y, q.p.z + 16))
        sc.lanterns.append((p.x, p.y, q.p.z + 15))
    a, b = q.side(-(q.w / 2 + 2.0), 11.5), q.side(q.w / 2 + 2.0, 11.5)
    m.add(("start_checker", "wall"), lambda bm: cuboid(bm, ((a.x + b.x) / 2, (a.y + b.y) / 2, a.z - 0.6), ((a - b).length, 0.5, 2.6), road_rot(q) + math.pi / 2))
    m.build(c, "Start Gate", "Props", "both")
    # Ice spikes and snowy rocks over the snowfield, lantern posts along the roads.
    for k in range(70):
        x = -380 + rnd(k * 3 + 1) * 640
        y = -470 + rnd(k * 3 + 2) * 270
        if not clear(c, x, y, 16.0) or y > ar.rim_y(x) - 6:
            continue
        z = sc.land(x, y)
        if k % 3 == 0:
            sc.put(ap.snow_rock(c, k % 3, 3.0 + 2 * rnd(k)), x, y, z - 0.6, rot=k, coll="Snowfield")
        else:
            sc.put(ap.ice_spike(c, k % 4, 10.0 + 14 * rnd(k * 5)), x, y, z - 1.0, rot=k * 0.7, coll="Snowfield")
    for s in [s for a, b, step in P["snow_lamps"] for s in range(int(a), int(b), int(step))]:
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 2.6))
            if p.y > ar.rim_y(p.x) - 2:
                continue
            sc.put(ap.lantern_post(c), p.x, p.y, sc.land(p.x, p.y) - 0.15, rot=road_rot(q), coll="Snowfield")
            sc.warm.append((p.x, p.y, q.p.z + 2.4))
            if side > 0:
                sc.lanterns.append((p.x, p.y, q.p.z + 2.4))
    # The Rift's rim: icicles over the edge, ice spikes along it.
    for k in range(60):
        x = -760 + k * 22.0
        y = ar.rim_y(x) - 1.0
        smp, d = c.nearest(x, y)
        if d < smp.w / 2 + 4:
            continue
        z = ar.snowfield(x, y - 4)
        sc.put(ap.icicle_fringe(c, k % 3, 14.0, 6.0 + 4 * rnd(k)), x, y + 1.5, z - 0.5, rot=0.0, coll="Rift")
        if k % 3 == 0 and clear(c, x, y - 6, 8):
            sc.put(ap.ice_spike(c, k % 4, 9.0 + 9 * rnd(k * 7)), x, y - 6, z - 1.0, rot=k, coll="Rift")
    # The descent's ledge: icicles under its edge, crystals in the wall.
    l0, ln = P["ledge"]
    for k in range(ln):
        q = c.at(l0 + k * 10)
        p = q.side(-(q.w / 2 + 1.0))
        sc.put(ap.icicle_fringe(c, k % 3, 9.0, 5.0), p.x, p.y, q.p.z - 7.0, rot=road_rot(q), coll="Rift")
        if k % 3 == 1:
            w = q.side(q.w / 2 + 3.5)
            sc.put(ap.fan(c, k % 4, 9.0, ap.CRYSTALS[k % 4]), w.x, w.y, q.p.z + 3.0, rot=road_rot(q) + math.pi, coll="Rift")
            sc.cold.append((w.x, w.y, q.p.z + 6))
    # The natural ice bridge over the Rift, and the great ice arch over the tunnel mouth.
    b0, s_face, s_lim = P["ice_bridge"]
    while c.at(s_face).p.y < ar.face_y(c.at(s_face).p.x) - 6 and s_face < s_lim:
        s_face += 1.0
    ice_span(c, sc, b0, s_face - 2, depth=26.0, name="Rift Ice Bridge")
    q = c.at(s_face - 4)
    sc.put(_big_arch(c, 46.0, 40.0), q.p.x, q.p.y, q.p.z - 1.0, rot=road_rot(q) + math.pi / 2, coll="Rift")
    # The tunnel: crystals along its walls and roof, denser and bigger toward the end.
    t0, t1 = s_face + 4, P["tunnel_end"]
    k = 0
    s = t0
    while s < t1:
        f = (s - t0) / (t1 - t0)
        q = c.at(s)
        for side in (-1, 1):
            if rnd(k * 7 + side) < 0.35 + 0.6 * f:
                p = q.side(side * (q.w / 2 + 2.5 + 2 * f))
                h = 3 + 9 * f
                sc.put(ap.needles(c, k % 3, h, ap.CRYSTALS[(k + side) % 4]), p.x, p.y, q.p.z - 0.5, rot=k, coll="Tunnels")
                if f > 0.3:
                    sc.cold.append((p.x, p.y, q.p.z + 3))
        if f > 0.4 and k % 2 == 0:
            sc.put(ap.hanging(c, k % 3, 4 + 6 * f, ap.CYAN), q.p.x, q.p.y, q.p.z + 13.0 + 6 * f ** 3, rot=k, coll="Tunnels")
        s += 7.0 - 3.0 * f
        k += 1


def _big_arch(c, span, height):
    """A colossal natural arch of glacier ice (origin at the road's middle, spanning X)."""
    name = "Great Ice Arch %d" % int(span)

    def build(bm):
        pts, radii = [], []
        n = 16
        for k in range(n + 1):
            t = k / n
            a = math.pi * t
            pts.append((-math.cos(a) * (span / 2 + 6.0), 2.5 * math.sin(a * 2), math.sin(a) ** 0.7 * height - 4))
            radii.append((7.0 - 2.5 * math.sin(a)) * (1 + 0.2 * math.sin(k * 2.3)))
        tube(bm, pts, radii, n=8)
        for v in bm.verts:
            v.co += Vector((0.8 * math.sin(v.co.z * 0.5), 0.8 * math.cos(v.co.x * 0.4), 0.6 * math.sin(v.co.x * 0.7)))
        ice = _faces(bm, 0)
        k0 = len(bm.faces)
        for k in range(3, n - 2):
            x, y, z = pts[k]
            res = bmesh.ops.create_cone(bm, cap_ends=False, segments=4, radius1=0.0, radius2=0.5, depth=4 + 4 * rnd(k))
            for v in res["verts"]:
                v.co += Vector((x, y + 2 * math.sin(k), z - radii[k] * 0.8 - 2))
        k1 = len(bm.faces)
        for k in range(2, n - 1, 3):
            x, y, z = pts[k]
            ap.shard(bm, (x, y, z + radii[k] * 0.6), (0.2 * math.sin(k), 0.3, 1), 6 + 4 * rnd(k), 1.2, n=6, tip=0.3)
        return [(c.lib(*ICEWALL), ice), (c.lib("icefall_rift"), list(range(k0, k1))), (c.lib("crystal_cyan"), _faces(bm, k1))]

    return ap._p(c, name, build)


def cathedral(c, sc, ar, info, lp, s_in, s_out):
    """The Crystal Cathedral: the Monolith and its island, the bridges, the waterfall
    curtain, the Loop's pedestal, crystal forests round the walls and down in the abyss,
    crystals hanging from the roof, mist layers."""
    P = sc.p
    ring, centre = info["cathedral"]
    mx, my = ar.MONOLITH
    # The island: open where the bridges arrive and leave.
    # (Wherever the road crosses the rim, with room either side.)
    gaps = []
    rt = P["island_r"]
    for smp in c.S:
        r = math.hypot(smp.p.x - mx, smp.p.y - my)
        if rt - 6.0 <= r <= rt + 4.0 and abs(smp.p.z - ar.Z_CATH) < 3:
            gaps.append((math.atan2(smp.p.y - my, smp.p.x - mx), (smp.w / 2 + 4.0) / r))
    island(c, sc, ar, r_top=rt, gaps=gaps, drop=P["island_drop"], role=P["island_role"])
    monolith(c, sc, ar)
    if getattr(ar, "MONO_SHORT", None):
        crystal_arch(c, sc, ar)
    # The suspended bridge (stone arches), the ice span to the north wall.
    for k, (a, b) in enumerate(P["cath_bridges"]):
        arch_bridge(c, sc, a, b, 120.0, every=26.0, name="Cathedral Bridge %d" % k if k else "Cathedral Bridge")
    if P["north_span"]:
        ice_span(c, sc, *P["north_span"], depth=26.0, name="North Ice Span")
    # The ledges round the east wall and along the north wall: icicles and lamps.
    for a, b in P["cath_ledges"]:
        k = 0
        s = a
        while s < b:
            q = c.at(s)
            p = q.side(-(q.w / 2 + 1.2))
            sc.put(ap.icicle_fringe(c, k % 3, 10.0, 6.0), p.x, p.y, q.p.z - 8.5, rot=road_rot(q), coll="Cathedral")
            if k % 2 == 0:
                sc.put(ap.lantern_post(c), p.x, p.y, q.p.z - 0.1, rot=road_rot(q), coll="Cathedral")
                sc.warm.append((p.x, p.y, q.p.z + 2.4))
                if k % 4 == 0:
                    sc.lanterns.append((p.x, p.y, q.p.z + 2.4))
            s += 12.0
            k += 1
    # The waterfall curtain over the north-wall gallery.
    if P["curtain"]:
        curtain(c, sc, ar, *P["curtain"])
    for k in range(P["curtain_needles"] if P["curtain"] else 0):
        q = c.at(P["curtain"][0] + 4 + k * 7.5)
        w = q.side(q.w / 2 + 3.0)
        sc.put(ap.needles(c, k % 3, 8.0 + 5 * (k % 2), ap.CRYSTALS[k % 4]), w.x, w.y, q.p.z - 0.5, rot=k, coll="Cathedral")
        sc.cold.append((w.x, w.y, q.p.z + 4))
        sc.shimmer.append((w.x, w.y, q.p.z + 0.5, k))
    # The causeway to the Loop: arches under it; the Loop's pedestal; crystals framing it.
    arch_bridge(c, sc, P["causeway"], s_in, 120.0, every=22.0, name="Causeway", lamps=10.0)
    arch_bridge(c, sc, s_out, P["far_causeway"], 120.0, every=22.0, name="Far Causeway", lamps=10.0)
    loop_pedestal(c, sc, ar, lp)
    for k in range(int((s_in - P["causeway"] - 2) / 9)):
        q = c.at(P["causeway"] + 6 + k * 9)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 1.0))
            sc.shimmer.append((p.x, p.y, q.p.z + 0.9, k * 2 + (side > 0)))
    # Crystal forests: hero spire clusters against the walls, fans and needles on the
    # wall ledges, gardens down in the abyss, crystals hanging from the roof.
    n = len(ring)
    for k in range(0, n, 3):
        x, y = ring[k]
        dx, dy = centre[0] - x, centre[1] - y
        dl = math.hypot(dx, dy) or 1
        # Step in from the wall a little.
        px, py = x + dx / dl * 10, y + dy / dl * 10
        if not clear(c, px, py, 10.0, [getattr(ar, "MONO_SHORT", [])]):
            continue
        r = rnd(k * 13)
        if k % 9 == 0:
            h = 55 + 45 * r
            sc.put(ap.spire_cluster(c, k % 4, h, ap.CRYSTALS[k % 4], ap.CRYSTALS[(k + 1) % 4]), px, py, ar.ABYSS + 40 + 30 * rnd(k), rot=k, coll="Cathedral")
        elif k % 3 == 0:
            z = ar.Z_CATH - 30 + 60 * r
            sc.put(ap.fan(c, k % 4, 14.0 + 8 * r, ap.CRYSTALS[k % 4]), px, py, z, rot=math.atan2(dy, dx) - math.pi / 2, coll="Cathedral")
        sc.cold.append((px, py, ar.Z_CATH))
    for k in range(40):
        a = k * 2.399
        rr = 40 + 150 * math.sqrt(rnd(k * 5 + 1))
        x, y = centre[0] + rr * math.cos(a), centre[1] + rr * math.sin(a) * 0.7
        if not inside(ring, x, y) or math.hypot(x - mx, y - my) < 70:
            continue
        sc.put(ap.garden(c, k % 4, 16.0), x, y, ar.ABYSS + 2, rot=k, coll="Abyss")
        if k % 4 == 0:
            sc.put(ap.spire_cluster(c, (k // 4) % 4, 70 + 30 * rnd(k), ap.CRYSTALS[k % 4], ap.CRYSTALS[(k + 2) % 4]), x + 8, y, ar.ABYSS, rot=k, coll="Abyss")
    for k in range(28):
        a = k * 2.399 + 1.0
        rr = 30 + 260 * math.sqrt(rnd(k * 9 + 4))
        x, y = centre[0] + rr * math.cos(a), centre[1] + rr * math.sin(a) * 0.45
        roof = roof_z(ring, centre, ar.Z_CATH + 62, ar.Z_CATH + 128, x, y)
        if roof is None or math.hypot(x - ar.LOOP_IN[0], y - ar.LOOP_IN[1]) < 60 or math.hypot(x - mx, y - my) < 40:
            continue
        roof -= 4.0  # the dome's wobble: tuck them up into it
        sc.put(ap.hanging(c, k % 4, 26 + 26 * rnd(k), ap.CRYSTALS[k % 4]), x, y, roof + 3, rot=k, scale=1.8, coll="Cathedral")
        (sc.cold if k % 3 else sc.violet).append((x, y, roof - 10))
    # Mist layers in the abyss.
    sheet(c, ring, -70.0, ("abyss_fog", "water"), "Abyss Mist", role="visual")
    sheet(c, ring, -115.0, ("abyss_fog", "water"), "Deep Mist", role="visual")
    # Frozen falls down the walls, and one that still runs (east wall, by the reveal).
    for k, idx in enumerate(range(5, n, n // 6)):
        x, y = ring[idx]
        dx, dy = centre[0] - x, centre[1] - y
        if not clear(c, x, y, 12.0):
            continue
        mat = ("falls_rift", "water") if k == 0 else ("icefall_rift", "wall")
        falls_sheet(c, x + dx * 0.02, y + dy * 0.02, ar.Z_CATH + 58, -60.0, 18.0 + 6 * (k % 2), (dx, dy), mat=mat, name="Cathedral Falls")


def loop_pedestal(c, sc, ar, lp):
    """The Rift Loop's pedestal: a great column of rock and ice rising from the abyss under
    the Loop (its top just under the Loop's road), crystals growing up both its sides and
    huge crystals flanking the Loop itself."""
    mid = lp.point(lp.L / 2)
    a = lp.origin
    b = lp.exit
    cx = (a.x + b.x) / 2 + lp.fwd.x * 2
    cy = (a.y + b.y) / 2 + lp.fwd.y * 2
    bm = bmesh.new()
    n = 32
    rings = []
    top = ar.Z_CATH - 2.0
    rx, ry = 34.0, 30.0
    h = math.radians(lp.head)
    for j, (zz, rr) in enumerate(((ar.ABYSS - 20, 0.6), (-60, 0.7), (-10, 0.82), (top - 8, 0.95), (top, 1.0))):
        ring = []
        for k in range(n):
            t = k * math.tau / n
            f = rr * (1 + 0.07 * math.sin(3 * t + j) + 0.05 * math.sin(5 * t + j * 2))
            lx, ly = rx * f * math.cos(t), ry * f * math.sin(t)
            ring.append(bm.verts.new((cx + lx * math.cos(h) - ly * math.sin(h), cy + lx * math.sin(h) + ly * math.cos(h), zz)))
        rings.append(ring)
    loft(bm, rings, cap_top=True, cap_bottom=True)
    ob = c.mesh_object("Loop Pedestal", bm, "Island", "both")
    c.assign(ob, c.lib(*CLIFF))
    ob.data.shade_flat()
    # Crystals: up the pedestal's flanks and two huge ones framing the Loop.
    side = lp.right
    for k, (off, ln, mat) in enumerate(((-26, 48, ap.CYAN), (lp.offset + 26, 52, ap.VIOLET), (-20, 30, ap.TEAL), (lp.offset + 20, 34, ap.MAGENTA))):
        along = 4 if k < 2 else 30
        p = a + lp.fwd * along + side * off
        lean = side * (0.25 if off < 0 else -0.25)
        name = "Loop Crystal %d" % k
        m = Mesh()
        m.add((mat, "wall"), lambda bm, p=p, lean=lean, ln=ln: ap.shard(bm, (p.x, p.y, top - 30), (lean.x, lean.y, 1), ln + 30, 5.0, n=6, tip=0.18))
        m.build(c, name, "Island", "visual")
        sc.cold.append((p.x, p.y, ar.Z_CATH + 10))
    sc.cold.append((mid.x, mid.y, mid.z))


def lake(c, sc, ar, info):
    """Mirror Lake: the ice (a driving surface, part clear: the cavern's floor far below
    shows through, with everything round it reflected upside down), ice columns rising
    from it, crystals round its shores, icicles and crystals hanging from its roof."""
    lring, lcentre = info["lake"]
    short = getattr(ar, "LAKE_SHORT", [])
    cx, cy = lcentre
    # The ice: the cavern's outline pulled in a little (the walls meet it).
    inner = [(cx + (x - cx) * 0.97, cy + (y - cy) * 0.97) for x, y in lring]
    ice = sheet(c, inner, ar.Z_LAKE, ("mirror_ice", "ice"), "Mirror Lake", coll="Lake", role="both", hug=2.5)
    # Ice columns from the depths to the roof, where the road can weave round them.
    cols = 0
    for k in range(60):
        a = k * 2.399
        rr = 120 * math.sqrt(rnd(k * 3 + 2))
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        if not inside(inner, x, y) or not clear(c, x, y, 12.0, [short]):
            continue
        sc.put(ap.ice_column(c, cols % 4, 70.0, 5.5 + 2 * rnd(k)), x, y, ar.Z_LAKE - 0.5, rot=k, coll="Lake", mirror=True)
        sc.cold.append((x, y, ar.Z_LAKE + 3))
        cols += 1
        if cols >= 7:
            break
    # Crystals round the shore (reflected), crystals and icicles hanging from the roof.
    n = len(lring)
    for k in range(0, n, 2):
        x, y = lring[k]
        dx, dy = cx - x, cy - y
        dl = math.hypot(dx, dy) or 1
        px, py = x + dx / dl * 8, y + dy / dl * 8
        if not clear(c, px, py, 7.0, [short]):
            continue
        if k % 4 == 0:
            sc.put(ap.spire_cluster(c, k % 4, 26 + 16 * rnd(k), ap.CRYSTALS[k % 4], ap.CRYSTALS[(k + 1) % 4]), px, py, ar.Z_LAKE - 1, rot=k, coll="Lake", mirror=True)
        else:
            sc.put(ap.needles(c, k % 3, 12 + 10 * rnd(k), ap.CRYSTALS[(k + 2) % 4]), px, py, ar.Z_LAKE - 0.5, rot=k, coll="Lake", mirror=True)
        (sc.cold if k % 3 else sc.violet).append((px, py, ar.Z_LAKE + 2))
    for k in range(26):
        a = k * 2.399 + 0.5
        rr = 110 * math.sqrt(rnd(k * 7 + 3))
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        if not inside(inner, x, y):
            continue
        roof = ar.Z_LAKE + 30 + 30 * (1 - min(1.0, rr / 130))
        if k % 2:
            sc.put(ap.icicle_fringe(c, k % 3, 10.0, 14 + 10 * rnd(k)), x, y, roof, rot=k, coll="Lake", mirror=True)
        else:
            sc.put(ap.hanging(c, k % 4, 14 + 10 * rnd(k), ap.CRYSTALS[k % 4]), x, y, roof, rot=k, coll="Lake", mirror=True)
    # Falls feeding the lake from the back wall.
    for k, idx in enumerate((n // 5, n // 2)):
        x, y = lring[idx]
        falls_sheet(c, x, y, ar.Z_LAKE + 34, ar.Z_LAKE - 0.5, 10.0, (cx - x, cy - y), mat=("falls_rift", "water"), name="Lake Falls")
        gx, gy, gz = c.game(x, y, ar.Z_LAKE)
        c.entity("waterfall", x=gx, y=gy, z=gz, top=round(gz + 30, 1), width=10.0, heading=round(math.atan2(-(cx - x), cy - y), 3))
    # The reflections: every prop above, upside down under the ice.
    for proto, x, y, z, rot, scale in sc.mirror:
        c.place(proto, x, y, 2 * ar.Z_LAKE - z, rot=rot, scale=(scale, scale, -scale), coll="Reflections", role="visual")
    return ice


def ascent(c, sc, ar):
    """The Aurora Ascent: crystals up the ice tunnel, natural arches over the canyon, falls
    down its walls, then the great opening in the glacier's face."""
    P = sc.p
    s, s_end = P["ascent_crystals"]
    k = 0
    while s < s_end:
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 3.0))
            sc.put(ap.needles(c, k % 3, 6 + 5 * rnd(k + side), ap.CRYSTALS[(k + 3 * side) % 4]), p.x, p.y, q.p.z - 0.5, rot=k, coll="Tunnels")
            sc.cold.append((p.x, p.y, q.p.z + 3))
        s += 8.0
        k += 1
    # The canyon: natural ice arches across it, crystals up its walls, frozen falls,
    # lanterns along the climb.
    for k, s in enumerate(P["canyon_arches"]):
        q = c.at(s)
        sc.put(ap.ice_arch_big(c, 30.0, 17.0 + 3 * k), q.p.x, q.p.y, q.p.z - 1.0, rot=road_rot(q) + math.pi / 2, coll="Canyon")
        sc.cold.append((q.p.x, q.p.y, q.p.z + 16))
    s, s_end = P["canyon_lamps"]
    k = 0
    while s < s_end:
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 0.9))
            if k % 2 == 0:
                sc.put(ap.lantern_post(c), p.x, p.y, q.p.z - 0.1, rot=road_rot(q), coll="Canyon")
                sc.warm.append((p.x, p.y, q.p.z + 2.4))
                if side > 0 and k % 4 == 0:
                    sc.lanterns.append((p.x, p.y, q.p.z + 2.4))
            w = q.side(side * 12.0)
            if (k + (side > 0)) % 3 == 0:
                sc.put(ap.fan(c, k % 4, 7.0 + 4 * rnd(k), ap.CRYSTALS[(k + side) % 4]), w.x, w.y, q.p.z + 6 + 10 * rnd(k * 3 + side),
                       rot=road_rot(q) + (math.pi / 2 if side > 0 else -math.pi / 2), coll="Canyon")
                sc.cold.append((w.x, w.y, q.p.z + 8))
        s += 12.0
        k += 1
    for k in range(5):
        q = c.at(P["canyon_falls"] + k * 16)
        side = 1 if k % 2 else -1
        p = q.side(side * 12.5)
        falls_sheet(c, p.x, p.y, q.p.z + 46, q.p.z + 1, 7.0, (-q.r.x * side, -q.r.y * side), name="Canyon Falls", bulge=1.5)
    # The great opening: crystals round its mouth.
    q = c.at(P["opening_at"])
    for side in (-1, 1):
        p = q.side(side * 26.0)
        sc.put(ap.spire_cluster(c, 1 + (side > 0), 40.0, ap.CYAN if side < 0 else ap.VIOLET, ap.TEAL), p.x, p.y, q.p.z - 4, rot=side, coll="Canyon")
        sc.cold.append((p.x, p.y, q.p.z + 8))


def rift(c, sc, ar):
    """The Rift itself: frozen falls down the glacier's face, crystals in it, mist far
    below, crystal gardens on the chasm's floor, the Great Rift Bridge."""
    for k in range(9):
        x = -740 + k * 115.0 + 30 * rnd(k)
        smp, d = c.nearest(x, ar.face_y(x))
        if d < 40:
            continue
        y = ar.face_y(x) - 3.0
        top = ar.glacier_top(x, ar.face_y(x)) - 6
        falls_sheet(c, x, y - 6, top, ar.ABYSS + 30, 8.0 + 6 * rnd(k * 3), (0, -1), name="Face Falls", bulge=7.0)
    for k in range(30):
        x = -760 + k * 36.0
        y = ar.face_y(x) - 2.0
        if not clear(c, x, y, 20):
            continue
        z = -30 + 90 * rnd(k * 5)
        sc.put(ap.fan(c, k % 4, 10 + 8 * rnd(k), ap.CRYSTALS[k % 4]), x, y, z, rot=-math.pi / 2, coll="Rift")
        sc.cold.append((x, y - 4, z + 6))
    for k in range(24):
        x = -900 + k * 60.0
        sheet(c, rect(x, x + 60, ar.rim_y(x) - 2, ar.face_y(x) + 6), -75.0 - 8 * (k % 2), ("abyss_fog", "water"), "Rift Mist")
        if k % 2 == 0:
            y = (ar.rim_y(x) + ar.face_y(x)) / 2
            sc.put(ap.garden(c, k % 4, 16.0), x + 30, y, ar.ABYSS + 4, rot=k, coll="Abyss")
    # The Great Rift Bridge: tall carved piers down into the mist, lanterns, crystals.
    g0, g1 = sc.p["great_bridge"]
    arch_bridge(c, sc, g0, g1, 160.0, every=28.0, pier=(9.0, 11.0), name="Great Rift Bridge", lamps=10.0)
    for k in range(5):
        q = c.at(g0 + 6 + k * (g1 - g0 - 12) / 4)
        for side in (-1, 1):
            p = q.side(side * 8.0)
            sc.put(ap.fan(c, k % 4, 8.0, ap.CRYSTALS[(k + side) % 4]), p.x, p.y, q.p.z - 14.0, rot=road_rot(q) + (math.pi / 2) * side, coll="Bridges")
            sc.cold.append((p.x, p.y, q.p.z - 10))


def skyline(c, sc, ar):
    """Ice spires on the glacier's top and the far mountains: silhouettes against the aurora."""
    x0, x1, y0, y1 = ar.MASSIF
    for k in range(40):
        x = x0 + (x1 - x0) * rnd(k * 3 + 11)
        y = y0 + 30 + (y1 - y0 - 30) * rnd(k * 3 + 12)
        z = ar.glacier_top(x, y)
        sc.put(ap.ice_spike(c, k % 4, 20 + 30 * rnd(k)), x, y, z - 3, rot=k, coll="Glacier Top")


# ------------------------------------------------------------------ build


def game_entity(c, kind, x, y, z, **extra):
    gx, gy, gz = c.game(x, y, z)
    c.entity(kind, x=gx, y=gy, z=gz, **extra)


def spots(c, ar, s_in, s_out):
    """Where things go along the lap: the first Aurora Rift's, unless the course module
    has its own (`scenery_spots(c, s_in, s_out)`, which may set any of these). Lap
    distances are road distances (c.at)."""
    S = ar.SEG
    L = ar.LENGTH
    P = {
        # Cut out of the glacier.
        "entrance_cut": (S[6] + 45, S[8] + 6),
        "cath_segs": (8, 19),
        "cath_extra": [(-430.0, 0.0), (-300.0, -20.0), (-120.0, 25.0), (60.0, 30.0)],
        "crystal_tunnel": (S[19] + 5, S[22] + 10),
        "lake_segs": (21, 24),
        "ice_tunnel": (S[24] + 40, S[26] + 10),
        "canyon_cut": (S[26] + 4, S[27] + 20),
        "opening_cut": (S[27] + 14, S[29] + 22),
        "face_fractures": (-300.0, -200.0, -40.0),
        # The Shattered Entrance.
        "snow_lamps": [(20.0, S[2], 26.0), (S[30], L - 30, 30.0)],
        "ledge": (S[1] + 30, int((S[6] - S[1]) / 10)),
        "ice_bridge": (S[5] + 20, S[6], S[7] + 40),
        "tunnel_end": S[8] + 4,
        # The Cathedral.
        "island_r": 66.0,
        "island_drop": 0.25,
        "island_role": "both",
        "mono_r": 22.0,
        "mono_foot": 28.0,
        "cath_bridges": [(S[12] - 6, S[13] + 4)],
        "north_span": (S[14] - 4, S[15] + 4),
        "cath_ledges": [(S[8] + 8, S[11] + 20), (S[15], S[17])],
        "curtain": (S[16] + 2, S[17] - 4),
        "curtain_needles": 10,
        "causeway": S[17] - 2,
        "far_causeway": S[20],
        "deco_spans": [(-130.0, 40.0, 9.0, "High Bridge"), (70.0, -34.0, 7.0, "Low Bridge")],
        # The ascent and the Great Rift Bridge.
        "ascent_crystals": (S[24] + 44, S[26] + 6),
        "canyon_arches": (S[26] + 14, S[26] + 46, S[27] + 10),
        "canyon_lamps": (S[25] + 10, S[28] + 30),
        "canyon_falls": S[26] + 6,
        "opening_at": S[28] + 50,
        "great_bridge": (S[29] - 6, S[30] + 6),
        # Hazards on the road: falling ice in the tunnel and canyon, a cracking patch
        # at the edge of the lake's line.
        "road_icicles": [(S[25] + 12, -3.0), (S[25] + 40, 3.5), (S[26] + 50, 0.0)],
        "lake_crack": S[23] + 40,
    }
    if hasattr(ar, "scenery_spots"):
        P.update(ar.scenery_spots(c, s_in, s_out))
    return P


def build(c, ar, lp, s_in, s_out):
    X0, X1, Y0, Y1 = -1000.0, 620.0, -560.0, 700.0
    sc = Scene(c, ar)
    sc.p = spots(c, ar, s_in, s_out)
    solid, info = caverns(c, ar, sc.p)
    c.terrain("Land", X0, X1, Y0, Y1, 8.0, ar.natural, ar.classify, near=8.5, fade=7.0, verge_fill=1.5, fine=4)

    def under(x, y):
        if c.nearest(x, y)[1] > 70:
            return None
        return min(ar.natural(x, y), c.road_height(x, y, 8.5, 7.0, 0.2, ar.natural(x, y))[1]) - 0.6

    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 8.0, under, c.lib("abyss_glow", "abyss"))
    c.start_line()

    entrance(c, sc, ar)
    cathedral(c, sc, ar, info, lp, s_in, s_out)
    multilevel(c, sc, ar, info)
    lake(c, sc, ar, info)
    ascent(c, sc, ar)
    rift(c, sc, ar)
    skyline(c, sc, ar)
    gameplay(c, sc, ar, s_in, s_out)

    groups = ("Props", "Snowfield", "Rift", "Tunnels", "Cathedral", "Abyss", "Bridges", "Monolith", "Lake", "Reflections", "Canyon", "Glacier Top", "Crystals")
    c.merge_props(groups)
    joined = [o for name in groups for o in c.coll(name).objects if o.type == "MESH" and o.data.users == 1]
    ter = list(c.coll("Terrain").objects)
    rocks = [solid] + list(c.coll("Island").objects) + list(c.coll("Bridges").objects)
    # Light: the caverns dim and blue, lit cyan and violet by their crystals, warm round
    # every lantern; the snowfield moonlit.
    cave = lambda w: ar.in_massif(w.x, w.y, -2) and w.z < ar.glacier_top(w.x, w.y) - 8  # noqa: E731
    c.glow(rocks + ter + joined, sc.cold, 36.0, (0.8, 1.2, 1.45), base=(0.62, 0.7, 0.92), region=cave)
    c.glow(rocks + ter + joined, sc.violet, 30.0, (1.2, 0.85, 1.45), base=1.0, region=cave)
    c.glow(rocks + ter + joined, sc.warm, 14.0, (1.5, 1.15, 0.7), base=1.0)
    c.preset("sun", ter, 0.2)
    kit.paint.shade_roads(c.pieces, 0.25)


def gameplay(c, sc, ar, s_in, s_out):
    """Pickups, boosts, checkpoints (with twin gates on both shortcuts), and the living
    parts: crystals that flare as you pass, ice motes in the air, falling ice, cracking
    ice on the lake, the lanterns' light."""
    if hasattr(ar, "pickups"):
        # The course's own pickups, boosts and checkpoints.
        ar.pickups(c, s_in, s_out)
    else:
        first_pickups(c, ar, s_in, s_out)
    living(c, sc, ar)


def first_pickups(c, ar, s_in, s_out):
    """The first Aurora Rift's pickups, boosts and checkpoints."""
    S = ar.SEG
    # Zippers: off the start, down the ice wall, round the cliffside drift, the boost
    # strip into the Loop, off the lake, up the canyon, off the Great Rift Bridge, and
    # down the final descent.
    for at in (40, S[3] + 10, S[9] + 70, s_in - 42, S[24] + 70, S[26] + 40, S[30] + 8, S[33] + 10):
        c.zipper(at, 0)
    for at, across in ((90, 0), (S[5] + 10, 0), (S[10] + 10, -3), (S[14] + 20, 0), (S[16] + 30, 3), (S[21] + 20, 0), (S[25] + 20, 0), (S[29] + 60, 0), (S[32] + 20, 0)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in ((100, -4, "red"), (100, 4, "green"), (S[6] + 20, 0, "blue"), (S[9] + 30, -4, "yellow"), (S[9] + 30, 4, "rainbow"),
                            (S[12] + 50, 0, "red"), (S[19] + 20, 0, "blue"), (S[23] + 30, -5, "green"), (S[23] + 30, 5, "red"), (S[27] + 30, 0, "yellow"),
                            (S[31] + 60, -4, "rainbow"), (S[31] + 60, 4, "blue")):
        c.balloon(at, across, col)

    # Checkpoints. Round the two shortcuts: a gate just before and just after the stretch
    # each skips and one in the middle, with a twin across the shortcut; none elsewhere
    # in those stretches. None inside the Loop (a gap: added automatically).
    def stretch(pts):
        a = kit.s_near(c, *pts[0])
        b = kit.s_near(c, *pts[-1])
        return a, b, (a + b) / 2

    m_in, m_out, m_apex = stretch(ar.MONO_SHORT)
    l_in, l_out, l_apex = stretch(ar.LAKE_SHORT)
    gates = c.checkpoints(
        extra=[S[2] + 10, S[6] + 10, S[7] + 40, S[9] + 40, S[12] + 20, m_in - 5, m_apex, m_out + 5, S[15] + 20, s_in - 25, s_out + 15,
               S[21] + 10, l_in - 5, l_apex, l_out + 5, S[25] + 20, S[27] + 20, S[29] + 30, S[31] + 60, S[34]],
        avoid=[(m_in - 2, m_apex - 6), (m_apex + 6, m_out + 2), (l_in - 2, l_apex - 6), (l_apex + 6, l_out + 2)],
        height=9.0,
    )
    for (apex, pts, route, z) in ((m_apex, ar.MONO_SHORT, "crystal_arch", ar.Z_CATH), (l_apex, ar.LAKE_SHORT, "thin_ice", ar.Z_LAKE + 0.25)):
        main_gate = min(gates.items(), key=lambda kv: abs(kv[0] - apex))[1]
        mid = len(pts) // 2
        c.alt_gate(main_gate, route, [(x, y, z) for x, y in pts[mid - 1:mid + 2]], width=16.0)


def living(c, sc, ar):
    """The living parts: crystals that flare as you pass, ice motes in the air, falling
    ice, cracking ice on the lake, the lanterns' light."""
    # Crystals that flare as you pass (along the gallery and the causeway).
    cols = ["#5ae8ff", "#b07aff", "#4affd0", "#ff6ad0"]
    for x, y, z, k in sc.shimmer:
        game_entity(c, "shimmer", x, y, z, size=round(1.2 + 0.5 * (k % 3), 2), color=cols[k % 4])
    # Ice motes drifting in the air.
    c.entity("sparkles", rate=36, radius=34)
    # Falling ice: icicles that drop on a fixed beat where the roof hangs low (the ice
    # tunnel and the canyon; a ring on the road warns), and a few out over the abyss.
    for k, (s, across) in enumerate(sc.p["road_icicles"]):
        q = c.at(s)
        p = q.side(across)
        game_entity(c, "icicle", p.x, p.y, q.p.z, top=round(q.p.z + 14.0, 1), period=9.0, offset=round(2.0 + k * 3.1, 2), warn=1.6, r=3.2)
    ring, centre = sc_info_ring(c, ar, sc.p["cath_segs"])
    for k in range(5):
        a = k * 1.3
        x, y = centre[0] + 120 * math.cos(a), centre[1] + 90 * math.sin(a)
        if clear(c, x, y, 20):
            game_entity(c, "icicle", x, y, ar.Z_CATH - 20, top=round(ar.Z_CATH + 70, 1), period=7.0 + k, offset=k * 1.7, warn=0.0, r=4.0, decor=True)
    # Cracking ice: patches on the thin-ice shortcut, and one at the edge of the main line.
    pts = getattr(ar, "LAKE_SHORT", [])
    for k, f in enumerate((0.3, 0.7) if pts else ()):
        x = pts[0][0] + (pts[-1][0] - pts[0][0]) * f
        y = pts[0][1] + (pts[-1][1] - pts[0][1]) * f
        game_entity(c, "thin_ice", x, y, ar.Z_LAKE + 0.3, r=6.5, hold=7.0)
    if sc.p["lake_crack"] is not None:
        q = c.at(sc.p["lake_crack"])
        p = q.side(5.5)
        game_entity(c, "thin_ice", p.x, p.y, ar.Z_LAKE + 0.45, r=5.5, hold=6.0)
    # Lanterns: the nearest few light the scene.
    for x, y, z in sc.lanterns:
        game_entity(c, "lantern", x, y, z)


def sc_info_ring(c, ar, segs=(8, 19)):
    pts = [(p[0], p[1]) for p in ar.PATH if segs[0] <= p[3] <= segs[1]]
    h = hull(pts)
    cx = sum(p[0] for p in h) / len(h)
    cy = sum(p[1] for p in h) / len(h)
    return h, (cx, cy)


def deco_span(c, sc, ar, ring, x0, y0, x1, y1, z, width=9.0, name="High Bridge"):
    """A decorative bridge high across the Cathedral (not part of the race: seen from
    below and across the abyss, so you see roads at several heights): a stone deck on
    arches, lanterns along its parapets."""
    m = Mesh()
    L = math.hypot(x1 - x0, y1 - y0)
    dx, dy = (x1 - x0) / L, (y1 - y0) / L
    rot = math.atan2(dy, dx)
    n = max(2, int(L / 8))
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n
        cx = x0 + (x1 - x0) * (t0 + t1) / 2
        cy = y0 + (y1 - y0) * (t0 + t1) / 2
        m.add(STONE, lambda bm, cx=cx, cy=cy: cuboid(bm, (cx, cy, z - 1.0), (L / n + 0.05, width, 2.0), rot))
        for side in (-1, 1):
            m.add(CARVED, lambda bm, cx=cx, cy=cy, side=side: cuboid(bm, (cx - dy * side * width / 2, cy + dx * side * width / 2, z + 0.6), (L / n + 0.05, 0.8, 1.2), rot))
    # Arches between piers dropping into the mist.
    piers = max(2, int(L / 40))
    for k in range(piers + 1):
        px, py = x0 + (x1 - x0) * k / piers, y0 + (y1 - y0) * k / piers
        m.add(STONE, lambda bm, px=px, py=py: cuboid(bm, (px, py, (z - 2 + ar.ABYSS + 40) / 2), (6.0, width - 1, z - 2 - ar.ABYSS - 40), rot))
    for k in range(piers):
        a = k / piers
        b = (k + 1) / piers

        def arc(bm, a=a, b=b):
            rings_ = []
            for j in range(11):
                t = a + (b - a) * j / 10
                px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                drop = (1 - math.sin(math.pi * j / 10)) * (L / piers) * 0.42
                zz = z - 2.0 - drop
                rings_.append([bm.verts.new((px - dy * o, py + dx * o, zz + dz)) for o, dz in ((-width / 2 + 0.5, 0), (width / 2 - 0.5, 0), (width / 2 - 0.5, 1.4), (-width / 2 + 0.5, 1.4))])
            loft(bm, rings_, cap_top=False)

        m.add(STONE, arc)
    m.build(c, name, "Cathedral", "visual")
    for k in range(int(L / 14) + 1):
        t = min(1.0, k * 14 / L)
        px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        for side in (-1, 1):
            lx, ly = px - dy * side * (width / 2 - 0.2), py + dx * side * (width / 2 - 0.2)
            sc.put(ap.lantern_post(c), lx, ly, z, rot=rot, coll="Cathedral")
            sc.warm.append((lx, ly, z + 2.4))


def multilevel(c, sc, ar, info):
    """Roads at other heights in the Cathedral: a high bridge across it and a low ledge
    path along its south wall, both lit by lanterns (scenery only)."""
    ring, centre = info["cathedral"]

    def wall_hits(x):
        ys = []
        n = len(ring)
        for k in range(n):
            (ax, ay), (bx, by) = ring[k], ring[(k + 1) % n]
            if (ax - x) * (bx - x) <= 0 and ax != bx:
                ys.append(ay + (by - ay) * (x - ax) / (bx - ax))
        return min(ys), max(ys)

    for x, dz, width, name in sc.p["deco_spans"]:
        lo, hi = wall_hits(x)
        half = 8.0 if width >= 9.0 else 6.0
        deco_span(c, sc, ar, ring, x - half, lo - 6, x + half, hi + 6, ar.Z_CATH + dz, width=width, name=name)
