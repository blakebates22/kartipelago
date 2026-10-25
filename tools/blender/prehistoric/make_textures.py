# Paints the Prehistoric World textures into the material library and lists them in
# materials.json. Every pixel is generated here from noise and simple shapes: original
# artwork for this MIT-licensed project, made in the same style as the starter pack
# (64x32, a handful of colours each, tiling seamlessly).
# SPDX-License-Identifier: MIT
#
#   python3 tools/blender/prehistoric/make_textures.py
#
# Needs Pillow. Safe to re-run: textures, thumbnails and library entries are replaced.

import json
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(os.path.dirname(HERE), "addons", "kartipelago_tools", "library")
W, H = 64, 32


def rng(seed):
    s = (seed * 2654435761) & 0xFFFFFFFF or 1

    def r():
        nonlocal s
        s ^= (s << 13) & 0xFFFFFFFF
        s ^= s >> 17
        s ^= (s << 5) & 0xFFFFFFFF
        return s / 4294967296

    return r


def noise(cx, cy, seed, w=W, h=H):
    """Smooth value noise that tiles over w x h, with cx x cy cells."""
    r = rng(seed)
    g = [[r() for _ in range(cx)] for _ in range(cy)]

    def at(x, y):
        fx, fy = x / w * cx, y / h * cy
        i, j = math.floor(fx), math.floor(fy)
        u, v = fx - i, fy - j
        u, v = u * u * (3 - 2 * u), v * v * (3 - 2 * v)
        a = g[j % cy][i % cx] + (g[j % cy][(i + 1) % cx] - g[j % cy][i % cx]) * u
        b = g[(j + 1) % cy][i % cx] + (g[(j + 1) % cy][(i + 1) % cx] - g[(j + 1) % cy][i % cx]) * u
        return a + (b - a) * v

    return at


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def pick(pal, v):
    return pal[max(0, min(len(pal) - 1, int(v * len(pal))))]


def paint(fn, w=W, h=H):
    im = Image.new("RGB", (w, h))
    px = im.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = hexrgb(fn(x, y))
    return im


def speckle(seed, n, w=W, h=H):
    r = rng(seed)
    return {(int(r() * w), int(r() * h)) for _ in range(n)}


# ------------------------------------------------------------------ River Valley


def valley_road():
    pal = ["#9a5a2c", "#b46c34", "#c98243", "#d99a55", "#e8b26a"]
    a, b = noise(4, 2, 101), noise(16, 8, 102)
    peb = speckle(103, 26)
    lit = {(x + 1, y) for x, y in peb}

    def f(x, y):
        if (x, y) in peb:
            return "#f2d39a"
        if (x, y) in lit:
            return "#7d4522"
        # Two faint wheel ruts along the road (V runs along it).
        rut = 0.12 if x % 32 in (9, 10, 22, 23) else 0
        return pick(pal, 0.15 + a(x, y) * 0.55 + b(x, y) * 0.3 - rut)

    return paint(f)


def valley_trail():
    """A footpath: the valley road's packed earth worn into the meadow, grass growing back
    in tufts and patches through it (no wheel ruts)."""
    dirt = ["#9a5a2c", "#b46c34", "#c98243", "#d99a55", "#e8b26a"]
    grass = ["#2f8a2a", "#3fa332", "#55bb3a", "#6fcf45", "#8ade55"]
    a, b = noise(4, 2, 121), noise(16, 8, 122)
    patch = noise(16, 8, 123)
    peb = speckle(124, 18)
    tufts = speckle(125, 45)
    tips = {(x, (y - 1) % H) for x, y in tufts}

    def f(x, y):
        v = 0.1 + a(x, y) * 0.6 + b(x, y) * 0.3
        if patch(x, y) > 0.74:
            return pick(grass, v)
        if (x, y) in tips:
            return pick(grass, 0.75)
        if (x, y) in tufts:
            return pick(grass, 0.3)
        if (x, y) in peb:
            return "#f2d39a"
        return pick(dirt, 0.15 + a(x, y) * 0.55 + b(x, y) * 0.3)

    return paint(f)


def valley_grass():
    pal = ["#2f8a2a", "#3fa332", "#55bb3a", "#6fcf45", "#8ade55"]
    a, b = noise(4, 2, 111), noise(16, 8, 112)
    flowers = speckle(113, 10)
    petals = speckle(114, 7)
    blades = speckle(115, 60)

    def f(x, y):
        if (x, y) in flowers:
            return "#ffe36b"
        if (x, y) in petals:
            return "#ffffff"
        v = 0.1 + a(x, y) * 0.6 + b(x, y) * 0.3
        if (x, y) in blades:
            v -= 0.25
        return pick(pal, v)

    return paint(f)


def valley_sand():
    pal = ["#d6b06a", "#e2c07c", "#ecd08f", "#f5dfa6", "#fbeec2"]
    a = noise(4, 2, 121)
    peb = speckle(122, 14)

    def f(x, y):
        if (x, y) in peb:
            return "#b89150"
        ripple = 0.18 * math.sin((x / W) * math.tau * 3 + a(x, y) * 4 + (y / H) * math.tau)
        return pick(pal, 0.3 + a(x, y) * 0.4 + ripple)

    return paint(f)


def valley_water():
    # v2: bluer (v1 was a turquoise #0f7f95..#7fe3da).
    pal = ["#0d5ea8", "#1476c2", "#1f92d6", "#38ade6", "#7fd3f5"]
    a, b = noise(4, 2, 131), noise(8, 4, 132)
    glints = speckle(133, 9)

    def f(x, y):
        if (x, y) in glints or ((x + 1, y) in glints):
            return "#e6fff8"
        wave = 0.22 * math.sin((y / H) * math.tau * 3 + math.sin((x / W) * math.tau * 2) * 1.4 + a(x, y) * 3)
        return pick(pal, 0.35 + wave + b(x, y) * 0.3)

    return paint(f)


def valley_cliff():
    # Warm sandstone in level bands, with green moss along some band tops.
    bands = ["#b45f34", "#c9773f", "#d98f4e", "#e6a764", "#c06a39", "#d48448"]
    a, b = noise(4, 2, 141), noise(16, 8, 142)

    def f(x, y):
        yy = y + a(x, y) * 3
        band = int(yy / 4) % len(bands)
        if int(yy) % 8 == 0 and b(x, y) > 0.55:
            return "#6aa83a"
        if int(yy) % 4 == 3:
            return "#8e4826"
        c = hexrgb(bands[band])
        k = 0.85 + b(x, y) * 0.3
        return "#%02x%02x%02x" % tuple(min(255, int(v * k)) for v in c)

    return paint(f)


def wood_planks():
    # Bridge deck boards running across the road (U), with gaps and nails.
    pal = ["#6b3d1c", "#83502a", "#9a6234", "#b07540", "#c4884c"]
    a, b = noise(2, 8, 151), noise(8, 16, 152)

    def f(x, y):
        board = y // 8
        yy = y % 8
        if yy == 7:
            return "#2e1a0c"  # the gap
        if yy == 0:
            return "#d29a5a"  # lit edge
        if (x + board * 23) % 32 in (3, 4) and yy in (2, 5):
            return "#3a3a3a"  # nails
        grain = 0.5 + 0.5 * math.sin(x * 0.7 + board * 2.1 + a(x, y) * 5)
        return pick(pal, 0.15 + grain * 0.45 + b(x, y) * 0.35)

    return paint(f)


def palm_bark():
    pal = ["#6a4426", "#7f5530", "#95683b", "#ab7c48", "#c19159"]
    a = noise(8, 2, 161)

    def f(x, y):
        ring = (y % 8) / 8
        v = 0.25 + 0.55 * (1 - abs(ring - 0.5) * 2) + a(x, y) * 0.2
        if y % 8 == 7:
            v = 0.02
        if y % 8 == 0:
            v = 0.9
        return pick(pal, v)

    return paint(f)


def palm_frond():
    pal = ["#1f6e2a", "#2d8a30", "#3fa437", "#5bbf3f", "#7fd24e"]
    a = noise(4, 2, 171)

    def f(x, y):
        # A midrib along U with leaflets slanting off it.
        mid = abs(y - 16)
        if mid <= 1:
            return "#c8d66a"
        slant = (x + mid * 1.6) % 6
        v = 0.55 + a(x, y) * 0.35 - (0.35 if slant < 1 else 0) - mid / 40
        return pick(pal, v)

    return paint(f)


def thatch():
    pal = ["#8a6a2c", "#a68038", "#c19a48", "#d6b25c", "#e8c874"]
    a, b = noise(16, 2, 181), noise(4, 4, 182)

    def f(x, y):
        row = y // 8
        yy = y % 8
        straw = 0.5 + 0.5 * math.sin(x * 2.3 + row * 1.7 + a(x, y) * 6)
        v = 0.1 + straw * 0.5 + b(x, y) * 0.3 + yy * 0.03
        if yy == 7:
            v = 0.0
        return pick(pal, v)

    return paint(f)


