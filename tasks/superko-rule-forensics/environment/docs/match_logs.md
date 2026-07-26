# Match books

Files under `/app/history/` are finished games from this table. Each book is one 9×9 game from an empty goban, Black to move.

## Line shape

```
<ply>  <color> <move>  <verdict>  [note]
```

- `<ply>` — zero-padded ply number (`001`, `002`, …), including passes and refused tries.
- `<color>` — `black` or `white`.
- `<move>` — `R,C` or `pass`.
- `<verdict>` — `accepted` or `rejected`.
- `[note]` — optional colour on accepts; structured on refusals.

`#` lines are commentary and can be skipped.

## Ko refusals

A refused ko-style play carries:

```
superko:recreates_board_from_ply_<REF>
```

`<REF>` points at an earlier accepted ply whose after-position the judge treats as repeating. The note names that ply only.

### Reading a refusal against the three families

The families disagree on what must match:

- **positional** — stones only (side to move ignored).
- **situational** — stones and side to move.
- **natural situational** — like situational, with a special reading of consecutive passes.

When a refusal cites `ply_<REF>`, compare the refusing colour to the colour that played that referenced ply. Cross-colour recreations are positional-only evidence; same-colour recreations still fit situational families.

Past games under this table are the fair way to learn which family the sealed judge is using.
