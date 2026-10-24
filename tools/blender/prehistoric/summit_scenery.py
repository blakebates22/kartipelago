# Snowy Summit Pass's scenery (see snowy_summit.py): the glacier and its crystal caves,
# the frozen bay with its icebergs, shipwreck and mammoth path, the ice archways, the hot
# springs (geysers, travertine terraces, ice floes, steam), the wind canyons, the giant
# trees (the hollow one with the spiral inside, two more with ledges round them, a
# canopy far overhead and shafts of sunlight), the treetop bridges and the lookout, the
# glacier fields with the mammoth-skull ruins, floating ice islands, bunting everywhere,
# and the light painted on it all.
# SPDX-License-Identifier: MIT

import math

import course_kit as kit
import props
import summit_props as sp
from course_kit import Vector, bmesh, rnd


def road_rot(q):
    return math.atan2(q.t.y, q.t.x)


class Mesh:
    """A one-off mesh built in place, its faces grouped by material."""

    def __init__(self):
        self.bm = bmesh.new()
        self.slots = {}

    def mark(self, mat, k0):
        self.slots.setdefault(mat, []).extend(range(k0, len(self.bm.faces)))

    def quad(self, mat, vs):
        k0 = len(self.bm.faces)
        self.bm.faces.new(vs)
        self.mark(mat, k0)

    def build(self, c, name, coll, role="both", flat=True):
        if not self.bm.faces:
            self.bm.free()
            return None
        self.bm.faces.ensure_lookup_table()
        ob = c.mesh_object(name, self.bm, coll, role)
        for mat, faces in self.slots.items():
            c.assign(ob, c.lib(*mat) if isinstance(mat, tuple) else c.lib(mat), faces)
        if flat:
            ob.data.shade_flat()
        return ob


def far_from_road(c, x, y, margin, s_skip=None):
    """No road (other than the stretch s_skip) within `margin` of (x, y) (2D)."""
    for smp in c.S:
        if s_skip and s_skip[0] <= smp.s <= s_skip[1]:
            continue
        if (smp.p.x - x) ** 2 + (smp.p.y - y) ** 2 < (smp.w / 2 + margin) ** 2:
            return False
    return True


def ground(c, ter, x, y, default=None):
    z = c.ground_z(x, y, ter)
    return default if z is None else z


def game_entity(c, kind, x, y, z, **extra):
    gx, gy, gz = c.game(x, y, z)
    c.entity(kind, x=gx, y=gy, z=gz, **extra)


# ------------------------------------------------------------------ the glacier and its caves


def glacier(c, ss, t0, t1):
    """The glacier the Crystal Caves run through: a dome of layered blue ice, cut through
    along the route, with a solid floor under the tunnel."""
    (cx, cy), rx, ry, ang = ss.GLACIER
    rock = c.rock_mass("Glacier", cx, cy, rx, ry, ss.GLACIER_TOP, z0=-10.0, n=40, seed=11, angle=ang,
                       bands=[(1.0, 0.0), (1.0, 0.4), (0.96, 0.46), (0.93, 0.7), (0.86, 0.75), (0.7, 0.92), (0.45, 1.0)])
    half = c.width / 2 + 3.6
    c.tunnel(rock, t0, t1, half=half, height=13.0, pad=16.0)
    c.paint_rock(rock, ("glacier_ice", "wall"), ("summit_snow", "deep_snow"), floor=("crystal_road", "snow_stone"), top_z=40, floor_z=30)
    floor = []
    s = t0 - 24
    while s <= t1 + 24:
        q = c.at(s)
        # As wide as the tunnel inside the ice (no strips hidden in the solid glacier to
        # walk off), wider outside it where the land is cut away round the portals.
        inside = ss.in_glacier(q.p.x, q.p.y, 0.97)
        floor.append((q.p.x, q.p.y, 2 * half - 0.6 if inside else 2 * half + 12, q.p.z - 0.25))
        s += 2.0
    c.ribbon("Cave Floor", floor, 26, 0, c.lib("crystal_road", "snow_stone"), coll="Collision", role="collision", steps=4)
    return rock


def cave_dressing(c, ss, rock, t0, t1, blue, violet):
    """Glowing crystal clusters up the tunnel walls (and from the roof), chevrons on its
    bends, and the portals' icefalls."""
    import volcano_props as vp

    half = c.width / 2 + 3.6
    s = t0 + 6
    k = 0
    while s < t1 - 4:
        q = c.at(s)
        side = 1 if k % 2 else -1
        mat = "crystal_violet" if k % 3 == 2 else "crystal_blue"
        p = q.side(side * (half - 0.6), 0.0)
        tilt_rot = road_rot(q) + (math.pi / 2 if side > 0 else -math.pi / 2)
        c.place(vp.crystals(c, mat, k % 3), p.x, p.y, p.z - 0.4, rot=tilt_rot, scale=0.9 + 0.3 * rnd(k), coll="Caves", role="visual")
        (violet if mat == "crystal_violet" else blue).append((p.x, p.y, p.z + 3.0))
        if k % 2 == 0:
            # Hanging from the roof.
            r = q.side(-side * 3.0, 11.6)
            ob = c.place(vp.crystals(c, "crystal_blue", (k + 1) % 3), r.x, r.y, r.z, rot=tilt_rot, scale=0.6, coll="Caves", role="visual")
            ob.rotation_euler = (math.pi, 0, tilt_rot)
            blue.append((r.x, r.y, r.z - 2))
        s += 13.0
        k += 1
    # Seracs: great blocks of ice standing up all over the glacier's back.
    ice = [rock]
    k = 0
    for i in range(40):
        a = rnd(i * 3.3) * math.tau
        r = math.sqrt(rnd(i * 7.1)) * 0.95
        (gx, gy), rx, ry, ang = ss.GLACIER
        u, v = r * rx * math.cos(a), r * ry * math.sin(a)
        x, y = gx + u * math.cos(ang) - v * math.sin(ang), gy + u * math.sin(ang) + v * math.cos(ang)
        z = c.ground_z(x, y, ice)
        if z is None or z < 30:
            continue
        c.place(sp.iceberg(c, i % 4), x, y, z - 3.0, rot=rnd(i) * 6, scale=0.8 + 0.9 * rnd(i * 5), coll="Caves", role="visual")
        k += 1
        if k >= 22:
            break
    # Chevrons on the outside of the bends inside (and at the exit).
    for s_, side in ((ss.SEG[10] + 14, -1), (ss.SEG[11] + 14, 1), (ss.SEG[13] + 18, -1), (ss.SEG[13] + 40, -1)):
        q = c.at(s_)
        p = q.side(side * (q.w / 2 + 2.2))
        z = p.z
        c.place(sp.chevron(c), p.x, p.y, z - 0.3, rot=road_rot(q) + (0 if side > 0 else math.pi) + math.pi, coll="Caves", role="visual")


