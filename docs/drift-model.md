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

## Zippers

Zipper pads on the road give a speed boost in the direction you're travelling. They
fire once when you drive onto one; staying on the pad doesn't fire it again. The code
is in `src/vehicles/zipper.ts` (phases), `src/vehicles/kart.ts` (speed) and
`src/world/zippers.ts` (pads). Pads are listed per track as `zippers: [{ at, across }]`
(metres along the lap, metres right of centre).

| Phase    | What happens                                                                          |
| -------- | ------------------------------------------------------------------------------------- |
| ACTIVE   | The zipper pushes speed toward its target at `zipAccel` (fast, but not instant).      |
| ENDING   | Enhanced boosts only: the last `zipRainbowSec`. The exhaust turns rainbow: press now. |
| RECOVERY | The push is over; the extra speed decays back to normal top speed.                    |

- **Ordinary boost** (throttle held when you touch the pad): `zipOrdinaryMult` × top
  speed for `zipOrdinarySec`.
- **Enhanced boost** (throttle released at contact): up to `zipEnhancedMult` × top speed
  for `zipEnhancedSec`, as long as you stay off the throttle.
- **Pressing early** (before the rainbow) cuts the remaining enhanced bonus by
  `zipEarlyPenalty` × the share of the boost still left. It's a gentle cost, not a
  slowdown: you keep at least the ordinary boost.
- **Pressing at the rainbow** carries the speed out: it decays over `zipCarrySec`
  instead of `zipRecoverSec`. Coasting with the throttle off after the push loses speed
  at `zipCoastDrag`.
- **Turning**: drifting is allowed throughout. Turning far harder than normal driving
  (sideways force above `turnScrubFree`) scrubs speed at `turnScrub`, and during an
  enhanced boost also drains the bonus at `zipTurnBleed`. At zipper speeds, a drift
  started right away turns hard and wastes speed; waiting a moment wastes less.
- **Walls**: a light scrape keeps the boost. A severe crash ends it and keeps only
  `zipCrashKeep` of the extra speed. Braking works as normal.

With `?debug`, the overlay shows the phase, time left, remaining enhanced power, whether
you were released at contact or pressed early, acceleration and lateral speed.

`tests/zipper.test.ts` compares ten scenarios from identical starts. Print the table with
`ZIP_REPORT=1 npx vitest run tests/zipper.test.ts --disableConsoleIntercept`.

## Bananas

Bananas lie on the track in rows (`bananas: [{ at, across, count, gap }]` in each
track's JSON). Each one can be taken once per race (R puts them all back); set
`respawnSec` above zero to have them come back that many seconds after being taken.
Drive through one to collect it. Every kart collects them (the AI has no banana
strategy; it just drives over them).

The code is in `src/vehicles/bananas.ts` (count and speed), `src/world/bananas.ts`
(pickups, drops) and `src/render/bananaView.ts`.

**Held vs effective.** A kart counts every banana it holds, but only up to
`bananaMaxEffective` (10) of them add speed. The rest are a reserve: drop two from 12
and you still have the full bonus.

**Speed.** The banana multiplier is `1 + bananaStep × effective` (1.125 at five, 1.25 at
ten). It isn't applied to the current speed. It feeds the normal driving model:

- acceleration under throttle × (1 + extra × `bananaAccelShare`), so ten bananas = 25%
  more acceleration;
- the throttle's top speed × (1 + extra × `bananaTopShare`), so ten bananas = 15% more
  top speed (22 → 25.3 m/s for the base kart).

The kart accelerates naturally to its new top speed; losing bananas lets the extra bleed
off at the normal drag rate. Steering, grip and the drift line are unchanged. Drift's
own speed bonus and tapping stack on top as before.

**Zippers.** The push itself (target, acceleration, timing, the released-throttle
enhanced boost) ignores bananas. Afterwards, speed settles back to the kart's own normal
top speed, bananas included, so bananas help before and after the boost. Collecting a
banana never touches the boost timer.

**Losing bananas.** `loseBananas(kart, event, cfg)` removes up to `lossWeapon` (2),
`lossSpin` (0), `lossSquash` (0) or `lossDebug` (2) bananas, never below zero, and
returns how many were lost. Walls never cost bananas. The lost ones are thrown out of the
kart (`dropBananas`): outward and up, falling, sliding to a stop on the road. They can be
collected only once they've settled (and at least `dropPickupDelay` after the drop).
Dropped bananas don't respawn.

**Debug.** With the overlay showing (`?debug` or backtick): L loses two bananas as a hit
would, K adds one. The overlay shows held/effective count, the multiplier, the resulting
top speed and acceleration scale, actual speed, acceleration and boost state.

`tests/bananas.test.ts` measures 0, 1, 5, 9, 10, 11 and 12 bananas (acceleration, speed
at 3 and 5 s, top speed, distance, an identical zipper, an identical drift) and losing two
at different counts. Print the table with
`BANANA_REPORT=1 npx vitest run tests/bananas.test.ts --disableConsoleIntercept`.
