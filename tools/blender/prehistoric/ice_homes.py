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
from props import blob, cuboid, loft, ring

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
DOORS = ("siding_red", "siding_green", "awning_teal", "wrap_blue", "siding_ochre", "party_pink")
CLOTH = ("party_red", "party_teal", "party_yellow", "party_blue", "party_pink", "party_white")
AWNINGS = ("awning_red", "awning_green", "awning_teal", "awning_rose", "candy_stripe")
SIGNS = ("fish", "owl", "bear", "star", "snowflake", "crown")


# ------------------------------------------------------------------ details


def sign(P, bm, kind, x, y, z, s=1.0):
    """A family's sign, carved in ice: what it carves (centred at x, y, z; facing +Y)."""
    if kind == "fish":
        P.add(ICE, lambda: blob(bm, (x, y, z), 0.9 * s, sx=1.5, sy=0.5, sz=0.8))
        for sz in (-1, 1):
            P.add(BLUE, lambda sz=sz: _crystal(bm, (x - 1.0 * s, y, z), (-1.0, 0, 0.7 * sz), 1.2 * s, 0.25 * s, n=4))
        P.add(BLUE, lambda: _crystal(bm, (x, y, z + 0.4 * s), (-0.3, 0, 1.0), 0.7 * s, 0.2 * s, n=4))
        P.add(BLUE, lambda: cuboid(bm, (x + 0.8 * s, y + 0.42 * s, z + 0.15 * s), (0.18 * s, 0.06, 0.18 * s)))
    elif kind == "owl":
        P.add(ICE, lambda: blob(bm, (x, y, z - 0.3 * s), 0.8 * s, sx=0.9, sy=0.7, sz=1.0))
        P.add(ICE, lambda: blob(bm, (x, y, z + 0.75 * s), 0.6 * s, sx=1.0, sy=0.8, sz=0.8))
        for sx in (-1, 1):
            P.add(BLUE, lambda sx=sx: cuboid(bm, (x + sx * 0.25 * s, y + 0.45 * s, z + 0.8 * s), (0.22 * s, 0.06, 0.22 * s)))
            P.add(ICE, lambda sx=sx: _crystal(bm, (x + sx * 0.35 * s, y, z + 1.1 * s), (sx * 0.35, 0, 1.0), 0.5 * s, 0.14 * s, n=4))
    elif kind == "bear":
        P.add(ICE, lambda: blob(bm, (x, y, z), 0.85 * s, sx=1.0, sy=0.8, sz=0.9))
        P.add(CLEAR, lambda: blob(bm, (x, y + 0.6 * s, z - 0.25 * s), 0.38 * s, sx=1.0, sy=0.9, sz=0.7))
        P.add(BLUE, lambda: cuboid(bm, (x, y + 0.95 * s, z - 0.15 * s), (0.2 * s, 0.08, 0.14 * s)))
        for sx in (-1, 1):
            P.add(ICE, lambda sx=sx: blob(bm, (x + sx * 0.62 * s, y, z + 0.68 * s), 0.3 * s))
            P.add(BLUE, lambda sx=sx: cuboid(bm, (x + sx * 0.3 * s, y + 0.62 * s, z + 0.25 * s), (0.14 * s, 0.06, 0.14 * s)))
    elif kind == "star":
        P.add(ICE, lambda: blob(bm, (x, y, z), 0.42 * s, sy=0.6))
        for k in range(5):
            a = math.pi / 2 + k * math.tau / 5
            P.add(BLUE, lambda a=a: _crystal(bm, (x, y, z), (math.cos(a), 0.0, math.sin(a)), 1.25 * s, 0.26 * s, n=4))
    elif kind == "snowflake":
        for k in range(6):
            a = k * math.tau / 6
            ca, sa = math.cos(a), math.sin(a)
            P.add(ICE, lambda ca=ca, sa=sa, a=a: cuboid(bm, (x + ca * 0.65 * s, y, z + sa * 0.65 * s), (1.3 * s, 0.14, 0.16 * s), tilt=(0.0, -a)))
            for sd in (-1, 1):
                b = a + sd * 0.8
                P.add(BLUE, lambda ca=ca, sa=sa, b=b: cuboid(bm, (x + ca * 0.95 * s + math.cos(b) * 0.2 * s, y, z + sa * 0.95 * s + math.sin(b) * 0.2 * s),
                                                             (0.42 * s, 0.12, 0.12 * s), tilt=(0.0, -b)))
    else:  # the crown
        P.add("gold_trim", lambda: loft(bm, [ring(bm, (x, y), 0.75 * s, z - 0.3 * s, 8), ring(bm, (x, y), 0.8 * s, z + 0.1 * s, 8)],
                                        cap_top=False))
        for k in range(5):
            a = k * math.tau / 5 + 0.3
            P.add(BLUE if k % 2 else ICE, lambda a=a, k=k: _crystal(bm, (x + math.cos(a) * 0.7 * s, y + math.sin(a) * 0.7 * s, z),
                                                                    (0, 0, 1), (0.9 + 0.3 * (k % 2)) * s, 0.2 * s, n=4))


