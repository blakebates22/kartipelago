// Dragonspire Keep (Dragon Kingdom, course 1): the v3 greybox's lap painted as a castle
// at sunset (tools/blender/prehistoric/dragon_isles.py, keep_scenery.py). It drives as the
// greybox did: the same two jumps, the Courtyard Passage's twin gate, the same zippers;
// it's dressed (its own theme, torches, falls, the courtyard fountain, the air in the
// tunnel); and an AI gets round without falling in.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import { parseAtmosphere } from "../src/game/depths";
import { trackById } from "../src/game/tracks";
import { WORLDS } from "../src/game/worlds";
import { loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const reader =
  (id: string): PackageReader =>
  async (file) => {
    const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
    return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
  };
type Entity = { type: string } & Record<string, unknown>;

describe("Dragonspire Keep", () => {
  it("opens the Dragon Kingdom, painted, with the old lap kept aside", async () => {
    const w = WORLDS.find((x) => x.id === "dragon")!;
    expect(w.tracks[0]).toBe("dragon_isles");
    const t = trackById("dragon_isles")!;
    expect(t.name).toBe("Dragonspire Keep");
    expect(t.theme).toBe("dragonspire_keep");
    expect(trackById("dragon_isles_v2")?.load).toEqual({
      scene: "track",
      packageId: "dragon_isles_v2",
    });
  });

  it("drives as the greybox did: its jumps, its zippers and the passage's gate", async () => {
    const p = await loadTrackPackage(reader("dragon_isles"), { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBe(5);
    const es = (p.meta.entities ?? []) as Entity[];
    expect(es.filter((e) => e.type === "respawn")).toHaveLength(2);
    expect(p.trackData.gates?.some((g) => g.route === "courtyard_passage")).toBe(true);
    const pts = p.route.routes.find((r) => r.id === "main")!.points;
    let lap = 0;
    for (let i = 0; i < pts.length; i++) {
      const a = pts[i]!;
      const b = pts[(i + 1) % pts.length]!;
      lap += Math.hypot(b.x - a.x, b.z - a.z);
    }
    expect(lap).toBeGreaterThan(2100);
    expect(lap).toBeLessThan(2250);
  });

  it("is dressed: torches, falls, the fountain and the tunnel's air", async () => {
    const p = await loadTrackPackage(reader("dragon_isles"), { visual: false });
    const es = (p.meta.entities ?? []) as Entity[];
    const n = (type: string) => es.filter((e) => e.type === type).length;
    expect(n("torch")).toBeGreaterThan(40);
    expect(n("waterfall")).toBeGreaterThanOrEqual(3);
    expect(n("fountain")).toBe(1);
    const air = parseAtmosphere(es.find((e) => e.type === "atmosphere")!);
    expect(air).toBeDefined();
    expect(Object.keys(air!.zones)).toContain("tunnel");
  });

  it("an AI gets round two laps without a respawn, as fast as on the greybox", async () => {
    const p = await loadTrackPackage(reader("dragon_isles"), { visual: false });
    const r = await aiLap(p, { laps: 2, surfaces: true, zippers: true, lapSeconds: 150 });
    const laps = r.race.racers[0]!.lapTimes;
    expect(laps.length).toBe(2);
    expect(r.respawns).toBe(0);
    for (const t of laps) {
      expect(t).toBeGreaterThan(60);
      expect(t).toBeLessThan(110);
    }
  }, 300_000);
});
