# The sharp turn

Hold the brake in a drift while steering into it, and the kart pivots into a much tighter
arc and rolls up onto its outside wheels: a really tight drift on two wheels, that you
can keep driving round as long as you like. The brake doesn't stop you here. It eases you
down to a holding speed (`sharpHoldSpeed`, 85% of top speed) and keeps you there while
you're on the throttle. The trade is the drift's speed bonus, which fades out while
you're up on two wheels. Let go of the brake and you widen smoothly back into the drift. It uses the existing buttons: drift (Space / Shift, or a bumper), brake (S / ↓,
or the left trigger / X) and steer.

This is our own model, built from Blake's description of how the move feels and the
numbers he gave (the steering coefficients, the lean angle and how fast it builds). No
other game's code was read or used.

## Steering coefficients

Steering is a coefficient that depends on what you're doing, relative to driving
normally:

| Doing                   | Coefficient (`tuning.json`) | Effect                             |
| ----------------------- | --------------------------- | ---------------------------------- |
| driving                 | `steerCoefNormal` 6         | the reference                      |
| braking, not drifting   | `steerCoefBrake` 12         | turn rate × 12 / 6                 |
| braking in a drift (in) | `steerCoefDriftBrake` 18    | drift arc curvature × up to 18 / 6 |

They're coefficients, not stacked multipliers: braking in a drift uses 18, not 12 × 18.
The drift-brake coefficient blends in with the sharp turn's hold (`sharp`, 0..1), which
builds at `sharpResponse` and lets go at `sharpRelease` (per second), so it never snaps.

## When it holds

All of these, every physics step:

- drifting (offset model), on the ground;
- the brake down (a partial trigger gives a partial sharp turn);
- the stick at least `sharpMinSteer` (0.2) into the drift: countersteering with the brake
  is not a sharp turn, it just slows and widens as before;
- at least `sharpMinSpeed` (8 m/s). The drift itself ends at `driftMinSpeed` (also 8), or
  when you let go of drift, as before.

Other parts:

- `sharpHoldSpeed` (0.85): the speed it settles to, as a share of top speed (after any
  banana slow-down). Above it, the brake eases you down to it at the drift's brake rate;
  below it, the throttle brings you back up to it. Off the throttle, you slow as usual.
- `sharpMinRadius` (9 m) is the tightest arc it can carve, so it can't pivot on the spot.
  Better handling characters get a smaller one, like their other arcs.
- The slide angle deepens from `driftOffsetDeg` (40°) to `sharpOffsetDeg` (45°).
- The drift's top-speed bonus (`driftSpeedMult`) fades out with the hold, and comes back
  as you let go. The spin-out on long hard countersteer is unchanged.

## The roll

The body rolls onto its outside wheels up to `sharpLeanDeg` (20°) at full hold. The roll
builds no faster than `sharpLeanRate` (250°/s) and eases back at `sharpLeanReturn` (per
second). The whole kart rolls: chassis, wheels and driver. It pivots on the outer edge of
the outside tyres, so they stay on the ground. This is visual only. The physics is still a
flat circle, so collisions and walls are unaffected. The camera doesn't roll.

## Measured (tests/sharpTurn.test.ts)

Flat ground, the base kart, full right. Entry is at top speed (a drift's entry includes
its speed bonus). Measured over 0.4 s.

| Case                     | Entry m/s | Exit m/s | Arc m | Turn °/s | Roll ° | (sharp off: arc, °/s) |
| ------------------------ | --------- | -------- | ----- | -------- | ------ | --------------------- |
| 1 steer                  | 22        | 22       | 13.8  | 92       | 0      | 13.8, 92              |
| 2 brake + steer          | 22        | 5.8      | 3.8   | 205      | 0      | 7.3, 108              |
| 3 drift                  | 25.3      | 25.3     | 29.9  | 49       | 0      | 29.9, 49              |
| 4 drift + brake (sharp)  | 25.3      | 19.7     | 12.0  | 107      | 19.6   | 21.6, 60              |
| 5 sharp, half stick      | 25.3      | 19.7     | 14.3  | 90       | 19.6   | 25.5, 50              |
| 6 drift + brake, counter | 25.3      | 19.7     | 65.3  | 20       | 0      | 65.3, 20              |
| 7 sharp, then brake off  | 21.1      | 25.3     | 16.8  | 82       | 18.9   | 27.1, 51              |
| 8 sharp held 3 s         | 25.3      | 18.7     | 9.4   | 117      | 20     | 9.0, 47 (brakes to 0) |

The tests also check that it's the same at 60, 120 and 240 Hz, that nothing happens in the
air, that countersteering with the brake doesn't spin you, and that `sharpTurn: false`
switches it off (braking then steers and tightens a drift exactly as before).

## Tuning live

In `npm run dev`, the debug panel (the backtick key) lists every value above under
_vehicle_. The overlay shows `sharp` (the hold and the roll), `arc` (path radius) and
`yaw` (path turn rate).
