# Canyon Dash's great walls (see canyon_dash.py): the inner gorge from its head to the
# horizon, and the outer canyon's rim walls, built as meshes that follow the cliffs, so
# each rock layer is a clean band and each ledge a clean step (a height-field grid can
# only stair-step a wavy cliff). The land grid leaves holes where these stand.
# SPDX-License-Identifier: MIT

import math

from course_kit import bmesh, lerp


class Strip:
    """A wall mesh: columns of points (each column a cross-section of the wall), stitched
    into quads; faces painted by height and slope."""

    def __init__(self):
        self.cols = []

    def add(self, col):
        self.cols.append(col)

    def runs(self):
        """Runs of consecutive usable columns (None marks a gap)."""
        out, cur = [], []
        for col in self.cols:
            if col is None:
                if len(cur) > 1:
                    out.append(cur)
                cur = []
            else:
                cur.append(col)
        if len(cur) > 1:
            out.append(cur)
        return out

    def build(self, c, name, paint, coll="Canyon", role="both"):
        bm = bmesh.new()
        for run in self.runs():
            vs = [[bm.verts.new(p) for p in col] for col in run]
            for a, b in zip(vs, vs[1:]):
                for k in range(len(a) - 1):
                    try:
                        bm.faces.new((a[k], b[k], b[k + 1], a[k + 1]))
                    except ValueError:
                        pass
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.01)
        bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.01)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        # The sheet as a whole looks up (floors up, so its walls face the open air).
        if sum(f.normal.z * f.calc_area() for f in bm.faces) < 0:
            for f in bm.faces:
                f.normal_flip()
        ob = c.mesh_object(name, bm, coll, role)
        groups = {}
        for p in ob.data.polygons:
            groups.setdefault(paint(p.center, p.normal), []).append(p.index)
        for m, faces in groups.items():
            c.assign(ob, c.lib(*m), faces)
        ob.data.shade_flat()
        return ob


def _clear_of_roads(c, pts, margin=3.0):
    """No point of a column on (or under) a road that sits on the land."""
    for p in pts:
        smp, d = c.nearest(p[0], p[1])
        if smp.ground and d < smp.w / 2 + margin and p[2] < smp.p.z + 4.0:
            return False
    return True


def _band_rows(bands, k, x, seed):
    """The wall's profile at x: (u, share of the drop so far) rows, each inner band edge
    wandering in and out a little (buttresses and alcoves), always in order; the rim
    (u = 0) and the foot (the whole width) stay put."""
    rows = [(0.0, 0.0)]
    base = 0.0
    done = 0.0
    last = len(bands) - 1
    for j, (w, share) in enumerate(bands):
        base += w * k
        n = 0.0 if j == last else 0.9 * k * (math.sin(x / (13.0 + 4.0 * j) + seed + j * 1.3) + 0.6 * math.sin(x / 5.7 + j * 2.1 + seed))
        u = max(rows[-1][0] + 0.5, base + n)
        if w > 5.0:
            # A talus slope: a middle row, so it bellies out.
            mid = rows[-1][0] + (u - rows[-1][0]) * 0.5
            rows.append((mid, done + share * 0.72))
        done += share
        rows.append((u, done))
    return rows


def gorge_rim(cd, x, side, reach=260.0):
    """Where the inner gorge's rim is at x on one side (side +1 north, -1 south): the
    nearest point out from its centre line where it stops being gorge."""
    cy = cd.gorge_c(min(x, cd.X_HEAD))
    lo, hi = 0.0, reach
    if cd.gorge_u(x, cy + side * hi) > 0:
        return cy + side * hi
    for _ in range(40):
        mid = (lo + hi) / 2
        if cd.gorge_u(x, cy + side * mid) > 0:
            lo = mid
        else:
            hi = mid
    return cy + side * (lo + hi) / 2


def gorge_paint(cd):
    def paint(p, n):
        zt = cd.terrace_z(p.x)
        low = p.z < zt - 8.0
        if n.z < 0.55:
            return (cd._layer(p.z), "wall")
        if not low:
            return ("talus", "loose_sand") if n.z < 0.8 else ("desert_sand", "loose_sand")
        if p.z < cd.Z_RIVER + 1.0:
            return ("strata_purple", "abyss")
        return ("talus", "abyss")

    return paint


