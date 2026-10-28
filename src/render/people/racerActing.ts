/**
 * Racers acting in a cutscene: sitting in their karts, they idle as they do on the grid
 * (the racers' own animator), and on top of that turn their heads to look at someone
 * and move their jaws in a speech rhythm while they have the line.
 */
import * as THREE from "three";
import type { Racer } from "../racers/racer";
import type { RacerMotion } from "../racers/animator";
import { speech } from "./animate";

export interface RacerActing {
  update(dt: number, cue: { talk?: boolean; look?: THREE.Vector3 | null }): void;
}

const IDLE: RacerMotion = {
  speed: 0,
  steer: 0,
  driftDir: 0,
  slip: 0,
  grounded: true,
  throttle: false,
  boostPhase: 0,
  boostEnhanced: false,
  boostLeft: 0,
  impactTier: 0,
  impactSpeed: 0,
  spinTime: 0,
};

const ease = (v: number, target: number, rate: number, dt: number) =>
  v + (target - v) * (1 - Math.exp(-rate * dt));
const tA = new THREE.Vector3();
const tQ = new THREE.Quaternion();

export function actRacer(racer: Racer): RacerActing {
  let yaw = 0;
  let pitch = 0;
  let lookW = 0;
  let talkW = 0;
  let talkT = 0;
  return {
    update(dt, cue) {
      racer.animate(dt, IDLE, null);
      if (racer.lod.getCurrentLevel() !== 0 || racer.boss) return;
      const rig = racer.rig;
      talkW = ease(talkW, cue.talk ? 1 : 0, 10, dt);
      if (cue.talk) talkT += dt;
      // Look: the target's direction in the rider's frame.
      let wantYaw = 0;
      let wantPitch = 0;
      if (cue.look) {
        rig.head.getWorldPosition(tA);
        tA.subVectors(cue.look, tA);
        racer.root.getWorldQuaternion(tQ).invert();
        tA.applyQuaternion(tQ);
        wantYaw = Math.max(-1.2, Math.min(1.2, Math.atan2(tA.x, tA.z)));
        wantPitch = Math.max(-0.4, Math.min(0.4, Math.atan2(tA.y, Math.hypot(tA.x, tA.z))));
      }
      lookW = ease(lookW, cue.look ? 1 : 0, 4, dt);
      yaw = ease(yaw, wantYaw, 4.5, dt);
      pitch = ease(pitch, wantPitch, 4.5, dt);
      const head = rig.head;
      const neck = rig.neck;
      const base = head.userData.base as THREE.Euler | undefined;
      if (base) {
        // (The animator set them from their bases this frame: turn them on from there,
        // easing out its idle glances as the look takes over.)
        const k = lookW;
        if (neck) {
          const nb = neck.userData.base as THREE.Euler;
          neck.rotation.y += (nb.y + yaw * 0.4 - neck.rotation.y) * k;
          neck.rotation.x += (nb.x - pitch * 0.3 - neck.rotation.x) * k;
        }
        head.rotation.y += (base.y + yaw * (neck ? 0.6 : 0.9) - head.rotation.y) * k;
        head.rotation.x += (base.x - pitch * 0.5 - head.rotation.x) * k * 0.7;
        for (const e of rig.face.eyes) e.look.rotation.y = yaw * 0.15 * k;
      }
      // Talking: the jaw in a speech rhythm, a little nod.
      const f = rig.face;
      if (f.jaw && talkW > 0.01) {
        const s = speech(talkT);
        const rest = rig.personality.restJaw;
        f.jaw.rotation.x += ((rest * 0.4 + s * 0.75) * f.jawOpen - f.jaw.rotation.x) * talkW;
        head.rotation.x += Math.sin(talkT * 3.1) * 0.04 * talkW;
        for (const b of f.brows) b.position.y += Math.max(0, Math.sin(talkT * 1.7)) * 0.012 * talkW;
      }
    },
  };
}
