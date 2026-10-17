# M3: Rivals

## Goal

Seven AI rivals race you on any track, drifting like skilled players, so a race is a
real contest. They must work on future tracks without hand-authoring anything.

## Done when

- [ ] A racing line is computed automatically from a track's data.
- [ ] AI karts drive with the same inputs and physics as the player.
- [ ] AI karts drift through corners that suit the drift, and follow the line.
- [ ] Seven rivals start on a grid behind the line, with original names and colours.
- [ ] Karts bump each other instead of driving through each other.
- [ ] The HUD shows your race position; the finish screen shows the standings.
- [ ] A difficulty setting can make rivals slower or stop them drifting.
- [ ] A race against seven rivals on Drift Loop is fun and close.

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
