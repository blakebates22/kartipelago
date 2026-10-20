/**
 * The racers' animation: a state machine read from the kart's physics state, blended
 * smoothly into a handful of pose channels, then applied to the rig.
 *
 *   physics state ──> state (IDLE, DRIFTING_LEFT, AIRBORNE...) ──> pose targets
 *        │                                                               │
 *        └──> continuous signals (steer, slip, speed) ──────────────> channels (eased)
 *                                                                        │
 *                                                       rig: torso, head, face, arms, tail
 *
 * Nothing is ever snapped: every channel eases toward its target, at a rate set by the
 * racer's personality (a calm racer moves slower; an excitable one overshoots). It's
 * all visual: the animator reads the kart state and never writes to it.
 */
import * as THREE from "three";
import type { KartModel } from "./kit/chassis";
import { reach, type RiderRig } from "./kit/rig";

/** What the animator reads from the kart each frame (all already in the kart state). */
export interface RacerMotion {
  speed: number;
  /** Smoothed stick, -1..1 (positive = right). */
  steer: number;
  driftDir: number;
  /** Nose angle minus travel angle (the kart's slip), radians. */
  slip: number;
  grounded: boolean;
  /** Throttle held. */
  throttle: boolean;
  /** Boost phase (ZIP.*) and whether it's the enhanced kind. */
  boostPhase: number;
  boostEnhanced: boolean;
  /** Boost time left: it jumps up whenever a new boost starts (we watch for that). */
  boostLeft: number;
  /** Last judged wall impact: tier and speed (watched for changes). */
  impactTier: number;
  impactSpeed: number;
  /** Spin-out time left (weapon hits and spin-outs). */
  spinTime: number;
}

export const STATES = [
  "IDLE",
  "ACCELERATING",
  "BRAKING",
  "STEERING_LEFT",
  "STEERING_RIGHT",
  "DRIFTING_LEFT",
  "DRIFTING_RIGHT",
  "BOOSTING",
  "AIRBORNE",
  "LANDING",
  "COLLISION",
  "VICTORY",
  "DEFEAT",
] as const;
export type AnimState = (typeof STATES)[number];

/** The pose channels. Each eases toward its target every frame. */
interface Channels {
  /** Torso roll into a turn (+ = lean right), forward pitch (+ = forward), twist. */
  lean: number;
  pitch: number;
  twist: number;
  headYaw: number;
  headPitch: number;
  headRoll: number;
  /** Face: mouth 0..1, lids 0 open..1 closed, wide-eyed 0..1, brow -1 cross..1 up. */
  jaw: number;
  lids: number;
  wide: number;
  brow: number;
  /** Hands off the wheel to celebrate (left, right), 0..1. */
  cheerL: number;
  cheerR: number;
  /** Wings: 0 folded, 1 spread; and how hard they flap. */
  spread: number;
  flap: number;
  /** Extra bounce in the seat. */
  bounce: number;
}

const ZERO: Channels = {
  lean: 0,
  pitch: 0,
  twist: 0,
  headYaw: 0,
  headPitch: 0,
  headRoll: 0,
  jaw: 0,
  lids: 0,
  wide: 0,
  brow: 0,
  cheerL: 0,
  cheerR: 0,
  spread: 0,
  flap: 0,
  bounce: 0,
};

/** How fast each channel follows its target (per second), before personality. */
const RATE: Record<keyof Channels, number> = {
  lean: 8,
  pitch: 7,
  twist: 6,
  headYaw: 6,
  headPitch: 8,
  headRoll: 6,
  jaw: 12,
  lids: 14,
  wide: 10,
  brow: 9,
  cheerL: 5,
  cheerR: 5,
  spread: 6,
  flap: 5,
  bounce: 6,
};

const ease = (v: number, target: number, rate: number, dt: number) =>
  v + (target - v) * (1 - Math.exp(-rate * dt));

function rng(seed: number) {
  let a = seed >>> 0 || 1;
  return () => {
    a ^= a << 13;
    a ^= a >>> 17;
    a ^= a << 5;
    return ((a >>> 0) % 10000) / 10000;
  };
}

const tmpA = new THREE.Vector3();
const tmpB = new THREE.Vector3();
const tmpQ = new THREE.Quaternion();
const tmpQ2 = new THREE.Quaternion();
const tmpM = new THREE.Matrix4();

