# Worlds, and the Prehistoric World

Tracks mode now goes **Mode Select → World Select → Track Select → race**. This page
covers the world registry, the four Prehistoric World courses, how they're built in
Blender, the hazards and creatures they use, and their music.

Everything here is original work for this MIT-licensed project: the layouts, models,
textures, creature, music and sounds. The courses are _inspired by_ the kind of bright,
prehistoric worlds late-90s console racers loved. Nothing is copied from any game.

## Worlds

`src/game/worlds.ts` lists the worlds. Each has a stable `id`, a name, a tagline, a
description, a banner colour and its track ids, in menu order:

| World             | Id            | Tracks                                                                                                                                                                                           |
| ----------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Prehistoric World | `prehistoric` | Riverbend Palms, Cascade Caverns, Bonebog Pyramid, Ember Peak                                                                                                                                    |
| Frostveil Peaks   | `frostveil`   | Frostveil Citadel, Snowy Summit Pass, Hearthglow Hollow, Aurora Rift                                                                                                                             |
| Desert World      | `desert`      | Canyon Dash, Oasis Haven, Dry Gulch Ghost Town, Impact Depths                                                                                                                                    |
| Dragon Kingdom    | `dragon`      | Dragon Isles, then three Coming Soon tiles (see [dragon-kingdom.md](dragon-kingdom.md))                                                                                                          |
| Test World        | `test_world`  | Dino Demo, Drift Loop, Ribbon Ridge, Meadow Run, Bridge Test, Loop Lab, Drift Park (hidden from the menus for now: `hidden: true` in `src/game/worlds.ts`; its tracks still load with `?track=`) |

- Every track belongs to exactly one world (a test checks this).
- Track ids are unchanged, so records and `?track=` links still work.
- World Select opens on the world you picked last, otherwise on your last track's world.
  New players start on Prehistoric World.
- To add a world, add an entry. Its tracks go in `src/game/tracks.ts` as usual.
- A world's `comingSoon` names show in track select as locked "Coming Soon" tiles after
  its real tracks (the Dragon Kingdom has three). See [frostveil-peaks.md](frostveil-peaks.md).

**The Ledger** (`src/screens/tracks.ts`) has a wooden bookmark for each world along the
top; the chosen world's Trophy Race and tracks are listed below, with the picture and
details on the right. Controls: ◀ ▶ world, ▲ ▼ track, Enter picks, Esc goes back. The
mouse works too.

## The courses

| Course          | Id                | Length  | Theme                                               | Music            |
| --------------- | ----------------- | ------- | --------------------------------------------------- | ---------------- |
| Riverbend Palms | `riverbend_palms` | ~1040 m | sunny river valley, palms, a tribal village         | F major, 138 BPM |
| Cascade Caverns | `cascade_caverns` | ~1210 m | lost jungle temple, waterfalls, torchlit hall       | D minor, 128 BPM |
| Bonebog Pyramid | `bonebog_pyramid` | ~1630 m | a living swamp, a colossal pyramid to drive through | E minor, 116 BPM |
| Ember Peak      | `ember_peak`      | ~2.4 km | an erupting volcano, lava caverns and a dragon      | D minor, 160 BPM |

All four share the same basics:

- **Laps:** three, with a checkered start line, a painted grid and 8–12 wide checkpoint
  gates ([checkpoints.md](checkpoints.md)), placed after turns, jumps and landmarks.
- **Road:** 14 m wide (12 m on bridges), roughly seven karts abreast, banked into every
  turn.
- **Collision:** ground, walls and barriers.
- **Pickups:** zippers, banana rows and balloons, all using the existing systems.
- **Testing:** the race's own AI drives three laps of each course in the tests
  (`tests/prehistoric.test.ts`).

### Riverbend Palms

Version 2 is laid out for drifting: real 30–40 m arcs you can hold a drift through
(and earn a boost), linked so one drift flows into the next. The road runs north up
the east bank, then west over the river on an arched wooden bridge with rope rails.

1. A long left sweeper in the north-east corner and a right flick line you up for the
   bridge.
2. Over the river, a three-bend S-chain (left, right, left) climbs the west ridge, with
   a view of the valley.
3. Along the ridge (with a zipper), then a right into a hairpin left at the south-west
   corner.
4. A quick left-right wiggle drops to the stone ford, where you can splash through the
   shallows; a zipper waits on the far side.
5. A right and a long left wind through the village, with thatched huts and painted
   totems.
6. The final straight has a zipper, right out of the last drift.

