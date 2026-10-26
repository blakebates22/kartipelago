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


IMPACT = {
    "id": "impact_ruins",
    "name": "Impact Depths in Ruins",
    "description": "The pit after its roof fell in: a dusty, smoky afternoon pouring down great holes, ash in the shafts of light, the depths glowing through the haze",
    "environment": {
        "sky": "#b88a5e",
        "fog": {"enabled": True, "color": "#c4a07e", "near": 300, "far": 1900},
        "sun": {"color": "#ffd8a0", "intensity": 2.7, "direction": [-0.34, 0.86, -0.38]},
        "ambient": {"sky": "#d8b898", "ground": "#7a4a32", "intensity": 1.25},
        "skyDome": {
            "top": "#5a6a8a",
            "horizon": "#f0b070",
            "bottom": "#c89a78",
            "sun": {"color": "#ffe8c0", "size": 10, "glow": "#ffb060", "elevation": 52},
            "clouds": {"count": 34, "color": "#9a7a6a", "shade": "#5a3a30", "seed": 367, "low": 8, "high": 30, "drift": 0.008},
            "hills": {"color": "#a0644c", "far": "#c89a86", "height": 5, "seed": 213, "layers": 3, "style": "mesas"},
        },
    },
}


COVE = {
    "id": "cove_ruins",
    "name": "Coral Cove in Ruins",
    "description": "The cove after Tidewyrm's raid: a stormy late afternoon, smoke drifting off the headland, the lighthouse down, the sea grey-green under heavy cloud",
    "environment": {
        "sky": "#7a9aa8",
        "fog": {"enabled": True, "color": "#a8b8b4", "near": 260, "far": 1300},
        "sun": {"color": "#ffd8b0", "intensity": 2.4, "direction": [-0.35, 0.62, -0.7]},
        "ambient": {"sky": "#c8d8dc", "ground": "#b09a78", "intensity": 1.3},
        "skyDome": {
            "top": "#3a5a78",
            "horizon": "#e8b88a",
            "bottom": "#7aa8a8",
            "sun": {"color": "#fff0d8", "size": 9, "glow": "#ffc890", "elevation": 18},
            "clouds": {"count": 40, "color": "#9aa0a4", "shade": "#5a6068", "seed": 373, "low": 5, "high": 22, "drift": 0.01},
            "hills": {"color": "#2f6a4a", "far": "#88a8a0", "height": 5, "seed": 143, "layers": 2},
        },
    },
}


WRECK = {
    "id": "wreck_ruins",
    "name": "Shipwreck Bay in Ruins",
    "description": "The pirate cove after Tidewyrm's raid: a blood-orange dusk under smoke, the galleon broken in two, fires along the beach",
    "environment": {
        "sky": "#c86a4a",
        "fog": {"enabled": True, "color": "#c8907a", "near": 260, "far": 1300},
        "sun": {"color": "#ffb070", "intensity": 2.4, "direction": [-0.6, 0.3, -0.74]},
        "ambient": {"sky": "#e0a888", "ground": "#8a5a3a", "intensity": 1.3},
        "skyDome": {
            "top": "#4a3a5a",
            "horizon": "#ff9a50",
            "bottom": "#a8706a",
            "sun": {"color": "#ffd8a0", "size": 12, "glow": "#ff8040", "elevation": 8},
            "clouds": {"count": 40, "color": "#7a5a5a", "shade": "#3a2a30", "seed": 379, "low": 5, "high": 22, "drift": 0.01},
            "hills": {"color": "#3a4a3a", "far": "#9a7a7a", "height": 5, "seed": 151, "layers": 2},
        },
    },
}


ISLE = {
    "id": "isle_ruins",
    "name": "Volcano Isle in Ruins",
    "description": "The island after Tidewyrm's raid woke its volcano: a sulphur-yellow noon under an ash plume, lava crusting across the flats, the village burnt, steam off the lagoon",
    "environment": {
        "sky": "#b89a6a",
        "fog": {"enabled": True, "color": "#c8a888", "near": 240, "far": 1200},
        "sun": {"color": "#ffd890", "intensity": 2.3, "direction": [0.42, 0.78, -0.46]},
        "ambient": {"sky": "#e8c8a0", "ground": "#5a3020", "intensity": 1.25},
        "skyDome": {
            "top": "#5a4a5a",
            "horizon": "#f0b878",
            "bottom": "#a08070",
            "sun": {"color": "#fff0c0", "size": 10, "glow": "#ffb060", "elevation": 34},
            "clouds": {"count": 44, "color": "#6a5a58", "shade": "#2a2024", "seed": 383, "low": 6, "high": 26, "drift": 0.012},
            "hills": {"color": "#3a3a2a", "far": "#a08a7a", "height": 6, "seed": 159, "layers": 2},
        },
    },
}


SPLASH = {
    "id": "splash_ruins",
    "name": "Splash Lagoon in Ruins",
    "description": "The water park after Tidewyrm's raid: an overcast, drizzly afternoon, the slide tower toppled, the pools drained and murky, smoke from the cabanas",
    "environment": {
        "sky": "#8aa4b4",
        "fog": {"enabled": True, "color": "#b0c0c4", "near": 240, "far": 1200},
        "sun": {"color": "#f0e8d8", "intensity": 2.2, "direction": [-0.3, 0.84, -0.44]},
        "ambient": {"sky": "#d0dce0", "ground": "#a89878", "intensity": 1.3},
        "skyDome": {
            "top": "#4a6680",
            "horizon": "#d8e0e0",
            "bottom": "#8ab0b4",
            "sun": {"color": "#fff8e8", "size": 8, "glow": "#e8e0c8", "elevation": 40},
            "clouds": {"count": 46, "color": "#a0a8ac", "shade": "#5a6268", "seed": 389, "low": 5, "high": 22, "drift": 0.01},
            "hills": {"color": "#3a6a52", "far": "#90aaa4", "height": 4, "seed": 163, "layers": 2},
        },
    },
}


