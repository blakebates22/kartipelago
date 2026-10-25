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

CASCADE = {
    "id": "cascade_ruins",
    "name": "Cascade in Ruins",
    "description": "The jungle canyon after the dragons' attack: smoke hanging in the canyon, a hazy amber light, burnt patches in the jungle, the viaduct fallen",
    "environment": {
        "sky": "#b89070",
        "fog": {"enabled": True, "color": "#a08c74", "near": 60, "far": 380},
        "sun": {"color": "#ffd8a8", "intensity": 1.8, "direction": [-0.4, 0.8, 0.3]},
        "ambient": {"sky": "#e0ccb0", "ground": "#3a3a22", "intensity": 1.2},
        "skyDome": {
            "top": "#6a6a78",
            "horizon": "#e0b080",
            "bottom": "#a08c74",
            "sun": {"color": "#ffe0b0", "size": 10, "glow": "#ffa860", "elevation": 26},
            "clouds": {"count": 34, "color": "#8a8078", "shade": "#4a4440", "seed": 311, "low": 10, "high": 28, "drift": 0.008},
            "hills": {"color": "#2a3a24", "far": "#8a8a74", "height": 13, "seed": 4, "layers": 3},
        },
    },
}

BONEBOG = {
    "id": "bonebog_ruins",
    "name": "Bonebog in Ruins",
    "description": "The swamp after the dragons' attack: the great tree fallen, smoke over the water, a red-gold dusk, burnt boardwalks and charred mangroves",
    "environment": {
        "sky": "#c0805a",
        "fog": {"enabled": True, "color": "#8a7a5a", "near": 60, "far": 520},
        "sun": {"color": "#ffc088", "intensity": 2.1, "direction": [-0.55, 0.5, 0.55]},
        "ambient": {"sky": "#e0c0a0", "ground": "#34402a", "intensity": 1.2},
        "skyDome": {
            "top": "#5a4a6a",
            "horizon": "#f0a060",
            "bottom": "#8a7a5a",
            "sun": {"color": "#ffe0b0", "size": 12, "glow": "#ff9050", "elevation": 10},
            "clouds": {"count": 34, "color": "#8a7068", "shade": "#4a3a3a", "seed": 313, "low": 8, "high": 24, "drift": 0.007},
            "hills": {"color": "#2a3a1c", "far": "#7a6a4a", "height": 24, "seed": 41, "layers": 3},
        },
    },
}

EMBER = {
    "id": "ember_ruins",
    "name": "Ember Peak in Ruins",
    "description": "The volcanic field after the eruption the dragons woke: a dark red sky full of ash, the volcano's flank slid down over the home straight, fires everywhere",
    "environment": {
        "sky": "#8a3a24",
        "fog": {"enabled": True, "color": "#7a3a28", "near": 140, "far": 900},
        "sun": {"color": "#ffb878", "intensity": 2.4, "direction": [0.5, 0.45, -0.7]},
        "ambient": {"sky": "#f0a080", "ground": "#3a1e16", "intensity": 1.25},
        "skyDome": {
            "top": "#3a1418",
            "horizon": "#ff8a40",
            "bottom": "#8a3a24",
            "sun": {"color": "#ffd0a0", "size": 12, "glow": "#ff7a30", "elevation": 14},
            "clouds": {"count": 44, "color": "#6a4a44", "shade": "#2e1c1c", "seed": 317, "low": 6, "high": 24, "drift": 0.01},
        },
    },
}

FROST = {
    "id": "frost_ruins",
    "name": "Frostveil in Ruins",
    "description": "The citadel after the dragons came: moonlight through smoke, fires burning in the snow, the Bridge of Giants fallen into the valley",
    "environment": {
        "sky": "#3a3466",
        "fog": {"enabled": True, "color": "#8a7a9a", "near": 120, "far": 760},
        "sun": {"color": "#c4c6f0", "intensity": 1.7, "direction": [-0.35, 0.8, 0.48]},
        "ambient": {"sky": "#b0a8d8", "ground": "#4a3a52", "intensity": 1.4},
        "skyDome": {
            "top": "#1a1a48",
            "horizon": "#c8906a",
            "bottom": "#7a6a8a",
            "sun": {"color": "#f4f0ff", "size": 9, "glow": "#d8b0a0", "elevation": 24},
            "clouds": {"count": 34, "color": "#8a7a8a", "shade": "#4a3a4a", "seed": 319, "low": 8, "high": 26, "drift": 0.006},
            "hills": {"color": "#5a5a90", "far": "#9a8aa8", "height": 17, "seed": 31, "layers": 3},
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
