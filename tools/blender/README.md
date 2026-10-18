# Kartipelago Track Tools (Blender)

A small Blender add-on for making Kartipelago tracks: spline roads that rebuild live as
you edit the curve, a library of N64-style textures to paint them with, semantic
surfaces, vertex-colour shading presets, and one-click export into the game. The full
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
- **Materials:** pick a theme and a texture, pick how it drives (**Surface**), then
  **Apply** to selected faces (Edit Mode), selected objects, or part of a road. UVs are
  projected for you. See [docs/materials.md](../../docs/materials.md).
- **Water & Lava**, **Vertex Paint**, **Sky & Fog:** flowing water and glowing lava,
  one-click shading (darker cliff bottoms, warm sunlight, dark tunnels...), and the
  track's sky and fog.
- Set **Track ID** and press **Export Track**. With `npm run dev` running and
  `?track=<id>` open, the game reloads it on its own.

## Sample

`tracks-src/bridge_test.blend` is the Bridge Test track, and `tracks-src/dino_demo.blend`
is Dino Demo, painted entirely from the material library. They're made by:

```
blender --background --python tools/blender/build_bridge_test.py
blender --background --python tools/blender/build_dino_demo.py
```

## Licence

MIT, like the rest of Kartipelago, including the textures in `library/` (original work
for this project).
