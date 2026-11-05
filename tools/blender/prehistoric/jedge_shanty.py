# The Night Bazaar as a smugglers' shantytown (Blake, Nov 5, review journey_cause 1: "what
# was the pirate space place in the show skeleton crew? I want to capture some of those
# general vibes without doing space theme"): Port Borgo's crammed, grimy, patched-together
# feel, done with what washes up at the Edge of the World. The smugglers dragged their
# wrecks in here and built the market out of them.
# SPDX-License-Identifier: MIT
#
#   shacks       hull halves and salvaged planks, every wall a different wood, boards
#                nailed over the holes, upturned boats for roofs, sail and canvas
#                lean-tos, a second storey up a ladder; stovepipes smoking, portholes lit,
#                wanted posters, a lantern on a hook, barrels, crates and nets about; the
#                alleys between them full of crocs (notes 7 and 8: the empty floor);
#   the stage    the bow of a wreck beached on the floor, a scruffy band of three on its
#                deck (a squeezebox, a fiddle, a drum on a barrel), the crowd sat about on
#                crates eating and talking, a few nodding along (note 2, in place of the
#                dancers: "if we do the shanty band right it could work. my concern is its
#                going to look super cheesey": kept low-key, background, no dancing);
#   flags        tattered smuggler flags (a croc's skull and crossed bones, jaws, a
#                patchwork with an anchor) where the bright banners hung (note 9);
#   net lines    ropes slung across hung with fishing nets, floats and a ship's lantern,
#                where the lantern strings were (note 6).
#
# jedge_districts.bazaar() calls stage() and shanty(); the flags and net lines are used by
# the bazaar, the Gallery and Spice Row (jedge_rookery).

import math

from course_kit import lerp
from gulch_scenery import Mesh
import props
from props import cuboid
import gulch_props as gp
import harbour_props as hp
import region_paint as paint
import jedge_rookery as R
from jedge_layout import BAZAAR, ellipse

FLAGS = ("edge_flag_skull", "edge_flag_jaw", "edge_flag_patch")
AWNINGS = ("edge_awning_rust", "edge_awning_slate", "edge_awning_ochre", "edge_canvas_grime")
PLANKS = ("wreck_hull", "weathered_timber", "door_wood", "wreck_planks", "barrel_wood", "siding_grey", "siding_brown")
rnd = R.rnd
local = R.local
facing = R.facing


def two_sided(m, mat, pts, uvs):
    m.quad((mat, "wall"), pts, uvs)
    m.quad((mat, "wall"), list(reversed(pts)), list(reversed(uvs)))


def flag(m, top, across, w, h, mat, k, strips=4):
    """A tattered flag hung from its top edge (the middle of it at `top`, x y z), across
    (ax, ay): the whole picture on it once, its hem torn ragged (each strip of it a
    different length, one torn short)."""
    ax, ay = across
    short = int(rnd(k * 3.7) * strips)
    for i in range(strips):
        u0, u1 = i / strips, (i + 1) / strips
        drop = (0.74 + 0.26 * rnd(k * 7.1 + i)) * (0.62 if i == short else 1.0)
        drop2 = (0.74 + 0.26 * rnd(k * 7.1 + i + 1)) * (0.62 if i + 1 == short else 1.0) if i + 1 < strips else 0.8 + 0.2 * rnd(k)
        a = (top[0] + ax * (u0 - 0.5) * w, top[1] + ay * (u0 - 0.5) * w)
        b = (top[0] + ax * (u1 - 0.5) * w, top[1] + ay * (u1 - 0.5) * w)
        za, zb = top[2] - h * drop, top[2] - h * min(drop, drop2)
        two_sided(m, mat, [(a[0], a[1], za), (b[0], b[1], zb), (b[0], b[1], top[2]), (a[0], a[1], top[2])],
                  [(u0, 1 - drop), (u1, 1 - min(drop, drop2)), (u1, 1), (u0, 1)])


