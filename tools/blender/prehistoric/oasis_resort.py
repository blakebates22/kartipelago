# Oasis Haven's architecture and life (see oasis_scenery.py): the start gate and its
# plaza, the promenade, the waterfront market, the Grand Arched Bridge and the causeway,
# the pavilion island, the terraces and their gardens, the palace and its gateway, the
# beach hotel over the canal passage, the beach, the resort round the shore, the docks,
# the gardens and the desert's edge, and the guests.
# SPDX-License-Identifier: MIT

import math

import oasis_props as op
import course_kit as kit
from course_kit import Vector, lerp, rnd
from oasis_scenery import COLL, Mesh, arch_gate, block, clear, great_dome, road_rot, tower
from props import cuboid, loft, ring


def pieces_of(c, kind):
    return [ob for ob in c.pieces if ob.name.endswith(" " + kind)]


def span_of(ob, length):
    s0, s1 = ob["kp_from"], ob["kp_to"]
    if s1 < s0:
        s1 += length
    return s0, s1


def side_spot(c, s, off):
    q = c.at(s)
    return q, q.side(off)


# ------------------------------------------------------------------ the start


def start_plaza(c, oh, sc):
    m = Mesh()
    q = c.at(14.0)
    arch_gate(m, q, q.w + 5.0, 13.0, depth=4.5)
    # Banners hung from the gate, and a checkered board on top.
    rot = road_rot(q)
    for o in (-q.w * 0.3, q.w * 0.3):
        p = q.side(o)
        m.add(("oasis_banner", "wall"), lambda bm, p=p: cuboid(bm, (p.x, p.y, q.p.z + 9.0), (0.1, 3.0, 4.6), rot + math.pi / 2))
    p = q.side(0)
    m.add(("start_checker", "wall"), lambda bm: cuboid(bm, (p.x, p.y, q.p.z + 16.2), (0.2, 12.0, 1.8), rot + math.pi / 2))
    # Shops and cafés along the south side of the plaza, the lake to the north.
    for k, s in enumerate((-70.0, -40.0, -8.0, 30.0, 62.0)):
        qq = c.at(s)
        pp = qq.side(-(qq.w / 2 + 22.0))
        z = sc.ground(pp.x, pp.y)
        top = block(m, pp.x, pp.y, 22.0, 14.0, z, 9.0 + 4.5 * (k % 2), rot=road_rot(qq), style=("white", "cream", "rose")[k % 3])
        sc.footprints.append((pp.x, pp.y, 13.0))
        if k == 2:
            great_dome(m, pp.x, pp.y, top, 6.0, mat="dome_teal", drum=2.5)
        elif k % 2:
            tower(m, pp.x + 8.0, pp.y, top, 9.0, r=1.8)
    m.build(c, "Start Gate", COLL, "both")
    # Two fountains either side of the road just past the gate.
    for side in (-1, 1):
        qq = c.at(40.0)
        pp = qq.side(side * (qq.w / 2 + 11.0))
        z = sc.ground(pp.x, pp.y)
        sc.put(op.fountain(c, 0, 4.0), pp.x, pp.y, z, coll="Props", role="both")
        sc.fountains.append((pp.x, pp.y, z + 2.4 * 4.0 * 0.95, 6.0, 6, 4.0))
    # Banner poles and lanterns down the straight, cafés and palms behind.
    for s in (-55.0, -30.0, -5.0, 25.0, 55.0, 80.0):
        qq = c.at(s)
        for side in (-1, 1):
            pp = qq.side(side * (qq.w / 2 + 2.6))
            sc.put(op.banner_pole(c), pp.x, pp.y, qq.p.z - 0.2, rot=road_rot(qq) + (math.pi if side < 0 else 0.0), role="both")
    for k, s in enumerate((-60.0, -20.0, 15.0, 70.0)):
        qq = c.at(s)
        pp = qq.side(-(qq.w / 2 + 9.0))
        sc.put(op.cafe_table(c, k), pp.x, pp.y, sc.ground(pp.x, pp.y), role="both")
        sc.guests.append((pp.x + 2.0, pp.y, sc.ground(pp.x + 2, pp.y), 0.0, "chill"))


# ------------------------------------------------------------------ along the road


