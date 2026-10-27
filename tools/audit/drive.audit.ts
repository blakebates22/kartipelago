/**
 * One kart, flat out from a spot, the wheel straight (STEER=1: steering for 12 m ahead
 * of its nearest route sample, roughly): where it gets to, how fast, and what it's
 * driving on, every half second. For "I can't get up this hill" reports.
 *
 *   AUDIT_FILE=tools/audit/drive.audit.ts AUDIT_TRACK=snow_region AT=x,z,heading \
 *     [SECONDS=20 REVERSE=1] npx vitest run --config tools/audit/vitest.config.ts --silent=false
 * REVERSE=1 follows the route backwards (for a passage that comes in against the lap).
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

it("drive", async () => {
  const id = process.env.AUDIT_TRACK!;
  const reader: PackageReader = async (file) => {
    const b = await readFile(new URL(`../../public/tracks/${id}/${file}`, import.meta.url));
    return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
  };
  const p = await loadTrackPackage(reader, { visual: false });
  const track = buildTrack(p.trackData, tuning.track.sampleSpacing);
  const S = track.samples;
  const ground = createMeshGround(p.collision);
  const [x0, z0, h0] = process.env.AT!.split(",").map(Number) as [number, number, number];
  const back = process.env.REVERSE === "1";
  const g0 = ground.at(x0, z0, 200);
  const k = createKartState(x0, z0, h0, g0.height);
  const seconds = Number(process.env.SECONDS ?? 20);
  const steerOn = process.env.STEER === "1";
  let next = 0;
  for (let t = 0; t < seconds; t += dt) {
    let bi = 0;
    let bd = Infinity;
    S.forEach((s, i) => {
      const d = (s.pos.x - k.x) ** 2 + (s.pos.z - k.z) ** 2 + 4 * (s.pos.y - k.y) ** 2;
      if (d < bd) {
        bd = d;
        bi = i;
      }
    });
    const ahead = Math.round(12 / tuning.track.sampleSpacing);
    const aim = S[(bi + (back ? -ahead : ahead) + S.length * 4) % S.length]!.pos;
    const want = Math.atan2(aim.x - k.x, aim.z - k.z);
    let err = want - k.heading;
    while (err > Math.PI) err -= 2 * Math.PI;
    while (err < -Math.PI) err += 2 * Math.PI;
    // (heading 0 faces +z; steering right turns towards -x... follow the sign the kart uses)
    const steer = steerOn ? Math.max(-1, Math.min(1, -err * 2)) : 0;
    const input = { throttle: 1, brake: 0, steer, drift: false, item: false };
    stepImpacts(k, tuning.collision, dt);
    let c = cfg;
    const here = ground.at(k.x, k.z, k.y);
    if (k.grounded && here.surface) c = applySurface(cfg, SURFACES[here.surface]);
    const px = k.x;
    const pz = k.z;
    stepKart(k, input, c, dt);
    stepMeshWalls(k, p.collision, wallCfg, dt, { x: px, z: pz });
    stepVertical(k, ground, tuning.physics, dt);
    if (t >= next) {
      next += 0.5;
      const g = ground.at(k.x, k.z, k.y + 0.5);
      console.log(
        `t ${t.toFixed(1)} (${k.x.toFixed(1)}, ${k.y.toFixed(2)}, ${k.z.toFixed(1)}) v ${k.speed.toFixed(1)} h ${k.heading.toFixed(2)} grounded ${k.grounded} ${g.surface ?? "-"} ny ${g.ny?.toFixed(2)} route s=${S[bi]!.dist.toFixed(0)} off ${Math.sqrt(bd).toFixed(1)}`,
      );
    }
  }
}, 120000);
