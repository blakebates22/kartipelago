/**
 * Character stats. Each character rates speed, acceleration and handling from 1 to 5,
 * where 3 is the base kart in tuning.json. Ratings turn into multipliers on the base
 * handling values, so tuning the base kart moves every character together.
 *
 * Characters are data (assets/data/characters.json). Names and looks are original.
 */
import type { KartConfig } from "./kart";

export interface Character {
  id: string;
  name: string;
  color: string;
  speed: number;
  accel: number;
  handling: number;
}

export interface StatScale {
  /** Top speed change per rating point away from 3, e.g. 0.05 = ±5%. */
  topSpeedPerPoint: number;
  accelPerPoint: number;
  handlingPerPoint: number;
}

const mult = (rating: number, perPoint: number) => 1 + (rating - 3) * perPoint;

/** The base kart config adjusted for one character. Doesn't modify base. */
export function applyCharacter(base: KartConfig, ch: Character, scale: StatScale): KartConfig {
  const speed = mult(ch.speed, scale.topSpeedPerPoint);
  const accel = mult(ch.accel, scale.accelPerPoint);
  const handling = mult(ch.handling, scale.handlingPerPoint);
  return {
    ...base,
    topSpeed: base.topSpeed * speed,
    accel: base.accel * accel,
    // Handling scales every turn rate, normal and drifting, so a sharper character
    // also bends a countersteered drift harder.
    turnRate: base.turnRate * handling,
    turnRateAtTop: base.turnRateAtTop * handling,
    driftTurnTight: base.driftTurnTight * handling,
    driftTurnNeutral: base.driftTurnNeutral * handling,
    driftTurnCounter: base.driftTurnCounter * handling,
    // Offset model works in arc radii: better handling = tighter arcs.
    driftRadiusNeutral: base.driftRadiusNeutral / handling,
    driftRadiusTight: base.driftRadiusTight / handling,
    driftRadiusCounter: base.driftRadiusCounter / handling,
    driftRadiusCounterOut: base.driftRadiusCounterOut / handling,
    sharpMinRadius: base.sharpMinRadius / handling,
  };
}
