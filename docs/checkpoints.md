# Checkpoints: how a lap is counted

Kartipelago counts progress the way late-90s kart racers did: with an ordered
sequence of **invisible checkpoint gates**. You can drive anywhere between them. The only
thing a lap requires is crossing the gates in order.

Leaving the road, drifting across the grass, flying, taking a wide line or a shortcut
never costs you progress or places. The code is in `src/race/checkpoints.ts`. It's
original, built from behaviour Blake described in his own words; nothing is copied.

## Why it changed

The old system put a gate every ~60 m along the centre line. Each gate only counted
within the road's width plus 2 m. Pass one even a few metres out on the grass, and it
didn't count. Because only the _next_ gate is ever checked, every gate after it was then
ignored as well. Your progress froze until you came round to that gate again. Meanwhile
your place was "gates passed plus a fraction", with the fraction capped below 1, so you
slid to last while still driving forward.

## Separate systems

| System              | Where                                      | What it decides                                                  |
| ------------------- | ------------------------------------------ | ---------------------------------------------------------------- |
| Vehicle physics     | `vehicles/kart.ts`, `physics/`             | how the kart moves (unchanged)                                   |
| Surface physics     | `surfaces.json`, collision mesh            | grip, grass, sand, mud, water (unchanged)                        |
| Checkpoint progress | `race/checkpoints.ts`                      | whether you've legally advanced                                  |
| Race position       | `race/race.ts` `standings`                 | who's ahead                                                      |
| Respawning          | `race/race.ts`, `game/hazards.ts`, session | falling off the world, deep water, lava, stuck outside the walls |

## Gates

A checkpoint is one or more gates:

- **Shape:** each gate is an upright, finite rectangle in 3D, with a bottom centre
  (`x, y, z`), a crossing direction (`heading`), a width (`left` + `right`) and a height
  (`height` above, `below` beneath).
