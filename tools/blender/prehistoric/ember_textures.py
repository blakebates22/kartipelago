# Emberdeep Hold's textures and theme (Dragon Kingdom, course 3: the Snow Dragon Pass v3
# lap, painted from Blake's Emberdeep Hold board), painted by make_textures.py. Every
# pixel is generated here: original artwork, 64x32 (64x64 for the banner). A fortress
# built into a dark mountain on a stormy night: weathered warm sandstone over black rock,
# red banners with a gold dragon, torchlit halls and a dragon's gold. (The castle kit,
# windows, iron, barrels, falls and flames are Dragonspire Keep's: keep_textures.py.)
# SPDX-License-Identifier: MIT

import math

THEME = {
    "id": "emberdeep_hold",
    "name": "Emberdeep Hold",
    "description": "A dragon-ruled fortress built into a dark mountain on a stormy night: weathered sandstone towers and battlements over black rock, red dragon banners, torchlit halls of pillars, waterfalls down the chasms, lightning over the peaks, and a red dragon on its hoard of gold",
    "environment": {
        "sky": "#232338",
        "fog": {"enabled": True, "color": "#2c2a3e", "near": 300, "far": 1900},
        "sun": {"color": "#b4c0ff", "intensity": 1.5, "direction": [0.45, 0.7, -0.55]},
        "ambient": {"sky": "#7a7aa8", "ground": "#4a3426", "intensity": 1.15},
        "skyDome": {
            "top": "#0e1020",
            "horizon": "#3c3654",
            "bottom": "#2a2636",
            "sun": {"color": "#e8ecff", "size": 6, "glow": "#5a6090", "elevation": 34, "face": "moon"},
            "clouds": {"count": 46, "color": "#3e3e5a", "shade": "#1a1a2a", "seed": 521, "low": 2, "high": 40, "drift": 0.012},
            "hills": {"color": "#1a1824", "far": "#3a3650", "height": 16, "seed": 523, "layers": 3},
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

    def ashlar(pal, mortar, seed, h=8, w=16, worn=0.0):
        a, b = noise(8, 4, seed), noise(32, 16, seed + 1)
        r = mt.rng(seed + 2)
        shade = [r() for _ in range(64)]
        chips = speckle(seed + 3, int(60 * worn))

        def f(x, y):
            row = y // h
            off = (row % 2) * (w // 2)
            col = (x + off) // w
            if y % h == 0 or (x + off) % w == 0:
                return mortar
            if (x, y) in chips:
                return mortar
            v = shade[(row * 7 + col) % 64] * 0.5 + a(x, y) * 0.3 + b(x, y) * 0.2
            if (x + off) % w == 1 or y % h == 1:
                v += 0.22
            return pick(pal, min(0.999, v))

        return paint(f)

    def flagstones(pal, joint, seed, rows=8, run=20):
        a, b = noise(4, 2, seed), noise(16, 8, seed + 1)
        sp = speckle(seed + 2, 50)

        def f(x, y):
            row = y // rows
            off = (row * 7) % run
            if y % rows == 0 or (x + off) % run == 0:
                return joint
            if (x, y) in sp:
                return joint
            return pick(pal, 0.1 + a(x, y) * 0.55 + b(x, y) * 0.35)

        return paint(f)

    def rock(pal, seed):
        a, b = noise(4, 2, seed), noise(16, 8, seed + 1)

        def f(x, y):
            if (y + int(a(x, 0) * 7)) % 9 == 0:
                return pal[0]
            if (x * 5 + y * 3) % 37 == 0:
                return pal[0]
            return pick(pal, a(x, y) * 0.5 + b(x, y) * 0.5)

        return paint(f)

    def rubble():
        a, b = noise(8, 4, 9101), noise(32, 16, 9102)
        sp = speckle(9103, 140)

        def f(x, y):
            if (x, y) in sp:
                return "#8a7a68" if (x + y) % 3 else "#1a1618"
            return pick(["#2a2428", "#342e30", "#3e3636", "#4a4040", "#564a46"], a(x, y) * 0.6 + b(x, y) * 0.4)

        return paint(f)

    def moss():
        a, b = noise(8, 4, 9111), noise(32, 16, 9112)

        def f(x, y):
            return pick(["#1e2a1c", "#243422", "#2c3e28", "#34482e", "#3e5234"], a(x, y) * 0.6 + b(x, y) * 0.4)

        return paint(f)

    def pillar():
        a = noise(4, 8, 9121)

        def f(x, y):
            u = x % 8
            if u == 0:
                return "#5a4a38"
            if u == 1:
                return "#c8b490"
            return pick(["#9a8666", "#a69272", "#b29e7c", "#bcaa88"], a(x, y) * 0.7 + (u / 8) * 0.3)

        return paint(f)

    def gold_hoard():
        a = noise(8, 4, 9131)
        r = mt.rng(9132)
        coins = [(r() * 64, r() * 32, 1.5 + r() * 1.5) for _ in range(70)]

        def f(x, y):
            for cx, cy, cr in coins:
                dx = min(abs(x - cx), 64 - abs(x - cx))
                dy = min(abs(y - cy), 32 - abs(y - cy))
                d = math.hypot(dx, dy)
                if d < cr:
                    return "#fff4a0" if d < cr * 0.35 else "#f0c040"
                if d < cr + 0.7:
                    return "#8a5a10"
            return pick(["#a06c14", "#b8841c", "#d0a028", "#e2b838"], a(x, y))

        return paint(f)

    def banner(field, edge, glyph, w=64, h=64):
        """A tall war banner with a gold border, a fringe, and a rearing serpent-dragon
        climbing it, wings up (our own design, unlike Dragonspire's rampant one)."""
        from PIL import Image as _Im, ImageDraw as _Dr

        m = _Im.new("L", (w, h), 0)
        d = _Dr.Draw(m)
        # The body: an S climbing from the foot to the head.
        pts = []
        for i in range(30):
            t = i / 29
            pts.append((32 + 9 * math.sin(t * math.pi * 1.6 + 0.4), 46 - 36 * t))
        d.line(pts, fill=255, width=9)
        d.polygon([(30, 8), (40, 6), (44, 9), (40, 12), (32, 13)], fill=255)  # the head
        d.polygon([(32, 8), (28, 2), (34, 7)], fill=255)  # the horn
        d.polygon([(26, 20), (10, 10), (14, 16), (8, 18), (14, 22), (9, 26), (24, 27)], fill=255)  # a wing
        d.polygon([(38, 20), (54, 10), (50, 16), (56, 18), (50, 22), (55, 26), (40, 27)], fill=255)  # the other
        d.polygon([(25, 44), (18, 48), (24, 49), (22, 52), (28, 47)], fill=255)  # the tail's barb
        d.point([(41, 9)], fill=0)
        mask = m.load()

        def f(x, y):
            if y > 54:
                return edge if (x // 4) % 2 == 0 else field
            if x < 3 or x > 60 or y < 4 or 50 < y < 53:
                return edge
            return glyph if mask[x, y] > 0 else field

        return paint(f, w, h)

    def flag_red():
        def f(x, y):
            if y < 2 or y > 29:
                return "#e8b040"
            return "#b81c24" if (x // 4) % 2 == 0 else "#c42630"

        return paint(f)

    def water():
        a, b = noise(4, 2, 9141), noise(16, 8, 9142)

        def f(x, y):
            v = a(x, y) * 0.6 + b(x, y) * 0.4
            if (y + int(a(x, 0) * 4)) % 8 == 0 and v > 0.66:
                return "#8aa4c8"
            return pick(["#141c2c", "#1a2436", "#202c40", "#28364a", "#304056"], v)

        return paint(f)

    def ember_glow():
        a = noise(8, 4, 9151)

        def f(x, y):
            v = a(x, y)
            if v > 0.72:
                return pick(["#ff8a20", "#ffb040"], (v - 0.72) * 3.5)
            return pick(["#1a1214", "#241818", "#2e1c18"], v * 1.3)

        return paint(f)

    T = "emberdeep_hold"
    SAND = ["#7a6648", "#8a7454", "#9a8260", "#a8906c", "#b49c78", "#c0a884"]
    DARK = ["#3a3028", "#463a30", "#524436", "#5e4e3e", "#6a5846"]
    BASALT = ["#16141a", "#201c24", "#2a2630", "#34303a", "#403a46", "#4c4652"]
    return [
        ("ember_setts", "Worn Hold Paving", T, "road", lambda: flagstones(["#5e5246", "#6a5c4e", "#766858", "#827262", "#8e7e6c"], "#2e2620", 9001), 5, None),
        ("ember_flag", "Sandstone Flags", T, "road", lambda: flagstones(["#8a7658", "#968262", "#a28e6e", "#ae9a7a", "#baa686"], "#4a3c2c", 9011, rows=8, run=24), 5, None),
        ("ember_path", "Mountain Track", T, "road", lambda: rock(["#3a3230", "#4a403c", "#584c46", "#665850", "#74665c"], 9021), 6, None),
        ("ember_kerb", "Hold Kerb", T, "road", lambda: ashlar(["#8a7656", "#a08a68", "#b29e7a"], "#3a3024", 9031, h=16, w=16), 2, None),
        ("ember_rubble", "Rubble", T, "rubble", rubble, 6, None),
        ("ember_moss", "Mountain Moss", T, "grass", moss, 6, None),
        ("ember_rock", "Black Crag", T, "wall", lambda: rock(BASALT, 9041), 12, None),
        ("ember_ashlar", "Weathered Sandstone", T, "wall", lambda: ashlar(SAND, "#3e3226", 9051, worn=1.0), 3, None),
        ("ember_ashlar_dark", "Old Hold Stone", T, "wall", lambda: ashlar(DARK, "#1e1814", 9053, h=8, w=12, worn=0.6), 3, None),
        ("ember_parapet", "Sandstone Parapet", T, "wall", lambda: ashlar(["#9a8664", "#a8946e", "#b4a07a", "#c0ac86"], "#3e3226", 9061, h=16, w=32), 3, None),
        ("ember_pillar", "Fluted Pillar", T, "wall", pillar, 3, None),
        ("ember_gold", "Dragon's Gold", T, "wall", gold_hoard, 2, GLOW(0.35, 0.25, 3.0)),
        ("ember_banner", "Emberdeep Banner", T, "wall", lambda: banner("#a8141e", "#e0a830", "#f0c048"), 3, SWAY),
        ("ember_flag_red", "Red Pennant", T, "wall", flag_red, 3, {"scrollU": 0, "scrollV": 0, "sway": 0.12}),
        ("ember_water", "Chasm Water", T, "water", water, 12, {"scrollU": 0.0, "scrollV": 0.08, "wave": 0.04, "wavePeriod": 4, "opacity": 0.9, "glow": 0.1}),
        ("ember_glow", "Ember Cracks", T, "wall", ember_glow, 4, GLOW(0.8, 0.3, 3.5)),
    ]
