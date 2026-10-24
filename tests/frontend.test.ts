import { describe, expect, it } from "vitest";
import { createScreenManager, type Screen } from "../src/app/app";
import { createMenuInput, type MenuAction } from "../src/app/menuInput";
import { loadRecords, submitResult } from "../src/app/records";
import { DEFAULT_SETTINGS, loadSettings, sanitize, saveSettings } from "../src/app/settings";
import { TRACKS, trackById } from "../src/game/tracks";
import { VISIBLE_WORLDS, WORLDS, currentWorld, tracksOf, worldOfTrack } from "../src/game/worlds";
import { FONT_CHARS, FONT_ROWS, textWidth, wrap } from "../src/ui/font";
import type { UiLayer } from "../src/ui/layer";
import { CATALOG } from "../src/audio/songs";
import { BINDINGS } from "../src/screens/options";

/** A tiny in-memory localStorage. */
function memoryStorage() {
  const m = new Map<string, string>();
  return {
    getItem: (k: string) => m.get(k) ?? null,
    setItem: (k: string, v: string) => void m.set(k, v),
  };
}

/** Enough of `window` to send keys to the menu input. */
function fakeWindow() {
  const handlers: Record<string, ((e: unknown) => void)[]> = {};
  return {
    addEventListener: (t: string, f: (e: unknown) => void) => (handlers[t] ??= []).push(f),
    key(type: "keydown" | "keyup", code: string, repeat = false) {
      for (const f of handlers[type] ?? [])
        f({ code, repeat, target: null, metaKey: false, ctrlKey: false, altKey: false });
    },
  };
}

describe("settings", () => {
  it("fills in defaults and repairs bad values", () => {
    expect(sanitize(undefined)).toEqual(DEFAULT_SETTINGS);
    const s = sanitize({
      audio: { master: 7, music: "loud", mono: true },
      video: { resolution: 123 },
      last: { racer: "nobody" },
    });
    expect(s.audio.master).toBe(1);
    expect(s.audio.music).toBe(DEFAULT_SETTINGS.audio.music);
    expect(s.audio.mono).toBe(true);
    expect(s.video.resolution).toBe(DEFAULT_SETTINGS.video.resolution);
    expect(s.last.racer).toBe("tiko");
  });

  it("survives a reload, and never throws on broken storage", () => {
    const store = memoryStorage();
    const s = sanitize(undefined);
    s.audio.music = 0.3;
    s.video.filtering = "sharp";
    s.last.racer = "pebble";
    saveSettings(s, store);
    const back = loadSettings(store);
    expect(back.audio.music).toBe(0.3);
    expect(back.video.filtering).toBe("sharp");
    expect(back.last.racer).toBe("pebble");
    store.setItem("kartipelago.settings.v1", "{not json");
    expect(loadSettings(store)).toEqual(DEFAULT_SETTINGS);
    const broken = {
      getItem: () => {
        throw new Error("blocked");
      },
    };
    expect(loadSettings(broken)).toEqual(DEFAULT_SETTINGS);
  });
});

describe("records", () => {
  it("keeps the best lap and best race per track and mode", () => {
    const store = memoryStorage();
    expect(submitResult("dino_demo", "race", 90, 29, store)).toMatchObject({
      lap: true,
      race: true,
    });
    expect(submitResult("dino_demo", "race", 95, 28, store)).toMatchObject({
      lap: true,
      race: false,
      previousRace: 90,
    });
    expect(submitResult("dino_demo", "timeTrial", 99, 30, store)).toMatchObject({
      lap: false,
      race: true,
    });
    const r = loadRecords(store).dino_demo!;
    expect(r.bestLap).toBe(28);
    expect(r.best).toEqual({ race: 90, timeTrial: 99 });
  });
});

describe("menu input", () => {
  it("turns keys into actions once per press, repeating only directions", () => {
    const w = fakeWindow();
    const input = createMenuInput(w as unknown as Window);
    w.key("keydown", "Enter");
    w.key("keydown", "Enter", true); // browser auto-repeat: ignored
    expect(input.poll(0.016)).toEqual(["confirm"]);
    expect(input.poll(1)).toEqual([]); // held Enter never repeats
    w.key("keyup", "Enter");
    w.key("keydown", "ArrowDown");
    const got: MenuAction[] = [...input.poll(0.016)];
    for (let i = 0; i < 60; i++) got.push(...input.poll(1 / 60));
    expect(got[0]).toBe("down");
    expect(got.filter((a) => a === "down").length).toBeGreaterThan(3); // held: repeats
    input.flush();
    expect([...input.poll(0.5), ...input.poll(0.5)]).toEqual([]); // nothing carries into a new screen
  });
});

/** A stand-in UI layer: screens here draw nothing. */
const ui = { begin() {}, rect() {}, W: 320, H: 240 } as unknown as UiLayer;

function probe(id: Screen["id"], log: string[]): Screen {
  return {
    id,
    enter: () => log.push(`enter ${id}`),
    exit: () => log.push(`exit ${id}`),
    resume: () => log.push(`resume ${id}`),
    frame: (_dt, actions) => {
      if (actions.length) log.push(`${id} got ${actions.join(",")}`);
    },
    draw() {},
  };
}

