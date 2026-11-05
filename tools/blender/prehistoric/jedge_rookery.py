# The Edge of the World's middle, reimagined (Blake, Nov 4: "we need to reimagine the next
# section of the edge of the world passage ... it is veery boring currently"; "lets do all
# of it"): from the docks to the Fighting Pits' gate.
# SPDX-License-Identifier: MIT
#
#   the Rookery       a crooked canyon street through the smugglers' slum: tenements
#                     stacked four storeys up its walls, leaning out over the road, balconies
#                     and washing and rope bridges overhead, crocs at every door and on every
#                     balcony; the water street down its right side, its towpath, rowing
#                     boats, the culvert it comes in by and the grate it goes out by;
#   the Rusty Anchor  the slum's fish-fry diner the road drives straight through: in the
#                     front door, past the kitchen's counter (the cooks, the fryers and their
#                     steam, baskets of fish and chips, the menu board, the giant fish on the
#                     wall), the diners at the counter and the tables, the piano and its
#                     player, a little band, the chandeliers; out the back door;
#   the Gallery       out of the rock high on the Night Bazaar's wall, the whole market lit
#                     up below: a scaffold ledge down the wall, the hairpin round the lookout
#                     tower, back along under it to the floor;
#   the lanes         Spice Row (the road: stalls on both sides under their awnings, sacks of
#                     spice, coloured smoke, fire-breathers) and the Beast Market (the side
#                     road: cages of dragonets and birds, pens of crocs, eggs, the
#                     auctioneer), either side of the Broker's ship, to the Pits' gate.
#
# jedge_districts.dress() calls rookery(), tavern(), gallery() and lanes() (bazaar()).

import math

from course_kit import lerp
from gulch_scenery import Mesh
from pocket_build import box, cone
import props
from props import cuboid
import gulch_props as gp
import harbour_props as hp
import swamp_props as sw
import beach_props as bp
import region_paint as paint
import jedge_layout as L
from jedge_layout import BAZ_FLOOR, BAZ_Z, BAZAAR, BEAST_MARKET, ROOK_CANAL, ROOK_N, ROOK_S, ROOK_WATER, ellipse

D = None  # (jedge_districts: set by dress(), for person, light, talkers, lantern_line and the rest)

SIDINGS = ("siding_brown", "siding_grey", "siding_red", "siding_ochre", "siding_green", "wood_wall", "wreck_planks", "cabin_plaster")
SIGN_TILES = {"sign_anchor": 3, "sign_nightbazaar": 4, "sign_spicerow": 3, "sign_beastmarket": 3, "sign_pawn": 1,
              "sign_soup": 1, "sign_bait": 1, "sign_maps": 1, "sign_rope": 1, "sign_fishfry": 2, "sign_menu": 3}
SHOP_SIGNS = ("sign_pawn", "sign_soup", "sign_bait", "sign_maps", "sign_rope")
W = ("weathered_timber", "wall")


def rnd(k):
    return (math.sin(k * 12.9898 + 4.1414) * 43758.5453) % 1.0


class Frame:
    """A spot on the road: its middle, along (t) and to the right (r), and its height."""

    def __init__(self, q):
        self.x, self.y, self.z = q.p.x, q.p.y, q.p.z
        n = math.hypot(q.t.x, q.t.y) or 1.0
        self.tx, self.ty = q.t.x / n, q.t.y / n
        self.rx, self.ry = self.ty, -self.tx
        self.w = q.w

    def P(self, u, v):
        """(x, y) u along and v to the right."""
        return self.x + self.tx * u + self.rx * v, self.y + self.ty * u + self.ry * v


def facing(dx, dy):
    """The rot that turns a thing built facing local -Y to face (dx, dy)."""
    return math.atan2(dx, -dy)


def local(x, y, rot, lx, ly):
    ca, sa = math.cos(rot), math.sin(rot)
    return x + lx * ca - ly * sa, y + lx * sa + ly * ca


def sign(m, sid, cx, cy, nx, ny, hw, z0, z1, out=0.06):
    """A painted sign, its tiles side by side, facing (nx, ny)."""
    rx, ry = -ny, nx
    ox, oy = cx + nx * out, cy + ny * out
    n = SIGN_TILES[sid]
    w = 2 * hw / n
    for k in range(n):
        a, b = -hw + k * w, -hw + (k + 1) * w
        pts = [(ox + rx * a, oy + ry * a, z0), (ox + rx * b, oy + ry * b, z0), (ox + rx * b, oy + ry * b, z1), (ox + rx * a, oy + ry * a, z1)]
        m.quad(("%s_%d" % (sid, k + 1), "wall"), pts, [(0, 0), (1, 0), (1, 1), (0, 1)])
    # (its board behind it)
    m.add(W, lambda bm: cuboid(bm, (cx - nx * 0.04, cy - ny * 0.04, (z0 + z1) / 2), (2 * hw + 0.3, 0.12, z1 - z0 + 0.3), facing(nx, ny)))


def cloth(m, mat, pts):
    m.add((mat, "wall"), lambda bm: bm.faces.new([bm.verts.new(p) for p in pts]))
    m.add((mat, "wall"), lambda bm: bm.faces.new([bm.verts.new(p) for p in reversed(pts)]))


def washing_line(m, p0, p1, sag, k, cols=("rug", "canvas_torn", "awning_red", "sail_cloth", "awning_teal", "robe_cloth")):
    """A line strung between two points, sagging, with the washing pegged on it."""
    n = 8
    pts = [(lerp(p0[0], p1[0], i / n), lerp(p0[1], p1[1], i / n), lerp(p0[2], p1[2], i / n) - sag * 4 * (i / n) * (1 - i / n))
           for i in range(n + 1)]
    m.add(("rope_rail", "wall"), lambda bm: props.tube(bm, pts, 0.03, n=3))
    span = math.dist(p0, p1)
    dx, dy = (p1[0] - p0[0]) / span, (p1[1] - p0[1]) / span
    for f in range(max(2, int(span / 2.4))):
        t = (f + 0.5) / max(2, int(span / 2.4))
        if rnd(k * 7 + f) < 0.25:
            continue
        x, y = lerp(p0[0], p1[0], t), lerp(p0[1], p1[1], t)
        z = lerp(p0[2], p1[2], t) - sag * 4 * t * (1 - t)
        hw = 0.35 + 0.3 * rnd(k + f * 3)
        h = 0.7 + 0.7 * rnd(k * 3 + f)
        cloth(m, cols[(k + f) % len(cols)], [(x - dx * hw, y - dy * hw, z), (x + dx * hw, y + dy * hw, z), (x + dx * hw, y + dy * hw, z - h),
                                               (x - dx * hw, y - dy * hw, z - h * 0.9)])


