# The frontend: from boot to the finish line

How Kartipelago goes from opening the page to racing and back: the screens, how they
share input, audio and the 3D view, the race session underneath, settings and records,
and the soundtrack.

The ideas come from how late-90s console racers organised their menus: separate
screens with their own setup and update, a title over a live scene, a character
select whose music changes instruments with the highlighted racer, wooden menu signs,
track previews, audio options and a music test. Everything here is our own
implementation, art and music.

## The flow

```
BOOT ─► TITLE ── PRESS START ──► main menu
                                   ├─ PLAY ─► CHARACTER_SELECT ─► MODE_SELECT
                                   │                                ├─ TRACKS ─► WORLD_SELECT ─► TRACK_SELECT ─► LOADING ─► RACING
                                   │                                └─ ADVENTURE ─► ADVENTURE_COMING_SOON
                                   ├─ OPTIONS ─► AUDIO_SETTINGS (─► MUSIC_PLAYER) / VIDEO_SETTINGS / CONTROLS / GENERAL_SETTINGS
                                   ├─ MUSIC ─► MUSIC_PLAYER
                                   └─ CREDITS

RACING ── Esc / Start ──► PAUSED ─► Resume · Restart · Options · Track select* · Main menu*
       ── finish line ──► RESULTS ─► Retry · Track select · Main menu
LOADING ── fails ──► LOAD_ERROR ─► Track select
                                                         * asks "Leave this race?" first
```

Esc (or B on a gamepad) always goes back one step. Mouse hover moves the keyboard focus,
so the two never disagree.

## The pieces

| File                   | What it owns                                                         |
| ---------------------- | -------------------------------------------------------------------- |
| `src/main.ts`          | Builds everything once: renderer, audio, input, settings, the loop.  |
| `src/app/app.ts`       | The screen manager: the stack, fades, input routing, the load token. |
| `src/app/menuInput.ts` | Keyboard, gamepad and mouse, turned into menu actions.               |
| `src/app/settings.ts`  | Settings, saved in the browser; any bad value falls back.            |
| `src/app/records.ts`   | Best lap and best race per track and mode.                           |
| `src/game/session.ts`  | One race: track, karts, AI, items, race rules, their 3D and HUD.     |
| `src/game/tracks.ts`   | Every track the menus list (add one here).                           |
| `src/game/worlds.ts`   | The worlds, and which tracks each holds (docs/prehistoric-world.md). |
| `src/screens/*.ts`     | The screens.                                                         |
| `src/ui/`              | The UI canvas, pixel font, textures, backdrops and logo.             |
| `src/audio/`           | The audio engine, instruments, notation, songs and renderer.         |

### Screens and the stack

Screens sit on a stack:

- **Most changes replace the whole stack** (`screens.go`), with a short fade.
- **Overlays are pushed on top of the screen they belong to** (`screens.push`) and
  popped again: pause over the race, options over the title or the pause menu, dialogs.
- **Only the top screen gets menu input.**
- **The 3D view is drawn by the highest screen that has one.** That's why the race
  shows under its pause menu, and the title demo under the options.

The manager guards against a few things:

- **Stale loads.** Every `go` bumps a token. A track that finishes loading after you've
  left is disposed instead of opening.
- **One press reaching two screens.** After any change, input is ignored for a moment,
  held keys stop repeating, and Confirm, Back and Pause never auto-repeat.
- **Clicks during drawing.** A click is acted on at the start of the next frame, never
  in the middle of drawing.

### Input

- **Gameplay:** `core/input.ts`, unchanged. The race samples it once per physics step,
  and only while it's racing.
- **Menus:** `app/menuInput.ts`, read once per frame by the screen manager. Directions
  repeat while held, after a pause.

The two use the same keys in places (arrows, Space), but they never act at the same
time. Gameplay input isn't read outside the race, and in a race only Pause and Back are
read from the menu input.

### The race session

`createSession()` loads a track (Blender tracks are fetched) and builds the race. It's
the code that used to be `main.ts`, now made into something that can be thrown away:

- **3D:** everything it adds hangs off one `root` group in the scene.
- **HUD:** every HUD element (the speedometer, the timing bar) goes in one DOM element.
- **Listeners:** its key listeners share one `AbortController`.
- **`dispose()`:** removes and frees all of it: geometry, materials, textures (racer
  expressions included) and listeners. The tests check that going title → race → menu
  over and over doesn't pile up objects or GPU memory.
- **Pausing:** the session simply isn't stepped. Physics, the race clock, items,
  bananas and the AI all advance in `update()` and nowhere else.
- **`restart()`:** resets the race in place, with no new objects.
- **Demo mode:** the title screen uses one too. The AI drives every kart, the camera
  circles your racer, and it makes no sound. The title races on **Party Beach**
  (`TITLE_TRACK` in `src/game/tracks.ts`, see [prehistoric-world.md](prehistoric-world.md)),
  falling back to Dino Demo, then Drift Loop, if it can't load. Party Beach isn't in any
  world, so it never shows in track select. `?shot=beach_party` shows it with no UI.

Vehicle physics, drifting, zippers, bananas, items and the AI are exactly as before.

### Results and records

When you cross the line:

- "FINISH!" shows, the fanfare plays, and the AI takes your kart round a lap of honour.
- A couple of seconds later the results open, over the still-running race. They show:
  - your position (racing the AI) or TIME TRIAL (solo);
  - the total time, every lap with the best one starred;
  - any new records;
  - the finishing order.

