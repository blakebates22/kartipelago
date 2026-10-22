/**
 * Impact Depths' life, light and air at run time (the entities are described in
 * game/depths.ts): grazing triceratops, raptor packs crossing the road on a beat (solid
 * while they cross: a knock and a slowdown), shooting stars and the fireball at the
 * start, the asteroid's smoke, the core, drifting motes, coloured lights near the
 * camera, and the air (fog, light and sound) blending from world to world as you go
 * down. Created by game/hazards.ts; nothing here changes how a kart drives.
 */
import * as THREE from "three";
import type { Sfx } from "../audio/sfx";
import type { GroundQuery } from "../physics/ground";
import type { KartState } from "../vehicles/kart";
import type { SolidCircle } from "../world/solids";
import {
  airAt,
  grazerAt,
  introAt,
  parseAtmosphere,
  parseCore,
  parseGlow,
  parseMeteors,
  parseMotes,
  parsePlume,
  parseTriceratops,
  SOUND_KINDS,
  type Air,
  type AtmosphereConfig,
  type GlowConfig,
  type SoundKind,
  type TriceratopsConfig,
} from "./depths";
import { crossingAt, parseCrossing, type CrossingConfig, type CrossingPhase } from "./movers";
import {
  createCoreView,
  createMeteorView,
  createMotesView,
  createPlumeView,
  createRaptorPackView,
  createTriceratopsView,
  type CoreView,
  type DriftView,
  type GrazerView,
  type MeteorView,
  type RaptorPackView,
} from "../render/depthsFx";

const isObj = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const num = (v: unknown, d: number) => (typeof v === "number" && Number.isFinite(v) ? v : d);

/** How many coloured lights shine at once (the ones nearest the camera). */
const GLOW_LIGHTS = 4;

interface Pack {
  cfg: CrossingConfig;
  count: number;
  phase: CrossingPhase;
  last: CrossingPhase;
  x: number;
  y: number;
  z: number;
  heading: number;
  run: number;
  solids: SolidCircle[];
  view?: RaptorPackView;
  chirp: number;
}

interface Grazer {
  cfg: TriceratopsConfig;
  x: number;
  y: number;
  z: number;
  heading: number;
  walk: number;
  graze: number;
  bellow: number;
  solids: SolidCircle[];
  view?: GrazerView;
  called: boolean;
}

export interface DepthsLife {
  readonly solids: SolidCircle[];
  /** Once per physics step after the karts move: the creatures go where the clocks say. */
  step(dt: number): void;
  /** A kart touching a crossing pack slows down (the solid circles push it out). */
  stepKart(s: KartState, dt: number): { bumped?: boolean };
  render(t: number, dt: number, listener: { x: number; y: number; z: number }): void;
  /** The air where the listener is (for tests and tools). */
  air(x: number, y: number, z: number): Air | undefined;
  readonly grazers: { x: number; y: number; z: number }[];
  dispose(): void;
}

/** Nothing here: tracks without any of these entities get this. */
export function hasDepthsLife(entities: unknown[]): boolean {
  const kinds = new Set([
    "triceratops",
    "raptors",
    "meteors",
    "plume",
    "core",
    "motes",
    "glow",
    "atmosphere",
  ]);
  return entities.some((e) => isObj(e) && kinds.has(String(e.type)));
}

