import * as THREE from "three";
import { acrossRoad, type Track } from "../world/track";
import type { ZipperPad } from "../world/zippers";
import { zipperMaterial } from "./zipperStyles";

export interface TrackLook {
  wallHeight: number;
  roadColor: string;
  wallColor: string;
  zipperColor: string;
}

/** Metres of road per repeat of the road texture. */
const ROAD_TILE = 8;
const LIFT = 0.03; // keeps the road just above the ground plane

function canvasTexture(w: number, h: number, draw: (g: CanvasRenderingContext2D) => void) {
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  draw(canvas.getContext("2d")!);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 8;
  return tex;
}

/** Grey road with white edge lines and a dashed centre line, tinted by roadColor. */
function roadTexture() {
  const tex = canvasTexture(64, 64, (g) => {
    g.fillStyle = "#7a7a7a";
    g.fillRect(0, 0, 64, 64);
    g.fillStyle = "#f5f5f5";
    g.fillRect(2, 0, 3, 64);
    g.fillRect(59, 0, 3, 64);
    g.fillRect(31, 0, 2, 32);
  });
  tex.wrapT = THREE.RepeatWrapping;
  return tex;
}

/** Alternating blocks along the wall, so speed reads well. */
function wallTexture() {
  const tex = canvasTexture(64, 16, (g) => {
    g.fillStyle = "#ffffff";
    g.fillRect(0, 0, 64, 16);
    g.fillStyle = "#bdbdbd";
    g.fillRect(32, 0, 32, 16);
  });
  tex.wrapS = THREE.RepeatWrapping;
  return tex;
}

function checkerTexture() {
  const tex = canvasTexture(64, 16, (g) => {
    for (let x = 0; x < 8; x++) {
      for (let y = 0; y < 2; y++) {
        g.fillStyle = (x + y) % 2 ? "#111111" : "#ffffff";
        g.fillRect(x * 8, y * 8, 8, 8);
      }
    }
  });
  tex.magFilter = THREE.NearestFilter;
  return tex;
}

