# Dragon Kingdom

The fourth world (`dragon` in `src/game/worlds.ts`): a sunlit kingdom of karst islands
in a turquoise lagoon, ruled by dragons. Festival towns, temple gardens, waterfalls and a
royal palace on its mountain, all watched over by a great jade dragon. Four courses:
Dragon Isles, Dragon Canyon, Snow Dragon Pass and the grand finale, Celestial Dragon
Festival.

The look is joyful and readable: blue and gold tiled roofs, red pillars, lanterns and
banners, blossom, bright water. Underneath there is a small, quiet unease, never more
than a hint. The royal emblem is everywhere. Statues face the road. Guards stand in
perfect formation and never move. A royal gate on a side street is shut, and a doorway
in the harbour opens onto a dark corridor. When the dragon's shadow passes, the crowd
falls quiet and bows all together. The kingdom has no prisons, chains, propaganda or
red skies.

All designs are our own. The concept art was mood only.

## Dragon Isles

A lap of about 2.7 km (an AI lap takes about 118 s, or about 114 s through the Courtyard
Passage). It's one continuous circuit. The road starts in the valley, climbs the cliffs
to the highland, runs along the karst spine over the lagoon, drops to the harbour, goes
through the headland and comes back to the palace gate.

| Section | Name                           | What happens                                                                                                                                                                                                                                                 |
| ------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1       | The Grand Ceremonial Gate      | The start, on the royal carpet, under a great gold-roofed gate between jade and gold dragon statues. Banners, bunting and cheering crowds line the road, and the palace stands on its mountain straight ahead.                                               |
| 2       | The Riverside Festival Village | Market streets of shops, stalls and houses, with lanterns strung across the road and crowds behind red rails. The road crosses a canal bridge. A mill wheel turns and sampans are moored. On the waterfront square, dancers and drummers play round a stage. |
| 3       | The Cliffside Ascent           | Up the north cliffs on stone ledges, round a hairpin and through a short tunnel in a rock outcrop. Falls drop off the great karst wall, and there are pines, lookout pavilions and stone lanterns. Across the valley you can see the dragon.                 |
| 4       | The Great Waterfall Bridge     | A stone bridge on tall piers across the turquoise gorge. The great falls thunder up the gorge, with a smaller fall from each wall either side of the bridge and dragon statues at both ends.                                                                 |
| 5       | The Temple Gardens             | Round a U-shaped bend through the temple's gardens: a seven-storey pagoda, lotus pools, pavilions, blossom and bamboo. Gates frame the road, guardian statues face it, and the temple guards stand in a row before the hall.                                 |
| 6       | The Sky Paths                  | South along a spine of karst pillars, from pillar to pillar on high bridges over the lagoon. Towers stand in the water all round. On the long bridge the dragon passes straight overhead.                                                                    |
| 7       | The Lantern Harbour            | Down to the boardwalk past the harbour town and its docks, with junks and sampans moored and lanterns strung overhead. Junks sail the lagoon and a dragon boat floats offshore. Then over the harbour bridge.                                                |
| 8       | The Ancient Dragon Passage     | A carved tunnel through the headland under the royal emblem: lanterns along the walls, old carvings glowing faintly teal, and a great round sealed door with one guard beside it.                                                                            |
| 9       | The Grand Reveal               | Out onto the overlook. The whole kingdom opens up, with the palace far to the north.                                                                                                                                                                         |
| 10      | The Royal Approach             | Down the royal avenue between guards in formation, statues, banners, walls and halls, with crowds bowing.                                                                                                                                                    |
| 11      | The Palace Finish              | Under the Royal Gate and onto the line.                                                                                                                                                                                                                      |

**The Courtyard Passage (the shortcut).** Where the main road swings south round the
temple's U, the passage goes straight on through the temple courtyard. It passes
between two gates, below the main hall and its guards. It counts as the stretch it skips
(a twin gate), it is narrower (11 m), and it saves about 4 s if you drive it well.

