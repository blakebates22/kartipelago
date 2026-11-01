# The mini-games' arenas (Blake, Oct 26: two battle royales like the old kart racers', two
# of our own; Oct 27: rework Balloon Brawl's and Star Fall's arenas ("I can hardly drive
# around", "I can't climb the centre mound"), new games Smugglers' Run and Crumble Rink):
# each an open bowl walled by its landscape, with the things its game needs. Built on
# pocket_kit like the overworld (one pocket, its floor, walls as steep as they're high).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/arena_region.py <bowl|docks|rink|stars>
#
#   bowl   Caldera Keep (Caldera Brawl): a castle in a crater, a lava moat round it (Oct
#          31, Blake picked "A": three heights to fight on). The outer bailey, the round
#          curtain wall's walk (four ramps up its outer face, two up its inner), four
#          gates through it into the courtyard, the keep in the middle (a tunnel through
#          it, its roof the high ground, reached by two bridges off the walk)
#   docks  Smugglers' Cove (Smugglers' Run): a sandy cove, a crew's dock at each corner,
#          crate stacks to dodge round, where the crates fall in the middle
#   rink   The Cutting Pond (Crumble Rink; Oct 31, Blake picked "A"): the snow kingdom's
#          ice harvesters' pond, cut into square blocks (the game's: src/screens/
#          minigames.ts draws them; the build is an invisible floor under them, the dark
#          water, the snowbanks round it), the derrick on its crib in the middle lifting
#          runs of blocks out, the yard round it (the ice house, sledges, the brazier)
#   stars  Meteor Crater (Star Fall; Oct 31, Blake picked "B": "an exciting level with
#          precision driving", matching the desert it's played in): the desert's meteor
#          crater at dusk, terraced down to its floor, each terrace a ring road, narrow
#          switchback ramps between them (a lane beside each, a drop off its side), a
#          thin ledge round the rim, the meteorite in the middle; the stars land on the
#          terraces, the gold ones in the hard places (the rim, the floor, the ramps' tops)
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
        "name": "Caldera Keep",
        "env": "ember_volcano",
        "floor": 2.0,
        "r": 86.0,
        "top": 40.0,
        # (Scorched ground, not slag: only the moat should look like lava.)
        "mats": (("scorched_ground", "dirt"), ("ember_rock", "wall"), ("basalt_road", "road")),
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
        "name": "The Cutting Pond",
        "env": "summit_pass",
        "floor": 2.6,
        "r": 74.0,
        "top": 34.0,
        "mats": (("snow_ground", "packed_snow"), ("summit_cliff", "wall"), ("lake_ice", "ice")),
    },
    "stars": {
        "name": "Meteor Crater",
        "env": "canyon_dash",
        "floor": 2.0,
        "r": 132.0,
        "top": 46.0,
        "mats": (("red_sand", "loose_sand"), ("strata_purple", "wall"), ("dash_road", "road")),
    },
}
SP = SPECS[AID]
F, R, TOP = SP["floor"], SP["r"], SP["top"]
RING = R - 22.0  # (the route's ring)
# The two-storey arenas: the deck's radius, its height over the floor, its road's width.
TWO = AID in ("bowl", "docks")
DECK = {"bowl": (40.0, 6.0), "docks": (30.0, 4.5)}.get(AID)
DECK_W = 12.0 if AID == "bowl" else 16.0
if TWO:
    RING = DECK[0]
DECK_Z = F + DECK[1] if TWO else None
# Crumble Rink's ice: its height and radius (the tiles are the game's); the Cutting Pond's
# blocks a side, the derrick's crib (blocks out from the middle each way).
ICE_Z, ICE_R, TILE = 2.0, 40.0, 3.6
POND_N, POND_ISLAND = 17, 1.5
POND_H = POND_N * TILE / 2
if AID == "rink":
    RING = 24.0

# Meteor Crater's terraces, from the floor up to the rim: (inner radius, outer, height).
# The ramps between them run along each terrace's outer RAMP_W metres (and up over the
# riser): (the lower terrace, the ramp's middle in degrees, rising anticlockwise?).
TIERS = [(0.0, 18.0, 2.0), (21.0, 34.0, 7.5), (37.0, 50.0, 13.0), (53.0, 66.0, 18.5), (69.0, 75.0, 24.0)]
RAMPS = [(0, 30.0, True), (0, 210.0, True), (1, 120.0, False), (1, 300.0, False), (2, 75.0, True), (2, 255.0, True),
         (3, 165.0, False), (3, 345.0, False)]
RAMP_W, RAMP_L = 6.0, 28.0
METEOR_R = 5.0
if AID == "stars":
    RING = (TIERS[2][0] + TIERS[2][1] - RAMP_W) / 2  # (the route: round the middle terrace's lane)


