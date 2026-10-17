# M2: First track

Status: **done**.

## Goal

One complete track with hills, a jump, walls and laps, where the M1 handling (above all
the drift) holds up on real corners, and leaving the ground feels as good as driving on
it.

## Done when

- [x] The kart follows the track surface: up and down hills, tilting to match slopes.
- [x] Slopes matter: uphill slows you a little, downhill speeds you up.
- [x] The kart leaves the ground at crests and ramps, flies, and lands without losing
      its horizontal speed.
- [x] Speed from drifting and boost pads carries through the air.
- [x] Walls stop you leaving the track; glancing hits slide along, head-on hits slow you.
- [x] Checkpoints in order make a lap; skipping one doesn't count.
- [x] A lap timer, best lap and a three-lap race with a finish.
- [x] Ending up off the track respawns you at the last checkpoint.
- [x] Every new feel value lives in `tuning.json`.
- [x] A full race on the track is fun.

## Also shipped

Added during the milestone after playtesting:

- **Start boost.** "Get ready!" then "GO!", with the perfect moment halfway between.
  A press within ±0.2 s of it is a perfect start (2× top speed for 2 s); up to 0.3 s
  earlier is a good start (1.2× for 0.8 s). Holding the throttle from the start, or
  letting go before GO, earns nothing.
- **Start timing tool.** A timeline bar showing the windows and where you pressed, in
  milliseconds. Shown only with `?timing` in the URL.
- **Smoother drift exit.** Releasing a drift eases the slide angle away (mostly by
  turning the nose toward the path) instead of snapping the path to the nose.
- **Best-ever lap record**, saved in the browser.

## Playtest notes

- The first track's corners didn't suit the drift: the median corner radius was 87 m
  (far gentler than a drift's 20 to 33 m arc) and the tightest was 10.5 m (too tight
  for anything). The track was rebuilt from straights and arcs sized to the drift, and
  widened to 22 m. **Rule for future tracks: size corners to the drift arc, not the
  other way round.** Speedster at drift speed (about 28 m/s): full-in about 20 m,
  neutral about 33 m.
- Releasing a drift felt too snappy and awkward; fixed with the drift exit above.
- The 3-2-1 countdown was replaced with "Get ready!" / "GO!" and tuned using the timing
  tool: `readySec` 1.5, `perfectWindowSec` 0.2, perfect boost 2× for 2 s.
- Air: barely any steering, speed never lost on landing, no hop button.
- Bugs caught along the way: road dipping under the ground (spline overshoot and the
  low edge of banked corners), uneven track sampling on long tracks, a start heading
  that leaned toward the previous corner, and karts pinned against walls.
- Next for tracks: a track builder tool (roadmap M7b) for more control over layouts.

## Not in this milestone

Other racers, items, water, sound, menus, more than one track.

## Decisions

### No physics engine

Kart handling stays a hand-written arcade model, as in M1. A general rigid-body engine
(Rapier, Cannon) makes karts bounce, tip and feel floaty, and we'd spend the milestone
fighting it. Instead the kart asks the track simple questions each step: "how high is
the ground under me, and which way does it face?" and "am I inside a wall?".

### Ground and air are two states of one kart

The M1 model already splits motion into a **horizontal** part (speed along a travel
direction, steered by the stick) and nothing vertical. M2 adds a **vertical** part:
height `y` and vertical speed `vy`, plus a `grounded` flag.

**On the ground:**

- Each step, cast a ray down to find the surface height and its normal.
- Snap the kart to the surface and tilt the mesh to the normal (visual only).
- Slopes add a little speed downhill and take a little uphill (`slopeGravity`).
- Everything from M1 (steering, drifting, grip) works as before.

**Leaving the ground:**

- No special "jump" code for ramps. If the surface drops away faster than the kart can
  follow it (a crest, the lip of a ramp), the kart becomes airborne. It keeps the
  upward speed it had from driving up the slope, so steeper, faster ramps throw you
  further.
- `snapDistance` decides how far the ground can fall away in one step before you
  leave it. Too big and karts stick to crests unnaturally; too small and every bump
  launches you.

**In the air:**

- Gravity pulls `vy` down (`airGravity`). There is no rolling drag, so horizontal speed,
  including drift and boost-pad speed, carries through the jump.
- Barely any air steering (`airSteer`, a small fraction of ground steering), so you can
  line up a landing but not turn corners in mid-air.
- A drift in progress stays locked while airborne and continues on landing if the
  button is still held. A new drift can't start in the air.

**Landing:**

- Drop the vertical speed, keep the horizontal speed. Landing **never** costs speed.
- Re-project the travel direction onto the new surface, so landing on a downslope feels
  smooth and landing flat after a big drop gives a small bump.

This keeps one controller for both states, so there's no hand-off between a "ground
kart" and an "air kart", and boosts carrying through the air falls out naturally.

### How the track is built

The first track is generated from data: a closed spline of centre points, each with a
height, width and bank angle. Code turns that into the road mesh, walls along both
edges, checkpoints at intervals and a ground ray target. This gets us a real track
without Blender or 3D art, and the layout is easy to iterate in a JSON file. Blender and
glTF tracks (see ARCHITECTURE.md) can come later, once we know what a track needs.

### Walls

Walls are segments along the road edges. When the kart overlaps one, push it out along
the wall normal and remove the speed going into the wall. A glancing hit barely slows
you; a head-on hit nearly stops you.

## Build order

1. **Track from a spline.** Flat road with walls drawn, no collision yet.
2. **Ground following.** Heights and slopes, mesh tilts to the surface.
3. **Airborne.** Leaving the ground, gravity, air steering, landing.
4. **Walls.** Collision and sliding.
5. **Laps.** Checkpoints, lap counter, timer, three-lap race, respawn.
6. **Playtest pass.**

## Answered

- Air steering: barely. Landing: never costs speed. Hop button: not yet.

## Open questions

- One big jump on the first track, or several small hops? (Starting with one, on the
  opening straight.)
