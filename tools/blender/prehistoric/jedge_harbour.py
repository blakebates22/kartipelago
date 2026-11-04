# The Smugglers' Docks' harbour, rebuilt (Blake, Nov 4: "theres a harbor that makes no sense.
# the boats are passing through bridges, the river is coming from no where. this underground
# harber needs to be way more immersive and high fidelity").
# SPDX-License-Identifier: MIT
#
# The water has a way in and a way out:
#   the sea leak    the sea pours in through a crack in the roof over the basin's west side,
#                   a shaft of sea light down with it, spray and mist at its foot;
#   the basin       the harbour: stone quays round it, wet and dark at the waterline, glowing
#                   algae, barnacles, weed; real ships moored with their ropes to bollards;
#   the canal       the outflow, running east (the water flowing), under the road's stone
#                   bridge (an arch the boats row under), past a boom, over a weir into the
#                   sump pool, and away through the iron water gate in the cavern's wall.
# Rowing boats with lanterns ply one round: about the basin, down the canal's south side,
# round at the boom, back up its north side, never across the road but under its arch.
# On the walls: shacks on stilts in two tiers, boardwalks along the lower, rope bridges
# between the upper, pulleys hauling cargo nets up and down; a crane swinging crates over
# the road; lantern light glinting on the water.

import math

from course_kit import bmesh, lerp
from pocket_build import box, cone
import props
import gulch_props as gp
import harbour_props as hp
import region_paint as paint
import jedge_layout as L
from jedge_layout import BASIN, CANAL, DOCK_FLOOR, DOCK_WATER, DOCKS, SEA_LEAK, SUMP_DROP, WEIR_X

D = None  # (jedge_districts: set by build, for person, light and the rest)


def _mesh(c, name, bm, mat, role="visual"):
    ob = c.mesh_object(name, bm, "Props", role)
    c.assign(ob, c.lib(mat, "wall"))
    return ob


def _game(c, x, y, z):
    return [round(v, 2) for v in c.game(x, y, z)]


# ------------------------------------------------------------------ the water


def water(c):
    """The basin's water, the canal flowing east, the sump pool under the weir."""
    bx, by, br = BASIN
    cy, hw, cx0, cx1 = CANAL
    c.disc("Harbour", bx, by, br + 1.5, DOCK_WATER, c.lib("dark_pool", "water"), role="visual", n=48, wobble=0.04, seed=4)
    run = [(x, cy) for x in [cx0 - 4.0 + k * 3.0 for k in range(int((WEIR_X - cx0 + 4.0) / 3.0) + 1)]] + [(WEIR_X, cy)]
    c.ribbon("Canal", run, 2 * hw + 1.6, DOCK_WATER + 0.01, c.lib("harbour_flow", "deep_water"), role="visual")
    c.ribbon("Sump Pool", [(WEIR_X - 0.3, cy), (cx1 + 5.0, cy)], 2 * hw + 1.6, DOCK_WATER - SUMP_DROP, c.lib("harbour_flow", "deep_water"),
             role="visual")


def _wall_band(c, name, pts, closed, inward):
    """A quay's wall along pts (x, y) at the water: dressed stone from under the water to the
    quay's edge, wet and dark over its lower half, a band of glowing algae at the waterline,
    barnacles scattered on it, its coping a step proud. `inward`: the water's side (+1: to
    the left of the line's direction)."""
    if closed:
        pts = pts + pts[:1]
    stone, wet, glow, barn, cope = (bmesh.new() for _ in range(5))
    z0, zw, z1 = DOCK_WATER - 1.6, DOCK_WATER + 0.9, DOCK_FLOOR + 0.18
    for k, ((ax, ay), (bx, by)) in enumerate(zip(pts, pts[1:])):
        dx, dy = bx - ax, by - ay
        n = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / n * inward, dx / n * inward  # (toward the water)
        for bm, lo, hi, off in ((wet, z0, zw, 0.0), (stone, zw, z1, 0.0), (glow, DOCK_WATER - 0.05, DOCK_WATER + 0.32, 0.04)):
            v = [bm.verts.new((ax + nx * off, ay + ny * off, lo)), bm.verts.new((bx + nx * off, by + ny * off, lo)),
                 bm.verts.new((bx + nx * off, by + ny * off, hi)), bm.verts.new((ax + nx * off, ay + ny * off, hi))]
            bm.faces.new(v[::-1] if inward > 0 else v)
        props.cuboid(cope, ((ax + bx) / 2 + nx * 0.1, (ay + by) / 2 + ny * 0.1, z1 + 0.1), (n + 0.05, 0.7, 0.24), rot=math.atan2(dy, dx))
        for j in range(int(n / 0.7)):
            t = (j + 0.5) / int(n / 0.7) if int(n / 0.7) else 0.5
            r = 0.09 + 0.07 * D.rnd(k * 31 + j)
            zz = DOCK_WATER + 0.1 + 0.5 * D.rnd(k * 17 + j * 3)
            props.blob(barn, (lerp(ax, bx, t) + nx * 0.06, lerp(ay, by, t) + ny * 0.06, zz), r, sx=1.0, sy=1.0, sz=0.6, subdiv=0)
    for bm, mat, tag in ((stone, "bog_stone", "Stone"), (wet, "bog_dark_stone", "Wet"), (glow, "glow_moss", "Algae"),
                         (barn, "limestone", "Barnacles"), (cope, "keep_ashlar_dark", "Coping")):
        _mesh(c, "%s %s" % (name, tag), bm, mat, role="both" if tag == "Stone" else "visual")