def lane_r(i):
    """The middle of a terrace's lane (beside its ramps up)."""
    r0, r1, _ = TIERS[i]
    if i == 0:
        r0 = METEOR_R + 1.0
    return (r0 + (r1 - RAMP_W if i < len(TIERS) - 1 else r1)) / 2


def ramp_span(k):
    """A ramp's band (radii), its start and end angles (from the foot up) and heights."""
    lo, mid, ccw = RAMPS[k]
    r0, r1 = TIERS[lo][1] - RAMP_W, TIERS[lo + 1][0] + 0.5
    rm = (r0 + r1) / 2
    half = RAMP_L / 2 / rm
    a = math.radians(mid)
    a0, a1 = (a - half, a + half) if ccw else (a + half, a - half)
    return r0, r1, a0, a1, TIERS[lo][2], TIERS[lo + 1][2]


def crater_profile(d):
    """The crater's height at d from its middle (terraces, risers, then the flank out)."""
    for (ra, rb, za), (rc, _rd, zc) in zip(TIERS, TIERS[1:]):
        if d <= rb:
            return za
        if d < rc:
            return lerp(za, zc, smooth((d - rb) / (rc - rb)))
    rim_out, rim_z = TIERS[-1][1], TIERS[-1][2]
    if d < rim_out + 2.0:
        return lerp(rim_z, rim_z - 6.0, smooth((d - rim_out) / 2.0))
    return lerp(rim_z - 6.0, F + 2.0, min(1.0, (d - rim_out - 2.0) / 30.0))


def in_ramp(x, y):
    """(k, t) for the ramp (x, y)'s on, t from its foot (0) to its top (1); or None."""
    d = math.hypot(x, y)
    a = math.atan2(y, x)
    for k in range(len(RAMPS)):
        r0, r1, a0, a1, z0, z1 = ramp_span(k)
        if not (r0 <= d <= r1):
            continue
        t = math.atan2(math.sin(a - a0), math.cos(a - a0)) / (a1 - a0)
        if 0.0 <= t <= 1.0:
            return k, t
    return None


def crater_z(x, y):
    d = math.hypot(x, y)
    z = crater_profile(d)
    rp = in_ramp(x, y)
    if rp:
        _r0, _r1, _a0, _a1, z0, z1 = ramp_span(rp[0])
        z = lerp(z0, z1, rp[1])
    # Out past the flank, the desert (the pocket's own, its mesas round it).
    out = L.natural(x, y) + 2.0
    return lerp(z, out, smooth((d - 100.0) / 14.0))


ROUTE = [(RING * math.cos(k * math.tau / 16), RING * math.sin(k * math.tau / 16),
          ICE_Z if AID == "rink" else (TIERS[2][2] if AID == "stars" else DECK_Z)) for k in range(16)]
L = Layout([("floor", "floor", [(0.0, 0.0, R, F)])], TOP, ROUTE, [], roll=1.2, flat=(), mountains=30.0)


MOAT = (72.0, 80.0)  # Caldera Keep's lava moat (inner and outer radius)


def feature(x, y):
    """The arena's own shape over its floor: flat (Blake, Oct 29: "no stupid mound in the
    middle"), banked up at the rim so you can drift round it."""
    d = math.hypot(x, y)
    if AID == "bowl":
        # The lava moat round the bailey (MOAT), then the crater's banked wall.
        m0, m1 = MOAT
        return -1.6 * smooth((d - m0) / 1.5) * smooth((m1 - d) / 1.5) + 5.0 * smooth((d - m1 - 1.0) / 6.0)
    if AID == "docks":
        return 4.0 * smooth((d - (R - 16.0)) / 14.0)
    if AID == "rink":
        # The pond's bed, dug down under the ice; its snowbanks round it.
        e = max(abs(x), abs(y)) - POND_H
        if e < 0.6:
            return ICE_Z - 3.0 - F
        return 1.4 * smooth((e - 0.6) / 1.0) - 1.0 * smooth((e - 4.0) / 3.0)
    return 0.0


def natural(x, y):
    if AID == "stars":
        return crater_z(x, y)
    return L.natural(x, y) + feature(x, y)


