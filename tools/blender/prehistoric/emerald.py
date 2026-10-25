# Dragon Canyon's repaint as the Emerald Kingdom (Blake's boards, Oct 25): the same lap,
# land and collision as before (dragon_canyon_v2), painted over. Three parts:
#
#   REMAP     every Dragon Canyon material -> its Emerald Kingdom texture (course_kit's
#             MAT_REMAP, which keeps each old material's surface: the driving can't
#             change);
#   install   the Eastern buildings swapped, at build time, for medieval ruins of about
#             the same size and place (the ceremonial gates become ancient stone gates,
#             pagodas ruined towers, pavilions shrines, halls and houses old stone houses,
#             the jade dragon statues mossy western ones, the dragon's bones mossy stone);
#             no villagers, no jade serpent, no desert dust;
#   extras    the jungle (giant trees, palms, ferns, big leaves, vines off the bridges),
#             glowing crystals in the caverns, and the green dragon on the watchtower.
# SPDX-License-Identifier: MIT

import math

import course_kit as kit
import keep_props as kp
import props
from course_kit import rnd
from keep_props import _p
from props import cuboid

REMAP = {
    "frontier_road": "em_road",
    "imperial_setts": "em_setts",
    "kerb_redwhite": "em_kerb",
    "canyon_ledge": "em_jungle_grass",  # (still dirt underneath: the remap keeps surfaces)
    "dust_shoulder": "em_verge",
    "oasis_grass": "em_jungle_grass",
    "canyon_scree": "em_forest_floor",
    "quarry_dust": "em_verge",
    "river_sand": "em_river_bank",
    "canyon_cliff": "em_cliff",
    "canyon_cliff_shade": "em_cliff_shade",
    "fortress_wall": "em_ruin_wall",
    "sandstone_block": "em_temple_block",
    "stone_base": "em_temple_block",
    "jade_stone": "em_moss_stone",
    "bone_ivory": "em_moss_stone",
    "roof_blue": "em_roof_moss",
    "roof_jade": "em_roof_moss",
    "red_lacquer": "em_wood_dark",
    "white_plaster": "em_plaster_moss",
    "awning_red": "em_canvas_green",
    "banner_royal": "em_banner",
    "emblem_plaque": "em_banner",
    "lattice_window": "keep_window",
    "chamber_glow": "em_crystal",
}

PALETTE = {  # keep_props' castle kit in the kingdom's stone
    "keep_ashlar": "em_ruin_wall",
    "keep_ashlar_dark": "em_moss_stone",
    "keep_parapet": "em_temple_block",
    "keep_slate": "em_roof_moss",
    "keep_roof": "em_roof_moss",
    "keep_timber": "em_plaster_moss",
    "keep_banner": "em_banner",
    "keep_banner_dark": "em_banner",
    "keep_flag_blue": "em_banner",
    "dragon_red": "em_dragon_green",
    "dragon_wing": "em_dragon_wing",
    "dragon_belly": "keep_gold",
}

STONE = "em_temple_block"
MOSS = "em_moss_stone"


# ------------------------------------------------------------------ the replacements


def stone_gate(c, span=24.0, height=10.0, roof_mat=None, grand=True):
    """An ancient stone gate over the road (along X; the road runs through along Y): two
    square pillars, a round arch between them, a green banner either side, moss."""
    name = "Emerald Gate %.1f %.1f %d" % (span, height, grand)
    half = span / 2

    def build(P, bm):
        for sx in (-1, 1):
            P.add(STONE, lambda sx=sx: cuboid(bm, (sx * half, 0, (height + 3.0) / 2 - 0.5), (3.4, 3.4, height + 4.0)))
            P.add(MOSS, lambda sx=sx: cuboid(bm, (sx * half, 0, height + 3.7), (4.2, 4.2, 1.0)))
            if grand:
                P.add("em_banner", lambda sx=sx: kp._quad(bm, [(sx * half - 1.2, -1.75, height + 1.5), (sx * half + 1.2, -1.75, height + 1.5),
                                                              (sx * half + 1.2, -1.75, height - 4.0), (sx * half - 1.2, -1.75, height - 4.0)], both=False,
                                                         normal=(0, -1, 0)))
        steps = 10

        def arch():
            rings = []
            for j in range(steps + 1):
                a = math.pi * j / steps
                x = -half * math.cos(a)
                z = height - 2.5 + 3.5 * math.sin(a)
                rings.append([bm.verts.new((x, y, zz)) for y, zz in ((-1.4, z), (1.4, z), (1.4, height + 3.2), (-1.4, height + 3.2))])
            for lo, hi in zip(rings, rings[1:]):
                for i in range(4):
                    bm.faces.new((lo[i], hi[i], hi[(i + 1) % 4], lo[(i + 1) % 4]))

        P.add(STONE, arch)

    return _p(c, name, build, fit=["em_banner"])