def road_dressing(c, oh, sc):
    """Lanterns and banners along the balustrades, palms and planters, red chevrons on the
    outside of the bends."""
    L = c.length
    s = 0.0
    k = 0
    while s < L:
        q = c.at(s)
        seg = oh.seg_of(s)
        wet_l = oh.lake_d(*tuple(q.side(-(q.w / 2 + 4.0)))[:2]) > 0
        wet_r = oh.lake_d(*tuple(q.side(q.w / 2 + 4.0))[:2]) > 0
        for side, wet in ((-1, wet_l), (1, wet_r)):
            p = q.side(side * (q.w / 2 + 1.6))
            if wet or seg in (0, 23, 4, 5, 6):
                continue
            if k % 2 == 0:
                sc.put(op.lantern_post(c), p.x, p.y, q.p.z - 0.1, role="both")
            elif seg not in (12, 13, 14):
                sc.put(op.planter(c, k % 2), p.x, p.y, q.p.z - 0.1, role="both")
        s += 16.0
        k += 1
    # Palms along the land side of the promenade and the descent.
    for s0, s1 in ((oh.SEG[1] + 20, oh.SEG[4]), (oh.SEG[17] + 30, oh.SEG[19]), (oh.SEG[22], oh.SEG[23])):
        s = s0
        while s < s1:
            q = c.at(s)
            for side in (-1, 1):
                p = q.side(side * (q.w / 2 + 6.0 + 2.0 * rnd(s)))
                if oh.lake_d(p.x, p.y) > -3 or not clear(c, p.x, p.y, 4.0):
                    continue
                sc.put(op.palm(c, int(s) % 4, 9.0 + 3.0 * rnd(s * 3)), p.x, p.y, sc.ground(p.x, p.y) - 0.2, rot=rnd(s) * math.tau, coll="Plants", role="both")
            s += 22.0
    # Red chevrons on the outside of the bends.
    S = oh.SEG
    for seg, frac in ((3, 0.6), (4, 0.5), (5, 0.5), (7, 0.4), (7, 0.8), (10, 0.3), (10, 0.7), (12, 0.6), (14, 0.3), (14, 0.7), (17, 0.5), (20, 0.5), (22, 0.5)):
        s = S[seg] + (S.get(seg + 1, c.length) - S[seg]) * frac
        q = c.at(s)
        side = -1 if oh.LAYOUT[seg][0] == "R" else 1
        p = q.side(side * (q.w / 2 + 3.0))
        if oh.lake_d(p.x, p.y) > -1:
            p = q.side(side * (q.w / 2 + 1.2))
        back = c.at(s - 30.0).p
        n = Vector((back.x - p.x, back.y - p.y, 0)).normalized()
        sc.put(op.chevron_board(c), p.x, p.y, q.p.z - 0.1, rot=math.atan2(-n.x, n.y), role="both")


# ------------------------------------------------------------------ bridges


def arches_under(c, oh, m, s0, s1, every, bed, pier=(5.0, 8.0), rise=0.42, mat=("oasis_stone", "wall")):
    """Stone piers down to the lake bed and arched soffits between them, under the road
    from s0 to s1; a blue tiled band along the deck's edge."""
    L = s1 - s0
    n = max(1, int(round(L / every)))
    for k in range(n + 1):
        q = c.at(s0 + L * k / n)
        top = q.p.z - 2.5
        m.add(mat, lambda bm, q=q, top=top: cuboid(bm, (q.p.x, q.p.y, (top + bed) / 2), (pier[0], q.w + 2.0, top - bed), road_rot(q)))
        # A cutwater at the waterline.
        m.add(mat, lambda bm, q=q: cuboid(bm, (q.p.x, q.p.y, 0.6), (pier[0] + 2.0, q.w + 3.0, 2.0), road_rot(q)))
    for k in range(n):
        a, b = s0 + L * k / n, s0 + L * (k + 1) / n

        def arc(bm, a=a, b=b):
            rs = []
            for j in range(11):
                t = j / 10
                q = c.at(a + (b - a) * t)
                z = q.p.z - 2.5 - (1 - math.sin(math.pi * t)) * (b - a) * rise
                half = q.w / 2 + 0.9
                rs.append([bm.verts.new(q.p + q.r * o + Vector((0, 0, z - q.p.z + dz))) for o, dz in ((-half, 0), (half, 0), (half, 1.0), (-half, 1.0))])
            loft(bm, rs, cap_top=False)

        m.add(mat, arc)
    # Spandrel walls each side of the arches.
    s = s0
    while s < s1:
        q = c.at(s)
        for side in (-1, 1):
            p = q.side(side * (q.w / 2 + 0.95))
            m.add(("tile_border", "wall"), lambda bm, p=p, q=q: cuboid(bm, (p.x, p.y, q.p.z - 1.3), (2.05, 0.25, 0.7), road_rot(q)))
        s += 2.0


def bridges(c, oh, sc):
    m = Mesh()
    for ob in pieces_of(c, "bridge"):
        s0, s1 = span_of(ob, c.length)
        arches_under(c, oh, m, s0, s1, 18.0, -8.0)
        # Banner poles and flower urns along the parapets.
        s = s0 + 6
        k = 0
        while s < s1 - 4:
            q = c.at(s)
            for side in (-1, 1):
                p = q.side(side * (q.w / 2 + 1.4))
                if k % 2 == 0:
                    sc.put(op.banner_pole(c), p.x, p.y, q.p.z - 0.2, rot=road_rot(q) + (math.pi if side < 0 else 0), role="both")
                else:
                    sc.put(op.planter(c, 1), p.x, p.y, q.p.z - 0.2, role="both")
            s += 12.0
            k += 1
    for ob in pieces_of(c, "causeway"):
        s0, s1 = span_of(ob, c.length)
        arches_under(c, oh, m, s0, s1, 12.0, -8.0, pier=(3.5, 6.0), rise=0.35)
        s = s0 + 6
        while s < s1 - 4:
            q = c.at(s)
            for side in (-1, 1):
                p = q.side(side * (q.w / 2 + 1.4))
                sc.put(op.lantern_post(c), p.x, p.y, q.p.z - 0.2, role="both")
            s += 14.0
    for ob in pieces_of(c, "canalbridge"):
        s0, s1 = span_of(ob, c.length)
        arches_under(c, oh, m, s0 - 2, s1 + 2, max(6.0, s1 - s0 + 4), -4.0, pier=(2.5, 4.0), rise=0.5)
    m.build(c, "Arches", COLL, "both")