# ------------------------------------------------------------------ the lake


def lake(c, ss, ter):
    """The hot water at the melted end (a surface you sink into), ice floes on it, geysers
    and travertine terraces round the road across it, steaming vents, icebergs in the
    frozen bay, the shipwreck and the mammoth's path."""
    (mx, my), mrx, mry = ss.MELT
    # The hot water: a fan just under the ice, a little wider than the melt.
    m = Mesh()
    n = 72
    centre = m.bm.verts.new((mx, my, -0.3))
    rim = []
    for i in range(n):
        a = i * math.tau / n
        # Walk out until the ice begins (plus a little, under it).
        r = 0.2
        while ss.melted(mx + r * mrx * math.cos(a), my + r * mry * math.sin(a)) and r < 1.6:
            r += 0.01
        r += 0.06
        rim.append(m.bm.verts.new((mx + r * mrx * math.cos(a), my + r * mry * math.sin(a), -0.3)))
    k0 = len(m.bm.faces)
    for i in range(n):
        m.bm.faces.new((centre, rim[i], rim[(i + 1) % n]))
    m.mark(("hot_spring", "deep_water"), k0)
    water = m.build(c, "Hot Springs", "Water", "both", flat=False)

    # Ice floes drifting on it, clear of the road.
    k = 0
    tries = 0
    while k < 16 and tries < 400:
        tries += 1
        a = rnd(tries * 1.7) * math.tau
        r = math.sqrt(rnd(tries * 2.3)) * 0.85
        x, y = mx + r * mrx * math.cos(a), my + r * mry * math.sin(a)
        if not ss.melted(x, y) or not far_from_road(c, x, y, 12.0):
            continue
        c.place(sp.floe(c, k % 4), x, y, -0.3, rot=rnd(tries) * math.tau, scale=0.8 + 0.5 * rnd(tries * 3), coll="Lake")
        k += 1

    # Icebergs frozen into the bay, and a couple at the edge of the melt.
    bergs = [(-60, -110, 0), (-10, -95, 1), (70, -230, 2), (-180, -230, 3), (-110, -290, 1), (150, -260, 0), (190, -210, 2), (-260, -150, 1), (40, -300, 3), (-25, -240, 2)]
    for i, (x, y, v) in enumerate(bergs):
        if far_from_road(c, x, y, 16.0):
            c.place(sp.iceberg(c, v), x, y, -0.2, rot=rnd(i * 5) * math.tau, scale=0.8 + 0.5 * rnd(i * 3), coll="Lake")

    # The shipwreck, listing in the ice south of the bay road.
    ob = c.place(sp.shipwreck(c), 58.0, -238.0, -1.6, rot=0.35, coll="Lake")
    ob.rotation_euler = (0.17, -0.06, 0.35)
    for k in range(9):
        a = k * 0.7 + 0.2
        x, y = 58.0 + 22 * math.cos(a) * (0.9 + 0.3 * rnd(k)), -238.0 + 9 * math.sin(a) * (1.0 + 0.4 * rnd(k * 3))
        fl = c.place(sp.floe(c, k % 4), x, y, -0.2, rot=rnd(k * 7) * 6, scale=0.5 + 0.3 * rnd(k), coll="Lake")
        fl.rotation_euler = (0.25 * (rnd(k * 5) - 0.5), 0.3 * (rnd(k * 9) - 0.5), rnd(k * 7) * 6)
    return water


def hot_springs(c, ss, ter, geysers):
    """Geysers (one in the road; one under the jump; more round about), travertine
    terraces stepping down to the water, and steam."""
    S = ss.SEG
    # The geyser in the road, on the terraces.
    q = c.at(S[4] + 26)
    c.place(sp.geyser_cone(c, 0, flush=True), q.p.x, q.p.y, q.p.z - 0.08, rot=road_rot(q), coll="Springs", role="visual")
    geysers.append((q.p.x, q.p.y, q.p.z, 4.2, 22.0, 0.0, True))
    # The big one under the jump: the column fills the gap.
    lip, land = ss.JUMPS[0]
    q = c.at((lip + land) / 2)
    c.place(sp.geyser_cone(c, 2), q.p.x, q.p.y, -1.6, coll="Springs", role="visual")
    geysers.append((q.p.x, q.p.y, -0.3, 5.5, 26.0, 2.0, True))
    # More round about (they blow, but nowhere near the road).
    spots = [(S[4] + 10, -24), (S[4] + 40, 22), (S[7] + 20, -26), (S[7] + 45, 24), (S[8] + 40, 26), (S[9] + 10, -24), (S[3] + 20, 30)]
    for k, (s, off) in enumerate(spots):
        q = c.at(s)
        p = q.side(off)
        z = ground(c, ter, p.x, p.y, 0.0)
        z = max(z, -0.3)
        c.place(sp.geyser_cone(c, 1 + k % 2), p.x, p.y, z - 0.3, rot=rnd(k) * 6, coll="Springs")
        geysers.append((p.x, p.y, z + 1.5, 3.5, 18.0 + 6 * rnd(k * 3), 1.0 + k * 1.7, False))
    # Terraces stepping down from the road on both sides.
    s = S[4] + 4
    k = 0
    while s < S[8] + 50:
        if ss.JUMPS[0][0] - 14 < s < ss.JUMPS[0][1] + 6:
            s += 10
            continue
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 5.5))
            if not far_from_road(c, p.x, p.y, 3.5):
                continue
            ob = c.place(sp.terrace_pools(c, k % 2), p.x, p.y, q.p.z - 0.6, rot=road_rot(q) + (math.pi if side < 0 else 0) - math.pi / 2, coll="Springs", role="visual")
            k += 1
        s += 17.0


