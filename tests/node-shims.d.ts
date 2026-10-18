// Just enough of Node's types for the tests that read files (no @types/node needed).
declare module "node:fs/promises" {
  export function readFile(path: URL | string): Promise<Uint8Array>;
}
declare module "node:fs" {
  export function readFileSync(path: URL | string): Uint8Array;
  export function readFileSync(path: URL | string, encoding: "utf8"): string;
  export function existsSync(path: URL | string): boolean;
}
