# Bonebog Pyramid in ruins: Adventure's treasure map course for the swamp
# (?track=bonebog_pyramid_ruin; in dev builds Bonebog's menu entry asks Standard or Ruined).
# SPDX-License-Identifier: MIT
#
#   python tools/blender/prehistoric/bonebog_ruins.py      (the bpy module)
#
# The dragons brought the great tree down: no spiral up its trunk any more; the lap rides
# along the fallen trunk itself, from the Rib Bridge straight to the pyramid's door, then
# runs Bonebog's own course (the corridor's crests, the turning chamber, the Great Hall's
# jump, Skull Lagoon, home along the dike). About 1320 m (the full lap is 1492 m).
# bonebog_pyramid.py lays the lap out (ruin_mode.ON); this adds the wreckage: the trunk
# and its torn-up roots, the treehouse village's platforms fallen in the water, burnt
# patches, charred trees, fires, smoke and ash; much of the swamp still alive.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ruin_mode  # noqa: E402

ruin_mode.ON = True

import bonebog_pyramid as bb  # noqa: E402  (lays out the ruined lap)
import course_kit as kit  # noqa: E402
import props  # noqa: E402
import ruin_kit as rk  # noqa: E402
from course_kit import rnd  # noqa: E402

# Where the fire fell: round the fallen tree, the treehouse village, the Rib Bridge, and
# a few patches across the swamp.
BURNS = [(bb.TREE[0], bb.TREE[1], 44.0), (-20.0, 120.0, 32.0), (60.0, 90.0, 26.0), (150.0, 30.0, 30.0), (110.0, 45.0, 24.0),
         (-100.0, -150.0, 24.0), (-170.0, 20.0, 22.0), (80.0, -120.0, 22.0), (-150.0, -100.0, 20.0),
         (40.0, -101.0, 18.0), (12.0, -22.0, 18.0), (81.0, -13.0, 16.0), (-124.0, -111.0, 18.0), (-187.0, -50.0, 18.0),
         (-30.0, -116.0, 16.0)]
burn = rk.burns_fn(BURNS)

_classify = bb.classify


def classify(c, n, info):
    mat = _classify(c, n, info)
    if mat and mat[0] in ("bog_bank", "bog_moss_ground") and burn(c.x, c.y) > 0.45 + 0.2 * math.sin(c.x * 0.6 + c.y * 0.4):
        return ("ruin_ash", mat[1])
    return mat


bb.classify = classify


def dress(c, m):
    import swamp_props as sp

    ter = list(c.coll("Terrain").objects)

    def z_at(x, y):
        z = c.ground_z(x, y, ter)
        return z if z is not None else m.natural(x, y)

    def clear(x, y, margin=4.0):
        return props.clear_of_road(c, x, y, margin)

    # The trunk: a huge log under the road the whole way (the road is its bark), thick at
    # the root end, and the root plate torn out of the swamp standing on end.
    s0 = kit.s_near(c, *next(p for p in m.PATH if p[3] == 15)[:2]) - 8
    s1 = kit.s_near(c, *next(p for p in m.PATH if p[3] == 18)[:2]) - 2
    path, radii = [], []
    n = 16
    for k in range(n + 1):
        q = c.at(s0 + (s1 - s0) * k / n)
        r = 6.5 - 2.5 * k / n
        path.append((q.p.x, q.p.y, q.p.z - r - 0.2))
        radii.append(r)
    bm = kit.bmesh.new()
    props.tube(bm, path, radii, n=10)
    trunk = c.mesh_object("Fallen Trunk", bm, "Wreck", "visual")
    c.assign(trunk, c.lib("bog_root", "wall"))
    q = c.at(s0)
    back = q.p - q.t * 6.0
    plate = c.rock_mass("Root Plate", back.x, back.y, 4.0, 16.0, q.p.z + 12.0, z0=-3.0, n=14, seed=7,
                        angle=math.atan2(q.t.y, q.t.x), bands=[(0.6, 0.0), (1.0, 0.3), (1.1, 0.6), (0.9, 0.85), (0.5, 1.0)])
    plate["kp_role"] = "visual"
    c.assign(plate, c.lib("bog_root", "wall"))
    # The treehouse village's platforms and huts, fallen into the water round the trunk.
    plat = sp.platform(c, 0)
    for k in range(6):
        a = k * 1.1 + 0.4
        x, y = m.TREE[0] - 30 + 40 * rnd(k * 2.3), m.TREE[1] + 10 + 30 * math.sin(a)
        if clear(x, y, 8.0):
            c.place(plat, x, y, m.WATER_Z - 0.6, rot=a, scale=0.9, coll="Wreck", role="visual")
            c.place(sp.stilt_hut(c, k % 2), x + 3, y - 2, m.WATER_Z - 2.5, rot=a + 0.4, scale=0.9, coll="Wreck", role="visual")
    fires = rk.scorch(c, BURNS, z_at, clear, per=4, wet=lambda x, y, z: z < m.WATER_Z + 0.4)
    for k in range(4):
        q = c.at(s0 + (s1 - s0) * (0.15 + 0.23 * k))
        p = q.side((1 if k % 2 else -1) * (q.w / 2 + 3.5))
        fires.append((p.x, p.y, q.p.z - 1.0))  # embers along the trunk's flanks
    spots = []
    print("charred trees", rk.char_trees(c, burn, ("Swamp Giant", "Tier Tree", "Palm", "Jungle Tree"), chance=0.7,
                                         scales={"Swamp Giant": 4.2, "Tier Tree": 1.6, "Palm": 1.4, "Jungle Tree": 1.4}, out=spots))
    st = rk.stub(c)
    for k, (x, y, z) in enumerate(spots):
        if k % 2 == 0:  # the fallen giants' neighbours still burning at their feet
            c.place(st, x + 2.5, y, z - 0.3, rot=k, scale=2.2, coll="Wreck", role="visual")
            fires.append((x + 2.5, y, z + 2.0))
    rk.emit(c, fires, glow_on=ter)
    c.entity("ashfall", rate=40, radius=40)
    print("bonebog ruin: fires", len(fires))


ruin_mode.DRESS = dress

if __name__ == "__main__":
    bb.main()
