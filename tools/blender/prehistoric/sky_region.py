# The Dragon Kingdom's overworld region, v4: floating isles round the Citadel's spire
# (sky_layout.py), replacing the walled basin of dragon_region.py (kept, unused). Builds
# dragon_region and, with --ruin, dragon_region_ruin (after the sacrifice's blast).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/sky_region.py [--ruin]
#
# Built for dragons (Blake's pick): everything at their scale, you tiny in it. The Sky
# Gate's colossal piers; the Crown's avenue of giant steps between pillars up to the
# Citadel's door, forty metres of it in the spire's foot; Dragonfire Square's great dragon;
# roosts jutting from the spire; the isles hanging on chains of dragon light; falls (and
# Emberdeep's lava) pouring off their rims into the cloud.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import bmesh, lerp  # noqa: E402
import region_ruin as ruin  # noqa: E402
import pocket_build as pb  # noqa: E402
from pocket_build import box, cone  # noqa: E402
import keep_props as kp  # noqa: E402
import swamp_props as swp  # noqa: E402
import aurora_props as ap  # noqa: E402
import props  # noqa: E402
import region_paint as paint  # noqa: E402
import ruin_kit  # noqa: E402
import sky_layout as M  # noqa: E402

RUIN = ruin.ON
TRACK_ID = ruin.track_id("dragon_region") + os.environ.get("KP_REGION_SUFFIX", "")

LOOK = {
    # look: (ground, cliff, road, shoulder)
    "crown": (("keep_grass", "grass"), ("keep_rock", "wall"), "keep_flag", ("keep_path", "dirt")),
    "keep": (("keep_grass", "grass"), ("keep_rock_moss", "wall"), "keep_cobble", ("keep_path", "dirt")),
    "moon": (("moon_grass", "grass"), ("moon_rock", "wall"), "moon_paving", ("moon_grass", "grass")),
    "hold": (("ember_rubble", "dirt"), ("ember_rock", "wall"), "ember_setts", ("ember_path", "dirt")),
    "canyon": (("em_jungle_grass", "grass"), ("em_cliff", "wall"), "em_road", ("em_verge", "grass")),
}
UNDER = {"crown": "keep_rock", "keep": "keep_rock_moss", "moon": "moon_rock", "hold": "ember_rock", "canyon": "em_cliff"}


def burn(x, y):
    """Where the sacrifice's blast fell (0 none .. 1)."""
    return 0.55 + 0.45 * math.sin(x / 61.0 - 0.7) * math.cos(y / 43.0 + 1.1)


def natural(x, y):
    return M.natural(x, y)


def classify(c, n, info):
    name, e = M.isle_at(c.x, c.y)
    if name is None or c.z < M.ISLES[name][4] - 14.0:
        return None  # (no ground: the isles float; their undersides are their own rock)
    look = M.ISLES[name][5]
    ground, cliff, _, _ = LOOK[look]
    if n.z < 0.62:
        return cliff
    if RUIN and burn(c.x, c.y) > 0.6:
        return ("scorched_ground", "dirt")
    if look == "crown" and n.z > 0.9 and math.hypot(c.x - M.SPIRE[0], c.y - M.SPIRE[1]) < M.SPIRE[2] + 66.0:
        return ("keep_flag", "road")  # (the plinth round the spire's foot: paved)
    return ground


