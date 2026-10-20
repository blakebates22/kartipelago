# Kartipelago Track Tools for Blender.
# SPDX-License-Identifier: MIT
"""
Spline roads, painted N64-style materials and one-click export of Kartipelago tracks.

Sidebar (N) > Kartipelago:
- Track: track id, Export Track (visual.glb, collision.glb, route.json, look.json into
  the game's public/tracks/<id>/; the game reloads it live while `npm run dev` runs).
- Roads: Add Road, Set as Route, object roles.
- Materials: browse the texture library by theme, pick a driving surface, and apply to
  selected faces, objects or a road. UVs are projected for you.
- Water & Lava: flow, ripple, opacity, glow and tint of the active material.
- Vertex Paint: one-click shading presets (darken bottoms, warm sunlight, tunnels...).
- Sky & Fog: the environment preset the game uses for this track.
- Checkpoints: the invisible gates a lap is made of. Generate them from the route, then
  move, rotate, scale, duplicate and renumber them (exported to checkpoints.json).
"""

bl_info = {
    "name": "Kartipelago Track Tools",
    "author": "Kartipelago contributors",
    "version": (0, 3, 0),
    "blender": (4, 2, 0),
    "location": "3D View > Sidebar > Kartipelago",
    "description": "Spline roads, N64-style materials and one-click track export for Kartipelago",
    "category": "Import-Export",
}

if "bpy" in locals():
    import importlib

    importlib.reload(road)  # noqa: F821
    importlib.reload(materials)  # noqa: F821
    importlib.reload(paint)  # noqa: F821
    importlib.reload(checkpoints)  # noqa: F821
    importlib.reload(export)  # noqa: F821
else:
    from . import checkpoints, export, materials, paint, road

import math

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, StringProperty

ROLES = [
    ("both", "Visual + Collision", "Seen and driven on / hit"),
    ("visual", "Visual only", "Decoration: seen, never collided with"),
    ("collision", "Collision only", "Invisible in game: driven on / hit"),
]


# ------------------------------------------------------------------ helpers


def _for_faces(context, fn):
    """
    Call fn(object, face_indices) for what's selected: in Edit Mode the selected faces
    of each mesh being edited, otherwise every face of each selected mesh. Returns the
    number of faces.
    """
    total = 0
    if context.mode == "EDIT_MESH":
        obs = [o for o in context.objects_in_mode_unique_data if o.type == "MESH"]
        bpy.ops.object.mode_set(mode="OBJECT")
        try:
            for o in obs:
                faces = [p.index for p in o.data.polygons if p.select]
                if faces:
                    fn(o, faces)
                    total += len(faces)
        finally:
            bpy.ops.object.mode_set(mode="EDIT")
    else:
        for o in context.selected_objects:
            if o.type == "MESH" and len(o.data.polygons):
                fn(o, list(range(len(o.data.polygons))))
                total += len(o.data.polygons)
    return total


def _theme_items(self, context):
    return [("all", "All Themes", "Every material")] + [
        (t["id"], t["name"], t["description"]) for t in materials.library()["themes"]
    ]


def _env_items(self, context):
    return [("none", "Game Default", "The game's usual sky and light")] + [
        (t["id"], t["name"], t["description"]) for t in materials.library()["themes"]
    ]


_pick_cache = []


def _pick_items(self, context):
    """Thumbnails for the browser: the current theme, filtered by the search box."""
    global _pick_cache
    s = context.scene if context else bpy.context.scene
    every = materials.library()["materials"]
    show = {m["id"] for m in materials.filtered(s.kp_theme, s.kp_mat_search)}
    items = []
    for i, m in enumerate(every):
        if m["id"] in show:
            items.append((m["id"], m["name"], f"{m['name']}: suggested surface {m['surface']}", materials.icon(m["id"]), i))
    if not items:
        m = every[0]
        items.append((m["id"], m["name"], "Nothing matches the search", materials.icon(m["id"]), 0))
    _pick_cache = items
    return _pick_cache


def _filter_changed(self, context):
    items = _pick_items(self, context)
    if self.kp_mat_pick not in {i[0] for i in items}:
        self.kp_mat_pick = items[0][0]