def quays(c, ground, taken):
    """The quay walls round the basin and both sides of the canal (but where the bridge
    crosses), bollards and timber fenders along them, ladders down to the water, weed
    hanging over the edge."""
    bx, by, br = BASIN
    cy, hw, cx0, cx1 = CANAL
    # (the basin's wall, round but where the canal leaves it)
    ring = []
    for j in range(72):
        a = j * math.tau / 72
        x, y = bx + (br + 0.6) * math.cos(a), by + (br + 0.6) * math.sin(a)
        if abs(y - cy) < hw + 0.6 and x > bx:
            if ring:
                _wall_band(c, "Basin Quay %d" % j, ring, False, 1)
                ring = []
            continue
        ring.append((x, y))
    if ring:
        _wall_band(c, "Basin Quay End", ring, False, 1)
    x_bridge = (-11.5, 5.5)
    x_mouth = bx + math.sqrt((br + 0.6) ** 2 - (hw + 0.3) ** 2)
    for sd in (-1, 1):
        y = cy + sd * (hw + 0.3)
        for name, xa, xb in (("West", x_mouth, x_bridge[0]), ("East", x_bridge[1], cx1 + 3.0)):
            pts = [(x, y) for x in [lerp(xa, xb, t / 12) for t in range(13)]]
            _wall_band(c, "Canal Quay %s %d" % (name, sd), pts, False, -sd)
    # Bollards, fenders, ladders and weed round the basin.
    for j in range(24):
        a = j * math.tau / 24 + 0.13
        x, y = bx + (br + 1.3) * math.cos(a), by + (br + 1.3) * math.sin(a)
        if abs(y - cy) < hw + 1.5 and x > bx:
            continue
        if j % 2 == 0:
            cone(c, "Bollard %d" % j, x, y, 0.32, DOCK_FLOOR + 0.25, 0.85, ("iron", "wall"), segs=8, role="visual")
        fx, fy = bx + (br + 0.45) * math.cos(a + 0.08), by + (br + 0.45) * math.sin(a + 0.08)
        D.tube(c, "Fender %d" % j, [(fx, fy, DOCK_WATER - 0.8), (fx, fy, DOCK_FLOOR + 0.1)], 0.22, "log_bark", n=6)
        if j % 5 == 1:
            for sd in (-0.3, 0.3):
                lx, ly = bx + (br + 0.35) * math.cos(a + sd * 0.03), by + (br + 0.35) * math.sin(a + sd * 0.03)
                D.tube(c, "Ladder %d %d" % (j, int(sd * 10)), [(lx, ly, DOCK_WATER - 1.0), (lx, ly, DOCK_FLOOR + 0.9)], 0.05, "iron")
        wx, wy = bx + (br + 0.62) * math.cos(a - 0.07), by + (br + 0.62) * math.sin(a - 0.07)
        ux, uy = -math.sin(a) * 0.5, math.cos(a) * 0.5
        D.cloth(c, "Weed %d" % j, [(wx - ux, wy - uy, DOCK_FLOOR + 0.1), (wx + ux, wy + uy, DOCK_FLOOR + 0.1),
                                   (wx + ux * 0.6, wy + uy * 0.6, DOCK_WATER + 0.1), (wx - ux * 0.6, wy - uy * 0.6, DOCK_WATER + 0.3)],
                "wreck_moss")
    for k in range(10):
        x = cx0 + 4.0 + k * 6.0
        if -14.0 < x < 8.0:
            continue
        for sd in (-1, 1):
            y = cy + sd * (hw + 1.0)
            if k % 2 == 0:
                cone(c, "Canal Bollard %d %d" % (k, sd), x, y, 0.3, DOCK_FLOOR + 0.25, 0.8, ("iron", "wall"), segs=8, role="visual")
            D.cloth(c, "Canal Weed %d %d" % (k, sd), [(x - 0.5, cy + sd * (hw + 0.32), DOCK_FLOOR + 0.1),
                                                      (x + 0.5, cy + sd * (hw + 0.32), DOCK_FLOOR + 0.1),
                                                      (x + 0.3, cy + sd * (hw + 0.36), DOCK_WATER + 0.2),
                                                      (x - 0.3, cy + sd * (hw + 0.36), DOCK_WATER + 0.1)], "wreck_moss")
    taken.add(bx, by, br + 1.5)


