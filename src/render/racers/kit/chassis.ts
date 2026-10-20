/**
 * The kart family: one shared chassis that every racer's kart is built on.
 *
 * All karts share the same wheel spots and sizes, seat, steering wheel, hand grips,
 * exhaust and footprint, so they drive, collide and film identically (and match the
 * physics, which never looks at any of this). What differs is the body kit on top: its
 * shapes, paint, emblem and gear, and the tyre and hub colours.
 *
 * Local frame: +Z forward, +Y up, origin on the ground under the kart's centre.
 */
import * as THREE from "three";
import { Build, box, cyl, lowDetail, torus, tyre } from "./shapes";
import { facetMaterial } from "./paint";

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

/** The shared measurements. Change these and every kart changes together. */
export const CHASSIS = {
  wheels: [
    { x: 0.76, z: 0.88, r: 0.36, front: true },
    { x: -0.76, z: 0.88, r: 0.36, front: true },
    { x: 0.8, z: -0.78, r: 0.42, front: false },
    { x: -0.8, z: -0.78, r: 0.42, front: false },
  ],
  tyreWidth: 0.36,
  seat: [0, 0.5, -0.3] as const,
  steering: { at: [0, 0.9, 0.24] as const, tilt: -0.5, radius: 0.17 },
  grips: [
    [0.15, 0.03, -0.02],
    [-0.15, 0.03, -0.02],
  ] as const,
  exhaust: [0, 0.42, -1.32] as const,
  /** Overall size, for the body kits: keep inside this box (the collision circle). */
  length: 2.7,
  width: 1.96,
  /**
   * For reference: the physics treats every kart as a circle of tuning.json's
   * walls.kartRadius (0.9 m). The look never changes it.
   */
  /** Characters are big for their karts, like toys. */
  riderScale: 1.2,
};

export interface WheelLook {
  tyre: string;
  rim: string;
  cap: string;
  /** Polygon sides of the tyre (8 chunky .. 12 round). */
  sides?: number;
  /** A ring of bolts or glow on the hub. */
  ring?: string;
}

/** A racer's kart: the body kit on the shared chassis. */
export interface BodyKit {
  /** Add the body's shapes (detail 0 near, 1 far: skip the small stuff). */
  shell(b: Build, detail: 0 | 1): void;
  /** Extra meshes on the body (painted emblems and the like), near version only. */
  decorate?(body: THREE.Group): void;
  wheel: WheelLook;
  /** Steering wheel colour. */
  steering: string;
}

export function wheelGeometry(r: number, w: WheelLook, far = false) {
  const b = new Build();
  if (far)
    return b
      .add(tyre(r, CHASSIS.tyreWidth, 0.07, 6), w.tyre)
      .add(cyl(r * 0.6, r * 0.6, CHASSIS.tyreWidth + 0.02, 6), w.rim, { r: [0, 0, Math.PI / 2] })
      .build();
  b.add(tyre(r, CHASSIS.tyreWidth, 0.07, w.sides ?? 10), w.tyre);
  // Tread blocks round the tyre, chunky like the era's karts.
  const n = (w.sides ?? 10) + 2;
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2;
    b.add(new THREE.BoxGeometry(CHASSIS.tyreWidth * 0.86, 0.06, 0.09), w.tyre, {
      p: [0, Math.sin(a) * (r - 0.005), Math.cos(a) * (r - 0.005)],
      r: [-a, 0, 0],
    });
  }
  b.add(cyl(r * 0.6, r * 0.6, CHASSIS.tyreWidth + 0.02, 10), w.rim, { r: [0, 0, Math.PI / 2] });
  if (w.ring)
    b.add(torus(r * 0.44, 0.03, 4, 10), w.ring, { r: [0, Math.PI / 2, 0], p: [0.2, 0, 0] }).add(
      torus(r * 0.44, 0.03, 4, 10),
      w.ring,
      { r: [0, Math.PI / 2, 0], p: [-0.2, 0, 0] },
    );
  b.add(cyl(r * 0.2, r * 0.26, CHASSIS.tyreWidth + 0.08, 8), w.cap, { r: [0, 0, Math.PI / 2] });
  return b.build();
}

/** Build a kart: the shared chassis (wheels, steering, attachment points) plus a body kit. */
export function buildKart(kit: BodyKit, detail: 0 | 1 = 0): KartModel {
  const mat = facetMaterial();
  const root = new THREE.Group();
  root.name = "kart";
  const body = new THREE.Group();
  body.name = "kart body";
  root.add(body);
  const b = new Build();
  if (detail === 1) lowDetail(() => kit.shell(b, 1));
  else kit.shell(b, 0);
  const shell = b.build();
  body.add(new THREE.Mesh(shell, mat));
  if (detail === 0) kit.decorate?.(body);

  const front = wheelGeometry(CHASSIS.wheels[0]!.r, kit.wheel, detail === 1);
  const rear = wheelGeometry(CHASSIS.wheels[2]!.r, kit.wheel, detail === 1);
  const wheels: KartModel["wheels"] = [];
  if (detail === 1) {
    // Far away: one mesh, wheels baked in.
    const baked = new Build().addColored(shell);
    for (const w of CHASSIS.wheels)
      baked.addColored(w.front ? front : rear, { p: [w.x, w.r, w.z] });
    (body.children[0] as THREE.Mesh).geometry = baked.build();
  } else {
    for (const w of CHASSIS.wheels) {
      const pivot = new THREE.Group();
      pivot.position.set(w.x, w.r, w.z);
      const t = new THREE.Mesh(w.front ? front : rear, mat);
      pivot.add(t);
      root.add(pivot);
      wheels.push({ pivot, tyre: t, radius: w.r, front: w.front });
    }
  }

  // The steering wheel: a chunky rim with three spokes, on a short column.
  const steering = new THREE.Group();
  steering.name = "steering";
  steering.position.set(...CHASSIS.steering.at);
  steering.rotation.x = CHASSIS.steering.tilt;
  const sw = new Build()
    .add(torus(CHASSIS.steering.radius, 0.04, 5, 10), kit.steering, { r: [0, 0, Math.PI / 10] })
    .add(box(0.3, 0.05, 0.04, 0.012), kit.steering)
    .add(box(0.05, 0.16, 0.04, 0.012), kit.steering, { p: [0, -0.08, 0] })
    .add(cyl(0.05, 0.05, 0.05, 8), kit.steering, { r: [Math.PI / 2, 0, 0] })
    .add(cyl(0.035, 0.035, 0.34, 6), kit.steering, {
      p: [0, -0.05, 0.17],
      r: [Math.PI / 2 - 0.3, 0, 0],
    });
  steering.add(new THREE.Mesh(sw.build(), mat));
  body.add(steering);

  return {
    root,
    body,
    wheels,
    steering,
    grips: [new THREE.Vector3(...CHASSIS.grips[0]), new THREE.Vector3(...CHASSIS.grips[1])],
    seat: new THREE.Vector3(...CHASSIS.seat),
    exhaust: new THREE.Vector3(...CHASSIS.exhaust),
  };
}
