# The Edge of the World's life between and over its districts (Blake, Nov 3: "lets just
# remove the jumps completely. its fine if there are no jumps, we need to make the
# immersiveness so great such that the boring driving is justified").
# SPDX-License-Identifier: MIT
#
#   the sound     every stretch its own (game/depths.ts' atmosphere, sound only: the
#                 overworld paints the air): drips in the bores, the harbour's water and
#                 gulls at the docks, the crowd's roar in the market, the pits and the den,
#                 the sea pouring off the world at the mouth, wind out on the bridges, bells
#                 at the shrine and the gate;
#   the canal     boats sailing it, the bridge's planks creaking under you;
#   the glowworms blue-green lights crawling over the bores' roofs, and their glow;
#   the mouth     the sea pours off the world straight over the Long Bore's mouth: you drive
#                 out through the curtain onto the Edge Bridge, the falls roaring, spray in
#                 the air, the sky opening up;
#   the sky       prayer flags strung along every bridge, gulls wheeling, pterosaurs gliding
#                 round and under the islands, bells.

import math

from pocket_build import box
import props
import jedge_districts as D
import jedge_layout as L
from jedge_layout import CANAL, CLOUD_Z, DOCK_WATER, ISLES, MOUTH, WATER_Z, cavern_at, isle_at, rim_y, smooth

# The sound of each stretch (fog and light unused: "light": False).
ZONES = {
    "bore": "drip",
    "docks": "harbour",
    "market": "festival",
    "pits": "festival",
    "den": "festival",
    "mouth": "falls",
    "sky": "wind",
    "shrine": "bells",
    "gate": "bells",
}


def zone_at(x, y, s, s_mouth):
    if s_mouth - 50.0 < s < s_mouth + 40.0:
        return "mouth"
    if y > rim_y(x) - 2.0:
        k = isle_at(x, y, 6.0)
        name = ISLES[k][0] if k is not None else ""
        return {"Shrine Isle": "shrine", "Sky Gate Isle": "gate", "Gatekeeper's Rock": "gate"}.get(name, "sky")
    return {"Smugglers' Docks": "docks", "Night Bazaar": "market", "Fighting Pits": "pits", "Lucky Bone": "den"}.get(
        cavern_at(x, y)[0], "bore")


def atmosphere(c, s0, s1, s_mouth):
    """Keys every 8 m along the road, blending each stretch's sound into the next."""
    blend = 30.0

    def zone(s):
        q = c.at(min(max(s, s0), s1))
        return zone_at(q.p.x, q.p.y, s, s_mouth)

    def change(s, direction):
        here = zone(s)
        d = 0.0
        while d < blend:
            d += 2.0
            if zone(s + direction * d) != here:
                return d, zone(s + direction * d)
        return None, here

    keys = []
    s = s0 - 20.0
    while s < s1 + 20.0:
        q = c.at(min(max(s, s0), s1))
        cur = zone(s)
        da, after = change(s, 1)
        db, before = change(s, -1)
        if da is not None and (db is None or da <= db):
            a_, b_, t = cur, after, 0.5 * (1.0 - da / blend)
        elif db is not None:
            a_, b_, t = before, cur, 0.5 + 0.5 * db / blend
        else:
            a_, b_, t = cur, cur, 0.0
        x, y, z = c.game(q.p.x, q.p.y, q.p.z)
        keys.append([round(x, 1), round(y, 1), round(z, 1), a_, b_, round(smooth(t), 3)])
        s += 8.0
    c.entity("atmosphere", light=False, zones={k: {"sound": v} for k, v in ZONES.items()}, keys=keys)
    return len(keys)


def canal(c):
    """Boats sailing the canal east of the bridge, and the bridge's planks creaking."""
    cy, hw, cx0, cx1 = CANAL
    pts = [(27.0 + 17.0 * math.cos(a), cy + 1.4 * math.sin(a)) for a in [k * math.tau / 14 for k in range(14)]]
    c.path_curve("Canal Boat Path", pts, z=DOCK_WATER, closed=True)
    c.entity("boat", route="Canal Boat Path", speed=2.0, start=0.0, colors=["#4a3424", "#2a5a4a"], scale=0.9)
    q, _ = c.nearest(-3.0, cy)
    g = c.game(q.p.x, q.p.y, q.p.z)
    c.entity("creak", x=round(g[0], 1), y=round(g[1], 1), z=round(g[2], 1), radius=26.0)
    g = c.game(-14.0, cy, DOCK_WATER + 0.5)
    c.entity("mist", x=round(g[0], 1), y=round(g[1], 1), z=round(g[2], 1), radius=22.0, rate=3.0, color="#a8b4b0")


