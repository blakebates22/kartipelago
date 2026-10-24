# Hearthglow Hollow's scenery (see hearthglow_hollow.py): the village (streets of
# cottages, the square with the giant tree, market stalls, the frozen fountain, lantern
# posts, strings of lights), the stone bridge and the river with its falls, the
# enchanted forest, the mountain road's trestles, the bell tower, the sleigh run's
# arches and candy canes, the covered bridge, the cabins lit up all over the mountains,
# and the moving parts: snowballs, the sleigh, presents, the bell, baubles, chimney smoke.
# SPDX-License-Identifier: MIT

import math

import course_kit as kit
import hearthglow_props as hp
import props
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

    def box(self, mat, centre, size, rot=0.0, tilt=(0.0, 0.0)):
        k0 = len(self.bm.faces)
        props.cuboid(self.bm, centre, size, rot, tilt)
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


class Scene:
    """What the dressing collects as it goes: warm light points (painted onto the land
    and the buildings), lanterns, chimneys, presents and the strings of lights."""

    def __init__(self):
        self.warm = []
        self.lanterns = []
        self.chimneys = []
        self.houses = []
        self.lights = hp.Lights()


def far_from_road(c, x, y, margin, s_skip=None):
    """No road (other than the stretch s_skip, nor the shortcut) within `margin` of (x, y)."""
    for smp in c.S:
        if s_skip and s_skip[0] <= smp.s <= s_skip[1]:
            continue
        if (smp.p.x - x) ** 2 + (smp.p.y - y) ** 2 < (smp.w / 2 + margin) ** 2:
            return False
    return all((q.p.x - x) ** 2 + (q.p.y - y) ** 2 > (q.w / 2 + margin) ** 2 for q in c.extra_ground + getattr(c, "side_samples", []))


def ground(c, ter, x, y, default=None):
    z = c.ground_z(x, y, ter)
    return default if z is None else z


def game_entity(c, kind, x, y, z, **extra):
    gx, gy, gz = c.game(x, y, z)
    c.entity(kind, x=gx, y=gy, z=gz, **extra)


def dry(hh, x, y, margin=4.0):
    d, hw, _ = hh.water_at(x, y)
    return d > hw + margin


# ------------------------------------------------------------------ the village


def place_house(c, hh, ter, sc, x, y, rot, variant, coll="Village"):
    """A cottage at (x, y) facing `rot` (its front, local -Y, turned that way), with its
    chimney smoke and its windows' warm light."""
    if any((x - hx) ** 2 + (y - hy) ** 2 < 13.0**2 for hx, hy in sc.houses):
        return False
    if math.hypot(x - hh.TREE[0], y - hh.TREE[1]) < 64 or not dry(hh, x, y, 7.0):
        return False
    if not far_from_road(c, x, y, 8.5):
        return False
    z = ground(c, ter, x, y)
    if z is None:
        return False
    c.place(hp.cottage(c, variant), x, y, z - 0.6, rot=rot, coll=coll, role="visual")
    c.place(hp.cottage_block(c, variant), x, y, z - 0.6, rot=rot, coll="Blocks", role="collision")
    sc.houses.append((x, y))
    cx, cy, cz = hp.CHIMNEY[variant % 5]
    ca, sa = math.cos(rot), math.sin(rot)
    sc.chimneys.append((x + cx * ca - cy * sa, y + cx * sa + cy * ca, z - 0.6 + cz))
    sc.warm.append((x, y, z + 3.0))
    return True


