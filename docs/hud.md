# HUD

The item box sits in the bottom-left corner, the eggs beside it: see
[balloons.md](balloons.md).

Drifting (or sliding hard) plays a tyre squeal (`sfx.skid`), louder the more you slide
and higher at speed, with a bark of the tyres going into a drift. It's mostly tone, with
only a low rumble of scrub, so it never turns into a hiss. Only your own kart skids
out loud.

## Speedometer

The speedometer sits in the bottom-right corner (`src/render/speedometer.ts`): a
wooden barrel dial with metal bands and a palm leaf, a red star needle, a digital
readout and a wooden BOOST sign. It's pixel art: every pixel is set by hand on a
124 × 96 canvas that's scaled up by a whole number (2× on a laptop, 3–4× on big
screens) with no smoothing, so the pixels stay square and crisp.

- **Unitless and true to the physics.** The number is the kart's real ground speed
  times one fixed scale, with no smoothing (`src/render/speedo.ts`). The scale is set so
  the fastest push in the game, an enhanced boost at the base top speed
  (22 m/s × 2.4 = 52.8 m/s), reads `hud.speedoFastest` (150). Plain top speed reads
  about 62, a held-throttle boost about 100. The scale is the same for every racer, so a
  faster character really reads higher, and it follows `vehicle.topSpeed` and
  `vehicle.zipEnhancedMult` if those are retuned.
- **Dial.** It sweeps 270° from 0 to `hud.speedoDialMax` (180), with coloured blocks lit
  up to the current speed. Anything faster pegs the needle just past the last mark while
  the number keeps counting.
- **BOOST sign.** The chevrons light while a boost pushes, in the exhaust colour (zipper
  amber; blue balloons orange, blue or purple by level), and go out as the boost's time
  runs down. They cycle through the rainbow during the "press the throttle now" window,
  and the BOOST lettering lights up during an enhanced boost.
