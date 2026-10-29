# Desert World's dressing, v5 (Blake, Oct 29: "much more exciting ... driving and visuals
# needs to be better. feel free to reshape"): great natural arches the road runs under,
# banded buttes standing out of the floors, the walls alive (saguaros, agaves and scrub on
# the ledges, cliff dwellings tucked under the overhangs), and the desert moving: vultures
# wheeling, tumbleweeds bowling across the road, the windmill's wheel turning, dust on the
# wind. (The dunes the road rides are desert_layout's.) desert_region.py calls these.
# SPDX-License-Identifier: MIT

import math
import random

import canyon_props as cp
import desert_layout as DL
import region_paint as paint
import region_props as rp
import region_ruin as ruin
from course_kit import Vector, bmesh, rnd
from pocket_build import box
from props import tube

RUIN = ruin.ON
L = DL.L
POCKET_LOOK = {p[0]: p[1] for p in DL.POCKETS}
LEDGE_ROCK = {"post": "strata_orange", "canyon": "strata_red", "oasis": "gold_cliff", "gulch": "strata_rust",
              "crater": "strata_purple"}
BANDS = {
    "post": ["strata_cream", "strata_orange", "strata_red", "strata_orange", "strata_cream"],
    "canyon": ["strata_red", "strata_rust", "strata_orange", "strata_cream", "strata_red"],
    "crater": ["strata_purple", "strata_rust", "crater_rock", "strata_purple", "strata_cream"],
    "gulch": ["strata_rust", "strata_red", "strata_purple", "strata_rust", "strata_orange"],
}
SPOTS = []  # (x, y, r): what the dressing here took


def _toward_pocket(x, y, e=1.5):
    gx = (L.wall_sd(x + e, y) - L.wall_sd(x - e, y)) / (2 * e)
    gy = (L.wall_sd(x, y + e) - L.wall_sd(x, y - e)) / (2 * e)
    d = math.hypot(gx, gy) or 1.0
    return -gx / d, -gy / d


def _slope(x, y, e=1.2):
    gx = (DL.natural(x + e, y) - DL.natural(x - e, y)) / (2 * e)
    gy = (DL.natural(x, y + e) - DL.natural(x, y - e)) / (2 * e)
    return math.hypot(gx, gy)


# ------------------------------------------------------------------ the arches


def natural_arch(c, name, x, y, rot, span, height, mat_bands, ground, seed=0):
    """A great natural arch of banded sandstone over the road: two legs standing on the
    land either side, a span between them thinning to its crown, worn lumpy, its rock in
    beds of colour by height. `rot`: the way across it (leg to leg)."""
    ca, sa = math.cos(rot), math.sin(rot)
    ax, ay = x - ca * span / 2, y - sa * span / 2
    bx, by = x + ca * span / 2, y + sa * span / 2
    za, zb = ground(ax, ay), ground(bx, by)
    base = min(za, zb)
    top = max(za, zb) + height
    pts, radii = [], []
    n = 22
    for i in range(n + 1):
        t = i / n
        th = math.pi * t
        px = -math.cos(th) * span / 2
        z0 = za + (zb - za) * t
        # (A rounded arch, its legs straight down into the land.)
        pz = z0 - 4.0 + (top - z0 + 4.0) * math.sin(th) ** 0.75
        pts.append((x + ca * px, y + sa * px, pz))
        radii.append(2.6 + 3.8 * (1 - math.sin(th)) ** 1.6 + 0.5 * rnd(i + seed))
    bm = bmesh.new()
    tube(bm, pts, radii, n=12)
    rng = random.Random(seed)
    for v in bm.verts:
        v.co.x += rng.uniform(-0.35, 0.35)
        v.co.y += rng.uniform(-0.35, 0.35)
        v.co.z += rng.uniform(-0.3, 0.3)
    # (Flattened along the road a little: a fin of rock, not a pipe.)
    for v in bm.verts:
        dx, dy = v.co.x - x, v.co.y - y
        along = -dx * sa + dy * ca
        acr = dx * ca + dy * sa
        along *= 1.35
        v.co.x, v.co.y = x + acr * ca - along * sa, y + acr * sa + along * ca
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = c.mesh_object(name, bm, "Arches", "both")
    groups = {}
    for p in ob.data.polygons:
        k = int((p.center.z - base) / max(1.0, (top - base) / len(mat_bands)))
        groups.setdefault(mat_bands[max(0, min(len(mat_bands) - 1, k))], []).append(p.index)
    for m, faces in groups.items():
        c.assign(ob, c.lib(m, "wall"), faces)
    return (ax, ay), (bx, by)


