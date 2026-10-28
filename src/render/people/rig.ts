/**
 * The people's rig: everyone who walks about on foot in the cutscenes and the villages
 * (Elder Mossback, Lumen in his robe, the smugglers' guards, the townsfolk), built from
 * the racers' kit (lofts, Gouraud skin, cartoon eyes with lids, two-bone arms) so they
 * stand next to the racers at the same finish.
 *
 *   root (on the ground, facing +Z)
 *     body (bobs and sways with the step)
 *       hips (crouches, pitches for a bow)
 *         torso (leans, twists): body, clothes, shoulders, arms (posed by IK)
 *           neck -> head: skull, eyes, brows, jaw (talks), hat
 *         legs: thigh and shin (posed by IK to the feet)
 *         tail: a chain of joints that sways
 *     hands, feet, props: placed every frame in root space
 *
 * Quadrupeds hang their front legs off the torso (they have no arms). Every mesh uses
 * the racers' skin material, so a whole person bakes down to a few meshes for crowds.
 */
import * as THREE from "three";
import { Build, ellipsoid, loft, type ColorLike, type V3 } from "../racers/kit/shapes";
import { skinMaterial } from "../racers/kit/paint";
import { handGeometry, type ArmRig, type FaceRig, type Wiggle } from "../racers/kit/rig";

export type { V3 };

/** A leg: the arm rig's two bones, the foot as its "hand". */
export interface LegRig extends ArmRig {
  /** Where the foot rests, in root space (under the hip). */
  rest: THREE.Vector3;
  /** A front leg of a four-legged kind (hangs off the torso). */
  front: boolean;
  /** Its step's phase offset (0..1). */
  phase: number;
}

/** A thing carried (a staff, the horn, a key ring), placed by the animator each frame. */
export interface Prop {
  obj: THREE.Object3D;
  /** Where it hangs at rest, in torso space (position, rotation XYZ). */
  restAt: V3;
  restRot: V3;
}

/** How a person stands and moves (the animator reads it). */
export interface Stance {
  /** Four-legged. */
  quad: boolean;
  /** Hip joint height (m, at scale 1) and leg bone lengths. */
  hipY: number;
  /** The step: stride (m) at a walk, and how high a foot lifts. */
  stride: number;
  lift: number;
  /** Resting stoop (torso pitch forward, radians) and head pitch to compensate. */
  stoop: number;
  /** Hands at rest, torso space (left; mirrored for the right). */
  handRest: V3;
  /** The left hand's own rest (a staff in it), if not the mirror of the right's. */
  handRestL?: V3;
  /** Where the mouth is, in head space (the horn goes there), and the chin. */
  mouth: V3;
  /** Breathing depth and idle sway (0..1). */
  breath: number;
  sway: number;
  /** Blink timing. */
  blinkEvery: number;
  /** Seconds between idle glances about (a shifty one darts his eyes). */
  glance: number;
  /** Curious head tilts (0..1). */
  curious: number;
  /** Resting face: jaw open, lids, brow. */
  restJaw: number;
  restLids: number;
  restBrow: number;
  /** How fast poses change (1 = normal; an old elder is slower). */
  response: number;
  /** How far the head turns to look (1 = normal). */
  lookReach: number;
}

export interface PersonRig {
  root: THREE.Group;
  body: THREE.Group;
  hips: THREE.Group;
  torso: THREE.Group;
  neck: THREE.Group;
  head: THREE.Group;
  face: FaceRig;
  arms: ArmRig[];
  legs: LegRig[];
  tail: THREE.Object3D[];
  hands: THREE.Group;
  feet: THREE.Group;
  props: Record<string, Prop>;
  wiggles: Wiggle[];
  stance: Stance;
  /** Glowing bits (Lumen's eyes) the crowd version keeps as they are. */
  glow: THREE.Object3D[];
}

export const DEFAULT_STANCE: Stance = {
  quad: false,
  hipY: 0.62,
  stride: 0.42,
  lift: 0.12,
  stoop: 0,
  handRest: [0.3, -0.05, 0.06],
  mouth: [0, 0.05, 0.32],
  breath: 1,
  sway: 1,
  blinkEvery: 3.4,
  glance: 4,
  curious: 0,
  restJaw: 0.08,
  restLids: 0.08,
  restBrow: 0,
  response: 1,
  lookReach: 1,
};

