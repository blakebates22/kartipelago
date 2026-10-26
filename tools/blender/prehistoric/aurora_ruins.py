# Aurora Rift in ruins: Adventure's treasure map course for the fractured glacier
# (?track=aurora_rift_ruin; in dev builds the course's menu entry asks Standard or Ruined).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/aurora_ruins.py      (the bpy module)
#
# The dragons brought the glacier's roof down (Blake: about 45% shorter, the whole cavern
# decimated, the Loop with half its top missing, the northern lights shining through the
# fire). The Crystal Cathedral lies open to the sky; Mirror Lake's cavern and the ascent
# are buried. The lap starts in the old tunnel off the ice bridge, rounds the Monolith,
# jumps the broken bridge, runs the causeway and goes round the Loop (the game still
# carries you over its missing top), then swings right through the Cathedral's broken
# east end and back over the fallen ice: south down the east end and west along the
# glacier's face, which fell into the Rift, onto the ice bridge's end. About 985 m (the
# full lap is 1908 m).
#
# aurora_rift.py lays the lap out (ruin_mode.ON); the glacier and its caverns, the
# Monolith, the bridges, the lake and the Great Rift Bridge are the course's own scenery
# code along the standard lap (ruin_kit.ghost); here the roof comes down: a crater open
# to the sky over the Cathedral and the lap, fallen ice slabs, fires on the ice.

import importlib
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ruin_mode  # noqa: E402

# The standard course first (its route and landmarks), then the ruin's lap.
ruin_mode.ON = False
import aurora_rift as std  # noqa: E402

sys.modules.pop("aurora_rift")
ruin_mode.ON = True
ar = importlib.import_module("aurora_rift")

import aurora_scenery as asc  # noqa: E402
import course_kit as kit  # noqa: E402
import ruin_kit as rk  # noqa: E402
from course_kit import rnd  # noqa: E402


def collapse(c, m):
    """The fallen roof: a crater cut open to the sky over everything the lap drives
    through (its walls the glacier's broken edges)."""
    pts = [(p[0], p[1]) for p in m.PATH[::4]]
    lx, ly = std.LOOP_IN[0], std.LOOP_IN[1]
    pts += [(lx + dx, ly + dy) for dx in (-50, 50) for dy in (-40, 60)]
    ring, centre = asc.outline(pts, 30.0, n=96, wobble=0.35, seed=11)

    def cut(solid):
        asc.apply_cut(c, solid, asc.chamber_cutter(c, ring, centre, std.ABYSS - 60, std.Z_CATH + 34, 420.0, wobble=1.4, seed=11,
                                                    name="Fallen Roof"))

    return cut, ring, centre


def fallen_ice(c, m, ring, centre, fires):
    """Slabs of the fallen roof: under the new road (it runs on them), heaped round the
    crater's floor and the Monolith's island, with fires burning on them."""
    S = m.SEG
    k = 0
    s = m.TO_ROAD(S[8]) + 10
    while s < m.TO_ROAD(S[13]):
        q = c.at(s)
        k += 1
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 6 + 5 * rnd(k + side)))
            top = q.p.z - 1.0 + 3.0 * rnd(k * 1.3 + side)
            slab = c.rock_mass("Fallen Ice %d %d" % (k, side), p.x, p.y, 9.0 + 4 * rnd(k), 6.0 + 3 * rnd(k + 5), top,
                               z0=std.ABYSS - 10, n=7, seed=k * 2 + (side > 0), angle=0.5 * k + side,
                               bands=[(1.0, 0.0), (1.0, 0.85), (0.8, 1.0)], base=std.ABYSS)
            c.assign(slab, c.lib("glacier_wall", "wall"))
            if (k + side) % 4 == 0:
                fires.append((p.x, p.y, top + 1.0))
        s += 22.0
    # Great blocks of roof down on the Cathedral's floor and across the abyss.
    for k in range(16):
        a = k * 2.399
        rr = 40 + 150 * math.sqrt(rnd(k * 3 + 2))
        x, y = centre[0] + rr * math.cos(a), centre[1] + rr * math.sin(a) * 0.7
        if not asc.inside(ring, x, y) or not asc.clear(c, x, y, 16.0):
            continue
        top = std.Z_CATH - 20 + 40 * rnd(k * 7)
        slab = c.rock_mass("Roof Block %d" % k, x, y, 16.0 + 10 * rnd(k), 10.0 + 8 * rnd(k + 1), top, z0=std.ABYSS - 10, n=8, seed=40 + k,
                           angle=k * 0.9, bands=[(1.0, 0.0), (1.0, 0.8), (0.75, 1.0)], base=std.ABYSS)
        c.assign(slab, c.lib("glacier_wall" if k % 3 else "cavern_ice", "wall"))
        if k % 2 == 0:
            fires.append((x, y, top + 1.5))


