# Builds the "Bridge Test" sample track with the Kartipelago add-on and exports it.
# SPDX-License-Identifier: MIT
#
#   blender --background --python tools/blender/build_bridge_test.py
#
# (or with the `bpy` Python module: python tools/blender/build_bridge_test.py)
#
# A banked figure-8 whose two halves cross: one passes over the other on a bridge.
# It saves tracks-src/bridge_test.blend (open it to keep editing by hand) and exports
# public/tracks/bridge_test/. Re-running it overwrites the .blend and the geometry, but
# never public/tracks/bridge_test/track.json.

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "addons"))

import bpy  # noqa: E402

import kartipelago_tools  # noqa: E402
from kartipelago_tools import export, road  # noqa: E402

A = 120.0  # half the figure-8's length, m (Blender X)
B = 80.0  # lobe height, m (Blender Y)
H = float(os.environ.get("KP_BRIDGE_HEIGHT", 8.0))  # height of the upper road where the halves cross, m
BANK = 9.0  # banking at the tightest parts, degrees
T0 = math.pi - 0.55  # start line: on the low half, just before it passes under the bridge
POINTS = 20


def path(t):
    """The figure-8 centre line (Blender coordinates) and its banking."""
    x = A * math.sin(t)
    y = (B / 2) * math.sin(2 * t)
    z = H * (1 + math.cos(t)) / 2
    # Bank into the turn: positive tilt = down to the right.
    dx, dy = A * math.cos(t), B * math.cos(2 * t)
    ddx, ddy = -A * math.sin(t), -2 * B * math.sin(2 * t)
    cross = dx * ddy - dy * ddx
    k = cross / max(1e-6, (dx * dx + dy * dy) ** 1.5)  # signed curvature, + = turning left
    tilt = -math.copysign(min(1.0, abs(k) * 60), k) * BANK
    return x, y, z, tilt


def terrain_height(x, y, near):
    """Rolling hills, flattened near the road."""
    hills = 6 * math.sin(x / 37) * math.cos(y / 29) + 4 * math.sin((x + y) / 53)
    hills = max(0.0, hills)
    fade = min(1.0, max(0.0, (near - 22) / 25))
    return -0.3 + hills * fade * fade


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    kartipelago_tools.register()
    scene = bpy.context.scene
    scene.kp_track_id = "bridge_test"
    scene.kp_track_name = "Bridge Test"
    mats = road.default_materials()

    pts = [path(T0 + i * math.tau / POINTS) for i in range(POINTS)]
    road_ob = road.make_road("Figure 8", pts, closed=True, width=12.0, barrier=1.0)
    road_ob["kp_route"] = "main"

    # Samples of the road's real centre line (the Bezier curve, as the game will see
    # it), for placing the terrain, bridge and trees. Game (x, y, z) is Blender (x, -z, y).
    samples = [(p["x"], -p["z"], p["y"], p["bank"]) for p in export.sample_route(road_ob, 1.0)["points"]]

    def near_road(x, y):
        return min(math.hypot(x - s[0], y - s[1]) for s in samples[::3])

    # Terrain: a grid, flat around the road, hills beyond.
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=96, y_subdivisions=72, size=1)
    ter = bpy.context.active_object
    ter.name = "Terrain"
    sx, sy = 2 * A + 140, B + 160
    for v in ter.data.vertices:
        x, y = v.co.x * sx, v.co.y * sy
        v.co = (x, y, terrain_height(x, y, near_road(x, y)))
    # Repeat the grass texture every 8 m.
    for loop in ter.data.uv_layers.active.data:
        loop.uv = (loop.uv.x * sx / 8, loop.uv.y * sy / 8)
    ter.data.materials.append(mats["grass"])
    ter.data.shade_flat()
    ter["kp_role"] = "both"

    # The bridge deck under the upper road, and pillars clear of the road below.
    # Stone: steep sides collide as walls, flat tops can be driven on.
    stone = road.surface_material("KP Stone", "dirt", color="#8a8278")
    deck_pts = [s for s in samples if s[2] > 1.6]
    half = 6 + 1.5 + 0.6  # road + shoulder + barrier
    verts, faces = [], []
    for i, (x, y, z, _) in enumerate(deck_pts):
        nx, ny, _, _ = deck_pts[min(i + 1, len(deck_pts) - 1)]
        px, py, _, _ = deck_pts[max(i - 1, 0)]
        dx, dy = nx - px, ny - py
        ln = math.hypot(dx, dy) or 1
        rx, ry = dy / ln, -dx / ln
        top, bot = z - 0.35, z - 1.4
        verts += [
            (x - rx * half, y - ry * half, top),
            (x + rx * half, y + ry * half, top),
            (x + rx * half, y + ry * half, bot),
            (x - rx * half, y - ry * half, bot),
        ]
        if i:
            a, b = 4 * (i - 1), 4 * i
            for k in range(4):
                faces.append((a + k, a + (k + 1) % 4, b + (k + 1) % 4, b + k))
    me = bpy.data.meshes.new("Bridge Deck")
    me.from_pydata(verts, [], faces)
    me.materials.append(stone)
    deck = bpy.data.objects.new("Bridge Deck", me)
    scene.collection.objects.link(deck)
    deck["kp_role"] = "both"

    lower = [s for s in samples if s[2] < 1.0]
    placed = []
    for i, (x, y, z, _) in enumerate(deck_pts[::6]):
        if z < 2.5:
            continue
        for side in (-1, 1):
            j = min(i * 6 + 1, len(deck_pts) - 1)
            dx, dy = deck_pts[j][0] - x, deck_pts[j][1] - y
            ln = math.hypot(dx, dy) or 1
            px, py = x + side * (dy / ln) * (half - 1), y - side * (dx / ln) * (half - 1)
            clear = min(math.hypot(px - s[0], py - s[1]) for s in lower)
            if clear < 11 or any(math.hypot(px - q[0], py - q[1]) < 8 for q in placed):
                continue
            placed.append((px, py))
            bpy.ops.mesh.primitive_cube_add(size=1, location=(px, py, (z - 1.7) / 2))
            p = bpy.context.active_object
            p.name = "Pillar"
            p.scale = (1.4, 1.4, z - 1.1)
            p.data.materials.append(stone)
            p["kp_role"] = "both"

    # Low-poly trees on the grass, well away from the road.
    leaf = road.surface_material("KP Leaves", "wall", color="#2f7d32")
    trunk = road.surface_material("KP Trunk", "wall", color="#6b4a2b")
    trees = 0
    for k in range(400):
        if trees >= 36:
            break
        x = (math.sin(k * 12.9898) * 43758.5453) % 1 * sx - sx / 2
        y = (math.sin(k * 78.233) * 12345.678) % 1 * sy - sy / 2
        if near_road(x, y) < 18:
            continue
        z = terrain_height(x, y, near_road(x, y))
        bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=3.2, depth=8, location=(x, y, z + 5.5))
        c = bpy.context.active_object
        c.name = "Tree"
        c.data.materials.append(leaf)
        c["kp_role"] = "both"
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.6, depth=2, location=(x, y, z + 1))
        t = bpy.context.active_object
        t.name = "Trunk"
        t.data.materials.append(trunk)
        t["kp_role"] = "both"
        trees += 1

    os.makedirs(os.path.join(REPO, "tracks-src"), exist_ok=True)
    blend = os.path.join(REPO, "tracks-src", "bridge_test.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    rep = export.export_track(os.path.join(REPO, "public", "tracks"), "bridge_test", "Bridge Test")
    print("EXPORTED", rep)


main()
