# Celestial Dragon Festival's new paint (Dragon Kingdom, course 4): the Moonstone Kingdom,
# from Blake's two boards. A moonlit violet kingdom: pale moonstone walls and violet slate
# spires, purple banners with a silver crescent, a glowing lake, blue and violet crystals,
# an observatory, and a purple dragon against a huge moon. Painted by make_textures.py;
# every pixel generated here (original artwork, 64x32, 64x64 for the banner).
# SPDX-License-Identifier: MIT

import math

THEME = {
    "id": "moonstone_kingdom",
    "name": "Moonstone Kingdom",
    "description": "A moonlit violet kingdom under a huge pale moon: moonstone walls and violet spires, purple crescent banners, a lake glowing blue, floating islands with castles and falls, crystal caverns, an observatory with a great armillary sphere, and a purple dragon on the palace tower",
    "environment": {
        "sky": "#2a2a6a",
        "fog": {"enabled": True, "color": "#3a3a78", "near": 380, "far": 2300},
        "sun": {"color": "#c8d4ff", "intensity": 1.8, "direction": [0.5, 0.62, -0.6]},
        "ambient": {"sky": "#9a9ae0", "ground": "#3a3060", "intensity": 1.3},
        "skyDome": {
            "top": "#120e3a",
            "horizon": "#5a4a9a",
            "bottom": "#3a3478",
            "sun": {"color": "#f4f0ff", "size": 22, "glow": "#8a8ad8", "elevation": 28, "face": "moon"},
            "clouds": {"count": 22, "color": "#6a62b0", "shade": "#2a2460", "seed": 721, "low": 3, "high": 26, "drift": 0.003},
            "hills": {"color": "#2a2458", "far": "#5a52a0", "height": 12, "seed": 723, "layers": 3},
            "stars": {"count": 220, "color": "#f0f0ff", "seed": 725, "low": 6},
        },
    },
}