def arch(P, bm, shape, w, h, y=0.0, mat=ICE, key=BLUE):
    """An opening's frame of cut blocks, `w` wide and `h` to the top of its curve: round,
    pointed, keyhole or crooked."""
    lean = 0.12 if shape == "crooked" else 0.0
    if shape == "pointed":
        r = w / 2
        z0 = h - r * 1.3
        for sx in (-1, 1):
            P.add(mat, lambda sx=sx: cuboid(bm, (sx * r, y, z0 / 2), (0.9, 1.0, z0 + 0.2)))
            P.add(mat, lambda sx=sx: cuboid(bm, (sx * r * 0.5, y, z0 + r * 0.62), (0.9, 1.0, r * 1.5), tilt=(0.0, -sx * 0.62)))
        P.add(key, lambda: cuboid(bm, (0, y + 0.05, h - 0.2), (0.8, 1.1, 0.8), rot=0.0, tilt=(0.0, math.pi / 4)))
        return
    if shape == "keyhole":
        r = w * 0.32
        z0 = h - r
        for sx in (-1, 1):
            P.add(mat, lambda sx=sx: cuboid(bm, (sx * w * 0.22, y, (z0 - r) / 2), (0.9, 1.0, z0 - r + 0.3)))
    else:
        r = w / 2
        z0 = h - r
        for sx in (-1, 1):
            P.add(mat, lambda sx=sx: cuboid(bm, (sx * r + lean * z0 / 2, y, z0 / 2), (0.9, 1.0, z0 + 0.2), tilt=(0.0, lean)))
    for k in range(7):
        t = math.pi * k / 6
        m = key if k == 3 else mat
        P.add(m, lambda t=t: cuboid(bm, (math.cos(t) * r + lean * z0, y, z0 + math.sin(t) * r), (0.85, 1.0, 0.75),
                                    tilt=(0.0, -(t - math.pi / 2) + lean)))


def door(P, bm, w, h, col, y=-0.1):
    P.add(col, lambda: cuboid(bm, (0, y, h / 2), (w, 0.12, h)))
    P.add(IRON, lambda: cuboid(bm, (w * 0.3, y + 0.1, h * 0.48), (0.12, 0.1, 0.12)))


def window(P, bm, x, z, shape, frame=BLUE, s=1.0, y=-0.05):
    """A warm window in a frame: square, round, tall or a pair."""
    if shape == "round":
        # (An octagon: a square and a diamond.)
        for a in (0.0, math.pi / 4):
            P.add(frame, lambda a=a: cuboid(bm, (x, y, z), (1.45 * s, 0.3, 1.45 * s), tilt=(0.0, a)))
            P.add(GLASS, lambda a=a: cuboid(bm, (x, y + 0.17, z), (1.0 * s, 0.05, 1.0 * s), tilt=(0.0, a)))
        P.add(frame, lambda: cuboid(bm, (x, y + 0.2, z), (0.08, 0.06, 1.0 * s)))
        return
    w, h = {"square": (1.1, 1.1), "tall": (0.8, 1.7), "pair": (0.7, 1.2)}.get(shape, (1.1, 1.1))
    xs = (x - 0.5 * s, x + 0.5 * s) if shape == "pair" else (x,)
    for xx in xs:
        P.add(frame, lambda xx=xx: cuboid(bm, (xx, y, z), ((w + 0.4) * s, 0.3, (h + 0.4) * s)))
        P.add(GLASS, lambda xx=xx: cuboid(bm, (xx, y + 0.17, z), (w * s, 0.05, h * s)))
        P.add(frame, lambda xx=xx: cuboid(bm, (xx, y + 0.2, z), (0.08, 0.06, h * s)))


