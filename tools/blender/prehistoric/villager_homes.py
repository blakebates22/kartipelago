# The villagers' homes (Blake, Oct 26: dinosaur folk walking about in every part of every
# overworld, so we need houses): a few homes in each pocket of a region (or each part of a
# journey), off the road, facing it, and a `villager_home` entity before each for the game
# to walk its folk about (src/overworld/villagers.ts).
# SPDX-License-Identifier: MIT

import math
import random

import region_paint as paint
from pocket_build import box


def adobe(c, name, x, y, z, rot, k):
    """A desert home: an adobe block, a flat roof with its beams out, a dark door, an
    awning."""
    ca, sa = math.cos(rot), math.sin(rot)

    def at(lx, ly):
        return x + lx * ca - ly * sa, y + lx * sa + ly * ca

    w, d = (5.0, 4.0, 6.0)[k % 3], (4.0, 4.5, 3.6)[k % 3]
    box(c, name, x, y, w / 2, d / 2, z - 1.0, z + 3.6 + 0.6 * (k % 2), ("adobe", "wall"), rot=rot)
    for j in range(4):
        bx, by = at(-w / 2 + 0.6 + j * (w - 1.2) / 3, -d / 2 - 0.3)
        box(c, name + " Beam %d" % j, bx, by, 0.15, 0.45, z + 3.1, z + 3.35, ("weathered_timber", "wall"), rot=rot,
            role="visual")
    dx, dy = at(0.0, -d / 2 - 0.05)
    box(c, name + " Door", dx, dy, 0.6, 0.08, z, z + 2.0, ("dark_corridor", "wall"), rot=rot, role="visual")
    ax, ay = at(0.0, -d / 2 - 1.0)
    box(c, name + " Awning", ax, ay, w / 2 - 0.4, 1.0, z + 2.4, z + 2.55, (("tent_cloth", "tent_cloth_red")[k % 2], "wall"),
        rot=rot, role="visual")


def _built():
    """What's been built already (landmarks, pens, gates: anything up to 30 m across), as
    (x, y, r) circles: no home goes on them."""
    import bpy
    from mathutils import Vector

    out = []
    for ob in bpy.data.objects:
        if ob.type != "MESH" or not ob.users_collection:
            continue
        if ob.users_collection[0].name not in ("Props", "Rocks", "Collision", "Water"):
            continue
        pts = [ob.matrix_world @ Vector(b) for b in ob.bound_box]
        xs, ys = [p.x for p in pts], [p.y for p in pts]
        r = max(max(xs) - min(xs), max(ys) - min(ys)) / 2
        if r < 30.0:
            out.append(((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, r + 2.0))
    return out


def homes(c, layout, ground, folk, house, per=2, pockets=None, room=13.0, near=(9.0, 26.0), roam=14.0, n=(2, 3),
          seed=7, skip=(), avoid=()):
    """Up to `per` homes in each of the layout's pockets (or `pockets`: names), each built
    by house(c, name, x, y, z, rot, k) facing the road, and its villager_home entity.
    `skip`: pockets with none (the hub's own houses are elsewhere, say); `avoid`: (x, y, r)
    circles to keep clear. Returns the spots taken [(x, y, r)] (region_paint.EXTRA keeps
    the dressing off them)."""
    rnd = random.Random(seed)
    taken = paint.Taken(list(avoid) + _built())
    out = []
    k = 0
    plist = getattr(layout, "pockets", None) or layout.POCKETS
    names = pockets or [p[0] for p in plist]
    for pname in names:
        if pname in skip:
            continue
        placed = 0
        circles = next(p[2] for p in plist if p[0] == pname)
        for _ in range(400):
            if placed >= per:
                break
            cx, cy, cr, _f = circles[rnd.randrange(len(circles))]
            a = rnd.uniform(0, math.tau)
            r = cr * math.sqrt(rnd.random())
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            if layout.pocket_at(x, y) != pname or layout.wall_sd(x, y) > -9.0:
                continue
            if not taken.clear(x, y, room) or not paint.road_clear(c, x, y, near[0]) or paint.road_clear(c, x, y, near[1]):
                continue
            z = ground(x, y)
            ring = [ground(x + 5.0 * math.cos(t), y + 5.0 * math.sin(t)) for t in (0.0, 1.57, 3.14, 4.71)]
            if max(ring) - min(ring) > 1.6:
                continue  # (too steep to build on)
            q, _ = c.nearest(x, y)
            face = math.atan2(q.p.y - y, q.p.x - x)
            rot = face + math.pi / 2  # (its front, local -y, to the road)
            house(c, "Home %s %d" % (pname.title(), k), x, y, min(ring) + 0.05, rot, k)
            # The yard before it: where its folk walk about.
            fx, fy = x + math.cos(face) * 6.0, y + math.sin(face) * 6.0
            g = c.game(fx, fy, ground(fx, fy))
            c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=roam,
                     n=rnd.randint(*n), folk=folk, heading=round(math.atan2(-math.cos(face), math.sin(face)), 3))
            taken.add(x, y, room)
            out.append((x, y, room * 0.6))
            placed += 1
            k += 1
    paint.EXTRA.extend(out)
    return out


def proto_house(proto_fn, sink=0.2):
    """A house from a prop prototype: proto_fn(c, k) -> proto name."""
    def house(c, name, x, y, z, rot, k):
        c.place(proto_fn(c, k), x, y, z - sink, rot=rot, name=name)
    return house
