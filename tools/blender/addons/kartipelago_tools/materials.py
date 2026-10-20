# Kartipelago Track Tools: the material library and Material Browser logic.
# SPDX-License-Identifier: MIT
"""
Library materials are ordinary Blender materials built from a small repeating image
(library/textures/*.png, listed in library/materials.json):

    Image Texture -> x Color Attribute "Col" (vertex paint) -> x Tint -> Base Color
                  \\-> Emission Color (glow, for lava)

The glTF exporter turns that into a standard glTF material: base colour texture, tint as
the base colour factor, glow as emissive, opacity as alpha, the image's Repeat / Extend
setting as the sampler's wrap. Things glTF has no slot for travel as material extras:

    kp_surface   the driving surface (physics), chosen separately from the image
    kp_texture   which library image it is
    kp_fx        water/lava animation: scroll_u, scroll_v (repeats per second),
                 wave (wobble, fraction of a repeat) and wave_period (seconds);
                 pulse (glow swelling by that share) and pulse_period (seconds)

UVs are projected in world space, so texture density is the same everywhere: one
repeat of a texture covers `tileMetres` across (and tileMetres x height/width up or
along, so texels stay square). Floors are mapped from above, walls from the side with
the texture upright. Each face remembers its tile size and rotation (face attributes
kp_uv_size, kp_uv_rot, kp_uv_aspect), and export re-projects those faces, so editing
the mesh never leaves stale, stretched UVs. Faces whose kp_uv_size is 0 keep their own
hand-made UVs.
"""

import json
import math
import os

import bpy
from . import road

LIB_DIR = os.path.join(os.path.dirname(__file__), "library")
PAINT = "Col"  # the colour attribute vertex painting uses, exported as glTF COLOR_0
SHADE_COLLECTION = "KP Shade Casters"

_library = None


def library():
    """The parsed library/materials.json (cached)."""
    global _library
    if _library is None:
        with open(os.path.join(LIB_DIR, "materials.json"), encoding="utf-8") as f:
            _library = json.load(f)
    return _library


def entry(mat_id):
    return next((m for m in library()["materials"] if m["id"] == mat_id), None)


def theme(theme_id):
    return next((t for t in library()["themes"] if t["id"] == theme_id), None)


def image_size(e):
    """(width, height) of a library texture, read from its PNG header."""
    with open(os.path.join(LIB_DIR, "textures", e["image"]), "rb") as f:
        head = f.read(24)
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")


def aspect(e):
    w, h = image_size(e)
    return h / w


def filtered(theme_id, search):
    """Library entries in a theme ('all' for every theme) whose name matches `search`."""
    words = search.lower().split()
    out = []
    for m in library()["materials"]:
        if theme_id not in ("all", m["theme"]):
            continue
        hay = f"{m['id']} {m['name']} {m['surface']} {m['theme']}".lower()
        if all(w in hay for w in words):
            out.append(m)
    return out


# ------------------------------------------------------------------ thumbnails

_previews = None


def previews():
    """A preview collection with a thumbnail per library material (keyed by id)."""
    global _previews
    if _previews is None:
        import bpy.utils.previews

        _previews = bpy.utils.previews.new()
        for m in library()["materials"]:
            path = os.path.join(LIB_DIR, "thumbs", m["image"])
            if not os.path.exists(path):
                path = os.path.join(LIB_DIR, "textures", m["image"])
            _previews.load(m["id"], path, "IMAGE")
    return _previews


def free_previews():
    global _previews
    if _previews is not None:
        import bpy.utils.previews

        bpy.utils.previews.remove(_previews)
        _previews = None


def icon(mat_id):
    p = previews().get(mat_id)
    return p.icon_id if p else 0


# ------------------------------------------------------------------ materials


