# The mini-games' arenas (Blake, Oct 26: two battle royales like the old kart racers', two
# of our own; Oct 27: rework Balloon Brawl's and Star Fall's arenas ("I can hardly drive
# around", "I can't climb the centre mound"), new games Smugglers' Run and Crumble Rink):
# each an open bowl walled by its landscape, with the things its game needs. Built on
# pocket_kit like the overworld (one pocket, its floor, walls as steep as they're high).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/arena_region.py <bowl|docks|rink|stars>
#
#   bowl   Crater Bowl (Balloon Brawl): a wide, open crater floor to drift round, banked
#          rims, a low island in the middle (gentle slopes all round), a few broken
#          walls and boulders for cover, two jumps on the outer loop
#   docks  Smugglers' Cove (Smugglers' Run): a sandy cove, a crew's dock at each corner,
#          crate stacks to dodge round, where the crates fall in the middle
#   rink   Crumble Rink: a round sheet of ice over a crevasse (the tiles are the game's:
#          src/screens/minigames.ts draws them; the build is the crevasse round it and an
#          invisible floor under the ice)
#   stars  Star Fall (catch the falling stars): a plaza of three terraces with gentle
#          slopes between (no step a kart can't climb), a shallow ring road round it
#
# Oct 29 (Blake: "completely scrap the level layout ... each needs a new cool level with 2
# levels to drive up and down. no stupid mound in the middle that cant be climbed"): Crater
# Bowl, Smugglers' Cove and Star Fall are two-storey arenas. The upper level is a broad
# ring deck on pillars (the route: the road generator's own deck, nothing under it but the
# pillars), open at its edges so you can drive off it; four long ramps climb to it from
# the outer floor and two run down from it to the middle. Under it and round it, the
# floor is flat (banked only at the rim), each arena with its own cover. The game knows
# the deck and the ramps (`deck`, `ramp` entities) for its rivals and its pickups.
#
# The route is the deck's ring (the balloons go round it, and a kart that falls off is put
# back on it); a second route, "ground", runs round the outer floor for the balloons down
# there.

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import lerp, smooth  # noqa: E402
from pocket_kit import Layout  # noqa: E402
from pocket_build import box  # noqa: E402
import region_paint as paint  # noqa: E402
import props  # noqa: E402
import beach_props as bp  # noqa: E402
import canyon_props as cp  # noqa: E402
import keep_props as kp  # noqa: E402

AID = sys.argv[-1]
TRACK_ID = "arena_%s" % AID

SPECS = {
    "bowl": {
        "name": "Crater Bowl",
        "env": "ember_volcano",
        "floor": 2.0,
        "r": 86.0,
        "top": 40.0,
        "mats": (("volcano_slag", "dirt"), ("ember_rock", "wall"), ("basalt_road", "road")),
    },
    "docks": {
        "name": "Smugglers' Cove",
        "env": "coral_cove",
        "floor": 1.5,
        "r": 80.0,
        "top": 30.0,
        "mats": (("beach_sand", "sand"), ("cove_rock", "wall"), ("cove_planks", "road")),
    },
    "rink": {
        "name": "Crumble Rink",
        "env": "aurora_rift",
        # (The crevasse's floor, far under the ice.)
        "floor": -34.0,
        "r": 66.0,
        "top": 40.0,
        "mats": (("cavern_ice", "wall"), ("icefall_rift", "wall"), ("lake_ice", "ice")),
    },
    "stars": {
        "name": "Star Fall",
        "env": "moonstone_kingdom",
        "floor": 2.0,
        "r": 80.0,
        "top": 40.0,
        "mats": (("moon_grass", "grass"), ("moon_rock", "wall"), ("moon_paving", "road")),
    },
}
SP = SPECS[AID]
F, R, TOP = SP["floor"], SP["r"], SP["top"]
RING = R - 22.0  # (the route's ring)
# The two-storey arenas: the deck's radius, its height over the floor, its road's width.
TWO = AID in ("bowl", "docks", "stars")
DECK = {"bowl": (32.0, 5.5), "docks": (30.0, 4.5), "stars": (33.0, 6.0)}.get(AID)
DECK_W = 16.0
if TWO:
    RING = DECK[0]
