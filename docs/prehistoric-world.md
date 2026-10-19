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

| World             | Id            | Tracks                                                                   |
| ----------------- | ------------- | ------------------------------------------------------------------------ |
| Prehistoric World | `prehistoric` | Riverbend Palms, Cascade Caverns, Bonebog Pyramid, Ember Peak            |
| Test World        | `test_world`  | Dino Demo, Drift Loop, Ribbon Ridge, Meadow Run, Bridge Test, Drift Park |

- Every track belongs to exactly one world (a test checks this).
- Track ids are unchanged, so records and `?track=` links still work.
- World Select opens on the world you picked last, otherwise on your last track's world.
  New players start on Prehistoric World.
- To add a world, add an entry. Its tracks go in `src/game/tracks.ts` as usual.

**World Select** (`src/screens/worldSelect.ts`) shows each world as a wooden board, with:

- a mosaic of its tracks' preview pictures;
- its name and tagline;
- its track count.

The highlighted board lifts and shines. Picking one makes it hop and flash, then Track
Select opens on that world's tracks. Controls: ◀ ▶ choose, Enter picks, Esc goes back.
The mouse works too.

## The courses

| Course          | Id                | Length  | Theme                                       | Music            |
| --------------- | ----------------- | ------- | ------------------------------------------- | ---------------- |
| Riverbend Palms | `riverbend_palms` | ~950 m  | sunny river valley, palms, a tribal village | C major, 132 BPM |
| Cascade Caverns | `cascade_caverns` | ~1100 m | jungle canyon, waterfalls, caves            | D minor, 142 BPM |
| Bonebog Pyramid | `bonebog_pyramid` | ~1140 m | misty fossil swamp, a stepped pyramid       | E minor, 116 BPM |
| Ember Peak      | `ember_peak`      | ~850 m  | a volcano with lava rivers                  | A minor, 158 BPM |

All four share the same basics:

- **Laps:** three, with a checkered start line, a painted grid and ordered checkpoints.
- **Road:** 14 m wide (12 m on bridges), roughly seven karts abreast, banked into every
  turn.
- **Collision:** ground, walls and barriers.
- **Pickups:** zippers, banana rows and balloons, all using the existing systems.
- **Testing:** the race's own AI drives three laps of each course in the tests
  (`tests/prehistoric.test.ts`).

### Riverbend Palms

The road runs north up the east bank and crosses the river on an arched wooden bridge
with rope rails.

1. Riverside S-bends lead up a ridge with a view of the valley.
2. A long sweeping descent drops to a stone ford, where you can splash through the
   shallows.
3. The road winds through the village, with thatched huts and painted totems.
4. The final straight has a zipper.

There's a **shortcut**: a narrow dirt track through the village cuts the last bend.

**Scenery:**

- palms, jungle trees, ferns, flowers and sandstone stacks;
- a waterfall pouring through a notch in the valley wall;
- a smoking volcano far away (a hint of Ember Peak).

**The long-neck:** a friendly dinosaur strolls round the west meadow and crosses the
road near the ford.

### Cascade Caverns

1. You start on the canyon floor.
2. A stone viaduct climbs the east end.
3. A ledge runs along the north wall.
4. A **high bridge** crosses the whole canyon, right over the start straight.
5. A **tunnel** goes through the south wall.
6. A wooden ramp launches you over the river gorge, **through a waterfall** pouring off
   an overhang.
7. The road winds back down over a low stone bridge.

More waterfalls tumble down both walls.

### Bonebog Pyramid

1. The old paved road runs under the **ribs of a giant skeleton**, with its tail
   trailing into the swamp and a frilled, horned skull beside it.
2. A wooden causeway crosses a lagoon.
3. Slick **mud** S-bends follow.
4. A stone road climbs to the stepped **pyramid**, and goes straight through it.
5. A second causeway and more mud bring you home.

**Scenery:** swamp trees hung with moss, reeds, glowing caps and more skulls.

| Surface         | Drives like                       |
| --------------- | --------------------------------- |
| stone road      | normal road                       |
| wooden causeway | road (firm)                       |
| wet mud         | slippery (grip ×0.55), a bit slow |
| shallow water   | slow (off the causeways)          |

### Ember Peak

1. The road spirals once round the cone, counter-clockwise, climbing about 25 m.
2. It crosses **three lava rivers** on basalt bridges.
3. A **glowing tunnel** goes through a rock spur, with lava crystals inside.
4. The road runs along the crater rim at the summit, under the crater's smoke.
5. Then it plunges straight down the south face.
6. On the way down you **jump a lava gully**.

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
- **Volcano Dusk** (an environment only, using the Hot Top Volcano textures).

There are 25 new textures, all 64×32:

- **River Valley:** valley road, grass, sand and water; sandstone cliff; wood planks;
  palm bark and fronds; thatch; painted wood; a start checker; blossom.
- **Fossil Swamp:** mud, swamp water, moss, bone, paving, glowing caps, pyramid steps.
- **Jungle Falls additions:** waterfall, foam, fern.
- **Hot Top Volcano additions:** volcano crust (glowing cracks), ember road, smoke.

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

```json
{ "id": "zip_01", "type": "zipper", "at": 120, "across": -3 }
{ "id": "ban_01", "type": "bananas", "at": 40, "across": 0, "count": 5, "gap": 2.6 }
{ "id": "bal_01", "type": "balloon", "at": 95, "across": 4, "color": "blue" }
```

These now work on any Blender track: `at` is metres along the lap, and `across` is
metres to the right of centre.

## Music

Each course has its own original piece in `src/audio/songs.ts`. Each track's registry
entry names its music. The music player lists all four.

| Piece           | Feel                                                                                    |
| --------------- | --------------------------------------------------------------------------------------- |
| Riverbend Palms | steel pan lead, marimba, flute, island bass, bongos, shaker, clave, brass stabs         |
| Cascade Caverns | flute and xylophone over running pizzicato, woodblocks, hand drums, bells, strings      |
| Bonebog Pyramid | clarinet and bassoon over a low marimba groove, plucks, toms, chimes, surprise chords   |
| Ember Peak      | strings and low brass over a galloping bass, fast marimba, square-wave stabs, big drums |

There are four new synthesized instruments: steel pan, bell, bowed strings and tom.

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