def main():
    c = kit.Course(TRACK_ID, "Dragon Kingdom (ruined)" if RUIN else "Dragon Kingdom", "dragon_isles")
    c.route(M.ROUTE, width=14.0, bank=5.0)
    kinds = {}
    for look, (ground, cliff, road, shoulder) in LOOK.items():
        kinds[look] = {"mat": road, "shoulder": 1.5, "shoulder_mat": shoulder}
    kinds["bridge"] = {"mat": "keep_flag", "surface": "road", "shoulder": 0.6, "shoulder_mat": ("keep_ashlar", "road"),
                       "barrier": 1.1, "barrier_mat": ("keep_ashlar", "wall"), "deck": 2.6, "deck_mat": ("keep_ashlar", "wall"),
                       "ground": False}
    c.kinds = kinds

    def label(q):
        # (A bridge, railed, wherever the land falls away under either edge: from the
        # isles' rims out over the void.)
        edges = [M._land(q.p.x + q.r.x * sd * (q.w / 2 + 2.0), q.p.y + q.r.y * sd * (q.w / 2 + 2.0)) for sd in (-1, 1)]
        if M._land(q.p.x, q.p.y) < q.p.z - 4.0 or min(edges) < q.p.z - 1.0:
            return "bridge"
        return M.look_at(q.p.x, q.p.y)

    c.roads(kit.plan(c, [(s0, s1, k) for s0, s1, k in kit.runs(c, label)], "crown", max_len=160.0))

    trail = dict(width=10.0, shoulder=1.2, shoulder_mat=("keep_path", "dirt"))
    # The Gate isle: over its bridge from the Crown, to the Sky Gate on its south rim.
    (ax, ay), (bx, by) = M.GATE_BRIDGE
    za = pb.road_z_at(c, ax, ay + 2.5) or c.nearest(ax, ay)[0].p.z
    zb = natural(bx, by) + 0.2
    c.side_road("Gate Bridge", [(ax, lerp(ay, by, k / 20), lerp(za, zb, k / 20)) for k in range(21)], "keep_flag", "road", width=12.0,
                shoulder=0.6, shoulder_mat=("keep_ashlar", "road"), barrier=1.1, barrier_mat=("keep_ashlar", "wall"), deck=2.6,
                deck_mat=("keep_ashlar", "wall"), ground=False)
    gx, gy = M.GATE_ZONE
    c.side_road("Gate Isle Road", pb.line(natural, (bx, by), (gx, gy + 4.0), z0=zb), "keep_flag", "road", **trail)
    wing_gates(c)
    gates = dict(GATES)
    gates["citadel"] = M.CITADEL_DOOR
    spots = pb.spurs(c, natural, gates, lambda x, y: LOOK[M.look_at(x, y)][2], trail, short={"citadel": 16.0})

    X0, X1, Y0, Y1 = -490, 490, -490, 490
    ter = c.terrain("Dragon Kingdom", X0, X1, Y0, Y1, 3.5, natural, classify, near=8.0, fade=16.0, verge_fill=1.5)
    c.disc("Abyss", 0.0, 0.0, 1600.0, M.VOID_Z, c.lib("cloud_bank", "abyss"), role="collision", n=48)
    c.disc("Cloud Sea", 0.0, 0.0, 2200.0, M.CLOUD_Z, c.lib("cloud_bank", "abyss"), role="visual", n=72)

    def ground(x, y):
        z = c.ground_z(x, y, [ter])
        return natural(x, y) if z is None else z

    undersides(c)
    battlements(c, ground)
    for name in WINGS:
        hall(c, ground, name)
    spire(c, ground)
    crown(c, ground, spots)
    sky_gate(c, ground)
    landmarks(c, ground, spots)
    chains(c)
    falls(c)
    pb.emit_spots(c, spots)
    dress(c, ground, spots)
    paint.wayfolk(c, ground, "dragon", [M.SQUARE[:2]], 8, apart=110.0, every=25)
    if RUIN:
        ruined(c, ground, spots)

    c.start_line()
    gts = c.checkpoints(height=10.0)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish(extra={"race": {"laps": 1}})
    print("loop", round(c.length, 1), "gates", len(gts))
    s0 = c.at(0.0)
    g = c.game(s0.p.x, s0.p.y, 0.0)
    print("start x %.1f z %.1f heading %.4f" % (g[0], g[2], math.atan2(s0.t.x, -s0.t.y)))
    sx, sy, _r = M.SQUARE
    g = c.game(sx, sy, 0.0)
    print("square x %.1f z %.1f" % (g[0], g[2]))
    g = c.game(gx, gy, 0.0)
    print("passage causeway: x %.1f z %.1f heading %.4f" % (g[0], g[2], 0.0 + math.pi))
    for name, (end, hd) in spots.items():
        g = c.game(end[0], end[1], 0.0)
        print("spot %s x %.2f z %.2f heading %.4f" % (name, g[0], g[2], hd))


# ------------------------------------------------------------------ the castle

# The floating castle (Blake, Oct 31: "more of a floating castle and we still have bridges
# but they are connecting large chunks of the castle together and these large chunks are
# the different immersive entrances to the levels capturing the theme from the levels";
# he picked driving through each wing): each gateway isle a wing of the castle in its
# course's world, the road through its great hall, the course's gateway a great door in the
# hall's side wall; battlements and towers round every chunk's rim.
WINGS = {
    # name: (walls, pillars, roof (None: open to the sky), height)
    "keep": (("keep_ashlar", "wall"), ("keep_ashlar_dark", "wall"), ("keep_slate", "wall"), 22.0),
    "hold": (("fortress_wall", "wall"), ("obsidian_cliff", "wall"), ("ember_rock", "wall"), 20.0),
    "canyon": (("limestone_moss", "wall"), ("moss_rock", "wall"), ("limestone_moss", "wall"), 20.0),
    "moon": (("moon_stone", "wall"), ("keep_ashlar_dark", "wall"), None, 24.0),
}
# (Their objects' names: "Keep" would read as a building in tests/buildings.test.ts.)
LABEL = {"keep": "Dragonspire", "hold": "Emberdeep", "canyon": "Jungle", "moon": "Moon", "crown": "Crown", "gate": "Gate Isle"}
HALF = 28.0  # the halls' half width (the walls this far from the road's middle)
GATES = {}  # each wing's gateway, in its hall's side wall (wing_gates)
SPANS = {}  # each wing's hall: (s0, s1, the gate's s, its side)


def wing_gates(c):
    """Where each wing's hall runs (the road across its isle) and its gateway, a door in the
    side wall towards the isle's middle."""
    for name in WINGS:
        ss = [q.s for q in c.S if M.isle_at(q.p.x, q.p.y)[0] == name and M.isle_e(name, q.p.x, q.p.y) < 0.72]
        if not ss:
            continue
        mid = (min(ss) + max(ss)) / 2
        s0, s1 = max(min(ss), mid - 60.0), min(max(ss), mid + 60.0)
        q = c.at(mid)
        cx, cy = M.ISLES[name][:2]
        sd = 1 if (cx - q.p.x) * q.r.x + (cy - q.p.y) * q.r.y > 0 else -1
        GATES[name] = (q.p.x + q.r.x * sd * (HALF - 1.5), q.p.y + q.r.y * sd * (HALF - 1.5))
        SPANS[name] = (s0, s1, mid, sd)


