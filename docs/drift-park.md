# Drift Park

A practice map for tuning and learning the drift: twelve separate loops, each meant to
be driven all the way round in **one drift, without letting go**.

Open it with `?scene=drift` (add `&loop=5` to start on loop 5).

| Key     | What it does                                          |
| ------- | ----------------------------------------------------- |
| `[` `]` | Previous / next loop (puts you on its start line)     |
| `F`     | Flip direction (drive the loop turning the other way) |
| `R`     | Back to the start of the current loop                 |

The bar at the bottom shows your **drift streak**: how far round the loop you've gone in
one unbroken drift while staying on the road. Letting go, spinning out or leaving the
road ends it. Each whole lap pops up a message, and your best streak per loop is kept in
this browser.

## How the loops are shaped

The loops aren't hand-drawn; the drift's own geometry sets them (`src/world/driftPark.ts`,
built when the page loads from the current tuning):

- A drift holds one direction, so every loop turns one way all round: no straights, no
  S-bends.
- The tightest a drift carves is `driftRadiusTight` (26 m at full lock; a dab of brake
  adds a little more).
- The widest it can hold for long is the **spin radius**: countersteer past
  `spinThreshold` for `spinOutAfterSec` spins you out, and that steer carves about 60 m.
  Wider than that only works in short bursts.

Each loop's curvature rises and falls smoothly between a tightest and a widest radius a
few times round (a rounded triangle, oval or pentagon), so holding the stick still never
works: you steer in through the tight parts and ease out through the wide ones.

| Size    | Shape            | Radius on the centre line | Lap   | What it teaches                                   |
| ------- | ---------------- | ------------------------- | ----- | ------------------------------------------------- |
| Tight   | rounded triangle | 34–40 m                   | 230 m | near full lock all the way; the entry swing       |
| Neutral | oval             | 36–55 m                   | 274 m | either side of hands-off (42 m)                   |
| Wide    | rounded triangle | 38–63 m                   | 297 m | countersteer, up to the spin radius               |
| Grand   | rounded pentagon | 44–81 m                   | 359 m | bursts past the spin radius: ease off to reset it |

The radii scale with the drift settings, so if the drift radii or the spin-out are
retuned, the loops follow on the next reload. All loops are 12 m wide (`driftPark.loopWidth`).

### Three of each

- **Plain** (top row, loops 1–4).
- **Bananas** (middle row, 5–8): a row on the inside at each tight part and singles
  between, inside and out. They come back `driftPark.bananaRespawnSec` (3 s) after you
  take them, so they're there again next lap.
- **Zipper** (bottom row, 9–12): a zipper just past the start line, and a second one on
  the bigger loops, on the wide parts. Drifting at zipper speed scrubs speed and swings
  wider, so these practise holding the line through a boost.

## Tips the loops teach

- **Start the drift on a wide part, from the inside of the road.** The entry swings you
  outward while the drift angle builds; on the Tight loop that swing is most of the
  road.
- On the Tight loop a light touch of brake tightens the arc without ending the drift.
- On the Grand loop, don't hold hard countersteer for more than about a second: ease
  off briefly and the spin-out count starts again.

## Tests

`tests/driftPark.test.ts` drives every loop with a test driver (pure pursuit, entering
from the inside before a wide part, a light brake when it needs more than full lock, and
countersteer past the spin point only in short bursts). It checks that each loop can be
held for three laps in one drift both ways round, through the zippers too, and that
holding the stick still always runs off the road. Run it with `PARK_REPORT=1` and
`--disableConsoleIntercept` to print how close to the edge the driver gets on each loop.
