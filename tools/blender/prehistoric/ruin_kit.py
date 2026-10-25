# The dragons' wreckage for the ruined courses (Adventure's treasure map challenge): burnt
# stubs glowing at their broken tops, charred trees where the fire fell (replacing a
# course's own trees in place), rubble heaps, fires (game torches), smoke (campfire
# smoke) and the warm glow they paint on the land. riverbend_ruins.py came first and
# keeps its own copy; Cascade's and Bonebog's ruins use this.
# SPDX-License-Identifier: MIT

import math
from contextlib import contextmanager

import props
from aurora_scenery import game_entity
from course_kit import rnd, smooth


def burns_fn(burns, reach=1.4, soft=0.7):
    """burn(x, y) -> 0..1, how scorched the ground is, from (x, y, r) circles."""

    def burn(x, y):
        return max(smooth((reach * r - math.hypot(x - bx, y - by)) / (r * soft)) for bx, by, r in burns)

    return burn


def stub(c):
    """A burnt stump or post: charred wood, glowing at its broken top."""
    name = "Charred Stub"
    if name in c.protos:
        return name

    def build(bm):
        from props import _faces, loft, ring

        rings = [ring(bm, (0, 0), r, z, 6) for r, z in ((0.45, 0.0), (0.4, 1.4), (0.3, 2.2))]
        loft(bm, rings, cap_top=False)
        wood = _faces(bm, 0)
        k0 = len(bm.faces)
        top = [bm.verts.new((0.3 * math.cos(a), 0.3 * math.sin(a), 2.2 + (0.4 if i % 2 else 0.0)))
               for i, a in enumerate(k * math.tau / 6 for k in range(6))]
        bm.faces.new(top)
        return [(c.lib("ruin_char"), wood), (c.lib("ruin_ember"), _faces(bm, k0))]

    return c.proto(name, build) and name


def char_trees(c, burn, prefixes, colls=None, chance=0.8, scale=1.4, threshold=0.25, scales=None, out=None):
    """Most of the course's trees where the fire fell become charred stems (the same
    spots). Matches objects by name or by their prototype mesh's ("Prop <name>");
    `scales`: a scale per prefix (a charred giant stays giant); `out` collects the spots."""
    import bpy

    me = c.protos[props.dead_tree(c)]
    obs = [o for name in colls for o in c.coll(name).objects] if colls else list(bpy.data.objects)
    n = 0
    for ob in obs:
        if ob.type != "MESH" or ob.data is me:
            continue
        name = ob.data.name[5:] if ob.data.name.startswith("Prop ") else ob.name
        hit = next((p for p in prefixes if name.startswith(p) or ob.name.startswith(p)), None)
        if hit is None:
            continue
        x, y = ob.location.x, ob.location.y
        if burn(x, y) > threshold and rnd(x * 0.37 + y * 0.71) < chance:
            k = (scales or {}).get(hit, scale) * (ob.scale.x if scales else 1.0)
            ob.data = me
            ob.scale = (k, k, k)
            if out is not None:
                out.append((x, y, ob.location.z))
            n += 1
    return n


def rubble_heap(c, x, y, z_at, n=9, spread=6.0, size=1.6, coll="Wreck", role="both", seed=0):
    rubble = [props.boulder(c, "ruin_rubble", v) for v in range(3)]
    for k in range(n):
        a = (k + seed) * 2.39996
        r = spread * math.sqrt((k + 0.5) / n)
        px, py = x + r * math.cos(a), y + r * math.sin(a)
        c.place(rubble[(k + seed) % 3], px, py, z_at(px, py) - 0.3, rot=k * 1.3 + seed, scale=size * (0.7 + 0.6 * rnd(k + seed * 7)),
                coll=coll, role=role)


def scorch(c, burns, z_at, clear, per=4, wet=None):
    """Charred trees and burning stubs scattered in each burn; returns the fires."""
    tree, st = props.dead_tree(c), stub(c)
    fires = []
    k = 0
    for bx, by, br in burns:
        for m in range(per):
            k += 1
            a, rr = rnd(k * 1.7) * math.tau, br * 0.8 * rnd(k * 2.3)
            x, y = bx + rr * math.cos(a), by + rr * math.sin(a)
            z = z_at(x, y)
            if (wet and wet(x, y, z)) or not clear(x, y):
                continue
            if m % 2 == 0:
                c.place(tree, x, y, z - 0.2, rot=k, scale=1.2 + 0.6 * rnd(k), coll="Wreck", role="visual")
            else:
                c.place(st, x, y, z - 0.3, rot=k, scale=1.6, coll="Wreck", role="visual")
                fires.append((x, y, z + 1.2))
    return fires


def emit(c, fires, smoke_every=2, glow_on=None, color=(1.6, 0.9, 0.5)):
    """Game torches at the fires, smoke from every other one, their glow on the land."""
    for x, y, z in fires:
        game_entity(c, "torch", x, y, z)
    for x, y, z in fires[::smoke_every]:
        game_entity(c, "campfire", x, y, z - 0.6)
    if glow_on:
        c.glow(glow_on, fires, 9.0, color, base=1.0)


# ---------------------------------------------------------------- the old lap's scenery


def ghost_route(c, route, **kw):
    """Sample a course's STANDARD route without keeping it (the ruin's own route stays
    the course's). Returns what `ghost` needs. Call after the ruin's c.route()."""
    import bpy

    real = (c.S, c.length, c.route_ob, c.width)
    c.route(route, **kw)
    g = (c.S, c.length)
    bpy.data.objects.remove(c.route_ob, do_unlink=True)
    c.S, c.length, c.route_ob, c.width = real
    c._near_tree = None
    return g


@contextmanager
def ghost(c, g):
    """Inside: c.at(), c.nearest() and friends follow the standard lap, so the course's
    own scenery code places its landmarks where they always were (the sync rule: the
    ruin is built from the course's scenery, not a copy). Anything placed also keeps
    clear of the ruin's real road (it's added to c.extra_ground meanwhile)."""
    real = (c.S, c.length, c.extra_ground)
    c.S, c.length = g
    c._near_tree = None
    c.extra_ground = list(real[2]) + real[0][::2]
    try:
        yield
    finally:
        c.S, c.length, c.extra_ground = real
        c._near_tree = None


def clear_new_road(c, colls, margin=2.5, height=9.0):
    """Remove anything in `colls` standing on the ruin's real road (old scenery placed
    from the standard lap that the new road now runs through). Returns how many."""
    import bpy

    gone = 0
    for name in colls:
        for ob in list(c.coll(name).objects):
            if ob.type != "MESH":
                continue
            mw = ob.matrix_world
            corners = [mw @ kit_vec(v) for v in ob.bound_box]
            xs = [p.x for p in corners]
            ys = [p.y for p in corners]
            zs = [p.z for p in corners]
            cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            r = max(max(xs) - min(xs), max(ys) - min(ys)) / 2
            if r > 40:
                continue  # big merged scenery: left alone
            smp, d = c.nearest(cx, cy)
            if d < smp.w / 2 + margin + r * 0.7 and min(zs) < smp.p.z + height and max(zs) > smp.p.z - 2:
                bpy.data.objects.remove(ob, do_unlink=True)
                gone += 1
    return gone


def kit_vec(v):
    from mathutils import Vector

    return Vector(v)
