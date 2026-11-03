# Roads crossing roads (Blake, review-desert_region 2, notes 6, 7, 13: "these dark lines
# shouldnt intersect the path coming from the portal"; "we want the dark lines on the
# outside of the road to not interfere"): where one road's shoulder strip runs across
# another road's paving, at a junction or a crossing, that bit of shoulder goes, so each
# road's dark edges stay on its outsides.
# SPDX-License-Identifier: MIT
#
# Called last, just before the course is finished: the roads named (side roads, and the
# lap's pieces near them) are made meshes (their road modifiers evaluated, as the export
# would) with those shoulder faces cut out.

import math

import bpy
import bmesh
from mathutils import Vector, kdtree

from kartipelago_tools import export


def _samples(ob, width):
    return [(p["x"], -p["z"], p.get("width", width) / 2.0) for p in export.sample_route(ob, 1.0)["points"]]


def clip_shoulders(c, side_roads, near=30.0, inset=0.3):
    """side_roads: [(object name, its width)]. Cuts out every flat non-road face (a
    shoulder) of those roads, and of the lap's pieces near them, whose middle lies on
    another of the roads' paving (its half width less `inset`). Returns how many faces."""
    roads = []
    for name, width in side_roads:
        ob = bpy.data.objects.get(name)
        if ob is not None:
            roads.append((ob, _samples(ob, width)))
    lap = [(q.p.x, q.p.y, q.w / 2.0) for q in c.S]
    side_pts = [p for _, ss in roads for p in ss]
    pieces = []
    tree = kdtree.KDTree(len(side_pts))
    for i, (x, y, _) in enumerate(side_pts):
        tree.insert((x, y, 0.0), i)
    tree.balance()
    for ob in getattr(c, "pieces", []):
        bb = [ob.matrix_world @ Vector(v) for v in ob.bound_box]
        cx, cy = sum(v.x for v in bb) / 8, sum(v.y for v in bb) / 8
        rad = max(math.hypot(v.x - cx, v.y - cy) for v in bb)
        if side_pts and tree.find((cx, cy, 0.0))[2] < rad + near:
            pieces.append(ob)
    targets = [(ob, ss, False) for ob, ss in roads] + [(ob, None, True) for ob in pieces]
    dg = bpy.context.evaluated_depsgraph_get()
    cut = 0
    for ob, own, is_lap in targets:
        others = list(side_pts) if is_lap else lap + [p for o2, ss in roads if o2 is not ob for p in ss]
        if not others:
            continue
        ot = kdtree.KDTree(len(others))
        for i, (x, y, _) in enumerate(others):
            ot.insert((x, y, 0.0), i)
        ot.balance()
        reach = max(hw for _, _, hw in others)
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
        bm = bmesh.new()
        bm.from_mesh(me)
        mw = ob.matrix_world
        dead = []
        for f in bm.faces:
            if f.normal.z < 0.5 or f.material_index >= len(me.materials):
                continue
            mat = me.materials[f.material_index]
            if mat is None or mat.get("kp_surface") in ("road", "boost", "wall"):
                continue
            p = mw @ f.calc_center_median()
            for _co, i, d in ot.find_range((p.x, p.y, 0.0), reach):
                if d < others[i][2] - inset:
                    dead.append(f)
                    break
        if not dead:
            bm.free()
            bpy.data.meshes.remove(me)
            continue
        bmesh.ops.delete(bm, geom=dead, context="FACES")
        bm.to_mesh(me)
        bm.free()
        uv = me.uv_layers.get("UVMap")
        if uv is not None:
            me.uv_layers.active = uv
            uv.active_render = True
        name = ob.name
        ob.name = name + " (curve)"
        copy = bpy.data.objects.new(name, me)
        copy.matrix_world = ob.matrix_world
        for k in ob.keys():
            copy[k] = ob[k]
        for coll in list(ob.users_collection):
            coll.objects.link(copy)
            coll.objects.unlink(ob)
        cut += len(dead)
    print("road shoulders clipped: %d faces" % cut)
    return cut
