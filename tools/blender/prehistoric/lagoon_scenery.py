# Splash Lagoon's paint (the beach world's fourth course; see splash_lagoon.py): the start
# arch, the park's beach (umbrellas, towels, loungers, the lifeguard tower), the slide
# tower dressed (railed decks, its striped canopy, flags) with more slides spiralling off
# the park's other towers into their own pools, tiled edges round the splash pool and
# the lazy river with rings floating in them, cabanas and the snack shack, bunting, palms
# and flowerbeds, lawns inland, buoys and sailboats offshore. Nothing here changes the
# driving: the lap, its surfaces, the loop and the plank are splash_lagoon.py's,
# unchanged; everything solid stands clear of the road.
# SPDX-License-Identifier: MIT

import math

import beach_props as bp
import course_kit as kit
import props
import ruin_kit as rk
import tropic_props as tp
from aurora_scenery import game_entity
from course_kit import Vector, rnd
from keep_scenery import Scene, across, clear_of, facing
from oasis_desert import Mesh

SLIDES = ("splash_slide_red", "splash_slide_blue", "splash_slide_yellow", "splash_slide_green")


def beach(sc):
    """The start arch, and the beach south of the road: umbrellas, towels, loungers,
    the lifeguard tower, flags."""
    c, m = sc.c, sc.dk
    q = c.at(10.0)
    sc.put(tp.start_arch(c, 27.0, flag="cove_flag"), q.p.x, q.p.y, q.p.z - 0.2, rot=across(q), coll="Gate", r=0.0)
    k = 0
    for x in range(-60, 200, 10):
        y = -22.0 - 5.0 * rnd(x * 0.37)
        if m.sea_d(x, y) > -6 or not clear_of(c, x, y, 4.0):
            continue
        z = sc.ground(x, y)
        sc.put(bp.umbrella(c, k % 5), x, y, z - 0.2, rot=rnd(x) * 6, coll="Beach", r=0.0)
        sc.put(bp.towel(c, k % 4), x + 1.6, y - 0.6, z + 0.02, rot=0.3 * (k % 3), coll="Beach", role="visual")
        if k % 2 == 0:
            sc.put(bp.deck_chair(c, k % 3), x - 1.8, y + 0.4, z, rot=math.pi + 0.2, coll="Beach", r=0.8)
        if k % 4 == 1:
            sc.put(bp.surfboard(c, k % 4), x + 3.2, y + 1.6, z - 0.4, rot=0.2, coll="Beach", r=0.5)
        if k % 3 == 2:
            sc.put(bp.beach_ball(c, k % 3), x + 2.0, y + 2.5, z + 0.3, coll="Beach", role="visual")
        k += 1
    for x in (20.0, 110.0):
        y = -30.0
        if clear_of(c, x, y, 3.0):
            sc.put(tp.lifeguard_tower(c), x, y, sc.ground(x, y) - 0.2, rot=math.pi, coll="Beach", r=2.2)


def slide(sc, name, cx, cy, top, turns, r, mat):
    """A tower slide: a post, a deck on top and a tube spiralling down round it to a pool
    at its foot (scenery: away from the road)."""
    c = sc.c
    z0 = sc.ground(cx, cy)
    me = Mesh()
    me.add(("party_white", "wall"), lambda bm: rk.tube_between(bm, Vector((cx, cy, z0 - 0.5)), Vector((cx, cy, z0 + top + 1.0)), 0.8, 0.8, n=10))
    me.add(("splash_deck", "wall"), lambda bm: rk.tube_between(bm, Vector((cx, cy, z0 + top)), Vector((cx, cy, z0 + top + 0.5)), 3.4, 3.4, n=12))
    me.add(("splash_cabana", "wall"), lambda bm: rk.tube_between(bm, Vector((cx, cy, z0 + top + 4.0)), Vector((cx, cy, z0 + top + 5.6)), 4.2, 0.4, n=12))
    for j in range(4):
        a = j * math.pi / 2 + 0.4
        px, py = cx + 3.0 * math.cos(a), cy + 3.0 * math.sin(a)
        me.add(("party_white", "wall"), lambda bm, px=px, py=py: rk.tube_between(bm, Vector((px, py, z0 + top)), Vector((px, py, z0 + top + 4.0)), 0.15, 0.15,
                                                                                    n=5))
    n = int(turns * 24)
    pts = []
    for i in range(n + 1):
        t = i / n
        a = t * turns * math.tau
        pts.append(Vector((cx + r * math.cos(a), cy + r * math.sin(a), z0 + top - t * (top - 0.6))))
    for a, b in zip(pts, pts[1:]):
        me.add((mat, "wall"), lambda bm, a=a, b=b: rk.tube_between(bm, a, b, 0.9, 0.9, n=8))
    me.build(c, name, "Slides", "visual")
    end = pts[-1]
    out = Vector((math.cos(turns * math.tau), math.sin(turns * math.tau), 0.0))
    pool = end + out * 5.0
    c.disc(name + " Pool", pool.x, pool.y, 5.0, z0 + 0.15, c.lib("splash_pool"), role="visual", n=20)
    c.disc(name + " Pool Edge", pool.x, pool.y, 6.0, z0 + 0.1, c.lib("splash_tile"), role="visual", n=20)
    sc.solid.append((cx, cy, r + 2.0))