def hall(c, ground, name):
    """A wing's great hall over the road: its walls (the gate's door in one), pillars down
    both sides, ribs across, the roof (the moon temple's open to the stars, the jungle's
    broken), a great arch at each end between towers; then its world inside."""
    if name not in SPANS:
        return
    wall, pillar, roof, H = WINGS[name]
    s0, s1, sg, gsd = SPANS[name]
    z0 = min(c.at(s0).p.z, c.at(s1).p.z) - 3.0
    s = s0
    k = 0
    while s <= s1:
        q = c.at(s)
        rot = math.atan2(q.t.y, q.t.x)
        z = q.p.z
        for sd in (-1, 1):
            if sd == gsd and abs(s - sg) < 11.0:
                continue  # (the gate's door stands here)
            x, y = q.p.x + q.r.x * sd * HALF, q.p.y + q.r.y * sd * HALF
            box(c, "%s Hall Wall %d %d" % (LABEL[name], k, sd), x, y, 3.4, 1.6, z - 4.0, z + H, wall, rot=rot)
            if k % 2 == 0:
                px, py = q.p.x + q.r.x * sd * (HALF - 5.0), q.p.y + q.r.y * sd * (HALF - 5.0)
                box(c, "%s Hall Pillar %d %d" % (LABEL[name], k, sd), px, py, 1.5, 1.5, z - 1.0, z + H, pillar, rot=rot)
        if k % 2 == 0:
            box(c, "%s Hall Rib %d" % (LABEL[name], k), q.p.x, q.p.y, 1.2, HALF + 1.5, z + H, z + H + 2.2, pillar, rot=rot,
                role="visual")
        if roof and not (name == "canyon" and k % 3 == 1):
            box(c, "%s Hall Roof %d" % (LABEL[name], k), q.p.x, q.p.y, 3.2, HALF + 1.6, z + H + 2.2, z + H + 3.2, roof, rot=rot,
                role="visual")
        s += 6.0
        k += 1
    # The great arches at the ends, between towers.
    for e, se in enumerate((s0, s1)):
        q = c.at(se)
        rot = math.atan2(q.t.y, q.t.x)
        z = q.p.z
        for sd in (-1, 1):
            x, y = q.p.x + q.r.x * sd * (HALF - 7.5), q.p.y + q.r.y * sd * (HALF - 7.5)
            box(c, "%s Arch Side %d %d" % (LABEL[name], e, sd), x, y, 1.8, 7.5, z - 4.0, z + H + 3.0, wall, rot=rot)
            tx, ty = q.p.x + q.r.x * sd * (HALF + 4.0), q.p.y + q.r.y * sd * (HALF + 4.0)
            box(c, "%s Arch Bastion %d %d" % (LABEL[name], e, sd), tx, ty, 5.0, 5.0, z - 6.0, z + H + 20.0, wall, rot=rot)
            cone(c, "%s Arch Bastion Cap %d %d" % (LABEL[name], e, sd), tx, ty, 6.8, z + H + 20.0, 14.0,
                 roof or ("crystal_violet2", "wall"), segs=4, role="visual")
        box(c, "%s Arch Lintel %d" % (LABEL[name], e), q.p.x, q.p.y, 1.8, HALF, z + 15.0, z + H + 3.0, wall, rot=rot, role="visual")
    WORLD[name](c, ground, name)


def _hall_spots(c, name, every, off, side=None):
    """Spots down a hall at `off` m from the road's middle (its side away from the gate, or
    `side`), every `every` m: [(x, y, z, rot)]."""
    s0, s1, sg, gsd = SPANS[name]
    sd = side or -gsd
    out = []
    s = s0 + every / 2
    while s < s1:
        q = c.at(s)
        out.append((q.p.x + q.r.x * sd * off, q.p.y + q.r.y * sd * off, q.p.z, math.atan2(q.t.y, q.t.x)))
        s += every
    return out


def _keep_world(c, ground, name):
    """Dragonspire's hall: banners down its pillars, braziers, tapestries on the walls."""
    for sd in (-1, 1):
        for k, (x, y, z, rot) in enumerate(_hall_spots(c, name, 18.0, HALF - 8.0, sd)):
            c.place(kp.banner_pole(c, h=12.0), x, y, ground(x, y), rot=rot)
            if k % 2 == 0:
                c.place(kp.brazier(c), x, y + 0.0, ground(x, y))
                g = c.game(x, y, ground(x, y) + 2.4)
                c.entity("torch", x=g[0], y=g[1], z=g[2])
    for k, (x, y, z, rot) in enumerate(_hall_spots(c, name, 12.0, HALF - 1.8)):
        box(c, "Dragonspire Tapestry %d" % k, x, y, 2.0, 0.2, z + 4.0, z + 14.0, (("banner_red", "banner_royal")[k % 2], "wall"), rot=rot,
            role="visual")


def _hold_world(c, ground, name):
    """Emberdeep's forge hall: furnaces glowing in the far wall, a lava channel along it
    behind a low kerb, chimneys up through the roof smoking, anvils, braziers."""
    s0, s1, sg, gsd = SPANS[name]
    for k, (x, y, z, rot) in enumerate(_hall_spots(c, name, 14.0, HALF - 2.4)):
        box(c, "Furnace %d" % k, x, y, 3.0, 1.2, z - 0.5, z + 7.0, ("obsidian_cliff", "wall"), rot=rot)
        box(c, "Furnace Mouth %d" % k, x, y, 2.0, 1.25, z + 0.8, z + 4.0, ("fire_glow", "wall"), rot=rot, role="visual")
        g = c.game(x, y, z + 3.0)
        c.entity("torch", x=g[0], y=g[1], z=g[2])
        box(c, "Chimney %d" % k, x, y, 1.6, 1.6, z + 7.0, z + WINGS[name][3] + 12.0, ("obsidian_cliff", "wall"), rot=rot, role="visual")
        g = c.game(x, y, z + WINGS[name][3] + 12.0)
        c.entity("steam", x=g[0], y=g[1], z=g[2])
    pts = [(x, y, z) for x, y, z, rot in _hall_spots(c, name, 4.0, HALF - 9.0)]
    if len(pts) > 2:
        c.ribbon("Forge Lava", [(x, y, 4.0, z - 0.3) for x, y, z in pts], 4.0, 0, c.lib("volcano_lava", "lava"), role="both")
        for k, (x, y, z, rot) in enumerate(_hall_spots(c, name, 6.0, HALF - 12.0)):
            box(c, "Forge Kerb %d" % k, x, y, 3.2, 0.4, z - 0.5, z + 0.9, ("obsidian_cliff", "wall"), rot=rot)
    for k, (x, y, z, rot) in enumerate(_hall_spots(c, name, 20.0, HALF - 15.0)):
        c.place(kp.brazier(c), x, y, ground(x, y))


