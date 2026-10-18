import { readFile } from "node:fs/promises";
import * as THREE from "three";
import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { NEUTRAL, type InputState } from "../src/core/input";
import { flatGround } from "../src/physics/ground";
import { stepVertical } from "../src/physics/vertical";
import { stepImpacts, stepMeshWalls } from "../src/physics/walls";
import { createDriver, driveAi } from "../src/ai/driver";
import { buildRacingLine } from "../src/ai/racingLine";
import { createRace, stepRacer, tickRace } from "../src/race/race";
import { createKartState, stepKart, type KartConfig, type KartState } from "../src/vehicles/kart";
import { buildTrack } from "../src/world/track";
import {
  buildCollisionMesh,
  createMeshGround,
  NO_FLOOR,
  type CollisionMesh,
} from "../src/world/collisionMesh";
import {
  loadTrackPackage,
  parseRoute,
  parseTrackMeta,
  SURFACES,
  swapPackage,
  TrackError,
  type PackageReader,
  type TrackPackage,
} from "../src/world/trackPackage";

const DIR = new URL("../public/tracks/bridge_test/", import.meta.url);
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(file, DIR));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};
const dt = 1 / 120;
const cfg: KartConfig = { ...tuning.vehicle };
const wallCfg = { ...tuning.physics, ...tuning.collision, wallHeight: tuning.track.wallHeight };

let cached: TrackPackage | undefined;
const pkg = async () => (cached ??= await loadTrackPackage(reader, { visual: false }));

describe("track package files", () => {
  it("rejects bad metadata with a clear message", () => {
    expect(() => parseTrackMeta(null)).toThrow(TrackError);
    expect(() => parseTrackMeta({ id: "x" })).toThrow(/schemaVersion/);
    expect(() => parseTrackMeta({ schemaVersion: 99, id: "x", geometry: {} })).toThrow(/newer/);
    expect(() =>
      parseTrackMeta({ schemaVersion: 1, id: "x", geometry: { visual: "v.glb" } }),
    ).toThrow(/geometry.collision/);
    expect(() => parseRoute({ schemaVersion: 1, routes: [{ points: [] }] })).toThrow(
      /fewer than 3/,
    );
    expect(() =>
      parseRoute({
        schemaVersion: 1,
        routes: [{ points: [1, 2, 3].map(() => ({ x: 0, y: 0, z: 0, width: 12, bank: NaN })) }],
      }),
    ).toThrow(/bad bank/);
  });

  it("loads the Blender-exported Bridge Test with tagged surfaces and no warnings", async () => {
    const p = await pkg();
    expect(p.meta.id).toBe("bridge_test");
    expect(p.warnings).toEqual([]);
    expect(p.collision.floors.count).toBeGreaterThan(5000);
    expect(p.collision.walls.count).toBeGreaterThan(1000);
    expect(new Set(p.collision.surfaces)).toEqual(new Set(["asphalt", "dirt", "wall", "grass"]));
    expect(p.trackData.points.length).toBeGreaterThan(100);
  });
});

