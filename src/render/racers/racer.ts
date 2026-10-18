/**
 * A complete racer for the screen: kart + character + exhaust flame + blob shadow, with
 * a cheaper far-away version, and the animator that brings it to life.
 *
 * Everything here is visual. The racer follows the kart's physics state (position,
 * heading, speed, drift, boosts, hits) and adds motion on top through child transforms:
 * leaning, bobbing, squash and stretch, head turns, blinks and expressions. It never
 * writes back to the physics.
 */
import * as THREE from "three";
import { buildCharacter, type CharacterRig } from "./characters";
import { DESIGNS, type RacerId } from "./designs";
import { buildKart, type KartModel } from "./kart";
import { buildMoss, buildMossKart } from "./moss";
import { atDetail } from "./geo";
import { shadowTexture } from "./paint";

/** What the animator reads from the kart each frame (all already in the kart state). */
export interface RacerMotion {
  speed: number;
  /** Smoothed stick, -1..1 (positive = right). */
  steer: number;
  driftDir: number;
  /** Nose angle minus travel angle (the kart's slip), radians. */
  slip: number;
  grounded: boolean;
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

/** Distance beyond which the cheap version is drawn, metres. */
export const LOD_DISTANCE = 45;

/** Characters are big for their karts, like toys. */
const CHARACTER_SCALE = 1.2;
const DRIFT_LEAN = 0.26;
const STEER_LEAN = 0.16;

const smoothTo = (v: number, target: number, rate: number, dt: number) =>
  v + (target - v) * (1 - Math.exp(-rate * dt));

/** A tiny deterministic random sequence per racer (blinks, glances). */
function rng(seed: number) {
  let a = seed >>> 0 || 1;
  return () => {
    a ^= a << 13;
    a ^= a >>> 17;
    a ^= a << 5;
    return ((a >>> 0) % 10000) / 10000;
  };
}

export class Racer {
  readonly root = new THREE.Group();
  readonly lod = new THREE.LOD();
  readonly high = new THREE.Group();
  readonly lowGroup = new THREE.Group();
  readonly kart: KartModel;
  readonly rig: CharacterRig;
  readonly flame: THREE.Mesh;
  readonly flameMat: THREE.MeshBasicMaterial;
  readonly core: THREE.Mesh;
  readonly shadow: THREE.Mesh;
  readonly id: RacerId;

  // Animation state.
  private t = 0;
  private lean = 0;
  private headYaw = 0;
  private headPitch = 0;
  private kick = 0; // boost "pushed back into the seat"
  private kickV = 0;
  private squash = 1;
  private squashV = 0;
  private recoil = 0;
  private wheelSpin = 0;
  private blinkIn: number;
  private blinkLeft = 0;
  private glanceIn: number;
  private glanceLeft = 0;
  private glanceYaw = 0;
  private surprise = 0;
  private wasGrounded = true;
  private airTime = 0;
  private lastBoostLeft = 0;
  private lastImpact = { tier: 0, speed: 0 };
  private lastSpin = 0;
  private rand: () => number;

