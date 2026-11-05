/**
 * The Edge of the World's crowd in full detail near you (Blake, Nov 5, review note 4: "lets
 * increase the fidelity of these crocs"; he picked "detailed near, simple far"): the
 * crocs within CROWD_DETAIL_NEAR m of you are drawn as the detailed folk (render/people,
 * the Rookery's crocs) and busy at what their role says (game/folkPoses.ts), the rest
 * stay the instanced crowd (render/islesFx.ts). At most CROWD_DETAIL_MAX at once, the
 * nearest first; the views are pooled and handed from one croc to the next as you go.
 */
import type { FolkPose, PosedFolk } from "./folkPoses";
import type { Role, Villager } from "./isles";

/** How near (m) a croc of the crowd is drawn in detail. */
export const CROWD_DETAIL_NEAR = 36;
/** How many at once, at most. */
export const CROWD_DETAIL_MAX = 24;
/** How often (s) who's near is worked out again. */
export const CROWD_DETAIL_EVERY = 0.25;

/** What a croc of the crowd does in detail, by its role (busy, not staring). */
export function crowdPose(role: Role, variant: number): FolkPose {
  switch (role) {
    case "cheer":
      return "cheer";
    case "wave":
      return variant % 3 ? "wave" : "chat";
    case "huddle":
      return "chat";
    case "queue":
      return variant % 2 ? "think" : "shrug";
    case "merchant":
      return variant % 2 ? "chat" : "point";
    case "guard":
      return "nod";
    case "hauler":
    case "worker":
    case "fisher":
      return "work";
    case "musician":
      return "tap";
    case "dancer":
      return "dance";
    default:
      return "chat";
  }
}

/** One of the crowd as a posed folk: where they stand, their heading, what they do, and for
 * the talkers someone to look at (the one in front of them). */
export function crowdFolk(v: Villager, i: number): PosedFolk {
  const pose = crowdPose(v.role, v.variant + i);
  return {
    x: v.x,
    y: v.y,
    z: v.z,
    heading: Math.atan2(v.fx, v.fz),
    pose,
    seed: (v.variant * 3 + i) % 97,
    ...(pose === "chat" && { target: { x: v.x + v.fx * 1.4, y: v.y + 1.4, z: v.z + v.fz * 1.4 } }),
  };
}

/** The crowd's nearest (indices, nearest first) within `near` of (x, z), at most `max`. */
export function nearestCrowd(
  people: readonly { x: number; z: number }[],
  x: number,
  z: number,
  near = CROWD_DETAIL_NEAR,
  max = CROWD_DETAIL_MAX,
): number[] {
  const hits: [number, number][] = [];
  const n2 = near * near;
  for (let i = 0; i < people.length; i++) {
    const p = people[i]!;
    const d = (p.x - x) ** 2 + (p.z - z) ** 2;
    if (d < n2) hits.push([d, i]);
  }
  hits.sort((a, b) => a[0] - b[0]);
  return hits.slice(0, max).map((h) => h[1]);
}