def _surface_items(self, context):
    s = context.scene if context else bpy.context.scene
    e = materials.entry(s.kp_mat_pick) if s else None
    first = ("default", f"Suggested ({e['surface']})" if e else "Suggested", "The library's suggestion for this texture")
    return [first] + road.SURFACES


ROTATIONS = [("0", "0°", ""), ("90", "90°", ""), ("180", "180°", ""), ("270", "270°", "")]
WRAPS = [
    ("default", "Suggested", "The library's setting for this texture"),
    ("repeat", "Repeat", "Tile the texture"),
    ("clamp", "Clamp", "Stretch the edge pixels past the edge (for a single decal)"),
]


def _current(context):
    """The browser's chosen library entry, material and settings."""
    s = context.scene
    e = materials.entry(s.kp_mat_pick)
    surface = None if s.kp_mat_surface == "default" else s.kp_mat_surface
    wrap = None if s.kp_mat_wrap == "default" else s.kp_mat_wrap
    size = s.kp_uv_size if s.kp_uv_size > 0 else e["tileMetres"]
    return e, surface, wrap, size, float(s.kp_uv_rotation), materials.aspect(e)


# ------------------------------------------------------------------ track & roads


class KP_OT_add_road(bpy.types.Operator):
    """Add a closed spline road (edit the curve to shape it; Tilt banks, Radius widens)"""

    bl_idname = "kartipelago.add_road"
    bl_label = "Add Road"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        c = context.scene.cursor.location
        r = 60.0
        pts = [
            (c.x + r * math.cos(a), c.y + r * math.sin(a), c.z, 0.0)
            for a in [i * math.tau / 8 for i in range(8)]
        ]
        ob = road.make_road("Road", pts, closed=True)
        for o in context.view_layer.objects:
            o.select_set(False)
        ob.select_set(True)
        context.view_layer.objects.active = ob
        return {"FINISHED"}


class KP_OT_set_route(bpy.types.Operator):
    """Make the active curve the race route (only one main route)"""

    bl_idname = "kartipelago.set_route"
    bl_label = "Set as Route"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == "CURVE"

    def execute(self, context):
        for o in bpy.data.objects:
            if "kp_route" in o:
                del o["kp_route"]
        context.active_object["kp_route"] = "main"
        return {"FINISHED"}


class KP_OT_set_role(bpy.types.Operator):
    """Set whether the selected objects are seen, collided with, or both"""

    bl_idname = "kartipelago.set_role"
    bl_label = "Set Role"
    bl_options = {"REGISTER", "UNDO"}
    role: EnumProperty(items=ROLES)

    def execute(self, context):
        for o in context.selected_objects:
            o["kp_role"] = self.role
        return {"FINISHED"}


class KP_OT_set_surface(bpy.types.Operator):
    """Change the driving surface of the active material. For a library material the
    faces switch to a version of it with this surface (the picture stays the same)"""

    bl_idname = "kartipelago.set_surface"
    bl_label = "Set Surface"
    bl_options = {"REGISTER", "UNDO"}
    surface: EnumProperty(items=road.SURFACES)

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob is not None and ob.active_material is not None

    def execute(self, context):
        ob = context.active_object
        mat = ob.active_material
        if materials.is_library(mat):
            e = materials.entry(mat["kp_texture"])
            if e is not None:
                new = materials.get_material(e, self.surface, mat.get("kp_wrap"))
                ob.material_slots[ob.active_material_index].material = new
                mod = materials.road_modifier(ob)
                if mod is not None:  # a road: swap it in the road's material inputs too
                    for sock in materials.PART_SOCKETS.values():
                        if road.get_input(mod, sock) == mat:
                            road.set_input(mod, sock, new)
                return {"FINISHED"}
        mat["kp_surface"] = self.surface
        return {"FINISHED"}


class KP_OT_export(bpy.types.Operator):
    """Export the track for the game (keeps track.json, so placements survive)"""

    bl_idname = "kartipelago.export_track"
    bl_label = "Export Track"

    def execute(self, context):
        s = context.scene
        if not s.kp_track_id:
            self.report({"ERROR"}, "Set a Track ID first")
            return {"CANCELLED"}
        if context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        try:
            rep = export.export_track(s.kp_export_dir, s.kp_track_id, s.kp_track_name or None)
        except RuntimeError as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}
        for w in rep["warnings"]:
            self.report({"WARNING"}, w)
        self.report(
            {"INFO"},
            f"Exported {rep['visual']} visual / {rep['collision']} collision objects to {rep['folder']}",
        )
        return {"FINISHED"}