  constructor(id: RacerId, opts: { alt?: boolean; seed?: number } = {}) {
    this.id = id;
    const design = DESIGNS[id];
    const paint = opts.alt ? design.altKart : design.kart;
    this.rand = rng(opts.seed ?? 7);
    this.blinkIn = 1 + this.rand() * 2;
    this.glanceIn = 3 + this.rand() * 4;

    // Moss uses the faceted, pixel-textured style (and its own kart).
    const faceted = id === "moss" && !opts.alt;
    this.kart = faceted ? buildMossKart(0) : buildKart(id, paint, 0);
    this.rig = faceted ? buildMoss(this.kart.grips) : buildCharacter(id, this.kart.grips);
    this.rig.root.position.copy(this.kart.seat);
    this.rig.root.scale.setScalar(CHARACTER_SCALE);
    this.kart.body.add(this.rig.root);
    this.kart.steering.add(this.rig.hands);
    this.high.add(this.kart.root);

    // Far away: a cheap kart and a one-piece character, no rig.
    const lowKart = faceted ? buildMossKart(1) : atDetail(0.5, () => buildKart(id, paint, 1));
    lowKart.steering.visible = false;
    this.rig.low.position.copy(lowKart.seat);
    this.rig.low.scale.setScalar(CHARACTER_SCALE);
    lowKart.body.add(this.rig.low);
    this.lowGroup.add(lowKart.root);
    this.lowWheels = lowKart.wheels;

    this.lod.addLevel(this.high, 0);
    this.lod.addLevel(this.lowGroup, LOD_DISTANCE);
    this.root.add(this.lod);

    // Exhaust flame: shows boosts (main.ts colours it by boost source and phase).
    this.flameMat = new THREE.MeshBasicMaterial({ color: "#ff8c1a", transparent: true });
    this.flame = new THREE.Mesh(
      new THREE.ConeGeometry(0.3, 1.2, 10).rotateX(-Math.PI / 2),
      this.flameMat,
    );
    this.flame.position.copy(this.kart.exhaust).add(new THREE.Vector3(0, 0, -0.5));
    this.flame.visible = false;
    this.core = new THREE.Mesh(
      new THREE.ConeGeometry(0.15, 0.95, 8).rotateX(-Math.PI / 2),
      new THREE.MeshBasicMaterial({ color: "#3ddc84" }),
    );
    this.core.position.copy(this.flame.position).add(new THREE.Vector3(0, 0, 0.12));
    this.core.visible = false;
    this.root.add(this.flame, this.core);

    this.shadow = new THREE.Mesh(
      new THREE.PlaneGeometry(2.2, 3).rotateX(-Math.PI / 2),
      new THREE.MeshBasicMaterial({ map: shadowTexture(), transparent: true, depthWrite: false }),
    );
    this.shadow.renderOrder = 1;
  }

  private lowWheels: KartModel["wheels"];

  /** Put the blob shadow on the ground under the kart (it stays flat on the road). */
  placeShadow(x: number, groundY: number, z: number, heading: number, above: number) {
    this.shadow.position.set(x, groundY + 0.05, z);
    this.shadow.rotation.y = heading;
    const s = Math.max(0.4, 1 - above * 0.12);
    this.shadow.scale.setScalar(s);
    (this.shadow.material as THREE.MeshBasicMaterial).opacity = Math.max(0.25, 1 - above * 0.15);
  }

  /** Remove from the scene and free the geometry. */
  dispose(scene: THREE.Scene) {
    scene.remove(this.root, this.shadow);
    this.root.traverse((o) => {
      if (o instanceof THREE.Mesh) o.geometry.dispose();
    });
    this.shadow.geometry.dispose();
  }