def _canyon_world(c, ground, name):
    """The jungle's hall: trees grown up through the broken roof, vines hanging off the ribs,
    water pouring in where the roof's gone into pools, ferns and big leaves."""
    for k, (x, y, z, rot) in enumerate(_hall_spots(c, name, 16.0, HALF - 13.0)):
        c.place(props.jungle_tree(c, k % 2), x, y, ground(x, y) - 0.2, rot=k, scale=1.6)
    for sd in (-1, 1):
        for k, (x, y, z, rot) in enumerate(_hall_spots(c, name, 12.0, HALF - 6.0, sd)):
            c.place(swp.hanging_vine(c, k % 2, length=10.0), x, y, z + WINGS[name][3] + 1.0, rot=rot, role="visual")
            c.place(props.big_leaf_plant(c, k % 2), x, y, ground(x, y), rot=k, role="visual")
    for k, (x, y, z, rot) in enumerate(_hall_spots(c, name, 36.0, HALF - 18.0)):
        props.falls(c, "Hall Falls %d" % k, x, y, z + WINGS[name][3] + 1.0, z + 0.2, 2.4, 4.0, facing=1, throw=1.0, bulge=0.4, veils=2,
                    angle=rot, mats=("falls_oasis", "falls_curtain_oasis", "falls_foam"))
        c.disc("Hall Pool %d" % k, x, y, 4.5, ground(x, y) + 0.12, c.lib("lagoon_shallow", "water"), role="visual", n=16, wobble=0.2,
               seed=k)


def _moon_world(c, ground, name):
    """The moon temple's court: open to the sky, violet crystals growing down both sides,
    moonstones glowing in the pillars, lanterns."""
    for k, (x, y, z, rot) in enumerate(_hall_spots(c, name, 14.0, HALF - 12.0)):
        c.place(ap.spire_cluster(c, k % 2, height=8.0 + 3.0 * (k % 2), mat="crystal_violet2", accent="crystal_cyan"), x, y,
                ground(x, y) - 0.3, rot=k)
    for sd in (-1, 1):
        for k, (x, y, z, rot) in enumerate(_hall_spots(c, name, 12.0, HALF - 5.0, sd)):
            box(c, "Moonstone %d %d" % (k, sd), x - math.sin(rot) * sd * 1.6, y + math.cos(rot) * sd * 1.6, 0.6, 0.2, z + 6.0, z + 8.0,
                ("crystal_violet2", "wall"), rot=rot, role="visual")
            g = c.game(x, y, z + 9.0)
            c.entity("lantern", x=g[0], y=g[1], z=g[2])


WORLD = {"keep": _keep_world, "hold": _hold_world, "canyon": _canyon_world, "moon": _moon_world}


def battlements(c, ground):
    """Round every chunk's rim: a battlemented wall, towers every so often (none across the
    road or the bridges' ends)."""
    for name, (x, y, rx, ry, z, look) in M.ISLES.items():
        wall = ("keep_ashlar", "wall") if look != "hold" else ("fortress_wall", "wall")
        n = int(2 * math.pi * max(rx, ry) / 9.0)
        for k in range(n):
            a = k * math.tau / n
            e = 0.93
            wob = 1.0 + 0.07 * math.sin(3.0 * a + len(name)) + 0.04 * math.sin(7.0 * a + 2.0 * len(name))
            px, py = x + rx * e * wob * math.cos(a), y + ry * e * wob * math.sin(a)
            if not paint.road_clear(c, px, py, 12.0):
                continue
            gz = ground(px, py)
            if gz < z - 8.0:
                continue
            rot = a + math.pi / 2
            if k % 8 == 0:
                box(c, "Rim Bastion %s %d" % (LABEL.get(name, name.title()), k), px, py, 3.6, 3.6, gz - 6.0, gz + 16.0, wall, rot=rot)
                cone(c, "Rim Bastion Cap %s %d" % (LABEL.get(name, name.title()), k), px, py, 5.0, gz + 16.0, 9.0, ("keep_slate", "wall"), segs=4, role="visual")
            else:
                box(c, "Rim Wall %s %d" % (LABEL.get(name, name.title()), k), px, py, 4.8, 1.2, gz - 6.0, gz + 3.2, wall, rot=rot)
                box(c, "Rim Merlon %s %d" % (LABEL.get(name, name.title()), k), px, py, 1.2, 1.3, gz + 3.2, gz + 4.4, wall, rot=rot, role="visual")


# ------------------------------------------------------------------ the isles


def undersides(c):
    """Under each isle its rock, hanging: wide at the top, tapering down to a point, in its
    own rock (scorched in the ruin)."""
    for k, (name, (x, y, rx, ry, z, look)) in enumerate(M.ISLES.items()):
        depth = 0.9 * max(rx, ry) + 30.0
        rm = c.rock_mass("Isle Under %s" % name.title(), x, y, rx * 1.03, ry * 1.03, z - 2.0, z0=z - depth, n=24, seed=60 + k,
                         bands=[(0.05, 0.0), (0.3, 0.25), (0.62, 0.55), (0.9, 0.82), (1.0, 0.94), (0.99, 1.0)])
        c.assign(rm, c.lib(UNDER[look], "wall"))
        rm.data.shade_flat()


