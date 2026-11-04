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
