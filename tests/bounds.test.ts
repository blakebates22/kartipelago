// The overworld's bounds (Blake, Nov 4: "Whenever I drive around and go to the river or
// anywhere off the main road it's very easy to get out of bounds"): every region and
// journey has a bounds.json baked from its own collision (tools/audit/bounds.audit.ts
// BAKE=1), it keeps the whole road, the spawn and every way in and out in bounds, and the
// fence holds a kart at its edge and puts one that lands out of it back.
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { REGIONS } from "../src/overworld/regions";
import { createKartState } from "../src/vehicles/kart";
import {
  createFence,
  encodeBounds,
  inBounds,
  parseBounds,
  stepBounds,
  type BoundsFile,
  type BoundsMask,
} from "../src/world/bounds";
import { builtFrom } from "../tools/audit/boundsSync";

const PACKAGES = [
  ...new Set(REGIONS.map((r) => r.packageId).filter((p) => p !== "riverbend_palms")),
].flatMap((p) => (p.startsWith("journey_") ? [p] : [p, `${p}_ruin`]));
const dir = (p: string) => new URL(`../public/tracks/${p}/`, import.meta.url);
const load = (p: string) =>
  JSON.parse(readFileSync(new URL("bounds.json", dir(p)), "utf8")) as BoundsFile;

describe("the overworld's bounds", () => {
  it.each(PACKAGES)("%s: baked from its collision as it is now", async (p) => {
    const f = load(p);
    // (rebuilt the region? bake its bounds again: tools/audit/bounds.audit.ts BAKE=1)
    expect(f.builtFrom).toBe(builtFrom(dir(p)));
    expect(parseBounds(f)).toBeDefined();
  });

  it.each(PACKAGES)("%s: the road, the spawn and the ways in and out are in bounds", async (p) => {
    const b = parseBounds(load(p))!;
    const meta = JSON.parse(readFileSync(new URL("track.json", dir(p)), "utf8")) as {
      journey?: { from: number; to: number };
    };
    const route = JSON.parse(readFileSync(new URL("route.json", dir(p)), "utf8")) as {
      routes: { id: string; points: { x: number; y: number; z: number }[] }[];
    };
    const pts = route.routes.find((r) => r.id === "main")!.points;
    let s = 0;
    let out = 0;
    let n = 0;
    pts.forEach((q, i) => {
      if (i) s += Math.hypot(q.x - pts[i - 1]!.x, q.z - pts[i - 1]!.z);
      if (meta.journey && (s < meta.journey.from || s > meta.journey.to)) return;
      n++;
      if (!inBounds(b, q.x, q.y, q.z)) out++;
    });
    expect(n).toBeGreaterThan(50);
    // (all but a stray point where the road's centre line runs under an arch's lip)
    expect(out / n).toBeLessThan(0.01);
    const region = REGIONS.find((r) => r.packageId === p.replace(/_ruin$/, ""))!;
    for (const w of [...(region.passages ?? []), ...(region.gateways ?? [])]) {
      const near = [0, 4, 8].some((d) =>
        [0, 1, 2, 3, 4, 5, 6, 7].some((a) => {
          const x = w.x + d * Math.cos((a * Math.PI) / 4);
          const z = w.z + d * Math.sin((a * Math.PI) / 4);
          return inBounds(b, x, -1e6, z);
        }),
      );
      expect(near, `${p}: ${w.id} in bounds`).toBe(true);
    }
  });
});

describe("the fence", () => {
  // (a 20 x 20 m square in bounds, capped at 5 m on one side: a ridge over a tunnel)
  const mask = (): BoundsMask => {
    const w = 30;
    const top = new Float32Array(w * w).fill(NaN);
    for (let j = 5; j < 15; j++) for (let i = 5; i < 15; i++) top[j * w + i] = i < 8 ? 5 : Infinity;
    return parseBounds({ builtFrom: "", cell: 2, x0: 0, z0: 0, w, h: w, runs: encodeBounds(top) })!;
  };

  it("round-trips its file and knows where you may be", () => {
    const b = mask();
    expect(inBounds(b, 20, 0, 20)).toBe(true);
    expect(inBounds(b, 20, 900, 20)).toBe(true); // (no cap)
    expect(inBounds(b, 12, 7, 20)).toBe(true); // (within the slack over the cap)
    expect(inBounds(b, 12, 12, 20)).toBe(false); // (up on the ridge)
    expect(inBounds(b, 40, 0, 20)).toBe(false);
    expect(inBounds(b, 30, 0, 20)).toBe(true); // (the next cell along still counts)
  });

  it("holds a kart driving out at the edge, like a wall you can't see", () => {
    const b = mask();
    const f = createFence();
    const k = createKartState(20, 20, Math.PI / 2, 0);
    k.grounded = true;
    k.speed = 20;
    expect(stepBounds(f, k, b, 1 / 60)).toBeUndefined();
    let held = 0;
    for (let t = 0; t < 3; t += 1 / 60) {
      k.x += k.speed / 60; // (heading +x, flat out)
      k.speed = Math.max(k.speed, 15);
      if (stepBounds(f, k, b, 1 / 60) === "held") held++;
      expect(k.x).toBeLessThan(34);
    }
    expect(held).toBeGreaterThan(10);
  });

  it("puts a kart that lands out of bounds back on the road", () => {
    const b = mask();
    const f = createFence();
    const k = createKartState(20, 20, 0, 0);
    stepBounds(f, k, b, 1 / 60);
    // (flung far over the edge: in the air it's left be; landed, put back)
    Object.assign(k, { x: 50, z: 20, y: 0, grounded: false });
    expect(stepBounds(f, k, b, 1 / 60)).toBeUndefined();
    k.grounded = true;
    let r: string | undefined;
    for (let t = 0; t < 1 && !r; t += 1 / 60) r = stepBounds(f, k, b, 1 / 60);
    expect(r).toBe("respawn");
    // (and never touches a kart warped somewhere odd before it's been in bounds)
    const g = createFence();
    const w = createKartState(80, 80, 0, 0);
    w.grounded = true;
    for (let t = 0; t < 3; t += 1 / 60) expect(stepBounds(g, w, b, 1 / 60)).toBeUndefined();
  });
});