def flag_pole(m, x, y, z, h, k, face=(1.0, 0.0)):
    """A pole (a broken oar, a spar) with a smuggler flag hung off its top."""
    m.add(R.W, lambda bm: props.tube(bm, [(x, y, z), (x, y, z + h)], 0.07, n=5))
    fx, fy = face
    ax, ay = -fy, fx
    m.add(R.W, lambda bm: props.tube(bm, [(x, y, z + h - 0.15), (x + ax * 1.5, y + ay * 1.5, z + h - 0.15)], 0.04, n=4))
    flag(m, (x + ax * 0.78, y + ay * 0.78, z + h - 0.15), (ax, ay), 1.4, 2.2, FLAGS[k % len(FLAGS)], k, strips=3)


def net_line(c, m, p0, p1, sag, k):
    """A rope slung between two points hung with fishing nets, cork floats and, now and
    then, a ship's lantern (in place of the lantern strings: note 6)."""
    n = 10
    pts = [(lerp(p0[0], p1[0], i / n), lerp(p0[1], p1[1], i / n), lerp(p0[2], p1[2], i / n) - sag * 4 * (i / n) * (1 - i / n))
           for i in range(n + 1)]
    m.add(("rope_rail", "wall"), lambda bm: props.tube(bm, pts, 0.035, n=3))
    span = math.dist(p0[:2], p1[:2])
    dx, dy = (p1[0] - p0[0]) / span, (p1[1] - p0[1]) / span

    def at(t):
        return lerp(p0[0], p1[0], t), lerp(p0[1], p1[1], t), lerp(p0[2], p1[2], t) - sag * 4 * t * (1 - t)

    panels = max(1, int(span / 4.0))
    for q in range(panels):
        t0 = (q + 0.18) / panels
        t1 = (q + 0.82) / panels
        if rnd(k * 5.3 + q) < 0.3:
            # (a lantern on its hook instead)
            x, y, z = at((t0 + t1) / 2)
            m.add(("keep_iron", "wall"), lambda bm, x=x, y=y, z=z: props.tube(bm, [(x, y, z), (x, y, z - 0.4)], 0.015, n=3))
            c.place(hp.cage_lantern(c, k + q), x, y, z - 0.4, role="visual")
            R.D.light(c, "lantern", x, y, z - 0.7)
            continue
        a, b = at(t0), at(t1)
        drop = 1.0 + 0.6 * rnd(k * 2.9 + q)
        cols = 5
        for i in range(cols + 1):
            t = i / cols
            x, y = lerp(a[0], b[0], t), lerp(a[1], b[1], t)
            ztop = lerp(a[2], b[2], t)
            bottom = ztop - drop * (1 - 0.35 * (4 * t * (1 - t)))
            m.add(("rope_rail", "wall"), lambda bm, x=x, y=y, ztop=ztop, bottom=bottom: props.tube(bm, [(x, y, ztop), (x, y, bottom)], 0.012, n=3))
        for j in range(1, 4):
            row = []
            for i in range(cols + 1):
                t = i / cols
                ztop = lerp(a[2], b[2], t)
                row.append((lerp(a[0], b[0], t), lerp(a[1], b[1], t), ztop - drop * (j / 3.6) * (1 - 0.35 * (4 * t * (1 - t)))))
            m.add(("rope_rail", "wall"), lambda bm, row=row: props.tube(bm, row, 0.012, n=3))
        for f in range(2):
            t = 0.3 + 0.4 * f
            x, y = lerp(a[0], b[0], t), lerp(a[1], b[1], t)
            z = lerp(a[2], b[2], t) - drop * 0.8
            m.add((("lantern_glass", "barrel_wood")[(k + q + f) % 2], "wall"),
                  lambda bm, x=x, y=y, z=z: props.blob(bm, (x, y, z), 0.13, subdiv=1))


