// The review tool's notes (src/review/notes.ts): every note keeps its own number, even
// ones made while the dev server was away (Blake, Oct 28: they all came out as #52).
import { describe, expect, it } from "vitest";
import { renumber, type ReviewNote } from "../src/review/notes";

const note = (id: string, number: number) => ({ id, number }) as ReviewNote;

describe("review notes", () => {
  it("give clashing numbers the next free ones, first come keeps its own", () => {
    const notes = [note("a", 50), note("b", 51), note("c", 52), note("d", 52), note("e", 52)];
    const changed = renumber(notes);
    expect(notes.map((n) => n.number)).toEqual([50, 51, 52, 53, 54]);
    expect(changed.map((n) => n.id)).toEqual(["d", "e"]);
    expect(renumber(notes)).toEqual([]);
  });
});
