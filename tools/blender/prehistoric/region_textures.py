# The overworld regions' own paint (Blake, Oct 28): the TRANSITIONS where two worlds meet
# ("we need to gradually transition between the grass and lava rock ... transitionary
# textures ... we can just color gradient the transition"), and the rivers' living water
# ("in our original Oasis level before the rework we had high quality water: let's bring
# it in": the lagoon effect, src/render/trackMaterials.ts).
# SPDX-License-Identifier: MIT
#
#   python3 tools/blender/prehistoric/region_textures.py
#
# A transition texture is two library textures mixed: the second showing through the
# first in organic patches that grow with the mix (25, 50, 75%), and both pulled a little
# toward each other's colour, so a band of them reads as one ground turning into another.
# Every pixel is made here from the library's own (original) textures. Needs Pillow.
# Safe to re-run: the textures and their library entries are replaced.

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(os.path.dirname(HERE), "addons", "kartipelago_tools", "library")
MIXES = (25, 50, 75)

# The pairs (first, second) that meet somewhere in a region: ground, shoulders, roads.
PAIRS = [
    # Dinosaur Valley
    ("valley_grass", "jungle_leafcover"),
    ("valley_grass", "bog_bank"),
    ("bog_bank", "ash_soil"),
    ("ash_soil", "jungle_leafcover"),
    ("valley_road", "jungle_path"),
    ("valley_road", "bog_paving"),
    ("bog_paving", "basalt_road"),
    ("basalt_road", "jungle_path"),
    ("bog_moss_ground", "scorched_ground"),
    ("valley_grass", "bog_moss_ground"),
    ("scorched_ground", "jungle_leafcover"),
    ("ancient_grass", "canopy_dark"),
    ("ancient_grass", "bog_moss_ground"),
    ("bog_moss_ground", "ember_ash"),
    ("ember_ash", "canopy_dark"),
    # The Snow Kingdom
    ("snow_ground", "summit_snow"),
    ("snow_ground", "rift_snow"),
    ("summit_snow", "rift_snow"),
    ("hearth_cobble", "snow_stone_road"),
    ("snow_stone_road", "summit_road"),
    ("summit_road", "rift_road"),
    ("rift_road", "packed_snow_road"),
    ("packed_snow_road", "hearth_cobble"),
    # Desert World
    ("pale_sand", "red_sand"),
    ("red_sand", "gold_sand"),
    ("gold_sand", "gulch_sand"),
    ("gulch_sand", "slickrock"),
    ("slickrock", "pale_sand"),
    ("dash_road", "oasis_paving"),
    ("oasis_paving", "gulch_road"),
    ("gulch_road", "dash_road"),
    ("dash_shoulder", "gold_sand"),
    ("gold_sand", "gulch_verge"),
    ("gulch_verge", "talus"),
    ("talus", "dash_shoulder"),
    # Tropic Isles
    ("isle_jungle", "wreck_sand"),
    ("wreck_sand", "cove_sand"),
    ("cove_sand", "beach_sand"),
    ("beach_sand", "isle_jungle"),
    ("isle_jungle", "cove_sand"),
    ("beach_road", "cove_road"),
    ("cove_road", "wreck_road"),
    # The Dragon Kingdom
    ("keep_grass", "moon_grass"),
    ("keep_grass", "ember_moss"),
    ("ember_moss", "ember_rubble"),
    ("ember_rubble", "em_jungle_grass"),
    ("em_jungle_grass", "keep_grass"),
    ("keep_cobble", "moon_paving"),
    ("moon_paving", "keep_flag"),
    ("keep_flag", "ember_setts"),
    ("ember_setts", "em_road"),
    ("em_road", "keep_cobble"),
    ("keep_path", "moon_grass"),
    ("keep_path", "ember_path"),
    ("ember_path", "em_verge"),
    ("em_verge", "keep_path"),
]


def blend_id(a, b, p):
    """The id of the transition from a to b, p% of the way (25, 50, 75)."""
    return "tx_%s__%s_%d" % (a, b, p)