def sea_leak(c, ground, taken):
    """The sea pouring in through a crack in the roof: the crack (glowing with sea light),
    the falls, their foam and spray, a shaft of light down to the water, motes drifting in
    it, the roar."""
    x, y, z = SEA_LEAK
    bm = bmesh.new()
    pts = []
    for k in range(9):
        t = k / 8
        px = x + (t - 0.5) * 9.0
        py = y + 0.9 * math.sin(t * 7.0) + (t - 0.5) * 2.0
        pts.append((px, py, z + 0.4 * math.sin(t * 11.0)))
    for (ax, ay, az), (bx2, by2, bz) in zip(pts, pts[1:]):
        w = 0.7
        v = [bm.verts.new((ax, ay - w, az)), bm.verts.new((bx2, by2 - w, bz)), bm.verts.new((bx2, by2 + w, bz)), bm.verts.new((ax, ay + w, az))]
        bm.faces.new(v)
        bm.faces.new([bm.verts.new(p.co) for p in reversed(v)])
    _mesh(c, "Sea Leak Crack", bm, "glow_moss")
    props.falls(c, "Sea Leak Falls", x, y, z - 0.2, DOCK_WATER + 0.05, 3.2, 5.5, facing=1, throw=1.4, bulge=0.6, veils=3, foam=True,
                foam_r=4.2, mats=("falls_oasis", "falls_curtain_oasis", "falls_foam"))
    shaft = bmesh.new()
    rings = [props.ring(shaft, (x, y + 0.6), r, zz, 16) for r, zz in ((1.6, z - 0.3), (4.0, (z + DOCK_WATER) / 2), (6.5, DOCK_WATER + 0.1))]
    props.loft(shaft, rings, cap_top=False)
    _mesh(c, "Sea Light Shaft", shaft, "light_shaft")
    g = _game(c, x, y + 1.0, DOCK_WATER)
    c.entity("waterfall", x=g[0], y=g[1], z=g[2], top=round(z - DOCK_WATER, 1), width=5.0, heading=0)
    for dz, r, rate in ((0.6, 9.0, 7.0), (3.0, 14.0, 3.0)):
        g = _game(c, x, y + 1.0, DOCK_WATER + dz)
        c.entity("mist", x=g[0], y=g[1], z=g[2], radius=r, rate=rate, color="#c8dcd8")
    g = _game(c, x, y + 1.0, (z + DOCK_WATER) / 2)
    c.entity("motes", x=g[0], y=g[1], z=g[2], radius=6.0, rate=10.0, color="#bff4ea", rise=-0.15, size=0.16, blink=False)
    g = _game(c, x, y + 1.0, DOCK_WATER + 2.0)
    c.entity("glow", x=g[0], y=g[1], z=g[2], color="#5ad8c8")
    taken.add(x, y, 7.0)


def weir_and_gate(c, ground, taken):
    """The canal's end: a boom of floats across it (the boats turn there), the weir the
    water spills over into the sump pool, and the iron water gate in the cavern's wall it
    runs away through; a winch platform over the gate, its keepers."""
    cy, hw, cx0, cx1 = CANAL
    # (the boom)
    bx = WEIR_X - 3.5
    for sd in (-1, 1):
        box(c, "Boom Post %d" % sd, bx, cy + sd * (hw + 0.6), 0.18, 0.18, DOCK_WATER - 1.0, DOCK_FLOOR + 1.4, ("weathered_timber", "wall"),
            role="visual")
    chain = [(bx, cy - hw - 0.6, DOCK_FLOOR + 1.0), (bx, cy, DOCK_WATER + 0.25), (bx, cy + hw + 0.6, DOCK_FLOOR + 1.0)]
    D.tube(c, "Boom Chain", chain, 0.06, "iron")
    for k in range(7):
        D.egg(c, "Boom Float %d" % k, bx, cy - hw + 0.8 + k * (2 * hw - 1.6) / 6, DOCK_WATER - 0.25, 0.28,
              ("awning_red", "sail_cloth")[k % 2])
    # (the weir: a stone lip the water pours over)
    box(c, "Weir", WEIR_X, cy, 0.35, hw + 0.4, DOCK_WATER - SUMP_DROP - 1.0, DOCK_WATER - 0.03, ("bog_dark_stone", "wall"), role="visual")
    props.falls(c, "Weir Falls", WEIR_X + 0.1, cy, DOCK_WATER + 0.02, DOCK_WATER - SUMP_DROP + 0.05, 2 * hw, 2 * hw, facing=1, throw=0.5,
                bulge=0.25, veils=2, foam=False, angle=-math.pi / 2, mats=("falls_oasis", "falls_curtain_oasis", "falls_foam"))
    g = _game(c, WEIR_X + 1.5, cy, DOCK_WATER - SUMP_DROP + 0.4)
    c.entity("mist", x=g[0], y=g[1], z=g[2], radius=6.0, rate=4.0, color="#c8dcd8")
    # (the water gate: stone piers, an arch, the portcullis, the dark beyond)
    gx = cx1 + 1.0
    zb, zt = DOCK_WATER - SUMP_DROP - 1.5, DOCK_FLOOR + 5.5
    for sd in (-1, 1):
        box(c, "Water Gate Pier %d" % sd, gx, cy + sd * (hw + 1.0), 1.0, 1.0, zb, zt, ("keep_ashlar_dark", "wall"))
    box(c, "Water Gate Lintel", gx, cy, 1.1, hw + 2.0, zt - 1.4, zt, ("keep_ashlar_dark", "wall"), role="visual")
    box(c, "Water Gate Dark", gx + 1.4, cy, 0.2, hw + 0.2, zb, zt - 1.4, ("window_dark", "wall"), role="visual")
    bars = bmesh.new()
    for k in range(13):
        y = cy - hw + k * (2 * hw) / 12
        props.tube(bars, [(gx - 0.4, y, zb + 0.6), (gx - 0.4, y, zt - 1.4)], 0.07, n=4)
    for zz in (DOCK_WATER - SUMP_DROP + 0.6, DOCK_WATER + 0.8, DOCK_FLOOR + 3.0):
        props.tube(bars, [(gx - 0.45, cy - hw, zz), (gx - 0.45, cy + hw, zz)], 0.08, n=4)
    _mesh(c, "Water Gate Portcullis", bars, "keep_iron")
    box(c, "Water Gate Walk", gx - 1.5, cy, 1.6, hw + 2.2, zt - 0.2, zt + 0.1, ("plank_deck", "wall"), role="visual")
    for sd in (-1, 1):
        D.tube(c, "Water Gate Chain %d" % sd, [(gx - 0.6, cy + sd * (hw - 0.6), zt), (gx - 0.4, cy + sd * (hw - 0.6), zt - 1.6)], 0.08, "iron")
        cone(c, "Winch %d" % sd, gx - 1.5, cy + sd * (hw + 0.4), 0.6, zt + 0.1, 1.0, ("weathered_timber", "wall"), segs=8, role="visual")
        D.light(c, "torch", gx - 1.2, cy + sd * (hw + 1.6), zt + 1.6)
        D.person(c, gx - 1.6, cy + sd * (hw - 1.4), zt + 0.1, "guard", gx - 10.0, cy)
    taken.add(gx - 3.0, cy, hw + 4.0)