def alley(c, hh, ter, sc):
    """The back alley: cottages crowding it on both sides, lanterns on its walls and
    lights strung across it, and a market stall and a pine half hiding its mouth."""
    pts = hh.alley_points()
    k = 0
    for i in range(0, len(pts) - 1, 6):
        x, y, d = pts[i]
        nx, ny = pts[i + 1][0] - x, pts[i + 1][1] - y
        n = math.hypot(nx, ny) or 1.0
        tx, ty = nx / n, ny / n
        rot = math.atan2(ty, tx)
        for side in (-1, 1):
            px, py = x - ty * side * 12.6, y + tx * side * 12.6
            if place_house(c, hh, ter, sc, px, py, rot + (math.pi if side > 0 else 0.0), (k + 3) % 5):
                k += 1
        if 20 < d < hh.ALLEY_LEN - 20 and i % 18 == 0:
            side = 1 if (i // 18) % 2 else -1
            lx, ly = x - ty * side * (hh.ALLEY_W / 2 + 0.9), y + tx * side * (hh.ALLEY_W / 2 + 0.9)
            z = ground(c, ter, lx, ly, 3.0)
            sc.lanterns.append((lx, ly, z + 2.4))
            sc.warm.append((lx, ly, z + 2.0))
            z0 = ground(c, ter, x, y, 3.0)
            sc.lights.line((x - ty * 7.5, y + tx * 7.5, z0 + 6.5), (x + ty * 7.5, y - tx * 7.5, z0 + 6.5), sag=1.0, width=0.35)
    # The mouth, half hidden: a market stall and a pine on the street's edge either side.
    x, y, _ = pts[6]
    tx, ty = pts[7][0] - x, pts[7][1] - y
    n = math.hypot(tx, ty) or 1.0
    tx, ty = tx / n, ty / n
    for side, what in ((-1, "stall"), (1, "pine")):
        px, py = x - ty * side * 8.5 - tx * 6.0, y + tx * side * 8.5 - ty * 6.0
        if not far_from_road(c, px, py, 1.2):
            continue
        z = ground(c, ter, px, py, 3.0)
        if what == "stall":
            c.place(hp.stall(c, 1), px, py, z - 0.1, rot=math.atan2(ty, tx) + math.pi / 2, coll="Village")
        else:
            c.place(hp.xmas_pine(c, 1, 10.0, lights=True), px, py, z - 0.3, coll="Village", role="visual")


def streets(c, hh, ter, sc):
    """Cottages lining the village streets (facing them), a second row behind, and more
    filling the blocks between, so the streets read as streets."""
    S = hh.SEG
    stretches = [
        (8.0, S[1], (-1, 1)),  # the entrance street
        (S[4] - 10, S[5], (-1, 1)),  # to the bridge
        (S[6] + 20, S[9] + 10, (-1, 1)),  # the north lane
        (S[18] + 72, S[27], (-1, 1)),  # the old town, the market chicane and the west lane
        (S[27] + 30, S[29], (-1, 1)),  # the bottom lane
        (S[29] + 30, hh.LENGTH - 2, (-1, 1)),  # the finish street
    ]
    k = 0
    for s0, s1, sides in stretches:
        s = s0
        while s < s1:
            q = c.at(s)
            for side in sides:
                for row, off in enumerate((q.w / 2 + 11.5, q.w / 2 + 26.0)):
                    if row == 1 and int(s / 15) % 2:
                        continue
                    p = q.side(side * off)
                    rot = road_rot(q) + (math.pi if side > 0 else 0.0)
                    if place_house(c, hh, ter, sc, p.x, p.y, rot, (k + row * 2) % 5):
                        k += 1
            s += 15.0 + 3.0 * rnd(s)
    # More filling the blocks, facing whichever way the nearest road runs (a few dozen).
    extra = 0
    for j in range(40):
        for i in range(40):
            if extra >= 45:
                break
            x = -230 + i * 15 + 4 * (rnd(i * 7 + j) - 0.5)
            y = -320 + j * 15 + 4 * (rnd(j * 11 + i) - 0.5)
            if not (-280 < x < 160 and -330 < y < 260):
                continue
            smp, d = c.nearest(x, y)
            if d > 70:
                continue
            rot = road_rot(smp) + (math.pi if (Vector((x, y, 0)) - Vector((smp.p.x, smp.p.y, 0))).dot(smp.r) > 0 else 0.0)
            if place_house(c, hh, ter, sc, x, y, rot + math.pi * (rnd(i + j) < 0.2), (i + j) % 5):
                extra += 1


def street_furniture(c, hh, ter, sc):
    """Lantern posts down both sides of every village street, strings of lights slung
    across them, candy canes and present piles here and there."""
    S = hh.SEG
    post = hp.lantern_post(c)
    village = [(4.0, S[1]), (S[3], S[9]), (S[18] - 10, hh.LENGTH - 4)]
    for s0, s1 in village:
        s = s0
        k = 0
        while s < s1:
            q = c.at(s)
            pts = []
            for side in (-1, 1):
                p = q.side(side * (q.w / 2 + 2.4))
                z = ground(c, ter, p.x, p.y, q.p.z)
                if far_from_road(c, p.x, p.y, 1.0) or abs(z - q.p.z) < 1.5:
                    c.place(post, p.x, p.y, z - 0.1, rot=road_rot(q), coll="Village", role="visual")
                    if k % 2 == 0:
                        sc.lanterns.append((p.x, p.y, z + 4.6))
                    sc.warm.append((p.x, p.y, z + 4.0))
                pts.append(Vector((p.x, p.y, z)))
            if k % 2 == 1:
                a, b = q.side(-(q.w / 2 + 9.0), 8.5), q.side(q.w / 2 + 9.0, 8.5)
                sc.lights.line(a, b, sag=1.6)
            k += 1
            s += 22.0
    cane = hp.candy_cane(c)
    pile = [hp.present_pile(c, v) for v in range(3)]
    for k, s in enumerate(range(20, int(hh.LENGTH), 37)):
        q = c.at(s)
        if hh.seg_of(s) in (5, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18):
            continue
        side = 1 if k % 2 else -1
        p = q.side(side * (q.w / 2 + 3.6))
        z = ground(c, ter, p.x, p.y)
        if z is None or abs(z - q.p.z) > 2.0 or not far_from_road(c, p.x, p.y, 1.5):
            continue
        if k % 3 == 0:
            c.place(pile[k % 3], p.x, p.y, z - 0.1, rot=rnd(k) * 6, coll="Village")
        else:
            c.place(cane, p.x, p.y, z - 0.1, rot=road_rot(q) + (math.pi if side < 0 else 0), coll="Village", role="visual")


def square(c, hh, ter, sc):
    """The village square: the giant tree (lights spiralling up it, a great star, giant
    baubles turning), presents and snowmen at its foot, stalls round the edge, the
    frozen fountain, and strings of lights from the tree to the stalls."""
    tx, ty = hh.TREE
    tz = ground(c, ter, tx, ty, 2.0)
    hp.giant_tree(c, "Giant Christmas Tree", tx, ty, tz - 0.3, 44.0)
    for k in range(10):
        a = k * math.tau / 10 + 0.3
        r = 6.0 + 2.0 * (k % 2)
        c.place(hp.present_pile(c, k % 3), tx + r * math.cos(a), ty + r * math.sin(a), tz - 0.1, rot=a, coll="Village")
    for k in range(4):
        a = k * math.tau / 4 + 0.9
        c.place(hp.snowman(c, k % 3), tx + 20 * math.cos(a), ty + 20 * math.sin(a), tz - 0.2, rot=a + math.pi / 2, coll="Village")
    # Baubles on the tree (moving entities), and its glow.
    cols = ["#e8303a", "#f6c040", "#3a8ae8", "#9a3ad0", "#2eaa4a", "#f07ac0"]
    for k in range(14):
        h = 8 + (k * 2.3) % 26
        r = 13.2 * (1 - (h - 4) / 44 * 0.82) + 0.6
        a = k * 2.4
        game_entity(c, "ornament", tx + r * math.cos(a), ty + r * math.sin(a), tz + h, r=1.4 if k % 3 else 1.9, color=cols[k % len(cols)])
    for h in (6, 18, 30, 42):
        sc.warm.append((tx, ty, tz + h))
    # Houses round the square, facing the tree.
    for k in range(22):
        a = k * math.tau / 22 + 0.1
        for r in (78.0, 90.0):
            if place_house(c, hh, ter, sc, tx + r * math.cos(a), ty + r * math.sin(a), a + math.pi / 2, k % 5):
                break
    # Inside the ring of road: a little market round the tree, lanterns, benches of presents.
    post = hp.lantern_post(c)
    for k in range(8):
        a = k * math.tau / 8 + 0.4
        x, y = tx + 30 * math.cos(a), ty + 30 * math.sin(a)
        if far_from_road(c, x, y, 4.0):
            z = ground(c, ter, x, y, tz)
            c.place(hp.stall(c, k % 2), x, y, z - 0.1, rot=a - math.pi / 2, coll="Village")
            sc.warm.append((x, y, z + 2.5))
        x, y = tx + 37 * math.cos(a + 0.39), ty + 37 * math.sin(a + 0.39)
        if far_from_road(c, x, y, 2.0):
            z = ground(c, ter, x, y, tz)
            c.place(post, x, y, z - 0.1, coll="Village", role="visual")
            sc.lanterns.append((x, y, z + 4.6))
            sc.warm.append((x, y, z + 4.0))
    # Stalls round the edge of the square, facing the tree.
    for k in range(14):
        a = k * math.tau / 14
        for r in (66.0, 74.0):
            x, y = tx + r * math.cos(a), ty + r * math.sin(a)
            if not far_from_road(c, x, y, 5.0) or not dry(hh, x, y):
                continue
            z = ground(c, ter, x, y, tz)
            c.place(hp.stall(c, k % 2), x, y, z - 0.1, rot=a + math.pi / 2, coll="Village")
            sc.warm.append((x, y, z + 2.5))
            break
    # Strings of lights from high on the tree out over the road to posts round the edge.
    pole = hp.lantern_post(c, 1)
    for k in range(8):
        a = k * math.tau / 8 + 0.2
        x, y = tx + 64 * math.cos(a), ty + 64 * math.sin(a)
        if not far_from_road(c, x, y, 2.0):
            x, y = tx + 70 * math.cos(a), ty + 70 * math.sin(a)
        z = ground(c, ter, x, y, tz)
        c.place(pole, x, y, z - 0.1, coll="Village", role="visual")
        sc.lights.line((tx + 4 * math.cos(a), ty + 4 * math.sin(a), tz + 30), (x, y, z + 5.0), sag=3.0, width=0.4)
    # The frozen fountain, at the edge of the square.
    a = 4.1
    fx, fy = tx + 82 * math.cos(a), ty + 82 * math.sin(a)
    if not far_from_road(c, fx, fy, 8.0):
        fx, fy = tx + 92 * math.cos(a), ty + 92 * math.sin(a)
    fz = ground(c, ter, fx, fy, tz)
    fountain(c, fx, fy, fz)
    sc.warm.append((fx, fy, fz + 3))


def fountain(c, x, y, z):
    m = Mesh()
    k0 = len(m.bm.faces)
    rings = [props.ring(m.bm, (x, y), 6.0, z - 0.5, 16), props.ring(m.bm, (x, y), 6.0, z + 1.0, 16), props.ring(m.bm, (x, y), 5.3, z + 1.0, 16), props.ring(m.bm, (x, y), 5.3, z + 0.6, 16)]
    props.loft(m.bm, rings, cap_top=True)
    props.tube(m.bm, [(x, y, z), (x, y, z + 4.5)], [0.9, 0.6], n=8)
    rings = [props.ring(m.bm, (x, y), 2.4, z + 3.6, 12), props.ring(m.bm, (x, y), 2.6, z + 4.0, 12)]
    props.loft(m.bm, rings, cap_top=True)
    m.mark("hearth_stone", k0)
    k0 = len(m.bm.faces)
    for i in range(12):
        a = i * math.tau / 12
        props.tube(m.bm, [(x + 2.4 * math.cos(a), y + 2.4 * math.sin(a), z + 3.7), (x + 4.0 * math.cos(a), y + 4.0 * math.sin(a), z + 2.5), (x + 4.7 * math.cos(a), y + 4.7 * math.sin(a), z + 0.8)], [0.35, 0.3, 0.2], n=4)
    props.blob(m.bm, (x, y, z + 5.1), 0.9, sz=1.6, subdiv=1)
    m.mark("river_ice", k0)
    m.build(c, "Frozen Fountain", "Village", "both")


# ------------------------------------------------------------------ bridges


def stone_bridge(c, hh, ter, sc):
    """Arches and piers under the stone bridge, icicles along its sides, lamps on it."""
    for p in c.pieces:
        if "stonebridge" not in p.name:
            continue
        s0, s1 = p["kp_from"], p["kp_to"]
        m = Mesh()
        n = 3
        for j in range(n + 1):
            q = c.at(s0 + (s1 - s0) * j / n)
            if j not in (0, n):
                k0 = len(m.bm.faces)
                props.cuboid(m.bm, (q.p.x, q.p.y, (q.p.z - 4.0 + hh.RIVER_Z - 2) / 2), (q.w + 2.0, 4.5, q.p.z - 4.0 - hh.RIVER_Z + 2), rot=road_rot(q) + math.pi / 2)
                m.mark("hearth_stone", k0)
            for side in (-1, 1):
                e = q.side(side * (q.w / 2 + 1.0), 1.4)
                if j in (1, 2):
                    c.place(hp.lantern_post(c), e.x, e.y, e.z - 0.2, coll="Bridges", role="visual")
                    sc.lanterns.append((e.x, e.y, e.z + 4.4))
                    sc.warm.append((e.x, e.y, e.z + 4.0))
        k0 = len(m.bm.faces)
        s = s0
        while s < s1:
            q = c.at(s)
            for side in (-1, 1):
                e = q.side(side * (q.w / 2 + 1.2), -3.9)
                for i in range(3):
                    ln = 1.2 + 1.6 * rnd(s * 3 + i + side)
                    res = bmesh.ops.create_cone(m.bm, cap_ends=False, segments=4, radius1=0.0, radius2=0.15, depth=ln)
                    for v in res["verts"]:
                        v.co += e + q.t * (i - 1) * 0.9 + Vector((0, 0, -ln / 2))
            s += 2.5
        m.mark("icefall_blue", k0)
        m.build(c, p.name + " Arches", "Bridges", "both")


def covered_bridge(c, hh, sc):
    """The covered bridge: timber posts down both sides with crossed braces, a snowy
    gabled roof, lanterns hanging inside, lights along the eaves, wreaths on the portals."""
    for p in c.pieces:
        if "covered" not in p.name:
            continue
        s0, s1 = p["kp_from"], p["kp_to"]
        m = Mesh()
        H = 7.0
        s = s0
        k = 0
        while s <= s1 + 0.1:
            q = c.at(s)
            half = q.w / 2 + 1.4
            for side in (-1, 1):
                b = q.side(side * half)
                m.box("timber_beam", (b.x, b.y, b.z + H / 2), (0.6, 0.6, H), rot=road_rot(q))
            # A tie beam across, and a lantern under it.
            m.box("timber_beam", (q.p.x, q.p.y, q.p.z + H + 0.3), (0.5, 2 * half + 0.6, 0.5), rot=road_rot(q))
            if k % 2 == 0:
                m.box("lantern_glow", (q.p.x, q.p.y, q.p.z + H - 0.9), (0.6, 0.6, 0.9), rot=road_rot(q))
                sc.lanterns.append((q.p.x, q.p.y, q.p.z + H - 0.9))
                sc.warm.append((q.p.x, q.p.y, q.p.z + H - 1.5))
            k += 1
            s += 5.0
        # Braces and the roof, segment by segment.
        s = s0
        while s < s1:
            q, r = c.at(s), c.at(min(s1, s + 5.0))
            half = q.w / 2 + 1.4
            for side in (-1, 1):
                a, b = q.side(side * half), r.side(side * half)
                k0 = len(m.bm.faces)
                props.tube(m.bm, [(a.x, a.y, a.z + 0.3), (b.x, b.y, b.z + H * 0.55)], 0.18, n=4)
                props.tube(m.bm, [(a.x, a.y, a.z + H * 0.55), (b.x, b.y, b.z + 0.3)], 0.18, n=4)
                props.tube(m.bm, [(a.x, a.y, a.z + H * 0.6), (b.x, b.y, b.z + H * 0.6)], 0.2, n=4)
                m.mark("timber_beam", k0)
                # The roof: a slope each side, deep in snow, the planks showing beneath.
                ea, eb = q.side(side * (half + 1.2), H - 0.2), r.side(side * (half + 1.2), H - 0.2)
                ra, rb = q.p + Vector((0, 0, H + 4.0)), r.p + Vector((0, 0, H + 4.0))
                k0 = len(m.bm.faces)
                vs = [m.bm.verts.new(v) for v in (ea, eb, rb + Vector((0, 0, 0.1)), ra + Vector((0, 0, 0.1)))]
                m.bm.faces.new(vs if side < 0 else list(reversed(vs)))
                m.mark("summit_snow", k0)
                k0 = len(m.bm.faces)
                vs = [m.bm.verts.new(v - Vector((0, 0, 0.35))) for v in (ea, eb, rb, ra)]
                m.bm.faces.new(list(reversed(vs)) if side < 0 else vs)
                m.mark("cabin_wall", k0)
                sc.lights.line(ea - Vector((0, 0, 0.5)), eb - Vector((0, 0, 0.5)), sag=0.0, width=0.3)
            s += 5.0
        # Gable ends over the portals, with wreaths.
        for s_, out in ((s0, -1), (s1, 1)):
            q = c.at(s_)
            half = q.w / 2 + 2.6
            a, b, top = q.side(-half, H - 0.2), q.side(half, H - 0.2), q.p + Vector((0, 0, H + 4.0))
            k0 = len(m.bm.faces)
            vs = [m.bm.verts.new(v) for v in (a, b, top)]
            m.bm.faces.new(vs if out > 0 else list(reversed(vs)))
            m.mark("cabin_wall", k0)
            k0 = len(m.bm.faces)
            w = q.p + q.t * out * 0.3 + Vector((0, 0, H + 1.3))
            for i in range(8):
                ang = i * math.tau / 8
                props.blob(m.bm, tuple(w + q.r * 1.2 * math.cos(ang) + Vector((0, 0, 1.2 * math.sin(ang)))), 0.5, subdiv=0)
            m.mark("wreath", k0)
        m.build(c, "Covered Bridge", "Bridges", "both")


def trestles(c, hh, ter):
    """Timber trestle bents under the mountain road's raised stretches and the jump ramps:
    two legs down to the ground, cross-braced."""
    m = Mesh()
    for p in c.pieces:
        if "trestle" not in p.name and "ramp" not in p.name:
            continue
        s0, s1 = p["kp_from"], p["kp_to"]
        s = s0 + 3
        while s < s1 - 2:
            q = c.at(s)
            legs = []
            for side in (-1, 1):
                b = q.side(side * (q.w / 2 - 0.5))
                gz = ground(c, ter, b.x, b.y)
                gz = (b.z - 30) if gz is None else gz
                if b.z - 2.0 - gz < 1.5:
                    continue
                k0 = len(m.bm.faces)
                props.cuboid(m.bm, (b.x, b.y, (b.z - 2.0 + gz - 1) / 2), (0.9, 0.9, b.z - 2.0 - gz + 1), rot=road_rot(q))
                m.mark("timber_beam", k0)
                legs.append((b, gz))
            if len(legs) == 2:
                (a, ga), (b, gb) = legs
                lo = max(ga, gb) + 1.0
                k0 = len(m.bm.faces)
                props.tube(m.bm, [(a.x, a.y, a.z - 2.2), (b.x, b.y, lo)], 0.22, n=4)
                props.tube(m.bm, [(b.x, b.y, b.z - 2.2), (a.x, a.y, lo)], 0.22, n=4)
                m.mark("timber_beam", k0)
            s += 7.0
    m.build(c, "Trestles", "Bridges", "both")


# ------------------------------------------------------------------ the forest and the mountain


def forest(c, hh, ter, sc):
    """The enchanted forest and the pines all over the valley: snow-laden pines, some
    strung with lights, log cabins with glowing windows, logs, lanterns and lights."""
    plain = [hp.xmas_pine(c, v, 13.0 + 4 * v, lights=False) for v in range(3)]
    lit = [hp.xmas_pine(c, v, 12.0 + 3 * v, lights=True) for v in range(2)]

    def ok(x, y, z):
        return far_from_road(c, x, y, 5.0) and dry(hh, x, y, 3.0) and all((x - hx) ** 2 + (y - hy) ** 2 > 81 for hx, hy in sc.houses)

    fz = (-420, 40, 200, 560)
    for v in range(3):
        props.scatter(c, plain[v], 50, fz, ok, ter, seed=10 + v, scale=(0.9, 1.7), coll="Forest", role="visual")
    for v in range(2):
        props.scatter(c, lit[v], 22, (-340, -60, 220, 440), lambda x, y, z: ok(x, y, z) and not far_from_road(c, x, y, 16.0), ter, seed=20 + v, scale=(1.0, 1.4), coll="Forest", role="visual")
    # Pines on the mountainsides all round, and a few lit ones round the village.
    lo = [hp.pine_lo(c, v, 14.0 + 4 * v) for v in range(3)]
    for v in range(3):
        props.scatter(c, lo[v], 45, (-600, 500, -440, 700), lambda x, y, z: ok(x, y, z) and z > 8, ter, seed=30 + v, scale=(0.8, 1.6), coll="Pines", role="visual")
    props.scatter(c, lit[0], 26, (-250, 150, -320, 220), lambda x, y, z: ok(x, y, z) and math.hypot(x - hh.TREE[0], y - hh.TREE[1]) > 30, ter, seed=40, scale=(0.8, 1.2), coll="Pines", role="visual")
    # Log cabins in the forest, with lanterns by the road.
    for k, (s, off) in enumerate(((hh.SEG[9] + 25, 26), (hh.SEG[10] + 15, -26), (hh.SEG[11] + 15, 26), (hh.SEG[12] + 10, -25), (hh.SEG[14] + 50, 28))):
        q = c.at(s)
        p = q.side(off)
        place_house(c, hh, ter, sc, p.x, p.y, road_rot(q) + (math.pi if off > 0 else 0.0), 1, coll="Forest")
    post = hp.lantern_post(c)
    s = hh.SEG[8]
    k = 0
    while s < hh.SEG[12]:
        q = c.at(s)
        side = 1 if k % 2 else -1
        p = q.side(side * (q.w / 2 + 2.6))
        z = ground(c, ter, p.x, p.y, q.p.z)
        c.place(post, p.x, p.y, z - 0.1, rot=road_rot(q), coll="Forest", role="visual")
        sc.lanterns.append((p.x, p.y, z + 4.6))
        sc.warm.append((p.x, p.y, z + 4.0))
        if k % 3 == 1:
            sc.lights.line(q.side(-(q.w / 2 + 8), 9.0), q.side(q.w / 2 + 8, 9.0), sag=2.0)
        k += 1
        s += 26.0
    for k in range(10):
        s = hh.SEG[8] + 25 * k
        q = c.at(s)
        p = q.side((1 if k % 2 else -1) * (q.w / 2 + 9))
        z = ground(c, ter, p.x, p.y)
        if z is not None and far_from_road(c, p.x, p.y, 3.0):
            c.place(hp.log(c, k % 2), p.x, p.y, z - 0.2, rot=road_rot(q) + 0.4 * (rnd(k) - 0.5), coll="Forest")


def mountain(c, hh, ter, sc):
    """The bell tower at the summit (its bell is an entity), lanterns along the mountain
    road, and lit cabins all over the mountains round the valley."""
    sx, sy = hh.SUMMIT
    sz = ground(c, ter, sx, sy, 50.0)
    c.place(hp.bell_tower(c), sx, sy, sz - 0.5, rot=-0.6, coll="Village")
    gx, gy, gz = c.game(sx, sy, sz - 0.5 + 19.6)
    c.entity("bell", x=gx, y=gy, z=gz, heading=0.6, period=14.0, offset=3.0, ring=3.4, scale=1.1)
    for h in (9, 19):
        sc.warm.append((sx, sy, sz + h))
    post = hp.lantern_post(c)
    s = hh.SEG[9]
    k = 0
    while s < hh.SEG[14] + 20:
        q = c.at(s)
        p = q.side(q.w / 2 + 1.0, 1.0)
        c.place(post, p.x, p.y, p.z - 1.1, rot=road_rot(q), coll="Mountain", role="visual")
        if k % 2 == 0:
            sc.lanterns.append((p.x, p.y, p.z + 3.5))
        sc.warm.append((p.x, p.y, p.z + 3.0))
        k += 1
        s += 30.0
    # Lit cabins scattered over the mountains (far off: the settlement goes on and on).
    k = 0
    for i in range(400):
        x = -600 + 1100 * rnd(i * 1.7 + 0.3)
        y = -440 + 1140 * rnd(i * 2.9 + 0.7)
        smp, d = c.nearest(x, y)
        if d < 90:
            continue
        z = c.ground_z(x, y, ter)
        if z is None or z < 30 or z > 200:
            continue
        if any((x - hx) ** 2 + (y - hy) ** 2 < 30**2 for hx, hy in sc.houses):
            continue
        c.place(hp.cottage(c, k % 5), x, y, z - 1.0, rot=math.atan2(-y, -x) + math.pi / 2, scale=1.1, coll="Distant", role="visual")
        sc.houses.append((x, y))
        k += 1
        if k >= 34:
            break


def hamlets(c, hh, ter, sc):
    """Little clusters of lit cottages round the valley (the settlement goes on beyond
    the track), with lit pines, lights strung between them and pines round about."""
    lit = hp.xmas_pine(c, 0, 12.0, lights=True)
    plain = [hp.xmas_pine(c, v, 13.0 + 4 * v, lights=False) for v in range(3)]
    for h, (hx, hy) in enumerate(((170.0, 240.0), (300.0, 70.0), (120.0, -280.0), (260.0, -180.0), (-470.0, -260.0), (200.0, 430.0), (-180.0, -380.0), (420.0, 300.0))):
        placed = []
        for k in range(9):
            a = k * 2.4 + h
            r = 0.0 if k == 0 else 14.0 + 7.0 * (k % 3)
            x, y = hx + r * math.cos(a), hy + r * math.sin(a)
            if place_house(c, hh, ter, sc, x, y, a + math.pi / 2 + 0.3 * rnd(k + h), (k + h) % 5, coll="Distant"):
                placed.append((x, y))
        for (x0, y0), (x1, y1) in zip(placed, placed[1:]):
            z0, z1 = ground(c, ter, x0, y0, 5.0), ground(c, ter, x1, y1, 5.0)
            sc.lights.line((x0, y0, z0 + 7.0), (x1, y1, z1 + 7.0), sag=1.5)
        for k in range(5):
            a = k * 1.3 + h
            x, y = hx + 30 * math.cos(a), hy + 30 * math.sin(a)
            z = c.ground_z(x, y, ter)
            if z is not None and far_from_road(c, x, y, 6.0) and dry(hh, x, y):
                c.place(lit if k % 2 == 0 else plain[k % 3], x, y, z - 0.3, scale=1.0 + 0.3 * rnd(k + h), coll="Distant", role="visual")
    # Pine woods filling the open snow east and south of the village.
    def ok(x, y, z):
        return far_from_road(c, x, y, 8.0) and dry(hh, x, y, 4.0) and all((x - hx) ** 2 + (y - hy) ** 2 > 144 for hx, hy in sc.houses)

    lo = [hp.pine_lo(c, v, 14.0 + 4 * v) for v in range(3)]
    for v in range(3):
        props.scatter(c, lo[v], 55, (40, 500, -440, 560), ok, ter, seed=50 + v, scale=(0.9, 1.7), coll="Pines", role="visual")
        props.scatter(c, lo[v], 30, (-600, 40, -440, -150), ok, ter, seed=60 + v, scale=(0.9, 1.7), coll="Pines", role="visual")


def sleigh_run(c, hh, ter, sc):
    """Decorated arches over the sleigh run, candy canes down its edges, the sleigh's
    crossing, and the jumps' snow banks."""
    S = hh.SEG
    for k, s in enumerate((S[14] + 8, S[15] + 18, S[17] + 30)):
        q = c.at(s)
        c.place(hp.xmas_arch(c, q.w + 6.0, 9.0, False, k % 2), q.p.x, q.p.y, q.p.z - 0.3, rot=road_rot(q) + math.pi / 2, coll="Mountain")
        sc.warm.append((q.p.x, q.p.y, q.p.z + 8))
    cane = hp.candy_cane(c, 6.0)
    s = S[14]
    k = 0
    while s < S[18]:
        if not any(lip - 6 < s < land + 6 for lip, land in hh.JUMPS):
            q = c.at(s)
            side = 1 if k % 2 else -1
            p = q.side(side * (q.w / 2 + 2.4))
            z = ground(c, ter, p.x, p.y, q.p.z)
            c.place(cane, p.x, p.y, z - 0.2, rot=road_rot(q) + (math.pi if side < 0 else 0), coll="Mountain", role="visual")
        k += 1
        s += 14.0


# ------------------------------------------------------------------ water


def waters(c, hh, ter, sc):
    """Open, flowing water down the middle of the river where it's only partly frozen,
    the falls where the river and the creek come down from the mountains, and frozen
    falls on the cliffs all round."""
    for name, a, b in (("River Flow North", 1, 4), ("River Flow South", 9, 12)):
        pts = []
        for (x0, y0), (x1, y1) in zip(hh.RIVER[a - 1 : b], hh.RIVER[a:b]):
            n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 8))
            for k in range(n):
                t = k / n
                pts.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 7.0 + 2.0 * math.sin(k * 0.7), hh.RIVER_Z + 0.08))
        c.ribbon(name, pts, 7.0, hh.RIVER_Z + 0.08, c.lib("frost_falls"), coll="Water", role="visual", steps=2)
    import winter_props as wp

    for k, (x, y, top, foot, w, face) in enumerate((
        (285.0, 540.0, 60.0, 8.0, 26.0, (-0.4, -0.9)),
        (-430.0, 600.0, 70.0, 12.0, 18.0, (0.0, -1.0)),
        (-520.0, 200.0, 70.0, 20.0, 22.0, (1.0, 0.0)),
        (-500.0, -100.0, 60.0, 8.0, 20.0, (1.0, 0.0)),
        (380.0, 100.0, 60.0, 6.0, 22.0, (-1.0, 0.0)),
        (100.0, 640.0, 80.0, 30.0, 30.0, (0.0, -1.0)),
    )):
        z = ground(c, ter, x, y)
        if z is None:
            continue
        wp.ice_fall(c, "Icefall %d" % k, x, y, z + top * 0.6, z - 2.0, w, facing=face, coll="Water")
        sc.warm.append((x, y, z))


