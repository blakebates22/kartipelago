# Building a pocket region (pocket_kit.Layout) in Blender: the thresholds bored through the
# high ground, the spurs out to the gateways, and the small helpers every region needs.
# SPDX-License-Identifier: MIT
#
# (Dinosaur Valley's own build, valley_region.py, came first and has its own copies.)

import math

import course_kit as kit
from course_kit import bmesh, lerp, smooth


def box(c, name, cx, cy, hx, hy, z0, z1, mat, rot=0.0, role="both", coll="Props"):
    bm = bmesh.new()
    ca, sa = math.cos(rot), math.sin(rot)
    vs = []
    for z in (z0, z1):
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            lx, ly = sx * hx, sy * hy
            vs.append(bm.verts.new((cx + lx * ca - ly * sa, cy + lx * sa + ly * ca, z)))
    for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([vs[i] for i in f])
    ob = c.mesh_object(name, bm, coll, role)
    c.assign(ob, c.lib(*mat))
    return ob


def cone(c, name, cx, cy, r, z0, h, mat, segs=4, role="both", coll="Props"):
    bm = bmesh.new()
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=0.0, depth=h)
    for v in res["verts"]:
        v.co = kit.Vector((cx + v.co.x, cy + v.co.y, z0 + h / 2 + v.co.z))
    ob = c.mesh_object(name, bm, coll, role)
    c.assign(ob, c.lib(*mat))
    return ob


def line(natural, a, b, every=8.0, z0=None):
    """Points from a to b on the land; z0: the height it leaves from (a road it joins),
    eased into the land over its first 24 m so the joint is flush."""
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / every))
    total = math.hypot(b[0] - a[0], b[1] - a[1])
    pts = []
    for k in range(n + 1):
        x, y = lerp(a[0], b[0], k / n), lerp(a[1], b[1], k / n)
        h = natural(x, y) + 0.2
        if z0 is not None:
            h = lerp(z0 + 0.02, h, smooth(total * k / n / 24.0))
        pts.append((x, y, h))
    return pts


def to_road(c, x, y):
    """The way from (x, y) to the nearest of the main road."""
    q, _ = c.nearest(x, y)
    return math.atan2(q.p.y - y, q.p.x - x)


def spurs(c, natural, gates, look_road, trail, short=None):
    """A short road from the main road out to each gateway's landmark (12 m short of it, or
    `short`[name] m: past a landmark's fence, say), and its gateway_spot entity. Returns
    {name: ((x, y) end, heading)}."""
    out = {}
    for name, (gx, gy) in gates.items():
        smp, _ = c.nearest(gx, gy)
        ax, ay = smp.p.x, smp.p.y
        d = math.hypot(gx - ax, gy - ay)
        ux, uy = (gx - ax) / d, (gy - ay) / d
        back = (short or {}).get(name, 12.0)
        end = (gx - ux * back, gy - uy * back)
        out[name] = (end, math.atan2(-ux, uy))
        # (From the main road's edge, at its height there: a banked road's edge isn't at its
        # middle's height, and a spur laid over it from the middle stood up out of it.)
        sx, sy = ax + ux * (smp.w / 2 - 1.0), ay + uy * (smp.w / 2 - 1.0)
        z0 = road_z_at(c, sx, sy)
        c.side_road(name.title() + " Road", line(natural, (sx, sy), end, z0=smp.p.z if z0 is None else z0),
                    look_road(gx, gy), "road", **trail)
    return out


def road_z_at(c, x, y):
    """The main road's surface height at (x, y) (its pieces evaluated, banking and all), or
    None."""
    import bpy

    dg = bpy.context.evaluated_depsgraph_get()
    best = None
    for ob in getattr(c, "pieces", []):
        ev = ob.evaluated_get(dg)
        try:
            me = ev.to_mesh()
        except RuntimeError:
            continue
        if me is None:
            continue
        mw = ob.matrix_world
        for poly in me.polygons:
            cx, cy = (mw @ poly.center).x, (mw @ poly.center).y
            if abs(cx - x) > 3.0 or abs(cy - y) > 3.0:
                continue
            z = (mw @ poly.center).z
            d = math.hypot(cx - x, cy - y)
            if best is None or d < best[0]:
                best = (d, z)
        ev.to_mesh_clear()
    return None if best is None else best[1]


def emit_spots(c, spots):
    for name, (end, heading) in spots.items():
        gx, gy, gz = c.game(end[0], end[1], 0.0)
        c.entity("gateway_spot", gateway=name, x=gx, z=gz, heading=heading)


def tunnel_span(c, layout, a, b):
    """The stretch of the road (s0, s1) through the high ground round route points a..b."""
    s0 = c.nearest(*layout.route[a][:2])[0].s
    s1 = c.nearest(*layout.route[b][:2])[0].s
    if s1 < s0:
        s1 += c.length

    def inwall(s):
        q = c.at(s)
        return layout.wall_sd(q.p.x, q.p.y) > -10.0

    for _ in range(40):
        if not inwall(s0 - 3.0):
            break
        s0 -= 3.0
    for _ in range(40):
        if not inwall(s1 + 3.0):
            break
        s1 += 3.0
    return s0, s1


def bore(c, layout, name, s0, s1, wall, top, half=None, height=10.0):
    """A ridge of rock heaped over the road where it crosses the high ground (it fills the
    cut the road makes, a little under the ridge's top so it's part of it), bored through,
    the approaches cleared right down (no skin left at the mouths)."""
    mid = c.at((s0 + s1) / 2)
    half_len = (s1 - s0) / 2
    ang = math.atan2(mid.t.y, mid.t.x)
    zr = min(c.at(s0).p.z, c.at(s1).p.z)
    rock = c.rock_mass(name + " Rock", mid.p.x, mid.p.y, half_len + 16.0, 40.0, layout.top - 1.0, z0=zr - 6.0, n=30,
                       seed=len(name), angle=ang, base=zr,
                       bands=[(1.0, 0.0), (1.0, 0.3), (0.96, 0.55), (0.9, 0.8), (0.8, 0.95), (0.7, 1.0)])
    half = half or c.width / 2 + 3.0
    c.tunnel(rock, s0, s1, half=half, height=height, pad=6.0)
    for p, q in ((s0 - 70.0, s0 - 2.0), (s1 + 2.0, s1 + 70.0)):  # (overlapping the bore)
        c.tunnel(rock, p, q, half=half + 1.0, height=90.0, pad=0.0, floor=-12.0)
    c.paint_rock(rock, wall, top, top_z=layout.top - 4.0)
    return half


def entrances(c, look_at):
    """Where the main road crosses into each look: [{s, frm, to}]."""
    out = []
    prev = look_at(c.S[0].p.x, c.S[0].p.y)
    for smp in c.S:
        cur = look_at(smp.p.x, smp.p.y)
        if cur != prev:
            out.append({"s": smp.s, "frm": prev, "to": cur})
            prev = cur
    return out
