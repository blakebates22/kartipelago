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
