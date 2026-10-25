/**
 * A kart over a course's jump at several speeds (boosted or not): where it loses speed.
 *   AUDIT_FILE=tools/audit/jump.audit.ts AUDIT_TRACK=coral_cove npx vitest run -c tools/audit/vitest.config.ts --silent=false
 */
import { readFile } from "node:fs/promises";
import { it } from "vitest";
import tuning from "../../assets/data/tuning.json";
import { stepVertical } from "../../src/physics/vertical";
import { stepImpacts, stepMeshWalls } from "../../src/physics/walls";
import { applyCharacter, type Character } from "../../src/vehicles/character";
import roster from "../../assets/data/characters.json";
import { applyBoost, createKartState, stepKart, type KartConfig } from "../../src/vehicles/kart";
import { applySurface, createMeshGround } from "../../src/world/collisionMesh";
import { buildTrack } from "../../src/world/track";
import { buildZippers, enteredZipper } from "../../src/world/zippers";
import { activateBlue } from "../../src/items/boosts";
import type { ItemsConfig } from "../../src/items/config";
import { startZipper, ZIP } from "../../src/vehicles/zipper";
import { SURFACES, loadTrackPackage, type PackageReader } from "../../src/world/trackPackage";

it("jump", async () => {
  const id = process.env.AUDIT_TRACK ?? "coral_cove";
  const reader: PackageReader = async (file) => {
    const b = await readFile(new URL(`../../public/tracks/${id}/${file}`, import.meta.url));
    return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
  };
  const p = await loadTrackPackage(reader, { visual: false });
  const track = buildTrack(p.trackData, tuning.track.sampleSpacing);
  const zone = (p.meta.entities ?? []).find((e) => (e as { type: string }).type === "respawn") as {
    from: number;
  };
  const lip = zone.from + 20;
  const ch = roster.characters.find((c) => c.id === roster.default) as Character;
  const cfg = applyCharacter(tuning.vehicle as KartConfig, ch, tuning.stats);
  const wallCfg = { ...tuning.physics, ...tuning.collision, wallHeight: tuning.track.wallHeight };
  const dt = 1 / 120;
  const sAt = (d: number) =>
    track.samples.reduce((a, q) => (Math.abs(q.dist - d) < Math.abs(a.dist - d) ? q : a));
  for (const [mult, across, headDeg = 0] of (process.env.CASES
    ? JSON.parse(process.env.CASES)
    : [
        [1, 0],
        [1.15, 0],
        [1.25, 0],
        [1.3, 0],
        [1.4, 0],
        [1.6, 0],
        [1.25, -4],
        [1.25, 4],
        [1.6, 4],
        [1.6, -4],
      ]) as [number, number, number?][]) {
    const g = createMeshGround(p.collision);
    const pads = buildZippers(track, p.trackData.zippers ?? [], tuning.track);
    const useZip = mult < 0;
    const s0 = sAt(useZip ? lip - 45 : lip - 30);
    const h = Math.atan2(s0.forward.x, s0.forward.z);
    const rx = Math.cos(h),
      rz = -Math.sin(h);
    const k = createKartState(s0.pos.x + rx * across, s0.pos.z + rz * across, h, s0.pos.y + 0.5);
    k.y = g.at(k.x, k.z, k.y + 1).height;
    k.speed = cfg.topSpeed;
    if (mult > 1) applyBoost(k, cfg, mult, 2.0);
    let lifted = false;
    let boosted = false;
    let minV = Infinity,
      at = "";
    const log: string[] = [];
    for (let t = 0; t < 3.2; t += dt) {
      const near = track.samples.reduce((a, q) =>
        (q.pos.x - k.x) ** 2 + (q.pos.z - k.z) ** 2 < (a.pos.x - k.x) ** 2 + (a.pos.z - k.z) ** 2
          ? q
          : a,
      );
      const want = Math.atan2(near.forward.x, near.forward.z) + (headDeg * Math.PI) / 180;
      const err = Math.atan2(Math.sin(want - k.heading), Math.cos(want - k.heading));
      stepImpacts(k, tuning.collision, dt);
      let c = cfg;
      const here = g.at(k.x, k.z, k.y);
      if (k.grounded && here.surface) c = applySurface(cfg, SURFACES[here.surface]);
      if (process.env.BOOST_AT && !boosted && near.dist - lip >= Number(process.env.BOOST_AT)) {
        if (process.env.BLUE)
          activateBlue(
            k,
            Number(process.env.BLUE),
            Number(process.env.BLUE_THR ?? 1),
            c,
            tuning.items as unknown as ItemsConfig,
          );
        else applyBoost(k, cfg, Number(process.env.BOOST_MULT ?? 1.5), 1.2);
        boosted = true;
      }
      const v0 = k.speed;
      const thr =
        (useZip && mult === -2 && k.zipPhase === ZIP.ACTIVE) ||
        (process.env.BLUE_THR === "0" && boosted && k.zipPhase === ZIP.ACTIVE)
          ? 0
          : 1;
      stepKart(
        k,
        {
          throttle: thr,
          brake: 0,
          steer: Math.max(-1, Math.min(1, -err * 2)),
          drift: false,
          item: false,
        },
        c,
        dt,
      );
      if (useZip && enteredZipper(k, pads)) {
        startZipper(k, mult === -2 ? 0 : 1, c);
        lifted = true;
      }
      const wall = stepMeshWalls(k, p.collision, wallCfg, dt);
      stepVertical(k, g, tuning.physics, dt);
      const d = near.dist - lip;
      if (Math.round(t * 120) % 12 === 0 || wall || k.speed < v0 - 2)
        log.push(
          `  t ${t.toFixed(2)} xz ${k.x.toFixed(1)},${k.z.toFixed(1)} d ${d.toFixed(1)} v ${k.speed.toFixed(1)} y ${k.y.toFixed(2)} vy ${k.vy.toFixed(1)} gnd ${k.grounded} ${wall ? "WALL" : ""} ${k.speed < v0 - 2 ? "DROP " + (v0 - k.speed).toFixed(1) : ""} surf ${here.surface}`,
        );
      if (k.speed < minV && d > -10) {
        minV = k.speed;
        at = `d ${d.toFixed(1)}`;
      }
    }
    console.log(
      `${useZip ? (mult === -2 ? "zipper enhanced" : "zipper") + (lifted ? "" : " (missed)") : "boost x" + mult} across ${across} angle ${headDeg}: min speed ${minV.toFixed(1)} at ${at}`,
    );
    if (process.env.LOG) console.log(log.join("\n"));
  }
});
