# Celestial Dragon Festival's textures and theme, painted by make_textures.py (which
# passes in its painting helpers). Every pixel is generated here: original artwork, 64x32
# (64x64 for the banners and murals), each tiling seamlessly. The course also reuses
# Dragon Isles' architecture (lacquer, lattice, roofs, gold, banners, blossom).
# SPDX-License-Identifier: MIT

import math

THEME = {
    "id": "celestial_dragon_festival",
    "name": "Celestial Dragon Festival",
    "description": "The dragon kingdom's sacred heart on the night of its greatest festival: a deep navy and violet sky full of stars, a crescent moon, karst islands over a glowing turquoise lagoon, thousands of warm red and gold lanterns, white and gold palaces under deep blue domes, golden astronomical rings, pink blossom, crimson and navy dragon banners, and fireworks",
    "environment": {
        "sky": "#141a4a",
        "fog": {"enabled": True, "color": "#2c2a6a", "near": 420, "far": 2600},
        "sun": {"color": "#c8d0ff", "intensity": 1.75, "direction": [0.36, 0.7, 0.6]},
        "ambient": {"sky": "#9a9af0", "ground": "#4a3a78", "intensity": 1.6},
        "skyDome": {
            "top": "#060a2e",
            "horizon": "#5a3a9a",
            "bottom": "#24205a",
            "sun": {"color": "#fff6dc", "size": 6, "glow": "#c8c4ff", "elevation": 38, "face": "crescent"},
            "clouds": {"count": 12, "color": "#4a3e8c", "shade": "#1a1648", "seed": 611, "low": 2, "high": 10, "drift": 0.002},
            "hills": {"color": "#1c1c4c", "far": "#4a4090", "height": 13, "seed": 613, "layers": 3, "style": "karst"},
            "stars": {"count": 1100, "color": "#ffffff", "seed": 617, "low": 8},
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

    def cdf_paving():
        # The festival city's road: warm cream flagstones lit gold by the lanterns, a
        # little sparkle of mica (V runs along the road).
        a, b = noise(4, 2, 11001), noise(16, 8, 11002)
        mica = speckle(11003, 50)

        def f(x, y):
            row = y // 8
            off = (row * 11) % 24
            if y % 8 == 0 or (x + off) % 24 == 0:
                return "#a07a4a"
            if (x, y) in mica:
                return "#fff4d0"
            return pick(["#d8b47e", "#e2c08a", "#eccc96", "#f4d8a4"], 0.1 + a(x, y) * 0.55 + b(x, y) * 0.3)

        return paint(f)

    def cdf_celestial():
        # The high roads to the palace: deep blue stone with a gold line down each edge
        # and little gold stars set into it (V along the road).
        a = noise(8, 4, 11011)

        def f(x, y):
            if x < 3 or x > 60:
                return "#f0c850"
            if x < 4 or x > 59:
                return "#7a5a1a"
            u, v = x % 32 - 16, y % 32 - 16
            if (abs(u) + abs(v) < 3) or (abs(u) < 1 and abs(v) < 5) or (abs(v) < 1 and abs(u) < 5):
                return "#ffe68a"
            if (x // 16 + y // 8) % 2 == 0 and (x % 16 == 0 or y % 8 == 0):
                return "#2a2c6a"
            return pick(["#3a3e8a", "#424896", "#4a52a2", "#545cae"], a(x, y))

        return paint(f)

    def cdf_royal():
        # The Procession Causeway and the finale: a crimson runner, gold borders with
        # cloud scrolls, a gold dragon-scale band down the middle.
        a = noise(8, 2, 11021)

        def f(x, y):
            if x < 5 or x > 58:
                k = (y + (x if x < 5 else 63 - x) * 2) % 8
                return "#f4cc50" if k < 4 else "#c8901c"
            if x < 7 or x > 56:
                return "#6a0e12"
            if 29 <= x <= 34:
                return "#f0c040" if (y + abs(x - 31)) % 6 < 3 else "#b07818"
            return pick(["#a01820", "#ac2028", "#b82a2c"], a(x, y))

        return paint(f)

    def cdf_kerb():
        # Gold and white kerb blocks.
        def f(x, y):
            if y % 16 < 2:
                return "#6a4a1a"
            return "#f6f0e2" if (x // 8) % 2 == 0 else "#e8b830"

        return paint(f)

    # ---------------------------------------------------------------- stone, rails, palace

    def cdf_marble():
        # White palace marble with faint violet veins.
        a, b = noise(8, 4, 11031), noise(4, 8, 11032)

        def f(x, y):
            if abs(b(x, y) - 0.5) < 0.025:
                return "#b8aee0"
            if y % 32 == 0:
                return "#c8c0d8"
            return pick(["#e6e2f0", "#ece8f4", "#f2eff8", "#f8f6fc"], a(x, y))

        return paint(f)

    def cdf_balustrade():
        # A white and gold balustrade: marble posts with gold caps, pierced panels lit
        # warm from behind (both sides of the high bridges).
        def f(x, y):
            if x % 16 < 3:
                return "#f4d060" if y < 4 else "#e8e4f0"
            if y < 4:
                return "#e8b830"
            if y > 27:
                return "#d8d4e4"
            if 8 < y < 24 and 5 < x % 16 < 14:
                cx, cy = x % 16 - 9.5, y - 16
                if cx * cx / 9 + cy * cy / 40 < 1:
                    return "#ffd890"
                return "#c8c4d8"
            return "#ecebf4"

        return paint(f)

    def cdf_lantern_rail():
        # A red lacquer rail strung with little glowing lanterns.
        def f(x, y):
            if x % 16 < 2:
                return "#e8b830" if y < 4 else "#7a1014"
            if y < 4:
                return "#b81c1e"
            cx, cy = x % 16 - 9, y - 17
            if cx * cx + cy * cy * 0.6 < 16:
                return "#ffd070" if cx * cx + cy * cy * 0.6 < 6 else "#ff7a30"
            if y > 28:
                return "#9a1418"
            return "#3a0a14"

        return paint(f)

    def cdf_dome():
        # Deep blue glazed dome tiles with gold stars.
        a = noise(8, 4, 11041)

        def f(x, y):
            u, v = x % 16 - 8, y % 16 - 8
            if (abs(u) + abs(v) < 2) or (u == 0 and abs(v) < 4) or (v == 0 and abs(u) < 4):
                return "#ffd860"
            if y % 4 == 0:
                return "#141a50"
            return pick(["#1e2a78", "#24338a", "#2c3e9c", "#3a4eae"], a(x, y) * 0.7 + ((x + (y // 4) * 2) % 4) * 0.06)

        return paint(f)

    def cdf_gold():
        # Bright gilding (glows a little under the fireworks).
        a = noise(8, 4, 11051)

        def f(x, y):
            if (x * 2 + y) % 11 == 0:
                return "#fff6c0"
            return pick(["#b88420", "#d09a28", "#e8b638", "#f8d050"], a(x, y))

        return paint(f)

    def cdf_window():
        # Tall arched palace windows, blazing with light.
        def f(x, y):
            u, v = x % 16, y % 32
            if u < 3 or u > 12 or v > 29:
                return "#e8e4f2"
            top = 8 - math.sqrt(max(0.0, 20.25 - (u - 7.5) ** 2))
            if v < top + 2:
                return "#e8e4f2" if v < top else "#d8a830"
            if u in (7, 8) or v in (15, 16):
                return "#d8a830"
            return "#fff0a0" if v < 15 else "#ffd060"

        return paint(f)

    def cdf_star_glass():
        # The observatory's glass: deep blue panes with stars and glowing gold leading.
        a = noise(8, 4, 11061)
        st = speckle(11062, 26)

        def f(x, y):
            if x % 16 == 0 or y % 16 == 0:
                return "#ffd060"
            if (x, y) in st:
                return "#ffffff"
            return pick(["#1a2a7a", "#22348e", "#2c42a6", "#3a56c0"], a(x, y))

        return paint(f)

    def cdf_mural():
        # A glowing mural: the dragon as a god among the stars (a gold serpent coiling
        # round a radiant star on a night-blue field). Our own design. 64x64.
        def f(x, y):
            cx, cy = x - 31.5, y - 31.5
            r = math.hypot(cx, cy)
            if x < 2 or x > 61 or y < 2 or y > 61:
                return "#e8b830"
            # The star at the centre.
            a = math.atan2(cy, cx)
            spike = 6 + 4 * abs(math.cos(a * 4))
            if r < spike:
                return "#fff8d0" if r < 4 else "#ffd860"
            # The serpent: a band coiling outward.
            s = (r / 26.0) * 1.6 - a / math.tau
            if 9 < r < 28 and abs((s % 1.0) - 0.5) < 0.12:
                return "#f4c040" if (x + y) % 3 else "#b07818"
            if 9 < r < 28 and abs((s % 1.0) - 0.5) < 0.16:
                return "#7a4a10"
            if math.hypot(cx - 20, cy + 16) < 3.5:
                return "#f4c040"  # its head
            if (x * 7 + y * 13) % 37 == 0:
                return "#ffffff"
            return "#141c5a" if r < 29 else "#0c1240"

        return paint(f, 64, 64)

    def emblem(base, ring, glyph, star=False):
        """The festival banners: a gold ring on a field, inside it a coiled dragon (or a
        radiant star), a gold fringe at the foot. 64x64."""

        def f(x, y):
            cx, cy = x - 31.5, y - 26.5
            r = math.hypot(cx, cy)
            if 16 < r < 19:
                return ring
            if r < 16:
                a = math.atan2(cy, cx)
                if star:
                    spike = 5 + 9 * abs(math.cos(a * 4)) ** 3
                    return glyph if r < spike else base
                s = (r / 16.0) * 2.2 + a / math.tau
                if abs((s % 1.0) - 0.5) < 0.17 and r > 4:
                    return glyph
                if math.hypot(cx - 7, cy + 9) < 3.2:
                    return glyph
                return base
            if y > 52 and (x // 6) % 2 == 0:
                return ring
            if x < 3 or x > 60 or y < 2:
                return ring
            return base

        return paint(f, 64, 64)

    def cdf_chevron():
        # Glowing red-and-white turn boards in gold frames, arrows along +U.
        def f(x, y):
            if y < 2 or y > 29:
                return "#e8b830"
            u = (x - abs(y - 15.5) * 0.8) % 16
            return "#fff4ec" if u < 8 else "#e0242a"

        return paint(f)

    # ---------------------------------------------------------------- land, water, sky

    def cdf_grass():
        # Night grass: deep blue-green, petals fallen in it.
        a, b = noise(8, 4, 11101), noise(16, 8, 11102)
        pet = speckle(11103, 30)

        def f(x, y):
            if (x, y) in pet:
                return "#f4a0d0"
            return pick(["#1e4a4a", "#245652", "#2a625a", "#326e62"], a(x, y) * 0.6 + b(x, y) * 0.4)

        return paint(f)

    def cdf_karst():
        # Karst limestone by moonlight: blue-grey, violet in the cracks, moss.
        a, b = noise(4, 2, 11111), noise(16, 4, 11112)

        def f(x, y):
            band = (y + int(a(x, y) * 6)) % 11
            if band == 0:
                return "#2a2450"
            if b(x, y) > 0.72:
                return pick(["#2e5a4e", "#386a5a"], a(x, y))
            return pick(["#5a5e8a", "#646a96", "#6e76a2", "#7a82ae", "#868eba"], a(x, y) * 0.55 + b(x, y) * 0.45)

        return paint(f)

    def cdf_lagoon():
        # The lagoon at night: deep glowing turquoise, gold ripples of lantern light.
        a, b = noise(8, 4, 11121), noise(16, 8, 11122)

        def f(x, y):
            rip = abs(math.sin(x * 0.35 + a(x, y) * 5) * math.sin(y * 0.5 + b(x, y) * 4))
            if rip > 0.94:
                return "#ffe0a0"
            if rip > 0.86:
                return "#a8f4f4"
            return pick(["#127a8e", "#168898", "#1c96a4", "#24a6b2", "#30b6c0"], 0.1 + rip * 0.45 + b(x, y) * 0.35)

        return paint(f)

    def cdf_cloud():
        # The sea of cloud below the Star Bridge: lit violet and pink from the city.
        a, b = noise(4, 2, 11131), noise(8, 4, 11132)

        def f(x, y):
            return pick(["#6a5ab0", "#7a6ac0", "#8c7ccc", "#a08ed8", "#b8a4e4", "#d4bcec"], a(x, y) * 0.6 + b(x, y) * 0.4)

        return paint(f)

    def cdf_abyss():
        # The chasm's floor, far below the clouds.
        a = noise(6, 3, 11141)

        def f(x, y):
            return pick(["#0a0a2a", "#0e0e34", "#12123e"], a(x, y))

        return paint(f)

    T = "celestial_dragon_festival"
    return [
        ("cdf_paving", "Festival Paving", T, "road", cdf_paving, 5, None),
        ("cdf_celestial", "Celestial Road", T, "road", cdf_celestial, 8, GLOW(0.12)),
        ("cdf_royal", "Processional Runner", T, "road", cdf_royal, 8, None),
        ("cdf_kerb", "Gold Kerb", T, "road", cdf_kerb, 2, GLOW(0.1)),
        ("cdf_marble", "Palace Marble", T, "wall", cdf_marble, 4, None),
        ("cdf_balustrade", "Gilded Balustrade", T, "wall", cdf_balustrade, 3, GLOW(0.22)),
        ("cdf_lantern_rail", "Lantern Rail", T, "wall", cdf_lantern_rail, 3, GLOW(0.45, flicker=0.12)),
        ("cdf_dome", "Star Dome Tiles", T, "wall", cdf_dome, 3, GLOW(0.15)),
        ("cdf_gold", "Festival Gold", T, "wall", cdf_gold, 1, GLOW(0.4, pulse=0.12, period=5.0)),
        ("cdf_window", "Palace Windows", T, "wall", cdf_window, 2, GLOW(1.0, flicker=0.06)),
        ("cdf_star_glass", "Star Glass", T, "wall", cdf_star_glass, 3, GLOW(0.7, pulse=0.2, period=6.0)),
        ("cdf_mural", "Celestial Dragon Mural", T, "wall", cdf_mural, 4, GLOW(0.6, pulse=0.15, period=7.0)),
        ("cdf_banner_dragon", "Festival Dragon Banner", T, "wall", lambda: emblem("#b8141e", "#f0c040", "#f8d860"), 3, SWAY),
        ("cdf_banner_star", "Celestial Star Banner", T, "wall", lambda: emblem("#1a2470", "#f0c040", "#fff0a0", star=True), 3, SWAY),
        ("cdf_chevron", "Festival Chevrons", T, "wall", cdf_chevron, 4, GLOW(0.5)),
        ("cdf_grass", "Night Grass", T, "grass", cdf_grass, 6, None),
        ("cdf_karst", "Moonlit Karst", T, "wall", cdf_karst, 12, None),
        ("cdf_lagoon", "Night Lagoon", T, "deep_water", cdf_lagoon, 14,
         {"scrollU": 0.004, "scrollV": 0.006, "wave": 0.04, "wavePeriod": 7, "lagoon": 0.8, "glow": 0.25}),
        ("cdf_cloud", "Cloud Sea", T, "water", cdf_cloud, 34,
         {"scrollU": 0.004, "scrollV": 0.0015, "wave": 0.05, "wavePeriod": 11, "opacity": 0.7, "glow": 0.55}),
        ("cdf_abyss", "Chasm Floor", T, "abyss", cdf_abyss, 14, None),
    ]
