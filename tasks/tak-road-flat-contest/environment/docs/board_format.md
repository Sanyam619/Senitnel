# Board format

Each round under `/app/puzzles/` is a small text sheet.

```
round_id: 1
to_move: white
flats_w: 2
flats_b: 2
caps_w: 0
caps_b: 0
board:
w . . . .
w . . . .
w . b . .
w . . . .
. . . . .
```

## Grid

- The board is **5×5** squares.
- Files are `a`–`e` left to right.
- Ranks are `1`–`5`. Rank 1 is south; rank 5 is north.
- The first `board:` row is rank 5; the last row is rank 1.
- Cells are space-separated. `.` is empty. A multi-character cell is a stack
  bottom→top using the piece alphabet below (e.g. `wbW`).

## Piece alphabet

| Glyph | Meaning |
| --- | --- |
| `w` | White flat |
| `W` | White standing stone |
| `C` | White capstone |
| `b` | Black flat |
| `B` | Black standing stone |
| `K` | Black capstone |

## Goals

- White's road goal is north–south: a chain of White road stones touching
  rank 5 and rank 1.
- Black's east–west road is not graded in this booklet.

## Move tokens

Used in `sequence` and `refutations`:

- `F:a3` — place a flat on `a3`
- `S:a3` — place a standing stone on `a3`
- `C:a3` — place the capstone on `a3`
- `1a3>1` — take 1 from `a3`, slide one step east (`>`), drop 1.
  Directions: `>` east, `<` west, `+` north, `-` south.
