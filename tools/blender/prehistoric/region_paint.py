# Dressing the overworld regions (the paint pass after the greybox): scattering the
# courses' own props (tools/blender/prehistoric/props.py) over a region's open ground,
# off its roads and clear of its landmarks.
# SPDX-License-Identifier: MIT

import math
import random


class Taken:
    """Circles already used (landmarks, gateways, puzzles, earlier props): nothing goes
    inside them."""

    def __init__(self, spots=()):
        self.spots = list(spots)

    def add(self, x, y, r):
        self.spots.append((x, y, r))

    def clear(self, x, y, r=0.0):
        return all(math.hypot(x - sx, y - sy) > sr + r for sx, sy, sr in self.spots)


def road_clear(c, x, y, margin):
    """Far enough from the ring road and every side road."""
    smp, d = c.nearest(x, y)
    if d <= smp.w / 2 + margin:
        return False
    return all((q.p.x - x) ** 2 + (q.p.y - y) ** 2 > (q.w / 2 + margin) ** 2 for q in c.extra_ground)


def trunk_proto(c, r, h):
    """A plain hexagonal post (`r` across its corners, `h` tall), for a tree's collision."""
    name = "Trunk Collider %.2f %.1f" % (r, h)

    def build(bm):
        lo = [bm.verts.new((r * math.cos(k * math.tau / 6), r * math.sin(k * math.tau / 6), -1.0)) for k in range(6)]
        hi = [bm.verts.new((v.co.x, v.co.y, h)) for v in lo]
        for k in range(6):
            bm.faces.new((lo[k], lo[(k + 1) % 6], hi[(k + 1) % 6], hi[k]))
        bm.faces.new(list(reversed(lo)))
        bm.faces.new(hi)
        return [(c.lib("valley_cliff", "wall"), list(range(8)))]

    return c.proto(name, build) and name


def scatter(c, proto, n, rmax, ok, ground, taken, seed, room=3.0, scale=(0.8, 1.3), role="both", sink=0.2,
            near_road=None, tries=60, instead=None, road_margin=3.0, trunk=None):
    """Up to `n` copies of `proto` at random spots within `rmax` of the middle where
    ok(x, y) holds, `room` metres clear of everything taken (they're taken in turn).
    `near_road` (m0, m1): only that far from a road's edge, e.g. lining it. `instead(x,
    y, z, scale)`: put something else at each of the same spots (a ruin's wreck of it).
    `trunk` (radius, height): a tree: it's only seen, and a plain post round its trunk is
    what a kart hits (its boughs' sloping faces would be floors a kart could drive up
    onto, and get caught under)."""
    rnd = random.Random(seed)
    placed = []
    for _ in range(n * tries):
        if len(placed) >= n:
            break
        a = rnd.uniform(0, math.tau)
        r = rmax * math.sqrt(rnd.random())
        x, y = r * math.cos(a), r * math.sin(a)
        if not ok(x, y) or not taken.clear(x, y, room):
            continue
        if near_road:
            if not road_clear(c, x, y, near_road[0]) or road_clear(c, x, y, near_road[1]):
                continue
        elif not road_clear(c, x, y, road_margin):
            continue
        s = rnd.uniform(*scale)
        rot = rnd.uniform(0, math.tau)
        if instead:
            instead(x, y, ground(x, y), s)
        else:
            if trunk:
                c.place(proto, x, y, ground(x, y) - sink, rot=rot, scale=s, role="visual")
                c.place(trunk_proto(c, *trunk), x, y, ground(x, y) - sink, scale=s, coll="Collision", role="collision")
            else:
                c.place(proto, x, y, ground(x, y) - sink, rot=rot, scale=s, role=role)
        taken.add(x, y, room * 0.5)
        placed.append((x, y))
    return placed
