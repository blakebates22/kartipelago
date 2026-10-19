/**
 * Track packages: a track authored in Blender and exported with the Kartipelago add-on
 * (tools/blender). One folder per track, served from public/tracks/<id>/:
 *
 *   track.json     gameplay metadata (ours: never written by Blender after creation)
 *   visual.glb     what you see
 *   collision.glb  what you drive on and hit (semantic surfaces in material extras)
 *   route.json     the race route sampled from the Blender curve (exporter-owned)
 *   look.json      sky, sun and fog (exporter-owned; optional)
 *   checkpoints.json  the checkpoint gates placed in Blender (exporter-owned; optional:
 *                  without it they're placed automatically from the route)
 *
 * Loading turns them into the pieces the game already uses: the route becomes an
 * ordinary centre-line TrackData (so checkpoints, the grid, the AI racing line and
 * placements along the lap all work unchanged), the collision GLB becomes a
 * CollisionMesh for the ground and wall queries, and the visual GLB is added to the
 * scene. Nothing here depends on the editor. See docs/track-pipeline.md.
 */
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import surfacesFile from "../../assets/data/surfaces.json";
import {
  prepareTrackMaterials,
  type LookMode,
  type TrackMaterials,
} from "../render/trackMaterials";
import { buildCollisionMesh, type CollisionMesh, type SurfaceTable } from "./collisionMesh";
import type { TrackData } from "./track";
import type { CheckpointGate } from "../race/checkpoints";

export const TRACK_SCHEMA = 1;
export const ROUTE_SCHEMA = 1;

export interface TrackMeta {
  schemaVersion: number;
  id: string;
  name: string;
  geometry: { visual: string; collision: string; route: string; look?: string };
  race?: { laps?: number };
  /** Gameplay entities with stable ids (Milestone 2). */
  entities?: unknown[];
}

export interface RoutePoint {
  x: number;
  y: number;
  z: number;
  width: number;
  bank: number;
}

export interface RouteFile {
  schemaVersion: number;
  generator?: string;
  routes: { id: string; closed: boolean; points: RoutePoint[] }[];
}

/** A track's sky, light and fog (look.json). Anything missing uses the game's default. */
export interface TrackLook {
  theme?: string;
  sky?: string;
  fog?: { enabled: boolean; color: string; near: number; far: number };
  sun?: { color: string; intensity: number; direction: [number, number, number] };
  ambient?: { sky: string; ground: string; intensity: number };
}

export const CHECKPOINT_SCHEMA = 1;

/** checkpoints.json: gates in game coordinates, as the Blender add-on exports them. */
export interface CheckpointFile {
  schemaVersion: number;
  checkpoints: {
    id: string;
    index: number;
    route?: string;
    position: [number, number, number];
    heading: number;
    width?: number;
    left?: number;
    right?: number;
    height: number;
    below?: number;
    respawn?: { position: [number, number, number]; heading: number };
  }[];
}

/** Check checkpoints.json and turn it into gates, or throw a TrackError. */
export function parseCheckpoints(json: unknown, warnings: string[] = []): CheckpointGate[] {
  if (!isObj(json) || !Array.isArray(json.checkpoints))
    throw new TrackError("checkpoints.json: no checkpoints list");
  if (!finite(json.schemaVersion) || (json.schemaVersion as number) > CHECKPOINT_SCHEMA)
    throw new TrackError(
      `checkpoints.json: unsupported schema version ${String(json.schemaVersion)}`,
    );
  const gates: CheckpointGate[] = [];
  for (const c of json.checkpoints as CheckpointFile["checkpoints"]) {
    const p = c.position;
    if (
      !Array.isArray(p) ||
      p.length !== 3 ||
      !p.every(finite) ||
      !finite(c.index) ||
      !finite(c.heading)
    ) {
      warnings.push(`checkpoints.json: ${String(c.id)} is malformed, skipped`);
      continue;
    }
    const half = finite(c.width) ? c.width! / 2 : 10;
    const fx = Math.sin(c.heading);
    const fz = Math.cos(c.heading);
    const rs = c.respawn;
    gates.push({
      id: typeof c.id === "string" ? c.id : `cp${c.index}`,
      index: c.index,
      route: typeof c.route === "string" && c.route ? c.route : "main",
      x: p[0],
      y: p[1],
      z: p[2],
      fx,
      fz,
      heading: c.heading,
      left: finite(c.left) ? c.left! : half,
      right: finite(c.right) ? c.right! : half,
      height: finite(c.height) ? c.height : 6,
      below: finite(c.below) ? c.below! : 3,
      respawn:
        rs && Array.isArray(rs.position) && rs.position.every(finite) && finite(rs.heading)
          ? { x: rs.position[0], y: rs.position[1], z: rs.position[2], heading: rs.heading }
          : { x: p[0] + fx * 4, y: p[1], z: p[2] + fz * 4, heading: c.heading },
    });
  }
  const idx = [...new Set(gates.filter((g) => g.route === "main").map((g) => g.index))].sort(
    (a, b) => a - b,
  );
  if (!idx.length) throw new TrackError("checkpoints.json: no main-route checkpoints");
  // An alternate gate stands in for a main checkpoint: without one it means nothing.
  for (const g of [...gates])
    if (g.route !== "main" && !idx.includes(g.index)) {
      warnings.push(`checkpoints.json: ${g.id} has no main checkpoint ${g.index}, skipped`);
      gates.splice(gates.indexOf(g), 1);
    }
  if (idx[0] !== 0) warnings.push("checkpoints.json: there's no checkpoint 0 (the start line)");
  idx.forEach((v, i) => {
    if (v !== i)
      warnings.push(`checkpoints.json: checkpoint numbers skip from ${idx[i - 1]} to ${v}`);
  });
  return gates;
}

