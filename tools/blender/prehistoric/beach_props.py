# Beach-party props for the title screen's beach (beach_party.py): umbrellas, towels,
# deck chairs, surfboards, beach balls, sandcastles, tiki torches, a tiki bar, a DJ
# stage, an outrigger canoe, a volleyball net, starfish and shells, and bunting and
# lantern strings slung between the palms.
# SPDX-License-Identifier: MIT
#
# Same rules as props.py: each builder makes one shared mesh through Course.proto, a few
# dozen faces each, all original designs.

import math

from course_kit import Vector, bmesh, rnd
from props import _faces, blob, cuboid, ring, loft, tube

COLOURS = ["party_red", "party_yellow", "party_teal", "party_pink", "party_blue", "party_white"]
PAIRS = [("party_red", "party_white"), ("party_teal", "party_yellow"), ("party_pink", "party_white"), ("party_blue", "party_yellow"), ("party_yellow", "party_red")]


def _slots(c, groups):
    """[(material id, [faces])] -> material slots, skipping empty groups."""
    return [(c.lib(m), f) for m, f in groups if f]


def umbrella(c, variant=0):
    """A beach umbrella: a pole and an eight-panel canopy in two alternating colours."""
    name = "Umbrella %d" % variant
    a_col, b_col = PAIRS[variant % len(PAIRS)]

    def build(bm):
        tilt = 0.18 * (1 if variant % 2 else -1)
        top = Vector((math.sin(tilt) * 2.6, 0, 2.6))
        tube(bm, [(0, 0, -0.4), tuple(top)], 0.05, n=5)
        pole = _faces(bm, 0)
        groups = {a_col: [], b_col: []}
        n = 8
        apex = bm.verts.new(top + Vector((0, 0, 0.55)))
        rim = [bm.verts.new(top + Vector((1.45 * math.cos(k * math.tau / n), 1.45 * math.sin(k * math.tau / n), -0.15))) for k in range(n)]
        for k in range(n):
            k0 = len(bm.faces)
            bm.faces.new((apex, rim[k], rim[(k + 1) % n]))
            # A little scalloped flap under each panel's edge.
            mid = (rim[k].co + rim[(k + 1) % n].co) / 2
            flap = bm.verts.new(mid + Vector((0, 0, -0.18)) + (mid - top).normalized() * 0.08)
            bm.faces.new((rim[k], flap, rim[(k + 1) % n]))
            groups[a_col if k % 2 else b_col].extend(_faces(bm, k0))
        k0 = len(bm.faces)
        blob(bm, tuple(apex.co + Vector((0, 0, 0.05))), 0.09, subdiv=0)
        return [(c.lib("party_white"), pole + _faces(bm, k0))] + _slots(c, groups.items())

    return c.proto(name, build) and name


def towel(c, variant=0):
    """A striped beach towel lying flat on the sand."""
    name = "Towel %d" % variant
    a_col, b_col = PAIRS[(variant + 2) % len(PAIRS)]

    def build(bm):
        groups = {a_col: [], b_col: []}
        for k in range(5):
            k0 = len(bm.faces)
            cuboid(bm, (0, -0.8 + 0.4 * k, 0.03), (1.0, 0.4, 0.04))
            groups[a_col if k % 2 else b_col].extend(_faces(bm, k0))
        return _slots(c, groups.items())

    return c.proto(name, build) and name