# ------------------------------------------------------------------ the pavilion


def pavilion(c, oh, sc):
    """The blue-domed pavilion on its island: a ring of slender columns on a stepped
    plinth, a drum and a great dome with a gold finial, a fountain inside; gardens round
    it inside the road's ring, and the island's sea wall."""
    px, py = oh.PAVILION
    z = oh.Z_ISLAND
    m = Mesh()
    for k, (r, h) in enumerate(((20.0, 0.5), (18.0, 1.0), (16.5, 1.5))):
        m.add(("oasis_stone", "wall"), lambda bm, r=r, h=h: op._cyl(bm, px, py, z - 1.0, z + h, r, n=24))
    m.add(("tile_border", "wall"), lambda bm: op._cyl(bm, px, py, z + 1.5, z + 1.6, 16.6, n=24))
    for k in range(12):
        a = k * math.tau / 12
        m.add(("oasis_stone", "wall"), lambda bm, a=a: op.column(bm, px + 14.0 * math.cos(a), py + 14.0 * math.sin(a), z + 1.5, z + 12.0, 0.75))
    m.add(("oasis_stone", "wall"), lambda bm: op._cyl(bm, px, py, z + 12.0, z + 13.6, 15.4, n=24))
    m.add(("tile_border", "wall"), lambda bm: op._cyl(bm, px, py, z + 13.6, z + 14.3, 15.6, n=24))
    m.add(("gold_leaf", "wall"), lambda bm: op._cyl(bm, px, py, z + 14.3, z + 14.7, 15.8, n=24))
    great_dome(m, px, py, z + 14.7, 13.0, mat="dome_blue", drum=3.5, onion=0.25)
    # Little domed turrets round the drum.
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        x, y = px + 15.0 * math.cos(a), py + 15.0 * math.sin(a)
        m.add(("oasis_stone", "wall"), lambda bm, x=x, y=y: op._cyl(bm, x, y, z + 14.7, z + 17.0, 1.2, n=8))
        m.add(("dome_blue", "wall"), lambda bm, x=x, y=y: op.dome(bm, x, y, z + 17.0, 1.3, h=2.0, n=8, rings=3, onion=0.7))
        m.add(("gold_leaf", "wall"), lambda bm, x=x, y=y: op.finial(bm, x, y, z + 19.0, 0.5))
    # The island's sea wall, open where the road crosses it.
    R = oh.ISLAND_R
    n = 96
    for k in range(n):
        a0, a1 = k * math.tau / n, (k + 1) * math.tau / n
        mx, my = px + R * math.cos((a0 + a1) / 2), py + R * math.sin((a0 + a1) / 2)
        if not clear(c, mx, my, 3.0):
            continue
        from oasis_scenery import wall_band

        p0 = (px + R * math.cos(a0), py + R * math.sin(a0))
        p1 = (px + R * math.cos(a1), py + R * math.sin(a1))
        wall_band(m, ("oasis_stone", "wall"), p1, p0, -3.0, z + 0.1, 4.0)
        q0 = (px + (R - 0.6) * math.cos(a0), py + (R - 0.6) * math.sin(a0))
        q1 = (px + (R - 0.6) * math.cos(a1), py + (R - 0.6) * math.sin(a1))
        wall_band(m, ("balustrade", "wall"), q0, q1, z + 0.1, z + 1.2, 3.0)
        wall_band(m, ("balustrade", "wall"), q1, q0, z + 0.1, z + 1.2, 3.0)
    m.build(c, "Pavilion", COLL, "both")
    sc.put(op.fountain(c, 2, 3.0), px, py, z + 1.5, coll="Props", role="both")
    sc.fountains.append((px, py, z + 1.5 + 2.4 * 3.0 * 0.95, 5.0, 8, 3.2))
    # Gardens between the pavilion and the road: palms, flower mounds, little fountains.
    for k in range(10):
        a = k * math.tau / 10 + 0.3
        r = 28.0 + 4.0 * (k % 2)
        x, y = px + r * math.cos(a), py + r * math.sin(a)
        if not clear(c, x, y, 3.0):
            continue
        if k % 2:
            sc.put(op.palm(c, k % 4, 10.0 + 2 * (k % 3)), x, y, z - 0.2, rot=a, coll="Gardens", role="both")
        else:
            sc.put(op.bougainvillea(c, k % 2), x, y, z - 0.1, rot=a, coll="Gardens")
    # Palms and flowers round the outer rim too.
    for k in range(24):
        a = k * math.tau / 24
        r = R - 7.0
        x, y = px + r * math.cos(a), py + r * math.sin(a)
        if not clear(c, x, y, 3.0):
            continue
        sc.put(op.palm(c, k % 4, 9.0 + 3 * rnd(k)) if k % 3 else op.bougainvillea(c, 1), x, y, z - 0.2, rot=a, coll="Gardens", role="visual")
    for k in range(6):
        a = k * math.tau / 6 + 0.5
        x, y = px + 23.0 * math.cos(a), py + 23.0 * math.sin(a)
        sc.guests.append((x, y, z, a + math.pi, ("wave", "sway", "bounce")[k % 3]))


# ------------------------------------------------------------------ the market


