# Loop Lab: a plain test circuit for the loop-the-loop (Test World).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/loop_lab.py      (the bpy module)
#
# A long straight with a boost pad into one big loop-the-loop, a straight out of it, and
# two hairpins back round to the start: just enough circuit to race and time the loop
# (src/game/loops.ts) with the AI, checkpoints and laps. Undecorated on purpose: flat
# snowfield, a few rocks for a sense of speed. Saves tracks-src/loop_lab.blend and
# exports public/tracks/loop_lab/.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import course_kit as kit  # noqa: E402  (first: it imports bpy)

TRACK_ID = "loop_lab"

# The loop: radius of its circular part, easing length at each end, sideways shift.
R, RAMP, SHIFT = 22.0, 26.0, 18.0
AHEAD, _ = kit.loop_layout(R, RAMP, SHIFT)
START = (0.0, -150.0)
ROAD_Z = 0.5
TAIL = 40.0  # start line to the end of the lap's last straight
LAYOUT = [
    ("S", 110),  # 0 the straight: start, boost pad, into the loop
    ("LOOP", R, RAMP, SHIFT),  # 1
    ("S", 70),  # 2 out of the loop
    ("L", 45, 180),  # 3 hairpin west
    ("S", 0),  # 4 back south (length set below)
    ("L", 36, 180),  # 5 hairpin east, onto the start line's x
    ("S", TAIL),  # 6
]
# Close the lap: the last straight ends where the lap started.
LAYOUT[4] = ("S", 110 + AHEAD + 70 + TAIL)
PATH = kit.turtle(LAYOUT, START, 90.0)
SEG = kit.segment_starts(PATH)


def road_z(d, seg):
    return ROAD_Z


def road_w(d, seg):
    return 14.0


ROUTE, SHARP, LOOPS = kit.route_with_loops(PATH, LAYOUT, road_z, every=10.0, width=road_w)


def natural(x, y):
    # A flat snowfield, rising into low hills well away from the road.
    r = math.hypot(x / 1.4, y - 40)
    return 0.0 + max(0.0, r - 230) * 0.35 + 3 * math.sin(x / 37) * math.cos(y / 29) * min(1, max(0, (r - 200) / 60))


def classify(c, n, info):
    if n.z < 0.7:
        return ("summit_cliff", "wall")
    if info["d"] < 11:
        return ("summit_road", "packed_snow")
    return ("summit_snow", "deep_snow")


def main():
    c = kit.Course(TRACK_ID, "Loop Lab", "summit_pass")
    (ex, ey, _), (xx, xy, _) = LOOPS[0]
    c.route(ROUTE, width=14.0, bank=6.0, sharp=SHARP, flat=[(ex, ey, 45), (xx, xy, 45)])
    c.kinds = {
        "road": {"mat": "summit_road", "shoulder": 1.5, "shoulder_mat": ("summit_snow", "packed_snow"), "barrier": 0.8, "barrier_mat": ("summit_snow", "wall")},
        "straight": {
            "mat": "summit_road",
            "shoulder": 1.5,
            "shoulder_mat": ("summit_snow", "packed_snow"),
            "barrier": 0.8,
            "barrier_mat": ("summit_snow", "wall"),
            "exact": True,
        },
    }
    s_in = kit.s_near(c, ex, ey)
    s_out = kit.s_near(c, xx, xy)
    # The pieces either side of the loop end dead straight at it.
    c.roads(kit.plan(c, [(s_in - 60, s_in, "straight"), (s_in, s_out, None), (s_out, s_out + 50, "straight")], "road"))
    lp = kit.LoopPath(ex, ey, ROAD_Z, 90.0, R, RAMP, SHIFT, 14.0)
    c.loop(
        lp,
        road_mat=("crystal_road", "ice"),
        side_mat=("glacier_ice", "wall"),
        rail_mat=("summit_stone_road", "wall"),
        glow_mat=("crystal_blue", "wall"),
    )

    X0, X1, Y0, Y1 = -420, 420, -420, 460
    c.terrain("Land", X0, X1, Y0, Y1, 8.0, natural, classify, near=9.0, fade=16.0)
    c.underfloor_flat("Underfloor", X0, X1, Y0, Y1, 8.0, lambda x, y: natural(x, y) - 0.4, c.lib("summit_snow", "deep_snow"))
    c.start_line()
    # The boost pad 45 m before the loop, a second on the back straight.
    c.zipper(s_in - 45, 0)
    c.zipper(SEG[4] + 60, 0)
    c.bananas(SEG[4] + 120, 0, count=5, gap=2.6)
    c.balloon(SEG[2] + 30, 0, "red")
    c.balloon(SEG[2] + 30, 4, "blue")
    c.checkpoints(extra=[s_in - 20, s_out + 20, SEG[4] + 80], height=8.0)

    # Rocks along the straights, for a sense of speed.
    c.proto("Rock", lambda bm: _rock(c, bm))
    rock = "Rock"
    for k in range(18):
        s = SEG[4] + 10 + k * 22
        smp = c.at(s)
        for side in (-1, 1):
            p = smp.p + smp.r * side * (14 + 6 * ((k * 7 + side) % 3))
            c.place(rock, p.x, p.y, natural(p.x, p.y) - 0.3, rot=k * 1.3, scale=1.2 + (k % 3) * 0.5, role="visual")
    ter = list(c.coll("Terrain").objects)
    c.preset("sun", ter, 0.2)
    kit.paint.shade_roads(c.pieces, 0.3)
    c.finish()


def _rock(c, bm):
    import bmesh

    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.6)
    for v in bm.verts:
        v.co.z *= 0.7
        v.co.x *= 1.3
    return [(c.lib("summit_rock", "wall"), range(len(bm.faces)))]


if __name__ == "__main__":
    main()
