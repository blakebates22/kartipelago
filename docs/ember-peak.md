# Ember Peak: the Volcanic Apocalypse

Dinosaur Valley's fourth course, rebuilt as its most dangerous and dramatic:
racing through a volcanic landscape at the start of an enormous eruption. About 2.4 km
a lap (an AI lap is about 106 s), climbing from the plain to 74 m and back.

The old version (a 31 m mound in a flat field, an 850 m lap and a 50 m tunnel) is in
git history before this rebuild; its music is kept as `ember_classic`.

## The lap

| Section | Name                  | What happens                                                                                                                                                 |
| ------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A       | The Burning Forest    | The start: a wide road east across the south, burning and charred pines and dead palms either side, smoke rising, the volcano looming on the left.           |
| B       | The Obsidian Fields   | Sweeping S-bends between obsidian spires, clusters and leaning slabs veined with glowing magma, past lava pools, under an obsidian arch.                     |
| C       | The Dragon's Crossing | A wide basalt bridge north over a deep lava ravine (lava falls down its walls). The dragon perches on its crag to the east and breathes fire across it.      |
| D       | The Volcanic Ascent   | A road carved round the east flank, a hairpin, and a second, higher cliff road, 17 to 55 m, over lava gorges; zippers, braziers, smoking fissures.           |
| E       | The Mouth             | A towering basalt gateway into the east face between two great obsidian spires, lava pouring down either side, the furnace glow within.                      |
| F       | The Infernal Caverns  | About 450 m (20 s) inside: the entry hall (lava channels both sides), the lava-lake cavern on a bridge, tunnels, the amethyst gallery, the magma falls hall. |
| G       | The Eruption Escape   | Out high on the north-west flank (74 m) and a fast sweeping descent round the west side, two zippers, the volcano erupting behind you.                       |
| H       | The Final Descent     | Past lava rivers and burning forest, under another obsidian arch, back onto the start.                                                                       |

**The volcano** stands in the middle of the map: 760 m across at its foot and about
250 m tall at its crater rim, its summit rising steeply from broad shoulders, lava
streaming down its flanks from the crater, a lake of lava in the crater, fountains of
fire and a vast plume of ash leaning on the wind. Seven more volcanoes smoke round the
horizon. Lava rivers run down four ravines; the road bridges each one.

## The dragon

An original low-poly fire-breather (`src/render/dragon.ts`): a dark red-brown body
gripping its crag, great wings, a long two-jointed neck, a horned head with glowing eyes
and a hinged jaw, and a throat that glows as it draws breath.

Its attack is a fixed schedule of the **race clock** (`src/game/dragon.ts`), so every
race and every time trial sees exactly the same attacks (learn the timing!):

| Phase          | Seconds | What you see                                                                           |
| -------------- | ------- | -------------------------------------------------------------------------------------- |
| IDLE           | 3.0     | It watches the bridge.                                                                 |
| AIMING         | 1.2     | It turns its head to the road.                                                         |
| WARNING        | 1.8     | It rears up, wings spread, throat glowing, roars; the burn zone glows red on the road. |
| BREATHING_FIRE | 2.0     | A roaring stream of fire from its jaws; flames fill the zone.                          |
| COOLDOWN       | 1.0     | The fire dies down.                                                                    |

The period is 9 s (`period`, `offset`, `aim`, `warn`, `breathe`, `cool` on the `dragon`
entity in track.json). Only BREATHING_FIRE hurts, and only inside the zone's box (16 m
along the road, the road's full width, 6 m high), which is exactly where the flames
are drawn. A kart caught in it gets **the same burning bounce as lava**: the hazards
module has one shared `burn()` (the bounce, the push back towards the road, the speed
penalty, the immunity after, and three burns in 8 s puts you back at the checkpoint),
with the same tuning numbers (`tuning.json` `hazards`), unchanged.

## The eruption and atmosphere

- `eruption` entity (`src/game/hazards.ts`): every 12 s of the race clock, a rumble,
  then a blast of glowing lava bombs out of the crater and a red flash of light; a
  fountain of fire in between. Purely visual.
- `ashfall`: grey ash drifting down and embers floating up round the camera.
- `steam`: fissures venting steam up the ascent and in the caverns.
- `campfire` entities on the burning trees (smoke and embers), `torch` entities on the
  braziers (the four nearest flicker real light), lava glow painted onto the rock round
  every river, pool and fall, the caverns dark but for their lava, braziers and (in the
  gallery) violet crystal light.
- The **Volcanic Apocalypse** theme: a smoke-filtered blood-red sunset low in the sky,
  dark crimson haze from 230 m, and 17 new textures (obsidian, veined obsidian, magma
  rock, basalt masonry and runes, scorched ground, ash soil, cave rock, lava falls, fire
  and amethyst crystals, charred bark, burning foliage, ash smoke, furnace glow).

**Music:** "Ember Peak" (`ember` in `src/audio/songs.ts`), D minor, 160 BPM, 128 beats:
low brass over a hammering marimba, heavy toms and a galloping bass, then strings and
brass soaring together. Sound effects: the dragon's roar and fire (`sfx.roar`,
`sfx.flame`) and the eruption's rumble (`sfx.rumble`).

## How it's built

Everything is in `tools/blender/prehistoric/`, on the course kit:

- `ember_peak.py`: the volcano's shape (`cone`, `land`), the route through the eight
  sections as waypoints, the lava rivers and pools, the road kinds (railed cliff roads
  and bridges), the terrain and hidden floors, the gameplay (6 zippers, 9 egg rows, 9
  balloons, respawn zones for the two bridges, checkpoints).
- `ember_scenery.py`: the volcano's core (its heart, a separate rock with the caverns cut
  through it: edit it in Blender), the lava, flank streams, the crater and plume, the
  distant volcanoes, the dragon's crag, the Mouth, the bridge piers and arches, the
  caverns' dressing, obsidian, the burning forest, ruins, lava falls, the painted light,
  and the dragon, eruption, ash and steam entities.
- `volcano_props.py`: the volcanic kit (obsidian spires, clusters, slabs and arches,
  ruin pillars, braziers, stalactites, cave columns, crystals, burnt pines and palms,
  smoke plumes, far volcanoes, the crag).

Run `python tools/blender/prehistoric/ember_peak.py` (with the bpy module) to rebuild
`tracks-src/ember_peak.blend` and `public/tracks/ember_peak/`.

**Tests:** `tests/ember.test.ts` (in Dinosaur Valley with its own music, a real
climb, 15-25 s in the caverns, the dragon and the eruption), `tests/dragon.test.ts`
(the schedule, fairness, the zone, and the shared burn), `tests/holes.test.ts`, and
`tests/prehistoric.test.ts` (three clean AI laps; Ember's lap limit is 120 s).
