# Snow Dragon Pass's textures and theme, painted by make_textures.py (which passes in
# its painting helpers). Every pixel is generated here: original artwork, 64x32, each
# tiling seamlessly. Snow Dragon Pass also reuses Dragon Isles' architecture (lacquer,
# lattice, banners, gold) and the Frost and Summit tracks' ice and falls.
# SPDX-License-Identifier: MIT

THEME = {
    "id": "snow_dragon_pass",
    "name": "Snow Dragon Pass",
    "description": "The dragon kingdom's highest mountains in a blizzard: slate-grey peaks buried in snow, frozen turquoise waterfalls, blue ice caverns, snow-laden monasteries in whitewash and red, weathered red timber, imperial crimson banners and muted gold, warm orange lanterns in the villages and the citadel blazing gold high above",
    "environment": {
        "sky": "#9fb2c8",
        "fog": {"enabled": True, "color": "#c6d3e2", "near": 150, "far": 900},
        "sun": {"color": "#e4ecff", "intensity": 1.7, "direction": [0.42, 0.62, -0.66]},
        "ambient": {"sky": "#cdd9ee", "ground": "#5a6478", "intensity": 1.45},
        "skyDome": {
            "top": "#4f6688",
            "horizon": "#c9d6e6",
            "bottom": "#b4c2d4",
            "sun": {"color": "#f4f6ff", "size": 9, "glow": "#d4def0", "elevation": 22},
            "clouds": {"count": 46, "color": "#e4eaf2", "shade": "#8a9ab4", "seed": 517, "low": 3, "high": 34, "drift": 0.006},
            "hills": {"color": "#6a7896", "far": "#b4c2d6", "height": 19, "seed": 521, "layers": 3},
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

    def speck(seed, every):
        import random

        r = random.Random(seed)
        return {(r.randrange(64), r.randrange(32)) for _ in range(64 * 32 // every)}

    SNOW = ["#c4cfe0", "#d2dbe9", "#dfe6f1", "#ebf0f7", "#f7f9fd"]

    # ---------------------------------------------------------------- roads

    def sdp_road():
        # The mountain road: packed snow over dark slate setts, worn through in places,
        # two grey ruts along it (V along). Clearly darker than the snow beside it.
        snow = ["#8794aa", "#94a0b4", "#a1acbe", "#aeb8c8"]
        sett = ["#545c6e", "#60687a", "#6c7486"]
        a, b = noise(4, 2, 9001), noise(16, 8, 9002)

        def f(x, y):
            rut = x % 32 in (9, 10, 11, 21, 22, 23)
            worn = a(x, y) * 0.7 + b(x, y) * 0.45
            if worn < 0.5 or rut:
                joint = x % 16 == 0 or (y + (8 if (x // 16) % 2 else 0)) % 16 == 0
                return "#3f4656" if joint else pick(sett, b(x, y) + (0.2 if rut else 0))
            return pick(snow, 0.15 + worn * 0.6)

        return paint(f)

    def sdp_setts():
        # The empire's paving in the village and the citadel: dark granite setts in rows,
        # snow packed into the joints.
        a = noise(8, 4, 9011)

        def f(x, y):
            row = y // 8
            off = 6 if row % 2 else 0
            if y % 8 == 0 or (x + off) % 12 == 0:
                return "#d8e0ea"
            return pick(["#5c6476", "#677083", "#727b8f", "#7e889c"], a(x, y) * 0.6 + ((x + off) // 12 * 7 + row * 3) % 5 * 0.08)

        return paint(f)

    def sdp_snowbank():
        # Banked snow along the roads: bright, with blue hollows.
        a, b = noise(4, 2, 9021), noise(16, 8, 9022)
        sp = speck(9023, 12)

        def f(x, y):
            if (x, y) in sp:
                return "#ffffff"
            return pick(SNOW, 0.35 + a(x, y) * 0.45 + b(x, y) * 0.25)

        return paint(f)

    def sdp_snowfield():
        # Windswept snow: drifts in long ripples, blue in their lee.
        a, b = noise(4, 2, 9031), noise(16, 8, 9032)

        def f(x, y):
            ripple = (y + int(a(x, y) * 8) + x // 6) % 9
            v = 0.3 + b(x, y) * 0.4 - (0.25 if ripple < 2 else 0)
            return pick(SNOW, v)

        return paint(f)

    # ---------------------------------------------------------------- the mountains

    def sdp_slate():
        # Dark slate, cleaved in steep layers, frost in the cracks.
        pal = ["#3c4556", "#475162", "#535d6f", "#606a7c", "#6d7789"]
        a, b = noise(4, 2, 9041), noise(16, 4, 9042)

        def f(x, y):
            cleave = (x * 2 + y + int(a(x, y) * 7)) % 13
            if cleave == 0:
                return "#c4d0e0"
            if cleave == 1:
                return "#2c3442"
            return pick(pal, a(x, y) * 0.6 + b(x, y) * 0.4)

        return paint(f)

    def sdp_slate_snow():
        # Slate with snow lying on every ledge: white bands across grey.
        pal = ["#475162", "#535d6f", "#606a7c", "#6d7789"]
        a = noise(4, 2, 9051)

        def f(x, y):
            ledge = (y + int(a(x, y) * 6)) % 10
            if ledge < 3:
                return "#f2f5fa" if ledge else "#c8d2e0"
            return pick(pal, 0.2 + a(x, y) * 0.7)

        return paint(f)

    def sdp_scree():
        a, b = noise(8, 4, 9061), noise(16, 8, 9062)

        def f(x, y):
            v = a(x, y) * 0.5 + b(x, y) * 0.5
            if v > 0.62:
                return pick(SNOW, v)
            return pick(["#4a5466", "#5a6476", "#6b7587"], v * 1.4)

        return paint(f)

    # ---------------------------------------------------------------- building

    def sdp_roof():
        # Grey-blue tiles in rows, thick snow lying on them (V up the roof).
        a = noise(8, 4, 9071)

        def f(x, y):
            snow = (y % 8) < 4 + int(a(x, y) * 3)
            if snow:
                return pick(SNOW[1:], a(x, y))
            if (x + (y // 8) * 4) % 8 == 0:
                return "#2c3648"
            return pick(["#3d4a62", "#485670", "#53627c"], a(x, y))

        return paint(f)

    def sdp_whitewash():
        # Monastery whitewash with a band of dark red (the eaves' trim) along the top.
        a = noise(8, 4, 9081)

        def f(x, y):
            if y > 25:
                return "#7a1e1a" if y < 30 else "#4a1010"
            return pick(["#d8d4cc", "#e2ded6", "#ece8e0", "#f4f1ea"], a(x, y))

        return paint(f)

    def sdp_redwall():
        # The great red walls of the citadel and the monastery's upper halls.
        a = noise(8, 4, 9091)

        def f(x, y):
            if y % 16 == 0:
                return "#5a1612"
            return pick(["#8a2420", "#962a24", "#a2322a", "#ae3c30"], a(x, y))

        return paint(f)

    def sdp_flags():
        # Prayer flags on a line: small squares in five colours, faded, a pattern printed
        # on each (U along the line).
        cols = ["#2f6ec0", "#f2f0e8", "#c8322a", "#3a9a4a", "#e8c030"]

        def f(x, y):
            i = (x // 8) % 5
            if y < 2:
                return "#6a5a48"  # the cord
            if x % 8 == 7:
                return "#8a7a66"  # the gap between flags
            c = cols[i]
            if 10 < y < 22 and 2 < x % 8 < 6 and (x + y) % 3 == 0:
                return "#5a4a3a"
            return c

        return paint(f)

    def sdp_ice_channel():
        # A frozen channel: turquoise ice, white cracks, bubbles caught in it.
        a, b = noise(4, 2, 9101), noise(16, 8, 9102)
        sp = speck(9103, 18)

        def f(x, y):
            if (x, y) in sp:
                return "#ffffff"
            crack = (x + int(a(x, y) * 10)) % 21 == 0
            if crack:
                return "#e8fbff"
            return pick(["#3aa6b8", "#4cb8c8", "#62c8d4", "#7cd8e0"], a(x, y) * 0.6 + b(x, y) * 0.4)

        return paint(f)

    def sdp_aqueduct():
        # Old grey ashlar, frost on every course.
        a = noise(8, 4, 9111)

        def f(x, y):
            row = y // 8
            off = 8 if row % 2 else 0
            if y % 8 == 0:
                return "#e4ebf4"
            if (x + off) % 16 == 0:
                return "#4a5262"
            return pick(["#7a8292", "#868e9e", "#929aaa", "#9ea6b4"], a(x, y))

        return paint(f)

    def sdp_cavern():
        # Blue ice, lit from within.
        a, b = noise(4, 2, 9121), noise(16, 8, 9122)

        def f(x, y):
            v = a(x, y) * 0.6 + b(x, y) * 0.4
            vein = (x + int(a(x, y) * 12) + y // 2) % 17 == 0
            if vein:
                return "#e8fcff"
            return pick(["#1e5a9a", "#2a72b4", "#3a8ccc", "#56a8e0", "#84c8f0"], v)

        return paint(f)

    def sdp_icicle():
        a = noise(4, 2, 9131)

        def f(x, y):
            return pick(["#a8d4ec", "#c4e4f4", "#dcf0fa", "#f4fbff"], a(x, y) * 0.5 + y / 64)

        return paint(f)

    def sdp_awning():
        # A tattered, faded red awning, patched.
        a = noise(8, 4, 9141)

        def f(x, y):
            if (x * 3 + y * 7) % 41 < 2 and y > 20:
                return "#3a2a24"  # a tear
            if 20 < x < 30 and 8 < y < 16:
                return pick(["#8a7a5a", "#9a8a68"], a(x, y))  # a patch
            return pick(["#8a3a30", "#9a4436", "#a84e3e", "#b45a48"], a(x, y))

        return paint(f)

    def sdp_window():
        # The citadel's windows, blazing warm gold through lattice.
        def f(x, y):
            if x % 16 in (0, 1, 15) or y % 16 in (0, 1, 15):
                return "#6a1a12"
            if x % 4 == 0 or y % 4 == 0:
                return "#c87a22"
            return "#ffd27a" if (x // 4 + y // 4) % 2 else "#ffc25a"

        return paint(f)

    def sdp_burlap():
        # Grain sacks: coarse weave, a stencilled mark.
        a = noise(8, 4, 9151)

        def f(x, y):
            if (x % 3 == 0) != (y % 3 == 0):
                return "#8a7650"
            if 26 < x < 38 and 10 < y < 22 and (x + y) % 2:
                return "#7a2a20"
            return pick(["#a89268", "#b49e74", "#c0aa80"], a(x, y))

        return paint(f)

    def sdp_chevron():
        # A red-and-white turn board with a frosted frame, arrows pointing along +U.
        def f(x, y):
            if y < 2 or y > 29:
                return "#e8eef6"
            u = (x - abs(y - 15.5) * 0.8) % 16
            return "#f4f6fa" if u < 8 else "#d0281e"

        return paint(f)

    def sdp_gold_trim():
        # Muted gold ornament on the citadel's eaves and gates.
        a = noise(8, 4, 9161)

        def f(x, y):
            if (x + y) % 8 == 0 or (x - y) % 8 == 0:
                return "#8a6420"
            return pick(["#b48a34", "#c49a40", "#d4aa4c", "#e2bc5e"], a(x, y))

        return paint(f)

    T = "snow_dragon_pass"
    return [
        ("sdp_road", "Mountain Road", T, "snow_stone", sdp_road, 6, None),
        ("sdp_setts", "Snowy Setts", T, "snow_stone", sdp_setts, 5, None),
        ("sdp_snowbank", "Snowbank", T, "packed_snow", sdp_snowbank, 4, None),
        ("sdp_snowfield", "Windswept Snow", T, "deep_snow", sdp_snowfield, 8, None),
        ("sdp_slate", "Slate Cliff", T, "wall", sdp_slate, 14, None),
        ("sdp_slate_snow", "Snowy Slate", T, "wall", sdp_slate_snow, 12, None),
        ("sdp_scree", "Snowy Scree", T, "deep_snow", sdp_scree, 6, None),
        ("sdp_roof", "Snowy Tiles", T, "wall", sdp_roof, 3, None),
        ("sdp_whitewash", "Monastery Whitewash", T, "wall", sdp_whitewash, 4, None),
        ("sdp_redwall", "Citadel Red", T, "wall", sdp_redwall, 5, None),
        ("sdp_flags", "Prayer Flags", T, "wall", sdp_flags, 4, None),
        ("sdp_ice_channel", "Frozen Channel", T, "ice", sdp_ice_channel, 6, None),
        ("sdp_aqueduct", "Aqueduct Stone", T, "wall", sdp_aqueduct, 4, None),
        ("sdp_cavern", "Blue Ice Cavern", T, "wall", sdp_cavern, 8, GLOW(0.55, pulse=0.15, period=6.0)),
        ("sdp_icicle", "Icicle", T, "wall", sdp_icicle, 2, None),
        ("sdp_awning", "Tattered Awning", T, "wall", sdp_awning, 3, None),
        ("sdp_window", "Citadel Windows", T, "wall", sdp_window, 3, GLOW(0.9, flicker=0.08)),
        ("sdp_burlap", "Grain Sacks", T, "wall", sdp_burlap, 2, None),
        ("sdp_chevron", "Snow Chevrons", T, "wall", sdp_chevron, 4, None),
        ("sdp_gold_trim", "Imperial Gold", T, "wall", sdp_gold_trim, 2, None),
    ]
