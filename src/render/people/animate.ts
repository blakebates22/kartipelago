/**
 * The people's animation: one animator drives every person's rig (rig.ts), the same way
 * the racers' animator drives every rider, with each person's stance setting their
 * build and temper (an old elder stoops and moves slowly; a small one bounces).
 *
 *   breathing, weight shift, blinks           (always)
 *   head and eyes turning to a look target    (the speaker, or the camera)
 *   talking: the jaw in a speech rhythm       (while they have the line)
 *   walking: feet planted, stepping by the distance travelled (never skating)
 *   gestures: wave, point, cheer, nod, shake, shrug, bow, cower, think, raiseStaff,
 *             blowHorn, breakHorn, holdOut, touchHorn, dance, kneel   (each blends in and out)
 *
 * Purely visual: it reads the cue and the distance moved, and poses the rig.
 */
import * as THREE from "three";
import { reach } from "../racers/kit/rig";
import type { PersonRig, V3 } from "./rig";

export type Gesture =
  | "wave"
  | "point"
  | "cheer"
  | "nod"
  | "shake"
  | "shrug"
  | "bow"
  | "cower"
  | "think"
  | "raiseStaff"
  | "blowHorn"
  | "breakHorn"
  | "holdOut"
  | "touchHorn"
  | "dance"
  | "kneel";

export const GESTURES: readonly Gesture[] = [
  "wave",
  "point",
  "cheer",
  "nod",
  "shake",
  "shrug",
  "bow",
  "cower",
  "think",
  "raiseStaff",
  "blowHorn",
  "breakHorn",
  "holdOut",
  "touchHorn",
  "dance",
  "kneel",
];

/** What a person is doing this frame. */
export interface PersonCue {
  /** Talking (they have the line). */
  talk?: boolean;
  gesture?: Gesture | null;
  /** A point in the world to look at (the speaker, the camera), or none. */
  look?: THREE.Vector3 | null;
}

/** A carried thing's pose: in torso space, or in a hand (0 left, 1 right). */
type PropPose = { at: V3; rot: V3; w?: number } | { hand: 0 | 1; at?: V3; rot?: V3; w?: number };

/** A gesture's pose at a moment. Angles in radians; positions in torso space. */
interface GPose {
  /** Hips lowered (m) and bent forward (a bow from the hips). */
  crouch?: number;
  hipsPitch?: number;
  lean?: number;
  roll?: number;
  twist?: number;
  head?: [number, number, number];
  jaw?: number;
  lids?: number;
  brow?: number;
  wide?: number;
  hands?: [V3 | null, V3 | null];
  /** Extra turn of each hand (XYZ). */
  handRot?: [V3 | null, V3 | null];
  /** Feet moved from rest (root space), by leg index. */
  feet?: Record<number, V3>;
  props?: Record<string, PropPose>;
  /** How much the look target still turns the head (1 = fully). */
  look?: number;
  /** The mouth is busy (the horn): no talking. */
  mouthBusy?: boolean;
  /** The horn snapped. */
  snapped?: boolean;
}

/** Where things are this frame, in torso space (for gestures to reach for). */
interface Ctx {
  mouth: THREE.Vector3;
  chin: THREE.Vector3;
  shoulder: [THREE.Vector3, THREE.Vector3];
  /** Forward toward the look target (torso space, unit). */
  toward: THREE.Vector3;
  quad: boolean;
  rig: PersonRig;
}

const tPoint = new THREE.Vector3();
const Y_AXIS = new THREE.Vector3(0, 1, 0);
const sm = (x: number) => {
  const t = Math.max(0, Math.min(1, x));
  return t * t * (3 - 2 * t);
};
/** 0 -> 1 over [a, b]. */
const ramp = (t: number, a: number, b: number) => sm((t - a) / Math.max(1e-4, b - a));
const ease = (v: number, target: number, rate: number, dt: number) =>
  v + (target - v) * (1 - Math.exp(-rate * dt));
const v3 = (v: THREE.Vector3): V3 => [v.x, v.y, v.z];
const add3 = (a: V3, b: V3, k = 1): V3 => [a[0] + b[0] * k, a[1] + b[1] * k, a[2] + b[2] * k];
const lerp3 = (a: V3, b: V3, t: number): V3 => [
  a[0] + (b[0] - a[0]) * t,
  a[1] + (b[1] - a[1]) * t,
  a[2] + (b[2] - a[2]) * t,
];

/** A held thing posed so its grip point (its own space) is at `hand`, pointing along `dir`. */
function gripAt(hand: V3, dir: V3, grip: V3): PropPose {
  const q = new THREE.Quaternion().setFromUnitVectors(
    new THREE.Vector3(0, 0, 1),
    new THREE.Vector3(...dir).normalize(),
  );
  const g = new THREE.Vector3(...grip).applyQuaternion(q);
  const e = new THREE.Euler().setFromQuaternion(q);
  return { at: [hand[0] - g.x, hand[1] - g.y, hand[2] - g.z], rot: [e.x, e.y, e.z], w: 1 };
}

