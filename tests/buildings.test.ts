// No floating buildings (Blake, Oct 29: "please no more floating buildings, this is
// getting old. develop a test so u can make sure this stops happening"). For every
// overworld region: each building's footprint (its walls' foot: the lowest metre or so of
// it), sampled at its foot's corners all round, must have the land under every point within
// a little of its foot: none of it hanging out over a drop or standing up off a slope.
// (The land: the collision's big meshes, not the props' own colliders.)
import { describe, expect, it } from "vitest";
import { heightField, readGlb, type GlbMesh } from "./glb";

const REGIONS = ["valley_region", "snow_region", "desert_region", "beach_region", "dragon_region"];
/** What's a building, by its name; and what isn't, though it matches. */
const BUILDING =
  /Cottage|Hut|House|Home|Shed|Cabin|Stall|Store|Tower|Lodge|Chapel|Barn|Mill|Keep|Temple Ruin/i;
/** (Stilt huts over the water, the avalanche gallery, statues and plinths, colliders, boats.) */
const NOT = /Snowshed|Collider|Block|Gate|Frame|Boat|Slide Tower|Swamp Hut|Statue|Road|Wreck/i;
/** How far the land may fall away under a building's foot before it floats (m). */
const GAP = 0.5;

const url = (pkg: string, f: string) => new URL(`../public/tracks/${pkg}/${f}`, import.meta.url);

function buildings(meshes: GlbMesh[]) {
  const out = new Map<string, GlbMesh[]>();
  for (const m of meshes) {
    const name = m.name.replace(/_[0-9a-f]{2,6}$/, "").replace(/_/g, " ");
    if (!BUILDING.test(name) || NOT.test(name)) continue;
    const key = /^(.*?\d+)/.exec(name)?.[1] ?? name;
    const l = out.get(key);
    if (l) l.push(m);
    else out.set(key, [m]);
  }
  return out;
}

async function floating(pkg: string) {
  const vis = await readGlb(url(pkg, "visual.glb"));
  const col = await readGlb(url(pkg, "collision.glb"));
  const land = col.filter((m) => {
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
    return Math.max(x1 - x0, z1 - z0) > 80;
  });
  const ground = heightField(land);
  const bad: string[] = [];
  for (const [name, parts] of buildings(vis)) {
    let y0 = Infinity;
    for (const m of parts) for (let k = 1; k < m.pos.length; k += 3) y0 = Math.min(y0, m.pos[k]!);
    let x0 = Infinity,
      x1 = -Infinity,
      z0 = Infinity,
      z1 = -Infinity;
    for (const m of parts)
      for (let k = 0; k < m.pos.length; k += 3)
        if (m.pos[k + 1]! < y0 + 1.2) {
          x0 = Math.min(x0, m.pos[k]!);
          x1 = Math.max(x1, m.pos[k]!);
          z0 = Math.min(z0, m.pos[k + 2]!);
          z1 = Math.max(z1, m.pos[k + 2]!);
        }
    if (Math.max(x1 - x0, z1 - z0) > 60) continue; // (a town wall, not a building)
    // (Where its foot is: its lowest metre's own corners, a metre apart, pulled in 20 cm.)
    const cx = (x0 + x1) / 2,
      cz = (z0 + z1) / 2;
    const seen = new Set<string>();
    const hs: number[] = [];
    for (const m of parts)
      for (let k = 0; k < m.pos.length; k += 3) {
        if (m.pos[k + 1]! > y0 + 1.2) continue;
        const key = `${Math.round(m.pos[k]!)},${Math.round(m.pos[k + 2]!)}`;
        if (seen.has(key)) continue;
        seen.add(key);
        const dx = cx - m.pos[k]!,
          dz = cz - m.pos[k + 2]!;
        const dl = Math.hypot(dx, dz) || 1;
        const h = ground(m.pos[k]! + (dx / dl) * 0.2, m.pos[k + 2]! + (dz / dl) * 0.2, y0 + 3);
        if (h !== undefined) hs.push(h);
      }
    if (hs.length < 4) continue; // (out over nothing: a cliff dwelling's face)
    const gap = y0 - Math.min(...hs);
    if (gap > GAP)
      bad.push(
        `${name} at (${cx.toFixed(0)}, ${cz.toFixed(0)}): ${gap.toFixed(2)} m over the land`,
      );
  }
  return bad;
}

describe("no floating buildings", () => {
  for (const pkg of REGIONS)
    it(`${pkg}: every building's foot is on the land`, async () => {
      expect(await floating(pkg)).toEqual([]);
    }, 120000);
});
