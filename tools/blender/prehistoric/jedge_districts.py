# The Edge of the World's districts, dressed (Blake, Nov 2: "it should be crawling with
# black market activity. we need npcs, alot of them, and all sorts of stuff going on.
# different areas that are distinct"): the Sea Door Grotto, the Smugglers' Docks, the
# alley and the bores, the Night Bazaar, the Fighting Pits, the Lucky Bone; and the Sky
# Islands' life. jedge_region.py calls dress() and sky_life().
# SPDX-License-Identifier: MIT
#
# The people: hundreds of them in the game's instanced crowds (game/isles.ts' roles:
# haulers, merchants, queues, cheering stands, guards, musicians, dancers), dressed in the
# black market's own clothes; the talkers (villager_home, folk "sump") each district's own
# lines (overworld/villagers.ts' TALK_LINES); party dinos boxing in the ring and dancing in
# the den, a conga round the bazaar's square, cranes swinging loads over the docks, boats
# on the black water.

import math

from course_kit import bmesh, lerp
from pocket_build import box, cone
import props
import beach_props as bp
import tropic_props as tp
import keep_props as kp
import gulch_props as gp
import swamp_props as sw
import region_paint as paint
import jedge_layout as L
from jedge_layout import (BASIN, BAZAAR, BAZ_Z, CANAL, DEN, DEN_Z, DOCK_FLOOR, DOCK_WATER, DOCKS, ISLES, PIT, PIT_FLOOR,
                          PIT_R, cavern_at, ellipse, pit_ground, spiral_at)

CROWD = []  # the black market's people (one instanced crowd)
SKY_CROWD = []  # the sky islands' (in the Dragon Kingdom's colours)
CROWD_N = [0, 0]  # how many people, how many talkers
FOLK = []  # the detailed folk, posed (game/folkPoses.ts: the Rookery's buildings, the diner)


def rnd(k):
    return (math.sin(k * 12.9898 + 4.1414) * 43758.5453) % 1.0


def person(c, x, y, z, role, fx, fy, v=None, sky=False):
    """One of the crowd (game/isles.ts' roles), standing at (x, y, z) facing (fx, fy)."""
    dx, dy = fx - x, fy - y
    n = math.hypot(dx, dy) or 1.0
    to = SKY_CROWD if sky else CROWD
    g = c.game(x, y, z)
    vv = v if v is not None else int(rnd(len(to) * 7.3 + x) * 11)
    to.append([round(g[0], 2), round(g[1], 2), round(g[2], 2), round(dx / n, 3), round(-dy / n, 3), role, vv])
    CROWD_N[0] += 1


def folk(c, x, y, z, pose, fx, fy, seed=None, at=None):
    """One of the detailed folk (a croc of the black market), facing (fx, fy), posed: busy
    at something ("eat", "cook", "chat", "lean", "beat", "hang", "dance"), looking at `at`
    (x, y, z: their partner, their plate, the street) when not glancing at you; or "watch",
    "wave", "cheer", "nod", "point", "think", "shrug", "kneel", "work" (game/folkPoses.ts)."""
    g = c.game(x, y, z)
    sd = seed if seed is not None else int(rnd(len(FOLK) * 3.1 + x + y) * 97)
    row = [round(g[0], 2), round(g[1], 2), round(g[2], 2), round(math.atan2(fx - x, -(fy - y)), 3), pose, sd]
    if at is not None:
        row += [round(v, 2) for v in c.game(*at)]
    FOLK.append(row)
    CROWD_N[0] += 1


def talkers(c, x, y, z, n, talk, r=10.0):
    """A home of the black market's talkers (folk "sump", their district's lines)."""
    g = c.game(x, y, z)
    c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=r, n=n, folk="sump", heading=0.0, talk=talk)
    CROWD_N[1] += n


def light(c, kind, x, y, z):
    g = c.game(x, y, z)
    c.entity(kind, x=round(g[0], 2), y=round(g[1], 2), z=round(g[2], 2))


def cloth(c, name, pts, mat):
    bm = bmesh.new()
    bm.faces.new([bm.verts.new(p) for p in pts])
    bm.faces.new([bm.verts.new(p) for p in reversed(pts)])
    c.assign(c.mesh_object(name, bm, "Props", "visual"), c.lib(mat, "wall"))


def tube(c, name, pts, r, mat, n=4):
    bm = bmesh.new()
    props.tube(bm, pts, r, n=n)
    c.assign(c.mesh_object(name, bm, "Props", "visual"), c.lib(mat, "wall"))


def egg(c, name, x, y, z, r, mat):
    bm = bmesh.new()
    props.blob(bm, (x, y, z + r * 1.2), r, sz=1.35, subdiv=1)
    c.assign(c.mesh_object(name, bm, "Props", "visual"), c.lib(mat, "wall"))


