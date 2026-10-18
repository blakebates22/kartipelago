/**
 * The racers' looks: one storybook palette shared by everyone, and each racer's
 * colours and kart paint. Appearance only: driving stats live in characters.json and
 * are chosen separately.
 */
export const PALETTE = {
  cherry: "#ef6056",
  gold: "#f8c95c",
  leaf: "#62be74",
  sky: "#4e9ecf",
  violet: "#8c70cb",
  rose: "#ec92b5",
  cream: "#f7e8c8",
  chestnut: "#765447",
  // Supporting shades.
  ink: "#2b2235",
  white: "#fffdf6",
  turquoise: "#55c6bd",
  coral: "#f08a8f",
  royal: "#3f6fd1",
  orange: "#f39a2b",
  lavender: "#b9a5e6",
  rust: "#a8583f",
  caramel: "#bf8a52",
} as const;

export type RacerId = "moss" | "bramble" | "poppy" | "otto";

export interface KartPaint {
  body: string;
  trim: string;
  tire: string;
  hub: string;
}

export interface RacerDesign {
  id: RacerId;
  name: string;
  species: string;
  /** The kart paint, and an alternate for when two racers share a design. */
  kart: KartPaint;
  altKart: KartPaint;
}

export const DESIGNS: Record<RacerId, RacerDesign> = {
  moss: {
    id: "moss",
    name: "Moss",
    species: "axolotl",
    kart: { body: PALETTE.gold, trim: PALETTE.turquoise, tire: PALETTE.violet, hub: PALETTE.cream },
    altKart: { body: PALETTE.sky, trim: PALETTE.gold, tire: PALETTE.rose, hub: PALETTE.cream },
  },
  bramble: {
    id: "bramble",
    name: "Bramble",
    species: "squirrel",
    kart: { body: PALETTE.leaf, trim: PALETTE.gold, tire: PALETTE.chestnut, hub: PALETTE.gold },
    altKart: { body: PALETTE.gold, trim: PALETTE.leaf, tire: PALETTE.chestnut, hub: PALETTE.cream },
  },
  poppy: {
    id: "poppy",
    name: "Poppy",
    species: "moth",
    kart: { body: PALETTE.cherry, trim: PALETTE.cream, tire: PALETTE.sky, hub: PALETTE.cream },
    altKart: { body: PALETTE.rose, trim: PALETTE.cream, tire: PALETTE.violet, hub: PALETTE.cream },
  },
  otto: {
    id: "otto",
    name: "Otto",
    species: "capybara",
    kart: { body: PALETTE.royal, trim: PALETTE.orange, tire: PALETTE.gold, hub: PALETTE.cream },
    altKart: { body: PALETTE.violet, trim: PALETTE.orange, tire: PALETTE.gold, hub: PALETTE.cream },
  },
};

export const RACER_IDS: RacerId[] = ["moss", "bramble", "poppy", "otto"];