/** One mesh in the shared skin material. */
export const mesh = (b: Build) => new THREE.Mesh(b.build(), skinMaterial());

/**
 * A limb bone along +Z from its joint: rounded at both ends, its colour by how far along
 * it is (`color(t)`: a sleeve that ends, a cuff, a boot top).
 */
export function limb(
  len: number,
  r0: number,
  r1: number,
  color: ColorLike | ((t: number, a: number) => ColorLike),
  opts: { bulge?: number; sides?: number } = {},
) {
  const c = typeof color === "function" ? undefined : color;
  const mid = (r0 + r1) / 2 + (opts.bulge ?? 0);
  return new Build().addColored(
    loft(
      [
        { at: [0, 0, -r0 * 0.75], rx: r0 * 0.55, ry: r0 * 0.55, color: c },
        { at: [0, 0, -r0 * 0.2], rx: r0 * 0.95, ry: r0 * 0.95, color: c },
        { at: [0, 0, len * 0.38], rx: mid, ry: mid, color: c },
        { at: [0, 0, len * 0.8], rx: (mid + r1) / 2, ry: (mid + r1) / 2, color: c },
        { at: [0, 0, len + r1 * 0.15], rx: r1, ry: r1, color: c },
        { at: [0, 0, len + r1 * 0.7], rx: r1 * 0.55, ry: r1 * 0.55, color: c },
      ],
      {
        sides: opts.sides ?? 9,
        steps: 2,
        capStart: true,
        capEnd: true,
        paint:
          typeof color === "function"
            ? (t, a) => color(Math.max(0, Math.min(1, (t * 1.15 - 0.05) * 1)), a)
            : undefined,
      },
    ),
  );
}

export interface FootStyle {
  len: number;
  width: number;
  color: ColorLike;
  /** Toe claws (or none: a boot, a padded foot). */
  claw?: string;
  /** Three toes (a dinosaur's foot) or one rounded front (a boot, an elephant pad). */
  toes?: boolean;
  /** A wrapped boot: its colour and cuff. */
  boot?: { color: string; cuff: string };
  /** A pale sole. */
  sole?: string;
}

/** A foot, the ankle at the origin, toes along +Z, sitting on y = -ankleH. */
export function footGeometry(s: FootStyle, ankleH: number) {
  const b = new Build();
  const L = s.len;
  const W = s.width;
  const base = s.boot?.color ?? s.color;
  // The heel and instep, down to a flat sole on the ground (y = -ankleH).
  const sec = (z: number, rx: number, r: number, f = 0.85) => ({
    at: [0, -ankleH + r * (1 - f), z] as V3,
    rx,
    ry: r,
    color: base,
    flat: f,
  });
  b.addColored(
    loft(
      [
        sec(-L * 0.24, W * 0.36, ankleH * 0.55),
        sec(-L * 0.12, W * 0.46, ankleH * 0.8),
        sec(L * 0.1, W * 0.5, ankleH * 0.62),
        sec(L * 0.32, W * 0.48, ankleH * 0.42),
        sec(L * 0.48, W * 0.36, ankleH * 0.3),
        sec(L * 0.56, W * 0.18, ankleH * 0.16),
      ],
      {
        sides: 10,
        steps: 2,
        capStart: true,
        capEnd: true,
        paint: s.sole ? (_t, a) => (a < -1.2 ? s.sole! : base) : undefined,
      },
    ),
  );
  if (s.boot)
    b.add(ellipsoid(10, 5), s.boot.cuff, {
      p: [0, 0, -L * 0.08],
      s: [W * 0.5, ankleH * 0.38, W * 0.5],
    });
  if (s.toes !== false && !s.boot) {
    // Three stubby toes, splayed, each with a claw.
    for (const k of [-1, 0, 1]) {
      const ang = k * 0.32;
      const tx = Math.sin(ang) * L * 0.4;
      const tz = L * 0.36 + Math.cos(ang) * L * 0.2;
      const th = ankleH * 0.3;
      b.add(ellipsoid(9, 6), s.color, {
        p: [tx, -ankleH + th * 0.85, tz],
        s: [W * 0.17, th, L * 0.21],
        r: [0, ang, 0],
      });
      if (s.claw)
        b.add(new THREE.ConeGeometry(W * 0.07, L * 0.13, 6), s.claw, {
          p: [tx + Math.sin(ang) * L * 0.2, -ankleH + th * 0.55, tz + Math.cos(ang) * L * 0.2],
          r: [Math.PI / 2 + 0.25, 0, -ang],
          s: [1, 1, 0.65],
        });
    }
  }
  return b.build();
}

