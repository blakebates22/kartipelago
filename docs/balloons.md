# Balloons and weapons

Balloons float over the track (`balloons: [{ at, across, color }]` in each track's JSON)
and come back `items.balloonRespawnSec` after being taken. Press and **release** the
item button (E or F; B or Y on a gamepad) to use what you hold. The HUD shows it.

Code: `src/items/` (inventory, boosts, effects, world), `render/itemView.ts`,
`debug/boostLab.ts`. Every number is in the `items` section of `tuning.json`.

## Inventory

Colour, level and ammo are stored separately (`inventory.ts`).

- The same colour again upgrades what you hold (while it has ammo), up to level 3.
- At level 3, the same colour refills the ammo.
- A different colour replaces it, at level 1.
- Once the ammo is used up you hold nothing, so the next balloon is level 1.

| Colour  | Level 1       | Level 2        | Level 3                              |
| ------- | ------------- | -------------- | ------------------------------------ |
| Red     | missile       | homing missile | 10 missiles                          |
| Blue    | boost 0.58 s  | boost 0.92 s   | boost 1.25 s                         |
| Green   | oil slick     | mine           | bubble trap                          |
| Yellow  | shield 5 s    | shield 10 s    | shield 15 s                          |
| Rainbow | magnet (50 m) | magnet (75 m)  | reverse magnet: pulls a rival to you |

AI rivals don't pick up balloons yet (`aiCollect`), but they can be hit.

## Blue boosts

All three levels use the same boost as a zipper pad (`vehicles/zipper.ts`). They share
the same acceleration toward the same target speeds, the same released-throttle
enhanced flag, the same early-press cost, rainbow window and recovery. **Only the timer
differs**: `blue1Sec` / `blue2Sec` / `blue3Sec`.

**From the original (verified):**

- The timer values, converted at 30 updates a second.
- The timer starts on activation.
- Every level checks whether the accelerator is released at that moment.
- That check sets an enhanced flag, which changes the exhaust.

**Our own tuning (not from the original):**

- How much faster the enhanced boost goes (`zipEnhancedMult` vs `zipOrdinaryMult`).
- The cost of pressing early (`zipEarlyPenalty`).
- The rainbow window (`zipRainbowSec`, capped at `zipRainbowMaxShare` of a short boost).
- The carry from a well-timed resume (`zipCarrySec` vs `zipRecoverSec`).
- Drift and turn losses, which come from the normal handling (`turnScrub`).

**What you see and hear:**

- The exhaust colour says which boost it is: zipper amber, blue 1 orange, blue 2 blue,
  blue 3 purple.
- A green core inside the flame means the enhanced boost took, with a double chime.
- The flame turns rainbow, with a blip, when it's time to press the throttle again.
- The flame shrinks and dims, with a puff, when the push ends.
- Level 3 plays a charging sound and then its boost sound `blue3ChargeSec` later, and
  its flame builds over that time. The physics started at once.

**Overlap rule.** One boost at a time. A new boost (balloon or zipper) **replaces** the
active timer, as the original does. That can shorten it. Speed is kept, and the
enhanced flag is judged again from the throttle at the new activation. Set
`boostOverlap` to 1 to keep whichever has longer left instead. A severe crash (wall, or
any weapon hit) ends the boost and keeps `zipCrashKeep` of its extra speed. Bananas
never scale the push itself; they raise the normal top speed it settles back to.

## Weapons

Weapons move and collide in `items/world.ts`, separately from vehicle physics. A hit
calls `hitRacer`, which only sets state the handling already understands: a spin-out,
lost speed, a pop into the air, or a boost ending.

| Hit     | Effect                                          | Bananas lost |
| ------- | ----------------------------------------------- | ------------ |
| Missile | spin-out, speed × 0.3, pops up                  | 2            |
| Mine    | spin-out, speed × 0.2, launched                 | 2            |
| Oil     | spin-out, speed × 0.6                           | 0 (a spin)   |
| Bubble  | held in place for `bubbleSec` (2 s), no control | 0            |

- **Missiles** launch along the nose, plus the kart's own velocity. Homing missiles pick
  the nearest rival ahead in `homingRange`. They aim straight at the target within
  `homingDirect`, and otherwise follow the road ahead toward it, so they go round
  corners. Missiles explode on walls, tunnel rock, trees and the boundary.
- **Traps** drop `trapBehind` metres behind the kart. The racer who dropped one can't
  set it off for `trapOwnerGrace` seconds.
- **Shields** block missiles and traps (the trap is used up). A shielded kart is
  `shieldMass` times heavier in bumps, so it shoves others aside. It flickers in its
  last second.
- **Magnets** need a rival ahead within range, and keep the balloon if there isn't one.
  The original's ranges are in game units; `magnetUnit` (0.05 m per unit, a guess)
  converts them. Levels 1-2 turn you toward the target and speed you up to
  `magnetSpeedMult` × top speed for `magnetSec` (1.5 s). Level 3 brakes the rival and
  drags them toward you for `reverseMagnetSec` (2 s). It moves them at `reversePull` m/s,
  never teleporting.
- After any hit, a racer can't be hit again for `hitImmuneSec`.

## Calibration tools

With the debug overlay showing (`?debug` or backtick):

- Open the **Balloon test** panel at the bottom of the tuning panel. Pick a balloon and
  level, then press **B** (or "Equip") to hold it.
- **Throttle after firing** scripts the throttle for 3 s from the moment a balloon
  fires (or a zipper is hit): hold, stay released, resume after 0.2 / 0.4 / 0.6 s, or at
  the rainbow. The script also decides the throttle at the moment of firing. Set it to
  "manual" to drive yourself.
- The **speed graph** plots speed against time for your last boost, with the previous
  one as a ghost. It shades the push and the rainbow window, and shows peak speed and
  when it was reached, distance at 1 / 2 / 3 s, and metres gained over normal driving.

`tests/blueBoost.test.ts` runs the ten scenarios for each level from identical starts.
Print the table with
`BLUE_REPORT=1 npx vitest run tests/blueBoost.test.ts --disableConsoleIntercept`.