export class Animator {
  state: AnimState = "IDLE";
  /** Seconds in the current state. */
  stateTime = 0;
  readonly c: Channels = { ...ZERO };
  private t = 0;
  private rand: () => number;
  // Events and springs.
  private lastSpeed = 0;
  private accel = 0;
  private kick = 0;
  private kickV = 0;
  private squash = 1;
  private squashV = 0;
  private airTime = 0;
  private wasGrounded = true;
  private landing = 0;
  private hit = 0;
  private hitHard = 0;
  private lastBoostLeft = 0;
  private lastImpact = { tier: 0, speed: 0 };
  private lastSpin = 0;
  private blinkIn: number;
  private blink = 0;
  private glanceIn: number;
  private glance = 0;
  private glanceYaw = 0;
  private tiltIn: number;
  private tilt = 0;
  private tiltDir = 1;
  private wheelSpin = 0;
  private result: { place: number; of: number } | null = null;
  /** A shake from a hazard reaction, seconds left. */
  private jolt = 0;
  private surprise = 0;

  constructor(
    readonly rig: RiderRig,
    seed = 7,
  ) {
    this.rand = rng(seed);
    this.blinkIn = 1 + this.rand() * 2;
    this.glanceIn = 2 + this.rand() * 3;
    this.tiltIn = 2 + this.rand() * 3;
  }

  /** The race is over for this racer: celebrate a podium, slump otherwise. */
  setResult(place: number | null, of = 8) {
    this.result = place === null ? null : { place, of };
  }

  /** A hazard reaction: a yelp and a jolt (burn) or a big-eyed bob (splash). */
  react(kind: "burn" | "splash") {
    this.surprise = 1;
    this.hit = 0.7;
    if (kind === "burn") {
      this.squashV -= 4;
      this.jolt = 0.6;
      this.hitHard = 1;
    } else {
      this.squashV -= 2;
      this.hitHard = 0.4;
    }
  }

  /** Decide the state from the kart's motion (and the race result). */
  private classify(m: RacerMotion): AnimState {
    if (this.result)
      return this.result.place <= Math.max(1, Math.round(this.result.of * 0.375))
        ? "VICTORY"
        : "DEFEAT";
    if (this.hit > 0) return "COLLISION";
    if (!m.grounded && this.airTime > 0.1) return "AIRBORNE";
    if (this.landing > 0) return "LANDING";
    if (m.boostPhase === 1 || m.boostPhase === 2) return "BOOSTING";
    if (m.driftDir < 0) return "DRIFTING_LEFT";
    if (m.driftDir > 0) return "DRIFTING_RIGHT";
    const speed = Math.abs(m.speed);
    if (speed < 0.5 && !m.throttle) return "IDLE";
    if (m.steer < -0.3 && speed > 2) return "STEERING_LEFT";
    if (m.steer > 0.3 && speed > 2) return "STEERING_RIGHT";
    if (this.accel < -5 && speed > 2) return "BRAKING";
    return "ACCELERATING";
  }

