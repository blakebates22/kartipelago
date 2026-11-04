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
import gulch_props as gp
import swamp_props as sw
import region_paint as paint
import jedge_layout as L
from jedge_layout import (BASIN, BAZAAR, BAZ_Z, CANAL, DEN, DEN_Z, DOCK_FLOOR, DOCK_WATER, DOCKS, ISLES, PIT, PIT_FLOOR,
                          PIT_R, cavern_at, ellipse, pit_ground, spiral_at)

CROWD = []  # the black market's people (one instanced crowd)
SKY_CROWD = []  # the sky islands' (in the Dragon Kingdom's colours)
CROWD_N = [0, 0]  # how many people, how many talkers


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
    bp.string_line(c, name, p0, p1, sag, kind="lanterns", coll="Props")


def ok(c, taken, x, y, r, margin=2.0):
    return paint.road_clear(c, x, y, r + margin) and taken.clear(x, y, r)


def dress(c, ground, s0, s1):
    taken = paint.Taken()
    grotto(c, ground, taken)
    docks(c, ground, taken)
    bazaar(c, ground, taken)
    pits(c, ground, taken)
    den(c, ground, taken)
    bores(c, ground, s0, s1)
    c.entity("villagers", list=CROWD, palette="sump")


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
    # The cranes on the quay (between the road and the water), jibs over the basin.
    for j, (x, y) in enumerate(((-18.0, -334.0), (-19.0, -314.0), (-22.0, -280.0))):
        z = ground(x, y)
        a = math.atan2(by - y, bx - x) + (j - 1) * 0.25
        reach = 11.0
        box(c, "Crane Tower %d" % j, x, y, 1.2, 1.2, z, z + 15.0, ("weathered_timber", "wall"), rot=a)
        tube(c, "Crane Jib %d" % j, [(x - 2.0 * math.cos(a), y - 2.0 * math.sin(a), z + 15.0),
                                     (x + reach * math.cos(a), y + reach * math.sin(a), z + 15.0)], 0.3, "weathered_timber", n=5)
        tube(c, "Crane Stay %d" % j, [(x, y, z + 18.0), (x + reach * math.cos(a), y + reach * math.sin(a), z + 15.2)], 0.05, "rope_rail")
        box(c, "Crane Cab %d" % j, x, y, 2.2, 2.2, z + 11.0, z + 14.0, ("wreck_planks", "wall"), rot=a, role="visual")
        g = c.game(x, y, z + 15.0)
        c.entity("crane", x=round(g[0], 2), y=round(g[1], 2), z=round(g[2], 2), heading=round(math.pi / 2 - a, 3), reach=reach,
                 drop=round(15.0 - (DOCK_WATER - z) - 1.0, 1), swing=0.6, period=round(9.0 + 2.5 * j, 1), load="net" if j % 2 else "crate")
        taken.add(x, y, 2.5)
        for k in range(3):
            px, py = x + 2.8 * math.cos(a + 2.2 + k), y + 2.8 * math.sin(a + 2.2 + k)
            person(c, px, py, ground(px, py), "worker", x + reach * math.cos(a), y + reach * math.sin(a))
    # Warehouses along the docks' east and north sides, the Customs House on the canal.
    sheds = [(26.0, -336.0, 0.3, "siding_brown"), (40.0, -318.0, 1.2, "siding_grey"), (-38.0, -264.0, 0.1, "siding_green"),
             (-60.0, -278.0, 1.5, "siding_red"), (-12.0, -258.0, 0.0, "siding_ochre"), (34.0, -282.0, 0.2, "siding_brown")]
    for j, (x, y, rot, mat) in enumerate(sheds):
        if not ok(c, taken, x, y, 6.0, 1.0) or ellipse(x, y, *DOCKS) > 0.9:
            continue
        z = ground(x, y)
        box(c, "Warehouse %d" % j, x, y, 6.5, 4.5, z - 0.5, z + 7.0, (mat, "wall"), rot=rot)
        box(c, "Warehouse Roof %d" % j, x, y, 7.2, 5.2, z + 7.0, z + 7.6, ("tin_roof", "wall"), rot=rot, role="visual")
        ca, sa = math.cos(rot), math.sin(rot)
        for sd in (-1, 1):
            # (its big doors open, a lamp over them, crates spilling out)
            dx, dy = x - sa * sd * 4.55, y + ca * sd * 4.55
            box(c, "Warehouse Door %d %d" % (j, sd), dx, dy, 2.4, 0.1, z, z + 4.2, ("window_dark", "wall"), rot=rot, role="visual")
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
        box(c, "Customs House", x, y, 4.0, 3.0, z - 0.5, z + 5.0, ("cabin_wall", "wall"))
        box(c, "Customs House Roof", x, y, 4.6, 3.6, z + 5.0, z + 5.5, ("shingle_roof", "wall"), role="visual")
        box(c, "Customs Window", x, y - 3.05, 1.8, 0.1, z + 1.2, z + 2.6, ("window_warm", "wall"), role="visual")
        c.place(tp.flag_pole(c, flag="wreck_flag", h=8.0), x + 3.4, y, z, role="visual")
        light(c, "lantern", x, y - 3.6, z + 3.2)
        taken.add(x, y, 5.0)
        for k in range(7):
            px, py = x - 1.0 + k * 1.3, y - 4.6 - 0.4 * (k % 2)
            person(c, px, py, ground(px, py), "queue", x, y)
        person(c, x, y - 3.4, z, "merchant", x, y - 8.0)
    # The fish market on the quay's north side: stalls of the black water's catch.
    for j in range(5):
        x, y = -30.0 + j * 5.0, cy + hw + 8.0 + (j % 2)
        if not ok(c, taken, x, y, 2.0, 1.0):
            continue
        z = ground(x, y)
        box(c, "Fish Stall %d" % j, x, y, 2.0, 0.9, z - 0.2, z + 1.0, ("wood_dock", "wall"))
        cloth(c, "Fish Awning %d" % j, [(x - 2.2, y + 1.4, z + 3.0), (x + 2.2, y + 1.4, z + 3.0), (x + 2.2, y - 1.4, z + 2.4),
                                        (x - 2.2, y - 1.4, z + 2.4)], ("awning_teal", "canvas_torn", "awning_sea")[j % 3])
        for k in range(3):
            egg(c, "Fish %d %d" % (j, k), x - 1.0 + k, y, z + 1.0, 0.25, ("cove_coral_pink", "isle_sea", "bog_moss_ground")[k])
        person(c, x, y + 1.6, z, "merchant", x, y - 4.0)
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
    lantern strings across the road; tents, rugs and cookfires behind; the music square with
    its band, dancers and a conga; the Broker's ship hanging over it all."""
    bx, by, brx, bry = BAZAAR
    s_in = [q for q in c.S if ellipse(q.p.x, q.p.y, bx, by, brx, bry) < 0.92 and abs(q.p.z - BAZ_Z) < 1.0]
    s_in = sorted(s_in, key=lambda q: q.s)
    mats = ("awning_red", "awning_teal", "canvas_torn", "awning_sun", "awning_rose", "tent_cloth_red", "awning_green", "rug")
    k = 0
    if s_in:
        s = s_in[0].s + 4.0
        while s < s_in[-1].s - 4.0:
            q = c.at(s)
            rot = math.atan2(q.t.y, q.t.x)
            for sd in (-1, 1):
                off = q.w / 2 + 4.6
                x, y = q.p.x + q.r.x * sd * off, q.p.y + q.r.y * sd * off
                if not ok(c, taken, x, y, 2.4, 1.6) or ellipse(x, y, bx, by, brx, bry) > 0.95:
                    continue
                z = ground(x, y)
                # (the counter along the road, its front to the road)
                stall(c, "Stall %d" % k, x, y, z, rot, LOOT[k % len(LOOT)], mats[k % len(mats)])
                if LOOT[k % len(LOOT)] == "food":
                    light(c, "chimney", x + q.r.x * sd * 1.2, y + q.r.y * sd * 1.2, z + 1.8)
                taken.add(x, y, 2.6)
                mx, my = x + q.r.x * sd * 1.3, y + q.r.y * sd * 1.3
                person(c, mx, my, z, "merchant", q.p.x, q.p.y)
                for j in range(2 + k % 2):
                    px = x - q.r.x * sd * 1.5 + q.t.x * (j - 1) * 1.1
                    py = y - q.r.y * sd * 1.5 + q.t.y * (j - 1) * 1.1
                    person(c, px, py, ground(px, py), ("queue", "huddle", "wave")[(j + k) % 3], x, y)
                k += 1
            s += 6.5
    # Lantern strings across the road on tall poles, every so often.
    s = s_in[0].s + 6.0 if s_in else 0.0
    j = 0
    while s_in and s < s_in[-1].s - 6.0:
        q = c.at(s)
        ends = []
        for sd in (-1, 1):
            x, y = q.p.x + q.r.x * sd * (q.w / 2 + 2.0), q.p.y + q.r.y * sd * (q.w / 2 + 2.0)
            z = ground(x, y)
            ends.append((x, y, z + 7.8))
        if True:
            for sd, (x, y, z) in zip((-1, 1), ends):
                box(c, "Lantern Pole %d %d" % (j, sd), x, y, 0.12, 0.12, z - 7.8, z + 0.2, ("weathered_timber", "wall"))
            lantern_line(c, "Lantern String %d" % j, ends[0], ends[1], sag=1.4)
        s += 12.0
        j += 1
    # Behind the stalls: tents, rugs, crates, cookfires, the crowd milling.
    for j in range(70):
        a = j * 2.399 + 0.2
        r = 0.2 + 0.72 * ((j * 0.618) % 1.0)
        x, y = bx + brx * r * math.cos(a), by + bry * r * math.sin(a)
        if not ok(c, taken, x, y, 2.6, 2.0):
            continue
        z = ground(x, y)
        kind = j % 5
        if kind == 0:
            box(c, "Tent %d" % j, x, y, 2.4, 2.4, z, z + 2.4, (("tent_cloth_red", "tent_cloth", "canvas_sun")[j % 3], "wall"), rot=a)
            cone(c, "Tent Roof %d" % j, x, y, 3.4, z + 2.4, 2.2, (("tent_cloth_red", "tent_cloth", "canvas_sun")[j % 3], "wall"), segs=4,
                 role="visual")
            light(c, "lantern", x + 2.8 * math.cos(a), y + 2.8 * math.sin(a), z + 2.4)
            person(c, x + 3.0 * math.cos(a + 0.4), y + 3.0 * math.sin(a + 0.4), z, "merchant", x, y)
        elif kind == 1:
            light(c, "campfire", x, y, z + 0.2)
            light(c, "chimney", x, y, z + 1.5)
            for i in range(5):
                b = i * math.tau / 5 + j
                person(c, x + 2.2 * math.cos(b), y + 2.2 * math.sin(b), z, ("huddle", "merchant", "huddle", "queue", "huddle")[i], x, y)
        elif kind == 2:
            for i in range(3):
                box(c, "Rug Pile %d %d" % (j, i), x + 0.3 * i, y - 0.2 * i, 1.4, 0.9, z + 0.3 * i, z + 0.3 * i + 0.3,
                    (("rug", "royal_carpet", "keep_carpet")[i], "wall"), rot=a + 0.3 * i, role="visual")
            person(c, x + 2.0 * math.cos(a), y + 2.0 * math.sin(a), z, "merchant", x, y)
            person(c, x - 2.2 * math.cos(a), y - 2.2 * math.sin(a), z, "queue", x, y)
        elif kind == 3:
            c.place(gp.crate_stack(c, j % 4), x, y, z, rot=a, role="both")
            person(c, x + 1.8 * math.cos(a), y + 1.8 * math.sin(a), z, "hauler", x, y)
        else:
            for i in range(4):
                b = i * math.tau / 4 + j * 0.3
                person(c, x + 1.0 * math.cos(b), y + 1.0 * math.sin(b), z, ("huddle", "wave", "huddle", "cheer")[i], x, y)
        taken.add(x, y, 3.0)
    # The music square: the band, dancers, a conga round it.
    best = None
    for j in range(40):
        a = j * 2.399
        r = 0.15 + 0.6 * ((j * 0.618) % 1.0)
        x, y = bx + brx * r * math.cos(a), by + bry * r * math.sin(a)
        if paint.road_clear(c, x, y, 10.0)  and (best is None or paint.road_clear(c, x, y, 13.0)):
            best = (x, y)
            if paint.road_clear(c, x, y, 13.0):
                break
    if best:
        x, y = best
        z = ground(x, y)
        g = c.game(x, y, z)
        c.entity("conga", x=round(g[0], 2), y=round(g[1], 2), z=round(g[2], 2), count=10, radius=6.5, speed=0.35)
        for i in range(4):
            b = i * 0.5 - 0.75
            person(c, x + 2.0 * math.cos(b), y + 2.0 * math.sin(b), z, "musician", x, y)
        c.place(bp.drum(c), x, y, z, role="visual")
        for i in range(8):
            b = i * math.tau / 8
            person(c, x + 9.0 * math.cos(b), y + 9.0 * math.sin(b), z, "dancer" if i % 2 else "cheer", x, y)
        light(c, "campfire", x + 3.0, y + 3.0, z + 0.2)
        taken.add(x, y, 10.0)
    # Banners from the roof, the soot of the cookfires.
    for j in range(14):
        a = j * math.tau / 14
        x, y = bx + brx * 0.7 * math.cos(a), by + bry * 0.7 * math.sin(a)
        z0 = BAZ_Z + 20.0
        cloth(c, "Bazaar Banner %d" % j, [(x - 1.2 * math.sin(a), y + 1.2 * math.cos(a), z0), (x + 1.2 * math.sin(a), y - 1.2 * math.cos(a), z0),
                                          (x + 1.0 * math.sin(a), y - 1.0 * math.cos(a), z0 - 7.0), (x - 1.0 * math.sin(a), y + 1.0 * math.cos(a), z0 - 7.0)],
              ("banner_red", "banner_teal", "em_banner", "meteor_banner")[j % 4])
    for j, (x, y) in enumerate(((84.0, -150.0), (132.0, -130.0), (90.0, -110.0), (132.0, -170.0))):
        if paint.road_clear(c, x, y, 6.0):
            talkers(c, x, y, ground(x, y), 6, "bazaar", r=9.0)
    broker(c)


