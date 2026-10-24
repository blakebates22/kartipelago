# The eggs on a course: few, in small clusters, placed off the racing line.
# SPDX-License-Identifier: MIT
#
#   python3 tools/blender/prehistoric/eggs.py public/tracks/<id> [...]   (rewrites track.json)
#
# Ten eggs give the full speed bonus, and every course used to lay rows of five straight
# down the racing line, so two rows maxed you out without a choice. Now (Blake, Oct 24:
# "lets reduce the number of bananas") a lap has about 14: at most six clusters of two or
# three, each a short diagonal across the road (never a line along it), out toward the
# outside of the next bend, where the racing line isn't, or on alternate sides on a
# straight. Picking them up means leaving your line; ignoring them costs you the bonus.
#
# Plain Python (no Blender): course_kit.finish() runs it on every course it builds, and
# the command line converts packages already built. It reads route.json for the shape of
# each route, and only touches "bananas" entities.

import json
import math
import os
import sys

MAX_CLUSTERS = 6
SIZES = (3, 2)  # alternating
ALONG = 2.4  # metres between eggs along the road...
ACROSS = 2.2  # ...and across it: a diagonal
EDGE = 3.0  # kept this far inside the road's edge


def _routes(folder):
    with open(os.path.join(folder, "route.json"), encoding="utf-8") as f:
        r = json.load(f)
    out = {}
    for route in r["routes"]:
        pts = route["points"]
        d = [0.0]
        for a, b in zip(pts, pts[1:]):
            d.append(d[-1] + math.dist((a["x"], a["y"], a["z"]), (b["x"], b["y"], b["z"])))
        out[route["id"]] = (pts, d)
    return out


def _at(route, s):
    """Index of the route point at distance s (wrapping round a lap)."""
    pts, d = route
    s %= d[-1]
    lo, hi = 0, len(d) - 1
    while lo < hi:
        m = (lo + hi + 1) // 2
        if d[m] <= s:
            lo = m
        else:
            hi = m - 1
    return lo


def _heading(route, i):
    pts, _ = route
    a, b = pts[i], pts[(i + 1) % len(pts)]
    return math.atan2(b["x"] - a["x"], b["z"] - a["z"])


def _bend(route, s, ahead=45.0):
    """Which way the road bends over the next `ahead` metres: + left, - right (radians)."""
    i0, i1 = _at(route, s), _at(route, s + ahead)
    t = math.atan2(math.sin(_heading(route, i1) - _heading(route, i0)), math.cos(_heading(route, i1) - _heading(route, i0)))
    return t


def cluster(entities, routes):
    """Rewrite the bananas rows in `entities` (in place) as clusters; returns them."""
    rows = [e for e in entities if e.get("type") == "bananas"]
    if not rows:
        return entities
    keep = rows
    if len(rows) > MAX_CLUSTERS:
        # Evenly through the list (they're in lap order).
        step = len(rows) / MAX_CLUSTERS
        keep = [rows[int(k * step)] for k in range(MAX_CLUSTERS)]
    for e in rows:
        if e not in keep:
            entities.remove(e)
    for k, e in enumerate(keep):
        route = routes.get(e.get("route", "main")) or routes.get("main")
        n = SIZES[k % len(SIZES)]
        at = e["at"]
        if route is None:
            e.update(count=n, gap=ALONG)
            continue
        i = _at(route, at)
        w = route[0][i].get("width", 14.0)
        half = max(0.0, w / 2 - EDGE)
        b = _bend(route, at)
        if abs(b) > 0.25:
            side = 1 if b > 0 else -1  # bending left: the outside is the right (+)
        else:
            side = 1 if k % 2 else -1
        # Start toward the edge and run diagonally back in toward the middle.
        start = side * half
        e.update(at=round(at, 1), across=round(start, 1), count=n, gap=ALONG, spread=round(-side * ACROSS, 1))
    return entities


def apply(folder):
    path = os.path.join(folder, "track.json")
    with open(path, encoding="utf-8") as f:
        meta = json.load(f)
    before = sum(e.get("count", 1) for e in meta.get("entities", []) if e.get("type") == "bananas")
    cluster(meta.get("entities", []), _routes(folder))
    after = sum(e.get("count", 1) for e in meta.get("entities", []) if e.get("type") == "bananas")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")
    return before, after


if __name__ == "__main__":
    for folder in sys.argv[1:]:
        if os.path.exists(os.path.join(folder, "track.json")) and os.path.exists(os.path.join(folder, "route.json")):
            print(folder, *apply(folder))