class KPMaterialFx(bpy.types.PropertyGroup):
    """Water and lava effects for a library material (animated in the game)."""

    def _changed(self, context):
        sync_nodes(self.id_data)

    scroll_u: bpy.props.FloatProperty(
        name="Flow Across",
        description="Texture scroll, repeats per second (sideways on the image)",
        default=0.0,
        soft_min=-0.5,
        soft_max=0.5,
        step=1,
        precision=3,
    )
    scroll_v: bpy.props.FloatProperty(
        name="Flow Along",
        description="Texture scroll, repeats per second (up/down on the image)",
        default=0.0,
        soft_min=-0.5,
        soft_max=0.5,
        step=1,
        precision=3,
    )
    wave: bpy.props.FloatProperty(
        name="Ripple",
        description="A small looping wobble, as a fraction of one texture repeat (0 = none)",
        default=0.0,
        min=0.0,
        soft_max=0.25,
        step=1,
        precision=3,
    )
    wave_period: bpy.props.FloatProperty(
        name="Ripple Time", description="Seconds per ripple loop", default=4.0, min=0.1, soft_max=20.0, unit="TIME_ABSOLUTE"
    )
    opacity: bpy.props.FloatProperty(
        name="Opacity",
        description="1 = solid. Lower lets you see through it (water)",
        default=1.0,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
        update=_changed,
    )
    glow: bpy.props.FloatProperty(
        name="Glow",
        description="Shines with its own light, unaffected by shade (lava). 0 = none",
        default=0.0,
        min=0.0,
        soft_max=2.0,
        update=_changed,
    )
    pulse: bpy.props.FloatProperty(
        name="Pulse",
        description="The glow swells and fades by this share (0 = steady), like a living crystal",
        default=0.0,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )
    pulse_period: bpy.props.FloatProperty(
        name="Pulse Time", description="Seconds per pulse", default=4.0, min=0.1, soft_max=20.0, unit="TIME_ABSOLUTE"
    )
    tint: bpy.props.FloatVectorProperty(
        name="Tint",
        description="Multiplies the texture's colour (white = unchanged)",
        subtype="COLOR",
        size=3,
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        update=_changed,
    )


def library_image(e):
    """The library texture as a packed Blender image (packed: the .blend carries it)."""
    name = f"KP {e['id']}"
    img = bpy.data.images.get(name)
    if img is None:
        img = bpy.data.images.load(os.path.join(LIB_DIR, "textures", e["image"]))
        img.name = name
        img.pack()
    return img


def material_name(e, surface, wrap):
    tags = []
    if surface != e["surface"]:
        tags.append(surface)
    if wrap != e.get("wrap", "repeat"):
        tags.append(wrap)
    return f"KP {e['name']}" + (f" [{', '.join(tags)}]" if tags else "")


def get_material(e, surface=None, wrap=None):
    """
    The material for library entry `e` with this driving surface and edge wrap. The same
    image with a different surface is a separate material ("KP Ancient Road [grass]"),
    so surfaces never depend on the picture.
    """
    surface = surface or e["surface"]
    wrap = wrap or e.get("wrap", "repeat")
    name = material_name(e, surface, wrap)
    mat = bpy.data.materials.get(name)
    if mat is not None and mat.get("kp_texture") == e["id"]:
        return mat
    mat = bpy.data.materials.new(name)
    mat["kp_texture"] = e["id"]
    mat["kp_surface"] = surface
    mat["kp_wrap"] = wrap
    fx = e.get("fx", {})
    mat.kp_fx.scroll_u = fx.get("scrollU", 0.0)
    mat.kp_fx.scroll_v = fx.get("scrollV", 0.0)
    mat.kp_fx.wave = fx.get("wave", 0.0)
    mat.kp_fx.wave_period = fx.get("wavePeriod", 4.0)
    mat.kp_fx.opacity = fx.get("opacity", 1.0)
    mat.kp_fx.glow = fx.get("glow", 0.0)
    mat.kp_fx.pulse = fx.get("pulse", 0.0)
    mat.kp_fx.pulse_period = fx.get("pulsePeriod", 4.0)
    build_nodes(mat, e, wrap)
    return mat


def is_library(mat):
    return mat is not None and mat.get("kp_texture") is not None


def build_nodes(mat, e, wrap):
    if hasattr(mat, "use_nodes") and not mat.use_nodes:
        mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes, nt.links
    out = N.new("ShaderNodeOutputMaterial")
    out.location = (700, 0)
    bsdf = N.new("ShaderNodeBsdfPrincipled")
    bsdf.name = "KP BSDF"
    bsdf.location = (400, 0)
    L.new(bsdf.outputs[0], out.inputs["Surface"])
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Metallic"].default_value = 0.0
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.0
    tex = N.new("ShaderNodeTexImage")
    tex.name = "KP Image"
    tex.location = (-400, 0)
    tex.image = library_image(e)
    tex.interpolation = "Closest"  # crisp texels in the viewport
    tex.extension = "EXTEND" if wrap == "clamp" else "REPEAT"
    paint = N.new("ShaderNodeVertexColor")
    paint.name = "KP Paint"
    paint.layer_name = PAINT
    paint.location = (-400, -260)
    mul = N.new("ShaderNodeMix")
    mul.name = "KP Paint Mix"
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    mul.location = (-150, 0)
    L.new(tex.outputs["Color"], mul.inputs[6])
    L.new(paint.outputs["Color"], mul.inputs[7])
    tint = N.new("ShaderNodeMix")
    tint.name = "KP Tint"
    tint.data_type = "RGBA"
    tint.blend_type = "MULTIPLY"
    tint.inputs["Factor"].default_value = 1.0
    tint.location = (100, 0)
    L.new(mul.outputs[2], tint.inputs[6])
    L.new(tint.outputs[2], bsdf.inputs["Base Color"])
    L.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
    sync_nodes(mat)


