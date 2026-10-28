// Adventure mode's progress rules (src/adventure/progress.ts), for the approved story
// (Blake, Oct 27: "The Shattered Pact"): a whole playthrough from the opening to the
// credits never gets stuck and plays every scene once, in order; the regions look the
// way the story says; light shards need every shard piece AND a win; replays never undo
// the story; the save survives a reload.
import { describe, expect, it } from "vitest";
import {
  DRAGON,
  END_CREDITS,
  FAKE_CREDITS,
  KINGDOMS,
  OPENING,
  RAGE,
  sceneOf,
} from "../src/adventure/data";
import {
  BEFORE_KING,
  HEART,
  UNDERGROUND,
  afterScene,
  bossFinished,
  challengeScene,
  crewOf,
  driversOf,
  dragonPhase,
  duelFinished,
  dueScene,
  eraseAdventure,
  finalFinished,
  gamesFinished,
  kingRaceFinished,
  kingdomPhase,
  loadAdventure,
  markSeen,
  newSave,
  newStoneScene,
  objective,
  raceFinished,
  regionLook,
  saveAdventure,
  shardCourse,
  shardRaceFinished,
  shardsOf,
  SLOTS,
  storyKingdom,
  storyScenes,
  winsOf,
  type AdventureSave,
} from "../src/adventure/progress";
import { SCENES, sceneById } from "../src/adventure/scenes";
import { autoCoinSpots } from "../src/game/coins";
import { STARTERS, loadUnlocked, unlockRacer } from "../src/app/unlocks";
import { kingdomField } from "../src/adventure/run";
import { minigameById } from "../src/game/minigames";
import { trackById } from "../src/game/tracks";
import { regionById, regionOfKingdom } from "../src/overworld/regions";

const exists = (id: string) => Boolean(trackById(id));
const hereIn = (s: AdventureSave) => (id: string) =>
  regionOfKingdom(id as never)?.id === s.where?.region;

/** Play every scene that's due (as the screens do: each puts you where it leaves you). */
function watch(s: AdventureSave, log: string[]) {
  for (let d = dueScene(s, hereIn(s)); d; d = dueScene(s, hereIn(s))) {
    log.push(d);
    markSeen(s, d);
    afterScene(s, d);
  }
}
/** A scene that starts a race where it happens (the overworld plays it). */
function trigger(s: AdventureSave, log: string[], id: string) {
  expect(s.seen).not.toContain(id);
  log.push(id);
  markSeen(s, id);
}
const drive = (s: AdventureSave, region: string, at?: string) =>
  (s.where = { region, ...(at ? { at } : {}) });

describe("the story data", () => {
  it("names real courses, mini-games, regions and journeys", () => {
    for (const k of KINGDOMS) {
      expect(k.courses).toHaveLength(4);
      for (const c of k.courses) {
        expect(trackById(c.track), c.track).toBeDefined();
        expect(shardCourse(c, exists).standIn, c.track).toBe(false);
      }
      expect(trackById(k.boss.track), k.boss.track).toBeDefined();
      expect(minigameById(k.minigame), k.minigame).toBeDefined();
      expect(regionById(k.tunnel)?.journey, k.tunnel).toBeDefined();
      expect(regionOfKingdom(k.id)?.cave, k.id).toBeDefined();
    }
    // One mini-game each.
    expect(new Set(KINGDOMS.map((k) => k.minigame)).size).toBe(4);
    for (const c of DRAGON.courses) {
      expect(trackById(c.track)).toBeDefined();
      expect(shardCourse(c, exists).standIn).toBe(false);
    }
    expect(trackById(DRAGON.king.track)).toBeDefined();
  });

  it("four shard pieces spread round the lap", () => {
    const spots = autoCoinSpots(1000);
    expect(spots.map((s) => s.at)).toEqual([180, 410, 630, 860]);
  });
});

