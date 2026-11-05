/**
 * The shanty band's instruments (Blake, Nov 5: the band on the beached bow in the Night
 * Bazaar, kept low-key): a fiddle tucked under the chin and its bow in the right hand, a
 * squeezebox between the hands (its bellows drawn open and pushed shut as they move), a
 * pair of drumsticks. Placed each frame from the player's hands and torso (world space),
 * so they follow whatever the gesture does (render/people/animate.ts: fiddle, squeeze,
 * drum).
 */
import * as THREE from "three";
import type { PersonRig } from "./people/rig";

export type Instrument = "fiddle" | "squeeze" | "drum";
export const INSTRUMENTS: readonly Instrument[] = ["fiddle", "squeeze", "drum"];

export interface InstrumentView {
  /** After the player's view has updated this frame. */
  update(): void;
  visible(on: boolean): void;
  dispose(): void;
}

const WOOD = "#7a4422";
const DARK = "#2a1a12";

function mat(color: string) {
  return new THREE.MeshLambertMaterial({ color });
}

export function createInstrumentView(
  parent: THREE.Object3D,
  rig: PersonRig,
  kind: Instrument,
): InstrumentView {
  const geos: THREE.BufferGeometry[] = [];
  const mats: THREE.Material[] = [];
  const mesh = (g: THREE.BufferGeometry, color: string) => {
    geos.push(g);
    const m = mat(color);
    mats.push(m);
    const o = new THREE.Mesh(g, m);
    o.castShadow = true;
    return o;
  };
  const objs: THREE.Object3D[] = [];
  const add = (o: THREE.Object3D) => {
    parent.add(o);
    objs.push(o);
    return o;
  };
  const tq = new THREE.Quaternion();
  const tp = new THREE.Vector3();
  const ts = new THREE.Vector3();
  const hl = new THREE.Vector3();
  const hr = new THREE.Vector3();
  const hands = () => {
    rig.arms[0]!.hand.getWorldPosition(hl);
    rig.arms[1]!.hand.getWorldPosition(hr);
    rig.torso.getWorldQuaternion(tq);
    rig.torso.getWorldScale(ts);
    return ts.x;
  };

  let update: () => void;
  if (kind === "fiddle") {
    // (its body, waist and scroll along +z, the neck reaching off toward the left hand)
    const body = new THREE.Group();
    const b1 = mesh(new THREE.SphereGeometry(0.1, 10, 6).scale(1, 0.4, 1.2), WOOD);
    const b2 = mesh(new THREE.SphereGeometry(0.08, 10, 6).scale(1, 0.4, 1.1), WOOD);
    b2.position.z = 0.15;
    const neck = mesh(new THREE.BoxGeometry(0.035, 0.03, 0.26).translate(0, 0.01, 0.34), DARK);
    const scroll = mesh(new THREE.SphereGeometry(0.03, 6, 4), DARK);
    scroll.position.set(0, 0.02, 0.48);
    body.add(b1, b2, neck, scroll);
    add(body);
    const bow = new THREE.Group();
    bow.add(mesh(new THREE.CylinderGeometry(0.008, 0.008, 0.66, 4).rotateZ(Math.PI / 2), DARK));
    bow.add(mesh(new THREE.BoxGeometry(0.62, 0.012, 0.012).translate(0, -0.03, 0), "#e8e0c8"));
    add(bow);
    const dir = new THREE.Vector3();
    update = () => {
      const s = hands();
      // (from under the chin, between the shoulders, out to the left hand)
      rig.neck.getWorldPosition(tp);
      dir.copy(hl).sub(tp);
      body.position.copy(tp).addScaledVector(dir, 0.3);
      body.position.y -= 0.02 * s;
      body.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), dir.normalize());
      body.scale.setScalar(s * 1.25);
      // (the bow across the strings, held at its frog)
      bow.position.copy(hr);
      bow.quaternion.copy(tq);
      bow.scale.setScalar(s);
    };
  } else if (kind === "squeeze") {
    const ends = [0, 1].map(() => {
      const g = new THREE.Group();
      g.add(mesh(new THREE.BoxGeometry(0.06, 0.24, 0.2), WOOD));
      const k = mesh(new THREE.BoxGeometry(0.065, 0.18, 0.14), "#e8dcc0");
      k.position.y = 0.0;
      g.add(k);
      add(g);
      return g;
    });
    const bellows = mesh(new THREE.BoxGeometry(1, 0.2, 0.16), "#6a2a20");
    add(bellows);
    const mid = new THREE.Vector3();
    update = () => {
      const s = hands();
      ends[0]!.position.copy(hl);
      ends[1]!.position.copy(hr);
      for (const e of ends) {
        e.quaternion.copy(tq);
        e.scale.setScalar(s);
      }
      mid.copy(hl).add(hr).multiplyScalar(0.5);
      bellows.position.copy(mid);
      bellows.quaternion.copy(tq);
      bellows.scale.set(Math.max(0.02, hl.distanceTo(hr) - 0.06 * s), s, s);
    };
  } else {
    const sticks = [0, 1].map(() =>
      add(mesh(new THREE.CylinderGeometry(0.012, 0.016, 0.38, 5).translate(0, 0.17, 0), "#d8c8a0")),
    );
    const tip = new THREE.Quaternion().setFromEuler(new THREE.Euler(1.8, 0, 0));
    update = () => {
      const s = hands();
      sticks.forEach((st, i) => {
        st.position.copy(i ? hr : hl);
        st.quaternion.copy(tq).multiply(tip);
        st.scale.setScalar(s);
      });
    };
  }
  return {
    update,
    visible(on) {
      for (const o of objs) o.visible = on;
    },
    dispose() {
      for (const o of objs) o.removeFromParent();
      for (const g of geos) g.dispose();
      for (const m of mats) m.dispose();
    },
  };
}
