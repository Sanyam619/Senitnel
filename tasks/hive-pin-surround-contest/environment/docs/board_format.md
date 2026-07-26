# Board format

Each round under `/app/puzzles/` is a small text sheet.

```
round_id: 1
to_move: white
moves_left: 1
pieces:
B-Q 0 0 0
B-S1 -1 0 0
B-S2 -1 1 0
W-G1 3 0 0
```

## Header

- `round_id` — round number, matches the file stem.
- `to_move` — whose turn it is (always `white` in this booklet).
- `moves_left` — White's remaining move count for that round.

## Pieces

Each `pieces:` row is `<id> <q> <r> <h>`:

- `id` — a piece id like `W-G1` or `B-S3`. The letter before the `-` is the
  color (`W` white, `B` black); the letter after the `-` is the insect
  kind: `Q` queen, `B` beetle, `G` grasshopper, `S` spider, `A` ant. The
  trailing digit disambiguates pieces of the same kind and color.
- `q`, `r` — axial hex coordinates.
- `h` — stack height. `0` means the piece sits on the ground; a beetle
  that has climbed onto another piece has `h` equal to one more than the
  piece it is standing on.

## Move tokens

A move is written `<id>><q>,<r>` — the moving piece's id, a `>`, then its
destination axial coordinates. Example: `W-G1>1,0` moves piece `W-G1` to
`(1, 0)`. `sequence` and `refutations` in the score card use this token
format, and so does the sealed judge's `--move` / `--moves` arguments.
