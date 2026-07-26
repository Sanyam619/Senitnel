# Board format

Each round file under `/app/puzzles/` looks like:

```
board_id: board_01
to_move: white
moves_left: 2
white:
a7 d7 g4 a1 b2 c3
black:
a4 d1 g1 b6 f6 e5 c5
```

Point names (files a–g, ranks 1–7) sit on the classic Morris lattice:

```
a7 ----- d7 ----- g7
|        |        |
|  b6 -- d6 -- f6 |
|  |     |     |  |
|  |  c5-d5-e5 |  |
a4 --b4--c4  e4--f4--g4
|  |  c3-d3-e3 |  |
|  |     |     |  |
|  b2 -- d2 -- f2 |
|        |        |
a1 ----- d1 ----- g1
```

## Mill lines

Outer: `a7-d7-g7`, `a1-d1-g1`, `a7-a4-a1`, `g7-g4-g1`
Middle: `b6-d6-f6`, `b2-d2-f2`, `b6-b4-b2`, `f6-f4-f2`
Inner: `c5-d5-e5`, `c3-d3-e3`, `c5-c4-c3`, `e5-e4-e3`
Crossbars: `a4-b4-c4`, `e4-f4-g4`, `d7-d6-d5`, `d3-d2-d1`

## Move tokens

A slide or flight is `W:fr-to` or `B:fr-to` (example `W:g4-g7`). A forced
pass when a side has no legal destination is `B:pass` / `W:pass`. Removals
are filed separately on the card as bare point names (`b6`, `g1`, …), not
as move tokens.