def cornice(P, bm, w, h, rng, y=0.2):
    """Snow heaped unevenly along the top, icicles of every length under it."""
    n = max(2, int(w / 2.2))
    for k in range(n):
        x = -w / 2 + (k + 0.5) * w / n + rng.uniform(-0.3, 0.3)
        P.add(SNOW, lambda x=x, r=rng.uniform(0.9, 1.4), sz=rng.uniform(0.45, 0.8): blob(bm, (x, y, h + 0.2), r, sx=1.3, sy=1.0, sz=sz))
    for k in range(int(w / 0.8)):
        x = -w / 2 + 0.4 + k * 0.8 + rng.uniform(-0.15, 0.15)
        ln = rng.choice((0.3, 0.5, 0.7, 1.0, 1.4, 1.8))
        P.add(BLUE, lambda x=x, ln=ln: _crystal(bm, (x, y + 0.7, h - 0.1), (0, 0, -1), ln, 0.12 + 0.03 * ln, n=4))


def awning(P, bm, x, z, w, mat, y=0.0):
    P.add(mat, lambda: cuboid(bm, (x, y + 1.0, z), (w, 2.0, 0.12), tilt=(0.32, 0.0)))
    for sx in (-1, 1):
        P.add(TIMBER, lambda sx=sx: cuboid(bm, (x + sx * (w / 2 - 0.15), y + 1.9, z / 2 - 0.3), (0.16, 0.16, z - 0.6)))


def shutters(P, bm, x, z, col, y=0.0):
    for sx in (-1, 1):
        P.add(col, lambda sx=sx: cuboid(bm, (x + sx * 1.05, y + 0.35, z), (0.55, 0.08, 1.4), rot=sx * 0.5))


def wreath(P, bm, x, z, y=0.0):
    for k in range(8):
        a = k * math.tau / 8
        P.add(WREATH, lambda a=a: cuboid(bm, (x + math.cos(a) * 0.45, y + 0.12, z + math.sin(a) * 0.45), (0.3, 0.2, 0.3), tilt=(0.0, a)))
    P.add("wrap_red", lambda: cuboid(bm, (x, y + 0.25, z - 0.5), (0.36, 0.1, 0.24)))


def stovepipe(P, bm, x, y, z, rng):
    """A crooked iron stovepipe, three lengths off true, a cap."""
    px, py = x, y
    for k in range(3):
        ln = rng.uniform(0.9, 1.5)
        dx, dy = rng.uniform(-0.25, 0.25), rng.uniform(-0.2, 0.2)
        P.add(IRON, lambda px=px, py=py, z=z, ln=ln, dx=dx, dy=dy: cuboid(bm, (px + dx / 2, py + dy / 2, z + ln / 2), (0.32, 0.32, ln),
                                                                          tilt=(dy * 0.6, -dx * 0.6)))
        px, py, z = px + dx, py + dy, z + ln
    P.add(IRON, lambda: cuboid(bm, (px, py, z + 0.1), (0.6, 0.6, 0.12)))
    return px, py, z


def woodpile(P, bm, x, y, rot=0.0):
    for row in range(3):
        for k in range(4 - row):
            P.add(LOGS, lambda row=row, k=k: cuboid(bm, (x + (k - (3 - row) / 2) * 0.42 * math.cos(rot), y + (k - (3 - row) / 2) * 0.42 * math.sin(rot),
                                                         0.22 + row * 0.38), (0.38, 0.38, 0.38), rot=rot + 0.1 * k))
    P.add(SNOW, lambda: blob(bm, (x, y, 1.3), 0.7, sx=1.3, sy=0.7, sz=0.35))


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


