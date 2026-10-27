/**
 * The chaos driver: drives a track (or every track) the way the race AI never does, to
 * find where a kart gets stuck, drops through a floor or gets flung. Hundreds of short
 * runs from random spots on and beside the road: flat out with boosts, random steering,
 * full lock into the walls, reversing, drift hops. Uses the race's own physics steps
 * (as tests/aiLap.ts does), so what it finds is what a kart finds.
 *
 *   AUDIT_FILE=tools/audit/chaos.audit.ts AUDIT_TRACK=valley_region [RUNS=300 SEED=1] \
 *     npx vitest run --config tools/audit/vitest.config.ts --silent=false
 *   ... AUDIT_TRACK=all   (every track in public/tracks)
 *
 * It reports, clustered into 6 m spots (worst first), with the distance along the lap:
 *   THROUGH  the kart went down through a floor (it was on or over it a step before, and
 *            is now under it).
 *   UNDER    the kart drove in under a floor's edge (one within 1.5 m over its head:
 *            a road's edge or a deck standing over the ground beside it).
 *   INWALL   pushed more than 0.7 m into a wall (by another kart, say): the next push
 *            out could put it through to the far side.
 *   FLUNG    thrown more than 4 m in one step (a collision push gone wrong). (Rising fast
 *            off a steep bank at full boost is just the physics: not counted.)
 *   STUCK    pinned: under 3 m driven in 4 s while trying forwards and back.
 *   RESPAWN  a checkpoint's respawn spot with its road standing over it (more than a step
 *            up from the route's height there): a respawn there drops under the road.
 *   VOID     fell out of the world from ground that wasn't off an edge of the course
 *            (more than 25 m from the road), or under the world's floor entirely.
 * Results also go to audit-out/chaos/<track>.json (git-ignored), for the baseline.
 */
import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import { it } from "vitest";
import tuning from "../../assets/data/tuning.json";
import { stepVertical } from "../../src/physics/vertical";
import { stepImpacts, stepMeshWalls } from "../../src/physics/walls";
import { createKartState, stepKart, type KartConfig } from "../../src/vehicles/kart";
import { startZipper } from "../../src/vehicles/zipper";
import { bumpKarts } from "../../src/physics/bump";
import {
  applySurface,
  createMeshGround,
  deepestWall,
  floorAt,
} from "../../src/world/collisionMesh";
import { buildTrack } from "../../src/world/track";
import { createRace } from "../../src/race/race";
import { SURFACES, loadTrackPackage, type PackageReader } from "../../src/world/trackPackage";

const dt = 1 / 120;
const cfg: KartConfig = { ...tuning.vehicle };
const wallCfg = { ...tuning.physics, ...tuning.collision, wallHeight: tuning.track.wallHeight };

