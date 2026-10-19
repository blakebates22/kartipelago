# Checkpoint gates: placing, editing and exporting the invisible gates a lap is made of.
# SPDX-License-Identifier: MIT
"""
A checkpoint is a mesh object in the "KP Checkpoints" collection: a translucent upright
rectangle with an arrow showing which way you cross it.

- Its origin is the bottom centre of the gate (on the road).
- Its local +Y is the crossing direction.
- Its X scale is the gate's width, its Z scale is its height.
- Custom properties:
    kp_checkpoint  the checkpoint number (0 = the start/finish line)
    kp_cp_route    "main", or the name of an alternate route (a shortcut): a gate with
                   the same number on another route counts the same as the main one
    kp_cp_below    how far the gate reaches below its origin, metres

Move, rotate, scale, duplicate (Shift+D) and delete (X) checkpoints like any object, then
press Renumber to put the numbers in order round the route again. Export writes them to
checkpoints.json (game coordinates). They never go into visual.glb or collision.glb, so
re-exporting geometry never touches them, and they live in the .blend.

Colours: gold = the start line, green = main route, orange = alternate routes.
"""

import json
import math
import os

import bpy
import bmesh
from mathutils import Vector

COLLECTION = "KP Checkpoints"
ORDER_NAME = "KP Checkpoint Order"
CHECKPOINT_SCHEMA = 1
COLORS = {"start": (1.0, 0.8, 0.15, 0.4), "main": (0.25, 0.95, 0.4, 0.3), "alt": (1.0, 0.55, 0.15, 0.35)}

# Defaults (match src/race/checkpoints.ts DEFAULT_GATES, with the imported-track height).
MARGIN = 18.0
HEIGHT = 6.0
BELOW = 3.0
MIN_GAP = 45.0
MAX_GAP = 130.0


def is_checkpoint(ob):
    return ob is not None and ob.get("kp_role") == "checkpoint"


def checkpoints(scene=None):
    scene = scene or bpy.context.scene
    return [o for o in scene.objects if is_checkpoint(o)]


def _collection(scene):
    c = bpy.data.collections.get(COLLECTION)
    if c is None:
        c = bpy.data.collections.new(COLLECTION)
    if c.name not in scene.collection.children:
        scene.collection.children.link(c)
    return c


def _material(kind):
    name = "KP Checkpoint " + kind.title()
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        m.diffuse_color = COLORS[kind]
        m.use_backface_culling = False
        try:
            m.surface_render_method = "BLENDED"
        except (AttributeError, TypeError):
            pass
    return m


def _gate_mesh():
    """A unit gate: 1 m wide (X), 1 m tall (Z), plus a 3 m arrow along +Y at mid-height."""
    me = bpy.data.meshes.get("KP Checkpoint Gate")
    if me is not None:
        return me
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in ((-0.5, 0, 0), (0.5, 0, 0), (0.5, 0, 1), (-0.5, 0, 1))]
    bm.faces.new(v)
    a = [bm.verts.new(p) for p in ((-0.04, 0, 0.45), (0.04, 0, 0.45), (0, 3.0, 0.45))]
    bm.faces.new(a)
    b = [bm.verts.new(p) for p in ((0, 0, 0.4), (0, 0, 0.5), (0, 3.0, 0.45))]
    bm.faces.new(b)
    me = bpy.data.meshes.new("KP Checkpoint Gate")
    bm.to_mesh(me)
    bm.free()
    return me


def style(ob):
    """Colour a checkpoint by what it is (start, main, alternate), and show its name."""
    route = ob.get("kp_cp_route", "main")
    kind = "alt" if route != "main" else ("start" if ob.get("kp_checkpoint", 0) == 0 else "main")
    ob.data = _gate_mesh()
    if len(ob.data.materials) == 0:
        ob.data.materials.append(None)
    # Linked to the object, so each gate shows its own colour on the shared mesh.
    ob.material_slots[0].link = "OBJECT"
    ob.material_slots[0].material = _material(kind)
    ob.color = COLORS[kind]
    ob.show_name = True
    ob.show_transparent = True
    ob.hide_render = True


