# Track pipeline

How tracks get from Blender into the game, and the plan for the in-game editor.

**Status: Milestone 1 done.** Blender → GLB → drive, with live reload. The sample
track is **Bridge Test**: `?track=bridge_test`.

## The three layers

```
Blender (geometry)                 Runtime (loading)                 Game (unchanged)
──────────────────                 ─────────────────                 ────────────────
Bezier road + KP Road  ──export──▶ route.json ──▶ centre-line ──────▶ checkpoints, grid,
  Geometry Nodes                                  TrackData            AI racing line,
terrain, bridges,      ──export──▶ collision.glb ▶ CollisionMesh ──▶ ground + wall queries
  props, materials                                  (grid index)       (same hitWall)
  with kp_surface      ──export──▶ visual.glb ──▶ Three.js scene
                                   track.json ──▶ metadata (ours; Blender never overwrites)
```

- **Blender** is where geometry is made: roads, terrain, bridges, tunnels, scenery. The
  add-on (`tools/blender/addons/kartipelago_tools`) adds spline roads and one-click
  export. We don't rebuild Blender's modelling tools.
- **The runtime** (`src/world/trackPackage.ts`) loads a package into the pieces the game
  already has. It doesn't depend on any editor code.
- **The browser editor** (Milestones 3–4) will load the same package and edit
  `track.json`, using the same collision and rendering as play.

## What we reuse

| Existing system                                       | How imported tracks use it                                                                                              |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `buildTrack` (centre-line samples)                    | Built from the Blender route, so everything that reads samples keeps working                                            |
| Checkpoints, laps, positions, respawn (`race.ts`)     | Unchanged. Gates gain an optional height window (`gateHeight`), so a gate on the lower road ignores karts on the bridge |
| Grid (`grid.ts`), AI racing line and driver           | Unchanged: they follow the route                                                                                        |
| Kart physics (`kart.ts`), vertical (`vertical.ts`)    | Unchanged. The ground query now takes the kart's height                                                                 |
| Walls (`hitWall`)                                     | Mesh walls feed the same function, so impacts, drift handling and wall alignment behave as tuned                        |
| Zippers, bananas, balloons (along-the-lap placements) | Work on the route today; Milestone 2 adds placed entities with ids in `track.json`                                      |
| Tuning panel, debug overlay, speedometer, racers      | Unchanged                                                                                                               |

## Files

One folder per track, served from `public/tracks/<id>/`:

| File            | Written by                | What it holds                                                               |
| --------------- | ------------------------- | --------------------------------------------------------------------------- |
| `track.json`    | us (and later the editor) | Gameplay metadata. Blender creates it once and then never touches it again. |
| `route.json`    | the Blender exporter      | The race route: points sampled from the curve marked as the route           |
| `collision.glb` | the Blender exporter      | What you drive on and hit. Materials carry `kp_surface`; no textures        |
| `visual.glb`    | the Blender exporter      | What you see                                                                |

Source `.blend` files live in `tracks-src/`. They're the real source of a track's
geometry.

### `track.json` (schema 1)

```json
{
  "schemaVersion": 1,
  "id": "bridge_test",
  "name": "Bridge Test",
  "geometry": { "visual": "visual.glb", "collision": "collision.glb", "route": "route.json" },
  "race": { "laps": 3 },
  "entities": []
}
```

Milestone 2 fills in `entities`. Each one gets a stable `id` (e.g. `"banana-7f3a"`), a
`type` (`banana`, `balloon`, `zipper`, `start`, `checkpoint`, `trigger`, `prop`), a
track-local transform (`position` in metres, `rotation` as a yaw or a quaternion) and
type-specific settings (balloon colour, zipper size, respawn time…). Planned additions:

- `start.grid`: ordered spawn transforms.
- `checkpoints`: ordered gates, with `next` lists so shortcuts and alternate routes stay
  valid.
- `surfaceOverrides`, `triggers`.
- `ai`: references to racing-line splines, kept separate from geometry.

`schemaVersion` is checked when a track loads: a newer version is refused with a
message, and older ones will be migrated in code as the schema grows.

### `route.json` (schema 1)

```json
{
  "schemaVersion": 1,
  "generator": "kartipelago_tools (Blender 5.1.2)",
  "units": "metres",
  "up": "+y",
  "routes": [
    {
      "id": "main",
      "closed": true,
      "points": [{ "x": 62.7, "y": 0.59, "z": 35.6, "width": 12, "bank": 5.2 }]
    }
  ]
}
```

