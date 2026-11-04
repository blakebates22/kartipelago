// What a package's bounds.json was baked from: its collision and the review tool's baked
// edits (tests/bounds.test.ts: rebuild a region, bake its bounds again). Two FNV-1a
// hashes over the bytes (no node:crypto: the tests' node shims are all it needs).
import { existsSync, readFileSync } from "node:fs";

function fnv(bytes: Uint8Array[], seed: number) {
  let h = seed >>> 0;
  for (const b of bytes)
    for (let i = 0; i < b.length; i++) {
      h ^= b[i]!;
      h = Math.imul(h, 0x01000193) >>> 0;
    }
  return h.toString(16).padStart(8, "0");
}

export function builtFrom(dir: URL) {
  const meta = JSON.parse(readFileSync(new URL("track.json", dir), "utf8")) as {
    geometry: { collision: string };
  };
  const bytes = [readFileSync(new URL(meta.geometry.collision, dir))];
  const edits = new URL("edits.json", dir);
  if (existsSync(edits)) bytes.push(readFileSync(edits));
  return fnv(bytes, 0x811c9dc5) + fnv(bytes, 0x5bd1e995);
}