/** The gestures. `t` is seconds since it began; hands are [left, right] in torso space. */
const POSES: Record<Gesture, (t: number, c: Ctx) => GPose> = {
  wave(t, c) {
    const s = c.shoulder[1];
    const w = Math.sin(t * 9) * 0.09;
    return {
      hands: [null, [s.x - 0.12 + w, s.y + 0.32, s.z + 0.1]],
      handRot: [null, [-1.4, 0, -0.6 + Math.sin(t * 9) * 0.35]],
      roll: 0.06,
      head: [-0.05, 0, -0.08],
      jaw: 0.3,
      brow: 0.5,
      feet: c.quad ? { 3: [0, 0.22 + Math.sin(t * 9) * 0.06, 0.18] } : undefined,
    };
  },
  point(t, c) {
    const s = c.shoulder[1];
    // (Off to one side of whoever they're talking to: over there.)
    const d = tPoint.copy(c.toward).applyAxisAngle(Y_AXIS, -0.75).normalize();
    const reachOut = 0.55 + 0.03 * Math.sin(t * 2);
    return {
      hands: [
        null,
        [s.x + d.x * reachOut - 0.05, s.y + 0.06 + d.y * reachOut, s.z + d.z * reachOut],
      ],
      handRot: [null, [0, 0, -0.4]],
      lean: 0.08,
      twist: Math.atan2(d.x, d.z) * 0.25,
      brow: 0.3,
      feet: c.quad ? { 3: [0, 0.18, 0.25] } : undefined,
    };
  },
  cheer(t, c) {
    const hop = Math.max(0, Math.sin(t * 7)) * 0.07;
    const pump = Math.sin(t * 7) * 0.05;
    const [l, r] = c.shoulder;
    return {
      crouch: -hop + 0.02,
      hands: [
        [l.x + 0.1, l.y + 0.42 + pump, l.z + 0.08],
        [r.x - 0.1, r.y + 0.42 - pump, r.z + 0.08],
      ],
      handRot: [
        [-1.2, 0, 0.4],
        [-1.2, 0, -0.4],
      ],
      head: [-0.25, 0, Math.sin(t * 3.5) * 0.08],
      lean: c.quad ? -0.25 : -0.08,
      jaw: 0.75,
      lids: t % 1.4 > 0.7 ? 0.8 : 0,
      brow: 0.7,
    };
  },
  dance(t, c) {
    // A festival dance: bouncing on the beat, swaying side to side, one arm up and then
    // the other, the head bobbing along.
    const beat = t * 2 * Math.PI * 1.15;
    const bounce = Math.abs(Math.sin(beat)) * 0.06;
    const sway = Math.sin(beat / 2);
    const [l, r] = c.shoulder;
    const up = (k: number) => Math.max(0, k);
    return {
      crouch: 0.04 - bounce,
      roll: sway * 0.12,
      twist: sway * 0.18,
      hands: [
        [l.x + 0.12, l.y + 0.1 + up(sway) * 0.36, l.z + 0.16],
        [r.x - 0.12, r.y + 0.1 + up(-sway) * 0.36, r.z + 0.16],
      ],
      handRot: [
        [-1.0, 0, 0.5],
        [-1.0, 0, -0.5],
      ],
      head: [-0.08 + Math.sin(beat) * 0.08, sway * 0.15, sway * 0.12],
      lean: c.quad ? -0.15 : -0.04,
      jaw: 0.5,
      brow: 0.6,
      lids: 0.15,
    };
  },
  nod(t) {
    const n = t < 1.6 ? Math.sin(t * 9) * 0.22 * (1 - t / 1.8) : 0;
    return { head: [0.12 + Math.max(-0.05, n), 0, 0], brow: 0.2, lids: 0.15 };
  },
  shake(t) {
    const n = t < 2 ? Math.sin(t * 10) * 0.32 * (1 - t / 2.2) : 0;
    return { head: [0.06, n, 0], brow: -0.4, jaw: 0.05 };
  },
  shrug(t, c) {
    const up = ramp(t, 0, 0.35) * (1 - ramp(t, 1.6, 2.1) * 0.5);
    const [l, r] = c.shoulder;
    return {
      hands: [
        [l.x + 0.22, l.y - 0.2 + up * 0.08, l.z + 0.2],
        [r.x - 0.22, r.y - 0.2 + up * 0.08, r.z + 0.2],
      ],
      handRot: [
        [0, 0, 1.4],
        [0, 0, -1.4],
      ],
      head: [0.02, 0, 0.18 * up],
      roll: -0.04 * up,
      brow: 0.8 * up,
      jaw: 0.15,
    };
  },
  bow(t, c) {
    const d = ramp(t, 0, 0.7) * (1 - ramp(t, 2.4, 3.2) * 0.4);
    const [l, r] = c.shoulder;
    return {
      // (Four-legged: a dip of the head and shoulders, not the whole body.)
      hipsPitch: (c.quad ? 0.1 : 0.62) * d,
      head: [(c.quad ? 0.7 : 0.35) * d, 0, 0],
      hands: c.quad
        ? undefined
        : [
            [l.x - 0.12, l.y - 0.32, l.z + 0.16],
            [r.x + 0.12, r.y - 0.32, r.z + 0.16],
          ],
      lids: 0.6 * d,
      look: 1 - d,
      crouch: c.quad ? 0.05 * d : 0.03 * d,
      feet: c.quad ? { 2: [0, 0, 0.12 * d], 3: [0, 0, 0.12 * d] } : undefined,
    };
  },
  cower(t, c) {
    const d = ramp(t, 0, 0.25);
    const tr = Math.sin(t * 38) * 0.012;
    const [l, r] = c.shoulder;
    return {
      crouch: 0.16 * d + tr,
      lean: -0.18 * d,
      hipsPitch: 0.08 * d,
      head: [0.2 * d, 0.2 * d, 0.1 * d],
      hands: [
        [l.x - 0.16, l.y + 0.12 + tr, l.z + 0.28],
        [r.x + 0.12, r.y + 0.2 - tr, r.z + 0.3],
      ],
      handRot: [
        [-1.3, 0, 1.2],
        [-1.3, 0, -1.2],
      ],
      wide: 0.9 * d,
      brow: 0.9,
      jaw: 0.35,
      look: 0.6,
    };
  },
  think(t, c) {
    const d = ramp(t, 0, 0.5);
    const r = c.shoulder[1];
    const chin = c.chin;
    return {
      hands: [
        [c.shoulder[0].x - 0.14, c.shoulder[0].y - 0.18, c.shoulder[0].z + 0.2],
        [chin.x - 0.02, chin.y - 0.06, chin.z + 0.02],
      ],
      handRot: [null, [-1.6, 0, -1.2]],
      head: [-0.12 * d, -0.15 * d, 0.16 * d + Math.sin(t * 1.3) * 0.03],
      lids: 0.3,
      brow: -0.2 + Math.sin(t * 0.9) * 0.4,
      jaw: 0.02,
      look: 0.3,
      twist: 0.05 * d,
      roll: -0.03 * d + r.x * 0,
    };
  },
  raiseStaff(t, c) {
    const d = ramp(t, 0, 0.6);
    const l = c.shoulder[0];
    const thrust = Math.max(0, Math.sin(Math.min(1, t / 0.6) * Math.PI)) * 0.05;
    return {
      hands: [[l.x + 0.08, l.y + 0.36 * d + thrust, l.z + 0.18], null],
      handRot: [[-0.5, 0, 0.2], null],
      lean: -0.22 * d,
      head: [-0.22 * d, 0, 0],
      props: { staff: { hand: 0, rot: [-0.25 * d, 0, -0.15 * d], w: 1 } },
      brow: 0.6,
      jaw: 0.35,
      wide: 0.3 * d,
    };
  },
  blowHorn(t, c) {
    // Lift it to the mouth (0.7 s), a big breath, then blow: straightening up, the horn
    // raised high, eyes squeezed shut. (The other hand keeps hold of his staff.)
    const d = ramp(t, 0, 0.7);
    const blow = ramp(t, 0.9, 1.15);
    const m = c.mouth;
    const at: V3 = [m.x, m.y - 0.005, m.z + 0.015];
    const horn: PropPose = {
      at: lerp3([-0.24, 0.12, 0.0], at, d),
      rot: lerp3([0.6, 0.2, 0.1], [-0.55 - 0.25 * blow, 0.06, 0], d),
      w: ramp(t, 0, 0.2),
    };
    return {
      props: { hornA: horn, hornB: horn },
      hands: [null, [m.x - 0.035, m.y - 0.07, m.z + 0.1]],
      handRot: [null, [-0.6, 0, -1.5]],
      lean: -0.22 * d - 0.06 * blow,
      head: [-0.12 * d - 0.12 * blow, 0, 0],
      lids: blow > 0.5 ? 0.92 : 0.1,
      brow: 0.8 * blow,
      jaw: 0.06,
      mouthBusy: true,
      look: 0.2,
      crouch: -0.01 * blow,
      wide: 0.3 * (1 - blow) * d,
    };
  },
  breakHorn(t) {
    // He leans his staff on his shoulder and takes the horn in both hands (0..0.6),
    // lifts it and a knee (..1.0), brings it down across the knee: SNAP (1.2), and holds
    // the two halves apart, looking at them (sagging, after).
    const take = ramp(t, 0, 0.6);
    const wind = ramp(t, 0.6, 1.0);
    const slam = ramp(t, 1.0, 1.2);
    const snap = t >= 1.2;
    const apart = ramp(t, 1.2, 1.55);
    const sag = ramp(t, 2.0, 2.8);
    const y = 0.16 + wind * 0.16 - slam * 0.3;
    const z = 0.34 + wind * 0.02 + slam * 0.04;
    const knee = Math.max(0, wind - apart);
    const hy0 = snap ? 0.06 + apart * 0.2 - sag * 0.2 : y;
    const hl: V3 = [0.15 + apart * 0.2, hy0, z - 0.02 + apart * 0.04];
    const hr: V3 = [-0.15 - apart * 0.2, hy0, z - 0.02 + apart * 0.04];
    // (After the snap: each half held by its middle, raised and turned out to look at.)
    const up = 0.9 - sag * 0.6;
    const halves: Record<string, PropPose> = snap
      ? {
          hornA: gripAt(hl, [0.55, up, 0.35], [0, 0.012, 0.1]),
          hornB: gripAt(hr, [-0.4, up, 0.45], [0, 0.07, 0.27]),
        }
      : {
          hornA: { at: [0.17, y - 0.02, z], rot: [0, -Math.PI / 2, 0], w: take },
          hornB: { at: [0.17, y - 0.02, z], rot: [0, -Math.PI / 2, 0], w: take },
        };
    return {
      props: { ...halves, staff: { at: [0.3, 0.26, 0.1], rot: [0.1, 0, -0.18], w: take } },
      hands: snap
        ? [hl, hr]
        : [
            [0.15, y, z - 0.02],
            [-0.15, y, z - 0.02],
          ],
      handRot: [
        [-0.2, 0, 1.4],
        [-0.2, 0, -1.4],
      ],
      feet: { 1: [0, 0.26 * knee, 0.24 * knee] },
      lean: 0.1 * wind + 0.12 * slam + 0.12 * sag - 0.1 * apart,
      head: [0.3 * take + 0.12 * sag, 0, 0],
      crouch: 0.03 * slam * (1 - apart),
      brow: -0.7 * take * (1 - apart) + 0.6 * sag,
      lids: 0.2 + 0.45 * sag,
      jaw: t > 1.15 && t < 1.5 ? 0.55 : 0.04,
      snapped: snap,
      look: 0.25,
    };
  },
  holdOut(t, c) {
    // Dangling the key ring up by his face, out toward whoever's getting it.
    const d = ramp(t, 0, 0.5);
    const r = c.shoulder[1];
    const dz = c.toward;
    const jig = Math.sin(t * 6) * 0.015 * d;
    return {
      hands: [null, [r.x + 0.06 + dz.x * 0.3, r.y + 0.32 * d + jig, r.z + 0.32 * d + 0.06]],
      handRot: [null, [-1.3, 0, -0.4]],
      props: { key: { hand: 1, w: ramp(t, 0.1, 0.35) } },
      lean: 0.06 * d,
      head: [-0.04, 0, -0.1],
      brow: 0.5,
      jaw: 0.25,
    };
  },
  touchHorn(t) {
    // His hand goes to the horn at his hip, closes round its middle and lifts it a little
    // out in front of him on that side (clear of his belly), and he looks down at it (the
    // story turns on it).
    const d = ramp(t, 0.1, 0.9);
    const grip: V3 = lerp3([-0.3, 0.06, -0.06], [-0.3, 0.2, 0.42], d);
    const dir = lerp3([0.1, 0.5, -0.3], [-0.1, 0.55, 1], d);
    const horn = gripAt(grip, dir, [0, 0.035, 0.18]);
    return {
      props: { hornA: horn, hornB: horn },
      hands: [null, [grip[0], grip[1] + 0.015, grip[2]]],
      handRot: [null, [-0.6, 0, -1.2]],
      head: [0.36 * d, 0.18 * d, 0.04 * d],
      lean: 0.06 * d,
      brow: -0.5 * d,
      lids: 0.35,
      jaw: 0.02,
      look: 0.1,
    };
  },
  kneel(t, c) {
    const d = ramp(t, 0, 0.8);
    const [l, r] = c.shoulder;
    return {
      crouch: 0.32 * d,
      feet: { 1: [0, 0, -0.34 * d], 0: [0, 0, 0.14 * d] },
      hipsPitch: 0.1 * d,
      head: [0.32 * d, 0, 0],
      hands: [
        [l.x - 0.02, l.y - 0.3, l.z + 0.3],
        [r.x + 0.18, r.y - 0.18, r.z + 0.26],
      ],
      lids: 0.45 * d,
      look: 1 - d * 0.7,
    };
  },
};

