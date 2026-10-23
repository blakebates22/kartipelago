/**
 * Out-of-bounds audit: where can a kart drive (or drop) to off a track that it can't
 * drive back from? Uses the game's own collision rules (floorAt, deepestWall), so what
 * it finds is what a kart would find.
 *
 *   npx vitest run --config tools/audit/vitest.config.ts            (every prehistoric track)
 *   AUDIT_TRACK=cascade_caverns npx vitest run --config tools/audit/vitest.config.ts
 *
 * How: a flood fill over a 2 m grid, starting on the road. A step to a neighbouring
 * cell walks there in small steps the way the kart follows the ground (it can climb any
 * floor, step up 0.5 m, drop off anything) and stops at walls. Then a second fill
 * backwards from the road finds everything you can get back from.
 *
 * - TRAPS: places you can reach but never drive back out of (a pit, under the world,
 *   behind a wall). These are bugs.
 * - FAR: places you can drive back from, but more than FAR_M off the road (up a wall,
 *   onto a cliff top). Worth a look.
 *
 * - DROPS: stretches of road where you can go over the edge and land somewhere with no
 *   road (every bit of route within 25 m is 4+ m above you). These want a rail.
 * - COVERED: route points with something solid just above the road (a hidden floor
 *   poking through: you'd hover on it).
 * Deep water and other respawn surfaces count as a way back (they put you back).
 *
 * Writes audit-out/<track>-oob.json and a top-down map audit-out/<track>-oob.png:
 * grey = reachable, white = the road, red = traps, purple = fallen off, orange = far.
 */
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { deflateSync } from "node:zlib";
import { it } from "vitest";
import { deepestWall, floorAt, type CollisionMesh, NO_FLOOR } from "../../src/world/collisionMesh";
import { loadTrackPackage, type PackageReader } from "../../src/world/trackPackage";

const CELL = 2;
const SUB = 0.5;
const RADIUS = 0.9;
const FAR_M = 30;
const TRACKS = (process.env.AUDIT_TRACK ?? "riverbend_palms,cascade_caverns").split(",");
const OUT = new URL("../../audit-out/", import.meta.url);

interface Node {
  ix: number;
  iz: number;
  h: number;
  road: boolean;
  surface: string;
}

const key = (ix: number, iz: number, h: number) => `${ix},${iz},${Math.round(h)}`;

/** Walk from (x, z, h) to (x1, z1) like a kart following the ground: the height there, or
 * undefined if a wall stops it or it falls off the world. */
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
    // A wall in the way at the height you're at stops you (before any climbing).
    const w0 = deepestWall(m, px, y, pz, RADIUS);
    if (w0 && w0.out > 0.05 && w0.wx * ux + w0.wz * uz > 0.3) return undefined;
    const f = floorAt(m, px, pz, y);
    if (!f || f.height <= NO_FLOOR + 1) return { y, surface: "", void: { x: px, z: pz } };
    // (floorAt brings a kart that's sunk into the ground back up onto it; driving along,
    // a floor more than a step above you is a ledge you can't get up.)
    if (f.height > y + 0.6) return undefined;
    y = f.height;
    surf = m.floors.surf[f.tri]!;
    const w = deepestWall(m, px, y, pz, RADIUS);
    if (w && w.out > 0.05 && w.wx * ux + w.wz * uz > 0.3) return undefined;
  }
  return { y, surface: m.surfaces[surf] ?? "", void: undefined };
}