def sync_nodes(mat):
    """Show a material's tint, glow and opacity in Blender (and in the exported glTF)."""
    nt = mat.node_tree
    if nt is None or "KP BSDF" not in nt.nodes:
        return
    fx = mat.kp_fx
    bsdf = nt.nodes["KP BSDF"]
    nt.nodes["KP Tint"].inputs[7].default_value = (*fx.tint, 1.0)
    bsdf.inputs["Emission Strength"].default_value = fx.glow
    bsdf.inputs["Alpha"].default_value = fx.opacity
    see_through = fx.opacity < 0.999
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED" if see_through else "DITHERED"
    elif hasattr(mat, "blend_method"):
        mat.blend_method = "BLEND" if see_through else "OPAQUE"


# ------------------------------------------------------------------ UV projection


def _float_attr(me, name, default=0.0):
    a = me.attributes.get(name)
    if a is None or a.domain != "FACE" or a.data_type != "FLOAT":
        if a is not None:
            me.attributes.remove(a)
        a = me.attributes.new(name, "FLOAT", "FACE")
        if default:
            a.data.foreach_set("value", [default] * len(me.polygons))
    return a


def ensure_paint(me):
    """Give a mesh the white "Col" colour attribute that vertex painting uses."""
    ca = me.color_attributes.get(PAINT)
    if ca is None or ca.domain != "CORNER":
        if ca is not None:
            me.color_attributes.remove(ca)
        ca = me.color_attributes.new(PAINT, "BYTE_COLOR", "CORNER")
        ca.data.foreach_set("color", [1.0] * (4 * len(me.loops)))
    me.color_attributes.active_color = ca
    try:
        me.color_attributes.render_color_index = me.color_attributes.active_color_index
    except (AttributeError, TypeError):
        pass
    return ca


def planar(n, p):
    """World-space projection: floors from above, walls from the side, upright."""
    ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
    if az >= ax and az >= ay:
        return p.x, p.y
    if ax >= ay:
        return (p.y if n.x > 0 else -p.y), p.z
    return (-p.x if n.y > 0 else p.x), p.z


def project(ob, faces=None):
    """
    Re-project the UVs of `faces` (polygon indices; None = every face that has a tile
    size) from their stored kp_uv_size / kp_uv_rot / kp_uv_aspect. Returns the count.
    """
    me = ob.data
    size = me.attributes.get("kp_uv_size")
    if size is None:
        return 0
    rot = me.attributes.get("kp_uv_rot")
    asp = me.attributes.get("kp_uv_aspect")
    uv = me.uv_layers.active or me.uv_layers.new(name="UVMap")
    mw = ob.matrix_world
    nm = mw.inverted_safe().transposed().to_3x3()
    verts, loops = me.vertices, me.loops
    polys = me.polygons if faces is None else [me.polygons[i] for i in faces]
    count = 0
    for p in polys:
        s = size.data[p.index].value
        if s <= 0:
            continue
        a = asp.data[p.index].value if asp else 0.5
        r = math.radians(rot.data[p.index].value) if rot else 0.0
        c, sn = math.cos(r), math.sin(r)
        n = (nm @ p.normal).normalized()
        for li in p.loop_indices:
            u, v = planar(n, mw @ verts[loops[li].vertex_index].co)
            uv.data[li].uv = ((u * c - v * sn) / s, (u * sn + v * c) / (s * max(a, 1e-3)))
        count += 1
    return count


def assign_faces(ob, mat, faces, size, rot_deg, asp):
    """Give `faces` of a mesh object this material and project their UVs."""
    me = ob.data
    names = [m.name if m else None for m in me.materials]
    if mat.name in names:
        slot = names.index(mat.name)
    else:
        me.materials.append(mat)
        slot = len(me.materials) - 1
    s_attr = _float_attr(me, "kp_uv_size")
    r_attr = _float_attr(me, "kp_uv_rot")
    a_attr = _float_attr(me, "kp_uv_aspect", 0.5)
    for i in faces:
        me.polygons[i].material_index = slot
        s_attr.data[i].value = size
        r_attr.data[i].value = rot_deg
        a_attr.data[i].value = asp
    ensure_paint(me)
    project(ob, faces)
    me.update()


