/**
 * The sleek kart family: low, long and pointed, built to look fast.
 *
 * Every sleek kart shares one shape language on the shared chassis (the wheels, seat,
 * steering wheel and exhaust never move): a low wedge monocoque that tapers to a nose
 * close to the road, open wheels under thin blade fenders, sidepods with intakes
 * between the wheels, a low engine deck behind the seat, and a wing or fins at the back.
 * Each racer picks a nose, sidepods and tail, and their colours, so the four still read
 * as four different machines from the race camera.
 *
 * Local frame: +Z forward, +Y up, origin on the ground under the kart's centre.
 */
import * as THREE from "three";
import { CHASSIS, type BodyKit } from "./chassis";
import { Build, box, card, cyl, ellipsoid, loft, type ColorLike, type Section } from "./shapes";
import { emblemMesh, type Emblem } from "./props";

export interface SleekStyle {
  /** Body colour, its shade below, and the racing stripe down the middle. */
  main: string;
  dark: string;
  stripe: string;
  /** The nose cone's colour (often a contrast). */
  nose: string;
  /** Wing, fender and pod trim. */
  trim: string;
  /** Exhausts, struts and bits of machinery. */
  metal: string;
  seat: string;
  glass: string;
  tyre: string;
  rim: string;
  cap: string;
  /** A thin line round the slicks' sidewalls. */
  tyreLine: string;
  /** How broad the body is (1 standard, a little more for the bruiser). */
  width?: number;
  /** The front: a wide blade wing, twin low winglets, two horn-like splitters, or a needle. */
  front: "blade" | "twin" | "horns" | "needle";
  /** The sidepods: intakes, swept delta wings, or round bubbles. */
  pods: "intake" | "delta" | "round";
  /** The back: a raised wing on struts, a kicked-up ducktail, twin fins, or a jet tail. */
  rear: "wing" | "ducktail" | "fins" | "jet";
  emblem: { kind: Emblem; disc: string; ink: string; rim: string };
  /** Spokes on the rims. */
  spokes?: number;
  /** Anything else on top (detail 0 near, 1 far). */
  extras?(b: Build, detail: 0 | 1): void;
}

/** An airfoil running across the kart (X), centred at `at`, chord along Z. */
export function airfoil(
  span: number,
  chord: number,
  thick: number,
  color: ColorLike,
  sweep = 0,
  tip = 1,
) {
  const sec = (x: number, k: number): Section => ({
    at: [x, 0, -Math.abs(x) * sweep],
    rx: (chord / 2) * k,
    ry: (thick / 2) * k,
    color,
    sq: 3,
  });
  return loft(
    [sec(-span / 2, tip), sec(-span / 4, 1), sec(0, 1), sec(span / 4, 1), sec(span / 2, tip)],
    {
      sides: 8,
      capStart: true,
      capEnd: true,
    },
  );
}

/**
 * A thin blade fender curving over a wheel: an arc round the axle (at x, centred on the
 * wheel) from angle `a0` to `a1` (0 = straight up, >0 forward).
 */
export function bladeFender(
  r: number,
  width: number,
  thick: number,
  a0: number,
  a1: number,
  color: ColorLike,
) {
  const n = 7;
  const secs: Section[] = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n;
    const a = a0 + (a1 - a0) * t;
    // Thinner at the ends, like a pressed-metal wing.
    const k = 0.35 + 0.65 * Math.sin(Math.PI * t);
    secs.push({
      at: [0, Math.cos(a) * r, Math.sin(a) * r],
      rx: (width / 2) * (0.75 + 0.25 * k),
      ry: thick * k,
      color,
      sq: 3.2,
    });
  }
  return loft(secs, { sides: 8, capStart: true, capEnd: true, up: [0, 0, 1] });
}

