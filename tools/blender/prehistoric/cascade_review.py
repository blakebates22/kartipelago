# Cascade Caverns v3: Blake's first review round (reviews/cascade_caverns/, 28 notes from
# the in-game review tool), built on v2 (kept playable as cascade_caverns_v2).
# SPDX-License-Identifier: MIT
#
#   bounds      stone rails wherever the road runs along a drop (the bridge's end into
#               the temple, the tunnel's west mouth, the ledge), each with a taller
#               invisible wall behind it; the hidden floor kept under the land everywhere
#               (it poked up through the landing strip: the "invisible plane")
#   water       every waterfall runs down (they all ran backwards); Wall Falls 3 is now a
#               great stepped cascade from the rim, tier by tier, into a stream that runs
#               across the floor into the river
#   wood        stump and log ends show one tree's rings; the giant trees are plain bark
#   trees       new giant and grand trees (buttress roots, real limbs, layered crowns);
#               any tree on a slope gets a grassy rock ledge to stand on
#   ruins       the random scatter is gone: composed sites instead (a colonnade, a shrine
#               court, a ruined gate, a small temple, a ball court, a great temple on the
#               tunnel rock), carved heads that face the road, no stairs into walls
#   tunnel      two stone guardians crouched either side of the temple's face
#   walls       calmer rock (strata by height, not a patchwork) and more green ledges
#
# Positions come from the notes: the game's (x, y, z) is Blender's (x, -z, y).
# All original designs, in the spirit of late-90s console scenery.

import math

import bpy
import props
from course_kit import Matrix, Vector, bmesh, rnd
from props import _faces, blob, tube

STONE = ("ruin_stone", "wall")
GLYPH = ("ruin_glyph", "wall")
DARK = ("ruin_dark", "wall")
MOSS = ("ruin_moss", "wall")
GLOW = ("torch_glow", None)
JADE = ("jade_stone", "wall")


def B(gx, gy, gz):
    """A point from the game (x, y up, z) in Blender (x, y, z up)."""
    return (gx, -gz, gy)


def ground_span(c, ter, x, y, r, n=8):
    """(lowest, highest) ground round a circle of radius r at (x, y), and the centre's."""
    zs = []
    for k in range(n):
        a = k * math.tau / n
        z = c.ground_z(x + r * math.cos(a), y + r * math.sin(a), ter)
        if z is not None:
            zs.append(z)
    z0 = c.ground_z(x, y, ter)
    if z0 is not None:
        zs.append(z0)
    if not zs:
        return None, None, None
    return min(zs), max(zs), z0


# ---------------------------------------------------------------- a mesh builder


class Build:
    """Parts in a local frame (x across, y back, z up), placed at (x, y, z) turned `rot`,
    into one mesh with a material per part."""

    def __init__(self, c, x, y, z, rot, scale=1.0):
        self.c = c
        self.bm = bmesh.new()
        self.m = Matrix.Translation((x, y, z)) @ Matrix.Rotation(rot, 4, "Z") @ Matrix.Scale(scale, 4)
        self.slots = {}

    def _take(self, mat, k0):
        self.bm.faces.ensure_lookup_table()
        self.slots.setdefault(mat, []).extend(range(k0, len(self.bm.faces)))

    def box(self, mat, centre, size, rot=0.0, tilt=(0.0, 0.0)):
        k0 = len(self.bm.faces)
        res = props.cuboid(self.bm, centre, size, rot, tilt)
        for v in res["verts"]:
            v.co = self.m @ v.co
        self._take(mat, k0)

    def cyl(self, mat, base, r, h, segs=8, r2=None, tilt=(0.0, 0.0), rot=0.0):
        """A drum standing on `base` (or laid down with tilt)."""
        k0 = len(self.bm.faces)
        res = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
        m = Matrix.Rotation(rot, 3, "Z") @ Matrix.Rotation(tilt[0], 3, "X") @ Matrix.Rotation(tilt[1], 3, "Y")
        for v in res["verts"]:
            v.co = self.m @ (Vector(base) + m @ (v.co + Vector((0, 0, h / 2))))
        self._take(mat, k0)

    def blob(self, mat, centre, r, sx=1.0, sy=1.0, sz=1.0, subdiv=1):
        k0 = len(self.bm.faces)
        res = blob(self.bm, centre, r, sx, sy, sz, subdiv)
        for v in res["verts"]:
            v.co = self.m @ v.co
        self._take(mat, k0)

    def done(self, name, coll="Ruins", role="both"):
        ob = self.c.mesh_object(name, self.bm, coll, role)
        for mat, faces in self.slots.items():
            self.c.assign(ob, self.c.lib(*mat), faces)
        ob.data.shade_flat()
        return ob


def slab(bm, cx, cy, rx, ry, z_top, z_bot, seed, n=10, angle=0.0):
    """A lumpy rock prism (sides and a flat top): returns (side faces, top faces)."""
    ca, sa = math.cos(angle), math.sin(angle)
    rings = []
    for scale, z in ((0.82, z_bot), (1.0, z_top - 0.9), (0.97, z_top)):
        ring = []
        for i in range(n):
            a = i * math.tau / n
            k = scale * (1 + 0.12 * math.sin(3 * a + seed) + 0.08 * (rnd(i * 7 + seed * 13) - 0.5))
            x, y = rx * k * math.cos(a), ry * k * math.sin(a)
            ring.append(bm.verts.new((cx + x * ca - y * sa, cy + x * sa + y * ca, z)))
        rings.append(ring)
    k0 = len(bm.faces)
    for lo, hi in zip(rings, rings[1:]):
        for i in range(n):
            bm.faces.new((lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i]))
    sides = _faces(bm, k0)
    k1 = len(bm.faces)
    bm.faces.new(rings[-1])
    return sides, _faces(bm, k1)


# ---------------------------------------------------------------- the bounds


def underfloor_height(c, cc):
    """The hidden floor's height: under the land as it's actually shaped (pulled to meet
    the roads), not just under the land's own shape. Where the road runs in a cutting,
    below the natural land (the landing strip after the leap), the old floor came up
    through the road: an invisible plane you hovered on."""

    def h(x, y):
        nat = cc.natural(x, y)
        w, z = c.road_height(x, y, 8.5, 16.0, 0.2, nat)
        shaped = nat + (z - nat) * w
        return min(cc.base_floor(x, y), nat, shaped) - 0.35

    return h


RAILED = ("viaduct", "ramp", "landing", "lowbridge", "ledge")


