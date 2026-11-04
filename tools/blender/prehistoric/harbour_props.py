# The Smugglers' Docks' things (Blake, Nov 4: "this underground harber needs to be way more
# immersive and high fidelity"): real ships at their moorings (lofted hulls with a pointed
# bow, bulwarks, a stern castle with lit windows, two masts with their yards and the sails
# furled on them, a bowsprit, rigging), and shacks on stilts for the cavern's walls
# (platforms on posts and braces, a shack of planks or siding, a tin roof, a porch rail, a
# ladder up, a stovepipe, a net hung to dry). Each a prop, built once.
# SPDX-License-Identifier: MIT

import math

from course_kit import rnd
from oasis_desert import Parts
from props import cuboid, loft, tube


def _p(c, name, build):
    return c.proto(name, build) and name


def _hull_ring(bm, L, B, z, n=18):
    """A waterline of the hull at z: half length L, half beam B, the bow (+X) drawn to a
    point, the stern (-X) full and round."""
    pts = []
    for i in range(n):
        a = i * math.tau / n
        x, y = L * math.cos(a), B * math.sin(a)
        if x > 0:
            y *= 1.0 - 0.55 * (x / L) ** 1.6
        else:
            y *= 1.0 - 0.12 * (-x / L) ** 3
        pts.append(bm.verts.new((x, y, z)))
    return pts


