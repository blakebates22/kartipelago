# Time Trial ghosts

Race your own best. Every Time Trial records your run, and the fastest finished run on
each course is saved and comes back as a see-through racer the next time you race there.
The idea comes from classic kart racers' time trials (Blake's brief). It's our own
design and code.

## What you see

- **The ghost:** a pale, see-through copy of the racer who set the time, on their kart.
  It sits on the line through GET READY..., goes at GO and drives its run exactly: the
  same line, drifts, sharp turns (on two wheels), jumps, shortcuts and boosts (flames
  and all). It doesn't react to you, and nothing touches it. It fades out at its finish.
- **The HUD** (top right): total time, lap time, best lap, then **PB** (your personal best
  race on this course) and **GHOST** while one is racing you. At each checkpoint, the
  gap to the ghost at the same checkpoint pops up in the middle for 3 s: green `-0.42`
  when you're ahead, red `+0.42` behind. It's measured by checkpoint (equal progress),
  not by who's physically nearer.
- **On / off:** Options > General > TIME TRIAL GHOST (PERSONAL BEST or OFF), or GHOST:
  ON/OFF in the pause menu during a Time Trial (it switches at once).
- Time Trial keeps only the **blue balloons** (the boosts). The weapons and shields
  have nobody to use them on.

## When a ghost is saved

Only a valid finished run, and only if it's faster than the saved one:

- every lap validated by the checkpoints (a skipped gate or an incomplete lap never
  finishes);
- not restarted, abandoned or touched by a debug tool on the way (`K` eggs, the review
  tool's "drive from here", the debug finish);
- a slower run never replaces a faster ghost, even if two saves race each other.

After a new best, the next attempt (RESTART, or coming back later) races it.

## How it works

- **Recording** (src/game/ghost.ts, src/game/ghostRunner.ts): on the fixed physics step,
  a timestamped snapshot about 30 times a second (`tuning.json` `ghost.hz`). Each one
  holds the kart's position, the body's tilt (as the race draws it: on the surface, or
  pitched in a jump, or on a loop), the sharp-turn roll, speed, steering, drift,
  slide, airborne, throttle and boost state. Plus the run's total, its laps and the race
  clock at every checkpoint. It records what was drawn, not the buttons pressed, so it
  doesn't depend on the physics replaying identically.
- **Playback:** by the race clock (so it's in step whatever the frame rate, stops when
  you pause, starts over when you restart), between the two physics steps each frame
  shows. Positions follow a Catmull-Rom curve through the snapshots (it passes through
  every one, so there's no drift); rotations slerp the shortest way, smoothed like your
  own kart's tilt. A respawn (a jump between snapshots faster than any kart) is shown as
  the cut it was, never as a slide.
- **Accuracy** (tests/ghost.test.ts): over a whole 3-lap AI race of Oasis Haven, traced
  every physics step and recorded at 30 Hz, the ghost is within 12 cm of the true path
  at every step between snapshots, in the air too, and within 3.5 degrees of its
  heading. Through an R+B sharp turn: within 8 cm, its roll within 3.5 degrees. In the
  browser, an autopilot run raced its own saved ghost and matched it to the decimetre.
- **Storage** (src/app/ghostStore.ts): IndexedDB (`kartipelago` > `ghosts`), gzipped
  where the browser can. A ghost is about 36 bytes a snapshot, so about 115 KB for a
  2-minute run before compression. Times also go to the usual records (records.ts). One
  ghost per course, _layout_ and _physics_: the key carries fingerprints of the course's
  centre line, gates and boosts, and of the driving tuning (vehicle, physics, collision,
  stats, laps). A ghost set on an older version never races a newer one. The stored
  format has a version too (`GHOST_FORMAT`).
- **Later:** `GhostChoice` is `"best" | "off"`. Developer ghosts or challenge ghosts
  (beat this time to unlock...) would be more choices: a ghost file shipped with the
  course, loaded the same way.