def edge_rails(c, cc, ter, every=2.0, drop=2.6, near=6.0, rubble=None, skip=None):
    """Stone rails along every stretch of road with a drop beside it (land more than
    `drop` metres below the road's edge within `near` metres of it), where the road has
    no barrier of its own. Each rail is a low carved wall (what you see and hit) with a
    taller invisible wall just behind it, so nobody hops over. Returns the stretches.
    `rubble(s)`: where the road is new in a ruin, the rail is a heap of broken stones
    instead (the destruction rule: nothing new looks built). `skip(s)`: stretches that
    get no rails at all (a tunnel, say)."""
    pieces = []
    for p in c.pieces:
        s0, s1 = p["kp_from"], p["kp_to"]
        if s1 < s0:
            s1 += c.length
        kind = p.name.split()[-1]
        pieces.append((s0, s1, kind))

    # Where one piece meets the next (a barrier can end short of the joint), rails go in
    # even beside a piece that has its own barrier.
    joints = sorted({round(p[0], 1) for p in pieces} | {round(p[1] % c.length, 1) for p in pieces})

    def near_joint(s):
        return any(abs(s - j) < 8.0 or abs(s - j + c.length) < 8.0 or abs(s - j - c.length) < 8.0 for j in joints)

    def kind_at(s):
        for s0, s1, k in pieces:
            if s0 <= s <= s1 or s0 <= s + c.length <= s1:
                return k
        return None  # a gap (the leap)

    shoulder = {k: v.get("shoulder", 1.5) for k, v in c.kinds.items()}
    marks = {-1: [], 1: []}
    s = 0.0
    while s < c.length:
        k = kind_at(s)
        if k is not None and (k not in RAILED or near_joint(s)) and not (skip and skip(s)):
            q = c.at(s)
            for side in (-1, 1):
                edge = q.w / 2 + shoulder.get(k, 1.5)
                ze = q.side(side * edge).z
                low = None
                for o in (1.0, 2.5, 4.0, near):
                    p = q.side(side * (edge + o))
                    g = c.ground_z(p.x, p.y, ter)
                    g = -50.0 if g is None else g  # nothing there at all: a hole
                    low = g if low is None else min(low, g)
                if ze - low > drop:
                    marks[side].append(s)
        s += every
    runs = []
    for side, ss in marks.items():
        cur = None
        for s in ss:
            if cur and s - cur[1] <= every * 3.5:
                cur[1] = s
            else:
                if cur:
                    runs.append((cur[0], cur[1], side))
                cur = [s, s]
        if cur:
            runs.append((cur[0], cur[1], side))
    bm = bmesh.new()
    rub = bmesh.new()
    inv = bmesh.new()
    kept = []
    for s0, s1, side in runs:
        s0, s1 = s0 - 6.0, s1 + 6.0  # past both ends of the drop
        if s1 - s0 < 10:
            continue
        kept.append((round(s0, 1), round(s1, 1), side))
        n = max(2, int((s1 - s0) / 2.0))
        for j in range(n):
            a, b = s0 + (s1 - s0) * j / n, s0 + (s1 - s0) * (j + 1) / n
            qa, qb = c.at(a), c.at(b)
            k = kind_at((a + b) / 2) or "path"
            ea = qa.w / 2 + shoulder.get(k, 1.5) + 0.35
            eb = qb.w / 2 + shoulder.get(k, 1.5) + 0.35
            pa, pb = qa.side(side * ea), qb.side(side * eb)
            mid = (pa + pb) / 2
            if rubble and rubble((a + b) / 2):
                # Broken stones: uneven heights, knocked askew.
                ln = (pb - pa).length + 0.06
                rot = math.atan2((pb - pa).y, (pb - pa).x) + 0.25 * math.sin(j * 2.3 + s0)
                hgt = 0.7 + 0.6 * (0.5 + 0.5 * math.sin(j * 1.7 + s0 * 0.3))
                props.cuboid(rub, (mid.x, mid.y, mid.z - 1.25 + hgt / 2), (ln * 0.9, 0.9, 2.5 + hgt), rot)
                back = Vector((math.cos(rot + math.pi / 2), math.sin(rot + math.pi / 2), 0)) * side * 0.6
                props.cuboid(inv, (mid.x + back.x, mid.y + back.y, mid.z + 0.9), (ln, 0.4, 5.0), rot)
                continue
            ln = (pb - pa).length + 0.06
            rot = math.atan2((pb - pa).y, (pb - pa).x)
            # The carved wall: from 2.5 m down (into the slope) to 1.25 m above the road.
            props.cuboid(bm, (mid.x, mid.y, mid.z - 0.625), (ln, 0.75, 3.75), rot)
            # A capstone, a little proud of the wall (every other block, for rhythm).
            if j % 2 == 0:
                props.cuboid(bm, (mid.x, mid.y, mid.z + 1.32), (ln * 0.96, 0.95, 0.22), rot)
            # The invisible wall: 3.4 m tall, just behind.
            back = Vector((math.cos(rot + math.pi / 2), math.sin(rot + math.pi / 2), 0)) * side * 0.6
            props.cuboid(inv, (mid.x + back.x, mid.y + back.y, mid.z + 0.9), (ln, 0.4, 5.0), rot)
    if rub.faces:
        ob = c.mesh_object("Rubble Rails", rub, "Bridge", "both")
        c.assign(ob, c.lib("ruin_rubble", "wall"), range(len(ob.data.polygons)))
        ob.data.shade_flat()
    else:
        rub.free()
    if bm.faces:
        ob = c.mesh_object("Edge Rails", bm, "Bridge", "both")
        bm_faces = len(ob.data.polygons)
        c.assign(ob, c.lib(*GLYPH), range(bm_faces))
        ob.data.shade_flat()
        ob2 = c.mesh_object("Edge Rail Walls", inv, "Collision", "collision")
        c.assign(ob2, c.lib(*STONE))
    else:
        bm.free()
        inv.free()
    return kept


# ---------------------------------------------------------------- trees


