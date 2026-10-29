// The overworlds' draw budget (Blake, Oct 29: "things are very very laggy ... we need to fix
// this asap"). With the dev server running (npx vite --port 5211):
//
//   node tools/perf/regions.cjs [region ...]        (default: every overworld region)
//
// For each region, from its spawn and in front of each of its gateways: the GPU's draw
// calls, triangles and textures, and the living fires burning. Fails (exit 1) over budget.
const { chromium } = require("playwright");

const PORT = process.env.PORT || 5211;
const BUDGET = { calls: 900, textures: 400, fires: 40 };

(async () => {
  const b = await chromium.launch({
    args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
  });
  const p = await b.newPage({ viewport: { width: 800, height: 450 } });
  p.on("pageerror", (e) => console.log("PAGEERR", e.message));
  await p.goto(`http://localhost:${PORT}/?debug&noclips`, { timeout: 180000 });
  await p.waitForFunction(() => window.kp && window.kp.game, null, { timeout: 180000 });
  const all = await p.evaluate(async () =>
    (await import("/src/overworld/regions.ts")).REGIONS.filter((r) => r.gateways.length).map(
      (r) => r.id,
    ),
  );
  const ids = process.argv.slice(2).length ? process.argv.slice(2) : all;
  let over = 0;
  for (const id of ids) {
    const spots = await p.evaluate(async (id) => {
      const ow = await import("/src/screens/overworld.ts");
      const { REGIONS } = await import("/src/overworld/regions.ts");
      const r = REGIONS.find((x) => x.id === id);
      const g = window.kp.game;
      g.overworld = { region: id, adventure: false, ruined: false };
      g.screens.go(ow.overworldLoading(g, id, undefined, false, false));
      return [
        [r.spawn.x, r.spawn.z, r.spawn.heading],
        ...r.gateways.map((w) => [
          w.x + Math.sin(w.heading) * 20,
          w.z + Math.cos(w.heading) * 20,
          w.heading + Math.PI,
        ]),
      ];
    }, id);
    for (let i = 0; i < 90; i++) {
      await p.waitForTimeout(2000);
      if (
        await p.evaluate(
          () => window.kp.game.screens.top && window.kp.game.screens.top.id === "OVERWORLD",
        )
      )
        break;
    }
    await p.waitForTimeout(2000);
    for (const [x, z, h] of spots) {
      await p.evaluate(([x, z, h]) => window.kp.session.placeYou(x, z, h, 300), [x, z, h]);
      await p.waitForTimeout(1500);
      const r = await p.evaluate(async () => {
        await new Promise((res) => requestAnimationFrame(() => requestAnimationFrame(res)));
        const st = window.kp.stage,
          ren = st.renderer;
        let fires = 0;
        st.scene.traverse((o) => {
          if (o.name !== "fire") return;
          for (let q = o; q; q = q.parent) if (!q.visible) return;
          fires++;
        });
        return {
          calls: ren.info.render.calls,
          tris: ren.info.render.triangles,
          textures: ren.info.memory.textures,
          fires,
        };
      });
      const bad = Object.keys(BUDGET).filter((k) => r[k] > BUDGET[k]);
      if (bad.length) over++;
      console.log(
        `${id} (${x.toFixed(0)}, ${z.toFixed(0)}): ${r.calls} calls, ${(r.tris / 1000).toFixed(0)}k tris, ${r.textures} textures, ${r.fires} fires${bad.length ? "  OVER: " + bad.join(", ") : ""}`,
      );
    }
  }
  await b.close();
  if (over) {
    console.log(`${over} spot(s) over budget`, BUDGET);
    process.exit(1);
  }
})();
