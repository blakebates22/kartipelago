/**
 * The racers: every one builds (near, far, both colourways), sits on the shared chassis,
 * keeps its hands on the wheel, stays inside its kart, has its own silhouette, stays
 * within the triangle budget, and animates from the physics state without touching it.
 */
import { DRAGON_PALETTES } from "../src/render/racers/roster/dragon";
import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { Racer, type RacerMotion } from "../src/render/racers/racer";
import { Animator, STATES } from "../src/render/racers/animator";
import { DESIGNS, RACER_IDS } from "../src/render/racers/designs";
import { BUILDS } from "../src/render/racers/roster";
import { CHASSIS } from "../src/render/racers/kit/chassis";
import { RACER_STEMS } from "../src/audio/songs";

const motion = (o: Partial<RacerMotion> = {}): RacerMotion => ({
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
  ...o,
});

function triangles(o: THREE.Object3D) {
  let n = 0;
  o.traverse((m) => {
    if (m instanceof THREE.Mesh) {
      const g = m.geometry as THREE.BufferGeometry;
      n += (g.index ? g.index.count : g.getAttribute("position").count) / 3;
    }
  });
  return n;
}

/** World-space bounds of a racer's rider meshes (body, head, tail, wings, gear). */
function riderBounds(r: Racer) {
  r.root.updateMatrixWorld(true);
  return new THREE.Box3().setFromObject(r.rig.root);
}

/** Run the animator for a while in one motion state. */
function run(r: Racer, m: RacerMotion, seconds = 1.5) {
  for (let t = 0; t < seconds; t += 1 / 60)
    if (r.boss) r.animate(1 / 60, m, null);
    else r.anim.step(1 / 60, m, r.kart, { x: 2, z: 3 });
  r.root.updateMatrixWorld(true);
}