def glowworms(c, stretches):
    """Glowworms on the bores' roofs: blue-green lights blinking in the dark, a glow on
    the road under the thickest of them."""
    n = 0
    for a, b in stretches:
        s = a
        k = 0
        while s < b:
            q = c.at(s)
            if cavern_at(q.p.x, q.p.y)[0] is None:
                g = c.game(q.p.x, q.p.y, q.p.z + 8.5)
                c.entity("motes", x=round(g[0], 1), y=round(g[1], 1), z=round(g[2], 1), radius=14.0, rate=9.0,
                         color=("#7af0d8", "#9ad8ff")[k % 2], rise=-0.05, size=0.18, blink=True)
                if k % 2 == 0:
                    g = c.game(q.p.x, q.p.y, q.p.z + 6.0)
                    c.entity("glow", x=round(g[0], 1), y=round(g[1], 1), z=round(g[2], 1), color="#3ac8b0")
                n += 1
            s += 15.0
            k += 1
    return n


def mouth(c, ground):
    """The sea pouring off the world straight over the Long Bore's mouth: a curtain you
    drive out through onto the Edge Bridge, its roar, the spray; and folk at the mouth
    who've come to see the edge of the world, sitting on the lip, waving you off."""
    mx = MOUTH[0]
    ry = rim_y(mx)
    props.falls(c, "Mouth Falls", mx, ry + 1.0, WATER_Z + 0.2, CLOUD_Z + 2.0, 40.0, 50.0, facing=1, throw=8.0, bulge=1.8, veils=3,
                foam=False, mats=("falls_oasis", "falls_curtain_oasis", "falls_foam"))
    q, _ = c.nearest(mx, ry + 4.0)
    g = c.game(q.p.x, q.p.y, q.p.z - 30.0)
    c.entity("waterfall", x=round(g[0], 1), y=round(g[1], 1), z=round(g[2], 1), top=round(WATER_Z, 1), width=40.0, heading=0)
    for dz, r in ((2.0, 16.0), (-12.0, 26.0)):
        g = c.game(q.p.x, q.p.y + 4.0, q.p.z + dz)
        c.entity("mist", x=round(g[0], 1), y=round(g[1], 1), z=round(g[2], 1), radius=r, rate=8.0, color="#f4f8ff")
    # (the onlookers, inside the mouth either side of the road)
    q0, _ = c.nearest(mx, ry - 14.0)
    for sd in (-1, 1):
        for i in range(5):
            x = q0.p.x + q0.r.x * sd * (q0.w / 2 + 2.4 + 0.9 * (i % 2)) + q0.t.x * (i * 2.4 - 4.0)
            y = q0.p.y + q0.r.y * sd * (q0.w / 2 + 2.4 + 0.9 * (i % 2)) + q0.t.y * (i * 2.4 - 4.0)
            D.person(c, x, y, q0.p.z, ("wave", "cheer", "huddle", "wave", "cheer")[i], q0.p.x + q0.t.x * 30.0, q0.p.y + q0.t.y * 30.0)
        D.light(c, "lantern", q0.p.x + q0.r.x * sd * (q0.w / 2 + 3.6), q0.p.y + q0.r.y * sd * (q0.w / 2 + 3.6), q0.p.z + 4.5)


