# Dinosaur Valley, the overworld's first region: the valley the game opens in, with the
# gateways into its four courses (the Claude Doc "Kartipelago Overworld: Concept &
# Layout"; src/overworld/regions.ts places the gateways).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/valley_region.py [--ruin]      (the bpy module)
#
# v2 (Blake, Oct 26: "a unique shape ... segments of the overworld that capture the
# flavor of the level ... secretly an awesome race course ... think of kokiri forest"):
# the layout is valley_layout.py. Four lobes round Elder Mossback's camp on its low
# plateau, each one of the valley's courses' worlds, joined by necks over low ridges:
#
#   Riverbend (west)   a palm-lined river bend; its gateway among the palms on the far bank
#   Cascade (NE)       a jungle canyon climbing to the falls, temple ruins in the trees; its
#                      gateway the cave mouth beside the falls
#   Ember (SE)         volcanic ground rising to the cliffs, lava pools and smoking vents;
#                      its gateway the lava-lit tunnel
#   Bonebog (SW)       sunken swamp: pools, mud, dead trees, reeds, bones, mist; its gateway
#                      on the shore by the pyramid's tip
#
# The main road is one winding loop through all four (the champion's challenge is raced
# on it, from the line by the camp). --ruin: the valley after Cinderjaw's attack: the
# Burnt Gorge split through the north cliff, his Scar in the south up a burnt trench, the
# trees charred, the ground scorched.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
from course_kit import Vector, bmesh, lerp, smooth  # noqa: E402
import region_ruin as ruin  # noqa: E402
import puzzle_kit  # noqa: E402
import props  # noqa: E402
import region_paint as paint  # noqa: E402
import ruin_kit  # noqa: E402
import swamp_props as sp  # noqa: E402
import bonebog_scenery as bs  # noqa: E402
import valley_layout as L  # noqa: E402

RUIN = ruin.ON
TRACK_ID = ruin.track_id("valley_region") + os.environ.get("KP_REGION_SUFFIX", "")
WATER_Z = L.WATER_Z
FLOOR_Z = 1.4  # (the other regions' builds still read these)
RIM_Z = L.RIM_Z
CAMP_R = L.CAMP[2]
GORGE_HW = 16.0
GORGE_END = L.GORGE_END
RIVER_HW = L.RIVER_HW

# The Three Stones (src/overworld/puzzles.ts): an old stone pen in the camp's north meadow,
# its gate shut, and three switch stones round it.
PEN = (-22.0, 60.0)  # x, y
PEN_HALF = 10.0
PEN_GAP = 4.5
STONES = [(-58.0, 34.0), (22.0, 54.0), (-36.0, 14.0)]
# The Elder's lookout (Act V's return task): a walled hollow on Ember's lower slope, its
# way in blocked by a rockfall the Valley Tool clears.
RETURN = (126.0, -174.0)
# A secret: a grotto in the Cascade's woods, walled with ice the Snow Tool melts.
SECRET = (208.0, 158.0)


def polar(a_deg, r):
    a = math.radians(a_deg)
    return r * math.cos(a), r * math.sin(a)


def gorge_x(y):
    """The Burnt Gorge winds a little as it climbs north from the road."""
    return L.GORGE[0] + 9.0 * math.sin(max(0.0, y - 250.0) / 45.0)


def burn(x, y):
    """Where Cinderjaw's fire fell (0 none .. 1): most of the valley, a few green patches
    left (the swamp's too wet to burn much)."""
    w = L.lobe_weights(x, y)
    return (0.6 + 0.45 * math.sin(x / 53.0 + 1.3) * math.cos(y / 47.0 - 0.4)) * (1.0 - 0.6 * w["bonebog"])


def natural(x, y):
    h = L.natural(x, y)
    tz = L.tunnel_floor(x, y)
    if tz is not None:
        h = min(h, tz - 0.25)  # (under a tunnel's rock: flush under its road, out to the walls)
    bz = L.bridge_floor(x, y)
    if bz is not None:
        h = min(h, bz)  # (under a bridge's deck)
    if RUIN:
        # The Burnt Gorge: the split in the north cliff, its floor rising gently to the far
        # end, where the way on to the Snow Kingdom begins.
        g = smooth((GORGE_HW + 12 - abs(x - gorge_x(y))) / 12) * smooth((y - L.GORGE[1] - 10.0) / 30.0)
        if g > 0:
            h = lerp(h, 11.0 + 0.04 * max(0.0, y - 300.0), g)
        # The burnt trench up to the Scar.
        sx, sy = L.SCAR
        if y < -270 and abs(x - sx) < 32:
            t = smooth((32 - abs(x - sx)) / 12.0) * smooth((-270 - y) / 20.0)
            h = lerp(h, 10.0, t)
    return h


LOOK = {
    # lobe: (ground, cliff, road, shoulder)
    "riverbend": (("valley_grass", "grass"), ("valley_cliff", "wall"), "valley_road", ("valley_grass", "dirt")),
    "cascade": (("jungle_leafcover", "grass"), ("jungle_mossstone", "wall"), "jungle_path", ("jungle_leafcover", "dirt")),
    "ember": (("ash_soil", "dirt"), ("magma_rock", "wall"), "basalt_road", ("scorched_ground", "dirt")),
    "bonebog": (("bog_bank", "grass"), ("bog_dark_stone", "wall"), "bog_paving", ("bog_moss_ground", "dirt")),
    "camp": (("valley_grass", "grass"), ("valley_cliff", "wall"), "valley_road", ("valley_grass", "dirt")),
}


def lobe_at(x, y):
    w = L.lobe_weights(x, y)
    return max(w, key=w.get)