def giant_tree(c, variant=0):
    """A jungle giant (34-44 m), redone: a massive trunk of plain bark on great flaring
    buttress roots, three tiers of strong limbs each ending in its own cloud of leaves,
    a broad high crown, and a few bromeliads perched in the forks."""
    name = "Cascade Giant %d" % variant

    def build(bm):
        h = 34.0 + 5.0 * variant
        lean = (0.7 * math.sin(variant * 2.1 + 0.4), 0.7 * math.cos(variant * 1.7))
        tr = lambda t: (lean[0] * t * t, lean[1] * t * t)  # noqa: E731
        trunk_pts = [(0, 0, -1.2)] + [(*tr(t), h * t) for t in (0.2, 0.42, 0.64, 0.86, 1.0)]
        tube(bm, trunk_pts, [2.5, 1.95, 1.6, 1.35, 1.05, 0.8], n=11)
        # Buttress roots: tall thin fins that curve out and down into the ground.
        for i in range(8):
            a = i * math.tau / 8 + variant * 0.5 + 0.2 * math.sin(i * 3.1)
            ca, sa = math.cos(a), math.sin(a)
            reach = 5.5 + 2.0 * rnd(i + variant * 3)
            top = 7.0 + 3.0 * rnd(i * 2 + variant)
            prof = [(1.3, top), (2.4, top * 0.55), (reach * 0.75, top * 0.18), (reach, -1.0), (1.1, -1.0)]
            th = 0.34 + 0.12 * rnd(i * 5)
            off = Vector((-sa, ca, 0)) * th
            vs = [bm.verts.new(Vector((r * ca, r * sa, z)) + off) for r, z in prof]
            ws = [bm.verts.new(Vector((r * ca, r * sa, z)) - off) for r, z in prof]
            bm.faces.new(vs)
            bm.faces.new(list(reversed(ws)))
            for j in range(len(prof)):
                k = (j + 1) % len(prof)
                bm.faces.new((vs[j], ws[j], ws[k], vs[k]))
        limbs = []
        for i in range(7):
            a = i * math.tau / 7 + 0.4 + variant
            tier = i % 3
            z0 = h * (0.58 + 0.12 * tier)
            reach = 8.0 + 4.0 * rnd(i * 5 + variant) - tier * 1.2
            bx, by = tr(z0 / h)
            mid = (bx + reach * 0.5 * math.cos(a), by + reach * 0.5 * math.sin(a), z0 + 3.0)
            end = (bx + reach * math.cos(a), by + reach * math.sin(a), z0 + 5.0 + 2 * rnd(i + 9))
            tube(bm, [(bx, by, z0), mid, end], [0.95 - tier * 0.12, 0.6, 0.32], n=6)
            # A forked twig off each limb.
            tw = (end[0] + 2.2 * math.cos(a + 0.9), end[1] + 2.2 * math.sin(a + 0.9), end[2] + 1.6)
            tube(bm, [mid, ((mid[0] + tw[0]) / 2, (mid[1] + tw[1]) / 2, mid[2] + 1.6), tw], [0.4, 0.26, 0.16], n=5)
            limbs.append((end, tw, mid))
        trunk = _faces(bm, 0)
        k0 = len(bm.faces)
        top = [(*tr(1.0), h + 2.0, 8.0)]
        for k, (end, tw, _) in enumerate(limbs):
            top.append((end[0], end[1], end[2] + 1.4, 5.4 + 1.3 * rnd(k + variant)))
            top.append((tw[0], tw[1], tw[2] + 1.0, 3.6 + 0.8 * rnd(k * 3 + variant)))
        for x, y, z, r in top:
            blob(bm, (x, y, z), r, sx=1.05, sz=0.48, subdiv=2)
        crown = _faces(bm, k0)
        k1 = len(bm.faces)
        for x, y, z, r in top:
            blob(bm, (x * 0.92, y * 0.92, z - r * 0.42), r * 0.86, sz=0.3, subdiv=1)
        under = _faces(bm, k1)
        k2 = len(bm.faces)
        # Bromeliads in the forks: little rosettes of stiff leaves.
        for k, (_, _, mid) in enumerate(limbs[::2]):
            for j in range(5):
                a = j * math.tau / 5 + k
                tip = (mid[0] + 0.9 * math.cos(a), mid[1] + 0.9 * math.sin(a), mid[2] + 1.0)
                v0 = bm.verts.new((mid[0], mid[1], mid[2] + 0.2))
                v1 = bm.verts.new((mid[0] + 0.25 * math.cos(a + 1.2), mid[1] + 0.25 * math.sin(a + 1.2), mid[2] + 0.45))
                v2 = bm.verts.new(tip)
                bm.faces.new((v0, v1, v2))
        brom = _faces(bm, k2)
        return [(c.lib("giant_bark"), trunk), (c.lib("canopy_dark"), crown), (c.lib("jungle_leafcover"), under), (c.lib("canopy_bright"), brom)]

    return c.proto(name, build) and name


def grand_tree(c, variant=0):
    """A grand canopy tree (16-21 m), redone: a stout trunk on buttress fins, a few big
    limbs that split, and a crown of overlapping leaf clouds, bright on top and dark
    underneath, wider than it is tall."""
    name = "Cascade Grand %d" % variant

    def build(bm):
        h = 15.0 + 3.0 * variant
        bend = 0.5 + 0.4 * variant
        tube(bm, [(0, 0, -0.8), (0.15 * bend, 0.1, h * 0.3), (0.35 * bend, 0.25, h * 0.62), (0.4 * bend, 0.3, h * 0.8)], [1.55, 1.15, 0.95, 0.75], n=10)
        for i in range(6):
            a = i * math.tau / 6 + variant + 0.3 * math.sin(i * 2.3)
            ca, sa = math.cos(a), math.sin(a)
            reach = 3.2 + 1.2 * rnd(i + variant * 4)
            top = 3.6 + 1.6 * rnd(i * 3 + variant)
            prof = [(0.8, top), (1.5, top * 0.5), (reach, -0.6), (0.7, -0.6)]
            off = Vector((-sa, ca, 0)) * 0.26
            vs = [bm.verts.new(Vector((r * ca, r * sa, z)) + off) for r, z in prof]
            ws = [bm.verts.new(Vector((r * ca, r * sa, z)) - off) for r, z in prof]
            bm.faces.new(vs)
            bm.faces.new(list(reversed(ws)))
            for j in range(len(prof)):
                k = (j + 1) % len(prof)
                bm.faces.new((vs[j], ws[j], ws[k], vs[k]))
        ends = []
        for i in range(5):
            a = i * math.tau / 5 + 0.5 + variant * 0.8
            z0 = h * (0.55 + 0.08 * (i % 3))
            reach = 6.0 + 2.5 * rnd(i * 3 + variant)
            base = (0.3 * bend, 0.25, z0)
            mid = (reach * 0.5 * math.cos(a), reach * 0.5 * math.sin(a), z0 + 2.2)
            end = (reach * math.cos(a), reach * math.sin(a), z0 + 3.4 + rnd(i * 7))
            tube(bm, [base, mid, end], [0.6, 0.4, 0.22], n=6)
            fork = (mid[0] + 2.6 * math.cos(a - 0.8), mid[1] + 2.6 * math.sin(a - 0.8), mid[2] + 2.4)
            tube(bm, [mid, fork], [0.3, 0.16], n=5)
            ends += [(end, 4.2 + 0.9 * rnd(i + variant)), (fork, 3.0 + 0.6 * rnd(i * 5))]
        trunk = _faces(bm, 0)
        k0 = len(bm.faces)
        clouds = [((0.4 * bend, 0.3, h + 2.2), 5.6)] + [((p[0], p[1], p[2] + 1.0), r) for p, r in ends]
        for (x, y, z), r in clouds:
            blob(bm, (x, y, z), r, sx=1.1, sz=0.5, subdiv=2)
        top = _faces(bm, k0)
        k1 = len(bm.faces)
        for (x, y, z), r in clouds:
            blob(bm, (x * 0.9, y * 0.9, z - r * 0.4), r * 0.85, sz=0.32, subdiv=1)
        under = _faces(bm, k1)
        return [(c.lib("giant_bark"), trunk), (c.lib("canopy_bright"), top), (c.lib("jungle_leafcover"), under)]

    return c.proto(name, build) and name


TREE_FOOT = {
    "Cascade Giant": 3.0,
    "Cascade Grand": 1.9,
    "Jungle Tree": 0.8,
    "Palm": 0.6,
}


