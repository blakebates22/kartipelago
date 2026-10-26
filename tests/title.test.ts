// The title screen's course, Party Beach: it loads cleanly, the race's AI can drive it
// (the title demo is an AI race), and the party is there.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { createHazards, type HazardConfig } from "../src/game/hazards";
import { TITLE_MONTAGE, TITLE_TRACK, TRACKS, trackById } from "../src/game/tracks";
import { WORLDS } from "../src/game/worlds";
import { createMeshGround } from "../src/world/collisionMesh";
import { buildTrack } from "../src/world/track";
import { loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const id = TITLE_TRACK.load.packageId!;
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};

describe("the title montage", () => {
  it("shows real courses from every world, each in the main game", () => {
    for (const t of TITLE_MONTAGE) {
      expect(trackById(t), t).toBeDefined();
      expect(
        WORLDS.some((w) => w.tracks.includes(t)),
        t,
      ).toBe(true);
    }
    const worlds = new Set(TITLE_MONTAGE.map((t) => WORLDS.find((w) => w.tracks.includes(t))!.id));
    expect(worlds.size).toBe(5);
  });
});

describe("Party Beach (the title screen's fallback course)", () => {
  it("is only on the title screen: not in track select", () => {
    expect(TRACKS.some((t) => t.id === id)).toBe(false);
    expect(WORLDS.some((w) => w.tracks.includes(id))).toBe(false);
  });

  it("loads cleanly, with the party, the wading long-necks and the pterosaurs", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    const types = (p.meta.entities ?? []).map((e) => (e as { type: string }).type);
    expect(types.filter((t) => t === "partygoer").length).toBeGreaterThan(10);
    expect(types).toContain("conga");
    expect(types).toContain("campfire");
    expect(types.filter((t) => t === "dinosaur").length).toBe(2);
    expect(types.filter((t) => t === "pterosaur").length).toBe(2);
    expect(p.trackData.bananas?.length).toBeGreaterThan(0);
    expect(p.trackData.balloons?.length).toBeGreaterThan(0);
  });

  it("can be driven by the AI: three laps, no respawns", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, { laps: 3, surfaces: true });
    expect(r.race.racers[0]!.lapTimes, `respawns ${r.respawns}`).toHaveLength(3);
    expect(r.respawns).toBe(0);
    expect(r.worstAbove).toBeLessThan(2.5);
  }, 120000);

  it("keeps the dancers off the road and the conga line on its circle", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const track = buildTrack(p.trackData, tuning.track.sampleSpacing);
    const ground = createMeshGround(p.collision);
    const h = createHazards({
      root: undefined as never,
      track,
      entities: p.meta.entities ?? [],
      routes: p.route.routes,
      makeGround: () => ground,
      cfg: tuning.hazards as HazardConfig,
      karts: 1,
      quiet: true,
      headless: true,
    });
    expect(h.solids).toHaveLength(4); // the two long-necks' bodies only
    for (const e of p.meta.entities ?? []) {
      const d = e as { type: string; x: number; z: number; radius?: number };
      if (d.type !== "partygoer" && d.type !== "conga") continue;
      const reach = (d.radius ?? 0) + 1;
      for (const s of track.samples)
        expect(Math.hypot(s.pos.x - d.x, s.pos.z - d.z), d.type).toBeGreaterThan(
          s.width / 2 + reach,
        );
    }
    h.render(1, 1 / 60, { x: 0, y: 0, z: 0 });
    h.dispose();
  });
});