def classify(c, n, info):
    lobe = lobe_at(c.x, c.y)
    ground, cliff, _, _ = LOOK[lobe]
    if n.z < 0.62:
        if RUIN and c.y > L.GORGE[1] + 20 and abs(c.x - gorge_x(c.y)) < GORGE_HW + 30:
            return ("obsidian_cliff", "wall")  # (the gorge's walls are scorched black)
        return cliff
    if RUIN and c.y < -280 and abs(c.x - L.SCAR[0]) < 24:
        return ("lava_crust", "dirt")
    for px, py, pr in L.POOLS:
        if math.hypot(c.x - px, c.y - py) < pr + 6 and c.z < WATER_Z + 0.6:
            return ("bog_mud", "mud")
    d, wz = L.river_d(c.x, c.y)
    if d < RIVER_HW + 3 and c.z < wz + 0.3:
        return ("valley_sand", "water")  # (the river's wadeable)
    if RUIN and lobe != "bonebog" and burn(c.x, c.y) > 0.5:
        return ("scorched_ground", "dirt")
    return ground


def box(c, name, cx, cy, hx, hy, z0, z1, mat, rot=0.0, role="both", coll="Props"):
    bm = bmesh.new()
    ca, sa = math.cos(rot), math.sin(rot)
    vs = []
    for z in (z0, z1):
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            lx, ly = sx * hx, sy * hy
            vs.append(bm.verts.new((cx + lx * ca - ly * sa, cy + lx * sa + ly * ca, z)))
    for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([vs[i] for i in f])
    ob = c.mesh_object(name, bm, coll, role)
    c.assign(ob, c.lib(*mat))
    return ob


def cone(c, name, cx, cy, r, z0, h, mat, segs=4, role="both", coll="Props"):
    bm = bmesh.new()
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=0.0, depth=h)
    for v in res["verts"]:
        v.co = kit.Vector((cx + v.co.x, cy + v.co.y, z0 + h / 2 + v.co.z))
    ob = c.mesh_object(name, bm, coll, role)
    c.assign(ob, c.lib(*mat))
    return ob


def line(a, b, every=8.0, z=None, z0=None):
    """Points from a to b on the land (or z(x, y)); z0: the height it leaves from (a road
    it joins), eased into the land over its first 24 m so the joint is flush."""
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / every))
    total = math.hypot(b[0] - a[0], b[1] - a[1])
    pts = []
    for k in range(n + 1):
        x, y = lerp(a[0], b[0], k / n), lerp(a[1], b[1], k / n)
        h = z(x, y) if z else natural(x, y) + 0.2
        if z0 is not None:
            h = lerp(z0 + 0.02, h, smooth(total * k / n / 24.0))
        pts.append((x, y, h))
    return pts