There's a **shortcut**: a narrow dirt track through the village cuts the last bend.

**Scenery** (v2.1 made it busier and more alive):

- a bright blue painted sky all round, with a sun low enough to see while racing and
  puffy cartoon clouds drifting along the top of the valley walls (the track's
  `skyDome` look, `src/render/skyDome.ts`);
- a winding blue river: big meanders north of the bridge and south of the ford, and an
  S through the middle (the crossings never move);
- lily pads, pink lotus flowers and clumps of cattails along the river's edges;
- a waterfall pouring off a ledge through a notch in the valley wall: a curved sheet
  with fast white veils, framing rocks, a churning foam pool, spray and a rainbow;
- grand canopy trees on buttress roots (the valley's landmarks), taller palms, jungle
  trees, bushes, ferns, lots of flowers and sandstone stacks;
- a village of thatched huts round a campfire south of the ford road, and six little
  hamlets round the valley, each with its own campfire (smoke and embers rise from
  them: the `campfire` entity) and painted totems;
- a friendly long-neck dinosaur strolling round the west meadow (one smooth skin,
  lofted round a spine that sways as it walks; trees are kept off its path);
- a smoking volcano far away (a hint of Ember Peak).

#### Going back to Riverbend v1

v1 is tagged `riverbend-v1` in git, and v2 (before the busier v2.1 scenery, river,
clouds and dinosaur) is `riverbend-v2`; use either tag in the commands below. Each
part can be undone on its own:

| To restore           | Do this                                                                                                                                    |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| The whole course     | `git checkout riverbend-v1 -- tools/blender/prehistoric/riverbend_palms.py public/tracks/riverbend_palms tracks-src/riverbend_palms.blend` |
| The old music        | set Riverbend's `music` to `"riverbend_classic"` in `src/game/tracks.ts`                                                                   |
| The old countersteer | set `vehicle.driftCounterOut` to `false` in `assets/data/tuning.json` (or in the debug tuning panel)                                       |
| The old dinosaur     | `git checkout riverbend-v1 -- src/render/dinosaur.ts`                                                                                      |

The sky, water colour, lilies and waterfall are part of the course files, so restoring
the course brings back the old ones too. (The old look.json has no `skyDome`, which
gives the plain sky.)

**The long-neck:** a friendly dinosaur strolls round the west meadow and crosses the
road near the ford.

**Campfires:** `{ "type": "campfire", "x", "y", "z" }` in track.json puts smoke and
embers over a fire (the fire itself is a scenery prop). Purely visual.

### Cascade Caverns

Version 2: a lost temple deep in the jungle.

1. You start on the canyon floor, between giant trees and toppled columns.
2. A carved stone **viaduct** climbs the east end, through a temple gateway.
3. A **ledge** road winds along the north wall: quick S-bends to drift.
4. The **temple bridge** crosses the whole canyon, high over the start straight: a
   stepped Mayan causeway with glyph friezes and a gateway at each end. Its piers stand
   only where no road runs underneath, so nothing on the road below blocks you.
5. The **temple hall** goes through the south wall, about 170 m long: a carved face at
   each mouth, pillars down both walls, roots hanging through the roof and torches
   every 8 m that throw flickering light on the road and the karts.
6. The **leap:** a long run-up (with a zipper), a short 16 m gap and a 22 m-wide
   landing with barriers, through a curtain of water pouring off a rock arch. Miss it
   and you're put down on the landing.
7. The road winds back down through more ruins, under a ruined arch, and over a low
   stone bridge.

**The jungle:** very large trees, dense undergrowth, big-leaf plants, vines spilling
down the cliffs and off rock ledges, lianas slung over the floor, colossal stone heads,
steles, stairs and tumbled blocks. The rock mixes grey, mossy and ochre patches so no
wall repeats.

**The river:** cattails, lily pads, logs, stumps and frogs. Six waterfalls: four down
the canyon walls, the river's source at the east end and a gorge fall at the west end.
The ends are closed by cliffs, and hills ring the horizon (`skyDome.hills` in
look.json), so there's no white void anywhere.

**The pterosaur:** circles high over the canyon, flapping and gliding, and cries now and
then.

**Checkpoints:** 17 gates, each 50 m wide and 10 m tall, so they count whatever line you
take, even high over the leap. `tests/cascade.test.ts` drives every line (both edges,
the middle, and 6.5 m up) for three laps.

#### Going back to Cascade v1

v1 is tagged `cascade-v1` in git:

| To restore       | Do this                                                                                                                                             |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| The whole course | `git checkout cascade-v1 -- tools/blender/prehistoric/cascade_caverns.py public/tracks/cascade_caverns tracks-src/cascade_caverns.blend`            |
| The old music    | set Cascade's `music` to `"cascade_classic"` in `src/game/tracks.ts`                                                                                |
| Bananas          | `git checkout cascade-v1 -- src/render/bananaView.ts src/screens/race.ts`, and set `bananas.color` back to `"#ffd23f"` in `assets/data/tuning.json` |
| Balloon strings  | `git checkout cascade-v1 -- src/render/itemView.ts`                                                                                                 |

### Bonebog Pyramid

Rebuilt as a living swamp: see [bonebog-pyramid.md](bonebog-pyramid.md) for the full
design. In short:

1. The start runs along an **old stone dike** and under the **Jawbone Gate**.
2. Railed **boardwalks** wind east between giant trees, under the canopy.
3. The **Rib Bridge**, a high trestle, runs straight through a colossal rib cage.
4. The **Grand Causeway** crosses the lagoon (a long-neck's neck arches over it) and
   aims at the pyramid's carved face.
5. About **ten seconds inside the pyramid**: a torchlit corridor, a chamber round a
   great column, and the Great Hall with its pillars, roof waterfalls and light.
6. A trestle drops past the **great skull** of Skull Lagoon, then the **mangrove
   boardwalks** under the treehouse village bring you home.

| Surface            | Drives like                          |
| ------------------ | ------------------------------------ |
| paving, boards     | normal road                          |
| mossy banks        | off-road (grass), beside the dike    |
| swamp water (deep) | puts you back at the last checkpoint |

### Ember Peak

Rebuilt as the Volcanic Apocalypse: see [ember-peak.md](ember-peak.md). In short: a
2.4 km lap round, up, into and down a colossal erupting volcano, past a fire-breathing
dragon, through about 20 seconds of lava caverns, and down the mountain as it erupts.

## Party Beach (the title screen)

The title screen's demo race runs on **Party Beach** (`beach_party`), a dinosaur beach
party built by `tools/blender/prehistoric/beach_party.py` with its props in
`beach_props.py`. It's not in any world, so you can't pick it; `?shot=beach_party`
shows it without the UI.

- **The loop (~720 m):** the start straight runs along the beach, then up the east side
  past the tiki bar, along the dunes at the back (over a creek on a little wooden
  bridge), and down the west side past the bonfire, back over the lagoon's outlet.
- **The beach:** white-gold sand, a turquoise sea with surf lapping the shore, striped
  umbrellas with towels and deck chairs, surfboards, beach balls, sandcastles,
  outrigger canoes, a volleyball game, starfish and shells. Sea stacks with palms on
  top, and a volcano island on the horizon.
- **The party:** a DJ stage with a dance floor of dancing dinosaurs, a conga line round
  the bonfire, regulars at the tiki bar, coconut palms lining the road with bunting and
  paper lanterns strung across it, tiki torches everywhere.
- **Wildlife:** two long-necks (a big one and a youngster) wading in the shallows and
  two pterosaurs circling overhead.
- **Look:** the **Beach Party** theme: a bright midday sky with clouds and low distant
  islands, and 14 new textures (beach sand, packed-sand road, wet sand, sea, surf, six
  party colours, paper lantern, tiki wood, dino scales).

### Partygoers

```json
{ "id": "partygoer_01", "type": "partygoer", "x": -30, "y": 2, "z": -60, "heading": 0.4, "variant": 2, "dance": "bounce" }
{ "id": "conga_01", "type": "conga", "x": -132, "y": 1, "z": -40, "radius": 6.5, "count": 7, "speed": 1.4 }
```

Little cartoon dinosaurs (`src/render/partyDino.ts`) in six looks (a duck-bill crest,
back plates, a horned frill, a bony dome, a spiky frill, a plain round one) with party
extras: sunglasses, leis, party hats, a flower. They dance on the beat of the title
music: `bounce`, `sway`, `wave`, `hop`, `chill` (at the bar), `dj` (at the decks), or
walk round a `conga` circle. Purely visual (no collision), so keep them off the road.

## How they're built

Each course is a Blender build script in `tools/blender/prehistoric/`:

```
python tools/blender/prehistoric/riverbend_palms.py      # with the bpy module, or
blender --background --python tools/blender/prehistoric/riverbend_palms.py
```

Each script saves `tracks-src/<id>.blend` and exports `public/tracks/<id>/`. The dev
server reloads a course in the game when its package is re-exported.

| File               | What it does                                                                                  |
| ------------------ | --------------------------------------------------------------------------------------------- |
| `course_kit.py`    | the shared toolkit: route, road pieces, terrain, rocks and tunnels, water, props, entities    |
| `props.py`         | the reusable low-poly props and their placement                                               |
| `make_textures.py` | paints the new library textures and lists them in `materials.json` (run with plain `python3`) |
| `<course>.py`      | one per course: the layout as data, and what goes where                                       |

### What a course is made of

**Route.** A hidden Bezier curve, the race line.

- Checkpoints, the start grid and the AI's racing line all come from it.
- The banking is worked out from its curvature.

**Roads.** Separate road curves, each with the add-on's KP Road modifier, cut from the
route between two distances.

- Each piece has its own material, shoulders, barriers and deck: dirt road, wooden
  bridge, stone viaduct, causeway, mud and so on.
- Pieces can leave a gap: that's how the jumps work.
- A ramp piece can tip up at its end (a kicker).
- A shortcut is a road curve that isn't part of the route.

**Terrain.** A height-field grid shaped by each script's `natural(x, y)` function.

- The roads pull it up or down to meet them.
- It never comes up through a bridge or into a jump's gap.
- Each script's `classify()` picks the textures by slope and height.

**Rocks and buildings.** Tunnels are cut through rock masses (and the pyramid) with a
boolean.

**Water and lava.** Strips that flow downstream, waterfall sheets, foam pools and lava
lakes. Everything that moves animates in the game through the material library's
`kp_fx`.

**Props.** One mesh per prop (`Prop Palm 0`, `Prop Hut`...), shared by every copy.

- Edit the prop mesh in Blender and every copy changes.
- Big props collide (trunks, huts, bones, rocks). Small ones are only seen (ferns,
  flowers, reeds, glowing caps).

**Paths.** Hidden curves exported as extra routes in `route.json`, such as `Dino Path`.

**Gameplay data.** Pickups, hazards and the creature go in `track.json` `entities`.
The build script rewrites them each time it runs.

The `.blend` files are ordinary scenes: open one to keep editing by hand.

Collections group everything:

- Route, Roads, Terrain, Rocks, Water;
- Props, Prop Library, Village, Landmarks, Backdrop;
- Markings, Paths.

Note that the road pieces were cut from the route when the script ran. If you move the
Route curve by hand, move the pieces to match, or change the control points in the
script and re-run it.

### New library textures

The Material Browser gains three themes, each with its own sky and fog:

- **River Valley**;
- **Fossil Swamp**;
- **Volcano Dusk** (an environment only, using the Ember Volcano textures).

There are 25 new textures, all 64×32:

- **River Valley:** valley road, grass, sand and water; sandstone cliff; wood planks;
  palm bark and fronds; thatch; painted wood; a start checker; blossom.
- **Fossil Swamp:** mud, swamp water, moss, bone, paving, glowing caps, pyramid steps.
- **Jungle Cascade additions:** waterfall, foam, fern.
- **Riverbend v2 additions (River Valley):** cattail leaf and head, campfire flame,
  bright canopy, lily pad, lotus petal, rainbow, and the
  falls' sheet, veil and foam (brighter and bluer than Cascade's, which keep the
  Jungle Cascade ones). Valley water is bluer than in v1.
- **Ember Volcano additions:** volcano crust (glowing cracks), ember road, smoke.
- **Cascade v2 additions (Jungle Cascade):** grey, mossy and ochre canyon rock; ruin
  stone, carved glyphs and sooty ruin stone; jungle bark; deep canopy; big leaf; vine
  leaves; frog skin; log end; pterosaur skin; torch flame; jungle mud.

There are also two new driving surfaces: `mud` and `deep_water`.

## Hazards and creatures

`src/game/hazards.ts` runs everything that reacts to where a kart is. Kart handling is
untouched: these only kick or slow a kart, or put it back, the same way an item hit
does. The settings are in `tuning.json` under `hazards`.

### Lava: the burning bounce

Touching lava (the `lava` surface):

- kicks you up, with a push back towards the road;
- cuts your speed;
- plays a sizzle, with sparks and smoke, and your racer yelps and shakes.

You can still steer in the air, and you're immune for a moment after. Get burnt three
times within eight seconds and you're put back at the last checkpoint, held still for
1.2 s (the time penalty). Then you're immune long enough to get going, so it never
loops.

### Water

- **Shallow water** (`water`): slow, with a splash going in and spray behind you.
- **Deep water** (`deep_water`): a big splash, then you bob, low in the water. After a
  second you're fished out at the last checkpoint.
- Riverbend's river is deep except by the ford. Cascade's river is deep all the way.

### Jump gaps

```json
{ "id": "respawn_01", "type": "respawn", "from": 820, "to": 860, "at": 868 }
```

A kart that needs putting back while it's between `from` and `to` (metres along the
lap) goes to `at` instead of the last checkpoint. That's past the gap, so a missed jump
never sends you back to try again at a crawl.

