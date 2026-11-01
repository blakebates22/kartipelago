# The Dragon Kingdom v4: floating isles round the Citadel's spire (Blake, Oct 31: "This needs
# to be the most breathtaking kingdom by far"; he picked built for dragons, floating isles
# and sky bridges, and the reveal through the gate). Pure geometry, no Blender
# (sky_region.py builds it).
# SPDX-License-Identifier: MIT
#
# No ground: isles of rock hanging in the sky over a sea of cloud, held by chains of dragon
# light to the Citadel's spire in the middle. You come in over the Sky Bridge through the
# Sky Gate onto the Gate isle, over the gate bridge onto the Crown (the great isle round the
# spire's foot: Dragonfire Square, the avenue of giant steps up to the Citadel's door),
# and the road climbs the isles round the spire on sky bridges: Dragonspire Keep's isle
# (west), the Moonstone isle (north-west, the highest), Emberdeep Hold's isle (north-east,
# its lava falling off into the void), the Emerald Canyon's jungle isle (east), and back to
# the Crown.
#
# Blender coordinates (x east, y north, z up).

import math

VOID_Z = -130.0  # the abyss under it all (fall and you're put back)
CLOUD_Z = -110.0  # the sea of cloud, just over it

# The isles: name: (x, y, rx, ry, top height, look).
ISLES = {
    "crown": (0.0, 0.0, 168.0, 152.0, 10.0, "crown"),
    "gate": (0.0, -392.0, 56.0, 50.0, 6.0, "crown"),
    "keep": (-330.0, -10.0, 86.0, 78.0, 28.0, "keep"),
    "moon": (-180.0, 322.0, 78.0, 70.0, 58.0, "moon"),
    "hold": (200.0, 322.0, 82.0, 72.0, 40.0, "hold"),
    "canyon": (348.0, -40.0, 92.0, 82.0, 18.0, "canyon"),
}
SPIRE = (0.0, 62.0, 30.0)  # x, y, radius at its foot
SPIRE_TOP = 230.0
SQUARE = (0.0, -92.0, 28.0)  # Dragonfire Square, on the Crown (the hub)
CITADEL_DOOR = (0.0, 30.0)  # the Citadel's door in the spire's foot: the King's race


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def _seg(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / L2))
    return math.hypot(px - a[0] - t * dx, py - a[1] - t * dy), t


def isle_e(name, x, y):
    """How far out (x, y) is in an isle's footprint (1 at its rim), its edge wavering."""
    cx, cy, rx, ry, _z, _ = ISLES[name]
    a = math.atan2(y - cy, x - cx)
    wob = 1.0 + 0.07 * math.sin(3.0 * a + len(name)) + 0.04 * math.sin(7.0 * a + 2.0 * len(name))
    return math.hypot((x - cx) / rx, (y - cy) / ry) / wob


def isle_at(x, y):
    best = (None, 9.0)
    for name in ISLES:
        e = isle_e(name, x, y)
        if e < best[1]:
            best = (name, e)
    return best


def _top(name, x, y):
    cx, cy, rx, ry, z, _ = ISLES[name]
    e = isle_e(name, x, y)
    h = z + 1.0 * math.sin(x / 13.0) * math.cos(y / 17.0) + 1.6 * (1.0 - e * e)
    if name == "crown":
        # The Crown's plinth round the spire's foot, a tier up.
        sx, sy, sr = SPIRE
        d = math.hypot(x - sx, y - sy)
        h += 6.0 * smooth((sr + 70.0 - d) / 30.0)
    return h


def _land(x, y):
    name, e = isle_at(x, y)
    if name is None or e > 1.08:
        return VOID_Z
    if e > 1.0:
        return lerp(_top(name, x, y) - 10.0, VOID_Z, smooth((e - 1.0) / 0.08))
    return lerp(_top(name, x, y), _top(name, x, y) - 10.0, smooth((e - 0.97) / 0.03))


