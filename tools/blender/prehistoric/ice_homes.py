# The ice carvers' homes in the Ice Hollow, every one its own (Blake, Oct 30: "they are too
# symmetrical looking ... so nicely and evenly laid out ... I want the detail to be higher
# ... they need a bit more individualism and character. too uniform is the main issue";
# he chose all four: break the ring, a carver's signature on each, lived-in clutter, mixed
# sizes and kinds).
#
# Seven kinds: a home cut into the wall, two stacked on a ledge with stairs and a bridge,
# a freestanding ice dome, a crooked ice tower, a wide workshop, a tiny hut, a home cut
# into one giant block of ice. Each family's sign (what it carves) stands over its door: a
# fish, an owl, a bear, a star, a snowflake, a crown. Each home picks its own arch, door
# colour, windows and clutter (awnings, shutters, wreaths, crooked stovepipes, woodpiles,
# drying lines of mittens and scarves, tool racks, strings of lights). Laid out by hand
# round the hollow, set in and out of the wall, turned a little off true. All our own
# designs; prototypes' fronts face +Y, their origins on the ground at the front.
# SPDX-License-Identifier: MIT

import math
import random

import region_paint as paint
import snow_layout as SL
from carvers_village import _crystal, _wedge
from keep_props import _p
from canyon_props import _beam
from props import blob, cuboid, loft, ring, tube

ICE = "glacier_ice"
BLUE = "icefall_blue"
CLEAR = "lake_ice"
SNOW = "snow_ground"
ROCK = "frost_cliff"  # (the backs, into the hollow's walls: the walls' own rock)
TIMBER = "timber_beam"
PLANK = "weathered_timber"
IRON = "keep_iron"
GLASS = "window_warm"
WREATH = "wreath"
LIGHTS = "xmas_lights"
LOGS = "log_end"
DECK = "plank_deck"
# (Blake, Oct 30, on draft 7: "it feels a bit too whimsical ... hearthglow hallow is
# supposed to be the whimsical portion of this world"; he chose the craftsmen's hollow:
# plain sturdy homes of stone, timber and packed snow, warm windows, dark wood doors; ice
# only as the carvers' craft, in their signs, lintels and showpieces.)
STONES = ("frost_stone", "rift_stone", "frost_stone")
DOORS = ("door_wood", "timber_beam", "weathered_timber", "door_wood", "siding_red", "siding_grey")
CLOTH = ("siding_red", "siding_grey", "timber_beam", "rift_stone", "snow_ground", "door_wood")
AWNINGS = ("weathered_timber", "timber_beam", "siding_grey", "siding_red")
LAMP = "lantern_amber"
SIGNS = ("fish", "owl", "bear", "star", "snowflake", "crown")


# ------------------------------------------------------------------ details


def sign(P, bm, kind, x, y, z, s=1.0):
    """A family's sign: what it carves, cut finely in ice (Blake, review-snow_region 3:
    "increase the resolution on all ice sculptures"), standing on a timber plaque held
    out on two iron brackets (centred at x, y, z; facing +Y)."""
    # The plaque and its brackets, back on the wall.
    P.add(TIMBER, lambda: cuboid(bm, (x, y - 0.55, z), (2.0 * s, 0.16, 1.8 * s)))
    P.add(TIMBER, lambda: cuboid(bm, (x, y - 0.45, z - 0.95 * s), (2.3 * s, 0.6, 0.16)))
    for sx in (-1, 1):
        P.add(IRON, lambda sx=sx: _beam(bm, (x + sx * 0.8 * s, y - 0.62, z - 0.6 * s), (x + sx * 0.8 * s, y - 0.2, z - 0.95 * s), 0.06))
    y = y - 0.15
    if kind == "fish":
        P.add(ICE, lambda: blob(bm, (x, y, z), 0.9 * s, sx=1.5, sy=0.5, sz=0.75, subdiv=2))
        P.add(ICE, lambda: blob(bm, (x + 0.95 * s, y, z - 0.05 * s), 0.38 * s, sx=1.0, sy=0.55, sz=0.8, subdiv=2))
        for sz in (-1, 1):
            P.add(BLUE, lambda sz=sz: _fin(bm, (x - 1.15 * s, y, z), (-0.55 * s, 0.0, 0.55 * s * sz), 0.18 * s))
        P.add(BLUE, lambda: _fin(bm, (x - 0.1 * s, y, z + 0.55 * s), (-0.45 * s, 0.0, 0.4 * s), 0.14 * s))
        P.add(BLUE, lambda: _fin(bm, (x + 0.2 * s, y + 0.3 * s, z - 0.35 * s), (-0.25 * s, 0.1 * s, -0.3 * s), 0.1 * s))
        P.add(BLUE, lambda: blob(bm, (x + 1.05 * s, y + 0.3 * s, z + 0.12 * s), 0.08 * s, subdiv=1))
        for k in range(4):  # (gill and scale lines)
            P.add(BLUE, lambda k=k: cuboid(bm, (x + (0.55 - k * 0.32) * s, y + 0.42 * s, z), (0.05 * s, 0.04, 0.9 * s * (1 - 0.15 * k))))
    elif kind == "owl":
        P.add(ICE, lambda: blob(bm, (x, y, z - 0.3 * s), 0.8 * s, sx=0.9, sy=0.7, sz=1.05, subdiv=2))
        P.add(ICE, lambda: blob(bm, (x, y + 0.05 * s, z + 0.72 * s), 0.6 * s, sx=1.05, sy=0.8, sz=0.85, subdiv=2))
        for sx in (-1, 1):
            P.add(CLEAR, lambda sx=sx: blob(bm, (x + sx * 0.26 * s, y + 0.42 * s, z + 0.78 * s), 0.24 * s, sy=0.4, subdiv=2))
            P.add(BLUE, lambda sx=sx: blob(bm, (x + sx * 0.26 * s, y + 0.52 * s, z + 0.78 * s), 0.09 * s, subdiv=1))
            P.add(ICE, lambda sx=sx: _fin(bm, (x + sx * 0.4 * s, y, z + 1.15 * s), (sx * 0.15 * s, 0.0, 0.38 * s), 0.12 * s))
            P.add(ICE, lambda sx=sx: blob(bm, (x + sx * 0.62 * s, y - 0.05 * s, z - 0.25 * s), 0.42 * s, sx=0.45, sy=0.6, sz=1.1, subdiv=2))
        P.add(BLUE, lambda: _fin(bm, (x, y + 0.55 * s, z + 0.62 * s), (0.0, 0.08 * s, -0.22 * s), 0.07 * s))
        for k in range(3):
            P.add(BLUE, lambda k=k: cuboid(bm, (x, y + 0.5 * s, z - 0.15 * s - k * 0.22 * s), (0.5 * s - 0.08 * k * s, 0.04, 0.05 * s)))
    elif kind == "bear":
        P.add(ICE, lambda: blob(bm, (x, y, z), 0.85 * s, sx=1.05, sy=0.8, sz=0.92, subdiv=2))
        P.add(CLEAR, lambda: blob(bm, (x, y + 0.6 * s, z - 0.25 * s), 0.38 * s, sx=1.05, sy=0.95, sz=0.72, subdiv=2))
        P.add(BLUE, lambda: blob(bm, (x, y + 0.95 * s, z - 0.12 * s), 0.12 * s, sx=1.3, sy=0.8, sz=0.8, subdiv=1))
        P.add(BLUE, lambda: cuboid(bm, (x, y + 0.88 * s, z - 0.42 * s), (0.26 * s, 0.04, 0.04 * s)))
        for sx in (-1, 1):
            P.add(ICE, lambda sx=sx: blob(bm, (x + sx * 0.6 * s, y, z + 0.7 * s), 0.3 * s, sy=0.6, subdiv=2))
            P.add(CLEAR, lambda sx=sx: blob(bm, (x + sx * 0.6 * s, y + 0.12 * s, z + 0.7 * s), 0.15 * s, sy=0.4, subdiv=1))
            P.add(BLUE, lambda sx=sx: blob(bm, (x + sx * 0.3 * s, y + 0.62 * s, z + 0.2 * s), 0.08 * s, subdiv=1))
            P.add(ICE, lambda sx=sx: _fin(bm, (x + sx * 0.38 * s, y + 0.5 * s, z + 0.38 * s), (sx * 0.18 * s, 0.02, 0.03 * s), 0.05 * s))
    elif kind == "star":
        P.add(ICE, lambda: blob(bm, (x, y, z), 0.42 * s, sy=0.6, subdiv=2))
        for k in range(5):
            a = math.pi / 2 + k * math.tau / 5
            P.add(BLUE if k % 2 else ICE, lambda a=a: _fin(bm, (x, y, z), (math.cos(a) * 1.25 * s, 0.0, math.sin(a) * 1.25 * s), 0.3 * s))
            b = a + math.tau / 10
            P.add(CLEAR, lambda b=b: _fin(bm, (x, y + 0.05, z), (math.cos(b) * 0.6 * s, 0.0, math.sin(b) * 0.6 * s), 0.16 * s))
    elif kind == "snowflake":
        P.add(ICE, lambda: blob(bm, (x, y, z), 0.25 * s, sy=0.5, subdiv=2))
        for k in range(6):
            a = k * math.tau / 6
            ca, sa = math.cos(a), math.sin(a)
            P.add(ICE, lambda ca=ca, sa=sa: _fin(bm, (x, y, z), (ca * 1.35 * s, 0.0, sa * 1.35 * s), 0.09 * s))
            for j, (t, ln) in enumerate(((0.45, 0.42), (0.75, 0.3))):
                for sd in (-1, 1):
                    b = a + sd * 0.75
                    bx, bz = x + ca * t * 1.35 * s, z + sa * t * 1.35 * s
                    P.add(BLUE, lambda bx=bx, bz=bz, b=b, ln=ln: _fin(bm, (bx, y, bz), (math.cos(b) * ln * s, 0.0, math.sin(b) * ln * s), 0.06 * s))
    else:  # the crown
        P.add("gold_trim", lambda: loft(bm, [ring(bm, (x, y), 0.75 * s, z - 0.3 * s, 16), ring(bm, (x, y), 0.8 * s, z + 0.1 * s, 16)],
                                        cap_top=False))
        for k in range(7):
            a = k * math.tau / 7 + 0.3
            ln = (0.9 + 0.35 * (k % 2)) * s
            P.add(BLUE if k % 2 else ICE, lambda a=a, ln=ln: _fin(bm, (x + math.cos(a) * 0.72 * s, y + math.sin(a) * 0.72 * s, z),
                                                                  (0.0, 0.0, ln), 0.17 * s))
            P.add(CLEAR, lambda a=a: blob(bm, (x + math.cos(a) * 0.8 * s, y + math.sin(a) * 0.8 * s, z - 0.1 * s), 0.09 * s, subdiv=1))