def tool_rack(P, bm, x, y):
    P.add(TIMBER, lambda: cuboid(bm, (x, y, 1.0), (1.6, 0.12, 2.0)))
    for k in range(4):
        P.add(IRON, lambda k=k: cuboid(bm, (x - 0.55 + k * 0.37, y + 0.12, 1.1), (0.06, 0.06, 1.2 + 0.2 * (k % 2))))
        P.add(IRON, lambda k=k: cuboid(bm, (x - 0.55 + k * 0.37, y + 0.12, 1.7 + 0.1 * (k % 2)), (0.18 + 0.1 * (k % 2), 0.06, 0.12)))


def lights(P, bm, w, z, y=0.6):
    P.add(LIGHTS, lambda: cuboid(bm, (0, y, z), (w, 0.1, 0.18)))


# ------------------------------------------------------------------ the kinds


def _clutter(P, bm, rng, w, h, door_col, wins, used):
    """A home's own mix of clutter round its front (`wins`: its windows' x, z)."""
    picks = rng.sample(("awning", "shutters", "wreath", "woodpile", "line", "rack", "lights"), rng.randint(3, 4))
    for it in picks:
        if it == "awning" and wins:
            x, z = wins[0]
            awning(P, bm, x, z + 1.2, 2.2, rng.choice(AWNINGS), y=0.1)
        elif it == "shutters" and wins:
            for x, z in wins:
                shutters(P, bm, x, z, rng.choice((door_col, "siding_green", "siding_red", PLANK)), y=0.0)
        elif it == "wreath":
            wreath(P, bm, 0.0, used["door_h"] * 0.72, y=0.0)
        elif it == "woodpile":
            sx = rng.choice((-1, 1))
            woodpile(P, bm, sx * (w / 2 + 0.6), 1.4, rot=0.0)
        elif it == "line":
            sx = rng.choice((-1, 1))
            drying_line(P, bm, sx * (w / 2 - 0.4), sx * (w / 2 + 2.6), 2.4, rng)
        elif it == "rack":
            tool_rack(P, bm, rng.choice((-1, 1)) * (w / 2 + 0.2), 0.7)
        elif it == "lights":
            lights(P, bm, w * 0.9, h - 0.2)
    return picks


def cut_home(c, idx, rng, w, h, sign_kind, door_col, arch_shape, deep=0.0):
    """Cut into the wall: a front of packed ice, the arch, the door, windows, the sign over
    the door, the snow and icicles along its top, the clutter; the snow behind runs back
    into the wall (`deep`: how far the front sits back in a cut of its own)."""
    info = {}

    def build(P, bm):
        P.add(ROCK, lambda: _wedge(bm, -w / 2 - 1.8, w / 2 + 1.8, -9.0, -0.6 - deep, -1.5, h + 1.6, h + 2.6))
        if deep > 0.5:  # (its own cut: side walls of snow out to the hollow's floor)
            for sx in (-1, 1):
                P.add(ROCK, lambda sx=sx: _wedge(bm, sx * (w / 2 + 0.2) - 0.8, sx * (w / 2 + 0.2) + 0.8, -deep - 0.6, 0.6, -1.0, h * 0.5, h + 1.2))
        P.add(CLEAR, lambda: cuboid(bm, (0, -0.5 - deep, h / 2 - 0.8), (w, 0.6, h + 0.6)))
        dw, dh = (2.6, 3.6) if arch_shape != "keyhole" else (2.2, 4.0)
        y0 = -deep
        arch(P, bm, arch_shape, dw, dh, y=y0, key=rng.choice((BLUE, "gold_trim", CLEAR)))
        P.add(door_col, lambda: cuboid(bm, (0, y0 - 0.1, (dh - 0.6) / 2), (dw - 0.6, 0.12, dh - 0.6)))
        info["door_h"] = dh
        wins = []
        shapes = ("square", "round", "tall", "pair")
        for sx in (-1, 1):
            x = sx * (w / 2 - 1.4 - rng.uniform(0.0, 0.4))
            if abs(x) < dw / 2 + 1.1 or rng.random() < 0.2:
                continue
            z = rng.uniform(2.0, 2.8)
            window(P, bm, x, z, rng.choice(shapes[:1] + shapes[2:]), frame=rng.choice((BLUE, ICE, TIMBER)), y=y0 - 0.1)
            wins.append((x, z))
        if h >= 6.5:
            x = rng.uniform(-w / 4, w / 4)
            window(P, bm, x, h - 1.5, rng.choice(("square", "pair")), frame=BLUE, s=0.8, y=y0 - 0.1)
        sign(P, bm, sign_kind, 0.0, y0 + 0.7, dh + 1.3, s=rng.uniform(0.9, 1.25))
        cornice(P, bm, w, h, rng, y=y0 + 0.2)
        if rng.random() < 0.6:
            info["chimney"] = stovepipe(P, bm, rng.uniform(-w / 3, w / 3), y0 - 2.0, h + 1.0, rng)
        info["clutter"] = _clutter(P, bm, rng, w, h, door_col, wins, info)
        P.add(SNOW, lambda: cuboid(bm, (0, y0 + 1.0, -0.25), (3.0 + rng.uniform(0, 1.0), 1.2, 0.6)))

    name = _p(c, "Ice Home %d" % idx, build)
    info.update(w=w, lantern=(w / 2 + 0.7, 0.9, 3.2))
    return name, info


