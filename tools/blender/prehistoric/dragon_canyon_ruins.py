# Dragon Canyon in ruins: Adventure's treasure map course for the Emerald Kingdom's canyon
# (?track=dragon_canyon_ruin; in dev builds the course's menu entry asks Standard or Ruined).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/dragon_canyon_ruins.py      (the bpy module)
#
# The Chosen One's sacrifice tore the canyon apart (Blake: reworked by the blast like the
# others, but the Dragon Kingdom's most fun drive: keep what makes it fun; at least half
# the lap). The lap keeps the Cliffside Hairpins, the Canyon Bridge (broken in the middle
# by the blast: jump it) and the Skeleton Pass; then the mesa's flank has split and slid,
# so it runs down the slip, crosses the river on rock the blast fused across it, and
# climbs to the Dragon Gate. About 1090 m (the full lap is 2201 m).
#
# dcanyon_land.py lays the lap out (ruin_mode.ON); the land is the canyon's own, with the
# slip cut into it; the outpost, the hairpins, the bones, the quarry, the oasis and the
# towers are the course's own scenery code along the standard lap (ruin_kit.ghost).

import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ruin_mode  # noqa: E402

ruin_mode.ON = False
import dcanyon_land as L0  # noqa: E402
import dragon_canyon as std  # noqa: E402
import dcanyon_scenery as ds  # noqa: E402
import dcanyon_town as town  # noqa: E402
import emerald  # noqa: E402,F401  (the paint, installed by the course)

for _m in ("dcanyon_land", "dragon_canyon"):
    sys.modules.pop(_m)
ruin_mode.ON = True
L = importlib.import_module("dcanyon_land")
dcr = importlib.import_module("dragon_canyon")

import props  # noqa: E402
import ruin_kit as rk  # noqa: E402
from course_kit import lerp  # noqa: E402

_STD_NATURAL = L0.natural
LINK = (L.S["k3"] + 10.0, L.S["x5"] + 20.0)


def ruin_ground(x, y):
    """The canyon's own land, with the slip the blast cut for the ruin's road: down from
    the Skeleton Pass, over the river (the rock fused across it), up to the gate."""
    z0 = _STD_NATURAL(x, y)
    d, s = L.nearest(x, y)
    if LINK[0] <= s <= LINK[1] and d < 60.0:
        k = L.sm((d - 12.0) / 36.0)
        return lerp(L.road_z(s) - 0.6, z0, k)
    return z0


L0.ground = ruin_ground
L.ground = ruin_ground
L.STD = L0

BURNS = [(150.0, 60.0, 24.0), (200.0, 120.0, 22.0), (60.0, 130.0, 22.0), (120.0, -60.0, 26.0), (40.0, -40.0, 20.0)]


def broken_bridge(c, fires):
    """The Canyon Bridge's broken ends, splintered stone hanging over the gap."""
    a, b = L.BREAK
    for s, k in ((a, 0), (b, 1)):
        q = c.at(s)
        rk.rubble_heap(c, q.p.x, q.p.y, lambda x, y: L.RIVER_Z, n=6, spread=6.0, size=2.6, role="visual", seed=70 + k)
        fires.append((q.p.x, q.p.y, q.p.z - 1.0))


def dress(c, m):
    sc = ds.Scene(c)
    sc.dc = std
    sc.short = ([], -1e9, -1e9)
    ds.land(c, sc)
    sc.mesa = sc.land  # (the caverns' mesa slid away with the slip)
    sc.tunnel = (-1.0, -1.0)
    ds.waters(c, sc)
    sc.falls = ds.falls(c, sc)
    c.start_line()
    g = rk.ghost_route(c, std.ROUTE, width=14.0, bank=6.0)
    with rk.ghost(c, g):
        town.build(c, sc)
        town.entities(c, sc)
    fires = []
    broken_bridge(c, fires)
    fires += rk.scorch(c, BURNS, sc.ground, lambda x, y: props.clear_of_road(c, x, y, 4.0), per=5)
    print("cleared off the new road:", rk.clear_new_road(c, ("Props", "Town", "Landmarks", "Quarry", "Oasis", "Plants", "Bridges", "Arch")))
    rk.emit(c, fires)
    sc.lights.setdefault("fire", []).extend(fires)
    ds.light(c, sc)
    c.merge_props(("Wreck",))
    c.entity("ashfall", rate=16, radius=40)
    print("canyon ruin: fires", len(fires), "lap", round(c.length, 1))


ruin_mode.DRESS = dress

if __name__ == "__main__":
    dcr.main()