def _fin(bm, base, vec, r, n=8):
    """A smooth tapered spike or fin from `base` along `vec`: eight-sided, rounded at its
    root, drawn to a point."""
    import mathutils

    b = mathutils.Vector(base)
    v = mathutils.Vector(vec)
    L = v.length
    path = [b - v.normalized() * r * 0.4, b, b + v * 0.35, b + v * 0.7, b + v]
    radii = [r * 0.6, r, r * 0.8, r * 0.45, 0.01]
    tube(bm, [tuple(p) for p in path], radii, n=n)


def arch(P, bm, shape, w, h, y=0.0, mat="frost_stone", key=ICE, dz=0.0):
    """An opening's frame of cut blocks, `w` wide and `h` to the top of its curve: round,
    pointed, keyhole or crooked."""
    lean = 0.12 if shape == "crooked" else 0.0
    if shape == "pointed":
        r = w / 2
        z0 = h - r * 1.3
        for sx in (-1, 1):
            P.add(mat, lambda sx=sx: cuboid(bm, (sx * r, y, z0 / 2 + dz), (0.9, 1.0, z0 + 0.2)))
            P.add(mat, lambda sx=sx: cuboid(bm, (sx * r * 0.5, y, z0 + r * 0.62 + dz), (0.9, 1.0, r * 1.5), tilt=(0.0, -sx * 0.62)))
        P.add(key, lambda: cuboid(bm, (0, y + 0.05, h - 0.2 + dz), (0.8, 1.1, 0.8), rot=0.0, tilt=(0.0, math.pi / 4)))
        return
    if shape == "keyhole":
        r = w * 0.32
        z0 = h - r
        for sx in (-1, 1):
            P.add(mat, lambda sx=sx: cuboid(bm, (sx * w * 0.22, y, (z0 - r) / 2 + dz), (0.9, 1.0, z0 - r + 0.3)))
    else:
        r = w / 2
        z0 = h - r
        for sx in (-1, 1):
            P.add(mat, lambda sx=sx: cuboid(bm, (sx * r + lean * z0 / 2, y, z0 / 2 + dz), (0.9, 1.0, z0 + 0.2), tilt=(0.0, lean)))
    for k in range(7):
        t = math.pi * k / 6
        m = key if k == 3 else mat
        P.add(m, lambda t=t: cuboid(bm, (math.cos(t) * r + lean * z0, y, z0 + math.sin(t) * r + dz), (0.85, 1.0, 0.75),
                                    tilt=(0.0, -(t - math.pi / 2) + lean)))


def door(P, bm, w, h, col, y=-0.1, x=0.0, open_=0.0, side=1, dz=0.0):
    """A planked door (Blake, review-snow_region 3: "it doesnt even look like a door"):
    upright boards, two battens and a Z brace on its face, iron strap hinges, a ring
    handle. Closed (open_ 0) it stands centred on x facing +Y; open, it swings out on the
    hinge at its `side` edge by open_ radians."""
    # (Along the leaf from its hinge edge: d; out of its face: n.)
    hx = x + side * w / 2
    d = (-side * math.cos(open_), math.sin(open_))
    n = (-d[1] * side, d[0] * side) if False else (-d[1], d[0])
    if side < 0:
        n = (d[1], -d[0])
    rot = math.atan2(d[1], d[0])

    def at(u, off=0.0):
        return (hx + d[0] * u + n[0] * off, y + d[1] * u + n[1] * off)

    nb = max(3, int(round(w / 0.3)))
    bw = w / nb
    for k in range(nb):
        px, py = at((k + 0.5) * bw)
        P.add(col, lambda px=px, py=py, k=k: cuboid(bm, (px, py, dz + h / 2 - 0.02 * (k % 2)), (bw - 0.04, 0.1, h - 0.04 * (k % 2)), rot=rot))
    for zz in (h * 0.22, h * 0.78):
        px, py = at(w / 2, 0.08)
        P.add(col, lambda px=px, py=py, zz=zz: cuboid(bm, (px, py, dz + zz), (w - 0.12, 0.07, 0.2), rot=rot))
    a0, a1 = at(0.18, 0.08), at(w - 0.18, 0.08)
    P.add(col, lambda: _beam(bm, (a1[0], a1[1], dz + h * 0.26), (a0[0], a0[1], dz + h * 0.74), 0.16, 0.06))
    for zz in (h * 0.22, h * 0.78):  # (strap hinges, from the hinge edge)
        px, py = at(w * 0.28, 0.13)
        P.add(IRON, lambda px=px, py=py, zz=zz: cuboid(bm, (px, py, dz + zz), (w * 0.56, 0.03, 0.09), rot=rot))
        px, py = at(0.04, 0.12)
        P.add(IRON, lambda px=px, py=py, zz=zz: cuboid(bm, (px, py, dz + zz), (0.12, 0.08, 0.16), rot=rot))
    px, py = at(w - 0.32, 0.12)
    P.add(IRON, lambda: cuboid(bm, (px, py, dz + h * 0.5), (0.1, 0.06, 0.1), rot=rot))
    for a in (0.0, math.pi / 4):  # (the ring)
        px, py = at(w - 0.32, 0.15)
        P.add(IRON, lambda px=px, py=py, a=a: cuboid(bm, (px, py, dz + h * 0.5 - 0.17), (0.2, 0.025, 0.2), rot=rot, tilt=(0.0, a)))


