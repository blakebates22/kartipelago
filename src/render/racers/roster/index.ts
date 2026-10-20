/**
 * The roster: every racer's build, by id. To add a racer, write roster/<id>.ts (copy one
 * as a starting point), then add their entry to designs.ts and here. See
 * docs/racer-pipeline.md.
 */
import type { RacerId } from "../designs";
import type { RacerBuild } from "./types";
import { TIKO } from "./tiko";
import { BRAKKA } from "./brakka";
import { PEBBLE } from "./pebble";
import { ZEPHYR } from "./zephyr";

export const BUILDS: Record<RacerId, RacerBuild> = {
  tiko: TIKO as unknown as RacerBuild,
  brakka: BRAKKA as unknown as RacerBuild,
  pebble: PEBBLE as unknown as RacerBuild,
  zephyr: ZEPHYR as unknown as RacerBuild,
};
