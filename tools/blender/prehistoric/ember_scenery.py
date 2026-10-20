# Ember Peak's scenery (see ember_peak.py): the volcano's core with the Infernal
# Caverns cut through it, the lava, the obsidian, the distant volcanoes, the burning
# forest and the light. Built from the volcanic kit in volcano_props.py.
# SPDX-License-Identifier: MIT

import math

import course_kit as kit
import props
from course_kit import Vector, bmesh, lerp, rnd

CLIFF = ("obsidian_cliff", "wall")
CAVE = ("cave_rock", "wall")
LAVA = ("volcano_lava", "lava")


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


# ------------------------------------------------------------------ the caverns


def tunnel_prof(half, h, depth=0.5):
    return [(-half, -depth), (half, -depth), (half, 0.6 * h), (0.62 * half, h), (-0.62 * half, h), (-half, 0.6 * h)]


def chamber_prof(half, h, depth=0.5):
    return [(-half, -depth), (half, -depth), (half * 1.04, 0.42 * h), (0.82 * half, 0.8 * h), (0.38 * half, h),
            (-0.38 * half, h), (-0.82 * half, 0.8 * h), (-half * 1.04, 0.42 * h)]


def cut(c, rock, s0, s1, prof, pad=0.0, step=2.0, wobble=0.0):
    """Cut a space along the route from s0 to s1 out of `rock`, with the cross-section
    `prof` [(across, up)] (an anticlockwise polygon, relative to the road). `wobble`
    makes the walls rougher, like a cave's."""
    bm = bmesh.new()
    rings = []
    n = max(3, math.ceil((s1 - s0 + 2 * pad) / step))
    for k in range(n + 1):
        s = s0 - pad + (s1 - s0 + 2 * pad) * k / n
        q = c.at(s)
        ring = []
        for j, (o, z) in enumerate(prof):
            w = 1.0 + wobble * (math.sin(s * 0.21 + j * 1.9) * 0.6 + math.sin(s * 0.07 + j) * 0.4) if 0 < j else 1.0
            ring.append(bm.verts.new(q.p + q.r * (o * w) + Vector((0, 0, z * (w if z > 0 else 1.0)))))
        rings.append(ring)
    m = len(prof)
    for lo, hi in zip(rings, rings[1:]):
        for j in range(m):
            bm.faces.new((lo[j], lo[(j + 1) % m], hi[(j + 1) % m], hi[j]))
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cutter = c.mesh_object("Cave Cutter", bm, "Rocks", "visual")
    mod = rock.modifiers.new("Cave", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
    mod.object = cutter
    import bpy

    bpy.context.view_layer.objects.active = rock
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter)


def cave_plan(ep, c0, c1, lake):
    """The caverns, along the lap: (name, from, to, profile, pad, wobble)."""
    L = c1 - c0
    at = lambda f: c0 + L * f  # noqa: E731
    return [
        ("corridor", c0, c1, tunnel_prof(11.5, 13.0), 20.0, 0.12),
        ("entry hall", at(0.04), at(0.16), chamber_prof(24.0, 26.0), 0.0, 0.15),
        ("lava lake", lake[0] - 18, lake[1] + 14, chamber_prof(44.0, 38.0, 16.0), 0.0, 0.12),
        ("crystal gallery", at(0.6), at(0.72), chamber_prof(21.0, 20.0), 0.0, 0.18),
        ("magma falls hall", at(0.78), at(0.92), chamber_prof(30.0, 30.0, 4.0), 0.0, 0.14),
    ]


