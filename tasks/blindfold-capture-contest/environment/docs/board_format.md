# Board file layout

Each file under `/app/puzzles/board_NN.txt` looks like:

```
sheet_id: 1
to_move: black
objective: capture_target
target: a8
defender: white
board:
N......K
........
........
........
........
........
........
r......k
```

- `target` is the starting square of the marked defender piece.
- Board rows are rank 8 through rank 1. Uppercase pieces are white; lowercase are black; `.` is empty.
- The objective is to capture that marked piece off the board under the house announce and try customs.

Do not edit files under `/app/puzzles/`. The table judge rereads them on each check.