def tenement(m, solid, x, y, z0, rot, w, d, floors, k, shop=True):
    """A slum tenement against the canyon's wall, its front (local -Y) to the road: a floor
    on a floor on a floor, each a bit further out over the street, each its own siding;
    lit windows and shutters, a door and a shop sign at the street, balconies with their
    washing and a croc or two out on them, a tin roof, a stovepipe. Returns where the
    balconies' folk stand and the windows' light."""
    fh = 3.0
    over = 0.75
    folk = []
    lights = []

    def P(lx, ly, z):
        px, py = local(x, y, rot, lx, ly)
        return px, py, z

    for i in range(floors):
        front = -i * over
        zb = z0 + i * fh
        mat = (SIDINGS[(k * 3 + i * 5) % len(SIDINGS)], "wall")
        cx, cy, _ = P(0.0, (front + d) / 2, 0)
        tgt = solid if i == 0 else m
        tgt.add(mat, lambda bm, cx=cx, cy=cy, zb=zb, front=front: cuboid(bm, (cx, cy, zb + fh / 2), (w - 0.3 * (i % 2), d - front, fh), rot))
        # (the floor's beam, proud of the wall)
        bx, by, _ = P(0.0, front - 0.08, 0)
        m.add(W, lambda bm, bx=bx, by=by, zb=zb: cuboid(bm, (bx, by, zb + 0.1), (w + 0.2, 0.25, 0.22), rot))
        # (its windows: lit, or dark, shutters flung open)
        nwin = 2 if w > 5.5 else 1
        for j in range(nwin):
            if i == 0 and j == 0:
                continue
            lx = (j - (nwin - 1) / 2) * (w / nwin)
            lit = rnd(k * 11 + i * 3 + j) < 0.7
            wx, wy, _ = P(lx, front - 0.04, 0)
            nx, ny = math.sin(rot), -math.cos(rot)
            ax, ay = math.cos(rot), math.sin(rot)
            pts = [(wx - ax * 0.5 + nx * 0.02, wy - ay * 0.5 + ny * 0.02, zb + 1.0), (wx + ax * 0.5 + nx * 0.02, wy + ay * 0.5 + ny * 0.02, zb + 1.0),
                   (wx + ax * 0.5 + nx * 0.02, wy + ay * 0.5 + ny * 0.02, zb + 2.3), (wx - ax * 0.5 + nx * 0.02, wy - ay * 0.5 + ny * 0.02, zb + 2.3)]
            m.quad(("window_lit" if lit else "window_dark", "wall"), pts, [(0, 0), (1, 0), (1, 1), (0, 1)])
            for sd in (-1, 1):
                sx, sy = wx + ax * sd * 0.82 + nx * 0.25, wy + ay * sd * 0.82 + ny * 0.25
                m.add(("door_wood", "wall"), lambda bm, sx=sx, sy=sy, zb=zb, sd=sd: cuboid(bm, (sx, sy, zb + 1.65), (0.5, 0.06, 1.35),
                                                                                            rot + sd * 1.1))
            if lit:
                lights.append(P(lx, front - 1.2, zb + 1.7))
            if lit and i >= 1 and rnd(k * 5.3 + i * 1.9 + j) < 0.45 and not ((i + k) % 2 == 0):
                # (a window box, a croc leaning on it looking out at the street)
                bx_, by_, _ = P(lx, front - 0.75, 0)
                m.add(("plank_deck", "wall"), lambda bm, bx_=bx_, by_=by_, zb=zb: cuboid(bm, (bx_, by_, zb + 0.55), (1.3, 0.36, 0.9), rot))
                for fl in range(3):
                    fx_, fy_, _ = P(lx - 0.4 + fl * 0.4, front - 0.75, 0)
                    m.add((("awning_red", "lush_grass", "awning_sun")[fl], "wall"),
                          lambda bm, fx_=fx_, fy_=fy_, zb=zb: props.blob(bm, (fx_, fy_, zb + 1.08), 0.16, subdiv=0))
                folk.append(P(lx, front - 0.32, zb + 0.02))
        # (a balcony, every other floor up)
        if i >= 1 and (i + k) % 2 == 0:
            bx, by, _ = P(0.0, front - 0.7, 0)
            m.add(("plank_deck", "wall"), lambda bm, bx=bx, by=by, zb=zb: cuboid(bm, (bx, by, zb), (w * 0.8, 1.4, 0.16), rot))
            pts = [P(-w * 0.4, front - 1.35, zb + 1.0), P(w * 0.4, front - 1.35, zb + 1.0)]
            m.add(W, lambda bm, pts=pts: props.tube(bm, [p for p in pts], 0.05, n=4))
            for lx in (-w * 0.4, 0.0, w * 0.4):
                a = P(lx, front - 1.35, zb)
                m.add(W, lambda bm, a=a, zb=zb: props.tube(bm, [a, (a[0], a[1], zb + 1.05)], 0.05, n=4))
            # (its washing, on a line under the eave above)
            washing_line(m, P(-w * 0.45, front - 1.2, zb + fh - 0.3), P(w * 0.45, front - 1.2, zb + fh - 0.4), 0.3, k * 5 + i)
            folk.append((P(-w * 0.2 + 0.4 * (i % 2) * w * 0.3, front - 0.8, zb + 0.08)))
    # The street door, the shop's sign and awning.
    dx, dy, _ = P(-w * 0.25, -0.04, 0)
    nx, ny = math.sin(rot), -math.cos(rot)
    ax, ay = math.cos(rot), math.sin(rot)
    pts = [(dx - ax * 0.6 + nx * 0.03, dy - ay * 0.6 + ny * 0.03, z0), (dx + ax * 0.6 + nx * 0.03, dy + ay * 0.6 + ny * 0.03, z0),
           (dx + ax * 0.6 + nx * 0.03, dy + ay * 0.6 + ny * 0.03, z0 + 2.4), (dx - ax * 0.6 + nx * 0.03, dy - ay * 0.6 + ny * 0.03, z0 + 2.4)]
    m.quad(("door_wood", "wall"), pts, [(0, 0), (1, 0), (1, 1), (0, 1)])
    if shop and rnd(k * 13) < 0.55:
        sx, sy, _ = P(w * 0.18, -0.1, 0)
        sign(m, SHOP_SIGNS[k % len(SHOP_SIGNS)], sx, sy, nx, ny, 0.9, z0 + 2.55, z0 + 3.45, out=0.08)
        a0, a1 = P(-w * 0.45, 0.0, 0), P(w * 0.45, 0.0, 0)
        b0, b1 = P(-w * 0.45, -1.3, 0), P(w * 0.45, -1.3, 0)
        cloth(m, ("awning_red", "awning_teal", "canvas_torn", "awning_green", "awning_sun")[k % 5],
              [(a0[0], a0[1], z0 + 2.4), (a1[0], a1[1], z0 + 2.4), (b1[0], b1[1], z0 + 2.0), (b0[0], b0[1], z0 + 2.0)])
    # The roof, the stovepipe, a pole and its rag of a flag.
    top = z0 + floors * fh
    front = -(floors - 1) * over
    rx_, ry_, _ = P(0.0, (front + d) / 2, 0)
    m.add(("tin_roof", "wall"), lambda bm: cuboid(bm, (rx_, ry_, top + 0.35), (w + 0.6, d - front + 0.8, 0.14), rot, tilt=(0.18, 0.0)))
    sx, sy, _ = P(w * 0.28, d * 0.6, 0)
    m.add(("iron", "wall"), lambda bm: props.tube(bm, [(sx, sy, top), (sx, sy, top + 2.2)], 0.14, n=6))
    return folk, lights, top


def _gate(m, f, name_sid, z, half, faces=(-1, 1)):
    """A timber gate over the road: two posts, a beam, a painted sign each way."""
    for sd in (-1, 1):
        px, py = f.P(0.0, sd * half)
        m.add(W, lambda bm, px=px, py=py: cuboid(bm, (px, py, z + 4.2), (0.7, 0.7, 9.0), facing(f.tx, f.ty)))
    cx, cy = f.P(0.0, 0.0)
    m.add(W, lambda bm: cuboid(bm, (cx, cy, z + 8.6), (2 * half + 1.6, 0.7, 0.9), facing(f.tx, f.ty) + math.pi / 2 - math.pi / 2))
    for sd in faces:
        sx, sy = f.P(sd * 0.5, 0.0)
        sign(m, name_sid, sx, sy, f.tx * sd, f.ty * sd, 3.6 if SIGN_TILES[name_sid] >= 3 else 1.2, z + 6.4, z + 7.9, out=0.1)


# ------------------------------------------------------------------ the Rookery