def market(c, oh, sc):
    """The waterfront market: halls with arcades along the inland side of the street,
    stalls under striped awnings between them and the road, cafés on the waterfront
    terraces on the lake side, docks and boats along the canals."""
    S = oh.SEG
    m = Mesh()
    s = S[4] - 10.0
    k = 0
    while s < S[7] + 30.0:
        q = c.at(s)
        if any(oh.canal_d(*tuple(q.side(o))[:2]) > -6 for o in (12, 20, 28, 36)):
            s += 8.0
            continue
        p = q.side(q.w / 2 + 19.0)
        z = sc.ground(p.x, p.y)
        w = 16.0 + 4.0 * (k % 3)
        top = block(m, p.x, p.y, w, 18.0, z, 9.0 + 4.5 * (k % 2), rot=road_rot(q), style=("cream", "rose", "white", "ochre")[k % 4])
        sc.footprints.append((p.x, p.y, math.hypot(w, 18.0) / 2))
        if k % 3 == 0:
            tower(m, p.x, p.y + 0.0, top, 7.0, r=2.0, dome_mat="dome_teal" if k % 2 else "dome_blue")
        elif k % 3 == 1:
            great_dome(m, p.x, p.y, top, 4.5, mat="dome_blue" if k % 2 else "dome_teal", drum=1.6, onion=0.5)
        # Stalls in front.
        for j in (-1, 1):
            sp = q.side(q.w / 2 + 5.0) + q.t * (j * 4.5)
            sc.put(op.market_stall(c, k + j + 2), sp.x, sp.y, sc.ground(sp.x, sp.y), rot=road_rot(q) + math.pi, coll="Market", role="both")
        sc.guests.append((p.x - q.r.x * 12, p.y - q.r.y * 12, sc.ground(p.x, p.y), road_rot(q) + math.pi / 2, ("bounce", "wave", "chill", "sway")[k % 4]))
        s += w + 6.0
        k += 1
    # Waterfront terraces on the lake side: cafés and goods.
    s = S[4]
    k = 0
    while s < S[7]:
        q = c.at(s)
        p = q.side(-(q.w / 2 + 8.0))
        if oh.lake_d(p.x, p.y) < -1 and clear(c, p.x, p.y, 3.0):
            sc.put(op.cafe_table(c, k), p.x, p.y, sc.ground(p.x, p.y), coll="Market", role="both")
            p2 = q.side(-(q.w / 2 + 14.0))
            if oh.lake_d(p2.x, p2.y) < -1:
                sc.put(op.crates(c, k % 2), p2.x, p2.y, sc.ground(p2.x, p2.y), rot=k, coll="Market", role="both")
        s += 14.0
        k += 1
    m.build(c, "Market Halls", COLL, "both")
    # The canals' docks and moored boats, and a fountain where each canal ends.
    for j, (pts, hw) in enumerate(oh.CANALS):
        (ax, ay), (bx, by) = pts[1], pts[2]
        L = math.hypot(bx - ax, by - ay)
        ux, uy = (bx - ax) / L, (by - ay) / L
        for t in (0.35, 0.7):
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            sc.put(op.moored_boat(c, j * 2 + int(t * 3)), x + uy * 1.0, y - ux * 1.0, 0.0, rot=math.atan2(uy, ux), coll="Market")
        ex, ey = bx + ux * 10.0, by + uy * 10.0
        if clear(c, ex, ey, 6.0):
            z = sc.ground(ex, ey)
            sc.put(op.fountain(c, 3, 3.0), ex, ey, z, coll="Market", role="both")
            sc.fountains.append((ex, ey, z + 2.4 * 3.0 * 0.95, 5.0, 6, 3.0))
            sc.put(op.kiosk(c, j), ex + uy * 9.0, ey - ux * 9.0, z, rot=0.3, coll="Market", role="both")


# ------------------------------------------------------------------ terraces and palace


