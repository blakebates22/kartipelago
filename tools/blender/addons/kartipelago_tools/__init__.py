# Kartipelago Track Tools for Blender.
# SPDX-License-Identifier: MIT
"""
Spline roads and one-click export of Kartipelago tracks.

Sidebar (N) > Kartipelago:
- Add Road: a closed Bezier road with the live "KP Road" Geometry Nodes modifier.
- Set as Route: the selected curve is the race route (checkpoints, grid, AI).
- Role: whether an object is seen, collided with, or both.
- Surface: the semantic surface of the active material (asphalt, grass, wall...).
- Export Track: writes visual.glb, collision.glb and route.json into the game's
  public/tracks/<id>/ folder; the game reloads it live while `npm run dev` runs.
"""

bl_info = {
    "name": "Kartipelago Track Tools",
    "author": "Kartipelago contributors",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "location": "3D View > Sidebar > Kartipelago",
    "description": "Spline roads and one-click track export for Kartipelago",
    "category": "Import-Export",
}

if "bpy" in locals():
    import importlib

    importlib.reload(road)  # noqa: F821
    importlib.reload(export)  # noqa: F821
else:
    from . import export, road

import math

import bpy
from bpy.props import EnumProperty, StringProperty

ROLES = [
    ("both", "Visual + Collision", "Seen and driven on / hit"),
    ("visual", "Visual only", "Decoration: seen, never collided with"),
    ("collision", "Collision only", "Invisible in game: driven on / hit"),
]


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
    """Tag the active object's active material with a gameplay surface"""

    bl_idname = "kartipelago.set_surface"
    bl_label = "Set Surface"
    bl_options = {"REGISTER", "UNDO"}
    surface: EnumProperty(items=road.SURFACES)

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob is not None and ob.active_material is not None

    def execute(self, context):
        context.active_object.active_material["kp_surface"] = self.surface
        return {"FINISHED"}


class KP_OT_export(bpy.types.Operator):
    """Export visual.glb, collision.glb and route.json for the game (keeps track.json)"""

    bl_idname = "kartipelago.export_track"
    bl_label = "Export Track"

    def execute(self, context):
        s = context.scene
        if not s.kp_track_id:
            self.report({"ERROR"}, "Set a Track ID first")
            return {"CANCELLED"}
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


CLASSES = (KP_OT_add_road, KP_OT_set_route, KP_OT_set_role, KP_OT_set_surface, KP_OT_export, KP_PT_panel)


def register():
    bpy.types.Scene.kp_track_id = StringProperty(name="Track ID", description="Folder name, e.g. forest_circuit")
    bpy.types.Scene.kp_track_name = StringProperty(name="Name", description="Display name")
    bpy.types.Scene.kp_export_dir = StringProperty(
        name="Export To",
        subtype="DIR_PATH",
        default="//../public/tracks/",
        description="The game's public/tracks folder ('//' = next to this .blend)",
    )
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.kp_track_id
    del bpy.types.Scene.kp_track_name
    del bpy.types.Scene.kp_export_dir