def rookery(c, ground, taken):
    """The Rookery: tenements up both walls, the water street, the towpath, washing and
    rope bridges overhead, crocs everywhere."""
    m, solid = Mesh(), Mesh()
    s_a = c.nearest(*L.ROUTE[L.AT["rook0"]][:2])[0].s  # (past the harbour: it's left as it was)
    s_b = c.nearest(*L.ROUTE[L.AT["portal"]][:2])[0].s
    s_t0 = c.nearest(*L.ROUTE[L.AT["tav0"]][:2])[0].s - 4.0
    s_t1 = c.nearest(*L.ROUTE[L.AT["tav1"]][:2])[0].s + 4.0
    s_c0 = c.nearest(*L.ROUTE[L.AT["rook1"]][:2])[0].s
    s_c1 = c.nearest(*L.ROUTE[L.AT["rook3"]][:2])[0].s
    lights = []
    tops = {}
    n_folk = 0
    k = 0
    # The left wall's tenements, shoulder to shoulder; the right's where the water street
    # isn't (past its end), and on its far bank.
    for side in (-1, 1):
        s = s_a + 4.0
        while s < s_b - 6.0:
            q = c.at(s)
            f = Frame(q)
            w = 5.0 + 3.0 * rnd(k * 1.7 + side)
            canal = s_c0 - 2.0 < s < s_c1 + 2.0
            if s_t0 - 2.0 < s < s_t1 + 2.0 and side < 0:
                s += 3.0
                continue
            if side < 0:
                v_front, d = -(f.w / 2 + 2.4), ROOK_N - f.w / 2 - 2.6
            elif canal:
                v_front, d = ROOK_CANAL[0] + ROOK_CANAL[1] + 0.6, ROOK_S - ROOK_CANAL[0] - ROOK_CANAL[1] - 1.2
            else:
                v_front, d = f.w / 2 + 2.4, 4.0
            hx, hy = f.P(0.0, v_front + side * d / 2)
            if not taken.clear(hx, hy, w * 0.45):
                s += 2.0
                continue
            fx, fy = f.P(0.0, v_front)
            rot = facing(-f.rx * side, -f.ry * side)
            z0 = f.z - 0.3
            floors = 3 + int(rnd(k * 2.3 + side) * 2.0)
            folk, lit, top = tenement(m, solid, fx, fy, z0, rot, w, d, floors, k)
            lights += lit
            taken.add(hx, hy, w * 0.5)
            tops.setdefault(side, []).append((s, f.P(0.0, v_front - side * 0.4), top, z0))
            for (px, py, pz) in folk:
                D.folk(c, px, py, pz, ("watch", "wave", "cheer", "watch", "point", "shrug")[(k + n_folk) % 6], f.x, f.y)
                n_folk += 1
            # (folk at the street door, by turns)
            if side < 0 or not canal:
                if k % 2 == 0:
                    px, py = f.P(-0.6, v_front - side * 0.9)
                    D.folk(c, px, py, f.z - 0.3, ("watch", "think", "wave", "nod")[k % 4], f.x, f.y)
                    n_folk += 1
            k += 1
            s += w + 0.4
    # The water street: its water, its stone banks, the culvert it comes in by from the
    # docks' water gate, the grate it goes out by, the towpath's lamps, bollards and folk.
    centre = []
    s = s_c0
    while s <= s_c1:
        f = Frame(c.at(s))
        centre.append(f.P(0.0, ROOK_CANAL[0]))
        s += 3.0
    c.ribbon("Rookery Water", centre, 2 * ROOK_CANAL[1] + 1.2, ROOK_WATER, c.lib("harbour_flow", "deep_water"), role="visual")
    s = s_c0
    j = 0
    while s < s_c1:
        f0, f1 = Frame(c.at(s)), Frame(c.at(min(s + 3.0, s_c1)))
        for sd in (-1, 1):
            v = ROOK_CANAL[0] + sd * ROOK_CANAL[1]
            a, b = f0.P(0.0, v), f1.P(0.0, v)
            za, zb = f0.z - 0.3, f1.z - 0.3
            pts = [(a[0], a[1], ROOK_WATER - 1.5), (b[0], b[1], ROOK_WATER - 1.5), (b[0], b[1], zb), (a[0], a[1], za)]
            m.quad(("bog_dark_stone", "wall"), pts if sd < 0 else pts[::-1], [(0, 0), (1, 0), (1, (zb - ROOK_WATER) / 2), (0, (za - ROOK_WATER) / 2)])
            pts = [(a[0], a[1], ROOK_WATER - 0.05), (b[0], b[1], ROOK_WATER - 0.05), (b[0], b[1], ROOK_WATER + 0.3), (a[0], a[1], ROOK_WATER + 0.3)]
            m.quad(("glow_moss", "wall"), pts if sd < 0 else pts[::-1], [(0, 0), (1, 0), (1, 1), (0, 1)])
            cx, cy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            m.add(("keep_ashlar_dark", "wall"), lambda bm, cx=cx, cy=cy, z=(za + zb) / 2: cuboid(bm, (cx, cy, z + 0.1), (3.05, 0.6, 0.24),
                                                                                            facing(f0.tx, f0.ty) + math.pi / 2))
        if j % 4 == 0:
            # (a lamp post on the towpath, a bollard, a croc fishing off the edge)
            lx, ly = f0.P(0.0, ROOK_CANAL[0] - ROOK_CANAL[1] - 0.9)
            m.add(("iron", "wall"), lambda bm, lx=lx, ly=ly, z=f0.z: props.tube(bm, [(lx, ly, z - 0.3), (lx, ly, z + 4.2)], 0.1, n=6))
            D.light(c, "lantern", lx, ly, f0.z + 4.4)
            bx, by = f0.P(1.5, ROOK_CANAL[0] - ROOK_CANAL[1] - 0.6)
            m.add(("keep_iron", "wall"), lambda bm, bx=bx, by=by, z=f0.z: props.tube(bm, [(bx, by, z - 0.3), (bx, by, z + 0.6)], 0.22, n=8))
            px, py = f0.P(-1.5, ROOK_CANAL[0] - ROOK_CANAL[1] - 0.5)
            D.person(c, px, py, f0.z - 0.3, "fisher", *f0.P(-1.5, ROOK_CANAL[0]))
            n_folk += 1
        elif j % 4 == 2 and not (s_t0 < s < s_t1):
            px, py = f0.P(0.0, f0.w / 2 + 2.6)
            c.place(gp.crate_stack(c, j % 4) if j % 3 else gp.barrel(c, j % 2), px, py, f0.z - 0.3, rot=j, role="both")
            hx, hy = f0.P(1.6, f0.w / 2 + 2.4)
            D.person(c, hx, hy, f0.z - 0.3, ("hauler", "worker", "huddle")[j % 3], px, py)
            n_folk += 1
        s += 3.0
        j += 1
    # (the culvert at the water street's head: the docks' water in through an arch in a
    # headwall, falling into it; and the grate at its foot it drains away through)
    for end, s_e, dirn in (("Culvert", s_c0, 1), ("Grate", s_c1, -1)):
        f = Frame(c.at(s_e))
        cx, cy = f.P(0.0, ROOK_CANAL[0])
        rot = facing(f.tx * dirn, f.ty * dirn)
        solid.add(("keep_ashlar_dark", "wall"), lambda bm, cx=cx, cy=cy, rot=rot, z=f.z: cuboid(bm, (cx - f.tx * dirn * 0.6, cy - f.ty * dirn * 0.6,
                                                                                                  (ROOK_WATER - 2.0 + z + 3.0) / 2),
                                                                                              (2 * ROOK_CANAL[1] + 2.4, 1.2, z + 5.0 - ROOK_WATER), rot))
        ax, ay = cx + f.tx * dirn * 0.02, cy + f.ty * dirn * 0.02
        pts = [local(ax, ay, rot, -2.2, 0.0) + (ROOK_WATER,), local(ax, ay, rot, 2.2, 0.0) + (ROOK_WATER,),
               local(ax, ay, rot, 2.2, 0.0) + (ROOK_WATER + 2.6,), local(ax, ay, rot, -2.2, 0.0) + (ROOK_WATER + 2.6,)]
        m.quad(("window_dark", "wall"), pts, [(0, 0), (1, 0), (1, 1), (0, 1)])
        if end == "Culvert":
            props.falls(c, "Rookery Culvert Falls", cx, cy, ROOK_WATER + 2.4, ROOK_WATER + 0.05, 3.6, 4.0, facing=1, throw=1.2, bulge=0.3,
                        veils=2, foam=False, angle=math.atan2(f.ty, f.tx) - math.pi / 2,
                        mats=("falls_oasis", "falls_curtain_oasis", "falls_foam"))
            g = c.game(cx + f.tx * 2.0, cy + f.ty * 2.0, ROOK_WATER + 0.5)
            c.entity("mist", x=round(g[0], 1), y=round(g[1], 1), z=round(g[2], 1), radius=5.0, rate=3.0, color="#a8bcb4")
        else:
            for b in range(9):
                lx = -2.0 + b * 0.5
                p0 = local(ax, ay, rot, lx, -0.05)
                m.add(("keep_iron", "wall"), lambda bm, p0=p0: props.tube(bm, [(p0[0], p0[1], ROOK_WATER - 0.4), (p0[0], p0[1], ROOK_WATER + 2.6)], 0.06, n=4))
        D.light(c, "torch", *f.P(0.0, ROOK_CANAL[0] - ROOK_CANAL[1] - 0.6), f.z + 2.6)
    # Rowing boats on the water street (up one side, back down the other).
    pts = []
    s = s_c0 + 8.0
    while s < s_c1 - 8.0:
        pts.append(Frame(c.at(s)).P(0.0, ROOK_CANAL[0] - 1.2))
        s += 6.0
    f_e = Frame(c.at(s_c1 - 6.0))
    pts.append(f_e.P(0.0, ROOK_CANAL[0]))
    back = []
    s = s_c1 - 8.0
    while s > s_c0 + 8.0:
        back.append(Frame(c.at(s)).P(0.0, ROOK_CANAL[0] + 1.2))
        s -= 6.0
    f_s = Frame(c.at(s_c0 + 6.0))
    pts += back + [f_s.P(0.0, ROOK_CANAL[0])]
    c.path_curve("Rookery Boat Round", pts, z=ROOK_WATER, closed=True)
    for b in range(3):
        c.entity("boat", route="Rookery Boat Round", speed=1.8 + 0.2 * b, start=b * 70.0, rig="row",
                 colors=[("#5a2a1a", "#2a4a3a", "#3a3a5a")[b], "#d8c8a0"], scale=0.7)
    # Overhead: washing lines and rope bridges across the street between the walls'
    # tenements, high over the road; lantern strings lower down.
    left = tops.get(-1, [])
    right = tops.get(1, [])
    for i, (s, (lx, ly), top, z0) in enumerate(left):
        if not right:
            break
        r = min(right, key=lambda t: abs(t[0] - s))
        if abs(r[0] - s) > 6.0:
            continue
        (rx_, ry_), rtop, rz0 = r[1], r[2], r[3]
        zl = min(top, rtop) - 1.4
        if zl - max(z0, rz0) < 8.5:
            continue
        if i % 3 == 0:
            # (a rope bridge: two ropes, planks hung between)
            for off in (-0.6, 0.6):
                ux, uy = -Frame(c.at(s)).tx * off, -Frame(c.at(s)).ty * off
                m.add(("rope_rail", "wall"), lambda bm, a=(lx + ux, ly + uy, zl + 1.0), b=(rx_ + ux, ry_ + uy, zl + 1.0):
                      props.tube(bm, [a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, a[2] - 1.6), b], 0.04, n=3))
            span = math.hypot(rx_ - lx, ry_ - ly)
            for p in range(int(span / 0.9)):
                t = (p + 0.5) / int(span / 0.9)
                px, py = lerp(lx, rx_, t), lerp(ly, ry_, t)
                pz = zl - 1.6 * 4 * t * (1 - t) * 1.0
                m.add(("plank_deck", "wall"), lambda bm, px=px, py=py, pz=pz: cuboid(bm, (px, py, pz), (0.35, 1.4, 0.08),
                                                                                      math.atan2(ry_ - ly, rx_ - lx)))
            if i % 2 == 0:
                bx, by = lerp(lx, rx_, 0.4), lerp(ly, ry_, 0.4)
                fx_, fy_ = bx + (ry_ - ly), by - (rx_ - lx)
                D.folk(c, bx, by, zl - 1.6 * 0.96 + 0.05, "wave", fx_, fy_)
                n_folk += 1
        else:
            washing_line(m, (lx, ly, zl), (rx_, ry_, zl - 0.6), 1.6, i * 9)
    s = s_a + 10.0
    j = 0
    while s < s_b - 10.0:
        if not s_t0 - 6.0 < s < s_t1 + 6.0 and j % 2 == 0:
            f = Frame(c.at(s))
            a = f.P(0.0, -(f.w / 2 + 2.2)) + (f.z + 6.6,)
            b = f.P(0.0, f.w / 2 + 2.2) + (f.z + 6.6,)
            D.lantern_line(c, "Rookery String %d" % j, a, b, sag=1.0)
        s += 13.0
        j += 1
    for x, y, z in lights[::3]:
        D.light(c, "glow", x, y, z)
    # The Rookery's talkers.
    for j, s in enumerate((s_a + 30.0, (s_c0 + s_t0) / 2, s_b - 30.0)):
        f = Frame(c.at(s))
        px, py = f.P(0.0, -(f.w / 2 + 1.6))
        D.talkers(c, px, py, f.z, 4, "rookery", r=4.0)
    m.build(c, "Rookery", coll="Props", role="visual")
    solid.build(c, "Rookery Walls", coll="Props", role="both")
    print("rookery: %d tenements, %d folk" % (k, n_folk))


