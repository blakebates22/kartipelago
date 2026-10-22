# Snow Dragon Pass's land, roads and gameplay (see snow_dragon_pass.py and snow_land.py):
# the mountains, the far peaks, the frozen gorge, the branch roads (the Frozen Supply
# Road and the Frozen Aqueduct) with their crags and tunnels, the whole-lap routes the
# rivals drive, the checkpoints on every branch, the pickups and the light. The
# buildings, people, weather and the ice dragon are snow_town.py.
# SPDX-License-Identifier: MIT

import math

import course_kit as kit
import snow_land as L
from course_kit import Vector, bmesh, lerp

# ------------------------------------------------------------------ shared


class Way:
    """A stretch of road as samples (x, y, z, width, s), looked up by distance like the
    course's own route: `at(s)` gives a kit.Sample with its tangent and right vector.
    The main road is the course itself; the branches are lanes (snow_land.LANES)."""

    def __init__(self, name, pts):
        self.name = name
        self.pts = pts
        self.s0 = pts[0][4]
        self.s1 = pts[-1][4]

    def at(self, s):
        s = min(max(s, self.s0), self.s1)
        k = 0
        lo, hi = 0, len(self.pts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self.pts[mid][4] <= s:
                lo = mid
            else:
                hi = mid - 1
        k = min(lo, len(self.pts) - 2)
        a, b = self.pts[k], self.pts[k + 1]
        f = (s - a[4]) / max(1e-6, b[4] - a[4])
        p = Vector((lerp(a[0], b[0], f), lerp(a[1], b[1], f), lerp(a[2], b[2], f)))
        out = kit.Sample(p, lerp(a[3], b[3], f), 0.0, s)
        t = Vector((b[0] - a[0], b[1] - a[1], b[2] - a[2])).normalized()
        out.t = t
        h = Vector((t.x, t.y, 0)).normalized()
        out.r = Vector((h.y, -h.x, 0))
        return out


class Scene:
    """What the scenery builders share."""

    MERGED = {"Landmarks": "Town", "Village": "Town", "Plants": "Props"}

    def __init__(self, c):
        self.c = c
        self.ground_obs = []
        self.lights = {}
        self.footprints = []
        self.cache = {}
        self.crowd = []
        self.rocks = []
        self.lanes = {}

    def light(self, kind, x, y, z):
        self.lights.setdefault(kind, []).append((x, y, z))

    def put(self, proto, x, y, z, rot=0.0, scale=1.0, coll="Props", role="visual"):
        return self.c.place(proto, x, y, z, rot, scale, coll=self.MERGED.get(coll, coll), role=role)

    def ground(self, x, y):
        z = self.c.ground_z(x, y, self.ground_obs)
        return z if z is not None else self.info(x, y)

    def info(self, x, y):
        k = (round(x, 2), round(y, 2))
        v = self.cache.get(k)
        if v is None:
            v = L.ground(x, y)
            self.cache[k] = v
        return v

    def free(self, x, y, r):
        return all(math.hypot(x - fx, y - fy) > r + fr for fx, fy, fr in self.footprints)


def game_entity(c, kind, x, y, z, **extra):
    gx, gy, gz = c.game(x, y, z)
    c.entity(kind, x=round(gx, 2), y=round(gy, 2), z=round(gz, 2), **extra)


def lane_tree(c):
    t = getattr(c, "_lane_tree", None)
    if t is None:
        from mathutils import kdtree

        t = kdtree.KDTree(max(1, len(c.lane_samples)))
        for i, q in enumerate(c.lane_samples):
            t.insert(Vector((q.p.x, q.p.y, 0)), i)
        t.balance()
        c._lane_tree = t
    return t


def lane_nearest(c, x, y):
    """The branch-road sample nearest (x, y), ignoring height, and how far it is."""
    _, i, d = lane_tree(c).find(Vector((x, y, 0)))
    return c.lane_samples[i], d


def clear(c, x, y, margin):
    """Far enough from every road (the main road and the branches)."""
    smp, d = c.nearest(x, y)
    if d <= smp.w / 2 + margin:
        return False
    q, d = lane_nearest(c, x, y)
    return d > q.w / 2 + margin


# ------------------------------------------------------------------ the branch roads

LANE_KINDS = {
    # The Frozen Supply Road: wide, timber rails, snowbanks.
    "supply": {"mat": "sdp_road", "surface": "snow_stone", "shoulder": 1.3, "shoulder_mat": ("sdp_snowbank", "packed_snow"),
               "barrier": 1.0, "barrier_mat": ("weathered_timber", "wall")},
    # The Frozen Aqueduct: the old channel road, frosted ashlar parapets.
    "aqueduct": {"mat": "sdp_road", "surface": "snow_stone", "shoulder": 1.3, "shoulder_mat": ("sdp_snowbank", "packed_snow"),
                 "barrier": 1.1, "barrier_mat": ("sdp_aqueduct", "wall")},
}

# Tunnels on the branches: (branch, from corner, fraction, to corner, fraction).
TUNNELS = [
    ("supply", "b3", 0.55, "b4", 0.55),  # the blue ice cavern, through the spur
    ("aqueduct", "q3", 0.0, "q4", 0.75),  # the aqueduct's tunnel bends through the crag
]
JOIN = 70.0  # metres of a lane at each end with no rails (where it leaves / meets the main road)
SINK = 0.05  # a lane sits this far below the main road where the two overlap


def tunnel_span(branch):
    for b, n0, f0, n1, f1 in TUNNELS:
        if b == branch:
            lap = L.LAPS[L.LANES[branch][0]]
            return lap.at(n0, f0), lap.at(n1, f1)
    return None


def lanes(c, sc):
    """The branch roads, built from their laps' own points: open (and a hair lower than
    the main road) where they leave and rejoin it, railed between, bored through rock
    in their tunnels, raised clear of the land over drops."""
    import dry_gulch

    c.lane_samples = []
    c.lane_ways = []
    for branch in ("supply", "aqueduct"):
        pts = L.lane_points(branch, 3.0)
        sc.lanes[branch] = Way(branch, pts)
        s0, s1 = pts[0][4], pts[-1][4]
        tun = tunnel_span(branch)

        def kind(s):
            if s < s0 + JOIN or s > s1 - JOIN:
                return "open"
            if tun and tun[0] - 6 < s < tun[1] + 6:
                return "tunnel"
            x, y, _ = L.LAPS[L.LANES[branch][0]].point_at(s)
            z = L.road_z(L.LAPS[L.LANES[branch][0]], s)
            if min(sc.info(x + ox, y + oy) for ox, oy in ((0, 0), (5, 0), (-5, 0), (0, 5), (0, -5))) < z - 3.5:
                return "bridge"
            return "rail"

        runs = []
        for p in pts:
            k = kind(p[4])
            if runs and runs[-1][0] == k:
                runs[-1][1].append(p)
            else:
                if runs:
                    runs[-1][1].append(p)
                runs.append([k, [p]])
        # Merge stretches shorter than 9 m into the one before.
        merged = []
        for k, ps in runs:
            if merged and (len(ps) < 4 or merged[-1][0] == k):
                merged[-1][1] += ps[1:]
            else:
                merged.append([k, ps])
        opt = LANE_KINDS[branch]
        for n, (k, ps) in enumerate(merged):
            if len(ps) < 2:
                continue
            seg = []
            for x, y, z, w, s in ps:
                # Where it overlaps the main road, a hair below it (the main road shows).
                sink = SINK if (s < s0 + JOIN or s > s1 - JOIN) else 0.0
                seg.append((x, y, z - sink, w, s))
            name = "%s %02d %s" % (branch.title(), n + 1, k)
            ground = k in ("open", "rail")
            barrier = 0.0 if k in ("open", "tunnel") else opt["barrier"]
            deck = 4.0 if k == "bridge" else 0.0
            w = sum(p[3] for p in ps) / len(ps)
            dry_gulch.lane(c, name, seg, opt["mat"], opt["surface"], width=w, shoulder=opt["shoulder"], shoulder_mat=opt["shoulder_mat"],
                           barrier=barrier, barrier_mat=opt["barrier_mat"], deck=deck, deck_mat=("sdp_aqueduct", "wall"), ground=ground)
        for x, y, z, w, s in pts:
            c.lane_samples.append(kit.Sample(Vector((x, y, z)), w, 0.0, s))
            c.lane_ways.append(branch)


# ------------------------------------------------------------------ junction rails


def rail_strip(c, name, pts, mat, h=1.0, t=0.5):
    """A rail along a polyline of edge points (x, y, z): a solid strip, `h` high and `t`
    thick (a wall to the karts)."""
    bm = bmesh.new()
    rings = []
    for i, (x, y, z) in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        d = Vector((b[0] - a[0], b[1] - a[1], 0)).normalized()
        n = Vector((d.y, -d.x, 0)) * (t / 2)
        base = Vector((x, y, z - 0.3))
        rings.append([bm.verts.new(base - n), bm.verts.new(base + n), bm.verts.new(base + n + Vector((0, 0, h + 0.3))),
                      bm.verts.new(base - n + Vector((0, 0, h + 0.3)))])
    for lo, hi in zip(rings, rings[1:]):
        for k in range(4):
            bm.faces.new((lo[k], lo[(k + 1) % 4], hi[(k + 1) % 4], hi[k]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    ob = c.mesh_object(name, bm, "Bridges")
    c.assign(ob, c.lib(*mat))
    return ob


def junction_rails(c, sc):
    """Where a branch leaves or joins the main road, neither road has rails of its own;
    instead a rail runs round the outside edge of the two together (wherever one road's
    edge isn't inside the other's surface), so the junction is open between them and
    closed to the drops beyond."""
    from mathutils import kdtree

    SH = 1.5  # shoulder width (about), metres
    roads = {"main": [(q.p.copy(), q.w, q.r.copy(), q.s) for q in c.S]}
    for branch, way in sc.lanes.items():
        rr = []
        for x, y, z, w, ls in way.pts:
            q = way.at(ls)
            rr.append((Vector((x, y, z)), w, q.r.copy(), ls))
        roads[branch] = rr
    trees = {}
    for name, rr in roads.items():
        t = kdtree.KDTree(len(rr))
        for i, (p, w, r, ss) in enumerate(rr):
            t.insert(Vector((p.x, p.y, 0)), i)
        t.balance()
        trees[name] = t

    def covered(pt, other):
        _, i, d = trees[other].find(Vector((pt.x, pt.y, 0)))
        p, w, r, ss = roads[other][i]
        return d < w / 2 + SH - 0.2 and abs(p.z - pt.z) < 3.0

    windows = []
    for (a, b), branch in ((L.SPLIT1, "supply"), (L.SPLIT2, "aqueduct")):
        lane = roads[branch]
        ls0, ls1 = lane[0][3], lane[-1][3]
        windows.append(("main", lambda ss, a=a: a - 12.0 < ss < a + 70.0, branch))
        windows.append(("main", lambda ss, b=b: b - 70.0 < ss < b + 12.0, branch))
        windows.append((branch, lambda ss, ls0=ls0: ss < ls0 + JOIN, "main"))
        windows.append((branch, lambda ss, ls1=ls1: ss > ls1 - JOIN, "main"))
    n = 0
    for name, inwin, other in windows:
        for side in (-1, 1):
            run = []
            for p, w, r, ss in roads[name]:
                if not inwin(ss):
                    continue
                e = p + r * side * (w / 2 + SH + 0.25)
                if covered(e, other):
                    if len(run) > 2:
                        n += 1
                        rail_strip(c, "Junction Rail %02d" % n, run, ("weathered_timber", "wall"))
                    run = []
                else:
                    run.append((e.x, e.y, p.z))
            if len(run) > 2:
                n += 1
                rail_strip(c, "Junction Rail %02d" % n, run, ("weathered_timber", "wall"))


# ------------------------------------------------------------------ the land


def land_mat(x, y, z, nz, d_road, w_road):
    near = d_road < w_road / 2 + 2.0
    if L.gorge_d(x, y) < L.GORGE_HW + 40 and z < L.FLOOR + 8:
        return ("sdp_ice_channel", "abyss")  # the gorge's floor: you're put back on the road
    if nz < 0.5:
        # Mostly snow-laden ledges, bare dark slate in patches where the wind scours it.
        return ("sdp_slate", "wall") if L.noise(x, y, 0.018, 21.0) > 0.35 else ("sdp_slate_snow", "wall")
    if nz < 0.78:
        return ("sdp_scree", "deep_snow")
    if near:
        return ("sdp_snowbank", "packed_snow")
    return ("sdp_snowfield", "deep_snow")


def land(c, sc):
    x0, x1, y0, y1 = L.GRID

    def classify(cen, n, info):
        d, w = info["d"], info["sample"].w
        q, dd = lane_nearest(c, cen.x, cen.y)
        if dd < d:
            d, w = dd, q.w
        return land_mat(cen.x, cen.y, cen.z, n.z, d, w)

    ter = c.terrain("Land", x0, x1, y0, y1, L.CELL, sc.info, classify, near=12.0, fade=12.0)
    sc.ground_obs = [ter]
    sc.land = ter

    # A hidden flat floor just under the land near every road (over steep faces, which
    # count only as walls, there's always ground below).
    def under(x, y):
        if c.nearest(x, y)[1] > 60 and lane_nearest(c, x, y)[1] > 60:
            return None
        nt = sc.info(x, y)
        w, z = c.road_height(x, y, 12.0, 12.0, 0.2, nt)
        return lerp(nt, z, w) - 0.6

    c.underfloor_flat("Underfloor", x0, x1, y0, y1, L.CELL, under, c.lib("sdp_snowfield", "deep_snow"))
    # The gorge's floor: fall in and you're put back on the road.
    c.underfloor_flat("Gorge Floor", x0, x1, y0, y1, L.CELL * 2,
                      lambda x, y: L.FLOOR - 4.0 if L.gorge_d(x, y) < L.GORGE_HW + 40 else None, c.lib("sdp_ice_channel", "abyss"))
    far_land(c)
    return ter


FAR = (-3600.0, 3600.0, -3600.0, 3600.0)


def far_natural(x, y):
    X0, X1, Y0, Y1 = L.GRID
    if X0 <= x <= X1 and Y0 <= y <= Y1:
        return L.FLOOR - 10.0
    d = max(X0 - x, x - X1, Y0 - y, y - Y1, 0.0)
    # Ranges of great peaks all round, the nearest the highest, snow to their feet.
    z = L.RIM - 20.0 + 40.0 * L.noise(x, y, 0.004, 3.0)
    ring = L.sm(d / 500.0)
    peaks = 160.0 * max(0.0, L.noise(x, y, 0.0023, 11.0)) + 90.0 * abs(L.noise(x, y, 0.006, 13.0))
    # The gorge runs on south between the ranges.
    if y < Y0 + 200 and abs(x - 60.0 - 80.0 * math.sin(y / 500.0)) < 160:
        k = L.sm((abs(x - 60.0 - 80.0 * math.sin(y / 500.0)) - 30.0) / 130.0)
        return lerp(L.FLOOR, z + ring * peaks, k)
    return z + ring * peaks


def far_land(c):
    X0, X1, Y0, Y1 = L.GRID

    def cls(cen, n, info):
        if X0 + 30 < cen.x < X1 - 30 and Y0 + 30 < cen.y < Y1 - 30:
            return None
        if n.z < 0.55:
            return ("sdp_slate_snow", "wall")
        return ("sdp_snowfield", "deep_snow")

    fx0, fx1, fy0, fy1 = FAR
    far = c.terrain("Far Land", fx0, fx1, fy0, fy1, 80.0, far_natural, cls, near=0.0, fade=1.0)
    far["kp_role"] = "visual"
    return far


# ------------------------------------------------------------------ rocks and tunnels


def bore(c, rock, pts, half, height, pad=10.0):
    """Cut a tunnel through `rock` along a lane's points (x, y, z, w, s), padded at both
    ends (course_kit.tunnel does the same along the main route)."""
    prof = [(-half, -0.4), (half, -0.4), (half, height * 0.62), (half * 0.62, height), (-half * 0.62, height), (-half, height * 0.62)]
    bm = bmesh.new()
    rings = []
    ext = [pts[0]] * 0 + pts

    def frame(i):
        a = ext[max(0, i - 1)]
        b = ext[min(len(ext) - 1, i + 1)]
        t = Vector((b[0] - a[0], b[1] - a[1], 0)).normalized()
        return Vector((ext[i][0], ext[i][1], ext[i][2])), Vector((t.y, -t.x, 0)), t

    p0, r0, t0 = frame(0)
    p1, r1, t1 = frame(len(ext) - 1)
    centres = [(p0 - t0 * pad, r0)] + [frame(i)[:2] for i in range(len(ext))] + [(p1 + t1 * pad, r1)]
    for p, r in centres:
        rings.append([bm.verts.new(p + r * a + Vector((0, 0, b))) for a, b in prof])
    m = len(prof)
    for lo, hi in zip(rings, rings[1:]):
        for k in range(m):
            bm.faces.new((lo[k], lo[(k + 1) % m], hi[(k + 1) % m], hi[k]))
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cutter = c.mesh_object("Tunnel Cutter", bm, "Rocks", "visual")
    import bpy

    mod = rock.modifiers.new("Tunnel", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
    mod.object = cutter
    bpy.context.view_layer.objects.active = rock
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter)
    return rock


def crags(c, sc):
    """The rock the branches' tunnels bore through: the spur over the Supply Road's ice
    cavern, and the crag the aqueduct bends through."""
    sc.tunnels = {}
    for branch, n0, f0, n1, f1 in TUNNELS:
        way = sc.lanes[branch]
        a, b = tunnel_span(branch)
        pts = [p for p in way.pts if a <= p[4] <= b]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        rx = (max(xs) - min(xs)) / 2 + 14.0
        ry = (max(ys) - min(ys)) / 2 + 14.0
        zlo = min(p[2] for p in pts)
        top = max(p[2] for p in pts) + 30.0
        bands = [(1.0, 0.0), (1.0, 0.3), (0.9, 0.38), (0.84, 0.66), (0.7, 0.74), (0.5, 1.0)]
        rock = c.rock_mass("%s Crag" % branch.title(), cx, cy, rx, ry, top, z0=zlo - 16.0, n=28, seed=31 + len(sc.rocks),
                           bands=bands, base=zlo - 2.0)
        half = max(p[3] for p in pts) / 2 + 4.5
        bore(c, rock, pts, half, 10.5, pad=6.0)
        c.paint_rock(rock, ("sdp_slate", "wall"), ("sdp_snowfield", "deep_snow"), top_z=top - 10.0)
        # The tunnel's own faces: blue ice (the cavern) or old stone (the aqueduct).
        inner = ("sdp_cavern", "wall") if branch == "supply" else ("sdp_aqueduct", "wall")
        faces = []
        for p in rock.data.polygons:
            ce = p.center
            if any(math.hypot(ce.x - q[0], ce.y - q[1]) < half + 1.0 and q[2] - 1.0 < ce.z < q[2] + 11.5 for q in pts[::2]):
                faces.append(p.index)
        c.assign(rock, c.lib(*inner), faces)
        sc.rocks.append(rock)
        sc.ground_obs.append(rock)
        sc.tunnels[branch] = (a, b, half)


# ------------------------------------------------------------------ the frozen gorge


def gorge(c, sc):
    """The frozen river at the gorge's foot (visual: the floor below puts you back), and
    the frozen falls down from the massif at its head."""
    import props

    path = []
    for a, b in zip(L.GORGE, L.GORGE[1:]):
        n = max(2, int(math.dist(a, b) / 8.0))
        for k in range(n):
            t = k / n
            path.append((lerp(a[0], b[0], t), lerp(a[1], b[1], t), 2 * L.GORGE_HW + 4.0, L.FLOOR + 0.3))
    path.append((L.GORGE[-1][0], L.GORGE[-1][1], 2 * L.GORGE_HW + 4.0, L.FLOOR + 0.3))
    c.ribbon("Frozen River", path, 2 * L.GORGE_HW, L.FLOOR + 0.3, c.lib("sdp_ice_channel"), role="visual")
    lx, ly = L.GORGE[0]
    top = sc.info(lx, ly + 22) - 2.0
    out = []
    if top > L.FLOOR + 20:
        props.falls(c, "Gorge Falls", lx, ly, top, L.FLOOR + 0.5, 14.0, 22.0, facing=-1, throw=6.0, bulge=1.4, veils=2,
                    mats=("frost_falls", "icefall_blue", "glacier_ice"))
        out.append((lx, ly, top))
    return out


# ------------------------------------------------------------------ whole-lap routes


def lap_routes(c):
    """The three other whole laps as routes the rivals can drive (route.json), each a
    closed curve through its own points with its road's width."""
    import bpy

    ids = []
    for cid, lap in L.LAPS.items():
        if cid == "main":
            continue
        pts = L.lap_points(lap, 6.0)
        cd = bpy.data.curves.new(cid, "CURVE")
        cd.dimensions = "3D"
        sp = cd.splines.new("BEZIER")
        sp.bezier_points.add(len(pts) - 1)
        for bp, (x, y, z, w) in zip(sp.bezier_points, pts):
            bp.co = (x, y, z)
            bp.handle_left_type = bp.handle_right_type = "AUTO"
            bp.radius = w / 16.0
        sp.use_cyclic_u = True
        sp.resolution_u = 12
        ob = bpy.data.objects.new(cid, cd)
        c.coll("Paths").objects.link(ob)
        ob["kp_route"] = cid
        ob["kp_width"] = 16.0
        ob.hide_set(True)
        ob.hide_render = True
        ids.append(cid)
    return ids


# ------------------------------------------------------------------ checkpoints


def _gate_on(c, scene, index, way, s, route, width_margin=7.0, height=8.0):
    from kartipelago_tools import checkpoints as cpts

    q = way.at(s)
    t = q.t
    g = cpts.make(scene, index, q.p.copy(), (t.x, t.y), q.w + 2 * width_margin, height, route=route,
                  name="CP %s %d" % (route, index))
    a = way.at(s + 4.0)
    cpts.add_respawn(g, a.p.copy(), (a.t.x, a.t.y))
    return g


class MainWay:
    """The main road as a Way (main-lap distances)."""

    name = "main"

    def __init__(self, c):
        self.c = c

    def at(self, s):
        return self.c.at(s % self.c.length)


FRACS = (0.18, 0.4, 0.62, 0.84)  # where the checkpoints sit along each branch


def checkpoints(c, sc):
    """The lap's checkpoints: the add-on's generator on the shared road (none inside the
    splits), then the same number on each branch of each split, numbered together, so
    passing either branch's gate counts the same. Each branch gate respawns you on its
    own branch."""
    from kartipelago_tools import checkpoints as cpts

    a1, b1 = L.SPLIT1
    a2, b2 = L.SPLIT2
    gates = c.checkpoints(
        extra=[a1 - 25.0, b1 + 30.0, a2 - 25.0, b2 + 30.0, L.MAIN.at("g1", 0.6), L.MAIN.at("m2", 0.3), L.MAIN.at("f2", 0.4)],
        avoid=[(a1 + 2.0, b1 - 2.0), (a2 + 2.0, b2 - 2.0)],
        height=8.0,
    )
    main = MainWay(c)
    temp = 100
    for (a, b), branch in (((a1, b1), "supply"), ((a2, b2), "aqueduct")):
        lap_id, ls0, ls1 = L.LANES[branch]
        way = sc.lanes[branch]
        for f in FRACS:
            # Main branch gate at the same share of its own stretch.
            sm_ = a + (b - a) * f
            sl = ls0 + (ls1 - ls0) * f
            sm_ = _clear_spot(c, sc, main, sm_, a, b)
            sl = _clear_spot(c, sc, way, sl, ls0, ls1)
            _gate_on(c, c.scene, temp, main, sm_, "main")
            _gate_on(c, c.scene, temp, way, sl, branch)
            temp += 1
    cpts.renumber(c.scene)
    return gates


def _clear_spot(c, sc, way, s, lo, hi):
    """Nudge a branch gate along its road until no other road at about its height is
    within reach of it (a crossing, or the other branch close by)."""
    name = getattr(way, "name", "main")
    others = [(o, "main") for o in c.S[::3]] + list(zip(c.lane_samples, c.lane_ways))[::2]

    def ok(ss):
        q = way.at(ss)
        for o, wn in others:
            if wn == name and abs(o.s - ss) < 40.0:
                continue  # this same stretch of road
            if abs(o.p.z - q.p.z) < 14.0 and math.hypot(o.p.x - q.p.x, o.p.y - q.p.y) < q.w / 2 + 7.0 + o.w / 2 + 6.0:
                return False
        return True

    for k in range(14):
        for sign in (1, -1):
            ss = s + sign * k * 6.0
            if lo + 30 < ss < hi - 30 and ok(ss):
                return ss
    return s


# ------------------------------------------------------------------ pickups


def pickups(c, sc):
    """Zippers where a clean exit is worth chaining, eggs (bananas) and balloons, on the
    shared road and on every branch (a branch's are placed along its own lap route)."""
    M = L.MAIN

    def on(lap_id, s, kind, **extra):
        n = sum(e["type"] == kind for e in c.entities) + 1
        pre = {"zipper": "zip", "bananas": "ban", "balloon": "bal"}[kind]
        e = {"id": "%s_%02d" % (pre, n), "type": kind, "at": round(s, 1), "across": extra.pop("across", 0.0), "route": lap_id}
        e.update(extra)
        c.entities.append(e)

    # Shared road and main branches.
    for s in (M.at("g2", 0.7), M.at("a4", 0.4), M.at("m1", 0.8), M.at("r4", 0.5), M.at("f1", 0.6)):
        c.zipper(s, 0.0)
    for s, across in ((M.at("g1", 0.5), 0), (M.at("a3", 0.5), 0), (M.at("a6", 0.5), 3), (M.at("m2", 0.6), 0), (M.at("r2", 0.5), 0),
                      (M.at("r5", 0.5), -3), (M.at("f2", 0.5), 0)):
        c.bananas(s, across, count=5, gap=2.4)
    for s, across, col in ((M.at("st", 0.5), -4, "red"), (M.at("st", 0.5), 4, "blue"), (M.at("fork1", 0.3), 0, "green"),
                           (M.at("a2", 0.5), 0, "yellow"), (M.at("a5", 0.5), 0, "red"), (M.at("m1", 0.4), -4, "rainbow"),
                           (M.at("m1", 0.4), 4, "blue"), (M.at("fork2", 0.2), 0, "green"), (M.at("r3", 0.6), 0, "yellow"),
                           (M.at("r5", 0.8), 0, "red"), (M.at("f2", 0.8), -3, "blue"), (M.at("f2", 0.8), 3, "rainbow")):
        c.balloon(s, across, col)
    # The Supply Road and the Aqueduct: their own zippers, eggs and balloons.
    SR, CA = L.LAPS["Lap Supply Ridge"], L.LAPS["Lap Cliff Aqueduct"]
    on("Lap Supply Ridge", SR.at("b2", 0.75), "zipper")
    on("Lap Supply Ridge", SR.at("b3", 0.3), "bananas", across=3.0, count=5, gap=2.4)
    on("Lap Supply Ridge", SR.at("b2", 0.3), "balloon", across=-4.0, color="yellow")
    on("Lap Supply Ridge", SR.at("b2", 0.3), "balloon", across=4.0, color="red")
    on("Lap Cliff Aqueduct", CA.at("q2", 0.0), "zipper")
    on("Lap Cliff Aqueduct", CA.at("q1", 0.9), "bananas", across=0.0, count=5, gap=2.4)
    on("Lap Cliff Aqueduct", CA.at("q2", 0.6), "balloon", across=0.0, color="blue")


# ------------------------------------------------------------------ the light


def light(c, sc):
    """A cold, overcast light from high in the north-west; the valleys and the gorge in
    blue shade; the caverns glowing blue, the tunnel dim; warm round every lantern,
    brazier and window."""
    c.merge_props(("Props", "Town", "Rocks Small"), cell=260.0)
    c.merge_props(("Far Rocks",), cell=2400.0)
    land = [sc.land] + sc.rocks
    built = [o for name in ("Bridges", "Arch", "Props", "Town", "Rocks Small") for o in c.coll(name).objects if o.type == "MESH" and o.data.users == 1]
    c.preset("sun", land + built, 0.3, color=(0.86, 0.9, 1.0))
    c.preset("bottoms", land, 0.32)

    def deep(w):
        return w.z < 62.0

    c.glow([sc.land], [], 1.0, (1, 1, 1), base=(0.72, 0.78, 0.92), region=deep)
    for branch, (a, b, half) in getattr(sc, "tunnels", {}).items():
        way = sc.lanes[branch]

        def inside(w, way=way, a=a, b=b, half=half):
            for s in range(int(a) - 6, int(b) + 6, 4):
                q = way.at(s)
                if math.hypot(w.x - q.p.x, w.y - q.p.y) < half + 2 and w.z < q.p.z + 12:
                    return True
            return False

        tint = (0.55, 0.75, 1.0) if branch == "supply" else (0.5, 0.52, 0.6)
        c.glow(land + built, [], 1.0, (1, 1, 1), base=tint, region=inside)
    colours = {"fire": (14.0, (1.0, 0.72, 0.42)), "lamp": (10.0, (1.0, 0.78, 0.5)), "ice": (12.0, (0.6, 0.85, 1.0))}
    for kind, pts in sc.lights.items():
        if kind in colours and pts:
            r, col = colours[kind]
            c.glow(land + built, pts, r, col, base=1.0)
    kit.paint.shade_roads(c.pieces + getattr(c, "lanes", []), 0.4)


# ------------------------------------------------------------------ build


def build(c, mod):
    import snow_town as town

    sc = Scene(c)
    sc.mod = mod
    lanes(c, sc)  # first: the land meets its roads
    junction_rails(c, sc)
    land(c, sc)
    crags(c, sc)
    sc.falls = gorge(c, sc)
    c.start_line()
    town.build(c, sc)
    checkpoints(c, sc)
    pickups(c, sc)
    sc.lap_ids = lap_routes(c)
    town.entities(c, sc)
    light(c, sc)
    return sc
