/**
 * The overworlds' bounds audit (Blake, Nov 4: "Do a thorough test for getting out of
 * bounds. Whenever I drive around and go to the river or anywhere off the main road it's
 * very easy to get out of bounds"). Two halves, both with the game's own collision:
 *
 *  1. Where can you get to? A flood fill over a 2 m grid from the road, the spawn and
 *     every gateway and passage, walking the way a kart follows the ground (climbing any
 *     floor, stepping up 0.6 m, dropping off anything, stopped by walls), as
 *     tools/audit/oob.audit.ts.
 *  2. Where does driving like a lunatic take you? Hundreds of runs of the real kart
 *     physics (stepKart, walls, vertical, surfaces), each from a random spot you can
 *     reach, half of them by the river or near where (1) found a way out: random
 *     steering, flat out, boosts, drift hops, reversing out of corners, 24 s.
 *
 * Out of bounds is any of:
 *   WALL   up in a region's walls or ridges (the layout's wall_sd over 3 m, and 6 m up
 *          over the roads near: tools/audit/bounds_export.py writes it; valley, snow,
 *          isles and the journeys);
 *   HIGH   up more than 12 m over every road within 80 m (up a mesa's side, onto a
 *          cliff top, up a wall that has no wall_sd);
 *   EDGE   within 30 m of the world's edge (and not at a passage);
 *   VOID   no floor under you, or under the world's kill height;
 *   TRAP   (1) somewhere you can't drive back out of; (2) stuck for 6 s.
 * Deep water, lava and the abyss put you back: they're a way back, not out of bounds.
 *
 *   python3 tools/audit/bounds_export.py
 *   AUDIT_FILE=tools/audit/bounds.audit.ts AUDIT_TRACK=valley_region,snow_region [RUNS=300]
 *     npx vitest run --config tools/audit/vitest.config.ts --silent=false
 *
 * The modes the fence (src/world/bounds.ts) is made and checked with:
 *   PURE=1     the fill goes everywhere a kart can, no rule stopping it; writes
 *              <track>-cells.json; with CHASE=<n> (default 400), n runs from the road aimed
 *              at the edge of where the fill got: BEYOND where the fill never went, VOID.
 *   BAKE=1     (with PURE=1) write public/tracks/<pkg>/bounds.json. After rebuilding a
 *              region or journey (or its ruin), bake it again: tests/bounds.test.ts.
 *   FENCE=1    (with PURE=1) the chase runs aim past bounds.json's edge with the game's
 *              fence on: OUT if one's grounded out of bounds for 2 s. NOFENCE=1: the same
 *              runs without it (how many got out before).
 *   e.g. AUDIT_TRACK=snow_region,snow_region_ruin PURE=1 BAKE=1 FENCE=1 CHASE=500 RUNS=0
 *
 * Writes audit-out/bounds/<track>.json (every escape: where you were in bounds last, and
 * where you got to) and a map audit-out/bounds/<track>.png: grey reachable, white road,
 * blue water, red out of bounds (static), yellow where a run got out, purple a void.
 */
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { deflateSync } from "node:zlib";
import { it } from "vitest";
import tuning from "../../assets/data/tuning.json";
import { stepVertical } from "../../src/physics/vertical";
import { stepImpacts, stepMeshWalls } from "../../src/physics/walls";
import { createKartState, stepKart, type KartConfig } from "../../src/vehicles/kart";
import { startZipper } from "../../src/vehicles/zipper";
import {
  applySurface,
  createMeshGround,
  deepestWall,
  floorAt,
  NO_FLOOR,
  type CollisionMesh,
} from "../../src/world/collisionMesh";
import { SURFACES, loadTrackPackage, type PackageReader } from "../../src/world/trackPackage";
import { REGIONS } from "../../src/overworld/regions";
import {
  createFence,
  encodeBounds,
  inBounds,
  parseBounds,
  stepBounds,
  type BoundsFile,
} from "../../src/world/bounds";
import { builtFrom } from "./boundsSync";

const CELL = 2;
const SUB = 0.5;
const RADIUS = 0.9;
const HIGH_M = 12;
const EDGE_M = 30;
const SD_OUT = 3;
const dt = 1 / 120;
const cfg: KartConfig = { ...tuning.vehicle };
const wallCfg = { ...tuning.physics, ...tuning.collision, wallHeight: tuning.track.wallHeight };
const TRACKS = (
  process.env.AUDIT_TRACK ??
  "valley_region,snow_region,desert_region,beach_region,dragon_region,journey_gorge,journey_pass,journey_dust,journey_cause"
).split(",");
const RUNS = Number(process.env.RUNS ?? 300);
const SECONDS = Number(process.env.SECONDS ?? 24);
// PURE=1: the fill goes everywhere a kart can (no out-of-bounds rule stops it), and every
// cell it reaches is written to <track>-cells.json for tools/audit/bounds_overlay.py.
const PURE = process.env.PURE === "1";
const CHASE = Number(process.env.CHASE ?? 400);
// BAKE=1: write each package's bounds.json (and RISE=<m> overrides RISES below).
const BAKE = process.env.BAKE === "1";
// FENCE=1: the chase runs with the baked bounds.json and the game's fence (stepBounds).
const FENCE = process.env.FENCE === "1";
// NOFENCE=1 (with FENCE=1): the same runs judged by bounds.json, the fence off (the before).
const NOFENCE = process.env.NOFENCE === "1";
/** How far up over the roads near the land stays in bounds, per region (m). */
const RISES: Record<string, number> = { valley_region: 15, desert_region: 25 };
/** How far in from the world's edge the land stays out of bounds, per region (m): the
 * desert's square of canyon walls stands 30-40 m in from its edge. */