# ------------------------------------------------------------------ the Rusty Anchor


def tavern(c, ground, taken):
    """The Rusty Anchor Fish Fry, the slum's diner: the road in at its front door and out
    the back."""
    m, solid = Mesh(), Mesh()
    s0 = c.nearest(*L.ROUTE[L.AT["tav0"]][:2])[0].s
    s1 = c.nearest(*L.ROUTE[L.AT["tav1"]][:2])[0].s
    f = Frame(c.at((s0 + s1) / 2))
    half = (s1 - s0) / 2 + 3.0
    z = min(c.at(s0).p.z, c.at(s1).p.z) - 0.35
    rot = facing(-f.tx, -f.ty)  # (the building's local -Y: back along the road, to the front door)
    along = math.atan2(f.ty, f.tx)
    H, RIDGE = 8.0, 11.6
    VW, VD = 12.6, 9.8  # (the walls' inside, the doors' half width)

    def P(u, v):
        return f.P(u, v)

    def slab(tgt, mat, u, v, su, sv, z0, z1):
        x, y = P(u, v)
        tgt.add((mat, "wall"), lambda bm: cuboid(bm, (x, y, (z0 + z1) / 2), (su, sv, z1 - z0), along))

    # The walls: the sides whole; the ends round their great doors.
    for sd in (-1, 1):
        slab(solid, "wreck_planks", 0.0, sd * (VW + 0.3), 2 * half, 0.6, z, z + H)
        for e in (-1, 1):
            slab(solid, "wreck_planks", e * half, sd * (VD + VW + 0.6) / 2, 0.6, VW + 0.6 - VD, z, z + H)
    for e in (-1, 1):
        slab(m, "wreck_planks", e * half, 0.0, 0.6, 2 * VD, z + 6.2, z + H)
        # (the gable over the door)
        a, b, cc = P(e * half, -(VW + 0.6)), P(e * half, VW + 0.6), P(e * half, 0.0)
        for pts in ([(a[0], a[1], z + H), (b[0], b[1], z + H), (cc[0], cc[1], z + RIDGE)],):
            cloth(m, "wood_wall", pts)
        # (the doorposts and the swing doors pinned open against the walls inside)
        for sd in (-1, 1):
            slab(m, "weathered_timber", e * half, sd * (VD + 0.2), 0.9, 0.4, z, z + 6.4)
            slab(m, "door_wood", e * (half - 1.3), sd * (VD - 0.3), 2.0, 0.12, z + 0.9, z + 3.3)
        # (the painted sign over the door, facing out; the lamps either side)
        sx, sy = P(e * (half + 0.32), 0.0)
        sign(m, "sign_anchor", sx, sy, f.tx * e, f.ty * e, 4.2, z + 6.4, z + 7.8, out=0.06)
        for sd in (-1, 1):
            hx_, hy_ = P(e * (half + 0.7), sd * (VD + 1.9))
            m.add(("keep_iron", "wall"), lambda bm, hx_=hx_, hy_=hy_: props.tube(bm, [(hx_ - f.tx * e * 0.4, hy_ - f.ty * e * 0.4, z + 5.4),
                                                                                 (hx_ + f.tx * e * 0.5, hy_ + f.ty * e * 0.5, z + 5.4)], 0.05, n=4))
            sign(m, "sign_fishfry", hx_ + f.tx * e * 0.3, hy_ + f.ty * e * 0.3, f.tx * e, f.ty * e, 1.4, z + 4.1, z + 5.2, out=0.0)
        for sd in (-1, 1):
            D.light(c, "lantern", *P(e * (half + 1.0), sd * (VD + 1.4)), z + 4.6)
    # The roof: two slopes on the walls, the ridge along the road.
    for sd in (-1, 1):
        a0, a1 = P(-half - 1.0, sd * (VW + 1.6)), P(half + 1.0, sd * (VW + 1.6))
        b0, b1 = P(-half - 1.0, 0.0), P(half + 1.0, 0.0)
        pts = [(a0[0], a0[1], z + H - 0.4), (a1[0], a1[1], z + H - 0.4), (b1[0], b1[1], z + RIDGE + 0.2), (b0[0], b0[1], z + RIDGE + 0.2)]
        m.quad(("shingle_roof", "wall"), pts, [(0, 0), (8, 0), (8, 4), (0, 4)])
        m.quad(("shingle_roof", "wall"), pts[::-1], [(0, 4), (8, 4), (8, 0), (0, 0)])
    # Inside: the floorboards off the road, beams across, the chandeliers.
    for sd in (-1, 1):
        slab(m, "plank_deck", 0.0, sd * (f.w / 2 + 1.6 + VW) / 2, 2 * half - 0.6, VW - f.w / 2 - 1.6, z - 0.2, z + 0.32)
    u = -half + 2.0
    while u < half - 1.0:
        slab(m, "timber_beam", u, 0.0, 0.45, 2 * VW, z + 7.3, z + 7.75)
        u += 4.0
    for j, u in enumerate((-half * 0.55, 0.0, half * 0.55)):
        cx, cy = P(u, 0.0)
        ring = [(cx + 1.6 * math.cos(a), cy + 1.6 * math.sin(a), z + 6.0) for a in [i * math.tau / 12 for i in range(13)]]
        m.add(("keep_iron", "wall"), lambda bm, ring=ring: props.tube(bm, ring, 0.05, n=4))
        for a in (0.0, 2.1, 4.2):
            m.add(("keep_iron", "wall"), lambda bm, a=a: props.tube(bm, [(cx + 1.6 * math.cos(a), cy + 1.6 * math.sin(a), z + 6.0), (cx, cy, z + 7.3)],
                                                                    0.02, n=3))
        for i in range(6):
            a = i * math.tau / 6
            c.place(hp.cage_lantern(c, i + j), cx + 1.6 * math.cos(a), cy + 1.6 * math.sin(a), z + 5.75, role="visual")
        D.light(c, "lantern", cx, cy, z + 5.6)
        D.light(c, "glow", cx, cy, z + 4.0)
    # The kitchen along the left wall (Blake, Nov 4: "this is going to be for all ages ...
    # perhaps a bar isnt the best option"; he picked the fish-fry diner): the long counter,
    # the fryers bubbling on it and their steam, baskets of fish and chips waiting, plates
    # stacked on the shelves behind, the menu board, the giant fish mounted over it all;
    # the cooks behind the counter, the diners along it.
    VB = -(f.w / 2 + 2.3)
    slab(solid, "barrel_wood", 0.0, VB - 0.4, 2 * half - 6.0, 0.8, z, z + 1.1)
    slab(m, "plank_deck", 0.0, VB - 0.4, 2 * half - 5.6, 1.1, z + 1.1, z + 1.22)
    for j, u in enumerate((-half * 0.5, -half * 0.15, half * 0.2)):
        fx_, fy_ = P(u, VB - 0.45)
        m.add(("keep_iron", "wall"), lambda bm, fx_=fx_, fy_=fy_: cuboid(bm, (fx_, fy_, z + 1.45), (1.4, 0.7, 0.5), along))
        m.add(("lantern_amber", "wall"), lambda bm, fx_=fx_, fy_=fy_: cuboid(bm, (fx_, fy_, z + 1.71), (1.25, 0.56, 0.04), along))
        g = c.game(fx_, fy_, z + 2.0)
        c.entity("steam", x=round(g[0], 2), y=round(g[1], 2), z=round(g[2], 2))
        D.light(c, "glow", fx_, fy_, z + 2.2)
    u = -half + 3.6
    b = 0
    while u < half - 3.6:
        if b % 3 == 1:
            # (a basket of fish and chips waiting on the counter)
            bx, by = P(u, VB - 0.3)
            m.add(("barrel_wood", "wall"), lambda bm, bx=bx, by=by: props.tube(bm, [(bx, by, z + 1.22), (bx, by, z + 1.4)], 0.2, n=8))
            for q in range(3):
                qx, qy = bx + 0.09 * math.cos(q * 2.1), by + 0.09 * math.sin(q * 2.1)
                m.add(("ember_gold", "wall"), lambda bm, qx=qx, qy=qy: props.blob(bm, (qx, qy, z + 1.45), 0.1, sx=1.6, subdiv=0))
        u += 1.4
        b += 1
    for lvl in (1.8, 2.6, 3.4):
        slab(m, "plank_deck", 0.0, -(VW - 0.25), 2 * half - 6.0, 0.5, z + lvl, z + lvl + 0.08)
        u = -half + 3.4
        b = 0
        while u < half - 3.4:
            bx, by = P(u, -(VW - 0.25))
            if b % 4 == 3:
                # (a jar: pickles, sauce, the cook's secret)
                mat = ("lantern_green", "lantern_red", "lantern_amber")[(b // 4) % 3]
                m.add((mat, "wall"), lambda bm, bx=bx, by=by, lvl=lvl: props.tube(bm, [(bx, by, z + lvl + 0.08), (bx, by, z + lvl + 0.42)], 0.11, n=6))
            else:
                # (a stack of plates)
                m.add(("party_white", "wall"), lambda bm, bx=bx, by=by, lvl=lvl: props.tube(bm, [(bx, by, z + lvl + 0.08), (bx, by, z + lvl + 0.22)], 0.16, n=8))
            u += 0.45
            b += 1
    mx, my = P(-half * 0.3, -(VW - 0.08))
    sign(m, "sign_menu", mx, my, f.rx, f.ry, 2.6, z + 4.0, z + 4.9, out=0.06)
    # (the giant fish over the counter, mounted on its board)
    gx, gy = P(half * 0.35, -(VW - 0.3))
    slab(m, "door_wood", half * 0.35, -(VW - 0.08), 4.6, 0.12, z + 3.9, z + 5.5)
    m.add((hp.FISH[1], "wall"), lambda bm: props.blob(bm, (gx, gy, z + 4.7), 1.6, sx=1.0, sy=0.28, sz=0.4, subdiv=2))
    tx_, ty_ = gx - f.tx * 1.9, gy - f.ty * 1.9
    cloth(m, hp.FISH[1], [(tx_, ty_, z + 4.7), (tx_ - f.tx * 0.9, ty_ - f.ty * 0.9, z + 5.4), (tx_ - f.tx * 0.9, ty_ - f.ty * 0.9, z + 4.0)])
    for e in (-1, 1):
        c.place(gp.barrel(c, 0), *P(e * (half - 2.0), VB - 0.5), z, rot=e, role="both")
    for j, u in enumerate((-half * 0.45, -half * 0.05, half * 0.3)):
        cx_, cy_ = P(u, -(VW - 1.2))
        D.folk(c, cx_, cy_, z, ("work", "nod", "work")[j], *P(u, 0.0), seed=11 + j)
    u = -half + 4.0
    i = 0
    while u < half - 4.0:
        sx, sy = P(u, VB + 0.6)
        if rnd(i * 3.3) < 0.6:
            # (a diner at the counter, eating)
            D.folk(c, sx, sy, z, ("work", "nod", "watch", "work")[i % 4], *P(u, VB - 1.0))
        else:
            m.add(("door_wood", "wall"), lambda bm, sx=sx, sy=sy: props.tube(bm, [(sx, sy, z), (sx, sy, z + 0.75)], 0.22, n=8))
        u += 1.7
        i += 1
    # The right side: tables of diners with their plates, the hearth, the piano and its
    # player, and a little band on a stage in the corner.
    VT = f.w / 2 + 2.6
    for j, u in enumerate((-half + 4.0, -half + 9.5, 1.0)):
        tx, ty = P(u, VT + 0.6)
        cone(c, "Anchor Table %d" % j, tx, ty, 0.9, z + 0.8, 0.12, ("door_wood", "wall"), segs=10, role="visual")
        m.add(("door_wood", "wall"), lambda bm, tx=tx, ty=ty: props.tube(bm, [(tx, ty, z), (tx, ty, z + 0.8)], 0.12, n=6))
        for i in range(3):
            a = i * math.tau / 3 + j + 0.5
            D.folk(c, tx + 1.45 * math.cos(a), ty + 1.45 * math.sin(a), z, ("nod", "cheer", "work", "watch")[(i + j) % 4], tx, ty)
            px_, py_ = tx + 0.5 * math.cos(a), ty + 0.5 * math.sin(a)
            m.add(("party_white", "wall"), lambda bm, px_=px_, py_=py_: props.tube(bm, [(px_, py_, z + 0.92), (px_, py_, z + 0.95)], 0.22, n=10))
            m.add(("ember_gold", "wall"), lambda bm, px_=px_, py_=py_: props.blob(bm, (px_, py_, z + 1.0), 0.09, sx=1.8, subdiv=0))
    hx, hy = P(-half + 6.5, VW - 0.5)
    solid.add(("keep_ashlar_dark", "wall"), lambda bm: cuboid(bm, (hx, hy, z + 1.8), (3.2, 1.0, 3.6), along))
    m.add(("keep_ashlar_dark", "wall"), lambda bm: cuboid(bm, (hx, hy, z + 5.5), (1.4, 0.8, 4.0), along))
    D.light(c, "campfire", *P(-half + 6.5, VW - 1.3), z + 0.3)
    px, py = P(half - 5.5, VW - 1.0)
    solid.add(("door_wood", "wall"), lambda bm: cuboid(bm, (px, py, z + 0.75), (2.6, 1.1, 1.5), along))
    k0, k1 = P(half - 5.5, VW - 1.62)
    m.add(("party_white", "wall"), lambda bm: cuboid(bm, (k0, k1, z + 1.05), (2.2, 0.3, 0.1), along))
    D.folk(c, *P(half - 5.5, VW - 2.3), z, "work", px, py, seed=21)
    # (the band: a little stage, a drummer and two singers dancing)
    bx, by = P(half - 10.0, VT + 1.6)
    solid.add(("plank_deck", "wall"), lambda bm: cuboid(bm, (bx, by, z + 0.2), (4.6, 2.6, 0.4), along))
    c.place(bp.drum(c), bx + f.rx * 0.6, by + f.ry * 0.6, z + 0.4, role="visual")
    D.folk(c, bx + f.rx * 0.9, by + f.ry * 0.9, z + 0.4, "nod", f.x, f.y, seed=31)
    for i in (-1, 1):
        D.folk(c, bx + f.tx * i * 1.3 - f.rx * 0.3, by + f.ty * i * 1.3 - f.ry * 0.3, z + 0.4, "dance", f.x, f.y, seed=33 + i)
    D.light(c, "glow", bx, by, z + 3.0)
    D.talkers(c, *P(-half + 9.5, VT + 2.0), z, 3, "diner", r=2.5)
    # The back porch over the water street: a croc fishing off it.
    px, py = P(-2.0, VW + 1.6)
    m.add(("plank_deck", "wall"), lambda bm: cuboid(bm, (px, py, z + 0.25), (12.0, 1.8, 0.2), along))
    for u in (-7.6, 3.6):
        for v in (VW + 1.0, VW + 2.2):
            a = P(u, v)
            m.add(W, lambda bm, a=a: props.tube(bm, [(a[0], a[1], ROOK_WATER - 1.0), (a[0], a[1], z + 0.2)], 0.12, n=5))
    D.folk(c, *P(-4.0, VW + 2.1), z + 0.35, "work", *P(-4.0, VW + 6.0), seed=41)
    # The hanging anchor by the front door, the barrels and crates outside.
    for e in (-1, 1):
        ax, ay = P(e * (half + 1.6), -(VD + 1.6))
        m.add(("keep_iron", "wall"), lambda bm, ax=ax, ay=ay: props.tube(bm, [(ax, ay, z + 1.6), (ax, ay, z + 4.6)], 0.14, n=6))
        m.add(("keep_iron", "wall"), lambda bm, ax=ax, ay=ay: props.tube(bm, [(ax - 0.9 * f.tx, ay - 0.9 * f.ty, z + 2.4), (ax, ay, z + 1.5),
                                                                           (ax + 0.9 * f.tx, ay + 0.9 * f.ty, z + 2.4)], 0.12, n=6))
        c.place(gp.crate_stack(c, 1 + (e > 0)), *P(e * (half + 3.0), VD + 1.8), z, rot=e, role="both")
    taken.add(f.x, f.y, half + 2.0)
    m.build(c, "Rusty Anchor", coll="Props", role="visual")
    solid.build(c, "Rusty Anchor Walls", coll="Props", role="both")
    return f, half


# ------------------------------------------------------------------ the Gallery


def gallery(c, ground, taken):
    """The scaffold under the Gallery's deck, its rail lamps and banners, the lookout tower
    in the hairpin with its beacon and crane, and the gate where the road comes out of the
    rock onto it, high over the market."""
    m, solid = Mesh(), Mesh()
    s_a = c.nearest(*L.ROUTE[L.AT["portal"]][:2])[0].s
    s_b = c.nearest(*L.ROUTE[L.AT["baz0"]][:2])[0].s + 10.0
    s = s_a
    j = 0
    prev = None
    first = None
    T = ("scaffold_timber", "wall")
    while s < s_b:
        q = c.at(s)
        f = Frame(q)
        up = q.p.z - BAZ_FLOOR
        inside = ellipse(q.p.x, q.p.y, *BAZAAR) < 0.99
        if up > 1.6 and inside:
            if first is None:
                first = s
            posts = []
            for sd in (-1, 1):
                px, py = f.P(0.0, sd * (f.w / 2 + 0.9))
                gz = ground(px, py)
                top = q.p.z - 1.5
                if top - gz > 0.6:
                    (solid if sd else m).add(T, lambda bm, px=px, py=py, gz=gz, top=top: cuboid(bm, (px, py, (gz + top) / 2), (0.4, 0.4, top - gz),
                                                                                              facing(f.tx, f.ty)))
                posts.append((px, py, gz, top))
            # (ties across under the deck, and down the scaffold every few metres)
            a, b = posts[0], posts[1]
            for zz in [a[3] - 0.3] + [a[2] + h for h in (2.5, 5.5, 8.5, 11.5) if a[2] + h < a[3] - 1.0]:
                m.add(T, lambda bm, zz=zz, a=a, b=b: props.tube(bm, [(a[0], a[1], zz), (b[0], b[1], zz)], 0.11, n=4))
            if prev is not None and j % 2 == 0:
                for sd in (0, 1):
                    p0, p1 = prev[sd], posts[sd]
                    m.add(T, lambda bm, p0=p0, p1=p1: props.tube(bm, [(p0[0], p0[1], p0[2] + 0.4), (p1[0], p1[1], p1[3] - 0.6)], 0.09, n=4))
                    m.add(T, lambda bm, p0=p0, p1=p1: props.tube(bm, [(p0[0], p0[1], p0[3] - 0.6), (p1[0], p1[1], p1[2] + 0.4)], 0.09, n=4))
            prev = posts
            # (the rail's lamps; banners hung off the rail down the scaffold toward the market)
            if j % 3 == 0:
                for sd in (-1, 1):
                    lx, ly = f.P(0.0, sd * (f.w / 2 + 1.2))
                    m.add(T, lambda bm, lx=lx, ly=ly: props.tube(bm, [(lx, ly, q.p.z), (lx, ly, q.p.z + 2.6)], 0.08, n=4))
                    c.place(hp.cage_lantern(c, j + sd), lx, ly, q.p.z + 2.35, role="visual")
                D.light(c, "lantern", *f.P(0.0, f.w / 2 + 1.2), q.p.z + 2.4)
            if j % 4 == 1 and up > 4.0:
                for sd in (-1, 1):
                    bx, by = f.P(0.0, sd * (f.w / 2 + 1.35))
                    cols = ("awning_red", "banner_teal", "awning_sun", "banner_red", "awning_green", "awning_rose")
                    cloth(m, cols[(j + sd) % len(cols)], [(bx - f.tx * 0.9, by - f.ty * 0.9, q.p.z + 0.9), (bx + f.tx * 0.9, by + f.ty * 0.9, q.p.z + 0.9),
                                                          (bx + f.tx * 0.8, by + f.ty * 0.8, q.p.z + 0.9 - min(5.5, up - 1.0)),
                                                          (bx, by, q.p.z + 0.4 - min(5.5, up - 1.0)),
                                                          (bx - f.tx * 0.8, by - f.ty * 0.8, q.p.z + 0.9 - min(5.5, up - 1.0))])
        s += 4.0
        j += 1
    # The gate where the road comes out of the rock onto the Gallery: the market's name
    # each way, guards either side.
    if first is not None:
        f = Frame(c.at(first + 6.0))
        _gate(m, f, "sign_nightbazaar", f.z, f.w / 2 + 1.8)
        for sd in (-1, 1):
            D.person(c, *f.P(2.0, sd * (f.w / 2 + 0.9)), f.z, "guard", f.x, f.y)
            D.light(c, "torch", *f.P(-0.8, sd * (f.w / 2 + 1.8)), f.z + 4.0)
    # The lookout tower in the hairpin: four legs from the floor, a platform over the
    # Gallery's deck, a beacon burning on it, a crane hoisting a net of crates up from the
    # market, lookouts.
    tx = sum(L.ROUTE[L.AT[t]][0] for t in ("pin0", "pin1", "pin2", "pin3")) / 4 + 6.0
    ty = sum(L.ROUTE[L.AT[t]][1] for t in ("pin0", "pin1", "pin2", "pin3")) / 4
    if paint.road_clear(c, tx, ty, 4.5):
        gz = ground(tx, ty)
        top = L.ROUTE[L.AT["pin1"]][2] + 7.0
        for ix in (-1, 1):
            for iy in (-1, 1):
                solid.add(T, lambda bm, ix=ix, iy=iy: props.tube(bm, [(tx + ix * 2.4, ty + iy * 2.4, gz), (tx + ix * 1.7, ty + iy * 1.7, top)], 0.22, n=6))
        for h in (3.0, 7.0, 11.0, top - gz - 0.3):
            for a, b in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
                sc = lerp(2.4, 1.7, h / (top - gz))
                m.add(T, lambda bm, a=a, b=b, h=h, sc=sc: props.tube(bm, [(tx + a[0] * sc, ty + a[1] * sc, gz + h), (tx + b[0] * sc, ty + b[1] * sc, gz + h)],
                                                                     0.1, n=4))
        m.add(("plank_deck", "wall"), lambda bm: cuboid(bm, (tx, ty, top), (4.6, 4.6, 0.25)))
        cone(c, "Lookout Beacon", tx, ty, 0.9, top + 0.1, 1.2, ("iron", "wall"), segs=8, role="visual")
        D.light(c, "campfire", tx, ty, top + 1.3)
        D.light(c, "glow", tx, ty, top + 2.5)
        for i in range(2):
            D.person(c, tx + 1.4 * (1 - 2 * i), ty + 1.2, top + 0.13, "guard", tx + 10.0, ty)
        jx, jy = tx + 9.0, ty - 2.0
        m.add(T, lambda bm: props.tube(bm, [(tx + 1.6, ty, top + 0.5), (jx, jy, top + 3.0)], 0.12, n=5))
        m.add(("rope_rail", "wall"), lambda bm: props.tube(bm, [(jx, jy, top + 3.0), (jx, jy, gz + 4.0)], 0.03, n=3))
        c.place(gp.crate_stack(c, 2), jx, jy, gz + 2.6, role="visual")
        taken.add(tx, ty, 4.0)
    m.build(c, "Gallery Scaffold", coll="Props", role="visual")
    solid.build(c, "Gallery Legs", coll="Props", role="both")
    return first


# ------------------------------------------------------------------ the lanes


def beast_frames(step=6.0):
    """Frames along the Beast Market's lane (x, y, z, tangent, right)."""
    pts = BEAST_MARKET
    out = []
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(math.dist(a[:2], b[:2]) / step))
        L_ = math.dist(a[:2], b[:2]) or 1.0
        tx, ty = (b[0] - a[0]) / L_, (b[1] - a[1]) / L_
        for i in range(n):
            t = i / n
            out.append((lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t), tx, ty, ty, -tx))
    return out


