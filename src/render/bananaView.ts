/**
 * Banana meshes, and the little burst when one is collected. Bananas are a curved
 * yellow arc with brown tips that spin and bob gently; a dropped banana tumbles while
 * it's in the air.
 */
import * as THREE from "three";
import type { BananaField, BananaPickup } from "../world/bananas";

export interface BananaLook {
  color: string;
  restHeight: number;
  /** Mesh scale (1 = about 1 m across). */
  size: number;
}

const BURST_SEC = 0.35;

function bananaMesh(body: THREE.Material, tip: THREE.Material) {
  const group = new THREE.Group();
  // An arc of a torus: about 130 degrees of a 0.45 m ring.
  const arc = new THREE.Mesh(new THREE.TorusGeometry(0.45, 0.13, 8, 16, 2.3), body);
  arc.rotation.z = (3 * Math.PI) / 2 - 1.15; // the lower part of the ring: curves up at the ends
  arc.position.y = 0.45; // ring centre: the lowest point of the banana sits at the group origin
  arc.castShadow = true;
  group.add(arc);
  for (const end of [0, 2.3]) {
    const a = end + arc.rotation.z;
    const nub = new THREE.Mesh(new THREE.SphereGeometry(0.07, 6, 4), tip);
    nub.position.set(Math.cos(a) * 0.45, 0.45 + Math.sin(a) * 0.45, 0);
    group.add(nub);
  }
  return group;
}

export function createBananaView(scene: THREE.Object3D, look: BananaLook) {
  const body = new THREE.MeshStandardMaterial({
    color: look.color,
    emissive: new THREE.Color(look.color),
    emissiveIntensity: 0.25,
    flatShading: true,
  });
  const tip = new THREE.MeshStandardMaterial({ color: "#5a3b1a" });
  const pool: THREE.Group[] = [];

  const burstGeo = new THREE.TorusGeometry(0.6, 0.06, 6, 20);
  const bursts: { mesh: THREE.Mesh; mat: THREE.MeshBasicMaterial; t: number }[] = [];

  return {
    /** A collect effect at this spot. */
    burst(p: BananaPickup) {
      const mat = new THREE.MeshBasicMaterial({ color: look.color, transparent: true });
      const mesh = new THREE.Mesh(burstGeo, mat);
      mesh.position.set(p.x, p.y + look.restHeight + 0.4, p.z);
      mesh.rotation.x = Math.PI / 2;
      scene.add(mesh);
      bursts.push({ mesh, mat, t: 0 });
    },

    render(field: BananaField, colors: BananaLook, seconds: number, frameSeconds: number) {
      body.color.set(colors.color);
      body.emissive.set(colors.color);
      const list = field.bananas;
      while (pool.length < list.length) {
        const m = bananaMesh(body, tip);
        scene.add(m);
        pool.push(m);
      }
      pool.forEach((m, i) => {
        const b = list[i];
        m.visible = Boolean(b?.active);
        if (!b || !b.active) return;
        const lift = b.settled ? colors.restHeight + Math.sin(seconds * 3 + i) * 0.08 : 0.2;
        m.position.set(b.x, b.y + lift, b.z);
        m.rotation.y = seconds * 2 + i;
        m.rotation.x = b.settled ? 0 : b.age * 9;
        // Pop in when (re)appearing.
        m.scale.setScalar(colors.size * Math.min(1, 0.3 + b.age * 3));
      });

      for (let k = bursts.length - 1; k >= 0; k--) {
        const fx = bursts[k]!;
        fx.t += frameSeconds;
        const f = fx.t / BURST_SEC;
        fx.mesh.scale.setScalar(1 + f * 2.5);
        fx.mat.opacity = Math.max(0, 1 - f);
        if (f >= 1) {
          scene.remove(fx.mesh);
          fx.mat.dispose();
          bursts.splice(k, 1);
        }
      }
    },
  };
}