### The long-neck

```json
{ "id": "dinosaur_01", "type": "dinosaur", "route": "Dino Path", "speed": 3, "start": 40 }
```

- **Path:** it walks round the `Dino Path` route at a steady pace, so where it is
  depends only on time. To move it, draw your own path in Blender: a curve marked as a
  route.
- **Never teleports:** it never moves more than one step's walk at a time.
- **Stops for karts:** it stops when one comes within 16 m, looks at it, and walks on
  once the way is clear.
- **Bumps:** its body is two solid circles. Karts are pushed out and slowed, never
  trapped.
- **Looks and sound:** its legs, neck and tail are animated, it casts a round shadow on
  the ground, and it hoots now and then and thuds as it walks.

A `"model": "mammoth"` makes it a woolly mammoth instead (Snowy Summit Pass: a mother
and her calf, `"scale": 0.55`, walking the `Mammoth Path`), who trumpets rather than
hoots.

### Geysers

```json
{
  "id": "geyser_01",
  "type": "geyser",
  "x": 186,
  "y": 0.9,
  "z": 114,
  "r": 4.2,
  "height": 22,
  "period": 7,
  "offset": 0,
  "warn": 1.4,
  "blast": 2.2,
  "launch": 15
}
```

Hot springs that blow on a fixed beat of the race clock (`src/game/geyser.ts`), so
every race and time trial sees the same eruptions:

- **Idle:** a gentle steam.
- **Warning** (`warn` seconds): bubbling, a gurgle, the steam thickening.
- **Blast** (`blast` seconds): a roaring column of water and steam, `height` metres.
- **Launch:** a kart inside the column (radius `r`) while it blows is thrown upward at
  `launch` m/s, keeping its speed and heading: a free jump, never a penalty. Not again
  for a second. With `"launch": 0` it's scenery.
- **Lava** (`"lava": true`, Impact Depths): the same beat, but the column is fire. While
  it gets ready its vent glows on the road and spits sparks; caught in it as it blows,
  you get lava's burning bounce.

### Snowballs and the sleigh

```json
{ "id": "snowball_01", "type": "snowball", "ax": -198, "ay": 6.9, "az": -300, "bx": -257, "by": 4.8, "bz": -266,
  "r": 2.6, "period": 8, "offset": 1.5, "travel": 4.2 }
{ "id": "sleigh_01", "type": "sleigh", "ax": -469, "ay": 17.6, "az": -106, "bx": -373, "by": 2.7, "bz": -106,
  "period": 13, "offset": 4, "travel": 5.5, "warn": 2.5 }
```

Things crossing the road on a fixed beat of the race clock (`src/game/movers.ts`), so
every race and time trial is the same. Each period a giant snowball rolls from A to B
over `travel` seconds (it's gone the rest of the time); the sleigh, pulled by two
reindeer with a snowman at the reins, does the same, its bells jingling for `warn`
seconds first. Both are solid (the same solid circles as the long-neck): hit one and
you bounce off and lose some speed, with a thud and a puff of snow. A clear moment
between crossings is guaranteed.

### Presents, the bell, baubles, chimneys and lanterns

- `present` `{ "x", "y", "z", "size": 2.4, "variant": 0, "heading": 0 }`: a big wrapped
  present by the road. Drive into it and it bursts in confetti (you lose a tenth of your
  speed); it pops back 14 s later.
- `bell` `{ "x", "y", "z", "heading", "period": 14, "offset": 3, "ring": 3.4 }`: the bell
  tower's bell, swinging and bonging on its beat.
- `ornament` `{ "x", "y", "z", "r": 1.5, "color": "#d82a3a" }`: a giant bauble turning
  slowly.
- `chimney` `{ "x", "y", "z" }`: smoke curling up from a chimney near you.
- `lantern` `{ "x", "y", "z" }`: like a torch (the nearest light the scene with a gentle
  flicker) but without embers.
- Snow powder puffs up behind any kart driving through deep snow.

### Loops, icicles, thin ice, shimmering crystals and ice motes

- `loop` `{ "x", "y", "z", "heading", "radius", "ramp", "offset", "width", ... }`: a
  loop-the-loop that karts ride in loop mode. See [loops.md](loops.md).
- `icicle` `{ "x", "y", "z", "top": 14, "period": 9, "offset": 0, "warn": 1.6, "r": 3.2 }`:
  a great icicle hanging over the road. On its beat of the race clock it creaks and
  shakes for `warn` seconds while a ring glows on the road where it will land, then
  drops and shatters. A kart within `r` there is knocked: half speed and a hop. It grows
  back for the next beat. `"decor": true` ones fall over the abyss and hit nothing.
  `"look": "rock"` makes it a boulder working loose from a cave roof, `"meteor"` a
  burning fragment of the asteroid streaking down out of the sky (it isn't seen until
  it falls): the same beat, warning ring and knock.
- `thin_ice` `{ "x", "y", "z", "r": 6, "hold": 7 }`: a cracked patch of lake ice. Every
  kart that drives onto it cracks it further. On the third pass it gives way into slush
  that slows anything in it for `hold` seconds, then it freezes whole again. Left alone,
  a crack heals every 10 s.
- `shimmer` `{ "x", "y", "z", "size": 1.4, "color": "#5ae8ff" }`: a crystal by the road
  that flares as a kart passes and fades slowly. In a row, they light up one after
  another.
- `sparkles` `{ "rate": 36, "radius": 34 }`: tiny ice crystals glinting round the camera.

The rules (timing and states) are in `src/game/rift.ts`; the drawing is in
`src/render/riftFx.ts`.

### Desert dust, wind, windmills and birds

- `dust` `{ "color": "#d89a6a", "rate": 1 }`: dust kicked up behind karts on dirt and
  sand, thicker with speed and off the road.
- `dustwind` `{ "rate": 10, "radius": 60, "color": "#e0a878" }`: wisps of dust blowing
  across the land round the camera on a gusting breeze.
- `windmill` `{ "x", "y", "z", "heading", "radius": 3.2, "speed": 1.4 }`: a ranch
  windmill's turning wheel (the tower is scenery), its hub at (x, y, z).
- `birds` `{ "x", "y", "z", "radius": 70, "count": 3, "speed": 0.2, "seed": 1 }`: big birds
  circling high over a spot, beating their wings now and then.

All purely visual. The rules are in `src/game/desert.ts`; the drawing is in
`src/render/desertFx.ts`. See [desert-world.md](desert-world.md).

### Boats and fountains

- `boat` `{ "route": "Boat Path 1", "speed": 4, "start": 0, "colors": ["#e02a2a",
"#f6c03a"], "scale": 1 }`: a little sailing boat going round a closed path from
  route.json (draw a curve on the water in Blender and mark it as a route), bobbing and
  heeling, its striped sail filling, a wake behind it.
- `fountain` `{ "x", "y", "z", "height": 6, "jets": 6, "radius": 3.5 }`: spray from a
  fountain (the basin is scenery): a jet straight up `height` metres and a ring of
  `jets` arcing out to land `radius` metres away. Drawn only near the camera.

The rules are in `src/game/oasis.ts`; the boats are drawn by `src/render/oasisFx.ts`.

### The haunting (Dry Gulch)

- `minecart` `{ "ax", "ay", "az", "bx", "by", "bz", "period": 7, "offset": 0, "travel": 3,
"warn": 1.8 }`: a runaway ore cart rattling across the road from A to B on a fixed
  beat of the race clock. For `warn` seconds first it waits in the side tunnel's mouth,
  glowing brighter and rattling. Solid, like the sleigh: hit it and you're knocked aside
  and slowed. There's always a clear moment in every period.
- `ghost` `{ "x", "y", "z", "heading", "look": "float", "period": 13, "offset": 0,
"scale": 1, "drift": 0, "vanish": 0 }`: a see-through figure that appears for a few
  seconds of each period and fades away. `look`: `window` (a figure at a window),
  `float` (a sheet-like spirit, bobbing, drifting round `drift` metres), `miner` (a
  ghostly miner who fades out when a kart comes within `vanish` metres), `shadow` (a
  giant miner's shadow on a wall, ringed with green light).
- `ghostrider` `{ "route": "Ghost Rider Path", "period": 38, "offset": 0, "travel": 14 }`:
  a ghostly rider galloping along a path once a period, rising out of the mist and
  melting back into it.
- `railcart` `{ "route": "Railway", "period": 34, "travel": 13, "pause": 4 }`: an empty
  ore cart rolling along a path by itself: out, a pause, back, a pause.
- `tumbleweed` `{ "ax", ..., "bz", "period", "offset", "travel", "r": 0.8 }`: a tumbleweed
  bowling across the road now and then. It rolls through karts: purely visual.
- `door` `{ "x", "y", "z", "heading", "width": 2.4, "period": 9 }`: swinging saloon doors
  that open on their own now and then (heading: the line of the doorway).
- `wisps` `{ "x", "y", "z", "radius", "count" }`: little green lights wandering about.
- `mist` `{ "x", "y", "z", "radius", "rate" }`: green mist curling low over the ground.
- `whispers`, `creak` `{ "x", "y", "z", "radius" }`: ghostly whispering, or old timber
  creaking, when you're near.
- `ambience` `{ "wind": 0.55, "caves": [[x, y, z, r], ...] }`: the night wind, which falls
  away underground (inside the caves' spheres) as a low rumble takes over.
- `windmill` can be `"gusty": true`: it turns fitfully, lurching and stalling.

All but the cart are purely visual (and audible). The rules are in `src/game/haunt.ts`
(the cart's in `src/game/movers.ts`); the drawing is in `src/render/hauntFx.ts`.

### The world under the desert (Impact Depths)

- `atmosphere` `{ "zones": { "crystal": { "fog": "#241a3a", "near": 60, "far": 520,
"sun": 0.35, "sky": "#8ab0ff", "ground": "#6a3a2a", "hemi": 1.25, "sound": "chime" },
... }, "keys": [[x, y, z, "zoneA", "zoneB", t], ...] }`: the air of each world (fog
  colour and distance, how much sunlight reaches it, the ambient light, its sound:
  `wind`, `resonance`, `chime`, `jungle`, `drip`, `rumble`, `hum`, or Dragon Isles'
  `festival`, `falls`, `garden` and `harbour`) and keys along the
  lap and the shortcut saying which worlds are either side and how far between them.
  Wherever you are, the nearest keys blend the air smoothly from one world into the next.
- `triceratops` `{ "x", "y", "z", "heading", "scale": 1, "roam": 6, "seed": 1 }`: a
  three-horned grazer ambling round its own patch, head down to graze, now and then
  lifting it to bellow. Solid.
- `raptors` `{ "ax", ..., "bz", "period": 9, "offset": 0, "travel": 2.2, "warn": 1.4,
"count": 3 }`: a pack darting across the road on a beat, chattering in the ferns for
  `warn` seconds first. Solid while crossing (a knock and a slowdown); a clear road
  between crossings.
- `meteors` `{ "x", "y", "z", "rate": 0.35, "intro": true }`: shooting stars over the
  open desert, and with `intro` the great fireball at the start of every race, down
  into the crater at (x, y, z) with a flash and a boom.
- `plume` `{ "x", "y", "z", "height": 150, "radius": 16, "rate": 7, "color", "glow" }`:
  a column of smoke rising and drifting, lit from below.
- `core` `{ "x", "y", "z", "size": 16 }`: the Heart of the Earth: a gold crystal heart
  in a shell of magenta points, beating, with three rings of light turning round it,
  motes rising and a pulsing light.
- `motes` `{ "x", "y", "z", "radius", "rate", "color", "rise", "size", "blink" }`: little
  lights drifting near a spot (sunbeam dust, crystal glints, fireflies, embers).
- `glow` `{ "x", "y", "z", "color" }`: a coloured light; the four nearest you light the
  road, the walls and the karts.
- The `dragon` takes `"look": "obsidian"` (black, with molten spines and a crimson
  membrane), and every dragon now blinks, flexes its wings and swishes its tail.

The triceratops, raptors, meteors, plume, core, motes, glows and air are in
`src/game/depths.ts` (the rules) and `src/game/depthsLife.ts` (running them); the
drawing is in `src/render/depthsFx.ts`.

### The dragon kingdom (Dragon Isles)

- `isles_dragon` `{ "keys": [[s, x, y, z], ...], "length", "size": 1 }`: the great
  dragon. Each key says where it should be when the player is `s` metres round the lap.
  It flies a smooth loop through the keys, never backwards: faster when behind, gliding
  when ahead. Its body follows its head's path, it turns its head toward you when near,
  its shadow crosses the ground and it calls now and then. Scenery only: it never
  touches a kart.
- `villagers` `{ "list": [[x, y, z, faceX, faceZ, role, variant], ...] }`: the crowd,
  drawn instanced. Roles: `cheer`, `wave`, `merchant`, `dancer`, `musician`, `fisher`,
  `gardener`, `guard` (never moves) and `bow`. Everyone but the guards bows together
  when the dragon passes close, and the `festival` sound hushes.
- `waterwheel` `{ "x", "y", "z", "heading", "radius": 3, "speed": 0.8 }`: a mill wheel
  turning about its axle (`heading`: 0 = the axle along +Z).
- `little_dragons` `{ "x", "y", "z", "radius", "count", "speed", "seed" }`: small
  dragons looping and weaving round a spot.

The rules are in `src/game/isles.ts`, running them in `src/game/islesLife.ts`, and the
drawing in `src/render/islesFx.ts`. See [dragon-kingdom.md](dragon-kingdom.md).

### Torches

```json
{ "id": "torch_01", "type": "torch", "x": -90, "y": 20, "z": 95 }
```

The flame of a wall torch (the torch itself is scenery). The four torches nearest you
light the road, the walls and the karts with a warm flicker, and drop the odd ember.

### The pterosaur

```json
{ "id": "pterosaur_01", "type": "pterosaur", "route": "Flyer Path", "speed": 13, "scale": 1.6 }
```

It flies smoothly round the `Flyer Path` route (its height comes from the route),
flapping for a while then gliding, banking into its turns. Purely visual: it has no
collision and stays high above the road.

### Waterfalls

```json
{
  "id": "waterfall_01",
  "type": "waterfall",
  "x": -190,
  "y": -1.6,
  "z": 1,
  "top": 27,
  "width": 34,
  "heading": 0
}
```

- Spray rises at the foot of each waterfall.
- Its roar fades in as you get close.
- Driving through one drenches you with a splash.

### Pickups

The pickups are **dinosaur eggs** (speckled, sitting in little straw nests), on every
track. They play exactly as bananas did, and the code and track files still call them
bananas. Balloons hang from squiggly twisted cords with a bone tied on, and carry
carved markings in their usual colours.

```json
{ "id": "zip_01", "type": "zipper", "at": 120, "across": -3 }
{ "id": "ban_01", "type": "bananas", "at": 40, "across": 0, "count": 5, "gap": 2.6 }
{ "id": "bal_01", "type": "balloon", "at": 95, "across": 4, "color": "blue" }
```

These now work on any Blender track: `at` is metres along the lap, and `across` is
metres to the right of centre.

## Music

Each course has its own original piece in `src/audio/songs.ts`. Each track's registry
entry names its music. The music player lists them all, plus Riverbend's and Cascade's
v1 themes.

| Piece                     | Feel                                                                                                    |
| ------------------------- | ------------------------------------------------------------------------------------------------------- |
| Riverbend Palms           | a beach party: steel pan lead, strummed marimba, brass hits, whistling flute, soca bass, congas, shaker |
| Riverbend Palms (Classic) | the gentler v1 theme: steel pan, marimba, flute, island bass, bongos, clave                             |
| Cascade Caverns           | the jungle temple: pan flute and bird calls over a log-drum ostinato, a buzzing drone, djembe, horns    |
| Cascade Caverns (Classic) | the v1 theme: flute and xylophone over running pizzicato, woodblocks, hand drums, bells, strings        |
| Bonebog Pyramid           | clarinet and bassoon over a low marimba groove, plucks, toms, chimes, surprise chords                   |
| Ember Peak                | low brass over a hammering marimba and heavy toms, then strings and brass soaring (Volcanic Apocalypse) |

There are eight new synthesized instruments: steel pan, bell, bowed strings, tom, pan
flute, log drum, drone and djembe.

The pieces behave like the rest of the soundtrack:

- they loop seamlessly;
- Restart starts the piece again cleanly, with no second copy playing;
- pausing ducks them;
- they follow the music volume;
- after the results fanfare, the menu music returns.

Track Select gets the highlighted course's piece ready while you browse.

## Not yet

- The water isn't truly buoyant: you float on the surface plane, with a visual bob.
- Track preview pictures are still game screenshots.
- There's only one shortcut so far (Riverbend). Bonebog's reeds and Cascade's ledges
  would suit more.
