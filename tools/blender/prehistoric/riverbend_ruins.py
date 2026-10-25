# Riverbend Palms in ruins: the first of Adventure's treasure map courses (?track=
# riverbend_palms_ruin; in dev builds Riverbend's menu entry asks Standard or Ruined).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/riverbend_ruins.py      (the bpy module)
#
# Blake (Oct 25): Adventure's treasure map challenge runs each world's courses after the
# dragons have attacked: the same places, wrecked, so the laps are much shorter and drive
# completely differently (for speedrunners, still fun for anyone). The ruin opens new
# lines through the same valley ("collapse shortcuts"); he picked route A:
#
#   1  The start straight up the east bank and the long drift onto the river road, as
#      ever (the same road).
#   2  The wooden bridge, burnt through in the middle: jump the gap (a zipper before it;
#      miss it and you're put down past it).
#   3  The S-bends and the ridge are blocked (rubble, fallen palms): a new scorched track
#      straight down the west meadow through the dragons' fire, an S round the craters.
#   4  Back onto the old road just before the ford; the ford, the burnt village (its
#      shortcut still there), the final straight.
#
# About 880 m (the full lap is 1036 m), without the climb, the ridge or the hairpin. The
# valley, river, waterfall, village and landmarks are Riverbend's own (riverbend_palms.py);
# the smoke, embers, ash and wreckage are new.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ruin_mode  # noqa: E402

ruin_mode.ON = True  # (Riverbend's own script doesn't lay out ruins; this marks the build)

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import props  # noqa: E402
import riverbend_palms as rb  # noqa: E402  (the valley itself)
from aurora_scenery import game_entity  # noqa: E402
from course_kit import lerp, rnd, smooth  # noqa: E402

TRACK_ID = "riverbend_palms_ruin"
river_x, WATER_Z = rb.river_x, rb.WATER_Z

# The lap: Riverbend's own road to the far end of the bridge (segments 0-3), the new track
# down the west meadow, and Riverbend's own road again from the ford (its segments 12-17).
O = rb.LAYOUT
LAYOUT = [
    *O[0:4],  # 0-3 the start straight, the drift, the river road and the bridge
    ("L", 30, 90),  # 4  off the bridge's end, south (the S-bends are blocked)
    ("S", 20),  # 5  the scorched track down the west meadow...
    ("R", 30, 70),  # 6  ...an S round the craters...
    ("S", 12),  # 7
    ("L", 30, 70),  # 8
    ("S", 70),  # 9  ...and on south (closes the lap)
    ("L", 30, 90),  # 10 east, back onto the old road before the ford
    ("S", 5),  # 11 (closes the lap)
    *O[12:18],  # 12-17 the ford, on to the village, the village bend, the final straight
]
LAYOUT, PATH = kit.close_turtle(LAYOUT, 9, 11, rb.START, 90.0)
SEG = kit.segment_starts(PATH)
LENGTH = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:]))
BRIDGE_Y = 80.0  # north of this, near the river: the bridge
FORD_Y0 = -100.0  # south of this, near the river: the ford


# The burnt bridge's gap, over the river's middle: the bridge runs due west along
# BRIDGE_LINE, so its distance along is just x. Cut like Coral Cove's jump (with_jumps'
# shape): a kick up to the lip, a landing dropped below the deck, easing back up.
BRIDGE_LINE = next(p for p in PATH if p[3] == 3)[1]
GAP, KICK, DROP, RUN, OUT = 10.0, 0.9, 2.5, 12.0, 30.0
X_LIP = river_x(BRIDGE_LINE) + GAP / 2
X_LAND = X_LIP - GAP


def _base_z(x, y):
    z = 0.5 + 8.2 * smooth((-x - 95) / 60) + 0.25 * math.sin(x / 37) * math.cos(y / 41)
    d = abs(x - river_x(y))
    if y > BRIDGE_Y:
        z += 3.0 * smooth((34 - d) / 28)
    elif y < FORD_Y0:
        z -= 0.95 * smooth((30 - d) / 22)
    return z