def add_respawn(gate, location, heading_dir):
    """A child empty marking where a respawn at this checkpoint puts you (move it freely)."""
    e = bpy.data.objects.new(gate.name + " Respawn", None)
    e.empty_display_type = "SINGLE_ARROW"
    e.empty_display_size = 3.0
    for c in gate.users_collection:
        c.objects.link(e)
    e.location = location
    # The arrow (empty's +Z) lies along the way to face; its +Y is that direction.
    e.rotation_euler = (math.radians(-90), 0.0, math.atan2(-heading_dir[0], heading_dir[1]))
    e["kp_respawn"] = True
    e["kp_role"] = "editor"
    bpy.context.view_layer.update()
    mw = e.matrix_world.copy()
    e.parent = gate
    e.matrix_world = mw
    return e


def make(scene, index, location, heading_dir, width, height=HEIGHT, route="main", below=BELOW, name=None):
    """A new checkpoint object. heading_dir: the crossing direction (Blender x, y)."""
    ob = bpy.data.objects.new(name or "CP %02d" % index, _gate_mesh())
    _collection(scene).objects.link(ob)
    ob["kp_role"] = "checkpoint"
    ob["kp_checkpoint"] = int(index)
    ob["kp_cp_route"] = route
    ob["kp_cp_below"] = float(below)
    ob.location = location
    ob.rotation_euler = (0.0, 0.0, math.atan2(-heading_dir[0], heading_dir[1]))
    ob.scale = (width, 1.0, height)
    style(ob)
    return ob


# ------------------------------------------------------------------ the route


def main_route(scene=None):
    scene = scene or bpy.context.scene
    routes = [o for o in scene.objects if o.get("kp_route") and o.type == "CURVE"]
    if not routes:
        return None
    return next((o for o in routes if o.get("kp_route") == "main"), routes[0])


def route_samples(scene=None, spacing=1.0):
    """The main route as [(position, forward, width, distance)] in Blender coordinates."""
    from . import export

    r = main_route(scene)
    if r is None:
        return [], 0.0
    pts = export.sample_route(r, spacing)["points"]
    out = []
    d = 0.0
    prev = None
    for p in pts:
        v = Vector((p["x"], -p["z"], p["y"]))
        if prev is not None:
            d += (v - prev).length
        out.append([v, None, p["width"], d])
        prev = v
    length = d + (out[0][0] - out[-1][0]).length
    n = len(out)
    for i in range(n):
        t = out[(i + 1) % n][0] - out[(i - 1) % n][0]
        t.z = 0
        out[i][1] = t.normalized()
    return out, length


def distance_along(samples, p):
    best = min(samples, key=lambda s: (s[0] - p).length_squared)
    return best[3]


def _curvature(s):
    n = len(s)
    head = [math.atan2(q[1].x, q[1].y) for q in s]
    raw = []
    for i in range(n):
        d = head[(i + 1) % n] - head[(i - 1) % n]
        d = (d + math.pi) % math.tau - math.pi
        a, b = s[(i - 1) % n][0], s[(i + 1) % n][0]
        raw.append(d / (max(1e-6, (b - a).xy.length)))
    step = max(0.5, s[1][3] - s[0][3]) if n > 1 else 1.0
    w = max(1, round(12 / step))
    return [sum(raw[(i + k) % n] for k in range(-w, w + 1)) / (2 * w + 1) for i in range(n)]


