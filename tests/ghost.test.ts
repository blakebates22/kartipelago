// Time Trial ghosts (src/game/ghost.ts, src/app/ghostStore.ts): recording, packing,
// playback accuracy over a whole race, personal bests, and that recording never touches
// the kart it watches.
import { readFile } from "node:fs/promises";
import * as THREE from "three";
import { describe, expect, it } from "vitest";
import { createGhostStore, memoryBackend } from "../src/app/ghostStore";
import { tuning } from "../src/core/tuning";
import type { InputState } from "../src/core/input";
import {
  GHOST_FORMAT,
  blankSample,
  createRecorder,
  decodeGhost,
  encodeGhost,
  fingerprint,
  recordSplit,
  recordStep,
  sampleGhost,
  splitDelta,
  tiltOf,
  type Ghost,
  type GhostSample,
} from "../src/game/ghost";
import { createKartState, stepKart, wrapAngle, type KartConfig } from "../src/vehicles/kart";
import { loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const HZ = 30;
const dt = 1 / 120;

function ghostOf(samples: GhostSample[], over: Partial<Ghost["meta"]> = {}): Ghost {
  return {
    meta: {
      format: GHOST_FORMAT,
      track: "t",
      layout: "L",
      physics: "P",
      racer: "tiko",
      character: "allrounder",
      hz: HZ,
      total: 90,
      lapTimes: [30, 30, 30],
      splits: [5, 10, 15],
      t0: samples[0]?.t ?? 0,
      recordedAt: 0,
      ...over,
    },
    samples,
  };
}

const yawQ = (h: number) => new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), h);
const sampleAt = (t: number, x: number, y: number, z: number, h: number): GhostSample => {
  const q = yawQ(h);
  return { ...blankSample(), t, x, y, z, qx: q.x, qy: q.y, qz: q.z, qw: q.w };
};

describe("ghost recording", () => {
  it("takes a snapshot about 30 times a second, stamped with the race clock", () => {
    const rec = createRecorder(HZ);
    let clock = -1.333;
    for (let i = 0; i < 1200; i++) {
      recordStep(rec, clock, () => sampleAt(0, i, 0, 0, 0));
      clock += dt;
    }
    const n = rec.samples.length;
    expect(n).toBeGreaterThan(295);
    expect(n).toBeLessThan(305);
    expect(rec.samples[0]!.t).toBeCloseTo(-1.333, 6);
    for (let i = 1; i < n; i++) {
      const gap = rec.samples[i]!.t - rec.samples[i - 1]!.t;
      expect(gap).toBeGreaterThan(1 / HZ - dt - 1e-9);
      expect(gap).toBeLessThan(1 / HZ + dt + 1e-9);
    }
  });

  it("records each checkpoint's time once, in order", () => {
    const rec = createRecorder(HZ);
    recordSplit(rec, 1, 4.2);
    recordSplit(rec, 1, 4.3);
    recordSplit(rec, 3, 9.0); // two at once (a fast stretch): both get the moment
    expect(rec.splits).toEqual([4.2, 9.0, 9.0]);
    const g = ghostOf([sampleAt(0, 0, 0, 0, 0)], { splits: [5, 10, 15] });
    expect(splitDelta(g, 1, 4.6)).toBeCloseTo(-0.4, 6); // ahead
    expect(splitDelta(g, 2, 10.5)).toBeCloseTo(0.5, 6); // behind
    expect(splitDelta(g, 4, 20)).toBeUndefined();
  });

  it("never changes the kart it watches", () => {
    const cfg = tuning.vehicle as KartConfig;
    const run = (watch: boolean) => {
      const s = createKartState(0, 0, 0);
      s.speed = 20;
      const rec = createRecorder(HZ);
      const q = new THREE.Quaternion();
      for (let i = 0; i < 600; i++) {
        const input: InputState = {
          throttle: 1,
          brake: i > 200 && i < 320 ? 1 : 0,
          steer: i > 60 ? 1 : 0,
          drift: i > 60 && i < 400,
          item: false,
        };
        stepKart(s, input, cfg, dt);
        if (watch)
          recordStep(rec, i * dt, () => {
            tiltOf(s, q);
            return { ...blankSample(), x: s.x, y: s.y, z: s.z, roll: s.sharpRoll };
          });
      }
      return s;
    };
    expect(run(true)).toEqual(run(false));
  });
});