def beast_clear(x, y, r):
    """Clear of the Beast Market's lane (half its road and shoulders, and r more)?"""
    best = 1e9
    for a, b in zip(BEAST_MARKET, BEAST_MARKET[1:]):
        d, _ = L._seg(x, y, a, b)
        best = min(best, d)
    return best > 6.4 + r


def spice_stall(m, solid, x, y, z, rot, k, over):
    """A spice merchant's stall, its counter to the road: sacks of spices heaped in every
    colour, strings of chillies, brass scales, a striped awning reaching out over the road's
    edge (`over` metres)."""
    def P(lx, ly, zz=0.0):
        px, py = local(x, y, rot, lx, ly)
        return px, py, z + zz

    cx, cy, _ = P(0, 0)
    solid.add(("barrel_wood", "wall"), lambda bm: cuboid(bm, (cx, cy, z + 0.5), (4.2, 1.0, 1.0), rot))
    tx, ty, _ = P(0, 0)
    m.add(("plank_deck", "wall"), lambda bm: cuboid(bm, (tx, ty, z + 1.05), (4.4, 1.2, 0.1), rot))
    cols = ("awning_sun", "awning_red", "ember_gold", "lantern_amber", "em_canvas_green", "gulch_sand", "brick", "tribal_paint")
    for i in range(5):
        lx = -1.7 + i * 0.85
        bx, by, _ = P(lx, 0.0)
        mat = cols[(k * 3 + i) % len(cols)]
        m.add(("canvas_sun", "wall"), lambda bm, bx=bx, by=by: props.tube(bm, [(bx, by, z + 1.1), (bx, by, z + 1.42)], 0.34, n=8))
        m.add((mat, "wall"), lambda bm, bx=bx, by=by: props.blob(bm, (bx, by, z + 1.45), 0.3, sz=0.55, subdiv=1))
    for sd in (-1, 1):
        a = P(sd * 2.2, 1.0)
        m.add(W, lambda bm, a=a: props.tube(bm, [(a[0], a[1], z), (a[0], a[1], z + 3.6)], 0.07, n=4))
        b = P(sd * 2.2, -over)
        m.add(W, lambda bm, b=b: props.tube(bm, [(b[0], b[1], z + 2.7), (b[0], b[1], z + 3.3)], 0.05, n=4))
    awn = ("awning_red", "awning_sun", "awning_teal", "awning_rose", "awning_green", "sdp_awning")[k % 6]
    p = [P(-2.4, 1.2, 3.7), P(2.4, 1.2, 3.7), P(2.4, -over, 3.15), P(-2.4, -over, 3.15)]
    cloth(m, awn, p)
    # (strings of chillies and garlic hung off the awning's edge)
    for i in range(4):
        hx, hy, _ = P(-1.8 + i * 1.2, -over + 0.2)
        mat = ("lantern_red", "party_white")[i % 2]
        for b in range(4):
            m.add((mat, "wall"), lambda bm, hx=hx, hy=hy, b=b: props.blob(bm, (hx, hy, z + 3.0 - b * 0.22), 0.08, sz=1.4, subdiv=0))
    return P(0.0, 1.2)[:2], P(0.0, -1.4)[:2]