# ------------------------------------------------------------------ the bridge


def bridge(c, ground, taken):
    """The road's stone bridge over the canal: its body down to an arch over the water,
    the arch's ring proud on both faces with its keystone, lanterns at its four corners,
    their light glinting on the water."""
    cy, hw, cx0, cx1 = CANAL
    xa, xb = -11.4, 5.4

    def arch(y):
        dy = abs(y - cy) / (hw + 0.2)
        if dy >= 1.0:
            return DOCK_FLOOR - 0.6
        return DOCK_WATER + 0.25 + 2.05 * math.sqrt(1.0 - dy * dy)

    ys = [cy - hw - 3.0 + k * 0.5 for k in range(int((2 * hw + 6.0) / 0.5) + 1)]
    top = [L.road_floor(-3.0, y)[1] - 1.1 for y in ys]
    bot = [min(arch(y), t - 0.1) for y, t in zip(ys, top)]
    bm = bmesh.new()
    F = [[bm.verts.new((xa, y, b)), bm.verts.new((xa, y, t))] for y, b, t in zip(ys, bot, top)]
    B = [[bm.verts.new((xb, y, b)), bm.verts.new((xb, y, t))] for y, b, t in zip(ys, bot, top)]
    for i in range(len(ys) - 1):
        bm.faces.new((F[i][0], F[i + 1][0], F[i + 1][1], F[i][1]))
        bm.faces.new((B[i][1], B[i + 1][1], B[i + 1][0], B[i][0]))
        bm.faces.new((F[i][0], B[i][0], B[i + 1][0], F[i + 1][0]))
    _mesh(c, "Harbour Bridge Body", bm, "bog_stone")
    ring = bmesh.new()
    for x, sgn in ((xa, -1), (xb, 1)):
        for i in range(len(ys) - 1):
            if abs(ys[i] - cy) > hw + 0.2 or abs(ys[i + 1] - cy) > hw + 0.2:
                continue
            a0, a1 = arch(ys[i]), arch(ys[i + 1])
            v = [ring.verts.new((x + sgn * 0.12, ys[i], a0)), ring.verts.new((x + sgn * 0.12, ys[i + 1], a1)),
                 ring.verts.new((x + sgn * 0.12, ys[i + 1], a1 + 0.65)), ring.verts.new((x + sgn * 0.12, ys[i], a0 + 0.65))]
            ring.faces.new(v if sgn > 0 else v[::-1])
        props.cuboid(ring, (x + sgn * 0.14, cy, arch(cy) + 0.45), (0.3, 0.7, 0.95))
    _mesh(c, "Harbour Bridge Arch", ring, "keep_ashlar_dark")
    for sx in (xa - 0.3, xb + 0.3):
        for sy in (cy - hw - 2.6, cy + hw + 2.6):
            z = L.road_floor(-3.0, sy)[1]
            c.place(gp.lantern_post(c), sx, sy, z - 0.2, rot=0.0 if sx > 0 else math.pi, role="visual")
            D.light(c, "lantern", sx + (1.1 if sx > 0 else -1.1), sy, z + 3.4)
            glint(c, "Bridge Glint %d %d" % (int(sx), int(sy)), sx + (1.4 if sx > 0 else -1.4), cy + (sy - cy) * 0.55, 2.2, 3.2)
    g = _game(c, xb + 1.0, cy, DOCK_WATER + 2.0)
    c.entity("glow", x=g[0], y=g[1], z=g[2], color="#ffb060")
    g = _game(c, xa - 1.0, cy, DOCK_WATER + 2.0)
    c.entity("glow", x=g[0], y=g[1], z=g[2], color="#ffb060")


