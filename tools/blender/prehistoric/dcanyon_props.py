# Dragon Canyon's props: sandstone spires and buttes, braziers and turn boards, the
# outpost's fortress walls and towers, the watchtower, the dragon's skull, ribs and
# vertebrae, the quarry's cranes, block stacks, scaffolds, carts, tents and cargo lift,
# the sealed chambers' glowing doors and an aqueduct. Dragon Isles' buildings, statues,
# banners and lanterns (isles_props.py) are reused. Each builds one mesh (a prototype)
# that every copy shares; origins at the ground, fronts face +Y. All our own designs.
# SPDX-License-Identifier: MIT

import math

from canyon_props import _beam, _cyl
from course_kit import Vector, bmesh, rnd
from isles_props import _box, _p, fit_uvs, pillars, roof, ridge
from props import _faces, blob, cuboid, loft, ring, tube


# ------------------------------------------------------------------ rock


def spire(c, variant=0, height=60.0):
    """A sandstone spire: banded, stepped where harder layers stand out, narrowing to a
    flat cap. `height` m tall; about a sixth as wide."""
    name = "Spire %d %g" % (variant, height)

    def build(bm):
        n = 9
        rings = []
        w = height / 6.0
        steps = [(-8.0, 1.25), (0.0, 1.15), (0.18, 1.0), (0.2, 0.86), (0.42, 0.84), (0.44, 0.74), (0.66, 0.72), (0.68, 0.6),
                 (0.86, 0.56), (0.9, 0.48), (1.0, 0.44)]
        k = len(bm.faces)
        for j, (f, s) in enumerate(steps):
            z = f if f < 0 else f * height
            rg = []
            for i in range(n):
                a = i * math.tau / n
                r = w * s * (1 + 0.14 * math.sin(2 * a + variant * 1.7 + j * 0.3) + 0.1 * (rnd(variant * 17 + i * 5 + j) - 0.5))
                rg.append(bm.verts.new((r * math.cos(a), r * 0.8 * math.sin(a), z)))
            rings.append(rg)
        loft(bm, rings, cap_top=True)
        walls = _faces(bm, k)
        top = [walls[-1]]
        return [(c.lib("canyon_cliff"), walls[:-1]), (c.lib("canyon_ledge"), top)]

    return _p(c, name, build)


def butte(c, variant=0):
    """A broad flat-topped butte: 40 m tall, ~70 m across (scale it)."""
    name = "Butte %d" % variant

    def build(bm):
        n = 14
        rings = []
        prof = [(-10.0, 1.1), (0.0, 1.05), (14.0, 0.92), (15.0, 0.84), (30.0, 0.8), (31.0, 0.74), (40.0, 0.72)]
        for j, (z, s) in enumerate(prof):
            rg = []
            for i in range(n):
                a = i * math.tau / n
                r = 35.0 * s * (1 + 0.12 * math.sin(3 * a + variant) + 0.08 * (rnd(variant * 7 + i * 3 + j) - 0.5))
                rg.append(bm.verts.new((r * math.cos(a), r * 0.75 * math.sin(a), z)))
            rings.append(rg)
        loft(bm, rings, cap_top=True)
        f = _faces(bm, 0)
        return [(c.lib("canyon_cliff_shade" if variant % 2 else "canyon_cliff"), f[:-1]), (c.lib("canyon_ledge"), f[-1:])]

    return _p(c, name, build)


# ------------------------------------------------------------------ the road's furniture


def brazier(c):
    """A stone pedestal with an iron fire bowl on top, burning."""
    name = "Brazier"

    def build(bm):
        k = len(bm.faces)
        _box(bm, -0.5, -0.5, -0.3, 0.5, 0.5, 1.1)
        _box(bm, -0.6, -0.6, 1.1, 0.6, 0.6, 1.3)
        stone = _faces(bm, k)
        k = len(bm.faces)
        loft(bm, [ring(bm, (0, 0), 0.3, 1.3, 8), ring(bm, (0, 0), 0.75, 1.75, 8), ring(bm, (0, 0), 0.7, 1.9, 8)], cap_top=False, cap_bottom=True)
        iron = _faces(bm, k)
        k = len(bm.faces)
        for i, (r, h) in enumerate(((0.55, 1.2), (0.35, 1.6))):
            res = bmesh.ops.create_cone(bm, cap_ends=False, segments=5, radius1=r, radius2=0.0, depth=h)
            for v in res["verts"]:
                v.co += Vector((0.08 * i, 0.05 * i, 1.8 + h / 2))
        fire = _faces(bm, k)
        return [(c.lib("fortress_wall"), stone), (c.lib("iron"), iron), (c.lib("brazier_fire"), fire)]

    return _p(c, name, build)