def main():
    c = kit.Course(TRACK_ID, "Dinosaur Valley (ruined)" if RUIN else "Dinosaur Valley", "mirror_lake")
    c.route(L.route_points(), width=14.0, bank=6.0)
    kinds = {}
    for lobe, (ground, cliff, road, shoulder) in LOOK.items():
        kinds[lobe] = {"mat": road, "shoulder": 1.5, "shoulder_mat": shoulder}
    stone = ("jungle_mossstone", "wall")
    kinds["bridge"] = {"mat": "wood_planks", "surface": "road", "shoulder": 0.6, "shoulder_mat": ("wood_planks", "road"),
                       "barrier": 1.0, "barrier_mat": ("palm_bark", "wall"), "deck": 1.8, "deck_mat": ("palm_bark", "wall"),
                       "ground": False}
    kinds["temple_bridge"] = {"mat": "jungle_temple", "surface": "road", "shoulder": 0.6, "shoulder_mat": ("ruin_stone", "road"),
                              "barrier": 1.2, "barrier_mat": stone, "deck": 2.4, "deck_mat": stone, "ground": False}
    c.kinds = kinds

    def label(smp):
        d, wz = L.river_d(smp.p.x, smp.p.y)
        # (a bridge only where the land's well under the road: no bank stands up through it)
        if d < RIVER_HW + 6 and smp.p.z > wz + 0.9 and natural(smp.p.x, smp.p.y) < smp.p.z - 1.2:
            return "temple_bridge" if lobe_at(smp.p.x, smp.p.y) == "cascade" else "bridge"
        return lobe_at(smp.p.x, smp.p.y)

    c.roads(kit.plan(c, list(kit.runs(c, label)), "camp", max_len=160.0))

    # The camp's square, and the way out of it onto the road (east).
    cx, cy, cr = L.CAMP
    trail = dict(width=10.0, shoulder=1.2, shoulder_mat=("valley_grass", "dirt"))
    smp, _ = c.nearest(cx + cr + 30.0, cy)
    c.side_road("Camp Road", list(reversed(line((smp.p.x, smp.p.y), (cx + cr - 2.0, cy), z0=smp.p.z))), "valley_trail",
                "road", **trail)
    # Out from the road to each landmark's gateway.
    spurs = {}
    for name, (gx, gy) in L.GATES.items():
        smp, _ = c.nearest(gx, gy)
        ax, ay = smp.p.x, smp.p.y
        d = math.hypot(gx - ax, gy - ay)
        ux, uy = (gx - ax) / d, (gy - ay) / d
        end = (gx - ux * 12.0, gy - uy * 12.0)
        spurs[name] = (end, math.atan2(-ux, uy))
        c.side_road(name.title() + " Road", line((ax, ay), end, z0=smp.p.z), LOOK[lobe_at(gx, gy)][2], "road", **trail)
    if RUIN:
        # Up the burnt trench to Cinderjaw's Scar, and the Burnt Gorge north.
        smp, _ = c.nearest(*L.SCAR)
        c.side_road("Scar Road", line((smp.p.x, smp.p.y), (L.SCAR[0], L.SCAR[1] + 18.0), z0=smp.p.z), "basalt_road", "road",
                    width=10.0,
                    shoulder=1.2, shoulder_mat=("lava_crust", "dirt"))
        smp, _ = c.nearest(*L.GORGE)
        gorge = [(smp.p.x, smp.p.y, smp.p.z)] + [(gorge_x(y), y, natural(gorge_x(y), y) + 0.2)
                                                 for y in range(int(L.GORGE[1]) + 24, int(GORGE_END) + 1, 8)]
        c.side_road("Burnt Gorge Road", gorge, "valley_trail", "road", **trail)

    X0, X1, Y0, Y1 = -480, 480, -480, 480
    ter = c.terrain("Valley", X0, X1, Y0, Y1, 5.0, natural, classify, near=8.0, fade=16.0)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 5.0, lambda x, y: natural(x, y) - 0.5, c.lib("valley_grass", "grass"))

    def ground(x, y):
        z = c.ground_z(x, y, [ter])
        return natural(x, y) if z is None else z

    # Water: the river down from the falls (sloping, a ribbon), the bog's pools.
    for j, riv in enumerate(L.RIVERS):
        river = []
        for (ax, ay, az), (bx, by, bz) in zip(riv, riv[1:]):
            n = max(1, int(math.hypot(bx - ax, by - ay) / 6))
            for k in range(n):
                t = k / n
                river.append((lerp(ax, bx, t), lerp(ay, by, t), 2 * RIVER_HW + 8, lerp(az, bz, t) - 0.1))
        river.append((riv[-1][0], riv[-1][1], 2 * RIVER_HW + 8, riv[-1][2] - 0.1))
        c.ribbon("River %d" % j, river, 2 * RIVER_HW + 8, 0, c.lib("valley_water", "water"), role="visual", steps=4)
    for k, (lx, ly, lr, lz) in enumerate(L.LAKES):
        c.disc("Lake %d" % k, lx, ly, lr + 6.0, lz - 0.1, c.lib("valley_water", "water"), role="visual", n=30, wobble=0.12,
               seed=20 + k)
    for k, (px, py, pr) in enumerate(L.POOLS):
        c.disc("Bog Pool %d" % k, px, py, pr + 8.0, WATER_Z, c.lib("bog_water", "mud"), role="visual", n=30, wobble=0.15,
               seed=k)
        gx, gy, gz = c.game(px, py, WATER_Z + 0.1)
        c.entity("bubbles", x=gx, y=gy, z=gz, r=pr * 0.7)
        c.entity("mist", x=gx, y=gy + 1.0, z=gz, radius=pr + 10.0, rate=5)
    # The falls, each out of its cliff, thrown down the river's way.
    for j, ((fx, fy), riv) in enumerate(zip(L.FALLS, L.RIVERS)):
        dx, dy = riv[1][0] - riv[0][0], riv[1][1] - riv[0][1]
        d = math.hypot(dx, dy)
        dx, dy = dx / d, dy / d
        top = min(riv[0][2] + 34.0, L.TOP + 2.0)
        props.falls(c, ("Riverbend Falls", "Cascade Falls")[j], fx - dx * 6.0, fy - dy * 6.0, top, riv[0][2], 12.0, 18.0,
                    facing=-1, throw=7.0, angle=math.atan2(dy, dx) + math.pi / 2)

    # The camp: a beaten-earth square, Riverbend's huts round a fire (burnt out after).
    c.disc("Camp Square", cx, cy, cr, L.CAMP_Z + 0.05, c.lib("valley_trail", "dirt"), coll="Props", n=40)
    for k in range(5):
        a = k * math.tau / 5 + 0.9
        hx, hy = cx + (cr - 6) * math.cos(a), cy + (cr - 6) * math.sin(a)
        if abs(math.sin(a)) < 0.35 and math.cos(a) > 0:
            continue  # (clear of the way out, east)
        if RUIN:
            box(c, "Hut %d" % k, hx, hy, 3.2, 3.2, L.CAMP_Z - 1.0, L.CAMP_Z + 2.2 + 0.6 * (k % 2), ("obsidian_cliff", "wall"), rot=a)
            ruin.smoke(c, hx, hy, L.CAMP_Z + 2.5)
        else:
            c.place(props.hut(c), hx, hy, L.CAMP_Z, rot=a + math.pi)
    gx, gy, gz = c.game(cx, cy, L.CAMP_Z + 0.2)
    c.entity("campfire", x=gx, y=gy, z=gz)

    thresholds(c, ground)
    landmarks(c, ground, spurs)
    if RUIN:
        ruined(c, ground, spurs)
    three_stones(c, ground)
    puzzle_kit.pen(c, "return", "Lookout", *RETURN, to_road(c, *RETURN), 11.0, 4.5, ("magma_rock", "wall"),
                   ground(*RETURN), height=6.0)
    puzzle_kit.pen(c, "secret", "Grotto", *SECRET, to_road(c, *SECRET), 9.0, 4.5, ("jungle_mossstone", "wall"),
                   ground(*SECRET), height=6.0)
    for name, (end, heading) in spurs.items():
        gx, gy, gz = c.game(end[0], end[1], 0.0)
        c.entity("gateway_spot", gateway=name, x=gx, z=gz, heading=heading)
    dress(c, ground, spurs)

    # (Raced too: the champion's challenge, once round the loop, from this line by the camp.)
    c.start_line()
    gates = c.checkpoints(height=10.0)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish(extra={"race": {"laps": 1}})
    print("loop", round(c.length, 1), "gates", len(gates))


def tunnel_span(c, a, b):
    """The stretch of the road (s0, s1) that runs through the high ground round route
    points a..b (a tunnel's length: from the wall's foot on one side to the other's)."""
    s0 = c.nearest(*L.ROUTE[a][:2])[0].s
    s1 = c.nearest(*L.ROUTE[b][:2])[0].s
    if s1 < s0:
        s1 += c.length

    def inwall(s):
        q = c.at(s)
        return L.wall_sd(q.p.x, q.p.y) > -10.0

    for _ in range(40):
        if not inwall(s0 - 3.0):
            break
        s0 -= 3.0
    for _ in range(40):
        if not inwall(s1 + 3.0):
            break
        s1 += 3.0
    return s0, s1


