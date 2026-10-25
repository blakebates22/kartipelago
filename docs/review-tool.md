# The level review tool

A way for Blake to point at exactly what he means on a track, so Claude can act on it.
The race freezes, you fly round the track, and you leave notes: arrows on things, boxes
round areas, paths along the ground, measurements, driving lines and general notes.
The code is in `src/review/`.

## Opening it

- **F2** in any race (on a Mac keyboard: fn + F2), or **REVIEW TRACK** in the pause menu.
- Or straight from the address bar: `?track=riverbend_palms&review`.

Run the game with `npm run dev` so that notes save straight into the repo (see below).

## Moving around

| Keys                                     | Does                                                                                       |
| ---------------------------------------- | ------------------------------------------------------------------------------------------ |
| W A S D                                  | fly forward, left, back, right                                                             |
| Q / E                                    | down / up                                                                                  |
| Shift                                    | four times faster                                                                          |
| mouse wheel                              | flying speed                                                                               |
| arrow keys, or drag with the right mouse | look around                                                                                |
| F                                        | mouse-look: a crosshair, click to place at it                                              |
| K                                        | jump to your kart                                                                          |
| H                                        | hide or show the panel                                                                     |
| Tab                                      | drive from here: your kart is put down under the camera, facing your way (F2 to come back) |
| Shift + Tab                              | back to your kart where it was                                                             |
| Esc                                      | cancel what you're placing, or leave the tool                                              |

## The tools (keys 1-5)

1. **PIN.** Click anything. An arrow points at that exact spot. The note records the
   point, the surface direction there, and the name of the object you hit along with its
   parents' names (for example `track:riverbend_palms › Palms › Palm_12`).
2. **BOX.** Click two corners on the ground to mark an area, then set its height in the
   editor. The note lists the named objects inside the box.
3. **PATH.** Click along the ground, then press Enter (Backspace takes the last point
   back). Use it for "the road should go like this".
4. **MEASURE.** Click two points to get the distance in metres. Save it as a note or
   cancel it.
5. **NOTE.** A note about the whole track. It has no marker, but keeps the view.

**RECORD LINE** (on the panel): drive the line you mean, then press F2 to stop. The line
becomes a note.

Every note gets:

- a screenshot with its marker in it (you can **DRAW** on it in red);
- the camera's exact view, so the **GO** button flies back to it;
- tags (art, layout, gameplay, bug) and an **IMPORTANT** flag.

Notes are pink (red if important) until they're done, then green with a tick.

## Clips (F4)

Off until you turn it on: the review tool's **● CLIPS** button (the choice is remembered
in this browser), so it costs nothing while you just play. While it's on, the game keeps
filming the last 20-40 seconds of play, with the sound.
Press **F4** (fn + F4 on a Mac) anywhere, in a race or in the review tool, and that stretch
is saved:

```
reviews/<trackId>/clips/<date>_<time>.mp4    the video (or .webm), the HUD in it, and a
                                             strip of readings under it (time, speed,
                                             height, vertical speed, ground, zipper, boost)
reviews/<trackId>/clips/<date>_<time>.json   your kart's whole state every frame
```

A note appears top left saying where it went. The clips folder isn't committed (videos are
big); tell Claude the file name and Claude reads it from the folder. Claude watches the
video by pulling frames out of it, and can replay the moment from the JSON. `?noclips`
turns the recorder off. The code is `src/debug/clipRecorder.ts`.

## Where notes go (for Claude)

With the dev server running, each note is written straight into the repo:

```
reviews/<trackId>/notes.json        every note (see src/review/notes.ts for the fields)
reviews/<trackId>/shots/<id>.jpg    each note's screenshot
```

`tools/reviewStore.mjs` writes these files (dev only). On the GitHub Pages build there's
no server, so notes stay in that browser, and **EXPORT** downloads them as one JSON file
with the screenshots inside.

To work through a track's notes, Claude reads `notes.json` and the screenshots. Then, for
each note:

- `pin.point` / `pin.path` say exactly what and where;
- `box.center` / `size` / `yaw` give the area, and `objects` lists what's in it;
- `path` or `measure` give the shape or the distance;
- `camera` gives the exact view to take before and after pictures from.

When a note is done, Claude sets `"status": "done"` and writes a short `"reply"` in
`notes.json`. The game shows the tick and the reply in the panel. Blake can **REOPEN** a
note if it isn't right.

The `reviews/` folder is ignored by Prettier: the tool writes it, not people.

## Moving props (tool 6, MOVE)

Click a prop (a tree, rock, bush, hut...) to pick it up. Handles appear:

- **G** or **MOVE** shifts it, **R** or **TURN** turns it, **T** or **SIZE** resizes it.
- **SNAP** moves in half-metre steps and turns in 15° steps.
- **COPY** makes a copy beside it and picks the copy up.
- **DELETE** removes it.
- **SAVE EDIT** saves it as a note (with a screenshot and optional words); **CANCEL** or
  Esc puts it back.

Ground, road and other very big pieces can't be picked up: use a pin or a box for those.

An edit is a preview until it's baked: you see it in the game (after the review tool has
been opened in that race), but karts still hit the prop where it was. Deleting the note
undoes the edit.

**Baking (Claude):** `node tools/bakeEdits.mjs <trackId> [note numbers]` copies the open
edits into `public/tracks/<trackId>/edits.json` and marks those notes done. The game
applies edits.json whenever the track loads, to what you see and to what you hit
(`src/world/trackEdits.ts`). Props are found by name, and a Blender re-export can rename
generated props, so check edits.json after one.

## Out-of-bounds audit (Claude)

`tools/audit/oob.audit.ts` checks a built track for places a kart can get to but
shouldn't, using the game's own collision rules (`floorAt`, `deepestWall`). It floods out
over a 2 m grid from the road, walking each step the way a kart follows the ground, then
floods back from the road to see what you can return from. It reports:

- **holes**: no floor at all (you'd fall out of the world);
- **traps**: places you can reach but never drive out of;
- **drops**: stretches of road where you can go over the edge and land somewhere with no
  road (want a rail);
- **covered**: something solid just above the road (a hidden floor poking through: you'd
  hover on it).

```
AUDIT_TRACK=cascade_caverns npx vitest run --config tools/audit/vitest.config.ts --disableConsoleIntercept
```

It writes `audit-out/<track>-oob.json` and a top-down map `audit-out/<track>-oob.png`
(white road, grey reachable, red traps, purple fallen off, orange far off course).
`TRACE=x,z` (and `TRACE_Y=y`) prints how it got to a spot. Not part of `npm test`.