def glint(c, name, x, y, w, h, rot=0.0):
    """Lantern light glinting on the water under a lantern: a streaky patch, flickering."""
    bm = bmesh.new()
    ca, sa = math.cos(rot), math.sin(rot)
    pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    bm.faces.new([bm.verts.new((x + px * ca - py * sa, y + px * sa + py * ca, DOCK_WATER + 0.04)) for px, py in pts])
    _mesh(c, name, bm, "water_glint")


# ------------------------------------------------------------------ ships and boats


SHIPS = ((1.75, 19.0), (2.55, 17.0), (4.5, 21.0))  # (angle round the basin, length)


def ships(c, ground, taken):
    """Three ships moored round the basin, side on to the quay, ropes to the bollards fore
    and aft, gangplanks, lanterns at their sterns; skiffs tied up between."""
    bx, by, br = BASIN
    for j, (a, ln) in enumerate(SHIPS):
        r = br - 4.3
        x, y = bx + r * math.cos(a), by + r * math.sin(a)
        rot = a + math.pi / 2
        c.place(hp.ship(c, j % 2, ln), x, y, DOCK_WATER, rot=rot, role="visual")
        ca, sa = math.cos(rot), math.sin(rot)
        for end in (-1, 1):
            ex, ey = x + ca * end * ln * 0.38, y + sa * end * ln * 0.38
            qa = math.atan2(ey - by, ex - bx)
            qx, qy = bx + (br + 1.3) * math.cos(qa), by + (br + 1.3) * math.sin(qa)
            mid = ((ex + qx) / 2, (ey + qy) / 2, DOCK_WATER + 0.8)
            D.tube(c, "Mooring %d %d" % (j, end), [(ex, ey, DOCK_WATER + 3.0), mid, (qx, qy, DOCK_FLOOR + 0.9)], 0.06, "rope_rail")
            cone(c, "Mooring Bollard %d %d" % (j, end), qx, qy, 0.34, DOCK_FLOOR + 0.25, 0.9, ("iron", "wall"), segs=8, role="visual")
        gx, gy = bx + (br + 1.6) * math.cos(a), by + (br + 1.6) * math.sin(a)
        sx, sy = x + (gx - x) * 0.18, y + (gy - y) * 0.18
        box(c, "Gangplank %d" % j, (sx + gx) / 2, (sy + gy) / 2, 0.7, math.hypot(gx - sx, gy - sy) / 2, DOCK_FLOOR - 0.05, DOCK_FLOOR + 0.05,
            ("plank_deck", "wall"), rot=a + math.pi / 2, role="visual")
        D.light(c, "lantern", x - ca * ln * 0.48, y - sa * ln * 0.48, DOCK_WATER + 6.2)
        glint(c, "Ship Glint %d" % j, x - ca * ln * 0.5, y - sa * ln * 0.5, 2.4, 4.0, rot)
        for k in range(3):
            px, py = lerp(x, gx, 0.25 + 0.3 * k), lerp(y, gy, 0.25 + 0.3 * k)
            D.person(c, px, py, DOCK_WATER + 2.6 if k == 0 else DOCK_FLOOR + 0.1, "hauler", gx if k % 2 else x, gy if k % 2 else y)
    for j, a in enumerate((0.6, 3.35, 5.4)):
        x, y = bx + (br - 1.6) * math.cos(a), by + (br - 1.6) * math.sin(a)
        c.place(hp.moored_skiff(c, j), x, y, DOCK_WATER, rot=a + math.pi / 2, role="visual")


def boat_round(c):
    """The rowing boats' round: about the basin (inside the moored ships), out down the
    canal's south side under the bridge's arch, round at the boom, back up its north side.
    Four boats on it, lanterns lit."""
    bx, by, br = BASIN
    cy, hw, cx0, cx1 = CANAL
    r = 8.0
    pts = []
    for k in range(12):
        a = math.radians(24.0 + k * (312.0 / 11))
        pts.append((bx + 2.0 + r * math.cos(a), by + r * math.sin(a)))
    lane = 2.4
    turn = WEIR_X - 6.5
    for x in [cx0 - 2.0 + k * 6.0 for k in range(int((turn - cx0) / 6.0))]:
        pts.append((x, cy - lane))
    pts += [(turn, cy - lane), (turn + 1.8, cy - 1.4), (turn + 2.2, cy), (turn + 1.8, cy + 1.4), (turn, cy + lane)]
    for x in reversed([cx0 - 2.0 + k * 6.0 for k in range(int((turn - cx0) / 6.0))]):
        pts.append((x, cy + lane))
    c.path_curve("Harbour Boat Round", pts, z=DOCK_WATER, closed=True)
    for k in range(4):
        c.entity("boat", route="Harbour Boat Round", speed=2.1 + 0.15 * (k % 2), start=k * 52.0, rig="row",
                 colors=[("#2a5a4a", "#7a2a22", "#3a3a5a", "#6a4a1a")[k], "#d8c8a0"], scale=0.8)
    return pts