def place(samples, length, avoid=(), extra=(), min_gap=MIN_GAP, max_gap=MAX_GAP):
    """
    Distances along the lap for checkpoints: the start line, just after every real turn,
    any `extra` distances you ask for, and enough in between that no stretch is longer
    than max_gap. Nothing goes inside an `avoid` stretch (a jump's gap).
    """
    k = _curvature(samples)
    blocked = lambda d: any(a - 8 <= d <= b + 8 for a, b in avoid)  # noqa: E731
    exits = []
    in_turn = False
    turned = 0.0
    for i, s in enumerate(samples):
        ak = abs(k[i])
        if ak > 1 / 70:
            in_turn = True
            turned += ak * (s[3] - samples[i - 1][3] if i else 0)
        elif in_turn and ak < 1 / 160:
            if turned > 0.6:
                exits.append(s[3] + 8)
            in_turn = False
            turned = 0.0
    picks = [0.0]
    forced = sorted(d for d in extra if 0 < d < length)
    for d in sorted(set(exits) | set(forced)):
        if d >= length - min_gap * (0.5 if d in forced else 1) or (blocked(d) and d not in forced):
            continue
        if d in forced:
            picks = [p for p in picks if p == 0 or abs(p - d) >= min_gap * 0.5 or p in forced]
            picks.append(d)
        elif all(abs(d - p) >= min_gap for p in picks):
            picks.append(d)
    picks.sort()
    out = []
    allp = picks + [length]
    for a, b in zip(allp, allp[1:]):
        out.append(a)
        extra_n = int((b - a) // max_gap)
        for e in range(1, extra_n + 1):
            d = a + (b - a) * e / (extra_n + 1)
            for x, y in avoid:
                if x - 8 <= d <= y + 8:
                    d = y + 20 if y + 20 < b - 10 else x - 20
            out.append(d)
    return out


def _at(samples, length, d):
    d %= length
    best = samples[0]
    for s in samples:
        if s[3] <= d:
            best = s
        else:
            break
    return best


def gate_extents(samples, length, d, margin=MARGIN, height=HEIGHT, below=BELOW):
    """Left and right reach of a gate at d: road plus margin, but never more than halfway
    to another part of the course at about the same height."""
    p, f, w, dist = _at(samples, length, d)
    half = w / 2
    left = right = half + margin
    right_dir = Vector((f.y, -f.x, 0))
    for q, _, qw, qd in samples:
        along = abs(qd - dist)
        if min(along, length - along) < 60 or abs(q.z - p.z) > height + below:
            continue
        rel = q - p
        if abs(rel.x * f.x + rel.y * f.y) > qw / 2 + 6:
            continue
        across = rel.x * right_dir.x + rel.y * right_dir.y
        room = max(half + 2, (abs(across) - qw / 2) * 0.5 + half * 0.5)
        if across < 0:
            left = min(left, room)
        else:
            right = min(right, room)
    return p, f, left, right


def generate(scene=None, avoid=(), extra=(), margin=MARGIN, height=HEIGHT, replace=True):
    """Place a set of main-route checkpoints along the route (replacing the old ones)."""
    scene = scene or bpy.context.scene
    samples, length = route_samples(scene)
    if not samples:
        raise RuntimeError("No route: mark the main road curve as the route first.")
    if replace:
        for o in checkpoints(scene):
            if o.get("kp_cp_route", "main") == "main":
                for ch in list(o.children):
                    bpy.data.objects.remove(ch)
                bpy.data.objects.remove(o)
    made = []
    for i, d in enumerate(place(samples, length, avoid, extra)):
        p, f, left, right = gate_extents(samples, length, d, margin, height)
        # Asymmetric gates: the origin sits at the middle of the gate, not the road.
        mid = (right - left) / 2
        loc = p + Vector((f.y, -f.x, 0)) * mid
        g = make(scene, i, loc, (f.x, f.y), left + right, height)
        q = _at(samples, length, d + 4)
        add_respawn(g, q[0], (q[1].x, q[1].y))
        made.append(g)
    # Alternate-route gates stay paired with the nearest new main gate.
    dists = [(distance_along(samples, g.location), g["kp_checkpoint"]) for g in made]
    for o in checkpoints(scene):
        if o.get("kp_cp_route", "main") != "main":
            d = distance_along(samples, o.location)
            o["kp_checkpoint"] = min(dists, key=lambda x: min(abs(x[0] - d), length - abs(x[0] - d)))[1]
            style(o)
    order_line(scene)
    return made


def renumber(scene=None):
    """Number the main-route checkpoints in order round the route, starting from the one
    nearest the start line. Alternate-route gates follow the main gate whose number they
    had (so they stay paired with it)."""
    scene = scene or bpy.context.scene
    samples, length = route_samples(scene)
    main = [o for o in checkpoints(scene) if o.get("kp_cp_route", "main") == "main"]
    if not samples or not main:
        return 0
    main.sort(key=lambda o: distance_along(samples, o.location) % length)
    old = {o.get("kp_checkpoint"): i for i, o in enumerate(main)}
    for i, o in enumerate(main):
        o["kp_checkpoint"] = i
        o.name = "CP %02d" % i
        style(o)
    for o in checkpoints(scene):
        if o.get("kp_cp_route", "main") != "main":
            o["kp_checkpoint"] = old.get(o.get("kp_checkpoint"), o.get("kp_checkpoint"))
            style(o)
    order_line(scene)
    return len(main)


def order_line(scene=None):
    """A line through the checkpoints in order (editor only; never exported)."""
    scene = scene or bpy.context.scene
    main = sorted((o for o in checkpoints(scene) if o.get("kp_cp_route", "main") == "main"), key=lambda o: o["kp_checkpoint"])
    ob = bpy.data.objects.get(ORDER_NAME)
    if len(main) < 2:
        if ob:
            bpy.data.objects.remove(ob)
        return None
    if ob is None:
        cd = bpy.data.curves.new(ORDER_NAME, "CURVE")
        cd.dimensions = "3D"
        ob = bpy.data.objects.new(ORDER_NAME, cd)
        _collection(scene).objects.link(ob)
    cd = ob.data
    cd.splines.clear()
    sp = cd.splines.new("POLY")
    sp.points.add(len(main) - 1)
    for p, o in zip(sp.points, main):
        c = o.location + Vector((0, 0, o.scale.z * 0.5))
        p.co = (c.x, c.y, c.z, 1.0)
    sp.use_cyclic_u = True
    cd.bevel_depth = 0.15
    ob["kp_role"] = "editor"
    ob.hide_render = True
    return ob


def step_selection(context, direction):
    """Select the next (or previous) main checkpoint after the active one."""
    main = sorted((o for o in checkpoints(context.scene) if o.get("kp_cp_route", "main") == "main"), key=lambda o: o["kp_checkpoint"])
    if not main:
        return None
    a = context.view_layer.objects.active
    i = main.index(a) if a in main else -1
    nxt = main[(i + direction) % len(main)]
    for o in context.selected_objects:
        o.select_set(False)
    nxt.select_set(True)
    context.view_layer.objects.active = nxt
    return nxt


# ------------------------------------------------------------------ export


def to_game(v):
    return [round(v.x, 3), round(v.z, 3), round(-v.y, 3)]


def describe(ob):
    """One checkpoint as checkpoints.json wants it (game coordinates)."""
    mw = ob.matrix_world
    fwd = (mw.to_3x3() @ Vector((0, 1, 0)))
    fwd.z = 0
    fwd.normalize()
    heading = math.atan2(fwd.x, -fwd.y)  # game forward is (x, -y)
    sx, _, sz = mw.to_scale()
    e = {
        "id": ("cp%02d" % ob["kp_checkpoint"]) + ("" if ob.get("kp_cp_route", "main") == "main" else "_" + ob["kp_cp_route"]),
        "index": int(ob["kp_checkpoint"]),
        "route": ob.get("kp_cp_route", "main"),
        "position": to_game(mw.translation),
        "heading": round(heading, 5),
        "width": round(abs(sx), 3),
        "height": round(abs(sz), 3),
        "below": round(float(ob.get("kp_cp_below", BELOW)), 3),
    }
    for child in ob.children:
        if child.get("kp_respawn"):
            f = child.matrix_world.to_3x3() @ Vector((0, 0, 1))  # the arrow
            e["respawn"] = {"position": to_game(child.matrix_world.translation), "heading": round(math.atan2(f.x, -f.y), 5)}
    return e


def export(scene, out_dir):
    """Write checkpoints.json (or remove a stale one if the scene has none). Returns the count."""
    path = os.path.join(out_dir, "checkpoints.json")
    cps = checkpoints(scene)
    if not cps:
        if os.path.exists(path):
            os.remove(path)
        return 0
    data = {
        "schemaVersion": CHECKPOINT_SCHEMA,
        "about": "Checkpoint gates, exported from Blender (the KP Checkpoints collection). Game coordinates; heading 0 faces +z.",
        "checkpoints": sorted((describe(o) for o in cps), key=lambda e: (e["index"], e["route"] != "main", e["route"])),
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=1)
        f.write("\n")
    return len(cps)
