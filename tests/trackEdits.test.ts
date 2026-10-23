import * as THREE from "three";
import { describe, expect, it } from "vitest";
import { applyEdits, parseEdits } from "../src/world/trackEdits";

const scene = () => {
  const s = new THREE.Group();
  for (const name of ["Bush_1", "Rock_2", "Palm_3"]) {
    const o = new THREE.Group();
    o.name = name;
    s.add(o);
  }
  return s;
};
const to = { pos: [1, 2, 3], quat: [0, 0, 0, 1], scale: [2, 2, 2] };

describe("baked review edits (edits.json)", () => {
  it("moves, copies and deletes props by name", () => {
    const s = scene();
    const edits = parseEdits({
      schemaVersion: 1,
      edits: [
        { op: "move", node: "Bush_1", to },
        { op: "copy", node: "Palm_3 copy 1", copyOf: "Palm_3", to },
        { op: "delete", node: "Rock_2" },
        { op: "move", node: "Missing", to },
      ],
    });
    applyEdits(s, edits);
    const bush = s.getObjectByName("Bush_1")!;
    expect(bush.position.toArray()).toEqual([1, 2, 3]);
    expect(bush.scale.x).toBe(2);
    expect(s.getObjectByName("Palm_3 copy 1")).toBeDefined();
    expect(s.getObjectByName("Palm_3")!.position.x).toBe(0);
    expect(s.getObjectByName("Rock_2")).toBeUndefined();
  });

  it("skips bad entries with a warning", () => {
    const warnings: string[] = [];
    const edits = parseEdits(
      {
        edits: [
          { op: "spin", node: "Bush_1" },
          { op: "move", node: "Bush_1" },
          { op: "copy", node: "X", to },
        ],
      },
      warnings,
    );
    expect(edits).toEqual([]);
    expect(warnings.length).toBe(3);
  });
});
