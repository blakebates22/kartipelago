# The Snow Kingdom, the overworld's second region (v3): built from snow_layout.py's
# pockets (Blake, Oct 26: each world walled off by landscape, the main road one loop through
# them by a threshold each time; see snow_layout.py for the plan).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/snow_region.py [--ruin]      (the bpy module)
#
# (--ruin: after Rimefang's attack. Only the ruin has his lair, the road out through the
# Frozen Pass (his ice across it is the game's, regions.ts's blocker, until he falls), the
# village frozen over, ice shards driven into the fields, the pines frozen solid.)

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)
import pocket_kit  # noqa: E402
from course_kit import lerp, smooth  # noqa: E402
import region_ruin as ruin  # noqa: E402
import puzzle_kit  # noqa: E402
import pocket_build as pb  # noqa: E402
from pocket_build import box, cone  # noqa: E402
import hearthglow_props as hp  # noqa: E402
import summit_props as sp  # noqa: E402
import iceage_props as ia  # noqa: E402
import aurora_props as ap  # noqa: E402
import rift_props as rp  # noqa: E402
import keep_props as kp  # noqa: E402
import villager_homes as vh  # noqa: E402
import valley_village as vv  # noqa: E402
import snow_props as snp_  # noqa: E402
import winter_props as wp  # noqa: E402
import region_paint as paint  # noqa: E402
import snow_layout as SL  # noqa: E402
import snow_dress as sd  # noqa: E402
import carvers_village as cv  # noqa: E402
import snow_sections as ss  # noqa: E402

RUIN = ruin.ON
# (The Frozen Pass Rimefang's attack opened out of the lake: gone. The only way out is the
# smugglers' tunnel from the Ice Cave: Blake, Nov 1.)
BROKEN_WAYS = False
TRACK_ID = ruin.track_id("snow_region") + os.environ.get("KP_REGION_SUFFIX", "")
L = SL.L
HUB = SL.HUB
ENTRY = []  # the way in, up out of the Burnt Gorge (its points)
FLOOR_Z = HUB[3]  # (the village's height: the old name)
RIM_Z = SL.TOP

# The Ice Bells (src/overworld/puzzles.ts): a frost-stone hut on an island in the frozen
# lake, its ice door shut, and three bells out on the ice round it to ring in order (their
# lanterns: one, two, three).
HUT = (-30.0, 148.0)  # (v4: the frozen lake's in the summit now)
HUT_HALF = 10.0
HUT_GAP = 4.5
BELLS = [(-44.0, 136.0), (-14.0, 160.0), (-16.0, 134.0)]  # (none out on the ice now: nothing kept clear for them)
LANTERNS = [1, 2, 3]
# The smugglers' Ice Cave (regions.ts cave): its mouth in the north wall of Aurora's bay, left
# of the crystal spires, facing south down the bay, its yard's gate 11 m out from it (Blake,
# review-snow_region 14 notes 5 and 7, "move the smugglers tunnel to aurora where I pinned",
# "flush on the wall to the left of the crystal structure"; it was in the summit meadow, by
# Brachio's old hot spring).
RETURN = (194.0, 86.5)
RETURN_FACING = -math.pi / 2  # (out of the wall, south)
CAVE_WALL_Y = 89.0  # (the face of the rock it's cut into, against the bay's north wall)
# A secret (regions.ts secret): an old store in Frostveil's bailey, buried under a drift
# (the Desert Tool's).
SECRET = (-140.0, -30.0)

LOOK = {
    # look: (ground, cliff, road, shoulder)
    "hearth": (("snow_ground", "deep_snow"), ("frost_cliff", "wall"), "hearth_cobble", ("snow_ground", "deep_snow")),
    "frostveil": (("snow_ground", "deep_snow"), ("frost_rock", "wall"), "snow_stone_road", ("snow_ground", "deep_snow")),
    "summit": (("summit_snow", "deep_snow"), ("summit_cliff", "wall"), "summit_road", ("summit_snow", "deep_snow")),
    "aurora": (("rift_snow", "deep_snow"), ("glacier_wall", "wall"), "rift_road", ("rift_snow", "deep_snow")),
    "lake": (("snow_ground", "deep_snow"), ("frost_cliff", "wall"), "packed_snow_road", ("snow_ground", "deep_snow")),
    "pass": (("snow_ground", "deep_snow"), ("frost_cliff", "wall"), "packed_snow_road", ("snow_ground", "deep_snow")),
}


# v4 (Blake, Oct 28: the walls with ledges, like Cascade Caverns'): the walls rise in
# tiers (pocket_kit.terrace), a bed of each world's rock to a tier, foot to rim.
STRATA = {
    "hearth": ["frost_stone", "frost_cliff", "frost_rock", "summit_cliff", "frost_cliff"],
    "frostveil": ["frost_rock", "frost_cliff", "summit_rock", "frost_cliff", "summit_cliff"],
    "summit": ["summit_rock", "summit_cliff", "frost_rock", "summit_cliff", "summit_rock"],
    "aurora": ["rift_rock", "rift_cliff", "rift_stone", "rift_cliff", "rift_rock"],
    "lake": ["frost_cliff", "frost_rock", "frost_stone", "frost_cliff", "summit_cliff"],
    "pass": ["frost_rock", "frost_cliff", "summit_cliff", "frost_cliff", "frost_rock"],
}


def _natural(x, y):
    h = SL.natural(x, y)
    tz = L.tunnel_floor(x, y)
    if tz is not None:
        h = min(h, tz - 0.25)  # (under a tunnel's rock: flush under its road, out to the walls)
    # (No island in the lake any more: the Ice Bells are long gone, and it left the lake a
    # thin ring of ice round it; review-snow_region 9 note 21, "make the frozen lake larger".)
    if RUIN and BROKEN_WAYS:
        # The Frozen Pass: a slot through the mountains east, out of the lake.
        (ax, ay), (bx, by) = SL.FROZEN_PASS, SL.PASS_END
        dd, t = pb_seg(x, y, (ax - 30.0, ay + 10.0), (bx, by))
        if dd < 30:
            h = lerp(h, 58.3 + 6.0 * t, smooth((30.0 - dd) / 12.0))  # (up from the glacier's tongue)
    if RUIN:
        # Rimefang's lair: a cleft in the summit's north wall.
        lx, ly = SL.LAIR
        dd, t = pb_seg(x, y, (lx, ly - 40.0), (lx, ly + 26.0))
        if dd < 26:
            h = lerp(h, 73.0 + 2.0 * t, smooth((26.0 - dd) / 10.0))
    # Frostveil's cove, carved back into the mountain west of its courtyard (note 5).
    fx, fy, fr, fz = SL.FROST_COVE
    d = math.hypot(x - fx, y - fy)
    if d < fr + 12.0:
        h = min(h, lerp(fz, h, smooth((d - fr) / 12.0)))
    # (No lane out of the old square to Hearthglow's portal any more: its gateway's spur
    # comes off the street like every other's; Blake, review-snow_region 9 note 14.)
    # The pads Hearthglow's cottages stand on, up the hollow's walls (snow_dress).
    return sd.pad_height(x, y, h)


# The ways in to the gateways cut level with the road (pocket_kit.Notches: a gateway's
# spur mustn't climb a wall).
NOTCHES = pocket_kit.Notches(SL.route_points(), dict(SL.GATES, **({"lair": SL.LAIR} if RUIN else {})))