BRAZIER_LIGHT = (0.0, 0.0, 2.4)


def chevron_board(c, length=8.0):
    """A turn board on two posts: red and white arrows along +X (turn it to point round
    the corner)."""
    name = "Chevron %g" % length
    face = []

    def build(bm):
        k = len(bm.faces)
        for x in (-length / 2 + 0.4, length / 2 - 0.4):
            _beam(bm, (x, 0.15, -0.5), (x, 0.15, 2.4), 0.2)
        wood = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -length / 2, -0.06, 0.9, length / 2, 0.06, 2.5)
        face.extend(_faces(bm, k))
        return [(c.lib("weathered_timber"), wood), (c.lib("chevron_canyon"), face)]

    if name not in c.protos:
        _p(c, name, build)
    return name


# ------------------------------------------------------------------ fortifications


def fort_wall(c, length=16.0, h=8.0):
    """A fortress wall along X with a crenellated walkway on top."""
    name = "Fort Wall %g %g" % (length, h)

    def build(bm):
        k = len(bm.faces)
        _box(bm, -length / 2, -1.6, -4.0, length / 2, 1.6, h)
        n = int(length / 2.0)
        for i in range(n):
            if i % 2 == 0:
                x = -length / 2 + (i + 0.5) * length / n
                _box(bm, x - 0.5, -1.6, h, x + 0.5, -1.0, h + 1.2)
        return [(c.lib("fortress_wall"), _faces(bm, k))]

    return _p(c, name, build)


def fort_tower(c, h=16.0, w=7.0, roof_mat="roof_blue"):
    """A square fortress tower: battered stone base, a red-pillared lookout under a
    hipped roof."""
    name = "Fort Tower %g %g %s" % (h, w, roof_mat)

    def build(bm):
        k = len(bm.faces)
        loft(bm, [ring(bm, (0, 0), w * 0.78, -4.0, 4, phase=math.pi / 4), ring(bm, (0, 0), w * 0.72, 3.0, 4, phase=math.pi / 4),
                  ring(bm, (0, 0), w * 0.62, h, 4, phase=math.pi / 4)], cap_top=True)
        _box(bm, -w * 0.52, -w * 0.52, h, w * 0.52, w * 0.52, h + 0.6)
        stone = _faces(bm, k)
        red = pillars(bm, (-w * 0.38, w * 0.38), (-w * 0.38, w * 0.38), h + 0.6, h + 3.8, r=0.25)
        k = len(bm.faces)
        _box(bm, -w * 0.45, -w * 0.45, h + 0.6, w * 0.45, w * 0.45, h + 1.5)
        red += _faces(bm, k)
        roofs = roof(bm, 0, 0, h + 3.8, w * 0.8, w * 0.8, w * 0.42, over=1.0, curl=0.7)
        gold = ridge(bm, 0, 0, h + 3.8 + w * 0.42, w * 0.8, w * 0.8, 1.0)
        return [(c.lib("fortress_wall"), stone), (c.lib("red_lacquer"), red), (c.lib(roof_mat), roofs), (c.lib("isle_gold"), gold)]

    return _p(c, name, build)