def dress(c, m, lp, s_in, s_out):
    X0, X1, Y0, Y1 = -1000.0, 620.0, -560.0, 700.0
    (ex, ey, _), (xx, xy, _) = std.LOOPS[0]
    g = rk.ghost_route(c, std.ROUTE, width=16.0, bank=6.0, sharp=std.SHARP, flat=[(ex, ey, 46), (xx, xy, 46)])
    cut, ring, centre = collapse(c, m)
    with rk.ghost(c, g):
        gs_in, gs_out = kit.s_near(c, ex, ey), kit.s_near(c, xx, xy)
        sc = asc.Scene(c, std)
        sc.p = asc.spots(c, std, gs_in, gs_out)
        solid, info = asc.caverns(c, std, sc.p, more=cut)
    # The land round the ruin's own road.
    c.terrain("Land", X0, X1, Y0, Y1, 8.0, std.natural, std.classify, near=8.5, fade=7.0)

    def under(x, y):
        if c.nearest(x, y)[1] > 70:
            return None
        return min(std.natural(x, y), c.road_height(x, y, 8.5, 7.0, 0.2, std.natural(x, y))[1]) - 0.6

    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 8.0, under, c.lib("abyss_glow", "abyss"))
    c.start_line()
    # The glacier's landmarks, from the course's own scenery code, along the standard lap.
    with rk.ghost(c, g):
        asc.entrance(c, sc, std)
        asc.cathedral(c, sc, std, info, lp, gs_in, gs_out)
        asc.multilevel(c, sc, std, info)
        asc.lake(c, sc, std, info)
        asc.ascent(c, sc, std)
        asc.rift(c, sc, std)
        asc.skyline(c, sc, std)
        asc.living(c, sc, std)
    m.ruin_pickups(c, s_in, s_out)
    fires = []
    fallen_ice(c, m, ring, centre, fires)
    # Fires along the lap too, on the fallen ice by the road.
    S = m.SEG
    for k, s in enumerate(range(int(m.TO_ROAD(S[1])), int(c.length) - 20, 55)):
        q = c.at(s)
        p = q.side((1 if k % 2 else -1) * (q.w / 2 + 3.5))
        fires.append((p.x, p.y, q.p.z + 0.6))
    groups = ("Props", "Snowfield", "Rift", "Tunnels", "Cathedral", "Abyss", "Bridges", "Monolith", "Lake", "Reflections", "Canyon", "Glacier Top", "Crystals")
    print("cleared off the new road:", rk.clear_new_road(c, groups))
    rk.emit(c, fires)
    c.merge_props(groups)
    joined = [o for name in groups for o in c.coll(name).objects if o.type == "MESH" and o.data.users == 1]
    ter = list(c.coll("Terrain").objects)
    rocks = [solid] + list(c.coll("Island").objects) + list(c.coll("Bridges").objects) + list(c.coll("Rocks").objects)
    # Light: the open crater moonlit and aurora-lit, its crystals still glowing, the fires
    # warm on the ice.
    cave = lambda w: std.in_massif(w.x, w.y, -2) and w.z < std.glacier_top(w.x, w.y) - 8  # noqa: E731
    c.glow(rocks + ter + joined, sc.cold, 36.0, (0.8, 1.2, 1.45), base=(0.78, 0.8, 0.98), region=cave)
    c.glow(rocks + ter + joined, sc.violet, 30.0, (1.2, 0.85, 1.45), base=1.0, region=cave)
    c.glow(rocks + ter + joined, sc.warm + fires, 16.0, (1.6, 1.0, 0.6), base=1.0)
    c.preset("sun", ter, 0.2)
    kit.paint.shade_roads(c.pieces, 0.25)
    c.entity("ashfall", rate=18, radius=40)
    print("aurora ruin: fires", len(fires), "lap", round(c.length, 1))


ruin_mode.DRESS = dress

if __name__ == "__main__":
    ar.main()