def volcano_core(c, ep, lake):
    """The heart of the volcano (inside CORE_R): one solid of rings following the
    mountain's slopes, ridges and crater, with the caverns cut through it. (Outside it
    the slopes are the terrain, which reaches in over its rim to hide the join.)"""
    n = 96
    radii = []
    r = ep.CORE_R
    while r > ep.CRATER_R + 14:
        radii.append(r)
        r -= 7.0
    radii += [ep.CRATER_R + 12, ep.CRATER_R + 8, ep.CRATER_R + 4, ep.CRATER_R, ep.CRATER_R - 8, ep.CRATER_R - 18]
    bm = bmesh.new()

    def ring(r, z_of):
        return [bm.verts.new((r * math.cos(k * math.tau / n), r * math.sin(k * math.tau / n), z_of(r, k))) for k in range(n)]

    def surf(r, k):
        a = k * math.tau / n
        x, y = r * math.cos(a), r * math.sin(a)
        h = ep.land(x, y)
        return h - (0.8 if r >= ep.CORE_R - 1 else 0.0)

    rings = [ring(ep.CORE_R, lambda r, k: -30.0)]
    for r in radii:
        rings.append(ring(r, surf))
    m = n
    for lo, hi in zip(rings, rings[1:]):
        for j in range(m):
            bm.faces.new((lo[j], lo[(j + 1) % m], hi[(j + 1) % m], hi[j]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    rock = c.mesh_object("Volcano Core", bm, "Volcano")
    c0, c1 = ep.CAVE_S
    for name, s0, s1, prof, pad, wob in cave_plan(ep, c0, c1, lake):
        cut(c, rock, s0, s1, prof, pad=pad, wobble=wob)
    paint_core(c, rock, ep, lake)
    return rock


def in_caves(c, ep, w, slack=0.0):
    """Is the world point w inside the caverns (or on their walls)?"""
    if math.hypot(w.x, w.y) > ep.CORE_R + 4:
        return False
    smp, d = c.nearest(w.x, w.y)
    if not (ep.CAVE_S[0] - 10 <= smp.s <= ep.CAVE_S[1] + 10):
        return False
    return d < 50 + slack and w.z < smp.p.z + 42


def paint_core(c, rock, ep, lake):
    g = {k: [] for k in ("cliff", "soil", "magma", "wall", "floor", "lava")}
    for p in rock.data.polygons:
        w = p.center
        r = math.hypot(w.x, w.y)
        if in_caves(c, ep, w):
            smp, _ = c.nearest(w.x, w.y)
            if p.normal.z > 0.7:
                g["lava" if w.z < smp.p.z - 5 else "floor"].append(p.index)
            else:
                g["wall"].append(p.index)
        elif r < ep.CRATER_R + 6:
            g["magma"].append(p.index)
        elif p.normal.z < 0.8 or (int(w.z / 14) + int(math.atan2(w.y, w.x) * 6)) % 3 == 0:
            g["cliff"].append(p.index)
        else:
            g["soil"].append(p.index)
    c.assign(rock, c.lib(*CLIFF), g["cliff"])
    c.assign(rock, c.lib("ash_soil", "sand"), g["soil"])
    c.assign(rock, c.lib("magma_rock", "wall"), g["magma"])
    c.assign(rock, c.lib(*CAVE), g["wall"])
    c.assign(rock, c.lib("cave_rock", "dirt"), g["floor"])
    c.assign(rock, c.lib(*LAVA), g["lava"])
    rock.data.shade_flat()


# ------------------------------------------------------------------ lava


def lava(c, ep):
    """The lava rivers down their ravines, the pools in the obsidian fields and the
    crater's lake. These are the surfaces that burn."""
    obs = []
    mat = c.lib(*LAVA)
    for k, (th, r0, r1, hw, depth) in enumerate(ep.RIVERS):
        path = []
        r = r0
        while r <= r1:
            x, y = ep.river_centre(k, r)
            z = ep.natural(x, y) + 1.0
            smp, d = c.nearest(x, y)
            if d < smp.w / 2 + 16:
                z = min(z, smp.p.z - 3.5)  # always well under a bridge
            path.append((x, y, 2 * hw + 2, z))
            r += 5.0
        obs.append(c.ribbon("Lava River %d" % (k + 1), path, 2 * hw, 0, mat, coll="Lava", steps=4))
    for k, (px, py, pr) in enumerate(ep.POOLS):
        obs.append(c.disc("Lava Pool %d" % (k + 1), px, py, pr + 2, -1.2, mat, coll="Lava", n=20, wobble=0.15, seed=k))
    obs.append(c.disc("Crater Lake", 0, 0, ep.CRATER_R - 2, ep.CRATER_LAVA_Z, mat, coll="Lava", role="visual", n=32, wobble=0.06))
    return obs


# ------------------------------------------------------------------ the mountain


def flank_streams(c, ep):
    """Lava pouring from the crater down the upper flanks (glowing, out of reach)."""
    mat = c.lib("lava_falls", "lava")
    for k, th in enumerate((-42.0, 15.0, 40.0, 60.0, 85.0, 105.0, 130.0, 200.0, 236.0, 275.0)):
        path = []
        r = ep.CRATER_R + 10
        end = 200.0 if th in (15.0, 200.0) else 250.0 if th == 236.0 else 215.0 if th == -42.0 else 150.0 + 40.0 * (k % 3)
        while r <= end:
            t = math.radians(th) + 0.08 * math.sin(r / 19 + k)
            x, y = r * math.cos(t), r * math.sin(t)
            w = 7.0 + 6.0 * (r - ep.CRATER_R) / 200
            path.append((x, y, w, ep.land(x, y) + 0.7))
            r += 6.0
        c.ribbon("Flank Lava %d" % (k + 1), path, 8, 0, mat, coll="Lava", role="visual", steps=2)


def crater(c, ep, vp):
    """The crater: the glowing pit, fountains of fire and an enormous plume of smoke
    and ash leaning away on the wind."""
    m = Mesh()
    for k in range(7):
        a = k * 0.9
        r = 10.0 + 14.0 * rnd(k * 3)
        base = (r * math.cos(a), r * math.sin(a), ep.CRATER_LAVA_Z)
        h = 45.0 + 45.0 * rnd(k * 7)
        top = (base[0] * 1.3, base[1] * 1.3, base[2] + h)
        m.add(("fire_glow", "wall"), lambda bm, base=base, top=top, k=k: vp.prism(bm, base, top, 4.5, 2.0, n=5, phase=k, tip=(top[0] * 1.1, top[1] * 1.1, top[2] + 8)))
    m.build(c, "Eruption Fountains", "Eruption", role="visual")
    plume = vp.smoke_plume(c, 0, 90.0)
    for k, (dx, dy, sc) in enumerate(((0, 0, 5.0), (25, 18, 3.8), (-28, 12, 3.2), (5, -24, 2.8))):
        c.place(plume, dx, dy, ep.RIM_Z - 20, rot=0.6 + k * 0.4, scale=sc, coll="Eruption", role="visual")


def far_volcanoes(c, vp):
    """Volcanoes smoking all round the horizon."""
    plume = vp.smoke_plume(c, 1, 70.0)
    for k, (bearing, dist, sc) in enumerate(((35, 900, 1.1), (95, 1050, 1.4), (150, 860, 0.9), (205, 1150, 1.5), (300, 980, 1.2), (345, 1100, 1.0), (250, 1250, 1.3))):
        t = math.radians(bearing)
        x, y = dist * math.cos(t), dist * math.sin(t)
        c.place(vp.far_volcano(c, k % 3), x, y, 0, rot=k * 1.3, scale=sc, coll="Horizon", role="visual")
        c.place(plume, x, y, 200 * sc - 8, rot=0.6, scale=2.2 * sc, coll="Horizon", role="visual")


def dragon_cliffs(c, ep, vp):
    """The dragon's crag: a towering pinnacle of black rock and obsidian blades east of
    its bridge, with a ledge near the top where it perches."""
    q = c.at(kit.s_near(c, *ep.WAYPOINTS[9][:2]))
    p = q.side(64.0)
    rot = math.atan2(-q.r.y, -q.r.x)
    c.place(vp.crag(c, 0), p.x, p.y, -4.0, rot=rot, coll="Crag", role="both")
    ledge = p + Vector((math.cos(rot), math.sin(rot), 0)) * -6.0
    return (ledge.x, ledge.y, 50.0)


# ------------------------------------------------------------------ dressing


def lava_falls(c, name, x, y, top, foot, w, facing_angle):
    """A falls of molten rock (props.falls with the lava materials), thrown out toward
    `facing_angle` (radians, 0 = +X)."""
    ang = facing_angle + math.pi / 2  # props.falls throws toward -Y; turn that
    return props.falls(c, name, x, y, top, foot, w * 0.7, w, facing=-1, throw=3.0, bulge=1.0, veils=2, angle=ang, foam_r=w * 0.6,
                       mats=("lava_falls", "fire_glow", "volcano_lava"))


def obsidian(c, ep, vp, ter):
    """Obsidian everywhere: a forest of spires, clusters and leaning slabs in the
    Obsidian Fields, more round the mountain, arches over the road, and two huge spires
    guarding the mouth."""
    spires = [vp.obsidian_spire(c, v) for v in range(3)]
    clusters = [vp.obsidian_cluster(c, v) for v in range(3)]
    slabs = [vp.leaning_slab(c, v) for v in range(2)]

    def ok(m0, m1, area=None):
        def f(x, y, z):
            if math.hypot(x, y) < ep.CORE_R + 10 or ep.lava_under(x, y):
                return False
            smp, d = c.nearest(x, y)
            return smp.w / 2 + m0 < d < smp.w / 2 + m1
        return f

    fields = (40, 360, -470, -220)
    for v, sp_ in enumerate(spires):
        props.scatter(c, sp_, 14, fields, ok(10, 80), ter, seed=700 + v, scale=(0.8, 1.5), coll="Obsidian", role="both", sink=0.5)
        props.scatter(c, sp_, 10, (-520, 520, -520, 520), ok(14, 140), ter, seed=710 + v, scale=(1.0, 2.0), coll="Obsidian", role="both", sink=0.5)
    for v, cl in enumerate(clusters):
        props.scatter(c, cl, 14, fields, ok(6, 60), ter, seed=720 + v, scale=(0.9, 1.6), coll="Obsidian", role="both", sink=0.3)
        props.scatter(c, cl, 12, (-520, 520, -520, 520), ok(6, 90), ter, seed=730 + v, scale=(0.9, 1.6), coll="Obsidian", role="both", sink=0.3)
    # Slabs leaning out over the road in the fields.
    for k, s in enumerate(range(int(kit.s_near(c, *ep.WAYPOINTS[3][:2])), int(kit.s_near(c, *ep.WAYPOINTS[7][:2])), 70)):
        q = c.at(s)
        sd = 1 if k % 2 else -1
        p = q.side(sd * (q.w / 2 + 10))
        z = c.ground_z(p.x, p.y, ter) or q.p.z
        rot = math.atan2(-sd * q.r.y, -sd * q.r.x)
        c.place(slabs[k % 2], p.x, p.y, z - 1.0, rot=rot, coll="Obsidian", role="visual")
    # Arches over the road: entering the fields, and on the final descent.
    for wp in (3, 41):
        q = c.at(kit.s_near(c, *ep.WAYPOINTS[wp][:2]) + 10)
        z = q.p.z
        c.place(vp.obsidian_arch(c, 30.0, 0), q.p.x, q.p.y, z - 1.0, rot=math.atan2(q.r.y, q.r.x), coll="Obsidian", role="visual")


def mouth(c, ep, vp, lights, ter):
    """The Mouth of the Volcano: a towering gateway of basalt round the cavern's opening,
    two great obsidian spires, a rune band glowing over the door, lava pouring down either
    side, and the furnace light inside."""
    s = ep.CAVE_S[0] - 2
    q = c.at(s)
    rot = math.atan2(q.r.y, q.r.x)
    m = Mesh()
    half, top = 11.5, q.p.z + 13.0
    for sd in (-1, 1):
        p = q.side(sd * (half + 5.0))
        m.box(("basalt_block", "wall"), (p.x, p.y, (q.p.z + top + 22) / 2 - 2), (10.0, 8.0, top + 26 - q.p.z), rot)
        p2 = q.side(sd * (half + 1.2))
        m.box(("basalt_carved", "wall"), (p2.x, p2.y, (q.p.z + top) / 2), (2.4, 9.0, top - q.p.z + 0.5), rot)
    m.box(("basalt_block", "wall"), (q.p.x, q.p.y, top + 6.0), (2 * half + 4, 9.0, 12.0), rot)
    m.box(("basalt_carved", "wall"), (q.p.x - q.t.x * 4.6, q.p.y - q.t.y * 4.6, top + 3.0), (2 * half + 2, 0.6, 3.0), rot)
    for k, (w, h) in enumerate(((2 * half + 18, 4.0), (2 * half + 10, 4.0), (2 * half, 5.0))):
        m.box(("basalt_block" if k != 1 else "basalt_carved", "wall"), (q.p.x, q.p.y, top + 12 + 4 * k + h / 2), (w, 8.0 - k, h), rot)
    m.build(c, "Volcano Mouth", "Mouth", role="both")
    sp_ = vp.obsidian_spire(c, 2)
    for sd in (-1, 1):
        p = q.side(sd * (half + 18.0))
        z = c.ground_z(p.x, p.y, ter) or q.p.z
        c.place(sp_, p.x, p.y, z - 2.0, rot=rot + sd, scale=1.6, coll="Mouth", role="both")
        f = q.side(sd * (half + 10.0), 0) - q.t * 6.0
        lava_falls(c, "Mouth Falls %d" % ((sd + 3) // 2), f.x, f.y, top + 18.0, q.p.z - 0.5, 7.0, math.atan2(-q.t.y, -q.t.x))
        lights.append(tuple(q.side(sd * (half + 3.0), 4.0) - q.t * 4.0))


def bridges(c, ep, ter):
    """Arched basalt piers under every bridge: thick piers on the deep ravines, with
    arches between them."""
    m = Mesh()
    for piece in c.pieces:
        if not ("bridge" in piece.name):
            continue
        s0, s1 = piece["kp_from"], piece["kp_to"]
        if s1 < s0:
            s1 += c.length
        if ep.CAVE_S[0] - 5 <= s0 <= ep.CAVE_S[1] + 5:
            continue
        n = max(1, int((s1 - s0) / 18.0))
        tops = []
        for k in range(n + 1):
            s = s0 + (s1 - s0) * k / n
            q = c.at(s)
            g = c.ground_z(q.p.x, q.p.y, ter)
            bot = (g if g is not None else q.p.z - 30) - 2.0
            deck = q.p.z - 4.0
            rot = math.atan2(q.t.y, q.t.x)
            if 0 < k < n and deck - bot > 2:
                m.box(("basalt_block", "wall"), (q.p.x, q.p.y, (bot + deck) / 2), (5.0, q.w + 3.0, deck - bot), rot)
                m.box(("basalt_carved", "wall"), (q.p.x, q.p.y, deck - 1.0), (5.6, q.w + 3.6, 2.0), rot)
            tops.append((q, deck))
        for (qa, da), (qb, db) in zip(tops, tops[1:]):
            for sd in (-1, 1):
                pts = []
                for j in range(7):
                    u = j / 6
                    p = qa.p.lerp(qb.p, u) + qa.r * (sd * (qa.w / 2 + 1.0))
                    z = lerp(da, db, u) - 6.0 * math.sin(u * math.pi)
                    pts.append((p.x, p.y, z))
                m.tube(("basalt_block", "wall"), pts, 1.0, n=4)
    m.build(c, "Bridge Piers", "Bridges", role="visual")


def cave_dressing(c, ep, vp, lake, lights, lava_lights, purple):
    """Inside the mountain: stalactites, obsidian columns, fire and amethyst crystals,
    torches, piers under the lake bridge, lava falls into the lake and the magma hall,
    and lava channels glowing along the entry hall."""
    c0, c1 = ep.CAVE_S
    L = c1 - c0
    stal = [vp.stalactite(c, v) for v in range(3)]
    reds = [vp.crystals(c, "crystal_red", v) for v in range(2)]
    purp = [vp.crystals(c, "crystal_purple", v) for v in range(2)]
    br = vp.brazier(c)
    plan = {name: (s0, s1, prof) for name, s0, s1, prof, pad, wob in cave_plan(ep, c0, c1, lake)}

    def roof(s):
        h = 13.0
        for name, (s0, s1, prof) in plan.items():
            if name != "corridor" and s0 <= s <= s1:
                h = max(h, max(z for _, z in prof))
        return h

    def width(s):
        w = 11.5
        for name, (s0, s1, prof) in plan.items():
            if name != "corridor" and s0 <= s <= s1:
                w = max(w, max(o for o, _ in prof))
        return w

    # Stalactites all through, hung from the roof.
    k = 0
    s = c0 + 6
    while s < c1 - 4:
        q = c.at(s)
        h, w = roof(s), width(s)
        off = (rnd(k * 3.1) - 0.5) * 1.5 * w
        top = h * (1 - 0.35 * (abs(off) / w) ** 2) - 1.0
        p = q.side(off, top)
        c.place(stal[k % 3], p.x, p.y, p.z, rot=k * 1.7, scale=0.8 + 0.6 * rnd(k) + (0.5 if h > 20 else 0), coll="Caverns", role="visual")
        s += 7.0 + 6.0 * rnd(k * 5.3)
        k += 1
    # Braziers along the road (the torchlight, and the way through).
    k = 0
    s = c0 + 4
    while s < c1:
        q = c.at(s)
        if not (lake[0] - 2 < s < lake[1] + 2):
            sd = 1 if k % 2 else -1
            p = q.side(sd * (q.w / 2 + 3.0))
            c.place(br, p.x, p.y, p.z - 0.3, rot=k, coll="Caverns", role="visual")
            lights.append((p.x, p.y, p.z + 3.0))
        s += 20.0
        k += 1
    # The entry hall: lava channels down both sides, fire crystals.
    e0, e1 = plan["entry hall"][:2]
    for sd in (-1, 1):
        path = []
        s = e0 + 2
        while s <= e1 - 2:
            q = c.at(s)
            p = q.side(sd * 17.5, -0.35)
            path.append((p.x, p.y, 6.0, p.z))
            lava_lights.append(tuple(p + Vector((0, 0, 1.0))))
            s += 4.0
        c.ribbon("Hall Lava %d" % ((sd + 3) // 2), path, 6, 0, c.lib(*LAVA), coll="Lava", role="both")
    for j in range(6):
        q = c.at(e0 + (e1 - e0) * (j + 0.5) / 6)
        sd = 1 if j % 2 else -1
        p = q.side(sd * 22.0, -0.3)
        c.place(reds[j % 2], p.x, p.y, p.z, rot=j, scale=0.9, coll="Caverns", role="visual")
    # The lava lake: columns rising out of it, falls pouring into it, piers under the
    # bridge, and red crystals on the walls.
    l0, l1 = lake
    col = vp.cave_column(c, 40.0)
    for j, (f, o) in enumerate(((0.15, -30), (0.4, 32), (0.65, -34), (0.9, 30))):
        q = c.at(l0 + (l1 - l0) * f)
        p = q.side(o, -16.0)
        c.place(col, p.x, p.y, p.z, rot=j, coll="Caverns", role="visual")
    for j, (f, sd) in enumerate(((0.25, 1), (0.55, -1), (0.85, 1))):
        q = c.at(l0 + (l1 - l0) * f)
        p = q.side(sd * 42.0)
        lava_falls(c, "Lake Falls %d" % (j + 1), p.x, p.y, q.p.z + 24.0, q.p.z - 14.5, 8.0, math.atan2(-sd * q.r.y, -sd * q.r.x))
    for j in range(10):
        q = c.at(l0 - 10 + (l1 - l0 + 20) * j / 9)
        lava_lights.append(tuple(q.side((rnd(j) - 0.5) * 60, -12.0)))
    for j in range(5):
        q = c.at(l0 + (l1 - l0) * (j + 0.5) / 5)
        sd = 1 if j % 2 else -1
        p = q.side(sd * 40.0, 4.0)
        c.place(reds[j % 2], p.x, p.y, p.z, rot=j * 1.3, scale=1.2, coll="Caverns", role="visual")
    # The crystal gallery: amethyst everywhere, glowing violet.
    g0, g1 = plan["crystal gallery"][:2]
    k = 0
    s = g0 - 6
    while s < g1 + 6:
        q = c.at(s)
        for sd in (-1, 1):
            o = sd * (14.0 + 5.0 * rnd(k * 3 + sd))
            p = q.side(o, -0.3)
            c.place(purp[k % 2], p.x, p.y, p.z, rot=k + sd, scale=0.7 + 0.5 * rnd(k * 5 + sd), coll="Caverns", role="visual")
            purple.append(tuple(q.side(o * 0.9, 3.0)))
            if k % 3 == 0:
                t = q.side(o * 0.8, 17.0)
                c.place(purp[(k + 1) % 2], t.x, t.y, t.z, rot=k, scale=(0.8, 0.8, -0.8), coll="Caverns", role="visual")
        s += 8.0
        k += 1
    # The magma falls hall: falls down both walls into lava pools beside the road.
    h0, h1 = plan["magma falls hall"][:2]
    for j, (f, sd) in enumerate(((0.25, -1), (0.5, 1), (0.75, -1))):
        q = c.at(h0 + (h1 - h0) * f)
        p = q.side(sd * 29.0)
        lava_falls(c, "Hall Falls %d" % (j + 1), p.x, p.y, q.p.z + 22.0, q.p.z - 3.5, 9.0, math.atan2(-sd * q.r.y, -sd * q.r.x))
        pool = q.side(sd * 23.0)
        c.disc("Hall Pool %d" % (j + 1), pool.x, pool.y, 7.0, q.p.z - 3.0, c.lib(*LAVA), coll="Lava", n=14, wobble=0.2, seed=j)
        lava_lights.append((pool.x, pool.y, q.p.z))
    q = c.at((h0 + h1) / 2)
    for sd in (-1, 1):
        p = q.side(sd * 20.0, -3.5)
        c.place(col, p.x, p.y, p.z, rot=sd, scale=(1.0, 1.0, 0.85), coll="Caverns", role="visual")


def forest(c, ep, vp, ter, fires):
    """The burning forest: charred and burning pines and dead palms across the plain
    round the mountain (thickest by the start and the final descent), with columns of
    smoke rising from the fires."""
    pines = [vp.burnt_pine(c, v, False) for v in range(2)]
    burning = [vp.burnt_pine(c, v, True) for v in range(2)]
    palm = vp.burnt_palm(c, 0)

    def ok(m0, m1):
        def f(x, y, z):
            r = math.hypot(x, y)
            if r < 300 or r > 520 or ep.lava_under(x, y) or z > 25:
                return False
            smp, d = c.nearest(x, y)
            return smp.w / 2 + m0 < d < smp.w / 2 + m1
        return f

    area = (-540, 540, -540, 540)
    for v, t in enumerate(pines):
        props.scatter(c, t, 70, area, ok(8, 160), ter, seed=800 + v, scale=(0.9, 1.5), coll="Forest", role="visual", sink=0.3)
    placed = []
    for v, t in enumerate(burning):
        placed += props.scatter(c, t, 34, area, ok(10, 160), ter, seed=810 + v, scale=(1.0, 1.5), coll="Forest", role="visual", sink=0.3)
    # Close to the start and the final descent: a burning grove either side.
    s_end = kit.s_near(c, *ep.WAYPOINTS[40][:2])
    k = 0
    for s in list(range(15, 230, 22)) + list(range(int(s_end), int(c.length) - 10, 22)):
        q = c.at(s)
        for sd in (-1, 1):
            k += 1
            p = q.side(sd * (q.w / 2 + 9 + 16 * rnd(k * 1.3)))
            if ep.lava_under(p.x, p.y):
                continue
            z = c.ground_z(p.x, p.y, ter)
            if z is None:
                continue
            t = burning[k % 2] if rnd(k * 2.7) < 0.55 else pines[k % 2]
            c.place(t, p.x, p.y, z - 0.3, rot=rnd(k) * math.tau, scale=0.9 + 0.5 * rnd(k * 3.1), coll="Forest", role="visual")
            if t in burning and k % 3 == 0:
                placed.append((p.x, p.y))
    props.scatter(c, palm, 30, area, ok(8, 120), ter, seed=820, scale=(1.0, 1.4), coll="Forest", role="visual", sink=0.3)
    plume = vp.smoke_plume(c, 2, 50.0)
    for k, (x, y) in enumerate(placed[::4]):
        z = c.ground_z(x, y, ter) or 0.0
        c.place(plume, x, y, z + 14, rot=0.6, scale=0.8 + 0.5 * rnd(k), coll="Smoke", role="visual")
    for x, y in placed[1::3][:12]:
        z = c.ground_z(x, y, ter) or 0.0
        fires.append((x, y, z + 16.0))


def ruins(c, ep, vp, ter, lights):
    """Ancient basalt pillars and braziers along the old roads: by the bridges, up the
    cliff roads and on the final descent."""
    pil = [vp.ruin_pillar(c, v) for v in range(2)]
    br = vp.brazier(c)
    k = 0
    s = 30.0
    while s < c.length:
        if ep.CAVE_S[0] - 20 <= s <= ep.CAVE_S[1] + 20:
            s += 40
            continue
        q = c.at(s)
        sd = 1 if k % 2 else -1
        p = q.side(sd * (q.w / 2 + 4.0))
        z = c.ground_z(p.x, p.y, ter)
        if z is not None and abs(z - q.p.z) < 2.5:
            if k % 3 == 0:
                c.place(pil[k % 2], p.x, p.y, z - 0.3, rot=math.atan2(q.t.y, q.t.x), coll="Ruins", role="both")
            else:
                c.place(br, p.x, p.y, z - 0.2, rot=k, coll="Ruins", role="both")
                lights.append((p.x, p.y, z + 3.0))
        s += 48.0 + 20 * rnd(k)
        k += 1


def ravine_falls(c, ep):
    """Lava falls down the walls of the ravine under the Dragon's Crossing, and where the
    east-flank river drops between the two cliff roads."""
    out = []
    for j, (r, sd) in enumerate(((270, 1), (300, -1), (380, 1), (410, -1))):
        k = 0
        th = ep.RIVERS[0][0]
        x, y = ep.river_centre(0, r)
        t = math.radians(th + 90)
        n = (math.cos(t) * sd, math.sin(t) * sd)
        wx, wy = x + n[0] * (ep.RIVERS[0][3] + 6), y + n[1] * (ep.RIVERS[0][3] + 6)
        top = ep.land(wx, wy) - 0.5
        bed = ep.natural(x, y) + 1.0
        lava_falls(c, "Ravine Falls %d" % (j + 1), wx, wy, top, bed, 9.0, math.atan2(-n[1], -n[0]))
        out.append((wx, wy, top))
    # The east-flank river tumbling down its gorge between the cliff roads.
    x, y = ep.river_centre(1, 262)
    a = math.radians(ep.RIVERS[1][0])
    top = ep.natural(x - 9 * math.cos(a), y - 9 * math.sin(a)) + 1.0
    lava_falls(c, "Gorge Falls", x - 9 * math.cos(a), y - 9 * math.sin(a), top + 6, ep.natural(x, y) - 2, 12.0, a)
    return out


# ------------------------------------------------------------------ build


def build(c, core, lava_obs, ep):
    import volcano_props as vp

    ter = list(c.coll("Terrain").objects)
    lights, lava_lights, purple, fires = [], [], [], []
    flank_streams(c, ep)
    crater(c, ep, vp)
    far_volcanoes(c, vp)
    perch = dragon_cliffs(c, ep, vp)
    lake = ep.LAKE_S
    mouth(c, ep, vp, lights, ter)
    bridges(c, ep, ter)
    cave_dressing(c, ep, vp, lake, lights, lava_lights, purple)
    obsidian(c, ep, vp, ter)
    forest(c, ep, vp, ter, fires)
    ruins(c, ep, vp, ter, lights)
    rf = ravine_falls(c, ep)
    for k, (th, r0, r1, hw, depth) in enumerate(ep.RIVERS):
        r = r0
        while r < r1:
            x, y = ep.river_centre(k, r)
            lava_lights.append((x, y, ep.natural(x, y) + 3.0))
            r += 14.0
    for px, py, pr in ep.POOLS:
        lava_lights.append((px, py, 1.0))

    # Light: lava glow on the rock round every river, pool and fall; dark caverns lit by
    # their lava, braziers and (in the gallery) violet crystals; firelight round every
    # brazier outside.
    def caves(w):
        return in_caves(c, ep, w)

    c.preset("sun", ter + [core], 0.35)
    c.preset("bottoms", ter, 0.35)
    c.glow([core], lava_lights + lights, 22.0, (1.5, 0.75, 0.4), base=(0.32, 0.22, 0.24), region=caves)
    c.glow([core], purple, 16.0, (0.9, 0.55, 1.4), base=1.0, region=caves)
    c.glow(ter + [core], lava_lights, 30.0, (1.55, 0.85, 0.5), base=1.0, region=lambda w: not caves(w))
    for x, y, z in lights:
        gx, gy, gz = c.game(x, y, z)
        c.entity("torch", x=gx, y=gy, z=gz)
    for x, y, z in fires:
        gx, gy, gz = c.game(x, y, z)
        c.entity("campfire", x=gx, y=gy, z=gz)
    # The dragon on its crag, breathing fire across the middle of its bridge on a fixed
    # schedule (game/dragon.ts): every 9 s, 1.8 s of warning, 2 s of fire.
    sb = kit.s_near(c, *ep.WAYPOINTS[9][:2])
    q = c.at(sb)
    px, py, pz = perch
    gx, gy, gz = c.game(px, py, pz)
    fx, fy, fz = c.game(q.p.x, q.p.y, q.p.z)
    c.entity(
        "dragon",
        x=gx, y=gy, z=gz,
        heading=round(math.atan2(q.p.x - px, -(q.p.y - py)), 3),
        scale=1.8,
        fire={"x": fx, "y": fy, "z": fz, "heading": round(math.atan2(q.t.x, -q.t.y), 3), "length": 16.0, "width": round(q.w + 5.0, 1), "height": 6.0},
        period=9.0, offset=3.0, aim=1.2, warn=1.8, breathe=2.0, cool=1.0,
    )

    # The eruption (on a 12 s beat of the race clock), ash and embers in the air, and
    # steam venting from fissures up the ascent and in the caverns.
    gx, gy, gz = c.game(0.0, 0.0, ep.CRATER_LAVA_Z)
    c.entity("eruption", x=gx, y=gy, z=gz, period=12.0, offset=2.0)
    c.entity("ashfall", rate=60, radius=40)
    for k, wp in enumerate((12, 13, 19, 20, 21)):
        q = c.at(kit.s_near(c, *ep.WAYPOINTS[wp][:2]) + 8)
        p = q.side((1 if k % 2 else -1) * (q.w / 2 + 3.5))
        z = c.ground_z(p.x, p.y, ter) or q.p.z
        gx, gy, gz = c.game(p.x, p.y, z)
        c.entity("steam", x=gx, y=gy, z=gz)
    c0, c1 = ep.CAVE_S
    for k in range(6):
        q = c.at(c0 + (c1 - c0) * (0.1 + 0.15 * k))
        p = q.side((1 if k % 2 else -1) * (q.w / 2 + 4.0), -0.3)
        gx, gy, gz = c.game(p.x, p.y, p.z)
        c.entity("steam", x=gx, y=gy, z=gz)

    c.merge_props(("Obsidian", "Forest", "Caverns", "Ruins", "Smoke", "Mouth"))
