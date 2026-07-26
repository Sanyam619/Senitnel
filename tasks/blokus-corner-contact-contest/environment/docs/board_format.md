# Board format

Each round sheet under `/app/puzzles/board_XX.txt` looks like:

```
board_id: 01
blue_inv: V3,1
yellow_inv: 2
board:
.....
.....
.....
.....
B....
```

- `board_id` is the round id filed on the card.
- `blue_inv` / `yellow_inv` are comma-separated remaining piece ids.
- The grid is five rows of five cells, top row is rank 5, bottom is rank 1.
  Files run `a`..`e` left to right. Cells: `.` empty, `B` Blue, `Y` Yellow,
  `X` block.