def ground_trees(c, cc, ter, max_lean=0.9, max_ledge=11.0):
    """Every tree on a slope (more than `max_lean` metres of fall across its foot) stands
    on a grassy rock ledge instead of hanging half off the wall: a shelf at the top of
    its footing with ferns round the rim. A tree on ground too steep even for that
    (more than `max_ledge` across) is taken out. Returns (ledged, removed)."""
    bm = bmesh.new()
    sides, tops = [], []
    fern = props.fern(c)
    ledged = removed = 0
    obs = [o for coll in ("Props",) for o in c.coll(coll).objects]
    for ob in obs:
        base = next((k for k in TREE_FOOT if ob.name.startswith(k)), None)
        if base is None or ob.type != "MESH":
            continue
        s = ob.scale.x
        r = TREE_FOOT[base] * s
        x, y = ob.location.x, ob.location.y
        lo, hi, mid = ground_span(c, ter, x, y, r + 0.8)
        if lo is None:
            continue
        if hi - lo <= max_lean:
            continue
        if hi - lo > max_ledge or cc.in_tunnel_rock(x, y, 1.0):
            bpy.data.objects.remove(ob)
            removed += 1
            continue
        top = hi + 0.25
        k = ledged
        sd, tp = slab(bm, x, y, r + 2.4, r + 2.0, top, lo - 1.2, seed=k * 3 + 1, angle=rnd(k) * math.tau)
        sides += sd
        tops += tp
        ob.location.z = top - 0.25
        for j in range(3):
            a = j * math.tau / 3 + k
            c.place(fern, x + (r + 1.4) * math.cos(a), y + (r + 1.2) * math.sin(a), top - 0.05, rot=a, scale=0.9 + 0.4 * rnd(k + j), coll="Walls", role="visual")
        ledged += 1
    if bm.faces:
        ob = c.mesh_object("Tree Ledges", bm, "Walls", "both")
        c.assign(ob, c.lib("canyon_rock_moss", "wall"), sides)
        c.assign(ob, c.lib("jungle_leafcover", "grass"), tops)
        ob.data.shade_flat()
    else:
        bm.free()
    return ledged, removed


# ---------------------------------------------------------------- ruins


def facing_road(c, x, y):
    """The turn (about Z) that points a part's front (-Y) at the nearest road."""
    smp, _ = c.nearest(x, y)
    return math.atan2(smp.p.x - x, -(smp.p.y - y))


def find_site(c, cc, ter, x, y, radius, keep=6.0, flat=2.2, tries=40):
    """A spot near (x, y) at least `keep` metres clear of the road (beyond the site's own
    radius), off the river, out of the tunnel rock and fairly level (less than `flat`
    metres of fall across it). Returns (x, y, ground_high, ground_low) or None."""
    for k in range(tries):
        if k == 0:
            px, py = x, y
        else:
            a = k * 2.399
            d = 2.0 + 1.6 * k
            px, py = x + d * math.cos(a), y + d * math.sin(a)
        if not props.clear_of_road(c, px, py, radius + keep):
            continue
        if abs(py - cc.river_y(px)) < cc.river_half(px) + radius + 2 or cc.in_tunnel_rock(px, py, 1.08):
            continue
        lo, hi, _ = ground_span(c, ter, px, py, radius, n=12)
        if lo is None or hi - lo > flat or lo < cc.WATER_Z + 0.5:
            continue
        return px, py, hi, lo
    return None


def column(b, x, y, z, h, r=0.72, capital=True, mat=STONE):
    """A column of drums from z: a square base, drums, a capital if it's whole."""
    b.box(mat, (x, y, z + 0.25), (1.9, 1.9, 0.5))
    n = max(1, round(h / 1.3))
    for k in range(n):
        dh = min(1.3, h - k * 1.3)
        if dh <= 0.2:
            break
        b.cyl(mat, (x + 0.03 * (k % 2), y, z + 0.5 + k * 1.3), r - 0.03 * k, dh - 0.04, segs=8)
    if capital:
        b.box(GLYPH, (x, y, z + 0.5 + h + 0.3), (2.0, 2.0, 0.6))


def colonnade(c, x, y, z, low, rot, name):
    """A temple porch fallen to ruin: a two-step platform, a row of five columns (two
    still carrying their lintel, one snapped, one a stump), a stretch of back wall with a
    carved band, a column fallen in drums across the front and tumbled blocks."""
    b = Build(c, x, y, z, rot)
    deep = z - low + 1.2
    b.box(STONE, (0, 0, -deep / 2 + 0.15), (25, 10, deep))
    b.box(STONE, (0, 0.8, 0.45), (21.5, 7.4, 0.6))
    b.box(MOSS, (-6.5, -4.2, 0.2), (7.0, 1.6, 0.18))
    top = 0.75
    heights = (6.2, 6.2, 2.9, 6.2, 1.2)
    for i, hgt in enumerate(heights):
        column(b, -9 + 4.5 * i, 0.6, top, hgt, capital=hgt > 6)
    lz = top + 0.5 + 6.2 + 0.6
    b.box(GLYPH, (-6.75, 0.6, lz + 0.55), (6.8, 1.9, 1.1))
    b.box(STONE, (-6.75, 0.6, lz + 1.3), (6.2, 1.5, 0.4))
    # The back wall, broken down to a stepped edge.
    for i, (wx, wl, wh) in enumerate(((-6.0, 9.0, 4.2), (1.5, 6.0, 2.6), (6.5, 4.0, 1.2))):
        b.box(STONE, (wx, 3.6, top + wh / 2), (wl, 1.0, wh))
        b.box(GLYPH, (wx, 3.05, top + wh - 0.55), (wl, 0.12, 0.7))
    # A column fallen across the front: drums lying in a line, a little apart.
    for k in range(4):
        b.cyl(STONE, (3.2 + k * 1.42, -6.6 + 0.12 * k, low - z + 0.62), 0.7, 1.3, tilt=(0, math.pi / 2), rot=0.08 * k)
    b.box(GLYPH, (9.6, -6.2, low - z + 0.4), (2.0, 2.0, 0.6), rot=0.3)
    for k, (bx, by, s) in enumerate(((-11.5, -5.5, 1.5), (-9.6, -6.8, 1.1), (11.4, 2.4, 1.3))):
        b.box(GLYPH, (bx, by, low - z + s * 0.35), (s, s * 0.85, s * 0.9), rot=0.4 * k + 0.2, tilt=(0.18 * (k % 2), 0.12))
    return b.done(name)


def shrine_court(c, x, y, z, low, rot, name):
    """A small walled court: a flagstone floor, low walls broken down in places with a
    gap for the gate, a stepped altar in the middle carrying a carved stele, and a stone
    brazier either side of the gate."""
    b = Build(c, x, y, z, rot)
    deep = z - low + 1.0
    half = 6.5
    b.box(STONE, (0, 0, -deep / 2 + 0.1), (2 * half + 1.2, 2 * half + 1.2, deep))
    for k in range(4):
        b.box(MOSS, (-3 + 2.6 * k, -2 + 1.7 * (k % 2), 0.14), (2.0, 1.8, 0.1))
    walls = [
        ((0, half, 1.1), (2 * half, 1.0, 2.2)),
        ((-half, 1.0, 0.9), (1.0, 2 * half - 2, 1.8)),
        ((half, 2.2, 0.6), (1.0, 2 * half - 4.4, 1.2)),
        ((-half / 2 - 1.2, -half, 0.9), (half - 2.4, 1.0, 1.8)),
        ((half / 2 + 1.2, -half, 0.5), (half - 2.4, 1.0, 1.0)),
    ]
    for (cx, cy, cz), size in walls:
        b.box(STONE, (cx, cy, 0.1 + cz), size)
        b.box(GLYPH, (cx, cy, 0.1 + cz * 2 + 0.15), (size[0] + 0.15, size[1] + 0.15, 0.3))
    # The altar and its stele.
    for k, (w, h) in enumerate(((4.6, 0.6), (3.4, 0.6), (2.3, 0.6))):
        b.box(STONE, (0, 1.0, 0.1 + 0.3 + k * 0.6), (w, w, h))
    b.box(GLYPH, (0, 1.0, 1.9 + 2.3), (1.5, 0.7, 4.6))
    b.box(STONE, (0, 1.0, 1.9 + 4.75), (1.9, 0.9, 0.4))
    # Braziers by the gate, and a tumbled wall block.
    for s in (-1, 1):
        b.cyl(STONE, (s * 2.4, -half - 1.2, 0.1), 0.55, 1.1, segs=8)
        b.cyl(DARK, (s * 2.4, -half - 1.2, 1.2), 0.75, 0.35, r2=0.85, segs=8)
    b.box(STONE, (half + 1.5, -1.5, low - z + 0.5), (1.6, 1.0, 1.0), rot=0.5, tilt=(0.2, 0.1))
    return b.done(name)