def gorge(c, cd, far_x=-2560.0):
    """The inner gorge: a cross-section every few metres from its head west to the
    horizon, rim to rim: skirt, rim, cliffs and ledges down to the river floor and up
    the other side. Its rounded head is a fan of sections round the plunge pool."""
    bands = cd.INNER_BANDS
    strip = Strip()
    xs = []
    x = cd.X_HEAD + 1.0
    while x > far_x:
        xs.append(x)
        x -= 4.0 if x > -440 else 10.0 if x > -900 else 20.0
    xs.reverse()
    far = Strip()
    gone = getattr(cd, "RUIN_OPEN", None)  # (the ruin: the walls down in a rockslide there)
    for x in xs:
        sec = gorge_section(cd, x, bands, far=x < -420)
        if gone and gone[0] <= x <= gone[1]:
            sec = None
        if x >= -460:
            strip.add(sec)
        if x <= -440:
            far.add(sec)
    strip.build(c, "Inner Gorge", gorge_paint(cd))
    # Far downstream only to be seen (no collision).
    far.build(c, "Inner Gorge Far", gorge_paint(cd), role="visual")
    # The head: rays round the plunge pool from due south, through east, to due north.
    head = Strip()
    hx, hy = cd.X_HEAD, cd.gorge_c(cd.X_HEAD)
    k = cd.inner_scale(hx)
    for j in range(0, 46):
        ang = -math.pi / 2 + math.pi * j / 45
        dx, dy = math.cos(ang), math.sin(ang)
        lo, hi = 0.0, 120.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if cd.gorge_u(hx + dx * mid, hy + dy * mid) > 0:
                lo = mid
            else:
                hi = mid
        r0 = (lo + hi) / 2
        rows = _band_rows(bands, k, ang * 60.0, 2.0)
        col = []
        top = cd.natural_outer(hx + dx * (r0 + 0.5), hy + dy * (r0 + 0.5))
        skirt = 5.5
        col.append((hx + dx * (r0 + skirt), hy + dy * (r0 + skirt), cd.natural_outer(hx + dx * (r0 + skirt), hy + dy * (r0 + skirt)) - 0.15))
        for u, f in rows:
            r = max(1.0, r0 - u)
            col.append((hx + dx * r, hy + dy * r, top - (top - cd.Z_RIVER) * f))
        col.append((hx, hy, cd.Z_RIVER))
        head.add(col)
    head.build(c, "Gorge Head", gorge_paint(cd))


def gorge_section(cd, x, bands, far=False):
    k = cd.inner_scale(x)
    skirt = 14.0 if far else 5.5
    out = []
    sides = []
    for side in (-1, 1):
        yr = gorge_rim(cd, x, side)
        top = cd.natural_outer(x, yr + side * 0.5)
        rows = _band_rows(bands, k, x, 0.0 if side < 0 else 3.0)
        cy = cd.gorge_c(min(x, cd.X_HEAD))
        pts = [(x, yr + side * skirt, cd.natural_outer(x, yr + side * skirt) - 0.15)]
        for u, f in rows:
            y = yr - side * u
            if (y - cy) * side < 2.0:
                y = cy + side * 2.0
            pts.append((x, y, top - (top - cd.Z_RIVER) * f))
        sides.append(pts)
    s, n = sides
    floor_mid = (x, (s[-1][1] + n[-1][1]) / 2, cd.Z_RIVER - 0.2)
    return s + [floor_mid] + list(reversed(n))


# ------------------------------------------------------------------ the rim walls


def rim_paint(cd):
    def paint(p, n):
        if n.z < 0.55:
            return (cd._layer(p.z), "wall")
        if n.z < 0.8:
            return ("talus", "loose_sand")
        return ("desert_sand", "loose_sand")

    return paint