describe("ghost packing", () => {
  it("round-trips to the millimetre, and its rotations to a hair", () => {
    const S: GhostSample[] = [];
    for (let i = 0; i < 200; i++) {
      const s = sampleAt(-1 + i / HZ, 123.4567 + i * 0.7, -86.25 + i * 0.1, -512.3 + i, i * 0.05);
      Object.assign(s, {
        roll: -0.33,
        speed: 31.27,
        steer: -0.5,
        driftDir: -1,
        slip: 0.69,
        grounded: i % 7 !== 0,
        throttle: true,
        zipPhase: 2,
        zipEnhanced: true,
        zipTime: 1.2,
        zipSource: 3,
        spinTime: 0.4,
      });
      S.push(s);
    }
    const g = ghostOf(S);
    const back = decodeGhost(encodeGhost(g))!;
    expect(back.meta).toEqual(g.meta);
    expect(back.samples.length).toBe(S.length);
    back.samples.forEach((b, i) => {
      const a = S[i]!;
      expect(Math.abs(b.t - a.t)).toBeLessThan(1e-5);
      expect(Math.hypot(b.x - a.x, b.y - a.y, b.z - a.z)).toBeLessThan(0.001);
      const dot = Math.abs(a.qx * b.qx + a.qy * b.qy + a.qz * b.qz + a.qw * b.qw);
      expect(dot).toBeGreaterThan(0.99999);
      expect(b.roll).toBeCloseTo(a.roll, 3);
      expect(b.speed).toBeCloseTo(a.speed, 1);
      expect(b.driftDir).toBe(a.driftDir);
      expect(b.grounded).toBe(a.grounded);
      expect(b.zipPhase).toBe(2);
      expect(b.zipEnhanced).toBe(true);
      expect(b.zipSource).toBe(3);
    });
    // About 36 bytes a snapshot.
    expect(encodeGhost(g).length).toBeLessThan(200 * 40 + 600);
  });

  it("ignores ghosts from another format", () => {
    const g = ghostOf([sampleAt(0, 0, 0, 0, 0)], { format: GHOST_FORMAT + 1 });
    expect(decodeGhost(encodeGhost(g))).toBeUndefined();
  });
});

describe("ghost playback", () => {
  it("passes through every snapshot, and across a respawn cuts instead of sliding", () => {
    const S = [0, 1, 2, 3].map((i) => sampleAt(i / HZ, i * 1.0, 0, 0, 0));
    S.push(sampleAt(4 / HZ, 300, 0, 0, 0)); // put back at a checkpoint
    S.push(sampleAt(5 / HZ, 301, 0, 0, 0));
    const g = ghostOf(S);
    const out = blankSample();
    for (const s of S) {
      sampleGhost(g, s.t, out);
      expect(Math.abs(out.x - s.x)).toBeLessThan(1e-6);
    }
    sampleGhost(g, 3.5 / HZ, out);
    expect(out.x).toBe(3); // still where it was, until the moment it's put back
    sampleGhost(g, 4.5 / HZ, out);
    expect(out.x).toBeGreaterThan(300);
    // Before the start it waits on the line; after the end it's done.
    expect(sampleGhost(g, -5, out)).toBe(true);
    expect(out.x).toBe(0);
    expect(sampleGhost(g, 10, out)).toBe(false);
  });

  it("follows a whole recorded race to within a few centimetres between snapshots, jumps, drifts and all", async () => {
    // A real race: the AI round Oasis Haven (its dune-lip jump, the spiral, the
    // weaving camp, drifting), traced every physics step. The ghost keeps one step in
    // four (30 a second) and must land on all the others.
    const id = "oasis_haven";
    const reader: PackageReader = async (file) => {
      const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
      return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
    };
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, {
      laps: 3,
      surfaces: true,
      zippers: true,
      lapSeconds: 120,
      trace: dt,
    });
    expect(r.race.racers[0]!.lapTimes.length).toBe(3);
    const steps = r.path;
    const rec = createRecorder(HZ);
    for (const q of steps) recordStep(rec, q.t, () => sampleAt(0, q.x, q.y, q.z, q.h ?? 0));
    const g = decodeGhost(encodeGhost(ghostOf(rec.samples)))!;
    const out = blankSample();
    let worst = 0;
    let worstAir = 0;
    let worstTurn = 0;
    // (Up to the last snapshot: past it there's nothing to land on but the last pose.)
    const tLast = rec.samples.at(-1)!.t;
    for (let i = 1; i < steps.length - 1; i++) {
      const q = steps[i]!;
      if (q.t > tLast) break;
      sampleGhost(g, q.t, out);
      const err = Math.hypot(out.x - q.x, out.y - q.y, out.z - q.z);
      worst = Math.max(worst, err);
      if (Math.abs(q.y - steps[i - 1]!.y) > 0.05) worstAir = Math.max(worstAir, err);
      const h = 2 * Math.atan2(out.qy, out.qw); // yaw back out of the quaternion
      worstTurn = Math.max(worstTurn, Math.abs(wrapAngle(h - (q.h ?? 0))));
    }
    expect(worst).toBeLessThan(0.12);
    expect(worstAir).toBeLessThan(0.12);
    expect(worstTurn).toBeLessThan(0.06); // radians: under 3.5 degrees
  }, 240_000);

  it("reproduces the sharp turn (R+B): the arc, the roll onto two wheels and the slide", () => {
    const cfg = tuning.vehicle as KartConfig;
    const s = createKartState(0, 0, 0);
    s.speed = cfg.topSpeed;
    const rec = createRecorder(HZ);
    const truth: { t: number; x: number; z: number; roll: number; slip: number }[] = [];
    const q = new THREE.Quaternion();
    for (let i = 0; i < 240; i++) {
      const t = i * dt;
      const input: InputState = {
        throttle: 1,
        brake: i > 72 ? 1 : 0,
        steer: 1,
        drift: true,
        item: false,
      };
      stepKart(s, input, cfg, dt);
      const slip = wrapAngle(s.heading - s.velAngle);
      truth.push({ t, x: s.x, z: s.z, roll: s.sharpRoll, slip });
      recordStep(rec, t, () => {
        tiltOf(s, q);
        return {
          ...blankSample(),
          x: s.x,
          y: s.y,
          z: s.z,
          qx: q.x,
          qy: q.y,
          qz: q.z,
          qw: q.w,
          roll: s.sharpRoll,
          slip,
          driftDir: s.driftDir,
        };
      });
    }
    const g = ghostOf(rec.samples);
    const out = blankSample();
    expect(Math.min(...truth.map((p) => p.roll))).toBeLessThan(-0.3); // it did roll
    // (Up to the last snapshot: after it, the run is over and the ghost stops.)
    const end = g.samples[g.samples.length - 1]!.t;
    for (const p of truth.slice(1).filter((p) => p.t <= end)) {
      sampleGhost(g, p.t, out);
      // (Within 8 cm and 3.5 degrees of roll, even where the brake bites mid-arc.)
      expect(Math.hypot(out.x - p.x, out.z - p.z)).toBeLessThan(0.08);
      expect(Math.abs(out.roll - p.roll)).toBeLessThan(0.06);
      expect(Math.abs(wrapAngle(out.slip - p.slip))).toBeLessThan(0.03);
    }
  });
});

