import { defineConfig } from "vitest/config";

export default defineConfig({
  // Relative base so the build works on GitHub Pages under /<repo-name>/
  // without hardcoding the repo name.
  base: "./",
  build: {
    target: "es2022",
    sourcemap: true,
    // Three.js alone is ~550 kB minified; split chunks once the game grows.
    chunkSizeWarningLimit: 800,
    // Two pages: the game, and the racer preview (garage.html).
    rollupOptions: {
      input: { main: "index.html", garage: "garage.html" },
    },
  },
  test: {
    include: ["tests/**/*.test.ts"],
  },
});
