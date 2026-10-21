# Desert World

Sun-baked red-rock country: vast canyons, towering mesas, hidden oases and the ghost
towns of the old frontier. Its courses so far are **Canyon Dash** (the great canyon)
and **Oasis Haven** (the resort paradise). Two more are planned, and they're shown in
track select as "Coming Soon": a haunted ghost town and an underground adventure.

All of it is our own design: the layout, the scenery, the props and the music were made
for this project. The concept art was only a guide to the mood and colours.

## Canyon Dash

A short, fast lap of about 1.8 km (an AI lap is about 80 s) round one great canyon on a
clear desert afternoon turning golden. The canyon has two tiers:

- **The outer canyon:** the plateau's rim, a stepped wall, then a broad sandstone
  terrace.
- **The inner gorge:** cut into the terrace, with a turquoise river 60 m down. At its
  head the twin falls pour in.

The lap runs clockwise round the gorge.

| Section | Name                     | What happens                                                                                                                                                                                                                                                                          |
| ------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1       | The Canyon Overlook      | The start, on the south rim's plateau at a desert racing outpost: a chunky timber start arch with banners and a checkered board, banner poles, braziers, a windmill, a lookout tower, a water tank and crates. The canyon drops away on the right, and the bridge is in the distance. |
| 2       | The Great Canyon Descent | Off the rim onto a road carved into the canyon's south wall. It runs down broad, banked cliffside corners (56 m down to 26 m), over a timber trestle across a side ravine, with timber struts under the ledge.                                                                        |
| 3       | The Sandstone Arch       | Round the great cliffside bend, the arch comes into view ahead. It's a 54 m span springing from the terrace on the canyon side and into the rim's cliff on the other, framing the canyon as it opens west to the horizon. The road runs right under it, flat out.                     |
| 4       | The Great Canyon Bridge  | A banked turn onto a long timber bridge 60 m over the inner gorge. It has masonry piers rising out of the river, timber towers, lattice trusses under the deck, and banners on timber portals at both ends. Waterfalls spill off the terraces downstream.                             |
| 5       | The Red-Rock Pass        | A broad banked turn east, then a winding slot between towering walls cut into the north mesa, and a short natural tunnel with a shaft of daylight through its roof.                                                                                                                   |
| 6       | The Waterfall Overlook   | Out along the gorge's north rim, with the great waterfall straight ahead. Round the canyon's head the road crosses a stone bridge between the twin falls: on the left, the river leaps off the East Shelf; on the right, it plunges 80 m into the gorge.                              |
| 7       | The Mesa Run             | South and west across the open eastern plateau between towering buttes and spires, then round a great butte. Or take the shortcut through the narrow slot in it.                                                                                                                      |
| 8       | The Final Sprint         | Rising back to the rim, the start arch ahead, a broad drifting corner onto the finish straight.                                                                                                                                                                                       |

**The shortcut:** the Butte Slot is a narrow, kinked slot straight through the great butte
on the Mesa Run, with a boulder wedged high above. It's shorter than the road round, but
narrow. A twin gate in the slot counts it as the stretch it skips. The AI keeps to the
main road.

**Driving:**

| Surface       | What it is                  | How it drives                                   |
| ------------- | --------------------------- | ----------------------------------------------- |
| `packed_dirt` | the road                    | full speed, a touch less grip than asphalt      |
| `dirt`        | the verges and rock shelves | a little slower                                 |
| `loose_sand`  | the sand off the road       | slower (74%), but not a trap like `sand`        |
| `abyss`       | the gorge's floor           | a fall into the gorge puts you back on the road |

Every edge with a drop has a ranch fence.

**Boosts and pickups:** eight zippers, nine banana rows and fourteen balloons.

**Living desert:**

- reddish dust trails behind every kart on dirt and sand;
- dust blowing across the land on a gusting breeze;
- the windmill turning;
- birds circling over the canyon;
- waterfall spray and roar;
- braziers flickering at the start.