describe("a playthrough", () => {
  it("goes from the opening to the credits without getting stuck, every scene once", () => {
    const s = newSave();
    s.racer = "tiko";
    const log: string[] = [OPENING];
    markSeen(s, OPENING);
    drive(s, "dinosaur_valley");
    watch(s, log);
    expect(log.at(-1)).toBe(sceneOf("valley", "festival"));
    expect(regionLook(s, "valley")).toBe("free");

    // ---- Acts I and II: out through the four kingdoms.
    for (const k of KINGDOMS) {
      const r = regionOfKingdom(k.id)!;
      if (k.id !== "valley") {
        // Its welcome (Caught) waits until you've driven there.
        watch(s, log);
        expect(log).not.toContain(sceneOf(k.id, "caught"));
        drive(s, r.id);
        watch(s, log);
        expect(log.at(-1)).toBe(sceneOf(k.id, "caught"));
        expect(regionLook(s, k.id)).toBe("conquered");
      }
      expect(storyKingdom(s)).toBe(k.id);
      expect(kingdomPhase(s, k)).toBe("games");
      expect(objective(s)).toContain("WIN ITS 4 COURSES");
      const courses = [...k.courses].reverse();
      expect(raceFinished(s, k.id, courses[0]!.track, 2).progressed).toBe(false);
      courses.forEach((c, i) => {
        expect(raceFinished(s, k.id, c.track, 1).progressed).toBe(true);
        watch(s, log);
        // The dragon in the stands, halfway through the games.
        if (i === 1 && k.id !== "valley") expect(log.at(-1)).toBe(sceneOf(k.id, "stands"));
      });
      expect(winsOf(s, k.id)).toBe(4);
      // The champion drives up as you come out: their challenge, then the 1 on 1.
      expect(kingdomPhase(s, k)).toBe("duel");
      trigger(s, log, challengeScene(k.id));
      expect(duelFinished(s, k.id, 2).progressed).toBe(false);
      expect(duelFinished(s, k.id, 1).progressed).toBe(true);
      expect(crewOf(s)).toContain(k.champion.look);
      watch(s, log);
      expect(log).toContain(sceneOf(k.id, "prize"));
      if (k.id === "valley") {
        // Cinderjaw comes at the end of festival day; the valley's his.
        expect(log.slice(-3)).toEqual([
          sceneOf("valley", "prize"),
          sceneOf("valley", "hundredth"),
          sceneOf("valley", "way_out"),
        ]);
        expect(regionLook(s, "valley")).toBe("conquered");
      }
      // The underground games, as the champion: the welcome, the mini-game, the key.
      expect(kingdomPhase(s, k)).toBe("underground");
      trigger(s, log, UNDERGROUND(k.id));
      expect(gamesFinished(s, k.id, false).progressed).toBe(false);
      expect(gamesFinished(s, k.id, true).progressed).toBe(true);
      watch(s, log);
      expect(log.slice(-2)).toEqual([sceneOf(k.id, "key"), sceneOf(k.id, "stone")]);
      expect(kingdomPhase(s, k)).toBe("escaped");
      // The stone's scene put you through the smugglers' tunnel, into the journey on.
      expect(s.where).toEqual({ region: k.tunnel, at: "start" });
    }

    // ---- Act III: the Dragon Kingdom.
    expect(dragonPhase(s)).toBe("games");
    watch(s, log);
    expect(log).not.toContain("dragon_challenger");
    drive(s, "dragon_kingdom");
    watch(s, log);
    expect(log.at(-1)).toBe("dragon_challenger");
    for (const c of DRAGON.courses) raceFinished(s, "dragon", c.track, 1);
    expect(dragonPhase(s)).toBe("king");
    trigger(s, log, BEFORE_KING);
    expect(kingRaceFinished(s, 3).progressed).toBe(false);
    expect(kingRaceFinished(s, 1).progressed).toBe(true);
    expect(regionLook(s, "dragon")).toBe("ruined");
    watch(s, log);
    // The Return, Lumen, the Horn, the fake ending, the Rage; the blackout leaves you in
    // the ruined valley, and Rex breaks you out.
    const act3 = ["dragon_return", "dragon_lumen", "dragon_horn", FAKE_CREDITS, ...RAGE];
    expect(log.slice(-(act3.length + 1))).toEqual([...act3, sceneOf("valley", "rescue")]);
    for (const k of KINGDOMS) expect(regionLook(s, k.id)).toBe("ruined");

    // ---- Act IV: back through the ruins.
    for (const k of KINGDOMS) {
      const r = regionOfKingdom(k.id)!;
      expect(kingdomPhase(s, k)).toBe("shards");
      if (k.id !== "valley") drive(s, r.id);
      // A shard needs every piece and 1st.
      const c0 = k.courses[0]!.track;
      expect(shardRaceFinished(s, c0, { got: 4, total: 4 }, 2).progressed).toBe(false);
      expect(shardRaceFinished(s, c0, { got: 3, total: 4 }, 1).progressed).toBe(false);
      for (const c of k.courses)
        expect(shardRaceFinished(s, c.track, { got: 4, total: 4 }, 1).progressed).toBe(true);
      expect(shardsOf(s, k.id)).toBe(4);
      expect(kingdomPhase(s, k)).toBe("boss");
      trigger(s, log, newStoneScene(k.id));
      expect(bossFinished(s, k.id, 2).progressed).toBe(false);
      expect(bossFinished(s, k.id, 1).progressed).toBe(true);
      watch(s, log);
      expect(log.at(-1)).toBe(sceneOf(k.id, "yield"));
      expect(kingdomPhase(s, k)).toBe("restored");
      expect(regionLook(s, k.id)).toBe("restored");
      expect(s.where).toEqual({ region: r.id, at: "cave:front" });
    }

    // ---- Act V.
    expect(dragonPhase(s)).toBe("shards");
    drive(s, "dragon_kingdom");
    watch(s, log);
    expect(log.at(-1)).toBe("dragon_court");
    for (const c of DRAGON.courses) shardRaceFinished(s, c.track, { got: 4, total: 4 }, 1);
    expect(dragonPhase(s)).toBe("final");
    trigger(s, log, HEART);
    expect(finalFinished(s, 2).progressed).toBe(false);
    expect(finalFinished(s, 1).progressed).toBe(true);
    watch(s, log);
    expect(log.slice(-3)).toEqual(["dragon_lumen_returns", "ending", END_CREDITS]);
    expect(dragonPhase(s)).toBe("done");
    expect(regionLook(s, "dragon")).toBe("restored");
    expect(objective(s)).toContain("RESTORED");

    // Every scene played once, and every scene the story has was played.
    expect(new Set(log).size).toBe(log.length);
    const credits = [FAKE_CREDITS, END_CREDITS];
    for (const id of Object.keys(SCENES)) expect(log, id).toContain(id);
    for (const id of log) if (!credits.includes(id)) expect(sceneById(id), id).toBeDefined();
  });

  it("opens the kingdoms one after another, each way", () => {
    const s = newSave();
    const ph = () => KINGDOMS.map((k) => kingdomPhase(s, k));
    expect(ph()).toEqual(["games", "locked", "locked", "locked"]);
    s.games.valley = true;
    expect(ph()).toEqual(["games", "games", "locked", "locked"]);
    s.kingRace = true;
    expect(ph()).toEqual(["shards", "waiting", "waiting", "waiting"]);
    s.bosses.valley = true;
    expect(ph()).toEqual(["restored", "shards", "waiting", "waiting"]);
  });

  it("a replay never undoes the story", () => {
    const s = newSave();
    const t = KINGDOMS[0]!.courses[0]!.track;
    shardRaceFinished(s, t, { got: 4, total: 4 }, 1);
    shardRaceFinished(s, t, { got: 0, total: 4 }, 8);
    expect(s.shards[t]).toBe(true);
    raceFinished(s, "valley", t, 1);
    expect(raceFinished(s, "valley", t, 6).progressed).toBe(false);
    expect(s.wins[t]).toBe(true);
    duelFinished(s, "valley", 1);
    duelFinished(s, "valley", 2);
    expect(s.duels.valley).toBe(true);
    // (Every due scene is in story order: the list's scenes each appear once.)
    const ids = storyScenes(s).map(([id]) => id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});

describe("the save", () => {
  it("survives a reload, and junk in storage is ignored", () => {
    const mem = new Map<string, string>();
    const store = {
      getItem: (k: string) => mem.get(k) ?? null,
      setItem: (k: string, v: string) => void mem.set(k, v),
    };
    const s = newSave();
    raceFinished(s, "valley", "riverbend_palms", 1);
    s.shards.riverbend_palms = true;
    s.duels.valley = true;
    s.racer = "pebble";
    s.driver = "rex";
    markSeen(s, OPENING);
    s.where = { region: "snow_kingdom", at: "frostveil" };
    saveAdventure(s, store);
    expect(loadAdventure(store)).toEqual(s);
    mem.set(
      "kartipelago.adventure.v2",
      '{"wins":{"x":"yes"},"seen":[3,"first_race"],"kingRace":1}',
    );
    const j = loadAdventure(store)!;
    expect(j.wins).toEqual({});
    expect(j.seen).toEqual(["first_race"]);
    expect(j.kingRace).toBe(false);
    mem.set("kartipelago.adventure.v2", '{"where":{"region":4}}');
    expect(loadAdventure(store)!.where).toBeUndefined();
    mem.set("kartipelago.adventure.v2", "not json");
    expect(loadAdventure(store)).toBeUndefined();
  });

  it("three files, each with its own story and racer; the old story's files are left alone", () => {
    const mem = new Map<string, string>();
    const store = {
      getItem: (k: string) => mem.get(k) ?? null,
      setItem: (k: string, v: string) => void mem.set(k, v),
      removeItem: (k: string) => void mem.delete(k),
    };
    mem.set("kartipelago.adventure.v1", '{"cups":{"valley":true}}');
    expect(SLOTS).toBe(3);
    expect(loadAdventure(store, 0)).toBeUndefined();
    const a = newSave();
    a.racer = "tiko";
    const b = newSave();
    b.racer = "pebble";
    saveAdventure(a, store, 0);
    saveAdventure(b, store, 2);
    expect(loadAdventure(store, 0)).toEqual(a);
    expect(loadAdventure(store, 1)).toBeUndefined();
    expect(loadAdventure(store, 2)!.racer).toBe("pebble");
    eraseAdventure(store, 2);
    expect(loadAdventure(store, 2)).toBeUndefined();
    expect(mem.get("kartipelago.adventure.v1")).toBe('{"cups":{"valley":true}}');
  });
});

describe("the crew", () => {
  it("you drive your own racer or a champion who's joined you, never another starter", () => {
    const mem = new Map<string, string>();
    const store = {
      getItem: (k: string) => mem.get(k) ?? null,
      setItem: (k: string, v: string) => void mem.set(k, v),
    };
    expect([...loadUnlocked(store)]).toEqual(STARTERS);
    const s = newSave();
    s.racer = "tiko";
    expect(driversOf(s)).toEqual(["tiko"]);
    duelFinished(s, "valley", 1);
    duelFinished(s, "snow", 1);
    expect(driversOf(s)).toEqual(["tiko", "rex", "brachio"]);
    expect(unlockRacer("rex", store)).toBe(true);
    expect(unlockRacer("rex", store)).toBe(false);
    // A file raced as Rex: his cousin joins in his place, so Rex isn't listed twice.
    const r = newSave();
    r.racer = "rex";
    duelFinished(r, "valley", 1);
    expect(driversOf(r)).toEqual(["rex"]);
    expect(KINGDOMS.map((k) => k.champion.look).sort()).toEqual(
      ["raptor", "rex", "brachio", "stego"].sort(),
    );
  });
});

describe("who you race", () => {
  it("the kingdom's champion, the other starters, your crew, and locals in other paints", () => {
    const f = kingdomField("valley", "tiko", new Set());
    expect(f).toHaveLength(7);
    expect(f[0]).toEqual({ id: "rex", alt: false });
    const met = f.filter((r) => !r.alt).map((r) => r.id);
    expect(met.sort()).toEqual(["brakka", "pebble", "rex", "zephyr"]);
    expect(f.some((r) => r.id === "tiko" && !r.alt)).toBe(false);
    // Later, Rex is in your crew; the Snow Kingdom brings Brachio.
    const s = kingdomField("snow", "tiko", new Set(["rex"]))
      .filter((r) => !r.alt)
      .map((r) => r.id);
    expect(s).toContain("brachio");
    expect(s).toContain("rex");
    expect(s).not.toContain("stego");
  });
});