describe("screen manager", () => {
  it("swaps screens after a fade, cleaning up the old ones, and stacks overlays", () => {
    const w = fakeWindow();
    const input = createMenuInput(w as unknown as Window);
    const log: string[] = [];
    const m = createScreenManager(ui, input, { reduceMotion: () => false });
    m.go(probe("TITLE", log));
    expect(log).toEqual(["enter TITLE"]); // the first screen appears at once
    const t0 = m.token;
    m.go(probe("CHARACTER_SELECT", log));
    expect(m.token).toBe(t0 + 1);
    m.frame(0.05);
    expect(m.top?.id).toBe("TITLE"); // still fading out
    m.frame(0.2);
    expect(m.top?.id).toBe("CHARACTER_SELECT");
    expect(log).toContain("exit TITLE");
    m.push(probe("OPTIONS", log));
    m.frame(0.2); // input cooldown
    w.key("keydown", "Enter");
    m.frame(0.016);
    expect(log).toContain("OPTIONS got confirm"); // only the top screen hears it
    expect(log).not.toContain("CHARACTER_SELECT got confirm");
    m.pop();
    expect(log.slice(-2)).toEqual(["exit OPTIONS", "resume CHARACTER_SELECT"]);
  });

  it("lets the newest request win while fading", () => {
    const input = createMenuInput(fakeWindow() as unknown as Window);
    const log: string[] = [];
    const m = createScreenManager(ui, input, { reduceMotion: () => false });
    m.go(probe("TITLE", log));
    m.go(probe("MODE_SELECT", log));
    m.frame(0.1);
    m.go(probe("TRACK_SELECT", log));
    m.frame(0.1);
    expect(m.top?.id).toBe("TRACK_SELECT");
    expect(log).not.toContain("enter MODE_SELECT");
  });
});

describe("tracks", () => {
  it("lists every track once, with a picture, a mode and something to load", () => {
    const ids = TRACKS.map((t) => t.id);
    expect(new Set(ids).size).toBe(ids.length);
    for (const t of TRACKS) {
      expect(t.modes.length, t.id).toBeGreaterThan(0);
      expect(t.preview, t.id).toMatch(/^previews\/.+\.jpg$/);
      expect(Boolean(t.load.trackData || t.load.packageId || t.load.scene !== "track"), t.id).toBe(
        true,
      );
      expect(
        CATALOG.some((c) => c.id === t.music && c.available),
        t.id,
      ).toBe(true);
    }
    expect(trackById("drift_loop")?.legacyNumber).toBe(1);
  });
});

describe("worlds", () => {
  it("puts every track in exactly one world, keeping the old ids", () => {
    expect(new Set(WORLDS.map((w) => w.id)).size).toBe(WORLDS.length);
    for (const t of TRACKS)
      expect(WORLDS.filter((w) => w.tracks.includes(t.id)).length, t.id).toBe(1);
    for (const w of WORLDS) expect(tracksOf(w).length, w.id).toBe(w.tracks.length);
    expect(worldOfTrack("dino_demo")?.id).toBe("test_world");
    expect(WORLDS.find((w) => w.id === "test_world")?.tracks).toEqual([
      "dino_demo",
      "drift_loop",
      "ribbon_ridge",
      "meadow_run",
      "bridge_test",
      "loop_lab",
      "drift_park",
      "riverbend_palms_v21",
      "cascade_caverns_v2",
      "ember_peak_v2",
      "bonebog_pyramid_v2",
      "frostveil_citadel_v2",
      "snowy_summit_v2",
      "hearthglow_hollow_v2",
      "oasis_haven_v2",
      "dry_gulch_v3",
    ]);
    expect(WORLDS.find((w) => w.id === "prehistoric")?.tracks).toEqual([
      "riverbend_palms",
      "cascade_caverns",
      "bonebog_pyramid",
      "ember_peak",
    ]);
  });

  it("keeps the prototype world in the game but out of the menus", () => {
    expect(WORLDS.find((w) => w.id === "test_world")?.hidden).toBe(true);
    expect(VISIBLE_WORLDS.map((w) => w.id)).toEqual([
      "prehistoric",
      "frostveil",
      "desert",
      "dragon",
    ]);
    // Its tracks still load directly.
    expect(trackById("loop_lab")).toBeTruthy();
  });

  it("opens on the world last picked, else the last track's", () => {
    expect(currentWorld({ trackId: "riverbend_palms" }).id).toBe("prehistoric");
    expect(currentWorld({ trackId: "aurora_rift" }).id).toBe("frostveil");
    // A hidden world's track opens on the first world shown.
    expect(currentWorld({ trackId: "meadow_run" }).id).toBe(VISIBLE_WORLDS[0]!.id);
    expect(currentWorld({ trackId: "meadow_run", worldId: "test_world" }).id).toBe(
      VISIBLE_WORLDS[0]!.id,
    );
    expect(currentWorld({ trackId: "meadow_run", worldId: "prehistoric" }).id).toBe("prehistoric");
    expect(currentWorld({ trackId: "gone", worldId: "gone" }).id).toBe(WORLDS[0]!.id);
  });
});

describe("pixel font", () => {
  it("has every glyph 7 rows tall and evenly wide", () => {
    for (const ch of FONT_CHARS) {
      const rows = FONT_ROWS(ch);
      expect(rows.length, ch).toBe(7);
      expect(new Set(rows.map((r) => r.length)).size, ch).toBe(1);
    }
  });

  it("can draw every character the menus use", () => {
    const used = [
      ...BINDINGS.flat(),
      ...CATALOG.map((c) => c.title.toUpperCase() + c.role.toUpperCase()),
      ...TRACKS.map((t) => t.name.toUpperCase() + t.description.toUpperCase()),
      ...WORLDS.map((w) => (w.name + w.tagline + w.description).toUpperCase()),
    ].join("");
    const missing = [...new Set(used)].filter(
      (c) => !FONT_CHARS.includes(c) && !FONT_CHARS.includes(c.toUpperCase()),
    );
    expect(missing).toEqual([]);
  });

  it("measures and wraps text", () => {
    expect(textWidth("A")).toBe(5);
    expect(textWidth("AB")).toBe(11);
    expect(wrap("ONE TWO THREE", textWidth("ONE TWO"))).toEqual(["ONE TWO", "THREE"]);
  });
});
