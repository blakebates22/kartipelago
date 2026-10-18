# Kartipelago Track Tools: spline roads.
# SPDX-License-Identifier: MIT
"""
A road is an ordinary Bezier curve with the "KP Road" Geometry Nodes modifier. The
modifier sweeps a cross-section along the curve, live, so you shape the road just by
editing the curve:

- move control points and handles: the road follows;
- per-point Tilt (Ctrl+T in edit mode): banking (positive tilts the road down to the right);
- per-point Radius (Alt+S): scales the whole cross-section (wider or narrower road);
- control point height (Z): hills, valleys, bridges.

The cross-section is the road surface, a shoulder either side and optional barriers,
each with its own material. Materials carry a `kp_surface` custom property (asphalt,
dirt, wall...) that the game uses for physics; colours never affect gameplay.
"""

import math

import bpy

GROUP_NAME = "KP Road"
GROUP_VERSION = 3

# Semantic surface ids, matching assets/data/surfaces.json in the game.
SURFACES = [
    ("asphalt", "Asphalt", "Driveable road"),
    ("dirt", "Dirt", "Driveable, a little slower"),
    ("grass", "Grass", "Off-road: slower"),
    ("sand", "Sand", "Off-road: much slower"),
    ("ice", "Ice", "Slippery"),
    ("water", "Water", "Shallow water: very slow"),
    ("boost", "Boost", "Driving onto it gives a boost"),
    ("wall", "Wall", "Solid: always collides as a wall"),
]


# ------------------------------------------------------------------ pixel textures


def _rng(seed):
    state = [seed & 0xFFFFFFFF]

    def rand():
        state[0] = (state[0] * 1664525 + 1013904223) & 0xFFFFFFFF
        return state[0] / 4294967296.0

    return rand


def _pixel_image(name, w, h, paint):
    """A small packed image painted pixel by pixel: paint(x, y, rand) -> (r, g, b)."""
    img = bpy.data.images.get(name)
    if img is None:
        img = bpy.data.images.new(name, w, h, alpha=False)
    rand = _rng(len(name) * 7919)
    px = []
    for y in range(h):
        for x in range(w):
            r, g, b = paint(x, y, rand)
            px += [r, g, b, 1.0]
    img.pixels = px
    img.pack()
    return img


def _hex(h):
    h = h.lstrip("#")
    # sRGB to linear: Blender image pixels are linear for non-colour-managed math,
    # but these images are sRGB, so store sRGB values directly.
    return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))


def _shade(c, k):
    return tuple(max(0.0, min(1.0, v * k)) for v in c)


def _asphalt(x, y, rand):
    # 32 across x 32 along: white edge lines, a dashed centre line, pixel grain.
    base = _hex("#5d5f66")
    if x in (1, 2) or x in (29, 30):
        return _hex("#f2f2ee")
    if x in (15, 16) and y < 16:
        return _hex("#f2d24a")
    return _shade(base, 0.9 + rand() * 0.2)


def _dirt(x, y, rand):
    return _shade(_hex("#b58552"), 0.85 + rand() * 0.3)


def _grass(x, y, rand):
    c = _hex("#5fa84a") if rand() > 0.12 else _hex("#4c9440")
    return _shade(c, 0.92 + rand() * 0.16)