const EDGES: Record<string, number> = { desert_region: 40 };
const OUT = new URL("../../audit-out/bounds/", import.meta.url);

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

/** Walk from (x, z, h) to (x1, z1) like a kart following the ground (oob.audit.ts). */
function walk(m: CollisionMesh, x: number, z: number, h: number, x1: number, z1: number) {
  const dx = x1 - x;
  const dz = z1 - z;
  const len = Math.hypot(dx, dz);
  const n = Math.ceil(len / SUB);
  const ux = dx / len;
  const uz = dz / len;
  let y = h;
  let surf = -1;
  for (let k = 1; k <= n; k++) {
    const px = x + (dx * k) / n;
    const pz = z + (dz * k) / n;
    const w0 = deepestWall(m, px, y, pz, RADIUS);
    if (w0 && w0.out > 0.05 && w0.wx * ux + w0.wz * uz > 0.3) return undefined;
    const f = floorAt(m, px, pz, y);
    if (!f || f.height <= NO_FLOOR + 1) return { y, surface: "", void: true };
    if (f.height > y + 0.6) return undefined;
    y = f.height;
    surf = m.floors.surf[f.tri]!;
    const w = deepestWall(m, px, y, pz, RADIUS);
    if (w && w.out > 0.05 && w.wx * ux + w.wz * uz > 0.3) return undefined;
  }
  return { y, surface: m.surfaces[surf] ?? "", void: false };
}

function png(w: number, h: number, rgb: Uint8Array) {
  const raw = Buffer.alloc((w * 3 + 1) * h);
  for (let y = 0; y < h; y++)
    Buffer.from(rgb.buffer, y * w * 3, w * 3).copy(raw, y * (w * 3 + 1) + 1);
  const table = Array.from({ length: 256 }, (_, n) => {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    return c >>> 0;
  });
  const crc = (b: Buffer) => {
    let c = 0xffffffff;
    for (const v of b) c = table[(c ^ v) & 0xff]! ^ (c >>> 8);
    return (c ^ 0xffffffff) >>> 0;
  };
  const chunk = (type: string, data: Buffer) => {
    const len = Buffer.alloc(4);
    len.writeUInt32BE(data.length);
    const td = Buffer.concat([Buffer.from(type), data]);
    const c = Buffer.alloc(4);
    c.writeUInt32BE(crc(td));
    return Buffer.concat([len, td, c]);
  };
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0);
  ihdr.writeUInt32BE(h, 4);
  ihdr[8] = 8;
  ihdr[9] = 2;
  return Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    chunk("IHDR", ihdr),
    chunk("IDAT", deflateSync(raw)),
    chunk("IEND", Buffer.alloc(0)),
  ]);
}

interface Node {
  ix: number;
  iz: number;
  h: number;
  surface: string;
  road: boolean;
}
type Why = "WALL" | "HIGH" | "EDGE" | "VOID" | "TRAP";

