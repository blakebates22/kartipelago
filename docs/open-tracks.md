# Open tracks

Meadow Run (`?track=3`, `assets/data/track3.json`) is the first open track: a wide (30 m),
flat road across open grass, with no walls along the road. You can drive anywhere. The
only things that stop you are solid obstacles:

- **Tunnels.** `tunnels: [{ from, to, thickness?, height? }]` (metres along the lap) put
  rock either side of a straight stretch of road, with a roof over it. The rock is two
  solid boxes, so you can hit its inside walls, its ends and its outer sides alike.
- **The map boundary.** A cliff `scenery.boundaryMargin` metres outside the course, all
  the way round.
- **Trees.** Scattered beside the road (`scenery.trees`, `treeClearance`, `treeSpread`,
  `treeRadius`), placed the same way every time (`scenery.seed`).

Hitting any of these uses the same impact rules as walls (light scrape, moderate kick,
severe crash; see drift-model.md). The code is `world/solids.ts` (what and where),
`stepSolids` in `physics/walls.ts` (collision) and `render/sceneryView.ts` (drawing).

Track options that make a track open:

| Key            | Effect                                                                                                                     |
| -------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `open`         | No road walls, no respawn for leaving the road, dropped bananas can land on grass.                                         |
| `gateMargin`   | How far beside the road still counts as passing a checkpoint (25 m here), so cutting a corner over the grass still counts. |
| `aiLineMargin` | Keeps the AI's racing line further from the edge (7 m), so it stays on the road.                                           |
| `groundColor`  | Grass colour for this track.                                                                                               |

Grass is the same as road for now. Rough terrain that slows you down comes later.
