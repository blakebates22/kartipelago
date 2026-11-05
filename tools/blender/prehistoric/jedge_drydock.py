# The Fighting Pits reimagined as the smugglers' dry dock (Blake, Nov 5: "we need to do a
# massive overhaul of where the boxing match is. i think its kind of weird, and it currenlty
# looks really bad with the stands to the boxing ring"; he picked the smugglers' dry dock,
# scaffold grandstands, the road kept where it is).
# SPDX-License-Identifier: MIT
#
#   the galleon      a great smuggler galleon building on the dock's floor, up on its keel
#                    blocks and shored: its bow half planked (gun ports, its deck, a mast up
#                    with its yard and sail furled, the bowsprit, a flag), its stern half
#                    still bare ribs with the first strakes going on; scaffolding up both
#                    sides, crocs hammering on every level;
#   the cranes       two timber derricks over it, guyed, a load hanging off each (a net of
#                    crates, a cannon), their winch crews;
#   the lock gate    the great timber gate in the dock's end wall, iron-banded, leaking:
#                    spray from its seams, water running down it and across the floor;
#   the yard         timber stacked, the steam box bending planks, the forge, the tar
#                    pots, a sail spread out being stitched, the saw horse, the croc
#                    figurehead being carved, puddles, barrels and rope;
#   the stands       rickety grandstands of planks on posts down both sides of the spiral,
#                    shaded with sails, lanterns and flags on them, packed for launch night.
#
# jedge_districts.pits() calls dock() and stands().

import math

from gulch_scenery import Mesh
import props
from props import cuboid
import gulch_props as gp
import harbour_props as hp
import swamp_props as sw
import region_paint as paint
import jedge_districts as D
import jedge_rookery as R
import jedge_shanty as S
import jedge_layout as L
from jedge_layout import PIT, PIT_FLOOR, PIT_R, pit_ground, spiral_at

W_ = ("weathered_timber", "wall")
# The galleon: its middle, which way its bow points, its size.
SHIP = (42.0, -10.0, math.pi)
SHIP_L, SHIP_W, SHIP_H = 40.0, 11.0, 7.5
BLOCKS = 1.2
BARE = -0.2  # (aft of this, t -1..BARE, still bare ribs)


def ship_at(u, v, z=0.0):
    """A point u along the galleon (toward its bow) and v across it (to port), world."""
    sx, sy, rot = SHIP
    ca, sa = math.cos(rot), math.sin(rot)
    return sx + u * ca - v * sa, sy + u * sa + v * ca, z


def deck_z():
    return PIT_FLOOR + BLOCKS + SHIP_H


def on_ship(x, y, margin=0.0):
    """Over the galleon's footprint, its scaffolding and its shores?"""
    sx, sy, rot = SHIP
    dx, dy = x - sx, y - sy
    u = dx * math.cos(rot) + dy * math.sin(rot)
    v = -dx * math.sin(rot) + dy * math.cos(rot)
    return abs(u) < SHIP_L / 2 + 10.0 + margin and abs(v) < SHIP_W / 2 + 5.0 + margin


