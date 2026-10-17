# M1: Drive a box

## Goal

A box you can drive around a large flat plane, and it already feels fun. Above all, the
drift should reward mastery.

## Done when

- [ ] Keyboard and gamepad input go through one input module (`core/input.ts`).
- [ ] Throttle, brake/reverse and steering, with speed-dependent steering.
- [ ] A drift button that slides the car, and drifting is faster than normal driving.
- [ ] Steering during a drift sets the arc: into the drift tightens, countersteer widens.
- [ ] A chase camera with smoothing and slight look-ahead.
- [ ] Every handling value lives in a `vehicle` section of `tuning.json`.
- [ ] The overlay shows speed, drift state, slip angle and grip.
- [ ] A practice course of pickups and boost pads tests whether you can drift onto a
      chosen line.
- [ ] Ten minutes of driving in circles is enjoyable.

## Not in this milestone

Hills, collision, tracks, other racers, sound, items. Boost pads exist only as a
practice-course aid; their real design comes in M4.

## Decisions

### Grippy base handling

Normal driving is arcade and grippy: the kart goes where the nose points, almost
instantly. Steering is precise and forgiving. We start here and loosen it only if
playtesting says so.

### The drift model

The kart tracks two directions separately:

1. **Heading**: where the nose points.
2. **Travel direction**: where the kart is actually going.

When not drifting, grip swings the travel direction round to the nose very quickly, so
the kart goes where it points.

Drifting works the other way round. The stick steers the **travel direction** directly,
and the **nose** is held at an angle into the drift.

- **Start:** press drift while steering. The drift direction (left or right) locks to the
  steering side at that moment. Pressing drift with no steering does nothing for now.
- **Steering the path:** the stick sets how the travel direction turns, over a range that
  crosses zero:
  - full into the drift: `driftTurnTight` (a hard curve the drift's way)
  - stick centred: `driftTurnNeutral` (a gentler curve the drift's way)
  - full countersteer: `driftTurnCounter` (negative, so the path bends the _other_ way)
- **Nose angle:** held into the drift, from `driftNoseCounterDeg` (full countersteer) to
  `driftNoseTightDeg` (full in), easing at `driftNoseRate`. It shows what the kart is
  doing and doesn't change the path.
- **Speed:** while drifting, top speed rises to `driftSpeedMult` × `topSpeed` (about
  15% faster). There is **no** boost for releasing; after the drift, the extra speed
  bleeds off.
- **Release:** normal grip returns, so the kart straightens up toward where the nose is
  pointing.
- **Cancel:** dropping below `driftMinSpeed` or braking ends the drift.

The skill this creates: drift right and countersteer left, and the kart slides left
while its nose still points right. Reaching a pickup or pad on the _outside_ of the turn
means steering _away_ from the turn.

The first version of this model (drift = low grip, stick only picks the arc size) could
never bend the path against the drift, so this skill was impossible. Playtesting caught
it.

### Character stats (early)

Characters rate **speed**, **acceleration** and **handling** from 1 to 5. A rating of 3
is the base kart in `tuning.json`; each point away from 3 scales the base values by the
`stats` section (top speed ±5%, acceleration ±15%, handling ±12% per point). Handling
scales every turn rate, including drift turn rates. The roster is data in
`assets/data/characters.json`, with original names and looks.

The default is **Speedster**, modelled on the speedrunner's favourite archetype: top
marks for speed and acceleration, below-average handling (5 / 5 / 2.5). Other
archetypes trade speed for sharper handling. Number keys switch character for testing.

### Tuning keys (first pass)

All in `vehicle` in `tuning.json`. Names may change during implementation.

| Key                   | Meaning                                                              |
| --------------------- | -------------------------------------------------------------------- |
| `accel`, `brake`      | Forward acceleration and braking, m/s²                               |
| `topSpeed`            | Top speed on throttle, m/s                                           |
| `reverseSpeed`        | Top reverse speed, m/s                                               |
| `drag`                | Coasting slowdown                                                    |
| `turnRate`            | Max yaw rate at low speed, rad/s                                     |
| `turnRateAtTop`       | Max yaw rate at top speed (lower = steadier at speed)                |
| `grip`                | How fast velocity aligns to heading when not drifting                |
| `driftTurnTight`      | Travel turn rate, full steer into the drift                          |
| `driftTurnNeutral`    | Travel turn rate, stick centred                                      |
| `driftTurnCounter`    | Travel turn rate, full countersteer (negative = bends the other way) |
| `driftNoseTightDeg`   | Nose angle into the drift, full steer in                             |
| `driftNoseCounterDeg` | Nose angle into the drift, full countersteer                         |
| `driftNoseRate`       | How fast the nose swings to its drift angle                          |
| `driftMinSpeed`       | Below this, a drift can't start and ends if active                   |
| `driftSpeedMult`      | Top speed multiplier while drifting (1.15 = 15% faster)              |

Input feel lives in a separate `input` section (deadzone, keyboard steering ramp).

## Build order

One small PR each, `main` playable after every merge:

1. **Input module.** Keyboard and gamepad merged into one state; shown on the overlay.
2. **Basic driving.** Throttle, brake/reverse, speed-dependent steering, grippy model.
3. **Chase camera.** Smoothed follow with look-ahead.
4. **Drift.** The model above, plus overlay readouts.
5. **Playtest pass.** Tune values on the deployed build and record notes here.

## Controls

| Action        | Keyboard           | Gamepad (standard layout) |
| ------------- | ------------------ | ------------------------- |
| Throttle      | W / Up             | A or right trigger        |
| Brake/reverse | S / Down           | X or left trigger         |
| Steer         | A, D / Left, Right | Left stick or d-pad       |
| Drift         | Space / Shift      | Right or left bumper      |

## Open questions

- Should drift ever start with no steering input (a straight hop)?