def stack_home(c, idx, rng, w, sign_kinds, door_cols):
    """Two homes stacked: the lower cut into the wall, the upper set back on a ledge over
    it, snow stairs up the side to its door, a timber balcony along its front."""
    info = {}
    h0, h1, lift = 5.2, 4.6, 6.0

    def build(P, bm):
        P.add(ROCK, lambda: _wedge(bm, -w / 2 - 2.0, w / 2 + 4.0, -11.0, -0.6, -1.5, lift + 0.2, lift + 2.0))
        P.add(ROCK, lambda: _wedge(bm, -w / 2 - 1.5, w / 2 + 1.5, -11.0, -3.6, lift - 0.5, lift + h1 + 1.4, lift + h1 + 2.4))
        # The lower home.
        P.add(CLEAR, lambda: cuboid(bm, (0, -0.5, h0 / 2 - 0.8), (w, 0.6, h0 + 0.6)))
        arch(P, bm, rng.choice(("round", "crooked")), 2.4, 3.4, y=0.0)
        door(P, bm, 1.8, 2.8, door_cols[0])
        window(P, bm, -w / 2 + 1.3, 2.3, "square", frame=BLUE)
        sign(P, bm, sign_kinds[0], 0.0, 0.7, 4.6, s=0.9)
        # The ledge in front of the upper home, its balcony rail, the stairs up.
        P.add(PLANK, lambda: cuboid(bm, (0.6, -1.3, lift + 0.1), (w + 1.6, 2.6, 0.3)))
        for k in range(6):
            P.add(TIMBER, lambda k=k: cuboid(bm, (-w / 2 + 0.2 + k * (w + 1.0) / 5, -0.15, lift + 0.8), (0.14, 0.14, 1.2)))
        P.add(TIMBER, lambda: cuboid(bm, (0.6, -0.15, lift + 1.4), (w + 1.4, 0.14, 0.14)))
        for k in range(8):
            top = 0.75 * (k + 1)
            P.add(SNOW, lambda k=k, top=top: cuboid(bm, (w / 2 + 4.6 - k * 0.55, -0.9, top / 2 - 0.2), (0.6, 1.8, top + 0.4)))
        # The upper home.
        P.add(ICE, lambda: cuboid(bm, (0, -3.1, lift + h1 / 2), (w - 1.0, 0.6, h1)))
        arch(P, bm, rng.choice(("pointed", "keyhole")), 2.2, 3.4, y=-2.7, mat=ICE)
        P.add(door_cols[1], lambda: cuboid(bm, (0, -2.85, lift + 1.35), (1.5, 0.12, 2.6)))
        for sx in (-1, 1):
            window(P, bm, sx * (w / 2 - 1.5), lift + 2.2, "round" if sx > 0 else "tall", frame=BLUE, y=-2.9)
        sign(P, bm, sign_kinds[1], 0.0, -2.1, lift + 4.4, s=0.9)
        cornice(P, bm, w - 0.6, lift + h1, rng, y=-2.9)
        wreath(P, bm, 0.0, lift + 2.3, y=-2.75)
        info["chimney"] = stovepipe(P, bm, -w / 3, -5.0, lift + h1 + 1.2, rng)
        drying_line(P, bm, -w / 2 - 0.4, -w / 2 - 3.0, 1.6, rng)

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
        P.add(ICE, lambda: loft(bm, rings, cap_top=True))
        for k in range(1, 6):  # (the courses' seams, a ring of blue at each)
            z = r * 0.92 * math.sin(k * (math.pi / 2) / 6) - 0.4
            rr = r * math.cos(k * (math.pi / 2) / 6) + 0.06
            P.add(BLUE, lambda z=z, rr=rr: loft(bm, [ring(bm, (0, -r), rr, z - 0.06, n), ring(bm, (0, -r), rr, z + 0.06, n)], cap_top=False))
        # The tunnel to the door.
        P.add(ICE, lambda: cuboid(bm, (0, 0.6, 1.0), (3.0, 2.6, 2.6)))
        P.add(SNOW, lambda: blob(bm, (0, 0.6, 2.4), 1.7, sx=1.0, sy=1.1, sz=0.45))
        P.add(door_col, lambda: cuboid(bm, (0, 1.92, 0.95), (1.5, 0.1, 1.9)))
        arch(P, bm, "round", 2.2, 2.4, y=1.85, mat=CLEAR)
        window(P, bm, r * 0.55, r * 0.45, "square", frame=BLUE, s=0.8, y=-r + r * 0.78)
        info["chimney"] = stovepipe(P, bm, -r * 0.3, -r - 0.3, r * 0.8, rng)
        sign(P, bm, sign_kind, 0.0, -r, r * 0.92 + 0.6, s=1.0)
        if rng.random() < 0.6:
            woodpile(P, bm, r * 0.9, -r * 0.2)

    name = _p(c, "Ice Home %d" % idx, build)
    info.update(w=2 * r + 2.0, lantern=(1.8, 1.9, 2.2), free=True)
    return name, info