def pb_seg(x, y, a, b):
    from pocket_kit import seg_d
    return seg_d(x, y, a, b)


def natural(x, y):
    return NOTCHES.apply(_natural(x, y), x, y)


class _RoadNear:
    """How far a point is from the ring road's middle line, quickly (a grid of its
    segments): (distance, metres along it, side +1 left / -1 right)."""

    def __init__(self, pts, cell=24.0):
        self.cell = cell
        self.segs = []
        s = 0.0
        self.grid = {}
        for i, p in enumerate(pts):
            q = pts[(i + 1) % len(pts)]
            ln = math.hypot(q[0] - p[0], q[1] - p[1])
            self.segs.append((p[0], p[1], q[0], q[1], s, ln))
            n = max(1, int(ln / (cell * 0.5)))
            for k in range(n + 1):
                t = k / n
                gx, gy = int((p[0] + (q[0] - p[0]) * t) // cell), int((p[1] + (q[1] - p[1]) * t) // cell)
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        self.grid.setdefault((gx + dx, gy + dy), set()).add(i)
            s += ln

    def near(self, x, y):
        best = (1e9, 0.0, 1)
        for i in self.grid.get((int(x // self.cell), int(y // self.cell)), ()):
            ax, ay, bx, by, s, ln = self.segs[i]
            dx, dy = bx - ax, by - ay
            t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / max(ln * ln, 1e-9)))
            d = math.hypot(x - ax - dx * t, y - ay - dy * t)
            if d < best[0]:
                best = (d, s + ln * t, 1 if dx * (y - ay) - dy * (x - ax) > 0 else -1)
        return best


ROAD = _RoadNear(SL.route_points())
# The grass verge up the climb (review-snow_region 10 note 6, "lets add a grass strip
# here"): along the road either way of Blake's pin, on its side, from the shoulder out to
# the foot of the wall.
_VERGE_PIN = (-147.1, 116.6)
_VD, _VS, _VSIDE = ROAD.near(*_VERGE_PIN)


def thaw_grass(x, y, nz):
    """Grass through the snow on the summit: in patches well off the road (none in thin
    slivers along its edge, note 8: "this little green strip looks weird"), and the verge
    up the climb."""
    d, s, side = ROAD.near(x, y)
    if side == _VSIDE and abs(s - _VS) < 34.0 + 3.0 * math.sin(s / 7.0) and 8.6 < d < 22.0 and nz > 0.85:
        return True
    return (d > 16.0 and nz > 0.93 and L.wall_sd(x, y) < -9.0
            and math.sin(x / 11.0 + 0.4) * math.cos(y / 9.0) + 0.4 * math.sin((x + y) / 5.0) > 0.75)


def classify(c, n, info):
    look = L.look_at(c.x, c.y)
    ground, cliff, _, _ = LOOK[look]
    # (on the tiered walls only the shelves' flat tops are ground)
    if n.z < (0.8 if L.wall_info(c.x, c.y)["t"] > 0.05 else 0.62):
        return (pb.strata(L, c, n, STRATA), "wall")
    if SL.crevasse_cut(c.x, c.y) > 1.5:
        # (Its floor puts you back on the road: review-snow_region 15 note 6, "lets make it so if
        # I fall down here, I respawn back on the road".)
        return ("glacier_ice", "wall") if n.z < 0.8 else ("cavern_ice", "abyss" if SL.crevasse_cut(c.x, c.y) > 3.0 else "ice")
    if not RUIN and look == "summit" and thaw_grass(c.x, c.y, n.z):
        return ("thaw_grass", "grass")  # (the deep thaw: grass through the snow)
    if not RUIN and look == "aurora" and n.z > 0.97 and math.sin(c.x / 21.0) * math.cos(c.y / 15.0 + 0.7) > 0.45:
        return ("mirror_ice", "ice")  # (the rift's mirror ice)
    if SL.hollow_floor(c.x, c.y):
        return ("snow_ground", "packed_snow")  # (the Ice Hollow's floor, driven on)
    lx, ly, lr, lz = SL.LAKE
    if math.hypot(c.x - lx, c.y - ly) < lr + 2 and c.z < lz + 0.1:
        return ("lake_ice", "ice")
    if RUIN and look in ("hearth", "summit", "frostveil") and math.sin(c.x / 23.0) * math.cos(c.y / 19.0) > 0.55:
        return ("berg_ice", "ice")  # (Rimefang's frost)
    return pb.transition(L.look_weights(c.x, c.y), lambda lk: LOOK[lk][0])


# Boulders across the way in behind Frostveil's north-east tower, between it and the cliff
# (Blake, review-snow_region 14 note 8, "we need to put some rocks here so you cant get stuck
# behind the castle"): Blender (x, y, variant, scale).
CASTLE_BACK = [(-180.0, 57.5, 1, 1.3), (-175.5, 58.0, 0, 1.45), (-171.2, 57.6, 1, 1.35),
               # (and the last gap, between them and the road by the tower: review-snow_region 15
               # notes 7, 8, "these rocks dont cover the out of bounds", "this is where the rocks
               # need to be")
               (-167.6, 56.6, 0, 0.85), (-167.8, 59.4, 1, 0.75)]


def castle_back(c, ground):
    n = 0
    for k, (x, y, v, s) in enumerate(CASTLE_BACK):
        if not paint.road_clear(c, x, y, 1.0):
            print("  (castle back boulder %d: on the road)" % k)
            continue
        # (Standing up off the terrace they close, not seated on the low ground by the road:
        # their tops a good 2.5 m over the terrace.)
        z = max(ground(x + 2.4 * s * math.cos(t), y + 2.4 * s * math.sin(t)) for t in [j * 0.785 for j in range(8)])
        c.place(sp.boulder(c, v), x, y, z - 0.6, rot=0.15 * k, scale=s, coll="Props")
        n += 1
    print("castle back: %d boulders" % n)


def ice_cave(c, ground):
    """The smugglers' Ice Cave's mouth in the face of Aurora's north wall: a dark way into
    the rock framed in old timbers, lanterns on poles either side, their sledges and sacks
    by it. (The game draws the mouth's rocks round the cave's spot, 2 m in from it.)"""
    import ice_yard as iy

    x, y = RETURN
    wy = CAVE_WALL_Y
    z = ground(x, wy - 1.0)
    # (A crag of the wall's rock heaped against it, its face sheer to the bay's floor, the
    # mouth cut in that: the north wall there only slopes up.)
    rk = c.rock_mass("Ice Cave Rock", x, wy + 6.5, 9.0, 6.5, z + 17.0, z0=z - 3.0, n=18, seed=14, angle=0.0, base=z)
    c.assign(rk, c.lib("frost_cliff", "wall"))
    box(c, "Ice Cave Mouth", x, wy + 0.2, 2.6, 0.9, z - 1.0, z + 5.6, ("dark_corridor", "wall"), role="visual")
    for sd in (-1, 1):
        px = x + sd * 3.4
        box(c, "Ice Cave Post %d" % sd, px, wy - 0.4, 0.3, 0.3, ground(px, wy - 0.4) - 0.5, z + 5.8, ("timber_beam", "wall"))
        lx, ly = x + sd * 6.0, wy - 2.6
        # (its lamp hung out toward the mouth)
        c.place(iy.lantern_pole(c), lx, ly, ground(lx, ly) - 0.1, rot=sd * math.pi / 2, coll="Props")
        g = c.game(lx - sd * 0.85, ly, ground(lx, ly) + 3.45)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
    box(c, "Ice Cave Lintel", x, wy - 0.4, 0.35, 4.0, z + 5.8, z + 6.4, ("timber_beam", "wall"), rot=math.pi / 2, role="visual")
    # (The smugglers' stock: crates and barrels, no sacks, review-snow_region 14 note 4, 15 note 4.)
    import gulch_props as gp_

    stock = [gp_.crate_stack(c, 0), gp_.barrel(c, 0), gp_.crate_stack(c, 1), gp_.barrel(c, 1), gp_.barrel(c, 0), gp_.crate_stack(c, 0)]
    for k, (dx, dy, rot) in enumerate(((-7.6, -5.0, 0.3), (-9.2, -3.6, 1.1), (7.8, -5.4, -0.5), (9.4, -3.8, 0.4), (8.6, -7.2, 2.0),
                                       (-8.4, -7.0, -0.8))):
        px, py = x + dx, wy + dy
        z = min(ground(px + 0.8 * math.cos(a), py + 0.8 * math.sin(a)) for a in (0.0, 1.57, 3.14, 4.71))
        c.place(stock[k], px, py, z - 0.05, rot=rot, coll="Props")
    px, py = x - 9.0, wy - 8.0
    c.place(snp_.sled(c, 0), px, py, ground(px, py) - 0.05, rot=0.8, coll="Props")


def main():
    c = kit.Course(TRACK_ID, "Snow Kingdom (ruined)" if RUIN else "Snow Kingdom", "summit_pass")
    c.route(L.route_points(), width=14.0, bank=5.0)
    kinds = {}
    for look, (ground, cliff, road, shoulder) in LOOK.items():
        kinds[look] = {"mat": road, "shoulder": 1.5, "shoulder_mat": shoulder}
    # v5: the bridge of ice over the crevasse on the glacier.
    kinds["icebridge"] = {"mat": "rift_road", "surface": "road", "shoulder": 0.8, "shoulder_mat": ("glacier_ice", "road"),
                          "barrier": 0.9, "barrier_mat": ("glacier_ice", "wall"), "deck": 3.0,
                          "deck_mat": ("glacier_ice", "wall"), "ground": False}
    c.kinds = kinds

    def label(smp):
        # (The bridge, with its rails, only where the crevasse is deep under the road: not on
        # past its shallow end across the way to Aurora Rift, review-snow_region 13 note 8.)
        if SL.crevasse_d(smp.p.x, smp.p.y) < SL.CREVASSE_HW + 8.0 and max(
                SL.crevasse_cut(smp.p.x + smp.r.x * f * smp.w / 2, smp.p.y + smp.r.y * f * smp.w / 2) for f in (-1.2, 0.0, 1.2)) > 2.0:
            return "icebridge"
        return L.look_at(smp.p.x, smp.p.y)

    c.roads(kit.plan(c, pb.blend_runs(c, list(kit.runs(c, label)), LOOK), "hearth", max_len=160.0))

    snow = ("snow_ground", "deep_snow")
    trail = dict(width=10.0, shoulder=1.2, shoulder_mat=snow)
    cx, cy, cr, cz = HUB
    # The way in: up out of the Burnt Gorge (from the valley, south) through the hollow and
    # onto the road (Blake, Oct 29: the old square's gone, with the village; the hollow is
    # the grand way in to the kingdom, snow_dress.entry_pass).
    # v4b: the way in (Blake, Oct 30: "go higher still"): out of the tunnel onto the
    # Carvers' Peak's summit, round its top, spiralling down its flanks into the carvers'
    # village, and down onto the lap at the pass (snow_layout.LOOKOUT_LINE).
    gorge = [(x, y, z + 0.05) for x, y, z in SL.LOOKOUT_LINE]
    c.side_road("Lookout Road", gorge, "packed_snow_road", "road", width=11.0, shoulder=1.2, shoulder_mat=snow, flush=True,
                ease=10.0)
    ENTRY.extend((p[0], p[1]) for p in gorge)
    # Into Hearthglow's square from the road (its west side).
    vx, vy, vr, vz = SL.VILLAGE
    smp, _ = c.nearest(vx, vy)
    a = math.atan2(smp.p.y - vy, smp.p.x - vx)
    c.side_road("Square Road", pb.line(natural, (smp.p.x, smp.p.y), (vx + (vr - 2.0) * math.cos(a), vy + (vr - 2.0) * math.sin(a)),
                                       z0=smp.p.z, c=c), "hearth_cobble", "road", **trail, flush=True, ease=8.0)
    # (v4c: the Ice Hollow has no lane: its whole floor is packed snow, the land's own
    # (classify), so nothing's laid over the pass's road: Blake, Oct 30.)
    gates = dict(SL.GATES)
    if RUIN:
        gates["lair"] = SL.LAIR
    spots = pb.spurs(c, natural, gates, lambda x, y: LOOK[L.look_at(x, y)][2], trail)
    if RUIN and BROKEN_WAYS:
        # Out of the lake through the Frozen Pass, east.
        smp, _ = c.nearest(*SL.FROZEN_PASS)
        (ax, ay), (bx, by) = SL.FROZEN_PASS, SL.PASS_END
        way = pb.line(natural, (smp.p.x, smp.p.y), (bx - 10.0, by), z0=smp.p.z, c=c)
        c.side_road("Frozen Pass Road", way, "packed_snow_road", "road", **trail)

    # (v4: drawn in, and finer, for the walls' tiers)
    # (v4b: out south to the passage at the Crest's foot)
    X0, X1, Y0, Y1 = -310, 310, -442, 310
    ter = c.terrain("Snow Kingdom", X0, X1, Y0, Y1, 2.5, natural, classify, near=8.0, fade=16.0, verge_fill=1.5)
    sd.level_pads(ter)
    mirror_floor(c, ter)
    global TER
    TER = ter
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 5.0, lambda x, y: natural(x, y) - 0.5, c.lib(*snow))

    def ground(x, y):
        z = c.ground_z(x, y, [ter])
        return natural(x, y) if z is None else z

    lx, ly, lr, lz = SL.LAKE
    c.disc("Frozen Lake", lx, ly, lr + 2.0, lz - 0.05, c.lib("lake_ice", "ice"), role="visual", n=48, wobble=0.06)

    thresholds(c, ground)
    sd.ice_bridge(c, ground)
    village(c, ground, ter)
    # The stone-carvers' village, cut into the switchbacks' terraces (v4b).
    carved = paint.Taken()
    cv.build(c, ground, carved)
    if not RUIN:
        sd.entry_pass(c, ground, ENTRY, carved)
    landmarks(c, ground, spots)
    if RUIN:
        ruined(c, ground)
    # (v4: its walls gone, Blake, review-snow_region 2 note 3, "we need to remove this"; the
    # smugglers' gate stays, for the story, till the Summit's rework gives it a home.)
    puzzle_kit.pen(c, "return", "Ice Cave", *RETURN, RETURN_FACING, 11.0, 4.5, ("frost_stone", "wall"),
                   ground(*RETURN), height=6.0, walls=False)
    ice_cave(c, ground)
    # (No Old Store any more: "we arent going to be using it", review-snow_region 8 notes 1, 13.)
    pb.emit_spots(c, spots)
    # The villagers' homes, in every part of the region (src/overworld/villagers.ts).
    # (Hearthglow's cottages, each set level and solid: the overworld rules, Blake, Oct 29,
    # where they were plain boxes half sunk in the snow.)
    # v4 (Blake, Oct 30: "there are random houses that probably no longer fit ... if there
    # is a house, it needs to match the theme for the section, like how we did for dino
    # valley"): Hearthglow's cottages in Hearthglow; the citadel's town houses in
    # Frostveil; the course's stone lookout huts up the summit; none in the rift or the
    # passes (the ice carvers live in their hollow).
    def home(c, name, x, y, z, rot, k):
        pocket = name.split()[1].lower()
        if pocket in ("frostveil",) and not RUIN:
            hi = sd.level_site(c, x, y, rot, 8.0, 7.5, ground, ter)
            if hi is None:
                return False
            box(c, name + " Footing", x, y, 4.2, 4.0, hi - 2.5, hi + 0.1, ("citadel_dark", "wall"), rot=rot, role="visual")
            c.place(kp.house(c, k % 4), x, y, hi - 0.05, rot=rot + math.pi, coll="Village")
            return True
        if pocket in ("summit", "climb") and not RUIN:
            hi = sd.level_site(c, x, y, rot, 6.5, 5.5, ground, ter)
            if hi is None:
                return False
            # (Ice-age bone huts, not the course's lookout huts: review-snow_region 9 note 22.)
            c.place(ia.bone_hut(c, k % 2), x, y, hi - 0.05, rot=rot, coll="Village")
            g = c.game(x, y, hi + 5.4)
            c.entity("chimney", x=g[0], y=g[1], z=g[2])
            YARDS.append((x, y, rot, k))  # (its yard: hut_yards)
            return True
        v = (1, 4, 2)[k % 3]
        if RUIN:
            w, d = hp.COTTAGE_SIZE[v]
            hi = sd.level_site(c, x, y, rot, w, d, ground, ter)
            if hi is None:
                return False
            box(c, name, x, y, w / 2 - 0.5, d / 2 - 0.5, hi - 1.3, hi + 4.0, ("hearth_stone", "wall"), rot=rot)
            box(c, name + " Ice", x, y, w / 2 + 0.4, d / 2 + 0.4, hi - 1.3, hi + 6.5, ("berg_ice", "wall"), rot=rot + 0.08)
            return True
        smoke = sd.seat_cottage(c, v, x, y, rot, ground, name=name, ter=ter)
        if smoke is None:
            return False
        g = c.game(*smoke)
        c.entity("chimney", x=g[0], y=g[1], z=g[2])
        return True

    # (None in Hearthglow, its street's built: nor Frostveil, review-snow_region 8 note 8.)
    vh.homes(c, L, ground, "snow", home, pockets=["descent", "summit", "climb"], avoid=[(SL.VILLAGE[0], SL.VILLAGE[1], SL.VILLAGE[2] + 24.0), (HUB[0], HUB[1], 30.0)],
             wall=-12.0, per=4, level=3.0, foot=6.5)
    dress(c, ground, spots)
    # (After the summit's ground is all cut: the hunters' camp's levelling raised the land
    # round the boulders and buried them, review-snow_region 15 notes 7, 8.)
    castle_back(c, ground)
    vv.clear_paths(c, LANES)
    # The gorge's far end, back towards the valley: it bends out of sight.
    # (v4b: the way in comes out of a tunnel on the peak's summit now; its mouth is the
    # carvers' village's work.)
    c.entity("snowfall", rate=60, radius=60)

    # (Raced too: the champion's challenge, once round the loop, from this line.)
    c.start_line()
    gts = c.checkpoints(height=10.0)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish(extra={"race": {"laps": 1}})
    print("loop", round(c.length, 1), "gates", len(gts))


def ladder_up(c, ground, at, normal):
    """A timber ladder up the face of the gatehouse wall nearest `at` (facing `normal`),
    from the snow to the wall's top (Blake, review-snow_region 8 note 12: "put a ladder up
    this wall all the way to the top")."""
    import bpy
    import bmesh
    from canyon_props import _beam

    x, y = at
    walls = [o for o in bpy.data.objects if o.name.startswith("Curtain Wall 10.0 10.0")]
    if not walls:
        return
    nx, ny = normal
    # the wall's own top, straight down onto it just inside its face (the nearest wall by
    # its origin can be a different, lower one)
    from mathutils import Vector

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, _n, _i, ob, _m = bpy.context.scene.ray_cast(
        dg, Vector((x - nx * 0.6, y - ny * 0.6, 400.0)), Vector((0, 0, -1))
    )
    if hit and ("Wall" in ob.name or "Gate" in ob.name):
        top = loc.z
    else:
        w = min(walls, key=lambda o: math.hypot(o.location.x - x, o.location.y - y))
        top = w.location.z + 10.0 + 0.4
    print("ladder: up to %.1f on %s" % (top, ob.name if hit else "-"))
    bx, by = x + nx * 1.0, y + ny * 1.0
    z0 = ground(bx, by) - 0.1
    tx, ty = x + nx * 0.25, y + ny * 0.25
    sx, sy = -ny * 0.45, nx * 0.45
    bm = bmesh.new()
    for sd in (-1, 1):
        _beam(bm, (bx + sx * sd, by + sy * sd, z0), (tx + sx * sd, ty + sy * sd, top + 0.6), 0.09)
    n = int((top - z0) / 0.4)
    for k in range(1, n):
        u = k / n
        px, py, pz = bx + (tx - bx) * u, by + (ty - by) * u, z0 + (top + 0.6 - z0) * u
        _beam(bm, (px - sx, py - sy, pz), (px + sx, py + sy, pz), 0.05)
    c.assign(c.mesh_object("Gatehouse Ladder", bm, "Village", "visual"), c.lib("keep_timber"))


def gatehouse(c, ground, s0, s1):
    """Frostveil's gatehouse over the way from Hearthglow, built from the citadel's own
    kit (its stone, slate and teal banners)."""
    half = c.width / 2 + 3.0
    # (No gold plaque: "lame and doesnt match castle vibes", review-snow_region 8 note 6.)
    arch = kp.gate_arch(c, span=2 * half + 6.0, clear=11.0, depth=7.0, gold=False)
    tower = kp.round_tower(c, r=4.8, h=22.0, variant=1)
    small = kp.round_tower(c, r=3.4, h=15.0, variant=0)
    wall = kp.curtain_wall(c, length=8.4, h=11.0, thick=3.0)
    out = kp.curtain_wall(c, length=10.0, h=10.0, thick=3.0)
    for k, s in enumerate((s0 - 4.0, s1 + 4.0)):
        q = c.at(s)
        rot = math.atan2(q.t.y, q.t.x) - math.pi / 2
        c.place(arch, q.p.x, q.p.y, q.p.z - 0.2, rot=rot, role="visual")
        for sd in (-1, 1):
            x, y = q.p.x + q.r.x * sd * (half + 6.5), q.p.y + q.r.y * sd * (half + 6.5)
            zt = min(ground(x + 5.0 * math.cos(t), y + 5.0 * math.sin(t)) for t in [j * math.tau / 16 for j in range(16)])
            c.place(tower, x, y, min(zt, ground(x, y)) - 3.0, rot=rot)
            # The wall out from the tower to the cliff, two lengths and a small tower.
            for j in range(2):
                d = half + 6.5 + 5.0 + 9.6 * j + 5.0
                wx, wy = q.p.x + q.r.x * sd * d, q.p.y + q.r.y * sd * d
                c.place(out, wx, wy, ground(wx, wy) - 0.5, rot=rot + (math.pi if (sd > 0) == (k == 0) else 0.0))
            d = half + 6.5 + 25.0
            tx, ty = q.p.x + q.r.x * sd * d, q.p.y + q.r.y * sd * d
            c.place(small, tx, ty, ground(tx, ty) - 2.0, rot=rot)
            bp = (q.p.x + q.r.x * sd * (half + 1.5) + q.t.x * (2.0 if k == 0 else -2.0) * -1,
                  q.p.y + q.r.y * sd * (half + 1.5) + q.t.y * (2.0 if k == 0 else -2.0) * -1)
            c.place(kp.banner_pole(c), bp[0], bp[1], ground(*bp) - 0.2, rot=rot, coll="Props")
    # The curtain walls either side of the road between the gates, on its shoulders.
    s = s0 + 1.0
    while s < s1 - 1.0:
        q = c.at(s)
        rot = math.atan2(q.t.y, q.t.x)
        for sd in (-1, 1):
            x, y = q.p.x + q.r.x * sd * (half + 2.0), q.p.y + q.r.y * sd * (half + 2.0)
            c.place(wall, x, y, q.p.z - 0.4, rot=rot + (0.0 if sd < 0 else math.pi))
            if int((s - s0) / 8.0) % 2 == 0:
                g = c.game(q.p.x + q.r.x * sd * (half + 0.4), q.p.y + q.r.y * sd * (half + 0.4), q.p.z + 4.5)
                c.entity("torch", x=g[0], y=g[1], z=g[2])
        s += 8.0


def thresholds(c, ground):
    """The Gatehouse (through Frostveil's curtain wall, a castle gate at each end) and the
    ice bores (the Ice Cave onto the glacier, the Ice Gallery in and out of the crystal
    cavern: blue ice, crystals in their walls)."""
    kp.use_palette({"keep_ashlar": "citadel_stone", "keep_ashlar_dark": "citadel_dark", "keep_parapet": "citadel_stone",
                    "keep_gold": "temple_gold", "keep_banner": "banner_teal", "keep_pine": "pine_snow"})
    for name, kind, a, b in L.tunnels:
        s0, s1 = pb.tunnel_span(c, L, a, b)
        if kind == "gatehouse":
            # v4 (Blake, Oct 30: "that bad tan tunnel going into frostveil, it is a massive
            # eye sore ... needs to be done away with and completely reworked"): no rock
            # over it; the road runs open through the cut in the wall, between curtain
            # walls, a gatehouse at each end (towers with slate spires, the gate's arch
            # and banners), the walls running out from the towers to the cliffs.
            gatehouse(c, ground, s0, s1)
            ladder_up(c, ground, (-126.72, -56.01), (-0.65, -0.76))
        elif kind == "ice" and name in ("Ice Cave", "Ice Gallery Out"):
            # (v4: open, no rock over them: Blake, review-snow_region 2 notes 4 and 7, "I need
            # to be able to drive through this", "this is in the way"; Aurora's ice to be
            # redone with its section.)
            continue
        elif kind == "ice":
            half = pb.bore(c, L, name, s0, s1, ("cavern_ice", "wall"), ("summit_snow", "deep_snow"), height=11.0)
            # (Stood on the floor at the foot of its walls, not stuck up the walls: Blake,
            # review-snow_region 14 note 4, "lets put all these crystals on the walls in this
            # tunnel on the ground"; their glow down by them.)
            crystals = [ap.fan(c, v, size=3.6, mat=m) for v, m in ((0, ap.CYAN), (1, ap.VIOLET), (2, ap.TEAL))]
            s = s0 + 5.0
            k = 0
            while s < s1 - 4.0:
                q = c.at(s)
                sd = 1 if k % 2 else -1
                x, y = q.p.x + q.r.x * sd * (half - 0.9), q.p.y + q.r.y * sd * (half - 0.9)
                z = min(ground(x + 0.8 * math.cos(a), y + 0.8 * math.sin(a)) for a in (0.0, 1.57, 3.14, 4.71))
                c.place(crystals[k % 3], x, y, z - 0.3, rot=math.atan2(-q.r.y * sd, -q.r.x * sd) - math.pi / 2,
                        role="visual")
                g = c.game(x - q.r.x * sd * 0.8, y - q.r.y * sd * 0.8, z + 1.6)
                c.entity("lantern", x=g[0], y=g[1], z=g[2])
                s += 9.0
                k += 1
            # (Hung from the roof just inside both mouths, following its arch: review-snow_region
            # 16 note 3, "these icicles in this tunnel are floating. pleace attach them to the
            # roof. do it on both ends of the tunnel"; they hung in the open cut outside.)
            for s in (s0 + 1.5, s1 - 1.5):
                roof_icicles(c, s, half, 11.0)
        else:  # the Frozen Falls
            half = pb.bore(c, L, name, s0, s1, ("frost_cliff", "wall"), ("snow_ground", "deep_snow"), height=10.0)
            q = c.at(s0 - 4.0)  # (the lake side: the falls pour down either side of the mouth)
            for sd in (-1, 1):
                x, y = q.p.x + q.r.x * sd * (half + 12.0), q.p.y + q.r.y * sd * (half + 12.0)
                foot = ground(x, y)
                wp.ice_fall(c, "%s %d" % (name, sd), x, y, foot + 22.0, foot - 0.5, 14.0, facing=(-q.t.x, -q.t.y))
            c.place(ap.icicle_fringe(c, 1, width=2 * half + 4.0, length=5.0), q.p.x, q.p.y, q.p.z + 9.5,
                    rot=math.atan2(q.t.y, q.t.x) - math.pi / 2, role="visual")
            for k in range(3):
                q = c.at(s0 + (s1 - s0) * (k + 0.5) / 3)
                g = c.game(q.p.x + q.r.x * (half - 0.6), q.p.y + q.r.y * (half - 0.6), q.p.z + 4.5)
                c.entity("lantern", x=g[0], y=g[1], z=g[2])


def mirror_floor(c, ter):
    """A floor of the walls' deep blue ice a little under the rift's mirror ice (review-snow_region
    16 note 4, "lets put a floor under the ice here so it isnt just a white void underneath";
    the mirror ice is see-through, and the snow underfloor showed white through it). Only
    seen. Returns how many faces."""
    tex = c.lib("mirror_ice", "ice")["kp_texture"]
    me = ter.data
    bm = kit.bmesh.new()
    n = 0
    for p in me.polygons:
        m = me.materials[p.material_index] if p.material_index < len(me.materials) else None
        if m is None or m.get("kp_texture") != tex:
            continue
        bm.faces.new([bm.verts.new(ter.matrix_world @ me.vertices[i].co - kit.Vector((0.0, 0.0, 0.4))) for i in p.vertices])
        n += 1
    if n:
        bmesh_ob = c.mesh_object("Mirror Ice Floor", bm, "Props", "visual")
        c.assign(bmesh_ob, c.lib("cavern_ice", "wall"))
    else:
        bm.free()
    print("mirror ice floor: %d faces" % n)
    return n


def roof_icicles(c, s, half, height):
    """Icicles hung along a bore's roof across the road at s: its arch (course_kit.tunnel's
    profile: level over the middle, sloping down to the walls, banked with the road), each
    short run's top sunk a little into the rock, shorter where the roof comes down."""
    q = c.at(s)
    tb = math.tan(math.radians(q.bank))
    rot = math.atan2(q.t.y, q.t.x) - math.pi / 2

    def roof(a):
        aa = abs(a)
        b = height if aa <= 0.62 * half else lerp(height, 0.62 * height, (aa - 0.62 * half) / (0.38 * half))
        return b - a * tb

    # (level over the middle: runs 1.8 m wide; down the slopes, runs 0.9 m wide, each
    # hung from its higher end so none floats)
    mid = 0.62 * half
    m = max(2, int(2 * mid / 1.8))
    runs = [(-mid + (i + 0.5) * 2 * mid / m, 2 * mid / m) for i in range(m)]
    side = half * 0.95 - mid
    k = max(1, int(side / 0.9))
    for sgn in (-1, 1):
        runs += [(sgn * (mid + (i + 0.5) * side / k), side / k) for i in range(k)]
    protos = {}
    n = 0
    for a, w in runs:
        flat = abs(a) < mid
        key = (flat, round(w, 1))
        if key not in protos:
            protos[key] = ap.icicle_fringe(c, 0 if flat else 1, width=w, length=3.6 if flat else 2.0)
        top = max(roof(a - w / 2), roof(a + w / 2))
        x, y = q.p.x + q.r.x * a, q.p.y + q.r.y * a
        c.place(protos[key], x, y, q.p.z + top + 0.2, rot=rot, role="visual")
        n += 1
    return n


LANES = []
YARDS = []  # (the bone huts' yards to dress: hut_yards)
TER = None  # (the terrain, once built: for seating buildings)


def village(c, ground, ter):
    """Hearthglow, in its new basin by the lake (Blake, Oct 29): the town square, the
    cottages round it on their lanes and up on the basin's walls, the fountain and the
    bonfire, the great tree, the market, the bell tower, lanterns and lights
    (snow_dress.hearthglow; after the attack: frozen solid, the tree iced)."""
    cx, cy, cr, cz = SL.VILLAGE
    taken = paint.Taken([(*SL.BELL, 8.0), (*SL.GATES["hearthglow"], 16.0), (*SL.TREE, 18.0)])
    LANES.extend(sd.hearthglow(c, ground, ter, taken))
    gx, gy = SL.TREE
    if RUIN:
        box(c, "Great Tree Trunk", gx, gy, 1.6, 1.6, ground(gx, gy) - 1.0, ground(gx, gy) + 8.0, ("weathered_timber", "wall"))
        for k, (r, z) in enumerate(((8.0, 6.0), (6.0, 12.0), (4.0, 17.0))):
            cone(c, "Great Tree Ice %d" % k, gx, gy, r, ground(gx, gy) + z, 6.0, ("glacier_ice", "wall"), segs=8,
                 role="visual")
    else:
        hp.giant_tree(c, "Great Tree", gx, gy, ground(gx, gy), height=52.0)  # (v4: bigger, seen from the Crest)
        # Its foot heaped with presents, inside its fence (Blake, review-snow_region 7).
        gz = ground(gx, gy)
        for k in range(10):
            a = k * math.tau / 10 + 0.3
            r = 5.2 + 1.6 * (k % 2)
            px, py = gx + r * math.cos(a), gy + r * math.sin(a)
            c.place(hp.present_pile(c, k % 3), px, py, sd.low(ground, px, py, 2.2) - 0.1, rot=a + 0.4 * (k % 3), scale=1.25 + 0.15 * (k % 3),
                    coll="Village")
    # The bell tower, on level ground, its door to the square, its stone footing down to
    # the land all round (Blake, review-snow_region note 3: "this building is floating ...
    # please no more floating buildings": tests/buildings.test.ts).
    bx, by = SL.BELL
    rot = math.atan2(cy - by, cx - bx) + math.pi / 2  # (its door, local -Y, to the square)
    hi = sd.level_site(c, bx, by, rot, 7.6, 7.6, ground, ter)
    if hi is not None:
        lo = min(ground(bx + dx, by + dy) for dx in (-4.0, 0.0, 4.0) for dy in (-4.0, 0.0, 4.0))
        box(c, "Bell Tower Footing", bx, by, 3.8, 3.8, lo - 1.5, hi + 0.1, ("hearth_stone", "wall"), rot=rot)
        if RUIN:
            box(c, "Bell Tower Ruin", bx, by, 3.5, 3.5, hi - 0.5, hi + 9.0, ("hearth_stone", "wall"), rot=rot)
        else:
            c.place(hp.bell_tower(c), bx, by, hi - 0.1, rot=rot)
    # The market (note 5, "right in the middle of the path"; note 1, "completely redone"):
    # a crescent of stalls round the square's north edge, off its lanes, facing in, lights
    # strung over them.
    if not RUIN:
        sd.market(c, ground, cx, cy, cr, cz)


def landmarks(c, ground, spots):
    """Each world's landmark, its gateway in front of it: Frostveil's keep, the summit's
    giant tree and shipwreck, the rift in the glacier."""
    def facing(name):
        (ex, ey), _ = spots[name]
        gx, gy = SL.GATES[name] if name in SL.GATES else SL.LAIR
        return math.atan2(gy - ey, gx - ex)

    # Frostveil Citadel: the keep behind its gate.
    gx, gy = SL.GATES["frostveil"]
    f = facing("frostveil")
    keep = kp.keep_block(c, w=30.0, d=20.0, h=30.0)
    c.place(keep, gx + 14.0 * math.cos(f), gy + 14.0 * math.sin(f), ground(gx, gy) - 0.5, rot=f + math.pi / 2)
    arch = kp.gate_arch(c, span=16.0, clear=9.0, depth=5.0)
    c.place(arch, gx, gy, ground(gx, gy) - 0.3, rot=f - math.pi / 2, role="visual")
    box(c, "Keep Gate Dark", gx + 2.0 * math.cos(f), gy + 2.0 * math.sin(f), 6.0, 1.0, ground(gx, gy) - 1.0,
        ground(gx, gy) + 9.0, ("dark_corridor", "wall"), rot=f + math.pi / 2, role="visual")
    # Snowy Summit: the giant tree at its gate, and a second giant out in the meadow (v4:
    # proper evergreens, green, seen from the Crest; frozen after the attack).
    gx, gy = SL.GATES["summit"]
    sd.giant_pine(c, "Giant Tree", gx, gy, ground(gx, gy), height=64.0, seed=1)
    sd.giant_pine(c, "Giant Tree 2", -16.0, 191.0, ground(-16.0, 191.0), height=54.0, seed=2)
    # Aurora Rift: the crack in the glacier, ice spires either side, the sky alight.
    gx, gy = SL.GATES["aurora"]
    f = facing("aurora")
    z = ground(gx, gy)
    # (No sheet of ice behind it: review-snow_region 13 note 6, "remove this blue sheet".)
    for side in (-1, 1):
        x, y = gx + side * 12.0 * math.cos(f + math.pi / 2), gy + side * 12.0 * math.sin(f + math.pi / 2)
        # (On the lowest ground under its whole ring of spires, not its middle's: review-snow_region
        # 15 note 5, "some of these crystals are floating".)
        zl = min([ground(x, y)] + [ground(x + r * math.cos(a), y + r * math.sin(a)) for r in (3.0, 6.0) for a in [j * 0.785 for j in range(8)]])
        c.place(ap.spire_cluster(c, 0 if side < 0 else 1, height=34.0), x, y, zl - 0.8, role="visual")
        c.place(paint.trunk_proto(c, 5.0, 16.0), x, y, zl - 0.8, coll="Collision", role="collision")
    g = c.game(gx, gy, z + 30.0)
    c.entity("sparkles", rate=12, radius=40)
    # v4 (Blake, Oct 30: "a few more crystals and glacier features visible for aurora,
    # nothing crazy"): crystal spires and ice columns along the glacier's and the
    # cavern's rims, catching the light from the Crest; an ice arch over the glacier.
    for k, (x, y, h, kind) in enumerate(((96.0, 176.0, 30.0, "spire"), (66.0, 130.0, 24.0, "column"), (150.0, 40.0, 34.0, "spire"),
                                         (120.0, 116.0, 18.0, "needles"), (206.0, 60.0, 22.0, "column"))):
        # (On the lowest ground under it: review-snow_region 13 note 3, "some of these crystals
        # are floating".)
        z = min([ground(x, y)] + [ground(x + 5.0 * math.cos(a), y + 5.0 * math.sin(a)) for a in [j * 0.785 for j in range(8)]])
        if kind == "spire":
            c.place(ap.spire_cluster(c, k % 2, height=h), x, y, z - 0.5, role="visual")
        elif kind == "column":
            c.place(rp.rift_column(c, k % 2, height=h, radius=3.5), x, y, z - 0.5, role="visual")
        else:
            c.place(ap.needles(c, k % 2, height=h), x, y, z - 0.5, role="visual")
        c.place(paint.trunk_proto(c, 3.5, 12.0), x, y, z - 0.5, coll="Collision", role="collision")
        g = c.game(x, y, z + 2.0)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])


