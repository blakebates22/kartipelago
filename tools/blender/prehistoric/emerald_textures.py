# Dragon Canyon's new paint (Dragon Kingdom, course 2): the Emerald Kingdom, from Blake's
# two boards. An overgrown jungle castle and its ruins in late-afternoon sun: mossy carved
# stone, giant roots, green banners with a gold spiral, turquoise water, glowing green
# crystals, and a green dragon. Painted by make_textures.py; every pixel generated here
# (original artwork, 64x32, 64x64 for the banner, tiling seamlessly).
# SPDX-License-Identifier: MIT

import math

THEME = {
    "id": "emerald_kingdom",
    "name": "Emerald Kingdom",
    "description": "An overgrown jungle castle and its ruins in late-afternoon sun: mossy carved stone, giant trees and roots, green banners with a gold spiral, turquoise rivers and falls, glowing green crystals in the caves, and a green dragon on the old watchtower",
    "environment": {
        "sky": "#7ab8d8",
        "fog": {"enabled": True, "color": "#bcd8c4", "near": 380, "far": 2300},
        "sun": {"color": "#ffe4b0", "intensity": 2.5, "direction": [-0.55, 0.62, 0.55]},
        "ambient": {"sky": "#bcdcd0", "ground": "#4a6a3a", "intensity": 1.25},
        "skyDome": {
            "top": "#3a86c4",
            "horizon": "#f2e2b4",
            "bottom": "#c4dcc0",
            "sun": {"color": "#fff6d8", "size": 9, "glow": "#ffe0a0", "elevation": 22},
            "clouds": {"count": 30, "color": "#fff8ec", "shade": "#c8d8d4", "seed": 621, "low": 3, "high": 28, "drift": 0.004},
            "hills": {"color": "#3e6a4a", "far": "#9ac0ac", "height": 12, "seed": 623, "layers": 3},
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

    def mossy(base, moss, seed, joints=None, amount=0.45, rows=8, run=16):
        """Stone with moss creeping over it (and block joints if asked)."""
        a, b, m = noise(8, 4, seed), noise(32, 16, seed + 1), noise(6, 3, seed + 2)

        def f(x, y):
            if joints:
                row = y // rows
                off = (row % 2) * (run // 2)
                if y % rows == 0 or (x + off) % run == 0:
                    return joints
            if m(x, y) * 0.8 + b(x, y) * 0.2 > 1.0 - amount:
                return pick(moss, a(x, y))
            return pick(base, a(x, y) * 0.6 + b(x, y) * 0.4)

        return paint(f)

    STONE = ["#5e6450", "#6a705a", "#767c64", "#82886e", "#8e9478"]
    MOSS = ["#2e5a24", "#3a6a2a", "#467a30", "#548a38", "#629a40"]

    def grass():
        a, b = noise(8, 4, 9301), noise(32, 16, 9302)
        sp = speckle(9303, 50)

        def f(x, y):
            if (x, y) in sp:
                return "#d8e070" if (x + y) % 2 else "#e86a8a"
            return pick(["#2a5a1e", "#346a24", "#3e7a2a", "#4a8a30", "#589a38"], a(x, y) * 0.6 + b(x, y) * 0.4)

        return paint(f)

    def floor():
        a, b = noise(8, 4, 9311), noise(32, 16, 9312)
        sp = speckle(9313, 90)

        def f(x, y):
            if (x, y) in sp:
                return pick(["#8a5a2a", "#a86a2a", "#5a7a2a"], (x * 7 + y) % 10 / 10)
            return pick(["#3a3020", "#463a26", "#52442c", "#4a5a2a", "#56682e"], a(x, y) * 0.6 + b(x, y) * 0.4)

        return paint(f)

    def bank():
        a, b = noise(8, 4, 9321), noise(32, 16, 9322)
        sp = speckle(9323, 140)

        def f(x, y):
            if (x, y) in sp:
                return "#d8d0b8"
            return pick(["#6a6450", "#787058", "#867e64", "#948a6e"], a(x, y) * 0.5 + b(x, y) * 0.5)

        return paint(f)

    def path():
        a, b = noise(8, 4, 9331), noise(32, 16, 9332)

        def f(x, y):
            v = a(x, y) * 0.6 + b(x, y) * 0.4
            if v > 0.72:
                return pick(["#3e6a2a", "#4a7a30"], b(x, y))
            return pick(["#6a5a40", "#766648", "#827052", "#8e7c5c"], v)

        return paint(f)

    def cliff(pal, seed):
        a, b, m = noise(4, 2, seed), noise(16, 8, seed + 1), noise(6, 3, seed + 2)

        def f(x, y):
            if m(x, y) > 0.62:
                return pick(MOSS, b(x, y))
            if (y + int(a(x, 0) * 6)) % 10 == 0:
                return pal[0]
            return pick(pal, a(x, y) * 0.55 + b(x, y) * 0.45)

        return paint(f)

    def bark():
        a = noise(4, 16, 9341)

        def f(x, y):
            u = (x + int(6 * math.sin(y / 5.0))) % 8
            if u == 0:
                return "#2a1e14"
            if (x * 3 + y) % 23 == 0:
                return "#4a7a30"
            return pick(["#4a3624", "#56402a", "#624a30", "#6e5438"], a(x, y) * 0.6 + (u / 8) * 0.4)

        return paint(f)

    def roof():
        a = noise(4, 8, 9351)
        m = noise(6, 3, 9352)

        def f(x, y):
            row = y // 4
            off = (row % 2) * 4
            if y % 4 == 3:
                return "#1e2a1c"
            if m(x, y) > 0.55:
                return pick(MOSS, a(x, y))
            if (x + off) % 8 == 0:
                return "#2a3428"
            return pick(["#3a4438", "#444e40", "#4e5848", "#586250"], a(x, y))

        return paint(f)

    def wood():
        a = noise(4, 16, 9361)

        def f(x, y):
            if x % 8 == 0:
                return "#2a2014"
            if (x * 5 + y * 3) % 31 == 0:
                return "#4a7a30"
            return pick(["#4a3a26", "#56442c", "#624e32", "#6e5838"], a(x, y))

        return paint(f)

    def canvas():
        a = noise(4, 8, 9371)

        def f(x, y):
            if y % 16 < 2:
                return "#e0c050"
            return pick(["#2a6a3a", "#327444", "#3a7e4c"], a(x, y))

        return paint(f)

    def plaster():
        a, m = noise(8, 4, 9381), noise(6, 3, 9382)

        def f(x, y):
            if m(x, y) > 0.6:
                return pick(MOSS, a(x, y))
            return pick(["#c8c0a0", "#d2caaa", "#dcd4b4", "#e4dcbe"], a(x, y))

        return paint(f)

    def banner(field, edge, glyph, w=64, h=64):
        """A green banner with a gold border, a fringe, and the kingdom's sign: a gold
        spiral with a dragon's head at its heart (our own design)."""

        def f(x, y):
            if y > 54:
                return edge if (x // 4) % 2 == 0 else field
            if x < 3 or x > 60 or y < 4 or 50 < y < 53:
                return edge
            cx, cy = x - 31.5, y - 27.5
            r = math.hypot(cx, cy)
            if r < 19:
                a = math.atan2(cy, cx)
                s = (r / 19.0) * 3.0 - a / math.tau
                if abs((s % 1.0) - 0.5) < 0.2 and r > 5:
                    return glyph
                if r < 4.5:
                    return glyph
            return field

        return paint(f, w, h)

    def crystal(pal, seed):
        a = noise(4, 8, seed)

        def f(x, y):
            u = (x + y // 2) % 16
            if u < 2:
                return pal[-1]
            return pick(pal, a(x, y) * 0.5 + (u / 16) * 0.5)

        return paint(f)

    def dragon_green():
        a = noise(8, 4, 9401)

        def f(x, y):
            row = y // 4
            off = (row % 2) * 4
            u = (x + off) % 8
            v = y % 4
            if v == 3 or (u == 0 and v > 0):
                return "#0e3a1a"
            return pick(["#1e6a2e", "#287a36", "#348c40", "#44a04a"], a(x, y) * 0.4 + (1 - v / 4) * 0.6)

        return paint(f)

    def dragon_wing():
        a = noise(8, 4, 9411)

        def f(x, y):
            if x % 16 == 0:
                return "#0e2a14"
            return pick(["#1e5a2a", "#286a32", "#347a3a", "#448a44"], a(x, y) * 0.5 + (y / 32) * 0.5)

        return paint(f)

    T = "emerald_kingdom"
    CLIFF = ["#3e4232", "#4c5240", "#5a604c", "#686e58", "#767c64", "#848a70"]
    SHADE = ["#2a2e22", "#343a2c", "#3e4434", "#484e3c", "#525844"]
    return [
        ("em_road", "Overgrown Flagstones", T, "road", lambda: mossy(["#6a6a58", "#767662", "#82826c", "#8e8e76"], MOSS, 9201, "#3a3a2e", 0.18, 8, 20), 5, None),
        ("em_setts", "Old Kingdom Setts", T, "road", lambda: mossy(["#707060", "#7c7c6a", "#888874", "#94947e"], MOSS, 9211, "#3e3e32", 0.14, 6, 12), 5, None),
        ("em_kerb", "Mossy Kerb", T, "road", lambda: mossy(["#8a8a76", "#96967e", "#a2a288"], MOSS, 9221, "#3e3e32", 0.25, 32, 16), 3, None),
        ("em_ledge", "Jungle Path", T, "dirt", path, 8, None),
        ("em_verge", "Leafy Verge", T, "dirt", floor, 4, None),
        ("em_jungle_grass", "Jungle Grass", T, "grass", grass, 6, None),
        ("em_forest_floor", "Forest Floor", T, "loose_sand", floor, 6, None),
        ("em_river_bank", "River Pebbles", T, "sand", bank, 6, None),
        ("em_cliff", "Mossy Crag", T, "wall", lambda: cliff(CLIFF, 9231), 14, None),
        ("em_cliff_shade", "Shaded Mossy Crag", T, "wall", lambda: cliff(SHADE, 9241), 14, None),
        ("em_ruin_wall", "Ruined Ashlar", T, "wall", lambda: mossy(STONE, MOSS, 9251, "#2e3226", 0.4), 4, None),
        ("em_temple_block", "Carved Temple Stone", T, "wall", lambda: mossy(["#7a7860", "#86846a", "#929074", "#9e9c7e"], MOSS, 9261, "#3a382a", 0.3, 16, 32), 4, None),
        ("em_moss_stone", "Moss-Grown Statue Stone", T, "wall", lambda: mossy(["#5a6a52", "#66765c", "#728266"], MOSS, 9271, None, 0.55), 3, None),
        ("em_roof_moss", "Mossy Slate", T, "wall", roof, 3, None),
        ("em_wood_dark", "Old Timber", T, "wall", wood, 2, None),
        ("em_root_bark", "Giant Root Bark", T, "wall", bark, 4, None),
        ("em_canvas_green", "Green Canvas", T, "wall", canvas, 2, SWAY),
        ("em_plaster_moss", "Mossy Plaster", T, "wall", plaster, 4, None),
        ("em_banner", "Emerald Banner", T, "wall", lambda: banner("#1e6a34", "#d8b040", "#f0cc58"), 3, SWAY),
        ("em_crystal", "Glow Crystal", T, "wall", lambda: crystal(["#1a8a4a", "#2aaa5a", "#4ad070", "#8affa8", "#d8ffe0"], 9421), 2, GLOW(0.9, 0.3, 3.6)),
        ("em_crystal_violet", "Violet Glow Crystal", T, "wall", lambda: crystal(["#5a2a9a", "#7a3aba", "#9a5ad8", "#c88aff", "#f0d8ff"], 9431), 2, GLOW(0.9, 0.3, 4.2)),
        ("em_dragon_green", "Green Dragon Scales", T, "wall", dragon_green, 1.5, None),
        ("em_dragon_wing", "Green Dragon Wing", T, "wall", dragon_wing, 4, None),
    ]