def ruined_gate(c, x, y, z, low, rot, name):
    """A ruined gateway: three steps up to two tall carved pillars, one half of the
    lintel still across them and the other half fallen, leaning on the steps."""
    b = Build(c, x, y, z, rot)
    deep = z - low + 1.0
    for k, (w, d) in enumerate(((14.0, 7.0), (12.0, 5.2), (10.0, 3.6))):
        h = (deep if k == 0 else 0.5)
        zc = (-deep / 2 + 0.15) if k == 0 else (0.15 + 0.25 + (k - 1) * 0.5)
        b.box(STONE, (0, 0, zc), (w, d, h))
    top = 1.15
    for s in (-1, 1):
        b.box(STONE, (s * 3.4, 0, top + 4.2), (2.2, 2.2, 8.4))
        for k in range(3):
            b.box(GLYPH, (s * 3.4, 0, top + 1.6 + 2.6 * k), (2.4, 2.4, 0.7))
        b.box(STONE, (s * 3.4, 0, top + 8.7), (2.7, 2.7, 0.6))
    b.box(GLYPH, (-1.6, 0, top + 9.55), (5.6, 2.0, 1.1))
    # The fallen half, leaning from the steps up against the right pillar's foot.
    b.box(GLYPH, (3.0, -4.6, top - 0.2), (5.4, 2.0, 1.1), rot=0.25, tilt=(0.0, -0.42))
    for k, (bx, by) in enumerate(((-6.2, -3.8), (6.8, 2.6), (-5.4, 3.4))):
        b.box(STONE, (bx, by, low - z + 0.45), (1.4, 1.2, 1.1), rot=0.7 * k, tilt=(0.15, 0.1 * k))
    return b.done(name)


def small_temple(c, x, y, z, low, rot, name):
    """A small temple: a three-tier base, a stair up the front between carved ramps, a
    one-room shrine with a dark doorway, a stepped roof and a pierced roof comb."""
    b = Build(c, x, y, z, rot)
    deep = z - low + 1.0
    tiers = ((15.0, 13.0, 1.3), (12.4, 10.6, 1.2), (10.0, 8.4, 1.2))
    zb = 0.0
    b.box(STONE, (0, 0, -deep / 2 + 0.1), (16.0, 14.0, deep))
    for k, (w, d, h) in enumerate(tiers):
        b.box(STONE, (0, 0.4 * k, zb + h / 2), (w, d, h))
        b.box(GLYPH, (0, 0.4 * k - d / 2 - 0.02, zb + h - 0.25), (w * 0.96, 0.1, 0.4))
        zb += h
    # The stair: up the front face to the top tier, with ramps either side.
    steps = 8
    run = 5.6 / steps
    for k in range(steps):
        b.box(STONE, (0, -6.9 + k * run + run / 2, (k + 1) * zb / steps / 2), (3.6, run * (steps - k) * 0.25 + run, (k + 1) * zb / steps))
    for s in (-1, 1):
        b.box(GLYPH, (s * 2.3, -4.6, zb / 2), (0.9, 5.2, 1.0), tilt=(0.6, 0))
    # The shrine.
    sz = zb
    for (cx, cy, w, d) in ((0, 2.6, 8.0, 0.9), (-3.55, 0.4, 0.9, 5.3), (3.55, 0.4, 0.9, 5.3), (-2.45, -1.9, 3.1, 0.9), (2.45, -1.9, 3.1, 0.9)):
        b.box(STONE, (cx, cy + 0.8, sz + 2.1), (w, d, 4.2))
    b.box(DARK, (0, -1.0 + 0.8, sz + 1.5), (1.8, 0.4, 3.0))
    b.box(GLYPH, (0, -1.9 + 0.8, sz + 3.85), (2.2, 1.0, 0.7))
    for k, (w, d) in enumerate(((8.8, 6.6), (7.4, 5.4), (5.8, 4.2))):
        b.box(STONE, (0, 1.2, sz + 4.4 + k * 0.6), (w, d, 0.6))
    for k in range(3):
        b.box(GLYPH, (-1.5 + 1.5 * k, 2.2, sz + 6.8), (0.7, 0.6, 2.4))
    b.box(STONE, (0, 2.2, sz + 8.2), (4.6, 0.7, 0.5))
    return b.done(name)


def great_temple(c, x, y, z, low, rot, name):
    """The great temple on top of the tunnel rock: five stepped tiers, a grand stair up
    the north face between carved balustrades, a shrine on top with three doorways, a
    tall roof comb, and torches. Seen from all over the canyon (scenery only)."""
    b = Build(c, x, y, z, rot)
    deep = z - low + 2.0
    tiers = ((36.0, 30.0, 3.2), (30.0, 25.0, 3.2), (24.4, 20.0, 3.2), (19.0, 15.4, 3.0), (14.0, 11.2, 2.8))
    b.box(STONE, (0, 0, -deep / 2 + 0.2), (38.0, 32.0, deep))
    zb = 0.0
    for k, (w, d, h) in enumerate(tiers):
        b.box(STONE if k % 2 == 0 else MOSS, (0, 0, zb + h / 2), (w, d, h))
        b.box(GLYPH, (0, -d / 2 - 0.05, zb + h - 0.45), (w * 0.9, 0.12, 0.6))
        for s in (-1, 1):
            b.box(GLYPH, (s * (w / 2 + 0.05), 0, zb + h - 0.45), (0.12, d * 0.9, 0.6))
        zb += h
    # The grand stair: up the front from the ground to the top.
    steps = 18
    front = tiers[0][1] / 2
    back = tiers[-1][1] / 2
    for k in range(steps):
        t0 = k / steps
        yk = -front - 1.5 + (front + 1.5 - back) * t0
        b.box(STONE, (0, yk + 0.9, zb * (k + 1) / steps / 2), (6.4, 1.9, zb * (k + 1) / steps))
    slope = math.atan2(zb, front + 1.5 - back)
    ln = math.hypot(zb, front + 1.5 - back)
    for s in (-1, 1):
        b.box(GLYPH, (s * 3.9, (-front - 1.5 - back) / 2, zb / 2 + 0.5), (1.4, ln, 1.2), tilt=(slope, 0))
        b.box(STONE, (s * 3.9, -front - 1.0, 0.9), (1.8, 1.8, 1.8))
    # The shrine on top: three doorways at the front, a stepped roof, a roof comb.
    sz = zb
    b.box(STONE, (0, 1.2, sz + 0.3), (12.0, 8.6, 0.6))
    for (cx, cy, w, d) in ((0, 4.6, 11.0, 1.0), (-5.0, 1.2, 1.0, 7.0), (5.0, 1.2, 1.0, 7.0)):
        b.box(STONE, (cx, cy, sz + 3.1), (w, d, 5.2))
    for cx in (-3.8, -1.25, 1.25, 3.8):
        b.box(STONE, (cx, -2.2, sz + 3.1), (1.5 if abs(cx) > 3 else 1.1, 1.0, 5.2))
    for cx in (-2.5, 0.0, 2.5):
        b.box(DARK, (cx, -1.6, sz + 2.3), (1.3, 0.3, 3.4))
    b.box(GLYPH, (0, -2.3, sz + 5.0), (11.0, 1.2, 1.0))
    for k, (w, d) in enumerate(((12.4, 9.6), (10.6, 8.0), (8.4, 6.2), (6.0, 4.4))):
        b.box(STONE, (0, 1.2, sz + 5.9 + k * 0.7), (w, d, 0.7))
    comb_z = sz + 8.6
    for k in range(5):
        b.box(GLYPH, (-3.2 + 1.6 * k, 2.4, comb_z + 1.6), (0.9, 0.8, 3.2))
    b.box(STONE, (0, 2.4, comb_z + 3.5), (8.0, 0.9, 0.6))
    b.box(GLYPH, (0, 2.4, comb_z + 4.4), (3.2, 0.9, 1.4))
    # Torches on posts at the stair head.
    for s in (-1, 1):
        b.box(STONE, (s * 4.4, -back - 0.5, sz + 1.0), (0.8, 0.8, 2.0))
        b.blob(GLOW, (s * 4.4, -back - 0.5, sz + 2.4), 0.45, sz=1.6, subdiv=0)
    return b.done(name, role="visual"), [b.m @ Vector((s * 4.4, -back - 0.5, sz + 2.6)) for s in (-1, 1)]


