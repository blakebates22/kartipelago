# The overworld puzzles' fixed parts, for the region builds (src/overworld/puzzles.ts has
# the switches, the gate and the prize): a walled pen with a gateway in its front, the
# gate's posts, the prize's plinth, and the entities tests/overworld.test.ts checks
# regions.ts against.
# SPDX-License-Identifier: MIT
#
# (Dinosaur Valley's and the Snow Kingdom's pens came first and are written out in their
# own builds; they're the same shape.)

import math


def _shapes():
    from valley_region import box, cone

    return box, cone


def pen(c, puzzle, name, px, py, facing, half, gap, mat, floor, roof=None, height=6.0):
    """A pen at (px, py) whose gateway looks along `facing` (radians, Blender), `gap` metres
    half wide; walls of `mat` standing on `floor`. Returns the gate's middle (Blender)."""
    box, cone = _shapes()
    fx, fy = math.cos(facing), math.sin(facing)
    sx, sy = -fy, fx
    t = 0.8
    for k, (cx, cy, hx, hy) in enumerate((
            (-half, 0.0, t, half + t),
            (0.0, half, half + t, t),
            (0.0, -half, half + t, t),
            (half, (half + gap) / 2, t, (half - gap) / 2 + t),
            (half, -(half + gap) / 2, t, (half - gap) / 2 + t))):
        wx, wy = px + cx * fx + cy * sx, py + cx * fy + cy * sy
        box(c, "%s Wall %d" % (name, k), wx, wy, hx, hy, floor - 2.0, floor + height, mat, rot=facing)
    if roof:
        cone(c, name + " Roof", px, py, half * 1.55, floor + height, 7.0, roof, segs=4, role="visual")
    for side in (-1, 1):
        gx, gy = px + half * fx + side * (gap + 0.9) * sx, py + half * fy + side * (gap + 0.9) * sy
        box(c, "%s Gatepost %d" % (name, side), gx, gy, 1.2, 1.2, floor - 2.0, floor + height + 2.0, mat, rot=facing)
    box(c, name + " Plinth", px, py, 1.0, 1.0, floor - 1.0, floor + 1.2, mat, rot=facing)
    gx, _, gz = c.game(px + half * fx, py + half * fy, floor)
    c.entity("puzzle_gate", puzzle=puzzle, x=gx, z=gz, heading=math.atan2(fx, -fy), width=2 * gap,
             prize_x=c.game(px, py, 0)[0], prize_z=c.game(px, py, 0)[2])


def switches(c, puzzle, spots, ground, ring_mat=None, lanterns=None):
    """The switches' entities (Blender (x, y) spots), and a ring of three standing stones
    round each one when `ring_mat` is given."""
    _, cone = _shapes()
    for k, (x, y) in enumerate(spots):
        gx, _, gz = c.game(x, y, 0.0)
        extra = {"lanterns": lanterns[k]} if lanterns else {}
        c.entity("puzzle_switch", puzzle=puzzle, index=k, x=gx, z=gz, **extra)
        if ring_mat:
            for j in range(3):
                b = j * math.tau / 3 + k
                cone(c, "%s Switch %d Stone %d" % (puzzle, k, j), x + 7.0 * math.cos(b), y + 7.0 * math.sin(b), 1.1,
                     ground(x, y) - 1.0, 4.5, ring_mat, segs=5)


__all__ = ["pen", "switches"]