def tower_home(c, idx, rng, sign_kind, door_col):
    """A crooked tower of ice: five storeys of cut blocks, each turned and shifted off the
    one below, windows all the way up, a balcony, a crystal cap, the sign at the top."""
    info = {}

    def build(P, bm):
        x, y, z = 0.0, -2.6, 0.0
        rot = 0.0
        s = 4.6
        for k in range(5):
            hh = rng.uniform(2.4, 3.0)
            mat = ICE if k % 2 == 0 else CLEAR
            P.add(mat, lambda x=x, y=y, z=z, s=s, hh=hh, rot=rot: cuboid(bm, (x, y, z + hh / 2), (s, s, hh), rot=rot))
            P.add(BLUE, lambda x=x, y=y, z=z, s=s, hh=hh, rot=rot: cuboid(bm, (x, y, z + hh), (s + 0.3, s + 0.3, 0.2), rot=rot))
            if k > 0:
                window(P, bm, x + rng.uniform(-0.6, 0.6), z + hh * 0.55, rng.choice(("square", "tall", "round")), frame=BLUE, s=0.75,
                       y=y + s / 2 - 0.05)
            z += hh
            x += rng.uniform(-0.35, 0.35)
            y += rng.uniform(-0.2, 0.2)
            rot += rng.uniform(-0.18, 0.18)
            s *= 0.9
        P.add(BLUE, lambda x=x, y=y, z=z: _crystal(bm, (x, y, z), (0.08, 0, 1.0), 4.0, s * 0.62, phase=rot))
        sign(P, bm, sign_kind, x, y + s / 2 + 0.5, z - 1.4, s=0.85)
        # The door and its arch, the balcony round the second storey.
        arch(P, bm, rng.choice(("round", "pointed")), 2.2, 3.2, y=-0.2)
        P.add(door_col, lambda: cuboid(bm, (0, -0.3, 1.3), (1.6, 0.12, 2.6)))
        P.add(PLANK, lambda: cuboid(bm, (0, -2.6, 5.4), (6.0, 6.0, 0.25)))
        for k in range(8):
            a = k * math.tau / 8
            P.add(TIMBER, lambda a=a: cuboid(bm, (math.cos(a) * 2.9, -2.6 + math.sin(a) * 2.9, 6.0), (0.14, 0.14, 1.1)))
        lights(P, bm, 4.4, 5.7, y=0.5)
        info["chimney"] = (x - 1.0, y, z - 0.5)

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
        P.add(ROCK, lambda: _wedge(bm, -w / 2 - 1.8, w / 2 + 1.8, -11.0, -0.6, -1.5, h + 1.6, h + 2.6))
        P.add(CLEAR, lambda: cuboid(bm, (-w / 2 + 1.5, -0.5, h / 2 - 0.8), (3.0, 0.6, h + 0.6)))
        P.add(CLEAR, lambda: cuboid(bm, (w / 2 - 1.5, -0.5, h / 2 - 0.8), (3.0, 0.6, h + 0.6)))
        P.add(CLEAR, lambda: cuboid(bm, (0, -0.5, h - 1.2), (w - 6.0, 0.6, 2.4)))
        P.add("cave_rock", lambda: cuboid(bm, (0, -3.0, 2.4), (w - 6.0, 4.6, 5.0)))  # (the dark inside)
        for k, (x, z) in enumerate(((-1.4, 0.6), (0.6, 0.6), (-0.4, 1.8), (1.8, 0.6))):
            P.add(CLEAR, lambda x=x, z=z, k=k: cuboid(bm, (x, -1.6 - 0.3 * k, z), (1.2, 1.2, 1.2), rot=0.2 * k))
        for sx in (-1, 1):
            P.add(door_col, lambda sx=sx: cuboid(bm, (sx * (w / 2 - 2.9) + sx * 0.9, 1.2, 2.6), (2.9, 0.15, 5.2), rot=-sx * 1.15))
        P.add(TIMBER, lambda: cuboid(bm, (0, 1.0, h - 0.2), (w + 0.6, 2.4, 0.5)))
        P.add(TIMBER, lambda: cuboid(bm, (1.5, 2.6, h + 0.4), (0.4, 3.4, 0.4)))
        P.add(IRON, lambda: cuboid(bm, (1.5, 4.0, h - 1.6), (0.08, 0.08, 3.6)))
        P.add(CLEAR, lambda: cuboid(bm, (1.5, 4.0, h - 3.9), (1.4, 1.4, 1.2), rot=0.3))
        sign(P, bm, sign_kind, -w / 2 + 1.5, 0.6, h + 1.0, s=1.3)
        window(P, bm, w / 2 - 1.5, 3.2, "tall", frame=TIMBER)
        cornice(P, bm, w, h, rng, y=0.3)
        tool_rack(P, bm, -w / 2 - 0.4, 0.9)
        info["chimney"] = stovepipe(P, bm, w / 3, -2.5, h + 1.2, rng)

    name = _p(c, "Ice Home %d" % idx, build)
    info.update(w=w + 2.0, lantern=(-w / 2 + 1.5, 0.9, 4.2))
    return name, info


