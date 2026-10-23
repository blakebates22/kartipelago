# Frostveil Citadel's scenery (see frostveil_citadel.py): the Great Gate, the Bridge of
# Giants and its piers, the Serpent Gate and its torchlit tunnel, the courtyard, the
# temple and the sun disk, the labyrinth's walls and arches, the high causeway, frozen
# and flowing waterfalls, fog in the chasms, the lower town, the fortress on the
# mountains, the far peaks, snowy palms and conifers, and the firelight on it all.
# SPDX-License-Identifier: MIT

import math

import course_kit as kit
import props
import winter_props as wp
from course_kit import Vector, bmesh, rnd
from winter_props import CARVED, DARK, GLOW, STONE, Blocks

FROST_FALLS = ("frost_falls", "frost_falls", "frost_pool")


def clear_of_other(c, x, y, s_lo, s_hi, margin):
    """No road other than the stretch s_lo..s_hi passes within `margin` of (x, y)."""
    for smp in c.S:
        if s_lo <= smp.s <= s_hi:
            continue
        if (smp.p.x - x) ** 2 + (smp.p.y - y) ** 2 < (smp.w / 2 + margin) ** 2:
            return False
    return True


def road_rot(q):
    return math.atan2(q.t.y, q.t.x)


class Lights:
    """Every flame on the course: torch entities for the runtime light, and the points
    the baked firelight is painted round."""

    def __init__(self):
        self.points = []

    def add(self, p):
        self.points.append(tuple(p))


# ------------------------------------------------------------------ pieces along roads


def place_arch(c, s, extra, height, variant=0, coll="Citadel"):
    """An arch over the road at s, widened until neither pier stands on any road (on a
    bend, the road swings out under a straight arch)."""
    q = c.at(s)
    for widen in range(0, 14, 2):
        span = q.w + extra + widen
        ok = all(props.clear_of_road(c, *tuple(q.side(side * (span / 2 + 2.0)))[:2], 3.0) for side in (-1, 1))
        if ok:
            c.place(wp.arch(c, span, height, variant), q.p.x, q.p.y, q.p.z - 0.4, rot=road_rot(q) + math.pi / 2, coll=coll)
            return span
    return None


def braziers_along(c, cc, lights, s0, s1, every, offset, up=0.0, variant=0, alternate=True, skip=None):
    """Braziers beside the road from s0 to s1 (alternating sides), lights included."""
    proto = wp.brazier(c, variant)
    k = 0
    s = s0
    while s < s1:
        q = c.at(s)
        sides = [1 if k % 2 else -1] if alternate else [-1, 1]
        for side in sides:
            p = q.side(side * (q.w / 2 + offset), up)
            if skip and skip(p):
                continue
            c.place(proto, p.x, p.y, p.z - 0.1, rot=road_rot(q), coll="Fire", role="both")
            lights.add((p.x, p.y, p.z + (5.8 if variant else 2.8)))
        s += every
        k += 1


def great_gate(c, cc, lights, s):
    """The Forgotten Entrance: a monumental arch over the start road, two giant carved
    dinosaur heads on plinths either side snarling down the valley, banners and braziers."""
    q = c.at(s)
    rot = road_rot(q)
    span = place_arch(c, s, 8.0, 15.0, 1) or q.w + 8.0
    head = wp.dino_head(c, 1)
    for side in (-1, 1):
        p = q.side(side * (span / 2 + 13.0))
        z = c.ground_z(p.x, p.y, list(c.coll("Terrain").objects)) or q.p.z
        k = Blocks()
        k.box(STONE, (p.x, p.y, z + 3.0), (11.0, 11.0, 6.0), rot=rot)
        k.box(CARVED, (p.x, p.y, z + 6.6), (12.0, 12.0, 1.2), rot=rot)
        k.build(c, "Gate Plinth %d" % (side + 2))
        # The heads face back down the valley, at whoever's coming.
        c.place(head, p.x - q.t.x * 3, p.y - q.t.y * 3, z + 7.0, rot=rot + math.pi, scale=1.0, coll="Citadel")
        for f in (-1, 1):
            b = p + q.t * (f * 7.5)
            c.place(wp.brazier(c, 1), b.x, b.y, z + 7.2, rot=rot, coll="Fire")
            lights.add((b.x, b.y, z + 7.2 + 5.8))
        bp = q.side(side * (span / 2 + 3.5)) - q.t * 4.0
        c.place(wp.banner_pole(c, 0), bp.x, bp.y, bp.z, rot=rot, coll="Citadel", role="visual")
    for off in (-12.0, 12.0):
        p = q.p - q.t * 6.0
        c.place(wp.hanging_banner(c, 0, 8.0), p.x + q.r.x * off, p.y + q.r.y * off, q.p.z + 15.2, rot=rot - math.pi / 2 + math.pi, coll="Citadel", role="visual")


def pillars_along(c, s0, s1, every, offset, side, variant=0, height=6.0):
    """Carved pillars along one side of the road (every fourth one broken)."""
    s = s0
    k = 0
    while s < s1:
        q = c.at(s)
        p = q.side(side * (q.w / 2 + offset))
        proto = wp.carved_pillar(c, 2 if k % 4 == 3 else variant, height)
        c.place(proto, p.x, p.y, p.z - 0.2, rot=road_rot(q), coll="Citadel")
        s += every
        k += 1


# ------------------------------------------------------------------ bridges


