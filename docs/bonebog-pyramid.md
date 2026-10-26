# Bonebog Pyramid

Dinosaur Valley's third course, rebuilt as a signature track: a living
prehistoric swamp under a vast canopy, a dinosaur graveyard, and a colossal overgrown
pyramid that you drive straight through. About 1.63 km a lap (an AI lap is about 70 s).

The old version (a small pyramid that seemed to float, bare water, small trees and lots
of easy falls into the swamp) is in git history before this rebuild.

## The lap

| Section | Name               | What happens                                                                                                                                                       |
| ------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A       | The Old Dike       | The start, on a raised stone road along an earthen dike, under the Jawbone Gate (a colossal lower jaw stood on end). Torch posts, reeds, giant trees on the banks. |
| B       | The Boardwalks     | Railed wooden walkways (rope rails, torch posts) winding east between giant trees, bubbling green pools, a lookout tower, under the canopy.                        |
| C       | The Rib Bridge     | A high timber trestle (12 m) north across Rib Lagoon, straight through a colossal rib cage; its skull lies in the water at the far end. A zipper on the climb.     |
| D       | The Grand Causeway | A railed stone causeway west across the lagoon, skull-capped posts and braziers, a long-neck's neck arching high overhead, aimed at the pyramid's carved face.     |
| E       | The Pyramid        | About 200 m (nine to ten seconds) inside: a torchlit corridor, a turning chamber round a great column with a guardian's head, the Great Hall, then the south door. |
| F       | Skull Lagoon       | A trestle down out of the south face past a 40 m skull lying in the water, jaws open.                                                                              |
| G       | The Mangroves      | Winding boardwalks under the treehouse village: plank platforms round the giant trunks, rope bridges, stilt huts with glowing doorways.                            |

**The pyramid** is 190 x 210 m at its base and about 90 m tall: a stone foundation
rising out of the swamp (so it's grounded, never floating), six stepped tiers draped in
vines and moss with small trees on the steps, grand staircases up the north and west
faces to a shrine with a beacon fire, colossal heads at the foundation's corners and
braziers round its terrace. The east face (the way in) and the south face (the way out)
are carved as guardians' faces with glowing green eyes and a row of fangs over the
door, with waterfalls pouring from spouts either side down to the terrace and on into
the swamp.

**Inside:** dark, damp stone lit only by torches (the firelight is painted on), carved
pilasters and a frieze along the corridor, cobwebs in the corners, roots and vines
through the roof. The Great Hall has two rows of massive carved pillars, glowing pools
along both walls fed by waterfalls from the roof, and shafts of light.

**The swamp:** deep, murky green water all round (fall in and you're fished out at the
last checkpoint), giant swamp trees 50-60 m tall on buttress roots, and a ceiling of
leaves at about 50 m over everything but the lagoon and the pyramid, with gaps where
shafts of sunlight come down. Vines and moss hang from the canopy, never low enough to
reach a kart. Lily pads and lotus flowers, cattails and reeds, rotting logs, stumps and
sunken timber, glowing caps and big leaves on the banks, crocodiles lurking beside the
walkways, frogs, low mist over the water, and the bones of the graveyard everywhere:
horned skulls, rib pairs rising from the water, femurs, bone piles and vertebrae.

## Safety: elevated, not punishing

- Every road point is at least 2.5 m above the water, and the road is 14.5-16 m wide.
- Every raised stretch has a rail (boardwalks and trestles: a 1.2-1.3 m wooden rail;
  the causeway: a carved stone balustrade). `tests/bonebog.test.ts` checks that at
  least 97% of the places where the edge drops to water are fenced in.
- The dike (the start) has a low stone curb and wide mossy banks before the water.
- There are no islands within 30 m of the road, so nobody gets stranded on one.

## Lighting and atmosphere

- The **Bonebog Swamp** theme: a warm golden-hour sun low in the west, a golden horizon,
  green-gold distance fog from 70 m, and greenish ambient light.
- Dappled canopy shade painted onto the swamp, brighter under the gaps.
- Torch posts along every walkway, braziers on the causeway and the terrace, lanterns in
  the village; warm light is painted round each one, and the nearest four light the
  road and the karts with a flicker (`torch` entities).
- Shafts of light under the canopy gaps and in the Great Hall (see-through, glowing).
- `bubbles` entities: glowing bubbles rising from the green pools, with the odd burp of
  swamp gas. A `fireflies` entity: glowing motes drifting round the camera. Both are
  in `src/game/hazards.ts` and purely visual.
- A pterosaur circles over the lagoon; spray and roar at every waterfall.

**Music:** the existing "Bonebog Pyramid" groove (`bonebog` in `src/audio/songs.ts`).

## How it's built

Everything is in `tools/blender/prehistoric/`, on the course kit:

- `bonebog_pyramid.py`: the layout (turtle segments, closed by stretching two
  straights), the heights along the lap, the swamp bed (islands, the dike, the jungle
  rising all round), the road kinds and the gameplay (4 zippers, 8 egg rows, 8 balloons,
  checkpoints).
- `bonebog_scenery.py`: the pyramid (one stepped solid with the corridor, chamber and
  halls cut through it), its faces, stairs, drapes, terrace and halls; the skeletons;
  the trees, canopy ceiling, hanging vines and light shafts; the walkways' timber; the
  swamp's life; the treehouses; the painted light and shade; then copies are joined per
  map square (fewer draw calls).
- `swamp_props.py`: the swamp kit (giant swamp trees, canopy clumps, hanging vines and
  moss, cobwebs, sunken timber, the croc, torch posts, stone braziers, stilt huts, the
  watchtower, tree platforms, vertebrae, femurs, horned and great skulls, rib pairs,
  bone piles, hall pillars, light cattails, tier trees).
- `make_textures.py`: the **Bonebog Swamp** theme and its 20 textures (`bog_*`, cobweb,
  light shaft, croc skin).

Run `python tools/blender/prehistoric/bonebog_pyramid.py` (with the bpy module) to
rebuild `tracks-src/bonebog_pyramid.blend` and `public/tracks/bonebog_pyramid/`.

**Tests:** `tests/bonebog.test.ts` (clean load and its entities, raised and fenced,
the time inside the pyramid, three clean AI laps), `tests/holes.test.ts` and
`tests/prehistoric.test.ts`.

**Size:** about 18 MB of visual geometry and 3 MB of collision (Frostveil is about 14 +
7 MB); about 900 draw calls at the start.
