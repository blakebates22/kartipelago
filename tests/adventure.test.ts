// Adventure mode's progress rules (src/adventure/progress.ts): a whole playthrough from
// the first scene to the ending never gets stuck; map pieces need all four coins AND a
// win; replays never undo the story; the save survives a reload.
import { describe, expect, it } from "vitest";
import { DRAGON, KINGDOMS, STORY_ORDER } from "../src/adventure/data";
import {
  bossFinished,
  championsOf,
  coinCourse,
  coinRaceFinished,
  completeReturn,
  cupFinished,
  dragonPhase,
  dueScene,
  kingFinished,
  kingdomPhase,
  loadAdventure,
  markSeen,
  newSave,
  objective,
  piecesOf,
  saveAdventure,
  toolsOf,
  unlocked,
  type AdventureSave,
} from "../src/adventure/progress";
import { sceneById } from "../src/adventure/scenes";
import { autoCoinSpots } from "../src/game/coins";
import { STARTERS, loadUnlocked, unlockRacer } from "../src/app/unlocks";
import { kingdomField } from "../src/adventure/run";
import { trackById } from "../src/game/tracks";

const exists = (id: string) => Boolean(trackById(id));

/** Play every scene that's due (as the hub does). */
function watch(s: AdventureSave, log: string[]) {
  for (let d = dueScene(s); d; d = dueScene(s)) {
    log.push(d);
    markSeen(s, d);
  }
}

describe("the story data", () => {
  it("names real courses, and every scene the story asks for exists", () => {
    for (const k of KINGDOMS) {
      expect(k.courses).toHaveLength(4);
      for (const c of k.courses) {
        expect(trackById(c.track), c.track).toBeDefined();
        // A ruin named but not built yet stands in with the standard course.
        expect(trackById(coinCourse(c, exists).track)).toBeDefined();
      }
      expect(trackById(k.boss!.track), k.boss!.track).toBeDefined();
      for (const sc of [...Object.values(k.scenes), k.returnTask!.scene])
        expect(sceneById(sc), sc).toBeDefined();
      expect(k.minigame).toBeNull();
    }
    for (const c of DRAGON.courses) expect(trackById(c.track)).toBeDefined();
    expect(trackById(DRAGON.king.track)).toBeDefined();
    for (const sc of Object.values(DRAGON.scenes)) expect(sceneById(sc), sc).toBeDefined();
    expect(sceneById("intro")).toBeDefined();
  });

  it("the valley's built ruins are used; the others stand in", () => {
    const v = KINGDOMS[0]!;
    expect(coinCourse(v.courses[0]!, exists)).toEqual({
      track: "riverbend_palms_ruin",
      standIn: false,
    });
    expect(coinCourse(KINGDOMS[2]!.courses[2]!, exists).standIn).toBe(true);
  });

  it("four coins spread round the lap", () => {
    const spots = autoCoinSpots(1000);
    expect(spots.map((s) => s.at)).toEqual([180, 410, 630, 860]);
  });
});

describe("a playthrough", () => {
  it("goes from the first scene to the ending without getting stuck", () => {
    const s = newSave();
    const log: string[] = [];
    watch(s, log);
    expect(log[0]).toBe("intro");
    expect(unlocked(s, "snow")).toBe(false);
    for (const k of KINGDOMS) {
      expect(kingdomPhase(s, k)).toBe("championship");
      expect(objective(s)).toContain("CHAMPIONSHIP");
      cupFinished(s, k.id, 1);
      watch(s, log);
      expect(log).toContain(k.scenes.catastrophe);
      expect(kingdomPhase(s, k)).toBe("coins");
      for (const c of k.courses) coinRaceFinished(s, c.track, { got: 4, total: 4 }, 1);
      watch(s, log);
      expect(kingdomPhase(s, k)).toBe("boss");
      bossFinished(s, k.id, 1);
      watch(s, log);
      expect(log).toContain(k.scenes.bossWon);
      expect(kingdomPhase(s, k)).toBe("done");
    }
    expect(toolsOf(s)).toHaveLength(4);
    expect(dragonPhase(s)).toBe("first");
    cupFinished(s, "dragon", 1);
    watch(s, log);
    expect(log).toContain(DRAGON.scenes.sacrifice);
    expect(dragonPhase(s)).toBe("return");
    for (const k of KINGDOMS) completeReturn(s, k.id);
    watch(s, log);
    expect(log).toContain(DRAGON.scenes.resurrection);
    expect(dragonPhase(s)).toBe("final");
    cupFinished(s, "dragon_final", 1);
    watch(s, log);
    expect(dragonPhase(s)).toBe("king");
    // The first race against the King is lost whatever happens (scripted).
    kingFinished(s, undefined);
    watch(s, log);
    expect(log).toContain(DRAGON.scenes.kingLost);
    expect(dragonPhase(s)).toBe("king");
    kingFinished(s, 2);
    expect(dragonPhase(s)).toBe("king");
    kingFinished(s, 1);
    watch(s, log);
    expect(dragonPhase(s)).toBe("done");
    expect(log.at(-1)).toBe(DRAGON.scenes.ending);
    expect(objective(s)).toContain("FREE");
    // Every scene played once, in order.
    expect(new Set(log).size).toBe(log.length);
  });

  it("opens the kingdoms one after another", () => {
    const s = newSave();
    expect(STORY_ORDER.map((id) => unlocked(s, id))).toEqual([true, false, false, false, false]);
    s.bosses.valley = true;
    expect(unlocked(s, "snow")).toBe(true);
    expect(unlocked(s, "desert")).toBe(false);
  });
});

