// The overworld's regions (src/overworld/regions.ts): every gateway opens a course that
// exists, ids are unique, and the trigger is a circle round the arch.
import { describe, expect, it } from "vitest";
import { existsSync } from "node:fs";
import { REGIONS, inGateway, regionById } from "../src/overworld/regions";
import { trackById } from "../src/game/tracks";
import { KINGDOMS } from "../src/adventure/data";
import { regionOfKingdom } from "../src/overworld/regions";

describe("overworld regions", () => {
  it("open courses that exist, on land that exists", () => {
    for (const r of REGIONS) {
      expect(existsSync(`public/tracks/${r.packageId}/track.json`), r.id).toBe(true);
      expect(new Set(r.gateways.map((g) => g.id)).size).toBe(r.gateways.length);
      for (const g of r.gateways) expect(trackById(g.track), g.id).toBeDefined();
    }
    expect(new Set(REGIONS.map((r) => r.id)).size).toBe(REGIONS.length);
  });

  it("open a gateway's card only inside its circle", () => {
    const g = regionById("test_valley")!.gateways[0]!;
    expect(inGateway(g, g.x, g.z)).toBe(true);
    expect(inGateway(g, g.x + g.radius - 0.1, g.z)).toBe(true);
    expect(inGateway(g, g.x + g.radius + 0.1, g.z)).toBe(false);
    expect(inGateway(g, g.x + g.radius + 0.1, g.z, 3)).toBe(true);
  });

  it("gives a kingdom's region a gateway for each of its courses (Adventure tours them)", () => {
    for (const k of KINGDOMS) {
      const r = regionOfKingdom(k.id);
      if (!r) continue;
      expect(r.gateways.map((g) => g.track).sort(), k.id).toEqual(
        k.courses.map((c) => c.track).sort(),
      );
    }
    expect(regionOfKingdom("valley")?.id).toBe("dinosaur_valley");
  });
});