export interface TrackPackage {
  meta: TrackMeta;
  route: RouteFile;
  /** The main route as centre-line track data. */
  trackData: TrackData;
  visual: THREE.Object3D;
  collision: CollisionMesh;
  /** The visual's materials: texture look and water/lava animation. */
  materials: TrackMaterials;
  look: TrackLook;
  /** Falling below this height puts you back on the track. */
  killY: number;
  /** Non-fatal problems worth showing the track's author. */
  warnings: string[];
}

/** A problem that stops the track loading, with a message for its author. */
export class TrackError extends Error {}

const isObj = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const finite = (v: unknown) => typeof v === "number" && Number.isFinite(v);

/** Check track.json and return it typed, or throw a TrackError saying what's wrong. */
export function parseTrackMeta(json: unknown): TrackMeta {
  if (!isObj(json)) throw new TrackError("track.json: not a JSON object");
  const v = json.schemaVersion;
  if (!finite(v)) throw new TrackError("track.json: missing schemaVersion");
  if ((v as number) > TRACK_SCHEMA)
    throw new TrackError(
      `track.json: schema version ${v} is newer than this game understands (${TRACK_SCHEMA})`,
    );
  if (typeof json.id !== "string" || !json.id) throw new TrackError("track.json: missing id");
  const g = json.geometry;
  if (!isObj(g)) throw new TrackError("track.json: missing geometry");
  for (const k of ["visual", "collision", "route"])
    if (typeof g[k] !== "string") throw new TrackError(`track.json: geometry.${k} is missing`);
  return {
    schemaVersion: v as number,
    id: json.id,
    name: typeof json.name === "string" ? json.name : json.id,
    geometry: g as TrackMeta["geometry"],
    race: isObj(json.race) ? (json.race as TrackMeta["race"]) : undefined,
    entities: Array.isArray(json.entities) ? json.entities : [],
  };
}

/** Check route.json, or throw a TrackError. */
export function parseRoute(json: unknown): RouteFile {
  if (!isObj(json) || !Array.isArray(json.routes) || json.routes.length === 0)
    throw new TrackError("route.json: no routes (mark the road curve as the route in Blender)");
  if (!finite(json.schemaVersion) || (json.schemaVersion as number) > ROUTE_SCHEMA)
    throw new TrackError(`route.json: unsupported schema version ${String(json.schemaVersion)}`);
  const routes = json.routes as RouteFile["routes"];
  routes.forEach((r, i) => {
    if (!Array.isArray(r.points) || r.points.length < 3)
      throw new TrackError(`route.json: route ${i} has fewer than 3 points`);
    r.points.forEach((p, j) => {
      for (const k of ["x", "y", "z", "width", "bank"] as const)
        if (!finite(p[k])) throw new TrackError(`route.json: route ${i} point ${j} has a bad ${k}`);
    });
  });
  return json as unknown as RouteFile;
}

const BALLOON_COLORS = ["red", "blue", "green", "yellow", "rainbow"] as const;
type BalloonColor = (typeof BALLOON_COLORS)[number];

/**
 * Pickups placed along the lap, from track.json's entities (each with a stable id):
 *
 *   { "id": "zip_01", "type": "zipper", "at": 120, "across": -3 }
 *   { "id": "ban_01", "type": "bananas", "at": 40, "across": 0, "count": 5, "gap": 2.5 }
 *   { "id": "bal_01", "type": "balloon", "at": 95, "across": 4, "color": "blue" }
 *
 * `at` is metres along the route from the start line, `across` metres right of its
 * centre. Entities of other types are left for the systems that understand them;
 * malformed ones are skipped with a warning.
 */