def sky(c, spans):
    """Prayer flags along every bridge (between its towers' tops, either side and across),
    gulls wheeling over the islands, pterosaurs gliding round and under them, bells at the
    shrine and the gate, the bridges' planks creaking."""
    lines = []
    for (a_s, b_s, tops) in spans:
        (a0, a1), (b0, b1) = tops
        for p, q_ in ((a0, b0), (a1, b1), (a0, b1), (a1, b0)):
            ga = c.game(p[0], p[1], p[2] - 1.0)
            gb = c.game(q_[0], q_[1], q_[2] - 1.0)
            sag = min(6.0, 0.15 * math.dist(p[:2], q_[:2]) + 1.0)
            lines.append([*(round(v, 2) for v in ga), *(round(v, 2) for v in gb), round(sag, 2)])
        for p, q_ in ((a0, a1), (b0, b1)):
            ga = c.game(p[0], p[1], p[2] - 0.5)
            gb = c.game(q_[0], q_[1], q_[2] - 0.5)
            lines.append([*(round(v, 2) for v in ga), *(round(v, 2) for v in gb), 1.6])
        q = c.at((a_s + b_s) / 2)
        g = c.game(q.p.x, q.p.y, q.p.z)
        c.entity("creak", x=round(g[0], 1), y=round(g[1], 1), z=round(g[2], 1), radius=max(14.0, (b_s - a_s) / 2 + 6.0))
    if lines:
        c.entity("prayer_flags", lines=lines)
    # (gulls over the islands and off the edge)
    for k, (x, y, z, r, n) in enumerate(((40.0, 200.0, -28.0, 50.0, 7), (-40.0, 300.0, -24.0, 40.0, 6), (30.0, 420.0, -20.0, 46.0, 8),
                                         (-120.0, 200.0, -10.0, 70.0, 5), (150.0, 230.0, -30.0, 60.0, 6))):
        g = c.game(x, y, z)
        c.entity("birds", color="#f4f2ec", x=round(g[0], 1), y=round(g[1], 1), z=round(g[2], 1), radius=r, count=n, speed=0.18 + 0.03 * k,
                 seed=k + 11)
    # (pterosaurs: one round under the islands, one wide round them, one up by the gate)
    for k, (cx, cy, rx, ry, z, sp, sc) in enumerate(((-6.0, 300.0, 70.0, 110.0, -62.0, 12.0, 1.6),
                                                      (0.0, 320.0, 120.0, 150.0, -30.0, 14.0, 1.2),
                                                      (10.0, 440.0, 60.0, 50.0, -18.0, 11.0, 1.0))):
        pts = [(cx + rx * math.cos(a), cy + ry * math.sin(a), z + 5.0 * math.sin(3 * a + k)) for a in [j * math.tau / 16 for j in range(16)]]
        if k == 1:
            pts.reverse()
        c.path_curve("Sky Flyer %d" % (k + 1), pts)
        c.entity("pterosaur", route="Sky Flyer %d" % (k + 1), speed=sp, scale=sc, start=k * 90.0)
    # (bells at the shrine's stele and the Sky Gate)
    bells = []
    for name, dx, dy in (("Shrine Isle", -6.0, 8.0), ("Shrine Isle", -14.0, -5.0), ("Sky Gate Isle", -12.0, 14.0), ("Sky Gate Isle", 12.0, 14.0)):
        k = [i for i, isle in enumerate(ISLES) if isle[0] == name][0]
        _, x, y, r, _ = ISLES[k]
        top = L.isle_top(k)
        bx, by = x + dx, y + dy
        box(c, "Bell Frame %d" % len(bells), bx, by, 0.15, 1.1, top, top + 4.2, ("weathered_timber", "wall"), role="visual")
        bells.append([round(v, 2) for v in c.game(bx, by, top + 3.0)])
    c.entity("bells", list=bells)
    return len(lines)


def all_life(c, ground, s0, s_mouth, s1, spans):
    n_keys = atmosphere(c, s0, s1, s_mouth)
    canal(c)
    s_den = c.nearest(*L.ROUTE[L.AT["den2"]][:2])[0].s
    s_dock = c.nearest(*L.ROUTE[L.AT["dock0"]][:2])[0].s
    s_alley = c.nearest(*L.ROUTE[L.AT["dock3"]][:2])[0].s
    s_stair = c.nearest(*L.ROUTE[L.AT["stair1"]][:2])[0].s
    n_glow = glowworms(c, [(s0 + 10.0, s_dock - 10.0), (s_alley, s_stair), (s_den + 10.0, s_mouth - 30.0)])
    mouth(c, ground)
    n_flags = sky(c, spans)
    print("life: %d sound keys, %d glowworm patches, %d prayer flag lines" % (n_keys, n_glow, n_flags))