def ice_arches(c, ss):
    """The Ice Archways: natural arches of blue ice over the S-bends."""
    for k, s in enumerate((ss.SEG[1] + 14, ss.SEG[2] + 18, ss.SEG[3] + 26)):
        q = c.at(s)
        c.place(sp.ice_arch(c, q.w + 12.0, 14.0 + 2 * (k % 2), k), q.p.x, q.p.y, q.p.z - 0.5, rot=road_rot(q) + math.pi / 2, coll="Arches")


# ------------------------------------------------------------------ the giant trees


def hollow_tree(c, ss, glow_pts):
    """The great hollow tree (84 m across at the road): a thick shell of bark outside and
    golden heartwood inside, an arched doorway where the road comes in at the bottom and
    another where it leaves 30 m up, knotholes letting the sunlight in, a heartwood
    column in the middle the spiral winds round, a floor, a ceiling, beams under every
    turn of the spiral, and above it all the trunk climbing to a vast crown."""
    cx, cy = ss.TREE1
    ri, ro = ss.TREE1_R
    P = Vector(next(p for p in ss.PATH if p[3] == 22)[:2])
    h = math.radians(next(p for p in ss.PATH if p[3] == 22)[2])
    d = Vector((math.cos(h), math.sin(h)))
    S22, S23 = ss.SEG[22], ss.SEG[23]

    def opening(x, y, z):
        """Is this point of the wall in one of the doorways (or a knothole)?"""
        rel = Vector((x, y)) - P
        t = rel.dot(d)
        lat = abs(rel.x * d.y - rel.y * d.x)
        # Only where the line crosses the wall (the two doorways), not all along it.
        cross = math.sqrt(max(0.0, (ri + 2.5) ** 2 - ss.HELIX_R**2))
        if abs(abs(t) - cross) > 13.0:
            return False
        zr = ss.road_z(S22 + t if t < 0 else S23 + t)
        top = zr + 9.0
        if z < zr - 1.5 or z > top + 4.5:
            return False
        hw = 11.5 if z <= top else 11.5 * math.sqrt(max(0.0, 1 - ((z - top) / 4.5) ** 2))
        return lat < hw

    knots = [(30.0, 26.0, 4.0), (110.0, 33.0, 3.5), (200.0, 20.0, 4.5), (250.0, 44.0, 4.0), (320.0, 30.0, 3.5), (150.0, 52.0, 3.0), (20.0, 55.0, 3.0)]

    def knothole(a_deg, z):
        for ka, kz, kr in knots:
            da = ((a_deg - ka + 180) % 360 - 180) * math.pi / 180 * ri
            if (da / kr) ** 2 + ((z - kz) / (kr * 1.3)) ** 2 < 1:
                return True
        return False

    N = 80
    zs = [-4.0 + 2.0 * j for j in range(36)]  # -4 .. 66
    m = Mesh()
    bm = m.bm

    def r_out(z):
        return ro + 9.0 * math.exp(-max(0.0, z - 6.0) / 5.0) + 0.8 * math.sin(z / 3.1)

    vo, vi = {}, {}
    for i in range(N):
        a = i * math.tau / N
        wob = 1.0 + 0.025 * math.sin(a * 7) + 0.015 * math.sin(a * 13 + 1)
        for j, z in enumerate(zs):
            vo[i, j] = bm.verts.new((cx + r_out(z) * wob * math.cos(a), cy + r_out(z) * wob * math.sin(a), z))
            vi[i, j] = bm.verts.new((cx + ri * math.cos(a), cy + ri * math.sin(a), z))
    present = {}
    for i in range(N):
        a0 = (i + 0.5) * math.tau / N
        for j in range(len(zs) - 1):
            zc = (zs[j] + zs[j + 1]) / 2
            x, y = cx + (ri + 2.5) * math.cos(a0), cy + (ri + 2.5) * math.sin(a0)
            present[i, j] = not (opening(x, y, zc) or knothole(math.degrees(a0) % 360, zc))
    bark, wood = [], []
    for (i, j), on in present.items():
        if not on:
            continue
        i1 = (i + 1) % N
        k0 = len(bm.faces)
        bm.faces.new((vo[i, j], vo[i1, j], vo[i1, j + 1], vo[i, j + 1]))
        bark.append(k0)
        bm.faces.new((vi[i, j + 1], vi[i1, j + 1], vi[i1, j], vi[i, j]))
        wood.append(k0 + 1)
        # Jambs where the next cell is missing (or at the top and bottom).
        for (ni, nj), edge in (((i1, j), "r"), (((i - 1) % N, j), "l"), ((i, j + 1), "t"), ((i, j - 1), "b")):
            if present.get((ni, nj), False):
                continue
            if edge == "r":
                q = (vo[i1, j], vi[i1, j], vi[i1, j + 1], vo[i1, j + 1])
            elif edge == "l":
                q = (vo[i, j + 1], vi[i, j + 1], vi[i, j], vo[i, j])
            elif edge == "t":
                q = (vo[i, j + 1], vo[i1, j + 1], vi[i1, j + 1], vi[i, j + 1])
            else:
                q = (vo[i1, j], vo[i, j], vi[i, j], vi[i1, j])
            k1 = len(bm.faces)
            bm.faces.new(q)
            wood.append(k1)
    m.slots[("giant_bark", "wall")] = bark
    m.slots[("heartwood", "wall")] = wood
    shell = m.build(c, "Great Tree Shell", "Trees", "both", flat=False)

    # The floor, the column, the ceiling and the trunk above it.
    m = Mesh()
    bm = m.bm
    zf = ss.road_z(S22) - 0.45
    k0 = len(bm.faces)
    ring_f = props.ring(bm, (cx, cy), ri + 5.0, zf, 48)  # (on under the wall: no gap at its foot)
    bm.faces.new(ring_f)
    m.mark(("forest_road", "dirt"), k0)
    k0 = len(bm.faces)
    col = [props.ring(bm, (cx, cy), 11.0 + 1.5 * math.exp(-(z - zf) / 4), z, 24, phase=0.1 * j) for j, z in enumerate((zf - 1, zf + 4, zf + 20, zf + 40, 60, 64.5))]
    props.loft(bm, col, cap_top=False)
    m.mark(("heartwood", "wall"), k0)
    k0 = len(bm.faces)
    up = [props.ring(bm, (cx, cy), r, z, 40) for r, z in ((ri + 0.4, 64.0), (ro + 1.5, 64.0), (ro + 0.5, 90.0), (ro - 3.0, 120.0), (ro - 9.0, 150.0), (ro - 16.0, 168.0))]
    bm.faces.new(list(reversed(up[0])))  # the ceiling, facing down
    m.mark(("heartwood", "wall"), k0)
    k0 = len(bm.faces)
    props.loft(bm, [up[0], up[1]], cap_top=False)
    props.loft(bm, up[1:], cap_top=True)
    m.mark(("giant_bark", "wall"), k0)
    trunk = m.build(c, "Great Tree Trunk", "Trees", "both", flat=False)

    # Beams under every turn of the spiral, and glowing moss on the column and walls.
    m = Mesh()
    bm = m.bm
    turns = ss.HELIX_TURNS
    L = S23 - S22
    for k in range(int(turns * 12)):
        s = S22 + L * (k + 0.5) / (turns * 12)
        q = c.at(s)
        rel = Vector((q.p.x - cx, q.p.y - cy, 0)).normalized()
        a = math.atan2(rel.y, rel.x)
        zb = q.p.z - 2.2
        k0 = len(bm.faces)
        props.cuboid(bm, (cx + rel.x * 24.5, cy + rel.y * 24.5, zb), (26.0, 1.4, 1.2), rot=a)
        props.cuboid(bm, (cx + rel.x * (ri - 1.0), cy + rel.y * (ri - 1.0), zb - 2.5), (1.4, 1.4, 6.0), rot=a)
        m.mark(("heartwood", "wall"), k0)
    for k in range(18):
        a = k * 2.4
        z = zf + 3 + (k * 3.1) % 50
        r = 11.6 if k % 2 else ri - 0.3
        k0 = len(bm.faces)
        props.blob(bm, (cx + r * math.cos(a), cy + r * math.sin(a), z), 1.6 + 0.8 * rnd(k), sx=1.0, sy=1.0, sz=0.5, subdiv=1)
        m.mark("glow_moss", k0)
        glow_pts.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
    # Shelf fungi glowing on the walls, high above the rails.
    for k in range(16):
        a = k * 2.05 + 0.4
        z = zf + 6 + (k * 3.7) % 48
        r = ri - 0.2
        k0 = len(bm.faces)
        rim = [bm.verts.new((cx + (r - 2.2 * math.sin(math.pi * j / 6)) * math.cos(a + 0.09 * (j - 3)), cy + (r - 2.2 * math.sin(math.pi * j / 6)) * math.sin(a + 0.09 * (j - 3)), z)) for j in range(7)]
        under = bm.verts.new((cx + (r - 0.2) * math.cos(a), cy + (r - 0.2) * math.sin(a), z - 0.9))
        bm.faces.new(rim)
        for j in range(6):
            bm.faces.new((rim[j + 1], rim[j], under))
        m.mark("glow_moss", k0)
        glow_pts.append((cx + (r - 1.5) * math.cos(a), cy + (r - 1.5) * math.sin(a), z))
    m.build(c, "Great Tree Beams", "Trees", "visual")
    # Sunbeams slanting in through the knotholes.
    sh = Mesh()
    for ka, kz, kr in knots:
        a = math.radians(ka)
        glow_pts.append((cx + (ri - 2) * math.cos(a), cy + (ri - 2) * math.sin(a), kz))
        o = Vector((cx + (ri + 3) * math.cos(a), cy + (ri + 3) * math.sin(a), kz))
        d_ = Vector((-math.cos(a), -math.sin(a), -0.55)).normalized()
        side = Vector((-math.sin(a), math.cos(a), 0))
        far = o + d_ * 34.0
        k0 = len(sh.bm.faces)
        ring_a = [sh.bm.verts.new(o + side * (kr * 0.8) * math.cos(j * math.tau / 5) + Vector((0, 0, kr * math.sin(j * math.tau / 5)))) for j in range(5)]
        ring_b = [sh.bm.verts.new(far + side * (kr * 1.4) * math.cos(j * math.tau / 5) + Vector((0, 0, kr * 1.4 * math.sin(j * math.tau / 5)))) for j in range(5)]
        for j in range(5):
            sh.bm.faces.new((ring_a[j], ring_a[(j + 1) % 5], ring_b[(j + 1) % 5], ring_b[j]))
        sh.mark("light_shaft", k0)
    sh.build(c, "Great Tree Sunbeams", "Shafts", "visual", flat=False)
    # Light coming in at the doorways.
    for t, base in ((-31.0, S22), (31.0, S23)):
        p = P + d * t
        glow_pts.append((p.x, p.y, ss.road_z(base + t) + 4.0))
    crown(c, cx, cy, 150.0, 1.0, 0)
    roots(c, ss, cx, cy, ro + 4.0, ss.road_z(S22) - 0.5, 9)
    return shell, trunk


