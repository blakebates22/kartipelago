// The Edge of the World (journey_cause), Nov 3 (Blake: "you cant actually traverse
// backwards. lets just remove the jumps completely ... we need to make the immersiveness
// so great such that the boring driving is justified"): one road with no jumps, no gap in
// it and no slope a kart can't climb either way; each stretch its own sound (the
// atmosphere's sound only: the overworld paints the air); and life over the bridges.
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { airAt, parseAtmosphere } from "../src/game/depths";

type Entity = { type: string } & Record<string, unknown>;
type P = { x: number; y: number; z: number };
const dir = new URL("../public/tracks/journey_cause/", import.meta.url);
const meta = JSON.parse(readFileSync(new URL("track.json", dir), "utf8")) as {
  entities: Entity[];
  journey: { from: number; to: number };
};
const routes = JSON.parse(readFileSync(new URL("route.json", dir), "utf8")) as {
  routes: { id: string; points: P[] }[];
};
const of = (t: string) => meta.entities.filter((e) => e.type === t);

describe("the Edge of the World", () => {
  it("has no jumps: nowhere to fall and be put back, every metre drivable both ways", () => {
    expect(of("respawn")).toHaveLength(0);
    const pts = routes.routes.find((r) => r.id === "main")!.points;
    // (the journey's road, start to end, measured over every 4 m)
    const { from, to } = meta.journey;
    const road: (P & { s: number })[] = [];
    let s = 0;
    pts.forEach((p, k) => {
      if (k) s += Math.hypot(p.x - pts[k - 1]!.x, p.z - pts[k - 1]!.z);
      if (s >= from && s <= to) road.push({ ...p, s });
    });
    expect(road.length).toBeGreaterThan(1000);
    let worst = 0;
    let j = 0;
    for (let k = 1; k < road.length; k++) {
      expect(road[k]!.s - road[k - 1]!.s).toBeLessThan(6);
      while (road[k]!.s - road[j]!.s > 4) j++;
      if (j > 0 && road[k]!.s - road[j - 1]!.s > 3.5)
        worst = Math.max(
          worst,
          Math.abs(road[k]!.y - road[j - 1]!.y) / (road[k]!.s - road[j - 1]!.s),
        );
    }
    expect(worst).toBeLessThan(0.16);
  });

  it("gives every stretch its own sound, and leaves the air to the overworld", () => {
    const [e] = of("atmosphere");
    const a = parseAtmosphere(e!);
    expect(a.light).toBe(false);
    const sounds = new Set(Object.values(a.zones).map((z) => z.sound));
    for (const s of ["drip", "harbour", "festival", "falls", "wind", "bells"])
      expect(sounds).toContain(s);
    expect(a.keys.length).toBeGreaterThan(150);
    // (at the docks, the harbour; out at the gate, its bells)
    const at = (x: number, y: number, z: number) => {
      const air = airAt(a, x, y, z)!;
      return Object.entries(air.sound).sort((p, q) => q[1] - p[1])[0]![0];
    };
    const near = (x: number, z: number) =>
      a.keys.reduce((best, k) =>
        Math.hypot(k.x - x, k.z - z) < Math.hypot(best.x - x, best.z - z) ? k : best,
      );
    const dock = near(-5, 332);
    expect(at(dock.x, dock.y, dock.z)).toBe("harbour");
    const gate = near(4, -440);
    expect(at(gate.x, gate.y, gate.z)).toBe("bells");
    // (a light-less atmosphere elsewhere still sets the light by default)
    expect(parseAtmosphere({ zones: {}, keys: [] }).light).toBe(true);
  });

  it("is alive between the districts and over the bridges", () => {
    expect(of("boat").length).toBeGreaterThanOrEqual(3);
    expect(of("motes").length).toBeGreaterThanOrEqual(12);
    expect(of("pterosaur").length).toBeGreaterThanOrEqual(3);
    expect(of("birds").length).toBeGreaterThanOrEqual(4);
    expect(of("waterfall")).toHaveLength(1);
    const flags = of("prayer_flags")[0]!.lines as unknown[];
    expect(flags.length).toBeGreaterThanOrEqual(20);
    expect(of("bells")[0]!.list as unknown[]).toHaveLength(4);
  });
});
