# The valley village's own paint (Blake, Oct 28, review-valley_region 3: the camp's
# logs "should just be a normal log", better doors on every hut, huts that "vary ... lots
# of character", a "Repair" sign on the kart shed): log bark and end grain, hut walls in
# three daubs, plank doors, two more thatches, a painted hide, and the shed's sign.
# SPDX-License-Identifier: MIT
#
#   python3 tools/blender/prehistoric/village_textures.py
#
# Every pixel is made here from noise and simple shapes (original artwork). Needs
# Pillow. Safe to re-run: the textures and their library entries are replaced.

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
LIB = os.path.join(os.path.dirname(HERE), "addons", "kartipelago_tools", "library")

from region_textures import _noise, _paint, thumb  # noqa: E402


def _hex(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _pick(pal, v):
    return pal[max(0, min(len(pal) - 1, int(v * len(pal))))]


def log_bark():
    """A felled log's bark: rough plates split by deep fissures running along the log
    (V), a few cross cracks, a touch of moss low down. Not a fire, not a palm."""
    w, h = 64, 64
    a, b = _noise(8, 4, 701, w, h), _noise(16, 16, 702, w, h)
    m = _noise(4, 4, 703, w, h)
    pal = [_hex(c) for c in ("#2e2016", "#3e2c1e", "#4e3826", "#5e4630", "#70563c", "#82664a")]
    moss = [_hex(c) for c in ("#4a5a28", "#5a6c30")]

    def f(x, y):
        # Plates: columns of wandering width, split by dark fissures.
        u = x + 6.0 * a(x, y) * 4
        col = u % 11.0
        if col < 1.3:
            return pal[0]
        if col < 2.2:
            return pal[1]
        # A cross crack now and then.
        if (y + int(col * 3)) % 23 == 0 and b(x, y) > 0.45:
            return pal[1]
        v = 0.3 + 0.45 * b(x, y) + 0.25 * (col / 11.0)
        if m(x, y) > 0.72 and b(x, y) > 0.5:
            return moss[int(b(x, y) * 7) % 2]
        return _pick(pal[2:], v)

    return _paint(w, h, f)


def log_end():
    """A log's cut end, mapped round the end of each log (the UVs are made to fit):
    pale wood in growth rings, a dark heart, radial cracks and the bark's dark rim."""
    w, h = 64, 64
    a = _noise(8, 8, 711, w, h)
    rings = [_hex(c) for c in ("#a8804e", "#b88e58", "#c89e66", "#d4ac74")]

    def f(x, y):
        dx, dy = x - 31.5, y - 31.5
        r = math.hypot(dx, dy) / 31.5
        if r > 0.93:
            return _hex("#3a2a1c")
        if r > 0.86:
            return _hex("#5a4230")
        ang = math.atan2(dy, dx)
        # Radial checks from the heart.
        for k in range(3):
            if abs(((ang - k * 2.2) + math.pi) % math.tau - math.pi) < 0.03 * (1.2 - r) and r < 0.75:
                return _hex("#5e4028")
        rr = r * 9.0 + 0.6 * a(x, y)
        if r < 0.08:
            return _hex("#7a5232")
        if rr % 1.0 < 0.22:
            return _hex("#8a6238")
        return _pick(rings, 0.25 + 0.5 * (1 - r) + 0.25 * a(x, y))

    return _paint(w, h, f)


def daub(base, seed):
    """Hut walls: daub smoothed on by hand, trowel sweeps, hairline cracks, a little
    staining up from the ground (the bottom of the texture)."""
    w, h = 64, 64
    a, b = _noise(4, 4, seed, w, h), _noise(16, 16, seed + 1, w, h)
    c = _noise(8, 2, seed + 2, w, h)
    pal = [_hex(x) for x in base]

    def f(x, y):
        sweep = 0.5 + 0.5 * math.sin((x + y * 0.6) * 0.35 + a(x, y) * 6)
        v = 0.25 + 0.3 * a(x, y) + 0.2 * b(x, y) + 0.15 * sweep
        if b(x, y) > 0.8 and c(x, y) > 0.6:
            v -= 0.35  # (a crack)
        if y > 56:
            v -= (y - 56) * 0.04  # (stained from the ground)
        return _pick(pal, v)

    return _paint(w, h, f)


def hut_door():
    """A plank door: five boards with dark gaps, bound by two lashed crosspieces, wooden
    pegs, a carved sun-disc and a pull ring."""
    w, h = 64, 64
    a = _noise(2, 8, 721, w, h)
    wood = [_hex(c) for c in ("#5a3a20", "#6a4628", "#7a5230", "#8a5e38", "#9a6a40")]

    def f(x, y):
        if x < 2 or x > 61 or y < 2 or y > 61:
            return _hex("#2a1a0e")
        board = (x - 2) // 12
        if (x - 2) % 12 == 11:
            return _hex("#24160c")
        # The crosspieces, with rope lashed round each end.
        for cy in (14, 48):
            if cy - 3 <= y <= cy + 3:
                if x < 8 or x > 55:
                    return _hex("#c8a868") if (x + y) % 3 else _hex("#8a7040")
                if y in (cy - 3, cy + 3):
                    return _hex("#3a2616")
                if (x - 2) % 12 in (5, 6) and y == cy:
                    return _hex("#2a1a0e")  # (pegs)
                return _pick(wood, 0.55 + 0.3 * a(x, y))
        # The carved sun on the middle boards.
        d = math.hypot(x - 31.5, y - 31)
        if 7.5 < d < 9.0 or d < 3.0:
            return _hex("#d88a3a")
        if d < 9.0 and int(math.degrees(math.atan2(y - 31, x - 31.5))) % 45 < 6:
            return _hex("#c87a30")
        # The pull ring.
        if 3.0 <= math.hypot(x - 50, y - 33) <= 4.2:
            return _hex("#2a2a2a")
        grain = 0.5 + 0.5 * math.sin(y * 0.5 + board * 2.3 + a(x, y) * 5)
        return _pick(wood, 0.15 + 0.5 * grain + 0.3 * a(x, y))

    return _paint(w, h, f)


def thatch_shade(pal_hex, seed):
    """Thatch in courses, each overlapping the one below with a ragged fringe."""
    w, h = 64, 64
    a, b = _noise(32, 4, seed, w, h), _noise(4, 4, seed + 1, w, h)
    pal = [_hex(c) for c in pal_hex]

    def f(x, y):
        row = y // 16
        yy = y % 16
        fringe = 13 + int(2.5 * a(x, y) * 2) - (x * 7 + row * 5) % 3
        if yy >= fringe:
            return pal[0]
        straw = 0.5 + 0.5 * math.sin(x * 2.1 + row * 1.9 + a(x, y) * 7)
        v = 0.1 + straw * 0.45 + b(x, y) * 0.25 + yy * 0.018
        return _pick(pal, v)

    return _paint(w, h, f)


def painted_hide():
    """A doorway hide: tanned leather, a painted spiral and dots, darker at its edges."""
    w, h = 64, 64
    a = _noise(4, 4, 731, w, h)
    pal = [_hex(c) for c in ("#8a5e36", "#9e6e40", "#b0804c", "#c2925a")]

    def f(x, y):
        dx, dy = x - 31.5, y - 31.5
        r = math.hypot(dx, dy)
        ang = math.atan2(dy, dx)
        if r < 20 and abs((r - (ang + math.pi) / math.tau * 6.0) % 6.0 - 3.0) < 0.9:
            return _hex("#7a2a1a")
        if 24 < r < 27 and int((ang + math.pi) * 6) % 2 == 0:
            return _hex("#e8d8a8")
        edge = min(x, y, 63 - x, 63 - y)
        return _pick(pal, 0.2 + 0.5 * a(x, y) + min(0.3, edge * 0.03) - 0.2)

    return _paint(w, h, f)


def repair_sign():
    """KART REPAIR, carved and painted on a plank (in 64 px tiles: see sign_tiles)."""
    import make_textures as mt

    return mt.sign_board("KART REPAIR", 192, 32, seed=21, ink="#f4d27a")


def materials():
    """[(id, name, theme, surface, painter, tile, fx)] for every texture made here."""
    out = [
        ("log_bark", "Log Bark", "river_valley", "wall", log_bark, 1.6, None),
        ("log_cut", "Log Cut End", "river_valley", "wall", log_end, 1, None),
        ("daub_ochre", "Hut Daub (Ochre)", "river_valley", "wall",
         lambda: daub(("#8a5e34", "#9e6e3e", "#b0804a", "#c29256", "#d0a264"), 741), 2.5, None),
        ("daub_cream", "Hut Daub (Cream)", "river_valley", "wall",
         lambda: daub(("#9a8a6a", "#b0a07c", "#c4b48e", "#d4c6a0", "#e2d6b4"), 751), 2.5, None),
        ("daub_rose", "Hut Daub (Rose)", "river_valley", "wall",
         lambda: daub(("#8a4e3c", "#9e5c46", "#b06c52", "#c27c5e", "#d08c6a"), 761), 2.5, None),
        ("hut_door", "Hut Door", "river_valley", "wall", hut_door, 1, None),
        ("thatch_dark", "Thatch (Old)", "river_valley", "wall",
         lambda: thatch_shade(("#3e3018", "#5e4a26", "#76602e", "#8c7438", "#a08642"), 771), 3, None),
        ("thatch_pale", "Thatch (Fresh Reed)", "river_valley", "wall",
         lambda: thatch_shade(("#6a6a30", "#9a9448", "#b8b058", "#ccc46a", "#dcd67e"), 781), 3, None),
        ("painted_hide", "Painted Hide", "river_valley", "wall", painted_hide, 1.4, None),
    ]
    # The sign, in 64 px tiles laid side by side (make_textures.sign_tiles).
    for k in range(3):
        out.append(("sign_repair_%d" % (k + 1), "Sign: Kart Repair (%d/3)" % (k + 1), "river_valley", "wall",
                    (lambda k=k: repair_sign().crop((k * 64, 0, k * 64 + 64, 32))), 2, None))
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
    print("painted", len(made), "village textures")


if __name__ == "__main__":
    sys.exit(main())
