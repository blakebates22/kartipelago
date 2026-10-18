# Builds the "Dino Demo" sample track with the Kartipelago add-on and exports it.
# SPDX-License-Identifier: MIT
#
#   blender --background --python tools/blender/build_dino_demo.py
#
# (or with the `bpy` Python module: python tools/blender/build_dino_demo.py)
#
# A small Ancient Lake-themed loop that shows off the material library: a curving dirt
# road, grass beside it, a layered cliff, a tunnel through a rock mesa and a lake. Every
# material comes from the Material Browser's library, every face's UVs are projected by
# the add-on, and the shading is the Vertex Paint presets, so opening the .blend shows
# exactly what a hand-made track would look like.
#
# It saves tracks-src/dino_demo.blend and exports public/tracks/dino_demo/. Re-running it
# overwrites both, but never public/tracks/dino_demo/track.json.

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "addons"))

import bpy  # noqa: E402  (first: bmesh and mathutils come with it)
import bmesh  # noqa: E402
from mathutils import Vector, kdtree  # noqa: E402

import kartipelago_tools  # noqa: E402
from kartipelago_tools import export, materials, paint, road  # noqa: E402

# The road: counter-clockwise from above, so every corner turns left (negative tilt
# banks it down to the left, into the turn).
ROAD = [
    (-100, -58, 0.0, 0),
    (-20, -72, 0.0, -2),
    (62, -64, 0.4, -3),
    (112, -26, 1.4, -3),
    (124, 26, 2.2, 0),
    (104, 78, 2.0, -3),
    (36, 94, 1.4, -2),
    (-46, 86, 1.0, -3),
    (-112, 44, 0.4, -3),
    (-130, -16, 0.0, -2),
]
MESA = Vector((126.0, 26.0))  # the rock the road tunnels through
MESA_R = 30.0
LAKE = Vector((-26.0, -150.0))
LAKE_R = 62.0
WATER_Z = -0.8
CLIFF_Y = 116.0  # the layered cliff north of the road


def rnd(k):
    return (math.sin(k * 12.9898) * 43758.5453) % 1


def lib(mat_id, surface=None):
    return materials.get_material(materials.entry(mat_id), surface)


def assign(ob, mat, faces):
    e = materials.entry(mat["kp_texture"])
    materials.assign_faces(ob, mat, faces, e["tileMetres"], 0.0, materials.aspect(e))


def mesa_ring(i, n, scale, z):
    a = i * math.tau / n
    r = MESA_R * scale * (1 + 0.12 * math.sin(3 * a + 1) + 0.06 * (rnd(i + 31 * scale) - 0.5))
    return Vector((MESA.x + r * math.cos(a), MESA.y + r * math.sin(a), z))


