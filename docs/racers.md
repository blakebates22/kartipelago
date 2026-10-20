# Racers

The launch roster is four dinosaur racers, built from Blake's finalized concept designs:

| Racer  | Species         | Design            | Seen from behind                                  | Kart                                                          |
| ------ | --------------- | ----------------- | ------------------------------------------------- | ------------------------------------------------------------- |
| Tiko   | parasaurolophus | Tropical Explorer | the big gold-to-orange crest, backpack and tail   | rounded turquoise explorer, ivory nose, palm emblem, leaves   |
| Brakka | triceratops     | Rocky Roader      | a broad frill covered in rocky plates             | sandstone and timber roader, stone fenders, footprint emblem  |
| Pebble | ankylosaurus    | Shoreline Roller  | an armoured dome with ivory spikes, the tail club | low cream-and-blue roller, big turquoise spiral, wooden trim  |
| Zephyr | pteranodon      | Sky Scout         | a swept crest, goggles and folded orange wings    | red aviation racer, pointed nose, wing emblem, rounded engine |

Tiko is the mascot (the default racer). Pick a racer on **Select Racer** (or with
`?racer=tiko`, `brakka`, `pebble`, `zephyr`). Rivals take the other looks in turn;
repeats get each racer's alternate colours.

**Looks never change how a kart drives.** Every racer is the same kart underneath: the
same physics, collision circle and handling. Driving stats are still chosen separately
(the 1-4 keys, `characters.json`), and the Select Racer screen shows no stat bars,
because the looks don't have any.

## What each racer does

Everything is visual. The animator reads the kart's physics state and adds motion
through child transforms. Nothing writes back to the physics.

The states, read from the kart every frame:

`IDLE`, `ACCELERATING`, `BRAKING`, `STEERING_LEFT`, `STEERING_RIGHT`, `DRIFTING_LEFT`,
`DRIFTING_RIGHT`, `BOOSTING`, `AIRBORNE`, `LANDING`, `COLLISION`, `VICTORY` and `DEFEAT`
(the last two once the racer has crossed the finish line: the top three celebrate).

Each state sets targets for a handful of pose channels (lean, pitch, head turn, jaw, lids,
brows, wings, hands), and every channel eases toward its target, so nothing ever snaps.
On top: blinks, glances at nearby rivals, curious head tilts, the seat bob, squash and
stretch on jumps and landings, a kick back into the seat on boosts, and the little
extras (crests lag, scarves flutter, packs bounce).

Personality changes the timing and the style:

| Racer  | Drives like                                                           | Celebrates               |
| ------ | --------------------------------------------------------------------- | ------------------------ |
| Tiko   | eager: leans hard, saws at the wheel, curious head tilts, looks about | both arms up, happy eyes |
| Brakka | determined: heavy brow, strong lean, shakes his head after a crash    | a proud fist and nods    |
| Pebble | calm: slow blinks, gentle steering, a big surprised face on a boost   | a friendly wave          |
| Zephyr | daring: quick head turns, wings out in the air, wings up to boost     | flaps his wings          |

## The character viewer

`garage.html` (the "Racer preview" link with `?debug`) shows the racers away from the
race:

- **views:** front, side, rear, three-quarter, the race camera, far away, face;
- **turnaround:** front, three-quarter, side and rear side by side;
- **all racers:** the four lined up;
- **animation:** put a racer in any state (drifting, boosting, airborne, victory...);
- **alternate colours**, a turntable, the render scale (try 0.4 for N64 resolution);
- **save sheet:** downloads a PNG of front, side, rear, three-quarter and race-camera
  views.

URL options, for screenshots: `garage.html?racer=pebble&view=rear&state=DRIFTING_LEFT`,
plus `&turnaround`, `&lineup`, `&alt`, `&scale=1`.

## How they're built

See [racer-pipeline.md](racer-pipeline.md) for changing a racer or adding a new one.

In short: each racer is one file in `src/render/racers/roster/`, built from a shared kit
(`kit/`): low-poly lofted shapes, small painted textures, the shared kart chassis, a
shared rider rig, and the shared animator.

Budgets (checked by `tests/racers.test.ts`): 3,000-12,000 triangles up close (kart and
rider together; the four come to about 7,500-8,500 each), under 3,000 far away (beyond
45 m), and about 30-35 draw calls each up close.