def galleon(c, m, solid, hidden):
    L_, W, H = SHIP_L, SHIP_W, SHIP_H
    dz = deck_z()
    sx, sy, rot = SHIP

    def sec(t):
        return S.hull_section(t, L_, W, H, bow=1.0, stern=0.55)

    def surf(t, a):
        half, hh = sec(t)
        return ship_at(t * L_ / 2, math.cos(a) * half, dz - math.sin(a) * hh)

    # (the planked bow half, its sides)
    m.add(("wreck_hull", "wall"), lambda bm: S.hull(bm, sx, sy, dz, rot, L_, W, H, upturned=False, bow=1.0, stern=0.55, n=14, m=9,
                                                     t0=BARE, t1=1.0, caps=False))
    # (the bare stern half: ribs, the first strakes along its bottom, the deck beams)
    t = -0.98
    while t < BARE:
        pts = [surf(t, math.pi * j / 10) for j in range(11)]
        m.add(W_, lambda bm, pts=pts: props.tube(bm, pts, 0.17, n=5))
        a, b = surf(t, 0.0), surf(t, math.pi)
        m.add(W_, lambda bm, a=a, b=b: props.tube(bm, [a, b], 0.13, n=4))
        t += 0.075
    for a in (math.pi / 2 - 0.3, math.pi / 2 + 0.3, math.pi / 2 - 0.62, math.pi / 2 + 0.62, math.pi / 2 - 0.95):
        reach = -0.95 if abs(a - math.pi / 2) < 0.4 else -0.6
        pts = [surf(t_, a) for t_ in [reach + (BARE + 0.02 - reach) * i / 8 for i in range(9)]]
        m.add(("wreck_planks", "wall"), lambda bm, pts=pts: props.tube(bm, pts, 0.2, n=4))
    # (the sheer clamps along both sides, the whole length, and the keel)
    for a in (0.0, math.pi):
        pts = [surf(t_, a) for t_ in [-1.0 + 1.96 * i / 20 for i in range(21)]]
        m.add(("door_wood", "wall"), lambda bm, pts=pts: props.tube(bm, pts, 0.16, n=4))
    kx, ky, _ = ship_at(0.0, 0.0)
    solid.add(("door_wood", "wall"), lambda bm: cuboid(bm, (kx, ky, dz - H + 0.25), (L_ * 0.94, 0.7, 0.7), rot))
    # (the stern post and the stem)
    a, b = ship_at(-L_ / 2 + 0.3, 0.0, dz - H + 0.4), ship_at(-L_ / 2 - 0.4, 0.0, dz + 3.2)
    m.add(("door_wood", "wall"), lambda bm: props.tube(bm, [a, b], 0.3, n=6))
    # (the deck over the planked half)
    for i in range(12):
        t0_ = BARE + (1.0 - BARE) * i / 12
        t1_ = BARE + (1.0 - BARE) * (i + 1) / 12
        h0, h1 = sec(t0_)[0] * 0.98, sec(t1_)[0] * 0.98
        pts = [ship_at(t0_ * L_ / 2, -h0, dz), ship_at(t1_ * L_ / 2, -h1, dz), ship_at(t1_ * L_ / 2, h1, dz), ship_at(t0_ * L_ / 2, h0, dz)]
        m.add(("plank_deck", "wall"), lambda bm, pts=pts: bm.faces.new([bm.verts.new(p) for p in pts]))
        m.add(("plank_deck", "wall"), lambda bm, pts=pts: bm.faces.new([bm.verts.new(p) for p in reversed(pts)]))
    # (gun ports down both sides)
    t = 0.02
    while t < 0.72:
        half, _ = sec(t)
        for sd in (-1, 1):
            gx, gy, gz = ship_at(t * L_ / 2, sd * (half * 0.985 + 0.05), dz - 1.4)
            m.add(("keep_iron", "wall"), lambda bm, gx=gx, gy=gy, gz=gz: cuboid(bm, (gx, gy, gz), (0.75, 0.12, 0.7), rot))
        t += 0.13
    # (the mast, its yard with the sail furled on it, the top, the flag; the bowsprit;
    # the rigging)
    mx, my, _ = ship_at(0.3 * L_ / 2, 0.0)
    top = dz + 23.0
    m.add(("door_wood", "wall"), lambda bm: props.tube(bm, [(mx, my, dz - 2.0), (mx, my, top)], [0.45, 0.32, 0.22], n=8))
    ya, yb = ship_at(0.3 * L_ / 2, -7.5, dz + 16.0), ship_at(0.3 * L_ / 2, 7.5, dz + 16.0)
    m.add(("door_wood", "wall"), lambda bm: props.tube(bm, [ya, yb], 0.18, n=5))
    m.add(("sail_cloth", "wall"), lambda bm: props.tube(bm, [ship_at(0.3 * L_ / 2, -6.8, dz + 15.6), ship_at(0.3 * L_ / 2, 6.8, dz + 15.6)],
                                                       [0.2, 0.42, 0.42, 0.2], n=6))
    m.add(("barrel_wood", "wall"), lambda bm: props.tube(bm, [(mx, my, dz + 18.5), (mx, my, dz + 19.4)], [0.9, 1.0], n=10))
    S.flag(m, (mx, my + 0.9, top - 0.2), (0.0, 1.0), 1.8, 2.8, "edge_flag_skull", 51, strips=4)
    bs0, bs1 = ship_at(L_ / 2 - 0.5, 0.0, dz + 0.6), ship_at(L_ / 2 + 9.0, 0.0, dz + 4.5)
    m.add(("door_wood", "wall"), lambda bm: props.tube(bm, [bs0, bs1], [0.3, 0.14], n=6))
    for end in (bs1, ship_at(-L_ / 2 + 0.6, 0.0, dz + 3.0)):
        m.add(("rope_rail", "wall"), lambda bm, end=end: props.tube(bm, [(mx, my, top - 1.0), end], 0.04, n=3))
    for sd in (-1, 1):
        for du in (-2.2, 0.0, 2.2):
            base = ship_at(0.3 * L_ / 2 + du, sd * sec(0.3)[0], dz + 0.2)
            m.add(("rope_rail", "wall"), lambda bm, base=base: props.tube(bm, [(mx, my, dz + 18.4), base], 0.03, n=3))
    # (a lantern at the bow and stern, hung for the night shift)
    for u in (L_ / 2 - 2.0, -L_ / 2 + 2.0):
        lx, ly, lz = ship_at(u, 0.0, dz + 2.6)
        c.place(hp.cage_lantern(c, int(u)), lx, ly, lz, role="visual")
        D.light(c, "lantern", lx, ly, lz)
    # Keel blocks under it, the shores propping its sides.
    u = -L_ / 2 + 2.0
    k = 0
    while u < L_ / 2 - 5.0:
        bx, by, _ = ship_at(u, 0.0)
        solid.add((("barrel_wood", "weathered_timber")[k % 2], "wall"),
                  lambda bm, bx=bx, by=by: cuboid(bm, (bx, by, PIT_FLOOR + BLOCKS / 2), (1.4, 2.4, BLOCKS), rot))
        if k % 2 == 0:
            t_ = u / (L_ / 2)
            half, hh = sec(t_)
            for sd in (-1, 1):
                a = ship_at(u, sd * (half + 3.6), PIT_FLOOR)
                b = ship_at(u, sd * half * 0.92, dz - hh * 0.45)
                m.add(W_, lambda bm, a=a, b=b: props.tube(bm, [a, b], 0.16, n=5))
        u += 3.0
        k += 1
    # (the whole of it solid to a kart that strays off the road into it)
    hx, hy, _ = ship_at(0.0, 0.0)
    hidden.add(("cave_rock", "wall"), lambda bm: cuboid(bm, (hx, hy, PIT_FLOOR + 4.0), (L_ + 1.0, W + 2.0, 8.0), rot))