/** One strip of quads between two rows of points per sample, closed into a loop. */
function strip(
  track: Track,
  a: (i: number) => THREE.Vector3,
  b: (i: number) => THREE.Vector3,
  vScale: number,
): THREE.BufferGeometry {
  const n = track.samples.length;
  const pos: number[] = [];
  const uv: number[] = [];
  const idx: number[] = [];
  // n + 1 rows: the last repeats the first so the texture doesn't jump at the seam.
  for (let i = 0; i <= n; i++) {
    const k = i % n;
    const dist = i === n ? track.length : track.samples[k]!.dist;
    const pa = a(k);
    const pb = b(k);
    pos.push(pa.x, pa.y, pa.z, pb.x, pb.y, pb.z);
    uv.push(0, dist / vScale, 1, dist / vScale);
    if (i < n) {
      const r = i * 2;
      // Wound so faces point up when a is the left edge and b the right.
      idx.push(r, r + 1, r + 2, r + 1, r + 3, r + 2);
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
  geo.setIndex(idx);
  geo.computeVertexNormals();
  return geo;
}

/** Road, walls (not on open tracks) and start line. Purely visual; collision comes from
 * the track samples. */
export function createTrackView(
  scene: THREE.Object3D,
  track: Track,
  look: TrackLook,
  zippers: ZipperPad[] = [],
  /** false: skip the road and walls (an imported track brings its own geometry). */
  opts: {
    surface?: boolean;
    /**
     * The ground's height under (x, z) near height y: zipper pads are draped over it so
     * they lie flush on humps, dips and banking (done on the first render).
     */
    drape?: (x: number, z: number, y: number) => number;
  } = {},
) {
  // Polygon offset makes the road win depth ties with the ground plane where it lies
  // nearly flat on it (no flickering grass showing through).
  const roadMat = new THREE.MeshStandardMaterial({
    map: roadTexture(),
    roughness: 0.9,
    polygonOffset: true,
    polygonOffsetFactor: -2,
    polygonOffsetUnits: -4,
  });
  const road = new THREE.Mesh(
    strip(
      track,
      (i) => acrossRoad(track.samples[i]!, -1, LIFT),
      (i) => acrossRoad(track.samples[i]!, 1, LIFT),
      ROAD_TILE,
    ),
    roadMat,
  );
  road.receiveShadow = true;

  const wallMat = new THREE.MeshStandardMaterial({
    map: wallTexture(),
    side: THREE.DoubleSide,
    flatShading: true,
  });
  const wall = (side: number) =>
    new THREE.Mesh(
      strip(
        track,
        // Down to the ground plane, so raised road sits on solid sides.
        (i) => acrossRoad(track.samples[i]!, side, 0).setY(0),
        (i) => acrossRoad(track.samples[i]!, side, look.wallHeight),
        4,
      ),
      wallMat,
    );
  // Open tracks have no walls along the road.
  const walls = track.data.open ? [] : [wall(-1), wall(1)];
  for (const w of walls) {
    w.castShadow = true;
    w.receiveShadow = true;
    // The strip's uv runs across the wall; swap so blocks run along it.
    const uv = w.geometry.getAttribute("uv") as THREE.BufferAttribute;
    for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getY(i), uv.getX(i));
  }

  const first = track.samples[0]!;
  const startLine = new THREE.Mesh(
    new THREE.PlaneGeometry(first.width, 2).rotateX(-Math.PI / 2),
    new THREE.MeshStandardMaterial({
      map: checkerTexture(),
      polygonOffset: true,
      polygonOffsetFactor: -4,
      polygonOffsetUnits: -8,
    }),
  );
  startLine.position.copy(first.pos).y += LIFT * 2;
  startLine.rotation.y = track.start.heading;

  const zipMat = zipperMaterial(look.zipperColor);
  // A fine grid, so it can bend to the ground under it.
  const zipMeshes = zippers.map((z) => {
    const mesh = new THREE.Mesh(
      new THREE.PlaneGeometry(z.halfWidth * 2, z.halfLength * 2, 6, 12).rotateX(-Math.PI / 2),
      zipMat,
    );
    mesh.position.set(z.x, z.y + LIFT * 2, z.z);
    mesh.rotation.y = z.heading;
    return mesh;
  });
  let draped = !opts.drape;
  /** Lay each pad's vertices on the ground beneath them, just above it. */
  function drape() {
    draped = true;
    zippers.forEach((z, i) => {
      const mesh = zipMeshes[i]!;
      mesh.updateMatrixWorld(true);
      const pos = mesh.geometry.getAttribute("position") as THREE.BufferAttribute;
      const c = Math.cos(z.heading);
      const sn = Math.sin(z.heading);
      for (let k = 0; k < pos.count; k++) {
        // Local to world (the pad only turns about Y).
        const lx = pos.getX(k);
        const lz = pos.getZ(k);
        const wx = z.x + lx * c + lz * sn;
        const wz = z.z - lx * sn + lz * c;
        const h = opts.drape!(wx, wz, z.y + 1);
        pos.setY(k, h + LIFT * 3 - mesh.position.y);
      }
      pos.needsUpdate = true;
      mesh.geometry.computeVertexNormals();
      mesh.geometry.computeBoundingSphere();
    });
  }

  const surface = opts.surface ?? true;
  const parts = [...(surface ? [road, ...walls] : []), startLine, ...zipMeshes];
  scene.add(...parts);

  return {
    /** Remove everything this view added and free its GPU resources. */
    dispose() {
      for (const m of [road, ...walls, startLine, ...zipMeshes]) {
        scene.remove(m);
        m.geometry.dispose();
      }
      for (const mat of [roadMat, wallMat, zipMat, startLine.material as THREE.Material]) {
        (mat as THREE.MeshStandardMaterial).map?.dispose();
        (mat as THREE.MeshStandardMaterial).emissiveMap?.dispose();
        mat.dispose();
      }
    },
    render(colors: Pick<TrackLook, "roadColor" | "wallColor" | "zipperColor">) {
      if (!draped) drape();
      // The chevrons flow forward along the pad.
      const flow = ((performance.now() / 1000) * 1.2) % 1;
      if (zipMat.map) zipMat.map.offset.y = flow;
      if (zipMat.emissiveMap) zipMat.emissiveMap.offset.y = flow;
      roadMat.color.set(colors.roadColor);
      wallMat.color.set(colors.wallColor);
      zipMat.color.set(colors.zipperColor);
      zipMat.emissive.set(colors.zipperColor);
    },
  };
}
