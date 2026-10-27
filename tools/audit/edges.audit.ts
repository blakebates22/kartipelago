/**
 * Onto the road from the side: from the land 10 m off each side of the road (every
 * ~10 m round the route), a kart at 18 m/s heads straight at it. Does it get on, or is
 * it stopped as if by a wall (Blake, Oct 27: in Desert World by Impact Depths, coming at
 * the road square on from a slope, he couldn't get on it)? Reports the stopped ones,
 * with how far the land there stands over or under the road's edge.
 *
 *   AUDIT_FILE=tools/audit/edges.audit.ts AUDIT_TRACK=desert_region[,other...] npx vitest run \
 *     --config tools/audit/vitest.config.ts --silent=false
 */
import { readFile } from "node:fs/promises";
import { it } from "vitest";
import tuning from "../../assets/data/tuning.json";
import { stepVertical } from "../../src/physics/vertical";
import { stepImpacts, stepMeshWalls } from "../../src/physics/walls";
import { createKartState, stepKart, type KartConfig } from "../../src/vehicles/kart";
import { applySurface, createMeshGround } from "../../src/world/collisionMesh";
import { buildTrack } from "../../src/world/track";
import { SURFACES, loadTrackPackage, type PackageReader } from "../../src/world/trackPackage";

const dt = 1 / 120;
const cfg: KartConfig = { ...tuning.vehicle };
const wallCfg = { ...tuning.physics, ...tuning.collision, wallHeight: tuning.track.wallHeight };

it("edges", async () => {
  for (const id of (process.env.AUDIT_TRACK ?? "desert_region").split(",")) {
    const reader: PackageReader = async (file) => {
      const b = await readFile(new URL(`../../public/tracks/${id}/${file}`, import.meta.url));
      return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
    };
    const p = await loadTrackPackage(reader, { visual: false });
    const track = buildTrack(p.trackData, tuning.track.sampleSpacing);
    const ground = createMeshGround(p.collision);
    const every = Math.max(1, Math.round(10 / tuning.track.sampleSpacing));
    let tried = 0;
    const stopped: string[] = [];
    let kerbs = 0;
    for (let i = 0; i < track.samples.length; i += every) {
      const s = track.samples[i]!;
      const half = s.width / 2;
      for (const side of [-1, 1]) {
        const x0 = s.pos.x + s.right.x * side * (half + 10);
        const z0 = s.pos.z + s.right.z * side * (half + 10);
        const g0 = ground.at(x0, z0, s.pos.y + 15);
        // (Only from open, drivable land, not far over or under the road.)
        if (!(g0.height > -999) || Math.abs(g0.height - s.pos.y) > 8) continue;
        const surf = g0.surface ? SURFACES[g0.surface] : undefined;
        if (!surf || surf.respawn || g0.surface === "wall" || g0.ny < 0.6) continue;
        const heading = Math.atan2(-s.right.x * side, -s.right.z * side);
        const k = createKartState(x0, z0, heading, g0.height);
        k.speed = 18;
        let hits = 0;
        let on = false;
        for (let t = 0; t < 2.5 && !on; t += dt) {
          stepImpacts(k, tuning.collision, dt);
          const here = ground.at(k.x, k.z, k.y);
          const c = k.grounded && here.surface ? applySurface(cfg, SURFACES[here.surface]) : cfg;
          const px = k.x;
          const pz = k.z;
          stepKart(k, { throttle: 1, brake: 0, steer: 0, drift: false, item: false }, c, dt);
          if (stepMeshWalls(k, p.collision, wallCfg, dt, { x: px, z: pz })) hits++;
          stepVertical(k, ground, tuning.physics, dt);
          const off = (k.x - s.pos.x) * s.right.x + (k.z - s.pos.z) * s.right.z;
          if (Math.abs(off) < half - 1 && Math.abs(k.y - s.pos.y) < 2) on = true;
        }
        tried++;
        if (!on && hits > 0) {
          // The land at the road's edge, against the road's edge.
          const ex = s.pos.x + s.right.x * side * (half + 1.5);
          const ez = s.pos.z + s.right.z * side * (half + 1.5);
          const ge = ground.at(ex, ez, s.pos.y + 15);
          // What stopped it: the walls within reach, their heights against the road.
          const w = p.collision.walls;
          const key = (cx: number, cz: number) => (cx + 32768) * 65536 + (cz + 32768);
          const near: string[] = [];
          let kerb = false;
          const seen = new Set<number>();
          for (let cx = Math.floor((k.x - 2) / 4); cx <= Math.floor((k.x + 2) / 4); cx++)
            for (let cz = Math.floor((k.z - 2) / 4); cz <= Math.floor((k.z + 2) / 4); cz++)
              for (const t of w.cells.get(key(cx, cz)) ?? []) {
                if (seen.has(t)) continue;
                seen.add(t);
                const o = t * 9;
                const xs = [w.pos[o]!, w.pos[o + 3]!, w.pos[o + 6]!];
                const ys = [w.pos[o + 1]!, w.pos[o + 4]!, w.pos[o + 7]!];
                const zs = [w.pos[o + 2]!, w.pos[o + 5]!, w.pos[o + 8]!];
                const mx = (xs[0]! + xs[1]! + xs[2]!) / 3;
                const mz = (zs[0]! + zs[1]! + zs[2]!) / 3;
                if (Math.hypot(mx - k.x, mz - k.z) > 3) continue;
                // (A low wall at the road's edge: the road's own side, a lip, a kerb.)
                if (Math.max(...ys) - s.pos.y < 1.6 && Math.max(...ys) - s.pos.y > -0.5)
                  kerb = true;
                near.push(
                  `${(Math.min(...ys) - s.pos.y).toFixed(2)}..${(Math.max(...ys) - s.pos.y).toFixed(2)}${p.collision.wallSurfaces ? "" : ""}`,
                );
              }
          if (kerb) kerbs++;
          stopped.push(
            `${kerb ? "KERB " : "     "}walls [${near.slice(0, 4).join(" ")}] s=${s.dist.toFixed(0)} ${side < 0 ? "left " : "right"} from (${x0.toFixed(1)}, ${g0.height.toFixed(1)}, ${z0.toFixed(1)}) slope ny ${g0.ny.toFixed(2)}: land at the edge ${(ge.height - s.pos.y).toFixed(2)} m vs road, stopped at (${k.x.toFixed(1)}, ${k.z.toFixed(1)}) wall steps ${hits}`,
          );
        }
      }
    }
    console.log(
      `${id}: ${tried} tries onto the road, ${stopped.length} stopped, ${kerbs} of them at a low wall by the road's edge`,
    );
    for (const l of stopped
      .filter((l) => l.startsWith("KERB"))
      .slice(0, Number(process.env.SHOW ?? 15)))
      console.log("  " + l);
  }
}, 600000);
