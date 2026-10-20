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

# id, name, theme, surface, painter, tileMetres, fx
MATERIALS = [
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