def ruined(c, ground):
    """After Rimefang's attack: his lair (ice teeth round a dark mouth in the summit's north
    wall), the cleft of the Frozen Pass, ice shards in the fields."""
    lx, ly = SL.LAIR
    z = ground(lx, ly)
    box(c, "Lair Mouth", lx, ly + 4.0, 8.0, 2.0, z - 1.0, z + 12.0, ("dark_corridor", "wall"), role="visual")
    for k in range(7):
        t = (k - 3) / 3.0
        if abs(t) < 0.4:
            continue
        px, py = lx + t * 13.0, ly + 2.0
        cone(c, "Lair Ice %d" % k, px, py, 3.0 + abs(t) * 1.5, ground(px, py) - 1.0, 10.0 + 8.0 * (1 - abs(t)),
             ("glacier_ice", "wall"), segs=5)
    if BROKEN_WAYS:
        bx, by = SL.PASS_END
        box(c, "Frozen Pass Bend", bx + 6.0, by, 6.0, 40.0, natural(bx, by) - 2.0, RIM_Z + 20.0, ("frost_cliff", "wall"))
    spots = []
    for k in range(40):
        a = k * 2.399
        r = 37.0 + 236.0 * ((k * 0.618) % 1.0)
        x, y = r * math.cos(a), r * math.sin(a)
        if L.wall_sd(x, y) < -16 and paint.road_clear(c, x, y, 8.0):
            spots.append((x, y))
    ruin.shards(c, "Ice Shard", spots, ground, ("glacier_ice", "wall"), seed=7)