def deck_chair(c, variant=0):
    """A wooden deck chair with a striped sling, leaning back toward the sea."""
    name = "Deck Chair %d" % variant
    a_col, _ = PAIRS[(variant + 1) % len(PAIRS)]

    def build(bm):
        for sx in (-0.32, 0.32):
            tube(bm, [(sx, 0.55, 0.0), (sx, 0.1, 0.45), (sx, -0.45, 1.0)], 0.035, n=4)
            tube(bm, [(sx, -0.2, 0.0), (sx, 0.25, 0.4)], 0.03, n=4)
        wood = _faces(bm, 0)
        k0 = len(bm.faces)
        verts = [bm.verts.new(p) for p in ((-0.3, 0.5, 0.12), (0.3, 0.5, 0.12), (0.3, -0.42, 0.95), (-0.3, -0.42, 0.95))]
        mid = [bm.verts.new(p) for p in ((-0.3, 0.05, 0.3), (0.3, 0.05, 0.3))]
        bm.faces.new((verts[0], verts[1], mid[1], mid[0]))
        bm.faces.new((mid[0], mid[1], verts[2], verts[3]))
        return [(c.lib("palm_bark"), wood), (c.lib(a_col), _faces(bm, k0))]

    return c.proto(name, build) and name


def surfboard(c, variant=0):
    """A surfboard stuck nose-up in the sand, painted with a stripe down the middle."""
    name = "Surfboard %d" % variant
    body, stripe = PAIRS[(variant + 3) % len(PAIRS)]

    def build(bm):
        L, Wd = 2.4, 0.32
        n = 10
        front, back = [], []
        for k in range(n + 1):
            t = k / n
            z = -0.5 + L * t
            w = Wd * math.sin(math.pi * (0.06 + 0.9 * t)) ** 0.7
            front.append((bm.verts.new((-w, 0.04, z)), bm.verts.new((w, 0.04, z))))
            back.append((bm.verts.new((-w, -0.04, z)), bm.verts.new((w, -0.04, z))))
        groups = {body: [], stripe: []}
        for k in range(n):
            k0 = len(bm.faces)
            for side, sgn in ((front, 1), (back, -1)):
                a, b = side[k], side[k + 1]
                quad = (a[0], a[1], b[1], b[0]) if sgn > 0 else (a[1], a[0], b[0], b[1])
                bm.faces.new(quad)
            for i in (0, 1):
                quad = (front[k][i], front[k + 1][i], back[k + 1][i], back[k][i])
                bm.faces.new(quad if i else tuple(reversed(quad)))
            groups[stripe if k in (3, 4, 6) else body].extend(_faces(bm, k0))
        return _slots(c, groups.items())

    return c.proto(name, build) and name


