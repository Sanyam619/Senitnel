# Round file layout

Each contest round lives at `/app/puzzles/board_NN.txt` and looks like:

```
round_id: 1
to_move: black
link_goal: top_bottom
board:
W.WWB
...W.
.BW..
B.BBB
W.W.B
```

- The grid is a square Hex rhombus. `B` is a Black stone, `W` is a White
  stone, `.` is an empty cell.
- The first board row is the **top** edge (row 1); the last row is the
  **bottom** edge. Columns are lettered `a`, `b`, `c`, ... from the left.
  A cell is named by its column letter and row number, e.g. `a1` is the
  top-left cell and `e5` is the bottom-right cell on a 5-wide board.
- Every round is Black to move.

## Links on a Hex board

Each cell touches six neighbours: same row left/right, same column
up/down, and the two "short-diagonal" cells (one column right and one row
up, one column left and one row down). Corners and edges touch fewer.

- **Black** owns the vertical link: a chain of Black stones joining the
  top edge to the bottom edge.
- **White** owns the horizontal link: a chain of White stones joining the
  left edge to the right edge.

On a filled board exactly one side holds a completed link; the two links
cannot both exist and cannot both fail.

Do not edit anything under `/app/puzzles/`. The table judge rereads the
round files on every call.
