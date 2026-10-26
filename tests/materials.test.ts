import { existsSync, readFileSync } from "node:fs";
import { readFile } from "node:fs/promises";
import * as THREE from "three";
import { describe, expect, it } from "vitest";
import surfacesFile from "../assets/data/surfaces.json";
import {
  filterFor,
  fxOffset,
  pulseAt,
  parseFx,
  prepareTrackMaterials,
} from "../src/render/trackMaterials";
import { createMeshGround } from "../src/world/collisionMesh";
import {
  loadTrackPackage,
  parseLook,
  type PackageReader,
  type TrackPackage,
} from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const ADDON = new URL("../tools/blender/addons/kartipelago_tools/", import.meta.url);
const library = JSON.parse(readFileSync(new URL("library/materials.json", ADDON), "utf8")) as {
  themes: { id: string; environment: unknown }[];
  materials: { id: string; theme: string; surface: string; image: string; tileMetres: number }[];
};
const surfaceIds = Object.keys(surfacesFile.surfaces);

const DEMO = new URL("../public/tracks/dino_demo/", import.meta.url);
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(file, DEMO));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};
let cached: TrackPackage | undefined;
const demo = async () => (cached ??= await loadTrackPackage(reader, { visual: false }));

/** The JSON chunk of a GLB file. */
function glbJson(file: URL) {
  const b = readFileSync(file);
  const len = new DataView(b.buffer, b.byteOffset).getUint32(12, true);
  return JSON.parse(new TextDecoder().decode(b.subarray(20, 20 + len))) as {
    materials: {
      name: string;
      extras?: Record<string, unknown>;
      pbrMetallicRoughness?: { baseColorTexture?: { index: number } };
    }[];
    textures: { source: number }[];
    meshes: { primitives: { attributes: Record<string, number> }[] }[];
  };
}

/** Width and height from a PNG header. */
function pngSize(file: URL) {
  const b = readFileSync(file);
  const v = new DataView(b.buffer, b.byteOffset);
  return [v.getUint32(16), v.getUint32(20)];
}

describe("material library (Blender add-on)", () => {
  it("keeps the four starter themes and their sixteen materials first", () => {
    const starter = ["mirror_lake", "bone_canyon", "jungle_cascade", "ember_volcano"];
    expect(library.themes.slice(0, 4).map((t) => t.id)).toEqual(starter);
    expect(library.materials.slice(0, 16).every((m) => starter.includes(m.theme))).toBe(true);
    for (const t of starter)
      expect(library.materials.slice(0, 16).filter((m) => m.theme === t)).toHaveLength(4);
  });

  it("adds the Dinosaur Valley textures, each in a known theme with unique ids", () => {
    const ids = library.materials.map((m) => m.id);
    expect(new Set(ids).size).toBe(ids.length);
    for (const id of [
      "valley_road",
      "wood_planks",
      "palm_frond",
      "waterfall",
      "swamp_mud",
      "bone",
      "volcano_crust",
    ])
      expect(ids).toContain(id);
    const themes = library.themes.map((t) => t.id);
    for (const m of library.materials) expect(themes, m.id).toContain(m.theme);
  });

  it("suggests only surfaces the game knows", () => {
    for (const m of library.materials) expect(surfaceIds, m.id).toContain(m.surface);
    // ...and so does the add-on's surface menu.
    const roadPy = readFileSync(new URL("road.py", ADDON), "utf8");
    const menu = [...roadPy.matchAll(/^\s+\("([a-z]+)", "[^"]+", "[^"]+"\),$/gm)].map((x) => x[1]);
    expect(menu.length).toBeGreaterThan(8);
    for (const id of menu) expect(surfaceIds).toContain(id);
  });

  it("keeps textures small, like the era (64 px or less), with a thumbnail each", () => {
    for (const m of library.materials) {
      const [w, h] = pngSize(new URL(`library/textures/${m.image}`, ADDON));
      expect(w, m.id).toBeLessThanOrEqual(64);
      expect(h, m.id).toBeLessThanOrEqual(64);
      expect(existsSync(new URL(`library/thumbs/${m.image}`, ADDON)), m.id).toBe(true);
      expect(m.tileMetres).toBeGreaterThan(0);
    }
  });

  it("gives every theme an environment the game accepts", () => {
    for (const t of library.themes) {
      const warnings: string[] = [];
      const look = parseLook({ schemaVersion: 1, ...(t.environment as object) }, warnings);
      expect(warnings, t.id).toEqual([]);
      expect(look.sky && look.fog && look.sun && look.ambient, t.id).toBeTruthy();
    }
  });
});

