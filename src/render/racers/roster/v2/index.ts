/**
 * The v2 racers (prototype): new heads and sleek karts on the v1 bodies. Turn them on
 * with ?racers=v2 (see racer.ts).
 */
import type { RacerId } from "../../designs";
import type { RacerBuild } from "../types";
import { TIKO_V2 } from "./tiko";
import { BRAKKA_V2 } from "./brakka";
import { PEBBLE_V2 } from "./pebble";
import { ZEPHYR_V2 } from "./zephyr";

export const BUILDS_V2: Partial<Record<RacerId, RacerBuild>> = {
  tiko: TIKO_V2 as unknown as RacerBuild,
  brakka: BRAKKA_V2 as unknown as RacerBuild,
  pebble: PEBBLE_V2 as unknown as RacerBuild,
  zephyr: ZEPHYR_V2 as unknown as RacerBuild,
};