def lantern_line(c, name, p0, p1, sag=1.0):
    """A rope slung between two points with ship's lanterns hung off it (review 1 note 7:
    the paper lanterns "dont match the smuggler vibe"): each on a short chain, tied on."""
    import harbour_props as hp

    n = 12
    pts = [(lerp(p0[0], p1[0], k / n), lerp(p0[1], p1[1], k / n), lerp(p0[2], p1[2], k / n) - sag * 4 * (k / n) * (1 - k / n))
           for k in range(n + 1)]
    tube(c, name + " Rope", pts, 0.03, "rope_rail")
    span = math.dist(p0, p1)
    m = max(1, int(span / 2.8))
    for k in range(m):
        t = (k + 0.5) / m
        x, y = lerp(p0[0], p1[0], t), lerp(p0[1], p1[1], t)
        z = lerp(p0[2], p1[2], t) - sag * 4 * t * (1 - t)
        tube(c, "%s Chain %d" % (name, k), [(x, y, z), (x, y, z - 0.35)], 0.012, "keep_iron", n=3)
        c.place(hp.cage_lantern(c, k + len(name)), x, y, z - 0.35, role="visual")


def ok(c, taken, x, y, r, margin=2.0):
    return paint.road_clear(c, x, y, r + margin) and taken.clear(x, y, r)


def dress(c, ground, s0, s1):
    import jedge_rookery as R

    R.D = __import__(__name__)
    taken = paint.Taken()
    grotto(c, ground, taken)
    docks(c, ground, taken)
    R.tavern(c, ground, taken)
    R.rookery(c, ground, taken)
    R.gallery(c, ground, taken)
    R.lanes(c, ground, taken)
    bazaar(c, ground, taken)
    pits(c, ground, taken)
    den(c, ground, taken)
    bores(c, ground, s0, s1)
    c.entity("villagers", list=CROWD, palette="sump")
    c.entity("folk_poses", folk="sump", list=FOLK)


# ------------------------------------------------------------------ the Sea Door Grotto


def grotto(c, ground, taken):
    """Where you come in from the isles: rowboats run up on the grotto's muck, haulers
    carrying their cargo in, a lookout, the first lanterns."""
    cx, cy = L.GROTTO[:2]
    for j in range(4):
        a = j * 1.6 + 0.4
        x, y = cx + 16.0 * math.cos(a), cy + 20.0 * math.sin(a)
        if ok(c, taken, x, y, 3.0):
            c.place(tp.rowboat(c), x, y, ground(x, y) - 0.2, rot=a, role="visual")
            taken.add(x, y, 3.0)
            for k in range(3):
                px, py = x + 2.6 * math.cos(a + 1.6 + k * 0.5), y + 2.6 * math.sin(a + 1.6 + k * 0.5)
                person(c, px, py, ground(px, py), "hauler" if k else "worker", x, y)
            c.place(gp.crate_stack(c, j % 3), x + 3.5 * math.cos(a - 1.2), y + 3.5 * math.sin(a - 1.2),
                    ground(x + 3.5 * math.cos(a - 1.2), y + 3.5 * math.sin(a - 1.2)), rot=a, role="visual")
    talkers(c, cx + 10.0, cy - 6.0, ground(cx + 10.0, cy - 6.0), 3, "docks", r=8.0)


# ------------------------------------------------------------------ the Smugglers' Docks