export function createDepthsLife(opts: {
  group: THREE.Group;
  entities: unknown[];
  ground: GroundQuery;
  sfx?: Sfx;
  volume: () => number;
  quiet?: boolean;
  headless?: boolean;
  clock: () => number;
  slow: number;
  /** Turns the festival's sound down (0..1): Dragon Isles' hush as the dragon passes. */
  hush?: () => number;
}): DepthsLife {
  const { group, ground } = opts;
  const packs: Pack[] = [];
  const grazers: Grazer[] = [];
  const drifts: DriftView[] = [];
  let core: { view?: CoreView; x: number; y: number; z: number } | undefined;
  let meteors: { view?: MeteorView; intro: boolean } | undefined;
  const glows: GlowConfig[] = [];
  let atmosphere: AtmosphereConfig | undefined;
  for (const e of opts.entities) {
    if (!isObj(e)) continue;
    if (e.type === "raptors") {
      const cfg = parseCrossing(e, false, false);
      const count = Math.max(1, Math.min(5, Math.round(num(e.count, 3))));
      packs.push({
        cfg,
        count,
        phase: "idle",
        last: "idle",
        x: cfg.a.x,
        y: cfg.a.y,
        z: cfg.a.z,
        heading: 0,
        run: 0,
        solids: Array.from({ length: count }, () => ({
          kind: "circle" as const,
          look: "creature" as const,
          x: 1e6,
          z: 1e6,
          radius: 0.9,
          height: -1e6,
        })),
        view: opts.headless ? undefined : createRaptorPackView(group, count),
        chirp: 0,
      });
    } else if (e.type === "triceratops") {
      const cfg = parseTriceratops(e);
      grazers.push({
        cfg,
        x: cfg.x,
        y: cfg.y,
        z: cfg.z,
        heading: cfg.heading,
        walk: 0,
        graze: 0,
        bellow: 0,
        solids: [0, 1].map(() => ({
          kind: "circle" as const,
          look: "creature" as const,
          x: 1e6,
          z: 1e6,
          radius: 1.9 * cfg.scale,
          height: 1e3,
        })),
        view: opts.headless ? undefined : createTriceratopsView(group, cfg.scale),
        called: false,
      });
    } else if (e.type === "meteors") {
      const m = parseMeteors(e);
      const target = new THREE.Vector3(m.x, m.y, m.z);
      // The fireball comes in from high over the start, behind the grid.
      const from = target.clone().add(new THREE.Vector3(-620, 420, 160));
      meteors = {
        intro: m.intro,
        view: opts.headless ? undefined : createMeteorView(group, target, from, m.rate),
      };
    } else if (e.type === "plume") {
      if (!opts.headless) drifts.push(createPlumeView(group, parsePlume(e)));
    } else if (e.type === "motes") {
      if (!opts.headless) drifts.push(createMotesView(group, parseMotes(e)));
    } else if (e.type === "core") {
      const c = parseCore(e);
      core = { x: c.x, y: c.y, z: c.z, view: opts.headless ? undefined : createCoreView(group, c) };
    } else if (e.type === "glow") glows.push(parseGlow(e));
    else if (e.type === "atmosphere") atmosphere = parseAtmosphere(e);
  }
  const solids: SolidCircle[] = [
    ...packs.flatMap((p) => p.solids),
    ...grazers.flatMap((g) => g.solids),
  ];

  function placePack(p: Pack) {
    const c = crossingAt(p.cfg, opts.clock());
    p.phase = c.phase;
    p.heading = c.heading;
    p.x = c.x;
    p.z = c.z;
    p.y = ground.at(c.x, c.z, Math.max(c.y, p.y) + 4).height;
    p.run = c.u * Math.hypot(p.cfg.b.x - p.cfg.a.x, p.cfg.b.z - p.cfg.a.z);
    const fx = Math.sin(p.heading);
    const fz = Math.cos(p.heading);
    p.solids.forEach((sd, k) => {
      if (p.phase !== "crossing" || !p.view) {
        // (Headless: the same formation the view uses.)
        const o = p.view?.offset(k) ?? {
          along: -k * 2.8,
          across: k % 2 ? 1.8 : -1.6 * Math.min(1, k),
        };
        if (p.phase !== "crossing") {
          sd.x = 1e6;
          sd.z = 1e6;
          sd.height = -1e6;
          return;
        }
        sd.x = p.x + fx * o.along + fz * o.across;
        sd.z = p.z + fz * o.along - fx * o.across;
        sd.height = p.y + 2.2;
        return;
      }
      const o = p.view.offset(k);
      sd.x = p.x + fx * o.along + fz * o.across;
      sd.z = p.z + fz * o.along - fx * o.across;
      sd.height = p.y + 2.2;
    });
  }

  function placeGrazer(g: Grazer, t: number) {
    const pose = grazerAt(g.cfg, t);
    g.x = pose.x;
    g.z = pose.z;
    g.heading = pose.heading;
    g.walk = pose.walk;
    g.graze = pose.graze;
    g.bellow = pose.bellow;
    g.y = ground.at(g.x, g.z, g.y + 3).height;
    const fx = Math.sin(g.heading);
    const fz = Math.cos(g.heading);
    const s = g.cfg.scale;
    g.solids[0]!.x = g.x + fx * 2.4 * s;
    g.solids[0]!.z = g.z + fz * 2.4 * s;
    g.solids[1]!.x = g.x - fx * 1.8 * s;
    g.solids[1]!.z = g.z - fz * 1.8 * s;
  }
  let time = 0;
  for (const g of grazers) {
    g.y = ground.at(g.x, g.z, g.y + 30).height;
    placeGrazer(g, 0);
  }

  // ---- the coloured lights and the air
  const lights: THREE.PointLight[] = [];
  if (!opts.headless && glows.length)
    for (let k = 0; k < Math.min(GLOW_LIGHTS, glows.length); k++) {
      const l = new THREE.PointLight(0xffffff, 0, 70, 1.4);
      l.castShadow = false;
      group.add(l);
      lights.push(l);
    }
  let scene: THREE.Scene | undefined;
  let sun: THREE.DirectionalLight | undefined;
  let hemi: THREE.HemisphereLight | undefined;
  let saved: { sun: number; sky: THREE.Color; ground: THREE.Color; hemi: number } | undefined;
  let cur: Air | undefined;
  const loops: Partial<Record<SoundKind, { set(v: number): void; stop(): void }>> = {};
  let nextBit = 2;

  function findScene() {
    let o: THREE.Object3D | null = group;
    while (o && !(o as THREE.Scene).isScene) o = o.parent;
    scene = (o as THREE.Scene) ?? undefined;
    scene?.traverse((c) => {
      if ((c as THREE.DirectionalLight).isDirectionalLight && !sun)
        sun = c as THREE.DirectionalLight;
      if ((c as THREE.HemisphereLight).isHemisphereLight && !hemi)
        hemi = c as THREE.HemisphereLight;
    });
    if (sun && hemi)
      saved = {
        sun: sun.intensity,
        sky: hemi.color.clone(),
        ground: hemi.groundColor.clone(),
        hemi: hemi.intensity,
      };
  }

  const smoothAir = (target: Air, dt: number) => {
    if (!cur) {
      cur = {
        ...target,
        fog: [...target.fog],
        sky: [...target.sky],
        ground: [...target.ground],
        sound: { ...target.sound },
      };
      return cur;
    }
    const k = 1 - Math.exp(-2.5 * dt);
    const m = (a: number, b: number) => a + (b - a) * k;
    for (let i = 0; i < 3; i++) {
      cur.fog[i] = m(cur.fog[i]!, target.fog[i]!);
      cur.sky[i] = m(cur.sky[i]!, target.sky[i]!);
      cur.ground[i] = m(cur.ground[i]!, target.ground[i]!);
    }
    cur.near = m(cur.near, target.near);
    cur.far = m(cur.far, target.far);
    cur.sun = m(cur.sun, target.sun);
    cur.hemi = m(cur.hemi, target.hemi);
    for (const s of SOUND_KINDS) cur.sound[s] = m(cur.sound[s], target.sound[s]);
    return cur;
  };

  return {
    solids,
    grazers,
    step(dt) {
      time += dt;
      for (const p of packs) placePack(p);
      for (const g of grazers) placeGrazer(g, time);
    },
    stepKart(s, dt) {
      const ev: { bumped?: boolean } = {};
      for (const p of packs) {
        if (p.phase !== "crossing") continue;
        for (const c of p.solids)
          if (Math.hypot(s.x - c.x, s.z - c.z) < c.radius + 1.3 && s.y < c.height) {
            s.speed *= Math.pow(opts.slow, dt * 6);
            ev.bumped = true;
          }
      }
      return ev;
    },
    render(t, dt, listener) {
      const vol = opts.quiet ? 0 : opts.volume();
      for (const g of grazers) {
        g.view?.update(g.x, g.y, g.z, g.heading, g.walk, g.graze, g.bellow, t);
        if (g.bellow > 0.5 && !g.called) {
          g.called = true;
          const far = Math.hypot(listener.x - g.x, listener.z - g.z);
          if (far < 120) opts.sfx?.grunt?.(vol * (1 - far / 120));
        } else if (g.bellow === 0) g.called = false;
      }
      for (const p of packs) {
        const far = Math.hypot(listener.x - p.x, listener.z - p.z);
        if (p.phase !== p.last) {
          if (p.phase !== "idle" && far < 110) opts.sfx?.raptor?.(vol * (1 - far / 110));
          p.last = p.phase;
        }
        const t0 = (((opts.clock() - p.cfg.offset) % p.cfg.period) + p.cfg.period) % p.cfg.period;
        const peek =
          p.phase === "warning"
            ? Math.min(
                1,
                (t0 - (p.cfg.period - p.cfg.travel - p.cfg.warn)) / Math.max(0.1, p.cfg.warn),
              )
            : 0;
        p.view?.update(p.x, p.y, p.z, p.heading, p.run, p.phase === "crossing", peek, t);
      }
      const cam = new THREE.Vector3(listener.x, listener.y, listener.z);
      for (const d of drifts) d.update(dt, cam);
      if (core?.view)
        core.view.update(
          t,
          dt,
          Math.hypot(listener.x - core.x, listener.y - core.y, listener.z - core.z),
        );
      // ---- the air
      let outdoors = 1;
      if (atmosphere && atmosphere.keys.length) {
        const target = airAt(atmosphere, listener.x, listener.y, listener.z);
        if (target) {
          const a = smoothAir(target, dt);
          outdoors = Math.max(0, Math.min(1, (a.sun - 0.8) / 1.6));
          if (!opts.headless) {
            if (!scene) findScene();
            if (scene?.fog instanceof THREE.Fog) {
              scene.fog.color.setRGB(a.fog[0], a.fog[1], a.fog[2]);
              scene.fog.near = a.near;
              scene.fog.far = a.far;
            }
            if (sun) sun.intensity = a.sun;
            if (hemi) {
              hemi.color.setRGB(a.sky[0], a.sky[1], a.sky[2]);
              hemi.groundColor.setRGB(a.ground[0], a.ground[1], a.ground[2]);
              hemi.intensity = a.hemi;
            }
          }
          // The sound of each world, faded into the next.
          if (!opts.quiet && opts.sfx?.ambience) {
            for (const kind of SOUND_KINDS) {
              const hushed = kind === "festival" ? 1 - 0.85 * (opts.hush?.() ?? 0) : 1;
              const v = a.sound[kind] * hushed;
              if (kind === "celebration") continue; // (no bed of noise)
              if (v > 0.02 && !loops[kind]) loops[kind] = opts.sfx.ambience(kind);
              loops[kind]?.set(vol * 0.42 * v);
            }
            nextBit -= dt;
            if (nextBit <= 0) {
              nextBit = 0.6 + Math.random() * 1.8;
              const pick = SOUND_KINDS.reduce(
                (best, k) => (a.sound[k] > a.sound[best] ? k : best),
                SOUND_KINDS[0]!,
              );
              const v = vol * a.sound[pick];
              if (pick === "chime") opts.sfx.chime?.(v);
              else if (pick === "drip") opts.sfx.drip?.(v);
              else if ((pick === "jungle" || pick === "garden") && Math.random() < 0.5)
                opts.sfx.bird?.(v);
              else if (pick === "harbour" && Math.random() < 0.35) opts.sfx.gull?.(v);
              else if (pick === "quarry" && Math.random() < 0.6) opts.sfx.chisel?.(v);
              else if (pick === "bells" && Math.random() < 0.18) opts.sfx.monasteryBell?.(v);
              else if (pick === "festival" && Math.random() < 0.4 * (1 - (opts.hush?.() ?? 0)))
                opts.sfx.festivalBit?.(v);
              else if (pick === "celebration" && Math.random() < 0.3) opts.sfx.festivalBit?.(v);
            }
          }
        }
      }
      // ---- shooting stars and the fireball
      if (meteors?.view) {
        const landed = meteors.view.update(
          dt,
          cam,
          outdoors,
          meteors.intro ? introAt(opts.clock()) : null,
        );
        if (landed) opts.sfx?.boom?.(vol * 0.9);
      }
      // ---- coloured light from the nearest glows
      if (lights.length) {
        const near = glows
          .map((g) => ({
            g,
            d: (g.x - listener.x) ** 2 + (g.y - listener.y) ** 2 + (g.z - listener.z) ** 2,
          }))
          .sort((a, b) => a.d - b.d)
          .slice(0, lights.length);
        near.forEach(({ g, d }, k) => {
          const l = lights[k]!;
          l.position.set(g.x, g.y, g.z);
          l.color.set(g.color);
          const fade = Math.max(0, Math.min(1, (80 - Math.sqrt(d)) / 30));
          l.intensity = 40 * fade * (0.9 + 0.1 * Math.sin(t * 3 + k));
        });
      }
    },
    air(x, y, z) {
      return atmosphere ? airAt(atmosphere, x, y, z) : undefined;
    },
    dispose() {
      for (const p of packs) p.view?.dispose();
      for (const g of grazers) g.view?.dispose();
      for (const d of drifts) d.dispose();
      core?.view?.dispose();
      meteors?.view?.dispose();
      for (const l of lights) l.removeFromParent();
      for (const k of SOUND_KINDS) loops[k]?.stop();
      if (saved && sun && hemi) {
        sun.intensity = saved.sun;
        hemi.color.copy(saved.sky);
        hemi.groundColor.copy(saved.ground);
        hemi.intensity = saved.hemi;
      }
    },
  };
}