def roots(c, ss, cx, cy, r0, z0, n):
    """Great roots spreading from a trunk over the ground (skipping any that would cross
    the road)."""
    m = Mesh()
    for k in range(n):
        a = k * math.tau / n + 0.3
        x1, y1 = cx + (r0 + 22) * math.cos(a), cy + (r0 + 22) * math.sin(a)
        mx_, my_ = cx + (r0 + 8) * math.cos(a), cy + (r0 + 8) * math.sin(a)
        if not (far_from_road(c, x1, y1, 4.0) and far_from_road(c, mx_, my_, 4.0)):
            continue
        k0 = len(m.bm.faces)
        props.tube(m.bm, [(cx + (r0 - 6) * math.cos(a), cy + (r0 - 6) * math.sin(a), z0 + 6.0), (mx_, my_, z0 + 2.5), (x1, y1, z0 - 1.5)], [5.0, 3.2, 1.0], n=7)
        m.mark(("giant_bark", "wall"), k0)
    m.build(c, "Roots %d %d" % (int(cx), int(cy)), "Trees", "both")


def crown(c, cx, cy, z, size, seed):
    """A giant's crown: great limbs and a vast spreading canopy of fresh green (with the
    last snow lying on top here and there)."""
    m = Mesh()
    bm = m.bm
    ends = []
    for k in range(7):
        a = k * math.tau / 7 + seed
        reach = (38.0 + 14 * rnd(k + seed * 3)) * size
        z0 = z - 30 + 8 * (k % 3)
        end = (cx + reach * math.cos(a), cy + reach * math.sin(a), z0 + 18 * size)
        k0 = len(bm.faces)
        props.tube(bm, [(cx + 10 * math.cos(a) * size, cy + 10 * math.sin(a) * size, z0), (cx + reach * 0.55 * math.cos(a), cy + reach * 0.55 * math.sin(a), z0 + 12 * size), end], [4.2 * size, 2.6 * size, 1.2 * size], n=6)
        m.mark(("giant_bark", "wall"), k0)
        ends.append(end)
    blobs = [(cx, cy, z + 20 * size, 34.0 * size)] + [(x, y, zz + 4, (18.0 + 6 * rnd(k + seed)) * size) for k, (x, y, zz) in enumerate(ends)]
    for k, (x, y, zz, r) in enumerate(blobs):
        k0 = len(bm.faces)
        props.blob(bm, (x, y, zz), r, sz=0.45, subdiv=2)
        m.mark("leaf_bright", k0)
        if k % 2 == 0:
            k0 = len(bm.faces)
            sp._cap(bm, (x + r * 0.15, y, zz + r * 0.4), r * 0.55, 1.6)
            m.mark("summit_snow", k0)
    return m.build(c, "Crown %d %d" % (int(cx), int(cy)), "Canopy", "visual", flat=False)


