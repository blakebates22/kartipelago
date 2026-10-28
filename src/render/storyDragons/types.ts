/**
 * What a story dragon's design says: its spine (the one skin from tail tip to the back
 * of the skull), its legs, wings, spines and fins, how its hide is painted, its head
 * (built by the design itself: that's where the character is), its breath and its
 * manner. The engine (render/storyDragon.ts) builds and animates any of them.
 *
 * Body space: metres at scale 1, +z forward, +y up, +x the dragon's left; the ground at
 * y = 0 under its feet.
 */
import type * as THREE from "three";
import type { BreathKind } from "./breath";
import type { EyeRig } from "./face";

export type V3 = [number, number, number];

export type DesignId =
  "cinderjaw" | "rimefang" | "scorchwind" | "tidewyrm" | "king" | "lumen" | "lumen_grown";

/** A spine control point: z, y, half-width, half-height (and squareness, belly keel). */
export type SpinePoint = [number, number, number, number, number?, number?];

export interface LegDesign {
  /** The hip (or shoulder) joint at rest, left side, body space. */
  hip: V3;
  /** Where the foot stands at rest (left side): x, z on the ground. */
  foot: [number, number];
  /** Thigh (upper arm) and shin (forearm) lengths. */
  upper: number;
  lower: number;
  /** From the ball of the foot up to the ankle (wrist), body space (left side). */
  meta: V3;
  /** Radii: haunch (where it meets the body), hip, knee, ankle, ball. */
  radii: [number, number, number, number, number];
  /** Which way the knee points: 1 forward (hind legs), -1 back (forelegs). */
  knee: 1 | -1;
  toes: number;
  toeLen: number;
  toeR: number;
  claw: number;
  /** The leg's colours (upper, lower) and the claws'. */
  color: [string, string];
  clawColor: string;
}

export interface WingDesign {
  /** The shoulder joint (left), and where the membrane meets the flank, at rest. */
  root: V3;
  flank: V3;
  humerus: number;
  forearm: number;
  /** Finger lengths, leading edge first. */
  fingers: number[];
  /** The fingers' fan when spread (radians in the wing's plane: 0 straight out, -pi/2
   * straight back). */
  fan: [number, number];
  boneR: number;
  /** Trailing-edge scallop (0..0.5) and how much the membrane sags. */
  scallop: number;
  sag: number;
  membrane: string;
  edge: string;
  vein?: string;
  bone: string;
  thumb: number;
  /** See-through membrane (0..1 opacity), and a glow (emissive colour). */
  opacity?: number;
  glow?: string;
  /** Repaint a membrane vertex (panel index or -1 for the inner ones; sr out along the
   * panel, a across it). */
  paint?: (c: THREE.Color, panel: number, sr: number, a: number) => THREE.Color;
  /** Resting spread (0..1). */
  rest: number;
}

/** A row of spines/plates/crystals/fin rays along the spine (0..1 along it). */
export interface SpikeRow {
  from: number;
  to: number;
  count: number;
  /** Height at the start, middle and end of the row. */
  size: [number, number, number];
  shape: "spike" | "plate" | "crystal" | "ray" | "nub";
  color: string;
  tip?: string;
  /** Lean back (radians). */
  lean: number;
  /** Width as a fraction of height. */
  width: number;
  /** Two rows, either side of the ridge (offset, radians round the body). */
  pair?: number;
  /** Translucent (crystals). */
  glass?: boolean;
}

/** A sail or fin along the back: a membrane on rays, `from`..`to` along the spine. */
export interface SailDesign {
  from: number;
  to: number;
  height: (k: number) => number;
  rays: number;
  color: string;
  edge: string;
  paint?: (c: THREE.Color, k: number, h: number) => THREE.Color;
  /** Down the middle of the back (0) or the belly (pi). */
  around?: number;
  opacity?: number;
}

/** A painted hide: the colour, height (bump) and glow at a spot on the skin. */
export interface HideSample {
  color: THREE.Color;
  /** 0..1, raised scales high. */
  height: number;
  /** Glow (0..1, in the design's glow colour). */
  glow: number;
}

