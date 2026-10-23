# Kartipelago Track Tools: export.
# SPDX-License-Identifier: MIT
"""
One-click export of a track package into the game's public/tracks/<id>/ folder:

    visual.glb     what you see: every visible object whose role is "both" or "visual"
    collision.glb  what you drive on and hit: role "both" or "collision"
    route.json     the race route, sampled from the curve(s) marked as the route
    look.json      sky, sun and fog (the Sky & Fog panel's environment preset)
    track.json     gameplay metadata. Written only if it doesn't exist yet: re-exporting
                   geometry never touches placements made in the game's editor.

Coordinates: Blender is Z-up, the game (like glTF) is Y-up. 1 Blender unit = 1 metre.
A Blender point (x, y, z) is game (x, z, -y). Banking: a positive curve Tilt tilts the
road down to the right, which is the game's positive `bank`.
"""

import json
import math
import os

import bpy
from . import checkpoints, materials, road

ROUTE_SCHEMA = 1
TRACK_SCHEMA = 1
DRIVEABLE_TYPES = {"MESH", "CURVE", "SURFACE", "META", "FONT"}


def role_of(ob):
    """'both' (seen and collided with), 'visual' (decoration), 'collision' (hidden), or
    'checkpoint' / 'editor' (editor-only helpers: never in the GLBs)."""
    r = ob.get("kp_role")
    if r in ("both", "visual", "collision", "checkpoint", "editor"):
        return r
    return "visual"


def to_game(v):
    """Blender (x, y, z) to game (x, y, z)."""
    return (v.x, v.z, -v.y)


def _bezier(p0, h0, h1, p1, t):
    u = 1 - t
    return p0 * (u * u * u) + h0 * (3 * u * u * t) + h1 * (3 * u * t * t) + p1 * (t * t * t)


def sample_route(ob, spacing=2.0):
    """Sample a Bezier curve object's first spline into game-space route points."""
    sp = ob.data.splines[0]
    mw = ob.matrix_world
    pts = sp.bezier_points
    n = len(pts)
    seg_count = n if sp.use_cyclic_u else n - 1
    # A road curve's width comes from its road; a bare route curve (no road of its own,
    # e.g. a track built from separate road pieces) can say it with "kp_width".
    settings = road.road_settings(ob) or {"width": float(ob.get("kp_width", 12.0)), "shoulder": 0.0}
    out = []
    for i in range(seg_count):
        a = pts[i]
        b = pts[(i + 1) % n]
        p0 = mw @ a.co
        h0 = mw @ a.handle_right
        h1 = mw @ b.handle_left
        p1 = mw @ b.co
        chord = (p1 - p0).length + (h0 - p0).length + (h1 - p1).length
        steps = max(4, math.ceil(chord / spacing))
        for k in range(steps):
            t = k / steps
            p = _bezier(p0, h0, h1, p1, t)
            tilt = a.tilt + (b.tilt - a.tilt) * t
            radius = a.radius + (b.radius - a.radius) * t
            x, y, z = to_game(p)
            out.append(
                {
                    "x": round(x, 4),
                    "y": round(y, 4),
                    "z": round(z, 4),
                    "width": round(settings["width"] * radius, 3),
                    "bank": round(math.degrees(tilt), 3),
                }
            )
    if not sp.use_cyclic_u:
        x, y, z = to_game(mw @ pts[-1].co)
        out.append({"x": x, "y": y, "z": z, "width": settings["width"], "bank": math.degrees(pts[-1].tilt)})
    return {"closed": bool(sp.use_cyclic_u), "points": out}


def _realize_uv_curves(objects):
    """Roads are curves whose geometry nodes store their UVs as a "UVMap" attribute. Some
    Blender builds (the bpy module, for one) don't export such a UV map from an evaluated
    curve, so roads came out untextured. Export a real mesh copy of each instead, with
    that UV map active, under the same name and properties. Returns (objects to export,
    a function that removes the copies and restores the names)."""
    dg = bpy.context.evaluated_depsgraph_get()
    out, made = [], []
    for o in objects:
        if o.type != "CURVE" or not any(m.type == "NODES" for m in o.modifiers):
            out.append(o)
            continue
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
        uv = me.uv_layers.get("UVMap")
        if uv is None:
            bpy.data.meshes.remove(me)
            out.append(o)
            continue
        me.uv_layers.active = uv
        uv.active_render = True
        name = o.name
        o.name = name + " (curve)"
        copy = bpy.data.objects.new(name, me)
        copy.matrix_world = o.matrix_world
        for k in o.keys():
            copy[k] = o[k]
        for coll in o.users_collection:
            coll.objects.link(copy)
        made.append((o, copy, name))
        out.append(copy)

    def restore():
        for o, copy, name in made:
            me = copy.data
            bpy.data.objects.remove(copy)
            bpy.data.meshes.remove(me)
            o.name = name

    return out, restore


def _export_glb(path, objects, images=True):
    """Export exactly these objects (modifiers applied) to a GLB file."""
    objects, restore = _realize_uv_curves(objects)
    try:
        _export_glb_objects(path, objects, images)
    finally:
        restore()


