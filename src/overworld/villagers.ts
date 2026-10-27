/**
 * The overworlds' villagers (Blake, Oct 26): dinosaur folk walking about round their
 * homes in every part of every kingdom (and a few travellers on the roads between). Not
 * in karts: on foot, ambling from spot to spot, stopping to look round, stepping aside
 * for a kart coming at them, turning to face you when you stop by them. Each has a name
 * and a line to say (placeholders: the dialogue comes later).
 *
 * The homes are the build's `villager_home` entities: { "type": "villager_home", "x",
 * "z", "y", "r", "n", "folk", "heading" } (game coordinates; `r` how far they roam, `n`
 * how many live there). The villagers are solid (circles, like the long-neck): a kart
 * bumps them, and they never trap one (they step away).
 */
import type * as THREE from "three";
import type { Solid, SolidCircle } from "../world/solids";
import {
  createVillagerView,
  SIZE,
  villagerLook,
  type Folk,
  type VillagerView,
} from "../render/villager";

export interface Home {
  x: number;
  z: number;
  y: number;
  r: number;
  n: number;
  folk: Folk;
  heading: number;
}

const FOLKS: Folk[] = ["valley", "snow", "desert", "beach", "dragon", "road"];

/** How far above a villager the ground is looked for: a roof over a spot (a house) is
 * found first, and isn't ground it can stand on, so it never walks into a house. */
const LOOK_UP = 8;

const num = (v: unknown, d: number) => (typeof v === "number" && Number.isFinite(v) ? v : d);

/** The homes among a package's entities. */
export function parseHomes(entities: unknown[]): Home[] {
  const out: Home[] = [];
  for (const e of entities) {
    if (!e || typeof e !== "object") continue;
    const o = e as Record<string, unknown>;
    if (o.type !== "villager_home") continue;
    const folk = FOLKS.includes(o.folk as Folk) ? (o.folk as Folk) : "valley";
    out.push({
      x: num(o.x, 0),
      z: num(o.z, 0),
      y: num(o.y, 0),
      r: Math.max(4, num(o.r, 14)),
      n: Math.max(1, Math.min(6, Math.round(num(o.n, 2)))),
      folk,
      heading: num(o.heading, 0),
    });
  }
  return out;
}

// ---------------------------------------------------------------- names and lines

const SYLL: Record<Folk, [string[], string[]]> = {
  valley: [
    ["Mo", "Fern", "Bram", "Ola", "Tuk", "Wil", "Pip", "Rue", "Kel", "Ash"],
    ["ble", "wick", "do", "mo", "ry", "ba", "tle", "nut", "pod", "sy"],
  ],
  snow: [
    ["Bo", "Fro", "Hild", "Nils", "Ing", "Sno", "Tove", "Kari", "Pel", "Yul"],
    ["rin", "sty", "da", "mer", "ka", "by", "gar", "ra", "vik", "ni"],
  ],
  desert: [
    ["Sa", "Dus", "Ra", "Mes", "Ca", "Del", "Zan", "Ory", "Pas", "Tum"],
    ["ty", "ko", "bel", "quite", "lo", "ra", "zo", "na", "ble", "do"],
  ],
  beach: [
    ["Ko", "Lu", "Ma", "Pua", "Ke", "Nalu", "Wai", "Sun", "Shel", "Rip"],
    ["na", "li", "ko", "lani", "pa", "ny", "ley", "ra", "mo", "py"],
  ],
  dragon: [
    ["Al", "Ber", "Cor", "Ed", "Gwen", "Os", "Ro", "Tam", "Wyn", "Eli"],
    ["ric", "tram", "win", "da", "mund", "ith", "na", "sel", "lin", "o"],
  ],
  road: [
    ["Way", "Rov", "Tra", "Pil", "Wan", "Jour", "Pack", "Hob", "Trek", "Mil"],
    ["fa", "er", "vel", "grim", "do", "ney", "ley", "bo", "ka", "ly"],
  ],
};