describe("treasure map races", () => {
  const track = KINGDOMS[0]!.courses[0]!.track;
  it("need all four coins AND a win", () => {
    const s = newSave();
    expect(coinRaceFinished(s, track, { got: 4, total: 4 }, 2).progressed).toBe(false);
    expect(coinRaceFinished(s, track, { got: 3, total: 4 }, 1).progressed).toBe(false);
    expect(s.pieces[track]).toBeUndefined();
    expect(coinRaceFinished(s, track, { got: 4, total: 4 }, 1).progressed).toBe(true);
    expect(piecesOf(s, KINGDOMS[0]!)).toBe(1);
  });

  it("a replay never takes a piece away, a lost cup never undoes a won one", () => {
    const s = newSave();
    coinRaceFinished(s, track, { got: 4, total: 4 }, 1);
    coinRaceFinished(s, track, { got: 0, total: 4 }, 8);
    expect(s.pieces[track]).toBe(true);
    cupFinished(s, "valley", 1);
    cupFinished(s, "valley", 5);
    expect(s.cups.valley).toBe(true);
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
    cupFinished(s, "valley", 1);
    markSeen(s, "intro");
    saveAdventure(s, store);
    expect(loadAdventure(store)).toEqual(s);
    mem.set("kartipelago.adventure.v1", '{"cups":{"valley":"yes"},"seen":[3,"intro"],"pieces":7}');
    const j = loadAdventure(store)!;
    expect(j.cups).toEqual({});
    expect(j.seen).toEqual(["intro"]);
    expect(j.pieces).toEqual({});
    mem.set("kartipelago.adventure.v1", "not json");
    expect(loadAdventure(store)).toBeUndefined();
  });
});

describe("the crew", () => {
  it("four racers to start; each kingdom's champion joins when you win its cup", () => {
    const mem = new Map<string, string>();
    const store = {
      getItem: (k: string) => mem.get(k) ?? null,
      setItem: (k: string, v: string) => void mem.set(k, v),
    };
    expect([...loadUnlocked(store)]).toEqual(STARTERS);
    const s = newSave();
    expect(championsOf(s)).toEqual([]);
    cupFinished(s, "valley", 1);
    expect(championsOf(s).map((c) => c.look)).toEqual(["rex"]);
    expect(unlockRacer("rex", store)).toBe(true);
    expect(unlockRacer("rex", store)).toBe(false);
    expect(loadUnlocked(store).has("rex")).toBe(true);
    // The four champions are the four racers who aren't starters.
    expect(KINGDOMS.map((k) => k.champion!.look).sort()).toEqual(
      ["raptor", "rex", "brachio", "stego"].sort(),
    );
  });
});

describe("who you race", () => {
  it("your crew, the kingdom's own champion, and local cousins: never a racer you haven't met", () => {
    const crew = new Set(STARTERS);
    const f = kingdomField("valley", "tiko", crew);
    expect(f).toHaveLength(7);
    // Rex, the valley's champion, is there to be beaten.
    expect(f[0]).toEqual({ id: "rex", alt: false });
    const met = f.filter((r) => !r.alt).map((r) => r.id);
    expect(met.sort()).toEqual(["brakka", "pebble", "rex", "zephyr"]);
    // Everyone else is a cousin in the alternate paint of someone you know.
    for (const r of f.filter((x) => x.alt)) expect([...crew]).toContain(r.id);
    // Later, Rex is in your crew; the Snow Kingdom brings Brachio, not the others.
    crew.add("rex");
    const s = kingdomField("snow", "tiko", crew)
      .filter((r) => !r.alt)
      .map((r) => r.id);
    expect(s).toContain("brachio");
    expect(s).not.toContain("stego");
    expect(s).not.toContain("raptor");
  });
});
