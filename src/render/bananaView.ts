/**
 * The pickups: dinosaur eggs (they play exactly like DKR-style bananas: the
 * code still calls them bananas). A cream egg speckled in the accent colour sits
 * upright in a little straw nest (dropped ones lie loose), turning slowly and rocking now and then as if
 * something inside is about to hatch; a dropped egg tumbles while it's in the air
 * (its nest stays behind). Collecting one gives a little ring burst.
 */
import * as THREE from "three";
import type { BananaField, BananaPickup } from "../world/bananas";

export interface BananaLook {
  /** The speckles and the collect burst. */
  color: string;
  restHeight: number;
  /** Mesh scale (1 = about 0.6 m across, 0.75 m tall). */
  size: number;
}

const BURST_SEC = 0.35;
const SHELL = new THREE.Color("#f6ecd2");
const H = 0.75;

/** The speckles: fixed directions on the shell and their sizes (radians). */
const SPECKS: [number, number, number][] = [
  [0.3, 0.9, 0.3],
  [1.9, 0.6, 0.26],
  [3.4, 1.1, 0.32],
  [4.6, 0.7, 0.24],
  [5.6, 1.3, 0.22],
  [1.0, 1.7, 0.3],
  [2.6, 1.9, 0.27],
  [4.1, 1.6, 0.3],
  [5.4, 2.1, 0.24],
  [0.2, 2.3, 0.22],
  [3.1, 2.5, 0.2],
  [1.6, 0.25, 0.2],
];

/** An egg: a lathed shell, wider below, with its speckle weights (0 shell .. 1 speck). */
function eggGeometry() {
  const pts: THREE.Vector2[] = [];
  const rings = 12;
  for (let k = 0; k <= rings; k++) {
    const th = (k / rings) * Math.PI;
    const r = 0.29 * Math.sin(th) * (1 + 0.13 * Math.cos(th));
    pts.push(new THREE.Vector2(Math.max(r, 1e-4), (H / 2) * (1 - Math.cos(th))));
  }
  const geo = new THREE.LatheGeometry(pts, 14).toNonIndexed();
  const pos = geo.getAttribute("position");
  const weight = new Float32Array(pos.count);
  const v = new THREE.Vector3();
  const d = new THREE.Vector3();
  const tri = new THREE.Vector3();
  // Weight per face (its centre), so the speckles are crisp flat-shaded patches.
  for (let i = 0; i < pos.count; i += 3) {
    tri.set(0, 0, 0);
    for (let j = 0; j < 3; j++) tri.add(v.fromBufferAttribute(pos, i + j));
    tri.multiplyScalar(1 / 3);
    tri.y -= H / 2;
    tri.normalize();
    let w = 0;
    for (const [lon, colat, size] of SPECKS) {
      d.set(Math.sin(colat) * Math.cos(lon), Math.cos(colat), Math.sin(colat) * Math.sin(lon));
      if (tri.angleTo(d) < size) w = 1;
    }
    weight[i] = weight[i + 1] = weight[i + 2] = w;
  }
  geo.setAttribute("color", new THREE.Float32BufferAttribute(new Float32Array(pos.count * 3), 3));
  geo.computeVertexNormals();
  return { geo, weight };
}

function paintEgg(geo: THREE.BufferGeometry, weight: Float32Array, accent: THREE.Color) {
  const col = geo.getAttribute("color") as THREE.BufferAttribute;
  const c = new THREE.Color();
  for (let i = 0; i < weight.length; i++) {
    c.copy(SHELL).lerp(accent, weight[i]! * 0.85);
    col.setXYZ(i, c.r, c.g, c.b);
  }
  col.needsUpdate = true;
}

/** A little straw nest: a squashed ring of straw and a few sticks poking out. */
function nestGeometry() {
  const parts: THREE.BufferGeometry[] = [];
  const ring = new THREE.TorusGeometry(0.3, 0.1, 5, 10);
  ring.rotateX(Math.PI / 2);
  ring.scale(1, 0.55, 1);
  ring.translate(0, 0.06, 0);
  parts.push(ring.toNonIndexed());
  for (let k = 0; k < 5; k++) {
    const a = (k / 5) * Math.PI * 2 + 0.4;
    const stick = new THREE.CylinderGeometry(0.018, 0.025, 0.42, 3);
    stick.rotateZ(Math.PI / 2 - 0.35);
    stick.rotateY(a);
    stick.translate(Math.cos(a) * 0.3, 0.1, -Math.sin(a) * 0.3);
    parts.push(stick.toNonIndexed());
  }
  // Merge by hand (no addons needed): positions and normals only.
  const pos: number[] = [];
  for (const g of parts) pos.push(...(g.getAttribute("position").array as Float32Array));
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  geo.computeVertexNormals();
  for (const g of parts) g.dispose();
  return geo;
}

export function createBananaView(scene: THREE.Object3D, look: BananaLook) {
  const egg = eggGeometry();
  let accent = "";
  const shell = new THREE.MeshStandardMaterial({
    vertexColors: true,
    emissive: new THREE.Color("#fff4dc"),
    emissiveIntensity: 0.22,
    flatShading: true,
    roughness: 0.7,
  });
  const nestGeo = nestGeometry();
  const straw = new THREE.MeshStandardMaterial({ color: "#b48a4c", flatShading: true });
  const pool: { egg: THREE.Mesh; nest: THREE.Mesh }[] = [];

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
      if (colors.color !== accent) {
        accent = colors.color;
        paintEgg(egg.geo, egg.weight, new THREE.Color(accent));
      }
      const list = field.bananas;
      while (pool.length < list.length) {
        const e = new THREE.Mesh(egg.geo, shell);
        e.castShadow = true;
        const n = new THREE.Mesh(nestGeo, straw);
        scene.add(e, n);
        pool.push({ egg: e, nest: n });
      }
      pool.forEach((m, i) => {
        const b = list[i];
        m.egg.visible = Boolean(b?.active);
        m.nest.visible = Boolean(b?.active && b.settled && b.placed);
        if (!b || !b.active) return;
        // Pop in when (re)appearing.
        const size = colors.size * Math.min(1, 0.3 + b.age * 3);
        const base = b.settled ? 0.08 : 0.2;
        m.egg.position.set(b.x, b.y + base, b.z);
        m.egg.scale.setScalar(size);
        if (b.settled) {
          m.egg.rotation.set(0, seconds * 1.2 + i, 0);
          // Every few seconds, a little wobble: something inside wants out.
          const k = (seconds * 0.45 + i * 0.37) % 1;
          const shake = k > 0.85 ? Math.sin((k - 0.85) * 120) * 0.16 * (1 - (k - 0.85) / 0.15) : 0;
          m.egg.rotation.z = shake + Math.sin(seconds * 1.7 + i) * 0.04;
          m.egg.position.y += 0.06 * Math.sin(seconds * 3 + i);
          m.nest.position.set(b.x, b.y + base - 0.05 * size, b.z);
          m.nest.scale.setScalar(size);
          m.nest.rotation.y = i * 1.3;
        } else {
          m.egg.rotation.set(b.age * 9, i, b.age * 5);
        }
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