async function audit(track: string) {
  const dir = new URL(`../../public/tracks/${track}/`, import.meta.url);
  const reader: PackageReader = async (file) => {
    const b = await readFile(new URL(file, dir));
    return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
  };
  const pkg = await loadTrackPackage(reader, { visual: false });
  const m = pkg.collision;
  // (A journey's road only: the rest of its loop goes round high out of sight.)
  const meta = JSON.parse(await readFile(new URL("track.json", dir), "utf8")) as {
    journey?: { from: number; to: number };
  };
  const all = pkg.trackData.points;
  let pts = all;
  if (meta.journey) {
    let s = 0;
    pts = all.filter((p, i) => {
      if (i) s += Math.hypot(p.x - all[i - 1]!.x, p.z - all[i - 1]!.z);
      return s >= meta.journey!.from - 5 && s <= meta.journey!.to + 5;
    });
  }
  const b = m.bounds;
  const region = REGIONS.find((r) => r.packageId === track.replace(/_ruin$/, ""));
  let sd: { x0: number; z0: number; cell: number; n: number; sd: number[][] } | undefined;
  try {
    sd = JSON.parse(await readFile(new URL(`${track}.json`, OUT), "utf8"));
  } catch {
    sd = undefined;
  }
  const wallSd = (x: number, z: number) => {
    if (!sd) return -1e9;
    const i = Math.round((x - sd.x0) / sd.cell);
    const j = Math.round((z - sd.z0) / sd.cell);
    if (i < 0 || j < 0 || i >= sd.n || j >= sd.n) return 1e9;
    return sd.sd[j]![i]!;
  };
  // The road's height near a spot (the highest route point within 80 m), on a coarse grid.
  const roadTop = new Map<string, number>();
  const topNear = (x: number, z: number) => {
    const k = `${Math.round(x / 16)},${Math.round(z / 16)}`;
    let v = roadTop.get(k);
    if (v === undefined) {
      v = -Infinity;
      let nd = Infinity;
      let ny = 0;
      for (const p of pts) {
        const d = Math.hypot(p.x - x, p.z - z);
        if (d < 80) v = Math.max(v, p.y ?? 0);
        if (d < nd) [nd, ny] = [d, p.y ?? 0];
      }
      // (none within 80 m: the nearest road's height)
      if (!Number.isFinite(v)) v = ny;
      roadTop.set(k, v);
    }
    return v;
  };
  const nearestRoad = (x: number, z: number) => {
    let best = Infinity;
    for (const p of pts) best = Math.min(best, Math.hypot(p.x - x, p.z - z));
    return best;
  };
  const passages = [...(region?.passages ?? []), ...(region?.gateways ?? [])].map((p) => ({
    x: p.x,
    z: p.z,
  }));
  /** (the spots themselves: where the passage or gateway takes you, and a kart round it) */
  const doors = [...(region?.passages ?? []), ...(region?.gateways ?? [])].map((p) => ({
    x: p.x,
    z: p.z,
    r: ((p as { radius?: number }).radius ?? 8) + 6,
  }));
  const atPassage = (x: number, z: number) =>
    passages.some((p) => Math.hypot(p.x - x, p.z - z) < 45);
  // (only what puts you back: deep water, lava, the abyss; a river's "water" you drive in)
  const isWater = (s: string) => Boolean(SURFACES[s]?.respawn);
  /** Out of bounds at (x, z) standing at height y on surface s (or not). */
  const outOf = (
    x: number,
    z: number,
    y: number,
    s: string,
  ): Exclude<Why, "VOID" | "TRAP"> | undefined => {
    if (isWater(s)) return undefined;
    // (deep in a wall or out beyond it; or in one, up off the land you drive on)
    const w = wallSd(x, z);
    const top0 = topNear(x, z);
    // (a notch cut for a gateway sits low in the layout's wall: only up in it counts)
    if (w > SD_OUT && Number.isFinite(top0) && y > top0 + 6) return "WALL";
    if (
      !atPassage(x, z) &&
      (x < b.minX + EDGE_M || x > b.maxX - EDGE_M || z < b.minZ + EDGE_M || z > b.maxZ - EDGE_M)
    ) {
      if (nearestRoad(x, z) > 25) return "EDGE";
    }
    const top = topNear(x, z);
    if (Number.isFinite(top) && y > top + HIGH_M && !m.defs[s]?.road) return "HIGH";
    return undefined;
  };

  // ---------------------------------------------------------- 1. the flood fill
  const t0 = Date.now();
  const key = (ix: number, iz: number, h: number) => `${ix},${iz},${Math.round(h)}`;
  const nodes = new Map<string, Node>();
  const back = new Map<string, string[]>();
  const queue: string[] = [];
  const holes: { x: number; z: number; y: number }[] = [];
  const add = (ix: number, iz: number, h: number, surface: string) => {
    const k = key(ix, iz, h);
    if (!nodes.has(k)) {
      nodes.set(k, { ix, iz, h, surface, road: Boolean(m.defs[surface]?.road) });
      queue.push(k);
    }
    return k;
  };
  const seedAt = (x: number, z: number, y: number) => {
    const f = floorAt(m, x, z, y + 1.5);
    if (f && f.height > NO_FLOOR + 1)
      add(Math.round(x / CELL), Math.round(z / CELL), f.height, m.surfaces[m.floors.surf[f.tri]!]!);
  };
  pts.forEach((p, i) => {
    if (i % 2) return;
    const q = pts[(i + 1) % pts.length]!;
    const l = Math.hypot(q.x - p.x, q.z - p.z) || 1;
    const half = (p.width ?? pkg.trackData.defaultWidth) / 2 - 1;
    for (let a = -2; a <= 2; a++)
      seedAt(
        p.x + (-(q.z - p.z) / l) * (a / 2) * half,
        p.z + ((q.x - p.x) / l) * (a / 2) * half,
        p.y ?? 0,
      );
  });
  if (region) {
    seedAt(region.spawn.x, region.spawn.z, region.spawn.y ?? 200);
    for (const p of passages) seedAt(p.x, p.z, 200);
  }
  const DIRS = [
    [1, 0],
    [-1, 0],
    [0, 1],
    [0, -1],
    [1, 1],
    [1, -1],
    [-1, 1],
    [-1, -1],
  ] as const;
  while (queue.length) {
    const k = queue.pop()!;
    const n = nodes.get(k)!;
    // (Out of bounds already: no need to go further out.)
    if (!PURE && outOf(n.ix * CELL, n.iz * CELL, n.h, n.surface) && !n.road) continue;
    if (isWater(n.surface)) continue; // (in the water: you're put back)
    for (const [dx, dz] of DIRS) {
      const r = walk(m, n.ix * CELL, n.iz * CELL, n.h, (n.ix + dx) * CELL, (n.iz + dz) * CELL);
      if (!r) continue;
      if (r.void) {
        holes.push({ x: (n.ix + dx) * CELL, z: (n.iz + dz) * CELL, y: n.h });
        continue;
      }
      const to = add(n.ix + dx, n.iz + dz, r.y, r.surface);
      let list = back.get(to);
      if (!list) back.set(to, (list = []));
      list.push(k);
    }
  }
  // What can get back to the road (or into the water, which puts you back).
  const ok = new Set<string>();
  const q2: string[] = [];
  for (const [k, n] of nodes)
    if (n.road || isWater(n.surface)) {
      ok.add(k);
      q2.push(k);
    }
  while (q2.length) {
    const k = q2.pop()!;
    for (const f of back.get(k) ?? [])
      if (!ok.has(f)) {
        ok.add(f);
        q2.push(f);
      }
  }
  const why = new Map<string, Why>();
  for (const [k, n] of nodes) {
    const o = outOf(n.ix * CELL, n.iz * CELL, n.h, n.surface);
    if (o && !n.road) why.set(k, o);
    else if (!ok.has(k)) why.set(k, "TRAP");
  }
  // Where you get out: an in-bounds cell with a step into an out-of-bounds one.
  const ways: { why: Why; from: [number, number, number]; to: [number, number, number] }[] = [];
  for (const [to, froms] of back) {
    const w = why.get(to);
    if (!w || w === "TRAP") continue;
    for (const f of froms) {
      if (why.has(f)) continue;
      const a = nodes.get(f)!;
      const c = nodes.get(to)!;
      ways.push({
        why: w,
        from: [a.ix * CELL, +a.h.toFixed(1), a.iz * CELL],
        to: [c.ix * CELL, +c.h.toFixed(1), c.iz * CELL],
      });
    }
  }
  // Grouped into 12 m spots.
  const group = <T extends { at: [number, number, number] }>(list: T[], r = 12) => {
    const out: (T & { n: number })[] = [];
    for (const it of list) {
      const g = out.find((q) => Math.hypot(q.at[0] - it.at[0], q.at[2] - it.at[2]) < r);
      if (g) g.n++;
      else out.push({ ...it, n: 1 });
    }
    return out.sort((p, q) => q.n - p.n);
  };
  const exits = group(ways.map((w) => ({ why: w.why, at: w.from, to: w.to })));
  const traps = group(
    [...why]
      .filter(([, w]) => w === "TRAP")
      .map(([k]) => {
        const n = nodes.get(k)!;
        return {
          why: "TRAP" as Why,
          at: [n.ix * CELL, +n.h.toFixed(1), n.iz * CELL] as [number, number, number],
          surface: n.surface,
        };
      }),
  );
  const voids = group(
    holes.map((h) => ({
      why: "VOID" as Why,
      at: [h.x, +h.y.toFixed(1), h.z] as [number, number, number],
    })),
  );
  const tFill = (Date.now() - t0) / 1000;

  /**
   * BAKE=1: write the package's bounds.json (src/world/bounds.ts). In bounds: where the
   * fill got to that you can drive back out of, that isn't up more than RISE m over every
   * road within 80 m (unless on a road or within 8 m of the route), inside the layout's
   * walls (wall_sd at most 3 m, where the layout has one), more than 10 m in from the
   * world's edge; and joined to the road through more of the same. Deep water and lava
   * count (they put you back anyway); round a passage or gateway, up to 20 m.
   */
  async function bake() {
    const pk = track.replace(/_ruin$/, "");
    const rise = Number(process.env.RISE ?? RISES[pk] ?? 8);
    const routeNear = (x: number, z: number, r: number) =>
      pts.some(
        (p) => Math.abs(p.x - x) < r && Math.abs(p.z - z) < r && Math.hypot(p.x - x, p.z - z) < r,
      );
    const atWay = (x: number, z: number) => doors.some((w) => Math.hypot(w.x - x, w.z - z) < w.r);
    const good = new Set<string>();
    for (const [k, n] of nodes) {
      const x = n.ix * CELL;
      const z = n.iz * CELL;
      const edge = Math.min(x - b.minX, b.maxX - x, z - b.minZ, b.maxZ - z);
      if (edge <= (EDGES[pk] ?? 10) && !atPassage(x, z)) continue;
      if (isWater(n.surface)) {
        good.add(k);
        continue;
      }
      if (!ok.has(k)) continue;
      // (on the road or beside it, at any height: a bridge, a ramp, a road through a notch
      // the layout's walls don't know about; any road, the route's or a spur's, as the snow's
      // switchbacks up to the Burnt Gorge (not a journey's: the rest of its loop, out of
      // sight, is road too); and right at a passage or gateway)
      if (routeNear(x, z, 8) || (n.road && !meta.journey) || atWay(x, z)) {
        good.add(k);
        continue;
      }
      const up = n.h - topNear(x, z);
      // (in the layout's walls and up off the roads' level, where a notch's floor isn't)
      // (or down under it: the isles' sea floor out past the reef)
      if (sd && wallSd(x, z) > SD_OUT && (up > 4 || up < -5) && !atPassage(x, z)) continue;
      if (up <= rise || (atPassage(x, z) && up <= 20)) good.add(k);
    }
    // (joined to the road: from the route's own cells, over steps the fill took)
    const next = new Map<string, string[]>();
    for (const [to, froms] of back)
      for (const f of froms) {
        (next.get(f) ?? next.set(f, []).get(f)!).push(to);
        (next.get(to) ?? next.set(to, []).get(to)!).push(f);
      }
    const inn = new Set<string>();
    const st: string[] = [];
    for (const k of good) {
      const n = nodes.get(k)!;
      if (routeNear(n.ix * CELL, n.iz * CELL, 4) || atWay(n.ix * CELL, n.iz * CELL)) {
        inn.add(k);
        st.push(k);
      }
    }
    while (st.length) {
      const k = st.pop()!;
      for (const q of next.get(k) ?? [])
        if (good.has(q) && !inn.has(q)) {
          inn.add(q);
          st.push(q);
        }
    }
    const x0 = Math.floor(b.minX / CELL) * CELL;
    const z0 = Math.floor(b.minZ / CELL) * CELL;
    const w = Math.floor((b.maxX - x0) / CELL) + 1;
    const h = Math.floor((b.maxZ - z0) / CELL) + 1;
    const top = new Float32Array(w * h).fill(NaN);
    for (const k of inn) {
      const n = nodes.get(k)!;
      const i = Math.round((n.ix * CELL - x0) / CELL);
      const j = Math.round((n.iz * CELL - z0) / CELL);
      if (i < 0 || j < 0 || i >= w || j >= h) continue;
      const t = top[j * w + i]!;
      if (Number.isNaN(t) || n.h > t) top[j * w + i] = n.h;
    }
    // (no cap where nothing's out of bounds over the land in bounds: most of it)
    const over = new Set<number>();
    for (const [k, n] of nodes) {
      if (inn.has(k)) continue;
      const i = Math.round((n.ix * CELL - x0) / CELL);
      const j = Math.round((n.iz * CELL - z0) / CELL);
      if (i < 0 || j < 0 || i >= w || j >= h) continue;
      const t = top[j * w + i]!;
      if (!Number.isNaN(t) && n.h > t + 1) over.add(j * w + i);
    }
    for (let c = 0; c < top.length; c++)
      if (!Number.isNaN(top[c]!) && !over.has(c)) top[c] = Infinity;
    const file: BoundsFile = {
      builtFrom: builtFrom(dir),
      cell: CELL,
      x0,
      z0,
      w,
      h,
      runs: encodeBounds(top),
    };
    await writeFile(new URL("bounds.json", dir), JSON.stringify(file) + "\n");
    console.log(
      `${track}: bounds baked: ${inn.size} of ${nodes.size} cells in bounds (rise ${rise} m), ${file.runs.length} runs`,
    );
  }
  if (BAKE) await bake();
  if (PURE) {
    await mkdir(OUT, { recursive: true });
    const cells = [...nodes].map(([k, n]) => [
      n.ix * CELL,
      n.iz * CELL,
      +n.h.toFixed(1),
      +(n.h - topNear(n.ix * CELL, n.iz * CELL)).toFixed(1),
      +nearestRoad(n.ix * CELL, n.iz * CELL).toFixed(0),
      n.road ? 1 : isWater(n.surface) ? 2 : !ok.has(k) ? 3 : 0,
      n.surface,
    ]);
    await writeFile(
      new URL(`${track}-cells.json`, OUT),
      JSON.stringify({ track, bounds: b, holes: voids.map((v) => v.at), cells }),
    );
  }

  // ---------------------------------------------------------- 2. the lunatics
  const ground = createMeshGround(m);
  const R = rng(Number(process.env.SEED ?? 7));
  const inside = [...nodes.entries()].filter(([k, n]) => !why.has(k) && !isWater(n.surface));
  const nearExit = inside.filter(([, n]) =>
    exits.some((e) => Math.hypot(e.at[0] - n.ix * CELL, e.at[2] - n.iz * CELL) < 30),
  );
  const byWater = inside.filter(([, n]) => {
    for (const [dx, dz] of DIRS) {
      const k2 = [...[0, 1, -1, 2, -2]].map(
        (dh) => `${n.ix + dx * 3},${n.iz + dz * 3},${Math.round(n.h) + dh}`,
      );
      if (k2.some((kk) => nodes.has(kk) && isWater(nodes.get(kk)!.surface))) return true;
    }
    return false;
  });
  const escapes: {
    why: Why;
    last: [number, number, number];
    got: [number, number, number];
    run: number;
    t: number;
    start: [number, number, number];
    surface?: string;
    trail?: [number, number, number][];
  }[] = [];
  let stuckN = 0;
  let respawnN = 0;
  const t1 = Date.now();
  for (let run = 0; run < RUNS; run++) {
    const pool =
      run % 4 === 0 && nearExit.length
        ? nearExit
        : run % 4 === 1 && byWater.length
          ? byWater
          : inside;
    const [, start] = pool[Math.floor(R() * pool.length)]!;
    const sx = start.ix * CELL;
    const sz = start.iz * CELL;
    const k = createKartState(sx, sz, R() * Math.PI * 2, start.h + 0.5);
    let steer = 0;
    let steerTo = 0;
    let next = 0;
    let drift = false;
    let boostAt = 1 + R() * 3;
    let reverseFor = 0;
    let last: [number, number, number] = [sx, start.h, sz];
    let lastMoveT = 0;
    let lastMoveAt = [sx, sz];
    const trail: [number, number, number][] = [];
    for (let t = 0; t < SECONDS; t += dt) {
      if (t >= next) {
        steerTo = R() < 0.25 ? 0 : (R() * 2 - 1) * (R() < 0.4 ? 1 : 0.5);
        next = t + 0.4 + R() * 1.8;
        drift = R() < 0.25;
      }
      steer += (steerTo - steer) * Math.min(1, dt * 6);
      if (reverseFor <= 0 && Math.abs(k.speed) < 1.5 && t > 1 && R() < dt * 2)
        reverseFor = 0.6 + R();
      reverseFor -= dt;
      const backing = reverseFor > 0;
      if (t >= boostAt && !backing) {
        startZipper(k, 1, cfg);
        boostAt = t + 2 + R() * 4;
      }
      stepImpacts(k, tuning.collision, dt);
      let c = cfg;
      const here = ground.at(k.x, k.z, k.y);
      if (k.grounded && here.surface) c = applySurface(cfg, SURFACES[here.surface]);
      stepKart(
        k,
        {
          throttle: backing ? 0 : 1,
          brake: backing ? 1 : 0,
          steer: backing ? -steer : steer,
          drift: !backing && drift && k.grounded,
          item: false,
        },
        c,
        dt,
      );
      stepMeshWalls(k, m, wallCfg, dt);
      stepVertical(k, ground, tuning.physics, dt);
      const g = ground.at(k.x, k.z, k.y);
      if (Math.round(t * 120) % 30 === 0) {
        trail.push([+k.x.toFixed(1), +k.y.toFixed(1), +k.z.toFixed(1)]);
        if (trail.length > 16) trail.shift();
      }
      if (k.grounded && isWater(g.surface ?? "")) {
        respawnN++;
        break;
      }
      if (
        k.y < pkg.killY ||
        (!k.grounded && g.height <= NO_FLOOR + 1 && k.y < (m.bounds.minY ?? -1e9))
      ) {
        escapes.push({
          why: "VOID",
          last,
          got: [+k.x.toFixed(1), +k.y.toFixed(1), +k.z.toFixed(1)],
          run,
          t: +t.toFixed(1),
          start: [sx, start.h, sz],
          trail: [...trail],
        });
        break;
      }
      if (k.grounded) {
        const o = outOf(k.x, k.z, k.y, g.surface ?? "");
        if (o) {
          escapes.push({
            why: o,
            last,
            got: [+k.x.toFixed(1), +k.y.toFixed(1), +k.z.toFixed(1)],
            run,
            t: +t.toFixed(1),
            start: [sx, start.h, sz],
            trail: [...trail],
          });
          break;
        }
        last = [+k.x.toFixed(1), +k.y.toFixed(1), +k.z.toFixed(1)];
      }
      if (Math.hypot(k.x - lastMoveAt[0]!, k.z - lastMoveAt[1]!) > 3) {
        lastMoveAt = [k.x, k.z];
        lastMoveT = t;
      } else if (t - lastMoveT > 6) {
        stuckN++;
        escapes.push({
          why: "TRAP",
          last,
          got: [+k.x.toFixed(1), +k.y.toFixed(1), +k.z.toFixed(1)],
          run,
          t: +t.toFixed(1),
          start: [sx, start.h, sz],
          surface: g.surface ?? "",
          trail: [...trail],
        });
        break;
      }
    }
  }
  const tRuns = (Date.now() - t1) / 1000;
  if ((PURE || FENCE) && CHASE > 0) await chase();

  /**
   * PURE=1's runs: drive the way Blake does, off the road at the edges of where you can
   * get to (a spot on the fill's edge within 70 m, flat out, boosting, hopping, backing out
   * of corners) and see if the real physics takes you anywhere the fill can't: up a wall
   * it can't climb, over a ridge, through one (BEYOND), or off the world (VOID).
   */
  async function chase() {
    const tc = Date.now();
    const at = new Map<string, number[]>();
    for (const n of nodes.values()) {
      const k = `${n.ix},${n.iz}`;
      (at.get(k) ?? at.set(k, []).get(k)!).push(n.h);
    }
    const known = (x: number, z: number, y: number) => {
      const ix = Math.round(x / CELL);
      const iz = Math.round(z / CELL);
      for (let a = -1; a <= 1; a++)
        for (let c = -1; c <= 1; c++)
          for (const h of at.get(`${ix + a},${iz + c}`) ?? []) if (Math.abs(h - y) < 3) return true;
      return false;
    };
    // (FENCE=1: the baked bounds.json in force, the game's fence on; drive at its edge)
    const mask = FENCE
      ? parseBounds(JSON.parse(await readFile(new URL("bounds.json", dir), "utf8")))
      : undefined;
    const inMask = (n: Node) => !mask || inBounds(mask, n.ix * CELL, n.h, n.iz * CELL);
    const live = [...nodes.entries()]
      .filter(([k, n]) => ok.has(k) && !isWater(n.surface) && inMask(n))
      .map(([, n]) => n);
    const rim = mask
      ? live.filter((n) =>
          DIRS.some(
            ([dx, dz]) => !inBounds(mask, (n.ix + dx * 2) * CELL, n.h, (n.iz + dz * 2) * CELL),
          ),
        )
      : live.filter((n) => DIRS.some(([dx, dz]) => !at.has(`${n.ix + dx},${n.iz + dz}`)));
    // (with bounds.json: aim past the edge, at land the fill reached that's out of bounds,
    // up the mountains, out on the sea floor, as you would trying to get out)
    const beyond = mask
      ? [...nodes.values()].filter(
          (n) => !isWater(n.surface) && !inBounds(mask, n.ix * CELL, n.h, n.iz * CELL),
        )
      : [];
    const grid = new Map<string, Node[]>();
    for (const n of beyond) {
      const g = `${Math.floor(n.ix / 20)},${Math.floor(n.iz / 20)}`;
      (grid.get(g) ?? grid.set(g, []).get(g)!).push(n);
    }
    const beyondNear = (x: number, z: number) => {
      const gx = Math.floor(x / CELL / 20);
      const gz = Math.floor(z / CELL / 20);
      const out: Node[] = [];
      for (let a = -2; a <= 2; a++)
        for (let c = -2; c <= 2; c++) out.push(...(grid.get(`${gx + a},${gz + c}`) ?? []));
      return out.filter((n) => Math.hypot(n.ix * CELL - x, n.iz * CELL - z) < 70);
    };
    let held = 0;
    let fenceBack = 0;
    // (which way does steer turn: the sign, from a kart on the flat)
    const probe = createKartState(0, 0, 0, 0);
    probe.speed = 10;
    for (let t = 0; t < 0.5; t += dt)
      stepKart(probe, { throttle: 1, brake: 0, steer: 1, drift: false, item: false }, cfg, dt);
    const sign = probe.heading > 0 ? 1 : -1;
    const fwd = (h: number) => [Math.sin(h), Math.cos(h)];
    const f0 = fwd(probe.heading);
    void f0;
    const RC = rng(Number(process.env.SEED ?? 11));
    const found: {
      why: string;
      last: [number, number, number];
      got: [number, number, number];
      run: number;
      t: number;
      trail: [number, number, number][];
      surface: string;
    }[] = [];
    let back = 0;
    for (let run = 0; run < CHASE; run++) {
      // (from the road, as you'd set off: a spot on it, any way round)
      const p0 = pts[Math.floor(RC() * pts.length)]!;
      const f0 = floorAt(m, p0.x, p0.z, (p0.y ?? 0) + 1.5);
      if (!f0 || f0.height <= NO_FLOOR + 1) continue;
      const st = { ix: Math.round(p0.x / CELL), iz: Math.round(p0.z / CELL), h: f0.height } as Node;
      const k = createKartState(p0.x, p0.z, RC() * Math.PI * 2, f0.height + 0.3);
      let target = st;
      let retarget = 0;
      let boostAt = 1 + RC() * 3;
      let reverseFor = 0;
      let hopAt = 2 + RC() * 3;
      let last: [number, number, number] = [k.x, k.y, k.z];
      void live;
      let beyondFor = 0;
      const fence = createFence();
      const trail: [number, number, number][] = [];
      for (let t = 0; t < SECONDS; t += dt) {
        if (t >= retarget) {
          const past = mask && RC() < 0.7 ? beyondNear(k.x, k.z) : [];
          const near = past.length
            ? past
            : rim.filter((n) => Math.hypot(n.ix * CELL - k.x, n.iz * CELL - k.z) < 70);
          target = near.length
            ? near[Math.floor(RC() * near.length)]!
            : rim[Math.floor(RC() * rim.length)]!;
          retarget = t + 3 + RC() * 4;
        }
        const want = Math.atan2(target.ix * CELL - k.x, target.iz * CELL - k.z);
        let diff = want - k.heading;
        while (diff > Math.PI) diff -= Math.PI * 2;
        while (diff < -Math.PI) diff += Math.PI * 2;
        const steer = Math.max(-1, Math.min(1, diff * 2)) * sign + (RC() - 0.5) * 0.3;
        if (reverseFor <= 0 && Math.abs(k.speed) < 1.5 && t > 1 && RC() < dt * 2)
          reverseFor = 0.6 + RC();
        reverseFor -= dt;
        const backing = reverseFor > 0;
        if (t >= boostAt && !backing) {
          startZipper(k, 1, cfg);
          boostAt = t + 1.5 + RC() * 3;
        }
        const hop = t >= hopAt && k.grounded;
        if (hop) hopAt = t + 1 + RC() * 3;
        stepImpacts(k, tuning.collision, dt);
        const here = ground.at(k.x, k.z, k.y);
        const c = k.grounded && here.surface ? applySurface(cfg, SURFACES[here.surface]) : cfg;
        stepKart(
          k,
          {
            throttle: backing ? 0 : 1,
            brake: backing ? 1 : 0,
            steer: backing ? -steer : steer,
            drift: hop,
            item: false,
          },
          c,
          dt,
        );
        stepMeshWalls(k, m, wallCfg, dt);
        stepVertical(k, ground, tuning.physics, dt);
        if (mask && !NOFENCE) {
          const r = stepBounds(fence, k, mask, dt);
          if (r === "held") held++;
          if (r === "respawn") {
            fenceBack++;
            break;
          }
        }
        const g = ground.at(k.x, k.z, k.y);
        if (Math.round(t * 120) % 30 === 0) {
          trail.push([+k.x.toFixed(1), +k.y.toFixed(1), +k.z.toFixed(1)]);
          if (trail.length > 16) trail.shift();
        }
        const pos: [number, number, number] = [+k.x.toFixed(1), +k.y.toFixed(1), +k.z.toFixed(1)];
        if (k.grounded && isWater(g.surface ?? "")) {
          back++;
          break;
        }
        if (k.y < pkg.killY) {
          found.push({
            why: "VOID",
            last,
            got: pos,
            run,
            t: +t.toFixed(1),
            trail: [...trail],
            surface: "",
          });
          break;
        }
        if (k.grounded && mask) {
          // (with the fence: grounded out of bounds for long is a way out it missed)
          if (!inBounds(mask, k.x, k.y, k.z)) {
            beyondFor += dt;
            if (beyondFor > 2) {
              found.push({
                why: "OUT",
                last,
                got: pos,
                run,
                t: +t.toFixed(1),
                trail: [...trail],
                surface: g.surface ?? "",
              });
              break;
            }
          } else {
            beyondFor = 0;
            last = pos;
          }
        } else if (k.grounded) {
          if (!known(k.x, k.z, k.y)) {
            beyondFor += dt;
            if (beyondFor > 0.3) {
              found.push({
                why: "BEYOND",
                last,
                got: pos,
                run,
                t: +t.toFixed(1),
                trail: [...trail],
                surface: g.surface ?? "",
              });
              break;
            }
          } else {
            beyondFor = 0;
            last = pos;
          }
        }
      }
    }
    const spots = group(
      found.map((f) => ({ ...f, at: f.got })),
      10,
    );
    await writeFile(
      new URL(`${track}-chase.json`, OUT),
      JSON.stringify({ track, runs: CHASE, back, spots }, null, 1),
    );
    console.log(
      `  chase${mask ? (NOFENCE ? " (bounds.json, no fence)" : " (fenced)") : ""}: ${CHASE} runs x ${SECONDS} s (${((Date.now() - tc) / 1000).toFixed(0)} s, steer sign ${sign}): ${found.length} ${mask ? "out" : "beyond the fill"} (VOID ${found.filter((f) => f.why === "VOID").length}), ${back} put back by water${mask ? `, fence held ${(held / 120).toFixed(0)} s in all, put back on the road ${fenceBack}` : ""}`,
    );
    for (const e of spots.slice(0, 14))
      console.log(
        `    ${e.why} x${e.n}: last known ${e.last.join(", ")} -> ${e.got.join(", ")} ${e.surface}`,
      );
  }
  const runEscapes = group(
    escapes.map((e) => ({ ...e, at: e.last })),
    15,
  );

  // ---------------------------------------------------------- the map and the report
  await mkdir(OUT, { recursive: true });
  const gx0 = Math.floor(b.minX / CELL);
  const gz0 = Math.floor(b.minZ / CELL);
  const W = Math.ceil(b.maxX / CELL) - gx0 + 1;
  const H = Math.ceil(b.maxZ / CELL) - gz0 + 1;
  const img = new Uint8Array(W * H * 3).fill(20);
  const put = (x: number, z: number, c: [number, number, number], r = 0) => {
    for (let a = -r; a <= r; a++)
      for (let bb = -r; bb <= r; bb++) {
        const px = Math.round(x / CELL) - gx0 + a;
        const py = Math.round(z / CELL) - gz0 + bb;
        if (px < 0 || py < 0 || px >= W || py >= H) continue;
        img.set(c, (py * W + px) * 3);
      }
  };
  for (const [k, n] of nodes) {
    const w = why.get(k);
    put(
      n.ix * CELL,
      n.iz * CELL,
      w === "TRAP"
        ? [235, 120, 40]
        : w
          ? [220, 40, 40]
          : isWater(n.surface)
            ? [40, 90, 200]
            : n.road
              ? [235, 235, 235]
              : [96, 104, 96],
    );
  }
  for (const v of voids) put(v.at[0], v.at[2], [190, 60, 220], 2);
  for (const e of escapes) put(e.got[0], e.got[2], [255, 230, 40], 2);
  await writeFile(new URL(`${track}.png`, OUT), png(W, H, img));
  const report = {
    track,
    wallData: Boolean(sd),
    reachable: nodes.size,
    outCells: [...why.values()].filter((w) => w !== "TRAP").length,
    exits,
    traps,
    voids,
    runs: RUNS,
    seconds: SECONDS,
    escapes: runEscapes,
    stuck: stuckN,
    putBack: respawnN,
  };
  await writeFile(new URL(`${track}-report.json`, OUT), JSON.stringify(report, null, 1));
  const byWhy = (list: { why: Why }[]) =>
    (["WALL", "HIGH", "EDGE", "VOID", "TRAP"] as Why[])
      .map((w) => `${w} ${list.filter((x) => x.why === w).length}`)
      .join(", ");
  console.log(
    `${track}: ${nodes.size} cells reachable (${tFill.toFixed(0)} s); ways out: ${exits.length} spots (${byWhy(exits)}); traps ${traps.length}; voids ${voids.length}`,
  );
  console.log(
    `  ${RUNS} runs x ${SECONDS} s (${tRuns.toFixed(0)} s): ${escapes.length} got out (${byWhy(escapes)}), ${respawnN} put back by water`,
  );
  for (const e of runEscapes.slice(0, 12))
    console.log(
      `    run ${e.why} x${e.n}: last in at game ${e.last.join(", ")} -> ${e.got.join(", ")} ${e.surface ?? ""}`,
    );
  for (const e of traps.slice(0, 8))
    console.log(`    trap x${e.n}: game ${e.at.join(", ")} ${e.surface}`);
  for (const e of exits.slice(0, 12))
    console.log(`    way ${e.why} x${e.n}: game ${e.at.join(", ")} -> ${e.to.join(", ")}`);
}

for (const t of TRACKS) it(`bounds ${t}`, () => audit(t), 3_600_000);
