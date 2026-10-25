# Which version a course script builds: its standard lap, or its ruin (Adventure's treasure
# map challenge, after the dragons' attack). A ruin's own script (cascade_ruins.py, ...)
# sets ON before importing the course's script, which then lays out its ruined lap and
# calls DRESS(c, module) before finishing, for the wreckage. Off, nothing changes.
# SPDX-License-Identifier: MIT

ON = False
DRESS = None


def fingerprints(track_id):
    """{file name: sha256} of the course's own scripts loaded for this build: every module
    from this folder sharing the course's prefix (riverbend_, cascade_, ember_, ...), the
    standard course's script and the ruin's. Shared kits (course_kit, props, ...) aren't
    counted: they change everything at once."""
    import hashlib
    import os
    import sys

    here = os.path.dirname(os.path.abspath(__file__))
    prefix = track_id.split("_")[0] + "_"
    out = {}
    for m in list(sys.modules.values()):
        f = getattr(m, "__file__", None)
        if not f or os.path.dirname(os.path.abspath(f)) != here:
            continue
        name = os.path.basename(f)
        if name.startswith(prefix) and name.endswith(".py"):
            with open(f, "rb") as fh:
                out[name] = hashlib.sha256(fh.read()).hexdigest()
    return dict(sorted(out.items()))
