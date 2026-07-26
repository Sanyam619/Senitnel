# Board format

Each round sheet under `/app/puzzles/` looks like:

```
board_id: 01
to_move: yellow
board:
.......
.......
.......
.Y.R...
RYRYR..
YRYRYR.
```

Six rows of seven characters, top rank first. `.` empty, `Y` Yellow, `R` Red.
Columns are `0`..`6` left to right. Rows for threat cells are `0`..`5` bottom
to top (the gravity landing of a column is the lowest empty row).