def scaffold(c, m, solid):
    """Scaffolding up both sides of the galleon and round its stern: posts, braces, plank
    walks on three levels, ladders; the crocs at work on it."""
    L_, W, H = SHIP_L, SHIP_W, SHIP_H
    dz = deck_z()
    levels = [PIT_FLOOR + 2.7, PIT_FLOOR + 5.4, dz - 0.2]
    n_folk = 0
    for sd in (-1, 1):
        v = sd * (W / 2 + 1.7)
        u = -L_ / 2 - 1.0
        k = 0
        while u < L_ * 0.34:
            a = ship_at(u, v)
            b = ship_at(u + 3.0, v)
            for p in (a, b):
                m.add(W_, lambda bm, p=p: props.tube(bm, [(p[0], p[1], PIT_FLOOR), (p[0], p[1], dz + 2.0)], 0.1, n=4))
                o = ship_at(u if p is a else u + 3.0, v + sd * 1.2)
                m.add(W_, lambda bm, o=o: props.tube(bm, [(o[0], o[1], PIT_FLOOR), (o[0], o[1], dz + 2.0)], 0.1, n=4))
            for z in levels:
                cx = (a[0] + b[0]) / 2
                cy = (a[1] + b[1]) / 2
                mx, my, _ = ship_at(u + 1.5, v + sd * 0.6)
                m.add(("plank_deck", "wall"), lambda bm, mx=mx, my=my, z=z: cuboid(bm, (mx, my, z), (3.0, 1.3, 0.08), SHIP[2]))
                if z != levels[0]:
                    ra, rb = ship_at(u, v + sd * 1.25, z + 1.0), ship_at(u + 3.0, v + sd * 1.25, z + 1.0)
                    m.add(W_, lambda bm, ra=ra, rb=rb: props.tube(bm, [ra, rb], 0.04, n=3))
            # (a brace across every other bay)
            if k % 2 == 0:
                m.add(W_, lambda bm, a=a, b=b: props.tube(bm, [(a[0], a[1], PIT_FLOOR + 0.3), (b[0], b[1], levels[1])], 0.06, n=3))
            # (crocs at work along it: hammering at the hull, carrying, a lookout down)
            if k % 2 == (0 if sd > 0 else 1):
                lv = levels[(k // 2) % 3]
                fx, fy, _ = ship_at(u + 1.5, v + sd * 0.4)
                tx, ty, _ = ship_at(u + 1.5, 0.0)
                pose = ("beat", "work", "beat", "point", "hang")[(k + (sd > 0)) % 5]
                D.folk(c, fx, fy, lv + 0.04, pose, tx, ty, seed=200 + n_folk * 3, at=(tx, ty, lv + 1.0))
                n_folk += 1
            # (ladders at the ends)
            if k == 0:
                la, lb = ship_at(u - 0.3, v + sd * 0.3), ship_at(u - 0.3, v + sd * 0.9)
                S.ladder(m, la, lb, PIT_FLOOR, dz)
            if k % 3 == 1:
                lx, ly, _ = ship_at(u + 1.5, v + sd * 1.3)
                c.place(hp.cage_lantern(c, k + sd), lx, ly, levels[1] + 1.8, role="visual")
                D.light(c, "lantern", lx, ly, levels[1] + 1.6)
            u += 3.0
            k += 1
    # (round the bare stern: a frame of posts and two walks)
    for i in range(5):
        v = -W / 2 + i * W / 4
        p = ship_at(-L_ / 2 - 2.5, v)
        m.add(W_, lambda bm, p=p: props.tube(bm, [(p[0], p[1], PIT_FLOOR), (p[0], p[1], dz + 2.0)], 0.1, n=4))
    for z in levels[1:]:
        cx, cy, _ = ship_at(-L_ / 2 - 2.0, 0.0)
        m.add(("plank_deck", "wall"), lambda bm, cx=cx, cy=cy, z=z: cuboid(bm, (cx, cy, z), (1.2, W + 0.6, 0.08), SHIP[2]))
    for i, pose in enumerate(("beat", "work", "beat")):
        fx, fy, _ = ship_at(-L_ / 2 - 1.9, -3.0 + i * 3.0)
        tx, ty, _ = ship_at(-L_ / 2 + 2.0, -3.0 + i * 3.0)
        D.folk(c, fx, fy, levels[1 + i % 2] + 0.04, pose, tx, ty, seed=260 + i, at=(tx, ty, levels[1 + i % 2] + 1.0))
    return n_folk + 3


def crane(c, m, solid, x, y, reach_to, load, k):
    """A timber derrick: its mast guyed to the floor, its boom out over the galleon, a
    rope down from its tip to the load hanging there; the winch at its foot and its crew."""
    z0 = PIT_FLOOR
    h = 24.0
    m.add(("door_wood", "wall"), lambda bm: props.tube(bm, [(x, y, z0), (x, y, z0 + h)], [0.45, 0.3], n=8))
    solid.add(("weathered_timber", "wall"), lambda bm: cuboid(bm, (x, y, z0 + 0.4), (2.2, 2.2, 0.8)))
    for a in (0.4, 2.0, 3.6, 5.2):
        gx, gy = x + 11.0 * math.cos(a + k), y + 11.0 * math.sin(a + k)
        m.add(("rope_rail", "wall"), lambda bm, gx=gx, gy=gy: props.tube(bm, [(x, y, z0 + h - 0.5), (gx, gy, z0 + 0.2)], 0.04, n=3))
        solid.add(("keep_iron", "wall"), lambda bm, gx=gx, gy=gy: cuboid(bm, (gx, gy, z0 + 0.25), (0.6, 0.6, 0.5)))
    tx, ty = reach_to
    tip = (tx, ty, z0 + 20.0)
    m.add(("door_wood", "wall"), lambda bm: props.tube(bm, [(x, y, z0 + 3.0), tip], [0.3, 0.18], n=6))
    m.add(("rope_rail", "wall"), lambda bm: props.tube(bm, [(x, y, z0 + h - 0.3), tip], 0.05, n=3))
    lz = deck_z() + 4.0
    m.add(("rope_rail", "wall"), lambda bm: props.tube(bm, [tip, (tx, ty, lz + 1.6)], 0.05, n=3))
    if load == "crates":
        for i, (ox, oy) in enumerate(((0, 0), (0.9, 0.2), (-0.4, 0.9))):
            m.add(("barrel_wood", "wall"), lambda bm, ox=ox, oy=oy, i=i: cuboid(bm, (tx + ox * 0.6, ty + oy * 0.6, lz + 0.45 + (0.9 if i == 2 else 0)), (0.9, 0.9, 0.9), 0.3 * i))
        for a in range(4):
            ex, ey = tx + 0.9 * math.cos(a * math.pi / 2 + 0.6), ty + 0.9 * math.sin(a * math.pi / 2 + 0.6)
            m.add(("rope_rail", "wall"), lambda bm, ex=ex, ey=ey: props.tube(bm, [(tx, ty, lz + 1.6), (ex, ey, lz)], 0.03, n=3))
    else:
        # (a cannon slung by its trunnions)
        a, b = (tx - 1.3, ty, lz + 0.6), (tx + 1.3, ty, lz + 0.8)
        m.add(("keep_iron", "wall"), lambda bm: props.tube(bm, [a, b], [0.34, 0.26], n=10))
        for sd in (-1, 1):
            m.add(("rope_rail", "wall"), lambda bm, sd=sd: props.tube(bm, [(tx, ty, lz + 1.6), (tx + sd * 0.8, ty, lz + 0.7)], 0.03, n=3))
    # (the winch at its foot, cranked by two)
    wx, wy = x + 2.2, y
    m.add(("door_wood", "wall"), lambda bm: props.tube(bm, [(wx, wy - 0.8, z0 + 0.9), (wx, wy + 0.8, z0 + 0.9)], 0.45, n=10))
    for sd in (-1, 1):
        solid.add(("weathered_timber", "wall"), lambda bm, sd=sd: cuboid(bm, (wx, wy + sd * 0.9, z0 + 0.55), (0.3, 0.15, 1.1)))
        D.folk(c, wx + 0.9, wy + sd * 1.3, z0, "work", wx, wy, seed=300 + k * 2 + (sd > 0), at=(wx, wy, z0 + 0.9))
    D.light(c, "lantern", x, y, z0 + 4.0)


def lock_gate(c, m, solid):
    """The great lock gate in the dock's end wall, holding the sea back: timber, iron
    bands, a walk along its top with its winding wheels; leaking: spray from its seams,
    water running down its face and away across the floor."""
    px, py = PIT
    x = px - PIT_R[0] - 0.6
    y = py
    z0 = PIT_FLOOR
    w, h = 20.0, 13.0
    solid.add(("wreck_hull", "wall"), lambda bm: cuboid(bm, (x - 0.6, y, z0 + h / 2), (1.2, w, h)))
    for i in range(1, 8):
        zz = z0 + i * h / 8
        m.add(("keep_iron", "wall"), lambda bm, zz=zz: cuboid(bm, (x + 0.05, y, zz), (0.12, w + 0.1, 0.22)))
    for i in range(5):
        yy = y - w / 2 + i * w / 4
        m.add(("door_wood", "wall"), lambda bm, yy=yy: cuboid(bm, (x + 0.15, yy, z0 + h / 2), (0.4, 0.6, h + 0.4)))
    # (the seam down its middle, where the two leaves meet)
    m.add(("keep_iron", "wall"), lambda bm: cuboid(bm, (x + 0.2, y, z0 + h / 2), (0.25, 0.2, h)))
    # (the walk along its top, its rail, the winding wheels)
    m.add(("plank_deck", "wall"), lambda bm: cuboid(bm, (x - 0.2, y, z0 + h + 0.1), (2.6, w + 2.0, 0.2)))
    for sd in (-1, 1):
        wx, wy = x - 0.2, y + sd * w / 3
        m.add(("door_wood", "wall"), lambda bm, wy=wy: props.tube(bm, [(wx - 0.3, wy, z0 + h + 1.4), (wx + 0.3, wy, z0 + h + 1.4)], 1.1, n=12))
        D.folk(c, wx + 0.9, wy + sd * 1.4, z0 + h + 0.2, "work", wx, wy, seed=320 + (sd > 0), at=(wx, wy, z0 + h + 1.4))
    ra, rb = (x + 0.9, y - w / 2 - 1.0, z0 + h + 1.1), (x + 0.9, y + w / 2 + 1.0, z0 + h + 1.1)
    m.add(W_, lambda bm: props.tube(bm, [ra, rb], 0.05, n=3))
    # (leaking: spray from the seams, sheets of water down its face, a stream across the
    # floor to the drain)
    for i, (dy, zz) in enumerate(((0.0, 2.0), (0.0, 7.5), (-5.5, 3.5), (6.0, 5.0), (2.5, 10.5))):
        g = c.game(x + 0.6, y + dy, z0 + zz)
        c.entity("mist", x=round(g[0], 1), y=round(g[1], 1), z=round(g[2], 1), radius=1.4, rate=4.0, color="#d8ecf4")
        top, bot = z0 + zz, z0 + 0.05
        sheet = [(x + 0.3, y + dy - 0.7, top), (x + 0.3, y + dy + 0.7, top), (x + 0.5, y + dy + 1.5, bot), (x + 0.5, y + dy - 1.5, bot)]
        S.two_sided(m, "waterfall", sheet, [(0, 1), (1, 1), (1, 0), (0, 0)])
    pts = [(x + 0.5, y, z0 + 0.04), (x + 6.0, y + 3.0, z0 + 0.04), (x + 11.0, y + 13.0, z0 + 0.04), (x + 14.0, y + 19.0, z0 + 0.04)]
    for a, b in zip(pts, pts[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy)
        nx, ny = -dy / n * 0.9, dx / n * 0.9
        q = [(a[0] - nx, a[1] - ny, a[2]), (b[0] - nx, b[1] - ny, b[2]), (b[0] + nx, b[1] + ny, b[2]), (a[0] + nx, a[1] + ny, a[2])]
        m.add(("canal_water", "wall"), lambda bm, q=q: bm.faces.new([bm.verts.new(p) for p in q]))
    gx, gy, _ = pts[-1]
    m.add(("keep_iron", "wall"), lambda bm: cuboid(bm, (gx, gy, z0 + 0.06), (1.8, 1.8, 0.1)))
    D.light(c, "glow", x + 2.0, y, z0 + 6.0)


def yard(c, m, solid, taken):
    """The dock's floor round the galleon: its trades."""
    z = PIT_FLOOR
    px, py = PIT

    def clear(x, y, r):
        return math.hypot(x - px, y - py) < PIT_R[0] - 3.0 and paint.road_clear(c, x, y, r + 2.0) and not on_ship(x, y, r)

    # (timber stacked, long beams in piles)
    for i, (x, y, a) in enumerate(((30.0, 10.0, 0.1), (52.0, 12.0, -0.2), (64.0, -2.0, 1.4))):
        if not clear(x, y, 4.5):
            continue
        for row in range(3):
            for q in range(4 - row):
                off = (q - (3 - row) / 2) * 0.5
                bx, by = x - math.sin(a) * off, y + math.cos(a) * off
                solid.add(("weathered_timber", "wall"), lambda bm, bx=bx, by=by, row=row: cuboid(bm, (bx, by, z + 0.25 + row * 0.45), (8.0, 0.45, 0.45), a))
        D.person(c, x + 2.0, y + 2.0, z, "hauler", x, y)
        taken.add(x, y, 5.0)
    # (the steam box, bending planks: a long box on trestles over a fire, steaming)
    x, y = 21.0, 12.0
    if clear(x, y, 4.0):
        solid.add(("barrel_wood", "wall"), lambda bm: cuboid(bm, (x, y, z + 1.4), (7.0, 1.0, 1.0), 0.3))
        for i in range(3):
            g = c.game(x + (i - 1) * 2.2 * math.cos(0.3), y + (i - 1) * 2.2 * math.sin(0.3), z + 2.0)
            c.entity("steam", x=round(g[0], 2), y=round(g[1], 2), z=round(g[2], 2))
        D.light(c, "campfire", x, y, z + 0.2)
        D.folk(c, x + 1.0, y - 1.6, z, "work", x, y, seed=340, at=(x, y, z + 1.4))
        taken.add(x, y, 4.5)
    # (the forge: its hearth glowing, the anvil, the smith hammering)
    x, y = 55.0, -27.0
    if clear(x, y, 3.0):
        solid.add(("sandstone_block", "wall"), lambda bm: cuboid(bm, (x, y, z + 0.5), (2.0, 1.6, 1.0)))
        m.add(("fire_glow", "wall"), lambda bm: cuboid(bm, (x, y, z + 1.02), (1.4, 1.0, 0.06)))
        m.add(("keep_iron", "wall"), lambda bm: props.tube(bm, [(x, y + 0.2, z + 1.0), (x, y + 0.2, z + 5.0)], 0.25, n=6))
        D.light(c, "campfire", x, y, z + 1.0)
        D.light(c, "chimney", x, y + 0.2, z + 5.2)
        D.light(c, "glow", x, y, z + 2.0)
        ax, ay = x + 2.0, y + 0.4
        solid.add(("keep_iron", "wall"), lambda bm: cuboid(bm, (ax, ay, z + 0.45), (0.8, 0.4, 0.9)))
        D.folk(c, ax + 0.8, ay, z, "beat", ax, ay, seed=342, at=(ax, ay, z + 0.9))
        taken.add(x, y, 4.0)
    # (the tar pots, bubbling, stirred)
    for i, (x, y) in enumerate(((28.0, -27.0), (32.0, -29.5))):
        if clear(x, y, 1.5):
            m.add(("keep_iron", "wall"), lambda bm, x=x, y=y: props.tube(bm, [(x, y, z), (x, y, z + 0.9)], [0.6, 0.7], n=10))
            m.add(("keep_iron", "wall"), lambda bm, x=x, y=y: props.tube(bm, [(x, y, z + 0.86), (x, y, z + 0.88)], 0.62, n=10))
            g = c.game(x, y, z + 1.1)
            c.entity("steam", x=round(g[0], 2), y=round(g[1], 2), z=round(g[2], 2))
            D.light(c, "chimney", x, y, z + 1.4)
            D.folk(c, x + 1.1, y + 0.3, z, "cook", x, y, seed=344 + i, at=(x, y, z + 0.9))
            taken.add(x, y, 2.0)
    # (a new sail spread on the floor, being stitched)
    x, y = 50.0, 17.0
    if clear(x, y, 4.0):
        pts = [(x - 4.0, y - 2.8, z + 0.05), (x + 4.0, y - 2.6, z + 0.05), (x + 3.4, y + 2.8, z + 0.05), (x - 3.8, y + 2.6, z + 0.05)]
        m.add(("sail_cloth", "wall"), lambda bm: bm.faces.new([bm.verts.new(p) for p in pts]))
        for i, (ox, oy) in enumerate(((-2.0, -3.4), (1.5, -3.3), (4.6, 0.5))):
            D.folk(c, x + ox, y + oy, z, "kneel", x, y, seed=350 + i, at=(x + ox * 0.6, y + oy * 0.6, z))
        taken.add(x, y, 5.0)
    # (the saw horse, a log on it, two at the saw)
    x, y = 60.0, 10.0
    if clear(x, y, 3.0):
        m.add(("weathered_timber", "wall"), lambda bm: props.tube(bm, [(x - 2.5, y, z + 1.0), (x + 2.5, y, z + 1.0)], 0.35, n=8))
        for sd in (-1, 1):
            solid.add(("weathered_timber", "wall"), lambda bm, sd=sd: cuboid(bm, (x + sd * 1.6, y, z + 0.4), (0.2, 1.2, 0.8)))
            D.folk(c, x + sd * 0.6, y + sd * 1.1, z, "work", x, y, seed=356 + (sd > 0), at=(x, y, z + 1.0))
        taken.add(x, y, 3.5)
    # (the figurehead: a great croc's head, carved, on its trestles; its carvers)
    x, y = 19.0, -26.0
    if clear(x, y, 3.0):
        for sd in (-1, 1):
            solid.add(("weathered_timber", "wall"), lambda bm, sd=sd: cuboid(bm, (x + sd * 1.2, y, z + 0.5), (0.3, 1.6, 1.0)))
        # (carved in dark wood: the head, the long snout, its teeth, the eyes)
        a = 0.6
        ca, sa = math.cos(a), math.sin(a)
        hz = z + 1.9
        m.add(("door_wood", "wall"), lambda bm: props.blob(bm, (x, y, hz), 1.0, sx=1.05, sy=0.95, sz=0.8, subdiv=2))
        nx_, ny_ = x + ca * 1.6, y + sa * 1.6
        m.add(("door_wood", "wall"), lambda bm: cuboid(bm, (nx_, ny_, hz - 0.25), (2.4, 0.95, 0.55), a + math.pi / 2, tilt=(0.0, 0.08)))
        for sd in (-1, 1):
            ex, ey = x + ca * 0.3 - sa * sd * 0.55, y + sa * 0.3 + ca * sd * 0.55
            m.add(("barrel_wood", "wall"), lambda bm, ex=ex, ey=ey: props.blob(bm, (ex, ey, hz + 0.75), 0.3, subdiv=1))
            for q in range(5):
                tx_, ty_ = x + ca * (0.9 + q * 0.45) - sa * sd * 0.42, y + sa * (0.9 + q * 0.45) + ca * sd * 0.42
                m.add(("party_white", "wall"), lambda bm, tx_=tx_, ty_=ty_: R.bmesh_cone(bm, tx_, ty_, hz - 0.62, 0.07, -0.18))
        for q in range(14):
            cx_, cy_ = x + 1.8 * math.cos(q * 2.1), y + 1.8 * math.sin(q * 1.3)
            m.add(("barrel_wood", "wall"), lambda bm, cx_=cx_, cy_=cy_: cuboid(bm, (cx_, cy_, z + 0.03), (0.2, 0.08, 0.04), q * 0.7))
        for i, (ox, pose) in enumerate(((-2.2, "beat"), (2.4, "work"))):
            D.folk(c, x + ox, y - 1.4, z, pose, x, y, seed=360 + i, at=(x, y, z + 1.4))
        taken.add(x, y, 3.5)
    # (puddles, barrels, rope coiled)
    for i in range(10):
        a = i * 2.399
        r = 8.0 + 20.0 * ((i * 0.618) % 1.0)
        x, y = px + r * math.cos(a), py + r * math.sin(a)
        if not clear(x, y, 1.5):
            continue
        rr = 1.0 + 1.4 * ((i * 0.37) % 1.0)
        pts = [(x + rr * math.cos(b) * (1 + 0.3 * math.sin(b * 3 + i)), y + rr * 0.7 * math.sin(b), z + 0.03) for b in [q * math.tau / 10 for q in range(10)]]
        m.add(("canal_water", "wall"), lambda bm, pts=pts: bm.faces.new([bm.verts.new(p) for p in pts]))
        if i % 2:
            bx, by = x + rr + 1.2, y
            solid.add(("barrel_wood", "wall"), lambda bm, bx=bx, by=by: props.tube(bm, [(bx, by, z), (bx, by, z + 0.95)], [0.32, 0.36, 0.32], n=8))
        else:
            m.add(("rope_rail", "wall"), lambda bm, x=x, y=y, rr=rr: props.blob(bm, (x + rr + 1.0, y + 0.6, z + 0.15), 0.55, sz=0.35, subdiv=1))


def dock(c, ground, taken):
    """The dry dock: the galleon, its scaffolding, the cranes, the lock gate, the yard."""
    m, solid, hidden = Mesh(), Mesh(), Mesh()
    galleon(c, m, solid, hidden)
    n = scaffold(c, m, solid)
    for k, (side, load) in enumerate(((1, "crates"), (-1, "cannon"))):
        x, y, _ = ship_at(-2.0 + 8.0 * k, side * (SHIP_W / 2 + 9.5))
        tx, ty, _ = ship_at(-6.0 + 12.0 * k, side * 1.0)
        crane(c, m, solid, x, y, (tx, ty), load, k)
    lock_gate(c, m, solid)
    yard(c, m, solid, taken)
    # (work lights strung over the galleon)
    for i in range(4):
        a = ship_at(-SHIP_L / 2 + 4.0 + i * 9.0, -SHIP_W / 2 - 2.9, deck_z() + 2.0)
        b = ship_at(-SHIP_L / 2 + 4.0 + i * 9.0, SHIP_W / 2 + 2.9, deck_z() + 2.0)
        S.net_line(c, m, a, b, 0.8, 70 + i)
        D.light(c, "glow", (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, deck_z() + 3.0)
    sx, sy, _ = SHIP
    taken.add(sx, sy, SHIP_L / 2 + 4.0)
    m.build(c, "Dry Dock", coll="Props", role="visual")
    solid.build(c, "Dry Dock Solids", coll="Props", role="both")
    hidden.build(c, "Dry Dock Galleon Hull", coll="Collision", role="collision")
    print("dry dock: %d at work on the scaffolding" % n)


def stands(c, taken):
    """Rickety grandstands of planks on posts down both sides of the spiral (in place of
    the stone benches: "it currenlty looks really bad with the stands"), each row a run of
    seat and footboard, posts down to the slope; sails over some, lanterns and flags on
    them; packed for launch night, all watching the galleon."""
    px, py = PIT
    f0, f1, f2 = PIT_R
    m, solid = Mesh(), Mesh()
    sx, sy, _ = SHIP
    n = 0
    K = 78
    for k in range(K):
        a0 = -60.0 - 300.0 * k / K
        a1 = -60.0 - 300.0 * (k + 1) / K
        r_road, z_road = spiral_at((a0 + a1) / 2)
        rows = []
        r = r_road + 10.5
        while r < min(f2 - 2.0, f1 + 6.0):
            rows.append(r)
            r += 3.0
        r = r_road - 10.5
        while r > f0 + 2.0:
            rows.append(r)
            r -= 3.0
        for ri, r in enumerate(rows):
            ra0, ra1 = math.radians(a0), math.radians(a1)
            p0 = (px + r * math.cos(ra0), py + r * math.sin(ra0))
            p1 = (px + r * math.cos(ra1), py + r * math.sin(ra1))
            mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
            if not all(paint.road_clear(c, *p, 2.0) for p in (p0, p1, mid)):
                continue
            g0, g1 = pit_ground(*p0), pit_ground(*p1)
            zs = max(g0, g1) + 0.5
            # (the seat, the footboard in front of it a step down toward the dock, posts)
            inward = r < r_road
            ox, oy = (px - mid[0]) / r, (py - mid[1]) / r
            ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
            span = math.dist(p0, p1) + 0.1
            tilt = (math.sin(k * 1.7 + r) * 0.04, 0.0)
            m.add(("weathered_timber", "wall"), lambda bm, mid=mid, zs=zs, ang=ang, span=span, tilt=tilt: cuboid(bm, (mid[0], mid[1], zs), (span, 0.55, 0.1), ang, tilt=tilt))
            m.add(("plank_deck", "wall"), lambda bm, mid=mid, zs=zs, ang=ang, span=span, ox=ox, oy=oy: cuboid(bm, (mid[0] + ox * 0.75, mid[1] + oy * 0.75, zs - 0.45), (span, 0.7, 0.08), ang))
            if k % 2 == 0:
                for p, g in ((p0, g0),):
                    m.add(W_, lambda bm, p=p, g=g, zs=zs: props.tube(bm, [(p[0], p[1], g - 0.3), (p[0], p[1], zs)], 0.07, n=4))
                    q = (p[0] + ox * 0.75, p[1] + oy * 0.75)
                    gq = pit_ground(*q)
                    m.add(W_, lambda bm, q=q, gq=gq, zs=zs: props.tube(bm, [(q[0], q[1], gq - 0.3), (q[0], q[1], zs - 0.45)], 0.06, n=4))
            # (a back rail on the top row; sails over every few bays; lanterns; flags)
            top = ri == 0 or (not inward and ri == len([x for x in rows if x > r_road]) - 1)
            if not inward and r + 3.0 >= min(f2 - 2.0, f1 + 6.0):
                b0, b1 = (p0[0] - ox * 0.4, p0[1] - oy * 0.4), (p1[0] - ox * 0.4, p1[1] - oy * 0.4)
                m.add(W_, lambda bm, b0=b0, b1=b1, zs=zs: props.tube(bm, [(b0[0], b0[1], zs + 0.9), (b1[0], b1[1], zs + 0.9)], 0.05, n=3))
                if k % 4 == 0:
                    m.add(W_, lambda bm, b0=b0, zs=zs, g0=g0: props.tube(bm, [(b0[0], b0[1], g0), (b0[0], b0[1], zs + 0.9)], 0.07, n=4))
                if k % 9 == 4:
                    S.flag_pole(m, b0[0], b0[1], zs, 5.0, k, face=(ox, oy))
                if k % 6 == 2:
                    c.place(hp.cage_lantern(c, k), b0[0], b0[1], zs + 1.6, role="visual")
                    D.light(c, "lantern", b0[0], b0[1], zs + 1.5)
            if k % 7 == 3 and ri % 2 == 0:
                # (a sail over the bay, on poles)
                q0 = (p0[0] - ox * 1.2, p0[1] - oy * 1.2)
                q1 = (p1[0] - ox * 1.2, p1[1] - oy * 1.2)
                h0, h1 = zs + 2.6, zs + 1.9
                for q in (q0, q1):
                    m.add(W_, lambda bm, q=q, zs=zs, h0=h0: props.tube(bm, [(q[0], q[1], zs - 0.3), (q[0], q[1], h0)], 0.05, n=3))
                R.cloth(m, S.AWNINGS[(k + ri) % len(S.AWNINGS)],
                        [(q0[0], q0[1], h0), (q1[0], q1[1], h0), (p1[0] + ox * 1.4, p1[1] + oy * 1.4, h1), (p0[0] + ox * 1.4, p0[1] + oy * 1.4, h1)])
            # (the crowd on it, watching the galleon)
            if (k + int(r)) % 3 == 0 or n > 420:
                continue
            for t in (0.3, 0.75):
                x, y = p0[0] + (p1[0] - p0[0]) * t + ox * 0.75, p0[1] + (p1[1] - p0[1]) * t + oy * 0.75
                D.person(c, x, y, zs - 0.4, ("cheer", "wave", "huddle", "cheer")[(k + int(t * 4)) % 4], sx, sy)
                n += 1
    m.build(c, "Dry Dock Stands", coll="Props", role="visual")
    print("stands: %d in the crowd" % n)
