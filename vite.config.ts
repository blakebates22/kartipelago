import { defineConfig, type Plugin } from "vitest/config";
import { reviewStore } from "./tools/reviewStore.mjs";

/**
 * Dev only: when the Blender add-on exports a track into public/tracks/<id>/, tell the
 * open game (it reloads that track's geometry in place, without a page reload). The
 * add-on writes route.json last, so a change to it means the whole export is on disk.
 */
function trackWatcher(): Plugin {
  return {
    name: "kartipelago-track-watcher",
    apply: "serve",
    configureServer(server) {
      const timers = new Map<string, ReturnType<typeof setTimeout>>();
      const changed = (file: string) => {
        const m = /[\\/]public[\\/]tracks[\\/]([^\\/]+)[\\/](route|track)\.json$/.exec(file);
        if (!m) return;
        const id = m[1]!;
        clearTimeout(timers.get(id));
        timers.set(
          id,
          setTimeout(() => {
            server.ws.send({ type: "custom", event: "kp:track-changed", data: { id } });
            server.config.logger.info(`track "${id}" changed: reloading it in the game`);
          }, 400),
        );
      };
      server.watcher.on("change", changed);
      server.watcher.on("add", changed);
    },
  };
}

export default defineConfig({
  // Relative base so the build works on GitHub Pages under /<repo-name>/
  // without hardcoding the repo name.
  base: "./",
  plugins: [trackWatcher(), reviewStore()],
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