/** Placeholder lines (Blake: the dialogue comes later), a few for each kingdom. */
const LINES: Record<Folk, string[]> = {
  valley: [
    "THE RIVER'S HIGH THIS SEASON. MIND THE FORD!",
    "MY GRANDMOTHER SAYS THE VOLCANO USED TO SING.",
    "HAVE YOU SEEN ELDER MOSSBACK? HE WAS LOOKING FOR YOU.",
    "THE FERNS GROW TALLER EVERY YEAR, I SWEAR IT.",
  ],
  snow: [
    "BRR! KEEP YOUR ENGINE WARM UP HERE.",
    "THE BELLS RING ON THEIR OWN WHEN THE WIND IS RIGHT.",
    "HOT SOUP AT HEARTHGLOW, IF YOU'RE PASSING.",
    "DON'T LINGER ON THE LAKE ICE. IT TALKS.",
  ],
  desert: [
    "WATER'S WORTH MORE THAN GOLD OUT HERE.",
    "STEGO'S GOT EVERYTHING AT THE POST. EVERYTHING.",
    "THE DUNES MOVE AT NIGHT. NOBODY BELIEVES ME.",
    "I SAW A GHOST RIDER ON THE RIDGE LAST NIGHT.",
  ],
  beach: [
    "SURF'S UP! WELL, IT'S ALWAYS UP.",
    "THE VOLCANO GRUMBLES WHEN IT'S HUNGRY.",
    "RAPTOR'S THE FASTEST ON THE ISLANDS. SO HE SAYS.",
    "FOUND A PIRATE COIN IN THE SAND THIS MORNING!",
  ],
  dragon: [
    "THE KING'S CITADEL WATCHES OVER US ALL.",
    "THE LANTERNS ARE LIT FOR THE MOON FESTIVAL.",
    "MIND THE STORM OVER EMBERDEEP. IT NEVER LEAVES.",
    "A RACER FROM THE ISLANDS? WELCOME, WELCOME.",
  ],
  road: [
    "LONG ROAD, ISN'T IT? THE VIEW'S WORTH IT.",
    "I'M WALKING TO THE NEXT KINGDOM. YOU'RE QUICKER.",
    "KEEP TO THE ROAD. THE ROCKS DON'T MOVE FOR KARTS.",
    "I TRADE BETWEEN THE KINGDOMS. BUSY TIMES.",
  ],
};

/** A small, repeatable random sequence (so a home's villagers are the same each visit). */
function rng(seed: number) {
  let s = seed >>> 0 || 1;
  return () => {
    s ^= s << 13;
    s ^= s >>> 17;
    s ^= s << 5;
    return ((s >>> 0) % 100000) / 100000;
  };
}

export function villagerName(folk: Folk, seed: number) {
  const [a, b] = SYLL[folk];
  return a[seed % a.length]! + b[Math.floor(seed / a.length) % b.length]!;
}

// ---------------------------------------------------------------- walking about

interface Villager {
  home: Home;
  x: number;
  z: number;
  y: number;
  heading: number;
  speed: number;
  /** Where it's walking to, or waiting (until `wait` runs out). */
  tx: number;
  tz: number;
  wait: number;
  walk: number;
  name: string;
  line: string;
  radius: number;
  solid: SolidCircle;
  view?: VillagerView;
  rand: () => number;
}

export interface Villagers {
  /** Once a frame: walk about; `you` is your kart. */
  step(dt: number, t: number, you: { x: number; z: number; speed: number }): void;
  /** The villager you've stopped by (its name and line), if any. */
  near(): { name: string; line: string } | undefined;
  readonly count: number;
  /** Where they are (tests). */
  readonly spots: { x: number; z: number; y: number }[];
  dispose(): void;
}