/** A tail: a chain of tapering joints from `at` (hips space) back along -Z. */
export function buildTail(
  hips: THREE.Object3D,
  at: V3,
  segs: [number, number, number][],
  lift: number[],
  paint: (seg: number, t: number, a: number) => ColorLike,
) {
  const out: THREE.Object3D[] = [];
  let parent: THREE.Object3D = hips;
  segs.forEach(([r0, len, r1], k) => {
    const j = new THREE.Group();
    if (k === 0) j.position.set(...at);
    else j.position.set(0, 0, -segs[k - 1]![1]);
    j.rotation.x = lift[k] ?? 0;
    parent.add(j);
    j.add(
      mesh(
        new Build().addColored(
          loft(
            [
              { at: [0, 0, r0 * 0.6], rx: r0 * 0.7, ry: r0 * 0.7 },
              { at: [0, 0, 0], rx: r0, ry: r0 },
              { at: [0, 0, -len * 0.5], rx: (r0 + r1) / 2, ry: (r0 + r1) / 2 },
              { at: [0, 0, -len], rx: r1, ry: r1 },
              { at: [0, 0, -len - r1 * 0.7], rx: r1 * 0.5, ry: r1 * 0.5 },
            ],
            {
              sides: 9,
              steps: 2,
              capStart: true,
              capEnd: true,
              paint: (t, a) => paint(k, t, a),
            },
          ),
        ),
      ),
    );
    out.push(j);
    parent = j;
  });
  return out;
}

export interface ArmSpec {
  /** Left shoulder, torso space. */
  shoulder: V3;
  upper: number;
  fore: number;
  radius: [number, number, number];
  /** Colour along the arm (0 shoulder .. 1 wrist), or one colour. */
  upperColor: ColorLike | ((t: number, a: number) => ColorLike);
  foreColor: ColorLike | ((t: number, a: number) => ColorLike);
  hand: string;
  handSize: number;
  claws?: string;
  /** Elbow direction, torso space (left side). */
  hint?: V3;
}

export interface LegSpec {
  /** Left hip, hips space (front legs of a quadruped: torso space). */
  hip: V3;
  thigh: number;
  shin: number;
  radius: [number, number, number];
  thighColor: ColorLike | ((t: number, a: number) => ColorLike);
  shinColor: ColorLike | ((t: number, a: number) => ColorLike);
  foot: FootStyle;
  /** Ankle height over the ground. */
  ankleH: number;
  /** Knee direction (hips space, left side): forward for a biped. */
  hint?: V3;
}

/**
 * The skeleton: root, body, hips (at `hipY`), torso, neck and head groups, two arms and
 * two (or four) legs built from the specs. The character adds its own shapes to the
 * groups after.
 */