# ------------------------------------------------------------------ materials


class KP_OT_pick_material(bpy.types.Operator):
    """Choose this texture in the Material Browser"""

    bl_idname = "kartipelago.pick_material"
    bl_label = "Pick Material"
    mat_id: StringProperty()

    def execute(self, context):
        context.scene.kp_mat_pick = self.mat_id
        return {"FINISHED"}


class KP_OT_pick_from_active(bpy.types.Operator):
    """Show the active object's material in the browser (to reuse its texture)"""

    bl_idname = "kartipelago.pick_from_active"
    bl_label = "From Active"

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob is not None and materials.is_library(ob.active_material)

    def execute(self, context):
        s = context.scene
        mat = context.active_object.active_material
        e = materials.entry(mat["kp_texture"])
        if e is None:
            return {"CANCELLED"}
        s.kp_theme = "all"
        s.kp_mat_search = ""
        s.kp_mat_pick = e["id"]
        surf = mat.get("kp_surface")
        s.kp_mat_surface = "default" if surf == e["surface"] else surf
        return {"FINISHED"}


class KP_OT_apply_material(bpy.types.Operator):
    """Paint the chosen texture and surface onto the selection: selected faces (Edit Mode), selected objects, or part of the active road"""

    bl_idname = "kartipelago.apply_material"
    bl_label = "Apply"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if materials.road_modifier(ob) is not None:
            return True
        return context.mode == "EDIT_MESH" or any(o.type == "MESH" for o in context.selected_objects)

    def execute(self, context):
        e, surface, wrap, size, rot, asp = _current(context)
        mat = materials.get_material(e, surface, wrap)
        ob = context.active_object
        if context.mode != "EDIT_MESH" and materials.road_modifier(ob) is not None:
            part = context.scene.kp_road_part
            materials.apply_to_road(ob, mat, part, size, rot, asp)
            self.report({"INFO"}, f"{mat.name} on the road's {part}")
            return {"FINISHED"}
        n = _for_faces(context, lambda o, faces: materials.assign_faces(o, mat, faces, size, rot, asp))
        if n == 0:
            self.report({"WARNING"}, "Nothing selected: select faces (Edit Mode) or objects")
            return {"CANCELLED"}
        self.report({"INFO"}, f"{mat.name} on {n} faces ({size:g} m repeat)")
        return {"FINISHED"}


class KP_OT_refresh_uvs(bpy.types.Operator):
    """Re-project the texture on selected objects after editing their shape (export does this too)"""

    bl_idname = "kartipelago.refresh_uvs"
    bl_label = "Refresh UVs"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        n = _for_faces(context, lambda o, faces: (materials.project(o, faces), o.data.update()))
        self.report({"INFO"}, f"Re-projected {n} faces")
        return {"FINISHED"}


class KP_OT_keep_uvs(bpy.types.Operator):
    """Keep these faces' own UVs: export won't re-project them (for hand-made UVs)"""

    bl_idname = "kartipelago.keep_uvs"
    bl_label = "Keep My UVs"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        n = _for_faces(context, materials.keep_uvs)
        self.report({"INFO"}, f"{n} faces keep their own UVs")
        return {"FINISHED"}


class KP_OT_preview(bpy.types.Operator):
    """Show textures and vertex paint in the 3D view (Material Preview)"""

    bl_idname = "kartipelago.preview_textures"
    bl_label = "Show Textures"

    def execute(self, context):
        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.shading.type = "MATERIAL"
        return {"FINISHED"}


# ------------------------------------------------------------------ vertex paint