  /**
   * Animate for one rendered frame. `rival` is the nearest other racer's position in
   * this racer's local frame (x across, z forward), if one is close enough to glance at.
   */
  animate(dt: number, m: RacerMotion, rival: { x: number; z: number } | null) {
    dt = Math.min(dt, 0.1);
    this.t += dt;
    const near = this.lod.getCurrentLevel() === 0;
    const spin = (Math.abs(m.speed) * dt) / 0.4;
    this.wheelSpin += spin;
    const wheels = near ? this.kart.wheels : this.lowWheels;
    for (const w of wheels) {
      w.tyre.rotation.x = this.wheelSpin * (0.4 / w.radius);
      if (w.front) w.pivot.rotation.y = -m.steer * 0.45;
    }
    if (!near) return; // far away: wheels only

    const rig = this.rig;
    const p = rig.personality;
    const moving = Math.min(1, Math.abs(m.speed) / 8);
    const fast = Math.min(1, Math.abs(m.speed) / 30);

    // --- Events, read from changes in the kart's state.
    const boosting = m.boostPhase === 1 || m.boostPhase === 2;
    if (boosting && m.boostLeft > this.lastBoostLeft + 0.02) this.kickV += m.boostEnhanced ? 7 : 5;
    this.lastBoostLeft = boosting ? m.boostLeft : 0;
    if (
      m.impactTier > 0 &&
      (m.impactTier !== this.lastImpact.tier || m.impactSpeed !== this.lastImpact.speed)
    ) {
      const hard = m.impactTier >= 3 ? 1 : m.impactTier === 2 ? 0.6 : 0.25;
      this.squashV -= 3 * hard;
      this.recoil = Math.max(this.recoil, hard);
      if (hard > 0.5) this.surprise = 0.6;
    }
    this.lastImpact = { tier: m.impactTier, speed: m.impactSpeed };
    if (m.spinTime > this.lastSpin + 0.05) {
      this.squashV -= 3.5;
      this.recoil = 1;
      this.surprise = 1;
    }
    this.lastSpin = m.spinTime;
    // Take-off and landing.
    if (this.wasGrounded && !m.grounded) {
      this.squashV -= 1.2; // a quick crouch...
      this.airTime = 0;
    }
    if (!m.grounded) this.airTime += dt;
    if (!this.wasGrounded && m.grounded && this.airTime > 0.15)
      this.squashV -= 2 + Math.min(3, this.airTime * 3);
    this.wasGrounded = m.grounded;

    // --- Springs: squash and stretch, boost kick.
    const squashTarget = !m.grounded && this.airTime > 0.08 ? 1.07 : 1;
    this.squashV += (-(this.squash - squashTarget) * 180 - this.squashV * 14) * dt;
    this.squash += this.squashV * dt;
    this.kickV += (-this.kick * 60 - this.kickV * 9) * dt;
    this.kick += this.kickV * dt;
    this.recoil = Math.max(0, this.recoil - dt * 2.5);
    this.surprise = Math.max(0, this.surprise - dt);

    // --- Lean: into the turn; harder in a drift; countersteer pulls against it.
    const drifting = m.driftDir !== 0;
    let leanTarget =
      (m.steer * STEER_LEAN * moving + (drifting ? m.driftDir * DRIFT_LEAN : 0)) * p.lean;
    if (!m.grounded) leanTarget *= 0.4;
    this.lean = smoothTo(this.lean, leanTarget, drifting ? 7 : 9, dt);

    // --- Head: looks where the kart is going (into the drift), toward the turn, and
    // now and then glances at a nearby racer.
    this.glanceIn -= dt;
    if (this.glanceLeft > 0) this.glanceLeft -= dt;
    else if (this.glanceIn <= 0) {
      this.glanceIn = p.glanceEvery * (0.6 + this.rand() * 0.8);
      if (rival && !drifting && moving > 0.3) {
        this.glanceYaw = Math.max(-1.1, Math.min(1.1, Math.atan2(rival.x, Math.max(rival.z, -4))));
        this.glanceLeft = 0.7 + this.rand() * 0.5;
      }
    }
    let yawTarget = (-m.slip * 0.7 - m.steer * 0.28) * moving;
    if (this.glanceLeft > 0) yawTarget = this.glanceYaw;
    const idle = Math.abs(m.speed) < 0.5;
    if (idle) {
      // Personality while waiting: Bramble keeps checking around; others drift slowly.
      const look = p.glanceEvery < 4 ? Math.sin(this.t * 1.3) * 0.5 : Math.sin(this.t * 0.6) * 0.25;
      yawTarget = look;
    }
    this.headYaw = smoothTo(this.headYaw, yawTarget, this.glanceLeft > 0 ? 6 : 4, dt);
    const pitchTarget = (!m.grounded ? -0.15 : 0) + this.kick * 0.35 - this.recoil * 0.25;
    this.headPitch = smoothTo(this.headPitch, pitchTarget, 10, dt);

    // --- Apply to the rig (child transforms only).
    const bob = Math.sin(this.t * Math.PI * 2 * (p.bobHz + fast * 2)) * p.bob * (idle ? 1.4 : 0.6);
    const body = this.kart.body;
    body.position.y = Math.abs(Math.sin(this.t * 13)) * 0.012 * moving + Math.max(0, bob) * 0.3;
    body.rotation.z = -this.lean * 0.18;
    body.rotation.x = -this.kick * 0.06;
    body.scale.set(1 / Math.sqrt(this.squash), this.squash, 1 / Math.sqrt(this.squash));

    rig.root.position.y = this.kart.seat.y + bob;
    rig.torso.rotation.z = this.lean + Math.sin(this.t * 25) * 0.04 * this.recoil;
    rig.torso.rotation.x =
      -this.kick * 0.32 - this.recoil * 0.2 + (idle ? Math.sin(this.t * 1.1) * 0.03 : 0);
    rig.torso.rotation.y = (drifting ? m.driftDir * -0.12 : 0) + this.headYaw * 0.15;
    rig.torso.scale.set(1 / Math.sqrt(this.squash), this.squash, 1 / Math.sqrt(this.squash));
    rig.head.rotation.y = this.headYaw * 0.85;
    rig.head.rotation.x = this.headPitch;
    rig.head.rotation.z =
      -this.lean * 0.45 + (idle && p.bobHz < 1.2 ? Math.sin(this.t * 0.8) * 0.06 : 0);

    // Steering wheel follows the stick; the hands ride on it.
    this.kart.steering.rotation.z = m.steer * 1.3;

    // --- Face: blinks, and expressions for boosts, hits and jumps.
    this.blinkIn -= dt;
    if (this.blinkIn <= 0 && this.blinkLeft <= 0) {
      this.blinkLeft = 0.13;
      this.blinkIn = p.blinkEvery * (0.5 + this.rand());
    }
    let eyeY = 1;
    if (this.blinkLeft > 0) {
      this.blinkLeft -= dt;
      eyeY = 0.12;
    } else if (this.surprise > 0 || (boosting && m.boostEnhanced)) eyeY = 1.15;
    else if (idle && p.bobHz < 1.2) eyeY = 0.7; // Otto, content
    rig.eyes.scale.set(1, eyeY, 1);
    const face: "smile" | "open" | "grin" =
      this.surprise > 0 || (!m.grounded && this.airTime > 0.2)
        ? "open"
        : boosting
          ? p.boostFace
          : drifting
            ? "grin"
            : "smile";
    if (rig.setFace) {
      rig.setFace(
        face,
        eyeY < 0.5 ? "closed" : eyeY > 1.05 ? "wide" : eyeY < 0.9 ? "sleepy" : "open",
      );
    } else {
      rig.mouths.smile.visible = face === "smile";
      rig.mouths.open.visible = face === "open";
      rig.mouths.grin.visible = face === "grin";
    }
    if (rig.brows) rig.brows.position.y = boosting || drifting ? -0.025 : 0;

    // --- Little personal motions: gills, antennae, tails, wings, scarf, the orange.
    for (const w of rig.wiggles) {
      const o = w.obj;
      const s = w.side;
      switch (w.kind) {
        case "gill":
          o.rotation.z = s * (Math.sin(this.t * 3 + s) * 0.12 - fast * 0.2);
          o.rotation.x = -fast * 0.5 - this.kick * 0.3;
          break;
        case "antenna":
          o.rotation.x =
            -fast * 0.6 -
            this.kick * 0.4 +
            (idle ? Math.sin(this.t * 9) * 0.06 * Math.max(0, Math.sin(this.t * 0.7)) : 0);
          o.rotation.z = s * Math.sin(this.t * 2 + s) * 0.08 - this.lean * 0.6;
          break;
        case "wing":
          o.rotation.y =
            s * (0.15 + fast * 0.25 + Math.sin(this.t * (idle ? 3 : 14)) * (idle ? 0.04 : 0.08));
          break;
        case "tail":
          o.rotation.y = Math.sin(this.t * (idle ? 1.5 : 3)) * 0.18 + this.lean * 0.8;
          o.rotation.x = fast * 0.25;
          break;
        case "scarf":
          o.rotation.x = -fast * 0.8 + Math.sin(this.t * 16) * 0.15 * fast;
          o.rotation.y = this.lean * 0.8;
          break;
        case "orange":
          o.rotation.z = Math.sin(this.t * 1.3) * 0.05 - this.lean * 0.5;
          o.position.y = 0.56 + Math.max(0, (this.squash - 1) * 0.6);
          break;
      }
    }

    // Arms reach from the shoulders to the hands on the wheel.
    this.root.updateMatrixWorld(true);
    rig.arms.forEach((a, i) => {
      const grip = this.kart.grips[i]!;
      const hand = this.kart.steering.localToWorld(tmpHand.copy(grip));
      const shoulder = rig.torso.localToWorld(tmpShoulder.copy(rig.shoulders[i]!));
      a.lookAt(hand);
      a.scale.set(1, 1, shoulder.distanceTo(hand));
    });
  }
}

const tmpHand = new THREE.Vector3();
const tmpShoulder = new THREE.Vector3();

export function motionOf(s: {
  speed: number;
  steerSmooth: number;
  driftDir: number;
  heading: number;
  velAngle: number;
  grounded: boolean;
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
    boostPhase: s.zipPhase,
    boostEnhanced: s.zipEnhanced,
    boostLeft: s.zipTime,
    impactTier: s.lastImpactTier,
    impactSpeed: s.lastImpactSpeed,
    spinTime: s.spinTime,
  };
}
