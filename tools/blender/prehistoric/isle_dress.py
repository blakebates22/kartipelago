# Tropic Isles v4's dressing, the deep pass (Blake, Nov 1: "rigorously go through beach and
# desert world and do the stuff that you have been seeing me do with dino and snow ... like
# nothing floating, make it immersive for that level"): each gateway's stretch of coast
# dressed from its own course's kit, the way Frostveil wears the citadel's:
#
#   the village      Raptor's square a real deck of planks on land graded level (not a
#                    plane laid over the sand), its huts graded level round it, bunting
#                    strung torch to torch, the tiki bar, canoes on the beach, lamps down
#                    the island hop's pier;
#   Coral Cove       its palm-trunk start arch, flags down both sides of the road, the red-
#                    and-white lighthouse on its rock, buoys off the beach, beach huts;
#   Splash Lagoon    its slide tower (lagoon_scenery's own) and two spiral slides into
#                    their pools, flags along the road;
#   Shipwreck Bay    a galleon on her side in the shallows, the pirates' camp (stockade,
#                    lookout, huts, cannons, the flag), lantern posts along the road, Skull
#                    Rock offshore, treasure at its feet;
#   the Volcano pier lamps down both sides, boats moored along it;
#   the jungle       tiki torches along the trail, the old carved stone heads by it.
#
# Every hut on land graded level under it; every prop on the lowest ground under it.
# SPDX-License-Identifier: MIT

import math
import random

import beach_props as bp
import isle_layout as M
import lagoon_scenery as ls
import props
import region_paint as paint
import tropic_props as tp
from canyon_props import _beam
from course_kit import Vector, bmesh, rnd
from keep_scenery import Scene, clear_of
from oasis_desert import Mesh
from props import _faces, blob, cuboid, loft, ring, tube

WATER_Z = M.WATER_Z


def road_rot(q):
    return math.atan2(q.t.y, q.t.x)


def across(q):
    return road_rot(q) - math.pi / 2


def _runs(c, test, step=2.0):
    runs, cur = [], None
    s = 0.0
    while s < c.length:
        if test(c.at(s)):
            cur = [s, s] if cur is None else [cur[0], s]
        elif cur:
            runs.append(tuple(cur))
            cur = None
        s += step
    if cur:
        runs.append(tuple(cur))
    return runs


def _ring(ground, x, y, r):
    return [ground(x + r * math.cos(t), y + r * math.sin(t)) for t in [k * math.tau / 8 for k in range(8)]] + [ground(x, y)]


def _lowest(ground, x, y, r):
    return min(_ring(ground, x, y, r))


def _spread(ground, x, y, r):
    hs = _ring(ground, x, y, r)
    return max(hs) - min(hs)


def _dry(x, y, margin=2.0):
    """Out of the sea, the lagoon and the river (by margin)."""
    lx, ly, lr = M.LAGOON
    return (M.inland(x, y) > margin and math.hypot(x - lx, y - ly) > lr + margin + 6.0
            and M.river_d(x, y)[0] > M.RIVER_HW + margin)


class _DK:
    natural = staticmethod(M.natural)
    RUIN = False


def scene(c, ter, **kw):
    dk = _DK()
    for k, v in kw.items():
        setattr(dk, k, v)
    return Scene(c, dk, ter)


def _find(c, ground, taken, x0, y0, rmin, rmax, room, road, spread, test=lambda x, y: True):
    """The nearest spot to (x0, y0), rmin to rmax from it, with `room` clear (of what's
    taken), `road` clear of every road, dry, its ground within `spread` across: or None."""
    k = 0
    while True:
        a = k * 2.399
        r = rmin + 0.35 * k
        if r > rmax:
            return None
        x, y = x0 + r * math.cos(a), y0 + r * math.sin(a)
        if (test(x, y) and _dry(x, y, room * 0.5) and clear_of(c, x, y, road) and taken.clear(x, y, room)
                and _spread(ground, x, y, room * 0.6) < spread):
            return x, y
        k += 1


