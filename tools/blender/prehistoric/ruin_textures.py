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


SUMMIT = {
    "id": "summit_ruins",
    "name": "Snowy Summit in Ruins",
    "description": "The frozen lake after the dragons felled the great tree: the bright day gone hazy with smoke, the sun a pale disc, fires in the forest and on the fallen trunk",
    "environment": {
        "sky": "#a0a4b4",
        "fog": {"enabled": True, "color": "#b8aca4", "near": 150, "far": 900},
        "sun": {"color": "#ffe0c0", "intensity": 2.2, "direction": [0.42, 0.74, 0.52]},
        "ambient": {"sky": "#dcdce6", "ground": "#6a6472", "intensity": 1.3},
        "skyDome": {
            "top": "#5a6484",
            "horizon": "#e8c0a0",
            "bottom": "#c8bcb4",
            "sun": {"color": "#fff0d8", "size": 10, "glow": "#ffc890", "elevation": 30},
            "clouds": {"count": 40, "color": "#9a9090", "shade": "#5a5050", "seed": 323, "low": 8, "high": 26, "drift": 0.007},
            "hills": {"color": "#8a90a8", "far": "#c0bcc4", "height": 16, "seed": 67, "layers": 3},
        },
    },
}


HEARTH = {
    "id": "hearth_ruins",
    "name": "Hearthglow in Ruins",
    "description": "The Christmas village after the dragons came: the twilight turned smoky red with fire, the stars dimmed by smoke, burning cottages, the stone bridge in the river",
    "environment": {
        "sky": "#3a2250",
        "fog": {"enabled": True, "color": "#6a4a6a", "near": 160, "far": 900},
        "sun": {"color": "#d8b8e8", "intensity": 1.7, "direction": [-0.38, 0.72, 0.58]},
        "ambient": {"sky": "#b896d8", "ground": "#5a3a5a", "intensity": 1.5},
        "skyDome": {
            "top": "#140a2a",
            "horizon": "#e0784a",
            "bottom": "#7a4a6a",
            "sun": {"color": "#f6e8ff", "size": 5, "glow": "#d8a0b0", "elevation": 34},
            "clouds": {"count": 30, "color": "#7a5a6a", "shade": "#3a2a3a", "seed": 331, "low": 4, "high": 18, "drift": 0.006},
            "hills": {"color": "#3a2a5a", "far": "#8a5a8a", "height": 15, "seed": 73, "layers": 3},
            "stars": {"count": 250, "color": "#ffffff", "seed": 79, "low": 14},
        },
    },
}


AURORA = {
    "id": "aurora_ruins",
    "name": "Aurora Rift in Ruins",
    "description": "The glacier after the dragons brought its roof down: the caverns open to the night, the northern lights blazing through the smoke of fires burning on the ice",
    "environment": {
        "sky": "#140c2c",
        "fog": {"enabled": True, "color": "#3a2448", "near": 220, "far": 1300},
        "sun": {"color": "#c8c0ff", "intensity": 1.6, "direction": [0.3, 0.78, -0.55]},
        "ambient": {"sky": "#9a98f0", "ground": "#3a2440", "intensity": 1.55},
        "skyDome": {
            "top": "#060420",
            "horizon": "#a8402c",
            "bottom": "#2a1430",
            "sun": {"color": "#f4f0ff", "size": 3.5, "glow": "#d8a8c0", "elevation": 40},
            "clouds": {"count": 22, "color": "#4a2c3c", "shade": "#20101c", "seed": 337, "low": 3, "high": 12, "drift": 0.005},
            "hills": {"color": "#141030", "far": "#5a3c70", "height": 17, "seed": 89, "layers": 3},
            "stars": {"count": 500, "color": "#ffffff", "seed": 97, "low": 10},
            "aurora": {"count": 9, "seed": 5, "low": 16, "high": 85, "speed": 1.2, "intensity": 1.4, "azimuth": 160,
                       "colors": ["#2effa0", "#36d8ff", "#9a5aff", "#ff4ab8"]},
        },
    },
}


CANYON = {
    "id": "canyon_ruins",
    "name": "Canyon Dash in Ruins",
    "description": "The canyon after the dragons came: a hazy orange afternoon full of dust and smoke, the great bridge broken, rockslides down the far side",
    "environment": {
        "sky": "#c8844a",
        "fog": {"enabled": True, "color": "#c49a7a", "near": 320, "far": 1900},
        "sun": {"color": "#ffc888", "intensity": 2.7, "direction": [-0.62, 0.52, 0.58]},
        "ambient": {"sky": "#e8b890", "ground": "#7a3a2c", "intensity": 1.25},
        "skyDome": {
            "top": "#6a4a5a",
            "horizon": "#f0a060",
            "bottom": "#c89478",
            "sun": {"color": "#ffe0b0", "size": 11, "glow": "#ff9a50", "elevation": 16},
            "clouds": {"count": 36, "color": "#9a7a6a", "shade": "#5a3a30", "seed": 341, "low": 8, "high": 30, "drift": 0.008},
            "hills": {"color": "#a0604c", "far": "#c89a8a", "height": 5, "seed": 103, "layers": 3, "style": "mesas"},
        },
    },
}


OASIS = {
    "id": "oasis_ruins",
    "name": "Oasis Haven in Ruins",
    "description": "The oasis after the dragons came: a smoky amber dusk, the watchtower toppled, the camp burnt, ash on the wind",
    "environment": {
        "sky": "#b8785a",
        "fog": {"enabled": True, "color": "#b89a84", "near": 300, "far": 1800},
        "sun": {"color": "#ffb878", "intensity": 2.6, "direction": [0.55, 0.45, -0.7]},
        "ambient": {"sky": "#e0b494", "ground": "#6a3a2a", "intensity": 1.25},
        "skyDome": {
            "top": "#4a4a62",
            "horizon": "#e89a62",
            "bottom": "#c8987a",
            "sun": {"color": "#ffd8a8", "size": 12, "glow": "#ff8a48", "elevation": 12},
            "clouds": {"count": 40, "color": "#8a6a62", "shade": "#4a302c", "seed": 353, "low": 8, "high": 30, "drift": 0.008},
            "hills": {"color": "#9a5e4c", "far": "#c0948a", "height": 5, "seed": 109, "layers": 3, "style": "mesas"},
        },
    },
}


GULCH = {
    "id": "gulch_ruins",
    "name": "Dry Gulch in Ruins",
    "description": "The ghost town burning under the full moon: smoke across the stars, the sky glowing orange over Main Street, the ridge slumped into the green chasm",
    "environment": {
        "sky": "#1e1030",
        "fog": {"enabled": True, "color": "#4a2a3a", "near": 260, "far": 1500},
        "sun": {"color": "#c4b8ff", "intensity": 1.5, "direction": [-0.22, 0.62, -0.75]},
        "ambient": {"sky": "#9a6ab8", "ground": "#6a3a3a", "intensity": 1.55},
        "skyDome": {
            "top": "#0a0620",
            "horizon": "#c8502e",
            "bottom": "#3a1a2a",
            "sun": {"color": "#f4e2ca", "size": 10, "glow": "#c08a6a", "elevation": 21, "face": "moon"},
            "clouds": {"count": 34, "color": "#5a3a4a", "shade": "#2a1420", "seed": 359, "low": 4, "high": 30, "drift": 0.006},
            "hills": {"color": "#2a1424", "far": "#6a2e3e", "height": 7, "seed": 157, "layers": 3, "style": "mesas"},
            "stars": {"count": 400, "color": "#ffffff", "seed": 163, "low": 14},
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