def road_z(x, y):
    """Riverbend's heights (as rb.road_z) where the road is Riverbend's, the jump cut into
    the bridge; the new track down the meadow is level ground (rb.road_z would arch it
    near the river)."""
    if y > BRIDGE_Y and abs(y - BRIDGE_LINE) < 3 and X_LAND - OUT <= x <= X_LIP + RUN:
        b = lambda xx: _base_z(xx, BRIDGE_LINE)  # noqa: E731
        if x >= X_LIP:
            return b(x) + KICK * ((X_LIP + RUN - x) / RUN) ** 2
        if x >= X_LAND:
            return lerp(b(X_LIP) + KICK, b(X_LAND) - DROP, (X_LIP - x) / GAP)
        return b(x) - DROP * (1 - smooth((X_LAND - x) / OUT))
    return _base_z(x, y)


ROUTE = kit.route_points(PATH, road_z, every=6.0)


def _plan_d(pred):
    d = 0.0
    for a, b in zip(PATH, PATH[1:]):
        d += math.hypot(b[0] - a[0], b[1] - a[1])
        if pred(b):
            return d
    return None


def _beside(i, off, r):
    """A crater `off` metres in from the middle of segment i (inside its bend; to the left
    of a straight), radius r."""
    pts = [p for p in PATH if p[3] == i]
    x, y, h, _ = pts[len(pts) // 2]
    hr = math.radians(h)
    side = -1 if LAYOUT[i][0] == "R" else 1
    return (x - side * math.sin(hr) * off, y + side * math.cos(hr) * off, r)


# Craters beside the new track: the S weaves round them.
CRATERS = [_beside(6, 15.0, 7.0), _beside(8, 15.0, 7.0), _beside(9, -18.0, 8.0)]


# The gap along the lap.
LIP = _plan_d(lambda p: p[3] == 3 and p[0] <= X_LIP)
LAND = _plan_d(lambda p: p[3] == 3 and p[0] <= X_LAND)

# The old road the ruin no longer takes (Riverbend's S-bends, ridge and hairpin), kept
# to see, blocked at both ends.
_d = [0.0]
for a, b in zip(rb.PATH, rb.PATH[1:]):
    _d.append(_d[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
_s4 = next(d for d, p in zip(_d, rb.PATH) if p[3] == 4)
_s12 = next(d for d, p in zip(_d, rb.PATH) if p[3] == 12)
OLD = [(p[0], p[1]) for d, p in zip(_d, rb.PATH) if _s4 + 46 < d < _s12 - 34][::10]

# Where the dragons' fire fell: (x, y, r). Scorched ground, smoke, charred trees.
BURNS = [(-70.0, 52.0, 22.0), (-96.0, 6.0, 26.0), (-72.0, -50.0, 20.0), (-128.0, 70.0, 24.0), (-150.0, -10.0, 26.0),
         (-140.0, -95.0, 22.0), (60.0, -150.0, 20.0), (100.0, -72.0, 14.0), (-30.0, 100.0, 14.0), (45.0, 98.0, 12.0),
         (120.0, 30.0, 18.0), (-60.0, 140.0, 22.0), (30.0, 150.0, 18.0)]


def burn(x, y):
    """0..1: how scorched the ground is here."""
    return max(smooth((1.4 * r - math.hypot(x - bx, y - by)) / (r * 0.7)) for bx, by, r in BURNS)


def natural(x, y):
    h = rb.natural(x, y)
    for cx, cy, r in CRATERS:
        d = math.hypot(x - cx, y - cy)
        if d < r * 1.5:
            h -= 1.6 * smooth((r - d) / r) - 0.5 * smooth((r * 1.5 - d) / (r * 0.5)) * smooth((d - r * 0.8) / (r * 0.2))
    return h


def classify(c, n, info):
    mat = rb.classify(c, n, info)
    if mat[0] == "valley_grass":
        # The same surface, singed everywhere, burnt black where the fire fell.
        if burn(c.x, c.y) > 0.4 + 0.2 * math.sin(c.x * 0.7 + c.y * 0.5):
            return ("ruin_ash", mat[1])
        return ("ruin_grass", mat[1])
    return mat


def main():
    c = kit.Course(TRACK_ID, "Riverbend Palms (Ruined)", "riverbend_ruins")
    c.route(ROUTE, width=14.0, bank=7.0)
    c.kinds = {
        "road": {"mat": "valley_road", "shoulder": 1.5, "shoulder_mat": ("ruin_grass", "dirt")},
        "scorched": {"mat": "ruin_road", "surface": "road", "shoulder": 1.5, "shoulder_mat": ("ruin_ash", "dirt")},
        "bridge": {"mat": "ruin_char_planks", "surface": "road", "shoulder": 0.4, "shoulder_mat": ("ruin_char_planks", "road"),
                   "barrier": 1.0, "barrier_mat": ("ruin_char", "wall"), "deck": 1.4, "deck_mat": ("ruin_char_planks", "road"),
                   "ground": False},
        "kicker": {"mat": "ruin_char_planks", "surface": "road", "shoulder": 0.4, "shoulder_mat": ("ruin_char_planks", "road"),
                   "deck": 1.4, "deck_mat": ("ruin_char_planks", "road"), "ground": False},
        "ford": {"mat": "swamp_stone", "surface": "road", "shoulder": 1.0, "shoulder_mat": ("valley_sand", "sand"), "deck": 1.6,
                 "deck_mat": ("swamp_stone", "wall"), "ground": False},
    }
    lip, land = kit.s_near(c, *_xy(LIP)), kit.s_near(c, *_xy(LAND))
    t0, t1 = kit.s_near(c, *_seg_xy(4)) + 20, kit.s_near(c, *_seg_xy(11))

    def near_river(smp):
        return abs(smp.p.x - river_x(smp.p.y)) < 30

    def label(smp):
        s = smp.s
        if lip <= s <= land:
            return "gap"
        if lip - 10 <= s < lip:
            return "kicker"
        if near_river(smp) and smp.p.y > BRIDGE_Y:
            return "bridge"
        if near_river(smp) and smp.p.y < FORD_Y0:
            return "ford"
        if t0 <= s <= t1:
            return "scorched"
        return "road"

    specials = []
    for s0, s1, k in kit.runs(c, label):
        if k == "gap":
            specials.append((s0, s1, None))
        elif k == "kicker":
            specials.append((s0, s1, "kicker", {"lift": lambda u, n: 0.6 * max(0.0, (u - (n - 8)) / 8) ** 2}))
        elif k != "road":
            specials.append((s0, s1, k))
    c.roads(kit.plan(c, specials, "road"))
    c.shortcut("Village Shortcut", [(x, y, road_z(x, y) - 0.05) for x, y in rb.SHORTCUT],
               "ruin_road", "dirt", width=8.0, shoulder_mat=("ruin_ash", "dirt"))
    # The old road: there to see, cut off at both ends by rubble (grass under it).
    c.side_road("Old Road", [(x, y, road_z(x, y) - 0.08) for x, y in OLD], "ruin_road", "dirt", width=13.0, shoulder=1.2,
                shoulder_mat=("ruin_ash", "dirt"))

    ter = c.terrain("Valley", -250, 250, -250, 250, 3.3, natural, classify)
    ford = [(river_x(y), y) for y in range(int(rb.FORD_Y) - 36, int(rb.FORD_Y) + 37, 6)]
    north = [(river_x(y), y) for y in range(int(rb.FORD_Y) + 36, int(rb.FALLS_Y) - 6, 6)]
    north.append((river_x(rb.FALLS_Y - 4.0), rb.FALLS_Y - 4.0))
    south = [(river_x(y), y) for y in range(-262, int(rb.FORD_Y) - 35, 6)]
    c.ribbon("River Ford", ford, 56, WATER_Z, c.lib("valley_water"), steps=4)
    c.ribbon("River", north, 56, WATER_Z, c.lib("valley_water", "deep_water"), steps=4)
    c.ribbon("River South", south, 56, WATER_Z, c.lib("valley_water", "deep_water"), steps=4)
    c.start_line()
    rb.scenery(c)
    char_trees(c)
    wreckage(c, [ter], lip, land)

    S = lambda i: kit.s_near(c, *_seg_xy(i))  # noqa: E731
    river_s = [r for r in kit.crossings(c, lambda s: near_river(s) and s.p.y < FORD_Y0, margin=3)]
    c.zipper(c.length - 40, 0)  # out of the last drift, onto the final straight
    c.zipper(lip - 46, 0)  # onto the bridge: it carries you over the gap
    c.zipper(S(9) + 20, 2)  # down the meadow
    for at, across in ((40, -3), (S(5) + 8, 3), (river_s[0][1] + 60, 2), (c.length - 22, 3)):
        c.bananas(at, across, count=5, gap=2.6)
    for at, across, col in ((95, -4, "red"), (95, 4, "blue"), (S(7) + 6, 0, "green"), (S(9) + 50, 0, "yellow"),
                            (river_s[0][0] - 15, 3, "rainbow")):
        c.balloon(at, across, col)
    c.entity("respawn", **{"from": round(lip - 20, 1), "to": round(land + 4, 1), "at": round(land + 16, 1)})
    gx, gy, gz = c.game(river_x(rb.FALLS_Y), rb.FALLS_Y - 7.5, WATER_Z)
    c.entity("waterfall", x=gx, y=gy, z=gz, top=rb.FALLS_TOP, width=30, heading=0)
    c.entity("ashfall", rate=50, radius=40)

    short = [(x, y, road_z(x, y)) for x, y in rb.SHORTCUT]
    s_in, s_out = kit.s_near(c, *rb.SHORTCUT[0]), kit.s_near(c, *rb.SHORTCUT[-1])
    apex = (s_in + s_out) / 2
    gates = c.checkpoints(
        extra=[land + 14, S(6), S(9) + 30, river_s[0][1] + 12, apex],
        avoid=[(lip - 16, land + 8), (s_in, apex - 12), (apex + 12, s_out)],
    )
    main_gate = min(gates.items(), key=lambda kv: abs(kv[0] - apex))[1]
    c.alt_gate(main_gate, "village_shortcut", short, width=26)

    c.preset("sun", [o for o in c.coll("Terrain").objects], 0.35)
    c.preset("road_edge", [o for o in c.coll("Terrain").objects], 0.4, color=(1.0, 0.8, 0.55), distance=7.0)
    c.finish()
    print("lap", round(c.length, 1), "gap", round(lip, 1), round(land, 1))


def _xy(d):
    t = 0.0
    for a, b in zip(PATH, PATH[1:]):
        t += math.hypot(b[0] - a[0], b[1] - a[1])
        if t >= d:
            return b[0], b[1]
    return PATH[-1][0], PATH[-1][1]


def _seg_xy(i):
    p = next(p for p in PATH if p[3] == i)
    return p[0], p[1]


def wreckage(c, ter, lip, land):
    """The dragons' work: the bridge's burnt-out middle (charred stubs, embers), rubble
    and fallen palms across both ends of the old road, craters ringed with rubble,
    charred trees, burning stumps (fire and smoke), smoke over the village."""
    stub, log, tree = _stub(c), props.log(c, 0), props.dead_tree(c)
    rubble = [props.boulder(c, "ruin_rubble", v) for v in range(3)]
    fires = []

    def ground(x, y):
        z = c.ground_z(x, y, ter)
        return z if z is not None else natural(x, y)

    # The gap: charred posts and planks sticking up at both broken ends, embers glowing.
    for s, sign in ((lip, 1), (land, -1)):
        q = c.at(s)
        for k, across in enumerate((-6.0, -3.0, 0.5, 3.5, 6.2)):
            p = q.side(across) + q.t * sign * (0.3 + 0.5 * (k % 2))
            c.place(stub, p.x, p.y, q.p.z - 1.6, rot=k * 1.7, scale=0.8 + 0.4 * (k % 3), coll="Wreck", role="visual")
        fires.append((q.p.x, q.p.y, q.p.z - 0.2))
    # The old road's two ends, blocked: a heap of rubble and fallen palms.
    for (x0, y0), (x1, y1) in ((OLD[0], OLD[1]), (OLD[-1], OLD[-2])):
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) or 1
        ux, uy = dx / L, dy / L
        cx, cy = x0 + ux * 2, y0 + uy * 2
        for k in range(9):
            a = (k - 4) * 1.6
            x, y = cx - uy * a + ux * (k % 3 - 1) * 1.2, cy + ux * a + uy * (k % 3 - 1) * 1.2
            c.place(rubble[k % 3], x, y, ground(x, y) - 0.3, rot=k * 1.3, scale=1.6 + 0.8 * rnd(k), coll="Wreck")
        for k in range(2):
            rot = math.atan2(-ux, uy) + 0.3 * (k - 0.5)
            c.place(log, cx + ux * (3 + 3 * k), cy + uy * (3 + 3 * k), ground(cx, cy) + 0.3, rot=rot, scale=2.2, coll="Wreck")
        fires.append((cx + ux * 5, cy + uy * 5, ground(cx, cy) + 1.0))
    # Fallen palms across the old road along its length.
    for k in range(2, len(OLD) - 2, 3):
        x, y = OLD[k]
        nx, ny = OLD[k + 1]
        rot = math.atan2(ny - y, nx - x) + math.pi / 2 + 0.4 * (rnd(k) - 0.5)
        c.place(log, x, y, ground(x, y) + 0.2, rot=rot, scale=2.4, coll="Wreck")
    # Craters, ringed with rubble.
    for j, (cx, cy, r) in enumerate(CRATERS):
        for k in range(10):
            a = k * math.tau / 10 + j
            x, y = cx + r * 1.1 * math.cos(a), cy + r * 1.1 * math.sin(a)
            if props.clear_of_road(c, x, y, 2.5):
                c.place(rubble[(k + j) % 3], x, y, ground(x, y) - 0.4, rot=k, scale=0.7 + 0.5 * rnd(k + j), coll="Wreck")
        fires.append((cx, cy, ground(cx, cy) + 0.3))
    # Charred trees and burning stumps in the burnt ground.
    k = 0
    for bx, by, br in BURNS:
        for m in range(4):
            k += 1
            a, rr = rnd(k * 1.7) * math.tau, br * 0.8 * rnd(k * 2.3)
            x, y = bx + rr * math.cos(a), by + rr * math.sin(a)
            z = ground(x, y)
            if z < WATER_Z + 0.4 or not props.clear_of_road(c, x, y, 4.0):
                continue
            if m % 2 == 0:
                c.place(tree, x, y, z - 0.2, rot=k, scale=1.2 + 0.6 * rnd(k), coll="Wreck", role="visual")
            else:
                c.place(stub, x, y, z - 0.3, rot=k, scale=1.6, coll="Wreck", role="visual")
                fires.append((x, y, z + 1.2))
    for x, y, z in fires:
        game_entity(c, "torch", x, y, z)
    # Smoke: from the fires, the burnt hamlets and the old road's ends.
    for x, y, z in fires[::2]:
        game_entity(c, "campfire", x, y, z - 0.6)
    for (hx, hy), _, _ in rb.HAMLETS:
        game_entity(c, "chimney", hx, hy, ground(hx, hy) + 3.0)
    c.glow([o for o in c.coll("Terrain").objects], fires, 9.0, (1.6, 0.9, 0.5), base=1.0)
    print("ruin wreckage: fires", len(fires))


def char_trees(c):
    """Most of the trees where the fire fell are charred stems now (the same spots)."""
    tree = props.dead_tree(c)
    me = c.protos[tree]
    n = 0
    for ob in list(c.coll("Props").objects):
        if not ob.name.startswith(("Palm", "Jungle Tree", "Grand Tree")) or ob.type != "MESH":
            continue
        x, y = ob.location.x, ob.location.y
        if burn(x, y) > 0.25 and rnd(x * 0.37 + y * 0.71) < 0.8:
            ob.data = me
            ob.scale = (1.4, 1.4, 1.4)
            n += 1
    print("charred trees", n)


def _stub(c):
    """A burnt stump or post: charred wood, glowing at its broken top."""
    name = "Charred Stub"

    def build(bm):
        from props import _faces, ring, loft

        rings = [ring(bm, (0, 0), r, z, 6) for r, z in ((0.45, 0.0), (0.4, 1.4), (0.3, 2.2))]
        loft(bm, rings, cap_top=False)
        wood = _faces(bm, 0)
        k0 = len(bm.faces)
        top = [bm.verts.new((0.3 * math.cos(a), 0.3 * math.sin(a), 2.2 + (0.4 if i % 2 else 0.0)))
               for i, a in enumerate(k * math.tau / 6 for k in range(6))]
        bm.faces.new(top)
        return [(c.lib("ruin_char"), wood), (c.lib("ruin_ember"), _faces(bm, k0))]

    return c.proto(name, build) and name


if __name__ == "__main__":
    main()