def cage(m, solid, x, y, z, rot, w, d, h, k, hidden=None):
    """A beast's cage: a plank floor, iron bars all round, a roof, a lamp; what's in it is
    the caller's (birds, dragonets, a croc, eggs)."""
    def P(lx, ly):
        return local(x, y, rot, lx, ly)

    cx, cy = P(0, 0)
    solid.add(("plank_deck", "wall"), lambda bm: cuboid(bm, (cx, cy, z + 0.2), (w, d, 0.4), rot))
    m.add(("keep_iron", "wall"), lambda bm: cuboid(bm, (cx, cy, z + h + 0.1), (w + 0.2, d + 0.2, 0.18), rot))
    per = 2 * (w + d)
    n = int(per / 0.32)
    for i in range(n):
        t = i * per / n
        if t < w:
            lx, ly = -w / 2 + t, -d / 2
        elif t < w + d:
            lx, ly = w / 2, -d / 2 + (t - w)
        elif t < 2 * w + d:
            lx, ly = w / 2 - (t - w - d), d / 2
        else:
            lx, ly = -w / 2, d / 2 - (t - 2 * w - d)
        bx, by = P(lx, ly)
        m.add(("keep_iron", "wall"), lambda bm, bx=bx, by=by: props.tube(bm, [(bx, by, z + 0.4), (bx, by, z + h)], 0.035, n=3))
    ring = [P(lx, ly) for lx, ly in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2), (-w / 2, -d / 2))]
    for zz in (z + 0.45, z + h * 0.55):
        m.add(("keep_iron", "wall"), lambda bm, zz=zz: props.tube(bm, [(p[0], p[1], zz) for p in ring], 0.05, n=4))
    # (unseen solid sides, so a kart bumps the cage's bars, not drives in through them)
    (hidden or solid).add(("keep_iron", "wall"), lambda bm: cuboid(bm, (cx, cy, z + 0.4 + (h - 0.4) / 2), (w - 0.1, d - 0.1, h - 0.4), rot))