def spire(c, ground):
    """The Citadel's spire out of the Crown, up into the sky; the Citadel on top (gold
    roofs; the ruin's broken off at the blast), roosts jutting from its sides, the door at
    its foot forty metres high."""
    sx, sy, sr = M.SPIRE
    top = M.SPIRE_TOP if not RUIN else M.SPIRE_TOP - 70.0
    rm = c.rock_mass("Spire", sx, sy, sr, sr, top, z0=-120.0, n=20, seed=11,
                     bands=[(0.6, 0.0), (1.0, 0.42), (0.92, 0.5), (0.8, 0.75), (0.62, 0.95), (0.55, 1.0)])
    c.assign(rm, c.lib("keep_rock", "wall"))
    rm.data.shade_flat()
    if not RUIN:
        box(c, "Citadel Hall", sx, sy, 26.0, 20.0, top - 4.0, top + 34.0, ("keep_ashlar_dark", "wall"), role="visual")
        for k, (dx, dy) in enumerate(((-24.0, -18.0), (24.0, -18.0), (-24.0, 18.0), (24.0, 18.0))):
            box(c, "Citadel Tower %d" % k, sx + dx, sy + dy, 6.0, 6.0, top - 4.0, top + 52.0, ("keep_ashlar_dark", "wall"), role="visual")
            cone(c, "Citadel Tower Roof %d" % k, sx + dx, sy + dy, 8.0, top + 52.0, 18.0, ("gold_trim", "wall"), segs=4, role="visual")
        box(c, "Citadel Keep", sx, sy, 12.0, 12.0, top + 34.0, top + 80.0, ("keep_ashlar_dark", "wall"), role="visual")
        cone(c, "Citadel Spire Roof", sx, sy, 15.0, top + 80.0, 34.0, ("gold_trim", "wall"), segs=4, role="visual")
    else:
        for k in range(6):
            a = k * 1.1
            box(c, "Citadel Stump %d" % k, sx + 14.0 * math.cos(a), sy + 14.0 * math.sin(a), 5.0, 5.0, top - 6.0, top + 6.0 + 5.0 * (k % 3),
                ("keep_ashlar_dark", "wall"), rot=a, role="visual")
    # Roosts: great platforms jutting from the spire, at the dragons' heights.
    for k in range(6):
        a = k * 2.2 + 0.4
        z = 60.0 + k * 24.0
        if z > top - 10.0:
            continue
        r = sr * (1.0 - 0.38 * (z + 120.0) / (top + 120.0)) + 6.0
        box(c, "Roost %d" % k, sx + r * math.cos(a), sy + r * math.sin(a), 9.0, 5.0, z - 2.0, z, ("keep_ashlar", "wall"), rot=a,
            role="visual")
    # The Citadel's door: forty metres of it in the spire's foot, gold-framed.
    dx, dy = M.CITADEL_DOOR
    z = ground(dx, dy - 10.0)
    box(c, "Citadel Door", dx, dy + 1.0, 9.0, 2.0, z - 1.0, z + 40.0, ("dark_corridor", "wall"), role="visual")
    for sd in (-1, 1):
        box(c, "Citadel Door Jamb %d" % sd, dx + sd * 11.0, dy - 1.0, 2.2, 3.0, z - 1.0, z + 44.0, ("gold_trim", "wall"))
    box(c, "Citadel Door Lintel", dx, dy - 1.0, 13.2, 3.0, z + 40.0, z + 46.0, ("gold_trim", "wall"), role="visual")


def crown(c, ground, spots):
    """The Crown: Dragonfire Square (the hub) and its great dragon; the avenue up to the
    Citadel's door between colossal pillars and over giant steps (their middles ramped for
    karts), braziers; the Kingdom's folk."""
    sx, sy, sr = M.SQUARE
    z = ground(sx, sy)
    c.disc("Dragonfire Square", sx, sy, sr, z + 0.06, c.lib("keep_ashlar", "road"), coll="Props", n=40)
    dragon_statue(c, sx, sy, z, 1.0 if not RUIN else 0.6)
    g = c.game(sx, sy - sr + 4.0, z + 0.3)
    c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=sr - 4.0, n=8, folk="dragon", heading=0.0)
    for k in range(8):
        a = k * math.tau / 8 + 0.2
        x, y = sx + (sr + 2.0) * math.cos(a), sy + (sr + 2.0) * math.sin(a)
        if not paint.road_clear(c, x, y, 2.0):
            continue
        c.place(kp.brazier(c), x, y, ground(x, y))
        gg = c.game(x, y, ground(x, y) + 2.4)
        c.entity("torch", x=gg[0], y=gg[1], z=gg[2])
    # The avenue: from the square to the Citadel's door, pillars either side, and the giant
    # steps beside it (the road itself ramps up between them).
    dx, dy = M.CITADEL_DOOR
    for k in range(6):
        y = lerp(sy + sr + 8.0, dy - 18.0, k / 5)
        for sd in (-1, 1):
            x = dx + sd * 15.0
            zg = ground(x, y)
            box(c, "Avenue Pillar %d %d" % (k, sd), x, y, 2.6, 2.6, zg - 1.0, zg + 26.0, ("keep_ashlar", "wall"))
            box(c, "Avenue Pillar Cap %d %d" % (k, sd), x, y, 3.4, 3.4, zg + 26.0, zg + 28.0, ("gold_trim", "wall"), role="visual")
            gg = c.game(x - sd * 2.0, y, zg + 3.0)
            c.entity("torch", x=gg[0], y=gg[1], z=gg[2])
    for k in range(4):
        y0 = lerp(sy + sr + 4.0, dy - 12.0, k / 4)
        y1 = lerp(sy + sr + 4.0, dy - 12.0, (k + 1) / 4)
        for sd in (-1, 1):
            xc = dx + sd * 30.0
            zg = ground(xc, (y0 + y1) / 2)
            box(c, "Giant Step %d %d" % (k, sd), xc, (y0 + y1) / 2, 12.0, (y1 - y0) / 2, zg - 4.0, zg + 1.0 + 3.0 * k,
                ("keep_ashlar", "wall"))


