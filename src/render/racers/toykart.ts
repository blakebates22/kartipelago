/**
 * The faceted "toy kart" shared by Bramble, Poppy and Otto: a rounded tub with big
 * goggly eyes on its nose, a chunky bill-shaped bumper, fenders over the wheels, a roll
 * hoop and dark octagonal tyres. Each racer gives it their own colours.
 */
import * as THREE from "three";
import type { KartModel } from "./kart";
import { Parts } from "./geo";
import { chamferBox, facetMaterial, gem, octTyre, taper } from "./faceted";

export interface ToyKartColors {
  body: string;
  /** Rear fenders (a shade of the body, or the trim). */
  bodyDark: string;
  /** Bill bumper, cockpit rim and roll hoop. */
  trim: string;
  tyre: string;
  hub: string;
  hubCap: string;
  wheel: string;
  seat: string;
}

export interface ToyKartShape {
  /** Bevel of the tub: bigger = rounder. */
  round?: number;
  /** Length of the bill sticking out at the front. */
  bill?: number;
}

const wheelGeo = (r: number, c: ToyKartColors) =>
  new Parts()
    .add(octTyre(r, 0.34, 0.07), c.tyre)
    .add(new THREE.CylinderGeometry(r * 0.62, r * 0.62, 0.36, 8), c.hub, { r: [0, 0, Math.PI / 2] })
    .add(new THREE.CylinderGeometry(r * 0.22, r * 0.26, 0.42, 8), c.hubCap, {
      r: [0, 0, Math.PI / 2],
    })
    .build();

export function buildToyKart(
  c: ToyKartColors,
  detail: 0 | 1 = 0,
  shape: ToyKartShape = {},
): KartModel {
  const mat = facetMaterial();
  const root = new THREE.Group();
  const body = new THREE.Group();
  root.add(body);
  const round = shape.round ?? 0.14;
  const bill = shape.bill ?? 0.55;

  const p = new Parts();
  p.add(chamferBox(0.9, 0.14, 2.1, 0.04), c.trim, { p: [0, 0.27, -0.05] });
  // A rounded tub, sloping down to the nose.
  p.add(taper(chamferBox(1.0, 0.5, 1.36, round), 0.84, 0.62), c.body, { p: [0, 0.5, 0.42] });
  // The chunky bill along the front, sticking out like a duck's.
  // A thick rounded lip: a flattened faceted ball, wider than it is long.
  p.add(gem(2), c.trim, { p: [0, 0.36, 0.98 + bill * 0.42], s: [0.56, 0.11, 0.18 + bill * 0.45] });
  // Cockpit sides with a trim rim.
  for (const side of [-1, 1]) {
    p.add(chamferBox(0.14, 0.4, 0.9, 0.05), c.body, { p: [side * 0.4, 0.52, -0.38] });
    p.add(chamferBox(0.13, 0.08, 0.88, 0.03), c.trim, { p: [side * 0.4, 0.74, -0.38] });
  }
  // Fenders over the wheels.
  for (const side of [-1, 1]) {
    p.add(taper(chamferBox(0.46, 0.3, 0.72, 0.1), 0.9, 0.7, 0.04), c.body, {
      p: [side * 0.76, 0.72, 0.84],
    });
    p.add(chamferBox(0.54, 0.46, 0.84, 0.12), c.bodyDark, { p: [side * 0.79, 0.68, -0.8] });
  }
  // Seat, and a roll hoop behind it.
  p.add(chamferBox(0.5, 0.1, 0.45, 0.03), c.seat, { p: [0, 0.44, -0.38] });
  p.add(chamferBox(0.52, 0.46, 0.1, 0.03), c.seat, { p: [0, 0.66, -0.62] });
  for (const side of [-1, 1])
    p.add(chamferBox(0.1, 0.52, 0.1, 0.03), c.trim, { p: [side * 0.3, 0.84, -0.7] });
  p.add(chamferBox(0.7, 0.1, 0.1, 0.03), c.trim, { p: [0, 1.09, -0.7] });
  for (const side of [-1, 1])
    p.add(new THREE.CylinderGeometry(0.08, 0.09, 0.3, 8), c.tyre, {
      p: [side * 0.2, 0.42, -1.18],
      r: [Math.PI / 2, 0, 0],
    });
  // Big goggly eyes on the nose, looking ahead.
  if (detail === 0) {
    for (const side of [-1, 1]) {
      p.add(gem(1), "#fffaf0", { p: [side * 0.2, 0.62, 0.86], s: [0.13, 0.13, 0.1] });
      p.add(gem(1), "#2b1d2a", { p: [side * 0.19, 0.62, 0.94], s: [0.07, 0.08, 0.04] });
      p.add(gem(0), "#fffaf0", { p: [side * 0.19 + 0.025, 0.66, 0.975], s: 0.018 });
    }
  }
  const shellGeo = p.build();
  body.add(new THREE.Mesh(shellGeo, mat));

  const spots: [number, number, number, boolean][] = [
    [0.76, 0.84, 0.36, true],
    [-0.76, 0.84, 0.36, true],
    [0.8, -0.8, 0.42, false],
    [-0.8, -0.8, 0.42, false],
  ];
  const front = wheelGeo(0.36, c);
  const rear = wheelGeo(0.42, c);
  const wheels: KartModel["wheels"] = [];
  if (detail === 1) {
    const baked = new Parts().addColored(shellGeo);
    for (const [x, z, r, f] of spots) baked.addColored(f ? front : rear, { p: [x, r, z] });
    (body.children[0] as THREE.Mesh).geometry = baked.build();
  } else {
    for (const [x, z, r, f] of spots) {
      const pivot = new THREE.Group();
      pivot.position.set(x, r, z);
      const tyre = new THREE.Mesh(f ? front : rear, mat);
      pivot.add(tyre);
      root.add(pivot);
      wheels.push({ pivot, tyre, radius: r, front: f });
    }
  }

  // A dark steering wheel: a chunky rim on a short column.
  const steering = new THREE.Group();
  steering.position.set(0, 0.86, 0.18);
  steering.rotation.x = -0.5;
  steering.add(
    new THREE.Mesh(
      new Parts()
        .add(new THREE.TorusGeometry(0.17, 0.045, 4, 8), c.wheel, { r: [0, 0, Math.PI / 8] })
        .add(chamferBox(0.07, 0.18, 0.05, 0.02), c.wheel, { p: [0, -0.07, 0] })
        .add(new THREE.CylinderGeometry(0.035, 0.035, 0.34, 6), c.wheel, {
          p: [0, -0.08, 0.17],
          r: [Math.PI / 2 - 0.3, 0, 0],
        })
        .build(),
      mat,
    ),
  );
  body.add(steering);

  return {
    root,
    body,
    wheels,
    steering,
    grips: [new THREE.Vector3(0.16, 0.04, -0.02), new THREE.Vector3(-0.16, 0.04, -0.02)],
    seat: new THREE.Vector3(0, 0.48, -0.36),
    exhaust: new THREE.Vector3(0, 0.42, -1.3),
  };
}