describe("the racers", () => {
  it("lists the same racers everywhere: designs, builds and the select music", () => {
    // (Plus Adventure's dragons: a racer for the bosses, never in the menus.)
    const all = [...RACER_IDS, "dragon"].sort();
    expect(Object.keys(DESIGNS).sort()).toEqual(all);
    expect(Object.keys(BUILDS).sort()).toEqual(all);
    expect([...RACER_STEMS].sort()).toEqual([...RACER_IDS].sort());
  });

  it("builds the dragons in every dragon's colours", () => {
    for (const palette of Object.values(DRAGON_PALETTES)) {
      const r = new Racer("dragon", { palette });
      expect(triangles(r.high)).toBeGreaterThan(3000);
      expect(triangles(r.high)).toBeLessThan(14000);
      expect(r.rig.wings).toHaveLength(2);
    }
  });

  it("races the bosses as huge dragons on foot: no kart, several karts long", () => {
    for (const palette of Object.values(DRAGON_PALETTES)) {
      const r = new Racer("dragon", { palette, boss: true });
      expect(r.boss).toBeDefined();
      expect(r.root.children).toContain(r.boss!.root);
      expect(r.root.children).not.toContain(r.lod);
      const n = triangles(r.root);
      expect(n).toBeGreaterThan(3000);
      expect(n).toBeLessThan(24000);
      // Bounding along, galloping and in the air, it stays whole and on its feet.
      for (const m of [
        motion(),
        motion({ speed: 25, throttle: true, steer: 0.6 }),
        motion({ speed: 25, grounded: false }),
      ]) {
        run(r, m, 0.6);
        const b = new THREE.Box3().setFromObject(r.boss!.root);
        expect(b.max.z - b.min.z, "length").toBeGreaterThan(CHASSIS.length * 4);
        expect(b.max.y, "height").toBeGreaterThan(3.5);
        expect(Number.isFinite(b.min.y)).toBe(true);
      }
    }
  });

  for (const id of RACER_IDS)
    describe(DESIGNS[id].name, () => {
      it("builds near and far, in both colourways, within budget", () => {
        for (const alt of [false, true]) {
          const r = new Racer(id, { alt });
          const near = triangles(r.high);
          const far = triangles(r.lowGroup);
          expect(near, "near").toBeGreaterThan(3000); // not a placeholder
          expect(near, "near").toBeLessThan(12000);
          expect(far, "far").toBeLessThan(3000);
        }
      });

      it("sits on the shared chassis: same wheels, seat, wheel grips and exhaust", () => {
        const r = new Racer(id);
        expect(r.kart.wheels.map((w) => [w.pivot.position.toArray(), w.radius, w.front])).toEqual(
          CHASSIS.wheels.map((w) => [[w.x, w.r, w.z], w.r, w.front]),
        );
        expect(r.kart.seat.toArray()).toEqual([...CHASSIS.seat]);
        expect(r.kart.exhaust.toArray()).toEqual([...CHASSIS.exhaust]);
        expect(r.kart.grips.map((g) => g.toArray())).toEqual(CHASSIS.grips.map((g) => [...g]));
        expect(r.kart.steering.position.toArray()).toEqual([...CHASSIS.steering.at]);
      });

      it("keeps both hands on the wheel while driving, steering and drifting", () => {
        const r = new Racer(id);
        for (const m of [
          motion({ speed: 20, throttle: true }),
          motion({ speed: 20, throttle: true, steer: -0.9 }),
          motion({ speed: 20, throttle: true, steer: 0.6, driftDir: 1, slip: 0.6 }),
        ]) {
          run(r, m);
          r.rig.arms.forEach((arm, i) => {
            const grip = r.kart.steering.localToWorld(r.kart.grips[i]!.clone());
            const hand = arm.hand.getWorldPosition(new THREE.Vector3());
            expect(hand.distanceTo(grip), `hand ${i}`).toBeLessThan(0.03);
          });
        }
      });

      it("stays inside the kart: above the road, within its length and width", () => {
        const r = new Racer(id);
        for (const m of [
          motion(),
          motion({ speed: 20, steer: -1, driftDir: -1, slip: -0.6, throttle: true }),
        ]) {
          run(r, m);
          const b = riderBounds(r);
          expect(b.min.y, "above the road").toBeGreaterThan(0.3);
          expect(b.min.z, "not past the back").toBeGreaterThan(-CHASSIS.length / 2 - 0.15);
          expect(b.max.z, "not past the nose").toBeLessThan(CHASSIS.length / 2);
          // (Leaning into a hard drift, a head may hang a little over the side.)
          expect(Math.max(-b.min.x, b.max.x), "not far past the sides").toBeLessThan(
            CHASSIS.width / 2 + 0.5,
          );
        }
      });

      it("animates from the kart's state without changing it", () => {
        const r = new Racer(id);
        const m = motion({
          speed: 25,
          steer: 0.4,
          driftDir: 1,
          slip: 0.5,
          throttle: true,
          boostPhase: 1,
          boostLeft: 1,
        });
        const before = JSON.stringify(m);
        run(r, m, 0.5);
        expect(JSON.stringify(m)).toBe(before);
      });
    });

  it("gives every racer their own silhouette from behind", () => {
    // Each rider's outline from the race camera's side (behind): which cells of a 16x16
    // grid over the kart's back view their vertices fill. Every pair must differ a lot.
    const masks = RACER_IDS.map((id) => {
      const r = new Racer(id);
      run(r, motion());
      const cells = new Set<number>();
      const v = new THREE.Vector3();
      r.rig.root.traverse((m) => {
        if (!(m instanceof THREE.Mesh)) return;
        const pos = (m.geometry as THREE.BufferGeometry).getAttribute("position");
        for (let i = 0; i < pos.count; i++) {
          v.fromBufferAttribute(pos, i).applyMatrix4(m.matrixWorld);
          const cx = Math.floor(((v.x + 1.2) / 2.4) * 16);
          const cy = Math.floor((v.y / 2.4) * 16);
          if (cx >= 0 && cx < 16 && cy >= 0 && cy < 16) cells.add(cy * 16 + cx);
        }
      });
      return cells;
    });
    for (let i = 0; i < masks.length; i++)
      for (let j = i + 1; j < masks.length; j++) {
        const [a, b] = [masks[i]!, masks[j]!];
        const shared = [...a].filter((c) => b.has(c)).length;
        const union = new Set([...a, ...b]).size;
        expect(1 - shared / union, `${RACER_IDS[i]} vs ${RACER_IDS[j]}`).toBeGreaterThan(0.2);
      }
  });
});