KEEP = {
    "id": "keep_ruins",
    "name": "Dragonspire Keep Remade",
    "description": "The castle after the Chosen One's sacrifice: a strange gold-and-violet dusk, the land split and heaved, light still pouring from the sky where the blast tore it",
    "environment": {
        "sky": "#8a6ab8",
        "fog": {"enabled": True, "color": "#b89ac8", "near": 300, "far": 1800},
        "sun": {"color": "#ffd8a0", "intensity": 2.6, "direction": [-0.4, 0.55, -0.73]},
        "ambient": {"sky": "#d8c0f0", "ground": "#6a4a5a", "intensity": 1.35},
        "skyDome": {
            "top": "#3a2a6a",
            "horizon": "#ffb878",
            "bottom": "#a07ab0",
            "sun": {"color": "#fff0c8", "size": 14, "glow": "#ffd090", "elevation": 14},
            "clouds": {"count": 36, "color": "#c8a0d8", "shade": "#5a3a6a", "seed": 383, "low": 6, "high": 28, "drift": 0.008},
            "hills": {"color": "#4a3a6a", "far": "#a888c0", "height": 6, "seed": 171, "layers": 3},
        },
    },
}


EMERALD = {
    "id": "emerald_ruins",
    "name": "Dragon Canyon Remade",
    "description": "The canyon after the Chosen One's sacrifice: the jungle castle's canyon torn open under a gold-and-violet afterglow, the river steaming where the blast fused rock across it",
    "environment": {
        "sky": "#9a6aa8",
        "fog": {"enabled": True, "color": "#c09aa8", "near": 300, "far": 1800},
        "sun": {"color": "#ffd090", "intensity": 2.6, "direction": [-0.7, 0.3, -0.65]},
        "ambient": {"sky": "#e0c0e0", "ground": "#6a4a3a", "intensity": 1.3},
        "skyDome": {
            "top": "#3a2a5a",
            "horizon": "#ffa868",
            "bottom": "#a07090",
            "sun": {"color": "#fff0c0", "size": 14, "glow": "#ffc070", "elevation": 12},
            "clouds": {"count": 34, "color": "#c098c0", "shade": "#5a3a5a", "seed": 389, "low": 6, "high": 28, "drift": 0.008},
            "hills": {"color": "#5a3a4a", "far": "#b08aa0", "height": 6, "seed": 173, "layers": 3, "style": "mesas"},
        },
    },
}


HOLD = {
    "id": "ember_hold_ruins",
    "name": "Emberdeep Hold Remade",
    "description": "The mountain fortress after the Chosen One's sacrifice: the mountain split in two, embers glowing in its heart, the storm torn open on a violet dawn",
    "environment": {
        "sky": "#4a3a6a",
        "fog": {"enabled": True, "color": "#6a4a6a", "near": 260, "far": 1500},
        "sun": {"color": "#ffc8a0", "intensity": 2.0, "direction": [-0.22, 0.62, -0.75]},
        "ambient": {"sky": "#a88ad0", "ground": "#5a3a3a", "intensity": 1.45},
        "skyDome": {
            "top": "#1a1438",
            "horizon": "#ff8a5a",
            "bottom": "#4a2a4a",
            "sun": {"color": "#ffe0c0", "size": 12, "glow": "#ff9a60", "elevation": 10},
            "clouds": {"count": 40, "color": "#6a4a7a", "shade": "#2a1a3a", "seed": 397, "low": 6, "high": 30, "drift": 0.01},
            "hills": {"color": "#2a1a2e", "far": "#6a4a6a", "height": 7, "seed": 179, "layers": 3},
        },
    },
}


MOON = {
    "id": "moon_ruins",
    "name": "Moonstone Kingdom Remade",
    "description": "The moonlit kingdom after the Chosen One's sacrifice: the Palace Mount split open, crystal shards glowing in the rubble, the huge moon low and red-gold through drifting ash",
    "environment": {
        "sky": "#2a2048",
        "fog": {"enabled": True, "color": "#4a3a6a", "near": 300, "far": 1700},
        "sun": {"color": "#ffd8b0", "intensity": 1.7, "direction": [-0.3, 0.6, -0.74]},
        "ambient": {"sky": "#9a8ad8", "ground": "#4a3a5a", "intensity": 1.5},
        "skyDome": {
            "top": "#0a0820",
            "horizon": "#c06a6a",
            "bottom": "#3a2a4a",
            "sun": {"color": "#ffd8a8", "size": 22, "glow": "#e08a6a", "elevation": 14, "face": "moon"},
            "clouds": {"count": 30, "color": "#5a4a7a", "shade": "#2a1a42", "seed": 401, "low": 6, "high": 30, "drift": 0.006},
            "hills": {"color": "#1a1430", "far": "#4a3a6a", "height": 6, "seed": 181, "layers": 3},
            "stars": {"count": 500, "color": "#ffffff", "seed": 187, "low": 12},
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