# ------------------------------------------------------------------ build


def build(c, hh):
    ter = list(c.coll("Terrain").objects)
    sc = Scene()
    S = hh.SEG

    # The start: a great wooden Christmas arch with a checkered banner, and more out of the
    # square, into the old town and down the west lane.
    for s, chk in ((0.0, True), (S[3] + 30, False), (S[19] + 8, False), (S[26] + 50, False)):
        q = c.at(s)
        c.place(hp.xmas_arch(c, q.w + 8.0, 11.0, chk, 0), q.p.x, q.p.y, q.p.z - 0.3, rot=road_rot(q) + math.pi / 2, coll="Village")
        sc.warm.append((q.p.x, q.p.y, q.p.z + 10))
    square(c, hh, ter, sc)
    alley(c, hh, ter, sc)
    streets(c, hh, ter, sc)
    street_furniture(c, hh, ter, sc)
    stone_bridge(c, hh, ter, sc)
    covered_bridge(c, hh, sc)
    trestles(c, hh, ter)
    forest(c, hh, ter, sc)
    mountain(c, hh, ter, sc)
    hamlets(c, hh, ter, sc)
    sleigh_run(c, hh, ter, sc)
    waters(c, hh, ter, sc)
    sc.lights.build(c)

    # Moving parts. Snowballs roll across the forest road, downhill, two at each crossing
    # (one 3.5 s after the other).
    for k, s in enumerate((S[8] + 12, S[12] + 10)):
        q = c.at(s)
        a, b = q.side(-34.0), q.side(34.0)
        za, zb = hh.natural(a.x, a.y), hh.natural(b.x, b.y)
        if za < zb:
            a, b, za, zb = b, a, zb, za
        for j in range(2):
            ax, ay, az = c.game(a.x, a.y, za)
            bx, by, bz = c.game(b.x, b.y, zb)
            c.entity("snowball", ax=ax, ay=ay, az=az, bx=bx, by=by, bz=bz, r=2.6 - 0.5 * j, period=8.0, offset=1.5 + k * 2.7 + j * 4.0, travel=4.2)
    # The sleigh: across the sleigh run, from the creek side into the woods, every 13 s.
    q = c.at(hh.SEG[17] + 30)
    a, b = q.side(48.0), q.side(-48.0)
    ax, ay, az = c.game(a.x, a.y, hh.natural(a.x, a.y))
    bx, by, bz = c.game(b.x, b.y, hh.natural(b.x, b.y))
    c.entity("sleigh", ax=ax, ay=ay, az=az, bx=bx, by=by, bz=bz, period=13.0, offset=4.0, travel=5.5, warn=2.5)
    for side in (-1, 1):
        p = q.side(side * (q.w / 2 + 3.0))
        z = ground(c, ter, p.x, p.y, q.p.z)
        c.place(hp.candy_cane(c, 8.0), p.x, p.y, z - 0.2, rot=road_rot(q), scale=1.2, coll="Mountain", role="visual")
        c.place(hp.lantern_post(c), p.x + q.t.x * 3, p.y + q.t.y * 3, z - 0.2, coll="Mountain", role="visual")
        sc.lanterns.append((p.x, p.y, z + 4.6))
    # Presents by the road (smash them: they come back, and boost you), where a boost is
    # worth having: out of the slow corners, on one side of the road or the other, and
    # never in a zipper's boost or just before one.
    spots = [(30.0, 1), (S[2] + 35, -1), (S[2] + 85, 1), (S[10] + 20, 1), (S[12] + 10, -1), (S[13] + 70, -1), (S[15] + 10, 1),
             (S[19] + 20, -1), (S[21] + 20, 1), (S[24] + 25, -1), (S[27] + 40, 1), (S[29] + 40, -1)]
    spots = [(s, side) for s, side in spots if not any(-25 <= s - z <= 90 for z in hh.ZIPPERS)]
    for k, (s, side) in enumerate(spots):
        q = c.at(s)
        p = q.side(side * (q.w / 2 + 0.9))
        game_entity(c, "present", p.x, p.y, q.p.z, size=2.2 + 0.4 * (k % 3), variant=k, heading=round(road_rot(q), 3))
    # And one in the back alley, before the dogleg.
    pts = hh.alley_points()
    i = next(k for k, p in enumerate(pts) if p[2] >= 110)
    x, y, _ = pts[i]
    tx, ty = pts[i + 1][0] - x, pts[i + 1][1] - y
    n = math.hypot(tx, ty) or 1.0
    px, py = x + ty / n * (hh.ALLEY_W / 2 - 1.4), y - tx / n * (hh.ALLEY_W / 2 - 1.4)
    game_entity(c, "present", px, py, ground(c, ter, px, py, 3.0), size=2.0, variant=len(spots), heading=round(math.atan2(ty, tx), 3))
    # Lanterns (the nearest light the scene), chimney smoke, falling snow.
    for x, y, z in sc.lanterns:
        game_entity(c, "lantern", x, y, z)
    for x, y, z in sc.chimneys[:90]:
        game_entity(c, "chimney", x, y, z)
    c.entity("snowfall", rate=60, radius=40)

    # Joined copies (far fewer draw calls), then the warm light of windows, lanterns and
    # lights painted on the snow, the streets and the houses.
    groups = ("Village", "Forest", "Pines", "Mountain", "Bridges", "Distant", "Water", "Blocks")
    c.merge_props(groups)
    joined = [o for name in groups for o in c.coll(name).objects if o.type == "MESH" and o.data.users == 1]
    c.glow(ter + joined, sc.warm, 22.0, (1.5, 1.15, 0.7), base=(0.84, 0.86, 1.0))