def door_in_arch(P, bm, shape, dw, dh, col, frame, y0, rng, dz=0.0):
    """An arched doorway: the arch of cut stone, a planked door up to where its curve
    springs, a warm fanlight in the curve over it."""
    key = ICE if dw >= 2.4 and shape != "crooked" else frame
    arch(P, bm, shape, dw, dh, y=y0, mat=frame, key=key, dz=dz)
    if shape == "keyhole":
        spring = dh - dw * 0.64
        inner = dw * 0.44 - 0.45
    elif shape == "pointed":
        spring = dh - dw * 0.65
        inner = dw - 0.9
    else:
        spring = dh - dw / 2
        inner = dw - 0.9
    door(P, bm, inner, spring, col, y=y0 - 0.15, dz=dz)
    P.add(GLASS, lambda: cuboid(bm, (0, y0 - 0.3, dz + spring + (dh - spring) * 0.4), (inner, 0.05, (dh - spring) * 0.8)))
    P.add(TIMBER, lambda: cuboid(bm, (0, y0 - 0.2, dz + spring + 0.05), (inner + 0.1, 0.16, 0.16)))
    return spring, inner


def window(P, bm, x, z, shape, frame=TIMBER, s=1.0, y=-0.05):
    """A warm window in a frame: square, round, tall or a pair."""
    if shape == "round":
        # (An octagon: a square and a diamond.)
        for a in (0.0, math.pi / 4):
            P.add(frame, lambda a=a: cuboid(bm, (x, y, z), (1.45 * s, 0.3, 1.45 * s), tilt=(0.0, a)))
            P.add(GLASS, lambda a=a: cuboid(bm, (x, y + 0.17, z), (1.0 * s, 0.05, 1.0 * s), tilt=(0.0, a)))
        P.add(frame, lambda: cuboid(bm, (x, y + 0.2, z), (0.08, 0.06, 1.0 * s)))
        return 0.75 * s
    w, h = {"square": (1.1, 1.1), "tall": (0.8, 1.7), "pair": (0.7, 1.2)}.get(shape, (1.1, 1.1))
    xs = (x - 0.5 * s, x + 0.5 * s) if shape == "pair" else (x,)
    for xx in xs:
        P.add(frame, lambda xx=xx: cuboid(bm, (xx, y, z), ((w + 0.4) * s, 0.3, (h + 0.4) * s)))
        P.add(GLASS, lambda xx=xx: cuboid(bm, (xx, y + 0.17, z), (w * s, 0.05, h * s)))
        P.add(frame, lambda xx=xx: cuboid(bm, (xx, y + 0.2, z), (0.08, 0.06, h * s)))
        P.add(frame, lambda xx=xx: cuboid(bm, (xx, y + 0.15, z - (h + 0.4) * s / 2), ((w + 0.6) * s, 0.45, 0.14)))
    return (abs(xs[-1] - x) + (w + 0.4) * s / 2)


def _icicle(bm, x, y, z, ln, r):
    """One icicle hanging from (x, y, z): six-sided, thick at the root, tapering in three
    steps to its point."""
    rings = [ring(bm, (x, y), r, z, 6, phase=0.3), ring(bm, (x, y), r * 0.62, z - ln * 0.35, 6, phase=0.3),
             ring(bm, (x, y), r * 0.3, z - ln * 0.72, 6, phase=0.3)]
    loft(bm, rings, cap_top=False, cap_bottom=False)
    tip = bm.verts.new((x, y, z - ln))
    lo = rings[-1]
    for k in range(6):
        bm.faces.new((lo[(k + 1) % 6], lo[k], tip))
    bm.faces.new(rings[0])


def cornice(P, bm, w, h, rng, y=0.2):
    """The eave along the top (Blake, review-snow_region 3: the icicles "look weird ... make
    them come from the wood"): a timber eave board, a ridge of ice along its underside and
    the icicles hanging from that, long and short in clusters with gaps between; snow
    heaped unevenly on top."""
    n = max(2, int(w / 2.2))
    for k in range(n):
        x = -w / 2 + (k + 0.5) * w / n + rng.uniform(-0.3, 0.3)
        P.add(SNOW, lambda x=x, r=rng.uniform(0.9, 1.4), sz=rng.uniform(0.45, 0.8): blob(bm, (x, y - 0.2, h + 0.25), r, sx=1.3, sy=1.0, sz=sz, subdiv=2))
    P.add(TIMBER, lambda: cuboid(bm, (0, y + 0.25, h - 0.05), (w + 0.4, 0.22, 0.4)))
    P.add(ICE, lambda: cuboid(bm, (0, y + 0.25, h - 0.3), (w + 0.2, 0.2, 0.12)))
    x = -w / 2 + 0.25
    while x < w / 2 - 0.2:
        if rng.random() < 0.18:  # (a gap)
            x += rng.uniform(0.5, 1.0)
            continue
        ln = rng.choice((0.25, 0.35, 0.5, 0.7, 0.9, 1.2, 1.6))
        P.add(BLUE, lambda x=x, ln=ln: _icicle(bm, x, y + 0.25, h - 0.3, ln, 0.07 + 0.035 * ln))
        x += rng.uniform(0.22, 0.45)


def awning(P, bm, x, z, w, mat, y=0.0):
    """A boarded awning over a window, falling forward, on two posts that carry its front
    edge (Blake, review-snow_region 3: "these poles need to be touching the roof")."""
    t = 0.32
    P.add(mat, lambda: cuboid(bm, (x, y + 1.0, z), (w, 2.0, 0.12), tilt=(t, 0.0)))
    front = z - math.sin(t) * 0.95 - 0.06
    for sx in (-1, 1):
        P.add(TIMBER, lambda sx=sx: cuboid(bm, (x + sx * (w / 2 - 0.15), y + 1.85, front / 2), (0.16, 0.16, front)))
    P.add(TIMBER, lambda: cuboid(bm, (x, y + 1.85, front - 0.06), (w, 0.16, 0.14)))