def docks(c, ground, taken):
    """The black-water harbour (jedge_harbour: the water, its quays, the sea leak, the weir
    and the water gate, the stone bridge, the ships, the rowing boats, the stilt shacks),
    the quay's cranes hauling nets and crates off the moored ships, warehouses and the
    Customs House, crates stacked everywhere, dockhands hauling, the fish market, mist."""
    import sys
    import jedge_harbour as H

    bx, by, br = BASIN
    cy, hw, cx0, cx1 = CANAL
    # The harbour's water, its quays, the sea leak, the weir and the water gate, the stone
    # bridge, the ships and the boats (jedge_harbour: Blake, Nov 4).
    H.harbour(c, ground, taken, sys.modules[__name__])
    # The cranes on the quay (between the road and the water), jibs out over the basin,
    # standing still (review 1 note 2): one lowering a net of crates onto a stack on the
    # quay, one a pallet into a skiff tied up under it.
    for j, (x, y, reach, drop, load) in enumerate(((-24.0, -339.0, 11.0, 8.6, "net"), (-22.0, -279.0, 12.0, 9.5, "pallet"))):
        if not paint.road_clear(c, x, y, 3.5):
            print("  (crane %d: too near the road)" % j)
            continue
        z = ground(x, y)
        a = math.atan2(by - y, bx - x)
        c.place(H.hp.harbour_crane(c, j, height=9.0, reach=reach, drop=drop, load=load), x, y, z - 0.3, rot=a, role="visual")
        box(c, "Crane Solid %d" % j, x, y, 2.0, 2.0, z - 0.5, z + 10.0, ("weathered_timber", "wall"), rot=a, role="collision")
        light(c, "lantern", x - 1.8 * math.cos(a), y - 1.8 * math.sin(a), z + 10.6)
        tx = x + (1.5 + reach * math.cos(0.42)) * math.cos(a)
        ty = y + (1.5 + reach * math.cos(0.42)) * math.sin(a)
        if L.in_water(tx, ty):
            c.place(H.hp.moored_skiff(c, 3 + j), tx, ty, DOCK_WATER, rot=a + 0.4, role="visual")
        else:
            c.place(gp.crate_stack(c, j), tx, ty, ground(tx, ty), rot=a, role="visual")
            for k in range(2):
                person(c, tx + 1.8 * math.cos(a + 1.6 + k * 3.1), ty + 1.8 * math.sin(a + 1.6 + k * 3.1), ground(tx, ty), "worker", tx, ty)
        taken.add(x, y, 3.0)
        taken.add(tx, ty, 2.0)
        for k in range(3):
            px, py = x + 2.8 * math.cos(a + 2.2 + k), y + 2.8 * math.sin(a + 2.2 + k)
            person(c, px, py, ground(px, py), "worker", tx, ty)
    # Warehouses along the docks' east and north sides, the Customs House on the canal.
    sheds = [(26.0, -336.0, 0.3, "siding_brown"), (40.0, -318.0, 1.2, "siding_grey"), (-38.0, -264.0, 0.1, "siding_green"),
             (-60.0, -278.0, 1.5, "siding_red"), (-12.0, -258.0, 0.0, "siding_ochre"), (34.0, -282.0, 0.2, "siding_brown")]
    for j, (x, y, rot, mat) in enumerate(sheds):
        if not ok(c, taken, x, y, 6.0, 1.0) or ellipse(x, y, *DOCKS) > 0.9:
            continue
        z = ground(x, y)
        # (run down: review 1 note 8; harbour_props.warehouse)
        c.place(H.hp.warehouse(c, j, 13.0, 9.0, 7.0), x, y, z - 0.05, rot=rot, coll="Village", role="visual")
        box(c, "Warehouse %d" % j, x, y, 6.5, 4.5, z - 0.5, z + 7.0, (mat, "wall"), rot=rot, role="collision")
        ca, sa = math.cos(rot), math.sin(rot)
        for sd in (-1, 1):
            # (its big doors, a lamp over them, crates spilling out)
            dx, dy = x - sa * sd * 4.55, y + ca * sd * 4.55
            light(c, "lantern", dx - sa * sd * 0.6, dy + ca * sd * 0.6, z + 5.0)
            ox, oy = dx - sa * sd * 3.0, dy + ca * sd * 3.0
            if paint.road_clear(c, ox, oy, 2.0):
                c.place(gp.crate_stack(c, (j + sd) % 3), ox + ca * 2.0, oy + sa * 2.0, ground(ox, oy), rot=rot, role="visual")
                person(c, ox - ca * 1.0, oy - sa * 1.0, ground(ox, oy), "hauler", dx, dy)
                person(c, dx - sa * sd * 1.0 + ca * 2.0, dy + ca * sd * 1.0 + sa * 2.0, z, "guard", ox, oy)
        taken.add(x, y, 7.0)
    x, y = 34.0, cy + hw + 6.0
    if ok(c, taken, x, y, 4.0, 1.0):
        z = ground(x, y)
        c.place(H.hp.warehouse(c, 7, 8.0, 6.0, 5.0), x, y, z - 0.05, rot=0.0, coll="Village", role="visual")
        box(c, "Customs House", x, y, 4.0, 3.0, z - 0.5, z + 5.0, ("cabin_wall", "wall"), role="collision")
        box(c, "Customs Window", x - 2.4, y - 3.12, 0.8, 0.05, z + 1.4, z + 2.6, ("window_warm", "wall"), role="visual")
        c.place(tp.flag_pole(c, flag="wreck_flag", h=8.0), x + 3.4, y, z, role="visual")
        light(c, "lantern", x, y - 3.6, z + 3.2)
        taken.add(x, y, 5.0)
        for k in range(7):
            px, py = x - 1.0 + k * 1.3, y - 4.6 - 0.4 * (k % 2)
            person(c, px, py, ground(px, py), "queue", x, y)
        person(c, x, y - 3.4, z, "merchant", x, y - 8.0)
    # The fish market on the quay's north side: stalls of the black water's catch (review 1
    # note 3: harbour_props.market_stall), a lantern hung at each.
    for j in range(5):
        x, y = -30.0 + j * 5.0, cy + hw + 8.0 + (j % 2)
        if not ok(c, taken, x, y, 2.0, 1.0):
            continue
        z = ground(x, y)
        c.place(H.hp.market_stall(c, j, ("fish", "crabs", "eels", "bottles", "fish")[j]), x, y, z - 0.03, rot=0.0, role="visual")
        box(c, "Fish Stall %d" % j, x, y - 0.6, 1.7, 0.4, z - 0.2, z + 1.0, ("wood_dock", "wall"), role="collision")
        c.place(H.hp.cage_lantern(c, j), x + 1.5, y - 0.85, z + 2.35, role="visual")
        light(c, "lantern", x + 1.5, y - 0.85, z + 1.9)
        person(c, x, y + 0.4, z, "merchant", x, y - 4.0)
        for k in range(2):
            person(c, x - 0.8 + 1.6 * k, y - 1.8, z, "huddle" if k else "queue", x, y)
        taken.add(x, y, 2.4)
    # Crates and barrels everywhere off the road, dockhands at them, fishers on the edge.
    for j in range(40):
        a = j * 2.399 + 0.7
        r = 0.25 + 0.65 * ((j * 0.618) % 1.0)
        x, y = DOCKS[0] + DOCKS[2] * r * math.cos(a), DOCKS[1] + DOCKS[3] * r * math.sin(a)
        if L.in_water(x, y) or math.hypot(x - bx, y - by) < br + 2.5 or not ok(c, taken, x, y, 1.6, 2.0):
            continue
        z = ground(x, y)
        if abs(z - DOCK_FLOOR) > 0.8:
            continue
        c.place(gp.crate_stack(c, j % 4) if j % 3 else gp.barrel(c, j % 2), x, y, z, rot=a, role="both" if j % 3 else "visual")
        taken.add(x, y, 1.8)
        if j % 2 == 0:
            person(c, x + 1.6 * math.cos(a), y + 1.6 * math.sin(a), z, ("hauler", "worker", "huddle")[j % 3], x, y)
    for j in range(10):
        a = j * 0.55 + 2.0
        x, y = bx + (br + 1.4) * math.cos(a), by + (br + 1.4) * math.sin(a)
        if paint.road_clear(c, x, y, 2.0) and taken.clear(x, y, 0.6):
            person(c, x, y, DOCK_FLOOR + 0.2, "fisher", bx, by)
    # (a low mist over the black water, not puffs of steam)
    for j in range(3):
        a = j * math.tau / 3 + 0.3
        g = c.game(bx + br * 0.5 * math.cos(a), by + br * 0.5 * math.sin(a), DOCK_WATER + 0.6)
        c.entity("mist", x=round(g[0], 1), y=round(g[1], 1), z=round(g[2], 1), radius=12.0, rate=2.5, color="#8aa4a0")
    # The shacks on stilts round the walls, their walkways and pulleys (they keep off the
    # warehouses and the market, so after them).
    print("stilt shacks: %d" % H.stilts(c, ground, taken))
    # A fire for the dockhands.
    x, y = 12.0, -326.0
    if ok(c, taken, x, y, 2.0, 2.0):
        z = ground(x, y)
        light(c, "campfire", x, y, z + 0.2)
        for k in range(6):
            a = k * math.tau / 6
            person(c, x + 2.4 * math.cos(a), y + 2.4 * math.sin(a), z, "huddle", x, y)
        taken.add(x, y, 3.2)
    # Along the quay road: lantern strings across it, cargo stacked by it, dockhands at it.
    s_in = sorted((q for q in c.S if ellipse(q.p.x, q.p.y, *DOCKS) < 0.9 and abs(q.p.z - DOCK_FLOOR) < 2.5), key=lambda q: q.s)
    if s_in:
        s = s_in[0].s + 5.0
        k = 0
        while s < s_in[-1].s - 5.0:
            q = c.at(s)
            if not L.over_canal(q.p.x, q.p.y, 6.0):
                if k % 2 == 0:
                    ends = []
                    for sd in (-1, 1):
                        x, y = q.p.x + q.r.x * sd * (q.w / 2 + 1.8), q.p.y + q.r.y * sd * (q.w / 2 + 1.8)
                        z = ground(x, y)
                        box(c, "Quay Pole %d %d" % (k, sd), x, y, 0.12, 0.12, z, z + 7.5, ("weathered_timber", "wall"))
                        ends.append((x, y, z + 7.3))
                    lantern_line(c, "Quay String %d" % k, ends[0], ends[1], sag=1.2)
                for sd in (-1, 1):
                    x, y = q.p.x + q.r.x * sd * (q.w / 2 + 4.0), q.p.y + q.r.y * sd * (q.w / 2 + 4.0)
                    if L.in_water(x, y) or not ok(c, taken, x, y, 1.4, 2.4):
                        continue
                    z = ground(x, y)
                    if abs(z - DOCK_FLOOR) > 0.8:
                        continue
                    c.place(gp.crate_stack(c, (k + sd) % 4) if (k + sd) % 3 else gp.barrel(c, k % 2), x, y, z, rot=k, role="both")
                    taken.add(x, y, 1.6)
                    for i in range(2):
                        px = x - q.r.x * sd * 1.8 + q.t.x * (i - 0.5) * 1.6
                        py = y - q.r.y * sd * 1.8 + q.t.y * (i - 0.5) * 1.6
                        person(c, px, py, z, ("hauler", "worker", "guard", "huddle")[(k + i) % 4], x, y)
            s += 9.0
            k += 1
    for j, (x, y) in enumerate(((-30.0, -332.0), (8.0, -270.0), (-40.0, -330.0))):
        talkers(c, x, y, ground(x, y), 5, "docks", r=9.0)


