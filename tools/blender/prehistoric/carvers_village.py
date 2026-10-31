# The ice carvers' village, the Snow Kingdom's own village (Blake, Oct 30: "for every
# overworld, there is a small village that captures the culture of the area and is
# independent of the level designs"; "I do want a little village that we can drive
# around in as soon as we get down into the switch backs ... we can just go into the
# plateau and carve out space"; he chose ice carvers over stone-carvers, "ice carvers is
# way better", and pinned its place, review-snow_region 1: "it doesnt need to be a big
# village, but enough to explore, like the village in dino valley").
#
# The Ice Hollow (snow_layout.HOLLOW), cut into the plateau over the pass: the carvers'
# homes cut into its snow walls behind ice-block arches, warm windows in blue ice frames;
# a lane looping round them; in the middle the sculpture garden, its pieces half-finished,
# blocks waiting on sleds, and the Frost Spire, the carvers' great crystal of ice, tall
# enough to see from the Crest. Ice pillars with lanterns mark the switchbacks' hairpins
# on the way down. All our own designs, chunky and low-poly; prototypes' fronts face +Y,
# their origins on the ground.
# SPDX-License-Identifier: MIT

import math

import region_paint as paint
import snow_layout as SL
from course_kit import Vector
from keep_props import _p
from props import cuboid

ICE = "glacier_ice"
BLUE = "icefall_blue"
CLEAR = "lake_ice"
SNOW = "snow_ground"
TIMBER = "keep_timber"
DOOR = "keep_door"
WINDOW = "keep_window"
IRON = "keep_iron"


def _wedge(bm, x0, x1, y0, y1, z0, zf, zb):
    """A block from y0 (back) to y1 (front), its top zf at the front, zb at the back."""
    v = [bm.verts.new(p) for p in ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                   (x0, y0, zb), (x1, y0, zb), (x1, y1, zf), (x0, y1, zf))]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        bm.faces.new([v[i] for i in f])


def _crystal(bm, base, axis, length, r, n=6, phase=0.0):
    """A pointed ice crystal: a prism `length` long from `base` along `axis`, the last
    quarter tapering to a point."""
    a = Vector(axis).normalized()
    u = a.cross(Vector((0, 0, 1)))
    if u.length < 1e-3:
        u = Vector((1, 0, 0))
    u.normalize()
    w = a.cross(u)
    b = Vector(base)

    def ring_at(t, rr):
        return [bm.verts.new(b + a * t + (u * math.cos(phase + k * math.tau / n) + w * math.sin(phase + k * math.tau / n)) * rr)
                for k in range(n)]

    r0 = ring_at(-0.5, r)
    r1 = ring_at(length * 0.75, r * 0.92)
    tip = bm.verts.new(b + a * length)
    bm.faces.new(list(reversed(r0)))
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((r0[k], r0[j], r1[j], r1[k]))
        bm.faces.new((r1[k], r1[j], tip))