describe("water and lava animation", () => {
  it("reads kp_fx and ignores still or broken ones", () => {
    expect(parseFx(undefined)).toBeUndefined();
    expect(parseFx({ kp_fx: { scroll_u: 0, scroll_v: 0, wave: 0 } })).toBeUndefined();
    expect(parseFx({ kp_fx: "fast" })).toBeUndefined();
    const fx = parseFx({ kp_fx: { scroll_u: 0.03, scroll_v: "x", wave: 9, wave_period: -1 } })!;
    expect(fx.scrollU).toBe(0.03);
    expect(fx.scrollV).toBe(0);
    expect(fx.wave).toBe(1); // clamped
    expect(fx.wavePeriod).toBeGreaterThan(0);
  });

  it("reads living water and swaying, which count as animated on their own", () => {
    const fx = parseFx({ kp_fx: { lagoon: 1, sway: 0.3 } })!;
    expect(fx.lagoon).toBe(1);
    expect(fx.sway).toBeCloseTo(0.3);
    expect(parseFx({ kp_fx: { sway: 0.2 } })?.sway).toBeCloseTo(0.2);
    expect(parseFx({ kp_fx: { lagoon: 99 } })?.lagoon).toBe(4); // clamped
  });

  it("reads a flickering glow (lanterns, lit windows), animated on its own", () => {
    expect(parseFx({ kp_fx: { flicker: 0.4 } })?.flicker).toBeCloseTo(0.4);
    expect(parseFx({ kp_fx: { flicker: 7 } })?.flicker).toBe(1); // clamped
    expect(parseFx({ kp_fx: { flicker: 0 } })).toBeUndefined();
  });

  it("scrolls steadily and ripples in a loop", () => {
    const fx = {
      scrollU: 0.25,
      scrollV: 0,
      wave: 0,
      wavePeriod: 4,
      pulse: 0,
      pulsePeriod: 4,
      lagoon: 0,
      sway: 0,
      flicker: 0,
    };
    expect(fxOffset(fx, 1)[0]).toBeCloseTo(0.25);
    expect(fxOffset(fx, 5)[0]).toBeCloseTo(0.25); // wraps every 4 s
    const ripple = {
      scrollU: 0,
      scrollV: 0,
      wave: 0.1,
      wavePeriod: 2,
      pulse: 0,
      pulsePeriod: 4,
      lagoon: 0,
      sway: 0,
      flicker: 0,
    };
    const a = fxOffset(ripple, 0.3);
    const b = fxOffset(ripple, 2.3);
    // Same place one period later (offsets wrap at 1).
    for (const k of [0, 1]) {
      const d = Math.abs(a[k]! - b[k]!);
      expect(Math.min(d, 1 - d)).toBeLessThan(1e-9);
    }
  });
});

describe("pulsing glow", () => {
  it("reads a pulse, and swells and fades round its own glow", () => {
    const fx = parseFx({
      kp_fx: { scroll_u: 0, scroll_v: 0, wave: 0, pulse: 0.4, pulse_period: 4 },
    })!;
    expect(fx.pulse).toBeCloseTo(0.4);
    expect(pulseAt(fx, 1)).toBeCloseTo(1);
    expect(pulseAt(fx, 3)).toBeCloseTo(0.6);
    expect(pulseAt({ ...fx, pulse: 0 }, 3)).toBe(1);
  });
});

describe("track materials in the game", () => {
  const source = () => {
    const tex = new THREE.DataTexture(new Uint8Array(64 * 32 * 4), 64, 32);
    const water = new THREE.MeshStandardMaterial({ map: tex, transparent: true, opacity: 0.8 });
    water.userData = { kp_surface: "water", kp_fx: { scroll_u: 0.1, wave: 0.02 } };
    const lava = new THREE.MeshStandardMaterial({
      map: tex,
      emissive: new THREE.Color(0.8, 0.8, 0.8),
      emissiveMap: tex,
    });
    const grass = new THREE.MeshStandardMaterial({ map: tex, vertexColors: true });
    grass.color.setRGB(1, 0.5, 0.5); // a tint
    const root = new THREE.Group();
    const geo = new THREE.PlaneGeometry();
    root.add(new THREE.Mesh(geo, water), new THREE.Mesh(geo, lava), new THREE.Mesh(geo, grass));
    root.add(new THREE.Mesh(geo, grass)); // shared material
    return { root, tex };
  };

  it("draws them as plain diffuse materials, keeping texture, paint, tint, glow and opacity", () => {
    const { root, tex } = source();
    prepareTrackMaterials(root, "authentic");
    const [w, l, g, g2] = root.children.map(
      (c) => (c as THREE.Mesh).material as THREE.MeshLambertMaterial,
    );
    for (const m of [w, l, g]) expect(m!.type).toBe("MeshLambertMaterial");
    expect(g).toBe(g2); // still shared
    expect(g!.vertexColors).toBe(true);
    expect(g!.color.g).toBeCloseTo(0.5);
    expect(w!.transparent && w!.opacity).toBeCloseTo(0.8);
    expect(w!.depthWrite).toBe(false);
    expect(l!.emissive.r).toBeCloseTo(0.8);
    expect(l!.emissiveMap).toBe(tex);
    expect(w!.userData.kp_surface).toBe("water");
    // The water moves on its own copy of the image; the others stay still.
    expect(w!.map).not.toBe(tex);
    expect(g!.map).toBe(tex);
    expect((root.children[0] as THREE.Mesh).castShadow).toBe(false);
  });

  it("animates only the moving textures", () => {
    const { root, tex } = source();
    const tm = prepareTrackMaterials(root, "authentic");
    expect(tm.animated).toHaveLength(1);
    tm.update(2);
    expect(tm.animated[0]!.texture.offset.x).not.toBe(0);
    expect(tex.offset.x).toBe(0);
  });

  it("switches between the authentic and enhanced looks", () => {
    const { root } = source();
    const tm = prepareTrackMaterials(root, "authentic");
    for (const t of tm.textures) expect(t.magFilter).toBe(filterFor("authentic").magFilter);
    tm.setMode("enhanced");
    for (const t of tm.textures) {
      expect(t.magFilter).toBe(THREE.NearestFilter);
      expect(t.anisotropy).toBe(8);
    }
    expect(filterFor("authentic").magFilter).toBe(THREE.LinearFilter);
  });

  it("checks look.json, falling back for bad parts", () => {
    const w: string[] = [];
    const look = parseLook(
      {
        sky: "#8fd3ff",
        fog: { enabled: true, color: "blue", near: 1, far: 2 },
        sun: { color: "#ffffff", intensity: 2, direction: [0, -1, 0] },
      },
      w,
    );
    expect(look.sky).toBe("#8fd3ff");
    expect(look.fog).toBeUndefined();
    expect(look.sun).toBeUndefined(); // a sun below the horizon
    expect(w).toHaveLength(2);
    expect(parseLook(null, [])).toEqual({});
  });
});