# ------------------------------------------------------------------ the Night Bazaar


LOOT = ("ice", "eggs", "neon", "coral", "crystals", "gold", "food", "rugs")


def goods(c, name, kind, x, y, z, rot):
    for i in range(3):
        lx, ly = x + (i - 1) * 1.4 * math.cos(rot), y + (i - 1) * 1.4 * math.sin(rot)
        if kind == "ice":
            box(c, "%s Ice %d" % (name, i), lx, ly, 0.55, 0.55, z, z + 1.0, ("glacier_ice", "wall"), rot=rot + i, role="visual")
        elif kind == "eggs":
            egg(c, "%s Egg %d" % (name, i), lx, ly, z, 0.38, ("party_white", "party_red", "lush_grass")[i])
        elif kind == "neon":
            box(c, "%s Neon %d" % (name, i), lx, ly, 0.55, 0.08, z + 0.1, z + 0.9, (("lantern_amber", "fire_glow", "crystal_magenta")[i], "wall"),
                rot=rot, role="visual")
        elif kind == "coral":
            c.place(tp.coral(c, i % 3), lx, ly, z, rot=i, scale=0.33, role="visual")
        elif kind == "crystals":
            cone(c, "%s Crystal %d" % (name, i), lx, ly, 0.32, z, 1.3, (("crystal_cyan", "crystal_violet", "crystal_gold")[i], "wall"), segs=5,
                 role="visual")
        elif kind == "gold":
            cone(c, "%s Gold %d" % (name, i), lx, ly, 0.55, z, 0.55, ("gold_trim", "wall"), segs=8, role="visual")
        elif kind == "food":
            cone(c, "%s Pot %d" % (name, i), lx, ly, 0.45, z, 0.7, ("iron", "wall"), segs=8, role="visual")
        else:
            box(c, "%s Rug %d" % (name, i), lx, ly, 0.6, 0.5, z, z + 0.25 + 0.2 * i, ("rug", "wall"), rot=rot, role="visual")