def watchtower(c):
    """The imperial watchtower: a tall tapering stone shaft, two balconies of red pillars
    under upswept jade roofs, banners hanging down its face, a gold finial. 34 m."""
    name = "Watchtower"
    cloth = []

    def build(bm):
        k = len(bm.faces)
        loft(bm, [ring(bm, (0, 0), 8.0, -6.0, 8, phase=math.pi / 8), ring(bm, (0, 0), 7.0, 2.0, 8, phase=math.pi / 8),
                  ring(bm, (0, 0), 5.2, 22.0, 8, phase=math.pi / 8)], cap_top=True)
        _cyl(bm, 0, 0, 22.0, 22.8, 6.4, 6.4, n=8, phase=math.pi / 8)
        _cyl(bm, 0, 0, 29.0, 29.6, 4.6, 4.6, n=8, phase=math.pi / 8)
        stone = _faces(bm, k)
        red = []
        for z0, z1, r in ((22.8, 26.0, 5.6), (29.6, 32.2, 3.8)):
            k = len(bm.faces)
            for i in range(8):
                a = i * math.tau / 8 + math.pi / 8
                _cyl(bm, math.cos(a) * r, math.sin(a) * r, z0, z1, 0.28, 0.28, n=5)
            _cyl(bm, 0, 0, z0, z1 - 0.2, r * 0.75, r * 0.75, n=8)
            red += _faces(bm, k)
        roofs = roof(bm, 0, 0, 26.0, 11.0, 11.0, 3.0, over=1.6, curl=1.0)
        roofs += roof(bm, 0, 0, 32.2, 7.5, 7.5, 3.6, over=1.2, curl=0.9)
        k = len(bm.faces)
        _cyl(bm, 0, 0, 35.6, 39.5, 0.3, 0.06, n=6)
        blob(bm, (0, 0, 36.2), 0.6)
        gold = _faces(bm, k)
        k = len(bm.faces)
        for a in (0.0, math.pi):
            ca, sa = math.cos(a), math.sin(a)
            for t in (-1, 1):
                pts = [(-2.0, 6.0, 21.0), (2.0, 6.0, 21.0), (2.0, 6.4, 8.0), (-2.0, 6.4, 8.0)]
                vs = [bm.verts.new((x * ca - y * sa * t, x * sa + y * ca * t, z)) for x, y, z in pts]
                bm.faces.new(vs if t > 0 else list(reversed(vs)))
        cloth.extend(_faces(bm, k))
        return [(c.lib("fortress_wall"), stone), (c.lib("red_lacquer"), red), (c.lib("roof_jade"), roofs), (c.lib("isle_gold"), gold),
                (c.lib("banner_royal"), cloth)]

    if name not in c.protos:
        _p(c, name, build)
        fit_uvs(c, name, cloth)
    return name


# ------------------------------------------------------------------ the dragon's bones


def skull(c):
    """A colossal dragon skull (about 30 m long), its snout toward +Y, jaw a little open,
    horns swept back, half buried."""
    name = "Dragon Skull"

    def build(bm):
        k = len(bm.faces)
        blob(bm, (0, -4, 8), 9.0, 1.1, 1.0, 0.85, subdiv=2)  # the cranium
        bone = _faces(bm, k)
        # The snout: a loft made along Z, turned to run along +Y.
        k2 = len(bm.faces)
        loft(bm, [ring(bm, (0, 0), 3.0, 0.0, 8), ring(bm, (0, 0), 2.6, 15.0, 8), ring(bm, (0, 0), 1.6, 22.0, 8)], cap_top=True)
        snout = _faces(bm, k2)
        verts = {v for i in snout for v in bm.faces[i].verts}
        for v in verts:
            x, y, z = v.co
            v.co = Vector((x, z + 2.0, 8.0 + y * 0.9 - z * 0.12))
        k3 = len(bm.faces)
        loft(bm, [ring(bm, (0, 0), 2.2, 0.0, 6), ring(bm, (0, 0), 2.0, 18.0, 6)], cap_top=True)
        jaw = _faces(bm, k3)
        verts = {v for i in jaw for v in bm.faces[i].verts}
        for v in verts:
            x, y, z = v.co
            v.co = Vector((x * 1.4, z + 1.0, 2.2 + y * 0.7 - z * 0.05))
        bone += snout + jaw
        k = len(bm.faces)
        for s in (-1, 1):
            tube(bm, [(s * 6.0, -6.0, 13.0), (s * 9.0, -13.0, 17.0), (s * 9.5, -22.0, 16.0), (s * 8.0, -27.0, 12.0)], [1.8, 1.4, 0.8, 0.2], n=6)
            for i in range(6):
                tube(bm, [(s * 1.2, 22.0 - i * 3.2, 6.5), (s * 1.3, 22.0 - i * 3.2, 4.4)], [0.45, 0.05], n=4)  # teeth
        horns = _faces(bm, k)
        k = len(bm.faces)
        for s in (-1, 1):
            loft(bm, [ring(bm, (s * 3.6, 3.0), 1.8, 9.5, 6), ring(bm, (s * 3.6, 3.0), 1.4, 10.2, 6)], cap_top=True)
        sockets = _faces(bm, k)
        return [(c.lib("bone_ivory"), bone + horns), (c.lib("dark_corridor"), sockets)]

    return _p(c, name, build)


