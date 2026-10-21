/**
 * Desert World's moving scenery, drawn in code (original, a few dozen triangles each):
 * the ranch windmill's wheel and the birds circling over the canyon. Purely visual: the
 * timing is game/desert.ts.
 */
import * as THREE from "three";
import { birdAt, windmillAngle, type BirdsConfig, type WindmillConfig } from "../game/desert";

const disposeAll = (o: THREE.Object3D) =>
  o.traverse((m) => {
    if (m instanceof THREE.Mesh) {
      m.geometry.dispose();
      (Array.isArray(m.material) ? m.material : [m.material]).forEach((x) => x.dispose());
    }
  });

export interface WindmillView {
  update(t: number): void;
  dispose(): void;
}

/** A windmill wheel: a ring of tilted galvanised vanes round a hub, a red-tipped rim. */
export function createWindmillView(parent: THREE.Object3D, c: WindmillConfig): WindmillView {
  const root = new THREE.Group();
  root.position.set(c.x, c.y, c.z);
  root.rotation.y = c.heading;
  const wheel = new THREE.Group();
  root.add(wheel);
  const metal = new THREE.MeshLambertMaterial({ color: 0xc8ced4, flatShading: true });
  const red = new THREE.MeshLambertMaterial({ color: 0xc8302a, flatShading: true });
  const dark = new THREE.MeshLambertMaterial({ color: 0x4a4440, flatShading: true });
  const vanes = 16;
  const r = c.radius;
  for (let k = 0; k < vanes; k++) {
    const a = (k / vanes) * Math.PI * 2;
    const g = new THREE.BoxGeometry(0.05, r * 0.62, r * 0.22);
    const vane = new THREE.Mesh(g, metal);
    vane.position.set(0, Math.cos(a) * r * 0.62, Math.sin(a) * r * 0.62);
    vane.rotation.x = -a;
    vane.rotation.y = 0.45; // the pitch that catches the wind
    wheel.add(vane);
    const tip = new THREE.Mesh(new THREE.BoxGeometry(0.06, r * 0.12, r * 0.22), red);
    tip.position.set(0, Math.cos(a) * r * 0.98, Math.sin(a) * r * 0.98);
    tip.rotation.x = -a;
    tip.rotation.y = 0.45;
    wheel.add(tip);
  }
  const ring = new THREE.Mesh(new THREE.TorusGeometry(r * 0.32, 0.06, 4, 16), dark);
  ring.rotation.y = Math.PI / 2;
  wheel.add(ring);
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.3, 0.6, 8), dark);
  hub.rotation.z = Math.PI / 2;
  root.add(hub);
  parent.add(root);
  return {
    update(t) {
      wheel.rotation.x = windmillAngle(c, t);
    },
    dispose() {
      root.removeFromParent();
      disposeAll(root);
    },
  };
}

export interface BirdsView {
  update(t: number): void;
  dispose(): void;
}

/** A flock of big dark birds, soaring: each a body and two wings that beat now and then. */
export function createBirdsView(parent: THREE.Object3D, c: BirdsConfig): BirdsView {
  const root = new THREE.Group();
  const mat = new THREE.MeshLambertMaterial({
    color: 0x2a201c,
    side: THREE.DoubleSide,
    flatShading: true,
  });
  const wingGeo = new THREE.BufferGeometry();
  // One wing: a long, swept triangle-and-a-half out along +X.
  wingGeo.setAttribute(
    "position",
    new THREE.Float32BufferAttribute(
      [0, 0, 0.5, 2.6, 0, -0.1, 0, 0, -0.6, 2.6, 0, -0.1, 3.4, 0, -0.6, 0, 0, -0.6],
      3,
    ),
  );
  wingGeo.computeVertexNormals();
  const bodyGeo = new THREE.ConeGeometry(0.28, 1.8, 5).rotateX(Math.PI / 2);
  const birds = Array.from({ length: c.count }, () => {
    const b = new THREE.Group();
    b.add(new THREE.Mesh(bodyGeo, mat));
    const l = new THREE.Mesh(wingGeo, mat);
    const r = new THREE.Mesh(wingGeo, mat);
    r.scale.x = -1;
    b.add(l, r);
    b.scale.setScalar(1.6);
    root.add(b);
    return { b, l, r };
  });
  parent.add(root);
  return {
    update(t) {
      birds.forEach(({ b, l, r }, k) => {
        const s = birdAt(c, k, t);
        b.position.set(s.x, s.y, s.z);
        b.rotation.set(0, s.heading, s.bank, "YXZ");
        const flap = 0.12 + 0.55 * s.beat;
        l.rotation.z = flap;
        r.rotation.z = -flap;
      });
    },
    dispose() {
      root.removeFromParent();
      wingGeo.dispose();
      bodyGeo.dispose();
      mat.dispose();
    },
  };
}
