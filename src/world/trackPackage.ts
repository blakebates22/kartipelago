/**
 * Track packages: a track authored in Blender and exported with the Kartipelago add-on
 * (tools/blender). One folder per track, served from public/tracks/<id>/:
 *
 *   track.json     gameplay metadata (ours: never written by Blender after creation)
 *   visual.glb     what you see
 *   collision.glb  what you drive on and hit (semantic surfaces in material extras)
 *   route.json     the race route sampled from the Blender curve (exporter-owned)
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
import { buildCollisionMesh, type CollisionMesh, type SurfaceTable } from "./collisionMesh";
import type { TrackData } from "./track";

export const TRACK_SCHEMA = 1;
export const ROUTE_SCHEMA = 1;

export interface TrackMeta {
  schemaVersion: number;
  id: string;
  name: string;
  geometry: { visual: string; collision: string; route: string };
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

export interface TrackPackage {
  meta: TrackMeta;
  route: RouteFile;
  /** The main route as centre-line track data. */
  trackData: TrackData;
  visual: THREE.Object3D;
  collision: CollisionMesh;
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

/** The main route as centre-line track data for the existing systems. */
export function routeToTrackData(meta: TrackMeta, route: RouteFile): TrackData {
  const main = route.routes.find((r) => r.id === "main") ?? route.routes[0]!;
  return {
    name: meta.name,
    defaultWidth: main.points[0]!.width,
    points: main.points.map((p) => ({ x: p.x, y: p.y, z: p.z, width: p.width, bank: p.bank })),
    open: true,
    imported: true,
    gateHeight: 6,
  };
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
  opts: { visual?: boolean } = {},
): Promise<TrackPackage> {
  const meta = parseTrackMeta(JSON.parse(text(await read("track.json"))));
  const [routeBuf, colBuf, visBuf] = await Promise.all([
    read(meta.geometry.route),
    read(meta.geometry.collision),
    opts.visual === false ? Promise.resolve(undefined) : read(meta.geometry.visual),
  ]);
  const route = parseRoute(JSON.parse(text(routeBuf)));
  const colScene = await parseGlb(colBuf, meta.geometry.collision);
  const { mesh: collision, warnings } = buildCollisionMesh(colScene, SURFACES);
  disposeObject(colScene); // only its triangles are kept
  if (collision.floors.count === 0)
    throw new TrackError(`${meta.geometry.collision}: nothing to drive on (no floor triangles)`);
  const visual = visBuf ? await parseGlb(visBuf, meta.geometry.visual) : new THREE.Group();
  visual.name = `track:${meta.id}`;
  visual.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    m.castShadow = true;
    m.receiveShadow = true;
    // Crisp texels up close (the exporter's nearest filter), smooth in the distance:
    // no shimmering on far-off road and grass.
    for (const mat of Array.isArray(m.material) ? m.material : [m.material]) {
      const map = (mat as THREE.MeshStandardMaterial).map;
      if (!map) continue;
      map.minFilter = THREE.LinearMipmapLinearFilter;
      map.anisotropy = 8;
    }
  });
  const trackData = routeToTrackData(meta, route);
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
  current.meta = next.meta;
  current.route = next.route;
  current.trackData = next.trackData;
  current.killY = next.killY;
  current.warnings = next.warnings;
}
