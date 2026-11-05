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
 * then, looking down at what's in front of them); busy all the time: "eat", "cook",
 * "chat", "lean", "beat", "hang", and the shanty band's "fiddle", "squeeze", "drum" (their
 * instruments in their hands: render/instruments.ts) and their crowd's "tap".
 */
import type * as THREE from "three";
import type { Gesture, PersonCue } from "../render/people/animate";

export type FolkPose =
  | "watch"
  | "wave"
  | "cheer"
  | "nod"
  | "point"
  | "think"
  | "shrug"
  | "dance"
  | "kneel"
  | "work"
  | "eat"
  | "cook"
  | "chat"
  | "lean"
  | "beat"
  | "hang"
  | "fiddle"
  | "squeeze"
  | "drum"
  | "tap";
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
  "eat",
  "cook",
  "chat",
  "lean",
  "beat",
  "hang",
  "fiddle",
  "squeeze",
  "drum",
  "tap",
];
/** The poses that are something to be busy at, all the time (render/people/animate.ts). */
const BUSY = new Set<FolkPose>([
  "eat",
  "cook",
  "chat",
  "lean",
  "beat",
  "hang",
  "dance",
  "kneel",
  "fiddle",
  "squeeze",
  "drum",
  "tap",
]);
/** The band (Blake, Nov 5: the shanty band, kept low-key): they play on, a glance and no
 * wave. */
export const PLAYING = new Set<FolkPose>(["fiddle", "squeeze", "drum"]);

export interface PosedFolk {
  x: number;
  y: number;
  z: number;
  heading: number;
  pose: FolkPose;
  seed: number;
  /** What they're busy with, to look at (game space): the one they're talking to, their
   * plate, the street below. */
  target?: { x: number; y: number; z: number };
}

/** One of them's state: whether they've had their glance at you as you came by. */
export interface FolkState {
  seen: boolean;
  glance: number;
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
      ...(r.length >= 9 && { target: { x: num(r[6], 0), y: num(r[7], 0), z: num(r[8], 0) } }),
    });
  }
  return out;
}

/** How far you can be and still have them watch you (m). */
export const FOLK_WATCH = 26;

/** How long they glance at you as you come by (s). */
export const FOLK_GLANCE = 1.6;

/**
 * What one of them is doing at t. Busy at their thing (eating, cooking, chatting,
 * leaning on the rail, beating a rug, hanging washing) all the time, looking at what
 * they're busy with; as you come by they glance at you (FOLK_GLANCE s, some with a wave)
 * and carry on (Blake, Nov 4: "they are just staring at me and its kinda weird"). The
 * rest (watch, wave, cheer...) do their gesture now and then, on their own clock.
 */
export function folkPoseCue(
  p: PosedFolk,
  st: FolkState,
  t: number,
  dt: number,
  near: boolean,
  you: THREE.Vector3 | null,
  at: THREE.Vector3 | null,
): PersonCue {
  if (near && !st.seen) {
    st.seen = true;
    st.glance = FOLK_GLANCE;
  } else if (!near) st.seen = false;
  st.glance = Math.max(0, st.glance - dt);
  const glancing = st.glance > 0;
  const look = glancing ? you : p.target && at ? at.set(p.target.x, p.target.y, p.target.z) : null;
  const period = 7 + (p.seed % 5);
  const phase = (t + p.seed * 1.37) % period;
  let gesture: Gesture | null = null;
  if (glancing && p.seed % 3 === 0 && p.pose !== "cook" && p.pose !== "eat" && !PLAYING.has(p.pose))
    gesture = "wave";
  else if (BUSY.has(p.pose)) gesture = p.pose as Gesture;
  else if (p.pose === "work") gesture = phase < 1.6 ? "nod" : null;
  else if (p.pose !== "watch" && phase < 2.6) gesture = p.pose as Gesture;
  // (talking: the chatters by turns, partners out of step; the cheerers now and then)
  const talk =
    p.pose === "chat" ? Math.sin(t * 0.6 + p.seed * 1.9) > 0 : p.pose === "cheer" && phase < 2.0;
  return { gesture, look, talk };
}