def lanes(c, ground, taken):
    """Spice Row (the road between the fork and the join) and the Beast Market (the side
    road), each crammed both sides; their gates and signs."""
    m, solid, hidden = Mesh(), Mesh(), Mesh()
    s0 = c.nearest(*L.ROUTE[L.AT["fork"]][:2])[0].s - 6.0
    s1 = c.nearest(*L.ROUTE[L.AT["join"]][:2])[0].s
    k = 0
    smoke = ("#e8b040", "#d8603a", "#a868d8", "#5ab070", "#f0d070", "#d84a6a")
    s = s0 + 3.0
    while s < s1 - 3.0:
        f = Frame(c.at(s))
        for sd in (-1, 1):
            v = sd * (f.w / 2 + 2.6)
            x, y = f.P(0.0, v)
            if not beast_clear(x, y, 2.4) or not taken.clear(x, y, 2.0):
                continue
            z = ground(x, y)
            rot = facing(-f.rx * sd, -f.ry * sd)
            back, front = spice_stall(m, solid, x, y, z, rot, k, over=2.1)
            taken.add(x, y, 2.6)
            D.person(c, back[0], back[1], z, "merchant", f.x, f.y)
            for j in range(2 + k % 2):
                px, py = f.P((j - 1) * 1.2, v - sd * 1.6)
                D.person(c, px, py, f.z, ("queue", "huddle", "wave")[(j + k) % 3], x, y)
            if k % 2 == 0:
                g = c.game(x, y, z + 1.6)
                c.entity("mist", x=round(g[0], 1), y=round(g[1], 1), z=round(g[2], 1), radius=4.5, rate=1.6, color=smoke[k % len(smoke)])
            if k % 5 == 3:
                D.light(c, "chimney", x, y, z + 2.2)
            k += 1
        s += 5.6
    # (the fire-breathers, on their boxes either side the row's middle)
    for sd, frac in ((-1, 0.35), (1, 0.7)):
        f = Frame(c.at(lerp(s0, s1, frac)))
        x, y = f.P(1.8, sd * (f.w / 2 + 1.4))
        solid.add(("barrel_wood", "wall"), lambda bm, x=x, y=y, f=f: cuboid(bm, (x, y, f.z + 0.35), (1.2, 1.2, 0.7), facing(f.tx, f.ty)))
        D.person(c, x, y, f.z + 0.7, "cheer", f.x, f.y)
        D.light(c, "torch", x - f.rx * sd * 0.6, y - f.ry * sd * 0.6, f.z + 2.4)
        g = c.game(x - f.rx * sd * 1.6, y - f.ry * sd * 1.6, f.z + 2.6)
        c.entity("mist", x=round(g[0], 1), y=round(g[1], 1), z=round(g[2], 1), radius=1.6, rate=6.0, color="#ff8a30")
        D.light(c, "glow", x, y, f.z + 3.0)
        for i in range(5):
            a = i * 0.5 - 1.0
            px, py = x + math.cos(a + math.atan2(-f.ry * sd, -f.rx * sd)) * 3.0, y + math.sin(a + math.atan2(-f.ry * sd, -f.rx * sd)) * 3.0
            if beast_clear(px, py, 0.5) and paint.road_clear(c, px, py, 0.2):
                D.person(c, px, py, ground(px, py), "cheer", x, y)
    # Spice Row's gates (at the fork and the join), lantern strings across it.
    for s_g, sid in ((s0 + 22.0, "sign_spicerow"), (s1 - 14.0, "sign_spicerow")):
        f = Frame(c.at(s_g))
        if all(beast_clear(*f.P(0.0, sd * (f.w / 2 + 1.5)), 1.0) for sd in (-1, 1)):
            _gate(m, f, sid, f.z, f.w / 2 + 1.5)
    s = s0 + 8.0
    j = 0
    while s < s1 - 6.0:
        f = Frame(c.at(s))
        a = f.P(0.0, -(f.w / 2 + 2.2)) + (f.z + 6.2,)
        b = f.P(0.0, f.w / 2 + 2.2) + (f.z + 6.2,)
        for p in (a, b):
            m.add(W, lambda bm, p=p: props.tube(bm, [(p[0], p[1], f.z - 0.3), (p[0], p[1], p[2] + 0.2)], 0.09, n=4))
        D.lantern_line(c, "Spice String %d" % j, a, b, sag=1.1)
        s += 11.0
        j += 1
    # The Beast Market: cages and pens along both sides of its lane, the auctioneer's
    # block at its bend, a gate with its sign at each end.
    frames = beast_frames(6.0)
    n_cage = 0
    for i, (x0, y0, z0, tx, ty, rx, ry) in enumerate(frames[1:-1]):
        for sd in (-1, 1):
            x, y = x0 + rx * sd * 9.0, y0 + ry * sd * 9.0
            if not paint.road_clear(c, x, y, 3.0) or not beast_clear(x, y, 1.0) or not taken.clear(x, y, 2.4):
                continue
            z = ground(x, y)
            rot = facing(-rx * sd, -ry * sd)
            kind = (i * 2 + (sd > 0)) % 5
            w, d, h = (3.4, 2.4, 2.6) if kind != 4 else (4.4, 3.0, 1.2)
            cage(m, solid, x, y, z, rot, w, d, h, i, hidden)
            g = c.game(x, y, z + 1.4)
            if kind == 0:
                c.entity("birds", color=("#e8483a", "#3ac0e8", "#f2c64a")[i % 3], x=round(g[0], 1), y=round(g[1], 1), z=round(g[2], 1), radius=0.8,
                         count=4, speed=0.9, seed=i + 40)
            elif kind == 1:
                c.entity("little_dragons", x=round(g[0], 1), y=round(g[1], 1), z=round(g[2], 1), radius=0.9, count=2, speed=0.6, seed=i + 7)
            elif kind == 2:
                c.place(sw.croc(c), x, y, z + 0.4, rot=rot + 1.2, scale=0.5, role="visual")
            elif kind == 3:
                for e in range(5):
                    ex, ey = local(x, y, rot, -1.0 + e * 0.5, 0.2 * (e % 2))
                    D.egg(c, "Beast Egg %d %d" % (i, e), ex, ey, z + 0.4, 0.28 + 0.06 * (e % 3), ("party_white", "lush_grass", "awning_sun")[e % 3])
            else:
                c.place(sw.croc(c), x, y, z + 0.4, rot=rot, scale=0.65, role="visual")
            D.light(c, "lantern", x, y, z + h + 0.6)
            mx, my = local(x, y, rot, 1.2, -d / 2 - 1.0)
            D.person(c, mx, my, z, "merchant" if kind % 2 else "huddle", x0, y0)
            taken.add(x, y, 2.8)
            n_cage += 1
    # (the auctioneer's block, at the lane's bend, the bidders round it, a dragonet's dome
    # cage hung over it)
    bx, by = BEAST_MARKET[3][0] + 9.0, BEAST_MARKET[3][1] + 6.0
    if beast_clear(bx, by, 3.0) and paint.road_clear(c, bx, by, 4.0):
        z = ground(bx, by)
        solid.add(("door_wood", "wall"), lambda bm: cuboid(bm, (bx, by, z + 0.6), (3.0, 2.2, 1.2), 0.4))
        D.person(c, bx, by, z + 1.2, "merchant", BEAST_MARKET[3][0], BEAST_MARKET[3][1])
        for i in range(9):
            a = math.atan2(BEAST_MARKET[3][1] - by, BEAST_MARKET[3][0] - bx) + (i - 4) * 0.28
            px, py = bx + 4.6 * math.cos(a), by + 4.6 * math.sin(a)
            if beast_clear(px, py, 0.4):
                D.person(c, px, py, ground(px, py), ("cheer", "queue", "wave")[i % 3], bx, by)
        g = c.game(bx, by, z + 6.0)
        c.entity("little_dragons", x=round(g[0], 1), y=round(g[1], 1), z=round(g[2], 1), radius=1.3, count=3, speed=0.5, seed=91)
        ring = [(bx + 2.0 * math.cos(a), by + 2.0 * math.sin(a), z + 4.6) for a in [i * math.tau / 16 for i in range(17)]]
        m.add(("keep_iron", "wall"), lambda bm: props.tube(bm, ring, 0.05, n=4))
        for i in range(10):
            a = i * math.tau / 10
            m.add(("keep_iron", "wall"), lambda bm, a=a: props.tube(bm, [(bx + 2.0 * math.cos(a), by + 2.0 * math.sin(a), z + 4.6),
                                                                         (bx + 1.0 * math.cos(a), by + 1.0 * math.sin(a), z + 7.3), (bx, by, z + 7.6)], 0.03, n=3))
        m.add(("keep_iron", "wall"), lambda bm: props.tube(bm, [(bx, by, z + 7.6), (bx, by, BAZ_Z + 30.0)], 0.06, n=4))
        D.light(c, "glow", bx, by, z + 3.0)
        taken.add(bx, by, 5.0)
    for (x0, y0, z0, tx, ty, rx, ry), dirn in ((frames[3], -1), (frames[-4], 1)):
        if not all(paint.road_clear(c, x0 + rx * sd * 6.6, y0 + ry * sd * 6.6, 1.2) for sd in (-1, 1)):
            continue
        class F:
            pass
        f = F()
        f.x, f.y, f.z, f.tx, f.ty, f.rx, f.ry, f.w = x0, y0, z0, tx, ty, rx, ry, 10.0
        f.P = lambda u, v, f=f: (f.x + f.tx * u + f.rx * v, f.y + f.ty * u + f.ry * v)
        _gate(m, f, "sign_beastmarket", z0, 6.6)
    for j, fr in enumerate(frames[2:-2:3]):
        px, py = fr[0] - fr[5] * 8.0, fr[1] - fr[6] * 8.0
        if j < 2 and taken.clear(px, py, 1.0):
            D.talkers(c, px, py, fr[2], 3, "beasts", r=3.0)
    m.build(c, "Market Lanes", coll="Props", role="visual")
    solid.build(c, "Market Lane Stalls", coll="Props", role="both")
    hidden.build(c, "Beast Market Cage Sides", coll="Collision", role="collision")
    print("lanes: %d spice stalls, %d cages" % (k, n_cage))