def ball_court(c, x, y, z, low, rot, name):
    """An old ball court: a long flagstone alley between two sloped walls, a carved stone
    ring high on each wall, end platforms with steps, one wall partly fallen in."""
    b = Build(c, x, y, z, rot)
    deep = z - low + 1.0
    L = 26.0
    b.box(STONE, (0, 0, -deep / 2 + 0.1), (L + 8, 16.0, deep))
    b.box(MOSS, (0, 0, 0.14), (L - 4, 3.0, 0.1))
    for s in (-1, 1):
        # The bench (a sloped face toward the alley) and the wall above it.
        b.box(STONE, (0, s * 4.6, 0.6), (L, 2.6, 1.2), tilt=(s * 0.0, 0))
        b.box(STONE, (0, s * 5.6, 1.2 + 1.5), (L * (0.7 if s > 0 else 1.0), 1.6, 3.0), rot=0.0)
        b.box(GLYPH, (0, s * 4.75, 1.2 + 2.8), (L * (0.7 if s > 0 else 1.0), 0.15, 0.5))
        b.cyl(GLYPH, (0, s * 4.55, 3.0), 1.0, 0.45, segs=10, r2=1.0, tilt=(math.pi / 2, 0))
        b.cyl(DARK, (0, s * 4.4, 3.0), 0.45, 0.5, segs=8, tilt=(math.pi / 2, 0))
    # Fallen blocks off the broken wall.
    for k in range(4):
        b.box(STONE, (L * 0.35 + 1.4 * k, 6.6 + 0.7 * (k % 2), low - z + 0.55), (1.5, 1.4, 1.1), rot=0.5 * k, tilt=(0.2, 0.15 * k))
    # End platforms with three steps.
    for s in (-1, 1):
        for k in range(3):
            b.box(STONE, (s * (L / 2 + 2.5 - 0.6 * k), 0, 0.25 + 0.5 * k), (5.0 - 1.2 * k, 12.0 - 1.5 * k, 0.5))
    return b.done(name)


def idol_head(c):
    """A colossal carved head (an original design), redone: a broad face with heavy
    cheeks, a deep brow over hollow eyes with stone pupils, a wide flat nose, thick lips
    over a row of teeth, great ear flares with hanging spools, and a tall headdress of
    stepped bands and a fan of carved plumes. Moss on its crown. Faces -Y."""
    name = "Cascade Idol"

    def build(bm):
        cuboid = props.cuboid
        k0 = len(bm.faces)
        cuboid(bm, (0, 0.2, 3.0), (4.8, 4.0, 6.0))  # the head
        cuboid(bm, (0, -1.7, 1.0), (3.6, 0.8, 1.6), tilt=(0.25, 0))  # the jaw and chin
        for s in (-1, 1):
            cuboid(bm, (s * 1.85, -1.75, 2.0), (1.3, 0.8, 1.6), rot=s * 0.35)  # cheeks
        cuboid(bm, (0, -2.0, 4.05), (5.0, 0.9, 0.75))  # brow
        cuboid(bm, (0, -2.25, 2.75), (1.35, 1.0, 1.9), tilt=(-0.22, 0))  # nose
        cuboid(bm, (0, -2.6, 2.05), (1.9, 0.5, 0.6))  # nostrils' wings
        cuboid(bm, (0, -2.3, 1.35), (2.7, 0.55, 0.42))  # upper lip
        cuboid(bm, (0, -2.25, 0.72), (2.4, 0.5, 0.36))  # lower lip
        for s in (-1, 1):
            cuboid(bm, (s * 2.7, 0.0, 2.8), (0.7, 2.0, 2.4))  # ear flares
            cuboid(bm, (s * 2.95, -0.1, 1.2), (0.5, 0.6, 1.4))  # hanging spools
        for k, (w, d, h) in enumerate(((5.6, 4.6, 0.8), (5.0, 4.2, 0.7), (4.2, 3.6, 0.6))):
            cuboid(bm, (0, 0.2, 6.4 + k * 0.7), (w, d, h))  # headdress bands
        for k in range(7):  # the fan of plumes
            a = (k - 3) * 0.28
            cuboid(bm, (math.sin(a) * 2.3, 0.9, 8.6 + math.cos(a) * 1.3), (0.7, 0.4, 3.0), rot=0.0, tilt=(0.0, -a))
        stone = _faces(bm, k0)
        k1 = len(bm.faces)
        cuboid(bm, (0, -2.07, 6.4), (5.4, 0.12, 0.45))  # the band's carving
        for s in (-1, 1):
            cuboid(bm, (s * 1.15, -1.78, 3.35), (1.15, 0.18, 0.7))  # hollow eyes
            cuboid(bm, (s * 0.25, -2.72, 2.0), (0.32, 0.1, 0.25))  # nostrils
        cuboid(bm, (0, -2.4, 1.03), (2.3, 0.1, 0.3))  # the mouth
        dark = _faces(bm, k1)
        k2 = len(bm.faces)
        for s in (-1, 1):
            cuboid(bm, (s * 1.1, -1.95, 3.3), (0.42, 0.2, 0.42))  # pupils
        for k in range(6):
            cuboid(bm, (-1.0 + 0.4 * k, -2.42, 1.03), (0.28, 0.1, 0.24))  # teeth
        pale = _faces(bm, k2)
        k3 = len(bm.faces)
        blob(bm, (0.6, 0.6, 8.0), 1.6, sx=1.4, sz=0.35, subdiv=1)
        blob(bm, (-1.8, -0.4, 4.5), 0.8, sx=1.0, sz=0.5, subdiv=0)
        moss = _faces(bm, k3)
        return [(c.lib("ruin_stone"), stone), (c.lib("ruin_dark"), dark), (c.lib("ruin_glyph"), pale), (c.lib("jungle_leafcover"), moss)]

    return c.proto(name, build) and name


