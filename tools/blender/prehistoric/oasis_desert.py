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


def house(c, variant=0, w=9.0, d=8.0, h=7.0):
    """A mud-brick house: plastered walls (darker at the foot), a parapet with stepped
    merlons, beam ends poking out under it, an arched door, small lit windows, and on
    some a little dome or an upper room. Faces -Y (its door), origin at its foot."""
    name = "Mud House %d %d %d" % (variant, int(w), int(h))

    def build(bm):
        out = []
        cuboid(bm, (0, 0, h / 2), (w, d, h))
        walls = _faces(bm, 0)
        k = len(bm.faces)
        cuboid(bm, (0, 0, 0.5), (w + 0.3, d + 0.3, 1.0))
        foot = _faces(bm, k)
        k = len(bm.faces)
        # The parapet's merlons, stepped at the corners.
        for i in range(int(w / 1.6)):
            x = -w / 2 + 0.6 + i * (w - 1.2) / max(1, int(w / 1.6) - 1)
            for y in (-d / 2 + 0.3, d / 2 - 0.3):
                cuboid(bm, (x, y, h + 0.45), (0.7, 0.5, 0.9 + 0.5 * ((i in (0, int(w / 1.6) - 1)))))
        for i in range(int(d / 1.6)):
            y = -d / 2 + 0.6 + i * (d - 1.2) / max(1, int(d / 1.6) - 1)
            for x in (-w / 2 + 0.3, w / 2 - 0.3):
                cuboid(bm, (x, y, h + 0.45), (0.5, 0.7, 0.9))
        if variant % 3 == 1:
            cuboid(bm, (w * 0.18, d * 0.1, h + 1.6), (w * 0.45, d * 0.5, 3.2))
        walls += _faces(bm, k)
        k = len(bm.faces)
        # Beam ends (vigas) under the parapet, front and back.
        for i in range(int(w / 1.3)):
            x = -w / 2 + 0.7 + i * 1.3
            for y in (-d / 2 - 0.35, d / 2 + 0.35):
                cuboid(bm, (x, y, h - 0.6), (0.28, 0.7, 0.28))
        wood = _faces(bm, k)
        k = len(bm.faces)
        # The door: a dark arch.
        door = [bm.verts.new(p) for p in ((-0.8, -d / 2 - 0.05, 0.0), (0.8, -d / 2 - 0.05, 0.0), (0.8, -d / 2 - 0.05, 2.2), (0.0, -d / 2 - 0.05, 2.9), (-0.8, -d / 2 - 0.05, 2.2))]
        bm.faces.new(list(reversed(door)))
        dark = _faces(bm, k)
        k = len(bm.faces)
        for i in range(2 if w > 7 else 1):
            x = (-w / 4, w / 4)[i] if w > 7 else w / 4
            for y, z in ((-d / 2 - 0.05, h * 0.62), (d / 2 + 0.05, h * 0.62)):
                win = [bm.verts.new(p) for p in ((x - 0.45, y, z - 0.6), (x + 0.45, y, z - 0.6), (x + 0.45, y, z + 0.3), (x, y, z + 0.75), (x - 0.45, y, z + 0.3))]
                bm.faces.new(win if y > 0 else list(reversed(win)))
        lit = _faces(bm, k)
        k = len(bm.faces)
        if variant % 3 == 2:
            op.dome(bm, -w * 0.2, 0.0, h, min(w, d) * 0.28, n=10, rings=4)
        domes = _faces(bm, k)
        out += [(c.lib("adobe"), walls), (c.lib("adobe_dark"), foot), (c.lib("weathered_timber"), wood), (c.lib("oasis_bark"), dark),
                (c.lib("lantern_glow"), lit)]
        if domes:
            out.append((c.lib("adobe"), domes))
        return out

    return c.proto(name, build) and name