def shutters(P, bm, x, z, col, y=0.0, half=0.75):
    """Two shutters hung on the window frame's sides, swung open (Blake, review-snow_region
    3: "floating ... they need to be connected"): boards, a batten, iron hinges at the
    frame."""
    a = 0.45
    sw = 0.6
    for sx in (-1, 1):
        hx, hy = x + sx * half, y + 0.18
        cx, cy = hx + sx * math.cos(a) * sw / 2, hy + math.sin(a) * sw / 2
        rot = sx * a
        P.add(col, lambda cx=cx, cy=cy, rot=rot: cuboid(bm, (cx, cy, z), (sw, 0.07, 1.4), rot=rot))
        P.add(col, lambda cx=cx, cy=cy, rot=rot, sx=sx: cuboid(bm, (cx + 0.03 * -sx, cy + 0.05, z), (sw - 0.08, 0.05, 0.14), rot=rot))
        for zz in (z - 0.45, z + 0.45):
            P.add(IRON, lambda hx=hx, hy=hy, zz=zz: cuboid(bm, (hx, hy, zz), (0.1, 0.12, 0.1)))


def wreath(P, bm, x, z, y=0.0):
    for k in range(8):
        a = k * math.tau / 8
        P.add(WREATH, lambda a=a: cuboid(bm, (x + math.cos(a) * 0.45, y + 0.12, z + math.sin(a) * 0.45), (0.3, 0.2, 0.3), tilt=(0.0, a)))
    P.add("wrap_red", lambda: cuboid(bm, (x, y + 0.25, z - 0.5), (0.36, 0.1, 0.24)))


def stovepipe(P, bm, x, y, z, rng):
    """A stovepipe, one continuous iron pipe out of the roof (Blake, review-snow_region 3:
    "it can be bent, but its like 3 pieces"), its collar sealed to the roof, a dog-leg
    bend part way up, a hat on top. `z`: the roof's top under it."""
    h1 = rng.uniform(0.8, 1.2)
    dx, dy = rng.choice((-1, 1)) * rng.uniform(0.35, 0.6), rng.uniform(-0.15, 0.15)
    h2 = rng.uniform(0.9, 1.4)
    pts = [(x, y, z - 0.3), (x, y, z + h1)]
    for k in range(1, 5):  # (the bend, eased)
        t = k / 5.0
        e = t * t * (3 - 2 * t)
        pts.append((x + dx * e, y + dy * e, z + h1 + 0.6 * t))
    pts.append((x + dx, y + dy, z + h1 + 0.6 + h2))
    P.add(IRON, lambda: tube(bm, pts, 0.17, n=8))
    P.add(IRON, lambda: loft(bm, [ring(bm, (x, y), 0.32, z - 0.1, 8), ring(bm, (x, y), 0.24, z + 0.22, 8)], cap_top=True, cap_bottom=True))
    tx, ty, tz = pts[-1]
    P.add(IRON, lambda: loft(bm, [ring(bm, (tx, ty), 0.36, tz + 0.12, 8), ring(bm, (tx, ty), 0.06, tz + 0.42, 8)], cap_top=True, cap_bottom=True))
    for k in range(3):
        a = k * math.tau / 3
        P.add(IRON, lambda a=a: _beam(bm, (tx + math.cos(a) * 0.16, ty + math.sin(a) * 0.16, tz - 0.02),
                                      (tx + math.cos(a) * 0.3, ty + math.sin(a) * 0.3, tz + 0.18), 0.04))
    return tx, ty, tz + 0.3


def _log(P, bm, a, b, r, k):
    """One split log: a bark-sided eight-sided length, its cut ends pale."""
    P.add("giant_bark", lambda: _beam_round(bm, a, b, r, k))
    for p, q in ((a, b), (b, a)):
        P.add(LOGS, lambda p=p, q=q: _cap(bm, p, q, r * 0.92))


def _beam_round(bm, a, b, r, k=0):
    ax = [b[i] - a[i] for i in range(3)]
    tube(bm, [a, b], r, n=8)


def _cap(bm, p, q, r):
    """A log's cut end at p (facing away from q)."""
    import mathutils

    d = mathutils.Vector([p[i] - q[i] for i in range(3)]).normalized()
    side = d.cross(mathutils.Vector((0, 0, 1)))
    if side.length < 1e-3:
        side = mathutils.Vector((1, 0, 0))
    side.normalize()
    up = side.cross(d).normalized()
    c = mathutils.Vector(p) + d * 0.015
    vs = [bm.verts.new(c + (side * math.cos(k * math.tau / 8) + up * math.sin(k * math.tau / 8)) * r) for k in range(8)]
    bm.faces.new(vs)


def woodpile(P, bm, x, y, rot=0.0, n=4):
    """A stack of split logs on two sleepers, sitting on the ground (Blake, review-snow_region
    3: "higher fidelity logs, and they are partially in the ground"), cut ends out,
    snow on the top course."""
    cr, sr = math.cos(rot), math.sin(rot)
    ln = 1.5
    r = 0.17

    def at(u, v, z):
        return (x + u * cr - v * sr, y + u * sr + v * cr, z)

    for v in (-0.5, 0.5):  # (the sleepers, along the stack)
        P.add(TIMBER, lambda v=v: _beam(bm, at(-(n * r), v, 0.08), at(n * r, v, 0.08), 0.16))
    k = 0
    for row in range(n - 1):
        cnt = n - row
        for j in range(cnt):
            u = (j - (cnt - 1) / 2) * 2 * r * 1.02
            z = 0.16 + r + row * r * 1.75
            jit = ((k * 37) % 7 - 3) * 0.03
            P_ = at(u, -ln / 2 + jit, z)
            Q_ = at(u, ln / 2 + jit, z)
            _log(P, bm, P_, Q_, r * (0.92 + 0.08 * ((k * 5) % 3) / 2), k)
            k += 1
    top = 0.16 + r + (n - 2) * r * 1.75 + r
    P.add(SNOW, lambda: blob(bm, at(0, 0, top), 0.55, sx=1.2, sy=1.6, sz=0.28, subdiv=2))


def drying_line(P, bm, x0, x1, y, rng):
    for x in (x0, x1):
        P.add(TIMBER, lambda x=x: cuboid(bm, (x, y, 1.2), (0.14, 0.14, 2.4)))
    P.add(PLANK, lambda: cuboid(bm, ((x0 + x1) / 2, y, 2.25), (abs(x1 - x0), 0.04, 0.04)))
    n = max(2, int(abs(x1 - x0) / 0.7))
    for k in range(n):
        x = x0 + (k + 0.5) * (x1 - x0) / n
        mat = rng.choice(CLOTH)
        if k % 3 == 1:  # (a scarf, long)
            P.add(mat, lambda x=x: cuboid(bm, (x, y, 1.65), (0.28, 0.05, 1.1)))
        else:  # (a mitten)
            P.add(mat, lambda x=x: cuboid(bm, (x, y, 1.95), (0.3, 0.06, 0.45)))
            P.add(mat, lambda x=x: cuboid(bm, (x + 0.16, y, 2.0), (0.1, 0.06, 0.2)))


