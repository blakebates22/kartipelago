// The Edge of the World (journey_cause), Nov 3 (Blake: "you cant actually traverse
// backwards. lets just remove the jumps completely ... we need to make the immersiveness
// so great such that the boring driving is justified"): one road with no jumps, no gap in
// it and no slope a kart can't climb either way; each stretch its own sound (the
// atmosphere's sound only: the overworld paints the air); and life over the bridges.
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { airAt, parseAtmosphere } from "../src/game/depths";
import { craneHeading, craneLoad, parseCrane } from "../src/game/isles";
import { boatAt, parseBoat } from "../src/game/oasis";

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
    // (the sea pouring off the edge over the Long Bore's mouth, and the sea leak in the docks)
    expect(of("waterfall")).toHaveLength(2);
    const flags = of("prayer_flags")[0]!.lines as unknown[];
    expect(flags.length).toBeGreaterThanOrEqual(20);
    expect(of("bells")[0]!.list as unknown[]).toHaveLength(4);
  });

  it("has a harbour that makes sense (Blake, Nov 4): its water in and out, boats under the bridge", () => {
    expect(of("zipper")).toHaveLength(0);
    // (rowing boats, no masts, on one round under the bridge's arch)
    const round = routes.routes.find((r) => r.id === "Harbour Boat Round")!;
    const rowers = of("boat").filter((e) => e.route === "Harbour Boat Round");
    expect(rowers.length).toBe(4);
    const b = parseBoat(rowers[0]!, routes.routes as never)!;
    expect(b.rig).toBe("row");
    expect(boatAt(b, 3).heel).toBeLessThan(0.06);
    // (where the round passes under the road, Blender (-3, y): the bridge is over it, at
    // least 2.8 m of road over the water: its arch 1.7 m up, over the boats)
    const under = round.points.filter((p) => Math.abs(p.x + 3) < 1.5);
    expect(under.length).toBeGreaterThan(0);
    for (const p of under) {
      const bridge = routes.routes
        .find((r) => r.id === "main")!
        .points.filter((q) => Math.hypot(q.x - p.x, q.z - p.z) < 6);
      expect(bridge.length).toBeGreaterThan(0);
      expect(Math.min(...bridge.map((q) => q.y)) - p.y).toBeGreaterThan(2.8);
    }
    // (the crane slewing out over the road with its crate, high over the karts)
    const slewing = of("crane")
      .map((e) => parseCrane(e))
      .filter((c) => c.slew > 0);
    expect(slewing).toHaveLength(1);
    const c = slewing[0]!;
    expect(c.load).toBe("crate");
    expect(Math.abs(craneHeading(c, c.slewPeriod / 4) - craneHeading(c, 0))).toBeGreaterThan(0.5);
    expect(craneLoad(c, c.period / 2).block.y).toBeGreaterThan(-18);
    // (cargo nets and crates going up and down on the pulleys)
    expect(of("crane").filter((e) => e.load === "net").length).toBeGreaterThanOrEqual(2);
    // (the sea leak's light and the bridge's lanterns light the water)
    expect(of("glow").length).toBeGreaterThanOrEqual(8);
    expect(of("mist").length).toBeGreaterThanOrEqual(8);
  });
});
