# Dragon Canyon's textures and theme, painted by make_textures.py (which passes in its
# painting helpers). Every pixel is generated here: original artwork, 64x32, each tiling
# seamlessly. Dragon Canyon also reuses Dragon Isles' architecture (roofs, lacquer,
# banners, emblem) and the Desert World's rock and sand.
# SPDX-License-Identifier: MIT

THEME = {
    "id": "dragon_canyon",
    "name": "Dragon Canyon",
    "description": "The dragon kingdom's desert frontier at golden hour: towering red-orange sandstone canyons, turquoise rivers and white waterfalls far below, cliffside fortresses under blue and jade roofs, red imperial banners, flaring braziers, pink and violet sunset clouds and a warm haze over the distant spires",
    "environment": {
        "sky": "#f2a070",
        "fog": {"enabled": True, "color": "#f0a47c", "near": 420, "far": 2300},
        "sun": {"color": "#ffc888", "intensity": 2.6, "direction": [-0.82, 0.36, 0.44]},
        "ambient": {"sky": "#f4b494", "ground": "#8a4630", "intensity": 1.2},
        "skyDome": {
            "top": "#5a5ab8",
            "horizon": "#ffb878",
            "bottom": "#f0a070",
            "sun": {"color": "#ffeab0", "size": 13, "glow": "#ff9a4a", "elevation": 9},
            "clouds": {"count": 30, "color": "#ffc4a8", "shade": "#c8708e", "seed": 421, "low": 4, "high": 30, "drift": 0.003},
            "hills": {"color": "#a84e36", "far": "#e48c6a", "height": 13, "seed": 423, "layers": 3, "style": "karst"},
        },
    },
}


