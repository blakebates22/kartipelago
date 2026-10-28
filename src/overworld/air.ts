/**
 * The overworld's air (Blake, Oct 28: "I know Riverbend is more bright than Bonebog, and
 * I want to capture that contrast in the overworlds"; "check the lighting and sky we used
 * for the actual levels"): each area of a region takes the look of the course whose
 * gateway is in it, its own look.json (sky, sky dome, sun, ambient light, fog), and the
 * square the region's own; driving between them, the two nearest blend.
 *
 * Pure: the blend from where you are, and a look mixed from two (screens/overworld.ts
 * puts it on the stage).
 */
import type { TrackLook } from "../world/trackPackage";

/** An area: where its look holds (a gateway, the square), and the look. */
export interface AirSpot {
  x: number;
  z: number;
  look: TrackLook;
}

/** How far apart (metres) the two nearest areas' distances have to be before the nearer
 * one's look holds alone; equally far, it's half and half. */
export const BLEND_WIDTH = 140;

/** The two nearest areas and how much of the second shows (0..0.5). */
export function airAt(
  spots: readonly AirSpot[],
  x: number,
  z: number,
  width = BLEND_WIDTH,
): { a: number; b: number; t: number } {
  let a = -1;
  let b = -1;
  let da = Infinity;
  let db = Infinity;
  spots.forEach((s, i) => {
    const d = Math.hypot(s.x - x, s.z - z);
    if (d < da) {
      b = a;
      db = da;
      a = i;
      da = d;
    } else if (d < db) {
      b = i;
      db = d;
    }
  });
  if (b < 0) return { a: Math.max(0, a), b: Math.max(0, a), t: 0 };
  const k = Math.max(0, Math.min(1, 1 - (db - da) / width));
  // (Smooth at both ends.)
  return { a, b, t: 0.5 * k * k * (3 - 2 * k) };
}

export type RGB = [number, number, number];
export const hex = (h: string): RGB => {
  const m = /^#?([0-9a-f]{6})$/i.exec(h.trim());
  if (!m) return [1, 1, 1];
  const n = parseInt(m[1]!, 16);
  return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
};
const mix = (a: number, b: number, t: number) => a + (b - a) * t;
const mixRGB = (a: RGB, b: RGB, t: number): RGB => [
  mix(a[0], b[0], t),
  mix(a[1], b[1], t),
  mix(a[2], b[2], t),
];

/** A look's air, every part filled (missing parts from `base`, the region's own). */
export interface Air {
  sky: RGB;
  fog: { color: RGB; near: number; far: number; enabled: boolean };
  sun: { color: RGB; intensity: number; direction: [number, number, number] };
  ambient: { sky: RGB; ground: RGB; intensity: number };
}

const DEFAULT: Air = {
  sky: hex("#8fd3ff"),
  fog: { color: hex("#c4e7fa"), near: 150, far: 680, enabled: true },
  sun: { color: hex("#fff0d2"), intensity: 2.3, direction: [0.55, 0.75, 0.35] },
  ambient: { sky: hex("#e2f4ff"), ground: hex("#5d7a3a"), intensity: 1.15 },
};

export function airOf(look: TrackLook, base: Air = DEFAULT): Air {
  return {
    sky: look.sky ? hex(look.sky) : base.sky,
    fog: look.fog
      ? {
          color: hex(look.fog.color),
          near: look.fog.near,
          far: look.fog.far,
          enabled: look.fog.enabled,
        }
      : base.fog,
    sun: look.sun
      ? { color: hex(look.sun.color), intensity: look.sun.intensity, direction: look.sun.direction }
      : base.sun,
    ambient: look.ambient
      ? {
          sky: hex(look.ambient.sky),
          ground: hex(look.ambient.ground),
          intensity: look.ambient.intensity,
        }
      : base.ambient,
  };
}

/** Two airs mixed (`t` of the second). */
export function mixAir(a: Air, b: Air, t: number): Air {
  const d = a.sun.direction;
  const e = b.sun.direction;
  return {
    sky: mixRGB(a.sky, b.sky, t),
    fog: {
      color: mixRGB(a.fog.color, b.fog.color, t),
      near: mix(a.fog.near, b.fog.near, t),
      far: mix(a.fog.far, b.fog.far, t),
      enabled: a.fog.enabled || b.fog.enabled,
    },
    sun: {
      color: mixRGB(a.sun.color, b.sun.color, t),
      intensity: mix(a.sun.intensity, b.sun.intensity, t),
      direction: [mix(d[0], e[0], t), mix(d[1], e[1], t), mix(d[2], e[2], t)],
    },
    ambient: {
      sky: mixRGB(a.ambient.sky, b.ambient.sky, t),
      ground: mixRGB(a.ambient.ground, b.ambient.ground, t),
      intensity: mix(a.ambient.intensity, b.ambient.intensity, t),
    },
  };
}