def leaning_tools(P, bm, x, y, rng):
    """The cutters' tools leant on the house wall (Blake, review-snow_region 3, in place of
    the rack: "lets have this leaning on the building"): a long ice saw, a pike pole, a
    pair of tongs, a shovel; their feet on the ground a pace out, their tops on the wall."""
    tops = y + 0.05
    k = 0
    for kind in rng.sample(("saw", "pike", "tongs", "shovel"), 3):
        x0 = x + (k - 1) * 0.55
        foot = (x0 + rng.uniform(-0.1, 0.1), y + 0.75, 0.0)
        if kind == "saw":
            P.add(IRON, lambda x0=x0: _beam(bm, (x0, y + 0.7, 0.05), (x0 + 0.1, tops + 0.05, 1.75), 0.04, 0.32))
            for j in range(9):
                t = j / 9
                P.add(IRON, lambda x0=x0, t=t: _crystal(bm, (x0 + 0.1 * t, y + 0.7 - 0.6 * t + 0.14, 0.05 + 1.7 * t), (0, 0.7, 0.0), 0.07, 0.03, n=3))
            P.add(TIMBER, lambda x0=x0: _beam(bm, (x0 - 0.3, tops + 0.05, 1.95), (x0 + 0.5, tops + 0.05, 1.95), 0.08))
            P.add(TIMBER, lambda x0=x0: _beam(bm, (x0 + 0.1, tops + 0.05, 1.75), (x0 + 0.1, tops + 0.05, 1.95), 0.07))
        elif kind == "pike":
            P.add(TIMBER, lambda foot=foot: _beam(bm, foot, (foot[0] + 0.15, tops, 3.3), 0.07))
            P.add(IRON, lambda foot=foot: _crystal(bm, (foot[0] + 0.15, tops, 3.3), (0.04, -0.2, 1.0), 0.4, 0.05, n=4))
            P.add(IRON, lambda foot=foot: _beam(bm, (foot[0] + 0.15, tops, 3.2), (foot[0] + 0.15, tops + 0.3, 3.05), 0.04))
        elif kind == "tongs":
            for sx in (-1, 1):
                P.add(IRON, lambda sx=sx, foot=foot: _beam(bm, (foot[0] + sx * 0.18, foot[1], 0.05), (foot[0] - sx * 0.12, tops, 1.4), 0.05))
            P.add(IRON, lambda foot=foot: _beam(bm, (foot[0] - 0.25, tops, 1.45), (foot[0] + 0.25, tops, 1.45), 0.05))
        else:
            P.add(TIMBER, lambda foot=foot: _beam(bm, (foot[0], foot[1] - 0.1, 0.55), (foot[0] + 0.05, tops, 1.9), 0.06))
            P.add(IRON, lambda foot=foot: cuboid(bm, (foot[0], foot[1] - 0.05, 0.3), (0.32, 0.06, 0.5), tilt=(0.45, 0.0)))
        k += 1


def lamp(P, bm, x, z, y=0.0):
    """An iron bracket off the wall, a lamp of amber glass hanging from it."""
    P.add(IRON, lambda: cuboid(bm, (x, y + 0.45, z), (0.08, 0.9, 0.08)))
    P.add(IRON, lambda: cuboid(bm, (x, y + 0.85, z - 0.3), (0.04, 0.04, 0.6)))
    P.add(LAMP, lambda: cuboid(bm, (x, y + 0.85, z - 0.75), (0.36, 0.36, 0.5)))
    P.add(IRON, lambda: cuboid(bm, (x, y + 0.85, z - 0.45), (0.46, 0.46, 0.08)))


# ------------------------------------------------------------------ the kinds


def _clutter(P, bm, rng, w, h, door_col, wins, used):
    """A home's own mix of clutter round its front (`wins`: its windows' x, z)."""
    picks = rng.sample(("awning", "shutters", "lamp", "woodpile", "line", "tools", "lamp2"), rng.randint(3, 4))
    for it in picks:
        if it == "awning" and wins:
            x, z, _ = wins[0]
            awning(P, bm, x, z + 1.2, 2.2, rng.choice(AWNINGS), y=0.1)
        elif it == "shutters" and wins:
            for x, z, hw in wins:
                shutters(P, bm, x, z, rng.choice((door_col, PLANK, TIMBER)), y=used.get("y0", 0.0) - 0.1, half=hw)
        elif it in ("lamp", "lamp2"):
            lamp(P, bm, (-1 if it == "lamp" else 1) * (used["door_w"] / 2 + 0.6), used["door_h"] + 0.4, y=0.0)
        elif it == "woodpile":
            sx = rng.choice((-1, 1))
            woodpile(P, bm, sx * (w / 2 + 1.1), 1.2, rot=math.pi / 2)
        elif it == "line":
            sx = rng.choice((-1, 1))
            drying_line(P, bm, sx * (w / 2 - 0.4), sx * (w / 2 + 2.6), 2.4, rng)
        elif it == "tools":
            leaning_tools(P, bm, rng.choice((-1, 1)) * (w / 2 - 0.9), used.get("y0", 0.0), rng)
    return picks


def cut_home(c, idx, rng, w, h, sign_kind, door_col, arch_shape, porch=False):
    """Cut into the wall: a stone front, its body back in the rock, packed snow on its top;
    the arched doorway, windows, the sign over the door, the eave and its icicles, the
    clutter; `porch`: a boarded porch roof out over the door on two posts (Blake,
    review-snow_region 3: the one set back in its own cut was "sunk into the wall")."""
    stone = rng.choice(STONES)
    info = {"y0": 0.0}

    def build(P, bm):
        P.add(stone, lambda: cuboid(bm, (0, -2.8, h / 2 - 0.8), (w, 4.6, h + 0.6)))
        P.add(SNOW, lambda: cuboid(bm, (0, -2.7, h - 0.3), (w + 0.5, 5.0, 0.6)))
        # A plinth of darker stone along its foot, quoins up its corners.
        P.add("rift_stone", lambda: cuboid(bm, (0, -0.35, 0.15), (w + 0.2, 0.5, 0.7)))
        for sx in (-1, 1):
            for k in range(int(h / 0.9)):
                P.add("rift_stone" if stone != "rift_stone" else "frost_stone",
                      lambda sx=sx, k=k: cuboid(bm, (sx * (w / 2 - 0.3 + 0.08 * (k % 2)), -0.45, 0.7 + k * 0.9), (0.75 + 0.16 * (k % 2), 0.36, 0.82)))
        dw, dh = (2.6, 3.8) if arch_shape != "keyhole" else (2.4, 4.0)
        door_in_arch(P, bm, arch_shape, dw, dh, door_col, rng.choice((stone, "frost_stone")), 0.0, rng)
        info["door_h"] = dh
        info["door_w"] = dw
        wins = []
        for sx in (-1, 1):
            x = sx * (w / 2 - 1.5 - rng.uniform(0.0, 0.3))
            if abs(x) < dw / 2 + 1.2 or rng.random() < 0.2:
                continue
            z = rng.uniform(2.0, 2.6)
            shape = rng.choice(("square", "tall", "square"))
            hw = window(P, bm, x, z, shape, frame=rng.choice((TIMBER, TIMBER, stone)), y=-0.1)
            wins.append((x, z, hw))
        if h >= 6.5:
            x = rng.uniform(-w / 5, w / 5)
            window(P, bm, x, h - 1.6, rng.choice(("square", "pair")), frame=TIMBER, s=0.8, y=-0.1)
        sign(P, bm, sign_kind, 0.0, 0.75, dh + 1.4, s=rng.uniform(0.85, 1.05))
        cornice(P, bm, w, h, rng, y=-0.2)
        if porch:
            P.add(PLANK, lambda: cuboid(bm, (0, 1.2, dh + 0.25), (dw + 2.2, 2.6, 0.18), tilt=(0.18, 0.0)))
            front = dh + 0.25 - math.sin(0.18) * 1.25 - 0.1
            for sx in (-1, 1):
                P.add(TIMBER, lambda sx=sx: cuboid(bm, (sx * (dw / 2 + 0.9), 2.3, front / 2), (0.22, 0.22, front)))
                P.add(TIMBER, lambda sx=sx: _beam(bm, (sx * (dw / 2 + 0.9), 2.3, front - 0.7), (sx * (dw / 2 + 0.9), 1.6, front - 0.05), 0.12))
            P.add(TIMBER, lambda: cuboid(bm, (0, 2.3, front - 0.05), (dw + 2.0, 0.2, 0.2)))
            P.add(SNOW, lambda: blob(bm, (0, 1.2, dh + 0.5), 1.6, sx=1.3, sy=0.9, sz=0.18, subdiv=2))
        if rng.random() < 0.65:
            info["chimney"] = stovepipe(P, bm, rng.uniform(-w / 3, w / 3), -2.6, h, rng)
        info["clutter"] = _clutter(P, bm, rng, w, h, door_col, wins, info)
        P.add(SNOW, lambda: cuboid(bm, (0, 1.0, -0.25), (3.0 + rng.uniform(0, 1.0), 1.2, 0.6)))

    name = _p(c, "Ice Home %d" % idx, build)
    info.update(w=w, lantern=(w / 2 + 0.7, 0.9, 3.2))
    return name, info