DECK_Z = F + DECK[1] if TWO else None
# Crumble Rink's ice: its height and radius (the tiles are the game's).
ICE_Z, ICE_R, TILE = 2.0, 40.0, 2.6
if AID == "rink":
    RING = 24.0

ROUTE = [(RING * math.cos(k * math.tau / 16), RING * math.sin(k * math.tau / 16),
          ICE_Z if AID == "rink" else DECK_Z) for k in range(16)]
L = Layout([("floor", "floor", [(0.0, 0.0, R, F)])], TOP, ROUTE, [], roll=1.2, flat=(), mountains=30.0)


def feature(x, y):
    """The arena's own shape over its floor: flat (Blake, Oct 29: "no stupid mound in the
    middle"), banked up at the rim so you can drift round it."""
    d = math.hypot(x, y)
    if AID in ("bowl", "docks", "stars"):
        return 4.0 * smooth((d - (R - 16.0)) / 14.0)
    return 0.0


def natural(x, y):
    return L.natural(x, y) + feature(x, y)


def classify(c, n, info):
    ground, cliff, _ = SP["mats"]
    if n.z < 0.62:
        return cliff
    if AID == "docks" and math.hypot(c.x, c.y) > R - 6:
        return ("cove_wet_sand", "water")
    return ground


def main():
    c = kit.Course(TRACK_ID, SP["name"], SP["env"])
    c.route(L.route_points(), width=DECK_W - 2.0 if TWO else 14.0, bank=0.0)
    ground_m, cliff_m, road_m = SP["mats"]
    c.kinds = {"floor": {"mat": road_m[0], "shoulder": 1.0, "shoulder_mat": ground_m}}
    if TWO:
        # The upper level: the road generator's deck, up on pillars, open at its edges.
        c.kinds = {"floor": {"mat": road_m[0], "surface": "road", "shoulder": 1.0, "shoulder_mat": (road_m[0], "road"),
                             "deck": 1.4, "deck_mat": cliff_m, "ground": False}}
    if TWO:
        # The upper level: the whole ring a deck.
        c.roads(kit.plan(c, [], "floor", max_len=60.0))
    elif AID != "rink":
        c.roads(kit.plan(c, [(0.0, c.length, None)], "floor", max_len=160.0))
    X0, X1, Y0, Y1 = -200, 200, -200, 200
    ter = c.terrain(SP["name"], X0, X1, Y0, Y1, 2.5, natural, classify, near=4.0, fade=8.0)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 2.5, lambda x, y: natural(x, y) - 0.5, c.lib(*ground_m))

    def ground(x, y):
        if AID == "rink" and math.hypot(x, y) < ICE_R:
            return ICE_Z
        z = c.ground_z(x, y, [ter])
        return natural(x, y) if z is None else z

    taken = paint.Taken([(0.0, 0.0, 30.0)])
    if TWO:
        two_levels(c, ground, taken)
    # Where the karts start: round the ring, facing in (on the outer floor, two-storey).
    for k in range(8):
        a = k * math.tau / 8 + 0.2 + (math.pi / 8 if TWO else 0.0)
        sr = 18.0 if AID == "rink" else (RING + DECK_W / 2 + 12.0 if TWO else RING - 6.0)
        x, y = sr * math.cos(a), sr * math.sin(a)
        g = c.game(x, y, ground(x, y))
        c.entity("arena_spawn", x=round(g[0], 2), z=round(g[2], 2), heading=round(math.atan2(-x, y), 3), index=k)
    # Item balloons round the ring and nearer the middle.
    n = 0
    for k in range(10 if not TWO else 6):
        c.balloon(c.length * (k + 0.5) / (10 if not TWO else 6), (k % 3 - 1) * 4.0,
                  ("red", "blue", "green", "yellow", "rainbow")[k % 5])
        n += 1
    if TWO:
        # Down on the floor too: round the outer floor (its own route), and in the middle.
        rg = (RING + DECK_W / 2 + R - 16.0) / 2
        pts = [(rg * math.cos(k * math.tau / 24), rg * math.sin(k * math.tau / 24), ground(rg * math.cos(k * math.tau / 24),
                                                                                         rg * math.sin(k * math.tau / 24)) + 0.3)
               for k in range(24)]
        c.path_curve("ground", pts)
        for k in range(8):
            c.entities.append({"id": "bal_g%02d" % k, "type": "balloon", "route": "ground", "at": round(math.tau * rg * (k + 0.5) / 8, 1),
                               "across": 0.0, "color": ("red", "blue", "green", "yellow", "rainbow")[(k + 2) % 5]})
    BUILD[AID](c, ground, taken)
    c.entity("arena", game={"bowl": "balloons", "docks": "smugglers", "rink": "crumble", "stars": "stars"}[AID],
             radius=round(R - 8.0, 1))
    kit.paint.shade_roads(c.pieces, 0.3)
    c.checkpoints(height=12.0)
    c.finish(extra={"race": {"laps": 1}, "arena": True})
    if AID in LOOKS:
        path = os.path.join(kit.TRACKS_DIR, TRACK_ID, "look.json")
        with open(path, encoding="utf-8") as f:
            look = json.load(f)
        for k, v in LOOKS[AID].items():
            look[k] = v
        with open(path, "w", encoding="utf-8") as f:
            json.dump(look, f, indent=2)
            f.write("\n")