def materials(mt):
    noise, pick, paint = mt.noise, mt.pick, mt.paint

    def GLOW(g, pulse=None, period=4.0, flicker=None):
        fx = {"scrollU": 0, "scrollV": 0, "glow": g}
        if pulse:
            fx["pulse"] = pulse
            fx["pulsePeriod"] = period
        if flicker:
            fx["flicker"] = flicker
        return fx

    # ---------------------------------------------------------------- roads

    def frontier_road():
        # Packed ochre earth, raked smooth, a few tyre-worn streaks along it (V along).
        a, b = noise(4, 8, 8001), noise(16, 16, 8002)

        def f(x, y):
            streak = 0.12 if x in (14, 15, 48, 49) else 0.0
            return pick(["#b8743e", "#c47e44", "#cc884c", "#d49256", "#dc9c60", "#e4a86a"], a(x, y) * 0.5 + b(x, y) * 0.3 + streak)

        return paint(f)

    def imperial_setts():
        # The empire's road: worn sandstone setts in rows, dusty joints.
        a = noise(8, 4, 8011)

        def f(x, y):
            row = y // 8
            off = 6 if row % 2 else 0
            if y % 8 == 0 or (x + off) % 12 == 0:
                return "#8a5432"
            return pick(["#c88a5a", "#d09464", "#d89e6c", "#e0a876"], a(x, y) * 0.6 + ((x + off) // 12 * 7 + row * 3) % 5 * 0.08)

        return paint(f)

    def kerb_redwhite():
        def f(x, y):
            if x < 4 or x > 59:
                return "#7a2a1a"
            return "#f2ece0" if (y // 8) % 2 else "#d0281e"

        return paint(f)

    def dust_shoulder():
        a = noise(8, 4, 8021)

        def f(x, y):
            return pick(["#a8643a", "#b46e40", "#c07a48", "#ca8652"], a(x, y))

        return paint(f)

    # ---------------------------------------------------------------- the canyon

    def strata(pal, seed, band=4):
        a, b = noise(4, 2, seed), noise(16, 4, seed + 1)

        def f(x, y):
            v = (y + int(a(x, y) * 6)) // band
            base = (v * 37) % len(pal) / len(pal)
            return pick(pal, base * 0.6 + b(x, y) * 0.4)

        return paint(f)

    def canyon_cliff():
        return strata(["#8a3420", "#a03e24", "#b4502c", "#c25e34", "#cc6c3c", "#d87c48"], 8031)

    def canyon_cliff_shade():
        return strata(["#5a2218", "#6a281c", "#7a3020", "#883826", "#96422c"], 8033)

    def canyon_ledge():
        # The flat tops: wind-scoured, sandy, a little scrub.
        a, b = noise(8, 4, 8041), noise(32, 16, 8042)

        def f(x, y):
            if b(x, y) > 0.82:
                return "#7a7a3a"
            return pick(["#c47a46", "#d0884e", "#d89458", "#e2a264"], a(x, y))

        return paint(f)

    def canyon_scree():
        a = noise(16, 8, 8051)

        def f(x, y):
            return pick(["#7a3a24", "#94482c", "#a85636", "#bc6640", "#cc7a4c"], a(x, y))

        return paint(f)

    def river_sand():
        a = noise(8, 4, 8061)

        def f(x, y):
            return pick(["#d8b088", "#e0ba92", "#e8c49c", "#eeceaa"], a(x, y))

        return paint(f)

    def oasis_grass():
        a, b = noise(8, 4, 8071), noise(32, 16, 8072)

        def f(x, y):
            if b(x, y) > 0.86:
                return "#f0d060"
            return pick(["#3a8a3a", "#46983e", "#54a644", "#62b24c"], a(x, y))

        return paint(f)

    # ---------------------------------------------------------------- the empire's works

    def sandstone_block():
        # Freshly cut quarry blocks: pale, chisel-striped, dark seams.
        a = noise(4, 2, 8081)

        def f(x, y):
            if x % 32 == 0 or y % 16 == 0:
                return "#7a4a2e"
            if (x + y * 2) % 7 == 0:
                return "#c88a5c"
            return pick(["#dca478", "#e4ae82", "#ecb88c", "#f2c296"], a(x, y))

        return paint(f)

    def fortress_wall():
        # Big weathered ashlar, sun-bleached, with mortar lines.
        a = noise(8, 4, 8091)

        def f(x, y):
            row = y // 10
            off = 10 if row % 2 else 0
            if y % 10 == 0 or (x + off) % 20 == 0:
                return "#6a4a36"
            return pick(["#a88a6e", "#b49678", "#c0a282", "#ccae8e"], a(x, y))

        return paint(f)

    def quarry_dust():
        a, b = noise(8, 4, 8101), noise(32, 16, 8102)

        def f(x, y):
            if b(x, y) > 0.84:
                return "#f4dcc0"
            return pick(["#c8a07c", "#d0aa86", "#d8b490", "#e0be9c"], a(x, y))

        return paint(f)

    def scaffold_timber():
        a = noise(16, 2, 8111)

        def f(x, y):
            if x % 16 == 0:
                return "#3a2416"
            if y % 16 == 0:
                return "#5a3a22"
            return pick(["#7a5434", "#86603c", "#946a44"], a(x, y))

        return paint(f)

    def bone_ivory():
        a, b = noise(4, 8, 8121), noise(16, 16, 8122)

        def f(x, y):
            if b(x, y) > 0.8:
                return "#b0a080"
            return pick(["#d8ccb0", "#e2d8be", "#ece4cc", "#f4eedc"], a(x, y))

        return paint(f)

    def chamber_glow():
        # Light seeping from a sealed chamber: amber, flickering.
        a = noise(4, 2, 8131)

        def f(x, y):
            return pick(["#c86a1a", "#e08424", "#f0a038", "#ffc050"], a(x, y))

        return paint(f)

    def brazier_fire():
        a = noise(8, 4, 8141)

        def f(x, y):
            v = a(x, y) * 0.6 + (1 - y / 32) * 0.4
            return pick(["#c82a10", "#e8501a", "#f88024", "#ffb030", "#ffe060"], v)

        return paint(f)

    def chevron_canyon():
        # A red-and-white turn board, arrows pointing along +U.
        def f(x, y):
            if y < 2 or y > 29:
                return "#5a2216"
            u = (x - abs(y - 15.5) * 0.8) % 16
            return "#f2ece0" if u < 8 else "#d0281e"

        return paint(f)

    T = "dragon_canyon"
    return [
        ("frontier_road", "Frontier Road", T, "road", frontier_road, 6, None),
        ("imperial_setts", "Imperial Setts", T, "road", imperial_setts, 5, None),
        ("kerb_redwhite", "Red-White Kerb", T, "road", kerb_redwhite, 3, None),
        ("dust_shoulder", "Dusty Verge", T, "dirt", dust_shoulder, 4, None),
        ("canyon_cliff", "Canyon Sandstone", T, "wall", canyon_cliff, 14, None),
        ("canyon_cliff_shade", "Shaded Sandstone", T, "wall", canyon_cliff_shade, 14, None),
        ("canyon_ledge", "Canyon Ledge", T, "dirt", canyon_ledge, 8, None),
        ("canyon_scree", "Red Scree", T, "loose_sand", canyon_scree, 6, None),
        ("river_sand", "River Sand", T, "sand", river_sand, 6, None),
        ("oasis_grass", "Oasis Grass", T, "grass", oasis_grass, 6, None),
        ("sandstone_block", "Cut Sandstone", T, "wall", sandstone_block, 4, None),
        ("fortress_wall", "Fortress Ashlar", T, "wall", fortress_wall, 5, None),
        ("quarry_dust", "Quarry Dust", T, "dirt", quarry_dust, 6, None),
        ("scaffold_timber", "Scaffold Timber", T, "wall", scaffold_timber, 3, None),
        ("bone_ivory", "Ancient Bone", T, "wall", bone_ivory, 4, None),
        ("chamber_glow", "Chamber Glow", T, "wall", chamber_glow, 3, GLOW(0.8, flicker=0.3)),
        ("brazier_fire", "Brazier Fire", T, "wall", brazier_fire, 1, GLOW(1.0, flicker=0.4)),
        ("chevron_canyon", "Canyon Chevrons", T, "wall", chevron_canyon, 4, None),
    ]
