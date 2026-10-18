# Racers

Four original racers replace the placeholder boxes. Their looks are separate from
driving stats: pick a look with the menu at the bottom left (or `?racer=moss`, `bramble`,
`poppy`, `otto`), and pick stats with the 1-4 keys as before. The rivals take the other
three looks in turn; repeats get alternate paint.

| Racer   | Species  | Kart                             | Seen from behind                        |
| ------- | -------- | -------------------------------- | --------------------------------------- |
| Moss    | axolotl  | sunflower yellow, turquoise trim | fans of coral gills, a tail fin         |
| Bramble | pangolin | leaf green, gold trim            | armour plates, a curled armoured tail   |
| Poppy   | moth     | cherry red, cream trim           | feathery antennae, folded spotted wings |
| Otto    | capybara | royal blue, orange trim          | big round back, small ears, an orange   |

Everything is visual. The racers follow the kart's physics state and add motion through
child transforms. Nothing writes back to the physics, and the collision shape is the same
circle as before.

## Moss's faceted style

Moss is the first racer in the faceted, pixel-textured style (`moss.ts`, `faceted.ts`).
The aim is the reference look Blake picked:

- flat-shaded low-poly shapes (icospheres, chamfered boxes, octagonal tyres);
- a 16x16 grain texture sampled nearest-neighbour, so texels show as soft pixel blocks;
- a face painted as 64x40 pixel art and laid on the head's own facets as a decal.

The face texture swaps for expressions: a cheerful toothy smile, a determined grin with
slanted lids when drifting or boosting, a wide-eyed "oh!" for hits and jumps, and closed
eyes to blink. Moss has his own angular formula kart, with a wedge nose and a cream crown
on it, chunky teal pods over the wheels, a roll hoop, and dark octagonal tyres with cream
hubs and green caps. The other three racers still use the earlier smooth style.

## How it's built

`src/render/racers/`:

- `geo.ts`: rounded shapes, each with one vertex colour, merged into one mesh per
  rigid part. A whole racer is about 17 draw calls up close.
- `paint.ts`: the shared look. A 64x64 soft painted wash multiplies the vertex colours.
  Lambert (Gouraud-style) lighting, no shiny modern materials, and blob shadows.
- `designs.ts`: the palette and each racer's kart paint.
- `kart.ts`: the shared toy kart. It has a rounded tub, big bright tyres with chunky
  hubs, mudguards, a steering wheel, a little exhaust and a per-racer decoration.
- `characters.ts`: the four characters on one rig layout. The hands ride on the
  steering wheel, and the arms stretch from the shoulders to the hands each frame.
- `racer.ts`: kart + character + exhaust flame + blob shadow, a far-away version (LOD,
  one mesh for the kart and one for the character beyond `LOD_DISTANCE`), and the
  animator.

The whole picture renders slightly below full resolution and is smoothly scaled up. It
has distance fog in the sky colour. Both are in `tuning.json` under `look`.

The procedural shapes can be swapped for modelled assets later: anything that provides
the same rig parts (torso, head, eyes, mouths, arms, hands, wiggles) works with the
animator.

## Animation

- **Idle:** breathing bob, blinks, slow head turns. Each racer has their own touches:
  Bramble keeps checking around, Otto nods with sleepy eyes, Poppy's antennae twitch,
  Moss's gills wave.
- **Steering:** the torso and head lean into the turn, and the steering wheel (with the
  hands on it) follows the stick. The front wheels steer and every wheel spins with speed.
- **Drifting:** a stronger lean and a determined face. The head looks along the
  direction of travel, and countersteering pulls the lean back.
- **Boosting:** pushed back into the seat, the kart's nose lifts, and the face goes
  excited or determined. The exhaust flame is the same boost cue as before.
- **Hits:** recoil, squash and stretch, and a surprised face, scaled by how hard the hit
  was.
- **Jumps:** a quick crouch at take-off, stretched and excited in the air, a squash on
  landing.
- **Glances:** now and then a racer looks at a nearby rival, then looks back.

## Racer preview

Open `garage.html`, or use the "Racer preview" link in the game. You can:

- orbit with the mouse
- show one racer or all four
- jump to the front, side, rear, gameplay-camera, face or far-away views
- set speed, steering and drift
- trigger boosts, wall hits, weapon spins and jumps

Adding `?view=`, `?speed=`, `?steer=`, `?drift=` and `?react=` to the address sets these
at load.
