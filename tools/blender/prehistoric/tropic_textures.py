# The beach world's paint (the Tropic Isles): Coral Cove's sunny cove and Shipwreck Bay's
# pirate cove at golden hour. Painted by make_textures.py; every pixel generated here
# (original artwork, 64x32; 64x64 for flags and signs).
# SPDX-License-Identifier: MIT

import math

COVE = {
    "id": "coral_cove",
    "name": "Coral Cove",
    "description": "A bright tropical cove at midday: white-gold sand, turquoise shallows over pink and orange coral, a red-and-white lighthouse on the headland, sun-bleached boardwalks with rope rails, striped beach huts, palms and sea stacks offshore",
    "environment": {
        "sky": "#38b4f4",
        "fog": {"enabled": True, "color": "#ccf2ff", "near": 300, "far": 1500},
        "sun": {"color": "#fff8e2", "intensity": 2.8, "direction": [-0.35, 0.82, -0.45]},
        "ambient": {"sky": "#e6f8ff", "ground": "#e0c890", "intensity": 1.3},
        "skyDome": {
            "top": "#1478e0",
            "horizon": "#c6f2ff",
            "bottom": "#9ee8f0",
            "sun": {"color": "#fffbe8", "size": 8, "glow": "#fff3b0", "elevation": 30},
            "clouds": {"count": 26, "color": "#ffffff", "shade": "#cfe8ff", "seed": 141, "low": 5, "high": 20, "drift": 0.006},
            "hills": {"color": "#2f8a5a", "far": "#9ad8d0", "height": 5, "seed": 143, "layers": 2},
        },
    },
}

WRECK = {
    "id": "shipwreck_bay",
    "name": "Shipwreck Bay",
    "description": "A pirate cove at golden hour: amber sand, a teal bay turning gold, the old galleon's dark planks and patched sails, Skull Rock, a log stockade, lanterns, barrels and treasure",
    "environment": {
        "sky": "#f2a25a",
        "fog": {"enabled": True, "color": "#f6c08a", "near": 260, "far": 1300},
        "sun": {"color": "#ffd29a", "intensity": 2.4, "direction": [0.75, 0.32, -0.55]},
        "ambient": {"sky": "#ffd8b0", "ground": "#8a5a3a", "intensity": 1.25},
        "skyDome": {
            "top": "#4a5ab0",
            "horizon": "#ffc27a",
            "bottom": "#f0a070",
            "sun": {"color": "#fff0c0", "size": 14, "glow": "#ffb060", "elevation": 9},
            "clouds": {"count": 22, "color": "#ffd0a0", "shade": "#c06a70", "seed": 151, "low": 4, "high": 18, "drift": 0.005},
            "hills": {"color": "#5a4a6a", "far": "#c88a8a", "height": 6, "seed": 153, "layers": 3},
        },
    },
}


ISLE = {
    "id": "volcano_isle",
    "name": "Volcano Isle",
    "description": "A tropical island on a clear morning: black volcanic sand, deep blue sea and a turquoise lagoon, jungle up the flanks, steaming hot springs, a fishing village of stilt huts, and the dormant volcano behind it all",
    "environment": {
        "sky": "#5ab8f0",
        "fog": {"enabled": True, "color": "#d4eef4", "near": 320, "far": 1700},
        "sun": {"color": "#fff4d8", "intensity": 2.7, "direction": [0.42, 0.78, -0.46]},
        "ambient": {"sky": "#d8f0ff", "ground": "#6a5a48", "intensity": 1.3},
        "skyDome": {
            "top": "#1868d0",
            "horizon": "#d0f0f6",
            "bottom": "#8ad8e4",
            "sun": {"color": "#fffbe8", "size": 9, "glow": "#ffeab0", "elevation": 38},
            "clouds": {"count": 28, "color": "#ffffff", "shade": "#c8dcf0", "seed": 157, "low": 6, "high": 24, "drift": 0.006},
            "hills": {"color": "#2a6a46", "far": "#88c0b8", "height": 6, "seed": 159, "layers": 2},
        },
    },
}


