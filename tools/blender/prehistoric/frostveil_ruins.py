# Frostveil Citadel in ruins: Adventure's treasure map course for the snowy citadel
# (?track=frostveil_citadel_ruin; in dev builds Frostveil's menu entry asks Standard or Ruined).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/frostveil_ruins.py      (the bpy module)
#
# The dragons brought the Bridge of Giants down into the start valley, and with it the
# climb, the Serpent Gate and the high town are cut off (Blake: at least half as long,
# fast like the beach courses, driving up ramps of castle rubble; the ruins are the
# course). The lap runs north past the first fallen stones, right onto the bridge's
# fallen spans and up across the east hillside over their humps, off a rubble kicker
# over a broken arch, round onto the course's own run-up and jump over the frozen
# gorge, and back west through the lower town's rubble in S-bends. About 810 m (the full
# lap is 2029 m).
#
# frostveil_citadel.py lays the lap out (ruin_mode.ON); the citadel itself (the temple,
# the labyrinth, the fortress, the lower town...) is placed by the course's own scenery
# code along the standard lap (ruin_kit.ghost), with the bridge broken and fires, smoke
# and rubble added.

import importlib
import math
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ruin_mode  # noqa: E402

# The standard course first (its route and landmarks), then the ruin's lap.
ruin_mode.ON = False
import frostveil_citadel as std  # noqa: E402

sys.modules.pop("frostveil_citadel")
ruin_mode.ON = True
fc = importlib.import_module("frostveil_citadel")

import course_kit as kit  # noqa: E402
import props  # noqa: E402
import ruin_kit as rk  # noqa: E402
from course_kit import rnd  # noqa: E402

# Where the fire fell: the bridge's fall, the hillside, the lower town.
BURNS = [(30.0, -105.0, 30.0), (110.0, -80.0, 26.0), (180.0, -85.0, 22.0), (60.0, -280.0, 24.0), (150.0, -285.0, 22.0), (-20.0, -170.0, 16.0)]