def tent(c, variant=0, w=10.0, d=8.0):
    """A nomad tent: a broad low roof of woven cloth over three tall poles, its front
    open (its back and sides pegged down), a rug and cushions inside and lanterns hung
    from the front beam. Faces -Y (its open front), origin at its foot."""
    name = "Nomad Tent %d" % variant
    cloth = ("tent_cloth", "tent_cloth_red")[variant % 2]

    def build(bm):
        H, E = 4.2, 1.5  # the poles' height and the eaves'
        # The roof: peaks over three poles, sloping to the eaves all round.
        xs = (-w / 2, -w / 4, 0.0, w / 4, w / 2)
        zs = (E + 0.8, H, H - 0.7, H, E + 0.8)
        front = [bm.verts.new((x, -d / 2, E)) for x in xs]
        ridge = [bm.verts.new((x, 0.0, z)) for x, z in zip(xs, zs)]
        back = [bm.verts.new((x, d / 2, E - 0.2)) for x in xs]
        for i in range(4):
            bm.faces.new((front[i], front[i + 1], ridge[i + 1], ridge[i]))
            bm.faces.new((ridge[i], ridge[i + 1], back[i + 1], back[i]))
        # The back and sides, pegged down to the sand.
        foot_b = [bm.verts.new((x, d / 2 + 0.6, 0.0)) for x in xs]
        for i in range(4):
            bm.faces.new((back[i], back[i + 1], foot_b[i + 1], foot_b[i]))
        for side, i in ((-1, 0), (1, 4)):
            fl = bm.verts.new((side * (w / 2 + 0.5), -d / 2 + 0.5, 0.0))
            bl = foot_b[i]
            bm.faces.new((front[i], ridge[i], back[i], bl, fl) if side < 0 else (fl, bl, back[i], ridge[i], front[i]))
        roof = _faces(bm, 0)
        # Double-sided: the cloth seen from inside too.
        k = len(bm.faces)
        bm.faces.ensure_lookup_table()
        for f in [bm.faces[i] for i in roof]:
            bm.faces.new([bm.verts.new(v.co - f.normal * 0.05) for v in reversed(f.verts)])
        inner = _faces(bm, k)
        k = len(bm.faces)
        for x in (-w / 4, w / 4):
            tube(bm, [(x, 0.0, 0.0), (x, 0.0, H)], 0.12, n=5)
        for x in (-w / 2 + 0.3, 0.0, w / 2 - 0.3):
            tube(bm, [(x, -d / 2, 0.0), (x, -d / 2, E)], 0.1, n=4)
        tube(bm, [(-w / 2, -d / 2, E), (w / 2, -d / 2, E)], 0.08, n=4)
        poles = _faces(bm, k)
        k = len(bm.faces)
        cuboid(bm, (0, 0.3, 0.06), (w - 1.6, d - 1.4, 0.12))
        rug = _faces(bm, k)
        k = len(bm.faces)
        for i in range(5):
            blob(bm, (-w / 2 + 1.6 + i * (w - 3.2) / 4, d / 2 - 1.2, 0.35), 0.55, sx=1.4, sz=0.6, subdiv=0)
        cushions = _faces(bm, k)
        k = len(bm.faces)
        for x in (-w / 3, 0.0, w / 3):
            loft(bm, [ring(bm, (x, -d / 2 + 0.1), r, z, 5) for r, z in ((0.05, E - 0.3), (0.22, E - 0.55), (0.22, E - 0.95), (0.05, E - 1.15))], cap_top=True, cap_bottom=True)
        lamps = _faces(bm, k)
        return [(c.lib(cloth), roof + inner), (c.lib("weathered_timber"), poles), (c.lib("rug"), rug), (c.lib("awning_sun"), cushions),
                (c.lib("lantern_glow"), lamps)]

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
            c.place(house(c, (k + (side > 0)) % 3, 9.0, 8.0, h), p.x, p.y, q.p.z - 0.5, rot=rot, coll="Village", role="both")
            sc["lights"].append((p.x, p.y, q.p.z + h * 0.6))
        s += 16.0
        k += 1
    q = c.at(oh.LENGTH - 30)
    for side in (-1, 1):
        p = q.side(side * (q.w / 2 + 10.0))
        c.place(house(c, 1 + (side > 0), 10.0, 9.0, 8.0), p.x, p.y, q.p.z - 0.5, rot=road_rot(q) + (math.pi if side > 0 else 0.0), coll="Village", role="both")
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