def rib(c, span=22.0, height=14.0, variant=0):
    """One rib of the dragon's skeleton arching over the road (feet at x = ±span/2)."""
    name = "Rib %g %g %d" % (span, height, variant)

    def build(bm):
        pts = []
        radii = []
        lean = (variant % 3 - 1) * 1.2
        for i in range(13):
            t = i / 12
            a = math.pi * t
            pts.append((-math.cos(a) * span / 2, lean * math.sin(a), -2.0 + (height + 2.0) * math.sin(a) ** 0.8))
            radii.append(1.1 - 0.35 * math.sin(a))
        tube(bm, pts, radii, n=6)
        return [(c.lib("bone_ivory"), _faces(bm, 0))]

    return _p(c, name, build)


def vertebra(c):
    """One vertebra of the spine: a bony disc with a tall spike."""
    name = "Vertebra"

    def build(bm):
        _cyl(bm, 0, 0, 0.0, 2.6, 2.2, 1.9, n=7)
        tube(bm, [(0, 0, 2.4), (0, -0.6, 6.0), (0, -1.8, 8.5)], [1.0, 0.6, 0.1], n=5)
        for s in (-1, 1):
            tube(bm, [(s * 1.6, 0, 1.6), (s * 4.0, 0.2, 2.4)], [0.6, 0.15], n=4)
        return [(c.lib("bone_ivory"), _faces(bm, 0))]

    return _p(c, name, build)


# ------------------------------------------------------------------ the quarry


