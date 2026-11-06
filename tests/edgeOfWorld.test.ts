// The Edge of the World (journey_cause), Nov 3 (Blake: "you cant actually traverse
// backwards. lets just remove the jumps completely ... we need to make the immersiveness
// so great such that the boring driving is justified"): one road with no jumps, no gap in
// it and no slope a kart can't climb either way; each stretch its own sound (the
// atmosphere's sound only: the overworld paints the air); and life over the bridges.
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { airAt, parseAtmosphere } from "../src/game/depths";
import { craneHeading, craneLoad, parseCrane, parseVillagers } from "../src/game/isles";
import { crocKingCue } from "../src/render/people/crocKing";
import { villagerLook } from "../src/render/people/folk";
import { boatAt, parseBoat } from "../src/game/oasis";

type Entity = { type: string } & Record<string, unknown>;
type P = { x: number; y: number; z: number };
const dir = new URL("../public/tracks/journey_cause/", import.meta.url);
const meta = JSON.parse(readFileSync(new URL("track.json", dir), "utf8")) as {
  entities: Entity[];
  journey: { from: number; to: number };
};
const routes = JSON.parse(readFileSync(new URL("route.json", dir), "utf8")) as {
  routes: { id: string; points: P[] }[];
};
const of = (t: string) => meta.entities.filter((e) => e.type === t);