- **Respawn spot:** each gate has one, just past it on the road by default.
- **Identity:** each gate has a stable `id`, a sequence `index` (0 = start/finish), and a
  `route` (`main`, or a shortcut's name).

**Several gates per checkpoint.** A checkpoint with several gates (the main road and a
shortcut) is passed by crossing any one of them. That's how alternate routes work today.
Branching route graphs can build on it later.

**Crossing test.** Every physics step, the kart's movement from its previous to its
current position is swept against each relevant gate's plane, in 3D:

- **Forward:** the movement goes from behind the plane to on or in front of it, and the
  crossing point is inside the rectangle. That works at boost speed, mid-air, on banks,
  and on layered tracks (a gate on a bridge ignores the road beneath it).
- **Backward:** the movement goes back through the gate by more than 1 m (the margin
  stops a wobble on the line counting).
- **Teleports:** a move of more than 8 m in one step (a respawn) is never swept, so a
  respawn can't pass a gate.

**Gate size.** Gates are wide: the road plus 18 m each side on open tracks, or 6 m between
walls. That covers wide lines and drift lines. But no gate reaches more than halfway to
another part of the course at about the same height, so it can't be crossed from the
wrong road.

## Each racer's progress

| Field           | Meaning                                                                           |
| --------------- | --------------------------------------------------------------------------------- |
| `completedLaps` | laps done                                                                         |
| `next`          | the checkpoint you must cross next                                                |
| `last`          | the checkpoint you passed last (respawns put you just past it)                    |
| `passed`        | checkpoints validated since the start (goes down if you reverse back through one) |
| `best`          | the most ever validated: laps are only awarded for _new_ progress                 |
| `activeRoute`   | `main`, or the shortcut whose gate you passed last                                |
| `lastEvent`     | accepted / rejected (and why) / reversed / lap: for the debug overlay             |

The rules:

- **Crossing the next checkpoint forward** validates it.
- **Crossing the start/finish line** completes a lap only if it's the next checkpoint
  (every other one is done) _and_ it's new progress. Reversing over the line and back
  never gives a second lap.
- **Crossing any other checkpoint** does nothing. The overlay says why: "out of order:
  cp04 first".
- **Reversing back through your last checkpoint** takes it back off you. Turn round and
  cross it again to carry on: no harm done.

Every racer, human or AI, uses the same code.

## Race positions

1. Racers who have finished keep their finishing order.
2. Everyone else ranks by `passed`, plus how far they are from their last gate's plane
   towards the next gate's plane (0–1).
3. Ties go to the lower racer number.

There's no search for the nearest bit of road, so being far off it changes nothing:
you keep what you've validated, and the fraction is measured between the gate planes.

On the grid, before anyone has crossed the line, karts rank by distance to the line
along the last 80 m of road. The HUD's place only changes once the new place has held
for a quarter of a second, so it doesn't flicker.

## Where the checkpoints come from

| Track                                            | Checkpoints                                                                       |
| ------------------------------------------------ | --------------------------------------------------------------------------------- |
| Prehistoric World (4 courses)                    | `checkpoints.json`, placed by each course script (see below), editable in Blender |
| Dino Demo                                        | `checkpoints.json` from `build_dino_demo.py`                                      |
| Drift Loop, Ribbon Ridge, Meadow Run             | `checkpoints` lists in `assets/data/track*.json` (distance along the lap)         |
| Bridge Test (and any Blender track without them) | placed automatically from the route when it loads                                 |

**Automatic placement** goes:

1. the start line;
2. just after the exit of every real turn (about 35° or more);
3. extra checkpoints wherever the gap would otherwise exceed 130 m;
4. no two closer than 45 m;
5. none inside a jump's gap or a respawn zone.

That makes roughly one checkpoint per 80–120 m: 7 to 12 per course.

The Prehistoric courses add checkpoints at their landmarks:

- **Riverbend:** after the bridge, the ridge and the ford. The village bend's checkpoint
  has a twin gate across the dirt shortcut, so either way counts.
- **Cascade:** up the viaduct, off the high bridge, out of the tunnel, just past the
  leap's landing.
- **Bonebog:** after the skeleton, the causeways and the pyramid.
- **Ember:** after the tunnel, at the summit, past the gully's landing.

A jump's checkpoint sits _past_ where a missed jump puts you, so respawning can't skip
it.

## In Blender

Open the sidebar (**N**) ▸ **Kartipelago** ▸ **Checkpoints**.

- **Generate from Route** places a set of gates along the route, using the **Margin** and
  **Height** settings. It replaces the existing main-route gates; shortcut gates stay
  paired with the nearest new one.
- **Add Checkpoint** adds a gate at the 3D cursor, facing along the route. Set **Route**
  first to make a shortcut's gate.
- **Move, rotate and resize** gates with the usual tools (G, R, S).
  - X scale is the width, Z scale the height.
  - The arrow shows the crossing direction.
  - The child arrow empty is where a respawn at that checkpoint puts you.
- **Duplicate** (Shift+D) or **delete** (X), then press **Renumber**. It numbers the main
  gates in order round the route, and keeps shortcut gates paired with theirs.
- **Next / Previous** step through the gates in order.
- **Show / Hide** toggles them. The **KP Checkpoint Order** line joins them in order.
- **The panel** shows the active gate's number, route, width, height and depth below.
- **Colours:** gold is the start line, green the main route, orange alternate routes.

**Export** writes `checkpoints.json`. Gates are never put in `visual.glb` or
`collision.glb`, so re-exporting geometry leaves them alone. They live in the `.blend`.
A scene with no gates removes a stale `checkpoints.json`, and the game places them
automatically.

```json
{
  "schemaVersion": 1,
  "checkpoints": [
    {
      "id": "cp09_village_shortcut",
      "index": 9,
      "route": "village_shortcut",
      "position": [96.1, 0.55, 120.4],
      "heading": 1.98,
      "width": 26,
      "height": 6,
      "below": 3,
      "respawn": { "position": [99.8, 0.6, 118.9], "heading": 1.98 }
    }
  ]
}
```

These are game coordinates: y is up, and a heading of 0 faces +z. A shortcut gate whose
number has no main gate is skipped, with a warning.

## Debugging

In a race with `?debug`, press **`** (backquote) for the overlay, and **G** to see the
gates.

The overlay shows:

- `race`: lap, laps done, place, and active route;
- `cp`: the next and last checkpoint, and passed (best) out of the checkpoints per lap;
- `seg`: progress towards the next gate;
- `cross`: the latest crossing (accepted, rejected and why, reversed, or lap).

The gates are drawn translucent, with outlines and direction arrows:

- **green:** the next one you must cross;
- **blue:** the one you passed last;
- **orange:** alternate routes;
- **white:** the rest.

## Tests

`tests/checkpoints.test.ts` covers scenarios A–N on Riverbend Palms (and the Bridge Test
reference copy for layering):

- **A** a normal lap;
- **B** the grass between gates;
- **C** a very wide line;
- **D** flying through a gate, and over one;
- **E** a skipped gate (no lap);
- **F** reversing over the line (no extra lap);
- **G** reversing, then recovering;
- **H** far from the road;
- **I** a wide line ranked by real progress;
- **J** boost-speed steps;
- **K** layered gates;
- **L** a respawn can't skip gates;
- **M** three laps;
- **N** restart.

They also cover wobbling on a gate, the shortcut gate, and an AI lap. The four courses'
three-lap AI tests run on these checkpoints too.
