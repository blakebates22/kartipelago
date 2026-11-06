// The Edge's dragons winged (Blake, Nov 6, review journey_cause 2 note 1: "the dragons are
// still the chinese dragons these need to be reworked completely").
import * as THREE from "three";
import { describe, expect, it } from "vitest";
import { createWyvernView } from "../src/render/wyvern";

describe("the winged dragon", () => {
  it("flies to where it's sent, facing the way it goes, its spine trailing behind", () => {
    const g = new THREE.Group();
    const w = createWyvernView(g, 0.5, { body: "#8a2418", belly: "#e8b048" });
    const look = { at: new THREE.Vector3(), amount: 0 };
    for (let t = 0; t <= 6; t += 1 / 30) w.update(new THREE.Vector3(t * 20, 30, 0), t, look);
    expect(w.head.x).toBeCloseTo(120, 3);
    // (its body behind its head, along +x the way it flew)
    expect(w.spine[0]!.x).toBeGreaterThan(w.spine[w.spine.length - 1]!.x);
    expect(w.spine.every((p) => Math.abs(p.y - 30) < 1e-6)).toBe(true);
    const root = g.children[0]!;
    const fwd = new THREE.Vector3(0, 0, 1).applyQuaternion(root.quaternion);
    expect(fwd.x).toBeGreaterThan(0.9);
    w.dispose();
    expect(g.children).toHaveLength(0);
  });
});