**The great dragon** (`isles_dragon`) is scenery: it never touches a kart. A long jade
serpent with a gold belly and crest, antlers, whiskers, a mane and four clawed legs, it
flies a loop keyed to your progress round the lap. It hurries when it's behind,
glides when it's ahead and never flies backwards. That way it meets the race at set
moments, whatever your pace:

- circling the palace as the race starts;
- across the valley from the cliff road;
- over the great falls as you reach the bridge;
- behind the temple;
- straight overhead on the long Sky Path bridge;
- low over the harbour, its shadow sweeping the road;
- heading back to the palace as the kingdom opens up below the overlook.

Its body follows the path its head has flown, with a ripple running down it. When it's
near, it turns its head toward you, its shadow crosses the ground under it, and now and
then it calls (a deep gliding horn: wonder, not menace). As it passes, the villagers
near it stop and bow together, and the festival's sound hushes.

**Villagers** (`villagers`): about 500 people, drawn as one instanced crowd. They cheer
and wave, merchants gesture at their shops, dancers circle on the square, musicians
drum, fishers hold their rods on the docks, gardeners bend over the beds, guards stand
perfectly still, and the temple and royal crowds bow now and then. Only those near the
camera are animated.

**Other life:**

- a mill wheel turning;
- little dragons (one red, one blue) looping round the pagoda and over the Sky Paths;
- junks sailing the lagoon;
- gulls and birds;
- blossom petals drifting over the square and the temple;
- spray at the great falls;
- teal motes in the passage.

**The air:** an `atmosphere` entity blends fog, light and sound along the lap. Each
part has its own bed of sound:

| Part                        | Sound                                                        |
| --------------------------- | ------------------------------------------------------------ |
| Festival (gate and village) | a crowd's murmur, with gongs, drum rolls and plucked phrases |
| Cliffs                      | the falls' roar                                              |
| Temple                      | a breeze and a faint bell hum, with birds                    |
| Sky Paths                   | the wind                                                     |
| Harbour                     | waves and gulls                                              |
| Passage                     | almost silence, with drips                                   |

The light is a sunlit late morning with a distant blue haze. The sky dome's hills are
the new `karst` style: tall rounded towers instead of mesas.

**Music:** "Dragon Isles" (`dragon`), G major pentatonic, 152 BPM.

- The bamboo flute leads through the festival over plucked strings.
- The market skips along on plucked strings and xylophone.
- Bells and celesta sing the dragon's broad theme over held strings.
- Brass and flute bring it home to the palace.
- Festival drums, bongos and a gong-like crash play throughout.

## How it's built

- `tools/blender/prehistoric/isles_land.py`: the land as plain data (no Blender):
  - the layout and heights;
  - the valley, the stepped northern highland, the gorge, the karst spine, the harbour
    shore, the headland's shelf and the great west wall;
  - the canal;
  - the shortcut line;
  - the zones.
- `dragon_isles.py`: the route and its road kinds. Bridges are found where the ground
  falls away.