def bridge_piers(c, cc, lights, s0, s1, every, name, deck=4.4, faces=True, bannered=True):
    """Under an elevated stretch: massive stepped piers down to whatever is below (never on
    another road), arches springing between them, carved creature faces on the piers,
    banners hanging off the parapets, and braziers on parapet pillars."""
    ter = list(c.coll("Terrain").objects)
    k = Blocks()
    piers = []
    n = max(1, int((s1 - s0) / every))
    head = wp.dino_head(c, 0)
    for i in range(1, n):
        s = s0 + (s1 - s0) * i / n
        q = c.at(s)
        ground = c.ground_z(q.p.x, q.p.y, ter)
        if ground is None:
            ground = cc.CHASM_FLOOR
        top = q.p.z - deck
        if top - ground < 4.0 or not clear_of_other(c, q.p.x, q.p.y, s - 40, s + 40, 10.0):
            continue
        rot = road_rot(q)
        w = q.w + 4.0
        tiers = 3
        span = top - (ground - 3.0)
        for t in range(tiers):
            z0 = ground - 3.0 + span * t / tiers
            h = span / tiers
            grow = (tiers - t - 1) * 2.4
            k.box(STONE, (q.p.x, q.p.y, z0 + h / 2), (7.0 + grow, w + grow, h), rot=rot, snow=t < tiers - 1)
        k.box(CARVED, (q.p.x, q.p.y, top - 1.2), (8.0, w + 1.2, 2.4), rot=rot, snow=False)
        piers.append((s, q, ground))
        if faces:
            # A creature's face on each side of the pier, under the deck.
            for side in (-1, 1):
                p = q.side(side * (w / 2 + 0.5))
                c.place(head, p.x, p.y, top - 10.5, rot=math.atan2(q.r.y * side, q.r.x * side), scale=0.5, coll="Bridges", role="visual")
    # Arches: a ring of stones from pier to pier, its crown under the deck.
    for (sa, qa, ga), (sb, qb, gb) in zip(piers, piers[1:]):
        half = (sb - sa) / 2
        rot = road_rot(qa)
        crown = min(qa.p.z, qb.p.z) - deck
        r = min(half - 3.0, crown - max(ga, gb) - 2.0)
        if r < 4:
            continue
        mid = c.at((sa + sb) / 2)
        for j in range(13):
            a = math.pi * j / 12
            along = -math.cos(a) * r
            z = crown - r + math.sin(a) * r
            p = mid.p + mid.t * along
            k.box(STONE if j % 2 else CARVED, (p.x, p.y, z - 0.6), (2.6, q.w + 3.0, 1.8), rot=rot, snow=False)
        # Spandrel walls between the ring and the deck, hiding the gap.
        for f in (-0.75, 0.75):
            p = mid.p + mid.t * (f * r)
            hgt = crown - (crown - r + math.sqrt(max(0.0, r * r - (f * r) ** 2)))
            if hgt > 0.5:
                k.box(STONE, (p.x, p.y, crown - hgt / 2), (r * 0.5, q.w + 2.0, hgt + 0.4), rot=rot, snow=False)
    if k.groups:
        k.build(c, name + " Piers", "Bridges")
    # Parapet pillars with braziers, and banners hanging over the sides.
    banner = [wp.hanging_banner(c, v, 7.0) for v in range(3)]
    pillar = Blocks()
    s = s0 + 6.0
    j = 0
    brz = wp.brazier(c, 0)
    while s < s1 - 4.0:
        q = c.at(s)
        rot = road_rot(q)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 1.6), 0.0)
            pillar.box(CARVED, (p.x, p.y, p.z + 1.4), (2.0, 2.0, 2.8), rot=rot)
            if (j + (side > 0)) % 2 == 0:
                c.place(brz, p.x, p.y, p.z + 2.8, rot=rot, coll="Fire", role="visual")
                lights.add((p.x, p.y, p.z + 5.6))
            if bannered and j % 2 == 1:
                b = q.side(side * (q.w / 2 + 2.7), -0.4)
                c.place(banner[(j // 2 + (side > 0)) % 3], b.x, b.y, b.z + 0.8, rot=math.atan2(q.r.y * side, q.r.x * side) - math.pi / 2, coll="Bridges", role="visual")
        s += 16.0
        j += 1
    pillar.build(c, name + " Parapet", "Bridges")


# ------------------------------------------------------------------ the serpent gate


def serpent_gate(c, cc, lights, s):
    """The giant serpent head carved into the cliff, its open mouth the tunnel's mouth:
    a great upper jaw over the road with fangs, glowing eyes under heavy brows, a lower
    jaw at road level lined with teeth, and solid cheeks either side."""
    q = c.at(s)
    rot = road_rot(q)
    fwd, right = q.t, q.r
    base = q.p.z

    def at(x, y, z):
        p = q.p + fwd * x + right * y
        return (p.x, p.y, base + z)

    k = Blocks()
    # The head: a great wedge over the mouth, the snout jutting out over the road.
    k.box(STONE, at(-2, 0, 22.0), (26.0, 56.0, 16.0), rot=rot)
    k.box(CARVED, at(-16, 0, 16.5), (12.0, 40.0, 7.0), rot=rot, snow=False)  # upper snout
    k.box(STONE, at(-20, 0, 21.2), (8.0, 30.0, 3.0), rot=rot)  # snout ridge
    k.box(CARVED, at(-2, 0, 31.5), (22.0, 44.0, 3.0), rot=rot, snow=False)  # scaled crown
    for side in (-1, 1):
        k.box(STONE, at(-8, side * 16, 32.5), (10.0, 11.0, 4.0), rot=rot)  # brow
        k.box(DARK, at(-15.2, side * 16, 27.0), (0.6, 9.0, 6.0), rot=rot, snow=False)  # socket
        k.box(GLOW, at(-15.6, side * 16, 27.0), (0.5, 6.0, 3.6), rot=rot, snow=False)  # eye
        k.box(DARK, at(-24.1, side * 6, 19.0), (0.4, 3.0, 1.8), rot=rot, snow=False)  # nostril
        k.box(STONE, at(-4, side * 21.5, 7.5), (20.0, 12.0, 15.0), rot=rot)  # cheek
        k.box(CARVED, at(-13, side * 17.0, 1.2), (18.0, 8.0, 2.4), rot=rot)  # lower jaw
        # Frills sweeping back from the cheeks, and scaly plates over the crown.
        for j in range(4):
            k.box(STONE, at(4 + j * 5.0, side * (29 + j * 2.0), 20.0 + j * 3.0), (5.0, 4.0, 18.0 - j * 2.5), rot=rot)
            k.box(CARVED, at(2 + j * 5.5, side * (8 + j * 3.5), 36.0 + j * 2.5), (4.5, 4.5, 6.0), rot=rot)
    # The serpent's coils, rising over the rock behind its head.
    for j in range(6):
        cx_ = 18 + j * 11
        k.box(STONE, at(cx_, 8 * math.sin(j * 1.3), 40.0 + 6 * math.sin(j * 0.9)), (12.0, 16.0, 9.0), rot=rot + 0.2 * math.sin(j))
        k.box(CARVED, at(cx_, 8 * math.sin(j * 1.3), 45.6 + 6 * math.sin(j * 0.9)), (8.0, 10.0, 2.4), rot=rot + 0.2 * math.sin(j), snow=False)

    def fangs(bm):
        for side in (-1, 1):
            for j, (y, ln) in enumerate(((5.0, 5.0), (9.5, 6.5), (14.5, 11.5))):
                res = bmesh.ops.create_cone(bm, cap_ends=True, segments=5, radius1=0.0, radius2=1.2 + 0.4 * j, depth=ln)
                for v in res["verts"]:
                    p = Vector(at(-21.0, side * y, 13.0 - ln / 2)) + Vector((0, 0, v.co.z))
                    v.co = p + fwd * v.co.x + right * v.co.y
            for j in range(4):
                res = bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.7, radius2=0.0, depth=2.2)
                for v in res["verts"]:
                    p = Vector(at(-20 + j * 3.6, side * 14.5, 3.5)) + Vector((0, 0, v.co.z))
                    v.co = p + fwd * v.co.x + right * v.co.y

    k.add("bone", fangs)
    k.build(c, "Serpent Gate", "Citadel", "both")
    for side in (-1, 1):
        p = Vector(at(-26, side * 12.0, 0.0))
        c.place(wp.brazier(c, 1), p.x, p.y, base - 0.2, rot=rot, coll="Fire")
        lights.add((p.x, p.y, base + 5.6))


def tunnel_dressing(c, cc, lights, s0, s1, half):
    """Inside the serpent: pilasters down both walls with a torch on every other one, a
    carved frieze, icicles hanging from the roof, fallen blocks, and glowing doorways
    into chambers off the passage."""
    k = Blocks()
    torch = props.torch(c)
    ice = wp.icicles(c, 0, 2.4)
    s = s0
    j = 0
    while s < s1:
        q = c.at(s)
        rot = road_rot(q)
        for side in (-1, 1):
            p = q.side(side * (half - 0.5))
            k.box(DARK, (p.x, p.y, p.z + 3.0), (2.0, 1.0, 6.4), rot=rot, snow=False)
            k.box(CARVED, (p.x, p.y, p.z + 6.6), (2.4, 1.3, 1.0), rot=rot, snow=False)
            if (j + (side > 0)) % 2 == 0:
                t = q.side(side * (half - 1.1), 3.8)
                c.place(torch, t.x, t.y, t.z, rot=math.atan2(-q.r.x * side, q.r.y * side), scale=1.6, coll="Fire", role="visual")
                lights.add(tuple(q.side(side * (half - 2.3), 5.6)))
            if j % 5 == 2 and side > 0:
                # A glowing doorway into a side chamber.
                d = q.side(side * (half - 0.05), 0.0) + q.t * 4.0
                k.box(GLOW, (d.x, d.y, d.z + 2.2), (3.0, 0.3, 4.4), rot=rot, snow=False)
                k.box(CARVED, (d.x, d.y, d.z + 4.9), (4.2, 0.6, 1.0), rot=rot, snow=False)
        r = (rnd(j * 3.1) - 0.5) * half
        ip = q.side(r, 11.0 - abs(r) * 0.35)
        c.place(ice, ip.x, ip.y, ip.z, rot=rot + j, coll="Fire", role="visual")
        if j % 3 == 1:
            rp = q.side((1 if j % 2 else -1) * (half - 1.6), -0.2)
            c.place(wp.rubble(c, j % 2), rp.x, rp.y, rp.z, rot=j, scale=0.5, coll="Fire", role="visual")
        s += 9.0
        j += 1
    # The frieze.
    s = s0 - 4
    while s < s1 + 4:
        q = c.at(s)
        q2 = c.at(s + 4.0)
        for side in (-1, 1):
            a = q.side(side * (half - 0.25), 7.0)
            b = q2.side(side * (half - 0.25), 7.0)
            mid = (a + b) / 2
            k.box(CARVED, (mid.x, mid.y, mid.z), ((b - a).length + 0.05, 0.5, 1.0), rot=math.atan2((b - a).y, (b - a).x), snow=False)
        s += 4.0
    k.build(c, "Serpent Halls", "Tunnel", "visual")


# ------------------------------------------------------------------ the courtyard and temple


def courtyard(c, cc, lights, center):
    """The Moonlit Temple's courtyard: the sun disk at the heart of the sweep, statues and
    a ring of carved pillars with braziers, the temple to the north."""
    ter = list(c.coll("Terrain").objects)
    cx, cy = center
    z = c.ground_z(cx, cy, ter) or cc.PLATEAU_Z
    q = c.at(cc.SEG[14] + 47)
    c.place(wp.sun_disk(c), cx, cy, z - 0.3, rot=math.atan2(cx - q.p.x, -(cy - q.p.y)) + math.pi / 2, coll="Citadel")
    for i in range(4):
        a = i * math.tau / 4 + 0.4
        x, y = cx + 11 * math.cos(a), cy + 11 * math.sin(a)
        c.place(wp.brazier(c, 0), x, y, z, rot=a, coll="Fire")
        lights.add((x, y, z + 2.8))
    # Pillars round the outside of the sweep, every other one with a brazier on top.
    j = 0
    for i in range(16):
        a = i * math.tau / 16
        r = 60 + cc.road_w(0, 14) / 2 + 9
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        if not props.clear_of_road(c, x, y, 5) or cc.in_tunnel_rock(x, y, 1.0):
            continue
        gz = c.ground_z(x, y, ter)
        if gz is None:
            continue
        c.place(wp.carved_pillar(c, 2 if j % 5 == 4 else j % 2, 8.0), x, y, gz - 0.2, rot=a, coll="Citadel")
        if j % 2 == 0 and j % 5 != 4:
            c.place(wp.brazier(c, 0), x, y, gz + 9.2, rot=a, coll="Fire", role="visual")
            lights.add((x, y, gz + 12.0))
        j += 1
    # Statues inside the sweep.
    for i, a in enumerate((2.3, 3.4, 4.6)):
        x, y = cx + 30 * math.cos(a), cy + 30 * math.sin(a)
        gz = c.ground_z(x, y, ter)
        if gz is not None and props.clear_of_road(c, x, y, 6):
            c.place(wp.statue(c, i % 2), x, y, gz - 0.2, rot=math.atan2(cy - y, cx - x) + math.pi / 2, coll="Citadel")


def temple_and_terraces(c, cc, lights, tx, ty):
    """The temple raised on a great terrace (so it shows over the cliffs from the start
    line, far below), stairs up the terrace's face, braziers on every tier."""
    ter = list(c.coll("Terrain").objects)
    z0 = c.ground_z(tx, ty, ter) or cc.PLATEAU_Z
    k = Blocks()
    lift = 18.0
    for i, (w, h) in enumerate(((96.0, 6.0), (86.0, 6.0), (76.0, 6.0))):
        k.box(STONE, (tx, ty, z0 - 2 + h * i + h / 2 + 2), (w, w, h), snow=True)
        k.box(CARVED, (tx, ty - w / 2 - 0.02, z0 + h * i + h - 0.8), (w * 0.9, 0.4, 1.0), snow=False)
    for j in range(16):
        t = j / 16
        y = ty - 48 - 6 + t * 16
        k.box(STONE, (tx, y, z0 + (lift * t) / 2), (16.0, 1.4, lift * t + 0.4), snow=j % 2 == 0)
    k.build(c, "Temple Terrace", "Temple")
    z = z0 + lift
    c.place(wp.temple(c), tx, ty, z - 0.4, rot=0.0, coll="Temple")
    # Braziers on the corners of every tier, and either side of the stairs.
    size, tiers, h = 64.0, 6, 6.2
    for i in range(tiers):
        s = (size - i * 8.5) / 2 - 1.2
        zz = z - 0.4 + h * (i + 1)
        for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            c.place(wp.brazier(c, 0), tx + sx * s, ty + sy * s, zz, rot=0, coll="Fire", role="visual")
            lights.add((tx + sx * s, ty + sy * s, zz + 2.8))
    for side in (-1, 1):
        x, y = tx + side * 9.0, ty - size / 2 - 3.0
        c.place(wp.brazier(c, 1), x, y, z - 0.2, rot=0, coll="Fire")
        lights.add((x, y, z + 5.6))
        c.place(wp.statue(c, 1), tx + side * 20.0, ty - size / 2 - 8.0, z - 0.2, rot=0, coll="Temple")
    # Banners hanging down the temple's face.
    for side in (-1, 1):
        for i in range(3):
            s = (size - i * 8.5) / 2
            c.place(wp.hanging_banner(c, 0 if i % 2 else 1, 5.5), tx + side * 14.0, ty - s - 0.1, z + h * (i + 1) - 0.6, rot=0, coll="Temple", role="visual")


# ------------------------------------------------------------------ walls, towers, the town


def wall_along(c, name, pts, height, thick=3.0, crenels=True, mat=STONE, coll="Citadel", role="visual", base=None):
    """A fortress wall along a path of (x, y) points, standing on the land (or on `base`
    heights), crenellated, with carved bands."""
    ter = list(c.coll("Terrain").objects)
    k = Blocks()
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        ln = math.hypot(bx - ax, by - ay)
        rot = math.atan2(by - ay, bx - ax)
        n = max(1, int(ln / 8))
        for i in range(n):
            t = (i + 0.5) / n
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            gz = c.ground_z(x, y, ter) if base is None else base(x, y)
            if gz is None:
                continue
            k.box(mat, (x, y, gz - 2 + (height + 2) / 2), (ln / n + 0.3, thick, height + 2), rot=rot, snow=not crenels)
            k.box(CARVED, (x, y, gz + height - 1.4), (ln / n + 0.35, thick + 0.3, 1.2), rot=rot, snow=False)
            if crenels:
                for m in (-0.25, 0.25):
                    p = (x + math.cos(rot) * m * ln / n, y + math.sin(rot) * m * ln / n)
                    k.box(mat, (p[0], p[1], gz + height + 0.6), (ln / n * 0.3, thick, 1.2), rot=rot)
    if k.groups:
        k.build(c, name, coll, role)


def labyrinth(c, cc, lights):
    """The High Labyrinth: tall walls hemming in the lanes, arches over them, watchtowers
    on the corners, and glimpses out through the gaps."""
    s0, s1 = cc.SEG[15], cc.SEG[19]
    for side in (-1, 1):
        pts = []
        s = s0 - 10
        while s <= s1 + 6:
            q = c.at(s)
            p = q.side(side * (q.w / 2 + 3.6))
            pts.append((p.x, p.y))
            s += 6.0
        # Gaps in the wall now and then, to see out (and down) through.
        runs = [pts[i:i + 7] for i in range(0, len(pts), 9)]
        for i, run in enumerate(runs):
            if len(run) > 1:
                wall_along(c, "Labyrinth Wall %s %d" % ("L" if side < 0 else "R", i), run, 9.0 + 3.0 * ((i + (side > 0)) % 2), thick=2.6)
    for i, s in enumerate((s0 + 12, s0 + 48, s0 + 84, s0 + 118)):
        q = c.at(s)
        if place_arch(c, s, 10.0, 10.0, i % 2) is None:
            continue
        for side in (-1, 1):
            b = q.side(side * (q.w / 2 + 3.0)) - q.t * 5.0
            c.place(wp.brazier(c, 0), b.x, b.y, b.z, rot=road_rot(q), coll="Fire")
            lights.add((b.x, b.y, b.z + 2.8))
    for i, s in enumerate((s0 + 30, s0 + 100)):
        q = c.at(s)
        side = 1 if i % 2 else -1
        p = q.side(side * (q.w / 2 + 12.0))
        c.place(wp.tower(c, i, 22.0), p.x, p.y, p.z - 1.0, rot=road_rot(q), coll="Citadel")


def cliff_dwellings(c, cc, lights):
    """The citadel carved into the cliffs: rows of firelit windows and doorways cut into
    the rock faces, balconies, and battlements along the cliff tops, all the way along
    the chasm's west wall, the north gorge and the mountains over the descent."""
    ter = list(c.coll("Terrain").objects)
    k = Blocks()
    walls = []

    def carve(x, y, z, face, wide=2.0, tall=4.0, balcony=False):
        """A doorway or window cut into a cliff facing `face` (a unit (x, y))."""
        fx, fy = face
        rot = math.atan2(fy, fx) + math.pi / 2
        k.box(CARVED, (x + fx * 0.3, y + fy * 0.3, z + tall / 2 + 0.6), (wide + 1.6, 0.8, tall + 1.8), rot=rot, snow=True)
        k.box(GLOW, (x + fx * 0.75, y + fy * 0.75, z + tall / 2), (wide, 0.2, tall), rot=rot, snow=False)
        lights.add((x + fx * 3.0, y + fy * 3.0, z + tall * 0.6))
        if balcony:
            k.box(STONE, (x + fx * 2.2, y + fy * 2.2, z - 0.4), (wide + 5.0, 4.0, 0.8), rot=rot)
            k.box(STONE, (x + fx * 4.0, y + fy * 4.0, z + 0.5), (wide + 5.0, 0.6, 1.2), rot=rot)

    # The chasm's west wall (facing east), in storeys.
    for i in range(14):
        y = -260 + i * 21 + 6 * math.sin(i * 1.7)
        if -150 < y < -20:
            continue  # the serpent rock is there
        for z in (-30, 0, 30):
            if (i + int(z)) % 3 == 0:
                continue
            x = -98 - 2.0
            # Step out to the face: find where the land drops away.
            for _ in range(12):
                g = c.ground_z(x + 2.0, y, ter)
                if g is not None and g < z:
                    break
                x += 2.0
            carve(x, y, z, (1, 0), balcony=(i + int(z / 30)) % 4 == 0)
        walls.append((-100.0, y))
    # The north gorge's north wall (facing south) and the mountains over the descent.
    for i in range(10):
        x = -10 + i * 22
        y = 172 + 4 * math.sin(i)
        g = c.ground_z(x, y - 6, ter)
        if g is not None:
            carve(x, y - 9, max(g, 10.0) + 4, (0, -1), balcony=i % 3 == 0)
    for i in range(9):
        y = 100 - i * 30
        x = 300 + 4 * math.sin(i)
        g = c.ground_z(x, y, ter)
        if g is not None:
            carve(x - 2, y, g + 2.0, (-1, 0), wide=2.6, tall=5.0, balcony=i % 2 == 0)
    k.build(c, "Cliff Dwellings", "Citadel", "visual")
    # Battlements along the top of the chasm's west wall.
    wall_along(c, "Chasm Battlements South", [(-104, -275), (-104, -230), (-103, -190), (-104, -160)], 6.0, thick=3.0)
    wall_along(c, "Chasm Battlements North", [(-102, -8), (-100, 30), (-92, 60)], 6.0, thick=3.0)


def keep(c, cc, lights):
    """The citadel's great keep, high on the mountain at the head of the valley: the
    first thing you see from the start line, straight ahead and far above. Tiered walls
    stepping up the mountainside, a gatehouse, towers and a tall lit hall."""
    ter = list(c.coll("Terrain").objects)
    x0, y0 = 30.0, 300.0
    z0 = c.ground_z(x0, y0, ter) or 120.0
    k = Blocks()
    for i, (w, d, h) in enumerate(((120.0, 50.0, 22.0), (90.0, 40.0, 20.0), (60.0, 30.0, 22.0))):
        y = y0 + i * 14
        z = z0 - 20 + sum(hh for _, _, hh in ((120.0, 50.0, 22.0), (90.0, 40.0, 20.0), (60.0, 30.0, 22.0))[:i])
        k.box(STONE, (x0, y, z + h / 2), (w, d, h))
        k.box(CARVED, (x0, y - d / 2 - 0.1, z + h - 2.0), (w, 0.4, 1.6), snow=False)
        for j in range(int(w / 12)):
            wx = x0 - w / 2 + 6 + j * 12
            k.box(GLOW, (wx, y - d / 2 - 0.15, z + h * 0.45), (2.4, 0.3, 4.0), snow=False)
        for m in range(int(w / 6)):
            k.box(STONE, (x0 - w / 2 + 3 + m * 6, y - d / 2 + 1.0, z + h + 0.8), (2.4, 2.0, 1.6))
    top = z0 - 20 + 64
    k.box(STONE, (x0, y0 + 30, top + 16), (28.0, 22.0, 32.0))
    k.box(GLOW, (x0, y0 + 30 - 11.1, top + 10), (8.0, 0.3, 14.0), snow=False)
    k.box("temple_gold", (x0, y0 + 30 - 11.3, top + 24), (7.0, 0.4, 5.0), snow=False)
    k.build(c, "Great Keep", "Fortress", "visual")
    for i, (dx, dz) in enumerate(((-66, 0), (66, 0), (-48, 22), (48, 22), (-20, 46), (20, 46))):
        c.place(wp.tower(c, i % 2, 30.0 + 6 * (i % 3)), x0 + dx, y0 + (i // 2) * 14 - 22, z0 - 22 + dz, rot=0, coll="Fortress", role="visual")
    lights.add((x0, y0 - 30, z0 + 10))
    lights.add((x0, y0 + 16, top + 8))


def lower_town(c, cc, lights):
    """The Lower Ruins: houses with firelit doorways, broken walls and pillars, rubble,
    a ruined arch over the road."""
    ter = list(c.coll("Terrain").objects)
    houses = [wp.ruin_house(c, v) for v in range(2)]
    n = 0
    for i in range(60):
        s = cc.SEG[28] + 10 + (cc.SEG[31] - cc.SEG[28] - 10) * rnd(i * 3.7)
        q = c.at(s)
        side = 1 if rnd(i * 1.9) < 0.5 else -1
        p = q.side(side * (q.w / 2 + 12 + 30 * rnd(i * 5.3)))
        if not props.clear_of_road(c, p.x, p.y, 8):
            continue
        z = c.ground_z(p.x, p.y, ter)
        if z is None:
            continue
        c.place(houses[i % 2], p.x, p.y, z - 0.3, rot=math.atan2(-q.r.y * side, -q.r.x * side) + math.pi / 2, coll="Town")
        n += 1
        if n >= 14:
            break
    place_arch(c, (cc.SEG[29] + cc.SEG[30]) / 2, 8.0, 11.0, 0, coll="Town")
    props.scatter(c, wp.rubble(c, 0), 16, (-60, 260, -350, -230), lambda x, y, z: props.clear_of_road(c, x, y, 5), ter, seed=900, scale=(0.8, 1.6), coll="Town", role="visual")
    props.scatter(c, wp.carved_pillar(c, 2, 7.0), 10, (-60, 260, -350, -230), lambda x, y, z: props.clear_of_road(c, x, y, 6), ter, seed=910, coll="Town")


def fortress(c, cc, lights):
    """The citadel on the mountains: walls and towers climbing the north and west
    mountainsides at different heights, lit windows, and towers on the cliff edges."""
    ter = list(c.coll("Terrain").objects)
    towers = [wp.tower(c, v, h) for v, h in ((0, 24.0), (1, 30.0), (2, 36.0))]
    spots = [
        (-330, 255), (-250, 300), (-160, 270), (-60, 245), (40, 230), (130, 225), (240, 215),
        (-370, 120), (-360, -20), (-350, -160), (330, 160), (340, 30), (350, -120),
        (-112, -250), (-112, -190), (-110, -150), (-112, 40),
    ]
    placed = []
    for i, (x, y) in enumerate(spots):
        z = c.ground_z(x, y, ter)
        if z is None or not props.clear_of_road(c, x, y, 18):
            continue
        c.place(towers[i % 3], x, y, z - 2.0, rot=0.3 * i, coll="Fortress", role="visual")
        placed.append((x, y, z))
        if i % 2 == 0:
            lights.add((x, y, z + 20))
    # Walls joining neighbouring towers on the north side.
    north = [p for p in placed if p[1] > 200]
    for i, (a, b) in enumerate(zip(north, north[1:])):
        wall_along(c, "Fortress Wall %d" % (i + 1), [(a[0], a[1]), (b[0], b[1])], 12.0, thick=4.0)
    # The far peaks, beyond the land: snowy rock cones round the horizon.
    for i in range(12):
        a = i * math.tau / 12 + 0.2
        r = 760 + 160 * rnd(i * 2.3)
        x, y = r * math.cos(a), r * math.sin(a)
        if y < -500 and -400 < x < 300:
            continue  # leave the view south down the valley open
        h = 260 + 220 * rnd(i * 4.1)
        bm = bmesh.new()
        rings = [props.ring(bm, (x, y), rr, z, 9, phase=i) for rr, z in ((260, -20), (150, h * 0.55), (60, h * 0.9), (8, h))]
        props.loft(bm, rings)
        ob = c.mesh_object("Far Peak %d" % (i + 1), bm, "Backdrop", "visual")
        top = [f.index for f in ob.data.polygons if f.center.z > h * 0.5]
        rest = [f.index for f in ob.data.polygons if f.center.z <= h * 0.5]
        c.assign(ob, c.lib("frost_cliff"), rest)
        c.assign(ob, c.lib(wp.SNOW), top)
        ob.data.shade_flat()


# ------------------------------------------------------------------ water, ice and fog


def waterfalls(c, cc, lights):
    """Waterfalls off the plateau into the chasm, from the mountains into the north gorge
    and the frozen gorge, frozen falls down the cliffs, and their entities (spray, roar)."""
    feet = []
    falls = (
        # (x, lip y, top, foot, width, angle): angle turns it to face across the chasm.
        ("Chasm Falls 1", -100.0, -175.0, 54.0, -95.0, 16.0, math.pi / 2),
        ("Chasm Falls 2", -100.0, -30.0, 54.0, -95.0, 12.0, math.pi / 2),
        ("Valley Falls", -32.0, -60.0, 0.0, -95.0, 10.0, -math.pi / 2),
        ("Gorge Falls", 230.0, 160.0, 70.0, 4.0, 14.0, 0.0),
        ("Temple Falls 1", -290.0, 250.0, 120.0, 56.0, 14.0, 0.0),
        ("Temple Falls 2", -140.0, 265.0, 110.0, 56.0, 10.0, 0.0),
        ("Jump Falls", 340.0, -176.0, 95.0, 40.0, 12.0, -math.pi / 2),
    )
    for name, x, y, top, foot, w, ang in falls:
        fx, fy = props.falls(c, name, x, y, top, foot, w, w * 1.3, facing=-1, throw=5.0, angle=ang, veils=3, mats=FROST_FALLS, foam=foot > -50)
        feet.append((fx, fy, foot, top, w * 1.3))
    for fx, fy, foot, top, w in feet:
        gx, gy, gz = c.game(fx, fy, max(foot, -40.0))
        c.entity("waterfall", x=round(gx, 1), y=round(gy, 1), z=round(gz, 1), top=round(top, 1), width=round(w, 1), heading=0)
    # Frozen falls down the mountainsides above the descent, and down the chasm walls.
    for i, (x, y, top, foot, w, face) in enumerate((
        (312, 70, 120, 62, 18, (-1, 0)),
        (318, -30, 130, 50, 22, (-1, 0)),
        (322, -110, 110, 34, 16, (-1, 0)),
        (-104, -110, 52, -40, 14, (1, 0)),
        (-104, -230, 52, -50, 18, (1, 0)),
        (60, 230, 120, 40, 20, (0, -1)),
    )):
        wp.ice_fall(c, "Frozen Falls %d" % (i + 1), x, y, top, foot, w, facing=face)


def fog(c, cc):
    """Layers of glowing fog in the chasm and the gorges: thin, wide sheets stacked over
    denser ones, so the drops fill with mist that fades into the depths."""
    chasm = cc.CHANNEL[: cc.CHASM_TO + 1]
    gorge = cc.CHANNEL[cc.CHASM_TO:]

    def ribbon(name, pts, width, z, mat):
        path = []
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(bx - ax, by - ay) / 10))
            for i in range(n):
                t = i / n
                path.append((ax + (bx - ax) * t, ay + (by - ay) * t))
        path.append(pts[-1])
        c.ribbon(name, path, width, z, c.lib(mat), coll="Fog", role="visual", steps=3)

    for i, (z, wid, mat) in enumerate(((-70, 70, "fog_sheet"), (-45, 78, "fog_sheet"), (-22, 92, "fog_thin"), (-6, 104, "fog_thin"))):
        ribbon("Chasm Fog %d" % (i + 1), chasm, wid, z, mat)
    for i, (dz, wid, mat) in enumerate(((-18, 56, "fog_sheet"), (-6, 70, "fog_thin"))):
        ribbon("Gorge Fog %d" % (i + 1), gorge, wid, 4.0 + dz + 8, mat)
    ribbon("Jump Fog", cc.GORGE, 26, 4.0, "fog_thin")


# ------------------------------------------------------------------ vegetation


def vegetation(c, cc):
    ter = list(c.coll("Terrain").objects)
    palms = [wp.snowy_palm(c, v) for v in range(2)]
    pines = [wp.conifer(c, v, h) for v, h in ((0, 9.0), (1, 13.0), (2, 17.0))]
    shrubs = [wp.snow_shrub(c, v) for v in range(2)]
    drifts = [wp.snow_drift(c, v) for v in range(2)]
    rocks = [props.boulder(c, "frost_rock", v) for v in range(3)]

    def ok(m0, m1, zmin=-5, zmax=400):
        def f(x, y, z):
            smp, d = c.nearest(x, y)
            return smp.w / 2 + m0 < d < smp.w / 2 + m1 and zmin < z < zmax and not cc.in_abyss(x, y, 4) and not cc.in_tunnel_rock(x, y, 1.02)

        return f

    area = (-400, 400, -400, 380)
    # Trees are scenery only (no collision): they stand well clear of the road.
    for v, p in enumerate(palms):
        props.scatter(c, p, 28, area, ok(5, 70, zmax=70), ter, seed=1000 + v, scale=(0.9, 1.3), coll="Trees", role="visual")
    for v, p in enumerate(pines):
        props.scatter(c, p, 50, area, ok(6, 160), ter, seed=1010 + v, scale=(0.8, 1.4), coll="Trees", role="visual")
        props.scatter(c, p, 22, area, ok(40, 400, zmin=60), ter, seed=1020 + v, scale=(1.0, 1.6), coll="Trees", role="visual")
    for v, s in enumerate(shrubs):
        props.scatter(c, s, 40, area, ok(3.5, 80), ter, seed=1030 + v, coll="Trees", role="visual", scale=(0.7, 1.4))
    for v, d in enumerate(drifts):
        props.scatter(c, d, 40, area, ok(4, 90), ter, seed=1040 + v, coll="Trees", role="visual", sink=0.4)
    for v, r in enumerate(rocks):
        props.scatter(c, r, 18, area, ok(8, 120), ter, seed=1050 + v, scale=(1.5, 4.0), coll="Trees")


# ------------------------------------------------------------------ build


def build(c, rock, t0, t1, cc):
    lights = Lights()
    ter = list(c.coll("Terrain").objects)
    half = c.width / 2 + 3.4

    # A: the Great Gate, braziers down the valley, pillars along the chasm's rim.
    great_gate(c, cc, lights, 59.0)
    braziers_along(c, cc, lights, 20.0, cc.SEG[1] + 40, 26.0, 3.2)
    pillars_along(c, 30.0, cc.SEG[1], 30.0, 4.5, -1, 0, 6.0)
    # B: the switchbacks, braziers on the outside and pillars on the guardrail.
    braziers_along(c, cc, lights, cc.SEG[2], cc.SEG[7] - 10, 24.0, 2.6)
    pillars_along(c, cc.SEG[2] + 10, cc.SEG[7] - 10, 28.0, 3.4, -1, 1, 5.0)
    # C: the Bridge of Giants and its approach gateway.
    bs = [p for p in c.pieces if "bridge" in p.name]
    for p in bs:
        s0, s1 = p["kp_from"], p["kp_to"]
        bridge_piers(c, cc, lights, s0, s1, 33.0, p.name)
    place_arch(c, cc.SEG[7] + 4, 8.0, 14.0, 1)
    # D: the Serpent Gate and its halls.
    serpent_gate(c, cc, lights, t0 + 2.0)
    tunnel_dressing(c, cc, lights, t0 + 8, t1 - 4, half)
    c.glow([rock], [p for p in lights.points if cc.in_tunnel_rock(p[0], p[1], 1.1)], 11.0, (1.25, 0.9, 0.55), base=0.4, region=lambda w: cc.in_tunnel_rock(w.x, w.y, 1.0) and w.z < 75)
    # E: the courtyard, the sun disk and the temple.
    q = c.at(cc.SEG[14])
    center = q.p + q.r * 60.0
    courtyard(c, cc, lights, (center.x, center.y))
    temple_and_terraces(c, cc, lights, -215.0, 188.0)
    # F: the labyrinth and the high causeway.
    labyrinth(c, cc, lights)
    for p in c.pieces:
        if "causeway" in p.name or "icebridge" in p.name or "ramp" in p.name:
            s0, s1 = p["kp_from"], p["kp_to"]
            bridge_piers(c, cc, lights, s0, s1, 30.0 if "causeway" in p.name else 14.0, p.name, deck=3.4, faces="causeway" in p.name, bannered="causeway" in p.name)
    # G: the descent.
    braziers_along(c, cc, lights, cc.SEG[20] + 60, cc.LIP - 10, 24.0, 2.6)
    braziers_along(c, cc, lights, cc.LAND + 10, cc.SEG[28], 20.0, 2.6, alternate=False)
    for i, s in enumerate((cc.SEG[22] + 10, cc.SEG[24] + 20)):
        q = c.at(s)
        p = q.side(22.0)
        z = c.ground_z(p.x, p.y, ter)
        if z is not None:
            c.place(wp.tower(c, i, 26.0), p.x, p.y, z - 1.0, rot=road_rot(q), coll="Citadel")
    # H: the lower town.
    lower_town(c, cc, lights)
    braziers_along(c, cc, lights, cc.SEG[28] + 10, cc.SEG[31], 26.0, 3.0)
    # The frozen pond by the start: a giant stone head half sunk in the ice.
    px, py, pr = cc.POND
    c.disc("Pond Ice", px, py, pr, -0.6, c.lib("frost_pool", "ice"), coll="Water", n=24, wobble=0.15)
    c.place(wp.dino_head(c, 0), px + 6, py + 4, -3.5, rot=2.3, coll="Citadel", role="visual")
    c.place(wp.statue(c, 0), px - 14, py - 10, -0.8, rot=0.9, coll="Citadel")

    fortress(c, cc, lights)
    cliff_dwellings(c, cc, lights)
    keep(c, cc, lights)
    waterfalls(c, cc, lights)
    fog(c, cc)
    vegetation(c, cc)

    # The firelight: torch entities for the flickering runtime light, and warm light
    # painted round every flame on the land and the stone (with a cold, moonlit tint
    # everywhere else).
    for x, y, z in lights.points:
        gx, gy, gz = c.game(x, y, z)
        c.entity("torch", x=round(gx, 2), y=round(gy, 2), z=round(gz, 2))
    # Copies joined into one mesh per map square (far fewer draw calls), which also lets
    # the firelight be painted onto them.
    groups = ("Citadel", "Bridges", "Temple", "Town", "Fortress", "Tunnel")
    c.merge_props(groups)
    stone = [o for name in groups for o in c.coll(name).objects if o.type == "MESH" and o.data.users == 1]
    c.glow(ter + stone, lights.points, 16.0, (1.0, 0.86, 0.6), base=(0.88, 0.9, 1.0), region=lambda w: not (cc.in_tunnel_rock(w.x, w.y, 1.0) and w.z < 75))
    # Light snow falling round the camera.
    c.entity("snowfall", rate=110, radius=40)