describe("imported collision", () => {
  it("puts the road surface where the route says, on the right layer", async () => {
    const p = await pkg();
    const ground = createMeshGround(p.collision);
    let worst = 0;
    for (const q of p.trackData.points) {
      const s = ground.at(q.x, q.z, (q.y ?? 0) + 0.2);
      expect(s.surface, `at ${q.x.toFixed(1)}, ${q.z.toFixed(1)}`).toBe("asphalt");
      worst = Math.max(worst, Math.abs(s.height - (q.y ?? 0)));
    }
    expect(worst).toBeLessThan(0.15);
  });

  it("keeps the lower road under the bridge and the bridge above it (G)", async () => {
    const p = await pkg();
    const pts = p.trackData.points;
    // The crossing: a high point and a low point at (almost) the same x/z.
    let best = { d: Infinity, hi: pts[0]!, lo: pts[0]! };
    for (const hi of pts)
      for (const lo of pts) {
        if ((hi.y ?? 0) - (lo.y ?? 0) < 5) continue;
        const d = Math.hypot(hi.x - lo.x, hi.z - lo.z);
        if (d < best.d) best = { d, hi, lo };
      }
    expect(best.d).toBeLessThan(2);
    const ground = createMeshGround(p.collision);
    const hi = { ...best.hi, y: best.hi.y ?? 0 };
    const lo = { ...best.lo, y: best.lo.y ?? 0 };
    expect(ground.at(lo.x, lo.z, lo.y).height).toBeCloseTo(lo.y, 0);
    expect(ground.at(lo.x, lo.z, lo.y).surface).toBe("asphalt");
    expect(ground.at(hi.x, hi.z, hi.y).height).toBeCloseTo(hi.y, 0);
    // Under the bridge, a kart's walls are the lower road's, not the deck's.
    expect(
      stepMeshWalls(createKartState(lo.x, lo.z, 0, lo.y), p.collision, wallCfg, dt),
    ).toBeNull();
  });

  it("banks the road the way the route says (positive bank = down to the right)", async () => {
    const p = await pkg();
    const track = buildTrack(p.trackData, tuning.track.sampleSpacing);
    const ground = createMeshGround(p.collision);
    let checked = 0;
    for (const s of track.samples) {
      const bank = Math.asin(Math.max(-1, Math.min(1, -s.right.y))) * (180 / Math.PI);
      if (Math.abs(bank) < 5) continue;
      const g = ground.at(s.pos.x, s.pos.z, s.pos.y + 0.2);
      // The surface normal leans toward the low side.
      const lean = g.nx * s.right.x + g.nz * s.right.z;
      expect(Math.sign(lean)).toBe(Math.sign(bank));
      checked++;
    }
    expect(checked).toBeGreaterThan(20);
  });

  it("has no floor off the edge of the world", async () => {
    const p = await pkg();
    const g = createMeshGround(p.collision);
    expect(g.at(p.collision.bounds.maxX + 50, 0, 0).height).toBe(NO_FLOOR);
  });
});

/** Drive one kart round the imported track with the race's own AI driver. */
async function aiLap() {
  const p = await pkg();
  const track = buildTrack(p.trackData, tuning.track.sampleSpacing);
  const line = buildRacingLine(track, {
    margin: tuning.ai.lineMargin,
    span: tuning.ai.lineSpan,
    iterations: tuning.ai.lineIterations,
  });
  const race = createRace(track, tuning.race, 1);
  const driver = createDriver(line, 1, tuning.ai);
  const ground = createMeshGround(p.collision);
  const start = track.start;
  const k = createKartState(start.x, start.z, start.heading, track.samples[0]!.pos.y);
  k.y = ground.at(k.x, k.z, k.y + 0.5).height;
  let lowest = Infinity;
  let worstAbove = 0;
  let walls = 0;
  for (let t = 0; t < 90 && !race.racers[0]!.lapTimes.length; t += dt) {
    tickRace(race, dt);
    const input = driveAi(driver, k, cfg, tuning.ai, {
      countdown: race.phase === "countdown",
      clock: race.clock,
      startTarget: -1,
    });
    stepImpacts(k, tuning.collision, dt);
    stepKart(k, race.phase === "countdown" ? NEUTRAL : input, cfg, dt);
    if (stepMeshWalls(k, p.collision, wallCfg, dt)) walls++;
    stepVertical(k, ground, tuning.physics, dt);
    stepRacer(race, 0, k, ground.at(k.x, k.z, k.y).onRoad, input.throttle, tuning.race, dt);
    lowest = Math.min(lowest, k.y);
    // How far above the nearest route point's height the kart is (wrong layer = ~8 m).
    if (k.grounded) {
      let near = track.samples[0]!;
      let nd = Infinity;
      for (const s of track.samples) {
        const d = (s.pos.x - k.x) ** 2 + (s.pos.z - k.z) ** 2 + ((s.pos.y - k.y) * 3) ** 2;
        if (d < nd) {
          nd = d;
          near = s;
        }
      }
      worstAbove = Math.max(worstAbove, Math.abs(k.y - near.pos.y));
    }
  }
  return { race, lowest, worstAbove, walls, killY: p.killY };
}