# Each arena's own sky and light where its kingdom's is wrong for it (Blake, Oct 29: the
# Crater Bowl was too dark: now a volcano at dusk, glowing orange, the floor lit warm).
LOOKS = {
    "bowl": {
        "sky": "#ff8a4a",
        "fog": {"enabled": True, "color": "#b0563a", "near": 140, "far": 900},
        "sun": {"color": "#ffd2a0", "intensity": 2.5, "direction": [0.35, 0.62, 0.55]},
        "ambient": {"sky": "#ffb08a", "ground": "#6a3020", "intensity": 1.55},
        "skyDome": {
            "top": "#2a1236",
            "horizon": "#ff8a46",
            "bottom": "#7a2a1a",
            "sun": {"color": "#ffe0a8", "size": 14, "glow": "#ff9a4a", "elevation": 16},
            "clouds": {"count": 18, "color": "#5a3040", "shade": "#2a1420", "seed": 311, "low": 4, "high": 18,
                       "drift": 0.004},
            "hills": {"color": "#2a1612", "far": "#7a3a2a", "height": 14, "seed": 313, "layers": 3},
        },
    },
}


def two_levels(c, ground, taken):
    """The upper level's pillars and ramps (the deck itself is the route's road): four
    long ramps up to it from the outer floor (on the four sides), two down from it into
    the middle (between them), pillars under it; and the `deck` and `ramp` entities."""
    rd, h = DECK
    ground_m, cliff_m, road_m = SP["mats"]
    half = DECK_W / 2 + 1.0
    zt = DECK_Z
    # Pillars, clear of the ramps.
    for k in range(16):
        a = k * math.tau / 16 + math.tau / 32
        x, y = rd * math.cos(a), rd * math.sin(a)
        box(c, "Pillar %d" % k, x, y, 1.1, 1.1, F - 1.0, zt - 1.2, cliff_m, rot=a)
        taken.add(x, y, 3.0)
    ramps = []
    # Up from the outer floor: radial, the high end at the deck's outer edge.
    for k in range(4):
        a = k * math.tau / 4
        Lr = 26.0
        r0 = rd + half - 0.8
        cx, cy = (r0 + Lr / 2) * math.cos(a), (r0 + Lr / 2) * math.sin(a)
        z0 = ground(cx, cy)
        ramp(c, "Ramp Up %d" % k, cx, cy, a + math.pi, Lr, 11.0, zt - z0 + 0.04, road_m, z0)
        ramps.append(((r0 + Lr) * math.cos(a), (r0 + Lr) * math.sin(a), r0 * math.cos(a), r0 * math.sin(a)))
        taken.add(cx, cy, 13.0)
    # Down into the middle: radial, the high end at the deck's inner edge.
    for k in range(2):
        a = k * math.pi + math.pi / 4
        Lr = 20.0
        r0 = rd - half + 0.8
        cx, cy = (r0 - Lr / 2) * math.cos(a), (r0 - Lr / 2) * math.sin(a)
        z0 = ground(cx, cy)
        ramp(c, "Ramp Down %d" % k, cx, cy, a, Lr, 10.0, zt - z0 + 0.04, road_m, z0)
        ramps.append(((r0 - Lr) * math.cos(a), (r0 - Lr) * math.sin(a), r0 * math.cos(a), r0 * math.sin(a)))
        taken.add(cx, cy, 11.0)
    g = c.game(0.0, 0.0, zt)
    c.entity("deck", r=rd, w=DECK_W, y=round(zt, 2))
    for k, (bx, by, tx, ty) in enumerate(ramps):
        b = c.game(bx, by, ground(bx, by))
        t = c.game(tx, ty, zt)
        c.entity("ramp", x=b[0], z=b[2], tx=t[0], tz=t[2], index=k)
    del g