def _old_ice_home(c, variant):
    """A carver's home cut into the snow wall: a round arch of cut ice blocks, the oak door
    in it and warm windows either side in frames of blue ice, a snow cornice over the
    front; the snow it's cut from runs back into the wall."""
    v = variant % 4
    w = (7.0, 8.5, 6.0, 9.5)[v]
    h = (6.0, 7.0, 5.5, 7.5)[v]
    name = "Ice Carver Home %d" % v

    def build(P, bm):
        # The snow it's cut into.
        P.add(SNOW, lambda: _wedge(bm, -w / 2 - 1.8, w / 2 + 1.8, -9.0, -0.6, -1.5, h + 1.8, h + 7.0))
        # The front wall, packed ice.
        P.add(CLEAR, lambda: cuboid(bm, (0, -0.5, h / 2 - 0.8), (w, 0.6, h + 0.6)))
        # The arch over the door: cut blocks round a half circle, a keystone of blue.
        ar, az = 1.9, 2.6
        for k in range(7):
            t = math.pi * k / 6
            mat = BLUE if k == 3 else ICE
            P.add(mat, lambda t=t: cuboid(bm, (math.cos(t) * ar, 0.0, az + math.sin(t) * ar), (0.9, 1.0, 0.8), tilt=(0.0, -(t - math.pi / 2))))
        for sx in (-1, 1):
            P.add(ICE, lambda sx=sx: cuboid(bm, (sx * ar, 0.0, az / 2 - 0.4), (0.9, 1.0, az + 0.6)))
        P.add(DOOR, lambda: cuboid(bm, (0, -0.1, 1.5), (2.6, 0.12, 3.0)))
        # Windows, warm, in blue ice frames.
        for sx in (-1, 1):
            x = sx * (w / 2 - 1.3)
            if abs(x) < ar + 1.0:
                continue
            P.add(BLUE, lambda x=x: cuboid(bm, (x, -0.1, 2.4), (1.7, 0.4, 1.9)))
            P.add(WINDOW, lambda x=x: cuboid(bm, (x, 0.12, 2.4), (1.1, 0.06, 1.3)))
        if h >= 7.0:
            P.add(BLUE, lambda: cuboid(bm, (0, -0.1, h - 1.6), (1.5, 0.4, 1.3)))
            P.add(WINDOW, lambda: cuboid(bm, (0, 0.12, h - 1.6), (1.0, 0.06, 0.8)))
        # The snow cornice over the front, icicles under it.
        P.add(SNOW, lambda: cuboid(bm, (0, 0.2, h + 0.1), (w + 1.2, 1.8, 1.0)))
        for k in range(int(w / 1.2)):
            x = -w / 2 + 0.6 + k * 1.2
            ln = 0.6 + 0.5 * ((k * 7 + v) % 3)
            P.add(BLUE, lambda x=x, ln=ln: _crystal(bm, (x, 0.9, h - 0.3), (0, 0, -1), ln, 0.16, n=4))
        # A step of packed snow.
        P.add(SNOW, lambda: cuboid(bm, (0, 1.0, -0.25), (3.2, 1.2, 0.6)))

    return _p(c, name, build)


def frost_spire(c):
    """The Frost Spire: the carvers' masterpiece, a cluster of great ice crystals on a
    ring of cut blocks, the tallest 26 m, catching the light over the whole kingdom."""

    def build(P, bm):
        for k in range(10):
            a = k * math.tau / 10
            P.add(ICE, lambda a=a: cuboid(bm, (math.cos(a) * 5.0, math.sin(a) * 5.0, 0.5), (2.6, 1.8, 1.6), rot=a))
        P.add(CLEAR, lambda: cuboid(bm, (0, 0, 0.6), (8.0, 8.0, 1.6), rot=0.3))
        P.add(BLUE, lambda: _crystal(bm, (0, 0, 1.0), (0.02, 0.03, 1.0), 26.0, 2.4, phase=0.3))
        for k, (a, tilt, ln, r) in enumerate(((0.3, 0.32, 17.0, 1.6), (1.6, 0.4, 14.0, 1.4), (2.7, 0.28, 19.0, 1.7),
                                              (3.9, 0.45, 11.0, 1.2), (5.0, 0.35, 15.0, 1.4), (0.9, 0.6, 8.0, 0.9),
                                              (4.4, 0.62, 7.0, 0.8))):
            ax = (math.sin(tilt) * math.cos(a), math.sin(tilt) * math.sin(a), math.cos(tilt))
            mat = ICE if k % 2 else BLUE
            P.add(mat, lambda ax=ax, a=a, ln=ln, r=r: _crystal(bm, (math.cos(a) * 1.8, math.sin(a) * 1.8, 1.0), ax, ln, r, phase=a))

    return _p(c, "Frost Spire", build)


def mammoth_sculpture(c):
    """An ice mammoth, finished but for its back (still the block it came out of)."""

    def build(P, bm):
        P.add(SNOW, lambda: cuboid(bm, (0, 0, 0.3), (6.0, 3.4, 0.8)))
        P.add(ICE, lambda: cuboid(bm, (-0.6, 0, 3.0), (4.4, 2.8, 3.4)))
        P.add(CLEAR, lambda: cuboid(bm, (-1.4, 0, 4.9), (2.8, 3.0, 1.4)))
        P.add(ICE, lambda: cuboid(bm, (2.1, 0, 3.6), (1.8, 2.2, 2.4)))
        P.add(ICE, lambda: cuboid(bm, (3.0, 0, 2.0), (0.8, 0.9, 2.8)))
        for sy in (-1, 1):
            P.add(BLUE, lambda sy=sy: _crystal(bm, (2.8, sy * 0.8, 2.6), (0.7, sy * 0.2, 0.5), 2.6, 0.22, n=5))
            P.add(ICE, lambda sy=sy: cuboid(bm, (1.9, sy * 1.3, 4.2), (0.3, 1.0, 1.4)))
            for x in (-1.8, 0.8):
                P.add(ICE, lambda sy=sy, x=x: cuboid(bm, (x, sy * 0.8, 1.4), (0.9, 0.9, 1.6)))

    return _p(c, "Ice Mammoth", build)


