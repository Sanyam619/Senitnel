# Board sheet format

Each round under `/app/puzzles/board_XX.txt` carries:

```
board_id: 01
to_move: red
floor: 4
budget: 3
blue_stock: 1
hand: FFCF,FFFC
tiles:
b2:CCFF:0
meeples:
b2:R:city:N
```

- `hand` lists pre-oriented tile codes (`*` pennant, `#` cloister).
- `tiles:` rows are `cell:CODE:0` (orientation fixed at zero).
- `meeples:` rows are `cell:colour:kind:edge` with colour `R` or `B`.
- Empty cells are omitted from `tiles:`.
