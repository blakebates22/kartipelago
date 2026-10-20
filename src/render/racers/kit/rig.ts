/**
 * The rider rig every racer is built on, and the parts that make a face and arms.
 *
 *   root (sits on the kart seat)
 *     torso (pivot at the hips): body, back gear, shoulders
 *       neck (optional, pivot at the base of the neck)
 *         head (pivot where it joins the neck): skull, crest, horns, eyes, brows
 *           jaw (pivot at the hinge): the lower jaw, opens to smile, shout and gasp
 *     arms: upper arm and forearm, posed each frame by two-bone IK
 *   hands: on the kart body, on the steering wheel (or raised to celebrate)
 *   tail: a chain of joints that sways and trails
 *   wings (optional): fold, spread and flap
 *
 * The animator (animator.ts) drives every rig the same way; each racer's personality
 * (timings, how far they lean, how they celebrate) makes the motion theirs.
 */
import * as THREE from "three";
import { Build, ellipsoid, loft, type ColorLike, type V3 } from "./shapes";
import { skinMaterial } from "./paint";

export interface Eye {
  group: THREE.Group;
  /** The upper lid: rotates down over the eye to blink. */
  lid: THREE.Object3D;
  /** Pupil and highlight: turn a little to look about. */
  look: THREE.Object3D;
  side: number;
}

export interface FaceRig {
  eyes: Eye[];
  brows: THREE.Object3D[];
  jaw: THREE.Object3D | null;
  /** Jaw rotation (radians) at "fully open". */
  jawOpen: number;
  /** The lids' rotation when open and when closed. */
  lidOpen: number;
  lidClosed: number;
}

export interface ArmRig {
  /** Shoulder, in torso space. */
  shoulder: THREE.Vector3;
  upper: THREE.Object3D;
  fore: THREE.Object3D;
  hand: THREE.Object3D;
  /** Bone lengths (rig units). */
  a: number;
  b: number;
  /** Which way the elbow points, in torso space (out and down, usually). */
  hint: THREE.Vector3;
  side: number;
}

/** How a racer moves: the same animator, their own timing and style. */
export interface Personality {
  /** Lean into turns and drifts (1 = normal). */
  lean: number;
  /** How much the head turns into corners. */
  headTurn: number;
  /** Curious head tilts and looks around (0..1). */
  curiosity: number;
  /** Seconds between glances at a nearby rival, roughly. */
  glanceEvery: number;
  /** Seconds between blinks, and how long a blink takes. */
  blinkEvery: number;
  blinkTime: number;
  /** Idle bob: height and speed. */
  bob: number;
  bobHz: number;
  /** How much the hands work the wheel (1 = normal). */
  steerHands: number;
  /** How hard a boost throws them back, and how wide the eyes and mouth go. */
  boostKick: number;
  boostFace: number;
  /** Head shake after a hard bump (frustration), 0..1. */
  grumble: number;
  /** How quickly poses change (1 = normal; lower is more relaxed). */
  response: number;
  /** Resting expression: how open the mouth is (0..1) and the brow (-1 cross .. 1 up). */
  restJaw: number;
  restBrow: number;
  /** Lids at rest (0 wide open .. 1 closed): a calm racer looks a little sleepy. */
  restLids: number;
  /** Victory celebration style. */
  victory: "cheer" | "nod" | "wave" | "flap";
}

export type WiggleKind =
  /** Lags behind the head's motion and bobs (crests, frills, ears). */
  | "crest"
  /** Flaps with speed (scarves, neckerchiefs, straps). */
  | "flutter"
  /** Bounces on bumps and landings (backpacks, bedrolls, gear). */
  | "bounce"
  /** Leaves and plumes: a gentle sway. */
  | "sway";

export interface Wiggle {
  obj: THREE.Object3D;
  kind: WiggleKind;
  side: number;
  amount: number;
}

export interface RiderRig {
  root: THREE.Group;
  torso: THREE.Group;
  neck: THREE.Group | null;
  head: THREE.Group;
  face: FaceRig;
  arms: [ArmRig, ArmRig];
  /** Hand meshes (they live on the kart body, the animator places them). */
  hands: THREE.Group;
  tail: THREE.Object3D[];
  /** Left then right wing, if any (each rotates to fold and spread). */
  wings: THREE.Object3D[];
  wiggles: Wiggle[];
  /** One cheap mesh for far away. */
  low: THREE.Mesh;
  personality: Personality;
  /** Where the hands go to celebrate, in torso space (left, right). */
  cheer: [THREE.Vector3, THREE.Vector3];
}