def stack_home(c, idx, rng, w, sign_kinds, door_cols):
    """Two homes stacked: the lower cut into the wall, the upper set back on a ledge over
    it, a timber balcony along the ledge, and a flight of stone stairs up beside the
    lower home, along the wall's face (Blake, review-snow_region 3: the stairs went "into
    the rock"), a rail on its open side."""
    info = {"y0": 0.0}
    h1, lift = 4.6, 6.0
    rise, tread = 0.4, 0.36
    steps = int(lift / rise)
    x_top = w / 2 + 1.2
    x_foot = x_top + steps * tread

    def build(P, bm):
        stone = rng.choice(STONES)
        upper = "rift_stone" if stone != "rift_stone" else "frost_stone"
        P.add(stone, lambda: cuboid(bm, (0, -3.4, lift / 2 - 0.8), (w, 6.0, lift + 1.4)))
        P.add(upper, lambda: cuboid(bm, (0, -5.2, lift + h1 / 2), (w - 1.0, 4.6, h1)))
        P.add(SNOW, lambda: cuboid(bm, (0, -5.0, lift + h1 + 0.2), (w - 0.4, 5.0, 0.6)))
        P.add("rift_stone", lambda: cuboid(bm, (0, -0.35, 0.15), (w + 0.2, 0.5, 0.7)))
        # The lower home.
        door_in_arch(P, bm, rng.choice(("round", "crooked")), 2.4, 3.4, door_cols[0], stone, 0.0, rng)
        hw = window(P, bm, -w / 2 + 1.4, 2.3, "square", frame=TIMBER, y=-0.1)
        shutters(P, bm, -w / 2 + 1.4, 2.3, door_cols[0], y=-0.1, half=hw)
        sign(P, bm, sign_kinds[0], 0.0, 0.75, 4.7, s=0.8)
        # The ledge, out to the stairs' head, and its balcony rail along the front.
        P.add(DECK, lambda: cuboid(bm, ((x_top - w / 2) / 2, -1.3, lift + 0.1), (w + x_top - w / 2 + 0.4, 2.6, 0.3)))
        for k in range(7):
            x = -w / 2 + 0.2 + k * (w - 0.4) / 6
            P.add(TIMBER, lambda x=x: cuboid(bm, (x, -0.15, lift + 0.75), (0.14, 0.14, 1.1)))
        P.add(TIMBER, lambda: cuboid(bm, (0, -0.15, lift + 1.35), (w, 0.16, 0.16)))
        for k in range(3):  # (the ledge's brackets, under it)
            x = -w / 2 + 0.6 + k * (w - 1.2) / 2
            P.add(TIMBER, lambda x=x: _beam(bm, (x, -0.7, lift - 1.4), (x, -0.1, lift - 0.05), 0.18))
        # The stairs: a flight up along the face, solid stone under each tread.
        for k in range(steps):
            top = rise * (k + 1)
            x = x_foot - (k + 0.5) * tread
            P.add("frost_stone", lambda x=x, top=top: cuboid(bm, (x, -1.05, top / 2 - 0.15), (tread + 0.02, 1.7, top + 0.3)))
            P.add(SNOW, lambda x=x, top=top: cuboid(bm, (x, -1.05, top + 0.03), (tread - 0.04, 1.5, 0.06)))
        P.add("frost_stone", lambda: cuboid(bm, (x_top - 0.3, -1.05, lift / 2 - 0.15), (0.6, 1.7, lift + 0.3)))
        # Its rail on the open side, posts and a sloping handrail.
        for k in range(0, steps + 1, 3):
            x = x_foot - k * tread
            zt = rise * k
            P.add(TIMBER, lambda x=x, zt=zt: cuboid(bm, (x, -0.25, zt + 0.55), (0.12, 0.12, 1.1)))
        P.add(TIMBER, lambda: _beam(bm, (x_foot, -0.25, 1.1), (x_top, -0.25, lift + 1.1), 0.12))
        # The upper home.
        door_in_arch(P, bm, rng.choice(("pointed", "round")), 2.2, 3.4, door_cols[1], "frost_stone", -2.6, rng, dz=lift)
        for sx in (-1, 1):
            window(P, bm, sx * (w / 2 - 1.5), lift + 2.2, "square" if sx > 0 else "tall", frame=TIMBER, y=-2.7)
        sign(P, bm, sign_kinds[1], 0.0, -1.85, lift + 4.0, s=0.75)
        cornice(P, bm, w - 1.0, lift + h1, rng, y=-2.9)
        lamp(P, bm, -1.6, lift + 3.4, y=-2.7)
        info["chimney"] = stovepipe(P, bm, -w / 3, -5.0, lift + h1 + 0.5, rng)
        drying_line(P, bm, -w / 2 - 0.4, -w / 2 - 3.0, 1.0, rng)

    name = _p(c, "Ice Home %d" % idx, build)
    info.update(w=w + 4.0, lantern=(-w / 2 - 0.6, 0.9, 3.0), lantern2=(w / 2 - 0.4, -0.6, lift + 2.6))
    return name, info


def dome_home(c, idx, rng, r, sign_kind, door_col):
    """A freestanding dome of ice blocks, a low tunnel to its door, a round window, a
    stovepipe through its top, the family sign on its crown."""
    info = {}

    def build(P, bm):
        n = 12
        rings = []
        for k in range(7):
            a = k * (math.pi / 2) / 6
            rings.append(ring(bm, (0, -r), r * math.cos(a) + 0.01, r * 0.92 * math.sin(a) - 0.4, n, phase=0.2 * k))
        P.add(SNOW, lambda: loft(bm, rings, cap_top=True))
        for k in range(1, 6):  # (the courses' seams, a ring of blue at each)
            z = r * 0.92 * math.sin(k * (math.pi / 2) / 6) - 0.4
            rr = r * math.cos(k * (math.pi / 2) / 6) + 0.06
            P.add("frost_stone", lambda z=z, rr=rr: loft(bm, [ring(bm, (0, -r), rr, z - 0.06, n), ring(bm, (0, -r), rr, z + 0.06, n)], cap_top=False))
        # The tunnel to the door.
        P.add("frost_stone", lambda: cuboid(bm, (0, 0.6, 1.0), (3.0, 2.6, 2.6)))
        P.add(SNOW, lambda: blob(bm, (0, 0.6, 2.4), 1.7, sx=1.0, sy=1.1, sz=0.45))
        door_in_arch(P, bm, "round", 2.2, 2.6, door_col, "rift_stone", 1.95, rng)
        window(P, bm, r * 0.55, r * 0.45, "square", frame=TIMBER, s=0.8, y=-r + r * 0.78)
        dd = math.hypot(r * 0.3, 0.3) / r
        info["chimney"] = stovepipe(P, bm, -r * 0.3, -r - 0.3, r * 0.92 * math.sqrt(1 - dd * dd) - 0.45, rng)
        sign(P, bm, sign_kind, 0.0, -r, r * 0.92 + 0.6, s=1.0)
        if rng.random() < 0.6:
            woodpile(P, bm, r * 0.9, -r * 0.2)

    name = _p(c, "Ice Home %d" % idx, build)
    info.update(w=2 * r + 2.0, lantern=(1.8, 1.9, 2.2), free=True)
    return name, info