def hut_yards(c, ground):
    """Pots, a bucket, a woodpile and a chopping block with its tools about each bone hut
    (review-snow_region 10 note 4), each on its own level spot. (Put down once the
    summit's ground is all cut: review-snow_region 12 notes 4, 5, "these things are
    floating".)"""
    for x, y, rot, k in YARDS:
        cs, sn = math.cos(rot), math.sin(rot)
        pieces = [(ia.camp_pots(c, k % 2), 4.5, -1.6, 0.55, 0.0), (ia.camp_bucket(c), 4.9, 0.4, 0.4, 0.0),
                  (ia.camp_woodpile(c), -4.7, 0.6, 0.95, math.pi / 2), (ia.camp_block(c), -4.3, -2.3, 0.5, 0.0)]
        for j, (proto, lx, ly, r, turn) in enumerate(pieces):
            if (k + j) % 4 == 3:
                continue  # (not every hut has everything)
            px, py = x + lx * cs - ly * sn, y + lx * sn + ly * cs
            if L.wall_sd(px, py) > -3.0 or not paint.road_clear(c, px, py, 1.5):
                continue
            hs = [ground(px, py)] + [ground(px + r * math.cos(t), py + r * math.sin(t)) for t in [i * 0.785 for i in range(8)]]
            if max(hs) - min(hs) > 0.45:
                continue  # (no spot level enough for it)
            c.place(proto, px, py, min(hs) - 0.04, rot=rot + turn + 0.3 * math.sin(k + j), coll="Props", role="visual")


