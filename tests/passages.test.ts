// The ways between the worlds (Blake, Oct 27: out of the Burnt Gorge into the Snow
// Kingdom he couldn't get up the "hill" after the portal: the Gorge Road ran over the
// pockets' walls, 54 m high; and coming back from Desert World he spawned in a pillar:
// every journey's passages faced the wrong way, mirrored, into the gate behind you).
// From every passage, where the overworld puts you: on open ground, out of every wall,
// facing along the road, and flat out with the wheel straight you get well away. And
// no region's roads stand steeper than a kart can climb.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { REGIONS } from "../src/overworld/regions";
import { exitSpot } from "../src/overworld/exits";
import { stepVertical } from "../src/physics/vertical";
import { stepImpacts, stepMeshWalls } from "../src/physics/walls";
import { createKartState, stepKart, type KartConfig } from "../src/vehicles/kart";
import { applySurface, createMeshGround, deepestWall } from "../src/world/collisionMesh";
import { SURFACES, loadTrackPackage, type PackageReader } from "../src/world/trackPackage";

const dt = 1 / 120;
const cfg: KartConfig = { ...tuning.vehicle };
const wallCfg = { ...tuning.physics, ...tuning.collision, wallHeight: tuning.track.wallHeight };

const reader =
  (id: string): PackageReader =>
  async (file) => {
    const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
    return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
  };

const PACKAGES = REGIONS.filter((r) => r.kingdom || r.journey).flatMap((r) =>
  (r.ruinPackageId ? [false, true] : [false]).map((ruined) => ({
    r,
    ruined,
    id: ruined ? r.ruinPackageId! : r.packageId,
  })),
);

describe("the ways between the worlds", () => {
  for (const { r, ruined, id } of PACKAGES)
    it(`${id}: every passage and gateway puts you on the road, facing the way on`, async () => {
      const p = await loadTrackPackage(reader(id), { visual: false });
      const ground = createMeshGround(p.collision);
      const bad: string[] = [];
      // (Back out of a gateway after its race, too.)
      const ways = [
        ...(r.passages ?? []).filter((ps) => ruined || !ps.ruinOnly),
        ...r.gateways.filter((g) => ruined || !g.boss),
      ];
      for (const ps of ways) {
        // (As screens/overworld.ts puts you out of it.)
        const out = exitSpot(
          ps,
          (x, z) =>
            !deepestWall(p.collision, x, ground.at(x, z, 200).height, z, wallCfg.kartRadius),
        );
        const x0 = out.x;
        const z0 = out.z;
        const top = ground.at(x0, z0, 200);
        const floor = ground.at(ps.x, ps.z, 200);
        if (top.height > floor.height + 2) bad.push(`${ps.id}: on top of something`);
        if (deepestWall(p.collision, x0, top.height, z0, wallCfg.kartRadius))
          bad.push(`${ps.id}: in a wall`);
        const k = createKartState(x0, z0, ps.heading, top.height);
        for (let t = 0; t < 4; t += dt) {
          stepImpacts(k, tuning.collision, dt);
          const here = ground.at(k.x, k.z, k.y);
          const c = k.grounded && here.surface ? applySurface(cfg, SURFACES[here.surface]) : cfg;
          const px = k.x;
          const pz = k.z;
          stepKart(k, { throttle: 1, brake: 0, steer: 0, drift: false, item: false }, c, dt);
          stepMeshWalls(k, p.collision, wallCfg, dt, { x: px, z: pz });
          stepVertical(k, ground, tuning.physics, dt);
        }
        const moved = Math.hypot(k.x - x0, k.z - z0);
        if (moved < 30) bad.push(`${ps.id}: only ${moved.toFixed(0)} m in 4 s flat out`);
      }
      expect(bad).toEqual([]);
    });

  for (const { r, ruined, id } of PACKAGES)
    it(`${id}: every gateway's arch stands clear of walls`, async () => {
      // (Blake, Oct 27: Hearthglow's stood three quarters inside a villager's house.)
      const p = await loadTrackPackage(reader(id), { visual: false });
      const ground = createMeshGround(p.collision);
      const bad: string[] = [];
      for (const g of r.gateways) {
        if (g.boss && !ruined) continue;
        let blocked = 0;
        let n = 0;
        for (let a = 0; a < 16; a++)
          for (const rr of [0, g.radius * 0.5, g.radius]) {
            const x = g.x + Math.sin((a * Math.PI) / 8) * rr;
            const z = g.z + Math.cos((a * Math.PI) / 8) * rr;
            n++;
            if (deepestWall(p.collision, x, ground.at(x, z, 200).height, z, 0.6)) blocked++;
          }
        if (blocked > n * 0.15) bad.push(`${g.id}: ${Math.round((100 * blocked) / n)}% in walls`);
      }
      expect(bad).toEqual([]);
    });

  for (const { id } of PACKAGES)
    it(`${id}: no road steeper than a kart can climb`, async () => {
      const p = await loadTrackPackage(reader(id), { visual: false });
      const f = p.collision.floors;
      const q = f.pos;
      const steep: string[] = [];
      for (let t = 0; t < f.count; t++) {
        if (!/road|bridge/.test(p.collision.surfaces[f.surf[t]!]!)) continue;
        const o = t * 9;
        const ux = q[o + 3]! - q[o]!,
          uy = q[o + 4]! - q[o + 1]!,
          uz = q[o + 5]! - q[o + 2]!;
        const vx = q[o + 6]! - q[o]!,
          vy = q[o + 7]! - q[o + 1]!,
          vz = q[o + 8]! - q[o + 2]!;
        const nx = uy * vz - uz * vy,
          ny = uz * vx - ux * vz,
          nz = ux * vy - uy * vx;
        const l = Math.hypot(nx, ny, nz);
        // (Steeper than 37°: the Gorge Road's wall was 56°.)
        if (l > 1e-9 && Math.abs(ny) / l < 0.8)
          steep.push(`${q[o]!.toFixed(0)}, ${q[o + 1]!.toFixed(1)}, ${q[o + 2]!.toFixed(0)}`);
      }
      expect(steep.slice(0, 5)).toEqual([]);
    });
});