def rim_walls(c, cd):
    """The outer canyon's walls where no road runs on them: the south rim (under the
    start's overlook, and west of the descent) and the north mesa's cliffs (behind the
    north terrace, the mesa's face over the gorge, and above the overlook). Returns the
    x-ranges each covers, for the land grid to leave out."""
    spans = {"south": [], "north": [], "east": []}
    for side, ranges in (("south", ((-2560.0, -150.0), (100.0, 400.0))), ("north", ((-2560.0, -158.0), (-134.0, 66.0), (74.0, 380.0)))):
        strip = Strip()
        far = Strip()
        for x0, x1 in ranges:
            x = x0
            prev = None
            while x <= x1:
                col = rim_section(c, cd, side, x, far=x < -420)
                ok = col is not None and (x < -420 or _clear_of_roads(c, col))
                gone = getattr(cd, "RUIN_RIM_OPEN", {}).get(side)  # (the ruin: down in a rockslide)
                if gone and gone[0] <= x <= gone[1]:
                    ok = False
                if x >= -460:
                    strip.add(col if ok else None)
                if x <= -440:
                    far.add(col if ok else None)
                if ok and prev is not None:
                    spans[side].append((prev, x))
                prev = x if ok else None
                x += 4.0 if x > -440 else 10.0 if x > -900 else 20.0
            strip.add(None)
            far.add(None)
        strip.build(c, "%s Rim" % side.title(), rim_paint(cd))
        far.build(c, "%s Rim Far" % side.title(), rim_paint(cd), role="visual")
    # The East Shelf's face, its sections running east-west.
    strip = Strip()
    y = -230.0
    prev = None
    while y <= 400.0:
        col = shelf_section(c, cd, y)
        ok = col is not None and _clear_of_roads(c, col)
        strip.add(col if ok else None)
        if ok and prev is not None:
            spans["east"].append((prev, y))
        prev = y if ok else None
        y += 4.0
    strip.build(c, "Shelf Face", rim_paint(cd))
    return spans


def shelf_section(c, cd, y):
    rim = cd.shelf_x(y)
    top = cd.natural_outer(rim + 0.5, y)
    width = sum(w for w, _ in cd.MESA_BANDS)
    foot = cd.plateau(rim - width, y)
    if top - foot < 2.0:
        return None
    rows = _band_rows(cd.MESA_BANDS, 1.0, y, 13.0)
    pts = [(rim + 5.5, y, cd.natural_outer(rim + 5.5, y) - 0.15)]
    for u, f in rows:
        pts.append((rim - u, y, top - (top - foot) * f))
    pts.append((rim - width - 5.5, y, cd.natural_outer(rim - width - 5.5, y) - 0.15))
    return pts


def rim_section(c, cd, side, x, far=False):
    """A cross-section of a rim wall at x: from the plateau (or mesa) out over the rim and
    down its layers to the terrace, stopping short of the inner gorge."""
    zt = cd.terrace_z(x)
    fade = cd.sm((420.0 - x) / 70.0)
    if side == "south":
        rim = cd.south_rim(x)
        sign = 1.0
        bands = cd.OUTER_BANDS
        top = max(cd.plateau(x, rim - 0.5), zt)
    else:
        rim = cd.north_rim(x)
        sign = -1.0
        bands = cd.MESA_BANDS
        mt = cd.mesa_top(x, rim + 0.5)
        top = max(mt if mt is not None else cd.plateau(x, rim + 0.5), zt)
    if top - zt < 2.0:
        return None
    skirt = 14.0 if far else 5.5
    rows = _band_rows(bands, 1.0, x, 5.0 if side == "south" else 9.0)
    pts = [(x, rim - sign * skirt, cd.natural_outer(x, rim - sign * skirt) - 0.15)]
    for u, f in rows:
        y = rim + sign * u
        if cd.gorge_u(x, y) > -2.0:
            break
        z = top - (top - zt) * f
        pts.append((x, y, lerp(cd.natural_outer(x, y), z, fade)))
    if len(pts) < 3:
        return None
    # Pad every column to the same row count (a short one ends in repeats at its foot).
    want = len(rows) + 2
    u_last = rows[-1][0]
    y = rim + sign * (u_last + skirt)
    end = (x, y, cd.natural_outer(x, y) - 0.15) if cd.gorge_u(x, y) < -2.0 else pts[-1]
    pts.append(end)
    while len(pts) < want:
        pts.append(pts[-1])
    return pts[:want]