def arches(c, ground, taken):
    """The road's arches: where it runs across an open floor, two in the canyon, one over
    the post's way north, one on the Wash, one out on the crater's floor."""
    want = {"canyon": 2, "post": 1, "wash": 1, "crater": 1}
    done = {k: 0 for k in want}
    last = -1e9
    made = 0
    S = c.S
    for i in range(0, len(S), 6):
        q = S[i]
        pk = L.pocket_at(q.p.x, q.p.y)
        key = pk if pk == "wash" else L.look_at(q.p.x, q.p.y)
        if key not in want or done[key] >= want[key] or q.s - last < 90.0:
            continue
        if math.hypot(q.p.x - DL.HUB[0], q.p.y - DL.HUB[1]) < DL.HUB[2] + 40.0 or L.tunnel_floor(q.p.x, q.p.y) is not None:
            continue
        if not q.ground or DL.ravine_d(q.p.x, q.p.y) < 45.0:
            continue
        span = 36.0 if key != "wash" else 32.0
        rot = math.atan2(q.r.y, q.r.x)
        legs = [(q.p.x - q.r.x * span / 2, q.p.y - q.r.y * span / 2), (q.p.x + q.r.x * span / 2, q.p.y + q.r.y * span / 2)]
        if not all(taken.clear(lx, ly, 5.0) and paint.road_clear(c, lx, ly, 6.0) for lx, ly in legs):
            continue
        # (Not over a gateway's spur, nor where the land either side is a wall face.)
        if any(L.wall_sd(lx, ly) > 6.0 for lx, ly in legs):
            continue
        a, b = natural_arch(c, "Arch %d" % made, q.p.x, q.p.y, rot, span, 17.0 + 4.0 * (made % 2),
                            BANDS.get(key if key != "wash" else "post", BANDS["canyon"]), ground, seed=made * 7 + 3)
        for lx, ly in (a, b):
            taken.add(lx, ly, 8.0)
            SPOTS.append((lx, ly, 8.0))
        done[key] += 1
        last = q.s
        made += 1
    print("desert arches: %d" % made)


# ------------------------------------------------------------------ the buttes


def butte(c, name, x, y, ground, height, r, bands, seed=0):
    """A butte: beds of coloured rock stacked up out of the floor, each a little narrower
    than the one under it, a flat cap on top."""
    z0 = ground(x, y) - 3.0
    n = len(bands)
    for k, m in enumerate(bands):
        f0, f1 = k / n, (k + 1) / n
        rr = r * (1.0 - 0.07 * k) * (1.08 if k == n - 1 else 1.0)
        ob = c.rock_mass("%s %d" % (name, k), x, y, rr, rr * 0.82, z0 + height * f1, z0=z0 + height * f0 - (3.0 if k == 0 else 0.6),
                         n=14, seed=seed + k, angle=seed * 0.7)
        c.assign(ob, c.lib(m, "wall"))


def buttes(c, ground, taken):
    """Buttes standing out of the open floors, well off the road: the canyon's, the post's
    outskirts', the gulch's backdrop and round the crater."""
    rng = random.Random(41)
    want = {"canyon": 4, "post": 2, "gulch": 2, "crater": 2}
    n = {k: 0 for k in want}
    for _ in range(9000):
        if all(n[k] >= want[k] for k in want):
            break
        x, y = rng.uniform(-260, 260), rng.uniform(-260, 260)
        if L.pocket_at(x, y) in ("slot", "rim", "wash", "pass"):
            continue
        look = L.look_at(x, y)
        if look not in want or n[look] >= want[look]:
            continue
        r = rng.uniform(7.0, 11.0)
        if L.wall_sd(x, y) > -(r + 2.0) or not paint.road_clear(c, x, y, r + 9.0) or not taken.clear(x, y, r + 4.0):
            continue
        if DL.ravine_d(x, y) < DL.RAVINE_HW + r + 4.0:
            continue
        if math.hypot(x - DL.HUB[0], y - DL.HUB[1]) < DL.HUB[2] + 30.0:
            continue
        h = rng.uniform(22.0, 38.0)
        butte(c, "Butte %s %d" % (look, n[look]), x, y, ground, h, r, BANDS[look], seed=n[look] * 5 + len(look))
        taken.add(x, y, r + 4.0)
        SPOTS.append((x, y, r + 4.0))
        n[look] += 1
    print("desert buttes:", n)


