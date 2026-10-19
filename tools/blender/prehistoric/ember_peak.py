# Ember Peak: Prehistoric World, course 4. "Frantic volcanic march."
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/ember_peak.py      (the bpy module)
#
# A smoking volcano in a field of black rock. The road spirals all the way up round the
# cone, counter-clockwise: over three rivers of lava on basalt bridges, through a
# glowing tunnel in a rock spur, along the crater rim at the summit, then plunges
# straight back down the south face, leaping a lava gully on the way, to the line.
#
# Saves tracks-src/ember_peak.blend and exports public/tracks/ember_peak/.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import props  # noqa: E402
from course_kit import bmesh, lerp, smooth  # noqa: E402

TRACK_ID = "ember_peak"
C = (10.0, 40.0)  # the crater's centre
CRATER_R = 30.0
LAVA_LAKE_Z = 25.0
FLOWS = [12.0, 128.0, 196.0]  # lava rivers, by compass angle from the centre (degrees)
GULLY_R = (108.0, 118.0)  # the lava gully the descent jumps
SPUR = 150.0  # the rock spur the tunnel goes through, by angle
TOP = 25.0  # the road's highest point


def polar(theta_deg, r, z, w=None):
    t = math.radians(theta_deg)
    p = (C[0] + r * math.cos(t), C[1] + r * math.sin(t), z)
    return p + ((w,) if w else ())


SPIRAL = (292.0, 304.0, 176.0, 62.0)  # start angle, degrees turned, start and end radius


def spiral_r(theta):
    """The climb's radius where it passes `theta` (degrees)."""
    a0, turn, r0, r1 = SPIRAL
    u = ((theta - a0) % 360) / turn
    return r0 + (r1 - r0) * u


def spiral():
    """The climb: once round the cone, from the start line to the summit."""
    a0, turn, r0, r1 = SPIRAL
    pts = []
    n = 13
    for k in range(n):
        u = k / (n - 1)
        pts.append(polar(a0 + turn * u, r0 + (r1 - r0) * u, 0.6 + (TOP - 0.6) * u ** 1.4))
    return pts


def descent():
    """Straight down the south-south-west face, in a long S, over the gully."""
    pts = []
    for theta, r, z in (
        (247, 66, TOP),
        (254, 76, TOP - 0.8),
        (258, 90, 22.0),
        (259, GULLY_R[0] - 1, 18.2),  # the lip
        (259, GULLY_R[1] + 2, 14.0),  # the landing
        (259.5, 138, 10.4),
        (262, 156, 5.6),
        (268, 168, 2.6),
        (278, 176, 0.8),
    ):
        pts.append(polar(theta, r, z))
    return pts


ROUTE = spiral() + descent()


def cone(r):
    if r < CRATER_R:
        return lerp(LAVA_LAKE_Z - 3, 31.0, smooth((r - 12) / (CRATER_R - 12)) ** 2)
    return 31.0 * (1 - smooth((r - CRATER_R) / 150)) ** 1.15


def flow_dist(x, y):
    """Distance (m, across the slope) to the nearest lava river, and that river."""
    a = math.degrees(math.atan2(y - C[1], x - C[0]))
    r = math.hypot(x - C[0], y - C[1])
    best = (1e9, None)
    for f in FLOWS:
        d = abs((a - f + 180) % 360 - 180)
        wob = 4 * math.sin(r / 13 + f)
        best = min(best, (abs(math.radians(d) * r - wob), f))
    return best[0], best[1], r


def natural(x, y):
    r = math.hypot(x - C[0], y - C[1])
    h = cone(r) + 0.5 * math.sin(x / 9) * math.cos(y / 11)
    d, f, _ = flow_dist(x, y)
    if r > CRATER_R + 4:
        h -= 3.2 * smooth((10 - d) / 4)  # the lava channels
    a = math.degrees(math.atan2(y - C[1], x - C[0])) % 360
    if 232 < a < 288 and GULLY_R[0] - 6 < r < GULLY_R[1] + 6:
        k = smooth((6 - abs(r - sum(GULLY_R) / 2) + 5) / 4) * smooth((28 - abs(a - 260)) / 6)
        h -= 7 * k
    # The black-rock field round the volcano, rising into jagged hills at the edge.
    e = math.hypot(x - C[0], (y - C[1]) * 0.9)
    h += 24 * smooth((e - 228) / 26) * (0.75 + 0.25 * math.sin(math.atan2(y, x) * 9))
    return h


def spur_centre():
    return polar(SPUR, spiral_r(SPUR), 0)[:2]


def in_spur(x, y, shrink=1.0):
    sx, sy = spur_centre()
    return math.hypot(x - sx, y - sy) < 26 * shrink