def tower(sc):
    """The slide tower, built (the greybox's box stays only as its solid core): four white
    corner posts, three decks in the slides' colours with railings round them, cross
    braces between the floors, a ladder up one side, and a big striped canopy on top with
    flags at its corners."""
    import bpy

    c, m = sc.c, sc.dk
    tx, ty = m.TOWER
    if getattr(m, "RUIN", False):
        return  # (the ruin's tower has toppled)
    for ob in list(c.coll("Props").objects):
        if ob.name.startswith("Slide Tower Canopy"):
            bpy.data.objects.remove(ob, do_unlink=True)
        elif ob.name.startswith("Slide Tower"):
            ob["kp_role"] = "collision"  # (the core: you can't drive into the tower)
    top = m.TOP + 9.0
    me = Mesh()
    white = ("party_white", "wall")
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        x, y = tx + sx * 8.2, ty + sy * 8.2
        me.add(white, lambda bm, x=x, y=y: props.cuboid(bm, (x, y, top / 2 - 0.5), (1.6, 1.6, top + 1.0)))
    floors = (5.0, 10.0, m.TOP + 0.4)
    for k, z in enumerate(floors):
        mat = (SLIDES[k % 4], "wall")
        me.add(mat, lambda bm, z=z: props.cuboid(bm, (tx, ty, z), (18.4, 18.4, 0.7)))
        # Railings: a top rail and posts round each deck's edge.
        for side in range(4):
            a = side * math.pi / 2
            ca, sa = math.cos(a), math.sin(a)
            cx, cy = tx + ca * 9.0, ty + sa * 9.0
            me.add(white, lambda bm, cx=cx, cy=cy, z=z, a=a: props.cuboid(bm, (cx, cy, z + 1.2), (0.25, 18.0, 0.25), a))
            for j in range(-3, 4):
                px, py = cx - sa * j * 2.6, cy + ca * j * 2.6
                me.add(white, lambda bm, px=px, py=py, z=z: props.cuboid(bm, (px, py, z + 0.65), (0.18, 0.18, 1.1)))
    # Cross braces between the floors, on all four faces.
    levels = (0.0,) + floors
    for side in range(4):
        a = side * math.pi / 2
        ca, sa = math.cos(a), math.sin(a)
        for z0, z1 in zip(levels, levels[1:]):
            for d in (-1, 1):
                p0 = Vector((tx + ca * 8.4 - sa * 8.2 * d, ty + sa * 8.4 + ca * 8.2 * d, z0 + 0.3))
                p1 = Vector((tx + ca * 8.4 + sa * 8.2 * d, ty + sa * 8.4 - ca * 8.2 * d, z1 - 0.3))
                me.add(white, lambda bm, p0=p0, p1=p1: rk.tube_between(bm, p0, p1, 0.18, 0.18, n=5))
    # A ladder up the inland face.
    lx, ly = tx, ty + 8.6
    for d in (-0.8, 0.8):
        me.add(("splash_deck", "wall"), lambda bm, d=d: props.cuboid(bm, (lx + d, ly, top / 2), (0.2, 0.2, top)))
    for k in range(int(top / 0.8)):
        me.add(("splash_deck", "wall"), lambda bm, k=k: props.cuboid(bm, (lx, ly, 0.6 + k * 0.8), (1.6, 0.16, 0.16)))
    # The canopy: a big striped tent roof over the top deck.
    for j in range(8):
        a0, a1 = j * math.tau / 8, (j + 1) * math.tau / 8
        mat = ("splash_slide_red" if j % 2 else "party_white", "wall")

        def wedge(bm, a0=a0, a1=a1):
            r, h = 13.0, 6.0
            for side in (1, -1):  # (both sides: it's seen from under the deck too)
                v0 = bm.verts.new((tx + r * math.cos(a0), ty + r * math.sin(a0), top))
                v1 = bm.verts.new((tx + r * math.cos(a1), ty + r * math.sin(a1), top))
                v2 = bm.verts.new((tx, ty, top + h))
                bm.faces.new((v0, v1, v2) if side > 0 else (v2, v1, v0))

        me.add(mat, wedge)
    me.build(c, "Slide Tower Frame", "Park", "visual")
    for j in range(8):
        a = (j + 0.5) * math.tau / 8
        x, y = tx + 13.0 * math.cos(a), ty + 13.0 * math.sin(a)
        if j % 2 == 0:
            sc.put(tp.flag_pole(c, "cove_flag", 3.0), x, y, top - 0.3, coll="Park", role="visual")
    sc.solid.append((tx, ty, 14.0))


