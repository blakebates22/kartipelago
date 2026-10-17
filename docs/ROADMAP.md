# Roadmap

Each milestone ends with something playable on the deployed site. Only the current
milestone gets detailed planning; later ones stay rough on purpose.

| #   | Milestone        | Playable result                                                   | Status  |
| --- | ---------------- | ----------------------------------------------------------------- | ------- |
| M0  | Skeleton         | A box renders; CI and Pages deploy work; debug tools toggle       | Done    |
| M1  | Drive a box      | Drive a box on a flat plane with steering, drift and chase camera | Done    |
| M2  | First track      | One track with ground following, walls, checkpoints, laps, timer  | Next    |
| M3  | Rivals           | AI racers follow a racing line; positions and a finish screen     | Planned |
| M4  | Items and boosts | Pickups, a few items, boost pads, drift and start boosts          | Planned |
| M5  | Water and sky    | Hovercraft and plane controllers on the shared vehicle interface  | Planned |
| M6  | Menus            | Title, character select, track select, HUD                        | Planned |
| M7  | Adventure        | A small hub island where doors start races; progress is saved     | Planned |
| M7b | Track builder    | An in-browser editor to lay out, shape and test tracks            | Ideas   |
| M8  | Beyond           | More tracks, bosses, challenges, split-screen, audio polish       | Ideas   |

## How a milestone runs

1. Write the spec in `docs/milestones/` covering the goal, the "done" test and what's
   deliberately excluded.
2. Create a GitHub milestone and break the spec into small issues.
3. Build in small PRs; `main` stays playable.
4. Playtest the deployed build. Note what feels wrong.
5. Close the milestone, update this table, and fold the playtest notes into the next spec.