def stall(c, name, x, y, z, rot, kind, mat):
    """A market stall: a counter, two poles, an awning, goods on it, its lamp."""
    ca, sa = math.cos(rot), math.sin(rot)  # (rot: along the counter; the front faces -(−sa, ca)... see callers)
    box(c, name + " Counter", x, y, 2.4, 0.8, z - 0.2, z + 1.0, ("plank_deck", "wall"), rot=rot)
    for px in (-2.2, 2.2):
        box(c, "%s Pole %d" % (name, px), x + ca * px - sa * 0.9, y + sa * px + ca * 0.9, 0.08, 0.08, z, z + 3.1, ("weathered_timber", "wall"),
            role="visual")
    cloth(c, name + " Awning", [(x - 2.6 * ca - 1.2 * sa, y - 2.6 * sa + 1.2 * ca, z + 3.2), (x + 2.6 * ca - 1.2 * sa, y + 2.6 * sa + 1.2 * ca, z + 3.2),
                                (x + 2.6 * ca + 1.4 * sa, y + 2.6 * sa - 1.4 * ca, z + 2.5), (x - 2.6 * ca + 1.4 * sa, y - 2.6 * sa - 1.4 * ca, z + 2.5)],
          mat)
    goods(c, name, kind, x, y, z + 1.0, rot)
    light(c, "lantern", x, y, z + 2.9)


