# Impact Depths' textures and theme, painted by make_textures.py (which passes in its
# painting helpers). Every pixel is generated here: original artwork, 64x32 like the
# rest of the library, each tiling seamlessly.
# SPDX-License-Identifier: MIT

import math

THEME = {
    "id": "impact_depths",
    "name": "Impact Depths",
    "description": "A blazing desert noon over a smoking asteroid crater, and under it a descending world: warm ochre caverns of cyan and violet crystal, a sunlit prehistoric jungle round a turquoise lake, black volcanic depths of lava, a dragon's crimson lair and a glowing gold-and-magenta core",
    "environment": {
        "sky": "#4a8ee0",
        "fog": {"enabled": True, "color": "#e0c49c", "near": 420, "far": 2400},
        "sun": {"color": "#fff0d0", "intensity": 2.8, "direction": [-0.34, 0.86, -0.38]},
        "ambient": {"sky": "#b0ccf0", "ground": "#9a6a42", "intensity": 1.2},
        "skyDome": {
            "top": "#1a5cc8",
            "horizon": "#e8d8c0",
            "bottom": "#e2c09a",
            "sun": {"color": "#fffbe8", "size": 8, "glow": "#ffe2a0", "elevation": 58},
            "clouds": {"count": 14, "color": "#ffffff", "shade": "#ecd6c0", "seed": 211, "low": 10, "high": 34, "drift": 0.003},
            "hills": {"color": "#b8784e", "far": "#d8b896", "height": 5, "seed": 213, "layers": 3, "style": "mesas"},
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

    # ---------------------------------------------------------------- the crater

    def crater_ground():
        # Scorched, ash-dusted impact ground: charcoal and burnt umber, pale ash flecks.
        pal = ["#2e2422", "#3a2e2a", "#463630", "#54423a", "#644e42"]
        a, b = noise(4, 2, 6001), noise(16, 8, 6002)
        ash = speckle(6003, 46)

        def f(x, y):
            if (x, y) in ash:
                return "#9a8a80"
            return pick(pal, a(x, y) * 0.55 + b(x, y) * 0.45)

        return paint(f)

    def crater_rock():
        # The crater's fractured wall: shocked dark rock in slumped layers, cracks.
        a, b = noise(8, 2, 6011), noise(16, 4, 6012)

        def f(x, y):
            band = (y + int(a(x, y) * 6)) % 11
            if band == 0:
                return "#1e1614"
            if abs(b(x, y) - 0.5) < 0.02:
                return "#140e0c"
            pal = ["#4a3a32", "#5a463c", "#6a5246", "#7a5e50"] if band > 5 else ["#3a2e2a", "#4a3a34", "#584640", "#66524a"]
            return pick(pal, a(x, y) * 0.7 + b(x, y) * 0.3)

        return paint(f)

    def crater_road():
        # A road across the shattered crater: dark basalt plates, dust in the joints.
        a, b = noise(4, 2, 6021), noise(8, 4, 6022)
        dust = speckle(6023, 30)

        def f(x, y):
            if (x, y) in dust:
                return "#a8927e"
            cell = (int((x + 3 * b(x, y) * 4) / 11) * 7 + int((y + 2 * a(x, y) * 4) / 9) * 13) % 5
            gap = (x + int(b(x, y) * 4)) % 11 == 0 or (y + int(a(x, y) * 4)) % 9 == 0
            if gap:
                return "#7a6656"
            return pick(["#3c3230", "#463a36", "#50423c", "#5a4a42", "#64524a"], 0.15 + cell * 0.14 + a(x, y) * 0.2)

        return paint(f)

    def impact_glow():
        # Dark rock split by fissures glowing magenta and orange from the heat below.
        a, b = noise(4, 2, 6031), noise(8, 4, 6032)

        def f(x, y):
            v = abs(a(x, y) * 0.6 + b(x, y) * 0.4 - 0.5)
            if v < 0.025:
                return "#fff0d8"
            if v < 0.05:
                return "#ffa040"
            if v < 0.085:
                return "#e03a8a"
            return pick(["#1a1214", "#22181a", "#2a1e20"], b(x, y))

        return paint(f)

    def asteroid_rock():
        # The asteroid: pitted, iron-dark, glinting metal flecks.
        a, b = noise(8, 4, 6041), noise(16, 8, 6042)
        glint = speckle(6043, 26)
        pits = speckle(6044, 18)

        def f(x, y):
            if (x, y) in glint:
                return "#c8c0b8"
            if (x, y) in pits or ((x + 1) % 64, y) in pits:
                return "#0e0c0e"
            return pick(["#1e1c22", "#28252c", "#332e36", "#3e3840", "#4a434a"], a(x, y) * 0.6 + b(x, y) * 0.4)

        return paint(f)

    def asteroid_vein():
        # The asteroid's cracks: a molten gold-magenta glow.
        a = noise(4, 8, 6051)

        def f(x, y):
            v = a(x, y)
            if (x + y * 3) % 23 == 0:
                return "#ffffff"
            return pick(["#b0206a", "#e03a7a", "#ff6a5a", "#ffa840", "#ffd870"], 0.15 + v * 0.8)

        return paint(f)

    def impact_glass():
        # Dark green-black impact glass, wet-looking streaks.
        a, b = noise(8, 2, 6061), noise(4, 8, 6062)

        def f(x, y):
            if abs(a(x, y) - b(x, y)) < 0.03:
                return "#7aa898"
            return pick(["#0e1a18", "#14241e", "#1a2e26", "#224034"], a(x, y) * 0.7 + b(x, y) * 0.3)

        return paint(f)

    # ---------------------------------------------------------------- the Crystal Descent

    def cave_ochre():
        # Warm cave rock: ochre, amber and rust in wavy flowstone layers.
        a, b = noise(8, 2, 6101), noise(16, 4, 6102)

        def f(x, y):
            w = y + 3 * math.sin(x / 64 * math.pi * 4 + a(x, y) * 3)
            band = int(w) % 8
            pal = ["#7a4a24", "#8a5a2c", "#9c6a36", "#ae7c42", "#c08e50"]
            if band == 0:
                return "#5a3418"
            return pick(pal, 0.2 + a(x, y) * 0.5 + (0.2 if band in (3, 4) else 0) + b(x, y) * 0.1)

        return paint(f)

    def cave_ochre_dark():
        a, b = noise(8, 2, 6111), noise(16, 4, 6112)

        def f(x, y):
            band = int(y + 2 * math.sin(x / 64 * math.pi * 2 + a(x, y) * 4)) % 9
            if band == 0:
                return "#2a160c"
            return pick(["#3e2412", "#4e2e18", "#5e3a1e", "#6e4626"], a(x, y) * 0.6 + b(x, y) * 0.4)

        return paint(f)

    def cave_road():
        # Old flagstones through the caverns: warm sandstone, worn smooth, dark joints.
        a, b = noise(4, 2, 6121), noise(16, 8, 6122)

        def f(x, y):
            row = y // 8
            off = 11 if row % 2 else 0
            if y % 8 == 0 or (x + off) % 22 == 0:
                return "#5a3c26"
            stone = ((x + off) // 22 + row * 3) % 4
            return pick(["#a87850", "#b8875c", "#c49668", "#d2a676", "#dcb484"], 0.12 + stone * 0.16 + a(x, y) * 0.25 + b(x, y) * 0.1)

        return paint(f)

    def bridge_stone():
        # Big dressed blocks for the stone bridges.
        a = noise(8, 4, 6131)

        def f(x, y):
            row = y // 11
            off = 16 if row % 2 else 0
            if y % 11 == 0 or (x + off) % 32 == 0:
                return "#4a3020"
            return pick(["#8a6448", "#9a7254", "#aa8262", "#b89270"], a(x, y) * 0.8 + 0.1)

        return paint(f)

    def crystal_tex(seed, pal, hi):
        a = noise(4, 8, seed)

        def f(x, y):
            facet = (x + 2 * y) % 29
            if facet == 0:
                return hi
            if (2 * x - y) % 41 == 0:
                return pal[-1]
            return pick(pal, 0.15 + a(x, y) * 0.8)

        return paint(f)

    def depths_water():
        # Deep cave water: dark blue going teal, faint light ripples.
        a, b = noise(4, 2, 6141), noise(8, 4, 6142)

        def f(x, y):
            v = a(x, y) * 0.6 + b(x, y) * 0.4
            if abs(math.sin((x + y * 2) / 64 * math.pi * 6 + v * 5)) > 0.97:
                return "#7ad8e8"
            return pick(["#082848", "#0c3458", "#10446a", "#16567a", "#1e6a88"], v)

        return paint(f)

    def flowstone():
        # Cream and amber flowstone (the cascades' rims and the cave floor's terraces).
        a = noise(16, 2, 6151)

        def f(x, y):
            v = (y + a(x, y) * 8) % 6
            return pick(["#c8986a", "#d6a878", "#e2b888", "#ecc89a"], v / 6 * 0.7 + a(x, y) * 0.3)

        return paint(f)

    # ---------------------------------------------------------------- the Lost World

    def moss_rock():
        # Cave rock furred with moss: brown stone and deep greens.
        a, b = noise(8, 4, 6201), noise(16, 8, 6202)

        def f(x, y):
            v = a(x, y) * 0.6 + b(x, y) * 0.4
            if v > 0.55:
                return pick(["#2e5a24", "#3a6e2a", "#4a8232", "#5a963c"], (v - 0.55) * 2.2)
            return pick(["#4a3a2a", "#584634", "#66523e", "#745e48"], v * 1.8)

        return paint(f)

    def jungle_lake():
        # The Lost World's turquoise lake.
        a, b = noise(4, 2, 6211), noise(8, 4, 6212)

        def f(x, y):
            v = a(x, y) * 0.6 + b(x, y) * 0.4
            if abs(math.sin((x * 2 - y) / 64 * math.pi * 5 + v * 4)) > 0.975:
                return "#c8fff4"
            return pick(["#0e6a6a", "#128080", "#169494", "#1eaaa4", "#2ec0b4"], v)

        return paint(f)

    def fern_floor():
        # The jungle floor: fern litter, leaf mould and moss.
        a, b = noise(8, 4, 6221), noise(16, 8, 6222)
        lit = speckle(6223, 40)

        def f(x, y):
            if (x, y) in lit:
                return "#9ad05a"
            return pick(["#24401a", "#2e5220", "#3a6428", "#4a7630", "#5a8838"], a(x, y) * 0.5 + b(x, y) * 0.5)

        return paint(f)

    def cycad_bark():
        # Cycad trunk: diamond-patterned leaf scars.
        a = noise(8, 4, 6231)

        def f(x, y):
            d = (x + y) % 8 == 0 or (x - y) % 8 == 0
            if d:
                return "#3a2a1a"
            return pick(["#6a5232", "#7a603c", "#8a6e46", "#9a7c52"], a(x, y))

        return paint(f)

    def cycad_leaf():
        # Stiff palm-like fronds: a midrib and rows of narrow leaflets.
        a = noise(4, 2, 6241)

        def f(x, y):
            if 15 <= y <= 16:
                return "#4a6a1e"
            if (x + (0 if y < 16 else 3)) % 4 == 0:
                return "#1e3e12"
            return pick(["#2e6a1e", "#3a7e24", "#4a922c", "#5aa636"], a(x, y) * 0.7 + abs(y - 16) / 16 * 0.3)

        return paint(f)

    def horsetail():
        # Giant horsetail stems: jointed green rings.
        a = noise(4, 8, 6251)

        def f(x, y):
            if y % 8 == 0:
                return "#2a3e14"
            return pick(["#4a7a24", "#5a8c2c", "#6a9e36", "#7ab042"], a(x, y) * 0.6 + (x % 8) / 8 * 0.4)

        return paint(f)

    def ruin_moss():
        # Ancient stone half-buried in moss: grey-green blocks, lichen.
        a, b = noise(8, 4, 6261), noise(16, 8, 6262)

        def f(x, y):
            row = y // 10
            off = 13 if row % 2 else 0
            if y % 10 == 0 or (x + off) % 26 == 0:
                return "#2e3428"
            v = a(x, y)
            if b(x, y) > 0.62:
                return pick(["#4a6e2e", "#5a7e36", "#6a9040"], v)
            return pick(["#6a6c5c", "#7a7c6a", "#8a8c78", "#9a9a86"], v)

        return paint(f)

    def jungle_track():
        # The road through the Lost World: red earth packed hard, roots, scattered leaves.
        a, b = noise(4, 2, 6271), noise(16, 8, 6272)
        leaves = speckle(6273, 30)

        def f(x, y):
            if (x, y) in leaves:
                return "#4a7a2a"
            if abs(b(x, y) - 0.5) < 0.018:
                return "#3e2414"
            track = x % 32 in (8, 9, 22, 23)
            return pick(["#6a3a22", "#7a4628", "#8a5230", "#9a5e38", "#aa6a40"], 0.15 + a(x, y) * 0.5 + b(x, y) * 0.2 + (0.12 if track else 0))

        return paint(f)

    def dino_trackway():
        # A muddy bank pressed full of three-toed footprints.
        a = noise(8, 4, 6281)

        def f(x, y):
            cx, cy = (x % 16) - 8, (y % 16) - 8
            if (x // 16 + y // 16) % 2 == 0 and cy < 2 and abs(cx) < 1 + (0 if cy < -3 else 2) and abs(cx) * 2 < abs(cy) + 3:
                return "#2a1a10"
            return pick(["#5a3e2a", "#6a4a32", "#7a563a"], a(x, y))

        return paint(f)

    # ---------------------------------------------------------------- volcanic depths, the lair

    def black_rock():
        # Volcanic black rock: glassy basalt columns, faint red reflections.
        a, b = noise(8, 2, 6301), noise(16, 4, 6302)

        def f(x, y):
            col = (x + int(a(x, y) * 3)) % 9
            if col == 0:
                return "#060404"
            if abs(b(x, y) - 0.5) < 0.02:
                return "#3a1610"
            return pick(["#141012", "#1c1618", "#241c1e", "#2e2426"], a(x, y) * 0.6 + col / 9 * 0.4)

        return paint(f)

    def lava_flow():
        # Flowing lava: yellow-white channels between rafts of dark crust (V runs downhill).
        a, b = noise(4, 2, 6311), noise(8, 4, 6312)

        def f(x, y):
            v = a(x, y) * 0.55 + b(x, y) * 0.45
            if v < 0.3:
                return pick(["#2a0e08", "#3a140a"], v * 3)
            if v < 0.38:
                return "#c02a08"
            return pick(["#e04a0a", "#f06a10", "#ff9020", "#ffbe40", "#fff090"], (v - 0.38) * 1.7)

        return paint(f)

    def lava_crust():
        # Cooling lava ground: black crust broken by glowing orange cracks.
        a, b = noise(4, 2, 6321), noise(16, 8, 6322)

        def f(x, y):
            v = abs(a(x, y) * 0.7 + b(x, y) * 0.3 - 0.5)
            if v < 0.022:
                return "#ffc040"
            if v < 0.04:
                return "#e04a10"
            return pick(["#141010", "#1e1614", "#281e1a", "#322620"], b(x, y))

        return paint(f)

    def basalt_slab():
        # The volcanic causeways' road: dark hexagonal basalt setts, red dust.
        a = noise(8, 4, 6331)

        def f(x, y):
            col = x // 8
            yy = y + (4 if col % 2 else 0)
            if x % 8 == 0 or yy % 8 == 0:
                return "#5a2a1e"
            return pick(["#2e2626", "#38302e", "#423836", "#4e423e"], a(x, y) * 0.7 + ((col * 5 + yy // 8 * 3) % 4) * 0.08)

        return paint(f)

    def lair_rock():
        # The lair's walls: crimson-black rock, scorched smooth, ember streaks.
        a, b = noise(8, 2, 6341), noise(4, 8, 6342)

        def f(x, y):
            if abs(b(x, y) - 0.5) < 0.008 and a(x, y) > 0.55:
                return "#ff5a1a"
            return pick(["#1a0806", "#260c08", "#32100a", "#42160c", "#521c10"], a(x, y) * 0.7 + b(x, y) * 0.3)

        return paint(f)

    def lair_road():
        # The dragon bridge's deck: great scorched flagstones, soot and ember-glow joints.
        a = noise(8, 4, 6351)

        def f(x, y):
            row = y // 16
            off = 16 if row % 2 else 0
            if y % 16 == 0 or (x + off) % 32 == 0:
                return "#8a2a0e"
            return pick(["#3a2a26", "#46322c", "#523c34", "#5e463c"], a(x, y) * 0.8 + 0.1)

        return paint(f)

    def bone_pile():
        # Old bones by the lair: bleached ivory and shadow.
        a = noise(8, 4, 6361)

        def f(x, y):
            if (x * 3 + y * 5) % 17 < 2:
                return "#3a2a1e"
            return pick(["#b8a888", "#c8b898", "#d8c8a8", "#e8dcc0"], a(x, y))

        return paint(f)

    def ember_ash():
        # Ash-grey ground near the fire: soft grey, ember specks.
        a = noise(8, 4, 6371)
        emb = speckle(6372, 22)

        def f(x, y):
            if (x, y) in emb:
                return "#ff7a20"
            return pick(["#3a3434", "#46403e", "#524a48", "#5e5652"], a(x, y))

        return paint(f)

    # ---------------------------------------------------------------- the Heart of the Earth

    def core_glass():
        # The core chamber's rock: dark violet glass shot with gold veins.
        a, b = noise(4, 2, 6401), noise(8, 4, 6402)

        def f(x, y):
            v = abs(a(x, y) * 0.6 + b(x, y) * 0.4 - 0.5)
            if v < 0.01:
                return "#ffe080"
            if v < 0.022:
                return "#b07a30"
            return pick(["#1a0c2a", "#241238", "#2e1846", "#3a2054"], b(x, y) * 0.7 + a(x, y) * 0.3)

        return paint(f)

    def core_road():
        # The ring road round the core: dark stone inlaid with glowing gold-and-magenta lines.
        a = noise(8, 4, 6411)

        def f(x, y):
            if y % 16 in (7, 8) and x % 8 < 5:
                return "#ffcc50"
            if x % 32 in (0, 1):
                return "#e040a0"
            return pick(["#24182e", "#2e2038", "#382842", "#42304c"], a(x, y))

        return paint(f)

    def core_abyss():
        # The bottomless glow under the core.
        a, b = noise(4, 2, 6421), noise(8, 4, 6422)

        def f(x, y):
            v = a(x, y) * 0.6 + b(x, y) * 0.4
            return pick(["#5a0a5a", "#8a1a7a", "#c03a8a", "#ff6a8a", "#ffb070", "#fff0b0"], v)

        return paint(f)

    def spiral_road():
        # The ascent's road: pale cut sandstone, chisel marks, a worn centre.
        a, b = noise(4, 2, 6431), noise(16, 8, 6432)

        def f(x, y):
            if y % 12 == 0:
                return "#8a6a4a"
            if (x + y) % 7 == 0 and b(x, y) > 0.5:
                return "#b89470"
            return pick(["#c8a47c", "#d4b088", "#dfbe96", "#e8cca6"], a(x, y) * 0.7 + (0.2 if 20 < x < 44 else 0))

        return paint(f)

    def crystal_rock():
        # Rock crusted with tiny crystals (the shaft's lowest walls).
        a = noise(8, 4, 6441)
        sp = speckle(6442, 70)

        def f(x, y):
            if (x, y) in sp:
                return "#e0b0ff" if (x + y) % 2 else "#a0f0ff"
            return pick(["#2a1e34", "#342640", "#3e2e4c", "#4a3858"], a(x, y))

        return paint(f)

    # ---------------------------------------------------------------- the hidden cavern

    def causeway_stone():
        # The ancients' causeway: big worn grey-green blocks, moss in the joints.
        a = noise(8, 4, 6501)

        def f(x, y):
            row = y // 12
            off = 12 if row % 2 else 0
            if y % 12 == 0 or (x + off) % 24 == 0:
                return "#2e4a2a"
            return pick(["#5a5e56", "#666a60", "#72766a", "#7e8276"], a(x, y) * 0.8 + 0.1)

        return paint(f)

    def dark_pool():
        # The hidden cavern's still black-green pool, flecks of glow.
        a = noise(4, 2, 6511)
        sp = speckle(6512, 16)

        def f(x, y):
            if (x, y) in sp:
                return "#6affd8"
            return pick(["#04100e", "#061814", "#0a201c", "#0e2a24"], a(x, y))

        return paint(f)

    def glow_fungus():
        # Glowing cave fungus: teal caps with pale gills.
        a = noise(4, 4, 6521)

        def f(x, y):
            if y % 8 == 7:
                return "#d8fff4"
            return pick(["#0a6a5a", "#10907a", "#18b89a", "#3ae0c0"], a(x, y))

        return paint(f)

    def ancient_glyph():
        # Carved glyphs glowing faintly gold in old stone.
        a = noise(8, 4, 6531)

        def f(x, y):
            cx, cy = x % 16, y % 16
            g = (cx in (3, 12) and 3 <= cy <= 12) or (cy in (3, 12) and 3 <= cx <= 12) or (cx == cy and 5 < cx < 11)
            if g and (x // 16 + y // 16) % 2 == 0:
                return "#ffd060"
            if g:
                return "#d8a040"
            return pick(["#4a4c44", "#56584e", "#626458", "#6e7062"], a(x, y))

        return paint(f)

    # ---------------------------------------------------------------- the desert outpost

    def depths_road():
        # The desert's dirt road: sun-baked tan, wheel ruts, pebbles.
        a, b = noise(4, 2, 6601), noise(16, 8, 6602)
        peb = speckle(6603, 36)

        def f(x, y):
            if (x, y) in peb:
                return "#f0d8b0"
            track = x % 32 in (9, 10, 22, 23)
            return pick(["#b07a4a", "#be8854", "#cc9660", "#d8a46c", "#e2b27a"], 0.15 + a(x, y) * 0.45 + b(x, y) * 0.25 - (0.12 if track else 0))

        return paint(f)

    def meteor_banner():
        # A race banner: orange and black with a white meteor streak.
        def f(x, y):
            if abs((x - 2 * y) % 64 - 32) < 3 and 6 < y < 26:
                return "#ffffff"
            if abs((x - 2 * y) % 64 - 26) < 3 and 8 < y < 24:
                return "#ffe080"
            return "#e8641c" if (x // 16) % 2 == 0 else "#2a1e1a"

        return paint(f)

    def warning_stripe():
        def f(x, y):
            return "#e8a020" if ((x + y) // 8) % 2 == 0 else "#1e1a18"

        return paint(f)

    def depths_mist():
        a, b = noise(4, 2, 6621), noise(8, 4, 6622)

        def f(x, y):
            return pick(["#d8c8b8", "#e2d4c6", "#ece0d4", "#f6eee6"], a(x, y) * 0.6 + b(x, y) * 0.4)

        return paint(f)

    def ember_mist():
        a, b = noise(4, 2, 6631), noise(8, 4, 6632)

        def f(x, y):
            return pick(["#8a2a14", "#a83a1a", "#c85024", "#e86a30"], a(x, y) * 0.6 + b(x, y) * 0.4)

        return paint(f)

    T = "impact_depths"
    flow = {"scrollU": 0.0, "scrollV": 0.06, "wave": 0.04, "wavePeriod": 5, "glow": 1.0, "pulse": 0.2, "pulsePeriod": 3.0}
    return [
        ("crater_ground", "Scorched Crater Ground", T, "loose_sand", crater_ground, 7, None),
        ("crater_rock", "Shocked Crater Rock", T, "wall", crater_rock, 12, None),
        ("crater_road", "Crater Plates Road", T, "road", crater_road, 6, None),
        ("impact_glow", "Glowing Impact Fissure", T, "wall", impact_glow, 8, GLOW(0.9, 0.4, 3.2)),
        ("asteroid_rock", "Asteroid Rock", T, "wall", asteroid_rock, 6, None),
        ("asteroid_vein", "Asteroid Vein", T, "wall", asteroid_vein, 3, GLOW(1.2, 0.45, 2.6)),
        ("impact_glass", "Impact Glass", T, "wall", impact_glass, 4, None),
        ("cave_ochre", "Warm Cave Rock", T, "wall", cave_ochre, 10, None),
        ("cave_ochre_dark", "Deep Cave Rock", T, "wall", cave_ochre_dark, 10, None),
        ("cave_road", "Cavern Flagstones", T, "road", cave_road, 5, None),
        ("bridge_stone", "Bridge Stone", T, "road", bridge_stone, 4, None),
        ("crystal_aqua", "Aqua Crystal", T, "wall", lambda: crystal_tex(6151, ["#0a4a6a", "#0e6e90", "#1898b8", "#3ac8e0", "#a0f4ff"], "#ffffff"), 3, GLOW(0.85, 0.3, 4.2)),
        ("crystal_amethyst", "Amethyst Crystal", T, "wall", lambda: crystal_tex(6152, ["#3a1060", "#5a1a8a", "#8a2ab0", "#c050d8", "#f0a8ff"], "#ffffff"), 3, GLOW(0.85, 0.3, 5.1)),
        ("crystal_rose", "Rose Crystal", T, "wall", lambda: crystal_tex(6153, ["#6a1040", "#9a1a5a", "#d0307a", "#f06aa0", "#ffc0dc"], "#ffffff"), 3, GLOW(0.85, 0.3, 3.7)),
        ("core_crystal", "Core Crystal", T, "wall", lambda: crystal_tex(6154, ["#8a4a10", "#c07818", "#f0a828", "#ffd050", "#fff4b0"], "#ffffff"), 3, GLOW(1.1, 0.5, 2.2)),
        ("depths_water", "Cavern Water", T, "deep_water", depths_water, 10, {"scrollU": 0.004, "scrollV": 0.01, "wave": 0.03, "wavePeriod": 6, "glow": 0.25}),
        ("depths_stream", "Underground River", T, "water", depths_water, 8, {"scrollU": 0.0, "scrollV": 0.12, "wave": 0.03, "wavePeriod": 3, "glow": 0.25}),
        ("flowstone", "Flowstone", T, "dirt", flowstone, 6, None),
        ("moss_rock", "Mossy Cave Rock", T, "wall", moss_rock, 9, None),
        ("jungle_lake", "Turquoise Lake", T, "deep_water", jungle_lake, 10, {"scrollU": 0.004, "scrollV": 0.008, "wave": 0.03, "wavePeriod": 7, "glow": 0.2}),
        ("jungle_river", "Jungle River", T, "water", jungle_lake, 8, {"scrollU": 0.0, "scrollV": 0.1, "wave": 0.03, "wavePeriod": 3, "glow": 0.15}),
        ("fern_floor", "Fern Floor", T, "grass", fern_floor, 6, None),
        ("cycad_bark", "Cycad Trunk", T, "wall", cycad_bark, 2, None),
        ("cycad_leaf", "Cycad Frond", T, "grass", cycad_leaf, 3, {"scrollU": 0, "scrollV": 0, "sway": 0.06}),
        ("horsetail", "Giant Horsetail", T, "grass", horsetail, 2, {"scrollU": 0, "scrollV": 0, "sway": 0.05}),
        ("ruin_moss", "Mossy Ruin Stone", T, "wall", ruin_moss, 5, None),
        ("jungle_track", "Lost World Track", T, "packed_dirt", jungle_track, 6, None),
        ("dino_trackway", "Footprint Mud", T, "mud", dino_trackway, 6, None),
        ("black_rock", "Volcanic Black Rock", T, "wall", black_rock, 10, None),
        ("lava_flow", "Flowing Lava", T, "lava", lava_flow, 10, flow),
        ("lava_fall", "Lava Fall", T, "lava", lava_flow, 8, {"scrollU": 0.0, "scrollV": 0.45, "wave": 0.06, "wavePeriod": 2, "glow": 1.0}),
        ("lava_crust", "Lava Crust", T, "dirt", lava_crust, 6, GLOW(0.5, 0.35, 3.5)),
        ("basalt_slab", "Basalt Setts", T, "road", basalt_slab, 4, None),
        ("lair_rock", "Lair Rock", T, "wall", lair_rock, 10, GLOW(0.15)),
        ("lair_road", "Scorched Flagstones", T, "road", lair_road, 6, GLOW(0.12, 0.3, 4.0)),
        ("bone_pile", "Old Bones", T, "wall", bone_pile, 2, None),
        ("ember_ash", "Ember Ash", T, "dirt", ember_ash, 6, None),
        ("core_glass", "Core Glass", T, "wall", core_glass, 9, GLOW(0.3, 0.4, 2.8)),
        ("core_road", "Core Ring Road", T, "road", core_road, 4, GLOW(0.7, 0.5, 2.2)),
        ("core_abyss", "Core Abyss", T, "abyss", core_abyss, 14, {"scrollU": 0.01, "scrollV": 0.02, "glow": 1.0, "pulse": 0.4, "pulsePeriod": 2.2}),
        ("spiral_road", "Ascent Road", T, "road", spiral_road, 5, None),
        ("crystal_rock", "Crystal-Crusted Rock", T, "wall", crystal_rock, 6, GLOW(0.3, 0.3, 3.0)),
        ("causeway_stone", "Ancient Causeway", T, "road", causeway_stone, 5, None),
        ("dark_pool", "Still Black Pool", T, "deep_water", dark_pool, 8, {"scrollU": 0.002, "scrollV": 0.003, "glow": 0.3}),
        ("glow_fungus", "Glow Fungus", T, "wall", glow_fungus, 1, GLOW(1.0, 0.4, 3.0)),
        ("ancient_glyph", "Glowing Glyphs", T, "wall", ancient_glyph, 3, GLOW(0.5, 0.45, 4.5)),
        ("depths_road", "Desert Track", T, "packed_dirt", depths_road, 6, None),
        ("meteor_banner", "Meteor Banner", T, "wall", meteor_banner, 3, {"scrollU": 0, "scrollV": 0, "sway": 0.05}),
        ("warning_stripe", "Warning Stripes", T, "wall", warning_stripe, 2, None),
        ("depths_mist", "Dust Haze", T, "wall", depths_mist, 16, {"scrollU": 0.01, "scrollV": 0.003, "wave": 0.05, "wavePeriod": 9, "opacity": 0.35}),
        ("ember_mist", "Ember Haze", T, "wall", ember_mist, 16, {"scrollU": 0.008, "scrollV": -0.01, "wave": 0.05, "wavePeriod": 7, "opacity": 0.3, "glow": 0.8}),
    ]