export function placementsFrom(entities: unknown[], warnings: string[] = []) {
  const zippers: NonNullable<TrackData["zippers"]> = [];
  const bananas: NonNullable<TrackData["bananas"]> = [];
  const balloons: NonNullable<TrackData["balloons"]> = [];
  for (const e of entities) {
    if (!isObj(e) || typeof e.type !== "string") continue;
    const id = typeof e.id === "string" ? e.id : "?";
    if (!["zipper", "bananas", "balloon"].includes(e.type)) continue;
    if (!finite(e.at)) {
      warnings.push(`track.json: entity ${id} has no "at"`);
      continue;
    }
    const at = e.at as number;
    const across = finite(e.across) ? (e.across as number) : 0;
    if (e.type === "zipper") zippers.push({ at, across });
    else if (e.type === "bananas")
      bananas.push({
        at,
        across,
        count: finite(e.count) ? (e.count as number) : undefined,
        gap: finite(e.gap) ? (e.gap as number) : undefined,
        respawn: finite(e.respawn) ? (e.respawn as number) : undefined,
      });
    else {
      const color = BALLOON_COLORS.includes(e.color as BalloonColor)
        ? (e.color as BalloonColor)
        : "red";
      balloons.push({ at, across, color });
    }
  }
  return { zippers, bananas, balloons };
}

/** The main route as centre-line track data for the existing systems. */
export function routeToTrackData(
  meta: TrackMeta,
  route: RouteFile,
  warnings: string[] = [],
): TrackData {
  const main = route.routes.find((r) => r.id === "main") ?? route.routes[0]!;
  return {
    name: meta.name,
    defaultWidth: main.points[0]!.width,
    points: main.points.map((p) => ({ x: p.x, y: p.y, z: p.z, width: p.width, bank: p.bank })),
    open: true,
    imported: true,
    gateHeight: 6,
    ...placementsFrom(meta.entities ?? [], warnings),
  };
}

const HEX = /^#[0-9a-fA-F]{6}$/;

/**
 * Check look.json. Bad parts are dropped (the game's default is used for them) with a
 * warning, never fatal: a typo in the sky colour shouldn't stop a track loading.
 */
export function parseLook(json: unknown, warnings: string[] = []): TrackLook {
  if (!isObj(json)) {
    warnings.push("look.json: not a JSON object");
    return {};
  }
  const look: TrackLook = {};
  const bad = (what: string) => warnings.push(`look.json: bad ${what}, using the default`);
  if (typeof json.theme === "string") look.theme = json.theme;
  if (json.sky !== undefined) {
    if (typeof json.sky === "string" && HEX.test(json.sky)) look.sky = json.sky;
    else bad("sky");
  }
  const f = json.fog;
  if (f !== undefined) {
    if (
      isObj(f) &&
      typeof f.enabled === "boolean" &&
      typeof f.color === "string" &&
      HEX.test(f.color) &&
      finite(f.near) &&
      finite(f.far) &&
      (f.far as number) > (f.near as number)
    )
      look.fog = f as TrackLook["fog"];
    else bad("fog");
  }
  const sun = json.sun;
  if (sun !== undefined) {
    const d = isObj(sun) ? sun.direction : undefined;
    if (
      isObj(sun) &&
      typeof sun.color === "string" &&
      HEX.test(sun.color) &&
      finite(sun.intensity) &&
      Array.isArray(d) &&
      d.length === 3 &&
      d.every(finite) &&
      (d[1] as number) > 0
    )
      look.sun = sun as TrackLook["sun"];
    else bad("sun");
  }
  const a = json.ambient;
  if (a !== undefined) {
    if (
      isObj(a) &&
      typeof a.sky === "string" &&
      HEX.test(a.sky) &&
      typeof a.ground === "string" &&
      HEX.test(a.ground) &&
      finite(a.intensity)
    )
      look.ambient = a as TrackLook["ambient"];
    else bad("ambient");
  }
  return look;
}

/** Reads one file of a package (fetch in the browser, the file system in tests). */
export type PackageReader = (file: string) => Promise<ArrayBuffer>;

/** Read files from a URL folder; `bust` defeats the browser cache on reloads. */
export function urlReader(base: string, bust?: string): PackageReader {
  return async (file) => {
    const url = `${base}${file}${bust ? `?v=${bust}` : ""}`;
    const res = await fetch(url);
    if (!res.ok) throw new TrackError(`${file}: ${res.status} ${res.statusText}`);
    return res.arrayBuffer();
  };
}