def broker(c):
    """The Broker's palace: a gilded ship hanging over the Night Bazaar on four chains from
    the roof, lit from within, its stern galleries gold, a gangway hanging down; the Broker
    (a huge croc) sprawled on its deck, watching the market."""
    sx, sy = BAZAAR[0] + 8.0, BAZAAR[1] + 4.0
    z = BAZ_Z + 17.0
    rot = 1.4
    ca, sa = math.cos(rot), math.sin(rot)

    def at(lx, ly):
        return sx + lx * ca - ly * sa, sy + lx * sa + ly * ca

    box(c, "Broker Hull", sx, sy, 16.0, 5.0, z - 4.0, z + 2.0, ("wreck_hull", "wall"), rot=rot, role="visual")
    box(c, "Broker Keel", sx, sy, 13.0, 2.0, z - 6.0, z - 4.0, ("wreck_hull", "wall"), rot=rot, role="visual")
    box(c, "Broker Deck", sx, sy, 16.4, 5.4, z + 2.0, z + 2.4, ("plank_deck", "wall"), rot=rot, role="visual")
    bx, by = at(-8.0, 0.0)
    box(c, "Broker Cabin", bx, by, 6.0, 4.6, z + 2.4, z + 8.0, ("door_wood", "wall"), rot=rot, role="visual")
    box(c, "Broker Cabin Roof", bx, by, 6.6, 5.2, z + 8.0, z + 8.8, ("gold_trim", "wall"), rot=rot, role="visual")
    for w in (-3.0, -1.0, 1.0, 3.0):
        for sd in (-1, 1):
            wx, wy = at(-8.0 + w, sd * 4.65)
            box(c, "Broker Window %d %d" % (int(w), sd), wx, wy, 0.6, 0.08, z + 4.0, z + 6.6, ("window_warm", "wall"), rot=rot, role="visual")
    gx, gy = at(-16.2, 0.0)
    box(c, "Broker Gallery", gx, gy, 0.4, 5.0, z - 1.0, z + 7.0, ("gold_trim", "wall"), rot=rot, role="visual")
    for sd, (lx, ly) in ((-1, (-3.6, -2.3)), (1, (6.2, -2.3))):
        mx, my = at(lx, ly)
        box(c, "Broker Lantern %d" % sd, mx, my, 0.5, 0.5, z + 2.4, z + 4.0, ("lantern_amber", "wall"), role="visual")
        light(c, "lantern", mx, my, z + 4.4)
    for lx, ly in ((-14.0, -4.0), (-14.0, 4.0), (14.0, -4.0), (14.0, 4.0)):
        px, py = at(lx, ly)
        tx, ty = at(lx * 1.5, ly * 2.5)
        tube(c, "Broker Chain %d %d" % (int(lx), int(ly)), [(px, py, z + 2.0), (tx, ty, BAZ_Z + 27.5)], 0.4, "iron", n=6)
    bx, by = at(-1.5, 0.0)
    c.place(sw.broker_croc(c), bx, by, z + 2.4, rot=rot, scale=1.5, role="visual", name="The Broker")
    gx, gy = at(10.0, 5.0)
    box(c, "Broker Gangway", gx, gy, 0.8, 0.3, z - 14.0, z + 2.0, ("weathered_timber", "wall"), rot=rot, role="visual")
    # (his guards on deck)
    for lx in (-4.0, 4.0, 9.0):
        px, py = at(lx, 2.2)
        person(c, px, py, z + 2.4, "guard", sx, sy - 40.0)


