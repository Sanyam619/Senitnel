# Board format

Contest rounds live under `/app/puzzles/board_XX.txt`.

```
board_id: board_01
to_move: first
budget: 2
heights:
0 0 0 0 0
0 0 0 0 0
0 2 3 0 0
0 0 0 0 0
0 0 0 0 0
first: b3 a1
second: e5 e1
```

- The five `heights` rows are rank 5 (top) through rank 1 (bottom); columns
  are files `a` … `e`.
- Height cells are `0`–`3` or `D` for a dome.
- `first` / `second` list the two worker squares for each side.
- Leave puzzle sheets unchanged.

## Move dialect

- Ordinary turn: `F:b3-c2:b3` — First moves the worker on `b3` to `c2`, then
  builds on `b3`.
- Summit turn: `F:b3-c3` — First moves onto a level-3 square and does not
  build.
- Second uses the `S:` prefix the same way.

Scratch sessions under `/app/history/` show the same dialect on throwaway
boards.