def dress(c, ground, spots):
    """The paint pass, world by world: the village's lantern posts, Christmas pines and
    snowmen; the bailey's curtain walls, towers, braziers and banners; the summit's pines,
    broadleaves, boulders, the frozen shipwreck and the mammoth's tusk gate; the glacier's
    ice columns, spires and crystal gardens; the lake's icebergs. After the attack: the
    pines frozen into ice, the undergrowth gone."""
    vx, vy, vr, _vz = SL.VILLAGE
    taken = paint.Taken([(HUB[0], HUB[1], 12.0), (vx, vy, vr + 10.0), (SL.LAKE[0], SL.LAKE[1], SL.LAKE[2] + 4.0), (*RETURN, 18.0),
                         *((e[0], e[1], 16.0) for e, _ in spots.values()),
                         *((x, y, 26.0) for x, y in SL.GATES.values()), (*SL.LAIR, 24.0), *sd.SPOTS,
                         (SL.HOLLOW[0], SL.HOLLOW[1], 41.0), (SL.HOLLOW_MOUTH[0], SL.HOLLOW_MOUTH[1], 16.0),
                         # (No shrub or boulder here: review-snow_region 11 notes 4, 7, "remove this
                         # shrub", "remove this rock.")
                         (-31.7, -150.3, 2.5), (-109.6, -74.2, 2.5),
                         # (review-snow_region 12 notes 7, 8: "remove this shrub", a broadleaf and a
                         # shrub up the summit; and no little pine inside the great tree)
                         (-27.0, 193.3, 3.0), (-87.4, 112.2, 2.0), (*SL.TREE, 14.0)])
    # The walls brought to life (snow_dress), both builds.
    sd.wall_life(c, ground, taken)

    def inside(x, y):
        if L.wall_sd(x, y) > -8:
            return False
        lx, ly, lr, _ = SL.LAKE
        return math.hypot(x - lx, y - ly) > lr + 6

    def look(name):
        return lambda x, y: inside(x, y) and L.look_at(x, y) == name

    rmax = 470.0
    g = ground
    pines = [sp.pine(c, v, 12.0 + 4.0 * v, snowy=True) for v in range(3)]
    for name in ("summit", "lake"):  # (v4: none in Hearthglow's streets or the castle)
        for v in range(2):
            paint.scatter(c, sp.boulder(c, v), 6, rmax, lambda x, y, n=name: look(n)(x, y) and L.wall_sd(x, y) > -30, g,
                          taken, 90 + v + len(name), room=4.0, scale=(1.0, 2.2), road_margin=9.0)
    if RUIN:
        for v, p in enumerate(pines):
            for x, y in paint.scatter(c, p, 50, rmax, lambda x, y: inside(x, y) and L.look_at(x, y) != "aurora", g, taken,
                                      10 + v, room=5.0, scale=(0.9, 1.4), road_margin=7.0):
                cone(c, "Frozen Pine %d %d" % (v, int(x)), x, y, 3.2, g(x, y) - 0.5, 9.0 + 3.0 * v, ("glacier_ice", "wall"),
                     segs=6, role="visual")
        # (The survivors, out along the roads: tests/villagers.test.ts wants eight homes.)
        homes = [(e["x"], -e["z"]) for e in c.entities if e["type"] == "villager_home"]
        paint.wayfolk(c, ground, "snow", homes, max(0, 8 - len(homes)) + 1, apart=70.0, every=12)
        return
    # Hearthglow (by the lake now): Christmas pines with lights round it, snowmen. The
    # hollow it left, the way in: snowy pines (its lanterns are snow_dress.entry_pass's).
    near_village = lambda x, y: (inside(x, y) and L.look_at(x, y) == "hearth"  # noqa: E731
                                 and math.hypot(x - vx, y - vy) < vr + 45.0)
    for v in range(2):
        paint.scatter(c, hp.xmas_pine(c, v, height=12.0 + 3.0 * v), 8, rmax, near_village, g, taken, 60 + v, room=6.0,
                      road_margin=6.0, trunk=(0.8, 6.0))
    paint.scatter(c, hp.snowman(c, 0), 5, rmax, near_village, g, taken, 63, room=3.0)
    ss.hearthglow(c, ground, taken, lambda v, x, y, rot, name: sd.seat_cottage(c, v, x, y, rot, ground, name=name, ter=TER))
    # Folk out along the roads too, away from the villages' own (every part of the kingdom
    # with someone to stop and talk to: tests/villagers.test.ts wants eight homes).
    homes = [(e["x"], -e["z"]) for e in c.entities if e["type"] == "villager_home"]
    paint.wayfolk(c, ground, "snow", homes, max(0, 8 - len(homes)) + 1, apart=70.0, every=12)
    hub = look("hearth")
    for v, p in enumerate(pines):
        paint.scatter(c, p, 8, rmax, lambda x, y: hub(x, y) and L.wall_sd(x, y) < -14.0, g, taken, 64 + v, room=6.0,
                      scale=(0.9, 1.4), road_margin=8.0, trunk=(0.8, 6.0))
    # Frostveil (v4): the road walled in, inside the castle (snow_sections.frostveil).
    fv = look("frostveil")
    clear = [(e[0], e[1], 14.0) for e, _ in spots.values()] + [(x, y, 22.0) for x, y in SL.GATES.values()]
    ss.frostveil(c, ground, taken, clear)
    for v, p in enumerate(pines[:2]):
        # (On the courtyard's floor only: none up on the cliffs, note 14.)
        paint.scatter(c, p, 14, rmax, lambda x, y: fv(x, y) and L.wall_sd(x, y) < -6.0, g, taken, 74 + v, room=6.0,
                      scale=(0.9, 1.3), road_margin=7.0, trunk=(0.8, 6.0))
    # The summit: pines, broadleaves, shrubs, the frozen shipwreck, the tusk gate over the road.
    su = look("summit")
    # (v4: the deep thaw, Blake, Oct 30: green trees; geysers, ponds, mammoths: snow_sections)
    pines = [sp.pine(c, v, 12.0 + 4.0 * v, snowy=False) for v in range(3)]
    ss.summit(c, ground, taken, TER)
    # (Biggest first, each kept its boughs' spread clear of the last's: no little pine stood
    # right under a big one, review-snow_region 10 note 9.)
    for v, p in reversed(list(enumerate(pines))):
        paint.scatter(c, p, 40, rmax, su, g, taken, 10 + v, room=(12.0 + 4.0 * v) * 0.3 * 1.5 * 1.4, scale=(0.9, 1.5),
                      road_margin=7.0, trunk=(0.8, 6.0))
    for v in range(2):
        paint.scatter(c, sp.broadleaf(c, v, frosted=False), 16, rmax, su, g, taken, 30 + v, room=7.5, road_margin=7.0,
                      trunk=(0.9, 6.0))
        paint.scatter(c, sp.shrub(c, v, frosted=False), 60, rmax, su, g, taken, 40 + v, room=2.5, role="visual", scale=(0.7, 1.4))
    paint.scatter(c, sp.shipwreck(c), 1, rmax, lambda x, y: su(x, y) and L.wall_sd(x, y) < -24, g, taken, 44, room=40.0,
                  road_margin=18.0)
    def lone_hut(x, y, z, s):
        # (Set level like the summit's homes: on a slope its step and stones stood off the
        # ground, review-snow_region 15 note 2, "this stone is floating".)
        rot = 2.3 * x + 1.1 * y
        hi = sd.level_site(c, x, y, rot, 7.5, 9.0, ground, TER)
        if hi is None:
            return
        c.place(ia.bone_hut(c, 1), x, y, hi - 0.05, rot=rot, scale=s, coll="Props")
        YARDS.append((x, y, rot, int(abs(x))))
    paint.scatter(c, ia.bone_hut(c, 1), 2, rmax, lambda x, y: su(x, y) and L.wall_sd(x, y) < -8, g, taken, 45, room=10.0,
                  road_margin=8.0, instead=lone_hut, scale=(1.0, 1.0))
    hut_yards(c, ground)
    # The glacier: ice columns, spires, crystal gardens, ice spikes.
    au = look("aurora")
    ss.aurora(c, ground, taken)
    if not RUIN:
        ss.rift_folk(c, ground, taken, TER)
        ss.outpost(c, ground, taken, TER)
    for v in range(2):
        # (Each set down on the lowest ground under its spread, so none floats on the rift's
        # slopes, review-snow_region 13 note 3; the columns' crystals rooted in them, note 5.)
        paint.scatter(c, rp.rift_column(c, v, height=30.0, radius=4.0), 6, rmax,
                      lambda x, y: au(x, y) and L.wall_sd(x, y) > -24, g, taken, 80 + v, room=14.0, road_margin=10.0, seat=4.5,
                      sink=0.8)
        paint.scatter(c, ap.spire_cluster(c, v, height=22.0), 5, rmax, au, g, taken, 82 + v, room=14.0, road_margin=10.0,
                      trunk=(4.0, 12.0), seat=4.0, sink=0.6)
        paint.scatter(c, ap.ice_spike(c, v, height=10.0), 14, rmax, au, g, taken, 84 + v, room=5.0, road_margin=6.0, seat=1.8,
                      sink=0.5)
    paint.scatter(c, ap.garden(c, 0, radius=8.0), 4, rmax, au, g, taken, 86, room=14.0, road_margin=9.0, role="visual", seat=5.0,
                  sink=0.4)
    # The lake: pines on its shores, icebergs frozen in the ice.
    la = look("lake")
    for v, p in enumerate(pines[:2]):
        paint.scatter(c, p, 16, rmax, la, g, taken, 50 + v, room=6.0, scale=(0.9, 1.3), road_margin=7.0, trunk=(0.8, 6.0))
    lx, ly, lr, lz = SL.LAKE
    for k in range(5):
        a = k * 1.3 + 0.5
        x, y = lx + lr * 0.75 * math.cos(a), ly + lr * 0.75 * math.sin(a)
        if taken.clear(x, y, 10.0) and paint.road_clear(c, x, y, 8.0):
            c.place(sp.iceberg(c, k % 2), x, y, lz - 0.4, rot=a)
            taken.add(x, y, 10.0)


if __name__ == "__main__":
    main()