export interface HideContext {
  /** 0..1 round the body from the belly's midline, up the left side to the back. */
  u: number;
  /** Distance from the tail tip (rest), and the landmarks along the spine. */
  s: number;
  hip: number;
  shoulder: number;
  head: number;
  length: number;
  /** Detail-cell coordinates (scales) here. */
  cu: number;
  cv: number;
  /** Up the side: -1 belly .. 1 back. */
  up: number;
}

export interface HeadParts {
  /** The head (pivot where the neck meets the skull) and the jaw (pivot at the hinge). */
  head: THREE.Group;
  jaw: THREE.Group;
  /** How far the jaw opens (radians). */
  jawOpen: number;
  eyes: EyeRig[];
  /** Brow groups (left, right) to raise and knit. */
  brows: THREE.Object3D[];
  /** Where the breath comes out, and a nostril (head space). */
  mouth: V3;
  nose: V3;
  /** Things that sway (whiskers, beard, frill) and a frill that flares. */
  sway: { obj: THREE.Object3D; amount: number; phase: number }[];
  frill?: THREE.Object3D;
  /** Things that glow with the breath (a throat, a mouth's insides). */
  heat?: THREE.MeshLambertMaterial;
}

export interface HeadKit {
  /** Hide-bumped parts (vertex colours). */
  skin: THREE.Material;
  /** The eyes' whites and pupils, the irises (they may glow), crystals/glass. */
  eye: THREE.Material;
  iris: THREE.Material;
  glass: THREE.Material;
  /** A mouth that glows with fire. */
  heat: THREE.MeshLambertMaterial;
  /** Thin membranes seen from both sides (frills, fins, fans). */
  fin: THREE.Material;
}

export interface Manner {
  /** Idle sway of the body, the tail's swish, breathing depth. */
  sway: number;
  tail: number;
  breathe: number;
  /** Seconds between blinks. */
  blink: number;
  /** How wide the jaw goes in speech (0..1), and how much the head bobs with it. */
  talk: number;
  nod: number;
  /** Brows at rest (-1 knit .. 1 raised), and when talking. */
  brow: number;
  talkBrow: number;
  /** Smoke from the nostrils at rest (0..1). */
  smoke: number;
  /** A golden aura (Lumen). */
  aura: number;
  /** Side-to-side undulation of the body (a serpent). */
  undulate: number;
  /** Cock the head (curious/sly). */
  tilt: number;
  /** How fast poses change (1 normal). */
  speed: number;
  /** Squint while talking (sly), brows asymmetric (the showman). */
  squint: number;
  quirk: number;
}

export interface DragonDesign {
  id: DesignId;
  spine: SpinePoint[];
  /** Indices into the spine: where the hips and shoulders are, and how many points are
   * the neck (ending at the back of the skull). */
  hip: number;
  shoulder: number;
  neck: number;
  /** The head's size (1 as built). */
  headScale?: number;
  /** The head's rest tilt (radians, + nose down), and how far the skin runs into it. */
  headTilt: number;
  neckInto: number;
  rings: number;
  sides: number;
  cells: number;
  cellAlong?: number;
  hide: (h: HideContext) => HideSample;
  glow?: string;
  /** Bump strength (0 smooth). */
  bump: number;
  legs: { hind: LegDesign; fore: LegDesign };
  wings: WingDesign;
  spikes: SpikeRow[];
  sails?: SailDesign[];
  buildHead: (kit: HeadKit) => HeadParts;
  /** The tail's tip ornament (club, fan, blade...): built along +z from its base, which
   * sits at the tip; it points back along the tail. */
  tailTip?: (kit: HeadKit) => THREE.Object3D;
  /** Tail's rest curl (radians per point, + = down) and sideways drape. */
  tailDroop: number;
  tailDrape: number;
  breath: BreathKind;
  manner: Manner;
  /** Horn/claw colour for the shared parts. */
  horn: string;
}