// ------------------------------------------------------------------ eyes

export interface EyeStyle {
  /** The left eye's centre, in head space (the right one is mirrored). */
  at: V3;
  /** Half-sizes of the eyeball. */
  size: V3;
  /** Turn each eye outward (radians) and tilt it. */
  yaw?: number;
  pitch?: number;
  white?: string;
  iris: string;
  pupil?: string;
  /** Lid colour (the skin round the eye). */
  lid: string;
  /** How far the pupil sits toward the nose (0..1), a friendly look. */
  inward?: number;
  brow?: { color: string; at: V3; size: V3; tilt?: number };
}

/** Two big cartoon eyes with blinking lids, pupils that look about, and brows. */
export function buildEyes(
  head: THREE.Object3D,
  s: EyeStyle,
): Pick<FaceRig, "eyes" | "brows" | "lidOpen" | "lidClosed"> {
  const mat = skinMaterial();
  const eyes: Eye[] = [];
  const brows: THREE.Object3D[] = [];
  const [rx, ry, rz] = s.size;
  for (const side of [1, -1]) {
    const g = new THREE.Group();
    g.position.set(s.at[0] * side, s.at[1], s.at[2]);
    g.rotation.set(s.pitch ?? 0, (s.yaw ?? 0) * side, 0, "YXZ");
    // The white.
    g.add(
      new THREE.Mesh(
        new Build().add(ellipsoid(12, 9), s.white ?? "#fffdf4", { s: [rx, ry, rz] }).build(),
        mat,
      ),
    );
    // Iris and pupil on the front, with a bright highlight.
    const look = new THREE.Group();
    const inward = (s.inward ?? 0.2) * -side * rx * 0.25;
    const b = new Build()
      .add(ellipsoid(10, 7), s.iris, {
        p: [inward, -ry * 0.04, rz * 0.62],
        s: [rx * 0.62, ry * 0.7, rz * 0.42],
      })
      .add(ellipsoid(8, 6), s.pupil ?? "#120d10", {
        p: [inward, -ry * 0.04, rz * 0.8],
        s: [rx * 0.4, ry * 0.48, rz * 0.28],
      })
      .add(ellipsoid(6, 4), "#ffffff", {
        p: [inward + rx * 0.2 * side, ry * 0.26, rz * 0.98],
        s: [rx * 0.17, ry * 0.19, rz * 0.08],
      });
    look.add(new THREE.Mesh(b.build(), mat));
    g.add(look);
    // The lid: a cap over the top of the eye, rotated down to blink.
    const lid = new THREE.Group();
    const lidGeo = new THREE.SphereGeometry(1, 12, 5, 0, Math.PI * 2, 0, Math.PI / 2);
    lid.add(
      new THREE.Mesh(
        new Build().add(lidGeo, s.lid, { s: [rx * 1.07, ry * 1.07, rz * 1.07] }).build(),
        mat,
      ),
    );
    g.add(lid);
    head.add(g);
    eyes.push({ group: g, lid, look, side });
    if (s.brow) {
      const br = new THREE.Group();
      br.position.set(s.brow.at[0] * side, s.brow.at[1], s.brow.at[2]);
      br.rotation.z = (s.brow.tilt ?? 0) * side;
      br.add(
        new THREE.Mesh(
          new Build().add(ellipsoid(8, 5), s.brow.color, { s: s.brow.size }).build(),
          mat,
        ),
      );
      head.add(br);
      brows.push(br);
    }
  }
  return { eyes, brows, lidOpen: -1.6, lidClosed: 1.45 };
}

// ------------------------------------------------------------------ arms

export interface ArmStyle {
  /** Left shoulder in torso space (the right is mirrored). */
  shoulder: V3;
  upper: number;
  fore: number;
  /** Radius at the shoulder, elbow and wrist. */
  radius: [number, number, number];
  color: ColorLike;
  /** Glove or hand colour, size, and claws if any. */
  hand: string;
  handSize: number;
  claws?: string;
  /** Elbow direction in torso space (left side; mirrored for the right). */
  hint?: V3;
}