def _export_glb_objects(path, objects, images=True):
    view = bpy.context.view_layer
    hidden = [o for o in objects if o.hide_get() or o.hide_viewport]
    for o in hidden:
        o.hide_viewport = False
        o.hide_set(False)
    prev_sel = [o for o in view.objects if o.select_get()]
    prev_active = view.objects.active
    for o in view.objects:
        o.select_set(False)
    for o in objects:
        o.select_set(True)
    # Vertex paint: the "Col" attribute that library materials multiply in (the
    # collision mesh needs none).
    opts = {"export_vertex_color": "MATERIAL" if images else "NONE"}
    if not images:
        opts["export_texcoords"] = False
    try:
        _gltf(
            filepath=path,
            export_format="GLB",
            use_selection=True,
            export_apply=True,
            export_extras=True,
            export_yup=True,
            export_materials="EXPORT",
            # Collision needs the materials (their kp_surface extras) but not textures.
            export_image_format="AUTO" if images else "NONE",
            export_cameras=False,
            export_lights=False,
            export_animations=False,
            **opts,
        )
    finally:
        for o in view.objects:
            o.select_set(False)
        for o in prev_sel:
            o.select_set(True)
        view.objects.active = prev_active
        for o in hidden:
            o.hide_set(True)


def _gltf(**kw):
    """The glTF exporter, dropping options this Blender's exporter doesn't have."""
    try:
        bpy.ops.export_scene.gltf(**kw)
    except TypeError:
        kw.pop("export_vertex_color", None)
        bpy.ops.export_scene.gltf(**kw)


def check_surfaces(objects):
    """Warnings for collision objects whose materials don't name a surface."""
    known = {s[0] for s in road.SURFACES}
    warnings = []
    for o in objects:
        mats = [s.material for s in getattr(o, "material_slots", []) if s.material]
        mod = o.modifiers.get("KP Road")
        if mod is not None:
            continue  # the road modifier assigns tagged materials itself
        if not mats:
            warnings.append(f"{o.name}: no material, collides as 'asphalt'")
        for m in mats:
            s = m.get("kp_surface")
            if s is None:
                warnings.append(f"{o.name}: material '{m.name}' has no kp_surface")
            elif s not in known:
                warnings.append(f"{o.name}: material '{m.name}' has unknown surface '{s}'")
    return warnings


def export_track(folder, track_id, name=None):
    """Write the package for `track_id` into `folder`/<track_id>/. Returns a report dict."""
    base = os.path.normpath(bpy.path.abspath(folder))
    # "Export To" pointing at the track's own folder already: don't nest another inside.
    out_dir = base if os.path.basename(base) == track_id else os.path.join(base, track_id)
    os.makedirs(out_dir, exist_ok=True)
    # Bring every road up to the add-on's current road generator (settings are kept),
    # re-project library UVs on edited meshes, refresh road shading.
    road.build_road_group()
    notes = materials.prepare_export()
    scene_objs = [o for o in bpy.context.scene.objects if o.type in DRIVEABLE_TYPES]
    visual = [o for o in scene_objs if role_of(o) in ("both", "visual") and o.visible_get()]
    collision = [o for o in scene_objs if role_of(o) in ("both", "collision")]
    routes = [o for o in scene_objs if o.get("kp_route") and o.type == "CURVE"]
    report = {"folder": out_dir, "visual": len(visual), "collision": len(collision), "warnings": [], "notes": notes}
    if not routes:
        raise RuntimeError("No route: select the main road curve and press 'Set as Route'.")
    if not collision:
        raise RuntimeError("Nothing to drive on: no objects with role 'both' or 'collision'.")
    report["warnings"] += check_surfaces(collision)

    _export_glb(os.path.join(out_dir, "visual.glb"), visual)
    _export_glb(os.path.join(out_dir, "collision.glb"), collision, images=False)

    main = next((o for o in routes if o.get("kp_route") == "main"), routes[0])
    route = {
        "schemaVersion": ROUTE_SCHEMA,
        "generator": "kartipelago_tools (Blender %s)" % bpy.app.version_string,
        "units": "metres",
        "up": "+y",
        "routes": [{"id": "main" if o is main else o.name, **sample_route(o)} for o in [main] + [r for r in routes if r is not main]],
    }
    # The environment first: route.json is written last, which is what the game's dev
    # server watches to reload the track.
    look = materials.environment(bpy.context.scene)
    with open(os.path.join(out_dir, "look.json"), "w") as f:
        json.dump(look, f, indent=2)
        f.write("\n")
    report["checkpoints"] = checkpoints.export(bpy.context.scene, out_dir)
    with open(os.path.join(out_dir, "route.json"), "w") as f:
        json.dump(route, f, separators=(",", ":"))
        f.write("\n")

    meta = os.path.join(out_dir, "track.json")
    if not os.path.exists(meta):
        with open(meta, "w") as f:
            json.dump(
                {
                    "schemaVersion": TRACK_SCHEMA,
                    "id": track_id,
                    "name": name or track_id.replace("_", " ").title(),
                    "geometry": {
                        "visual": "visual.glb",
                        "collision": "collision.glb",
                        "route": "route.json",
                        "look": "look.json",
                    },
                    "race": {"laps": 3},
                    "entities": [],
                },
                f,
                indent=2,
            )
            f.write("\n")
        report["created_track_json"] = True
    report["route_points"] = len(route["routes"][0]["points"])
    return report