- `isles_scenery.py`:
  - the land mesh and its underfloor, and the far kingdom (mountains, the palace's peak);
  - the headland and the outcrop, with their tunnels bored through;
  - the lagoon, the far sea and the gorge river;
  - the light (sun, dim tunnels, warm round lanterns, teal round the carvings);
  - the checkpoints, the shortcut's twin gate, zippers, bananas and balloons.
- `isles_town.py`: each section's buildings and dressing, the palace, the waterfalls,
  the crowd's places and roles, the dragon's keys, boats, birds and the air.
- `isles_props.py`: halls, pagodas, pavilions, houses, shops, stalls, walls, gates, the
  closed royal gate, the dark arch, the sealed door, dragon and guardian statues,
  lanterns, lantern strings, bunting, banners, the emblem plaque, the drum stage,
  blossom, pines, bamboo, hedges, karst towers, junks, sampans, the dragon boat, docks,
  the mill, lotus pools and footbridges.
- `isles_textures.py`: the textures and the `dragon_isles` theme.
- Game side:
  - `src/game/isles.ts`: the rules (the dragon's flight, villager poses, awe);
  - `src/game/islesLife.ts`: running them;
  - `src/render/islesFx.ts`: the serpent, its shadow, the crowd and the mill wheel.

Props are merged by map square: all the buildings share one collection, so each square
is a single merged mesh. The far karst towers merge into a few big meshes.

## Tests

`tests/isles.test.ts` checks:

- the world, theme and music;
- a clean load with the whole kingdom and every villager role;
- that the lap runs through the festival, cliffs, temple, Sky Paths, harbour and passage
  in order;
- that the dragon flies forwards only, keeps pace with the race, never comes within
  12 m of the road, and passes straight over the long bridge;
- that villagers bow together and guards never move;
- that the Courtyard Passage counts as the stretch it skips and is a real short cut;
- three AI laps of 100-130 s with no falls.

`tests/holes.test.ts` covers it too.

## Dragon Canyon

The kingdom's desert frontier at golden hour, and the most technical, drift-hungry lap in
the game: about 2.2 km (an AI lap is about 94 s), turning harder per kilometre than any
other course, with five 180° hairpins. Red sandstone ledges, a turquoise river far below,
cliffside fortresses, red banners and flaring braziers under a low orange sun.

| Section | Name                      | What happens                                                                                                                                       |
| ------- | ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1       | The Canyon Outpost        | The start, under the fortress's Dragon Gate between stone dragons. Guards on the walls, a caravan and workers by the road.                         |
| 2       | The Cliffside Hairpins    | Right onto the bottom ledge, then two stacked hairpins (left, right) climbing the cliff: each ledge 8 m over the last, the next one visible above. |
| 3       | The Great Canyon Descent  | Off the top ledge onto the Canyon Bridge, the Great Falls dropping into the gorge beside it, then down the far wall.                               |
| 4       | Dragon Skeleton Pass      | Left-right-left under the ribs of a colossal dragon, its skull jutting from the east wall, its spine running off along the cliff.                  |
| 5       | The Imperial Quarry       | Round the loading yard: treadwheel cranes lifting blocks, stacks of cut stone, scaffolds and a cargo lift on the cliffs, tired workers, guards.    |
| 6       | The Winding Caverns       | A torchlit tunnel bending through the mesa; barred side passages leak a warm glow from sealed chambers.                                            |
| 7       | The High Bridges          | Out over the chasm and the River Sprint below, sweeping round the Lone Spire.                                                                      |
| 8       | The Hidden Oasis          | Down round a palm-fringed pool, its little village, stalls and mill wheel.                                                                         |
| 9       | River Canyon Sprint       | North along the river, fast, under the High Bridges and an old aqueduct.                                                                           |
| 10      | The Watchtower Ascent     | Over the river and up two hairpins round the imperial watchtower; the dragon glides low over it, its shadow across the road.                       |
| 11      | The Final Twist           | Snapping left and right off the tower's ledge, over the crest and round the Dragon's Coil hairpin, a giant dragon statue at its heart...           |
| 12      | Return to the Dragon Gate | ...and back onto the straight under the gate.                                                                                                      |

**Built for drifting.** Every corner was sized for the current drift (tight arc 26 m,
hands-off 42 m): hairpins are 30 m on the centre line on 16 m roads, so a full drift fits
with room for the entry swing; sweepers sit inside the hands-off arc; the S-bends are
spaced so one drift's exit sets up the next. Drifting raises top speed by 15%, so the
fastest lap is the one that spends the most time drifting. The AI drifts about half the
lap and is faster for it, though only by about a second: it drifts cautiously, and a
player chaining drifts through the hairpins and the Final Twist gains much more. Zippers
sit on the exits worth chaining (off the hairpins, onto the bridges, out of the oasis and
the Dragon's Coil). Barriers line every edge: mistakes cost speed, not falls.

**The Quarry Service Road (the shortcut):** off the Skeleton Pass's last bend, straight
through the loading yard under a stone arch, back onto the road where it turns into the
mesa. It's narrow (8 m), dusty (a dirt surface, a little slower) and saves about half a
second if you hit it cleanly; it counts as the stretch it skips (a twin gate).

**The unease:** stronger than in Dragon Isles, still quiet. The quarry's workers are
dusty and stooped, hewing and hauling under guards; a barred door leads somewhere
restricted; the caverns' side passages are sealed, with light behind them. The dragon is
still majestic, but here it watches: its low pass over the watchtower casts its shadow
across the road. No prisons, chains or villains.

**Life:** the dragon (`isles_dragon`, keyed to the lap), workers and haulers pacing with
their loads, guards on the walls and the tower, oasis villagers, crane loads rising and
falling (`crane`), the oasis mill wheel, little dragons over the skull, birds, dust behind
the karts and blowing across the road (`dust`, `dustwind`), waterfalls, flickering
braziers and torches.

**The air:** golden-hour sun low in the west; the canyon's depths in cooler shade.
Sounds: wind on the ledges, falls in the gorge and along the river, the quarry's drone
with chisel strikes, near-silence and drips in the caverns, birds at the oasis.

**Music:** "Dragon Canyon" (`dragon_canyon`), D minor, 168 BPM: a galloping flute over
plucked strings, the quarry's low brass and marimba, strings soaring over the High
Bridges, flute and xylophone racing through the Final Twist; toms, bongos and shaker.

**How it's built:** `dcanyon_land.py` (pure data: the corners as fillets, heights,
widths, the river, the basin, the Service Road, zones), `dragon_canyon.py` (route and
road kinds; bridges found where the ground falls away), `dcanyon_scenery.py` (land, far
desert, the caverns' mesa, river and pool, falls, light, gameplay),
`dcanyon_town.py` (every section's dressing, the people, the dragon's keys, the air),
`dcanyon_props.py` (spires, buttes, braziers, turn boards, fortress, watchtower, skull,
ribs, vertebrae, cranes, block stacks, scaffolds, carts, tents, lift, chamber doors,
aqueduct), `dcanyon_textures.py` (18 textures and the `dragon_canyon` theme). The game
side reuses Dragon Isles' runtime, with new `worker` and `hauler` villagers and the
`crane` entity. `course_kit.road_height` now lets the land meet a road that runs under a
bridge (the River Sprint under the High Bridges).

**Tests:** `tests/dcanyon.test.ts`: the world, theme and music; a clean load with the
frontier's life; the twistiest course per km in the game with at least five hairpins;
roads that never touch where they cross over and under; the Service Road counts; three
AI laps of 80-110 s with no falls; drifting faster than steering. `tests/holes.test.ts`
covers it too.

**Polish next:** a richer quarry (moving carts on rails, more scaffolding up the faces);
the cliffs' terracing between the hairpins (retaining walls, more ledge detail);
sharper sandstone strata; the dragon skeleton's ribcage could close over the road more
dramatically; side passages you can glimpse further into; the AI's drifting (it leaves
time on the table in S-bends).

## Snow Dragon Pass

The kingdom's highest mountains in a blizzard, and the first course where **the lap
splits**. Half of it is shared road; the other half is a choice of two roads at each of
two splits, four whole laps in all (about 2.31-2.38 km, an AI lap about 98-101 s).
Slate-grey peaks buried in snow, frozen turquoise falls, a blue ice cavern, a monastery in
whitewash and red, villages in weathered timber, and above it all the Dragon Citadel
blazing gold. It is the third chapter of the kingdom's story: the people are suffering.

| Part | Name                   | What happens                                                                                                                                                                                                                                                                                          |
| ---- | ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | The Frozen Gate        | The start, just past the citadel's ceremonial gate: guardian dragons, braziers, banners, guards on the walls; the Frozen Gate over the straight. The citadel towers above on its crag.                                                                                                                |
| 2    | The Windy Village      | Down through the village: snow-buried houses with warm windows, families huddled round small fires, a ration line at a bare stall under guard, prayer flags across the street.                                                                                                                        |
| 3a   | The High Cliff Road    | (Main.) A switchback up the mountain's face, along an exposed ledge past the colossal Dragon Overlook statue, down to the crossing. Narrow (14 m), tight, parapets and turn boards.                                                                                                                   |
| 3b   | The Frozen Supply Road | Round the mountain's foot past the full storehouses (guarded), sledges hauled to and fro, workers at the sacks, people sheltering under tattered awnings; through the blue ice cavern. Wide (18 m) and flowing.                                                                                       |
| 4    | Starvation Road        | The shared supply corridor: a long line of people at an empty storehouse; across the road, the royal storehouses stacked to the rafters, guarded, banners flying; fires, empty stalls, houses half buried.                                                                                            |
| 5    | The Broken Bridges     | Over the frozen gorge on the road's own bridge, ruined bridges either side, icicles hanging from their broken ends, the gorge's frozen falls.                                                                                                                                                         |
| 6    | The Avalanche Run      | Down the windswept pass, the storm at its fiercest; avalanches pour down the far slopes on the race clock's beat.                                                                                                                                                                                     |
| 7a   | The Monastery Ridge    | (Main.) A switchback up round the mount, east over the monastery's bridge (the aqueduct runs beneath), under its ceremonial gates, past the monastery itself (halls, chortens, bells, prayer flags, silent monks all looking across to the citadel), and a steep descending exit.                     |
| 7b   | The Frozen Aqueduct    | Straight on and down along the old water channels (a frozen channel beside the road), under the monastery's bridge, past frozen falls and the aqueduct's arches, a tunnel bend through the crag. Faster.                                                                                              |
| 8    | The Final Ascent       | Up past pairs of guardian dragons and walls lined with guards, braziers and banners whipping in the wind, toward the citadel; the ice dragon comes down out of the cloud and passes low over the road, its shadow sweeping the snow, then away to the citadel; under the ceremonial gate to the line. |

**The network.** Each split's two branches leave the shared road along the same line out
of its last corner (one turns away while the other runs on, a Y) and come back along the
same line into the next shared corner, so the shared road is exactly the same whichever
way you came. The main route (the one the game's track, checkpoints and placements are
measured along) is Cliff + Ridge; `track.json`'s `lapRoutes` lists the other three
combinations, each a whole closed route in `route.json`:

- Rivals are spread across the four laps (rival i drives lap route i mod 4, always the
  same one, so races repeat). Each drives its own racing line.
- Pickups can sit on a branch: a zipper, egg row or balloon with `"route": "<lap id>"` is
  placed along that lap route instead of the main one.
- Zipper pads now need you within a few metres of their height, so a pad on a lower road
  never fires for a kart on the bridge above it.

**Route balance (computer racers, flying laps):**

| Lap                                 | Time     | vs fastest |
| ----------------------------------- | -------- | ---------- |
| High Cliff + Frozen Aqueduct        | ~98.3 s  | fastest    |
| High Cliff + Monastery Ridge (main) | ~99.0 s  | +0.7%      |
| Supply + Aqueduct                   | ~99.8 s  | +1.5%      |
| Supply + Ridge                      | ~101.3 s | +3.0%      |

The Cliff Road is shorter but narrower and tighter; the Supply Road is wider and longer.
The Aqueduct is shorter and flowing; the Ridge climbs through switchbacks. These are the
current AI's times, measured with its own physics: a skilled player's gains on the
technical roads will differ, and the AI is due to be rewritten. Only playtesting will
settle the real balance.

**Checkpoints on every branch.** The add-on's generator places the shared road's gates
(none inside the splits); then each branch of each split gets four gates at the same
shares of its length, numbered together with the other branch's (a pair: crossing
either counts the same). Each branch's gate respawns you on that branch, and every gate
is nudged clear of any other road at about its height (the monastery's bridge over the
aqueduct). Dropping from a high road to a low one gains nothing: the next gate in order
is still needed.

**Junctions.** Where a branch leaves or joins, neither road has rails of its own; a rail
runs round the outside edge of the two together (wherever one road's edge isn't inside
the other's surface), so the junction is open between them and closed to the drops
beyond. A branch sits 5 cm below the main road where they overlap (the main road shows).
A signpost in the gore points both ways: either road is the race.

**The story, told by the places.** Hungry villagers queue at bare stalls and huddle round
small fires; guards stand before storehouses stacked to the rafters; workers haul sledges
through the snow; the citadel's every window blazes gold above the freezing villages; the
monks stand silent, all looking across at it; the ice dragon, majestic in Dragon Isles,
here feels like a ruler passing over its kingdom. No violence, no villains, nothing
explained.

**The blizzard** (`src/game/snow.ts`, `snowLife.ts`), all visual, never touching a kart:
veils of snow sweeping across the distance (camera-centred cylinders with streaks
drifting on them), driving snow in the middle distance, a few flakes whipping past the
camera, powder blowing low across the road. How hard it snows is set per place (`blizzard`
keys: fiercest on the exposed heights, gentle in the village, none in the tunnels) and
the storm ebbs and gusts on its own slow rhythm. The fog closes to 800-1050 m, never so
close a bend disappears. Prayer flags flap in the wind (`prayer_flags`), the monastery's
bells sway and toll (`bells`), avalanches pour down the far slopes on the race clock's
beat (`avalanches`): predictable and never on the road.

**People:** about 110: `queue` (shuffling in the ration lines), `huddle` (crouched round
the fires), `monk` (hooded, still, heads bowed), plus the canyon's `worker`, `hauler` and
`guard`. Winter wool and maroon robes (`render/islesFx.ts`).

**The air:** zones for the gate, village, cliff, supply road, cavern (blue and dark),
starvation road, gorge, avalanche run, monastery, aqueduct, tunnel and ascent. Sounds:
a howling `blizzard` on the heights, wind elsewhere, the monastery's `bells` (a chanted
drone and the bells tolling), drips in the cavern and tunnel, distant avalanches.

**Music:** "Snow Dragon Pass" (`snow_dragon`), B minor, 150 BPM: bells and celesta over a
pulsing drone in the storm, strings lamenting through the village and the ration lines,
low horns and toms for the ice dragon, flute and strings climbing to the citadel.

**How it's built:** `snow_land.py` (pure data: the network's sections, the four laps,
heights with level junctions, widths, the mountains, the gorge, the branches and zones),
`snow_dragon_pass.py` (the main route and its road kinds; bridges where the ground falls
away or a branch passes under), `snow_scenery.py` (the branch roads, junction rails, land
and far peaks, the tunnels' crags, the gorge, the lap routes, checkpoints, pickups,
light), `snow_town.py` (every part's dressing, the people, the dragon's keys, the air and
the weather), `snow_props.py` (houses, ration stalls, storehouses, sledges, sacks, pines,
chortens, monastery halls, flag poles, bells, citadel towers and hall, icicles, broken
arches, fork signs, guard posts, ice), `snow_textures.py` (20 textures and the
`snow_dragon_pass` theme).