def infield(sc):
    """The park inside the lap (it was bare lawn): a wave pool with its tiled deck,
    loungers and umbrellas round it, the wave machine's house and a lifeguard chair; a
    kiddie pool with a mushroom fountain; a row of cabanas; the snack kiosk with picnic
    tables; tiled paths joining them; flowerbeds along the paths."""
    c, m = sc.c, sc.dk

    def room(x, y, r):
        return clear_of(c, x, y, r + 6.0) and sc.free(x, y, r)

    k = 0
    # The wave pool.
    wx, wy, wr = 40.0, 80.0, 22.0
    if room(wx, wy, wr + 6.0):
        z = sc.ground(wx, wy)
        c.disc("Wave Pool Deck", wx, wy, wr + 6.0, z + 0.08, c.lib("splash_tile"), role="visual", n=40)
        c.disc("Wave Pool", wx, wy, wr, z + 0.14, c.lib("splash_pool"), role="visual", n=40)
        for j in range(4):  # the waves' white crests, rolling across it
            yy = wy - wr * 0.6 + j * wr * 0.4
            hw = math.sqrt(max(0.0, wr * wr - (yy - wy) ** 2)) - 1.5
            c.ribbon("Wave Crest %d" % j, [(wx - hw, yy), (wx + hw, yy)], 1.0, z + 0.18, c.lib("party_white"), role="visual")
        box_ = Mesh()
        box_.add(("splash_slide_blue", "wall"), lambda bm: props.cuboid(bm, (wx, wy + wr + 3.0, z + 2.5), (12.0, 4.0, 5.0)))
        box_.add(("party_white", "wall"), lambda bm: props.cuboid(bm, (wx, wy + wr + 3.0, z + 5.3), (13.0, 5.0, 0.6)))
        box_.build(c, "Wave Machine House", "Park", "both")
        sc.solid.append((wx, wy, wr + 6.0))
        sc.put(tp.lifeguard_tower(c), wx + wr + 3.5, wy - 6.0, z - 0.1, rot=math.pi / 2, coll="Park", r=2.2)
        for j in range(10):
            a = math.pi * 1.05 + j * 0.19
            px, py = wx + (wr + 4.0) * math.cos(a), wy + (wr + 4.0) * math.sin(a)
            sc.put(bp.deck_chair(c, j % 3), px, py, z + 0.08, rot=a + math.pi / 2, coll="Park", r=0.0, role="visual")
            if j % 3 == 1:
                sc.put(bp.umbrella(c, (j + k) % 5), px + 1.5 * math.cos(a), py + 1.5 * math.sin(a), z, coll="Park", r=0.0,
                       role="visual")
    # The kiddie pool and its mushroom fountain.
    kx, ky, kr = 100.0, 100.0, 9.0
    if room(kx, ky, kr + 3.0):
        z = sc.ground(kx, ky)
        c.disc("Kiddie Pool Deck", kx, ky, kr + 3.0, z + 0.08, c.lib("splash_tile"), role="visual", n=28)
        c.disc("Kiddie Pool", kx, ky, kr, z + 0.14, c.lib("splash_pool"), role="visual", n=28)
        mush = Mesh()
        mush.add(("party_white", "wall"), lambda bm: rk.tube_between(bm, Vector((kx, ky, z)), Vector((kx, ky, z + 3.2)), 0.5, 0.4, n=8))
        mush.add(("splash_slide_red", "wall"), lambda bm: rk.tube_between(bm, Vector((kx, ky, z + 3.0)), Vector((kx, ky, z + 4.2)), 3.4, 0.3, n=12))
        mush.build(c, "Mushroom Fountain", "Park", "visual")
        game_entity(c, "fountain", kx, ky, z + 4.0, height=1.5, jets=8, radius=3.2)
        sc.solid.append((kx, ky, kr + 3.0))
    # A row of cabanas along the infield's south side, facing the pools.
    for j, x in enumerate(range(80, 175, 16)):
        y = 44.0
        if room(x, y, 4.0):
            sc.put(tp.beach_hut(c, j % 3), x, y, sc.ground(x, y) - 0.2, rot=0.0, coll="Park", r=4.0)
    # The snack kiosk, picnic tables round it.
    sx_, sy_ = 145.0, 100.0
    if room(sx_, sy_, 6.0):
        sc.put(bp.tiki_bar(c), sx_, sy_, sc.ground(sx_, sy_) - 0.2, rot=facing(sx_, sy_, kx, ky), coll="Park", r=4.5)
        tables = Mesh()
        for j in range(5):
            a = 0.6 + j * 1.2
            px, py = sx_ + 9.0 * math.cos(a), sy_ + 9.0 * math.sin(a)
            if not clear_of(c, px, py, 3.0):
                continue
            zz = sc.ground(px, py)
            tables.add(("splash_deck", "wall"), lambda bm, px=px, py=py, zz=zz, a=a: props.cuboid(bm, (px, py, zz + 0.8), (2.6, 1.2, 0.15), a))
            for d in (-1, 1):
                tables.add(("splash_deck", "wall"),
                           lambda bm, px=px, py=py, zz=zz, a=a, d=d: props.cuboid(bm, (px - math.sin(a) * d * 1.0, py + math.cos(a) * d * 1.0, zz + 0.45), (2.6, 0.4, 0.12), a))
            sc.put(bp.umbrella(c, j % 5), px, py, zz - 0.2, coll="Park", r=0.0, role="visual")
        tables.build(c, "Picnic Tables", "Park", "visual")
        sc.solid.append((sx_, sy_, 12.0))
    # Tiled paths joining them, flowers along them.
    paths = [[(-22.0, 80.0), (wx - wr - 6.0, 80.0)], [(wx + wr + 6.0, 80.0), (kx - kr - 3.0, 98.0)], [(kx + kr + 3.0, 100.0), (sx_ - 6.0, 100.0)],
             [(kx, ky - kr - 3.0), (kx, 50.0)], [(sx_, sy_ - 6.0), (sx_, 50.0)]]
    for j, (a, b) in enumerate(paths):
        n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 6))
        pts = []
        for i in range(n + 1):
            x, y = a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n
            if clear_of(c, x, y, 3.0):
                pts.append((x, y, 4.0, sc.ground(x, y) + 0.1))
        if len(pts) >= 2:
            c.ribbon("Park Path %d" % j, pts, 4.0, 0.0, c.lib("splash_tile"), role="visual")
            for i, (x, y, _, z) in enumerate(pts[1:-1]):
                if i % 2 == 0:
                    dx, dy = b[0] - a[0], b[1] - a[1]
                    L = math.hypot(dx, dy)
                    nx, ny = -dy / L, dx / L
                    for side in (-1, 1):
                        sc.put(props.flowers(c), x + nx * side * 3.2, y + ny * side * 3.2, z - 0.1, rot=i + side, coll="Park", role="visual")


