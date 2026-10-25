/**
 * Anything solid over the road? For each route point (and 4 m either side), a ray up from
 * just above the road: hits under 5 m are a wall or roof poking into the road.
 *   AUDIT_FILE=tools/audit/overhead.audit.ts AUDIT_TRACK=aurora_rift npx vitest run -c tools/audit/vitest.config.ts --silent=false
 */
import { readFile } from "node:fs/promises";
import { it } from "vitest";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import * as THREE from "three";

const T = process.env.AUDIT_TRACK ?? "aurora_rift";
it("overhead", async () => {
  const b = await readFile(new URL(`../../public/tracks/${T}/collision.glb`, import.meta.url));
  const scene = (
    await new GLTFLoader().parseAsync(
      b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer,
      "",
    )
  ).scene;
  scene.updateMatrixWorld(true);
  const route = JSON.parse(
    await readFile(new URL(`../../public/tracks/${T}/route.json`, import.meta.url), "utf8"),
  );
  const pts = (route.routes[0].points as { x: number; y: number; z: number }[]).map((q) => [
    q.x,
    q.y,
    q.z,
  ]);
  const rc = new THREE.Raycaster();
  rc.far = 5;
  let d = 0;
  for (let i = 0; i < pts.length; i++) {
    const [x, y, z] = pts[i]!;
    const [nx, , nz] = pts[(i + 1) % pts.length]!;
    if (i) d += Math.hypot(x! - pts[i - 1]![0]!, z! - pts[i - 1]![2]!);
    const fx = nx! - x!,
      fz = nz! - z!;
    const l = Math.hypot(fx, fz) || 1;
    for (const side of [-4, 0, 4]) {
      const px = x! + (-fz / l) * side,
        pz = z! + (fx / l) * side;
      rc.set(new THREE.Vector3(px, y! + 0.6, pz), new THREE.Vector3(0, 1, 0));
      const h = rc.intersectObject(scene, true)[0];
      if (h)
        console.log(
          "over",
          d.toFixed(0),
          side,
          h.distance.toFixed(1),
          h.object.name,
          px.toFixed(0),
          y!.toFixed(0),
          pz.toFixed(0),
        );
    }
  }
});
