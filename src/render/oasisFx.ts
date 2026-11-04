/**
 * Oasis Haven's boats, drawn in code (original, a few dozen triangles): a rounded hull
 * with a painted stripe, a mast and a striped lateen sail. Purely visual: the motion is
 * game/oasis.ts.
 */
import * as THREE from "three";
import { boatAt, type BoatConfig } from "../game/oasis";

export interface BoatView {
  /** Where it is now (for the wake). */
  readonly pos: THREE.Vector3;
  readonly heading: number;
  update(t: number): void;
  dispose(): void;
}

function sailTexture(colors: string[]) {
  const c = document.createElement("canvas");
  c.width = 32;
  c.height = 32;
  const g = c.getContext("2d")!;
  for (let k = 0; k < 8; k++) {
    g.fillStyle = colors[k % colors.length]!;
    g.fillRect(0, k * 4, 32, 4);
  }
  g.fillStyle = "#f0c040";
  g.fillRect(14, 12, 4, 8);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.magFilter = THREE.NearestFilter;
  return t;
}

export function createBoatView(parent: THREE.Object3D, c: BoatConfig): BoatView {
  const root = new THREE.Group();
  const body = new THREE.Group();
  root.add(body);
  const hullMat = new THREE.MeshLambertMaterial({ color: 0x8a5230, flatShading: true });
  const trimMat = new THREE.MeshLambertMaterial({
    color: new THREE.Color(c.colors[0]!),
    flatShading: true,
  });
  const deckMat = new THREE.MeshLambertMaterial({ color: 0xd8b07a, flatShading: true });
  // The hull: a boat-shaped prism, pointed at the bow (+Z), round-ish at the stern.
  const shape = new THREE.Shape();
  shape.moveTo(0, 3.2);
  shape.quadraticCurveTo(1.25, 1.6, 1.2, -0.6);
  shape.quadraticCurveTo(1.1, -2.4, 0, -2.6);
  shape.quadraticCurveTo(-1.1, -2.4, -1.2, -0.6);
  shape.quadraticCurveTo(-1.25, 1.6, 0, 3.2);
  const hullGeo = new THREE.ExtrudeGeometry(shape, {
    depth: 1.0,
    bevelEnabled: false,
    curveSegments: 4,
  })
    .rotateX(Math.PI / 2)
    .translate(0, 0.55, 0);
  const hull = new THREE.Mesh(hullGeo, hullMat);
  hull.scale.set(1, 1, 1);
  body.add(hull);
  const stripe = new THREE.Mesh(
    new THREE.ExtrudeGeometry(shape, { depth: 0.18, bevelEnabled: false, curveSegments: 4 })
      .rotateX(Math.PI / 2)
      .translate(0, 0.62, 0),
    trimMat,
  );
  stripe.scale.set(1.03, 1, 1.02);
  body.add(stripe);
  const deck = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.1, 3.6), deckMat);
  deck.position.set(0, 0.55, -0.2);
  body.add(deck);
  // The mast and a lateen sail on a long slanted yard; or (a rowing boat) the oars,
  // crates of cargo lashed amidships and a lantern on a pole at the stern.
  const row = c.rig === "row";
  const mastMat = new THREE.MeshLambertMaterial({ color: 0x5a3a20 });
  const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.09, 5.2, 5), mastMat);
  mast.position.set(0, 3.1, 0.4);
  const tex = sailTexture(c.colors);
  const sailMat = new THREE.MeshLambertMaterial({ map: tex, side: THREE.DoubleSide });
  const sailGeo = new THREE.BufferGeometry();
  sailGeo.setAttribute(
    "position",
    new THREE.Float32BufferAttribute([0, 0.9, 2.6, 0, 6.2, -1.6, 0, 1.0, -2.0], 3),
  );
  sailGeo.setAttribute("uv", new THREE.Float32BufferAttribute([1, 0, 0.5, 1, 0, 0], 2));
  sailGeo.computeVertexNormals();
  const sail = new THREE.Mesh(sailGeo, sailMat);
  sail.position.x = 0.15;
  const oars: THREE.Object3D[] = [];
  const glowMat = new THREE.MeshBasicMaterial({ color: 0xffc46a });
  if (!row) body.add(mast, sail);
  else {
    const oarGeo = new THREE.BoxGeometry(2.6, 0.06, 0.12).translate(1.3, 0, 0);
    for (const side of [-1, 1])
      for (const at of [0.9, -0.5]) {
        const pivot = new THREE.Group();
        pivot.position.set(side * 1.05, 0.95, at);
        const oar = new THREE.Mesh(oarGeo, mastMat);
        oar.rotation.y = side < 0 ? Math.PI : 0;
        oar.rotation.z = side * -0.35;
        pivot.add(oar);
        pivot.userData.side = side;
        body.add(pivot);
        oars.push(pivot);
      }
    const crateGeo = new THREE.BoxGeometry(0.8, 0.6, 0.8);
    for (const [x, z, y] of [
      [0.25, 0.3, 0.9],
      [-0.3, -0.4, 0.9],
      [0.0, -0.05, 1.35],
    ] as const) {
      const crate = new THREE.Mesh(crateGeo, deckMat);
      crate.position.set(x, y, z);
      crate.rotation.y = x * 2;
      body.add(crate);
    }
    // (all of it under 1.7 m: it rows under the harbour bridge's arch)
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 1.0, 4), mastMat);
    pole.position.set(0, 1.1, -2.2);
    const lamp = new THREE.Mesh(new THREE.BoxGeometry(0.28, 0.32, 0.28), glowMat);
    lamp.position.set(0, 1.6, -2.2);
    body.add(pole, lamp);
  }
  root.scale.setScalar(c.scale);
  parent.add(root);
  const pos = new THREE.Vector3();
  const view = {
    pos,
    heading: 0,
    update(t: number) {
      const s = boatAt(c, t);
      root.position.set(s.x, s.y, s.z);
      root.rotation.set(0, s.heading, 0);
      body.rotation.set(s.pitch, 0, s.heel);
      // The sail bellies a little in the gusts; the oars sweep, dip and lift.
      sail.rotation.y = 0.18 + 0.06 * Math.sin(t * 1.1 + c.start);
      for (const o of oars) {
        const k = t * 2.2 + c.start;
        o.rotation.y = 0.5 * Math.sin(k) * o.userData.side;
        o.rotation.z = 0.12 * Math.cos(k);
      }
      pos.set(s.x, s.y, s.z);
      view.heading = s.heading;
    },
    dispose() {
      root.removeFromParent();
      root.traverse((o) => {
        if (o instanceof THREE.Mesh) o.geometry.dispose();
      });
      [hullMat, trimMat, deckMat, mastMat, sailMat, glowMat].forEach((m) => m.dispose());
      tex.dispose();
    },
  };
  return view;
}
