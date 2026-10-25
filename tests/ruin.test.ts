// Riverbend Palms in ruins (tools/blender/prehistoric/riverbend_ruins.py): the first of
// Adventure's treasure map courses. The same valley after the dragons' attack: a shorter
// lap (the burnt bridge's jump, a scorched track down the west meadow), offered in dev
// builds from Riverbend's own menu entry, and much quicker to drive.
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

describe("Riverbend Palms (Ruined)", () => {
  it("is Riverbend's ruin, in its own theme", () => {
    expect(trackById("riverbend_palms")!.ruin).toBe("riverbend_palms_ruin");
    expect(trackById("riverbend_palms_ruin")!.theme).toBe("riverbend_ruins");
  });

  it("loads cleanly: a shorter lap with the bridge's jump, smoke and ash", async () => {
    const p = await loadTrackPackage(reader("riverbend_palms_ruin"), { visual: false });
    const full = await loadTrackPackage(reader("riverbend_palms"), { visual: false });
    expect(p.warnings).toEqual([]);
    const a = lapLength(p.trackData.points);
    expect(a).toBeLessThan(0.9 * lapLength(full.trackData.points));
    expect(a).toBeGreaterThan(750);
    const es = (p.meta.entities ?? []) as Entity[];
    const n = (type: string) => es.filter((e) => e.type === type).length;
    expect(n("respawn")).toBe(1);
    expect(n("ashfall")).toBe(1);
    expect(n("campfire")).toBeGreaterThan(4);
    expect(n("dinosaur")).toBe(0); // the long-necks have fled
  });

  it("an AI drives it, jump and all, well inside the full lap's time", async () => {
    const lap = async (id: string) => {
      const p = await loadTrackPackage(reader(id), { visual: false });
      const r = await aiLap(p, { laps: 2, surfaces: true, zippers: true, lapSeconds: 70 });
      expect(r.respawns).toBe(0);
      return r.race.racers[0]!.lapTimes[1]!;
    };
    expect(await lap("riverbend_palms_ruin")).toBeLessThan(0.9 * (await lap("riverbend_palms")));
  }, 240_000);
});
