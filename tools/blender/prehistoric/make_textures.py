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


def rainbow():
    # Soft rainbow bands across V, for the mist under the waterfall.
    bands = ["#ff5a5a", "#ff9d42", "#ffe24a", "#6fe05a", "#4ab6ff", "#8a6dff"]

    def f(x, y):
        return bands[min(len(bands) - 1, int(y / H * len(bands)))]

    return paint(f)


THEMES = [
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
                "sun": {"color": "#fff9dc", "size": 6, "glow": "#ffe27a"},
                "clouds": {"count": 26, "color": "#ffffff", "shade": "#d2e8ff", "seed": 5, "low": 2, "high": 22, "drift": 0.004},
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

# id, name, theme, surface, painter, tileMetres, fx
MATERIALS = [
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
    ids = {t["id"] for t in THEMES}
    lib["themes"] = [t for t in lib["themes"] if t["id"] not in ids] + THEMES
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
