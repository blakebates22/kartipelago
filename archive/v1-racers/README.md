# The first racers (archived)

These are the first versions of the four racers and the old character select screen, kept
for reference. They are not built or loaded by the game.

- `roster/tiko.ts`, `brakka.ts`, `pebble.ts`, `zephyr.ts`: the original heads and the chunky
  toy karts (fenders, timber slats, the log on Brakka's back).
- `screens/characterSelect.ts`: the 3D jungle-clearing select screen (the racer turning on
  a stone pedestal, the others waiting in front).

They were replaced in October 2026 by the redesigned heads (bolder eyes and head shapes),
the sleek kart family (`src/render/racers/kit/sleek.ts`) and the pixel roster select
(`src/screens/characterSelect.ts`).

To see them in the game again, check out the commit tagged `v1-racers`, or copy a file back
over its replacement in `src/` (the imports are relative to `src/render/racers/roster/` and
`src/screens/`).