def hull(bm, cx, cy, z, rot, length, width, height, upturned=True, bow=1.0, stern=0.8, n=10, m=7):
    """A boat's hull lofted from sections: `upturned` (keel up, for a roof) or upright
    (keel down, a beached bow). Along local X; `bow` and `stern` how pointed each end
    (1 closes to a point, less leaves a transom). Both faces of every panel."""
    ca, sa = math.cos(rot), math.sin(rot)
    rings = []
    for i in range(n + 1):
        t = -1.0 + 2.0 * i / n
        end = bow if t > 0 else stern
        half = width / 2 * math.sqrt(max(0.0, 1.0 - end * abs(t) ** 2.4))
        hh = height * (0.9 + 0.1 * (1 - t * t)) * (0.35 + 0.65 * (half / (width / 2)) ** 0.5)
        ring = []
        for j in range(m + 1):
            a = math.pi * j / m
            lx = t * length / 2
            ly = math.cos(a) * half
            lz = math.sin(a) * hh if upturned else -math.sin(a) * hh
            ring.append(bm.verts.new((cx + lx * ca - ly * sa, cy + lx * sa + ly * ca, z + lz)))
        rings.append(ring)
    for i in range(n):
        for j in range(m):
            q = (rings[i][j], rings[i + 1][j], rings[i + 1][j + 1], rings[i][j + 1])
            if len({v.index for v in q}) == 4:
                bm.faces.new(q)
                bm.faces.new(q[::-1])
    for ring in (rings[0], rings[-1]):
        pts = [v.co.copy() for v in ring]
        if math.dist(pts[0], pts[-1]) > 0.2:
            vs = [bm.verts.new(p) for p in pts]
            bm.faces.new(vs)
            bm.faces.new([bm.verts.new(p) for p in reversed(pts)])


def ladder(m, a, b, z0, z1):
    """Two rails and rungs from (a) to (b) side by side, z0 up to z1."""
    for p in (a, b):
        m.add(R.W, lambda bm, p=p: props.tube(bm, [(p[0], p[1], z0), (p[0], p[1], z1)], 0.04, n=4))
    zz = z0 + 0.35
    while zz < z1:
        m.add(R.W, lambda bm, zz=zz: props.tube(bm, [(a[0], a[1], zz), (b[0], b[1], zz)], 0.03, n=3))
        zz += 0.4


