# Tournament card

File the card at `/app/answers.json`. One row per sheet under `/app/puzzles/`,
`board_id` spelled as printed there, rows ordered by `board_id` ascending.

Shape only — the rounds below are from an old booklet, not the one on the desk:

```json
{
  "rounds": [
    {
      "board_id": "41",
      "status": "win",
      "key_push": "c3d3>e3",
      "ejected": 1,
      "sequence": ["black c3d3>e3", "white a1>b1", "black e3>e2"],
      "refutations": [],
      "coop_eject": true
    },
    {
      "board_id": "42",
      "status": "trap",
      "key_push": "b2>c2",
      "ejected": 1,
      "sequence": ["black b2>c2", "black c2d2>e2"],
      "refutations": [{"move": "c3>d3", "reply": "e1>d1"}],
      "coop_eject": true
    },
    {
      "board_id": "43",
      "status": "fort",
      "key_push": "",
      "ejected": 0,
      "sequence": [],
      "refutations": [],
      "coop_eject": false
    }
  ]
}
```

- `status` is one of the three verdict words in `contest_rules.md`.
- `key_push` is the first Black turn of the filed line on a `win` or `trap`, and
  `""` on a `fort`.
- `ejected` is the White marbles the sealed judge reports after replaying the
  filed line (`0` on a `fort`); padding above that count is refused.
- `sequence` carries the colour-tagged turns that witness the verdict — a
  fighting line on a `win`, a friendly Black-only line on a `trap`, empty on a
  `fort`.
- `refutations` covers the sheet's threats on a `trap` (see `contest_rules.md`),
  and is empty on a `win` or `fort`.
- `coop_eject` says whether the friendly three-turn climb exists.

The table checks the whole booklet at once, so a round filed on a hunch costs
that round. A finished card already at `/app/answers.json` stays byte-identical
when the desk emits it twice with no edits.
