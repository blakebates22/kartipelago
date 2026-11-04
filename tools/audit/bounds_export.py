# The overworlds' walls, for tools/audit/bounds.audit.ts: each region's signed distance to
# its walls (negative inside the land you drive, positive in a wall or a ridge and beyond)
# sampled every 4 m in game coordinates (x, z = -Blender y). Pure Python (no Blender).
#
#   python3 tools/audit/bounds_export.py        -> audit-out/bounds/<package>.json
# SPDX-License-Identifier: MIT

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "blender", "prehistoric"))

LAYOUTS = {
    "valley_region": "valley_layout",
    "snow_region": "snow_layout",
    "beach_region": "isle_layout",
    "journey_gorge": "jgorge_layout",
    "journey_pass": "jpass_layout",
    "journey_dust": "jdust_layout",
}
CELL = 4.0
EXTENT = 520.0


def main():
    out = os.path.join(HERE, "..", "..", "audit-out", "bounds")
    os.makedirs(out, exist_ok=True)
    for pkg, mod in LAYOUTS.items():
        L = __import__(mod)
        n = int(2 * EXTENT / CELL) + 1
        sd = []
        for j in range(n):
            gz = -EXTENT + j * CELL
            row = []
            for i in range(n):
                gx = -EXTENT + i * CELL
                row.append(round(L.wall_sd(gx, -gz), 1))
            sd.append(row)
        for suffix in ("", "_ruin"):
            with open(os.path.join(out, pkg + suffix + ".json"), "w") as f:
                json.dump({"package": pkg + suffix, "layout": mod, "x0": -EXTENT, "z0": -EXTENT, "cell": CELL, "n": n, "sd": sd}, f)
        print(pkg, mod, n * n)


if __name__ == "__main__":
    main()