/** The speech rhythm: the jaw opening on syllables, grouped into words with pauses. */
export function speech(t: number) {
  const syl = 0.5 + 0.5 * Math.sin(t * 24 + 2.1 * Math.sin(t * 3.3));
  const word = sm((Math.sin(t * 4.7) + Math.sin(t * 2.3 + 1.3) + 0.9) * 1.5);
  return 0.08 + syl * word * 0.82;
}

function rng(seed: number) {
  let a = seed >>> 0 || 1;
  return () => {
    a ^= a << 13;
    a ^= a >>> 17;
    a ^= a << 5;
    return ((a >>> 0) % 10000) / 10000;
  };
}

const tA = new THREE.Vector3();
const tB = new THREE.Vector3();
const tQ = new THREE.Quaternion();
const tQ2 = new THREE.Quaternion();
const tE = new THREE.Euler();
const tM = new THREE.Matrix4();
const ONE = new THREE.Vector3(1, 1, 1);
const compose = (p: V3, r: V3) =>
  new THREE.Matrix4().compose(
    new THREE.Vector3(...p),
    new THREE.Quaternion().setFromEuler(new THREE.Euler(...r)),
    ONE,
  );

export class PersonAnimator {
  private t = 0;
  private rand: () => number;
  /** Gesture weights (eased) and when each began. */
  private w = new Map<Gesture, { w: number; t0: number }>();
  private current: Gesture | null = null;
  private phase = 0;
  private walkW = 0;
  private speed = 0;
  private talkW = 0;
  private talkT = 0;
  private blinkIn: number;
  private blink = 0;
  private yaw = 0;
  private pitch = 0;
  private eyeYaw = 0;
  private eyePitch = 0;
  private idleLookIn = 2;
  private idleYaw = 0;
  /** Persistent: the horn is broken. */
  hornBroken = false;
  private ctx: Ctx;

