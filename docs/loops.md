# Loop-the-loops

A loop-the-loop is a road that climbs, goes right over the top upside down and comes
back down, offset sideways so its exit clears its entry. Karts ride it in a special
**loop mode**, the way classic kart racers did it: the ordinary physics (which treat the
kart as driving on a height field, always upright) would never get a kart round. The
system is in `src/game/loops.ts`. Any track can have loops, and **Loop Lab** in the Test
World is a plain circuit for trying one out. **Aurora Rift**'s Rift Loop uses the same
system.

This is our own design, written for this project. No code was taken from any other game.

## The shape

```
            ___
          /     \          side view: the pitch angle turns through 360°
         |       |         its curvature eases in over `ramp` metres (no kink where it
          \     /          meets the road), holds at 1/radius round the top, eases out
  ________/_____\______    and the exit is `offset` metres to the driver's right
```

- The road's pitch turns through a full circle. Its **curvature ramps up** over `ramp`
  metres, holds at 1/`radius` through the round part, and ramps back down. This is a
  clothoid entry, like a real coaster's: no sudden jolt as you go in, and a teardrop
  shape.
- The **sideways shift** follows a smootherstep along the loop's length. The road is dead
  straight where it meets the ordinary road at either end, and drifts across over the
  top.
- The **frame** (tangent, surface normal, across) is continuous and orthonormal all the
  way round. The normal points up at the ends and down at the top, and never flips.
- Beyond either end the curve carries on straight. The camera rail and the hand-back
  use this.

`buildLoop(def)` integrates the curve once (1,024 samples), and `loopFrame(path, s)`
gives the point and frame at any distance along it.

The Blender kit has the same curve in `course_kit.py` (`LoopPath`). It builds the visible
road from it and writes a few of its points into the entity as `probe`. A test
(`tests/loops.test.ts`) checks that the two agree to within 2 cm.

## The entity

```json
{ "id": "loop_01", "type": "loop", "x": 0, "y": 0.5, "z": 40, "heading": -3.14159,
  "radius": 22, "ramp": 26, "offset": 18, "width": 14,
  "minSpeed": 14, "commit": 18, "boostMult": 1.45, "boostSec": 2.2, "gravity": 8,
  "probe": [[0, 0, 0.5, 40], ...] }
```

| Field                   | Meaning                                                                                                           |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `x`, `y`, `z`           | Where the loop starts (the road surface, game coordinates).                                                       |
| `heading`               | The direction of travel there.                                                                                    |
| `radius`, `ramp`        | The shape (see above).                                                                                            |
| `offset`                | The sideways shift to the exit, in metres to the driver's right.                                                  |
| `width`                 | The road width (steering keeps you 1.1 m inside each edge).                                                       |
| `minSpeed`, `commit`    | Once you're `commit` metres in, the loop won't let you drop below `minSpeed`.                                     |
| `boostMult`, `boostSec` | The entry booster: an ordinary boost from the existing boost system (top-speed multiplier, seconds). 0 = none.    |
| `gravity`               | Gravity along the road (m/s²): you slow on the way up and speed up on the way down. It's gentler than in the air. |

In Blender, use `Course.loop(LoopPath(...))` to build the road and add the entity. Use a
`("LOOP", radius, ramp, offset)` turtle segment for the gap in the route between entry
and exit, and `route_with_loops` for the control points (exact and sharp at both
ends). `route(..., sharp=..., flat=...)` keeps the route straight and unbanked into
and out of the loop. Mark the pieces of road next to the loop `exact` so they end dead
straight at it. `loop_lab.py` is the smallest example.

## Riding it

Each kart has its own `LoopRide`.

- **Entry trigger:** the kart crosses either end's gate onto the loop. It has to be
  driving forwards, roughly lined up (within about 65°), across the road's width and at
  its height. Anything else drives on by. A kart already on a loop can't be caught
  again.
- **In loop mode** the kart is attached to the road surface. It moves along the curve
  at its speed. Gravity along the road slows it climbing and speeds it descending.
  Steering turns it across the road (up to about 24°): it slides between the edges and
  straightens up when you let go. The ordinary kart model still runs every step for
  throttle, brakes, boosts, zippers and tapping, with the steering and drifting taken
  over by the loop. Walls, the height field and ground snapping are skipped.
- **The assist:** once the kart is past the commit point, its speed can't drop below
  `minSpeed`. A slow kart is carried round, so nobody stalls upside down. Before the
  commit point you can stop and back out.
- **Exit:** at either end the kart is handed back to normal driving at exactly the
  loop's end point. Its speed, its steering angle and its sideways place are kept, and
  it is grounded and upright.
- **Wrong way:** a kart that drives onto the exit the wrong way rides the loop backwards
  and comes out of the entry.
- **Other karts:** karts on the same loop bump along and across its road. They share
  speed if one rams another, and push apart sideways. A kart on a loop doesn't bump karts
  on the ordinary road.
- **Failures:** a respawn or a restart drops a kart out of loop mode at once. A safety
  net ends any ride after 25 s at its far end.
- **Race logic** (checkpoints, laps, places, item targeting) sees a riding kart on the
  straight line from the loop's entry to its exit. Gates and positions never see it
  upside down. Don't put a gate inside a loop (the kit's checkpoint generator avoids the
  gap automatically).
- **AI:** on the approach the AI steers onto the loop's centre line (it doesn't drift
  there). On the loop it holds the middle of the road.

## The loop camera

When the player is on a loop, the camera rides a rail: a point on the loop's road a
chase-distance behind the kart, lifted off the surface along its normal. It looks at a
point ahead on the road. Its "up" is the road's normal, so the camera rolls with the
kart and the world turns over at the top.

The camera always stays on the inside of the curve, so it never clips through the road.
It blends in from the chase camera over about half a second as you drive on. While you
ride, the ordinary chase camera keeps following the kart's place on the straight line
underneath, so it's already settled behind you when the loop camera hands back. That
blend-out starts once the camera itself has left the loop.

## Drawing

The kart is drawn from the ride's pose, interpolated between physics steps: sitting on
the road, its "up" the road's normal. Its blob shadow is hidden while it's on the loop.
The `loop` sound plays as you drive on.

## Loop Lab

`loop_lab` (Test World): a 750 m circuit. A long straight with a boost pad leads into
one 46 m tall loop (radius 22, ramp 26, shift 18), then a straight out, and two hairpins
back round. It's built by `tools/blender/prehistoric/loop_lab.py`. Tests:
`tests/loops.test.ts` covers the geometry, the Blender agreement, riding at speed,
riding slowly (the assist), backing out, steering limits, wrong-way rides, two karts side
by side, race positions, and three AI laps.
