# Frostveil Peaks

A prehistoric winter world: snowbound mountains where an ancient civilization built
temples, bridges and fortresses into the peaks. Its courses are **Frostveil Citadel**
(moonlit ruins), **Snowy Summit Pass** (a bright, sunny lake) and **Hearthglow Hollow**
(a Christmas village at twilight); one more is planned and shows in track select as a
locked "Coming Soon" tile (`comingSoon` in `src/game/worlds.ts`: rename it there when it
has a name).

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

## Snowy Summit Pass

The sunny opposite of the citadel: a wild, bright lap of about 2.4 km (an AI lap is
about 103 s) round a frozen mountain lake, with three jumps, geysers, a glowing ice
cave and a spiral up inside a giant tree. Its layout follows the "Snowy Summit Pass"
concept: frozen bay, ice archways, crystal caves, polar ruins, glacier fields, ice
floes, wind canyons and a summit lookout, with plank bridges and prayer flags, floating
ice islands, icefalls, a wrecked ship and frozen tower ruins. All designs are original.

| #   | Section                  | What happens                                                                                                                                                                                       |
| --- | ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | The Frozen Bay           | The start, under strings of prayer flags, on a groomed snow road straight across the lake's turquoise ice. Icebergs, a pirate ship wrecked in the ice, and two woolly mammoths wandering the bay.  |
| 2   | The Ice Archways         | S-bends under three great natural arches of blue ice.                                                                                                                                              |
| 3   | The Geothermal Springs   | The lake's east end is melted by hot springs: steaming turquoise water, ice floes, orange-rimmed travertine terraces. A geyser in the road, a wooden ramp, and a jump over the geyser basin.       |
| 4   | The Crystal Caves        | North into the glacier: a tunnel of blue ice climbing 3 to 21 m, glowing blue and violet crystals on the walls and roof, chevron signs on the bends.                                               |
| 5   | The Wind Canyons         | West along a canyon carved into the snowy plateau, under an ice arch and flags strung wall to wall, then a jump over a deep gorge (a zipper on the run-up makes it a huge one).                    |
| 6   | The Giant Trees          | Down into a half-frozen, half-thawed forest: snowy pines up high, green trees and meadow on the low ground, shafts of sunlight. The road drives into the biggest tree and spirals up inside it.    |
| 7   | Treetop Bridges, Lookout | Out of the tree 30 m up onto plank bridges with rope rails and bunting, round ledges on two more giants, and onto the lookout rock (a hut, flags) with the whole lake below.                       |
| 8   | The Glacier Fields       | A fast plunge down the west ridge, a jump off an icy bluff over a crevasse, and a sweep across the open ice (bare ice is road but slippery: cut across if you dare) under a mammoth skull's tusks. |

**The great tree:** 84 m across at the road, its trunk a thick shell (bark outside,
golden heartwood inside) on great roots. The road goes in through an arched doorway,
winds up two whole turns of a 28 m spiral (15 m a turn, so each turn passes over the
one below) round a heartwood column, on a ramp with rails both sides and beams under
every turn, and leaves through a doorway 30 m up straight onto the first bridge.
Glowing shelf fungi, knotholes letting in beams of sunlight, and a crown of green far
above (with the last snow on it).