function limb(len: number, r0: number, r1: number, color: ColorLike) {
  const geo = loft(
    [
      { at: [0, 0, -r0 * 0.6], rx: r0 * 0.7, ry: r0 * 0.7, color },
      { at: [0, 0, 0], rx: r0, ry: r0, color },
      { at: [0, 0, len * 0.5], rx: (r0 + r1) * 0.5, ry: (r0 + r1) * 0.5, color },
      { at: [0, 0, len], rx: r1, ry: r1, color },
      { at: [0, 0, len + r1 * 0.6], rx: r1 * 0.6, ry: r1 * 0.6, color },
    ],
    { sides: 7, capStart: true, capEnd: true },
  );
  return new THREE.Mesh(new Build().addColored(geo).build(), skinMaterial());
}

/** A rounded mitten hand with a thumb (and claws if wanted), palm facing in. */
export function handGeometry(color: string, size: number, side: number, claws?: string) {
  const b = new Build()
    .add(ellipsoid(9, 7), color, { s: [size * 0.95, size * 0.8, size] })
    .add(ellipsoid(7, 5), color, {
      p: [-side * size * 0.75, size * 0.3, size * 0.3],
      s: [size * 0.38, size * 0.32, size * 0.45],
    });
  if (claws)
    for (const k of [-1, 0, 1])
      b.add(new THREE.ConeGeometry(size * 0.16, size * 0.42, 5), claws, {
        p: [k * size * 0.45, -size * 0.1, size * 0.95],
        r: [Math.PI / 2, 0, 0],
      });
  return b.build();
}

/** Two arms (shoulder to wrist, posed by the animator) and two hands. */
export function buildArms(
  torso: THREE.Object3D,
  s: ArmStyle,
): { arms: [ArmRig, ArmRig]; hands: THREE.Group } {
  const hands = new THREE.Group();
  hands.name = "hands";
  const out: ArmRig[] = [];
  for (const side of [1, -1]) {
    const upper = limb(s.upper, s.radius[0], s.radius[1], s.color);
    const fore = limb(s.fore, s.radius[1], s.radius[2], s.color);
    torso.add(upper, fore);
    const hand = new THREE.Mesh(handGeometry(s.hand, s.handSize, side, s.claws), skinMaterial());
    hands.add(hand);
    const hint = new THREE.Vector3(...(s.hint ?? [0.8, -0.6, -0.2]));
    hint.x *= side;
    out.push({
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
  return { arms: [out[0]!, out[1]!], hands };
}

const tS = new THREE.Vector3();
const tD = new THREE.Vector3();
const tP = new THREE.Vector3();
const tE = new THREE.Vector3();
const tH = new THREE.Vector3();

/**
 * Two-bone IK: place the upper arm and forearm so the wrist reaches `target` (world
 * space), bending the elbow toward the arm's hint. Bone lengths are in rig units (the
 * limb meshes are built along +Z from their joint).
 */
export function reach(arm: ArmRig, torso: THREE.Object3D, target: THREE.Vector3) {
  const S = torso.localToWorld(tS.copy(arm.shoulder));
  const scale = torso.getWorldScale(tP).x;
  let a = arm.a * scale;
  let b = arm.b * scale;
  tD.subVectors(target, S);
  const far = tD.length();
  // Out of reach: the arm stretches a little (cartoon arms), so the hand never leaves
  // the wheel.
  const stretch = Math.max(1, far / ((a + b) * 0.995));
  a *= stretch;
  b *= stretch;
  arm.upper.scale.set(1, 1, stretch);
  arm.fore.scale.set(1, 1, stretch);
  const d = Math.min(a + b - 1e-4, Math.max(Math.abs(a - b) + 1e-4, far));
  tD.normalize();
  // The elbow's direction: the hint, made square to the shoulder-wrist line.
  tH.copy(arm.hint).transformDirection(torso.matrixWorld);
  tH.addScaledVector(tD, -tH.dot(tD)).normalize();
  const cosA = (a * a + d * d - b * b) / (2 * a * d);
  const sinA = Math.sqrt(Math.max(0, 1 - cosA * cosA));
  tE.copy(S)
    .addScaledVector(tD, a * cosA)
    .addScaledVector(tH, a * sinA);
  const wrist = tP.copy(S).addScaledVector(tD, d);
  arm.upper.position.copy(arm.shoulder);
  arm.upper.lookAt(tE);
  arm.fore.position.copy(torso.worldToLocal(tE.clone()));
  arm.fore.lookAt(wrist);
  return wrist;
}