**Tests:** `tests/sdp.test.ts`: the world, theme and music; a clean load with its people,
weather and dragon; the blizzard's strengths and the avalanches' beat; about half of
every lap shared; paired checkpoints on every branch, respawning on the branch; falling
off a branch puts you back on it; roads that never touch where they pass over and under;
all four laps driven cleanly by the AI, Cliff + Aqueduct fastest by 0.2-3.5%.
`tests/holes.test.ts` covers it too.

**Limits and polish next:** there is no minimap in the HUD yet, so the splits are shown
by the fork signs only. The AI picks its lap at the start rather than choosing at each
fork. The balance is the current AI's; a player's needs playtesting. The blizzard's
veils are simple cylinders: from some angles their edges show. The monastery and citadel
read well from the road but would reward a closer look (stairs, more buildings). Lanterns
don't swing yet.

## Celestial Dragon Festival

The kingdom's grand finale, and the most spectacular course in the game: its sacred heart
on the night of its greatest festival. A lap of about 2.7 km (an AI lap about 114 s) round
the Palace Mount, at night under a sky of stars and a crescent moon, while the whole
kingdom celebrates its dragon ruler, and the sky fills with fireworks, more every lap. It
closes the kingdom's story: the beauty and the riches are all here, and after the canyon's
labour and the pass's hunger, the worship feels a little too much.

