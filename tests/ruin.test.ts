// The ruined courses (Adventure's treasure map challenge: each course after the dragons'
// attack): riverbend_ruins.py, cascade_ruins.py, bonebog_ruins.py, ember_ruins.py. The
// same places, wrecked: new laps through them (most shorter), offered in dev builds from
// each course's own menu entry, smoke and ash in the air. The sync rule (Blake): a ruin
// is rebuilt whenever its standard course changes; each records the course scripts it
// was built from, and a ruin left behind fails here.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import { trackById } from "../src/game/tracks";
import { loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const reader =
  (id: string): PackageReader =>
  async (file) => {
    const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
    return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
  };
const lapLength = (pts: { x: number; z: number }[]) =>
  pts.reduce(
    (a, p, i) =>
      a + Math.hypot(p.x - pts[(i + 1) % pts.length]!.x, p.z - pts[(i + 1) % pts.length]!.z),
    0,
  );
type Entity = { type: string } & Record<string, unknown>;

// [course, its ruin, its theme, the ruin's lap length (shortest, longest, of the full
// lap's), the most its AI lap time may be (of the full lap's)]
const RUINS: [string, string, string, [number, number], number][] = [
  ["riverbend_palms", "riverbend_palms_ruin", "riverbend_ruins", [0.7, 0.9], 0.93],
  ["cascade_caverns", "cascade_caverns_ruin", "cascade_ruins", [0.7, 0.92], 0.93],
  ["bonebog_pyramid", "bonebog_pyramid_ruin", "bonebog_ruins", [0.7, 0.92], 0.93],
  // Blake: Ember Peak's ruin is a little longer (an exciting home run, not a shortcut).
  ["ember_peak", "ember_peak_ruin", "ember_ruins", [1.0, 1.15], 1.15],
  // Blake: at least half as long, and fast like the beach courses.
  ["frostveil_citadel", "frostveil_citadel_ruin", "frost_ruins", [0.35, 0.5], 0.55],
  // Blake: much shorter, the great tree fallen and driven through like a tunnel. (About
  // two thirds: the course's first two thirds come before the tree.)
  ["snowy_summit", "snowy_summit_ruin", "summit_ruins", [0.6, 0.72], 0.75],
  // Blake: the ruined city as a fast, speedrun-feel course (about Volcano Isle's length).
  ["hearthglow_hollow", "hearthglow_hollow_ruin", "hearth_ruins", [0.5, 0.62], 0.65],
  // Blake: about 45% shorter, the whole cavern decimated, the Loop's top half missing.
  ["aurora_rift", "aurora_rift_ruin", "aurora_ruins", [0.45, 0.6], 0.62],
  // Blake: keep it, about 22% shorter (jump the broken bridge, dive to the river, climb out).
  ["canyon_dash", "canyon_dash_ruin", "canyon_ruins", [0.7, 0.82], 0.8],
  // Blake: about the same length, but it drives quite differently and more fun.
  ["oasis_haven", "oasis_haven_ruin", "oasis_ruins", [0.95, 1.03], 1.05],
  // Blake: minimal; the lighthouse fallen across the road, rubble to avoid; the jump untouched.
  ["coral_cove", "coral_cove_ruin", "cove_ruins", [0.95, 1.05], 1.25],
  // Blake: minimal; the galleon split open, rubble to avoid.
  ["shipwreck_bay", "shipwreck_bay_ruin", "wreck_ruins", [0.95, 1.05], 1.1],
  // Blake: remade by the sacrifice's blast, at least 50% shorter (this one is 52%: the harbour and the passage are fixed).
  ["dragon_isles", "dragon_isles_ruin", "keep_ruins", [0.5, 0.56], 0.6],
  // Blake: reworked by the blast, the Dragon Kingdom's most fun drive kept fun; at least half the lap.
  ["dragon_canyon", "dragon_canyon_ruin", "emerald_ruins", [0.45, 0.55], 0.55],
  // Blake: about 20% shorter, the mine destroyed (no shortcut), the town in flames, a new path opened by the destruction.
  ["dry_gulch", "dry_gulch_ruin", "gulch_ruins", [0.72, 0.88], 0.88],
  // Blake: the ceiling caved in; the broken descent road is many jumps; falling rock with a warning shadow.
  ["impact_depths", "impact_depths_ruin", "impact_ruins", [0.97, 1.03], 1.03],
  // Blake: the Dragon Kingdom's ruins are new courses, every change explained by the blast; at least half the lap.
  ["snow_dragon_pass", "snow_dragon_pass_ruin", "ember_hold_ruins", [0.45, 0.56], 0.6],
  // Blake: the Dragon Kingdom's ruins are new courses, every change explained by the blast; at least half the lap.
  ["celestial_dragon_festival", "celestial_dragon_festival_ruin", "moon_ruins", [0.42, 0.58], 0.6],
  // Blake: Tropic Isles ruins change little: one decent change each, plus rubble to avoid.
  ["volcano_isle", "volcano_isle_ruin", "isle_ruins", [0.98, 1.02], 1.03],
  // Blake: Tropic Isles ruins change little: one decent change each, plus rubble to avoid.
  ["splash_lagoon", "splash_lagoon_ruin", "splash_ruins", [0.98, 1.02], 1.05],
];

describe.each(RUINS)("%s's ruin", (full, ruin, theme, [least, most], slowest) => {
  it("is offered from the course's own entry, in its own theme", () => {
    expect(trackById(full)!.ruin).toBe(ruin);
    expect(trackById(ruin)!.theme).toBe(theme);
  });

  it("loads cleanly: a shorter lap, smoke and ash", async () => {
    const p = await loadTrackPackage(reader(ruin), { visual: false });
    const f = await loadTrackPackage(reader(full), { visual: false });
    expect(p.warnings).toEqual([]);
    const a = lapLength(p.trackData.points);
    const b = lapLength(f.trackData.points);
    expect(a).toBeLessThan(most * b);
    expect(a).toBeGreaterThan(least * b);
    const es = (p.meta.entities ?? []) as Entity[];
    const n = (type: string) => es.filter((e) => e.type === type).length;
    expect(n("ashfall")).toBe(1);
    expect(n("campfire")).toBeGreaterThan(2);
  });

  it("an AI drives it without a respawn, well inside the full lap's time", async () => {
    const lap = async (id: string) => {
      const p = await loadTrackPackage(reader(id), { visual: false });
      const r = await aiLap(p, { laps: 2, surfaces: true, zippers: true, lapSeconds: 120 });
      expect(r.respawns).toBe(0);
      return r.race.racers[0]!.lapTimes[1]!;
    };
    expect(await lap(ruin)).toBeLessThan(slowest * (await lap(full)));
  }, 300_000);

  it("was built from the course scripts as they are now (the sync rule)", async () => {
    const text = new TextDecoder().decode(
      await readFile(new URL(`../public/tracks/${ruin}/track.json`, import.meta.url)),
    );
    const meta = JSON.parse(text) as { builtFrom?: Record<string, string> };
    const from = meta.builtFrom ?? {};
    // The standard course's own script is among them.
    expect(Object.keys(from)).toContain(`${full}.py`);
    for (const [file, sha] of Object.entries(from)) {
      const bytes = await readFile(
        new URL(`../tools/blender/prehistoric/${file}`, import.meta.url),
      );
      const hash = await crypto.subtle.digest("SHA-256", bytes as Uint8Array<ArrayBuffer>);
      const now = [...new Uint8Array(hash)].map((b) => b.toString(16).padStart(2, "0")).join("");
      expect(now, `${file} changed since ${ruin} was built: rebuild the ruin`).toBe(sha);
    }
  });
});