def ship(c, variant=0, length=20.0):
    """A smugglers' ship at her mooring, facing +X; origin at the waterline amidships."""
    name = "Harbour Ship %d %d" % (variant, int(length))

    def build(bm):
        P = Parts(bm)
        L, B = length / 2, length * 0.135
        lines = [(-1.7, 0.6, 0.22), (-0.9, 0.84, 0.62), (0.0, 0.95, 0.88), (0.9, 1.0, 1.0), (1.8, 1.02, 0.99), (2.5, 1.04, 0.95)]
        rings = [_hull_ring(bm, L * fl, B * fb, z) for z, fl, fb in lines]
        k0 = len(bm.faces)
        loft(bm, rings, cap_top=False, cap_bottom=True)
        P.slots.setdefault("ship_hull", []).extend(range(k0, len(bm.faces)))
        # (the bulwark above the deck, and the deck inside it)
        top = _hull_ring(bm, L * 1.05, B * 0.96, 3.2)
        k0 = len(bm.faces)
        loft(bm, [rings[-1], top], cap_top=False)
        P.slots.setdefault("wreck_hull", []).extend(range(k0, len(bm.faces)))
        deck = _hull_ring(bm, L * 1.0, B * 0.9, 2.55)
        k0 = len(bm.faces)
        bm.faces.new(deck)
        P.slots.setdefault("plank_deck", []).extend(range(k0, len(bm.faces)))
        # The stern castle, its windows lit, a lantern rail on top.
        sx = -L * 0.78
        P.add("ship_hull", cuboid, (sx, 0, 4.0), (L * 0.42, B * 1.5, 2.9))
        P.add("plank_deck", cuboid, (sx, 0, 5.5), (L * 0.44, B * 1.55, 0.15))
        for j in range(3):
            P.add("window_warm", cuboid, (sx - L * 0.215, (j - 1) * B * 0.45, 4.2), (0.08, 0.7, 0.9))
        for sd in (-1, 1):
            P.add("window_warm", cuboid, (sx, sd * B * 0.76, 4.2), (0.9, 0.08, 0.7))
        # The masts, their yards, the sails furled along them; the bowsprit.
        masts = [(L * 0.22, 15.0 + 1.5 * (variant % 2)), (-L * 0.28, 13.0)]
        for mx, mh in masts:
            P.add("weathered_timber", tube, [(mx, 0, 2.5), (mx, 0, mh)], 0.22, n=6)
            for yz, yw in ((mh * 0.58, B * 1.15), (mh * 0.86, B * 0.85)):
                P.add("weathered_timber", tube, [(mx + 0.3, -yw, yz), (mx + 0.3, yw, yz)], 0.11, n=5)
                P.add("sail_cloth", tube, [(mx + 0.45, -yw * 0.92, yz - 0.3), (mx + 0.45, 0, yz - 0.42), (mx + 0.45, yw * 0.92, yz - 0.3)],
                      0.3, n=6)
            P.add("weathered_timber", cuboid, (mx, 0, mh * 0.72), (1.2, 1.2, 0.15))  # (the top)
        bow = (L * 1.04, 0, 3.0)
        tip = (L * 1.45, 0, 5.0)
        P.add("weathered_timber", tube, [bow, tip], 0.16, n=5)
        # The rigging: stays fore and aft, shrouds down to the rails.
        fm, am = masts
        rope = [
            [(fm[0], 0, fm[1]), tip], [(fm[0], 0, fm[1]), (am[0], 0, am[1])], [(am[0], 0, am[1]), (sx - L * 0.2, 0, 5.6)],
            [(fm[0], 0, fm[1] * 0.86), (L * 0.95, 0, 3.2)],
        ]
        for mx, mh in masts:
            for sd in (-1, 1):
                for dx in (-1.2, 0.0, 1.2):
                    rope.append([(mx, 0, mh * 0.9), (mx + dx, sd * B * 0.97, 3.2)])
        for a, b in rope:
            P.add("rope_rail", tube, [a, b], 0.045, n=3)
        # A rowing boat lashed on deck, a pile of crates, a capstan.
        P.add("wreck_hull", cuboid, (L * 0.02, 0, 3.0), (3.6, 1.5, 0.7))
        for j in range(4):
            P.add("weathered_timber" if j % 2 else "wood_dock", cuboid, (L * 0.48 - j * 0.9, 0.8 * ((j % 2) * 2 - 1), 3.0 + 0.45 * (j // 2)),
                  (0.9, 0.9, 0.9), rot=j * 0.4)
        P.add("weathered_timber", tube, [(L * 0.75, 0, 2.55), (L * 0.75, 0, 3.6)], 0.4, n=8)
        return P.out(c)

    return _p(c, name, build)


SIDINGS = ("wreck_planks", "siding_brown", "siding_grey", "siding_green", "siding_red", "siding_ochre")


def stilt_shack(c, variant=0, P_h=3.0, w=5.0, d=4.0, h=2.8):
    """A shack on a platform on stilts (front, the door, to -Y; origin on the ground under
    the platform's middle): posts and braces, a plank platform with a porch in front and
    its rail, a shack of planks or siding, a tin roof sloping back, a lit window or two, a
    ladder up from the ground, a stovepipe, a net hung over the rail."""
    name = "Stilt Shack %d %d %d %d" % (variant, int(P_h * 10), int(w), int(h * 10))

    def build(bm):
        P = Parts(bm)
        pw, pd = w + 1.6, d + 2.6
        cy = 0.6  # (the shack sits back on the platform: the porch in front)
        for ix in (-1, 0, 1):
            for iy in (-1, 1):
                x, y = ix * pw / 2 * 0.92, iy * pd / 2 * 0.9
                lean = 0.12 * rnd(ix * 3 + iy + variant)
                P.add("weathered_timber", tube, [(x - lean, y, -0.6), (x, y, P_h)], 0.16, n=6)
        for iy in (-1, 1):
            y = iy * pd / 2 * 0.9
            P.add("weathered_timber", tube, [(-pw / 2 * 0.92, y, 0.3), (pw / 2 * 0.92, y, P_h - 0.3)], 0.07, n=4)
        for ix in (-1, 1):
            x = ix * pw / 2 * 0.92
            P.add("weathered_timber", tube, [(x, -pd / 2 * 0.9, P_h - 0.3), (x, pd / 2 * 0.9, 0.4)], 0.07, n=4)
        P.add("plank_deck", cuboid, (0, 0, P_h), (pw, pd, 0.3))
        mat = SIDINGS[variant % len(SIDINGS)]
        P.add(mat, cuboid, (0, cy, P_h + h / 2), (w, d, h))
        # (the roof sloping back, off the front's eave)
        P.add("tin_roof", cuboid, (0, cy + 0.15, P_h + h + 0.35), (w + 0.8, d + 1.0, 0.14), tilt=(-0.22, 0.0))
        P.add("window_dark", cuboid, (-w * 0.2, cy - d / 2 - 0.03, P_h + 1.05), (0.9, 0.06, 1.9))
        P.add("window_warm", cuboid, (w * 0.22, cy - d / 2 - 0.03, P_h + 1.5), (0.9, 0.06, 0.7))
        if variant % 2:
            P.add("window_warm", cuboid, (w / 2 + 0.03, cy, P_h + 1.5), (0.06, 0.8, 0.6))
        # The porch rail, the ladder, the stovepipe, a net.
        fy = -pd / 2 + 0.1
        P.add("weathered_timber", tube, [(-pw / 2, fy, P_h + 1.0), (pw / 2 * 0.3, fy, P_h + 1.0)], 0.05, n=4)
        for x in (-pw / 2, -pw / 4, 0.0, pw / 2 * 0.3):
            P.add("weathered_timber", tube, [(x, fy, P_h), (x, fy, P_h + 1.05)], 0.05, n=4)
        lx = pw / 2 * 0.62
        for sd in (-0.35, 0.35):
            P.add("weathered_timber", tube, [(lx + sd, fy - 1.0, -0.2), (lx + sd, fy, P_h + 0.9)], 0.05, n=4)
        for k in range(int(P_h / 0.4)):
            t = (k + 0.5) / (P_h / 0.4)
            P.add("weathered_timber", tube, [(lx - 0.35, fy - 1.0 + t, -0.2 + t * (P_h + 1.1)), (lx + 0.35, fy - 1.0 + t, -0.2 + t * (P_h + 1.1))],
                  0.035, n=3)
        P.add("iron", tube, [(w * 0.3, cy + d * 0.25, P_h + h), (w * 0.3, cy + d * 0.25, P_h + h + 1.6)], 0.12, n=6)
        P.poly("isle_net", [(-pw / 2 + 0.2, fy - 0.05, P_h + 1.0), (-pw / 2 + 1.8, fy - 0.05, P_h + 1.0), (-pw / 2 + 1.7, fy - 0.1, P_h - 0.6),
                            (-pw / 2 + 0.3, fy - 0.1, P_h - 0.4)], both=True)
        return P.out(c)

    return _p(c, name, build)


def moored_skiff(c, variant=0):
    """A rowing boat tied up at the quay steps (still; the ones rowing about are entities)."""
    name = "Moored Skiff %d" % variant

    def build(bm):
        P = Parts(bm)
        rings = [_hull_ring(bm, 2.0 * f, 0.8 * b, z, n=12) for z, f, b in ((-0.35, 0.7, 0.4), (0.0, 0.95, 0.9), (0.45, 1.0, 1.0))]
        k0 = len(bm.faces)
        loft(bm, rings, cap_top=False, cap_bottom=True)
        P.slots.setdefault("wreck_hull" if variant % 2 else "ship_hull", []).extend(range(k0, len(bm.faces)))
        P.add("plank_deck", cuboid, (0, 0, 0.12), (3.0, 1.1, 0.06))
        for x in (-0.6, 0.6):
            P.add("weathered_timber", cuboid, (x, 0, 0.3), (0.25, 1.5, 0.08))
        P.add("weathered_timber", tube, [(0.2, -0.9, 0.45), (1.6, -1.9, -0.1)], 0.04, n=3)
        return P.out(c)

    return _p(c, name, build)


# ------------------------------------------------------------------ Nov 4, review 1


def _ring_wheel(P, mat, cx, cy, cz, r, axis="y", spokes=8, rim=0.08):
    """A wheel (a treadwheel, a ship's wheel): its rim, spokes, hub; standing in the plane
    across `axis`."""
    pts = []
    for k in range(17):
        a = k * math.tau / 16
        u, v = r * math.cos(a), r * math.sin(a)
        pts.append((cx + u, cy, cz + v) if axis == "y" else (cx, cy + u, cz + v))
    P.add(mat, tube, pts, rim, n=5)
    for k in range(spokes):
        a = k * math.tau / spokes
        u, v = r * math.cos(a), r * math.sin(a)
        end = (cx + u, cy, cz + v) if axis == "y" else (cx, cy + u, cz + v)
        P.add(mat, tube, [(cx, cy, cz), end], rim * 0.6, n=4)


def harbour_crane(c, variant=0, height=9.0, reach=11.0, drop=6.0, load="net"):
    """A harbour crane, standing still (Blake, review 1 note 2: "make them look really
    good"): a stone plinth; a timber tower on four posts, X-braced between its rings; the
    house on top, its gabled roof, a treadwheel on its side; a lattice jib out along +X,
    its pulley; a stone counterweight behind; the stays; and its load hanging `drop`
    under the tip: a cargo net of crates or a slung pallet, its ropes all tied on. Origin
    at the plinth's foot."""
    name = "Harbour Crane %d %d %d %d %s" % (variant, int(height), int(reach), int(drop), load)

    def build(bm):
        P = Parts(bm)
        P.add("bog_stone", cuboid, (0, 0, 0.4), (3.8, 3.8, 0.8))
        H = height
        s = 1.4
        for ix in (-1, 1):
            for iy in (-1, 1):
                P.add("weathered_timber", tube, [(ix * s, iy * s, 0.8), (ix * s * 0.9, iy * s * 0.9, H)], 0.2, n=6)
        levels = [0.9, H * 0.36, H * 0.7, H]
        for z in levels[1:]:
            k = 1.0 - 0.1 * (z / H)
            ring = [(s * k, s * k, z), (-s * k, s * k, z), (-s * k, -s * k, z), (s * k, -s * k, z), (s * k, s * k, z)]
            P.add("weathered_timber", tube, ring, 0.12, n=5)
        for z0, z1 in zip(levels, levels[1:]):
            k0, k1 = 1.0 - 0.1 * (z0 / H), 1.0 - 0.1 * (z1 / H)
            for (ax, ay), (bx, by) in (((1, 1), (-1, 1)), ((-1, 1), (-1, -1)), ((-1, -1), (1, -1)), ((1, -1), (1, 1))):
                P.add("weathered_timber", tube, [(ax * s * k0, ay * s * k0, z0), (bx * s * k1, by * s * k1, z1)], 0.07, n=4)
                P.add("weathered_timber", tube, [(bx * s * k0, by * s * k0, z0), (ax * s * k1, ay * s * k1, z1)], 0.07, n=4)
        # The house, its roof, its treadwheel.
        P.add("wreck_planks", cuboid, (0, 0, H + 1.3), (3.4, 3.0, 2.6))
        for sd in (-1, 1):
            P.add("tin_roof", cuboid, (0, sd * 0.85, H + 3.05), (3.9, 1.9, 0.12), tilt=(sd * 0.5, 0.0))
        P.add("window_warm", cuboid, (-1.71, 0, H + 1.6), (0.06, 0.8, 0.7))
        _ring_wheel(P, "weathered_timber", -0.2, -1.75, H + 1.3, 1.25, axis="y", spokes=8, rim=0.09)
        P.add("weathered_timber", tube, [(-0.2, -1.5, H + 1.3), (-0.2, 1.4, H + 1.3)], 0.12, n=6)
        # The jib: two chords, laced; its pulley at the tip.
        e = 0.42
        x0, z0 = 1.5, H + 0.6
        tx, tz = x0 + reach * math.cos(e), z0 + reach * math.sin(e)
        for sd in (-0.35, 0.35):
            P.add("weathered_timber", tube, [(x0, sd, z0), (tx, sd * 0.4, tz)], 0.13, n=5)
        steps = max(3, int(reach / 1.3))
        for k in range(steps):
            t0, t1 = k / steps, (k + 1) / steps
            a = (lerp_(x0, tx, t0), -0.35 * lerp_(1, 0.4, t0), lerp_(z0, tz, t0))
            b = (lerp_(x0, tx, t1), 0.35 * lerp_(1, 0.4, t1), lerp_(z0, tz, t1))
            P.add("weathered_timber", tube, [a, b], 0.05, n=4)
            P.add("weathered_timber", tube, [(a[0], -a[1], a[2]), (b[0], -b[1], b[2])], 0.05, n=4)
        P.add("iron", cuboid, (tx, 0, tz), (0.5, 0.25, 0.5))
        # The counterweight, the A-frame over the house, its stays to the tip and the weight.
        P.add("bog_dark_stone", cuboid, (-2.6, 0, H + 0.6), (1.6, 1.6, 1.2))
        P.add("weathered_timber", tube, [(-1.2, 0, H + 0.6), (-2.6, 0, H + 0.6)], 0.15, n=5)
        mast = (0.2, 0, H + 5.2)
        for sd in (-1, 1):
            P.add("weathered_timber", tube, [(1.2, sd * 1.2, H + 2.6), mast], 0.12, n=5)
        for end in ((tx, 0, tz + 0.2), (-2.6, 0, H + 1.2)):
            P.add("rope_rail", tube, [mast, end], 0.05, n=4)
        # The load: its rope from the pulley down to the hook, the slings, the load.
        hook = (tx, 0, tz - drop)
        P.add("rope_rail", tube, [(tx, 0, tz - 0.25), hook], 0.045, n=4)
        P.add("iron", tube, [(tx, 0, hook[2]), (tx + 0.15, 0, hook[2] - 0.3), (tx, 0, hook[2] - 0.45)], 0.04, n=4)
        if load == "net":
            cz = hook[2] - 1.5
            for k in range(5):
                a = k * 2.4
                P.add("weathered_timber" if k % 2 else "wood_dock", cuboid,
                      (tx + 0.35 * math.cos(a), 0.35 * math.sin(a), cz - 0.2 + 0.25 * (k % 3)), (0.7, 0.6, 0.55), rot=a)
            P.add("isle_net", props_blob(), (tx, 0, cz), 1.05)
            for k in range(4):
                a = k * math.tau / 4 + 0.4
                P.add("rope_rail", tube, [(tx, 0, hook[2] - 0.45), (tx + 0.85 * math.cos(a), 0.85 * math.sin(a), cz + 0.35)], 0.03, n=3)
        else:
            cz = hook[2] - 2.0
            P.add("plank_deck", cuboid, (tx, 0, cz - 0.6), (2.0, 1.4, 0.12))
            for k in range(4):
                P.add("weathered_timber" if k % 2 else "wood_dock", cuboid,
                      (tx - 0.5 + (k % 2) * 1.0, -0.3 + (k // 2) * 0.6, cz - 0.25 + 0.0), (0.9, 0.55, 0.6))
            for sx in (-1, 1):
                for sy in (-1, 1):
                    P.add("rope_rail", tube, [(tx, 0, hook[2] - 0.45), (tx + sx * 0.95, sy * 0.65, cz - 0.55)], 0.03, n=3)
        return P.out(c)

    return _p(c, name, build)


def lerp_(a, b, t):
    return a + (b - a) * t


def props_blob():
    from props import blob

    def f(bm, centre, r):
        return blob(bm, centre, r, sx=1.0, sy=1.0, sz=0.85, subdiv=2)

    return f


FISH = ("keep_iron", "isle_sea", "cove_coral_pink", "bog_moss_ground")


def _fish(P, x, y, z, ln, rot, mat):
    """A fish: a lofted body, a tail fin."""
    from props import blob
    ca, sa = math.cos(rot), math.sin(rot)
    P.add(mat, blob, (x, y, z), ln * 0.5, sx=1.0, sy=0.32, sz=0.22, subdiv=1)
    tx, ty = x - ca * ln * 0.55, y - sa * ln * 0.55
    k0 = len(P.bm.faces)
    v = [P.bm.verts.new((tx, ty, z)), P.bm.verts.new((tx - ca * ln * 0.25 - sa * ln * 0.18, ty - sa * ln * 0.25 + ca * ln * 0.18, z)),
         P.bm.verts.new((tx - ca * ln * 0.25 + sa * ln * 0.18, ty - sa * ln * 0.25 - ca * ln * 0.18, z))]
    P.bm.faces.new(v)
    P.bm.faces.new([P.bm.verts.new(q.co) for q in reversed(v)])
    P.slots.setdefault(mat, []).extend(range(k0, len(P.bm.faces)))


def market_stall(c, variant=0, kind="fish"):
    """A market stall on the quay (Blake, review 1 note 3: "we need higher fidelity
    markets"): four posts, a plank counter with a front panel, a tilted tray of the day's
    catch on ice (fish, or crabs in baskets, or smoked eels hanging, or contraband
    bottles), a rail of fish on hooks, a striped awning with a scalloped valance, a sign
    board, baskets and a barrel beside it. Customers on -Y; origin on the ground at its
    middle."""
    name = "Market Stall %d %s" % (variant, kind)

    def build(bm):
        from props import blob
        P = Parts(bm)
        w, d = 3.4, 1.8
        for ix in (-1, 1):
            for iy in (-1, 1):
                P.add("weathered_timber", tube, [(ix * w / 2, iy * d / 2, 0), (ix * w / 2, iy * d / 2, 2.6 if iy < 0 else 3.0)], 0.07, n=5)
        P.add("wood_dock", cuboid, (0, -d / 2 + 0.3, 0.95), (w, 0.7, 0.08))
        P.add("wreck_planks", cuboid, (0, -d / 2 + 0.02, 0.48), (w, 0.06, 0.9))
        for k in range(5):
            P.add("weathered_timber", cuboid, (-w / 2 + 0.2 + k * (w - 0.4) / 4, -d / 2 - 0.02, 0.48), (0.08, 0.06, 0.92))
        # The tray, tilted toward the customers, and what's on it.
        P.add("snow_ground" if kind in ("fish", "crabs") else "plank_deck", cuboid, (0, -d / 2 + 0.33, 1.06), (w - 0.3, 0.6, 0.08),
              tilt=(0.25, 0))
        if kind == "fish":
            for k in range(10):
                _fish(P, -w / 2 + 0.35 + (k % 5) * 0.65, -d / 2 + 0.18 + (k // 5) * 0.3, 1.13 + (k // 5) * 0.08, 0.45 + 0.1 * ((k + variant) % 3),
                      0.2 * ((k % 3) - 1), FISH[(k + variant) % len(FISH)])
        elif kind == "crabs":
            for j in range(3):
                bx = -w / 2 + 0.6 + j * 1.1
                P.add("thatch", loft, [_r(bm, bx, -d / 2 + 0.3, 0.28, 1.08), _r(bm, bx, -d / 2 + 0.3, 0.36, 1.4)], cap_bottom=True)
                for k in range(4):
                    a = k * 1.6 + j
                    P.add("awning_red", blob, (bx + 0.15 * math.cos(a), -d / 2 + 0.3 + 0.15 * math.sin(a), 1.42), 0.11, sx=1.3, sz=0.5, subdiv=1)
        elif kind == "bottles":
            for k in range(14):
                bx = -w / 2 + 0.3 + (k % 7) * 0.45
                by = -d / 2 + 0.2 + (k // 7) * 0.3
                mat = ("bog_glow_pool", "window_warm", "ember_glow")[(k + variant) % 3]
                P.add(mat, loft, [_r(bm, bx, by, 0.07, 1.1), _r(bm, bx, by, 0.08, 1.32), _r(bm, bx, by, 0.03, 1.4), _r(bm, bx, by, 0.03, 1.5)],
                      cap_top=True, cap_bottom=True)
        # The rail of fish (or eels) on hooks, under the awning's front.
        P.add("weathered_timber", tube, [(-w / 2, -d / 2 + 0.05, 2.35), (w / 2, -d / 2 + 0.05, 2.35)], 0.04, n=4)
        for k in range(6):
            x = -w / 2 + 0.35 + k * (w - 0.7) / 5
            P.add("rope_rail", tube, [(x, -d / 2 + 0.05, 2.35), (x, -d / 2 + 0.05, 2.1)], 0.012, n=3)
            if kind == "eels":
                P.add("charred_bark", tube, [(x, -d / 2 + 0.05, 2.1), (x + 0.05, -d / 2 + 0.08, 1.7), (x - 0.04, -d / 2 + 0.05, 1.35)], 0.04, n=4)
            else:
                P.add(FISH[(k + variant + 1) % len(FISH)], blob, (x, -d / 2 + 0.05, 1.85), 0.24, sx=0.35, sy=0.18, sz=1.0, subdiv=1)
        # The awning: sloped from the back's posts over the front, its scalloped valance.
        stripe = ("awning_teal", "awning_red", "canvas_sun", "awning_sea")[variant % 4]
        P.poly(stripe, [(-w / 2 - 0.3, d / 2 + 0.2, 3.05), (w / 2 + 0.3, d / 2 + 0.2, 3.05), (w / 2 + 0.3, -d / 2 - 0.5, 2.55),
                        (-w / 2 - 0.3, -d / 2 - 0.5, 2.55)], both=True)
        n = 9
        for k in range(n):
            x0 = -w / 2 - 0.3 + k * (w + 0.6) / n
            x1 = x0 + (w + 0.6) / n
            P.poly(stripe if k % 2 else "sail_cloth", [(x0, -d / 2 - 0.5, 2.55), (x1, -d / 2 - 0.5, 2.55), ((x0 + x1) / 2, -d / 2 - 0.52, 2.2)],
                   both=True)
        # The sign board on top of the back posts; a barrel and baskets beside.
        P.add("weathered_timber", cuboid, (0, d / 2, 3.35), (2.2, 0.08, 0.55))
        P.add("wreck_planks", cuboid, (0, d / 2 - 0.05, 3.35), (2.0, 0.06, 0.42))
        P.add("weathered_timber", loft, [_r(bm, w / 2 + 0.6, 0.2, 0.36, 0.0), _r(bm, w / 2 + 0.6, 0.2, 0.42, 0.45), _r(bm, w / 2 + 0.6, 0.2, 0.36, 0.9)],
              cap_top=True)
        P.add("thatch", loft, [_r(bm, -w / 2 - 0.55, -0.3, 0.3, 0.0), _r(bm, -w / 2 - 0.55, -0.3, 0.4, 0.5)], cap_bottom=True)
        return P.out(c)

    return _p(c, name, build)


def _r(bm, x, y, r, z, n=10):
    from props import ring
    return ring(bm, (x, y), r, z, n)


def warehouse(c, variant=0, w=13.0, d=9.0, h=7.0):
    """A run-down warehouse (Blake, review 1 note 8: "the buildings need to look a bit
    more run down and high detail"): its timber frame proud of the walls; walls of
    planks, some gone (the dark inside showing) and some patched; a sagging gabled roof of
    tin, rusted panels patched in and a hole or two; big doors on its long sides, one
    leaf hanging open; a loft door with its hoist beam, rope and a crate on the hook;
    boarded windows; a lean-to at one end with crates under it; rust streaks; a broken
    gutter; a stovepipe. Doors to +-Y; origin on the ground at its middle."""
    name = "Run-down Warehouse %d %d %d %d" % (variant, int(w), int(d), int(h))

    def build(bm):
        from props import blob
        P = Parts(bm)
        siding = SIDINGS[1 + variant % (len(SIDINGS) - 1)]
        P.add("window_dark", cuboid, (0, 0, h / 2), (w - 0.5, d - 0.5, h - 0.2))
        # The planks: vertical boards round all four walls, some missing, some patched.
        for side, (L_, fixed, along) in enumerate(((w, d / 2, "x"), (w, -d / 2, "x"), (d, w / 2, "y"), (d, -w / 2, "y"))):
            n = int(L_ / 0.42)
            for k in range(n):
                q = -L_ / 2 + (k + 0.5) * L_ / n
                gone = (k * 7 + side * 3 + variant) % 23 == 0
                short = (k * 5 + side + variant) % 17 == 0
                if gone:
                    continue
                top = h - (0.9 if short else 0.0)
                mat = "wreck_planks" if (k * 3 + side + variant) % 11 == 0 else siding
                c0 = (q, fixed, top / 2) if along == "x" else (fixed, q, top / 2)
                size = (L_ / n * 0.94, 0.12, top) if along == "x" else (0.12, L_ / n * 0.94, top)
                P.add(mat, cuboid, c0, size, rot=0.0, tilt=(0.0, 0.015 * ((k % 3) - 1)))
        # The frame: corner and middle posts, the wall plate.
        for x in (-w / 2, -w / 6, w / 6, w / 2):
            for y in (-d / 2, d / 2):
                P.add("weathered_timber", cuboid, (x, y + (0.1 if y > 0 else -0.1), h / 2), (0.3, 0.3, h))
        for y in (-d / 2, d / 2):
            P.add("weathered_timber", cuboid, (0, y + (0.12 if y > 0 else -0.12), h - 0.15), (w + 0.3, 0.3, 0.3))
        # The roof: two slopes in three bays, the middle sagging; rusty patches, a hole.
        rise = d * 0.28
        slope = math.atan2(rise, d / 2)
        for sd in (-1, 1):
            for bay in range(3):
                bx = -w / 3 + bay * w / 3
                sag = 0.3 if bay == 1 else 0.0
                if bay == 2 and sd > 0 and variant % 2 == 0:
                    continue  # (a hole in the roof)
                mat = "wreck_iron" if (bay + variant + (sd > 0)) % 3 == 0 else "tin_roof"
                P.add(mat, cuboid, (bx, sd * d / 4, h + rise / 2 - sag), (w / 3 + 0.05, math.hypot(d / 2, rise) + 0.5, 0.1),
                      tilt=(-sd * slope, 0.0))
        P.add("weathered_timber", tube, [(-w / 2 - 0.3, 0, h + rise + 0.05), (0, 0, h + rise - 0.25), (w / 2 + 0.3, 0, h + rise + 0.05)], 0.12, n=5)
        for x in (-w / 2, w / 2):
            # (the gable ends, closed with planks)
            k0 = len(bm.faces)
            v = [bm.verts.new((x, -d / 2, h)), bm.verts.new((x, d / 2, h)), bm.verts.new((x, 0, h + rise))]
            bm.faces.new(v)
            bm.faces.new([bm.verts.new(q.co) for q in reversed(v)])
            P.slots.setdefault(siding, []).extend(range(k0, len(bm.faces)))
        # The doors: double doors on both long sides, one leaf hanging open on one.
        for y, sgn in ((-d / 2, -1), (d / 2, 1)):
            P.add("window_dark", cuboid, (0, y + sgn * 0.08, 2.1), (3.6, 0.05, 4.2))
            for leaf in (-1, 1):
                open_ = leaf > 0 and sgn < 0
                if open_:
                    P.add("wreck_planks", cuboid, (1.8 + 0.7, y - 1.4, 2.1), (0.12, 1.8, 4.1), rot=0.4)
                else:
                    P.add("wreck_planks", cuboid, (leaf * 0.9, y + sgn * 0.14, 2.1), (1.76, 0.1, 4.1))
                    P.add("weathered_timber", cuboid, (leaf * 0.9, y + sgn * 0.2, 2.1), (1.6, 0.06, 0.14), rot=0.0, tilt=(0, leaf * 1.0))
            # (boarded windows either side)
            for x in (-w / 3, w / 3):
                P.add("window_dark", cuboid, (x, y + sgn * 0.08, 3.6), (1.3, 0.05, 1.1))
                for k in (-1, 1):
                    P.add("weathered_timber", cuboid, (x, y + sgn * 0.16, 3.6), (1.5, 0.05, 0.16), tilt=(0, k * 0.55))
        # The loft door, its hoist beam out over the doors, rope, hook, a crate on it.
        P.add("window_dark", cuboid, (0, -d / 2 - 0.08, h - 0.9), (1.4, 0.05, 1.5))
        P.add("weathered_timber", cuboid, (0, -d / 2 - 1.0, h + 0.3), (0.25, 2.2, 0.25))
        P.add("rope_rail", tube, [(0, -d / 2 - 1.9, h + 0.2), (0, -d / 2 - 1.9, h - 2.4)], 0.035, n=3)
        P.add("wood_dock", cuboid, (0, -d / 2 - 1.9, h - 2.85), (0.9, 0.9, 0.8))
        # The lean-to at the +X end, crates under it.
        P.add("weathered_timber", tube, [(w / 2 + 3.0, -d / 2 + 0.5, 0), (w / 2 + 3.0, -d / 2 + 0.5, 3.0)], 0.1, n=5)
        P.add("weathered_timber", tube, [(w / 2 + 3.0, d / 2 - 0.5, 0), (w / 2 + 3.0, d / 2 - 0.5, 3.0)], 0.1, n=5)
        P.add("wreck_iron", cuboid, (w / 2 + 1.6, 0, 3.4), (3.4, d - 0.6, 0.1), tilt=(0, 0.25))
        for k in range(4):
            P.add("wood_dock" if k % 2 else "weathered_timber", cuboid, (w / 2 + 1.2 + (k % 2) * 1.2, -1.5 + (k // 2) * 2.0, 0.45), (1.0, 1.0, 0.9),
                  rot=k * 0.3)
        # Rust streaks under the eaves, a gutter hanging off, a stovepipe.
        for k in range(5):
            x = -w / 2 + 1.5 + k * (w - 3.0) / 4
            P.add("wreck_iron", cuboid, (x, -d / 2 - 0.09, h - 1.2), (0.25, 0.02, 2.2))
        P.add("iron", tube, [(-w / 2, d / 2 + 0.3, h - 0.1), (0.0, d / 2 + 0.35, h - 0.25), (w / 3, d / 2 + 0.5, h - 1.4)], 0.08, n=5)
        P.add("iron", tube, [(w / 4, d / 4, h + rise * 0.5), (w / 4, d / 4, h + rise + 1.5)], 0.16, n=6)
        P.add("bog_dark_stone", blob, (-w / 2 - 0.5, -d / 2 - 0.5, 0.1), 0.5, sz=0.5, subdiv=1)
        return P.out(c)

    return _p(c, name, build)


def cage_lantern(c, variant=0):
    """A ship's lantern: an iron cage (plates top and bottom, bars, a ring to hang it by)
    round a warm glass. Origin at its ring (it hangs down from there)."""
    name = "Cage Lantern %d" % variant

    def build(bm):
        P = Parts(bm)
        P.add("window_glow" if variant % 2 == 0 else "lantern_glow", cuboid, (0, 0, -0.42), (0.18, 0.18, 0.3))
        P.add("keep_iron", cuboid, (0, 0, -0.24), (0.3, 0.3, 0.05))
        P.add("keep_iron", cuboid, (0, 0, -0.6), (0.27, 0.27, 0.05))
        P.add("keep_iron", loft, [_r(bm, 0, 0, 0.12, -0.23, n=6), _r(bm, 0, 0, 0.02, -0.1, n=6)], cap_top=False)
        for sx in (-1, 1):
            for sy in (-1, 1):
                P.add("keep_iron", tube, [(sx * 0.13, sy * 0.13, -0.6), (sx * 0.13, sy * 0.13, -0.24)], 0.02, n=3)
        P.add("keep_iron", tube, [(0, 0, -0.1), (0, 0.07, -0.02), (0, 0, 0.04), (0, -0.07, -0.02), (0, 0, -0.1)], 0.015, n=3)
        return P.out(c)

    return _p(c, name, build)


def treasure_chest(c, variant=0, s=1.0):
    """A treasure chest, its lid bound in gold, coins spilling from it."""
    name = "Treasure Chest %d %d" % (variant, int(s * 10))

    def build(bm):
        from props import blob
        P = Parts(bm)
        w, d, h = 1.4 * s, 0.9 * s, 0.75 * s
        P.add("weathered_timber", cuboid, (0, 0, h / 2), (w, d, h))
        P.add("weathered_timber", cuboid, (0, -0.1 * s, h + 0.22 * s), (w, d, 0.4 * s), tilt=(0.45 if variant % 2 else 0.0, 0))
        for x in (-w / 2 + 0.12 * s, w / 2 - 0.12 * s):
            P.add("gold_trim", cuboid, (x, 0, h / 2 + 0.1 * s), (0.1 * s, d + 0.04, h + 0.25 * s))
        P.add("gold_trim", cuboid, (0, -d / 2 - 0.02, h * 0.8), (0.18 * s, 0.05, 0.2 * s))
        for k in range(7):
            a = k * 2.4 + variant
            P.add("gold_trim", blob, (0.35 * s * math.cos(a), -d / 2 - 0.25 * s + 0.2 * s * math.sin(a), 0.05), 0.12 * s, sz=0.35, subdiv=1)
        return P.out(c)

    return _p(c, name, build)