# ------------------------------------------------------------------ the walls


def _wall_spot(e, a):
    return DOCKS[0] + DOCKS[2] * e * math.cos(a), DOCKS[1] + DOCKS[3] * e * math.sin(a)


def _edge_point(x, y, pw, pd, rot, ux, uy):
    """Where a ray from a platform's middle (x, y) along (ux, uy) leaves its edge (the
    platform pw x pd, turned rot)."""
    ca, sa = math.cos(rot), math.sin(rot)
    lx, ly = ux * ca + uy * sa, -ux * sa + uy * ca
    t = min((pw / 2) / abs(lx) if abs(lx) > 1e-6 else 1e9, (pd / 2) / abs(ly) if abs(ly) > 1e-6 else 1e9)
    return x + ux * t, y + uy * t


def stilts(c, ground, taken):
    """Shacks on stilts round the cavern's walls, their doors to the cavern's middle: a
    lower tier on short stilts with boardwalks between them, an upper tier on tall stilts
    behind with rope bridges between; every walkway runs from one platform's edge to the
    next's, a post at each end its rails are tied to (review 1 note 5: "make sure all the
    roped and bridges are rigoursly connected and not floating"). Pulleys out from the
    upper tier hold cargo still on their ropes over the stacks below. Returns how many."""
    bx, by, br = BASIN
    cy, hw, cx0, cx1 = CANAL
    tiers = [(0.79, 2.2, 0.0), (0.9, 5.2, 0.045)]
    built = [[], []]
    n = 0
    for t, (e, ph, shift) in enumerate(tiers):
        for k in range(64):
            a = k * math.tau / 64 + shift
            x, y = _wall_spot(e, a)
            w = 4.6 + 1.4 * D.rnd(k + 7 * t)
            d = 3.4 + 0.8 * D.rnd(k * 3 + t)
            reach = max(w, d) / 2 + 2.0
            if L.in_water(x, y) or math.hypot(x - bx, y - by) < br + reach + 1.0 or abs(y - cy) < hw + reach + 1.0 and x > cx0:
                continue
            if not paint.road_clear(c, x, y, reach + (3.0 if t == 0 else 1.0)) or not taken.clear(x, y, reach if t == 0 else 1.0):
                continue
            if built[t] and math.hypot(x - built[t][-1]["x"], y - built[t][-1]["y"]) < reach + built[t][-1]["reach"] + 0.8:
                continue
            z = ground(x, y)
            if abs(z - DOCK_FLOOR) > 1.0:
                continue
            rot = a - math.pi / 2  # (its door, its -Y, to the cavern's middle)
            c.place(hp.stilt_shack(c, k + t, ph, w, d, 2.6 + 0.4 * (k % 2)), x, y, z, rot=rot, coll="Village", role="visual")
            box(c, "Stilt Shack Solid %d %d" % (t, k), x, y, w / 2 + 0.8, d / 2 + 1.3, z - 0.5, z + ph + 2.8, ("wreck_planks", "wall"),
                rot=rot, role="collision")
            fx, fy = x - math.cos(a) * (d / 2 + 1.3), y - math.sin(a) * (d / 2 + 1.3)
            D.light(c, "lantern", fx, fy, z + ph + 2.4)
            built[t].append({"x": x, "y": y, "z": z + ph + 0.15, "reach": reach, "a": a, "fx": fx, "fy": fy, "pw": w + 1.6,
                             "pd": d + 2.6, "rot": rot, "ground": z})
            if t == 0:
                taken.add(x, y, reach)
            n += 1
            if k % 3 == 0:
                D.person(c, fx, fy, z + ph + 0.15, ("fisher", "huddle", "worker")[k % 3], bx, by)
    # (the walkways: platform edge to platform edge, a post at each end, the rails tied to them)
    for t, row in enumerate(built):
        for A, B in zip(row, row[1:]):
            gap = math.hypot(B["x"] - A["x"], B["y"] - A["y"])
            if gap > 16.0:
                continue
            ux, uy = (B["x"] - A["x"]) / gap, (B["y"] - A["y"]) / gap
            ax, ay = _edge_point(A["x"], A["y"], A["pw"], A["pd"], A["rot"], ux, uy)
            bx2, by2 = _edge_point(B["x"], B["y"], B["pw"], B["pd"], B["rot"], -ux, -uy)
            ax, ay, bx2, by2 = ax - ux * 0.25, ay - uy * 0.25, bx2 + ux * 0.25, by2 + uy * 0.25
            dip = 0.0 if t == 0 else 0.8
            span = [(lerp(ax, bx2, s / 10), lerp(ay, by2, s / 10), lerp(A["z"], B["z"], s / 10) - dip * math.sin(math.pi * s / 10))
                    for s in range(11)]
            planks = bmesh.new()
            for s in range(10):
                (x0, y0, z0), (x1, y1, z1) = span[s], span[s + 1]
                props.cuboid(planks, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2 - 0.05),
                             (math.hypot(x1 - x0, y1 - y0) * 0.92, 1.3, 0.1), rot=math.atan2(y1 - y0, x1 - x0),
                             tilt=(0.0, -math.atan2(z1 - z0, math.hypot(x1 - x0, y1 - y0))))
            _mesh(c, "Walkway %d %d" % (t, int(A["x"])), planks, "plank_deck")
            for sd in (-1, 1):
                ox, oy = -uy * sd * 0.7, ux * sd * 0.7
                ends = []
                for (px, py, pz) in (span[0], span[-1]):
                    D.tube(c, "Walkway Post %d %d %d %d" % (t, int(A["x"]), sd, int(px)), [(px + ox, py + oy, pz - 0.2), (px + ox, py + oy, pz + 1.1)],
                           0.07, "weathered_timber", n=5)
                    ends.append((px + ox, py + oy, pz + 1.05))
                rail = [ends[0]] + [(px + ox, py + oy, pz + 1.0) for px, py, pz in span[1:-1]] + [ends[1]]
                D.tube(c, "Walkway Rail %d %d %d" % (t, int(A["x"]), sd), rail, 0.035, "rope_rail" if t else "weathered_timber")
                if t:
                    for px, py, pz in span[2:-2:2]:
                        D.tube(c, "Walkway Hanger %d %d %d %d" % (t, int(A["x"]), sd, int(px * 10)),
                               [(px + ox, py + oy, pz + 1.0), (px + ox, py + oy, pz)], 0.02, "rope_rail", n=3)
            if t == 0:
                for s in (3, 7):
                    px, py, pz = span[s]
                    D.tube(c, "Walkway Leg %d %d" % (int(A["x"]), s), [(px, py, DOCK_FLOOR - 0.3), (px, py, pz - 0.1)], 0.13, "weathered_timber", n=5)
    # (pulleys from the upper tier: a beam out over the floor, the rope down, the load on its
    # hook still, just over the stack it's going on)
    for j, P in enumerate(built[1]):
        if j % 2:
            continue
        a = P["a"]
        tipx, tipy = P["fx"] - math.cos(a) * 1.6, P["fy"] - math.sin(a) * 1.6
        if not paint.road_clear(c, tipx, tipy, 3.0):
            continue
        top = P["z"] + 3.1
        D.tube(c, "Pulley Beam %d" % j, [(P["fx"] + math.cos(a) * 1.0, P["fy"] + math.sin(a) * 1.0, top), (tipx, tipy, top)], 0.12,
               "weathered_timber", n=5)
        D.tube(c, "Pulley Strut %d" % j, [(P["fx"], P["fy"], P["z"] + 0.1), (tipx + math.cos(a) * 1.0, tipy + math.sin(a) * 1.0, top)], 0.08,
               "weathered_timber", n=4)
        cone(c, "Pulley Block %d" % j, tipx, tipy, 0.18, top - 0.3, 0.3, ("iron", "wall"), segs=6, role="visual")
        g = ground(tipx, tipy)
        c.place(gp.crate_stack(c, j % 3), tipx, tipy, g, rot=a, role="visual")
        load_z = g + 2.6
        D.tube(c, "Pulley Rope %d" % j, [(tipx, tipy, top - 0.3), (tipx, tipy, load_z + 0.55)], 0.035, "rope_rail", n=3)
        if j % 4 == 0:
            D.egg(c, "Pulley Net %d" % j, tipx, tipy, load_z - 0.4, 0.55, "isle_net")
        else:
            box(c, "Pulley Crate %d" % j, tipx, tipy, 0.45, 0.45, load_z - 0.4, load_z + 0.5, ("wood_dock", "wall"), rot=a, role="visual")
    return n


