/**
 * Boost effects in the world (visual only): light trails streaming from the rear wheels
 * while a boost pushes, in the boost's colour, and a burst when one kicks in (a
 * shockwave ring and a flash at the exhaust).
 *
 *   const fx = createBoostFx(scene);
 *   fx.update(i, kartRoot, { pushing, color, enhanced, rainbow }, seconds, dt);  // each kart, each frame
 */
import * as THREE from "three";

/** Points kept along each wheel's trail (about 0.3 s of history). */
const N = 12;
/** Where the trail comes from, in the kart's frame: low behind each rear wheel. */
const WHEELS: [number, number, number][] = [
  [0.8, 0.12, -1.05],
  [-0.8, 0.12, -1.05],
];

const WHITE = new THREE.Color("#ffffff");

export interface BoostLook {
  pushing: boolean;
  color: string;
  enhanced: boolean;
  /** The rainbow window (an enhanced boost's last moments). */
  rainbow: boolean;
}

interface Trail {
  pts: THREE.Vector3[];
  mesh: THREE.Mesh;
}

interface KartFx {
  trails: Trail[];
  wasPushing: boolean;
  burst: THREE.Group;
  burstAge: number;
  fade: number;
}

export function createBoostFx(scene: THREE.Object3D) {
  const karts: KartFx[] = [];
  const ringGeo = new THREE.TorusGeometry(1, 0.08, 6, 28);
  const flashGeo = new THREE.SphereGeometry(1, 12, 8);
  const tmp = new THREE.Vector3();
  const up = new THREE.Vector3();
  const color = new THREE.Color();

  function trailMesh(): THREE.Mesh {
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(N * 2 * 3), 3));
    g.setAttribute("color", new THREE.BufferAttribute(new Float32Array(N * 2 * 3), 3));
    const idx: number[] = [];
    for (let i = 0; i < N - 1; i++) {
      const a = i * 2;
      idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2);
    }
    g.setIndex(idx);
    const m = new THREE.Mesh(
      g,
      new THREE.MeshBasicMaterial({
        vertexColors: true,
        transparent: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        side: THREE.DoubleSide,
      }),
    );
    m.frustumCulled = false;
    m.visible = false;
    scene.add(m);
    return m;
  }

  function kartFx(i: number): KartFx {
    let k = karts[i];
    if (!k) {
      const burst = new THREE.Group();
      const ring = new THREE.Mesh(
        ringGeo,
        new THREE.MeshBasicMaterial({
          transparent: true,
          blending: THREE.AdditiveBlending,
          depthWrite: false,
        }),
      );
      ring.name = "ring";
      const flash = new THREE.Mesh(
        flashGeo,
        new THREE.MeshBasicMaterial({
          color: "#fff6d0",
          transparent: true,
          blending: THREE.AdditiveBlending,
          depthWrite: false,
        }),
      );
      flash.name = "flash";
      burst.add(ring, flash);
      burst.visible = false;
      scene.add(burst);
      k = {
        trails: WHEELS.map(() => ({ pts: [], mesh: trailMesh() })),
        wasPushing: false,
        burst,
        burstAge: 99,
        fade: 0,
      };
      karts[i] = k;
    }
    return k;
  }

  return {
    update(i: number, root: THREE.Object3D, look: BoostLook, seconds: number, dt: number) {
      const k = kartFx(i);
      root.updateMatrixWorld();
      // A boost just kicked in: the burst.
      if (look.pushing && !k.wasPushing) {
        k.burstAge = 0;
        root.localToWorld(k.burst.position.set(0, 0.45, -1.4));
        k.burst.quaternion.copy(root.getWorldQuaternion(new THREE.Quaternion()));
        const ring = k.burst.getObjectByName("ring") as THREE.Mesh;
        (ring.material as THREE.MeshBasicMaterial).color.set(look.color);
      }
      k.wasPushing = look.pushing;
      k.burstAge += dt;
      const b = k.burstAge / 0.4;
      k.burst.visible = b < 1;
      if (b < 1) {
        const ring = k.burst.getObjectByName("ring") as THREE.Mesh;
        ring.scale.setScalar(0.4 + b * 2.6);
        (ring.material as THREE.MeshBasicMaterial).opacity = 1 - b;
        const flash = k.burst.getObjectByName("flash") as THREE.Mesh;
        flash.scale.setScalar(0.5 + b * 1.4);
        (flash.material as THREE.MeshBasicMaterial).opacity = Math.max(0, 0.9 - b * 1.8);
      }
      // Trails: fade in while pushing, out after.
      k.fade = Math.max(0, Math.min(1, k.fade + (look.pushing ? dt * 6 : -dt * 3)));
      up.set(0, 1, 0).applyQuaternion(root.quaternion);
      k.trails.forEach((tr, w) => {
        root.localToWorld(tmp.set(...WHEELS[w]!));
        const head = tr.pts[0];
        if (!head || head.distanceToSquared(tmp) > 0.04) {
          tr.pts.unshift(tmp.clone());
          if (tr.pts.length > N) tr.pts.length = N;
        } else head.copy(tmp);
        tr.mesh.visible = k.fade > 0.01 && tr.pts.length > 1;
        if (!tr.mesh.visible) {
          if (!look.pushing) tr.pts.length = 0;
          return;
        }
        const pos = tr.mesh.geometry.getAttribute("position") as THREE.BufferAttribute;
        const col = tr.mesh.geometry.getAttribute("color") as THREE.BufferAttribute;
        const width = look.enhanced ? 0.26 : 0.19;
        for (let n = 0; n < N; n++) {
          const p = tr.pts[Math.min(n, tr.pts.length - 1)]!;
          const t = n / (N - 1);
          const wv = width * (1 - t * 0.7);
          pos.setXYZ(n * 2, p.x + up.x * wv, p.y + up.y * wv, p.z + up.z * wv);
          pos.setXYZ(n * 2 + 1, p.x - up.x * wv, p.y - up.y * wv, p.z - up.z * wv);
          // The rainbow window: the trail runs through every colour.
          if (look.rainbow) color.setHSL((seconds * 1.6 + t) % 1, 1, 0.6);
          else color.set(look.color).lerp(WHITE, (1 - t) * 0.2);
          const a = (1 - t) * k.fade;
          col.setXYZ(n * 2, color.r * a, color.g * a, color.b * a);
          col.setXYZ(n * 2 + 1, color.r * a, color.g * a, color.b * a);
        }
        pos.needsUpdate = true;
        col.needsUpdate = true;
      });
    },
    dispose() {
      for (const k of karts) {
        for (const tr of k.trails) {
          tr.mesh.removeFromParent();
          tr.mesh.geometry.dispose();
        }
        k.burst.removeFromParent();
      }
      ringGeo.dispose();
      flashGeo.dispose();
    },
  };
}

export type BoostFx = ReturnType<typeof createBoostFx>;