SPLASH = {
    "id": "splash_lagoon",
    "name": "Splash Lagoon",
    "description": "A seaside water park on a bright summer afternoon: candy-coloured slides and pools, the slide tower over the beach, striped cabanas and umbrellas, palms, bunting, and the Big Curl breaking over it all",
    "environment": {
        "sky": "#46c4f8",
        "fog": {"enabled": True, "color": "#d8f4ff", "near": 320, "far": 1600},
        "sun": {"color": "#fffaf0", "intensity": 2.9, "direction": [-0.3, 0.84, -0.44]},
        "ambient": {"sky": "#e8f8ff", "ground": "#e8d0a8", "intensity": 1.35},
        "skyDome": {
            "top": "#1a86e8",
            "horizon": "#d4f6ff",
            "bottom": "#a8ecf4",
            "sun": {"color": "#fffbe8", "size": 8, "glow": "#fff6c0", "elevation": 46},
            "clouds": {"count": 20, "color": "#ffffff", "shade": "#d8ecff", "seed": 161, "low": 6, "high": 24, "drift": 0.006},
            "hills": {"color": "#3a9a6a", "far": "#a8e0d8", "height": 4, "seed": 163, "layers": 2},
        },
    },
}


def materials(mt):
    noise, pick, paint, speckle = mt.noise, mt.pick, mt.paint, mt.speckle
    W, H = 64, 32

    def GLOW(g, pulse=None, period=4.0, flicker=None):
        fx = {"scrollU": 0, "scrollV": 0, "glow": g}
        if pulse:
            fx["pulse"] = pulse
            fx["pulsePeriod"] = period
        if flicker:
            fx["flicker"] = flicker
        return fx

    SWAY = {"scrollU": 0, "scrollV": 0, "sway": 0.08}

    # -------------------------------------------------------------- ground

    def sand(pal, seed, shells=8, pinks=5, peb=10, ripples=True):
        a, b = noise(4, 2, seed), noise(16, 8, seed + 1)
        sh, pk, pb = speckle(seed + 2, shells), speckle(seed + 3, pinks), speckle(seed + 4, peb)

        def f(x, y):
            if (x, y) in sh:
                return "#ffffff"
            if (x, y) in pk:
                return "#f8a8a0"
            if (x, y) in pb:
                return pal[0]
            r = 0.1 * math.sin((x / W) * math.tau * 2 + a(x, y) * 3 + (y / H) * math.tau * 2) if ripples else 0
            return pick(pal, 0.2 + a(x, y) * 0.4 + b(x, y) * 0.25 + r)

        return paint(f)

    def road(pal, edge, seed):
        """Packed sand: wheel-worn, with shell grit (`edge`: unused, kept for the call)."""
        a, b = noise(4, 2, seed), noise(16, 8, seed + 1)
        grit = speckle(seed + 2, 10)

        def f(x, y):
            if (x, y) in grit:
                return "#fff8ea"
            u = x % 32
            rut = 0.14 if u in (8, 9, 22, 23) else 0
            return pick(pal, 0.2 + a(x, y) * 0.45 + b(x, y) * 0.3 - rut)

        return paint(f)

    def water(pal, seed, glints=10, bands=2):
        a, b = noise(4, 2, seed), noise(8, 4, seed + 1)
        gl = speckle(seed + 2, glints)

        def f(x, y):
            if (x, y) in gl:
                return "#ffffff"
            wave = 0.15 * math.sin((x / W) * math.tau * bands + (y / H) * math.tau + a(x, y) * 5)
            return pick(pal, 0.2 + a(x, y) * 0.35 + b(x, y) * 0.25 + wave)

        return paint(f)

    def shallows(pal, sandy, seed):
        """Clear water over sand: caustic ripples, sand showing through."""
        a, b = noise(4, 4, seed), noise(16, 8, seed + 1)

        def f(x, y):
            c = abs(math.sin(x * 0.35 + a(x, y) * 6) + math.sin(y * 0.5 + b(x, y) * 6))
            if c < 0.12:
                return "#f4ffff"
            if b(x, y) > 0.72:
                return sandy
            return pick(pal, 0.2 + a(x, y) * 0.5 + b(x, y) * 0.3)

        return paint(f)

    def rock(pal, seed, barnacles=None):
        a, b = noise(4, 2, seed), noise(16, 8, seed + 1)
        bn = speckle(seed + 2, 18)

        def f(x, y):
            if barnacles and (x, y) in bn:
                return barnacles
            crack = (y + int(a(x, 0) * 8)) % 11 == 0
            if crack:
                return pal[0]
            return pick(pal, 0.15 + a(x, y) * 0.5 + b(x, y) * 0.35)

        return paint(f)

    # -------------------------------------------------------------- wood and rope

    def planks(pal, gap, seed, nails="#5a5a5a", knots=True):
        a, b = noise(2, 8, seed), noise(8, 16, seed + 1)
        r = mt.rng(seed + 2)
        tone = [r() for _ in range(8)]

        def f(x, y):
            board = y // 8
            yy = y % 8
            if yy == 7:
                return gap
            if yy == 0:
                return pal[-1]
            if (x + board * 23) % 32 in (3, 4) and yy in (2, 5):
                return nails
            if knots and (x + board * 13) % 41 == 7 and yy in (3, 4):
                return pal[0]
            grain = 0.5 + 0.5 * math.sin(x * 0.6 + board * 2.1 + a(x, y) * 5)
            return pick(pal, 0.1 + grain * 0.35 + b(x, y) * 0.25 + tone[board % 8] * 0.25)

        return paint(f)

    def rope_rail(post, rope, shade, back, seed):
        """A boardwalk rail: stout posts and two thick twisted ropes."""
        a = noise(8, 4, seed)

        def f(x, y):
            if x < 5:
                return pick(post, 0.3 + a(x, y) * 0.5 + (0.2 if x == 1 else 0))
            for yc in (7, 20):
                d = y - yc
                if -2 <= d <= 2:
                    twist = (x + d * 2) % 5
                    return shade if twist == 0 or abs(d) == 2 else rope
            return back

        return paint(f)

    def bark_post(pal, algae, seed):
        a = noise(8, 4, seed)

        def f(x, y):
            if y > 24:
                return pick(algae, a(x, y))
            v = 0.3 + 0.4 * math.sin(x * 0.9 + a(x, y) * 4) + a(x, y) * 0.3
            return pick(pal, v)

        return paint(f)

    def thatch(pal, seed):
        a = noise(16, 4, seed)

        def f(x, y):
            row = y // 6
            yy = y % 6
            off = (row * 5) % 7
            strand = (x + off) % 3 == 0
            if yy == 5:
                return pal[0]
            return pick(pal, 0.25 + a(x, y) * 0.45 - (0.2 if strand else 0) + yy / 20)

        return paint(f)

    def boards(pal, gap, seed):
        """Vertical painted boards (a beach hut's walls), the paint worn."""
        a, b = noise(4, 8, seed), noise(16, 16, seed + 1)
        wear = speckle(seed + 2, 40)

        def f(x, y):
            if x % 8 == 7:
                return gap
            if (x, y) in wear:
                return "#c8b490"
            return pick(pal, 0.25 + a(x, y) * 0.4 + b(x, y) * 0.3 + (0.15 if x % 8 == 0 else 0))

        return paint(f)

    def stripes(a_col, b_col, seed, w=8, edge=None):
        n = noise(8, 4, seed)

        def f(x, y):
            base = a_col if (x // w) % 2 == 0 else b_col
            if edge and y > 27:
                return edge if (x // 4) % 2 == 0 else base
            return base if n(x, y) > 0.2 else pick([base, "#ffffff"], 0.2)

        return paint(f)

    def bands(a_col, b_col, h=16):
        """Horizontal bands (the lighthouse), v going up the tower."""

        def f(x, y):
            return a_col if (y // h) % 2 == 0 else b_col

        return paint(f)

    def solid(pal, seed, cells=(4, 4)):
        a = noise(cells[0], cells[1], seed)
        return paint(lambda x, y: pick(pal, 0.2 + a(x, y) * 0.6))

    def coral(pal, dots, seed):
        a = noise(8, 4, seed)
        d = speckle(seed + 1, 60)

        def f(x, y):
            if (x, y) in d:
                return dots
            return pick(pal, 0.15 + a(x, y) * 0.7 + 0.15 * math.sin(x * 0.8 + y * 0.6))

        return paint(f)

    def lamp(pal):
        def f(x, y):
            u, v = (x % 16) - 7.5, y - 16
            return pick(pal, max(0.0, 1 - math.hypot(u / 9, v / 18)))

        return paint(f)

    def flag_cove(field, edge, shell, w=64, h=64):
        """Coral Cove's flag: a scallop shell fanned over waves (our own emblem)."""

        def f(x, y):
            if x < 3 or x > 60 or y < 3 or y > 60:
                return edge
            cx, cy = x - 31.5, y - 40.0
            r = math.hypot(cx, cy)
            ang = math.atan2(-cy, cx)
            if 0.2 < ang < math.pi - 0.2 and r < 22:
                rib = int((ang - 0.2) / ((math.pi - 0.4) / 9))
                if abs(((ang - 0.2) / ((math.pi - 0.4) / 9)) - rib - 0.5) > 0.42:
                    return edge
                return shell if rib % 2 == 0 else "#ffd6b8"
            if 44 <= y <= 47 and (x // 8) % 2 == 0:
                return edge
            if 50 <= y <= 53 and ((x + 4) // 8) % 2 == 0:
                return edge
            return field

        return paint(f, w, h)

    def sign_board(face, rim, glyph, w=64, h=64):
        """A wooden sign: an arrow and a palm (no words)."""
        a = noise(4, 8, 7071, w, h)

        def f(x, y):
            if x < 4 or x > 59 or y < 4 or y > 59:
                return rim
            if y % 12 == 0:
                return rim
            u, v = x - 32, y - 32
            if -18 < u < 10 and abs(v) < 4:
                return glyph
            if 10 <= u < 22 and abs(v) < 14 - (u - 10):
                return glyph
            return pick(face, 0.3 + a(x, y) * 0.5)

        return paint(f, w, h)

    # -------------------------------------------------------------- Shipwreck Bay

    def skull_flag(field, bone, w=64, h=64):
        """A pirate flag of our own: a round skull with a bandana, crossed oars."""

        def f(x, y):
            if y > 56 and (x // 6) % 2 == 0:
                return "#000000" if y > 60 else field
            u, v = x - 32, y - 26
            # crossed oars behind
            for sgn in (1, -1):
                if abs(u - sgn * v * 1.1) < 2.2 and abs(u) < 26:
                    return bone
            if math.hypot(u, v) < 12:
                if v < -5:
                    return "#c8303a"  # the bandana
                if math.hypot(u - 4.5, v + 0.5) < 3 or math.hypot(u + 4.5, v + 0.5) < 3:
                    return field
                if 5 < v < 9 and u % 3 == 0:
                    return field
                return bone
            if v >= 11 and v < 16 and abs(u) < 7:
                return bone
            return field

        return paint(f, w, h)

    def sailcloth(pal, patch, seed):
        a, b = noise(4, 8, seed), noise(16, 8, seed + 1)

        def f(x, y):
            if x % 16 == 0:
                return pal[0]  # seams
            if 20 <= x % 64 <= 30 and 6 <= y <= 14:
                if x % 64 in (20, 30) or y in (6, 14):
                    return pal[0]
                return patch
            return pick(pal, 0.3 + a(x, y) * 0.4 + b(x, y) * 0.25)

        return paint(f)

    def logs(pal, end, seed):
        """A stockade: upright logs, rounded, with a dark gap."""
        a = noise(4, 8, seed)

        def f(x, y):
            u = x % 8
            if u == 7:
                return "#2a160a"
            v = 0.15 + 0.6 * math.sin(math.pi * (u + 0.5) / 7) + a(x, y) * 0.25
            return pick(pal, v)

        return paint(f)

    def treasure():
        sp = speckle(9181, 90)
        a = noise(8, 4, 9182)

        def f(x, y):
            if (x, y) in sp:
                return "#fffbd0"
            ring = (x // 4 + y // 4) % 3
            return pick(["#8a5a10", "#b07a1a", "#d8a428", "#f0c840", "#ffe070"], 0.2 + a(x, y) * 0.5 + ring * 0.12)

        return paint(f)

    def iron(pal, seed):
        a = noise(8, 4, seed)
        rivets = {(x, y) for x in range(4, 64, 8) for y in (4, 27)}

        def f(x, y):
            if (x, y) in rivets:
                return pal[-1]
            return pick(pal, 0.2 + a(x, y) * 0.6)

        return paint(f)

    T, R, I, P = "coral_cove", "shipwreck_bay", "volcano_isle", "splash_lagoon"
    SAND = ["#e8cf96", "#f0dca8", "#f6e6ba", "#faefcc", "#fff6de"]
    PL = ["#6e7a7e", "#808c8e", "#94a09e", "#a8b2ac", "#c0c8bc"]
    out = [
        # Coral Cove
        ("cove_sand", "Cove Sand", T, "sand", lambda: sand(SAND, 7001), 6, None),
        ("cove_road", "Cove Track", T, "road", lambda: road(["#b88c5a", "#c69c68", "#d2aa76", "#dcb884", "#e6c694"], "#efdcb0", 7011), 4, None),
        ("cove_wet_sand", "Cove Wet Sand", T, "sand", lambda: sand(["#b8985c", "#c6a66c", "#d2b47c", "#dcc28e"], 7021, 4, 2, 6, False), 5, None),
        ("cove_sea", "Cove Sea", T, "water", lambda: water(["#0688b4", "#0ea2c8", "#1ebcd6", "#46d4de", "#90ecea"], 7031),
         10, {"scrollU": 0.02, "scrollV": 0.03, "wave": 0.05, "wavePeriod": 4, "opacity": 0.86}),
        ("cove_shallows", "Cove Shallows", T, "water", lambda: shallows(["#3ccad6", "#56d6dc", "#72e2e2", "#94eee8"], "#d8e8c8", 7041),
         8, {"scrollU": 0.006, "scrollV": 0.01, "wave": 0.04, "wavePeriod": 6, "opacity": 0.82, "lagoon": 0.9}),
        ("cove_reef", "Reef Surf", T, "water", lambda: water(["#7ae0e0", "#b0f0ea", "#e0fbf6", "#ffffff"], 7051, 20, 3),
         5, {"scrollU": 0.0, "scrollV": 0.1, "wave": 0.1, "wavePeriod": 3.4, "opacity": 0.75, "glow": 0.15}),
        ("cove_planks", "Bleached Boardwalk", T, "road", lambda: planks(PL, "#3a4446", 7061), 3, None),
        ("cove_rail", "Rope Rail", T, "wall", lambda: rope_rail(["#5a4630", "#6e563a", "#846a48"], "#e8d6a6", "#a88e62", "#9aa6a2", 7071), 2, None),
        ("cove_post", "Piling", T, "wall", lambda: bark_post(["#4a3a2a", "#5c4a36", "#705c44", "#846e52"], ["#2e5a3a", "#3a6e44", "#4a8050"], 7081), 2, None),
        ("cove_rock", "Cove Rock", T, "wall", lambda: rock(["#6a5a4c", "#7c6c5c", "#8e7e6c", "#a2927e", "#b6a690"], 7091, "#e8e0d0"), 8, None),
        ("cove_grass", "Dune Grass", T, "grass", lambda: sand(["#7aa850", "#8cb85a", "#a0c66a", "#c8d890", "#e8dca8"], 7101, 2, 0, 20), 5, None),
        ("cove_hut_teal", "Hut Boards Teal", T, "wall", lambda: boards(["#2a9a9a", "#34aaa8", "#40b8b4", "#58c8c0"], "#1a5a5a", 7111), 3, None),
        ("cove_hut_coral", "Hut Boards Coral", T, "wall", lambda: boards(["#e06a5a", "#e87c66", "#f08e74", "#f6a286"], "#8a3a30", 7121), 3, None),
        ("cove_hut_sun", "Hut Boards Sun", T, "wall", lambda: boards(["#e8b030", "#eebe42", "#f4cc58", "#f8d872"], "#8a6a1a", 7131), 3, None),
        ("cove_white", "White Boards", T, "wall", lambda: boards(["#d8dcd8", "#e4e8e2", "#eef0ea", "#f8f8f2"], "#9aa4a2", 7141), 3, None),
        ("cove_thatch", "Palm Thatch", T, "wall", lambda: thatch(["#7a5a2a", "#9a7636", "#b48e44", "#c8a254", "#dab668"], 7151), 2, None),
        ("cove_awning_teal", "Awning Teal", T, "wall", lambda: stripes("#2ab0b0", "#f6f6ee", 7161, edge="#2ab0b0"), 2, SWAY),
        ("cove_awning_coral", "Awning Coral", T, "wall", lambda: stripes("#f06a5a", "#f6f6ee", 7171, edge="#f06a5a"), 2, SWAY),
        ("cove_awning_sun", "Awning Sun", T, "wall", lambda: stripes("#f4b832", "#f6f6ee", 7181, edge="#f4b832"), 2, SWAY),
        ("cove_lighthouse", "Lighthouse Bands", T, "wall", lambda: bands("#d83a34", "#f4f2ea"), 6, None),
        ("cove_lamp", "Lighthouse Lamp", T, "wall", lambda: lamp(["#e8b040", "#f8d060", "#fff090", "#fffbe0"]), 2, GLOW(1.0, 0.25, 3.0)),
        ("cove_coral_pink", "Pink Coral", T, "wall", lambda: coral(["#c84a7a", "#e05e8e", "#f07aa4", "#f898bc"], "#ffe0ec", 7191), 1.5, None),
        ("cove_coral_orange", "Orange Coral", T, "wall", lambda: coral(["#d8602a", "#e8783a", "#f4924e", "#fcae6a"], "#fff0d0", 7201), 1.5, None),
        ("cove_coral_violet", "Violet Coral", T, "wall", lambda: coral(["#6a3aa8", "#7c4cbc", "#9262d0", "#ac80e0"], "#e8d8ff", 7211), 1.5, GLOW(0.2)),
        ("cove_flag", "Cove Flag", T, "wall", lambda: flag_cove("#1aa4b4", "#f4f0e4", "#f88a6a"), 3, SWAY),
        ("cove_sign", "Cove Sign", T, "wall", lambda: sign_board(["#9a7244", "#ac8250", "#bc925e"], "#5a3e22", "#f4f0e4"), 2, None),
        ("cove_metal", "Lantern Metal", T, "wall", lambda: solid(["#2a3a3a", "#344646", "#3e5252", "#4a5e5e"], 7221), 1, None),
        # Shipwreck Bay
        ("wreck_sand", "Amber Sand", R, "sand", lambda: sand(["#d8aa6e", "#e2b87c", "#eac48a", "#f0d09a", "#f6dcac"], 8001, 6, 3, 14), 6, None),
        ("wreck_road", "Cove Trail", R, "road", lambda: road(["#9a6a40", "#a87a4a", "#b68856", "#c29662", "#cea470"], "#dcb47e", 8011), 4, None),
        ("wreck_wet_sand", "Bay Wet Sand", R, "sand", lambda: sand(["#9a7a4c", "#a88858", "#b49664", "#c0a472"], 8021, 3, 1, 6, False), 5, None),
        ("wreck_sea", "Golden Bay", R, "water", lambda: water(["#1a6a88", "#227c96", "#3a90a0", "#70a8a0", "#e8c890"], 8031, 16),
         10, {"scrollU": 0.02, "scrollV": 0.03, "wave": 0.05, "wavePeriod": 4.4, "opacity": 0.88}),
        ("wreck_planks", "Old Ship Planks", R, "road", lambda: planks(["#3e2a1a", "#4c3420", "#5a3e28", "#6a4a30", "#7e5a3a"], "#1a0e06", 8041), 3, None),
        ("wreck_hull", "Galleon Hull", R, "wall", lambda: planks(["#2e1e14", "#3a281a", "#463020", "#523a28", "#604430"], "#140a04", 8051, "#7a6a4a"), 3, None),
        ("wreck_trim", "Hull Trim", R, "wall", lambda: solid(["#8a6a1e", "#a07a24", "#b88c2e", "#d0a23a"], 8061), 1, None),
        ("wreck_rail", "Ship's Rail", R, "wall", lambda: rope_rail(["#3a2616", "#4a321e", "#5a3e26"], "#c8a874", "#8a6a44", "#3a2616", 8071), 2, None),
        ("wreck_post", "Old Piling", R, "wall", lambda: bark_post(["#3a2a1c", "#4a3826", "#5a4630", "#6a543a"], ["#2a4a2e", "#36583a", "#446846"], 8081), 2, None),
        ("wreck_rock", "Bay Rock", R, "wall", lambda: rock(["#4a3e3e", "#5a4c4a", "#6c5c58", "#806e66", "#968276"], 8091, "#c8c0b0"), 8, None),
        ("wreck_skull", "Skull Stone", R, "wall", lambda: rock(["#8a8070", "#9c927e", "#b0a68e", "#c4ba9e", "#d6ceb0"], 8101), 6, None),
        ("wreck_sail", "Patched Sail", R, "wall", lambda: sailcloth(["#a89070", "#c4ae8a", "#d6c29e", "#e6d4b2", "#f0e2c4"], "#a87a5a", 8111), 4, SWAY),
        ("wreck_flag", "Pirate Flag", R, "wall", lambda: skull_flag("#1a1a22", "#ece4cc"), 3, SWAY),
        ("wreck_logs", "Stockade Logs", R, "wall", lambda: logs(["#4a321c", "#5c4024", "#6e4e2e", "#80603a", "#926e44"], "#c8a070", 8121), 3, None),
        ("wreck_thatch", "Old Thatch", R, "wall", lambda: thatch(["#5a4022", "#6e502c", "#846236", "#987442", "#aa864e"], 8131), 2, None),
        ("wreck_gold", "Treasure", R, "wall", treasure, 1.5, GLOW(0.35, 0.2, 2.6)),
        ("wreck_iron", "Ship Iron", R, "wall", lambda: iron(["#1e1e22", "#28282e", "#32323a", "#3e3e48", "#6a6a74"], 8141), 1, None),
        ("wreck_lantern", "Lantern Glow", R, "wall", lambda: lamp(["#c86a20", "#e88a30", "#ffb04a", "#ffe0a0"]), 1, GLOW(0.95, flicker=0.12)),
        ("wreck_grass", "Bay Grass", R, "grass", lambda: sand(["#5a7a3a", "#6a8a42", "#7e9a4c", "#a8a868", "#c8b07a"], 8151, 2, 0, 20), 5, None),
        ("wreck_moss", "Weed", R, "wall", lambda: solid(["#2a4a2a", "#345a30", "#3e6a36", "#4a7a3e"], 8161, (8, 4)), 2, SWAY),
        # Volcano Isle
        ("isle_sand", "Black Sand", I, "sand", lambda: sand(["#2a2a2e", "#36363a", "#424246", "#505052", "#62605c"], 9001, 6, 0, 12), 6, None),
        ("isle_road", "Island Track", I, "road", lambda: road(["#6a4a36", "#7a5840", "#88644a", "#967256", "#a48262"], "#c0a07a", 9011), 4, None),
        ("isle_wet_sand", "Wet Black Sand", I, "sand", lambda: sand(["#18181c", "#202024", "#2a2a2e", "#36363a"], 9021, 4, 0, 6, False), 5, None),
        ("isle_sea", "Island Sea", I, "water", lambda: water(["#0a5a9a", "#0e6eae", "#1a86c0", "#38a6d0", "#78cce0"], 9031),
         10, {"scrollU": 0.02, "scrollV": 0.03, "wave": 0.05, "wavePeriod": 4.2, "opacity": 0.86}),
        ("isle_lagoon", "Island Lagoon", I, "water", lambda: shallows(["#18b8c8", "#2ac6d2", "#46d4da", "#6ae2e2"], "#5a5a56", 9041),
         8, {"scrollU": 0.006, "scrollV": 0.01, "wave": 0.04, "wavePeriod": 6, "opacity": 0.82, "lagoon": 0.9}),
        ("isle_spring", "Hot Spring", I, "water", lambda: shallows(["#7ad8d0", "#8ee2d8", "#a6ece2", "#c4f4ec"], "#e8e0c8", 9051),
         5, {"scrollU": 0.004, "scrollV": 0.008, "wave": 0.03, "wavePeriod": 3, "opacity": 0.9, "glow": 0.15}),
        ("isle_rock", "Basalt", I, "wall", lambda: rock(["#26262a", "#323236", "#3e3e40", "#4c4a4a", "#5c5856"], 9061, "#4a7a42"), 8, None),
        ("isle_tube", "Lava Tube Rock", I, "wall", lambda: rock(["#1a1416", "#24191a", "#2e2020", "#3a2824", "#4a3028"], 9071, "#c8602a"), 6, None),
        ("isle_jungle", "Jungle Floor", I, "grass", lambda: sand(["#2a5a26", "#346a2c", "#3e7a32", "#4a8a3a", "#5a9a44"], 9081, 0, 4, 10), 5, None),
        ("isle_moss", "Moss", I, "grass", lambda: sand(["#3a6a2a", "#4a7a32", "#5a8a3c", "#6e9a48"], 9091, 0, 0, 6, False), 4, None),
        ("isle_huts", "Stilt Hut Boards", I, "wall", lambda: boards(["#8a6040", "#9a6e4a", "#aa7e56", "#ba8e62"], "#4a3020", 9101), 3, None),
        ("isle_thatch", "Island Thatch", I, "wall", lambda: thatch(["#6a5426", "#8a6e32", "#a4863e", "#bc9c4c", "#d0b05c"], 9111), 2, None),
        ("isle_rail", "Island Rope Rail", I, "wall", lambda: rope_rail(["#4a3626", "#5a442e", "#6c5438"], "#d8c49a", "#9a8460", "#3a3a3a", 9121), 2, None),
        ("isle_net", "Fishing Net", I, "wall", lambda: stripes("#c8b88a", "#6a5a3a", 9131, w=4), 2, SWAY),
        # Splash Lagoon
        ("splash_path", "Park Paving", P, "road", lambda: road(["#d8a890", "#e2b6a0", "#eac2ac", "#f0ceb8", "#f6dac6"], "#fff0e0", 9501), 4, None),
        ("splash_sand", "Park Sand", P, "sand", lambda: sand(["#f0d8a0", "#f6e2b2", "#faeac2", "#fdf2d4", "#fff8e6"], 9511, 10, 6, 6), 6, None),
        ("splash_wet_sand", "Park Wet Sand", P, "sand", lambda: sand(["#c8aa72", "#d4b882", "#dec490", "#e8d2a2"], 9521, 4, 2, 4, False), 5, None),
        ("splash_sea", "Summer Sea", P, "water", lambda: water(["#0a90d0", "#14a6dc", "#28bce4", "#52d2ea", "#98e8f2"], 9531),
         10, {"scrollU": 0.02, "scrollV": 0.03, "wave": 0.05, "wavePeriod": 4, "opacity": 0.86}),
        ("splash_pool", "Pool Water", P, "water", lambda: shallows(["#22c0e8", "#38ccec", "#54d8f0", "#76e4f4"], "#e8f8ff", 9541),
         6, {"scrollU": 0.008, "scrollV": 0.012, "wave": 0.03, "wavePeriod": 3.4, "opacity": 0.85, "lagoon": 0.9}),
        ("splash_tile", "Pool Tile", P, "wall", lambda: stripes("#e8f6fa", "#3ab4d8", 9551, w=4), 2, None),
        ("splash_deck", "Park Decking", P, "road", lambda: planks(["#c08a5a", "#cc9866", "#d8a672", "#e2b480", "#ecc290"], "#7a5030", 9561), 3, None),
        ("splash_slide_red", "Slide Red", P, "wall", lambda: solid(["#e8402e", "#f04e36", "#f6623e", "#fa764a"], 9571), 2, None),
        ("splash_slide_blue", "Slide Blue", P, "wall", lambda: solid(["#2a6ae8", "#3478f0", "#4488f6", "#5a9cfa"], 9581), 2, None),
        ("splash_slide_yellow", "Slide Yellow", P, "wall", lambda: solid(["#f4b820", "#f8c430", "#fcd040", "#ffdc5a"], 9591), 2, None),
        ("splash_slide_green", "Slide Green", P, "wall", lambda: solid(["#34b858", "#40c464", "#4ed070", "#62dc80"], 9601), 2, None),
        ("splash_cabana", "Cabana Stripes", P, "wall", lambda: stripes("#f06a8a", "#fff6ee", 9611, edge="#f06a8a"), 2, SWAY),
        ("splash_grass", "Park Lawn", P, "grass", lambda: sand(["#4aa840", "#56b448", "#62c050", "#72cc5c", "#86d46c"], 9621, 0, 0, 8), 5, None),
        ("splash_rock", "Park Rock", P, "wall", lambda: rock(["#8a7a6a", "#9a8a78", "#ac9c88", "#beae98", "#d0c0a8"], 9631, "#e8e0d0"), 8, None),
        ("isle_ember", "Old Lava Glow", I, "wall", lambda: coral(["#8a2a10", "#b8401a", "#e06424", "#ff9a3a"], "#ffe0a0", 9141), 1.5, GLOW(0.5, 0.3, 4.0)),
    ]
    return out