def road_crane(c, ground, taken):
    """A big harbour crane on the canal's north bank, east of the road, its jib out over
    the road, a slung pallet of crates on its hook (high over the karts: its bottom 5 m
    and more over the road)."""
    x, y = 13.0, -289.0
    z = ground(x, y)
    c.place(hp.harbour_crane(c, 1, height=7.0, reach=14.0, drop=3.5, load="pallet"), x, y, z - 0.3, rot=math.pi, role="visual")
    box(c, "Road Crane Solid", x, y, 2.0, 2.0, z - 0.5, z + 10.0, ("weathered_timber", "wall"), role="collision")
    D.light(c, "lantern", x + 1.8, y, z + 7.0 + 1.6)
    taken.add(x, y, 4.0)


KING = (-28.0, -325.0)  # the King Croc's throne, on the quay between the road and the basin


def king(c, ground, taken):
    """The King Croc holding court (Blake, Nov 4: "a big king croc on a throne"; review 1:
    "make it so we can actually see the croc"): on a stone dais on the quay right by the
    road, facing it, standing before his throne: a heap of treasure chests under a great
    carved back cut from a ship's stern, a ship's wheel behind it like a halo, gold spilled
    everywhere; braziers either side, his black banners, a rug down the steps to the road,
    his guards. He's three times the height of his people and watches you go by (the
    croc_king entity: render/people/crocKing.ts)."""
    x, y = KING
    z = ground(x, y)
    top = z + 1.4
    # (the dais and its steps down toward the road, east)
    box(c, "King Dais", x, y, 5.0, 4.5, z - 0.5, top, ("bog_stone", "wall"))
    box(c, "King Dais Coping", x, y, 5.2, 4.7, top - 0.1, top + 0.05, ("keep_ashlar_dark", "wall"), role="visual")
    for k in range(3):
        box(c, "King Step %d" % k, x + 5.0 + 0.5 + k * 0.7, y, 0.35, 2.8, z - 0.5, top - 0.45 * (k + 1), ("bog_stone", "wall"))
    D.cloth(c, "King Rug", [(x - 2.0, y - 1.2, top + 0.07), (x + 5.2, y - 1.2, top + 0.07), (x + 7.6, y - 1.2, z + 0.06),
                            (x + 7.6, y + 1.2, z + 0.06), (x + 5.2, y + 1.2, top + 0.07), (x - 2.0, y + 1.2, top + 0.07)], "royal_carpet")
    # (the throne: chests heaped, the carved stern-board back, the wheel)
    for k, (dx, dy, dz, s_, r) in enumerate(((-2.6, 0.0, 0.0, 1.6, 0.0), (-2.6, -1.9, 0.0, 1.2, 0.3), (-2.6, 1.9, 0.0, 1.2, -0.3),
                                              (-2.9, 0.0, 1.2, 1.3, 0.1), (-1.4, -2.6, 0.0, 1.0, 0.8), (-1.2, 2.7, 0.0, 1.0, -0.7))):
        c.place(hp.treasure_chest(c, k, s_), x + dx, y + dy, top + dz, rot=math.pi / 2 + r, role="visual")
    box(c, "Throne Back", x - 3.6, y, 0.35, 2.4, top, top + 7.5, ("ship_hull", "wall"), role="visual")
    box(c, "Throne Back Trim", x - 3.4, y, 0.1, 2.5, top + 7.0, top + 7.6, ("gold_trim", "wall"), role="visual")
    for sd in (-1, 1):
        cone(c, "Throne Finial %d" % sd, x - 3.5, y + sd * 2.3, 0.35, top + 7.5, 1.1, ("gold_trim", "wall"), segs=6, role="visual")
    wheel = bmesh.new()
    cx_, cz_ = x - 3.25, top + 5.4
    pts = [(cx_, y + 2.0 * math.cos(k * math.tau / 20), cz_ + 2.0 * math.sin(k * math.tau / 20)) for k in range(21)]
    props.tube(wheel, pts, 0.14, n=6)
    for k in range(8):
        a = k * math.tau / 8
        props.tube(wheel, [(cx_, y, cz_), (cx_, y + 2.5 * math.cos(a), cz_ + 2.5 * math.sin(a))], 0.09, n=5)
    _mesh(c, "Throne Wheel", wheel, "weathered_timber")
    for k in range(9):
        a = k * 0.9
        D.egg(c, "King Gold %d" % k, x - 1.5 + 1.2 * math.cos(a), y + 2.8 * math.sin(a), top, 0.35 + 0.1 * (k % 3), "gold_trim")
    # (braziers either side of the dais front, banners behind)
    for sd in (-1, 1):
        bx_, by_ = x + 3.6, y + sd * 3.6
        D.tube(c, "Brazier Stand %d" % sd, [(bx_, by_, top), (bx_, by_, top + 1.4)], 0.12, "keep_iron", n=6)
        cone(c, "Brazier %d" % sd, bx_, by_, 0.75, top + 1.4, -0.6, ("keep_iron", "wall"), segs=8, role="visual")
        D.light(c, "campfire", bx_, by_, top + 1.5)
        px, py = x - 2.0, y + sd * 4.2
        D.tube(c, "Banner Pole %d" % sd, [(px, py, top), (px, py, top + 8.5)], 0.1, "weathered_timber", n=5)
        D.cloth(c, "King Banner %d" % sd, [(px, py, top + 8.3), (px + 0.1, py + sd * 2.2, top + 8.3), (px + 0.1, py + sd * 2.0, top + 4.6),
                                           (px, py + sd * 1.1, top + 5.2), (px, py, top + 4.6)], "wreck_sail")
        for k in range(3):
            D.person(c, x + 2.5 - k * 1.8, y + sd * 3.9, top + 0.05, "guard", x + 12.0, y)
    for k in range(4):
        D.person(c, x + 8.5, y - 3.0 + k * 2.0, z + 0.05, ("cheer", "wave", "cheer", "huddle")[k], x, y)
    # (the King himself: standing before his throne, facing the road)
    g = _game(c, x - 0.8, y, top)
    c.entity("croc_king", x=g[0], y=g[1], z=g[2], heading=round(math.pi / 2, 4))
    g = _game(c, x + 2.0, y, top + 4.0)
    c.entity("glow", x=g[0], y=g[1], z=g[2], color="#ffa050")
    taken.add(x, y, 9.0)


def harbour(c, ground, taken, dressing):
    """Everything above, in order (the water and its walls first: the rest keeps off them)."""
    global D
    D = dressing
    water(c)
    quays(c, ground, taken)
    king(c, ground, taken)
    sea_leak(c, ground, taken)
    weir_and_gate(c, ground, taken)
    bridge(c, ground, taken)
    ships(c, ground, taken)
    boat_round(c)
    road_crane(c, ground, taken)