# ------------------------------------------------------------------ the Fighting Pits


def pits(c, ground, taken):
    """The Fighting Pits: the arena, the road corkscrewing down its wall through the
    stands (benches packed with the cheering crowd all the way down), the fight ring on
    the sand floor (two brawlers in it, the crowd round the ropes), the bookies' booths
    with their queues, braziers, banners from the roof, cages, a great skull over the
    gate."""
    px, py = PIT
    f0, f1, f2 = PIT_R
    taken.add(px, py, f0 - 1.0)
    # The ring: a raised platform, corner posts, ropes; two brawlers; the referee.
    z = PIT_FLOOR
    box(c, "Fight Ring", px, py, 6.5, 6.5, z - 0.5, z + 1.2, ("gulch_sand", "road"))
    box(c, "Fight Ring Skirt", px, py, 6.7, 6.7, z - 0.5, z + 1.0, ("banner_red", "wall"), role="visual")
    corners = [(px + sx * 6.3, py + sy * 6.3) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for k, (x, y) in enumerate(corners):
        box(c, "Ring Post %d" % k, x, y, 0.2, 0.2, z + 1.2, z + 3.0, ("iron", "wall"), role="visual")
    for h in (1.9, 2.6):
        for k in range(4):
            (ax, ay), (bx_, by_) = corners[k], corners[(k + 1) % 4]
            tube(c, "Ring Rope %d %d" % (k, int(h * 10)), [(ax, ay, z + h), (bx_, by_, z + h)], 0.05, "banner_red", n=3)
    for k, (dx, h) in enumerate(((-1.8, 0.4), (1.8, 0.4 + math.pi))):
        g = c.game(px + dx, py, z + 1.2)
        c.entity("partygoer", x=round(g[0], 2), y=round(g[1], 2), z=round(g[2], 2), heading=round(math.pi / 2 if dx < 0 else -math.pi / 2, 3),
                 dance="hop", variant=3 + k * 2)
    person(c, px, py + 3.5, z + 1.2, "wave", px, py)
    for k in range(4):
        bx_, by_ = corners[k][0] + (corners[k][0] - px) * 0.5, corners[k][1] + (corners[k][1] - py) * 0.5
        c.place(sw.stone_brazier(c), bx_, by_, z, role="visual")
        light(c, "campfire", bx_, by_, z + 2.0)
    # Ringside: the crowd packed round the ropes.
    for k in range(44):
        a = k * math.tau / 44
        for rr_ in (10.5, 12.5):
            if (k + int(rr_)) % 3 == 0:
                continue
            x, y = px + rr_ * math.cos(a), py + rr_ * math.sin(a)
            person(c, x, y, z, "cheer", px, py)
    # The bookies' booths round the floor, queues at them, odds boards.
    for k in range(6):
        a = k * math.tau / 6 + 0.25
        x, y = px + 22.0 * math.cos(a), py + 22.0 * math.sin(a)
        if not paint.road_clear(c, x, y, 3.0):
            continue
        rot = a + math.pi / 2
        stall(c, "Bookie %d" % k, x, y, z, rot, "gold", ("awning_red", "tent_cloth_red", "awning_sun")[k % 3])
        box(c, "Odds Board %d" % k, x + 1.6 * math.cos(a), y + 1.6 * math.sin(a), 2.0, 0.12, z + 1.2, z + 4.4, ("window_lit", "wall"),
            rot=rot, role="visual")
        person(c, x + 1.0 * math.cos(a), y + 1.0 * math.sin(a), z, "merchant", px, py)
        for i in range(5):
            qx, qy = x - (1.8 + i * 1.0) * math.cos(a), y - (1.8 + i * 1.0) * math.sin(a)
            person(c, qx, qy, z, "queue", x, y)
    for k, a in enumerate((1.3, 3.4, 5.2)):
        x, y = px + 28.0 * math.cos(a), py + 28.0 * math.sin(a)
        if paint.road_clear(c, x, y, 5.0):
            # (a cage: the next challenger, a croc, pacing)
            for i in range(8):
                b = i * math.tau / 8
                box(c, "Cage Bar %d %d" % (k, i), x + 2.6 * math.cos(b), y + 2.6 * math.sin(b), 0.08, 0.08, z, z + 3.4, ("iron", "wall"),
                    role="visual")
            box(c, "Cage Top %d" % k, x, y, 2.8, 2.8, z + 3.4, z + 3.6, ("iron", "wall"), role="visual")
            box(c, "Cage Floor %d" % k, x, y, 2.8, 2.8, z - 0.2, z + 0.2, ("rail_iron", "wall"))
            c.place(sw.croc(c), x, y, z + 0.6, rot=a, scale=0.6, role="visual")
            for i in range(3):
                b = a + math.pi + (i - 1) * 0.4
                person(c, x + 4.0 * math.cos(b), y + 4.0 * math.sin(b), z, "cheer" if i != 1 else "huddle", x, y)
    for j, a in enumerate((0.8, 2.7, 4.6)):
        x, y = px + 16.0 * math.cos(a), py + 16.0 * math.sin(a)
        talkers(c, x, y, z, 5, "pits", r=6.0)
    # The stands: benches down the slope on both sides of the spiral, packed.
    n = 0
    for k in range(78):
        a = -60.0 - 300.0 * (k + 0.5) / 78
        r_road, z_road = spiral_at(a)
        ra = math.radians(a)
        rows = []
        r = r_road + 10.5
        while r < f2 - 2.0:
            rows.append(r)
            r += 3.0
        r = r_road - 10.5
        while r > f0 + 2.0:
            rows.append(r)
            r -= 3.0
        for r in rows:
            x, y = px + r * math.cos(ra), py + r * math.sin(ra)
            if not paint.road_clear(c, x, y, 2.0):
                continue
            zt = pit_ground(x, y)
            box(c, "Bench %d %d" % (k, int(r)), x, y, 1.0, 2.0, zt - 1.6, zt + 0.35, (("ember_ashlar", "sandstone_block")[int(r) % 2], "wall"), rot=ra + math.pi / 2,
                role="visual")
            if (k + int(r)) % 3 == 0 or n > 420:
                continue
            for i in (-1, 1):
                sx, sy = x + math.cos(ra + math.pi / 2) * i * 0.9, y + math.sin(ra + math.pi / 2) * i * 0.9
                person(c, sx, sy, zt + 0.35, "cheer" if (k + i) % 4 else "wave", px, py)
                n += 1
    # Torches along the spiral's rail, every few metres, both sides by turns.
    for k in range(40):
        a = -60.0 - 300.0 * (k + 0.5) / 40
        r_road, z_road = spiral_at(a)
        ra = math.radians(a)
        r = r_road + (8.6 if k % 2 else -8.6)
        light(c, "torch", px + r * math.cos(ra), py + r * math.sin(ra), z_road + 2.2)
    # Braziers on the stands, banners down the walls, the great skull over the gate.
    for k in range(16):
        a = k * math.tau / 16 + 0.1
        x, y = px + (f2 - 4.0) * math.cos(a), py + (f2 - 4.0) * math.sin(a)
        if paint.road_clear(c, x, y, 2.5):
            zt = pit_ground(x, y)
            c.place(sw.stone_brazier(c), x, y, zt, rot=a, role="visual")
            light(c, "campfire", x, y, zt + 2.0)
        z0 = -12.0
        x, y = px + (f2 - 1.5) * math.cos(a + 0.2), py + (f2 - 1.5) * math.sin(a + 0.2)
        cloth(c, "Pit Banner %d" % k, [(x - 1.8 * math.sin(a), y + 1.8 * math.cos(a), z0), (x + 1.8 * math.sin(a), y - 1.8 * math.cos(a), z0),
                                       (x + 1.4 * math.sin(a), y - 1.4 * math.cos(a), z0 - 12.0), (x - 1.4 * math.sin(a), y + 1.4 * math.cos(a), z0 - 12.0)],
              ("banner_red", "ember_banner", "banner_red", "keep_banner_dark")[k % 4])
    q, _ = c.nearest(*L.ROUTE[L.AT["pit_gate"]][:2])
    rot = math.atan2(q.t.y, q.t.x)
    c.place(sw.great_skull(c), q.p.x - q.t.x * 6.0, q.p.y - q.t.y * 6.0, q.p.z + 9.0, rot=rot, scale=0.42, role="visual")
    for sd in (-1, 1):
        gx, gy = q.p.x + q.r.x * sd * (q.w / 2 + 2.5), q.p.y + q.r.y * sd * (q.w / 2 + 2.5)
        box(c, "Pit Gate Post %d" % sd, gx, gy, 1.0, 1.0, q.p.z - 1.0, q.p.z + 9.5, ("bone_ivory", "wall"), rot=rot)
        light(c, "torch", gx - q.t.x * 1.2, gy - q.t.y * 1.2, q.p.z + 7.0)
    # (Dust over the sand, the braziers' smoke.)
    for k in range(4):
        a = k * math.tau / 4 + 0.6
        light(c, "chimney", px + 18.0 * math.cos(a), py + 18.0 * math.sin(a), PIT_FLOOR + 3.0)


# ------------------------------------------------------------------ the Lucky Bone


def den(c, ground, taken):
    """The Lucky Bone, the gambling den: card tables and dice tables crowded round, a
    wheel of fortune, gold heaped up and chests of it, the bar, the stage with its DJ and
    dancing dinos, lantern strings, the house's guards."""
    dx, dy, rx, ry = DEN
    z = DEN_Z - 0.6
    tables = []
    for j in range(36):
        a = j * 2.399 + 0.4
        r = 0.25 + 0.65 * ((j * 0.618) % 1.0)
        x, y = dx + rx * r * math.cos(a), dy + ry * r * math.sin(a)
        if ok(c, taken, x, y, 2.4, 1.6):
            tables.append((x, y, a, j))
            taken.add(x, y, 3.0)
    for k, (x, y, a, j) in enumerate(tables):
        zz = ground(x, y)
        kind = k % 4
        if kind in (0, 1):
            # (a card table, players round it, the dealer)
            box(c, "Card Table %d" % k, x, y, 1.3, 0.8, zz, zz + 0.9, ("keep_carpet" if kind else "royal_carpet", "wall"), rot=a)
            for i in range(4):
                b = a + i * math.pi / 2
                person(c, x + 1.8 * math.cos(b), y + 1.8 * math.sin(b), zz, "merchant" if i == 0 else "huddle", x, y)
            light(c, "lantern", x, y, zz + 3.0)
        elif kind == 2:
            # (the dice: bones, crowded round, a winner cheering)
            box(c, "Dice Pit %d" % k, x, y, 1.6, 1.6, zz, zz + 0.5, ("bog_boards", "wall"), rot=a)
            for i in range(3):
                box(c, "Die %d %d" % (k, i), x + 0.5 * (i - 1), y + 0.3 * (i % 2), 0.2, 0.2, zz + 0.5, zz + 0.9, ("bone_ivory", "wall"),
                    rot=a + i, role="visual")
            for i in range(6):
                b = a + i * math.tau / 6
                person(c, x + 2.3 * math.cos(b), y + 2.3 * math.sin(b), zz, "cheer" if i == 2 else "huddle", x, y)
        else:
            c.place(tp.gold_pile(c) if j % 2 else tp.chest(c), x, y, zz, rot=a, role="visual")
            person(c, x + 2.0 * math.cos(a), y + 2.0 * math.sin(a), zz, "guard", x, y)
    # The wheel of fortune, standing, by the road.
    x, y = dx + rx * 0.55, dy - ry * 0.1
    if ok(c, taken, x, y, 2.5, 1.0):
        zz = ground(x, y)
        box(c, "Fortune Wheel Stand", x, y, 0.3, 0.3, zz, zz + 3.0, ("gold_trim", "wall"))
        g = c.game(x, y, zz + 4.2)
        c.entity("waterwheel", x=round(g[0], 2), y=round(g[1], 2), z=round(g[2], 2), heading=0.0, radius=2.0, speed=1.4)
        for i in range(5):
            person(c, x - 3.0 + 1.4 * i, y - 3.2, zz, "cheer" if i % 2 else "queue", x, y)
        taken.add(x, y, 3.5)
    # The stage: the DJ and the dancing dinos.
    x, y = dx - rx * 0.55, dy + ry * 0.25
    if ok(c, taken, x, y, 5.0, 1.0):
        zz = ground(x, y)
        c.place(bp.stage(c), x, y, zz, rot=0.0, role="both")
        g = c.game(x, y + 1.0, zz + 1.0)
        c.entity("partygoer", x=round(g[0], 2), y=round(g[1], 2), z=round(g[2], 2), heading=0.0, dance="dj", variant=1)
        for i, dance in enumerate(("bounce", "sway", "hop", "wave", "chill", "bounce")):
            b = i * 0.5 - 1.25
            g = c.game(x + 8.0 * math.sin(b), y - 7.0 - 1.5 * math.cos(b), zz)
            c.entity("partygoer", x=round(g[0], 2), y=round(g[1], 2), z=round(g[2], 2), heading=round(math.pi, 3), dance=dance, variant=i + 2)
        taken.add(x, y, 9.0)
    # The bar along the wall, lantern strings over everything.
    x, y = dx + rx * 0.2, dy + ry * 0.7
    if ok(c, taken, x, y, 4.0, 1.0):
        zz = ground(x, y)
        box(c, "Bar", x, y, 5.0, 0.8, zz, zz + 1.1, ("door_wood", "wall"))
        for i in range(8):
            cone(c, "Bottle %d" % i, x - 4.0 + i * 1.1, y, 0.12, zz + 1.1, 0.5, (("lantern_green", "lantern_amber", "lantern_red")[i % 3], "wall"),
                 segs=5, role="visual")
        person(c, x, y + 1.4, zz, "merchant", x, y - 5.0)
        for i in range(6):
            person(c, x - 4.0 + 1.6 * i, y - 1.6, zz, "huddle", x, y)
    for j in range(8):
        a = j * math.tau / 8
        p0 = (dx + rx * 0.85 * math.cos(a), dy + ry * 0.85 * math.sin(a), z + 9.0)
        p1 = (dx + rx * 0.85 * math.cos(a + 2.4), dy + ry * 0.85 * math.sin(a + 2.4), z + 9.0)
        lantern_line(c, "Den String %d" % j, p0, p1, sag=2.0)
    for x, y in ((dx - 12.0, dy - 10.0), (dx + 14.0, dy + 12.0)):
        if paint.road_clear(c, x, y, 5.0):
            talkers(c, x, y, ground(x, y), 5, "den", r=7.0)
    # (the house's sign over the road: a gilded bone)
    q, _ = c.nearest(*L.ROUTE[L.AT["den0"]][:2])
    rot = math.atan2(q.t.y, q.t.x)
    for sd in (-1, 1):
        gx, gy = q.p.x + q.r.x * sd * (q.w / 2 + 2.0), q.p.y + q.r.y * sd * (q.w / 2 + 2.0)
        box(c, "Den Gate Post %d" % sd, gx, gy, 0.6, 0.6, q.p.z - 0.5, q.p.z + 8.0, ("gold_trim", "wall"), rot=rot)
        person(c, gx - q.t.x * 1.5, gy - q.t.y * 1.5, ground(gx, gy), "guard", q.p.x, q.p.y)
    box(c, "Den Gate Sign", q.p.x, q.p.y, 0.6, q.w / 2 + 2.6, q.p.z + 8.0, q.p.z + 9.6, ("gold_trim", "wall"), rot=rot, role="visual")
    c.place(sw.femur(c), q.p.x, q.p.y, q.p.z + 10.0, rot=rot + math.pi / 2, scale=1.2, role="visual")


# ------------------------------------------------------------------ the alley and the bores


def bores(c, ground, s0, s1):
    """The underworld lived in, between the districts: timber shoring, pipes, puddles of
    oily water, lanterns both sides by turns; and in Smugglers' Alley (the S-bends down to
    the Drop) doors and windows in its walls, laundry across overhead, folk in doorways."""
    sets = gp.timber_set(c, half=c.width / 2 + 3.4, height=10.4)
    a0 = c.nearest(*L.ROUTE[L.AT["dock3"]][:2])[0].s
    a1 = c.nearest(*L.ROUTE[L.AT["stair1"]][:2])[0].s
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
        if a0 <= s <= a1:
            # (the alley: a door in the wall, lit windows, folk in the doorway, washing
            # strung across overhead)
            dx, dy = q.p.x + q.r.x * sd * (c.width / 2 + 3.9), q.p.y + q.r.y * sd * (c.width / 2 + 3.9)
            box(c, "Alley Door %d" % k, dx, dy, 1.0, 0.2, q.p.z - 0.2, q.p.z + 2.6, ("door_wood", "wall"), rot=rot, role="visual")
            for w in (-2.4, 2.4):
                box(c, "Alley Window %d %d" % (k, int(w)), dx + q.t.x * w, dy + q.t.y * w, 0.6, 0.2, q.p.z + 1.4, q.p.z + 2.4,
                    ("window_warm", "wall"), rot=rot, role="visual")
            for i in range(2):
                px, py = dx - q.r.x * sd * (1.0 + 0.6 * i) + q.t.x * (i - 0.5) * 1.4, dy - q.r.y * sd * (1.0 + 0.6 * i) + q.t.y * (i - 0.5) * 1.4
                person(c, px, py, q.p.z, ("huddle", "wave", "merchant")[(k + i) % 3], q.p.x, q.p.y)
            if k % 2:
                p0 = (q.p.x - q.r.x * (c.width / 2 + 3.6), q.p.y - q.r.y * (c.width / 2 + 3.6), q.p.z + 8.2)
                p1 = (q.p.x + q.r.x * (c.width / 2 + 3.6), q.p.y + q.r.y * (c.width / 2 + 3.6), q.p.z + 8.2)
                tube(c, "Wash Line %d" % k, [p0, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, q.p.z + 7.4), p1], 0.04, "rope_rail", n=3)
                for f in range(5):
                    t = (f + 0.5) / 5
                    x, y = lerp(p0[0], p1[0], t), lerp(p0[1], p1[1], t)
                    zz = q.p.z + 8.2 - 0.8 * (1.0 - (2 * t - 1) ** 2)
                    ux, uy = q.r.x * 0.55, q.r.y * 0.55
                    cloth(c, "Wash %d %d" % (k, f), [(x - ux, y - uy, zz), (x + ux, y + uy, zz), (x + ux, y + uy, zz - 1.3), (x - ux, y - uy, zz - 1.1)],
                          ("rug", "canvas_torn", "awning_red", "sail_cloth", "awning_teal")[(k + f) % 5])
        else:
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
    # The Stair's foot, where the alley comes down into the Night Bazaar: a great timber
    # gate hung with banners and a lantern string, braziers either side, hawkers and
    # touts calling you in.
    q, _ = c.nearest(*L.ROUTE[L.AT["stair2"]][:2])
    rot = math.atan2(q.t.y, q.t.x)
    tops = []
    for sd in (-1, 1):
        x, y = q.p.x + q.r.x * sd * (q.w / 2 + 2.2), q.p.y + q.r.y * sd * (q.w / 2 + 2.2)
        z = ground(x, y)
        box(c, "Bazaar Gate Post %d" % sd, x, y, 0.55, 0.55, z - 0.5, q.p.z + 10.5, ("weathered_timber", "wall"), rot=rot)
        light(c, "campfire", x + q.t.x * 2.5, y + q.t.y * 2.5, z + 0.1)
        tops.append((x, y, q.p.z + 10.0))
        for i in range(4):
            px, py = x + q.t.x * (4.0 + 1.6 * i) + q.r.x * sd * 0.8, y + q.t.y * (4.0 + 1.6 * i) + q.r.y * sd * 0.8
            person(c, px, py, ground(px, py), ("wave", "merchant", "cheer", "huddle")[(i + (sd > 0)) % 4], q.p.x, q.p.y)
    box(c, "Bazaar Gate Beam", q.p.x, q.p.y, 0.5, q.w / 2 + 3.2, q.p.z + 9.6, q.p.z + 10.6, ("weathered_timber", "wall"),
        rot=rot + math.pi / 2, role="visual")
    for f in range(5):
        t = (f + 0.5) / 5
        x, y = lerp(tops[0][0], tops[1][0], t), lerp(tops[0][1], tops[1][1], t)
        ux, uy = q.t.x * 0.05 + q.r.x * 0.7, q.t.y * 0.05 + q.r.y * 0.7
        cloth(c, "Bazaar Gate Banner %d" % f, [(x - ux, y - uy, q.p.z + 9.6), (x + ux, y + uy, q.p.z + 9.6), (x + ux, y + uy, q.p.z + 6.8),
                                                (x, y, q.p.z + 6.3), (x - ux, y - uy, q.p.z + 6.8)],
              ("awning_red", "rug", "awning_teal", "rug", "awning_red")[f])
    lantern_line(c, "Bazaar Gate Lanterns", (tops[0][0] - q.t.x * 3, tops[0][1] - q.t.y * 3, q.p.z + 8.4),
                 (tops[1][0] - q.t.x * 3, tops[1][1] - q.t.y * 3, q.p.z + 8.4), sag=1.2)


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
            if j % 2:
                c.place(props.ruin_column(c, j % 3), bx, by, top, rot=a, role="both")
            else:
                c.place(tp.flag_pole(c, flag="temple_flag" if k % 2 else "keep_flag", h=7.0), bx, by, top, role="visual")
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
                 seed=k + 3)
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
    c.entity("isles_dragon", keys=keys, length=round(c.length, 1), size=1.2)
    c.entity("villagers", list=SKY_CROWD)