def beach_ball(c, variant=0):
    """A beach ball: six gores in three colours and white."""
    name = "Beach Ball %d" % variant
    cols = [COLOURS[(variant + k) % 5] for k in range(3)]

    def build(bm):
        r = 0.45
        res = bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=r)
        for v in res["verts"]:
            v.co.z += r
        groups = {m: [] for m in cols + ["party_white"]}
        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            cen = f.calc_center_median()
            a = (math.atan2(cen.y, cen.x) + math.tau) % math.tau
            gore = int(a / (math.tau / 6))
            groups[cols[gore // 2] if gore % 2 == 0 else "party_white"].append(f.index)
        return _slots(c, groups.items())

    return c.proto(name, build) and name


def sandcastle(c, variant=0):
    """A sandcastle: a mound, a keep and corner towers with cone roofs and a little flag."""
    name = "Sandcastle %d" % variant

    def build(bm):
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=1.6, radius2=1.2, depth=0.5)
        for v in res["verts"]:
            v.co.z += 0.15
        cuboid(bm, (0, 0, 0.85), (1.3, 1.3, 0.9))
        for i in range(4):
            a = i * math.tau / 4 + math.pi / 4
            x, y = 0.95 * math.cos(a), 0.95 * math.sin(a)
            h = 1.2 + 0.25 * ((i + variant) % 2)
            res = bmesh.ops.create_cone(bm, cap_ends=True, segments=7, radius1=0.32, radius2=0.28, depth=h)
            for v in res["verts"]:
                v.co += Vector((x, y, 0.4 + h / 2))
            res = bmesh.ops.create_cone(bm, cap_ends=True, segments=7, radius1=0.38, radius2=0.0, depth=0.5)
            for v in res["verts"]:
                v.co += Vector((x, y, 0.4 + h + 0.25))
        # Crenellations round the keep.
        for i in range(8):
            a = i * math.tau / 8
            cuboid(bm, (0.55 * math.cos(a), 0.55 * math.sin(a), 1.4), (0.18, 0.18, 0.2))
        sand = _faces(bm, 0)
        k0 = len(bm.faces)
        tube(bm, [(0, 0, 1.3), (0, 0, 2.3)], 0.025, n=4)
        pole = _faces(bm, k0)
        k1 = len(bm.faces)
        v = [bm.verts.new(p) for p in ((0, 0, 2.3), (0.45, 0, 2.15), (0, 0, 2.0))]
        bm.faces.new(v)
        return [(c.lib("beach_sand"), sand), (c.lib("palm_bark"), pole), (c.lib(COLOURS[variant % 5]), _faces(bm, k1))]

    return c.proto(name, build) and name


def tiki_torch(c, variant=0):
    """A bamboo tiki torch with a flame on top."""
    name = "Tiki Torch %d" % variant

    def build(bm):
        h = 2.6 + 0.4 * variant
        tube(bm, [(0, 0, -0.4), (0, 0, h)], [0.07, 0.06], n=5)
        for k in range(3):
            cuboid(bm, (0, 0, 0.6 + k * 0.8), (0.17, 0.17, 0.06))
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.1, radius2=0.18, depth=0.3)
        for v in res["verts"]:
            v.co.z += h + 0.1
        wood = _faces(bm, 0)
        k0 = len(bm.faces)
        for k, (r, hh) in enumerate(((0.22, 0.8), (0.14, 0.6))):
            res = bmesh.ops.create_cone(bm, cap_ends=False, segments=5, radius1=r, radius2=0.0, depth=hh)
            for v in res["verts"]:
                v.co += Vector((0.03 * k, 0, h + 0.25 + hh / 2))
        return [(c.lib("palm_bark"), wood), (c.lib("campfire_flame"), _faces(bm, k0))]

    return c.proto(name, build) and name


def tiki_bar(c):
    """A thatched tiki bar: carved posts, a counter with coconut cups, stools and a sign."""
    name = "Tiki Bar"

    def build(bm):
        posts = []
        for x in (-2.6, 2.6):
            for y in (-1.6, 1.6):
                k0 = len(bm.faces)
                cuboid(bm, (x, y, 1.5), (0.4, 0.4, 3.0))
                posts += _faces(bm, k0)
        k0 = len(bm.faces)
        cuboid(bm, (0, -1.2, 0.55), (4.6, 0.7, 1.1))
        cuboid(bm, (0, -1.3, 1.15), (5.0, 1.0, 0.12))
        counter = _faces(bm, k0)
        k0 = len(bm.faces)
        # The thatched roof: a low hip roof with a ridge.
        base = [bm.verts.new(p) for p in ((-3.6, -2.5, 3.0), (3.6, -2.5, 3.0), (3.6, 2.5, 3.0), (-3.6, 2.5, 3.0))]
        ridge = [bm.verts.new(p) for p in ((-1.4, 0, 4.6), (1.4, 0, 4.6))]
        bm.faces.new((base[0], base[1], ridge[1], ridge[0]))
        bm.faces.new((base[2], base[3], ridge[0], ridge[1]))
        bm.faces.new((base[1], base[2], ridge[1]))
        bm.faces.new((base[3], base[0], ridge[0]))
        bm.faces.new(list(reversed(base)))
        roof = _faces(bm, k0)
        k0 = len(bm.faces)
        for i, x in enumerate((-1.8, -0.6, 0.6, 1.8)):
            tube(bm, [(x, -2.2, 0.0), (x, -2.2, 0.75)], 0.07, n=4)
            res = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.28, radius2=0.28, depth=0.1)
            for v in res["verts"]:
                v.co += Vector((x, -2.2, 0.8))
        stools = _faces(bm, k0)
        k0 = len(bm.faces)
        for i, x in enumerate((-1.5, -0.3, 1.1)):
            blob(bm, (x, -1.35, 1.32), 0.14, subdiv=0)
        cups = _faces(bm, k0)
        k0 = len(bm.faces)
        cuboid(bm, (0, -2.55, 3.35), (2.6, 0.12, 0.6))
        sign = _faces(bm, k0)
        return [(c.lib("tiki_wood"), posts + counter), (c.lib("thatch"), roof), (c.lib("palm_bark"), stools + cups), (c.lib("party_teal"), sign)]

    return c.proto(name, build) and name