def dragon_statue(c, x, y, z, s):
    """A great dragon on its plinth, wings half spread (s: its size; the ruin's toppled to
    rubble)."""
    box(c, "Dragon Plinth", x, y, 7.0, 7.0, z - 0.5, z + 3.0, ("keep_ashlar_dark", "wall"))
    if RUIN:
        for k in range(5):
            a = k * 1.3
            box(c, "Dragon Rubble %d" % k, x + 9.0 * math.cos(a), y + 9.0 * math.sin(a), 2.2, 1.6, z - 0.5, z + 1.6, ("gold_trim", "wall"),
                rot=a, role="visual")
        return
    gold = ("gold_trim", "wall")
    box(c, "Dragon Body", x, y, 3.2 * s, 7.0 * s, z + 3.0, z + 3.0 + 7.0 * s, gold, role="visual")
    box(c, "Dragon Neck", x, y + 7.0 * s, 1.8 * s, 2.0 * s, z + 7.0 * s, z + 18.0 * s, gold, rot=0.0, role="visual")
    cone(c, "Dragon Head", x, y + 9.0 * s, 2.6 * s, z + 18.0 * s, 6.0 * s, gold, segs=4, role="visual")
    for sd in (-1, 1):
        bm = bmesh.new()
        pts = [(x + sd * 3.0 * s, y - 2.0 * s, z + 9.0 * s), (x + sd * 16.0 * s, y - 6.0 * s, z + 18.0 * s),
               (x + sd * 20.0 * s, y + 2.0 * s, z + 14.0 * s), (x + sd * 3.0 * s, y + 4.0 * s, z + 9.5 * s)]
        bm.faces.new([bm.verts.new(p) for p in pts])
        bm.faces.new([bm.verts.new(p) for p in reversed(pts)])
        c.assign(c.mesh_object("Dragon Wing %d" % sd, bm, "Props", "visual"), c.lib("gold_trim", "wall"))
    box(c, "Dragon Tail", x, y - 10.0 * s, 1.2 * s, 5.0 * s, z + 3.0, z + 5.0 * s, gold, role="visual")


def sky_gate(c, ground):
    """The Sky Gate on the Gate isle's south rim, as the other side has it: two colossal
    piers, gold heads, the lintel; beyond, the Sky Bridge's last span back over the void."""
    gx, gy = M.GATE_ZONE
    z = ground(gx, gy)
    py = gy - 12.0
    for sd in (-1, 1):
        px = gx + sd * 15.0
        box(c, "Sky Gate Pier %d" % sd, px, py, 4.0, 4.0, z - 40.0, z + 44.0, ("keep_rock", "wall"))
        cone(c, "Sky Gate Head %d" % sd, px, py + 4.0, 3.2, z + 30.0, 12.0, ("gold_trim", "wall"), segs=6, role="visual")
        g = c.game(px, py + 5.0, z + 8.0)
        c.entity("torch", x=g[0], y=g[1], z=g[2])
    box(c, "Sky Gate Lintel", gx, py, 19.0, 4.5, z + 40.0, z + 46.0, ("keep_rock", "wall"), role="visual")
    box(c, "Sky Bridge End", gx, py - 30.0, 7.0, 30.0, z - 2.6, z - 0.2, ("plank_road", "wall"), role="visual")
    for sd in (-1, 1):
        box(c, "Sky Bridge End Rail %d" % sd, gx + sd * 7.0, py - 30.0, 0.15, 30.0, z - 0.2, z + 1.0, ("rope_rail", "wall"), role="visual")