def tiny_hut(c, idx, rng, sign_kind, door_col):
    """A tiny hut: a block of snow under a lopsided cap of ice, a door you'd duck through,
    one window, a sled leant by it."""
    info = {}

    def build(P, bm):
        P.add(SNOW, lambda: cuboid(bm, (0, -1.6, 1.4), (3.6, 3.2, 3.0)))
        P.add(ICE, lambda: cuboid(bm, (0.15, -1.6, 3.15), (4.2, 3.8, 0.6), tilt=(0.06, 0.1)))
        P.add(BLUE, lambda: _crystal(bm, (0.3, -1.6, 3.4), (0.15, 0.0, 1.0), 1.6, 0.9, n=5))
        P.add(door_col, lambda: cuboid(bm, (-0.5, 0.02, 0.95), (1.1, 0.1, 1.9)))
        arch(P, bm, "crooked", 1.6, 2.2, y=0.05, mat=ICE)
        window(P, bm, 1.0, 1.8, "round", frame=BLUE, s=0.6, y=0.0)
        sign(P, bm, sign_kind, 0.4, 0.4, 4.4, s=0.7)
        P.add(TIMBER, lambda: cuboid(bm, (2.1, -0.4, 1.0), (0.1, 1.4, 2.2), tilt=(0.0, -0.25)))
        P.add(TIMBER, lambda: cuboid(bm, (2.25, -0.4, 1.0), (0.1, 0.2, 2.2), tilt=(0.0, -0.25)))
        info["chimney"] = stovepipe(P, bm, -1.0, -2.2, 3.4, rng)

    name = _p(c, "Ice Home %d" % idx, build)
    info.update(w=5.5, lantern=(-1.6, 0.6, 2.4), free=True)
    return name, info


