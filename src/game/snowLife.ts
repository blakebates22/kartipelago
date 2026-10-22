/**
 * Snow Dragon Pass's weather and life (game/snow.ts has the rules): the blizzard in
 * layers (veils of snow sweeping across the distance, snow driving past in the middle
 * distance, flakes whipping past the camera, powder blowing low across the road), the
 * prayer flags flapping, the monastery bells swaying and tolling, the avalanches down the
 * far slopes. Created by game/hazards.ts; nothing here touches a kart.
 *
 * Readability comes first: the flakes are small and sparse enough that the road, its
 * rails and its turn boards always show through, and the storm's strength is set per
 * place (fiercest on the exposed heights), never so thick the next bend disappears.
 */
import * as THREE from "three";
import type { Sfx } from "../audio/sfx";
import type { GroundQuery } from "../physics/ground";
import { createParticles, type ParticlePool } from "../render/particles";
import {
  avalancheAt,
  gust,
  linePoint,
  parseAvalanches,
  parseBlizzard,
  parseFlags,
  parsePoints,
  snowAt,
  type Avalanche,
  type BlizzardConfig,
  type FlagLine,
  type V3,
} from "./snow";

const isObj = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);

export interface SnowLife {
  render(t: number, dt: number, listener: { x: number; y: number; z: number }): void;
  /** How hard it's snowing round the listener right now (tests, the HUD). */
  readonly strength: number;
  dispose(): void;
}

export function hasSnowLife(entities: unknown[]): boolean {
  const kinds = new Set(["blizzard", "prayer_flags", "bells", "avalanches"]);
  return entities.some((e) => isObj(e) && kinds.has(String(e.type)));
}

const FLAG_COLORS = ["#2f6ec0", "#f2f0e8", "#c8322a", "#3a9a4a", "#e8c030"];