def terraces(c, oh, sc):
    """The retaining walls of the terraces (cream stone, a balustrade along the top),
    open where the road climbs past them and where the cascades fall; gardens on each."""
    from oasis_scenery import wall_band

    m = Mesh()
    levels = (oh.Z_SHORE + 1.0, oh.Z_T1, oh.Z_T2, oh.Z_PALACE)
    for k, y in enumerate(oh.TERRACE_Y):
        lo, hi = levels[k], levels[k + 1]
        x = -175.0
        while x < 262.0:
            x1 = x + 4.0
            if any(abs((x + x1) / 2 - fx) < w for fx, w in ((160.0, 18.0), (-128.0, 13.0), (186.0, 6.0), (-154.0, 6.0), (25.0, 5.0))):
                x = x1
                continue
            mid = ((x + x1) / 2, y + 3.0)
            smp, d = c.nearest(*mid)
            if d < smp.w / 2 + 4.0 and lo - 1 < smp.p.z < hi + 3:
                x = x1
                continue
            lo_here = min(oh.natural((x + x1) / 2, y - 6.0), lo + 0.5)
            # The wall's face: storeys of arcades (a palace of terraces), a tiled band.
            zb = lo_here - 1.0
            wall_band(m, ("oasis_stone", "wall"), (x, y), (x1, y), zb, lo + 0.2, 5.0)
            za = lo + 0.2
            sty = ("oasis_arcade", "arcade_white", "arcade_rose")[k]
            while za < hi - 0.5:
                zz = min(hi - 0.4, za + 5.0)
                wall_band(m, (sty, "wall"), (x, y), (x1, y), za, zz, 10.4, uv0=(x + 175.0) / 10.4)
                za = zz
            wall_band(m, ("tile_border", "wall"), (x, y), (x1, y), hi - 0.4, hi + 0.1, 4.0)
            wall_band(m, ("balustrade", "wall"), (x1, y + 0.6), (x, y + 0.6), hi + 0.1, hi + 1.2, 3.0)
            wall_band(m, ("balustrade", "wall"), (x, y + 0.6), (x1, y + 0.6), hi + 0.1, hi + 1.2, 3.0)
            x = x1
    m.build(c, "Terrace Walls", COLL, "both")
    # Gardens: cypress rows, flower mounds, palms, little kiosks on each terrace.
    for k, (y0, y1, z) in enumerate(((oh.TERRACE_Y[0] + 6, oh.TERRACE_Y[1] - 4, oh.Z_T1), (oh.TERRACE_Y[1] + 6, oh.TERRACE_Y[2] - 4, oh.Z_T2))):
        x = -165.0
        j = 0
        while x < 250.0:
            for y in (y0 + 3.0, y1 - 3.0):
                if clear(c, x, y, 5.0) and abs(x - 160) > 20 and abs(x + 128) > 15 and abs(x - 25) > 8:
                    pick = (j + int(y)) % 4
                    proto = (op.cypress(c, j % 2), op.bougainvillea(c, j % 2), op.palm(c, j % 4, 9.0), op.cypress(c, 1))[pick]
                    sc.put(proto, x, y, z - 0.1, rot=j, coll="Gardens", role="visual")
            x += 11.0
            j += 1
        for x in (-60.0, 95.0, 215.0):
            yy = (y0 + y1) / 2
            if clear(c, x, yy, 8.0):
                sc.put(op.kiosk(c, k + int(x)), x, yy, z - 0.1, rot=0.2, coll="Gardens", role="both")


def palace(c, oh, sc):
    """The palace on its plateau: a great central hall under a vast blue dome, arcaded
    wings stepping forward on each side, towers at every corner, galleries over the
    gardens; and its gateway over the road below."""
    z = oh.Z_PALACE
    m = Mesh()
    cx, cy = 15.0, 478.0
    top = block(m, cx, cy, 90.0, 44.0, z, 28.0, ground=7.0, storey=5.5, style="white")
    great_dome(m, cx, cy, top, 24.0, mat="dome_blue", drum=7.0, onion=0.35)
    for sx in (-1, 1):
        for sy in (-1, 1):
            tower(m, cx + sx * 45.0, cy + sy * 22.0, top - 2.0, 30.0, r=4.0, onion=0.7)
        # Smaller domes on the roof either side of the great one.
        great_dome(m, cx + sx * 30.0, cy, top, 7.0, mat="dome_blue", drum=2.5, onion=0.5)
    for side in (-1, 1):
        wx = cx + side * 80.0
        wt = block(m, wx, cy - 12.0, 54.0, 32.0, z, 20.0, ground=6.0, style="white")
        great_dome(m, wx, cy - 12.0, wt, 12.0, mat="dome_teal" if side > 0 else "dome_blue", drum=3.5, onion=0.5)
        ft = block(m, cx + side * 118.0, cy - 44.0, 26.0, 36.0, z, 15.0, style="cream")
        tower(m, cx + side * 118.0, cy - 58.0, ft, 20.0, r=3.0)
        # A gallery along the front, over the gardens.
        block(m, cx + side * 55.0, cy - 36.0, 30.0, 7.0, z, 7.0, ground=7.0, style="white")
    # The front portico: a tall entrance arch facing the spring.
    block(m, cx, cy - 28.0, 36.0, 10.0, z, 16.0, ground=8.0, style="white")
    great_dome(m, cx, cy - 28.0, z + 17.4, 6.0, mat="dome_teal", drum=1.5, onion=0.6)
    m.build(c, "Palace", COLL, "both")
    # The palace gateway over the road below (a grand arch with towers), banners and
    # lanterns either side, and stairs up to the gardens.
    m = Mesh()
    S = oh.SEG
    q = c.at(S[16] + 28.0)
    arch_gate(m, q, q.w + 6.0, 15.0, depth=6.0)
    rot = road_rot(q)
    for o in (-q.w * 0.3, q.w * 0.3):
        p = q.side(o)
        m.add(("oasis_banner", "wall"), lambda bm, p=p: cuboid(bm, (p.x, p.y, q.p.z + 10.0), (0.1, 3.0, 5.0), rot + math.pi / 2))
    st = q.side(-(q.w / 2 + 14.0))
    for k in range(10):
        m.add(("oasis_stone", "wall"), lambda bm, k=k: cuboid(bm, (st.x, st.y + k * 1.2, q.p.z + k * (z - q.p.z) / 10.0 - 0.5), (12.0, 1.3, 1.2)))
    m.build(c, "Palace Gate", COLL, "both")
    # The palace gardens: cypress avenues, flower beds and palms round the spring.
    for k in range(16):
        a = k * math.tau / 16
        x, y = 15.0 + 26.0 * math.cos(a), 424.0 + 16.0 * math.sin(a)
        sc.put(op.cypress(c, k % 2) if k % 2 else op.palm(c, k % 4, 11.0), x, y, z - 0.1, rot=a, coll="Gardens")
    for x in (-110.0, -80.0, 110.0, 140.0):
        for y in (418.0, 440.0):
            sc.put(op.bougainvillea(c, int(x) % 2), x, y, z - 0.1, coll="Gardens")
    for k in range(5):
        sc.guests.append((15.0 + (k - 2) * 7.0, 444.0, z, math.pi / 2, ("wave", "chill", "sway", "bounce", "wave")[k]))


