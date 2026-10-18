/**
 * The shared toy kart: a rounded, low body with a curved nose, big bright tyres with
 * chunky hubs, a steering wheel, rounded fenders and a little exhaust. Per-racer paint
 * and a small decoration make each one its own.
 *
 * Local frame: +Z forward, +Y up, origin on the ground under the kart's centre. About
 * the same footprint as the old placeholder box, so it matches the collision circle.
 */
import * as THREE from "three";
import type { KartPaint, RacerId } from "./designs";
import { PALETTE } from "./designs";
import { Parts, ball, ring, tube } from "./geo";
import { paintedMaterial } from "./paint";

export interface KartModel {
  root: THREE.Group;
  /** Body (bobs and squashes; the character sits in it). */
  body: THREE.Group;
  /** Front wheels steer (yaw); every tyre spins (its child mesh). */
  wheels: { pivot: THREE.Group; tyre: THREE.Mesh; radius: number; front: boolean }[];
  steering: THREE.Group;
  /** Where the hands hold the wheel, in steering-wheel space. */
  grips: [THREE.Vector3, THREE.Vector3];
  /** Where the character sits, and where the exhaust flame goes (both in body space). */
  seat: THREE.Vector3;
  exhaust: THREE.Vector3;
}

const darker = (hex: string, k = 0.72) => new THREE.Color(hex).multiplyScalar(k);
const lighter = (hex: string, k = 0.35) => new THREE.Color(hex).lerp(new THREE.Color("#ffffff"), k);

/** A half-ring mudguard over a wheel (unit radius, in the wheel's plane). */
const arch = () =>
  new THREE.TorusGeometry(1, 0.12, 6, 12, Math.PI).rotateY(Math.PI / 2).scale(1.5, 1, 1);

function tyre(radius: number, width: number, paint: KartPaint) {
  const p = new Parts();
  // A fat rounded tyre (torus), a hub filling it, and a cap in the middle.
  p.add(ring(1, 0.36, 14), paint.tire, {
    r: [0, Math.PI / 2, 0],
    s: [radius * 0.72, radius * 0.72, width * 1.25],
  });
  p.add(tube(1, 1, 12), paint.hub, {
    r: [0, 0, Math.PI / 2],
    s: [radius * 0.62, width * 0.9, radius * 0.62],
  });
  p.add(tube(1, 1, 8), darker(paint.hub, 0.75), {
    r: [0, 0, Math.PI / 2],
    s: [radius * 0.28, width * 1.05, radius * 0.28],
  });
  for (const side of [-1, 1])
    p.add(ball(8), lighter(paint.hub, 0.2), {
      p: [side * width * 0.52, 0, 0],
      s: [0.05, radius * 0.2, radius * 0.2],
    });
  return p.build();
}

/** A small flourish per racer, so the karts differ a little. */
function decorate(p: Parts, id: RacerId, paint: KartPaint) {
  if (id === "moss") {
    // A frilly fin on the cowl, like the axolotl's tail.
    p.add(ball(10), paint.trim, { p: [0, 1.0, -0.92], s: [0.06, 0.24, 0.26], r: [-0.3, 0, 0] });
  } else if (id === "bramble") {
    // A leaf spoiler.
    p.add(ball(10), PALETTE.leaf, { p: [0, 1.02, -1.02], s: [0.42, 0.04, 0.2], r: [0.2, 0, 0] });
    p.add(tube(0.03, 0.03, 6), PALETTE.chestnut, { p: [0, 0.94, -1.0], s: [1, 0.16, 1] });
  } else if (id === "poppy") {
    // Little rounded wing fins either side of the cowl.
    for (const side of [-1, 1])
      p.add(ball(10), paint.trim, {
        p: [side * 0.62, 0.78, -0.86],
        s: [0.22, 0.16, 0.05],
        r: [0, side * 0.5, side * 0.4],
      });
  } else {
    // An orange-slice badge on the nose.
    p.add(tube(1, 1, 12), PALETTE.orange, {
      p: [0, 0.6, 1.16],
      r: [Math.PI / 2 - 0.5, 0, 0],
      s: [0.12, 0.03, 0.12],
    });
  }
}