def shack(c, m, solid, x, y, z, rot, k):
    """One of the shanty's shacks, its front (local -Y) to `rot`: salvaged walls, every one
    a different wood with boards nailed over the holes, a door and a lit porthole, its
    roof an upturned boat, or planks with a second storey up a ladder, or a canvas
    lean-to over a chowder counter; a stovepipe smoking, a wanted poster, a lantern on a
    hook, a flag, barrels and crates about. Returns its door (x, y) and kind."""
    w = 3.4 + 1.6 * rnd(k * 1.3)
    d = 2.8 + 1.2 * rnd(k * 2.1)
    h = 2.3 + 0.5 * rnd(k * 3.3)
    kind = ("hull", "stack", "stand", "hull", "stack")[k % 5]
    lean = (rnd(k * 4.1) - 0.5) * 0.05

    def P(lx, ly, lz=0.0):
        px, py = local(x, y, rot, lx, ly)
        return px, py, z + lz

    def slab(tgt, mat, lx, ly, lz, sx, sy, sz, tilt=(0.0, 0.0)):
        px, py, _ = P(lx, ly)
        tgt.add((mat, "wall"), lambda bm: cuboid(bm, (px, py, z + lz), (sx, sy, sz), rot, tilt=tilt))

    # (the body, for collision; its walls each a different wood)
    solid.add((PLANKS[k % len(PLANKS)], "wall"), lambda bm: cuboid(bm, (x, y, z + h / 2), (w, d, h), rot, tilt=(lean, 0.0)))
    for q, (lx, ly, sx, sy) in enumerate(((0, -d / 2 - 0.04, w, 0.08), (0, d / 2 + 0.04, w, 0.08), (-w / 2 - 0.04, 0, 0.08, d), (w / 2 + 0.04, 0, 0.08, d))):
        slab(m, PLANKS[(k * 3 + q + 1) % len(PLANKS)], lx, ly, h / 2, sx, sy, h * (0.92 + 0.08 * rnd(k + q)), (lean, 0.0))
    # (boards nailed over the holes, at angles)
    for q in range(2 + k % 3):
        lx = (rnd(k * 5.1 + q) - 0.5) * (w - 1.0)
        lz = 0.5 + rnd(k * 6.3 + q) * (h - 1.0)
        slab(m, PLANKS[(k + q * 2) % len(PLANKS)], lx, -d / 2 - 0.1, lz, 1.0 + 0.6 * rnd(q + k), 0.05, 0.2, (0.0, (rnd(k * 7 + q) - 0.5) * 0.9))
    # (the door and a porthole, lit)
    slab(m, "door_wood", -w / 4, -d / 2 - 0.09, 0.95, 0.85, 0.06, 1.9)
    px, py, _ = P(w / 4, -d / 2 - 0.1)
    m.add(("window_warm", "wall"), lambda bm: props.blob(bm, (px, py, z + 1.55), 0.26, sy=0.2, subdiv=1))
    m.add(("keep_iron", "wall"), lambda bm: props.tube(bm, [P(w / 4 - 0.3, -d / 2 - 0.12, 1.55), P(w / 4 + 0.3, -d / 2 - 0.12, 1.55)], 0.03, n=4))
    # The roof.
    top = h
    if kind == "hull":
        L_, Wd = w + 1.0, d + 0.8
        m.add(("wreck_hull", "wall"), lambda bm: hull(bm, x, y, z + h, rot, L_, Wd, 1.1 + 0.3 * rnd(k), upturned=True, bow=1.0, stern=0.7))
        top = h + 1.2
    elif kind == "stack":
        slab(m, "wreck_planks", 0, 0, h + 0.1, w + 0.5, d + 0.5, 0.14, (0.12, 0.0))
        if k % 2 == 0:
            # (a second storey, smaller, set back, its own sail roof; a ladder up)
            w2, d2, h2 = w * 0.6, d * 0.7, 1.9
            ox = (rnd(k * 8.1) - 0.5) * (w - w2) * 0.8
            slab(solid, PLANKS[(k + 3) % len(PLANKS)], ox, d * 0.1, h + 0.2 + h2 / 2, w2, d2, h2, (-lean, 0.0))
            wx, wy, _ = P(ox, -d * 0.1 - d2 / 2 + d * 0.2 - 0.05)
            m.add(("window_warm", "wall"), lambda bm: cuboid(bm, (wx, wy, z + h + 1.2), (0.5, 0.05, 0.45), rot))
            corners = [P(ox - w2 / 2 - 0.2, d * 0.1 - d2 / 2 - 0.3, h + h2 + 0.6), P(ox + w2 / 2 + 0.2, d * 0.1 - d2 / 2 - 0.3, h + h2 + 0.4),
                       P(ox + w2 / 2 + 0.2, d * 0.1 + d2 / 2 + 0.3, h + h2 + 0.1), P(ox - w2 / 2 - 0.2, d * 0.1 + d2 / 2 + 0.3, h + h2 + 0.3)]
            R.cloth(m, ("wreck_sail", "edge_canvas_grime")[k % 2], corners)
            a, b = P(w / 2 + 0.25, -0.3), P(w / 2 + 0.25, 0.3)
            ladder(m, a, b, z, z + h + 0.8)
            top = h + h2 + 0.6
    else:
        # (a canvas lean-to out front over a chowder counter; the cookpot steaming)
        aw = AWNINGS[k % len(AWNINGS)]
        for sd in (-1, 1):
            m.add(R.W, lambda bm, sd=sd: props.tube(bm, [P(sd * (w / 2 - 0.2), -d / 2 - 1.8), P(sd * (w / 2 - 0.2), -d / 2 - 1.8, h - 0.5)], 0.06, n=4))
        R.cloth(m, aw, [P(-w / 2 - 0.1, -d / 2, h), P(w / 2 + 0.1, -d / 2, h + 0.1), P(w / 2 + 0.2, -d / 2 - 2.0, h - 0.55), P(-w / 2 - 0.2, -d / 2 - 2.0, h - 0.4)])
        slab(solid, "barrel_wood", 0, -d / 2 - 0.9, 0.5, w - 0.6, 0.7, 1.0)
        slab(m, "plank_deck", 0, -d / 2 - 0.95, 1.04, w - 0.4, 0.9, 0.08)
        cx_, cy_, _ = P(-w / 4, -d / 2 - 0.9)
        m.add(("keep_iron", "wall"), lambda bm: props.tube(bm, [(cx_, cy_, z + 1.08), (cx_, cy_, z + 1.45)], 0.26, n=10))
        g = c.game(cx_, cy_, z + 1.5)
        c.entity("steam", x=round(g[0], 2), y=round(g[1], 2), z=round(g[2], 2))
        for q in range(4):
            bx, by, _ = P(w / 8 + q * 0.32, -d / 2 - 1.05)
            m.add(("party_white", "wall"), lambda bm, bx=bx, by=by: props.tube(bm, [(bx, by, z + 1.08), (bx, by, z + 1.18)], 0.09, n=6))
        R.sign(m, "sign_soup", *P(w / 4, -d / 2 - 0.12)[:2], *_n(rot), 0.45, z + h - 0.75, z + h - 0.3, out=0.0)
    # (a stovepipe through the roof, smoking)
    if k % 3 != 1:
        sx_, sy_, _ = P(w / 2 - 0.6, d / 2 - 0.5)
        m.add(("keep_iron", "wall"), lambda bm: props.tube(bm, [(sx_, sy_, z + h - 0.2), (sx_, sy_, z + top + 0.9)], 0.11, n=6))
        R.D.light(c, "chimney", sx_, sy_, z + top + 1.0)
    # (a wanted poster on its side wall; a lantern on a hook by the door)
    if k % 2 == 0:
        sd = 1 if k % 4 == 0 else -1
        a, b = P(sd * (w / 2 + 0.11), -0.35 * sd), P(sd * (w / 2 + 0.11), 0.35 * sd)
        two_sided(m, "edge_poster", [(a[0], a[1], z + 1.0), (b[0], b[1], z + 1.0), (b[0], b[1], z + 2.0), (a[0], a[1], z + 2.0)],
                  [(0, 0), (1, 0), (1, 1), (0, 1)])
    if k % 2 == 1 or kind == "stand":
        hx, hy, _ = P(-w / 2 + 0.2, -d / 2 - 0.6)
        bx, by, _ = P(-w / 2 + 0.2, -d / 2 - 0.05)
        m.add(("keep_iron", "wall"), lambda bm: props.tube(bm, [(bx, by, z + 2.1), (hx, hy, z + 2.1)], 0.025, n=3))
        c.place(hp.cage_lantern(c, k), hx, hy, z + 1.75, role="visual")
        R.D.light(c, "lantern", hx, hy, z + 1.6)
    if k % 4 == 2:
        fx_, fy_, _ = P(-w / 2 + 0.3, d / 2 - 0.3)
        flag_pole(m, fx_, fy_, z + top - 0.3, 3.2, k, face=_n(rot))
    # (barrels, crates, a heap of net about it)
    for q in range(1 + k % 3):
        lx = (w / 2 + 0.6) * (1 if q % 2 else -1)
        ly = -d / 2 + 0.4 + q * 0.9
        bx, by, _ = P(lx, ly)
        if q == 2:
            c.place(gp.crate_stack(c, k % 4), bx, by, z, rot=rot, role="visual")
        else:
            solid.add(("barrel_wood", "wall"), lambda bm, bx=bx, by=by: props.tube(bm, [(bx, by, z), (bx, by, z + 0.95)], [0.32, 0.36, 0.32], n=8))
    if k % 3 == 0:
        nx_, ny_, _ = P(w / 2 + 0.7, d / 2 - 0.2)
        m.add(("rope_rail", "wall"), lambda bm: props.blob(bm, (nx_, ny_, z + 0.15), 0.6, sz=0.35, subdiv=1))
    return P(-w / 4, -d / 2 - 1.1)[:2], kind