def stage(c):
    """The DJ stage: a wooden deck with steps, a bamboo frame, a thatched awning, speaker
    stacks either side and a booth at the front."""
    name = "Party Stage"

    def build(bm):
        cuboid(bm, (0, 0, 0.5), (10.0, 6.0, 1.0))
        for k in range(3):
            cuboid(bm, (0, -3.3 - k * 0.4, 0.33 - k * 0.15), (3.0, 0.4, 0.66 - k * 0.3))
        deck = _faces(bm, 0)
        k0 = len(bm.faces)
        for x in (-4.6, 4.6):
            for y in (-2.6, 2.6):
                tube(bm, [(x, y, 1.0), (x, y, 5.2)], 0.14, n=5)
        tube(bm, [(-4.8, -2.6, 5.2), (4.8, -2.6, 5.2)], 0.12, n=5)
        tube(bm, [(-4.8, 2.6, 5.2), (4.8, 2.6, 5.2)], 0.12, n=5)
        frame = _faces(bm, k0)
        k0 = len(bm.faces)
        for dz in (0.0, -0.08):
            a = [bm.verts.new((x, y, z + dz)) for x, y, z in ((-5.4, -3.2, 5.1), (5.4, -3.2, 5.1), (5.4, 3.2, 5.9), (-5.4, 3.2, 5.9))]
            bm.faces.new(a if dz == 0 else list(reversed(a)))
        roof = _faces(bm, k0)
        k0 = len(bm.faces)
        for x in (-4.0, 4.0):
            cuboid(bm, (x, -1.0, 1.9), (1.4, 1.2, 1.8))
            cuboid(bm, (x, -1.0, 3.3), (1.1, 1.0, 1.0))
        cuboid(bm, (0, -1.4, 1.55), (2.6, 1.0, 1.1))
        boxes = _faces(bm, k0)
        k0 = len(bm.faces)
        # Speaker cones and the booth's lights.
        for x in (-4.0, 4.0):
            for z, r in ((1.55, 0.45), (2.4, 0.3), (3.3, 0.32)):
                res = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=r, radius2=r * 0.6, depth=0.12)
                for v in res["verts"]:
                    v.co = Vector((v.co.x + x, -1.62 - v.co.z, v.co.y + z))
        cones = _faces(bm, k0)
        k0 = len(bm.faces)
        for i, x in enumerate((-0.9, -0.3, 0.3, 0.9)):
            cuboid(bm, (x, -1.92, 1.75), (0.4, 0.06, 0.3))
        lights = _faces(bm, k0)
        return [
            (c.lib("wood_planks"), deck),
            (c.lib("palm_bark"), frame),
            (c.lib("thatch"), roof),
            (c.lib("ruin_dark"), boxes),
            (c.lib("party_white"), cones),
            (c.lib("lantern_glow"), lights),
        ]

    return c.proto(name, build) and name


