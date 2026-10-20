# Materials: painting tracks in the late-N64 style

Kartipelago tracks are painted in Blender with a small library of low-resolution,
repeating textures, vertex colour shading and simple light, the way late-90s console
racers were. This page covers how that works, from the Blender panel to the game's
renderer. For roads, collision and export in general, see
[track-pipeline.md](track-pipeline.md).

Everything here is original work for this MIT-licensed project. The texture themes are
_inspired by_ the kind of prehistoric worlds that era loved (a lake, a fossil canyon, a
jungle, a volcano). They aren't copies of any game's textures, levels or designs, and
nothing is extracted from any ROM.

## The ideas

Four principles, all borrowed from how games of that era were built:

1. **Each track uses a small set of textures.** Faces pick one by material and map it
   with UVs.
2. **What a surface looks like is separate from how it drives.** A golden dirt picture
   can be a full-grip road in one place and slow off-road in another.
3. **Vertex colours do the shading.** Darker cliff bottoms, warm sunlit faces, gloomy
   tunnels: painted onto the geometry, multiplied into the texture.
4. **Small textures, on purpose.** 64×32 or 32×32 pixels, a handful of colours each,
   repeated across the world. No normal maps, no shiny highlights.

## In Blender

Open the sidebar (**N**) in the 3D view and pick the **Kartipelago** tab. Besides the
Track panel there are four more panels.

### Materials

1. Pick a **Theme**: Ancient Lake, Fossil Canyon, Jungle Falls, Hot Top Volcano, or All.
   Type in the search box to filter by name.
2. Click a texture. Either click the big thumbnail for a grid of every texture in the
   theme, or click one of the buttons below it.
3. Choose the settings:
   - **Surface:** how it drives (road, dirt, grass, sand, water, lava, wall...). Leave it
     on _Suggested_ to use the library's choice for that picture.
   - **Repeat Size:** how many metres one copy of the texture covers. 0 means the
     library's suggestion.
   - **Rotation:** 0°, 90°, 180° or 270°.
   - **Edges:** Repeat tiles the texture. Clamp stretches the edge pixels, for a one-off
     decal.
4. Press **Apply**. What it does depends on what's selected:
   - **Edit Mode** (Tab): the texture goes on the selected faces only.
   - **Object Mode:** the texture goes on every face of the selected objects.
   - **A road curve:** the texture goes on the **Road Part** you pick: road, shoulders,
     barriers or underside.

**Show Textures** switches the 3D view to Material Preview, so you see the textures
and the vertex paint. **From Active** loads the active object's texture back into the
browser.

#### UVs are done for you

Apply projects the texture from the world, so it has the same size everywhere:

- **Floors** (anything flatter than 45°) are mapped from above.
- **Walls and cliffs** are mapped from the side, with the texture kept upright. That's
  why cliff strata run level.
- **Texels stay square.** A 64×32 texture with a 4 m repeat covers 4 m across and 2 m
  the other way.

Each face remembers its repeat size and rotation. If you then reshape a mesh, export
re-projects those faces automatically (or press **Refresh UVs** to see it now), so
textures never stretch.

If you'd rather make a face's UVs by hand, select it and press **Keep My UVs**. Export
then leaves that face alone.

#### Roads

Roads build their own UVs, which follow the curve:

- **Along the road:** the texture is measured along the road's real 3D length, so hills
  and banking don't stretch it. Each road is fitted to a whole number of repeats, so
  where two roads meet, or where a loop closes, the texture joins without a seam.
- **Across the road:** the texture is measured in metres, scaled with the point
  **Radius**, so a widened section isn't stretched either.

When you put a library texture on a road's surface, the road's **Texture Width** and
**Texture Repeat** are set from it. Rotation 90° or 270° turns the texture
(**Turn Texture**).

Older roads have **Texture Width 0**. That's the original behaviour: one copy of the
texture stretched across each part, which suits the striped asphalt.

#### The same picture, different surfaces

The surface lives on the material, so the same image with a different surface is a
separate material, named after the picture plus the surface in brackets. Dino Demo uses
the Ancient Road picture three ways:

| Material                 | Where                      | Drives like |
| ------------------------ | -------------------------- | ----------- |
| `KP Ancient Road`        | the road                   | road        |
| `KP Ancient Road [dirt]` | the tunnel floor beside it | dirt        |
| `KP Ancient Road [sand]` | the lake bed               | sand        |

**Set Surface** on the Track panel works the same way: on a library material it swaps
in the version with the new surface, and the picture stays the same.

### Water & Lava

These settings belong to the active object's material:

- **Flow Across / Flow Along:** how fast the texture scrolls, in repeats per second.
- **Ripple / Ripple Time:** a small looping wobble, and how many seconds each loop
  takes.
- **Opacity:** below 1 you can see through it (water).
- **Glow:** it shines with its own light, whatever the shade (lava).
- **Tint:** multiplies the texture's colour.

Ancient Water and Volcano Lava come with sensible settings already. The animation runs
in the game, not in Blender (glTF has no way to carry it), and it is purely visual.
Whether water slows you down, or lava sends you back, is the material's **Surface**.

### Vertex Paint

Each preset paints colour variation onto the selected objects, or onto just the selected
faces in Edit Mode. Presets add to what's already there, so you can layer them; **Reset
to White** starts again.

| Preset                   | Does                                                 | Good for                 |
| ------------------------ | ---------------------------------------------------- | ------------------------ |
| **Darken Bottoms**       | darker towards the bottom of the selection           | cliff bases, rocks       |
| **Lighten Tops**         | lightens faces that point up (undoes darkening)      | exposed ledges           |
| **Warm Sunlight**        | warm on the sun's side, cool and darker away from it | everything, lightly      |
| **Tint Near Roads**      | tints ground within _Distance_ of any road           | worn, dry grass by roads |
| **Darken Under Cover**   | darkens anything with geometry above it              | tunnels, under bridges   |
| **Blend Material Edges** | tints where two materials meet                       | soft terrain transitions |

The panel's **Strength**, **Tint** and **Distance** settings apply to every preset.
Colours multiply, so presets can darken and tint, but can't go brighter than the
texture.

Roads are shaded differently. Select a road and press **Darken Under Cover**. The road
then darkens itself wherever something is above it, live, by casting a ray straight up
against the **KP Shade Casters** collection (the track's visible meshes, refreshed on
export).

For freehand painting, Blender's own **Vertex Paint** mode (the mode menu, top left)
paints the same colour attribute, `Col`.

### Sky & Fog

Pick an environment for the track's sky colour, sun, ambient light and distance fog.
The four themes each have one. **Game Default** keeps the game's usual blue sky. **Distance
Fog** turns the fog on or off.

## What gets exported

| What                 | Where                            | How                                    |
| -------------------- | -------------------------------- | -------------------------------------- |
| Textures             | inside `visual.glb`              | glTF images: the library PNGs, packed  |
| Texture mapping      | `visual.glb`                     | `TEXCOORD_0`, projected by the add-on  |
| Repeat / clamp       | `visual.glb`                     | glTF sampler wrap mode                 |
| Vertex paint         | `visual.glb`                     | `COLOR_0` (the `Col` colour attribute) |
| Tint                 | `visual.glb`                     | base colour factor                     |
| Glow                 | `visual.glb`                     | emissive texture × factor              |
| Opacity              | `visual.glb`                     | base colour alpha, `alphaMode: BLEND`  |
| Driving surface      | `visual.glb` and `collision.glb` | material extra `kp_surface`            |
| Library texture id   | `visual.glb`                     | material extra `kp_texture`            |
| Water/lava animation | `visual.glb`                     | material extra `kp_fx`                 |
| Sky, sun, fog        | `look.json`                      | written on every export                |

Anything glTF can describe uses standard glTF. Only things glTF has no slot for travel as
material extras (custom properties) or in `look.json`.

`kp_fx` holds:

```json
{ "scroll_u": 0.03, "scroll_v": 0.015, "wave": 0.04, "wave_period": 4, "opacity": 0.85 }
```

The game reads `scroll_u` and `scroll_v` (texture repeats per second), and `wave` and
`wave_period` (a circular wobble, as a fraction of a repeat, and its loop time in
seconds). Opacity, glow and tint are also stored there, so Blender can show them, but
the game takes those three from the standard glTF fields.