class KP_OT_paint_preset(bpy.types.Operator):
    """Paint colour variation onto the selected objects (or selected faces in Edit Mode)"""

    bl_idname = "kartipelago.paint_preset"
    bl_label = "Paint Preset"
    bl_options = {"REGISTER", "UNDO"}
    preset: EnumProperty(items=paint.PRESETS)

    @classmethod
    def description(cls, context, props):
        return next(p[2] for p in paint.PRESETS if p[0] == props.preset)

    def execute(self, context):
        s = context.scene
        edit = context.mode == "EDIT_MESH"
        road_objs = [] if edit else [o for o in context.selected_objects if materials.road_modifier(o) is not None]
        if road_objs and self.preset in ("cover", "reset"):
            paint.shade_roads(road_objs, 0.0 if self.preset == "reset" else s.kp_paint_strength)
        if edit:
            obs = [o for o in context.objects_in_mode_unique_data if o.type == "MESH"]
            bpy.ops.object.mode_set(mode="OBJECT")
        else:
            obs = [o for o in context.selected_objects if o.type == "MESH"]
        try:
            ts = [paint.Target(o, [p.index for p in o.data.polygons if p.select] if edit else None) for o in obs]
            ts = [t for t in ts if t.corners]
            if not ts and not road_objs:
                self.report({"WARNING"}, "Select objects (or faces in Edit Mode) first")
                return {"CANCELLED"}
            paint.run(
                self.preset,
                ts,
                s.kp_paint_strength,
                tuple(s.kp_paint_color),
                s.kp_paint_distance,
                paint.sun_direction(s),
            )
        finally:
            if edit:
                bpy.ops.object.mode_set(mode="EDIT")
        return {"FINISHED"}


# ------------------------------------------------------------------ panels


class KP_PT_panel(bpy.types.Panel):
    bl_label = "Kartipelago"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Kartipelago"

    def draw(self, context):
        s = context.scene
        ob = context.active_object
        col = self.layout.column(align=True)
        col.label(text="Track")
        col.prop(s, "kp_track_id")
        col.prop(s, "kp_track_name")
        col.prop(s, "kp_export_dir")
        col.operator(KP_OT_export.bl_idname, icon="EXPORT")

        col = self.layout.column(align=True)
        col.label(text="Roads")
        col.operator(KP_OT_add_road.bl_idname, icon="CURVE_BEZCURVE")
        col.operator(KP_OT_set_route.bl_idname, icon="TRACKING")
        if ob is not None and ob.get("kp_route"):
            col.label(text="This curve is the route", icon="CHECKMARK")

        if ob is not None:
            col = self.layout.column(align=True)
            col.label(text=f"Role: {export.role_of(ob)}")
            row = col.row(align=True)
            for key, label, _ in ROLES:
                row.operator(KP_OT_set_role.bl_idname, text=label.split(" ")[0]).role = key
            mat = ob.active_material
            if mat is not None:
                col.label(text=f"Surface of '{mat.name}': {mat.get('kp_surface', 'none')}")
                col.operator_menu_enum(KP_OT_set_surface.bl_idname, "surface", text="Set Surface")


class KP_OT_cp_generate(bpy.types.Operator):
    """Place main-route checkpoints along the route: the start line, after every real turn, and enough in between (replaces the existing main-route checkpoints)"""

    bl_idname = "kartipelago.cp_generate"
    bl_label = "Generate from Route"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            made = checkpoints.generate(context.scene, margin=context.scene.kp_cp_margin, height=context.scene.kp_cp_height)
        except RuntimeError as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}
        self.report({"INFO"}, f"Placed {len(made)} checkpoints")
        return {"FINISHED"}

    def invoke(self, context, event):
        if any(o.get("kp_cp_route", "main") == "main" for o in checkpoints.checkpoints(context.scene)):
            return context.window_manager.invoke_confirm(self, event)
        return self.execute(context)


class KP_OT_cp_add(bpy.types.Operator):
    """Add a checkpoint at the 3D cursor, facing along the route there (use Alternate Route for a shortcut's gate)"""

    bl_idname = "kartipelago.cp_add"
    bl_label = "Add Checkpoint"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        s = context.scene
        samples, length = checkpoints.route_samples(s)
        cur = s.cursor.location.copy()
        f = (0.0, 1.0)
        width = 30.0
        if samples:
            best = min(samples, key=lambda q: (q[0] - cur).length_squared)
            f = (best[1].x, best[1].y)
            width = best[2] + 2 * checkpoints.MARGIN
        a = context.view_layer.objects.active
        index = a["kp_checkpoint"] + 1 if checkpoints.is_checkpoint(a) else len(checkpoints.checkpoints(s))
        route = s.kp_cp_new_route.strip() or "main"
        ob = checkpoints.make(s, index, cur, f, width, s.kp_cp_height, route=route)
        for o in context.selected_objects:
            o.select_set(False)
        ob.select_set(True)
        context.view_layer.objects.active = ob
        if route == "main":
            checkpoints.renumber(s)
        return {"FINISHED"}


