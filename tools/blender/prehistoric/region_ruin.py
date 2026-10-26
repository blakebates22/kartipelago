# The overworld regions in ruins (the overworld doc: "the region has two states, like the
# courses"): after the kingdom's dragon attacks, the same ground and roads, wrecked. Each
# region's build makes both (`python <x>_region.py --ruin` builds <x>_region_ruin), under
# the courses' sync rule: the ruin records the script it was built from (builtFrom,
# checked in tests/overworld.test.ts).
# SPDX-License-Identifier: MIT
#
# The shared pieces of wreckage. Broad strokes, all placeholder.

import math
import random
import sys

import ruin_mode

if "--ruin" in sys.argv:
    ruin_mode.ON = True
ON = ruin_mode.ON


def _shapes():
    from valley_region import box, cone

    return box, cone


def track_id(base):
    return base + "_ruin" if ruin_mode.ON else base


def scorch(c, name, spots, ground, mat=("lava_crust", "dirt"), r=(6.0, 14.0), seed=1):
    """Burnt patches on the ground (visual only, just above it)."""
    rnd = random.Random(seed)
    for k, (x, y) in enumerate(spots):
        c.disc("%s %d" % (name, k), x, y, rnd.uniform(*r), ground(x, y) + 0.12, c.lib(*mat), coll="Props", role="visual",
               n=14, wobble=0.35, seed=seed + k)


def rubble(c, name, x, y, ground, mat, n=7, spread=5.0, size=1.2, seed=1):
    """A heap of broken blocks (solid; keep it off the roads)."""
    box, _ = _shapes()
    rnd = random.Random(seed)
    for k in range(n):
        a = rnd.uniform(0, math.tau)
        d = rnd.uniform(0, spread)
        bx, by = x + d * math.cos(a), y + d * math.sin(a)
        s = size * rnd.uniform(0.6, 1.4)
        g = ground(bx, by)
        box(c, "%s %d" % (name, k), bx, by, s, s * rnd.uniform(0.6, 1.2), g - 0.6, g + s * rnd.uniform(0.6, 1.5), mat,
            rot=rnd.uniform(0, math.pi))


def smoke(c, x, y, z):
    """A column of smoke and embers (the campfire entity)."""
    gx, gy, gz = c.game(x, y, z)
    c.entity("campfire", x=gx, y=gy, z=gz)


def stump(c, name, x, y, g, mat=("obsidian_cliff", "wall"), h=4.0, r=0.6):
    """A burnt or snapped trunk: no crown."""
    box, _ = _shapes()
    box(c, name, x, y, r, r, g - 1.0, g + h, mat)


def shards(c, name, spots, ground, mat, seed=1):
    """Ice or rock shards driven into the ground (solid), leaning."""
    _, cone = _shapes()
    rnd = random.Random(seed)
    for k, (x, y) in enumerate(spots):
        cone(c, "%s %d" % (name, k), x, y, rnd.uniform(1.2, 2.4), ground(x, y) - 1.0, rnd.uniform(4.0, 9.0), mat, segs=5)


def ring_spots(n, r0, r1, seed, avoid=(), clear=9.0):
    """`n` spots between radii r0 and r1, at least `clear` degrees from every angle in
    `avoid` (the roads out)."""
    rnd = random.Random(seed)
    out = []
    while len(out) < n:
        a = rnd.uniform(-180.0, 180.0)
        if any(abs((a - b + 180.0) % 360.0 - 180.0) < clear for b in avoid):
            continue
        r = rnd.uniform(r0, r1)
        out.append((r * math.cos(math.radians(a)), r * math.sin(math.radians(a))))
    return out


def burn_away(c, burn, prefixes, threshold=0.3):
    """Delete the undergrowth (props by name or prototype) where the fire fell."""
    import bpy

    gone = [ob for ob in list(bpy.data.objects) if ob.type == "MESH" and burn(ob.location.x, ob.location.y) > threshold
            and any((ob.data.name[5:] if ob.data.name.startswith("Prop ") else ob.name).startswith(p) for p in prefixes)]
    for ob in gone:
        bpy.data.objects.remove(ob, do_unlink=True)
    return len(gone)