def ramp(c, name, x, y, rot, length, width, rise, mat, z0):
    """A wedge ramp: up `rise` over `length` along local +x."""
    bm = kit.bmesh.new()
    ca, sa = math.cos(rot), math.sin(rot)

    def at(lx, ly, z):
        return bm.verts.new((x + lx * ca - ly * sa, y + lx * sa + ly * ca, z))

    a = [at(-length / 2, -width / 2, z0 - 0.5), at(length / 2, -width / 2, z0 - 0.5), at(length / 2, width / 2, z0 - 0.5),
         at(-length / 2, width / 2, z0 - 0.5)]
    b = [at(-length / 2, -width / 2, z0 - 0.02), at(length / 2, -width / 2, z0 + rise), at(length / 2, width / 2, z0 + rise),
         at(-length / 2, width / 2, z0 - 0.02)]
    for f in ((0, 3, 2, 1),):
        bm.faces.new([a[i] for i in f])
    bm.faces.new([b[0], b[1], b[2], b[3]])
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh = kit.bmesh
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = c.mesh_object(name, bm, "Props", "both")
    c.assign(ob, c.lib(*mat))
    return ob


def build_bowl(c, ground, taken):
    """Cover on the outer floor between the ramps (broken walls and boulders, spaced so
    there's room to drive round each), a ring of low basalt stumps in the middle, steam
    vents and a bubbling pit in the very middle."""
    for k in range(4):
        a = k * math.tau / 4 + math.pi / 4
        for j, rr in enumerate((50.0, 62.0)):
            x, y = rr * math.cos(a + (j - 0.5) * 0.18), rr * math.sin(a + (j - 0.5) * 0.18)
            if j == 0:
                for w in range(3):
                    t = (w - 1) * 3.4
                    hh = (3.6, 2.6, 1.8)[w]
                    box(c, "Broken Wall %d %d" % (k, w), x - math.sin(a) * t, y + math.cos(a) * t, 1.6, 3.2, F - 0.5,
                        ground(x, y) + hh, ("obsidian_cliff", "wall"), rot=a)
            else:
                c.assign(c.rock_mass("Boulder %d" % k, x, y, 3.2, 2.6, ground(x, y) + 3.4, z0=F - 2.0, n=10, seed=k + 2),
                         c.lib("obsidian_cliff", "wall"))
            taken.add(x, y, 9.0)
    for k in range(3):
        a = k * math.tau / 3 + 1.2
        x, y = 11.0 * math.cos(a), 11.0 * math.sin(a)
        box(c, "Stump %d" % k, x, y, 1.4, 1.4, F - 0.5, ground(x, y) + 1.4, ("obsidian_cliff", "wall"), rot=a)
    for k in range(5):
        a = k * math.tau / 5 + 0.3
        x, y = 6.0 * math.cos(a), 6.0 * math.sin(a)
        g = c.game(x, y, ground(x, y) + 0.3)
        c.entity("steam", x=g[0], y=g[1], z=g[2])
    g = c.game(0.0, 0.0, ground(0.0, 0.0) + 1.0)
    c.entity("bubbles", x=g[0], y=g[1], z=g[2], r=3.0, molten=True)
    paint.scatter(c, props.basalt_columns(c), 10, R - 6, lambda x, y: math.hypot(x, y) > R - 14, ground, taken, 4,
                  room=6.0, road_margin=-60.0)


