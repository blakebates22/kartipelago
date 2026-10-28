/** The story dragons' designs, by id. */
import type { DesignId, DragonDesign } from "../types";
import { CINDERJAW } from "./cinderjaw";
import { KING } from "./king";
import { LUMEN, LUMEN_GROWN } from "./lumen";
import { RIMEFANG } from "./rimefang";
import { SCORCHWIND } from "./scorchwind";
import { TIDEWYRM } from "./tidewyrm";

export const DESIGNS: Record<DesignId, DragonDesign> = {
  cinderjaw: CINDERJAW,
  rimefang: RIMEFANG,
  scorchwind: SCORCHWIND,
  tidewyrm: TIDEWYRM,
  king: KING,
  lumen: LUMEN,
  lumen_grown: LUMEN_GROWN,
};