export function createVillagers(opts: {
  root?: THREE.Object3D;
  homes: Home[];
  solids: Solid[];
  /** The ground's height at (x, z), and whether a villager may stand there (not water,
   * lava or a wall). */
  ground: (x: number, z: number, y: number) => { height: number; ok: boolean };
}): Villagers {
  const folk: Villager[] = [];
  opts.homes.forEach((h0, hi) => {
    // The yard: the home's spot, or (if that's under a roof: a big house) the nearest
    // open ground round it.
    let h = h0;
    if (!opts.ground(h0.x, h0.z, h0.y + LOOK_UP).ok)
      search: for (let r = 3; r <= 15; r += 3)
        for (let k = 0; k < 8; k++) {
          const a = (k / 8) * Math.PI * 2;
          const x = h0.x + Math.sin(a) * r;
          const z = h0.z + Math.cos(a) * r;
          const g = opts.ground(x, z, h0.y + LOOK_UP);
          if (g.ok && Math.abs(g.height - h0.y) < 2) {
            h = { ...h0, x, z, y: g.height };
            break search;
          }
        }
    for (let k = 0; k < h.n; k++) {
      const seed = Math.abs(Math.round(h.x * 7 + h.z * 13)) + k * 31 + hi * 101;
      const rand = rng(seed + 17);
      const look = villagerLook(h.folk, seed);
      const size = SIZE[look.species];
      const a = rand() * Math.PI * 2;
      const r = 3 + rand() * Math.min(6, h.r * 0.5);
      const x = h.x + Math.sin(a) * r;
      const z = h.z + Math.cos(a) * r;
      const g = opts.ground(x, z, h.y + LOOK_UP);
      const y = g.ok ? g.height : h.y;
      const solid: SolidCircle = {
        kind: "circle",
        look: "creature",
        x,
        z,
        radius: size.radius,
        height: y + 2.5,
      };
      opts.solids.push(solid);
      folk.push({
        home: h,
        x: g.ok ? x : h.x,
        z: g.ok ? z : h.z,
        y,
        heading: rand() * Math.PI * 2,
        speed: size.speed * (0.85 + rand() * 0.3),
        tx: x,
        tz: z,
        wait: rand() * 3,
        walk: 0,
        name: villagerName(h.folk, seed),
        line: LINES[h.folk][seed % LINES[h.folk].length]!,
        radius: size.radius,
        solid,
        view: opts.root ? createVillagerView(opts.root, h.folk, seed) : undefined,
        rand,
      });
    }
  });
  let nearest: Villager | undefined;

  const pick = (v: Villager) => {
    for (let i = 0; i < 6; i++) {
      const a = v.rand() * Math.PI * 2;
      const r = 2 + v.rand() * v.home.r;
      const x = v.home.x + Math.sin(a) * r;
      const z = v.home.z + Math.cos(a) * r;
      const g = opts.ground(x, z, v.y + LOOK_UP);
      if (g.ok && Math.abs(g.height - v.home.y) < 4 && Math.abs(g.height - v.y) < 3) {
        v.tx = x;
        v.tz = z;
        return;
      }
    }
    v.wait = 2;
  };

  return {
    get count() {
      return folk.length;
    },
    get spots() {
      return folk.map((v) => ({ x: v.x, z: v.z, y: v.y }));
    },
    step(dt, t, you) {
      nearest = undefined;
      let best = 6;
      for (const v of folk) {
        const dx = you.x - v.x;
        const dz = you.z - v.z;
        const dyou = Math.hypot(dx, dz);
        let want = 0;
        if (dyou < 7 && Math.abs(you.speed) > 4) {
          // A kart coming: out of its way.
          v.tx = v.x - (dx / (dyou || 1)) * 5;
          v.tz = v.z - (dz / (dyou || 1)) * 5;
          v.wait = 0;
          want = 1.6;
        } else if (dyou < 6 && Math.abs(you.speed) < 2) {
          // You've stopped by: it stops and looks at you.
          const face = Math.atan2(dx, dz);
          v.heading += wrap(face - v.heading) * Math.min(1, dt * 4);
          v.wait = Math.max(v.wait, 1);
          if (dyou < best) {
            best = dyou;
            nearest = v;
          }
        } else if (v.wait > 0) {
          v.wait -= dt;
          if (v.wait <= 0) pick(v);
        } else {
          want = 1;
        }
        if (want > 0) {
          const ex = v.tx - v.x;
          const ez = v.tz - v.z;
          const d = Math.hypot(ex, ez);
          if (d < 0.6) {
            v.wait = 1.5 + v.rand() * 5;
            want = 0;
          } else {
            const face = Math.atan2(ex, ez);
            v.heading += wrap(face - v.heading) * Math.min(1, dt * 3);
            const sp = v.speed * want * Math.max(0.2, Math.cos(wrap(face - v.heading)));
            const nx = v.x + Math.sin(v.heading) * sp * dt;
            const nz = v.z + Math.cos(v.heading) * sp * dt;
            const g = opts.ground(nx, nz, v.y + LOOK_UP);
            if (g.ok && Math.abs(g.height - v.y) < 0.6) {
              v.x = nx;
              v.z = nz;
              v.y += (g.height - v.y) * Math.min(1, dt * 10);
            } else {
              // A drop, a wall or water ahead: somewhere else.
              v.wait = 0.5;
              want = 0;
            }
          }
        }
        v.walk += ((want > 0 ? want : 0) - v.walk) * Math.min(1, dt * 6);
        v.solid.x = v.x;
        v.solid.z = v.z;
        v.solid.height = v.y + 2.5;
        v.view?.update(v.x, v.y, v.z, v.heading, v.walk, t);
      }
    },
    near() {
      return nearest ? { name: nearest.name.toUpperCase(), line: nearest.line } : undefined;
    },
    dispose() {
      for (const v of folk) {
        v.view?.dispose();
        const i = opts.solids.indexOf(v.solid);
        if (i >= 0) opts.solids.splice(i, 1);
      }
    },
  };
}

function wrap(a: number) {
  return Math.atan2(Math.sin(a), Math.cos(a));
}