`look.json`:

```json
{
  "schemaVersion": 1,
  "theme": "ancient_lake",
  "sky": "#8fd3ff",
  "fog": { "enabled": true, "color": "#c4e7fa", "near": 150, "far": 680 },
  "sun": { "color": "#fff0d2", "intensity": 2.3, "direction": [0.55, 0.75, 0.35] },
  "ambient": { "sky": "#e2f4ff", "ground": "#5d7a3a", "intensity": 1.15 }
}
```

How it's read:

- `direction` points towards the sun, in game coordinates (y up).
- Anything missing, or malformed, falls back to the game's default, with a warning in
  the console.
- Tracks exported before `look.json` existed simply don't have one.
- An environment can also ask for a **painted sky** with `skyDome`: a gradient dome
  (`top`, `horizon`, `bottom`), a glowing sun where the sunlight comes from
  (`sun: { color, size, glow, elevation }`, size in degrees; `elevation` puts the disc
  lower than the light really comes from, so it shows while racing), and cartoon clouds round the horizon
  (`clouds: { count, color, shade, seed, low, high, drift }`, heights in degrees above
  the horizon, drift in radians per second), and rings of distant hills
  (`hills: { color, far, height, seed, layers }`: `color` is the nearest ring, `far` the
  farthest, `height` in degrees above the horizon) so a course's edges never open onto
  empty sky. Every field is optional. River Valley (Riverbend Palms) and Jungle Falls
  (Cascade Caverns) use one; without it the sky is the flat `sky` colour. The code is
  `src/render/skyDome.ts`.

Re-exporting never touches `track.json`. Placements, checkpoint order and physics are
unaffected by anything on this page.

## In the game

`src/render/trackMaterials.ts` turns the exported materials into simple diffuse
(Lambert) materials:

- **What's drawn:** texture × vertex colour × tint, with light from the sun and the sky
  and fog on top.
- **What's dropped:** specular highlights and normal maps.
- **What doesn't cast shadows:** see-through materials.
- **What animates:** water and lava, each scrolling its own copy of the texture, so
  other materials sharing the image stay still.

Options ▸ Video sets the texture filtering and the render resolution separately (see
[frontend.md](frontend.md)); **V** in a race switches between these two presets, and
`?look=authentic` or `?look=enhanced` in the URL picks one.

|            | Authentic (default)                               | Enhanced                                    |
| ---------- | ------------------------------------------------- | ------------------------------------------- |
| Resolution | 360 lines, smoothed up to the window              | the screen's own                            |
| Textures   | soft bilinear close up, trilinear in the distance | crisp texels close up, anisotropic far away |
| Same       | art, geometry, colours, fog                       | art, geometry, colours, fog                 |

The line count can be 240, 360 or 480 (Options ▸ Video ▸ Resolution).

## The library

The library lives in `tools/blender/addons/kartipelago_tools/library/`:

- **`materials.json`:** the themes (each with its environment) and the materials. Each
  material has an id, a name, a theme, a suggested surface, an image, its wrap, its
  repeat size (`tileMetres`, the width of one copy) and optional water/lava `fx`.
- **`textures/`:** the PNGs, 64×32, a few colours each, tiling seamlessly.
- **`thumbs/`:** the browser's thumbnails (the texture tiled and scaled up with hard
  pixels).
- **`starter_manifest.json`:** the starter pack's original manifest, kept as supplied.

The starter pack's suggested surfaces map to the game's ids: `solid` became `wall`;
`road`, `grass`, `sand`, `water` and `lava` kept their names.

To add a texture:

1. Drop a small PNG into `textures/`.
2. Add an entry to `materials.json`.
3. Add a thumbnail to `thumbs/`, made the same way as the others (tile 2 × 4, scale to
   256 px with nearest-neighbour). Without one, the texture itself is used.
4. Restart Blender, or reload the add-on.

Materials already used in a `.blend` keep a packed copy of their image, so a `.blend`
opens correctly on any computer.

## Not yet

These would build on the same conventions:

- prop placement (trees, rocks, fossils, arches, ruins, waterfalls) as instanced low-poly
  meshes;
- flipbook animations (several images in a loop);
- 32×32 variants of the starter textures;
- more themes and environments.
