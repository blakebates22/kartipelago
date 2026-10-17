# Kartipelago

An original adventure kart racer you can play in your browser. Drive, hover and fly
across a chain of islands, race rivals, and unlock new worlds.

> **Status:** Milestone 0 (skeleton). There's no racing yet, just the foundations.
> See the [roadmap](docs/ROADMAP.md).

## Play

The latest build of `main` is deployed automatically to GitHub Pages:
`https://<your-username>.github.io/kartipelago/`

## Run it locally

You need [Node.js](https://nodejs.org) 24 or newer (it includes npm 11, which this project needs).

```bash
npm install
npm run dev      # starts a local server with hot reload
```

| Command             | What it does                                       |
| ------------------- | -------------------------------------------------- |
| `npm run dev`       | Local dev server with hot reload                   |
| `npm run build`     | Production build into `dist/`                      |
| `npm run preview`   | Serve the production build locally                 |
| `npm run typecheck` | TypeScript type checking                           |
| `npm test`          | Run unit tests once                                |
| `npm run format`    | Auto-format all files                              |
| `npm run check`     | Everything CI runs: format, types, tests and build |

## Debug tools

Press the **backtick key** (`` ` ``) in game, or open the page with `?debug` in the URL.

- **Overlay** (top left): FPS, frame time, simulation tick, plus any value a system reports.
- **Tuning panel** (top right): live controls for every value in
  [`assets/data/tuning.json`](assets/data/tuning.json). When something feels right, click
  **Copy tuning JSON** and paste it into the file.

In dev, saving `tuning.json` hot-reloads the values without restarting the game.

## Project layout

```
src/
  core/      game loop, fixed timestep, tuning data
  render/    Three.js renderer, scene and camera
  debug/     overlay and tuning panel
assets/
  data/      tuning.json and other game data
docs/        design doc, architecture, roadmap, milestone specs
tests/       unit tests (Vitest)
```

More folders (`physics/`, `vehicles/`, `race/`, `ai/`, `items/`, `world/`, `ui/`, `audio/`)
are added as the milestones that need them begin. See [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) first, especially the **originality rule**: every
character, track, name, sound and model in this project must be our own or openly licensed.

## License

Code is released under the [MIT License](LICENSE). Asset licenses are listed in
[assets/CREDITS.md](assets/CREDITS.md).
