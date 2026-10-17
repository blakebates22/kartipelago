import GUI from "lil-gui";
import { tuning, tuningAsJson } from "../core/tuning";

/**
 * Live controls for every value in tuning.json. Builds itself from the data,
 * so new tuning keys appear automatically. Strings starting with # get a color picker.
 */
export function createTuningPanel() {
  const gui = new GUI({ title: "Tuning" });

  for (const [group, values] of Object.entries(tuning)) {
    const folder = gui.addFolder(group);
    const record = values as Record<string, unknown>;
    for (const key of Object.keys(record)) {
      const value = record[key];
      if (typeof value === "string" && value.startsWith("#")) {
        folder.addColor(record, key).listen();
      } else {
        folder.add(record, key).listen();
      }
    }
    folder.close();
  }

  const actions = {
    copy: async () => {
      await navigator.clipboard.writeText(tuningAsJson());
      console.info("[tuning] copied; paste into assets/data/tuning.json");
    },
  };
  gui.add(actions, "copy").name("Copy tuning JSON");

  gui.hide();
  return gui;
}