def bazaar(c, ground, taken):
    """The Night Bazaar (Blake: the black market, crawling): stalls crammed along both sides
    of the road's slalom, a merchant behind every counter and customers haggling in front;
    net lines across the floor; cookfires behind; the shanty band's stage; smuggler flags
    under the roof; the shantytown's shacks crammed in wherever there's room (jedge_shanty,
    Blake, Nov 5: Port Borgo's feel)."""
    import jedge_rookery as R

    import jedge_shanty as S
    from gulch_scenery import Mesh

    bx, by, brx, bry = BAZAAR
    nets = Mesh()

    def ok(c, taken, x, y, r, margin=2.0):
        # (clear of the road, the Beast Market's lane and the Gallery over the floor)
        return paint.road_clear(c, x, y, r + margin) and taken.clear(x, y, r) and R.beast_clear(x, y, r + margin)

    # The shanty band's stage (Blake, Nov 5, note 2: "this crowd of dancing people is weird.
    # we need to redo this area"; he picked a low-key band): the bow of a wreck beached on
    # the floor, the band on its deck, their crowd sat about before it, the bow to the road.
    best = None
    for j in range(40):
        a = j * 2.399
        r = 0.15 + 0.6 * ((j * 0.618) % 1.0)
        x, y = bx + brx * r * math.cos(a), by + bry * r * math.sin(a)
        if paint.road_clear(c, x, y, 10.0) and R.beast_clear(x, y, 10.0) and (best is None or paint.road_clear(c, x, y, 13.0)):
            best = (x, y)
            if paint.road_clear(c, x, y, 13.0):
                break
    if best:
        x, y = best
        smp, _ = c.nearest(x, y)
        dx, dy = smp.p.x - x, smp.p.y - y
        n = math.hypot(dx, dy) or 1.0
        S.stage(c, ground, taken, x, y, (dx / n, dy / n))
    # Behind the stalls: crates, cookfires, the crowd milling.
    for j in range(160):
        a = j * 2.399 + 0.2
        r = 0.12 + 0.8 * ((j * 0.618) % 1.0)
        x, y = bx + brx * r * math.cos(a), by + bry * r * math.sin(a)
        if not ok(c, taken, x, y, 2.6, 2.0):
            continue
        z = ground(x, y)
        kind = j % 5
        if kind in (0, 2):
            # (the tents and rug piles that stood here: the shanty's shacks now, S.shanty)
            continue
        if kind == 1:
            light(c, "campfire", x, y, z + 0.2)
            light(c, "chimney", x, y, z + 1.5)
            for i in range(5):
                b = i * math.tau / 5 + j
                person(c, x + 2.2 * math.cos(b), y + 2.2 * math.sin(b), z, ("huddle", "merchant", "huddle", "queue", "huddle")[i], x, y)
        elif kind == 3:
            c.place(gp.crate_stack(c, j % 4), x, y, z, rot=a, role="both")
            person(c, x + 1.8 * math.cos(a), y + 1.8 * math.sin(a), z, "hauler", x, y)
        else:
            for i in range(4):
                b = i * math.tau / 4 + j * 0.3
                person(c, x + 1.0 * math.cos(b), y + 1.0 * math.sin(b), z, ("huddle", "wave", "huddle", "cheer")[i], x, y)
        taken.add(x, y, 3.0)
    # Lantern strings slung across the market's floor between tall poles (the Gallery looks
    # down on them).
    poles = []
    for j in range(60):
        a = j * 2.399 + 1.1
        r = 0.15 + 0.75 * ((j * 0.618 + 0.3) % 1.0)
        x, y = bx + brx * r * math.cos(a), by + bry * r * math.sin(a)
        if y < -160.0 or not ok(c, taken, x, y, 0.4, 1.5):
            continue
        poles.append((x, y, ground(x, y)))
    n_str = 0
    for i, (x, y, z) in enumerate(poles):
        best = min((p for p in poles[i + 1:] if 14.0 < math.dist(p[:2], (x, y)) < 30.0), key=lambda p: math.dist(p[:2], (x, y)), default=None)
        if best is None or n_str >= 12:
            continue
        for (px, py, pz) in ((x, y, z), best):
            box(c, "Market Pole %d %d" % (i, int(px)), px, py, 0.12, 0.12, pz, pz + 8.2, ("weathered_timber", "wall"))
            taken.add(px, py, 0.6)
        S.net_line(c, nets, (x, y, z + 8.0), (best[0], best[1], best[2] + 8.0), 1.6, i)
        light(c, "glow", (x + best[0]) / 2, (y + best[1]) / 2, (z + best[2]) / 2 + 5.0)
        n_str += 1
    # Smuggler flags hung from spars under the roof (note 9: "remove all of these chinese
    # looking banners. we need smuggler looking banners"), tattered.
    for j in range(14):
        a = j * math.tau / 14
        x, y = bx + brx * 0.7 * math.cos(a), by + bry * 0.7 * math.sin(a)
        z0 = BAZ_Z + 20.0
        ax, ay = -math.sin(a), math.cos(a)
        nets.add(("weathered_timber", "wall"), lambda bm, x=x, y=y, ax=ax, ay=ay: props.tube(bm, [(x - ax * 1.6, y - ay * 1.6, z0 + 0.1), (x + ax * 1.6, y + ay * 1.6, z0 + 0.1)], 0.07, n=4))
        for sd in (-1, 1):
            nets.add(("rope_rail", "wall"), lambda bm, x=x, y=y, ax=ax, ay=ay, sd=sd: props.tube(bm, [(x + ax * sd * 1.5, y + ay * sd * 1.5, z0 + 0.1), (x + ax * sd * 0.4, y + ay * sd * 0.4, BAZ_Z + 30.0)], 0.03, n=3))
        S.flag(nets, (x, y, z0), (ax, ay), 2.8, 5.6, S.FLAGS[j % 3], 60 + j, strips=5)
    nets.build(c, "Bazaar Nets And Flags", coll="Props", role="visual")
    S.shanty(c, ground, taken)
    for j, (x, y) in enumerate(((176.0, -180.0), (150.0, -190.0), (190.0, -150.0), (128.0, -150.0))):
        if paint.road_clear(c, x, y, 6.0) and R.beast_clear(x, y, 6.0):
            talkers(c, x, y, ground(x, y), 6, "bazaar", r=9.0)


# ------------------------------------------------------------------ the Fighting Pits