| Part | Name                    | What happens                                                                                                                                                                                       |
| ---- | ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | The Festival Gate       | The start on the gate's terrace: the great ceremonial gate, colossal golden dragons, grandstands packed with the crowd, banners, braziers, lanterns strung across the broad straight, drum stages. |
| 2    | The Lantern Market      | Sweeping down through the night market to the water: shops, stalls, lantern strings and bunting, dragon floats parked for the procession, dancers and musicians.                                   |
| 3    | The Waterfall Bridge    | North over the lagoon's inlet on a long white bridge, waterfalls pouring off the mountain beside it, pagodas on the islands, lantern boats sailing beneath.                                        |
| 4    | The Dragon Promenade    | West across the great plaza of worship: the altar and its glowing mural of the dragon among the stars, two colossal golden dragons, gongs, braziers, rows of worshippers kneeling as one, priests. |
| 5    | The Celestial Climb     | Up the mountain's north face in sweeping S-bends on blue and gold celestial stone, star pillars, terraced gardens of blossom.                                                                      |
| 6    | The Star Bridge         | West across the Cloud Chasm, high over a sea of cloud; its middle 70 m has no parapets (the one place you can fall).                                                                               |
| 7    | The Observatory Spiral  | Right, all the way round the Observatory Pinnacle under its great golden armillary rings (they turn in the game), climbing, and out over the Star Bridge's far end (15 m clear).                   |
| 8    | The Palace Terraces     | Through the palace's upper gardens: domed halls, lotus pools, blossom, guards.                                                                                                                     |
| 9    | The Procession Causeway | Down the broad processional way between grandstands of thousands, golden dragons, banners, a line of monks.                                                                                        |
| 10   | The Fireworks Overlook  | Out on the cliff's edge: the best seat for the fireworks, the whole kingdom below.                                                                                                                 |
| 11   | The Final Ascension     | Up round the palace's western bastion under golden celestial arches, crowds packed in.                                                                                                             |
| 12   | The Grand Finale        | Down onto the straight, under the celestial arches and the gate, to the line, the palace blazing above.                                                                                            |