class KP_OT_cp_renumber(bpy.types.Operator):
    """Number the main-route checkpoints in order round the route (after moving, duplicating or deleting some)"""

    bl_idname = "kartipelago.cp_renumber"
    bl_label = "Renumber"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        n = checkpoints.renumber(context.scene)
        self.report({"INFO"}, f"{n} main-route checkpoints in order")
        return {"FINISHED"}


class KP_OT_cp_step(bpy.types.Operator):
    """Select the next (or previous) checkpoint in the order"""

    bl_idname = "kartipelago.cp_step"
    bl_label = "Next Checkpoint"
    direction: bpy.props.IntProperty(default=1)

    def execute(self, context):
        if checkpoints.step_selection(context, self.direction) is None:
            return {"CANCELLED"}
        return {"FINISHED"}


class KP_OT_cp_show(bpy.types.Operator):
    """Show or hide the checkpoints (they're never seen in the game)"""

    bl_idname = "kartipelago.cp_show"
    bl_label = "Show / Hide Checkpoints"

    def execute(self, context):
        cps = checkpoints.checkpoints(context.scene)
        if not cps:
            return {"CANCELLED"}
        hide = not cps[0].hide_get()
        for o in cps:
            o.hide_set(hide)
            for ch in o.children:
                ch.hide_set(hide)
        line = bpy.data.objects.get(checkpoints.ORDER_NAME)
        if line:
            line.hide_set(hide)
        return {"FINISHED"}


class KP_PT_checkpoints(bpy.types.Panel):
    bl_label = "Checkpoints"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Kartipelago"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        s = context.scene
        ob = context.active_object
        cps = checkpoints.checkpoints(s)
        col = self.layout.column(align=True)
        main = [o for o in cps if o.get("kp_cp_route", "main") == "main"]
        col.label(text=f"{len(main)} checkpoints, {len(cps) - len(main)} on alternate routes")
        row = col.row(align=True)
        row.prop(s, "kp_cp_margin")
        row.prop(s, "kp_cp_height")
        col.operator(KP_OT_cp_generate.bl_idname, icon="FORCE_HARMONIC")
        col.separator()
        col.prop(s, "kp_cp_new_route", text="Route")
        col.operator(KP_OT_cp_add.bl_idname, icon="ADD")
        col.operator(KP_OT_cp_renumber.bl_idname, icon="SORTSIZE")
        row = col.row(align=True)
        row.operator(KP_OT_cp_step.bl_idname, text="Previous", icon="TRIA_LEFT").direction = -1
        row.operator(KP_OT_cp_step.bl_idname, text="Next", icon="TRIA_RIGHT").direction = 1
        col.operator(KP_OT_cp_show.bl_idname, icon="HIDE_OFF")
        if checkpoints.is_checkpoint(ob):
            box = self.layout.box()
            box.label(text=ob.name, icon="TRACKING")
            box.prop(ob, '["kp_checkpoint"]', text="Number")
            box.prop(ob, '["kp_cp_route"]', text="Route")
            box.prop(ob, "scale", index=0, text="Width")
            box.prop(ob, "scale", index=2, text="Height")
            box.prop(ob, '["kp_cp_below"]', text="Below")
            box.label(text="Move / rotate / Shift+D / X as usual", icon="INFO")
        self.layout.label(text="Gold: start   Green: main   Orange: alternate")


