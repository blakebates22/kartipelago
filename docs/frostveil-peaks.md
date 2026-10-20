# Frostveil Peaks

A prehistoric winter world: snowbound mountains where an ancient civilization built
temples, bridges and fortresses into the peaks. Its first course is **Frostveil
Citadel**; three more are planned and show in track select as locked "Coming Soon"
tiles (`comingSoon` in `src/game/worlds.ts`: rename them there when they have names).

## Frostveil Citadel

A journey of about 2.2 km a lap (an AI lap is about 95 s) through a lost mountain
citadel, under moonlight, by firelight. The course climbs 58 m and comes back down.

| Section | Name                         | What happens                                                                                                                                                         |
| ------- | ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A       | The Forgotten Entrance       | The start, on the valley floor beside a fog-filled chasm. Through the Great Gate (an arch between two giant carved dinosaur heads), under the Bridge of Giants.      |
| B       | The Frozen Causeway          | Sweeping switchbacks up the east hillside (0 to 31 m), carved pillars on the guardrail, braziers. The first zipper.                                                  |
| C       | The Bridge of Giants         | 230 m of arched stone, 32 m over the start straight and then 130 m over the chasm. Stepped piers with creature faces, banners, braziers, a zipper on the approach.   |
| D       | The Serpent Gate             | The bridge aims straight into the open mouth of a giant serpent carved into the cliff. A torchlit tunnel climbs inside the mountain (32 to 53 m), with an icy patch. |
| E       | The Moonlit Temple           | Out into a courtyard before the stepped temple on its terrace, a broad sweep round the golden sun disk, statues and pillars. A zipper on the exit.                   |
| F       | The High Labyrinth           | Walled lanes and arches, watchtowers, then a high causeway east over the north gorge, looking down on the valley.                                                    |
| G       | The Frozen Waterfall Descent | Down the east mountainside (58 to 10 m), frozen falls on the cliffs above, a jump over a frozen gorge (miss it and you're put down on the landing).                  |
| H       | The Lower Ruins              | West through the lower town (firelit houses, rubble, a ruined arch) and round onto the start.                                                                        |

**The reveals:** from the start line the Great Keep glows high on the mountain straight
ahead; the bridge appears as you round the last switchback; the bridge aims at the
serpent's glowing eyes; the tunnel opens onto the courtyard with the temple ahead; and
from the causeway and the descent you look back down on the bridge, the gate and the
start.

**Surfaces** (`assets/data/surfaces.json`; how they drive is separate from how they look):

| Surface       | Drives like                                                          | Where                                    |
| ------------- | -------------------------------------------------------------------- | ---------------------------------------- |
| `snow_stone`  | road, a touch less grip                                              | most of the road                         |
| `icy_stone`   | road, much less grip                                                 | a patch in the tunnel, the gorge bridges |
| `packed_snow` | road, a little slower and looser                                     | the shoulders, the lower town            |
| `deep_snow`   | off-road: slow                                                       | the snowfields                           |
| `abyss`       | puts you back on the road (the respawn zone, or the last checkpoint) | the floors of the chasm and gorges       |

**Lighting and atmosphere:**

- The **Frost Citadel** theme: moonlight (a blue-lavender light and sky, a moon, clouds,
  rings of far peaks) and lavender distance fog that starts 150 m out.
- Firelight: every brazier and torch is a glowing flame, and warm light is painted onto
  the land and the stone round each one (with a cold blue tint everywhere else). The
  four torches nearest you also light the road and the karts with a real flicker
  (`torch` entities, as on Cascade Caverns).
- Glowing doorways and windows cut into the cliffs, the temple and the keep.
- Layered see-through fog sheets fill the chasm and the gorges.
- Spray at every waterfall, and light snow falling round the camera (the `snowfall`
  entity: `{ "type": "snowfall", "rate": 110, "radius": 40 }`).

**Music:** "Frostveil Citadel" (`frostveil` in `src/audio/songs.ts`), E minor, 138 BPM:
celesta and bells in the moonlit first half, then a wooden flute and warm horns, over
plucked strings, a bright marimba, deep toms and a driving bass.

## How it's built

Everything is in `tools/blender/prehistoric/`, on the same course kit as the Prehistoric
World (no Blender needed at runtime):

- `frostveil_citadel.py`: the layout (turtle segments, closed by stretching the last
  two straights so the early sections never move), the heights along the lap, the land
  (valley, chasm, gorges, the temple plateau, terraced mountains with jagged summits),
  the road kinds, the tunnel, the gameplay (zippers, eggs, balloons, the jump's catch,
  17-26 tall checkpoint gates) and the hidden floors.
- `frostveil_scenery.py`: the Great Gate, the bridge piers and arches, the Serpent Gate
  and its halls, the courtyard, temple and sun disk, the labyrinth, the cliff dwellings,
  the Great Keep, the fortress towers, waterfalls (flowing and frozen), fog, trees, and
  the baked firelight. Copies are joined per map square at the end (fewer draw calls).
- `winter_props.py`: the winter-ruin kit (braziers, banners, carved pillars, guard
  blocks, rubble, towers, houses, arches, dinosaur heads, statues, the sun disk, the
  temple, snowy palms, conifers, shrubs, drifts, icicles, frozen falls). Each prop is one
  shared mesh, placed as copies.

Run `python tools/blender/prehistoric/frostveil_citadel.py` (with the bpy module) to
rebuild `tracks-src/frostveil_citadel.blend` and `public/tracks/frostveil_citadel/`.
Roads stay editable curves in the .blend; collision is separate (`Collision`
collection); track.json's gameplay is rewritten by the script.

**No holes:** two hidden floors sit under everything a kart could reach (within 80 m of
the road): one just under the land (flat squares, so even under a cliff there's floor),
and the `abyss` floor under the chasm and gorges. `tests/holes.test.ts` walks every
reachable floor from the road and fails on any hole.

**Tests:** `tests/frostveil.test.ts` (the world and its locked slots, the surfaces, a
clean load, three AI laps, every gate counting on any line including high over the
jump) and `tests/holes.test.ts`.

**Size:** the biggest course so far (about 13 MB of visual geometry and 7 MB of
collision; about 1,400 draw calls at the start). Fog hides the far edges.
