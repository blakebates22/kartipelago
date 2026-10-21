# Dragon Kingdom

The fourth world (`dragon` in `src/game/worlds.ts`): a sunlit kingdom of karst islands
in a turquoise lagoon, ruled by dragons. Festival towns, temple gardens, waterfalls and a
royal palace on its mountain, all watched over by a great jade dragon. One course so far,
Dragon Isles, then three "Coming Soon" tiles (Jade Lagoon, Lantern Peaks, Dragon's
Crown).

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

## Polish next

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
