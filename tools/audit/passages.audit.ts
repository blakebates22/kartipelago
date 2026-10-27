/**
 * Every way between worlds, from the side you come out of it: where the overworld puts
 * you (screens/overworld.ts: the passage's spot, radius + 6 m along its heading, dropped
 * from 200 m), what's under you there, and a few seconds flat out with the wheel straight
 * (how far you get, on what, what you hit). For "I spawned in a pillar" and "I can't get
 * up the hill after the portal".
 *
 *   AUDIT_FILE=tools/audit/passages.audit.ts [REGIONS=snow_kingdom,...] npx vitest run \
 *     --config tools/audit/vitest.config.ts --silent=false
 */
import { readFile } from "node:fs/promises";
import { it } from "vitest";
import tuning from "../../assets/data/tuning.json";
import { REGIONS } from "../../src/overworld/regions";
import { exitSpot } from "../../src/overworld/exits";
import { stepVertical } from "../../src/physics/vertical";
import { stepImpacts, stepMeshWalls } from "../../src/physics/walls";
import { createKartState, stepKart, type KartConfig } from "../../src/vehicles/kart";
import { applySurface, createMeshGround, deepestWall } from "../../src/world/collisionMesh";
import { SURFACES, loadTrackPackage, type PackageReader } from "../../src/world/trackPackage";

const dt = 1 / 120;
const cfg: KartConfig = { ...tuning.vehicle };
const wallCfg = { ...tuning.physics, ...tuning.collision, wallHeight: tuning.track.wallHeight };

it("passages", async () => {
  const want = process.env.REGIONS?.split(",");
  for (const r of REGIONS) {
    if (want && !want.includes(r.id)) continue;
    for (const ruined of r.ruinPackageId ? [false, true] : [false]) {
      const id = ruined ? r.ruinPackageId! : r.packageId;
      const reader: PackageReader = async (file) => {
        const b = await readFile(new URL(`../../public/tracks/${id}/${file}`, import.meta.url));
        return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
      };
      const p = await loadTrackPackage(reader, { visual: false });
      const ground = createMeshGround(p.collision);
      // The gateways too (and the ruin's lair): how much of the arch is in a wall.
      for (const g of r.gateways) {
        if (g.boss && !ruined) continue;
        let blocked = 0;
        let n = 0;
        for (let a = 0; a < 16; a++)
          for (const rr of [0, g.radius * 0.5, g.radius]) {
            const x = g.x + Math.sin(a * 0.3927) * rr;
            const z = g.z + Math.cos(a * 0.3927) * rr;
            const gh = ground.at(x, z, 200).height;
            n++;
            if (deepestWall(p.collision, x, gh, z, 0.6)) blocked++;
          }
        console.log(
          `${blocked > n * 0.15 ? "BAD " : "ok  "}${id} gateway ${g.id}: ${Math.round((100 * blocked) / n)}% of its ring in walls`,
        );
      }
      const ways = [
        ...(r.passages ?? []).filter((ps) => ruined || !ps.ruinOnly),
        ...r.gateways.filter((g) => ruined || !g.boss).map((g) => ({ ...g, to: `(${g.track})` })),
      ];
      for (const ps of ways) {
        const out = exitSpot(
          ps,
          (x, z) =>
            !deepestWall(p.collision, x, ground.at(x, z, 200).height, z, wallCfg.kartRadius),
        );
        const x0 = out.x;
        const z0 = out.z;
        const top = ground.at(x0, z0, 200);
        const atPassage = ground.at(ps.x, ps.z, 200);
        const wall = deepestWall(p.collision, x0, top.height, z0, wallCfg.kartRadius);
        const k = createKartState(x0, z0, ps.heading, top.height);
        let hits = 0;
        let minY = k.y;
        let maxY = k.y;
        let surfaces = new Set<string>();
        for (let t = 0; t < 4; t += dt) {
          stepImpacts(k, tuning.collision, dt);
          const here = ground.at(k.x, k.z, k.y);
          const c = k.grounded && here.surface ? applySurface(cfg, SURFACES[here.surface]) : cfg;
          const px = k.x;
          const pz = k.z;
          stepKart(k, { throttle: 1, brake: 0, steer: 0, drift: false, item: false }, c, dt);
          if (stepMeshWalls(k, p.collision, wallCfg, dt, { x: px, z: pz })) hits++;
          stepVertical(k, ground, tuning.physics, dt);
          minY = Math.min(minY, k.y);
          maxY = Math.max(maxY, k.y);
          if (k.grounded && here.surface) surfaces.add(here.surface);
        }
        const moved = Math.hypot(k.x - x0, k.z - z0);
        const bad = moved < 40 || hits > 12 || top.height > atPassage.height + 2 || wall != null;
        console.log(
          `${bad ? "BAD " : "ok  "}${id} ${ps.id} -> ${ps.to}: spawn (${x0.toFixed(1)}, ${top.height.toFixed(1)}, ${z0.toFixed(1)}) on ${top.surface ?? "-"} (passage floor ${atPassage.height.toFixed(1)})${wall ? ` IN A WALL (out ${wall.out.toFixed(2)})` : ""}; 4 s flat out: ${moved.toFixed(0)} m, wall steps ${hits}, y ${minY.toFixed(1)}..${maxY.toFixed(1)}, on ${[...surfaces].join("/")}`,
        );
      }
    }
  }
}, 600000);