# ------------------------------------------------------------------ the west shore


def headland(c, oh, sc):
    """The beach hotel over the canal passage (the shortcut runs through its arcade), the
    beach round the headland, and villas up the west ridge."""
    pts = oh.SHORT
    mid = len(pts) // 2
    (ax, ay), (bx, by) = pts[mid - 2], pts[mid + 2]
    z = c.nearest(*pts[mid])[0].p.z
    m = Mesh()
    # The hotel: raised on piers over the passage and its canal, three storeys and towers.
    cx, cy = (ax + bx) / 2 + 6.0, (ay + by) / 2
    length = math.hypot(bx - ax, by - ay)
    rot = math.atan2(by - ay, bx - ax)
    base = z + 8.0
    top = block(m, cx, cy, length, 34.0, base, 13.0, rot=rot, ground=4.5, base=base - 1.2, style="white")
    sc.footprints.append((cx, cy, length / 2 + 6.0))
    tower(m, cx + math.cos(rot) * length / 2, cy + math.sin(rot) * length / 2, top, 10.0, r=2.2, dome_mat="dome_teal")
    great_dome(m, cx, cy, top, 6.5, mat="dome_blue", drum=2.0, onion=0.4)
    # Piers between the passage and the canal, and outside them.
    for t in (0.0, 0.33, 0.66, 1.0):
        px, py = ax + (bx - ax) * t, ay + (by - ay) * t
        for off in (-7.5, 5.5, 18.5):
            x, y = px + off, py
            if off == 5.5 and False:
                continue
            m.add(("oasis_stone", "wall"), lambda bm, x=x, y=y: cuboid(bm, (x, y, (base + z - 3) / 2), (2.4, 2.4, base - z + 3)))
    m.build(c, "Beach Hotel", COLL, "both")
    # Lanterns inside the passage.
    for t in (0.2, 0.5, 0.8):
        x, y = ax + (bx - ax) * t - 5.5, ay + (by - ay) * t
        sc.lamps.append((x, y, z + 4.0))
    # The beach: umbrellas and loungers on the sand round the headland's outer side, and
    # a conga line of guests.
    S = oh.SEG
    s = S[19] + 10
    k = 0
    while s < S[21] + 40:
        q = c.at(s)
        p = q.side(-(q.w / 2 + 8.0))
        if oh.lake_d(p.x, p.y) < -1.5:
            sc.put(op.beach_set(c, k), p.x, p.y, sc.ground(p.x, p.y), rot=road_rot(q), coll="Props", role="both")
        s += 13.0
        k += 1
    q = c.at(S[20] + 50)
    p = q.side(-(q.w / 2 + 10.0))
    gx, gy, gz = c.game(p.x, p.y, sc.ground(p.x, p.y))
    c.entity("conga", x=gx, y=gy, z=gz, radius=4.5, count=6, speed=1.2)


def free(sc, x, y, r):
    return all((x - fx) ** 2 + (y - fy) ** 2 > (r + fr) ** 2 for fx, fy, fr in sc.footprints)


def district(c, oh, sc, m, s0, s1, sides, rows=((22.0, 36.0),), step=24.0, seed=0, heights=(10.0, 24.0), keep_out=()):
    """Buildings lining the road from s0 to s1 on the land side(s): blocks of varied
    size, height, colour and roof (a dome, a tower, a roof garden), facing the road,
    never on the water, a road, a cascade or another building."""
    s = s0
    k = seed
    styles = ("cream", "white", "rose", "cream", "ochre", "white")
    while s < s1:
        q = c.at(s)
        for side in sides:
            for (near, far) in rows:
                off = near + (far - near) * rnd(k * 3.1 + seed)
                w = 14.0 + 12.0 * rnd(k * 1.7 + seed)
                d = 12.0 + 8.0 * rnd(k * 2.3 + seed)
                p = q.side(side * (q.w / 2 + off))
                r = math.hypot(w, d) / 2
                k += 1
                if oh.lake_d(p.x, p.y) > -r - 2.0 or not clear(c, p.x, p.y, r + 2.0) or not free(sc, p.x, p.y, r):
                    continue
                if any(abs(p.x - kx) < kw for kx, kw in keep_out):
                    continue
                g = [sc.ground(p.x + dx, p.y + dy) for dx, dy in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2), (0, 0))]
                if max(g) - min(g) > 6.0:
                    continue
                z = min(g)
                h = heights[0] + (heights[1] - heights[0]) * rnd(k * 5.3 + seed)
                rot = road_rot(q)
                top = block(m, p.x, p.y, w, d, z, h, rot=rot, style=styles[k % len(styles)])
                sc.footprints.append((p.x, p.y, r))
                pick = k % 6
                if pick in (0, 4):
                    great_dome(m, p.x, p.y, top, min(w, d) * 0.36, mat="dome_blue", drum=2.2, onion=0.45)
                elif pick == 5:
                    great_dome(m, p.x - math.cos(rot) * w * 0.2, p.y - math.sin(rot) * w * 0.2, top, min(w, d) * 0.3, mat="dome_blue", drum=1.6, onion=0.6)
                    tower(m, p.x + math.cos(rot) * w * 0.38, p.y + math.sin(rot) * w * 0.38, top, 9.0, r=1.7)
                elif pick == 1:
                    tower(m, p.x + math.cos(rot) * w * 0.35, p.y + math.sin(rot) * w * 0.35, top, 8.0 + 4.0 * rnd(k), r=1.9,
                          dome_mat="dome_teal" if k % 2 else "dome_blue")
                elif pick == 2:
                    great_dome(m, p.x, p.y, top, min(w, d) * 0.32, mat="dome_teal", drum=1.6, onion=0.7)
                elif pick == 3:
                    # A roof terrace: an awning over it and a palm in a pot.
                    m.add((op.AWNINGS[k % 4], "wall"), lambda bm, p=p, top=top, rot=rot: cuboid(bm, (p.x, p.y, top + 2.6), (w * 0.5, d * 0.5, 0.12), rot))
                    sc.put(op.palm(c, k % 4, 6.0), p.x + 2.0, p.y + 2.0, top - 1.4, coll="Plants")
        s += step