def _n(rot):
    """The way local -Y faces, for a rot."""
    return math.sin(rot), -math.cos(rot)


def shanty(c, ground, taken):
    """The shantytown: shacks crammed across the market's floor wherever the roads and
    lanes leave room (the alleys between them), the folk of it about their doors."""
    m, solid = Mesh(), Mesh()
    bx, by, brx, bry = BAZAAR
    k = 0
    step = 7.2
    y = by - bry
    row = 0
    while y < by + bry:
        x = bx - brx + (step / 2 if row % 2 else 0.0)
        while x < bx + brx:
            jx = x + (rnd(x * 1.7 + y) - 0.5) * 1.6
            jy = y + (rnd(y * 2.3 + x) - 0.5) * 1.6
            x += step
            if ellipse(jx, jy, *BAZAAR) > 0.84:
                continue
            if not paint.road_clear(c, jx, jy, 5.2) or not R.beast_clear(jx, jy, 3.4) or not taken.clear(jx, jy, 2.8):
                continue
            # (the shacks face the nearest road, their doors to the traffic)
            smp, _ = c.nearest(jx, jy)
            rot = facing(smp.p.x - jx, smp.p.y - jy) + (rnd(jx + jy) - 0.5) * 0.5
            gz = min(ground(jx, jy), *(ground(jx + ox, jy + oy) for ox, oy in ((2, 2), (-2, 2), (2, -2), (-2, -2))))
            if rnd(jx * 0.7 + jy * 1.3) < 0.18:
                # (a gap in the shacks: a cookfire, folk round it)
                R.D.light(c, "campfire", jx, jy, gz + 0.2)
                for i in range(4):
                    a = i * math.tau / 4 + k
                    R.D.person(c, jx + 1.9 * math.cos(a), jy + 1.9 * math.sin(a), gz, ("huddle", "queue", "huddle", "merchant")[i], jx, jy)
                taken.add(jx, jy, 2.6)
                k += 1
                continue
            door, kind = shack(c, m, solid, jx, jy, gz, rot, k)
            # (folk about the door)
            fx_, fy_ = door
            if kind == "stand":
                R.D.person(c, *local(jx, jy, rot, 0.0, 0.2), gz, "merchant", fx_, fy_)
                for q in range(2):
                    qx, qy = local(jx, jy, rot, -0.8 + q * 1.4, -3.3 - 0.3 * q)
                    R.D.person(c, qx, qy, gz, "queue", jx, jy)
            elif k % 3 == 0:
                for q in range(2):
                    qx, qy = local(jx, jy, rot, -0.6 + q * 1.2, -3.2)
                    ox, oy = local(jx, jy, rot, 0.6 - q * 1.2, -3.2)
                    R.D.person(c, qx, qy, gz, "huddle", ox, oy)
            elif k % 3 == 1:
                qx, qy = local(jx, jy, rot, 0.4, -2.6)
                R.D.person(c, qx, qy, gz, "hauler", *local(jx, jy, rot, 0.4, -6.0))
            taken.add(jx, jy, 3.2)
            k += 1
        y += step * 0.86
        row += 1
    m.build(c, "Shanty", coll="Props", role="visual")
    solid.build(c, "Shanty Shacks", coll="Props", role="both")
    print("shanty: %d shacks and gaps" % k)


