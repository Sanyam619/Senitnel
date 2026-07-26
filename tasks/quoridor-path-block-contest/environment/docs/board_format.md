# Board format

Each round under `/app/puzzles/` is a small text sheet.

```
round_id: 1
to_move: black
walls_left: 3
walls: h-a2 v-c3
board:
..W..
.....
.....
.....
..B..
```

## Grid

- The board is **5×5** squares.
- Files are `a`–`e` left to right.
- Ranks are `1`–`5`. Rank 1 is south; rank 5 is north.
- The first `board:` row is rank 5; the last row is rank 1.
- `B` is Black's pawn; `W` is White's pawn; `.` is empty.

## Goals

- Black's goal is the north edge: any square on rank 5.
- White's goal is the south edge: any square on rank 1.

## Wall spelling

Walls are length-2 fence placements:

- `h-XY` — horizontal wall anchored at square `XY`. Example `h-b2` sits on
  the gap between ranks 2 and 3 across files `b` and `c`, so it blocks
  vertical steps `b2↔b3` and `c2↔c3`.
- `v-XY` — vertical wall anchored at square `XY`. Example `v-b2` sits on
  the gap between files `b` and `c` across ranks 2 and 3, so it blocks
  horizontal steps `b2↔c2` and `b3↔c3`.

Anchors fit on the board only when the two-segment wall stays inside the
5×5 frame (files `a`–`d`, ranks `1`–`4`).

## `walls_left`

`walls_left` is Black's remaining wall inventory for that round. White does
not place walls in this booklet.