  /** One rendered frame. `rival`: the nearest other racer in this kart's frame (x across, z ahead). */
  step(dt: number, m: RacerMotion, kart: KartModel, rival: { x: number; z: number } | null) {
    dt = Math.min(dt, 0.1);
    if (dt <= 0) return;
    this.t += dt;
    const rig = this.rig;
    const p = rig.personality;
    const speed = Math.abs(m.speed);
    const moving = Math.min(1, speed / 8);
    const fast = Math.min(1, speed / 30);

    // Wheels spin with speed; the front ones steer.
    this.wheelSpin += (m.speed * dt) / 0.4;
    for (const w of kart.wheels) {
      w.tyre.rotation.x = this.wheelSpin * (0.4 / w.radius);
      if (w.front) w.pivot.rotation.y = -m.steer * 0.45;
    }

    // --- Events, read from changes in the kart's state.
    this.accel = ease(this.accel, (m.speed - this.lastSpeed) / dt, 8, dt);
    this.lastSpeed = m.speed;
    const boosting = m.boostPhase === 1 || m.boostPhase === 2;
    if (boosting && m.boostLeft > this.lastBoostLeft + 0.02) {
      this.kickV += (m.boostEnhanced ? 7 : 5) * p.boostKick;
      this.surprise = Math.max(this.surprise, 0.25 * p.boostKick);
    }
    this.lastBoostLeft = boosting ? m.boostLeft : 0;
    if (
      m.impactTier > 0 &&
      (m.impactTier !== this.lastImpact.tier || m.impactSpeed !== this.lastImpact.speed)
    ) {
      const hard = m.impactTier >= 3 ? 1 : m.impactTier === 2 ? 0.6 : 0.25;
      this.squashV -= 3 * hard;
      if (hard >= 0.5) {
        this.hit = 0.45 + 0.4 * hard;
        this.hitHard = hard;
      }
    }
    this.lastImpact = { tier: m.impactTier, speed: m.impactSpeed };
    if (m.spinTime > this.lastSpin + 0.05) {
      this.squashV -= 3.5;
      this.hit = 1;
      this.hitHard = 1;
    }
    this.lastSpin = m.spinTime;
    if (this.wasGrounded && !m.grounded) {
      this.squashV -= 1.2;
      this.airTime = 0;
    }
    if (!m.grounded) this.airTime += dt;
    if (!this.wasGrounded && m.grounded && this.airTime > 0.15) {
      this.squashV -= 2 + Math.min(3, this.airTime * 3);
      this.landing = 0.35;
    }
    this.wasGrounded = m.grounded;
    this.hit = Math.max(0, this.hit - dt);
    this.landing = Math.max(0, this.landing - dt);
    this.jolt = Math.max(0, this.jolt - dt);
    this.surprise = Math.max(0, this.surprise - dt);

    // Springs, in small slices so a slow frame can't blow them up.
    const squashTarget = !m.grounded && this.airTime > 0.08 ? 1.06 : 1;
    const slices = Math.ceil(dt / (1 / 120));
    const h = dt / slices;
    for (let i = 0; i < slices; i++) {
      this.squashV += (-(this.squash - squashTarget) * 180 - this.squashV * 14) * h;
      this.squash += this.squashV * h;
      this.kickV += (-this.kick * 60 - this.kickV * 9) * h;
      this.kick += this.kickV * h;
    }

    // --- The state, and its pose.
    const state = this.classify(m);
    if (state !== this.state) {
      this.state = state;
      this.stateTime = 0;
    } else this.stateTime += dt;
    const T: Channels = {
      ...ZERO,
      jaw: p.restJaw,
      lids: p.restLids,
      brow: p.restBrow,
    };
    const drifting = m.driftDir !== 0;
    // Continuous: lean into the turn, harder in a drift; head into the corner.
    T.lean = (m.steer * 0.1 * moving + (drifting ? m.driftDir * 0.17 : 0)) * p.lean;
    T.headYaw = (-m.slip * 0.4 - m.steer * 0.2) * moving * p.headTurn;
    T.headRoll = -T.lean * 0.25;
    T.twist = drifting ? -m.driftDir * 0.08 * p.lean : 0;
    const st = this.stateTime;
    switch (state) {
      case "IDLE":
        T.bounce = 1;
        // Look around while waiting; curious racers tilt their heads.
        T.headYaw = Math.sin(this.t * (0.5 + p.curiosity * 0.6)) * (0.25 + 0.3 * p.curiosity);
        T.headPitch = Math.sin(this.t * 0.37) * 0.06;
        break;
      case "ACCELERATING":
        T.pitch = 0.06 + fast * 0.06;
        T.brow = p.restBrow - 0.2;
        break;
      case "BRAKING":
        T.pitch = 0.2;
        T.headPitch = -0.12;
        T.wide = 0.35;
        T.jaw = 0.3;
        break;
      case "STEERING_LEFT":
      case "STEERING_RIGHT":
        T.pitch = 0.05;
        T.brow = p.restBrow - 0.25;
        break;
      case "DRIFTING_LEFT":
      case "DRIFTING_RIGHT":
        T.pitch = 0.08;
        T.jaw = Math.max(p.restJaw, 0.35);
        T.brow = -0.6;
        T.lids = Math.max(p.restLids, 0.18);
        break;
      case "BOOSTING":
        T.pitch = -0.12 * p.boostKick;
        T.jaw = 0.4 + 0.5 * p.boostFace;
        T.wide = 0.5 * p.boostFace + (m.boostEnhanced ? 0.3 : 0);
        T.brow = 0.6;
        T.lids = 0;
        T.spread = 0.35;
        T.flap = 0.25;
        break;
      case "AIRBORNE":
        T.pitch = -0.08;
        T.headPitch = -0.15;
        T.jaw = 0.7;
        T.wide = 0.7;
        T.brow = 0.8;
        T.lids = 0;
        T.spread = 0.85;
        T.flap = 0.2;
        break;
      case "LANDING":
        T.pitch = 0.18;
        T.lids = 0.45;
        T.jaw = 0.15;
        break;
      case "COLLISION": {
        const hard = this.hitHard;
        T.pitch = -0.22 * hard;
        T.jaw = 0.55;
        // Grumpy racers shake their heads; the rest just go wide-eyed.
        if (p.grumble > 0.4 && st > 0.15) {
          T.brow = -1;
          T.wide = 0;
          T.lids = 0.35;
          T.headYaw = Math.sin(st * 22) * 0.35 * p.grumble * hard;
          T.jaw = 0.25;
        } else {
          T.wide = 0.9;
          T.brow = 0.9;
          T.lids = 0;
        }
        break;
      }
      case "VICTORY": {
        T.jaw = 0.9;
        T.brow = 1;
        T.lids = 0;
        T.wide = 0.3;
        T.bounce = 1.5;
        const beat = Math.sin(st * 7);
        if (p.victory === "cheer") {
          T.cheerL = 1;
          T.cheerR = 1;
          T.headRoll = beat * 0.2;
          T.headPitch = -0.15;
          T.lids = beat > 0.4 ? 0.85 : 0; // happy squeezed eyes
        } else if (p.victory === "nod") {
          T.cheerR = 1;
          T.headPitch = Math.max(0, Math.sin(st * 6)) * 0.35 - 0.05;
          T.pitch = -0.1;
          T.brow = 0.2;
          T.jaw = 0.6;
        } else if (p.victory === "wave") {
          T.cheerR = 0.75;
          T.headRoll = 0.15;
          T.jaw = 0.55;
          T.lids = 0.35;
        } else {
          T.cheerL = 1;
          T.spread = 1;
          T.flap = 1;
          T.headPitch = -0.2;
        }
        break;
      }
      case "DEFEAT":
        T.pitch = 0.22;
        T.headPitch = 0.35;
        T.headYaw = Math.sin(this.t * 0.6) * 0.1;
        T.jaw = 0.05;
        T.lids = 0.5;
        T.brow = 0.7;
        T.bounce = 0;
        break;
    }
    // Personal touches while driving: curious head tilts and glances at a nearby rival.
    if (state !== "VICTORY" && state !== "DEFEAT") {
      this.tiltIn -= dt;
      if (this.tiltIn <= 0) {
        this.tiltIn = (4 + this.rand() * 5) / Math.max(0.15, p.curiosity);
        this.tilt = 0.9;
        this.tiltDir = this.rand() < 0.5 ? -1 : 1;
      }
      if (this.tilt > 0) {
        this.tilt -= dt;
        T.headRoll +=
          this.tiltDir * 0.28 * p.curiosity * Math.sin(Math.min(1, this.tilt / 0.9) * Math.PI);
        if (!drifting)
          T.headYaw +=
            this.tiltDir * 0.35 * p.curiosity * Math.sin(Math.min(1, this.tilt / 0.9) * Math.PI);
      }
      this.glanceIn -= dt;
      if (this.glance > 0) this.glance -= dt;
      else if (this.glanceIn <= 0) {
        this.glanceIn = p.glanceEvery * (0.6 + this.rand() * 0.8);
        if (rival && !drifting && moving > 0.3) {
          this.glanceYaw = Math.max(
            -1.1,
            Math.min(1.1, Math.atan2(rival.x, Math.max(rival.z, -4))),
          );
          this.glance = 0.6 + this.rand() * 0.5;
        }
      }
      if (this.glance > 0) T.headYaw = this.glanceYaw;
    }
    if (this.surprise > 0) {
      T.wide = Math.max(T.wide, this.surprise);
      T.jaw = Math.max(T.jaw, this.surprise * 0.8);
    }

    // --- Ease every channel toward its target.
    const resp = p.response;
    for (const k of Object.keys(RATE) as (keyof Channels)[])
      this.c[k] = ease(this.c[k], T[k], RATE[k] * resp, dt);
    const c = this.c;

    // Blinks (never while wide-eyed with surprise).
    this.blinkIn -= dt;
    if (this.blinkIn <= 0 && this.blink <= 0) {
      this.blink = p.blinkTime;
      this.blinkIn = p.blinkEvery * (0.5 + this.rand());
    }
    let blink = 0;
    if (this.blink > 0) {
      this.blink -= dt;
      blink = Math.sin(Math.max(0, this.blink / p.blinkTime) * Math.PI);
    }

    // --- Apply: the kart body (bob, squash, sway).
    const bob =
      Math.sin(this.t * Math.PI * 2 * (p.bobHz + fast * 2)) * p.bob * (0.5 + c.bounce * 0.6);
    const hop =
      state === "VICTORY" ? Math.max(0, Math.sin(this.stateTime * 7)) * 0.05 * c.bounce : 0;
    const body = kart.body;
    body.position.y = Math.abs(Math.sin(this.t * 13)) * 0.012 * moving + Math.max(0, bob) * 0.3;
    body.rotation.z = -c.lean * 0.15;
    body.rotation.x = -this.kick * 0.06;
    const sq = this.squash;
    body.scale.set(1 / Math.sqrt(sq), sq, 1 / Math.sqrt(sq));

    // The rider: torso, neck and head.
    rig.root.position.y = kart.seat.y + bob + hop;
    const torso = rig.torso;
    torso.rotation.set(
      c.pitch * 0.9 - this.kick * 0.3 * p.boostKick + Math.sin(this.t * 1.1) * 0.02 * c.bounce,
      c.twist + c.headYaw * 0.12,
      // Positive roll tips the head toward the racer's right (-X): into a right turn.
      c.lean + Math.sin(this.t * 40) * 0.12 * this.jolt,
    );
    torso.scale.set(1 / Math.sqrt(sq), sq, 1 / Math.sqrt(sq));
    const head = rig.head;
    const base = (head.userData.base ??= head.rotation.clone()) as THREE.Euler;
    const neck = rig.neck;
    if (neck) {
      const nb = (neck.userData.base ??= neck.rotation.clone()) as THREE.Euler;
      neck.rotation.set(
        nb.x + c.headPitch * 0.4 - c.pitch * 0.4,
        nb.y + c.headYaw * 0.4,
        nb.z + c.headRoll * 0.4,
      );
      head.rotation.set(
        base.x + c.headPitch * 0.6 - c.pitch * 0.3 + this.kick * 0.2,
        base.y + c.headYaw * 0.6,
        base.z + c.headRoll * 0.6,
        "YXZ",
      );
    } else
      head.rotation.set(
        base.x + c.headPitch - c.pitch * 0.6 + this.kick * 0.3,
        base.y + c.headYaw * 0.85,
        base.z + c.headRoll,
        "YXZ",
      );

    // Face.
    const f = rig.face;
    const lids = Math.max(c.lids * (1 - c.wide), blink);
    for (const e of f.eyes) {
      e.lid.rotation.x = f.lidOpen + (f.lidClosed - f.lidOpen) * Math.min(1, lids);
      const w = 1 + c.wide * 0.14;
      e.group.scale.set(w, w, w);
      e.look.rotation.set(-c.headPitch * 0.3, -c.headYaw * 0.25, 0);
    }
    f.brows.forEach((b, i) => {
      const bb = (b.userData.base ??= { y: b.position.y, z: b.rotation.z }) as {
        y: number;
        z: number;
      };
      const side = f.eyes[i]?.side ?? 1;
      b.position.y = bb.y + c.brow * 0.03 + c.wide * 0.03;
      b.rotation.z = bb.z - side * c.brow * 0.35;
    });
    if (f.jaw) f.jaw.rotation.x = c.jaw * f.jawOpen;

    // Steering wheel follows the stick (an eager racer saws at it a bit more).
    kart.steering.rotation.z = m.steer * 1.3 * p.steerHands;

    // Arms and hands: on the wheel, or up to celebrate.
    this.rig.root.updateMatrixWorld(true);
    kart.steering.updateMatrixWorld(true);
    const cheer = [c.cheerL, c.cheerR];
    const wave = p.victory === "wave" ? Math.sin(this.t * 9) * 0.12 : 0;
    rig.arms.forEach((arm, i) => {
      const grip = kart.steering.localToWorld(tmpA.copy(kart.grips[i]!));
      const up = rig.cheer[i]!;
      const pump = state === "VICTORY" ? Math.max(0, Math.sin(this.stateTime * 7 + i)) * 0.06 : 0;
      const raised = torso.localToWorld(tmpB.set(up.x + wave, up.y + pump, up.z));
      const w = cheer[i]!;
      const target = grip.lerp(raised, w);
      const wrist = reach(arm, torso, target);
      // The hand sits at the wrist: gripping the wheel, or turned up to wave.
      const hand = arm.hand;
      hand.position.copy(kart.body.worldToLocal(wrist.clone()));
      tmpQ.copy(kart.steering.quaternion);
      tmpM.extractRotation(torso.matrixWorld);
      tmpQ2
        .setFromRotationMatrix(tmpM)
        .premultiply(kart.body.getWorldQuaternion(new THREE.Quaternion()).invert());
      tmpQ2.multiply(
        new THREE.Quaternion().setFromEuler(new THREE.Euler(-0.4, 0, arm.side * (0.3 + wave * 2))),
      );
      hand.quaternion.copy(tmpQ).slerp(tmpQ2, w);
    });

    // Tail: trails behind, sways with the motion and swings out in a drift.
    rig.tail.forEach((j, k) => {
      const b = (j.userData.base ??= j.rotation.clone()) as THREE.Euler;
      const sway =
        Math.sin(this.t * (speed < 0.5 ? 1.6 : 3) - k * 0.7) * (0.06 + 0.04 * k) * (1 - fast * 0.5);
      j.rotation.set(
        b.x - fast * 0.05 * (k + 1) + Math.max(0, this.squash - 1) * 0.6,
        b.y + sway + c.lean * 0.25 * (k + 1) + (drifting ? m.driftDir * 0.12 : 0),
        b.z,
      );
    });

    // Wings: fold, spread and flap.
    rig.wings.forEach((wg, i) => {
      const side = i === 0 ? 1 : -1;
      const fold = wg.userData.fold as THREE.Euler | undefined;
      const open = wg.userData.open as THREE.Euler | undefined;
      if (!fold || !open) return;
      const s = c.spread;
      const flap = Math.sin(this.t * 14) * 0.45 * c.flap;
      wg.rotation.set(
        fold.x + (open.x - fold.x) * s,
        fold.y + (open.y - fold.y) * s + Math.sin(this.t * 3 + i) * 0.03,
        fold.z + (open.z - fold.z) * s + side * flap - c.lean * 0.2,
      );
    });

    // Little extras: crests lag and bob, scarves flutter, packs bounce, leaves sway.
    for (const w of rig.wiggles) {
      const o = w.obj;
      const b = (o.userData.base ??= { r: o.rotation.clone(), y: o.position.y }) as {
        r: THREE.Euler;
        y: number;
      };
      const a = w.amount;
      switch (w.kind) {
        case "crest":
          o.rotation.set(
            b.r.x +
              (Math.sin(this.t * p.bobHz * 3) * 0.03 +
                this.kick * 0.25 +
                Math.max(0, this.squash - 1) * 0.8) *
                a,
            b.r.y - c.headYaw * 0.15 * a,
            b.r.z - c.lean * 0.25 * a,
          );
          break;
        case "flutter":
          o.rotation.set(
            b.r.x - (fast * 0.6 + Math.sin(this.t * 16 + w.side) * 0.18 * fast) * a,
            b.r.y + c.lean * 0.5 * a,
            b.r.z + Math.sin(this.t * 11 + w.side) * 0.1 * fast * a,
          );
          break;
        case "bounce":
          o.position.y =
            b.y + (Math.max(0, this.squash - 1) * 0.5 + Math.max(0, -this.squashV) * 0.004) * a;
          o.rotation.set(
            b.r.x + Math.sin(this.t * 9) * 0.03 * moving * a + this.kick * 0.15 * a,
            b.r.y,
            b.r.z - c.lean * 0.2 * a,
          );
          break;
        case "sway":
          o.rotation.set(
            b.r.x - fast * 0.2 * a,
            b.r.y,
            b.r.z + (Math.sin(this.t * 2.2 + w.side) * 0.12 - c.lean * 0.4) * a,
          );
          break;
      }
    }
  }
}

export function motionOf(s: {
  speed: number;
  steerSmooth: number;
  driftDir: number;
  heading: number;
  velAngle: number;
  grounded: boolean;
  throttleOn: boolean;
  zipPhase: number;
  zipEnhanced: boolean;
  zipTime: number;
  lastImpactTier: number;
  lastImpactSpeed: number;
  spinTime: number;
}): RacerMotion {
  return {
    speed: s.speed,
    steer: s.steerSmooth,
    driftDir: s.driftDir,
    slip: Math.atan2(Math.sin(s.heading - s.velAngle), Math.cos(s.heading - s.velAngle)),
    grounded: s.grounded,
    throttle: s.throttleOn,
    boostPhase: s.zipPhase,
    boostEnhanced: s.zipEnhanced,
    boostLeft: s.zipTime,
    impactTier: s.lastImpactTier,
    impactSpeed: s.lastImpactSpeed,
    spinTime: s.spinTime,
  };
}
