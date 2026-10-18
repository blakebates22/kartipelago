// Just enough of Node's types for the tests that read files (no @types/node needed).
declare module "node:fs/promises" {
  export function readFile(path: URL | string): Promise<Uint8Array>;
}