def stage(c, ground, taken, x, y, face):
    """The bow of a wreck beached on the market floor, its deck the stage: three scruffy
    crocs playing on it (a squeezebox, a fiddle, a drum on a barrel), a broken mast with a
    flag, lanterns; the crowd about it on crates and barrels, eating, talking, a few
    nodding along. Background: no show, no dancing."""
    m, solid = Mesh(), Mesh()
    z = ground(x, y)
    fx, fy = face
    rot = math.atan2(fy, fx)  # (the bow's length along local X, pointing at the crowd)
    L_, Wd, H = 11.0, 5.2, 1.6
    deck = z + 1.15
    hx, hy = x - fx * 1.0, y - fy * 1.0
    m.add(("wreck_hull", "wall"), lambda bm: hull(bm, hx, hy, deck, rot, L_, Wd, H, upturned=False, bow=1.0, stern=0.2))
    solid.add(("wreck_hull", "wall"), lambda bm: cuboid(bm, (hx, hy, z + 0.55), (L_ * 0.8, Wd * 0.8, 1.1), rot - math.pi / 2 + math.pi / 2))
    rx, ry = -fy, fx

    def S(u, v, zz=0.0):
        return hx + fx * u + rx * v, hy + fy * u + ry * v, deck + zz

    # (its deck, its broken rail, the stump of its mast with a flag on it)
    pts = [S(-L_ / 2 + 0.2, -Wd / 2 + 0.3), S(L_ / 2 - 2.0, -Wd / 2 + 0.9), S(L_ / 2 - 0.6, 0), S(L_ / 2 - 2.0, Wd / 2 - 0.9), S(-L_ / 2 + 0.2, Wd / 2 - 0.3)]
    m.add(("plank_deck", "wall"), lambda bm: bm.faces.new([bm.verts.new(p) for p in pts]))
    m.add(("plank_deck", "wall"), lambda bm: bm.faces.new([bm.verts.new(p) for p in reversed(pts)]))
    for sd in (-1, 1):
        for q in range(4):
            if q == 2 and sd > 0:
                continue  # (broken)
            a, b = S(-L_ / 2 + 0.6 + q * 2.0, sd * (Wd / 2 - 0.35 - q * 0.08)), S(-L_ / 2 + 2.4 + q * 2.0, sd * (Wd / 2 - 0.4 - q * 0.12))
            m.add(R.W, lambda bm, a=a, b=b: props.tube(bm, [a, (a[0], a[1], a[2] + 0.9)], 0.05, n=4))
            m.add(R.W, lambda bm, a=a, b=b: props.tube(bm, [(a[0], a[1], a[2] + 0.85), (b[0], b[1], b[2] + 0.8 - 0.25 * (q == 1))], 0.04, n=4))
    mx, my, mz = S(-L_ / 2 + 1.2, 0)
    m.add(R.W, lambda bm: props.tube(bm, [(mx, my, mz), (mx + 0.2, my, mz + 5.5)], [0.22, 0.16], n=8))
    flag(m, (mx + 0.2 + rx * 0.9, my + ry * 0.9, mz + 5.3), (rx, ry), 1.6, 2.6, "edge_flag_skull", 41, strips=4)
    # (the stern's ragged cut: planks sprung, a crate stack and a ladder up)
    lx1, ly1, _ = S(-L_ / 2 - 0.3, -1.2)
    lx2, ly2, _ = S(-L_ / 2 - 0.3, -0.6)
    ladder(m, (lx1, ly1), (lx2, ly2), z, deck + 0.4)
    # The band: a squeezebox, a fiddle, a drum on a barrel (their instruments in their
    # hands, game/folkPoses.ts); lanterns on poles either side.
    for i, (pose, v) in enumerate((("squeeze", -1.3), ("fiddle", 0.0), ("drum", 1.3))):
        u = 0.6 - abs(v) * 0.4
        bx_, by_, bz = S(u, v)
        tx_, ty_, _ = S(u + 8.0, v * 1.5)
        R.D.folk(c, bx_, by_, bz, pose, tx_, ty_, seed=141 + i * 5, at=(tx_, ty_, bz))
        if pose == "drum":
            dx_, dy_, _ = S(u + 0.62, v)
            m.add(("barrel_wood", "wall"), lambda bm: props.tube(bm, [(dx_, dy_, bz), (dx_, dy_, bz + 0.78)], [0.3, 0.34, 0.3], n=10))
            m.add(("sail_cloth", "wall"), lambda bm: props.tube(bm, [(dx_, dy_, bz + 0.78), (dx_, dy_, bz + 0.8)], 0.31, n=10))
    for sd in (-1, 1):
        px_, py_, pz = S(1.6, sd * 2.0)
        m.add(R.W, lambda bm, px_=px_, py_=py_: props.tube(bm, [(px_, py_, pz), (px_, py_, pz + 2.6)], 0.06, n=4))
        c.place(hp.cage_lantern(c, 7 + sd), px_, py_, pz + 2.3, role="visual")
        R.D.light(c, "lantern", px_, py_, pz + 2.2)
    R.D.light(c, "glow", *S(0.5, 0)[:2], deck + 2.5)
    # The crowd: on crates and barrels in an arc before the bow, eating, talking, a few
    # nodding along; a cookfire with its pot to one side.
    poses = ("kneel", "eat", "chat", "tap", "kneel", "chat", "chat", "tap", "kneel", "eat", "chat", "kneel")
    base = math.atan2(fy, fx)
    n = len(poses)
    spots = []
    for i in range(n):
        a = base + (i - (n - 1) / 2) * 0.17
        r_ = L_ / 2 + 3.4 + 1.7 * (i % 2)
        spots.append((hx + math.cos(a) * r_, hy + math.sin(a) * r_))
    bx_, by_, _ = S(0.4, 0)
    for i, pose in enumerate(poses):
        px_, py_ = spots[i]
        gz = ground(px_, py_)
        seat = 0.0
        if pose == "kneel":
            seat = 0.45
            a = facing(bx_ - px_, by_ - py_)
            solid.add((("barrel_wood", "wreck_planks")[i % 2], "wall"),
                      lambda bm, px_=px_, py_=py_, gz=gz, a=a: cuboid(bm, (px_, py_, gz + 0.22), (0.6, 0.6, 0.45), a))
        if pose == "chat":
            # (talking to the one beside them)
            j = i + 1 if i % 2 == 0 and i + 1 < n else i - 1
            qx, qy = spots[j]
            R.D.folk(c, px_, py_, gz, pose, qx, qy, seed=160 + i, at=(qx, qy, gz + 1.2))
        else:
            R.D.folk(c, px_, py_, gz + seat, pose, bx_, by_, seed=160 + i, at=(bx_, by_, deck + 1.0))
    ox, oy = hx + fx * (L_ / 2 + 4.0), hy + fy * (L_ / 2 + 4.0)
    cx_, cy_ = ox + rx * 7.5, oy + ry * 7.5
    R.D.light(c, "campfire", cx_, cy_, ground(cx_, cy_) + 0.2)
    for i in range(3):
        a = i * math.tau / 3 + 0.4
        R.D.person(c, cx_ + 1.8 * math.cos(a), cy_ + 1.8 * math.sin(a), ground(cx_, cy_), ("huddle", "merchant", "huddle")[i], cx_, cy_)
    m.build(c, "Band Stage", coll="Props", role="visual")
    solid.build(c, "Band Stage Hull", coll="Props", role="both")
    taken.add(x, y, 9.0)
    taken.add(ox, oy, 7.0)