def pits(c, ground, taken):
    """The Fighting Pits, the smugglers' dry dock now (Blake, Nov 5; jedge_drydock): the
    road corkscrewing down its wall past the breakers' wrecks, the great galleon building
    on its floor with its scaffolding and cranes, the lock gate leaking, the yard's trades;
    braziers round its rim, smuggler flags down its walls, the gate in with its sign."""
    import jedge_drydock as DD
    import jedge_rookery as R
    import jedge_shanty as S
    from gulch_scenery import Mesh

    px, py = PIT
    f0, f1, f2 = PIT_R
    DD.dock(c, ground, taken)
    DD.breakers(c, taken)
    for j, a in enumerate((0.9, 2.3, 4.4)):
        x, y = px + 27.0 * math.cos(a), py + 27.0 * math.sin(a)
        if paint.road_clear(c, x, y, 4.0) and not DD.on_ship(x, y, 2.0):
            talkers(c, x, y, PIT_FLOOR, 5, "pits", r=4.0)
    # Torches along the spiral's rail, every few metres, both sides by turns.
    for k in range(40):
        a = -60.0 - 300.0 * (k + 0.5) / 40
        r_road, z_road = spiral_at(a)
        ra = math.radians(a)
        r = r_road + (8.6 if k % 2 else -8.6)
        light(c, "torch", px + r * math.cos(ra), py + r * math.sin(ra), z_road + 2.2)
    # Braziers round the rim; smuggler flags down the walls.
    flags = Mesh()
    for k in range(16):
        a = k * math.tau / 16 + 0.1
        x, y = px + (f2 - 4.0) * math.cos(a), py + (f2 - 4.0) * math.sin(a)
        if paint.road_clear(c, x, y, 2.5):
            zt = pit_ground(x, y)
            c.place(sw.stone_brazier(c), x, y, zt, rot=a, role="visual")
            light(c, "campfire", x, y, zt + 2.0)
        z0 = -12.0
        x, y = px + (f2 - 1.5) * math.cos(a + 0.2), py + (f2 - 1.5) * math.sin(a + 0.2)
        ax, ay = -math.sin(a), math.cos(a)
        flags.add(("weathered_timber", "wall"), lambda bm, x=x, y=y, ax=ax, ay=ay: props.tube(bm, [(x - ax * 2.0, y - ay * 2.0, z0 + 0.1), (x + ax * 2.0, y + ay * 2.0, z0 + 0.1)], 0.09, n=4))
        S.flag(flags, (x, y, z0), (ax, ay), 3.6, 7.2, S.FLAGS[k % 3], 80 + k, strips=5)
    # The gate in: a timber gate over the road, THE DRY DOCK on it each way, torches.
    q, _ = c.nearest(*L.ROUTE[L.AT["pit_gate"]][:2])
    f = R.Frame(q)
    R._gate(flags, f, "sign_drydock", q.p.z, q.w / 2 + 2.5)
    for sd in (-1, 1):
        gx, gy = f.P(-1.2, sd * (q.w / 2 + 2.5))
        light(c, "torch", gx, gy, q.p.z + 7.0)
    flags.build(c, "Dry Dock Flags And Gate", coll="Props", role="visual")


# ------------------------------------------------------------------ the Lucky Bone


def den(c, ground, taken):
    """The Lucky Bone, the smugglers' treasure hoard now (Blake, Nov 5: "more kid
    appropriate ... something pirate related. but not drugs, alcohol, gambling"; he picked
    the treasure hoard cave; jedge_hoard): the heaps of gold, the counting tables, the
    scales, the pearl, the gate; lanterns slung over it all, its talkers."""
    import jedge_hoard as H

    dx, dy, rx, ry = DEN
    z = DEN_Z - 0.6
    H.hoard(c, ground, taken)
    for j in range(8):
        a = j * math.tau / 8
        p0 = (dx + rx * 0.85 * math.cos(a), dy + ry * 0.85 * math.sin(a), z + 9.0)
        p1 = (dx + rx * 0.85 * math.cos(a + 2.4), dy + ry * 0.85 * math.sin(a + 2.4), z + 9.0)
        lantern_line(c, "Den String %d" % j, p0, p1, sag=2.0)
    for x, y in ((dx - 12.0, dy - 10.0), (dx + 14.0, dy + 12.0)):
        if paint.road_clear(c, x, y, 5.0) and taken.clear(x, y, 3.0):
            talkers(c, x, y, ground(x, y), 5, "den", r=7.0)


# ------------------------------------------------------------------ the alley and the bores


def bores(c, ground, s0, s1):
    """The underworld lived in, between the districts: timber shoring, pipes, puddles of
    oily water, lanterns both sides by turns. (Smugglers' Alley is the Rookery now:
    jedge_rookery.py.)"""
    sets = gp.timber_set(c, half=c.width / 2 + 3.4, height=10.4)
    s = s0 + 6.0
    k = 0
    while s < s1 - 6.0:
        q = c.at(s)
        if cavern_at(q.p.x, q.p.y)[0] is not None:
            s += 9.0
            k += 1
            continue
        rot = math.atan2(q.t.y, q.t.x)
        sd = 1 if k % 2 else -1
        if k % 2 == 0:
            c.place(sets, q.p.x, q.p.y, q.p.z - 0.3, rot=rot - math.pi / 2, role="visual")
        g = c.game(q.p.x + q.r.x * sd * (c.width / 2 + 3.0), q.p.y + q.r.y * sd * (c.width / 2 + 3.0), q.p.z + 5.0)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
        ex, ey = q.p.x + q.r.x * sd * (c.width / 2 + 2.6), q.p.y + q.r.y * sd * (c.width / 2 + 2.6)
        tube(c, "Pipe %d" % k, [(ex - q.t.x * 4.5, ey - q.t.y * 4.5, q.p.z + 6.5), (ex + q.t.x * 4.5, ey + q.t.y * 4.5, q.p.z + 6.5)], 0.35,
             "iron", n=6)
        if True:
            if k % 3 == 0:
                c.disc("Puddle %d" % k, q.p.x - q.r.x * sd * 3.0, q.p.y - q.r.y * sd * 3.0, 2.2, q.p.z + 0.04, c.lib("bog_water", "water"),
                       role="visual", n=12, wobble=0.25, seed=k)
            if k % 4 == 1:
                jx, jy = q.p.x + q.r.x * sd * (c.width / 2 + 1.8), q.p.y + q.r.y * sd * (c.width / 2 + 1.8)
                c.place(tp.barrel(c), jx, jy, ground(jx, jy) - 0.1, rot=k)
            if k % 5 == 2:
                # (a pair of lookouts, warming their hands at a brazier)
                jx, jy = q.p.x - q.r.x * sd * (c.width / 2 + 2.4), q.p.y - q.r.y * sd * (c.width / 2 + 2.4)
                light(c, "campfire", jx, jy, q.p.z + 0.1)
                for i in (-1, 1):
                    person(c, jx + q.t.x * i * 1.2, jy + q.t.y * i * 1.2, q.p.z, "huddle", jx, jy)
        s += 9.0
        k += 1