def build_mesa():
    """A layered rock mesa: three stacked, inset bands."""
    bm = bmesh.new()
    n = 16
    rings = [(1.0, -4.0), (1.0, 13.5), (0.88, 14.2), (0.88, 20.5), (0.76, 21.2), (0.73, 27.0)]
    verts = [[bm.verts.new(mesa_ring(i, n, s, z)) for i in range(n)] for s, z in rings]
    for lo, hi in zip(verts, verts[1:]):
        for i in range(n):
            bm.faces.new((lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i]))
    bm.faces.new(list(reversed(verts[0])))
    bm.faces.new(verts[-1])
    me = bpy.data.meshes.new("Mesa")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("Mesa", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def build_tunnel_cutter(samples):
    """The tunnel's shape swept along the road where it passes through the mesa."""
    inside = [s for s in samples if (Vector(s[:2]) - MESA).length < MESA_R + 14]
    profile = [(-10.0, -0.3), (10.0, -0.3), (10.0, 5.5), (6.5, 8.6), (-6.5, 8.6), (-10.0, 5.5)]
    bm = bmesh.new()
    rings = []
    for i, (x, y, z, _) in enumerate(inside):
        nx, ny = inside[min(i + 1, len(inside) - 1)][:2]
        px, py = inside[max(i - 1, 0)][:2]
        t = Vector((nx - px, ny - py, 0)).normalized()
        right = Vector((t.y, -t.x, 0))
        rings.append([bm.verts.new(Vector((x, y, z)) + right * a + Vector((0, 0, b))) for a, b in profile])
    m = len(profile)
    for lo, hi in zip(rings, rings[1:]):
        for k in range(m):
            bm.faces.new((lo[k], lo[(k + 1) % m], hi[(k + 1) % m], hi[k]))
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("Tunnel Cutter")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("Tunnel Cutter", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def terrain_height(x, y, near_d, near_z):
    """Gentle hills; a terraced cliff to the north; the lake bowl; flat by the road."""
    h = 1.8 * math.sin(x / 41) * math.cos(y / 33) + 1.2 * math.sin((x - y) / 57)
    edge = CLIFF_Y + 6 * math.sin(x / 23) + 3 * math.sin(x / 9)
    for step, rise in ((0.0, 9.0), (10.0, 8.0), (20.0, 7.0)):
        h += rise * min(1.0, max(0.0, (y - edge - step) / 3.0))
    d = (Vector((x, y)) - LAKE).length
    if d < LAKE_R + 20:
        bowl = -4.5 * (1 - min(1.0, d / LAKE_R) ** 2)
        k = min(1.0, max(0.0, (LAKE_R + 20 - d) / 20))
        h = h * (1 - k) + bowl * k
    if (Vector((x, y)) - MESA).length < MESA_R * 0.95:
        h = -6.0  # hidden inside the mesa (the tunnel has its own floor)
    fade = min(1.0, max(0.0, (near_d - 9.0) / 18.0))
    return (near_z - 0.45) * (1 - fade) + h * fade


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    kartipelago_tools.register()
    scene = bpy.context.scene
    scene.kp_track_id = "dino_demo"
    scene.kp_track_name = "Dino Demo"
    scene.kp_environment = "ancient_lake"
    scene.kp_fog = True

    # The road, textured from the library (ancient_road drives as road; the shoulders
    # use the grass picture but drive like dirt).
    road_ob = road.make_road("Lakeside Road", ROAD, closed=True, width=12.0, barrier=0.0)
    road_ob["kp_route"] = "main"
    e = materials.entry("ancient_road")
    materials.apply_to_road(road_ob, lib("ancient_road"), "road", e["tileMetres"], 0, materials.aspect(e))
    materials.apply_to_road(road_ob, lib("ancient_grass", "dirt"), "shoulder", 4, 0, 0.5)
    mod = road_ob.modifiers["KP Road"]
    road.set_input(mod, "Shoulder Width", 2.0)
    samples = [(p["x"], -p["z"], p["y"], p["bank"]) for p in export.sample_route(road_ob, 1.0)["points"]]
    tree = kdtree.KDTree(len(samples))
    for i, s in enumerate(samples):
        tree.insert(Vector((s[0], s[1], 0)), i)
    tree.balance()

    def near(x, y):
        _, i, d = tree.find(Vector((x, y, 0)))
        return d, samples[i][2]

    # Terrain: a grid shaped by terrain_height. Steep faces become cliff, the lake bowl
    # scree, everything else grass.
    sx, sy = 400.0, 330.0
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=140, y_subdivisions=116, size=1)
    ter = bpy.context.active_object
    ter.name = "Terrain"
    for v in ter.data.vertices:
        x, y = v.co.x * sx, v.co.y * sy - 20
        d, z = near(x, y)
        v.co = (x, y, terrain_height(x, y, d, z))
    ter.data.update()
    ter["kp_role"] = "both"
    grass, cliff, bed = [], [], []
    for p in ter.data.polygons:
        c = p.center
        if p.normal.z < 0.62:
            cliff.append(p.index)
        elif c.z < WATER_Z - 0.3 and (Vector(c[:2]) - LAKE).length < LAKE_R + 10:
            bed.append(p.index)
        else:
            grass.append(p.index)
    assign(ter, lib("ancient_grass"), grass)
    assign(ter, lib("ancient_cliff"), cliff)
    assign(ter, lib("ancient_road", "sand"), bed)
    ter.data.shade_smooth()  # Gouraud-shaded hills, like the era

    # The lake: a water surface (drives as shallow water; ripples and flows in game).
    bpy.ops.mesh.primitive_circle_add(vertices=40, radius=LAKE_R + 14, fill_type="NGON", location=(*LAKE, WATER_Z))
    water = bpy.context.active_object
    water.name = "Lake"
    water["kp_role"] = "both"
    assign(water, lib("ancient_water"), range(len(water.data.polygons)))

    # The mesa and its tunnel.
    mesa = build_mesa()
    mesa["kp_role"] = "both"
    cutter = build_tunnel_cutter(samples)
    boolean = mesa.modifiers.new("Tunnel", "BOOLEAN")
    boolean.operation = "DIFFERENCE"
    boolean.solver = "EXACT"
    boolean.object = cutter
    bpy.context.view_layer.objects.active = mesa
    bpy.ops.object.modifier_apply(modifier=boolean.name)
    bpy.data.objects.remove(cutter)
    floor, top, rock = [], [], []
    for p in mesa.data.polygons:
        if p.normal.z > 0.7 and p.center.z < 8:
            floor.append(p.index)
        elif p.normal.z > 0.7 and p.center.z > 26:
            top.append(p.index)
        else:
            rock.append(p.index)
    assign(mesa, lib("ancient_cliff"), rock)
    assign(mesa, lib("ancient_road", "dirt"), floor)  # same picture as the road, drives like dirt
    assign(mesa, lib("ancient_grass"), top)
    mesa.data.shade_flat()

    # A few low-poly trees and boulders, well clear of the road.
    leaf, trunk, boulder = lib("jungle_leafcover", "wall"), lib("ancient_road", "wall"), lib("ancient_cliff")
    placed = 0
    for k in range(600):
        if placed >= 40:
            break
        x, y = rnd(k) * sx - sx / 2, rnd(k + 0.5) * (sy - 60) - sy / 2 + 10
        d, z0 = near(x, y)
        if d < 20 or (Vector((x, y)) - LAKE).length < LAKE_R + 6 or (Vector((x, y)) - MESA).length < MESA_R + 6:
            continue
        if y > CLIFF_Y - 8:
            continue
        z = terrain_height(x, y, d, z0)
        if k % 5 == 0:
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=2.2 + rnd(k + 2) * 2, location=(x, y, z + 0.6))
            b = bpy.context.active_object
            b.name = "Boulder"
            b.scale.z = 0.7
            b["kp_role"] = "both"
            assign(b, boulder, range(len(b.data.polygons)))
            b.data.shade_flat()
        else:
            h = 7 + rnd(k + 3) * 4
            bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=3.0, depth=h, location=(x, y, z + 1.6 + h / 2))
            c = bpy.context.active_object
            c.name = "Tree"
            c["kp_role"] = "both"
            assign(c, leaf, range(len(c.data.polygons)))
            bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.55, depth=2.2, location=(x, y, z + 1.0))
            t = bpy.context.active_object
            t.name = "Trunk"
            t["kp_role"] = "both"
            assign(t, trunk, range(len(t.data.polygons)))
        placed += 1

    # Vertex paint, with the panel's presets.
    sun = paint.sun_direction(scene)
    warm = (1.0, 0.9, 0.7)

    def preset(name, obs, strength, color=warm, distance=8.0, faces=None):
        ts = [paint.Target(o, faces) for o in obs]
        paint.run(name, ts, strength, color, distance, sun)

    preset("sun", [ter, mesa], 0.35)
    preset("bottoms", [ter], 0.5, faces=cliff)
    preset("edges", [ter], 0.4, color=(0.78, 0.68, 0.5))
    preset("road_edge", [ter], 0.5, color=(1.0, 0.86, 0.55), distance=7.0)
    preset("bottoms", [mesa], 0.45)
    preset("tops", [mesa], 0.4)
    preset("cover", [mesa], 0.55)
    preset("bottoms", [o for o in scene.objects if o.name.startswith("Tree")], 0.45)
    paint.shade_roads([road_ob], 0.55)  # the road darkens inside the tunnel

    os.makedirs(os.path.join(REPO, "tracks-src"), exist_ok=True)
    blend = os.path.join(REPO, "tracks-src", "dino_demo.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    rep = export.export_track(os.path.join(REPO, "public", "tracks"), "dino_demo", "Dino Demo")
    print("EXPORTED", rep)


main()
