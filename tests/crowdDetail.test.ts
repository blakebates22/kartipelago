// The Edge's crowd in detail near you (Blake, Nov 5, review note 4: "lets increase the
// fidelity of these crocs"; he picked "detailed near, simple far").
import { describe, expect, it } from "vitest";
import {
  CROWD_DETAIL_MAX,
  CROWD_DETAIL_NEAR,
  crowdFolk,
  crowdPose,
  nearestCrowd,
} from "../src/game/crowdDetail";
import { FOLK_POSES } from "../src/game/folkPoses";
import { ROLES, type Villager } from "../src/game/isles";

const at = (x: number, z: number, role: Villager["role"] = "cheer"): Villager => ({
  x,
  y: 0,
  z,
  fx: 0,
  fz: 1,
  role,
  variant: 0,
  palette: "sump",
});

describe("the crowd in detail near you", () => {
  it("picks the nearest within reach, nearest first, no more than the most", () => {
    const people = [at(50, 0), at(3, 0), at(0, 10), at(0, 2), at(CROWD_DETAIL_NEAR + 1, 0)];
    expect(nearestCrowd(people, 0, 0)).toEqual([3, 1, 2]);
    const many = Array.from({ length: 80 }, (_, i) => at(i * 0.3, 0));
    const got = nearestCrowd(many, 0, 0);
    expect(got).toHaveLength(CROWD_DETAIL_MAX);
    expect(got[0]).toBe(0);
  });

  it("keeps every role busy at something, nobody just staring", () => {
    for (const role of ROLES)
      for (const v of [0, 1, 2]) {
        const pose = crowdPose(role, v);
        expect(FOLK_POSES).toContain(pose);
        expect(pose).not.toBe("watch");
      }
  });

  it("stands them where the crowd stands them, the talkers looking at who's in front", () => {
    const f = crowdFolk({ ...at(4, 5, "huddle"), fx: 1, fz: 0 }, 0);
    expect([f.x, f.z]).toEqual([4, 5]);
    expect(f.heading).toBeCloseTo(Math.PI / 2);
    expect(f.pose).toBe("chat");
    expect(f.target!.x).toBeGreaterThan(4);
  });
});