describe("the Edge of the World", () => {
  it("has no jumps: nowhere to fall and be put back, every metre drivable both ways", () => {
    expect(of("respawn")).toHaveLength(0);
    const pts = routes.routes.find((r) => r.id === "main")!.points;
    // (the journey's road, start to end, measured over every 4 m)
    const { from, to } = meta.journey;
    const road: (P & { s: number })[] = [];
    let s = 0;
    pts.forEach((p, k) => {
      if (k) s += Math.hypot(p.x - pts[k - 1]!.x, p.z - pts[k - 1]!.z);
      if (s >= from && s <= to) road.push({ ...p, s });
    });
    expect(road.length).toBeGreaterThan(1000);
    let worst = 0;
    let j = 0;
    for (let k = 1; k < road.length; k++) {
      expect(road[k]!.s - road[k - 1]!.s).toBeLessThan(6);
      while (road[k]!.s - road[j]!.s > 4) j++;
      if (j > 0 && road[k]!.s - road[j - 1]!.s > 3.5)
        worst = Math.max(
          worst,
          Math.abs(road[k]!.y - road[j - 1]!.y) / (road[k]!.s - road[j - 1]!.s),
        );
    }
    expect(worst).toBeLessThan(0.16);
  });

  it("gives every stretch its own sound, and leaves the air to the overworld", () => {
    const [e] = of("atmosphere");
    const a = parseAtmosphere(e!);
    expect(a.light).toBe(false);
    const sounds = new Set(Object.values(a.zones).map((z) => z.sound));
    for (const s of ["drip", "harbour", "tavern", "festival", "falls", "wind", "bells"])
      expect(sounds).toContain(s);
    expect(a.keys.length).toBeGreaterThan(150);
    // (at the docks, the harbour; out at the gate, its bells)
    const at = (x: number, y: number, z: number) => {
      const air = airAt(a, x, y, z)!;
      return Object.entries(air.sound).sort((p, q) => q[1] - p[1])[0]![0];
    };
    const near = (x: number, z: number) =>
      a.keys.reduce((best, k) =>
        Math.hypot(k.x - x, k.z - z) < Math.hypot(best.x - x, best.z - z) ? k : best,
      );
    const dock = near(-5, 332);
    expect(at(dock.x, dock.y, dock.z)).toBe("harbour");
    const gate = near(4, -440);
    expect(at(gate.x, gate.y, gate.z)).toBe("bells");
    // (in the Rusty Anchor Fish Fry, its piano and its diners)
    const anchor = near(109, 264);
    expect(at(anchor.x, anchor.y, anchor.z)).toBe("tavern");
    // (a light-less atmosphere elsewhere still sets the light by default)
    expect(parseAtmosphere({ zones: {}, keys: [] }).light).toBe(true);
  });

  it("is alive between the districts and over the bridges", () => {
    expect(of("boat").length).toBeGreaterThanOrEqual(3);
    expect(of("motes").length).toBeGreaterThanOrEqual(12);
    expect(of("pterosaur").length).toBeGreaterThanOrEqual(3);
    expect(of("birds").length).toBeGreaterThanOrEqual(4);
    // (the sea pouring off the edge over the Long Bore's mouth, and the sea leak in the docks)
    expect(of("waterfall")).toHaveLength(2);
    const flags = of("prayer_flags")[0]!.lines as unknown[];
    expect(flags.length).toBeGreaterThanOrEqual(20);
    expect(of("bells")[0]!.list as unknown[]).toHaveLength(4);
  });

  it("has a harbour that makes sense (Blake, Nov 4): its water in and out, boats under the bridge", () => {
    expect(of("zipper")).toHaveLength(0);
    // (rowing boats, no masts, on one round under the bridge's arch)
    const round = routes.routes.find((r) => r.id === "Harbour Boat Round")!;
    const rowers = of("boat").filter((e) => e.route === "Harbour Boat Round");
    expect(rowers.length).toBe(4);
    const b = parseBoat(rowers[0]!, routes.routes as never)!;
    expect(b.rig).toBe("row");
    expect(boatAt(b, 3).heel).toBeLessThan(0.06);
    // (where the round passes under the road, Blender (-3, y): the bridge is over it, at
    // least 2.8 m of road over the water: its arch 1.7 m up, over the boats)
    const under = round.points.filter((p) => Math.abs(p.x + 3) < 1.5);
    expect(under.length).toBeGreaterThan(0);
    for (const p of under) {
      const bridge = routes.routes
        .find((r) => r.id === "main")!
        .points.filter((q) => Math.hypot(q.x - p.x, q.z - p.z) < 6);
      expect(bridge.length).toBeGreaterThan(0);
      expect(Math.min(...bridge.map((q) => q.y)) - p.y).toBeGreaterThan(2.8);
    }
    // (no sail boats: only the rowing boats under the bridge; review 1 note 1)
    for (const e of of("boat")) expect(e.rig).toBe("row");
    // (the cranes stand still, built in full, their loads hung on: review 1 note 2; a
    // slewing crane is still the game's to draw where a track wants one)
    expect(of("crane")).toHaveLength(0);
    const c = parseCrane({ heading: 1, slew: 0.8, slewPeriod: 20, load: "net" });
    expect(c.load).toBe("net");
    expect(Math.abs(craneHeading(c, 5) - craneHeading(c, 0))).toBeGreaterThan(0.5);
    expect(craneLoad(c, 0).heading).toBeCloseTo(1, 5);
    // (the sea leak's light and the bridge's lanterns light the water)
    expect(of("glow").length).toBeGreaterThanOrEqual(8);
    expect(of("mist").length).toBeGreaterThanOrEqual(8);
  });

  it("is peopled by crocs, not townsfolk, and has its King Croc (Blake, Nov 4)", () => {
    // (every crowd in the Edge is a croc crowd: the black market's and the sky islands')
    const crowds = of("villagers");
    expect(crowds.length).toBe(2);
    for (const e of crowds) expect(["sump", "skycroc"]).toContain(e.palette);
    for (const v of crowds.flatMap((e) => parseVillagers(e)))
      expect(["sump", "skycroc"]).toContain(v.palette);
    // (and the talkers: folk "sump" are crocs)
    for (const e of of("villager_home")) expect(e.folk).toBe("sump");
    expect(villagerLook("sump", 7).species).toBe("croc");
    expect(villagerLook("valley", 7).species).not.toBe("croc");
    // (the King Croc on his throne by the road, facing it)
    const kings = of("croc_king");
    expect(kings).toHaveLength(1);
    const k = kings[0]!;
    const road = routes.routes.find((r) => r.id === "main")!.points;
    const near = Math.min(
      ...road.map((p) => Math.hypot(p.x - (k.x as number), p.z - (k.z as number))),
    );
    expect(near).toBeLessThan(30);
    expect(near).toBeGreaterThan(12);
    // (holding court: a gesture most of the time, roaring now and then)
    const cues = Array.from({ length: 48 }, (_, i) => crocKingCue(i / 2));
    expect(new Set(cues.map((q) => q.gesture)).size).toBeGreaterThanOrEqual(4);
    expect(cues.some((q) => q.talk)).toBe(true);
  });

  it("has the Rookery, the Rusty Anchor, the Gallery and the market's two lanes (Blake, Nov 4)", () => {
    const road = routes.routes.find((r) => r.id === "main")!.points;
    const { from, to } = meta.journey;
    let s = 0;
    const drive = road.filter((p, i) => {
      if (i) s += Math.hypot(p.x - road[i - 1]!.x, p.z - road[i - 1]!.z);
      return s >= from && s <= to;
    });
    // (the water street's boats keep to the water, off the road, under its washing)
    const round = routes.routes.find((r) => r.id === "Rookery Boat Round")!;
    expect(
      of("boat").filter((e) => e.route === "Rookery Boat Round").length,
    ).toBeGreaterThanOrEqual(2);
    for (const p of round.points.filter((_, i) => i % 5 === 0)) {
      const d = Math.min(...drive.map((q) => Math.hypot(q.x - p.x, q.z - p.z)));
      expect(d).toBeGreaterThan(12);
    }
    // (the Gallery: out high on the Night Bazaar's wall, 12 m and more over its floor)
    const inBazaar = drive.filter((p) => Math.hypot((p.x - 140) / 64, (p.z - 145) / 76) < 0.97);
    expect(Math.max(...inBazaar.map((p) => p.y)) - -34.6).toBeGreaterThan(11);
    // (each stretch's own talkers: the slum, the tavern, the Beast Market)
    const talks = of("villager_home").map((e) => e.talk);
    for (const t of ["rookery", "diner", "bazaar", "beasts"]) expect(talks).toContain(t);
    // (and the Beast Market's pens of hatchlings, every kind)
    const pens = of("pen");
    expect(pens.length).toBeGreaterThanOrEqual(6);
    expect(new Set(pens.map((e) => e.species))).toEqual(new Set(["raptor", "trike", "stego"]));
    // (Nov 5, the shantytown: the dancers and their conga gone, the shanty band on its
    // beached bow, one of each instrument, their crowd listening)
    expect(of("conga")).toHaveLength(0);
    const folk = (of("folk_poses")[0]!.list as unknown[][]).map((r) => r[4]);
    for (const play of ["fiddle", "squeeze", "drum"])
      expect(folk.filter((p) => p === play)).toHaveLength(1);
    expect(folk.filter((p) => p === "tap").length).toBeGreaterThanOrEqual(2);
    // (Nov 5, the dry dock where the Fighting Pits' boxing ring was: no boxers, the
    // shipwrights at work on the galleon, hammering, sawing, stirring the tar)
    const pit = (e: Entity) => Math.hypot((e.x as number) - 40, (e.z as number) - 10) < 34;
    expect(of("partygoer").filter(pit)).toHaveLength(0);
    const rows = of("folk_poses")[0]!.list as number[][];
    const inPit = rows.filter((r) => Math.hypot(r[0]! - 40, r[2]! - 10) < 34);
    expect(inPit.length).toBeGreaterThanOrEqual(15);
    expect(inPit.filter((r) => (r[4] as unknown) === "beat").length).toBeGreaterThanOrEqual(4);
    // (and no gambling: the Lucky Bone a treasure hoard, no wheel of fortune, no dancers;
    // its counters, weighers and polishers at work)
    expect(of("partygoer")).toHaveLength(0);
    // (Nov 6, review journey_cause 2: the sky's flags the Kingdom's pennants, its dragons
    // winged, the Kingdom's kind)
    expect(of("prayer_flags")[0]!.style).toBe("pennants");
    for (const e of [...of("little_dragons"), ...of("isles_dragon")])
      expect(e.style).toBe("winged");
    expect(of("waterwheel")).toHaveLength(0);
    const inDen = rows.filter((r) => Math.hypot((r[0]! - 152) / 30, (r[2]! + 36) / 26) < 1);
    expect(inDen.length).toBeGreaterThanOrEqual(8);
    const dancers = (of("villagers") as unknown as { list: unknown[][] }[])
      .flatMap((e) => e.list)
      .filter((r) => r[5] === "dancer");
    expect(
      dancers.filter(
        (r) => Math.hypot(((r[0] as number) - 140) / 64, ((r[2] as number) - 145) / 76) < 1,
      ),
    ).toHaveLength(0);
  });
});
