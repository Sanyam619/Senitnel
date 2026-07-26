# Round file layout

Each round under `/app/puzzles/` is a small text card: a header, then a 9×9 goban. Blank lines between header lines are fine. Lines starting with `#` are comments.

## Header

- `puzzle_id: <N>` — round number 1..12 (matches the file suffix).
- `to_move: black` or `to_move: white` — who plays first in a submitted line.
- `target: R,C` — 1-indexed point that must be empty for a win.
- `board:` — marker; the next 9 non-blank lines are the goban, top to bottom.

## Goban grid

Nine lines of nine characters:

- `.` empty
- `X` black
- `O` white

Row grows downward; column grows right. Top-left is `(1,1)`.

## Example

```
puzzle_id: 0
to_move: black
target: 5,5
board:
.........
.........
.........
....X....
...XO....
....X....
.........
.........
.........
```

Do not edit files under `/app/puzzles/`. The table judge rereads them on each `validate`.