# ------------------------------------------------------------------ the walls


def wall_spots(c, seed=17, tries=30000):
    rng = random.Random(seed)
    shelves, lips, rims = [], [], []
    for _ in range(tries):
        x, y = rng.uniform(-300, 300), rng.uniform(-300, 300)
        wi = L.wall_info(x, y)
        look = POCKET_LOOK.get(wi["pocket"], "post")
        if wi["past"] > 1.0:
            lw = L.look_weights(x, y)
            look = max(lw, key=lw.get)
            if wi["past"] < 20.0 and _slope(x, y) < 0.6 and paint.road_clear(c, x, y, 14.0):
                rims.append((x, y, look))
            continue
        if not 0.05 < wi["t"] < 1.0 or _slope(x, y) > 0.6 or not paint.road_clear(c, x, y, 12.0):
            continue
        dx, dy = _toward_pocket(x, y)
        h = L.natural(x, y)
        drop = h - L.natural(x + dx * 3.5, y + dy * 3.5)
        rise = L.natural(x - dx * 4.0, y - dy * 4.0) - h
        if drop > 3.5:
            lips.append((x, y, look, (dx, dy), drop))
        else:
            shelves.append((x, y, look, (dx, dy), rise))
    return shelves, lips, rims


def cliff_dwelling(c, name, x, y, z, dx, dy, k):
    """Rooms of adobe built up against the riser behind a shelf, like swallows' nests: two
    or three boxes stepped up and back, dark doorways and windows, a ladder up the front,
    a round tower at one end."""
    face = math.atan2(dy, dx)
    rot = face + math.pi / 2
    ca, sa = math.cos(face), math.sin(face)
    side = (-sa, ca)
    rng = random.Random(k)
    rooms = 2 + k % 2
    for j in range(rooms):
        off = (j - (rooms - 1) / 2) * 4.6
        back = 0.9 * (j % 2)
        rx, ry = x + side[0] * off - ca * back, y + side[1] * off - sa * back
        hh = 3.0 + 1.6 * (j % 2) + rng.uniform(-0.3, 0.4)
        box(c, "%s Room %d" % (name, j), rx, ry, 2.1, 1.8, z - 1.0, z + hh, ("adobe", "wall"), rot=rot, role="visual")
        # Its doorway (a T, as the old builders cut them) and a window, dark in the face.
        fx, fy = rx + ca * 1.82, ry + sa * 1.82
        box(c, "%s Door %d" % (name, j), fx, fy, 0.45, 0.05, z, z + 1.5, ("dark_corridor", "wall"), rot=rot, role="visual")
        box(c, "%s Lintel %d" % (name, j), fx, fy, 0.75, 0.05, z + 1.5, z + 1.9, ("dark_corridor", "wall"), rot=rot,
            role="visual")
        if hh > 3.6:
            wx, wy = fx + side[0] * 1.2, fy + side[1] * 1.2
            box(c, "%s Window %d" % (name, j), wx, wy, 0.32, 0.05, z + 2.7, z + 3.3, ("dark_corridor", "wall"), rot=rot,
                role="visual")
        # (Poles sticking out under the roof: the beams.)
        for b in range(3):
            px, py = rx + side[0] * (b - 1) * 1.3 + ca * 2.2, ry + side[1] * (b - 1) * 1.3 + sa * 2.2
            box(c, "%s Beam %d %d" % (name, j, b), px, py, 0.09, 0.4, z + hh - 0.4, z + hh - 0.22, ("weathered_timber", "wall"),
                rot=rot, role="visual")
    # The tower: round, at one end.
    tx, ty = x + side[0] * (rooms * 2.3 + 1.6), y + side[1] * (rooms * 2.3 + 1.6)
    ob = c.rock_mass(name + " Tower", tx, ty, 1.6, 1.6, z + 5.2, z0=z - 1.0, n=10, seed=k, bands=[(1.0, 0.0), (1.0, 1.0)])
    c.assign(ob, c.lib("adobe", "wall"))
    # The ladder.
    lx, ly = x + ca * 2.6 - side[0] * 1.2, y + sa * 2.6 - side[1] * 1.2
    for sd in (-1, 1):
        box(c, "%s Ladder %d" % (name, sd), lx + side[0] * sd * 0.35, ly + side[1] * sd * 0.35, 0.06, 0.06, z - 0.2, z + 3.6,
            ("weathered_timber", "wall"), rot=rot - 0.3, role="visual")