describe("driving an imported track", () => {
  it("drives a full lap on the Blender track with the existing physics (A, E)", async () => {
    const r = await aiLap();
    const racer = r.race.racers[0]!;
    expect(racer.lapTimes).toHaveLength(1);
    expect(racer.passed).toBe(r.race.gates.length);
    expect(r.lowest).toBeGreaterThan(r.killY);
    // Never dropped through the bridge or popped up onto it.
    expect(r.worstAbove).toBeLessThan(1.5);
    // A clean line touches no walls: nothing invisible stands in the road.
    expect(r.walls).toBeLessThan(60);
  }, 30000);

  it("keeps a kart inside the barriers when it steers straight at one", async () => {
    const p = await pkg();
    const track = buildTrack(p.trackData, tuning.track.sampleSpacing);
    const s = track.samples[20]!;
    const right = Math.atan2(s.right.x, s.right.z);
    const k = createKartState(s.pos.x, s.pos.z, right, s.pos.y);
    k.speed = 20;
    k.velAngle = right;
    const ground = createMeshGround(p.collision);
    let hit = false;
    for (let t = 0; t < 2; t += dt) {
      stepImpacts(k, tuning.collision, dt);
      stepKart(k, { ...NEUTRAL, throttle: 1 }, cfg, dt);
      if (stepMeshWalls(k, p.collision, wallCfg, dt)) hit = true;
      stepVertical(k, ground, tuning.physics, dt);
    }
    expect(hit).toBe(true);
    const across = (k.x - s.pos.x) * s.right.x + (k.z - s.pos.z) * s.right.z;
    expect(across).toBeLessThan(s.width / 2 + 1.5); // the barrier sits beyond the shoulder
    expect(k.y).toBeGreaterThan(s.pos.y - 0.5);
  });
});

/** A flat square of collision: two triangles at height 0. */
function flatMesh(size = 2000): CollisionMesh {
  const g = new THREE.PlaneGeometry(size, size, 40, 40).rotateX(-Math.PI / 2);
  const mesh = new THREE.Mesh(g, new THREE.MeshBasicMaterial());
  mesh.material.userData.kp_surface = "asphalt";
  return buildCollisionMesh(mesh, SURFACES).mesh;
}

describe("physics are unchanged on imported geometry (H)", () => {
  it("drives, drifts and boosts identically on a flat mesh and on the flat ground", () => {
    const mesh = createMeshGround(flatMesh());
    const run = (ground: typeof flatGround) => {
      const k: KartState = createKartState(3, -7, 0.4);
      const script: [number, Partial<InputState>][] = [
        [2, { throttle: 1 }],
        [0.05, { throttle: 1, steer: 1, drift: true }],
        [2.5, { throttle: 1, steer: 0.6, drift: true }],
        [1, { throttle: 1, steer: -0.4 }],
        [1, { throttle: 0, brake: 1 }],
      ];
      for (const [secs, input] of script)
        for (let t = 0; t < secs; t += dt) {
          stepKart(k, { ...NEUTRAL, ...input }, cfg, dt);
          stepVertical(k, ground, tuning.physics, dt);
        }
      return k;
    };
    const a = run(flatGround);
    const b = run(mesh);
    for (const key of ["x", "y", "z", "speed", "heading", "velAngle", "driftOffset"] as const)
      expect(b[key], key).toBeCloseTo(a[key], 9);
  });
});

describe("hot reload (F)", () => {
  it("swaps the geometry in place without piling up objects or leaking", async () => {
    const scene = new THREE.Scene();
    const first = await loadTrackPackage(reader, { visual: false });
    const box = () => {
      const g = new THREE.Group();
      g.add(new THREE.Mesh(new THREE.BoxGeometry(), new THREE.MeshBasicMaterial()));
      return g;
    };
    first.visual = box();
    scene.add(first.visual);
    const ground = createMeshGround(first.collision);
    const collision = first.collision;
    let disposed = 0;
    for (let i = 0; i < 3; i++) {
      const next = await loadTrackPackage(reader, { visual: false });
      next.visual = box();
      const old = first.visual;
      old.traverse((o) => {
        const m = o as THREE.Mesh;
        if (m.isMesh) m.geometry.addEventListener("dispose", () => disposed++);
      });
      swapPackage(scene, first, next);
      expect(scene.children).toHaveLength(1);
      expect(scene.children[0]).toBe(next.visual);
    }
    expect(disposed).toBe(3);
    // Grounds created before the reload see the new collision.
    expect(first.collision).toBe(collision);
    const q = first.trackData.points[0]!;
    expect(ground.at(q.x, q.z, (q.y ?? 0) + 0.2).surface).toBe("asphalt");
  });
});