def guardian(c, x, y, z, low, rot, name, mirror=1, scale=1.0):
    """A stone guardian (an original design): a great crouching saurian on a stepped
    plinth, forelegs braced, jaws open, a carved frill fanned behind its head, its tail
    wrapped round the plinth and its eyes glowing like embers. Carved from green jade, so
    it stands out from the grey temple behind it. About 9 m tall (at scale 1)."""
    b = Build(c, x, y, z, rot, scale)
    deep = (z - low) / scale + 1.5
    b.box(STONE, (0, 0, -deep / 2 + 0.2), (6.6, 8.6, deep))
    b.box(GLYPH, (0, 0, 0.45), (6.0, 8.0, 0.5))
    b.box(STONE, (0, 0.2, 1.0), (5.4, 7.4, 0.6))
    top = 1.3
    # Haunches and the body, crouched, rising to the chest.
    for s in (-1, 1):
        b.box(JADE, (s * 1.55, 1.6, top + 1.2), (1.5, 3.2, 2.4), tilt=(0.25, 0))
        b.box(JADE, (s * 1.7, 0.6, top + 0.35), (1.2, 2.2, 0.7))  # hind feet
    b.box(JADE, (0, 0.6, top + 2.4), (3.4, 4.6, 2.6), tilt=(-0.42, 0))
    b.box(JADE, (0, -1.4, top + 3.7), (3.0, 2.0, 2.6), tilt=(-0.2, 0))  # chest
    for s in (-1, 1):
        b.box(JADE, (s * 1.25, -2.3, top + 1.4), (0.95, 1.0, 2.8))  # forelegs
        b.box(JADE, (s * 1.25, -2.75, top + 0.2), (1.3, 1.6, 0.5))  # paws
        for k in range(3):
            b.box(GLYPH, (s * 1.25 + (k - 1) * 0.38, -3.65, top + 0.2), (0.24, 0.5, 0.3))  # claws
    # The neck and head, jaws open toward the road.
    b.box(JADE, (0, -2.1, top + 5.3), (1.9, 1.8, 2.2), tilt=(0.3, 0))
    b.box(JADE, (0, -3.2, top + 6.6), (2.4, 2.6, 1.6))  # skull
    b.box(JADE, (0, -4.9, top + 6.75), (1.7, 2.2, 0.9))  # upper jaw
    b.box(JADE, (0, -4.6, top + 5.55), (1.5, 2.0, 0.55), tilt=(0.35, 0))  # lower jaw, open
    b.box(DARK, (0, -4.6, top + 6.15), (1.3, 1.9, 0.5))  # the mouth
    for k in range(4):
        for zz, dz in ((top + 6.28, -0.2), (top + 5.85, 0.2)):
            b.box(GLYPH, (-0.5 + k * 0.33, -5.4, zz), (0.16, 0.18, 0.32))  # teeth
    b.box(JADE, (0, -3.3, top + 7.55), (2.6, 1.6, 0.4))  # brow ridge
    for s in (-1, 1):
        b.box(GLYPH, (s * 1.0, -3.95, top + 7.1), (0.5, 0.3, 0.38))  # eye rims
        b.blob(GLOW, (s * 1.0, -4.1, top + 7.08), 0.3, subdiv=1)  # glowing eyes
        b.box(JADE, (s * 0.7, -2.4, top + 8.2), (0.4, 0.6, 1.3), tilt=(0.5, s * 0.2))  # horns
    # The frill, a carved fan behind the head.
    for k in range(7):
        a = (k - 3) * 0.32
        b.box(GLYPH, (math.sin(a) * 1.9, -1.9, top + 7.4 + math.cos(a) * 1.4), (0.9, 0.35, 2.4), tilt=(0.0, -a))
    # The tail, curled round the plinth.
    for k in range(7):
        a = -math.pi / 2 + k * 0.42
        r = 3.1
        b.box(JADE, (mirror * r * math.cos(a) * 0.9 + mirror * 0.3, 1.2 + r * math.sin(a) * 1.15 + 3.0, top + 0.45 - 0.02 * k), (1.1 - 0.1 * k, 1.3, 0.9 - 0.08 * k), rot=a)
    return b.done(name, coll="Tunnel")


# ---------------------------------------------------------------- water


def cascade_falls(c, cc, ter, x, name, width=16.0):
    """A great stepped waterfall down the north wall at x: from a notch in the rim, the
    water drops tier by tier (a falls off each rise, a pool on each shelf) to the canyon
    floor, then runs as a stream down across the floor into the river. Returns the
    waterfalls' feet (for the spray and roar)."""
    edge = cc.wall_n(x)
    # Walk out from the rim to the floor, finding each rise (a drop of 4 m or more).
    prof = []
    d = 36.0
    while d >= -2.0:
        prof.append((d, cc.natural(x, edge + d)))
        d -= 0.5
    drops = []
    i = 0
    while i < len(prof) - 1:
        if prof[i][1] - prof[i + 1][1] > 0.35:
            j = i
            while j < len(prof) - 1 and prof[j][1] - prof[j + 1][1] > 0.15:
                j += 1
            if prof[i][1] - prof[j][1] > 4.0:
                drops.append((prof[i][0], prof[i][1], prof[j][0], prof[j][1]))
            i = j
        i += 1
    feet = []
    w = width
    for k, (d0, z0, d1, z1) in enumerate(drops):
        lip_y = edge + d0 + 0.6
        foot = z1 + 0.1
        wt, wb = w, w * 1.12
        fx, fy = props.falls(c, "%s %d" % (name, k + 1), x, lip_y, z0 + 0.25, foot, wt, wb, facing=-1, throw=min(3.5, d0 - d1 + 1.0), bulge=0.8, veils=3, foam_r=wb * 0.55)
        feet.append((fx, fy, foot, z0, wb))
        # The pool on the shelf below (to the next lip), a little wider than the falls.
        nxt = drops[k + 1] if k + 1 < len(drops) else None
        if nxt is not None:
            y0, y1 = edge + d1 - 0.5, edge + nxt[0] + 0.8
            c.ribbon("%s Shelf %d" % (name, k + 1), [(x - 0.01, y0, w * 1.2), (x + 0.01, (y0 + y1) / 2, w * 1.25), (x, y1, w * 1.2)], w * 1.25, z1 + 0.18,
                     c.lib("valley_water"), role="visual", steps=1)
        w *= 1.06
    if not drops:
        return feet
    # The stream: from the last pool, down across the floor to the river.
    fx, fy = feet[-1][0], feet[-1][1]
    ry = cc.river_y(x - 8) + cc.river_half(x - 8) - 2.0
    pts = []
    n = 18
    for k in range(n + 1):
        t = k / n
        px = x - 8 * t + 2.2 * math.sin(t * 5.0)
        py = fy + (ry - fy) * t
        g = c.ground_z(px, py, ter)
        pts.append(Vector((px, py, (g if g is not None else 0.0) + 0.14)))
    rows = []
    along = 0.0
    for k, p in enumerate(pts):
        if k:
            along += (p - pts[k - 1]).length
        q = pts[min(k + 1, n)] - pts[max(k - 1, 0)]
        side = Vector((q.y, -q.x, 0)).normalized()
        hw = 3.2 + 1.4 * (k / n)
        rows.append([(p + side * (u * hw), (u + 1) * hw / 4.0, along / 4.0) for u in (-1.0, -0.5, 0.0, 0.5, 1.0)])
    props.strip(c, name + " Stream", rows, c.lib("valley_water"))
    # Foam where the stream tumbles over a step on its way down.
    for k in range(1, n):
        if pts[k - 1].z - pts[k + 1].z > 1.0:
            c.disc("%s Riffle %d" % (name, k), pts[k].x, pts[k].y, 2.8, pts[k].z + 0.04, c.lib("falls_foam"), role="visual", n=12, wobble=0.25)
    return feet