export function sleekKart(s: SleekStyle): BodyKit {
  const W = s.width ?? 1;
  const [fw, , rw] = [CHASSIS.wheels[0]!, CHASSIS.wheels[1]!, CHASSIS.wheels[2]!];
  return {
    smooth: true,
    wheel: {
      tyre: s.tyre,
      rim: s.rim,
      cap: s.cap,
      sides: 18,
      slick: { stripe: s.tyreLine, spokes: s.spokes ?? 5 },
    },
    steering: "#2a2629",
    shell(b, detail) {
      const nose = new THREE.Color(s.nose);
      const main = new THREE.Color(s.main);
      // The undertray: a thin dark plank close to the road.
      b.add(box(0.96 * W, 0.08, 2.3, 0.03), "#2a2629", { p: [0, 0.24, -0.02] });
      // The monocoque: low at the back, a hump round the cockpit, then a long wedge down
      // to the nose. A stripe down the spine, the colour going to the nose's at the front.
      const needle = s.front === "needle";
      const tipZ = needle ? 1.42 : 1.36;
      const secs: Section[] = [
        { at: [0, 0.42, -1.2], rx: 0.28 * W, ry: 0.12, sq: 2.6, flat: 0.6 },
        { at: [0, 0.46, -0.95], rx: 0.4 * W, ry: 0.17, sq: 2.6, flat: 0.6 },
        { at: [0, 0.48, -0.45], rx: 0.48 * W, ry: 0.2, sq: 2.6, flat: 0.6 },
        { at: [0, 0.5, 0.05], rx: 0.46 * W, ry: 0.21, sq: 2.6, flat: 0.6 },
        { at: [0, 0.47, 0.5], rx: 0.34 * W, ry: 0.17, sq: 2.5, flat: 0.6 },
        { at: [0, 0.4, 0.92], rx: 0.22 * W, ry: 0.11, sq: 2.4, flat: 0.5 },
        { at: [0, 0.32, 1.22], rx: needle ? 0.09 : 0.13 * W, ry: 0.07, sq: 2.2, flat: 0.4 },
        { at: [0, 0.28, tipZ], rx: 0.03, ry: 0.025, sq: 2 },
      ];
      b.addColored(
        loft(secs, {
          sides: 16,
          steps: 3,
          capStart: true,
          capEnd: true,
          paint: (t, a) => {
            const z = -1.2 + t * (tipZ + 1.2);
            const top = Math.abs(a - Math.PI / 2);
            const base = z > 0.72 ? nose : main;
            if (top < 0.22 && z > -1.0) return s.stripe;
            if (top < 0.34 && z > -1.0) return s.trim;
            if (a < -0.25) return s.dark;
            return base;
          },
        }),
      );
      // The cockpit: a raised cowl round the steering wheel, a tinted screen, a rim
      // round the seat and the seat itself.
      b.addColored(
        loft(
          [
            { at: [0, 0.6, -0.02], rx: 0.3, ry: 0.06, color: s.main },
            { at: [0, 0.66, 0.24], rx: 0.27, ry: 0.1, color: s.main },
            { at: [0, 0.62, 0.48], rx: 0.2, ry: 0.07, color: s.main },
            { at: [0, 0.55, 0.66], rx: 0.1, ry: 0.03, color: s.main },
          ],
          { sides: 12, steps: 2, capStart: true, capEnd: true },
        ),
      );
      b.add(
        card(
          [
            [-0.2, 0],
            [0.2, 0],
            [0.15, 0.13],
            [-0.15, 0.13],
          ],
          0.015,
        ),
        s.glass,
        {
          p: [0, 0.72, 0.42],
          r: [-0.95, 0, 0],
        },
      );
      b.add(new THREE.TorusGeometry(0.32, 0.04, 5, 16), s.trim, {
        p: [0, 0.64, -0.3],
        r: [Math.PI / 2, 0, 0],
        s: [0.95, 1.25, 1],
      });
      b.add(box(0.46, 0.08, 0.4, 0.03), s.seat, { p: [0, 0.5, -0.3] });
      b.add(box(0.44, 0.24, 0.08, 0.03), s.seat, { p: [0, 0.64, -0.54], r: [-0.25, 0, 0] });

      // The engine deck behind the seat, low enough for tails to rest on, and the
      // exhaust (the boost flame comes out of it).
      b.addColored(
        loft(
          [
            { at: [0, 0.6, -0.62], rx: 0.26, ry: 0.06, color: s.main },
            { at: [0, 0.62, -0.85], rx: 0.24, ry: 0.08, color: s.main },
            { at: [0, 0.56, -1.12], rx: 0.17, ry: 0.07, color: s.dark },
            { at: [0, 0.48, -1.24], rx: 0.12, ry: 0.05, color: s.dark },
          ],
          { sides: 12, steps: 2, capStart: true, capEnd: true },
        ),
      );
      const ex = CHASSIS.exhaust;
      b.add(cyl(0.1, 0.12, 0.2, 12), s.metal, {
        p: [ex[0], ex[1], ex[2] + 0.12],
        r: [Math.PI / 2, 0, 0],
      });
      b.add(cyl(0.075, 0.075, 0.04, 12), "#151316", {
        p: [ex[0], ex[1], ex[2] + 0.02],
        r: [Math.PI / 2, 0, 0],
      });

      // Blade fenders over every wheel.
      for (const x of [1, -1]) {
        b.addColored(bladeFender(fw.r + 0.07, 0.34, 0.03, -0.55, 0.85, s.trim), {
          p: [x * fw.x, fw.r, fw.z],
        });
        b.addColored(bladeFender(rw.r + 0.07, 0.4, 0.035, -1.15, 0.35, s.main), {
          p: [x * rw.x, rw.r, rw.z],
        });
        // Fender stays down to the body.
        b.add(box(0.2, 0.03, 0.05, 0.01), s.metal, {
          p: [x * (fw.x - 0.2), 0.62, fw.z - 0.1],
          r: [0, 0, x * -0.4],
        });
        b.add(box(0.2, 0.03, 0.05, 0.01), s.metal, {
          p: [x * (rw.x - 0.2), 0.7, rw.z + 0.1],
          r: [0, 0, x * -0.4],
        });
        // Suspension arms to the hubs.
        for (const w of [fw, rw]) {
          b.add(cyl(0.022, 0.022, 0.42, 5), s.metal, {
            p: [x * (w.x * 0.62), w.r + 0.04, w.z],
            r: [0, 0, Math.PI / 2 + x * 0.08],
          });
        }
      }

      // Sidepods between the wheels.
      for (const x of [1, -1]) {
        if (s.pods === "intake") {
          b.addColored(
            loft(
              [
                { at: [x * 0.58, 0.4, 0.42], rx: 0.15, ry: 0.11, sq: 3, color: s.main },
                { at: [x * 0.62, 0.4, 0.2], rx: 0.18, ry: 0.13, sq: 3, color: s.main },
                { at: [x * 0.6, 0.39, -0.15], rx: 0.17, ry: 0.12, sq: 3, color: s.main },
                { at: [x * 0.52, 0.38, -0.42], rx: 0.1, ry: 0.08, sq: 3, color: s.dark },
              ],
              {
                sides: 12,
                steps: 2,
                capStart: true,
                capEnd: true,
                paint: (t, a, base) =>
                  Math.abs(a - Math.PI / 2) < 0.4 && t > 0.1 && t < 0.8
                    ? s.trim
                    : a < -0.3
                      ? s.dark
                      : base,
              },
            ),
          );
          // The intake's dark mouth.
          b.add(ellipsoid(10, 6), "#151316", { p: [x * 0.58, 0.4, 0.46], s: [0.12, 0.085, 0.04] });
        } else if (s.pods === "delta") {
          // Swept-back delta wings out of the sides, like a jet's.
          b.add(
            card(
              [
                [0, 0.38],
                [0.5, -0.42],
                [0.42, -0.58],
                [0, -0.5],
              ],
              0.04,
            ),
            (p) => (p.x > 0.32 ? s.trim : s.main),
            {
              p: [x * 0.38, 0.42, 0.05],
              r: [Math.PI / 2, 0, 0],
              s: [x, 1, 1],
              mirror: x < 0,
            },
          );
          b.addColored(
            loft(
              [
                { at: [x * 0.5, 0.42, 0.42], rx: 0.09, ry: 0.08, color: s.main },
                { at: [x * 0.54, 0.42, 0.1], rx: 0.12, ry: 0.1, color: s.main },
                { at: [x * 0.5, 0.42, -0.35], rx: 0.08, ry: 0.07, color: s.dark },
              ],
              { sides: 10, steps: 2, capStart: true, capEnd: true },
            ),
          );
          b.add(ellipsoid(8, 6), "#151316", { p: [x * 0.5, 0.42, 0.45], s: [0.07, 0.06, 0.03] });
        } else {
          // Round bubble pods, smooth as pebbles.
          b.addColored(
            loft(
              [
                { at: [x * 0.58, 0.4, 0.4], rx: 0.05, ry: 0.05, color: s.main },
                { at: [x * 0.6, 0.41, 0.28], rx: 0.17, ry: 0.15, color: s.main },
                { at: [x * 0.6, 0.41, -0.05], rx: 0.19, ry: 0.16, color: s.main },
                { at: [x * 0.56, 0.4, -0.36], rx: 0.1, ry: 0.09, color: s.dark },
              ],
              {
                sides: 12,
                steps: 2,
                capStart: true,
                capEnd: true,
                paint: (_t, a, base) =>
                  Math.abs(a - 0.3) < 0.22 ? s.stripe : a < -0.3 ? s.dark : base,
              },
            ),
          );
        }
      }

      // The front.
      const fz = 1.27;
      if (s.front === "blade") {
        b.addColored(airfoil(1.9 * W, 0.16, 0.035, s.trim, 0.06, 0.8), { p: [0, 0.2, fz] });
        for (const x of [1, -1])
          b.add(
            card(
              [
                [-0.14, 0],
                [0.12, 0],
                [0.06, 0.16],
                [-0.12, 0.12],
              ],
              0.025,
            ),
            s.stripe,
            {
              p: [x * 0.96 * W, 0.18, fz - 0.04],
              r: [0, Math.PI / 2, 0],
            },
          );
      } else if (s.front === "twin") {
        for (const x of [1, -1]) {
          b.addColored(airfoil(0.62, 0.15, 0.04, s.trim, 0.1, 0.7), {
            p: [x * 0.52, 0.22, fz - 0.02],
            r: [0, 0, x * 0.08],
          });
          b.add(ellipsoid(10, 6), s.cap, { p: [x * 0.2, 0.36, 1.1], s: [0.06, 0.045, 0.05] });
        }
      } else if (s.front === "horns") {
        // Two splitters pushed forward like horns, and a short wing between them.
        for (const x of [1, -1])
          b.addColored(
            loft(
              [
                { at: [x * 0.42, 0.26, 0.92], rx: 0.09, ry: 0.07, color: s.dark },
                { at: [x * 0.44, 0.24, 1.15], rx: 0.07, ry: 0.05, color: s.trim },
                { at: [x * 0.4, 0.24, 1.36], rx: 0.015, ry: 0.012, color: s.trim },
              ],
              { sides: 8, steps: 2, capStart: true, capEnd: true },
            ),
          );
        b.addColored(airfoil(1.3 * W, 0.14, 0.04, s.trim, -0.05, 0.9), { p: [0, 0.2, fz - 0.02] });
      } else {
        // The needle: a long thin nose with a small canard each side.
        for (const x of [1, -1])
          b.add(
            card(
              [
                [0, 0],
                [0.24, -0.1],
                [0.24, -0.14],
                [0, -0.13],
              ],
              0.02,
            ),
            s.trim,
            {
              p: [x * 0.08, 0.33, 1.2],
              r: [Math.PI / 2, 0, 0],
              s: [x, 1, 1],
              mirror: x < 0,
            },
          );
        b.addColored(airfoil(1.7 * W, 0.12, 0.03, s.trim, 0.16, 0.6), { p: [0, 0.2, 1.24] });
      }

      // The back.
      if (s.rear === "wing") {
        b.addColored(airfoil(1.3, 0.3, 0.045, s.trim, 0.0, 1), {
          p: [0, 1.04, -1.18],
          r: [-0.12, 0, 0],
        });
        for (const x of [1, -1]) {
          b.add(
            card(
              [
                [-0.2, -0.06],
                [0.16, -0.06],
                [0.12, 0.1],
                [-0.22, 0.12],
              ],
              0.025,
            ),
            s.stripe,
            {
              p: [x * 0.66, 1.03, -1.18],
              r: [0, Math.PI / 2, 0],
            },
          );
          b.add(box(0.035, 0.42, 0.09, 0.012), s.metal, {
            p: [x * 0.24, 0.8, -1.12],
            r: [0.15, 0, 0],
          });
        }
      } else if (s.rear === "ducktail") {
        // A kicked-up tail across the back, and fat twin pipes.
        b.addColored(airfoil(1.0 * W, 0.26, 0.06, s.main, -0.1, 0.9), {
          p: [0, 0.68, -1.17],
          r: [-0.45, 0, 0],
        });
        for (const x of [1, -1]) {
          b.add(cyl(0.065, 0.075, 0.42, 10), s.metal, {
            p: [x * 0.24, 0.5, -1.14],
            r: [Math.PI / 2 - 0.2, 0, 0],
          });
          b.add(cyl(0.05, 0.05, 0.02, 10), "#151316", {
            p: [x * 0.24, 0.54, -1.35],
            r: [Math.PI / 2 - 0.2, 0, 0],
          });
        }
      } else if (s.rear === "fins") {
        for (const x of [1, -1])
          b.add(
            card(
              [
                [0, 0],
                [0.34, 0],
                [0.42, 0.3],
                [0.3, 0.32],
              ],
              0.04,
            ),
            (p) => (p.y > 0.2 ? s.stripe : s.main),
            {
              p: [x * 0.3, 0.52, -0.82],
              r: [0, -Math.PI / 2, x * -0.2],
            },
          );
        b.addColored(airfoil(0.7, 0.18, 0.04, s.trim, 0, 1), { p: [0, 0.78, -1.15] });
      } else {
        // The jet tail: a tall swept fin, a small tailplane and two burner rings.
        b.add(
          card(
            [
              [0.0, 0],
              [0.42, 0],
              [0.62, 0.52],
              [0.46, 0.54],
            ],
            0.04,
          ),
          (p) => (p.y > 0.36 ? s.stripe : s.main),
          {
            p: [0, 0.58, -0.78],
            r: [0, -Math.PI / 2, 0],
          },
        );
        b.addColored(airfoil(0.9, 0.2, 0.035, s.trim, 0.25, 0.7), { p: [0, 0.66, -1.16] });
        for (const x of [1, -1]) {
          b.add(cyl(0.07, 0.09, 0.3, 12), s.metal, {
            p: [x * 0.22, 0.44, -1.14],
            r: [Math.PI / 2, 0, 0],
          });
          b.add(cyl(0.055, 0.055, 0.02, 12), s.cap, {
            p: [x * 0.22, 0.44, -1.3],
            r: [Math.PI / 2, 0, 0],
          });
        }
      }
      if (detail === 0) {
        // A number-plate stripe of rivets along the sides, headlight slits at the front.
        for (const x of [1, -1])
          b.add(box(0.012, 0.03, 0.4, 0.005), s.stripe, {
            p: [x * 0.47 * W, 0.53, 0.25],
            r: [0, x * 0.17, 0],
          });
      }
      s.extras?.(b, detail);
    },
    decorate(body) {
      // The emblem, on top of the nose just in front of the cowl.
      const e = emblemMesh(s.emblem.kind, s.emblem, 0.26);
      e.position.set(0, 0.5, 0.86);
      e.rotation.x = -Math.PI / 2 + 0.38;
      body.add(e);
    },
  };
}