def block_home(c, idx, rng, sign_kind, door_col):
    """A home cut into one giant block of clear ice, leaning a little where it settled: a
    deep doorway, windows cut in it, snow on its top, icicles down its edges."""
    s = 8.0
    info = {}

    def build(P, bm):
        P.add(ROCK, lambda: _wedge(bm, -s / 2 - 1.0, s / 2 + 1.0, -s - 4.0, -s + 1.0, -1.5, s * 0.6, s + 2.0))
        P.add(CLEAR, lambda: cuboid(bm, (0, -s / 2, s / 2 - 0.4), (s, s, s), tilt=(0.05, 0.04)))
        P.add(BLUE, lambda: cuboid(bm, (0, -s / 2, s / 2 - 0.4), (s * 0.7, s * 0.7, s * 0.7), tilt=(0.05, 0.04)))
        P.add("cave_rock", lambda: cuboid(bm, (0, 0.02, 1.6), (2.4, 0.2, 3.2)))
        arch(P, bm, rng.choice(("round", "keyhole")), 2.6, 3.8, y=0.15, mat=ICE)
        P.add(door_col, lambda: cuboid(bm, (0, 0.08, 1.45), (1.9, 0.1, 2.9)))
        for x, z in ((-2.6, 4.6), (2.4, 2.6), (1.6, 5.9)):
            window(P, bm, x, z, rng.choice(("square", "round", "tall")), frame=ICE, s=0.8, y=0.05)
        P.add(SNOW, lambda: blob(bm, (0.3, -s / 2, s - 0.1), s * 0.55, sx=1.0, sy=1.0, sz=0.25))
        for k in range(10):
            x = -s / 2 + 0.4 + k * (s - 0.8) / 9
            P.add(BLUE, lambda x=x, ln=rng.choice((0.5, 0.9, 1.4, 2.0)): _crystal(bm, (x, 0.25, s - 0.6), (0, 0, -1), ln, 0.16, n=4))
        sign(P, bm, sign_kind, -1.8, 0.7, s + 0.6, s=1.15)
        info["clutter"] = _clutter(P, bm, rng, s, s - 0.6, door_col, [(2.4, 2.6)], {"door_h": 3.4})

    name = _p(c, "Ice Home %d" % idx, build)
    info.update(w=s + 2.0, lantern=(s / 2 + 0.6, 0.8, 3.2))
    return name, info


# ------------------------------------------------------------------ the layout

# (Round the hollow from its mouth's east side, by the back, to its west: the ellipse's
# angle, how far in from the wall the front stands (m), the kind, a turn off true. "free"
# kinds stand out on the floor.)
SLOTS = [
    (-0.50, 2.0, "workshop", 0.10),
    (-0.05, 1.2, "cut", -0.12),
    (0.32, 7.5, "dome", 0.0),
    (0.62, 1.6, "stack", 0.08),
    (0.98, 4.0, "cut_deep", -0.06),
    (1.28, 5.8, "tower", 0.2),
    (1.55, 1.0, "block", -0.1),
    (1.90, 1.8, "cut", 0.14),
    (2.15, 4.5, "hut", 0.5),
    (2.40, 1.4, "stack", -0.08),
    (2.76, 2.0, "cut", 0.05),
    (3.05, 5.8, "tower", -0.25),
    (3.33, 1.2, "cut_deep", 0.12),
    (3.62, 7.0, "dome", 0.0),
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
                    deep=2.4 if kind == "cut_deep" else 0.0)


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