def pools(sc):
    """Tiled edges round the splash pool and the lazy river, rings floating in them,
    fountains."""
    c, m = sc.c, sc.dk
    for name, (x, y, r) in (("Splash Pool", m.SPLASH_POOL), ("Lazy River", (m.POND_C[0], m.POND_C[1], m.POND_R + 1.0))):
        c.disc(name + " Edge", x, y, r + 3.4, 0.05, c.lib("splash_tile"), role="visual", n=32)
        for k in range(6):
            a = k * 1.1 + r
            rr = r * (0.3 + 0.5 * rnd(k * 2.3 + r))
            px, py = x + rr * math.cos(a), y + rr * math.sin(a)
            sc.put(bp.beach_ball(c, k % 3), px, py, 0.2, scale=2.2, coll="Park", role="visual")
        game_entity(c, "fountain", x, y, 0.3, height=3.0, jets=6, radius=min(4.0, r * 0.3))


def park(sc):
    """Cabanas and the snack shack, slides off the park's other towers, bunting, palms,
    flowers, lawns."""
    c, m = sc.c, sc.dk
    k = 0
    for x, y in ((150.0, 40.0), (170.0, 60.0), (130.0, 70.0), (-30.0, 70.0), (-50.0, 40.0), (60.0, 150.0), (80.0, 170.0)):
        if clear_of(c, x, y, 6.0) and sc.free(x, y, 4.0):
            sc.put(bp.umbrella(c, k % 5), x, y, sc.ground(x, y) - 0.2, coll="Park", r=0.5)
            sc.put(bp.deck_chair(c, k % 3), x + 2.0, y, sc.ground(x, y), rot=k, coll="Park", r=0.8)
            k += 1
    for x, y in ((-40.0, 110.0), (200.0, 20.0)):
        if clear_of(c, x, y, 8.0) and sc.free(x, y, 6.0):
            sc.put(bp.tiki_bar(c), x, y, sc.ground(x, y) - 0.2, rot=facing(x, y, m.TOWER[0], m.TOWER[1]), coll="Park", r=4.5)
    j = 0
    for x, y, top, turns, r in ((-80.0, 160.0, 16.0, 2.2, 6.0), (230.0, 120.0, 18.0, 2.5, 7.0), (200.0, 220.0, 14.0, 1.8, 5.5), (-110.0, 20.0, 12.0, 1.6, 5.0)):
        if clear_of(c, x, y, r + 14.0) and sc.free(x, y, r + 6.0):
            slide(sc, "Tower Slide %d" % j, x, y, top, turns, r, SLIDES[j % 4])
            j += 1

    def ok(margin):
        return lambda x, y, z: z > 0.8 and m.sea_d(x, y) < -6 and clear_of(c, x, y, margin) and sc.free(x, y, 2.5)

    area = (-190, 320, -40, 290)
    for v in range(3):
        props.scatter(c, bp.coconut_palm(c, v), 18, area, ok(6.0), [sc.ter], seed=3 + v, coll="Palms")
    props.scatter(c, props.flowers(c), 40, area, ok(3.0), [sc.ter], seed=9, coll="Park", role="visual")
    props.scatter(c, props.bush(c, 0), 30, area, ok(4.0), [sc.ter], seed=11, coll="Park", role="visual")
    # Bunting along the start straight, pole to pole on the inland side.
    S = m.TO_ROAD
    prev = None
    s = 20.0
    while s < S(m.SEG[1]) + 40:
        q = c.at(s)
        p = q.side(q.w / 2 + 4.0)
        if clear_of(c, p.x, p.y, 2.0):
            z = sc.ground(p.x, p.y)
            sc.put(bp.bamboo_pole(c), p.x, p.y, z - 0.3, coll="Park", role="visual")
            if prev:
                bp.string_line(c, "Bunting %d" % int(s), prev, (p.x, p.y, z + 4.6), 0.8, coll="Park")
            prev = (p.x, p.y, z + 4.6)
        s += 16.0