def resort(c, oh, sc):
    """The resort all round the shore: hotels, villas and arcades lining the roads on the
    land side, more behind them, up the west ridge and along the terraces; docks on the
    lake."""
    m = Mesh()
    S = oh.SEG
    cascades = ((160.0, 30.0), (-128.0, 24.0), (25.0, 10.0), (186.0, 10.0), (-154.0, 10.0))
    # Behind the start and along the promenade (the land is on the right).
    district(c, oh, sc, m, -90.0, S[4], (1,), rows=((18.0, 30.0), (44.0, 60.0)), step=22.0, seed=1)
    # The descent and the west shore (land on the right), the headland's back.
    district(c, oh, sc, m, S[17], S[19], (1,), rows=((16.0, 26.0), (40.0, 56.0)), step=22.0, seed=7, heights=(9.0, 22.0))
    district(c, oh, sc, m, S[21], S[23], (1,), rows=((18.0, 30.0),), step=24.0, seed=13)
    # Villas on the terraces, either side of the climb.
    district(c, oh, sc, m, S[12] + 30, S[17], (-1, 1), rows=((20.0, 30.0),), step=26.0, seed=19, heights=(7.0, 12.0), keep_out=cascades)
    # The north-east beach resort, round behind the cascades.
    for k, (x, y) in enumerate(((215.0, 140.0), (232.0, 190.0), (205.0, 238.0), (250.0, 100.0), (265.0, 160.0), (255.0, 225.0), (300.0, -60.0), (310.0, 30.0),
                                (290.0, 120.0), (-150.0, -255.0), (-215.0, -200.0), (140.0, -230.0))):
        w, d = 18.0 + 6 * rnd(k), 14.0 + 6 * rnd(k + 9)
        r = math.hypot(w, d) / 2
        if not clear(c, x, y, r + 2) or oh.lake_d(x, y) > -r or not free(sc, x, y, r):
            continue
        z = min(sc.ground(x + dx, y + dy) for dx, dy in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2), (0, 0)))
        top = block(m, x, y, w, d, z, 10.0 + 8.0 * rnd(k * 3), rot=0.3 * k, style=("white", "rose", "cream", "ochre")[k % 4])
        sc.footprints.append((x, y, r))
        if k % 2:
            great_dome(m, x, y, top, min(w, d) * 0.3, mat="dome_blue" if k % 4 == 1 else "dome_teal", drum=1.8, onion=0.5)
        else:
            tower(m, x + w * 0.3, y, top, 10.0, r=2.0)
    m.build(c, "Resort", COLL, "both")
    # Docks out into the lake, boats tied up.
    for k, (x, y, a) in enumerate(((150.0, 140.0, math.pi), (60.0, 254.0, -math.pi / 2), (-150.0, 250.0, -math.pi / 2), (-60.0, -186.0, math.pi / 2),
                                   (20.0, -184.0, math.pi / 2))):
        if not clear(c, x, y, 3.0):
            continue
        dx, dy = math.cos(a), math.sin(a)
        dm = Mesh()
        L = 22.0
        dm.add(("wood_dock", "road"), lambda bm: cuboid(bm, (x + dx * L / 2, y + dy * L / 2, 0.9), (L if abs(dx) > 0.5 else 3.0, 3.0 if abs(dx) > 0.5 else L, 0.3)))
        for t in range(6):
            px, py = x + dx * L * t / 5, y + dy * L * t / 5
            for o in (-1.4, 1.4):
                qx, qy = px - dy * o, py + dx * o
                dm.add(("weathered_timber", "wall"), lambda bm, qx=qx, qy=qy: op._cyl(bm, qx, qy, -4.0, 1.6, 0.18, n=5))
        dm.build(c, "Dock %d" % (k + 1), "Props", "visual")
        sc.put(op.moored_boat(c, k), x + dx * L * 0.6 - dy * 3.2, y + dy * L * 0.6 + dx * 3.2, 0.0, rot=a, coll="Props")


# ------------------------------------------------------------------ plants