describe("Dino Demo (exported from Blender)", () => {
  it("loads with its environment, surfaces and no warnings", async () => {
    const p = await demo();
    expect(p.warnings).toEqual([]);
    expect(p.look.theme).toBe("mirror_lake");
    expect(p.look.fog?.enabled).toBe(true);
    expect(new Set(p.collision.surfaces)).toEqual(
      new Set(["road", "dirt", "grass", "wall", "water", "sand"]),
    );
  });

  it("keeps the picture and the driving surface separate", () => {
    const j = glbJson(new URL("visual.glb", DEMO));
    const image = (name: string) => {
      const m = j.materials.find((x) => x.name === name)!;
      return j.textures[m.pbrMetallicRoughness!.baseColorTexture!.index]!.source;
    };
    const surface = (name: string) => j.materials.find((x) => x.name === name)!.extras!.kp_surface;
    // One image, three surfaces: the road, the tunnel floor beside it, the lake bed.
    expect(image("KP Ancient Road [dirt]")).toBe(image("KP Ancient Road"));
    expect(image("KP Ancient Road [sand]")).toBe(image("KP Ancient Road"));
    expect(surface("KP Ancient Road")).toBe("road");
    expect(surface("KP Ancient Road [dirt]")).toBe("dirt");
    expect(surface("KP Ancient Road [sand]")).toBe("sand");
    // Water carries its animation; everything painted carries vertex colours.
    const water = j.materials.find((x) => x.name === "KP Ancient Water")!;
    expect(parseFx(water.extras)).toBeDefined();
    const painted = j.meshes.flatMap((m) => m.primitives).filter((p) => "COLOR_0" in p.attributes);
    expect(painted.length).toBeGreaterThan(5);
  });

  it("puts water on the lake and road under the tunnel roof", async () => {
    const p = await demo();
    const ground = createMeshGround(p.collision);
    expect(ground.at(-26, 150, 0).surface).toBe("water"); // game z = -Blender y
    // Inside the mesa: the road, with rock overhead that isn't mistaken for the floor.
    const inside = p.trackData.points.filter((q) => Math.hypot(q.x - 126, q.z + 26) < 12);
    expect(inside.length).toBeGreaterThan(5);
    for (const q of inside) {
      const g = ground.at(q.x, q.z, (q.y ?? 0) + 0.3);
      expect(g.surface).toBe("road");
      expect(g.height).toBeCloseTo(q.y ?? 0, 0);
    }
  });

  it("drives a full AI lap, through the tunnel, with the existing physics (A, E)", async () => {
    const r = await aiLap(await demo());
    const racer = r.race.racers[0]!;
    expect(racer.lapTimes).toHaveLength(1);
    expect(racer.passed).toBe(r.race.gates.length);
    expect(r.lowest).toBeGreaterThan(r.killY);
    expect(r.worstAbove).toBeLessThan(1.5);
    expect(r.walls).toBeLessThan(60);
  }, 30000);
});

describe("surfaces", () => {
  it("has a full-grip road surface and lava that sends you back", () => {
    const s = surfacesFile.surfaces as Record<
      string,
      { road?: boolean; respawn?: boolean; grip?: number }
    >;
    expect(s.road).toMatchObject({ road: true, grip: 1 });
    expect(s.lava?.respawn).toBe(true);
  });
});