def canoe(c, variant=0):
    """An outrigger canoe pulled up on the sand, with a paddle across it."""
    name = "Canoe %d" % variant

    def build(bm):
        L = 5.5
        rings_ = []
        for k in range(9):
            t = k / 8
            x = (t - 0.5) * L
            w = 0.45 * math.sin(math.pi * t) ** 0.6 + 0.02
            rings_.append([bm.verts.new((x, w * math.cos(a), 0.45 + 0.4 * math.sin(a) * (1 if a < 0 else 0.2) + 0.15 * (2 * t - 1) ** 4)) for a in [math.pi + i * math.pi / 5 for i in range(6)]])
        for lo, hi in zip(rings_, rings_[1:]):
            for i in range(5):
                bm.faces.new((lo[i], lo[i + 1], hi[i + 1], hi[i]))
        hull = _faces(bm, 0)
        k0 = len(bm.faces)
        tube(bm, [(-1.0, 0, 0.75), (-1.0, 1.9, 0.6)], 0.05, n=4)
        tube(bm, [(1.0, 0, 0.75), (1.0, 1.9, 0.6)], 0.05, n=4)
        tube(bm, [(-2.0, 1.9, 0.25), (2.0, 1.9, 0.25)], [0.1, 0.12], n=5)
        tube(bm, [(-0.6, -0.9, 0.9), (1.0, 0.9, 0.9)], 0.03, n=4)
        blob(bm, (1.1, 1.0, 0.9), 0.2, sx=1.6, sz=0.3, subdiv=0)
        wood = _faces(bm, k0)
        return [(c.lib("dino_scales" if variant % 2 else "tribal_paint"), hull), (c.lib("palm_bark"), wood)]

    return c.proto(name, build) and name


def volley_net(c):
    """Two poles and a net (a grid of cords) for beach volleyball."""
    name = "Volley Net"

    def build(bm):
        for x in (-4.5, 4.5):
            tube(bm, [(x, 0, -0.3), (x, 0, 2.6)], 0.07, n=5)
        poles = _faces(bm, 0)
        k0 = len(bm.faces)
        for z in (1.6, 2.0, 2.4):
            tube(bm, [(-4.5, 0, z), (4.5, 0, z)], 0.02, n=3)
        for k in range(13):
            x = -4.2 + 8.4 * k / 12
            tube(bm, [(x, 0, 1.6), (x, 0, 2.4)], 0.015, n=3)
        net = _faces(bm, k0)
        return [(c.lib("party_white"), poles), (c.lib("party_white"), net)]

    return c.proto(name, build) and name


def starfish(c, variant=0):
    name = "Starfish %d" % variant

    def build(bm):
        cen = bm.verts.new((0, 0, 0.06))
        tips, valleys = [], []
        for k in range(5):
            a = k * math.tau / 5
            tips.append(bm.verts.new((0.32 * math.cos(a), 0.32 * math.sin(a), 0.02)))
            b = a + math.tau / 10
            valleys.append(bm.verts.new((0.11 * math.cos(b), 0.11 * math.sin(b), 0.04)))
        for k in range(5):
            bm.faces.new((cen, valleys[k - 1], tips[k]))
            bm.faces.new((cen, tips[k], valleys[k]))
        return [(c.lib(["party_red", "party_pink", "party_yellow"][variant % 3]), _faces(bm, 0))]

    return c.proto(name, build) and name


def shell(c):
    name = "Shell"

    def build(bm):
        blob(bm, (0, 0, 0.05), 0.15, sx=1.0, sy=0.8, sz=0.45, subdiv=1)
        return [(c.lib("party_white"), _faces(bm, 0))]

    return c.proto(name, build) and name


def drum(c):
    """A big bongo drum by the bonfire."""
    name = "Bongo"

    def build(bm):
        rings_ = [ring(bm, (0, 0), r, z, 10) for r, z in ((0.32, 0.0), (0.38, 0.35), (0.3, 0.75), (0.34, 0.9))]
        loft(bm, rings_, cap_top=False)
        wood = _faces(bm, 0)
        k0 = len(bm.faces)
        bm.faces.new(rings_[-1])
        return [(c.lib("tiki_wood"), wood), (c.lib("party_white"), _faces(bm, k0))]

    return c.proto(name, build) and name