def tribal_paint():
    # Carved, painted wood: bands of zigzags, dots and diamonds in the accent colours.
    wood = ["#7a4a24", "#8e5a2e", "#a26a38"]
    a = noise(4, 2, 191)

    def f(x, y):
        base = pick(wood, 0.2 + a(x, y) * 0.7)
        if y in (0, 15, 16, 31):
            return "#3a2414"
        if 2 <= y <= 13:
            # Zigzag band.
            zz = abs(((x % 16) - 8)) + 3
            if abs(y - zz) <= 1:
                return "#f0645a"
            if abs(y - zz - 4) <= 0:
                return "#f7c948"
            return base
        if 18 <= y <= 29:
            cx = (x // 16) * 16 + 8
            d = abs(x - cx) + abs(y - 23.5)
            if d <= 4:
                return "#2ec4b6" if d > 2 else "#fff4d6"
            if (x % 8, y) in ((0, 19), (0, 28)):
                return "#f7c948"
            return base
        return base

    return paint(f)


def start_checker():
    def f(x, y):
        return "#f4f1e8" if ((x // 8) + (y // 8)) % 2 == 0 else "#1d1a18"

    return paint(f)


# ------------------------------------------------------------------ Jungle Cascade additions


def waterfall():
    pal = ["#4fb3d9", "#78c9e6", "#a6dff0", "#d4f1f8", "#ffffff"]
    a, b = noise(16, 2, 201), noise(8, 4, 202)

    def f(x, y):
        streak = 0.5 + 0.5 * math.sin(x * 1.3 + a(x, y) * 7)
        return pick(pal, 0.1 + streak * 0.55 + b(x, y) * 0.35)

    return paint(f)


def foam():
    pal = ["#9fd8e8", "#c4e9f2", "#e2f6fa", "#ffffff"]
    a, b = noise(8, 4, 211), noise(16, 8, 212)

    def f(x, y):
        return pick(pal, 0.2 + a(x, y) * 0.5 + b(x, y) * 0.35)

    return paint(f)


def jungle_fern():
    pal = ["#14502a", "#1d6a30", "#2b8838", "#40a640", "#62c24e"]
    a = noise(4, 2, 221)

    def f(x, y):
        # Overlapping leaves: rounded tips drawn as offset arcs.
        cell_x, cell_y = x % 16, y % 16
        off = 8 if (x // 16) % 2 else 0
        cy = (cell_y + off) % 16
        leaf = (cell_x - 8) ** 2 / 40 + (cy - 10) ** 2 / 30
        v = 0.75 - leaf * 0.5 + a(x, y) * 0.25
        if abs(cell_x - 8) < 1 and cy > 4:
            v += 0.2
        return pick(pal, v)

    return paint(f)


# ------------------------------------------------------------------ Fossil Swamp


def swamp_mud():
    pal = ["#2e2014", "#3d2b1a", "#4f3822", "#62462b", "#7a5a38"]
    a, b, c = noise(4, 2, 231), noise(16, 8, 232), noise(8, 4, 234)
    shine = speckle(233, 16)

    def f(x, y):
        if (x, y) in shine:
            return "#a99a7a"  # wet glints: it's slippery
        if c(x, y) > 0.74:
            return pick(["#3a4a3a", "#4a5c48", "#5a6e56"], (c(x, y) - 0.74) * 4)
        return pick(pal, 0.1 + a(x, y) * 0.6 + b(x, y) * 0.3)

    return paint(f)


def swamp_water():
    pal = ["#1f4a3c", "#28604a", "#357658", "#4a8c62", "#6aa66e"]
    a, b = noise(4, 2, 241), noise(8, 4, 242)
    pads = noise(8, 4, 243)

    def f(x, y):
        if pads(x, y) > 0.8:
            return "#7fbf4a" if pads(x, y) < 0.86 else "#a6d65c"  # lily pads
        wave = 0.15 * math.sin((y / H) * math.tau * 2 + a(x, y) * 4)
        return pick(pal, 0.3 + wave + b(x, y) * 0.35)

    return paint(f)


def swamp_moss():
    pal = ["#24402c", "#2f5536", "#3d6a3e", "#517f46", "#6c9450"]
    a, b = noise(4, 2, 251), noise(16, 8, 252)
    glow = speckle(253, 5)

    def f(x, y):
        if (x, y) in glow:
            return "#b8f0d8"
        return pick(pal, 0.1 + a(x, y) * 0.55 + b(x, y) * 0.35)

    return paint(f)


def bone():
    pal = ["#b9ab8a", "#cfc2a0", "#e0d5b6", "#eee6cc", "#f8f2e0"]
    a, b = noise(4, 2, 261), noise(16, 8, 262)
    crack = noise(8, 4, 263)

    def f(x, y):
        if abs(crack(x, y) - 0.5) < 0.025:
            return "#8a7a5a"
        pits = (x * 7 + y * 13) % 29 == 0
        return pick(pal, 0.2 + a(x, y) * 0.5 + b(x, y) * 0.3 - (0.4 if pits else 0))

    return paint(f)


def swamp_stone():
    # Old paving slabs, green with moss in the joints.
    pal = ["#6a6e62", "#7c8070", "#8e917e", "#a0a28c"]
    a, b = noise(4, 2, 271), noise(16, 8, 272)

    def f(x, y):
        row = y // 16
        bx = (x + (row % 2) * 12) % 24
        by = y % 16
        if bx == 0 or by == 0:
            return "#4f7a3a" if b(x, y) > 0.45 else "#454a40"
        if bx == 1 or by == 1:
            return "#b4b6a0"
        v = 0.2 + a(x, y) * 0.5 + b(x, y) * 0.3
        if a(x, y) > 0.72:
            return "#6f8a4a"
        return pick(pal, v)

    return paint(f)


def glow_cap():
    pal = ["#4b2a7a", "#6a3fa0", "#8a5cc4", "#a97ce0", "#d0a8ff"]
    a = noise(4, 2, 281)

    def f(x, y):
        spot = ((x % 16) - 8) ** 2 + ((y % 16) - 8) ** 2
        if spot < 6:
            return "#b8fff0"
        if spot < 12:
            return "#6ae0d0"
        return pick(pal, 0.3 + a(x, y) * 0.6)

    return paint(f)


def pyramid_step():
    # Big carved blocks with a meander frieze band.
    pal = ["#7d8a6a", "#8e9a78", "#a0aa86", "#b2ba94"]
    a, b = noise(4, 2, 291), noise(16, 8, 292)

    def f(x, y):
        if y in (0, 31):
            return "#3e4636"
        if y in (1,):
            return "#c8ceaa"
        if 12 <= y <= 19:
            # A stepped meander carving.
            u = x % 16
            v = y - 12
            shape = (u < 2) or (v == 0 and u < 10) or (u == 9 and v < 5) or (v == 4 and 5 <= u <= 9) or (u == 5 and 2 <= v <= 4)
            return "#4e5842" if shape else pick(pal, 0.5 + b(x, y) * 0.4)
        if x % 32 == 0:
            return "#4e5842"
        if a(x, y) > 0.7 and y > 20:
            return "#5e8a3a"  # moss
        return pick(pal, 0.15 + a(x, y) * 0.5 + b(x, y) * 0.35)

    return paint(f)


# ------------------------------------------------------------------ Ember Volcano additions


def volcano_crust():
    pal = ["#1d1414", "#2a1c1a", "#3a2622", "#4a302a"]
    a, b = noise(4, 2, 301), noise(8, 4, 302)

    def f(x, y):
        c = abs(b(x, y) - 0.5)
        if c < 0.03:
            return "#ffd23a"
        if c < 0.06:
            return "#ff7a1a"
        if c < 0.08:
            return "#b8361a"
        return pick(pal, 0.1 + a(x, y) * 0.8)

    return paint(f)


def ember_road():
    # Dark ash road with glowing embers in the cracks; drives as plain road.
    pal = ["#3a2c28", "#4a3832", "#5a463e", "#6a544a"]
    a, b = noise(4, 2, 311), noise(16, 8, 312)
    embers = speckle(313, 8)

    def f(x, y):
        if (x, y) in embers:
            return "#ff9a3a"
        return pick(pal, 0.15 + a(x, y) * 0.5 + b(x, y) * 0.35)

    return paint(f)


def blossom():
    # Flower heads on leaves: coral, gold and white petals with gold centres.
    leaf = ["#2f8a2a", "#3fa332", "#55bb3a"]
    a = noise(4, 2, 321)
    cols = ["#f0645a", "#f7c948", "#ffffff", "#ff8fc8"]

    def f(x, y):
        cx, cy = (x // 8) * 8 + 4, (y // 8) * 8 + 4
        k = (x // 8) * 3 + (y // 8) * 5
        d = (x - cx) ** 2 + (y - cy) ** 2
        if d <= 1:
            return "#ffd23a"
        if d <= 8:
            return cols[k % 4]
        return pick(leaf, a(x, y))

    return paint(f)


def smoke():
    pal = ["#4a3a3a", "#5e4c4a", "#76625e", "#8e7a74", "#a8948c"]
    a, b = noise(4, 2, 331), noise(8, 4, 332)

    def f(x, y):
        return pick(pal, 0.1 + a(x, y) * 0.6 + b(x, y) * 0.3)

    return paint(f)


def lily_pad():
    # Round green pads with a notch and veins, on clear water (cut out by the mesh).
    pal = ["#2f8a2a", "#3fa332", "#56bb3c", "#74cf4a"]
    a = noise(4, 2, 341)

    def f(x, y):
        cx, cy = (x // 32) * 32 + 16, 16
        dx, dy = x - cx, y - cy
        ang = math.atan2(dy, dx)
        if abs(ang) < 0.1 and dx > 0:
            return "#2a6a2a"  # the notch's edge
        vein = abs(math.sin(ang * 5)) < 0.12
        d = math.hypot(dx, dy)
        v = 0.3 + a(x, y) * 0.4 + (0.25 if d < 4 else 0) - (0.3 if vein else 0) - d / 60
        return pick(pal, v)

    return paint(f)


def lotus():
    # Pink-to-white petals for floating water flowers.
    def f(x, y):
        t = y / H
        cols = ["#ff6fa8", "#ff8fbc", "#ffb0cf", "#ffd2e4", "#fff2f7"]
        streak = 0.1 * math.sin(x * 0.8)
        return pick(cols, t + streak)

    return paint(f)


def falls_sheet():
    # Riverbend's waterfall: deep blue with bright streaks (matches the bluer river).
    pal = ["#1f74c4", "#3b97da", "#6fbdec", "#b4e2f7", "#ffffff"]
    a, b = noise(16, 2, 351), noise(8, 4, 352)

    def f(x, y):
        streak = 0.5 + 0.5 * math.sin(x * 1.1 + a(x, y) * 8)
        return pick(pal, 0.05 + streak * 0.6 + b(x, y) * 0.35)

    return paint(f)


def falls_veil():
    # A thin, fast white veil over the sheet: mostly white streaks.
    pal = ["#9ed6f2", "#d2eefa", "#f2fbff", "#ffffff"]
    a = noise(16, 2, 361)

    def f(x, y):
        streak = 0.5 + 0.5 * math.sin(x * 2.3 + a(x, y) * 9)
        return pick(pal, streak * 0.8 + 0.2 * a(x, y))

    return paint(f)


def falls_foam():
    # Bright churning white water at the waterfall's foot.
    pal = ["#bfe6f7", "#e4f6fd", "#ffffff", "#ffffff"]
    a, b = noise(8, 4, 371), noise(16, 8, 372)

    def f(x, y):
        return pick(pal, 0.15 + a(x, y) * 0.55 + b(x, y) * 0.35)

    return paint(f)


def cattail_leaf():
    # Long blades: vertical green streaks with a pale midrib now and then.
    pal = ["#3c7a26", "#4f9330", "#62a83a", "#7cbd48", "#9bcf5a"]
    a = noise(16, 2, 381)

    def f(x, y):
        if x % 8 == 3:
            return "#a9cf6a"
        return pick(pal, 0.25 + a(x, y) * 0.55 + 0.15 * math.sin(x * 0.9))

    return paint(f)


def cattail_head():
    # The velvety brown seed head.
    pal = ["#5a3417", "#6e4220", "#83522a", "#99633a"]
    a, b = noise(8, 4, 391), noise(16, 8, 392)

    def f(x, y):
        return pick(pal, 0.2 + a(x, y) * 0.5 + b(x, y) * 0.3)

    return paint(f)


def campfire_flame():
    # Flame tongues: white-yellow at the root to deep orange at the tips (V runs up).
    cols = ["#fff6c8", "#ffe070", "#ffb63a", "#ff8a24", "#f2561a"]
    a = noise(8, 2, 401)

    def f(x, y):
        return pick(cols, 1 - y / H + (a(x, y) - 0.5) * 0.35)

    return paint(f)


def canopy_bright():
    # A sunnier leaf canopy for the grand trees: clumps of light and mid greens.
    pal = ["#2f7d2c", "#3f9634", "#55ad3c", "#72c44a", "#95d75c"]
    a, b = noise(8, 4, 411), noise(16, 8, 412)

    def f(x, y):
        clump = 0.5 + 0.5 * math.sin(x * 0.7 + 2 * math.sin(y * 0.5))
        return pick(pal, 0.15 + a(x, y) * 0.4 + b(x, y) * 0.25 + clump * 0.2)

    return paint(f)


def rainbow():
    # Soft rainbow bands across V, for the mist under the waterfall.
    bands = ["#ff5a5a", "#ff9d42", "#ffe24a", "#6fe05a", "#4ab6ff", "#8a6dff"]

    def f(x, y):
        return bands[min(len(bands) - 1, int(y / H * len(bands)))]

    return paint(f)


# ------------------------------------------------------------------ Cascade v2 (jungle ruins)


def canyon_rock_grey():
    # Grey-green layered rock: slanted beds, dark cracks, pale edges.
    pal = ["#3e4740", "#525c52", "#67705f", "#7d8470", "#9a9c84"]
    a, b = noise(6, 3, 421), noise(16, 8, 422)

    def f(x, y):
        bed = math.sin((y + x * 0.25) * 0.55 + a(x, y) * 4)
        if abs(bed) < 0.08:
            return "#2c332d"
        v = 0.35 + bed * 0.18 + a(x, y) * 0.3 + b(x, y) * 0.2
        if bed > 0.85:
            v += 0.2
        return pick(pal, v)

    return paint(f)


def canyon_rock_moss():
    # Dark rock blotched with moss.
    rock = ["#3a3a34", "#4b4a41", "#5e5b4e", "#716c5b"]
    moss = ["#2f5a24", "#3d7230", "#4f8a38", "#68a446"]
    a, b, m = noise(8, 4, 431), noise(16, 8, 432), noise(5, 3, 433)

    def f(x, y):
        k = m(x, y) + b(x, y) * 0.3
        if k > 0.72:
            return pick(moss, (k - 0.72) * 2.2 + a(x, y) * 0.4)
        crack = abs(math.sin(x * 0.35 + a(x, y) * 6)) < 0.05
        return "#25241f" if crack else pick(rock, 0.2 + a(x, y) * 0.5 + b(x, y) * 0.3)

    return paint(f)


def canyon_rock_ochre():
    # Warm ochre sandstone with wavy, uneven bands (not the even fossil strata).
    pal = ["#6e4a2c", "#8a5f36", "#a8763f", "#c18f52", "#d7aa6a"]
    a, b = noise(4, 2, 441), noise(16, 8, 442)

    def f(x, y):
        band = math.sin(y * 0.42 + a(x, y) * 5 + math.sin(x * 0.12) * 1.5)
        v = 0.45 + band * 0.25 + b(x, y) * 0.3
        if abs(band) < 0.06:
            v -= 0.35
        return pick(pal, v)

    return paint(f)


def ruin_stone():
    # Big weathered blocks, moss in the joints: the ruins and the temple bridge.
    pal = ["#5d6152", "#6f7461", "#838672", "#999a83", "#adab92"]
    a, b = noise(8, 4, 451), noise(16, 8, 452)

    def f(x, y):
        row = y // 16
        off = 16 if row % 2 else 0
        bx, by = (x + off) % 32, y % 16
        if bx < 1 or by < 1:
            return pick(["#3a5a2a", "#486c32", "#2e3a2a"], a(x, y))
        chip = b(x, y) > 0.78
        v = 0.25 + a(x, y) * 0.45 + b(x, y) * 0.25 - (0.25 if chip else 0) + (0.12 if by == 1 or bx == 1 else 0)
        return pick(pal, v)

    return paint(f)


def ruin_glyph():
    # A carved frieze: square glyph panels with spirals, eyes and steps, worn and mossy.
    pal = ["#5e6352", "#757a66", "#8d917b", "#a7a891"]
    a = noise(8, 4, 461)

    def f(x, y):
        cx, cy = x % 16, y % 16
        cell = (x // 16 + (y // 16) * 3) % 4
        edge = cx < 1 or cy < 1 or cx > 14 or cy > 14
        dx, dy = cx - 7.5, cy - 7.5
        r = math.hypot(dx, dy)
        if cell == 0:
            carved = abs(r - (math.atan2(dy, dx) + math.pi) * 0.9) < 0.9 and r < 6.5
        elif cell == 1:
            carved = (4 < r < 6) or r < 1.6
        elif cell == 2:
            carved = (cy > 11 - (cx // 3) * 2 and cy < 13 - (cx // 3) * 2) or (2 < cy < 4)
        else:
            carved = (abs(dx) < 1 or abs(dy) < 1) and r < 6 or (abs(abs(dx) - 4) < 1 and abs(abs(dy) - 4) < 1)
        if edge:
            return "#454a3c"
        if carved:
            return "#3c4034"
        v = 0.3 + a(x, y) * 0.55
        if a(x, y) > 0.8:
            return "#4d7a34"
        return pick(pal, v)

    return paint(f)


def ruin_dark():
    # Soot-darkened stone inside the temple tunnel.
    pal = ["#24221e", "#302d27", "#3d3930", "#4c463a", "#5a5243"]
    a, b = noise(8, 4, 471), noise(16, 8, 472)

    def f(x, y):
        row = y // 16
        bx, by = (x + (16 if row % 2 else 0)) % 32, y % 16
        if bx < 1 or by < 1:
            return "#181612"
        return pick(pal, 0.15 + a(x, y) * 0.55 + b(x, y) * 0.3)

    return paint(f)


def jungle_bark():
    # Dark, deeply ridged bark for the giant trees, with moss.
    pal = ["#3b2a1e", "#4b3524", "#5d432c", "#715336", "#856441"]
    a, b = noise(16, 2, 481), noise(6, 3, 482)

    def f(x, y):
        ridge = math.sin(x * 0.9 + a(x, y) * 6)
        if b(x, y) > 0.74:
            return pick(["#3e6a2c", "#4f8236", "#64983f"], a(x, y))
        return pick(pal, 0.4 + ridge * 0.3 + a(x, y) * 0.2)

    return paint(f)


def canopy_dark():
    # Deep jungle canopy: dark greens with lighter leaf clumps.
    pal = ["#163a1c", "#1f4f24", "#2b652c", "#3a7d36", "#4f9442"]
    a, b = noise(8, 4, 491), noise(16, 8, 492)

    def f(x, y):
        clump = 0.5 + 0.5 * math.sin(x * 0.8 + 2.2 * math.sin(y * 0.6))
        return pick(pal, 0.1 + a(x, y) * 0.45 + b(x, y) * 0.25 + clump * 0.2)

    return paint(f)


def big_leaf():
    # Elephant-ear leaves: broad green with a pale midrib and veins (V along the leaf).
    pal = ["#2f7a2a", "#3c9032", "#4ea83c", "#66bd4a"]
    a = noise(8, 2, 501)

    def f(x, y):
        mid = abs(y - 16)
        if mid < 1.2:
            return "#b8d872"
        vein = abs(((x + mid * 1.4) % 8) - 4) < 0.6
        return pick(pal, 0.55 + a(x, y) * 0.35 - (0.3 if vein else 0) - mid / 50)

    return paint(f)


def vine_leaf():
    # Hanging vines: small overlapping ivy leaves on a dark stem.
    pal = ["#1f4f1f", "#2d6a28", "#3f8634", "#58a046"]
    a = noise(8, 4, 511)

    def f(x, y):
        cx, cy = x % 8, y % 8
        off = 4 if (y // 8) % 2 else 0
        d = math.hypot((x + off) % 8 - 4, cy - 4)
        if d < 3.2:
            return pick(pal, 0.4 + (3.2 - d) * 0.15 + a(x, y) * 0.2)
        return "#173a17"

    return paint(f)


def frog_skin():
    # Bright tree-frog green with darker spots and a pale belly band (V down the body).
    pal = ["#3fae2a", "#58c43a", "#74d84e"]
    a, b = noise(8, 4, 521), noise(4, 2, 522)

    def f(x, y):
        if y > 24:
            return "#e8f0b0"
        if b(x, y) > 0.72 and a(x, y) > 0.5:
            return "#1f5a1a"
        return pick(pal, a(x, y))

    return paint(f)


def log_end():
    # Cut log ends: rings round a pale heart.
    pal = ["#8a5e32", "#a8763f", "#c49a5e", "#d9b47a"]

    def f(x, y):
        d = math.hypot((x % 32) - 16, y - 16)
        if d > 14.5:
            return "#4b3524"
        return pick(pal, 0.5 + 0.5 * math.sin(d * 1.3))

    return paint(f)


def torch_glow():
    # A flickering torch flame: hot white-yellow core to orange (scrolls upward).
    cols = ["#fffbe0", "#ffe58a", "#ffbb3a", "#ff8a22", "#e85a1a"]
    a = noise(8, 2, 531)

    def f(x, y):
        return pick(cols, 1 - y / H + (a(x, y) - 0.5) * 0.5)

    return paint(f)


def jungle_mud():
    # Dark, wet riverbank mud with leaf litter.
    pal = ["#3b2f22", "#4a3b2a", "#5a4832", "#6b563b"]
    a, b = noise(8, 4, 541), noise(16, 8, 542)

    def f(x, y):
        if b(x, y) > 0.8:
            return pick(["#5b7a2a", "#7a8a32", "#8a6a2a"], a(x, y))
        return pick(pal, 0.2 + a(x, y) * 0.5 + b(x, y) * 0.3)

    return paint(f)


def pterosaur_skin():
    # Leathery wing and body: rust brown to tan with darker veining.
    pal = ["#7a3a24", "#94502e", "#ad6a3c", "#c4864e"]
    a = noise(8, 4, 551)

    def f(x, y):
        vein = abs(math.sin(x * 0.4 + y * 0.15)) < 0.08
        return "#5a2a1a" if vein else pick(pal, 0.3 + a(x, y) * 0.6)

    return paint(f)


# ------------------------------------------------------------------ Beach Party


def beach_sand():
    pal = ["#ead39a", "#f2dfaa", "#f7e8bc", "#fbf0cd", "#fff7e0"]
    a, b = noise(4, 2, 1501), noise(16, 8, 1502)
    shells = speckle(1503, 6)
    pink = speckle(1504, 4)
    peb = speckle(1505, 12)

    def f(x, y):
        if (x, y) in shells:
            return "#ffffff"
        if (x, y) in pink:
            return "#f7b3a8"
        if (x, y) in peb:
            return "#d2b277"
        ripple = 0.12 * math.sin((x / W) * math.tau * 2 + a(x, y) * 3 + (y / H) * math.tau * 2)
        return pick(pal, 0.25 + a(x, y) * 0.4 + b(x, y) * 0.2 + ripple)

    return paint(f)


def beach_road():
    # Packed sand, a little darker, with two wheel ruts and the odd shell.
    pal = ["#a8784a", "#b88a56", "#c69a64", "#d2a872", "#dcb882"]
    a, b = noise(4, 2, 1511), noise(16, 8, 1512)
    shells = speckle(1513, 5)

    def f(x, y):
        if (x, y) in shells:
            return "#fff6e6"
        rut = 0.16 if x % 32 in (9, 10, 22, 23) else 0
        return pick(pal, 0.2 + a(x, y) * 0.45 + b(x, y) * 0.3 - rut)

    return paint(f)


def wet_sand():
    pal = ["#b99a62", "#c6a76e", "#d1b47c", "#dcc28d"]
    a = noise(4, 2, 1521)
    glints = speckle(1522, 8)

    def f(x, y):
        if (x, y) in glints:
            return "#fff4d8"
        return pick(pal, 0.2 + a(x, y) * 0.6)

    return paint(f)


def sea_water():
    pal = ["#0a8fb0", "#13a9c4", "#25c2d2", "#4fd8dc", "#9ef0e6"]
    a, b = noise(4, 2, 1531), noise(8, 4, 1532)
    glints = speckle(1533, 10)

    def f(x, y):
        if (x, y) in glints:
            return "#ffffff"
        wave = 0.15 * math.sin((x / W) * math.tau * 2 + (y / H) * math.tau + a(x, y) * 5)
        return pick(pal, 0.2 + a(x, y) * 0.35 + b(x, y) * 0.25 + wave)

    return paint(f)


def surf_foam():
    a, b = noise(8, 4, 1541), noise(16, 8, 1542)

    def f(x, y):
        v = a(x, y) * 0.6 + b(x, y) * 0.4 + 0.25 * math.sin((x / W) * math.tau * 3)
        if v > 0.62:
            return "#ffffff"
        if v > 0.5:
            return "#d8f8f6"
        return "#7fe0e0"

    return paint(f)


def fabric(base, light, dark, seed):
    a = noise(4, 2, seed)

    def make():
        def f(x, y):
            # A faint weave.
            if (x + y) % 4 == 0 and a(x, y) > 0.5:
                return light
            if (x - y) % 6 == 0 and a(x, y) < 0.35:
                return dark
            return base

        return paint(f)

    return make


party_red = fabric("#ec3b4a", "#ff6a74", "#c62838", 1551)
party_yellow = fabric("#ffd23f", "#fff08a", "#e8b020", 1552)
party_teal = fabric("#19c3b0", "#5be6d4", "#0f9a8c", 1553)
party_pink = fabric("#ff6fb1", "#ffa3cf", "#e04c93", 1554)
party_white = fabric("#fbf7ee", "#ffffff", "#e3ddd0", 1555)
party_blue = fabric("#2f80ed", "#6aa8ff", "#1f5fc0", 1556)


def lantern_glow():
    a = noise(4, 2, 1561)

    def f(x, y):
        if y % 8 == 0:
            return "#d06a20"
        return pick(["#ff9a3a", "#ffb24a", "#ffc866", "#ffdc8a"], 0.2 + a(x, y) * 0.7)

    return paint(f)


def tiki_wood():
    # Carved tiki posts: warm wood, with bands of eyes, mouths and zigzags.
    pal = ["#6a3a1c", "#844a24", "#9a5a2e", "#b06c38"]
    a = noise(8, 4, 1571)

    def f(x, y):
        v = 0.3 + a(x, y) * 0.5 + 0.15 * math.sin(y * 1.3)
        cx = x % 16
        # A face every 16 px: two eyes and a wide mouth.
        if 8 <= y <= 11 and cx in (3, 4, 11, 12):
            return "#f4e2b0" if y in (9, 10) else "#2a160a"
        if 18 <= y <= 21 and 2 <= cx <= 13:
            return "#2a160a" if y in (18, 21) or cx in (2, 13) else "#f4e2b0"
        if y in (27, 28) and (cx + (y - 27) * 2) % 4 < 2:
            return "#2a160a"
        return pick(pal, v)

    return paint(f)


def dino_scales():
    # Bright scaly hide for the partygoers' accessories and the canoes.
    a = noise(4, 2, 1581)

    def f(x, y):
        if (x // 4 + y // 4) % 2 == 0 and (x % 4 == 0 or y % 4 == 0):
            return "#2a8c4a"
        return pick(["#3fae5e", "#52c46e", "#6ad884"], a(x, y))

    return paint(f)


# ------------------------------------------------------------------ Frost Citadel


def snow_ground():
    # Fresh snow under moonlight: white with lavender-blue hollows and the odd sparkle.
    pal = ["#b9c4ea", "#cad3f2", "#dbe2f8", "#e9eefc", "#f7f9ff"]
    a, b = noise(4, 2, 1601), noise(16, 8, 1602)
    sparkle = speckle(1603, 9)

    def f(x, y):
        if (x, y) in sparkle:
            return "#ffffff"
        return pick(pal, 0.2 + a(x, y) * 0.5 + b(x, y) * 0.3)

    return paint(f)


def snow_stone_road():
    # An old paved road under packed snow: white-lavender snow worn through to the grey
    # paving here and there, two darker wheel tracks pressed along it.
    snow = ["#c9cfe8", "#d6dbf0", "#e2e6f6", "#eef0fb"]
    pave = ["#8d90ab", "#9da1bb", "#aeb2c9"]
    a, b = noise(4, 2, 1611), noise(16, 8, 1612)

    def f(x, y):
        rut = x % 32 in (9, 10, 11, 21, 22, 23)
        worn = a(x, y) * 0.75 + b(x, y) * 0.45
        if worn < 0.38 and not rut:
            joint = x % 16 == 0 or (y + (8 if (x // 16) % 2 else 0)) % 16 == 0
            return "#6c7090" if joint else pick(pave, b(x, y))
        v = 0.15 + worn * 0.7 - (0.35 if rut else 0)
        if rut and (y % 6) < 2:
            v -= 0.1
        return pick(snow, v)

    return paint(f)


def icy_stone_road():
    pal = ["#5fa7d6", "#76bde4", "#92d2ee", "#b4e4f6"]
    a = noise(4, 2, 1621)
    glints = speckle(1622, 14)
    cracks = speckle(1623, 30)

    def f(x, y):
        if (x, y) in glints:
            return "#ffffff"
        if (x, y) in cracks or (x + y * 2) % 37 == 0:
            return "#e6f8ff"
        joint = x % 16 == 0 or (y + (8 if (x // 16) % 2 else 0)) % 16 == 0
        if joint:
            return "#4c87b4"
        return pick(pal, 0.2 + a(x, y) * 0.7)

    return paint(f)


def packed_snow_road():
    pal = ["#c2c8e2", "#ced3ea", "#dadff1", "#e6e9f7"]
    a, b = noise(4, 2, 1631), noise(16, 8, 1632)

    def f(x, y):
        rut = x % 32 in (8, 9, 10, 22, 23, 24)
        tread = rut and y % 4 == 0
        v = 0.25 + a(x, y) * 0.4 + b(x, y) * 0.3 - (0.3 if rut else 0) - (0.15 if tread else 0)
        return pick(pal, v)

    return paint(f)


def frost_rock():
    pal = ["#5d6283", "#6d7395", "#7e85a7", "#9198b8", "#a6adca"]
    a, b = noise(4, 2, 1641), noise(16, 8, 1642)

    def f(x, y):
        v = 0.15 + a(x, y) * 0.5 + b(x, y) * 0.35
        streak = math.sin(x / W * math.tau * 3 + a(x, y) * 4) > 0.75 and (y % 8) < 3
        if streak or v > 0.92:
            return "#e4e9fb"
        if (x * 7 + y * 3) % 23 == 0:
            return "#363a56"
        return pick(pal, v)

    return paint(f)


def frost_cliff():
    # Rock with snow lying on every ledge: bands of white across grey-blue.
    pal = ["#626887", "#737a9b", "#868dad", "#9aa1c0"]
    a = noise(4, 2, 1651)

    def f(x, y):
        ledge = (y + int(a(x, y) * 6)) % 11
        if ledge < 2:
            return "#eef1fd" if ledge == 0 else "#cdd4f0"
        return pick(pal, 0.2 + a(x, y) * 0.7)

    return paint(f)


def citadel_stone():
    # Warm, weathered sandstone blocks (the concept art's tan-brown masonry).
    pal = ["#a88e76", "#baa084", "#cbb293", "#d9c2a2", "#e6d1b2"]
    a = noise(4, 2, 1661)

    def f(x, y):
        row = y // 8
        off = 8 if row % 2 else 0
        if y % 8 == 0 or (x + off) % 16 == 0:
            return "#6b5848"
        moss = a(x, y) > 0.78 and y % 8 > 4
        if moss:
            return "#7f8c72"
        return pick(pal, 0.2 + a(x, y) * 0.5 + ((x * 13 + row * 7) % 5) * 0.06)

    return paint(f)


def citadel_carved():
    # Carved panels: spirals, step-frets and little dinosaur skulls, cut into the stone.
    pal = ["#b49a80", "#c6ab8f", "#d6bc9f"]
    a = noise(4, 2, 1671)

    def f(x, y):
        cx, cy = x % 16, y % 16
        cell = (x // 16 + y // 16) % 3
        if cx in (0, 15) or cy in (0, 15):
            return "#6b5848"
        groove = False
        if cell == 0:  # a square spiral
            r = max(abs(cx - 7.5), abs(cy - 7.5))
            groove = int(r) % 3 == 0 and not (cy == 7 and cx > 7)
        elif cell == 1:  # a step-fret
            groove = (cx - 2) == (cy // 2) * 2 or cy == 12 or (cx == 13 and cy > 3)
        else:  # a skull: eye sockets and teeth
            groove = (cy in (5, 6) and cx in (4, 5, 10, 11)) or (cy == 10 and 3 <= cx <= 12) or (cy == 11 and cx % 2 == 1 and 3 <= cx <= 12)
        if groove:
            return "#5a4636"
        return pick(pal, 0.2 + a(x, y) * 0.7)

    return paint(f)


def citadel_dark():
    pal = ["#6a5c52", "#796a5d", "#887869"]
    a = noise(4, 2, 1681)

    def f(x, y):
        row = y // 8
        if y % 8 == 0 or (x + (8 if row % 2 else 0)) % 16 == 0:
            return "#40362f"
        return pick(pal, a(x, y))

    return paint(f)


def temple_gold():
    # A golden sun disk emblem (glowing): rays round a ring round a face.
    def f(x, y):
        cx, cy = (x % 32) - 15.5, y - 15.5
        r = math.hypot(cx, cy)
        a = math.atan2(cy, cx)
        if r < 5:
            return "#ffe38a" if not (abs(cy + 1.5) < 1 and abs(abs(cx) - 2) < 1) else "#a8641c"
        if r < 7:
            return "#d99a2b"
        if r < 13 and math.cos(a * 8) > 0.3:
            return "#f5c242"
        return "#5a3d22"

    return paint(f)


def banner(base, trim, emblem):
    def make():
        def f(x, y):
            cx, cy = (x % 32) - 15.5, (y % 32) - 13.5
            if x % 32 in (1, 30) or y % 32 in (1,):
                return trim
            r = math.hypot(cx, cy)
            a = math.atan2(cy, cx)
            if 3 < r < 5 or (r < 9 and r > 6.5 and math.cos(a * 6) > 0.5):
                return emblem
            if r < 2:
                return emblem
            return base

        return paint(f)

    return make


banner_red = banner("#a5282e", "#e8b64a", "#f2c95a")
banner_teal = banner("#16707a", "#e8b64a", "#f2c95a")
banner_blue = banner("#2c3f8f", "#d7dcf4", "#e8b64a")


def ice():
    pal = ["#6fd0e6", "#8fe0f0", "#b2ecf7", "#d8f7fc"]
    a, b = noise(4, 8, 1691), noise(8, 16, 1692)

    def f(x, y):
        v = a(x, y) * 0.6 + b(x, y) * 0.4 + 0.2 * math.sin(x / W * math.tau * 4)
        if (x * 5 + y) % 29 == 0:
            return "#ffffff"
        return pick(pal, v)

    return paint(f)


def frost_falls():
    pal = ["#2fb6cf", "#59cde0", "#8fe3ef", "#c8f5fb", "#ffffff"]
    a = noise(8, 2, 1701)

    def f(x, y):
        streak = math.sin(x * 1.9 + a(x, y) * 6) * 0.5 + 0.5
        return pick(pal, streak * 0.7 + a(x, y) * 0.4)

    return paint(f)


def frost_pool():
    pal = ["#1d8fae", "#2aa9c4", "#45c3d8", "#7ad9e6"]
    a, b = noise(4, 2, 1711), noise(8, 4, 1712)
    floes = speckle(1713, 12)

    def f(x, y):
        if (x, y) in floes:
            return "#eaf9ff"
        return pick(pal, 0.2 + a(x, y) * 0.45 + b(x, y) * 0.3)

    return paint(f)


def fog_sheet():
    a, b = noise(4, 2, 1721), noise(8, 4, 1722)

    def f(x, y):
        return pick(["#9fd8e4", "#b9e4ee", "#d3eff6", "#eef9fc"], a(x, y) * 0.6 + b(x, y) * 0.5)

    return paint(f)


def pine_snow():
    # Conifer needles with snow lying on the boughs.
    a = noise(8, 4, 1731)

    def f(x, y):
        if y % 8 < 2 and a(x, y) > 0.35:
            return "#eef2fd" if y % 8 == 0 else "#cfd8f0"
        return pick(["#1f4a3c", "#285a47", "#326a52", "#3d7a5d"], a(x, y))

    return paint(f)


def frond_snow():
    a = noise(8, 4, 1741)

    def f(x, y):
        if y < 10 and a(x, y) > 0.3:
            return "#eef2fd"
        rib = x % 8 == 0
        return "#1f5a34" if rib else pick(["#2a6e40", "#357f4b", "#438f57"], a(x, y))

    return paint(f)


def window_glow():
    a = noise(4, 2, 1751)

    def f(x, y):
        return pick(["#ff9b3a", "#ffb04a", "#ffc766", "#ffdc8f"], 0.2 + a(x, y) * 0.8)

    return paint(f)


# ------------------------------------------------------------------ Bonebog Pyramid (the living swamp)


def bog_water():
    # Murky swamp water: deep green, darker in the depths, with long soft ripples of
    # lighter green and a few bright glints (it scrolls slowly).
    pal = ["#123824", "#17432a", "#1c4f30", "#235c35", "#2b693b"]
    a, b = noise(2, 2, 1801), noise(8, 4, 1802)
    glint = speckle(1804, 7)

    def f(x, y):
        if (x, y) in glint:
            return "#cfeea0"
        ripple = math.sin((y / H) * math.tau * 3 + a(x, y) * 6 + (x / W) * math.tau)
        if ripple > 0.93:
            return "#4f8c48"
        if ripple > 0.8:
            return "#3a7840"
        return pick(pal, 0.15 + a(x, y) * 0.45 + b(x, y) * 0.35)

    return paint(f)


def bog_glow_pool():
    # A bubbling pool lit from inside by something strange: bright greens with pale
    # rings where bubbles have just popped.
    pal = ["#23702c", "#2f8a36", "#3fa240", "#55b84a", "#74cc58"]
    a, b = noise(4, 2, 1811), noise(8, 4, 1812)
    rings = [(9, 7, 5.0), (40, 20, 6.5), (25, 26, 3.5), (55, 6, 4.0)]

    def f(x, y):
        for cx, cy, r in rings:
            dx = min(abs(x - cx), W - abs(x - cx))
            dy = min(abs(y - cy), H - abs(y - cy))
            if abs(math.hypot(dx, dy) - r) < 0.6:
                return "#b8f08a"
        return pick(pal, 0.2 + a(x, y) * 0.5 + b(x, y) * 0.3)

    return paint(f)


def bog_mud():
    pal = ["#1f2a14", "#2a3618", "#36441e", "#445424", "#53642c"]
    a, b = noise(4, 2, 1821), noise(16, 8, 1822)

    def f(x, y):
        return pick(pal, 0.1 + a(x, y) * 0.6 + b(x, y) * 0.3)

    return paint(f)


def bog_bank():
    # Wet swamp ground: rich, soft moss with a few fallen leaves.
    pal = ["#2c5420", "#336024", "#3a6c28", "#42782c", "#4c8432"]
    a, b = noise(4, 2, 1831), noise(16, 8, 1832)
    leaf = speckle(1834, 10)

    def f(x, y):
        if (x, y) in leaf:
            return "#7fae44"
        return pick(pal, 0.1 + a(x, y) * 0.5 + b(x, y) * 0.4)

    return paint(f)


def bog_moss_ground():
    # Mossy ground beside the road: lighter, trodden, with roots showing.
    pal = ["#3a5a22", "#4a6e28", "#5a8230", "#6c9438", "#82a646"]
    a, b = noise(4, 2, 1841), noise(16, 8, 1842)
    root = noise(8, 2, 1843)

    def f(x, y):
        if abs(root(x, y) - 0.5) < 0.012:
            return "#5a4a2a"
        return pick(pal, 0.1 + a(x, y) * 0.55 + b(x, y) * 0.35)

    return paint(f)


def bog_root():
    # Gnarled root and old timber: dark brown, deeply grooved, streaked with moss.
    pal = ["#2c1e14", "#3a281a", "#4a3420", "#5c4228", "#6e5232"]
    a, b = noise(16, 2, 1851), noise(4, 4, 1852)

    def f(x, y):
        groove = math.sin(x * 1.1 + a(x, y) * 7)
        if b(x, y) > 0.8:
            return pick(["#33502a", "#3e5e2e"], a(x, y))
        return pick(pal, 0.45 + groove * 0.3 + a(x, y) * 0.2)

    return paint(f)


def bog_boards():
    # Weathered boardwalk planks across the road, moss creeping in from the edges, nails.
    pal = ["#5a3c20", "#6e4a28", "#835a31", "#976b3a", "#ab7d44"]
    a, b = noise(2, 8, 1861), noise(8, 16, 1862)
    m = noise(4, 2, 1863)

    def f(x, y):
        board = y // 8
        yy = y % 8
        if yy == 7:
            return "#1d140c"
        if yy == 0:
            return "#c0905a"
        if m(x, y) > 0.86 and yy in (1, 2, 3):
            return pick(["#4f6e2a", "#5a7a30"], b(x, y))  # a little moss in the grain
        if (x + board * 19) % 32 in (2, 29) and yy in (2, 5):
            return "#2a2a28"
        grain = 0.5 + 0.5 * math.sin(x * 0.6 + board * 1.7 + a(x, y) * 5)
        return pick(pal, 0.12 + grain * 0.45 + b(x, y) * 0.35)

    return paint(f)


def bog_rail():
    # A wooden rail bound with rope every so often.
    pal = ["#5a3c20", "#6e4a28", "#835a31", "#976b3a"]
    a = noise(8, 2, 1871)

    def f(x, y):
        if x % 32 in range(12, 20):
            k = (x + y) % 3
            return ["#c9a86a", "#a8874c", "#7a5f34"][k]  # rope
        if y in (0, 31):
            return "#2a1c10"
        grain = 0.5 + 0.5 * math.sin(y * 0.9 + a(x, y) * 6)
        return pick(pal, 0.15 + grain * 0.5 + a(x, y) * 0.3)

    return paint(f)


def bog_paving():
    # The old road: big worn flagstones, bright moss in every joint, a few cracks.
    pal = ["#6b7360", "#7b8470", "#8c947e", "#9ca48c", "#aeb49a"]
    a, b = noise(4, 2, 1881), noise(16, 8, 1882)
    crack = noise(8, 4, 1883)

    def f(x, y):
        row = y // 16
        bx = (x + (row % 2) * 10) % 21
        by = y % 16
        if bx == 0 or by == 0:
            return pick(["#3f7a2a", "#4e8e30", "#5fa238"], b(x, y))
        if abs(crack(x, y) - 0.5) < 0.02:
            return "#3e4434"
        if a(x, y) > 0.74:
            return pick(["#5e8e3a", "#6ea242"], b(x, y))
        return pick(pal, 0.15 + a(x, y) * 0.5 + b(x, y) * 0.35 + (0.15 if bx == 1 or by == 1 else 0))

    return paint(f)


def bog_stone():
    # The pyramid's masonry: huge green-grey blocks, moss pouring over them.
    pal = ["#6c765c", "#7c8768", "#8e9876", "#a0a986", "#b2ba96"]
    a, b, c = noise(4, 2, 1891), noise(16, 8, 1892), noise(8, 4, 1893)

    def f(x, y):
        row = y // 16
        bx, by = (x + (16 if row % 2 else 0)) % 32, y % 16
        moss = c(x, y) + (1 - y / H) * 0.25
        if moss > 0.78:
            return pick(["#356a24", "#437e2a", "#539232", "#65a63a"], (moss - 0.78) * 3 + b(x, y) * 0.3)
        if bx < 1 or by < 1:
            return pick(["#2a3424", "#3a5a28"], a(x, y))
        return pick(pal, 0.15 + a(x, y) * 0.45 + b(x, y) * 0.3 + (0.15 if by == 1 else 0))

    return paint(f)


def bog_carved():
    # Carved temple panels: skull-like masks, step frets and eye glyphs, mossy.
    pal = ["#5c6550", "#6d775e", "#80896e", "#929a7e"]
    a = noise(8, 4, 1901)

    def f(x, y):
        cx, cy = x % 16, y % 16
        cell = (x // 16 + (y // 16)) % 3
        dx, dy = cx - 7.5, cy - 7.5
        if cx < 1 or cy < 1:
            return "#2e3628"
        if cell == 0:  # a mask: two eyes and a toothy mouth
            carved = (abs(abs(dx) - 3) < 1.6 and -4 < dy < -1) or (2 < dy < 5 and abs(dx) < 5 and cx % 2 == 0)
        elif cell == 1:  # a step fret
            carved = (cy - 3) == (cx // 3) * 2 or (cy - 4) == (cx // 3) * 2
        else:  # a ringed eye
            r = math.hypot(dx, dy)
            carved = 4.5 < r < 6 or r < 1.8
        if carved:
            return "#333b2c"
        if a(x, y) > 0.78:
            return "#4a8030"
        return pick(pal, 0.25 + a(x, y) * 0.6)

    return paint(f)


def bog_dark_stone():
    # Inside the pyramid: dark, damp stone, glistening, with moss in the joints.
    pal = ["#262a20", "#30352a", "#3c4234", "#4a5040", "#575e4a"]
    a, b = noise(8, 4, 1911), noise(16, 8, 1912)
    wet = speckle(1913, 14)

    def f(x, y):
        if (x, y) in wet:
            return "#8a9a80"
        row = y // 16
        bx, by = (x + (16 if row % 2 else 0)) % 32, y % 16
        if bx < 1 or by < 1:
            return "#2e4a22" if b(x, y) > 0.5 else "#181c14"
        return pick(pal, 0.15 + a(x, y) * 0.55 + b(x, y) * 0.3)

    return paint(f)


def bog_canopy():
    # The swamp canopy: deep, saturated greens with sunlit clumps.
    pal = ["#183e16", "#21541c", "#2d6c22", "#3b862a", "#4f9e32", "#6ab43e"]
    a, b = noise(8, 4, 1921), noise(16, 8, 1922)

    def f(x, y):
        clump = 0.5 + 0.5 * math.sin(x * 0.9 + 2.4 * math.sin(y * 0.55))
        return pick(pal, 0.05 + a(x, y) * 0.45 + b(x, y) * 0.25 + clump * 0.25)

    return paint(f)


def bog_moss_hang():
    # Hanging moss: grey-green strands.
    pal = ["#4a5a3a", "#5c6e46", "#708252", "#86985e", "#9cae6c"]
    a = noise(16, 2, 1931)

    def f(x, y):
        strand = math.sin(x * 1.7 + a(x, y) * 4)
        return pick(pal, 0.4 + strand * 0.35 + a(x, y) * 0.2)

    return paint(f)


def cobweb():
    a = noise(8, 4, 1941)

    def f(x, y):
        return pick(["#cfd6cc", "#dfe4da", "#eef1ea", "#ffffff"], a(x, y))

    return paint(f)


def light_shaft():
    # A warm haze for shafts of light through the canopy (V runs down the shaft).
    a = noise(8, 2, 1951)

    def f(x, y):
        return pick(["#ffd27a", "#ffdf96", "#ffe9b4", "#fff4d6"], 0.3 + a(x, y) * 0.6)

    return paint(f)


def bog_mist():
    a, b = noise(4, 2, 1961), noise(8, 4, 1962)

    def f(x, y):
        return pick(["#a9cf8c", "#bedca2", "#d2e8bc", "#e6f2d8"], a(x, y) * 0.6 + b(x, y) * 0.5)

    return paint(f)


def bog_bone():
    # Ancient bone, stained green-brown by the swamp, mossy in the hollows.
    pal = ["#a49a78", "#b8ae8a", "#cbc29e", "#dcd4b2", "#ebe5c8"]
    a, b, c = noise(4, 2, 1971), noise(16, 8, 1972), noise(8, 4, 1973)

    def f(x, y):
        if c(x, y) > 0.72:
            return pick(["#5e7a3a", "#6e8c42", "#80a04c"], b(x, y))
        if abs(a(x, y) - 0.5) < 0.02:
            return "#6e6448"
        stain = 0.3 if c(x, y) > 0.6 else 0
        return pick(pal, 0.2 + a(x, y) * 0.45 + b(x, y) * 0.35 - stain)

    return paint(f)


def bog_eye():
    # Eerie green light in the carved eyes.
    a = noise(4, 2, 1981)

    def f(x, y):
        r = math.hypot(x % 16 - 7.5, y % 16 - 7.5)
        if r < 2.5:
            return "#f2ffd0"
        return pick(["#5ee05a", "#7aee6a", "#9ef884", "#c8ffa8"], 0.2 + a(x, y) * 0.5 + max(0, 6 - r) * 0.08)

    return paint(f)


def croc_skin():
    pal = ["#26321c", "#2f3e22", "#3a4c28", "#465a2e", "#566c36"]
    a = noise(8, 4, 1991)

    def f(x, y):
        scute = (x % 6 == 0) or (y % 5 == 0)
        return pick(pal, 0.15 + a(x, y) * 0.6 - (0.2 if scute else 0))

    return paint(f)


# ------------------------------------------------------------------ Ember Peak (the volcanic apocalypse)


def basalt_road():
    # A dark volcanic road: charcoal grit, ash-grey dust, the odd glowing cinder.
    pal = ["#3a302c", "#463a34", "#52443c", "#5e4e44", "#6a584c"]
    a, b = noise(4, 2, 2001), noise(16, 8, 2002)
    cinder = speckle(2003, 9)

    def f(x, y):
        if (x, y) in cinder:
            return "#ff8a2a"
        rut = 0.1 if x % 32 in (8, 9, 23, 24) else 0
        return pick(pal, 0.2 + a(x, y) * 0.45 + b(x, y) * 0.35 - rut)

    return paint(f)


def scorched_ground():
    # Black-brown burnt earth with ash and embers.
    pal = ["#1c1412", "#261a16", "#30201a", "#3a2820", "#463026"]
    a, b = noise(4, 2, 2011), noise(16, 8, 2012)
    ember = speckle(2013, 12)
    ash = speckle(2014, 14)

    def f(x, y):
        if (x, y) in ember:
            return "#ff6a1a"
        if (x, y) in ash:
            return "#8a7e78"
        return pick(pal, 0.15 + a(x, y) * 0.5 + b(x, y) * 0.35)

    return paint(f)


def ash_soil():
    # Ash-grey and rust-red volcanic soil on the mountain's flanks.
    pal = ["#2e1e1c", "#3a2622", "#462e28", "#523830", "#5e4238"]
    a, b, c = noise(4, 2, 2021), noise(16, 8, 2022), noise(8, 4, 2023)

    def f(x, y):
        if c(x, y) > 0.72:
            return pick(["#6e6460", "#7e7470", "#8e8480"], b(x, y))  # ash drifts
        return pick(pal, 0.1 + a(x, y) * 0.55 + b(x, y) * 0.35)

    return paint(f)


def magma_rock():
    # Cracked black rock with molten veins glowing through (it glows: only the veins
    # show, the rock stays dark).
    pal = ["#140e10", "#1c1416", "#241a1a", "#2e2020"]
    a, b = noise(8, 4, 2031), noise(4, 2, 2032)

    def f(x, y):
        v = abs(a(x, y) - 0.5)
        if v < 0.03:
            return "#ffd060"
        if v < 0.06:
            return "#ff7a1e"
        if v < 0.085:
            return "#a02a10"
        return pick(pal, b(x, y))

    return paint(f)


def obsidian():
    # Volcanic glass: near-black with violet depths and sharp pale glints.
    pal = ["#0e0b12", "#15111c", "#1d1626", "#261c32", "#30243e"]
    a, b = noise(4, 8, 2041), noise(16, 8, 2042)

    def f(x, y):
        facet = (x + 2 * y) % 23
        if facet == 0:
            return "#8a7aa8"
        if facet == 1:
            return "#4a3e60"
        return pick(pal, 0.15 + a(x, y) * 0.5 + b(x, y) * 0.35)

    return paint(f)


def obsidian_vein():
    # Obsidian split by glowing magma veins (glows: the black stays black).
    pal = ["#0e0b12", "#15111c", "#1d1626", "#241a2c"]
    a, b = noise(4, 8, 2051), noise(8, 4, 2052)

    def f(x, y):
        v = abs(a(x, y) - 0.5) + 0.08 * abs(math.sin(y * 0.4))
        if v < 0.035:
            return "#fff0a0"
        if v < 0.07:
            return "#ffa030"
        if v < 0.1:
            return "#d84a14"
        return pick(pal, b(x, y))

    return paint(f)


def obsidian_cliff():
    # The volcano's cliffs: layered dark basalt and obsidian bands, a few glints.
    pal = ["#1a1416", "#231a1c", "#2e2224", "#3a2c2c", "#463634"]
    a, b = noise(16, 2, 2061), noise(8, 4, 2062)

    def f(x, y):
        band = math.sin(y * 0.55 + a(x, y) * 4)
        if (x * 7 + y * 3) % 41 == 0:
            return "#7a6a90"
        return pick(pal, 0.4 + band * 0.3 + b(x, y) * 0.25)

    return paint(f)


def basalt_block():
    # Masonry of dark basalt blocks: the bridges and walls.
    pal = ["#2c2426", "#362c2e", "#423636", "#4e4040", "#5a4a48"]
    a, b = noise(8, 4, 2071), noise(16, 8, 2072)

    def f(x, y):
        row = y // 16
        bx, by = (x + (16 if row % 2 else 0)) % 32, y % 16
        if bx < 1 or by < 1:
            return "#140e0e"
        if by == 1:
            return "#6a5654"
        return pick(pal, 0.15 + a(x, y) * 0.5 + b(x, y) * 0.35)

    return paint(f)


def basalt_carved():
    # Carved basalt with glowing runes: the parapets and the gate.
    pal = ["#2c2426", "#362c2e", "#423636", "#4e4040"]
    a = noise(8, 4, 2081)

    def f(x, y):
        cx, cy = x % 16, y % 32
        if cx < 1 or cy < 1:
            return "#140e0e"
        dx, dy = cx - 7.5, cy - 15.5
        diamond = abs(abs(dx) + abs(dy) * 0.5 - 5) < 0.8
        if diamond:
            return "#ff8a2a"
        if abs(dx) < 0.8 and abs(dy) < 3:
            return "#ffb050"
        return pick(pal, 0.25 + a(x, y) * 0.6)

    return paint(f)


def cave_rock():
    # The caverns: deep red-brown rock, darker in the cracks.
    pal = ["#1e1012", "#2a1616", "#361c1a", "#44241e", "#522c24"]
    a, b = noise(8, 4, 2091), noise(16, 8, 2092)

    def f(x, y):
        if abs(a(x, y) - 0.5) < 0.02:
            return "#0e0606"
        return pick(pal, 0.15 + a(x, y) * 0.45 + b(x, y) * 0.4)

    return paint(f)


def lava_falls():
    # A molten waterfall: bright streaks running down it (V runs downhill).
    a = noise(16, 2, 2101)

    def f(x, y):
        streak = math.sin(x * 0.8 + a(x, y) * 6)
        return pick(["#b8280c", "#e8480e", "#ff7a18", "#ffaa30", "#ffd860", "#fff4a0"], 0.35 + streak * 0.35 + (y / H) * 0.1)

    return paint(f)


def crystal_red():
    a = noise(4, 8, 2111)

    def f(x, y):
        facet = (x + 2 * y) % 37
        if facet == 0:
            return "#fff0c0"
        return pick(["#a01810", "#d02c14", "#f05020", "#ff7a30", "#ffaa50"], 0.2 + a(x, y) * 0.7)

    return paint(f)


def crystal_purple():
    a = noise(4, 8, 2121)

    def f(x, y):
        facet = (x + 2 * y) % 37
        if facet == 0:
            return "#f4e0ff"
        return pick(["#3a1460", "#5a2090", "#7a34b8", "#9a50dc", "#c080ff"], 0.2 + a(x, y) * 0.7)

    return paint(f)


def charred_bark():
    pal = ["#120c0a", "#1a1210", "#241816", "#2e201c"]
    a, b = noise(16, 2, 2131), noise(8, 4, 2132)

    def f(x, y):
        if abs(b(x, y) - 0.5) < 0.025:
            return "#ff6a1a"  # embers in the cracks
        return pick(pal, 0.4 + math.sin(x * 1.2 + a(x, y) * 6) * 0.3 + a(x, y) * 0.2)

    return paint(f)


def burning_leaves():
    # Foliage on fire: dark scorched needles with flames licking through.
    a, b = noise(8, 4, 2141), noise(16, 8, 2142)

    def f(x, y):
        v = a(x, y) * 0.6 + b(x, y) * 0.4
        if v > 0.62:
            return pick(["#ff6a14", "#ff9a28", "#ffd050"], (v - 0.62) * 3)
        return pick(["#140c08", "#22140c", "#30200e", "#3e2a10"], v)

    return paint(f)


def ash_smoke():
    a, b = noise(4, 2, 2151), noise(8, 4, 2152)

    def f(x, y):
        return pick(["#2e2220", "#3e2e2a", "#504038", "#64524a", "#7a665c"], a(x, y) * 0.6 + b(x, y) * 0.5)

    return paint(f)


def fire_glow():
    # A fierce glow for eruption fire, crater light and the mouth's furnace.
    a = noise(4, 2, 2161)

    def f(x, y):
        return pick(["#ff4a10", "#ff7a18", "#ffa828", "#ffd050", "#fff090"], 0.2 + a(x, y) * 0.8)

    return paint(f)

# ------------------------------------------------------------------ Snowy Summit Pass


def summit_snow():
    # Fresh snow in bright sunshine: white with soft sky-blue hollows and sparkles.
    pal = ["#c6dcf4", "#d6e6f8", "#e4effb", "#f0f6fd", "#fbfdff"]
    a, b = noise(4, 2, 2201), noise(16, 8, 2202)
    sparkle = speckle(2203, 10)

    def f(x, y):
        if (x, y) in sparkle:
            return "#ffffff"
        return pick(pal, 0.3 + a(x, y) * 0.45 + b(x, y) * 0.3)

    return paint(f)


def summit_road():
    # A groomed snow track: corduroy lines from the groomer, two pressed wheel ruts.
    pal = ["#b4cbe6", "#c4d7ee", "#d3e2f4", "#e2ecf8", "#eef4fb"]
    a, b = noise(4, 2, 2211), noise(16, 8, 2212)

    def f(x, y):
        rut = x % 32 in (8, 9, 10, 22, 23, 24)
        cord = y % 3 == 0
        v = 0.4 + a(x, y) * 0.35 + b(x, y) * 0.25 - (0.3 if rut else 0) - (0.08 if cord else 0)
        return pick(pal, v)

    return paint(f)


def summit_stone_road():
    # Warm grey cobbles swept mostly clear of snow, snow lying in the joints.
    pave = ["#8f8c94", "#a29fa6", "#b4b1b6", "#c4c1c4"]
    a, b = noise(4, 2, 2221), noise(16, 8, 2222)

    def f(x, y):
        bx = (x + (4 if (y // 8) % 2 else 0)) % 8
        if bx == 0 or y % 8 == 0:
            return "#e8f0fa" if a(x, y) > 0.35 else "#6e6a74"
        if a(x, y) * 0.7 + b(x, y) * 0.5 > 0.92:
            return "#eef4fb"
        return pick(pave, 0.2 + a(x, y) * 0.5 + b(x, y) * 0.3)

    return paint(f)


def crystal_road():
    # The caves' floor: packed blue snow over ice, with glinting frost.
    pal = ["#7fa8e0", "#92b8e8", "#a6c8ef", "#bcd8f5"]
    a = noise(4, 2, 2231)
    glints = speckle(2232, 16)

    def f(x, y):
        if (x, y) in glints:
            return "#ffffff"
        rut = x % 32 in (8, 9, 22, 23)
        return pick(pal, 0.25 + a(x, y) * 0.6 - (0.2 if rut else 0))

    return paint(f)


def lake_ice():
    # Clear turquoise lake ice with white cracks and frozen bubbles.
    pal = ["#3cbcd2", "#52cadc", "#6cd6e4", "#8ae2ec", "#aaecf2"]
    a, b = noise(4, 2, 2241), noise(8, 4, 2242)
    bubbles = speckle(2243, 18)

    def f(x, y):
        if (x, y) in bubbles:
            return "#e8fbff"
        crack = abs(a(x, y) - 0.5) < 0.018 or abs(b(x, y) - 0.45) < 0.012
        if crack:
            return "#f4feff"
        return pick(pal, 0.15 + a(x, y) * 0.5 + b(x, y) * 0.35)

    return paint(f)


def glacier_ice():
    # Glacier walls: layered blue ice, brighter strata and dark-blue seams.
    pal = ["#4a8ad8", "#5c9ee2", "#72b2ea", "#8ec6f2", "#b0dcf8"]
    a = noise(8, 2, 2251)

    def f(x, y):
        band = math.sin((y + a(x, y) * 8) / H * math.tau * 3)
        if band > 0.93:
            return "#e6f6ff"
        if band < -0.95:
            return "#2e62b0"
        return pick(pal, 0.45 + band * 0.3 + a(x, y) * 0.2)

    return paint(f)


def crystal_blue():
    a = noise(4, 8, 2261)

    def f(x, y):
        if (x + 2 * y) % 37 == 0:
            return "#ffffff"
        return pick(["#1a4ab0", "#2a68d4", "#3c8cf0", "#62b4ff", "#a0dcff"], 0.2 + a(x, y) * 0.75)

    return paint(f)


def crystal_violet():
    a = noise(4, 8, 2271)

    def f(x, y):
        if (x + 2 * y) % 37 == 0:
            return "#fbeaff"
        return pick(["#4a1e9a", "#6630c4", "#8448e0", "#a46cf4", "#cca0ff"], 0.2 + a(x, y) * 0.75)

    return paint(f)


def chevron_sign():
    # Turn signs: white chevrons on bright blue.
    def f(x, y):
        u = (x + abs(y - 16)) % 16
        if u < 6:
            return "#ffffff"
        if y in (0, 31):
            return "#0e2e70"
        return "#1f64d8"

    return paint(f)


def summit_rock():
    # Sunny granite: warm light grey, speckled, with snow in the cracks.
    pal = ["#7f7a86", "#918c96", "#a5a0a8", "#b8b4ba", "#cac6ca"]
    a, b = noise(4, 2, 2281), noise(16, 8, 2282)
    dots = speckle(2283, 40)

    def f(x, y):
        if (x, y) in dots:
            return "#5e5966"
        if abs(a(x, y) - 0.5) < 0.02:
            return "#f2f6fc"
        return pick(pal, 0.15 + a(x, y) * 0.5 + b(x, y) * 0.35)

    return paint(f)


def summit_cliff():
    # Bright granite cliffs with snow lying thick on every ledge.
    pal = ["#9690a0", "#a8a3b0", "#bab6c0", "#ccc9d0"]
    a = noise(4, 2, 2291)

    def f(x, y):
        ledge = (y + int(a(x, y) * 6)) % 10
        if ledge < 3:
            return "#fafcff" if ledge < 2 else "#d8e6f6"
        return pick(pal, 0.2 + a(x, y) * 0.7)

    return paint(f)


def hot_spring():
    # Steaming geothermal water: vivid turquoise, paler where it wells up.
    pal = ["#0aa4b8", "#14b6c6", "#2ac8d4", "#52d8e0", "#8ce8ec"]
    a, b = noise(4, 2, 2301), noise(8, 4, 2302)
    foam = speckle(2303, 12)

    def f(x, y):
        if (x, y) in foam:
            return "#f0fdff"
        return pick(pal, 0.15 + a(x, y) * 0.5 + b(x, y) * 0.35)

    return paint(f)


def hot_pool():
    # A shallow hot pool on the terraces: bright aqua over cream sinter.
    a = noise(4, 2, 2311)

    def f(x, y):
        return pick(["#44d0d8", "#66dce0", "#8ae6e8", "#b0f0ee"], 0.2 + a(x, y) * 0.7)

    return paint(f)


def sinter():
    # Travertine: cream mineral crust with orange and rust streaks where the hot water
    # runs (the bright colours of a real hot spring's mats).
    pal = ["#e2d2b0", "#ecdcbc", "#f4e8cc", "#faf2de"]
    a, b = noise(8, 2, 2321), noise(16, 4, 2322)

    def f(x, y):
        streak = math.sin(x * 0.45 + a(x, y) * 7)
        if streak > 0.86:
            return pick(["#e07a2a", "#ee9a3a", "#f6b84e"], b(x, y))
        if streak > 0.74:
            return "#d8b26a"
        return pick(pal, 0.2 + a(x, y) * 0.5 + b(x, y) * 0.3)

    return paint(f)


def sinter_road():
    # A road worn into the terraces: pale cream stone, two ruts.
    pal = ["#cdbb98", "#d8c8a6", "#e2d4b6", "#ece0c6"]
    a, b = noise(4, 2, 2331), noise(16, 8, 2332)

    def f(x, y):
        rut = x % 32 in (8, 9, 10, 22, 23, 24)
        return pick(pal, 0.35 + a(x, y) * 0.4 + b(x, y) * 0.25 - (0.3 if rut else 0))

    return paint(f)


def sinter_rim():
    # The terraces' rims: orange and rust bands of mineral and microbe mats.
    a = noise(8, 2, 2341)

    def f(x, y):
        band = (y + int(a(x, y) * 5)) % 8
        return ["#f6e6c2", "#f0c070", "#e89440", "#d26a26", "#b8521e", "#e89440", "#f0c070", "#f6e6c2"][band]

    return paint(f)


def thaw_grass():
    # Thawed meadow: bright spring grass with the last patches of snow.
    a, b = noise(4, 2, 2351), noise(16, 8, 2352)
    flowers = speckle(2353, 8)

    def f(x, y):
        if (x, y) in flowers:
            return "#ffe86a" if (x + y) % 2 else "#ffffff"
        v = a(x, y) * 0.6 + b(x, y) * 0.4
        if v > 0.72:
            return pick(["#e6eef8", "#f6faff"], (v - 0.72) * 3)
        return pick(["#4c9a3c", "#5aac44", "#6cbc4e", "#84cc5a"], v * 1.3)

    return paint(f)


def forest_road():
    # A forest track: warm brown earth, damp from the thaw, with slush in the ruts.
    pal = ["#8a6a4a", "#9a7a56", "#ab8a64", "#bc9c72"]
    a, b = noise(4, 2, 2361), noise(16, 8, 2362)

    def f(x, y):
        rut = x % 32 in (8, 9, 10, 22, 23, 24)
        if rut and a(x, y) > 0.5:
            return "#d6e2ee"
        return pick(pal, 0.3 + a(x, y) * 0.4 + b(x, y) * 0.3 - (0.2 if rut else 0))

    return paint(f)


def giant_bark():
    # Colossal red-brown bark in deep vertical furrows (V runs up the trunk).
    pal = ["#5a2c1c", "#6e3822", "#82462a", "#985634", "#ac6a42"]
    a = noise(16, 2, 2371)

    def f(x, y):
        furrow = math.sin(x * 0.9 + a(x, y) * 5)
        if furrow < -0.8:
            return "#3a1a10"
        return pick(pal, 0.45 + furrow * 0.35 + a(x, y) * 0.15)

    return paint(f)


def heartwood():
    # Inside the great tree: golden heartwood with grain lines.
    pal = ["#b8823e", "#c8944a", "#d8a65a", "#e6b86c", "#f0ca82"]
    a = noise(8, 2, 2381)

    def f(x, y):
        grain = math.sin(y * 0.8 + a(x, y) * 9)
        if grain > 0.9:
            return "#8e5a26"
        return pick(pal, 0.4 + grain * 0.3 + a(x, y) * 0.2)

    return paint(f)


def plank_road():
    # Sunny wooden planks across the road, nail heads and gaps between boards.
    pal = ["#a8743e", "#b88248", "#c69254", "#d4a262"]
    a = noise(16, 2, 2391)

    def f(x, y):
        board = y // 4
        if y % 4 == 3:
            return "#5e3c1e"
        if x % 16 in (2, 13) and y % 4 == 1:
            return "#4a4a52"
        return pick(pal, 0.2 + a(x + board * 7, y) * 0.6 + ((board * 37) % 5) * 0.04)

    return paint(f)


def rope_rail():
    # A rail of rope between wooden posts, with snow on the top rope.
    a = noise(8, 2, 2401)

    def f(x, y):
        if x % 16 < 3:
            return pick(["#7a4e26", "#8e5e30"], a(x, y))
        if y in (2, 3, 14, 15, 26, 27):
            return "#f2f6fc" if y == 2 else pick(["#c8a466", "#d8b878"], a(x, y))
        if (x + y) % 6 == 0 and 4 < y < 26:
            return "#b8945a"
        return pick(["#6e4a28", "#7e5832"], a(x, y)) if y > 27 else "#a87e46"

    return paint(f)


def bunting():
    # Prayer-flag colours, one per flag (the flags are triangles cut in the mesh; U runs
    # along the line, a flag every 1/8 of the tile).
    cols = ["#e84a3a", "#f8c838", "#4cbc5a", "#3a8ae8", "#f4f4f4", "#f08a2a", "#c04ab8", "#3ac0d0"]

    def f(x, y):
        if x % 8 == 7 or y in (0, 31):
            return "#8a6a48"
        return cols[(x // 8) % 8]

    return paint(f)


def pine_bright():
    # Sunny conifer needles with snow lying on the boughs.
    a = noise(8, 4, 2421)

    def f(x, y):
        if y % 8 < 2 and a(x, y) > 0.3:
            return "#ffffff" if y % 8 == 0 else "#dce8f6"
        return pick(["#1e6a3e", "#287a48", "#348c52", "#44a060"], a(x, y))

    return paint(f)


def leaf_bright():
    # A thawed canopy: fresh bright greens with sunlit gold.
    a, b = noise(8, 4, 2431), noise(16, 8, 2432)

    def f(x, y):
        v = a(x, y) * 0.6 + b(x, y) * 0.4
        if v > 0.78:
            return "#d8f080"
        return pick(["#2e7a2c", "#3e8e34", "#52a23c", "#6cb648", "#88c856"], v)

    return paint(f)


def ship_hull():
    # An old ship's hull: dark tarred planks, frost on the seams.
    pal = ["#3a2a22", "#46322a", "#523c30", "#5e4636"]
    a = noise(16, 2, 2441)

    def f(x, y):
        if y % 6 == 5:
            return "#c8d8e8" if a(x, y) > 0.55 else "#22160e"
        if x % 24 == 0 and y % 6 == 2:
            return "#8a8a90"
        return pick(pal, 0.2 + a(x, y) * 0.7)

    return paint(f)


def sail_cloth():
    # A patched, weathered sail.
    a = noise(4, 2, 2451)

    def f(x, y):
        if x % 21 == 0 or y % 15 == 0:
            return "#b8ab90"
        if 30 < x < 46 and 10 < y < 22:
            return "#c8b48a"
        return pick(["#d6cbb0", "#e2d8c0", "#ece4d0"], a(x, y))

    return paint(f)


def mammoth_bone():
    pal = ["#cdbf9e", "#dccfae", "#e8dcbe", "#f2e8d0"]
    a, b = noise(4, 8, 2461), noise(16, 4, 2462)

    def f(x, y):
        if abs(b(x, y) - 0.5) < 0.02:
            return "#9e8e6e"
        return pick(pal, 0.2 + a(x, y) * 0.5 + b(x, y) * 0.3)

    return paint(f)


def frost_stone():
    # The old ruins: pale blue-grey blocks with snow in the joints.
    pal = ["#9aa4b8", "#aab4c6", "#bac4d2", "#cad2de"]
    a = noise(4, 2, 2471)

    def f(x, y):
        joint = x % 16 == 0 or (y + (8 if (x // 16) % 2 else 0)) % 16 == 0
        if joint:
            return "#f2f6fc" if y % 16 == 0 else "#6c7488"
        return pick(pal, 0.2 + a(x, y) * 0.7)

    return paint(f)


def glow_moss():
    # Glowing fungi and moss inside the great tree: warm gold and green.
    a, b = noise(8, 4, 2481), noise(16, 8, 2482)

    def f(x, y):
        v = a(x, y) * 0.6 + b(x, y) * 0.4
        if v > 0.7:
            return pick(["#fff0a0", "#ffe070"], v)
        return pick(["#b8d84a", "#d0e85a", "#e8d060", "#f0c050"], v)

    return paint(f)


def steam_mist():
    a, b = noise(4, 2, 2491), noise(8, 4, 2492)

    def f(x, y):
        return pick(["#dceef6", "#e8f4fa", "#f2f9fc", "#ffffff"], a(x, y) * 0.6 + b(x, y) * 0.5)

    return paint(f)


def icefall_blue():
    # Frozen waterfalls: streaky blue-white ice (V runs down the fall).
    pal = ["#62aee8", "#80c4f0", "#a2d8f6", "#c6eafb", "#eef9ff"]
    a = noise(8, 2, 2501)

    def f(x, y):
        streak = math.sin(x * 1.7 + a(x, y) * 6) * 0.5 + 0.5
        return pick(pal, streak * 0.7 + a(x, y) * 0.3)

    return paint(f)


def warm_falls():
    # A hot waterfall from the springs: bright aqua streaks (V runs downhill).
    pal = ["#2cc0cc", "#54d2da", "#86e2e6", "#bcf2f2", "#ffffff"]
    a = noise(8, 2, 2511)

    def f(x, y):
        streak = math.sin(x * 1.9 + a(x, y) * 6) * 0.5 + 0.5
        return pick(pal, streak * 0.7 + a(x, y) * 0.4)

    return paint(f)


def mammoth_fur():
    # Shaggy russet-brown fur (for the mammoth model's reference swatch).
    a = noise(16, 4, 2521)

    def f(x, y):
        return pick(["#5a3420", "#6e4228", "#844e30", "#9a5e3a"], 0.3 + math.sin(x * 1.3 + a(x, y) * 5) * 0.3 + a(x, y) * 0.3)

    return paint(f)

# ------------------------------------------------------------------ Hearthglow Hollow


def hearth_cobble():
    # Village cobbles at dusk: lavender-grey setts, snow lying in the joints.
    pave = ["#8a8298", "#9a92a8", "#aaa2b6", "#bab3c4"]
    a, b = noise(4, 2, 2601), noise(16, 8, 2602)

    def f(x, y):
        row = y // 6
        bx = (x + (5 if row % 2 else 0)) % 10
        if bx == 0 or y % 6 == 0:
            return "#eef2fc" if a(x, y) > 0.3 else "#6a6278"
        if a(x, y) * 0.7 + b(x, y) * 0.5 > 0.95:
            return "#f4f6ff"
        return pick(pave, 0.2 + a(x, y) * 0.5 + b(x, y) * 0.3)

    return paint(f)


def icy_cobble():
    # Cobbles glazed with ice: glossy blue, the setts showing through.
    pal = ["#7a96d0", "#8ea8dc", "#a4bae6", "#bcd0f0"]
    a = noise(4, 2, 2611)
    glints = speckle(2612, 18)

    def f(x, y):
        if (x, y) in glints:
            return "#ffffff"
        row = y // 6
        if (x + (5 if row % 2 else 0)) % 10 == 0 or y % 6 == 0:
            return "#6a80b8"
        return pick(pal, 0.2 + a(x, y) * 0.7)

    return paint(f)


def hearth_stone():
    # Warm grey stone blocks for the bridges, walls and the bell tower.
    pal = ["#857a78", "#958a86", "#a59a94", "#b5aaa2"]
    a = noise(4, 2, 2621)

    def f(x, y):
        joint = x % 16 == 0 or (y + (8 if (x // 16) % 2 else 0)) % 8 == 0
        if joint:
            return "#f0f2fa" if y % 8 == 0 and a(x, y) > 0.4 else "#5a5058"
        return pick(pal, 0.2 + a(x, y) * 0.7)

    return paint(f)


def river_ice():
    # The frozen river: deep blue-violet ice with white cracks and frozen bubbles.
    pal = ["#4a6ac8", "#5a7ed4", "#6c92de", "#84a8e8", "#a4c2f2"]
    a, b = noise(4, 2, 2631), noise(8, 4, 2632)
    bubbles = speckle(2633, 16)

    def f(x, y):
        if (x, y) in bubbles:
            return "#e8f2ff"
        if abs(a(x, y) - 0.5) < 0.018 or abs(b(x, y) - 0.45) < 0.012:
            return "#f4f8ff"
        return pick(pal, 0.15 + a(x, y) * 0.5 + b(x, y) * 0.35)

    return paint(f)


def river_ice_road():
    # The shortcut across the river ice: scraped tracks and snow dust.
    pal = ["#7896d8", "#8aa6e0", "#9eb6e8", "#c4d4f4"]
    a = noise(4, 2, 2641)

    def f(x, y):
        scrape = (x + y // 4) % 9 == 0
        if scrape:
            return "#e4ecfc"
        return pick(pal, 0.2 + a(x, y) * 0.7)

    return paint(f)


def timber_rail():
    # A wooden fence: posts and two rails, snow on top, a string of little bulbs.
    a = noise(8, 2, 2651)

    def f(x, y):
        if y < 3:
            return "#f4f6ff"
        if x % 16 < 3:
            return pick(["#6a4022", "#7a4c2a"], a(x, y))
        if 6 <= y <= 10 or 20 <= y <= 24:
            return pick(["#8a5832", "#9a6438"], a(x, y))
        if y == 4 and x % 8 == 4:
            return ["#ffd060", "#ff5050", "#60e070", "#60a0ff"][(x // 8) % 4]
        return "#3a2a3a"

    return paint(f)


def timber_beam():
    pal = ["#4e3424", "#5a3c2a", "#664430", "#724c36"]
    a = noise(16, 2, 2661)

    def f(x, y):
        if y % 16 == 0:
            return "#2e1e16"
        return pick(pal, 0.4 + math.sin(y * 0.9 + a(x, y) * 6) * 0.25 + a(x, y) * 0.2)

    return paint(f)


def cabin_wall():
    # Log-cabin walls: warm brown logs with dark gaps.
    pal = ["#8a5634", "#9a643c", "#a87044", "#b67c4c"]
    a = noise(16, 4, 2671)

    def f(x, y):
        if y % 8 in (0, 7):
            return "#4a2a1a"
        return pick(pal, 0.3 + a(x, y) * 0.5 + (y % 8 in (3, 4)) * 0.15)

    return paint(f)


def cabin_plaster():
    # Alpine half-timbering: cream plaster between dark beams.
    a = noise(4, 2, 2681)

    def f(x, y):
        if x % 32 < 3 or y % 32 < 3 or abs((x % 32) - (y % 32)) < 2:
            return "#5a3624"
        return pick(["#e2d2b8", "#ead9c0", "#f2e2ca"], a(x, y))

    return paint(f)


def window_warm():
    # A glowing window: golden light behind a cross of glazing bars.
    a = noise(4, 2, 2691)

    def f(x, y):
        if x % 32 in (0, 1, 15, 16) or y % 16 in (0, 1, 8):
            return "#6a3a1c"
        return pick(["#ffb848", "#ffc860", "#ffd878", "#ffe8a0"], 0.2 + a(x, y) * 0.8)

    return paint(f)


def brick():
    a = noise(4, 2, 2701)

    def f(x, y):
        if y % 4 == 0 or (x + (4 if (y // 4) % 2 else 0)) % 8 == 0:
            return "#d8d0dc"
        return pick(["#8a3a2e", "#9a4434", "#aa4e3a"], a(x, y))

    return paint(f)


def awning_red():
    def f(x, y):
        return "#d82a34" if (x // 8) % 2 == 0 else "#f6f0ea"

    return paint(f)


def awning_green():
    def f(x, y):
        return "#2a8a48" if (x // 8) % 2 == 0 else "#f6f0ea"

    return paint(f)


def candy_stripe():
    def f(x, y):
        return "#e0263a" if ((x + y) // 6) % 2 == 0 else "#fbf6f2"

    return paint(f)


def wrap(base, dark, ribbon, seed):
    a = noise(4, 2, seed)

    def f(x, y):
        if 28 <= x % 64 <= 35 or 13 <= y <= 18:
            return ribbon
        if (x // 4 + y // 4) % 5 == 0:
            return dark
        return pick([base, base, dark], a(x, y) * 0.9)

    return paint(f)


def wreath():
    # Holly: dark glossy leaves, red berries.
    a = noise(8, 4, 2711)
    berries = speckle(2712, 26)

    def f(x, y):
        if (x, y) in berries:
            return "#f02a2a"
        return pick(["#1a5a2c", "#226a34", "#2e7c40", "#3a8e4c"], a(x, y))

    return paint(f)


def xmas_lights():
    # A string of coloured bulbs (U runs along the string). The pattern scrolls along, so
    # the bulbs chase and twinkle: every other bulb is dimmer.
    cols = [("#ff3a3a", "#9a2020"), ("#ffd040", "#9a7a20"), ("#3aff6a", "#209a40"), ("#4a9aff", "#24509a"), ("#ff7aff", "#9a409a")]

    def f(x, y):
        k = x // 8
        u = x % 8
        if abs(u - 3.5) < 2.6 and 8 <= y <= 23:
            on, off = cols[k % 5]
            return on if k % 2 == 0 else off
        return "#2a2034"

    return paint(f)


def banner_tree():
    # A red banner with a golden tree.
    def f(x, y):
        cx = x % 32
        if cx < 2 or cx > 29:
            return "#f2c040"
        tree = y > 4 and abs(cx - 16) < (y - 4) * 0.45 and y < 26
        if tree or (y >= 26 and abs(cx - 16) < 2):
            return "#f6c848"
        return "#c0202c"

    return paint(f)


def gold_trim():
    a = noise(4, 2, 2721)

    def f(x, y):
        return pick(["#c8902a", "#e0aa38", "#f2c44a", "#fde070"], a(x, y))

    return paint(f)


def star_gold():
    a = noise(4, 2, 2731)

    def f(x, y):
        return pick(["#ffe060", "#fff090", "#fffbd0"], 0.3 + a(x, y) * 0.7)

    return paint(f)


def carrot():
    def f(x, y):
        return "#f08a2a" if y % 6 else "#c86a1a"

    return paint(f)


def pine_night():
    # Snow-laden pines (a deep blue-green under the twilight, heavy snow on the boughs).
    a = noise(8, 4, 2741)

    def f(x, y):
        if y % 8 < 3 and a(x, y) > 0.25:
            return "#ffffff" if y % 8 == 0 else "#e2e8fa"
        return pick(["#1a4a3a", "#205644", "#28624e", "#327058"], a(x, y))

    return paint(f)


THEMES = [
    {
        "id": "jungle_cascade",
        "name": "Jungle Cascade",
        "description": "Mossy stone, old masonry, leafy ground and soft green light, ringed by misty jungle hills",
        "environment": {
            "sky": "#8fcfe0",
            "fog": {"enabled": True, "color": "#a9d6c2", "near": 70, "far": 420},
            "sun": {"color": "#f6ffe0", "intensity": 2.0, "direction": [-0.4, 0.85, 0.3]},
            "ambient": {"sky": "#d6f2e2", "ground": "#2f5a2c", "intensity": 1.25},
            "skyDome": {
                "top": "#3f9fd6",
                "horizon": "#c6ead8",
                "bottom": "#a9d6c2",
                "sun": {"color": "#fffbe6", "size": 6, "glow": "#fff0a8", "elevation": 34},
                "clouds": {"count": 22, "color": "#ffffff", "shade": "#d4ece4", "seed": 9, "low": 14, "high": 30, "drift": 0.004},
                "hills": {"color": "#24502c", "far": "#8dbfa4", "height": 13, "seed": 4, "layers": 3},
            },
        },
    },
    {
        "id": "river_valley",
        "name": "River Valley",
        "description": "Sunny orange dirt roads, bright grass, blue water, palms and wooden bridges, under a sunny painted sky",
        "environment": {
            "sky": "#3aa2f2",
            "fog": {"enabled": True, "color": "#c6ebff", "near": 220, "far": 900},
            "sun": {"color": "#fff3d2", "intensity": 2.6, "direction": [-0.45, 0.6, -0.66]},
            "ambient": {"sky": "#e6f6ff", "ground": "#5d8a3a", "intensity": 1.25},
            "skyDome": {
                "top": "#1f7fe0",
                "horizon": "#c2eaff",
                "bottom": "#a8dcff",
                "sun": {"color": "#fff9dc", "size": 7, "glow": "#ffe27a", "elevation": 15},
                "clouds": {"count": 40, "color": "#ffffff", "shade": "#d2e8ff", "seed": 5, "low": 8, "high": 24, "drift": 0.006},
            },
        },
    },
    {
        "id": "fossil_swamp",
        "name": "Fossil Swamp",
        "description": "Misty green water, slick mud, old paving, giant bones and glowing caps",
        "environment": {
            "sky": "#7b86b4",
            "fog": {"enabled": True, "color": "#9aa8a4", "near": 70, "far": 420},
            "sun": {"color": "#ffe2b8", "intensity": 1.6, "direction": [-0.45, 0.6, 0.55]},
            "ambient": {"sky": "#c6c2e6", "ground": "#34482c", "intensity": 1.3},
        },
    },
]

THEMES.append(
    {
        "id": "volcano_dusk",
        "name": "Volcano Dusk",
        "description": "A glowing red-orange evening under a smoking volcano (uses the Ember Volcano textures)",
        "environment": {
            "sky": "#9a4f4a",
            "fog": {"enabled": True, "color": "#b0603e", "near": 150, "far": 680},
            "sun": {"color": "#ffcf98", "intensity": 2.1, "direction": [-0.35, 0.65, 0.65]},
            "ambient": {"sky": "#f0a07a", "ground": "#40201a", "intensity": 1.2},
        },
    }
)

THEMES.append(
    {
        "id": "beach_party",
        "name": "Beach Party",
        "description": "White-gold sand, a turquoise sea, palms, bright party colours and a high midday sun",
        "environment": {
            "sky": "#3fb0f5",
            "fog": {"enabled": True, "color": "#d2f1ff", "near": 260, "far": 1100},
            "sun": {"color": "#fff6dc", "intensity": 2.7, "direction": [-0.3, 0.85, -0.45]},
            "ambient": {"sky": "#eaf8ff", "ground": "#d8c08a", "intensity": 1.3},
            "skyDome": {
                "top": "#1d86ea",
                "horizon": "#c8f0ff",
                "bottom": "#a6e6f2",
                "sun": {"color": "#fffbe6", "size": 7, "glow": "#fff0a0", "elevation": 22},
                "clouds": {"count": 30, "color": "#ffffff", "shade": "#d6ecff", "seed": 12, "low": 6, "high": 22, "drift": 0.006},
                "hills": {"color": "#3f9a6a", "far": "#a9dcd8", "height": 4, "seed": 21, "layers": 2},
            },
        },
    }
)

THEMES.append(
    {
        "id": "frost_citadel",
        "name": "Frost Citadel",
        "description": "Moonlit snow and ice, blue-lavender fog and weathered stone ruins lit by golden firelight",
        "environment": {
            "sky": "#4b5596",
            "fog": {"enabled": True, "color": "#9a9fd6", "near": 150, "far": 980},
            "sun": {"color": "#c4ceff", "intensity": 1.9, "direction": [-0.35, 0.8, 0.48]},
            "ambient": {"sky": "#aab2f0", "ground": "#4a4472", "intensity": 1.45},
            "skyDome": {
                "top": "#1f2766",
                "horizon": "#a7a0d8",
                "bottom": "#8e93cc",
                "sun": {"color": "#f4f6ff", "size": 9, "glow": "#c9d2ff", "elevation": 24},
                "clouds": {"count": 26, "color": "#c9c6ec", "shade": "#7f80b8", "seed": 17, "low": 8, "high": 26, "drift": 0.003},
                "hills": {"color": "#6b6fa8", "far": "#a39fd4", "height": 17, "seed": 31, "layers": 3},
            },
        },
    }
)

THEMES.append(
    {
        "id": "bonebog_swamp",
        "name": "Bonebog Swamp",
        "description": "A living swamp at golden hour: vivid murky greens, mossy stone, old timber, ancient bone and warm torchlight under a vast canopy",
        "environment": {
            "sky": "#d9b46a",
            "fog": {"enabled": True, "color": "#9fa866", "near": 70, "far": 600},
            "sun": {"color": "#ffd59a", "intensity": 2.4, "direction": [-0.55, 0.62, 0.55]},
            "ambient": {"sky": "#e2ecb4", "ground": "#35502a", "intensity": 1.3},
            "skyDome": {
                "top": "#5f9cc0",
                "horizon": "#ffd48a",
                "bottom": "#9fbc6a",
                "sun": {"color": "#fff1c8", "size": 9, "glow": "#ffc866", "elevation": 14},
                "clouds": {"count": 20, "color": "#fff0d0", "shade": "#e0b080", "seed": 23, "low": 10, "high": 26, "drift": 0.003},
                "hills": {"color": "#1f4a1c", "far": "#6e9a52", "height": 24, "seed": 41, "layers": 3},
            },
        },
    }
)

THEMES.append(
    {
        "id": "volcanic_apocalypse",
        "name": "Volcanic Apocalypse",
        "description": "A smoke-filtered blood-red sunset over erupting volcanoes: black obsidian, charred ground, molten lava and firelight",
        "environment": {
            "sky": "#7a2618",
            "fog": {"enabled": True, "color": "#6a2a1a", "near": 230, "far": 1500},
            "sun": {"color": "#ffb070", "intensity": 2.9, "direction": [0.55, 0.42, -0.72]},
            "ambient": {"sky": "#ff9a78", "ground": "#2e1410", "intensity": 1.3},
            "skyDome": {
                "top": "#2a0c0e",
                "horizon": "#ff7a32",
                "bottom": "#8a3220",
                "sun": {"color": "#ffd890", "size": 11, "glow": "#ff8a3a", "elevation": 7},
                "clouds": {"count": 46, "color": "#5a2c26", "shade": "#1e0e0e", "seed": 37, "low": 6, "high": 30, "drift": 0.004},
                "hills": {"color": "#200c0c", "far": "#6a2a1e", "height": 9, "seed": 53, "layers": 2},
            },
        },
    }
)

THEMES.append(
    {
        "id": "summit_pass",
        "name": "Summit Pass",
        "description": "A brilliant sunny day in the snowy mountains: dazzling snow, turquoise ice, steaming hot springs, glowing ice caves and giant trees",
        "environment": {
            "sky": "#5ab8ff",
            "fog": {"enabled": True, "color": "#d4eeff", "near": 260, "far": 1400},
            "sun": {"color": "#fff4dc", "intensity": 2.7, "direction": [0.42, 0.74, 0.52]},
            "ambient": {"sky": "#eaf6ff", "ground": "#8ea2bc", "intensity": 1.35},
            "skyDome": {
                "top": "#1c7ee8",
                "horizon": "#c8ecff",
                "bottom": "#e4f4ff",
                "sun": {"color": "#fffbe6", "size": 8, "glow": "#fff0b0", "elevation": 32},
                "clouds": {"count": 30, "color": "#ffffff", "shade": "#d2e6fa", "seed": 61, "low": 8, "high": 26, "drift": 0.005},
                "hills": {"color": "#9eb8de", "far": "#d2e4f8", "height": 16, "seed": 67, "layers": 3},
            },
        },
    }
)

THEMES.append(
    {
        "id": "hearthglow",
        "name": "Hearthglow",
        "description": "A Christmas village on a snowy evening: a purple and blue twilight full of stars, warm golden windows and lanterns, coloured lights, deep snow and frozen water",
        "environment": {
            "sky": "#2a2370",
            "fog": {"enabled": True, "color": "#5a4c9a", "near": 220, "far": 1250},
            "sun": {"color": "#c8c4ff", "intensity": 1.9, "direction": [-0.38, 0.72, 0.58]},
            "ambient": {"sky": "#a49ae8", "ground": "#584a88", "intensity": 1.6},
            "skyDome": {
                "top": "#120c3a",
                "horizon": "#c47ac8",
                "bottom": "#6a58a8",
                "sun": {"color": "#f6f4ff", "size": 5, "glow": "#b8b0ff", "elevation": 34},
                "clouds": {"count": 18, "color": "#d49ad8", "shade": "#6a5aa8", "seed": 71, "low": 4, "high": 16, "drift": 0.003},
                "hills": {"color": "#3a3478", "far": "#8a74c0", "height": 15, "seed": 73, "layers": 3},
                "stars": {"count": 600, "color": "#ffffff", "seed": 79, "low": 14},
            },
        },
    }
)

# ------------------------------------------------------------------ Aurora Rift


def rift_road():
    # The glacier road: smooth, polished blue ice over packed snow, a few long glossy
    # streaks where the lanterns and the aurora catch it. Calm: it fills the screen.
    pal = ["#5d72b0", "#6579b6", "#6d82bc", "#778cc4", "#8296ca"]
    a, b = noise(2, 1, 3101), noise(8, 2, 3102)
    glints = speckle(3103, 6)

    def f(x, y):
        if (x, y) in glints:
            return "#dfeaff"
        streak = abs(math.sin(y * 0.39 + a(x, y) * 2.0))
        if streak > 0.985 and b(x, y) > 0.45:
            return "#a8bce8"
        return pick(pal, 0.15 + a(x, y) * 0.5 + b(x, y) * 0.35)

    return paint(f)


def rift_ice_road():
    # Clear ice to drive on: deep, glassy blue with soft pale streaks; slippery.
    pal = ["#3e66b8", "#456ec0", "#4c78c8", "#5682d0", "#628ed6"]
    a, b = noise(2, 1, 3111), noise(6, 2, 3112)
    glints = speckle(3113, 5)

    def f(x, y):
        if (x, y) in glints:
            return "#d8ecff"
        if abs(b(x, y) - 0.5) < 0.012:
            return "#8eb6ea"
        return pick(pal, 0.15 + a(x, y) * 0.5 + b(x, y) * 0.35)

    return paint(f)

def mirror_ice():
    # Mirror Lake's ice: dark, clear teal (the crystals' reflections show through it),
    # faint frozen ripples and a few bright glints.
    pal = ["#0e3a5a", "#124a6c", "#175a7c", "#1e6c8c", "#2a82a0"]
    a, b = noise(4, 2, 3121), noise(12, 6, 3122)
    glints = speckle(3123, 8)

    def f(x, y):
        if (x, y) in glints:
            return "#bff6ff"
        rip = math.sin(y * 0.6 + a(x, y) * 5) * 0.5 + 0.5
        return pick(pal, 0.1 + a(x, y) * 0.45 + rip * 0.2 + b(x, y) * 0.2)

    return paint(f)


def thin_ice():
    # Thin ice over dark water: pale, crazed with white cracks.
    pal = ["#3c7aa4", "#4c8cb4", "#62a2c4", "#7cb8d4"]
    a, b, c = noise(4, 2, 3131), noise(8, 4, 3132), noise(5, 3, 3133)

    def f(x, y):
        if abs(a(x, y) - 0.5) < 0.03 or abs(b(x, y) - 0.42) < 0.02 or abs(c(x, y) - 0.6) < 0.018:
            return "#f2faff"
        return pick(pal, 0.2 + a(x, y) * 0.4 + b(x, y) * 0.4)

    return paint(f)


def rift_snow():
    # Night snow: blue-lavender, catching the aurora.
    pal = ["#9aa6d8", "#a8b4e2", "#b8c2ea", "#c8d2f2", "#dae2f8"]
    a, b = noise(4, 2, 3141), noise(16, 8, 3142)
    sparkle = speckle(3143, 10)

    def f(x, y):
        if (x, y) in sparkle:
            return "#ffffff"
        return pick(pal, 0.15 + a(x, y) * 0.6 + b(x, y) * 0.3)

    return paint(f)


def rift_rock():
    # Dark indigo rock, snow caught in its cracks.
    pal = ["#1e2148", "#262a58", "#2f3468", "#3a4078", "#4a5090"]
    a, b = noise(6, 3, 3151), noise(16, 8, 3152)

    def f(x, y):
        v = a(x, y) * 0.65 + b(x, y) * 0.45
        if v > 0.92 or (y % 11 == 0 and a(x, y) > 0.55):
            return "#c8d2f2"
        return pick(pal, v)

    return paint(f)


def rift_cliff():
    # The Rift's walls: banded dark indigo rock, frosted ledges, streaks of blue ice.
    pal = ["#161a3c", "#1c2248", "#232a56", "#2a3364", "#333e74"]
    a, b = noise(4, 8, 3161), noise(12, 4, 3162)

    def f(x, y):
        band = (y + int(a(x, y) * 6)) % 12
        if band == 0:
            return "#a8b8e8" if b(x, y) > 0.4 else "#5a6ca8"
        if (x + int(b(x, y) * 4)) % 17 == 0 and a(x, y) > 0.5:
            return "#4a78c8"
        return pick(pal, 0.1 + a(x, y) * 0.5 + b(x, y) * 0.4)

    return paint(f)


def glacier_wall():
    # Old glacier ice seen from close by: deep blue, soft bands, a few pale bubbles.
    pal = ["#1a2c6a", "#203476", "#263e84", "#2e4a92", "#3858a2"]
    a, b = noise(3, 6, 3171), noise(6, 3, 3172)
    bubbles = speckle(3173, 6)

    def f(x, y):
        if (x, y) in bubbles:
            return "#8ab4e8"
        layer = math.sin(y * 0.35 + a(x, y) * 3) * 0.5 + 0.5
        return pick(pal, 0.1 + layer * 0.3 + b(x, y) * 0.55)

    return paint(f)


def cavern_ice():
    # The cavern walls: dark indigo rock and old ice, a faint vein of crystal here and
    # there.
    pal = ["#121836", "#161e42", "#1a244c", "#202c58", "#283664"]
    a, b = noise(5, 3, 3181), noise(3, 6, 3182)

    def f(x, y):
        if abs(b(x, y) - 0.52) < 0.012 and a(x, y) > 0.55:
            return "#4ab8e0"
        return pick(pal, 0.1 + a(x, y) * 0.55 + b(x, y) * 0.35)

    return paint(f)


def rift_stone():
    # Frost-rimed slate masonry for the bridges and arches.
    pal = ["#3a4266", "#444e76", "#4e5a86", "#5a6894"]
    a = noise(4, 2, 3191)

    def f(x, y):
        course = y // 8
        joint = y % 8 == 0 or (x + (8 if course % 2 else 0)) % 16 == 0
        if joint:
            return "#e2eaff" if y % 8 == 0 and a(x, y) > 0.45 else "#22284a"
        return pick(pal, 0.15 + a(x, y) * 0.75)

    return paint(f)


def rift_carved():
    # Carved arch stones: ancient runes glowing cyan in the slate.
    a = noise(4, 2, 3201)

    def f(x, y):
        cx, cy = x % 16, y % 16
        rune = (cx in (4, 11) and 3 <= cy <= 12) or (cy in (3, 12) and 4 <= cx <= 11) or (cx == cy and 4 <= cx <= 11)
        if rune and (x // 16 + y // 16) % 2 == 0:
            return "#7af4ff"
        if y % 16 == 0 or x % 16 == 0:
            return "#20264a"
        return pick(["#3c4468", "#465078", "#505c88"], a(x, y))

    return paint(f)


def crystal(seed, pal, glint):
    """A faceted crystal: broad facets along it, each shading from bright to deep across
    its width, a fine bright edge between them, a few inner sparkles."""
    a = noise(3, 6, seed)
    sparkle = speckle(seed + 1, 8)

    def f(x, y):
        facet = (x // 16) % 4
        if x % 16 == 0:
            return pick(pal, 0.95)
        if (x, y) in sparkle:
            return glint
        across = (x % 16) / 16.0
        v = 0.15 + 0.5 * (1 - across) * (0.6 + 0.4 * (facet % 2)) + a(x, y) * 0.3
        return pick(pal, min(0.99, v))

    return paint(f)

def lantern_amber():
    # Warm lantern glass in an iron frame.
    a = noise(4, 2, 3211)

    def f(x, y):
        if x % 16 < 2 or y < 2 or y > 29:
            return "#2a1e18"
        return pick(["#ff9a2a", "#ffb43c", "#ffcc5a", "#ffe08a"], 0.2 + a(x, y) * 0.7 + (1 - abs(y - 16) / 16) * 0.2)

    return paint(f)


def edge_amber():
    # The road's edge walls: dark frosted slate with a row of small warm amber lamps
    # (the guiding lights along the road).
    a = noise(4, 2, 3215)

    def f(x, y):
        cx = x % 32
        if 13 <= cx <= 18 and 13 <= y <= 18:
            return "#ffd88a" if 15 <= cx <= 16 and 15 <= y <= 16 else "#ff9e3a"
        if y < 4:
            return "#c4d0f0" if a(x, y) > 0.3 else "#9aaada"
        return pick(["#20264a", "#262d54", "#2c345e"], a(x, y))

    return paint(f)


def icefall_rift():
    # A frozen waterfall: long blue icicle streaks, pale at their ridges.
    pal = ["#2a4c9c", "#3a62b4", "#5280cc", "#78a2e0", "#b2cef2"]
    a = noise(8, 2, 3221)

    def f(x, y):
        streak = math.sin(x * 1.3 + a(x, y) * 7) * 0.5 + 0.5
        return pick(pal, streak * 0.75 + a(x, y) * 0.3)

    return paint(f)


def falls_rift():
    # Falling water lit from below: white and cyan streaks.
    pal = ["#3ab6e0", "#62cdec", "#94e2f6", "#ccf4fc", "#ffffff"]
    a = noise(8, 2, 3231)

    def f(x, y):
        streak = math.sin(x * 2.1 + a(x, y) * 6) * 0.5 + 0.5
        return pick(pal, streak * 0.7 + a(x, y) * 0.45)

    return paint(f)


def rift_mist():
    a, b = noise(4, 2, 3241), noise(8, 4, 3242)

    def f(x, y):
        return pick(["#7ab4e8", "#94c6f0", "#b4d8f6", "#d4e8fc", "#f0f6ff"], a(x, y) * 0.6 + b(x, y) * 0.5)

    return paint(f)


def rift_roof():
    # The caverns' roofs: deep violet-blue ice glittering with countless tiny crystals.
    pal = ["#1c1c4e", "#22225a", "#2a2a66", "#323474"]
    a = noise(4, 2, 3245)
    big = speckle(3246, 10)
    small = speckle(3247, 26)

    def f(x, y):
        if (x, y) in big:
            return "#9af0ff" if (x + y) % 2 else "#d8b0ff"
        if (x, y) in small:
            return "#5a8ad8"
        return pick(pal, a(x, y))

    return paint(f)


def abyss_glow():
    # The bottom of the abyss, far below: darkness, glowing crystal dust.
    a = noise(6, 3, 3251)
    dust = speckle(3252, 40)

    def f(x, y):
        if (x, y) in dust:
            return "#5ae8ff" if (x + y) % 3 else "#b07aff"
        return pick(["#060a22", "#0a1030", "#0e163c", "#141e4c"], a(x, y))

    return paint(f)


def abyss_fog():
    a, b = noise(4, 2, 3261), noise(8, 4, 3262)

    def f(x, y):
        return pick(["#141c4a", "#1c2a62", "#26387a", "#324a92", "#4462aa"], a(x, y) * 0.6 + b(x, y) * 0.5)

    return paint(f)


THEMES.append(
    {
        "id": "aurora_rift",
        "name": "Aurora Rift",
        "description": "A fractured glacier under the northern lights: deep blue ice, dark indigo rock, glowing cyan and violet crystals, warm amber lanterns and a starry night alive with aurora",
        "environment": {
            "sky": "#0c1030",
            "fog": {"enabled": True, "color": "#1c2c64", "near": 280, "far": 1600},
            "sun": {"color": "#b8d4ff", "intensity": 1.7, "direction": [0.3, 0.78, -0.55]},
            "ambient": {"sky": "#8aa8ff", "ground": "#2c2458", "intensity": 1.55},
            "skyDome": {
                "top": "#040720",
                "horizon": "#6a2c8c",
                "bottom": "#1c1848",
                "sun": {"color": "#f4f8ff", "size": 3.5, "glow": "#a8c0ff", "elevation": 40},
                "clouds": {"count": 10, "color": "#3c2c70", "shade": "#1a1444", "seed": 83, "low": 3, "high": 9, "drift": 0.002},
                "hills": {"color": "#121838", "far": "#4c4c90", "height": 17, "seed": 89, "layers": 3},
                "stars": {"count": 900, "color": "#ffffff", "seed": 97, "low": 10},
                "aurora": {"count": 7, "seed": 5, "low": 18, "high": 80, "speed": 1, "intensity": 1.1, "azimuth": 160,
                           "colors": ["#2effa0", "#36d8ff", "#9a5aff", "#ff4ab8"]},
            },
        },
    }
)

# ------------------------------------------------------------------ Canyon Dash


def _shade(c, k):
    r, g, b = hexrgb(c)
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(v * k))) for v in (r, g, b))


def dash_road():
    # Packed red-orange desert dirt: smooth and fast, two worn tyre lines along it
    # (V runs along the road), a few pale pebbles. Calm, because it fills the screen.
    pal = ["#c8885a", "#d09262", "#d89c6a", "#dfa572", "#e6ae7c"]
    a, b = noise(3, 6, 3601), noise(12, 8, 3602)
    peb = speckle(3603, 14)

    def f(x, y):
        if (x, y) in peb:
            return "#f2cc9c"
        v = 0.2 + a(x, y) * 0.45 + b(x, y) * 0.35
        # Tyre lines: two soft darker bands across U, a little wobbly.
        for c in (19, 45):
            d = abs(x - c - 2.0 * math.sin(y * 0.2 + c))
            if d < 3.5:
                v -= 0.22 * (1 - d / 3.5)
        return pick(pal, v)

    return paint(f)


def dash_shoulder():
    # The verge: browner loose dirt and gravel, pebbles and the odd tuft.
    pal = ["#8e4424", "#9c4e2a", "#aa5a30", "#b86638", "#c67444"]
    a, b = noise(6, 3, 3611), noise(16, 8, 3612)
    peb = speckle(3613, 70)
    tuft = speckle(3614, 10)

    def f(x, y):
        if (x, y) in tuft:
            return "#9a8a3a"
        if (x, y) in peb:
            return "#e0ae7a" if (x + y) % 3 else "#6a3018"
        return pick(pal, 0.15 + a(x, y) * 0.5 + b(x, y) * 0.35)

    return paint(f)


def desert_sand():
    # Off the road: soft red sand with ripples, dry grass and sage dots.
    pal = ["#c46a3a", "#cf7642", "#d9824c", "#e38f56", "#eb9c62"]
    a, b = noise(4, 2, 3621), noise(16, 8, 3622)
    sage = speckle(3623, 18)
    grass = speckle(3624, 22)

    def f(x, y):
        if (x, y) in sage:
            return "#7a8a4a"
        if (x, y) in grass:
            return "#d8b860"
        rip = 0.5 + 0.5 * math.sin(x * 0.55 + y * 0.9 + a(x, y) * 4)
        return pick(pal, 0.12 + rip * 0.3 + b(x, y) * 0.5)

    return paint(f)


def red_sand():
    # Deeper, redder sand where the ground is lower and sheltered, more scrub.
    pal = ["#b4522e", "#be5c34", "#c8663a", "#d07040", "#d87a48"]
    a, b = noise(4, 2, 3801), noise(16, 8, 3802)
    sage = speckle(3803, 30)
    grass = speckle(3804, 16)

    def f(x, y):
        if (x, y) in sage:
            return "#6e8a46"
        if (x, y) in grass:
            return "#d8b05a"
        rip = 0.5 + 0.5 * math.sin(x * 0.5 - y * 0.8 + a(x, y) * 4)
        return pick(pal, 0.12 + rip * 0.3 + b(x, y) * 0.5)

    return paint(f)


def pale_sand():
    # Pale, sun-bleached sand drifts on the high ground.
    pal = ["#d08a5c", "#d69464", "#dc9e6e", "#e2a878", "#e8b282"]
    a, b = noise(4, 2, 3811), noise(16, 8, 3812)
    dots = speckle(3813, 14)

    def f(x, y):
        if (x, y) in dots:
            return "#9a7a40"
        rip = 0.5 + 0.5 * math.sin(x * 0.6 + y * 1.1 + a(x, y) * 4)
        return pick(pal, 0.1 + rip * 0.35 + b(x, y) * 0.45)

    return paint(f)


def slickrock():
    # The mesa tops: smooth pink-orange sandstone pavement, cracked into slabs, with
    # sand drifted in the cracks and a few dark potholes.
    pal = ["#c8784a", "#d28452", "#dc905c", "#e49c66", "#eca872"]
    a, b = noise(4, 2, 3631), noise(12, 6, 3632)

    def f(x, y):
        cell = abs(math.sin(x * 0.19 + a(x, y) * 3) * math.sin(y * 0.37 + b(x, y) * 2))
        if cell < 0.05:
            return "#a85a34"
        return pick(pal, 0.2 + a(x, y) * 0.45 + b(x, y) * 0.35)

    return paint(f)


def strata(seed, base, light, dark, lines=4, grain=0.35):
    """A sandstone layer: horizontal bedding lines (V is height on a cliff), soft
    cross-bedding, light and dark streaks. One per band of the canyon wall."""

    def make():
        a, b = noise(4, 2, seed), noise(16, 8, seed + 1)
        c = noise(2, 4, seed + 2)

        def f(x, y):
            yy = y + a(x, y) * 3.0
            line = yy % (H / lines)
            k = 0.86 + b(x, y) * 0.26
            # Cross-bedding: faint slanting lines inside each bed.
            if abs(math.sin((x * 0.35 + yy * 1.2) + c(x, y) * 3)) < 0.06:
                k -= 0.08
            if line < 1.0:
                return _shade(dark, 0.95 + b(x, y) * 0.1)
            if line < 2.0:
                return _shade(light, k)
            if b(x, y) > 0.82:
                return _shade(light, 0.95)
            return _shade(base, k + (c(x, y) - 0.5) * grain)

        return paint(f)

    return make


strata_cream = strata(3641, "#e2b07a", "#f4d2a0", "#b47a4c", lines=3)
strata_orange = strata(3644, "#d4783e", "#eca262", "#9a4a24", lines=4)
strata_red = strata(3647, "#b84a2a", "#d86a3e", "#7e2c18", lines=4)
strata_rust = strata(3650, "#9a3a24", "#be5434", "#64221a", lines=6)
strata_purple = strata(3653, "#7a3a3a", "#9a5048", "#4a2230", lines=5)


def talus():
    # Scree slopes under the cliffs: orange-brown rubble with dark gaps.
    pal = ["#8c4428", "#a2522e", "#b46036", "#c66e40", "#d68050"]
    a, b = noise(8, 4, 3661), noise(32, 16, 3662)

    def f(x, y):
        v = b(x, y)
        if v < 0.18:
            return "#5a2a1c"
        if v > 0.85:
            return "#e4a070"
        return pick(pal, 0.2 + a(x, y) * 0.4 + v * 0.4)

    return paint(f)


def canyon_river():
    # The river far below: bright turquoise, paler where it riffles (scrolls along V).
    pal = ["#1898a8", "#22aab6", "#36bcc2", "#58d0cc", "#8ae4dc"]
    a, b = noise(4, 8, 3671), noise(8, 16, 3672)

    def f(x, y):
        rip = 0.5 + 0.5 * math.sin(y * 0.8 + a(x, y) * 6)
        if rip > 0.94 and b(x, y) > 0.5:
            return "#e4fbf6"
        return pick(pal, 0.1 + rip * 0.4 + b(x, y) * 0.45)

    return paint(f)


def falls_dash():
    # The canyon falls: white water streaked with turquoise.
    pal = ["#4ab8c8", "#7ed2dc", "#b4e8ec", "#e2f8f8", "#ffffff"]
    a, b = noise(16, 2, 3681), noise(8, 4, 3682)

    def f(x, y):
        streak = 0.5 + 0.5 * math.sin(x * 1.3 + a(x, y) * 8)
        return pick(pal, 0.15 + streak * 0.55 + b(x, y) * 0.35)

    return paint(f)


def canyon_mist():
    # Spray hanging over the plunge pools.
    a, b = noise(4, 2, 3691), noise(8, 4, 3692)

    def f(x, y):
        return pick(["#d8ecf0", "#e6f4f6", "#f2fafa", "#ffffff"], a(x, y) * 0.6 + b(x, y) * 0.4)

    return paint(f)


def weathered_timber():
    # Sun-bleached trestle timber: grey-brown grain, dark splits, iron bolts.
    pal = ["#6e5038", "#7e5e42", "#8e6c4c", "#a07c58", "#b28c66"]
    a, b = noise(2, 8, 3701), noise(8, 16, 3702)

    def f(x, y):
        if y % 16 in (4, 12) and x % 16 == 8:
            return "#2a2622"
        grain = 0.5 + 0.5 * math.sin(x * 1.4 + a(x, y) * 6)
        if grain < 0.07:
            return "#463224"
        return pick(pal, 0.15 + grain * 0.45 + b(x, y) * 0.35)

    return paint(f)


def fence_rail():
    # The road-edge fence: two round timber rails on dark posts, the sandstone curb
    # under them. (Horizontal: U runs along the barrier, V up it.)
    a = noise(8, 2, 3711)

    def f(x, y):
        if x % 16 < 3:
            return pick(["#4e3220", "#5e3c26", "#6e4a30"], a(x, y))  # a post
        for top in (4, 14):
            if top <= y < top + 5:
                k = (y - top) / 4
                return pick(["#c09868", "#a8804e", "#8e6a40", "#6a4c2e", "#4e3622"], k * 0.8 + a(x, y) * 0.2)
        if y >= 24:
            return pick(["#b8683c", "#c87648", "#d68654"], a(x, y))  # the curb
        return pick(["#6a3a22", "#7a4428"], a(x, y))  # shadow between the rails

    return paint(f)


def plank_deck():
    # The great bridge's deck: sun-bleached boards across the road, dark gaps.
    pal = ["#8a6a48", "#9c7a54", "#ae8a60", "#be9a6c", "#cca878"]
    a, b = noise(2, 8, 3721), noise(8, 16, 3722)

    def f(x, y):
        board = y // 6
        yy = y % 6
        if yy == 5:
            return "#3a2818"
        if yy == 0:
            return "#dcb888"
        if (x + board * 19) % 32 in (2, 3) and yy == 2:
            return "#3a3530"
        grain = 0.5 + 0.5 * math.sin(x * 0.6 + board * 2.3 + a(x, y) * 5)
        return pick(pal, 0.15 + grain * 0.45 + b(x, y) * 0.35)

    return paint(f)


def masonry():
    # Dressed sandstone blocks: the bridge piers, retaining walls, the outpost.
    a, b = noise(4, 2, 3731), noise(16, 8, 3732)

    def f(x, y):
        row = y // 8
        off = 8 if row % 2 else 0
        if y % 8 == 7 or (x + off) % 16 == 15:
            return "#7a3e24"
        k = 0.85 + a(x, y) * 0.2 + ((x + off) // 16 + row * 3) % 4 * 0.03
        if y % 8 == 0:
            k += 0.12
        return _shade("#c87a48", k + (b(x, y) - 0.5) * 0.12)

    return paint(f)


def saguaro():
    # Cactus skin: deep green ribs (vertical) with pale spines.
    a = noise(4, 8, 3741)
    sp = speckle(3742, 40)

    def f(x, y):
        if (x, y) in sp:
            return "#f0e4b0"
        rib = (x % 8) / 8
        v = 0.25 + 0.6 * (1 - abs(rib - 0.5) * 2) + (a(x, y) - 0.5) * 0.2
        return pick(["#1e5a2a", "#2a7034", "#3a8640", "#4e9a4a", "#68ae58"], v)

    return paint(f)


def agave():
    a = noise(8, 4, 3751)

    def f(x, y):
        v = 0.3 + 0.5 * (1 - abs((x % 12) / 12 - 0.5) * 2) + (a(x, y) - 0.5) * 0.3
        if y < 2:
            return "#e0d070"
        return pick(["#3a6a5a", "#4a7e6a", "#5e927a", "#78a88a", "#94bc9c"], v)

    return paint(f)


def sagebrush():
    a, b = noise(8, 4, 3761), noise(16, 8, 3762)

    def f(x, y):
        v = a(x, y) * 0.6 + b(x, y) * 0.4
        if b(x, y) > 0.86:
            return "#d8c070"  # little yellow flowers
        return pick(["#4a5a2a", "#5e6e34", "#74823e", "#8a944c", "#a2a65e"], v)

    return paint(f)


def dry_grass():
    a = noise(16, 2, 3771)

    def f(x, y):
        blade = 0.5 + 0.5 * math.sin(x * 2.1 + a(x, y) * 5)
        return pick(["#a8782e", "#c0903a", "#d4a848", "#e4c060", "#f0d47a"], blade * 0.7 + (1 - y / H) * 0.3)

    return paint(f)


def chevron_amber():
    # Turn signs: black chevrons on bright amber, a dark frame.
    def f(x, y):
        u = (x + abs(y - 16)) % 16
        if y in (0, 1, 30, 31):
            return "#2a1a10"
        if u < 6:
            return "#1c1410"
        return "#ffb81c" if (x + y) % 9 else "#ffc840"

    return paint(f)


def windmill_blade():
    # Galvanised windmill vanes, a red stripe near the tips.
    a = noise(4, 2, 3781)

    def f(x, y):
        if x > 52:
            return "#c8302a" if x < 58 else "#e8e4dc"
        if x % 8 == 0:
            return "#7a8088"
        return pick(["#a8b0b8", "#bcc4ca", "#d0d6da", "#e2e6e8"], a(x, y))

    return paint(f)


def canvas_sun():
    # Race-day canvas: deep red with a gold sun emblem, a gold hem.
    def f(x, y):
        cx, cy = (x % 32) - 15.5, (y % 32) - 14.5
        if y % 32 >= 29 or x % 32 in (0, 31):
            return "#f0b840"
        r = math.hypot(cx, cy)
        a = math.atan2(cy, cx)
        if r < 4.5:
            return "#ffd050"
        if 5.5 < r < 10 and math.cos(a * 8) > 0.55:
            return "#f4b83a"
        return "#b8262a" if (x + y) % 7 else "#a82026"

    return paint(f)


def canvas_blue():
    def f(x, y):
        cx, cy = (x % 32) - 15.5, (y % 32) - 14.5
        if y % 32 >= 29 or x % 32 in (0, 31):
            return "#f0b840"
        if abs(cx) + abs(cy) < 7 and abs(cx) + abs(cy) > 4:
            return "#f4c048"
        return "#1e4c9a" if (x + y) % 7 else "#1a4288"

    return paint(f)


def desert_haze():
    # Far-off mesas: soft and pale, a few faint bands.
    a = noise(4, 2, 3791)

    def f(x, y):
        return pick(["#c48a7a", "#cc9482", "#d49e8a", "#dca894"], (y % 8) / 10 + a(x, y) * 0.4)

    return paint(f)


THEMES.append(
    {
        "id": "canyon_dash",
        "name": "Canyon Dash",
        "description": "A clear desert afternoon turning golden: layered red, orange and cream sandstone, deep blue-violet canyon shadows, a turquoise river and a saturated blue sky with big white clouds",
        "environment": {
            "sky": "#3f8fe6",
            "fog": {"enabled": True, "color": "#d4c4cc", "near": 520, "far": 2900},
            "sun": {"color": "#ffd8a0", "intensity": 3.0, "direction": [-0.62, 0.52, 0.58]},
            "ambient": {"sky": "#a8c8f4", "ground": "#8a4636", "intensity": 1.25},
            "skyDome": {
                "top": "#155ed6",
                "horizon": "#cfe2f2",
                "bottom": "#e2c8b4",
                "sun": {"color": "#fff4d0", "size": 9, "glow": "#ffc878", "elevation": 18},
                "clouds": {"count": 28, "color": "#ffffff", "shade": "#e6d0c8", "seed": 101, "low": 8, "high": 32, "drift": 0.004},
                "hills": {"color": "#b4705c", "far": "#d0b2b0", "height": 5, "seed": 103, "layers": 3, "style": "mesas"},
            },
        },
    }
)


# ------------------------------------------------------------------ Oasis Haven


def oasis_paving():
    # Warm cream flagstones in staggered rows (V runs along the road), soft joints, a
    # few pale and honey stones, the odd blue tile set in.
    a, b = noise(4, 2, 3901), noise(16, 8, 3902)

    def f(x, y):
        row = y // 8
        off = 8 if row % 2 else 0
        cell = ((x + off) // 16) * 7 + row * 13
        if y % 8 == 7 or (x + off) % 16 == 15:
            return "#c8a878"
        if cell % 23 == 5 and 3 <= (x + off) % 16 <= 11 and 2 <= y % 8 <= 5:
            return "#2c64c8" if (x + y) % 2 else "#3a78d8"
        k = 0.93 + a(x, y) * 0.07 + ((cell * 37) % 7) * 0.012 + (b(x, y) - 0.5) * 0.05
        return _shade("#efd9b0", k)

    return paint(f)


def palace_paving():
    # The palace road: larger pale stones with a blue-and-gold star inlay.
    a = noise(4, 2, 3911)

    def f(x, y):
        cx, cy = (x % 32) - 15.5, (y % 32) - 15.5
        if abs(cx) + abs(cy) < 6:
            return "#e6b43a" if abs(cx) + abs(cy) < 3 else "#2a5cc0"
        if x % 32 == 31 or y % 32 == 31:
            return "#c7a676"
        return _shade("#f4e2c0", 0.94 + a(x, y) * 0.08)

    return paint(f)


def tile_border():
    # The road's border: bands of blue and white tiles with a gold line (V along the road).
    def f(x, y):
        u = x % 64
        if u < 3 or u > 60:
            return "#e2b84a"
        k = (u // 6 + y // 6) % 2
        cx, cy = (u % 6) - 2.5, (y % 6) - 2.5
        if abs(cx) + abs(cy) < 1.6:
            return "#ffffff" if k else "#f0c040"
        return "#2456c0" if k else "#3c8ae0"

    return paint(f)


def balustrade():
    # A cream stone balustrade: a capping rail, turned balusters, a base course; a blue
    # tile band under the rail. (U along the wall, V up it.)
    a = noise(8, 2, 3921)

    def f(x, y):
        if y < 5:
            return _shade("#f2e2c4", 0.95 + a(x, y) * 0.06)
        if y < 8:
            return "#2e66cc" if (x // 4) % 2 else "#e8c04a"
        if y >= 26:
            return _shade("#dcc49a", 0.95 + a(x, y) * 0.06)
        u = x % 8
        w = 2.4 + 1.2 * math.sin((y - 8) / 18 * math.pi)
        if abs(u - 3.5) < w:
            return _shade("#efdcb8", 0.88 + 0.12 * (1 - abs(u - 3.5) / w))
        return "#7a5a3a"

    return paint(f)


def market_rail():
    # Market street railings: dark carved wood with brass knobs and a striped cloth hung on it.
    def f(x, y):
        if y < 4:
            return "#6a3a1e"
        if x % 16 < 2:
            return "#4a2812" if y > 6 else "#d8a83a"
        if 8 < y < 22:
            return ["#d83a3a", "#f0c040", "#2a8ad8", "#f6f0e0"][(x // 4) % 4]
        return "#5a3418"

    return paint(f)


def oasis_stone():
    # Cream sandstone ashlar for buildings and terrace walls, lit warm.
    a, b = noise(4, 2, 3931), noise(16, 8, 3932)

    def f(x, y):
        row = y // 8
        off = 8 if row % 2 else 0
        if y % 8 == 7 or (x + off) % 16 == 15:
            return "#c9a87a"
        k = 0.92 + a(x, y) * 0.08 + (((x + off) // 16 + row * 5) % 4) * 0.015 + (b(x, y) - 0.5) * 0.06
        return _shade("#f0dcb4", k)

    return paint(f)


def oasis_arcade(wall="#f2deb8", band="#2e66cc", dark="#3a3a6a"):
    # A façade of pointed arches: cream stone, deep blue-shadowed openings with a gold
    # lamp glow, blue tile bands. (U along the wall, V up it: one storey per repeat.)
    return paint(_arcade(wall, band, dark))


def _arcade(wall, band, dark):
    def f(x, y):
        u = x % 16
        if y < 3:
            return band if (x // 2) % 2 else "#f0f0f0"
        if y > 28:
            return _shade(wall, 0.88)
        cx = u - 7.5
        top = 9 + abs(cx) * 0.9 if abs(cx) < 5 else 99
        if abs(cx) < 5 and y > top - 2 and y < 27:
            if y < top:
                return "#e8c04a"
            return dark if y < 22 else "#ffcf70"
        return _shade(wall, 0.95 + 0.05 * ((x * 7 + y * 3) % 5) / 5)

    return f


def oasis_windows(wall="#f2deb8", shutter="#1fa6a8"):
    # Upper storeys: cream walls with small arched windows, turquoise shutters, a frieze.
    def f(x, y):
        u, v = x % 16, y % 32
        if v < 2:
            return "#e8c04a"
        if 6 < v < 22 and 5 <= u <= 10:
            if v < 9 and (u in (5, 10)):
                return wall
            if u in (5, 10):
                return shutter
            return "#203a6a" if v < 18 else "#2a4a7a"
        return wall if (x + y) % 9 else _shade(wall, 0.95)

    return paint(f, 64, 32)


def dome_blue():
    # A royal-blue tiled dome: scale-pattern tiles, gold ribs (U round, V up).
    def f(x, y):
        if x % 16 == 0:
            return "#f0c040"
        r = (y // 4) % 2
        u = (x + (2 if r else 0)) % 4
        if y % 4 == 0 or u == 0:
            return "#1a3a9a"
        return "#2a5ad0" if (u + y) % 3 else "#3c78e8"

    return paint(f)


def dome_teal():
    def f(x, y):
        if x % 16 == 0:
            return "#f0c040"
        r = (y // 4) % 2
        u = (x + (2 if r else 0)) % 4
        if y % 4 == 0 or u == 0:
            return "#0a6a6a"
        return "#14a0a0" if (u + y) % 3 else "#2cc4bc"

    return paint(f)


def gold_leaf():
    a = noise(8, 4, 3941)

    def f(x, y):
        return pick(["#b07a10", "#d49a20", "#f0c040", "#ffe080", "#fff4c0"], 0.15 + a(x, y) * 0.75)

    return paint(f)


def lagoon():
    # The lake: brilliant pale turquoise (the depth comes from the vertex paint, the
    # waves and sparkle from the game's water shader), soft light ripple lines.
    a, b = noise(8, 4, 3951), noise(16, 8, 3952)

    def f(x, y):
        rip = abs(math.sin(x * 0.35 + a(x, y) * 5) * math.sin(y * 0.5 + b(x, y) * 4))
        if rip > 0.92:
            return "#f4ffff"
        return pick(["#6ad8e4", "#7ee0ea", "#92e8ef", "#a8eff4", "#c0f6f8"], 0.1 + rip * 0.5 + b(x, y) * 0.35)

    return paint(f)


def shore_foam():
    # A band of foam lapping at the shore (V across the band: thick at the shore edge).
    a = noise(16, 2, 3961)

    def f(x, y):
        k = 1 - y / H + (a(x, y) - 0.5) * 0.6
        if k > 0.62:
            return "#ffffff"
        if k > 0.42:
            return "#d8f8fa" if (x + y) % 3 else "#ffffff"
        return "#9ae6ee"

    return paint(f)


def lake_sand():
    a, b = noise(4, 2, 3971), noise(16, 8, 3972)

    def f(x, y):
        return pick(["#d8c896", "#e2d2a0", "#ead9aa", "#f0e2b6"], a(x, y) * 0.6 + b(x, y) * 0.4)

    return paint(f)


def gold_sand():
    # The desert round the oasis: golden sand with wind ripples.
    a, b = noise(4, 2, 3981), noise(16, 8, 3982)
    dots = speckle(3983, 10)

    def f(x, y):
        if (x, y) in dots:
            return "#a8803a"
        rip = 0.5 + 0.5 * math.sin(x * 0.6 + y * 1.0 + a(x, y) * 4)
        return pick(["#e2b06a", "#e8b874", "#eec07e", "#f2ca8a", "#f6d498"], 0.1 + rip * 0.35 + b(x, y) * 0.45)

    return paint(f)


def adobe():
    # Mud-brick plaster for the oasis village: warm tan, patchy, with the odd crack and
    # a brick or two showing where the plaster has fallen.
    a, b = noise(4, 2, 4101), noise(16, 8, 4102)
    cracks = speckle(4103, 14)
    bricks = noise(4, 4, 4104)

    def f(x, y):
        if (x, y) in cracks or ((x - 1, y + 1) in cracks):
            return "#9a6a40"
        if bricks(x, y) > 0.88 and (y % 4 == 0 or (x + (y // 4) * 4) % 8 == 0):
            return "#a8703e"
        if bricks(x, y) > 0.88:
            return "#c08048"
        return pick(["#c8925a", "#d29e64", "#daa86e", "#e2b278", "#e8bc84"], 0.1 + a(x, y) * 0.5 + b(x, y) * 0.4)

    return paint(f)


def adobe_dark():
    # The same plaster in shade, and round the bases of walls (darker, dustier).
    a, b = noise(4, 2, 4111), noise(16, 8, 4112)

    def f(x, y):
        return pick(["#9c6a40", "#a8744a", "#b27e52", "#bc8a5c"], a(x, y) * 0.5 + b(x, y) * 0.5)

    return paint(f)


def tent_cloth():
    # Nomad tent cloth: dark woven goat hair with cream and red stripes along it.
    a = noise(16, 8, 4121)

    def f(x, y):
        k = y % 16
        if k in (3, 4):
            return "#e8d4a8"
        if k == 5:
            return "#b83a2a"
        if k in (11,):
            return "#c8a060"
        weave = ((x + y) % 2) * 0.12
        return pick(["#2e2018", "#3a2a1e", "#463424", "#52402c"], a(x, y) * 0.7 + weave)

    return paint(f)


def tent_cloth_red():
    # A brighter tent: madder red with gold and indigo bands.
    a = noise(16, 8, 4131)

    def f(x, y):
        k = y % 16
        if k in (2, 3):
            return "#e0a83a"
        if k in (9, 10):
            return "#2a3a6a"
        if k == 11:
            return "#e8d4a8"
        return pick(["#8a2418", "#a02c1e", "#b43624", "#c0402a"], a(x, y) * 0.6 + ((x + y) % 2) * 0.15)

    return paint(f)


def dune_crest():
    # Wind-sculpted sand on the dunes' faces: long ripples, lighter crests.
    a, b = noise(4, 2, 4141), noise(16, 8, 4142)

    def f(x, y):
        rip = 0.5 + 0.5 * math.sin(y * 0.9 + 1.6 * math.sin(x * 0.2) + a(x, y) * 3)
        return pick(["#dca060", "#e6ae6c", "#eebc7a", "#f4c886", "#fad696"], 0.05 + rip * 0.55 + b(x, y) * 0.35)

    return paint(f)


def gold_cliff():
    # The basin's cliffs: golden and peach sandstone in bands.
    bands = ["#e0a86a", "#eab87a", "#d89458", "#f0c48a", "#d08a52"]
    a, b = noise(4, 2, 3991), noise(16, 8, 3992)

    def f(x, y):
        yy = y + a(x, y) * 3
        c = bands[int(yy / 5) % len(bands)]
        if int(yy) % 5 == 4:
            return _shade(c, 0.82)
        return _shade(c, 0.9 + b(x, y) * 0.2)

    return paint(f)


def oasis_lawn():
    # Lush garden grass: bright and green, little flowers.
    a, b = noise(8, 4, 4001), noise(16, 8, 4002)
    fl = speckle(4003, 22)

    def f(x, y):
        if (x, y) in fl:
            return ["#ff5aa8", "#ffe060", "#ffffff"][(x + y) % 3]
        return pick(["#3a9a2e", "#46aa34", "#54b83c", "#64c644", "#78d050"], a(x, y) * 0.5 + b(x, y) * 0.5)

    return paint(f)


def garden_soil():
    a, b = noise(8, 4, 4011), noise(16, 8, 4012)
    tuft = speckle(4013, 40)

    def f(x, y):
        if (x, y) in tuft:
            return "#5aa63a"
        return pick(["#b88a56", "#c49660", "#cea26c", "#d8ae78"], a(x, y) * 0.5 + b(x, y) * 0.5)

    return paint(f)


def bougainvillea():
    # Magenta and pink blossom clouds over dark green leaves.
    a, b = noise(8, 4, 4021), noise(16, 8, 4022)

    def f(x, y):
        v = a(x, y) * 0.6 + b(x, y) * 0.4
        if v > 0.42:
            return pick(["#c8186e", "#e02a88", "#f04aa0", "#ff7cc0", "#ffb0dc"], (v - 0.42) / 0.58)
        return pick(["#1e5a26", "#2a7030", "#3a8640"], v / 0.42)

    return paint(f)


def hedge():
    a, b = noise(8, 4, 4031), noise(16, 8, 4032)
    fl = speckle(4033, 12)

    def f(x, y):
        if (x, y) in fl:
            return "#ffffff" if (x * y) % 2 else "#ffd040"
        return pick(["#1e6a2a", "#287a32", "#348a3a", "#44a046", "#5ab454"], a(x, y) * 0.5 + b(x, y) * 0.5)

    return paint(f)


def stripes(cols, w=8):
    def make():
        def f(x, y):
            if y >= 28:
                return "#f0c040" if (x // 2) % 2 else cols[0]
            return cols[(x // w) % len(cols)]

        return paint(f)

    return make


def oasis_banner():
    # Royal blue banner with a gold border and a gold lotus emblem.
    def f(x, y):
        u, v = x % 32, y % 32
        if u in (0, 1, 30, 31) or v in (0, 1, 30, 31):
            return "#f0c040"
        cx, cy = u - 15.5, v - 14.5
        r = math.hypot(cx, cy)
        a = math.atan2(cy, cx)
        petal = 4.5 + 3.5 * abs(math.cos(a * 2.5))
        if r < petal and r > 1.5:
            return "#f4c84a" if r < petal - 1.2 else "#c8901a"
        if r <= 1.5:
            return "#fff0a0"
        return "#1e44a8" if (u + v) % 6 else "#22489c"

    return paint(f)


def chevron_red():
    # Red-and-white turn chevrons in a gold frame.
    def f(x, y):
        if y in (0, 1, 30, 31):
            return "#e8b83a"
        u = (x + abs(y - 16)) % 16
        return "#ffffff" if u < 7 else "#e02a2a"

    return paint(f)


def terracotta():
    a = noise(8, 4, 4041)

    def f(x, y):
        if y % 8 == 0:
            return "#f0c040" if (x // 4) % 2 else "#2a64c8"
        return pick(["#a84a24", "#bc5a2e", "#cc6a38", "#da7c46"], a(x, y))

    return paint(f)


def rug():
    def f(x, y):
        u, v = x % 32, y % 32
        if u < 2 or u > 29 or v < 2 or v > 29:
            return "#f0c040"
        d = abs(u - 15.5) + abs(v - 15.5)
        if d < 5:
            return "#f6e6c0"
        if d < 9:
            return "#1e44a8"
        if d < 12:
            return "#f0c040"
        return "#b8202e" if (u + v) % 4 else "#d02e3e"

    return paint(f)


def fruit():
    # Market produce piled in crates: oranges, melons, lemons, grapes, pomegranates.
    cols = [["#ff8a1a", "#ffa63a"], ["#5ac040", "#3a9a2a"], ["#ffe040", "#f0c820"], ["#8a2aa8", "#a84ac8"], ["#d8202e", "#f04050"]]
    a = noise(8, 4, 4051)

    def f(x, y):
        c = cols[(x // 13 + y // 11) % len(cols)]
        if ((x % 4) - 1.5) ** 2 + ((y % 4) - 1.5) ** 2 < 2.2:
            return c[0] if a(x, y) > 0.4 else c[1]
        return "#6a4426"

    return paint(f)


def wood_dock():
    pal = ["#8a5a32", "#9a6838", "#ac7a44", "#be8c52"]
    a = noise(2, 8, 4061)

    def f(x, y):
        if y % 6 == 5:
            return "#3a2414"
        return pick(pal, 0.2 + 0.6 * (0.5 + 0.5 * math.sin(x * 0.7 + (y // 6) * 2 + a(x, y) * 4)))

    return paint(f)


THEMES.append(
    {
        "id": "oasis_haven",
        "name": "Oasis Haven",
        "description": "A perfect summer afternoon at a desert oasis resort: an intense blue sky with big white clouds, high bright sun, brilliant turquoise water, cream sandstone with royal-blue domes and gold, lush palms and flowers, and golden dunes and red mesas beyond",
        "environment": {
            "sky": "#2a8af0",
            "fog": {"enabled": True, "color": "#bfe2fa", "near": 600, "far": 3200},
            "sun": {"color": "#fff6e0", "intensity": 3.0, "direction": [-0.35, 0.86, 0.38]},
            "ambient": {"sky": "#bfe0ff", "ground": "#d8b880", "intensity": 1.35},
            "skyDome": {
                "top": "#0a5ce0",
                "horizon": "#a8dcff",
                "bottom": "#e8d4a8",
                "sun": {"color": "#fffbe8", "size": 10, "glow": "#fff4b0", "elevation": 46},
                "clouds": {"count": 32, "color": "#ffffff", "shade": "#d6e8fa", "seed": 131, "low": 7, "high": 34, "drift": 0.005},
                "hills": {"color": "#d0805e", "far": "#e6b896", "height": 5, "seed": 137, "layers": 3, "style": "mesas"},
            },
        },
    }
)


# ------------------------------------------------------------------ Dry Gulch Ghost Town

# A little 5x7 pixel font for the town's painted signs (our own glyphs).
FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10011", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "01010", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "01010", "00100", "00100", "00100", "01010", "10001"],
    "Y": ["10001", "01010", "00100", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "&": ["01100", "10010", "10100", "01000", "10101", "10010", "01101"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "-": ["00000", "00000", "00000", "01110", "00000", "00000", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "00000", "00100"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    " ": ["00000"] * 7,
}


def sign_board(text, w=128, h=32, wood=("#4a3220", "#5a3e28", "#6a4a30", "#7a5636"), ink="#f0e2c0", seed=0, scale=None):
    """A weathered plank sign with the text in pale paint: a dark border, nail heads,
    the paint a little worn."""
    a, b = noise(2, 8, 5101 + seed, w, h), noise(8, 4, 5102 + seed, w, h)
    sc = scale or max(1, min((h - 8) // 7, (w - 8) // max(1, len(text) * 6 - 1)))
    tw = len(text) * 6 * sc - sc
    x0 = (w - tw) // 2
    y0 = (h - 7 * sc) // 2
    lit = set()
    for k, ch in enumerate(text):
        g = FONT.get(ch, FONT[" "])
        for gy, row in enumerate(g):
            for gx, bit in enumerate(row):
                if bit == "1":
                    for dx in range(sc):
                        for dy in range(sc):
                            lit.add((x0 + (k * 6 + gx) * sc + dx, y0 + gy * sc + dy))
    wear = speckle(5103 + seed, w * h // 14, w, h)

    def f(x, y):
        if x < 2 or y < 2 or x >= w - 2 or y >= h - 2:
            return "#2a1c12"
        if (x in (4, w - 5)) and (y in (4, h - 5)):
            return "#1a1410"
        if (x, y) in lit and (x, y) not in wear:
            return ink
        if (x, y) in lit:
            return "#b8a888"
        if y % 10 == 9:
            return "#3a2818"
        grain = 0.5 + 0.5 * math.sin(x * 0.35 + (y // 10) * 2.1 + a(x, y) * 5)
        return pick(list(wood), 0.15 + grain * 0.5 + b(x, y) * 0.3)

    return paint(f, w, h)


def gulch_road():
    # The town's packed dirt: orange-red, hoof-churned, pale wheel tracks and pebbles.
    pal = ["#8a4a2e", "#9a5634", "#aa623a", "#ba7044", "#c87e4e"]
    a, b = noise(4, 2, 5001), noise(16, 8, 5002)
    peb = speckle(5003, 40)
    dark = speckle(5004, 30)

    def f(x, y):
        if (x, y) in peb:
            return "#d8a478"
        if (x, y) in dark:
            return "#6a3622"
        track = x % 32 in (9, 10, 22, 23)
        return pick(pal, 0.2 + a(x, y) * 0.45 + b(x, y) * 0.3 + (0.12 if track else 0))

    return paint(f)


def gulch_verge():
    pal = ["#6e3c28", "#7c462e", "#8a5034", "#9a5c3c"]
    a, b = noise(4, 2, 5011), noise(16, 8, 5012)
    tufts = speckle(5013, 34)

    def f(x, y):
        if (x, y) in tufts or ((x - 1, y) in tufts and y % 2):
            return "#9a8a5a"
        return pick(pal, 0.2 + a(x, y) * 0.5 + b(x, y) * 0.3)

    return paint(f)


def gulch_sand():
    # Moonlit red sand: wind ripples, darker hollows.
    pal = ["#8a4c38", "#9a563e", "#a86246", "#b66e4e", "#c27a58"]
    a, b = noise(4, 2, 5021), noise(8, 4, 5022)

    def f(x, y):
        rip = 0.5 + 0.5 * math.sin((x * 0.5 + y * 1.3) + a(x, y) * 6)
        return pick(pal, 0.15 + rip * 0.3 + b(x, y) * 0.45)

    return paint(f)


def gulch_talus():
    pal = ["#5a3028", "#6c3a2e", "#7e4636", "#904f3c", "#a25c44"]
    a = noise(8, 4, 5031)

    def f(x, y):
        cx, cy = (x // 8) * 8 + 4 + int(a(x - x % 8, y - y % 8) * 3), (y // 8) * 8 + 4
        d = abs(x - cx) + abs(y - cy)
        if d > 5:
            return "#3a2220"
        return pick(pal, 0.2 + a(x, y) * 0.5 + (0.25 if y < cy else 0))

    return paint(f)


def gulch_wash():
    # The ravine floor: pebbly wash, dark cracks, a faint green glow deep in a few.
    pal = ["#5e3a32", "#6c4438", "#7a4e3e", "#885846"]
    a, b = noise(4, 2, 5041), noise(3, 2, 5042)
    peb = speckle(5043, 50)

    def f(x, y):
        v = abs(b(x, y) - 0.5)
        if v < 0.008:
            return "#3ad88a"
        if v < 0.025:
            return "#2a2228"
        if (x, y) in peb:
            return "#a8806a"
        return pick(pal, 0.2 + a(x, y) * 0.7)

    return paint(f)


def graveyard_earth():
    pal = ["#5e4436", "#6a4c3c", "#765642", "#82604a"]
    a, b = noise(4, 2, 5051), noise(16, 8, 5052)
    grass = speckle(5053, 60)

    def f(x, y):
        if (x, y) in grass:
            return "#9a9a62" if (x + y) % 3 else "#7a8a56"
        return pick(pal, 0.2 + a(x, y) * 0.5 + b(x, y) * 0.3)

    return paint(f)


def gulch_chasm():
    # The chasm's floor, far down: dark rock, thin glowing green seams through it.
    a, b = noise(3, 2, 5061), noise(6, 3, 5062)
    c2 = noise(12, 6, 5063)

    def f(x, y):
        v = abs(a(x, y) - 0.5)
        w = abs(b(x, y) - 0.5)
        if v < 0.012 or w < 0.008:
            return "#9affd0"
        if v < 0.03 or w < 0.02:
            return "#24b878"
        if v < 0.05:
            return "#0e3a2a"
        return pick(["#120a18", "#180e20", "#1e1428", "#241a2e"], 0.2 + c2(x, y) * 0.7)

    return paint(f)


def mine_floor():
    # The mine's floor: dark packed earth, spilt ore, the odd green glint.
    pal = ["#3a2a26", "#46322c", "#523a32", "#5e4438"]
    a, b = noise(4, 2, 5071), noise(16, 8, 5072)
    ore = speckle(5073, 30)
    glints = speckle(5074, 6)

    def f(x, y):
        if (x, y) in glints:
            return "#6affb0"
        if (x, y) in ore:
            return "#2a2028"
        return pick(pal, 0.2 + a(x, y) * 0.5 + b(x, y) * 0.3)

    return paint(f)


def mine_rock():
    # The rock inside the mine: dark red-brown, chisel marks, the odd thin glowing vein.
    pal = ["#2e1c1e", "#3a2224", "#46292a", "#523032", "#5e3838"]
    a, b, vein = noise(4, 2, 5081), noise(16, 8, 5082), noise(3, 2, 5083)

    def f(x, y):
        v = abs(vein(x, y) - 0.5)
        if v < 0.01:
            return "#56f0a0"
        if v < 0.022:
            return "#1a5a40"
        chisel = (x + y * 2) % 11 == 0 and b(x, y) > 0.5
        return pick(pal, 0.2 + a(x, y) * 0.45 + b(x, y) * 0.3 - (0.25 if chisel else 0))

    return paint(f)


def fissure_glow():
    # A crack in the rock with the green light pouring out of it.
    a = noise(4, 8, 5091)

    def f(x, y):
        c = abs((x % 64) - 32 - (a(x, y) - 0.5) * 18)
        if c < 2:
            return "#e8fff2"
        if c < 5:
            return "#7affc0"
        if c < 9:
            return "#22c47c"
        if c < 14:
            return "#0e5a3a"
        return "#14100e"

    return paint(f)


def siding(base, light, dark, seed):
    """Weathered clapboard: horizontal boards, each its own shade, peeling paint over grey
    wood, nail lines, cracks."""

    def make():
        a, b = noise(2, 8, seed), noise(8, 4, seed + 1)
        peel = noise(6, 4, seed + 2)
        pal = [dark, base, light]

        def f(x, y):
            board = y // 4
            if y % 4 == 3:
                return "#1c1410"
            if x % 32 == (board * 13) % 32 and y % 4 == 1:
                return "#2a2420"
            if peel(x, y) > 0.76:
                return pick(["#5a5048", "#6a6058", "#7a7066"], 0.3 + a(x, y) * 0.6)
            g = 0.5 + 0.5 * math.sin(x * 0.3 + board * 1.7 + a(x, y) * 4)
            return pick(pal, 0.2 + g * 0.35 + b(x, y) * 0.35 - (0.25 if y % 4 == 0 else 0))

        return paint(f)

    return make


def board_walk():
    pal = ["#5a3e28", "#664830", "#725238", "#7e5c40"]
    a = noise(2, 8, 5111)

    def f(x, y):
        if y % 5 == 4:
            return "#24180e"
        if x % 16 == ((y // 5) * 7) % 16 and y % 5 == 2:
            return "#1a1410"
        return pick(pal, 0.2 + a(x, y) * 0.7)

    return paint(f)


def shingle_roof():
    pal = ["#3a2c2a", "#463430", "#523c36", "#5e463e"]
    a = noise(4, 8, 5121)
    gaps = speckle(5122, 10)

    def f(x, y):
        row = y // 4
        if y % 4 == 3:
            return "#1a1210"
        if (x + row * 3) % 6 == 0:
            return "#241a16"
        if (x // 6, row) in {(gx // 6, gy // 4) for gx, gy in gaps}:
            return "#120c0a"
        return pick(pal, 0.15 + a(x, y) * 0.8)

    return paint(f)


def tin_roof():
    # Corrugated tin, rusting.
    a, b = noise(4, 4, 5131), noise(8, 8, 5132)

    def f(x, y):
        rib = 0.5 + 0.5 * math.sin(x * 0.8)
        if b(x, y) > 0.62:
            return pick(["#6a3018", "#8a4020", "#a45428"], a(x, y))
        return pick(["#4a4a52", "#5c5c64", "#707078", "#86868c"], 0.1 + rib * 0.6 + a(x, y) * 0.2)

    return paint(f)


def window_lit():
    # A lit window: four warm panes in a dark frame, a ragged curtain drawn half across.
    a = noise(2, 2, 5141)

    def f(x, y):
        if x < 3 or x > 60 or y < 2 or y > 29 or x in (31, 32) or y in (15, 16):
            return "#2a1a10"
        if x < 9 or x > 54:
            return "#8a2a22" if (y // 3) % 2 else "#6a1e18"
        glow = 1.0 - abs(y - 16) / 18.0
        return pick(["#ff9030", "#ffa844", "#ffc060", "#ffd88a"], 0.2 + glow * 0.5 + a(x, y) * 0.25)

    return paint(f)


def window_ghost():
    # A window glowing the wrong colour: cold green light behind cracked panes.
    a = noise(2, 2, 5151)

    def f(x, y):
        if x < 3 or x > 60 or y < 2 or y > 29 or x in (31, 32) or y in (15, 16):
            return "#141a14"
        if abs((x - y * 2) % 41) == 0:
            return "#e8fff0"
        glow = 1.0 - abs(y - 16) / 18.0
        return pick(["#14a86a", "#28c884", "#4ae0a0", "#9af4c8"], 0.15 + glow * 0.5 + a(x, y) * 0.3)

    return paint(f)


def window_dark():
    # A dead window: dark panes, a broken one, boards nailed across.
    a = noise(2, 2, 5161)

    def f(x, y):
        if 9 <= y <= 13 or 20 <= y <= 24:
            if x % 20 == 7:
                return "#1a1410"
            return pick(["#5a4030", "#6a4c38", "#7a5640"], a(x, y))
        if x < 3 or x > 60 or y < 2 or y > 29 or x in (31, 32) or y in (15, 16):
            return "#1e1612"
        if x > 33 and y < 15 and (x - 33) + y > 18:
            return "#080608"
        return pick(["#141824", "#1c2230", "#262c3c"], 0.2 + a(x, y) * 0.6 + (0.3 if (x - y) % 23 == 0 else 0))

    return paint(f)


def door_wood():
    a = noise(2, 8, 5171)

    def f(x, y):
        if x < 2 or x > 61 or y < 1:
            return "#1a120c"
        if x in (31, 32):
            return "#22160e"
        if 4 <= y <= 13 and (6 <= x <= 26 or 37 <= x <= 57):
            return pick(["#3a2616", "#442e1c"], a(x, y))
        if y in (20, 21) and x in (27, 36):
            return "#c8a050"
        return pick(["#4e3420", "#5a3e28", "#664830"], 0.2 + a(x, y) * 0.7)

    return paint(f)


def lantern_glass():
    a = noise(4, 2, 5181)

    def f(x, y):
        if x % 16 < 2 or y < 2 or y > 29:
            return "#22180e"
        hot = 1 - abs(y - 17) / 15
        return pick(["#ff8a20", "#ffa030", "#ffbc50", "#ffd880", "#fff0c0"], 0.1 + hot * 0.65 + a(x, y) * 0.25)

    return paint(f)


def lantern_green():
    a = noise(4, 2, 5191)

    def f(x, y):
        if x % 16 < 2 or y < 2 or y > 29:
            return "#0e1a14"
        hot = 1 - abs(y - 17) / 15
        return pick(["#14a060", "#22c47c", "#48e09c", "#8cf4c4", "#e0fff0"], 0.1 + hot * 0.65 + a(x, y) * 0.25)

    return paint(f)


def iron():
    a = noise(8, 4, 5201)

    def f(x, y):
        if a(x, y) > 0.7:
            return pick(["#5a2a14", "#743818"], a(x, y) * 3 % 1)
        return pick(["#1e1c20", "#28262a", "#323034", "#3c3a3e"], 0.2 + a(x, y) * 0.7)

    return paint(f)


def mine_timber():
    # The mine's timbers: old, dark, split, with iron straps.
    pal = ["#2e2018", "#3a281c", "#463022", "#523a28"]
    a, b = noise(2, 8, 5211), noise(8, 16, 5212)

    def f(x, y):
        if y % 32 in (6, 7):
            return "#1a1818"
        if y % 32 == 6 and x % 8 == 3:
            return "#6a6460"
        grain = 0.5 + 0.5 * math.sin(x * 1.3 + a(x, y) * 6)
        if grain < 0.08:
            return "#140e0a"
        return pick(pal, 0.15 + grain * 0.45 + b(x, y) * 0.35)

    return paint(f)


def rail_iron():
    a = noise(8, 2, 5221)

    def f(x, y):
        if y < 6:
            return pick(["#8a8a92", "#a0a0a8"], a(x, y))
        return pick(["#3a2a24", "#4a3226", "#5a3a28", "#6e4428"], 0.2 + a(x, y) * 0.7)

    return paint(f)


def spectral_mist():
    # A drifting sheet of ghostly green mist (see-through, glowing).
    a, b = noise(4, 2, 5231), noise(8, 4, 5232)

    def f(x, y):
        v = a(x, y) * 0.6 + b(x, y) * 0.4
        fade = 1.0 - abs(y - 16) / 16.0
        return pick(["#06140e", "#0e3a28", "#16684a", "#28a070", "#5ad8a4", "#a8f8d4"], v * 0.6 + fade * 0.45)

    return paint(f)


def tombstone():
    pal = ["#5a5a62", "#6a6a72", "#7a7a82", "#8a8a90", "#9a9aa0"]
    a, b = noise(4, 2, 5241), noise(16, 8, 5242)
    moss = noise(6, 3, 5243)

    def f(x, y):
        if moss(x, y) > 0.7:
            return pick(["#3a4a30", "#4a5a38"], b(x, y))
        if abs(a(x, y) - 0.5) < 0.02:
            return "#3a3a40"
        return pick(pal, 0.2 + a(x, y) * 0.4 + b(x, y) * 0.35)

    return paint(f)


def dead_wood():
    pal = ["#3a3230", "#4a403a", "#5a4e46", "#6a5c52", "#7a6c60"]
    a, b = noise(2, 8, 5251), noise(8, 16, 5252)

    def f(x, y):
        grain = 0.5 + 0.5 * math.sin(x * 1.1 + a(x, y) * 7)
        if grain < 0.1:
            return "#1e1816"
        return pick(pal, 0.15 + grain * 0.5 + b(x, y) * 0.3)

    return paint(f)


def canvas_torn():
    # Old wagon and awning canvas: off-white, stained, patched, frayed edge.
    pal = ["#9a9080", "#aaa08e", "#b8ae9a", "#c6bca6"]
    a, b = noise(4, 2, 5261), noise(8, 4, 5262)

    def f(x, y):
        if y >= 28 and (x * 7) % 5 < 2:
            return "#2a2018"
        if 10 <= x <= 22 and 6 <= y <= 15:
            return pick(["#7a5a3a", "#8a6a48"], a(x, y))
        return pick(pal, 0.15 + a(x, y) * 0.4 + b(x, y) * 0.4 - (0.3 if b(x, y) > 0.72 else 0))

    return paint(f)


def barrel_wood():
    a = noise(2, 8, 5271)

    def f(x, y):
        if y in (5, 6, 25, 26):
            return "#2a2626"
        if x % 8 == 0:
            return "#24180e"
        return pick(["#5a3a22", "#664428", "#724e30", "#7e5838"], 0.2 + a(x, y) * 0.7)

    return paint(f)


def clock_face():
    # The clock tower's face, stopped long ago: cream dial, black ticks, the hands at
    # a quarter to midnight.
    w = h = 64

    def f(x, y):
        dx, dy = x - 31.5, y - 31.5
        r = math.hypot(dx, dy)
        if r > 31:
            return "#2a1c14"
        if r > 28:
            return "#1a1410"
        a = math.atan2(dy, dx)
        tick = abs(((a / (math.tau / 12)) + 0.5) % 1 - 0.5) < 0.06
        if 22 < r < 27 and tick:
            return "#1a1410"
        # Hour hand to the 12 (up), minute hand to the 9 (left): a quarter to twelve.
        if abs(dx) < 1.6 and -18 < dy < 0:
            return "#141010"
        if abs(dy) < 1.2 and -24 < dx < 0:
            return "#141010"
        if r < 2.5:
            return "#141010"
        crack = abs(dx * 0.6 - dy + 9) < 0.7 and dx > 0
        if crack:
            return "#6a5a40"
        return pick(["#c8b88a", "#d8c89a", "#e4d6aa"], 0.4 + 0.3 * math.sin(x * 0.3) * math.cos(y * 0.2))

    return paint(f, w, h)


def tank_staves():
    a, b = noise(8, 2, 5281), noise(16, 4, 5282)

    def f(x, y):
        if x % 6 == 5:
            return "#20160e"
        if y in (6, 7, 22, 23):
            return "#2a2a2c"
        return pick(["#4a3420", "#563e28", "#624830", "#6e5238"], 0.2 + a(x, y) * 0.4 + b(x, y) * 0.3)

    return paint(f)


def ore_pile():
    a = noise(8, 4, 5291)
    glints = speckle(5292, 14)

    def f(x, y):
        if (x, y) in glints:
            return "#8affc8"
        return pick(["#1e1a1e", "#2a242a", "#363036", "#423a40"], 0.2 + a(x, y) * 0.7)

    return paint(f)


def ghost_sheet():
    # For the ghostly silhouettes painted on glass and rock: soft green-white glow.
    def f(x, y):
        v = 1.0 - abs(y - 16) / 16.0
        return pick(["#2aa070", "#5ad0a0", "#a8f0d0", "#e8fff4"], 0.3 + v * 0.6)

    return paint(f)


THEMES.append(
    {
        "id": "dry_gulch",
        "name": "Dry Gulch Ghost Town",
        "description": "A haunted frontier mining town under an enormous full moon: deep violet and indigo sky, red-rock mesas in moonlight, weathered wooden buildings glowing with warm orange lanterns, and an abandoned mine pouring out an eerie spectral green",
        "environment": {
            "sky": "#1a1040",
            "fog": {"enabled": True, "color": "#3a2a6a", "near": 300, "far": 1700},
            "sun": {"color": "#b8c4ff", "intensity": 1.65, "direction": [-0.22, 0.62, -0.75]},
            "ambient": {"sky": "#8a7ad8", "ground": "#5a3a5a", "intensity": 1.55},
            "skyDome": {
                "top": "#0a0626",
                "horizon": "#a0388c",
                "bottom": "#2a1a4a",
                "sun": {"color": "#f4f2ea", "size": 10, "glow": "#9ab0ff", "elevation": 21, "face": "moon"},
                "clouds": {"count": 22, "color": "#5a3e8a", "shade": "#2a1a52", "seed": 151, "low": 4, "high": 30, "drift": 0.004},
                "hills": {"color": "#2a1630", "far": "#5a2e5e", "height": 7, "seed": 157, "layers": 3, "style": "mesas"},
                "stars": {"count": 700, "color": "#ffffff", "seed": 163, "low": 12},
                "skull": {"azimuth": 52, "elevation": 32, "size": 34, "color": "#6a4e9a", "shade": "#2c1c58", "period": 46},
            },
        },
    }
)

WOOD_SIGN = ("#4a3220", "#5a3e28", "#6a4a30", "#7a5636")


def sign_tiles(sid, name, text, w, h, kw):
    """A sign's library entries: the board painted whole, cut into 64 px tiles
    ("<id>_1", "<id>_2", ...), each one tile metre per 64 px."""
    n = max(1, w // 64)
    out = []
    for k in range(n):
        def painter(k=k):
            return sign_board(text, w, h, **kw).crop((k * 64, 0, k * 64 + 64, h))

        out.append(("%s_%d" % (sid, k + 1), "Sign: %s (%d/%d)" % (name, k + 1, n), "dry_gulch", "wall", painter, 2, None))
    return out
RED_SIGN = ("#5a1e18", "#6a241c", "#782a20", "#863226")
GREEN_SIGN = ("#1e3a2a", "#244630", "#2a5238", "#305e40")
GLOW = lambda g: {"scrollU": 0, "scrollV": 0, "glow": g}  # noqa: E731

GULCH_MATERIALS = [
    ("gulch_road", "Ghost Town Dirt Road", "dry_gulch", "packed_dirt", gulch_road, 6, None),
    ("gulch_verge", "Dirt Verge (Night)", "dry_gulch", "dirt", gulch_verge, 4, None),
    ("gulch_sand", "Red Sand (Night)", "dry_gulch", "loose_sand", gulch_sand, 8, None),
    ("gulch_talus", "Ravine Rubble", "dry_gulch", "loose_sand", gulch_talus, 6, None),
    ("gulch_wash", "Ravine Wash", "dry_gulch", "dirt", gulch_wash, 8, GLOW(0.08)),
    ("graveyard_earth", "Graveyard Earth", "dry_gulch", "dirt", graveyard_earth, 5, None),
    ("gulch_chasm", "Glowing Chasm Floor", "dry_gulch", "abyss", gulch_chasm, 22, {"scrollU": 0, "scrollV": 0, "glow": 0.7, "pulse": 0.4, "pulsePeriod": 5.0}),
    ("mine_floor", "Mine Floor", "dry_gulch", "packed_dirt", mine_floor, 5, GLOW(0.06)),
    ("mine_rock", "Mine Rock", "dry_gulch", "wall", mine_rock, 12, {"scrollU": 0, "scrollV": 0, "glow": 0.12, "pulse": 0.3, "pulsePeriod": 6.0}),
    ("fissure_glow", "Glowing Fissure", "dry_gulch", "wall", fissure_glow, 6, {"scrollU": 0, "scrollV": 0, "glow": 1.0, "pulse": 0.35, "pulsePeriod": 3.7}),
    ("siding_brown", "Clapboard (Brown)", "dry_gulch", "wall", siding("#6a4a32", "#7e5a3e", "#4e3624", 5301), 4, None),
    ("siding_grey", "Clapboard (Grey)", "dry_gulch", "wall", siding("#6e6660", "#827a72", "#524a46", 5311), 4, None),
    ("siding_red", "Clapboard (Barn Red)", "dry_gulch", "wall", siding("#7a2c24", "#8e382c", "#5a2018", 5321), 4, None),
    ("siding_ochre", "Clapboard (Ochre)", "dry_gulch", "wall", siding("#9a7238", "#ae8444", "#76562a", 5331), 4, None),
    ("siding_green", "Clapboard (Faded Green)", "dry_gulch", "wall", siding("#4a5e4a", "#5a6e56", "#364636", 5341), 4, None),
    ("board_walk", "Boardwalk", "dry_gulch", "road", board_walk, 3, None),
    ("shingle_roof", "Shingle Roof", "dry_gulch", "wall", shingle_roof, 3, None),
    ("tin_roof", "Tin Roof", "dry_gulch", "wall", tin_roof, 3, None),
    ("window_lit", "Lit Window", "dry_gulch", "wall", window_lit, 2, {"scrollU": 0, "scrollV": 0, "glow": 0.95, "flicker": 0.3}),
    ("window_ghost", "Haunted Window", "dry_gulch", "wall", window_ghost, 2, {"scrollU": 0, "scrollV": 0, "glow": 1.0, "pulse": 0.5, "pulsePeriod": 4.4}),
    ("window_dark", "Boarded Window", "dry_gulch", "wall", window_dark, 2, None),
    ("door_wood", "Old Door", "dry_gulch", "wall", door_wood, 2, None),
    ("lantern_glass", "Lantern Glass", "dry_gulch", "wall", lantern_glass, 1, {"scrollU": 0, "scrollV": 0, "glow": 1.3, "flicker": 0.45}),
    ("lantern_green", "Spectral Lantern", "dry_gulch", "wall", lantern_green, 1, {"scrollU": 0, "scrollV": 0, "glow": 1.3, "flicker": 0.35}),
    ("iron", "Old Iron", "dry_gulch", "wall", iron, 2, None),
    ("mine_timber", "Mine Timber", "dry_gulch", "wall", mine_timber, 3, None),
    ("rail_iron", "Mine Rail", "dry_gulch", "wall", rail_iron, 2, None),
    ("spectral_mist", "Spectral Mist", "dry_gulch", "wall", spectral_mist, 16,
     {"scrollU": 0.012, "scrollV": 0.004, "wave": 0.06, "wavePeriod": 9, "opacity": 0.42, "glow": 0.75}),
    ("crystal_ghost", "Spectral Crystal", "dry_gulch", "wall",
     lambda: crystal(5401, ["#0a5a3a", "#128a56", "#22b874", "#58e0a0", "#b4ffdc"], "#ffffff"), 3,
     {"scrollU": 0, "scrollV": 0, "glow": 1.0, "pulse": 0.35, "pulsePeriod": 3.4}),
    ("tombstone", "Weathered Headstone", "dry_gulch", "wall", tombstone, 2, None),
    ("dead_wood", "Dead Wood", "dry_gulch", "wall", dead_wood, 2, None),
    ("canvas_torn", "Torn Canvas", "dry_gulch", "wall", canvas_torn, 3, {"scrollU": 0, "scrollV": 0, "sway": 0.05}),
    ("barrel_wood", "Barrel Staves", "dry_gulch", "wall", barrel_wood, 2, None),
    ("clock_face", "Stopped Clock", "dry_gulch", "wall", clock_face, 2, {"scrollU": 0, "scrollV": 0, "glow": 0.35}),
    ("tank_staves", "Water Tank Staves", "dry_gulch", "wall", tank_staves, 3, None),
    ("ore_pile", "Spectral Ore", "dry_gulch", "wall", ore_pile, 2, {"scrollU": 0, "scrollV": 0, "glow": 0.25}),
    ("ghost_sheet", "Ghost Glow", "dry_gulch", "wall", ghost_sheet, 2, {"scrollU": 0, "scrollV": 0, "glow": 1.2, "opacity": 0.6}),
] + [
    # The painted signs: each a wide board cut into 64 px tiles (the era's texture size),
    # drawn side by side.
    entry
    for sid, name, text, w, h, kw in (
        ("sign_saloon", "Saloon", "SALOON", 128, 32, {"seed": 1}),
        ("sign_general", "General Store", "GENERAL STORE", 192, 32, {"seed": 2}),
        ("sign_hotel", "Hotel", "HOTEL", 128, 32, {"seed": 3, "wood": RED_SIGN}),
        ("sign_sheriff", "Sheriff", "SHERIFF", 128, 32, {"seed": 4}),
        ("sign_jail", "Jail", "JAIL", 64, 32, {"seed": 5}),
        ("sign_bank", "Bank", "BANK", 64, 32, {"seed": 6, "wood": GREEN_SIGN}),
        ("sign_assay", "Assay Office", "ASSAY OFFICE", 192, 32, {"seed": 7}),
        ("sign_livery", "Livery", "LIVERY", 128, 32, {"seed": 8, "wood": RED_SIGN}),
        ("sign_undertaker", "Undertaker", "UNDERTAKER", 192, 32, {"seed": 9, "ink": "#c8d8c0"}),
        ("sign_barber", "Barber", "BARBER", 128, 32, {"seed": 10, "wood": GREEN_SIGN}),
        ("sign_drygulch", "Dry Gulch", "DRY GULCH", 256, 48, {"seed": 11}),
        ("sign_ghosttown", "Ghost Town", "GHOST TOWN", 256, 32, {"seed": 12, "ink": "#f4c870"}),
        ("sign_hazard", "Hazard Mine", "HAZARD MINE", 256, 48, {"seed": 13}),
        ("sign_keepout", "Keep Out", "KEEP OUT!", 128, 32, {"seed": 14, "wood": RED_SIGN}),
        ("sign_finish", "Finish", "FINISH", 128, 32, {"seed": 15}),
        ("sign_shaft", "Shaft No 9", "SHAFT NO.9", 192, 32, {"seed": 16}),
    )
    for entry in sign_tiles(sid, name, text, w, h, kw)
]


# id, name, theme, surface, painter, tileMetres, fx
MATERIALS = [
    ("oasis_paving", "Oasis Flagstones", "oasis_haven", "road", oasis_paving, 5, None),
    ("palace_paving", "Palace Flagstones", "oasis_haven", "road", palace_paving, 8, None),
    ("tile_border", "Blue Tile Border", "oasis_haven", "road", tile_border, 4, None),
    ("balustrade", "Balustrade", "oasis_haven", "wall", balustrade, 3, None),
    ("market_rail", "Market Railing", "oasis_haven", "wall", market_rail, 3, None),
    ("oasis_stone", "Cream Sandstone", "oasis_haven", "wall", oasis_stone, 5, None),
    ("oasis_arcade", "Arcade Façade", "oasis_haven", "wall", oasis_arcade, 8, None),
    ("oasis_windows", "Window Façade", "oasis_haven", "wall", oasis_windows, 8, None),
    ("arcade_rose", "Arcade Façade (Rose)", "oasis_haven", "wall", lambda: oasis_arcade("#f4cbb4", "#1fa6a8", "#5a2a4a"), 8, None),
    ("windows_rose", "Window Façade (Rose)", "oasis_haven", "wall", lambda: oasis_windows("#f4cbb4", "#2e66cc"), 8, None),
    ("arcade_white", "Arcade Façade (White)", "oasis_haven", "wall", lambda: oasis_arcade("#f8f4ea", "#2e66cc", "#2a3a6a"), 8, None),
    ("windows_white", "Window Façade (White)", "oasis_haven", "wall", lambda: oasis_windows("#f8f4ea", "#e8a020"), 8, None),
    ("arcade_ochre", "Arcade Façade (Ochre)", "oasis_haven", "wall", lambda: oasis_arcade("#eebc78", "#c8302a", "#4a2a2a"), 8, None),
    ("windows_ochre", "Window Façade (Ochre)", "oasis_haven", "wall", lambda: oasis_windows("#eebc78", "#1fa6a8"), 8, None),
    ("dome_blue", "Royal Blue Dome", "oasis_haven", "wall", dome_blue, 6, {"scrollU": 0, "scrollV": 0, "glow": 0.08}),
    ("dome_teal", "Turquoise Dome", "oasis_haven", "wall", dome_teal, 6, {"scrollU": 0, "scrollV": 0, "glow": 0.08}),
    ("gold_leaf", "Gold Leaf", "oasis_haven", "wall", gold_leaf, 2, {"scrollU": 0, "scrollV": 0, "glow": 0.3}),
    ("lagoon", "Lagoon Water", "oasis_haven", "deep_water", lagoon, 14, {"scrollU": 0.004, "scrollV": 0.006, "wave": 0.04, "wavePeriod": 7, "lagoon": 1.0}),
    ("lagoon_shallow", "Lagoon Shallows", "oasis_haven", "water", lagoon, 14, {"scrollU": 0.004, "scrollV": 0.006, "wave": 0.04, "wavePeriod": 7, "lagoon": 1.0}),
    ("canal_water", "Canal Water", "oasis_haven", "deep_water", lagoon, 10, {"scrollU": 0.0, "scrollV": 0.08, "wave": 0.03, "wavePeriod": 4, "lagoon": 0.6}),
    ("shore_foam", "Shore Foam", "oasis_haven", "water", shore_foam, 8, {"scrollU": 0.05, "scrollV": 0.0, "wave": 0.08, "wavePeriod": 3.2, "opacity": 0.75, "glow": 0.3}),
    ("lake_sand", "Lake Bed", "oasis_haven", "water", lake_sand, 8, None),
    ("gold_sand", "Golden Sand", "oasis_haven", "loose_sand", gold_sand, 8, None),
    ("adobe", "Mud-brick Plaster", "oasis_haven", "wall", adobe, 4, None),
    ("adobe_dark", "Mud-brick in Shade", "oasis_haven", "wall", adobe_dark, 4, None),
    ("tent_cloth", "Goat-hair Tent Cloth", "oasis_haven", "wall", tent_cloth, 4, {"scrollU": 0, "scrollV": 0, "sway": 0.04}),
    ("tent_cloth_red", "Red Tent Cloth", "oasis_haven", "wall", tent_cloth_red, 4, {"scrollU": 0, "scrollV": 0, "sway": 0.04}),
    ("dune_crest", "Dune Ripples", "oasis_haven", "loose_sand", dune_crest, 10, None),
    ("gold_cliff", "Golden Cliffs", "oasis_haven", "wall", gold_cliff, 14, None),
    ("oasis_lawn", "Garden Lawn", "oasis_haven", "grass", oasis_lawn, 5, None),
    ("garden_soil", "Garden Path", "oasis_haven", "dirt", garden_soil, 5, None),
    ("bougainvillea", "Bougainvillea", "oasis_haven", "wall", bougainvillea, 2, {"scrollU": 0, "scrollV": 0, "sway": 0.12}),
    ("hedge", "Hedge", "oasis_haven", "wall", hedge, 2, None),
    ("awning_sun", "Awning (Red & Gold)", "oasis_haven", "wall", stripes(["#e02a2a", "#f6c03a"]), 3, {"scrollU": 0, "scrollV": 0, "sway": 0.06}),
    ("awning_sea", "Awning (Blue & White)", "oasis_haven", "wall", stripes(["#2a6ad8", "#f6f2e6"]), 3, {"scrollU": 0, "scrollV": 0, "sway": 0.06}),
    ("awning_teal", "Awning (Teal & Orange)", "oasis_haven", "wall", stripes(["#16a8a0", "#ff8a2a"]), 3, {"scrollU": 0, "scrollV": 0, "sway": 0.06}),
    ("awning_rose", "Awning (Pink & Yellow)", "oasis_haven", "wall", stripes(["#e8388a", "#ffe050"]), 3, {"scrollU": 0, "scrollV": 0, "sway": 0.06}),
    ("oasis_banner", "Oasis Banner", "oasis_haven", "wall", oasis_banner, 3, {"scrollU": 0, "scrollV": 0, "sway": 0.1}),
    ("chevron_red", "Chevron Sign (Red)", "oasis_haven", "wall", chevron_red, 3, {"scrollU": 0, "scrollV": 0, "glow": 0.25}),
    ("terracotta", "Painted Terracotta", "oasis_haven", "wall", terracotta, 2, None),
    ("rug", "Market Rug", "oasis_haven", "wall", rug, 3, None),
    ("fruit", "Market Produce", "oasis_haven", "wall", fruit, 2, None),
    ("wood_dock", "Dock Planks", "oasis_haven", "road", wood_dock, 3, None),
    ("oasis_frond", "Swaying Palm Frond", "oasis_haven", "wall", palm_frond, 3, {"scrollU": 0, "scrollV": 0, "sway": 0.3}),
    ("oasis_bark", "Palm Trunk", "oasis_haven", "wall", palm_bark, 2, None),
    ("fountain_jet", "Fountain Jet", "oasis_haven", "water", falls_dash, 3, {"scrollU": 0.0, "scrollV": -1.8, "wave": 0.04, "wavePeriod": 0.7, "opacity": 0.8, "glow": 0.35}),
    ("falls_oasis", "Oasis Falls", "oasis_haven", "water", falls_dash, 6, {"scrollU": 0.0, "scrollV": 1.3, "wave": 0.03, "wavePeriod": 1.2, "opacity": 0.92, "glow": 0.3}),
    ("falls_curtain_oasis", "Oasis Falls Curtain", "oasis_haven", "water", falls_dash, 6, {"scrollU": 0.0, "scrollV": 1.1, "wave": 0.03, "wavePeriod": 1.5, "opacity": 0.55, "glow": 0.35}),
    ("dash_road", "Canyon Dirt Road", "canyon_dash", "packed_dirt", dash_road, 6, None),
    ("dash_shoulder", "Dirt Verge", "canyon_dash", "dirt", dash_shoulder, 4, None),
    ("desert_sand", "Red Sand", "canyon_dash", "loose_sand", desert_sand, 8, None),
    ("slickrock", "Slickrock", "canyon_dash", "dirt", slickrock, 10, None),
    ("red_sand", "Red Sand (Deep)", "canyon_dash", "loose_sand", red_sand, 8, None),
    ("pale_sand", "Pale Sand", "canyon_dash", "loose_sand", pale_sand, 8, None),
    ("strata_cream", "Caprock Sandstone", "canyon_dash", "wall", strata_cream, 14, None),
    ("strata_orange", "Orange Sandstone", "canyon_dash", "wall", strata_orange, 14, None),
    ("strata_red", "Red Sandstone", "canyon_dash", "wall", strata_red, 14, None),
    ("strata_rust", "Red Shale", "canyon_dash", "wall", strata_rust, 12, None),
    ("strata_purple", "Canyon Base Rock", "canyon_dash", "wall", strata_purple, 12, None),
    ("talus", "Talus", "canyon_dash", "wall", talus, 8, None),
    ("canyon_river", "Turquoise River", "canyon_dash", "water", canyon_river, 12, {"scrollU": 0.0, "scrollV": 0.12, "wave": 0.03, "wavePeriod": 5, "glow": 0.15}),
    ("falls_dash", "Canyon Falls", "canyon_dash", "water", falls_dash, 7, {"scrollU": 0.0, "scrollV": 1.2, "wave": 0.03, "wavePeriod": 1.3, "opacity": 0.92, "glow": 0.25}),
    ("canyon_mist", "Falls Mist", "canyon_dash", "water", canyon_mist, 20, {"scrollU": 0.01, "scrollV": -0.03, "wave": 0.08, "wavePeriod": 5, "opacity": 0.4, "glow": 0.3}),
    ("weathered_timber", "Weathered Timber", "canyon_dash", "wall", weathered_timber, 3, None),
    ("fence_rail", "Ranch Fence", "canyon_dash", "wall", fence_rail, 4, None),
    ("plank_deck", "Bridge Planks", "canyon_dash", "road", plank_deck, 4, None),
    ("masonry", "Sandstone Masonry", "canyon_dash", "wall", masonry, 4, None),
    ("saguaro", "Saguaro", "canyon_dash", "wall", saguaro, 1.5, None),
    ("agave", "Agave", "canyon_dash", "wall", agave, 1.5, None),
    ("sagebrush", "Sagebrush", "canyon_dash", "grass", sagebrush, 2, None),
    ("dry_grass", "Dry Grass", "canyon_dash", "grass", dry_grass, 1.5, None),
    ("chevron_amber", "Chevron Sign (Amber)", "canyon_dash", "wall", chevron_amber, 3, {"scrollU": 0, "scrollV": 0, "glow": 0.35}),
    ("windmill_blade", "Windmill Vane", "canyon_dash", "wall", windmill_blade, 3, None),
    ("canvas_sun", "Race Banner (Red)", "canyon_dash", "wall", canvas_sun, 3, None),
    ("canvas_blue", "Race Banner (Blue)", "canyon_dash", "wall", canvas_blue, 3, None),
    ("desert_haze", "Distant Mesa", "canyon_dash", "wall", desert_haze, 40, None),
    ("rift_road", "Glacier Road", "aurora_rift", "snow_stone", rift_road, 6, {"scrollU": 0, "scrollV": 0, "glow": 0.08}),
    ("rift_ice_road", "Clear Ice Track", "aurora_rift", "icy_stone", rift_ice_road, 5, {"scrollU": 0, "scrollV": 0, "glow": 0.22}),
    ("mirror_ice", "Mirror Ice", "aurora_rift", "ice", mirror_ice, 16, {"scrollU": 0, "scrollV": 0, "glow": 0.3, "opacity": 0.7}),
    ("thin_ice", "Thin Ice", "aurora_rift", "ice", thin_ice, 7, {"scrollU": 0, "scrollV": 0, "glow": 0.3, "opacity": 0.85}),
    ("rift_snow", "Night Snow", "aurora_rift", "deep_snow", rift_snow, 6, None),
    ("rift_rock", "Indigo Rock", "aurora_rift", "wall", rift_rock, 9, None),
    ("rift_cliff", "Rift Cliff", "aurora_rift", "wall", rift_cliff, 12, None),
    ("glacier_wall", "Glacier Ice Wall", "aurora_rift", "wall", glacier_wall, 16, {"scrollU": 0, "scrollV": 0, "glow": 0.12}),
    ("cavern_ice", "Crystal-Veined Ice", "aurora_rift", "wall", cavern_ice, 14, {"scrollU": 0, "scrollV": 0, "glow": 0.08}),
    ("rift_stone", "Frosted Slate", "aurora_rift", "wall", rift_stone, 4, None),
    ("rift_carved", "Rune Stones", "aurora_rift", "wall", rift_carved, 4, {"scrollU": 0, "scrollV": 0, "glow": 0.45}),
    ("crystal_cyan", "Rift Crystal (Cyan)", "aurora_rift", "wall",
     lambda: crystal(3271, ["#0a7aa4", "#14a2c8", "#2ac8e6", "#64e4f6", "#b4f6ff"], "#ffffff"), 3,
     {"scrollU": 0, "scrollV": 0, "glow": 1.0, "pulse": 0.35, "pulsePeriod": 3.2}),
    ("crystal_violet2", "Rift Crystal (Violet)", "aurora_rift", "wall",
     lambda: crystal(3272, ["#3a1a8a", "#5428b0", "#7040d2", "#9a6cee", "#d0b0ff"], "#f8eeff"), 3,
     {"scrollU": 0, "scrollV": 0, "glow": 0.95, "pulse": 0.4, "pulsePeriod": 4.1}),
    ("crystal_magenta", "Rift Crystal (Magenta)", "aurora_rift", "wall",
     lambda: crystal(3273, ["#7a1464", "#a0207e", "#c83a9c", "#ea6cc0", "#ffb4e4"], "#fff0fa"), 3,
     {"scrollU": 0, "scrollV": 0, "glow": 0.9, "pulse": 0.3, "pulsePeriod": 5.3}),
    ("crystal_teal", "Rift Crystal (Teal)", "aurora_rift", "wall",
     lambda: crystal(3274, ["#0a6a6a", "#128a86", "#22b0a4", "#58d4c4", "#aaf4e8"], "#f0fffc"), 3,
     {"scrollU": 0, "scrollV": 0, "glow": 0.9, "pulse": 0.3, "pulsePeriod": 3.9}),
    ("crystal_gold", "Rift Crystal (Amber)", "aurora_rift", "wall",
     lambda: crystal(3275, ["#a05a10", "#c87818", "#e89a2a", "#ffc050", "#ffe6a0"], "#fffbe8"), 3,
     {"scrollU": 0, "scrollV": 0, "glow": 1.1, "pulse": 0.2, "pulsePeriod": 2.7}),
    ("monolith_core", "Monolith Crystal", "aurora_rift", "wall",
     lambda: crystal(3276, ["#2a8ad8", "#3cacec", "#62ccf8", "#9ae6ff", "#e0fbff"], "#ffffff"), 14,
     {"scrollU": 0, "scrollV": 0, "glow": 1.15, "pulse": 0.25, "pulsePeriod": 6.0}),
    ("lantern_amber", "Lantern Glass", "aurora_rift", "wall", lantern_amber, 1, {"scrollU": 0, "scrollV": 0, "wave": 0.02, "wavePeriod": 0.6, "glow": 1.2}),
    ("edge_amber", "Edge Lamps", "aurora_rift", "wall", edge_amber, 4, {"scrollU": 0, "scrollV": 0, "glow": 0.5}),
    ("icefall_rift", "Frozen Falls", "aurora_rift", "wall", icefall_rift, 8, {"scrollU": 0, "scrollV": 0, "glow": 0.18}),
    ("falls_rift", "Rift Falls", "aurora_rift", "water", falls_rift, 7, {"scrollU": 0.0, "scrollV": 1.1, "wave": 0.03, "wavePeriod": 1.4, "opacity": 0.86, "glow": 0.5}),
    ("falls_curtain", "Waterfall Curtain", "aurora_rift", "water", falls_rift, 12, {"scrollU": 0.0, "scrollV": 0.8, "wave": 0.03, "wavePeriod": 1.8, "opacity": 0.6, "glow": 0.55}),
    ("rift_mist", "Rift Mist", "aurora_rift", "water", rift_mist, 30, {"scrollU": 0.004, "scrollV": 0.002, "wave": 0.06, "wavePeriod": 9, "opacity": 0.24, "glow": 0.6}),
    ("rift_roof", "Glittering Roof", "aurora_rift", "wall", rift_roof, 10, {"scrollU": 0, "scrollV": 0, "glow": 0.55}),
    ("abyss_glow", "Abyss Floor", "aurora_rift", "abyss", abyss_glow, 14, {"scrollU": 0, "scrollV": 0, "glow": 0.6}),
    ("abyss_fog", "Abyss Fog", "aurora_rift", "water", abyss_fog, 40, {"scrollU": -0.003, "scrollV": 0.004, "wave": 0.05, "wavePeriod": 12, "opacity": 0.26, "glow": 0.5}),
    ("hearth_cobble", "Village Cobbles", "hearthglow", "snow_stone", hearth_cobble, 3.5, None),
    ("icy_cobble", "Icy Cobbles", "hearthglow", "icy_stone", icy_cobble, 3.5, {"scrollU": 0, "scrollV": 0, "glow": 0.15}),
    ("hearth_stone", "Village Stone", "hearthglow", "wall", hearth_stone, 4, None),
    ("river_ice", "River Ice", "hearthglow", "ice", river_ice, 8, {"scrollU": 0, "scrollV": 0, "glow": 0.3}),
    ("river_ice_road", "River Ice Track", "hearthglow", "icy_stone", river_ice_road, 5, {"scrollU": 0, "scrollV": 0, "glow": 0.2}),
    ("timber_rail", "Fence with Lights", "hearthglow", "wall", timber_rail, 3, None),
    ("timber_beam", "Timber", "hearthglow", "wall", timber_beam, 3, None),
    ("cabin_wall", "Log Wall", "hearthglow", "wall", cabin_wall, 3, None),
    ("cabin_plaster", "Half-Timbering", "hearthglow", "wall", cabin_plaster, 4, None),
    ("window_warm", "Glowing Window", "hearthglow", "wall", window_warm, 2, {"scrollU": 0, "scrollV": 0, "glow": 1.0}),
    ("brick", "Chimney Brick", "hearthglow", "wall", brick, 2, None),
    ("awning_red", "Awning (Red)", "hearthglow", "wall", awning_red, 2, None),
    ("awning_green", "Awning (Green)", "hearthglow", "wall", awning_green, 2, None),
    ("candy_stripe", "Candy Stripe", "hearthglow", "wall", candy_stripe, 1.5, None),
    ("wrap_red", "Gift Wrap (Red)", "hearthglow", "wall", lambda: wrap("#d02434", "#a01a28", "#f6d040", 2751), 3, None),
    ("wrap_green", "Gift Wrap (Green)", "hearthglow", "wall", lambda: wrap("#2a9a48", "#1e7636", "#f6f0e0", 2752), 3, None),
    ("wrap_gold", "Gift Wrap (Gold)", "hearthglow", "wall", lambda: wrap("#f0b428", "#c88e18", "#d02434", 2753), 3, None),
    ("wrap_blue", "Gift Wrap (Blue)", "hearthglow", "wall", lambda: wrap("#3068d8", "#2250a8", "#f6f0e0", 2754), 3, None),
    ("wreath", "Holly", "hearthglow", "wall", wreath, 1.5, None),
    ("xmas_lights", "Christmas Lights", "hearthglow", "wall", xmas_lights, 3, {"scrollU": 0.35, "scrollV": 0, "glow": 1.0}),
    ("banner_tree", "Christmas Banner", "hearthglow", "wall", banner_tree, 3, None),
    ("gold_trim", "Gold Trim", "hearthglow", "wall", gold_trim, 2, {"scrollU": 0, "scrollV": 0, "glow": 0.45}),
    ("star_gold", "Golden Star", "hearthglow", "wall", star_gold, 2, {"scrollU": 0, "scrollV": 0, "wave": 0.02, "wavePeriod": 2, "glow": 1.2}),
    ("carrot", "Carrot", "hearthglow", "wall", carrot, 1, None),
    ("pine_night", "Snow-Laden Pine", "hearthglow", "grass", pine_night, 2, None),
    ("summit_snow", "Sunny Snow", "summit_pass", "deep_snow", summit_snow, 6, None),
    ("summit_road", "Groomed Snow Road", "summit_pass", "packed_snow", summit_road, 5, None),
    ("summit_stone_road", "Swept Cobbles", "summit_pass", "snow_stone", summit_stone_road, 3.5, None),
    ("crystal_road", "Ice Cave Floor", "summit_pass", "snow_stone", crystal_road, 5, None),
    ("lake_ice", "Lake Ice", "summit_pass", "ice", lake_ice, 10, {"scrollU": 0, "scrollV": 0, "glow": 0.2}),
    ("glacier_ice", "Glacier Ice", "summit_pass", "wall", glacier_ice, 9, {"scrollU": 0, "scrollV": 0, "glow": 0.25}),
    ("crystal_blue", "Ice Crystal (Blue)", "summit_pass", "wall", crystal_blue, 2, {"scrollU": 0, "scrollV": 0, "glow": 0.85}),
    ("crystal_violet", "Ice Crystal (Violet)", "summit_pass", "wall", crystal_violet, 2, {"scrollU": 0, "scrollV": 0, "glow": 0.85}),
    ("chevron_sign", "Chevron Sign", "summit_pass", "wall", chevron_sign, 3, {"scrollU": 0, "scrollV": 0, "glow": 0.55}),
    ("summit_rock", "Sunny Granite", "summit_pass", "wall", summit_rock, 9, None),
    ("summit_cliff", "Snowy Granite Cliff", "summit_pass", "wall", summit_cliff, 8, None),
    ("hot_spring", "Hot Spring Water", "summit_pass", "deep_water", hot_spring, 9, {"scrollU": 0.01, "scrollV": 0.03, "wave": 0.05, "wavePeriod": 4, "opacity": 0.9, "glow": 0.3}),
    ("hot_pool", "Hot Pool", "summit_pass", "water", hot_pool, 4, {"scrollU": 0.02, "scrollV": 0.01, "wave": 0.05, "wavePeriod": 3, "opacity": 0.88, "glow": 0.35}),
    ("sinter", "Travertine", "summit_pass", "dirt", sinter, 6, None),
    ("sinter_road", "Travertine Road", "summit_pass", "road", sinter_road, 4, None),
    ("sinter_rim", "Travertine Rim", "summit_pass", "wall", sinter_rim, 2, None),
    ("thaw_grass", "Thawed Meadow", "summit_pass", "grass", thaw_grass, 5, None),
    ("forest_road", "Forest Track", "summit_pass", "dirt", forest_road, 4, None),
    ("giant_bark", "Giant Bark", "summit_pass", "wall", giant_bark, 6, None),
    ("heartwood", "Heartwood", "summit_pass", "wall", heartwood, 4, None),
    ("plank_road", "Plank Road", "summit_pass", "road", plank_road, 4, None),
    ("rope_rail", "Rope Rail", "summit_pass", "wall", rope_rail, 2.5, None),
    ("bunting", "Bunting", "summit_pass", "wall", bunting, 4, None),
    ("pine_bright", "Sunny Pine", "summit_pass", "grass", pine_bright, 2, None),
    ("leaf_bright", "Thawed Canopy", "summit_pass", "grass", leaf_bright, 4, None),
    ("ship_hull", "Ship Hull", "summit_pass", "wall", ship_hull, 3, None),
    ("sail_cloth", "Sailcloth", "summit_pass", "wall", sail_cloth, 4, None),
    ("mammoth_bone", "Mammoth Bone", "summit_pass", "wall", mammoth_bone, 3, None),
    ("frost_stone", "Frost Stone", "summit_pass", "wall", frost_stone, 4, None),
    ("glow_moss", "Glowing Moss", "summit_pass", "wall", glow_moss, 3, {"scrollU": 0, "scrollV": 0, "wave": 0.03, "wavePeriod": 3, "glow": 0.75}),
    ("steam_mist", "Steam", "summit_pass", "wall", steam_mist, 10, {"scrollU": 0.004, "scrollV": -0.05, "wave": 0.05, "wavePeriod": 5, "opacity": 0.42, "glow": 0.5}),
    ("icefall_blue", "Icefall", "summit_pass", "wall", icefall_blue, 6, {"scrollU": 0, "scrollV": 0, "glow": 0.3}),
    ("warm_falls", "Warm Falls", "summit_pass", "water", warm_falls, 6, {"scrollU": 0.0, "scrollV": 1.0, "wave": 0.03, "wavePeriod": 1.4, "opacity": 0.9, "glow": 0.3}),
    ("mammoth_fur", "Mammoth Fur", "summit_pass", "wall", mammoth_fur, 2, None),
    ("basalt_road", "Basalt Road", "volcanic_apocalypse", "road", basalt_road, 4, None),
    ("scorched_ground", "Scorched Ground", "volcanic_apocalypse", "dirt", scorched_ground, 6, None),
    ("ash_soil", "Ash Soil", "volcanic_apocalypse", "sand", ash_soil, 7, None),
    ("magma_rock", "Magma Rock", "volcanic_apocalypse", "wall", magma_rock, 7, {"scrollU": 0, "scrollV": 0, "wave": 0.01, "wavePeriod": 5, "glow": 0.9}),
    ("obsidian", "Obsidian", "volcanic_apocalypse", "wall", obsidian, 5, None),
    ("obsidian_vein", "Obsidian (Veined)", "volcanic_apocalypse", "wall", obsidian_vein, 5, {"scrollU": 0, "scrollV": 0, "glow": 1.0}),
    ("obsidian_cliff", "Volcanic Cliff", "volcanic_apocalypse", "wall", obsidian_cliff, 10, None),
    ("basalt_block", "Basalt Masonry", "volcanic_apocalypse", "wall", basalt_block, 4, None),
    ("basalt_carved", "Basalt Runes", "volcanic_apocalypse", "wall", basalt_carved, 5, {"scrollU": 0, "scrollV": 0, "glow": 0.4}),
    ("cave_rock", "Cave Rock", "volcanic_apocalypse", "wall", cave_rock, 8, None),
    ("lava_falls", "Lava Falls", "volcanic_apocalypse", "lava", lava_falls, 6, {"scrollU": 0.0, "scrollV": 0.6, "wave": 0.03, "wavePeriod": 2, "glow": 1.0}),
    ("crystal_red", "Fire Crystal", "volcanic_apocalypse", "wall", crystal_red, 2, {"scrollU": 0, "scrollV": 0, "glow": 0.85}),
    ("crystal_purple", "Amethyst Crystal", "volcanic_apocalypse", "wall", crystal_purple, 2, {"scrollU": 0, "scrollV": 0, "glow": 0.85}),
    ("charred_bark", "Charred Bark", "volcanic_apocalypse", "wall", charred_bark, 2, {"scrollU": 0, "scrollV": 0, "glow": 0.5}),
    ("burning_leaves", "Burning Foliage", "volcanic_apocalypse", "grass", burning_leaves, 3, {"scrollU": 0.0, "scrollV": -0.15, "wave": 0.05, "wavePeriod": 0.9, "glow": 0.8}),
    ("ash_smoke", "Ash Smoke", "volcanic_apocalypse", "wall", ash_smoke, 20, {"scrollU": 0.004, "scrollV": -0.02, "wave": 0.05, "wavePeriod": 7, "opacity": 0.72}),
    ("fire_glow", "Furnace Glow", "volcanic_apocalypse", "wall", fire_glow, 4, {"scrollU": 0.03, "scrollV": -0.2, "wave": 0.06, "wavePeriod": 1.3, "glow": 1.2}),
    ("bog_water", "Bog Water", "bonebog_swamp", "deep_water", bog_water, 18, {"scrollU": 0.004, "scrollV": 0.01, "wave": 0.04, "wavePeriod": 8, "opacity": 0.94, "glow": 0.18}),
    ("bog_glow_pool", "Glowing Pool", "bonebog_swamp", "deep_water", bog_glow_pool, 7, {"scrollU": 0.02, "scrollV": -0.03, "wave": 0.1, "wavePeriod": 3, "opacity": 0.92, "glow": 0.5}),
    ("bog_mud", "Bog Mud", "bonebog_swamp", "mud", bog_mud, 6, None),
    ("bog_bank", "Swamp Bank", "bonebog_swamp", "grass", bog_bank, 6, None),
    ("bog_moss_ground", "Mossy Ground", "bonebog_swamp", "grass", bog_moss_ground, 5, None),
    ("bog_root", "Root Wood", "bonebog_swamp", "wall", bog_root, 3, None),
    ("bog_boards", "Boardwalk", "bonebog_swamp", "road", bog_boards, 4, None),
    ("bog_rail", "Rope Rail", "bonebog_swamp", "wall", bog_rail, 3, None),
    ("bog_paving", "Mossy Paving", "bonebog_swamp", "road", bog_paving, 4.5, None),
    ("bog_stone", "Pyramid Stone", "bonebog_swamp", "wall", bog_stone, 5, None),
    ("bog_carved", "Pyramid Carvings", "bonebog_swamp", "wall", bog_carved, 3.5, None),
    ("bog_dark_stone", "Damp Stone", "bonebog_swamp", "wall", bog_dark_stone, 4, None),
    ("bog_canopy", "Swamp Canopy", "bonebog_swamp", "grass", bog_canopy, 6, None),
    ("bog_moss_hang", "Hanging Moss", "bonebog_swamp", "grass", bog_moss_hang, 2, None),
    ("cobweb", "Cobweb", "bonebog_swamp", "wall", cobweb, 2, {"scrollU": 0, "scrollV": 0, "opacity": 0.6, "glow": 0.35}),
    ("light_shaft", "Light Shaft", "bonebog_swamp", "wall", light_shaft, 20, {"scrollU": 0.0, "scrollV": 0.01, "wave": 0.04, "wavePeriod": 8, "opacity": 0.09, "glow": 1.0}),
    ("bog_mist", "Swamp Mist", "bonebog_swamp", "water", bog_mist, 30, {"scrollU": 0.005, "scrollV": 0.002, "wave": 0.06, "wavePeriod": 10, "opacity": 0.22, "glow": 0.45}),
    ("bog_bone", "Swamp Bone", "bonebog_swamp", "wall", bog_bone, 3, None),
    ("bog_eye", "Glowing Eye", "bonebog_swamp", "wall", bog_eye, 1, {"scrollU": 0, "scrollV": 0, "wave": 0.04, "wavePeriod": 2.5, "glow": 1.2}),
    ("croc_skin", "Croc Skin", "bonebog_swamp", "wall", croc_skin, 1.5, None),
    ("snow_ground", "Snow", "frost_citadel", "deep_snow", snow_ground, 6, None),
    ("snow_stone_road", "Snowy Stone Road", "frost_citadel", "snow_stone", snow_stone_road, 3.5, None),
    ("icy_stone_road", "Icy Stone Road", "frost_citadel", "icy_stone", icy_stone_road, 5, None),
    ("packed_snow_road", "Packed Snow Road", "frost_citadel", "packed_snow", packed_snow_road, 5, None),
    ("frost_rock", "Frost Rock", "frost_citadel", "wall", frost_rock, 9, None),
    ("frost_cliff", "Snowy Cliff", "frost_citadel", "wall", frost_cliff, 8, None),
    ("citadel_stone", "Citadel Stone", "frost_citadel", "wall", citadel_stone, 4, None),
    ("citadel_carved", "Citadel Carvings", "frost_citadel", "wall", citadel_carved, 3, None),
    ("citadel_dark", "Citadel Stone (Dark)", "frost_citadel", "wall", citadel_dark, 4, None),
    ("temple_gold", "Sun Emblem", "frost_citadel", "wall", temple_gold, 4, {"scrollU": 0, "scrollV": 0, "glow": 0.7}),
    ("banner_red", "Banner (Red)", "frost_citadel", "wall", banner_red, 3, None),
    ("banner_teal", "Banner (Teal)", "frost_citadel", "wall", banner_teal, 3, None),
    ("banner_blue", "Banner (Blue)", "frost_citadel", "wall", banner_blue, 3, None),
    ("ice", "Ice", "frost_citadel", "ice", ice, 4, {"scrollU": 0, "scrollV": 0, "glow": 0.35, "opacity": 0.9}),
    ("frost_falls", "Glacier Falls", "frost_citadel", "water", frost_falls, 6, {"scrollU": 0.0, "scrollV": 1.0, "wave": 0.03, "wavePeriod": 1.4, "opacity": 0.9, "glow": 0.4}),
    ("frost_pool", "Glacier Water", "frost_citadel", "water", frost_pool, 8, {"scrollU": 0.01, "scrollV": 0.04, "wave": 0.04, "wavePeriod": 4, "opacity": 0.88, "glow": 0.25}),
    ("fog_sheet", "Fog", "frost_citadel", "water", fog_sheet, 30, {"scrollU": 0.004, "scrollV": 0.002, "wave": 0.06, "wavePeriod": 9, "opacity": 0.3, "glow": 0.55}),
    ("fog_thin", "Thin Fog", "frost_citadel", "water", fog_sheet, 40, {"scrollU": -0.003, "scrollV": 0.003, "wave": 0.05, "wavePeriod": 11, "opacity": 0.16, "glow": 0.6}),
    ("pine_snow", "Snowy Pine", "frost_citadel", "grass", pine_snow, 2, None),
    ("frond_snow", "Snowy Frond", "frost_citadel", "grass", frond_snow, 3, None),
    ("window_glow", "Firelit Doorway", "frost_citadel", "wall", window_glow, 2, {"scrollU": 0, "scrollV": 0, "wave": 0.03, "wavePeriod": 0.7, "glow": 1.0}),
    ("beach_sand", "Beach Sand", "beach_party", "sand", beach_sand, 6, None),
    ("beach_road", "Packed Sand Road", "beach_party", "road", beach_road, 4, None),
    ("wet_sand", "Wet Sand", "beach_party", "sand", wet_sand, 5, None),
    ("sea_water", "Sea Water", "beach_party", "water", sea_water, 10, {"scrollU": 0.02, "scrollV": 0.03, "wave": 0.05, "wavePeriod": 4, "opacity": 0.86}),
    ("surf_foam", "Surf", "beach_party", "water", surf_foam, 5, {"scrollU": 0.0, "scrollV": 0.12, "wave": 0.12, "wavePeriod": 3.2, "opacity": 0.8, "glow": 0.2}),
    ("party_red", "Party Red", "beach_party", "wall", party_red, 2, None),
    ("party_yellow", "Party Yellow", "beach_party", "wall", party_yellow, 2, None),
    ("party_teal", "Party Teal", "beach_party", "wall", party_teal, 2, None),
    ("party_pink", "Party Pink", "beach_party", "wall", party_pink, 2, None),
    ("party_white", "Party White", "beach_party", "wall", party_white, 2, None),
    ("party_blue", "Party Blue", "beach_party", "wall", party_blue, 2, None),
    ("lantern_glow", "Paper Lantern", "beach_party", "wall", lantern_glow, 1, {"scrollU": 0, "scrollV": 0, "glow": 0.6}),
    ("tiki_wood", "Tiki Wood", "beach_party", "wall", tiki_wood, 2, None),
    ("dino_scales", "Dino Scales", "beach_party", "wall", dino_scales, 1, None),
    ("valley_road", "Valley Road", "river_valley", "road", valley_road, 4, None),
    ("valley_grass", "Valley Grass", "river_valley", "grass", valley_grass, 6, None),
    ("valley_trail", "Valley Trail", "river_valley", "road", valley_trail, 4, None),
    ("valley_sand", "Valley Sand", "river_valley", "sand", valley_sand, 5, None),
    (
        "valley_water",
        "Valley Water",
        "river_valley",
        "water",
        valley_water,
        7,
        {"scrollU": 0.0, "scrollV": 0.09, "wave": 0.05, "wavePeriod": 3, "opacity": 0.82},
    ),
    ("valley_cliff", "Valley Cliff", "river_valley", "wall", valley_cliff, 8, None),
    ("wood_planks", "Wood Planks", "river_valley", "road", wood_planks, 3, None),
    ("palm_bark", "Palm Bark", "river_valley", "wall", palm_bark, 2, None),
    ("palm_frond", "Palm Frond", "river_valley", "wall", palm_frond, 3, None),
    ("thatch", "Thatch", "river_valley", "wall", thatch, 3, None),
    ("tribal_paint", "Painted Wood", "river_valley", "wall", tribal_paint, 3, None),
    ("start_checker", "Start Checker", "river_valley", "road", start_checker, 2, None),
    ("blossom", "Blossom", "river_valley", "grass", blossom, 2, None),
    ("cattail_leaf", "Cattail Leaf", "river_valley", "grass", cattail_leaf, 2, None),
    ("cattail_head", "Cattail Head", "river_valley", "wall", cattail_head, 1, None),
    ("campfire_flame", "Campfire Flame", "river_valley", "wall", campfire_flame, 1.5, {"scrollU": 0.15, "scrollV": -1.2, "wave": 0.08, "wavePeriod": 0.6, "glow": 1.0}),
    ("canopy_bright", "Bright Canopy", "river_valley", "grass", canopy_bright, 4, None),
    ("lily_pad", "Lily Pad", "river_valley", "grass", lily_pad, 4, None),
    ("lotus", "Lotus Petal", "river_valley", "wall", lotus, 1, {"scrollU": 0, "scrollV": 0, "glow": 0.45}),
    ("rainbow", "Rainbow", "river_valley", "wall", rainbow, 8, {"scrollU": 0, "scrollV": 0, "glow": 0.6, "opacity": 0.32}),
    ("falls_sheet", "Falls Sheet", "river_valley", "water", falls_sheet, 6, {"scrollU": 0.0, "scrollV": 1.1, "wave": 0.02, "wavePeriod": 1.4, "opacity": 0.92, "glow": 0.22}),
    ("falls_veil", "Falls Veil", "river_valley", "water", falls_veil, 4, {"scrollU": 0.0, "scrollV": 2.1, "wave": 0.04, "wavePeriod": 0.9, "opacity": 0.5, "glow": 0.3}),
    ("falls_foam", "Falls Foam", "river_valley", "water", falls_foam, 4, {"scrollU": 0.06, "scrollV": 0.2, "wave": 0.07, "wavePeriod": 1.8, "opacity": 0.85, "glow": 0.25}),
    (
        "waterfall",
        "Waterfall",
        "jungle_cascade",
        "water",
        waterfall,
        6,
        {"scrollU": 0.0, "scrollV": 0.9, "wave": 0.02, "wavePeriod": 1.5, "opacity": 0.8},
    ),
    (
        "foam",
        "Foam",
        "jungle_cascade",
        "water",
        foam,
        4,
        {"scrollU": 0.05, "scrollV": 0.12, "wave": 0.06, "wavePeriod": 2, "opacity": 0.75},
    ),
    ("jungle_fern", "Jungle Fern", "jungle_cascade", "grass", jungle_fern, 4, None),
    ("canyon_rock_grey", "Canyon Rock (Grey)", "jungle_cascade", "wall", canyon_rock_grey, 9, None),
    ("canyon_rock_moss", "Canyon Rock (Mossy)", "jungle_cascade", "wall", canyon_rock_moss, 8, None),
    ("canyon_rock_ochre", "Canyon Rock (Ochre)", "jungle_cascade", "wall", canyon_rock_ochre, 10, None),
    ("ruin_stone", "Ruin Stone", "jungle_cascade", "wall", ruin_stone, 4, None),
    ("ruin_glyph", "Ruin Glyphs", "jungle_cascade", "wall", ruin_glyph, 3, None),
    ("ruin_dark", "Ruin Stone (Sooty)", "jungle_cascade", "wall", ruin_dark, 4, None),
    ("jungle_bark", "Jungle Bark", "jungle_cascade", "wall", jungle_bark, 3, None),
    ("canopy_dark", "Deep Canopy", "jungle_cascade", "grass", canopy_dark, 5, None),
    ("big_leaf", "Big Leaf", "jungle_cascade", "grass", big_leaf, 2, None),
    ("vine_leaf", "Vine Leaves", "jungle_cascade", "grass", vine_leaf, 1.5, None),
    ("frog_skin", "Frog Skin", "jungle_cascade", "wall", frog_skin, 0.4, None),
    ("log_end", "Log End", "jungle_cascade", "wall", log_end, 1, None),
    ("torch_glow", "Torch Flame", "jungle_cascade", "wall", torch_glow, 1, {"scrollU": 0.2, "scrollV": -1.6, "wave": 0.1, "wavePeriod": 0.4, "glow": 1.0}),
    ("jungle_mud", "Jungle Mud", "jungle_cascade", "mud", jungle_mud, 5, None),
    ("pterosaur_skin", "Pterosaur Skin", "jungle_cascade", "wall", pterosaur_skin, 2, None),
    ("swamp_mud", "Swamp Mud", "fossil_swamp", "mud", swamp_mud, 5, None),
    (
        "swamp_water",
        "Swamp Water",
        "fossil_swamp",
        "water",
        swamp_water,
        8,
        {"scrollU": 0.006, "scrollV": 0.012, "wave": 0.03, "wavePeriod": 6, "opacity": 0.9},
    ),
    ("swamp_moss", "Swamp Moss", "fossil_swamp", "grass", swamp_moss, 6, None),
    ("bone", "Fossil Bone", "fossil_swamp", "wall", bone, 3, None),
    ("swamp_stone", "Swamp Paving", "fossil_swamp", "road", swamp_stone, 5, None),
    ("glow_cap", "Glow Cap", "fossil_swamp", "wall", glow_cap, 2, {"scrollU": 0, "scrollV": 0, "glow": 0.6}),
    ("pyramid_step", "Pyramid Step", "fossil_swamp", "wall", pyramid_step, 6, None),
    (
        "volcano_crust",
        "Volcano Crust",
        "ember_volcano",
        "wall",
        volcano_crust,
        7,
        {"scrollU": 0, "scrollV": 0, "glow": 0.35},
    ),
    ("ember_road", "Ember Road", "ember_volcano", "road", ember_road, 4, None),
    (
        "smoke",
        "Smoke",
        "ember_volcano",
        "wall",
        smoke,
        8,
        {"scrollU": 0.01, "scrollV": -0.05, "wave": 0.05, "wavePeriod": 5, "opacity": 0.55},
    ),
]

MATERIALS += GULCH_MATERIALS

# Impact Depths (Desert World, course 4): its own module, painted with the helpers above.
import impact_textures  # noqa: E402

MATERIALS += impact_textures.materials(sys.modules[__name__])
THEMES.append(impact_textures.THEME)

# Dragon Isles (Dragon Kingdom, course 1).
import isles_textures  # noqa: E402

MATERIALS += isles_textures.materials(sys.modules[__name__])
THEMES.append(isles_textures.THEME)

# Dragonspire Keep (Dragon Kingdom, course 1, painted Oct 25: the castle at sunset).
import keep_textures  # noqa: E402

MATERIALS += keep_textures.materials(sys.modules[__name__])
THEMES.append(keep_textures.THEME)

# Dragon Canyon's new paint, the Emerald Kingdom (Dragon Kingdom, course 2, Oct 25).
import emerald_textures  # noqa: E402

MATERIALS += emerald_textures.materials(sys.modules[__name__])
THEMES.append(emerald_textures.THEME)

# Dragon Canyon (Dragon Kingdom, course 2).
import dcanyon_textures  # noqa: E402

MATERIALS += dcanyon_textures.materials(sys.modules[__name__])
THEMES.append(dcanyon_textures.THEME)

# Snow Dragon Pass (Dragon Kingdom, course 3).
import snow_textures  # noqa: E402

MATERIALS += snow_textures.materials(sys.modules[__name__])
THEMES.append(snow_textures.THEME)

# Emberdeep Hold (Dragon Kingdom, course 3, painted Oct 25: the fortress in the storm).
import ember_textures  # noqa: E402

MATERIALS += ember_textures.materials(sys.modules[__name__])
THEMES.append(ember_textures.THEME)

# Celestial Dragon Festival's new paint, the Moonstone Kingdom (course 4, Oct 25).
import moon_textures  # noqa: E402

MATERIALS += moon_textures.materials(sys.modules[__name__])
THEMES.append(moon_textures.THEME)

# Celestial Dragon Festival (Dragon Kingdom, course 4).
import cdf_textures  # noqa: E402

MATERIALS += cdf_textures.materials(sys.modules[__name__])
THEMES.append(cdf_textures.THEME)

# The beach world's paint, the Tropic Isles: Coral Cove and Shipwreck Bay (Oct 25).
import tropic_textures  # noqa: E402

MATERIALS += tropic_textures.materials(sys.modules[__name__])
THEMES += [tropic_textures.COVE, tropic_textures.WRECK]

# The ruined courses (Adventure's treasure map challenge): Riverbend in ruins first.
import ruin_textures  # noqa: E402

MATERIALS += ruin_textures.materials(sys.modules[__name__])
THEMES.append(ruin_textures.RIVERBEND)


def thumb(im):
    t = Image.new("RGB", (W * 2, H * 4))
    for i in range(2):
        for j in range(4):
            t.paste(im, (i * W, j * H))
    return t.resize((256, 256), Image.NEAREST)


def main():
    path = os.path.join(LIB, "materials.json")
    with open(path, encoding="utf-8") as f:
        lib = json.load(f)
    # Replace themes in place (keeping the library's order); add new ones at the end.
    mine = {t["id"]: t for t in THEMES}
    known = {t["id"] for t in lib["themes"]}
    lib["themes"] = [mine.get(t["id"], t) for t in lib["themes"]] + [t for t in THEMES if t["id"] not in known]
    mids = {m[0] for m in MATERIALS}
    lib["materials"] = [m for m in lib["materials"] if m["id"] not in mids]
    for mid, name, theme, surface, painter, tile, fx in MATERIALS:
        im = painter()
        im.save(os.path.join(LIB, "textures", mid + ".png"))
        thumb(im).save(os.path.join(LIB, "thumbs", mid + ".png"))
        e = {"id": mid, "name": name, "theme": theme, "surface": surface, "image": mid + ".png", "wrap": "repeat", "tileMetres": tile}
        if fx:
            e["fx"] = fx
        lib["materials"].append(e)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(lib, f, indent=2)
        f.write("\n")
    print("painted", len(MATERIALS), "textures")


if __name__ == "__main__":
    main()