export function buildKart(id: RacerId, paint: KartPaint, detail: 0 | 1 = 0): KartModel {
  const root = new THREE.Group();
  const body = new THREE.Group();
  root.add(body);
  const mat = paintedMaterial();

  const p = new Parts();
  // A rounded tub built from soft overlapping shapes: hull, nose, side pods, rear cowl.
  p.add(ball(16), paint.body, { p: [0, 0.42, 0], s: [0.6, 0.26, 1.12] });
  p.add(ball(14), paint.body, { p: [0, 0.4, 0.92], s: [0.5, 0.23, 0.44] });
  p.add(ball(14), paint.body, { p: [0, 0.56, -0.8], s: [0.5, 0.22, 0.34] });
  p.add(ball(12), darker(paint.body), { p: [0, 0.27, 0], s: [0.55, 0.1, 1.05] });
  for (const side of [-1, 1]) {
    p.add(ball(12), paint.trim, { p: [side * 0.5, 0.38, 0.05], s: [0.2, 0.16, 0.74] });
    // Fenders hugging the wheels.
    p.add(arch(), paint.body, { p: [side * 0.8, 0.36, 0.86], s: [1, 0.43, 0.43] });
    p.add(arch(), paint.trim, { p: [side * 0.82, 0.43, -0.8], s: [1.1, 0.5, 0.5] });
  }
  // Nose bumper and toy "headlight eyes".
  p.add(ball(12), paint.trim, { p: [0, 0.32, 1.32], s: [0.44, 0.13, 0.14] });
  if (detail === 0) {
    for (const side of [-1, 1]) {
      p.add(ball(10), PALETTE.white, { p: [side * 0.24, 0.56, 1.2], s: [0.11, 0.09, 0.06] });
      p.add(ball(8), PALETTE.ink, { p: [side * 0.24, 0.56, 1.25], s: [0.05, 0.05, 0.03] });
    }
  }
  // Seat: a soft dark cushion with a rounded back.
  p.add(ball(10), darker(paint.trim, 0.55), { p: [0, 0.62, -0.3], s: [0.34, 0.08, 0.28] });
  p.add(ball(10), darker(paint.trim, 0.65), { p: [0, 0.78, -0.58], s: [0.32, 0.2, 0.09] });
  // Dashboard.
  p.add(ball(10), darker(paint.body, 0.85), { p: [0, 0.64, 0.5], s: [0.38, 0.1, 0.16] });
  // Exhaust: two short chunky pipes out the back.
  for (const side of [-1, 1]) {
    p.add(tube(1, 1, 10), PALETTE.cream, {
      p: [side * 0.22, 0.46, -1.13],
      r: [Math.PI / 2, 0, 0],
      s: [0.09, 0.22, 0.09],
    });
    p.add(tube(1, 1, 10), PALETTE.ink, {
      p: [side * 0.22, 0.46, -1.24],
      r: [Math.PI / 2, 0, 0],
      s: [0.06, 0.02, 0.06],
    });
  }
  decorate(p, id, paint);
  const shell = new THREE.Mesh(p.build(), mat);
  body.add(shell);

  // Wheels: big and bright; the rears a touch bigger, like a toy.
  const wheels: KartModel["wheels"] = [];
  const spots: [number, number, number, boolean][] = [
    [0.8, 0.86, 0.36, true],
    [-0.8, 0.86, 0.36, true],
    [0.82, -0.8, 0.43, false],
    [-0.82, -0.8, 0.43, false],
  ];
  const geoFront = tyre(0.36, 0.3, paint);
  const geoRear = tyre(0.43, 0.34, paint);
  if (detail === 1) {
    // Far away the wheels don't need to turn: bake them into the body (one draw call).
    const baked = new Parts().addColored(shell.geometry);
    for (const [x, z, r, front] of spots)
      baked.addColored(front ? geoFront : geoRear, { p: [x, r, z] });
    shell.geometry.dispose();
    shell.geometry = baked.build();
  } else {
    for (const [x, z, r, front] of spots) {
      const pivot = new THREE.Group();
      pivot.position.set(x, r, z);
      const mesh = new THREE.Mesh(front ? geoFront : geoRear, mat);
      pivot.add(mesh);
      root.add(pivot);
      wheels.push({ pivot, tyre: mesh, radius: r, front });
    }
  }

  // Steering wheel on a short column, tilted toward the driver.
  const steering = new THREE.Group();
  steering.position.set(0, 0.92, 0.3);
  steering.rotation.x = -0.45;
  const sw = new Parts();
  sw.add(ring(0.16, 0.03, 14), PALETTE.ink);
  sw.add(ball(8), paint.trim, { s: [0.06, 0.06, 0.04] });
  for (const a of [Math.PI / 2, Math.PI / 2 + 2.1, Math.PI / 2 - 2.1])
    sw.add(tube(1, 1, 5), PALETTE.ink, {
      p: [Math.cos(a) * 0.08, Math.sin(a) * 0.08, 0],
      r: [0, 0, a - Math.PI / 2],
      s: [0.016, 0.16, 0.016],
    });
  sw.add(tube(1, 1, 6), PALETTE.ink, {
    p: [0, -0.04, 0.16],
    r: [Math.PI / 2 - 0.3, 0, 0],
    s: [0.03, 0.32, 0.03],
  });
  steering.add(new THREE.Mesh(sw.build(), mat));
  body.add(steering);

  return {
    root,
    body,
    wheels,
    steering,
    grips: [new THREE.Vector3(0.145, 0.06, -0.01), new THREE.Vector3(-0.145, 0.06, -0.01)],
    seat: new THREE.Vector3(0, 0.62, -0.3),
    exhaust: new THREE.Vector3(0, 0.46, -1.25),
  };
}
