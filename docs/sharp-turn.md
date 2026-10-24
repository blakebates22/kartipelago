# The sharp turn

Hold the brake in a drift while steering into it, and the kart pivots into a much tighter
arc and rolls up onto its outside wheels. The brake still slows you, so it's a trade:
you get the tight line and give up speed. Let go of the brake and the drift carries on
as before. It uses the existing buttons: drift (Space / Shift, or a bumper), brake (S / ↓,
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

- `sharpMinRadius` (7 m) is the tightest arc it can carve, so it can't pivot on the spot.
  Better handling characters get a smaller one, like their other arcs.
- The slide angle deepens from `driftOffsetDeg` (40°) to `sharpOffsetDeg` (45°).
- The drift's top-speed bonus (`driftSpeedMult`) and the spin-out on long hard
  countersteer are unchanged.

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
| 4 drift + brake (sharp)  | 25.3      | 19.7     | 11.9  | 108      | 19.6   | 21.6, 60              |
| 5 sharp, half stick      | 25.3      | 19.7     | 14.3  | 90       | 19.6   | 25.5, 50              |
| 6 drift + brake, counter | 25.3      | 19.7     | 65.3  | 20       | 0      | 65.3, 20              |
| 7 sharp, then brake off  | 21.1      | 25.3     | 16.8  | 82       | 18.9   | 27.1, 51              |
| 8 sharp held to a crawl  | 25.3      | 0.4      | 5.4   | 78       | 20     | 9.0, 47               |

The tests also check that it's the same at 60, 120 and 240 Hz, that nothing happens in the
air, that countersteering with the brake doesn't spin you, and that `sharpTurn: false`
switches it off (braking then steers and tightens a drift exactly as before).

## Tuning live

In `npm run dev`, the debug panel (the backtick key) lists every value above under
_vehicle_. The overlay shows `sharp` (the hold and the roll), `arc` (path radius) and
`yaw` (path turn rate).
