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


# ------------------------------------------------------------------ Jungle Falls additions


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


# ------------------------------------------------------------------ Hot Top Volcano additions


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


THEMES = [
    {
        "id": "jungle_falls",
        "name": "Jungle Falls",
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
        "description": "A glowing red-orange evening under a smoking volcano (uses the Hot Top Volcano textures)",
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

# id, name, theme, surface, painter, tileMetres, fx
MATERIALS = [
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
        "jungle_falls",
        "water",
        waterfall,
        6,
        {"scrollU": 0.0, "scrollV": 0.9, "wave": 0.02, "wavePeriod": 1.5, "opacity": 0.8},
    ),
    (
        "foam",
        "Foam",
        "jungle_falls",
        "water",
        foam,
        4,
        {"scrollU": 0.05, "scrollV": 0.12, "wave": 0.06, "wavePeriod": 2, "opacity": 0.75},
    ),
    ("jungle_fern", "Jungle Fern", "jungle_falls", "grass", jungle_fern, 4, None),
    ("canyon_rock_grey", "Canyon Rock (Grey)", "jungle_falls", "wall", canyon_rock_grey, 9, None),
    ("canyon_rock_moss", "Canyon Rock (Mossy)", "jungle_falls", "wall", canyon_rock_moss, 8, None),
    ("canyon_rock_ochre", "Canyon Rock (Ochre)", "jungle_falls", "wall", canyon_rock_ochre, 10, None),
    ("ruin_stone", "Ruin Stone", "jungle_falls", "wall", ruin_stone, 4, None),
    ("ruin_glyph", "Ruin Glyphs", "jungle_falls", "wall", ruin_glyph, 3, None),
    ("ruin_dark", "Ruin Stone (Sooty)", "jungle_falls", "wall", ruin_dark, 4, None),
    ("jungle_bark", "Jungle Bark", "jungle_falls", "wall", jungle_bark, 3, None),
    ("canopy_dark", "Deep Canopy", "jungle_falls", "grass", canopy_dark, 5, None),
    ("big_leaf", "Big Leaf", "jungle_falls", "grass", big_leaf, 2, None),
    ("vine_leaf", "Vine Leaves", "jungle_falls", "grass", vine_leaf, 1.5, None),
    ("frog_skin", "Frog Skin", "jungle_falls", "wall", frog_skin, 0.4, None),
    ("log_end", "Log End", "jungle_falls", "wall", log_end, 1, None),
    ("torch_glow", "Torch Flame", "jungle_falls", "wall", torch_glow, 1, {"scrollU": 0.2, "scrollV": -1.6, "wave": 0.1, "wavePeriod": 0.4, "glow": 1.0}),
    ("jungle_mud", "Jungle Mud", "jungle_falls", "mud", jungle_mud, 5, None),
    ("pterosaur_skin", "Pterosaur Skin", "jungle_falls", "wall", pterosaur_skin, 2, None),
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
        "hot_top_volcano",
        "wall",
        volcano_crust,
        7,
        {"scrollU": 0, "scrollV": 0, "glow": 0.35},
    ),
    ("ember_road", "Ember Road", "hot_top_volcano", "road", ember_road, 4, None),
    (
        "smoke",
        "Smoke",
        "hot_top_volcano",
        "wall",
        smoke,
        8,
        {"scrollU": 0.01, "scrollV": -0.05, "wave": 0.05, "wavePeriod": 5, "opacity": 0.55},
    ),
]


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