def gardens(c, oh, sc):
    """Palms, flowers and cypresses wherever the garden is green; desert scrub, cacti and
    a few palms round the edge beyond it."""
    import canyon_props as cp
    import props as pr

    X0, X1, Y0, Y1 = -360.0, 420.0, -320.0, 540.0
    ter = sc.ground_obs

    def ok(lush, margin):
        def f(x, y, z):
            if oh.lake_d(x, y) > -4.0 or not clear(c, x, y, margin):
                return False
            g = oh.garden_k(x, y)
            return g > 0.55 if lush else 0.0 < g < 0.2
        return f

    for j, (make, n, margin, scale, lush, coll) in enumerate((
        (lambda v: op.palm(c, v, 10.0), 64, 6.0, (0.8, 1.35), True, "Plants"),
        (lambda v: op.palm(c, v + 2, 12.0), 36, 6.0, (0.8, 1.3), True, "Plants"),
        (lambda v: op.bougainvillea(c, v), 90, 4.0, (0.7, 1.4), True, "Plants"),
        (lambda v: op.cypress(c, v), 30, 5.0, (0.8, 1.2), True, "Plants"),
        (lambda v: cp.sagebrush(c, v), 120, 4.0, (0.7, 1.3), False, "Plants"),
        (lambda v: cp.dry_grass(c, v), 120, 3.0, (0.8, 1.4), False, "Plants"),
        (lambda v: cp.barrel_cactus(c, v), 30, 4.0, (0.8, 1.2), False, "Plants"),
        (lambda v: op.palm(c, v, 8.0), 24, 5.0, (0.8, 1.1), False, "Plants"),
    )):
        for v in range(2):
            pr.scatter(c, make(v), n // 2, (X0, X1, Y0, Y1), ok(lush, margin), ter, seed=j * 11 + v * 7 + 3, scale=scale,
                       role="visual", coll=coll)


def far_settlements(c, oh, sc):
    """Little settlements and palm groves far out in the desert (only to be seen)."""
    m = Mesh()
    for k, (x, y) in enumerate(((-700.0, 500.0), (650.0, -600.0), (820.0, 420.0), (-760.0, -520.0))):
        for j in range(5):
            bx = x + 30.0 * math.cos(j * 1.3 + k)
            by = y + 30.0 * math.sin(j * 1.7 + k)
            z = oh.natural(bx, by)
            top = block(m, bx, by, 14.0 + 4 * (j % 2), 12.0, z, 7.0 + 3 * (j % 3), rot=j * 0.4, parapet=False)
            if j == 0:
                great_dome(m, bx, by, top, 4.0, mat="dome_blue", drum=1.0, onion=0.5)
        for j in range(8):
            a = j * 0.8 + k
            px, py = x + 55.0 * math.cos(a), y + 55.0 * math.sin(a)
            sc.put(op.palm(c, j % 4, 11.0), px, py, oh.natural(px, py) - 0.3, rot=a, coll="Plants")
    m.build(c, "Far Settlements", COLL, "visual")


class _Rock:
    """What canyon_scenery's rock builders need: the land, and the rock's layers (golden
    and peach low down, red higher up, cream caprock)."""

    def __init__(self, oh):
        self.natural = oh.natural

    @staticmethod
    def _layer(z):
        if z > 150:
            return "strata_cream"
        if z > 90:
            return "strata_red"
        if z > 60:
            return "strata_orange"
        return "gold_cliff"


def rocks(c, oh, sc):
    """Red-rock formations standing on the desert round the basin's rim: a great natural
    arch to the north-east, spires and buttes (only to be seen)."""
    import canyon_scenery as cs

    rk = _Rock(oh)
    base = 70.0
    cs.arch(c, rk, "Desert Arch", (420.0, 610.0), (0.9, -0.45), 110.0, 70.0, base - 10.0, 26.0, 22.0, seed=5, role="visual", coll="Rocks")
    for k, (x, y, rx, ry, top) in enumerate(((-520.0, 640.0, 40.0, 30.0, 190.0), (-470.0, 700.0, 26.0, 22.0, 160.0), (640.0, 380.0, 34.0, 26.0, 180.0),
                                              (680.0, 300.0, 24.0, 20.0, 150.0), (-640.0, -120.0, 46.0, 34.0, 170.0), (600.0, -420.0, 40.0, 30.0, 175.0),
                                              (-420.0, -560.0, 30.0, 24.0, 140.0), (200.0, 760.0, 50.0, 30.0, 200.0))):
        cs.butte(c, rk, "Rock %d" % (k + 1), x, y, rx, ry, top, base=base - 15.0, seed=k * 7 + 3, angle=k * 0.9,
                 bands=cs.SPIRE_BANDS if rx < 25 else cs.BUTTE_BANDS, coll="Rocks", role="visual")


def build(c, oh, sc):
    sc.footprints = [(15.0, 470.0, 140.0), (oh.PAVILION[0], oh.PAVILION[1], oh.ISLAND_R)]
    start_plaza(c, oh, sc)
    road_dressing(c, oh, sc)
    bridges(c, oh, sc)
    pavilion(c, oh, sc)
    market(c, oh, sc)
    terraces(c, oh, sc)
    palace(c, oh, sc)
    headland(c, oh, sc)
    resort(c, oh, sc)
    gardens(c, oh, sc)
    far_settlements(c, oh, sc)
    rocks(c, oh, sc)