export function skeleton(o: {
  name: string;
  stance: Partial<Stance>;
  /** Torso pivot (hips space), neck base (torso space), head pivot (neck space). */
  torsoAt?: V3;
  neckAt: V3;
  headAt: V3;
  arms?: ArmSpec;
  legs: LegSpec;
  /** A quadruped's front legs (torso space). */
  frontLegs?: LegSpec;
}): PersonRig {
  const stance: Stance = { ...DEFAULT_STANCE, ...o.stance };
  const root = new THREE.Group();
  root.name = o.name;
  const body = new THREE.Group();
  root.add(body);
  const hips = new THREE.Group();
  hips.position.y = stance.hipY;
  body.add(hips);
  const torso = new THREE.Group();
  if (o.torsoAt) torso.position.set(...o.torsoAt);
  hips.add(torso);
  const neck = new THREE.Group();
  neck.position.set(...o.neckAt);
  torso.add(neck);
  const head = new THREE.Group();
  head.position.set(...o.headAt);
  neck.add(head);
  const hands = new THREE.Group();
  hands.name = "hands";
  const feet = new THREE.Group();
  feet.name = "feet";
  root.add(hands, feet);

  const arms: ArmRig[] = [];
  if (o.arms) {
    const s = o.arms;
    for (const side of [1, -1]) {
      const upper = mesh(limb(s.upper, s.radius[0], s.radius[1], s.upperColor));
      const fore = mesh(limb(s.fore, s.radius[1], s.radius[2], s.foreColor));
      torso.add(upper, fore);
      const hand = new THREE.Group();
      hand.add(new THREE.Mesh(handGeometry(s.hand, s.handSize, side, s.claws), skinMaterial()));
      hands.add(hand);
      const hint = new THREE.Vector3(...(s.hint ?? [0.7, -0.5, -0.5]));
      hint.x *= side;
      arms.push({
        shoulder: new THREE.Vector3(s.shoulder[0] * side, s.shoulder[1], s.shoulder[2]),
        upper,
        fore,
        hand,
        a: s.upper,
        b: s.fore,
        hint: hint.normalize(),
        side,
      });
    }
  }

  const legs: LegRig[] = [];
  const makeLegs = (s: LegSpec, parent: THREE.Object3D, front: boolean, quad: boolean) => {
    for (const side of [1, -1]) {
      const upper = mesh(limb(s.thigh, s.radius[0], s.radius[1], s.thighColor, { bulge: 0.012 }));
      const fore = mesh(limb(s.shin, s.radius[1], s.radius[2], s.shinColor));
      // (Legs point down: keep their twist steady.)
      upper.up.set(0, 0, 1);
      fore.up.set(0, 0, 1);
      parent.add(upper, fore);
      const foot = new THREE.Group();
      const fm = new THREE.Mesh(footGeometry(s.foot, s.ankleH), skinMaterial());
      fm.position.y = s.ankleH;
      foot.add(fm);
      feet.add(foot);
      const hint = new THREE.Vector3(...(s.hint ?? [0.12, 0, 1]));
      hint.x *= side;
      // Where the foot rests: under the hip (on the ground).
      const hipLocal = new THREE.Vector3(s.hip[0] * side, s.hip[1], s.hip[2]);
      const restZ = front ? (o.torsoAt?.[2] ?? 0) + s.hip[2] : s.hip[2] + (quad ? 0 : 0.02);
      legs.push({
        shoulder: hipLocal,
        upper,
        fore,
        hand: foot,
        a: s.thigh,
        b: s.shin,
        hint: hint.normalize(),
        side,
        rest: new THREE.Vector3(s.hip[0] * side * 1.02, 0, restZ),
        front,
        // Bipeds: opposite feet. Quadrupeds: the diagonal pairs together.
        phase: quad ? (front ? (side > 0 ? 0 : 0.5) : side > 0 ? 0.5 : 0) : side > 0 ? 0 : 0.5,
      });
    }
  };
  makeLegs(o.legs, hips, false, !!o.frontLegs);
  if (o.frontLegs) makeLegs(o.frontLegs, torso, true, true);

  return {
    root,
    body,
    hips,
    torso,
    neck,
    head,
    face: { eyes: [], brows: [], jaw: null, jawOpen: 0.4, lidOpen: -1.6, lidClosed: 1.45 },
    arms,
    legs,
    tail: [],
    hands,
    feet,
    props: {},
    wiggles: [],
    stance,
    glow: [],
  };
}

/** A colour a little darker (k < 1) or lighter (k > 1). */
export function shade(c: ColorLike, k: number) {
  const x = c instanceof THREE.Color ? c.clone() : new THREE.Color(c);
  if (k < 1) x.multiplyScalar(k);
  else x.lerp(new THREE.Color("#ffffff"), k - 1);
  return `#${x.getHexString()}`;
}

/** Mix two colours. */
export function mix(a: ColorLike, b: ColorLike, t: number) {
  const x = a instanceof THREE.Color ? a.clone() : new THREE.Color(a);
  return `#${x.lerp(b instanceof THREE.Color ? b : new THREE.Color(b), t).getHexString()}`;
}

/** A cheap value-noise mottle for skin (deterministic), 0..1. */
export function mottle(x: number, y: number, seed = 0) {
  return (
    0.5 +
    0.25 * Math.sin(x * 13.1 + seed * 1.7 + Math.sin(y * 7.3)) +
    0.25 * Math.sin(y * 11.7 - x * 5.3 + seed)
  );
}
