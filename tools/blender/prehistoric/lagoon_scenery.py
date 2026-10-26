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
    """The slide tower dressed: its box in yellow and red, a striped canopy, railed deck
    edges, flags at its corners."""
    c, m = sc.c, sc.dk
    tx, ty = m.TOWER
    if getattr(m, "RUIN", False):
        return  # (the ruin's tower has toppled)
    for ob in list(c.coll("Props").objects):
        if ob.name.startswith("Slide Tower Canopy"):
            ob.data.materials.clear()
            ob.data.materials.append(c.lib("splash_cabana"))
        elif ob.name.startswith("Slide Tower"):
            ob.data.materials.clear()
            ob.data.materials.append(c.lib("splash_slide_yellow"))
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        x, y = tx + sx * 11.5, ty + sy * 11.5
        sc.put(tp.flag_pole(c, "cove_flag", 4.0), x, y, m.TOP + 10.0, coll="Park", role="visual")


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
    park(sc)
    offshore(sc)
    for x, y, z in sc.flames:
        game_entity(c, "torch", x, y, z)
    if getattr(m, "RUIN", False):
        return sc  # (the ruin lights it, with its own wreckage)
    light(sc)
    print("lagoon scenery: props", c.prop_count)
    return sc