  constructor(
    readonly rig: PersonRig,
    seed = 1,
  ) {
    this.rand = rng(seed * 7919 + 13);
    this.blinkIn = 0.5 + this.rand() * 2;
    this.t = this.rand() * 10;
    const sh = rig.arms.map((a) => a.shoulder.clone());
    this.ctx = {
      mouth: new THREE.Vector3(0, 0.8, 0.3),
      chin: new THREE.Vector3(0, 0.75, 0.3),
      shoulder: [sh[0] ?? new THREE.Vector3(0.2, 0.4, 0), sh[1] ?? new THREE.Vector3(-0.2, 0.4, 0)],
      toward: new THREE.Vector3(0, 0, 1),
      quad: rig.stance.quad,
      rig,
    };
  }

  /**
   * One frame. `moved`: metres travelled since the last frame (the walk steps by it).
   * The rig's root must already be placed in the world (its matrixWorld current).
   */
  step(dt: number, cue: PersonCue, moved: number) {
    dt = Math.min(Math.max(dt, 0), 0.1);
    this.t += dt;
    const rig = this.rig;
    const S = rig.stance;
    const resp = S.response;
    const t = this.t;

    // --- Gestures: the cued one blends in, the rest out.
    const g = cue.gesture ?? null;
    if (g !== this.current) {
      this.current = g;
      if (g) {
        const e = this.w.get(g);
        this.w.set(g, { w: e?.w ?? 0, t0: t });
      }
    }
    for (const [k, e] of this.w) {
      e.w = ease(e.w, k === g ? 1 : 0, (k === g ? 5 : 4) * resp, dt);
      if (k !== g && e.w < 0.002) this.w.delete(k);
    }

    // --- Walking: by the distance moved (so the feet never skate).
    const sp = dt > 0 ? Math.min(6, moved / dt) : 0;
    this.speed = ease(this.speed, sp, 6, dt);
    this.walkW = ease(this.walkW, this.speed > 0.15 ? 1 : 0, 5, dt);
    const scale = rig.root.getWorldScale(tA).x || 1;
    this.phase = (this.phase + moved / scale / (2 * S.stride)) % 1;
    const walk = this.walkW;

    // --- Talking.
    this.talkW = ease(this.talkW, cue.talk ? 1 : 0, 10, dt);
    if (cue.talk) this.talkT += dt;

    // --- The pose: the gestures' blended over the idle.
    let crouch = 0;
    let hipsPitch = 0;
    let lean = S.stoop;
    let roll = 0;
    let twist = 0;
    let head: V3 = [0, 0, 0];
    let jaw = S.restJaw;
    let lids = S.restLids;
    let brow = S.restBrow;
    let wide = 0;
    let lookK = 1;
    let mouthBusy = false;
    const hands: (V3 | null)[] = [null, null];
    const handW = [0, 0];
    const handRot: V3[] = [
      [0, 0, 0],
      [0, 0, 0],
    ];
    const feet = new Map<number, V3>();
    const props = new Map<string, { pose: PropPose; w: number }>();
    for (const [k, e] of this.w) {
      const p = POSES[k](t - e.t0, this.ctx);
      const w = e.w;
      if (p.snapped && k === "breakHorn") this.hornBroken = true;
      if (p.crouch !== undefined) crouch += p.crouch * w;
      if (p.hipsPitch !== undefined) hipsPitch += p.hipsPitch * w;
      if (p.lean !== undefined) lean += p.lean * w;
      if (p.roll !== undefined) roll += p.roll * w;
      if (p.twist !== undefined) twist += p.twist * w;
      if (p.head) head = add3(head, p.head, w);
      if (p.jaw !== undefined) jaw += (p.jaw - jaw) * w;
      if (p.lids !== undefined) lids += (p.lids - lids) * w;
      if (p.brow !== undefined) brow += (p.brow - brow) * w;
      if (p.wide !== undefined) wide += (p.wide - wide) * w;
      if (p.look !== undefined) lookK += (p.look - lookK) * w;
      if (p.mouthBusy && w > 0.3) mouthBusy = true;
      p.hands?.forEach((h, i) => {
        if (!h) return;
        hands[i] = hands[i] ? lerp3(hands[i]!, h, w) : h;
        handW[i] = Math.max(handW[i]!, w);
      });
      p.handRot?.forEach((r, i) => {
        if (r) handRot[i] = lerp3(handRot[i]!, r, w);
      });
      if (p.feet)
        for (const [i, off] of Object.entries(p.feet)) {
          const was = feet.get(+i) ?? [0, 0, 0];
          feet.set(+i, add3(was, off, w));
        }
      if (p.props)
        for (const [n, pp] of Object.entries(p.props))
          props.set(n, { pose: pp, w: (pp.w ?? 1) * w });
    }

    // A curious one tilts their head now and then.
    if (S.curious > 0)
      head = add3(head, [0, 0, Math.max(0, Math.sin(t * 0.7) - 0.3) * 0.35 * S.curious]);
    // Idle: breathing, weight shift, a glance about now and then.
    const breath = Math.sin(t * 1.7) * S.breath;
    const shift = Math.sin(t * 0.45) * S.sway * (1 - walk);
    this.idleLookIn -= dt;
    if (this.idleLookIn <= 0) {
      this.idleLookIn = S.glance * (0.6 + this.rand() * 0.9);
      this.idleYaw = (this.rand() - 0.5) * (S.glance < 2 ? 1.2 : 0.7);
    }

    // Talking: the jaw in the speech rhythm, small nods and brow lifts.
    if (this.talkW > 0.01 && !mouthBusy) {
      const s = speech(this.talkT);
      jaw += (s * 0.85 - jaw * 0.5) * this.talkW;
      head = add3(
        head,
        [Math.sin(this.talkT * 3.1) * 0.05, Math.sin(this.talkT * 1.3) * 0.05, 0],
        this.talkW,
      );
      brow += Math.max(0, Math.sin(this.talkT * 1.7)) * 0.35 * this.talkW;
    }

    // --- Look: toward the target (or about, idly), eyes first, then the head.
    let wantYaw = this.idleYaw * 0.5;
    let wantPitch = 0;
    if (cue.look) {
      rig.neck.getWorldPosition(tA);
      tB.copy(cue.look).sub(tA);
      rig.root.getWorldQuaternion(tQ).invert();
      tB.applyQuaternion(tQ);
      wantYaw = Math.atan2(tB.x, tB.z);
      wantPitch = Math.atan2(tB.y, Math.hypot(tB.x, tB.z));
      // (Toward it, for pointing and holding things out.)
      this.ctx.toward.set(tB.x, tB.y * 0.3, Math.max(0.3, tB.z)).normalize();
    } else this.ctx.toward.set(0, 0, 1);
    const reachYaw = 1.25 * S.lookReach;
    wantYaw = Math.max(-reachYaw, Math.min(reachYaw, wantYaw)) * lookK;
    wantPitch = Math.max(-0.5, Math.min(0.45, wantPitch)) * lookK;
    const oldYaw = this.yaw;
    this.eyeYaw = ease(this.eyeYaw, wantYaw, 16, dt);
    this.eyePitch = ease(this.eyePitch, wantPitch, 16, dt);
    this.yaw = ease(this.yaw, wantYaw, 4.2 * resp, dt);
    this.pitch = ease(this.pitch, wantPitch, 4.2 * resp, dt);
    // A big turn of the head starts with a blink.
    if (Math.abs(this.yaw - oldYaw) > 1.4 * dt && this.blink <= 0 && this.rand() < dt * 3)
      this.blink = 0.14;

    // --- Apply: body, hips, torso, neck, head.
    const bob =
      walk *
      (S.quad
        ? Math.cos(this.phase * Math.PI * 4) * 0.02
        : Math.cos(this.phase * Math.PI * 4) * 0.03);
    rig.body.position.set(shift * 0.025, bob - walk * 0.02, 0);
    rig.body.rotation.set(0, 0, -shift * 0.02);
    rig.hips.position.y = S.hipY - crouch;
    rig.hips.rotation.set(hipsPitch, Math.sin(this.phase * Math.PI * 2) * 0.08 * walk, 0);
    const swayRoll = Math.sin(this.phase * Math.PI * 2) * 0.05 * walk;
    rig.torso.rotation.set(
      lean + breath * 0.012 + walk * 0.05,
      twist + this.yaw * 0.18 - Math.sin(this.phase * Math.PI * 2) * 0.1 * walk,
      roll + swayRoll + shift * 0.03,
      "YXZ",
    );
    const bs = 1 + breath * 0.012;
    rig.torso.scale.set(1 + breath * 0.006, bs, 1 + breath * 0.008);
    const nb = (rig.neck.userData.base ??= rig.neck.rotation.clone()) as THREE.Euler;
    // (The stoop's tilt taken back out of the head, so they still look ahead.)
    const level = -(lean + hipsPitch) * (S.quad ? 0.5 : 0.75);
    rig.neck.rotation.set(
      nb.x + this.pitch * -0.35 + head[0] * 0.4 + level * 0.5,
      nb.y + this.yaw * 0.32 + head[1] * 0.4,
      nb.z + head[2] * 0.4,
      "YXZ",
    );
    const hb = (rig.head.userData.base ??= rig.head.rotation.clone()) as THREE.Euler;
    rig.head.rotation.set(
      hb.x - this.pitch * 0.55 + head[0] * 0.6 + level * 0.5 + Math.sin(t * 0.37) * 0.02,
      hb.y + this.yaw * 0.5 + head[1] * 0.6,
      hb.z + head[2] * 0.6,
      "YXZ",
    );

    // --- Face: blinks, lids, brows, the jaw, the eyes looking.
    this.blinkIn -= dt;
    if (this.blinkIn <= 0 && this.blink <= 0) {
      this.blink = 0.13;
      this.blinkIn = S.blinkEvery * (0.4 + this.rand() * 1.1);
      // (Sometimes a double blink.)
      if (this.rand() < 0.2) this.blinkIn = 0.25;
    }
    let bl = 0;
    if (this.blink > 0) {
      this.blink -= dt;
      bl = Math.sin(Math.max(0, this.blink / 0.13) * Math.PI);
    }
    const f = rig.face;
    const lid = Math.max(lids * (1 - wide), bl);
    for (const e of f.eyes) {
      // (Glowing eyes with no lids squash shut instead.)
      if (e.lid.userData.squash) e.lid.scale.y = Math.max(0.06, 1 - Math.min(1, lid));
      else e.lid.rotation.x = f.lidOpen + (f.lidClosed - f.lidOpen) * Math.min(1, lid);
      const ws = 1 + wide * 0.15;
      e.group.scale.setScalar(ws);
      e.look.rotation.set(
        -(this.eyePitch - this.pitch) * 0.6 + 0.02,
        (this.eyeYaw - this.yaw) * 0.5 + this.yaw * 0.12,
        0,
      );
    }
    f.brows.forEach((b, i) => {
      const base = (b.userData.base ??= { y: b.position.y, z: b.rotation.z }) as {
        y: number;
        z: number;
      };
      const side = f.eyes[i]?.side ?? (i === 0 ? 1 : -1);
      b.position.y = base.y + brow * 0.025 + wide * 0.02;
      b.rotation.z = base.z - side * brow * 0.3;
    });
    if (f.jaw) f.jaw.rotation.x = Math.max(0, Math.min(1, jaw)) * f.jawOpen;

    // --- Tail and wiggles.
    rig.tail.forEach((j, k) => {
      const b = (j.userData.base ??= j.rotation.clone()) as THREE.Euler;
      j.rotation.set(
        b.x + Math.sin(t * 1.1 - k * 0.6) * 0.03 - crouch * 0.6 * (k === 0 ? 1 : 0),
        b.y +
          Math.sin(t * 1.3 - k * 0.8) * (0.07 + 0.03 * k) +
          Math.sin(this.phase * Math.PI * 2 - k) * 0.12 * walk,
        b.z,
      );
    });
    for (const wg of rig.wiggles) {
      const b = (wg.obj.userData.base ??= wg.obj.rotation.clone()) as THREE.Euler;
      const k = wg.amount;
      wg.obj.rotation.set(
        b.x +
          Math.sin(t * 2.1 + wg.side) * 0.04 * k +
          walk * Math.sin(this.phase * Math.PI * 4) * 0.05 * k,
        b.y,
        b.z + Math.sin(t * 1.7 + wg.side * 2) * 0.05 * k,
      );
    }

    rig.root.updateMatrixWorld(true);

    // Where things are now (for next frame's gestures).
    const m = this.ctx;
    rig.torso.worldToLocal(rig.head.localToWorld(m.mouth.set(...S.mouth)));
    m.chin.copy(m.mouth).add(tA.set(0, -0.08, -0.02));

    // --- Legs: each foot planted or swinging, unless a gesture moves it.
    rig.root.getWorldQuaternion(tQ2);
    rig.legs.forEach((leg, i) => {
      const p = (this.phase + leg.phase) % 1;
      let z = 0;
      let y = 0;
      const L = S.stride;
      if (p < 0.5) z = L / 2 - L * (p / 0.5);
      else {
        const q = (p - 0.5) / 0.5;
        z = -L / 2 + L * sm(q);
        y = Math.sin(q * Math.PI) * S.lift;
      }
      const tgt: V3 = [leg.rest.x + shift * 0.01, leg.rest.y + y * walk, leg.rest.z + z * walk];
      const off = feet.get(i);
      const fin = off ? add3(tgt, off) : tgt;
      const ankle = (leg.hand.children[0] as THREE.Object3D).position.y;
      const parent = leg.front ? rig.torso : rig.hips;
      const world = rig.root.localToWorld(tA.set(fin[0], fin[1] + ankle, fin[2]));
      const wrist = reach(leg, parent, world);
      leg.hand.position.copy(rig.root.worldToLocal(tB.copy(wrist))).add(tA.set(0, -ankle, 0));
      // The foot stays flat (toes down a little as it swings through).
      const toe = p >= 0.5 ? Math.sin(((p - 0.5) / 0.5) * Math.PI) * 0.35 * walk : 0;
      leg.hand.rotation.set(toe - (off ? off[1] * 0.8 : 0), 0, 0);
    });

    // --- Arms: hanging (swinging as they walk), or posed by a gesture.
    rig.arms.forEach((arm, i) => {
      const side = arm.side;
      const swing = Math.sin((this.phase + (side > 0 ? 0.5 : 0)) * Math.PI * 2) * 0.13 * walk;
      const hr = side > 0 && S.handRestL ? S.handRestL : S.handRest;
      const rest: V3 = [
        hr[0] * side,
        hr[1] + breath * 0.008 + Math.abs(swing) * 0.15,
        hr[2] + swing,
      ];
      const target = hands[i] ? lerp3(rest, hands[i]!, handW[i]!) : rest;
      const world = rig.torso.localToWorld(tA.set(...target));
      const wrist = reach(arm, rig.torso, world);
      arm.hand.position.copy(rig.root.worldToLocal(tB.copy(wrist)));
      // The hand follows the forearm, turned as the gesture wants.
      arm.fore.getWorldQuaternion(tQ);
      tQ.premultiply(tQ2.clone().invert());
      const r = handRot[i]!;
      tE.set(r[0], r[1] * side, r[2], "XYZ");
      arm.hand.quaternion.copy(tQ).multiply(tQ.clone().setFromEuler(tE));
    });

    // --- Props: at rest where they hang, or held.
    rig.torso.updateMatrixWorld();
    const toRoot = tM.copy(rig.root.matrixWorld).invert().multiply(rig.torso.matrixWorld);
    for (const [name, prop] of Object.entries(rig.props)) {
      const got = props.get(name);
      const rest = compose(prop.restAt, prop.restRot).premultiply(toRoot);
      // A broken horn's halves hang apart at the hip.
      if (this.hornBroken && (name === "hornA" || name === "hornB")) {
        const k = name === "hornA" ? 1 : -1;
        rest.multiply(compose([k * 0.035, -0.05, 0], [0, 0, k * 0.55]));
      }
      let held: THREE.Matrix4 | null = null;
      let w = 0;
      const always = prop.obj.userData.alwaysHeld as { hand: 0 | 1; at: V3; rot: V3 } | undefined;
      if (always && !(got && !("hand" in got.pose))) {
        // A staff: always in its hand, upright in the world; a pose only tips it.
        const hand = rig.arms[always.hand]?.hand;
        if (hand) {
          const r = got?.pose.rot ?? [0, 0, 0];
          const k = got?.w ?? 0;
          const at = add3(v3(hand.position), always.at);
          // (Its foot rests on the ground: it slides up through his hand.)
          const foot = (prop.obj.userData.foot as number | undefined) ?? 0;
          if (foot && at[1] - foot < 0) at[1] = foot;
          held = compose(at, add3(always.rot, r, k));
          w = 1;
        }
      } else if (always && got && !("hand" in got.pose)) {
        // Put down (leaning on him): from his hand to where the pose leaves it.
        const hand = rig.arms[always.hand]?.hand;
        const pp = got.pose;
        if (hand) {
          const inHand = compose(add3(v3(hand.position), always.at), always.rot);
          const put = compose(pp.at, pp.rot).premultiply(toRoot);
          inHand.decompose(prop.obj.position, prop.obj.quaternion, tA);
          put.decompose(tB, tQ, tA);
          prop.obj.position.lerp(tB, Math.min(1, got.w));
          prop.obj.quaternion.slerp(tQ, Math.min(1, got.w));
          continue;
        }
      } else if (got) {
        w = Math.min(1, got.w);
        const pp = got.pose;
        if ("hand" in pp) {
          const hand = rig.arms[pp.hand]?.hand;
          if (hand) {
            hand.updateMatrix();
            const inHand = (prop.obj.userData.inHand as { at: V3; rot: V3 } | undefined) ?? {
              at: [0, 0, 0] as V3,
              rot: [0, 0, 0] as V3,
            };
            held = hand.matrix.clone().multiply(compose(pp.at ?? inHand.at, pp.rot ?? inHand.rot));
            // (A ring of keys dangles straight down from the hand.)
            if (prop.obj.userData.dangle) {
              held.decompose(tB, tQ, tA);
              held = compose(v3(tB), [0, 0, 0]);
            }
          }
        } else held = compose(pp.at, pp.rot).premultiply(toRoot);
      }
      rest.decompose(prop.obj.position, prop.obj.quaternion, tA);
      if (held && w > 0) {
        held.decompose(tB, tQ, tA);
        prop.obj.position.lerp(tB, w);
        prop.obj.quaternion.slerp(tQ, w);
      }
    }
  }
}