def landmarks(c, ground, spots):
    """Each isle's gateway: Dragonspire's tall keep, the moon gate's standing stones, the
    Hold's fortress gate, the jungle castle's overgrown gate."""
    def facing(name):
        (ex, ey), _ = spots[name]
        gx, gy = GATES[name]
        return math.atan2(gy - ey, gx - ex)

    def gateway(name, mat, width=8.0, height=14.0, towers=0.0, roof=None):
        x, y = GATES[name]
        f = facing(name)
        rot = f + math.pi / 2
        z0 = ground(x - 6.0 * math.cos(f), y - 6.0 * math.sin(f))
        box(c, name.title() + " Gate", x, y, width, 2.0, z0 - 1.0, z0 + height, ("dark_corridor", "wall"), rot=rot, role="visual")
        for sd in (-1, 1):
            px, py = x + sd * (width + 1.5) * math.cos(rot), y + sd * (width + 1.5) * math.sin(rot)
            box(c, "%s Gate Jamb %d" % (name.title(), sd), px, py, 1.8, 2.8, z0 - 1.0, z0 + height + 2.0, mat, rot=rot)
            if towers:
                tx, ty = x + sd * (width + 7.0) * math.cos(rot), y + sd * (width + 7.0) * math.sin(rot)
                box(c, "%s Gate Tower %d" % (name.title(), sd), tx, ty, 4.0, 4.0, z0 - 1.0, z0 + towers, mat, rot=rot)
                if roof:
                    cone(c, "%s Gate Roof %d" % (name.title(), sd), tx, ty, 5.5, z0 + towers, 9.0, roof, segs=4, role="visual")
        box(c, name.title() + " Gate Lintel", x, y, width + 2.5, 3.0, z0 + height, z0 + height + 3.5, mat, rot=rot)
        return x, y, z0, f

    roof = ("keep_slate", "wall")
    x, y, z0, f = gateway("keep", ("keep_ashlar", "wall"))
    kx, ky = x + 22.0 * math.cos(f), y + 22.0 * math.sin(f)
    box(c, "Dragonspire", kx, ky, 6.0, 6.0, z0 - 1.0, z0 + (30.0 if RUIN else 64.0), ("keep_ashlar", "wall"))
    if not RUIN:
        cone(c, "Dragonspire Roof", kx, ky, 8.0, z0 + 64.0, 16.0, roof, segs=4, role="visual")
    gateway("canyon", ("limestone_moss", "wall"), towers=22.0, roof=("lush_grass", "wall"))
    gateway("hold", ("fortress_wall", "wall"), height=18.0, towers=32.0)
    mx, my = GATES["moon"]
    f = facing("moon")
    rot = f + math.pi / 2
    z0 = ground(mx - 6.0 * math.cos(f), my - 6.0 * math.sin(f))
    for sd in (-1, 1):
        bx, by = mx + sd * 8.0 * math.cos(rot), my + sd * 8.0 * math.sin(rot)
        box(c, "Moon Gate Stone %d" % sd, bx, by, 2.2, 1.8, z0 - 1.0, z0 + 16.0, ("moon_stone", "wall"), rot=rot)
    box(c, "Moon Gate Lintel", mx, my, 11.0, 2.2, z0 + 16.0, z0 + 19.0, ("moon_stone", "wall"), rot=rot, role="visual")
    box(c, "Moon Gate Moonstone", mx + 1.15 * math.cos(f), my + 1.15 * math.sin(f), 1.4, 0.15, z0 + 16.6, z0 + 18.4,
        ("crystal_violet2", "wall"), rot=rot, role="visual")


def chains(c):
    """The chains of dragon light: from each isle's underside, glowing, slung across to the
    spire (the ruin's snapped, hanging)."""
    sx, sy, sr = M.SPIRE
    for k, (name, (x, y, rx, ry, z, look)) in enumerate(M.ISLES.items()):
        if name == "crown":
            continue
        a = math.atan2(sy - y, sx - x)
        for j, off in enumerate((-0.35, 0.35)):
            b = a + off
            p0 = (x + rx * 0.7 * math.cos(b), y + ry * 0.7 * math.sin(b), z - 20.0)
            p1 = (sx + (sr - 4.0) * math.cos(a + math.pi + off * 0.5), sy + (sr - 4.0) * math.sin(a + math.pi + off * 0.5), z + 30.0)
            pts = []
            n = 16 if not RUIN else 7
            for i in range(n + 1):
                t = i / 16
                sag = 26.0 * (1.0 - (2 * t - 1) ** 2)
                pts.append((lerp(p0[0], p1[0], t), lerp(p0[1], p1[1], t), lerp(p0[2], p1[2], t) - sag))
            if RUIN:
                pts.append((pts[-1][0], pts[-1][1], pts[-1][2] - 30.0))
            bm = bmesh.new()
            props.tube(bm, pts, 0.7, n=6)
            c.assign(c.mesh_object("Light Chain %d %d" % (k, j), bm, "Props", "visual"), c.lib("lantern_amber", "wall"))


def falls(c):
    """Falls off the isles' rims into the cloud (Emberdeep's lava)."""
    for k, (name, (x, y, rx, ry, z, look)) in enumerate(M.ISLES.items()):
        if name == "gate":
            continue
        for j, a in enumerate((0.6 + k, 2.9 + k)):
            lx, ly = x + rx * 0.99 * math.cos(a), y + ry * 0.99 * math.sin(a)
            if not paint.road_clear(c, lx, ly, 10.0):
                continue
            mats = ("lava_falls", "lava_falls", "fire_glow") if look == "hold" else ("falls_oasis", "falls_curtain_oasis", "falls_foam")
            props.falls(c, "Isle Falls %d %d" % (k, j), lx, ly, z - 0.5, M.CLOUD_Z + 10.0, 6.0, 14.0, facing=1, throw=6.0,
                        bulge=1.4, veils=3, foam=False, angle=a - math.pi / 2, mats=mats)


# ------------------------------------------------------------------ the paint pass