def materials(mt):
    noise, pick, paint, speckle = mt.noise, mt.pick, mt.paint, mt.speckle

    def GLOW(g, pulse=None, period=4.0, flicker=None):
        fx = {"scrollU": 0, "scrollV": 0, "glow": g}
        if pulse:
            fx["pulse"] = pulse
            fx["pulsePeriod"] = period
        if flicker:
            fx["flicker"] = flicker
        return fx

    SWAY = {"scrollU": 0, "scrollV": 0, "sway": 0.06}

    def blocks(pal, joint, seed, h=8, w=16, glints=0):
        a, b = noise(8, 4, seed), noise(32, 16, seed + 1)
        r = mt.rng(seed + 2)
        shade = [r() for _ in range(64)]
        sp = speckle(seed + 3, glints)

        def f(x, y):
            row = y // h
            off = (row % 2) * (w // 2)
            col = (x + off) // w
            if y % h == 0 or (x + off) % w == 0:
                return joint
            if (x, y) in sp:
                return "#ffffff"
            v = shade[(row * 7 + col) % 64] * 0.5 + a(x, y) * 0.3 + b(x, y) * 0.2
            if (x + off) % w == 1 or y % h == 1:
                v += 0.2
            return pick(pal, min(0.999, v))

        return paint(f)

    def tiles():
        a = noise(4, 4, 9501)

        def f(x, y):
            u, v = x % 16, y % 16
            if u == 0 or v == 0:
                return "#3a3670"
            if 6 <= u <= 9 and 6 <= v <= 9 and (u + v) % 2 == 0:
                return "#c8c8f0"
            return pick(["#6a6aa0", "#7474aa", "#7e7eb4", "#8888be"], a(x, y))

        return paint(f)

    def grass():
        a, b = noise(8, 4, 9511), noise(32, 16, 9512)
        sp = speckle(9513, 40)

        def f(x, y):
            if (x, y) in sp:
                return "#b8a8ff" if (x + y) % 2 else "#e8e8ff"
            return pick(["#1e3a3e", "#244446", "#2a4e4e", "#305858", "#386262"], a(x, y) * 0.6 + b(x, y) * 0.4)

        return paint(f)

    def rock():
        a, b = noise(4, 2, 9521), noise(16, 8, 9522)

        def f(x, y):
            if (y + int(a(x, 0) * 6)) % 10 == 0:
                return "#2a2648"
            return pick(["#3a3660", "#46426e", "#524e7c", "#5e5a8a", "#6a6698"], a(x, y) * 0.55 + b(x, y) * 0.45)

        return paint(f)

    def slate():
        a = noise(4, 8, 9531)

        def f(x, y):
            row = y // 4
            off = (row % 2) * 4
            if y % 4 == 3:
                return "#1a1240"
            if (x + off) % 8 == 0:
                return "#241a50"
            return pick(["#3a2a70", "#44327c", "#4e3a88", "#5a4494", "#664ea0"], a(x, y) * 0.6 + (y % 4) / 4 * 0.4)

        return paint(f)

    def silver():
        a = noise(4, 4, 9541)

        def f(x, y):
            return pick(["#8a8ab0", "#a6a6c8", "#c4c4e0", "#e0e0f4", "#ffffff"], a(x, y) * 0.6 + ((x + y) % 8) / 8 * 0.4)

        return paint(f)

    def banner(field, edge, glyph, w=64, h=64):
        """A purple banner with a silver border and fringe, and a silver crescent moon
        cradling a star (our own design)."""

        def f(x, y):
            if y > 54:
                return edge if (x // 4) % 2 == 0 else field
            if x < 3 or x > 60 or y < 4 or 50 < y < 53:
                return edge
            cx, cy = x - 31.5, y - 27.5
            if math.hypot(cx, cy) < 17 and math.hypot(cx - 7, cy - 4) > 14:
                return glyph
            if abs(cx - 4) + abs(cy - 2) < 3.5:
                return glyph
            return field

        return paint(f, w, h)

    def lake():
        a, b = noise(4, 2, 9551), noise(16, 8, 9552)

        def f(x, y):
            v = a(x, y) * 0.6 + b(x, y) * 0.4
            if (y + int(a(x, 0) * 4)) % 8 == 0 and v > 0.6:
                return "#c8e8ff"
            return pick(["#1a3a7a", "#20488a", "#28569a", "#3064aa", "#3a74ba"], v)

        return paint(f)

    def crystal(pal, seed):
        a = noise(4, 8, seed)

        def f(x, y):
            u = (x + y // 2) % 16
            if u < 2:
                return pal[-1]
            return pick(pal, a(x, y) * 0.5 + (u / 16) * 0.5)

        return paint(f)

    def dragon_scales():
        a = noise(8, 4, 9561)

        def f(x, y):
            row = y // 4
            off = (row % 2) * 4
            u = (x + off) % 8
            v = y % 4
            if v == 3 or (u == 0 and v > 0):
                return "#1a0e3a"
            return pick(["#3a2a8a", "#46349a", "#5440ac", "#644ebe"], a(x, y) * 0.4 + (1 - v / 4) * 0.6)

        return paint(f)

    def dragon_wing():
        a = noise(8, 4, 9571)

        def f(x, y):
            if x % 16 == 0:
                return "#140c30"
            return pick(["#3a2e7a", "#46388a", "#54449a", "#6450aa"], a(x, y) * 0.5 + (y / 32) * 0.5)

        return paint(f)

    def window():
        a = noise(4, 4, 9581)

        def f(x, y):
            u, v = x % 16, y
            cx = 7.5
            inside = 3 <= u <= 12 and 8 <= v <= 28 and (v >= 12 or math.hypot(u - cx, v - 12) < 4.6)
            if inside:
                if u in (7, 8) or v == 18:
                    return "#2a2a5a"
                return pick(["#8ab8ff", "#a8ccff", "#c8e0ff", "#e8f2ff"], a(x, y) * 0.6 + (v / 32) * 0.4)
            if y % 8 == 0:
                return "#3a3670"
            return pick(["#8a88b8", "#9492c2", "#9e9ccc"], a(x, y))

        return paint(f)

    T = "moonstone_kingdom"
    MOON = ["#8a88b4", "#9694c0", "#a2a0ca", "#aeacd4", "#bab8de", "#c6c4e8"]
    DARK = ["#4a4670", "#54507c", "#5e5a88", "#686494", "#726ea0"]
    return [
        ("moon_paving", "Moonstone Paving", T, "road", lambda: blocks(["#6e6c98", "#7876a2", "#8280ac", "#8c8ab6", "#9694c0"], "#3a3666", 9601, 8, 20, 18), 5, None),
        ("moon_tiles", "Moon Tiles", T, "road", tiles, 4, None),
        ("moon_kerb", "Moonstone Kerb", T, "road", lambda: blocks(["#a8a6d0", "#b4b2dc", "#c0bee6"], "#4a4680", 9611, 32, 16), 2, None),
        ("moon_grass", "Moonlit Grass", T, "grass", grass, 6, None),
        ("moon_rock", "Moon Crag", T, "wall", rock, 12, None),
        ("moon_stone", "Moonstone Ashlar", T, "wall", lambda: blocks(MOON, "#4a4680", 9621, glints=12), 3, None),
        ("moon_stone_dark", "Old Moonstone", T, "wall", lambda: blocks(DARK, "#2a2650", 9631, 8, 12), 3, None),
        ("moon_slate", "Violet Slate", T, "wall", slate, 3, None),
        ("moon_silver", "Silver Trim", T, "wall", silver, 1, GLOW(0.3)),
        ("moon_window", "Moonlit Windows", T, "wall", window, 4, GLOW(0.8, flicker=0.05)),
        ("moon_banner", "Crescent Banner", T, "wall", lambda: banner("#4a1e7a", "#d0d0ec", "#f0f0ff"), 3, SWAY),
        ("moon_lake", "Glowing Lake", T, "deep_water", lake, 14, {"scrollU": 0.006, "scrollV": 0.01, "wave": 0.04, "wavePeriod": 6, "opacity": 0.9, "glow": 0.45}),
        ("moon_lake_shallow", "Glowing Shallows", T, "water", lake, 14, {"scrollU": 0.006, "scrollV": 0.01, "wave": 0.04, "wavePeriod": 6, "opacity": 0.86, "glow": 0.45}),
        ("moon_crystal", "Blue Moon Crystal", T, "wall", lambda: crystal(["#1a4a9a", "#2a6aca", "#4a8ae8", "#8ab8ff", "#e0f0ff"], 9641), 2, GLOW(0.95, 0.3, 3.8)),
        ("moon_crystal_violet", "Violet Moon Crystal", T, "wall", lambda: crystal(["#4a1e8a", "#6a2aaa", "#8a4ad0", "#c08aff", "#f0e0ff"], 9651), 2, GLOW(0.95, 0.3, 4.4)),
        ("dragon_purple", "Purple Dragon Scales", T, "wall", dragon_scales, 1.5, None),
        ("dragon_purple_wing", "Purple Dragon Wing", T, "wall", dragon_wing, 4, None),
    ]