**Look:** the `canyon_dash` theme has:

- a saturated blue sky with big white clouds;
- a low golden sun from the west-south-west;
- a far skyline of flat-topped mesas and buttes (the sky dome's new `"style": "mesas"` hills);
- pale lavender haze far off;
- deep blue-violet shadows down in the canyon (painted into the rock).

The rock is in layers: cream caprock, orange and red sandstone, red shale and a
purple-brown base. Each wall shows them as clean bands and ledges.

**Music:** "Canyon Dash" (`canyon` in `src/audio/songs.ts`), D minor, 168 BPM. It's a desert
gallop:

- brass and flute trade the tune;
- strings come in for the bridge and the falls;
- under them: a clip-clopping woodblock, strummed pizzicato, a rolling marimba, bongos
  and a galloping bass.

### How it's built

- **Course script:** `tools/blender/prehistoric/canyon_dash.py` holds the layout, the
  heights, the land, the shortcut and the road kinds.
- **Scenery:** `canyon_scenery.py` builds the river, the falls, the arch, the buttes,
  the tunnel, the bridges, the outpost, the plants, the light and the entities.
- **Props:** `canyon_props.py` holds the saguaros, barrel cacti, agaves, sagebrush, dry
  grass, desert trees, boulders, hoodoos, chevron signs, braziers, banner poles, the
  windmill tower, the lookout tower, the water tank, and the crates.
- **Wall meshes:** `canyon_walls.py` builds the inner gorge and the outer canyon's rim
  walls as meshes that follow the cliffs, a cross-section every few metres. Each rock
  layer is a clean band and each ledge a clean step; a height-field grid can only
  stair-step a wavy cliff. The land grid leaves holes where they stand. Far downstream,
  the walls are only drawn and have no collision.
- **Far land:** a coarse, visual-only land runs out to the horizon, with the canyon
  continuing west and big mesas all round.
- **Safety floors:** an invisible abyss floor lies under the whole gorge, so a fall
  anywhere into it puts you back on the road. An underfloor everywhere else means no
  kart can fall through the world.

Re-run the course with `python tools/blender/prehistoric/canyon_dash.py` (the bpy
module). Paint the textures with `python3 tools/blender/prehistoric/make_textures.py`.

### Tests

- `tests/canyon.test.ts` checks:
  - the world, the theme, the music and the surfaces;
  - that the track loads cleanly, with all its entities and the slot's twin gate;
  - that the slot counts as the stretch it skips;
  - three AI laps of 60–85 s with no falls;
  - the dust, wind, windmill and bird rules.
- `tests/holes.test.ts` checks that there are no holes in the world.

## Oasis Haven

The desert's paradise: a sun-drenched resort round a great turquoise lake in a basin of
golden sand and cliffs, red mesas beyond. A lap of about 2.1 km (an AI lap is about 90
s), anticlockwise round the lake on a perfect summer afternoon.

**Water is the lifeblood of it all.** A spring in the palace gardens, high on the north
shore, feeds everything you see:

- It runs east and west along the palace terrace in stone channels.
- It falls down the terraces in two great three-tier cascades, east and west, into the
  lake.
- A central stream crosses the second terrace into an aqueduct over the terrace road,
  pours through a slot in it as a curtain you drive through, and falls into the lake.
- The pavilion island's fountain spills off its rim in little falls.
- The lake runs into the market in canals.

Lush gardens grow where the water is, and give way to sand and scrub beyond.

| Section | Name                       | What happens                                                                                                                                                                                                                                                        |
| ------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1       | The Grand Resort Entrance  | The start, on a raised plaza at the south shore under a great sandstone gateway with domed towers, banners and a checkered board, fountains either side, cafés and shops. The lake, the pavilion and the palace are ahead across the water. Down to the waterfront. |
| 2       | The Great Lagoon Promenade | Sweeping drifts along the south and east shores on a tiled promenade, the lake on the left all the way, the pavilion, bridges, falls and boats across the water.                                                                                                    |
| 3       | The Waterfront Market      | A tighter run between market halls (arcades, domes, towers), stalls under striped awnings and waterfront cafés, over two canals with boats moored in them and fountains at their ends.                                                                              |
| 4       | The Grand Arched Bridge    | West across the lake on stone arches, rising to a crown and down again, banners and flower urns along the parapets, a broad drifting turn off it.                                                                                                                   |
| 5       | The Central Pavilion       | Round the blue-domed pavilion on its island (a colonnade, a great dome with turrets, a fountain inside, gardens, little falls off the island's rim), then north over the causeway.                                                                                  |
| 6       | The Waterfall Terraces     | Up the terraced gardens: through the aqueduct's waterfall curtain, then round a broad climbing turn beside the great east cascade. The terrace walls are tiers of arcades.                                                                                          |
| 7       | The Palace Heights         | Along the foot of the palace (a great hall under a vast blue dome, wings, towers and galleries round the spring garden), through its gateway, the whole lake below.                                                                                                 |
| 8       | The Lakeside Return        | Down the west shore past villas, round the beach headland (umbrellas, loungers, a conga line), or straight on through the canal passage under the beach hotel: the shortcut. Back to the gate.                                                                      |

**The shortcut:** the Canal Passage. Where the road swings out round the beach headland,
the passage goes straight on, under the arcade of the beach hotel, beside a canal that
runs through the headland. It's narrower, and a little shorter. A twin gate counts it as
the stretch it skips. The AI keeps to the main road.

**The living resort:**

- the lake's living water (below);
- thirteen waterfalls with spray and roar;
- fountains whose jets arc and splash;
- five sailing boats going round the lake with wakes behind them;
- gulls wheeling over the water;
- palm fronds, flowers, banners and awnings swaying in the breeze;
- dinosaur guests dancing and waving in the plaza, the market, the pavilion and the
  palace gardens, and a conga line on the beach.

**Living water:** the lake and canals use the new `lagoon` material effect
([materials.md](materials.md)):

- the surface rolls in a few travelling waves;
- bright ripple lines play over it;
- the sun glitters off the waves in winking sparkles;
- low angles take on the sky's sheen.

The depth is painted into the water mesh's vertex colours: bright, pale turquoise over
the sandy shallows, deepening to rich blue. Foam laps at the natural shores and round
the island.

**Driving:**

- **The roads:** cream flagstones with a blue-tiled border and stone balustrades, full
  grip.
- **Off the road:** the lawns are grass and the sand is loose sand.
- **The water:** the shallows are slow water. The deep lake fishes you out back on the
  road after a moment.

**Music:** "Oasis Haven" (`oasis`), A major, 150 BPM: a carefree holiday tune.

- Steel pan and flute trade the tune, with strings over the falls.
- Marimba and bells run up and down the chords like sparkling water.
- A bouncy bass, congas, shaker and tambourine keep the groove.

**How it's built:**

- `oasis_haven.py`: the layout, heights, the lake's outline (from the roads), the
  canals, the terraces, the land, the shortcut.
- `oasis_scenery.py`: the land, the lake and foam, the water system (the spring,
  channels, cascades and aqueduct), the architecture helpers (blocks, towers, domes,
  gates), and the gameplay.
- `oasis_resort.py`: the start gate, the road dressing, the bridges, the pavilion, the
  market, the terraces, the palace, the beach hotel, the resort districts, gardens and
  rocks.
- `oasis_props.py`: palms, cypresses, flowers, lanterns, banners, stalls, cafés, beach
  sets, boats, fountains, kiosks.

**Tests:** `tests/oasis.test.ts` checks:

- the world, the theme and the music;
- a clean load with living water, swaying plants, the falls, fountains, boats and their
  paths, and the guests;
- that the passage counts as the stretch it skips;
- three AI laps of 75–100 s with no falls into the lake;
- the boat and fountain rules.

`tests/holes.test.ts` covers it too.