def wall_life(c, ground, taken):
    """The walls alive (as the valley's and the snow's): saguaros, joshua trees, agaves
    and sage on the shelves, a rock ledge under each tree; in the canyon and round the
    post, cliff dwellings built against the risers; along the rims, saguaros against the
    sky."""
    shelves, lips, rims = wall_spots(c)
    sag = [cp.saguaro(c, v) for v in range(2)]
    josh = [cp.joshua_tree(c, v) for v in range(2)]
    agave = cp.agave(c, 0)
    sage = [cp.sagebrush(c, v) for v in range(2)]
    stone = [cp.boulder(c, v) for v in range(2)]
    ledges = {lk: rp.tree_ledge(c, mat) for lk, mat in LEDGE_ROCK.items()}
    room = paint.Taken(list(taken.spots))
    k = 0
    dwell = 0

    def put(proto, x, y, rot, scale, sink=0.3, coll="Ledges"):
        c.place(proto, x, y, ground(x, y) - sink, rot=rot, scale=scale, coll=coll, role="visual")

    def put_tree(proto, x, y, rot, scale, look):
        dx, dy = _toward_pocket(x, y)
        c.place(ledges.get(look, ledges["post"]), x - dx * 0.7, y - dy * 0.7, ground(x, y) - 0.2, rot=rot, coll="Ledges",
                role="visual")
        put(proto, x, y, rot, scale)

    for x, y, look, (dx, dy), rise in shelves:
        if look in ("canyon", "post") and dwell < 9 and rise > 5.0 and room.clear(x, y, 14.0) and (int(x * 7 + y * 3) % 5 == 0):
            cliff_dwelling(c, "Cliff Dwelling %d" % dwell, x, y, ground(x, y) - 0.2, dx, dy, dwell)
            room.add(x, y, 12.0)
            dwell += 1
            continue
        if not room.clear(x, y, 3.5):
            continue
        k += 1
        rot = (k * 2.39996) % math.tau
        if look == "oasis":
            pick = k % 3
            if pick == 0:
                put(sage[k % 2], x, y, rot, 1.2, sink=0.2)
            else:
                continue
        else:
            pick = k % 7
            if pick in (0, 3):
                put_tree(sag[k % 2], x, y, rot, 0.6 + 0.25 * ((k * 7) % 5) / 5, look)
            elif pick == 1:
                put_tree(josh[k % 2], x, y, rot, 0.6, look)
            elif pick == 2:
                put(agave, x, y, rot, 1.1, sink=0.2)
            elif pick in (4, 5):
                put(sage[k % 2], x, y, rot, 1.0 + 0.4 * ((k * 3) % 5) / 5, sink=0.2)
            else:
                put(stone[k % 2], x, y, rot, 0.7, sink=0.5)
        room.add(x, y, 3.5)
    n_rims = 0
    for x, y, look in rims:
        if not room.clear(x, y, 7.0):
            continue
        k += 1
        if k % 2:
            continue
        put(sag[k % 2] if k % 4 else josh[k % 2], x, y, (k * 1.7) % math.tau, 0.9 + 0.3 * (k % 3) / 2, coll="Rim")
        n_rims += 1
        room.add(x, y, 7.0)
    print("desert walls: shelves %d, dwellings %d, rims %d" % (len(shelves), dwell, n_rims))


# ------------------------------------------------------------------ the life