Other curves marked as routes are exported too, for branches and future AI paths. Only
`main` is used today.

### Coordinates and units

- 1 Blender unit = 1 metre = 1 game unit.
- Blender is Z-up; the game, like glTF, is Y-up. A Blender point `(x, y, z)` is game
  `(x, z, −y)`. The glTF exporter and `route.json` both use this.
- Heading 0 faces +Z in the game. Seen from above in Blender, that's −Y.
- **Bank:** a positive curve Tilt tilts the road down to the right (in the direction of
  travel). That matches the game's positive `bank`, and a test checks it against the
  exported mesh.
- Object transforms are applied on export, so position and rotate freely in Blender.

## Collision

`src/world/collisionMesh.ts` turns `collision.glb` into plain triangle arrays.

- **Floors:** triangles flatter than about 57° (normal y ≥ 0.55) whose surface isn't a
  wall. A downward-facing floor (a flipped mesh) is flipped back up.
- **Walls:** steeper triangles, plus anything with the `wall` surface.
- **Index:** both sets sit in a uniform 4 m grid over x/z, so a query tests a handful of
  triangles. There's no new dependency. A BVH such as `three-mesh-bvh` (MIT) is the
  upgrade path if profiling ever asks for it; for downward rays and kart-sized circles
  the grid is enough.
- **Ground:** the ground query takes the kart's own height. It picks the highest floor at
  or just below it (up to `STEP_UP`, 0.5 m, above, so slopes at speed still climb). That's
  why bridges, tunnels and overlapping roads work, rather than the nearest x/z position.
  Normals are interpolated from the mesh's own vertex normals, so banked corners are
  smooth.
- **Walls:** the kart is a circle of `kartRadius` covering a slice from 0.25 m above its
  wheels to 1.4 m. The deepest overlapping wall triangle pushes it out through the
  existing `hitWall`. Ledges lower than 0.25 m are driven over; a wall stops a kart in
  the air until it clears the wall's top.
- **Falling:** off the geometry, below the lowest collision point minus 15 m, the kart
  goes back to the last checkpoint.

## Surfaces