def build_docks(c, ground, taken):
    """A crew's dock in each corner (four players: red, blue, green, yellow): a plank
    landing flush with the sand, mooring posts, a flag in the crew's colour and crates
    stacked behind; crate stacks round the middle to dodge round; where the crates fall."""
    colors = ("red", "blue", "green", "yellow")
    flags = {"red": "party_red", "blue": "party_blue", "green": "party_teal", "yellow": "party_yellow"}
    for k, col in enumerate(colors):
        a = k * math.tau / 4 + math.pi / 4
        x, y = 50.0 * math.cos(a), 50.0 * math.sin(a)
        z = ground(x, y)
        box(c, "Dock %s Deck" % col, x, y, 12.0, 10.0, z - 0.3, z + 0.06, ("cove_planks", "road"), rot=a, role="visual")
        for j in range(6):
            b = a + (j - 2.5) * 0.36
            px, py = x + 8.0 * math.cos(b), y + 8.0 * math.sin(b)
            box(c, "Dock %s Post %d" % (col, j), px, py, 0.5, 0.5, z - 0.5, z + 1.6, ("cove_post", "wall"))
        fx, fy = x + 9.5 * math.cos(a), y + 9.5 * math.sin(a)
        box(c, "Dock %s Flagpole" % col, fx, fy, 0.3, 0.3, z, z + 7.0, ("cove_post", "wall"))
        box(c, "Dock %s Flag" % col, fx - 1.3 * math.sin(a), fy + 1.3 * math.cos(a), 0.12, 2.4, z + 5.0, z + 6.6,
            (flags[col], "wall"), rot=a, role="visual")
        for j in (-1, 1):
            sx, sy = x + 11.0 * math.cos(a) + j * 6.0 * math.sin(a), y + 11.0 * math.sin(a) - j * 6.0 * math.cos(a)
            box(c, "Dock %s Crates %d" % (col, j), sx, sy, 2.2, 2.2, z - 0.2, z + 2.0, ("weathered_timber", "wall"), rot=a + 0.3 * j)
        g = c.game(x, y, z)
        c.entity("dock", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), color=col, index=k)
        taken.add(x, y, 14.0)
    # Stacks round the middle (cover, and something to cut round), inside the deck's ring.
    for k in range(4):
        a = k * math.tau / 4 + math.pi / 4 + 0.4
        x, y = 12.0 * math.cos(a), 12.0 * math.sin(a)
        z = ground(x, y)
        box(c, "Stack %d" % k, x, y, 2.2, 2.2, z - 0.3, z + 2.2, ("weathered_timber", "wall"), rot=a + 0.4)
        taken.add(x, y, 6.0)
    g = c.game(0.0, 0.0, ground(0.0, 0.0))
    # (Where the crates fall: the middle, inside the deck's ring, on the floor.)
    c.entity("crate_spawn", x=g[0], z=g[2], y=g[1], r=16.0)
    for v in range(2):
        paint.scatter(c, bp.coconut_palm(c, v), 10, R - 6, lambda x, y: math.hypot(x, y) > R - 14, ground, taken, 10 + v,
                      room=6.0, road_margin=-60.0, trunk=(0.6, 7.0))


def build_rink(c, ground, taken):
    """The ice's invisible floor (the karts drive on it; what they see is the game's
    tiles), a rim of ice boulders round the crevasse's lip, icicles down its walls."""
    c.disc("Ice Floor", 0.0, 0.0, ICE_R + 0.5, ICE_Z, c.lib("lake_ice", "ice"), coll="Props", role="collision", n=64)
    for k in range(14):
        a = k * math.tau / 14 + 0.1
        rr = R - 4.0
        x, y = rr * math.cos(a), rr * math.sin(a)
        c.assign(c.rock_mass("Lip Boulder %d" % k, x, y, 4.0, 3.0, ground(x, y) + 5.0 + (k % 3) * 2.0, z0=ground(x, y) - 3.0,
                             n=10, seed=k + 5), c.lib("glacier_ice", "wall"))
    g = c.game(0.0, 0.0, ICE_Z)
    c.entity("rink", x=g[0], z=g[2], y=g[1], r=ICE_R, tile=TILE)
    c.entity("fireflies", rate=20, radius=40)


def build_stars(c, ground, taken):
    """Lanterns round the terraces (their slopes are gentle all round: no ramps needed)."""
    for k in range(12):
        a = k * math.tau / 12 + 0.26
        x, y = 56.0 * math.cos(a), 56.0 * math.sin(a)
        g = c.game(x, y, ground(x, y) + 3.0)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
    c.entity("star_field", radius=R - 12.0)
    c.entity("fireflies", rate=30, radius=36)


BUILD = {"bowl": build_bowl, "docks": build_docks, "rink": build_rink, "stars": build_stars}

if __name__ == "__main__":
    main()