def camp(c, oh, ter, sc):
    """The nomad camp along the weave: a tent where each of the greybox's stood, a
    lantern by each, rugs airing on lines and a campfire in the middle."""
    s = oh.SEG[10] + 8
    k = 0
    fire = None
    line = rug_line(c)
    while s < oh.SEG[16]:
        q = c.at(s)
        side = 1 if k % 2 else -1
        p = q.side(side * (q.w / 2 + 8.0))
        rot = road_rot(q) + (math.pi if side > 0 else 0.0)
        c.place(tent(c, k % 2), p.x, p.y, q.p.z - 0.05, rot=rot, coll="Camp", role="both")
        lp = q.side(side * (q.w / 2 + 2.2))
        sc["torches"].append((lp.x, lp.y, q.p.z + 3.2))
        sc["lanterns"].append((lp.x, lp.y, q.p.z + 3.2))
        if k % 2 == 0:
            b = q.side(side * (q.w / 2 + 17.0))
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
    for k in range(22):
        a = k * math.tau / 22
        r = oh.POOL[2] + 9.0 + 4.0 * math.sin(k * 2.1)
        x, y = oh.POOL[0] + r * math.cos(a), oh.POOL[1] + r * math.sin(a)
        if props.clear_of_road(c, x, y, 3.0):
            z = ground(c, ter, x, y, 1.0)
            c.place(palms[k % 4], x, y, z - 0.2, rot=a * 3, scale=0.9 + 0.3 * math.sin(k), coll="Grove", role="both")
    for f, off in ((0.38, 1.8), (0.66, -1.8)):
        i = int(f * (len(oh.SHORTCUT) - 1))
        x0, y0 = oh.SHORTCUT[i]
        x1, y1 = oh.SHORTCUT[i + 1]
        t = f * (len(oh.SHORTCUT) - 1) - i
        x, y = lerp(x0, x1, t), lerp(y0, y1, t) + off
        z = ground(c, ter, x, y, 2.0)
        c.place(palms[(i + 1) % 4], x, y, z - 0.2, rot=f * 9, scale=1.1, coll="Grove", role="both")
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


def butte_and_arch(c, oh, ter):
    """The butte inside the hairpin, banded like the canyons, and the wind-carved arch
    over the road beyond it (its legs where the greybox's stood)."""
    bt = c.rock_mass("Butte", oh.BUTTE[0], oh.BUTTE[1], 15.0, 14.0, 34.0, z0=-4, n=18, seed=5,
                     bands=[(1.15, 0.0), (1.0, 0.1), (0.92, 0.45), (0.88, 0.5), (0.86, 0.9), (0.8, 1.0)])
    c.paint_rock(bt, ("gold_cliff", "wall"), ("pale_sand", "dirt"))
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


def build(c, oh):
    ter = list(c.coll("Terrain").objects)
    sc = {"lights": [], "lanterns": [], "torches": [], "fires": []}
    village(c, oh, ter, sc)
    camp(c, oh, ter, sc)
    pool(c, oh, ter, sc)
    butte_and_arch(c, oh, ter)
    watchtower(c, oh)
    dunes(c, oh, ter)
    for x, y, z in sc["lanterns"]:
        g = c.game(x, y, z)
        c.entity("torch", x=g[0], y=g[1], z=g[2])
    for x, y, z in sc["fires"]:
        g = c.game(x, y, z)
        c.entity("campfire", x=g[0], y=g[1], z=g[2])
    groups = ("Village", "Camp", "Grove", "Dunes")
    c.merge_props(groups)