def giant_tree(c, cx, cy, z_ledge, seed):
    """One of the other giants (42 m across at the ledge): a flared trunk, its ledge's
    brackets, and a crown far above."""
    m = Mesh()
    bm = m.bm
    r = 21.0
    rings = []
    for j, z in enumerate((-6.0, 6.0, 12.0, 24.0, z_ledge - 6, z_ledge + 20, 100.0, 140.0, 152.0)):
        rr = (r + 12.0 * math.exp(-max(0.0, z - 6.0) / 6.0)) * (1.0 - 0.0016 * max(0.0, z - 60))
        rings.append(props.ring(bm, (cx, cy), rr, z, 28, phase=0.13 * j))
    props.loft(bm, rings, cap_top=True)
    m.mark(("giant_bark", "wall"), 0)
    # Brackets under the ledge.
    for k in range(14):
        a = k * math.tau / 14 + seed
        k0 = len(bm.faces)
        props.tube(bm, [(cx + (r - 1) * math.cos(a), cy + (r - 1) * math.sin(a), z_ledge - 10.0), (cx + 30.0 * math.cos(a), cy + 30.0 * math.sin(a), z_ledge - 2.5)], [1.0, 0.7], n=5)
        m.mark(("heartwood", "wall"), k0)
    m.build(c, "Giant Tree %d %d" % (int(cx), int(cy)), "Trees", "both", flat=False)
    crown(c, cx, cy, 150.0, 0.8, seed)
    roots(c, None, cx, cy, r + 6.0, 9.0, 8)


def forest(c, ss, ter):
    """The forest between frozen and thawed: snowy pines up high and to the west, green
    broadleaf trees and thawed pines on the low ground, a few mid-sized giants whose
    crowns the bridges pass through, shrubs, and shafts of sunlight."""
    trees = [(ss.TREE1, 44.0), (ss.TREE2, 30.0), (ss.TREE3, 30.0)]

    def ok(x, y, z):
        if not far_from_road(c, x, y, 6.0):
            return False
        if any(math.hypot(x - tx, y - ty) < tr for (tx, ty), tr in trees):
            return False
        return z > 3.0 and ss.lake_k(x, y) > 1.15

    in_forest = (-260, 140, 30, 330)
    thaw = lambda x, y, z: ok(x, y, z) and z < 18 and (math.sin(x / 23) + math.cos(y / 19)) > -0.4  # noqa: E731
    snowy = lambda x, y, z: ok(x, y, z) and not thaw(x, y, z)  # noqa: E731
    for v in range(3):
        props.scatter(c, sp.broadleaf(c, v, frosted=v == 2), 26, in_forest, thaw, ter, seed=40 + v, scale=(0.9, 1.6), coll="Forest", role="visual")
        props.scatter(c, sp.pine(c, v, 14.0 + 3 * v, snowy=False), 12, in_forest, thaw, ter, seed=50 + v, scale=(0.9, 1.5), coll="Forest", role="visual")
        props.scatter(c, sp.pine(c, v, 14.0 + 4 * v), 28, in_forest, snowy, ter, seed=60 + v, scale=(0.9, 1.6), coll="Forest", role="visual")
        props.scatter(c, sp.shrub(c, v, frosted=v != 1), 14, in_forest, ok, ter, seed=70 + v, scale=(0.8, 1.4), coll="Forest", role="visual")
    # Pines all round the lake and up the slopes.
    def slopes(x, y, z):
        return far_from_road(c, x, y, 7.0) and ss.lake_k(x, y) > 1.12 and 1.5 < z < 70 and not ss.in_glacier(x, y, 1.1)

    for v in range(3):
        props.scatter(c, sp.pine(c, v + 3, 11.0 + 3 * v), 42, (-480, 480, -460, 30), slopes, ter, seed=80 + v, scale=(0.8, 1.5), coll="Pines", role="visual")
        props.scatter(c, sp.pine(c, v + 3, 11.0 + 3 * v), 26, (140, 480, 30, 460), slopes, ter, seed=90 + v, scale=(0.8, 1.4), coll="Pines", role="visual")
        props.scatter(c, sp.boulder(c, v), 18, (-480, 480, -460, 460), slopes, ter, seed=100 + v, scale=(0.7, 1.6), coll="Pines")
    # Mid-sized giants (35-40 m) whose crowns crowd the treetop bridges.
    for k, (x, y) in enumerate(((-40, 170), (-60, 95), (-150, 190), (-75, 205), (-150, 115), (-30, 230), (-165, 290), (40, 230), (-200, 160))):
        if not far_from_road(c, x, y, 14.0):
            continue
        z = ground(c, ter, x, y, 10.0)
        c.place(sp.broadleaf(c, k % 3, frosted=k % 3 == 0), x, y, z - 0.5, rot=k * 1.3, scale=3.2, coll="Forest", role="visual")
    # Sunlight slanting down through the canopy.
    m = Mesh()
    for k, (x, y) in enumerate(((-20, 60), (-120, 70), (-55, 140), (-120, 260), (30, 200), (-200, 230), (-90, 180), (70, 140))):
        z = ground(c, ter, x, y, 10.0)
        k0 = len(m.bm.faces)
        top = [m.bm.verts.new((x + 30 + 9 * math.cos(i * math.tau / 6), y + 20 + 9 * math.sin(i * math.tau / 6), z + 120)) for i in range(6)]
        bot = [m.bm.verts.new((x + 5 * math.cos(i * math.tau / 6), y + 5 * math.sin(i * math.tau / 6), z)) for i in range(6)]
        for i in range(6):
            m.bm.faces.new((bot[i], bot[(i + 1) % 6], top[(i + 1) % 6], top[i]))
        m.mark("light_shaft", k0)
    m.build(c, "Light Shafts", "Shafts", "visual", flat=False)


