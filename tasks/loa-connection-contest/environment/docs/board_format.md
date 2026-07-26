# Round sheet layout

Each contest round lives at `/app/puzzles/board_NN.txt` and looks like:

```
round_id: 1
to_move: black
board:
W.....
.B....
..B...
.BB...
WW....
.B....
```

- The grid is square. `B` is a Black piece, `W` is a White piece, `.` is an
  empty square. Sheets in this booklet run from four to six squares wide.
- The first board line is **rank 1**; the last board line is the highest
  rank. Files are lettered `a`, `b`, `c`, ... from the left. A square is
  named by its file letter and rank number, so `a1` is the first square of
  the first board line and `d3` is the fourth square of the third line.
- Every round is Black to move.

## Move tokens

A move is written `<from>-<to>`, both in the square naming above, for
example `a1-a3` or `d3-b3`. The table judge speaks the same tokens.

## Connected groups

Two pieces of the same colour sit in the same group when their squares
touch — sharing a side or only a corner both count, so a square has up to
eight neighbours. A side is **connected** when every one of its surviving
pieces belongs to one group. A side down to a single piece is connected.

Captures remove pieces from the board, so a side's group count can change
because a piece moved *or* because a piece was taken.

Do not edit anything under `/app/puzzles/`. The table judge rereads the
round sheets on every call.