**The festival** (`src/game/festival.ts` rules, `festivalLife.ts` drawing it; the
`festival` entity from `cdf_town.py`). Three stages, one per lap, following **your**
lap (the rivals never change it; time trials the same): the Opening Celebration (lap 1),
the Ceremony Intensifies (middle laps) and the Grand Finale (the last lap, and after the
line). Each stage sets how often the city's own rockets go up (about 0.45 a second, then
1.5, then 2.6 rising to about 4 by the line), how big (16-26 m bursts, then 20-38, then
26-52) and how varied (peonies and glitter; then willows, palms, rings and stars; then
everything, in rainbow too), how many sky lanterns rise (up to 700), how fast and bright
the observatory's rings turn and the brightness of the flash each burst throws on the
kingdom. Inside the last lap everything keeps building to the finish.

Over that, **set pieces**: choreographed displays keyed to places on the lap, so whoever
is driving sees them as they reach the landmark, each once per lap on its own laps:

- Lap 1: the opening salvo over the palace (a gong), bursts over the plaza, a blue ring
  round the observatory.
- Lap 2: a bigger salvo, golden comets across the inlet, a pink dragon sketched over the
  observatory as you reach the Star Bridge (a roar), three rings round the rings, the
  districts answering one another from the overlook.
- Lap 3: the Imperial Salute rippling along the skyline, golden rain over the palace,
  the Starfall, the dragon constellation in blue (bells), **the golden dragon drawn
  above the observatory, ringed, as you cross the Star Bridge** (a roar), the Celestial
  Rings, the palace salute, the panorama from the overlook (the crowd roars), the red
  dragon over the palace on the Final Ascension, and the Grand Finale over the finish:
  a golden dragon, a ring round the palace, a constellation, wave after wave of the
  biggest bursts and a curtain of golden rain.