def _noise(cx, cy, seed, w, h):
    """Smooth value noise tiling over w x h with cx x cy cells (as make_textures.noise)."""
    s = (seed * 2654435761) & 0xFFFFFFFF or 1

    def r():
        nonlocal s
        s ^= (s << 13) & 0xFFFFFFFF
        s ^= s >> 17
        s ^= (s << 5) & 0xFFFFFFFF
        return s / 4294967296

    g = [[r() for _ in range(cx)] for _ in range(cy)]

    def at(x, y):
        fx, fy = x / w * cx, y / h * cy
        i, j = math.floor(fx), math.floor(fy)
        u, v = fx - i, fy - j
        u, v = u * u * (3 - 2 * u), v * v * (3 - 2 * v)
        a = g[j % cy][i % cx] + (g[j % cy][(i + 1) % cx] - g[j % cy][i % cx]) * u
        b = g[(j + 1) % cy][i % cx] + (g[(j + 1) % cy][(i + 1) % cx] - g[(j + 1) % cy][i % cx]) * u
        return a + (b - a) * v

    return at


def _load(mid):
    from PIL import Image

    return Image.open(os.path.join(LIB, "textures", mid + ".png")).convert("RGB")


def _mean(im):
    px = [im.getpixel((x, y)) for y in range(im.height) for x in range(im.width)]
    n = len(px)
    return tuple(sum(p[k] for p in px) / n for k in range(3))


def blend(a, b, p, seed=0):
    """a turning into b, p% of the way."""
    from PIL import Image

    A, B = _load(a), _load(b)
    w, h = max(A.width, B.width), max(A.height, B.height)
    A = A.resize((w, h), Image.NEAREST)
    B = B.resize((w, h), Image.NEAREST)
    ma, mb = _mean(A), _mean(B)
    big = _noise(4, 2, 101 + seed, w, h)
    fine = _noise(16, 8, 202 + seed, w, h)
    q = p / 100.0
    out = Image.new("RGB", (w, h))
    pa, pb, po = A.load(), B.load(), out.load()
    for y in range(h):
        for x in range(w):
            m = 0.7 * big(x, y) + 0.3 * fine(x, y)
            # (where the mask is under the mix, the second shows: more of it as p grows)
            take_b = m < q
            src = pb[x, y] if take_b else pa[x, y]
            # Each side drifts toward the other's colour (more so near the patches' edges).
            edge = 1.0 - min(1.0, abs(m - q) / 0.12)
            pull = (0.25 + 0.25 * edge) * (q if not take_b else 1.0 - q)
            tgt = ma if take_b else mb
            po[x, y] = tuple(int(round(src[k] + (tgt[k] - src[k]) * pull)) for k in range(3))
    return out


def river():
    """The rivers' and lakes' living water: clear turquoise over a sandy bed, soft lighter
    swirls (the lagoon effect adds the waves, ripples of light, glitter and sky)."""
    from PIL import Image

    w, h = 64, 32
    a, b = _noise(4, 2, 77, w, h), _noise(16, 8, 78, w, h)
    pal = [(38, 128, 156), (44, 146, 170), (52, 162, 182), (66, 178, 192), (92, 196, 204)]
    im = Image.new("RGB", (w, h))
    px = im.load()
    for y in range(h):
        for x in range(w):
            v = 0.6 * a(x, y) + 0.4 * b(x, y)
            sw = math.sin((x / w) * math.tau * 2 + a(x, y) * 4.0) * 0.5 + 0.5
            v = 0.75 * v + 0.25 * sw
            px[x, y] = pal[max(0, min(len(pal) - 1, int(v * len(pal))))]
    return im


def _paint(w, h, f):
    from PIL import Image

    im = Image.new("RGB", (w, h))
    px = im.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = f(x, y)
    return im


