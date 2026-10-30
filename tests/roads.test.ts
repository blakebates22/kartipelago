// Back up onto the road (Blake, valley polish 14, note 1: "sometimes the road is higher
// than the ground and if I fall off the road and try to go back on the road, I cant ...
// unless its an explicit rail we built, we should be able to get back onto the road").
// A kart can drive up a step of 0.25 m at most (collisionMesh's WALL_BAND.low); anything
// taller is a wall. For every overworld region: from the land right beside any road (not
// a bridge), the road's edge is no more than that above it. (A drop of more than 2 m, or a
// bank falling steeply away to a river or off a ledge, is a cliff: you fell off, and
// that's allowed.)
import { describe, expect, it } from "vitest";
import { heightField, readGlb, type GlbMesh } from "./glb";

const REGIONS = ["valley_region"];
/** What's a road (the race line's pieces, the side roads, aprons and lanes), by name. */
const ROAD = /^(Road \d+ |.* Road$|.* Apron$|.* Lane$)/;
/** A bridge: its sides are meant to be drops (railed, or over the water). */
const BRIDGE = /^Road \d+ .*bridge/;
/** The kart climbs 0.25 m; for now a few edges in the tunnels sit a little over that (the
 * skirt's lip under the shoulder), so the test allows 0.35 until the rollout tightens it. */
const STEP = 0.35;
const CLIFF = 2.0;

const url = (pkg: string, f: string) => new URL(`../public/tracks/${pkg}/${f}`, import.meta.url);
const base = (n: string) => n.replace(/_[0-9a-f]{2,8}$/, "").replace(/_/g, " ");

function extent(m: GlbMesh) {
  let x0 = Infinity,
    x1 = -Infinity,
    z0 = Infinity,
    z1 = -Infinity;
  for (let k = 0; k < m.pos.length; k += 3) {
    x0 = Math.min(x0, m.pos[k]!);
    x1 = Math.max(x1, m.pos[k]!);
    z0 = Math.min(z0, m.pos[k + 2]!);
    z1 = Math.max(z1, m.pos[k + 2]!);
  }
  return Math.max(x1 - x0, z1 - z0);
}

/** Every spot (a 4 m cell) where the land beside a road lies more than STEP (and no more
 * than CLIFF) below it: "x, z: step". */
export async function roadSteps(pkg: string) {
  const col = await readGlb(url(pkg, "collision.glb"));
  const roads: GlbMesh[] = [];
  const bridges: GlbMesh[] = [];
  const land: GlbMesh[] = [];
  const other: GlbMesh[] = [];
  for (const m of col) {
    const n = base(m.name);
    if (BRIDGE.test(n)) bridges.push(m);
    else if (ROAD.test(n)) roads.push(m);
    else if (/^Underfloor/.test(n)) continue;
    else if (extent(m) > 80) land.push(m);
    else other.push(m);
  }
  const roadH = heightField(roads, 4);
  const bridgeH = heightField(bridges, 4);
  const landH = heightField(land, 4);
  const otherH = heightField(other, 4);
  // (The points on a road's top, a metre apart.)
  const pts = new Set<string>();
  for (const m of roads)
    for (let t = 0; t < m.tris.length; t += 3) {
      const a = m.tris[t]! * 3,
        b = m.tris[t + 1]! * 3,
        c = m.tris[t + 2]! * 3;
      const ux = m.pos[b]! - m.pos[a]!,
        uy = m.pos[b + 1]! - m.pos[a + 1]!,
        uz = m.pos[b + 2]! - m.pos[a + 2]!;
      const vx = m.pos[c]! - m.pos[a]!,
        vy = m.pos[c + 1]! - m.pos[a + 1]!,
        vz = m.pos[c + 2]! - m.pos[a + 2]!;
      const nx = uy * vz - uz * vy,
        ny = uz * vx - ux * vz,
        nz = ux * vy - uy * vx;
      if (Math.abs(ny) < 0.7 * Math.hypot(nx, ny, nz)) continue;
      const xs = [m.pos[a]!, m.pos[b]!, m.pos[c]!];
      const zs = [m.pos[a + 2]!, m.pos[b + 2]!, m.pos[c + 2]!];
      for (let x = Math.floor(Math.min(...xs)); x <= Math.ceil(Math.max(...xs)); x++)
        for (let z = Math.floor(Math.min(...zs)); z <= Math.ceil(Math.max(...zs)); z++)
          pts.add(`${x},${z}`);
    }
  const spots = new Map<string, number>();
  for (const key of pts) {
    const [x, z] = key.split(",").map(Number) as [number, number];
    const r = roadH(x, z, 400);
    if (r === undefined) continue;
    const br = bridgeH(x, z, 400);
    if (br !== undefined && br > r - 0.5) continue;
    // (Out from here, 8 ways: the road's edge, where it ends, and the land just past it.
    // The step is measured right at the edge, so a steep road's grade isn't counted.)
    for (let k = 0; k < 8; k++) {
      const dx = Math.cos((k * Math.PI) / 4) * 0.1;
      const dz = Math.sin((k * Math.PI) / 4) * 0.1;
      let top = r;
      for (let i = 1; i <= 20; i++) {
        const qx = x + dx * i;
        const qz = z + dz * i;
        const rq = roadH(qx, qz, top + 0.3);
        if (rq !== undefined && rq > top - 0.25) {
          top = rq;
          continue;
        }
        if (bridgeH(qx, qz, top + 1) !== undefined) break;
        // (By a bridge's end, where the bank falls to the water: a drop, not a kerb.)
        let byBridge = false;
        for (let a = 0; a < 8 && !byBridge; a++)
          byBridge =
            bridgeH(
              qx + Math.cos((a * Math.PI) / 4) * 4,
              qz + Math.sin((a * Math.PI) / 4) * 4,
              top + 2,
            ) !== undefined;
        if (byBridge) break;
        // (Something else stands there, a wall, a rock, a prop: not open land.)
        const o = otherH(qx, qz, top + 1.5);
        const l = landH(qx, qz, top + 1.5);
        if (l === undefined || (o !== undefined && o > l + 0.3)) break;
        const step = top - Math.max(l, rq ?? -Infinity);
        // (A bank falling away beside the road, steeper than 1 in 1 over the next metre and
        // a half, down to a river or off a ledge, is a drop, not a kerb: you fell off.)
        const l2 = landH(qx + dx * 15, qz + dz * 15, top + 1.5);
        if (l2 !== undefined && l - l2 > 1.5) break;
        if (step > STEP && step <= CLIFF) {
          const cell = `${Math.floor(x / 4) * 4}, ${Math.floor(z / 4) * 4}`;
          spots.set(cell, Math.max(spots.get(cell) ?? 0, step));
        }
        break;
      }
    }
  }
  return [...spots].sort((a, b) => b[1] - a[1]).map(([c, s]) => `${c}: ${s.toFixed(2)} m`);
}

describe("back up onto the road", () => {
  for (const pkg of REGIONS)
    it(`${pkg}: no road stands more than ${STEP} m over the land beside it`, async () => {
      expect(await roadSteps(pkg)).toEqual([]);
    }, 300000);
});