function png(w: number, h: number, rgb: Uint8Array) {
  const raw = Buffer.alloc((w * 3 + 1) * h);
  for (let y = 0; y < h; y++) {
    raw[y * (w * 3 + 1)] = 0;
    Buffer.from(rgb.buffer, y * w * 3, w * 3).copy(raw, y * (w * 3 + 1) + 1);
  }
  const crcTable = Array.from({ length: 256 }, (_, n) => {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    return c >>> 0;
  });
  const crc = (b: Buffer) => {
    let c = 0xffffffff;
    for (const v of b) c = crcTable[(c ^ v) & 0xff]! ^ (c >>> 8);
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

async function audit(track: string) {
  const dir = new URL(`../../public/tracks/${track}/`, import.meta.url);
  const reader: PackageReader = async (file) => {
    const b = await readFile(new URL(file, dir));
    return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
  };
  const pkg = await loadTrackPackage(reader, { visual: false });
  const m = pkg.collision;
  const pts = pkg.trackData.points;
  const b = m.bounds;
  const gx0 = Math.floor(b.minX / CELL);
  const gz0 = Math.floor(b.minZ / CELL);
  const gw = Math.ceil(b.maxX / CELL) - gx0 + 1;
  const gh = Math.ceil(b.maxZ / CELL) - gz0 + 1;

  // Distance to the route centre line per cell (coarse: nearest route point).
  const distTo = (x: number, z: number) => {
    let best = Infinity;
    for (const p of pts) best = Math.min(best, Math.hypot(p.x - x, p.z - z));
    return best;
  };

  const nodes = new Map<string, Node>();
  // Places with no floor at all: drive in and you fall out of the world.
  const holes: { x: number; z: number; y: number }[] = [];
  const parent = new Map<string, string>();
  const back = new Map<string, string[]>(); // to -> froms
  const queue: string[] = [];
  const add = (ix: number, iz: number, h: number, surface: string) => {
    const k = key(ix, iz, h);
    if (!nodes.has(k)) {
      nodes.set(k, { ix, iz, h, surface, road: Boolean(m.defs[surface]?.road) });
      queue.push(k);
    }
    return k;
  };
  // Seeds: the road under each route point (its own layer), and across its width.
  for (const p of pts) {
    for (let a = -4; a <= 4; a++) {
      const i = pts.indexOf(p);
      const q = pts[(i + 1) % pts.length]!;
      const fx = q.x - p.x;
      const fz = q.z - p.z;
      const l = Math.hypot(fx, fz) || 1;
      const half = (p.width ?? pkg.trackData.defaultWidth) / 2 - 1;
      const x = p.x + (-fz / l) * (a / 4) * half;
      const z = p.z + (fx / l) * (a / 4) * half;
      const f = floorAt(m, x, z, (p.y ?? 0) + 1);
      if (!f) continue;
      const s = m.surfaces[m.floors.surf[f.tri]!]!;
      if (!m.defs[s]?.road) continue;
      add(Math.round(x / CELL), Math.round(z / CELL), f.height, s);
    }
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
    for (const [dx, dz] of DIRS) {
      const r = walk(m, n.ix * CELL, n.iz * CELL, n.h, (n.ix + dx) * CELL, (n.iz + dz) * CELL);
      if (!r) continue;
      if (r.void) {
        holes.push({ x: r.void.x, z: r.void.z, y: n.h });
        continue;
      }
      const isNew = !nodes.has(key(n.ix + dx, n.iz + dz, r.y));
      const to = add(n.ix + dx, n.iz + dz, r.y, r.surface);
      if (isNew) parent.set(to, k);
      let list = back.get(to);
      if (!list) back.set(to, (list = []));
      list.push(k);
    }
  }
  if (process.env.TRACE) {
    const [tx, tz] = process.env.TRACE.split(",").map(Number) as [number, number];
    let best: string | undefined;
    let bd = Infinity;
    for (const [k, n] of nodes) {
      const d =
        Math.hypot(n.ix * CELL - tx, n.iz * CELL - tz) +
        (process.env.TRACE_Y ? Math.abs(n.h - Number(process.env.TRACE_Y)) * 3 : 0);
      if (d < bd) [bd, best] = [d, k];
    }
    const chain: string[] = [];
    for (let k = best; k; k = parent.get(k))
      chain.push(`${k}:${nodes.get(k)!.h.toFixed(1)}:${nodes.get(k)!.surface}`);
    console.log("TRACE", chain.reverse().join("  "));
  }
  // Back from the road: everything that can return.
  const ok = new Set<string>();
  const q2: string[] = [];
  const hazard = (surf: string) => Boolean(m.defs[surf]?.respawn) || /water|lava/.test(surf);
  for (const [k, n] of nodes)
    if (n.road || hazard(n.surface)) {
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

  // Fallen off the course: every bit of route within 25 m is more than 4 m above you
  // (you dropped off a ledge or a bridge, and there's no road down here).
  const routeNear = (x: number, z: number) => {
    const out: { i: number; y: number; d: number }[] = [];
    pts.forEach((p, i) => {
      const d = Math.hypot(p.x - x, p.z - z);
      if (d < 25) out.push({ i, y: p.y ?? 0, d });
    });
    return out;
  };
  const isFallen = (n: Node) => {
    if (n.road || hazard(n.surface)) return false;
    const near = routeNear(n.ix * CELL, n.iz * CELL);
    return near.length > 0 && near.every((r) => r.y > n.h + 4);
  };
  const fallen = new Set<string>();
  for (const [k, n] of nodes) if (isFallen(n)) fallen.add(k);
  // Where you go over the edge: a step from somewhere not fallen to somewhere fallen.
  const edges = new Map<number, { i: number; x: number; z: number; y: number; n: number }>();
  for (const [to, froms] of back) {
    if (!fallen.has(to)) continue;
    for (const f of froms) {
      if (fallen.has(f)) continue;
      const n = nodes.get(f)!;
      // Only from on (or right beside) the road, at its level: not wandering the floor
      // under a bridge.
      const near = routeNear(n.ix * CELL, n.iz * CELL).sort((a, b) => a.d - b.d)[0];
      if (!near) continue;
      const rp = pts[near.i]!;
      const half = (rp.width ?? pkg.trackData.defaultWidth) / 2;
      if (near.d > half + 8 || Math.abs(n.h - near.y) > 1.5) continue;
      const e = edges.get(near.i) ?? { i: near.i, x: n.ix * CELL, z: n.iz * CELL, y: n.h, n: 0 };
      e.n++;
      if (process.env.EDGES)
        console.log(
          "EDGE",
          near.i,
          f,
          n.surface,
          "->",
          to,
          nodes.get(to)!.h.toFixed(1),
          nodes.get(to)!.surface,
        );
      edges.set(near.i, e);
    }
  }
  // Runs of route points with a drop-off beside them.
  const dropRuns: { from: number; to: number; game: [number, number, number]; edges: number }[] =
    [];
  for (const i of [...edges.keys()].sort((a, b) => a - b)) {
    const e = edges.get(i)!;
    const last = dropRuns[dropRuns.length - 1];
    if (last && i - last.to <= 2) {
      last.to = i;
      last.edges += e.n;
    } else
      dropRuns.push({
        from: i,
        to: i,
        game: [+e.x.toFixed(1), +e.y.toFixed(1), +e.z.toFixed(1)],
        edges: e.n,
      });
  }
  // Something solid just above the road (a hidden floor poking through: you'd hover on it).
  const covered: { i: number; game: [number, number, number]; above: number; surface: string }[] =
    [];
  pts.forEach((p, i) => {
    for (let a = -3; a <= 3; a++) {
      const q = pts[(i + 1) % pts.length]!;
      const l = Math.hypot(q.x - p.x, q.z - p.z) || 1;
      const half = (p.width ?? pkg.trackData.defaultWidth) / 2 - 1;
      const x = p.x + (-(q.z - p.z) / l) * (a / 3) * half;
      const z = p.z + ((q.x - p.x) / l) * (a / 3) * half;
      const road = floorAt(m, x, z, (p.y ?? 0) + 0.3);
      const top = floorAt(m, x, z, (p.y ?? 0) + 3);
      if (!road || !top) continue;
      const s = m.surfaces[m.floors.surf[top.tri]!]!;
      if (top.height > road.height + 0.15 && !m.defs[s]?.road) {
        covered.push({
          i,
          game: [+x.toFixed(1), +top.height.toFixed(2), +z.toFixed(1)],
          above: +(top.height - road.height).toFixed(2),
          surface: s,
        });
        break;
      }
    }
  });

  // Holes, grouped (4 m).
  const holeGroups: { game: [number, number, number]; n: number }[] = [];
  for (const h of holes) {
    const g = holeGroups.find((q) => Math.hypot(q.game[0] - h.x, q.game[2] - h.z) < 6);
    if (g) g.n++;
    else holeGroups.push({ game: [+h.x.toFixed(1), +h.y.toFixed(1), +h.z.toFixed(1)], n: 1 });
  }

  // Clusters of traps, falls and far-off cells.
  const kindOf = new Map<string, "trap" | "far" | "fallen">();
  for (const [k, n] of nodes) {
    if (!ok.has(k)) kindOf.set(k, "trap");
    else if (fallen.has(k)) kindOf.set(k, "fallen");
    else if (!n.road && distTo(n.ix * CELL, n.iz * CELL) > FAR_M) kindOf.set(k, "far");
  }
  const seen = new Set<string>();
  const clusters: {
    kind: string;
    cells: number;
    game: [number, number, number];
    blender: [number, number, number];
    fromRoad: number;
    surfaces: string[];
  }[] = [];
  for (const [k, kind] of kindOf) {
    if (seen.has(k)) continue;
    const stack = [k];
    seen.add(k);
    const members: Node[] = [];
    while (stack.length) {
      const c = stack.pop()!;
      const n = nodes.get(c)!;
      members.push(n);
      for (const [dx, dz] of DIRS)
        for (let dh = -3; dh <= 3; dh++) {
          const k2 = `${n.ix + dx},${n.iz + dz},${Math.round(n.h) + dh}`;
          if (!seen.has(k2) && kindOf.get(k2) === kind) {
            seen.add(k2);
            stack.push(k2);
          }
        }
    }
    const cx = (members.reduce((a, n) => a + n.ix, 0) / members.length) * CELL;
    const cz = (members.reduce((a, n) => a + n.iz, 0) / members.length) * CELL;
    const cy = members.reduce((a, n) => a + n.h, 0) / members.length;
    clusters.push({
      kind,
      cells: members.length,
      game: [+cx.toFixed(1), +cy.toFixed(1), +cz.toFixed(1)],
      blender: [+cx.toFixed(1), +(-cz).toFixed(1), +cy.toFixed(1)],
      fromRoad: +Math.min(...members.map((n) => distTo(n.ix * CELL, n.iz * CELL))).toFixed(1),
      surfaces: [...new Set(members.map((n) => n.surface))],
    });
  }
  clusters.sort((a, b) => b.cells - a.cells);

  // The map: north (-z game = +y Blender) up.
  const S = 2;
  const W = gw * S;
  const H = gh * S;
  const img = new Uint8Array(W * H * 3).fill(24);
  const put = (ix: number, iz: number, c: [number, number, number]) => {
    const px = (ix - gx0) * S;
    const py = (iz - gz0) * S;
    for (let a = 0; a < S; a++)
      for (let bb = 0; bb < S; bb++) {
        const o = ((py + bb) * W + px + a) * 3;
        img[o] = c[0];
        img[o + 1] = c[1];
        img[o + 2] = c[2];
      }
  };
  for (const n of nodes.values()) put(n.ix, n.iz, n.road ? [235, 235, 235] : [96, 104, 96]);
  for (const [k, kind] of kindOf) {
    const n = nodes.get(k)!;
    put(
      n.ix,
      n.iz,
      kind === "trap" ? [235, 40, 40] : kind === "fallen" ? [190, 60, 220] : [255, 150, 30],
    );
  }
  await mkdir(OUT, { recursive: true });
  await writeFile(new URL(`${track}-oob.png`, OUT), png(W, H, img));
  const traps = clusters.filter((c) => c.kind === "trap");
  const far = clusters.filter((c) => c.kind === "far");
  await writeFile(
    new URL(`${track}-oob.json`, OUT),
    JSON.stringify(
      {
        track,
        reachable: nodes.size,
        holes: holeGroups,
        traps,
        dropRuns,
        covered,
        far,
        fallen: clusters.filter((c) => c.kind === "fallen"),
      },
      null,
      1,
    ),
  );
  console.log(
    `${track}: ${nodes.size} cells reachable, ${traps.length} trap areas (${traps.reduce((a, c) => a + c.cells, 0)} cells), ${far.length} far-off areas`,
  );
  console.log(
    `  ${dropRuns.length} drop-off stretches, ${covered.length} route points with something just above the road`,
  );
  console.log(`  ${holeGroups.length} holes (no floor: you'd fall out of the world)`);
  for (const h of holeGroups) console.log(`  hole at game ${h.game.join(", ")} (${h.n})`);
  for (const r of dropRuns)
    console.log(
      `  drop: route points ${r.from}-${r.to} at game ${r.game.join(", ")} (${r.edges} edges)`,
    );
  for (const c of covered.slice(0, 30))
    console.log(
      `  covered: point ${c.i} at game ${c.game.join(", ")}: ${c.surface} ${c.above} m above the road`,
    );
  for (const c of [...traps.slice(0, 25), ...far.slice(0, 15)])
    console.log(
      `  ${c.kind} ${c.cells} cells at game ${c.game.join(", ")} (Blender ${c.blender.join(", ")}), ${c.fromRoad} m from the route: ${c.surfaces.join(" ")}`,
    );
}

for (const t of TRACKS) it(`audit ${t}`, () => audit(t), 600_000);
