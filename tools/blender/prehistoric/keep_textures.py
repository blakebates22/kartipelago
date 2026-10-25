# Dragonspire Keep's textures and theme (Dragon Kingdom, course 1), painted by
# make_textures.py (which passes in its painting helpers). Every pixel is generated here:
# original artwork, 64x32 (64x64 for the banners), each tiling seamlessly. A fantasy
# castle at sunset: grey-violet stone, slate roofs, crimson dragon banners, torchlight.
# SPDX-License-Identifier: MIT

import math

THEME = {
    "id": "dragonspire_keep",
    "name": "Dragonspire Keep",
    "description": "A dark-stone castle on its cliffs at sunset: grey-violet walls and slate spires, crimson dragon banners, torches and braziers, waterfalls into a mountain lake, a sea of cloud and snowy peaks beyond, and a red dragon on the highest tower",
    "environment": {
        "sky": "#7a4a8a",
        "fog": {"enabled": True, "color": "#c4849a", "near": 420, "far": 2600},
        "sun": {"color": "#ffc08a", "intensity": 2.5, "direction": [-0.62, 0.42, 0.66]},
        "ambient": {"sky": "#b49ad8", "ground": "#5a4048", "intensity": 1.2},
        "skyDome": {
            "top": "#2c2266",
            "horizon": "#ff9a5a",
            "bottom": "#e4889a",
            "sun": {"color": "#fff0c0", "size": 11, "glow": "#ffb070", "elevation": 9},
            "clouds": {"count": 30, "color": "#ffb48a", "shade": "#8a5a9a", "seed": 421, "low": 3, "high": 30, "drift": 0.004},
            "hills": {"color": "#5a4a7a", "far": "#b48ab4", "height": 13, "seed": 423, "layers": 3},
            "stars": {"count": 60, "color": "#fff4e0", "seed": 425, "low": 48},
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

    def flagstones(pal, joint, seed, rows=8, run=24):
        a, b = noise(4, 2, seed), noise(16, 8, seed + 1)
        sp = speckle(seed + 2, 40)

        def f(x, y):
            row = y // rows
            off = (row * 11) % run
            if y % rows == 0 or (x + off) % run == 0:
                return joint
            if (x, y) in sp:
                return pal[0]
            return pick(pal, 0.15 + a(x, y) * 0.55 + b(x, y) * 0.3)

        return paint(f)

    def cobbles(pal, joint, seed):
        a = noise(8, 4, seed)
        r = mt.rng(seed + 3)
        cells = [(r() * 64, r() * 32) for _ in range(46)]

        def f(x, y):
            d = []
            for cx, cy in cells:
                dx = min(abs(x - cx), 64 - abs(x - cx))
                dy = min(abs(y - cy), 32 - abs(y - cy))
                d.append(dx * dx + dy * dy)
            d.sort()
            if math.sqrt(d[1]) - math.sqrt(d[0]) < 1.1:
                return joint
            return pick(pal, a(x, y) * 0.7 + (d[0] % 7) / 7 * 0.3)

        return paint(f)

    def cliff_path():
        a, b = noise(8, 4, 8101), noise(32, 16, 8102)
        sp = speckle(8103, 70)

        def f(x, y):
            if (x, y) in sp:
                return "#4a3a48"
            return pick(["#6a5a66", "#7a6872", "#8a7680", "#9a868c", "#ab9698"], a(x, y) * 0.6 + b(x, y) * 0.4)

        return paint(f)

    def carpet():
        a = noise(4, 8, 8111)

        def f(x, y):
            if x < 4 or x > 59:
                return "#e8b040" if x in (1, 2, 61, 62) else "#5a1018"
            if x in (6, 57):
                return "#e8b040"
            return pick(["#9a1a24", "#a8202a", "#b42630", "#c02c36"], a(x, y))

        return paint(f)

    def kerb():
        a = noise(4, 2, 8121)

        def f(x, y):
            if x % 16 == 0:
                return "#3a3044"
            band = (x // 16) % 2
            return pick(["#8a8094", "#9a90a4", "#aaa0b2"] if band else ["#6a6078", "#786e86", "#867c92"], a(x, y))

        return paint(f)

    # ---------------------------------------------------------------- land

    def grass():
        a, b = noise(8, 4, 8201), noise(32, 16, 8202)
        sp = speckle(8203, 60)

        def f(x, y):
            if (x, y) in sp:
                return "#c4b85a"
            return pick(["#2e4a2a", "#36562e", "#406234", "#4c6e38", "#5a7a3e", "#6a8442"], a(x, y) * 0.6 + b(x, y) * 0.4)

        return paint(f)

    def rock(pal, seed, strata=True):
        a, b = noise(4, 2, seed), noise(16, 8, seed + 1)

        def f(x, y):
            v = a(x, y) * 0.55 + b(x, y) * 0.45
            if strata and (y + int(a(x, 0) * 6)) % 11 == 0:
                return pal[0]
            if strata and (x * 3 + y * 7) % 41 == 0:
                return pal[0]
            return pick(pal, v)

        return paint(f)

    def rock_moss():
        a, b = noise(4, 2, 8221), noise(16, 8, 8222)

        def f(x, y):
            v = a(x, y)
            if v > 0.6:
                return pick(["#36502e", "#40603a", "#4c6c40"], b(x, y))
            return pick(["#3c3448", "#4a4058", "#584c66", "#665a72"], b(x, y) * 0.5 + v * 0.5)

        return paint(f)

    def shore():
        a, b = noise(8, 4, 8231), noise(32, 16, 8232)
        sp = speckle(8233, 120)

        def f(x, y):
            if (x, y) in sp:
                return "#e0c8b8"
            return pick(["#7a6670", "#8a747a", "#9a8486", "#ab9494", "#bca4a0"], a(x, y) * 0.5 + b(x, y) * 0.5)

        return paint(f)

    def pine():
        a = noise(8, 8, 8241)

        def f(x, y):
            if (x + y * 2) % 7 == 0:
                return "#14281e"
            return pick(["#1a3424", "#22402a", "#2a4c30", "#345a36", "#40683c"], a(x, y) * 0.7 + (y % 8) / 8 * 0.3)

        return paint(f)

    # ---------------------------------------------------------------- the castle

    def ashlar(pal, mortar, seed, h=8, w=16):
        a, b = noise(8, 4, seed), noise(32, 16, seed + 1)
        r = mt.rng(seed + 2)
        shade = [r() for _ in range(64)]

        def f(x, y):
            row = y // h
            off = (row % 2) * (w // 2)
            col = (x + off) // w
            if y % h == 0 or (x + off) % w == 0:
                return mortar
            v = shade[(row * 7 + col) % 64] * 0.5 + a(x, y) * 0.3 + b(x, y) * 0.2
            if (x + off) % w == 1 or y % h == 1:
                v += 0.25  # the lit top-left edge of each block
            return pick(pal, min(0.999, v))

        return paint(f)

    def slate():
        a = noise(4, 8, 8311)

        def f(x, y):
            row = y // 4
            off = (row % 2) * 4
            if y % 4 == 3:
                return "#1a1830"
            if (x + off) % 8 == 0:
                return "#24223c"
            return pick(["#2e3058", "#363a66", "#404674", "#4c5282", "#5a6090"], a(x, y) * 0.6 + (y % 4) / 4 * 0.4)

        return paint(f)

    def roof_tiles():
        a = noise(4, 8, 8321)

        def f(x, y):
            row = y // 4
            off = (row % 2) * 3
            if y % 4 == 3:
                return "#4a1a1a"
            if (x + off) % 6 == 0:
                return "#5a2020"
            return pick(["#7a2a24", "#8a342a", "#9a4030", "#a84c36", "#b85a40"], a(x, y) * 0.5 + (y % 4) / 4 * 0.5)

        return paint(f)

    def timber():
        a = noise(8, 4, 8331)

        def f(x, y):
            u = x % 32
            if u < 3 or y < 2 or y > 29 or abs(u - 3 - (y * 27 // 32)) < 2:
                return pick(["#2a1a14", "#342018", "#3e281c"], a(x, y))
            return pick(["#d8c8a8", "#e2d4b4", "#ecdcc0", "#f2e6cc"], a(x, y))

        return paint(f)

    def door():
        a = noise(4, 16, 8341)

        def f(x, y):
            if y in (6, 7, 24, 25) and 4 < x < 60:
                return "#2a2a30"
            if x % 8 == 0:
                return "#2a1810"
            if (x % 8 == 4) and y in (6, 24):
                return "#8a8a90"
            return pick(["#4a2c1a", "#56341e", "#623c22", "#6e4426"], a(x, y))

        return paint(f)

    def window():
        a = noise(4, 4, 8351)

        def f(x, y):
            u, v = x % 16, y
            # A tall arched window in each 16 px column: stone round it, lit inside.
            cx = 7.5
            inside = 3 <= u <= 12 and 8 <= v <= 28 and (v >= 12 or math.hypot(u - cx, v - 12) < 4.6)
            if inside:
                if u in (7, 8) or v == 18:
                    return "#5a3020"
                return pick(["#ff9a30", "#ffb048", "#ffc860", "#ffd878"], a(x, y) * 0.6 + (v / 32) * 0.4)
            if (y // 8 + (x // 16)) % 2 == 0 and y % 8 == 0:
                return "#2a2438"
            return pick(["#4a4260", "#544c6a", "#5e5674"], a(x, y))

        return paint(f)

    def parapet():
        a, b = noise(8, 4, 8361), noise(32, 16, 8362)

        def f(x, y):
            if y < 3:
                return pick(["#a49ab4", "#b4aac2"], a(x, y))  # the coping
            if y == 3 or (x % 16 == 0 and y > 3):
                return "#2e283c"
            return pick(["#5a5270", "#665e7c", "#726a88", "#7e7694"], a(x, y) * 0.6 + b(x, y) * 0.4)

        return paint(f)

    def gold():
        a = noise(4, 4, 8371)

        def f(x, y):
            return pick(["#8a5a14", "#b07c1c", "#d4a02c", "#ecc248", "#fbe07a"], a(x, y) * 0.6 + ((x + y) % 8) / 8 * 0.4)

        return paint(f)

    def iron():
        a = noise(8, 4, 8381)

        def f(x, y):
            return pick(["#1e1c22", "#28262c", "#323036", "#3c3a42"], a(x, y))

        return paint(f)

    def barrel():
        a = noise(4, 16, 8391)

        def f(x, y):
            if y in (4, 5, 26, 27):
                return "#3a3a40"
            if x % 8 == 0:
                return "#3a2010"
            return pick(["#6a3e1e", "#7a4824", "#8a5228", "#9a5c2e"], a(x, y))

        return paint(f)

    def dock():
        a = noise(4, 16, 8411)
        sp = speckle(8412, 30)

        def f(x, y):
            if y % 8 == 0:
                return "#2a2228"
            if (x, y) in sp:
                return "#3a3036"
            k = (y // 8 + (x // 32) * 3) % 4
            pal = [["#5a4c4a", "#665650", "#726058"], ["#4e4446", "#5a4e4e", "#665856"], ["#625450", "#6e5e58", "#7a6a60"], ["#544848", "#605252", "#6c5e5a"]][k]
            return pick(pal, a(x, y))

        return paint(f)

    def crate():
        a = noise(8, 8, 8401)

        def f(x, y):
            u, v = x % 32, y
            if u < 3 or u > 28 or v < 3 or v > 28 or abs(u - v) < 2:
                return pick(["#4a2c14", "#5a3418"], a(x, y))
            return pick(["#8a5a2c", "#9a6634", "#aa723c"], a(x, y))

        return paint(f)

    # ---------------------------------------------------------------- banners

    def dragon_banner(field, edge, glyph, w=64, h=64):
        """A war banner: a field with a gold edge and a fringed foot, and on it a
        rampant winged dragon in gold (our own design: a body, a raised wing, a tail
        curling under, a horned head)."""

        from PIL import Image as _Im, ImageDraw as _Dr

        m = _Im.new("L", (w, h), 0)
        d = _Dr.Draw(m)
        d.ellipse((24, 20, 40, 42), fill=255)  # the body
        d.polygon([(31, 24), (36, 14), (40, 12), (42, 16), (38, 20), (37, 27)], fill=255)  # the neck
        d.polygon([(38, 9), (46, 9), (51, 12), (51, 14), (45, 15), (39, 16)], fill=255)  # the head
        d.polygon([(39, 10), (35, 3), (42, 9)], fill=255)  # the horn
        d.polygon([(28, 23), (13, 5), (17, 11), (10, 11), (16, 17), (8, 18), (15, 23), (8, 26), (25, 30)], fill=255)  # the wing
        d.polygon([(36, 25), (44, 20), (47, 21), (45, 24), (39, 29)], fill=255)  # a raised claw
        d.polygon([(37, 32), (44, 31), (46, 34), (43, 35), (37, 36)], fill=255)  # the other
        d.polygon([(27, 38), (24, 46), (31, 46), (33, 39)], fill=255)  # the hind leg
        d.line([(26, 40), (18, 45), (12, 43), (11, 37)], fill=255, width=3)  # the tail...
        d.polygon([(7, 36), (11, 31), (15, 36)], fill=255)  # ...and its barb
        d.point([(47, 11)], fill=0)  # the eye
        mask = m.load()

        def dragon(x, y):
            return mask[x, y] > 0

        def f(x, y):
            # The foot: a gold fringe.
            if y > 54:
                return edge if (x // 4) % 2 == 0 else field
            if x < 3 or x > 60 or y < 4:
                return edge
            if y > 48 and y < 51:
                return edge
            if dragon(x, y):
                return glyph
            return field

        return paint(f, w, h)

    def flag_blue():
        def f(x, y):
            if (x // 8 + y // 8) % 2 == 0 and 20 < x < 44 and 8 < y < 24:
                return "#f0c040"
            if y < 2 or y > 29:
                return "#f0c040"
            return "#24408a" if (x // 4) % 2 == 0 else "#2a4898"

        return paint(f)

    # ---------------------------------------------------------------- the dragon

    def dragon_red():
        a = noise(8, 4, 8501)

        def f(x, y):
            row = y // 4
            off = (row % 2) * 4
            u = (x + off) % 8
            v = y % 4
            if v == 3 or (u == 0 and v > 0):
                return "#4a0c10"
            return pick(["#8a1a1c", "#a42422", "#be3428", "#d44a30"], a(x, y) * 0.4 + (1 - v / 4) * 0.6)

        return paint(f)

    def dragon_wing():
        a = noise(8, 4, 8511)

        def f(x, y):
            if x % 16 == 0:
                return "#3a0a0e"
            return pick(["#7a1a2a", "#8c2430", "#a03238", "#b44440"], a(x, y) * 0.5 + (y / 32) * 0.5)

        return paint(f)

    def dragon_belly():
        a = noise(4, 4, 8521)

        def f(x, y):
            if y % 6 == 0:
                return "#8a5a20"
            return pick(["#d8a040", "#e4b050", "#f0c060"], a(x, y))

        return paint(f)

    # ---------------------------------------------------------------- water and air

    def lake():
        a, b = noise(4, 2, 8601), noise(16, 8, 8602)

        def f(x, y):
            v = a(x, y) * 0.6 + b(x, y) * 0.4
            if (y + int(a(x, 0) * 4)) % 8 == 0 and v > 0.62:
                return "#c87a7a"  # sunset glints
            return pick(["#1c1e44", "#24284e", "#2c3058", "#343a64", "#3e4470"], v)

        return paint(f)

    def falls():
        a, b = noise(8, 2, 8611), noise(32, 4, 8612)

        def f(x, y):
            return pick(["#b4b0d8", "#c8c4e4", "#dcd8f0", "#eeeaf8", "#ffffff"], a(x, y) * 0.5 + b(x, y) * 0.5)

        return paint(f)

    def cloud():
        a, b = noise(4, 2, 8621), noise(8, 4, 8622)

        def f(x, y):
            return pick(["#b886b0", "#cc94b4", "#e0a4b4", "#f0b8b0", "#ffd0b0"], a(x, y) * 0.6 + b(x, y) * 0.4)

        return paint(f)

    def mist():
        a, b = noise(4, 2, 8631), noise(8, 4, 8632)

        def f(x, y):
            return pick(["#d8c8e8", "#e4d8f0", "#f0e8f8", "#ffffff"], a(x, y) * 0.6 + b(x, y) * 0.4)

        return paint(f)

    def flame():
        a = noise(8, 4, 8641)

        def f(x, y):
            v = y / 32 + a(x, y) * 0.3
            return pick(["#fff4b0", "#ffd860", "#ffaa30", "#ff7a20", "#e04a18"], min(0.999, v))

        return paint(f)

    T = "dragonspire_keep"
    STONE = ["#4a4260", "#544c6a", "#5e5674", "#68607e", "#746c8a", "#827a96"]
    DARK = ["#2e283c", "#363046", "#3e3850", "#48405a", "#524a64"]
    ROCK = ["#3e3648", "#4e4658", "#5c5468", "#6a6276", "#7a7086", "#8a8094"]
    return [
        ("keep_flag", "Keep Flagstones", T, "road", lambda: flagstones(["#5a5466", "#666072", "#726c7e", "#7e788a", "#8a8496"], "#3a3446", 8001), 5, None),
        ("keep_cobble", "Castle Town Cobbles", T, "road", lambda: cobbles(["#5e5462", "#6a606e", "#766c7a", "#847a86", "#928894"], "#3a3240", 8011), 4, None),
        ("keep_path", "Cliff Path", T, "road", cliff_path, 6, None),
        ("keep_carpet", "Royal Carpet", T, "road", carpet, 8, None),
        ("keep_kerb", "Keep Kerb", T, "road", kerb, 2, None),
        ("keep_grass", "Sunset Grass", T, "grass", grass, 6, None),
        ("keep_rock", "Keep Crag", T, "wall", lambda: rock(ROCK, 8211), 12, None),
        ("keep_rock_moss", "Mossy Crag", T, "wall", rock_moss, 9, None),
        ("keep_shore", "Lake Shingle", T, "sand", shore, 6, None),
        ("keep_pine", "Mountain Pine", T, "grass", pine, 2, None),
        ("keep_ashlar", "Keep Ashlar", T, "wall", lambda: ashlar(STONE, "#2a2438", 8301), 3, None),
        ("keep_ashlar_dark", "Old Keep Ashlar", T, "wall", lambda: ashlar(DARK, "#1c1828", 8303, h=8, w=12), 3, None),
        ("keep_slate", "Spire Slate", T, "wall", slate, 3, None),
        ("keep_roof", "Town Roof Tiles", T, "wall", roof_tiles, 3, None),
        ("keep_timber", "Half-Timbering", T, "wall", timber, 4, None),
        ("keep_door", "Oak Door", T, "wall", door, 3, None),
        ("keep_window", "Lit Arched Windows", T, "wall", window, 4, GLOW(0.85, flicker=0.12)),
        ("keep_parapet", "Parapet Stone", T, "wall", parapet, 3, None),
        ("keep_gold", "Gilded Trim", T, "wall", gold, 1, GLOW(0.2)),
        ("keep_iron", "Black Iron", T, "wall", iron, 2, None),
        ("keep_barrel", "Barrel Staves", T, "wall", barrel, 2, None),
        ("keep_dock", "Weathered Dock Boards", T, "road", dock, 4, None),
        ("keep_crate", "Crate", T, "wall", crate, 2, None),
        ("keep_banner", "Dragon Banner", T, "wall", lambda: dragon_banner("#a8182a", "#e8b040", "#f4cc58"), 3, SWAY),
        ("keep_banner_dark", "Black Dragon Banner", T, "wall", lambda: dragon_banner("#2a1a2a", "#c03030", "#e04838"), 3, SWAY),
        ("keep_flag_blue", "Blue Pennant", T, "wall", flag_blue, 3, {"scrollU": 0, "scrollV": 0, "sway": 0.1}),
        ("dragon_red", "Red Dragon Scales", T, "wall", dragon_red, 1.5, None),
        ("dragon_wing", "Red Dragon Wing", T, "wall", dragon_wing, 4, None),
        ("dragon_belly", "Dragon Belly", T, "wall", dragon_belly, 1.5, None),
        ("keep_lake", "Sunset Lake", T, "deep_water", lake, 14, {"scrollU": 0.006, "scrollV": 0.01, "wave": 0.04, "wavePeriod": 6, "opacity": 0.92, "glow": 0.1}),
        ("keep_lake_shallow", "Sunset Shallows", T, "water", lake, 14, {"scrollU": 0.006, "scrollV": 0.01, "wave": 0.04, "wavePeriod": 6, "opacity": 0.88, "glow": 0.1}),
        ("keep_falls", "Keep Falls", T, "water", falls, 6, {"scrollU": 0.0, "scrollV": 1.2, "wave": 0.03, "wavePeriod": 1.3, "opacity": 0.9, "glow": 0.35}),
        ("keep_cloud", "Sunset Cloud Sea", T, "water", cloud, 34, {"scrollU": 0.004, "scrollV": 0.0015, "wave": 0.05, "wavePeriod": 11, "opacity": 0.85, "glow": 0.5}),
        ("keep_mist", "Falls Mist", T, "water", mist, 18, {"scrollU": 0.01, "scrollV": -0.03, "wave": 0.08, "wavePeriod": 5, "opacity": 0.38, "glow": 0.4}),
        ("keep_flame", "Torch Flame", T, "wall", flame, 1, {"scrollU": 0.15, "scrollV": -1.4, "wave": 0.1, "wavePeriod": 0.5, "glow": 1.0}),
    ]