describe("the animator", () => {
  const cases: [Partial<RacerMotion>, (typeof STATES)[number]][] = [
    [{}, "IDLE"],
    [{ speed: 15, throttle: true }, "ACCELERATING"],
    [{ speed: 15, throttle: true, steer: -0.8 }, "STEERING_LEFT"],
    [{ speed: 15, throttle: true, steer: 0.8 }, "STEERING_RIGHT"],
    [{ speed: 15, throttle: true, driftDir: -1, slip: -0.5 }, "DRIFTING_LEFT"],
    [{ speed: 15, throttle: true, driftDir: 1, slip: 0.5 }, "DRIFTING_RIGHT"],
    [{ speed: 25, throttle: true, boostPhase: 1, boostLeft: 1 }, "BOOSTING"],
  ];
  for (const [m, state] of cases)
    it(`reads ${state} from the kart`, () => {
      const r = new Racer("tiko");
      run(r, motion(m), 0.5);
      expect(r.anim.state).toBe(state);
    });

  it("reads braking, jumps, landings, crashes and the race result", () => {
    const r = new Racer("brakka");
    run(r, motion({ speed: 20, throttle: true }), 0.5);
    let speed = 20;
    for (let k = 0; k < 20; k++)
      r.anim.step(1 / 60, motion({ speed: (speed -= 0.4) }), r.kart, null);
    expect(r.anim.state).toBe("BRAKING");
    run(r, motion({ speed: 20, grounded: false }), 0.4);
    expect(r.anim.state).toBe("AIRBORNE");
    r.anim.step(1 / 60, motion({ speed: 20 }), r.kart, null);
    expect(r.anim.state).toBe("LANDING");
    r.anim.step(1 / 60, motion({ speed: 20, impactTier: 3, impactSpeed: 14 }), r.kart, null);
    expect(r.anim.state).toBe("COLLISION");
    r.setResult(1, 8);
    run(r, motion({ speed: 8 }), 0.2);
    expect(r.anim.state).toBe("VICTORY");
    r.setResult(7, 8);
    run(r, motion({ speed: 8 }), 0.2);
    expect(r.anim.state).toBe("DEFEAT");
  });

  it("never snaps: poses ease from one state to the next", () => {
    const r = new Racer("zephyr");
    run(r, motion({ speed: 20, throttle: true }), 1);
    const a = new Animator(r.rig, 3);
    let prev = { ...a.c };
    let worst = 0;
    // Jump straight into a hard drift, then a boost, then the air.
    for (const m of [
      motion({ speed: 20, throttle: true, steer: -1, driftDir: -1, slip: -0.6 }),
      motion({ speed: 25, throttle: true, boostPhase: 1, boostLeft: 1 }),
      motion({ speed: 25, grounded: false }),
    ])
      for (let k = 0; k < 30; k++) {
        a.step(1 / 60, m, r.kart, null);
        for (const key of ["lean", "headYaw", "jaw", "spread"] as const)
          worst = Math.max(worst, Math.abs(a.c[key] - prev[key]));
        prev = { ...a.c };
      }
    expect(worst).toBeLessThan(0.2);
  });

  it("has its own timing per racer", () => {
    const p = RACER_IDS.map((id) => new Racer(id).rig.personality);
    expect(new Set(p.map((x) => x.victory)).size).toBe(4);
    expect(new Set(p.map((x) => x.response)).size).toBeGreaterThan(2);
  });
});