def dress(c, ground, spots):
    """Each isle in its world: the Crown's pines and banners and houses; Dragonspire's pines,
    houses, round towers; Moonstone's violet crystals, torch posts, dark pines; Emberdeep's
    black walls, basalt and lava pools; the Emerald Canyon's jungle and ruins."""
    taken = paint.Taken([(M.SQUARE[0], M.SQUARE[1], M.SQUARE[2] + 14.0), *((e[0], e[1], 16.0) for e, _ in spots.values()),
                         *((x, y, 28.0) for x, y in GATES.values()), (M.SPIRE[0], M.SPIRE[1], M.SPIRE[2] + 70.0),
                         *((M.ISLES[n][0], M.ISLES[n][1], 40.0) for n in WINGS),
                         (M.ISLES["gate"][0], M.ISLES["gate"][1], 64.0)])  # (the Gate isle bare: the view in, clear)

    def on(*names):
        def ok(x, y):
            n, e = M.isle_at(x, y)
            return n is not None and e < 0.9 and M.ISLES[n][5] in names and natural(x, y) > M.VOID_Z + 10.0
        return ok

    rmax = 480.0
    g = ground
    cr = on("crown")
    for v in range(2):
        paint.scatter(c, kp.pine(c, v, 10.0 + 2.0 * v), 20, rmax, cr, g, taken, 10 + v, room=6.0, road_margin=6.0, trunk=(0.7, 6.0))
        paint.scatter(c, kp.house(c, v + 2), 4, rmax, cr, g, taken, 12 + v, room=14.0, road_margin=9.0)
    paint.scatter(c, kp.banner_pole(c), 12, rmax, cr, g, taken, 14, room=8.0, near_road=(2.0, 5.0))
    ke = on("keep")
    for v in range(2):
        paint.scatter(c, kp.pine(c, v, 9.0 + 3.0 * v), 26, rmax, ke, g, taken, 20 + v, room=5.0, scale=(1.0, 1.6), road_margin=6.0,
                      trunk=(0.7, 6.0))
        paint.scatter(c, kp.house(c, v), 4, rmax, ke, g, taken, 22 + v, room=14.0, road_margin=9.0)
    paint.scatter(c, kp.round_tower(c, r=3.2, h=14.0, roof=True, variant=0), 2, rmax, ke, g, taken, 24, room=14.0, road_margin=10.0,
                  seat=3.2)
    mo = on("moon")
    for v in range(2):
        paint.scatter(c, ap.spire_cluster(c, v, height=7.0 + 3.0 * v, mat="crystal_violet2", accent="crystal_cyan"), 8, rmax, mo, g,
                      taken, 30 + v, room=7.0, road_margin=6.0)
        paint.scatter(c, kp.pine(c, v, 9.0 + 2.0 * v), 10, rmax, mo, g, taken, 32 + v, room=5.0, road_margin=6.0, trunk=(0.7, 6.0))
    for x, y in paint.scatter(c, kp.torch_post(c), 10, rmax, mo, g, taken, 34, room=6.0, near_road=(2.0, 5.0)):
        gg = c.game(x, y, g(x, y) + 2.6)
        c.entity("torch", x=gg[0], y=gg[1], z=gg[2])
    ho = on("hold")
    paint.scatter(c, kp.curtain_wall(c, length=18.0, h=10.0), 4, rmax, ho, g, taken, 40, room=16.0, road_margin=10.0)
    paint.scatter(c, props.basalt_columns(c), 10, rmax, ho, g, taken, 41, room=7.0, road_margin=7.0)
    for x, y in paint.scatter(c, props.boulder(c, "volcano_basalt", 1), 6, rmax, ho, g, taken, 42, room=6.0):
        gg = c.game(x, y, g(x, y) + 1.0)
        c.entity("steam", x=gg[0], y=gg[1], z=gg[2])
    for x, y in paint.scatter(c, kp.brazier(c), 6, rmax, ho, g, taken, 43, room=8.0, near_road=(2.0, 6.0)):
        gg = c.game(x, y, g(x, y) + 2.4)
        c.entity("torch", x=gg[0], y=gg[1], z=gg[2])
    ca = on("canyon")
    for v in range(2):
        paint.scatter(c, props.jungle_tree(c, v), 26, rmax, ca, g, taken, 50 + v, room=5.0, scale=(1.1, 1.8), road_margin=6.0,
                      trunk=(0.8, 6.0))
        paint.scatter(c, props.big_leaf_plant(c, v), 30, rmax, ca, g, taken, 52 + v, room=2.5, role="visual")
    for v, p in enumerate((props.ruin_column(c, 0), props.ruin_blocks(c, 0), props.idol_head(c))):
        paint.scatter(c, p, 4, rmax, ca, g, taken, 54 + v, room=6.0, near_road=(5.0, 20.0))


def ruined(c, ground, spots):
    """After the sacrifice's blast: smoke and rubble at every gate, the trees charred, broken
    rock drifting off the isles' rims."""
    for name, ((ex, ey), h) in spots.items():
        ux, uy = -math.sin(h), math.cos(h)
        for sd in (-1, 1):
            rx, ry = ex - uy * sd * 13.0 + ux * 3.0, ey + ux * sd * 13.0 + uy * 3.0
            ruin.rubble(c, "%s Rubble %d" % (name.title(), sd), rx, ry, ground, ("keep_rock", "wall"), seed=len(name) + sd)
        ruin.smoke(c, ex + ux * 8.0, ey + uy * 8.0, ground(ex, ey) + 0.5)
    for k, (name, (x, y, rx, ry, z, look)) in enumerate(M.ISLES.items()):
        for j in range(3):
            a = k * 1.7 + j * 2.1
            bx, by = x + rx * 1.25 * math.cos(a), y + ry * 1.25 * math.sin(a)
            r = 8.0 + 4.0 * j
            rm = c.rock_mass("Drift Rock %s %d" % (name.title(), j), bx, by, r, r * 0.8, z - 6.0 - 9.0 * j, z0=z - 6.0 - 9.0 * j - r * 1.6, n=12,
                             seed=90 + k * 3 + j, bands=[(0.2, 0.0), (0.8, 0.5), (1.0, 0.85), (0.9, 1.0)])
            c.assign(rm, c.lib(UNDER[look], "wall"))
    ruin_kit.char_trees(c, burn, ("Pine", "Broadleaf", "Jungle Tree"), chance=0.85, threshold=0.4)


if __name__ == "__main__":
    main()