def thresholds(c, ground):
    """The ways between the worlds (Blake: tunnels you can't see through, walls that are
    landscape): a ridge of rock heaped over the road where it crosses the high ground,
    bored through, each its own: the Fallen Giant (a colossal hollow log the dinosaurs
    made their tunnel, lanterns inside), the Lava Tube (basalt, lava glowing in channels
    along its walls) and the Temple Steps (carved stone, a gateway at each end)."""
    for name, kind, a, b in L.TUNNELS:
        s0, s1 = tunnel_span(c, a, b)
        mid = c.at((s0 + s1) / 2)
        half_len = (s1 - s0) / 2
        ang = math.atan2(mid.t.y, mid.t.x)
        zr = min(c.at(s0).p.z, c.at(s1).p.z)
        wall, top = {"log": (("valley_cliff", "wall"), ("valley_grass", "grass")),
                     "lava": (("volcano_basalt", "wall"), ("ash_soil", "dirt")),
                     "temple": (("jungle_mossstone", "wall"), ("jungle_leafcover", "grass"))}[kind]
        # The heap over the road (it fills the cut the road makes through the high ground,
        # and stands a little over the ridge round it, so nothing shows through).
        rock = c.rock_mass(name + " Rock", mid.p.x, mid.p.y, half_len + 16.0, 40.0, L.TOP - 1.0, z0=zr - 6.0, n=30,
                           seed=len(name), angle=ang, base=zr,
                           bands=[(1.0, 0.0), (1.0, 0.3), (0.96, 0.55), (0.9, 0.8), (0.8, 0.95), (0.7, 1.0)])
        half = c.width / 2 + (4.5 if kind == "log" else 3.0)
        c.tunnel(rock, s0, s1, half=half, height=13.0 if kind == "log" else 10.0, pad=6.0)
        for p, q in ((s0 - 70.0, s0 - 2.0), (s1 + 2.0, s1 + 70.0)):  # (overlapping the bore: no skin left between)
            c.tunnel(rock, p, q, half=half + 1.0, height=70.0, pad=0.0, floor=-12.0)
        c.paint_rock(rock, wall, top, top_z=L.TOP - 4.0)
        if kind == "log":
            fallen_giant(c, s0, s1)
        elif kind == "lava":
            for sd in (-1, 1):
                strip = []
                s = s0 + 4.0
                while s < s1 - 4.0:
                    q = c.at(s)
                    off = c.width / 2 + 2.2
                    strip.append((q.p.x + q.r.x * sd * off, q.p.y + q.r.y * sd * off, 1.6, q.p.z - 0.15))
                    s += 4.0
                c.ribbon(name + " Lava %d" % sd, strip, 1.6, 0, c.lib("volcano_lava", "lava"), role="visual", steps=2)
            for k in range(3):
                q = c.at(s0 + (s1 - s0) * (k + 0.5) / 3)
                g = c.game(q.p.x + q.r.x * (c.width / 2 + 2.2), q.p.y + q.r.y * (c.width / 2 + 2.2), q.p.z + 0.2)
                c.entity("bubbles", x=g[0], y=g[1], z=g[2], r=1.0, molten=True)
                c.entity("steam", x=g[0], y=g[1], z=g[2])
            for s in (s0, s1):
                q = c.at(s)
                g = c.game(q.p.x, q.p.y, q.p.z + 0.5)
                c.entity("steam", x=g[0], y=g[1], z=g[2])
        else:
            for k, s in enumerate((s0 - 1.0, s1 + 1.0)):
                q = c.at(s)
                rot = math.atan2(q.r.y, q.r.x)
                for sd in (-1, 1):
                    x, y = q.p.x + q.r.x * sd * (half + 1.6), q.p.y + q.r.y * sd * (half + 1.6)
                    box(c, "%s Jamb %d %d" % (name, k, sd), x, y, 1.6, 2.2, q.p.z - 1.0, q.p.z + 11.0,
                        ("jungle_temple", "wall"), rot=rot)
                box(c, "%s Lintel %d" % (name, k), q.p.x, q.p.y, half + 3.4, 2.4, q.p.z + 10.0, q.p.z + 12.6,
                    ("jungle_temple", "wall"), rot=rot)
                c.place(props.idol_head(c), q.p.x, q.p.y, q.p.z + 12.6, rot=math.atan2(q.t.y, q.t.x) + math.pi * k,
                        role="visual")
            for k in range(3):
                q = c.at(s0 + (s1 - s0) * (k + 0.5) / 3)
                for sd in (-1, 1):
                    x, y = q.p.x + q.r.x * sd * (half - 0.6), q.p.y + q.r.y * sd * (half - 0.6)
                    g = c.game(x, y, q.p.z + 4.2)
                    c.entity("torch", x=g[0], y=g[1], z=g[2])


