# The race start: GET READY... GO!

Every race opens with **GET READY...** for `race.readySec` (1.33 s: about 80 frames at
60 fps, from Blake's notes on the N64 original), then **GO!**, the moment every kart is let
go. GO! stays up for `race.goShowSec`.

## The start boost

What counts is when you **first** press the throttle during GET READY, counted in frames
of a 60 fps reference (`race.startRefHz`) before GO, and that you're **still holding it
at GO**. The windows come from Blake's notes on the original's `handle_racer_top_speed()`:

| First press                                   | Result         | Tier       |
| --------------------------------------------- | -------------- | ---------- |
| 35 or more frames before GO (0.58 s or more)  | no boost       | `early`    |
| 20 to 34 frames before GO                     | weak boost     | `weak`     |
| 1 to 19 frames before GO (about 17 to 317 ms) | strong boost   | `strong`   |
| at or after GO                                | ordinary start | `none`     |
| let go before GO (any press)                  | no boost       | `released` |

- Only the first press counts. Let go before GO and the boost is lost for this start:
  pressing again doesn't earn another try, so tapping can't game it.
- A throttle already held when GET READY appears isn't a press.
- `race.startStrongFrames` (19) and `race.startWeakFrames` (34) set the window edges.
  (Blake, Oct 25: five frames more lenient than the notes' 1-14 for a strong start; the
  weak window moved along with it.)

### What the boost does

The strength is the start boost the game has always had (Blake asked to keep it: it makes
the start feel fast); only the timing above is new. At GO the kart is launched at a
multiple of its top speed and held there for a while (`vehicles/kart.ts`, `applyBoost`):

| Tier   | Launch                                   | Held for                      |
| ------ | ---------------------------------------- | ----------------------------- |
| strong | `race.startStrongMult` (2.0) × top speed | `race.startStrongSec` (2.0 s) |
| weak   | `race.startWeakMult` (1.2) × top speed   | `race.startWeakSec` (0.8 s)   |

These are **our tuning, not values from the original**: adjust them in the Tuning panel's
`race` folder.

Feedback: a launch whoosh (the strong start adds a two-note fanfare), and STRONG START! /
GOOD START under GO!.

## Frame-rate independence

- The race clock advances in fixed simulation steps (120 Hz, `loop.physicsHz`), whatever
  the display's frame rate. The windows are converted from frames to seconds
  (`frames / startRefHz`) and compared with that clock.
- A frame runs its fixed steps in a burst, each standing for a moment a little before
  the frame. Throttle presses carry the time they happened (the key event's
  `timeStamp`, or the gamepad's own `timestamp`), and a press only counts from the step
  it happened in (`core/input.ts: downAt`). So pressing at the same instant gives the
  same result at 30, 60, 120 or 144 fps. The resolution is the 120 Hz step: half a
  reference frame.
- Keyboard and gamepad (A or the right trigger) share the same throttle and timing.

## Rivals

Rivals sit still until GO like everyone else. Each first presses the throttle
`ai.startAimFrames` (10) frames before GO, give or take up to `ai.startSpreadFrames` (12),
fixed per rival so races repeat. That lands most of them in the strong or weak window and
some on an ordinary start; none is given a boost it didn't time. (There's no difficulty
setting yet: these two numbers are the knob for one.)

## Tuning tool

`?timing` in the URL shows a timeline of the countdown with the weak and strong windows,
where you pressed, and the result in frames before GO.

## Tests

`tests/race.test.ts` (windows, edges, release rule, holding early, fixed-step and
30/60/120/144 fps rendering), `tests/input.test.ts` (keyboard and gamepad throttle, press
timing) and `tests/ai.test.ts` (no rival moves before GO; rivals get a mix of starts).
