/**
 * The overworlds' villagers (Blake, Oct 26): dinosaur folk who live in each kingdom,
 * walking about round their homes, and the townsfolk and crowds of the cutscenes. Their
 * own cast, not the racers, built to the racers' finish: see render/people/folk.ts for
 * the eight kinds and the kingdoms' clothes, and render/people/view.ts for how a crowd
 * stays cheap (far away, each is a few baked meshes).
 *
 * Purely visual: src/overworld/villagers.ts walks them about.
 */
import type * as THREE from "three";
import { buildFolk, FOURS, SIZE, villagerLook, type Folk, type Species } from "./people/folk";
import { createPersonView, type PersonView } from "./people/view";

export { SPECIES, SIZE, villagerLook, type Folk, type Species } from "./people/folk";

/**
 * A villager: place it with update(x, y, z, heading, cue, t), where the cue is how fast
 * it's walking (0..1; it steps by the distance it actually moves) or what it's doing
 * (talking, a gesture, someone to look at).
 */
export type VillagerView = PersonView;

export function createVillagerView(
  parent: THREE.Object3D,
  folk: Folk,
  seed: number,
  kind?: Species,
): VillagerView {
  const look = villagerLook(folk, seed, kind);
  const key = `folk|${folk}|${look.species}|${seed}`;
  return createPersonView(parent, key, () => buildFolk(folk, seed, kind), {
    scale: SIZE[look.species].scale,
    shadow: FOURS.has(look.species) ? 0.95 : 0.5,
    seed,
  });
}
