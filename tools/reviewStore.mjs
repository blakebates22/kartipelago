import fs from "node:fs";
import path from "node:path";

/**
 * Dev only: the level review tool's notes (src/review/notes.ts) are saved straight into
 * the repo, reviews/<track>/notes.json with screenshots in reviews/<track>/shots/.
 *
 *   GET    /__review/<track>                notes.json (an empty file if none yet)
 *   POST   /__review/<track>/note           { trackName, note, shot? }  -> the saved note
 *   DELETE /__review/<track>/note/<id>
 *   GET    /__review/<track>/shots/<file>
 */
export function reviewStore() {
  return {
    name: "kartipelago-review-store",
    apply: "serve",
    configureServer(server) {
      const root = path.resolve(server.config.root, "reviews");
      const safe = (s) => /^[A-Za-z0-9_-]+$/.test(s);
      const read = (track) => {
        const f = path.join(root, track, "notes.json");
        if (!fs.existsSync(f)) return { track, trackName: track, notes: [] };
        return JSON.parse(fs.readFileSync(f, "utf8"));
      };
      const write = (track, data) => {
        fs.mkdirSync(path.join(root, track), { recursive: true });
        fs.writeFileSync(
          path.join(root, track, "notes.json"),
          JSON.stringify(data, null, 2) + "\n",
        );
      };
      server.middlewares.use((req, res, next) => {
        const m = /^\/__review\/([^/?]+)(?:\/(note|shots)(?:\/([^/?]+))?)?/.exec(req.url ?? "");
        if (!m) return next();
        const track = decodeURIComponent(m[1]);
        const sub = m[2];
        const arg = m[3] ? decodeURIComponent(m[3]) : undefined;
        if (!safe(track)) {
          res.statusCode = 400;
          return res.end("bad track id");
        }
        const send = (body) => {
          res.setHeader("content-type", "application/json");
          res.end(JSON.stringify(body));
        };
        if (!sub && req.method === "GET") return send(read(track));
        if (sub === "shots" && arg && /^[A-Za-z0-9_-]+\.jpg$/.test(arg) && req.method === "GET") {
          const f = path.join(root, track, "shots", arg);
          if (!fs.existsSync(f)) {
            res.statusCode = 404;
            return res.end();
          }
          res.setHeader("content-type", "image/jpeg");
          return res.end(fs.readFileSync(f));
        }
        if (sub === "note" && req.method === "DELETE" && arg) {
          const data = read(track);
          const gone = data.notes.find((n) => n.id === arg);
          data.notes = data.notes.filter((n) => n.id !== arg);
          write(track, data);
          if (gone?.shot && !gone.shot.startsWith("data:")) {
            const f = path.join(root, track, "shots", gone.shot);
            if (fs.existsSync(f)) fs.rmSync(f);
          }
          return send({ ok: true });
        }
        if (sub === "note" && req.method === "POST") {
          let body = "";
          req.on("data", (c) => (body += c.toString()));
          req.on("end", () => {
            try {
              const { trackName, note, shot } = JSON.parse(body);
              if (!safe(note.id)) throw new Error("bad note id");
              if (shot?.startsWith("data:image/jpeg;base64,")) {
                fs.mkdirSync(path.join(root, track, "shots"), { recursive: true });
                const file = `${note.id}.jpg`;
                fs.writeFileSync(
                  path.join(root, track, "shots", file),
                  Buffer.from(shot.slice(shot.indexOf(",") + 1), "base64"),
                );
                note.shot = file;
              }
              const data = read(track);
              if (trackName) data.trackName = trackName;
              const i = data.notes.findIndex((n) => n.id === note.id);
              if (i >= 0) data.notes[i] = note;
              else data.notes.push(note);
              write(track, data);
              server.config.logger.info(`review: saved note ${note.id} on ${track}`);
              send(note);
            } catch (err) {
              res.statusCode = 400;
              res.end(String(err));
            }
          });
          return;
        }
        res.statusCode = 405;
        res.end();
      });
    },
  };
}