def swan_sculpture(c):
    """An ice swan, wings up, on a snow plinth."""

    def build(P, bm):
        P.add(SNOW, lambda: cuboid(bm, (0, 0, 0.3), (3.4, 2.4, 0.8)))
        P.add(ICE, lambda: cuboid(bm, (0, 0, 1.3), (2.6, 1.4, 1.2)))
        P.add(ICE, lambda: cuboid(bm, (1.0, 0, 2.6), (0.4, 0.4, 2.4), tilt=(0.0, 0.2)))
        P.add(BLUE, lambda: cuboid(bm, (1.5, 0, 3.7), (0.9, 0.4, 0.4)))
        for sy in (-1, 1):
            P.add(CLEAR, lambda sy=sy: cuboid(bm, (-0.4, sy * 0.9, 2.3), (2.0, 0.2, 1.6), tilt=(sy * 0.5, 0.2)))

    return _p(c, "Ice Swan", build)


def owl_sculpture(c):
    """An ice owl on a column."""

    def build(P, bm):
        P.add(SNOW, lambda: cuboid(bm, (0, 0, 0.6), (1.6, 1.6, 1.4)))
        P.add(ICE, lambda: cuboid(bm, (0, 0, 2.2), (1.5, 1.2, 1.9)))
        P.add(ICE, lambda: cuboid(bm, (0, 0, 3.6), (1.3, 1.1, 1.0)))
        for sx in (-1, 1):
            P.add(BLUE, lambda sx=sx: cuboid(bm, (sx * 0.35, 0.56, 3.65), (0.36, 0.06, 0.36)))
            P.add(ICE, lambda sx=sx: _crystal(bm, (sx * 0.5, 0, 4.0), (sx * 0.3, 0, 1.0), 0.7, 0.18, n=4))

    return _p(c, "Ice Owl", build)


def ice_blocks(c, k):
    """Cut blocks of clear ice, stacked waiting."""

    def build(P, bm):
        for j, (x, y, z) in enumerate(((0, 0, 0.6), (1.3, 0.1, 0.6), (0.6, 0.0, 1.8), (-1.2, 0.6, 0.6))[: 2 + k % 3]):
            P.add(CLEAR if j % 2 == 0 else ICE, lambda x=x, y=y, z=z: cuboid(bm, (x, y, z), (1.2, 1.2, 1.2), rot=0.1 * j))

    return _p(c, "Ice Blocks %d" % (k % 3), build)


def sled(c):
    """A timber sled with a block of ice roped on."""

    def build(P, bm):
        for sy in (-1, 1):
            P.add(TIMBER, lambda sy=sy: cuboid(bm, (0, sy * 0.7, 0.15), (3.2, 0.15, 0.3)))
        P.add(TIMBER, lambda: cuboid(bm, (1.7, 0, 0.45), (0.2, 1.6, 0.6), tilt=(0.0, 0.5)))
        P.add(TIMBER, lambda: cuboid(bm, (0, 0, 0.4), (2.8, 1.6, 0.15)))
        P.add(CLEAR, lambda: cuboid(bm, (-0.2, 0, 1.15), (1.8, 1.3, 1.3)))
        P.add(TIMBER, lambda: cuboid(bm, (-0.2, 0, 1.15), (0.12, 1.4, 1.4)))

    return _p(c, "Ice Sled", build)


def bench(c):
    """A carver's bench: a timber top on trestles, a half-cut piece of ice on it."""

    def build(P, bm):
        P.add(TIMBER, lambda: cuboid(bm, (0, 0, 0.95), (2.8, 1.1, 0.2)))
        for sx in (-1, 1):
            P.add(TIMBER, lambda sx=sx: cuboid(bm, (sx * 1.1, 0, 0.45), (0.2, 1.0, 0.9)))
        P.add(ICE, lambda: _crystal(bm, (0.2, 0, 1.05), (0, 0, 1), 1.4, 0.5, n=5))
        P.add(IRON, lambda: cuboid(bm, (-0.9, 0.2, 1.1), (0.6, 0.1, 0.1)))

    return _p(c, "Ice Carver Bench", build)