# ------------------------------------------------------------------ bridges, the lookout and flags


def rope_bridge(c, ss):
    """The swinging rope bridge out of the great tree, built plank by plank (its road
    piece is collision only): loose planks with gaps between them, a few missing, laid
    on rope stringers; rope handrails netted down to the planks; big log posts at both
    ends with the main ropes slung from their tops; broken planks dangling underneath
    and one hanger snapped. It sags in the middle and looks ready to go."""
    s0, s1 = ss.R(ss.SEG[23] + 33), ss.R(ss.SEG[24])
    m = Mesh()
    bm = m.bm
    rope = "rope_rail"

    def tube(pts, r, n=5):
        k0 = len(bm.faces)
        props.tube(bm, [tuple(p) for p in pts], r, n=n)
        m.mark(rope, k0)

    def along(off, up, a=s0, b=s1, step=1.0):
        pts, s = [], a
        while s < b:
            pts.append(c.at(s).side(off, up))
            s += step
        pts.append(c.at(b).side(off, up))
        return pts

    half = c.at((s0 + s1) / 2).w / 2
    # The planks.
    k = 0
    s = s0 + 0.4
    while s < s1 - 0.3:
        q = c.at(s)
        k += 1
        if k % 7 == 4 and s0 + 3 < s < s1 - 3:
            s += 1.0
            continue  # a missing plank
        jit = math.sin(k * 2.7)
        k0 = len(bm.faces)
        props.cuboid(bm, (q.p.x, q.p.y, q.p.z - 0.07 + 0.03 * jit), (0.74, q.w + 0.6 - 0.25 * (k % 3), 0.14), rot=road_rot(q) + 0.05 * jit, tilt=(0.03 * math.cos(k * 1.3), 0.0))
        m.mark("plank_road" if k % 3 else ("heartwood", "wall"), k0)
        s += 1.0
    # The stringers under the planks, the handrails and a middle rope on each side, and
    # the netting between them.
    for side in (-1, 1):
        tube(along(side * (half - 0.4), -0.2), 0.1)
        top = along(side * (half + 0.3), 1.15)
        mid = along(side * (half + 0.3), 0.6)
        foot = along(side * (half + 0.2), -0.05)
        tube(top, 0.08)
        tube(mid, 0.05)
        for j in range(len(top) - 1):
            if side > 0 and j == len(top) // 2:
                continue  # one hanger's snapped
            a, b = (top[j], foot[j + 1]) if j % 2 == 0 else (foot[j], top[j + 1])
            tube([a, b], 0.03, n=4)
        snap = top[len(top) // 2]
        tube([snap, snap + Vector((0.15, 0.1, -0.7))], 0.03, n=4)
    # The posts, and the main ropes slung from their tops to the handrails mid-span.
    tops = []
    for s_, lean in ((s0 - 0.6, -0.12), (s1 + 0.6, 0.12)):
        q = c.at(s_)
        pair = []
        for side in (-1, 1):
            p = q.side(side * (half + 0.9))
            k0 = len(bm.faces)
            props.tube(bm, [tuple(p + Vector((0, 0, -2.0))), tuple(p + Vector((0, 0, 4.2)))], 0.34, n=8)
            m.mark(("heartwood", "wall"), k0)
            t = p + Vector((0, 0, 3.9))
            tube([t + Vector((0, 0, -0.35)), t + Vector((0, 0, 0.15))], 0.42, n=6)
            pair.append(t)
        tops.append(pair)
    n = 20
    for j, side in enumerate((-1, 1)):
        a, b = tops[0][j], tops[1][j]
        rail = along(side * (half + 0.3), 1.15, step=(s1 - s0) / n)
        pts = []
        for i in range(n + 1):
            t = i / n
            p = a.lerp(b, t)
            r = rail[min(i, len(rail) - 1)]
            # Down from the post tops to just above the handrail in the middle.
            p.z = lerp_z(p.z, r.z + 0.35, math.sin(math.pi * t) ** 0.7)
            pts.append(p)
        tube(pts, 0.11)
        for i in range(2, n - 1, 3):
            tube([pts[i], rail[min(i, len(rail) - 1)]], 0.03, n=4)
    # Two broken planks hanging underneath by a rope.
    for t, side in ((0.35, 1), (0.66, -1)):
        q = c.at(s0 + (s1 - s0) * t)
        e = q.side(side * (half - 0.8), -1.7)
        k0 = len(bm.faces)
        props.cuboid(bm, (e.x, e.y, e.z), (0.62, 0.14, 2.6), rot=road_rot(q), tilt=(0.25 * side, 0.15))
        m.mark("plank_road", k0)
        tube([e + Vector((0, 0, 1.3)), q.side(side * (half - 0.4), -0.2)], 0.035, n=4)
    m.build(c, "Rope Bridge", "Bridges", "visual", flat=False)


def lerp_z(a, b, t):
    return a + (b - a) * t


def bridges_and_flags(c, ss, ter, flags):
    """Bunting along the treetop bridges and round the ledges (from posts on the rails),
    over the start, across the canyon, and round the lookout, with its hut and cairns."""
    S = ss.SEG
    post = sp.flag_pole(c, 4.5)
    for i0, i1 in ((24, 25), (25, 26), (26, 27), (27, 28)):
        s = S[i0] + 4
        prev = None
        while s < S[i1] - 2:
            q = c.at(s)
            pair = []
            for side in (-1, 1):
                p = q.side(side * (q.w / 2 + 0.7))
                c.place(post, p.x, p.y, p.z, coll="Bridges", role="visual")
                pair.append(p + Vector((0, 0, 4.4)))
            if prev is not None:
                for a, b in zip(prev, pair):
                    flags.line(a, b, sag=0.6, spacing=1.1, size=0.6)
            prev = pair
            s += 12.0
    # The start: two tall poles and lines of flags over the grid.
    q = c.at(-6.0)
    pole = sp.flag_pole(c, 11.0)
    ends = []
    for side in (-1, 1):
        p = q.side(side * (q.w / 2 + 3.0))
        c.place(pole, p.x, p.y, p.z - 0.3, coll="Flags", role="visual")
        ends.append(p)
    for k in range(4):
        flags.line(ends[0] + Vector((0, 0, 10.6 - k * 0.9)), ends[1] + Vector((0, 0, 10.6 - k * 0.9)), sag=1.6 + 0.4 * k, spacing=1.1, size=0.85)
    for s0 in (25.0, 62.0):
        a, b = c.at(s0), c.at(s0 + 25)
        for side in (-1, 1):
            p0, p1 = a.side(side * (a.w / 2 + 3.0)), b.side(side * (b.w / 2 + 3.0))
            c.place(pole, p0.x, p0.y, p0.z - 0.3, coll="Flags", role="visual")
            flags.line(p0 + Vector((0, 0, 10.6)), p1 + Vector((0, 0, 10.6)), sag=2.0, spacing=1.2, size=0.8)
    # Across the canyon, wall to wall.
    for k, s in enumerate((S[14] + 10, S[14] + 40, S[16] + 20)):
        q = c.at(s)
        a, b = q.side(-(q.w / 2 + 9.0), 13.0), q.side(q.w / 2 + 9.0, 13.0)
        flags.line(a, b, sag=3.0, spacing=1.3, size=0.9)
    # The lookout: a hut, cairns and poles strung with flags round the edge.
    lx, ly = ss.LOOKOUT
    z = ground(c, ter, lx, ly, 47.0)
    c.place(sp.lookout_hut(c), lx - 6, ly + 6, z - 0.2, rot=0.6, coll="Flags")
    poles = []
    for k in range(10):
        q = c.at(S[28] + 8 + 7.0 * k)
        p = q.side(-(q.w / 2 + 2.2))
        c.place(pole, p.x, p.y, p.z - 0.3, coll="Flags", role="visual")
        poles.append(p + Vector((0, 0, 10.4)))
    for a, b in zip(poles, poles[1:]):
        flags.line(a, b, sag=1.2, spacing=1.1, size=0.8)
    for k in range(5):
        a = k * 1.3
        x, y = lx + 14 * math.cos(a), ly + 14 * math.sin(a)
        if far_from_road(c, x, y, 3.0):
            zz = ground(c, ter, x, y, z)
            c.place(sp.ruin_column(c, k), x, y, zz - 0.3, coll="Flags")
    return (lx - 6, ly + 6, z + 1.0)


# ------------------------------------------------------------------ the canyons, the ridge and the ruins


def canyons(c, ss, ter):
    """The Wind Canyons: chevrons on the bends, an ice arch over the road, and frozen
    falls down into the gorge either side of the jump."""
    S = ss.SEG
    for s_, side in ((S[15] + 12, 1), (S[16] + 12, -1), (S[20] + 10, -1), (S[30] + 14, -1), (S[31] + 14, 1)):
        q = c.at(s_)
        p = q.side(side * (q.w / 2 + 3.0))
        z = ground(c, ter, p.x, p.y, q.p.z)
        c.place(sp.chevron(c), p.x, p.y, z - 0.2, rot=road_rot(q) + (0 if side > 0 else math.pi) + math.pi, coll="Canyons", role="visual")
    q = c.at(S[14] + 28)
    c.place(sp.ice_arch(c, q.w + 14, 17.0, 3), q.p.x, q.p.y, q.p.z - 0.5, rot=road_rot(q) + math.pi / 2, coll="Canyons")
    import winter_props as wp

    lip, land = ss.JUMPS[1]
    q = c.at((lip + land) / 2)
    for k, dy in enumerate((-36.0, 32.0)):
        x, y = q.p.x + 2.0 * k, q.p.y + dy
        wp.ice_fall(c, "Gorge Icefall %d" % k, x, y, q.p.z + 14.0, -12.0, 14.0, facing=(0.0, -1.0 if dy > 0 else 1.0), coll="Canyons")


def ruins(c, ss, ter):
    """The Polar Ruins on the glacier fields: a colossal mammoth skull beside the road,
    its tusks arching over it, ribs and frozen towers round about."""
    S = ss.SEG
    q = c.at(S[35] + 44)
    c.place(sp.tusk_gate(c, q.w + 18.0, 15.0), q.p.x, q.p.y, q.p.z - 1.2, rot=road_rot(q) + math.pi / 2, coll="Ruins")
    for k, (s, off, v) in enumerate(((S[35] + 10, 26, 0), (S[35] + 80, -30, 1), (S[34] + 30, 24, 0), (S[36] - 5, -28, 1))):
        p = c.at(s).side(off)
        c.place(sp.ribs(c, v), p.x, p.y, -0.6, rot=rnd(k) * 6, coll="Ruins")
    for k, (s, off, h) in enumerate(((S[35] + 20, -40, 22.0), (S[35] + 100, 34, 16.0), (S[34] + 10, -26, 26.0), (120.0, 30, 18.0), (30.0, -34, 20.0))):
        p = c.at(s).side(off)
        z = ground(c, ter, p.x, p.y, 0.0)
        c.place(sp.tower_ruin(c, k % 3, h), p.x, p.y, z - 1.0, rot=rnd(k) * 6, coll="Ruins")
    for k in range(8):
        s = S[35] + 14 * k
        p = c.at(s).side((1 if k % 2 else -1) * (c.at(s).w / 2 + 8 + 6 * rnd(k)))
        c.place(sp.ruin_column(c, k), p.x, p.y, -0.3, rot=rnd(k * 3) * 6, coll="Ruins")


def sky_islands(c):
    """Floating ice islands high over the plateau and the lake's far shore."""
    for k, (x, y, z) in enumerate(((250.0, 30.0, 100.0), (200.0, -360.0, 80.0), (430.0, 230.0, 130.0), (-80.0, 400.0, 125.0), (-340.0, 110.0, 105.0), (-300.0, -360.0, 85.0))):
        c.place(sp.floating_island(c, k % 3), x, y, z, rot=k * 1.1, scale=0.6 + 0.15 * (k % 2), coll="Sky", role="visual")


def mammoth_path(c, ss):
    """The mammoths' walk: a loop on the frozen bay between the road and the shipwreck."""
    cx, cy, rx, ry = -55.0, -244.0, 62.0, 30.0
    pts = []
    for k in range(16):
        a = k * math.tau / 16
        pts.append((cx + rx * math.cos(a) + 6 * math.sin(3 * a), cy + ry * math.sin(a), 0.0))
    c.path_curve("Mammoth Path", pts, z=0.0, closed=True)


# ------------------------------------------------------------------ build


def build(c, rock, t0, t1, ss):
    ter = list(c.coll("Terrain").objects)
    blue, violet, tree_glow, geysers = [], [], [], []
    flags = sp.Bunting()

    cave_dressing(c, ss, rock, t0, t1, blue, violet)
    water = lake(c, ss, ter)
    hot_springs(c, ss, ter, geysers)
    ice_arches(c, ss)
    shell, trunk = hollow_tree(c, ss, tree_glow)
    for k, (tree, seg) in enumerate(((ss.TREE2, 24), (ss.TREE3, 26))):
        giant_tree(c, tree[0], tree[1], ss.road_z(ss.SEG[seg] + 30), k + 1)
    forest(c, ss, ter)
    hut = bridges_and_flags(c, ss, ter, flags)
    rope_bridge(c, ss)
    canyons(c, ss, ter)
    ruins(c, ss, ter)
    sky_islands(c)
    mammoth_path(c, ss)
    flags.build(c)

    # Entities: the geysers (on a fixed beat of the race clock), steam, the mammoths.
    for k, (x, y, z, r, height, offset, road) in enumerate(geysers):
        game_entity(c, "geyser", x, y, z, r=r, height=height, period=7.0 if road else 9.0 + (k % 3), offset=offset, warn=1.4, blast=2.2, launch=15.0 if road else 0.0)
    for k in range(12):
        s = ss.SEG[3] + 20 + k * 22
        q = c.at(s)
        p = q.side((1 if k % 2 else -1) * (q.w / 2 + 9.0 + 6 * rnd(k)))
        game_entity(c, "steam", p.x, p.y, -0.2)
    game_entity(c, "campfire", hut[0] + 4, hut[1] - 3, hut[2] - 1.0)
    c.entity("dinosaur", route="Mammoth Path", speed=1.7, scale=1.0, model="mammoth")
    c.entity("dinosaur", route="Mammoth Path", speed=1.7, scale=0.55, model="mammoth", start=14.0)

    # Joined copies (far fewer draw calls), then the light: the caves glow blue and violet,
    # the hollow tree warm gold, and the forest floor lies in dappled shade.
    groups = ("Caves", "Lake", "Springs", "Arches", "Forest", "Pines", "Bridges", "Flags", "Canyons", "Ruins")
    c.merge_props(groups)
    joined = [o for name in groups for o in c.coll(name).objects if o.type == "MESH" and o.data.users == 1]

    def in_caves(w):
        return ss.in_glacier(w.x, w.y, 1.0) and w.z < 40

    c.glow([rock], blue, 16.0, (0.75, 0.95, 1.5), base=(0.5, 0.6, 0.9), region=in_caves)
    c.glow([rock], violet, 14.0, (1.15, 0.75, 1.5), base=1.0, region=in_caves)

    cx, cy = ss.TREE1

    def in_tree(w):
        return math.hypot(w.x - cx, w.y - cy) < ss.TREE1_R[0] + 0.5 and w.z < 64.5

    c.glow([o for o in c.coll("Trees").objects if o.type == "MESH"], tree_glow, 18.0, (1.35, 1.2, 0.85), base=(0.55, 0.48, 0.42), region=in_tree)

    def shade(w):
        return w.y > 30 and -270 < w.x < 150 and w.z < 60 and not in_tree(w)

    sun_spots = [(x, y, 10.0) for x, y in ((-20, 60), (-120, 70), (-55, 140), (-120, 260), (30, 200), (-200, 230), (-90, 180), (70, 140))]
    forest_obs = [o for name in ("Forest", "Trees") for o in c.coll(name).objects if o.type == "MESH" and o.data.users == 1]
    c.glow(ter + forest_obs, sun_spots, 26.0, (1.12, 1.1, 1.0), base=(0.78, 0.84, 0.8), region=shade)
    return water