def keep_uvs(ob, faces):
    """Stop export from re-projecting these faces (for hand-made UVs)."""
    a = ob.data.attributes.get("kp_uv_size")
    if a is None:
        return
    for i in faces:
        a.data[i].value = 0.0


# ------------------------------------------------------------------ roads

ROAD_PARTS = [
    ("road", "Road", "The driving surface"),
    ("shoulder", "Shoulders", "The strips either side"),
    ("barrier", "Barriers", "The low walls (if Barrier Height > 0)"),
    ("deck", "Underside", "The solid deck under the road (if Deck Depth > 0)"),
]
PART_SOCKETS = {
    "road": "Road Material",
    "shoulder": "Shoulder Material",
    "barrier": "Barrier Material",
    "deck": "Deck Material",
}


def road_modifier(ob):
    if ob is None or ob.type != "CURVE":
        return None
    mod = ob.modifiers.get("KP Road")
    return mod if mod is not None and mod.type == "NODES" else None


def apply_to_road(ob, mat, part, size, rot_deg, asp):
    """Put a material on part of a road. The road surface also sets the road's texture
    size (one density for the whole road; texels stay square)."""
    road.build_road_group()
    mod = road_modifier(ob)
    road.set_input(mod, PART_SOCKETS[part], mat)
    # The object's slots list exactly the road's materials (the glTF exporter reads
    # them; a stale one would also confuse the Surface button).
    used = []
    for sock in PART_SOCKETS.values():
        m = road.get_input(mod, sock)
        if m is not None and m not in used:
            used.append(m)
    ob.data.materials.clear()
    for m in used:
        ob.data.materials.append(m)
    ob.active_material_index = used.index(mat)
    if part == "road" or road.get_input(mod, "Texture Width") <= 0:
        turn = int(round(rot_deg / 90.0)) % 2 == 1
        across, along = (size * asp, size) if turn else (size, size * asp)
        road.set_input(mod, "Texture Width", across)
        road.set_input(mod, "Texture Repeat", along)
        road.set_input(mod, "Turn Texture", turn)
    ob.update_tag()


def roads(scene=None):
    scene = scene or bpy.context.scene
    return [o for o in scene.objects if road_modifier(o) is not None]


def refresh_shade_casters(scene=None):
    """
    The "KP Shade Casters" collection: what can shade a road from above (tunnel
    roofs, bridges, overhangs). Every visible mesh of the track; roads aren't included
    (a road can't shade another road yet).
    """
    from .export import role_of

    scene = scene or bpy.context.scene
    coll = bpy.data.collections.get(SHADE_COLLECTION)
    if coll is None:
        coll = bpy.data.collections.new(SHADE_COLLECTION)
        coll.use_fake_user = True  # not linked into the scene; keep it when saving
    want = {o for o in scene.objects if o.type == "MESH" and role_of(o) in ("both", "visual")}
    for o in list(coll.objects):
        if o not in want:
            coll.objects.unlink(o)
    for o in want:
        if o.name not in coll.objects:
            coll.objects.link(o)
    for o in roads(scene):
        mod = road_modifier(o)
        if road.get_input(mod, "Shade Casters") is None:
            road.set_input(mod, "Shade Casters", coll)
    return coll


# ------------------------------------------------------------------ before export


def prepare_export(scene=None):
    """Bring derived data up to date before export. Returns notes for the report."""
    scene = scene or bpy.context.scene
    notes = []
    projected = 0
    for ob in scene.objects:
        if ob.type != "MESH":
            continue
        mats = [m for m in ob.data.materials if m]
        if any(is_library(m) for m in mats) and PAINT not in ob.data.color_attributes:
            ensure_paint(ob.data)
        projected += project(ob)
    for m in bpy.data.materials:
        if is_library(m):
            sync_nodes(m)
    if roads(scene) and any(road.get_input(road_modifier(o), "Shade Strength") > 0 for o in roads(scene)):
        refresh_shade_casters(scene)
    if projected:
        notes.append(f"re-projected UVs on {projected} faces")
    return notes


def environment(scene):
    """The look.json content for the scene's environment preset."""
    look = {"schemaVersion": 1}
    t = theme(scene.kp_environment) if scene.kp_environment != "none" else None
    if t is not None:
        env = json.loads(json.dumps(t["environment"]))
        env["fog"]["enabled"] = bool(scene.kp_fog)
        look.update({"theme": t["id"], **env})
    return look