def offshore(sc):
    c = sc.c
    for k, (x, y) in enumerate(((0.0, -80.0), (60.0, -90.0), (120.0, -80.0), (180.0, -90.0))):
        sc.put(tp.buoy(c, "cove_awning_sun" if k % 2 else "cove_lighthouse"), x, y, -0.2, coll="Offshore", role="visual")
    for k, (x, y, rot) in enumerate(((40.0, -150.0, 0.5), (-80.0, -130.0, -0.3), (200.0, -170.0, 1.0))):
        sc.put(tp.sailboat(c, k), x, y, 0.0, rot=rot, coll="Offshore", role="visual")
    game_entity(c, "birds", 60.0, 60.0, 40.0, radius=60, count=5, speed=0.2, seed=3, color="#ffffff")
    c.entity("sparkles", rate=10, radius=30)


def light(sc):
    c = sc.c
    groups = ("Gate", "Beach", "Park", "Palms", "Offshore")
    c.merge_props(groups, cell=220.0)
    built = [o for name in groups + ("Slides",) for o in c.coll(name).objects if o.type == "MESH" and o.data.users == 1]
    c.preset("sun", [sc.ter] + built, 0.22)
    if sc.flames:
        c.glow([sc.ter] + built, sc.flames, 9.0, (1.4, 1.1, 0.7), base=1.0)
    kit.paint.shade_roads(c.pieces, 0.3)


def build(c, m, ter):
    sc = Scene(c, m, ter)
    beach(sc)
    tower(sc)
    pools(sc)
    infield(sc)
    park(sc)
    offshore(sc)
    for x, y, z in sc.flames:
        game_entity(c, "torch", x, y, z)
    if getattr(m, "RUIN", False):
        return sc  # (the ruin lights it, with its own wreckage)
    light(sc)
    print("lagoon scenery: props", c.prop_count)
    return sc