Surfaces are semantic ids set on Blender materials (the `kp_surface` custom property;
the add-on's **Set Surface** button sets it). They're defined in
`assets/data/surfaces.json`:

| id        | Effect                                      |
| --------- | ------------------------------------------- |
| `asphalt` | ×1 everything: the tuned physics, unchanged |
| `dirt`    | slightly slower                             |
| `grass`   | off-road: slower, less acceleration         |
| `sand`    | much slower                                 |
| `ice`     | low grip                                    |
| `water`   | very slow                                   |
| `boost`   | driving onto it starts a zipper boost       |
| `wall`    | always collides as a wall                   |

`speed`, `accel` and `grip` multiply the kart's own top speed, acceleration and grip
while it's on the surface. That's the same mechanism the AI speed setting uses, so the
physics code itself is untouched. Colours never matter. A material with no surface, or
an unknown one, loads as asphalt and is reported (in the console and as a toast). Sound
and particle hooks will hang off the same table.

## Blender workflow

Install once (Blender 5.1 or newer recommended):

1. Edit ▸ Preferences ▸ File Paths ▸ **Script Directories**: add the repo's
   `tools/blender` folder.
2. Restart Blender, then Preferences ▸ Add-ons: enable **Kartipelago Track Tools**.
   It now updates whenever you `git pull`.

Then, in the 3D view's sidebar (N) ▸ **Kartipelago**:

- **Add Road:** a closed Bezier road with the live **KP Road** Geometry Nodes modifier.
  Edit the curve and the road follows:
  - move points and handles to shape it;
  - change point height (G Z) for hills, valleys and bridges;
  - **Ctrl+T** (Tilt) for banking;
  - **Alt+S** (Radius) to widen or narrow it.

  Modifier settings: road width, shoulder width, barrier height (0 = none), segment
  length (mesh density), across segments, texture length, and **Allow Loops**. Off keeps
  the road level (Z-up frames, no twist on hills); on uses minimum-twist frames for
  loops.

- **Set as Route:** the active curve becomes the race route. Exactly one main route.
- **Role:** Visual + Collision (default for roads), Visual only (decoration), or
  Collision only (invisible walls, simplified collision).
- **Set Surface:** tags the active material.
- **Export Track:** writes the package to **Export To**/**Track ID**/. The default is
  `//../public/tracks/`, which is right for a `.blend` saved in `tracks-src/`.

Iteration loop:

1. `npm run dev` and open `?track=<id>`.
2. Edit in Blender and press **Export Track**.
3. The game reloads the track in place within a second: no page reload, the race
   restarts on the new geometry.
4. **T** reloads by hand too, for example on a build without the dev server.

`tools/blender/build_bridge_test.py` builds the sample track from a script (run it with
`blender --background --python tools/blender/build_bridge_test.py`). It's a worked
example of making roads, terrain, a bridge deck, pillars and props in code.

## Dependencies and licences

- **Milestone 1 adds no new dependency.** Three.js's `GLTFLoader` (MIT) ships with
  `three`.
- Blender (GPL) is an authoring tool only. The add-on is our own code, MIT-licensed
  (MIT is GPL-compatible).
- The pixel textures are generated by the add-on: original, part of this project.
- Planned: a transform gizmo (`TransformControls` from `three/examples`, MIT) and
  possibly `three-mesh-bvh` (MIT).

## Milestones

1. **Geometry pipeline** ✅ Import a Blender GLB, render it, collide with it, drive it,
   and re-export it with live reload.
2. **Gameplay data:** `track.json` entities with stable ids (bananas, balloons,
   zippers, start grid, checkpoints) placed in 3D. Loading and saving keeps unknown
   fields, and placements survive geometry re-exports.
3. **Interactive editor:** editor mode (`?edit`) with free-fly and orbit cameras,
   selection, transform gizmo (move, rotate, scale, snapping to the grid and to the
   surface), palette, inspector, undo/redo, and save/load through a dev-only save
   endpoint (falling back to download/upload).
4. **Racing tools:** checkpoint gates with order and route visualisation, start-grid
   editing with clearance checks, validation, and an Edit/Play toggle that snapshots
   the level (play never alters authored data).
5. **Authoring polish:** collision, surface, radius and volume overlays, better
   snapping, shortcuts, and profiling (instancing repeated props, LODs).

## Risks

- **Blender API drift.** Geometry Nodes sockets change between versions (menu sockets,
  `Curve to Mesh` axes). The add-on targets 5.x, and the sample build script doubles as
  a smoke test.
- **Physics feel on meshes.** Triangle seams could make bumps. We use smoothed normals
  and height-based ground following. A test shows a flat mesh gives exactly the same
  driving as the old flat ground.
- **Thin walls at high speed.** The kart moves at most 0.45 m per step, under its 0.9 m
  radius, so barriers 0.3 m or thicker can't be tunnelled. Very thin collision should be
  given thickness in Blender.
- **Geometry in the road.** Anything flagged as a wall surface that pokes up through the
  road is a real wall. That's correct, but it's easy to do by accident; validation in M4
  will flag it. The AI-lap test asserts a clean line touches no walls.
- **Big binary files in git.** Each export rewrites about 3.5 MB of GLB. Fine for a few
  tracks; Git LFS later if it grows.
- **Startup is built once.** Hot reload replaces geometry, the route, the AI line and
  the race in place. Anything new that's built from the track at startup must be added
  to `reloadTrack` in `main.ts`.

## Acceptance (Milestone 1)

| Scenario                                   | How it's checked                                                                                                                                   |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| A. Drive a curved, banked Blender road     | `tests/trackPackage.test.ts`: the race AI drives a full lap through every gate. Bank sign checked against the mesh                                 |
| B. Change it in Blender and see it in game | Re-exported with the bridge at 8 m and 11 m while the game was open: it updated in place each time, with no page reload                            |
| F. Reload repeatedly without leaks         | Test: three swaps keep one track object in the scene and dispose each old one. In the browser the GPU geometry count stayed flat over four reloads |
| G. Under and over a bridge                 | Test: at the crossing the ground picks each road by height, no deck walls under the bridge, and the AI lap never changes layer                     |
| H. Physics unchanged                       | Test: drive, drift and brake on a flat mesh match the old flat ground to 9 decimal places; the existing 208 tests still pass                       |
| C, D, E                                    | Milestones 2 and 4 (placements and Edit/Play). E's checkpoint progression already works on the imported route                                      |