Fireworks are purely visual. The city's own rockets follow the race clock and a fixed
seed, so every race and time trial sees the same show. Every star is a point in one
pooled buffer (24,000); the GPU works out where each is from when it was fired, and the
CPU writes each star once, when it's born. The lanterns are animated entirely on the
GPU. The flash is one hemisphere light. Stars never write depth or fog. Sounds (a
launch whistle, the boom and crackle a moment later with distance, a gong, the crowd's
roar) stay under the engines.

**The imperial dragon** is the kingdom's (`isles_dragon`), here in gold, bigger; on the
last lap it flies its `finale` path: round the palace's west side as you reach the
overlook, rising high above the palace on the Final Ascension, then down low over the
finish. Worshippers bow as it passes.

**People:** about 1,300: grandstand crowds (`cheer`, `wave`, `bow`), `worship` (new:
kneeling in rows before the altar, arms raised to the sky then a deep bow, all
together), monks, dancers, musicians, merchants, guards.

**Music:** "Celestial Dragon Festival" (`celestial`), D major, 144 BPM, in three layers
that follow the laps (`screens/race.ts` fades them as the lap changes): the base (flute
and bells, strings for the worship, celesta above the clouds, a bright tune for the
triumph); `rise` adds horns, sustained strings, a running marimba, toms, bongos and
tambourine; `finale` carries all of that plus brass and bells on the tune, a xylophone,
snare, more kick and a crash every phrase.

