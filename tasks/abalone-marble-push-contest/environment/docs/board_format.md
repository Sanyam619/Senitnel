# Board format

Each sheet under `/app/puzzles/` carries a `board_id`, `to_move: black`, and a
staggered hex ASCII grid under `board:`. Glyphs: `.` empty, `B` Black, `W`
White. Five visual rows map to the radius-2 hex (lengths 3-4-5-4-3). Leading
spaces are only for the stagger; the judge strips them.
