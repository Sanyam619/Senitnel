# Round sheets

Each round under `/app/puzzles/board_XX.txt` is printed like this:

```
board_id: 04
to_move: black
mark: b6
board:
..WB....
WBBBBB..
WWWW.W..
WBWBW...
.WWWWW..
.BWBBB..
..BBBBB.
.W.BBBB.
```

- Eight rows follow `board:`, rank 8 on top down to rank 1.
- Files run left to right in the order `abcdefgh`, putting `a8` top left.
- `B` is a Black disc, `W` is a White disc, `.` is an empty square.
- `mark:` names the White disc the round is played for. On every sheet the mark
  starts out White.
- Every round on the booklet is Black to move.

The sealed judge reads these sheets directly, so `view` is the quickest way to
confirm you read a grid the same way the table does.
