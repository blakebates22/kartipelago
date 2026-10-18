# Kartipelago Track Tools (Blender)

A small Blender add-on for making Kartipelago tracks: spline roads that rebuild live as
you edit the curve, semantic surfaces, and one-click export into the game. The full
guide is in [docs/track-pipeline.md](../../docs/track-pipeline.md).

## Install

Blender 5.1 or newer is recommended.

1. **Edit ▸ Preferences ▸ File Paths ▸ Script Directories**: add this `tools/blender`
   folder.
2. Restart Blender. In **Preferences ▸ Add-ons**, enable **Kartipelago Track Tools**.

Because Blender loads the add-on from the repo, it stays up to date with `git pull`.

## Use

Open the sidebar (N) in the 3D view and pick the **Kartipelago** tab.

- **Add Road**, then edit the curve:
  - move points and handles;
  - **G Z** for height;
  - **Ctrl+T** for banking;
  - **Alt+S** for width.
- **Set as Route** on the main road curve.
- **Role** and **Set Surface** for other objects (terrain = grass, rocks = wall…).
- Set **Track ID** and press **Export Track**. With `npm run dev` running and
  `?track=<id>` open, the game reloads it on its own.

## Sample

`tracks-src/bridge_test.blend` is the Bridge Test track. It's made by:

```
blender --background --python tools/blender/build_bridge_test.py
```

## Licence

MIT, like the rest of Kartipelago.
