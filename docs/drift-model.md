# Drift model

Kartipelago's drift is an original model, designed from gameplay observations of
classic kart racers (what the player feels), not from any other game's code.

## The idea

The kart has two directions: where the **body** points and where the **path** goes.

- **Normal driving:** steering turns the body; grip pulls the path onto it quickly.
- **Drifting (offset model, `driftModel` 1):**
  - The smoothed stick steers the **body**, as a _curvature_ (1 / arc radius), so the same
    stick position carves the same arc at any speed.
  - The path is the body direction plus a **drift offset**. The offset builds smoothly to
    `driftOffsetDeg` and does not follow the stick, so steering doesn't swing the kart's
    visible angle around. On entry the growing offset carries the kart wide; on release
    it eases back to zero and the path settles onto where the nose points.

## Assisted steering shape

`u` is the smoothed steer measured into the drift: -1 full countersteer, 0 centred,
1 full in. Curvatures are `1 / radius`.

```
into the drift (u >= 0):  k = kNeutral + (kTight - kNeutral) * (1 - (1 - u)^q)
countersteer   (u <  0):  k = kNeutral - (kNeutral - kCounter) * |u|^p
```

- Hands-off keeps a natural inward turn (`driftRadiusNeutral`).
- Steering in tightens, with diminishing returns (`driftInCurve` = q), up to a hard
  limit (`driftRadiusTight`), so full lock can't over-rotate.
- Countersteering widens the arc (`driftCounterCurve` = p). A large positive
  `driftRadiusCounter` keeps a slight inward pull; a negative one bends outward.
- Character handling scales all three radii.

## Braking and keyboard control

- **Brake while drifting** tightens the arc (up to `driftBrakeTighten` more curvature at
  full brake) and slows you only gently (`driftBrakeDecel` of normal braking), so a dab
  of brake adds bite without ending the drift. In the legacy model braking cancels it.
- **Keyboard steering while drifting** builds more slowly (`input.driftKeyRate`), eases
  back at `driftKeyReturn`, and swings through centre fast (`driftKeyReverse`) when you
  switch direction. A short tap nudges the arc; holding commits to it.

## Countersteer spin-out (optional)

Holding countersteer beyond `spinThreshold` for `spinOutAfterSec` spins the kart out:
the drift ends, the body whirls round over `spinSec`, speed drops to `spinSpeedKeep`,
and steering is limited to `spinSteer`. Easing off resets the count. Set
`spinOutAfterSec` to 0 to turn spin-outs off.

## Comparing

Press **M** in game to flip between the offset model and the legacy M1 model. With
`?debug`, the overlay shows the model, smoothed stick, current arc radius, drift offset
and the spin-out counter.

## Tuning reference

| Key                     | Default | Meaning                                                |
| ----------------------- | ------- | ------------------------------------------------------ |
| `driftModel`            | 1       | 0 legacy, 1 offset model                               |
| `driftSteerSmooth`      | 0.06    | Steering smoothing time, s                             |
| `driftRadiusNeutral`    | 33      | Arc hands-off, m                                       |
| `driftRadiusTight`      | 20      | Tightest arc (full in), m                              |
| `driftRadiusCounter`    | 120     | Arc at full countersteer, m                            |
| `driftInCurve`          | 2       | Diminishing returns steering in                        |
| `driftCounterCurve`     | 1.3     | Finer widening near centre                             |
| `driftOffsetDeg`        | 40      | Body-to-path angle the drift builds to                 |
| `driftOffsetRate`       | 4       | Entry build-up, per s (about 86% in 0.5 s)             |
| `driftOffsetReturnRate` | 4       | Release ease-out, per s                                |
| `driftRecoverSteer`     | 1       | Steering available right after release (1 = full)      |
| `spinThreshold`         | 0.6     | Countersteer amount that counts toward a spin-out      |
| `spinOutAfterSec`       | 1.5     | Seconds of hard countersteer before spinning (0 = off) |
| `spinSec`               | 0.8     | Spin duration, s                                       |
| `spinSpeedKeep`         | 0.5     | Speed kept by a spin-out                               |
| `spinSteer`             | 0.3     | Steering available while spinning                      |

## Wall impacts

How hard a wall hit is depends on the kart's speed _into_ the wall when contact starts.
Each contact is judged once (a clearly harder hit during the same contact counts again),
so scraping along a wall never keeps cancelling a drift.

| Tier     | When                                                          | Effect                                                                       |
| -------- | ------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Light    | below `scrapeSpeed`                                           | No rotation. A drift carries on along the wall.                              |
| Moderate | between the two                                               | A yaw kick turns the nose away from the wall and fades. The drift survives.  |
| Severe   | above `crashSpeed`, or a kick that would pass `driftBreakDeg` | Drift cancelled, kick damped, steering and grip drop, then recover smoothly. |

While drifting, the wall's deflection goes into the drift offset rather than the body, so
the path follows the wall at once and the body only turns gradually. Settings are in the
`collision` section of `tuning.json`; with `?debug`, the overlay shows the last hit.

## Throttle tapping

Tapping the throttle at a steady, moderate rhythm builds a **tap charge** that raises top
speed by up to `tapBonus` (10%). It stacks with the drift speed bonus.

- A tap counts when you press again between `tapMinInterval` and `tapMaxInterval`
  seconds after the last press (about 2.5 to 6.5 taps a second; 3 to 5 is the sweet
  spot), having let go for no longer than `tapMaxGap`. Mashing faster or tapping slower
  doesn't count.
- Each good tap adds `tapGain` charge. The short lifts between good taps don't cost
  speed.
- Once you stop tapping, the charge fades at `tapDecay` per second, so the extra speed
  bleeds away over a second or two.

With `?debug`, the overlay shows the tap charge.