class KP_PT_materials(bpy.types.Panel):
    bl_label = "Materials"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Kartipelago"

    def draw(self, context):
        s = context.scene
        ob = context.active_object
        lay = self.layout
        col = lay.column(align=True)
        col.prop(s, "kp_theme", text="Theme")
        col.prop(s, "kp_mat_search", text="", icon="VIEWZOOM")

        # The big thumbnail: click it for every texture in the theme.
        lay.template_icon_view(s, "kp_mat_pick", show_labels=True, scale=6.0, scale_popup=4.0)
        e = materials.entry(s.kp_mat_pick)
        if e is not None:
            w, h = materials.image_size(e)
            box = lay.box()
            box.label(text=e["name"], icon="TEXTURE")
            box.label(text=f"{w}×{h} px · suggested surface: {e['surface']}")

        # Every texture in the theme as a clickable list.
        grid = lay.grid_flow(row_major=True, columns=2, even_columns=True, align=True)
        for m in materials.filtered(s.kp_theme, s.kp_mat_search):
            label = m["name"].split(" ", 1)[-1]
            grid.operator(
                KP_OT_pick_material.bl_idname,
                text=label,
                icon_value=materials.icon(m["id"]),
                depress=m["id"] == s.kp_mat_pick,
            ).mat_id = m["id"]

        col = lay.column(align=True)
        col.label(text="Settings")
        col.prop(s, "kp_mat_surface", text="Surface")
        col.prop(s, "kp_uv_size", text="Repeat Size (m)")
        if s.kp_uv_size <= 0 and e is not None:
            col.label(text=f"   0 = suggested: {e['tileMetres']:g} m", icon="INFO")
        row = col.row(align=True)
        row.prop(s, "kp_uv_rotation", expand=True)
        col.prop(s, "kp_mat_wrap", text="Edges")

        is_road = context.mode != "EDIT_MESH" and materials.road_modifier(ob) is not None
        if is_road:
            col.prop(s, "kp_road_part", text="Road Part")
            text = f"Apply to Road ({dict((p[0], p[1]) for p in materials.ROAD_PARTS)[s.kp_road_part]})"
        elif context.mode == "EDIT_MESH":
            text = "Apply to Selected Faces"
        else:
            text = "Apply to Selected Objects"
        big = lay.row()
        big.scale_y = 1.6
        big.operator(KP_OT_apply_material.bl_idname, text=text, icon="BRUSH_DATA")
        if not is_road and context.mode != "EDIT_MESH":
            lay.label(text="Tab into Edit Mode to paint just some faces", icon="INFO")

        row = lay.row(align=True)
        row.operator(KP_OT_preview.bl_idname, icon="SHADING_TEXTURE")
        row.operator(KP_OT_pick_from_active.bl_idname, icon="EYEDROPPER")
        row = lay.row(align=True)
        row.operator(KP_OT_refresh_uvs.bl_idname, icon="UV")
        row.operator(KP_OT_keep_uvs.bl_idname, icon="LOCKED")


class KP_PT_effects(bpy.types.Panel):
    bl_label = "Water & Lava"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Kartipelago"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        ob = context.active_object
        mat = ob.active_material if ob else None
        lay = self.layout
        if not materials.is_library(mat):
            lay.label(text="Select something with a library material")
            return
        fx = mat.kp_fx
        lay.label(text=mat.name, icon="MATERIAL")
        col = lay.column(align=True)
        col.label(text="Moves in the game (not in Blender):")
        col.prop(fx, "scroll_u")
        col.prop(fx, "scroll_v")
        col.prop(fx, "wave")
        col.prop(fx, "wave_period")
        col.prop(fx, "pulse", slider=True)
        col.prop(fx, "pulse_period")
        col = lay.column(align=True)
        col.prop(fx, "opacity", slider=True)
        col.prop(fx, "glow")
        col.prop(fx, "tint")
        lay.label(text="Shared by everything using this material", icon="INFO")


class KP_PT_paint(bpy.types.Panel):
    bl_label = "Vertex Paint"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Kartipelago"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        s = context.scene
        lay = self.layout
        col = lay.column(align=True)
        col.prop(s, "kp_paint_strength", slider=True)
        col.prop(s, "kp_paint_color", text="Tint")
        col.prop(s, "kp_paint_distance", text="Distance (m)")
        col = lay.column(align=True)
        for key, label, _ in paint.PRESETS:
            icon = "LOOP_BACK" if key == "reset" else "BRUSH_DATA"
            col.operator(KP_OT_paint_preset.bl_idname, text=label, icon=icon).preset = key
        lay.label(text="Works on selected objects, or", icon="INFO")
        lay.label(text="selected faces in Edit Mode.")
        lay.label(text="Roads: Darken Under Cover.")