def tower_home(c, idx, rng, sign_kind, door_col):
    """A crooked tower: five storeys of cut stone, each turned and shifted off the one
    below, windows all the way up, a balcony, a steep timber roof, the sign up top."""
    info = {}

    def build(P, bm):
        x, y, z = 0.0, -2.6, 0.0
        rot = 0.0
        s = 4.6
        for k in range(5):
            hh = rng.uniform(2.4, 3.0)
            mat = "frost_stone" if k % 2 == 0 else "rift_stone"
            P.add(mat, lambda x=x, y=y, z=z, s=s, hh=hh, rot=rot: cuboid(bm, (x, y, z + hh / 2), (s, s, hh), rot=rot))
            P.add(TIMBER, lambda x=x, y=y, z=z, s=s, hh=hh, rot=rot: cuboid(bm, (x, y, z + hh), (s + 0.3, s + 0.3, 0.2), rot=rot))
            if k > 0:
                window(P, bm, x + rng.uniform(-0.6, 0.6), z + hh * 0.55, rng.choice(("square", "tall", "round")), frame=TIMBER, s=0.75,
                       y=y + s / 2 - 0.05)
            z += hh
            x += rng.uniform(-0.35, 0.35)
            y += rng.uniform(-0.2, 0.2)
            rot += rng.uniform(-0.18, 0.18)
            s *= 0.9
        # A steep timber roof, boarded, its eaves out over the top storey, snow on it, a
        # finial (Blake, review-snow_region 3: the crystal cap "looks weird").
        P.add(PLANK, lambda x=x, y=y, z=z: loft(bm, [ring(bm, (x, y), s * 0.82, z + 0.05, 4, phase=math.pi / 4 + rot),
                                                     ring(bm, (x, y), 0.05, z + 3.2, 4, phase=math.pi / 4 + rot)], cap_top=True, cap_bottom=True))
        P.add(SNOW, lambda x=x, y=y, z=z: loft(bm, [ring(bm, (x, y), s * 0.7, z + 0.55, 4, phase=math.pi / 4 + rot),
                                                    ring(bm, (x, y), s * 0.2, z + 2.3, 4, phase=math.pi / 4 + rot)], cap_top=True))
        P.add(IRON, lambda x=x, y=y, z=z: _beam(bm, (x, y, z + 3.0), (x, y, z + 4.0), 0.08))
        sign(P, bm, sign_kind, x, y + s / 2 + 0.5, z - 1.4, s=0.85)
        # The door and its arch, the balcony round the second storey.
        door_in_arch(P, bm, rng.choice(("round", "pointed")), 2.4, 3.4, door_col, "rift_stone", -0.2, rng)
        P.add(PLANK, lambda: cuboid(bm, (0, -2.6, 5.4), (6.0, 6.0, 0.25)))
        for k in range(8):
            a = k * math.tau / 8
            P.add(TIMBER, lambda a=a: cuboid(bm, (math.cos(a) * 2.9, -2.6 + math.sin(a) * 2.9, 6.0), (0.14, 0.14, 1.1)))
        lamp(P, bm, 1.6, 5.2, y=-0.3)
        info["chimney"] = stovepipe(P, bm, x - s * 0.25, y - s * 0.25, z + 0.9, rng)

    name = _p(c, "Ice Home %d" % idx, build)
    info.update(w=7.0, lantern=(2.2, 0.6, 3.0), free=True)
    return name, info


def workshop(c, idx, rng, sign_kind, door_col):
    """A carvers' workshop: a wide front cut into the wall, great double doors swung open
    on the dark inside where blocks wait, a hoist beam over the door with a block on its
    chain, a bench and a sled outside."""
    w, h = 12.0, 7.5
    info = {}

    def build(P, bm):
        P.add("frost_stone", lambda: cuboid(bm, (-w / 2 + 1.5, -3.0, h / 2 - 0.8), (3.0, 5.6, h + 0.6)))
        P.add("frost_stone", lambda: cuboid(bm, (w / 2 - 1.5, -3.0, h / 2 - 0.8), (3.0, 5.6, h + 0.6)))
        P.add("frost_stone", lambda: cuboid(bm, (0, -3.0, h - 1.2), (w - 6.0, 5.6, 2.4)))
        P.add(SNOW, lambda: cuboid(bm, (0, -2.9, h + 0.1), (w + 0.5, 6.0, 0.6)))
        P.add("cave_rock", lambda: cuboid(bm, (0, -3.0, 2.4), (w - 6.0, 4.6, 5.0)))  # (the dark inside)
        for k, (x, z) in enumerate(((-1.4, 0.6), (0.6, 0.6), (-0.4, 1.8), (1.8, 0.6))):
            P.add(ICE, lambda x=x, z=z, k=k: cuboid(bm, (x, -1.6 - 0.3 * k, z), (1.2, 1.2, 1.2), rot=0.2 * k))
        # The great doors, each hung on its side of the opening and swung out (Blake,
        # review-snow_region 3: "redo these doors. this one is in the window").
        for sx in (-1, 1):
            door(P, bm, (w - 6.0) / 2, 5.0, door_col, y=-0.35, x=sx * (w - 6.0) / 4, open_=1.9, side=sx)
            for zz in (1.0, 4.0):
                P.add(IRON, lambda sx=sx, zz=zz: cuboid(bm, (sx * (w - 6.0) / 2, -0.35, zz), (0.2, 0.2, 0.3)))
        P.add(TIMBER, lambda: cuboid(bm, (0, -0.35, 5.15), (w - 5.6, 0.4, 0.3)))
        P.add(TIMBER, lambda: cuboid(bm, (0, 1.0, h - 0.2), (w + 0.6, 2.4, 0.5)))
        P.add(TIMBER, lambda: cuboid(bm, (1.5, 2.6, h + 0.4), (0.4, 3.4, 0.4)))
        P.add(IRON, lambda: cuboid(bm, (1.5, 4.0, h - 1.6), (0.08, 0.08, 3.6)))
        P.add(ICE, lambda: cuboid(bm, (1.5, 4.0, h - 3.9), (1.4, 1.4, 1.2), rot=0.3))
        sign(P, bm, sign_kind, -w / 2 + 1.5, 0.6, h + 1.0, s=1.3)
        lamp(P, bm, w / 2 - 1.5, 4.6, y=0.0)
        cornice(P, bm, w, h, rng, y=0.0)
        leaning_tools(P, bm, w / 2 - 1.5, 0.0, rng)
        info["chimney"] = stovepipe(P, bm, w / 3, -2.5, h + 0.4, rng)

    name = _p(c, "Ice Home %d" % idx, build)
    info.update(w=w + 2.0, lantern=(-w / 2 + 1.5, 0.9, 4.2))
    return name, info


