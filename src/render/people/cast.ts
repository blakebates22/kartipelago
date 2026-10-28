/**
 * A person by a short name, for the preview page and tests: "elder", "lumen",
 * "guard:<folk>:<seed>", "villager:<folk>:<seed>[:<species>]".
 */
import type * as THREE from "three";
import { createElderView, createGuardView, createLumenView } from "./index";
import { createVillagerView, type Folk, type Species } from "../villager";
import type { PersonView } from "./view";

export function createPerson(parent: THREE.Object3D, who: string): PersonView {
  const [kind, a, b] = who.split(":");
  switch (kind) {
    case "lumen":
      return createLumenView(parent);
    case "villager":
      return createVillagerView(
        parent,
        (a ?? "valley") as Folk,
        Number(b ?? 1),
        (who.split(":")[3] || undefined) as Species | undefined,
      );
    case "guard":
      return createGuardView(parent, (a ?? "valley") as Folk, Number(b ?? 7));
    default:
      return createElderView(parent);
  }
}
