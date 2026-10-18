# M3: Rivals

Status: **done**.

## Goal

Seven AI rivals race you on any track, drifting like skilled players, so a race is a
real contest. They must work on future tracks without hand-authoring anything.

## Done when

- [x] A racing line is computed automatically from a track's data.
- [x] AI karts drive with the same inputs and physics as the player.
- [x] AI karts drift through corners that suit the drift, and follow the line.
- [x] Seven rivals start on a grid behind the line, with original names and colours.
- [x] Karts bump each other instead of driving through each other.
- [x] The HUD shows your race position; the finish screen shows the standings.
- [x] A difficulty setting can make rivals slower or stop them drifting.
- [x] A race against seven rivals is fun and close.

## Also shipped

Added during the milestone after playtesting:

- **Offset drift model** (`driftModel` 1, see `docs/drift-model.md`): the stick steers
  the body as an arc curvature with an assisted shape, the path is the body plus a drift
  offset that builds and eases over about half a second, and sustained hard
  countersteer can spin you out. Braking tightens a drift; keyboard steering builds more
  slowly while drifting, so tap length gives fine control. **M** flips to the old model.
- **Ribbon Ridge**, a second track built for linked drifts and direction changes, with
  track selection (`?track=1`, `?track=2`) and per-track lap records.
- **Wall impact severity**: light scrapes keep the drift, moderate hits knock the kart but
  the drift survives, crashes cancel it and briefly disrupt control.
- Fixes: ground-lookup gaps on the outside of bends, false take-offs on banked road, a
  crest that launched karts at a corner, and grid ranking on curved approaches.

## Playtest notes

- Rivals feel good as they are. Revisit difficulty once items arrive.
- The new drift model "feels much better" than the old one.
- Wall impacts feel good; the light/moderate/severe bands are `scrapeSpeed` 4 and
  `crashSpeed` 12 m/s.
- AI settings that work on both tracks: line margin 4.5 m, drift when a corner ahead is
  tighter than 45 m, look 20 m ahead for corners.
- Track design rules learned: no corner tighter than a full-in drift (about 20 m);
  direction changes need room (wider, unbanked); ease height changes; avoid flipping the
  bank on raised road.

## Not in this milestone

Items, rubber-banding, multiple difficulty presets in a menu, AI shortcuts or alternate
routes, split-screen.

## Decisions

### No level design needed first

The AI reads the same track data as everything else (the spline that builds the road,
walls and checkpoints), so any track gets a working AI for free. Later, the track
builder (M7b) can let a designer nudge the racing line where wanted.

### Racing line

Start from the centre line and repeatedly smooth it, pulling each point toward the
average of its neighbours while keeping it inside the road (minus a margin). Smoothing a
path straightens it, so the result cuts the inside of corners and runs wide on entry and
exit, like a real racing line.

### AI drives like a player

An AI driver only produces an `InputState` (throttle, brake, steer, drift) each step.
The kart model, walls, air and race rules treat it exactly like the player's input.
Tuning the handling tunes the rivals too.

- **Steering:** aim at a point ahead on the racing line, further ahead at speed (pure
  pursuit), and convert the needed turn rate into a stick position.
- **Drifting:** look ahead along the line. When an upcoming corner's radius falls in the
  drift range (`driftEnterRadius`), tap drift and steer into the corner. While
  drifting, work out the path turn rate the line needs and pick the stick position that
  gives it, using the same tight / neutral / counter mapping the player feels. Release
  when the corner opens up or changes direction.
- **Start:** each rival presses the throttle near the perfect start moment, a little
  early or late depending on skill.

### Difficulty

`ai.speedMult` scales rivals' top speed; `ai.drift` (0 or 1) turns their drifting off.
Start here; scale back if it's too hard.

## Build order

1. Spec, racing line, AI driver, grid, collisions, positions, standings (one PR).
2. Playtest pass: tune difficulty and line margin; note what feels unfair.