def _seat(c, ground, ter, x, y, rot, w, d, front=2.0):
    """Grade the land level under a footprint at its mean height; that height."""
    hs = [ground(x + dx, y + dy) for dx in (-w / 2, 0.0, w / 2) for dy in (-d / 2, 0.0, d / 2)]
    z = sum(hs) / len(hs)
    paint.grade(c, ter, x, y, rot, w, d, z, front=front)
    return z


# ------------------------------------------------------------------ the village


def village_deck(c, ground, ter):
    """Raptor's square: a round deck of planks laid on land graded level (not a plane over
    the sand), a beam round its edge, its skirt down into the sand all round."""
    hx, hy, hr = M.HUB
    hz = M.natural(hx, hy)
    paint.grade(c, ter, hx, hy, 0.0, 2 * hr + 2.0, 2 * hr + 2.0, hz, front=0.0)
    n = 48
    bm = bmesh.new()
    top = [bm.verts.new((hx + hr * math.cos(k * math.tau / n), hy + hr * math.sin(k * math.tau / n), hz + 0.12)) for k in range(n)]
    mid = bm.verts.new((hx, hy, hz + 0.12))
    for k in range(n):
        bm.faces.new((mid, top[k], top[(k + 1) % n]))
    deck = len(bm.faces)
    low = [bm.verts.new((hx + hr * math.cos(k * math.tau / n), hy + hr * math.sin(k * math.tau / n), hz - 0.8)) for k in range(n)]
    for k in range(n):
        bm.faces.new((top[k], low[k], low[(k + 1) % n], top[(k + 1) % n]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = c.mesh_object("Village Deck", bm, "Props", "both")
    c.assign(ob, c.lib("wood_dock", "road"), range(deck))
    c.assign(ob, c.lib("tiki_wood", "wall"), range(deck, len(ob.data.polygons)))
    return hz + 0.12


def village(c, ground, taken, ter, hz):
    """Round the square: beach huts on land graded level, their doors to it; bunting strung
    torch to torch round it; the tiki bar; drums by the fire; canoes pulled up on the
    beach below; lamps down both sides of the island hop's pier."""
    hx, hy, hr = M.HUB
    placed = []
    n = 0
    spots = [(k * math.tau / 10 + 0.15, hr + 8.0) for k in range(10)] + [((k + 0.5) * math.tau / 10 + 0.15, hr + 19.0) for k in range(10)]
    for k, (a, r) in enumerate(spots):
        x, y = hx + r * math.cos(a), hy + r * math.sin(a)
        if any(math.hypot(x - ox, y - oy) < 8.5 for ox, oy in placed):
            continue
        # (The square's own ground is taken: only the roads, the pier and the sea keep huts off.)
        if not clear_of(c, x, y, 5.0) or not _dry(x, y, 4.0):
            continue
        rot = a + math.pi / 2  # (its door to the square)
        if _spread(ground, x, y, 3.5) > 3.0:
            continue
        z = _seat(c, ground, ter, x, y, rot, 6.5, 6.5, front=2.0)
        c.place(tp.beach_hut(c, k % 4), x, y, z - 0.1, rot=rot + math.pi, coll="Village", role="both")
        taken.add(x, y, 5.0)
        placed.append((x, y))
        n += 1
    # The tiki bar at the square's edge, facing in.
    for a in (2.4, 3.6, 4.4):
        x, y = hx + (hr + 4.0) * math.cos(a), hy + (hr + 4.0) * math.sin(a)
        if clear_of(c, x, y, 4.0) and _dry(x, y, 3.0):
            z = _seat(c, ground, ter, x, y, a, 7.0, 5.0)
            c.place(bp.tiki_bar(c), x, y, z - 0.1, rot=a + math.pi / 2, coll="Village", role="both")
            taken.add(x, y, 4.5)
            break
    # Drums by the fire.
    for k in range(3):
        a = k * 2.1 + 0.5
        x, y = hx + 3.4 * math.cos(a), hy + 3.4 * math.sin(a)
        c.place(bp.drum(c), x, y, hz, rot=a, coll="Village", role="both")
    # Bunting torch to torch round the square (the torches: isle_region.village).
    tops = []
    for k in range(12):
        a = k * math.tau / 12 + 0.26
        x, y = hx + (hr + 1.5) * math.cos(a), hy + (hr + 1.5) * math.sin(a)
        tops.append((x, y, ground(x, y) + 2.4) if paint.road_clear(c, x, y, 1.0) else None)
    for k in range(12):
        p0, p1 = tops[k], tops[(k + 1) % 12]
        if p0 and p1:
            bp.string_line(c, "Village Bunting %d" % k, p0, p1, 0.6, kind="bunting", coll="Village")
    # Canoes pulled up on the beach below the square.
    m = 0
    for j in range(240):
        a = j * 2.399
        r = hr + 12.0 + 0.25 * j
        x, y = hx + r * math.cos(a), hy + r * math.sin(a)
        if m >= 4 or not (0.5 < M.inland(x, y) < 10.0) or not clear_of(c, x, y, 3.0) or not taken.clear(x, y, 3.0):
            continue
        c.place(bp.canoe(c, m % 2), x, y, _lowest(ground, x, y, 1.6) - 0.05, rot=a + math.pi / 2, coll="Village", role="both")
        taken.add(x, y, 3.0)
        m += 1
    # The way in from the island hop (review-beach_region 1 note 1: "this whole front entrance
    # looks terrible"): a palm-trunk welcome arch over the pier's foot where it leaves the
    # square, flags under it; tiki torches and flag poles either side; bunting from the arch
    # to the square's torches.
    (ax, ay), (bx, by) = M.HOP_PIER
    ux, uy = (bx - ax), (by - ay)
    d = math.hypot(ux, uy)
    ux, uy = ux / d, uy / d
    gx, gy = hx + (hr + 2.0) * ux, hy + (hr + 2.0) * uy
    rot = math.atan2(uy, ux) + math.pi / 2  # (the arch spans across the pier)
    c.place(tp.start_arch(c, span=15.0, h=7.8, flag="cove_flag"), gx, gy, hz - 0.1, rot=rot, coll="Village", role="visual")
    for sd in (-1, 1):
        px, py = gx - uy * sd * 7.5, gy + ux * sd * 7.5
        c.place(paint.trunk_proto(c, 0.5, 8.0), px, py, hz - 0.5, coll="Collision", role="collision")
        for f, kind in ((-3.5, "torch"), (3.0, "flag")):
            x, y = gx - uy * sd * 9.5 + ux * f, gy + ux * sd * 9.5 + uy * f
            z = _lowest(ground, x, y, 0.6)
            if kind == "torch":
                c.place(bp.tiki_torch(c, 0), x, y, z, coll="Village")
                g = c.game(x, y, z + 2.6)
                c.entity("torch", x=g[0], y=g[1], z=g[2])
            else:
                c.place(tp.flag_pole(c, flag="cove_flag", h=9.0), x, y, z - 0.2, coll="Village")
        top = (px, py, hz + 7.2)
        k = min(range(12), key=lambda j: math.hypot(tops[j][0] - px, tops[j][1] - py) if tops[j] else 1e9)
        if tops[k]:
            bp.string_line(c, "Pier Bunting %d" % sd, top, tops[k], 0.8, kind="bunting", coll="Village")
    print("village: %d huts, %d canoes" % (n, m))


def pier_lamps(c, name, a, b, z, every=12.0, off=4.6, start=0.0):
    """Lamps down both sides of a pier from a to b at deck height z (from `start` m along
    it, where it's reached that height), a light on every other."""
    (ax, ay), (bx, by) = a, b
    L = math.hypot(bx - ax, by - ay)
    tx, ty = (bx - ax) / L, (by - ay) / L
    nx, ny = -ty, tx
    post = tp.lamp_post(c)
    k = 0
    d = start + every / 2
    while d < L - 2.0:
        for sd in (-1, 1):
            x, y = ax + tx * d + nx * sd * off, ay + ty * d + ny * sd * off
            c.place(post, x, y, z, rot=math.atan2(-ny * sd, -nx * sd), coll="Village", role="both")
            if k % 2 == 0:
                g = c.game(x, y, z + 3.3)
                c.entity("lantern", x=g[0], y=g[1], z=g[2])
            k += 1
        d += every
    return k


# ------------------------------------------------------------------ the gateways' coasts


def _gate_s(c, name):
    gx, gy = M.GATES[name]
    smp, _ = c.nearest(gx, gy)
    return smp.s


def flags_along(c, ground, taken, s0, s1, flag, every=14.0, pole="cove_white"):
    """Flag poles down both sides of the road from s0 to s1, every `every` m."""
    n = 0
    s = s0
    while s < s1:
        q = c.at(s)
        for sd in (-1, 1):
            p = q.side(sd * (q.w / 2 + 2.6))
            if clear_of(c, p.x, p.y, 1.0) and taken.clear(p.x, p.y, 0.5) and _dry(p.x, p.y, 0.5):
                c.place(tp.flag_pole(c, flag, 6.0, pole), p.x, p.y, _lowest(ground, p.x, p.y, 0.3) - 0.3,
                        rot=road_rot(q) + (math.pi / 2 if sd > 0 else -math.pi / 2), coll="Village", role="both")
                taken.add(p.x, p.y, 0.6)
                n += 1
        s += every
    return n


def coral_cove(c, ground, taken, ter):
    """Coral Cove's coast: its palm-trunk start arch over the road before the gateway, flags
    down both sides, the red-and-white lighthouse on its rock out on the bay's point, buoys
    off the beach, a row of beach huts."""
    sg = _gate_s(c, "coral")
    q = c.at(sg - 50.0)
    c.place(tp.start_arch(c, q.w + 13.0), q.p.x, q.p.y, q.p.z - 0.2, rot=across(q), coll="Village", role="both")
    nf = flags_along(c, ground, taken, sg - 110.0, sg + 60.0, "cove_flag")
    # The lighthouse: on the shore's rock nearest the gateway, out of the road's way.
    gx, gy = M.GATES["coral"]
    best = None
    for k in range(400):
        a = k * 2.399
        r = 30.0 + 0.2 * k
        x, y = gx + r * math.cos(a), gy + r * math.sin(a)
        if -6.0 < M.inland(x, y) < 3.0 and clear_of(c, x, y, 16.0) and taken.clear(x, y, 9.0):
            best = (x, y)
            break
    if best:
        x, y = best
        rk = tp.rock_island(c, "Lighthouse Rock", x, y, 8.0, 7.0, 5.0, ("cove_rock", "wall"), ("cove_grass", "grass"), seed=4,
                            z0=WATER_Z - 4.0)
        rk["kp_role"] = "both"  # (solid: the lighthouse stands on it)
        c.place(tp.lighthouse(c), x, y, 4.6, coll="Village", role="both")
        g = c.game(x, y, 4.6 + 17.8)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
        taken.add(x, y, 10.0)
    # Buoys in a line off the beach either side of the gateway.
    nb = 0
    for k in range(-5, 6):
        q = c.at(sg + k * 14.0)
        for off in (40.0, 52.0, 64.0):
            sd = 1 if M.inland(*q.side(30.0).xy) < M.inland(*q.side(-30.0).xy) else -1
            p = q.side(sd * off)
            if M.inland(p.x, p.y) < -6.0:
                c.place(tp.buoy(c, "cove_lighthouse" if k % 2 else "cove_awning_sun"), p.x, p.y, WATER_Z - 0.2, coll="Village",
                        role="visual")
                nb += 1
                break
    # Beach huts in a row along the road's landward side, every 16 m.
    nh = 0
    for k, ds in enumerate(range(-96, 50, 16)):
        q = c.at(sg + ds)
        sd = -1 if M.inland(*q.side(30.0).xy) < M.inland(*q.side(-30.0).xy) else 1
        p = q.side(sd * (q.w / 2 + 9.0))
        if not (clear_of(c, p.x, p.y, 5.0) and taken.clear(p.x, p.y, 4.0) and _dry(p.x, p.y, 3.0)) or _spread(ground, p.x, p.y, 3.5) > 2.5:
            continue
        rot = math.atan2(q.p.y - p.y, q.p.x - p.x) + math.pi / 2
        z = _seat(c, ground, ter, p.x, p.y, rot, 6.0, 6.0)
        c.place(tp.beach_hut(c, k % 4), p.x, p.y, z - 0.1, rot=rot + math.pi, coll="Village", role="both")
        taken.add(p.x, p.y, 5.0)
        nh += 1
    print("coral cove: %d flags, %d buoys, %d huts, lighthouse %s" % (nf, nb, nh, bool(best)))


def splash(c, ground, taken, ter):
    """Splash Lagoon's park by the lagoon: its slide tower (lagoon_scenery's own, round a
    solid core) back from the gateway, two spiral slides beside it into their pools, flags
    along the road."""
    from pocket_build import box

    sg = _gate_s(c, "splash")
    gx, gy = M.GATES["splash"]
    q = c.at(sg)
    # (Near the gateway, off the road, on ground that can be graded level.)
    best = _find(c, ground, taken, gx, gy, 24.0, 110.0, 12.0, 14.0, 5.0)
    if not best:
        print("splash: no room for the tower")
        return
    tx, ty = best
    tz = _seat(c, ground, ter, tx, ty, 0.0, 22.0, 22.0, front=0.0)
    TOP = 14.0
    box(c, "Slide Tower Core", tx, ty, 8.2, 8.2, tz - 1.0, tz + TOP, ("party_white", "wall"))
    for ob in c.coll("Props").objects:
        if ob.name.startswith("Slide Tower Core"):
            ob["kp_role"] = "collision"
    sc = scene(c, ter, TOWER=(tx, ty), TOP=tz + TOP)
    ls.tower(sc)
    taken.add(tx, ty, 16.0)
    for k, (dx, dy, mat) in enumerate(((22.0, 8.0, "splash_slide_red"), (-20.0, 12.0, "splash_slide_blue"))):
        sx, sy = tx + dx, ty + dy
        if clear_of(c, sx, sy, 14.0) and _dry(sx, sy, 10.0) and taken.clear(sx, sy, 8.0):
            ls.slide(sc, "Splash Slide %d" % k, sx, sy, 10.0 + 2.0 * k, 1.25, 4.0, mat)
            taken.add(sx, sy, 11.0)
    nf = flags_along(c, ground, taken, sg - 70.0, sg + 50.0, "cove_flag", pole="party_white")
    print("splash: tower at (%.0f, %.0f), %d flags" % (tx, ty, nf))


def galleon_hull(c):
    """A galleon's hull lying on her side: planked ribs of a long round-bottomed hull, the
    deck's edge with its rail, a high stern; laid over 30 degrees (her keel to +Y). Origin
    at her middle at the waterline; about 34 m long."""
    name = "Galleon Hull"

    def build(bm):
        L, B, D = 34.0, 10.0, 7.5
        tilt = math.radians(32.0)
        ct, st = math.cos(tilt), math.sin(tilt)
        rings = []
        n = 14
        for i in range(n + 1):
            u = i / n
            x = -L / 2 + L * u
            # (fuller amidships, fine at the bow (-X), squarer at the stern (+X))
            wfac = math.sin(math.pi * min(1.0, 0.15 + 0.85 * u)) ** 0.5 if u < 0.9 else 0.85
            hb = B / 2 * max(0.15, wfac)
            top = D + (2.5 if u > 0.8 else 0.0) + 1.2 * (1 - u) ** 3
            pts = []
            for j in range(9):
                a = math.pi * j / 8  # (round the bottom, side to side)
                yy = -hb * math.cos(a)
                zz = -D * 0.55 * math.sin(a) * max(0.25, wfac)
                pts.append((yy, zz))
            pts = [(-hb, top - D)] + pts + [(hb, top - D)]
            ring_v = []
            for yy, zz in pts:
                # (tilt over about the long axis)
                ry, rz = yy * ct - zz * st, yy * st + zz * ct
                ring_v.append(bm.verts.new((x, ry, rz)))
            rings.append(ring_v)
        for r0, r1 in zip(rings, rings[1:]):
            for k in range(len(r0) - 1):
                bm.faces.new((r0[k], r1[k], r1[k + 1], r0[k + 1]))
        bm.faces.new(rings[0])
        bm.faces.new(list(reversed(rings[-1])))
        hull = _faces(bm, 0)
        k0 = len(bm.faces)
        # The rail along her high side, and the stern castle's windows.
        for i in range(0, n, 2):
            x = -L / 2 + L * i / n
            yy, zz = rings[i][-1].co.y, rings[i][-1].co.z
            cuboid(bm, (x, yy, zz + 0.5), (0.2, 0.2, 1.0))
        rail = _faces(bm, k0)
        # Her masts, leaning over with her: the main whole with a yard and a torn sail, the
        # fore snapped short.
        k1 = len(bm.faces)

        def tilt_pt(x, y, z):
            return (x, y * ct - z * st, y * st + z * ct)

        for x, h in ((-2.0, 17.0), (-11.0, 7.0)):
            tube(bm, [tilt_pt(x, 0.0, 0.0), tilt_pt(x, 0.0, h)], [0.45, 0.32], n=8)
        _beam(bm, tilt_pt(-2.0, -5.5, 13.0), tilt_pt(-2.0, 5.5, 13.0), 0.22)
        spars = _faces(bm, k1)
        k2 = len(bm.faces)
        corners = ((-5.2, 12.8), (5.2, 12.8), (4.0, 7.5), (-4.6, 8.4))  # (torn at its foot)
        bm.faces.new([bm.verts.new(tilt_pt(-1.8, y, z)) for y, z in corners])
        bm.faces.new([bm.verts.new(tilt_pt(-2.2, y, z)) for y, z in reversed(corners)])  # (seen from both sides)
        sail = _faces(bm, k2)
        return [(c.lib("wreck_hull", "wall"), hull), (c.lib("wreck_trim", "wall"), rail + spars), (c.lib("wreck_sail", "wall"), sail)]

    return c.proto(name, build) and name


def shipwreck(c, ground, taken, ter):
    """Shipwreck Bay's coast: the galleon on her side in the shallows off the gateway, a
    broken mast and a torn sail on her, the pirates' camp ashore (a stockade round it, the
    lookout, huts, cannons on the beach facing the sea, the flag), lantern posts down the
    road, Skull Rock out in the bay with treasure at its feet."""
    sg = _gate_s(c, "wreck")
    gx, gy = M.GATES["wreck"]
    q = c.at(sg)
    sea = 1 if M.inland(*q.side(30.0).xy) < M.inland(*q.side(-30.0).xy) else -1
    # The galleon: in the shallows seaward of the gateway.
    hull = None
    for off in (34.0, 42.0, 50.0, 26.0):
        p = q.side(sea * (q.w / 2 + off))
        if M.inland(p.x, p.y) < -3.0 and clear_of(c, p.x, p.y, 18.0) and taken.clear(p.x, p.y, 10.0):
            hull = p
            break
    if hull:
        rot = road_rot(q)
        c.place(galleon_hull(c), hull.x, hull.y, WATER_Z + 2.0, rot=rot, coll="Village", role="both")
        taken.add(hull.x, hull.y, 20.0)
    # The camp ashore, landward of the road.
    land = -sea
    p = q.side(land * (q.w / 2 + 30.0))
    found = _find(c, ground, taken, p.x, p.y, 0.0, 70.0, 14.0, 12.0, 5.0)
    camp = Vector((found[0], found[1], 0.0)) if found else None
    nh = 0
    if camp:
        cx, cy = camp.x, camp.y
        z = _seat(c, ground, ter, cx, cy, road_rot(q), 28.0, 24.0, front=0.0)
        rot = road_rot(q)
        ca, sa = math.cos(rot), math.sin(rot)

        def at(u, v):
            return cx + u * ca - v * sa, cy + u * sa + v * ca

        # The stockade: back and sides (its open front to the road).
        for (u, v), r, L in (((0.0, -land * 12.0), 0.0, 24.0), ((-12.0, 0.0), math.pi / 2, 22.0), ((12.0, 0.0), math.pi / 2, 22.0)):
            x, y = at(u, v)
            if clear_of(c, x, y, 4.0):
                c.place(tp.stockade(c, L), x, y, z - 0.2, rot=rot + r, coll="Village", role="both")
        x, y = at(-9.0, -land * 9.0)
        c.place(tp.watchtower(c), x, y, z - 0.2, rot=rot + 0.3, coll="Village", role="both")
        g = c.game(x, y, z + 10.6)
        c.entity("torch", x=g[0], y=g[1], z=g[2])
        for k, (u, v) in enumerate(((-4.0, -land * 7.0), (5.0, -land * 7.5))):
            x, y = at(u, v)
            c.place(tp.pirate_hut(c, k % 2), x, y, z - 0.1, rot=rot + (math.pi if land < 0 else 0.0), coll="Village", role="both")
            nh += 1
        x, y = at(0.0, 0.0)
        c.place(props.campfire(c), x, y, z - 0.1, coll="Village", role="both")
        g = c.game(x, y, z + 1.2)
        c.entity("campfire", x=g[0], y=g[1], z=g[2])
        x, y = at(8.0, land * 4.0)
        c.place(tp.flag_pole(c, "wreck_flag", 10.0, "wreck_iron"), x, y, z - 0.3, coll="Village", role="both")
        for k in range(4):
            x, y = at(-8.0 + 4.5 * k, -land * 2.0)
            c.place((tp.barrel(c), tp.crate(c), tp.chest(c, True), tp.barrel(c))[k], x, y, z - 0.05, rot=k * 1.3, coll="Village",
                    role="both")
        taken.add(cx, cy, 18.0)
    # Cannons on the beach facing the sea, either side of the gateway.
    ncan = 0
    for ds in (-40.0, -24.0, 24.0, 40.0):
        q2 = c.at(sg + ds)
        p = q2.side(sea * (q2.w / 2 + 6.0))
        if clear_of(c, p.x, p.y, 2.5) and taken.clear(p.x, p.y, 2.0) and M.inland(p.x, p.y) > 1.0:
            c.place(tp.cannon(c), p.x, p.y, _lowest(ground, p.x, p.y, 1.2), rot=math.atan2(q2.r.y * sea, q2.r.x * sea) - math.pi / 2,
                    coll="Village", role="both")
            taken.add(p.x, p.y, 2.0)
            ncan += 1
    # Lantern posts down the road, by turns either side, every 16 m.
    post = tp.lantern_post(c)
    nl = 0
    for j, ds in enumerate(range(-80, 81, 16)):
        q2 = c.at(sg + ds)
        sd = 1 if j % 2 else -1
        p = q2.side(sd * (q2.w / 2 + 2.6))
        if clear_of(c, p.x, p.y, 0.6) and taken.clear(p.x, p.y, 0.4) and _dry(p.x, p.y, 0.5):
            z = _lowest(ground, p.x, p.y, 0.3)
            c.place(post, p.x, p.y, z, rot=road_rot(q2) + (math.pi / 2 if sd > 0 else -math.pi / 2), coll="Village", role="both")
            if j % 2 == 0:
                g = c.game(p.x, p.y, z + 3.3)
                c.entity("lantern", x=g[0], y=g[1], z=g[2])
            nl += 1
    # Skull Rock: out in the bay.
    sk = None
    for off in (90.0, 110.0, 130.0):
        for ds in (60.0, -60.0, 100.0, -100.0):
            q2 = c.at(sg + ds)
            p = q2.side(sea * off)
            if M.inland(p.x, p.y) < -20.0:
                sk = p
                break
        if sk:
            break
    if sk:
        face = math.atan2(q.p.y - sk.y, q.p.x - sk.x) - math.pi / 2
        tp.rock_island(c, "Skull Rock", sk.x, sk.y, 11.0, 9.0, 18.0, ("isle_rock", "wall"), ("isle_jungle", "grass"), seed=9,
                       z0=WATER_Z - 6.0)
        c.place(tp.skull_face(c, 9.5, 17.0), sk.x + 3.0 * math.cos(face + math.pi / 2), sk.y + 3.0 * math.sin(face + math.pi / 2),
                -0.6, rot=face, coll="Village", role="visual")
    print("shipwreck: hull %s, camp %s (%d huts), %d cannons, %d lanterns, skull rock %s" % (bool(hull), bool(camp), nh, ncan, nl,
                                                                                           bool(sk)))


def volcano_pier(c, a, b, z):
    """The Volcano Isle pier: lamps down both sides, boats moored along it."""
    n = pier_lamps(c, "Volcano Pier", a, b, z, every=12.0, off=4.6)
    (ax, ay), (bx, by) = a, b
    L = math.hypot(bx - ax, by - ay)
    tx, ty = (bx - ax) / L, (by - ay) / L
    nx, ny = -ty, tx
    for j, (t, sd) in enumerate(((0.35, 1), (0.6, -1), (0.85, 1))):
        x, y = ax + tx * L * t + nx * sd * 11.0, ay + ty * L * t + ny * sd * 11.0
        if M.inland(x, y) < -2.0:
            c.place(tp.sailboat(c, j), x, y, WATER_Z, rot=math.atan2(ty, tx) + 0.3 * sd, coll="Village", role="visual")
    print("volcano pier: %d lamps" % n)


# ------------------------------------------------------------------ the jungle


def tiki_head(c, variant=0):
    """An old carved stone head in the jungle: a tall block of mossy stone, a heavy brow,
    deep eyes, a broad nose, a long mouth; moss on its crown. About 4.5 m; faces -Y."""
    name = "Stone Head %d" % variant

    def build(bm):
        h = 4.2 + 0.6 * variant
        cuboid(bm, (0, 0, h / 2 - 0.6), (2.4, 1.9, h + 1.2))
        cuboid(bm, (0, -1.0, h * 0.72), (2.6, 0.5, 0.45))  # brow
        cuboid(bm, (0, -1.05, h * 0.5), (0.7, 0.5, 1.2))  # nose
        cuboid(bm, (0, -1.0, h * 0.3), (1.7, 0.35, 0.35))  # lips
        stone = _faces(bm, 0)
        k0 = len(bm.faces)
        for sx in (-0.6, 0.6):
            cuboid(bm, (sx, -0.97, h * 0.62), (0.55, 0.1, 0.4))
        cuboid(bm, (0, -0.86, h * 0.3), (1.3, 0.1, 0.12))
        dark = _faces(bm, k0)
        k1 = len(bm.faces)
        blob(bm, (0, 0, h), 1.3, sx=1.0, sy=0.8, sz=0.35, subdiv=1)
        moss = _faces(bm, k1)
        return [(c.lib("jungle_mossstone", "wall"), stone), (c.lib("dark_corridor", "wall"), dark), (c.lib("isle_jungle", "wall"), moss)]

    return c.proto(name, build) and name


def jungle(c, ground, taken):
    """The trail through the jungle: tiki torches by turns either side every 30 m (a fire on
    every other), and the old stone heads standing back from it every 90 m or so."""
    torch = bp.tiki_torch(c, 0)
    nt = nh = 0
    for s0, s1 in _runs(c, lambda q: M.look_at(q.p.x, q.p.y) == "jungle"):
        if s1 - s0 < 60.0:
            continue
        s, j = s0 + 15.0, 0
        while s < s1 - 10.0:
            q = c.at(s)
            sd = 1 if j % 2 else -1
            p = q.side(sd * (q.w / 2 + 2.2))
            if clear_of(c, p.x, p.y, 0.6) and taken.clear(p.x, p.y, 0.4) and _dry(p.x, p.y, 0.5) and _spread(ground, p.x, p.y, 0.4) < 0.6:
                z = _lowest(ground, p.x, p.y, 0.3)
                c.place(torch, p.x, p.y, z, coll="Village", role="both")
                if j % 2 == 0:
                    g = c.game(p.x, p.y, z + 2.6)
                    c.entity("torch", x=g[0], y=g[1], z=g[2])
                taken.add(p.x, p.y, 0.6)
                nt += 1
            if j % 3 == 1:
                p = q.side(-sd * (q.w / 2 + 6.5))
                if clear_of(c, p.x, p.y, 3.0) and taken.clear(p.x, p.y, 2.0) and _dry(p.x, p.y, 2.0) and _spread(ground, p.x, p.y, 1.4) < 1.5:
                    c.place(tiki_head(c, nh % 2), p.x, p.y, _lowest(ground, p.x, p.y, 1.4) - 0.1,
                            rot=math.atan2(q.p.y - p.y, q.p.x - p.x) + math.pi / 2, coll="Village", role="both")
                    taken.add(p.x, p.y, 2.0)
                    nh += 1
            s += 30.0
            j += 1
    print("jungle: %d torches, %d stone heads" % (nt, nh))