def shrine(c, w=6.0, roof_mat=None, rail=True):
    """A small ruined shrine: four columns on a step, a stone slab roof, one column
    broken."""
    name = "Emerald Shrine %.1f" % w

    def build(P, bm):
        P.add(STONE, lambda: cuboid(bm, (0, 0, 0.0), (w + 1.4, w + 1.4, 1.0)))
        for k, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
            h = 4.6 if k != 2 else 2.4
            P.add(STONE, lambda sx=sx, sy=sy, h=h: kp._cyl(bm, sx * w / 2, sy * w / 2, 0.4, 0.4 + h, 0.42, 0.36, n=8))
        P.add(MOSS, lambda: cuboid(bm, (-0.6, -0.6, 5.3), (w + 0.6, w + 0.6, 0.9), rot=0.0, tilt=(0.05, -0.04)))

    return _p(c, name, build)


def stall(c, variant=0):
    """A market stall: a plank table under a green canvas on poles."""
    name = "Emerald Stall %d" % (variant % 2)

    def build(P, bm):
        P.add("em_wood_dark", lambda: cuboid(bm, (0, 0, 0.9), (3.2, 1.6, 0.2)))
        for sx in (-1, 1):
            for sy in (-1, 1):
                P.add("em_wood_dark", lambda sx=sx, sy=sy: kp._cyl(bm, sx * 1.5, sy * 0.9, -0.2, 2.5, 0.08, 0.08, n=4))
        P.add("em_canvas_green", lambda: cuboid(bm, (0, 0, 2.6), (3.6, 2.4, 0.12), tilt=(0.12 * (1 if variant % 2 else -1), 0.0)))
        for k in range(3):
            P.add("keep_barrel", lambda k=k: cuboid(bm, (-1.0 + k, 0.2, 1.2), (0.6, 0.6, 0.5)))

    return _p(c, name, build)


def plaque(c):
    """The kingdom's sign in a mossy stone frame (over the caverns' mouth)."""
    name = "Emerald Plaque"

    def build(P, bm):
        P.add(MOSS, lambda: cuboid(bm, (0, -0.1, 0), (3.6, 0.3, 3.6)))
        P.add("em_banner", lambda: kp._quad(bm, [(-1.5, 0.08, 1.5), (1.5, 0.08, 1.5), (1.5, 0.08, -1.5), (-1.5, 0.08, -1.5)], both=False))

    return _p(c, name, build, fit=["em_banner"])


def install(town, ip, dp):
    """Swap the Eastern buildings for the kingdom's (call before the scenery is built)."""
    kit.MAT_REMAP.clear()
    kit.MAT_REMAP.update(REMAP)
    kp.use_palette(PALETTE)
    ip.gate = stone_gate
    ip.pavilion = shrine
    ip.stall = stall
    ip.pagoda = lambda c, tiers=3, w=6.0, roof_mat=None: kp.round_tower(c, w * 0.6, 4.5 * tiers + 2.0, True, tiers % 3)
    ip.house = lambda c, variant=0: kp.house(c, variant % 4)
    ip.dragon_statue = lambda c, mat="jade_stone": kp.dragon_statue(c, "keep_ashlar_dark")
    ip.banner_pole = lambda c, mat="banner_royal": kp.banner_pole(c, "keep_banner")
    ip.emblem_plaque = plaque
    dp.fort_tower = lambda c, h=16.0, w=7.0, roof_mat=None: kp.square_tower(c, w, h, False, int(h) % 3)
    dp.fort_wall = lambda c, length=16.0, h=8.0: kp.curtain_wall(c, length, h)
    dp.watchtower = lambda c: kp.round_tower(c, 5.0, 21.0, False, 1)
    # The jungle's air, no villagers, no serpent, no desert dust.
    for name, z in town.ZONES.items():
        if name == "caverns":
            z.update({"fog": "#14261c", "sky": "#7ad0a0", "ground": "#1a2a1a"})
        else:
            z.update({"fog": "#bcd8c4", "sky": "#bcdcd0", "ground": "#4a6a3a"})
    town.ZONES["quarry"]["sound"] = "garden"
    town.dragon = lambda c, sc: None
    first_scenery = town.scenery

    def scenery(c, sc):
        first_scenery(c, sc)
        extras(c, sc, town)

    town.scenery = scenery

    def entities(c, sc):
        town.atmosphere(c, sc)
        from dcanyon_scenery import game_entity

        game_entity(c, "birds", 150.0, 60.0, 110.0, radius=140, count=6, speed=0.14, seed=5, color="#f0f0e0")
        game_entity(c, "birds", -60.0, -40.0, 95.0, radius=90, count=5, speed=0.18, seed=9, color="#e86a3a")
        c.entity("fireflies", rate=18, radius=34)
        for kind, col, step in (("fire", "#ff9a40", 5), ("glow", "#6affa0", 1)):
            for x, y, z in sc.lights.get(kind, [])[::step]:
                game_entity(c, "glow", x, y, z, color=col)

    town.entities = entities