class KP_PT_environment(bpy.types.Panel):
    bl_label = "Sky & Fog"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Kartipelago"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        s = context.scene
        col = self.layout.column(align=True)
        col.prop(s, "kp_environment", text="Sky")
        col.prop(s, "kp_fog")
        col.label(text="Used by the game on export", icon="INFO")


CLASSES = (
    materials.KPMaterialFx,
    KP_OT_add_road,
    KP_OT_set_route,
    KP_OT_set_role,
    KP_OT_set_surface,
    KP_OT_export,
    KP_OT_pick_material,
    KP_OT_pick_from_active,
    KP_OT_apply_material,
    KP_OT_refresh_uvs,
    KP_OT_keep_uvs,
    KP_OT_preview,
    KP_OT_paint_preset,
    KP_PT_panel,
    KP_PT_materials,
    KP_PT_effects,
    KP_PT_paint,
    KP_PT_environment,
    KP_OT_cp_generate,
    KP_OT_cp_add,
    KP_OT_cp_renumber,
    KP_OT_cp_step,
    KP_OT_cp_show,
    KP_PT_checkpoints,
)

SCENE_PROPS = {
    "kp_track_id": StringProperty(name="Track ID", description="Folder name, e.g. forest_circuit"),
    "kp_track_name": StringProperty(name="Name", description="Display name"),
    "kp_export_dir": StringProperty(
        name="Export To",
        subtype="DIR_PATH",
        default="//../public/tracks/",
        description="The game's public/tracks folder ('//' = next to this .blend)",
    ),
    "kp_theme": EnumProperty(name="Theme", items=_theme_items, update=_filter_changed),
    "kp_mat_search": StringProperty(name="Search", description="Filter by name", update=_filter_changed, options={"TEXTEDIT_UPDATE"}),
    "kp_mat_pick": EnumProperty(name="Texture", items=_pick_items),
    "kp_mat_surface": EnumProperty(
        name="Surface", items=_surface_items, description="How it drives (separate from how it looks)"
    ),
    "kp_uv_size": FloatProperty(
        name="Repeat Size",
        description="Metres one copy of the texture covers across. 0 = the library's suggestion",
        default=0.0,
        min=0.0,
        soft_max=40.0,
        unit="LENGTH",
    ),
    "kp_uv_rotation": EnumProperty(name="Rotation", items=ROTATIONS, default="0"),
    "kp_mat_wrap": EnumProperty(name="Edges", items=WRAPS, default="default"),
    "kp_road_part": EnumProperty(name="Road Part", items=materials.ROAD_PARTS, default="road"),
    "kp_environment": EnumProperty(name="Sky & Light", items=_env_items, description="The game's sky, sun and fog for this track"),
    "kp_fog": BoolProperty(name="Distance Fog", default=True),
    "kp_cp_margin": FloatProperty(
        name="Margin", description="Extra gate width beside the road, each side, m", default=18.0, min=0.0, soft_max=60.0
    ),
    "kp_cp_height": FloatProperty(
        name="Height",
        description="Gate height above the road, m (keep it under the height between layers on layered tracks)",
        default=6.0,
        min=1.0,
        soft_max=30.0,
    ),
    "kp_cp_new_route": StringProperty(
        name="Route",
        description="Route for new checkpoints: 'main', or a shortcut's name (its gates count the same as the main gate with their number)",
        default="main",
    ),
    "kp_paint_strength": FloatProperty(name="Strength", default=0.4, min=0.0, max=1.0, subtype="FACTOR"),
    "kp_paint_color": FloatVectorProperty(
        name="Tint", subtype="COLOR", size=3, default=(1.0, 0.88, 0.62), min=0.0, max=1.0
    ),
    "kp_paint_distance": FloatProperty(
        name="Distance", description="How far presets reach (near roads, ray up for cover)", default=8.0, min=0.5, soft_max=60.0
    ),
}


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)
    bpy.types.Material.kp_fx = bpy.props.PointerProperty(type=materials.KPMaterialFx)
    for name, prop in SCENE_PROPS.items():
        setattr(bpy.types.Scene, name, prop)


def unregister():
    for name in SCENE_PROPS:
        delattr(bpy.types.Scene, name)
    del bpy.types.Material.kp_fx
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
    materials.free_previews()