# ---------------------------------------------------------------- the road

# Round the isles, anticlockwise from the Crown's south side (x, y, height).
ROUTE = [
    (60.0, -132.0, 10.0),  # 0: the start, south of Dragonfire Square, westbound
    (-60.0, -132.0, 10.0),
    (-128.0, -84.0, 12.0),
    (-160.0, -52.0, 15.0),  # 3: off the Crown, the bridge west
    (-246.0, -32.0, 27.0),  # 4: onto Dragonspire Keep's isle
    (-318.0, -52.0, 28.0),
    (-382.0, 8.0, 28.0),
    (-346.0, 66.0, 28.0),  # 7: off the Keep's isle, the bridge north
    (-300.0, 150.0, 40.0),
    (-236.0, 252.0, 56.0),  # 9: onto the Moonstone isle (the highest)
    (-202.0, 318.0, 58.0),
    (-128.0, 344.0, 58.0),  # 11: off it, the long bridge east, north of the spire
    (-20.0, 372.0, 52.0),
    (118.0, 346.0, 41.0),  # 13: onto Emberdeep's isle
    (190.0, 300.0, 40.0),
    (250.0, 262.0, 40.0),  # 15: off it, the bridge south
    (300.0, 150.0, 28.0),
    (332.0, 36.0, 18.0),  # 17: onto the Emerald Canyon's isle
    (372.0, -40.0, 18.0),
    (330.0, -102.0, 18.0),
    (258.0, -92.0, 16.0),  # 20: off it, the bridge west
    (164.0, -100.0, 12.0),  # 21: onto the Crown
    (120.0, -128.0, 10.0),
]
# The gateways' landmarks (each on its isle, a spur to it from the road).
GATES = {
    "keep": (-372.0, -48.0),
    "moon": (-196.0, 364.0),
    "hold": (222.0, 352.0),
    "canyon": (396.0, -84.0),
}
# The Gate isle: the Sky Gate on its south rim (the passage), the bridge north to the Crown.
GATE_ZONE = (0.0, -424.0)
GATE_BRIDGE = [(0.0, -141.0), (0.0, -344.0)]  # (from the road's edge: all bridge, off the Crown's rim)


def _dense(points, every=4.0):
    n = len(points)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = points[(i - 1) % n], points[i], points[(i + 1) % n], points[(i + 2) % n]
        L = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        k = max(2, int(L / every))
        for j in range(k):
            t = j / k
            t2, t3 = t * t, t * t * t
            x = 0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y, lerp(p1[2], p2[2], t)))
    return out


LINE = _dense(ROUTE)
_GRID = {}
for _a, _b in zip(LINE, LINE[1:] + LINE[:1]):
    for _gx in range(int(math.floor(min(_a[0], _b[0]) / 24)) - 1, int(math.floor(max(_a[0], _b[0]) / 24)) + 2):
        for _gy in range(int(math.floor(min(_a[1], _b[1]) / 24)) - 1, int(math.floor(max(_a[1], _b[1]) / 24)) + 2):
            _GRID.setdefault((_gx, _gy), []).append((_a, _b))


def road_floor(x, y):
    best = (1e9, 0.0)
    for a, b in _GRID.get((int(math.floor(x / 24)), int(math.floor(y / 24))), ()):
        d, t = _seg(x, y, a, b)
        if d < best[0]:
            best = (d, lerp(a[2], b[2], t))
    return best


def natural(x, y):
    """The isles, the road's shelf cut level into them (only on an isle: over the void the
    road's a bridge)."""
    h = _land(x, y)
    if h < VOID_Z + 1.0:
        return h
    d, z = road_floor(x, y)
    if d < 8.0:
        return z - 0.25
    if d < 22.0:
        return lerp(z - 0.25, h, smooth((d - 8.0) / 14.0))
    return h


def look_at(x, y):
    name, e = isle_at(x, y)
    return ISLES[name][5] if name else "crown"