# ------------------------------------------------------------------ the jungle


def extras(c, sc, town):
    L = town.L
    from dcanyon_scenery import clear

    # Glowing crystals along the caverns' walls.
    t0, t1 = sc.tunnel
    s = t0 + 10.0
    k = 0
    while s < t1 - 8.0:
        q = c.at(s)
        side = 1 if k % 2 else -1
        p = q.side(side * (q.w / 2 + 1.6))
        mat = "em_crystal" if k % 3 else "em_crystal_violet"
        sc.put(props.crystals(c, mat), p.x, p.y, q.p.z - 0.3, rnd(k) * 6.28, 1.3, coll="Props", role="visual")
        sc.light("glow", p.x, p.y, q.p.z + 2.0)
        s += 13.0
        k += 1
    # The green dragon on the watchtower, looking out over the canyon.
    tx, ty = L.TOWER
    gz = sc.ground(tx, ty)
    sc.put(kp.great_dragon(c), tx, ty, gz + 20.4, math.atan2(-ty, -tx) - math.pi / 2, 0.95, coll="Landmarks", role="visual")
    # Vines off the bridges' decks.
    for piece in c.pieces:
        if not piece.name.endswith("bridge"):
            continue
        s0, s1 = piece["kp_from"], piece["kp_to"]
        if s1 < s0:
            s1 += c.length
        s = s0 + 5.0
        k = 0
        while s < s1 - 5.0:
            q = c.at(s % c.length)
            for side in (-1, 1):
                if (k + (side > 0)) % 2:
                    continue
                p = q.side(side * (q.w / 2 + 1.4))
                sc.put(props.vine_curtain(c, k % 3, 8.0 + 4 * (k % 2)), p.x, p.y, q.p.z - 1.0, math.atan2(q.t.y, q.t.x), 1.0, coll="Props",
                       role="visual")
            s += 9.0
            k += 1
    # Giant trees, jungle trees and palms on the flats, ferns and big leaves near the
    # roads, clear of everything.
    x0, x1, y0, y1 = L.GRID
    placed = 0
    for i in range(4000):
        if placed > 520:
            break
        x = x0 + rnd(i * 2.7 + 0.3) * (x1 - x0)
        y = y0 + rnd(i * 5.3 + 0.7) * (y1 - y0)
        z = sc.ground(x, y)
        dz = max(abs(sc.ground(x + 3, y) - z), abs(sc.ground(x, y + 3) - z))
        if dz > 1.6:
            continue  # a cliff
        if L.river_d(x, y) < L.RIVER_HW + 3:
            continue
        r = rnd(i * 11.1)
        if r < 0.06:
            if clear(c, x, y, 26.0) and sc.free(x, y, 14.0):
                sc.put(props.giant_tree(c, i % 3), x, y, z - 0.5, rnd(i) * 6.28, 0.8 + 0.4 * rnd(i * 3), coll="Props", role="both")
                sc.footprints.append((x, y, 8.0))
                placed += 1
        elif r < 0.5:
            if clear(c, x, y, 11.0) and sc.free(x, y, 3.0):
                proto = props.palm(c, 9.0, 1.4, i % 3) if L.river_d(x, y) < 40 else props.jungle_tree(c, i % 3)
                sc.put(proto, x, y, z - 0.3, rnd(i) * 6.28, 0.9 + 0.5 * rnd(i * 7), coll="Props", role="both")
                sc.footprints.append((x, y, 1.5))
                placed += 1
        else:
            if clear(c, x, y, 3.5) and sc.free(x, y, 1.5):
                proto = props.fern(c) if r < 0.8 else props.big_leaf_plant(c, i % 3)
                sc.put(proto, x, y, z - 0.1, rnd(i) * 6.28, 0.9 + 0.8 * rnd(i * 13), coll="Props", role="visual")
                placed += 1
