# Tournament card

File the card at `/app/answers.json`. One row per sheet under `/app/puzzles/`,
`board_id` spelled as printed there, rows ordered by `board_id` ascending.
`schema_tag` is `carcassonne-meeple-v1`.

Shape only — the rounds below are from an old booklet, not the one on the desk:

```json
{
  "schema_tag": "carcassonne-meeple-v1",
  "rounds": [
    {
      "board_id": "41",
      "status": "win",
      "tile": "FFCF@b3:0",
      "meeple": "city:S",
      "score_delta": 4,
      "sequence": ["red FFCF@b3:0+city:S"],
      "refutations": [],
      "coop_claim": true
    },
    {
      "board_id": "42",
      "status": "trap",
      "tile": "FFCF@b3:0",
      "meeple": "",
      "score_delta": 6,
      "sequence": ["red FFCF@b3:0", "red FFFC@c2:0+city:W"],
      "refutations": [{"placement": "FFCF@b3:0+city:S", "reply": "seat:b2:city:N"}],
      "coop_claim": true
    },
    {
      "board_id": "43",
      "status": "fort",
      "tile": "",
      "meeple": "",
      "score_delta": 0,
      "sequence": [],
      "refutations": [],
      "coop_claim": false
    }
  ]
}
```

- `status` is one of the three verdict words in `contest_rules.md`.
- `tile` is the first Red placement without the meeple suffix on a `win` or
  `trap`, and `""` on a `fort`.
- `meeple` is the seat on that first placement (`kind:edge`), or `""`.
- `score_delta` is the Red score the sealed judge reports after replaying the
  filed line (`0` on a `fort`); padding above that count is refused.
- `sequence` carries the colour-tagged turns that witness the verdict — a
  fighting line on a `win`, a friendly Red-only line on a `trap`, empty on a
  `fort`.
- `refutations` covers the sheet's threats on a `trap` (see `contest_rules.md`),
  and is empty on a `win` or `fort`. Each row uses `placement` and `reply`.
- `coop_claim` says whether the friendly climb exists inside three Red turns.

The table checks the whole booklet at once, so a round filed on a hunch costs
that round. A finished card already at `/app/answers.json` stays byte-identical
when the desk emits it twice with no edits.
