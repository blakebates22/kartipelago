# Contributing to Kartipelago

Thanks for helping. This project grows one small, playable step at a time.

## The originality rule

Kartipelago is inspired by the _style_ of classic adventure kart racers: multiple vehicle
types, a hub world, stackable power-ups. It is **not** a remake or port of any existing game.

- Do not add ripped, extracted, traced or recreated assets (models, textures, music,
  sounds, track layouts) from any commercial game.
- Do not use names, characters, logos or trademarks from existing games.
- All assets must be original or carry a license that allows redistribution (CC0, CC-BY,
  etc.). Record every third-party asset in [`assets/CREDITS.md`](assets/CREDITS.md).

PRs that break this rule will be closed, however good the work is.

## How we work

1. **One milestone at a time.** Work is planned in [docs/ROADMAP.md](docs/ROADMAP.md),
   and each milestone has a spec in `docs/milestones/`.
2. **Small issues, small PRs.** If a PR touches more than a few systems, split it.
3. **`main` is always playable.** Every merge deploys. Never merge something that breaks
   the game, even temporarily; hide unfinished work behind a debug toggle instead.
4. **Feel values go in data.** Speeds, grip, camera distances and similar values belong in
   `assets/data/*.json`, not in code.
5. **Simulation runs on the fixed step.** Anything that affects gameplay goes in `update()`
   (fixed timestep), never in `render()`. See [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Workflow

```bash
git checkout -b m1/basic-steering   # milestone/short-description
npm run dev
npm run check                       # run before pushing
```

Open a PR against `main` and fill in the template. CI must pass before merging.

## Code style

- TypeScript in strict mode. Prettier formats everything (`npm run format`).
- Prefer small modules with plain functions and data. Avoid deep class hierarchies.
- Comment _why_, not _what_.
- Add a unit test for logic that can be tested without a browser (math, race rules, data).

## Commit messages

Short and imperative: `Add drift input`, `Fix lap counter on reverse driving`.
Reference the issue when there is one: `Add checkpoint triggers (#12)`.
