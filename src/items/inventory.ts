/**
 * The balloon a racer is holding: its colour, upgrade level and ammunition, stored
 * separately.
 *
 * Rules:
 * - Collecting the colour you already hold (with ammo left) upgrades it, up to level 3.
 * - At level 3, the same colour again refills the ammunition.
 * - A different colour replaces what you hold, at level 1.
 * - Once the last of the ammo is used you hold nothing, so the next balloon is level 1.
 *
 * What each colour and level does:
 * - red: 1 missile, 2 homing missile, 3 ten missiles
 * - blue: boosts, short / medium / long
 * - green: 1 oil slick, 2 mine, 3 bubble trap
 * - yellow: shields, short / medium / long
 * - rainbow: 1 magnet, 2 longer-range magnet, 3 reverse magnet (pulls a rival to you)
 */
export const COLORS = ["red", "blue", "green", "yellow", "rainbow"] as const;
export type BalloonColor = (typeof COLORS)[number];

export interface Held {
  color: BalloonColor | null;
  /** 0 when holding nothing, otherwise 1-3. */
  level: number;
  ammo: number;
}

export interface InventoryConfig {
  /** Missiles in a level-3 red balloon. */
  redL3Ammo: number;
}

export const emptyHeld = (): Held => ({ color: null, level: 0, ammo: 0 });

export function ammoFor(color: BalloonColor, level: number, cfg: InventoryConfig): number {
  return color === "red" && level >= 3 ? cfg.redL3Ammo : 1;
}

/** Pick up a balloon. Returns what changed, for feedback. */
export function collectBalloon(
  h: Held,
  color: BalloonColor,
  cfg: InventoryConfig,
): "new" | "upgrade" | "refill" {
  if (h.color === color && h.ammo > 0) {
    if (h.level >= 3) {
      h.ammo = ammoFor(color, 3, cfg);
      return "refill";
    }
    h.level += 1;
    h.ammo = ammoFor(color, h.level, cfg);
    return "upgrade";
  }
  h.color = color;
  h.level = 1;
  h.ammo = ammoFor(color, 1, cfg);
  return "new";
}

/** Use one shot. When the ammo runs out, the racer holds nothing. */
export function useAmmo(h: Held) {
  h.ammo = Math.max(0, h.ammo - 1);
  if (h.ammo === 0) {
    h.color = null;
    h.level = 0;
  }
}

/** A short name for the HUD, e.g. "Blue 2" or "Red 3 ×7". */
export function heldLabel(h: Held): string {
  if (!h.color) return "-";
  const name = h.color[0]!.toUpperCase() + h.color.slice(1);
  return h.ammo > 1 ? `${name} ${h.level} ×${h.ammo}` : `${name} ${h.level}`;
}