Records (`kartipelago.records.v1`) keep the best lap per track, and the best total time
per track and mode.

## Settings

Saved as `kartipelago.settings.v1`, applied at once:

- **Audio:** master, music, sound effects and racer voices (the character calls); music
  on/off; stereo or mono.
- **Video:**
  - textures: soft (bilinear, N64-like) or sharp;
  - resolution: 240, 360 or 480 lines, or full;
  - screen shape: fill the window, or 4:3 with bars;
  - scanlines;
  - fullscreen.

  V in a race flips between soft at 360 lines and sharp at full resolution.

- **General:** reduce motion (no bouncing logo, sliding or camera swoops), and reset to
  the defaults (records are kept).
- **Controls:** shows every binding on keyboard and gamepad. Keys can't be remapped
  yet, because the input system has fixed bindings.

Left out on purpose, rather than added as switches that do nothing: a headphones mode
(there's no spatial audio to change), subtitles (there's no dialogue yet) and languages
(there's one).

## The UI layer

Menus and the race HUD are drawn on one canvas over the 3D view:

- **Resolution:** a logical 240 lines, 320 wide at 4:3 and up to 480 for widescreen.
  It's drawn at a whole multiple of that and smoothed up to the window, so it's chunky
  but soft.
- **Layout:** important things stay inside the centred 320-wide safe area.
- **Text:** an original 5×7 pixel font, all capitals.
- **Panels:** nine-sliced frames (gold, ink, mossy stone) round tiled 64×32 wood, 64×64
  parchment or 32×32 stone. All are painted in code in `ui/textures.ts`.
- **Accents:** coral, turquoise, leaf, gold, sky and violet.
- **Backgrounds:** the island landscape, treasure map and logo are drawn in code too
  (`ui/backdrops.ts`).

Track select shows pictures from `public/previews/`. They're screenshots of the game,
made with `?shot=<track id>`, which runs the title demo on that track with no UI.

## Audio

### The engine

```
music ─┐
sfx ───┼─► master ─► (mono fold-down) ─► speakers
voice ─┘
```

- **Sound starts on your first key or click.** Browsers require it. Until then
  everything is silent, and nothing breaks.
- **If Web Audio is missing**, every call does nothing and the game runs on.
- **Music gets a small generated room reverb.** Pausing the race ducks it.
- **Changing piece crossfades.** Asking for the piece that's already playing does
  nothing, so screens can ask freely.
- **Menu sounds and racer calls are played live.** Sound effects from the race
  (`audio/sfx.ts`) go through the SFX bus.

### The soundtrack

All original, written in code (`audio/songs.ts`) with a small notation (`audio/score.ts`):

```ts
seq("C5:.5 F5:.5 A5:1 G5:.5 F5:.5 C5:1"); // note:length in beats
chart("F:4 Am:4 Bb:4 C:4"); // chords, which drive bass lines, arpeggios, pads
drums("K...k.k.", KIT, 0.5, 24); // a step grid, repeated
```

| Piece           | Plays in              | Feel                                       |
| --------------- | --------------------- | ------------------------------------------ |
| Kartipelago!    | title and menus       | welcoming, a little heroic (F major, 132)  |
| Pick Your Racer | character select      | playful, one groove + a layer per racer    |
| Course Map      | mode and track select | relaxed, exploring (D major, 98)           |
| Lakeside Dash   | racing                | quick and bouncy (A minor / C major, 152)  |
| Finish Line!    | results               | a short fanfare                            |
| Riverbend Palms | Riverbend Palms       | a beach party, steel pan and soca (F, 138) |
| Cascade Caverns | Cascade Caverns       | rushing, flute over pizzicato (Dm, 142)    |
| Bonebog Pyramid | Bonebog Pyramid       | a mysterious swamp groove (Em, 116)        |
| Ember Peak      | Ember Peak            | frantic, brass and strings (Am, 158)       |

**Pick Your Racer** is one arrangement split into stems that always play in sync. There's
a base groove, plus a layer per racer playing the same tune in their own instruments:

| Racer  | Layer                                        |
| ------ | -------------------------------------------- |
| Tiko   | marimba and xylophone, woodblocks and bongos |
| Brakka | pizzicato strings, walking bass and bassoon  |
| Zephyr | flute, a celesta sparkle and light pizzicato |
| Pebble | clarinet, soft horns and a lazy marimba      |

Highlighting a racer fades their layer up and the last one down. The piece never
restarts.

**The band** is synthesized, with no recorded samples:

- marimba, xylophone, celesta, pizzicato, upright bass;
- flute, clarinet, brass, horn, bassoon;
- a soft pad and a square-wave accent;
- kick, snare, shakers, woodblock, bongos, tambourine and crash.

How it's produced:

- **Rendering:** each piece is rendered once into looping buffers (`audio/dsp.ts`, in a
  worker), at 32 kHz like a lot of console music of the era. Notes ringing past the loop
  point are wrapped to its start, so loops have no gap.
- **Tests:** they check that every melody and chord chart fills its bars, that
  on-the-beat melody notes mostly sit in their chords, and that every piece renders
  cleanly.

The music player lists every piece, plus Adventure's (planned) as "not composed yet".

## Temporary stand-ins

These work, but are meant to be replaced or extended:

- **The music** is synthesized. Real sampled instruments, or a composer, can replace the
  pieces one at a time; the engine just plays buffers.
- **Track previews** are game screenshots.
- **Select Racer** draws its jungle clearing, cliffs and pedestals from simple primitives.
- **Adventure** is a "coming soon" page only.
