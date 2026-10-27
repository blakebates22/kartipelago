# Pocket layouts for the overworld regions: pure geometry, no Blender (so a layout can be
# drawn and checked on its own). Dinosaur Valley's (valley_layout.py) is where the idea was
# worked out; the later regions are built on this kit.
# SPDX-License-Identifier: MIT
#
# Blake (Oct 26): each world its own segment, walled off by landscape so you only see the
# one you're in (an inkling of the next beyond a tunnel or down a hill), the main road one
# winding loop through them that's secretly a great race course.
#
# A region is POCKETS, each a hollow with a floor (blending its circles' heights, so a
# pocket can slope) rising into walls up to `top`: the land is the lowest of every pocket's
# floor-into-wall, so two pockets apart make a ridge between them and two at different
# heights a cliff. The walls rise in proportion to their height (as steep everywhere: too
# steep to drive up). The main road's control points ride the land (None) or are set by
# hand (in the tunnels); TUNNELS name the stretches bored through the high ground.

import math


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def smin(a, b, k):
    h = max(0.0, min(1.0, 0.5 + 0.5 * (b - a) / k))
    return lerp(b, a, h) - k * h * (1 - h)


def seg_d(px, py, a, b):
    ax, ay = a[0], a[1]
    bx, by = b[0], b[1]
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / ((dx * dx + dy * dy) or 1e-9)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy), t


def catmull(points, per=12):
    """A closed Catmull-Rom curve through (x, y, z) points (a stand-in for Blender's AUTO
    Bezier, for checking a layout without Blender)."""
    out = []
    n = len(points)
    for i in range(n):
        p0, p1, p2, p3 = (points[(i + k) % n] for k in (-1, 0, 1, 2))
        for s in range(per):
            t = s / per
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in range(3)))
    return out