def fallen_giant(c, s0, s1):
    """The Fallen Giant: a colossal hollow trunk lying through the ridge, the road running
    inside it, its broken top and its root plate standing out at the two ends, the
    dinosaurs' lanterns hung in it, moss over it."""
    ro, ri = 13.0, 11.0
    lift = ri * 0.42
    a = c.at(s0 - 8.0)
    bm = bmesh.new()
    n = 20
    rings = []
    m = max(6, int((s1 - s0 + 16.0) / 3.0))
    frames = []
    for k in range(m + 1):
        f = k / m
        q = c.at(s0 - 8.0 + (s1 - s0 + 16.0) * f)  # (it follows the road, bending with it)
        side = Vector((q.r.x, q.r.y, 0.0)).normalized()
        c0 = Vector((q.p.x, q.p.y, q.p.z + lift))
        frames.append((c0, side, q))
        lump = 1.0 + 0.04 * math.sin(f * 17.0)
        outer = [bm.verts.new(c0 + (side * math.cos(t) + Vector((0, 0, math.sin(t)))) * ro * lump)
                 for t in (j * math.tau / n for j in range(n))]
        inner = [bm.verts.new(c0 + (side * math.cos(t) + Vector((0, 0, math.sin(t)))) * ri)
                 for t in (j * math.tau / n for j in range(n))]
        rings.append((outer, inner))
    for (o0, i0), (o1, i1) in zip(rings, rings[1:]):
        for j in range(n):
            jj = (j + 1) % n
            bm.faces.new((o0[j], o0[jj], o1[jj], o1[j]))
            bm.faces.new((i0[j], i1[j], i1[jj], i0[jj]))
    for (oo, ii), flip in ((rings[0], True), (rings[-1], False)):
        for j in range(n):
            jj = (j + 1) % n
            f = (oo[j], ii[j], ii[jj], oo[jj])
            bm.faces.new(f if flip else tuple(reversed(f)))
    o, side, qa = frames[0]
    end, side_e, qb = frames[-1]
    ax = Vector((qa.t.x, qa.t.y, 0.0)).normalized()
    zc = o.z
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    log = c.mesh_object("Fallen Giant", bm, "Props", "both")
    c.assign(log, c.lib("palm_bark", "wall"))
    # The root plate at one end, the broken top at the other.
    for k in range(9):
        t = k * math.tau / 9 + 0.3
        d = (side * math.cos(t) + Vector((0, 0, math.sin(t)))).normalized()
        if d.z < -0.5:
            continue
        p0 = o + d * ro * 0.9
        p1 = p0 + d * (7.0 + 3.0 * math.sin(k * 2.1)) - ax * 3.0
        cone(c, "Giant Root %d" % k, p1.x, p1.y, 1.6, min(p0.z, p1.z) - 1.0, abs(p1.z - p0.z) + 4.0,
             ("bog_root", "wall"), segs=5, role="visual")
    for k in range(5):
        t = k * math.tau / 5 + 1.0
        d = (side_e * math.cos(t) + Vector((0, 0, math.sin(t)))).normalized()
        if d.z < -0.3:
            continue
        p = end + d * (ro - 1.0) + Vector((qb.t.x, qb.t.y, 0.0)) * 1.0
        cone(c, "Giant Splinter %d" % k, p.x, p.y, 1.8, p.z - 1.5, 4.0 + 2.0 * (k % 2), ("palm_bark", "wall"), segs=4,
             role="visual")
    # Lanterns hung inside, and a carved frame of bones at the near mouth.
    s = s0 + 6.0
    k = 0
    while s < s1 - 4.0:
        q = c.at(s)
        sd = 1 if k % 2 else -1
        g = c.game(q.p.x + q.r.x * sd * (c.width / 2 + 1.5), q.p.y + q.r.y * sd * (c.width / 2 + 1.5), q.p.z + 6.0)
        c.entity("torch", x=g[0], y=g[1], z=g[2])
        s += 12.0
        k += 1
    q = c.at(s0 - 6.0)
    c.place(sp.horned_skull(c), q.p.x, q.p.y, zc + ro + 0.6, rot=math.atan2(-q.t.y, -q.t.x), scale=1.8, role="visual")


def facing(spurs, name):
    """The way a landmark at the end of its spur faces (back down the spur), as a box's
    turn: its local x across the spur."""
    (ex, ey), _ = spurs[name]
    gx, gy = L.GATES[name]
    return math.atan2(gy - ey, gx - ex) + math.pi / 2


def landmarks(c, ground, spurs):
    """Each lobe's landmark, its gateway in front of it."""
    # Cascade Caverns' cave mouth beside the falls; Ember Peak's lava-lit tunnel.
    for name, key, rock in (("Cave Mouth", "cascade", ("jungle_mossstone", "wall")),
                            ("Tunnel Mouth", "ember", ("magma_rock", "wall"))):
        gx, gy = L.GATES[key]
        rot = facing(spurs, key)
        z0 = ground(gx - 8 * math.cos(rot - math.pi / 2), gy - 8 * math.sin(rot - math.pi / 2))
        box(c, name, gx, gy, 9.0, 2.0, z0 - 1.0, z0 + 11.0, ("dark_corridor", "wall"), rot=rot, role="visual")
        for side in (-1, 1):
            px, py = gx + side * 8.0 * math.cos(rot), gy + side * 8.0 * math.sin(rot)
            box(c, name + " Jamb %d" % side, px, py, 1.6, 2.6, z0 - 1.0, z0 + 12.0, rock, rot=rot)
        box(c, name + " Lintel", gx, gy, 10.0, 2.8, z0 + 11.0, z0 + 14.0, rock, rot=rot)
    gx, gy = L.GATES["ember"]
    rot = facing(spurs, "ember")
    z0 = ground(gx, gy)
    box(c, "Tunnel Lava", gx + 1.5 * math.cos(rot - math.pi / 2), gy + 1.5 * math.sin(rot - math.pi / 2), 7.0, 0.6, z0 - 3.0,
        z0 + 2.0, ("volcano_lava", "wall"), rot=rot, role="visual")
    # The volcano smoking beyond Ember's cliffs.
    vx, vy = 430.0, -400.0
    volc = c.rock_mass("Volcano", vx, vy, 120.0, 110.0, 200.0, z0=60.0, n=18, seed=5,
                       bands=[(1.0, 0.0), (0.7, 0.5), (0.4, 0.85), (0.25, 1.0)], base=60.0)
    c.assign(volc, c.lib("magma_rock", "wall"))
    gx2, gy2, gz2 = c.game(vx, vy, 202.0)
    c.entity("eruption", x=gx2, y=gy2, z=gz2, period=14.0, offset=3.0)
    # Ember's lava pools, ringed with black rock, bubbling and steaming.
    for k, (px, py, pr) in enumerate(L.LAVA):
        g = ground(px, py)
        c.disc("Lava Pool %d" % k, px, py, pr, g - 0.2, c.lib("volcano_lava"), coll="Props", role="visual", n=18, wobble=0.25,
               seed=11 + k)
        for j in range(5):
            a = j * math.tau / 5 + k
            cone(c, "Lava Rim %d %d" % (k, j), px + (pr + 2.0) * math.cos(a), py + (pr + 2.0) * math.sin(a), 2.2, g - 0.8,
                 2.6 + j % 2, ("obsidian_cliff", "wall"), segs=5)
        gx, gy, gz = c.game(px, py, g + 0.2)
        c.entity("bubbles", x=gx, y=gy, z=gz, r=pr * 0.8, molten=True)
        c.entity("steam", x=gx, y=gy, z=gz)
    # Bonebog Pyramid: its tip above the bog.
    px, py = L.PYRAMID
    cone(c, "Pyramid Tip", px, py, 14.0, WATER_Z - 2.0, 18.0, ("sandstone_block", "wall"))


