# Dry Gulch in ruins: Adventure's treasure map course for the haunted ghost town
# (?track=dry_gulch_ruin; in dev builds the course's menu entry asks Standard or Ruined).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/dry_gulch_ruins.py      (the bpy module)
#
# The dragons set the town alight and brought the mine down (Blake: the mine fully
# destroyed, no shortcut; the town in flames; a new path opened by the destruction;
# about 20% shorter). The chasm cavern's roof fell in, and Hazard Ridge, hollowed out by
# the mine, slumped into it: the portal is buried, and a landslide runs from the mine
# approach down through the ridge's broken middle, over the crack where the cavern fell
# in (a jump), to the ravine's bend. The approach beyond the slide and the Rickety
# Trestle went into the chasm with the ridge's north face, the rim road with them. Main
# Street burns. About 1450 m (the full lap is 1813 m).
#
# dry_gulch.py lays the lap out (ruin_mode.ON) and shapes the land round the slide and
# the crack; the town, Boot Hill, the mineworks, the ravine and the rocks are the
# course's own scenery code along the standard lap (ruin_kit.ghost); here the ridge is
# cut open by the slide, the cavern's pit is opened to the sky, and the fires.

import importlib
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ruin_mode  # noqa: E402

# The standard course first (its route and landmarks), then the ruin's lap.
ruin_mode.ON = False
import dry_gulch as std  # noqa: E402

sys.modules.pop("dry_gulch")
ruin_mode.ON = True
dg = importlib.import_module("dry_gulch")

import gulch_scenery as gs  # noqa: E402
import gulch_town as gt  # noqa: E402
import props  # noqa: E402
import ruin_kit as rk  # noqa: E402
from course_kit import rnd  # noqa: E402

# Where the fire fell: up Main Street, the square, the saloon district, Boot Hill's
# chapel, round the slide's head and foot.
BURNS = [(-20.0, 40.0, 22.0), (20.0, 70.0, 20.0), (-40.0, 150.0, 22.0), (-110.0, 160.0, 24.0), (-200.0, 140.0, 20.0),
         (-230.0, 230.0, 20.0), (-20.0, 300.0, 22.0), (190.0, -60.0, 20.0)]


def slide_cut(c, m, ridge):
    """The ridge's broken middle: the landslide's corridor cut through it, and the
    cavern's pit opened to the sky, the crack between them."""
    pts = [(x, y, z) for x, y, z in m.SLIDE if std.ridge_d(x, y) > -40.0]
    if len(pts) > 2:
        gs.cut(c, ridge, gs.path_cutter(c, pts, lambda t: 24.0 + 4.0 * math.sin(t * 9.0), -4.0, 120.0, name="Slide Cutter"))
    cx, cy = std.CAVERN
    gs.cut(c, ridge, gs.cave_cutter(c, cx, cy, 0.6, 76.0, 58.0, -31.0, 160.0, 0.0, n=28, seed=5, name="Fallen Cavern"))
    crack = [(x, y, -30.0) for x, y in m.CRACK]
    gs.cut(c, ridge, gs.path_cutter(c, crack, 6.0, -2.0, 140.0, name="Crack Cutter"))
    gs.white_paint(ridge)


def wreckage(c, m, sc, fires):
    """The portal buried under the slide's head; rubble where the approach and the
    trestle fell into the chasm; charred stumps of the trestle's bents; boulders down the
    slide's sides; the pit glowing green."""
    z_at = sc.ground
    # The buried portal: a heap where it stood, a broken beam or two of its frame.
    line = c.mine
    i = std.mine_index(line, std.PORTAL_AT)
    px, py = line[i][0], line[i][1]
    if props.clear_of_road(c, px, py, 6.0):
        rk.rubble_heap(c, px, py, z_at, n=12, spread=10.0, size=3.0, seed=3)
    # Down the slide's sides: the ridge's rock in blocks, clear of the road.
    k = 0
    for x, y, z in m.SLIDE[2:-6]:
        for side in (-1, 1):
            k += 1
            if k % 3:
                continue
            ox, oy = 14.0 + 10.0 * rnd(k), (rnd(k * 1.7) - 0.5) * 6.0
            px, py = x + side * ox * 0.866 + oy * 0.5, y + side * ox * 0.5 - oy * 0.866
            if props.clear_of_road(c, px, py, 3.0) and m.crack_d(px, py) > 10.0:
                rk.rubble_heap(c, px, py, z_at, n=5, spread=4.0, size=2.4, role="both", seed=k)
                if k % 9 == 0:
                    fires.append((px, py, z_at(px, py) + 1.5))
    # Where the approach and the trestle went into the chasm: a few charred bent stumps
    # standing on the chasm's floor, rubble on its lip.
    st = rk.stub(c)
    for s in range(int(std.SEG[15]) + 70, int(std.SEG[17]), 14):
        q = std_at(c, s)
        if q is None:
            continue
        x, y = q
        if not props.clear_of_road(c, x, y, 8.0):
            continue
        zf = std.natural(x, y)
        if zf < 10.0:
            c.place(st, x, y, zf - 0.5, scale=3.0 + 2.0 * rnd(s), coll="Wreck", role="visual")
            if s % 3 == 0:
                fires.append((x, y, zf + 3.0))
        else:
            rk.rubble_heap(c, x, y, z_at, n=4, spread=5.0, size=2.2, role="visual", seed=s)
    # The pit: green light and mist rising from the chasm far below.
    cx, cy = std.CAVERN
    for k in range(6):
        a = k * math.tau / 6
        sc.green.append((cx + 22 * math.cos(a), cy + 16 * math.sin(a), -20.0))
    sc.mist.append((cx, cy, -24.0, 26.0, 6))
    sc.green.append((cx, cy, 10.0))