describe("personal best ghosts", () => {
  const run = (track: string, total: number, physics = "P") =>
    ghostOf(
      [0, 1, 2].map((i) => sampleAt(i / HZ, i, 0, 0, 0)),
      { track, total, physics },
    );

  it("keeps the first, ignores a slower run, takes a faster one, and survives a reload", async () => {
    const bytes = new Map<string, Uint8Array>();
    const store = createGhostStore(memoryBackend(bytes));
    expect(await store.load("oasis_haven", "L", "P")).toBeUndefined();
    expect(await store.offer(run("oasis_haven", 80))).toBe(true);
    expect((await store.load("oasis_haven", "L", "P"))?.meta.total).toBe(80);
    expect(await store.offer(run("oasis_haven", 81))).toBe(false);
    expect((await store.load("oasis_haven", "L", "P"))?.meta.total).toBe(80);
    expect(await store.offer(run("oasis_haven", 79.5))).toBe(true);
    // A refresh: a new store on the same saved bytes.
    const again = createGhostStore(memoryBackend(bytes));
    const g = await again.load("oasis_haven", "L", "P");
    expect(g?.meta.total).toBe(79.5);
    expect(g?.samples.length).toBe(3);
  });

  it("keeps each course (and each physics version) separate", async () => {
    const store = createGhostStore(memoryBackend());
    await store.offer(run("oasis_haven", 80));
    await store.offer(run("dry_gulch", 95));
    await store.offer(run("oasis_haven", 70, "P2"));
    expect((await store.load("oasis_haven", "L", "P"))?.meta.total).toBe(80);
    expect((await store.load("dry_gulch", "L", "P"))?.meta.total).toBe(95);
    expect((await store.load("oasis_haven", "L", "P2"))?.meta.total).toBe(70);
    expect(await store.load("dry_gulch", "L", "P2")).toBeUndefined();
  });

  it("never saves a broken run, and two saves at once can't let the slower win", async () => {
    const store = createGhostStore(memoryBackend());
    expect(await store.offer(run("oasis_haven", NaN))).toBe(false);
    expect(await store.offer(ghostOf([], { total: 50 }))).toBe(false);
    const [a, b] = await Promise.all([
      store.offer(run("oasis_haven", 60)),
      store.offer(run("oasis_haven", 65)),
    ]);
    expect([a, b]).toEqual([true, false]);
    expect((await store.load("oasis_haven", "L", "P"))?.meta.total).toBe(60);
  });

  it("fingerprints change when what they cover changes", () => {
    expect(fingerprint({ a: 1 })).toBe(fingerprint({ a: 1 }));
    expect(fingerprint({ a: 1 })).not.toBe(fingerprint({ a: 2 }));
  });
});