def ruined(c, ground, spurs):
    """After Cinderjaw's attack: his Scar, the Burnt Gorge's far end, smoke and rubble."""
    sx, sy = L.SCAR
    for k in range(9):
        a = k * math.tau / 9
        if abs(math.sin(a) - 1.0) < 0.35:
            continue  # (its mouth, towards the valley)
        px, py = sx + 17.0 * math.cos(a), sy + 17.0 * math.sin(a)
        cone(c, "Scar Rock %d" % k, px, py, 6.0 + 2.0 * math.sin(k * 2.3), ground(px, py) - 1.0, 12.0 + 6.0 * math.cos(k * 1.7),
             ("obsidian_cliff", "wall"), segs=5)
    g = ground(sx, sy)
    c.disc("Scar Lava", sx, sy - 4.0, 9.0, g + 0.25, c.lib("volcano_lava"), coll="Props", role="visual", n=18, wobble=0.2, seed=7)
    gx, gy, gz = c.game(sx, sy - 4.0, g + 1.0)
    c.entity("eruption", x=gx, y=gy, z=gz, period=9.0, offset=1.0)
    for k in range(4):
        px, py = sx + (k - 1.5) * 9.0, sy + 12.0
        ruin.smoke(c, px, py, ground(px, py) + 0.2)
    # The gorge's far end: it bends out of sight (the passage on starts just before it).
    box(c, "Gorge Bend", gorge_x(GORGE_END + 25.0), GORGE_END + 25.0, GORGE_HW + 24.0, 6.0, 0.0, RIM_Z + 10.0,
        ("obsidian_cliff", "wall"))
    for k, y in enumerate((300.0, 350.0, 400.0)):
        x = gorge_x(y) + (GORGE_HW - 2.0) * (1 if k % 2 else -1)
        ruin.smoke(c, x, y, ground(x, y) + 0.2)
    # Rubble at the cave and tunnel mouths.
    for name in ("cascade", "ember"):
        gx, gy = L.GATES[name]
        rot = facing(spurs, name)
        for side in (-1, 1):
            x, y = gx + side * 16.0 * math.cos(rot), gy + side * 16.0 * math.sin(rot)
            ruin.rubble(c, "%s Rubble %d" % (name, side), x, y, ground, ("valley_cliff", "wall"), seed=len(name) + side)


def to_road(c, x, y):
    """The way from (x, y) to the nearest of the main road (a pen's gate faces it)."""
    q, _ = c.nearest(x, y)
    return math.atan2(q.p.y - y, q.p.x - x)


def three_stones(c, ground):
    """The pen (its gate is the game's) and a ring of standing stones round each switch."""
    px, py = PEN
    puzzle_kit.pen(c, "three_stones", "Pen", px, py, to_road(c, px, py), PEN_HALF, PEN_GAP, ("sandstone_block", "wall"),
                   ground(px, py), height=5.0)
    puzzle_kit.switches(c, "three_stones", STONES, ground, ring_mat=("sandstone_block", "wall"))


def entrances(c):
    """Where the main road crosses into each lobe: [{s, frm, to}], s along the road."""
    out = []
    prev = lobe_at(c.S[0].p.x, c.S[0].p.y)
    for smp in c.S:
        cur = lobe_at(smp.p.x, smp.p.y)
        if cur != prev:
            out.append({"s": smp.s, "frm": prev, "to": cur})
            prev = cur
    return out


def gates(c, ground):
    """Each lobe's sign where the road comes into it, so you know the course's world from
    its threshold: the swamp through a giant's rib cage, Ember between smoking basalt
    stacks, the Cascade under a temple lintel, Riverbend between two great palms."""
    for k, e in enumerate(entrances(c)):
        to, s = e["to"], e["s"] + 10.0
        for _ in range(40):  # (out of a tunnel first, into the pocket)
            q = c.at(s)
            if L.wall_sd(q.p.x, q.p.y) < -14.0:
                break
            s += 4.0
        q = c.at(s)
        half = q.w / 2
        side = lambda sd, off=0.0: (q.p.x + q.r.x * sd * (half + off), q.p.y + q.r.y * sd * (half + off))
        head = math.atan2(q.t.y, q.t.x)
        if to == "bonebog":
            bs.rib_cage(c, None, s - 14.0, s + 22.0, "Bonebog Ribs %d" % k, spine_up=13.0, reach=half + 7.0, every=6.0)
        elif to == "ember":
            for sd in (-1, 1):
                x, y = side(sd, 5.0)
                c.place(props.basalt_columns(c), x, y, ground(x, y) - 0.3, rot=head, scale=1.6)
                x, y = side(sd, 2.5)
                c.place(sp.stone_brazier(c), x, y, ground(x, y) - 0.1)
                gx, gy, gz = c.game(x, y, ground(x, y) + 1.6)
                c.entity("torch", x=gx, y=gy, z=gz)
        elif to == "cascade":
            for sd in (-1, 1):
                x, y = side(sd, 2.5)
                c.place(props.ruin_column(c, 0), x, y, ground(x, y) - 0.2, scale=1.5)
            x0, y0 = side(-1, 3.5)
            x1, y1 = side(1, 3.5)
            zt = max(ground(x0, y0), ground(x1, y1)) + 9.5
            box(c, "Cascade Lintel %d" % k, (x0 + x1) / 2, (y0 + y1) / 2, half + 4.5, 1.3, zt, zt + 1.8,
                ("jungle_temple", "wall"), rot=math.atan2(q.r.y, q.r.x), role="visual")
        elif to == "riverbend":
            for sd in (-1, 1):
                x, y = side(sd, 3.5)
                c.place(props.palm(c, 15.0, 2.0, 2), x, y, ground(x, y) - 0.2, rot=head + sd)


