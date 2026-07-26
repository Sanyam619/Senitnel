# Match logs

Files under `/app/history/` are finished blindfold sessions from this table.

## Line shape

```
<ply>  <color> <move>  <verdict>  [announce-or-note]
```

- `<ply>` — zero-padded ply number (`001`, `002`, …), including refused tries.
- `<color>` — `black` or `white`.
- `<move>` — a four-character square-to-square try, or `pass`.
- `<verdict>` — `accepted` or `rejected`.
- On accepts, the final token is the announce the table spoke.
- On rejects, the note is usually `void`.

`#` lines are commentary and can be skipped.

## Reading capture announces

Past logs under this table are the fair way to learn which announce shape the sealed judge expects on capture tries. Quiet captures use `taken:<sq>`. When the same try also gives check, the table speaks the compound tag `taken:<sq>+check` (and `taken:<sq>+mate` on mate). Bare `taken` without a square is the wrong dialect for this table.