/** A small seeded random (mulberry32). */
function rng(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

type Kind = "THROUGH" | "UNDER" | "INWALL" | "FLUNG" | "STUCK" | "VOID" | "RESPAWN";
interface Hit {
  kind: Kind;
  x: number;
  y: number;
  z: number;
  s: number;
  off: number;
  run: number;
  size: number;
}

async function chaos(id: string, runs: number, seed: number) {
  const reader: PackageReader = async (file) => {
    const b = await readFile(new URL(`../../public/tracks/${id}/${file}`, import.meta.url));
    return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
  };
  const p = await loadTrackPackage(reader, { visual: false });
  const track = buildTrack(p.trackData, tuning.track.sampleSpacing);
  const ground = createMeshGround(p.collision);
  const mesh = p.collision;
  const S = track.samples;
  const nearest = (x: number, y: number, z: number) => {
    let best = S[0]!;
    let bd = Infinity;
    for (const smp of S) {
      const d = (smp.pos.x - x) ** 2 + (smp.pos.z - z) ** 2 + ((smp.pos.y - y) * 2) ** 2;
      if (d < bd) {
        bd = d;
        best = smp;
      }
    }
    return { smp: best, d: Math.hypot(best.pos.x - x, best.pos.z - z) };
  };
  const R = rng(seed);
  const hits: Hit[] = [];
  // The respawn spots first (each checkpoint's, 4 m past it, at the route's height): a
  // spot whose road stands more than a step over it puts the kart down under the road.
  const race = createRace(track, tuning.race, 1);
  for (const g of race.course.flatMap((c) => c.gates)) {
    const r = g.respawn;
    const on = floorAt(mesh, r.x, r.z, r.y);
    const top = floorAt(mesh, r.x, r.z, r.y + 3);
    const lands = on ? on.height : -Infinity;
    if (top && top.height > lands + 0.3 && top.height > r.y + 0.3) {
      const n = nearest(r.x, r.y, r.z);
      hits.push({
        kind: "RESPAWN",
        x: r.x,
        y: r.y,
        z: r.z,
        s: n.smp.dist,
        off: 0,
        run: -1,
        size: top.height - lands,
      });
    }
  }
  let simmed = 0;
  interface Car {
    k: ReturnType<typeof createKartState>;
    mode: number;
    steer: number;
    steerTarget: number;
    nextTurn: number;
    nextBoost: number;
    reverseFor: number;
    drift: boolean;
    marks: { t: number; d: number }[];
    travelled: number;
    lastGood: { x: number; y: number; z: number };
    done: boolean;
    y0: number;
    px: number;
    pz: number;
  }
  for (let run = 0; run < runs; run++) {
    // Somewhere on or just beside the road, facing roughly along it (now and then any
    // way). Every third run is a pack of six, shoving each other as karts do in a race
    // (their bumps come after the walls and the ground, as in the game).
    const smp = S[Math.floor(R() * S.length)]!;
    const fwd = Math.atan2(smp.forward.x, smp.forward.z);
    const pack = run % 3 === 2 ? 6 : 1;
    const cars: Car[] = [];
    for (let j = 0; j < pack; j++) {
      const across = (R() * 2 - 1) * (smp.width / 2 + (pack > 1 ? 0 : 3));
      const ahead = pack > 1 ? (j - 2.5) * 3.5 : 0;
      const x0 = smp.pos.x + smp.right.x * across + smp.forward.x * ahead;
      const z0 = smp.pos.z + smp.right.z * across + smp.forward.z * ahead;
      const g0 = ground.at(x0, z0, smp.pos.y + 2);
      if (!Number.isFinite(g0.height) || Math.abs(g0.height - smp.pos.y) > 3) continue;
      const heading = R() < 0.15 ? R() * Math.PI * 2 : fwd + (R() - 0.5) * (pack > 1 ? 0.5 : 1.2);
      cars.push({
        k: createKartState(x0, z0, heading, g0.height),
        mode: pack > 1 ? R() * 0.75 : R(), // < .45 flat out, < .75 into the walls, else wild
        steer: 0,
        steerTarget: 0,
        nextTurn: 0,
        nextBoost: R() * 2,
        reverseFor: 0,
        drift: false,
        marks: [],
        travelled: 0,
        lastGood: { x: x0, y: g0.height, z: z0 },
        done: false,
        y0: g0.height,
        px: x0,
        pz: z0,
      });
    }
    if (!cars.length) continue;
    const seconds = 8 + R() * 8;
    for (let t = 0; t < seconds && cars.some((c) => !c.done); t += dt) {
      simmed += dt * cars.filter((c) => !c.done).length;
      for (const car of cars) {
        if (car.done) continue;
        const k = car.k;
        if (t >= car.nextTurn) {
          if (car.mode < 0.45) car.steerTarget = (R() * 2 - 1) * 0.7;
          else if (car.mode < 0.75) car.steerTarget = R() < 0.5 ? -1 : 1;
          else car.steerTarget = (R() * 2 - 1) * 1;
          car.nextTurn = t + 0.3 + R() * (car.mode < 0.75 ? 1.6 : 0.6);
          car.drift = R() < (car.mode < 0.45 ? 0.35 : 0.2);
        }
        car.steer += (car.steerTarget - car.steer) * Math.min(1, dt * 6);
        // Slow and getting nowhere: back off for a moment, the other lock.
        if (car.reverseFor <= 0 && Math.abs(k.speed) < 1.5 && t > 1 && R() < dt * 2)
          car.reverseFor = 0.6 + R();
        car.reverseFor -= dt;
        const back = car.reverseFor > 0;
        const input = {
          throttle: back ? 0 : 1,
          brake: back ? 1 : 0,
          steer: back ? -car.steer : car.steer,
          drift: !back && car.drift && k.grounded,
          item: false,
        };
        if (t >= car.nextBoost && !back) {
          startZipper(k, 1, cfg);
          car.nextBoost = t + 1.5 + R() * 3;
        }
        stepImpacts(k, tuning.collision, dt);
        let c = cfg;
        const here = ground.at(k.x, k.z, k.y);
        if (k.grounded && here.surface) c = applySurface(cfg, SURFACES[here.surface]);
        car.y0 = k.y;
        car.px = k.x;
        car.pz = k.z;
        stepKart(k, input, c, dt);
        stepMeshWalls(k, mesh, wallCfg, dt);
        stepVertical(k, ground, tuning.physics, dt);
      }
      if (cars.length > 1) {
        const live = cars.filter((c) => !c.done);
        bumpKarts(
          live.map((c) => c.k),
          tuning.physics.kartBump,
        );
      }
      for (const car of cars) {
        if (car.done) continue;
        const k = car.k;
        const report = (kind: Kind, size: number) => {
          const n = nearest(k.x, k.y, k.z);
          const off = (k.x - n.smp.pos.x) * n.smp.right.x + (k.z - n.smp.pos.z) * n.smp.right.z;
          hits.push({ kind, x: k.x, y: k.y, z: k.z, s: n.smp.dist, off, run, size });
          car.done = true;
        };
        // Under a floor: one within 1.5 m over the kart's head.
        const over = floorAt(mesh, k.x, k.z, k.y + 1.0);
        if (over && over.height > k.y + 0.3) {
          // (Down through it: the kart was over that height a step ago.)
          report(car.y0 >= over.height - 0.05 ? "THROUGH" : "UNDER", over.height - k.y);
          continue;
        }
        // Deep in a wall (the next step's push could put it out the far side).
        const w = deepestWall(mesh, k.x, k.y, k.z, 1.0);
        if (w && w.out > 0.7) {
          report("INWALL", w.out);
          continue;
        }
        const moved = Math.hypot(k.x - car.px, k.z - car.pz);
        if (Math.abs(k.y - car.y0) > 4 || moved > 4) {
          report("FLUNG", Math.max(Math.abs(k.y - car.y0), moved));
          continue;
        }
        if (k.grounded) {
          const surf = ground.at(k.x, k.z, k.y).surface;
          if (surf && SURFACES[surf]?.respawn) {
            car.done = true; // (lava, deep water: the game's respawn)
            continue;
          }
          car.lastGood = { x: k.x, y: k.y, z: k.z };
        }
        if (k.y < p.killY || ground.at(k.x, k.z, k.y).height === -1000) {
          const n = nearest(car.lastGood.x, car.lastGood.y, car.lastGood.z);
          if (n.d < 25) {
            car.done = true; // (off an edge of the course: the respawn)
            continue;
          }
          report("VOID", n.d);
          continue;
        }
        car.travelled += moved;
        car.marks.push({ t, d: car.travelled });
        while (car.marks.length && car.marks[0]!.t < t - 4) car.marks.shift();
        if (t > 5 && car.marks.length > 2 && car.travelled - car.marks[0]!.d < 3)
          report("STUCK", 4);
      }
    }
  }
  // Clustered by 6 m cells, worst first.
  const cells = new Map<string, { kind: Kind; n: number; size: number; at: Hit }>();
  for (const h of hits) {
    const key = `${h.kind}:${Math.round(h.x / 6)}:${Math.round(h.z / 6)}`;
    const c = cells.get(key);
    if (c) {
      c.n++;
      c.size = Math.max(c.size, h.size);
    } else cells.set(key, { kind: h.kind, n: 1, size: h.size, at: h });
  }
  const spots = [...cells.values()].sort((a, b) => b.n - a.n || b.size - a.size);
  const count = (k: Kind) => hits.filter((h) => h.kind === k).length;
  console.log(
    `${id}: ${runs} runs, ${simmed.toFixed(0)} s driven: through ${count("THROUGH")}, under ${count("UNDER")}, in wall ${count("INWALL")}, flung ${count("FLUNG")}, respawn ${count("RESPAWN")}, stuck ${count("STUCK")}, void ${count("VOID")} (${spots.length} spots)`,
  );
  for (const c of spots.slice(0, 20)) {
    const h = c.at;
    console.log(
      `  ${c.kind.padEnd(7)} x${String(c.n).padEnd(3)} at ${h.x.toFixed(1)}, ${h.y.toFixed(1)}, ${h.z.toFixed(1)}  s=${h.s.toFixed(0)} off=${h.off.toFixed(1)}  size ${c.size.toFixed(2)}`,
    );
  }
  await mkdir(new URL("../../audit-out/chaos/", import.meta.url), { recursive: true });
  await writeFile(
    new URL(`../../audit-out/chaos/${id}.json`, import.meta.url),
    JSON.stringify(
      {
        track: id,
        runs,
        seed,
        seconds: Math.round(simmed),
        spots: spots.map((c) => ({
          kind: c.kind,
          n: c.n,
          size: +c.size.toFixed(2),
          x: +c.at.x.toFixed(1),
          y: +c.at.y.toFixed(1),
          z: +c.at.z.toFixed(1),
          s: Math.round(c.at.s),
          off: +c.at.off.toFixed(1),
        })),
      },
      null,
      1,
    ),
  );
  return spots;
}

it("chaos", async () => {
  const want = process.env.AUDIT_TRACK ?? "valley_region";
  const runs = Number(process.env.RUNS ?? 300);
  const seed = Number(process.env.SEED ?? 1);
  let ids = [want];
  if (want === "all") {
    const dir = new URL("../../public/tracks/", import.meta.url);
    ids = [];
    for (const d of (await readdir(dir, { withFileTypes: true })).sort((a, b) =>
      a.name.localeCompare(b.name),
    )) {
      if (!d.isDirectory()) continue;
      const files = await readdir(new URL(`${d.name}/`, dir)).catch(() => [] as string[]);
      if (files.includes("collision.glb") && files.includes("track.json")) ids.push(d.name);
    }
  }
  for (const id of ids) {
    try {
      await chaos(id, runs, seed);
    } catch (e) {
      console.log(`${id}: failed: ${(e as Error).message}`);
    }
  }
}, 7_200_000);