def block_stack(c, variant=0):
    """Cut sandstone blocks stacked for shipping."""
    name = "Block Stack %d" % variant

    def build(bm):
        k = len(bm.faces)
        for i in range(3 + variant % 3):
            for j in range(3 - i // 2):
                if rnd(variant * 7 + i * 3 + j) < 0.25 and i:
                    continue
                cuboid(bm, (-2.4 + j * 2.4 + (i % 2) * 1.2, 0.0, 0.7 + i * 1.4), (2.2, 1.6, 1.35), rot=0.04 * (rnd(i + j + variant) - 0.5))
        return [(c.lib("sandstone_block"), _faces(bm, k))]

    return _p(c, name, build)


def crane(c):
    """A timber treadwheel crane: a braced mast, a long jib (along +Y from the mast's top)
    and its rope; the block it lifts swings in the game. Mast 14 m; the jib reaches 10 m
    out at 13 m up."""
    name = "Quarry Crane"

    def build(bm):
        k = len(bm.faces)
        for x, y in ((-1.6, -1.6), (1.6, -1.6), (-1.6, 1.6), (1.6, 1.6)):
            _beam(bm, (x * 1.5, y * 1.5, -0.5), (x * 0.3, y * 0.3, 14.0), 0.35)
        for z in (3.0, 7.0, 11.0):
            s = 1.0 - z / 16.0
            _beam(bm, (-2.4 * s, -2.4 * s, z), (2.4 * s, 2.4 * s, z), 0.22)
            _beam(bm, (2.4 * s, -2.4 * s, z), (-2.4 * s, 2.4 * s, z), 0.22)
        _beam(bm, (0, -3.0, 13.0), (0, 10.5, 13.6), 0.4)
        _beam(bm, (0, 0, 14.0), (0, 10.0, 13.7), 0.15)
        _beam(bm, (0, 0, 14.0), (0, -3.0, 13.2), 0.15)
        wood = _faces(bm, k)
        k = len(bm.faces)
        # The treadwheel at the foot.
        for side in (-0.6, 0.6):
            pts = [(side, -3.5 + 2.6 * math.cos(a), 2.8 + 2.6 * math.sin(a)) for a in [i * math.tau / 12 for i in range(13)]]
            tube(bm, pts, 0.14, n=4)
        wheel = _faces(bm, k)
        k = len(bm.faces)
        cuboid(bm, (0, -3.0, 12.6), (1.6, 1.6, 1.2))
        counter = _faces(bm, k)
        return [(c.lib("scaffold_timber"), wood + wheel), (c.lib("sandstone_block"), counter)]

    return _p(c, name, build)


CRANE_TIP = (0.0, 10.0, 13.4)


def scaffold(c, w=10.0, h=12.0):
    """A timber scaffold against a cliff (its back on the cliff, the face toward +Y):
    posts, ledgers, braces, plank decks, a ladder."""
    name = "Scaffold %g %g" % (w, h)

    def build(bm):
        k = len(bm.faces)
        xs = [-w / 2 + i * w / 3 for i in range(4)]
        for x in xs:
            for y in (0.0, 2.6):
                _beam(bm, (x, y, -0.5), (x, y, h), 0.2)
        z = 3.0
        while z < h:
            _beam(bm, (-w / 2, 2.6, z), (w / 2, 2.6, z), 0.16)
            _box(bm, -w / 2, 0.0, z - 0.1, w / 2, 2.6, z + 0.08)
            for i in range(3):
                _beam(bm, (xs[i], 2.6, z - 3.0), (xs[i + 1], 2.6, z), 0.1)
            z += 3.0
        _beam(bm, (w / 2 - 0.6, 3.0, 0.0), (w / 2 - 0.2, 3.0, h), 0.1)
        return [(c.lib("scaffold_timber"), _faces(bm, k))]

    return _p(c, name, build)


def cart(c, variant=0):
    """A two-wheeled cart loaded with blocks (its shafts toward +Y)."""
    name = "Cart %d" % variant

    def build(bm):
        k = len(bm.faces)
        _box(bm, -1.0, -1.6, 0.8, 1.0, 1.6, 1.1)
        for s in (-1, 1):
            _beam(bm, (s * 0.6, 1.4, 0.95), (s * 0.5, 3.4, 0.6), 0.12)
        wood = _faces(bm, k)
        k = len(bm.faces)
        for s in (-1, 1):
            rg = [bm.verts.new((s * 1.15, 0.8 * math.cos(a), 0.8 + 0.8 * math.sin(a))) for a in [i * math.tau / 10 for i in range(10)]]
            bm.faces.new(rg if s > 0 else list(reversed(rg)))
        wheels = _faces(bm, k)
        k = len(bm.faces)
        for i in range(1 + variant % 2):
            cuboid(bm, (0.0, -0.6 + i * 1.3, 1.65), (1.5, 1.1, 1.1))
        load = _faces(bm, k)
        return [(c.lib("scaffold_timber"), wood), (c.lib("barrel_wood"), wheels), (c.lib("sandstone_block"), load)]

    return _p(c, name, build)


def tent(c, variant=0):
    """A workers' canvas awning on poles."""
    name = "Tent %d" % variant
    cloth_mat = ("canvas_sun", "canvas_torn", "awning_red")[variant % 3]

    def build(bm):
        k = len(bm.faces)
        for x in (-2.5, 2.5):
            for y in (-2.0, 2.0):
                _beam(bm, (x, y, -0.3), (x, y, 2.6 if y > 0 else 3.2), 0.12)
        wood = _faces(bm, k)
        k = len(bm.faces)
        a = [bm.verts.new(p) for p in ((-2.8, -2.3, 3.3), (2.8, -2.3, 3.3), (2.8, 2.3, 2.6), (-2.8, 2.3, 2.6))]
        bm.faces.new(a)
        bm.faces.new(list(reversed([bm.verts.new(v.co + Vector((0, 0, -0.05))) for v in a])))
        cloth = _faces(bm, k)
        return [(c.lib("scaffold_timber"), wood), (c.lib(cloth_mat), cloth)]

    return _p(c, name, build)


def lift(c, h=24.0):
    """A cargo lift up a cliff face: two tall rails, a winch frame on top, a cage
    partway up (its back toward -Y, on the cliff)."""
    name = "Cargo Lift %g" % h

    def build(bm):
        k = len(bm.faces)
        for x in (-1.6, 1.6):
            _beam(bm, (x, 0.5, -0.5), (x, 0.5, h + 2.0), 0.3)
        _beam(bm, (-2.4, 0.5, h + 2.0), (2.4, 0.5, h + 2.0), 0.35)
        _beam(bm, (0, 0.5, h + 2.0), (0, 2.8, h + 1.4), 0.2)
        for z in range(4, int(h), 6):
            _beam(bm, (-1.6, 0.5, z), (1.6, 0.5, z), 0.12)
        wood = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -1.2, 0.8, h * 0.45, 1.2, 3.0, h * 0.45 + 2.0)
        cage = _faces(bm, k)
        return [(c.lib("scaffold_timber"), wood + cage)]

    return _p(c, name, build)


