# The racer pipeline

How to change a racer, or add a new one. Everything is code (original art, MIT), so a
racer is a single TypeScript file you can read, tweak and diff.

```
src/render/racers/
  designs.ts         who they are: name, species, title, bio, quote, menu colours, voice
  roster/
    index.ts         every racer's build, by id
    types.ts         what a racer file provides
    tiko.ts ...      one file per racer: colours, kart style, rider (body, then buildHead)
  kit/
    shapes.ts        Build (merge shapes into one mesh), loft, tube, horn, box, card...
    paint.ts         tiny painted textures (Pix) and the shared materials
    chassis.ts       the shared kart: wheels, seat, steering wheel, grips, exhaust
    sleek.ts         the sleek kart family: the body every kart is built from
    rig.ts           the shared rider rig: eyes and lids, jaw, IK arms, personality
    props.ts         leaves, packs, bedrolls, straps, goggles, kart emblems
  animator.ts        the state machine and pose channels (one for everyone)
  racer.ts           puts it together: kart + rider + flame + shadow + far version
```

## The workflow

1. Run `npm run dev` and open **`/garage.html?racer=<id>&scale=1`**.
2. Edit `roster/<id>.ts` and save. The page reloads with your change.
3. Check the **turnaround** (front, three-quarter, side, rear), the **gameplay** view
   (the race camera; this is where they're seen most) and **far** (the cheap version).
4. Try the **animation** states, especially `DRIFTING_LEFT`, `AIRBORNE` and `VICTORY`.
5. **Save sheet** for a PNG to compare against the concept art.
6. Run `npm test`: `tests/racers.test.ts` checks the hands stay on the wheel, nothing
   pokes through the road or past the kart, the silhouettes stay distinct and the
   triangle budget holds.

## Changing a racer

**Colours:** each file starts with its `MAIN` palette (and an `ALT` one for repeated
rivals). Change a hex and everything painted with it follows.

**Shapes:** bodies, heads, snouts, crests and tails are **lofts**: a list of
cross-sections, each a centre `at: [x, y, z]` and a half-width and half-height
(`rx`, `ry`). Move a section and the skin follows. Options:

- `steps: 2` adds a smooth in-between section (rounder curves);
- `sides` (8-12) sets how round it is (fewer sides is more faceted);
- `sq: 3` makes a section boxier, `flat: 0.4` flattens its underside (a jaw, a snout);
- `paint: (t, angle, base) => colour` colours it along (`t`, 0..1) and round (`angle`,
  -pi/2 underneath to pi/2 on top): bellies, gradients, stripes.

Everything else is primitives placed with `{ p, r, s }` (position, rotation, scale):
`ellipsoid`, `gem` (faceted rocks), `box` (chamfered), `cyl`, `cone`, `card` (flat
outlines like wings and frills), `horn`, `tube`.

Axes: +Z forward, +Y up, +X to the racer's **left**. The rider is built at 1x and drawn at
1.2x (`CHASSIS.riderScale`); heads are scaled up again, mascot-style.

**The face:** `buildEyes` makes the eyes (white, iris, pupil, highlight), the lids that
blink and squint, and the brows. Set `at` (the left eye; the right is mirrored), `size`,
`yaw` (how far round the head they sit) and `inward` (how much the pupils look toward the
nose). For character: `lidTilt` slants the upper lids (positive is determined, negative
worried), `cheek` pushes a grin up under the eyes, `irisRing` and `irisScale` colour and
size the irises, and `gaze` sets where the pupils rest (a side glance). With `restLids`
in the personality, the lid tilt shapes the whole expression. The jaw is a group the
animator opens: `jawOpen` is how far, in radians.

Each racer builds its head in `buildHead(rig, c)`, after the rest of the rig: skull,
crest or frill, eyes and jaw, and it fills in `rig.face`.

**The arms** are two-bone IK: give the shoulder, the bone lengths and radii, and the
hands find the steering wheel by themselves (they stretch a little if they can't quite
reach). `cheer` is where the hands go to celebrate.

**Personality** (in `rider()`): lean, head turn, curiosity, blink rate, how hard boosts
throw them back, how fast poses change (`response`), resting face (`restJaw`,
`restBrow`, `restLids`), whether bumps make them grumpy (`grumble`) and how they
celebrate (`cheer`, `nod`, `wave` or `flap`).

**Wiggles** are parts with their own motion: `crest` (lags and bobs), `flutter`
(scarves), `bounce` (packs) and `sway` (leaves). Tails are a chain of joints in `tail`,
wings go in `wings` with `fold` and `open` rotations in their `userData`.

**The kart:** `kart()` returns a body kit for the shared chassis, usually `sleekKart()`
(`kit/sleek.ts`): a low wedge monocoque, open wheels on racing slicks under blade
fenders, a cockpit cowl and engine deck. Pick the colours and a `front` (`blade`, `twin`,
`horns`, `needle`), `pods` (`intake`, `delta`, `round`) and `rear` (`wing`, `ducktail`,
`fins`, `jet`), plus `extras` for anything of your own. A hand-made body kit works too:
`shell(b, detail)` adds the body's shapes (detail 1 is the far version: leave out small
things), `decorate` adds the emblem, plus the wheel and steering colours. The chassis itself (wheel spots,
seat, steering wheel, grips, exhaust, size) is shared by every kart in `CHASSIS`, so
they all drive, collide and film the same. Stay inside `CHASSIS.length` x `CHASSIS.width`.

Emblems are painted in `props.ts` (`emblemTexture`) on a 32x32 canvas with the `Pix`
painter: add a new symbol there.

## Adding a racer

1. Copy the closest racer, e.g. `roster/pebble.ts` to `roster/<id>.ts`, and rename its
   export.
2. Add the id to `RacerId` and an entry to `DESIGNS` and `RACER_IDS` in `designs.ts`.
3. Add it to `BUILDS` in `roster/index.ts`.
4. Give it a layer in "Pick Your Racer" (`RACER_STEMS` and the parts in `select()` in
   `src/audio/songs.ts`) and a voice call (`call` in `designs.ts`).
5. Open the viewer and the tests, as above. For a picture of every racer from several
   angles with their select-screen sprites, run `racerSheet()` from
   `src/debug/racerLab.ts` in the browser console (see the file).

## Rules of thumb

- **Silhouette first.** Each racer must be recognisable from behind at race distance:
  check the gameplay view at render scale 0.4.
- **Keep the face clear.** Horns, crests and goggles go above or behind the eyes.
- **Small textures.** 16 to 64 texels a side, nearest-neighbour filtered; colours come
  mostly from vertex colours.
- **Budget:** under 12,000 triangles up close for kart and rider together, under 3,000
  far away.
- **Never touch the physics.** Looks can't change speed, handling or the collision
  circle.
