# Architecture

## Stack

| Area      | Choice                          | Why                                          |
| --------- | ------------------------------- | -------------------------------------------- |
| Language  | TypeScript (strict)             | Catches mistakes early in a growing codebase |
| Build     | Vite                            | Fast dev server, hot reload, static output   |
| Rendering | Three.js                        | Mature, well documented, good glTF support   |
| Debug UI  | lil-gui                         | Tiny, builds controls straight from data     |
| Tests     | Vitest                          | Shares Vite's config, fast                   |
| Hosting   | GitHub Pages via GitHub Actions | Free; every merge to `main` is playable      |

Planned later: custom arcade vehicle physics (raycasts against the track), Web Audio,
the Gamepad API, and tracks authored in Blender and exported as glTF.

## Folder map

| Folder          | Owns                                            | Added in  |
| --------------- | ----------------------------------------------- | --------- |
| `src/core/`     | Game loop, fixed timestep, tuning data, input   | M0        |
| `src/render/`   | Renderer, scene, cameras, materials             | M0        |
| `src/debug/`    | Overlay, tuning panel, later a free camera      | M0        |
| `src/physics/`  | Ground following, collision queries             | M1        |
| `src/vehicles/` | Vehicle controllers behind one shared interface | M1        |
| `src/world/`    | Loading tracks, checkpoints, triggers           | M2        |
| `src/race/`     | Laps, positions, race rules                     | M2        |
| `src/ai/`       | Racing-line following, difficulty               | M3        |
| `src/items/`    | Pickups and their effects                       | M4        |
| `src/ui/`       | Menus and HUD                                   | M6        |
| `src/audio/`    | Sound effects and music                         | as needed |

Folders are created when the milestone that needs them starts, so the tree never
contains empty placeholders.

## Key rules

### Fixed timestep

`core/loop.ts` calls `update(dt)` at a fixed rate (`tuning.loop.physicsHz`, default 120 Hz)
and `render(alpha)` once per browser frame. All gameplay state changes happen in `update`.
`render` only reads state, interpolating between the previous and current step using
`alpha` so motion looks smooth at any refresh rate.

### Data-driven tuning

Every gameplay "feel" number lives in `assets/data/tuning.json`. Code reads from the
`tuning` object exported by `core/tuning.ts`. The debug panel edits that same object live,
and edits to the file hot-reload in dev. A unit test validates the file's values.

### State separate from visuals

Simulation state (positions, velocities, lap counts) lives in plain objects. Three.js
meshes are views of that state. This makes systems testable without a browser and leaves
the door open for replays and networking later.

## Asset pipeline (planned, M2)

Tracks will be modeled in Blender and exported to `.glb`. Gameplay markers are named
empties in the scene (for example `checkpoint_01`, `item_spawn_03`, `ai_line_*`), which
`world/` reads on load. If binary assets grow large, we'll move them to Git LFS.