def classify(c, n, info):
    if in_spur(c.x, c.y, 0.92):
        return None
    if n.z < 0.62:
        return ("volcano_basalt", "wall")
    r = math.hypot(c.x - C[0], c.y - C[1])
    if r < CRATER_R - 2:
        return ("volcano_crust", "wall")
    fd, _, _ = flow_dist(c.x, c.y)
    if fd < 16 or r < 70:
        return ("volcano_crust", "sand")  # hot rock with glowing cracks
    if c.z > 6 or info["d"] < 18:
        return ("volcano_slag", "sand")
    return ("volcano_basalt", "sand")


def lava_path(c, f, r0, r1, step=5.0):
    """A lava river down the cone, dipping well under the road where a bridge crosses."""
    pts = []
    r = r0
    while r <= r1:
        wob = 4 * math.sin(r / 13 + f)
        t = math.radians(f) + wob / r
        x, y = C[0] + r * math.cos(t), C[1] + r * math.sin(t)
        z = cone(r) - 2.6
        smp, d = c.nearest(x, y)
        if d < 26:
            z = min(z, lerp(smp.p.z - 3.5, z, kit.smooth((d - 10) / 16)))
        pts.append((x, y, 13.0, z))
        r += step
    return pts


def scenery(c, s_tunnel):
    ter = list(c.coll("Terrain").objects)
    for piece in c.pieces:
        if "bridge" in piece.name or "ramp" in piece.name:
            props.piers(c, piece, every=10, mat=("volcano_basalt", "wall"), size=1.0, terrain=ter, inset=1.6)
    cols, dead = props.basalt_columns(c), props.dead_tree(c)
    rocks = [props.boulder(c, "volcano_basalt", v) for v in range(3)]
    gems = props.crystals(c)

    def away(m0, m1):
        def ok(x, y, z):
            smp, d = c.nearest(x, y)
            fd, _, r = flow_dist(x, y)
            return smp.w / 2 + m0 < d < smp.w / 2 + m1 and fd > 12 and r > CRATER_R + 6 and not in_spur(x, y, 1.1)
        return ok

    props.scatter(c, cols, 22, (-230, 250, -210, 270), away(8, 70), ter, seed=200, scale=(0.8, 1.8), sink=0.5)
    props.scatter(c, dead, 34, (-230, 250, -210, 270), away(5, 50), ter, seed=210)
    for v, r in enumerate(rocks):
        props.scatter(c, r, 12, (-230, 250, -210, 270), away(5, 60), ter, seed=220 + v, scale=(1.0, 3.0))
    # Glowing crystals inside the tunnel, along both walls.
    s0, s1 = s_tunnel
    for k in range(8):
        smp = c.at(s0 + (s1 - s0) * (k + 0.5) / 8)
        p = smp.side((1 if k % 2 else -1) * (smp.w / 2 + 2.2))
        c.place(gems, p.x, p.y, p.z - 0.3, rot=k * 1.1, scale=1.0 + 0.3 * (k % 3), role="visual", coll="Props")
    # Smoke rising from the crater.
    bm = bmesh.new()
    rings = []
    for k in range(7):
        z = LAVA_LAKE_Z + 4 + k * 14
        r = 12 + k * 7 + 3 * math.sin(k * 1.7)
        rings.append(props.ring(bm, (C[0] + 4 * math.sin(k), C[1] + 6 * k), r, z, 12))
    props.loft(bm, rings, cap_top=False)
    smoke = c.mesh_object("Crater Smoke", bm, "Backdrop", "visual")
    c.assign(smoke, c.lib("smoke"))
    # Lava falls spilling over the crater rim into the rivers.
    for f in FLOWS:
        x, y, _ = polar(f, CRATER_R + 1, 0)
        c.disc("Rim Glow %d" % int(f), x, y, 6, cone(CRATER_R) - 1.5, c.lib("volcano_lava"), role="visual", n=12)


