// Solid things are solid (Blake, valley polish 18: "a lot of things that you would expect
// to have hit boxes do not ... we need proper hitboxes moving forward across the board").
// For every overworld region: every prop that stands up off the ground and looks like
// something you'd hit (a column, post, rock, log, crate, statue ...) has collision round
// its own foot, on at least three sides of it, not just a wall behind it.
import { describe, expect, it } from "vitest";
import { readGlb, type GlbMesh } from "./glb";

export const HIT_REGIONS = ["valley_region"];
/** What you'd expect to hit, by name. */
const SOLID =
  /Column|Pillar|Pilaster|Post|Pole|Boulder|Rock|Stack|Totem|Statue|Brazier|Crate|Barrel|Lip|Log\b|Stump|Well|Tower|Lantern|Block|Stela|Obelisk|Heap|Hut|House|Home|Cottage|Shed|Stall|Tree|Palm|Giant/i;
/** What's soft, flat, high up or seen through (or isn't a prop). */
const SOFT =
  /Vine|Fern|Grass|Flower|Leaf|Canopy|Moss|Bush|Reed|Cattail|Lily|Lotus|Smoke|Fire|Flame|Glow|Water|Road|Valley|Rope|Web|Ledge|Shelf|Rubble|Pebble|batch|Strata|Frieze|Sconce|Lintel|Cornice|Capital|Idol|Yard|Skull|Pool|Ribbon|Sign|Stair|Steps|Floor|Plaza|Path|Apron|Pact Stone Ground|Underfloor|Ruin \d+ Tier|Bridge/i;

const url = (pkg: string, f: string) => new URL(`../public/tracks/${pkg}/${f}`, import.meta.url);
const base = (n: string) =>
  n
    .replace(/_[0-9a-f]{6}$/, "")
    .replace(/\.\d+$/, "")
    .replace(/_/g, " ");

export async function unhit(pkg: string) {
  const vis = await readGlb(url(pkg, "visual.glb"));
  const col = await readGlb(url(pkg, "collision.glb"));
  // The collision's upright faces (walls), by the cell they're in.
  const CELL = 4;
  const walls = new Map<string, number[]>(); // (x, low, high, z) of each wall face
  for (const m of col)
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
      if (Math.abs(ny) > 0.7 * Math.hypot(nx, ny, nz)) continue;
      const cx = (m.pos[a]! + m.pos[b]! + m.pos[c]!) / 3;
      const lo = Math.min(m.pos[a + 1]!, m.pos[b + 1]!, m.pos[c + 1]!);
      const hi = Math.max(m.pos[a + 1]!, m.pos[b + 1]!, m.pos[c + 1]!);
      const cz = (m.pos[a + 2]! + m.pos[b + 2]! + m.pos[c + 2]!) / 3;
      const k = `${Math.floor(cx / CELL)},${Math.floor(cz / CELL)}`;
      const l = walls.get(k);
      if (l) l.push(cx, lo, hi, cz);
      else walls.set(k, [cx, lo, hi, cz]);
    }
  // Where you can drive: the roads' points (a prop far from any road, or high above or
  // below it on a wall's shelf, is out of reach).
  const ROAD = /^(Road \d+ |.* Road$|.* Apron$|.* Lane$)/;
  const roadPts = new Map<string, number[]>();
  for (const m of col) {
    if (!ROAD.test(base(m.name))) continue;
    for (let k = 0; k < m.pos.length; k += 9) {
      const key = `${Math.floor(m.pos[k]! / 20)},${Math.floor(m.pos[k + 2]! / 20)}`;
      const l = roadPts.get(key);
      if (l) l.push(m.pos[k]!, m.pos[k + 1]!, m.pos[k + 2]!);
      else roadPts.set(key, [m.pos[k]!, m.pos[k + 1]!, m.pos[k + 2]!]);
    }
  }
  const reachable = (x: number, y: number, z: number) => {
    for (let gx = Math.floor(x / 20) - 2; gx <= Math.floor(x / 20) + 2; gx++)
      for (let gz = Math.floor(z / 20) - 2; gz <= Math.floor(z / 20) + 2; gz++) {
        const l = roadPts.get(`${gx},${gz}`) ?? [];
        for (let i = 0; i < l.length; i += 3)
          if (Math.hypot(l[i]! - x, l[i + 2]! - z) < 30 && Math.abs(l[i + 1]! - y) < 4) return true;
      }
    return false;
  };
  const props = new Map<string, GlbMesh[]>();
  for (const m of vis) {
    const n = base(m.name);
    if (!SOLID.test(n) || SOFT.test(n)) continue;
    const l = props.get(m.name.replace(/_[0-9a-f]{6}$/, ""));
    if (l) l.push(m);
    else props.set(m.name.replace(/_[0-9a-f]{6}$/, ""), [m]);
  }
  const bad: string[] = [];
  for (const [name, parts] of props) {
    let y0 = Infinity,
      y1 = -Infinity;
    for (const m of parts)
      for (let k = 1; k < m.pos.length; k += 3) {
        y0 = Math.min(y0, m.pos[k]!);
        y1 = Math.max(y1, m.pos[k]!);
      }
    if (y1 - y0 < 0.6) continue; // (knee-high at most: you drive over it)
    // Its foot: what it has in its lowest metre and a half above the ground.
    let x0 = Infinity,
      x1 = -Infinity,
      z0 = Infinity,
      z1 = -Infinity;
    for (const m of parts)
      for (let k = 0; k < m.pos.length; k += 3)
        if (m.pos[k + 1]! < y0 + 1.5) {
          x0 = Math.min(x0, m.pos[k]!);
          x1 = Math.max(x1, m.pos[k]!);
          z0 = Math.min(z0, m.pos[k + 2]!);
          z1 = Math.max(z1, m.pos[k + 2]!);
        }
    if (Math.max(x1 - x0, z1 - z0) > 40) continue;
    const cx = (x0 + x1) / 2,
      cz = (z0 + z1) / 2;
    if (!reachable(cx, y0, cz)) continue;
    const r = Math.max(x1 - x0, z1 - z0) / 2 + 0.4;
    // (Collision on at least three of its four sides.)
    const sides = new Set<number>();
    for (let gx = Math.floor((cx - r) / CELL); gx <= Math.floor((cx + r) / CELL); gx++)
      for (let gz = Math.floor((cz - r) / CELL); gz <= Math.floor((cz + r) / CELL); gz++) {
        const l = walls.get(`${gx},${gz}`) ?? [];
        for (let i = 0; i < l.length; i += 4) {
          const dx = l[i]! - cx,
            dz = l[i + 3]! - cz;
          // (A wall that reaches into the kart's height at its foot.)
          if (Math.hypot(dx, dz) > r || l[i + 2]! < y0 - 0.5 || l[i + 1]! > y0 + 2.5) continue;
          sides.add(Math.abs(dx) > Math.abs(dz) ? (dx > 0 ? 0 : 1) : dz > 0 ? 2 : 3);
        }
      }
    if (sides.size < 3) bad.push(`${base(name)} at (${cx.toFixed(0)}, ${cz.toFixed(0)})`);
  }
  return bad;
}

describe("solid things are solid", () => {
  for (const pkg of HIT_REGIONS)
    it(`${pkg}: everything you'd hit has a hitbox`, async () => {
      expect(await unhit(pkg)).toEqual([]);
    }, 300000);
});
