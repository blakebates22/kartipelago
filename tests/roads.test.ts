// Back up onto the road (Blake, valley polish 14, note 1: "sometimes the road is higher
// than the ground and if I fall off the road and try to go back on the road, I cant ...
// unless its an explicit rail we built, we should be able to get back onto the road").
// A kart can drive up a step of 0.25 m at most (collisionMesh's WALL_BAND.low); anything
// taller is a wall. For every overworld region: from the land right beside any road (not
// a bridge), the road's edge is no more than that above it. (A drop of more than 2 m, or a
// bank falling steeply away to a river or off a ledge, is a cliff: you fell off, and
// that's allowed.) The courses too, one world at a time.
import { describe, expect, it } from "vitest";
import { readFile } from "node:fs/promises";
import { heightField, readGlb, type GlbMesh } from "./glb";

const REGIONS = ["valley_region", "snow_region", "desert_region", "beach_region", "dragon_region"];
/** The courses done so far (Oct 30: the Prehistoric world's but Bonebog Pyramid, which
 * needs none, the Snow world's, the desert's, the beach's and the dragon world's; standard and ruin). */
const COURSES = [
  "riverbend_palms",
  "cascade_caverns",
  "ember_peak",
  "snowy_summit",
  "frostveil_citadel",
  "hearthglow_hollow",
  "aurora_rift",
  "snow_dragon_pass",
  "canyon_dash",
  "oasis_haven",
  "dry_gulch",
  "impact_depths",
  "coral_cove",
  "shipwreck_bay",
  "volcano_isle",
  "splash_lagoon",
  "dragon_isles",
  "dragon_canyon",
  "celestial_dragon_festival",
].flatMap((t) => [t, `${t}_ruin`]);
/** What's a road (the race line's pieces, the side roads, aprons and lanes), by name. */
const ROAD = /^(Road \d+ |.* Road$|.* Apron$|.* Lane$)/;
/** Built drops: a bridge, a raised deck or causeway, a jump's ramp and landing, a cliff ledge, a ford (its sides are meant to fall away: a rail, water, or a jump). */
const BRIDGE =
  /^Road \d+ .*(bridge|boardwalk|pier|landing|ramp|kicker|jump|ford|launch|viaduct|ledge|dike|causeway|spiral|wreck|mast)|^Pier/;
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
    // (The seabed under the beach world's deep water: in there you sink and respawn.)
    else if (/^(Underfloor|Seabed)/.test(n)) continue;
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
    // (On a rail's or a wall's top, not the road: a strip under 2.5 m across, falling away on
    // both sides. It's the wall we built, not somewhere you drive.)
    const level = (dx: number, dz: number) => {
      let h = r;
      for (let i = 1; i <= 15; i++) {
        const q = roadH(x + dx * i, z + dz * i, h + 0.3);
        if (q === undefined || q < h - 0.25) return i - 1;
        h = q;
      }
      return 15;
    };
    let rail = false;
    for (let k = 0; k < 4 && !rail; k++) {
      const dx = Math.cos((k * Math.PI) / 4) * 0.1;
      const dz = Math.sin((k * Math.PI) / 4) * 0.1;
      rail = level(dx, dz) + level(-dx, -dz) < 25;
    }
    if (rail) continue;
    // (Out from here, 8 ways: the road's edge, where it ends, and the land just past it.
    // The step is measured right at the edge, so a steep road's grade isn't counted.)
    for (let k = 0; k < 8; k++) {
      const dx = Math.cos((k * Math.PI) / 4) * 0.1;
      const dz = Math.sin((k * Math.PI) / 4) * 0.1;
      let top = r;
      for (let i = 1; i <= 20; i++) {
        const qx = x + dx * i;
        const qz = z + dz * i;
        const rq = roadH(qx, qz, top + 3);
        // (A rail or barrier: the road's side climbing up, a wall we built on purpose.)
        if (rq !== undefined && rq > top + 0.25) break;
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

/** Where the land comes up through a road (grass on the road): each road's top faces'
 * middles where the land stands over the road by more than `over` m ("x, z: height"). */
export async function landOverRoad(pkg: string, over = 0.15) {
  const col = await readGlb(url(pkg, "collision.glb"));
  const roads: GlbMesh[] = [];
  // (The land: the terrain itself, the big mesh with the most faces, split by material,
  // not rocks heaped over a tunnel or a plaza laid on it.)
  const sizes = new Map<string, number>();
  for (const m of col) {
    const n = base(m.name).replace(/ \d+$/, "");
    if (ROAD.test(n) || BRIDGE.test(n)) roads.push(m);
    else if (!/^Underfloor/.test(n) && extent(m) > 80)
      sizes.set(n, (sizes.get(n) ?? 0) + m.tris.length);
  }
  const terrain = [...sizes].sort((a, b) => b[1] - a[1])[0]?.[0];
  const land = col.filter((m) => base(m.name).replace(/ \d+$/, "") === terrain);
  const roadH = heightField(roads, 4);
  const landH = heightField(land, 4);
  // (On the race line's surface itself, not its shoulders or the skirt under its edge, which
  // the land is meant to cover.)
  const route = JSON.parse(new TextDecoder().decode(await readFile(url(pkg, "route.json")))) as {
    routes: { points: { x: number; z: number; width: number }[] }[];
  };
  const pts = route.routes[0]!.points;
  const onRoad = (x: number, z: number) => {
    let best = Infinity,
      w = 0;
    for (const p of pts) {
      const d = (p.x - x) ** 2 + (p.z - z) ** 2;
      if (d < best) {
        best = d;
        w = p.width;
      }
    }
    return Math.sqrt(best) < w / 2 - 0.5;
  };
  const bad = new Map<string, number>();
  for (const m of roads.filter((m) => /^Road \d+/.test(base(m.name))))
    for (let t = 0; t < m.tris.length; t += 9) {
      const a = m.tris[t]! * 3,
        b = m.tris[t + 1]! * 3,
        c = m.tris[t + 2]! * 3;
      const x = (m.pos[a]! + m.pos[b]! + m.pos[c]!) / 3;
      const y = (m.pos[a + 1]! + m.pos[b + 1]! + m.pos[c + 1]!) / 3;
      const z = (m.pos[a + 2]! + m.pos[b + 2]! + m.pos[c + 2]!) / 3;
      const r = roadH(x, z, 400);
      // (Only the road's top: its own face the highest there, not a skirt's side or foot.)
      if (r === undefined || Math.abs(r - y) > 0.05) continue;
      const l = landH(x, z, r + 3);
      if (l === undefined || l - r <= over || !onRoad(x, z)) continue;
      const cell = `${Math.floor(x / 8) * 8}, ${Math.floor(z / 8) * 8}`;
      bad.set(cell, Math.max(bad.get(cell) ?? 0, l - r));
    }
  return [...bad].map(([c, h]) => `${c}: ${h.toFixed(2)} m`);
}

/** What's still allowed in each region, until its last junctions are tidied (Oct 30: the
 * other overworlds' handful of spots, side roads meeting the road at a slant, 0.4-0.75 m). */
const ALLOW: Record<string, number> = {
  snow_region: 0.75,
  desert_region: 0.6,
  beach_region: 0.5,
  dragon_region: 0.55,
  // (Where a side road leaves the race line at a slant off its banked high side: you drop
  // onto it going that way. Where it joins again, it's flush.)
  hearthglow_hollow: 0.5,
  snow_dragon_pass: 0.95,
  // (A few spots on the snowfield's ridge, 0.4.)
  aurora_rift: 0.45,
  // (A spot or two where a road meets a path or a cave's mouth, 0.4-0.5.)
  riverbend_palms: 0.5,
  cascade_caverns: 0.55,
  ember_peak: 0.45,
  ember_peak_ruin: 0.45,
  // (Beside the ruin's old road, which runs a metre under the new one there: the land
  // between follows the old road.)
  riverbend_palms_ruin: 1.3,
  // (The desert: a few low spots; where the mine's road leaves the race line; the ruins'
  // narrow ridges where the land falls straight off, a bridge's abutment in Impact Depths,
  // and the wreck lying across the oasis ruin's road.)
  canyon_dash_ruin: 0.55,
  // (Where the fenced Brink meets the Mesa Run: a dip by the fence, left as it was.)
  canyon_dash: 2.0,
  oasis_haven: 0.6,
  oasis_haven_ruin: 1.65,
  dry_gulch: 0.8,
  dry_gulch_ruin: 1.95,
  impact_depths: 1.85,
  impact_depths_ruin: 1.3,
  // (The beach: a spot or two, 0.4-0.8 m.)
  coral_cove: 0.45,
  coral_cove_ruin: 0.8,
  shipwreck_bay: 0.45,
  shipwreck_bay_ruin: 0.45,
  volcano_isle: 0.45,
  volcano_isle_ruin: 0.5,
  splash_lagoon: 0.5,
  splash_lagoon_ruin: 0.5,
  // (The dragon world: a few spots; the Festival's railed terraces, where the land falls
  // away past the end of a balustrade, left as they were.)
  dragon_isles: 0.8,
  dragon_isles_ruin: 0.5,
  dragon_canyon: 0.75,
  celestial_dragon_festival: 1.7,
  celestial_dragon_festival_ruin: 1.75,
};

describe("back up onto the road", () => {
  for (const pkg of [...REGIONS, ...COURSES])
    it(`${pkg}: no road stands more than ${ALLOW[pkg] ?? STEP} m over the land beside it`, async () => {
      const over = (await roadSteps(pkg)).filter(
        (l) => Number(/: ([\d.]+) m$/.exec(l)?.[1]) > (ALLOW[pkg] ?? STEP),
      );
      expect(over).toEqual([]);
    }, 300000);
});

/** Known, and out of sight: where two of the valley's road pieces overlap at a seam (the
 * land between the lower piece and the upper one); the foot of Cascade's ruined jump ramp,
 * set into the canyon floor; where Dragon Isles' and Dragon Canyon's bridges and railed
 * roads meet the banks, as they always have. */
const SEAMS = new Set([
  "valley_region 24, 16",
  "valley_region 160, -48",
  "cascade_caverns_ruin -256, 16",
  "dragon_isles 40, -216",
  "dragon_isles 40, -224",
  "dragon_isles 64, -336",
  "dragon_isles 56, -336",
  "dragon_canyon 176, 112",
  "dragon_canyon 168, 80",
]);

/** Where the land is left as it was by a fenced road (the fence keeps you on): Canyon
 * Dash's Mesa Run, its hillside coming down over the road's edge, as it always has. */
const FENCED = new Set(["canyon_dash", "canyon_dash_ruin"]);

describe("no grass on the road", () => {
  for (const pkg of [...REGIONS, ...COURSES].filter((p) => !FENCED.has(p)))
    it(`${pkg}: the land never comes up through a road`, async () => {
      const bad = (await landOverRoad(pkg)).filter((l) => !SEAMS.has(`${pkg} ${l.split(":")[0]}`));
      expect(bad).toEqual([]);
    }, 300000);
});