**The sky:** stars (1,100), a crescent moon (`skyDome.sun.face: "crescent"`, new), dark
violet clouds low on the horizon, karst hills. Night but readable: moonlight from the
south-east, warm pools round every lantern and brazier, gold round the palace,
blue-white round the observatory and the star pillars.

**How it's built:** `cdf_land.py` (pure data: the corners, heights, widths, the Palace
Mount with its terraced gardens, the Observatory Pinnacle, the Cloud Chasm, the inlet,
the city's terraces, the zones), `celestial_dragon_festival.py` (the route and road
kinds; bridges where the ground falls away or another stretch passes beneath; the Star
Bridge's open middle), `cdf_scenery.py` (land, lagoon, cloud sea, islands, falls, light,
checkpoints and pickups), `cdf_town.py` (every part's dressing, the palace, the
observatory, the people, the dragon's two flights, the festival's sites, set pieces and
lantern grounds, the air), `cdf_props.py` (domed halls and towers, terraces, celestial
arches, the observatory, the altar, mural walls, gongs, braziers, star pillars,
grandstands, dragon floats, colossal dragons), `cdf_textures.py` (20 textures and the
`celestial_dragon_festival` theme).

**Tests:** `tests/cdf.test.ts`: the world, theme and three-layer music; a clean load
with its worshippers, the dragon's finale flight, the festival and the air; the stages
and levels; the city's rockets more often, bigger and more varied each stage, the same
every time; set pieces firing once at their places on their laps only (the Star Bridge
dragon on the last); the show running as you drive (headless); the spiral well clear
over the Star Bridge; the AI driving it cleanly in 100-125 s. `tests/holes.test.ts`
covers it too.

**Limits and polish next:** the AI lap is about 114 s, a little over the 110 s aimed
for (players are usually quicker, and the AI is due to be rewritten). There's no
multiplayer yet; when there is, the festival can take its lap from any source (the
leader's, for a shared sky). There are no reflections of the fireworks in the water,
only their light. The firework sounds are simple synthesis. The palace and observatory
read well from the road; a closer pass (stairs, gardens, a lit interior) would reward
the overview shots.

## Polish next (Dragon Isles)

- **The cliffs.** They read as broad grey walls. More terracing, ledges with gardens
  and a few more falls (and mist) would bring the Cliffside Ascent closer to the
  storyboard.
- **The limestone texture** is busy up close. A calmer, softer stone would sit better
  under the towers.
- **The palace** reads well as a silhouette. A closer look (more roofs, gold, terraces of
  steps) and a finish view framing it through the Royal Gate.
- **The dragon:** a proper sculpted head (it's built from boxes now), animated whiskers
  and mane, and a scripted pause where it hangs in the air looking down at the leader.
- **Villagers:** more variety (hats, children, carried lanterns and parasols), and
  people who turn to watch karts go by.
- **Festival life:** a dragon dance (a long costume weaving through the square),
  fireworks or kites, and petals blowing across the road.
- **Draw calls** are about 480 at the start (the village, gate and palace all in view).
  Bigger merge squares for the town, or shared atlas materials, would bring that down.