def _barrier(x, y, rand):
    # Red and white blocks.
    return _hex("#e6e2da") if (x // 8 + y // 8) % 2 else _hex("#d8443a")


def _rock(x, y, rand):
    return _shade(_hex("#8a7f72"), 0.85 + rand() * 0.3)


TEXTURES = {
    "asphalt": (_asphalt, 32, 32),
    "dirt": (_dirt, 16, 16),
    "grass": (_grass, 16, 16),
    "wall": (_barrier, 16, 16),
    "rock": (_rock, 16, 16),
}


def surface_material(name, surface, texture=None, color=None):
    """A material tagged with a semantic surface, with an optional pixel texture."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat["kp_surface"] = surface
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        nt.links.new(bsdf.outputs[0], out.inputs[0])
    bsdf.inputs["Roughness"].default_value = 1.0
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.0
    if texture:
        paint, w, h = TEXTURES[texture]
        img = _pixel_image(f"KP {texture}", w, h, paint)
        tex = next((n for n in nt.nodes if n.type == "TEX_IMAGE"), None) or nt.nodes.new(
            "ShaderNodeTexImage"
        )
        tex.image = img
        tex.interpolation = "Closest"  # crisp pixels in game (glTF NEAREST)
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    elif color:
        bsdf.inputs["Base Color"].default_value = (*_hex(color), 1.0)
    return mat


def default_materials():
    return {
        "road": surface_material("KP Asphalt", "asphalt", "asphalt"),
        "shoulder": surface_material("KP Dirt", "dirt", "dirt"),
        "barrier": surface_material("KP Barrier", "wall", "wall"),
        "grass": surface_material("KP Grass", "grass", "grass"),
        "rock": surface_material("KP Rock", "wall", "rock"),
    }


# ------------------------------------------------------------------ the node group


def _socket(ng, name, kind, default=None, lo=None, hi=None, desc=""):
    s = ng.interface.new_socket(name, in_out="INPUT", socket_type=kind)
    if default is not None:
        s.default_value = default
    if lo is not None:
        s.min_value = lo
    if hi is not None:
        s.max_value = hi
    s.description = desc
    return s


def _math(ng, op, a, b=None):
    n = ng.nodes.new("ShaderNodeMath")
    n.operation = op
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            ng.links.new(v, n.inputs[i])
    return n.outputs[0]


def build_road_group():
    """Create (or rebuild) the "KP Road" Geometry Nodes group."""
    old = bpy.data.node_groups.get(GROUP_NAME)
    if old is not None and old.get("kp_version") == GROUP_VERSION:
        return old
    ng = old or bpy.data.node_groups.new(GROUP_NAME, "GeometryNodeTree")
    ng.nodes.clear()
    ng.interface.clear()
    ng["kp_version"] = GROUP_VERSION
    ng.interface.new_socket("Curve", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Road", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    _socket(ng, "Road Width", "NodeSocketFloat", 12.0, 2.0, 80.0, "Width of the road surface, m")
    _socket(ng, "Shoulder Width", "NodeSocketFloat", 1.5, 0.0, 20.0, "Shoulder each side, m")
    _socket(ng, "Barrier Height", "NodeSocketFloat", 1.0, 0.0, 10.0, "0 = no barriers, m")
    _socket(ng, "Barrier Thickness", "NodeSocketFloat", 0.6, 0.1, 5.0, "m")
    _socket(ng, "Segment Length", "NodeSocketFloat", 1.5, 0.25, 10.0, "Mesh density along the road, m")
    _socket(ng, "Across Segments", "NodeSocketInt", 4, 1, 32, "Mesh density across the road")
    _socket(ng, "Texture Repeat", "NodeSocketFloat", 8.0, 1.0, 100.0, "Road texture length, m")
    _socket(
        ng,
        "Allow Loops",
        "NodeSocketBool",
        False,
        desc="Minimum-twist frames (for loops). Off = road stays level (Z up) plus Tilt",
    )
    _socket(ng, "Road Material", "NodeSocketMaterial")
    _socket(ng, "Shoulder Material", "NodeSocketMaterial")
    _socket(ng, "Barrier Material", "NodeSocketMaterial")

    N = ng.nodes
    L = ng.links
    gi = N.new("NodeGroupInput")
    go = N.new("NodeGroupOutput")
    I = gi.outputs  # noqa: E741

    # Even spacing along the curve, then a stable frame: Z up (no twist on hills) or
    # minimum twist (for loops); the per-point Tilt banks it either way.
    res = N.new("GeometryNodeResampleCurve")
    res.inputs["Mode"].default_value = "Length"
    L.new(I["Curve"], res.inputs["Curve"])
    L.new(I["Segment Length"], res.inputs["Length"])
    zup = N.new("GeometryNodeSetCurveNormal")
    zup.inputs["Mode"].default_value = "Z Up"
    twist = N.new("GeometryNodeSetCurveNormal")
    twist.inputs["Mode"].default_value = "Minimum Twist"
    L.new(res.outputs[0], zup.inputs["Curve"])
    L.new(res.outputs[0], twist.inputs["Curve"])
    sw = N.new("GeometryNodeSwitch")
    sw.input_type = "GEOMETRY"
    L.new(I["Allow Loops"], sw.inputs["Switch"])
    L.new(zup.outputs[0], sw.inputs["False"])
    L.new(twist.outputs[0], sw.inputs["True"])

    # Distance along the curve, kept for the road texture's V coordinate.
    sp = N.new("GeometryNodeSplineParameter")
    store_v = N.new("GeometryNodeStoreNamedAttribute")
    store_v.data_type = "FLOAT"
    store_v.domain = "POINT"
    store_v.inputs["Name"].default_value = "kp_v"
    L.new(sw.outputs[0], store_v.inputs["Geometry"])
    L.new(sp.outputs["Length"], store_v.inputs["Value"])
    path = store_v.outputs[0]

    half = _math(ng, "MULTIPLY", I["Road Width"], 0.5)
    neg_half = _math(ng, "MULTIPLY", I["Road Width"], -0.5)
    edge = _math(ng, "ADD", half, I["Shoulder Width"])
    neg_edge = _math(ng, "MULTIPLY", edge, -1.0)

    def line(x0, x1, y0=0.0, y1=0.0, count=None):
        """
        A profile line across the road, given as (across, up). Curve to Mesh maps a
        profile's X to the right of the curve and its Y to *down*, so Y is negated.
        """
        n = N.new("GeometryNodeCurvePrimitiveLine")
        for sock, xv, yv in ((n.inputs["Start"], x0, -y0), (n.inputs["End"], x1, -y1)):
            c = N.new("ShaderNodeCombineXYZ")
            for axis, v in (("X", xv), ("Y", yv)):
                if isinstance(v, (int, float)):
                    c.inputs[axis].default_value = v
                else:
                    L.new(v, c.inputs[axis])
            L.new(c.outputs[0], sock)
        out = n.outputs[0]
        if count is not None:
            r = N.new("GeometryNodeResampleCurve")
            r.inputs["Mode"].default_value = "Count"
            L.new(out, r.inputs["Curve"])
            L.new(count, r.inputs["Count"])
            out = r.outputs[0]
        return out

    def sweep(profile, material, smooth):
        # Keep each profile point's 0..1 position round the profile, for the texture's U.
        store_u = N.new("GeometryNodeStoreNamedAttribute")
        store_u.data_type = "FLOAT"
        store_u.domain = "POINT"
        store_u.inputs["Name"].default_value = "kp_u"
        L.new(profile, store_u.inputs["Geometry"])
        L.new(N.new("GeometryNodeSplineParameter").outputs["Factor"], store_u.inputs["Value"])
        c2m = N.new("GeometryNodeCurveToMesh")
        L.new(path, c2m.inputs["Curve"])
        L.new(store_u.outputs[0], c2m.inputs["Profile Curve"])
        # Point Radius scales the cross-section.
        L.new(N.new("GeometryNodeInputRadius").outputs[0], c2m.inputs["Scale"])
        mat = N.new("GeometryNodeSetMaterial")
        L.new(c2m.outputs[0], mat.inputs["Geometry"])
        L.new(material, mat.inputs["Material"])
        sm = N.new("GeometryNodeSetShadeSmooth")
        sm.inputs["Shade Smooth"].default_value = smooth
        L.new(mat.outputs[0], sm.inputs["Mesh"])
        return sm.outputs[0]

    # Road surface.
    across_count = _math(ng, "ADD", I["Across Segments"], 1)
    road = sweep(line(neg_half, half, count=across_count), I["Road Material"], True)

    # Shoulders, dipping slightly at the outside edge.
    shoulder_l = sweep(line(neg_edge, neg_half, -0.06, 0.0), I["Shoulder Material"], True)
    shoulder_r = sweep(line(half, edge, 0.0, -0.06), I["Shoulder Material"], True)

    # Barriers: a rectangle profile just outside each shoulder.
    def barrier(side):
        q = N.new("GeometryNodeCurvePrimitiveQuadrilateral")
        q.mode = "RECTANGLE"
        L.new(I["Barrier Thickness"], q.inputs["Width"])
        L.new(I["Barrier Height"], q.inputs["Height"])
        t = N.new("GeometryNodeTransform")
        L.new(q.outputs[0], t.inputs["Geometry"])
        off = _math(ng, "ADD", edge, _math(ng, "MULTIPLY", I["Barrier Thickness"], 0.5))
        c = N.new("ShaderNodeCombineXYZ")
        L.new(_math(ng, "MULTIPLY", off, side), c.inputs["X"])
        # Profile Y points down: centre the barrier H/2 - 0.1 above the road.
        L.new(_math(ng, "SUBTRACT", 0.1, _math(ng, "MULTIPLY", I["Barrier Height"], 0.5)), c.inputs["Y"])
        L.new(c.outputs[0], t.inputs["Translation"])
        return sweep(t.outputs[0], I["Barrier Material"], False)

    barriers = N.new("GeometryNodeJoinGeometry")
    L.new(barrier(1), barriers.inputs[0])
    L.new(barrier(-1), barriers.inputs[0])
    has_barrier = _math(ng, "GREATER_THAN", I["Barrier Height"], 0.001)
    bsw = N.new("GeometryNodeSwitch")
    bsw.input_type = "GEOMETRY"
    L.new(has_barrier, bsw.inputs["Switch"])
    L.new(barriers.outputs[0], bsw.inputs["True"])

    join = N.new("GeometryNodeJoinGeometry")
    for g in (road, shoulder_l, shoulder_r, bsw.outputs[0]):
        L.new(g, join.inputs[0])

    # UVs: U across, V along. On a closed road the last ring of faces wraps from the end
    # of the curve back to 0; add one curve length there so the texture doesn't squash,
    # and fit a whole number of texture repeats so the join is seamless.
    nv = N.new("GeometryNodeInputNamedAttribute")
    nv.data_type = "FLOAT"
    nv.inputs["Name"].default_value = "kp_v"
    nu = N.new("GeometryNodeInputNamedAttribute")
    nu.data_type = "FLOAT"
    nu.inputs["Name"].default_value = "kp_u"
    face_mean = N.new("GeometryNodeFieldOnDomain")
    face_mean.domain = "FACE"
    face_mean.data_type = "FLOAT"
    L.new(nv.outputs["Attribute"], face_mean.inputs[0])
    clen = N.new("GeometryNodeCurveLength")
    L.new(path, clen.inputs[0])
    length = clen.outputs[0]
    quarter = _math(ng, "MULTIPLY", length, 0.25)
    threshold = _math(ng, "SUBTRACT", face_mean.outputs[0], quarter)
    wraps = _math(ng, "LESS_THAN", nv.outputs["Attribute"], threshold)
    v = _math(ng, "ADD", nv.outputs["Attribute"], _math(ng, "MULTIPLY", wraps, length))
    repeats = _math(ng, "MAXIMUM", _math(ng, "ROUND", _math(ng, "DIVIDE", length, I["Texture Repeat"])), 1)
    v_tex = _math(ng, "DIVIDE", _math(ng, "MULTIPLY", v, repeats), length)
    uv = N.new("ShaderNodeCombineXYZ")
    L.new(nu.outputs["Attribute"], uv.inputs["X"])
    L.new(v_tex, uv.inputs["Y"])
    store_uv = N.new("GeometryNodeStoreNamedAttribute")
    store_uv.data_type = "FLOAT2"
    store_uv.domain = "CORNER"
    store_uv.inputs["Name"].default_value = "UVMap"
    L.new(join.outputs[0], store_uv.inputs["Geometry"])
    L.new(uv.outputs[0], store_uv.inputs["Value"])

    # The helper attributes aren't needed in the exported mesh.
    rm = N.new("GeometryNodeRemoveAttribute")
    rm.inputs["Name"].default_value = "kp_v"
    L.new(store_uv.outputs[0], rm.inputs["Geometry"])
    rm2 = N.new("GeometryNodeRemoveAttribute")
    rm2.inputs["Name"].default_value = "kp_u"
    L.new(rm.outputs[0], rm2.inputs["Geometry"])
    L.new(rm2.outputs[0], go.inputs["Road"])

    # Tidy layout (purely cosmetic in the node editor).
    for i, n in enumerate(N):
        n.location = ((i % 8) * 220, -(i // 8) * 220)
    return ng


def make_road(name, points, closed=True, width=12.0, barrier=1.0, collection=None):
    """
    A road from a list of (x, y, z, tilt_degrees[, radius]) control points, with smooth
    auto handles. Returns the curve object (with the KP Road modifier).
    """
    cd = bpy.data.curves.new(name, "CURVE")
    cd.dimensions = "3D"
    cd.twist_mode = "Z_UP"
    sp = cd.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp, p in zip(sp.bezier_points, points):
        bp.co = p[:3]
        bp.handle_left_type = bp.handle_right_type = "AUTO"
        bp.tilt = math.radians(p[3] if len(p) > 3 else 0.0)
        bp.radius = p[4] if len(p) > 4 else 1.0
    sp.use_cyclic_u = closed
    sp.resolution_u = 24
    ob = bpy.data.objects.new(name, cd)
    (collection or bpy.context.scene.collection).objects.link(ob)
    attach_road(ob, width=width, barrier=barrier)
    return ob


def attach_road(ob, width=12.0, barrier=1.0):
    """Give a curve object the KP Road modifier and make it the route if none is set."""
    mats = default_materials()
    mod = ob.modifiers.get("KP Road") or ob.modifiers.new("KP Road", "NODES")
    mod.node_group = build_road_group()
    ids = {item.name: item.identifier for item in mod.node_group.interface.items_tree if item.item_type == "SOCKET"}
    mod[ids["Road Width"]] = width
    mod[ids["Barrier Height"]] = barrier
    mod[ids["Road Material"]] = mats["road"]
    mod[ids["Shoulder Material"]] = mats["shoulder"]
    mod[ids["Barrier Material"]] = mats["barrier"]
    # The exporter takes materials from the object's slots, so list them there too.
    if ob.type == "CURVE":
        for m in (mats["road"], mats["shoulder"], mats["barrier"]):
            if m.name not in ob.data.materials:
                ob.data.materials.append(m)
    ob["kp_role"] = "both"
    if not any(o.get("kp_route") for o in bpy.data.objects):
        ob["kp_route"] = True
    return mod


def road_settings(ob):
    """The road modifier's width and shoulder for an object, if it has one."""
    mod = ob.modifiers.get("KP Road")
    if mod is None or mod.node_group is None:
        return None
    ids = {item.name: item.identifier for item in mod.node_group.interface.items_tree if item.item_type == "SOCKET"}
    return {"width": float(mod[ids["Road Width"]]), "shoulder": float(mod[ids["Shoulder Width"]])}