**Geysers:** they blow on a fixed beat of the race clock (`geyser` entities, see
[prehistoric-world.md](prehistoric-world.md#geysers)): steam at rest, a gurgle and
bubbling as a warning, then a roaring column. The one in the road on the terraces and
the big one under the jump throw you into the air if you're in the column as it blows
(you keep your speed: a free jump). The rest are scenery.

**The mammoths:** a mother and her calf (`dinosaur` entities with `"model":
"mammoth"`, an original cartoon mammoth in `src/render/mammoth.ts`) walk a loop on the
bay south of the road, stop for karts and trumpet.

**Jumps:** the geyser basin (12 m), the gorge (16 m) and the crevasse (16 m). Missing
one puts you down on its landing (`respawn` entities). No checkpoint sits inside a
jump's catch stretch.

**Surfaces:** the snow road is `packed_snow`, cobbles `snow_stone`, plank bridges and
travertine `road`, the forest track `dirt`, bare lake ice `ice` (road, but very
slippery), deep snow off the road `deep_snow`, the hot water `deep_water` (you're
fished out), and the gorge and crevasse floors `abyss`.

**Lighting:** the **Summit Pass** theme: a high sun in a deep blue sky with white
clouds and pale far peaks, light fog only far out. The caves are painted blue and
violet round their crystals; the inside of the great tree warm gold round its fungi
and knotholes; and the forest floor lies in dappled shade with sunny patches, with the
giants' canopy shading the roads under it.

**Music:** "Snowy Summit Pass" (`summit` in `src/audio/songs.ts`), D major, 152 BPM: flute
and xylophone on the bay, brass up through the caves and canyons, strings and bells in
the treetops, everything together for the plunge back down, over a running marimba, a
skipping bass, shaker and tambourine.

**How it's built** (`tools/blender/prehistoric/`):

- `snowy_summit.py`: the layout (turtle segments; the spiral is one 720° arc), heights,
  the land (the lake and its melted end, the gorge, the crevasse, the plateau, the
  glacier, the west ridge, the lookout rock, terraced mountains), the road kinds, the
  hidden floors and the gameplay.
- `summit_scenery.py`: the glacier and its caves, the lake (hot water, floes, icebergs,
  the wreck), the hot springs, the ice arches, the great tree and the other giants, the
  forest, the bridges, flags and lookout, the canyons, the polar ruins, the floating
  islands, the mammoths' path, the entities and the painted light.
- `summit_props.py`: the kit (pines, broadleaf trees, shrubs, boulders, icebergs, floes,
  ice arches, floating islands, geyser cones, terrace pools, the shipwreck, the tusk
  gate, ribs, tower ruins, columns, chevrons, flag poles, the hut, bunting lines).
- Theme `summit_pass` and 34 textures in `make_textures.py`.

**Tests:** `tests/summit.test.ts` (the world, a clean load, the spiral really stacking,
the geysers' schedule and launch, the mammoths, three AI laps) and `tests/holes.test.ts`.

**Size:** about 17 MB of visual geometry and 6 MB of collision; about 510 draw calls
at the start.

## Hearthglow Hollow

A Christmas village on a snowy evening: a lap of about 2.57 km (an AI lap is about
112 s) through an alpine village decorated for Christmas, round its giant tree, over the
frozen river, through an enchanted forest, up the mountain to the bell tower and down a
sleigh run. A deep purple and blue twilight full of stars, warm golden windows and
lanterns, coloured lights everywhere. All designs are original.

| #   | Section                        | What happens                                                                                                                                                                            |
| --- | ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A   | The Village Entrance           | The start under a great wooden Christmas arch (wreath, lanterns, banners, a checkered banner), up a cobbled street of glowing cottages, lantern posts and lights, the giant tree ahead. |
| B   | The Village Square             | Down into the paved square and round the 44 m giant tree (lights spiralling up it, a golden star, giant baubles turning) in a sweep of curves, past stalls, snowmen and presents.       |
| C   | The Frozen River Crossing      | North over an arched stone bridge above the frozen river, icicles under it. Or, before it, the shortcut: down the bank onto the river ice, west along it and back up onto the lane.     |
| D   | The Enchanted Forest           | Between snow-laden pines (some strung with lights), log cabins and lanterns. At two crossings giant snowballs roll across the road on a fixed beat.                                     |
| E   | The Mountain Climb             | Up the mountainside on snowy roads and timber trestles, a hairpin, the high road with the village glowing below, a trestle over the creek's gorge, to the bell tower at the summit.     |
| F   | The Sleigh Run                 | A fast plunge down a broad snowy chute under decorated arches, candy canes down its edges, two jumps, and a sleigh crossing on a fixed beat (its bells jingle as a warning).            |
| G   | Covered Bridge, Village Return | Through a long lantern-lit covered bridge over the river, back along the village lanes (an icy patch on two of them) and a last left-hand drift onto the finish straight.               |

**The shortcut:** off the street just before the stone bridge, down the bank onto the
frozen river (`icy_stone`: half the grip), west along it and up the north bank onto the
lane. It's shorter, with tighter turns on slippery ice. A twin checkpoint gate stands
across it on the ice (either counts); no other gate is in the stretch it skips.

**Mechanics:** rolling snowballs and the sleigh (`snowball` and `sleigh` entities,
`src/game/movers.ts`) are solid and slow you; presents by the road burst when you drive
into them and come back; the bell swings and rings on its beat; icy cobbles in two lanes
and on the river; jumps with catches. See
[prehistoric-world.md](prehistoric-world.md#snowballs-and-the-sleigh). Kart physics is
unchanged.

**Atmosphere:** the `hearthglow` theme (a twilight sky dome with stars, which the dome
now supports with `"stars"`), warm light painted onto the snow and the houses round
every window, lantern and light; the nearest lanterns light the road and karts with a
gentle flicker (`lantern` entities); chimney smoke; falling snow; Christmas lights that
chase along their strings (a scrolling glow texture); flowing water down the middle of
the river where it's only partly frozen; frozen falls on the cliffs; lit cabins and
hamlets all over the valley and the mountains.

**Music:** "Hearthglow Hollow" (`hearthglow` in `src/audio/songs.ts`), G major, 160 BPM:
sleigh bells throughout; celesta and bells, then flute, then strings and brass, over
plucked strings, a twinkling glockenspiel and an oom-pah walking bass.

**How it's built** (`tools/blender/prehistoric/`):

- `hearthglow_hollow.py`: the layout (turtle segments), heights, the land (the valley,
  the river and the creek, the mountainside shaped round the climb, the ridge, the
  mountains), the road kinds, the shortcut, the hidden floor and the gameplay.
- `hearthglow_scenery.py`: the village (streets of cottages, the square, stalls, the
  frozen fountain, lantern posts, lights), the bridges, trestles, the forest, the bell
  tower, the hamlets, the sleigh run, the water, the entities and the painted light.
- `hearthglow_props.py`: the kit (cottages and their collision blocks, stalls, lantern
  posts, lit and plain pines, the giant tree, present piles, snowmen, candy canes,
  Christmas arches, the bell tower, logs, strings of lights).
- Theme `hearthglow` and 25 textures in `make_textures.py`.
- The moving parts are drawn in code: `src/render/festive.ts` (snowballs, presents, the
  bell, baubles, the sleigh, reindeer and snowman).

**Tests:** `tests/hearthglow.test.ts` (the world, a clean load, where the moving parts
are, their schedules, the bump and the bursting present, the shortcut counting, three
AI laps) and `tests/holes.test.ts`.

**Size:** about 22 MB of visual geometry and 6 MB of collision; about 1,000 draw calls
at the start.