def tiny_hut(c, idx, rng, sign_kind, door_col):
    """A tiny hut: a block of snow under a lopsided boarded roof, a door you'd duck through,
    one window, a sled leant by it."""
    info = {}

    def build(P, bm):
        P.add(SNOW, lambda: cuboid(bm, (0, -1.6, 1.4), (3.6, 3.2, 3.0)))
        P.add(PLANK, lambda: cuboid(bm, (0.15, -1.6, 3.15), (4.2, 3.8, 0.3), tilt=(0.06, 0.1)))
        P.add(SNOW, lambda: blob(bm, (0.2, -1.6, 3.4), 2.0, sx=1.05, sy=0.95, sz=0.3))
        # A low door in a timber frame (no ice in it: Blake, review-snow_region 3).
        door(P, bm, 1.1, 1.9, door_col, y=0.02, x=-0.5)
        for sx in (-1, 1):
            P.add(TIMBER, lambda sx=sx: cuboid(bm, (-0.5 + sx * 0.68, 0.05, 1.0), (0.24, 0.22, 2.1)))
        P.add(TIMBER, lambda: cuboid(bm, (-0.5, 0.05, 2.1), (1.7, 0.24, 0.26), tilt=(0.0, 0.06)))
        window(P, bm, 1.0, 1.8, "round", frame=TIMBER, s=0.6, y=0.0)
        sign(P, bm, sign_kind, 0.4, 0.4, 4.4, s=0.7)
        P.add(TIMBER, lambda: cuboid(bm, (2.1, -0.4, 1.0), (0.1, 1.4, 2.2), tilt=(0.0, -0.25)))
        P.add(TIMBER, lambda: cuboid(bm, (2.25, -0.4, 1.0), (0.1, 0.2, 2.2), tilt=(0.0, -0.25)))
        info["chimney"] = stovepipe(P, bm, -1.0, -2.2, 3.3, rng)

    name = _p(c, "Ice Home %d" % idx, build)
    info.update(w=5.5, lantern=(-1.6, 0.6, 2.4), free=True)
    return name, info


def block_home(c, idx, rng, sign_kind, door_col):
    """A home cut into one giant block of clear ice, leaning a little where it settled: a
    deep doorway, windows cut in it, snow on its top, icicles down its edges."""
    s = 8.0
    info = {}

    def build(P, bm):
        P.add(ICE, lambda: cuboid(bm, (0, -s / 2, s / 2 - 0.4), (s, s, s), tilt=(0.05, 0.04)))
        # The doorway: a stone arch set into the ice, a planked door (Blake,
        # review-snow_region 3: "it doesnt even look like a door").
        door_in_arch(P, bm, "round", 2.8, 4.0, door_col, "frost_stone", 0.2, rng)
        for x, z in ((-2.6, 4.6), (2.4, 2.6), (1.6, 5.9)):
            window(P, bm, x, z, rng.choice(("square", "round", "tall")), frame=TIMBER, s=0.8, y=0.05)
        P.add(SNOW, lambda: blob(bm, (0.3, -s / 2, s - 0.1), s * 0.55, sx=1.0, sy=1.0, sz=0.25))
        cornice(P, bm, s, s - 0.6, rng, y=0.15)
        sign(P, bm, sign_kind, -1.8, 0.7, s + 0.6, s=1.15)
        info["clutter"] = _clutter(P, bm, rng, s, s - 0.6, door_col, [(2.4, 2.6, 0.75)], {"door_h": 4.0, "door_w": 2.8, "y0": 0.1})

    name = _p(c, "Ice Home %d" % idx, build)
    info.update(w=s + 2.0, lantern=(s / 2 + 0.6, 0.8, 3.2))
    return name, info


# ------------------------------------------------------------------ the layout

# (Round the hollow from its mouth's east side, by the back, to its west: the ellipse's
# angle, how far in from the wall the front stands (m), the kind, a turn off true. "free"
# kinds stand out on the floor.)
# (The walls' foot is 2 m soft on the land's 2.5 m grid: the fronts stand 2 m out, their
# bodies back in the rock.)
SLOTS = [
    (-0.50, 2.0, "workshop", 0.06),
    (-0.08, 2.0, "cut", -0.08),
    (0.30, 7.5, "dome", 0.0),
    (0.62, 2.0, "stack", 0.05),
    (1.06, 2.0, "cut_deep", -0.04),
    (1.34, 5.8, "tower", 0.2),
    (1.60, 2.0, "block", -0.06),
    (1.90, 2.0, "cut", 0.08),
    (2.15, 4.5, "hut", 0.5),
    (2.42, 2.0, "stack", -0.05),
    (2.84, 2.0, "cut", 0.04),
    (3.12, 5.8, "tower", -0.25),
    (3.42, 2.0, "cut_deep", 0.07),
]


def _make(c, k, kind, rng):
    sk = SIGNS[(k * 5 + 2) % len(SIGNS)]
    col = DOORS[(k * 4 + 1) % len(DOORS)]
    if kind == "workshop":
        return workshop(c, k, rng, sk, col)
    if kind == "stack":
        return stack_home(c, k, rng, rng.uniform(7.0, 8.5), (sk, SIGNS[(k * 5 + 5) % 6]), (col, DOORS[(k * 4 + 3) % len(DOORS)]))
    if kind == "dome":
        return dome_home(c, k, rng, rng.uniform(3.4, 4.2), sk, col)
    if kind == "tower":
        return tower_home(c, k, rng, sk, col)
    if kind == "hut":
        return tiny_hut(c, k, rng, sk, col)
    if kind == "block":
        return block_home(c, k, rng, sk, col)
    w = rng.choice((6.0, 7.0, 8.0, 9.5))
    h = rng.uniform(5.5, 7.8)
    return cut_home(c, k, rng, w, h, sk, col, rng.choice(("round", "pointed", "keyhole", "crooked")),
                    porch=kind == "cut_deep")


def place_homes(c, ground, taken):
    """The homes, slot by slot (SLOTS), each kept off the lane; their lanterns and chimney
    smoke. Returns how many stand."""
    hx, hy, rx, ry = SL.HOLLOW
    done = 0
    for k, (t, inset, kind, turn) in enumerate(SLOTS):
        rng = random.Random(1000 + 37 * k)
        name, info = _make(c, k, kind, rng)
        wx, wy = hx + rx * math.cos(t), hy + ry * math.sin(t)
        nx, ny = hx - wx, hy - wy
        nl = math.hypot(nx, ny)
        nx, ny = nx / nl, ny / nl
        x, y = wx + nx * inset, wy + ny * inset
        if not paint.road_clear(c, x + nx * 1.5, y + ny * 1.5, 1.0) or not taken.clear(x, y, info["w"] / 2 - 1.0):
            print("  (home %d, %s: no room)" % (k, kind))
            continue
        rot = math.atan2(ny, nx) - math.pi / 2 + turn
        z = ground(x + nx * 1.5, y + ny * 1.5)
        if info.get("free"):
            z = min(ground(x + dx, y + dy) for dx in (-2.0, 0.0, 2.0) for dy in (-2.0, 0.0, 2.0))
        c.place(name, x, y, z - 0.25, rot=rot, coll="Village")
        taken.add(x, y, info["w"] / 2 + 0.3)
        cr, sr = math.cos(rot), math.sin(rot)

        def world(lx, ly, lz):
            return c.game(x + lx * cr - ly * sr, y + lx * sr + ly * cr, z + lz)

        for key in ("lantern", "lantern2"):
            if key in info:
                g = world(*info[key])
                c.entity("lantern", x=g[0], y=g[1], z=g[2])
        if "chimney" in info:
            g = world(*info["chimney"])
            c.entity("chimney", x=g[0], y=g[1], z=g[2] + 0.4)
        done += 1
    return done
