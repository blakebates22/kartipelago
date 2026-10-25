# The ruined courses' paint (Adventure's treasure map challenge: each world's courses after
# the dragons' attack). Riverbend Palms in ruins first: a smoky, ember-lit valley under a
# hazy orange sky; scorched grass, sooty roads, charred planks, embers. Painted by
# make_textures.py; every pixel generated here (original artwork, 64x32).
# SPDX-License-Identifier: MIT

import math

RIVERBEND = {
    "id": "riverbend_ruins",
    "name": "Riverbend in Ruins",
    "description": "The river valley after the dragons' attack: a hazy orange sky full of smoke, scorched meadows, sooty roads, charred bridges and smouldering embers",
    "environment": {
        "sky": "#c8865a",
        "fog": {"enabled": True, "color": "#b48a72", "near": 140, "far": 760},
        "sun": {"color": "#ffc890", "intensity": 2.0, "direction": [-0.45, 0.5, -0.7]},
        "ambient": {"sky": "#e8c0a0", "ground": "#4a3a2a", "intensity": 1.15},
        "skyDome": {
            "top": "#6a5a6a",
            "horizon": "#e8a070",
            "bottom": "#b07a5a",
            "sun": {"color": "#ffd8a0", "size": 13, "glow": "#ff9a50", "elevation": 12},
            "clouds": {"count": 46, "color": "#8a7a74", "shade": "#4a3e3e", "seed": 307, "low": 5, "high": 22, "drift": 0.009},
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

    def ash():
        """Scorched grass: black and grey ash, a few burnt-orange stalks, embers."""
        a, b = noise(4, 2, 9701), noise(16, 8, 9702)
        em = speckle(9703, 10)
        stalk = speckle(9704, 40)

        def f(x, y):
            if (x, y) in em:
                return "#ff8a2a"
            if (x, y) in stalk:
                return "#8a6a3a"
            return pick(["#1e1a18", "#2a2420", "#38302a", "#4a4038", "#5a5048"], a(x, y) * 0.55 + b(x, y) * 0.45)

        return paint(f)

    def sooty_road():
        """The valley's orange dirt road darkened with soot, scorch streaks across it."""
        a, b = noise(4, 2, 9711), noise(16, 8, 9712)
        grit = speckle(9713, 14)

        def f(x, y):
            if (x, y) in grit:
                return "#2a2018"
            streak = 0.25 if (y + int(a(x, 0) * 10)) % 16 < 3 else 0
            return pick(["#5a3a22", "#6e4628", "#82552e", "#946236", "#a8723e"], 0.2 + a(x, y) * 0.45 + b(x, y) * 0.3 - streak)

        return paint(f)

    def char_planks():
        """Bridge boards burnt black, glowing at their cracks."""
        a = noise(4, 8, 9721)

        def f(x, y):
            board = y // 8
            yy = y % 8
            if yy == 7:
                return "#ff7a2a" if (x * 7 + board * 13) % 23 == 0 else "#0e0a08"
            crack = (x + board * 11) % 19 == 0 and yy in (2, 3, 4)
            if crack:
                return "#e8601e"
            return pick(["#1a1410", "#241a14", "#30241a", "#3e2e20", "#4e3a28"], 0.2 + a(x, y) * 0.5 + (0.15 if yy == 0 else 0))

        return paint(f)

    def char_wood():
        a = noise(8, 2, 9731)

        def f(x, y):
            v = 0.3 + 0.4 * math.sin(x * 0.8 + a(x, y) * 5) + a(x, y) * 0.3
            if (x * 3 + y * 5) % 37 == 0:
                return "#ff7a2a"
            return pick(["#141010", "#201814", "#2c2018", "#3a2a1e"], v)

        return paint(f)

    def ember():
        a, b = noise(4, 2, 9741), noise(16, 8, 9742)

        def f(x, y):
            return pick(["#6a1a08", "#a8300e", "#e85a1a", "#ff8a2a", "#ffc860"], a(x, y) * 0.6 + b(x, y) * 0.4)

        return paint(f)

    def rubble():
        a, b = noise(8, 4, 9751), noise(16, 8, 9752)
        soot = speckle(9753, 60)

        def f(x, y):
            if (x, y) in soot:
                return "#1e1a18"
            crack = (x + int(a(x, y) * 9)) % 13 == 0 or (y + int(b(x, y) * 7)) % 9 == 0
            if crack:
                return "#3a2e24"
            return pick(["#6a5644", "#7c6650", "#8e765c", "#a08668", "#b29674"], 0.2 + a(x, y) * 0.5 + b(x, y) * 0.3)

        return paint(f)

    def singed():
        """The valley's grass dried and singed: olive and straw, soot specks, the odd
        surviving green tuft."""
        a, b = noise(4, 2, 9761), noise(16, 8, 9762)
        soot, green = speckle(9763, 40), speckle(9764, 12)

        def f(x, y):
            if (x, y) in soot:
                return "#2a241a"
            if (x, y) in green:
                return "#4a8a2a"
            return pick(["#5a5a26", "#6e6a2e", "#827a38", "#968a44", "#a89a52"], 0.1 + a(x, y) * 0.6 + b(x, y) * 0.3)

        return paint(f)

    T = "riverbend_ruins"
    return [
        ("ruin_ash", "Scorched Grass", T, "grass", ash, 6, None),
        ("ruin_grass", "Singed Grass", T, "grass", singed, 6, None),
        ("ruin_road", "Sooty Road", T, "road", sooty_road, 4, None),
        ("ruin_char_planks", "Charred Planks", T, "road", char_planks, 3, GLOW(0.15, 0.25, 3.0)),
        ("ruin_char", "Charred Wood", T, "wall", char_wood, 2, None),
        ("ruin_ember", "Embers", T, "wall", ember, 2, GLOW(0.9, 0.3, 2.2, 0.1)),
        ("ruin_rubble", "Rubble", T, "wall", rubble, 3, None),
    ]