class Layout:
    """pockets: [(name, look, [(x, y, radius, floor)])]; top: the high ground's height;
    hub: (x, y, radius, height) of a level square (or None); rivers: [[(x, y, water z)]];
    lakes: [(x, y, radius, z)]; route: [(x, y, z or None)]; tunnels: [(name, kind, first
    point, last point)]; roll: the rolling ground's height (m); flat: looks kept flat."""

    def __init__(self, pockets, top, route, tunnels, hub=None, rivers=(), lakes=(), river_hw=9.0, roll=5.0,
                 flat=(), mountains=40.0, water_floor=None, hidden=()):
        self.pockets = pockets
        self.top = top
        self.route = route
        self.tunnels = tunnels
        self.hub = hub
        self.rivers = list(rivers)
        self.lakes = list(lakes)
        self.river_hw = river_hw
        self.roll = roll
        self.flat = set(flat)
        self.mountains = mountains
        self.water_floor = water_floor
        # Route points with no road (a journey's way back round to its start, out of sight
        # over the mountains: the route is a loop, the road isn't): their heights are their
        # own and never smoothed into the road's.
        self.hidden = set(hidden)
        self.looks = sorted({p[1] for p in pockets})
        self._corridors = []
        self._rp = None

    # ------------------------------------------------------------------ the land

    def pocket_sd(self, p, x, y):
        """Signed distance from the pocket's edge (< 0 inside), and its floor height there."""
        sd = None
        fw = fz = 0.0
        for cx, cy, r, f in p[2]:
            d = math.hypot(x - cx, y - cy) - r
            sd = d if sd is None else smin(sd, d, 22.0)
            w = math.exp(-max(0.0, d + r * 0.6) / 30.0)
            fw += w
            fz += w * f
        return sd, fz / fw

    def wall_sd(self, x, y):
        return min(self.pocket_sd(p, x, y)[0] for p in self.pockets)

    def pocket_at(self, x, y):
        return min(self.pockets, key=lambda p: self.pocket_sd(p, x, y)[0])[0]

    def look_weights(self, x, y):
        acc = {n: 0.0 for n in self.looks}
        for p in self.pockets:
            sd, _ = self.pocket_sd(p, x, y)
            acc[p[1]] += math.exp(-max(-40.0, sd) / 14.0)
        tot = sum(acc.values()) or 1.0
        return {n: w / tot for n, w in acc.items()}

    def look_at(self, x, y):
        w = self.look_weights(x, y)
        return max(w, key=w.get)

    def water_d(self, x, y):
        """Distance to the nearest river's middle (or a lake's edge, less the half width), and
        the water's height there."""
        best, bz = 1e9, 0.0
        for riv in self.rivers:
            for a, b in zip(riv, riv[1:]):
                d, t = seg_d(x, y, a, b)
                if d < best:
                    best, bz = d, lerp(a[2], b[2], t)
        for lx, ly, lr, lz in self.lakes:
            d = max(0.0, math.hypot(x - lx, y - ly) - lr + self.river_hw)
            if d < best:
                best, bz = d, lz
        return best, bz

    def natural(self, x, y):
        h = None
        best = 1e9
        for p in self.pockets:
            sd, f = self.pocket_sd(p, x, y)
            best = min(best, sd)
            rise = max(10.0, 0.42 * (self.top - f))
            hp = lerp(f, self.top, smooth((sd + 8.0) / rise))
            h = hp if h is None else min(h, hp)
        w = self.look_weights(x, y)
        floor = 1.0 - smooth((best + 14.0) / 20.0)
        r = self.roll
        roll = (r * math.sin(x / 61.0 + 0.6) * math.cos(y / 73.0 - 0.3) + 0.52 * r * math.sin((x - y) / 47.0)
                + 0.2 * r * math.sin(x / 23.0) * math.cos(y / 29.0))
        keep = 1.0
        for n in self.flat:
            keep *= 1.0 - 0.9 * w.get(n, 0.0)
        h += roll * floor * keep
        if self.hub:
            cx, cy, cr, cz = self.hub
            h = lerp(cz, h, smooth((math.hypot(x - cx, y - cy) - cr) / 16.0))
        d, wz = self.water_d(x, y)
        hw = self.river_hw
        if d < hw + 14:
            h = lerp(h, wz - (self.water_floor if self.water_floor is not None else 1.4),
                     smooth((hw + 14 - d) / 14.0))
        if best > 0:
            h += 5.0 * smooth(best / 30.0) * (0.5 + 0.5 * math.sin(x / 17.0 + math.cos(y / 23.0) * 2.0))
            h += self.mountains * smooth((best - 70.0) / 110.0)
        return h

    # ------------------------------------------------------------------ the road

    def route_points(self):
        """The main road's control points at the land's height round each (a ring average,
        smoothed, so the road rides the swells), the hand-set ones as set, over the water on
        bridges."""
        if self._rp is not None:
            return self._rp
        n = len(self.route)
        zs = []
        for x, y, z in self.route:
            if z is None:
                ring = [self.natural(x + 12 * math.cos(a), y + 12 * math.sin(a)) for a in (0, 1.57, 3.14, 4.71)]
                z = (sum(ring) + self.natural(x, y)) / 5.0 + 0.3
            zs.append(z)
        for _ in range(2):
            def nb(i, j):
                return zs[i] if j % n in self.hidden else zs[j % n]

            zs = [z if self.route[i][2] is not None else 0.25 * nb(i, i - 1) + 0.5 * z + 0.25 * nb(i, i + 1)
                  for i, z in enumerate(zs)]
        out = []
        for i, (x, y, _) in enumerate(self.route):
            z = zs[i]
            d, wz = self.water_d(x, y)
            if d < self.river_hw + 24:
                z = max(z, wz + 2.4)
            out.append((x, y, round(z, 2)))
        self._rp = out
        return out

    def bridge_floor(self, x, y):
        """Under a bridge (where the road crosses water above it): the deck's underside if
        (x, y) is within 13 m of the road there, else None (the banks are kept down under
        it, out past its barriers: a bank standing up into a deck shoves karts sideways)."""
        if not hasattr(self, "_bridges"):
            self._bridges = []
            for p in catmull(self.route_points(), 8):
                d, wz = self.water_d(p[0], p[1])
                if d < self.river_hw + 12 and p[2] > wz + 0.9:
                    self._bridges.append(p)
        best = None
        for p in self._bridges:
            d = math.hypot(x - p[0], y - p[1])
            if d < 13.0 and (best is None or d < best[0]):
                best = (d, p[2] - 1.9)
        return None if best is None else best[1]

    def tunnel_floor(self, x, y):
        """Under a tunnel's rock: the road's height if (x, y) is within 18 m of the road
        through it (the land's kept flush under it, out to the bore's walls), else None."""
        if not self._corridors:
            rp = self.route_points()
            n = len(rp)
            for _, _, a, b in self.tunnels:
                sub = [rp[i % n] for i in range(a - 2, b + 4)]
                pts = catmull(sub, 8)[8:-16]
                self._corridors.append([p for p in pts if self.wall_sd(p[0], p[1]) > -14.0])
        best = None
        for pts in self._corridors:
            for p, q in zip(pts, pts[1:]):
                d, t = seg_d(x, y, p, q)
                if d < 18.0 and (best is None or d < best[0]):
                    best = (d, lerp(p[2], q[2], t))
        return None if best is None else best[1]


class Notches:
    """The ways in to the gateways: from the main road to each gateway's landmark, the land
    cut down level with the road (Blake, Oct 26: Canyon Dash's gateway stood up on the
    cliff, its spur climbing the wall, and you couldn't get into it). `gates`: {name: (x,
    y)}; the cut runs to `reach` m short of each."""

    def __init__(self, route_points, gates, reach=2.0, flat=9.0, blend=9.0):
        pts = catmull(route_points, 8)
        self.segs = []
        self.flat, self.blend = flat, blend
        for gx, gy in gates.values():
            p = min(pts, key=lambda q: (q[0] - gx) ** 2 + (q[1] - gy) ** 2)
            d = math.hypot(gx - p[0], gy - p[1]) or 1.0
            ux, uy = (gx - p[0]) / d, (gy - p[1]) / d
            self.segs.append(((p[0], p[1]), (gx - ux * reach, gy - uy * reach), p[2] - 0.3))

    def apply(self, h, x, y):
        for a, b, z in self.segs:
            if h <= z:
                continue
            d, _ = seg_d(x, y, a, b)
            if d < self.flat + self.blend:
                h = lerp(h, z, smooth((self.flat + self.blend - d) / self.blend))
        return h
