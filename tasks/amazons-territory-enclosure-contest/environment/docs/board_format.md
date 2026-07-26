# Round sheets

Each round under `/app/puzzles/board_XX.txt` is printed like this:

```
board_id: 04
to_move: white
board:
W.X.B
.XXX.
X.W.X
.XXX.
B.X.W
```

- Five rows follow `board:`, rank 5 on top down to rank 1.
- Files run left to right in the order `abcde`, putting `a5` top left.
- `W` is a White amazon, `B` is a Black amazon, `X` is a fired arrow, `.` is
  empty.
- Every round on this booklet is White to move on a 5x5 board.

The sealed judge reads these sheets directly, so `view` is the quickest way to
confirm you read a grid the same way the table does. Do not edit anything
under `/app/puzzles/`.