# ------------------------------------------------------------------ the sky


def sky_life(c, ground):
    """The Sky Islands' life: a shrine on Shrine Isle with its monks and pilgrims, banners
    and torches on every island, the Dragon Kingdom's guards and well-wishers at the Sky
    Gate; little dragons circling the islands, and a great dragon flying alongside you."""
    for k, (name, x, y, r, z) in enumerate(ISLES):
        top = L.isle_top(k)
        for j in range(6):
            a = j * math.tau / 6 + k
            bx, by = x + r * 0.72 * math.cos(a), y + r * 0.72 * math.sin(a)
            if not paint.road_clear(c, bx, by, 2.5):
                continue
            if j == 1 and paint.road_clear(c, bx, by, 4.5):
                # (a dragon pillar: review journey_cause 2 note 3, "lets make this a spectavular
                # dragon pillar")
                import jedge_sky as SK

                SK.dragon_pillar(c, bx, by, top, a + math.pi, k)
            elif j % 2:
                c.place(kp.banner_pole(c, h=9.0), bx, by, top, rot=a, role="visual")
            else:
                # (the Kingdom's banners: note 4, the flags had a paving stone's texture)
                c.place(tp.flag_pole(c, flag="keep_flag_blue" if k % 2 else "keep_banner", h=7.0), bx, by, top, role="visual")
                light(c, "torch", bx + 0.6, by, top + 2.2)
        if name == "Shrine Isle":
            sx, sy = x - 10.0, y + 2.0
            if paint.road_clear(c, sx, sy, 4.0):
                c.place(props.stele(c, 1), sx, sy, top, rot=0.4, role="both")
                for i in range(9):
                    b = i * math.tau / 9
                    person(c, sx + 3.2 * math.cos(b), sy + 3.2 * math.sin(b), top, "worship" if i % 3 else "monk", sx, sy, sky=True)
        if name == "Sky Gate Isle":
            for i in range(10):
                b = i * 0.6 - 2.6
                gx, gy = x + (r - 5.0) * math.cos(b), y + (r - 5.0) * math.sin(b)
                if paint.road_clear(c, gx, gy, 1.5):
                    person(c, gx, gy, top, "guard" if i % 3 == 0 else "wave", 0.0, 445.0, sky=True)
    # (the little dragons, circling)
    for k, (x, y, z, rad, n) in enumerate(((10.0, 230.0, -25.0, 40.0, 4), (-30.0, 320.0, -20.0, 34.0, 5), (4.0, 440.0, -10.0, 46.0, 6),
                                           (60.0, 300.0, -30.0, 28.0, 3))):
        g = c.game(x, y, z)
        c.entity("little_dragons", x=round(g[0], 1), y=round(g[1], 1), z=round(g[2], 1), radius=rad, count=n, speed=0.25 + 0.05 * k,
                 seed=k + 3, style="winged")
    # The great dragon: far off over the Kingdom while you're underground; out at the edge it
    # swoops down to meet you and flies alongside the islands to the gate.
    s0 = c.nearest(*L.ROUTE[L.START][:2])[0].s
    sm = c.nearest(*L.ROUTE[L.AT["mouth"]][:2])[0].s
    se = c.nearest(*L.ROUTE[L.END][:2])[0].s
    keys = []
    for s, (x, y, z) in ((s0, (200.0, 800.0, 120.0)), (lerp(s0, sm, 0.5), (-160.0, 720.0, 140.0)), (sm - 40.0, (90.0, 300.0, 30.0)),
                         (sm + 20.0, (60.0, 236.0, -22.0)), (sm + 120.0, (30.0, 320.0, -14.0)), (sm + 220.0, (70.0, 400.0, -10.0)),
                         (se, (40.0, 470.0, 0.0)), (se + 120.0, (0.0, 640.0, 60.0))):
        g = c.game(x, y, z)
        keys.append([round(s, 1), round(g[0], 1), round(g[1], 1), round(g[2], 1)])
    c.entity("isles_dragon", keys=keys, length=round(c.length, 1), size=1.2, style="winged",
             colors={"body": "#8a2418", "belly": "#e8b048"})
    c.entity("villagers", list=SKY_CROWD, palette="skycroc")
