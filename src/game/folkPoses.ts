/**
 * Folk posed about a place, in full detail (Blake, Nov 4: "we need to bring up the
 * fidelity of the npcs in the buildings. they look really bad"): the crocs leaning on the
 * Rookery's balconies, at its doors and in its windows, the cooks and diners in the Rusty
 * Anchor; the same detailed folk as the talkers (render/people), not the instanced crowd.
 * They stay where they're put: they watch you go by, and now and then wave, cheer, nod,
 * point, shrug or think, each on their own clock.
 *
 *   folk_poses  { "type": "folk_poses", "folk": "sump",
 *                 "list": [[x, y, z, heading, pose, seed], ...] }
 *
 * pose: "watch" (looks at you), "wave", "cheer", "nod", "point", "think", "shrug",
 * "dance", "kneel" (sat, crouched, on a step or a stool), "work" (busy: a nod now and
 * then, looking down at what's in front of them).
 */
import type * as THREE from "three";
import type { Gesture, PersonCue } from "../render/people/animate";

export type FolkPose =
  "watch" | "wave" | "cheer" | "nod" | "point" | "think" | "shrug" | "dance" | "kneel" | "work";
export const FOLK_POSES: readonly FolkPose[] = [
  "watch",
  "wave",
  "cheer",
  "nod",
  "point",
  "think",
  "shrug",
  "dance",
  "kneel",
  "work",
];

export interface PosedFolk {
  x: number;
  y: number;
  z: number;
  heading: number;
  pose: FolkPose;
  seed: number;
}

const num = (v: unknown, d: number) => (typeof v === "number" && Number.isFinite(v) ? v : d);

export function parseFolkPoses(e: Record<string, unknown>): PosedFolk[] {
  const list = Array.isArray(e.list) ? e.list : [];
  const out: PosedFolk[] = [];
  for (const r of list) {
    if (!Array.isArray(r) || r.length < 4) continue;
    const pose = FOLK_POSES.includes(r[4] as FolkPose) ? (r[4] as FolkPose) : "watch";
    out.push({
      x: num(r[0], 0),
      y: num(r[1], 0),
      z: num(r[2], 0),
      heading: num(r[3], 0),
      pose,
      seed: Math.abs(Math.round(num(r[5], 0))),
    });
  }
  return out;
}

/** How far you can be and still have them watch you (m). */
export const FOLK_WATCH = 26;

/**
 * What one of them is doing at t: their pose's gesture for a few seconds out of every
 * eight or so (offset by their seed, so a balcony row doesn't wave in step), watching you
 * when you're near (`near`), else looking out at the street.
 */
export function folkPoseCue(
  p: PosedFolk,
  t: number,
  near: boolean,
  look: THREE.Vector3 | null,
): PersonCue {
  const period = 7 + (p.seed % 5);
  const phase = (t + p.seed * 1.37) % period;
  let gesture: Gesture | null = null;
  if (p.pose === "kneel") gesture = "kneel";
  else if (p.pose === "dance") gesture = "dance";
  else if (p.pose === "work") gesture = phase < 1.6 ? "nod" : null;
  else if (p.pose !== "watch" && phase < 2.6) gesture = p.pose;
  else if (p.pose === "watch" && near && phase < 1.8) gesture = p.seed % 2 ? "wave" : "nod";
  return {
    gesture,
    look: near && p.pose !== "work" ? look : null,
    talk: p.pose === "cheer" && phase < 2.0,
  };
}
