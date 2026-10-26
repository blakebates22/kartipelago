/**
 * Lava bombs: the chunks a volcano throws when it erupts (Ember Peak). Each is a little
 * tumbling lump of rock, glowing yellow-orange as it leaves the crater and cooling to a
 * dark red crust as it falls, trailing smoke behind it. (Blake's Ember Peak review: the
 * eruption's lava looked like sparks; these read as molten rock.)
 *
 * A fixed pool drawn as one instanced mesh. Purely visual: nothing reads them back.
 */
import * as THREE from "three";

export interface LavaBombs {
  /** Throw one: from (x, y, z) at (vx, vy, vz), `size` metres across, for `life` s. */
  emit(
    x: number,
    y: number,
    z: number,
    vx: number,
    vy: number,
    vz: number,
    size: number,
    life: number,
  ): void;
  /** Move them; `trail(x, y, z)` is called now and then along each one's path (smoke). */
  step(dt: number, trail?: (x: number, y: number, z: number) => void): void;
  dispose(): void;
}

const HOT = new THREE.Color(0xffd060);
const WARM = new THREE.Color(0xff6a18);
const COOL = new THREE.Color(0x4a1408);

export function createLavaBombs(parent: THREE.Object3D, max = 260, gravity = -16): LavaBombs {
  const geo = new THREE.IcosahedronGeometry(0.5, 0);
  const mat = new THREE.MeshBasicMaterial({ color: 0xffffff, fog: true });
  const mesh = new THREE.InstancedMesh(geo, mat, max);
  mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  mesh.count = 0;
  mesh.frustumCulled = false;
  mesh.name = "lava bombs";
  parent.add(mesh);
  const pos = new Float32Array(max * 3);
  const vel = new Float32Array(max * 3);
  const age = new Float32Array(max);
  const life = new Float32Array(max);
  const size = new Float32Array(max);
  const spin = new Float32Array(max * 2);
  const puff = new Float32Array(max);
  let n = 0;
  const m = new THREE.Matrix4();
  const q = new THREE.Quaternion();
  const e = new THREE.Euler();
  const s = new THREE.Vector3();
  const p = new THREE.Vector3();
  const c = new THREE.Color();

  return {
    emit(x, y, z, vx, vy, vz, sz, lf) {
      if (n >= max) return;
      const i = n++;
      pos.set([x, y, z], i * 3);
      vel.set([vx, vy, vz], i * 3);
      age[i] = 0;
      life[i] = lf;
      size[i] = sz;
      spin[i * 2] = (Math.random() - 0.5) * 6;
      spin[i * 2 + 1] = (Math.random() - 0.5) * 6;
      puff[i] = Math.random() * 0.15;
    },
    step(dt, trail) {
      let w = 0;
      for (let i = 0; i < n; i++) {
        age[i]! += dt;
        if (age[i]! >= life[i]!) continue;
        // Keep it (compacting the pool as we go).
        if (w !== i) {
          pos.copyWithin(w * 3, i * 3, i * 3 + 3);
          vel.copyWithin(w * 3, i * 3, i * 3 + 3);
          spin.copyWithin(w * 2, i * 2, i * 2 + 2);
          age[w] = age[i]!;
          life[w] = life[i]!;
          size[w] = size[i]!;
          puff[w] = puff[i]!;
        }
        vel[w * 3 + 1]! += gravity * dt;
        pos[w * 3]! += vel[w * 3]! * dt;
        pos[w * 3 + 1]! += vel[w * 3 + 1]! * dt;
        pos[w * 3 + 2]! += vel[w * 3 + 2]! * dt;
        puff[w]! -= dt;
        if (trail && puff[w]! <= 0) {
          puff[w] = 0.12 + Math.random() * 0.1;
          trail(pos[w * 3]!, pos[w * 3 + 1]!, pos[w * 3 + 2]!);
        }
        const u = age[w]! / life[w]!;
        e.set(age[w]! * spin[w * 2]!, age[w]! * spin[w * 2 + 1]!, 0);
        q.setFromEuler(e);
        const k = size[w]! * (1 - 0.25 * u);
        s.set(k, k * 0.8, k);
        p.set(pos[w * 3]!, pos[w * 3 + 1]!, pos[w * 3 + 2]!);
        m.compose(p, q, s);
        mesh.setMatrixAt(w, m);
        // Hot as it leaves, cooling to a dark crust as it falls.
        if (u < 0.35) c.copy(HOT).lerp(WARM, u / 0.35);
        else c.copy(WARM).lerp(COOL, Math.min(1, (u - 0.35) / 0.65));
        mesh.setColorAt(w, c);
        w++;
      }
      n = w;
      mesh.count = n;
      mesh.instanceMatrix.needsUpdate = true;
      if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    },
    dispose() {
      parent.remove(mesh);
      geo.dispose();
      mat.dispose();
      mesh.dispose();
    },
  };
}
