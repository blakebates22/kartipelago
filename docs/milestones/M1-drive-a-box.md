# M1: Drive a box

> Draft. Refine this together before starting.

## Goal

A box you can drive around a large flat plane, and it already feels fun.

## Done when

- [ ] Keyboard and gamepad input go through one input module (`core/input.ts`).
- [ ] Throttle, brake/reverse and steering, with speed-dependent steering.
- [ ] A drift button that slides the car and gives a small boost on release.
- [ ] A chase camera with smoothing and slight look-ahead.
- [ ] Every handling value lives in a `vehicle` section of `tuning.json`.
- [ ] The overlay shows speed, drift state and grip.
- [ ] Ten minutes of driving in circles is enjoyable.

## Not in this milestone

Hills, collision, tracks, other racers, sound.

## Open questions

- Arcade "always grippy" handling, or more slide and weight?
- Should drift have charge levels (longer drift, bigger boost)?
