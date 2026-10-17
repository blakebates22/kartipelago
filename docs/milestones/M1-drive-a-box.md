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
- [ ] Ten minutes of driving in circles is enjoyable.

## Not in this milestone

Hills, collision, tracks, other racers, sound, boosts of any kind (M4).

## Decisions

### Grippy base handling

Normal driving is arcade and grippy: the kart goes where the nose points, almost
instantly. Steering is precise and forgiving. We start here and loosen it only if
playtesting says so.

### The drift model

The kart tracks two directions separately:

1. **Heading**: where the nose points.
2. **Velocity direction**: where the kart is actually travelling.

When not drifting, velocity catches up to heading very quickly (high grip). When
drifting, it catches up slowly, so the body slides wide while the nose points into the
turn.

How a drift works:

- **Start:** press drift while steering. The drift direction (left or right) locks to the
  steering side at that moment. Pressing drift with no steering does nothing for now.
- **Hold:** the stick no longer steers normally. It picks the arc between
  `driftTurnLoose` (full countersteer) and `driftTurnTight` (full into the drift). The
  kart always keeps turning in the locked direction, even at full countersteer.
- **Speed:** while drifting, top speed rises to `driftSpeedMult` × `topSpeed` (about
  15% faster). Drifting is the fast way round corners. There is **no** boost for
  releasing; after the drift, the extra speed bleeds off.
- **Release:** grip returns and normal steering resumes.
- **Cancel:** dropping below `driftMinSpeed` or braking ends the drift.

The skill this creates: because the kart slides along an arc outside where the nose
points, reaching something on the _outside_ of the turn means steering _away_ from it
(countersteer). Players who learn this take tight, fast lines; newcomers still get round
corners. This behaviour falls out of the model and should not be special-cased.

### Tuning keys (first pass)

All in `vehicle` in `tuning.json`. Names may change during implementation.

| Key              | Meaning                                                 |
| ---------------- | ------------------------------------------------------- |
| `accel`, `brake` | Forward acceleration and braking, m/s²                  |
| `topSpeed`       | Top speed on throttle, m/s                              |
| `reverseSpeed`   | Top reverse speed, m/s                                  |
| `drag`           | Coasting slowdown                                       |
| `turnRate`       | Max yaw rate at low speed, rad/s                        |
| `turnRateAtTop`  | Max yaw rate at top speed (lower = steadier at speed)   |
| `grip`           | How fast velocity aligns to heading when not drifting   |
| `driftGrip`      | Same, while drifting (much lower)                       |
| `driftTurnTight` | Yaw rate with full steer into the drift                 |
| `driftTurnLoose` | Yaw rate at full countersteer                           |
| `driftMinSpeed`  | Below this, a drift can't start and ends if active      |
| `driftSpeedMult` | Top speed multiplier while drifting (1.15 = 15% faster) |

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
