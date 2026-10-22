/**
 * Dragon Isles' life (game/isles.ts has the rules): the great dragon flying its loop in
 * step with the race, its shadow sweeping the road, the villagers cheering, dancing,
 * fishing, standing guard and bowing all together as it passes, the festival going
 * quiet under it, the little dragons and the mill wheels. Created by game/hazards.ts;
 * nothing here touches a kart.
 */
import * as THREE from "three";
import type { Sfx } from "../audio/sfx";
import type { GroundQuery } from "../physics/ground";
import type { Track } from "../world/track";
import {
  awe,
  dragonHead,
  littleDragonAt,
  nearestSample,
  parseCrane,
  parseIslesDragon,
  parseLittleDragons,
  parseVillagers,
  parseWaterwheel,
  placeDragon,
  stepDragon,
  type DragonFlight,
  type IslesDragonConfig,
  type LittleDragonsConfig,
  type Villager,
} from "./isles";
import {
  createCraneView,
  createCrowdView,
  createSerpentView,
  createShadowView,
  createWaterwheelView,
  type CraneView,
  type CrowdView,
  type SerpentView,
  type ShadowView,
  type WheelView,
} from "../render/islesFx";

const isObj = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);

export interface IslesLife {
  render(t: number, dt: number, listener: { x: number; y: number; z: number }): void;
  /** The great dragon's head (for tests and the camera), if the course has one. */
  readonly dragon?: { x: number; y: number; z: number };
  /** How hushed the festival is round the listener (0..1): the dragon's passing. */
  hush(): number;
  readonly villagers: Villager[];
  /** Put the dragon where it should be for lap distance s (tools and tests). */
  placeDragon(s: number): void;
  dispose(): void;
}

export function hasIslesLife(entities: unknown[]): boolean {
  const kinds = new Set(["isles_dragon", "villagers", "waterwheel", "little_dragons", "crane"]);
  return entities.some((e) => isObj(e) && kinds.has(String(e.type)));
}

export function createIslesLife(opts: {
  group: THREE.Group;
  entities: unknown[];
  track: Track;
  ground: GroundQuery;
  sfx?: Sfx;
  volume: () => number;
  quiet?: boolean;
  headless?: boolean;
}): IslesLife {
  const { group, ground } = opts;
  let dragonCfg: IslesDragonConfig | undefined;
  const villagers: Villager[] = [];
  const wheels: WheelView[] = [];
  const cranes: CraneView[] = [];
  const littles: { cfg: LittleDragonsConfig; views: SerpentView[] }[] = [];
  for (const e of opts.entities) {
    if (!isObj(e)) continue;
    if (e.type === "isles_dragon") dragonCfg = parseIslesDragon(e);
    else if (e.type === "villagers") villagers.push(...parseVillagers(e));
    else if (e.type === "crane") {
      if (!opts.headless) cranes.push(createCraneView(group, parseCrane(e)));
    } else if (e.type === "waterwheel") {
      if (!opts.headless) wheels.push(createWaterwheelView(group, parseWaterwheel(e)));
    } else if (e.type === "little_dragons") {
      const cfg = parseLittleDragons(e);
      littles.push({
        cfg,
        views: opts.headless
          ? []
          : Array.from({ length: cfg.count }, (_, k) =>
              createSerpentView(group, 0.11 + 0.02 * (k % 2), {
                simple: true,
                colors:
                  k % 2
                    ? { body: "#e8483a", belly: "#f2c64a" }
                    : { body: "#3a8ad8", belly: "#f4ecd8" },
              }),
            ),
      });
    }
  }

  // ---- the great dragon
  const flight: DragonFlight = { u: 0, speed: 20 };
  const head = new THREE.Vector3();
  let serpent: SerpentView | undefined;
  let shadow: ShadowView | undefined;
  if (dragonCfg) {
    const p = dragonHead(dragonCfg, 0, 0);
    head.set(p.x, p.y, p.z);
    if (!opts.headless) {
      serpent = createSerpentView(group, dragonCfg.size);
      shadow = createShadowView(group, dragonCfg.size);
    }
  }
  const crowd: CrowdView | undefined =
    !opts.headless && villagers.length ? createCrowdView(group, villagers) : undefined;

  let hint = 0;
  let hushNow = 0;
  let callIn = 6;
  const look = { at: new THREE.Vector3(), amount: 0 };
  const groundAt = (x: number, z: number, y: number) => ground.at(x, z, y).height;
  // Points along the body the kingdom reacts to (head, middle, tail end).
  const body = [new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3()];

  function aweAt(x: number, y: number, z: number) {
    if (!dragonCfg) return 0;
    let best = 0;
    for (const b of body) best = Math.max(best, awe(Math.hypot(b.x - x, b.z - z), b.y - y));
    return best;
  }

  return {
    villagers,
    get dragon() {
      return dragonCfg ? { x: head.x, y: head.y, z: head.z } : undefined;
    },
    hush: () => hushNow,
    placeDragon(s) {
      if (dragonCfg) placeDragon(dragonCfg, flight, s);
    },
    render(t, dt, listener) {
      const vol = opts.quiet ? 0 : opts.volume();
      if (dragonCfg) {
        // Where the listener is round the lap sets where the dragon should be.
        const samples = opts.track.samples;
        hint = nearestSample(samples, listener.x, listener.z, hint);
        const s = samples[hint]?.dist ?? 0;
        stepDragon(dragonCfg, flight, s, Math.min(0.1, dt));
        const p = dragonHead(dragonCfg, flight.u, t);
        head.set(p.x, p.y, p.z);
        const far = Math.hypot(listener.x - head.x, listener.y - head.y, listener.z - head.z);
        look.at.set(listener.x, listener.y + 2, listener.z);
        look.amount = Math.max(0, Math.min(1, (200 - far) / 120)) * 0.7;
        if (serpent) {
          serpent.update(head, t, look, groundAt);
          const sp = serpent.spine;
          body[0]!.copy(sp[0]!);
          body[1]!.copy(sp[Math.floor(sp.length / 2)]!);
          body[2]!.copy(sp[Math.floor(sp.length * 0.85)]!);
          shadow?.update(sp, groundAt);
        } else for (const b of body) b.copy(head);
        // The festival hushes under it; it calls now and then when near.
        const target = aweAt(listener.x, listener.y, listener.z);
        hushNow += (target - hushNow) * (1 - Math.exp(-2 * dt));
        callIn -= dt;
        if (callIn <= 0 && far < 260) {
          opts.sfx?.dragonCall?.(vol * Math.max(0.25, 1 - far / 260));
          callIn = 16 + Math.random() * 10;
        }
      }
      crowd?.update(t, new THREE.Vector3(listener.x, listener.y, listener.z), (i) => {
        const v = villagers[i]!;
        return v.role === "guard" ? 0 : aweAt(v.x, v.y, v.z);
      });
      for (const w of wheels) w.update(t);
      for (const k of cranes) k.update(t);
      for (const l of littles)
        l.views.forEach((v, k) => {
          const p = littleDragonAt(l.cfg, k, t);
          v.update(new THREE.Vector3(p.x, p.y, p.z), t, { at: look.at, amount: 0 });
        });
    },
    dispose() {
      serpent?.dispose();
      shadow?.dispose();
      crowd?.dispose();
      for (const w of wheels) w.dispose();
      for (const k of cranes) k.dispose();
      for (const l of littles) for (const v of l.views) v.dispose();
    },
  };
}