def giant_bark():
    """The jungle giants' bark (Blake, note 20: "remove the leaves from the bark"): deep
    brown, ridged and furrowed running up the trunk, a little lichen grey, no leaves."""
    w, h = 32, 64
    a, b = _noise(4, 4, 31, w, h), _noise(8, 16, 32, w, h)
    pal = [(46, 30, 20), (62, 40, 26), (78, 52, 33), (96, 66, 42), (118, 86, 58)]

    def f(x, y):
        ridge = 0.5 + 0.5 * math.sin((x / w) * math.tau * 5 + a(x, y) * 5.0)
        v = 0.55 * ridge + 0.3 * b(x, y) + 0.15 * a(x, y)
        if b(x, y) > 0.82 and ridge > 0.6:
            return (128, 124, 104)  # (lichen)
        return pal[max(0, min(4, int(v * 5)))]

    return _paint(w, h, f)


def camp_earth():
    """The camp's beaten earth (Blake, note 1: "I don't want the dirt to have grass in
    it"): packed warm earth, scuffed paler where feet go, a few pebbles."""
    w, h = 64, 32
    a, b = _noise(4, 2, 41, w, h), _noise(16, 8, 42, w, h)
    pal = [(150, 94, 52), (166, 106, 60), (180, 120, 70), (194, 136, 84), (206, 152, 98)]

    def f(x, y):
        v = 0.6 * a(x, y) + 0.4 * b(x, y)
        if b(x, y) > 0.86:
            return (120, 98, 80) if (x + y) % 3 else (214, 196, 170)  # (pebbles)
        return pal[max(0, min(4, int(v * 5)))]

    return _paint(w, h, f)


def thumb(im):
    from PIL import Image

    t = Image.new("RGB", (im.width * 2, im.height * 4))
    for i in range(2):
        for j in range(4):
            t.paste(im, (i * im.width, j * im.height))
    return t.resize((256, 256), Image.NEAREST)


def materials():
    """[(id, name, theme, surface, image, tile, fx)] for every texture made here."""
    path = os.path.join(LIB, "materials.json")
    with open(path, encoding="utf-8") as f:
        lib = {m["id"]: m for m in json.load(f)["materials"]}
    out = []
    for k, (a, b) in enumerate(PAIRS):
        ea, eb = lib[a], lib[b]
        tile = round((ea["tileMetres"] + eb["tileMetres"]) / 2.0, 2)
        for p in MIXES:
            # (the surface of whichever is more of it)
            surface = (ea if p <= 50 else eb)["surface"]
            out.append((blend_id(a, b, p), "%s to %s (%d%%)" % (ea["name"], eb["name"], p), ea["theme"], surface,
                        (lambda a=a, b=b, p=p, k=k: blend(a, b, p, k)), tile, None))
    out.append(("giant_bark", "Giant Bark", "jungle_cascade", "wall", giant_bark, 4, None))
    out.append(("camp_earth", "Camp Earth", "river_valley", "dirt", camp_earth, 5, None))
    out.append(("valley_river", "Valley River (living)", "river_valley", "water", river, 12,
                {"scrollU": 0.0, "scrollV": 0.02, "wave": 0.03, "wavePeriod": 5, "lagoon": 1.0}))
    return out


def main():
    path = os.path.join(LIB, "materials.json")
    with open(path, encoding="utf-8") as f:
        lib = json.load(f)
    made = materials()
    mids = {m[0] for m in made}
    lib["materials"] = [m for m in lib["materials"] if m["id"] not in mids]
    for mid, name, theme, surface, painter, tile, fx in made:
        im = painter()
        im.save(os.path.join(LIB, "textures", mid + ".png"))
        thumb(im).save(os.path.join(LIB, "thumbs", mid + ".png"))
        e = {"id": mid, "name": name, "theme": theme, "surface": surface, "image": mid + ".png", "wrap": "repeat",
             "tileMetres": tile}
        if fx:
            e["fx"] = fx
        lib["materials"].append(e)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(lib, f, indent=2)
        f.write("\n")
    print("painted", len(made), "region textures")


if __name__ == "__main__":
    sys.exit(main())