def dress(c, m, rock):
    import frostveil_scenery as fs
    import winter_props as wp

    ter = list(c.coll("Terrain").objects)
    lights = fs.Lights()

    def z_at(x, y):
        z = c.ground_z(x, y, ter)
        return z if z is not None else m.natural(x, y)

    def clear(x, y, margin=4.0):
        return props.clear_of_road(c, x, y, margin)

    # Along the ruin's own road: the Great Gate over the start, braziers.
    fs.great_gate(c, m, lights, 30.0)
    fs.braziers_along(c, m, lights, m.SEG[12] + 20, m.LIP - 10, 24.0, 2.6)
    fs.braziers_along(c, m, lights, m.LAND + 10, m.SEG[16], 20.0, 2.6, alternate=False)
    fs.braziers_along(c, m, lights, m.SEG[16] + 10, m.SEG[23], 26.0, 3.0)

    # The citadel, from the course's own scenery code, along the standard lap.
    g = rk.ghost_route(c, std.ROUTE, width=15.0, bank=6.0)
    with rk.ghost(c, g):
        S = std.SEG
        # The Bridge of Giants: its west half still stands over the chasm; the east half
        # lies in pieces on the hillside (the rubble the lap climbs).
        fs.bridge_piers(c, std, lights, S[7] + 95, S[8] + 25, 33.0, "Bridge Ruin", bannered=False)
        k = 0
        s = S[6] + 20
        while s < S[7] + 80:
            q = c.at(s)
            k += 1
            if clear(q.p.x, q.p.y, 7.0):
                z = z_at(q.p.x, q.p.y)
                slab = c.rock_mass("Fallen Span %d" % k, q.p.x + 4 * math.sin(k), q.p.y + 6 * math.cos(k * 1.3), 9.0, 5.0,
                                   z + 4.0 + 3 * rnd(k * 1.7), z0=z - 2.0, n=6, seed=k, angle=0.4 * k,
                                   bands=[(1.0, 0.0), (1.0, 0.6), (0.8, 1.0)], base=z)
                c.assign(slab, c.lib("citadel_stone", "wall"))
            rk.rubble_heap(c, q.p.x, q.p.y - 8, z_at, n=7, spread=7.0, size=2.2, role="visual", seed=k)
            s += 14.0
        # The climb, buried under the bridge's fall: rubble along where it ran.
        s = S[1]
        while s < S[6]:
            q = c.at(s)
            k += 1
            if clear(q.p.x, q.p.y, 8.0):
                rk.rubble_heap(c, q.p.x, q.p.y, z_at, n=6, spread=6.0, size=2.0, role="visual", seed=k)
            s += 22.0
        # The Serpent Gate, its mouth fallen in.
        inside = kit.crossings(c, lambda smp: std.in_tunnel_rock(smp.p.x, smp.p.y, 1.0), margin=0)
        t0, t1 = max(inside, key=lambda r: r[1] - r[0])
        fs.serpent_gate(c, std, lights, t0 + 2.0)
        q = c.at(t0 + 4.0)
        rk.rubble_heap(c, q.p.x, q.p.y, z_at, n=12, spread=9.0, size=3.0, seed=77)
        # The high town: the courtyard and the temple, the labyrinth, the causeway's piers.
        q = c.at(S[14])
        center = q.p + q.r * 60.0
        fs.courtyard(c, std, lights, (center.x, center.y))
        fs.temple_and_terraces(c, std, lights, -215.0, 188.0)
        fs.labyrinth(c, std, lights)
        fs.bridge_piers(c, std, lights, S[19] + 20, S[20], 30.0, "Causeway Ruin", deck=3.4, bannered=False)
        fs.lower_town(c, std, lights)
        fs.fortress(c, std, lights)
        fs.cliff_dwellings(c, std, lights)
        fs.keep(c, std, lights)
        fs.waterfalls(c, std, lights)
        fs.fog(c, std)
        fs.vegetation(c, std)
    # The frozen pond by the start, the stone head half sunk in its ice.
    px, py, pr = m.POND
    c.disc("Pond Ice", px, py, pr, -0.6, c.lib("frost_pool", "ice"), coll="Water", n=24, wobble=0.15)
    c.place(wp.dino_head(c, 0), px + 6, py + 4, -3.5, rot=2.3, coll="Citadel", role="visual")
    # Rubble beside the lap's humps (the stones it rides over).
    for at, h, ln in m.HUMPS:
        q = c.at(at)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 5.0))
            if clear(p.x, p.y, 4.0):
                rk.rubble_heap(c, p.x, p.y, z_at, n=5, spread=4.0, size=1.7, role="visual", seed=int(at) + side)
    # Whatever the old lap's scenery put on the new road goes.
    print("cleared off the new road:", rk.clear_new_road(c, ("Citadel", "Town", "Bridges", "Fire", "Temple", "Fortress", "Trees", "Props")))
    fires = rk.scorch(c, BURNS, z_at, clear, per=5, wet=lambda x, y, z: z < -1.0)
    for x, y, z in lights.points:
        gx, gy, gz = c.game(x, y, z)
        c.entity("torch", x=round(gx, 2), y=round(gy, 2), z=round(gz, 2))
    rk.emit(c, fires)
    groups = ("Citadel", "Bridges", "Temple", "Town", "Fortress")
    c.merge_props(groups)
    stone = [o for name in groups for o in c.coll(name).objects if o.type == "MESH" and o.data.users == 1]
    c.glow(ter + stone, lights.points + fires, 16.0, (1.1, 0.8, 0.55), base=(0.86, 0.86, 0.98))
    c.entity("snowfall", rate=90, radius=40)
    c.entity("ashfall", rate=20, radius=40)
    print("frostveil ruin: fires", len(fires), "lap", round(c.length, 1))


ruin_mode.DRESS = dress

if __name__ == "__main__":
    fc.main()