def dress(c, ground, spurs):
    """The paint pass, lobe by lobe, each with its course's own things. After the attack:
    the same trees charred where the fire fell, the undergrowth burnt away."""
    taken = paint.Taken([(L.CAMP[0], L.CAMP[1], L.CAMP[2] + 6.0), (*L.PYRAMID, 18.0), (*PEN, 18.0), (*RETURN, 18.0),
                         (*SECRET, 16.0), *((x, y, 30.0) for x, y in L.FALLS), *((x, y, r + 8.0) for x, y, r, _ in L.LAKES), *((x, y, 10.0) for x, y in STONES),
                         *((e[0], e[1], 16.0) for e, _ in spurs.values()), *((x, y, 22.0) for x, y in L.GATES.values()),
                         *((x, y, r + 6.0) for x, y, r in L.POOLS), *((x, y, r + 8.0) for x, y, r in L.LAVA),
                         (*L.SCAR, 30.0)])

    def inside(x, y):
        if L.wall_sd(x, y) > -8:
            return False
        if L.river_d(x, y)[0] < RIVER_HW + 5:
            return False
        if RUIN and abs(x - gorge_x(y)) < GORGE_HW + 14 and y > L.GORGE[1]:
            return False
        return True

    def lobe(name):
        return lambda x, y: inside(x, y) and lobe_at(x, y) == name

    def bank(x, y):
        return inside(x, y) and L.river_d(x, y)[0] < RIVER_HW + 22

    rmax = 420.0
    # Rocks at the cliffs' feet, lobe by lobe.
    for name, mat in (("riverbend", "valley_cliff"), ("cascade", "jungle_mossstone"), ("ember", "volcano_basalt"),
                      ("bonebog", "bog_dark_stone")):
        def foot(x, y, n=name):
            return lobe(n)(x, y) and L.wall_sd(x, y) > -30

        for v in range(2):
            paint.scatter(c, props.boulder(c, mat, v), 8, rmax, foot, ground, taken, 90 + v + len(name), room=4.0,
                          scale=(1.0, 2.4))
    # Riverbend: palms along the river and the road, jungle trees.
    palms = [props.palm(c, 10.0 + 1.5 * v, 1.3 + 0.5 * v, v) for v in range(3)]
    rb = lobe("riverbend")
    for v, p in enumerate(palms):
        paint.scatter(c, p, 20, rmax, lambda x, y: bank(x, y) and lobe_at(x, y) in ("riverbend", "camp"), ground, taken, 20 + v,
                      room=4.0, scale=(0.9, 1.4), road_margin=5.0, trunk=(0.6, 8.0))
        paint.scatter(c, p, 14, rmax, rb, ground, taken, 10 + v, room=4.0, near_road=(5.0, 14.0), scale=(0.9, 1.4),
                      trunk=(0.6, 8.0))
    for v in range(2):
        paint.scatter(c, props.jungle_tree(c, v), 22, rmax, rb, ground, taken, 30 + v, room=5.0, scale=(1.0, 1.6),
                      road_margin=6.0, trunk=(0.8, 6.0))
    # Cascade: a jungle canyon: giant and grand trees, big-leaf plants, temple ruins.
    cas = lobe("cascade")
    for v in range(2):
        paint.scatter(c, props.giant_tree(c, v), 5, rmax, cas, ground, taken, 60 + v, room=16.0, scale=(0.9, 1.2),
                      road_margin=12.0, trunk=(3.0, 14.0))
        paint.scatter(c, props.grand_tree(c, v), 10, rmax, cas, ground, taken, 62 + v, room=10.0, scale=(1.2, 1.6),
                      road_margin=9.0, trunk=(1.6, 10.0))
        paint.scatter(c, props.jungle_tree(c, v), 30, rmax, cas, ground, taken, 64 + v, room=5.0, scale=(1.1, 1.9),
                      road_margin=6.0, trunk=(0.8, 6.0))
        paint.scatter(c, props.big_leaf_plant(c, v), 40, rmax, cas, ground, taken, 66 + v, room=2.5, role="visual")
    for v, p in enumerate((props.ruin_column(c, 0), props.ruin_column(c, 1), props.ruin_blocks(c, 0), props.stele(c, 0),
                           props.idol_head(c))):
        paint.scatter(c, p, 5, rmax, cas, ground, taken, 70 + v, room=5.0, near_road=(5.0, 24.0))
    # Ember: charred trees, basalt columns, glowing crystals, smoking vents.
    em = lobe("ember")
    paint.scatter(c, props.dead_tree(c), 30, rmax, em, ground, taken, 80, room=5.0, scale=(1.0, 1.7), road_margin=5.0,
                  trunk=(0.6, 6.0))
    paint.scatter(c, props.basalt_columns(c), 10, rmax, em, ground, taken, 81, room=7.0, road_margin=7.0)
    paint.scatter(c, props.crystals(c), 12, rmax, em, ground, taken, 82, room=4.0, role="visual")
    for x, y in paint.scatter(c, props.boulder(c, "volcano_basalt", 2), 8, rmax, em, ground, taken, 83, room=6.0):
        gx, gy, gz = c.game(x, y, ground(x, y) + 1.0)
        c.entity("steam", x=gx, y=gy, z=gz)
    # Bonebog: swamp trees, reeds and cattails round the pools, lily pads on them, glowing
    # caps, skulls and bones.
    bog = lobe("bonebog")

    def shore(x, y):
        return bog(x, y) and any(abs(math.hypot(x - px, y - py) - pr - 6) < 6 for px, py, pr in L.POOLS)

    for v in range(2):
        paint.scatter(c, props.swamp_tree(c, v), 24, rmax, bog, ground, taken, 40 + v, room=6.0, scale=(1.0, 1.6),
                      road_margin=6.0, trunk=(0.9, 6.0))
        paint.scatter(c, props.cattails(c, v), 30, rmax, shore, ground, taken, 42 + v, room=2.0, role="visual")
    paint.scatter(c, props.reeds(c), 50, rmax, shore, ground, taken, 44, room=2.0, role="visual")
    paint.scatter(c, props.glow_caps(c), 30, rmax, bog, ground, taken, 45, room=2.0, role="visual")
    paint.scatter(c, props.skull(c), 10, rmax, bog, ground, taken, 46, room=4.0, road_margin=4.0)
    for k, (px, py, pr) in enumerate(L.POOLS):
        for j in range(int(pr / 4)):
            a = j * 2.39996 + k
            r = pr * 0.8 * math.sqrt((j + 0.5) / (pr / 4))
            x, y = px + r * math.cos(a), py + r * math.sin(a)
            if math.hypot(x - L.PYRAMID[0], y - L.PYRAMID[1]) > 18 and paint.road_clear(c, x, y, 3.0):
                c.place(props.lily_pad(c, j % 3), x, y, WATER_Z + 0.03, rot=a * 3.0, role="visual")
    # The swamp's big things: giant trees, stilt huts on the shores, sunken timber and
    # crocodiles in the pools, bone piles, torch posts along its road.
    paint.scatter(c, sp.swamp_giant(c, 0), 6, rmax, bog, ground, taken, 47, room=14.0, scale=(0.8, 1.1),
                  road_margin=12.0, trunk=(2.5, 12.0))
    for v in range(2):
        paint.scatter(c, sp.bone_pile(c, v), 5, rmax, bog, ground, taken, 48 + v, room=5.0, road_margin=5.0)
    big = sorted(L.POOLS, key=lambda q: -q[2])
    for k, (px, py, pr) in enumerate(big[:3]):
        a = 0.9 + 2.1 * k
        x, y = px + (pr + 9.0) * math.cos(a), py + (pr + 9.0) * math.sin(a)
        if paint.road_clear(c, x, y, 9.0) and taken.clear(x, y, 6.0):
            c.place(sp.stilt_hut(c, k % 2), x, y, ground(x, y) - 0.4, rot=a + math.pi)
            taken.add(x, y, 7.0)
    for k, (px, py, pr) in enumerate(big[:5]):
        a = 2.4 * k + 0.4
        x, y = px + pr * 0.45 * math.cos(a), py + pr * 0.45 * math.sin(a)
        if math.hypot(x - L.PYRAMID[0], y - L.PYRAMID[1]) > 20:
            c.place(sp.sunken_timber(c, k % 2), x, y, WATER_Z - 0.3, rot=a * 1.7, role="visual")
    for k, (px, py, pr) in enumerate(big[:2]):
        x, y = px - pr * 0.3, py + pr * 0.35
        c.place(sp.croc(c), x, y, WATER_Z - 0.25, rot=1.1 + 2.0 * k, role="visual")
    torch = sp.torch_post(c)
    for e in entrances(c):
        if e["to"] != "bonebog":
            continue
        for k in range(6):
            q = c.at(e["s"] + 20.0 + 34.0 * k)
            if lobe_at(q.p.x, q.p.y) != "bonebog":
                break
            sd = 1 if k % 2 else -1
            x, y = q.p.x + q.r.x * sd * (q.w / 2 + 6.5), q.p.y + q.r.y * sd * (q.w / 2 + 6.5)
            c.place(torch, x, y, ground(x, y) - 0.2)
            gx, gy, gz = c.game(x, y, ground(x, y) + 3.2)
            c.entity("torch", x=gx, y=gy, z=gz)
    gates(c, ground)
    # The camp: totems where the road leaves it.
    tot = props.totem(c)
    for side in (-1, 1):
        x, y = L.CAMP[0] + L.CAMP[2] + 4.0, L.CAMP[1] + side * 9.0
        c.place(tot, x, y, ground(x, y) - 0.2, rot=-math.pi / 2)
    # Everywhere that isn't the swamp or the volcano's slope: bushes, ferns, flowers.
    def green(x, y):
        return inside(x, y) and lobe_at(x, y) in ("riverbend", "cascade", "camp")

    for v in range(2):
        paint.scatter(c, props.bush(c, v), 90, rmax, green, ground, taken, 50 + v, room=2.5, role="visual", scale=(0.7, 1.5))
    paint.scatter(c, props.fern(c), 200, rmax, green, ground, taken, 54, room=1.5, role="visual")
    paint.scatter(c, props.flowers(c), 180, rmax, lambda x, y: green(x, y) and lobe_at(x, y) != "cascade", ground, taken, 55,
                  room=1.5, role="visual", sink=0.1)
    if RUIN:
        ruin_kit.char_trees(c, burn, ("Palm", "Jungle Tree", "Grand Tree", "Giant Tree"), chance=0.85, threshold=0.3)
        ruin.burn_away(c, burn, ("Fern", "Flowers", "Bush", "Big Leaf"), threshold=0.3)
        paint.scatter(c, props.log(c, 0), 40, rmax, inside, ground, taken, 13, room=5.0, role="visual", sink=0.3)


if __name__ == "__main__":
    main()