def life(c, ground, windmill=None):
    """The desert moving: vultures wheeling over the canyon, the crater and the ghost
    town; tumbleweeds bowling across the road on the post's outskirts, the Wash and the
    gulch's street; the windmill's wheel; dust on the wind."""
    def ent(kind, x, y, z, **kw):
        g = c.game(x, y, z)
        c.entity(kind, x=g[0], y=g[1], z=g[2], **kw)

    for k, (x, y, r, n, col) in enumerate(((-50.0, 160.0, 60.0, 4, "#2a1a1a"), (-6.0, -133.0, 50.0, 3, "#2a1a1a"),
                                            (140.0, -90.0, 55.0, 5, "#1e1424"), (140.0, 130.0, 50.0, 3, "#ffffff"))):
        ent("birds", x, y, DL.TOP + 30.0 + 8.0 * k, radius=r, count=n, speed=round(0.18 + 0.05 * k, 2), seed=k + 3,
            color=col)
    # Tumbleweeds: across the road where it's open sand.
    k = 0
    for i in range(0, len(c.S), 9):
        q = c.S[i]
        pk = L.pocket_at(q.p.x, q.p.y)
        key = pk if pk in ("wash",) else L.look_at(q.p.x, q.p.y)
        if key not in ("post", "wash", "gulch", "canyon") or L.tunnel_floor(q.p.x, q.p.y) is not None:
            continue
        if math.hypot(q.p.x - DL.HUB[0], q.p.y - DL.HUB[1]) < DL.HUB[2] + 12.0 or (i // 9) % 7 or not q.ground:
            continue
        sd = 1 if k % 2 else -1
        a = (q.p.x - q.r.x * sd * 16.0, q.p.y - q.r.y * sd * 16.0)
        b = (q.p.x + q.r.x * sd * 16.0, q.p.y + q.r.y * sd * 16.0)
        ga = c.game(a[0], a[1], ground(*a) + 0.8)
        gb = c.game(b[0], b[1], ground(*b) + 0.8)
        c.entity("tumbleweed", ax=ga[0], ay=ga[1], az=ga[2], bx=gb[0], by=gb[1], bz=gb[2], period=round(11.0 + 3.0 * (k % 4), 1),
                 offset=round(1.7 * k, 1), travel=6.0, r=0.8)
        k += 1
    if windmill and not RUIN:
        wx, wy, wz, wr = windmill
        ent("windmill", wx + math.cos(wr) * 1.4, wy + math.sin(wr) * 1.4, wz, heading=round(wr, 3), radius=3.2, speed=1.0)
    c.entity("dust", color="#d89a6a", rate=1.0)
    c.entity("dustwind", rate=7, radius=60, color="#e0a878")
    print("desert life: %d tumbleweeds" % k)


# ------------------------------------------------------------------ the Gorge Bridge


def trestle(c, ground):
    """The Gorge Bridge's timber trestle: a bent every few metres under the deck, two legs
    splayed down to the ravine's bed, a cap beam, cross braces, and a stringer each side."""
    m = bmesh.new()
    bents = 0
    last = -1e9
    under = [q for q in c.S if not q.ground and DL.ravine_d(q.p.x, q.p.y) < DL.RAVINE_HW + 12.0]
    for q in under:
        if q.s - last < 5.5:
            continue
        last = q.s
        top = q.p.z - 1.8
        half = q.w / 2 - 0.8
        legs = []
        for sd in (-1, 1):
            x, y = q.p.x + q.r.x * sd * half, q.p.y + q.r.y * sd * half
            foot = ground(x + q.r.x * sd * 1.6, y + q.r.y * sd * 1.6) - 0.6
            if top - foot < 1.0:
                continue
            fx, fy = x + q.r.x * sd * 1.6 * min(1.0, (top - foot) / 10.0), y + q.r.y * sd * 1.6 * min(1.0, (top - foot) / 10.0)
            tube(m, [(fx, fy, foot), (x, y, top)], [0.32, 0.26], n=6)
            legs.append(((fx, fy, foot), (x, y, top)))
        if len(legs) < 2:
            continue
        (a0, a1), (b0, b1) = legs
        tube(m, [(a1[0], a1[1], top - 0.2), (b1[0], b1[1], top - 0.2)], 0.28, n=6)
        # Cross braces, one X per few metres of height.
        h = top - max(a0[2], b0[2])
        rows = max(1, int(h / 5.0))
        for r in range(rows):
            z0 = max(a0[2], b0[2]) + h * r / rows + 0.4
            z1 = max(a0[2], b0[2]) + h * (r + 1) / rows - 0.2
            tube(m, [(a1[0], a1[1], z0), (b1[0], b1[1], z1)], 0.14, n=5)
            tube(m, [(b1[0], b1[1], z0), (a1[0], a1[1], z1)], 0.14, n=5)
        bents += 1
    if bents:
        ob = c.mesh_object("Gorge Bridge Trestle", m, "Bridges", "visual")
        c.assign(ob, c.lib("weathered_timber", "wall"))
    else:
        m.free()
    print("gorge bridge: %d bents" % bents)


# ------------------------------------------------------------------ the trading post


def adobe_house(c, name, x, y, z, rot, w, d, h, k, lit=True):
    """A pueblo house of the post: a thick-walled adobe block, a smaller storey set back
    on its roof, a parapet, the roof beams poking out, a dark doorway with a timber
    lintel, windows (warm, or dark), a striped awning over the door, and a ladder up to
    the roof. Its front, local -Y, faces rot's way."""
    ca, sa = math.cos(rot), math.sin(rot)

    def at(lx, ly):
        return x + lx * ca - ly * sa, y + lx * sa + ly * ca

    walls = ("adobe", "wall")
    box(c, name, x, y, w / 2, d / 2, z - 1.0, z + h, walls, rot=rot)
    # The parapet's lip and the upper storey, set back to one side.
    box(c, name + " Parapet", x, y, w / 2 + 0.15, d / 2 + 0.15, z + h, z + h + 0.45, walls, rot=rot, role="visual")
    if k % 3 != 2:
        ux, uy = at(w * 0.18 * (1 if k % 2 else -1), d * 0.15)
        uw, ud = w * 0.32, d * 0.3
        box(c, name + " Upper", ux, uy, uw, ud, z + h, z + h + 2.8, walls, rot=rot, role="visual")
        box(c, name + " Upper Lip", ux, uy, uw + 0.12, ud + 0.12, z + h + 2.8, z + h + 3.15, walls, rot=rot, role="visual")
    # Roof beams (vigas) out through the front wall.
    nb = max(3, int(w / 1.4))
    for j in range(nb):
        bx, by = at(-w / 2 + 0.6 + j * (w - 1.2) / (nb - 1), -d / 2 - 0.35)
        box(c, name + " Viga %d" % j, bx, by, 0.14, 0.45, z + h - 0.6, z + h - 0.32, ("weathered_timber", "wall"), rot=rot,
            role="visual")
    # The doorway, its lintel, and the windows either side.
    dx, dy = at(0.0, -d / 2 - 0.05)
    box(c, name + " Door", dx, dy, 0.65, 0.07, z, z + 2.2, ("dark_corridor", "wall"), rot=rot, role="visual")
    lx, ly = at(0.0, -d / 2 - 0.12)
    box(c, name + " Lintel", lx, ly, 1.0, 0.14, z + 2.2, z + 2.5, ("weathered_timber", "wall"), rot=rot, role="visual")
    for sd in (-1, 1):
        if w < 5.0:
            break
        wx, wy = at(sd * w * 0.3, -d / 2 - 0.05)
        box(c, name + " Window %d" % sd, wx, wy, 0.45, 0.06, z + 1.1, z + 2.0, ("window_lit" if lit else "window_dark", "wall"),
            rot=rot, role="visual")
    # The awning on two poles.
    ax, ay = at(0.0, -d / 2 - 1.3)
    box(c, name + " Awning", ax, ay, 1.6, 1.3, z + 2.65, z + 2.8, (("tent_cloth", "tent_cloth_red")[k % 2], "wall"), rot=rot,
        role="visual")
    for sd in (-1, 1):
        px, py = at(sd * 1.5, -d / 2 - 2.5)
        box(c, name + " Pole %d" % sd, px, py, 0.07, 0.07, z - 0.2, z + 2.7, ("weathered_timber", "wall"), rot=rot,
            role="visual")
    # The ladder up the side.
    sx, sy = at(w / 2 + 0.25, -d * 0.15)
    for sd in (-1, 1):
        qx, qy = at(w / 2 + 0.25, -d * 0.15 + sd * 0.3)
        box(c, name + " Ladder %d" % sd, qx, qy, 0.05, 0.05, z - 0.2, z + h + 1.2, ("weathered_timber", "wall"), rot=rot,
            role="visual")
    return at(0.0, -d / 2 - 3.0)  # (before its door)


def trading_post(c, ground, ter):
    """Stego's trading post made a real place (as Hearthglow was): a dusty square, and
    round it pueblo houses facing in, with awnings over their doors and lanes worn to
    them; market stalls under striped cloth; bunting strung across the square; the water
    tank and the windmill, a corral with a covered wagon, troughs and hitching rails,
    barrels and crates. The cutscenes' stage, east-west across the square, is kept
    clear. (After the attack: roofless, the bunting down, the stalls flattened.)"""
    import beach_props as bp
    import gulch_props as gp
    import oasis_props as op
    import valley_village as vv

    cx, cy, cr, cz = DL.HUB
    R = 15.0
    vv.plaza(c, cx, cy, R, ground, dirt=("dash_road", "road"), edge=("dash_shoulder", "dirt"), verge=1.8, name="Post Square")
    c.disc("Post Square Floor", cx, cy, R + 0.6, cz + 0.02, c.lib("dash_road", "road"), coll="Props", role="collision", n=40)
    taken = paint.Taken([(-183.5, -17.4, 14.0), (-172.5, -17.5, 9.0)])
    SPOTS.extend([(-183.5, -17.4, 14.0)])

    def in_stage(x, y, w):
        return abs(y - cy) < w

    built = []
    paths = []
    k = 0
    for r in (24.0, 31.0, 38.0):
        n = int(math.tau * r / 11.0)
        for i in range(n):
            a = i * math.tau / n + 0.2 * r
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            if L.wall_sd(x, y) > -6.0 or L.pocket_at(x, y) not in ("post",):
                continue
            if in_stage(x, y, 12.0) or not paint.road_clear(c, x, y, 8.0) or not taken.clear(x, y, 5.0):
                continue
            if any(math.hypot(x - hx, y - hy) < 11.0 for hx, hy in built):
                continue
            ring = [ground(x + 4.5 * math.cos(t), y + 4.5 * math.sin(t)) for t in (0.0, 1.57, 3.14, 4.71)]
            if max(ring) - min(ring) > 2.0:
                continue
            rot = a - math.pi / 2
            w, d, h = (8.0, 6.0, 4.2), (6.0, 5.5, 3.6), (10.0, 6.5, 4.6)
            w, d, h = (w, d, h)[k % 3]
            z = min(ring) + 0.05
            if RUIN:
                box(c, "Post House %d" % k, x, y, w / 2, d / 2, z - 1.0, z + 1.4 + 0.8 * (k % 2), ("adobe", "wall"), rot=rot)
                ruin.rubble(c, "Post Rubble %d" % k, x + 3.0 * math.cos(a), y + 3.0 * math.sin(a), ground, ("adobe", "wall"),
                            n=5, spread=3.0, size=0.9, seed=k)
                door = (x - math.cos(a) * (d / 2 + 3.0), y - math.sin(a) * (d / 2 + 3.0))
            else:
                door = adobe_house(c, "Post House %d" % k, x, y, z, rot, w, d, h, k, lit=k % 3 != 1)
            built.append((x, y))
            taken.add(x, y, 7.0)
            SPOTS.append((x, y, 8.0))
            # Its lane to the square.
            da = math.hypot(door[0] - cx, door[1] - cy)
            if da - R > 2.0:
                end = (cx + (door[0] - cx) / da * (R - 0.5), cy + (door[1] - cy) / da * (R - 0.5))
                paths.append(vv.wander(door, end, bend=1.0 * math.sin(a * 2.0), seed=k))
            k += 1
    vv.path_ribbons(c, paths, ground, look=lambda x, y: (("dash_road", "road"), ("dash_shoulder", "dirt")), width=2.4,
                    verge=1.0, name="Post Lanes")
    # Market stalls round the square's edge (not across the stage).
    if not RUIN:
        for j in range(8):
            a = j * math.tau / 8 + math.pi / 8
            x, y = cx + (R - 2.5) * math.cos(a), cy + (R - 2.5) * math.sin(a)
            if in_stage(x, y, 9.0) or not taken.clear(x, y, 2.0):
                continue
            c.place(op.market_stall(c, j % 2), x, y, ground(x, y) - 0.05, rot=a + math.pi / 2, coll="Village")
            taken.add(x, y, 3.0)
    # The water tank, the corral and its wagon, troughs, rails, barrels, crates.
    tx, ty = cx - 12.0, cy + 19.0
    if taken.clear(tx, ty, 3.0):
        if RUIN:
            ruin.rubble(c, "Water Tank Rubble", tx, ty, ground, ("weathered_timber", "wall"), n=7, spread=4.0, size=1.0, seed=3)
        else:
            c.place(cp.water_tank(c), tx, ty, ground(tx, ty) - 0.2, rot=0.3, coll="Village")
        taken.add(tx, ty, 4.0)
    spot = next(((x, y) for x, y in ((cx - 26.0, cy + 20.0), (cx - 20.0, cy + 30.0), (cx + 2.0, cy + 30.0), (cx - 4.0, cy - 30.0))
                 if L.wall_sd(x, y) < -9.0 and taken.clear(x, y, 8.0) and not in_stage(x, y, 16.0)
                 and paint.road_clear(c, x, y, 9.0)), None)
    if spot:
        ox, oy = spot
        for j in range(10):
            a = j * math.tau / 10
            px, py = ox + 7.0 * math.cos(a), oy + 7.0 * math.sin(a)
            if j == 0:
                continue  # (the gate)
            c.place(cp.fence_post(c), px, py, ground(px, py) - 0.1, rot=a + math.pi / 2, coll="Village")
        c.place(gp.wagon(c, covered=True, broken=RUIN), ox, oy, ground(ox, oy) - 0.05, rot=0.8, coll="Village")
        c.place(gp.trough(c), ox + 3.0, oy + 4.0, ground(ox + 3.0, oy + 4.0) - 0.05, rot=0.2, coll="Village")
        taken.add(ox, oy, 8.0)
        SPOTS.append((ox, oy, 8.0))
    for j, (x, y, rot) in enumerate(((cx + 4.0, cy + R + 2.5, 0.0), (cx + 4.0, cy - R - 2.5, 0.0), (cx - 8.0, cy - R - 1.5, 0.4))):
        if taken.clear(x, y, 1.5) and paint.road_clear(c, x, y, 2.0):
            c.place(gp.hitching_rail(c), x, y, ground(x, y) - 0.05, rot=rot, coll="Village")
            c.place(gp.trough(c), x + 2.6, y, ground(x + 2.6, y) - 0.05, rot=rot, coll="Village")
            taken.add(x, y, 3.0)
    rng = random.Random(9)
    for x, y in built:
        for j in range(2):
            a = rng.uniform(0, math.tau)
            px, py = x + 5.5 * math.cos(a), y + 5.5 * math.sin(a)
            if taken.clear(px, py, 1.0) and not in_stage(px, py, 10.0) and paint.road_clear(c, px, py, 3.0):
                proto = gp.barrel(c, j) if j == 0 else op.crates(c, j)
                c.place(proto, px, py, ground(px, py) - 0.05, rot=a, coll="Village")
    # Bunting across the square, house to house.
    if not RUIN:
        tops = []
        for x, y in built:
            if math.hypot(x - cx, y - cy) < 30.0:
                tops.append((x, y, ground(x, y) + 4.4))
        tops.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
        for j, (a, b) in enumerate(zip(tops, tops[1:] + tops[:1])):
            if math.hypot(a[0] - b[0], a[1] - b[1]) > 34.0:
                continue
            bp.string_line(c, "Post Bunting %d" % j, a, b, 1.4, "bunting", coll="Village")
        for j, (x, y, z) in enumerate(tops[: len(tops) // 2]):
            # (And across the square, over the stage, high.)
            ox, oy = 2 * cx - x, 2 * cy - y
            near = min(tops, key=lambda p: math.hypot(p[0] - ox, p[1] - oy))
            if j % 2 == 0 and math.hypot(near[0] - ox, near[1] - oy) < 12.0:
                bp.string_line(c, "Post Bunting Across %d" % j, (x, y, z + 1.5), (near[0], near[1], near[2] + 1.5), 2.2, "bunting",
                               coll="Village")
    if not RUIN:
        g = c.game(cx - 5.0, cy + 8.0, ground(cx - 5.0, cy + 8.0) + 0.3)
        c.entity("campfire", x=g[0], y=g[1], z=g[2])
    print("trading post: %d houses, %d lanes" % (len(built), len(paths)))
    return paths