def string_line(c, name, p0, p1, sag, kind="bunting", coll="Party"):
    """A cord slung between two points (palm to palm), hung with triangle flags in
    alternating party colours ("bunting") or glowing paper lanterns ("lanterns")."""
    bm = bmesh.new()
    a, b = Vector(p0), Vector(p1)
    n = max(6, int((b - a).length / 1.2))
    pts = []
    for k in range(n + 1):
        t = k / n
        p = a.lerp(b, t)
        p.z -= sag * 4 * t * (1 - t)
        pts.append(p)
    tube(bm, [tuple(p) for p in pts], 0.025, n=3)
    groups = {"palm_bark": _faces(bm, 0)}
    across = (b - a).normalized()
    for k in range(1, n):
        p = pts[k]
        k0 = len(bm.faces)
        if kind == "bunting":
            nrm = across.cross(Vector((0, 0, 1))).normalized() * 0.02
            for o in (nrm, -nrm):
                v = [bm.verts.new(q + o) for q in (p - across * 0.35, p + across * 0.35, p + Vector((0, 0, -0.75)))]
                bm.faces.new(v if o is nrm else list(reversed(v)))
            mat = COLOURS[k % 5]
        else:
            blob(bm, tuple(p + Vector((0, 0, -0.35))), 0.24, sx=1.0, sy=1.0, sz=1.25, subdiv=0)
            mat = "lantern_glow" if k % 3 else ["party_pink", "party_teal", "party_yellow"][k % 3]
        groups.setdefault(mat, []).extend(_faces(bm, k0))
    ob = c.mesh_object(name, bm, coll, "visual")
    for mat, faces in groups.items():
        c.assign(ob, c.lib(mat), faces)
    ob.data.shade_flat()
    return ob


def coconut_palm(c, variant=0):
    """A tall, curving coconut palm with coconuts under the crown (bigger and bendier
    than props.palm, for the beach)."""
    name = "Coconut Palm %d" % variant

    def build(bm):
        h = 11.0 + 2.0 * variant
        lean = 3.0 + 1.2 * variant
        rings_ = []
        top = None
        for k in range(11):
            t = k / 10
            x = lean * t * t + 0.25 * math.sin(variant + t * 4)
            rings_.append(ring(bm, (x, 0), 0.38 - 0.14 * t, h * t, 6))
            top = Vector((x, 0, h * t))
        loft(bm, rings_)
        bark = _faces(bm, 0)
        k0 = len(bm.faces)
        from props import frond

        for i in range(9):
            a = i * math.tau / 9 + variant
            frond(bm, tuple(top), a, 4.6 + 0.8 * rnd(i + variant), 2.8, 0.75, segs=5)
        leaves = _faces(bm, k0)
        k0 = len(bm.faces)
        for i in range(4):
            a = i * math.tau / 4 + 0.4
            blob(bm, tuple(top + Vector((0.35 * math.cos(a), 0.35 * math.sin(a), -0.45))), 0.24, subdiv=0)
        nuts = _faces(bm, k0)
        return [(c.lib("palm_bark"), bark + nuts), (c.lib("palm_frond"), leaves)]

    return c.proto(name, build) and name


def bamboo_pole(c):
    """A tall bamboo pole for hanging lantern strings, with a lantern at the top."""
    name = "Bamboo Pole"

    def build(bm):
        tube(bm, [(0, 0, -0.3), (0, 0, 6.3)], [0.09, 0.07], n=5)
        for k in range(4):
            cuboid(bm, (0, 0, 1.2 + k * 1.4), (0.21, 0.21, 0.06))
        pole = _faces(bm, 0)
        k0 = len(bm.faces)
        blob(bm, (0, 0, 6.5), 0.3, sz=1.2, subdiv=0)
        return [(c.lib("palm_bark"), pole), (c.lib("lantern_glow"), _faces(bm, k0))]

    return c.proto(name, build) and name