# ------------------------------------------------------------------ the caverns


def chamber_door(c):
    """A side passage shut by a heavy barred gate, warm light leaking round it (its face
    toward +Y)."""
    name = "Chamber Door"

    def build(bm):
        k = len(bm.faces)
        _box(bm, -3.6, -1.2, -1.0, -2.0, 0.4, 7.0)
        _box(bm, 2.0, -1.2, -1.0, 3.6, 0.4, 7.0)
        _box(bm, -3.6, -1.2, 5.6, 3.6, 0.4, 7.4)
        stone = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -2.0, -1.0, -0.2, 2.0, -0.6, 5.6)
        glow = _faces(bm, k)
        k = len(bm.faces)
        for i in range(6):
            x = -1.7 + i * 0.68
            _box(bm, x - 0.09, -0.5, -0.2, x + 0.09, -0.3, 5.6)
        for z in (1.4, 3.0, 4.6):
            _box(bm, -2.0, -0.55, z - 0.1, 2.0, -0.25, z + 0.1)
        bars = _faces(bm, k)
        return [(c.lib("fortress_wall"), stone), (c.lib("chamber_glow"), glow), (c.lib("iron"), bars)]

    return _p(c, name, build)


def aqueduct(c, span=40.0, h=30.0):
    """A stone aqueduct on arches across a gap (along X), its channel on top."""
    name = "Aqueduct %g %g" % (span, h)

    def build(bm):
        k = len(bm.faces)
        n = max(2, int(span / 14.0))
        for i in range(n + 1):
            x = -span / 2 + i * span / n
            if abs(x) < 16.0:
                continue  # (no pier on the road under it)
            _box(bm, x - 1.4, -1.6, -h, x + 1.4, 1.6, -2.0)
        _box(bm, -span / 2 - 1.4, -1.8, -2.2, span / 2 + 1.4, 1.8, 0.0)
        _box(bm, -span / 2 - 1.4, -1.8, 0.0, span / 2 + 1.4, -1.2, 0.8)
        _box(bm, -span / 2 - 1.4, 1.2, 0.0, span / 2 + 1.4, 1.8, 0.8)
        stone = _faces(bm, k)
        k = len(bm.faces)
        for i in range(n):
            x0 = -span / 2 + i * span / n + 1.4
            x1 = -span / 2 + (i + 1) * span / n - 1.4
            if abs(x0) < 16.0 or abs(x1) < 16.0:
                continue
            pts = [(x0 + (x1 - x0) * t, 0, -2.2 - (x1 - x0) * 0.5 * (1 - math.sin(math.pi * t)) * 0.6) for t in [j / 6 for j in range(7)]]
            tube(bm, pts, 0.9, n=4)
        arches = _faces(bm, k)
        k = len(bm.faces)
        _box(bm, -span / 2 - 1.2, -1.2, 0.3, span / 2 + 1.2, 1.2, 0.55)
        water = _faces(bm, k)
        return [(c.lib("fortress_wall"), stone + arches), (c.lib("canyon_river"), water)]

    return _p(c, name, build)