def main():
    c = kit.Course(TRACK_ID, "Ember Peak", "volcano_dusk")
    c.route(ROUTE, width=14.0, bank=7.0)
    basalt = ("volcano_basalt", "wall")
    c.kinds = {
        "ash": {"mat": "volcano_ashroad", "shoulder": 1.5, "shoulder_mat": ("volcano_slag", "dirt")},
        "bridge": {
            "mat": "ember_road",
            "surface": "road",
            "shoulder": 0.6,
            "shoulder_mat": ("volcano_basalt", "road"),
            "barrier": 1.1,
            "barrier_mat": basalt,
            "deck": 2.0,
            "deck_mat": basalt,
            "ground": False,
        },
        "cave": {"mat": "ember_road", "surface": "road", "shoulder": 1.0, "shoulder_mat": ("volcano_crust", "dirt")},
        "ramp": {
            "mat": "ember_road",
            "surface": "road",
            "shoulder": 0.6,
            "shoulder_mat": ("volcano_basalt", "road"),
            "barrier": 1.0,
            "barrier_mat": basalt,
            "deck": 2.0,
            "deck_mat": basalt,
            "ground": False,
        },
    }
    s_lip = kit.s_near(c, *polar(259, GULLY_R[0] - 1, 0)[:2])
    s_land = kit.s_near(c, *polar(259, GULLY_R[1] + 2, 0)[:2])

    def label(smp):
        x, y = smp.p.x, smp.p.y
        if s_lip <= smp.s <= s_land:
            return "gap"
        if s_lip - 26 <= smp.s < s_lip:
            return "ramp"
        if in_spur(x, y, 0.98):
            return "cave"
        d, _, r = flow_dist(x, y)
        if d < 13 and r > CRATER_R + 4:
            return "bridge"
        if smp.p.z - natural(x, y) > 4.5:
            return "bridge"
        return "ash"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "ramp":
            specials.append((s0, s1, "ramp", {"lift": lambda u, n: 1.2 * max(0.0, (u - (n - 9)) / 9) ** 2}))
        elif k != "ash":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "ash"))

    c.terrain("Volcano", -250, 270, -230, 290, 3.3, natural, classify, near=8.5, fade=18.0)
    lava = c.lib("volcano_lava")
    for k, f in enumerate(FLOWS):
        c.ribbon("Lava River %d" % (k + 1), lava_path(c, f, CRATER_R + 2, 196), 13, 0, lava, steps=3)
    c.disc("Lava Lake", C[0], C[1], CRATER_R - 6, LAVA_LAKE_Z, lava, n=32, wobble=0.08)
    # The gully's lava, an arc under the jump.
    arc = []
    for a in range(230, 292, 4):
        x, y, _ = kit.Vector(polar(a, sum(GULLY_R) / 2, 0))
        arc.append((x, y, 10.0, natural(x, y) + 1.4))
    c.ribbon("Lava Gully", arc, 10, 0, lava, steps=2)

    sx, sy = spur_centre()
    rs = spiral_r(SPUR)
    base = cone(rs) - 6
    rock = c.rock_mass("Tunnel Spur", sx, sy, 28, 26, cone(rs) + 16, z0=base - 6, n=24, seed=5, base=base,
                       bands=[(1.0, 0.0), (1.0, 0.4), (0.9, 0.45), (0.86, 0.75), (0.7, 0.8), (0.6, 1.0)])
    inside = kit.crossings(c, lambda s: in_spur(s.p.x, s.p.y, 1.0), margin=0)
    s0, s1 = max(inside, key=lambda r: r[1] - r[0])
    c.tunnel(rock, s0, s1, height=9.0, pad=12.0)
    c.paint_rock(rock, ("volcano_crust", "wall"), ("volcano_slag", "sand"), floor=("volcano_ashroad", "dirt"), top_z=cone(rs) + 10, floor_z=cone(rs) + 2)

    c.start_line()
    scenery(c, (s0, s1))
    L = c.length
    c.zipper(s_lip - 20, 0)
    c.zipper(kit.s_near(c, *polar(40, 158, 0)[:2]), 0)
    c.zipper(kit.s_near(c, *polar(220, 52, 0)[:2]), -2)
    for at, across in ((60, 0), (kit.s_near(c, *polar(90, 140, 0)[:2]), 2), (s1 + 25, 0), (kit.s_near(c, *polar(240, 45, 0)[:2]), 0), (L - 60, -2)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in (
        (130, -3, "red"),
        (130, 3, "blue"),
        (kit.s_near(c, *polar(60, 150, 0)[:2]), 0, "green"),
        (kit.s_near(c, *polar(180, 75, 0)[:2]), 0, "yellow"),
        (kit.s_near(c, *polar(262, 146, 0)[:2]), 0, "rainbow"),
    ):
        c.balloon(at, across, col)

    # Falling into the gully: the lava bounces you; give up and you're put down past it.
    c.entity("respawn", **{"from": round(s_lip - 30, 1), "to": round(s_land + 6, 1), "at": round(s_land + 14, 1)})

    # Checkpoints: round the climb, out of the tunnel, at the summit, and just past the
    # gully's landing (beyond where falling in puts you).
    c.checkpoints(extra=[s1 + 10, kit.s_near(c, *polar(246, 46, 0)[:2]), s_land + 24])

    ter = list(c.coll("Terrain").objects)
    c.preset("sun", ter + [rock], 0.35)
    c.preset("bottoms", ter, 0.4)
    c.preset("cover", [rock], 0.7)
    kit.paint.shade_roads(c.pieces, 0.6)
    c.finish()


main()