/** A tiling texture of driving snow: streaks slanting along +U. */
function veilTexture() {
  const c = document.createElement("canvas");
  c.width = 128;
  c.height = 128;
  const g = c.getContext("2d")!;
  g.clearRect(0, 0, 128, 128);
  let seed = 7;
  const r = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  for (let i = 0; i < 260; i++) {
    const x = r() * 128;
    const y = r() * 128;
    const len = 2 + r() * 7;
    g.fillStyle = `rgba(255,255,255,${0.25 + r() * 0.6})`;
    for (let k = 0; k < len; k++)
      g.fillRect(Math.floor(x + k) % 128, Math.floor(y + k * 0.35) % 128, 1, 1);
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.magFilter = THREE.NearestFilter;
  t.minFilter = THREE.NearestFilter;
  t.generateMipmaps = false;
  return t;
}

export function createSnowLife(opts: {
  group: THREE.Group;
  entities: unknown[];
  ground: GroundQuery;
  sfx?: Sfx;
  volume: () => number;
  clock: () => number;
  quiet?: boolean;
  headless?: boolean;
}): SnowLife {
  const { group } = opts;
  let blizzard: BlizzardConfig | undefined;
  let flags: FlagLine[] = [];
  let bells: V3[] = [];
  let avalanches: Avalanche[] = [];
  for (const e of opts.entities) {
    if (!isObj(e)) continue;
    if (e.type === "blizzard") blizzard = parseBlizzard(e);
    else if (e.type === "prayer_flags") flags = parseFlags(e);
    else if (e.type === "bells") bells = parsePoints(e);
    else if (e.type === "avalanches") avalanches = parseAvalanches(e);
  }
  const disposers: (() => void)[] = [];
  let strength = 0.5;

  if (opts.headless)
    return {
      render(t, _dt, l) {
        if (blizzard) strength = snowAt(blizzard, l.x, l.y, l.z) * gust(t);
      },
      get strength() {
        return strength;
      },
      dispose() {},
    };

  // ---- the blizzard's layers
  let mid: ParticlePool | undefined;
  let near: ParticlePool | undefined;
  let low: ParticlePool | undefined;
  const veils: { mesh: THREE.Mesh; mat: THREE.MeshBasicMaterial; tex: THREE.Texture }[] = [];
  if (blizzard) {
    mid = createParticles(group, { max: 1600, size: 0.2, gravity: 0, opacity: 0.9 });
    near = createParticles(group, { max: 160, size: 0.32, gravity: 0, opacity: 0.85 });
    low = createParticles(group, { max: 500, size: 0.7, gravity: 0, opacity: 0.55 });
    disposers.push(() => {
      mid?.dispose();
      near?.dispose();
      low?.dispose();
    });
    // Veils: open cylinders round the camera, snow streaks drifting across them.
    for (const [radius, height, rep] of [
      [70, 70, 6],
      [170, 140, 10],
    ] as const) {
      const tex = veilTexture();
      tex.repeat.set(rep, rep * (height / radius) * 0.35);
      const mat = new THREE.MeshBasicMaterial({
        map: tex,
        transparent: true,
        depthWrite: false,
        side: THREE.DoubleSide,
        opacity: 0.3,
        fog: true,
      });
      const geo = new THREE.CylinderGeometry(radius, radius, height, 24, 1, true);
      const mesh = new THREE.Mesh(geo, mat);
      mesh.renderOrder = 2;
      mesh.frustumCulled = false;
      group.add(mesh);
      veils.push({ mesh, mat, tex });
      disposers.push(() => {
        group.remove(mesh);
        geo.dispose();
        mat.dispose();
        tex.dispose();
      });
    }
  }
  const acc = { mid: 0, near: 0, low: 0 };

  // ---- the prayer flags: one mesh, its flags' lower edges moved every frame
  let flagMesh: THREE.Mesh | undefined;
  let flagPos: THREE.BufferAttribute | undefined;
  const flagTops: { x: number; y: number; z: number; dx: number; dz: number; ph: number }[] = [];
  if (flags.length) {
    const pos: number[] = [];
    const col: number[] = [];
    const idx: number[] = [];
    const cords: number[] = [];
    const c = new THREE.Color();
    flags.forEach((f, li) => {
      const len = Math.hypot(f.b.x - f.a.x, f.b.z - f.a.z);
      const n = Math.max(3, Math.floor(len / 1.3));
      const dx = (f.b.x - f.a.x) / (len || 1);
      const dz = (f.b.z - f.a.z) / (len || 1);
      for (let k = 0; k <= 12; k++) {
        const p = linePoint(f, k / 12);
        const q = linePoint(f, (k + 1) / 12);
        if (k < 12) cords.push(p.x, p.y, p.z, q.x, q.y, q.z);
      }
      for (let i = 0; i < n; i++) {
        const p = linePoint(f, (i + 0.5) / n);
        const base = pos.length / 3;
        // Top edge on the cord (two verts), bottom edge 0.9 m below (moved each frame).
        const w = 0.4;
        pos.push(p.x - dx * w, p.y, p.z - dz * w, p.x + dx * w, p.y, p.z + dz * w);
        pos.push(p.x + dx * w, p.y - 0.9, p.z + dz * w, p.x - dx * w, p.y - 0.9, p.z - dz * w);
        c.set(FLAG_COLORS[(i + li) % FLAG_COLORS.length]!);
        for (let k = 0; k < 4; k++) col.push(c.r, c.g, c.b);
        idx.push(base, base + 1, base + 2, base, base + 2, base + 3);
        flagTops.push({ x: p.x, y: p.y, z: p.z, dx, dz, ph: i * 0.7 + li * 1.3 });
      }
    });
    const geo = new THREE.BufferGeometry();
    flagPos = new THREE.BufferAttribute(new Float32Array(pos), 3);
    flagPos.setUsage(THREE.DynamicDrawUsage);
    geo.setAttribute("position", flagPos);
    geo.setAttribute("color", new THREE.BufferAttribute(new Float32Array(col), 3));
    geo.setIndex(idx);
    const mat = new THREE.MeshLambertMaterial({ vertexColors: true, side: THREE.DoubleSide });
    flagMesh = new THREE.Mesh(geo, mat);
    flagMesh.frustumCulled = false;
    group.add(flagMesh);
    const cg = new THREE.BufferGeometry();
    cg.setAttribute("position", new THREE.BufferAttribute(new Float32Array(cords), 3));
    const cm = new THREE.LineBasicMaterial({ color: "#5a4a3a" });
    const lines = new THREE.LineSegments(cg, cm);
    group.add(lines);
    disposers.push(() => {
      group.remove(flagMesh!, lines);
      geo.dispose();
      mat.dispose();
      cg.dispose();
      cm.dispose();
    });
  }

  // ---- the bells: bronze cones swinging from their frames
  const bellMeshes: THREE.Mesh[] = [];
  if (bells.length) {
    const geo = new THREE.ConeGeometry(0.75, 1.4, 8, 1, true).translate(0, -0.7, 0);
    const mat = new THREE.MeshLambertMaterial({ color: "#b48a34", side: THREE.DoubleSide });
    for (const b of bells) {
      const m = new THREE.Mesh(geo, mat);
      m.position.set(b.x, b.y + 0.7, b.z);
      group.add(m);
      bellMeshes.push(m);
    }
    disposers.push(() => {
      for (const m of bellMeshes) group.remove(m);
      geo.dispose();
      mat.dispose();
    });
  }
  let tollIn = 4;

  // ---- avalanches: big slow powder puffs rolling down
  const powder = avalanches.length
    ? createParticles(group, { max: 900, size: 7, gravity: -0.4, opacity: 0.7 })
    : undefined;
  if (powder) disposers.push(() => powder.dispose());
  const roared = avalanches.map(() => -1);

  const W = blizzard?.wind ?? { x: 1, z: 0 };

  return {
    get strength() {
      return strength;
    },
    render(t, dt, l) {
      const vol = opts.quiet ? 0 : opts.volume();
      // ---- the blizzard
      if (blizzard && mid && near && low) {
        const k = snowAt(blizzard, l.x, l.y, l.z);
        const g = gust(t);
        strength += (k * g - strength) * (1 - Math.exp(-dt * 1.5));
        const s = Math.max(0, strength);
        // Middle distance: driving snow, slanting with the wind.
        acc.mid = Math.min(3, acc.mid + dt * 520 * s);
        for (; acc.mid >= 1; acc.mid -= 1) {
          const sp = 9 + Math.random() * 6;
          // Start upwind so the snow is drifting through the view, not appearing in it.
          const ox = (Math.random() - 0.5) * 90 - W.x * 20;
          const oz = (Math.random() - 0.5) * 90 - W.z * 20;
          mid.emit(
            l.x + ox,
            l.y + 2 + Math.random() * 26,
            l.z + oz,
            W.x * sp,
            -2.6 - Math.random() * 1.6,
            W.z * sp,
            4.5,
            Math.random() < 0.8 ? 0xffffff : 0xdce6f8,
          );
        }
        // Near the camera: a few flakes whipping past fast (fewer: they mustn't blind).
        acc.near = Math.min(3, acc.near + dt * 55 * s * s);
        for (; acc.near >= 1; acc.near -= 1) {
          const sp = 20 + Math.random() * 10;
          near.emit(
            l.x - W.x * 14 + (Math.random() - 0.5) * 18,
            l.y + 0.5 + Math.random() * 5,
            l.z - W.z * 14 + (Math.random() - 0.5) * 18,
            W.x * sp,
            -1.5,
            W.z * sp,
            1.6,
            0xffffff,
          );
        }
        // Low: powder blowing across the ground.
        acc.low = Math.min(3, acc.low + dt * 70 * s);
        for (; acc.low >= 1; acc.low -= 1) {
          const x = l.x + (Math.random() - 0.5) * 60 - W.x * 15;
          const z = l.z + (Math.random() - 0.5) * 60 - W.z * 15;
          const gy = opts.ground.at(x, z, l.y + 6).height;
          if (Math.abs(gy - l.y) > 12) continue;
          const sp = 11 + Math.random() * 5;
          low.emit(x, gy + 0.3, z, W.x * sp, 0.4 + Math.random() * 0.6, W.z * sp, 1.8, 0xf4f8ff);
        }
        mid.step(dt);
        near.step(dt);
        low.step(dt);
        // The veils: centred on the camera, the streaks drifting with the wind.
        veils.forEach((v, i) => {
          v.mesh.position.set(l.x, l.y + (i ? 30 : 12), l.z);
          v.tex.offset.x = (v.tex.offset.x + dt * (0.05 + 0.03 * i) * g) % 1;
          v.tex.offset.y = (v.tex.offset.y - dt * 0.05) % 1;
          v.mat.opacity = Math.min(0.5, (i ? 0.38 : 0.22) * s);
        });
      }
      // ---- the prayer flags: each flag's lower edge streams out with the wind, flapping
      if (flagPos) {
        const a = flagPos.array as Float32Array;
        const gs = blizzard ? gust(t) : 1;
        flagTops.forEach((f, i) => {
          if (Math.abs(f.x - l.x) > 220 || Math.abs(f.z - l.z) > 220) return;
          const flap = Math.sin(t * 7 + f.ph) * 0.25 + Math.sin(t * 13 + f.ph * 2) * 0.1;
          const out = 0.45 * gs;
          const w = 0.4;
          const bx = W.x * out + f.dz * flap * 0.3;
          const bz = W.z * out - f.dx * flap * 0.3;
          const by = f.y - 0.9 + Math.abs(out) * 0.35 + flap * 0.15;
          const o = i * 12 + 6;
          a[o] = f.x + f.dx * w + bx;
          a[o + 1] = by;
          a[o + 2] = f.z + f.dz * w + bz;
          a[o + 3] = f.x - f.dx * w + bx;
          a[o + 4] = by;
          a[o + 5] = f.z - f.dz * w + bz;
        });
        flagPos.needsUpdate = true;
      }
      // ---- the bells
      bellMeshes.forEach((m, i) => {
        m.rotation.x = 0.12 * Math.sin(t * 1.3 + i);
        m.rotation.z = 0.08 * Math.sin(t * 0.9 + i * 2);
      });
      if (bells.length) {
        tollIn -= dt;
        if (tollIn <= 0) {
          tollIn = 9 + Math.random() * 7;
          let d = Infinity;
          for (const b of bells) d = Math.min(d, Math.hypot(b.x - l.x, b.y - l.y, b.z - l.z));
          if (d < 260) opts.sfx?.monasteryBell?.(vol * Math.max(0.15, 1 - d / 260));
        }
      }
      // ---- avalanches
      if (powder) {
        const rc = opts.clock();
        avalanches.forEach((av, i) => {
          const st = avalancheAt(av, rc);
          if (!st.running) return;
          const cycle = Math.floor((rc - av.offset) / av.period);
          if (roared[i] !== cycle) {
            roared[i] = cycle;
            const d = Math.hypot(av.a.x - l.x, av.a.z - l.z);
            if (d < 700) opts.sfx?.avalanche?.(vol * Math.max(0.1, 1 - d / 700));
          }
          const x = av.a.x + (av.b.x - av.a.x) * st.u;
          const y = av.a.y + (av.b.y - av.a.y) * st.u;
          const z = av.a.z + (av.b.z - av.a.z) * st.u;
          const n = Math.ceil(dt * 40);
          for (let k = 0; k < n; k++)
            powder.emit(
              x + (Math.random() - 0.5) * 18,
              y + Math.random() * 4,
              z + (Math.random() - 0.5) * 18,
              (av.b.x - av.a.x) * 0.02 + (Math.random() - 0.5) * 3,
              1 + Math.random() * 2,
              (av.b.z - av.a.z) * 0.02 + (Math.random() - 0.5) * 3,
              3.5,
              Math.random() < 0.7 ? 0xf4f8ff : 0xd8e2f0,
            );
        });
        powder.step(dt);
      }
    },
    dispose() {
      for (const d of disposers) d();
    },
  };
}