# ---------------------------------------------------------------- placing it all


SITES = [
    # (name, builder, near (Blender x, y), radius): from Blake's notes 12, 18, 19, 21, 25.
    ("Colonnade", colonnade, (134.3, -49.0), 14.0),
    ("Shrine Court", shrine_court, (-2.8, -27.0), 8.0),
    ("Ruined Gate", ruined_gate, (-112.1, -50.0), 8.0),
    ("Small Temple", small_temple, (-164.7, -32.0), 10.0),
    ("Ball Court", ball_court, (-160.0, 45.4), 17.0),
]


def ruin_sites(c, cc, ter):
    """The composed ruins (instead of pieces scattered at random), each on level ground,
    clear of the road and turned to face it; and the carved heads, facing the road."""
    made = []
    for name, build, (x, y), radius in SITES:
        s = find_site(c, cc, ter, x, y, radius, keep=4.0)
        if s is None:
            print("ruins: no room for", name)
            continue
        px, py, hi, lo = s
        rot = facing_road(c, px, py)
        build(c, px, py, hi + 0.05, lo, rot, name)
        made.append((name, round(px, 1), round(py, 1)))
    head = idol_head(c)
    # (The one Blake pinned, note 13, turns to where he was looking at it from.)
    for i, (x, y, look) in enumerate(((10.0, -62.0, None), (-160.0, 104.0, None), (150.7, -61.0, B(144.34, 3.13, 74.26)))):
        s = find_site(c, cc, ter, x, y, 3.6, keep=3.0, flat=1.6)
        if s is None:
            continue
        px, py, hi, lo = s
        rot = facing_road(c, px, py) if look is None else math.atan2(look[0] - px, -(look[1] - py))
        c.place(head, px, py, lo - 0.5, rot=rot, scale=1.25, coll="Ruins")
        made.append(("Idol", round(px, 1), round(py, 1)))
    return made


def temple_on_rock(c, cc, rock):
    """The great temple on the flat top of the tunnel rock (note 22), facing the canyon."""
    x, y, _ = B(-157.6, 40.0, 100.4)
    zs = [c.ground_z(x + dx, y + dy, [rock]) for dx in (-18, 0, 18) for dy in (-15, 0, 15)]
    zs = [z for z in zs if z is not None]
    if not zs:
        return []
    ob, flames = great_temple(c, x, y, max(zs) + 0.02, min(zs), math.pi, "Great Temple")
    return flames


def tunnel_guardians(c, cc, ter, s, half, facing=1):
    """Two guardians crouched either side of the temple's face (note 16), a little out in
    front, turned toward the karts coming in."""
    # Right in front of the face's great pillars, flanking the mouth (the wall rises
    # straight beside the road here, so further out they'd be buried in it).
    q = c.at(s)
    out = []
    for side in (-1, 1):
        p = q.p + q.r * side * (half + 0.6) - q.t * facing * 5.6
        d = -q.t * facing * math.cos(0.2) + q.r * side * math.sin(0.2)
        rot = math.atan2(d.x, -d.y)
        lo, _, _ = ground_span(c, ter, p.x, p.y, 3.5)
        z = q.p.z - 0.15
        low = min(lo if lo is not None else z - 8.0, z - 1.0)
        guardian(c, p.x, p.y, z, low, rot, "Guardian %d" % ((side + 3) // 2), mirror=side, scale=0.8)
        out.append((round(p.x, 1), round(p.y, 1), round(z, 1)))
    return out


def wall_shelves(c, cc, ter):
    """More green ledges on the bare walls (notes 23, 24): the west end wall and the
    north-west wall, two tiers each, with shrubs, ferns and vines spilling off."""
    bush = props.bush(c, 1)
    fern = props.fern(c)
    vines = [props.vine_curtain(c, v, 7.0 + 3 * v) for v in range(3)]
    # Heights are above the floor in front of the wall (the plateau out west is 8-13 m
    # up), so a shelf is always well up the wall, never a lump at its foot.
    spots = []
    for k in range(7):  # the west end wall, facing east
        y = -40 + 14 * k + 4 * math.sin(k * 1.9)
        spots.append(((-262.0, y), (-1.0, 0.0), 8 + 9 * (k % 2) + 3 * rnd(k)))
    for k in range(7):  # the north-west wall, facing south
        x = -262 + 14 * k + 3 * math.sin(k * 2.3)
        spots.append(((x, cc.wall_n(x) - 8.0), (0.0, 1.0), 8 + 9 * (k % 2) + 3 * rnd(k + 5)))
    spots = [(p, u, cc.natural(*p) + up) for p, u, up in spots]
    made = 0
    for k, ((x0, y0), (ux, uy), target) in enumerate(spots):
        hit = None
        for step in range(90):
            px, py = x0 + ux * step * 0.6, y0 + uy * step * 0.6
            if cc.natural(px, py) >= target:
                hit = (px, py)
                break
        if hit is None or not props.clear_of_road(c, hit[0], hit[1], 10):
            continue
        z = c.ground_z(hit[0], hit[1], ter)
        if z is None:
            continue
        length = 12 + 10 * rnd(k * 5.1)
        depth = 5.0 + 3.0 * rnd(k * 7.3)
        cx, cy = hit[0] - ux * depth * 0.45, hit[1] - uy * depth * 0.45
        ang = math.atan2(uy, ux) + math.pi / 2
        made += 1
        rock = c.rock_mass("Wall Shelf %d" % made, cx, cy, length / 2, depth, z + 0.3, z0=z - 5 - 3 * rnd(k), n=12, seed=k * 3 + 50,
                           bands=[(1.0, 0.0), (1.0, 0.55), (0.96, 0.8), (0.94, 1.0)], angle=ang, base=z - 5)
        c.paint_rock(rock, ("canyon_rock_moss", "wall"), ("jungle_leafcover", "grass"))
        px, py = math.cos(ang), math.sin(ang)
        for m in range(int(length / 3.2)):
            t = (m + 0.5) / max(1, int(length / 3.2)) - 0.5
            c.place(bush if (k + m) % 3 else fern, cx + px * t * length * 0.8, cy + py * t * length * 0.8, z + 0.2, rot=rnd(k * 9 + m) * math.tau,
                    scale=0.8 + 0.5 * rnd(k * 4 + m), coll="Walls", role="visual")
        for j in range(2):
            t = (j - 0.5) * 0.6
            c.place(vines[(k + j) % 3], cx + px * t * length - ux * depth * 0.9, cy + py * t * length - uy * depth * 0.9, z + 0.3,
                    rot=math.atan2(-uy, -ux) - math.pi / 2, coll="Vines", role="visual")
    return made