def ice_pillar(c):
    """An ice pillar: a column of cut blocks narrowing up, blue bands between them, a
    lantern's iron arm at the top."""

    def build(P, bm):
        P.add(SNOW, lambda: cuboid(bm, (0, 0, 0.0), (2.4, 2.4, 1.0)))
        for k in range(4):
            s = 1.5 - 0.15 * k
            P.add(ICE, lambda k=k, s=s: cuboid(bm, (0, 0, 1.3 + k * 1.4), (s, s, 1.2)))
            P.add(BLUE, lambda k=k, s=s: cuboid(bm, (0, 0, 2.0 + k * 1.4), (s + 0.1, s + 0.1, 0.2)))
        P.add(BLUE, lambda: _crystal(bm, (0, 0, 6.6), (0, 0, 1), 1.6, 0.6))
        P.add(IRON, lambda: cuboid(bm, (0, 0.8, 6.2), (0.12, 1.6, 0.12)))

    return _p(c, "Ice Pillar", build)


# ------------------------------------------------------------------ placing it


def build(c, ground, taken):
    """The village in the Ice Hollow, and the ice pillars down the switchbacks; `taken`
    gets every spot used (snow_dress.entry_pass's lantern posts keep off them)."""
    hx, hy, rx, ry = SL.HOLLOW
    gx, gy, gr = SL.HOLLOW_GARDEN
    # The Frost Spire, in the garden's middle.
    c.place(frost_spire(c), gx, gy, ground(gx, gy) - 0.4, rot=0.0, coll="Village")
    taken.add(gx, gy, 7.5)
    # Its sculptures round it, facing out to the lane, and the carvers' work between.
    pieces = ((mammoth_sculpture, 0.6, 8.0), (swan_sculpture, 2.4, 8.5), (owl_sculpture, 3.6, 8.0),
              (swan_sculpture, 5.0, 8.0))
    for fn, a, r in pieces:
        x, y = gx + r * math.cos(a), gy + r * math.sin(a)
        c.place(fn(c), x, y, ground(x, y) - 0.1, rot=a - math.pi / 2, coll="Village")
        taken.add(x, y, 2.5)
    for k, (a, r, fn) in enumerate(((1.5, 9.0, bench), (4.3, 9.5, bench), (5.7, 8.5, sled), (0.0, 9.5, lambda c: ice_blocks(c, 0)),
                                    (3.0, 9.0, lambda c: ice_blocks(c, 1)), (4.9, 10.0, lambda c: ice_blocks(c, 2)))):
        x, y = gx + r * math.cos(a), gy + r * math.sin(a)
        if taken.clear(x, y, 1.0):
            c.place(fn(c), x, y, ground(x, y) - 0.05, rot=a + 0.4 * k, coll="Village")
            taken.add(x, y, 1.6)
    # The carvers, at work in the garden.
    g = c.game(gx + 4.0, gy - 6.0, ground(gx + 4.0, gy - 6.0))
    c.entity("villager_home", x=round(g[0], 2), z=round(g[2], 2), y=round(g[1], 2), r=8.0, n=5, folk="snow",
             heading=0.0)
    # Their homes, each its own, round the walls and out on the floor (ice_homes).
    import ice_homes

    homes = ice_homes.place_homes(c, ground, taken)
    # Ice pillars on the switchbacks' hairpins, on their outsides, lanterns on them.
    w = SL.CREST_WAY
    pil = 0
    for i in range(SL._CREST_TOP + 2, len(w) - 4):
        a, p, q = w[i - 1], w[i], w[i + 1]
        t0 = math.atan2(p[1] - a[1], p[0] - a[0])
        t1 = math.atan2(q[1] - p[1], q[0] - p[0])
        if abs((t1 - t0 + math.pi) % math.tau - math.pi) < 1.0:
            continue
        ox, oy = p[0] - (a[0] + q[0]) / 2, p[1] - (a[1] + q[1]) / 2
        ol = math.hypot(ox, oy) or 1.0
        px, py = p[0] + ox / ol * 4.0, p[1] + oy / ol * 4.0
        f = SL.lookout_floor(px, py)
        if f is None:
            continue
        c.place(ice_pillar(c), px, py, f[1] - 0.3, rot=math.atan2(oy, ox) + math.pi / 2, coll="Village")
        taken.add(px, py, 3.0)
        g = c.game(px - ox / ol * 0.8, py - oy / ol * 0.8, f[1] + 5.6)
        c.entity("lantern", x=g[0], y=g[1], z=g[2])
        pil += 1
    print("ice carvers' village: %d homes, %d ice pillars" % (homes, pil))
