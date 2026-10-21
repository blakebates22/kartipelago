# Dragon Isles' textures and theme, painted by make_textures.py (which passes in its
# painting helpers). Every pixel is generated here: original artwork, 64x32 (or 64x64 for
# the emblem banners), each tiling seamlessly.
# SPDX-License-Identifier: MIT

import math

THEME = {
    "id": "dragon_isles",
    "name": "Dragon Isles",
    "description": "A sunlit kingdom of karst mountains in a turquoise lagoon: red-lacquered temples under blue and gold tiled roofs, white waterfalls, pink blossom, golden lanterns and red festival banners, distant peaks fading into soft blue haze",
    "environment": {
        "sky": "#5aa8f0",
        "fog": {"enabled": True, "color": "#cfe4f4", "near": 520, "far": 2900},
        "sun": {"color": "#fff2dc", "intensity": 2.7, "direction": [-0.42, 0.78, 0.46]},
        "ambient": {"sky": "#c4dcff", "ground": "#86a070", "intensity": 1.25},
        "skyDome": {
            "top": "#2a7ae0",
            "horizon": "#dceefa",
            "bottom": "#cfe4f0",
            "sun": {"color": "#fffbe8", "size": 8, "glow": "#ffe8b0", "elevation": 46},
            "clouds": {"count": 34, "color": "#ffffff", "shade": "#dce8f4", "seed": 311, "low": 2, "high": 26, "drift": 0.004},
            "hills": {"color": "#7a9ab0", "far": "#c4d8e8", "height": 11, "seed": 313, "layers": 3, "style": "karst"},
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

    # ---------------------------------------------------------------- roads

    def palace_paving():
        # Warm cream flagstones in long courses (V runs along the road), honey joints.
        a, b = noise(4, 2, 7001), noise(16, 8, 7002)

        def f(x, y):
            row = y // 8
            off = (row * 13) % 32
            if y % 8 == 0 or (x + off) % 32 == 0:
                return "#c09a64"
            return pick(["#e2c896", "#ead2a2", "#f0dcae", "#f6e6bc", "#fbeecb"], 0.15 + a(x, y) * 0.5 + b(x, y) * 0.25)

        return paint(f)

    def village_cobble():
        a = noise(8, 4, 7011)

        def f(x, y):
            cx, cy = (x + (4 if (y // 8) % 2 else 0)) % 8, y % 8
            if cx == 0 or cy == 0:
                return "#8a6a4a"
            return pick(["#c4a27a", "#ceac84", "#d8b890", "#e0c29a"], a(x, y) * 0.7 + ((x // 8 * 3 + y // 8 * 5) % 4) * 0.08)

        return paint(f)

    def temple_flag():
        # Pale grey-white temple stone, big square slabs.
        a = noise(8, 4, 7021)

        def f(x, y):
            if x % 16 == 0 or y % 16 == 0:
                return "#9a9a92"
            return pick(["#d4d2c8", "#dcdad0", "#e4e2d8", "#ecebe2"], a(x, y) * 0.8 + 0.1)

        return paint(f)

    def royal_carpet():
        # The royal approach: a red runner with a gold cloud-scroll border down each edge.
        a = noise(8, 2, 7031)

        def f(x, y):
            if x < 4 or x > 59:
                return "#e8b830" if (y + x) % 6 < 3 else "#c89020"
            if x < 6 or x > 57:
                return "#7a1010"
            cx = (x - 32) / 26.0
            cy = (y % 16 - 8) / 8.0
            if abs(cx * cx + cy * cy - 0.3) < 0.05:
                return "#f0c040"
            return pick(["#a8181a", "#b42020", "#c02824"], a(x, y))

        return paint(f)

    def stone_curb():
        def f(x, y):
            if y % 16 < 2:
                return "#7a5a3a"
            return "#d63a2a" if (x // 8) % 2 == 0 else "#f0d070"

        return paint(f)

    def cliff_road():
        a, b = noise(4, 2, 7041), noise(16, 8, 7042)
        peb = speckle(7043, 30)

        def f(x, y):
            if (x, y) in peb:
                return "#f2e6cc"
            return pick(["#b8a07a", "#c4ac86", "#d0b892", "#dcc49e"], 0.1 + a(x, y) * 0.6 + b(x, y) * 0.3)

        return paint(f)

    def passage_stone():
        a = noise(8, 4, 7051)

        def f(x, y):
            row = y // 10
            off = 12 if row % 2 else 0
            if y % 10 == 0 or (x + off) % 24 == 0:
                return "#4a3a2a"
            return pick(["#8a7258", "#967e62", "#a2896c", "#ae9476"], a(x, y) * 0.8 + 0.1)

        return paint(f)

    # ---------------------------------------------------------------- the land

    def lush_grass():
        a, b = noise(8, 4, 7101), noise(16, 8, 7102)
        fl = speckle(7103, 24)

        def f(x, y):
            if (x, y) in fl:
                return "#fff4c0" if (x + y) % 3 else "#ffb4d0"
            return pick(["#4a9a3a", "#56a842", "#62b44a", "#70c054", "#7ecc5e"], a(x, y) * 0.6 + b(x, y) * 0.4)

        return paint(f)

    def flowerbed():
        a = noise(8, 4, 7111)
        sp = speckle(7112, 160)

        def f(x, y):
            if (x, y) in sp:
                return ["#ff6aa0", "#ffffff", "#ffd040", "#ff3a4a"][(x * 7 + y * 3) % 4]
            return pick(["#3a7a2a", "#468a32", "#52983a"], a(x, y))

        return paint(f)

    def limestone():
        # Karst limestone: pale grey with dark rain streaks running down (V up the cliff).
        a, b = noise(16, 2, 7121), noise(4, 8, 7122)

        def f(x, y):
            streak = abs(math.sin(x * 0.7 + a(x, y) * 6))
            if streak > 0.96:
                return "#6a6c6a"
            return pick(["#9a9c96", "#a8aaa4", "#b6b8b0", "#c4c6bc", "#d2d2c8"], 0.1 + b(x, y) * 0.7 + (0.15 if streak < 0.3 else 0))

        return paint(f)

    def limestone_moss():
        a, b = noise(8, 4, 7131), noise(16, 8, 7132)

        def f(x, y):
            v = a(x, y) * 0.6 + b(x, y) * 0.4
            if v > 0.5:
                return pick(["#3a7a2a", "#4a8a32", "#5a9a3c", "#6aaa48"], (v - 0.5) * 2)
            return pick(["#8a8c86", "#9a9c94", "#aaaca2"], v * 2)

        return paint(f)

    def pale_beach():
        a = noise(8, 4, 7141)

        def f(x, y):
            return pick(["#e8dcbc", "#eee4c6", "#f4ead0", "#f8f0da"], a(x, y))

        return paint(f)

    # ---------------------------------------------------------------- architecture

    def red_lacquer():
        a = noise(4, 16, 7201)

        def f(x, y):
            return pick(["#a8141a", "#b81c1e", "#c42624", "#d03028"], a(x, y) * 0.7 + (x % 16) / 16 * 0.3)

        return paint(f)

    def tile_roof(pal, seed):
        # Glazed half-round roof tiles in rows (V runs down the roof), bright ridges.
        a = noise(8, 4, seed)

        def f(x, y):
            u = x % 8
            if y % 8 == 7:
                return pal[0]
            if u in (0, 7):
                return pal[1]
            return pick(pal[2:], 0.2 + (1 - abs(u - 3.5) / 3.5) * 0.6 + a(x, y) * 0.2)

        return paint(f)

    def gold_trim():
        a = noise(8, 4, 7221)

        def f(x, y):
            if (x + y) % 9 == 0:
                return "#fff4b0"
            return pick(["#b07818", "#c88c20", "#e0a830", "#f0c040"], a(x, y))

        return paint(f)

    def white_plaster():
        a = noise(8, 4, 7231)

        def f(x, y):
            if y % 32 > 28:
                return "#8a5a3a"
            return pick(["#ece4d4", "#f2eadc", "#f6f0e4", "#faf6ee"], a(x, y))

        return paint(f)

    def lattice_window():
        # Carved lattice over warm lamplight.
        def f(x, y):
            u, v = x % 16, y % 16
            if u in (0, 15) or v in (0, 15):
                return "#5a1a10"
            if u == v or u == 15 - v or u == 8 or v == 8:
                return "#7a2414"
            return "#ffc860" if (x // 16 + y // 16) % 2 else "#ffb040"

        return paint(f)

    def wood_wall():
        a = noise(16, 2, 7241)

        def f(x, y):
            if x % 8 == 0:
                return "#4a2a18"
            return pick(["#7a4a2a", "#8a5632", "#9a623a"], a(x, y))

        return paint(f)

    def stone_base():
        a = noise(8, 4, 7251)

        def f(x, y):
            row = y // 8
            off = 8 if row % 2 else 0
            if y % 8 == 0 or (x + off) % 16 == 0:
                return "#6a6a62"
            return pick(["#a8a69c", "#b4b2a8", "#c0beb4"], a(x, y))

        return paint(f)

    def balustrade():
        # A carved stone railing: posts and panels (both sides of a bridge).
        def f(x, y):
            if x % 16 < 3:
                return "#c8c4b8" if y > 3 else "#e8c040"
            if y < 4 or y > 27:
                return "#b8b4a8"
            if 8 < y < 24 and 5 < x % 16 < 14:
                return "#a8a498" if (x + y) % 4 else "#c06040"
            return "#d4d0c4"

        return paint(f)

    def red_rail():
        def f(x, y):
            if x % 16 < 3:
                return "#e8b830" if y < 4 else "#8a1414"
            if y < 5 or 14 < y < 18:
                return "#b81c1e"
            return "#00000000" if False else "#c42624"

        return paint(f)

    def jade_stone():
        a, b = noise(8, 4, 7271), noise(4, 8, 7272)

        def f(x, y):
            if abs(b(x, y) - 0.5) < 0.03:
                return "#d4f0d8"
            return pick(["#2a7a5a", "#348a66", "#409a72", "#4eaa80", "#62bc90"], a(x, y))

        return paint(f)

    def dragon_scales():
        # Jade scales with a gold edge (for the statues' bodies).
        def f(x, y):
            u, v = x % 8, y % 8
            r = (u - 4) ** 2 + (v - 2) ** 2
            if r < 4:
                return "#4ab884"
            if r < 10:
                return "#2e9a6a"
            if v < 1:
                return "#e8c040"
            return "#1e7a52"

        return paint(f)

    def carved_relief():
        # Warm stone with carved dragon coils (the passage's walls).
        a = noise(8, 4, 7281)

        def f(x, y):
            u = (x % 32) / 32 * math.tau
            c = math.sin(u * 2) * 8 + 16
            if abs((y % 32) - c) < 2:
                return "#5a3a24"
            if abs((y % 32) - c) < 3:
                return "#d8b080"
            return pick(["#9a7a58", "#a68462", "#b28e6c"], a(x, y))

        return paint(f)

    def glyph_teal():
        # Old carvings glowing faintly blue-green.
        a = noise(8, 4, 7291)

        def f(x, y):
            cx, cy = x % 16, y % 16
            g = (cx in (4, 11) and 3 < cy < 13) or (cy in (4, 11) and 3 < cx < 13) or (abs(cx - cy) < 1 and 3 < cx < 13)
            if g:
                return "#6affd0" if (x // 16 + y // 16) % 2 else "#3ac8a8"
            return pick(["#3a3a34", "#44443c", "#4e4e44"], a(x, y))

        return paint(f)

    def dark_corridor():
        a = noise(8, 4, 7301)

        def f(x, y):
            return pick(["#0a0a0c", "#121216", "#1a1a20"], a(x, y))

        return paint(f)

    # ---------------------------------------------------------------- festival

    def emblem(base, ring, glyph, w=64, h=64):
        """The royal dragon emblem: a gold ring on a field, inside it a coiled dragon
        (an S of a body, a head with a horn) — our own design."""

        def f(x, y):
            cx, cy = x - 31.5, y - 28.5
            r = math.hypot(cx, cy)
            if 17 < r < 20:
                return ring
            if r < 17:
                a = math.atan2(cy, cx)
                # The coil: a spiral band.
                s = (r / 17.0) * 2.2 + a / math.tau
                if abs((s % 1.0) - 0.5) < 0.17 and r > 4:
                    return glyph
                if math.hypot(cx - 7, cy + 9) < 3.2:
                    return glyph
                return base
            if y > 54 and (x // 6) % 2 == 0:
                return ring  # the tassel fringe at the foot
            if x < 3 or x > 60:
                return ring
            return base

        return paint(f, w, h)

    def bunting():
        def f(x, y):
            k = x // 8
            col = ["#e83a3a", "#f6c03a", "#3aa8e8", "#4ac86a", "#f07ab0", "#ffffff"][k % 6]
            u = x % 8
            if y < 4:
                return "#7a5a3a"
            if y - 4 < (8 - abs(u - 3.5) * 2) * 2.5:
                return col
            return "#00000000" if False else "#cfe4f4"

        return paint(f)

    def lantern_red():
        a = noise(4, 8, 7311)

        def f(x, y):
            if y < 3 or y > 28:
                return "#d0a020"
            if y % 8 == 0:
                return "#c02010"
            return pick(["#ff5a30", "#ff7a40", "#ff9a50", "#ffb060"], a(x, y))

        return paint(f)

    def sail_red():
        a = noise(4, 8, 7321)

        def f(x, y):
            if y % 8 == 0:
                return "#7a2010"
            return pick(["#c43a24", "#d04a2c", "#dc5a34"], a(x, y))

        return paint(f)

    def blossom_pink():
        a, b = noise(8, 4, 7331), noise(16, 8, 7332)
        sp = speckle(7333, 50)

        def f(x, y):
            if (x, y) in sp:
                return "#ffffff"
            return pick(["#e86a9a", "#f07aa8", "#f68ab6", "#fa9cc4", "#feb2d2"], a(x, y) * 0.6 + b(x, y) * 0.4)

        return paint(f)

    def bamboo():
        a = noise(4, 8, 7341)

        def f(x, y):
            if y % 12 == 0:
                return "#5a7a2a"
            return pick(["#7aa83a", "#8ab844", "#9ac84e"], a(x, y) * 0.6 + (x % 8) / 8 * 0.4)

        return paint(f)

    def robe_cloth():
        a = noise(4, 8, 7351)

        def f(x, y):
            if y % 16 < 2:
                return "#e8c040"
            return pick(["#d84a3a", "#e05a44", "#e86a4e"], a(x, y))

        return paint(f)

    def cloud_bank():
        a, b = noise(4, 2, 7361), noise(8, 4, 7362)

        def f(x, y):
            return pick(["#e8f0f8", "#f0f6fa", "#f8fbfd", "#ffffff"], a(x, y) * 0.6 + b(x, y) * 0.4)

        return paint(f)

    T = "dragon_isles"
    return [
        ("isle_paving", "Palace Paving", T, "road", palace_paving, 5, None),
        ("village_cobble", "Village Cobbles", T, "road", village_cobble, 4, None),
        ("temple_flag", "Temple Flagstones", T, "road", temple_flag, 5, None),
        ("royal_carpet", "Royal Runner", T, "road", royal_carpet, 8, None),
        ("stone_curb", "Festival Kerb", T, "road", stone_curb, 2, None),
        ("cliff_road", "Cliff Road", T, "road", cliff_road, 6, None),
        ("passage_stone", "Passage Stone", T, "road", passage_stone, 4, None),
        ("lush_grass", "Lush Grass", T, "grass", lush_grass, 6, None),
        ("flowerbed", "Flower Bed", T, "grass", flowerbed, 3, None),
        ("limestone", "Karst Limestone", T, "wall", limestone, 12, None),
        ("limestone_moss", "Mossy Limestone", T, "wall", limestone_moss, 9, None),
        ("pale_beach", "Pale Beach", T, "sand", pale_beach, 6, None),
        ("red_lacquer", "Red Lacquer", T, "wall", red_lacquer, 2, None),
        ("roof_blue", "Blue Glazed Tiles", T, "wall", lambda: tile_roof(["#1a3a6a", "#24467a", "#2a5a9a", "#3a6eb0", "#4a82c4", "#62a0dc"], 7211), 3, None),
        ("roof_jade", "Jade Glazed Tiles", T, "wall", lambda: tile_roof(["#145a3a", "#1c6a46", "#22804e", "#2e965c", "#3cac6a", "#56c27e"], 7212), 3, None),
        ("roof_gold", "Imperial Gold Tiles", T, "wall", lambda: tile_roof(["#8a5a10", "#a06c14", "#c08a1c", "#d8a228", "#ecbc38", "#fcd858"], 7213), 3, GLOW(0.15)),
        ("isle_gold", "Gilded Trim", T, "wall", gold_trim, 1, GLOW(0.25)),
        ("white_plaster", "White Plaster", T, "wall", white_plaster, 4, None),
        ("lattice_window", "Lattice Window", T, "wall", lattice_window, 2, GLOW(0.55, flicker=0.15)),
        ("wood_wall", "Timber Wall", T, "wall", wood_wall, 3, None),
        ("stone_base", "Dressed Stone", T, "wall", stone_base, 3, None),
        ("isle_balustrade", "Stone Balustrade", T, "wall", balustrade, 3, None),
        ("red_rail", "Lacquered Rail", T, "wall", red_rail, 2, None),
        ("jade_stone", "Jade Stone", T, "wall", jade_stone, 3, None),
        ("dragon_scales", "Dragon Scales", T, "wall", dragon_scales, 1, None),
        ("carved_relief", "Carved Dragon Relief", T, "wall", carved_relief, 4, None),
        ("glyph_teal", "Old Glowing Carvings", T, "wall", glyph_teal, 3, GLOW(0.5, 0.5, 6.5)),
        ("dark_corridor", "Dark Corridor", T, "wall", dark_corridor, 4, None),
        ("banner_royal", "Royal Banner", T, "wall", lambda: emblem("#c41c1e", "#f0c040", "#f8d860"), 3, SWAY),
        ("banner_jade", "Jade Banner", T, "wall", lambda: emblem("#1e7a52", "#f0c040", "#f8d860"), 3, SWAY),
        ("emblem_plaque", "Royal Emblem", T, "wall", lambda: emblem("#8a1414", "#e8b830", "#f8d860"), 3, GLOW(0.2)),
        ("isle_bunting", "Festival Bunting", T, "wall", bunting, 4, SWAY),
        ("lantern_red", "Red Lantern", T, "wall", lantern_red, 1, GLOW(0.9, flicker=0.25)),
        ("sail_red", "Junk Sail", T, "wall", sail_red, 4, {"scrollU": 0, "scrollV": 0, "sway": 0.04}),
        ("blossom_pink", "Cherry Blossom", T, "grass", blossom_pink, 2, {"scrollU": 0, "scrollV": 0, "sway": 0.05}),
        ("bamboo", "Bamboo", T, "grass", bamboo, 2, {"scrollU": 0, "scrollV": 0, "sway": 0.05}),
        ("robe_cloth", "Festival Cloth", T, "wall", robe_cloth, 2, SWAY),
        ("cloud_bank", "Cloud Bank", T, "wall", cloud_bank, 30, {"scrollU": 0.004, "scrollV": 0.001, "wave": 0.05, "wavePeriod": 11, "opacity": 0.55, "glow": 0.6}),
    ]
