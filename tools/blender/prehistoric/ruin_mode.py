# Which version a course script builds: its standard lap, or its ruin (Adventure's treasure
# map challenge, after the dragons' attack). A ruin's own script (cascade_ruins.py, ...)
# sets ON before importing the course's script, which then lays out its ruined lap and
# calls DRESS(c, module) before finishing, for the wreckage. Off, nothing changes.
# SPDX-License-Identifier: MIT

ON = False
DRESS = None
