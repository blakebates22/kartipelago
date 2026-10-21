# Desert World

Sun-baked red-rock country: vast canyons, towering mesas, hidden oases and the ghost
towns of the old frontier. Its first course is **Canyon Dash**. Three more are planned,
and they're shown in track select as "Coming Soon": a desert oasis, a haunted ghost
town and an underground adventure.

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
