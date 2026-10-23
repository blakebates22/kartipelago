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

| Keys                                     | Does                                          |
| ---------------------------------------- | --------------------------------------------- |
| W A S D                                  | fly forward, left, back, right                |
| Q / E                                    | down / up                                     |
| Shift                                    | four times faster                             |
| mouse wheel                              | flying speed                                  |
| arrow keys, or drag with the right mouse | look around                                   |
| F                                        | mouse-look: a crosshair, click to place at it |
| K                                        | jump to your kart                             |
| H                                        | hide or show the panel                        |
| Tab                                      | back to driving (F2 to come back)             |
| Esc                                      | cancel what you're placing, or leave the tool |

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

## Coming next

Nudges: select a prop and move, turn, scale, copy or delete it with handles. The tool
will record the edits exactly, for Claude to bake into the track build.
