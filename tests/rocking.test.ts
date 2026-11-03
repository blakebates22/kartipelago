// The desert's frontier town (review-desert_region 2): dinos rocking in rocking chairs on
// their porches (render/partyDino.ts' "rock"), and no green lights out of Dry Gulch.
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { createPartyDinoView, DANCES, rockingChairGeometry } from "../src/render/partyDino";

describe("rocking chairs", () => {
  it("are a dance: the dino and its chair rock together, slowly", () => {
    expect(DANCES).toContain("rock");
    const g = rockingChairGeometry();
    expect(g.getAttribute("position").count).toBeGreaterThan(100);
    const parent = new THREE.Group();
    const v = createPartyDinoView(parent, 2);
    const tilts: number[] = [];
    for (let t = 0; t < 4; t += 0.25) {
      v.update(0, 0, 0, 1.0, "rock", t, 0.3);
      tilts.push(v.root.rotation.x);
    }
    expect(Math.max(...tilts) - Math.min(...tilts)).toBeGreaterThan(0.2);
    expect(Math.max(...tilts.map(Math.abs))).toBeLessThan(0.2);
    // (its chair came with it)
    expect(v.root.children.length).toBeGreaterThan(1);
    v.update(0, 0, 0, 1.0, "bounce", 0, 0);
    expect(v.root.rotation.x).toBe(0);
    v.dispose();
  });

  it("stand on the frontier town's porches", () => {
    const meta = JSON.parse(readFileSync("public/tracks/desert_region/track.json", "utf8")) as {
      entities: { type: string; dance?: string }[];
    };
    const rockers = meta.entities.filter((e) => e.type === "partygoer" && e.dance === "rock");
    expect(rockers.length).toBeGreaterThanOrEqual(2);
  });
});
