/**
 * What's under a point? Lists every surface of a track's collision (and visual) straight
 * below game (x, z), top first, with the object's name: for finding invisible floors.
 *
 *   AT=-246,-47.5 AUDIT_FILE=tools/audit/probe.audit.ts AUDIT_TRACK=cascade_caverns \
 *     npx vitest run --config tools/audit/vitest.config.ts --disableConsoleIntercept
 */
import { readFile } from "node:fs/promises";
import { it } from "vitest";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { buildCollisionMesh } from "../../src/world/collisionMesh";
import * as THREE from "three";

const T = process.env.AUDIT_TRACK ?? "cascade_caverns";
async function load(f: string) {
  const b = await readFile(new URL(`../../public/tracks/${T}/${f}`, import.meta.url));
  const ab = b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
  return (await new GLTFLoader().parseAsync(ab, "")).scene;
}
it("probe", async () => {
  const [x, z] = (process.env.AT ?? "-246,-47.5").split(",").map(Number) as [number, number];
  for (const f of ["collision.glb", "visual.glb"]) {
    const s = await load(f).catch((e) => {
      console.log(f, "fail", e.message);
      return undefined;
    });
    if (!s) continue;
    s.updateMatrixWorld(true);
    const rc = new THREE.Raycaster(new THREE.Vector3(x, 200, z), new THREE.Vector3(0, -1, 0));
    const hits = rc.intersectObject(s, true);
    console.log(
      f,
      hits
        .slice(0, 8)
        .map((h) => `${h.point.y.toFixed(2)} ${h.object.name} (${h.object.parent?.name})`)
        .join(" | "),
    );
  }
}, 120000);