const text = (buf: ArrayBuffer) => new TextDecoder().decode(buf);

async function parseGlb(buf: ArrayBuffer, name: string): Promise<THREE.Object3D> {
  try {
    const gltf = await new GLTFLoader().parseAsync(buf, "");
    return gltf.scene;
  } catch (e) {
    throw new TrackError(`${name}: not a readable GLB (${(e as Error).message})`);
  }
}

export const SURFACES = surfacesFile.surfaces as SurfaceTable;

/** Load and check a whole package. Throws a TrackError for anything fatal. */
export async function loadTrackPackage(
  read: PackageReader,
  opts: { visual?: boolean; mode?: LookMode } = {},
): Promise<TrackPackage> {
  const meta = parseTrackMeta(JSON.parse(text(await read("track.json"))));
  // look.json is optional: tracks exported before it existed don't list it.
  const lookFile = meta.geometry.look ?? "look.json";
  const [routeBuf, colBuf, visBuf, lookBuf, cpBuf] = await Promise.all([
    read(meta.geometry.route),
    read(meta.geometry.collision),
    opts.visual === false ? Promise.resolve(undefined) : read(meta.geometry.visual),
    read(lookFile).catch(() => undefined),
    read("checkpoints.json").catch(() => undefined),
  ]);
  const route = parseRoute(JSON.parse(text(routeBuf)));
  const colScene = await parseGlb(colBuf, meta.geometry.collision);
  const { mesh: collision, warnings } = buildCollisionMesh(colScene, SURFACES);
  disposeObject(colScene); // only its triangles are kept
  if (collision.floors.count === 0)
    throw new TrackError(`${meta.geometry.collision}: nothing to drive on (no floor triangles)`);
  let look: TrackLook = {};
  if (lookBuf) {
    try {
      look = parseLook(JSON.parse(text(lookBuf)), warnings);
    } catch {
      if (meta.geometry.look) warnings.push(`${lookFile}: not valid JSON, using the default look`);
    }
  } else if (meta.geometry.look) warnings.push(`${lookFile}: missing, using the default look`);
  const visual = visBuf ? await parseGlb(visBuf, meta.geometry.visual) : new THREE.Group();
  visual.name = `track:${meta.id}`;
  const materials = prepareTrackMaterials(visual, opts.mode ?? "authentic");
  const trackData = routeToTrackData(meta, route, warnings);
  if (cpBuf) {
    try {
      trackData.gates = parseCheckpoints(JSON.parse(text(cpBuf)), warnings);
    } catch (e) {
      warnings.push(
        e instanceof TrackError
          ? `${e.message}; placing checkpoints automatically`
          : "checkpoints.json: not valid JSON; placing checkpoints automatically",
      );
    }
  }
  // Sanity check: the route should lie on the collision surface.
  const b = collision.bounds;
  const off = trackData.points.filter(
    (p) => p.x < b.minX - 1 || p.x > b.maxX + 1 || p.z < b.minZ - 1 || p.z > b.maxZ + 1,
  ).length;
  if (off > 0) warnings.push(`route: ${off} points lie outside the collision mesh`);
  return {
    meta,
    route,
    trackData,
    visual,
    collision,
    materials,
    look,
    killY: b.minY - 15,
    warnings,
  };
}

/** Free an object's GPU resources (geometries, materials, textures). */
export function disposeObject(root: THREE.Object3D) {
  root.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    m.geometry?.dispose();
    const mats = Array.isArray(m.material) ? m.material : [m.material];
    for (const mat of mats) {
      if (!mat) continue;
      for (const v of Object.values(mat)) if (v instanceof THREE.Texture) v.dispose();
      mat.dispose();
    }
  });
}

/**
 * Hot reload: put a freshly loaded package in place of the current one. The visual is
 * swapped in the scene (the old one's GPU resources are freed) and the collision mesh
 * is replaced in place, so every ground lookup already holding it sees the new one.
 */
export function swapPackage(scene: THREE.Object3D, current: TrackPackage, next: TrackPackage) {
  scene.remove(current.visual);
  disposeObject(current.visual);
  scene.add(next.visual);
  Object.assign(current.collision, next.collision);
  current.visual = next.visual;
  current.materials = next.materials;
  current.look = next.look;
  current.meta = next.meta;
  current.route = next.route;
  current.trackData = next.trackData;
  current.killY = next.killY;
  current.warnings = next.warnings;
}
