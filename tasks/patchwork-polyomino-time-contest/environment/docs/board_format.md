# Round sheet format

Each `/app/puzzles/board_XX.txt` describes one round:

```
board_id: 07
quilt: 4x4
blocked: r2c2
time_track: 11
income: 5,6,7
floor: 2
red_start: 4
blue_start: 5
market:
P1 2 2 0 : XXX/.X.
P2 2 1 1 : XX/X.
P3 2 1 1 : XXX/.X.
P4 3 2 3 : XX/XX
```

- `quilt: RxC` — Red's quilt is R rows by C columns. Rows and columns are
  0-indexed; cell `rRcC` is row R, column C.
- `blocked:` — comma-separated pre-filled quilt cells (may be absent). Blocked
  cells cannot be covered and are not counted as empty.
- `time_track:` — the last position on the shared track; both tokens start at 0.
- `income:` — the track positions that pay income.
- `floor:` — the closing score Red is trying to reach.
- `red_start:` / `blue_start:` — starting banked buttons for each player.
- `market:` — one patch per line, `PID TIME COST INCOME : SHAPE`. The shape is
  drawn row by row with `/` between rows, `X` for a filled cell and `.` for a
  gap, in the orientation the patch is placed (no rotation).