_STD_LINE = []


def std_at(c, s):
    """(x, y) on the standard lap s metres along (its path, not a ghost)."""
    if not _STD_LINE:
        d = 0.0
        prev = None
        for x, y, _, _ in std.STD_PATH:
            if prev:
                d += math.hypot(x - prev[0], y - prev[1])
            _STD_LINE.append((d, x, y))
            prev = (x, y)
    for d, x, y in _STD_LINE:
        if d >= s:
            return (x, y)
    return None


def town_fires(c, m, sc, fires):
    """Main Street and the saloon district burning: fires along the fronts of the
    buildings either side, up in their roofs, and embers in the road's edges."""
    S = m.SEG
    k = 0
    for s0, s1 in ((S[23] - 30.0, m.LENGTH), (0.0, S[7])):
        s = s0 + 8.0
        while s < s1:
            q = c.at(s)
            for side in (-1, 1):
                k += 1
                if k % 3 == 0:
                    continue
                p = q.side(side * (q.w / 2 + 9.0 + 4.0 * rnd(k)))
                z = sc.ground(p.x, p.y)
                fires.append((p.x, p.y, z + (7.0 + 4.0 * rnd(k * 3) if k % 2 else 1.5)))
            s += 22.0


def dress(c, m):
    sc = gs.Scene(c, m)
    gs.protos(c)
    ter = gs.land(c, m, sc)
    c.start_line()
    sc.caves = []
    fires = []
    g = rk.ghost_route(c, std.ROUTE, width=16.0, bank=7.0)
    with rk.ghost(c, g):
        c.mine = std.mine_line(c)
        # The town, Boot Hill, the mineworks (the portal is buried), the ravine.
        gt.start_arch(c, sc, std)
        gt.town(c, sc, std)
        gt.square(c, sc, std)
        gt.chapel_and_tower(c, sc, std)
        gt.street_dressing(c, sc, std)
        gt.graveyard(c, sc, std)
        gt.back_lanes(c, sc, std)
        gt.headframe(c, sc, std)
        gt.railway(c, sc, std)
        gt.mine_approach(c, sc, std)
        gs.ravine(c, sc, std)
        gs.chasm_mist(c, sc, std)
        # The ridge's crags that stood over the slide came down with it.
        crags = std.CRAGS
        std.CRAGS = tuple(cr for cr in crags if m.slide_d(cr[0], cr[1]) > cr[2] + 26.0)
        gs.rocks(c, sc, std)
        std.CRAGS = crags
        gs.road_furniture(c, sc, std)
        gs.plants(c, sc, std)
    # The ridge, slumped: cut open by the slide and the cavern's fall.
    ridge = gs.ridge_mass(c, std)
    slide_cut(c, m, ridge)
    gs.paint_ridge(c, std, ridge)
    wreckage(c, m, sc, fires)
    town_fires(c, m, sc, fires)
    fires += rk.scorch(c, BURNS, sc.ground, lambda x, y: gs.clear(c, x, y, 4.0) and sc.free(x, y, 2.0), per=5)
    print("cleared off the new road:", rk.clear_new_road(c, ("Props", "Plants", "Town Props", "Graveyard", "Mineworks", "Ravine", "Rocks")))
    gs.gameplay(c, sc, m)
    rk.emit(c, fires)
    sc.warm += fires
    gs.light(c, sc, std, ter, ridge)
    c.entity("ashfall", rate=20, radius=40)
    print("gulch ruin: fires", len(fires), "lap", round(c.length, 1))


ruin_mode.DRESS = dress

if __name__ == "__main__":
    dg.main()