def classify(c, n, info):
    ground, cliff, _ = SP["mats"]
    if AID == "stars":
        # Like the desert's own crater: purple-banded walls, slickrock terraces, talus
        # on the flank, red sand out round it; the ramps paler (so you can see them).
        d = math.hypot(c.x, c.y)
        if n.z < 0.62:
            if d < 100.0:
                return ("strata_purple", "wall") if int(c.z / 4.0) % 2 else ("strata_rust", "wall")
            return (("strata_red", "strata_cream", "strata_orange")[int(c.z / 9.0) % 3], "wall")
        if d < TIERS[-1][1] + 0.5:
            return ("dash_shoulder", "dirt") if in_ramp(c.x, c.y) else ("slickrock", "dirt")
        if d < 100.0:
            return ("talus", "dirt")
        return ground
    if n.z < 0.62:
        return cliff
    if AID == "docks" and math.hypot(c.x, c.y) > R - 6:
        return ("cove_wet_sand", "water")
    if AID == "bowl" and MOAT[0] - 0.5 < math.hypot(c.x, c.y) < MOAT[1] + 0.5 and c.z < F - 0.3:
        return ("volcano_lava", "lava")
    if AID == "bowl" and math.hypot(c.x, c.y) < DECK[0] - DECK_W / 2 + 0.5:
        return ("basalt_road", "road")  # (the courtyard's paved)
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
    elif AID not in ("rink", "stars"):
        c.roads(kit.plan(c, [(0.0, c.length, None)], "floor", max_len=160.0))
    X0, X1, Y0, Y1 = (-160, 160, -160, 160) if AID == "stars" else (-200, 200, -200, 200)
    if AID == "stars":
        # (Finer, its terraces' edges sharp, the risers' bands cut level.)
        ter = c.terrain(SP["name"], X0, X1, Y0, Y1, 1.25, natural, classify, near=4.0, fade=8.0,
                        cut_z=tuple(t[2] - 2.0 for t in TIERS[1:]))
    else:
        ter = c.terrain(SP["name"], X0, X1, Y0, Y1, 2.5, natural, classify, near=4.0, fade=8.0)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 2.5, lambda x, y: natural(x, y) - 0.5, c.lib(*ground_m))

    def ground(x, y):
        if AID == "rink" and max(abs(x), abs(y)) < POND_H:
            return ICE_Z
        z = c.ground_z(x, y, [ter])
        return natural(x, y) if z is None else z

    taken = paint.Taken([(0.0, 0.0, 30.0)])
    if AID == "bowl":
        keep(c, ground, taken)
    elif TWO:
        two_levels(c, ground, taken)
    # Where the karts start: round the ring, facing in (on the outer floor, two-storey).
    for k in range(8):
        a = k * math.tau / 8 + 0.2 + (math.pi / 8 if TWO else 0.0)
        if AID == "bowl":
            a = k * math.tau / 8 + math.pi / 8  # (clear of the gates' towers)
        if AID == "stars":
            a = k * math.tau / 8 + math.radians(10.0)
        sr = 18.0 if AID == "rink" else (RING + DECK_W / 2 + 12.0 if TWO else (RING if AID == "stars" else RING - 6.0))
        x, y = sr * math.cos(a), sr * math.sin(a)
        g = c.game(x, y, ground(x, y))
        # Facing in; in Caldera Keep, round the bailey (anticlockwise), not at the wall.
        hd = math.atan2(-math.sin(a), -math.cos(a)) if AID in ("bowl", "stars") else math.atan2(-x, y)
        c.entity("arena_spawn", x=round(g[0], 2), z=round(g[2], 2), heading=round(hd, 3), index=k)
    # Item balloons round the ring and nearer the middle.
    n = 0
    for k in range(10 if not TWO else 6):
        if AID == "rink" and k >= 8:
            break
        at = c.length * (k + 0.5) / (10 if not TWO else 6)
        if AID == "rink":
            at = c.length * ((k + 0.5) / 8 + 0.2 / math.tau)  # (between the starts, not in front of them)
        c.balloon(at, (k % 3 - 1) * (2.0 if AID == "stars" else 4.0),
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
    c.entity("arena", game={"bowl": "brawl", "docks": "smugglers", "rink": "crumble", "stars": "stars"}[AID],
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
    # The Cutting Pond: the snow kingdom's own sky (snow_region's look).
    "rink": {
        "theme": "summit_pass",
        "sky": "#5ab8ff",
        "fog": {"enabled": True, "color": "#d4eeff", "near": 200, "far": 1100},
        "sun": {"color": "#fff4dc", "intensity": 2.7, "direction": [0.42, 0.74, 0.52]},
        "ambient": {"sky": "#eaf6ff", "ground": "#8ea2bc", "intensity": 1.35},
        "skyDome": {
            "top": "#1c7ee8",
            "horizon": "#c8ecff",
            "bottom": "#e4f4ff",
            "sun": {"color": "#fffbe6", "size": 8, "glow": "#fff0b0", "elevation": 32},
            "clouds": {"count": 30, "color": "#ffffff", "shade": "#d2e6fa", "seed": 61, "low": 8, "high": 26, "drift": 0.005},
            "hills": {"color": "#9eb8de", "far": "#d2e4f8", "height": 16, "seed": 67, "layers": 3},
        },
    },
    # Meteor Crater at dusk (the stars come out): the desert's own sky gone indigo, a
    # rising moon, the mesas dark against the last light.
    "stars": {
        "theme": "canyon_dash",
        "sky": "#2a2a5e",
        "fog": {"enabled": True, "color": "#4a3a6a", "near": 260, "far": 1600},
        "sun": {"color": "#d8d0ff", "intensity": 1.9, "direction": [-0.5, 0.6, 0.55]},
        "ambient": {"sky": "#a0a0e0", "ground": "#6a3a40", "intensity": 1.35},
        "skyDome": {
            "top": "#0e1034",
            "horizon": "#b0607a",
            "bottom": "#4a2a4a",
            "sun": {"color": "#f4f0ff", "size": 20, "glow": "#8a8ad8", "elevation": 24, "face": "moon"},
            "clouds": {"count": 10, "color": "#6a4a80", "shade": "#2a2040", "seed": 731, "low": 4, "high": 20, "drift": 0.003},
            "hills": {"color": "#2a1a2a", "far": "#6a3a5a", "height": 6, "seed": 733, "layers": 3, "style": "mesas"},
            "stars": {"count": 260, "color": "#f0f0ff", "seed": 735, "low": 8},
        },
    },
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


def ring_wall(c, name, r0, r1, z0, z1, skip, mat, n=96):
    """A ring of wall between radii r0 and r1, z0 to z1, but where skip(angle)."""
    bm = kit.bmesh.new()
    for k in range(n):
        a0, a1 = k * math.tau / n, (k + 1) * math.tau / n
        if skip((a0 + a1) / 2):
            continue
        vs = []
        for r in (r0, r1):
            for a in (a0, a1):
                for z in (z0, z1):
                    vs.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        # (vs: [r0 a0 lo, r0 a0 hi, r0 a1 lo, r0 a1 hi, r1 a0 lo, r1 a0 hi, r1 a1 lo, r1 a1 hi])
        for f in ((0, 2, 3, 1), (4, 5, 7, 6), (1, 3, 7, 5), (0, 4, 6, 2), (0, 1, 5, 4), (2, 6, 7, 3)):
            bm.faces.new([vs[i] for i in f])
    kit.bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.01)
    kit.bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    c.assign(c.mesh_object(name, bm, "Props", "both"), c.lib(*mat))


def keep(c, ground, taken):
    """Caldera Keep's castle (Blake, Oct 31: "A"): the round curtain wall under the walk
    (the route's deck: solid stone under it, four gates through it), battlements along
    the walk's outer edge, a pair of towers flanking each gate, tangential ramps up the
    wall's faces (four outside, two inside), the keep in the middle (a tunnel through it
    east to west, its roof the high ground, bridges to it off the walk). And its `nav`:
    the rivals' map of the levels (nodes, and the links you can drive between)."""
    rd, h = DECK
    zt = DECK_Z
    wi, wo = rd - DECK_W / 2 + 0.6, rd + DECK_W / 2 - 0.6  # the wall's faces (the walk overhangs them)
    stone = ("basalt_block", "wall")
    gates = [k * math.tau / 4 + math.pi / 4 for k in range(4)]
    gate_half = math.radians(7.5)
    near_gate = lambda a: min(abs(math.atan2(math.sin(a - g), math.cos(a - g))) for g in gates)  # noqa: E731
    # The curtain wall: solid from the floor to under the walk, but at the gates.
    ring_wall(c, "Curtain Wall", wi, wo, F - 1.0, zt - 1.35, lambda a: near_gate(a) < gate_half, stone)
    # The moat's parapet: a low stone rail round its inner edge, broken in eight places
    # (where you can be knocked in).
    m0 = MOAT[0] - 1.2
    ring_wall(c, "Moat Parapet", m0 - 0.5, m0 + 0.5, F - 1.0, F + 0.9,
              lambda a: (a * 8 / math.tau + 0.5) % 1.0 < 0.14, ("basalt_block", "wall"), n=160)
    # The gates: their arches' piers either side, and a pair of towers out front.
    for k, g in enumerate(gates):
        for sd in (-1, 1):
            a = g + sd * (gate_half + math.radians(1.5))
            x, y = rd * math.cos(a), rd * math.sin(a)
            box(c, "Gate Pier %d %d" % (k, sd), x, y, DECK_W / 2 - 0.4, 0.9, F - 1.0, zt - 1.3, ("basalt_carved", "wall"), rot=a)
            a = g + sd * math.radians(11.0)
            x, y = (wo + 3.4) * math.cos(a), (wo + 3.4) * math.sin(a)
            bm = kit.bmesh.new()
            props.tube(bm, [(x, y, F - 1.0), (x, y, zt + 5.0)], [3.2, 2.9], n=10)
            ob = c.mesh_object("Gate Tower %d %d" % (k, sd), bm, "Props", "both")
            c.assign(ob, c.lib(*stone))
            bm = kit.bmesh.new()
            props.tube(bm, [(x, y, zt + 5.0), (x, y, zt + 10.5)], [3.7, 0.05], n=10)
            c.assign(c.mesh_object("Gate Tower Roof %d %d" % (k, sd), bm, "Props", "visual"), c.lib("obsidian", "wall"))
            g2 = c.game(x, y, zt + 5.6)
            c.entity("lantern", x=g2[0], y=g2[1], z=g2[2])
            taken.add(x, y, 5.0)
    # The ramps: tangential, along the wall's faces, each up to the walk (a chord of a
    # circle, its top end touching the walk's edge). (centre angle, outside?, rising
    # anticlockwise?)
    nodes, links = [], []

    def node(x, y, z):
        nodes.append((x, y, z))
        return len(nodes) - 1

    def link(a, b):
        links.append((a, b))

    def ring(r, z, m, phase=0.0):
        ids = [node(r * math.cos(phase + k * math.tau / m), r * math.sin(phase + k * math.tau / m), z) for k in range(m)]
        for k in range(m):
            link(ids[k], ids[(k + 1) % m])
        return ids

    def nearest(ids, x, y):
        return min(ids, key=lambda i: math.hypot(nodes[i][0] - x, nodes[i][1] - y))

    W = ring(rd, zt, 16)  # the walk
    B = ring(58.0, F, 16)  # the bailey
    C = ring(22.0, F, 8)  # the courtyard
    Lr = 22.0
    for k, (ca, outside, ccw) in enumerate(((0.0, True, True), (math.pi / 2, True, False), (math.pi, True, True),
                                            (3 * math.pi / 2, True, False), (math.pi / 2, False, True),
                                            (3 * math.pi / 2, False, False))):
        width = 9.0
        re = (rd + DECK_W / 2 + 4.7) if outside else (rd - DECK_W / 2 - 4.0)
        half = math.asin(Lr / 2 / re)
        sg = 1 if ccw else -1
        a0, a1 = ca - sg * half, ca + sg * half
        p0 = (re * math.cos(a0), re * math.sin(a0))
        p1 = (re * math.cos(a1), re * math.sin(a1))
        cx, cy = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        rot = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        z0 = ground(cx, cy)
        ramp(c, "Ramp %d" % k, cx, cy, rot, Lr, width, zt - z0 + 0.04, ("basalt_road", "road"), z0)
        taken.add(cx, cy, 12.0)
        ux, uy = math.cos(rot), math.sin(rot)
        ra = node(p0[0] - ux * 7.0, p0[1] - uy * 7.0, F)
        rf = node(p0[0] + ux * 2.0, p0[1] + uy * 2.0, F + 0.5)
        rt = node(p1[0] - ux * 2.0, p1[1] - uy * 2.0, zt - 0.5)
        wl = node(rd * math.cos(a1), rd * math.sin(a1), zt)
        link(nearest(B if outside else C, *nodes[ra][:2]), ra)
        link(ra, rf)
        link(rf, rt)
        link(rt, wl)
        link(wl, nearest(W, *nodes[wl][:2]))
    # The gates: bailey to courtyard.
    for g in gates:
        link(nearest(B, 58.0 * math.cos(g), 58.0 * math.sin(g)), nearest(C, 22.0 * math.cos(g), 22.0 * math.sin(g)))
    # Battlements along the walk's outer edge (but where the ramps come up).
    m = 0
    for k in range(72):
        a = k * math.tau / 72 + 0.02
        if near_gate(a) < math.radians(3.0) or min(abs(math.atan2(math.sin(a - q), math.cos(a - q))) for q in
                                                    (0.0, math.pi / 2, math.pi, 3 * math.pi / 2)) < math.radians(20.0):
            continue
        r = rd + DECK_W / 2 - 0.5
        box(c, "Merlon %d" % m, r * math.cos(a), r * math.sin(a), 0.45, 1.1, zt - 0.2, zt + 1.1, stone, rot=a)
        m += 1
    # The keep: two halves either side of the tunnel through it (east to west), the roof
    # over both, its parapet's corners, a banner.
    kh, th = 8.0, 4.0
    for sd in (-1, 1):
        box(c, "Keep %s" % ("North" if sd > 0 else "South"), 0.0, sd * (th + kh) / 2, kh, (kh - th) / 2, F - 1.0, zt - 1.0,
            stone)
    box(c, "Keep Roof", 0.0, 0.0, kh, kh, zt - 1.0, zt - 0.02, ("basalt_road", "road"))
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(c, "Keep Parapet %d %d" % (sx, sy), sx * (kh - 0.8), sy * (kh - 0.8), 0.8, 0.8, zt - 0.1, zt + 1.4, stone)
    box(c, "Keep Banner Pole", 0.0, kh - 0.8, 0.15, 0.15, zt + 1.4, zt + 9.0, ("obsidian", "wall"), role="visual")
    box(c, "Keep Banner", 0.0, kh - 0.75, 1.6, 0.06, zt + 5.6, zt + 8.8, ("banner_red", "wall"), role="visual")
    taken.add(0.0, 0.0, kh * 1.5)
    # The bridges, off the walk's inner edge to the keep's roof (east and west, over the
    # tunnel's mouths).
    K = node(0.0, 0.0, zt)
    T = node(0.0, 0.0, F)
    for sd in (-1, 1):
        x0, x1 = sd * (kh - 0.3), sd * (rd - DECK_W / 2 + 0.6)
        box(c, "Bridge %d" % sd, (x0 + x1) / 2, 0.0, abs(x1 - x0) / 2, 4.0, zt - 0.9, zt - 0.02, ("basalt_road", "road"))
        for edge in (-1, 1):
            box(c, "Bridge Rail %d %d" % (sd, edge), (x0 + x1) / 2, edge * 3.8, abs(x1 - x0) / 2 - 1.0, 0.2, zt - 0.1, zt + 0.7,
                stone)
        mid = node(sd * (rd / 2 + 2.0), 0.0, zt)
        link(K, mid)
        link(mid, nearest(W, sd * rd, 0.0))
        link(T, nearest(C, sd * 22.0, 0.0))
    # The rivals' map, in game coordinates.
    gn = [[round(v, 2) for v in c.game(x, y, z)] for x, y, z in nodes]
    c.entity("nav", nodes=gn, links=[list(l) for l in links])
    g = c.game(0.0, 0.0, zt)
    c.entity("deck", r=rd, w=DECK_W, y=round(zt, 2))
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
    """Caldera Keep's dressing (the castle is keep()): boulders and broken walls out in the
    bailey for cover, stumps and steam vents in the courtyard, basalt columns round the
    crater's rim past the moat."""
    for k in range(4):
        for j, da in enumerate((math.radians(31.0), math.radians(62.0))):
            a = k * math.tau / 4 + da
            x, y = 64.0 * math.cos(a), 64.0 * math.sin(a)
            if j == 0:
                for w in range(3):
                    t = (w - 1) * 3.4
                    hh = (3.0, 2.2, 1.5)[w]
                    box(c, "Broken Wall %d %d" % (k, w), x - math.sin(a) * t, y + math.cos(a) * t, 0.8, 1.6, F - 0.5,
                        ground(x, y) + hh, ("basalt_block", "wall"), rot=a)
            else:
                c.assign(c.rock_mass("Boulder %d" % k, x, y, 3.0, 2.4, ground(x, y) + 3.2, z0=F - 2.0, n=10, seed=k + 2),
                         c.lib("obsidian_cliff", "wall"))
            taken.add(x, y, 7.0)
    for k in range(4):
        a = k * math.tau / 4 + math.radians(67.5)
        x, y = 17.0 * math.cos(a), 17.0 * math.sin(a)
        box(c, "Stump %d" % k, x, y, 1.3, 1.3, F - 0.5, ground(x, y) + 1.3, ("basalt_block", "wall"), rot=a)
        x, y = 26.0 * math.cos(a + 0.35), 26.0 * math.sin(a + 0.35)
        g = c.game(x, y, ground(x, y) + 0.3)
        c.entity("steam", x=g[0], y=g[1], z=g[2])
    paint.scatter(c, props.basalt_columns(c), 10, R - 2, lambda x, y: math.hypot(x, y) > MOAT[1] + 3.0, ground, taken, 4,
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
    """The Cutting Pond, like the snow kingdom's (ice_yard.py, its props): the ice's
    invisible floor (the karts drive on it; what they see is the game's blocks), the dark
    water under it, the pond's banks walled in snow (nobody drives off it), the derrick on
    its crib in the middle, its boom out over the ice; the ice house, sledges, the
    brazier, the tool bench, lantern poles, pines round the hollow, snow falling."""
    import ice_yard as iy
    import summit_props as sp
    H = POND_H
    box(c, "Ice Floor", 0.0, 0.0, H, H, ICE_Z - 0.6, ICE_Z, ("lake_ice", "ice"), role="collision")
    box(c, "Pond Water", 0.0, 0.0, H + 0.4, H + 0.4, ICE_Z - 2.6, ICE_Z - 1.4, ("frost_pool", "water"), role="visual")
    # The banks: snow walls round it (and a collider, so no kart leaves the ice but down).
    for k in range(4):
        a = k * math.pi / 2
        cx, cy = (H + 0.9) * math.cos(a), (H + 0.9) * math.sin(a)
        box(c, "Snowbank %d" % k, cx, cy, 0.9, H + 1.8, ICE_Z - 1.0, ICE_Z + 1.1, ("snow_ground", "wall"), rot=a)
        box(c, "Bank Collider %d" % k, cx, cy, 0.9, H + 1.8, ICE_Z - 1.0, ICE_Z + 3.0, ("snow_ground", "wall"), rot=a,
            role="collision")
    # The derrick's crib in the middle, and the derrick on it, its boom out over the ice.
    ih = POND_ISLAND * TILE
    box(c, "Derrick Crib", 0.0, 0.0, ih, ih, ICE_Z - 2.0, ICE_Z + 1.0, ("timber_beam", "wall"))
    c.place(iy.derrick(c), 0.0, -1.5, ICE_Z + 1.0, rot=0.5, coll="Props")
    taken.add(0.0, 0.0, H + 3.0)

    def put(proto, x, y, rot, r):
        z = ground(x, y)
        c.place(proto, x, y, z - 0.1, rot=rot)
        taken.add(x, y, r)
        return z

    # The yard round it: the ice house north, sledges, the brazier, the bench and stump.
    put(iy.ice_house(c), 0.0, H + 12.0, math.pi, 7.0)
    put(iy.sledge(c, 0), H + 9.0, 8.0, 1.2, 3.0)
    put(iy.sledge(c, 1), H + 8.0, -14.0, 1.9, 3.0)
    put(iy.sledge(c, 2), -14.0, H + 9.0, 0.3, 3.0)
    z = put(iy.brazier(c), -(H + 9.0), -10.0, 0.0, 3.5)
    g = c.game(-(H + 9.0), -10.0, z + 1.6)
    c.entity("campfire", x=g[0], y=g[1], z=g[2])
    put(iy.tool_bench(c), -(H + 8.0), 6.0, math.pi / 2, 3.0)
    put(iy.stump(c), -(H + 10.0), 13.0, 0.7, 1.2)
    for k in range(12):
        a = k * math.tau / 12 + 0.26
        rr = H * 1.414 + 3.0 if k % 3 == 1 else H + 5.0
        x, y = rr * math.cos(a), rr * math.sin(a)
        if not taken.clear(x, y, 1.5):
            continue
        z = ground(x, y)
        c.place(iy.lantern_pole(c), x, y, z - 0.1, rot=a + math.pi / 2)
        taken.add(x, y, 1.5)
        g = c.game(x, y, z + 3.45)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
    # Pines round the hollow.
    for v in range(3):
        paint.scatter(c, sp.pine(c, v, 12.0 + 4.0 * v, snowy=True), 26, R + 6, lambda x, y: max(abs(x), abs(y)) > H + 16, ground,
                      taken, 40 + v, room=5.0, scale=(0.9, 1.4), road_margin=-60.0)
    # The rink: the blocks' grid, its crib (the game's).
    g = c.game(0.0, 0.0, ICE_Z)
    c.entity("rink", x=g[0], z=g[2], y=g[1], r=H, tile=TILE, square=POND_N, island=POND_ISLAND)
    c.entity("snowfall", rate=50, radius=50)


def build_stars(c, ground, taken):
    """Meteor Crater's dressing, like the desert's own crater (mesa_region.py crater()):
    the meteorite in the floor, glowing shards round the terraces, boulders to steer
    round on the lanes, a rail round the rim's outer edge (its warning signs on it), the
    observatory out on the flank, the surveyors' tents; where the stars land (`star_spot`:
    the gold ones the hard places), and the rivals' map (`nav`)."""
    import impact_props as ip
    import oasis_props as op
    from pocket_build import cone
    c.place(ip.meteorite(c, 0, size=3.5), 0.0, 0.0, ground(0.0, 0.0) - 0.8)
    taken.add(0.0, 0.0, METEOR_R + 1.0)
    # Boulders on the lanes, here and there (not on a ramp, nor its foot).
    k = 0
    for i in (1, 2, 3):
        rl = lane_r(i)
        for j in range(3):
            a = j * math.tau / 3 + 0.9 * i + 0.4 + (0.35 if i == 2 else 0.0)  # (clear of the karts' starts)
            x, y = rl * math.cos(a), rl * math.sin(a)
            if in_ramp(x, y) or any(in_ramp(x + 6 * dx, y + 6 * dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                continue
            c.assign(c.rock_mass("Crater Boulder %d" % k, x, y, 1.8, 1.5, TIERS[i][2] + 2.0, z0=TIERS[i][2] - 1.0, n=9,
                                 seed=30 + k), c.lib("strata_purple", "wall"))
            taken.add(x, y, 4.0)
            k += 1
    # Shards glowing round the risers' feet (visual).
    for j in range(26):
        i = j % 4
        a = j * 2.399
        rr = TIERS[i][1] - 0.8
        x, y = rr * math.cos(a), rr * math.sin(a)
        if not in_ramp(x, y):
            c.place(ip.glass_shards(c, j % 2), x, y, ground(x, y) - 0.3, rot=a, role="visual")
    # The rim's rail (nobody falls out of the crater), its signs, lanterns.
    rim_out, rim_z = TIERS[-1][1], TIERS[-1][2]
    ring_wall(c, "Rim Rail", rim_out - 0.6, rim_out - 0.2, rim_z - 0.6, rim_z + 0.9, lambda a: False, ("weathered_timber", "wall"),
              n=120)
    for j in range(12):
        a = j * math.tau / 12 + 0.13
        x, y = (rim_out + 0.6) * math.cos(a), (rim_out + 0.6) * math.sin(a)
        if j % 2 == 0:
            c.place(ip.warning_sign(c, j // 2 % 2), x, y, rim_z - 0.6, rot=a, role="visual")
        g = c.game((rim_out - 0.4) * math.cos(a + 0.13), (rim_out - 0.4) * math.sin(a + 0.13), rim_z + 1.4)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
    # The observatory out on the flank (south-west, where you can see it from everywhere),
    # the surveyors' tents by it.
    oa = math.radians(215.0)
    ox, oy = 90.0 * math.cos(oa), 90.0 * math.sin(oa)
    oz = ground(ox, oy)
    cone(c, "Observatory Tower", ox, oy, 5.4, oz - 1.0, 9.0 + 4.0, ("arcade_white", "wall"), segs=16, role="visual")
    box(c, "Observatory Base", ox, oy, 5.0, 5.0, oz - 1.0, oz + 7.0, ("arcade_white", "wall"), role="visual")
    bm = kit.bmesh.new()
    op.dome(bm, ox, oy, oz + 7.0, 5.2)
    c.assign(c.mesh_object("Observatory Dome", bm, "Props", "visual"), c.lib("tin_roof", "wall"))
    box(c, "Observatory Slit", ox, oy, 0.7, 5.3, oz + 8.0, oz + 12.0, ("dark_corridor", "wall"), rot=oa, role="visual")
    for j in range(3):
        a = oa + (j - 1) * 0.28
        x, y = 98.0 * math.cos(a), 98.0 * math.sin(a)
        c.place(ip.tent(c, j % 2), x, y, ground(x, y) - 0.1, rot=a, role="visual")
    # Where the stars land: round every terrace's lane; the gold ones (more often) on the
    # rim, the floor and the ramps' tops.
    spots = []
    for i in range(len(TIERS)):
        rl = lane_r(i)
        n = max(6, int(rl * math.tau / (18.0 if i == len(TIERS) - 1 else 11.0)))
        for j in range(n):
            a = (j + 0.5 * (i % 2)) * math.tau / n
            spots.append((rl * math.cos(a), rl * math.sin(a), i in (0, len(TIERS) - 1)))
    for k in range(len(RAMPS)):
        r0, r1, a0, a1, z0, z1 = ramp_span(k)
        a = a0 + (a1 - a0) * 0.85
        spots.append(((r0 + r1) / 2 * math.cos(a), (r0 + r1) / 2 * math.sin(a), True))
    for x, y, gold in spots:
        g = c.game(x, y, ground(x, y))
        c.entity("star_spot", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), gold=gold)
    # The rivals' map: round every terrace's lane, and up and down every ramp.
    nodes, links = [], []

    def node(x, y, z):
        nodes.append((x, y, z))
        return len(nodes) - 1

    rings = []
    for i, (_r0, _r1, z) in enumerate(TIERS):
        rl = lane_r(i)
        m = max(8, int(rl * math.tau / 14.0))
        ids = [node(rl * math.cos(j * math.tau / m), rl * math.sin(j * math.tau / m), z) for j in range(m)]
        links.extend((ids[j], ids[(j + 1) % m]) for j in range(m))
        rings.append(ids)

    def nearest(ids, x, y):
        return min(ids, key=lambda q: math.hypot(nodes[q][0] - x, nodes[q][1] - y))

    for k, (lo, _mid, _ccw) in enumerate(RAMPS):
        r0, r1, a0, a1, z0, z1 = ramp_span(k)
        rb = (r0 + r1) / 2
        sg = 1.0 if a1 > a0 else -1.0
        at = lambda a, r=rb: (r * math.cos(a), r * math.sin(a))  # noqa: E731
        ra = node(*at(a0 - sg * 7.0 / rb), z0)
        rf = node(*at(a0 + sg * 2.0 / rb), z0 + 0.3)
        rt = node(*at(a1 - sg * 2.0 / rb), z1 - 0.3)
        land = node(*at(a1, lane_r(lo + 1)), z1)
        links.extend(((nearest(rings[lo], *nodes[ra][:2]), ra), (ra, rf), (rf, rt), (rt, land),
                      (land, nearest(rings[lo + 1], *nodes[land][:2]))))
    gn = [[round(v, 2) for v in c.game(x, y, z)] for x, y, z in nodes]
    c.entity("nav", nodes=gn, links=[list(q) for q in links])
    c.entity("fireflies", rate=24, radius=60)


BUILD = {"bowl": build_bowl, "docks": build_docks, "rink": build_rink, "stars": build_stars}

if __name__ == "__main__":
    main()
